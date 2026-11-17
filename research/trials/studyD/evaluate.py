"""Study D: run the static checks on the change of each run and report recall and false alarms.

  python evaluate.py RUNS_JSON CHECKS_DIR OUT_DIR
RUNS_JSON comes from extract_changes.py. CHECKS_DIR has one <RULE>.py for each rule, with CLASS, NOTES and check().
Writes OUT_DIR/findings.json (one row for each run) and OUT_DIR/studyd.md.
"""
import collections
import importlib.util
import json
import os
import sys

RULES = ("N1", "N2", "N3", "P1", "P3", "P5")
SITES = ("consistent", "control", "none", "contradicting")


def load(checks_dir):
    mods = {}
    for r in RULES:
        spec = importlib.util.spec_from_file_location(f"check_{r}", os.path.join(checks_dir, f"{r}.py"))
        mods[r] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mods[r])
    return mods


def pct(a, b):
    return f"{a} / {b} ({100 * a / b:.1f}%)" if b else "none"


def table(rows, key, values, label):
    lines = [f"| {label} | Violations found (recall) | Runs without violation that got a finding (false alarms) |", "|---|---|---|"]
    for v in values:
        x = [r for r in rows if r[key] == v]
        if x:
            viol = [r for r in x if r["violations"]]
            clean = [r for r in x if not r["violations"]]
            lines.append(f"| {v} | {pct(sum(r['found'] for r in viol), len(viol))} | {pct(sum(r['found'] for r in clean), len(clean))} |")
    return lines


def main():
    runs = json.load(open(sys.argv[1], encoding="utf-8"))
    mods = load(sys.argv[2])
    out_dir = sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    errors = collections.Counter()
    for r in runs:
        r["findings"], r["other"] = [], {}
        for rule, mod in mods.items():
            try:
                res = [str(x) for x in mod.check(r["workspace"], {p: list(v) for p, v in r["changed"].items()})]
            except Exception as exc:  # an error counts as "nothing found"
                errors[rule] += 1
                res = []
                r.setdefault("errors", {})[rule] = f"{type(exc).__name__}: {exc}"[:200]
            if rule == r["rule_id"]:
                r["findings"] = res[:20]
            elif res:
                r["other"][rule] = res[:5]
        r["found"] = int(bool(r["findings"]))
    json.dump([{k: v for k, v in r.items() if k not in ("workspace", "changed")} for r in runs],
              open(f"{out_dir}/findings.json", "w", encoding="utf-8"), indent=1)

    viol = [r for r in runs if r["violations"]]
    clean = [r for r in runs if not r["violations"]]
    recall = sum(r["found"] for r in viol) / len(viol)
    alarms = sum(r["found"] for r in clean) / len(clean)
    decision = "REFUTED" if recall < 0.30 else ("SUPPORTED" if alarms <= 0.10 else "INCONCLUSIVE")
    md = [f"Study D: {len(runs)} runs, {len(viol)} violations", "",
          "## Checks as delivered", "", "| Rule | Class | Notes of the author | Errors |", "|---|---|---|---|"]
    md += [f"| {r} | {mods[r].CLASS} | {' '.join(str(mods[r].NOTES).split())} | {errors[r]} |" for r in RULES]
    md += ["", "## All rules", "",
           f"- Recall: {pct(sum(r['found'] for r in viol), len(viol))}",
           f"- False alarms: {pct(sum(r['found'] for r in clean), len(clean))}",
           f"- H5: {decision}", "", "## For each rule", ""] + table(runs, "rule_id", RULES, "Rule")
    md += ["", "## For each site type", ""] + table(runs, "site", SITES, "Site")
    md += ["", "## For each study and model", ""]
    for r in runs:
        r["sm"] = f"{r['study']} {r['model']}"
    md += table(runs, "sm", sorted({r["sm"] for r in runs}), "Study and model")
    md += ["", "## Only runs with task success", ""] + table([r for r in runs if r["success"]], "rule_id", RULES, "Rule")
    cross = collections.Counter()
    for r in runs:
        for rule in r["other"]:
            cross[(rule, r["rule_id"])] += 1
    md += ["", "## Cross-rule findings (the check of one rule on runs of a different rule; not confirmed by a grader)", "",
           "| Check | Runs of rule | Runs with a finding |", "|---|---|---|"]
    md += [f"| {a} | {b} | {n} |" for (a, b), n in sorted(cross.items())] or ["| none | | |"]
    open(f"{out_dir}/studyd.md", "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    print("\n".join(md))


main()
