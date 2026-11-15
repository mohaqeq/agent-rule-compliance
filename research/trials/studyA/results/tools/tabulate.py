"""python tabulate.py MODEL: merge graded batches, apply the validator correction, write three result files, print cells."""
import collections
import glob
import json
import sys

model = sys.argv[1]
REV = "D:/personal/repos/unified-context-notation/research/trials/studyA/review/"
rows = []
for f in sorted(glob.glob(f"{model}/grade/*/results.json")):
    rows += json.load(open(f))
fix = json.load(open(f"{model}/validator_fix.json"))
flag = collections.defaultdict(set)
for f in ("grader-review.json", "grader-review-cohere.json"):
    for t, r in json.load(open(REV + f)).items():
        for x in r.get("over_specified", []):
            flag[t].add((x.get("test") or "").split("[")[0])
out = {"prereg": [], "corrected": [], "unflagged": []}
for r in rows:
    rf = r.get("rule_failed") or []
    vn = fix[r["run"]]["new_without_line_numbers"] if r["run"] in fix else (r.get("validator_new") or [])
    out["prereg"].append(dict(r))
    b = dict(r, violations=int(bool(rf) or bool(vn) or bool(r.get("tampered"))), validator_new=vn)
    out["corrected"].append(b)
    rf2 = [t for t in rf if t.split("[")[0] not in flag[r["task"]]]
    out["unflagged"].append(dict(b, violations=int(bool(rf2) or bool(vn))))
for k, v in out.items():
    json.dump(v, open(f"{model}/results-{k}.json", "w"), indent=1)
SITES = ("consistent", "control", "none", "contradicting")
print(len(rows), "runs")
for k, v in out.items():
    c = collections.defaultdict(lambda: [0, 0, 0])
    for r in v:
        x = c[(r["rule_id"], r["site"])]
        x[0] += r["violations"]
        x[1] += 1
        x[2] += r["success"]
    print("==", k)
    for rule in ("N1", "N2", "N3", "P1", "P3", "P5"):
        print(" ", rule, " ".join(f"{s[:6]}={c[(rule, s)][0]}/{c[(rule, s)][1]}(ok{c[(rule, s)][2]})" for s in SITES if (rule, s) in c))
    for s in SITES:
        print("  TOTAL", s, sum(x[0] for (_, s_), x in c.items() if s_ == s), "/", sum(x[1] for (_, s_), x in c.items() if s_ == s))
