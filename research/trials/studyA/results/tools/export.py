"""python export.py REPO_RESULTS_DIR SUBAGENTS_DIR: copy the Study A results into the repository, with sensitivity files and tool-call logs."""
import collections
import json
import os
import re
import shutil
import statistics
import sys

OUT = sys.argv[1]
SUB = sys.argv[2].rstrip("/") + "/"
SITES = ("consistent", "control", "none", "contradicting")
USER = re.compile(r"(?i)([\\/]+users[\\/]+)[^\\/\"]+")


def clean(s):
    return USER.sub(r"\1<user>", s)


for m in ("haiku", "sonnet"):
    d = os.path.join(OUT, m)
    os.makedirs(d, exist_ok=True)
    log = json.load(open(f"{m}/runlog.json"))
    rows = json.load(open(f"{m}/results-prereg.json"))
    for k in ("prereg", "corrected", "unflagged"):
        shutil.copy(f"{m}/results-{k}.json", d)
        for f in ("studya.md", "studya.json"):
            src = f"{m}/eval-{k}/{f}"
            if os.path.exists(src):
                shutil.copy(src, os.path.join(d, f"analysis-{k}{os.path.splitext(f)[1]}"))
    json.dump([r for r in rows if r["success"]], open(os.path.join(d, "results-success-only.json"), "w"), indent=1)
    out_runs = {r for r, e in log.items() if e["outside"]}
    json.dump([r for r in rows if r["run"] not in out_runs], open(os.path.join(d, "results-no-outside.json"), "w"), indent=1)
    json.dump(json.loads(clean(json.dumps(json.load(open(f"{m}/validator_fix.json"))))),
              open(os.path.join(d, "validator_fix.json"), "w"), indent=1)
    json.dump(json.loads(clean(json.dumps(log))), open(os.path.join(d, "runlog.json"), "w"), indent=1)
    with open(os.path.join(d, "tool-calls.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for run in sorted(log):
            calls = []
            for line in open(SUB + "agent-" + log[run]["agent_id"] + ".jsonl", encoding="utf-8"):
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                c = (o.get("message") or {}).get("content")
                if not isinstance(c, list):
                    continue
                for x in c:
                    if isinstance(x, dict) and x.get("type") == "tool_use":
                        inp = x.get("input") or {}
                        arg = inp.get("file_path") or inp.get("path") or inp.get("command") or inp.get("pattern") or ""
                        if inp.get("pattern") and inp.get("path"):
                            arg = f"{inp['pattern']} in {inp['path']}"
                        calls.append([x.get("name"), clean(str(arg))[:300]])
            fh.write(json.dumps({"run": run, "model": log[run]["model"], "calls": calls}, ensure_ascii=False) + "\n")
    c = collections.defaultdict(lambda: [[], []])
    for r in rows:
        c[r["site"]][0].append(r.get("tokens") or 0)
        c[r["site"]][1].append(log[r["run"]]["tool_calls"])
    print(m, "median tokens / median tool calls")
    for s in SITES:
        print("  ", s, round(statistics.median(c[s][0])), statistics.median(c[s][1]))
    print("   size tool-calls.jsonl", os.path.getsize(os.path.join(d, "tool-calls.jsonl")))
