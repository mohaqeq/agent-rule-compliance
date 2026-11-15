"""Map every coding-agent transcript to its run by its exact prompt, and check model and workspace containment.

  python check.py RUNS_DIR SUBAGENTS_DIR  -> RUNS_DIR/runlog.json  {run: {agent_id, model, tool_calls, outside}}
The runners' own batch files are not trusted for the agent-to-run mapping.
"""
import glob
import json
import os
import re
import sys

runs, sub = sys.argv[1], sys.argv[2]
prompts = {open(p, encoding="utf-8").read().strip(): os.path.basename(p)[:-len(".prompt.txt")]
           for p in glob.glob(runs + "/*.prompt.txt")}
ABS = re.compile(r"(?<![A-Za-z0-9:/])(?:[A-Za-z]:[\\/]|/[a-z]/)[\w.\-\\/]{3,}")
log, dup = {}, []
for f in glob.glob(sub + "/agent-*.jsonl"):
    rows = []
    for line in open(f, encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    first = None
    for o in rows:
        m = o.get("message") or {}
        c = m.get("content")
        if m.get("role") == "user":
            first = (c if isinstance(c, str) else "".join(x.get("text", "") for x in c if isinstance(x, dict))).strip()
            break
    rid = prompts.get(first)
    if not rid:
        continue
    ws = re.search(r"repository at (\S+)", first).group(1).lower().rstrip("/")
    models, calls, outside = set(), 0, {}
    for o in rows:
        m = o.get("message") or {}
        if m.get("model"):
            models.add(m["model"])
        c = m.get("content")
        if not isinstance(c, list):
            continue
        for x in c:
            if not (isinstance(x, dict) and x.get("type") == "tool_use"):
                continue
            calls += 1
            name = x.get("name")
            if name in ("WebFetch", "WebSearch", "Agent"):
                outside["TOOL:" + name] = name
            inp = x.get("input") or {}
            for k in ("file_path", "path", "notebook_path", "command"):
                v = inp.get(k)
                if not isinstance(v, str):
                    continue
                if k == "command":  # the test command is the only permitted path outside the workspace
                    v = re.sub(r"(?i)python3?\s+d:[\/]work[\/]tools[\/]run_tests\.py", "python RUN_TESTS", v)
                for p in ABS.findall(v):
                    q = re.sub(r"^/([a-z])/", r"\1:/", p.replace("\\", "/").lower().strip())
                    if not q.startswith(ws) and not q.startswith(("c:/program files", "c:/windows")):
                        outside[q[:110]] = name
    e = {"agent_id": os.path.basename(f)[6:-6], "model": sorted(models), "tool_calls": calls,
         "outside": [f"{t}: {p}" for p, t in sorted(outside.items())]}
    if rid in log:
        dup.append(rid)
    log[rid] = e
json.dump(log, open(runs + "/runlog.json", "w", encoding="utf-8"), indent=1)
print(len(log), "runs with a transcript and an exact prompt; duplicates:", dup)
print("models:", sorted({m for e in log.values() for m in e["model"]}))
for r, e in sorted(log.items()):
    if e["outside"]:
        print(r, e["outside"][:6])
