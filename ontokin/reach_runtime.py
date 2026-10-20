"""Coupled reach lifecycle on the inherited whole-boundary force transaction."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType

from .diagnostics import OntoKinError
from .evaluator import (_ActionState, _DynamicInitial, _Kinematics, _NumericFault,
                        ZERO, _f, _round, time_text)
from .force_runtime import ForceSimulator, _ForceRunState
from .json_limits import JSONLimitError, measure_json
from .reach_kinematics import (admit_planar, measured_residual_squared,
                               rounded_sqrt, sample_pair)
from .reach_numeric import ReachAdmissionError, ReachExecutionWork, compare, exact, round_binary64
from .reach_projection import (occurrence, reach_projection, reach_record_bound,
                               measure_reach_json)
from .reach_source import reach_error
from .reach_phase import AnchorError, PhaseArithmetic, joint_phase, phase_bounds
from .values import bounded_data


def _incoming_release_bound(model, time, *, check=None):
    """Count topology-permitted contributor identities without admitting events."""
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


def boundary_history_bound(model, boundary_times, *, horizon=None, side="after", check=None):
    """Preflight the adopted complete H06 history before retaining all sides.

    The supplied exact clocks are actual semantic boundaries discovered by a
    bounded prefix replay. This function never performs admission or samples a
    future event. Both sides use the inherited conservative nested-history
    weights, and every repeated reach/source identity counts at each occurrence.
    """
    from .evaluator import MAX_OUTPUT_RECORDS, _records_per_sample
    endpoint = model.duration if horizon is None else Fraction(horizon)
    if side not in {"before", "after"} or not 0 <= endpoint <= model.duration:
        raise ValueError("The history horizon must be a valid exact source prefix.")
    dropped = len(model.objects) + len(model.sites) + 1
    total = 0
    for value in boundary_times:
        if check is not None:
            check()
        time = Fraction(value)
        if not 0 <= time <= endpoint:
            raise ValueError("A retained boundary lies outside the requested prefix.")
        last_side = "before" if time == endpoint and side == "before" else "after"
        before = _records_per_sample(model, check=check, horizon=time, side="before") - dropped
        after = _records_per_sample(model, check=check, horizon=time, side=last_side) - dropped
        incoming = 1 if last_side == "before" else _incoming_release_bound(model, time, check=check)
        total += 2 + before + after + incoming
        if total > MAX_OUTPUT_RECORDS:
            raise reach_error("reach_resource", "Complete retained reach boundaries exceed the state-record budget.",
                model.span, phase="inspection", blocks=[], details={"budget": "boundary_state_records",
                    "limit": MAX_OUTPUT_RECORDS, "consumed": total,
                    "through_seconds": time_text(time)})
    return total


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


@dataclass(frozen=True)
class RecordingPose:
    """Only the actual canonical components consumed by a recorded key."""
    position: tuple[float, float, float]
    orientation: tuple[float, float, float, float]


class ReachSimulator(ForceSimulator):
    """One exact clock and two claims per reach, with no partial admission."""

    def __init__(self, model, check=None, *, work=None):
        self.work = work if work is not None else ReachExecutionWork(check=check)
        self.context_kind = "recorded_prefix"
        self._pose_cache = {}
        self._pair_cache = {}
        self._derived_pose_cache = {}
        self._pending_releases = []
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
        self._pose_cache.clear()
        self._derived_pose_cache.clear()

    def _pose_slot(self, path, signature, build):
        """Reuse only a numerically identical node within the bounded work cache.

        Each path has one replaceable slot, not one retained entry per sample.
        The signature retains its private parent value and complete local
        operands, so neither object-id reuse nor a changed claim can hit it.
        Every lookup/insertion remains a charged request operation.
        """
        key = ("reach_source_pose", self.model.program_revision, path)
        old = self.work.lookup(key)
        if old is not None and old[0] == signature:
            return old[1]
        result = build()
        self.work.remember(key, (signature, result))
        return result

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

    def _advance_orientation(self, initial, omega, elapsed):
        plan = self.work.lookup(("reach_source_spin_phase", tuple(omega)))
        if plan is not None and abs(elapsed) > plan.max_elapsed_s:
            plan = None
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

    def _pair(self, path, time, state):
        runtime, action = state.actions[path], self.model.actions[path]
        self._check()
        key = (runtime.initial, runtime.solution.target_rad, self.model.actions[path].duration,
               runtime.elapsed_at(time), runtime.status == "running")
        if key not in self._pair_cache:
            if len(self._pair_cache) >= 256:
                self._pair_cache.clear()
            self._pair_cache[key] = sample_pair(runtime.initial, runtime.solution.target_rad,
                action.duration, runtime.elapsed_at(time), running=runtime.status == "running", work=self.work)
        return self._pair_cache[key]

    def _coordinate(self, path, time, state):
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
        pair = self._pair(claimant, time, state)
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

    def _dynamic_kinematics(self, path, time, state, *, pose_only=False):
        self._check()
        anchor = state.dynamic[path]
        initial = anchor.state
        elapsed = time - anchor.time
        acceleration = self._acceleration(path, state)
        rotation = initial.rotation if hasattr(initial, "rotation") else initial.orientation
        return self.pose_ops.make(
            position=self.pose_ops.parabolic(initial.position, initial.velocity, acceleration, elapsed),
            orientation=self._advance_orientation(rotation, initial.omega, elapsed),
            velocity=ZERO if pose_only else self.pose_ops.affine(initial.velocity, acceleration, elapsed),
            omega=ZERO if pose_only else initial.omega)

    def _kinematics(self, time, state):
        return self._resolve_kinematics(time, state)

    def recording_frames(self, time, state, selected_paths):
        """Sample p/q from a validated phase without constructing unused rates.

        The recording planner must first validate the complete requested prefix
        and derive its whole-phase bounds. This method neither advances events
        nor substitutes partial output for a complete source observation. Its
        private derivative-free graph cannot enter the full-kinematics cache.
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
            _, frames = self._resolve_kinematics(time, state, selected_frames=selected, pose_only=True)
            result = {}
            for path in selected:
                self._check()
                result[path] = RecordingPose(frames[path].position, frames[path].orientation)
            return result
        except ReachAdmissionError as error:
            self._numeric_error(error, time=time)

    def _resolve_kinematics(self, time, state, *, selected_frames=None, pose_only=False):
        """Resolve the actual pose graph without intermediate float exposure.

        This separate 0.6 path leaves every older profile's pose arithmetic
        unchanged. Only public sample/anchor components materialize binary64.
        """
        key = (id(state), time)
        cached = self._pose_cache.get(key) if not pose_only and selected_frames is None else None
        if cached is not None and cached[0] is state:
            self._check()
            return cached[1], cached[2]
        ops = self.pose_ops
        incoming = self._incoming(state)
        objects, frames, resolving = {}, {"world": self._identity_pose}, set()

        def slot(path, signature, build):
            return self._pose_slot(("recording", path) if pose_only else path, signature, build)

        def frame(path):
            if path not in frames:
                stem = path.removesuffix(".frame")
                if stem in self.model.objects:
                    frames[path] = instance(stem)
                else:
                    site = self.model.sites[stem]
                    owner = instance(site.owner)
                    frames[path] = slot(path, (owner, site.pose),
                        lambda: ops.compose(owner, self._constant_pose(site.pose)))
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
                        lambda: ops.compose(parent, self._constant_pose(follow.offset)))
                else:
                    joint = self.model.joints[relation_path]
                    parent = frame(joint.parent + ".frame")
                    coordinate, slope = None, None
                    if joint.kind in {"hinge", "slider"}:
                        if pose_only:
                            coordinate, slope = self._coordinate(relation_path, time, state)[0], Fraction(0)
                        else:
                            coordinate, slope, _ = self._exact_coordinate(relation_path, time, state)
                    child_pose = self.model.sites[joint.child].pose
                    def connected():
                        relative = self._identity_pose
                        if joint.kind == "hinge":
                            relative = ops.hinge_pose(joint.axis, coordinate, slope)
                        elif joint.kind == "slider":
                            relative = ops.make(position=ops.scale(joint.axis, Fraction(coordinate)),
                                                velocity=ops.scale(joint.axis, slope))
                        return ops.compose(ops.compose(parent, relative),
                                           self._constant_pose(child_pose, inverse=True))
                    result = slot(path,
                        ("joint", parent, joint.kind, joint.axis, coordinate, slope, child_pose), connected)
            elif state.modes[path] == "dynamic":
                result = self._dynamic_kinematics(path, time, state, pose_only=pose_only)
            else:
                position = state.positions[path]
                rotation = state.root_rotation_values.get(path, state.orientations[path])
                velocity, omega = ZERO, ZERO
                claimant = state.claims.get((path, "translation"))
                if claimant is not None:
                    action, runtime = self.model.actions[claimant], state.actions[claimant]
                    position = ops.affine(runtime.initial, action.vector, runtime.elapsed_at(time))
                    if runtime.status == "running" and not pose_only:
                        velocity = action.vector
                claimant = state.claims.get((path, "orientation"))
                if claimant is not None:
                    action, runtime = self.model.actions[claimant], state.actions[claimant]
                    rotation = self._advance_orientation(runtime.initial_rotation or runtime.initial,
                                                         action.vector, runtime.elapsed_at(time))
                    if runtime.status == "running" and not pose_only:
                        omega = action.vector
                result = slot(path, ("root", position, rotation, velocity, omega),
                    lambda: ops.make(position=position, orientation=rotation, velocity=velocity, omega=omega))
            resolving.remove(path)
            # This is an explicit finiteness check; opaque internals continue
            # down the graph even after canonical components are cached.
            if not pose_only:
                result.position, result.orientation, result.velocity, result.omega
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

    def _tip_base(self, action, time, state):
        payload = action.reach
        key = (id(state), time, "tip", payload.base_frame, payload.tip)
        self._check()
        if key in self._derived_pose_cache:
            return self._derived_pose_cache[key]
        _, frames = self._kinematics(time, state)
        base, tip = frames[payload.base_frame], frames[payload.tip + ".frame"]
        def relative_pose():
            rotation = self.pose_ops.multiply(self.pose_ops.inverse_rotation(base.rotation), tip.rotation)
            return self.pose_ops.make(position=self.pose_ops.relative_point(base, tip), orientation=rotation)
        result = self._pose_slot(("tip_in_base", payload.base_frame, payload.tip), (base, tip), relative_pose)
        if len(self._derived_pose_cache) < 256:
            self._derived_pose_cache[key] = result
        return result

    def _world_target(self, payload, time, state, frames):
        key = (id(state), time, "target", payload.base_frame, payload.target_m)
        self._check()
        if key not in self._derived_pose_cache:
            base = frames[payload.base_frame]
            result = self._pose_slot(("target_in_world", payload.base_frame, payload.target_m), (base,),
                lambda: self.pose_ops.compose(base, self.pose_ops.make(position=payload.target_m)))
            if len(self._derived_pose_cache) >= 256:
                return result
            self._derived_pose_cache[key] = result
        return self._derived_pose_cache[key]

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
        if action.kind != "reach_planar":
            self._latch_ordinary(path, time, state, status)
            self._invalidate()
            return
        runtime, payload = state.actions[path], action.reach
        pair = self._pair(path, time, state)
        tip = self._tip_base(action, time, state)
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
        self._invalidate()
        try:
            super()._process_boundary(time)
        except BaseException:
            self._pending_releases = []
            self._invalidate()
            raise
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
        super()._validate_staged(time, staged, incoming)
        self._reach_map(time, "after", staged)
        try:
            measure_reach_json(self._pending_releases, check=self._work_check)
        except JSONLimitError as error:
            raise reach_error("reach_resource", "Complete incoming releases exceed the output bound.",
                              self.model.span, phase="evaluation", time=time, details=error.details) from error

    @staticmethod
    def _pose_record(pose):
        return {"position_m": list(pose.position), "orientation_wxyz": list(pose.orientation)}

    def _current(self, path, time, side, state):
        action, runtime = self.model.actions[path], state.actions[path]
        payload = action.reach
        physical = [self._coordinate(joint, time, state) for joint in (payload.shoulder, payload.elbow)]
        _, frames = self._kinematics(time, state)
        base_tip = self._tip_base(action, time, state)
        target_world = self._world_target(payload, time, state, frames)
        admitted = runtime.solution is not None
        residual = (rounded_sqrt(measured_residual_squared(base_tip.position, payload.target_m, work=self.work),
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
            "current_residual_m": residual, "tip_pose_base": self._pose_record(base_tip),
            "tip_pose_world": self._pose_record(frames[payload.tip + ".frame"]),
            "current_world_target_m": list(target_world.position),
            "terminal_result": copy.deepcopy(runtime.terminal),
        }

    def _reach_map(self, time, side, state):
        result = {}
        entries, byte_count = 1, 2
        for path, action in self.model.actions.items():
            self._check()
            if action.kind != "reach_planar":
                continue
            projection = reach_projection(self.model, path, check=self._work_check,
                context_kind=self.context_kind, current=self._current(path, time, side, state))
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

    def snapshot(self, time, side):
        result = super().snapshot(time, side)
        result["reaches"] = self._reach_map(time, side, self.state)
        try:
            # Inherited geometry retains immutable LoftSection dataclasses.
            # Materialize their complete contents under the existing guarded
            # converter before publishing a JSON source observation. This
            # charges each repeated occurrence; no geometry field is omitted.
            result = bounded_data(result, check=self._work_check)
        except JSONLimitError as error:
            raise reach_error("reach_resource", "The complete sampled source state exceeds its JSON bound.",
                              self.model.span, phase="inspection", time=time, side=side,
                              details=error.details, blocks=[]) from error
        return result

    def advance(self, time, side="after"):
        try:
            return super().advance(time, side)
        except ReachAdmissionError as error:
            self._numeric_error(error, time=time)
