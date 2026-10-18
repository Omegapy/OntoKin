"""Pure source-revision operations for the local OntoKin agent service.

The service owns acceptance, durable request identities, run identities, and
transactions. This module owns bounded semantic work on one immutable UTF-8
snapshot. It never writes files, accepts source, or advances a stored run.
Inspection replays the requested prefix analytically and checks it against the
stored run's available interval. Shared class declarations remain definition
edit scopes; expanding them never grants an occurrence their writable bytes.
"""

from __future__ import annotations

import copy
from dataclasses import asdict
from fractions import Fraction
import hashlib
from time import monotonic
from typing import Any, Callable

from .diagnostics import OntoKinError, Source
from .evaluator import evaluate_prefix, exact_time, inspect_in_frame, time_text
from .syntax import MAX_SOURCE_BYTES, Node, Parser, lex, parse
from .validator import FIELD_TYPES, KEY_RE, Context, Validator, optional
from .values import Type, Value


SCHEMA_VERSION = "ontokin.agent-runtime/0.1"
MAX_BUDGETS = {"max_objects": 1000, "max_operations": 100000,
               "max_result_items": 1000, "max_elapsed_ms": 30000}
INSPECTION_FIELDS = ("identity", "source", "values", "geometry", "matter",
                     "relations", "actions", "state", "support")


class _Interrupt(Exception):
    """Keep a caller's cancellation/deadline exception out of semantic catches."""

    def __init__(self, error: Exception):
        self.error = error


class _Budget:
    def __init__(self, budgets: dict | None, check: Callable[[], None] | None):
        self.limits = dict(MAX_BUDGETS)
        if budgets is not None:
            if not isinstance(budgets, dict) or set(budgets) - set(MAX_BUDGETS):
                raise OntoKinError("OKL-E-RESOURCE", "Unknown or malformed agent work budget.",
                                   category="resource_limit", phase="support")
            for name, value in budgets.items():
                if type(value) is not int or not 1 <= value <= MAX_BUDGETS[name]:
                    raise OntoKinError("OKL-E-RESOURCE", f"Budget {name} must be an integer from 1 through {MAX_BUDGETS[name]}.",
                                       category="resource_limit", phase="support")
                self.limits[name] = value
        self.external_check = check
        self.started = monotonic()
        self.operations = 0

    def tick(self) -> None:
        if self.external_check is not None:
            try:
                self.external_check()
            except Exception as exc:
                raise _Interrupt(exc) from exc
        self.operations += 1
        if self.operations > self.limits["max_operations"]:
            self.exhausted("max_operations", self.operations)
        elapsed = (monotonic() - self.started) * 1000
        if elapsed > self.limits["max_elapsed_ms"]:
            self.exhausted("max_elapsed_ms", elapsed)

    def exhausted(self, name: str, consumed: int | float, node: Any = None) -> None:
        raise OntoKinError("OKL-E-RESOURCE", f"The agent operation exhausted {name}.", node,
                           category="resource_limit", phase="support",
                           details={"budget": name, "limit": self.limits[name], "consumed": consumed,
                                    "partial_results": "Only an explicitly returned valid prefix is available."})


class _RuntimeValidator(Validator):
    """Observe actual elaboration dependencies without changing their values."""

    def __init__(self, program: Node, budget: _Budget):
        super().__init__(program, "represented")
        self.budget = budget
        self.dependencies: dict[tuple[str, str], set[tuple[str, str]]] = {}
        self.call_dependencies: dict[tuple[str, str], set[tuple[str, ...]]] = {}

    def expression(self, node: Any, ctx: Context) -> Value:
        self.budget.tick()
        return super().expression(node, ctx)

    def effective(self, name: str):
        self.budget.tick()
        return super().effective(name)

    def expand(self, node: Any, path: str, owner: str | None, ids: tuple[str, ...], context: Context) -> None:
        self.budget.tick()
        if len(self.instances) >= self.budget.limits["max_objects"]:
            self.budget.exhausted("max_objects", len(self.instances) + 1, node)
        super().expand(node, path, owner, ids, context)

    def guarded(self, key: tuple[str, str], node: Any, compute) -> Value:
        self.budget.tick()
        if self.pending and self.pending[-1] != key:
            self.dependencies.setdefault(self.pending[-1], set()).add(key)
        return super().guarded(key, node, compute)

    def invoke(self, function: Any, args: list[Value], node: Any, caller: Context) -> Value:
        self.budget.tick()
        if self.pending and not caller.abstract:
            ids = ((self.model.module_key, "definitions", function.node.key) if function.lexical_class is None
                   else _definition_id(self, function.lexical_class, function.node))
            self.call_dependencies.setdefault(self.pending[-1], set()).add(ids)
        return super().invoke(function, args, node, caller)


def _raw(source: Source) -> bytes:
    if not isinstance(source, Source):
        raise TypeError("The agent runtime requires a revision-bound Source.")
    raw = source.raw
    if not isinstance(raw, bytes) or len(raw) > MAX_SOURCE_BYTES:
        raise OntoKinError("OKL-E-RESOURCE", "The source exceeds the 2 MB reference budget.",
                           category="resource_limit", phase="lexical")
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OntoKinError("OKL-E-LEXICAL", "The snapshot is not valid UTF-8.",
                           Node("span", exc.start, exc.end), phase="lexical") from exc
    if decoded != source.text:
        raise OntoKinError("OKL-E-REVISION", "Source text and immutable snapshot bytes disagree.",
                           category="stale", phase="edit", rule_ids=["LANG-025"])
    if source.revision != "sha256:" + hashlib.sha256(raw).hexdigest():
        raise OntoKinError("OKL-E-REVISION", "The source revision does not identify these immutable bytes.",
                           category="stale", phase="edit", rule_ids=["LANG-025"])
    return raw


def _walk(node: Any, budget: _Budget):
    stack = [node]
    seen = set()
    while stack:
        item = stack.pop()
        if isinstance(item, Node):
            if id(item) in seen:
                continue
            seen.add(id(item))
            budget.tick()
            yield item
            stack.extend(reversed(list(item.data.values())))
        elif isinstance(item, (list, tuple)):
            stack.extend(reversed(item))
        elif isinstance(item, dict):
            stack.extend(reversed(list(item.values())))


def _parse(source: Source, budget: _Budget) -> Node:
    budget.tick()
    _raw(source)
    ast = parse(source.text, source.filename)
    for _ in _walk(ast, budget):
        pass
    budget.tick()
    return ast


def _compile(source: Source, budget: _Budget, ast: Node | None = None) -> _RuntimeValidator:
    ast = ast if ast is not None else _parse(source, budget)
    compiler = _RuntimeValidator(ast, budget)
    try:
        compiler.run()
    except OntoKinError as exc:
        compiler.annotate(exc)
        raise
    except RecursionError as exc:
        raise OntoKinError("OKL-E-RESOURCE", "Semantic nesting exceeds the local runtime stack budget.",
                           ast, category="resource_limit", phase="elaboration") from exc
    budget.tick()
    return compiler


def _support(compiler: _RuntimeValidator) -> None:
    model = compiler.model
    for diagnostic in model.diagnostics:
        if diagnostic.category == "unsupported":
            error = OntoKinError(diagnostic.code, diagnostic.message, diagnostic.node,
                                category="unsupported", phase="support",
                                details=copy.deepcopy(diagnostic.details))
            compiler.annotate(error)
            raise error
    if model.requested_capabilities:
        raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "The required capabilities are not supplied by core-0.1: " +
                           ", ".join(model.requested_capabilities), compiler.program.requires[0],
                           category="unsupported", phase="support", blocks=["constructed", "evaluated", "delivered"])


def _result(source: Source, requested: str | None, achieved: str | None, diagnostics: list[dict],
            outcome: str = "valid", **payload: Any) -> dict:
    return {"schema_version": SCHEMA_VERSION, "source_revision": source.revision,
            "requested_level": requested, "achieved_level": achieved, "outcome": outcome,
            "diagnostics": diagnostics, **payload}


def _error_result(source: Source, requested: str | None, achieved: str | None,
                  error: OntoKinError, diagnostics: list[dict] | None = None, **payload: Any) -> dict:
    diagnostic = error.diagnostic.to_dict(source)
    earlier = [d for d in diagnostics or [] if not (d["code"] == diagnostic["code"] and d["primary"] == diagnostic["primary"])]
    return _result(source, requested, achieved, earlier + [diagnostic], error.diagnostic.category, **payload)


def _run_state(source: Source, prefix: dict, *, previous: dict | None = None) -> dict:
    error = prefix["failure"]
    diagnostic = None if error is None else error.diagnostic.to_dict(source, (previous or {}).get("run_id"))
    failure = None if error is None else {
        "time_seconds": None if error.diagnostic.time is None else time_text(error.diagnostic.time),
        "side": error.diagnostic.side, "diagnostic": diagnostic,
        "last_valid_interval_only": True,
    }
    state = {"source_revision": source.revision, "valid_until_seconds": prefix["valid_until_seconds"],
             "valid_until_side": prefix["valid_until_side"], "status": "ready" if error is None else "failed",
             "failure": failure, "last_valid_state": prefix["last_valid_state"],
             "boundary_times_seconds": prefix["boundary_times_seconds"]}
    if error is not None and previous is not None and previous.get("last_valid_state") is not None:
        # Replaying under a smaller budget may stop before a formerly committed
        # prefix. An attempted extension never erases that existing evidence.
        prior = _point(exact_time(previous["valid_until_seconds"]), previous["valid_until_side"])
        current = None if state["valid_until_seconds"] is None else _point(
            exact_time(state["valid_until_seconds"]), state["valid_until_side"])
        if current is None or current < prior:
            for key in ("valid_until_seconds", "valid_until_side", "last_valid_state", "boundary_times_seconds"):
                state[key] = copy.deepcopy(previous.get(key, []))
            state["retained_prior_prefix"] = True
    if previous is not None and "run_id" in previous:
        state["run_id"] = previous["run_id"]
    return state


def _levels(compiler: _RuntimeValidator) -> dict:
    unavailable = bool(compiler.model.requested_capabilities or any(d.category == "unsupported" for d in compiler.model.diagnostics))
    return {"represented": "valid", "construction_support": "unsupported" if unavailable else "available",
            "evaluated": "not_requested", "delivered": "requires_named_external_contract"}


def validate_revision(source: Source, *, level: str = "represented", budgets: dict | None = None,
                      check: Callable[[], None] | None = None) -> dict:
    """Validate one requested stage; evaluated means the complete fresh horizon."""
    achieved = None
    diagnostics: list[dict] = []
    stages = {"represented": "unavailable", "constructed": "not_requested", "evaluated": "not_requested"}
    try:
        budget = _Budget(budgets, check)
        compiler = _compile(source, budget)
        diagnostics = [d.to_dict(source) for d in compiler.model.diagnostics]
        achieved = "represented"
        stages.update(_levels(compiler))
        if level not in ("represented", "constructed", "evaluated", "delivered"):
            raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", f"Unknown requested output level {level!r}.",
                               compiler.program, category="unsupported", phase="support")
        if level == "represented":
            return _result(source, level, achieved, diagnostics, stages=stages,
                           duration_seconds=time_text(compiler.model.duration))
        if level == "delivered":
            raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "A delivered request requires an explicit supported destination contract.",
                               compiler.program, category="unsupported", phase="support", blocks=["delivered"])
        _support(compiler)
        prefix = evaluate_prefix(compiler.model, "0", side="before", check=budget.tick)
        if prefix["failure"] is not None:
            error = prefix["failure"]
            if error.diagnostic.category == "numerical_failure":
                error.diagnostic.phase = "elaboration"
                error.diagnostic.blocks = ["constructed", "evaluated", "delivered"]
            return _error_result(source, level, achieved, error, diagnostics, stages=stages,
                                 run_state=_run_state(source, prefix))
        achieved = "constructed"
        stages["constructed"] = "valid"
        if level == "constructed":
            return _result(source, level, achieved, diagnostics, stages=stages,
                           duration_seconds=time_text(compiler.model.duration), initial_state=prefix["last_valid_state"])
        prefix = evaluate_prefix(compiler.model, compiler.model.duration, check=budget.tick)
        run = _run_state(source, prefix)
        if prefix["failure"] is not None:
            stages["evaluated"] = prefix["failure"].diagnostic.category
            return _error_result(source, level, achieved, prefix["failure"], diagnostics, stages=stages, run_state=run)
        stages["evaluated"] = "valid"
        return _result(source, level, "evaluated", diagnostics, stages=stages, run_state=run,
                       duration_seconds=time_text(compiler.model.duration))
    except _Interrupt as exc:
        raise exc.error
    except OntoKinError as exc:
        return _error_result(source, level, achieved, exc, diagnostics, stages=stages)


def _interval(source: Source, run: dict, *, node: Any = None) -> tuple[Fraction, str]:
    if not isinstance(run, dict) or run.get("source_revision") != source.revision:
        raise OntoKinError("OKL-E-SAMPLE", "The run does not identify this source revision.", node,
                           category="stale", phase="inspection", blocks=[], rule_ids=["LANG-025", "LANG-027"])
    if run.get("valid_until_seconds") is None or run.get("valid_until_side") not in ("before", "after"):
        raise OntoKinError("OKL-E-SAMPLE", "This run has no available evaluated interval.", node,
                           phase="inspection", blocks=[])
    return exact_time(run["valid_until_seconds"]), run["valid_until_side"]


def _point(time: Fraction, side: str) -> tuple[Fraction, bool]:
    return time, side == "after"


def evaluate_revision(source: Source, *, until: Any, side: str = "after", previous: dict | None = None,
                      budgets: dict | None = None, check: Callable[[], None] | None = None) -> dict:
    """Return a forward, revision-bound run descriptor; never preflight its future."""
    achieved = None
    diagnostics: list[dict] = []
    try:
        budget = _Budget(budgets, check)
        compiler = _compile(source, budget)
        achieved = "represented"
        diagnostics = [d.to_dict(source) for d in compiler.model.diagnostics]
        _support(compiler)
        endpoint = exact_time(until)
        if side not in ("before", "after"):
            raise OntoKinError("OKL-E-SAMPLE", "A run boundary side must be before or after.",
                               compiler.program.scene, phase="inspection", blocks=[])
        if previous is not None:
            prior_time, prior_side = _interval(source, previous, node=compiler.program.scene)
            if _point(endpoint, side) < _point(prior_time, prior_side):
                raise OntoKinError("OKL-E-SAMPLE", "An existing run cannot evaluate backward.", compiler.program.scene,
                                   category="conflict", phase="inspection", blocks=[],
                                   details={"valid_until_seconds": time_text(prior_time), "valid_until_side": prior_side})
            if previous.get("status") == "failed":
                raise OntoKinError("OKL-E-SAMPLE", "A failed run is retained for diagnosis; reset to start a new run.",
                                   compiler.program.scene, phase="inspection", blocks=[])
        prefix = evaluate_prefix(compiler.model, endpoint, side=side, check=budget.tick)
        run = _run_state(source, prefix, previous=previous)
        if run["last_valid_state"] is not None:
            achieved = "constructed"
        if prefix["failure"] is not None:
            return _error_result(source, "evaluated", achieved, prefix["failure"], diagnostics, run_state=run)
        return _result(source, "evaluated", "evaluated", diagnostics, run_state=run,
                       duration_seconds=time_text(compiler.model.duration))
    except _Interrupt as exc:
        raise exc.error
    except OntoKinError as exc:
        return _error_result(source, "evaluated", achieved, exc, diagnostics)


def _span(source: Source, node: Any) -> dict | None:
    if node is None:
        return None
    return {"file": source.filename, "start_byte": node.start, "end_byte": node.end}


def _scope(source: Source, node: Any, ids: tuple[str, ...] | list[str], kind: str) -> dict:
    return {**_span(source, node), "element_id": list(ids), "scope": kind}


def _base_record(source: Source, ids: tuple[str, ...], kind: str, path: str, name: str,
                 node: Any, *, writable: bool = False, definition: bool = False,
                 owner: tuple[str, ...] | None = None, definition_id: tuple[str, ...] | None = None,
                 definition_node: Any = None) -> dict:
    return {"element_id": list(ids), "kind": kind, "path": path,
            "identity": {"element_id": list(ids), "kind": kind, "key": ids[-1], "key_path": list(ids),
                         "name": name, "display_identifier": name, "source_revision": source.revision,
                         "definition_id": None if definition_id is None else list(definition_id),
                         "definition_revision": source.revision if definition_id else None,
                         "is_definition": definition, "owner": None if owner is None else list(owner),
                         "children": [], "class_name": None, "role": None},
            "source": {"source_revision": source.revision, "declaration_span": _span(source, node),
                       "definition_span": _span(source, definition_node),
                       "writable_spans": [_scope(source, node, ids, "definition" if definition else "declaration")] if writable else [],
                       "shared_declaration": bool(node is not None and not writable and not definition)},
            "_definition": definition}


def _definition_id(compiler: _RuntimeValidator, class_name: str, member: Any = None) -> tuple[str, ...]:
    if class_name == "Object":
        base = (compiler.model.module_key, "@system", "Object")
    else:
        base = (compiler.model.module_key, "definitions", compiler.class_nodes[class_name].key)
    return base if member is None else base + (member.key,)


def _field_id(compiler: _RuntimeValidator, path: str, name: str) -> tuple[str, ...]:
    instance = compiler.instances[path]
    member = instance.cls.members.get(name)
    return instance.model.element_id + ((member.node.key,) if member is not None else ("@system", name))


def _syntax_records(source: Source, ast: Node, budget: _Budget) -> list[dict]:
    if not KEY_RE.fullmatch(ast.module_key):
        return []
    module = (ast.module_key,)
    records = [_base_record(source, module, "module", ast.module_name, ast.module_name,
                            Node("span", 0, len(source.raw)), writable=True)]
    for declaration in ast.definitions:
        budget.tick()
        if not KEY_RE.fullmatch(declaration.key):
            continue
        ids = (ast.module_key, "definitions", declaration.key)
        record = _base_record(source, ids, declaration.kind, "definitions." + declaration.name,
                              declaration.name, declaration, writable=True, definition=True, owner=module)
        if declaration.kind == "class":
            record["identity"]["class_name"] = declaration.name
        records.append(record)
        for member in optional(declaration, "members", []):
            budget.tick()
            if optional(member, "key") is None or not KEY_RE.fullmatch(member.key):
                continue
            member_kind = "property" if member.kind in ("param", "derive") else member.kind
            item = _base_record(source, ids + (member.key,), member_kind,
                                "definitions." + declaration.name + "." + member.name,
                                member.name, member, writable=True, definition=True, owner=ids)
            item["identity"]["declaration_kind"] = member.kind
            records.append(item)
    scene_ids = module + (ast.scene.key,)
    if not KEY_RE.fullmatch(ast.scene.key) or ast.scene.key == "definitions":
        return records
    records.append(_base_record(source, scene_ids, "scene", ast.scene.name, ast.scene.name,
                                ast.scene, writable=True, owner=module))
    for node in ast.scene.members:
        budget.tick()
        if optional(node, "key") is None or not KEY_RE.fullmatch(node.key):
            continue
        records.append(_base_record(source, scene_ids + (node.key,), node.kind,
                                    node.name, node.name, node, writable=True, owner=scene_ids))
    return records


def _header_record(source: Source, error: OntoKinError, budget: _Budget) -> list[dict]:
    """Recover only a lexically verified header identity after a body failure."""
    budget.tick()
    _raw(source)
    prefix = source.text
    if error.diagnostic.phase == "lexical" and error.diagnostic.node is not None:
        prefix = source.raw[:error.diagnostic.node.start].decode("utf-8")
    try:
        parser = Parser(lex(prefix))
        parser.take("ontokin")
        parser.take("STRING")
        parser.take(";")
        parser.take("module")
        name = parser.take("IDENT").value
        key = parser.identity()
        parser.take(";")
        if not KEY_RE.fullmatch(key):
            return []
    except (OntoKinError, UnicodeDecodeError):
        return []
    return [_base_record(source, (key,), "module", name, name,
                         Node("span", 0, len(source.raw)), writable=True)]


def _initializer_scope(source: Source, compiler: _RuntimeValidator, path: str, name: str) -> tuple[Any, Any]:
    """Return a unique scene initializer assignment, never a class part copy."""
    root = compiler.instances[path.split(".")[0]].model
    expression = compiler.instances[path].overrides.get(name)
    if expression is None:
        return root, None
    for assignment in root.span.assignments:
        if assignment.value is expression.expression:
            return root, assignment
    return root, None


def _initializer_available(compiler: _RuntimeValidator, root: Any, path: str, name: str) -> bool:
    names = path.split(".")[1:] + [name]
    try:
        compiler.initializer_type(root.class_name, names, root.span)
    except OntoKinError as exc:
        if exc.diagnostic.category == "resource_limit":
            raise
        return False
    return True


def _index(source: Source, ast: Node, compiler: _RuntimeValidator | None, budget: _Budget) -> list[dict]:
    records = _syntax_records(source, ast, budget)
    if compiler is not None:
        # Replace scene-level syntax records by their elaborated occurrences.
        scene_prefix = (ast.module_key, ast.scene.key)
        records = [r for r in records if len(r["element_id"]) <= 2 or tuple(r["element_id"][:2]) != scene_prefix]
        model = compiler.model
        for path, obj in model.objects.items():
            budget.tick()
            cls = compiler.instances[path].cls
            owner_ids = model.objects[obj.owner].element_id if obj.owner else scene_prefix
            root = model.objects[path.split(".")[0]]
            item = _base_record(source, obj.element_id, "object", path, obj.name, obj.span,
                                writable=obj.owner is None, owner=owner_ids,
                                definition_id=_definition_id(compiler, obj.class_name), definition_node=cls.node)
            item["identity"].update({"class_name": obj.class_name, "role": obj.role})
            item["_object_path"] = path
            item["source"]["initializer_target"] = {
                "element_id": list(root.element_id), "span": _span(source, root.span),
                "parameter_path_prefix": path[len(root.path):].lstrip("."),
                "note": "Nested writes must end in an accessible public parameter; built-in nested fields are not writable."}
            if obj.owner is not None:
                member = compiler.instances[obj.owner].cls.members[obj.name]
                item["source"]["declaration_definition_id"] = list(_definition_id(compiler, member.declaring, member.node))
            records.append(item)
            names = list(FIELD_TYPES) + [name for name, member in cls.members.items() if member.node.kind in ("param", "derive")]
            for name in names:
                budget.tick()
                member = cls.members.get(name)
                ids = _field_id(compiler, path, name)
                definition_node = None if member is None else member.node
                definition_id = None if member is None else _definition_id(compiler, member.declaring, member.node)
                root, assignment = _initializer_scope(source, compiler, path, name)
                prop = _base_record(source, ids, "property", path + "." + name, name,
                                    assignment if assignment is not None else definition_node,
                                    owner=obj.element_id, definition_id=definition_id, definition_node=definition_node)
                prop["identity"].update({"class_name": obj.class_name, "declaration_kind": member.node.kind if member else "builtin_field"})
                prop["source"]["writable_spans"] = []
                # LANG-025 targets initializer changes with the occurrence ID,
                # not with a property identity referring to a shared default.
                if assignment is not None:
                    prop["source"]["initializer_assignment"] = _span(source, assignment)
                prop["source"]["initializer_target"] = {
                    "element_id": list(root.element_id), "span": _span(source, root.span),
                    "parameter_path": (path[len(root.path):].lstrip(".") + "." if path != root.path else "") + name,
                    "available": _initializer_available(compiler, root, path, name)}
                prop["_object_path"], prop["_value_name"] = path, name
                records.append(prop)
        for kind, collection in (("site", model.sites), ("joint", model.joints), ("follow", model.follows), ("action", model.actions)):
            for path, value in collection.items():
                budget.tick()
                ids = value.element_id
                owner_path = value.owner if kind == "site" else path.rpartition(".")[0] or None
                owner_ids = model.objects[owner_path].element_id if owner_path in model.objects else scene_prefix
                implicit = kind == "site" and ids[-2:] == ("@system", "origin")
                local = owner_ids == scene_prefix and not implicit
                item = _base_record(source, ids, kind, path, path.rsplit(".", 1)[-1],
                                    None if implicit else value.span, writable=local, owner=owner_ids)
                item["_relation_path"] = path
                if implicit:
                    item["source"]["origin"] = "builtin"
                elif not local:
                    member = compiler.instances[owner_path].cls.members[path.rsplit(".", 1)[-1]]
                    definition_id = _definition_id(compiler, member.declaring, member.node)
                    item["identity"]["definition_id"] = list(definition_id)
                    item["identity"]["definition_revision"] = source.revision
                    item["source"]["definition_span"] = _span(source, member.node)
                records.append(item)
    # Never expose an ambiguous stable identity as a writable target, including
    # partially parsed candidates with duplicate keys.
    counts: dict[tuple[str, ...], int] = {}
    for record in records:
        budget.tick()
        ids = tuple(record["element_id"])
        counts[ids] = counts.get(ids, 0) + 1
    ambiguous = {ids for ids, count in counts.items() if count > 1}
    records = [r for r in records if not any(tuple(r["element_id"][:length]) in ambiguous
                                           for length in range(1, len(r["element_id"]) + 1))]
    by_id = {tuple(record["element_id"]): record for record in records}
    for record in records:
        budget.tick()
        owner = record["identity"]["owner"]
        if owner is not None and tuple(owner) in by_id:
            by_id[tuple(owner)]["identity"]["children"].append(record["element_id"])
    return sorted(records, key=lambda r: tuple(r["element_id"]))


def _index_context(source: Source, budget: _Budget) -> tuple[list[dict], _RuntimeValidator | None, list[dict], bool]:
    ast = None
    try:
        ast = _parse(source, budget)
        compiler = _compile(source, budget, ast)
    except OntoKinError as exc:
        if exc.diagnostic.category == "resource_limit":
            raise
        records = _index(source, ast, None, budget) if ast is not None else _header_record(source, exc, budget)
        return records, None, [exc.diagnostic.to_dict(source)], False
    return _index(source, ast, compiler, budget), compiler, [d.to_dict(source) for d in compiler.model.diagnostics], True


def source_index(source: Source, *, budgets: dict | None = None,
                 check: Callable[[], None] | None = None) -> dict:
    """Return bounded, byte-exact source scopes and separate occurrence identities."""
    try:
        budget = _Budget(budgets, check)
        records, compiler, diagnostics, complete = _index_context(source, budget)
        limit = budget.limits["max_result_items"]
        items = [{key: record[key] for key in ("element_id", "kind", "path", "identity", "source")} for record in records[:limit]]
        return _result(source, None, "represented" if compiler else None, diagnostics,
                       items=items, total=len(records), truncated=len(records) > limit,
                       next_offset=limit if len(records) > limit else None, index_complete=complete)
    except _Interrupt as exc:
        raise exc.error


def apply_patches(source: Source, patches: list[dict], *, budgets: dict | None = None,
                  check: Callable[[], None] | None = None) -> Source:
    """Check all byte and scope preconditions, then form one unaccepted snapshot."""
    try:
        budget = _Budget(budgets, check)
        raw = _raw(source)
        if not isinstance(patches, list) or not patches or len(patches) > budget.limits["max_result_items"]:
            raise OntoKinError("OKL-E-REVISION", "An edit requires a bounded, nonempty patch list.",
                               category="conflict", phase="edit", rule_ids=["LANG-025"])
        records, _, _, _ = _index_context(source, budget)
        by_id = {tuple(record["element_id"]): record for record in records}
        prepared = []
        for patch in patches:
            budget.tick()
            required = {"element_id", "start_byte", "end_byte", "expected_text", "replacement"}
            if not isinstance(patch, dict) or set(patch) != required:
                raise OntoKinError("OKL-E-REVISION", "Patch members must match the versioned edit contract.",
                                   category="conflict", phase="edit", rule_ids=["LANG-025"])
            ids = patch["element_id"]
            start, end = patch["start_byte"], patch["end_byte"]
            if not isinstance(ids, list) or not ids or not all(isinstance(key, str) for key in ids):
                raise OntoKinError("OKL-E-REVISION", "A patch must name a known stable element identity.",
                                   category="conflict", phase="edit", rule_ids=["LANG-025"])
            if type(start) is not int or type(end) is not int or not 0 <= start <= end <= len(raw):
                raise OntoKinError("OKL-E-REVISION", "Patch byte coordinates are outside this snapshot.",
                                   category="conflict", phase="edit", rule_ids=["LANG-025"])
            node = Node("span", start, end)
            if not isinstance(patch["expected_text"], str) or not isinstance(patch["replacement"], str):
                raise OntoKinError("OKL-E-REVISION", "Patch text must be UTF-8 strings.", node,
                                   category="conflict", phase="edit", rule_ids=["LANG-025"])
            try:
                expected = patch["expected_text"].encode("utf-8")
                replacement = patch["replacement"].encode("utf-8")
                raw[:start].decode("utf-8")
                raw[start:end].decode("utf-8")
            except UnicodeError as exc:
                raise OntoKinError("OKL-E-REVISION", "Patch text or byte offsets split a UTF-8 character.", node,
                                   category="conflict", phase="edit", rule_ids=["LANG-025"]) from exc
            if raw[start:end] != expected:
                record = by_id.get(tuple(ids))
                raise OntoKinError("OKL-E-REVISION", "Patch expected_text does not match this immutable snapshot.", node,
                                   category="stale", phase="edit", rule_ids=["LANG-025"],
                                   element_id=ids if record is not None else None)
            record = by_id.get(tuple(ids))
            if record is None or not any(scope["start_byte"] <= start <= end <= scope["end_byte"] for scope in record["source"]["writable_spans"]):
                raise OntoKinError("OKL-E-REVISION", "Patch lies outside the identified element's writable source scope.", node,
                                   category="conflict", phase="edit", rule_ids=["LANG-025"],
                                   element_id=ids if record is not None else None,
                                   repair="Target the local occurrence initializer or explicitly target the shared definition identity.")
            prepared.append((start, end, replacement, ids))
        prepared.sort(key=lambda entry: (entry[0], entry[1]))
        for left, right in zip(prepared, prepared[1:]):
            if right[0] < left[1] or (left[0] == left[1] == right[0] == right[1]):
                raise OntoKinError("OKL-E-REVISION", "Patch ranges overlap or repeat an insertion offset.",
                                   Node("span", right[0], right[1]), category="conflict", phase="edit", rule_ids=["LANG-025"])
        size = len(raw) + sum(len(replacement) - (end - start) for start, end, replacement, _ in prepared)
        if size > MAX_SOURCE_BYTES:
            raise OntoKinError("OKL-E-RESOURCE", "Patched source exceeds the 2 MB reference budget.",
                               category="resource_limit", phase="edit", rule_ids=["LANG-025"])
        chunks = []
        cursor = 0
        for start, end, replacement, _ in prepared:
            budget.tick()
            chunks.extend((raw[cursor:start], replacement))
            cursor = end
        chunks.append(raw[cursor:])
        candidate = b"".join(chunks)
        budget.tick()
        return Source(candidate.decode("utf-8"), source.filename, candidate)
    except _Interrupt as exc:
        raise exc.error


def _unit(typ: Type) -> str | None:
    if typ.element is not None:
        return _unit(typ.element)
    if typ.dimension is None:
        return "m" if typ.kind == "Point3" else None
    terms = [name if power == 1 else f"{name}^{power}" for name, power in zip(("m", "kg", "s", "rad"), typ.dimension) if power]
    return "*".join(terms) or "1"


def _dependency(compiler: _RuntimeValidator, key: tuple[str, str]) -> dict:
    path, name = key
    if path in compiler.instances and name in FIELD_TYPES | compiler.instances[path].cls.members:
        ids = _field_id(compiler, path, name)
    else:
        value = next((group[path] for group in (compiler.model.sites, compiler.model.joints, compiler.model.follows, compiler.model.actions) if path in group), None)
        ids = None if value is None else value.element_id
    return {"element_id": None if ids is None else list(ids), "path": path if name.startswith("@") else path + "." + name,
            "source_revision": None, "relationship": "effective_value_dependency"}


def _value_record(source: Source, compiler: _RuntimeValidator, path: str, name: str) -> dict:
    compiler.budget.tick()
    instance = compiler.instances[path]
    member = instance.cls.members.get(name)
    value = compiler.memo[(path, name)]
    expression = None
    declaring = None
    origin = "defaulted"
    scope = "builtin"
    if name in instance.overrides:
        expression = instance.overrides[name].expression
        origin, scope = "authored", "initializer"
    elif name in instance.cls.defaults:
        expression, declaring = instance.cls.defaults[name]
        origin = "derived" if member is not None and member.node.kind == "derive" else "inherited" if declaring != instance.cls.name else "defaulted"
        scope = "definition"
    definition_id = None
    source_element_id = None
    if declaring is not None:
        definition_id = _definition_id(compiler, declaring)
        if member is not None and member.declaring == declaring:
            definition_id += (member.node.key,)
        source_element_id = definition_id
    elif expression is not None:
        root, assignment = _initializer_scope(source, compiler, path, name)
        if assignment is not None:
            source_element_id = root.element_id
        else:
            candidates = []
            for declaration in compiler.program.classes:
                for declared in declaration.members:
                    compiler.budget.tick()
                    if optional(declared, "key") is not None and declared.start <= expression.start <= expression.end <= declared.end:
                        candidates.append((declared.end - declared.start,
                                           _definition_id(compiler, declaration.name, declared)))
            if candidates:
                source_element_id = definition_id = min(candidates, key=lambda candidate: candidate[0])[1]
    dependencies = [_dependency(compiler, key) for key in sorted(compiler.dependencies.get((path, name), set()))]
    for dependency in dependencies:
        dependency["source_revision"] = source.revision
    dependencies.extend({"element_id": list(ids), "source_revision": source.revision,
                         "relationship": "called_definition"} for ids in sorted(compiler.call_dependencies.get((path, name), set())))
    result = {**value.to_data(), "canonical_unit": _unit(value.type), "display_unit": _unit(value.type),
              "display_unit_origin": "canonical_presentation", "status": "resolved" if value.known else "unresolved",
              "stale": False, "origin": {"category": origin if value.known else "unresolved",
                                         "scope": scope, "source_revision": source.revision,
                                         "source": _span(source, expression),
                                         "source_element_id": None if source_element_id is None else list(source_element_id),
                                         "definition_id": None if definition_id is None else list(definition_id)},
              "dependencies": dependencies, "dependency_basis": "observed_pure_elaboration_reads"}
    return result


def _support_record(compiler: _RuntimeValidator | None, budget: _Budget) -> dict:
    blocked = compiler is None or bool(compiler.model.requested_capabilities or
                                       any(d.category == "unsupported" for d in compiler.model.diagnostics))
    return {"profile": "core-0.1", "available_implementation_levels": ["represented", "constructed", "evaluated"],
            "source_supported_levels": [] if compiler is None else ["represented"] if blocked else ["represented", "constructed", "evaluated"],
            "requested_capabilities": [] if compiler is None else list(compiler.model.requested_capabilities),
            "limits": dict(budget.limits),
            "numerical_method": "analytical trajectories; exact rational event clock; binary64 spatial values",
            "approximations": {"physical_model": "homogeneous_solid_sphere", "inertia": "derived_from_authored_radius_and_mass"},
            "unavailable": ["contact_response", "collision_response", "connected_load_solution", "relative_frame_velocity", "unnamed_delivery_target"],
            "collision": "disabled", "source_resolved": compiler is not None}


def _relation_record(compiler: _RuntimeValidator, path: str, sample: dict | None) -> dict:
    model = compiler.model
    if path in model.sites:
        site = model.sites[path]
        return {"kind": "site", "frame": path + ".frame", "owner": list(model.objects[site.owner].element_id),
                "local_pose": asdict(site.pose), "interface": site.interface, "size_m": site.size,
                "world_state": {"available": sample is not None, "value": None if sample is None else sample["frames"][path + ".frame"]}}
    if path in model.joints:
        joint = model.joints[path]
        return {"kind": joint.kind, "parent_site": joint.parent, "parent_site_id": list(model.sites[joint.parent].element_id),
                "child_site": joint.child, "child_site_id": list(model.sites[joint.child].element_id),
                "axis": joint.axis, "limits": joint.limits, "initial_coordinate": joint.initial,
                "physical_interpretation": "externally_prescribed_no_load_solution",
                "current": {"available": sample is not None, "value": None if sample is None else sample["joints"][path]}}
    follow = model.follows[path]
    return {"kind": "follow", "parent_frame": follow.parent, "child": follow.child,
            "child_id": list(model.objects[follow.child].element_id), "offset": asdict(follow.offset),
            "physical_interpretation": "one_way_massless_spatial_following"}


def _object_relations(compiler: _RuntimeValidator, path: str, sample: dict | None) -> dict:
    model = compiler.model
    relations = []
    for name, joint in model.joints.items():
        compiler.budget.tick()
        if path in (model.sites[joint.parent].owner, model.sites[joint.child].owner):
            relations.append({"element_id": list(joint.element_id), "path": name, **_relation_record(compiler, name, sample)})
    for name, follow in model.follows.items():
        compiler.budget.tick()
        if path in (follow.child, model.frame_owner(follow.parent)):
            relations.append({"element_id": list(follow.element_id), "path": name, **_relation_record(compiler, name, sample)})
    sites = []
    for name, site in model.sites.items():
        compiler.budget.tick()
        if site.owner == path:
            sites.append({"element_id": list(site.element_id), "path": name})
    return {"frame": path + ".frame", "incoming_authority": {"available": sample is not None,
            "value": None if sample is None else sample["objects"][path]["pose_authority"]},
            "sites": sites,
            "connections": relations, "collision": "disabled"}


def _action_record(compiler: _RuntimeValidator, path: str, sample: dict | None) -> dict:
    action = compiler.model.actions[path]
    target = compiler.model.joints[action.target] if action.kind == "tween" else compiler.model.objects[action.target]
    return {"element_id": list(action.element_id), "description_identity": list(action.element_id),
            "kind": action.kind, "target": action.target, "target_id": list(target.element_id),
            "channel": {"move": "translation", "spin": "orientation", "tween": "coordinate"}[action.kind],
            "duration_seconds": time_text(action.duration), "vector": action.vector, "goal": action.goal,
            "current": {"available": sample is not None, "reason": "run_required" if sample is None else None,
                        "value": None if sample is None else sample["actions"][path]}}


def _selected(record: dict, selector: dict, compiler: _RuntimeValidator | None,
              relation_paths: set[str | None] | None = None) -> bool:
    identity = record["identity"]
    for name in ("kind", "path", "element_id"):
        if name in selector and record[name] != selector[name]:
            return False
    if "class_name" in selector:
        actual = identity.get("class_name")
        if record["kind"] != "object" or actual is None or compiler is None or not compiler.subtype(actual, selector["class_name"]):
            return False
    if "role" in selector and identity.get("role") != selector["role"]:
        return False
    if "relation" in selector:
        if relation_paths is None or record["path"] not in relation_paths:
            return False
    return True


def _query(selector: dict | None, fields: list[str] | None, limit: int, offset: int, budget: _Budget) -> tuple[dict, list[str]]:
    selector = {} if selector is None else selector
    fields = list(INSPECTION_FIELDS) if fields is None else fields
    if not isinstance(selector, dict) or set(selector) - {"element_id", "kind", "path", "class_name", "role", "relation"}:
        raise OntoKinError("OKL-E-SAMPLE", "Unsupported inspection selector.", phase="inspection", blocks=[])
    for key, value in selector.items():
        if key == "element_id" or key == "relation" and isinstance(value, list):
            if not isinstance(value, list) or not value or not all(isinstance(part, str) for part in value):
                raise OntoKinError("OKL-E-SAMPLE", "An identity selector requires a nonempty string key path.", phase="inspection", blocks=[])
        elif not isinstance(value, str):
            raise OntoKinError("OKL-E-SAMPLE", "An inspection selector has an invalid value type.", phase="inspection", blocks=[])
    if not isinstance(fields, list) or not fields or any(not isinstance(field, str) for field in fields) or len(fields) != len(set(fields)) or any(field not in INSPECTION_FIELDS for field in fields):
        raise OntoKinError("OKL-E-SAMPLE", "Inspection fields must be a nonempty set of supported field groups.", phase="inspection", blocks=[])
    if type(limit) is not int or not 1 <= limit <= budget.limits["max_result_items"] or type(offset) is not int or offset < 0:
        raise OntoKinError("OKL-E-SAMPLE", "Inspection limit or offset exceeds the bounded result contract.", phase="inspection", blocks=[])
    return selector, sorted(fields)


def _project(source: Source, record: dict, fields: list[str], compiler: _RuntimeValidator | None,
             sample: dict | None, run: dict | None, frame: str, budget: _Budget) -> dict:
    budget.tick()
    result = {key: record[key] for key in ("element_id", "kind", "path")}
    for key in ("identity", "source"):
        if key in fields:
            result[key] = copy.deepcopy(record[key])
    path = record.get("_object_path")
    if "support" in fields:
        result["support"] = _support_record(compiler, budget)
    if compiler is None or record["_definition"]:
        for key in fields:
            if key not in result:
                result[key] = {"available": False, "reason": "definition_has_no_occurrence_state" if record["_definition"] else "source_is_unresolved"}
        return result
    model = compiler.model
    if "values" in fields:
        if path is not None:
            names = [record["_value_name"]] if "_value_name" in record else list(FIELD_TYPES) + list(model.objects[path].properties)
            result["values"] = {name: _value_record(source, compiler, path, name) for name in names}
        else:
            result["values"] = {"available": False, "reason": "not_an_object_value_record"}
    if "geometry" in fields:
        result["geometry"] = {"available": path is not None, "description": None if path is None else model.objects[path].geometry,
                              "appearance_rgba_linear": None if path is None else model.objects[path].appearance,
                              "representation": "authored_analytic_geometry"}
    if "matter" in fields:
        if path is not None:
            obj = model.objects[path]
            mass = sum((Fraction(other.mass) for other in model.objects.values() if other.path == path or other.path.startswith(path + ".")), Fraction(0))
            try:
                owned_mass = float(mass)
                if owned_mass == float("inf"):
                    raise OverflowError
            except OverflowError:
                owned_mass = None
            result["matter"] = {"body_model": obj.physical, "own_mass_kg": obj.mass,
                                "owned_aggregate_mass_kg": owned_mass, "owned_aggregate_available": owned_mass is not None,
                                "inertia_kg_m2": obj.inertia, "inertia_origin": "derived" if obj.inertia is not None else "unavailable",
                                "connected_loads": {"available": False, "reason": "no_load_solution"}, "collision": "disabled"}
        else:
            result["matter"] = {"available": False, "reason": "not_an_object"}
    if "relations" in fields:
        relation_path = record.get("_relation_path")
        if path is not None:
            result["relations"] = _object_relations(compiler, path, sample)
        elif relation_path in model.sites or relation_path in model.joints or relation_path in model.follows:
            result["relations"] = _relation_record(compiler, relation_path, sample)
        else:
            result["relations"] = {"available": False, "reason": "not_a_relation_record"}
    if "actions" in fields:
        names = [record["path"]] if record["path"] in model.actions else []
        if path is not None:
            names = []
            for name, action in model.actions.items():
                budget.tick()
                if action.target == path or (action.target in model.joints and path in (
                    model.sites[model.joints[action.target].parent].owner, model.sites[model.joints[action.target].child].owner)):
                    names.append(name)
        result["actions"] = [_action_record(compiler, name, sample) for name in names]
    if "state" in fields:
        if sample is None:
            result["state"] = {"available": False, "reason": "run_required"}
        elif path is not None:
            state = copy.deepcopy(sample["objects"][path])
            if frame != "world":
                state.update(inspect_in_frame(sample, path, frame))
            state.update({"available": True, "source_revision": source.revision, "run_id": run.get("run_id"),
                          "time_seconds": sample["time_seconds"], "side": sample["side"],
                          "valid_interval": {"start_seconds": "0", "start_side": "before",
                                             "end_seconds": run["valid_until_seconds"], "end_side": run["valid_until_side"]}})
            result["state"] = state
        else:
            result["state"] = {"available": False, "reason": "use_relations_or_actions_for_this_record"}
    return result


def inspect_revision(source: Source, *, selector: dict | None = None, fields: list[str] | None = None,
                     limit: int = 100, offset: int = 0, run: dict | None = None, time: Any = None,
                     side: str = "after", frame: str = "world", budgets: dict | None = None,
                     check: Callable[[], None] | None = None) -> dict:
    """Read a bounded source or already-evaluated interval; never extend a run."""
    diagnostics: list[dict] = []
    achieved = None
    try:
        budget = _Budget(budgets, check)
        selector, fields = _query(selector, fields, limit, offset, budget)
        records, compiler, diagnostics, complete = _index_context(source, budget)
        achieved = "represented" if compiler is not None else None
        sample = None
        if run is not None and not isinstance(run, dict):
            raise OntoKinError("OKL-E-SAMPLE", "Inspection needs a valid revision-bound run descriptor.", phase="inspection", blocks=[])
        context = {"source_revision": source.revision, "run_id": None if run is None else run.get("run_id"),
                   "time_seconds": None, "side": None, "frame": frame, "selector": selector, "fields": fields}
        if not isinstance(frame, str) or side not in ("before", "after"):
            raise OntoKinError("OKL-E-SAMPLE", "Inspection frame or boundary side is invalid.", phase="inspection", blocks=[])
        if run is None and time is not None:
            raise OntoKinError("OKL-E-SAMPLE", "A current-state time requires a matching run.", phase="inspection", blocks=[])
        if run is not None:
            end, end_side = _interval(source, run)
            sample_time = end if time is None else exact_time(time)
            sample_side = end_side if time is None else side
            if compiler is None or not 0 <= sample_time <= compiler.model.duration or _point(sample_time, sample_side) > _point(end, end_side):
                raise OntoKinError("OKL-E-SAMPLE", "This sample lies outside the run's available evaluated interval.",
                                   phase="inspection", blocks=[], details={"valid_until_seconds": time_text(end), "valid_until_side": end_side})
            _support(compiler)
            prefix = evaluate_prefix(compiler.model, sample_time, side=sample_side, check=budget.tick)
            if prefix["failure"] is not None:
                return _error_result(source, None, achieved, prefix["failure"], diagnostics, items=[], total=0,
                                     next_offset=None, truncated=False, index_complete=complete)
            sample = prefix["last_valid_state"]
            if frame not in sample["frames"]:
                raise OntoKinError("OKL-E-SAMPLE", "The requested frame is absent from this evaluated snapshot.", phase="inspection", blocks=[])
            context.update({"time_seconds": sample["time_seconds"], "side": sample["side"]})
        selected = []
        relation_paths = None
        if "relation" in selector and compiler is not None:
            model = compiler.model
            relation = None
            for group in (model.joints, model.follows):
                for value in group.values():
                    budget.tick()
                    if value.path == selector["relation"] or list(value.element_id) == selector["relation"]:
                        relation = value
                        break
                if relation is not None:
                    break
            if relation is not None:
                relation_paths = {relation.path}
                if relation.path in model.joints:
                    relation_paths.update((relation.parent, relation.child, model.sites[relation.parent].owner, model.sites[relation.child].owner))
                else:
                    relation_paths.update((relation.child, model.frame_owner(relation.parent)))
        for record in records:
            budget.tick()
            if _selected(record, selector, compiler, relation_paths):
                selected.append(record)
        items = [_project(source, record, fields, compiler, sample, run, frame, budget)
                 for record in selected[offset:offset + limit]]
        next_offset = offset + len(items) if offset + len(items) < len(selected) else None
        payload = {"items": items, "total": len(selected), "offset": offset, "next_offset": next_offset,
                   "truncated": next_offset is not None, "index_complete": complete, "context": context}
        if "source" in fields:
            payload.update({"source_text": source.text, "filename": source.filename})
        return _result(source, None, achieved, diagnostics, **payload)
    except _Interrupt as exc:
        raise exc.error
    except OntoKinError as exc:
        return _error_result(source, None, achieved, exc, diagnostics, items=[], total=0, next_offset=None, truncated=False)
