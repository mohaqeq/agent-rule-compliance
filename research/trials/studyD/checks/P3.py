"""P3: never rely on settings.SITE_ID and never assume a single Site row."""

import ast
import os

CLASS = "pattern"
NOTES = (
    "Reports changed code that reads `settings.SITE_ID` (also through getattr) outside the two "
    "modules that implement site resolution, and queries that assume one site: Site/SiteSettings "
    ".objects.get() with no filter, .first()/.last()/.earliest()/.latest(), indexing [0], or get(pk=<constant>). "
    "It cannot see per-site data keyed by a constant (for example a cache key or a module-level dict "
    "without the site), because that needs knowledge of what the data means."
)

# Modules that implement Site.objects.get_current() and get_site_promise; they must read SITE_ID.
_ALLOWED = (
    "saleor/site/patch_sites.py",
    "saleor/graphql/site/dataloaders.py",
    "saleor/settings.py",
)
_SITE_MODELS = {"Site", "SiteSettings"}
_SINGLE_ROW = {"first", "last", "earliest", "latest"}
_PASS_THROUGH = {
    "using", "all", "select_related", "prefetch_related", "only", "defer", "values",
    "values_list", "select_for_update", "order_by", "annotate",
}


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


def _last(expr):
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def _is_settings(expr):
    name = _last(expr)
    return bool(name) and name.lower().endswith("settings") and name not in _SITE_MODELS


def _site_manager_model(expr):
    """For Site.objects[.using(..)...] return 'Site' / 'SiteSettings', else None.

    Only plain pass-through calls are allowed between `.objects` and the final call, so a
    filtered queryset (`.filter(site=...)`) is not reported.
    """
    cur = expr
    while True:
        if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Attribute):
            if cur.func.attr not in _PASS_THROUGH:
                return None
            cur = cur.func.value
        elif isinstance(cur, ast.Attribute) and cur.attr == "objects":
            model = _last(cur.value)
            return model if model in _SITE_MODELS else None
        else:
            return None


def _check_tree(path, tree, lines, out):
    allowed = path.replace("\\", "/").endswith(_ALLOWED)
    for node in ast.walk(tree):
        if not _touched(node, lines):
            continue
        # settings.SITE_ID
        if (
            not allowed
            and isinstance(node, ast.Attribute)
            and node.attr == "SITE_ID"
            and _is_settings(node.value)
        ):
            out.append(f"{path}:{node.lineno}: settings.SITE_ID is read directly; resolve the site "
                       "with Site.objects.get_current() (or get_site_promise in GraphQL)")
        if not isinstance(node, (ast.Call, ast.Subscript)):
            continue
        if (
            not allowed
            and isinstance(node, ast.Call)
            and _last(node.func) in ("getattr", "hasattr")
            and len(node.args) >= 2
            and _is_settings(node.args[0])
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "SITE_ID"
        ):
            out.append(f"{path}:{node.lineno}: settings.SITE_ID is read directly; resolve the site "
                       "with Site.objects.get_current() (or get_site_promise in GraphQL)")
            continue
        if isinstance(node, ast.Subscript):
            # Site.objects.all()[0]
            idx = node.slice
            if isinstance(idx, ast.Constant) and idx.value in (0, -1):
                model = _site_manager_model(node.value)
                if model:
                    out.append(f"{path}:{node.lineno}: {model} row taken by index assumes a single "
                               "site; filter by the resolved site (Site.objects.get_current())")
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        model = _site_manager_model(func.value)
        if not model:
            continue
        if func.attr == "get":
            if not node.args and not node.keywords:
                out.append(f"{path}:{node.lineno}: {model}.objects.get() with no filter breaks as "
                           "soon as a second site exists; filter by the resolved site")
            else:
                for kw in node.keywords:
                    if kw.arg in ("pk", "id", "site_id", "site__pk", "site__id") and isinstance(
                        kw.value, ast.Constant
                    ) and isinstance(kw.value.value, int):
                        out.append(f"{path}:{node.lineno}: {model} is fetched by a constant "
                                   f"{kw.arg}={kw.value.value}; resolve the site with "
                                   "Site.objects.get_current()")
        elif func.attr in _SINGLE_ROW:
            out.append(f"{path}:{node.lineno}: {model}.objects.{func.attr}() assumes a single site; "
                       "filter by the resolved site (Site.objects.get_current())")


def check(workspace, changed):
    findings = []
    try:
        for path in sorted(changed or {}):
            lines = set(changed[path] or [])
            if not lines or _is_test(path) or not path.endswith(".py"):
                continue
            src = _read(workspace, path)
            if src is None or ("SITE_ID" not in src and "Site" not in src):
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
