"""N2: thumbnail size rounding defaults to UP; NEAREST is opt-in only."""

import ast
import os
import re

CLASS = "pattern"
NOTES = (
    "Reports changed code that makes NEAREST the default or the forced thumbnail rounding: "
    "DEFAULT_THUMBNAIL_SIZE_ROUNDING set to anything but UP, NEAREST as a parameter/field default or "
    "as an `or`/`.get()` fallback, None treated as NEAREST, NEAREST hard-coded in get_thumbnail_size(), "
    "a nearest-size min(THUMBNAIL_SIZES, ...) in code without any rounding choice, a resolver that "
    "ignores its size_rounding argument, and `= NEAREST` defaults in schema.graphql. It cannot see "
    "rounding logic written in other forms, or a new thumbnail field that has no sizeRounding argument."
)


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


def _strip_value(expr):
    # X.NEAREST.value -> X.NEAREST
    if isinstance(expr, ast.Attribute) and expr.attr in ("value", "name"):
        return expr.value
    return expr


def _is_member(expr, member, allow_str=False):
    """True for ThumbnailSizeRounding.<member> / ...Enum.<member> (and the string, when allowed)."""
    expr = _strip_value(expr)
    if isinstance(expr, ast.Attribute) and expr.attr == member:
        base = expr.value
        name = base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", "")
        return "rounding" in (name or "").lower()
    if allow_str and isinstance(expr, ast.Constant) and expr.value == member:
        return True
    return False


def _mentions_rounding(node):
    try:
        return "rounding" in ast.unparse(node).lower()
    except Exception:  # noqa: BLE001
        return False


def _round_param(name):
    return "round" in (name or "").lower()


def _names_in(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _check_tree(path, tree, lines, out):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def enclosing_function(node):
        cur = parents.get(node)
        while cur is not None and not isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cur = parents.get(cur)
        return cur

    def add(node, msg):
        out.append(f"{path}:{node.lineno}: {msg}")

    for node in ast.walk(tree):
        # 1. The project default constant.
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and _touched(node, lines):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                tname = t.id if isinstance(t, ast.Name) else getattr(t, "attr", None)
                if tname == "DEFAULT_THUMBNAIL_SIZE_ROUNDING" and node.value is not None:
                    if not _is_member(node.value, "UP", allow_str=True):
                        add(node, "DEFAULT_THUMBNAIL_SIZE_ROUNDING must stay "
                                  "ThumbnailSizeRounding.UP; NEAREST is opt-in only")

        # 2a. Parameter defaults.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            args = node.args
            pos = args.posonlyargs + args.args
            pairs = list(zip(pos[len(pos) - len(args.defaults):], args.defaults))
            pairs += [(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is not None]
            for arg, default in pairs:
                if not _touched(default, lines) and not _touched(arg, lines):
                    continue
                if _is_member(default, "NEAREST", allow_str=_round_param(arg.arg)):
                    add(default, f"parameter '{arg.arg}' defaults to NEAREST; "
                                 "thumbnail rounding must default to UP")

        # 2b. Field / argument defaults: default_value=NEAREST, default=NEAREST.
        if isinstance(node, ast.Call) and _touched(node, lines):
            for kw in node.keywords:
                if kw.arg in ("default_value", "default", "size_rounding", "rounding"):
                    allow_str = kw.arg in ("size_rounding", "rounding") or _mentions_rounding(
                        node.func
                    ) or any(_mentions_rounding(a) for a in node.args)
                    if kw.arg in ("size_rounding", "rounding"):
                        # passing NEAREST explicitly to a call forces NEAREST
                        if _is_member(kw.value, "NEAREST", allow_str=True):
                            add(kw.value, f"'{kw.arg}' is forced to NEAREST; the client's "
                                          "sizeRounding (default UP) must decide")
                    elif _is_member(kw.value, "NEAREST", allow_str=allow_str):
                        add(kw.value, "sizeRounding default set to NEAREST; it must default to UP")

            fname = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(
                node.func, "id", None
            )
            # 3. get_thumbnail_size(size, NEAREST)
            if fname == "get_thumbnail_size" and len(node.args) >= 2:
                if _is_member(node.args[1], "NEAREST", allow_str=True):
                    add(node, "get_thumbnail_size() is called with a hard-coded NEAREST; pass the "
                              "client's size_rounding (default UP)")
            # 2d. .get("size_rounding", NEAREST) / getattr(x, "size_rounding", NEAREST)
            if fname in ("get", "getattr", "pop") and len(node.args) >= 2:
                key = node.args[-2]
                if isinstance(key, ast.Constant) and isinstance(key.value, str) and "round" in key.value.lower():
                    if _is_member(node.args[-1], "NEAREST", allow_str=True):
                        add(node, "missing sizeRounding falls back to NEAREST; the default must be UP")
            # 4. Nearest-size selection with no rounding choice in the function.
            if fname == "min" and node.args:
                first = node.args[0]
                fname0 = first.id if isinstance(first, ast.Name) else getattr(first, "attr", "")
                has_abs_key = any(
                    kw.arg == "key"
                    and any(
                        isinstance(c, ast.Call) and getattr(c.func, "id", None) == "abs"
                        for c in ast.walk(kw.value)
                    )
                    for kw in node.keywords
                )
                if fname0 == "THUMBNAIL_SIZES" and has_abs_key:
                    func = enclosing_function(node)
                    scope = func if func is not None else tree
                    if not _mentions_rounding(scope) and not re.search(
                        r"\bUP\b", ast.unparse(scope)
                    ):
                        add(node, "thumbnail size is picked by nearest match with no sizeRounding "
                                  "choice; use get_thumbnail_size(size, size_rounding) (default UP)")

        # 2c. size_rounding or ThumbnailSizeRounding.NEAREST
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and _touched(node, lines):
            if len(node.values) >= 2 and _is_member(node.values[-1], "NEAREST", allow_str=any(
                _mentions_rounding(v) for v in node.values[:-1]
            )):
                add(node, "a missing sizeRounding falls back to NEAREST; the default must be UP")
            # 5b. rounding is None or rounding == NEAREST
            none_names, nearest_names = set(), set()
            for v in node.values:
                if isinstance(v, ast.Compare) and len(v.ops) == 1 and isinstance(v.left, ast.Name):
                    comp = v.comparators[0]
                    if isinstance(v.ops[0], (ast.Is, ast.Eq)) and isinstance(comp, ast.Constant) and comp.value is None:
                        none_names.add(v.left.id)
                    if isinstance(v.ops[0], (ast.Is, ast.Eq)) and _is_member(comp, "NEAREST"):
                        nearest_names.add(v.left.id)
                if isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.Not) and isinstance(v.operand, ast.Name):
                    none_names.add(v.operand.id)
            if {n for n in none_names & nearest_names if _round_param(n)}:
                add(node, "an unset sizeRounding is treated as NEAREST; the default must be UP")

    # 5a / 6: per-function checks on a rounding parameter.
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = func.args
        all_args = args.posonlyargs + args.args + args.kwonlyargs
        pos = args.posonlyargs + args.args
        defaults = dict(zip([a.arg for a in pos[len(pos) - len(args.defaults):]], args.defaults))
        defaults.update({a.arg: d for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is not None})
        round_args = [a for a in all_args if _round_param(a.arg)]
        if not round_args:
            continue
        body_names = set()
        for stmt in func.body:
            body_names |= _names_in(stmt)
        reassigned = set()
        for n in ast.walk(func):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                reassigned.add(n.id)
        for arg in round_args:
            default = defaults.get(arg.arg)
            # 6a. Parameter never used: the client's choice is dropped.
            if arg.arg not in body_names and not arg.arg.startswith("_"):
                where = arg if _touched(arg, lines) else next(
                    (
                        n
                        for n in ast.walk(func)
                        if isinstance(n, ast.Call)
                        and _touched(n, lines)
                        and getattr(n.func, "id", getattr(n.func, "attr", None))
                        == "get_thumbnail_size"
                    ),
                    None,
                )
                if where is not None:
                    add(where, f"parameter '{arg.arg}' is not used, so the client's sizeRounding "
                               "is ignored")
                continue
            # 5a. `if rounding == UP: ...` with a None default and no fallback: None means NEAREST.
            none_default = isinstance(default, ast.Constant) and default.value is None
            if none_default and arg.arg not in reassigned:
                for n in ast.walk(func):
                    if (
                        isinstance(n, ast.Compare)
                        and _touched(n, lines)
                        and len(n.ops) == 1
                        and isinstance(n.left, ast.Name)
                        and n.left.id == arg.arg
                    ):
                        op, comp = n.ops[0], n.comparators[0]
                        if (isinstance(op, (ast.Eq, ast.Is)) and _is_member(comp, "UP", allow_str=True)) or (
                            isinstance(op, (ast.NotEq, ast.IsNot)) and _is_member(comp, "UP", allow_str=True)
                        ):
                            add(n, f"'{arg.arg}' is compared with UP but can be None; an unset "
                                   "sizeRounding then gets NEAREST (use the UP default)")
        # 6b. get_thumbnail_size(size) without the rounding the function received.
        for n in ast.walk(func):
            if (
                isinstance(n, ast.Call)
                and _touched(n, lines)
                and getattr(n.func, "id", getattr(n.func, "attr", None)) == "get_thumbnail_size"
                and len(n.args) < 2
                and not any(k.arg == "rounding" for k in n.keywords)
                and any(a.arg in body_names for a in round_args)
            ):
                add(n, "get_thumbnail_size() is called without the size_rounding argument that "
                       "this resolver receives")


_GRAPHQL_NEAREST = re.compile(r"Rounding\w*\s*=\s*NEAREST\b")


def check(workspace, changed):
    findings = []
    try:
        for path in sorted(changed or {}):
            lines = set(changed[path] or [])
            if not lines or _is_test(path):
                continue
            if path.endswith(".graphql"):
                src = _read(workspace, path)
                if src is None:
                    continue
                for i, text in enumerate(src.splitlines(), 1):
                    if i in lines and _GRAPHQL_NEAREST.search(text):
                        findings.append(f"{path}:{i}: sizeRounding defaults to NEAREST in the "
                                        "schema; it must default to UP")
                continue
            if not path.endswith(".py"):
                continue
            src = _read(workspace, path)
            if src is None or ("NEAREST" not in src and "THUMBNAIL" not in src
                               and "rounding" not in src.lower()):
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
