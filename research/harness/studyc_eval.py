"""Study C analysis: does information about the wrong precedent prevent the violation?

  python studyc_eval.py RESULTS.json [...] [--out DIR] [--arms none,mark,warn]
Input rows are the results.json rows of recon.py with arms. Each model is analysed separately.
Contrasts (difference of violation rates, 95% cluster bootstrap over rules, permutation within rules):
  mark - none, warn - none (primary), mark - warn (secondary).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studya_eval as A  # noqa: E402
import studyb_eval as B  # noqa: E402

ARMS = ("none", "mark", "warn")
PLAN = [("mark - none", "mark", "none"), ("warn - none", "warn", "none"), ("mark - warn", "mark", "warn")]
HAND_RULES = ("P1", "P5")  # the places of these rules were given by hand, not by the scan


def decide(c, none_rate, primary):
    if not c["available"] or c["diff"] is None or not c["ci"]:
        return B.NA
    if primary:
        return B.decide_h2b(c, none_rate)
    if B.ceiling_or_floor(c["rate_a"], c["rate_b"]):
        return "INCONCLUSIVE (ceiling or floor)"
    return "DIFFERENT" if c["ci"][0] > 0 or c["ci"][1] < 0 else "NO DIFFERENCE SHOWN"


def block(rows, arms):
    by = {a: [r for r in rows if r["site"] == a] for a in arms}
    rates = {a: {"violations": sum(1 for r in x if r["violations"]), "runs": len(x), "rate": A.rate(x),
                 "success": (sum(r["success"] for r in x) / len(x)) if x else None} for a, x in by.items()}
    none_rate = rates.get("none", {}).get("rate")
    contrasts = []
    for label, a, b in PLAN:
        c = B.compare(rows, a, b, label)
        c["decision"] = decide(c, none_rate if none_rate is not None else 0.0, b == "none") if "none" in arms or b != "none" else B.NA
        contrasts.append(c)
    return {"rates": rates, "contrasts": contrasts}


def analyse(rows, arms=ARMS):
    rows, skipped = B.prepare(rows, arms)
    out = {"analysed": len(rows), "skipped": skipped, "models": {}}
    for model in sorted({r.get("agent_model") or "unknown" for r in rows}):
        g = [r for r in rows if (r.get("agent_model") or "unknown") == model]
        rules = sorted({r["rule_id"] for r in g})
        m = {"runs": len(g), "main": block(g, arms),
             "by_rule": {rule: {a: [sum(1 for r in g if r["rule_id"] == rule and r["site"] == a and r["violations"]),
                                    sum(1 for r in g if r["rule_id"] == rule and r["site"] == a),
                                    sum(r["success"] for r in g if r["rule_id"] == rule and r["site"] == a)] for a in arms}
                         for rule in rules},
             "leave_one_out": {rule: {label: B.compare([r for r in g if r["rule_id"] != rule], a, b, label)["diff"]
                                      for label, a, b in PLAN} for rule in rules},
             "success_only": block([r for r in g if r["success"]], arms),
             "without_hand_rules": block([r for r in g if r["rule_id"] not in HAND_RULES], arms),
             "cost": {a: {"median_tokens": B.med([r for r in g if r["site"] == a], "tokens"),
                          "median_tool_calls": B.med([r for r in g if r["site"] == a], "tool_calls")} for a in arms}}
        out["models"][model] = m
    return out


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def pp(x):
    return "n/a" if x is None else f"{100 * x:+.1f} pp"


def block_md(b):
    L = ["| Arm | Violations | Rate | Task success |", "|---|---|---|---|"]
    L += [f"| {a} | {v['violations']} / {v['runs']} | {pct(v['rate'])} | {pct(v['success'])} |" for a, v in b["rates"].items()]
    L += ["", "| Difference | Estimate | 95% cluster-bootstrap interval | Permutation p | Decision |", "|---|---|---|---|---|"]
    for c in b["contrasts"]:
        ci = f"[{pp(c['ci'][0])}, {pp(c['ci'][1])}]" if c.get("ci") else "n/a"
        p = "n/a" if c.get("p") is None else f"{c['p']:.4f}"
        L.append(f"| {c['contrast']} | {pp(c['diff'])} | {ci} | {p} | {c['decision']} |")
    return L


def markdown(res, arms):
    L = [f"Study C: {res['analysed']} runs analysed, {res['skipped']} skipped", ""]
    for model, m in res["models"].items():
        L += [f"## Model: {model} ({m['runs']} runs)", "", "### Main analysis", ""] + block_md(m["main"])
        L += ["", "### For each rule (violations / runs, and runs with task success)", "",
              "| Rule | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
        L += [f"| {rule} | " + " | ".join(f"{v[a][0]}/{v[a][1]} ({v[a][2]})" for a in arms) + " |" for rule, v in m["by_rule"].items()]
        L += ["", "### Leave one rule out", "", "| Rule left out | " + " | ".join(p[0] for p in PLAN) + " |", "|---|---|---|---|"]
        L += [f"| {rule} | " + " | ".join(pp(v[p[0]]) for p in PLAN) + " |" for rule, v in m["leave_one_out"].items()]
        L += ["", "### Sensitivity 1: only runs with task success", ""] + block_md(m["success_only"])
        L += ["", "### Sensitivity 2: without the rules with places given by hand (P1, P5)", ""] + block_md(m["without_hand_rules"])
        L += ["", "### Cost (medians)", "", "| Arm | Tokens | Tool calls |", "|---|---|---|"]
        L += [f"| {a} | {v['median_tokens']} | {v['median_tool_calls']} |" for a, v in m["cost"].items()] + [""]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--out", default=".")
    ap.add_argument("--arms", default=",".join(ARMS))
    a = ap.parse_args(argv)
    arms = tuple(x for x in a.arms.split(",") if x)
    res = analyse(A.load(a.results), arms)
    md = markdown(res, arms)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "studyc.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    with open(os.path.join(a.out, "studyc.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
