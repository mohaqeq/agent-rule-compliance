"""Fill the site table and the hashes into a pre-registration, and write the blind counts next to the tasks.

  python research/harness/studya_pin.py STUDY_DIR KEY.json COUNTS.json...

STUDY_DIR holds PREREGISTRATION.md (with <!--SITES--> and <!--HASHES--> markers), tasks/ and sites/. KEY.json maps the
neutral item keys of site_items.py to task directories; COUNTS files are the blind counter's output (later files win).
Exits 1 if a cell does not meet the definition of its condition.
"""
import hashlib
import json
import os
import sys


def condition(follow, brk):
    n = follow + brk
    if n == 0:
        return "none"
    if n >= 3 and follow / n >= 0.8:
        return "consistent"
    if n >= 3 and brk / n >= 0.6:
        return "contradicting"
    return "mixed"


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def main(argv):
    study, key_file, count_files = argv[0], argv[1], argv[2:]
    counts = {}
    for f in count_files:
        for x in json.load(open(f, encoding="utf-8")):
            counts[x["key"]] = x
    key = json.load(open(key_file, encoding="utf-8"))
    by_task = {t: counts[k] for k, ts in key.items() for t in ts}
    tasks = os.path.join(study, "tasks")
    rows, bad, blind = [], [], {}
    for t in sorted(os.listdir(tasks)):
        meta = json.load(open(os.path.join(tasks, t, "meta.json"), encoding="utf-8"))
        c = by_task[t]["app"]
        got = condition(c["follow"], c["break"])
        want = "consistent" if meta["site"] == "control" else meta["site"]
        seed = "seeded" if os.path.exists(os.path.join(tasks, t, "seed.patch")) else "natural"
        if meta["site"] == "control":
            seed = "neutral patch"
        rows.append(f"| {t} | {meta['half']} | {meta['site']} | {seed} | `{c.get('package', '')}` | {c['follow']} | {c['break']} | {got} |")
        blind[t] = by_task[t]
        if got != want:
            bad.append(f"{t}: wanted {want}, blind count gives {got} ({c['follow']}/{c['break']})")
    sites = ("Precedents are the blind counter's, over the feature package ([sites/blind-counts.json](sites/blind-counts.json)).\n\n"
             "| Task | Half | Site | Base | Package | Follow | Break | Blind count gives |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(rows))
    with open(os.path.join(study, "sites", "blind-counts.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(blind, fh, indent=1)
        fh.write("\n")
    files = []
    for root in ("tasks", "sites", "review", "spec.json"):
        p = os.path.join(study, root)
        if os.path.isfile(p):
            files.append(p)
        for d, _, names in os.walk(p):
            files += [os.path.join(d, n) for n in names if "__pycache__" not in d and n != "proof.json"]
    harness = os.path.join(study, "..", "..", "harness")
    files += [os.path.join(harness, n) for n in ("recon.py", "prove.py", "studya_eval.py", "studya_mixed.py")]
    lines = [f"| {os.path.relpath(f, study).replace(os.sep, '/')} | `{sha(f)}` |" for f in sorted(files)]
    hashes = ("SHA-256 of each file with LF line endings. `proof.json` files are not pinned (they hold timings).\n\n"
              "| File | SHA-256 |\n|---|---|\n" + "\n".join(lines))
    p = os.path.join(study, "PREREGISTRATION.md")
    s = open(p, encoding="utf-8").read()
    for marker, text in (("<!--SITES-->", sites), ("<!--HASHES-->", hashes)):
        if marker not in s:
            raise SystemExit(f"{marker} not found (already pinned?)")
        s = s.replace(marker, text)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(s)
    print(f"{len(rows)} tasks, {len(lines)} files pinned")
    for b in bad:
        print("NOT MET:", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
