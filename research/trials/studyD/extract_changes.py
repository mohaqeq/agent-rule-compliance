"""Study D: write, for each run, the files and line numbers that the run added or modified.

  python extract_changes.py OUT_DIR
Reads the run indexes and results of Study A and Study B (paths in SOURCES) and writes OUT_DIR/runs.json:
  [{key, study, model, run, rule_id, site, arm, violations, success, workspace, changed: {path: [lines]}}]
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRIALS = os.path.dirname(HERE)
SOURCES = [  # study, model, results file, runs directory
    ("A", "haiku", f"{TRIALS}/studyA/results/haiku/results-prereg.json", "D:/ucn-studya-runs/haiku"),
    ("A", "sonnet", f"{TRIALS}/studyA/results/sonnet/results-prereg.json", "D:/ucn-studya-runs/sonnet"),
    ("B", "haiku", f"{TRIALS}/studyB/results/haiku/results-all.json", "D:/work/b/h"),
    ("B", "sonnet", f"{TRIALS}/studyB/results/sonnet/results-all.json", "D:/work/b/s"),
]
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def git(ws, *args):
    return subprocess.run(["git", "-C", ws, "-c", "core.quotepath=off", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def changed_lines(ws, base):
    out = {}
    path = None
    for line in git(ws, "diff", "--unified=0", "--no-color", "--ignore-cr-at-eol", base, "--").splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif path and (m := HUNK.match(line)):
            start, count = int(m.group(1)), int(m.group(2) or 1)
            if count:
                out.setdefault(path, []).extend(range(start, start + count))
    for path in git(ws, "ls-files", "--others", "--exclude-standard").splitlines():  # new files that are not tracked
        full = os.path.join(ws, path)
        if os.path.isfile(full):
            with open(full, "rb") as fh:
                n = fh.read().count(b"\n") + 1
            out[path] = list(range(1, n + 1))
    return {p: sorted(set(v)) for p, v in sorted(out.items())}


def main():
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    runs = []
    for study, model, results, runs_dir in SOURCES:
        index = {e["run"]: e for e in json.load(open(f"{runs_dir}/index.json", encoding="utf-8"))}
        for r in json.load(open(results, encoding="utf-8")):
            e = index[r["run"]]
            ws = e["workspace"].replace("\\", "/")
            runs.append({"key": f"{study}-{model}-{r['run']}", "study": study, "model": model, "run": r["run"],
                         "rule_id": r["rule_id"], "site": r["site"], "arm": r.get("arm") or "none",
                         "violations": int(bool(r["violations"])), "success": r["success"], "workspace": ws,
                         "changed": changed_lines(ws, e["base_commit"])})
    json.dump(runs, open(f"{out_dir}/runs.json", "w", encoding="utf-8"), indent=1)
    print(len(runs), "runs;", sum(r["violations"] for r in runs), "violations;",
          sum(not r["changed"] for r in runs), "runs with no change")


main()
