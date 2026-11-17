"""N3: reference a Django model's primary key as `pk`, not as the `id` field."""

import ast
import os

CLASS = "pattern"
NOTES = (
    "Reports `id` used as a Django field in changed code: lookups such as filter(id=...), get(id=...), "
    "Q(id__in=...), product__id=..., string references such as values_list('id'), OuterRef('id'), "
    "order_by('-id'), and `.id` read on a variable that is known to hold a model instance (a parameter "
    "annotated with a model class that the check resolves through the imports, a result of "
    "Model.objects.get/first/create, a loop over a queryset, `self` in a model, or one ForeignKey step "
    "from such a variable). It misses `.id` on objects whose type it cannot prove (for example "
    "`info.context.user.id`, attributes of other objects, unannotated parameters)."
)

_LOOKUP_METHODS = {"filter", "exclude", "get", "get_or_create", "update_or_create"}
_LOOKUP_FUNCS = {"Q", "get_object_or_404", "get_list_or_404"}
_FIELD_METHODS = {"values_list", "values", "order_by", "only", "defer", "distinct"}
_FIELD_FUNCS = {"F", "OuterRef", "Count", "Max", "Min"}
_SINGLE = {"get", "first", "last", "create", "earliest", "latest"}
_PAIR = {"get_or_create", "update_or_create"}
_QS_CHAIN = {
    "all", "filter", "exclude", "select_related", "prefetch_related", "order_by", "iterator",
    "using", "only", "defer", "select_for_update", "distinct", "annotate", "reverse", "none",
}
_NON_INSTANCE = {"values", "values_list", "in_bulk", "count", "exists", "aggregate", "dates"}
_CONTAINERS = {
    "list", "List", "Iterable", "Sequence", "set", "Set", "frozenset", "Iterator", "QuerySet",
    "Collection", "tuple", "Tuple",
}
_FK_FIELDS = {"ForeignKey", "OneToOneField"}


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


def _is_id_field(name):
    """'id', 'id__in', 'product__id', 'product__id__in' -> True."""
    if not isinstance(name, str):
        return False
    parts = name.lstrip("-").split("__")
    return "id" in parts


# --------------------------------------------------------------------------- model resolution


class _Modules:
    def __init__(self, workspace):
        self.ws = workspace
        self.cache = {}
        self.model_cache = {}

    def dotted_for_path(self, rel):
        rel = rel.replace("\\", "/")
        if rel.endswith("/__init__.py"):
            return rel[: -len("/__init__.py")].replace("/", "."), True
        return rel[:-3].replace("/", "."), False

    def load(self, dotted):
        if dotted in self.cache:
            return self.cache[dotted]
        result = None
        base = os.path.join(self.ws, *dotted.split("."))
        for cand, is_pkg in ((base + ".py", False), (os.path.join(base, "__init__.py"), True)):
            if os.path.isfile(cand):
                tree = _parse(_read(cand))
                if tree is not None:
                    result = _ModuleInfo(dotted, is_pkg, tree)
                break
        self.cache[dotted] = result
        return result

    def is_model_class(self, module, name, depth=0):
        key = (module, name)
        if key in self.model_cache:
            return self.model_cache[key]
        self.model_cache[key] = False  # guard against cycles
        result = self._is_model_class(module, name, depth)
        self.model_cache[key] = result
        return result

    def _is_model_class(self, module, name, depth):
        if depth > 12 or not module or not name:
            return False
        if module == "django.db.models" or module == "django.db.models.base":
            return name == "Model"
        if module.startswith("django."):
            return (
                module.endswith(".models")
                and name[:1].isupper()
                and not name.endswith(("Manager", "QuerySet", "Queryset"))
            )
        info = self.load(module)
        if info is None:
            return False
        cls = info.classes.get(name)
        if cls is not None:
            return any(self.is_model_expr(info, b, depth + 1) for b in cls.bases)
        target = info.imports.get(name)
        if target and target[1] is not None:
            return self.is_model_class(target[0], target[1], depth + 1)
        return False

    def resolve_class(self, info, expr, depth=0):
        """Return (module, class name) for a Name/Attribute that names a model class, else None."""
        if isinstance(expr, ast.Name):
            name = expr.id
            if name in info.classes:
                if any(self.is_model_expr(info, b, depth + 1) for b in info.classes[name].bases):
                    return (info.dotted, name)
                return None
            target = info.imports.get(name)
            if target and target[1] is not None:
                if self.is_model_class(target[0], target[1], depth + 1):
                    return self.canonical(target[0], target[1])
            return None
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            target = info.imports.get(expr.value.id)
            if target:
                module = target[0] if target[1] is None else target[0] + "." + target[1]
                if self.is_model_class(module, expr.attr, depth + 1):
                    return self.canonical(module, expr.attr)
        return None

    def canonical(self, module, name, depth=0):
        """Follow re-exports to the module that defines the class."""
        info = self.load(module)
        while info is not None and depth < 12 and name not in info.classes:
            target = info.imports.get(name)
            if not target or target[1] is None:
                break
            module, name = target
            info = self.load(module)
            depth += 1
        return (module, name)

    def is_model_expr(self, info, expr, depth=0):
        if isinstance(expr, ast.Name):
            if expr.id in info.classes:
                return any(self.is_model_expr(info, b, depth + 1) for b in info.classes[expr.id].bases)
            target = info.imports.get(expr.id)
            return bool(target and target[1] is not None and self.is_model_class(target[0], target[1], depth))
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            target = info.imports.get(expr.value.id)
            if target:
                module = target[0] if target[1] is None else target[0] + "." + target[1]
                return self.is_model_class(module, expr.attr, depth)
        return False

    def fk_fields(self, cls_ref):
        """Return {field name: target class ref or None} for ForeignKey/OneToOne fields of a model."""
        module, name = cls_ref
        info = self.load(module)
        if info is None or name not in info.classes:
            return {}
        fields = {}
        for stmt in info.classes[name].body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                value = stmt.value
                if isinstance(value, ast.Call):
                    fname = value.func.attr if isinstance(value.func, ast.Attribute) else getattr(value.func, "id", "")
                    if fname in _FK_FIELDS:
                        fields[stmt.targets[0].id] = None
        return fields


class _ModuleInfo:
    def __init__(self, dotted, is_pkg, tree):
        self.dotted = dotted
        self.tree = tree
        self.classes = {}
        self.imports = {}
        package = dotted if is_pkg else dotted.rpartition(".")[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        self.imports[alias.asname] = (alias.name, None)
                    else:
                        top = alias.name.split(".")[0]
                        self.imports.setdefault(top, (top, None))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    parts = package.split(".") if package else []
                    if node.level > 1:
                        parts = parts[: len(parts) - (node.level - 1)]
                    base = ".".join(parts)
                    module = base + ("." + node.module if node.module else "") if base else (node.module or "")
                else:
                    module = node.module or ""
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    self.imports[alias.asname or alias.name] = (module, alias.name)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self.classes[node.name] = node


# --------------------------------------------------------------------------- instance inference


def _unwrap_annotation(ann):
    """Yield (expr, is_container) for the class names an annotation can mean."""
    if ann is None:
        return
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        try:
            ann = ast.parse(ann.value, mode="eval").body
        except SyntaxError:
            return
    if isinstance(ann, ast.BinOp) and isinstance(ann.op, ast.BitOr):
        yield from _unwrap_annotation(ann.left)
        yield from _unwrap_annotation(ann.right)
        return
    if isinstance(ann, ast.Subscript):
        head = ann.value.attr if isinstance(ann.value, ast.Attribute) else getattr(ann.value, "id", "")
        inner = ann.slice
        if head in ("Optional", "Union"):
            elts = inner.elts if isinstance(inner, ast.Tuple) else [inner]
            for e in elts:
                yield from _unwrap_annotation(e)
        elif head in _CONTAINERS:
            elts = inner.elts if isinstance(inner, ast.Tuple) else [inner]
            for e in elts[:1]:
                for expr, container in _unwrap_annotation(e):
                    if not container:
                        yield expr, True
        return
    if isinstance(ann, (ast.Name, ast.Attribute)):
        yield ann, False


def _chain(expr):
    """Return the list of attribute/method names of a call chain, from the root."""
    names = []
    cur = expr
    while True:
        if isinstance(cur, ast.Call):
            cur = cur.func
        elif isinstance(cur, ast.Attribute):
            names.append(cur.attr)
            cur = cur.value
        elif isinstance(cur, ast.Subscript):
            cur = cur.value
        else:
            break
    names.reverse()
    return names, cur


def _objects_root(expr):
    """For X.objects.<...> return the X expression, else None."""
    cur = expr
    while True:
        if isinstance(cur, ast.Call):
            cur = cur.func
        elif isinstance(cur, ast.Attribute):
            if cur.attr == "objects":
                return cur.value
            cur = cur.value
        else:
            return None


class _Scope:
    def __init__(self, mods, info, lines, path, out):
        self.mods = mods
        self.info = info
        self.lines = lines
        self.path = path
        self.out = out

    def model_of_expr(self, expr, collections):
        """Return ('one'|'many', class ref or None) if expr evaluates to model instance(s)."""
        if isinstance(expr, ast.Call):
            func = expr.func
            # Model(...)
            if isinstance(func, (ast.Name, ast.Attribute)):
                ref = self.mods.resolve_class(self.info, func)
                if ref is not None:
                    return ("one", ref)
            if isinstance(func, ast.Name) and func.id == "get_object_or_404" and expr.args:
                ref = self.mods.resolve_class(self.info, expr.args[0])
                return ("one", ref)
        names, _root = _chain(expr)
        if "objects" in names and not (_NON_INSTANCE & set(names)):
            last = names[-1]
            root = _objects_root(expr)
            ref = self.mods.resolve_class(self.info, root) if root is not None else None
            if isinstance(expr, ast.Call) and last in _SINGLE:
                return ("one", ref)
            if isinstance(expr, ast.Call) and last in _PAIR:
                return ("pair", ref)
            if last in _QS_CHAIN or last == "objects":
                return ("many", ref)
        if isinstance(expr, ast.Name) and expr.id in collections:
            return ("many", collections[expr.id])
        return None

    def run(self, func, self_ref=None):
        """Analyse one function (or the module body when func is a Module)."""
        bindings = {}  # name -> list of (kind, ref) ; kind None means not a model

        def bind(name, value):
            bindings.setdefault(name, []).append(value)

        collections = {}
        body_nodes = []
        if isinstance(func, ast.Module):
            stmts = [s for s in func.body if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        else:
            stmts = func.body
            args = func.args
            all_args = args.posonlyargs + args.args + args.kwonlyargs
            for i, a in enumerate(all_args):
                if i == 0 and self_ref is not None and a.arg == "self":
                    bind("self", ("one", self_ref))
                    continue
                found = None
                for expr, container in _unwrap_annotation(a.annotation):
                    ref = self.mods.resolve_class(self.info, expr)
                    if ref is not None:
                        found = ("many" if container else "one", ref)
                        break
                bind(a.arg, found)
            for a in (args.vararg, args.kwarg):
                if a is not None:
                    bind(a.arg, None)

        def walk(nodes):
            stack = list(nodes)
            while stack:
                n = stack.pop()
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if isinstance(n, ast.ClassDef):
                        bind(n.name, None)
                    else:
                        bind(n.name, None)
                    continue
                if isinstance(n, ast.Lambda):
                    for a in n.args.args + n.args.kwonlyargs + n.args.posonlyargs:
                        bind(a.arg, None)
                body_nodes.append(n)
                stack.extend(ast.iter_child_nodes(n))

        walk(stmts)

        # collections first (parameters annotated as containers)
        for name, vals in bindings.items():
            if vals and all(v is not None and v[0] == "many" for v in vals):
                collections[name] = vals[0][1]

        for _pass in range(2):
            for n in body_nodes:
                if isinstance(n, ast.Assign) and _pass == 0:
                    kind = self.model_of_expr(n.value, collections)
                    for t in n.targets:
                        self._bind_target(t, kind, bind)
                elif isinstance(n, ast.AnnAssign) and _pass == 0 and isinstance(n.target, ast.Name):
                    found = None
                    for expr, container in _unwrap_annotation(n.annotation):
                        ref = self.mods.resolve_class(self.info, expr)
                        if ref is not None:
                            found = ("many" if container else "one", ref)
                            break
                    if found is None and n.value is not None:
                        found = self.model_of_expr(n.value, collections)
                    bind(n.target.id, found)
                elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)) and _pass == 1:
                    kind = self.model_of_expr(n.iter, collections)
                    if isinstance(n.target, ast.Name):
                        bind(n.target.id, ("one", kind[1]) if kind and kind[0] == "many" else None)
                    else:
                        self._bind_target(n.target, None, bind)
                elif _pass == 0 and isinstance(n, (ast.AugAssign,)):
                    self._bind_target(n.target, None, bind)
                elif _pass == 0 and isinstance(n, ast.NamedExpr):
                    bind(n.target.id, self.model_of_expr(n.value, collections))
                elif _pass == 0 and isinstance(n, ast.withitem) and n.optional_vars is not None:
                    self._bind_target(n.optional_vars, None, bind)
                elif _pass == 0 and isinstance(n, ast.ExceptHandler) and n.name:
                    bind(n.name, None)
                elif _pass == 0 and isinstance(n, (ast.Import, ast.ImportFrom)):
                    for alias in n.names:
                        bind((alias.asname or alias.name).split(".")[0], None)
                elif _pass == 0 and isinstance(n, (ast.Global, ast.Nonlocal)):
                    for name in n.names:
                        bind(name, None)
            if _pass == 0:
                for name, vals in bindings.items():
                    if vals and all(v is not None and v[0] == "many" for v in vals):
                        collections[name] = vals[0][1]

        instances = {}
        for name, vals in bindings.items():
            if vals and all(v is not None and v[0] == "one" for v in vals):
                refs = {v[1] for v in vals}
                instances[name] = refs.pop() if len(refs) == 1 else None

        for n in body_nodes:
            if not (isinstance(n, ast.Attribute) and n.attr == "id" and _touched(n, self.lines)):
                continue
            base = n.value
            if isinstance(base, ast.Name) and base.id in instances:
                self.out.append(
                    f"{self.path}:{n.lineno}: '{base.id}.id' reads the id field of a model "
                    f"instance; use '{base.id}.pk'"
                )
            elif (
                isinstance(base, ast.Attribute)
                and isinstance(base.value, ast.Name)
                and instances.get(base.value.id) is not None
                and base.attr in self.mods.fk_fields(instances[base.value.id])
            ):
                v, fk = base.value.id, base.attr
                self.out.append(
                    f"{self.path}:{n.lineno}: '{v}.{fk}.id' reads the id field of a related "
                    f"model; use '{v}.{fk}.pk' (or '{v}.{fk}_id')"
                )

    def _bind_target(self, target, kind, bind):
        if isinstance(target, ast.Name):
            bind(target.id, kind if kind and kind[0] in ("one", "many") else None)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for i, elt in enumerate(target.elts):
                if kind and kind[0] == "pair" and i == 0:
                    self._bind_target(elt, ("one", kind[1]), bind)
                else:
                    self._bind_target(elt, None, bind)
        elif isinstance(target, ast.Starred):
            self._bind_target(target.value, None, bind)


# --------------------------------------------------------------------------- lookups


def _check_lookups(path, tree, lines, out):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _touched(node, lines):
            continue
        func = node.func
        fname = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if (isinstance(func, ast.Attribute) and fname in _LOOKUP_METHODS) or (
            isinstance(func, ast.Name) and fname in _LOOKUP_FUNCS
        ):
            for kw in node.keywords:
                if kw.arg and kw.arg != "defaults" and _is_id_field(kw.arg) and _touched(kw, lines):
                    new = "__".join("pk" if p == "id" else p for p in kw.arg.split("__"))
                    out.append(
                        f"{path}:{kw.value.lineno}: lookup '{kw.arg}=' uses the id field; "
                        f"use '{new}='"
                    )
        if (isinstance(func, ast.Attribute) and fname in _FIELD_METHODS) or (
            isinstance(func, ast.Name) and fname in _FIELD_FUNCS
        ):
            for arg in node.args:
                if (
                    isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)
                    and _is_id_field(arg.value)
                    and _touched(arg, lines)
                ):
                    new = "__".join("pk" if p == "id" else p for p in arg.value.split("__"))
                    out.append(
                        f"{path}:{arg.lineno}: field reference '{arg.value}' uses the id field; "
                        f"use '{new}'"
                    )


def check(workspace, changed):
    findings = []
    try:
        mods = _Modules(workspace)
        for path in sorted(changed or {}):
            lines = set(changed[path] or [])
            if not lines or _is_test(path) or not path.endswith(".py"):
                continue
            src = _read(os.path.join(workspace, path))
            if src is None or "id" not in src:
                continue
            tree = _parse(src)
            if tree is None:
                continue
            out = []
            try:
                _check_lookups(path, tree, lines, out)
            except Exception:  # noqa: BLE001
                pass
            try:
                dotted, is_pkg = mods.dotted_for_path(path)
                info = _ModuleInfo(dotted, is_pkg, tree)
                mods.cache.setdefault(dotted, info)
                scope = _Scope(mods, info, lines, path, out)
                scope.run(tree)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        self_ref = None
                        if any(mods.is_model_expr(info, b) for b in node.bases):
                            self_ref = (dotted, node.name) if node in tree.body else None
                        for stmt in node.body:
                            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                is_static = any(
                                    getattr(d, "id", None) in ("staticmethod", "classmethod")
                                    for d in stmt.decorator_list
                                )
                                scope.run(stmt, None if is_static else self_ref)
                _run_functions(tree, scope)
            except RecursionError:
                pass
            seen = set()
            out.sort(key=lambda s: int(s.split(":", 2)[1]) if s.split(":", 2)[1].isdigit() else 0)
            for f in out:
                if f not in seen:
                    seen.add(f)
                    findings.append(f)
    except Exception:  # noqa: BLE001
        return findings
    return findings


def _run_functions(tree, scope):
    """Run every function that is not a direct method of a class."""
    methods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(stmt)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node not in methods:
            scope.run(node)
