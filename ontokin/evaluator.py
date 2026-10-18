"""Headless analytical evaluation of the OntoKin ``core-0.1`` profile.

The clock is rational, so a source event and a natural action endpoint cannot
change order through accumulated floating-point clock error. Motion is evaluated
from its initial conditions, without a simulation step size. Quaternions use
``(w, x, y, z)`` order and angular velocities use world axes.

The public functions create a fresh run. Repeating an inspection therefore
cannot advance the scene or retain action state from an earlier request.
"""

from __future__ import annotations

import copy
import math
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from itertools import groupby
from typing import Any, Callable, Iterable

from .diagnostics import OntoKinError
from .model import ActionModel, Pose, Quat, SceneModel, Vec


ZERO: Vec = (0.0, 0.0, 0.0)
IDENTITY: Quat = (1.0, 0.0, 0.0, 0.0)
MAX_SAMPLES = 1000
MAX_OUTPUT_RECORDS = 100000
IMPULSE_PROFILE = "impulse-0.1"


class _NumericFault(Exception):
    """A requested exposed state cannot be represented by finite binary64."""


def _f(value: float | int) -> Fraction:
    return Fraction(value)


def _round(value: Fraction) -> float:
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise _NumericFault("A state component exceeds the finite binary64 range.") from exc
    if not math.isfinite(result):
        raise _NumericFault("A state component is not finite.")
    return 0.0 if result == 0.0 else result


def _add(a: Vec, b: Vec) -> Vec:
    return tuple(_round(_f(x) + _f(y)) for x, y in zip(a, b))  # type: ignore[return-value]


def _neg(a: Vec) -> Vec:
    return tuple(-x if x else 0.0 for x in a)  # type: ignore[return-value]


def _scale(a: Vec, factor: float | Fraction) -> Vec:
    factor = Fraction(factor)
    return tuple(_round(_f(x) * factor) for x in a)  # type: ignore[return-value]


def _cross(a: Vec, b: Vec) -> Vec:
    ax, ay, az = map(_f, a)
    bx, by, bz = map(_f, b)
    return (_round(ay * bz - az * by), _round(az * bx - ax * bz),
            _round(ax * by - ay * bx))


def _unit_quaternion(q: Quat) -> Quat:
    length = math.hypot(*q)
    if not math.isfinite(length) or length == 0:
        raise _NumericFault("A calculated orientation is not a finite proper rotation.")
    result = tuple(x / length for x in q)
    first = next((x for x in result if x != 0), 1.0)
    if first < 0:
        result = tuple(-x for x in result)
    return tuple(0.0 if x == 0 else x for x in result)  # type: ignore[return-value]


def _multiply(a: Quat, b: Quat) -> Quat:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return _unit_quaternion((aw * bw - ax * bx - ay * by - az * bz,
                             aw * bx + ax * bw + ay * bz - az * by,
                             aw * by - ax * bz + ay * bw + az * bx,
                             aw * bz + ax * by - ay * bx + az * bw))


def _inverse(q: Quat) -> Quat:
    return (q[0], -q[1], -q[2], -q[3])


def _rotate(q: Quat, v: Vec) -> Vec:
    # Form each dot product as a rational sum. This avoids an intermediate
    # overflow when large products cancel to a finite exposed coordinate.
    w, x, y, z = map(_f, _unit_quaternion(q))
    rows = ((1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
            (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
            (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)))
    values = tuple(map(_f, v))
    return tuple(_round(sum((a * b for a, b in zip(row, values)), Fraction(0)))
                 for row in rows)  # type: ignore[return-value]


def _axis_rotation(axis: Vec, angle: float) -> Quat:
    if not math.isfinite(angle):
        raise _NumericFault("A calculated rotation angle is not finite.")
    half = angle / 2
    sine = math.sin(half)
    return _unit_quaternion((math.cos(half), *(component * sine for component in axis)))


def _spin_rotation(omega: Vec, elapsed: Fraction) -> Quat:
    if omega == ZERO or elapsed == 0:
        return IDENTITY
    # Scaling also handles finite vectors whose Euclidean magnitude would
    # overflow a binary64 intermediate.
    maximum = max(abs(value) for value in omega)
    scaled = tuple(value / maximum for value in omega)
    scaled_norm = math.hypot(*scaled)
    axis = tuple(value / scaled_norm for value in scaled)
    angle = _round(_f(maximum) * _f(scaled_norm) * elapsed)
    return _axis_rotation(axis, angle)  # type: ignore[arg-type]


def _advance_orientation(initial: Quat, omega: Vec, elapsed: Fraction) -> Quat:
    # In particular, a release sample at elapsed=0 preserves the saved
    # orientation projections without an extra normalization/rounding step.
    if omega == ZERO or elapsed == 0:
        return initial
    return _multiply(_spin_rotation(omega, elapsed), initial)


def _affine(initial: Vec, rate: Vec, elapsed: Fraction) -> Vec:
    return tuple(_round(_f(p) + _f(v) * elapsed) for p, v in zip(initial, rate))  # type: ignore[return-value]


@dataclass(frozen=True)
class _Kinematics:
    position: Vec = ZERO
    orientation: Quat = IDENTITY
    velocity: Vec = ZERO
    omega: Vec = ZERO


def _compose(parent: _Kinematics, local: _Kinematics) -> _Kinematics:
    """Compose poses and spatial velocities, including the offset term."""
    offset = _rotate(parent.orientation, local.position)
    velocity = _add(_add(parent.velocity, _cross(parent.omega, offset)),
                    _rotate(parent.orientation, local.velocity))
    return _Kinematics(_add(parent.position, offset),
                       _multiply(parent.orientation, local.orientation), velocity,
                       _add(parent.omega, _rotate(parent.orientation, local.omega)))


def _constant_pose(pose: Pose) -> _Kinematics:
    return _Kinematics(pose.position, pose.rotation)


def _inverse_pose(pose: Pose) -> _Kinematics:
    rotation = _inverse(pose.rotation)
    return _Kinematics(_rotate(rotation, _neg(pose.position)), rotation)


def exact_time(value: Fraction | float | int | str | Decimal) -> Fraction:
    """Read protocol decimals exactly; a Python float keeps its binary64 value."""
    try:
        if isinstance(value, bool):
            raise ValueError("Boolean values are not timestamps.")
        if isinstance(value, Fraction):
            result = value
        elif isinstance(value, str):
            if len(value) > 4096:
                raise OntoKinError("OKL-E-RESOURCE", "The timestamp exceeds the 4096-digit inspection budget.",
                                   category="resource_limit", phase="inspection", blocks=[])
            if re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value) is None:
                raise ValueError("A timestamp must be a decimal string.")
            decimal = Decimal(value)
            if not decimal.is_finite():
                raise ValueError("Timestamps must be finite.")
            if decimal.adjusted() > 308:
                raise ValueError("A timestamp cannot exceed the finite scene horizon.")
            if len(decimal.as_tuple().digits) + max(0, -decimal.as_tuple().exponent) > 4096:
                raise OntoKinError("OKL-E-RESOURCE", "The timestamp exceeds the 4096-digit inspection budget.",
                                   category="resource_limit", phase="inspection", blocks=[])
            result = Fraction(decimal)
        elif isinstance(value, Decimal):
            return exact_time(str(value))
        elif isinstance(value, (float, int)):
            result = Fraction(value)
        else:
            raise ValueError("Use an exact decimal string for a timestamp.")
        if max(result.numerator.bit_length(), result.denominator.bit_length()) > 16384:
            raise OntoKinError("OKL-E-RESOURCE", "The timestamp exceeds the inspection arithmetic budget.",
                               category="resource_limit", phase="inspection", blocks=[])
        # An exact protocol timestamp must have a finite decimal expansion.
        time_text(result)
        return result
    except (ValueError, TypeError, OverflowError, InvalidOperation) as exc:
        raise OntoKinError("OKL-E-SAMPLE", "Invalid sample time; use a finite decimal string.",
                           phase="inspection", blocks=[],
                           repair="Supply a time within the declared scene duration.") from exc


def time_text(time: Fraction) -> str:
    """Serialize rational binary64/decimal timestamps without clock rounding."""
    numerator, denominator = time.numerator, time.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError("A timestamp must have a finite exact decimal representation.")
    places = max(twos, fives)
    sign = "-" if numerator < 0 else ""
    integer = abs(numerator) * 2 ** (places - twos) * 5 ** (places - fives)
    if places == 0:
        return sign + str(integer)
    digits = str(integer).rjust(places + 1, "0")
    return (sign + digits[:-places] + "." + digits[-places:]).rstrip("0").rstrip(".")


@dataclass
class _ActionState:
    status: str = "pending"
    elapsed: Fraction = Fraction(0)
    running_since: Fraction = Fraction(0)
    initial: Any = None

    def elapsed_at(self, time: Fraction) -> Fraction:
        return self.elapsed + (time - self.running_since if self.status == "running" else 0)


@dataclass
class _DynamicInitial:
    time: Fraction
    state: _Kinematics
    since: Fraction | None = None

    def __post_init__(self) -> None:
        if self.since is None:
            self.since = self.time


@dataclass
class _ImpulseState:
    applied_count: int = 0
    last_time: Fraction | None = None
    last_applications: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class _RunState:
    modes: dict[str, str] = field(default_factory=dict)
    positions: dict[str, Vec] = field(default_factory=dict)
    orientations: dict[str, Quat] = field(default_factory=dict)
    coordinates: dict[str, float] = field(default_factory=dict)
    actions: dict[str, _ActionState] = field(default_factory=dict)
    claims: dict[tuple[str, str], str] = field(default_factory=dict)
    active_grips: set[str] = field(default_factory=set)
    dynamic: dict[str, _DynamicInitial] = field(default_factory=dict)
    impulses: dict[str, _ImpulseState] = field(default_factory=dict)


class _Simulator:
    """Private staged evaluator; a failed event never commits a partial state."""

    def __init__(self, model: SceneModel, check: Callable[[], None] | None = None):
        self.model = model
        # Optional cooperative hook for bounded revision-bound agent work.
        self.check = check
        self.state = _RunState()
        self.events = sorted(model.events, key=lambda block: block.time)
        self.event_index = 0
        self.zero_pending = True
        self.last_boundary = Fraction(0)
        self.boundaries: list[str] = []
        for path, obj in model.objects.items():
            if self.check is not None:
                self.check()
            self.state.modes[path] = obj.motion
            self.state.positions[path] = obj.placement.position
            self.state.orientations[path] = obj.placement.rotation
            if model.profile == IMPULSE_PROFILE:
                self.state.impulses[path] = _ImpulseState()
            if obj.motion == "dynamic":
                self.state.dynamic[path] = _DynamicInitial(Fraction(0), _Kinematics(
                    obj.placement.position, obj.placement.rotation, obj.velocity, obj.omega))
        for path, joint in model.joints.items():
            if self.check is not None:
                self.check()
            if joint.initial is not None:
                self.state.coordinates[path] = joint.initial
            if joint.kind == "grip":
                self.state.active_grips.add(path)
        self.state.actions = {path: _ActionState() for path in model.actions}

    @staticmethod
    def _channel(action: ActionModel) -> tuple[str, str]:
        return (action.target, {"move": "translation", "spin": "orientation", "tween": "coordinate"}[action.kind])

    def _incoming(self, state: _RunState) -> dict[str, tuple[str, str]]:
        relations: dict[str, tuple[str, str]] = {}
        for path, joint in self.model.joints.items():
            if self.check is not None and self.model.profile == IMPULSE_PROFILE:
                self.check()
            if joint.kind != "grip" or path in state.active_grips:
                relations[self.model.sites[joint.child].owner] = ("joint", path)
        for path, follow in self.model.follows.items():
            if self.check is not None and self.model.profile == IMPULSE_PROFILE:
                self.check()
            relations[follow.child] = ("follow", path)
        return relations

    def _coordinate(self, path: str, time: Fraction, state: _RunState) -> tuple[float, float]:
        claim = state.claims.get((path, "coordinate"))
        if claim is None:
            return state.coordinates[path], 0.0
        action = self.model.actions[claim]
        runtime = state.actions[claim]
        elapsed = runtime.elapsed_at(time)
        difference = _f(action.goal) - _f(runtime.initial)
        value = action.goal if elapsed == action.duration else _round(
            _f(runtime.initial) + difference * elapsed / action.duration)
        rate = _round(difference / action.duration) if runtime.status == "running" else 0.0
        return value, rate

    def _dynamic_kinematics(self, path: str, time: Fraction, state: _RunState) -> _Kinematics:
        anchor = state.dynamic[path]
        elapsed = time - anchor.time
        initial = anchor.state
        position = tuple(_round(_f(p) + _f(v) * elapsed + _f(g) * elapsed * elapsed / 2)
                         for p, v, g in zip(initial.position, initial.velocity, self.model.gravity))
        return _Kinematics(position, _advance_orientation(initial.orientation, initial.omega, elapsed),
                           _affine(initial.velocity, self.model.gravity, elapsed), initial.omega)

    def _kinematics(self, time: Fraction, state: _RunState) -> tuple[dict[str, _Kinematics], dict[str, _Kinematics]]:
        incoming = self._incoming(state)
        objects: dict[str, _Kinematics] = {}
        frames: dict[str, _Kinematics] = {"world": _Kinematics()}
        resolving: set[str] = set()

        def frame(path: str) -> _Kinematics:
            if path in frames:
                return frames[path]
            stem = path.removesuffix(".frame")
            if stem in self.model.objects:
                result = instance(stem)
            else:
                site = self.model.sites[stem]
                result = _compose(instance(site.owner), _constant_pose(site.pose))
            frames[path] = result
            return result

        def instance(path: str) -> _Kinematics:
            if path in objects:
                return objects[path]
            if self.check is not None:
                self.check()
            if path in resolving:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "The active pose graph contains a cycle.",
                                   self.model.objects[path].span, category="unsupported", phase="support")
            resolving.add(path)
            if path in incoming:
                kind, relation_path = incoming[path]
                if kind == "follow":
                    follow = self.model.follows[relation_path]
                    result = _compose(frame(follow.parent), _constant_pose(follow.offset))
                else:
                    joint = self.model.joints[relation_path]
                    parent = frame(joint.parent + ".frame")
                    relative = _Kinematics()
                    if joint.kind in ("hinge", "slider"):
                        coordinate, rate = self._coordinate(relation_path, time, state)
                        if joint.kind == "hinge":
                            relative = _Kinematics(orientation=_axis_rotation(joint.axis, coordinate),
                                                   omega=_scale(joint.axis, rate))
                        else:
                            relative = _Kinematics(position=_scale(joint.axis, coordinate),
                                                   velocity=_scale(joint.axis, rate))
                    child_site = self.model.sites[joint.child]
                    result = _compose(_compose(parent, relative), _inverse_pose(child_site.pose))
            elif state.modes[path] == "dynamic":
                result = self._dynamic_kinematics(path, time, state)
            else:
                position = state.positions[path]
                orientation = state.orientations[path]
                velocity, omega = ZERO, ZERO
                claim = state.claims.get((path, "translation"))
                if claim is not None:
                    action, runtime = self.model.actions[claim], state.actions[claim]
                    position = _affine(runtime.initial, action.vector, runtime.elapsed_at(time))
                    if runtime.status == "running":
                        velocity = action.vector
                claim = state.claims.get((path, "orientation"))
                if claim is not None:
                    action, runtime = self.model.actions[claim], state.actions[claim]
                    orientation = _advance_orientation(runtime.initial, action.vector, runtime.elapsed_at(time))
                    if runtime.status == "running":
                        omega = action.vector
                result = _Kinematics(position, orientation, velocity, omega)
            resolving.remove(path)
            components = (*result.position, *result.orientation, *result.velocity, *result.omega)
            if not all(math.isfinite(x) for x in components):
                raise _NumericFault(f"The state of {path} contains a non-finite component.")
            objects[path] = result
            frames[path + ".frame"] = result
            return result

        for path in self.model.objects:
            instance(path)
        for path in self.model.sites:
            if self.check is not None:
                self.check()
            frame(path + ".frame")
        return objects, frames

    def _next_boundary(self) -> Fraction | None:
        times: list[Fraction] = []
        if self.zero_pending:
            times.append(Fraction(0))
        if self.event_index < len(self.events):
            times.append(self.events[self.event_index].time)
        for path, runtime in self.state.actions.items():
            if runtime.status == "running":
                times.append(runtime.running_since + self.model.actions[path].duration - runtime.elapsed)
        return min(times) if times else None

    def _latch(self, path: str, time: Fraction, state: _RunState, status: str) -> None:
        action, runtime = self.model.actions[path], state.actions[path]
        elapsed = runtime.elapsed_at(time)
        if action.kind == "move":
            state.positions[action.target] = _affine(runtime.initial, action.vector, elapsed)
        elif action.kind == "spin":
            state.orientations[action.target] = _advance_orientation(runtime.initial, action.vector, elapsed)
        else:
            state.coordinates[action.target] = self._coordinate(action.target, time, state)[0]
        runtime.elapsed = elapsed
        runtime.status = status
        state.claims.pop(self._channel(action))

    def _dependencies(self, child: str, state: _RunState) -> set[tuple[str, str]]:
        incoming = self._incoming(state)
        dependencies: set[tuple[str, str]] = set()
        while child is not None:
            dependencies.add(("object", child))
            if child not in incoming:
                break
            kind, path = incoming[child]
            dependencies.add((kind, path))
            if kind == "joint":
                child = self.model.sites[self.model.joints[path].parent].owner
            else:
                child = self.model.frame_owner(self.model.follows[path].parent)
        return dependencies

    def _event(self, event: Any, time: Fraction, state: _RunState,
               incoming: dict[str, _Kinematics], dependencies: dict[str, set[tuple[str, str]]],
               touched: set[tuple[str, str]]) -> None:
        def fail(code: str, message: str, *, phase: str = "transition", conflict: bool = False,
                 rules: list[str] | None = None, repair: str | None = None,
                 details: dict[str, Any] | None = None, category: str | None = None) -> None:
            element = (self.model.objects.get(event.target) if event.kind == "impulse" else
                       self.model.joints.get(event.target) if event.kind == "release" else
                       self.model.actions.get(event.target))
            related = [element.span] if element is not None and element.span is not None else []
            if event.kind == "impulse":
                details = {"target_path": event.target,
                           "sequence_index": None if event.impulse is None else event.impulse.sequence_index,
                           **(details or {})}
            raise OntoKinError(code, message, event.span,
                               category=category or ("conflict" if conflict else "invalid"),
                               phase=phase, rule_ids=rules, time=time,
                               repair=repair, details=details,
                               element_id=list(element.element_id) if element is not None else None, related=related,
                               blocks=["evaluated", "delivered"])

        if event.kind == "impulse":
            if self.model.profile != IMPULSE_PROFILE:
                fail("OKL-E-CAPABILITY-UNSUPPORTED", "Source impulses require impulse-0.1.",
                     phase="support", category="unsupported", rules=["IMP-001"])
            obj = self.model.objects.get(event.target)
            if obj is None or event.impulse is None:
                fail("OKL-E-TYPE", "An impulse requires a resolved object and elaborated operands.",
                     phase="admission", rules=["IMP-001", "IMP-002"])
            if state.modes[event.target] != "dynamic" or event.target in self._incoming(state):
                fail("OKL-E-MOTION-MODE", "An impulse requires a currently free dynamic sphere.",
                     phase="admission", rules=["IMP-002", "IMP-003"],
                     repair="Use a free dynamic sphere, or release its grip earlier in this sequence.",
                     details={"motion": state.modes[event.target]})
            if obj.physical.get("kind") != "sphere_body" or obj.mass <= 0 or obj.inertia is None or obj.inertia <= 0:
                fail("OKL-E-PHYSICAL-DOMAIN", "An impulse requires positive own sphere mass and inertia.",
                     phase="admission", rules=["IMP-002"])
            payload = event.impulse
            operation = "current_dynamic_state"
            try:
                if not all(math.isfinite(value) for value in
                           (*payload.impulse_world_n_s, *payload.point_self_m, obj.mass, obj.inertia)):
                    raise _NumericFault("Impulse operands and sphere mass/inertia must be finite.")
                current = self._dynamic_kinematics(event.target, time, state)
                operation = "lever_arm_world_m"
                lever = _rotate(current.orientation, payload.point_self_m)
                operation = "application_point_world_m"
                point = _add(current.position, lever)
                operation = "angular_impulse_world_n_m_s"
                angular_impulse = _cross(lever, payload.impulse_world_n_s)
                # Round each exposed final component once. The unexposed
                # quotient can exceed binary64 when the final sum cancels.
                operation = "linear_velocity_after_world_m_per_s"
                velocity = tuple(_round(_f(value) + _f(impulse) / _f(obj.mass))
                                 for value, impulse in zip(current.velocity, payload.impulse_world_n_s))
                operation = "angular_velocity_after_world_rad_per_s"
                omega = tuple(_round(_f(value) + _f(impulse) / _f(obj.inertia))
                              for value, impulse in zip(current.omega, angular_impulse))
            except _NumericFault as error:
                fail("OKL-E-NUMERIC", str(error), phase="evaluation", category="numerical_failure",
                     rules=["IMP-002", "IMP-003", "LANG-004"],
                     details={"operation": operation},
                     repair="Use finite authored operands whose exposed impulse state remains representable.")
            if self.check is not None:
                self.check()
            if payload.impulse_world_n_s != ZERO:
                original = state.dynamic[event.target]
                state.dynamic[event.target] = _DynamicInitial(
                    time, _Kinematics(current.position, current.orientation, velocity, omega), original.since)
                touched.add(("object", event.target))
            # A zero impulse changes only its influence projection. In
            # particular, it does not change another grip's motion dependency.
            history = state.impulses[event.target]
            if history.last_time != time:
                history.last_applications = []
                history.last_time = time
            history.applied_count += 1
            history.last_applications.append({
                "sequence_index": payload.sequence_index,
                "source_location": dict(payload.source),
                "target_element_id": list(obj.element_id), "target_path": event.target,
                "impulse_world_n_s": list(payload.impulse_world_n_s),
                "application_point_self_m": list(payload.point_self_m),
                "lever_arm_world_m": list(lever), "application_point_world_m": list(point),
                "angular_impulse_world_n_m_s": list(angular_impulse),
                "linear_velocity_before_world_m_per_s": list(current.velocity),
                "linear_velocity_after_world_m_per_s": list(velocity),
                "angular_velocity_before_world_rad_per_s": list(current.omega),
                "angular_velocity_after_world_rad_per_s": list(omega),
            })
            return

        if event.kind == "release":
            joint = self.model.joints.get(event.target)
            if joint is None or joint.kind != "grip" or event.target not in state.active_grips:
                fail("OKL-E-RELEASE-STATE", f"{event.target} is not an active releasable grip.",
                     rules=["LANG-017", "LANG-020"], repair="Release each active grip once.")
            if touched & dependencies[event.target]:
                fail("OKL-E-EVENT-CONFLICT", "An earlier statement changed this grip's incoming motion dependencies.",
                     conflict=True, rules=["LANG-017", "LANG-020"],
                     repair="Place the incoming release before stopping, pausing, or replacing its carrier's actions.",
                     details={"changed_dependencies": sorted([list(x) for x in touched & dependencies[event.target]])})
            child = self.model.sites[joint.child].owner
            obj = self.model.objects[child]
            if obj.physical.get("kind") != "sphere_body" or state.modes[child] != "prescribed":
                fail("OKL-E-RELEASE-STATE", "The grip child is not a prescribed physical sphere.", rules=["LANG-017"])
            state.active_grips.remove(event.target)
            state.modes[child] = "dynamic"
            state.dynamic[child] = _DynamicInitial(time, incoming[child])
            touched.update({("joint", event.target), ("object", child)})
            return

        action = self.model.actions[event.target]
        runtime = state.actions[event.target]
        valid = {"start": {"pending"}, "pause": {"running"},
                 "resume": {"paused"}, "stop": {"running", "paused"}}
        if runtime.status not in valid[event.kind]:
            fail("OKL-E-ACTION-STATE", f"Cannot {event.kind} action {event.target} while it is {runtime.status}.",
                 phase="admission" if event.kind == "start" else "transition", rules=["LANG-019", "LANG-020"],
                 repair="Use a lifecycle transition valid for the action's current state; create a new action to restart.",
                 details={"action": event.target, "status": runtime.status, "requested_event": event.kind})
        if event.kind == "start":
            channel = self._channel(action)
            if action.kind in ("move", "spin"):
                if state.modes[action.target] != "prescribed" or action.target in self._incoming(state):
                    fail("OKL-E-MOTION-MODE", "Root motion requires a free prescribed object.", phase="admission",
                         rules=["LANG-015", "LANG-018"],
                         repair="Target a free prescribed object, or control an existing hinge/slider with tween.")
            else:
                joint = self.model.joints[action.target]
                if joint.kind not in ("hinge", "slider"):
                    fail("OKL-E-MOTION-MODE", "Only hinges and sliders have tweenable coordinates.", phase="admission",
                         rules=["LANG-013", "LANG-018"])
                if not joint.limits[0] <= action.goal <= joint.limits[1]:
                    fail("OKL-E-JOINT-LIMIT", f"Requested target {action.goal} exceeds the mandatory joint range.",
                         phase="admission", rules=["LANG-013", "LANG-018"],
                         repair="Choose a target within the joint's closed limits.",
                         details={"joint": action.target, "target": action.goal, "limits": list(joint.limits)})
            if channel in state.claims:
                fail("OKL-E-CONTROL-CONFLICT", f"Action {state.claims[channel]} already owns this channel.",
                     phase="admission", conflict=True, rules=["LANG-018", "LANG-020"],
                     repair="Stop the existing action before starting its replacement, or use a different channel.",
                     details={"channel": list(channel), "claimant": state.claims[channel], "requested": event.target})
            runtime.initial = (state.positions[action.target] if action.kind == "move" else
                               state.orientations[action.target] if action.kind == "spin" else
                               state.coordinates[action.target])
            runtime.status = "running"
            runtime.elapsed = Fraction(0)
            runtime.running_since = time
            state.claims[channel] = event.target
        elif event.kind == "pause":
            runtime.elapsed = runtime.elapsed_at(time)
            runtime.status = "paused"
        elif event.kind == "resume":
            runtime.running_since = time
            runtime.status = "running"
        else:
            self._latch(event.target, time, state, "stopped")
        touched.add(("joint" if action.kind == "tween" else "object", action.target))

    def _process_boundary(self, time: Fraction) -> None:
        if self.check is not None:
            self.check()
        incoming, _ = self._kinematics(time, self.state)
        dependencies = {path: self._dependencies(self.model.sites[self.model.joints[path].child].owner, self.state)
                        for path in self.state.active_grips}
        staged = copy.deepcopy(self.state)
        for path, runtime in staged.actions.items():
            if self.check is not None:
                self.check()
            if runtime.status == "running" and runtime.elapsed_at(time) == self.model.actions[path].duration:
                self._latch(path, time, staged, "completed")
        has_source = self.event_index < len(self.events) and self.events[self.event_index].time == time
        if has_source:
            touched: set[tuple[str, str]] = set()
            for event in self.events[self.event_index].events:
                if self.check is not None:
                    self.check()
                self._event(event, time, staged, incoming, dependencies, touched)
        self._kinematics(time, staged)
        self.state = staged
        if has_source:
            self.event_index += 1
        self.zero_pending = False
        self.last_boundary = time
        self.boundaries.append(time_text(time))

    def _check_dynamic_extrema(self, start: Fraction, end: Fraction) -> None:
        # A free-flight position can leave the finite range and return before
        # either requested endpoint. Check every interior quadratic extremum.
        for anchor in self.state.dynamic.values():
            if self.check is not None:
                self.check()
            for velocity, gravity in zip(anchor.state.velocity, self.model.gravity):
                if gravity:
                    extremum = anchor.time - _f(velocity) / _f(gravity)
                    if start < extremum < end:
                        self._kinematics(extremum, self.state)

    def advance(self, time: Fraction, side: str = "after") -> dict[str, Any]:
        try:
            while True:
                if self.check is not None:
                    self.check()
                boundary = self._next_boundary()
                if boundary is None or boundary > time or (boundary == time and side == "before"):
                    break
                self._check_dynamic_extrema(self.last_boundary, boundary)
                self._process_boundary(boundary)
            self._check_dynamic_extrema(self.last_boundary, time)
            return self.snapshot(time, side)
        except _NumericFault as exc:
            raise OntoKinError("OKL-E-NUMERIC", str(exc), self.model.span, phase="evaluation",
                               category="numerical_failure", blocks=["evaluated", "delivered"],
                               time=time, side=side, rule_ids=["LANG-004", "LANG-016"],
                               details={"last_valid_boundary_seconds": time_text(self.last_boundary),
                                        "requested_time_seconds": time_text(time)},
                               repair="Reduce the interval or the authored magnitudes so the requested state is finite.") from exc

    def snapshot(self, time: Fraction, side: str) -> dict[str, Any]:
        poses, frames = self._kinematics(time, self.state)
        incoming = self._incoming(self.state)
        objects: dict[str, Any] = {}
        for path, obj in self.model.objects.items():
            if self.check is not None:
                self.check()
            pose = poses[path]
            mode = self.state.modes[path]
            if path in incoming:
                kind, relation = incoming[path]
                authority: dict[str, Any] = {"kind": kind, "relation": relation}
            elif mode == "dynamic":
                anchor = self.state.dynamic[path]
                authority = {"kind": "free_sphere", "since_seconds": time_text(
                    anchor.since if self.model.profile == IMPULSE_PROFILE else anchor.time)}
                if self.model.profile == IMPULSE_PROFILE:
                    authority["trajectory_anchor_seconds"] = time_text(anchor.time)
            else:
                authority = {"kind": mode, "translation_action": self.state.claims.get((path, "translation")),
                             "orientation_action": self.state.claims.get((path, "orientation"))}
            gravity = ("active_dynamic" if mode == "dynamic" else
                       "inactive_prescribed" if mode == "prescribed" and obj.mass else
                       "inactive_static" if mode == "static" and obj.mass else "no_body")
            objects[path] = {
                "element_id": list(obj.element_id), "kind": "object", "name": obj.name,
                "class_name": obj.class_name, "owner": obj.owner, "motion": mode,
                "position_m": list(pose.position), "orientation_wxyz": list(pose.orientation),
                "velocity_m_per_s": list(pose.velocity), "angular_velocity_rad_per_s": list(pose.omega),
                "pose_frame": "world", "velocity_measured_in": "world", "velocity_expressed_in": "world",
                "velocity_reference_point": "center_of_mass" if obj.mass else "origin",
                "pose_authority": authority, "own_mass_kg": obj.mass,
                "owned_aggregate_mass_kg": _round(sum((_f(owned.mass) for owned in self.model.objects.values()
                    if owned.path == path or owned.path.startswith(path + ".")), Fraction(0))),
                "inertia_kg_m2": obj.inertia, "geometry": obj.geometry, "physical": obj.physical,
                "gravity_participation": gravity, "collision": obj.collision,
            }
            if self.model.profile == IMPULSE_PROFILE:
                history = self.state.impulses[path]
                applications = []
                for record in history.last_applications:
                    if self.check is not None:
                        self.check()
                    applications.append(copy.deepcopy(record))
                objects[path]["impulses"] = {
                    "applied_count": history.applied_count,
                    "last_application_time_seconds": None if history.last_time is None else time_text(history.last_time),
                    "last_applications": applications,
                }
        joints: dict[str, Any] = {}
        for path, joint in self.model.joints.items():
            record: dict[str, Any] = {"element_id": list(joint.element_id), "kind": joint.kind,
                                      "status": "inactive" if joint.kind == "grip" and path not in self.state.active_grips else "active",
                                      "parent_site": joint.parent, "child_site": joint.child,
                                      "coupling": "externally_prescribed_no_load_solution"}
            if joint.kind in ("hinge", "slider"):
                coordinate, rate = self._coordinate(path, time, self.state)
                record.update({"coordinate": coordinate, "coordinate_rate": rate,
                               "unit": "rad" if joint.kind == "hinge" else "m",
                               "limits": list(joint.limits), "action": self.state.claims.get((path, "coordinate"))})
            joints[path] = record
        actions = {path: {"element_id": list(action.element_id), "kind": action.kind,
                          "target": action.target, "status": self.state.actions[path].status,
                          "local_elapsed_seconds": time_text(self.state.actions[path].elapsed_at(time)),
                          "duration_seconds": time_text(action.duration)}
                   for path, action in self.model.actions.items()}
        frame_records = {path: {"position_m": list(value.position), "orientation_wxyz": list(value.orientation),
                                "velocity_m_per_s": list(value.velocity), "angular_velocity_rad_per_s": list(value.omega)}
                         for path, value in frames.items()}
        return {"time_seconds": time_text(time), "side": side, "objects": objects,
                "joints": joints, "actions": actions, "frames": frame_records,
                "scene_mass_kg": _round(sum((_f(obj.mass) for obj in self.model.objects.values()), Fraction(0)))}


def preflight(model: SceneModel, *, check: Callable[[], None] | None = None) -> dict[str, Any]:
    """Validate the authored timeline without creating a persistent live run."""
    if model.profile == IMPULSE_PROFILE:
        _output_budget(model, 1, check=check)
    simulator = _Simulator(model, check=check)
    simulator.advance(model.duration)
    return {"outcome": "valid", "duration_seconds": time_text(model.duration),
            "boundary_times_seconds": simulator.boundaries}


def _records_per_sample(model: SceneModel, *, constructing: bool = False,
                        check: Callable[[], None] | None = None) -> int:
    """Conservative complete output weight, shared with recorded animation.

    Existing row accounting is unchanged. Impulse projections additionally
    charge their exact nested logical entries before any sample duplicates
    them. Untouched objects retain their latest boundary's full record group.
    """
    # Frames contain world, each object frame, and each declared/implicit site
    # frame. Include them so an object with many sites cannot bypass the cap.
    base = 2 * len(model.objects) + len(model.sites) + len(model.joints) + len(model.actions) + 1
    if model.profile != IMPULSE_PROFILE:
        return base
    if check is not None:
        check()
    base += 4 * len(model.objects)
    if constructing:
        return base
    retained: dict[str, int] = {}
    total = maximum = 0
    for _, blocks in groupby(sorted(model.events, key=lambda block: block.time), key=lambda block: block.time):
        group: dict[str, int] = {}
        for block in blocks:
            if check is not None:
                check()
            for event in block.events:
                if check is not None:
                    check()
                if event.kind == "impulse":
                    obj = model.objects.get(event.target)
                    weight = 45 + (0 if obj is None else len(obj.element_id))
                    group[event.target] = group.get(event.target, 0) + weight
        for target, weight in group.items():
            if check is not None:
                check()
            total += weight - retained.get(target, 0)
            retained[target] = weight
        maximum = max(maximum, total)
    return base + maximum


def _output_budget(model: SceneModel, sample_count: int, *, constructing: bool = False,
                   check: Callable[[], None] | None = None,
                   records_per_sample: int | None = None) -> None:
    if records_per_sample is None:
        records_per_sample = _records_per_sample(model, constructing=constructing, check=check)
    if sample_count > MAX_SAMPLES or sample_count * records_per_sample > MAX_OUTPUT_RECORDS:
        raise OntoKinError("OKL-E-RESOURCE", "The requested state output exceeds the prototype's inspection budget.",
                           model.span, category="resource_limit", phase="elaboration" if constructing else "inspection",
                           blocks=["constructed", "evaluated", "delivered"] if constructing else [],
                           rule_ids=["IMP-004"] if model.profile == IMPULSE_PROFILE else None,
                           details={"max_samples": MAX_SAMPLES, "max_output_records": MAX_OUTPUT_RECORDS,
                                    "requested_samples": sample_count, "records_per_sample": records_per_sample},
                           repair="Request fewer sample times, or use a smaller scene for this bounded prototype.")


def construct(model: SceneModel) -> dict[str, Any]:
    """Construct initial world state, before t=0 action/event processing.

    Construction resolves the relationship graph and physical descriptions. A
    later action conflict does not prevent this lower-level result.
    """
    _output_budget(model, 1, constructing=True)
    try:
        initial = _Simulator(model).advance(Fraction(0), "before")
    except OntoKinError as exc:
        if exc.diagnostic.category == "numerical_failure":
            exc.diagnostic.phase = "elaboration"
            exc.diagnostic.blocks = ["constructed", "evaluated", "delivered"]
            exc.diagnostic.details["operation"] = "construct"
        raise
    return {"outcome": "valid", "level": "constructed", "profile": model.profile,
            "module": model.module_name, "scene": model.scene_name,
            "duration_seconds": time_text(model.duration), "initial_state": initial}


def evaluate(model: SceneModel, times: Iterable[Any] | None = None, *, side: str = "after") -> dict[str, Any]:
    """Evaluate requested times and verify all authored events through the horizon.

    A request may be a decimal string/number, or a dictionary containing
    ``time_seconds`` and an optional ``side``. Results retain the caller's order.
    Exact decimal strings are recommended; float arguments retain binary64 time.
    """
    if times is None:
        times = ["0", model.duration]
    records = _records_per_sample(model)
    if model.profile == IMPULSE_PROFILE:
        # Even an empty requested sample list still validates the full horizon
        # and must not allocate an unbounded retained application group.
        _output_budget(model, 1, records_per_sample=records)
    requests: list[tuple[Fraction, str, int]] = []
    for index, request in enumerate(times):
        _output_budget(model, index + 1, records_per_sample=records)
        sample_side = request.get("side", side) if isinstance(request, dict) else side
        value = request.get("time_seconds", request.get("time")) if isinstance(request, dict) else request
        time = exact_time(value)
        if sample_side not in ("before", "after") or not 0 <= time <= model.duration:
            raise OntoKinError("OKL-E-SAMPLE", "The requested time or boundary side is unavailable.",
                               model.span, phase="inspection", blocks=[],
                               details={"duration_seconds": time_text(model.duration),
                                        "requested_time_seconds": time_text(time), "requested_side": sample_side},
                               repair="Use before or after and a timestamp from zero through the scene duration.")
        requests.append((time, sample_side, index))
    simulator = _Simulator(model)
    samples: list[Any] = [None] * len(requests)
    for time, sample_side, index in sorted(requests, key=lambda request: (request[0], request[1] == "after")):
        samples[index] = simulator.advance(time, sample_side)
    simulator.advance(model.duration)
    assumptions = {
        "gravity_m_per_s2": list(model.gravity), "collision": "disabled",
        "contact_response": "unavailable", "drag": "absent", "ground_plane": "absent",
        "dynamic_body_model": "homogeneous_solid_sphere", "external_torque": "absent",
        "joint_coupling": "externally_prescribed_no_load_solution",
    }
    if model.profile == IMPULSE_PROFILE:
        assumptions.update(external_torque="authored_instantaneous_angular_impulses_only",
                           impulses="authored_world_impulse_at_target_self_point",
                           continuous_external_forces="uniform_gravity_only", continuous_external_torque="absent")
    return {
        "outcome": "valid", "level": "evaluated", "profile": model.profile,
        "module": model.module_name, "scene": model.scene_name,
        "duration_seconds": time_text(model.duration), "samples": samples,
        "boundary_times_seconds": simulator.boundaries,
        "physical_assumptions": assumptions,
        "numerical_method": "analytical trajectories; rational event clock; binary64 spatial calculations",
    }


def evaluate_prefix(model: SceneModel, until: Any, *, side: str = "after",
                    check: Callable[[], None] | None = None) -> dict[str, Any]:
    """Replay only through an exact endpoint, retaining the last checked state.

    Unlike evaluate(), this additive agent hook does not preflight future
    events. A failed atomic boundary retains its incoming before-state. Failure
    between boundaries retains the last state actually checked. ``failure`` is
    an OntoKinError for the caller to bind to its immutable source and run.
    Wrap OntoKinError callback interruptions if they must propagate unchanged.
    """
    endpoint = exact_time(until)
    if side not in ("before", "after") or not 0 <= endpoint <= model.duration:
        raise OntoKinError("OKL-E-SAMPLE", "The requested run endpoint is outside the scene or has an invalid side.",
                           model.span, phase="inspection", blocks=[],
                           details={"duration_seconds": time_text(model.duration),
                                    "requested_time_seconds": time_text(endpoint), "requested_side": side})
    _output_budget(model, 1, check=check)
    simulator = None
    last = None
    failure = None

    def capture(time: Fraction, boundary_side: str) -> dict[str, Any]:
        sample = simulator.advance(time, boundary_side)
        # These fields belong to the prefix adapter; legacy samples stay intact.
        for path, action in model.actions.items():
            if check is not None:
                check()
            runtime = simulator.state.actions[path]
            record = sample["actions"][path]
            record["channel"] = simulator._channel(action)[1]
            record["start_value"] = {"available": runtime.initial is not None,
                                      "value": copy.deepcopy(runtime.initial)}
            if action.kind == "tween":
                current = sample["joints"][action.target]["coordinate"]
            else:
                name = "position_m" if action.kind == "move" else "orientation_wxyz"
                current = sample["objects"][action.target][name]
            record["current_value"] = {"available": True, "value": current}
            target, reason = action.goal, None
            if action.kind != "tween":
                if runtime.initial is None:
                    reason = "action_has_not_started"
                else:
                    try:
                        target = (_affine(runtime.initial, action.vector, action.duration) if action.kind == "move"
                                  else _advance_orientation(runtime.initial, action.vector, action.duration))
                    except _NumericFault:
                        reason = "target_exceeds_finite_range"
            record["target_value"] = {"available": reason is None, "value": target, "reason": reason}
            record["value_type"] = {"move": "Point3", "spin": "Rotation", "tween": "Quantity"}[action.kind]
        return sample

    try:
        simulator = _Simulator(model, check=check)
        last = capture(Fraction(0), "before")
        while True:
            if check is not None:
                check()
            boundary = simulator._next_boundary()
            if boundary is None or boundary > endpoint or (boundary == endpoint and side == "before"):
                break
            last = capture(boundary, "before")
            last = capture(boundary, "after")
        if last["time_seconds"] != time_text(endpoint) or last["side"] != side:
            last = capture(endpoint, side)
        if check is not None:
            check()
    except OntoKinError as exc:
        failure = exc
    return {"valid_until_seconds": None if last is None else last["time_seconds"],
            "valid_until_side": None if last is None else last["side"],
            "last_valid_state": last, "failure": failure,
            "boundary_times_seconds": [] if simulator is None else list(simulator.boundaries)}


def inspect_in_frame(sample: dict[str, Any], object_path: str, frame_path: str = "world") -> dict[str, Any]:
    """Re-express a sampled pose and world-measured velocity in another frame.

    Velocity components are rotated into the requested axes. They remain
    measured relative to world; this is not velocity relative to a moving owner.
    """
    try:
        obj = sample["objects"][object_path]
        reference = sample["frames"][frame_path]
    except KeyError as exc:
        raise OntoKinError("OKL-E-SAMPLE", "The requested object or frame is absent from this sample.",
                           phase="inspection", blocks=[],
                           repair="Use an object and frame present in this revision's sample.") from exc
    try:
        inverse = _inverse(tuple(reference["orientation_wxyz"]))
        position = _rotate(inverse, _add(tuple(obj["position_m"]), _neg(tuple(reference["position_m"]))))
        rotation = _multiply(inverse, tuple(obj["orientation_wxyz"]))
        velocity = _rotate(inverse, tuple(obj["velocity_m_per_s"]))
        omega = _rotate(inverse, tuple(obj["angular_velocity_rad_per_s"]))
    except _NumericFault as exc:
        raise OntoKinError("OKL-E-NUMERIC", str(exc), phase="inspection", category="numerical_failure",
                           time=exact_time(sample["time_seconds"]), side=sample["side"], blocks=[],
                           element_id=obj["element_id"], details={"object": object_path, "frame": frame_path},
                           repair="Inspect in world or in a frame whose relative coordinates remain finite.") from exc
    return {
        "element_id": obj["element_id"], "time_seconds": sample["time_seconds"], "side": sample["side"],
        "pose_frame": frame_path, "position_m": list(position),
        "orientation_wxyz": list(rotation),
        "velocity_m_per_s": list(velocity),
        "angular_velocity_rad_per_s": list(omega),
        "velocity_measured_in": "world", "velocity_expressed_in": frame_path,
        "velocity_reference_point": obj["velocity_reference_point"],
    }
