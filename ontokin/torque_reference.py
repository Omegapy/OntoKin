"""Independent source reconstruction for finite Cartesian torque.

Only immutable constructed source records and the independent interval
arithmetic are inputs. No runtime state, producer sampler, phase table or
certificate is consulted. The canonical and ideal angular histories have
separate clocks; translational history remains the inherited reference.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
from fractions import Fraction as F
import math

from .reach_reference import (
    Interval, PoseEnclosure, ReachReference, ReferenceError, ZERO,
    MAX_BOUNDARIES, _time_text,
)
from . import torque_axis_reference as axis_reference
from . import torque_axis_exact as exact_axis

AXES = {"world_x": (1, 0, 0), "world_y": (0, 1, 0), "world_z": (0, 0, 1)}
PHASE_LIMIT = F(1 << 20)
ROUND_RELATIVE = F(1, 1 << 53)
ROUND_TINY = F(1, 1 << 1075)
AXIS_ERROR = F(1, 1 << 74)
PRODUCT_ERROR = F(1, 1 << 91)
EXPOSED_ERROR = F(1, 1 << 50)


@dataclass
class _RotationOrigin:
    time: F
    orientation: tuple
    speed: Interval
    theta_error: F
    speed_error: F


@dataclass
class _ReferenceOrigin:
    time: F
    orientation: tuple
    speed: Interval
    acceleration: F
    theta_error: F
    speed_error: F
    required_theta: F = F(0)
    required_speed: F = F(0)


class TorqueErrorRequirement(Interval):
    def __init__(self, minimum):
        super().__init__(F(minimum), F(minimum))

    @property
    def minimum(self):
        return self.lo


@dataclass
class _TorqueHistory:
    active: dict = field(default_factory=dict)
    axis: str | None = None
    net: float = 0.0
    acceleration: float = 0.0
    reference_acceleration: F = F(0)
    rotation: _RotationOrigin | None = None
    reference: _ReferenceOrigin | None = None
    pending_angular: tuple | None = None
    started: int = 0
    completed: int = 0
    last_time: F | None = None
    changes: list = field(default_factory=list)
    support: axis_reference.AngularSupport | None = None


class TorqueReference(ReachReference):
    """Source-event ledger with independent exact angular acceleration."""

    def _initialize(self):
        super()._initialize()
        self._state.torques = {}
        for path in self.model.objects:
            self.a.tick()
            obj = self.model.objects[path]
            exact_q = exact_axis.rotation(obj.placement.rotation, self.a)
            exact_w = tuple(F(value) for value in obj.omega) if obj.motion == "dynamic" else (F(0),)*3
            support = axis_reference.AngularSupport(F(0), axis_reference.constants(exact_q),
                        axis_reference.constants(exact_w), exact_q, exact_w,
                        rotation_error=PRODUCT_ERROR)
            self._state.torques[path] = _TorqueHistory(support=support)

    def _recording_body_domain(self):
        # Existing receipts and cursors prove constant angular rate only.
        return False

    def _recording_root_body(self, path, state):
        return None

    def recording_stationary_frames(self, carriers, first, last, side="after"):
        self.a.tick()
        return {}

    def recording_pose_enclosures(self, carriers, time, side="after", *, ideal=True,
                                  recording_context=None):
        return super().recording_pose_enclosures(carriers, time, side, ideal=ideal,
                                                 recording_context=None)

    def _copy_state(self, state):
        entries = sum(49 + len(h.active) * 14 + len(h.changes) * 15
                      for h in state.torques.values())
        if entries * (len(self._times) + 1) > 100000:
            raise ReferenceError("resource", "Independent torque history exceeds its retained-state bound")
        for _ in range(entries):
            self.a.tick()
        return super()._copy_state(state)

    def _next(self, state, current):
        inherited = super()._next(state, current)
        times = [] if inherited is None else [inherited]
        for history in state.torques.values():
            for payload, start in history.active.values():
                self.a.tick()
                end = self.a.exact(start, payload.duration, "add")
                if end > current:
                    times.append(end)
        return min(times) if times else None

    def _build(self):
        time, previous = F(0), F(0)
        while True:
            self.a.tick()
            if len(self._times) >= MAX_BOUNDARIES:
                raise ReferenceError("resource", "Independent torque semantic boundary cap exceeded")
            self._certify_prefix(self._state, previous, time)
            if self.mode == "recording":
                # This is a conservative bounded preflight for complete new
                # histories. Exact projected membership is checked afterward.
                weight = self._boundary_weight(time)
                weight += sum(40 + 32 * (len(h.active) + len(h.changes))
                              for h in self._state.torques.values())
                self._history_weight += weight
                if self._history_weight > 100000:
                    raise ReferenceError("resource", "Independent torque boundary histories exceed 100000 records")
            before = self._state
            if time == self.end and self.end_side == "before":
                self._times.append(time)
                self._before.append(before)
                self._after.append(None)
                self._release_records[time] = ()
                break
            completions, _, _, _ = self._coordinate_boundary_plan(time)
            staged = self._copy_state(before)
            releases = []
            for path in completions:
                self.a.tick()
                self._finish(path, time, staged, "completed")
            for history in staged.forces.values():
                for key in sorted(tuple(history.active)):
                    self.a.tick()
                    payload, start = history.active[key]
                    if self.a.exact(start, payload.duration, "add") == time:
                        del history.active[key]
                        history.completed += 1
                        self._force_change(history, time, "completed", (payload, start))
            for history in staged.torques.values():
                for key in sorted(tuple(history.active)):
                    self.a.tick()
                    payload, start = history.active[key]
                    if self.a.exact(start, payload.duration, "add") == time:
                        del history.active[key]
                        history.completed += 1
                        self._torque_change(history, time, "completed", (payload, start))
            touched = set()
            if self._event_index < len(self.model.events) and self.model.events[self._event_index].time == time:
                for index, event in enumerate(self.model.events[self._event_index].events):
                    self.a.tick()
                    self._event(event, index, time, staged, before, touched, releases)
                self._event_index += 1
            for path in staged.forces:
                self._aggregate(path, time, staged)
            for path in sorted(staged.torques):
                self._aggregate_torque(path, time, staged)
            self.a.tick()
            self._state = staged
            self._times.append(time)
            self._before.append(before)
            self._after.append(staged)
            self._release_records[time] = tuple(releases)
            if time == self.end:
                break
            following = self._next(staged, time)
            if following is None or following > self.end:
                following = self.end
            if following <= time:
                raise ReferenceError("source_admission", "Independent torque ledger failed to advance")
            previous, time = time, following

    def _torque_change(self, history, time, kind, active):
        self.a.tick()
        if history.last_time != time:
            history.last_time, history.changes = time, []
        history.changes.append((kind, active))

    def _axis_check(self, vector, axis, reason, support):
        self.a.tick()
        index = AXES[axis].index(1)
        for position, value in enumerate(vector):
            value = self.a.interval(value)
            # Canonical source arithmetic supplies this exact support. The
            # separate interval may be wide, or enclose a smooth law that the
            # fixed source grid rounds to zero; it is never an axis predicate.
            if position != index and support[position]:
                raise ReferenceError("source_admission", "Independent torque angular state has no exact zero-axis proof",
                                     torque_reason=reason, expected_axis=axis)
        return self.a.interval(vector[index])

    def _event(self, event, sequence_index, time, state, incoming, touched, releases):
        if event.kind != "torque":
            return super()._event(event, sequence_index, time, state, incoming, touched, releases)
        self.a.tick()
        self._dynamic_admission(event.target, state)
        payload = event.torque
        if payload is None or payload.axis not in AXES or payload.duration <= 0:
            raise ReferenceError("source_admission", "Independent torque payload is invalid")
        history = state.torques[event.target]
        if payload.key in history.active:
            raise ReferenceError("source_admission", "Independent torque key is already active")
        if history.axis is not None and history.axis != payload.axis:
            raise ReferenceError("source_admission", "Independent torque axis lock changed", torque_reason="axis_lock")
        actual = self._root_pose(event.target, time, state, ideal=False)
        support = axis_reference.root_support(self, event.target, time, state)
        speed = self._axis_check(actual.omega, payload.axis, "incoming_axis", support.omega)
        if history.axis is None:
            basis = self._source_basis(event.target + ".frame", time, time, state)
            history.axis = payload.axis
            history.reference = _ReferenceOrigin(time, actual.orientation, speed, F(0),
                basis.rotation_error, basis.omega_error, basis.rotation_error, basis.omega_error)
        history.active[payload.key] = (copy.deepcopy(payload), time)
        history.started += 1
        self._torque_change(history, time, "started", history.active[payload.key])
        self._poses.clear()
        self._basis_cache.clear()

    def _impulse(self, event, time, state, touched):
        history = state.torques[event.target]
        original_support = history.support
        support = axis_reference.root_support(self, event.target, time, state)
        exact_w = exact_axis.exposed_vector(support.exact_omega, self.a)
        lever = exact_axis.exposed_vector(exact_axis.rotated(
            support.exact_quaternion, event.impulse.point_self_m, self.a), self.a)
        exact_angular = exact_axis.exposed_vector(exact_axis.cross(
            lever, event.impulse.impulse_world_n_s, self.a), self.a)
        exact_w = exact_axis.exposed_vector((self.a.exact(before,
            self.a.exact(delta,self.model.objects[event.target].inertia,"div"),"add")
            for before,delta in zip(exact_w,exact_angular)),self.a)
        before_actual = self._root_pose(event.target, time, state, ideal=False)
        before_ideal = self._root_pose(event.target, time, state, ideal=True)
        exact_transfer = self._coordinate_impulse(event, time, state, before_actual)
        super()._impulse(event, time, state, touched)
        if not any(event.impulse.impulse_world_n_s):
            # The inherited row/count is real, but a zero impulse does not
            # materialize or reanchor either trajectory. In particular the
            # legacy COM anchor's omega is not the current split angular law.
            return
        if exact_transfer is not None and any(event.impulse.impulse_world_n_s):
            actual, position_error, rotation_error, velocity_error, omega_error = exact_transfer
            anchor = state.dynamic[event.target]
            state.dynamic[event.target] = replace(anchor, actual=actual,
                position_error=position_error, rotation_error=rotation_error,
                velocity_error=velocity_error, omega_error=omega_error)
            self._poses.clear()
            self._basis_cache.clear()
        omega_support = axis_reference.constants(exact_w)
        # Legacy impulses materialize the complete public rotation even when
        # their angular delta cancels. The split law retains its own private
        # rotation and only a genuinely changed speed reanchors that law.
        updated_support = (axis_reference.materialize(support, self.a)
                           if history.rotation is None else support)
        updated_support = replace(updated_support, time=time,
                                  omega=omega_support, exact_omega=exact_w)
        history.support = updated_support
        if history.axis is None:
            return
        self.a.tick()
        anchor = state.dynamic[event.target]
        self._axis_check(anchor.actual.omega, history.axis, "impulse_axis", omega_support)
        index = AXES[history.axis].index(1)
        actual_speed = self.a.point(exact_w[index])
        # A source interval's width is not a canonical change. In particular,
        # R*0 and an independently reconstructed exact zero cross product keep
        # every already exposed canonical speed unchanged. The angular origin
        # must remain its original complete controlled expression in that case.
        angular_changed = exact_w != support.exact_omega
        if history.rotation is not None and not angular_changed:
            history.support = original_support
        # Every nonzero impulse transports the separate shadow and complete
        # inherited uncertainty, even when its canonical angular impulse is
        # zero. Optional enclosure width is not promoted to a mandatory lower
        # error requirement: retain the independently proved requirement and
        # propagate the whole upper transfer radius in the reference bound.
        theta_error, speed_error = self._shadow_bounds(history, time)
        required_theta, required_speed = self._required_shadow(history, time)
        reference_acceleration = history.reference.acceleration
        history.reference = _ReferenceOrigin(time, before_ideal.orientation,
            anchor.ideal.omega[index], reference_acceleration,
            self.a.exact(theta_error, anchor.rotation_error, "add"),
            self.a.exact(speed_error, anchor.omega_error, "add"),
            required_theta, required_speed)
        if history.rotation is not None and angular_changed:
            history.pending_angular = (time, before_actual.orientation, actual_speed,
                before_ideal.orientation, anchor.ideal.omega[index], F(0), F(0))
        self._poses.clear()
        self._basis_cache.clear()

    def _release(self, event, index, time, state, incoming, touched, releases):
        joint = self.model.joints.get(event.target)
        if joint is None or joint.kind != "grip" or event.target not in state.grips:
            return super()._release(event, index, time, state, incoming, touched, releases)
        child = self.model.sites[joint.child].owner
        support = axis_reference.frame_support(self, child + ".frame", time, incoming)
        super()._release(event, index, time, state, incoming, touched, releases)
        state.torques[child].support = axis_reference.materialize(support, self.a)

    def _finish(self, path, time, state, status):
        action = self.model.actions[path]
        support = (axis_reference.root_support(self, action.target, time, state)
                   if action.kind == "spin" else None)
        super()._finish(path, time, state, status)
        if support is not None:
            state.torques[action.target].support = replace(
                axis_reference.materialize(support, self.a),
                omega=axis_reference.ZERO, exact_omega=(F(0),)*3)

    def _aggregate(self, path, time, state):
        support = (axis_reference.root_support(self, path, time, state)
                   if state.modes[path] == "dynamic" else None)
        original = state.dynamic.get(path)
        previous_acceleration = state.forces[path].acceleration or tuple(self.model.gravity)
        super()._aggregate(path, time, state)
        if (support is not None and state.dynamic[path] is not original
                and state.torques[path].rotation is None):
            if state.forces[path].acceleration != previous_acceleration:
                state.torques[path].support = axis_reference.materialize(support, self.a)
            # Equal canonical acceleration moves only the independent error
            # clock. Retain the entire older source origin, not the sampled
            # quaternion at this error boundary.

    def _coordinate_impulse(self, event, time, state, current):
        """Resolve an exact coordinate rotation without a fictitious cell width.

        The general inherited oracle deliberately expands all three angular
        components before an impulse. Its resulting L1 enclosure is sound,
        but is not a lower bound on the canonical source's error certificate.
        For an exactly reconstructed signed coordinate quaternion and point
        input cells, the controlled impulse outputs are uniquely determined.
        Reconstruct that finite expression from source operands and derive the
        documented transfer radius directly. No producer object or reported
        error is an input. All other rotations retain the general enclosure.

        A coordinate rotation is a sign permutation with coefficients 0/1;
        its private 96-bit vector projection is exact only for admitted grid
        operands. Cross products and final mass/inertia quotients are exact
        rationals followed by one binary64 nearest-even exposure.
        """
        self.a.tick()
        payload = event.impulse
        if payload is None:
            return None
        vectors = (current.position, current.orientation, current.velocity, current.omega)
        if any(type(cell) is not Interval or cell.lo != cell.hi
               for vector in vectors for cell in vector):
            return None
        q = tuple(cell.lo for cell in current.orientation)
        if len(q) != 4 or sum(value != 0 for value in q) != 1 or max(map(abs, q)) != 1:
            return None
        point = tuple(F(value) for value in payload.point_self_m)
        impulse = tuple(F(value) for value in payload.impulse_world_n_s)
        if any(value.denominator > 1 << 96 or value.denominator & (value.denominator - 1)
               for value in point):
            return None
        self.a.guard(*q, *point, *impulse,
                     *(cell.lo for vector in vectors for cell in vector))
        exact = self.a.exact
        add, mul = self.a.exact_sum, self.a.exact_product
        exposed = lambda value: F(self.a.round64(value))
        actual_position = tuple(exposed(cell.lo) for cell in current.position)
        before_velocity = tuple(exposed(cell.lo) for cell in current.velocity)
        before_omega = tuple(exposed(cell.lo) for cell in current.omega)
        axis = next(index for index, value in enumerate(q) if value)
        lever = tuple(value if axis == 0 or index == axis - 1 else -value
                      for index, value in enumerate(point))
        angular = tuple(exposed(exact(exact(lever[j], impulse[k], "mul"),
                                      exact(lever[k], impulse[j], "mul"), "sub"))
                        for j, k in ((1, 2), (2, 0), (0, 1)))
        obj = self.model.objects[event.target]
        velocity_law = tuple(add(value, exact(delta, obj.mass, "div"))
                             for value, delta in zip(before_velocity, impulse))
        omega_law = tuple(add(value, exact(delta, obj.inertia, "div"))
                          for value, delta in zip(before_omega, angular))
        velocity = tuple(exposed(value) for value in velocity_law)
        omega = tuple(exposed(value) for value in omega_law)
        before = self._phase(event.target + ".frame", time, time, state)
        l1 = lambda values: add(*(abs(value) for value in values))
        rounding = lambda size: add(mul(size, ROUND_RELATIVE), mul(3, ROUND_TINY))
        lever_error = add(mul(before.source_numeric_rotation_error, l1(point)),
                          F(2, 1 << 96), rounding(l1(lever)))
        angular_error = add(mul(lever_error, l1(impulse)), rounding(l1(angular)))
        velocity_error = add(before.source_numeric_velocity_error,
            l1(tuple(exact(value, law, "sub") for value, law in zip(velocity, velocity_law))))
        omega_error = add(before.source_numeric_angular_velocity_error,
            exact(angular_error, obj.inertia, "div"),
            l1(tuple(exact(value, law, "sub") for value, law in zip(omega, omega_law))))
        actual = PoseEnclosure(self.p.vector(actual_position), current.orientation,
                               self.p.vector(velocity), self.p.vector(omega))
        return (actual, before.source_numeric_position_error,
                before.source_numeric_rotation_error, velocity_error, omega_error)

    def _round_cell(self, cell):
        cell = self.a.interval(cell)
        low, high = self.a.round64(cell.lo), self.a.round64(cell.hi)
        return Interval(F(low), F(high))

    def _polynomial(self, speed, acceleration, elapsed):
        speed = self.a.interval(speed)
        u = F(elapsed)
        squared = self.a.exact(u, u, "mul")
        curved = self.a.exact(self.a.exact(acceleration, squared, "mul"), 2, "div")
        delta = self.a.exact(acceleration, u, "mul")
        phases = [self.a.exact(self.a.exact(value, u, "mul"), curved, "add")
                  for value in (speed.lo, speed.hi)]
        rates = [self.a.exact(value, delta, "add") for value in (speed.lo, speed.hi)]
        return Interval(min(phases), max(phases)), Interval(min(rates), max(rates))

    def _axis_rotation(self, orientation, axis, phase):
        phase = self.a.interval(phase)
        if phase.lo == phase.hi == 0:
            return orientation
        # Signed phase is explicit, avoiding an unresolved norm near zero.
        rotation = self.p.hinge(AXES[axis], phase, 0, ideal=True).orientation
        return self.p.multiply(rotation, orientation)

    def _general_spin(self, omega, elapsed):
        values = tuple(self.a.interval(value) for value in omega)
        nonzero = [i for i, value in enumerate(values) if value.lo != 0 or value.hi != 0]
        if len(nonzero) <= 1:
            if not nonzero or elapsed == 0:
                return self.p.vector((1, 0, 0, 0))
            index = nonzero[0]
            axis = tuple(int(i == index) for i in range(3))
            return self.p.hinge(axis, self.a.mul(values[index], elapsed), 0, ideal=True).orientation
        try:
            return self.p.spin(values, elapsed)
        except ReferenceError as error:
            if (getattr(self.a.work, "callback_error", None) is error
                    or str(error) != "Independent spin norm is unresolved"):
                raise
            radius = self.a.exact(self._l1(values), abs(elapsed), "mul")
            if radius > 1:
                raise
            half = self.a.exact(radius, 2, "div")
            cosine_error = self.a.exact(self.a.exact(radius, radius, "mul"), 8, "div")
            return (Interval(1 - cosine_error, F(1)), *(Interval(-half, half) for _ in range(3)))

    def _root_pose(self, path, time, state, *, ideal, pose_only=False):
        if state.modes[path] != "dynamic":
            return super()._root_pose(path, time, state, ideal=ideal, pose_only=pose_only)
        anchor = state.dynamic[path]
        saved = anchor.ideal if ideal else anchor.actual
        elapsed = self.a.exact(time, anchor.time, "sub")
        acceleration = ((state.forces[path].ideal_acceleration if ideal else state.forces[path].acceleration)
                        or self.model.gravity)
        square_half = self.a.exact(self.a.exact(elapsed, elapsed, "mul"), 2, "div")
        position = self.p.add(self.p.add(saved.position, self.p.scale(saved.velocity, elapsed)),
                              self.p.scale(acceleration, square_half))
        history = state.torques[path]
        pending = history.pending_angular
        if pending is not None and pending[0] == time:
            orientation, speed = (pending[3], pending[4]) if ideal else (pending[1], pending[2])
            omega = self.p.scale(AXES[history.axis], speed)
        elif ideal and history.reference is not None:
            reference = history.reference
            dt = self.a.exact(time, reference.time, "sub")
            phase, speed = self._polynomial(reference.speed, reference.acceleration, dt)
            orientation = self._axis_rotation(reference.orientation, history.axis, phase)
            omega = self.p.scale(AXES[history.axis], speed)
        elif not ideal and history.rotation is not None:
            rotation = history.rotation
            dt = self.a.exact(time, rotation.time, "sub")
            phase, speed = self._polynomial(rotation.speed, history.acceleration, dt)
            phase, speed = self._round_cell(phase), self._round_cell(speed)
            orientation = self._axis_rotation(rotation.orientation, history.axis, phase)
            omega = self.p.scale(AXES[history.axis], speed)
        else:
            orientation = self.p.multiply(self._general_spin(saved.omega, elapsed), saved.orientation)
            omega = saved.omega
        velocity = self.p.add(saved.velocity, self.p.scale(acceleration, elapsed))
        if pose_only:
            zero = self.p.vector(ZERO)
            return PoseEnclosure(position, orientation, zero, zero)
        return PoseEnclosure(position, orientation, velocity, omega)

    def _shadow_bounds(self, history, time):
        reference = history.reference
        if reference is None:
            return F(0), F(0)
        dt = abs(self.a.exact(time, reference.time, "sub"))
        discrepancy = abs(self.a.exact(history.acceleration, reference.acceleration, "sub"))
        dw = self.a.exact(discrepancy, dt, "mul")
        theta = self.a.exact_sum(reference.theta_error,
            self.a.exact(reference.speed_error, dt, "mul"),
            self.a.exact_product(discrepancy, dt, dt, F(1, 2)))
        return theta, self.a.exact(reference.speed_error, dw, "add")

    def _required_shadow(self, history, time):
        reference = history.reference
        dt = abs(self.a.exact(time, reference.time, "sub"))
        discrepancy = abs(self.a.exact(history.acceleration, reference.acceleration, "sub"))
        return (self.a.exact_sum(reference.required_theta,
                    self.a.exact_product(reference.required_speed, dt),
                    self.a.exact_product(discrepancy, dt, dt, F(1, 2))),
                self.a.exact_sum(reference.required_speed, self.a.exact_product(discrepancy, dt)))

    def _aggregate_torque(self, path, time, state):
        history = state.torques[path]
        if history.axis is None:
            return
        self.a.tick()
        total = F(0)
        for key in sorted(history.active):
            self.a.tick()
            total = self.a.exact(total, history.active[key][0].torque_n_m, "add")
        net = self.a.round64(total)
        inertia = F(self.model.objects[path].inertia)
        canonical = self.a.round64(self.a.exact(net, inertia, "div"))
        reference_acceleration = self.a.exact(total, inertia, "div")
        pending = history.pending_angular is not None
        change = canonical != history.acceleration or pending
        support = axis_reference.root_support(self, path, time, state) if change else None
        reference_change = reference_acceleration != history.reference_acceleration or change
        if reference_change:
            actual = self._root_pose(path, time, state, ideal=False)
            ideal = self._root_pose(path, time, state, ideal=True)
            theta_error, speed_error = self._shadow_bounds(history, time)
            required_theta, required_speed = self._required_shadow(history, time)
            if pending:
                theta_error = self.a.exact(theta_error, history.pending_angular[5], "add")
                speed_error = self.a.exact(speed_error, history.pending_angular[6], "add")
            if change and (history.rotation is not None or canonical != 0):
                self.a.tick()
                if history.rotation is not None:
                    dt = self.a.exact(time, history.rotation.time, "sub")
                    phase, speed = self._polynomial(history.rotation.speed, history.acceleration, dt)
                    if phase.lo == phase.hi:
                        residual = abs(self.a.exact(self.a.round64(phase.lo), phase.lo, "sub"))
                        required_theta = self.a.exact(required_theta, residual, "add")
                    if speed.lo == speed.hi:
                        residual = abs(self.a.exact(self.a.round64(speed.lo), speed.lo, "sub"))
                        required_speed = self.a.exact(required_speed, residual, "add")
                    theta_error = self.a.exact_sum(theta_error,
                        self.a.exact_product(phase.magnitude, ROUND_RELATIVE), ROUND_TINY,
                        AXIS_ERROR, PRODUCT_ERROR)
                    speed_error = self.a.exact_sum(speed_error,
                        self.a.exact_product(speed.magnitude, ROUND_RELATIVE), ROUND_TINY)
                signed = self.a.point(support.exact_omega[AXES[history.axis].index(1)])
                history.rotation = _RotationOrigin(time, actual.orientation, signed, theta_error, speed_error)
            self.a.tick()
            history.reference = _ReferenceOrigin(time, ideal.orientation,
                ideal.omega[AXES[history.axis].index(1)], reference_acceleration, theta_error, speed_error,
                required_theta, required_speed)
        history.net = net
        history.acceleration = canonical
        history.reference_acceleration = reference_acceleration
        history.pending_angular = None
        if support is not None:
            omega_support = tuple(possible or bool(canonical and axis)
                                  for possible, axis in zip(support.omega, AXES[history.axis]))
            history.support = replace(support, time=time, omega=omega_support)
        self._poses.clear()
        self._basis_cache.clear()

    def _phase_extrema(self, history, start, end):
        origin = history.rotation
        if origin is None:
            return F(0), F(0)
        times = [self.a.exact(start, origin.time, "sub"), self.a.exact(end, origin.time, "sub")]
        if history.acceleration:
            for speed in (origin.speed.lo, origin.speed.hi):
                vertex = self.a.exact(-speed, history.acceleration, "div")
                if times[0] < vertex < times[1]:
                    times.append(vertex)
        values = [self._polynomial(origin.speed, history.acceleration, dt) for dt in times]
        return max(p.magnitude for p, _ in values), max(w.magnitude for _, w in values)

    def _certify_prefix(self, state, start, end):
        for history in state.torques.values():
            if history.rotation is not None:
                self.a.tick()
                phase, _ = self._phase_extrema(history, start, end)
                if phase > PHASE_LIMIT:
                    raise ReferenceError("numeric", "Independent torque phase exceeds the complete segment domain",
                                         torque_reason="phase_domain")

    def _phase_root_poses(self, path, time, state):
        if state.torques[path].axis is not None:
            return (self._root_pose(path, time, state, ideal=False),
                    self._root_pose(path, time, state, ideal=True))
        return super()._phase_root_poses(path, time, state)

    def _affected_root(self, carrier, state):
        root, _, _, path = self._ancestry(carrier, state)
        if root is None or state.torques[root].axis is None:
            return None
        for entry in path:
            self.a.tick()
            if self.mode == "recording" and entry in self.model.joints:
                raise ReferenceError("unsupported", "Torque recording requires fixed rigid marker paths.",
                                     export_code="OKE-E-TORQUE-COMPOSITION", carrier=root, frame=carrier)
            stem = entry.removesuffix(".frame")
            if self.mode == "recording" and stem in self.model.objects and any((stem, key) in state.claims
                                                   for key in ("translation", "orientation")):
                raise ReferenceError("unsupported", "Torque recording requires fixed rigid marker paths.",
                                     export_code="OKE-E-TORQUE-COMPOSITION", carrier=root, frame=carrier)
        return root

    def _axial_derivatives(self, carrier, start, end, state):
        if self._affected_root(carrier, state) is not None:
            return None
        return super()._axial_derivatives(carrier, start, end, state)

    def _phase(self, carrier, start, end, state):
        self._affected_root(carrier, state)
        return super()._phase(carrier, start, end, state)

    def _dynamic_source_basis(self, path, start, end, state, bound):
        history = state.torques[path]
        if history.axis is None:
            return bound
        reference = history.reference
        ideal_rates = [self._polynomial(reference.speed, reference.acceleration,
                        self.a.exact(t, reference.time, "sub"))[1] for t in (start, end)]
        omega = max(rate.magnitude for rate in ideal_rates)
        alpha = abs(reference.acceleration)
        theta, speed_error = self._shadow_bounds(history, end)
        theta = max(theta, self._shadow_bounds(history, start)[0])
        if history.rotation is None:
            return replace(bound, omega=omega, alpha=alpha,
                anchor_rotation=self.a.exact(bound.anchor_rotation, theta, "add"),
                rotation_error=self.a.exact(bound.rotation_error, theta, "add"),
                omega_error=self.a.exact(bound.omega_error, speed_error, "add"))
        phase, actual_speed = self._phase_extrema(history, start, end)
        if phase > PHASE_LIMIT:
            raise ReferenceError("numeric", "Independent torque phase exceeds the complete segment domain",
                                 torque_reason="phase_domain")
        phase_round = self.a.exact_sum(self.a.exact_product(phase, ROUND_RELATIVE), ROUND_TINY)
        rotation_error = self.a.exact_sum(theta, phase_round, AXIS_ERROR, PRODUCT_ERROR, EXPOSED_ERROR)
        speed_error = self.a.exact_sum(speed_error,
            self.a.exact_product(actual_speed, ROUND_RELATIVE), ROUND_TINY)
        return replace(bound, omega=omega, alpha=alpha, actual_omega=actual_speed,
                       anchor_rotation=theta, rotation_error=rotation_error,
                       omega_error=speed_error, trig=int(bool(phase)), products=3 if phase else 1)

    def _torque_record(self, path, active):
        self.a.tick()
        payload, start = active
        return {"torque_key": payload.key,
            "torque_element_id": [self.model.module_key, self.model.scene_key, "torque", payload.key],
            "target_path": path, "target_element_id": list(self.model.objects[path].element_id),
            "program_revision": self.model.program_revision, "source_location": dict(payload.source),
            "sequence_index": payload.sequence_index, "activation_time_seconds": _time_text(start),
            "duration_seconds": _time_text(payload.duration),
            "completion_time_seconds": _time_text(self.a.exact(start, payload.duration, "add")),
            "axis": payload.axis, "torque_n_m": payload.torque_n_m,
            "operand_location": dict(payload.operand_source), "duration_location": dict(payload.duration_source)}

    def _rational(self, value):
        self.a.tick()
        value = F(value)
        self.a.guard(value)
        return {"numerator": str(value.numerator), "denominator": str(value.denominator)}

    def _torques(self, path, time, state):
        self.a.tick()
        history = state.torques[path]
        axis, rotation = history.axis, history.rotation
        speed = phase = None
        if axis is not None:
            if rotation is None:
                support = axis_reference.root_support(self, path, time, state)
                speed = self.a.point(support.exact_omega[AXES[axis].index(1)])
            else:
                phase, speed = self._polynomial(rotation.speed, history.acceleration,
                                                self.a.exact(time, rotation.time, "sub"))
                phase, speed = self._round_cell(phase), self._round_cell(speed)
        theta_error, speed_error = (self._required_shadow(history, time) if axis is not None else (F(0), F(0)))
        if axis is not None:
            # Every exposed rotation includes the inherited publication term.
            # A point projection adds the actual scalar RN discrepancy, not
            # the larger uniform whole-phase allowance used by certificates.
            theta_error = self.a.exact(theta_error, EXPOSED_ERROR, "add")
            if rotation is not None:
                smooth_phase, smooth_speed = self._polynomial(rotation.speed, history.acceleration,
                    self.a.exact(time, rotation.time, "sub"))
                if smooth_phase.lo == smooth_phase.hi:
                    theta_error = self.a.exact(theta_error,
                        abs(self.a.exact(self.a.round64(smooth_phase.lo), smooth_phase.lo, "sub")), "add")
                if smooth_speed.lo == smooth_speed.hi:
                    speed_error = self.a.exact(speed_error,
                        abs(self.a.exact(self.a.round64(smooth_speed.lo), smooth_speed.lo, "sub")), "add")
        return {"active": [self._torque_record(path, history.active[key]) for key in sorted(history.active)],
            "net_torque_n_m": history.net,
            "angular_acceleration_rad_per_s2": None if axis is None else history.acceleration,
            "axis": axis, "rotation_route": "legacy" if rotation is None else "split",
            "rotation_anchor_seconds": None if rotation is None else _time_text(rotation.time),
            "signed_angular_speed_rad_per_s": speed, "phase_since_anchor_rad": phase,
            "angular_acceleration_reference_rad_per_s2": None if axis is None else self._rational(history.reference_acceleration),
            "angular_error_bound_rad": None if axis is None else TorqueErrorRequirement(theta_error),
            "angular_speed_error_bound_rad_per_s": None if axis is None else TorqueErrorRequirement(speed_error),
            "started_count": history.started, "completed_count": history.completed,
            "last_change_time_seconds": None if history.last_time is None else _time_text(history.last_time),
            "last_changes": [{"kind": kind, **self._torque_record(path, active)}
                             for kind, active in history.changes]}

    def sample(self, time, side="after"):
        result = super().sample(time, side)
        state = self._state_at(F(time), side)
        for path, record in result["objects"].items():
            record["torques"] = self._torques(path, F(time), state)
        return result

    def _boundary_projection(self, time, side):
        result = super()._boundary_projection(time, side)
        state = self._state_at(time, side)
        result["torque_states"] = {path: self._torques(path, time, state) for path in self.model.objects}
        return result

    def boundary_states(self):
        if self.mode != "recording" or self.end_side != "after":
            raise ReferenceError("unsupported", "Complete torque histories require recording and the final after-side")
        records, weight = [], 0
        for time in self.boundaries:
            self.a.tick()
            record = {"source_seconds": _time_text(time),
                      "incoming_releases": copy.deepcopy(list(self._release_records[time]))}
            for side in ("before", "after"):
                projection = self._boundary_projection(time, side)
                for name, value in projection.items():
                    record[name + "_" + side] = value
            weight += self._logical_entries(record)
            if weight > 100000:
                raise ReferenceError("resource", "Independent complete torque histories exceed 100000 records")
            records.append(record)
        return records
