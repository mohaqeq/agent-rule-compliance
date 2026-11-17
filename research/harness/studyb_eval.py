"""Study B, pre-registered analysis.

  python research/harness/studyb_eval.py RESULTS.json [RESULTS.json ...] [--out DIR] [--stats-image ucn-studya-stats]
                                          [--arms none,prose,gen,rule,prule,urule]

Input rows are the results.json rows of recon.py with arms. Fields used: run, task, rule_id, arm, guidance, check,
agent_model, violations (0/1), success, tokens, tool_calls, check_runs, failed_check_runs, rule_test_changed,
final_rule_test_passed (true when the last run of the visible rule test passed; null when it never ran).
A row is skipped, and counted, when it has no rule_id, no arm, no violations value, or an arm outside --arms.

Output: DIR/studyb.json and DIR/studyb.md. The table is also printed.
Rows with different agent_model values are analysed apart. The Sonnet replication is a separate section.

The statistics code comes from studya_eval.py: cluster bootstrap over rules, permutation test inside each rule,
leave-one-rule-out, and the mixed model in the stats container. Here the arm takes the place of the Study A "site".
A missing arm is not an error. Each comparison that needs it is marked "not available".

Decision rules (see research/trials/studyB/PREREGISTRATION.md):
  A ceiling or floor (both rates <= 10% or both >= 90%) is INCONCLUSIVE.
  H2:  REFUTED if gen is 15 points or more below prose. SUPPORTED if the lower bound of (gen - prose) is above 0.
       Otherwise INCONCLUSIVE.
  H2b: for each arm, EFFECTIVE if the upper bound of (arm - none) is below 0. All are INCONCLUSIVE when none is below 60%.
  H3:  REFUTED if the median tokens and the median failed check runs of prule are both not lower than those of rule.
       SUPPORTED if both are lower. Otherwise INCONCLUSIVE (the two medians disagree).
  UCN: the differences urule - prule. No decision.
"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studya_eval as A  # noqa: E402

ARMS = ("none", "prose", "gen", "rule", "prule", "urule")
CHECK_ARMS = ("gen", "rule", "prule", "urule")
RULE_TEST_ARMS = ("rule", "prule", "urule")
PLAN = [("gen - prose", "gen", "prose")] + [(f"{a} - none", a, "none") for a in ARMS if a != "none"] + [
    ("urule - prule", "urule", "prule")]
H2_POINTS = 0.15
BASELINE_MIN = 0.60
DROP_IN_SENSITIVITY_2 = ("N2", "P1")
NA = "not available"


def prepare(rows, arms):
    """Keep the usable rows. The arm becomes the "site" key, so the Study A functions work on it."""
    keep = []
    for r in rows:
        if r.get("rule_id") and r.get("arm") in arms and r.get("violations") is not None:
            keep.append(dict(r, site=r["arm"]))
    return keep, len(rows) - len(keep)


def med(rows, key):
    xs = [r[key] for r in rows if r.get(key) is not None]
    return statistics.median(xs) if xs else None


def mean_of(rows, key):
    xs = [r[key] for r in rows if r.get(key) is not None]
    return sum(xs) / len(xs) if xs else None


def ceiling_or_floor(ra, rb):
    return (ra <= 0.10 and rb <= 0.10) or (ra >= 0.90 and rb >= 0.90)


def compare(rows, a, b, label):
    """A.contrast, or a marked stub when an arm has no rows."""
    if not any(r["site"] == a for r in rows) or not any(r["site"] == b for r in rows):
        return {"contrast": label, "a": a, "b": b, "available": False, "diff": None, "ci": None, "p": None,
                "rate_a": A.rate([r for r in rows if r["site"] == a]), "rate_b": A.rate([r for r in rows if r["site"] == b]),
                "rules": 0}
    c = A.contrast(rows, a, b, label)
    c["available"] = True
    return c


def decide_h2(c):
    if not c["available"] or c["diff"] is None or not c["ci"]:
        return NA
    ra, rb = c["rate_a"], c["rate_b"]
    if ceiling_or_floor(ra, rb):
        return "INCONCLUSIVE (ceiling or floor)"
    if ra <= rb - H2_POINTS + 1e-12:
        return "REFUTED (gen is 15 points or more below prose)"
    if c["ci"][0] > 0:
        return "SUPPORTED"
    return "INCONCLUSIVE"


def decide_h2b(c, none_rate):
    if not c["available"] or c["diff"] is None or not c["ci"]:
        return NA
    if none_rate < BASELINE_MIN:
        return "INCONCLUSIVE (the none arm is below 60%: the baseline did not reproduce)"
    if ceiling_or_floor(c["rate_a"], c["rate_b"]):
        return "INCONCLUSIVE (ceiling or floor)"
    return "EFFECTIVE" if c["ci"][1] < 0 else "NOT EFFECTIVE"


def h3(rows):
    p = [r for r in rows if r["arm"] == "prule"]
    q = [r for r in rows if r["arm"] == "rule"]
    if not p or not q:
        return {"decision": NA}
    out = {"tokens_prule": med(p, "tokens"), "tokens_rule": med(q, "tokens"),
           "failed_check_runs_prule": med(p, "failed_check_runs"), "failed_check_runs_rule": med(q, "failed_check_runs")}
    if None in out.values():
        out["decision"] = NA + " (tokens or check counts are missing)"
        return out
    lower_t = out["tokens_prule"] < out["tokens_rule"]
    lower_f = out["failed_check_runs_prule"] < out["failed_check_runs_rule"]
    out["decision"] = "SUPPORTED" if lower_t and lower_f else "REFUTED" if not lower_t and not lower_f else "INCONCLUSIVE"
    return out


def ucn_report(rows, contrasts):
    u = [r for r in rows if r["arm"] == "urule"]
    p = [r for r in rows if r["arm"] == "prule"]
    c = next(x for x in contrasts if x["contrast"] == "urule - prule")
    out = {"violations": c, "decision": "none (no threshold)"}
    for key in ("tokens", "failed_check_runs"):
        a, b = med(u, key), med(p, key)
        out[f"{key}_urule"], out[f"{key}_prule"] = a, b
        out[f"{key}_diff"] = None if a is None or b is None else a - b
    return out


def rates(rows):
    arms = [a for a in ARMS if any(r["arm"] == a for r in rows)]
    over = {a: {"violation_rate": A.rate([r for r in rows if r["arm"] == a]),
                "success_rate": mean_of([r for r in rows if r["arm"] == a], "success"),
                "n": sum(1 for r in rows if r["arm"] == a)} for a in arms}
    by_rule = {}
    for rule in sorted({r["rule_id"] for r in rows}):
        by_rule[rule] = {}
        for a in arms:
            sub = [r for r in rows if r["rule_id"] == rule and r["arm"] == a]
            by_rule[rule][a] = {"violation_rate": A.rate(sub), "success_rate": mean_of(sub, "success"), "n": len(sub)}
    return over, by_rule


def core(rows):
    """Rates, the pre-registered contrasts, and the decisions for one set of rows."""
    over, by_rule = rates(rows)
    contrasts = [compare(rows, a, b, label) for label, a, b in PLAN]
    by_label = {c["contrast"]: c for c in contrasts}
    none_rate = over["none"]["violation_rate"] if "none" in over else None
    h2b = {}
    for a in ARMS:
        if a == "none":
            continue
        c = by_label[f"{a} - none"]
        h2b[a] = NA if none_rate is None else decide_h2b(c, none_rate)
    return {"rates": over, "rates_by_rule": by_rule, "contrasts": contrasts,
            "decision": {"H2": decide_h2(by_label["gen - prose"]), "H2b": h2b}}


def check_use(rows):
    out = {}
    for a in RULE_TEST_ARMS:
        sub = [r for r in rows if r["arm"] == a]
        if not sub:
            continue
        ended = [r for r in sub if r.get("final_rule_test_passed") is True]
        rest = [r for r in sub if r.get("final_rule_test_passed") is not True]
        out[a] = {"runs": len(sub), "ended_with_passing_rule_test": len(ended),
                  "share_passing": len(ended) / len(sub),
                  "never_ran_rule_test": sum(1 for r in sub if r.get("final_rule_test_passed") is None),
                  "violation_rate_passing": A.rate(ended), "violation_rate_not_passing": A.rate(rest)}
    return out


def cost(rows):
    out = {}
    for a in ARMS:
        sub = [r for r in rows if r["arm"] == a]
        if sub:
            out[a] = {"median_tokens": med(sub, "tokens"), "median_tool_calls": med(sub, "tool_calls"),
                      "median_check_runs": med(sub, "check_runs") if a in CHECK_ARMS else None, "n": len(sub)}
    return out


def mixed(rows, image):
    """violation ~ arm + (1 | rule). The none arm is the reference: it is sent as "consistent", the name that
    studya_mixed.py uses for its reference level."""
    if not any(r["arm"] == "none" for r in rows):
        return {"run": False, "reason": "no none arm"}
    view = [dict(r, site="consistent" if r["arm"] == "none" else r["arm"]) for r in rows]
    return A.mixed(view, image)


def sens3(rows):
    return [dict(r, violations=int(bool(r["violations"]) or bool(r.get("rule_test_changed")))) for r in rows]


def analyse_group(rows, image=None):
    res = {"analysed": len(rows)}
    res.update(core(rows))
    res["h2_leave_one_rule_out"] = A.leave_one_out(rows, "gen", "prose") if any(r["arm"] == "gen" for r in rows) and any(
        r["arm"] == "prose" for r in rows) else NA
    res["h3"] = h3(rows)
    res["ucn"] = ucn_report(rows, res["contrasts"])
    res["mixed_model"] = mixed(rows, image)
    res["sensitivity"] = {
        "1_success_only": core([r for r in rows if r.get("success") == 1]),
        "2_without_N2_P1": core([r for r in rows if r["rule_id"] not in DROP_IN_SENSITIVITY_2]),
        "3_rule_test_change_is_violation": core(sens3(rows)),
    }
    res["check_use"] = check_use(rows)
    res["cost"] = cost(rows)
    return res


def analyse(rows, stats_image=None, arms=ARMS):
    kept, skipped = prepare(rows, arms)
    res = {"rows": len(rows), "analysed": len(kept), "skipped": skipped, "arms": list(arms), "seed": A.SEED,
           "bootstrap_resamples": A.RESAMPLES, "permutation_shuffles": A.SHUFFLES, "models": {}}
    for m in sorted({str(r.get("agent_model")) for r in kept}):
        res["models"][m] = analyse_group([r for r in kept if str(r.get("agent_model")) == m], stats_image)
    return res


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def num(x):
    return "n/a" if x is None else f"{x:g}"


def contrast_table(contrasts):
    L = ["| Difference | Rate a | Rate b | Estimate | 95% cluster-bootstrap interval | Permutation p |", "|---|---|---|---|---|---|"]
    for c in contrasts:
        if not c["available"]:
            L.append(f"| {c['contrast']} | {pct(c['rate_a'])} | {pct(c['rate_b'])} | {NA} | {NA} | {NA} |")
            continue
        ci = "n/a" if not c["ci"] else f"[{100 * c['ci'][0]:+.1f}, {100 * c['ci'][1]:+.1f}] pp"
        L.append(f"| {c['contrast']} | {pct(c['rate_a'])} | {pct(c['rate_b'])} | {A.pp(c['diff'])} | {ci} | {A.pval(c['p'])} |")
    return L


def rates_table(over):
    L = ["| Arm | Violation rate | Task success | Runs |", "|---|---|---|---|"]
    for a, v in over.items():
        L.append(f"| {a} | {pct(v['violation_rate'])} | {pct(v['success_rate'])} | {v['n']} |")
    return L


def section(name, g):
    L = [f"## Model: {name} ({g['analysed']} runs)", "", "### Violation rate and task success for each arm", ""]
    L += rates_table(g["rates"])
    arms = list(g["rates"])
    L += ["", "### For each rule and arm (violation rate, task success, runs)", "",
          "| Rule | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for rule, cells in g["rates_by_rule"].items():
        L.append(f"| {rule} | " + " | ".join(f"{pct(cells[a]['violation_rate'])} / {pct(cells[a]['success_rate'])} / n={cells[a]['n']}"
                                              for a in arms) + " |")
    L += ["", "### Pre-registered differences", ""] + contrast_table(g["contrasts"])
    d = g["decision"]
    L += ["", "### Decisions", "", f"- H2 (gen - prose): {d['H2']}"]
    for a, v in d["H2b"].items():
        L.append(f"- H2b, {a} against none: {v}")
    h = g["h3"]
    L.append(f"- H3 (prule against rule): {h['decision']}")
    if "tokens_prule" in h:
        L.append(f"  - median tokens: prule {num(h['tokens_prule'])}, rule {num(h['tokens_rule'])}")
        L.append(f"  - median failed check runs: prule {num(h['failed_check_runs_prule'])}, rule {num(h['failed_check_runs_rule'])}")
    u = g["ucn"]
    L.append(f"- UCN (urule - prule, no decision): violations {A.pp(u['violations']['diff'])}, "
             f"median tokens {num(u['tokens_diff'])}, median failed check runs {num(u['failed_check_runs_diff'])}")
    L += ["", "### Leave one rule out, H2 difference (gen - prose)", ""]
    if g["h2_leave_one_rule_out"] == NA:
        L.append(NA)
    else:
        L += ["| Rule left out | gen - prose |", "|---|---|"]
        L += [f"| {x['left_out']} | {A.pp(x['diff'])} |" for x in g["h2_leave_one_rule_out"]]
    m = g["mixed_model"]
    L += ["", "### Mixed-effects logistic regression, violation ~ arm + (1 | rule), reference arm none (descriptive)", ""]
    if not m.get("run"):
        L.append(f"Not run: {m.get('reason', 'unknown')}")
    elif not m.get("converged"):
        L.append(f"DID NOT CONVERGE: {m.get('reason', '')}")
    else:
        L += ["| Arm | Odds ratio | 95% interval |", "|---|---|---|"]
        L += [f"| {t['term']} | {t['or']:.2f} | [{t['lo']:.2f}, {t['hi']:.2f}] |" for t in m["terms"]]
    names = {"1_success_only": "Sensitivity 1: only runs with task success",
             "2_without_N2_P1": "Sensitivity 2: without rules N2 and P1",
             "3_rule_test_change_is_violation": "Sensitivity 3: a changed rule test counts as a violation"}
    for k, s in g["sensitivity"].items():
        L += ["", f"### {names[k]}", ""] + rates_table(s["rates"]) + [""] + contrast_table(s["contrasts"])
        L += ["", f"H2: {s['decision']['H2']}; H2b: " + "; ".join(f"{a} {v}" for a, v in s["decision"]["H2b"].items())]
    L += ["", "### Check arms: runs that ended with a passing visible rule test", "",
          "| Arm | Runs | Ended with passing rule test | Share | Never ran it | Violation rate, passing | Violation rate, other |",
          "|---|---|---|---|---|---|---|"]
    for a, v in g["check_use"].items():
        L.append(f"| {a} | {v['runs']} | {v['ended_with_passing_rule_test']} | {pct(v['share_passing'])} | "
                 f"{v['never_ran_rule_test']} | {pct(v['violation_rate_passing'])} | {pct(v['violation_rate_not_passing'])} |")
    L += ["", "### Cost for each arm (medians)", "", "| Arm | Tokens | Tool calls | Check invocations | Runs |", "|---|---|---|---|---|"]
    for a, v in g["cost"].items():
        L.append(f"| {a} | {num(v['median_tokens'])} | {num(v['median_tool_calls'])} | {num(v['median_check_runs'])} | {v['n']} |")
    return L


def markdown(res):
    L = [f"Study B: {res['analysed']} runs analysed, {res['skipped']} skipped (no rule, no arm in the list, or no violations value)", ""]
    for name, g in res["models"].items():
        L += section(name, g) + [""]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--out", default=".")
    ap.add_argument("--stats-image", default=None, help="container with statsmodels, e.g. ucn-studya-stats")
    ap.add_argument("--arms", default=",".join(ARMS))
    a = ap.parse_args(argv)
    arms = tuple(x for x in a.arms.split(",") if x)
    res = analyse(A.load(a.results), a.stats_image, arms)
    md = markdown(res)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "studyb.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    with open(os.path.join(a.out, "studyb.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
