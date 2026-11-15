"""Neutral test command for coding agents: python run_tests.py TOKEN [pytest arguments].

Copy this file to a folder outside the repository (Study B: D:/work/tools/run_tests.py). The prompt names that copy,
so the command does not show the name of this repository. Set HARNESS and RUNS for the machine.
"""
import json
import os
import subprocess
import sys

HARNESS = "D:/personal/repos/agent-rule-compliance/research/harness/agent_tests.py"
RUNS = ["D:/work/b/h", "D:/work/b/s"]

if len(sys.argv) < 2:
    sys.exit("usage: run_tests.py TOKEN [pytest arguments]")
for runs in RUNS:
    index = os.path.join(runs, "index.json")
    if os.path.exists(index) and any(sys.argv[1] in e["workspace"].replace("\\", "/").split("/")
                                     for e in json.load(open(index, encoding="utf-8"))):
        sys.exit(subprocess.call([sys.executable, HARNESS, runs, *sys.argv[1:]]))
sys.exit("unknown workspace token")
