"""Study A, pre-registered analysis.

  python research/harness/studya_eval.py RESULTS.json [RESULTS.json ...] [--out DIR] [--stats-image ucn-studya-stats]

Input rows (recon.py results.json) need: rule_id, site (consistent | none | contradicting | control), seeded, half,
agent_model, violations (0/1), success. A row is skipped, and counted, when it has no rule test left: it lacks rule_id
or site, its violations is null, or it carries no_rule_test = true.

Output: DIR/studya.json and DIR/studya.md (the table is also printed). Bootstrap, permutation and tables are pure
standard library. The mixed-effects logistic model (violation ~ site + (1 | rule)) needs statsmodels and runs in the
container built from research/trials/containers/stats (harness/studya_mixed.py); without Docker it is reported as not run.

Decision per level (contradicting, none): H1 is REFUTED when the lower bound of the 95% cluster-bootstrap interval of
(level - consistent) is not above 0; INCONCLUSIVE when the cell is at a ceiling or floor (both rates <= 10% or both
>= 90%); otherwise SUPPORTED.
"""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile

MIXED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "studya_mixed.py")
SEED = 20260101
RESAMPLES = 10000
SHUFFLES = 10000
LEVELS = ("contradicting", "none")


def load(paths):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            rows += json.load(fh)
    return rows


def usable(row):
    return (row.get("rule_id") and row.get("site") and row.get("violations") is not None
            and not row.get("no_rule_test"))


def split(rows):
    keep = [r for r in rows if usable(r)]
    return keep, len(rows) - len(keep)


def rate(rows):
    return sum(r["violations"] for r in rows) / len(rows) if rows else None


def counts(rows, a, b):
    """{rule: [n_a, v_a, n_b, v_b]} for sites a and b."""
    out = {}
    for r in rows:
        if r["site"] not in (a, b):
            continue
        c = out.setdefault(r["rule_id"], [0, 0, 0, 0])
        i = 0 if r["site"] == a else 2
        c[i] += 1
        c[i + 1] += int(r["violations"])
    return out


def diff_of(cs):
    na = sum(c[0] for c in cs)
    nb = sum(c[2] for c in cs)
    if not na or not nb:
        return None
    return sum(c[1] for c in cs) / na - sum(c[3] for c in cs) / nb


def quantile(xs, q):
    xs = sorted(xs)
    pos = q * (len(xs) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def bootstrap(cs, rng, n=RESAMPLES):
    """Cluster bootstrap over rules: resample whole rules with replacement."""
    cs = list(cs.values())
    ds = []
    for _ in range(n):
        d = diff_of([cs[rng.randrange(len(cs))] for _ in cs])
        if d is not None:
            ds.append(d)
    if len(ds) < n // 2:
        return None, len(ds)
    return (quantile(ds, 0.025), quantile(ds, 0.975)), len(ds)


def permutation(rows, a, b, rng, n=SHUFFLES):
    """Two-sided p: site labels shuffled within each rule (only rows at sites a and b take part)."""
    by = {}
    for r in rows:
        if r["site"] in (a, b):
            by.setdefault(r["rule_id"], []).append((r["site"] == a, int(r["violations"])))
    groups = [(sum(1 for s, _ in g if s), [v for s, v in g if s] + [v for s, v in g if not s]) for g in by.values()]

    def stat(assign):  # assign: list of (n_a, values in the order a-first)
        va = na = vb = nb = 0
        for k, vals in assign:
            na += k
            va += sum(vals[:k])
            nb += len(vals) - k
            vb += sum(vals[k:])
        return va / na - vb / nb if na and nb else None

    observed = stat(groups)
    if observed is None:
        return None
    hits = 0
    pools = [(k, vals[:]) for k, vals in groups]
    for _ in range(n):
        for _, vals in pools:
            rng.shuffle(vals)
        d = stat(pools)
        if d is not None and abs(d) >= abs(observed) - 1e-12:
            hits += 1
    return (hits + 1) / (n + 1)


def contrast(rows, a, b, label):
    """The difference a - b with its bootstrap interval and permutation p."""
    cs = counts(rows, a, b)
    out = {"contrast": label, "a": a, "b": b, "rules": len(cs)}
    ra = rate([r for r in rows if r["site"] == a])
    rb = rate([r for r in rows if r["site"] == b])
    out.update(rate_a=ra, rate_b=rb, n_a=sum(1 for r in rows if r["site"] == a), n_b=sum(1 for r in rows if r["site"] == b))
    d = diff_of(list(cs.values()))
    out["diff"] = d
    if d is None:
        out.update(ci=None, p=None)
        return out
    ci, used = bootstrap(cs, random.Random(f"{SEED}-boot-{label}"))
    out["ci"] = list(ci) if ci else None
    out["bootstrap_resamples_used"] = used
    out["p"] = permutation(rows, a, b, random.Random(f"{SEED}-perm-{label}"))
    return out


def leave_one_out(rows, a, b):
    out = []
    for rule in sorted({r["rule_id"] for r in rows}):
        d = diff_of(list(counts([r for r in rows if r["rule_id"] != rule], a, b).values()))
        out.append({"left_out": rule, "diff": d})
    return out


def decision(c):
    if c["diff"] is None or not c["ci"]:
        return "no data"
    ra, rb = c["rate_a"], c["rate_b"]
    if (ra <= 0.10 and rb <= 0.10) or (ra >= 0.90 and rb >= 0.90):
        return "INCONCLUSIVE (ceiling or floor)"
    return "REFUTED" if c["ci"][0] <= 0 else "SUPPORTED"


def rates_by(rows, key):
    out = {}
    for v in sorted({str(r.get(key)) for r in rows}):
        sub = [r for r in rows if str(r.get(key)) == v]
        out[v] = {s: {"rate": rate([r for r in sub if r["site"] == s]), "n": sum(1 for r in sub if r["site"] == s)}
                  for s in sorted({r["site"] for r in rows})}
    return out


def mixed(rows, image):
    """violation ~ site + (1 | rule) inside the stats container; never raises."""
    if not image:
        return {"run": False, "reason": "no stats image given"}
    try:
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "rows.json"), "w") as fh:
                json.dump([{"rule_id": r["rule_id"], "site": r["site"], "violations": int(r["violations"])} for r in rows], fh)
            p = subprocess.run(["docker", "run", "--rm", "-v", f"{d}:/data:ro", "-v", f"{MIXED}:/studya_mixed.py:ro", image, "/data/rows.json"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        return json.loads(p.stdout)
    except Exception as e:  # docker missing, image missing, bad output: say so, do not fail
        return {"run": False, "reason": f"{type(e).__name__}: {str(e)[:200]}"}


def analyse(rows, stats_image=None):
    kept, skipped = split(rows)
    main = [r for r in kept if r["site"] != "control"]
    res = {"rows": len(rows), "analysed": len(kept), "skipped_no_rule_test": skipped,
           "seed": SEED, "bootstrap_resamples": RESAMPLES, "permutation_shuffles": SHUFFLES}
    sites = sorted({r["site"] for r in kept})
    res["rates"] = {"overall": {s: {"rate": rate([r for r in kept if r["site"] == s]), "n": sum(1 for r in kept if r["site"] == s)}
                                for s in sites}}
    for key in ("agent_model", "half", "seeded"):
        res["rates"][f"by_{key}"] = rates_by(kept, key)
    res["contrasts"] = [contrast(main, lvl, "consistent", f"{lvl} - consistent") for lvl in LEVELS]
    res["leave_one_rule_out"] = {lvl: leave_one_out(main, lvl, "consistent") for lvl in LEVELS}
    res["control_vs_consistent"] = contrast([r for r in kept if r["site"] in ("control", "consistent")],
                                            "control", "consistent", "control - consistent")
    res["decision"] = {c["a"]: decision(c) for c in res["contrasts"]}
    res["mixed_model"] = mixed(main, stats_image)
    return res


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def pp(x):
    return "n/a" if x is None else f"{100 * x:+.1f} pp"


def pval(p):
    return "n/a" if p is None else f"{p:.4f}"


def markdown(res):
    L = [f"Study A: {res['analysed']} runs analysed, {res['skipped_no_rule_test']} skipped (no rule test left)", ""]
    L += ["| Site condition | Violation rate | Runs |", "|---|---|---|"]
    for s, v in res["rates"]["overall"].items():
        L.append(f"| {s} | {pct(v['rate'])} | {v['n']} |")
    for key in ("agent_model", "half", "seeded"):
        L += ["", f"By {key}:", "", "| " + key + " | " + " | ".join(res["rates"]["overall"]) + " |",
              "|---|" + "---|" * len(res["rates"]["overall"])]
        for val, cells in res["rates"][f"by_{key}"].items():
            L.append(f"| {val} | " + " | ".join(f"{pct(cells[s]['rate'])} (n={cells[s]['n']})" if s in cells else "-"
                                                 for s in res["rates"]["overall"]) + " |")
    L += ["", "| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Rules |", "|---|---|---|---|---|"]
    for c in res["contrasts"] + [res["control_vs_consistent"]]:
        ci = "n/a" if not c["ci"] else f"[{100 * c['ci'][0]:+.1f}, {100 * c['ci'][1]:+.1f}] pp"
        L.append(f"| {c['contrast']} | {pp(c['diff'])} | {ci} | {pval(c['p'])} | {c['rules']} |")
    L += ["", "Leave one rule out (difference in percentage points):", "",
          "| Rule left out | contradicting - consistent | none - consistent |", "|---|---|---|"]
    lo = res["leave_one_rule_out"]
    for a, b in zip(lo["contradicting"], lo["none"]):
        L.append(f"| {a['left_out']} | {pp(a['diff'])} | {pp(b['diff'])} |")
    m = res["mixed_model"]
    L += ["", "Mixed-effects logistic regression, violation ~ site + (1 | rule):", ""]
    if not m.get("run"):
        L.append(f"Not run: {m.get('reason', 'unknown')}")
    else:
        if not m.get("converged"):
            L.append(f"DID NOT CONVERGE: {m.get('reason', '')}")
        else:
            L += ["| Term | Odds ratio | 95% interval |", "|---|---|---|"]
            for t in m["terms"]:
                L.append(f"| {t['term']} | {t['or']:.2f} | [{t['lo']:.2f}, {t['hi']:.2f}] |")
    L += ["", "Decision: " + "; ".join(f"H1 for '{k}': {v}" for k, v in res["decision"].items())]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--out", default=".")
    ap.add_argument("--stats-image", default=None, help="container with statsmodels, e.g. ucn-studya-stats")
    a = ap.parse_args(argv)
    res = analyse(load(a.results), a.stats_image)
    md = markdown(res)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "studya.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    with open(os.path.join(a.out, "studya.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
