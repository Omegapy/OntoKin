"""Pure bounded operations on an exact construction source bundle.

This layer never accepts a program or writes durable state. Source locations
come from each original unit; occurrence repair uses explicit initializer scope.
"""
from __future__ import annotations

import copy
from fractions import Fraction
from typing import Any, Callable

from . import agent_runtime as core
from .agent_runtime import _Interrupt, _point
from .bundle import ProgramBundle, load_bundle, BundleError
from .diagnostics import OntoKinError
from .evaluator import evaluate_prefix, exact_time, inspect_in_frame, time_text
from .json_limits import measure_json, JSONLimitError
from .program_diagnostics import diagnostic_dict
from .program_protocol import MAX_BUDGETS
from .program_bindings import PROFILE_BINDINGS
from .profile_capabilities import BUDGET_PROFILE, EXTRUSION_PROFILE, HOLES_PROFILE, RING_LOFT_PROFILE, FRAMED_LOFT_PROFILE, POCKETS_PROFILE, TEXTURE_PROFILE, KEYED_TRANSFORM_PROFILE, KEYED_REDUCTION_PROFILE, KEYED_FILTER_PROFILE, KEYED_MERGE_PROFILE, KEYED_ZIP_PROFILE, KEYED_REKEY_PROFILE, STRING_CONCAT_PROFILE, KEYED_MEMBERSHIP_PROFILE, TORQUE_PROFILE, KEYED_REKEY_PROFILES, KEYED_ZIP_PROFILES, KEYED_MERGE_PROFILES, KEYED_FILTER_PROFILES, KEYED_REDUCTION_PROFILES, KEYED_TRANSFORM_PROFILES, POCKETS_PROFILES, EXECUTION_PROFILES, REACH_PROFILES
from .syntax import Node
from .validator import FIELD_TYPES, optional
from .values import KeyedValue, Value, bounded_data

SCHEMA_VERSION = "ontokin.program-runtime/0.1"
CONSTRUCTION_PROFILE = "construction-0.1"
SURFACE_PROFILE = "surface-0.1"
IMPULSE_PROFILE = "impulse-0.1"
FORCE_PROFILE = "force-0.1"
REACH_PROFILE = "planar-reach-0.1"


class ProgramRuntime:
    """Bind existing pure operations to one explicit entry-language profile."""

    def __init__(self, profile=CONSTRUCTION_PROFILE):
        if not isinstance(profile, str) or profile not in PROFILE_BINDINGS:
            raise ValueError("Unknown program runtime profile.")
        self.profile = profile

    def validate_revision(self, source, **kwargs):
        return validate_revision(source, profile=self.profile, **kwargs)

    def evaluate_revision(self, source, **kwargs):
        return evaluate_revision(source, profile=self.profile, **kwargs)

    def inspect_revision(self, source, **kwargs):
        return inspect_revision(source, profile=self.profile, **kwargs)

    def apply_patches(self, source, patches, **kwargs):
        return apply_patches(source, patches, profile=self.profile, **kwargs)

    def compile_program(self, source, **kwargs):
        return compile_program(source, profile=self.profile, **kwargs)

    def prepare_delivery(self, source, **kwargs):
        return prepare_delivery(source, profile=self.profile, **kwargs)


class _Budget(core._Budget):
    def __init__(self, budgets=None, check=None, profile=CONSTRUCTION_PROFILE):
        incoming = {} if budgets is None else budgets
        if not isinstance(incoming, dict) or set(incoming) - set(MAX_BUDGETS):
            raise OntoKinError("OKL-E-RESOURCE", "Unknown program work budget.", category="resource_limit", phase="support")
        super().__init__({k: v for k, v in incoming.items() if k in core.MAX_BUDGETS}, check)
        value_limit = incoming.get("max_value_entries", MAX_BUDGETS["max_value_entries"])
        if type(value_limit) is not int or not 1 <= value_limit <= MAX_BUDGETS["max_value_entries"]:
            raise OntoKinError("OKL-E-RESOURCE", "Invalid logical value budget.", category="resource_limit", phase="support")
        self.limits["max_value_entries"] = value_limit
        self.profile = profile

    def data(self, value):
        try:
            return bounded_data(value, max_entries=self.limits["max_value_entries"], check=self.tick)
        except JSONLimitError as exc:
            raise OntoKinError("OKL-E-RESOURCE", "The program result exceeded its materialization budget.",
                               category="resource_limit", phase="support", details=exc.details) from exc

    def json(self, value):
        try:
            measure_json(value, max_entries=self.limits["max_value_entries"], check=self.tick)
        except JSONLimitError as exc:
            raise OntoKinError("OKL-E-RESOURCE", "The program result exceeded its materialization budget.",
                               category="resource_limit", phase="support", details=exc.details) from exc
        return value


def _request_budget(budgets=None, check=None, profile=CONSTRUCTION_PROFILE):
    """Select the explicit .7 adapter without changing legacy budget owners."""
    if isinstance(profile, str) and profile in EXECUTION_PROFILES:
        from .budget_program_runtime import ExecutionProgramBudget
        return ExecutionProgramBudget(budgets, check, profile=profile)
    return _Budget(budgets, check, profile)


def _compile(source: ProgramBundle, budget: _Budget):
    from .construction import compile_construction
    if budget.profile in EXECUTION_PROFILES:
        ledger = budget.execution_budget
        try:
            budget.context.admit(source)
            budget.limits.update(ledger.limits)
            ledger.stage = "construction"
            limits = {name: value for name, value in budget.limits.items()
                      if name not in ("max_operations", "max_elapsed_ms")}
            compiler = compile_construction(source, level="represented", budgets=limits,
                                            execution_budget=ledger)
        except BaseException as error:
            if error is ledger.callback_error:
                raise _Interrupt(error) from None
            raise
        budget.context._budget_program_compiler = (source.program_revision, compiler)
    else:
        compiler = compile_construction(source, level="represented", budgets=budget.limits, check=budget.tick)
    if compiler.model.profile != budget.profile:
        raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "This program binding requires a " + budget.profile + " entry source.",
                           compiler.program, category="unsupported", phase="support",
                           blocks=["represented", "constructed", "evaluated", "delivered"],
                           details={"required_profile": budget.profile, "actual_profile": compiler.model.profile})
    return compiler


def _reach_work(compiler):
    """Keep the explicit 0.6 request's bounded numerical context transient."""
    return {"work": compiler.reach_work} if compiler.model.profile in REACH_PROFILES else {}


def compile_program(source, *, budgets=None, check=None, profile=CONSTRUCTION_PROFILE):
    """Compile one profile-bound source model without creating a run or effects."""
    try:
        budget = _request_budget(budgets, check, profile)
        compiler = _compile(source, budget)
        _support(compiler)
        return compiler
    except _Interrupt as exc:
        raise exc.error


def _support(compiler: ConstructionCompiler) -> None:
    model = compiler.model
    for diagnostic in model.diagnostics:
        if diagnostic.category == "unsupported":
            error = OntoKinError(diagnostic.code, diagnostic.message, diagnostic.node,
                                category="unsupported", phase="support",
                                details=copy.deepcopy(diagnostic.details))
            compiler.annotate(error)
            raise error
    if model.requested_capabilities:
        raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "The required capabilities are not supplied by " + model.profile + ": " +
                           ", ".join(model.requested_capabilities), compiler.linked_program.capabilities[0],
                           category="unsupported", phase="support", blocks=["constructed", "evaluated", "delivered"])


def _result(source: ProgramBundle, requested: str | None, achieved: str | None, diagnostics: list[dict],
            outcome: str = "valid", **payload: Any) -> dict:
    return {"schema_version": SCHEMA_VERSION, "program_revision": source.program_revision,
            "requested_level": requested, "achieved_level": achieved, "outcome": outcome,
            "diagnostics": diagnostics, "source_manifest": source.manifest(), **payload}


def _error_result(source: ProgramBundle, requested: str | None, achieved: str | None,
                  error: OntoKinError, diagnostics: list[dict] | None = None, **payload: Any) -> dict:
    diagnostic = diagnostic_dict(error.diagnostic, source)
    earlier = [d for d in diagnostics or [] if not (d["code"] == diagnostic["code"] and d["primary"] == diagnostic["primary"])]
    return _result(source, requested, achieved, earlier + [diagnostic], error.diagnostic.category, **payload)


def _run_state(source: ProgramBundle, prefix: dict, *, budget: _Budget, previous: dict | None = None) -> dict:
    error = prefix["failure"]
    diagnostic = None if error is None else diagnostic_dict(error.diagnostic, source, (previous or {}).get("run_id"))
    failure = None if error is None else {
        "time_seconds": None if error.diagnostic.time is None else time_text(error.diagnostic.time),
        "side": error.diagnostic.side, "diagnostic": diagnostic,
        "last_valid_interval_only": True,
    }
    state = {"program_revision": source.program_revision, "valid_until_seconds": prefix["valid_until_seconds"],
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
    return budget.data(state)


def _levels(compiler: ConstructionCompiler) -> dict:
    unavailable = bool(compiler.model.requested_capabilities or any(d.category == "unsupported" for d in compiler.model.diagnostics))
    return {"represented": "valid", "construction_support": "unsupported" if unavailable else "available",
            "evaluated": "not_requested", "delivered": "requires_named_external_contract"}


def validate_revision(source: ProgramBundle, *, level: str = "represented", budgets: dict | None = None,
                      check: Callable[[], None] | None = None, profile=CONSTRUCTION_PROFILE) -> dict:
    """Validate one requested stage; evaluated means the complete fresh horizon."""
    achieved = None
    diagnostics: list[dict] = []
    stages = {"represented": "unavailable", "constructed": "not_requested", "evaluated": "not_requested"}
    try:
        budget = _request_budget(budgets, check, profile)
        compiler = _compile(source, budget)
        diagnostics = [diagnostic_dict(d, source) for d in compiler.model.diagnostics]
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
        if profile in EXECUTION_PROFILES:
            budget.execution_budget.stage = "evaluation"
        prefix = evaluate_prefix(compiler.model, "0", side="before", check=budget.tick, **_reach_work(compiler))
        if prefix["failure"] is not None:
            error = prefix["failure"]
            if error.diagnostic.category == "numerical_failure":
                error.diagnostic.phase = "elaboration"
                error.diagnostic.blocks = ["constructed", "evaluated", "delivered"]
            return _error_result(source, level, achieved, error, diagnostics, stages=stages,
                                 run_state=_run_state(source, prefix, budget=budget))
        achieved = "constructed"
        stages["constructed"] = "valid"
        if level == "constructed":
            return _result(source, level, achieved, diagnostics, stages=stages,
                           duration_seconds=time_text(compiler.model.duration), initial_state=budget.data(prefix["last_valid_state"]))
        prefix = evaluate_prefix(compiler.model, compiler.model.duration, check=budget.tick, **_reach_work(compiler))
        run = _run_state(source, prefix, budget=budget)
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


def _interval(source: ProgramBundle, run: dict, *, node: Any = None) -> tuple[Fraction, str]:
    if not isinstance(run, dict) or run.get("program_revision") != source.program_revision:
        raise OntoKinError("OKL-E-SAMPLE", "The run does not identify this source revision.", node,
                           category="stale", phase="inspection", blocks=[], rule_ids=["LANG-025", "LANG-027"])
    if run.get("valid_until_seconds") is None or run.get("valid_until_side") not in ("before", "after"):
        raise OntoKinError("OKL-E-SAMPLE", "This run has no available evaluated interval.", node,
                           phase="inspection", blocks=[])
    return exact_time(run["valid_until_seconds"]), run["valid_until_side"]


def _point(time: Fraction, side: str) -> tuple[Fraction, bool]:
    return time, side == "after"


def _evaluate_compiled(source, compiler, budget, until, *, side="after", previous=None, capture_observer=None):
    """Use the already compiled request context for a single source prefix."""
    achieved = "represented"
    diagnostics = [diagnostic_dict(d, source) for d in compiler.model.diagnostics]
    _support(compiler)
    if budget.profile in EXECUTION_PROFILES:
        budget.execution_budget.stage = "evaluation"
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
    prefix = evaluate_prefix(compiler.model, endpoint, side=side, check=budget.tick,
                             capture_observer=capture_observer, **_reach_work(compiler))
    run = _run_state(source, prefix, budget=budget, previous=previous)
    if run["last_valid_state"] is not None:
        achieved = "constructed"
    if prefix["failure"] is not None:
        return _error_result(source, "evaluated", achieved, prefix["failure"], diagnostics, run_state=run)
    return _result(source, "evaluated", "evaluated", diagnostics, run_state=run,
                   duration_seconds=time_text(compiler.model.duration))


def prepare_delivery(source, *, until=None, budgets=None, check=None, profile=REACH_PROFILE):
    """Return one transient compiler and prefix result for the 0.6 adapter.

    The compiler owns the request's numerical work/cache and checked recording
    plan; the exporter consumes those without replay or a fresh allowance.
    None of these transient objects is placed in returned JSON.
    """
    compiler, achieved, diagnostics = None, None, []
    try:
        budget = _request_budget(budgets, check, profile)
        compiler = _compile(source, budget)
        achieved = "represented"
        diagnostics = [diagnostic_dict(d, source) for d in compiler.model.diagnostics]
        endpoint = compiler.model.duration if until is None else until
        capture = None
        if profile in REACH_PROFILES:
            if budget.profile == TORQUE_PROFILE:
                from .torque_recording import TorqueDeliveryCapture as ReachDeliveryCapture
            else:
                from .reach_delivery import ReachDeliveryCapture
            capture = ReachDeliveryCapture(compiler.model, exact_time(endpoint), work=compiler.reach_work)
        result = _evaluate_compiled(source, compiler, budget, endpoint, capture_observer=capture)
        if capture is not None and result["outcome"] == "valid":
            compiler.reach_delivery_plan = capture.finish()
        return compiler, result
    except _Interrupt as exc:
        raise exc.error
    except OntoKinError as exc:
        return compiler, _error_result(source, "evaluated", achieved, exc, diagnostics)


def evaluate_revision(source: ProgramBundle, *, until: Any, side: str = "after", previous: dict | None = None,
                      budgets: dict | None = None, check: Callable[[], None] | None = None,
                      profile=CONSTRUCTION_PROFILE) -> dict:
    """Return a forward, revision-bound run descriptor; never preflight its future."""
    achieved = None
    diagnostics: list[dict] = []
    try:
        budget = _request_budget(budgets, check, profile)
        compiler = _compile(source, budget)
        achieved = "represented"
        diagnostics = [diagnostic_dict(d, source) for d in compiler.model.diagnostics]
        return _evaluate_compiled(source, compiler, budget, until, side=side, previous=previous)
    except _Interrupt as exc:
        raise exc.error
    except OntoKinError as exc:
        return _error_result(source, "evaluated", achieved, exc, diagnostics)



def _span(program, node):
    source_id = getattr(node, "source_id", None)
    source = program.sources.get(source_id)
    if source is None:
        return None
    return {"source_id": source_id, "source_revision": source.revision, "file": source.filename,
            "start_byte": node.start, "end_byte": node.end}


def _record(program, ids, kind, path, name, node=None, *, owner=None, definition_id=None,
            definition_node=None, writable=False, definition=False):
    span = _span(program, node)
    defined = _span(program, definition_node)
    return {"element_id": list(ids), "kind": kind, "path": path,
            "identity": {"name": name, "owner": None if owner is None else list(owner), "children": [],
                         "definition_id": None if definition_id is None else list(definition_id),
                         "definition_revision": None if defined is None else defined["source_revision"]},
            "source": {"program_revision": program.program_revision,
                       "source_id": None if span is None else span["source_id"],
                       "source_revision": None if span is None else span["source_revision"],
                       "span": span, "definition_span": defined,
                       "writable_spans": [span] if writable and span is not None else []},
            "_definition": definition}


def _file_records(program, budget=None):
    result = []
    for unit in program.units:
        if budget is not None:
            budget.tick()
        node = Node("source", 0, len(unit.raw))
        node.source_id = unit.source_id
        result.append(_record(program, ("sources", unit.source_id), "source", unit.source_id,
                              unit.filename, node, writable=True, definition=True))
    return result


def _target(program, compiler, path, name):
    target = compiler.initializer_target(path, name)
    if not target["available"]:
        return {"available": False, "reason": target.get("reason", "No public occurrence initializer is available.")}
    scope = _span(program, target["root_node"])
    element_id = (["sources", scope["source_id"]]
                  if compiler.model.profile in EXECUTION_PROFILES and scope is not None
                  else list(target["element_id"]))
    return {"available": target["available"], "reason": target.get("reason"),
            "element_id": element_id,
            "span": scope,
            "parameter_path": [{"kind": step.kind, "value": step.value} for step in target["parameter_path"]],
            "rendered_path": target["rendered_path"],
            "assignment_span": _span(program, target.get("assignment_node"))}


def _index(program, compiler, budget):
    records = _file_records(program, budget if budget.profile in EXECUTION_PROFILES else None)
    model = compiler.model
    scene_ids = (model.module_key, model.scene_key)
    entry_ast = compiler.program
    for source_id, module in compiler.linked_program.modules.items():
        records.append(_record(program, module.module_identity, "module", source_id, module.ast.module_name,
                               module.ast, writable=True, definition=True))
        for declaration in module.ast.imports:
            records.append(_record(program, module.module_identity + ("imports", declaration.key), "import",
                                   source_id + "::" + declaration.name, declaration.name, declaration,
                                   owner=module.module_identity, writable=True, definition=True))
    records.append(_record(program, scene_ids, "scene", entry_ast.scene.name, entry_ast.scene.name,
                           entry_ast.scene, writable=True, definition=True))
    for ids, symbol in sorted(compiler.definitions.items()):
        budget.tick()
        node = symbol.node
        kind = symbol.kind if symbol.kind in {"class", "function", "module", "import"} else "property"
        record = _record(program, ids, kind, symbol.source_id + "::" + symbol.name, symbol.name,
                         node, definition_id=ids, definition_node=node, writable=True, definition=True)
        record["identity"].update(visibility=symbol.visibility, declaration_kind=symbol.kind)
        records.append(record)
    for path, obj in model.objects.items():
        budget.tick()
        provenance = compiler.occurrence_provenance[path]
        cls = compiler.instances[path].cls
        generated = provenance.get("generated")
        owner_ids = model.objects[obj.owner].element_id if obj.owner else scene_ids
        record = _record(program, obj.element_id, "object", path, obj.name,
                         None if generated is not None else provenance["declaration_node"], owner=owner_ids,
                         definition_id=provenance["definition_id"], definition_node=provenance["definition_node"],
                         writable=obj.owner is None)
        record["identity"].update(class_name=obj.class_name, role=obj.role,
                                  path_steps=[{"kind": step.kind, "value": step.value} for step in provenance["path_steps"]])
        record["source"].update(declaration_span=_span(program, provenance["declaration_node"]),
                                 declaration_definition_id=None if provenance["declaration_definition_id"] is None else list(provenance["declaration_definition_id"]))
        if generated is not None:
            declaring_span = _span(program, provenance["declaration_node"])
            if declaring_span is not None:
                record["source"].update(source_id=declaring_span["source_id"], source_revision=declaring_span["source_revision"])
            record["source"]["generated"] = {
                "collection_id": list(generated["collection_id"]), "input_key": generated["key"],
                "collection_definition_id": list(generated["collection_definition_id"]),
                "input_span": _span(program, generated["input_node"]),
                "input_entry_span": _span(program, generated.get("input_entry_node")),
                "unique_declaration_span": False,
                "repair": "Use an available public parameter initializer in the selected root occurrence."}
        if generated is not None and budget.profile in KEYED_TRANSFORM_PROFILES:
            transforms = model.occurrence_provenance[path].get("generated", {}).get("input_transforms")
            if transforms:
                record["source"]["generated"]["input_transforms"] = budget.data(transforms)
        if generated is not None and budget.profile in KEYED_REDUCTION_PROFILES:
            reductions = model.occurrence_provenance[path].get("generated", {}).get("input_reductions")
            if reductions:
                record["source"]["generated"]["input_reductions"] = budget.data(reductions)
        if generated is not None and budget.profile in KEYED_FILTER_PROFILES:
            filters = model.occurrence_provenance[path].get("generated", {}).get("input_filters")
            if filters:
                record["source"]["generated"]["input_filters"] = budget.data(filters)
        if generated is not None and budget.profile in KEYED_MERGE_PROFILES:
            merges = model.occurrence_provenance[path].get("generated", {}).get("input_merges")
            if merges:
                record["source"]["generated"]["input_merges"] = budget.data(merges)
        if generated is not None and budget.profile in KEYED_ZIP_PROFILES:
            zips = model.occurrence_provenance[path].get("generated", {}).get("input_zips")
            if zips:
                record["source"]["generated"]["input_zips"] = budget.data(zips)
        if generated is not None and budget.profile in KEYED_REKEY_PROFILES:
            rekeys = model.occurrence_provenance[path].get("generated", {}).get("input_rekeys")
            if rekeys:
                record["source"]["generated"]["input_rekeys"] = budget.data(rekeys)
        record["_object_path"] = path
        records.append(record)
        names = list(FIELD_TYPES) + [name for name, member in cls.members.items() if member.node.kind in ("param", "derive")]
        for name in names:
            budget.tick()
            member = cls.members.get(name)
            node = None if member is None else member.node
            ids = tuple(obj.element_id) + (("@system", name) if member is None else (node.key,))
            definition_id = None if member is None else compiler.definition_id(member.declaring, name)
            prop = _record(program, ids, "property", path + "." + name, name, node,
                           owner=obj.element_id, definition_id=definition_id, definition_node=node)
            prop["identity"].update(class_name=obj.class_name, declaration_kind="builtin_field" if member is None else node.kind)
            prop["source"]["initializer_target"] = _target(program, compiler, path, name)
            prop["_object_path"], prop["_value_name"] = path, name
            records.append(prop)
    for path, collection in compiler.collections.items():
        budget.tick()
        node = collection["declaration_node"]
        record = _record(program, collection["element_id"], "collection", path, collection["name"], node,
                         owner=model.objects[collection["owner_path"]].element_id,
                         definition_id=collection["definition_id"], definition_node=node)
        record["identity"].update(ordered_keys=list(collection["ordered_keys"]),
                                  entry_ids={key: list(ids) for key, ids in collection["entry_ids"].items()},
                                  class_name=collection["class_id"], is_object=False)
        record["source"].update(input_span=_span(program, collection["input_node"]), unique_declaration_span=False)
        record["_collection"] = path
        records.append(record)
    for kind, group in (("site", model.sites), ("joint", model.joints), ("follow", model.follows), ("action", model.actions)):
        for path, value in group.items():
            budget.tick()
            owner_path = value.owner if kind == "site" else path.rpartition(".")[0]
            owner = model.objects[owner_path].element_id if owner_path in model.objects else scene_ids
            record = _record(program, value.element_id, kind, path, path.rsplit(".", 1)[-1], value.span,
                             owner=owner, writable=owner_path not in model.objects)
            record["_relation_path"] = path
            records.append(record)
    counts = {}
    for record in records:
        ids = tuple(record["element_id"])
        counts[ids] = counts.get(ids, 0) + 1
    ambiguous = {ids for ids, count in counts.items() if count > 1}
    if ambiguous:
        raise OntoKinError("OKL-E-ID", "Inspection encountered ambiguous bound identities.",
                           phase="binding", details={"identities": [list(x) for x in sorted(ambiguous)]})
    by_id = {tuple(r["element_id"]): r for r in records}
    for record in records:
        owner = record["identity"]["owner"]
        if owner is not None and tuple(owner) in by_id:
            by_id[tuple(owner)]["identity"]["children"].append(record["element_id"])
    if budget.profile in EXECUTION_PROFILES:
        # Agent/0.7 patches exact bytes through immutable source-unit scopes.
        # Definition and generated-instance identities remain inspection data.
        for record in records:
            budget.tick()
            if record["kind"] != "source":
                record["source"]["writable_spans"] = []
    return sorted(records, key=lambda item: tuple(item["element_id"]))


def _index_context(program, budget):
    try:
        compiler = _compile(program, budget)
        return _index(program, compiler, budget), compiler, [diagnostic_dict(d, program) for d in compiler.model.diagnostics], True
    except OntoKinError as exc:
        if exc.diagnostic.category == "resource_limit":
            raise
        # Invalid units still have exact source scopes and revision-bound diagnostics.
        return _file_records(program, budget if budget.profile in EXECUTION_PROFILES else None), None, [diagnostic_dict(exc.diagnostic, program)], False


def source_index(program, *, budgets=None, check=None, profile=CONSTRUCTION_PROFILE):
    return inspect_revision(program, fields=["identity", "source"],
                            limit=(budgets or {}).get("max_result_items", 1000), budgets=budgets, check=check, profile=profile)


def apply_patches(program, patches, *, module_changes=None, budgets=None, check=None, profile=CONSTRUCTION_PROFILE):
    """Form one atomic candidate after checking all original-unit byte scopes."""
    try:
        budget = _request_budget(budgets, check, profile)
        if profile in EXECUTION_PROFILES:
            # Preparing replacement bytes does not execute the old entry or
            # authorize its declaration. The service admits the resulting
            # candidate with this same provisional ledger before validation.
            budget.execution_budget.stage = "edit_preparation"
            records = _file_records(program, budget)
        else:
            records, _, _, _ = _index_context(program, budget)
        by_id = {tuple(record["element_id"]): record for record in records}
        units = {unit.source_id: unit for unit in program.units}
        prepared = {}
        modified = set()
        for patch in patches:
            budget.tick()
            source_id = patch["source_id"]
            unit = units.get(source_id)
            node = None
            def conflict(message, category="conflict"):
                raise OntoKinError("OKL-E-REVISION", message, node, category=category, phase="edit", rule_ids=["CON-013"],
                                  details={"submitted_source_id": source_id, "submitted_source_revision": patch["source_revision"],
                                           "submitted_start_byte": patch["start_byte"], "submitted_end_byte": patch["end_byte"]})
            if unit is None or unit.revision != patch["source_revision"]:
                conflict("The patch does not identify an exact member of the expected program.", "stale")
            start, end = patch["start_byte"], patch["end_byte"]
            if not 0 <= start <= end <= len(unit.raw):
                conflict("Patch byte coordinates are outside the identified source.")
            node = Node("patch", start, end)
            node.source_id = source_id
            try:
                unit.raw[:start].decode("utf-8")
                unit.raw[start:end].decode("utf-8")
                expected = patch["expected_text"].encode("utf-8")
                replacement = patch["replacement"].encode("utf-8")
            except UnicodeError:
                conflict("Patch text or offsets split a UTF-8 character.")
            if unit.raw[start:end] != expected:
                conflict("Patch expected_text differs from the immutable source bytes.", "stale")
            record = by_id.get(tuple(patch["element_id"]))
            if record is None or not any(span["source_id"] == source_id and span["start_byte"] <= start <= end <= span["end_byte"]
                                         for span in record["source"]["writable_spans"]):
                conflict("This identity does not own these writable bytes; use a public occurrence initializer or explicitly target its source definition.")
            prepared.setdefault(source_id, []).append((start, end, replacement))
        payload = program.to_payload()
        descriptors = {"entry": payload["entry"], **{"package:" + x["package_id"] + "@" + x["version"]: x for x in payload["modules"]}}
        for change in module_changes or []:
            budget.tick()
            mode = change["operation"]
            if mode != "add":
                source_id = change["source_id"]
                unit = units.get(source_id)
                if source_id == "entry" or unit is None or unit.revision != change["source_revision"]:
                    raise OntoKinError("OKL-E-REVISION", "A module change requires an exact existing dependency hash.", category="stale", phase="edit")
                if source_id in modified or source_id in prepared:
                    raise OntoKinError("OKL-E-REVISION", "A source cannot be patched and replaced/removed or changed twice in one candidate.", category="conflict", phase="edit")
                modified.add(source_id)
                del descriptors[source_id]
            if mode != "remove":
                descriptor = copy.deepcopy(change["module"])
                new_id = "package:" + descriptor["package_id"] + "@" + descriptor["version"]
                same_replacement = mode == "replace" and new_id == change["source_id"]
                if new_id in descriptors or (new_id in units and not same_replacement) or (new_id in modified and not same_replacement):
                    raise OntoKinError("OKL-E-REVISION", "Module addition/replacement cannot overwrite another source identity.", category="conflict", phase="edit")
                descriptors[new_id] = descriptor
                modified.add(new_id)
        total = sum(len(x["source"].encode("utf-8")) for x in descriptors.values())
        for source_id, ranges in prepared.items():
            ranges.sort(key=lambda x: (x[0], x[1]))
            for left, right in zip(ranges, ranges[1:]):
                if right[0] < left[1] or left[0] == left[1] == right[0] == right[1]:
                    node = Node("patch", right[0], right[1]); node.source_id = source_id
                    raise OntoKinError("OKL-E-REVISION", "Patch ranges overlap or repeat an insertion offset.", node, category="conflict", phase="edit")
            total += sum(len(value) - (end - start) for start, end, value in ranges)
        if total > 2000000:
            raise OntoKinError("OKL-E-RESOURCE", "The complete candidate exceeds the source byte limit.", category="resource_limit", phase="edit")
        for source_id, ranges in prepared.items():
            raw = units[source_id].raw
            parts, offset = [], 0
            for start, end, value in ranges:
                budget.tick()
                parts.extend((raw[offset:start], value)); offset = end
            parts.append(raw[offset:])
            descriptors[source_id]["source"] = b"".join(parts).decode("utf-8")
        try:
            return load_bundle({"schema_version": "ontokin.bundle/0.1", "entry": descriptors.pop("entry"),
                                "modules": list(descriptors.values())})
        except BundleError as exc:
            raise OntoKinError("OKL-E-RESOURCE" if exc.code == "OKA-E-RESOURCE" else "OKL-E-REVISION", str(exc),
                               category="resource_limit" if exc.code == "OKA-E-RESOURCE" else "conflict", phase="edit", details=exc.details) from exc
    except _Interrupt as exc:
        raise exc.error

def _value_record(program, compiler, path, name, budget):
    budget.tick()
    instance = compiler.instances[path]
    member = instance.cls.members.get(name)
    expression = None
    declaring = None
    category, scope = "defaulted", "builtin"
    if name in instance.overrides:
        expression = instance.overrides[name].expression
        category, scope = "authored", "initializer"
    elif name in instance.cls.defaults:
        expression, declaring = instance.cls.defaults[name]
        category = "derived" if member is not None and member.node.kind == "derive" else "inherited" if declaring != instance.cls.name else "defaulted"
        scope = "definition"
    definition_id = None
    if declaring is not None:
        definition_id = compiler.definition_id(declaring, name if member is not None and member.declaring == declaring else None)
    origin = _span(program, expression)
    dependencies = []
    for dependency_path, dependency_name in sorted(compiler.dependencies.get((path, name), set())):
        dependency_id = None
        if dependency_path in compiler.instances:
            other = compiler.instances[dependency_path]
            other_member = other.cls.members.get(dependency_name)
            dependency_id = tuple(other.model.element_id) + (("@system", dependency_name) if other_member is None else (other_member.node.key,))
        dependencies.append({"element_id": None if dependency_id is None else list(dependency_id),
                             "path": dependency_path + ("." + dependency_name if not dependency_name.startswith("@") else ""),
                             "program_revision": program.program_revision, "relationship": "effective_value_dependency"})
    dependencies.extend({"element_id": list(ids), "program_revision": program.program_revision,
                         "relationship": "called_definition"} for ids in sorted(compiler.call_dependencies.get((path, name), set())))
    value = compiler.memo[(path, name)]
    data = budget.data(value)
    result = {**data, "canonical_unit": core._unit(value.type), "display_unit": core._unit(value.type),
            "display_unit_origin": "canonical_presentation", "status": "resolved" if value.known else "unresolved",
            "stale": False, "origin": {"category": category, "scope": scope,
                                        "source_id": None if origin is None else origin["source_id"],
                                        "source_revision": None if origin is None else origin["source_revision"],
                                        "source": origin, "definition_id": None if definition_id is None else list(definition_id)},
            "dependencies": dependencies, "dependency_basis": "observed_pure_elaboration_reads"}
    if budget.profile in KEYED_TRANSFORM_PROFILES:
        transforms = compiler.transform_provenance(value)
        if transforms:
            result["derived_transforms"] = budget.data(transforms)
        if value.known and isinstance(value.value, KeyedValue):
            # These are the actual already evaluated output wrappers. Preserve
            # each selected key/origin without evaluating the map again or
            # granting any new writable identity to a derived leaf.
            for (_, leaf), projected in zip(value.value.entries, result["value"]):
                budget.tick()
                transforms = compiler.transform_provenance(leaf)
                if transforms:
                    projected["value"]["derived_transforms"] = budget.data(transforms)
    if budget.profile in KEYED_REDUCTION_PROFILES:
        reductions = compiler.reduction_provenance(value)
        if reductions:
            result["derived_reductions"] = budget.data(reductions)
        if value.known and isinstance(value.value, KeyedValue):
            for (_, leaf), projected in zip(value.value.entries, result["value"]):
                budget.tick()
                reductions = compiler.reduction_provenance(leaf)
                if reductions:
                    projected["value"]["derived_reductions"] = budget.data(reductions)
    if budget.profile in KEYED_FILTER_PROFILES:
        filters = compiler.filter_provenance(value)
        if filters:
            result["derived_filters"] = budget.data(filters)
        if value.known and isinstance(value.value, KeyedValue):
            for (_, leaf), projected in zip(value.value.entries, result["value"]):
                budget.tick()
                filters = compiler.filter_provenance(leaf)
                if filters:
                    projected["value"]["derived_filters"] = budget.data(filters)
    if budget.profile in KEYED_MERGE_PROFILES:
        merges = compiler.merge_provenance(value)
        if merges:
            result["derived_merges"] = budget.data(merges)
        if value.known and isinstance(value.value, KeyedValue):
            for (_, leaf), projected in zip(value.value.entries, result["value"]):
                budget.tick()
                merges = compiler.merge_provenance(leaf)
                if merges:
                    projected["value"]["derived_merges"] = budget.data(merges)
    if budget.profile in KEYED_ZIP_PROFILES:
        zips = compiler.zip_provenance(value)
        if zips:
            result["derived_zips"] = budget.data(zips)
        if value.known and isinstance(value.value, KeyedValue):
            for (_, leaf), projected in zip(value.value.entries, result["value"]):
                budget.tick()
                zips = compiler.zip_provenance(leaf, aggregate=value)
                if zips:
                    projected["value"]["derived_zips"] = budget.data(zips)
    if budget.profile in KEYED_REKEY_PROFILES:
        rekeys = compiler.rekey_provenance(value)
        if rekeys:
            result["derived_rekeys"] = budget.data(rekeys)
        if value.known and isinstance(value.value, KeyedValue):
            for (_, leaf), projected in zip(value.value.entries, result["value"]):
                budget.tick()
                rekeys = compiler.rekey_provenance(leaf, aggregate=value)
                if rekeys:
                    projected["value"]["derived_rekeys"] = budget.data(rekeys)
    return result


def _project(program, record, fields, compiler, sample, run, frame, budget):
    # Geometry, mass, and mechanical projections are the same normalized model
    # operations as core0.1. Source, values, support, and state context are versioned.
    specialized = {"values", "state", "support"}
    if budget.profile in REACH_PROFILES:
        specialized.add("actions")
    shared = [field for field in fields if field not in specialized]
    result = core._project(program.entry.to_source(), record, shared, compiler, sample, run, frame, budget)
    if "support" in fields:
        result["support"] = core._support_record(compiler, budget)
        result["support"]["profile"] = budget.profile
        result["support"]["named_destination"] = ("ontokin.glb/0.22" if budget.profile == TORQUE_PROFILE else "ontokin.glb/0.21" if budget.profile == KEYED_MEMBERSHIP_PROFILE else "ontokin.glb/0.20" if budget.profile == STRING_CONCAT_PROFILE else "ontokin.glb/0.19" if budget.profile == KEYED_REKEY_PROFILE else "ontokin.glb/0.18" if budget.profile == KEYED_ZIP_PROFILE else "ontokin.glb/0.17" if budget.profile == KEYED_MERGE_PROFILE else "ontokin.glb/0.16" if budget.profile == KEYED_FILTER_PROFILE else "ontokin.glb/0.15" if budget.profile == KEYED_REDUCTION_PROFILE else
                       "ontokin.glb/0.14" if budget.profile == KEYED_TRANSFORM_PROFILE else
                      "ontokin.glb/0.13" if budget.profile == TEXTURE_PROFILE else
                      "ontokin.glb/0.12" if budget.profile == POCKETS_PROFILE else
                      "ontokin.glb/0.11" if budget.profile == FRAMED_LOFT_PROFILE else
                      "ontokin.glb/0.10" if budget.profile == RING_LOFT_PROFILE else
                                                   "ontokin.glb/0.9" if budget.profile == HOLES_PROFILE else
                                                   "ontokin.glb/0.8" if budget.profile == EXTRUSION_PROFILE else
                                                   "ontokin.glb/0.7" if budget.profile == BUDGET_PROFILE else
                                                   PROFILE_BINDINGS[budget.profile].destination)
        if budget.profile not in EXECUTION_PROFILES and not PROFILE_BINDINGS[budget.profile].delivery_available:
            result["support"]["destination_support"] = "unsupported"
            result["support"]["delivery_targets"] = []
    if compiler is None or record["_definition"]:
        for field in fields:
            if field not in result:
                result[field] = {"available": False, "reason": "definition_has_no_occurrence_state" if record["_definition"] else "source_is_unresolved"}
        return result
    path = record.get("_object_path")
    if "source" in fields and record["kind"] == "object" and path is not None and budget.profile == TORQUE_PROFILE:
        from .torque_source import source_intervals
        result["source"]["torque_intervals"] = source_intervals(compiler, path, budget)
    if "actions" in fields and budget.profile in REACH_PROFILES:
        result["actions"] = _reach_actions(compiler, record, path, sample, budget)
    if "geometry" in fields and path is not None and compiler.model.objects[path].geometry["kind"] in ("loft", "extrusion", "placed", "holes", "ring_loft", "framed_loft", "pockets"):
        from .program_surface import surface_summary
        result["geometry"]["representation"] = "native_parameterized_exterior_surface"
        result["geometry"]["surface"] = surface_summary(compiler.model.objects[path].geometry, check=budget.tick)
    if "values" in fields:
        if path is not None:
            names = [record["_value_name"]] if "_value_name" in record else list(FIELD_TYPES) + list(compiler.model.objects[path].properties)
            result["values"] = {name: _value_record(program, compiler, path, name, budget) for name in names}
        elif "_collection" in record:
            collection = compiler.collections[record["_collection"]]
            result["values"] = {"read_only": True, "type": "Keyed<Ref<" + collection["class_id"] + ">>",
                                "entries": [{"key": key, "path": collection["entries"][key],
                                             "element_id": list(collection["entry_ids"][key])} for key in collection["ordered_keys"]]}
        else:
            result["values"] = {"available": False, "reason": "not_an_object_value_record"}
    if "state" in fields:
        if sample is None:
            result["state"] = {"available": False, "reason": "run_required"}
        elif path is None:
            result["state"] = {"available": False, "reason": "collection_has_no_state" if "_collection" in record else "use_relations_or_actions_for_this_record"}
        else:
            state = copy.deepcopy(sample["objects"][path])
            if frame != "world":
                state.update(inspect_in_frame(sample, path, frame, **_reach_work(compiler)))
            state.update(available=True, program_revision=program.program_revision, run_id=run.get("run_id"),
                         time_seconds=sample["time_seconds"], side=sample["side"],
                         valid_interval={"start_seconds": "0", "start_side": "before",
                                         "end_seconds": run["valid_until_seconds"], "end_side": run["valid_until_side"]})
            result["state"] = state
    return budget.data(result)


def _reach_actions(compiler, record, object_path, sample, budget):
    """Project both claimed joints without reusing the one-target renderer."""
    from .reach_projection import reach_projection
    model = compiler.model
    names = [record["path"]] if record["path"] in model.actions else []
    if object_path is not None:
        names = []
        for name, action in model.actions.items():
            budget.tick()
            payload = getattr(action, "reach", None)
            targets = (payload.shoulder, payload.elbow) if payload is not None else (action.target,)
            associated = object_path in targets
            for target in targets:
                if target in model.joints:
                    joint = model.joints[target]
                    associated |= object_path in (model.sites[joint.parent].owner, model.sites[joint.child].owner)
            if associated:
                names.append(name)
    result = []
    for name in names:
        budget.tick()
        if getattr(model.actions[name], "reach", None) is not None:
            result.append(reach_projection(model, name, sample, check=budget.tick))
        else:
            result.append(core._action_record(compiler, name, sample))
    return result


def inspect_revision(program, *, selector=None, fields=None, limit=100, offset=0, run=None,
                     time=None, side="after", frame="world", budgets=None, check=None,
                     profile=CONSTRUCTION_PROFILE):
    diagnostics, achieved = [], None
    try:
        budget = _request_budget(budgets, check, profile)
        selector = {} if selector is None else selector
        source_id = selector.get("source_id")
        base_selector = {k: v for k, v in selector.items() if k != "source_id"}
        base_selector, fields = core._query(base_selector, fields, limit, offset, budget)
        records, compiler, diagnostics, complete = _index_context(program, budget)
        if profile in EXECUTION_PROFILES:
            budget.execution_budget.stage = "inspection"
        achieved = "represented" if compiler is not None else None
        context = {"program_revision": program.program_revision, "run_id": None if run is None else run.get("run_id"),
                   "time_seconds": None, "side": None, "frame": frame, "selector": selector, "fields": fields}
        sample = None
        if not isinstance(frame, str) or side not in ("before", "after"):
            raise OntoKinError("OKL-E-SAMPLE", "Invalid sample frame or side.", phase="inspection", blocks=[])
        if run is None and time is not None:
            raise OntoKinError("OKL-E-SAMPLE", "A current-state time requires a matching program run.", phase="inspection", blocks=[])
        if run is not None:
            end, end_side = _interval(program, run)
            when = end if time is None else exact_time(time)
            which_side = end_side if time is None else side
            if compiler is None or not 0 <= when <= compiler.model.duration or _point(when, which_side) > _point(end, end_side):
                raise OntoKinError("OKL-E-SAMPLE", "This sample is outside the run's available interval.", category="stale", phase="inspection", blocks=[])
            _support(compiler)
            prefix = evaluate_prefix(compiler.model, when, side=which_side, check=budget.tick, **_reach_work(compiler))
            if prefix["failure"] is not None:
                return _error_result(program, None, achieved, prefix["failure"], diagnostics,
                                     items=[], total=0, next_offset=None, truncated=False, index_complete=complete)
            sample = prefix["last_valid_state"]
            if frame not in sample["frames"]:
                raise OntoKinError("OKL-E-SAMPLE", "The requested frame is absent from the evaluated snapshot.", phase="inspection", blocks=[])
            context.update(time_seconds=sample["time_seconds"], side=sample["side"])
        if "class_name" in base_selector and compiler is not None and base_selector["class_name"] not in compiler.classes:
            symbol = compiler.linked_program.resolve_definition("entry", base_selector["class_name"], kind="class")
            base_selector["class_name"] = "/".join(symbol.element_id)
        relation_paths = None
        if "relation" in selector and compiler is not None:
            model = compiler.model
            for group in (model.joints, model.follows):
                for relation in group.values():
                    budget.tick()
                    if relation.path == selector["relation"] or list(relation.element_id) == selector["relation"]:
                        relation_paths = {relation.path}
                        if relation.path in model.joints:
                            relation_paths.update((relation.parent, relation.child, model.sites[relation.parent].owner, model.sites[relation.child].owner))
                        else:
                            relation_paths.update((relation.child, model.frame_owner(relation.parent)))
        selected = []
        for record in records:
            budget.tick()
            if source_id is not None and record["source"].get("source_id") != source_id:
                continue
            if core._selected(record, base_selector, compiler, relation_paths):
                selected.append(record)
        items = [_project(program, record, fields, compiler, sample, run, frame, budget) for record in selected[offset:offset + limit]]
        next_offset = offset + len(items) if offset + len(items) < len(selected) else None
        payload = {"items": items, "total": len(selected), "offset": offset, "next_offset": next_offset,
                   "truncated": next_offset is not None, "index_complete": complete, "context": context}
        if "source" in fields:
            requested_ids = set()
            for item in items:
                source = item["source"]
                if source.get("source_id"):
                    requested_ids.add(source["source_id"])
                if source.get("definition_span"):
                    requested_ids.add(source["definition_span"]["source_id"])
                if source.get("initializer_target", {}).get("span"):
                    requested_ids.add(source["initializer_target"]["span"]["source_id"])
            payload["source_units"] = [{"source_id": unit.source_id, "source_revision": unit.revision,
                                        "filename": unit.filename, "source": unit.text}
                                       for unit in program.units if unit.source_id in requested_ids]
        result = _result(program, None, achieved, diagnostics, **payload)
        return budget.json(result)
    except _Interrupt as exc:
        raise exc.error
    except OntoKinError as exc:
        return _error_result(program, None, achieved, exc, diagnostics, items=[], total=0, next_offset=None, truncated=False)
