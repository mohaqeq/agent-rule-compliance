# Brief: write static checks for six project rules

You write one static check for each of six rules of a Python project (saleor, a Django shop system).
A team wants to run these checks on each change, before the change is merged.

## What you get

- `RULES_DIR/<ID>.md`: the text of each rule, as the project documents it. The ids are N1, N2, N3, P1, P3, P5.
- `REPO`: a clean copy of the codebase. You can read it. Do not change it.

Read nothing else on this machine. Do not use the web.

## What you deliver

For each rule, one file `OUT_DIR/<ID>.py` with:

```python
CLASS = "import" | "pattern" | "none"
NOTES = "one or two sentences: what the check looks for, and what it cannot see"

def check(workspace, changed):
    """workspace: path of a checkout of the project with one change applied (not committed).
    changed: dict {relative posix path: sorted list of 1-based line numbers that the change added or modified}.
             Only changed and new files are in the dict. Deleted lines are not listed.
    Return a list of strings, one for each finding: "path:line: message". Return [] if the change obeys the rule."""
```

Requirements:

1. **Static only.** Read files. Do not import or run the project, and do not start processes. Use only the Python
   standard library (`ast`, `re`, `tokenize` and so on).
2. **Judge the change, not the old code.** The codebase can contain old violations of a rule. Report a finding only
   for code that the change added or modified. You can read all other code of the workspace for context.
3. **Ignore test files** (paths with `/tests/` or files named `test_*.py` or `conftest.py`).
4. **General.** You do not know which changes the team will make. The check must work for any change that the rule
   applies to, in any part of the codebase.
5. **Precision is important.** A check that reports correct code makes the team ignore it. If you cannot write a
   static check with acceptable precision for a rule, set `CLASS = "none"`, return `[]`, and say why in `NOTES`.
   A narrow check that finds only a part of the violations is acceptable: say in `NOTES` what it misses.
6. `CLASS = "import"` is for a check on module dependencies. `CLASS = "pattern"` is for a check on text or on the
   syntax tree.
7. A check must not stop with an exception on a file that it cannot parse. It must finish in a few seconds.

You can test your checks on the clean codebase: make a temporary copy of single files in your own temporary folder,
or call `check(REPO, {...})` with line numbers of existing code. Do not change `REPO`.

## Report

Reply with one short paragraph for each rule: the class, what the check looks for, and what it misses.
