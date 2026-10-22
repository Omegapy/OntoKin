"""Bounded planar recording arithmetic with explicit endpoint enclosures.

This module supplies no source pose, event anchor, rate or admission result.
Its binary64 candidates carry proved component enclosures against the original
projective-grid recording recurrence. Production certificates include those
enclosures as additional endpoint error; supplied-byte checking remains
independent. The separately callable strict-cell diagnostic additionally proves
identical float32 values and requests an original phase replay when ambiguous.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import math
import struct

from .reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, compare, rational, round_binary64
from .reach_pose import (AXIS_ERROR, PRODUCT_ERROR, MAX_RECORDING_ROTATION_STEPS,
                         PoseValue, RecordedTransform, ReachPoseOps, RotationValue, ZERO, UNIT)

METHOD = "ontokin.recording-planar-binary64-enclosures/0.5"
MAX_FLOAT_DEPTH = 64
# This ceiling belongs only to the optional native candidate. The original
# recording recurrence and its separate error allowance still use 10,000.
# Counting the direct seed as one leaves at most 126 native products.
MAX_FLOAT_ROTATION_STEPS = 127
_MAX_POSITION = float(2**500)
_MAX_BALLISTIC_OPERAND = float(2**250)
_MIN_BALLISTIC_ELAPSED = F(1, 2**250)
_MAX_BALLISTIC_ELAPSED = F(2**250)


class RecordingRoundingAmbiguity(Exception):
    """The complete current phase must use its original recording sampler."""
    def __init__(self, path, components=(), *, reason=None):
        super().__init__(reason or "A recording component straddles a float32 rounding cell.")
        self.path = path
        self.components = components


class _UnsupportedPlanar(Exception):
    pass


@dataclass(frozen=True)
class RecordingFloatExcess:
    position_m: F
    quaternion_component: F
    rotation_rad: F
    # Completed outward projections belong to this exact cached enclosure.
    # They are private sampling proofs, not extra fields in delivered metadata.
    _cell_radii: tuple[float, float] | None = None


_ZERO_EXCESS = RecordingFloatExcess(F(0), F(0), F(0))


@dataclass(frozen=True)
class CertifiedRecordingFrames:
    frames: dict
    excess_by_frame: dict[str, RecordingFloatExcess]


@dataclass(frozen=True)
class _FloatRotation:
    w: float
    z: float
    zero_w: bool
    zero_z: bool


@dataclass(frozen=True)
class _FloatPose:
    position: tuple[float, float, float]
    rotation: _FloatRotation
    zeros: tuple[bool, bool, bool]
    depth: int

    @property
    def orientation(self):
        return (self.rotation.w, 0.0, 0.0, self.rotation.z)


@dataclass(frozen=True)
class _AffineLaw:
    """Private completed exact law; built only after its source-domain proof."""
    initial: F
    target: F
    duration: F
    slope: F


@dataclass(frozen=True)
class _AffineCoordinate:
    law: _AffineLaw
    elapsed: F
    running: bool


@dataclass(frozen=True)
class _BallisticLaw:
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    acceleration: tuple[float, float, float]
    horizon: F
    extent: F


def _checked_compare(left, right, work):
    """Charge every actual rational ordering and retain the native domain."""
    result = compare(left, right, work)
    if work.max_operand_bits != MAX_OPERAND_BITS:
        raise _UnsupportedPlanar("The recording arithmetic domain changed.")
    return result


def recording_float_excess(bound, *, work, include_cell_radii=True, dynamic=False):
    """Bound positions and sign-aligned quaternion components of the recorder.

    E encloses the unnormalized planar quaternion after at most 127 candidate
    cursor steps and 64 leaf compositions. G is the original controlled recurrence
    excess. Both algorithms' existing source errors are retained explicitly.
    The 2^-46*(C+1) translation term allows 128*u for each composition and
    source leaf conversion, including gradual underflow. Dynamic-dependent
    paths add 64*u*(M+L+1) after separately proving M encloses their actual
    root's ballistic extent over the complete source phase.
    Quaternion comparison is projective: one common sign aligns all components
    with the original unit quaternion. Canonical signs can disagree near w=0.
    rotation_rad deliberately uses the four-component conservative conversion.
    """
    work.charge("recording_float_excess_domain")
    t, c = bound.trig_count, bound.product_count
    l, m = bound.path_offset_l1_m, bound.max_position_l1_m
    sp, sq = bound.position_error_m, bound.rotation_error_rad
    if (type(t) is not int or type(c) is not int or min(t, c) < 0
            or any(type(v) is not F or v.numerator < 0 for v in (l, m, sp, sq))):
        raise ValueError("Certified planar recording requires exact nonnegative source bounds.")
    work.guard(t, c, l, m, sp, sq)
    if type(include_cell_radii) is not bool or type(dynamic) is not bool:
        raise ValueError("The optional recording proof selectors must be boolean.")
    key = (METHOD, "excess", work.max_operand_bits, t, c, l, m, sp, sq, include_cell_radii, dynamic)
    old = work.lookup(key)
    if work.max_operand_bits != key[2]:
        raise _UnsupportedPlanar("The recording arithmetic domain changed.")
    if old is not None:
        work.guard(old.position_m, old.quaternion_component, old.rotation_rad)
        return old
    from .reach_numeric import exact
    op = lambda a, b, kind: exact(a, b, kind, work)
    source_leaves = op(F(c), F(1), "add")
    e = op(F(2), op(op(F(t), F(1, 2**41), "mul"),
                    op(source_leaves, F(1, 2**47), "mul"), "add"), "mul")
    g = op(op(F(MAX_RECORDING_ROTATION_STEPS - 1), F(t), "mul"),
           op(AXIS_ERROR, op(F(2), PRODUCT_ERROR, "mul"), "add"), "mul")
    q = op(op(op(F(2), sq, "mul"), g, "add"), op(F(16), e, "mul"), "add")
    p = op(op(op(F(2), sp, "mul"),
              op(l, op(g, op(F(3), e, "mul"), "add"), "mul"), "add"),
           op(op(F(1, 2**46), source_leaves, "mul"),
              op(op(m, l, "add"), F(1), "add"), "mul"), "add")
    if dynamic:
        # A dynamic root evaluates its exact ballistic law in native Horner
        # arithmetic. Its separately proved 64u*(B+1) L1 error propagates by
        # addition only. The current selected path must first prove M >= B.
        p = op(p, op(F(1, 2**47), op(op(m, l, "add"), F(1), "add"), "mul"), "add")
    if _checked_compare(e, F(1, 64), work) > 0 or _checked_compare(q, F(1, 64), work) > 0:
        raise _UnsupportedPlanar("The planar error envelope exceeds its local range.")
    rotation_rad = op(F(16), q, "mul")
    radii = ((_upper_float(p, work, cache=False), _upper_float(q, work, cache=False))
             if include_cell_radii else None)
    result = RecordingFloatExcess(p, q, rotation_rad, radii)
    work.remember(key, result)
    work.guard(result.position_m, result.quaternion_component, result.rotation_rad)
    work.guard_bits(1075)
    if work.max_operand_bits != key[2]:
        raise _UnsupportedPlanar("The recording arithmetic domain changed.")
    return result


def _direct_excess(bound, *, work):
    """Compare a fresh direct source projection with the original recurrence."""
    from .reach_numeric import exact
    work.charge("recording_direct_excess_domain")
    t, l = bound.trig_count, bound.path_offset_l1_m
    work.guard(t, l, bound.position_error_m, bound.rotation_error_rad)
    op = lambda a, b, kind: exact(a, b, kind, work)
    g = op(op(F(MAX_RECORDING_ROTATION_STEPS - 1), F(t), "mul"),
           op(AXIS_ERROR, op(F(2), PRODUCT_ERROR, "mul"), "add"), "mul")
    q = op(op(F(2), bound.rotation_error_rad, "mul"), g, "add")
    p = op(op(F(2), bound.position_error_m, "mul"), op(l, g, "mul"), "add")
    return RecordingFloatExcess(p, q, op(F(16), q, "mul"))


def _upper_float(value, work, *, cache=True):
    work.charge("recording_cell_radius_domain")
    if type(value) is not F or value.numerator < 0:
        raise ValueError("A rounding-cell radius must be a nonnegative exact rational.")
    work.guard(value)
    key = (METHOD, "cell_radius", work.max_operand_bits, value)
    cached = work.lookup(key) if cache else None
    if cached is not None:
        work.guard_bits(1075)
        if work.max_operand_bits != MAX_OPERAND_BITS:
            raise _UnsupportedPlanar("The recording arithmetic domain changed.")
        return cached
    result = round_binary64(value, work=work)
    if _checked_compare(rational(result, work), value, work) < 0:
        work.charge("recording_float_nextafter")
        if work.max_operand_bits != MAX_OPERAND_BITS:
            raise _UnsupportedPlanar("The recording arithmetic domain changed.")
        result = math.nextafter(result, math.inf)
    if cache:
        work.remember(key, result)
    work.guard_bits(1075)
    if work.max_operand_bits != MAX_OPERAND_BITS:
        raise _UnsupportedPlanar("The recording arithmetic domain changed.")
    return result


def certified_float32_cell(value, radius, *, work):
    """Prove every real in [value-radius,value+radius] has one float32 result.

    The binary32 candidate and an inscribed symmetric half-cell are exact
    binary64 numbers. value-candidate is exact by Sterbenz, including the
    subnormal and zero cells. If h-error rounds upward to t, every binary64
    strictly below t is at most its predecessor, which is below exact h-error.
    Thus the strict threshold test remains conservative without nextafter.
    """
    work.charge("recording_float_cell_domain")
    if type(value) is not float or not math.isfinite(value):
        return False
    work.guard_bits(1075)
    error = _upper_float(radius, work) if type(radius) is F else radius
    if type(error) is not float or not math.isfinite(error) or error < 0:
        return False
    work.charge("recording_float32_candidate")
    work.guard_bits(1075)
    try:
        encoded = struct.pack("<f", value)
    except (OverflowError, struct.error):
        return False
    candidate = struct.unpack("<f", encoded)[0]
    if not math.isfinite(candidate):
        return False
    bits = struct.unpack("<I", encoded)[0]
    if candidate == 0.0:
        # Positive and negative zero have different delivered bits. A real
        # enclosure crossing zero does not certify either sign. Exact source
        # zero is canonical positive zero; structural zeros skip this gate.
        if value == 0.0:
            work.guard_bits(1075)
            return error == 0.0 and not (bits >> 31)
        if error >= abs(value):
            return False
    exponent, fraction = (bits >> 23) & 255, bits & ((1 << 23) - 1)
    work.charge("recording_float_sub")
    work.guard_bits(1075)
    delta = value - candidate
    # Use the smaller symmetric cell at a power of two. Both sides of the
    # interval must fit, even when its center lies on the wider side.
    halfwidth = math.ldexp(1.0, -150 if exponent == 0 else
                          exponent - 152 if fraction == 0 and exponent > 1 else exponent - 151)
    work.charge("recording_float_sub")
    work.guard_bits(1075)
    threshold = halfwidth - error
    return abs(delta) < threshold


class Binary64RecordingOps(ReachPoseOps):
    """Finite planar candidates only; all source helpers remain on source_ops."""
    recording_namespace = METHOD

    def __init__(self, source_ops, *, constant_hinges=frozenset(), constant_hinge_check=None,
                 share_arithmetic=False, affine_coordinates=False, dynamic_phase=None,
                 dynamic_bounds=None):
        super().__init__(source_ops.work)
        self.source_ops = source_ops
        self.constant_hinges = constant_hinges
        self.constant_hinge_check = constant_hinge_check
        self.share_arithmetic = share_arithmetic
        self.affine_coordinates = affine_coordinates
        self.dynamic_phase = dynamic_phase
        self.dynamic_bounds = dynamic_bounds
        # This per-graph index contains only completed root extents. It is
        # discarded after the current sampler call, never retained as a cache.
        self.dynamic_extents = {}

    def _domain(self):
        self.work.charge("recording_float_domain")
        self._require_domain()

    def _require_domain(self):
        """Recheck after the last callback without charging another callback."""
        if self.work.max_operand_bits != MAX_OPERAND_BITS:
            raise _UnsupportedPlanar("The recording arithmetic domain changed.")

    def _native(self, a, b, kind):
        self.work.charge("recording_float_" + kind)
        self._require_domain()
        result = a * b if kind == "mul" else a - b if kind == "sub" else a + b
        if not math.isfinite(result):
            raise _UnsupportedPlanar("A native planar intermediate is not finite.")
        return result

    def _rotation_domain(self, value):
        if (type(value) is not _FloatRotation or any(type(v) is not float or not math.isfinite(v)
                or abs(v) > 2 for v in (value.w, value.z))
                or type(value.zero_w) is not bool or type(value.zero_z) is not bool):
            raise _UnsupportedPlanar("A native planar rotation left its proved domain.")

    @staticmethod
    def _rotation_bits(value):
        # Numerical equality coalesces signed zeros. Include their actual bits
        # so a pure arithmetic hit has exactly the same binary64 operands.
        return struct.pack("<dd??", value.w, value.z, value.zero_w, value.zero_z)

    def _project_rotation(self, rotation, *, structural=True):
        rotation = self.source_ops._rotation(rotation)
        if (type(rotation.components) is not tuple or len(rotation.components) != 4
                or any(type(v) is not F for v in rotation.components)):
            raise _UnsupportedPlanar("A recorded rotation needs four private exact components.")
        if rotation.components[1] or rotation.components[2]:
            raise _UnsupportedPlanar("A recorded rotation is not planar.")
        projection = self.source_ops._unit_projection(rotation)
        self._require_domain()
        if (type(projection) is not tuple or len(projection) != 4
                or any(type(v) is not float or not math.isfinite(v) for v in projection)):
            raise _UnsupportedPlanar("A projected recorded rotation must have four finite binary64 components.")
        w, x, y, z = projection
        if x != 0.0 or y != 0.0 or any(v == 0.0 and math.copysign(1.0, v) < 0 for v in projection):
            raise _UnsupportedPlanar("The projected recorded rotation is not scalar/Z with canonical zeros.")
        if not (w > 0.0 or w == 0.0 and z > 0.0):
            raise _UnsupportedPlanar("The projected recorded rotation needs a canonical planar lift.")
        if rotation.frozen_projection is not None:
            # Materialized event anchors preserve the actual public bits as
            # their private projective components. An arbitrary inconsistent
            # frozen tuple is not a normalized source leaf for this candidate.
            from .reach_numeric import compare
            self.work.charge("recording_frozen_projection_domain")
            self._require_domain()
            decoded = tuple(rational(v, self.work) for v in projection)
            self._require_domain()
            if any(compare(actual, private, self.work) != 0
                   for actual, private in zip(decoded, rotation.components)):
                raise _UnsupportedPlanar("The frozen projection does not match its private source components.")
            self._require_domain()
            op = self.source_ops._op
            norm = op(op(decoded[0], decoded[0], "mul"),
                      op(decoded[3], decoded[3], "mul"), "add")
            defect = abs(op(norm, F(1), "sub"))
            self._require_domain()
            # A correctly rounded unit projection has squared-norm defect
            # <=2u+u^2. Four u leaves a conservative exact admission margin.
            outside = compare(defect, F(1, 2**51), self.work) > 0
            self._require_domain()
            if outside:
                raise _UnsupportedPlanar("The frozen source projection is outside its unit-rounding envelope.")
        result = _FloatRotation(w, z, False, False)
        self._rotation_domain(result)
        return _FloatRotation(w, z,
            structural and not rotation.components[0] and w == 0.0 and math.copysign(1.0, w) > 0,
            structural and not rotation.components[3] and z == 0.0 and math.copysign(1.0, z) > 0)

    def _axis_rotation(self, axis, coordinate, *, structural=True):
        """Reuse one completed controlled kernel and native unit projection.

        Callers have already decoded the exact axis/coordinate and checked the
        scalar/Z domain. Different path cursors still advance independently;
        only this pure function of complete immutable operands is shared.
        """
        self._require_domain()
        self.work.guard(*axis, coordinate)
        key = (METHOD, "axis_projection", self.work.max_operand_bits,
               axis, coordinate, structural)
        old = self.work.lookup(key)
        self._require_domain()
        if old is not None:
            return old
        result = self._project_rotation(self.source_ops.axis_rotation(axis, coordinate),
                                        structural=structural)
        self.work.remember(key, result)
        self._require_domain()
        return result

    def _immutable_scalar_domain(self, values, *, small=False):
        """Prove exact decoding admissible before reusing immutable operands."""
        for value in values:
            if type(value) is float:
                if not math.isfinite(value):
                    raise _UnsupportedPlanar("A recording law requires finite source operands.")
                # Every finite binary64 has an exact rational representation
                # within 1075 bits. The optional small proof is checked after
                # the cold decode, when its actual rational width is known.
                self.work.guard_bits(1075)
            elif type(value) in (int, F):
                self.work.guard(value)
                if small and max(value.numerator.bit_length(), value.denominator.bit_length()) > 1024:
                    raise _UnsupportedPlanar("The native recording proof requires small exact operands.")
            else:
                raise _UnsupportedPlanar("A recording law requires exact real source operands.")

    def _affine_law(self, initial, target, duration, *, running):
        self._domain()
        if type(running) is not bool:
            raise _UnsupportedPlanar("A recording affine state must be boolean.")
        self._immutable_scalar_domain((initial, target, duration), small=True)
        key = (METHOD, "affine_law", self.work.max_operand_bits, initial, target, duration, running)
        old = self.work.lookup(key)
        self._require_domain()
        if old is not None:
            return old
        initial, target, duration = (rational(value, self.work) for value in (initial, target, duration))
        self._immutable_scalar_domain((initial, target, duration), small=True)
        if duration.numerator <= 0:
            raise ReachAdmissionError("reach_numeric", "A recording affine law needs a positive duration.")
        slope = self.source_ops._op(self.source_ops._op(target, initial, "sub"), duration, "div")
        # The actual affine value stays between these endpoints. Their finite
        # projections therefore cover every omitted coordinate exposure. A
        # running source also exposes its rate; paused sources do not, and
        # must not acquire an eager derivative-overflow rejection here.
        round_binary64(initial, work=self.work)
        round_binary64(target, work=self.work)
        if running:
            round_binary64(slope, work=self.work)
        result = _AffineLaw(initial, target, duration, slope)
        self.work.remember(key, result)
        self._require_domain()
        return result

    def recording_coordinate(self, simulator, path, time, state):
        """Return a private unexposed affine scalar for bounded interiors only.

        The source PairSample and its canonical coordinate/rate projections are
        never changed. The phase's existing coordinate error contains both the
        actual/ideal affine discrepancy and the omitted exposure rounding.
        """
        if not self.affine_coordinates:
            return simulator._coordinate(path, time, state)[0]
        claimant = state.claims.get((path, "coordinate"))
        if claimant is None:
            return state.coordinates[path]
        action, runtime = simulator.model.actions[claimant], state.actions[claimant]
        if action.kind == "reach_planar":
            index = 0 if path == action.reach.shoulder else 1
            initial, target = runtime.initial[index], runtime.solution.target_rad[index]
        else:
            initial, target = runtime.initial, action.goal
        running = runtime.status == "running"
        law = self._affine_law(initial, target, action.duration, running=running)
        self.work.charge("recording_affine_clock_domain")
        self._require_domain()
        # Check the actual clock operands before forming a difference, rather
        # than trusting a previously valid clock or an unguarded Fraction sum.
        clocks = (runtime.elapsed, time, runtime.running_since) if running else (runtime.elapsed,)
        self._immutable_scalar_domain(clocks, small=True)
        clocks = tuple(value if type(value) is F else rational(value, self.work) for value in clocks)
        self._immutable_scalar_domain(clocks, small=True)
        elapsed = (self.source_ops._op(clocks[0],
            self.source_ops._op(clocks[1], clocks[2], "sub"), "add") if running else clocks[0])
        self._immutable_scalar_domain((elapsed,), small=True)
        if elapsed.numerator < 0 or _checked_compare(elapsed, law.duration, self.work) > 0:
            raise ReachAdmissionError("reach_numeric", "Invalid recording affine clock.")
        self._require_domain()
        return _AffineCoordinate(law, elapsed, running)

    def _affine_axis_rotation(self, axis, coordinate, *, context, path, max_steps):
        law, elapsed, running = coordinate.law, coordinate.elapsed, coordinate.running
        self.work.charge("recording_affine_operand_guard")
        self._require_domain()
        if (type(law) is not _AffineLaw or type(elapsed) is not F or type(running) is not bool
                or any(type(value) is not F for value in
                       (law.initial, law.target, law.duration, law.slope))):
            raise _UnsupportedPlanar("A recording affine descriptor is malformed.")
        self.work.guard(law.initial, law.target, law.duration, law.slope, elapsed)
        self._immutable_scalar_domain((law.initial, law.target, law.duration, elapsed), small=True)
        if (law.duration.numerator <= 0 or elapsed.numerator < 0
                or _checked_compare(elapsed, law.duration, self.work) > 0):
            raise ReachAdmissionError("reach_numeric", "Invalid recording affine clock or duration.")
        key = self._recording_cursor_key("bounded_affine_axis", context, path, max_steps,
                                         axis, law, running)
        previous = self.work.lookup(key)
        self._require_domain()
        step_limit = min(max_steps, MAX_FLOAT_ROTATION_STEPS)
        delta = increment = None
        if previous is None or previous[2] >= step_limit:
            value = (law.target if elapsed == law.duration else law.initial if not law.slope
                     else self.source_ops._op(law.initial,
                         self.source_ops._op(law.slope, elapsed, "mul"), "add"))
            # An unrounded affine cancellation does not establish a zero in
            # the preceding history-dependent source recording recurrence.
            result = self._axis_rotation(axis, value, structural=False)
            count = 1
        else:
            last, rotation, count, old_delta, old_increment = previous
            self.work.charge("recording_float_cursor_guard")
            self.work.guard(last, count)
            self._rotation_domain(rotation)
            delta_elapsed = self.source_ops._op(elapsed, last, "sub")
            delta = self.source_ops._op(law.slope, delta_elapsed, "mul")
            if delta:
                if delta == old_delta:
                    self.work.charge("recording_float_increment_reuse")
                    self._require_domain()
                    increment = old_increment
                else:
                    increment = self._axis_rotation(axis, delta, structural=False)
                result = self._product(increment, rotation)
            else:
                result = rotation
                delta, increment = old_delta, old_increment
            self.work.charge("recording_float_rotation_step")
            self._require_domain()
            count += 1
        self._require_domain()
        self.work.remember(key, (elapsed, result, count, delta, increment))
        self._require_domain()
        return result

    def recording_constant_pose(self, pose, *, inverse=False, build):
        """Reuse the complete source-leaf projection, retaining fresh parents."""
        self._domain()
        if type(inverse) is not bool:
            raise _UnsupportedPlanar("A recording leaf inverse selector must be boolean.")
        if (type(pose.position) is not tuple or type(pose.rotation) is not tuple
                or len(pose.position) != 3 or len(pose.rotation) != 4):
            raise _UnsupportedPlanar("A recording leaf must have complete source pose operands.")
        position, rotation = pose.position, pose.rotation
        self._immutable_scalar_domain((*position, *rotation))
        key = (METHOD, "source_leaf", self.work.max_operand_bits, position, rotation, inverse)
        old = self.work.lookup(key)
        self._require_domain()
        if old is not None:
            return old
        result = self._pose(build(pose, inverse=inverse))
        self.work.remember(key, result)
        self._require_domain()
        return result

    def _ballistic_law(self, position, velocity, acceleration, *, anchor_time,
                       phase_interval, root_extent, context, path):
        """Prove one actual immutable root law against its whole-phase extent."""
        self.work.charge("recording_ballistic_law_domain")
        self._require_domain()
        if (type(anchor_time) is not F or type(phase_interval) is not tuple
                or len(phase_interval) != 2 or any(type(value) is not F for value in phase_interval)
                or type(context) is not object or type(path) is not str):
            raise _UnsupportedPlanar("A native ballistic law needs exact phase and anchor clocks.")
        self._immutable_scalar_domain((anchor_time, *phase_interval), small=True)
        if (anchor_time.numerator < 0
                or _checked_compare(anchor_time, phase_interval[0], self.work) > 0
                or _checked_compare(phase_interval[0], phase_interval[1], self.work) > 0):
            raise _UnsupportedPlanar("A native ballistic phase must follow its actual anchor.")
        vectors = (position, velocity, acceleration)
        if any(type(vector) is not tuple or len(vector) != 3 or
               any(type(value) is not float or not math.isfinite(value)
                   or abs(value) > _MAX_BALLISTIC_OPERAND for value in vector)
               for vector in vectors):
            raise _UnsupportedPlanar("A native ballistic law needs bounded canonical source vectors.")
        self.work.guard_bits(1075)
        if type(root_extent) is not F or root_extent.numerator < 0:
            raise _UnsupportedPlanar("A native ballistic law needs its actual source extent.")
        self.work.guard(root_extent)
        key = (METHOD, "ballistic_law", self.work.max_operand_bits, context, path,
               anchor_time, phase_interval, root_extent, *vectors)
        previous = self.work.lookup(key)
        self._require_domain()
        if previous is not None:
            return previous
        horizon = self.source_ops._op(phase_interval[1], anchor_time, "sub")
        self._immutable_scalar_domain((horizon,), small=True)
        if horizon.numerator < 0 or _checked_compare(horizon, _MAX_BALLISTIC_ELAPSED, self.work) > 0:
            raise _UnsupportedPlanar("The native ballistic horizon exceeds its proved domain.")
        p, v, a = (self.source_ops._vector(vector) for vector in vectors)
        op = self.source_ops._op
        extent = op(op(self.source_ops._l1(p),
                       op(self.source_ops._l1(v), horizon, "mul"), "add"),
                    op(op(op(self.source_ops._l1(a), horizon, "mul"), horizon, "mul"), F(2), "div"), "add")
        from .reach_numeric import compare
        if compare(extent, root_extent, self.work) > 0:
            raise _UnsupportedPlanar("A native ballistic law is outside its actual whole-phase extent.")
        result = _BallisticLaw(*vectors, horizon, extent)
        self.work.remember(key, result)
        self._require_domain()
        return result

    def _ballistic_position(self, law, elapsed):
        """Evaluate p0+t*(v0+a*t/2), with each actual native operation charged."""
        self.work.charge("recording_ballistic_clock_domain")
        self._require_domain()
        if type(law) is not _BallisticLaw or type(elapsed) is not F:
            raise _UnsupportedPlanar("A native ballistic sample needs a completed law and exact clock.")
        self.work.guard(law.horizon, law.extent, elapsed)
        self._immutable_scalar_domain((elapsed,), small=True)
        if (elapsed.numerator < 0 or _checked_compare(elapsed, law.horizon, self.work) > 0 or (elapsed and
                (_checked_compare(elapsed, _MIN_BALLISTIC_ELAPSED, self.work) < 0 or
                 _checked_compare(elapsed, _MAX_BALLISTIC_ELAPSED, self.work) > 0))):
            raise _UnsupportedPlanar("A native ballistic sample is outside its proved clock domain.")
        t = round_binary64(elapsed, work=self.work)
        self._require_domain()
        if not math.isfinite(t) or not 0 <= t <= _MAX_BALLISTIC_OPERAND:
            raise _UnsupportedPlanar("A native ballistic clock has no bounded binary64 projection.")
        if not elapsed:
            position = law.position
        else:
            half_time = self._native(t, 0.5, "mul")
            result = []
            for p, v, a in zip(law.position, law.velocity, law.acceleration):
                if not a and not v:
                    result.append(p)
                    continue
                rate = self._native(v, self._native(a, half_time, "mul"), "add") if a else v
                result.append(self._native(p, self._native(t, rate, "mul"), "add"))
            position = tuple(result)
        if any(abs(value) > _MAX_POSITION for value in position):
            raise _UnsupportedPlanar("A native ballistic position exceeds its finite composition domain.")
        zeros = tuple(not p and not v and not a
                      for p, v, a in zip(law.position, law.velocity, law.acceleration))
        self._require_domain()
        return tuple(0.0 if zero else value for value, zero in zip(position, zeros)), zeros

    def recording_dynamic_pose(self, simulator, path, time, state, *, context):
        """Sample one current free root without exposing source rates or anchors."""
        self._domain()
        phase = self.dynamic_phase
        if (type(phase) is not tuple or len(phase) != 2 or any(type(value) is not F for value in phase)
                or type(time) is not F or type(context) is not object or type(path) is not str):
            raise _UnsupportedPlanar("A native dynamic root needs its exact source phase and context.")
        anchor = state.dynamic[path]
        duration = simulator.model.duration
        if type(anchor.time) is not F or type(duration) is not F:
            raise _UnsupportedPlanar("A native dynamic anchor clock must be exact.")
        self.work.charge("recording_dynamic_clock_domain")
        self._require_domain()
        self._immutable_scalar_domain((*phase, anchor.time, time, duration), small=True)
        ordered_clocks = (anchor.time, phase[0], time, phase[1], duration)
        if (anchor.time.numerator < 0 or
                any(_checked_compare(left, right, self.work) > 0 for left, right in
                    zip(ordered_clocks, ordered_clocks[1:]))):
            raise _UnsupportedPlanar("A native dynamic sample does not belong to its actual source phase.")
        elapsed = self.source_ops._op(time, anchor.time, "sub")
        self._immutable_scalar_domain((elapsed,), small=True)
        if elapsed and (_checked_compare(elapsed, _MIN_BALLISTIC_ELAPSED, self.work) < 0 or
                        _checked_compare(elapsed, _MAX_BALLISTIC_ELAPSED, self.work) > 0):
            raise _UnsupportedPlanar("A native dynamic elapsed clock exceeds its proved domain.")
        initial = anchor.state
        root_bound = self.dynamic_bounds.get(path + ".frame") if self.dynamic_bounds is not None else None
        if root_bound is None:
            raise _UnsupportedPlanar("A native dynamic root is missing its actual source bound.")
        law = self._ballistic_law(initial.position, initial.velocity, simulator._acceleration(path, state),
            anchor_time=anchor.time, phase_interval=phase, root_extent=root_bound.max_position_l1_m,
            context=context, path=path)
        position, zeros = self._ballistic_position(law, elapsed)
        rotation = initial.rotation if hasattr(initial, "rotation") else initial.orientation
        orientation = simulator._advance_orientation(rotation, initial.omega, elapsed,
            recording_context=context, recording_path=METHOD + ":dynamic:" + path, recording_pose_ops=self)
        self._rotation_domain(orientation)
        self._require_domain()
        self.dynamic_extents[path] = law.extent
        return _FloatPose(position, orientation, zeros, 0)

    def _product(self, a, b):
        self._domain()
        self._rotation_domain(a)
        self._rotation_domain(b)
        if (a.w, a.z) == (1.0, 0.0) and a.zero_z:
            return b
        if (b.w, b.z) == (1.0, 0.0) and b.zero_z:
            return a
        key = None
        if self.share_arithmetic:
            key = (METHOD, "native_product", self.work.max_operand_bits,
                   self._rotation_bits(a), self._rotation_bits(b))
            old = self.work.lookup(key)
            self._require_domain()
            if old is not None:
                return old
        op = self._native
        real = op(op(a.w, b.w, "mul"), op(a.z, b.z, "mul"), "sub")
        imag = op(op(a.w, b.z, "mul"), op(a.z, b.w, "mul"), "add")
        if real < 0 or (real == 0 and imag < 0):
            self.work.charge("recording_float_sign", 2)
            self._require_domain()
            real, imag = -real, -imag
        zero_w = (a.zero_w or b.zero_w) and (a.zero_z or b.zero_z)
        zero_z = (a.zero_w or b.zero_z) and (a.zero_z or b.zero_w)
        result = _FloatRotation(0.0 if zero_w else real, 0.0 if zero_z else imag, zero_w, zero_z)
        if key is not None:
            self.work.remember(key, result)
            self._require_domain()
        return result

    def _rotated_offset(self, rotation, position, zeros):
        """Reuse only the complete pure local arithmetic, never world origins."""
        key = None
        if self.share_arithmetic:
            key = (METHOD, "native_offset", self.work.max_operand_bits,
                   self._rotation_bits(rotation), struct.pack("<ddd???", *position, *zeros))
            old = self.work.lookup(key)
            self._require_domain()
            if old is not None:
                return old
        op = self._native
        w, z = rotation.w, rotation.z
        x, y, zz = position
        c = op(op(w, w, "mul"), op(z, z, "mul"), "sub")
        s = op(op(w, z, "mul"), 2.0, "mul")
        cross_zero = rotation.zero_w or rotation.zero_z
        if zeros[1]:
            offset = (op(c, x, "mul"), op(s, x, "mul"), zz)
            offset_zeros = (zeros[0], zeros[0] or cross_zero, zeros[2])
        elif zeros[0]:
            self.work.charge("recording_float_sign")
            self._require_domain()
            offset = (op(-s, y, "mul"), op(c, y, "mul"), zz)
            offset_zeros = (zeros[1] or cross_zero, zeros[1], zeros[2])
        else:
            offset = (op(op(c, x, "mul"), op(s, y, "mul"), "sub"),
                      op(op(s, x, "mul"), op(c, y, "mul"), "add"), zz)
            offset_zeros = (False, False, zeros[2])
        result = offset, offset_zeros
        if key is not None:
            self.work.remember(key, result)
            self._require_domain()
        return result

    def recording_axis_rotation(self, axis, coordinate, *, context, path, max_steps):
        self._domain()
        affine = type(coordinate) is _AffineCoordinate
        if not affine:
            coordinate = rational(coordinate, self.work)
        axis = self.source_ops._vector(axis)
        if axis[0] or axis[1] or not axis[2]:
            raise _UnsupportedPlanar("Only a nonzero scalar/Z hinge is planar.")
        if affine:
            return self._affine_axis_rotation(axis, coordinate, context=context,
                                              path=path, max_steps=max_steps)
        key = self._recording_cursor_key("certified_binary64_axis", context, path, max_steps, axis)
        step_limit = min(max_steps, MAX_FLOAT_ROTATION_STEPS)
        if (path in self.constant_hinges or self.constant_hinge_check is not None
                and self.constant_hinge_check(path)):
            # The complete current phase has one coordinate, so the original
            # recurrence also retains its direct seed and exact zero support.
            return self._axis_rotation(axis, coordinate)
        previous = self.work.lookup(key)
        delta, increment = None, None
        if previous is None or previous[2] >= step_limit:
            # A seed at an interior zero coordinate cannot prove a zero in
            # the original history-dependent grid recurrence.
            result = self._axis_rotation(axis, coordinate, structural=False)
            count = 1
        else:
            last, rotation, count, old_delta, old_increment = previous
            self.work.charge("recording_float_cursor_guard")
            self.work.guard(last, count)
            self._rotation_domain(rotation)
            delta = self.source_ops._op(coordinate, last, "sub")
            if delta:
                if delta == old_delta:
                    self.work.charge("recording_float_increment_reuse")
                    increment = old_increment
                else:
                    increment = self._axis_rotation(axis, delta)
                result = self._product(increment, rotation)
            else:
                result = rotation
                delta, increment = old_delta, old_increment
            self.work.charge("recording_float_rotation_step")
            self._require_domain()
            count += 1
        if self.work.max_operand_bits != MAX_OPERAND_BITS:
            raise _UnsupportedPlanar("The recording arithmetic domain changed.")
        self.work.remember(key, (coordinate, result, count, delta, increment))
        if self.work.max_operand_bits != MAX_OPERAND_BITS:
            raise _UnsupportedPlanar("The recording arithmetic domain changed.")
        return result

    def recording_advance_orientation(self, initial, omega, elapsed, *, context, path,
                                      max_steps, phase_plan=None):
        """Reuse checked scalar/Z spin increments without source pose derivatives."""
        self._domain()
        initial = self.source_ops._rotation(initial)
        elapsed = rational(elapsed, self.work)
        omega = self.source_ops._vector(omega)
        if initial.components[1] or initial.components[2] or omega[0] or omega[1]:
            raise _UnsupportedPlanar("Only a complete scalar/Z prescribed spin is planar.")
        key = self._recording_cursor_key("certified_binary64_spin", context, path, max_steps,
                                        initial, omega, phase_plan)
        self.work.charge("orientation_stationary", 3)
        if not any(omega) or not elapsed:
            # The original recurrence returns the identical source initial
            # value on this branch, independently of all earlier cursor keys.
            return self._project_rotation(initial)
        # Retain the ordinary absolute elapsed / omega / plan checks before
        # inspecting a cached cursor or a previously controlled increment.
        plan = self.source_ops._checked_spin_plan(omega, elapsed, phase_plan)
        previous = self.work.lookup(key)
        delta, increment = None, None
        step_limit = min(max_steps, MAX_FLOAT_ROTATION_STEPS)
        if previous is not None and previous[2] < step_limit:
            last, rotation, count, old_delta, old_increment = previous
            self.work.charge("recording_float_cursor_guard")
            self.work.guard(last, count)
            self._rotation_domain(rotation)
            delta = self.source_ops._op(elapsed, last, "sub")
            from .reach_numeric import compare
            if compare(abs(delta), plan.max_elapsed_s, self.work) > 0:
                delta = None
        if delta is None:
            result = self._project_rotation(self.source_ops.advance_orientation(
                initial, omega, elapsed, phase_plan=plan), structural=False)
            count = 1
        else:
            if delta:
                if delta == old_delta:
                    self.work.charge("recording_float_increment_reuse")
                    increment = old_increment
                else:
                    increment = self._project_rotation(self.source_ops.spin_rotation(
                        omega, delta, phase_plan=plan), structural=False)
                result = self._product(increment, rotation)
            else:
                result = rotation
                delta, increment = old_delta, old_increment
            self.work.charge("recording_float_rotation_step")
            self._require_domain()
            count += 1
        self._require_domain()
        self.work.remember(key, (elapsed, result, count, delta, increment))
        self._require_domain()
        return result

    def make_recording(self, position=ZERO, orientation=UNIT):
        self._domain()
        if position is ZERO:
            # The private immutable default is exactly three Fraction zeros.
            # The full native domain guard above proves their exact binary64
            # image; no vector conversion or numerical projection is executed.
            exact_position, result = ZERO, (0.0, 0.0, 0.0)
        else:
            exact_position = self.source_ops._vector(position)
            result = self.source_ops._vector_projection(exact_position)
        if any(abs(v) > _MAX_POSITION for v in result):
            raise _UnsupportedPlanar("A native planar position exceeds its finite domain.")
        rotation = (orientation if type(orientation) is _FloatRotation else
                    self._project_rotation(orientation, structural=type(orientation) is not RotationValue))
        self._rotation_domain(rotation)
        self._require_domain()
        return _FloatPose(result, rotation, tuple(not v for v in exact_position), 0)

    def _pose(self, value):
        if type(value) is _FloatPose:
            if self.work.max_operand_bits != MAX_OPERAND_BITS:
                raise _UnsupportedPlanar("The recording arithmetic domain changed.")
            if value.depth > MAX_FLOAT_DEPTH:
                raise _UnsupportedPlanar("The native planar composition depth is exhausted.")
            return value
        if not isinstance(value, (PoseValue, RecordedTransform)) or value._ops is not self.source_ops:
            raise _UnsupportedPlanar("A planar recording needs private source transforms.")
        self._domain()
        self.work.guard(*value.exact_position, *value.rotation.components, value.rotation.error_rad)
        key = (METHOD, "constant_projection", self.work.max_operand_bits,
               value.exact_position, value.rotation)
        old = self.work.lookup(key)
        if old is not None:
            self._require_domain()
            return old
        result = self.make_recording(value.exact_position,
            self._project_rotation(value.rotation, structural=type(value) is PoseValue))
        self.work.remember(key, result)
        self._require_domain()
        return result

    def compose_recording_fast(self, parent, local):
        self._domain()
        parent = self._pose(parent)
        if parent.depth >= MAX_FLOAT_DEPTH:
            raise _UnsupportedPlanar("A planar composition requires a bounded source leaf.")
        self._rotation_domain(parent.rotation)
        if any(abs(v) > _MAX_POSITION for v in parent.position):
            raise _UnsupportedPlanar("A planar translation exceeds its finite domain.")
        # A genuine source identity has exactly the projection (0, identity).
        # Its frozen projection, if present, is an independent operand and is
        # deliberately left to the ordinary conversion below. Complete private
        # types and the current cap are checked before omitting that conversion.
        if (type(local) is PoseValue and local._ops is self.source_ops
                and type(local.exact_position) is tuple and len(local.exact_position) == 3
                and all(type(v) is F and not v for v in local.exact_position)
                and type(local.rotation) is RotationValue
                and type(local.rotation.components) is tuple and len(local.rotation.components) == 4
                and all(type(v) is F for v in local.rotation.components)
                and local.rotation.components[0].numerator > 0 and not any(local.rotation.components[1:])
                and local.rotation.components[0].numerator.bit_length() <= 512
                and local.rotation.components[0].denominator.bit_length() <= 512
                and type(local.rotation.error_rad) is F and local.rotation.frozen_projection is None):
            # The scalar square and its subsequent exact ratio must also fit
            # the ordinary projection preflights. Huge projective scales keep
            # that original path even though they represent the same identity.
            self.work.guard(*local.exact_position, *local.rotation.components, local.rotation.error_rad)
            self._require_domain()
            return _FloatPose(parent.position, parent.rotation, parent.zeros, parent.depth + 1)
        local = self._pose(local)
        # Only source leaf transforms may be placed on the right. This avoids
        # amplifying an already approximate local origin in nested products.
        if local.depth:
            raise _UnsupportedPlanar("A planar composition requires a bounded source leaf.")
        if any(abs(v) > _MAX_POSITION for v in local.position):
            raise _UnsupportedPlanar("A planar translation exceeds its finite domain.")
        op = self._native
        if all(local.zeros):
            position, zeros = parent.position, parent.zeros
        else:
            if parent.rotation.zero_z and parent.rotation.w == 1.0:
                offset, offset_zeros = local.position, local.zeros
            else:
                offset, offset_zeros = self._rotated_offset(parent.rotation, local.position, local.zeros)
            position = tuple(b if az else a if bz else op(a, b, "add")
                             for a, b, az, bz in zip(parent.position, offset, parent.zeros, offset_zeros))
            zeros = tuple(a and b for a, b in zip(parent.zeros, offset_zeros))
            position = tuple(0.0 if zero else value for value, zero in zip(position, zeros))
        rotation = self._product(parent.rotation, local.rotation)
        return _FloatPose(position, rotation, zeros, parent.depth + 1)


def _planar_paths(simulator, state, selected, *, dynamic_roots=None):
    """Classify complete dependency paths; unsupported paths stay original."""
    incoming = simulator._incoming(state)
    objects, frames, resolving = {}, {"world": True}, set()
    object_roots, frame_roots = {}, {"world": None}

    def planar_rotation(rotation):
        values = rotation.components if type(rotation) is RotationValue else rotation
        return isinstance(values, (list, tuple)) and len(values) == 4 and not values[1] and not values[2]

    def frame(path):
        if path not in frames:
            stem = path.removesuffix(".frame")
            if stem in simulator.model.objects:
                frames[path] = instance(stem)
                frame_roots[path] = object_roots[stem]
            else:
                site = simulator.model.sites[stem]
                frames[path] = instance(site.owner) and planar_rotation(site.pose.rotation)
                frame_roots[path] = object_roots[site.owner]
        return frames[path]

    def instance(path):
        if path in objects:
            return objects[path]
        simulator._check()
        if path in resolving:
            raise _UnsupportedPlanar("A source dependency cycle cannot use planar recording.")
        resolving.add(path)
        root = None
        if path in incoming:
            kind, relation = incoming[path]
            if kind == "follow":
                follow = simulator.model.follows[relation]
                value = frame(follow.parent) and planar_rotation(follow.offset.rotation)
                root = frame_roots[follow.parent]
            else:
                joint = simulator.model.joints[relation]
                value = (frame(joint.parent + ".frame")
                         and planar_rotation(simulator.model.sites[joint.child].pose.rotation)
                         and (joint.kind != "hinge" or (not joint.axis[0] and not joint.axis[1] and bool(joint.axis[2]))))
                root = frame_roots[joint.parent + ".frame"]
        elif state.modes[path] == "dynamic":
            value = False
            if dynamic_roots is not None:
                initial = state.dynamic[path].state
                rotation = initial.rotation if hasattr(initial, "rotation") else initial.orientation
                value = planar_rotation(rotation) and not initial.omega[0] and not initial.omega[1]
                root = path
        else:
            rotation = state.root_rotation_values.get(path, state.orientations[path])
            value = planar_rotation(rotation)
            claimant = state.claims.get((path, "orientation"))
            if claimant is not None:
                action, runtime = simulator.model.actions[claimant], state.actions[claimant]
                value = value and not action.vector[0] and not action.vector[1]
                value = value and planar_rotation(runtime.initial_rotation or runtime.initial)
        resolving.remove(path)
        objects[path] = value
        object_roots[path] = root
        return value

    supported = frozenset(path for path in selected if frame(path))
    if dynamic_roots is not None:
        dynamic_roots.update((path, frame_roots[path]) for path in supported if frame_roots[path] is not None)
    return supported


def _constant_hinge(simulator, state, recording_path):
    """Check only the current law actually requested by this transform graph."""
    simulator._check()
    if not recording_path.startswith("hinge:"):
        return False
    path = recording_path[len("hinge:"):]
    claimant = state.claims.get((path, "coordinate"))
    if claimant is None:
        return True
    action, runtime = simulator.model.actions[claimant], state.actions[claimant]
    if runtime.status != "running":
        return True
    if action.kind == "reach_planar":
        index = 0 if path == action.reach.shoulder else 1
        return runtime.initial[index] == runtime.solution.target_rad[index]
    return runtime.initial == action.goal


def _certify_rotation(orientation, radius, work, *, rotation_zeros=None, float_radius=None):
    q_radius = _upper_float(radius, work) if float_radius is None else float_radius
    # Both original and candidate use the source's canonical quaternion sign.
    # A nonstructural leading component close to zero cannot prove that sign.
    q = orientation
    if abs(q[0]) <= q_radius and not (rotation_zeros and rotation_zeros[0]):
        return False
    for index, value in enumerate(q):
        if index in (1, 2) or rotation_zeros and rotation_zeros[0 if index == 0 else 1]:
            continue
        if not certified_float32_cell(value, q_radius, work=work):
            return False
    return True


def _rotation_cell_groups(candidates, work):
    """Share only actual identical immutable rotations in this one graph.

    Every member already has its own validated source-path enclosure. A
    successful maximum-radius proof covers them all; a failed group proof
    leaves every member eligible for its own smaller radius before refinement.
    This temporary graph index survives neither a key nor a sampler call.
    """
    from .reach_numeric import compare
    groups = {}
    for _, value, _, excess in candidates:
        rotation = value.rotation
        key = (id(rotation), rotation.zero_w, rotation.zero_z)
        previous = groups.get(key)
        float_radius = excess._cell_radii[1] if excess._cell_radii is not None else None
        if previous is None:
            groups[key] = (value.orientation, excess.quaternion_component, float_radius, 1)
        else:
            orientation, radius, old_float_radius, count = previous
            if compare(excess.quaternion_component, radius, work) > 0:
                radius = excess.quaternion_component
                old_float_radius = float_radius
            groups[key] = (orientation, radius, old_float_radius, count + 1)
    certified = set()
    for key, (orientation, radius, float_radius, count) in groups.items():
        if count > 1 and _certify_rotation(orientation, radius, work,
                                         rotation_zeros=key[1:], float_radius=float_radius):
            certified.add(key)
    return certified


def _certify_pose(pose, excess, work, *, zeros=None, rotation_zeros=None,
                  rotation_certified=False):
    if rotation_certified:
        work.charge("recording_rotation_cell_reuse")
        if work.max_operand_bits != MAX_OPERAND_BITS:
            raise _UnsupportedPlanar("The recording arithmetic domain changed.")
    elif not _certify_rotation(pose.orientation, excess.quaternion_component, work,
                              rotation_zeros=rotation_zeros,
                              float_radius=excess._cell_radii[1] if excess._cell_radii is not None else None):
        return False
    p_radius = (excess._cell_radii[0] if excess._cell_radii is not None else
                _upper_float(excess.position_m, work))
    for index, value in enumerate(pose.position):
        if zeros and zeros[index]:
            continue
        if not certified_float32_cell(value, p_radius, work=work):
            return False
    return True


def _sample_planar_frames(simulator, time, state, selected_paths, *, context,
                          moving_frames, phase_bounds, require_same_cells,
                          phase_interval=None, recording_angular_proof=None):
    """Return independently bounded candidates, or request phase replay.

    The exporter calls the original sampler at a phase's first/final boundary.
    Every unsupported complete dependency path uses that original recurrence
    context at every key. No approximate parent enters a source composition.
    """
    selected = tuple(selected_paths)
    dynamic_roots = {} if phase_interval is not None and not require_same_cells else None
    ops = Binary64RecordingOps(simulator.pose_ops,
        constant_hinge_check=lambda path: _constant_hinge(simulator, state, path),
        share_arithmetic=len(selected) > 16, affine_coordinates=not require_same_cells,
        dynamic_phase=phase_interval if dynamic_roots is not None else None,
        dynamic_bounds=phase_bounds if dynamic_roots is not None else None)
    try:
        ops._domain()
        supported_set = _planar_paths(simulator, state, selected, dynamic_roots=dynamic_roots)
        supported = tuple(path for path in selected if path in supported_set)
        ordinary = tuple(path for path in selected if path not in supported_set)
        frames = (simulator.recording_frames(time, state, ordinary, moving_frames=moving_frames,
                  recording_context=context, recording_angular_proof=recording_angular_proof)
                  if ordinary else {})
        excesses = {path: _ZERO_EXCESS for path in ordinary}
        # Ask the existing graph for its private transforms so structural zero
        # proofs survive to the rounding gate. Its ordinary source paths and
        # public recording_frames interface are not changed by this helper.
        _, private = simulator._resolve_kinematics(time, state, selected_frames=tuple(supported),
            pose_only=True, recording_only=True, recording_moving_frames=moving_frames,
            recording_context=context, recording_pose_ops=ops)
        from .reach_runtime import RecordingPose
        candidates = []
        for path in supported:
            simulator._check()
            value = private[path]
            if type(value) is not _FloatPose:
                value = ops._pose(value)
                private[path] = value
            bound = phase_bounds[path]
            dynamic = dynamic_roots is not None and path in dynamic_roots
            if dynamic:
                root = dynamic_roots[path]
                extent = ops.dynamic_extents.get(root)
                simulator.work.charge("recording_dynamic_path_extent")
                ops._require_domain()
                if type(extent) is not F or type(bound.max_position_l1_m) is not F:
                    raise _UnsupportedPlanar("A dynamic path is missing its completed root extent.")
                from .reach_numeric import compare
                if compare(extent, bound.max_position_l1_m, simulator.work) > 0:
                    raise _UnsupportedPlanar("A dynamic descendant does not enclose its root's ballistic extent.")
                ops._require_domain()
            excess = recording_float_excess(bound, work=simulator.work,
                                            include_cell_radii=require_same_cells, dynamic=dynamic)
            pose = RecordingPose(value.position, value.orientation)
            candidates.append((path, value, pose, excess))
        certified_rotations = (_rotation_cell_groups(candidates, simulator.work)
                               if require_same_cells else set())
        ambiguous = []
        for path, value, pose, excess in candidates:
            if not require_same_cells:
                frames[path], excesses[path] = pose, excess
                continue
            rotation_key = (id(value.rotation), value.rotation.zero_w, value.rotation.zero_z)
            if _certify_pose(pose, excess, simulator.work, zeros=value.zeros,
                             rotation_zeros=(value.rotation.zero_w, value.rotation.zero_z),
                             rotation_certified=rotation_key in certified_rotations):
                frames[path], excesses[path] = pose, excess
            else:
                ambiguous.append(path)
        if ambiguous:
            # A direct kernel does not claim to reproduce the recurrence's
            # private state. Its small independent enclosure must still prove
            # the same float32 cell. Otherwise the complete phase is replayed.
            direct = simulator.recording_frames(time, state, ambiguous, moving_frames=moving_frames)
            for path in ambiguous:
                excess = _direct_excess(phase_bounds[path], work=simulator.work)
                value = private[path]
                if not _certify_pose(direct[path], excess, simulator.work, zeros=value.zeros,
                                     rotation_zeros=(value.rotation.zero_w, value.rotation.zero_z)):
                    raise RecordingRoundingAmbiguity(path)
                frames[path], excesses[path] = direct[path], excess
        if simulator.work.max_operand_bits != MAX_OPERAND_BITS:
            raise _UnsupportedPlanar("The recording arithmetic domain changed.")
        return CertifiedRecordingFrames(frames, excesses)
    except _UnsupportedPlanar as error:
        if simulator.work.callback_error is error:
            raise
        raise RecordingRoundingAmbiguity(None, reason=str(error)) from error


def sample_bounded_frames(simulator, time, state, selected_paths, *, context,
                          moving_frames, phase_bounds, phase_interval=None,
                          recording_angular_proof=None):
    """Production recording with rigorous additional endpoint allowances.

    No equality with an earlier recorder's rounded accessors is claimed. The
    full original source-bound and stored-conversion terms remain required in
    addition to these explicit native arithmetic allowances. The independent
    reader evaluates the actual delivered values and every requested bound.
    """
    return _sample_planar_frames(simulator, time, state, selected_paths,
        context=context, moving_frames=moving_frames, phase_bounds=phase_bounds,
        require_same_cells=False, phase_interval=phase_interval,
        recording_angular_proof=recording_angular_proof)


def sample_certified_frames(simulator, time, state, selected_paths, *, context,
                            moving_frames, phase_bounds, phase_interval=None,
                            recording_angular_proof=None):
    """Optional diagnostic retaining the earlier recorder's float32 cells."""
    return _sample_planar_frames(simulator, time, state, selected_paths,
        context=context, moving_frames=moving_frames, phase_bounds=phase_bounds,
        require_same_cells=True, phase_interval=phase_interval,
        recording_angular_proof=recording_angular_proof)
