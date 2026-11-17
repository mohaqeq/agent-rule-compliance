"""Study C, descriptive analyses 5 and 6 of the pre-registration.

  python repair_check.py RUNS_DIR RESULTS_JSON OUT_JSON
5. Repair: for N1, N2, N3 and P3, the Study D check runs on the complete files of the places (rules/<rule>/places.json)
   after the run. The base count is the number of findings in the same files before the run. A run is "clean" if the
   check finds nothing in those files, and "reduced" if it finds fewer than the base count.
6. Comments (mark arm): the number of mark comments that stay in the workspace, against the number of places.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRIALS = os.path.dirname(HERE)
SCAN_RULES = ("N1", "N2", "N3", "P3")
MARK_TEXT = "breaks a project rule and stays only until it is repaired"


def load(rule):
    spec = importlib.util.spec_from_file_location(f"check_{rule}", f"{TRIALS}/studyD/checks/{rule}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def findings(mod, ws, files):
    changed = {}
    for f in files:
        p = os.path.join(ws, f)
        if os.path.exists(p):
            with open(p, "rb") as fh:
                changed[f] = list(range(1, fh.read().count(b"\n") + 2))
    return len(mod.check(ws, changed))


def main():
    runs_dir, results, out = sys.argv[1:4]
    index = {e["run"]: e for e in json.load(open(f"{runs_dir}/index.json", encoding="utf-8"))}
    rows = json.load(open(results, encoding="utf-8"))
    mods = {r: load(r) for r in SCAN_RULES}
    places = {r: json.load(open(f"{HERE}/rules/{r}/places.json", encoding="utf-8"))["places"]
              for r in ("N1", "N2", "N3", "P1", "P3", "P5")}
    res = []
    for r in rows:
        e = index[r["run"]]
        ws, rule = e["workspace"], r["rule_id"]
        files = sorted({p["path"] for p in places[rule]})
        item = {"run": r["run"], "rule_id": rule, "arm": r["arm"], "violations": r["violations"]}
        if rule in SCAN_RULES:
            item["after"] = findings(mods[rule], ws, files)
        if r["arm"] == "mark":
            n = 0
            for f in files:
                p = os.path.join(ws, f)
                if os.path.exists(p):
                    n += open(p, encoding="utf-8", errors="replace").read().count(MARK_TEXT)
            item["marks_left"], item["marks"] = n, len(places[rule])
        res.append(item)
    for rule in SCAN_RULES:  # base count: the prepared base of the task, without marks
        base_ws = f"{runs_dir}/_base/{rule}-contradicting"
        b = findings(mods[rule], base_ws, sorted({p["path"] for p in places[rule]}))
        for item in res:
            if item["rule_id"] == rule:
                item["base"] = b
                item["clean"] = item["after"] == 0
                item["reduced"] = item["after"] < b
    json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
    summary = {}
    for item in res:
        if "after" in item:
            k = summary.setdefault(item["arm"], {"runs": 0, "clean": 0, "reduced": 0})
            k["runs"] += 1
            k["clean"] += item["clean"]
            k["reduced"] += item["reduced"]
    print("repair (N1, N2, N3, P3):", summary)
    marks = [i for i in res if "marks_left" in i]
    print("mark arm: runs that removed or lost a comment:",
          sum(i["marks_left"] < i["marks"] for i in marks), "of", len(marks))


main()
