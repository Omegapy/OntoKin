"""Coupled reach lifecycle on the inherited whole-boundary force transaction."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType

from . import force_runtime as _force_runtime
from .diagnostics import OntoKinError
from .evaluator import (_ActionState, _DynamicInitial, _Kinematics, _NumericFault,
                        ZERO, _f, _round, time_text)
from .force_runtime import ForceSimulator, _ForceRunState
from .json_limits import JSONLimitError, measure_json
from .reach_kinematics import (admit_planar, measured_residual_squared,
                               recording_pair, rounded_sqrt, sample_pair)
from .reach_numeric import ReachAdmissionError, ReachExecutionWork, compare, exact, round_binary64
from .reach_projection import (occurrence, reach_projection, reach_record_bound,
                               measure_reach_json)
from .reach_source import reach_error
from .reach_phase import AnchorError, PhaseArithmetic, joint_phase, phase_bounds
from .reach_pose import ZERO as POSE_ZERO
from .values import bounded_data


def _incoming_release_bound(model, time, *, check=None):
    """Count topology-permitted contributor identities without admitting events."""
    parents = None
    total = 1  # The array itself is retained even with no releases.
    for block in model.events:
        if check is not None:
            check()
        if block.time != time:
            continue
        for index, event in enumerate(block.events):
            if check is not None:
                check()
            if event.kind != "release":
                continue
            if parents is None:
                # Most boundaries have no release. Their retained empty array
                # still has weight one, but no contributor graph is needed.
                # Build it once, only when an actual source release needs it.
                parents = {}
                for path, joint in model.joints.items():
                    if check is not None:
                        check()
                    parents[model.sites[joint.child].owner] = (
                        ("joint", path), model.sites[joint.parent].owner)
                for path, follow in model.follows.items():
                    if check is not None:
                        check()
                    parents[follow.child] = (("follow", path), model.frame_owner(follow.parent))
            joint = model.joints[event.target]
            child = model.sites[joint.child].owner
            cursor, dependencies, visited = child, set(), set()
            while cursor in parents and cursor not in visited:
                if check is not None:
                    check()
                visited.add(cursor)
                relation, cursor = parents[cursor]
                dependencies.add(relation)
            contributors = []
            for path, action in model.actions.items():
                if check is not None:
                    check()
                payload = action.reach
                if payload is None or not ({("joint", payload.shoulder), ("joint", payload.elbow)} & dependencies):
                    continue
                contributors.append({"action": occurrence(model, path),
                    "shoulder": occurrence(model, payload.shoulder),
                    "elbow": occurrence(model, payload.elbow),
                    "joint_coordinates_rad": [0.0, 0.0], "joint_rates_rad_per_s": [0.0, 0.0]})
            source = model.source_provenance[event.span.source_id]
            record = {"program_revision": model.program_revision,
                "source_location": {"source_id": event.span.source_id,
                    "source_revision": source["source_revision"],
                    "start_byte": event.span.start, "end_byte": event.span.end},
                "sequence_index": index, "time_seconds": time_text(time),
                "grip": occurrence(model, event.target), "target": occurrence(model, child),
                "reach_contributors": contributors,
                "incoming_pose_world": {"position_m": [0.0, 0.0, 0.0], "orientation_wxyz": [1.0, 0.0, 0.0, 0.0]},
                "incoming_linear_velocity_world_m_per_s": [0.0, 0.0, 0.0],
                "incoming_angular_velocity_world_rad_per_s": [0.0, 0.0, 0.0]}
            total += measure_reach_json(record, check=check)["entries"]
    return total


def _boundary_history_endpoint(model, horizon, side):
    endpoint = model.duration if horizon is None else Fraction(horizon)
    if side not in {"before", "after"} or not 0 <= endpoint <= model.duration:
        raise ValueError("The history horizon must be a valid exact source prefix.")
    return endpoint


def _boundary_history_weight(model, time, endpoint, side, check):
    """One complete H06 row, independent of previously retained rows."""
    from .evaluator import _records_per_sample

    if not 0 <= time <= endpoint:
        raise ValueError("A retained boundary lies outside the requested prefix.")
    dropped = len(model.objects) + len(model.sites) + 1
    last_side = "before" if time == endpoint and side == "before" else "after"
    before = _records_per_sample(model, check=check, horizon=time, side="before") - dropped
    after = _records_per_sample(model, check=check, horizon=time, side=last_side) - dropped
    incoming = 1 if last_side == "before" else _incoming_release_bound(model, time, check=check)
    return 2 + before + after + incoming


def _check_boundary_history_total(model, total, time):
    from .evaluator import MAX_OUTPUT_RECORDS

    if total > MAX_OUTPUT_RECORDS:
        raise reach_error("reach_resource", "Complete retained reach boundaries exceed the state-record budget.",
            model.span, phase="inspection", blocks=[], details={"budget": "boundary_state_records",
                "limit": MAX_OUTPUT_RECORDS, "consumed": total,
                "through_seconds": time_text(time)})


def boundary_history_bound(model, boundary_times, *, horizon=None, side="after", check=None):
    """Preflight the adopted complete H06 history before retaining all sides.

    The supplied exact clocks are actual semantic boundaries discovered by a
    bounded prefix replay. This function never performs admission or samples a
    future event. Both sides use the inherited conservative nested-history
    weights, and every repeated reach/source identity counts at each occurrence.
    """
    endpoint = _boundary_history_endpoint(model, horizon, side)
    total = 0
    for value in boundary_times:
        if check is not None:
            check()
        time = Fraction(value)
        total += _boundary_history_weight(model, time, endpoint, side, check)
        _check_boundary_history_total(model, total, time)
    return total


class _BoundaryHistoryPreflight:
    """Append complete exact history weights within one immutable source plan.

    The planner discovers increasing boundaries. A completed row's forecast
    depends only on its source model, exact clock and fixed endpoint/side; a
    later boundary cannot change it. Keep the sum rather than reconstructing
    all earlier forecasts. No output occurrence is removed from that sum, and
    no source or numerical result is cached across plans.
    """

    def __init__(self, model, *, horizon=None, side="after", check=None):
        self.model = model
        self.endpoint = _boundary_history_endpoint(model, horizon, side)
        self.side = side
        self.check = check
        self._model = model
        self._endpoint = self.endpoint
        self._side = side
        self._program_revision = model.program_revision
        self._duration = model.duration
        self.total = 0
        self.last_time = None
        self._active = False

    def _check_context(self):
        if (self.model is not self._model
                or self.model.program_revision != self._program_revision
                or self.model.duration != self._duration
                or self.endpoint != self._endpoint or self.side != self._side):
            raise ValueError("A history preflight cannot change its source or endpoint context.")
        _boundary_history_endpoint(self.model, self.endpoint, self.side)

    def append(self, value):
        if self._active:
            raise ValueError("A history preflight cannot be reentered while appending a boundary.")
        self._active = True
        try:
            if self.check is not None:
                self.check()
            self._check_context()
            time = Fraction(value)
            if self.last_time is not None and time <= self.last_time:
                raise ValueError("Recording history boundaries must increase strictly.")
            weight = _boundary_history_weight(self.model, time, self.endpoint, self.side, self.check)
            total = self.total + weight
            # Charge/check the new accumulation before publishing either
            # field. Cancellation or a lowered limit leaves the prior prefix
            # intact; a callback cannot replace its source context unnoticed.
            if self.check is not None:
                self.check()
            self._check_context()
            _check_boundary_history_total(self.model, total, time)
            self.total, self.last_time = total, time
            return total
        finally:
            self._active = False


@dataclass
class _ReachActionState(_ActionState):
    start_time: Fraction | None = None
    solution: object | None = None
    terminal: dict | None = None
    ideal_initial: object | None = None
    ideal_rotation_error: Fraction = Fraction(0)
    initial_rotation: object | None = None


@dataclass
class _ReachRunState(_ForceRunState):
    ideal_coordinates: dict = field(default_factory=dict)
    ideal_positions: dict = field(default_factory=dict)
    root_rotation_errors: dict = field(default_factory=dict)
    root_rotation_values: dict = field(default_factory=dict)
    dynamic_errors: dict = field(default_factory=dict)
    dynamic_error_times: dict = field(default_factory=dict)
    ideal_accelerations: dict = field(default_factory=dict)


@dataclass
class _TerminalPoseContext:
    time: Fraction
    incoming_state: _ReachRunState
    staged_state: _ReachRunState | None = None
    frames: dict | None = None
    tips: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RecordingPose:
    """Only the actual canonical components consumed by a recorded key."""
    position: tuple[float, float, float]
    orientation: tuple[float, float, float, float]


@dataclass(frozen=True)
class _WorldTargetPoint:
    """The observed target point; no unused frame or derivative claim."""
    position: tuple[float, float, float]


@dataclass(frozen=True)
class _WorldTargetComponents:
    """One exact rotated target and its last complete translated projection."""
    offset: tuple[Fraction, Fraction, Fraction]
    position: tuple[Fraction, Fraction, Fraction]
    rounded: tuple[Fraction, Fraction, Fraction]
    point: _WorldTargetPoint
    target: tuple[Fraction, Fraction, Fraction] | None = None


class ReachSimulator(ForceSimulator):
    """One exact clock and two claims per reach, with no partial admission."""

    def __init__(self, model, check=None, *, work=None):
        self.work = work if work is not None else ReachExecutionWork(check=check)
        self.context_kind = "recorded_prefix"
        self._pose_cache = {}
        self._pair_cache = {}
        self._derived_pose_cache = {}
        self._terminal_pose_context = None
        self._pending_releases = []
        self._pending_reach_output = None
        self.incoming_releases = []
        self.incoming_release_time = None
        from .reach_pose import ReachPoseOps
        self.pose_ops = ReachPoseOps(self.work)
        self._identity_pose = self.pose_ops.identity()
        super().__init__(model, check=self._work_check)
        self.state = _ReachRunState(**vars(self.state))
        arithmetic = PhaseArithmetic(self.work)
        self.state.ideal_coordinates = {path: arithmetic.number(value) for path, value in self.state.coordinates.items()}
        self.state.ideal_positions = {path: tuple(arithmetic.number(value) for value in position)
                                     for path, position in self.state.positions.items()}
        for path in self.state.dynamic:
            self._check()
            self.state.dynamic_errors[path] = AnchorError()
            self.state.dynamic_error_times[path] = Fraction(0)
            self.state.ideal_accelerations[path] = tuple(arithmetic.number(value) for value in model.gravity)
        for path, action in model.actions.items():
            self._check()
            self.state.actions[path] = _ReachActionState()
        # Bound the maximal complete shape before allocating sampled maps.
        self.reach_weight_bound = reach_record_bound(model, check=self._work_check)

    def _numeric_error(self, error, *, action=None, time=None, phase="evaluation", node=None):
        if error is self.work.callback_error:
            raise error
        raise reach_error(error.reach_code, str(error), node or (action.span if action else self.model.span),
                          phase=phase, details=error.details, time=time,
                          element_id=None if action is None else action.element_id,
                          blocks=["evaluated", "delivered"]) from error

    def _work_check(self):
        try:
            self.work.tick()
        except ReachAdmissionError as error:
            self._numeric_error(error)

    def _invalidate(self):
        self._pending_reach_output = None
        self._pose_cache.clear()
        self._derived_pose_cache.clear()

    def _pose_slot(self, path, signature, build):
        """Reuse only a numerically identical node within the bounded work cache.

        Each path has one replaceable slot, not one retained entry per sample.
        The signature retains its private parent value and complete local
        operands, so neither object-id reuse nor a changed claim can hit it.
        Every lookup/insertion remains a charged request operation.
        """
        # A complete traversal cannot retain one slot per source node when
        # the graph itself exceeds the cache. Such single-use entries evict
        # reusable arithmetic without helping the next traversal. Keep the
        # exact state/time graph cache and resolve every source node normally.
        root_slot = bool(signature) and signature[0] == "root"
        if len(self.model.objects) + len(self.model.sites) > self.work.max_cache_entries and not root_slot:
            self.work.charge("source_pose_cache_bypass")
            if type(path) is str:
                translated = self._translated_source_slot(signature, build)
                if translated is not None:
                    return translated
            return build()
        key = ("reach_source_pose", self.model.program_revision, path)
        old = self.work.lookup(key)
        if old is not None and old[0] == signature:
            return old[1]
        result = build()
        self.work.remember(key, (signature, result))
        return result

    def _translated_source_slot(self, signature, build):
        """Reuse an unchanged full source node under an even grid translation.

        This is a pure numerical slot shared by source occurrences. Topology,
        claims, current coordinates, and each public output are still resolved
        by the caller. Recording-only tuples and relative-tip transforms do
        not enter this helper.
        """
        from math import isfinite
        from .model import Pose
        from .reach_numeric import MAX_OPERAND_BITS
        from .reach_pose import BITS, PoseValue, RotationValue

        self.work.charge("source_relative_pose_domain")
        cap = self.work.max_operand_bits
        if cap != MAX_OPERAND_BITS:
            return None
        if len(signature) == 3 and signature[0] == "follow":
            kind, parent, local = signature
            extra = ()
        elif len(signature) == 7 and signature[0] == "joint":
            _, parent, joint_kind, axis, coordinate, slope, local = signature
            if joint_kind not in {"hinge", "slider", "rigid", "grip"}:
                return None
            if not (type(axis) is tuple and len(axis) == 3 and
                    all(type(value) is float and isfinite(value) for value in axis)):
                return None
            if joint_kind in {"hinge", "slider"}:
                if not (type(coordinate) is float and isfinite(coordinate) and type(slope) is Fraction):
                    return None
                self.work.guard(slope)
            elif coordinate is not None or slope is not None:
                return None
            kind, extra = "joint", (joint_kind, axis, coordinate, slope)
        elif len(signature) == 2 and type(signature[0]) is PoseValue:
            kind, (parent, local), extra = "site", signature, ()
        else:
            return None
        # These are the complete numerical operands read by the original
        # builders. Strict types prevent equal booleans/malformed vectors
        # from borrowing a proof for ordinary canonical source values.
        if not (type(parent) is PoseValue and parent._ops is self.pose_ops and
                type(parent.rotation) is RotationValue and
                type(local) is Pose and type(local.position) is tuple and len(local.position) == 3 and
                type(local.rotation) is tuple and len(local.rotation) == 4 and
                all(type(value) is float and isfinite(value) for value in (*local.position, *local.rotation))):
            return None
        vectors = (parent.exact_position, parent.exact_velocity, parent.exact_omega, parent.rotation.components)
        if not all(type(values) is tuple and len(values) == length and
                   all(type(value) is Fraction for value in values)
                   for values, length in zip(vectors, (3, 3, 3, 4))):
            return None
        if type(parent.position_error_m) is not Fraction or type(parent.rotation.error_rad) is not Fraction:
            return None
        frozen = parent.rotation.frozen_projection
        if frozen is not None and not (type(frozen) is tuple and len(frozen) == 4 and
                                      all(type(value) is float and isfinite(value) for value in frozen)):
            return None
        operands = (*parent.exact_position, *parent.exact_velocity, *parent.exact_omega,
                    *parent.rotation.components, parent.position_error_m, parent.rotation.error_rad)
        self.work.guard(*operands)
        # Nearest/even rounding commutes with an EVEN integer grid shift.
        # Keeping the low grid bit is necessary at exact halfway values.
        # Larger/ungrounded operands keep the ordinary source build, avoiding
        # new prospective subtraction widths near the arithmetic ceiling.
        if any(value.denominator & (value.denominator - 1) or
               value.denominator.bit_length() > BITS + 1 or
               abs(value.numerator).bit_length() > MAX_OPERAND_BITS // 4
               for value in parent.exact_position):
            return None
        parity = tuple(value.numerator & 1 if value.denominator.bit_length() == BITS + 1 else 0
                       for value in parent.exact_position)
        if max(parent.position_error_m.numerator.bit_length(),
               parent.position_error_m.denominator.bit_length()) > MAX_OPERAND_BITS // 4:
            return None
        # The inherited position allowance also enters each composition only
        # additively. Distinct translated mounts may have different such
        # allowances despite sharing every actual rotation/rate calculation.
        parent_shape = (parity, parent.rotation, parent.exact_velocity, parent.exact_omega)
        key = ("reach_source_translated_node", cap, kind, parent_shape,
               extra, local.position, local.rotation)
        cached = self.work.lookup(key)
        if self.work.max_operand_bits != cap:
            return None
        self.work.guard(*operands)
        if cached is None:
            result = build()
            if self.work.max_operand_bits != cap:
                return None
            if type(result) is not PoseValue:
                return result
            if any(max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_OPERAND_BITS // 4
                   for value in (*result.exact_position, result.position_error_m)):
                return result
            try:
                position_offset = tuple(Fraction(0) if value == origin else
                    exact(value, origin, "sub", self.work)
                    for value, origin in zip(result.exact_position, parent.exact_position))
                error_offset = (Fraction(0) if result.position_error_m == parent.position_error_m else
                    exact(result.position_error_m, parent.position_error_m, "sub", self.work))
            except ReachAdmissionError as error:
                if (error is self.work.callback_error or self.work.max_operand_bits == cap or
                        error.details.get("budget") != "numeric_operand_bits"):
                    raise
                return None
            if self.work.max_operand_bits != cap:
                return None
            self.work.remember(key, (parent.exact_position, parent.position_error_m,
                                     position_offset, error_offset, result))
            if self.work.max_operand_bits != cap:
                return None
            self.work.guard(*operands, *result.exact_position, *result.exact_velocity, *result.exact_omega,
                            *result.rotation.components, result.position_error_m, result.rotation.error_rad)
            return result
        origin, inherited_error, position_offset, error_offset, result = cached
        self.work.charge("source_relative_pose_reuse")
        if self.work.max_operand_bits != cap:
            return None
        self.work.guard(*origin, inherited_error, *position_offset, error_offset,
                        *result.exact_position, *result.exact_velocity, *result.exact_omega,
                        *result.rotation.components, result.position_error_m, result.rotation.error_rad)
        if parent.exact_position == origin and parent.position_error_m == inherited_error:
            return result
        try:
            translated = tuple(value if current == previous else
                current if not offset else offset if not current else exact(current, offset, "add", self.work)
                for value, current, previous, offset in
                zip(result.exact_position, parent.exact_position, origin, position_offset))
            position_error = (result.position_error_m if parent.position_error_m == inherited_error else
                parent.position_error_m if not error_offset else error_offset if not parent.position_error_m else
                exact(parent.position_error_m, error_offset, "add", self.work))
        except ReachAdmissionError as error:
            if (error is self.work.callback_error or self.work.max_operand_bits == cap or
                    error.details.get("budget") != "numeric_operand_bits"):
                raise
            return None
        if self.work.max_operand_bits != cap:
            return None
        self.work.guard(*translated, position_error)
        # Position is occurrence-specific. All other immutable projections
        # belong to the same exact rotation and spatial rates in this key.
        projection = {name: value for name, value in result._projection.items() if name != "position"}
        occurrence = PoseValue(translated, result.rotation, result.exact_velocity, result.exact_omega,
                               position_error, self.pose_ops, projection)
        self.pose_ops._carry_finite_proof(result, occurrence)
        return occurrence

    def _constant_pose(self, value, *, inverse=False):
        key = ("reach_source_constant_pose", inverse, value.position, value.rotation)
        result = self.work.lookup(key)
        if result is None:
            result = (self.pose_ops.inverse_pose(value) if inverse else self.pose_ops.constant_pose(value))
            self.work.remember(key, result)
        return result

    def _incoming(self, state):
        # Only grip activity can change this finite profile's relation graph.
        # A cached mapping is immutable and shares the same bounded work cache.
        self.work.charge("source_topology_key", len(state.active_grips) + 1)
        key = ("reach_source_topology", self.model.program_revision, frozenset(state.active_grips))
        result = self.work.lookup(key)
        if result is None:
            result = MappingProxyType(super()._incoming(state))
            self.work.remember(key, result)
        return result

    def _register_spin_plan(self, omega, plan):
        key = ("reach_source_spin_phase", tuple(omega))
        old = self.work.lookup(key)
        if old is None or plan.max_elapsed_s > old.max_elapsed_s:
            self.work.remember(key, plan)

    def _advance_orientation(self, initial, omega, elapsed, *,
                             recording_context=None, recording_path=None,
                             recording_pose_ops=None):
        ops = self.pose_ops if recording_pose_ops is None else recording_pose_ops
        if recording_pose_ops is not None and (recording_context is None
                or getattr(ops, "source_ops", None) is not self.pose_ops or ops.work is not self.work):
            raise ValueError("Alternate spin recording requires this source's recording-only work context.")
        plan = self.work.lookup(("reach_source_spin_phase", tuple(omega)))
        if plan is not None and abs(elapsed) > plan.max_elapsed_s:
            plan = None
        if recording_context is not None:
            from .scene import MAX_KEYFRAMES
            return ops.recording_advance_orientation(initial, omega, elapsed,
                context=recording_context, path=recording_path, max_steps=MAX_KEYFRAMES,
                phase_plan=plan)
        return self.pose_ops.advance_orientation(initial, omega, elapsed, phase_plan=plan)

    def phase_bounds(self, start, end, state=None):
        try:
            return phase_bounds(self, start, end, state)
        except ReachAdmissionError as error:
            self._numeric_error(error, time=Fraction(start))

    def _anchor_bound(self, path, time, state):
        return phase_bounds(self, time, time, state, selected_frames=[path + ".frame"])["objects"][path]

    @staticmethod
    def _anchor_error(bound):
        return AnchorError(bound.position_error_m, bound.rotation_error_rad,
                           bound.velocity_error_m_per_s, bound.angular_velocity_error_rad_per_s)

    def _ideal_coordinate(self, path, time, state):
        return joint_phase(self, path, time, time, state).ideal_start

    def _ideal_position(self, path, time, state):
        claimant = state.claims.get((path, "translation"))
        if claimant is None:
            return state.ideal_positions[path]
        action, runtime = self.model.actions[claimant], state.actions[claimant]
        return self.pose_ops.affine(runtime.ideal_initial, action.vector, runtime.elapsed_at(time))

    def ordinary_target(self, path, time):
        """Project an ordinary action's target through the same 0.6 arithmetic."""
        action, runtime = self.model.actions[path], self.state.actions[path]
        try:
            key = ("reach_ordinary_target", self.model.program_revision, path,
                   runtime.initial, runtime.initial_rotation)
            cached = self.work.lookup(key)
            if cached is not None:
                return cached
            if action.kind == "move":
                values = self.pose_ops.affine(runtime.initial, action.vector, action.duration)
                # The exact midpoint above maximum finite binary64 rounds to
                # infinity under nearest-even. Keep the inherited unavailable
                # target projection without hiding other numeric/work failures.
                overflow = Fraction((1 << 1024) - (1 << 970))
                arithmetic = PhaseArithmetic(self.work)
                if any(compare(arithmetic.absolute(value), overflow, self.work) >= 0 for value in values):
                    raise _NumericFault("The ordinary action target exceeds finite binary64.")
                result = tuple(round_binary64(value, work=self.work) for value in values)
            elif action.kind == "spin":
                rotation = self._advance_orientation(runtime.initial_rotation or runtime.initial,
                                                     action.vector, action.duration)
                result = self.pose_ops.make(orientation=rotation).orientation
            else:
                raise ValueError("An ordinary target projection requires move or spin.")
            self.work.remember(key, result)
            return result
        except ReachAdmissionError as error:
            self._numeric_error(error, action=action, time=time)

    def _pair(self, path, time, state, *, recording=False):
        runtime, action = state.actions[path], self.model.actions[path]
        self._check()
        key = (runtime.initial, runtime.solution.target_rad, self.model.actions[path].duration,
               runtime.elapsed_at(time), runtime.status == "running")
        if recording:
            key = ("recording", self.work.max_operand_bits, *key)
        if key not in self._pair_cache:
            if len(self._pair_cache) >= 256:
                self._pair_cache.clear()
            sampler = recording_pair if recording else sample_pair
            self._pair_cache[key] = sampler(runtime.initial, runtime.solution.target_rad,
                action.duration, runtime.elapsed_at(time), running=runtime.status == "running", work=self.work)
        return self._pair_cache[key]

    def _coordinate(self, path, time, state, *, recording=False):
        claimant = state.claims.get((path, "coordinate"))
        if claimant is None:
            return state.coordinates[path], 0.0
        action = self.model.actions[claimant]
        if action.kind != "reach_planar":
            runtime = state.actions[claimant]
            elapsed = runtime.elapsed_at(time)
            arithmetic = PhaseArithmetic(self.work)
            initial, target = arithmetic.number(runtime.initial), arithmetic.number(action.goal)
            difference = arithmetic.sub(target, initial)
            value = (action.goal if elapsed == action.duration else round_binary64(arithmetic.add(initial,
                arithmetic.div(arithmetic.mul(difference, elapsed), action.duration)), work=self.work))
            rate = (round_binary64(arithmetic.div(difference, action.duration), work=self.work)
                    if runtime.status == "running" else 0.0)
            return value, rate
        index = 0 if path == action.reach.shoulder else 1
        pair = self._pair(claimant, time, state, recording=recording)
        return pair.coordinates_rad[index], pair.rates_rad_s[index]

    def _exact_coordinate(self, path, time, state):
        coordinate, rate = self._coordinate(path, time, state)
        claimant = state.claims.get((path, "coordinate"))
        if claimant is None:
            return coordinate, Fraction(0), Fraction(coordinate)
        action, runtime = self.model.actions[claimant], state.actions[claimant]
        if action.kind == "reach_planar":
            index = 0 if path == action.reach.shoulder else 1
            pair = self._pair(claimant, time, state)
            return coordinate, pair.exact_slopes[index], pair.exact_coordinates[index]
        arithmetic = PhaseArithmetic(self.work)
        slope = arithmetic.div(arithmetic.sub(arithmetic.number(action.goal),
                                             arithmetic.number(runtime.initial)), action.duration)
        ideal = arithmetic.add(arithmetic.number(runtime.initial),
                               arithmetic.mul(slope, runtime.elapsed_at(time)))
        return coordinate, slope if runtime.status == "running" else Fraction(0), ideal

    def _dynamic_kinematics(self, path, time, state, *, pose_only=False,
                            recording_context=None):
        self._check()
        if recording_context is not None and not pose_only:
            raise ValueError("A recording rotation cursor cannot provide source rates.")
        anchor = state.dynamic[path]
        initial = anchor.state
        elapsed = time - anchor.time
        acceleration = self._acceleration(path, state)
        rotation = initial.rotation if hasattr(initial, "rotation") else initial.orientation
        position = self.pose_ops.parabolic(initial.position, initial.velocity, acceleration, elapsed)
        orientation = self._advance_orientation(rotation, initial.omega, elapsed,
            recording_context=recording_context, recording_path="dynamic:" + path)
        if recording_context is not None:
            return self.pose_ops.make_recording(position=position, orientation=orientation)
        return self.pose_ops.make(
            position=position, orientation=orientation,
            velocity=POSE_ZERO if pose_only else self.pose_ops.affine(initial.velocity, acceleration, elapsed),
            omega=POSE_ZERO if pose_only else initial.omega)

    def _kinematics(self, time, state):
        result = self._resolve_kinematics(time, state)
        context = self._terminal_pose_context
        if context is not None and context.incoming_state is state and context.time == time:
            context.frames = result[1]
        return result

    def _pose_cache_time(self, time, state):
        self.work.charge("source_pose_time_key")
        return None if not state.dynamic and not state.claims else time

    def _check_object_pose(self, pose):
        """Validate every ordinary object's actual public components."""
        pose.position, pose.orientation, pose.velocity, pose.omega

    def recording_frames(self, time, state, selected_paths, *, moving_frames=None,
                          recording_context=None, recording_angular_proof=None,
                          recording_pose_ops=None):
        """Sample p/q from a validated phase without constructing unused rates.

        The recording planner must first validate the complete requested prefix
        and derive its whole-phase bounds. This method neither advances events
        nor substitutes partial output for a complete source observation. Its
        private derivative-free graph cannot enter the full-kinematics cache.
        A phase movement classification only avoids caching changing nodes;
        current dependencies and exact local operands are still resolved.
        An optional opaque phase context enables bounded angular recurrence
        only for recording endpoints. Its numerical cursors belong to the
        existing work cache; ordinary source poses and anchors remain direct.
        An optional immutable angular proof permits complete carrier cursors
        only after this traversal checks its current chained source witnesses.
        """
        selected = []
        seen = set()
        try:
            for path in selected_paths:
                self._check()
                if not isinstance(path, str) or (path != "world" and (
                        not path.endswith(".frame") or
                        path[:-6] not in self.model.objects and path[:-6] not in self.model.sites)):
                    raise ValueError("A recording selector must name an actual source frame.")
                if path not in seen:
                    seen.add(path)
                    selected.append(path)
            _, frames = self._resolve_kinematics(time, state, selected_frames=selected,
                                               pose_only=True, recording_only=True,
                                               recording_moving_frames=moving_frames,
                                               recording_context=recording_context,
                                               recording_angular_proof=recording_angular_proof,
                                               recording_pose_ops=recording_pose_ops)
            result = {}
            for path in selected:
                self._check()
                result[path] = RecordingPose(frames[path].position, frames[path].orientation)
            return result
        except ReachAdmissionError as error:
            self._numeric_error(error, time=time)

    def recording_moving_frames(self, state, selected_paths):
        """Identify tracks that may change inside one validated source phase.

        This is a dependency walk over actual source laws, with no numerical
        output cache. Paused/unclaimed coordinates and roots are constant until
        the next boundary. A running affine law with identical exact endpoints
        or a zero move/spin vector is also constant. Dynamic roots remain
        conservatively moving even when an instantaneous rate is zero.
        The recording caller must derive this again whenever its state changes.
        """
        incoming = self._incoming(state)
        objects, frames, resolving = {}, {"world": False}, set()

        def running(path, component):
            self._check()
            claimant = state.claims.get((path, component))
            if claimant is None or state.actions[claimant].status != "running":
                return False
            action, runtime = self.model.actions[claimant], state.actions[claimant]
            self.work.charge("recording_constant_law_check")
            if component == "coordinate":
                arithmetic = PhaseArithmetic(self.work)
                if action.kind == "reach_planar":
                    index = 0 if path == action.reach.shoulder else 1
                    initial = arithmetic.number(runtime.initial[index])
                    target = arithmetic.number(runtime.solution.target_rad[index])
                else:
                    initial, target = arithmetic.number(runtime.initial), arithmetic.number(action.goal)
                return initial != target
            return any(self.pose_ops._vector(action.vector))

        def frame(path):
            self._check()
            if not isinstance(path, str) or (path != "world" and (
                    not path.endswith(".frame") or path[:-6] not in self.model.objects
                    and path[:-6] not in self.model.sites)):
                raise ValueError("A recording selector must name an actual source frame.")
            if path not in frames:
                stem = path[:-6]
                frames[path] = (instance(stem) if stem in self.model.objects
                                else instance(self.model.sites[stem].owner))
            return frames[path]

        def instance(path):
            self._check()
            if path in objects:
                return objects[path]
            if path in resolving:
                raise reach_error("reach_chain", "The active reach pose graph contains a cycle.",
                                  self.model.objects[path].span)
            resolving.add(path)
            if path in incoming:
                kind, relation = incoming[path]
                if kind == "follow":
                    moving = frame(self.model.follows[relation].parent)
                else:
                    joint = self.model.joints[relation]
                    inherited = frame(joint.parent + ".frame")
                    coordinate = (running(relation, "coordinate")
                                  if joint.kind in {"hinge", "slider"} else False)
                    moving = inherited or coordinate
            elif state.modes[path] == "dynamic":
                moving = True
            else:
                translation = running(path, "translation")
                orientation = running(path, "orientation")
                moving = translation or orientation
            resolving.remove(path)
            objects[path] = moving
            frames[path + ".frame"] = moving
            return moving

        return frozenset(path for path in selected_paths if frame(path))

    def _terminal_static_kinematics(self, time, state):
        """Reuse unchanged complete p/q after a natural-only static handoff.

        The transaction context survives only natural reach completions: every
        source event, ordinary latch, and changed dynamic aggregation clears
        it. A completed reach latches the same canonical coordinates that the
        incoming graph already used. If no claims or dynamics remain, every
        derivative is exactly zero; position, rotation, and their private
        allowances follow the identical arithmetic DAG. Rebuild the complete
        outgoing maps with fresh zero rates and no incoming rate projections.
        Already exposed p/q may retain their same-operand, same-domain receipt.

        This is one boundary's retained graph, not another numerical cache.
        All source identities and exact final coordinates are checked again;
        narrowed operand domains use the ordinary resolver instead.
        """
        from .reach_numeric import MAX_OPERAND_BITS
        from .reach_pose import PoseValue, RotationValue
        from math import isfinite

        context = self._terminal_pose_context
        work = self.work
        work.charge("source_terminal_static_context")

        def valid_context():
            return (work.max_operand_bits == MAX_OPERAND_BITS
                and context is self._terminal_pose_context and context is not None
                and context.time == time and context.staged_state is state
                and context.incoming_state is not state
                and not state.claims and not state.dynamic
                and not context.incoming_state.dynamic
                and type(context.frames) is dict
                and len(context.frames) == len(self.model.objects) + len(self.model.sites) + 1
                and state.active_grips == context.incoming_state.active_grips)

        if not valid_context():
            return None
        before = context.incoming_state
        incoming = self._incoming(state)

        def same_scalar(left, right):
            return (type(left) is type(right) and
                (left.hex() == right.hex() if type(left) is float else left == right))

        def same_vector(left, right, length):
            return (type(left) is type(right) is tuple and len(left) == len(right) == length
                and all(same_scalar(a, b) for a, b in zip(left, right)))

        def same_rotation(left, right):
            if left is None or right is None:
                return left is right
            return (type(left) is type(right) is RotationValue
                and same_vector(left.components, right.components, 4)
                and same_scalar(left.error_rad, right.error_rad)
                and (left.frozen_projection is right.frozen_projection is None
                    or same_vector(left.frozen_projection, right.frozen_projection, 4)))

        # Roots are the only objects whose stored p/q enter this static graph.
        # Connected objects still resolve through the unchanged finite topology.
        roots = {}
        for path in self.model.objects:
            work.charge("source_terminal_static_root_guard")
            if path in incoming:
                continue
            saved = (before.modes[path], before.positions[path], before.orientations[path],
                     before.root_rotation_values.get(path))
            if (state.modes[path] != saved[0]
                    or not same_vector(state.positions[path], saved[1], 3)
                    or not same_vector(state.orientations[path], saved[2], 4)
                    or not same_rotation(state.root_rotation_values.get(path), saved[3])):
                return None
            roots[path] = saved
        for channel, claimant in before.claims.items():
            work.charge("source_terminal_static_claim_guard")
            action, runtime = self.model.actions[claimant], before.actions[claimant]
            if (action.kind != "reach_planar" or channel[1] != "coordinate"
                    or channel[0] not in (action.reach.shoulder, action.reach.elbow)
                    or runtime.status != "running" or runtime.elapsed_at(time) != action.duration
                    or state.actions[claimant].status != "completed"):
                return None
        coordinates = {}
        for path, joint in self.model.joints.items():
            work.charge("source_terminal_static_coordinate_guard")
            if joint.kind in {"hinge", "slider"}:
                value = self._coordinate(path, time, before)[0]
                if not same_scalar(state.coordinates[path], value):
                    return None
                coordinates[path] = value

        objects, frames = {}, {}
        for path, pose in context.frames.items():
            work.charge("source_terminal_static_node")
            if not valid_context():
                return None
            if (type(pose) is not PoseValue or pose._ops is not self.pose_ops
                    or type(pose.rotation) is not RotationValue
                    or type(pose.position_error_m) is not Fraction
                    or type(pose.rotation.error_rad) is not Fraction):
                return None
            vectors = (pose.exact_position, pose.rotation.components,
                       pose.exact_velocity, pose.exact_omega)
            if any(type(vector) is not tuple or len(vector) != length
                    or any(type(value) is not Fraction for value in vector)
                    for vector, length in zip(vectors, (3, 4, 3, 3))):
                return None
            work.guard(*(value for vector in vectors for value in vector),
                       pose.position_error_m, pose.rotation.error_rad)
            value = PoseValue(pose.exact_position, pose.rotation, POSE_ZERO, POSE_ZERO,
                              pose.position_error_m, self.pose_ops)
            if (type(pose._projection) is dict and type(pose._projection_domains) is dict
                    and any(name in pose._projection for name in ("position", "orientation"))):
                work.charge("source_terminal_static_projections")
                if not valid_context():
                    return None
                # Copy only an existing immutable p/q exposure whose ordinary
                # _expose receipt names these identical private operands. The
                # new rates and their projections always start independently.
                # Re-read both plain maps after the cancellation checkpoint.
                if type(pose._projection) is dict and type(pose._projection_domains) is dict:
                    for name, length in (("position", 3), ("orientation", 4)):
                        operand = pose.exact_position if name == "position" else pose.rotation
                        domain = pose._projection_domains.get(name)
                        exposed = pose._projection.get(name)
                        if (type(domain) is tuple and len(domain) == 2
                                and type(domain[0]) is int and domain[0] == work.max_operand_bits
                                and domain[1] is operand and type(exposed) is tuple and len(exposed) == length
                                and all(type(part) is float and isfinite(part) for part in exposed)):
                            value._projection[name] = exposed
                            value._projection_domains[name] = domain
            if path == "world":
                frames[path] = self._identity_pose
                self.pose_ops.ensure_finite(frames[path])
            elif path.endswith(".frame") and path[:-6] in self.model.objects:
                self._check_object_pose(value)
                objects[path[:-6]] = frames[path] = value
            elif path.endswith(".frame") and path[:-6] in self.model.sites:
                self.pose_ops.ensure_finite(value)
                frames[path] = value
            else:
                return None

        # Precharge the final source checks, then inspect their actual values
        # without another callback between those checks and publication. A
        # cancelled callback or changed live domain cannot publish a prefix.
        work.charge("source_terminal_static_final_guard", len(roots) + len(coordinates) + 1)
        if not valid_context() or len(objects) != len(self.model.objects):
            return None
        for path, saved in roots.items():
            if (state.modes[path] != saved[0]
                    or not same_vector(state.positions[path], saved[1], 3)
                    or not same_vector(state.orientations[path], saved[2], 4)
                    or not same_rotation(state.root_rotation_values.get(path), saved[3])):
                return None
        if any(not same_scalar(state.coordinates[path], value) for path, value in coordinates.items()):
            return None
        return objects, frames

    def _resolve_kinematics(self, time, state, *, selected_frames=None, pose_only=False,
                            recording_only=False, recording_moving_frames=None,
                            recording_context=None, recording_angular_proof=None,
                            recording_pose_ops=None):
        """Resolve the actual pose graph without intermediate float exposure.

        This separate 0.6 path leaves every older profile's pose arithmetic
        unchanged. Only public sample/anchor components materialize binary64.
        """
        if recording_only and not pose_only:
            raise ValueError("A recording transform graph cannot provide full source kinematics.")
        if recording_context is not None and not recording_only:
            raise ValueError("A recording rotation cursor cannot enter full source kinematics.")
        if recording_pose_ops is not None and (not recording_only or recording_context is None
                or getattr(recording_pose_ops, "source_ops", None) is not self.pose_ops
                or recording_pose_ops.work is not self.work
                or recording_angular_proof is not None and
                   getattr(recording_pose_ops, "recording_body_cursors", False) is not True):
            raise ValueError("Alternate recording arithmetic requires this source's recording-only work context.")
        # With neither a free trajectory nor a motion claim, all actual pose
        # operands belong to this current state rather than a clock.
        # Event/force transitions still invalidate the single complete graph.
        key = (id(state), self._pose_cache_time(time, state))
        cached = self._pose_cache.get(key) if not pose_only and selected_frames is None else None
        if cached is not None and cached[0] is state:
            self._check()
            return cached[1], cached[2]
        context = self._terminal_pose_context
        if (not pose_only and selected_frames is None and context is not None
                and context.staged_state is state):
            terminal = self._terminal_static_kinematics(time, state)
            if terminal is not None:
                objects, frames = terminal
                self._pose_cache = {key: (state, objects, frames)}
                return objects, frames
        ops = self.pose_ops if recording_pose_ops is None else recording_pose_ops
        compose = (ops.compose_recording_fast if recording_context is not None else
                   ops.compose_recording if recording_only else ops.compose)
        def constant_pose(pose, *, inverse=False):
            if recording_pose_ops is not None:
                return ops.recording_constant_pose(pose, inverse=inverse, build=self._constant_pose)
            return self._constant_pose(pose, inverse=inverse)
        incoming = self._incoming(state)
        objects, frames, resolving = {}, {"world": self._identity_pose}, set()
        angular_proof = None
        valid_angular_frames = set()
        resolving_angular_frames = set()
        angular_receipts = {}
        orientation_recipes, shared_orientation_frames = {}, {}
        share_orientations = (recording_pose_ops is not None
            and getattr(ops, "share_arithmetic", False) is True)
        source_model, source_state, source_root_state = self.model, state, self.state
        if recording_angular_proof is not None:
            from .reach_numeric import rational
            from .reach_phase import (_AxialRate, RecordingAngularFrame, RecordingAngularProof,
                                      current_recording_angular_witness,
                                      _current_recording_angular_witness,
                                      _recording_orientation_recipe)
            self.work.charge("recording_body_proof_domain")
            if (recording_context is None or
                    type(recording_angular_proof) is not RecordingAngularProof):
                raise ValueError("A carrier rotation proof belongs to a recorded phase.")
            proof = recording_angular_proof
            if (self.work.max_operand_bits == 32768 and
                    proof.program_revision == self.model.program_revision and
                    type(proof.frames) is MappingProxyType and
                    type(proof.start) is Fraction and type(proof.end) is Fraction):
                proof_time = rational(time, self.work)
                self.work.guard(proof.start, proof.end)
                if (compare(proof.start, proof_time, self.work) <= 0 and
                        compare(proof_time, proof.end, self.work) <= 0):
                    angular_proof = proof

        def angular_frame(frame_path, kind, source_path):
            """Validate one current law and its already visited parent proof.

            This set stores only structural validity for the current graph
            traversal. Numeric cursor state remains in the shared bounded LRU.
            A changed source operand, authority or topology uses the ordinary
            sampler; neither state identity nor a prior-clock pose is proof.
            """
            if angular_proof is None:
                return None
            if frame_path in valid_angular_frames:
                return angular_proof.frames[frame_path]
            if frame_path in resolving_angular_frames:
                return None
            self.work.charge("recording_body_witness")
            record = angular_proof.frames.get(frame_path)
            if (self.work.max_operand_bits != 32768 or
                    type(record) is not RecordingAngularFrame or
                    type(record.trig_count) is not int or record.trig_count < 0 or
                    type(record.rate) is not _AxialRate or
                    type(record.rate.value) is not Fraction or
                    (record.rate.value and not record.trig_count)):
                return None
            self.work.guard(record.rate.value, record.trig_count)
            current = current_recording_angular_witness(
                self.model, state, kind, source_path, work=self.work)
            if (self.work.max_operand_bits != 32768 or
                    current != (record.parent, record.witness)):
                return None
            if record.parent is not None and record.parent not in valid_angular_frames:
                resolving_angular_frames.add(frame_path)
                try:
                    parent_record = ensure_angular_frame(record.parent)
                finally:
                    resolving_angular_frames.remove(frame_path)
                if parent_record is None or self.work.max_operand_bits != 32768:
                    return None
            valid_angular_frames.add(frame_path)
            angular_receipts[frame_path] = (kind, source_path, record,
                angular_receipts.get(record.parent) if record.parent is not None else None)
            if share_orientations:
                recipe = _recording_orientation_recipe(record,
                    orientation_recipes.get(record.parent), work=self.work)
                if recipe is not None:
                    orientation_recipes[frame_path] = recipe
            return record

        def ensure_angular_frame(frame_path):
            # Only a candidate complete carrier needs these witnesses. Walk
            # its actual current ancestry; unrelated selected leaves do not
            # produce or reuse a body cursor and need no optional proof.
            if frame_path == "world":
                return angular_frame(frame_path, "world", "world")
            if type(frame_path) is not str or not frame_path.endswith(".frame"):
                return None
            stem = frame_path.removesuffix(".frame")
            if stem in self.model.objects:
                relation = incoming.get(stem)
                return (angular_frame(frame_path, "root", stem) if relation is None else
                        angular_frame(frame_path, relation[0], relation[1]))
            if stem in self.model.sites:
                return angular_frame(frame_path, "site", stem)
            return None

        def slot(path, signature, build, *, owner=None):
            if recording_only and recording_moving_frames is not None:
                # Changing nodes already have same-clock sharing in objects /
                # frames below. Their previous-clock path slot is otherwise a
                # one-use numeric result that displaces reusable arithmetic.
                # A site's movement follows its actual owner. Every dependency
                # and local signature above this cache policy remains fresh;
                # incomplete hints merely retain the ordinary bounded lookup.
                frame_path = path if owner is not None else path + ".frame"
                if (frame_path in recording_moving_frames or
                        owner is not None and owner + ".frame" in recording_moving_frames):
                    self.work.charge("recording_moving_pose")
                    return build()
            namespace = "recorded_transform" if recording_only else "recording"
            if recording_pose_ops is not None:
                namespace = recording_pose_ops.recording_namespace
            identity = (namespace, path) if pose_only else path
            if recording_context is not None:
                # An incremental rotation can differ privately from another
                # pass's direct seed at the same coordinate. Reuse never
                # carries that approximation across a fresh phase context.
                identity = (*identity, recording_context)
            return self._pose_slot(identity, signature, build)

        def frame(path):
            if path not in frames:
                stem = path.removesuffix(".frame")
                if stem in self.model.objects:
                    frames[path] = instance(stem)
                else:
                    site = self.model.sites[stem]
                    owner = instance(site.owner)
                    frames[path] = slot(path, (owner, site.pose),
                        lambda: compose(owner, constant_pose(site.pose)), owner=site.owner)
            return frames[path]

        def instance(path):
            if path in objects:
                return objects[path]
            self._check()
            if path in resolving:
                raise reach_error("reach_chain", "The active reach pose graph contains a cycle.",
                                  self.model.objects[path].span)
            resolving.add(path)
            if path in incoming:
                kind, relation_path = incoming[path]
                if kind == "follow":
                    follow = self.model.follows[relation_path]
                    parent = frame(follow.parent)
                    result = slot(path, ("follow", parent, follow.offset),
                        lambda: compose(parent, constant_pose(follow.offset)))
                else:
                    joint = self.model.joints[relation_path]
                    parent = frame(joint.parent + ".frame")
                    child_pose = self.model.sites[joint.child].pose
                    eligible_body = (joint.kind == "hinge" and
                        (recording_pose_ops is None or ops.recording_body_hinges is None
                         or relation_path in ops.recording_body_hinges))
                    record = ensure_angular_frame(path + ".frame") if eligible_body else None
                    body_cursor = False
                    if record is not None:
                        native_zero = (ops.recording_zero_child_origin(child_pose.position)
                            if recording_pose_ops is not None else None)
                        if native_zero is None:
                            child_position = ops._recording_vector(child_pose.position)
                            self.work.charge("recording_body_child_origin")
                            body_cursor = (not any(child_position) and
                                           self.work.max_operand_bits == 32768)
                        else:
                            body_cursor = native_zero
                    coordinate, slope = None, None
                    if joint.kind in {"hinge", "slider"} and not body_cursor:
                        if pose_only:
                            coordinate = (ops.recording_coordinate(self, relation_path, time, state)
                                if recording_pose_ops is not None and joint.kind == "hinge" else
                                self._coordinate(relation_path, time, state,
                                    recording=recording_context is not None)[0])
                            slope = Fraction(0)
                        else:
                            coordinate, slope, _ = self._exact_coordinate(relation_path, time, state)
                    def connected():
                        relative = self._identity_pose
                        if joint.kind == "hinge":
                            if recording_context is not None:
                                from .scene import MAX_KEYFRAMES
                                relative = ops.make_recording(orientation=ops.recording_axis_rotation(
                                    joint.axis, coordinate, context=recording_context,
                                    path="hinge:" + relation_path, max_steps=MAX_KEYFRAMES))
                            else:
                                relative = (ops.hinge_recording(joint.axis, coordinate) if recording_only
                                            else ops.hinge_pose(joint.axis, coordinate, slope))
                        elif joint.kind == "slider":
                            position = ops.scale(joint.axis, Fraction(coordinate))
                            relative = (ops.make_recording(position=position) if recording_only
                                        else ops.make(position=position,
                                                      velocity=ops.scale(joint.axis, slope)))
                        return compose(compose(parent, relative),
                                       constant_pose(child_pose, inverse=True))
                    if body_cursor:
                        from .scene import MAX_KEYFRAMES
                        receipt = angular_receipts[path + ".frame"]
                        source_records = 0
                        current_receipt = receipt
                        while current_receipt is not None:
                            source_records += 1
                            current_receipt = current_receipt[3]
                        def source_admission():
                            # Each record's check is precharged by the cursor.
                            # This entire final read has no callback between
                            # an ancestor comparison and cache publication.
                            if (self.model is not source_model or self.state is not source_root_state
                                    or state is not source_state
                                    or self.model.program_revision != angular_proof.program_revision):
                                raise ReachAdmissionError("reach_domain", "The carrier source context changed during sampling.")
                            current_receipt = receipt
                            while current_receipt is not None:
                                kind, source_path, expected, current_receipt = current_receipt
                                current = _current_recording_angular_witness(
                                    source_model, source_state, kind, source_path, work=self.work)
                                if current != (expected.parent, expected.witness):
                                    raise ReachAdmissionError("reach_domain", "The carrier source witness changed during sampling.")
                            return True
                        def direct_seed():
                            # The exact source kernels consume the same frozen
                            # operands as this admitted body proof. A callback
                            # cannot substitute a temporary live-source value
                            # into a seed published under the old proof token.
                            from .reach_recording_fast import captured_recording_orientation
                            return captured_recording_orientation(
                                self.pose_ops, angular_proof, path + ".frame", time)
                        recipe = orientation_recipes.get(path + ".frame")
                        if recipe is not None:
                            recipe = (angular_proof.start, angular_proof.end, recipe)
                        representative = (shared_orientation_frames.get(recipe)
                            if recipe is not None else None)
                        if representative is None:
                            rotation = ops.recording_body_orientation(direct_seed,
                                record.rate.axis, record.rate.value, time,
                                phase_start=angular_proof.start, phase_end=angular_proof.end,
                                context=recording_context, path="carrier:" + path,
                                proof_token=record.token, max_steps=MAX_KEYFRAMES,
                                source_admission=source_admission, source_records=source_records)
                        else:
                            # This index refers only to an already required
                            # pose in this same graph/clock/phase. No second
                            # numerical cache or cursor is retained. Equality
                            # binds the complete frozen orientation law, not
                            # an exposed quaternion or instantaneous rate.
                            self.work.charge("recording_body_shared_orientation")
                            ops._require_domain()
                            rotation = frames[representative].rotation
                            self.work.charge("recording_angular_witness_guard", source_records)
                            ops._require_domain()
                            source_admission()
                            ops._rotation_domain(rotation)
                        # With a zero child-site offset, the hinge and inverse
                        # child-site rotations do not move the parent's origin.
                        # Repeated identical 96-bit grid projections are
                        # idempotent; retain the original final position grid.
                        result = (ops.recording_parent_origin(parent, rotation)
                            if recording_pose_ops is not None else ops.make_recording(
                                position=ops._rounded_vector(parent.exact_position),
                                orientation=rotation))
                        if recipe is not None:
                            shared_orientation_frames.setdefault(recipe, path + ".frame")
                    else:
                        result = slot(path,
                            ("joint", parent, joint.kind, joint.axis, coordinate, slope, child_pose), connected)
            elif state.modes[path] == "dynamic":
                result = (ops.recording_dynamic_pose(self, path, time, state, context=recording_context)
                    if recording_pose_ops is not None else
                    self._dynamic_kinematics(path, time, state, pose_only=pose_only,
                                             recording_context=recording_context))
            else:
                position = state.positions[path]
                rotation = state.root_rotation_values.get(path, state.orientations[path])
                # These are exact private derivative operands. The inherited
                # evaluator's binary64 ZERO would needlessly decode a fresh
                # tuple and repeat its domain checks down every composition.
                velocity, omega = POSE_ZERO, POSE_ZERO
                claimant = state.claims.get((path, "translation"))
                if claimant is not None:
                    action, runtime = self.model.actions[claimant], state.actions[claimant]
                    affine = ops.recording_affine if recording_context is not None else ops.affine
                    position = affine(runtime.initial, action.vector, runtime.elapsed_at(time))
                    if runtime.status == "running" and not pose_only:
                        velocity = action.vector
                claimant = state.claims.get((path, "orientation"))
                if claimant is not None:
                    action, runtime = self.model.actions[claimant], state.actions[claimant]
                    rotation = self._advance_orientation(runtime.initial_rotation or runtime.initial,
                        action.vector, runtime.elapsed_at(time), recording_context=recording_context,
                        recording_path=("prescribed:" + path if recording_pose_ops is None else
                                        recording_pose_ops.recording_namespace + ":prescribed:" + path),
                        recording_pose_ops=recording_pose_ops)
                    if runtime.status == "running" and not pose_only:
                        omega = action.vector
                result = slot(path, ("root", position, rotation, velocity, omega),
                    lambda: (ops.make_recording(position=position, orientation=rotation) if recording_only
                             else ops.make(position=position, orientation=rotation,
                                           velocity=velocity, omega=omega)))
            resolving.remove(path)
            # This is an explicit finiteness check; opaque internals continue
            # down the graph even after canonical components are cached.
            if not pose_only:
                self._check_object_pose(result)
            objects[path] = result
            frames[path + ".frame"] = result
            return result

        if selected_frames is None:
            for path in self.model.objects:
                instance(path)
            for path in self.model.sites:
                self._check()
                frame(path + ".frame")
        else:
            for path in selected_frames:
                frame(path)
        if not pose_only and selected_frames is None:
            self._pose_cache = {key: (state, objects, frames)}
        return objects, frames

    def _tip_base(self, action, time, state, *, terminal=False):
        from .reach_pose import PoseValue, RotationValue

        payload = action.reach
        ops = self.pose_ops
        while True:
            cap = self.work.max_operand_bits
            self._check()
            if self.work.max_operand_bits != cap:
                continue
            key = (id(state), self._pose_cache_time(time, state), "tip", payload.base_frame, payload.tip, cap)
            if key in self._derived_pose_cache:
                return self._derived_pose_cache[key]
            context = self._terminal_pose_context
            same_pose = (context is not None and context.time == time and
                         context.staged_state is state and context.frames is not None)
            tip_key = (payload.base_frame, payload.tip, cap)
            self.work.charge("source_terminal_pose_guard")
            if self.work.max_operand_bits != cap:
                continue
            if same_pose and tip_key in context.tips:
                result = context.tips[tip_key]
                if len(self._derived_pose_cache) < 256:
                    self.work.charge("source_terminal_pose_publish")
                    if self.work.max_operand_bits != cap:
                        continue
                    self._derived_pose_cache[key] = result
                return result
            # A terminal record exposes only p/q along the complete dependency
            # paths of its base and tip. Its unused rates need not be constructed.
            # The boundary transaction still checks the complete incoming graph and
            # the final staged graph. Partial maps never enter the full graph cache.
            if same_pose:
                # Natural reach latching preserves canonical p/q even when its
                # incoming rates are nonzero. These frames are never reused as
                # the staged full graph or as outgoing derivative values.
                frames = context.frames
            elif terminal:
                _, frames = self._resolve_kinematics(time, state,
                    selected_frames=(payload.base_frame, payload.tip + ".frame"), pose_only=True)
            else:
                _, frames = self._kinematics(time, state)
            base, tip = frames[payload.base_frame], frames[payload.tip + ".frame"]
            self.work.charge("source_relative_pose_operands")
            private = all(type(value) is PoseValue and type(value.exact_position) is tuple
                          and len(value.exact_position) == 3
                          and all(type(part) is Fraction for part in value.exact_position)
                          and type(value.rotation) is RotationValue
                          and type(value.rotation.components) is tuple and len(value.rotation.components) == 4
                          and all(type(part) is Fraction for part in value.rotation.components)
                          and type(value.rotation.error_rad) is Fraction for value in (base, tip))
            if private:
                self.work.guard(*base.exact_position, *tip.exact_position,
                    *base.rotation.components, base.rotation.error_rad,
                    *tip.rotation.components, tip.rotation.error_rad)
                difference = tuple(exact(a, b, "sub", self.work)
                                   for a, b in zip(tip.exact_position, base.exact_position))
                if self.work.max_operand_bits != cap:
                    continue
                # World translation cancels before rotation. Repeated independent
                # arms can share this exact arithmetic without sharing identities,
                # lifecycle state, observations or a larger numerical cache.
                numeric_key = ("reach_relative_tip_pose", cap, difference, base.rotation, tip.rotation)
                result = self.work.lookup(numeric_key)
                if self.work.max_operand_bits != cap:
                    continue
                if result is None:
                    inverse = ops.inverse_rotation(base.rotation)
                    rotation = ops.multiply(inverse, tip.rotation)
                    result = ops.make(position=ops.rotate(inverse, difference), orientation=rotation)
                    if self.work.max_operand_bits != cap:
                        continue
                    self.work.remember(numeric_key, result)
            else:
                # Unrecognized private shapes retain the ordinary helper's
                # coercion/domain behavior and cannot borrow a pure result.
                rotation = ops.multiply(ops.inverse_rotation(base.rotation), tip.rotation)
                result = ops.make(position=ops.relative_point(base, tip), orientation=rotation)
            if self.work.max_operand_bits != cap:
                continue
            if same_pose and len(context.tips) < 256:
                self.work.charge("source_terminal_pose_remember")
                if self.work.max_operand_bits != cap:
                    continue
                context.tips[tip_key] = result
            if len(self._derived_pose_cache) < 256:
                self._derived_pose_cache[key] = result
            return result

    def _world_target(self, payload, time, state, frames):
        # The public reach observation consumes only this canonical point.
        # Its position uses exactly compose's rotate/add/grid/projection path;
        # target orientation, velocity and their allowances are never required.
        from .reach_pose import RotationValue
        from .reach_numeric import MAX_OPERAND_BITS, float_bits, rational

        ops = self.pose_ops
        while True:
            cap = self.work.max_operand_bits
            self._check()
            base = frames[payload.base_frame]
            position = ops._vector(base.exact_position)
            raw_target = payload.target_m
            native_target = None
            if (cap == MAX_OPERAND_BITS and type(raw_target) is tuple and len(raw_target) == 3
                    and all(type(value) is float for value in raw_target)):
                # Retain the ordinary bounded vector admission. The actual
                # immutable bit patterns identify already completed decodes.
                self.work.charge("pose_vector_domain")
                if self.work.max_operand_bits != cap:
                    continue
                encoded = tuple(float_bits(value) for value in raw_target)
                if all(bits & 0x7FF0000000000000 != 0x7FF0000000000000 for bits in encoded):
                    self.work.guard_bits(1075)
                    native_target = ("canonical_binary64", encoded)
            target = None if native_target is not None else ops._vector(raw_target)
            rotation = ops._rotation(base.rotation)
            self.work.charge("source_world_target_rotation")
            if not (type(rotation) is RotationValue and type(rotation.components) is tuple
                    and len(rotation.components) == 4
                    and all(type(value) is Fraction for value in rotation.components)
                    and any(rotation.components) and type(rotation.error_rad) is Fraction):
                raise ReachAdmissionError("reach_numeric", "An observed target requires a private source rotation.")
            self.work.guard(*rotation.components, rotation.error_rad)
            if self.work.max_operand_bits != cap:
                continue
            if cap == MAX_OPERAND_BITS:
                # An outer translation changes only the corresponding scalar
                # additions and projections. Retain one complete last point
                # with the shared rotation/target in the existing numeric LRU.
                # Every unchanged component has identical original operands;
                # changed components use the original exact add/grid kernels.
                key = ("reach_world_target_point", cap, "translated_components", rotation,
                       native_target if native_target is not None else target)
                saved = self.work.lookup(key)
                if self.work.max_operand_bits != cap:
                    continue
                if native_target is not None:
                    if (type(saved) is _WorldTargetComponents and type(saved.target) is tuple
                            and len(saved.target) == 3 and all(type(value) is Fraction for value in saved.target)):
                        target = saved.target
                    else:
                        # The dimensions/types were admitted above. These are
                        # precisely the ordinary _vector scalar decodes.
                        target = tuple(rational(value, self.work) for value in raw_target)
                        saved = None
                    if self.work.max_operand_bits != cap:
                        continue
                if type(saved) is _WorldTargetComponents:
                    self.work.charge("source_world_target_components")
                    if self.work.max_operand_bits != cap:
                        continue
                    self.work.guard(*position, *target, *rotation.components, rotation.error_rad,
                                    *saved.offset, *saved.position, *saved.rounded)
                    if self.work.max_operand_bits != cap:
                        continue
                    if position == saved.position:
                        return saved.point
                    actual, projected = list(saved.rounded), list(saved.point.position)
                    for index, (previous, current, delta) in enumerate(zip(saved.position, position, saved.offset)):
                        if previous == current:
                            continue
                        summed = (delta if not current else current if not delta
                                  else exact(current, delta, "add", self.work))
                        actual[index] = ops._rounded_vector((summed,))[0]
                        if actual[index] != saved.rounded[index]:
                            projected[index] = round_binary64(actual[index], work=self.work)
                    result = _WorldTargetPoint(tuple(projected))
                    replacement = _WorldTargetComponents(saved.offset, position, tuple(actual), result, target)
                else:
                    offset = ops.rotate(rotation, target)
                    actual = ops._rounded_vector(ops._add_exact_vectors(position, offset))
                    result = _WorldTargetPoint(ops._vector_projection(actual))
                    replacement = _WorldTargetComponents(offset, position, actual, result, target)
                if self.work.max_operand_bits != cap:
                    continue
                self.work.guard(*position, *target, *rotation.components, rotation.error_rad,
                                *replacement.offset, *replacement.rounded)
                self.work.remember(key, replacement)
                if self.work.max_operand_bits == cap:
                    return result
                continue
            key = ("reach_world_target_point", cap, position, rotation, target)
            result = self.work.lookup(key)
            if self.work.max_operand_bits != cap:
                continue
            if result is None:
                offset = ops.rotate(rotation, target)
                actual = ops._rounded_vector(ops._add_exact_vectors(position, offset))
                result = _WorldTargetPoint(ops._vector_projection(actual))
                if self.work.max_operand_bits != cap:
                    continue
                self.work.remember(key, result)
            if self.work.max_operand_bits == cap:
                return result

    def _latch_ordinary(self, path, time, state, status):
        action, runtime = self.model.actions[path], state.actions[path]
        elapsed = runtime.elapsed_at(time)
        if action.kind == "move":
            state.ideal_positions[action.target] = self._ideal_position(action.target, time, state)
            state.positions[action.target] = tuple(round_binary64(value, work=self.work) for value in
                self.pose_ops.affine(runtime.initial, action.vector, elapsed))
        elif action.kind == "spin":
            state.root_rotation_errors[action.target] = self._anchor_bound(action.target, time, state).rotation_error_rad
            anchor = self.pose_ops.materialize(self.pose_ops.make(orientation=
                self._advance_orientation(runtime.initial_rotation or runtime.initial, action.vector, elapsed)))
            state.orientations[action.target] = anchor.orientation
            state.root_rotation_values[action.target] = anchor.rotation
        else:
            state.ideal_coordinates[action.target] = self._ideal_coordinate(action.target, time, state)
            state.coordinates[action.target] = self._coordinate(action.target, time, state)[0]
        runtime.elapsed = elapsed
        runtime.status = status
        state.claims.pop(self._channel(action))

    def _exposed_vector(self, values):
        return tuple(round_binary64(value, work=self.work) for value in values)

    def _impulse_lever(self, current, point):
        return self._exposed_vector(self.pose_ops.rotate(current.rotation, point))

    def _impulse_point(self, current, lever):
        return self._exposed_vector(self.pose_ops.add(current.position, lever))

    def _impulse_cross(self, lever, impulse):
        return self._exposed_vector(self.pose_ops.cross(lever, impulse))

    def _impulse_velocity(self, initial, impulse, denominator):
        scale = exact(Fraction(1), Fraction(denominator), "div", self.work)
        return self._exposed_vector(self.pose_ops.add(initial, self.pose_ops.scale(impulse, scale)))

    def _impulse_anchor(self, current, velocity, omega):
        return self.pose_ops.materialize(self.pose_ops.make(
            position=current.position, orientation=current.rotation, velocity=velocity, omega=omega))

    def _impulse_error(self, event, time, state, before):
        """Propagate the actual impulse's rounding and incoming orientation error."""
        a = PhaseArithmetic(self.work)
        obj, payload = self.model.objects[event.target], event.impulse
        record = state.impulses[event.target].last_applications[-1]
        lever_size = a.l1(record["lever_arm_world_m"])
        lever_error = a.add(a.mul(before.rotation_error_rad, a.l1(payload.point_self_m)),
                           a.mul(Fraction(2), Fraction(1, 1 << 96)), a.rounding(lever_size))
        angular_impulse_error = a.add(a.mul(lever_error, a.l1(payload.impulse_world_n_s)),
                                      a.rounding(a.l1(record["angular_impulse_world_n_m_s"])))
        nominal_velocity = tuple(a.add(a.number(value), a.div(a.number(delta), a.number(obj.mass)))
            for value, delta in zip(record["linear_velocity_before_world_m_per_s"], payload.impulse_world_n_s))
        nominal_omega = tuple(a.add(a.number(value), a.div(a.number(delta), a.number(obj.inertia)))
            for value, delta in zip(record["angular_velocity_before_world_rad_per_s"], record["angular_impulse_world_n_m_s"]))
        velocity_round = a.l1(tuple(a.sub(a.number(actual), ideal) for actual, ideal in zip(
            record["linear_velocity_after_world_m_per_s"], nominal_velocity)))
        omega_round = a.l1(tuple(a.sub(a.number(actual), ideal) for actual, ideal in zip(
            record["angular_velocity_after_world_rad_per_s"], nominal_omega)))
        state.dynamic_errors[event.target] = AnchorError(before.position_error_m, before.rotation_error_rad,
            a.add(before.velocity_error_m_per_s, velocity_round),
            a.add(before.angular_velocity_error_rad_per_s, a.div(angular_impulse_error, a.number(obj.inertia)), omega_round))
        state.dynamic_error_times[event.target] = time

    def _ideal_acceleration(self, path, state):
        a = PhaseArithmetic(self.work)
        net = [Fraction(0), Fraction(0), Fraction(0)]
        for force in state.forces[path].active.values():
            self._check()
            net = [a.add(value, a.number(delta)) for value, delta in zip(net, force.payload.force_world_n)]
        mass = a.number(self.model.objects[path].mass)
        return tuple(a.add(a.number(gravity), a.div(force, mass)) for gravity, force in zip(self.model.gravity, net))

    def _bounded_projection(self, state):
        """Count unchanged force histories with the existing reach JSON units."""
        def empty_history(value):
            # Share only the completed measurement of this exact plain shape.
            # Distinct zero/count encodings and all other histories retain the
            # ordinary complete walker and its diagnostic ordering.
            if type(value) is not dict or tuple(value) != (
                    "active", "net_force_world_n", "acceleration_world_m_per_s2",
                    "started_count", "completed_count", "last_change_time_seconds", "last_changes"):
                return False
            net = value["net_force_world_n"]
            return (type(value["active"]) is list and not value["active"]
                and type(value["last_changes"]) is list and not value["last_changes"]
                and type(net) is list and len(net) == 3
                and all(type(component) is float and component.hex() == "0x0.0p+0" for component in net)
                and value["acceleration_world_m_per_s2"] is None
                and type(value["started_count"]) is int and value["started_count"] == 0
                and type(value["completed_count"]) is int and value["completed_count"] == 0
                and value["last_change_time_seconds"] is None)

        result = {}
        entries = byte_count = 0
        empty_size = None
        for path in state.forces:
            self._check()
            projection = self._projection(path, state)
            remaining_entries = _force_runtime.MAX_OUTPUT_RECORDS - entries
            remaining_bytes = _force_runtime.MAX_JSON_BYTES - byte_count
            try:
                if (empty_size is not None and empty_history(projection)
                        and empty_size["entries"] <= remaining_entries
                        and empty_size["bytes"] <= remaining_bytes):
                    size = empty_size
                else:
                    # A possible overflow still uses the original walker so
                    # the first failing entry/byte and consumed count match.
                    size = measure_reach_json(projection, max_entries=remaining_entries,
                        max_bytes=remaining_bytes, check=self.check)
                    if empty_history(projection):
                        empty_size = size
            except JSONLimitError as error:
                raise _force_runtime._resource(self.model, error.details) from error
            entries += size["entries"]
            byte_count += size["bytes"]
            result[path] = projection
        return result

    def _force_components(self, path, state):
        """Preserve canonical net/acceleration order while charging every helper."""
        a = PhaseArithmetic(self.work)
        sums = [Fraction(0), Fraction(0), Fraction(0)]
        for key in sorted(state.forces[path].active):
            self._check()
            values = state.forces[path].active[key].payload.force_world_n
            sums = [a.add(value, a.number(delta)) for value, delta in zip(sums, values)]
        net = tuple(round_binary64(value, work=self.work) for value in sums)
        mass = a.number(self.model.objects[path].mass)
        acceleration = tuple(round_binary64(a.add(a.number(gravity), a.div(a.number(force), mass)), work=self.work)
                             for gravity, force in zip(self.model.gravity, net))
        return net, acceleration

    def _event(self, event, time, state, incoming, dependencies, touched):
        self._terminal_pose_context = None
        self._invalidate()
        action = self.model.actions.get(event.target)
        if event.kind not in {"start", "pause", "resume", "stop"} or action is None or action.kind != "reach_planar":
            # A tween cannot acquire either half of an active reach's authority.
            if event.kind == "start" and action is not None and action.kind == "tween":
                owner = state.claims.get((action.target, "coordinate"))
                if owner is not None and self.model.actions[owner].kind == "reach_planar":
                    raise reach_error("reach_claim_conflict", "A reach already owns this coordinate.", event.span,
                                      phase="admission", time=time, element_id=action.element_id,
                                      details={"joint": action.target, "claimant": owner, "requested": action.path})
            ideal_initial = None
            if event.kind == "start" and action is not None:
                if action.kind == "move":
                    ideal_initial = self._ideal_position(action.target, time, state)
                elif action.kind == "tween":
                    ideal_initial = self._ideal_coordinate(action.target, time, state)
            impulse_bound = (self._anchor_bound(event.target, time, state)
                             if event.kind == "impulse" and event.target in state.dynamic else None)
            super()._event(event, time, state, incoming, dependencies, touched)
            if event.kind == "start" and action is not None:
                runtime = state.actions[action.path]
                runtime.ideal_initial = ideal_initial
                if action.kind == "spin":
                    runtime.ideal_rotation_error = state.root_rotation_errors.get(action.target, Fraction(0))
                    runtime.initial_rotation = state.root_rotation_values.get(action.target)
            if event.kind == "release":
                child = self.model.sites[self.model.joints[event.target].child].owner
                state.dynamic[child].state = self.pose_ops.materialize(incoming[child])
                state.dynamic_errors[child] = self._anchor_error(self._anchor_bound(child, time, self.state))
                state.dynamic_error_times[child] = time
                state.ideal_accelerations[child] = tuple(PhaseArithmetic(self.work).number(value) for value in self.model.gravity)
                self._pending_releases.append(self._release_record(event, time, incoming, dependencies))
            if event.kind == "impulse" and event.impulse.impulse_world_n_s != ZERO:
                self._impulse_error(event, time, state, impulse_bound)
            self._invalidate()
            return
        runtime = state.actions[event.target]
        valid = {"start": {"pending"}, "pause": {"running"},
                 "resume": {"paused"}, "stop": {"running", "paused"}}
        if runtime.status not in valid[event.kind]:
            raise OntoKinError("OKL-E-ACTION-STATE",
                f"Cannot {event.kind} action {event.target} while it is {runtime.status}.", event.span,
                phase="admission" if event.kind == "start" else "transition", time=time,
                element_id=list(action.element_id), related=[action.span], rule_ids=["LANG-019", "LANG-020"],
                details={"action": action.path, "status": runtime.status, "requested_event": event.kind})
        payload = action.reach
        channels = ((payload.shoulder, "coordinate"), (payload.elbow, "coordinate"))
        if event.kind == "start":
            self._check()
            for channel in channels:
                if channel in state.claims:
                    raise reach_error("reach_claim_conflict", "Another action owns a requested reach coordinate.",
                                      event.span, phase="admission", time=time, element_id=action.element_id,
                                      details={"channel": list(channel), "claimant": state.claims[channel],
                                               "requested": action.path})
            active = sum(self.model.actions[path].kind == "reach_planar" and
                         item.status in {"running", "paused"} for path, item in state.actions.items())
            if active >= 32:
                raise reach_error("reach_resource", "At most 32 reaches may run or pause simultaneously.",
                                  event.span, phase="admission", time=time, element_id=action.element_id,
                                  details={"budget": "active_reaches", "limit": 32, "consumed": active + 1})
            for joint_path in (payload.shoulder, payload.elbow):
                joint = self.model.joints[joint_path]
                child = self.model.sites[joint.child].owner
                if state.modes[child] != "prescribed":
                    raise reach_error("reach_chain", "The admitted reach links must remain prescribed.",
                                      event.span, time=time, element_id=action.element_id)
            initial = tuple(self._coordinate(path, time, state)[0] for path in (payload.shoulder, payload.elbow))
            ideal_initial = tuple(self._ideal_coordinate(path, time, state) for path in (payload.shoulder, payload.elbow))
            try:
                solution = admit_planar(payload.lengths_m, payload.target_m, payload.branch,
                                        payload.limits_rad, work=self.work)
            except ReachAdmissionError as error:
                self._numeric_error(error, action=action, time=time, phase="admission", node=event.span)
            # All admission checks succeeded. These writes affect only the
            # staged whole-boundary state, never one externally visible claim.
            runtime.initial = initial
            runtime.ideal_initial = ideal_initial
            runtime.solution = solution
            runtime.start_time = time
            runtime.elapsed = Fraction(0)
            runtime.running_since = time
            runtime.status = "running"
            for channel in channels:
                state.claims[channel] = action.path
        elif event.kind == "pause":
            runtime.elapsed = runtime.elapsed_at(time)
            runtime.status = "paused"
        elif event.kind == "resume":
            runtime.running_since = time
            runtime.status = "running"
        else:
            self._latch(action.path, time, state, "stopped")
        touched.update({("joint", payload.shoulder), ("joint", payload.elbow)})
        self._invalidate()

    def _latch(self, path, time, state, status):
        self._invalidate()
        action = self.model.actions[path]
        context = self._terminal_pose_context
        if context is not None:
            self.work.charge("source_terminal_latch_guard")
            runtime = state.actions[path]
            if (action.kind != "reach_planar" or status != "completed" or
                    runtime.status != "running" or runtime.elapsed_at(time) != action.duration or
                    context.time != time or context.staged_state is not None and context.staged_state is not state):
                self._terminal_pose_context = None
            else:
                context.staged_state = state
        if action.kind != "reach_planar":
            self._latch_ordinary(path, time, state, status)
            self._invalidate()
            return
        runtime, payload = state.actions[path], action.reach
        pair = self._pair(path, time, state)
        tip = self._tip_base(action, time, state, terminal=True)
        squared = measured_residual_squared(tip.position, payload.target_m, work=self.work)
        if status == "completed" and squared > Fraction(1, 10**18):
            raise reach_error("reach_numeric", "The measured terminal reach residual exceeds 1e-9 meters.",
                              action.span, phase="evaluation", time=time, element_id=action.element_id,
                              details={"position_residual_m": rounded_sqrt(squared, work=self.work)})
        terminal = {"outcome": "satisfied" if status == "completed" else "interrupted",
                    "time_seconds": time_text(time), "position_residual_m": rounded_sqrt(squared, work=self.work),
                    "joint_coordinates_rad": list(pair.coordinates_rad), "tip_pose_base": self._pose_record(tip)}
        for joint_path, coordinate in zip((payload.shoulder, payload.elbow), pair.coordinates_rad):
            state.ideal_coordinates[joint_path] = self._ideal_coordinate(joint_path, time, state)
            state.coordinates[joint_path] = coordinate
        runtime.elapsed = runtime.elapsed_at(time)
        runtime.status = status
        runtime.terminal = terminal
        for joint_path in (payload.shoulder, payload.elbow):
            state.claims.pop((joint_path, "coordinate"))
        self._invalidate()

    def _process_boundary(self, time):
        self._pending_releases = []
        # The incoming state is unchanged until the inherited transaction has
        # deep-copied it. Keep the single complete graph already checked by an
        # immediate before-side observation: _resolve_kinematics still requires
        # its exact state identity and applicable clock. All staged mutations
        # below keep their own invalidation, and failure discards every graph.
        # Mutable output and derived observations are never carried forward.
        self._pending_reach_output = None
        self._derived_pose_cache.clear()
        self._terminal_pose_context = (None if self.state.dynamic else
                                       _TerminalPoseContext(time, self.state))
        try:
            super()._process_boundary(time)
        except BaseException:
            self._pending_releases = []
            self._invalidate()
            raise
        finally:
            self._terminal_pose_context = None
        self.incoming_releases = self._pending_releases
        self.incoming_release_time = time
        self._pending_releases = []

    def incoming_releases_at(self, time):
        """Return only releases from this successfully committed exact boundary."""
        self._check()
        records = self.incoming_releases if Fraction(time) == self.incoming_release_time else []
        measure_reach_json(records, check=self._work_check)
        return copy.deepcopy(records)

    def _aggregate(self, path, time, state):
        self._invalidate()
        changed = path in state.dynamic and (state.forces[path].last_time == time or
                                            state.forces[path].acceleration is None)
        if changed:
            self._terminal_pose_context = None
        original = state.dynamic.get(path)
        before = self._anchor_bound(path, time, state) if changed else None
        super()._aggregate(path, time, state)
        if changed:
            error = self._anchor_error(before)
            if state.dynamic[path] is original:
                # A net-zero/equal-force replacement keeps the inherited actual
                # trajectory anchor. The ideal acceleration still has a new
                # phase. Convert the public-point bound back to this private
                # continuing trajectory using its exact publication discrepancy.
                a = PhaseArithmetic(self.work)
                point = self._dynamic_kinematics(path, time, state)
                position_round = a.l1(tuple(a.sub(a.number(x), y) for x, y in zip(point.position, point.exact_position)))
                velocity_round = a.l1(tuple(a.sub(a.number(x), y) for x, y in zip(point.velocity, point.exact_velocity)))
                error = AnchorError(a.add(error.position_m, position_round),
                    a.add(error.rotation_rad, Fraction(1, 1 << 50)),
                    a.add(error.velocity_m_per_s, velocity_round), error.angular_velocity_rad_per_s)
            else:
                state.dynamic[path].state = self.pose_ops.materialize(state.dynamic[path].state)
            state.dynamic_errors[path] = error
            state.dynamic_error_times[path] = time
            state.ideal_accelerations[path] = self._ideal_acceleration(path, state)
        self._invalidate()

    def _validate_staged(self, time, staged, incoming):
        # The complete after-side projection is required for admission. Its
        # single pending output may be transferred to the immediate matching
        # observer once, after every staged check succeeds. It is not retained
        # as a reusable numerical result or exposed before the boundary commits.
        self._pending_reach_output = None
        super()._validate_staged(time, staged, incoming)
        projection = self._reach_map(time, "after", staged)
        try:
            measure_reach_json(self._pending_releases, check=self._work_check)
        except JSONLimitError as error:
            raise reach_error("reach_resource", "Complete incoming releases exceed the output bound.",
                              self.model.span, phase="evaluation", time=time, details=error.details) from error
        self.work.charge("source_validated_reach_output_publish")
        self._pending_reach_output = (staged, time, self.context_kind, projection)

    @staticmethod
    def _pose_record(pose):
        return {"position_m": list(pose.position), "orientation_wxyz": list(pose.orientation)}

    def _physical_observation(self, action, time, state):
        """Return immutable physical values for one unchanged snapshot's inputs."""
        payload = action.reach
        physical = tuple(self._coordinate(joint, time, state) for joint in (payload.shoulder, payload.elbow))
        _, frames = self._kinematics(time, state)
        base_tip = self._tip_base(action, time, state)
        target_world = self._world_target(payload, time, state, frames)
        world_tip = frames[payload.tip + ".frame"]
        return (physical, (base_tip.position, base_tip.orientation),
                (world_tip.position, world_tip.orientation), target_world.position)

    def _current(self, path, time, side, state, *, observation_cache=None):
        action, runtime = self.model.actions[path], state.actions[path]
        payload = action.reach
        observation = None
        key = (payload.shoulder, payload.elbow, payload.base_frame, payload.tip, payload.target_m)
        if observation_cache is not None:
            self.work.charge("source_physical_observation_lookup")
            observation = observation_cache.get(key)
        if observation is None:
            observation = self._physical_observation(action, time, state)
            if observation_cache is not None and len(observation_cache) < min(128, self.work.max_cache_entries):
                self.work.charge("source_physical_observation_publish")
                observation_cache[key] = observation
        physical, base_tip, world_tip, target_world = observation
        admitted = runtime.solution is not None
        residual = (rounded_sqrt(measured_residual_squared(base_tip[0], payload.target_m, work=self.work),
                                 work=self.work) if admitted else None)
        completion = (runtime.running_since + action.duration - runtime.elapsed
                      if runtime.status == "running" else
                      Fraction(runtime.terminal["time_seconds"]) if runtime.status == "completed" else None)
        own = self._pair(path, time, state).rates_rad_s if runtime.status == "running" else (0.0, 0.0)
        return {
            "observation": {"time_seconds": time_text(time), "side": side,
                            "run_id": None, "context_kind": self.context_kind},
            "lifecycle": runtime.status,
            "goal_outcome": {"pending": "pending", "running": "active", "paused": "active",
                             "stopped": "interrupted", "completed": "satisfied"}[runtime.status],
            "resolved_joint_targets_rad": list(runtime.solution.target_rad) if admitted else None,
            "start_coordinates_rad": list(runtime.initial) if admitted else None,
            "start_time_seconds": time_text(runtime.start_time) if admitted else None,
            "elapsed_seconds": time_text(runtime.elapsed_at(time)) if admitted else None,
            "completion_time_seconds": None if completion is None else time_text(completion),
            "joint_coordinates_rad": [entry[0] for entry in physical],
            "joint_rates_rad_per_s": [entry[1] for entry in physical],
            "action_joint_rates_rad_per_s": list(own),
            "claimed_joint_ids": [list(self.model.joints[joint].element_id)
                                  for joint in (payload.shoulder, payload.elbow)]
                                 if runtime.status in {"running", "paused"} else [],
            "current_residual_m": residual,
            "tip_pose_base": {"position_m": list(base_tip[0]), "orientation_wxyz": list(base_tip[1])},
            "tip_pose_world": {"position_m": list(world_tip[0]), "orientation_wxyz": list(world_tip[1])},
            "current_world_target_m": list(target_world),
            "terminal_result": copy.deepcopy(runtime.terminal),
        }

    def _reach_map(self, time, side, state):
        pending = self._pending_reach_output
        # Detach before even invoking the charged callback. A miss, cancelled
        # transfer or failed observer can never leave a reusable mutable alias.
        self._pending_reach_output = None
        if pending is not None:
            self.work.charge("source_validated_reach_output_check")
            staged, validated_time, context_kind, projection = pending
            if (state is staged and time == validated_time and side == "after"
                    and self.context_kind == context_kind):
                return projection
        result = {}
        # This bounded cache lives only during one unchanged state/time/side.
        # Its tuples contain physical values, never action identity, lifecycle,
        # claims, admission results or mutable output records. Every action is
        # still visited, projected freshly and counted in the complete output.
        observations = {}
        entries, byte_count = 1, 2
        for path, action in self.model.actions.items():
            self._check()
            if action.kind != "reach_planar":
                continue
            projection = reach_projection(self.model, path, check=self._work_check,
                context_kind=self.context_kind,
                current=self._current(path, time, side, state, observation_cache=observations))
            try:
                key_size = measure_reach_json(path, check=self._work_check)["bytes"] + 2
                measured = measure_reach_json(projection, max_entries=100000 - entries,
                                              max_bytes=4 * 1024 * 1024 - byte_count - key_size,
                                              check=self._work_check)
            except JSONLimitError as error:
                raise reach_error("reach_resource", "Complete current reach output exceeds its bound.",
                                  action.span, phase="inspection", time=time, side=side,
                                  element_id=action.element_id, details=error.details, blocks=[]) from error
            entries += measured["entries"]
            byte_count += measured["bytes"] + key_size
            result[path] = projection
        return result

    def _release_record(self, event, time, incoming, dependencies):
        joint = self.model.joints[event.target]
        child = self.model.sites[joint.child].owner
        pose = incoming[child]
        contributors = []
        for path, action in self.model.actions.items():
            self._check()
            if action.kind != "reach_planar":
                continue
            payload = action.reach
            runtime = self.state.actions[path]  # Saved incoming state, before completion/source statements.
            if runtime.status != "running" or not ({("joint", payload.shoulder), ("joint", payload.elbow)}
                                                    & dependencies[event.target]):
                continue
            pair = self._pair(path, time, self.state)
            contributors.append({"action": occurrence(self.model, path),
                                 "shoulder": occurrence(self.model, payload.shoulder),
                                 "elbow": occurrence(self.model, payload.elbow),
                                 "joint_coordinates_rad": list(pair.coordinates_rad),
                                 "joint_rates_rad_per_s": list(pair.rates_rad_s)})
        block = self.events[self.event_index]
        sequence_index = next(index for index, candidate in enumerate(block.events) if candidate is event)
        node = event.span
        source = self.model.source_provenance[node.source_id]
        return {"program_revision": self.model.program_revision,
                "source_location": {"source_id": node.source_id, "source_revision": source["source_revision"],
                                    "start_byte": node.start, "end_byte": node.end},
                "sequence_index": sequence_index, "time_seconds": time_text(time),
                "grip": occurrence(self.model, event.target), "target": occurrence(self.model, child),
                "reach_contributors": contributors, "incoming_pose_world": self._pose_record(pose),
                "incoming_linear_velocity_world_m_per_s": list(pose.velocity),
                "incoming_angular_velocity_world_rad_per_s": list(pose.omega)}

    def recording_boundary(self, time, side, *, _reuse=None):
        """Project every promised H06 history without unused inspection output.

        Recording preparation has already executed this exact boundary side.
        The complete graph still receives the public finiteness checks from a
        source snapshot, including every unselected site. A guarded exact proof
        may establish admissibility without constructing unused public tuples.
        Only output that the recording actually retains is allocated and
        serialized here; ordinary
        source snapshots keep their complete geometry, masses and frame maps.
        """
        poses, frames = self._kinematics(time, self.state)
        for path, pose in frames.items():
            self._check()
            if not (path.endswith(".frame") and poses.get(path[:-6]) is pose):
                self.pose_ops.ensure_finite(pose)
        incoming = self._incoming(self.state)
        forces = self._bounded_projection(self.state)
        objects = {}
        for path, obj in self.model.objects.items():
            self._check()
            mode = self.state.modes[path]
            if path in incoming:
                kind, relation = incoming[path]
                authority = {"kind": kind, "relation": relation}
            elif mode == "dynamic":
                anchor = self.state.dynamic[path]
                authority = {"kind": "free_sphere", "since_seconds": time_text(anchor.since),
                             "trajectory_anchor_seconds": time_text(anchor.time)}
            else:
                authority = {"kind": mode,
                             "translation_action": self.state.claims.get((path, "translation")),
                             "orientation_action": self.state.claims.get((path, "orientation"))}
            # Retain the ordinary source aggregate-finiteness check, even
            # though no aggregate mass is part of the H06 boundary output.
            _round(sum((_f(owned.mass) for owned in self.model.objects.values()
                        if owned.path == path or owned.path.startswith(path + ".")), Fraction(0)))
            history = self.state.impulses[path]
            applications = []
            for record in history.last_applications:
                self._check()
                applications.append(copy.deepcopy(record))
            objects[path] = {"pose_authority": authority, "forces": forces[path],
                "impulses": {"applied_count": history.applied_count,
                    "last_application_time_seconds": (None if history.last_time is None else
                                                        time_text(history.last_time)),
                    "last_applications": applications}}
        _round(sum((_f(obj.mass) for obj in self.model.objects.values()), Fraction(0)))
        if _reuse is not None and side == "after" and _reuse[0].owner is self:
            # The complete graph, force/impulse histories and aggregate-mass
            # checks above remain fresh. Only unchanged endpoint joint/action/
            # reach projection may transfer, with complete after output bounds.
            result = _reuse[0].after(_reuse[1], time, objects=objects)
            if result is not None:
                return result
            # A callback may change actual source/state or live limits during
            # receipt validation or output copying. Rebuild under those inputs.
            return self.recording_boundary(time, side)
        joints = {}
        for path, joint in self.model.joints.items():
            self._check()
            record = {"element_id": list(joint.element_id), "kind": joint.kind,
                "status": "inactive" if joint.kind == "grip" and path not in self.state.active_grips else "active",
                "parent_site": joint.parent, "child_site": joint.child,
                "coupling": "externally_prescribed_no_load_solution"}
            if joint.kind in ("hinge", "slider"):
                coordinate, rate = self._coordinate(path, time, self.state)
                record.update(coordinate=coordinate, coordinate_rate=rate,
                    unit="rad" if joint.kind == "hinge" else "m", limits=list(joint.limits),
                    action=self.state.claims.get((path, "coordinate")))
            joints[path] = record
        actions = {}
        for path, action in self.model.actions.items():
            self._check()
            actions[path] = {"element_id": list(action.element_id), "kind": action.kind,
                "target": action.target, "status": self.state.actions[path].status,
                "local_elapsed_seconds": time_text(self.state.actions[path].elapsed_at(time)),
                "duration_seconds": time_text(action.duration)}
        return self._snapshot_data({"time_seconds": time_text(time), "side": side,
            "objects": objects, "joints": joints, "actions": actions,
            "reaches": self._reach_map(time, side, self.state)}, time, side)

    def _snapshot_data(self, result, time, side):
        """Apply the unchanged complete JSON bounds to an actual output scope."""
        try:
            return bounded_data(result, check=self._work_check)
        except JSONLimitError as error:
            raise reach_error("reach_resource", "The complete sampled source state exceeds its JSON bound.",
                              self.model.span, phase="inspection", time=time, side=side,
                              details=error.details, blocks=[]) from error

    def snapshot(self, time, side):
        result = super().snapshot(time, side)
        result["reaches"] = self._reach_map(time, side, self.state)
        # Inherited geometry retains immutable LoftSection dataclasses.
        # Materialize every occurrence before publishing the source snapshot.
        return self._snapshot_data(result, time, side)

    def advance(self, time, side="after"):
        try:
            return super().advance(time, side)
        except ReachAdmissionError as error:
            self._numeric_error(error, time=time)
