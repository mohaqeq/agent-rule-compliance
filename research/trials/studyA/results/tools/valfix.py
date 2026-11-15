"""Recompute 'new validator findings' without line numbers: a finding counts as new only if the run has more findings
for the same (file, rule text) than its (seeded) baseline. Fixes false positives from line shifts in seeded files."""
import json, os, re, shutil, sys, glob, collections
ROOT = "D:/personal/repos/unified-context-notation"
sys.path.insert(0, f"{ROOT}/ucn"); sys.path.insert(0, f"{ROOT}/research/harness")
import ucn_validate
model = sys.argv[1]
runs = f"D:/ucn-studya-runs/{model}"
MODEL = f"{ROOT}/research/trials/saleor/model.ucn"
def findings(ws):
    gm = os.path.join(ws, "_m.ucn"); shutil.copy(MODEL, gm)
    try:
        b = ucn_validate.validate(gm, today="2026-11-14")
    finally:
        os.remove(gm)
    return collections.Counter(re.sub(r":\d+ ", ": ", f["message"]) for f in b["findings"] if f["class"] in ("VIOLATION", "CONFLICT"))
index = {e["run"]: e for e in json.load(open(f"{runs}/index.json"))}
out, base = {}, {}
for f in sorted(glob.glob(f"{runs}/grade/*/results.json")):
    gdir = os.path.dirname(f)
    for r in json.load(open(f)):
        if not r.get("validator_new"):
            continue
        task = r["task"]
        bdir = os.path.join(gdir, f"_baseline-{task}") if os.path.exists(os.path.join(gdir, f"_baseline-{task}")) else os.path.join(gdir, "_baseline")
        if bdir not in base:
            base[bdir] = findings(bdir)
        now = findings(index[r["run"]]["workspace"])
        new = sorted((now - base[bdir]).elements())
        out[r["run"]] = {"reported": r["validator_new"], "new_without_line_numbers": new}
        print(r["run"], len(r["validator_new"]), "->", len(new), flush=True)
json.dump(out, open(f"{runs}/validator_fix.json", "w"), indent=1)
