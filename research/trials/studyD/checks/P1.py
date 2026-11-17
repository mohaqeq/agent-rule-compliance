"""P1: a gift card restricted to a customer stays restricted after that customer is deleted."""

import ast
import os
import re

CLASS = "pattern"
NOTES = (
    "Reports changed code that drops the trace of a gift card assignment in a user-deletion path "
    "(clears `assigned_to_email` in a function or file about delete/remove/anonymize/deactivate), "
    "a usage check that tests only `assigned_to`/`assigned_to_id` (\"assigned and not this user\", "
    "or `assigned_to__isnull=True` as \"free\") in a function that never looks at `assigned_to_email` "
    "or `usage_restriction_reason`. It misses other forms, for example a change to the "
    "`assigned_to` foreign key, raw SQL, or a restriction check that is written in another way."
)

_DELETION_WORDS = re.compile(r"delet|remov|anonymi|purge|erase|gdpr|deactivat|destroy|wipe|forget", re.I)
_SAFE_WORDS = re.compile(r"unassign|reassign|assign_user|assign_to", re.I)
_TRACE_NAMES = ("assigned_to_email", "usage_restriction_reason")


def _is_test(path):
    p = "/" + path.replace("\\", "/")
    name = p.rsplit("/", 1)[-1]
    return "/tests/" in p or name.startswith("test_") or name == "conftest.py"


def _read(workspace, rel):
    try:
        with open(os.path.join(workspace, rel), encoding="utf-8") as f:
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


def _is_empty(expr):
    return isinstance(expr, ast.Constant) and expr.value in (None, "")


def _attr_name(expr):
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def _is_assignee_attr(expr):
    return _attr_name(expr) in ("assigned_to", "assigned_to_id")


def _src_of(node):
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return ""


def check(workspace, changed):
    findings = []
    try:
        for path in sorted(changed or {}):
            lines = set(changed[path] or [])
            if not lines or _is_test(path) or not path.endswith(".py"):
                continue
            src = _read(workspace, path)
            if src is None or "assigned_to" not in src:
                continue
            tree = _parse(src)
            if tree is None:
                continue
            out = []
            _check_tree(path, tree, lines, out)
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


def _check_tree(path, tree, lines, out):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def enclosing(node, kinds):
        cur = parents.get(node)
        while cur is not None and not isinstance(cur, kinds):
            cur = parents.get(cur)
        return cur

    def context_names(node):
        """Names of the enclosing functions and classes, and the file name."""
        names = [path.rsplit("/", 1)[-1]]
        cur = parents.get(node)
        while cur is not None:
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(cur.name)
            cur = parents.get(cur)
        return names

    def in_deletion_path(node):
        names = context_names(node)
        if any(_SAFE_WORDS.search(n) for n in names):
            return False
        return any(_DELETION_WORDS.search(n) for n in names)

    file_has_trace = any(t in _src_of(tree) for t in _TRACE_NAMES)

    def scope_has_trace(node):
        func = enclosing(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        if func is None:
            return file_has_trace
        text = _src_of(func)
        return any(t in text for t in _TRACE_NAMES)

    for node in ast.walk(tree):
        # (a) assignment trace dropped in a deletion path.
        if isinstance(node, ast.Assign) and _touched(node, lines) and _is_empty(node.value):
            for t in node.targets:
                if _attr_name(t) == "assigned_to_email" and in_deletion_path(node):
                    out.append(f"{path}:{node.lineno}: assigned_to_email is cleared while a "
                               "customer is deleted; keep it so the card stays restricted")
        if isinstance(node, ast.Call) and _touched(node, lines):
            for kw in node.keywords:
                if kw.arg == "assigned_to_email" and _is_empty(kw.value) and in_deletion_path(node):
                    out.append(f"{path}:{kw.value.lineno}: assigned_to_email is cleared while a "
                               "customer is deleted; keep it so the card stays restricted")
            # (c2) filter(assigned_to__isnull=True) as "free to use"
            fname = _attr_name(node.func) or getattr(node.func, "id", None)
            if fname in ("filter", "exclude", "Q", "get"):
                func = enclosing(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                listing = (
                    "/filters" in path
                    or "sorter" in path
                    or (func is not None and re.match(r"(filter_|resolve_|sort_)", func.name))
                )
                for kw in node.keywords:
                    if kw.arg in ("assigned_to__isnull", "assigned_to_id__isnull") and isinstance(
                        kw.value, ast.Constant
                    ) and kw.value.value is True and not listing:
                        if not scope_has_trace(node) and not any(
                            _SAFE_WORDS.search(n) for n in context_names(node)
                        ):
                            out.append(f"{path}:{kw.value.lineno}: a card is treated as unrestricted "
                                       "by assigned_to alone; a card whose customer was deleted has "
                                       "assigned_to NULL but must stay restricted (check "
                                       "assigned_to_email or use usage_restriction_reason)")
        # (c1) "assigned and not this user" without the deleted-customer case.
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And) and _touched(node, lines):
            truthy, compared = set(), set()
            for v in node.values:
                if _is_assignee_attr(v):
                    truthy.add(_src_of(v))
                elif isinstance(v, ast.Compare) and len(v.ops) == 1 and _is_assignee_attr(v.left):
                    comp = v.comparators[0]
                    if isinstance(v.ops[0], ast.IsNot) and isinstance(comp, ast.Constant) and comp.value is None:
                        truthy.add(_src_of(v.left))
                    elif isinstance(v.ops[0], (ast.NotEq, ast.IsNot)):
                        compared.add(_src_of(v.left))
            if truthy & compared and not scope_has_trace(node):
                out.append(f"{path}:{node.lineno}: restriction check uses only assigned_to; a card "
                           "whose customer was deleted (assigned_to NULL, assigned_to_email kept) "
                           "becomes usable by anyone; use usage_restriction_reason()")
        # (c3) `if not card.assigned_to_id: <allow>` style guard
        if isinstance(node, (ast.If, ast.IfExp)) and _touched(node.test, lines):
            test = node.test
            negated = None
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not) and _is_assignee_attr(test.operand):
                negated = test.operand
            elif (
                isinstance(test, ast.Compare)
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Is)
                and _is_assignee_attr(test.left)
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value is None
            ):
                negated = test.left
            allows = False
            if isinstance(node, ast.If) and node.body:
                first = node.body[0]
                allows = isinstance(first, (ast.Continue, ast.Pass)) or (
                    isinstance(first, ast.Return)
                    and (first.value is None or (isinstance(first.value, ast.Constant) and first.value.value in (None, True)))
                )
            if negated is not None and allows and not scope_has_trace(node):
                func = enclosing(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                fname = func.name if func is not None else ""
                names = context_names(node)
                # Only in code that decides whether a card may be used.
                if (
                    re.search(r"valid|usab|can_use|restrict|allow|permit|check|clean|apply|add|redeem|spend|charge|use", fname, re.I)
                    and not re.match(r"(resolve_|filter_|sort_)", fname)
                    and not any(_SAFE_WORDS.search(n) for n in names)
                ):
                    out.append(f"{path}:{node.lineno}: a card without assigned_to is treated as "
                               "unrestricted; a card whose customer was deleted keeps only "
                               "assigned_to_email and must stay restricted (use "
                               "usage_restriction_reason())")
