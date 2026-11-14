"""Print a markdown table of path and SHA-256 for every file under the given directories, sorted.
  python research/harness/hash_tree.py DIR [DIR ...]
Line endings are assumed to be \n (see .gitattributes): files are hashed as they are on disk."""
import hashlib
import os
import sys


def tree(dirs):
    rows = []
    for d in dirs:
        for base, names, files in os.walk(d):
            names[:] = [n for n in names if n != ".git"]
            for f in files:
                p = os.path.join(base, f)
                with open(p, "rb") as fh:
                    rows.append((p.replace("\\", "/"), hashlib.sha256(fh.read()).hexdigest()))
    return sorted(rows)


def table(dirs):
    return "\n".join(["| Path | SHA-256 |", "|---|---|"] + [f"| {p} | {h} |" for p, h in tree(dirs)]) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: hash_tree.py DIR [DIR ...]")
    sys.stdout.write(table(sys.argv[1:]))
