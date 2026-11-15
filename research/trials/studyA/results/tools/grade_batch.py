"""Grade the runs of the given batches only: python grade_batch.py MODEL BATCH..."""
import json, os, sys
ROOT = "D:/personal/repos/unified-context-notation"
sys.path.insert(0, f"{ROOT}/research/harness")
import prove, recon
model, batches = sys.argv[1], sys.argv[2:]
runs = f"D:/ucn-studya-runs/{model}"
spec = json.load(open(f"D:/ucn-studya-runs/spec-{model}.json", encoding="utf-8"))
index = {e["run"]: e for e in json.load(open(f"{runs}/index.json"))}
for b in batches:
    out = f"{runs}/grade/{b}"
    if os.path.exists(f"{out}/results.json"):
        continue
    os.makedirs(out, exist_ok=True)
    batch = json.load(open(f"{runs}/batches/{b}.json", encoding="utf-8"))
    done = [index[r] for r, v in batch.items() if v.get("status") == "completed"]
    usage = {r: [v.get("tokens"), round((v.get("duration_ms") or 0) / 1000, 1), v.get("tool_uses")] for r, v in batch.items()}
    json.dump(done, open(f"{out}/index.json", "w"), indent=1)
    json.dump(usage, open(f"{out}/usage.json", "w"), indent=1)
    with prove.Postgres() as pg:
        recon.grade(dict(spec, grader_docker_args=pg.args, usage=f"{out}/usage.json"), out)
print("graded", batches)
