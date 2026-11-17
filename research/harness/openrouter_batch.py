"""Run openrouter_agent.py for many runs, a few at a time. Free models only.

  python openrouter_batch.py RUNS_DIR --model MODEL:free [--parallel 2] [--max-turns 50] [--only RUN_ID ...]

Runs that have a record in RUNS_DIR/records are skipped. Before each new run the tool reads the daily limit of free
requests of the key. It starts a run only if the remaining requests are enough for a full run (max turns + 10), so a
run does not stop in the middle because of the limit. Any recorded cost above 0 stops the batch.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def spent(runs_dir):
    return sum(json.load(open(f)).get("cost", 0) for f in glob.glob(f"{runs_dir}/records/*.json"))


def free_remaining():
    key = open(os.path.expanduser("~/.openrouter_key"), encoding="utf-8").read().strip()
    req = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"Authorization": "Bearer " + key})
    d = json.load(urllib.request.urlopen(req, timeout=30))["data"]
    return (d.get("free_model_daily_requests") or {}).get("remaining", 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("--model", required=True)
    ap.add_argument("--parallel", type=int, default=2)
    ap.add_argument("--max-turns", type=int, default=50)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    if not a.model.endswith(":free"):
        sys.exit("refused: free models only")
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
        if spent(a.runs_dir) > 0:
            print("a run has a cost above 0; stop", flush=True)
            todo = []
        while todo and len(live) < a.parallel:
            if free_remaining() < (a.max_turns + 10) * (len(live) + 1):
                print("not enough free requests today; stop starting runs", flush=True)
                todo = []
                break
            r = todo.pop(0)
            log = open(f"{a.runs_dir}/agent-{r}.log", "w")
            live[r] = subprocess.Popen([sys.executable, f"{HERE}/openrouter_agent.py", a.runs_dir, r, "--model", a.model,
                                        "--max-turns", str(a.max_turns)], stdout=log, stderr=subprocess.STDOUT)
        time.sleep(5)
    print("cost", round(spent(a.runs_dir), 4), "free requests left", free_remaining())


if __name__ == "__main__":
    sys.exit(main())
