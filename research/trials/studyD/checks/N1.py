"""N1: dispatch webhook events through call_event, not by a direct manager call."""

import ast
import os

CLASS = "pattern"
NOTES = (
    "Reports a direct call of a PluginsManager webhook-event method (a method whose name matches a "
    "WebhookEventAsyncType, read from the workspace) on a receiver named like a manager, for example "
    "`manager.product_updated(p)`, also inside `transaction.on_commit(lambda: ...)`; a call wrapped as "
    "`call_event(manager.x, ...)` is correct. It cannot see a call through an alias "
    "(`f = manager.x; f()`) or through a receiver whose name does not contain 'manager'."
)

# Manager methods that send an async webhook but whose names do not match an event type.
_EXTRA_EVENT_METHODS = {
    "tracking_number_updated",
    "invoice_delete",
    "translations_created",
    "translations_updated",
}
# Methods that match an event name but return a value that the caller needs.
_NOT_EVENT_METHODS = {"invoice_request", "event_delivery_retry", "notify"}

_FALLBACK_MANAGER = "saleor/plugins/manager.py"
_FALLBACK_EVENTS = "saleor/webhook/event_types.py"


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


def _event_methods(workspace):
    events = set()
    tree = _parse(_read(workspace, _FALLBACK_EVENTS))
    if tree is not None:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "WebhookEventAsyncType":
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for t in stmt.targets:
                            if isinstance(t, ast.Name) and t.id.isupper():
                                events.add(t.id.lower())
    methods = set()
    tree = _parse(_read(workspace, _FALLBACK_MANAGER))
    if tree is not None:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "PluginsManager":
                for stmt in node.body:
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.add(stmt.name)
    if not methods:
        return set()
    result = {m for m in methods if m in events}
    result |= _EXTRA_EVENT_METHODS & methods
    return result - _NOT_EVENT_METHODS


def _last_name(expr):
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def _is_manager_receiver(expr):
    name = _last_name(expr)
    if name and name.lower().endswith("manager"):
        return True
    if isinstance(expr, ast.Call):
        fname = _last_name(expr.func)
        if fname in ("PluginsManager", "get_plugins_manager"):
            return True
        # get_plugin_manager_promise(ctx).get()
        if (
            fname == "get"
            and isinstance(expr.func, ast.Attribute)
            and isinstance(expr.func.value, ast.Call)
            and _last_name(expr.func.value.func) == "get_plugin_manager_promise"
        ):
            return True
    return False


def check(workspace, changed):
    findings = []
    try:
        targets = {
            p: set(lines)
            for p, lines in (changed or {}).items()
            if p.endswith(".py") and not _is_test(p) and lines
        }
        if not targets:
            return []
        methods = _event_methods(workspace)
        if not methods:
            return []
        for path in sorted(targets):
            if path.replace("\\", "/").endswith(_FALLBACK_MANAGER):
                continue
            tree = _parse(_read(workspace, path))
            if tree is None:
                continue
            lines = targets[path]
            parents = {}
            for node in ast.walk(tree):
                for child in ast.iter_child_nodes(node):
                    parents[child] = node
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                    continue
                if node.func.attr not in methods:
                    continue
                if not _is_manager_receiver(node.func.value):
                    continue
                # Only a call whose result is not used (call_event drops the result).
                parent = parents.get(node)
                if not (
                    isinstance(parent, (ast.Expr, ast.Return))
                    or (isinstance(parent, ast.Lambda) and parent.body is node)
                ):
                    continue
                start = node.lineno
                end = getattr(node, "end_lineno", None) or start
                if not any(ln in lines for ln in range(start, end + 1)):
                    continue
                findings.append(
                    f"{path}:{start}: direct call of webhook event method "
                    f"'{node.func.attr}' on the plugin manager; use "
                    f"call_event(manager.{node.func.attr}, ...) from saleor.core.utils.events"
                )
    except Exception:  # noqa: BLE001 - a check must never stop the pipeline
        return findings
    return findings
