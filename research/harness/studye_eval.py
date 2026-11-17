"""Study E analysis: contrasts between cells, for each model.

  python studye_eval.py RESULTS.json [...] --contrasts a-b,c-d [--primary a-b,...] [--out DIR]

The cell of a row is its site (for example consistent, onewrong, repaired, contradicting) when its arm is `none`,
and its arm otherwise (prose, rule, mark, warn). A contrast `a-b` is the difference of violation rates a − b with a
95% cluster bootstrap over rules and a permutation test within rules (the functions of studya_eval.py).
A primary contrast `a-b` gets the decision LOWER (upper bound below 0), HIGHER (lower bound above 0) or NOT SHOWN.
Rows with violations = None (no measure) are left out and counted.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studya_eval as A  # noqa: E402
import studyb_eval as B  # noqa: E402


def cell(r):
    return r.get("site") if (r.get("arm") or "none") == "none" else r["arm"]


def decide(c):
    if not c["available"] or not c.get("ci"):
        return B.NA
    if B.ceiling_or_floor(c["rate_a"], c["rate_b"]):
        return "INCONCLUSIVE (ceiling or floor)"
    if c["ci"][1] < 0:
        return "LOWER"
    if c["ci"][0] > 0:
        return "HIGHER"
    return "NOT SHOWN"


def analyse(rows, contrasts, primary):
    used = [dict(r, site=cell(r)) for r in rows if r.get("violations") is not None and r.get("rule_id")]
    out = {"analysed": len(used), "no_measure": [r["run"] for r in rows if r.get("violations") is None], "models": {}}
    for model in sorted({r.get("agent_model") or "unknown" for r in used}):
        g = [r for r in used if (r.get("agent_model") or "unknown") == model]
        cells = sorted({r["site"] for r in g})
        m = {"cells": {c: {"violations": sum(1 for r in g if r["site"] == c and r["violations"]),
                           "runs": sum(1 for r in g if r["site"] == c),
                           "success": sum(r["success"] for r in g if r["site"] == c)} for c in cells},
             "by_rule": {rule: {c: [sum(1 for r in g if r["rule_id"] == rule and r["site"] == c and r["violations"]),
                                    sum(1 for r in g if r["rule_id"] == rule and r["site"] == c),
                                    sum(r["success"] for r in g if r["rule_id"] == rule and r["site"] == c)] for c in cells}
                         for rule in sorted({r["rule_id"] for r in g})},
             "contrasts": [], "success_only": []}
        for label in contrasts:
            a, b = label.split("-", 1)
            for key, data in (("contrasts", g), ("success_only", [r for r in g if r["success"]])):
                c = B.compare(data, a, b, label)
                c["decision"] = decide(c) if label in primary else "descriptive"
                m[key].append(c)
        out["models"][model] = m
    return out


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def pp(x):
    return "n/a" if x is None else f"{100 * x:+.1f} pp"


def ctable(cs):
    L = ["| Difference | Rate a | Rate b | Estimate | 95% interval | Permutation p | Decision |", "|---|---|---|---|---|---|---|"]
    for c in cs:
        ci = f"[{pp(c['ci'][0])}, {pp(c['ci'][1])}]" if c.get("ci") else "n/a"
        p = "n/a" if c.get("p") is None else f"{c['p']:.4f}"
        L.append(f"| {c['contrast']} | {pct(c['rate_a'])} | {pct(c['rate_b'])} | {pp(c['diff'])} | {ci} | {p} | {c['decision']} |")
    return L


def markdown(res):
    L = [f"Study E: {res['analysed']} runs analysed; runs without a measure: {res['no_measure'] or 'none'}", ""]
    for model, m in res["models"].items():
        cells = list(m["cells"])
        L += [f"## Model: {model}", "", "| Cell | Violations | Rate | Task success |", "|---|---|---|---|"]
        L += [f"| {c} | {v['violations']} / {v['runs']} | {pct(v['violations'] / v['runs'] if v['runs'] else None)} | "
              f"{v['success']} / {v['runs']} |" for c, v in m["cells"].items()]
        L += ["", "### Contrasts", ""] + ctable(m["contrasts"])
        L += ["", "### For each rule (violations / runs, runs with task success)", "", "| Rule | " + " | ".join(cells) + " |",
              "|---|" + "---|" * len(cells)]
        L += [f"| {rule} | " + " | ".join(f"{v[c][0]}/{v[c][1]} ({v[c][2]})" for c in cells) + " |" for rule, v in m["by_rule"].items()]
        L += ["", "### Sensitivity: only runs with task success", ""] + ctable(m["success_only"]) + [""]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--contrasts", required=True)
    ap.add_argument("--primary", default="")
    ap.add_argument("--out", default=".")
    a = ap.parse_args(argv)
    contrasts = [x for x in a.contrasts.split(",") if x]
    primary = {x for x in a.primary.split(",") if x}
    res = analyse(A.load(a.results), contrasts, primary)
    md = markdown(res)
    os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, "studye.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    open(os.path.join(a.out, "studye.md"), "w", encoding="utf-8", newline="\n").write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
