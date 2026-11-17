"""Run openrouter_agent.py for many runs, a few at a time, and stop at a cost limit.

  python openrouter_batch.py RUNS_DIR --model MODEL [--parallel 4] [--max-cost 8.0] [--only RUN_ID ...]

Runs that have a record in RUNS_DIR/records are skipped. The cost limit counts the cost of the records in RUNS_DIR.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def spent(runs_dir):
    return sum(json.load(open(f)).get("cost", 0) for f in glob.glob(f"{runs_dir}/records/*.json"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("--model", required=True)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--max-cost", type=float, default=8.0)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    runs = [e["run"] for e in json.load(open(f"{a.runs_dir}/index.json", encoding="utf-8"))]
    if a.only:
        runs = [r for r in runs if r in a.only]
    todo = [r for r in runs if not os.path.exists(f"{a.runs_dir}/records/{r}.json")]
    live = {}
    while todo or live:
        for r, p in list(live.items()):
            if p.poll() is not None:
                del live[r]
                print("done", r, p.returncode, flush=True)
        if spent(a.runs_dir) >= a.max_cost:
            print("cost limit reached; no new runs", flush=True)
            todo = []
        while todo and len(live) < a.parallel:
            r = todo.pop(0)
            log = open(f"{a.runs_dir}/agent-{r}.log", "w")
            live[r] = subprocess.Popen([sys.executable, f"{HERE}/openrouter_agent.py", a.runs_dir, r, "--model", a.model],
                                       stdout=log, stderr=subprocess.STDOUT)
        time.sleep(5)
    print("spent", round(spent(a.runs_dir), 4))


if __name__ == "__main__":
    sys.exit(main())
