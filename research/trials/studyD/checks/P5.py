"""P5: gift card balance changes must be atomic, not a read-modify-write in application code."""

import ast
import os
import re

CLASS = "pattern"
NOTES = (
    "Reports a changed write of a gift card balance (`current_balance_amount`/`current_balance` by "
    "assignment, `-=`/`+=`, setattr, `.update(...)` or a cleaned_input key) whose value is computed "
    "from a balance read in Python, or that sits under an `if` that tests the balance, when the row "
    "is not locked with select_for_update (in the same function, or by every caller when the card "
    "is a parameter); an F() expression is accepted. It cannot see races that span several functions "
    "in other ways, for example a check in one request and an F() write without a condition in another, "
    "and it does not check that an F() write is clamped at zero."
)

_BAL = {"current_balance_amount", "current_balance"}
_LOCK = "select_for_update"
_OPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}


def _is_test(path):
    p = "/" + path.replace("\\", "/")
    name = p.rsplit("/", 1)[-1]
    return "/tests/" in p or name.startswith("test_") or name == "conftest.py"


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _parse(src):
    if src is None:
        return None
    try:
        return ast.parse(src)
    except (SyntaxError, ValueError, MemoryError, RecursionError):
        return None


def _touched(node, lines):
    start = getattr(node, "lineno", None)
    if start is None:
        return False
    end = getattr(node, "end_lineno", None) or start
    return any(ln in lines for ln in range(start, end + 1))


def _src(node):
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return ""


def _uses_f_balance(expr):
    for n in ast.walk(expr):
        if isinstance(n, ast.Call):
            fname = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            if fname == "F" and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value in _BAL:
                return True
    return False


def _reads_balance(expr, tainted):
    for n in ast.walk(expr):
        if isinstance(n, ast.Attribute) and n.attr in _BAL and isinstance(n.ctx, ast.Load):
            return True
        if isinstance(n, ast.Name) and n.id in tainted and isinstance(n.ctx, ast.Load):
            return True
    return False


class _Callers:
    """Find the functions that call a function by name, in the workspace (tests excluded)."""

    def __init__(self, workspace, overrides):
        self.ws = workspace
        self.overrides = overrides  # rel path -> parsed tree for changed files
        self.files = None
        self.cache = {}

    def _all_files(self):
        if self.files is None:
            self.files = []
            root = os.path.join(self.ws, "saleor")
            if not os.path.isdir(root):
                root = self.ws
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in ("tests", "migrations", "node_modules", ".git")]
                for fn in filenames:
                    if fn.endswith(".py") and not fn.startswith("test_") and fn != "conftest.py":
                        full = os.path.join(dirpath, fn)
                        rel = os.path.relpath(full, self.ws).replace(os.sep, "/")
                        self.files.append((rel, full))
        return self.files

    def callers_locked(self, name):
        """Return True (all callers lock), False (some caller does not), None (no caller found)."""
        if name in self.cache:
            return self.cache[name]
        pattern = re.compile(r"\b" + re.escape(name) + r"\s*\(")
        found_any = False
        all_locked = True
        for rel, full in self._all_files():
            src = _read(full)
            if src is None or not pattern.search(src):
                continue
            tree = self.overrides.get(rel) or _parse(src)
            if tree is None:
                continue
            for func in ast.walk(tree):
                if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)) or func.name == name:
                    continue
                calls = [
                    n
                    for n in ast.walk(func)
                    if isinstance(n, ast.Call)
                    and (getattr(n.func, "id", None) == name or getattr(n.func, "attr", None) == name)
                ]
                if not calls:
                    continue
                found_any = True
                if _LOCK not in _src(func):
                    all_locked = False
                    break
            if found_any and not all_locked:
                break
        result = None if not found_any else all_locked
        self.cache[name] = result
        return result


def _function_of(parents, node):
    cur = parents.get(node)
    while cur is not None and not isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
        cur = parents.get(cur)
    return cur


def _analyse(path, tree, lines, callers, out):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    scopes = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for scope in scopes:
        # nodes that belong to this scope (not to nested functions)
        nodes = []
        stack = list(ast.iter_child_nodes(scope))
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            nodes.append(n)
            stack.extend(ast.iter_child_nodes(n))
        if not any(_touched(n, lines) for n in nodes if isinstance(n, ast.stmt)):
            continue
        scope_src = _src(scope) if not isinstance(scope, ast.Module) else ""
        params = set()
        if not isinstance(scope, ast.Module):
            a = scope.args
            params = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs}

        # bindings and taint
        bindings = {}
        for n in nodes:
            if isinstance(n, (ast.Assign, ast.AnnAssign)) and getattr(n, "value", None) is not None:
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in targets:
                    for nm in ast.walk(t):
                        if isinstance(nm, ast.Name) and isinstance(nm.ctx, ast.Store):
                            bindings.setdefault(nm.id, []).append(n.value)
            elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
                for nm in ast.walk(n.target):
                    if isinstance(nm, ast.Name) and isinstance(nm.ctx, ast.Store):
                        bindings.setdefault(nm.id, []).append(n.iter)
            elif isinstance(n, ast.withitem) and n.optional_vars is not None:
                for nm in ast.walk(n.optional_vars):
                    if isinstance(nm, ast.Name) and isinstance(nm.ctx, ast.Store):
                        bindings.setdefault(nm.id, []).append(n.context_expr)
        tainted = set()
        grew = True
        while grew:
            grew = False
            for name, values in bindings.items():
                if name not in tainted and any(
                    _reads_balance(v, tainted) and not _uses_f_balance(v) for v in values
                ):
                    tainted.add(name)
                    grew = True

        def under_balance_test(node):
            cur = parents.get(node)
            while cur is not None and cur is not scope:
                if isinstance(cur, (ast.If, ast.While, ast.IfExp)) and _reads_balance(cur.test, tainted):
                    return True
                cur = parents.get(cur)
            return False

        def object_locked(base):
            """True if the written object is locked, False if not, None if unknown."""
            if isinstance(base, ast.Name):
                values = bindings.get(base.id, [])
                if base.id in params:
                    if values and all(_LOCK in _src(v) for v in values):
                        return True
                    if isinstance(scope, ast.Module):
                        return None
                    return callers.callers_locked(scope.name)
                if values:
                    return all(_LOCK in _src(v) for v in values)
                return None
            if isinstance(scope, ast.Module):
                return None
            # attribute chains (self.gift_card) or no object (update, cleaned_input): function text
            return _LOCK in scope_src

        def report(node, what):
            out.append(
                f"{path}:{node.lineno}: gift card balance is changed by read-modify-write in "
                f"application code ({what}) without a row lock; apply the change atomically in "
                "the database (F() expression, clamped at zero) or lock the row with "
                "select_for_update"
            )

        def consider(node, base, value, label, always_reads=False):
            if _uses_f_balance(value):
                # Atomic write. It is still a TOCTOU when it is decided on an unlocked balance read.
                if under_balance_test(node) and object_locked(base) is False:
                    report(node, f"{label} decided by a balance check")
                return
            if not (always_reads or _reads_balance(value, tainted) or under_balance_test(node)):
                return
            if object_locked(base) is False:
                report(node, f"{label} computed from the balance")

        for n in nodes:
            if not isinstance(n, (ast.stmt, ast.Call)) or not _touched(n, lines):
                continue
            if isinstance(n, ast.AugAssign):
                t = n.target
                if isinstance(t, ast.Attribute) and t.attr in _BAL:
                    consider(n, t.value, n.value, f"'{_src(t)} {_OPS.get(type(n.op), '?')}= ...'", always_reads=True)
                elif isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and t.slice.value in _BAL:
                    consider(n, None, n.value, f"'{_src(t)} {_OPS.get(type(n.op), '?')}= ...'", always_reads=True)
            elif isinstance(n, (ast.Assign, ast.AnnAssign)) and getattr(n, "value", None) is not None:
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in targets:
                    if isinstance(t, ast.Attribute) and t.attr in _BAL:
                        consider(n, t.value, n.value, f"'{_src(t)} = ...'")
                    elif isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and t.slice.value in _BAL:
                        consider(n, None, n.value, f"'{_src(t)} = ...'")
            elif isinstance(n, ast.Call):
                fname = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                if fname == "update":
                    for kw in n.keywords:
                        if kw.arg in _BAL:
                            consider(n, None, kw.value, f"update({kw.arg}=...)")
                elif fname == "setattr" and len(n.args) == 3:
                    key = n.args[1]
                    if isinstance(key, ast.Constant) and key.value in _BAL:
                        consider(n, n.args[0], n.args[2], f"setattr(..., '{key.value}', ...)")


def check(workspace, changed):
    findings = []
    try:
        trees = {}
        for path in sorted(changed or {}):
            lines = set(changed[path] or [])
            if not lines or _is_test(path) or not path.endswith(".py"):
                continue
            src = _read(os.path.join(workspace, path))
            if src is None or "current_balance" not in src:
                continue
            tree = _parse(src)
            if tree is None:
                continue
            trees[path] = (tree, lines)
        if not trees:
            return []
        callers = _Callers(workspace, {p: t for p, (t, _l) in trees.items()})
        for path, (tree, lines) in trees.items():
            out = []
            _analyse(path, tree, lines, callers, out)
            seen = set()
            out.sort(key=lambda s: int(s.split(":", 2)[1]) if s.split(":", 2)[1].isdigit() else 0)
            for f in out:
                loc = f.split(": ", 1)[0]
                if loc not in seen:
                    seen.add(loc)
                    findings.append(f)
    except Exception:  # noqa: BLE001
        return findings
    return findings
