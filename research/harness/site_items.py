"""Build the input for blind site coding: one neutral item per (rule, package, seed), with no condition label.

  python research/harness/site_items.py TASKS_DIR SITES.json... OUT_DIR

Writes OUT_DIR/items.json (what the coder sees), OUT_DIR/<key>.seed.patch, and OUT_DIR/key.json (item key -> task
directories; the coder must not read it).
"""
import collections
import hashlib
import json
import os
import re
import shutil
import sys


def package_of(patch):
    """The package a task's reference changes: the most common directory of the non-test files it touches."""
    dirs = collections.Counter()
    for m in re.finditer(r"^\+\+\+ b/(\S+)", open(patch, encoding="utf-8").read(), re.M):
        f = m.group(1)
        if f.endswith(".py") and "/tests/" not in f and "/migrations/" not in f and not os.path.basename(f).startswith("test_"):
            dirs[os.path.dirname(f)] += 1
    return dirs.most_common(1)[0][0] if dirs else ""


def main(argv):
    tasks, sites, out = argv[0], argv[1:-1], argv[-1]
    rules = {}
    for s in sites:
        for r in json.load(open(s, encoding="utf-8"))["rules"]:
            rules[r["id"]] = r
    os.makedirs(out, exist_ok=True)
    items, key = {}, collections.defaultdict(list)
    for t in sorted(os.listdir(tasks)):
        d = os.path.join(tasks, t)
        if not os.path.isfile(os.path.join(d, "meta.json")):
            continue
        meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
        seed = os.path.join(d, "seed.patch")
        seed_sha = hashlib.sha256(open(seed, "rb").read()).hexdigest() if os.path.exists(seed) else ""
        pkg = package_of(os.path.join(d, "reference.patch"))
        k = "S" + hashlib.sha256(f"{meta['rule_id']}|{pkg}|{seed_sha}".encode()).hexdigest()[:8]
        key[k].append(t)
        if k in items:
            continue
        r = rules[meta["rule_id"]]
        items[k] = {"key": k, "rule": r["statement"], "source": r["source"], "signature": r["signature"],
                    "package": pkg, "patch_to_apply_first": f"{k}.seed.patch" if seed_sha else None}
        if seed_sha:
            shutil.copyfile(seed, os.path.join(out, f"{k}.seed.patch"))
    ordered = sorted(items.values(), key=lambda i: i["key"])
    json.dump(ordered, open(os.path.join(out, "items.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    json.dump(key, open(os.path.join(out, "key.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(len(ordered), "items for", sum(len(v) for v in key.values()), "tasks")


if __name__ == "__main__":
    main(sys.argv[1:])
