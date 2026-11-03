"""Finite .22 Cartesian couples on the existing staged reach evaluator.

Canonical rotation, translation and the independent torque error origin have
separate records. A torque-only boundary never writes the translation anchor.
"""
from __future__ import annotations

import copy
import math
from contextlib import contextmanager
from dataclasses import dataclass, field, fields, replace
from fractions import Fraction as F
from itertools import chain, repeat
from operator import attrgetter, is_
from types import MethodType

from .diagnostics import OntoKinError
from .evaluator import MAX_OUTPUT_RECORDS, ZERO, time_text
from .execution_budget import SharedExecutionBudget
from .force_runtime import ForceSimulator, _ForceState
from .json_limits import JSONLimitError, MAX_JSON_BYTES, measure_json
from .model import Event, EventBlock, ObjectModel, SceneModel, TorquePayload
from .reach_numeric import (MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork, compare,
                            exact, require_execution_work, round_binary64)
from .reach_phase import AnchorError, PhaseArithmetic
from .reach_pose import (AXIS_ERROR, EXPOSED_ROTATION_ERROR, PRODUCT_ERROR,
                         RotationValue)
from .reach_runtime import ReachSimulator, RecordingPose, _ReachRunState
from .torque_canonical_spin import (advance_orientation as _canonical_advance_orientation,
    admit_simulator as _admit_canonical_dispatch, bind_simulator_type as _bind_canonical_dispatch,
    admit_simulator_after_entry as _canonical_after_entry,
    _POINT_AUTHORITY as _canonical_point_authority)


PROFILE = "torque-0.1"
PHASE_LIMIT = F(1 << 20)
AXES = {"world_x": (1.0, 0.0, 0.0), "world_y": (0.0, 1.0, 0.0),
        "world_z": (0.0, 0.0, 1.0)}
AXIS_INDEX = {name: index for index, name in enumerate(AXES)}
_LOCATION_KEYS = ("source_id", "source_revision", "start_byte", "end_byte")
_F_NUMERATOR = attrgetter("_numerator")
_F_DENOMINATOR = attrgetter("_denominator")
_NATIVE_LEDGER_TICK = SharedExecutionBudget.tick


def _native_work_callback(work, ledger):
    callback, current = work.external_check, ledger.tick
    return (type(callback) is MethodType and callback.__self__ is ledger
            and callback.__func__ is _NATIVE_LEDGER_TICK
            and type(current) is MethodType and current.__self__ is ledger
            and current.__func__ is _NATIVE_LEDGER_TICK)


def _location(value):
    if (type(value) is not dict or len(value) != len(_LOCATION_KEYS)
            or any(type(key) is not str for key in value) or set(value) != set(_LOCATION_KEYS)
            or type(value["source_id"]) is not str
            or type(value["source_revision"]) is not str
            or len(value["source_id"]) > 4096
            or len(value["source_revision"]) != 71
            or not value["source_revision"].startswith("sha256:")
            or type(value["start_byte"]) is not int
            or type(value["end_byte"]) is not int
            or not 0 <= value["start_byte"] <= value["end_byte"] <= 2_000_000):
        raise ValueError("A torque needs an original bounded source location.")
    return tuple((key, value[key]) for key in _LOCATION_KEYS)


@dataclass(frozen=True)
class _ActiveTorque:
    target: str
    key: str
    axis: str
    torque_n_m: float
    duration: F
    sequence_index: int
    source: tuple
    operand_source: tuple
    duration_source: tuple
    activation: F
    completion: F
    span: object


@dataclass(frozen=True)
class TorqueRotationAnchor:
    time: F
    rotation: RotationValue
    speed: float
    acceleration: float


@dataclass(frozen=True)
class TorqueReferenceOrigin:
    time: F
    speed: F
    acceleration: F
    angle_error: F
    speed_error: F


@dataclass
class TorqueState:
    active: dict = field(default_factory=dict)
    axis: str | None = None
    net: float = 0.0
    acceleration: float | None = None
    rotation: TorqueRotationAnchor | None = None
    reference: TorqueReferenceOrigin | None = None
    started_count: int = 0
    completed_count: int = 0
    last_time: F | None = None
    last_changes: tuple = ()
    # Ordered impulses need an immediately visible tentative speed, but the
    # complete boundary publishes one final canonical rotation anchor.
    pending_rotation: TorqueRotationAnchor | None = None


@dataclass
class TorqueRunState(_ReachRunState):
    torques: dict = field(default_factory=dict)


def _source_snapshot(model, event):
    """Callback-free native admission, before inspecting or allocating operands."""
    if type(event) is not Event or type(event.torque) is not TorquePayload:
        raise ValueError("A torque needs its original native event and payload.")
    p = event.torque
    if (type(event.kind) is not str or type(event.target) is not str or event.target not in model.objects
            or event.kind != "torque"
            or type(p.key) is not str or not 1 <= len(p.key) <= 64
            or type(p.axis) is not str or p.axis not in AXES
            or type(p.torque_n_m) is not float or not math.isfinite(p.torque_n_m)
            or type(p.duration) is not F
            or type(p.duration.numerator) is not int or type(p.duration.denominator) is not int
            or p.duration.denominator <= 0
            or max(p.duration.numerator.bit_length(), p.duration.denominator.bit_length()) > MAX_OPERAND_BITS
            or p.duration <= 0
            or type(p.sequence_index) is not int or not 0 <= p.sequence_index < MAX_OUTPUT_RECORDS):
        raise ValueError("A torque source event has an invalid native shape.")
    return (event.target, p.key, p.axis, p.torque_n_m, p.duration,
            p.sequence_index, _location(p.source), _location(p.operand_source),
            _location(p.duration_source), event.span)


def _active(model, event, activation, *, work, snapshot=None):
    source = _source_snapshot(model, event) if snapshot is None else snapshot
    if type(activation) is not F:
        raise ValueError("A torque activation needs its native exact clock.")
    if (type(work) is not ReachExecutionWork
            or type(work.execution_budget) is not SharedExecutionBudget
            or work.execution_budget.resolved is None
            or not _native_work_callback(work, work.execution_budget)):
        raise OntoKinError("OKL-E-RESOURCE", "Torque clocks require the original admitted work.",
            category="resource_limit", phase="support",
            details={"budget_reason": "execution_context_required"})
    work.guard(activation, source[4])
    # Source Fraction instances are native but can still be attacked through
    # their private integer slots. Run history owns detached exact clocks.
    activation = F(activation.numerator, activation.denominator)
    duration = F(source[4].numerator, source[4].denominator)
    source = (*source[:4], duration, *source[5:])
    end = exact(activation, source[4], "add", work)
    return _ActiveTorque(*source[:9], activation, end, source[9])


def _record(model, value):
    return {"torque_key": value.key,
        "torque_element_id": [model.module_key, model.scene_key, "torque", value.key],
        "target_path": value.target,
        "target_element_id": list(model.objects[value.target].element_id),
        "program_revision": model.program_revision,
        "source_location": dict(value.source), "sequence_index": value.sequence_index,
        "activation_time_seconds": time_text(value.activation),
        "duration_seconds": time_text(value.duration),
        "completion_time_seconds": time_text(value.completion),
        "axis": value.axis, "torque_n_m": value.torque_n_m,
        "operand_location": dict(value.operand_source),
        "duration_location": dict(value.duration_source)}


def torque_source_record(model, event, activation, *, work):
    """Closed immutable-source projection; the caller owns source accounting."""
    return _record(model, _active(model, event, activation, work=work))


def _native_source_receipt(model):
    """Callback-free bounded identities and values for the actual source law.

    Owners are strongly retained separately from immutable scalar tokens;
    equal replacement containers cannot impersonate the admitted source.
    Geometry is validated by the independent delivery reader. This receipt
    covers every source operand that can change the runtime trajectory.
    """
    from .model import (ActionModel, FollowModel, ForcePayload, ImpulsePayload,
                        JointModel, Pose, ReachPayload, ReachSourceLocation, SiteModel)
    from .syntax import Node
    owners = [model]
    count = 0
    records = (Pose, ReachPayload, ReachSourceLocation, ImpulsePayload, ForcePayload, TorquePayload)
    def value(item, depth=0):
        nonlocal count
        count += 1
        if count > MAX_OUTPUT_RECORDS * 64 or depth > 8:
            raise ValueError("A torque source receipt exceeds its bounded shape.")
        kind = type(item)
        if item is None:
            return None
        if kind is str and len(item) <= 4096:
            return ("str", item)
        if kind is int and item.bit_length() <= MAX_OPERAND_BITS:
            return ("int", item)
        if kind is float and math.isfinite(item):
            return ("float", item.hex())
        if kind is F and max(item.numerator.bit_length(), item.denominator.bit_length()) <= MAX_OPERAND_BITS:
            owners.append(item)
            return ("fraction", item.numerator, item.denominator)
        if kind in (tuple, list, dict) and len(item) <= MAX_OUTPUT_RECORDS:
            if kind is not tuple:
                owners.append(item)
            if kind is dict:
                return ("dict", tuple((value(k, depth + 1), value(v, depth + 1)) for k, v in item.items()))
            return (kind.__name__, tuple(value(v, depth + 1) for v in item))
        if kind is Node:
            owners.append(item)
            return ("span", value((item.kind, item.source_id, item.start, item.end), depth + 1))
        if kind in records:
            owners.append(item)
            return (kind.__name__, tuple(value(getattr(item, f.name), depth + 1) for f in fields(kind)))
        raise ValueError("A torque source receipt requires native finite operands.")
    if type(model) is not SceneModel:
        raise ValueError("A torque source receipt requires a native model.")
    header = value((model.profile, model.program_revision, model.module_key,
                    model.scene_key, model.duration, model.gravity))
    tables = (
        ("objects", ObjectModel, ("path", "element_id", "owner", "placement", "velocity", "omega", "motion", "physical", "span")),
        ("sites", SiteModel, ("path", "element_id", "owner", "pose", "interface", "size", "span")),
        ("joints", JointModel, ("path", "element_id", "kind", "parent", "child", "axis", "limits", "initial", "span")),
        ("follows", FollowModel, ("path", "element_id", "parent", "child", "offset", "span")),
        ("actions", ActionModel, ("path", "element_id", "kind", "target", "duration", "vector", "goal", "reach", "span")))
    contents = []
    for name, native, names in tables:
        table = getattr(model, name)
        if type(table) is not dict or len(table) > MAX_OUTPUT_RECORDS:
            raise ValueError("A torque source receipt requires bounded native tables.")
        owners.append(table)
        rows = []
        for key, item in table.items():
            if type(key) is not str or type(item) is not native:
                raise ValueError("A torque source receipt requires native records.")
            owners.append(item)
            rows.append((value(key), tuple(value(getattr(item, name)) for name in names)))
        contents.append(tuple(rows))
    if type(model.events) is not list or len(model.events) > MAX_OUTPUT_RECORDS:
        raise ValueError("A torque source receipt requires native event order.")
    owners.append(model.events)
    blocks, event_count = [], 0
    for block in model.events:
        if type(block) is not EventBlock or type(block.events) is not list:
            raise ValueError("A torque source receipt requires native event blocks.")
        event_count += len(block.events)
        if event_count > MAX_OUTPUT_RECORDS:
            raise ValueError("A torque source receipt exceeds its source-event bound.")
        owners.extend((block, block.events))
        events = []
        for event in block.events:
            if type(event) is not Event:
                raise ValueError("A torque source receipt requires native events.")
            owners.append(event)
            events.append(tuple(value(getattr(event, f.name)) for f in fields(Event)))
        blocks.append((value(block.time), value(block.span), tuple(events)))
    return tuple(owners), (header, tuple(contents), tuple(blocks))


def _source_watches(receipt):
    """Retain native leaves for callback checks without rebuilding operands.

    Identity comparisons never invoke a newly supplied object's equality or
    numeric conversion. Retained original keys/values prevent id recycling.
    """
    seen, owners, instances, dictionaries, sequences, fractions = set(), [], [], [], [], []
    for owner in receipt[0]:
        if id(owner) in seen:
            continue
        seen.add(id(owner))
        owners.append(owner)
        kind = type(owner)
        if kind is F:
            fractions.append(owner)
            continue
        namespace = owner if kind in (dict, list) else vars(owner)
        if kind not in (dict, list):
            instances.append(owner)
        if type(namespace) is dict:
            dictionaries.append(namespace)
        elif type(namespace) is list:
            sequences.append(namespace)
        else:
            raise ValueError("A torque receipt requires native attribute storage.")
    owners, instances = tuple(owners), tuple(instances)
    dictionaries, sequences, fractions = tuple(dictionaries), tuple(sequences), tuple(fractions)
    key_views = tuple(map(dict.keys, dictionaries))
    value_views = tuple(map(dict.values, dictionaries))
    keys = tuple(chain.from_iterable(key_views))
    values = tuple(chain.from_iterable(value_views))
    members = tuple(chain.from_iterable(sequences))
    numerators = tuple(map(_F_NUMERATOR, fractions))
    denominators = tuple(map(_F_DENOMINATOR, fractions))
    # Native C iterators avoid a separate Python comparison loop and multiple
    # temporary tuples for every source dictionary on each original callback.
    # Keep every old key/value/member alive so an identity can never be reused.
    # Native views remain attached to these exact dictionary owners and expose
    # every later mutation; retaining them avoids rebuilding views per tick.
    return ((owners, instances, dictionaries, sequences, fractions, key_views, value_views),
            (keys, values, members, numerators, denominators),
            (tuple(map(type, owners)), tuple(map(vars, instances)),
             tuple(map(len, dictionaries)), tuple(map(len, sequences))))


def _source_watches_current(watches):
    (owners, instances, dictionaries, sequences, fractions, key_views, value_views), retained, signature = watches
    # Check all exact native types before vars/attribute access. The remaining
    # operations only inspect admitted native containers and compare identities;
    # a replacement value's equality or other foreign method is never called.
    return (all(map(is_, map(type, owners), signature[0]))
        and all(map(is_, map(vars, instances), signature[1]))
        and tuple(map(len, dictionaries)) == signature[2]
        and all(map(is_, chain.from_iterable(key_views), retained[0]))
        and all(map(is_, chain.from_iterable(value_views), retained[1]))
        and tuple(map(len, sequences)) == signature[3]
        and all(map(is_, chain.from_iterable(sequences), retained[2]))
        and all(map(is_, map(_F_NUMERATOR, fractions), retained[3]))
        and all(map(is_, map(_F_DENOMINATOR, fractions), retained[4])))


def _preflight_work(work, check):
    if work is None and type(check) is MethodType:
        owner, function = check.__self__, check.__func__
        if type(owner) is ReachExecutionWork and function is ReachExecutionWork.tick:
            work = owner
        elif isinstance(owner, TorqueSimulator) and function is TorqueSimulator._work_check:
            work = owner.work
    # Native admission itself must not call require_execution_work: that
    # inherited helper invokes the original zero-charge checkpoint.
    ledger = work.execution_budget if type(work) is ReachExecutionWork else None
    if (type(work) is not ReachExecutionWork or type(ledger) is not SharedExecutionBudget
            or ledger.resolved is None or not _native_work_callback(work, ledger)):
        raise OntoKinError("OKL-E-RESOURCE", "Torque preflight requires its original shared execution context.",
            category="resource_limit", phase="support", details={
                "budget_reason": "execution_context_required", "target_contract": "ontokin.glb/0.22"})
    return work


def admit_torque_request_source(model, *, work=None, check=None):
    """Admit the complete source before an output-budget callback can run.

    Public evaluator preflights precede simulator construction. Their source
    therefore needs its own bounded receipt before the first callback, rather
    than allowing a later simulator to adopt callback-mutated operands.
    """
    work = _preflight_work(work, check)
    ledger = work.execution_budget
    previous = ledger._torque_context_guard
    if previous is not None:
        previous()
    watches = _source_watches(_native_source_receipt(model))
    original = (ledger.check, ledger._clock, ledger.started, ledger.resolved,
                work.started, work.max_operand_bits, work.max_cache_entries,
                work.max_operations, work.max_elapsed_ms)
    def guard():
        if (type(work) is not ReachExecutionWork or type(ledger) is not SharedExecutionBudget
                or work.execution_budget is not ledger or not _native_work_callback(work, ledger)
                or ledger._torque_context_guard is not guard
                or ledger.check is not original[0] or ledger._clock is not original[1]
                or ledger.started is not original[2] or ledger.resolved is not original[3]
                or any(actual is not expected for actual, expected in zip(
                    (work.started, work.max_operand_bits, work.max_cache_entries,
                     work.max_operations, work.max_elapsed_ms), original[4:]))
                or not _source_watches_current(watches)):
            raise OntoKinError("OKL-E-RESOURCE", "Torque preflight source or context changed after native admission.",
                category="resource_limit", phase="evaluation",
                details={"budget_reason": "execution_context_required"})
    ledger._torque_context_guard = guard
    guard()
    return work, previous, guard


@contextmanager
def torque_source_preflight(model, *, work=None, check=None):
    work, previous, guard = admit_torque_request_source(model, work=work, check=check)
    ledger = work.execution_budget
    completed = False
    try:
        yield work
        guard()
        completed = True
    finally:
        ledger._torque_context_guard = previous
        if completed and previous is not None:
            previous()


def torque_record_bound(model, *, constructing=False, horizon=None,
                        side="after", check=None, work=None):
    """Preflight complete headers and source histories at exact prefix clocks."""
    base = 36 * len(model.objects)
    if constructing:
        return base
    with torque_source_preflight(model, work=work, check=check) as original_work:
        # Preserve the original checkpoint, now protected by the source
        # captured before it rather than by operands captured after it.
        require_execution_work(original_work, target_contract="ontokin.glb/0.22")
        return _torque_record_bound(model, base, horizon=horizon, side=side, check=check, work=original_work)


def _torque_record_bound(model, base, *, horizon, side, check, work):
    horizon = model.duration if horizon is None else horizon
    boundaries = {}
    for block in sorted(model.events, key=lambda item: item.time):
        if check is not None:
            check()
        if block.time > horizon or block.time == horizon and side == "before":
            break
        for event in block.events:
            if check is not None:
                check()
            if event.kind != "torque":
                continue
            value = _active(model, event, block.time, work=work)
            weight = measure_json(_record(model, value), check=check)["entries"]
            boundaries.setdefault(block.time, []).append(("started", value, weight))
            if value.completion < horizon or value.completion == horizon and side == "after":
                boundaries.setdefault(value.completion, []).append(("completed", value, weight))
    active, latest = {}, {}
    total_active = total_latest = maximum = 0
    for _, entries in sorted(boundaries.items()):
        changes = {}
        for kind, value, weight in entries:
            if check is not None:
                check()
            identity = (value.target, value.key)
            if kind == "completed":
                total_active -= active.pop(identity)
            else:
                active[identity] = weight
                total_active += weight
            changes[value.target] = changes.get(value.target, 0) + weight + 1
        for path, weight in changes.items():
            total_latest += weight - latest.get(path, 0)
            latest[path] = weight
        maximum = max(maximum, total_active + total_latest)
    return base + maximum


class TorqueSimulator(ReachSimulator):
    """One admitted request, exact torque intervals and atomic boundaries."""

    def __init__(self, model, check=None, *, work=None):
        # This request-private entry receipt runs before mutable public guard
        # functions. Its code and closure cells are trusted owner metadata,
        # like the existing source-preflight receipt; this is not a sandbox
        # against arbitrary inspection or replacement of interpreter state.
        (entry, original_admit, original_context, native_all, native_any, native_map,
         native_is, native_flatten, native_repeat, native_len, native_getattribute,
         native_get, native_items, native_contains, error_type) = _CANONICAL_GUARD_BOOTSTRAP
        context_ready = False

        def guard():
            # Captured native is_ compares object identity without invoking
            # value equality. The full records remain strongly owned in
            # entry[0]; every callback performs the checks again.
            actual = native_flatten(native_map(entry[1], entry[2]))
            if not native_all(native_map(native_is, actual, entry[3])):
                raise error_type("OKL-E-RESOURCE", "Torque point guard dispatch changed after admission.",
                    category="resource_limit", phase="evaluation",
                    details={"budget_reason": "execution_context_required"})
            for mapping, expected in entry[4]:
                if (native_len(mapping) * 2 != native_len(expected)
                        or not native_all(native_map(native_is,
                            native_flatten(native_items(mapping)), expected))):
                    raise error_type("OKL-E-RESOURCE", "Torque point guard defaults changed after admission.",
                        category="resource_limit", phase="evaluation",
                        details={"budget_reason": "execution_context_required"})
            actual = native_map(native_get, entry[5], entry[6], native_repeat(entry[10]))
            if (not native_all(native_map(native_is, actual, entry[7]))
                    or native_any(native_map(native_contains, entry[8], entry[9]))):
                raise error_type("OKL-E-RESOURCE", "Torque point guard bindings changed after admission.",
                    category="resource_limit", phase="evaluation",
                    details={"budget_reason": "execution_context_required"})
            original_admit(self)
            if context_ready:
                namespace = native_getattribute(self, "__dict__")
                original_context(self, initial=not namespace["_torque_constructed"])

        guard()
        if (type(model) is not SceneModel or type(model.events) is not list
                or type(model.objects) is not dict
                or type(work) is not ReachExecutionWork
                or type(work.execution_budget) is not SharedExecutionBudget):
            raise OntoKinError("OKL-E-RESOURCE", "Torque execution requires native source and its original context.",
                category="resource_limit", phase="support",
                details={"budget_reason": "execution_context_required", "target_contract": "ontokin.glb/0.22"})
        ledger = work.execution_budget
        self._torque_context_receipt = (ledger.check, ledger._clock, ledger.started,
            ledger.resolved, ledger._limits.copy(), work.started, work.max_operand_bits,
            work.max_cache_entries, work.max_operations, work.max_elapsed_ms)
        self._torque_limits_owner = ledger._limits
        self._torque_source_receipt = _native_source_receipt(model)
        self._torque_source_watches = _source_watches(self._torque_source_receipt)
        self._torque_sources = {}
        self._torque_objects_owner = model.objects
        self._torque_bodies = {}
        for path, obj in model.objects.items():
            if type(path) is not str or type(obj) is not ObjectModel or type(obj.physical) is not dict:
                raise ValueError("A torque request needs its original native body records.")
            self._torque_bodies[path] = (obj, obj.physical, obj.physical.get("kind"),
                                         obj.mass, obj.radius, obj.inertia)
        count = 0
        for block in model.events:
            if type(block) is not EventBlock or type(block.events) is not list or type(block.time) is not F:
                raise ValueError("A torque request needs original native event blocks.")
            for event in block.events:
                count += 1
                if count > MAX_OUTPUT_RECORDS or type(event) is not Event:
                    raise ValueError("A torque request needs bounded native source events.")
                if event.kind == "torque":
                    self._torque_sources[id(event)] = (event, event.torque, block, block.time,
                                                       _source_snapshot(model, event))
        require_execution_work(work, target_contract="ontokin.glb/0.22")
        # The original zero-charge checkpoint above can invoke the original
        # callback before this simulator becomes the ledger's context owner.
        guard()
        if model.profile != PROFILE:
            raise ValueError("The torque simulator requires its explicit source profile.")
        self._torque_ledger = work.execution_budget
        self._torque_work = work
        self._torque_model = model
        self._torque_revision = model.program_revision
        self._requested_time = F(0)
        self._requested_side = "before"
        self._torque_constructed = False
        previous_guard = ledger._torque_context_guard
        if previous_guard is not None:
            previous_guard()
        context_ready = True
        self._torque_guard_hook = guard
        ledger._torque_context_guard = self._torque_guard_hook
        self._context(initial=True)
        super().__init__(model, check=check, work=work)
        self.state = TorqueRunState(**vars(self.state))
        self.state.torques = {path: TorqueState() for path in model.objects}
        self._torque_state_owner = self.state
        self._torque_history_owner = self.state.torques
        self._torque_event_order = (self.events, tuple(self.events))
        self._torque_constructed = True

    def _guard_context(self):
        _admit_canonical_dispatch(self)
        self._context(initial=not self._torque_constructed)

    def _advance_orientation(self, initial, omega, elapsed, *,
                             recording_context=None, recording_path=None,
                             recording_pose_ops=None):
        """Select the first certifying plan for this exact source operation.

        A registered whole-phase plan proves coverage, but its horizon must
        not choose this point's canonical operands. The unchanged source
        kernel selects from the actual elapsed time when no plan is supplied.
        Recording uses that same complete source operation, without a cursor.
        """
        self._context()
        if recording_pose_ops is not None and (recording_context is None
                or getattr(recording_pose_ops, "source_ops", None) is not self.pose_ops
                or recording_pose_ops.work is not self.work):
            raise ValueError("Alternate spin recording requires this source's recording-only work context.")
        result = _canonical_advance_orientation(self, initial, omega, elapsed)
        self._context()
        return result

    def _context(self, *, initial=False):
        _admit_canonical_dispatch(self)
        return self._context_after_dispatch(initial=initial)

    def _context_after_dispatch(self, *, initial=False):
        """The native context body after callback-free dispatch admission."""
        ledger = self._torque_ledger
        work = self._torque_work
        receipt = self._torque_context_receipt
        if ((not initial and (self.model is not self._torque_model or self.work is not work))
                or self._torque_model.program_revision is not self._torque_revision
                or self._torque_model.objects is not self._torque_objects_owner
                or type(work) is not ReachExecutionWork
                or type(ledger) is not SharedExecutionBudget
                or work.execution_budget is not ledger
                or not _native_work_callback(work, ledger) or ledger.resolved is None
                or ledger.check is not receipt[0] or ledger._clock is not receipt[1]
                or ledger.started is not receipt[2] or ledger.resolved is not receipt[3]
                or ledger._limits is not self._torque_limits_owner
                or len(ledger._limits) != len(receipt[4])
                or any(key is not old_key or value is not old_value
                       for (key, value), (old_key, old_value) in zip(ledger._limits.items(), receipt[4].items()))
                or not ledger._torque_guarded
                or ledger._torque_context_guard is not self._torque_guard_hook
                or any(actual is not expected for actual, expected in zip(
                    (work.started, work.max_operand_bits, work.max_cache_entries,
                     work.max_operations, work.max_elapsed_ms), receipt[5:]))
                or (hasattr(self, "_torque_state_owner") and
                    (self.state is not self._torque_state_owner or
                     self.state.torques is not self._torque_history_owner))):
            raise OntoKinError("OKL-E-RESOURCE", "Torque execution requires its original admitted context.",
                category="resource_limit", phase="support", details={
                    "budget_reason": "execution_context_required", "target_contract": "ontokin.glb/0.22"})
        if (not _source_watches_current(self._torque_source_watches)
                or (self._torque_constructed and (
                    self.events is not self._torque_event_order[0]
                    or type(self.events) is not list
                    or len(self.events) != len(self._torque_event_order[1])
                    or any(a is not b for a, b in zip(self.events, self._torque_event_order[1]))))):
            raise OntoKinError("OKL-E-RESOURCE", "Torque source operands changed after native admission.",
                category="resource_limit", phase="evaluation",
                details={"budget_reason": "execution_context_required"})

    def _source_event(self, event, time):
        saved = self._torque_sources.get(id(event))
        if (saved is None or saved[0] is not event or saved[1] is not event.torque
                or saved[2].time != saved[3] or saved[3] != time
                or _source_snapshot(self.model, event) != saved[4]):
            raise OntoKinError("OKL-E-RESOURCE", "A torque source changed after native admission.",
                category="resource_limit", phase="evaluation",
                details={"budget_reason": "execution_context_required"})
        return saved[4]

    def _body(self, path):
        saved = self._torque_bodies[path]
        obj = self.model.objects.get(path)
        if (obj is not saved[0] or obj.physical is not saved[1]
                or (obj.physical.get("kind"), obj.mass, obj.radius, obj.inertia) != saved[2:]):
            raise OntoKinError("OKL-E-RESOURCE", "A torque body's own physical operands changed.",
                category="resource_limit", phase="evaluation",
                details={"budget_reason": "execution_context_required"})
        return saved[2:]

    def recording_path_snapshot(self, state):
        """Detach the finite native graph before any recording-path callback.

        The snapshot reads only topology, claims, and persistent axis latches;
        it does not clone a constructor, pose graph, numerical cache, or history.
        Its owner tuple keeps every compared object alive. Re-admission below
        repeats this callback-free native read once before publication.
        """
        from .model import ActionModel, FollowModel, JointModel, Pose, SiteModel
        from .syntax import Node
        self._context()
        if type(state) is not TorqueRunState:
            raise ReachAdmissionError("reach_domain", "Torque paths require native source state.")
        model = self.model
        names = ("objects", "sites", "joints", "follows", "actions")
        tables = tuple(getattr(model, name) for name in names)
        runtime = (state.torques, state.claims, state.modes)
        if (any(type(table) is not dict for table in tables + runtime)
                or sum(len(table) for table in tables + runtime) > MAX_OUTPUT_RECORDS
                or type(state.active_grips) is not set
                or len(state.active_grips) > MAX_OUTPUT_RECORDS):
            raise ReachAdmissionError("reach_domain", "Torque paths require bounded native source tables.")
        owners = [model, state, *tables, *runtime, state.active_grips]
        token, data = [], {}
        def scalar(value, depth=0):
            kind = type(value)
            if depth > 4:
                raise ReachAdmissionError("reach_domain", "A torque path source operand is too deep.")
            if value is None:
                return None
            if kind is str and len(value) <= 4096:
                return value
            if kind is float and math.isfinite(value):
                return ("float", value.hex())
            if kind is int and value.bit_length() <= MAX_OPERAND_BITS:
                return ("int", value)
            if kind is F and max(value.numerator.bit_length(), value.denominator.bit_length()) <= MAX_OPERAND_BITS:
                return ("fraction", value.numerator, value.denominator)
            if kind is tuple and len(value) <= 32:
                return tuple(scalar(item, depth + 1) for item in value)
            raise ReachAdmissionError("reach_domain", "A torque path source operand is not native and bounded.")
        def span(value):
            if value is None:
                return None, None
            if type(value) is not Node:
                raise ReachAdmissionError("reach_domain", "A torque path requires its original source span.")
            owners.append(value)
            location = (value.source_id, value.start, value.end)
            signature = scalar(location)
            return signature, Node("span", value.start, value.end, source_id=value.source_id)
        def pose(value):
            if type(value) is not Pose:
                raise ReachAdmissionError("reach_domain", "A torque path requires a native fixed pose.")
            owners.append(value)
            return scalar((value.frame, value.position, value.rotation))
        expected = (ObjectModel, SiteModel, JointModel, FollowModel, ActionModel)
        for name, table, native in zip(names, tables, expected):
            copied, rows = {}, []
            for path, item in table.items():
                if type(path) is not str or type(item) is not native:
                    raise ReachAdmissionError("reach_domain", "A torque path requires native typed source rows.")
                owners.append(item)
                location, saved_span = span(item.span)
                if name == "objects":
                    self._body(path)
                    row = scalar((item.path, item.owner, item.motion, item.mass))
                    copied[path] = None
                elif name == "sites":
                    row = (scalar(item.owner), pose(item.pose))
                    copied[path] = item.owner
                elif name == "joints":
                    row = scalar((item.kind, item.parent, item.child, item.axis, item.initial, item.limits))
                    copied[path] = (item.kind, item.parent, item.child, saved_span)
                elif name == "follows":
                    row = (scalar((item.parent, item.child)), pose(item.offset))
                    copied[path] = (item.parent, item.child)
                else:
                    row = scalar((item.kind, item.target, item.duration, item.vector, item.goal))
                    copied[path] = saved_span
                rows.append((scalar(path), row, location))
            token.append((name, tuple(rows)))
            data[name] = copied
        axes = {}
        for path, history in state.torques.items():
            if type(path) is not str or type(history) is not TorqueState or path not in data["objects"]:
                raise ReachAdmissionError("reach_domain", "A torque path needs its native latch records.")
            if history.axis is not None and (type(history.axis) is not str or history.axis not in AXES):
                raise ReachAdmissionError("reach_domain", "A torque path latch has an invalid axis.")
            owners.append(history)
            axes[path] = history.axis
        if set(axes) != set(data["objects"]):
            raise ReachAdmissionError("reach_domain", "A torque path latch table is incomplete.")
        claims = []
        for channel, action in state.claims.items():
            if (type(channel) is not tuple or len(channel) != 2
                    or any(type(part) is not str for part in channel)
                    or type(action) is not str or action not in data["actions"]):
                raise ReachAdmissionError("reach_domain", "A torque path needs native current claims.")
            claims.append((channel, action))
        if any(type(path) is not str or path not in data["joints"] for path in state.active_grips):
            raise ReachAdmissionError("reach_domain", "A torque path grip set is not native.")
        grips = frozenset(state.active_grips)
        modes = tuple((scalar(path), scalar(mode)) for path, mode in state.modes.items())
        token.extend((("torques", tuple(axes.items())), ("claims", tuple(claims)),
                      ("grips", tuple(sorted(grips))), ("modes", modes)))
        data.update(axes=axes, claims=tuple(claims), grips=grips)
        return tuple(owners), tuple(token), data

    def admit_recording_paths(self, state, saved):
        current = self.recording_path_snapshot(state)
        if (len(current[0]) != len(saved[0])
                or any(left is not right for left, right in zip(current[0], saved[0]))
                or current[1] != saved[1]):
            raise ReachAdmissionError("reach_domain", "Torque recording paths changed during the original callback.")

    @contextmanager
    def _stage(self, name):
        self._context()
        ledger = self._torque_ledger
        previous = ledger.stage
        ledger.stage = name
        try:
            self.work.charge(name)
            self._context()
            yield
            self._context()
        finally:
            ledger.stage = previous

    @staticmethod
    def _entries(history):
        if (type(history) is not TorqueState or type(history.active) is not dict
                or len(history.active) > MAX_OUTPUT_RECORDS
                or type(history.started_count) is not int or history.started_count < 0
                or type(history.completed_count) is not int or history.completed_count < 0
                or any(type(key) is not str or type(value) is not _ActiveTorque
                       or key != value.key for key, value in history.active.items())):
            raise ValueError("A torque history has an invalid native shape.")
        result = []
        for key, value in sorted(history.active.items()):
            if (type(value.target) is not str or type(value.axis) is not str or value.axis not in AXES
                    or type(value.torque_n_m) is not float or not math.isfinite(value.torque_n_m)
                    or type(value.sequence_index) is not int or value.sequence_index < 0
                    or any(type(clock) is not F or
                           max(clock.numerator.bit_length(), clock.denominator.bit_length()) > MAX_OPERAND_BITS
                           for clock in (value.duration, value.activation, value.completion))
                    or any(type(location) is not tuple or len(location) != 4
                           for location in (value.source, value.operand_source, value.duration_source))):
                raise ValueError("A torque history needs bounded native source operands.")
            # Copy immutable leaves before any structural callback, so a
            # mutation through an externally retained object cannot alter the
            # computation and its post-callback comparison together.
            result.append((key, replace(value)))
        return tuple(result)

    def _assert_entries(self, history, entries, owner=None):
        if (owner is not None and history.active is not owner) or self._entries(history) != entries:
            raise OntoKinError("OKL-E-RESOURCE", "Torque history changed during bounded traversal.",
                category="resource_limit", phase="evaluation",
                details={"budget_reason": "execution_context_required"})

    def _assert_entry(self, history, entry, owner, count):
        key, value = entry
        if (type(history) is not TorqueState or history.active is not owner
                or type(owner) is not dict or len(owner) != count or owner.get(key) != value):
            raise OntoKinError("OKL-E-RESOURCE", "Torque history changed during bounded traversal.",
                category="resource_limit", phase="evaluation",
                details={"budget_reason": "execution_context_required"})

    def _error(self, path, reason, message, *, code="OKL-E-FRAME", phase="admission",
               time=None, side="after", event=None, state=None, extra=None):
        state = self.state if state is None else state
        history = state.torques[path]
        changes = sorted(history.last_changes if history.last_time == time else (),
                         key=lambda item: item[1].key)
        active = self._entries(history)
        value = (changes[0][1] if changes else active[0][1] if active else
                 history.last_changes[0][1] if history.last_changes else None)
        payload = event.torque if event is not None else None
        source = event.span if event is not None else value.span if value else self.model.objects[path].span
        details = {"torque_reason": reason, "target_path": path,
                   "torque_key": payload.key if payload else value.key if value else None,
                   "sequence_index": (payload.sequence_index if payload else
                                      value.sequence_index if value else None)}
        if event is not None and event.impulse is not None:
            details["sequence_index"] = event.impulse.sequence_index
        if changes:
            details["changed_torques"] = [
                {"kind": kind, **_record(self.model, item)} for kind, item in changes]
        if extra:
            details.update(extra)
        if reason == "phase_domain":
            details.update(requested_time_seconds=time_text(self._requested_time),
                           last_valid_boundary_seconds=time_text(self.last_boundary))
        return OntoKinError(code, message, source,
            category="numerical_failure" if code == "OKL-E-NUMERIC" else "invalid",
            phase=phase, time=time, side=side, element_id=list(self.model.objects[path].element_id),
            related=[self.model.objects[path].span], details=details,
            blocks=["evaluated", "delivered"], rule_ids=["TOR-001"])

    def _next_boundary(self):
        result = super()._next_boundary()
        if not hasattr(self.state, "torques"):
            return result
        for history in self.state.torques.values():
            entries = self._entries(history)
            owner = history.active
            for entry in entries:
                _, value = entry
                with self._stage("torque_boundary_scan"):
                    self._assert_entry(history, entry, owner, len(entries))
                    if result is None or compare(value.completion, result, self.work) < 0:
                        result = value.completion
            self._assert_entries(history, entries, owner)
        return result

    @staticmethod
    def _change(history, time, kind, value):
        if type(history) is _ForceState:
            ForceSimulator._change(history, time, kind, value)
            return
        if history.last_time != time:
            history.last_time = time
            history.last_changes = ()
        history.last_changes += ((kind, value),)

    def _phase_polynomial(self, anchor, time):
        a = PhaseArithmetic(self.work)
        u = exact(a.number(time), a.number(anchor.time), "sub", self.work)
        u2 = exact(u, u, "mul", self.work)
        linear = exact(a.number(anchor.speed), u, "mul", self.work)
        curved = exact(exact(a.number(anchor.acceleration), u2, "mul", self.work), F(2), "div", self.work)
        phase = exact(linear, curved, "add", self.work)
        speed = exact(a.number(anchor.speed), exact(a.number(anchor.acceleration), u, "mul", self.work), "add", self.work)
        return phase, speed

    def _smooth_speed(self, path, time, state):
        history = state.torques[path]
        anchor = history.pending_rotation or history.rotation
        if anchor is not None:
            return self._phase_polynomial(anchor, time)[1]
        return PhaseArithmetic(self.work).number(state.dynamic[path].state.omega[AXIS_INDEX[history.axis]])

    def _reference_at(self, history, time):
        reference = history.reference
        a = PhaseArithmetic(self.work)
        d = a.sub(a.number(time), reference.time)
        width = a.absolute(d)
        difference = a.absolute(a.sub(a.number(history.acceleration or 0.0), reference.acceleration))
        speed = a.add(reference.speed, a.mul(reference.acceleration, d))
        speed_error = a.add(reference.speed_error, a.mul(difference, width))
        angle_error = a.add(reference.angle_error, a.mul(reference.speed_error, width),
                            a.div(a.mul(difference, width, width), F(2)))
        return speed, angle_error, speed_error

    def _reference_origin(self, path, time, state, acceleration, *, before=None,
                          angle_extra=F(0), speed_extra=F(0), speed_delta=F(0)):
        history = state.torques[path]
        with self._stage("torque_reference_origin"):
            a = PhaseArithmetic(self.work)
            if history.reference is None:
                if before is None:
                    before = self._anchor_bound(path, time, state)
                speed = self._smooth_speed(path, time, state)
                angle_error = before.rotation_error_rad
                speed_error = before.angular_velocity_error_rad_per_s
            else:
                speed, angle_error, speed_error = self._reference_at(history, time)
            history.reference = TorqueReferenceOrigin(time, a.add(speed, speed_delta), acceleration,
                a.add(angle_error, angle_extra), a.add(speed_error, speed_extra))

    def angular_state(self, path, time, state=None):
        """Full internal rotation and canonical selected speed on the split law."""
        state = self.state if state is None else state
        history = state.torques[path]
        anchor = history.pending_rotation or history.rotation
        if anchor is None:
            point = super()._dynamic_kinematics(path, time, state)
            return point.rotation, point.omega[AXIS_INDEX[history.axis]], None
        phase, speed = self._phase_polynomial(anchor, time)
        if compare(abs(phase), PHASE_LIMIT, self.work) > 0:
            raise self._error(path, "phase_domain", "A torque rotation segment exceeds the supported phase domain.",
                code="OKL-E-NUMERIC", phase="evaluation", time=time,
                side=self._requested_side, state=state)
        phi = round_binary64(phase, work=self.work)
        omega = round_binary64(speed, work=self.work)
        rotation = anchor.rotation
        if phase:
            rotation = self.pose_ops.multiply(self.pose_ops.axis_rotation(AXES[history.axis], phi), rotation)
        return rotation, omega, phi

    def _dynamic_kinematics(self, path, time, state, *, pose_only=False, recording_context=None):
        history = getattr(state, "torques", {}).get(path)
        if history is None or history.rotation is None and history.pending_rotation is None:
            return super()._dynamic_kinematics(path, time, state, pose_only=pose_only,
                                              recording_context=recording_context)
        self._check()
        anchor = state.dynamic[path]
        elapsed = time - anchor.time
        initial = anchor.state
        acceleration = self._acceleration(path, state)
        position = self.pose_ops.parabolic(initial.position, initial.velocity, acceleration, elapsed)
        rotation, speed, _ = self.angular_state(path, time, state)
        if recording_context is not None:
            return self.pose_ops.make_recording(position=position, orientation=rotation)
        omega = [0.0, 0.0, 0.0]
        omega[AXIS_INDEX[history.axis]] = speed
        return self.pose_ops.make(position=position, orientation=rotation,
            velocity=ZERO if pose_only else self.pose_ops.affine(initial.velocity, acceleration, elapsed),
            omega=ZERO if pose_only else tuple(omega))

    def _event(self, event, time, state, incoming, dependencies, touched):
        if id(event) in self._torque_sources:
            self._source_event(event, time)
        if event.kind != "torque":
            history = state.torques.get(event.target) if event.kind == "impulse" else None
            latched = history is not None and history.axis is not None
            old_rotation = None
            before_speed = None
            if latched:
                old_rotation, before_speed, _ = self.angular_state(event.target, time, state)
            self._ordinary_event(event, time, state, incoming, dependencies, touched)
            if latched:
                record = state.impulses[event.target].last_applications[-1]
                omega = tuple(record["angular_velocity_after_world_rad_per_s"])
                with self._stage("torque_impulse_axis"):
                    index = AXIS_INDEX[history.axis]
                    if any(value != 0.0 for i, value in enumerate(omega) if i != index):
                        raise self._error(event.target, "impulse_axis",
                            "An impulse must preserve the carrier's latched torque axis.",
                            event=event, time=time, state=state, extra={"expected_axis": history.axis,
                            "actual_angular_velocity_world_rad_per_s": list(omega)})
                if event.impulse.impulse_world_n_s != ZERO:
                    a = PhaseArithmetic(self.work)
                    delta = a.div(a.number(record["angular_impulse_world_n_m_s"][index]),
                                  a.number(self.model.objects[event.target].inertia))
                    inherited = state.dynamic_errors[event.target]
                    self._reference_origin(event.target, time, state, history.reference.acceleration,
                        angle_extra=inherited.rotation_rad,
                        speed_extra=inherited.angular_velocity_rad_per_s, speed_delta=delta)
                    if history.rotation is not None and omega[index] != before_speed:
                        # A tentative record supports the next ordered impulse.
                        # Only final aggregation charges/publishes the anchor.
                        history.pending_rotation = TorqueRotationAnchor(time, old_rotation,
                            omega[index], history.acceleration or 0.0)
            return
        source = self._source_event(event, time)
        body = self._body(event.target)
        with self._stage("torque_activation"):
            self._source_event(event, time)
            self._body(event.target)
            p = event.torque
            obj = self.model.objects[event.target]
            history = state.torques[event.target]
            if state.modes[event.target] != "dynamic" or event.target in self._incoming(state):
                raise self._error(event.target, "target_mode", "A torque requires a currently free dynamic sphere.",
                    code="OKL-E-MOTION-MODE", event=event, time=time, state=state)
            if (body[0] != "sphere_body" or
                    any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0
                        for value in body[1:])):
                raise self._error(event.target, "target_body",
                    "A torque requires positive own sphere mass, radius and inertia.",
                    code="OKL-E-PHYSICAL-DOMAIN", event=event, time=time, state=state)
            if history.axis is not None and history.axis != p.axis:
                raise self._error(event.target, "axis_lock", "A torque interval must use the carrier's latched world axis.",
                    event=event, time=time, state=state,
                    extra={"expected_axis": history.axis, "actual_axis": p.axis})
            current = self._dynamic_kinematics(event.target, time, state)
            if any(value != 0.0 for i, value in enumerate(current.omega) if i != AXIS_INDEX[p.axis]):
                raise self._error(event.target, "incoming_axis", "Angular velocity must lie on the selected torque axis.",
                    event=event, time=time, state=state)
            initial_bound = self._anchor_bound(event.target, time, state) if history.axis is None else None
            value = _active(self.model, event, time, work=self.work, snapshot=source)
            if p.key in history.active:
                raise ValueError("Duplicate admitted torque key.")
            if history.axis is None:
                history.axis = p.axis
                history.acceleration = 0.0
                self._reference_origin(event.target, time, state, F(0), before=initial_bound)
            self._source_event(event, time)
            self._body(event.target)
            history.active[p.key] = value
            history.started_count += 1
            self._change(history, time, "started", value)
        self._invalidate()

    def _ordinary_event(self, event, time, state, incoming, dependencies, touched):
        if event.kind not in {"release", "impulse"}:
            return super()._event(event, time, state, incoming, dependencies, touched)
        from .torque_transfer_bounds import (dynamic_transfer, first_release,
                                              release_anchor)
        self._terminal_pose_context = None
        self._invalidate()
        before = (self._anchor_bound(event.target, time, state)
                  if event.kind == "impulse" and event.target in state.dynamic else None)
        captured = None
        if event.kind == "release":
            joint = self.model.joints.get(event.target)
            site = self.model.sites.get(joint.child) if joint is not None else None
            if site is not None:
                captured = first_release(self, self.state, site.owner, time)
        elif before is not None and event.impulse is not None and event.impulse.impulse_world_n_s != ZERO:
            captured = dynamic_transfer(self, state, event.target, time)
        ForceSimulator._event(self, event, time, state, incoming, dependencies, touched)
        if event.kind == "release":
            child = self.model.sites[self.model.joints[event.target].child].owner
            state.dynamic[child].state = self.pose_ops.materialize(incoming[child])
            state.dynamic_errors[child] = self._anchor_error(self._anchor_bound(child, time, self.state))
            state.dynamic_error_times[child] = time
            state.ideal_accelerations[child] = tuple(PhaseArithmetic(self.work).number(value)
                                                    for value in self.model.gravity)
            release_anchor(self, state, child, time, captured)
            self._pending_releases.append(self._release_record(event, time, incoming, dependencies))
        elif event.impulse.impulse_world_n_s != ZERO:
            self._impulse_error(event, time, state, before, captured)
        self._invalidate()

    def _impulse_error(self, event, time, state, before, transfer=None):
        super()._impulse_error(event, time, state, before, transfer=None)
        if transfer is not None:
            from .torque_transfer_bounds import impulse_anchor
            obj = self.model.objects[event.target]
            impulse_anchor(self, state, event.target, time, transfer, before,
                           event.impulse, obj.mass, obj.inertia)

    def _aggregate(self, path, time, state):
        history = state.torques[path]
        original_anchor = state.dynamic.get(path)
        original_error = state.dynamic_errors.get(path)
        # A neutral couple has no authority to alter the inherited force
        # anchor or its numerical record. The torque shadow remains in its
        # own origin and is propagated after this ordinary transition.
        previous = getattr(self, "_torque_legacy_force_bound", None)
        self._torque_legacy_force_bound = path if history.rotation is None else None
        try:
            self._force_aggregate(path, time, state)
        finally:
            self._torque_legacy_force_bound = previous
        if (history.axis is not None and history.rotation is None
                and (state.dynamic.get(path) is not original_anchor
                     or state.dynamic_errors.get(path) is not original_error)):
            error = state.dynamic_errors[path]
            self._reference_origin(path, time, state, history.reference.acceleration,
                angle_extra=error.rotation_rad, speed_extra=error.angular_velocity_rad_per_s)

    def _force_aggregate(self, path, time, state):
        """Inherited force graph with the .22 transition-envelope adapter."""
        from .torque_transfer_bounds import CellArithmetic, dynamic_transfer, force_anchor
        self._invalidate()
        changed = path in state.dynamic and (state.forces[path].last_time == time or
                                             state.forces[path].acceleration is None)
        if changed:
            self._terminal_pose_context = None
        original = state.dynamic.get(path)
        before = self._anchor_bound(path, time, state) if changed else None
        transfer = dynamic_transfer(self, state, path, time) if changed and path in state.dynamic_cells else None
        ForceSimulator._aggregate(self, path, time, state)
        if changed:
            error = self._anchor_error(before)
            if state.dynamic[path] is original:
                a = PhaseArithmetic(self.work)
                point = self._dynamic_kinematics(path, time, state)
                position_round = a.l1(tuple(a.sub(a.number(x), y) for x, y in zip(point.position, point.exact_position)))
                velocity_round = a.l1(tuple(a.sub(a.number(x), y) for x, y in zip(point.velocity, point.exact_velocity)))
                if transfer is not None:
                    cell = CellArithmetic(self.work)
                    position_round = a.maximum(position_round, cell.publication(transfer.sizes[0]))
                    velocity_round = a.maximum(velocity_round, cell.publication(transfer.sizes[1]))
                error = AnchorError(a.add(error.position_m, position_round),
                    a.add(error.rotation_rad, F(1, 1 << 50)),
                    a.add(error.velocity_m_per_s, velocity_round), error.angular_velocity_rad_per_s)
            else:
                state.dynamic[path].state = self.pose_ops.materialize(state.dynamic[path].state)
            state.dynamic_errors[path] = error
            state.dynamic_error_times[path] = time
            state.ideal_accelerations[path] = self._ideal_acceleration(path, state)
            if transfer is not None:
                force_anchor(self, state, path, time, transfer, self._anchor_error(before),
                             changed=state.dynamic[path] is not original)
        self._invalidate()

    def _aggregate_torque(self, path, time, state):
        history = state.torques[path]
        if history.axis is None:
            return
        changed = history.last_time == time
        if not changed and history.pending_rotation is None:
            return
        entries = self._entries(history)
        owner = history.active
        body = self._body(path)
        with self._stage("torque_aggregate_begin"):
            self._assert_entries(history, entries, owner)
            self._body(path)
            inertia = PhaseArithmetic(self.work).number(body[-1])
        total = F(0)
        for entry in entries:
            _, value = entry
            with self._stage("torque_aggregate_term"):
                self._assert_entry(history, entry, owner, len(entries))
                total = exact(total, PhaseArithmetic(self.work).number(value.torque_n_m), "add", self.work)
        try:
            net = round_binary64(total, work=self.work)
        except ReachAdmissionError as error:
            if error is self.work.callback_error or error.reach_code != "reach_numeric":
                raise
            raise self._error(path, "net_overflow", "A canonical torque result exceeds the finite binary64 domain.",
                code="OKL-E-NUMERIC", phase="evaluation", time=time, state=state,
                extra={"operation": "net_torque"}) from error
        try:
            acceleration = round_binary64(exact(PhaseArithmetic(self.work).number(net), inertia, "div", self.work), work=self.work)
        except ReachAdmissionError as error:
            if error is self.work.callback_error or error.reach_code != "reach_numeric":
                raise
            raise self._error(path, "acceleration_overflow", "A canonical torque result exceeds the finite binary64 domain.",
                code="OKL-E-NUMERIC", phase="evaluation", time=time, state=state,
                extra={"operation": "angular_acceleration"}) from error
        reference_alpha = exact(total, inertia, "div", self.work)
        with self._stage("torque_aggregate_publish"):
            self._assert_entries(history, entries, owner)
            self._body(path)
            needs_anchor = ((history.rotation is None and acceleration != 0.0)
                or history.rotation is not None and acceleration != history.acceleration
                or history.pending_rotation is not None)
            if needs_anchor:
                rotation, speed, _ = self.angular_state(path, time, state)
                a = PhaseArithmetic(self.work)
                old_anchor = history.pending_rotation or history.rotation
                phase_error = speed_error = F(0)
                if old_anchor is not None:
                    phase, smooth_speed = self._phase_polynomial(old_anchor, time)
                    phase_error = a.absolute(a.sub(a.number(round_binary64(phase, work=self.work)), phase))
                    speed_error = a.absolute(a.sub(a.number(speed), smooth_speed))
                self._reference_origin(path, time, state, reference_alpha,
                    angle_extra=a.add(phase_error, rotation.error_rad), speed_extra=speed_error)
                with self._stage("torque_rotation_anchor"):
                    history.rotation = TorqueRotationAnchor(time, rotation, speed, acceleration)
                    history.pending_rotation = None
            elif history.reference.acceleration != reference_alpha:
                self._reference_origin(path, time, state, reference_alpha)
            history.net = net
            history.acceleration = acceleration
            self._body(path)
        self._invalidate()

    def _process_boundary(self, time):
        self._context()
        if type(time) is not F:
            raise ValueError("A torque boundary requires its native exact clock.")
        self.work.guard(time)
        time = F(time.numerator, time.denominator)
        self._pending_releases = []
        self._pending_reach_output = None
        self._derived_pose_cache.clear()
        self._terminal_pose_context = None
        self._check()
        incoming, _ = self._kinematics(time, self.state)
        dependencies = {path: self._dependencies(self.model.sites[self.model.joints[path].child].owner, self.state)
                        for path in self.state.active_grips}
        staged = copy.deepcopy(self.state)
        try:
            for path, runtime in staged.actions.items():
                self._check()
                if runtime.status == "running" and runtime.elapsed_at(time) == self.model.actions[path].duration:
                    self._latch(path, time, staged, "completed")
            for history in staged.forces.values():
                self._check()
                for key in sorted(history.active):
                    self._check()
                    value = history.active[key]
                    if value.completion == time:
                        del history.active[key]
                        history.completed_count += 1
                        # The inherited method accepts force history records.
                        ForceSimulator._change(history, time, "completed", value)
            for path in sorted(staged.torques):
                history = staged.torques[path]
                entries = self._entries(history)
                owner = history.active
                ending = tuple((key, value) for key, value in entries if value.completion == time)
                for key, value in ending:
                    with self._stage("torque_completion"):
                        if history.active is not owner or history.active.get(key) != value:
                            raise ValueError("Torque completion source changed during staging.")
                        del history.active[key]
                        history.completed_count += 1
                        self._change(history, time, "completed", value)
            has_source = self.event_index < len(self.events) and self.events[self.event_index].time == time
            if has_source:
                touched = set()
                for event in self.events[self.event_index].events:
                    self._check()
                    self._event(event, time, staged, incoming, dependencies, touched)
            # Force failures retain their inherited precedence and object order.
            for path in staged.forces:
                self._aggregate(path, time, staged)
            for path in sorted(staged.torques):
                self._aggregate_torque(path, time, staged)
            self._validate_staged(time, staged, incoming)
            self._bounded_torque_projection(time, staged)
            torque_changed = any(history != self.state.torques[path]
                                 for path, history in staged.torques.items())
            if torque_changed:
                with self._stage("torque_boundary_commit"):
                    self._context()
            else:
                self._check()
            self.state = staged
            self._torque_state_owner = staged
            self._torque_history_owner = staged.torques
            if has_source:
                self.event_index += 1
            self.zero_pending = False
            self.last_boundary = time
            self.boundaries.append(time_text(time))
            self.incoming_releases = self._pending_releases
            self.incoming_release_time = time
        except BaseException:
            self._invalidate()
            raise
        finally:
            self._pending_releases = []
            self._terminal_pose_context = None

    def _segment(self, path, start, end, state):
        history = state.torques[path]
        anchor = history.pending_rotation or history.rotation
        with self._stage("torque_segment"):
            a = PhaseArithmetic(self.work)
            if anchor is None:
                speed = a.number(state.dynamic[path].state.omega[AXIS_INDEX[history.axis]])
                return F(0), a.absolute(speed), False
            values = [self._phase_polynomial(anchor, time) for time in (start, end)]
            phase_max = a.maximum(*(a.absolute(pair[0]) for pair in values))
            speed_max = a.maximum(*(a.absolute(pair[1]) for pair in values))
            if anchor.acceleration:
                with self._stage("torque_segment_vertex"):
                    vertex = a.div(-a.number(anchor.speed), a.number(anchor.acceleration))
                    lo, hi = a.sub(start, anchor.time), a.sub(end, anchor.time)
                    if compare(lo, vertex, self.work) <= 0 and compare(vertex, hi, self.work) <= 0:
                        vertex_phase = self._phase_polynomial(anchor, a.add(anchor.time, vertex))[0]
                        phase_max = a.maximum(phase_max, a.absolute(vertex_phase))
            if compare(phase_max, PHASE_LIMIT, self.work) > 0:
                raise self._error(path, "phase_domain", "A torque rotation segment exceeds the supported phase domain.",
                    code="OKL-E-NUMERIC", phase="evaluation", time=end,
                    side=self._requested_side, state=state)
            for _, speed in values:
                round_binary64(speed, work=self.work)
            return phase_max, speed_max, bool(phase_max)

    def _check_dynamic_extrema(self, start, end):
        super()._check_dynamic_extrema(start, end)
        for path, history in self.state.torques.items():
            if history.axis is not None:
                self._segment(path, start, end, self.state)

    def torque_phase_fields(self, path, start, end, state):
        """Angular terms for the shared source-phase graph, before composition."""
        if getattr(self, "_torque_legacy_force_bound", None) == path:
            return None
        history = getattr(state, "torques", {}).get(path)
        if history is None or history.axis is None or history.reference is None:
            return None
        a = PhaseArithmetic(self.work)
        phase_max, speed_max, moving = self._segment(path, start, end, state)
        references = [self._reference_at(history, time) for time in (start, end)]
        angle_error = a.maximum(*(value[1] for value in references))
        speed_error = a.maximum(*(value[2] for value in references))
        reference_speed = a.maximum(*(a.absolute(value[0]) for value in references))
        anchor = history.pending_rotation or history.rotation
        if anchor is not None:
            phase_round = a.add(a.mul(phase_max, F(1, 1 << 53)), F(1, 1 << 1075))
            speed_round = a.add(a.mul(speed_max, F(1, 1 << 53)), F(1, 1 << 1075))
            angle_error = a.add(angle_error, anchor.rotation.error_rad)
        else:
            elapsed = a.maximum(a.absolute(a.sub(start, state.dynamic[path].time)),
                                a.absolute(a.sub(end, state.dynamic[path].time)))
            moving = bool(speed_max and elapsed)
            phase_round = a.add(a.mul(a.mul(speed_max, elapsed), F(1, 1 << 53)), F(1, 1 << 1075)) if moving else F(0)
            speed_round = F(0)
        speed_error = a.add(speed_error, speed_round)
        return {"trig_count": int(moving), "product_count": 3 if moving else 1,
            "coordinate_angle_error_rad": phase_round,
            "anchor_rotation_error_rad": angle_error,
            "angular_velocity_error_rad_per_s": speed_error,
            "angular_speed_upper_rad_per_s": a.add(reference_speed, speed_error),
            "angular_acceleration_upper_rad_per_s2": a.absolute(history.reference.acceleration),
            "actual_angular_speed_upper_rad_per_s": a.add(speed_max, speed_round),
            "actual_angular_acceleration_upper_rad_per_s2": a.absolute(a.number(history.acceleration))}

    def phase_bounds(self, start, end, state=None):
        from .torque_phase import phase_bounds
        try:
            return phase_bounds(self, start, end, state)
        except ReachAdmissionError as error:
            self._numeric_error(error, time=F(start))

    def _anchor_bound(self, path, time, state):
        from .torque_phase import phase_bounds
        return phase_bounds(self, time, time, state,
                            selected_frames=[path + ".frame"])["objects"][path]

    def recording_frames(self, time, state, selected_paths, *, moving_frames=None,
                          recording_context=None, recording_angular_proof=None,
                          recording_pose_ops=None):
        """Use the direct controlled transform graph without angular cursors.

        The inherited recording namespace retains exact p/q operands and
        omits unused derivatives. No phase context, alternate operations, or
        constant-rate proof enters this traversal, so dynamic roots still call
        this subclass's exact split polynomial at every requested clock.
        """
        selected, seen = [], set()
        for path in selected_paths:
            self._check()
            if (type(path) is not str or path != "world" and
                    (not path.endswith(".frame") or path[:-6] not in self.model.objects
                     and path[:-6] not in self.model.sites)):
                raise ValueError("A recording selector must name an actual source frame.")
            if path not in seen:
                seen.add(path)
                selected.append(path)
        _, frames = self._resolve_kinematics(time, state, selected_frames=selected,
                                            pose_only=True, recording_only=True,
                                            recording_moving_frames=moving_frames)
        result = {}
        for path in selected:
            self._check()
            result[path] = RecordingPose(frames[path].position, frames[path].orientation)
        self._context()
        return result

    def torque_projection(self, path, time, state=None):
        state = self.state if state is None else state
        history = state.torques[path]
        entries = self._entries(history)
        owner = history.active
        active, changes = [], []
        for entry in entries:
            _, value = entry
            with self._stage("torque_projection"):
                self._assert_entry(history, entry, owner, len(entries))
                active.append(_record(self.model, value))
        recent = history.last_changes
        if type(recent) is not tuple or len(recent) > MAX_OUTPUT_RECORDS:
            raise ValueError("Invalid torque change history.")
        for kind, value in recent:
            with self._stage("torque_projection"):
                if history.last_changes != recent:
                    raise ValueError("Torque change history changed during projection.")
                changes.append({"kind": kind, **_record(self.model, value)})
        with self._stage("torque_projection"):
            result = {"active": active, "net_torque_n_m": history.net,
                "angular_acceleration_rad_per_s2": history.acceleration,
                "axis": history.axis, "rotation_route": "split" if history.rotation else "legacy",
                "rotation_anchor_seconds": None if history.rotation is None else time_text(history.rotation.time),
                "signed_angular_speed_rad_per_s": None, "phase_since_anchor_rad": None,
                "angular_acceleration_reference_rad_per_s2": None,
                "angular_error_bound_rad": None, "angular_speed_error_bound_rad_per_s": None,
                "started_count": history.started_count, "completed_count": history.completed_count,
                "last_change_time_seconds": None if history.last_time is None else time_text(history.last_time),
                "last_changes": changes}
            if history.axis is not None:
                rotation, speed, phase = self.angular_state(path, time, state)
                _, angle_error, speed_error = self._reference_at(history, time)
                a = PhaseArithmetic(self.work)
                if history.rotation is not None:
                    smooth_phase, smooth_speed = self._phase_polynomial(history.rotation, time)
                    angle_error = a.add(angle_error, a.absolute(a.sub(a.number(phase), smooth_phase)))
                    speed_error = a.add(speed_error, a.absolute(a.sub(a.number(speed), smooth_speed)))
                angle_error = a.add(angle_error, rotation.error_rad, EXPOSED_ROTATION_ERROR)
                def ratio(value):
                    self.work.guard(value)
                    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}
                result.update(signed_angular_speed_rad_per_s=speed, phase_since_anchor_rad=phase,
                    angular_acceleration_reference_rad_per_s2=ratio(history.reference.acceleration),
                    angular_error_bound_rad=ratio(angle_error),
                    angular_speed_error_bound_rad_per_s=ratio(speed_error))
            self._assert_entries(history, entries, owner)
            return result

    def _bounded_torque_projection(self, time, state):
        result, entries, byte_count = {}, 0, 0
        for path in self.model.objects:
            value = self.torque_projection(path, time, state)
            try:
                size = measure_json(value, max_entries=MAX_OUTPUT_RECORDS - entries,
                    max_bytes=MAX_JSON_BYTES - byte_count, check=self._work_check)
            except JSONLimitError as error:
                raise OntoKinError("OKL-E-RESOURCE", "Complete torque history exceeds the bounded output contract.",
                    self.model.span, category="resource_limit", phase="inspection", blocks=[],
                    details=error.details) from error
            entries += size["entries"]
            byte_count += size["bytes"]
            result[path] = value
        return result

    def snapshot(self, time, side):
        result = super().snapshot(time, side)
        for path, value in self._bounded_torque_projection(time, self.state).items():
            result["objects"][path]["torques"] = value
        return self._snapshot_data(result, time, side)

    def recording_boundary(self, time, side, *, _reuse=None):
        result = super().recording_boundary(time, side, _reuse=None)
        for path, value in self._bounded_torque_projection(time, self.state).items():
            result["objects"][path]["torques"] = value
        return self._snapshot_data(result, time, side)

    def advance(self, time, side="after"):
        self._requested_time, self._requested_side = getattr(
            self, "_torque_requested_observation", (F(time), side))
        return super().advance(time, side)


# Capture before any request callback, including public source preflights that
# occur before a simulator is constructed. Mutable aliases cannot become a
# new request's trusted entrypoint. This tuple has the same private immutable
# receipt status as the helper's authority catalogues.
_CANONICAL_PRESENT_BINDINGS = tuple(row for row in _canonical_point_authority[2]
                                    if row[1] in row[0])
_CANONICAL_ABSENT_BINDINGS = tuple(row for row in _canonical_point_authority[2]
                                   if row[1] not in row[0])
_CANONICAL_POINT_ENTRY = (
    _canonical_point_authority,
    # Original native function objects retain their read-only globals,
    # builtins, closure and class pointers. Their dictionary contents remain
    # checked separately on every callback. Only these three fields can be
    # replaced on the retained function object.
    attrgetter("__code__", "__defaults__", "__kwdefaults__"),
    tuple(row[0] for row in _canonical_point_authority[0]),
    tuple(value for row in _canonical_point_authority[0] for value in row[1:4]),
    tuple((row[3], tuple(value for pair in row[7] for value in pair))
          for row in _canonical_point_authority[0] if row[3] is not None),
    tuple(row[0] for row in _CANONICAL_PRESENT_BINDINGS),
    tuple(row[1] for row in _CANONICAL_PRESENT_BINDINGS),
    tuple(row[2] for row in _CANONICAL_PRESENT_BINDINGS),
    tuple(row[0] for row in _CANONICAL_ABSENT_BINDINGS),
    tuple(row[1] for row in _CANONICAL_ABSENT_BINDINGS),
    object(),
)
_CANONICAL_GUARD_BOOTSTRAP = (
    _CANONICAL_POINT_ENTRY, _canonical_after_entry, TorqueSimulator._context_after_dispatch,
    all, any, map, is_, chain.from_iterable, repeat, len, object.__getattribute__, dict.get,
    dict.items, dict.__contains__, OntoKinError,
)
_bind_canonical_dispatch(TorqueSimulator)
