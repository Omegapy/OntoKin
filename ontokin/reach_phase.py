"""Uniform source-phase inputs, with continuous ideal state across anchors.

This module derives bounds from actual topology and exact phase operands. It
does not infer a uniform error from sampled poses or an inverse-solve residual.
All arithmetic consumes the simulator's existing bounded request work context.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from fractions import Fraction as F
from math import isfinite
from types import MappingProxyType

from .reach_numeric import ReachAdmissionError, compare, exact, rational
from .reach_pose import EXPOSED_ROTATION_ERROR, VECTOR_ERROR, RotationValue, uniform_source_bounds


@dataclass(frozen=True)
class AnchorError:
    position_m: F = F(0)
    rotation_rad: F = F(0)
    velocity_m_per_s: F = F(0)
    angular_velocity_rad_per_s: F = F(0)


@dataclass(frozen=True)
class JointPhase:
    actual_start: F
    actual_end: F
    ideal_start: F
    ideal_end: F
    actual_slope: F
    ideal_slope: F
    coordinate_error: F


@dataclass(frozen=True)
class PhaseBound:
    max_position_l1_m: F = F(0)
    path_offset_l1_m: F = F(0)
    trig_count: int = 0
    product_count: int = 0
    vector_round_count: int = 0
    coordinate_angle_error_rad: F = F(0)
    anchor_position_error_m: F = F(0)
    anchor_rotation_error_rad: F = F(0)
    position_error_m: F = F(0)
    rotation_error_rad: F = F(0)
    velocity_error_m_per_s: F = F(0)
    angular_velocity_error_rad_per_s: F = F(0)
    carrier_speed_upper_m_per_s: F = F(0)
    carrier_acceleration_upper_m_per_s2: F = F(0)
    angular_speed_upper_rad_per_s: F = F(0)
    angular_acceleration_upper_rad_per_s2: F = F(0)
    actual_speed_upper_m_per_s: F = F(0)
    actual_angular_speed_upper_rad_per_s: F = F(0)


_BOUND_FIELDS = tuple(PhaseBound.__dataclass_fields__)
_JOINT_PHASE_FIELDS = tuple(JointPhase.__dataclass_fields__)
_COMPOSITION_FIELDS = tuple(name for name in _BOUND_FIELDS
                            if name not in {"max_position_l1_m", "path_offset_l1_m", "position_error_m"})
_CACHE_DOMAIN = "reach_source_phase/0.1"


@dataclass(frozen=True)
class _AxialRate:
    """Exact constant body angular velocity on one Cartesian basis axis."""
    axis: int | None
    value: F


_ZERO_AXIAL_RATE = _AxialRate(None, F(0))


@dataclass(frozen=True)
class RecordingAngularFrame:
    """One optional recording law, bound to immutable typed local operands."""
    rate: _AxialRate
    parent: str | None
    witness: tuple
    trig_count: int
    token: object = field(default_factory=object, compare=False, repr=False)


@dataclass(frozen=True)
class RecordingAngularProof:
    start: F
    end: F
    program_revision: str
    frames: MappingProxyType


class _RecordingWitnessUnavailable(Exception):
    pass


def current_recording_angular_witness(model, state, kind, path, *, work):
    """Snapshot one fixed-size source law for both proof and cursor checking.

    No state/model identity substitutes for these current inputs. Numeric
    values retain their concrete types and binary64 signs; each nested vector
    has a fixed maximum of four components. This helper supplies no numeric
    result or source authority and creates no cache. Unsupported mutable shapes
    make the optional proof unavailable, leaving ordinary evaluation in place.
    """
    work.charge("recording_angular_witness_guard")
    if (work.max_operand_bits < 1075 or type(kind) is not str or type(path) is not str
            or kind not in {"world", "root", "site", "follow", "joint"}):
        return None
    work.guard_bits(1075)

    def freeze(value, depth=0):
        if depth > 2:
            raise _RecordingWitnessUnavailable
        if value is None:
            return ("none",)
        if type(value) is str:
            return ("string", value)
        if type(value) is float:
            if not isfinite(value):
                raise _RecordingWitnessUnavailable
            return ("binary64", value.hex())
        if type(value) is F:
            work.guard(value)
            return ("rational", value.numerator, value.denominator)
        if type(value) is int:
            work.guard(value)
            return ("integer", value)
        if type(value) is tuple and len(value) <= 4:
            return ("tuple", tuple(freeze(part, depth + 1) for part in value))
        if type(value) is RotationValue:
            if type(value.error_rad) is not F:
                raise _RecordingWitnessUnavailable
            return ("private_rotation", vector(value.components, 4), freeze(value.error_rad, depth + 1),
                    None if value.frozen_projection is None else vector(value.frozen_projection, 4))
        raise _RecordingWitnessUnavailable

    def vector(value, size):
        if type(value) is not tuple or len(value) != size:
            raise _RecordingWitnessUnavailable
        if any(type(part) not in (float, int, F) for part in value):
            raise _RecordingWitnessUnavailable
        return freeze(value)

    def pose(value):
        return vector(value.position, 3), vector(value.rotation, 4)

    def law(claimant):
        if claimant is None:
            return None
        action, active = model.actions[claimant], state.actions[claimant]
        reach = ((action.reach.shoulder, action.reach.elbow)
                 if action.kind == "reach_planar" else None)
        solution = active.solution.target_rad if active.solution is not None else None
        return (freeze(claimant), freeze(action.kind), freeze(action.target), freeze(action.duration),
                freeze(action.vector), freeze(action.goal), freeze(reach), freeze(active.status),
                freeze(active.initial), freeze(active.ideal_initial), freeze(solution),
                freeze(active.elapsed), freeze(active.running_since),
                freeze(active.ideal_rotation_error), freeze(active.initial_rotation))

    try:
        if kind == "world":
            return (None, ("world",)) if path == "world" else None
        if kind == "root":
            if state.modes[path] == "dynamic":
                return None
            witness = (kind, path, freeze(state.modes[path]), vector(state.positions[path], 3),
                       vector(state.ideal_positions[path], 3), vector(state.orientations[path], 4),
                       freeze(state.root_rotation_values.get(path)),
                       freeze(state.root_rotation_errors.get(path, F(0))),
                       law(state.claims.get((path, "orientation"))),
                       law(state.claims.get((path, "translation"))))
            return None, witness
        if kind == "site":
            site = model.sites[path]
            return site.owner + ".frame", (kind, path, freeze(site.owner), pose(site.pose))
        if kind == "follow":
            follow = model.follows[path]
            return follow.parent, (kind, path, freeze(follow.parent), freeze(follow.child), pose(follow.offset))
        joint = model.joints[path]
        child = model.sites[joint.child]
        moving = joint.kind in {"hinge", "slider"}
        witness = (kind, path, freeze(joint.kind), freeze(joint.parent), freeze(joint.child),
                   freeze(joint.axis), freeze(joint.limits), freeze(child.owner), pose(child.pose),
                   law(state.claims.get((path, "coordinate"))) if moving else None,
                   freeze(state.coordinates[path]) if moving else None,
                   freeze(state.ideal_coordinates[path]) if moving else None)
        return joint.parent + ".frame", witness
    except (_RecordingWitnessUnavailable, KeyError, AttributeError):
        return None


def _single_axis(vector, work, *, unit=False):
    """Recognize a canonical binary64 axis without approximate comparisons."""
    work.charge("phase_axial_axis_guard")
    # The optional proof can fall back when a lowered live domain does not
    # admit every possible canonical binary64 component. Existing phase
    # arithmetic still applies its exact per-operand admission checks.
    if work.max_operand_bits < 1075:
        return None
    if (type(vector) is not tuple or len(vector) != 3
            or any(type(value) is not float or not isfinite(value) for value in vector)):
        return None
    work.guard_bits(1075)
    axes = tuple(index for index, value in enumerate(vector) if value)
    if len(axes) != 1 or unit and vector[axes[0]] not in (-1.0, 1.0):
        return None
    return axes[0]


def _transport_axial_rate(rate, rotation, work):
    """Transport through a fixed quaternion that preserves or reverses its axis.

    Both the forward and inverse rotations have the same sign on this
    one-dimensional invariant subspace. No quaternion normalization, products,
    trigonometry, or sampled orientation is needed for these exact zero patterns.
    """
    work.charge("phase_axial_transport_guard")
    if rate is None:
        return None
    work.guard(rate.value)
    if not rate.value:
        return _ZERO_AXIAL_RATE
    if work.max_operand_bits < 1075:
        return None
    if (type(rotation) is not tuple or len(rotation) != 4
            or any(type(value) is not float or not isfinite(value) for value in rotation)
            or not any(rotation)):
        return None
    work.guard_bits(1075)
    component = rate.axis + 1  # Canonical quaternion order is w,x,y,z.
    other = tuple(rotation[index] for index in range(1, 4) if index != component)
    if not any(other):
        return rate
    if not rotation[0] and not rotation[component]:
        work.charge("phase_axial_reverse")
        work.guard(rate.value)
        return _AxialRate(rate.axis, -rate.value)
    return None


def _hinge_axial_rate(parent, axis, slope, work):
    """Add signed affine hinge rates only in a proved common body axis."""
    work.charge("phase_axial_hinge_guard")
    work.guard(slope)
    if parent is None:
        return None
    work.guard(parent.value)
    if not parent.value and not slope:
        return _ZERO_AXIAL_RATE
    component = _single_axis(axis, work, unit=True)
    if component is None or parent.value and parent.axis != component:
        return None
    # The unit-axis sign selection is a charged bounded classification. The
    # subsequent exact addition retains the ordinary intermediate-width guard.
    work.charge("phase_axial_hinge_sign")
    work.guard(slope, parent.value)
    value = PhaseArithmetic(work).add(parent.value, -slope if axis[component] < 0 else slope)
    return _AxialRate(component, value) if value else _ZERO_AXIAL_RATE


def _root_axial_rate(action, runtime, work):
    work.charge("phase_axial_root_guard")
    if (type(runtime.ideal_rotation_error) is not F or runtime.ideal_rotation_error
            or runtime.initial_rotation is not None):
        return None
    component = _single_axis(action.vector, work)
    if component is None:
        return None
    value = rational(action.vector[component], work)
    # A root spin is world-fixed. Its initial inverse rotation gives the
    # constant body vector; the eligible axis has the same forward/inverse sign.
    return _transport_axial_rate(_AxialRate(component, value), runtime.initial, work)


def _tighten_angular(bound, rate, work):
    if rate is None:
        return bound
    work.charge("phase_axial_derivative_guard")
    work.guard(rate.value, bound.angular_speed_upper_rad_per_s,
               bound.angular_acceleration_upper_rad_per_s2)
    return replace(bound, angular_speed_upper_rad_per_s=abs(rate.value),
                   angular_acceleration_upper_rad_per_s2=F(0))


def _local_translation_independent(parent):
    """A parent's exact zero angular bounds remove every offset derivative."""
    return all(type(value) is F and not value for value in (
        parent.angular_speed_upper_rad_per_s,
        parent.angular_acceleration_upper_rad_per_s2,
        parent.actual_angular_speed_upper_rad_per_s,
        parent.angular_velocity_error_rad_per_s))


class PhaseArithmetic:
    def __init__(self, work):
        self.work = work

    def number(self, value):
        return rational(value, self.work)

    def add(self, *values):
        if 0 < len(values) <= 8 and all(type(value) is F for value in values):
            self.work.charge("phase_sum_domain")
            self.work.guard(*values)
            nonzero = tuple(value for value in values if value)
            if not nonzero:
                return F(0)
            result = nonzero[0]
            for value in nonzero[1:]:
                result = exact(result, value, "add", self.work)
            return result
        result = F(0)
        for value in values:
            result = exact(result, value, "add", self.work)
        return result

    def sub(self, a, b):
        return exact(a, b, "sub", self.work)

    def mul(self, *values):
        if 0 < len(values) <= 8 and all(type(value) is F for value in values):
            self.work.charge("phase_product_domain")
            self.work.guard(*values)
            if not all(values):
                return F(0)
            factors = tuple(value for value in values if value != 1)
            if not factors:
                return F(1)
            result = factors[0]
            for value in factors[1:]:
                result = exact(result, value, "mul", self.work)
            return result
        result = F(1)
        for value in values:
            result = exact(result, value, "mul", self.work)
        return result

    def div(self, a, b):
        return exact(a, b, "div", self.work)

    def absolute(self, value):
        self.work.charge("phase_absolute")
        self.work.guard(value)
        return abs(value)

    def maximum(self, *values):
        result = F(0)
        for value in values:
            if compare(value, result, self.work) > 0:
                result = value
        return result

    def l1(self, vector):
        return self.add(*(self.absolute(self.number(value)) for value in vector))

    def rounding(self, magnitude):
        # L1 component exposure allowance; also bounds its Euclidean norm.
        return self.add(self.mul(magnitude, F(1, 1 << 53)), F(3, 1 << 1075))


def joint_phase(simulator, path, start, end, state):
    """Exact affine endpoints and slopes; continuous ideal starts are retained."""
    a = PhaseArithmetic(simulator.work)
    claimant = state.claims.get((path, "coordinate"))
    if claimant is None:
        actual = a.number(state.coordinates[path])
        ideal = a.number(state.ideal_coordinates[path])
        simulator.work.charge("phase_joint_key")
        key = (_CACHE_DOMAIN, simulator.work.max_operand_bits, "unclaimed_joint", actual, ideal)
        cached = simulator.work.lookup(key)
        if cached is not None:
            return cached
        result = JointPhase(actual, actual, ideal, ideal, F(0), F(0), a.absolute(a.sub(actual, ideal)))
        simulator.work.remember(key, result)
        return result
    action, runtime = simulator.model.actions[claimant], state.actions[claimant]
    if action.kind == "reach_planar":
        index = 0 if path == action.reach.shoulder else 1
        actual_initial = a.number(runtime.initial[index])
        ideal_initial = a.number(runtime.ideal_initial[index])
        target = a.number(runtime.solution.target_rad[index])
    else:
        actual_initial = a.number(runtime.initial)
        ideal_initial = a.number(runtime.ideal_initial)
        target = a.number(action.goal)
    duration = a.number(action.duration)
    elapsed = tuple(a.number(runtime.elapsed_at(time)) for time in (start, end))
    simulator.work.charge("phase_joint_key")
    key = (_CACHE_DOMAIN, simulator.work.max_operand_bits, "claimed_joint", action.kind,
           actual_initial, ideal_initial, target, duration, elapsed, runtime.status)
    cached = simulator.work.lookup(key)
    if cached is not None:
        return cached
    actual_rate = a.div(a.sub(target, actual_initial), duration)
    ideal_rate = a.div(a.sub(target, ideal_initial), duration)
    actual = tuple(a.add(actual_initial, a.mul(actual_rate, time)) for time in elapsed)
    ideal = tuple(a.add(ideal_initial, a.mul(ideal_rate, time)) for time in elapsed)
    error = a.maximum(*(a.absolute(a.sub(x, y)) for x, y in zip(actual, ideal)))
    extent = a.maximum(*(a.absolute(value) for value in actual))
    # The affine scalar is rounded once at exposure into the source hinge.
    # Its magnitude lies between these endpoints throughout this phase.
    error = a.add(error, a.rounding(extent))
    running = runtime.status == "running"
    result = JointPhase(*actual, *ideal, actual_rate if running else F(0),
                        ideal_rate if running else F(0), error)
    simulator.work.remember(key, result)
    return result


def phase_bounds(simulator, start, end, state=None, *, selected_frames=None, recording_proof=False):
    """Return uniform bounds on one continuous closed source phase.

    The state governs the entire interval; the caller splits at all source and
    natural boundaries. The public result contains immutable bound records and
    exact scalar joint descriptors, never mutable solver/work objects.
    ``selected_frames`` is an internal anchor-proof optimization.
    ``recording_proof`` retains optional immutable angular laws for a separately
    bounded recording cursor; ordinary callers receive no extra result fields.
    """
    start, end = F(start), F(end)
    state = simulator.state if state is None else state
    if not 0 <= start <= end <= simulator.model.duration:
        raise ValueError("A source phase must be an ordered interval within the scene.")
    model, work, ops = simulator.model, simulator.work, simulator.pose_ops
    if type(recording_proof) is not bool:
        raise ValueError("A recording proof selector must be boolean.")
    a = PhaseArithmetic(work)
    for block in model.events:
        work.charge("phase_boundary_check")
        if start < block.time < end:
            raise ValueError("A uniform phase cannot cross an authored boundary.")
    for path, runtime in state.actions.items():
        work.charge("phase_boundary_check")
        if runtime.status == "running" and start < runtime.running_since + model.actions[path].duration - runtime.elapsed < end:
            raise ValueError("A uniform phase cannot cross an action completion.")
    for history in state.forces.values():
        for force in history.active.values():
            work.charge("phase_boundary_check")
            if start < force.completion < end:
                raise ValueError("A uniform phase cannot cross a force completion.")
    incoming = simulator._incoming(state)
    objects, frames, joints, resolving = {}, {"world": PhaseBound()}, {}, set()
    # This phase-local proof state follows the same bounded source traversal.
    # It is neither a sampled pose map nor an additional numerical-result cache.
    axial_rates = {"world": _ZERO_AXIAL_RATE}
    angular_frames = {}
    proof_revision = model.program_revision if recording_proof else None
    if recording_proof:
        work.charge("phase_recording_proof_domain")
        angular_frames["world"] = RecordingAngularFrame(_ZERO_AXIAL_RATE, None, ("world",), 0)

    def witness(kind, path):
        return (current_recording_angular_witness(model, state, kind, path, work=work)
                if recording_proof else None)

    def retain_angular(frame, rate, bound, original, kind, path):
        if not recording_proof or rate is None or original is None:
            return
        parent, operands = original
        if parent is not None and parent not in angular_frames:
            return
        work.charge("phase_recording_proof_publish")
        # Check once more after the publication callback. A partial phase or a
        # changed local law cannot authorize a cursor through an old signature.
        if witness(kind, path) != original:
            return
        work.guard(rate.value, bound.trig_count)
        angular_frames[frame] = RecordingAngularFrame(rate, parent, operands, bound.trig_count)

    def finish(**values):
        inputs = {name: values.get(name, 0 if name.endswith("count") else F(0)) for name in (
            "max_position_l1_m", "path_offset_l1_m", "trig_count", "product_count", "vector_round_count",
            "coordinate_angle_error_rad", "anchor_position_error_m", "anchor_rotation_error_rad")}
        bound = uniform_source_bounds(**inputs, work=work)
        values.update(position_error_m=bound["position_m"], rotation_error_rad=bound["rotation_rad"])
        return PhaseBound(**values)

    def constant(pose, *, inverse=False):
        # Decode/guard every position component before a lookup. No mutable
        # model record is retained; the key contains its complete local pose.
        position = tuple(a.number(value) for value in pose.position)
        work.charge("phase_constant_key")
        if type(inverse) is not bool:
            raise ValueError("A phase constant inverse selector must be boolean.")
        key = (_CACHE_DOMAIN, work.max_operand_bits, "constant", position, pose.rotation, inverse)
        cached = work.lookup(key)
        if cached is not None:
            return cached
        extent = a.add(*(a.absolute(value) for value in position))
        result = finish(max_position_l1_m=a.add(a.mul(F(2), extent), a.mul(F(2), VECTOR_ERROR)) if inverse else extent,
            path_offset_l1_m=extent if inverse else F(0), product_count=1,
            vector_round_count=int(inverse))
        work.remember(key, result)
        return result

    def compose(parent, local, *, axial_rate=None):
        # The recurrence never reads the parent's position_error_m: it derives
        # that allowance again from inherited anchor errors and path counts.
        # Its extent and path offset appear only in the final uniform position
        # formula. Keep all other parent fields and the complete local bound in
        # one immutable key, with a single relative bound and replaceable
        # extent/offset/result. The exact formula is affine in these two values:
        # extent*2^-53 + path_offset*(rotation_error-EXPOSED_ROTATION_ERROR).
        # No sampled error or rounded arithmetic enters this factorization.
        work.charge("phase_composition_operand_guard")
        operands = tuple(getattr(bound, field) for bound in (parent, local) for field in _BOUND_FIELDS)
        work.guard(*operands)
        local_translation = None
        if _local_translation_independent(parent):
            # When all four angular derivative bounds are exactly zero,
            # neither local extent nor its position allowance contributes to
            # any derivative equation below. Their only remaining effects are
            # the exact uniform extent/path-offset position formula. Reuse
            # the zero-translation recurrence across distinct rigid mounts;
            # retain every other parent/local field in its original key.
            work.charge("phase_local_translation_factor")
            work.guard(*operands)
            local_translation = (local.max_position_l1_m, local.path_offset_l1_m)
            local = replace(local, max_position_l1_m=F(0), path_offset_l1_m=F(0), position_error_m=F(0))
        kind = "composition_translation_recurrence" if local_translation is not None else "composition_recurrence"
        key = (_CACHE_DOMAIN, work.max_operand_bits, kind,
               tuple(getattr(parent, field) for field in _COMPOSITION_FIELDS), local)
        cached = work.lookup(key)
        work.guard(*operands)
        location = (parent.max_position_l1_m, parent.path_offset_l1_m, local_translation)

        def checked(bound):
            # A lookup, identity check, or insertion callback can narrow the
            # live domain after the original operands/results were checked.
            # The cached recurrence is unchanged. Only its ideal derivatives
            # are tightened after a fresh topology proof for this source node.
            bound = _tighten_angular(bound, axial_rate, work)
            work.guard(*operands, *(getattr(bound, field) for field in _BOUND_FIELDS))
            return bound

        def translated(base):
            work.charge("phase_composition_extent")
            extent_delta, offset_delta = parent.max_position_l1_m, parent.path_offset_l1_m
            if local_translation is not None:
                local_extent, local_offset = local_translation
                extent_delta = a.add(extent_delta, a.mul(F(2), local_extent))
                offset_delta = a.add(offset_delta, local_offset, local_extent)
            extent = a.add(extent_delta, base.max_position_l1_m)
            offset = a.add(offset_delta, base.path_offset_l1_m)
            if compare(extent, F(0), work) < 0 or compare(offset, F(0), work) < 0:
                raise ReachAdmissionError("reach_numeric", "Source uniform allowances must be nonnegative.")
            rotation = a.sub(base.rotation_error_rad, EXPOSED_ROTATION_ERROR)
            position_error = a.add(base.position_error_m,
                a.mul(extent_delta, F(1, 1 << 53)), a.mul(offset_delta, rotation))
            return replace(base, max_position_l1_m=extent, path_offset_l1_m=offset,
                           position_error_m=position_error)

        if cached is not None:
            work.charge("phase_composition_extent_identity")
            if location == cached[0]:
                return checked(cached[1])
            result = translated(cached[2])
            work.remember(key, (location, result, cached[2]))
            return checked(result)
        work.charge("phase_path_counts", 3)
        offset = local.max_position_l1_m
        ideal_offset = a.add(offset, local.position_error_m)
        p_speed, l_speed = parent.carrier_speed_upper_m_per_s, local.carrier_speed_upper_m_per_s
        p_omega, l_omega = parent.angular_speed_upper_rad_per_s, local.angular_speed_upper_rad_per_s
        speed = a.add(p_speed, a.mul(p_omega, ideal_offset), l_speed)
        acceleration = a.add(parent.carrier_acceleration_upper_m_per_s2,
            a.mul(a.add(parent.angular_acceleration_upper_rad_per_s2, a.mul(p_omega, p_omega)), ideal_offset),
            a.mul(F(2), p_omega, l_speed), local.carrier_acceleration_upper_m_per_s2)
        omega = a.add(p_omega, l_omega)
        alpha = a.add(parent.angular_acceleration_upper_rad_per_s2,
            a.mul(p_omega, l_omega), local.angular_acceleration_upper_rad_per_s2)
        actual_speed = a.add(parent.actual_speed_upper_m_per_s,
            a.mul(parent.actual_angular_speed_upper_rad_per_s, a.add(offset, VECTOR_ERROR)),
            local.actual_speed_upper_m_per_s, a.mul(F(2), VECTOR_ERROR))
        actual_omega = a.add(parent.actual_angular_speed_upper_rad_per_s,
            local.actual_angular_speed_upper_rad_per_s, a.mul(F(2), VECTOR_ERROR))
        offset_error = a.add(local.position_error_m,
            a.mul(parent.rotation_error_rad, offset), VECTOR_ERROR)
        velocity_error = a.add(parent.velocity_error_m_per_s,
            a.mul(parent.angular_velocity_error_rad_per_s, a.add(offset, local.position_error_m)),
            a.mul(parent.actual_angular_speed_upper_rad_per_s, offset_error),
            local.velocity_error_m_per_s,
            a.mul(parent.rotation_error_rad, local.actual_speed_upper_m_per_s),
            a.mul(F(4), VECTOR_ERROR), a.rounding(a.mul(F(2), actual_speed)))
        omega_error = a.add(parent.angular_velocity_error_rad_per_s,
            local.angular_velocity_error_rad_per_s,
            a.mul(parent.rotation_error_rad, local.actual_angular_speed_upper_rad_per_s),
            a.mul(F(2), VECTOR_ERROR), a.rounding(a.mul(F(2), actual_omega)))
        values = dict(
            path_offset_l1_m=a.add(local.path_offset_l1_m, offset),
            trig_count=parent.trig_count + local.trig_count,
            product_count=parent.product_count + local.product_count + 1,
            vector_round_count=parent.vector_round_count + local.vector_round_count + 2,
            coordinate_angle_error_rad=a.add(parent.coordinate_angle_error_rad, local.coordinate_angle_error_rad),
            anchor_position_error_m=a.add(parent.anchor_position_error_m, local.anchor_position_error_m),
            anchor_rotation_error_rad=a.add(parent.anchor_rotation_error_rad, local.anchor_rotation_error_rad),
            velocity_error_m_per_s=velocity_error, angular_velocity_error_rad_per_s=omega_error,
            carrier_speed_upper_m_per_s=speed, carrier_acceleration_upper_m_per_s2=acceleration,
            angular_speed_upper_rad_per_s=omega, angular_acceleration_upper_rad_per_s2=alpha,
            actual_speed_upper_m_per_s=actual_speed, actual_angular_speed_upper_rad_per_s=actual_omega)
        base = finish(max_position_l1_m=a.add(a.mul(F(2), offset), a.mul(F(4), VECTOR_ERROR)), **values)
        result = translated(base)
        work.remember(key, (location, result, base))
        return checked(result)

    def rotation_plan(omega, elapsed):
        plan = ops.spin_plan(omega, elapsed)
        simulator._register_spin_plan(omega, plan)

    def joint_local(joint, scalar):
        # Different joints may have identical numerical laws. Their own
        # authority/clock lookup has already produced this exact JointPhase;
        # only the pure local-bound equations are shared. Decode the complete
        # axis and guard every scalar before a cache hit can return a result.
        axis = tuple(a.number(value) for value in joint.axis)
        work.charge("phase_joint_bound_key")
        values = tuple(getattr(scalar, name) for name in _JOINT_PHASE_FIELDS)
        if any(type(value) is not F for value in values):
            raise ReachAdmissionError("reach_numeric", "A local joint bound requires exact phase operands.")
        work.guard(*values)
        key = (_CACHE_DOMAIN, work.max_operand_bits, "joint_local", joint.kind, axis, scalar)
        cached = work.lookup(key)
        if cached is not None:
            return cached
        axis_size = a.add(*(a.absolute(value) for value in axis))
        rate_error = a.absolute(a.sub(scalar.actual_slope, scalar.ideal_slope))
        if joint.kind == "hinge":
            # |norm(axis)-1| <= |norm(axis)^2-1|, without a host sqrt or an
            # assumption that the canonical source axis has exact unit length.
            norm_defect = a.absolute(a.sub(a.add(*(a.mul(x, x) for x in axis)), F(1)))
            omega_error = a.add(a.mul(axis_size, rate_error),
                a.mul(norm_defect, a.absolute(scalar.ideal_slope)))
            result = finish(trig_count=1, product_count=1,
                coordinate_angle_error_rad=scalar.coordinate_error,
                angular_velocity_error_rad_per_s=omega_error,
                angular_speed_upper_rad_per_s=a.absolute(scalar.ideal_slope),
                actual_angular_speed_upper_rad_per_s=a.mul(axis_size, a.absolute(scalar.actual_slope)))
        else:
            extent = a.mul(axis_size, a.maximum(a.absolute(scalar.actual_start), a.absolute(scalar.actual_end)))
            result = finish(max_position_l1_m=extent, product_count=1,
                anchor_position_error_m=a.mul(axis_size, scalar.coordinate_error),
                velocity_error_m_per_s=a.mul(axis_size, rate_error),
                carrier_speed_upper_m_per_s=a.mul(axis_size, a.absolute(scalar.ideal_slope)),
                actual_speed_upper_m_per_s=a.mul(axis_size, a.absolute(scalar.actual_slope)))
        work.remember(key, result)
        return result

    def root(path):
        actual_position = tuple(a.number(value) for value in state.positions[path])
        ideal_position = state.ideal_positions[path]
        extent = a.l1(actual_position)
        position_error = a.l1(tuple(a.sub(x, y) for x, y in zip(actual_position, ideal_position)))
        speed = omega = F(0)
        axial_rate = _ZERO_AXIAL_RATE
        rotation_error = state.root_rotation_errors.get(path, F(0))
        trig, products = 0, 1
        claimant = state.claims.get((path, "translation"))
        if claimant is not None:
            action, runtime = model.actions[claimant], state.actions[claimant]
            elapsed = a.maximum(*(a.absolute(runtime.elapsed_at(time)) for time in (start, end)))
            extent = a.add(a.l1(runtime.initial), a.mul(a.l1(action.vector), elapsed))
            position_error = a.l1(tuple(a.sub(a.number(x), y) for x, y in zip(runtime.initial, runtime.ideal_initial)))
            speed = a.l1(action.vector) if runtime.status == "running" else F(0)
        claimant = state.claims.get((path, "orientation"))
        if claimant is not None:
            action, runtime = model.actions[claimant], state.actions[claimant]
            elapsed = a.maximum(*(a.absolute(runtime.elapsed_at(time)) for time in (start, end)))
            rotation_plan(action.vector, elapsed)
            rotation_error = runtime.ideal_rotation_error
            if any(action.vector) and elapsed:
                trig, products = 1, 3
            omega = a.l1(action.vector) if runtime.status == "running" else F(0)
            if runtime.status == "running":
                axial_rate = _root_axial_rate(action, runtime, work)
        bound = finish(max_position_l1_m=extent, trig_count=trig, product_count=products,
            anchor_position_error_m=position_error, anchor_rotation_error_rad=rotation_error,
            carrier_speed_upper_m_per_s=speed, angular_speed_upper_rad_per_s=omega,
            actual_speed_upper_m_per_s=speed, actual_angular_speed_upper_rad_per_s=omega)
        return bound, axial_rate

    def dynamic(path):
        anchor, error = state.dynamic[path], state.dynamic_errors.get(path, AnchorError())
        initial = anchor.state
        elapsed = a.maximum(a.absolute(a.sub(start, anchor.time)), a.absolute(a.sub(end, anchor.time)))
        error_elapsed = a.maximum(a.absolute(a.sub(start, state.dynamic_error_times[path])),
                                  a.absolute(a.sub(end, state.dynamic_error_times[path])))
        actual_acceleration = tuple(a.number(value) for value in simulator._acceleration(path, state))
        ideal_acceleration = state.ideal_accelerations[path]
        acceleration_error = a.l1(tuple(a.sub(x, y) for x, y in zip(actual_acceleration, ideal_acceleration)))
        velocity = a.l1(initial.velocity)
        acceleration = a.l1(actual_acceleration)
        extent = a.add(a.l1(initial.position), a.mul(velocity, elapsed),
            a.div(a.mul(acceleration, elapsed, elapsed), F(2)))
        actual_speed = a.add(velocity, a.mul(acceleration, elapsed))
        position_error = a.add(error.position_m, a.mul(error.velocity_m_per_s, error_elapsed),
            a.div(a.mul(acceleration_error, error_elapsed, error_elapsed), F(2)))
        velocity_error = a.add(error.velocity_m_per_s, a.mul(acceleration_error, error_elapsed), a.rounding(actual_speed))
        actual_omega = a.l1(initial.omega)
        rotation_plan(initial.omega, elapsed)
        moving = bool(actual_omega and elapsed)
        return finish(max_position_l1_m=extent, trig_count=int(moving), product_count=3 if moving else 1,
            anchor_position_error_m=position_error,
            anchor_rotation_error_rad=a.add(error.rotation_rad, a.mul(error.angular_velocity_rad_per_s, error_elapsed)),
            velocity_error_m_per_s=velocity_error,
            angular_velocity_error_rad_per_s=error.angular_velocity_rad_per_s,
            carrier_speed_upper_m_per_s=a.add(actual_speed, velocity_error),
            carrier_acceleration_upper_m_per_s2=a.l1(ideal_acceleration),
            angular_speed_upper_rad_per_s=a.add(actual_omega, error.angular_velocity_rad_per_s),
            actual_speed_upper_m_per_s=actual_speed, actual_angular_speed_upper_rad_per_s=actual_omega)

    def frame(path):
        if path not in frames:
            stem = path.removesuffix(".frame")
            if stem in model.objects:
                frames[path] = instance(stem)
            else:
                site = model.sites[stem]
                original = witness("site", stem)
                parent = instance(site.owner)
                rate = _transport_axial_rate(axial_rates[site.owner + ".frame"], site.pose.rotation, work)
                frames[path] = compose(parent, constant(site.pose), axial_rate=rate)
                axial_rates[path] = rate
                retain_angular(path, rate, frames[path], original, "site", stem)
        return frames[path]

    def instance(path):
        if path in objects:
            return objects[path]
        work.charge("phase_source_node")
        if path in resolving:
            raise ReachAdmissionError("reach_chain", "A phase topology contains a cycle.")
        resolving.add(path)
        if path in incoming:
            kind, relation = incoming[path]
            witness_kind, witness_path = ("follow" if kind == "follow" else "joint"), relation
            original = witness(witness_kind, witness_path)
            if kind == "follow":
                follow = model.follows[relation]
                parent = frame(follow.parent)
                rate = _transport_axial_rate(axial_rates[follow.parent], follow.offset.rotation, work)
                result = compose(parent, constant(follow.offset), axial_rate=rate)
            else:
                joint = model.joints[relation]
                local = PhaseBound()
                if joint.kind in {"hinge", "slider"}:
                    if relation not in joints:
                        joints[relation] = joint_phase(simulator, relation, start, end, state)
                    local = joint_local(joint, joints[relation])
                parent = frame(joint.parent + ".frame")
                rate = axial_rates[joint.parent + ".frame"]
                if joint.kind == "hinge":
                    rate = _hinge_axial_rate(rate, joint.axis, joints[relation].ideal_slope, work)
                joint_bound = compose(parent, local, axial_rate=rate)
                child_pose = model.sites[joint.child].pose
                rate = _transport_axial_rate(rate, child_pose.rotation, work)
                result = compose(joint_bound, constant(child_pose, inverse=True), axial_rate=rate)
        elif state.modes[path] == "dynamic":
            result = dynamic(path)
            rate = None
            original = None
            witness_kind, witness_path = "root", path
        else:
            witness_kind, witness_path = "root", path
            original = witness(witness_kind, witness_path)
            result, rate = root(path)
        resolving.remove(path)
        objects[path] = result
        frames[path + ".frame"] = result
        axial_rates[path + ".frame"] = rate
        retain_angular(path + ".frame", rate, result, original, witness_kind, witness_path)
        return result

    if selected_frames is None:
        for path in model.objects:
            instance(path)
        for path in model.sites:
            frame(path + ".frame")
    else:
        for path in selected_frames:
            frame(path)
    result = {"objects": objects, "frames": frames, "joints": joints}
    if recording_proof:
        work.charge("phase_recording_proof_return")
        work.guard(start, end)
        result["recording_angular_proof"] = RecordingAngularProof(
            start, end, proof_revision, MappingProxyType(angular_frames))
    return result
