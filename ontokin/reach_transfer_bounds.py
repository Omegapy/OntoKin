"""Bounded scalar cell envelopes for an admitted first release.

The source still owns every actual pose and native anchor.  This helper carries
only transition proof radii and magnitudes.  It neither imports nor executes the
independent reader.  Unsupported first-release histories retain the ordinary
source allowance path.  See reach-release-cell-envelope.md for the finite-grid
recurrences and the deliberately restricted lineage domain.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction as F
from math import isfinite

from .reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, compare
from .reach_phase import AnchorError, PhaseArithmetic


GRID = F(1, 1 << 128)
EXPOSE = F(1, 1 << 53)
TINY = F(1, 1 << 1075)
PROOF_BITS = 256
PROOF_SCALE = 1 << PROOF_BITS
PROOF_GRID = F(1, PROOF_SCALE)
_LIMIT = 256


class _OwnerRef(tuple):
    """One strongly retained receipt owner, compared without invoking it.

    A bare address can be reused after a callback removes the original owner.
    The immutable tuple payload keeps that owner alive. State deepcopy keeps
    this identity token itself, so a retained model receipt never clones the
    model, its arithmetic context or their request callbacks.
    """
    __slots__ = ()

    def __new__(cls, owner):
        return tuple.__new__(cls, (owner,))

    def __eq__(self, other):
        return type(other) is _OwnerRef and self[0] is other[0]

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return id(self[0])

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def __repr__(self):
        return "<_OwnerRef " + type(self[0]).__name__ + ">"


@dataclass(frozen=True)
class CellEnvelope:
    position: F = F(0)
    rotation: F = F(0)
    velocity: F = F(0)
    omega: F = F(0)
    position_size: F = F(0)
    velocity_size: F = F(0)
    omega_size: F = F(0)


@dataclass(frozen=True)
class CellAnchor:
    clock: F
    envelope: CellEnvelope
    position_size: F
    velocity_size: F
    omega_size: F
    lineage: tuple
    witness: tuple


class CellArithmetic:
    """Outward scalar radius recurrences charged to the existing source work."""
    def __init__(self, work):
        self.work = work
        self.a = PhaseArithmetic(work)

    def less(self, left, right):
        return compare(left, right, self.work) < 0

    def upper(self, value):
        """Round only a nonnegative proof upper bound toward positive infinity.

        Capture integer operands before the first callback. The shift and
        directed quotient each retain a live prospective-width guard. Exact
        proof-grid values need no shift or quotient and remain unchanged.
        """
        numerator, denominator = ((value.numerator, value.denominator)
                                  if type(value) is F else (None, None))
        work = self.work
        work.charge("transfer_upper_round")
        if (type(numerator) is not int or type(denominator) is not int
                or numerator < 0 or denominator <= 0):
            raise ReachAdmissionError("reach_domain", "A cell upper bound must be a nonnegative rational.")
        work.guard(numerator, denominator, PROOF_SCALE)
        if denominator <= PROOF_SCALE and not denominator & (denominator - 1):
            return F(numerator, denominator)
        width = numerator.bit_length() + PROOF_BITS + 1
        work.guard_bits(width)
        shifted = numerator << PROOF_BITS
        work.charge("transfer_upper_ceil")
        work.guard(shifted, denominator, PROOF_SCALE)
        work.guard_bits(width)
        result = F(-((-shifted) // denominator), PROOF_SCALE)
        work.guard(result)
        return result

    def envelope(self, value):
        """Bound retained radii/magnitudes, without rounding source operands."""
        return CellEnvelope(*(self.upper(getattr(value, field)) for field in (
            "position", "rotation", "velocity", "omega",
            "position_size", "velocity_size", "omega_size")))

    def publication(self, size, dimensions=3):
        return self.a.add(self.a.mul(size, EXPOSE), self.a.mul(F(dimensions), TINY))

    def round_radius(self, radius, magnitude, dimensions=3):
        return self.upper(self.a.add(radius, self.publication(self.a.add(magnitude, radius), dimensions)))

    def expand(self, radius, magnitude, allowance, dimensions=3):
        result = self.a.add(radius, self.a.mul(F(dimensions), allowance),
                            self.a.mul(F(dimensions), GRID))
        return self.round_radius(result, magnitude, dimensions)

    def product(self, left, right):
        a = self.a
        return self.upper(a.add(a.mul(F(2), left), a.mul(F(2), right), a.mul(left, right), a.mul(F(28), GRID)))

    def normalize(self, radius):
        a = self.a
        if self.less(radius, F(1)):
            b = self.upper(a.add(radius, a.div(a.mul(F(3), GRID), a.sub(F(1), radius)), GRID))
            if self.less(b, F(1)):
                return self.upper(a.add(a.div(a.add(radius, a.mul(F(2), b)), a.sub(F(1), b)), a.mul(F(4), GRID)))
        # A successful finite square root has a positive g-lattice lower
        # endpoint. This coarse branch makes no small-radius admission claim.
        return self.upper(a.add(a.div(a.add(F(2), radius), GRID), F(2), a.mul(F(4), GRID)))

    def normalized_point(self, values):
        a = self.a
        values = tuple(a.number(value) for value in values)
        self.work.charge("transfer_normalized_point")
        self.work.guard(*values)
        dimensions = len(values)
        if dimensions not in (3, 4) or not any(values):
            raise ReachAdmissionError("reach_numeric", "A transfer axis or quaternion must be nonzero.")
        if ((dimensions == 4 and not any(values[1:])) or
                sum(bool(value) for value in values) == 1 and max(map(abs, values)) == 1):
            return F(0)
        lower = a.maximum(*(a.absolute(value) for value in values))
        b = self.upper(a.add(a.div(a.mul(F(dimensions - 1), GRID), lower), GRID))
        if self.less(b, lower):
            return self.upper(a.add(a.div(a.mul(F(2), b), a.sub(lower, b)), a.mul(F(dimensions), GRID)))
        return self.upper(a.add(a.div(a.l1(values), GRID), F(2), a.mul(F(dimensions), GRID)))

    def rotate(self, quaternion, vector, magnitude):
        a = self.a
        size = a.add(magnitude, vector)
        return self.upper(a.add(a.mul(F(4), vector),
            a.mul(a.add(a.mul(F(4), quaternion), a.mul(quaternion, quaternion)), size),
            a.mul(F(8), GRID, size), a.mul(F(100), GRID, a.add(F(1), quaternion))))

    def cross(self, left, right, left_size, right_size):
        a = self.a
        return self.upper(a.add(a.mul(left_size, right), a.mul(right_size, left),
                     a.mul(left, right), a.mul(F(9), GRID)))

    def sincos(self, half_error, half_size):
        a = self.a
        quadrant = a.add(half_size, half_error, F(1))
        return self.upper(a.add(a.mul(F(2), half_error), a.mul(a.add(a.mul(F(24), quadrant), F(6)), GRID)))

    def spin(self, native_omega, radius, source_error, elapsed):
        a = self.a
        native = tuple(a.number(value) for value in native_omega)
        elapsed = a.absolute(a.number(elapsed))
        self.work.charge("transfer_spin_identity")
        self.work.guard(*native, radius, source_error, elapsed)
        if not elapsed or not any(native) and not radius and not source_error:
            return F(0)
        size = a.add(a.l1(native), a.mul(F(2), source_error))
        lower = a.sub(a.maximum(*(a.absolute(value) for value in native)), source_error)
        axis = None
        if self.less(radius, lower):
            norm_error = self.upper(a.add(radius, a.div(a.mul(F(3), GRID), a.sub(lower, radius)), GRID))
            if self.less(norm_error, lower):
                axis = self.upper(a.add(a.div(a.add(radius, a.mul(F(2), norm_error)),
                                   a.sub(lower, norm_error)), a.mul(F(3), GRID)))
        if axis is None:
            norm_error = self.upper(a.add(radius, F(1, 1 << 63), GRID))
        half_error = a.add(a.div(a.mul(elapsed, norm_error), F(2)), GRID)
        epsilon = self.sincos(half_error, a.div(a.mul(size, elapsed), F(2)))
        if axis is None:
            return self.upper(a.add(a.mul(a.add(F(1), epsilon),
                a.add(F(1), a.div(a.add(size, radius), GRID), a.mul(F(3), GRID))),
                F(2), a.mul(F(3), GRID)))
        return self.upper(a.add(a.mul(axis, a.add(F(1), epsilon)), a.mul(F(3), epsilon), a.mul(F(3), GRID)))

    def constant(self, position, rotation, *, inverse=False):
        size = self.a.l1(position)
        quaternion = self.normalized_point(rotation)
        return self.envelope(CellEnvelope(self.rotate(quaternion, F(0), size) if inverse else F(0), quaternion,
                            position_size=self.a.mul(F(2), size) if inverse else size))

    def compose(self, parent, local):
        a = self.a
        offset = self.rotate(parent.rotation, local.position, local.position_size)
        offset_size = a.mul(F(2), local.position_size)
        velocity = a.add(parent.velocity,
            self.cross(parent.omega, offset, parent.omega_size, offset_size),
            self.rotate(parent.rotation, local.velocity, local.velocity_size), a.mul(F(6), GRID))
        omega = a.add(parent.omega,
            self.rotate(parent.rotation, local.omega, local.omega_size), a.mul(F(3), GRID))
        return self.envelope(CellEnvelope(
            a.add(parent.position, offset, a.mul(F(3), GRID)),
            self.product(parent.rotation, local.rotation), velocity, omega,
            a.add(parent.position_size, offset_size),
            a.add(parent.velocity_size, a.mul(parent.omega_size, offset_size),
                  a.mul(F(2), local.velocity_size)),
            a.add(parent.omega_size, a.mul(F(2), local.omega_size))))

    def scalar(self, law):
        """Both original affine scalar laws, with actual binary64 exposure."""
        a = self.a
        if law[0] == "constant":
            actual, ideal = (a.number(value) for value in law[1:])
            return ideal, F(0), F(0), a.absolute(a.sub(actual, ideal))
        _, initial, ideal_initial, target, duration, elapsed, since, running, time = law
        initial, ideal_initial, target, duration, elapsed, since, time = (
            a.number(value) for value in (initial, ideal_initial, target, duration, elapsed, since, time))
        if running:
            elapsed = a.add(elapsed, a.sub(time, since))
        actual_rate = a.div(a.sub(target, initial), duration)
        ideal_rate = a.div(a.sub(target, ideal_initial), duration)
        actual = a.add(initial, a.mul(actual_rate, elapsed))
        ideal = a.add(ideal_initial, a.mul(ideal_rate, elapsed))
        error = a.add(a.absolute(a.sub(actual, ideal)), a.rounding(a.absolute(actual)))
        return ideal, actual_rate if running else F(0), ideal_rate if running else F(0), error

    def joint(self, kind, axis, law):
        a = self.a
        ideal, actual_rate, ideal_rate, coordinate_error = self.scalar(law)
        axis = tuple(a.number(value) for value in axis)
        size = a.l1(axis)
        rate_error = a.absolute(a.sub(actual_rate, ideal_rate))
        if kind == "slider":
            return self.envelope(CellEnvelope(a.add(a.mul(size, coordinate_error), a.mul(F(3), GRID)),
                velocity=a.add(a.mul(size, rate_error), a.mul(F(3), GRID)),
                position_size=a.mul(size, a.absolute(ideal)), velocity_size=a.mul(size, a.absolute(ideal_rate))))
        axis_error = self.normalized_point(axis)
        epsilon = self.sincos(a.add(a.div(coordinate_error, F(2)), GRID), a.div(a.absolute(ideal), F(2)))
        rotation = a.add(a.mul(axis_error, a.add(F(1), epsilon)), a.mul(F(3), epsilon), a.mul(F(3), GRID))
        defect = a.absolute(a.sub(a.add(*(a.mul(value, value) for value in axis)), F(1)))
        physical = a.add(a.mul(size, rate_error), a.mul(defect, a.absolute(ideal_rate)))
        omega = a.add(a.mul(F(2), physical), a.mul(axis_error, a.absolute(ideal_rate)), a.mul(F(3), GRID))
        return self.envelope(CellEnvelope(rotation=rotation, omega=omega, omega_size=a.mul(F(2), a.absolute(ideal_rate))))

    def root(self, position, rotation, ideal_position, move, spin, time):
        a = self.a
        canonical = tuple(a.number(value) for value in position)
        ideal = tuple(a.number(value) for value in ideal_position)
        self.work.charge("transfer_canonical_initial")
        self.work.guard(*canonical, *ideal)
        if canonical != ideal:
            raise _Unsupported
        result = self.constant(position, rotation)
        if move is not None:
            vector, elapsed, since, running, ideal_initial = move
            initial = tuple(a.number(value) for value in ideal_initial)
            self.work.charge("transfer_canonical_initial")
            self.work.guard(*canonical, *initial)
            if initial != canonical:
                raise _Unsupported
            elapsed = a.number(elapsed)
            if running:
                elapsed = a.add(elapsed, a.sub(a.number(time), a.number(since)))
            size = a.l1(vector)
            result = replace(result, position=a.mul(F(6), GRID),
                position_size=a.add(result.position_size, a.mul(size, a.absolute(a.number(elapsed)))),
                velocity_size=size if running else F(0))
        if spin is not None:
            vector, elapsed, since, running = spin
            elapsed = a.number(elapsed)
            if running:
                elapsed = a.add(elapsed, a.sub(a.number(time), a.number(since)))
            result = replace(result,
                rotation=self.product(self.spin(vector, F(0), F(0), elapsed), result.rotation),
                omega_size=a.l1(vector) if running else F(0))
        return self.envelope(result)

    def released(self, incoming, error):
        return self.envelope(CellEnvelope(
            self.expand(incoming.position, incoming.position_size, error.position_m),
            self.normalize(self.expand(incoming.rotation, F(2), error.rotation_rad, 4)),
            self.expand(incoming.velocity, incoming.velocity_size, error.velocity_m_per_s),
            self.expand(incoming.omega, incoming.omega_size, error.angular_velocity_rad_per_s),
            incoming.position_size, incoming.velocity_size, incoming.omega_size))

    def dynamic(self, proof, native_omega, error, acceleration, ideal_acceleration, elapsed):
        a = self.a
        initial = proof.envelope
        elapsed = a.absolute(a.number(elapsed))
        acceleration_error = a.l1(tuple(a.sub(a.number(x), a.number(y))
                                       for x, y in zip(acceleration, ideal_acceleration)))
        ideal_size = a.l1(ideal_acceleration)
        return self.envelope(CellEnvelope(
            a.add(initial.position, a.mul(initial.velocity, elapsed),
                  a.div(a.mul(acceleration_error, elapsed, elapsed), F(2)), a.mul(F(12), GRID)),
            self.product(self.spin(native_omega, initial.omega, error.angular_velocity_rad_per_s, elapsed),
                         initial.rotation),
            a.add(initial.velocity, a.mul(acceleration_error, elapsed), a.mul(F(6), GRID)), initial.omega,
            a.add(initial.position_size, a.mul(initial.velocity_size, elapsed),
                  a.div(a.mul(ideal_size, elapsed, elapsed), F(2))),
            a.add(initial.velocity_size, a.mul(ideal_size, elapsed)), initial.omega_size))

    def forced(self, point, before, *, changed):
        if not changed:
            return point
        return self.envelope(replace(point,
            position=self.round_radius(point.position, point.position_size),
            rotation=self.normalize(self.expand(point.rotation, F(2), before.rotation_rad, 4)),
            velocity=self.round_radius(point.velocity, point.velocity_size),
            omega=self.round_radius(point.omega, point.omega_size)))

    def impulse(self, point, before, self_point, impulse, mass, inertia):
        a = self.a
        lever_size = a.mul(F(2), a.l1(self_point))
        impulse_size = a.l1(impulse)
        lever = self.rotate(point.rotation, F(0), a.l1(self_point))
        allowance = a.add(a.mul(before.rotation_rad, a.l1(self_point)), F(1, 1 << 96))
        actual_lever = self.expand(lever, lever_size, allowance)
        angular = self.cross(actual_lever, F(0), lever_size, impulse_size)
        angular = self.round_radius(angular, a.mul(lever_size, impulse_size))
        inverse_mass, inverse_inertia = a.div(F(1), a.number(mass)), a.div(F(1), a.number(inertia))
        velocity = self.expand(point.velocity, point.velocity_size, before.velocity_m_per_s)
        # The exact impulse scale contributes at most three endpoint grids.
        velocity = a.add(velocity, a.mul(F(6), GRID))
        velocity_size = a.add(point.velocity_size, a.mul(impulse_size, inverse_mass))
        velocity = self.round_radius(velocity, velocity_size)
        omega = self.expand(point.omega, point.omega_size, before.angular_velocity_rad_per_s)
        omega = a.add(omega, a.mul(angular, inverse_inertia), a.mul(F(6), GRID))
        omega_size = a.add(point.omega_size, a.mul(lever_size, impulse_size, inverse_inertia))
        omega = self.round_radius(omega, omega_size)
        # Actual expansion contains the old ideal cells. Its lever/cross/
        # scales and rounding also dominate the corresponding ideal formula.
        return self.envelope(CellEnvelope(
            self.expand(point.position, point.position_size, before.position_m),
            self.normalize(self.expand(point.rotation, F(2), before.rotation_rad, 4)),
            velocity, omega, point.position_size, velocity_size, omega_size))

    def point_sizes(self, proof, acceleration, ideal_acceleration, elapsed):
        a = self.a
        elapsed = a.absolute(a.number(elapsed))
        acceleration_size = a.maximum(a.l1(acceleration), a.l1(ideal_acceleration))
        return (self.upper(a.add(proof.position_size, a.mul(proof.velocity_size, elapsed),
                      a.div(a.mul(acceleration_size, elapsed, elapsed), F(2)), a.mul(F(12), GRID))),
                self.upper(a.add(proof.velocity_size, a.mul(acceleration_size, elapsed), a.mul(F(6), GRID))),
                proof.omega_size)

    def rounded_sizes(self, sizes):
        return tuple(self.upper(self.a.add(size, self.publication(size))) for size in sizes)

    def expanded_size(self, size, allowance):
        enlarged = self.a.add(size, self.a.mul(F(3), allowance), self.a.mul(F(3), GRID))
        return self.upper(self.a.add(enlarged, self.publication(enlarged)))

    def impulse_sizes(self, point, sizes, before, self_point, impulse, mass, inertia):
        a = self.a
        point_size, impulse_size = a.l1(self_point), a.l1(impulse)
        ideal_lever_size = a.mul(F(2), point_size)
        lever_size = a.add(ideal_lever_size, self.rotate(point.rotation, F(0), point_size))
        allowance = a.add(a.mul(before.rotation_rad, point_size), F(1, 1 << 96))
        lever_size = self.expanded_size(lever_size, allowance)
        angular_size = a.add(a.mul(lever_size, impulse_size), a.mul(F(9), GRID))
        angular_size = a.add(angular_size, self.publication(angular_size))
        velocity_size = a.add(self.expanded_size(sizes[1], before.velocity_m_per_s),
                             a.div(impulse_size, a.number(mass)), a.mul(F(6), GRID))
        omega_size = a.add(self.expanded_size(sizes[2], before.angular_velocity_rad_per_s),
                          a.div(angular_size, a.number(inertia)), a.mul(F(6), GRID))
        return (self.expanded_size(sizes[0], before.position_m),
                self.upper(a.add(velocity_size, self.publication(velocity_size))),
                self.upper(a.add(omega_size, self.publication(omega_size))))


class _Unsupported(Exception):
    """An optional source lineage keeps its original ordinary proof path."""


_TABLES = ("objects", "sites", "joints", "follows", "actions")
# The recording planner changes only its two observation hooks. Every method
# that supplies native source values, transfer state, or their admission must
# retain the ordinary implementation. Keep this fixed list bounded and bind
# the actual class/function identities in the complete lineage receipt.
_SOURCE_METHODS = (
    "__init__", "_numeric_error", "_work_check", "_invalidate", "_pose_slot",
    "_translated_source_slot", "_constant_pose", "_incoming", "_register_spin_plan",
    "_advance_orientation", "phase_bounds", "_anchor_bound", "_anchor_error",
    "_ideal_coordinate", "_ideal_position", "ordinary_target", "_pair", "_coordinate",
    "_exact_coordinate", "_dynamic_kinematics", "_kinematics", "_pose_cache_time",
    "recording_frames", "recording_moving_frames", "_terminal_static_kinematics",
    "_resolve_kinematics", "_tip_base", "_world_target", "_latch_ordinary",
    "_exposed_vector", "_impulse_lever", "_impulse_point", "_impulse_cross",
    "_impulse_velocity", "_impulse_anchor", "_impulse_error", "_ideal_acceleration",
    "_bounded_projection", "_force_components", "_event", "_latch", "_process_boundary",
    "incoming_releases_at", "_aggregate", "_validate_staged", "_pose_record",
    "_physical_observation", "_current", "_reach_map", "_release_record",
    "recording_boundary", "_snapshot_data", "advance", "_check", "_acceleration",
    "_next_boundary", "_change", "_projection", "_check_dynamic_extrema", "_channel",
    "_dependencies")


def _source_method_receipt(simulator):
    from .reach_runtime import ReachSimulator

    kind = type(simulator)
    if type(kind) is not type or len(kind.__mro__) > 8 or ReachSimulator not in kind.__mro__:
        raise _Unsupported
    absent = object()

    def raw(mro, name):
        # Class-level getattr would invoke a descriptor that can disguise a
        # foreign instance method as the original function. Read raw entries.
        for base in mro:
            namespace = vars(base)
            if name in namespace:
                return namespace[name]
        return absent

    mro, native_mro = kind.__mro__, ReachSimulator.__mro__
    storage = []
    for name in ("__getattribute__", "__setattr__", "__delattr__", "__dict__"):
        actual = raw(mro, name)
        if actual is not raw(native_mro, name):
            raise _Unsupported
        storage.append(_OwnerRef(actual))
    if raw(mro, "__getattr__") is not absent:
        raise _Unsupported
    namespace = object.__getattribute__(simulator, "__dict__")
    methods = []
    for name in _SOURCE_METHODS:
        actual = raw(mro, name)
        if name in namespace or actual is absent or actual is not raw(native_mro, name):
            raise _Unsupported
        methods.append(_OwnerRef(actual))
    # Context fields must use ordinary instance storage, not a subclass's
    # descriptor that can return different owners between receipt checks.
    for name in ("model", "state", "work", "pose_ops", "_check_callback"):
        if raw(mro, name) is not absent:
            raise _Unsupported
    return _OwnerRef(kind), tuple(storage), tuple(methods)


def _literal(value, work, depth=0):
    """Callback-free bounded copies of typed immutable source operands."""
    from .reach_pose import RotationValue
    if depth > 8:
        raise _Unsupported
    kind = type(value)
    if value is None or kind is bool:
        return kind.__name__, value
    if kind is str:
        if len(value) > 4096:
            raise _Unsupported
        return "str", value
    if kind is float:
        if not isfinite(value):
            raise _Unsupported
        work.guard_bits(1075)
        return "float", value.hex()
    if kind in (F, int):
        work.guard(value)
        return kind.__name__, value.numerator, value.denominator
    if kind is tuple and len(value) <= 32:
        return "tuple", tuple(_literal(part, work, depth + 1) for part in value)
    if kind is RotationValue:
        return "rotation", _literal((value.components, value.error_rad, value.frozen_projection), work, depth + 1)
    raise _Unsupported


def _copy(value):
    """Copy admitted scalar leaves before a callback can mutate a wrapper."""
    if type(value) is F:
        return F(value.numerator, value.denominator)
    if type(value) is tuple:
        return tuple(_copy(part) for part in value)
    return value


def _plain_receipt(value, work):
    """Admit the bounded immutable structure made by the source snapshots."""
    pending, remaining = [(value, 0)], _LIMIT * _LIMIT
    while pending:
        current, depth = pending.pop()
        remaining -= 1
        if remaining < 0 or depth > 24:
            raise _Unsupported
        kind = type(current)
        if current is None or kind is bool:
            continue
        if kind is _OwnerRef and len(current) == 1:
            # The owner is opaque source authority, not another receipt tree
            # or a numerical operand. Its address retains the old width check;
            # equality relies only on the strongly held object itself.
            work.guard(id(current[0]))
        elif kind is int:
            work.guard(current)
        elif kind is str and len(current) <= 4096:
            continue
        elif kind is tuple and len(current) <= _LIMIT:
            pending.extend((part, depth + 1) for part in current)
        else:
            raise _Unsupported
    return value


def _proof_receipt(proof, work):
    if type(proof) is not CellAnchor or type(proof.envelope) is not CellEnvelope:
        raise _Unsupported
    numbers = (proof.clock, proof.position_size, proof.velocity_size, proof.omega_size,
               *(getattr(proof.envelope, name) for name in CellEnvelope.__dataclass_fields__))
    if any(type(value) is not F for value in numbers):
        raise _Unsupported
    work.guard(*numbers)
    if any(value < 0 for value in numbers):
        raise _Unsupported
    return (_literal(numbers, work), _plain_receipt(proof.lineage, work),
            _plain_receipt(proof.witness, work))


def _copy_proof(proof):
    envelope = CellEnvelope(*(_copy(getattr(proof.envelope, name))
                              for name in CellEnvelope.__dataclass_fields__))
    return CellAnchor(_copy(proof.clock), envelope, _copy(proof.position_size),
                      _copy(proof.velocity_size), _copy(proof.omega_size),
                      proof.lineage, proof.witness)


def _table_token(state, path):
    table = state.dynamic_cells
    if type(table) is not dict or len(table) > _LIMIT or path not in table and len(table) == _LIMIT:
        raise ReachAdmissionError("reach_domain", "The bounded dynamic proof table is unavailable.")
    return table, table.get(path)


def _table_admit(state, path, token):
    table, previous = token
    if state.dynamic_cells is not table or table.get(path) is not previous:
        raise ReachAdmissionError("reach_domain", "The dynamic proof entry changed during its transition.")


def _pose(value):
    from .model import Pose
    if type(value) is not Pose:
        raise _Unsupported
    return value.frame, value.position, value.rotation


def _model_snapshot(simulator):
    """Capture the complete bounded numeric topology before any arithmetic."""
    from .model import ActionModel, FollowModel, JointModel, ObjectModel, ReachPayload, SceneModel, SiteModel
    from .reach_pose import ReachPoseOps
    methods = _source_method_receipt(simulator)
    model, work = simulator.model, simulator.work
    if (type(model) is not SceneModel or type(simulator.pose_ops) is not ReachPoseOps
            or simulator.pose_ops.work is not work):
        raise _Unsupported
    tables = tuple(getattr(model, name) for name in _TABLES)
    if (type(work.max_cache_entries) is not int
            or not 0 < work.max_cache_entries <= _LIMIT
            or any(type(table) is not dict for table in tables)
            or sum(map(len, tables)) > _LIMIT):
        raise _Unsupported
    copied, receipts = {}, []
    expected = dict(zip(_TABLES, (ObjectModel, SiteModel, JointModel, FollowModel, ActionModel)))
    for name, table in zip(_TABLES, tables):
        rows, receipt = {}, []
        for path, value in table.items():
            if type(path) is not str or type(value) is not expected[name] or value.path != path:
                raise _Unsupported
            identity = (value.path, value.element_id, getattr(value, "owner", None))
            reach_inputs = None
            if name == "objects":
                if type(value.physical) is not dict:
                    raise _Unsupported
                row = (value.motion, _pose(value.placement), value.velocity, value.omega,
                       value.physical.get("kind"), value.mass, value.inertia)
                owners = (_OwnerRef(value.placement), _OwnerRef(value.physical))
            elif name == "sites":
                row, owners = (value.owner, _pose(value.pose)), (_OwnerRef(value.pose),)
            elif name == "joints":
                row = (value.kind, value.parent, value.child, value.axis, value.initial, value.limits)
                owners = ()
            elif name == "follows":
                row, owners = (value.parent, value.child, _pose(value.offset)), (_OwnerRef(value.offset),)
            else:
                reach = value.reach
                if reach is not None and type(reach) is not ReachPayload:
                    raise _Unsupported
                pair = None if reach is None else (reach.shoulder, reach.elbow)
                row = (value.kind, value.target, value.duration, value.vector, value.goal, pair)
                owners = (_OwnerRef(reach),)
                if reach is not None:
                    reach_inputs = (reach.shoulder, reach.elbow, reach.tip, reach.target_frame,
                        reach.target_m, reach.branch, reach.base_frame, reach.lengths_m,
                        reach.limits_rad, reach.description_identity)
            receipt.append((path, _OwnerRef(value), owners, _literal((identity, row, reach_inputs), work)))
            rows[path] = _copy(row)
        copied[name] = rows
        receipts.append((name, _OwnerRef(table), tuple(receipt)))
    header = (_OwnerRef(model), _OwnerRef(work), _OwnerRef(simulator.pose_ops), methods,
              _literal((model.program_revision, model.duration, model.gravity), work))
    return copied, (header, tuple(receipts))


def _state_snapshot(simulator, state):
    from .reach_runtime import _ReachActionState, _ReachRunState
    work = simulator.work
    if type(state) is not _ReachRunState:
        raise _Unsupported
    copied, receipt = {}, []
    fields = ("modes", "positions", "orientations", "ideal_positions", "root_rotation_errors",
              "root_rotation_values", "coordinates", "ideal_coordinates", "claims")
    for name in fields:
        table = getattr(state, name)
        if type(table) is not dict or len(table) > _LIMIT:
            raise _Unsupported
        rows = tuple(table.items())
        copied[name] = {key: _copy(value) for key, value in rows}
        receipt.append((name, _OwnerRef(table), tuple((_literal(key, work), _literal(value, work)) for key, value in rows)))
    if (type(state.actions) is not dict or len(state.actions) > _LIMIT
            or type(state.active_grips) not in (set, frozenset) or len(state.active_grips) > _LIMIT
            or any(type(path) is not str for path in state.active_grips)):
        raise _Unsupported
    active = {}
    for path, runtime in state.actions.items():
        if type(path) is not str or type(runtime) is not _ReachActionState:
            raise _Unsupported
        target = None if runtime.solution is None else runtime.solution.target_rad
        row = (runtime.status, runtime.elapsed, runtime.running_since, runtime.initial,
               runtime.ideal_initial, runtime.ideal_rotation_error, runtime.initial_rotation, target)
        active[path] = _copy(row)
        receipt.append(("action", path, _OwnerRef(runtime), _OwnerRef(runtime.solution), _literal(row, work)))
    copied["actions"] = active
    copied["grips"] = frozenset(state.active_grips)
    receipt.append(("grips", _OwnerRef(state.active_grips), tuple(sorted(state.active_grips))))
    return copied, (_OwnerRef(state), _OwnerRef(simulator.state), tuple(receipt))


def _first_ancestry(simulator, state, path, time):
    from .reach_pose import ReachPoseOps
    work = simulator.work
    if (type(simulator.pose_ops) is not ReachPoseOps
            or simulator.pose_ops.work is not work or work.max_operand_bits != MAX_OPERAND_BITS
            or path in state.dynamic or type(time) is not F):
        raise _Unsupported
    model, lineage = _model_snapshot(simulator)
    source, state_receipt = _state_snapshot(simulator, state)
    incoming = {}
    for name, joint in model["joints"].items():
        kind, parent, child, *_ = joint
        if kind != "grip" or name in source["grips"]:
            incoming[model["sites"][child][0]] = ("joint", name)
    for name, follow in model["follows"].items():
        incoming[follow[1]] = ("follow", name)
    nodes, resolved, active = [], {}, set()

    def add(node):
        if len(nodes) >= _LIMIT:
            raise _Unsupported
        index = len(nodes)
        nodes.append(node)
        return index

    def constant(pose, inverse=False):
        return add(("constant", pose[1], pose[2], inverse))

    def compose(parent, local):
        return add(("compose", parent, local))

    def law(relation):
        claimant = source["claims"].get((relation, "coordinate"))
        if claimant is None:
            return ("constant", source["coordinates"][relation], source["ideal_coordinates"][relation])
        action, runtime = model["actions"][claimant], source["actions"][claimant]
        kind, _, duration, _, goal, pair = action
        status, elapsed, since, initial, ideal_initial, _, _, targets = runtime
        if status not in ("running", "paused"):
            raise _Unsupported
        if kind == "reach_planar" and pair is not None and relation in pair:
            index = pair.index(relation)
            initial, ideal_initial, target = initial[index], ideal_initial[index], targets[index]
        elif kind == "tween":
            target = goal
        else:
            raise _Unsupported
        return ("claimed", initial, ideal_initial, target, duration, elapsed, since, status == "running", time)

    def root(name):
        obj = model["objects"][name]
        placement = obj[1]
        if (source["modes"].get(name) != "prescribed" or
                source["positions"].get(name) != placement[1] or
                source["orientations"].get(name) != placement[2] or
                source["root_rotation_values"].get(name) is not None or
                source["root_rotation_errors"].get(name, F(0)) != 0):
            raise _Unsupported
        move = spin = None
        for action_path, action in model["actions"].items():
            kind, target, _, vector, _, _ = action
            if target != name or kind not in ("move", "spin"):
                continue
            runtime = source["actions"][action_path]
            status, elapsed, since, initial, ideal_initial, rotation_error, initial_rotation, _ = runtime
            if status == "pending":
                continue
            channel = "translation" if kind == "move" else "orientation"
            if (status not in ("running", "paused") or
                    source["claims"].get((name, channel)) != action_path or
                    initial != placement[1 if kind == "move" else 2] or
                    initial_rotation is not None or rotation_error != 0):
                raise _Unsupported
            if kind == "move":
                move = (vector, elapsed, since, status == "running", ideal_initial)
            else:
                spin = (vector, elapsed, since, status == "running")
        # A foreign or missing claimant must not be hidden by an absent law.
        if (source["claims"].get((name, "translation")) is not None and move is None or
                source["claims"].get((name, "orientation")) is not None and spin is None):
            raise _Unsupported
        return add(("root", placement[1], placement[2], source["ideal_positions"][name], move, spin, time))

    def frame(name):
        if name == "world":
            if name not in resolved:
                resolved[name] = add(("world",))
            return resolved[name]
        if name in resolved:
            return resolved[name]
        if name in active or len(active) >= 64:
            raise _Unsupported
        active.add(name)
        stem = name.removesuffix(".frame")
        if stem in model["objects"]:
            if source["modes"].get(stem) != "prescribed":
                raise _Unsupported
            if stem not in incoming:
                result = root(stem)
            else:
                kind, relation = incoming[stem]
                if kind == "follow":
                    parent, _, offset = model["follows"][relation]
                    result = compose(frame(parent), constant(offset))
                else:
                    joint_kind, parent, child, axis, *_ = model["joints"][relation]
                    parent_value = frame(parent + ".frame")
                    if joint_kind in ("hinge", "slider"):
                        local = add(("joint", joint_kind, axis, law(relation)))
                    elif joint_kind in ("fixed", "grip"):
                        local = add(("world",))
                    else:
                        raise _Unsupported
                    result = compose(compose(parent_value, local), constant(model["sites"][child][1], True))
        else:
            owner, pose = model["sites"][stem]
            result = compose(frame(owner + ".frame"), constant(pose))
        active.remove(name)
        resolved[name] = result
        return result

    selected = frame(path + ".frame")
    receipt = (lineage, state_receipt, tuple(nodes), selected, _literal(time, work))
    return _copy(tuple(nodes)), selected, receipt


@dataclass
class _FirstRelease:
    simulator: object
    state: object
    path: str
    time: F
    nodes: tuple
    selected: int
    receipt: tuple
    work: object
    pose_ops: object

    @property
    def lineage(self):
        return self.receipt[0]

    def admit(self):
        sim = self.simulator
        if (sim.work is not self.work or sim.pose_ops is not self.pose_ops or
                self.pose_ops.work is not self.work or self.work.max_operand_bits != MAX_OPERAND_BITS):
            raise ReachAdmissionError("reach_domain", "A release envelope's arithmetic owner or cap changed.")
        try:
            current = _first_ancestry(sim, self.state, self.path, self.time)[2]
        except (KeyError, TypeError, AttributeError, _Unsupported) as error:
            raise ReachAdmissionError("reach_domain", "The admitted release ancestry changed.") from error
        if current != self.receipt:
            raise ReachAdmissionError("reach_domain", "The admitted release ancestry changed.")

    def evaluate(self):
        arithmetic = CellArithmetic(self.work)
        values = []
        for node in self.nodes:
            self.work.charge("transfer_ancestry_node")
            kind, *args = node
            if kind == "world":
                value = CellEnvelope()
            elif kind == "compose":
                value = arithmetic.compose(*(values[index] for index in args))
            elif kind == "constant":
                value = arithmetic.constant(*args[:2], inverse=args[2])
            elif kind == "joint":
                value = arithmetic.joint(*args)
            else:
                value = arithmetic.root(*args)
            values.append(value)
        self.work.charge("transfer_ancestry_guard", _release_units(self.nodes, self.receipt))
        self.admit()
        return values[self.selected]


def _release_units(nodes, receipt):
    state = receipt[1][2]
    state_rows = sum(1 if row[0] == "action" else len(row[2]) for row in state)
    return len(nodes) + sum(len(rows[2]) for rows in receipt[0][1]) + state_rows + 1


def first_release(simulator, state, path, time):
    """Return a source-only recipe, or preserve the unsupported ordinary path."""
    work, ops = simulator.work, simulator.pose_ops
    try:
        nodes, selected, receipt = _first_ancestry(simulator, state, path, time)
    except (KeyError, TypeError, AttributeError, _Unsupported):
        work.charge("transfer_release_domain")
        return None
    result = _FirstRelease(simulator, state, path, time, nodes, selected, receipt, work, ops)
    work.charge("transfer_release_capture", _release_units(nodes, receipt))
    result.admit()
    return result


def _native_pose(value, simulator):
    from .evaluator import _Kinematics
    from .reach_pose import PoseValue, RotationValue
    work = simulator.work
    if type(value) is PoseValue:
        if (value._ops is not simulator.pose_ops or type(value.rotation) is not RotationValue
                or type(value._projection) is not dict):
            raise _Unsupported
        # Materialized anchor operands are exact rational copies of its native
        # tuple. Do not call a live projection property while taking a receipt.
        vectors = (value.exact_position, value.exact_velocity, value.exact_omega)
        fields = ("position", "orientation", "velocity", "omega")
        if len(value._projection) > 4 or set(value._projection) - set(fields):
            raise _Unsupported
        projection = tuple((name, value._projection[name]) for name in fields if name in value._projection)
        identity = (vectors, value.rotation.components, value.rotation.error_rad,
                    value.rotation.frozen_projection, value.position_error_m, projection)
    elif type(value) is _Kinematics:
        vectors = (value.position, value.velocity, value.omega)
        identity = (vectors, value.orientation)
    else:
        raise _Unsupported
    if any(type(vector) is not tuple or len(vector) != 3 for vector in vectors):
        raise _Unsupported
    return _copy(vectors), _literal(identity, work)


def _force_receipt(history, work):
    from .force_runtime import _ActiveForce, _ForceState
    from .model import ForcePayload
    if (type(history) is not _ForceState or type(history.active) is not dict
            or type(history.last_changes) is not list
            or len(history.active) + len(history.last_changes) > _LIMIT):
        raise _Unsupported

    def force(value):
        if type(value) is not _ActiveForce or type(value.payload) is not ForcePayload:
            raise _Unsupported
        payload = value.payload
        return (value.target, value.activation, payload.key, payload.force_world_n,
                payload.duration, payload.sequence_index)

    active = tuple((_literal(key, work), _literal(force(value), work)) for key, value in history.active.items())
    changes = tuple((_literal(kind, work), _literal(force(value), work)) for kind, value in history.last_changes)
    return (active, changes, _literal((history.started_count, history.completed_count, history.last_time), work))


def _source_owners(state, path, *, anchor=True):
    fields = ("dynamic", "dynamic_cells", "dynamic_errors", "dynamic_error_times",
              "ideal_accelerations", "forces", "modes", "claims")
    owners = (state, *(getattr(state, name) for name in fields))
    if anchor:
        current = state.dynamic[path]
        owners += (current, current.state, state.dynamic_errors[path], state.forces[path])
    return owners


def _same_source_owners(state, path, owners, *, anchor=True):
    current = _source_owners(state, path, anchor=anchor)
    return len(current) == len(owners) and all(left is right for left, right in zip(current, owners))


def _dynamic_snapshot(simulator, state, path, *, error_override=None):
    from .evaluator import _DynamicInitial
    anchor, history = state.dynamic[path], state.forces[path]
    error = state.dynamic_errors[path] if error_override is None else error_override
    work = simulator.work
    if (type(anchor) is not _DynamicInitial or type(error) is not AnchorError
            or type(anchor.time) is not F or type(anchor.since) is not F
            or type(state.dynamic_error_times[path]) is not F
            or state.modes[path] != "dynamic"
            or state.claims.get((path, "translation")) is not None
            or state.claims.get((path, "orientation")) is not None):
        raise _Unsupported
    vectors, native = _native_pose(anchor.state, simulator)
    acceleration = simulator.model.gravity if history.acceleration is None else history.acceleration
    ideal_acceleration = state.ideal_accelerations[path]
    errors = (error.position_m, error.rotation_rad, error.velocity_m_per_s, error.angular_velocity_rad_per_s)
    force = _force_receipt(history, work)
    witness = (native, _literal((anchor.time, anchor.since, errors, state.dynamic_error_times[path],
                               acceleration, ideal_acceleration, history.net), work), force)
    return vectors, _copy(acceleration), _copy(ideal_acceleration), AnchorError(*_copy(errors)), witness


def _source_guard(simulator, state, path, proof, *, charged=True, receipt=None):
    work, ops = simulator.work, simulator.pose_ops
    _table_token(state, path)
    if (ops.work is not work or work.max_operand_bits != MAX_OPERAND_BITS
            or state.dynamic_cells.get(path) is not proof):
        raise ReachAdmissionError("reach_domain", "An admitted dynamic envelope changed owner or cap.")
    try:
        owners = _source_owners(state, path)
        saved = _proof_receipt(proof, work)
        current_lineage = _model_snapshot(simulator)[1]
        values = _dynamic_snapshot(simulator, state, path)
    except (KeyError, TypeError, AttributeError, _Unsupported) as error:
        raise ReachAdmissionError("reach_domain", "An admitted dynamic envelope changed source.") from error
    if (receipt is not None and saved != receipt or current_lineage != proof.lineage
            or values[-1][:2] != proof.witness):
        raise ReachAdmissionError("reach_domain", "An admitted dynamic envelope changed source.")
    if charged:
        history = state.forces[path]
        work.charge("transfer_dynamic_guard", sum(len(table[2]) for table in proof.lineage[1])
                    + len(history.active) + len(history.last_changes) + 1)
        try:
            unchanged = (simulator.work is work and simulator.pose_ops is ops and ops.work is work
                and work.max_operand_bits == MAX_OPERAND_BITS
                and state.dynamic_cells.get(path) is proof
                and _same_source_owners(state, path, owners)
                and _proof_receipt(proof, work) == saved
                and _model_snapshot(simulator)[1] == current_lineage
                and _dynamic_snapshot(simulator, state, path)[-1] == values[-1])
        except (KeyError, TypeError, AttributeError, _Unsupported) as error:
            raise ReachAdmissionError("reach_domain", "A dynamic envelope changed during its admission callback.") from error
        if not unchanged:
            raise ReachAdmissionError("reach_domain", "A dynamic envelope changed during its admission callback.")
    return values


def source_sizes(simulator, state, path, start, end):
    """Additional uniform source magnitudes; physical/native clocks stay put."""
    proof = state.dynamic_cells.get(path)
    if proof is None:
        return None
    if type(proof) is not CellAnchor:
        raise ReachAdmissionError("reach_domain", "An unknown dynamic envelope cannot supply bounds.")
    work, ops, model, root_state = simulator.work, simulator.pose_ops, simulator.model, simulator.state
    _, acceleration, _, _, initial = _source_guard(simulator, state, path, proof)
    receipt, copied = _proof_receipt(proof, work), _copy_proof(proof)
    owners = _source_owners(state, path)
    a = PhaseArithmetic(work)
    start, end = _copy((start, end))
    elapsed = a.maximum(a.absolute(a.sub(start, copied.clock)), a.absolute(a.sub(end, copied.clock)))
    acceleration_size = a.l1(acceleration)
    result = (a.add(copied.position_size, a.mul(copied.velocity_size, elapsed),
                    a.div(a.mul(acceleration_size, elapsed, elapsed), F(2))),
              a.add(copied.velocity_size, a.mul(acceleration_size, elapsed)), copied.omega_size)
    work.charge("transfer_dynamic_publish")
    if (simulator.work is not work or simulator.pose_ops is not ops or simulator.model is not model
            or simulator.state is not root_state or not _same_source_owners(state, path, owners)):
        raise ReachAdmissionError("reach_domain", "A dynamic envelope changed its current source owner.")
    if _source_guard(simulator, state, path, proof, charged=False, receipt=receipt)[-1] != initial:
        raise ReachAdmissionError("reach_domain", "A dynamic envelope's current force context changed.")
    return result


@dataclass
class DynamicTransfer:
    simulator: object
    state: object
    path: str
    time: F
    proof: CellAnchor
    point: CellEnvelope
    sizes: tuple
    original_anchor: object
    original_native: tuple
    original_clock: tuple
    force: tuple
    work: object
    pose_ops: object
    root_state: object
    proof_receipt: tuple
    table_token: tuple
    state_owners: tuple

    def admit_after(self):
        sim = self.simulator
        if (sim.work is not self.work or sim.pose_ops is not self.pose_ops
                or self.pose_ops.work is not self.work or sim.state is not self.root_state
                or self.work.max_operand_bits != MAX_OPERAND_BITS):
            raise ReachAdmissionError("reach_domain", "A transfer envelope changed source ownership.")
        try:
            _table_admit(self.state, self.path, self.table_token)
            if not _same_source_owners(self.state, self.path, self.state_owners, anchor=False):
                raise _Unsupported
            proof_receipt = _proof_receipt(self.proof, self.work)
            lineage = _model_snapshot(sim)[1]
            original = _native_pose(self.original_anchor.state, sim)[1]
            clock = _literal((self.original_anchor.time, self.original_anchor.since), self.work)
            force = _force_receipt(self.state.forces[self.path], self.work)
        except (KeyError, TypeError, AttributeError, _Unsupported) as error:
            raise ReachAdmissionError("reach_domain", "A transfer envelope changed its source operands.") from error
        if (proof_receipt != self.proof_receipt or lineage != self.proof.lineage
                or original != self.original_native or clock != self.original_clock or force != self.force):
            raise ReachAdmissionError("reach_domain", "A transfer envelope changed its source operands.")


def dynamic_transfer(simulator, state, path, time):
    proof = state.dynamic_cells.get(path)
    if proof is None:
        return None
    if type(proof) is not CellAnchor:
        raise ReachAdmissionError("reach_domain", "An unknown dynamic envelope cannot be transferred.")
    work, ops, root_state = simulator.work, simulator.pose_ops, simulator.state
    time = _copy(time)
    vectors, acceleration, ideal_acceleration, error, witness = _source_guard(simulator, state, path, proof)
    receipt, copied, token = _proof_receipt(proof, work), _copy_proof(proof), _table_token(state, path)
    original = state.dynamic[path]
    original_clock = _literal((original.time, original.since), work)
    owners = _source_owners(state, path, anchor=False)
    arithmetic = CellArithmetic(work)
    elapsed = arithmetic.a.sub(time, copied.clock)
    point = arithmetic.dynamic(copied, vectors[2], error, acceleration, ideal_acceleration, elapsed)
    sizes = arithmetic.point_sizes(copied, acceleration, ideal_acceleration, elapsed)
    result = DynamicTransfer(simulator, state, path, time, proof, point, sizes,
                             original, witness[0], original_clock, witness[2], work, ops, root_state,
                             receipt, token, owners)
    work.charge("transfer_point_publish")
    _source_guard(simulator, state, path, proof, charged=False, receipt=receipt)
    result.admit_after()
    return result


def _publish(simulator, state, path, time, envelope, sizes, lineage, guard, *, new_error=None):
    work, ops, model, root_state = simulator.work, simulator.pose_ops, simulator.model, simulator.state
    try:
        owners = _source_owners(state, path)
        initial = _dynamic_snapshot(simulator, state, path)[-1]
        next_witness = (_dynamic_snapshot(simulator, state, path, error_override=new_error)[-1]
                        if new_error is not None else initial)
    except (KeyError, TypeError, AttributeError, _Unsupported) as error:
        raise ReachAdmissionError("reach_domain", "A transfer's new native anchor is unsupported.") from error
    result = CellAnchor(time, envelope, *sizes, lineage, next_witness[:2])
    work.charge("transfer_anchor_publish")
    if (simulator.work is not work or simulator.pose_ops is not ops or ops.work is not work
            or simulator.model is not model or simulator.state is not root_state
            or work.max_operand_bits != MAX_OPERAND_BITS):
        raise ReachAdmissionError("reach_domain", "A transfer's source owner changed before publication.")
    guard()
    try:
        unchanged = (_same_source_owners(state, path, owners)
                     and _dynamic_snapshot(simulator, state, path)[-1] == initial)
    except (KeyError, TypeError, AttributeError, _Unsupported) as error:
        raise ReachAdmissionError("reach_domain", "A transfer's native anchor changed before publication.") from error
    if not unchanged:
        raise ReachAdmissionError("reach_domain", "A transfer's native anchor changed before publication.")
    if new_error is not None:
        state.dynamic_errors[path] = new_error
    state.dynamic_cells[path] = result
    return result


def _admit_dynamic(simulator, state, path, initial):
    try:
        unchanged = _dynamic_snapshot(simulator, state, path)[-1] == initial
    except (KeyError, TypeError, AttributeError, _Unsupported) as error:
        raise ReachAdmissionError("reach_domain", "The new native anchor changed during its envelope proof.") from error
    if not unchanged:
        raise ReachAdmissionError("reach_domain", "The new native anchor changed during its envelope proof.")


def release_anchor(simulator, state, path, time, captured):
    if captured is None:
        state.dynamic_cells.pop(path, None)
        return None
    token = _table_token(state, path)
    vectors, _, _, error, initial = _dynamic_snapshot(simulator, state, path)

    def admit():
        _table_admit(state, path, token)
        captured.admit()
        _admit_dynamic(simulator, state, path, initial)

    arithmetic = CellArithmetic(simulator.work)
    try:
        incoming = captured.evaluate()
    except _Unsupported:
        admit()
        state.dynamic_cells.pop(path, None)
        return None
    envelope = arithmetic.released(incoming, error)
    sizes = tuple(arithmetic.upper(arithmetic.a.add(arithmetic.a.l1(vector), arithmetic.a.mul(F(2), allowance), radius))
                  for vector, allowance, radius in zip(vectors,
                      (error.position_m, error.velocity_m_per_s, error.angular_velocity_rad_per_s),
                      (envelope.position, envelope.velocity, envelope.omega)))
    admit()
    return _publish(simulator, state, path, time, envelope, sizes, captured.lineage, admit)


def force_anchor(simulator, state, path, time, captured, before, *, changed):
    if captured is None:
        state.dynamic_cells.pop(path, None)
        return None
    initial = _dynamic_snapshot(simulator, state, path)[-1]

    def admit():
        captured.admit_after()
        _admit_dynamic(simulator, state, path, initial)

    arithmetic = CellArithmetic(simulator.work)
    error = AnchorError(*_copy((before.position_m, before.rotation_rad, before.velocity_m_per_s, before.angular_velocity_rad_per_s)))
    envelope = arithmetic.forced(captured.point, error, changed=changed)
    sizes = arithmetic.rounded_sizes(captured.sizes) if changed else captured.sizes
    return _publish(simulator, state, path, time, envelope, sizes, captured.proof.lineage, admit)


def impulse_anchor(simulator, state, path, time, captured, before, payload, mass, inertia):
    if captured is None:
        state.dynamic_cells.pop(path, None)
        return None
    work = simulator.work
    _, _, _, current, initial = _dynamic_snapshot(simulator, state, path)
    operands = _literal((payload.point_self_m, payload.impulse_world_n_s, mass, inertia), work)

    def admit():
        captured.admit_after()
        _admit_dynamic(simulator, state, path, initial)
        if _literal((payload.point_self_m, payload.impulse_world_n_s, mass, inertia), work) != operands:
            raise ReachAdmissionError("reach_domain", "The impulse operands changed during their envelope proof.")

    arithmetic = CellArithmetic(work)
    error = AnchorError(*_copy((before.position_error_m, before.rotation_error_rad,
                        before.velocity_error_m_per_s, before.angular_velocity_error_rad_per_s)))
    point, impulse, mass, inertia = _copy((payload.point_self_m, payload.impulse_world_n_s, mass, inertia))
    envelope = arithmetic.impulse(captured.point, error, point, impulse, mass, inertia)
    sizes = arithmetic.impulse_sizes(captured.point, captured.sizes, error, point, impulse, mass, inertia)
    a = arithmetic.a
    new_error = AnchorError(current.position_m, current.rotation_rad,
        a.maximum(current.velocity_m_per_s, a.add(a.mul(F(2), envelope.velocity), a.mul(F(3), GRID))),
        a.maximum(current.angular_velocity_rad_per_s, a.add(a.mul(F(2), envelope.omega), a.mul(F(3), GRID))))
    admit()
    return _publish(simulator, state, path, time, envelope, sizes, captured.proof.lineage,
                    admit, new_error=new_error)


def recording_receipt(simulator, state, path):
    """Bind transition proof state to an optional captured recording batch."""
    table, proof = _table_token(state, path)
    if proof is None:
        return (table,), None
    _source_guard(simulator, state, path, proof, charged=False)
    receipt = _proof_receipt(proof, simulator.work)
    return (table, proof, proof.envelope, proof.lineage, proof.witness), receipt


def recording_work(state, path):
    """Charge each bounded source row used by a captured proof admission."""
    _, proof = _table_token(state, path)
    if proof is None:
        return 0
    if (type(proof) is not CellAnchor or type(proof.lineage) is not tuple
            or len(proof.lineage) != 2 or type(proof.lineage[1]) is not tuple
            or len(proof.lineage[1]) != len(_TABLES)):
        raise TypeError("A captured transfer proof needs its bounded source lineage.")
    rows = 0
    for table in proof.lineage[1]:
        if type(table) is not tuple or len(table) != 3 or type(table[2]) is not tuple:
            raise TypeError("A captured transfer proof needs its bounded source lineage.")
        rows += len(table[2])
    if rows > _LIMIT:
        raise TypeError("An oversized transfer proof retains ordinary recording sampling.")
    return rows + 1
