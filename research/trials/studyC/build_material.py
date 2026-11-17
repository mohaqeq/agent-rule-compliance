"""Study C: build the mark patch and the warning text of each rule.

  python build_material.py BASES_DIR
BASES_DIR has one prepared base for each task (<rule>-contradicting), as recon.py makes it (seed applied).
For each rule the tool finds the places of old code that breaks the rule:
  - with the static check of Study D (trials/studyD/checks/<rule>.py) on the complete non-test Python files that the
    naive solution of the task modifies; or
  - from hand_places.json, when the check finds nothing there.
There is one place for each function that has a finding. The tool writes rules/<rule>/places.json, mark.patch and warn.md.
"""
import ast
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRIALS = os.path.dirname(HERE)
RULES = ("N1", "N2", "N3", "P1", "P3", "P5")
MARK = ("# NOTE: the code below breaks a project rule and stays only until it is repaired. Do not copy it.",
        "# Rule: {sentence}")
WARN = ("A scan of the project found old code near this change that breaks a project rule. That code stays only "
        "until it is repaired. Do not copy it.\n\nRule: {sentence}\n\nPlaces:\n{places}\n")


def scan(rule, base):
    spec = importlib.util.spec_from_file_location(f"check_{rule}", f"{TRIALS}/studyD/checks/{rule}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    naive = f"{TRIALS}/studyA/tasks/{rule}-contradicting/naive.patch"
    files = sorted({l[6:].strip() for l in open(naive, encoding="utf-8") if l.startswith("+++ b/")})
    files = [f for f in files if f.endswith(".py") and "/tests/" not in f and os.path.exists(f"{base}/{f}")]
    changed = {}
    for f in files:
        with open(f"{base}/{f}", "rb") as fh:
            changed[f] = list(range(1, fh.read().count(b"\n") + 2))
    out = []
    for finding in mod.check(base, changed):
        m = re.match(r"([^:]+):(\d+):", finding)
        out.append({"path": m.group(1), "line": int(m.group(2))})
    return out


def anchor(tree, line):
    """(function name, line to put the comment above) for a finding at `line`."""
    func, stmt = None, None
    for node in ast.walk(tree):
        if not hasattr(node, "lineno") or not (node.lineno <= line <= getattr(node, "end_lineno", node.lineno)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (func is None or node.lineno >= func.lineno):
            func = node
        if isinstance(node, ast.stmt) and (stmt is None or node.lineno >= stmt.lineno):
            stmt = node
    if func is not None and (stmt is func or line < func.body[0].lineno):  # the finding is in the signature
        return func.name, min([d.lineno for d in func.decorator_list] + [func.lineno])
    return (func.name if func else "module level"), stmt.lineno


def main():
    bases = sys.argv[1]
    sentences = json.load(open(f"{HERE}/sentences.json", encoding="utf-8"))
    hand = json.load(open(f"{HERE}/hand_places.json", encoding="utf-8"))
    for rule in RULES:
        base = f"{bases}/{rule}-contradicting"
        found = scan(rule, base)
        source = "scan" if found else "hand"
        places, seen = [], set()
        for p in sorted(found or hand[rule], key=lambda x: (x["path"], x["line"])):
            text = open(f"{base}/{p['path']}", encoding="utf-8").read()
            name, at = anchor(ast.parse(text), p["line"])
            if (p["path"], name) in seen:  # one place for each function
                continue
            seen.add((p["path"], name))
            places.append({"path": p["path"], "line": p["line"], "function": name, "comment_above": at})
        out = f"{HERE}/rules/{rule}"
        os.makedirs(out, exist_ok=True)
        json.dump({"source": source, "places": places}, open(f"{out}/places.json", "w", encoding="utf-8"), indent=1)
        # the mark patch: comments above each place, made in the base and taken back out
        by_file = {}
        for p in places:
            by_file.setdefault(p["path"], []).append(p["comment_above"])
        originals = {}
        for path, lines in by_file.items():
            with open(f"{base}/{path}", "rb") as fh:
                originals[path] = fh.read()
            eol = "\r\n" if b"\r\n" in originals[path] else "\n"
            src = originals[path].decode("utf-8").split(eol)
            for at in sorted(set(lines), reverse=True):
                indent = re.match(r"\s*", src[at - 1]).group(0)
                src[at - 1:at - 1] = [indent + m.format(sentence=sentences[rule]) for m in MARK]
            new = eol.join(src)
            ast.parse(new)  # the marked file must still be valid Python
            with open(f"{base}/{path}", "wb") as fh:
                fh.write(new.encode("utf-8"))
        diff = subprocess.run(["git", "-C", base, "-c", "core.autocrlf=false", "diff", "--no-color", "--"] + list(by_file),
                              capture_output=True).stdout
        for path, data in originals.items():
            with open(f"{base}/{path}", "wb") as fh:
                fh.write(data)
        with open(f"{out}/mark.patch", "wb") as fh:
            fh.write(diff)
        listing = "\n".join(f"- {p['path']}:{p['line']} (in `{p['function']}`)" for p in places)
        with open(f"{out}/warn.md", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(WARN.format(sentence=sentences[rule], places=listing))
        print(rule, source, len(places), "places,", len(by_file), "files, patch bytes", len(diff))


main()
