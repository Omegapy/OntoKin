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
from types import MappingProxyType

from .reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, compare, rational, round_binary64
from .reach_pose import (AXIS_ERROR, PRODUCT_ERROR, MAX_RECORDING_ROTATION_STEPS,
                         PoseValue, RecordedTransform, ReachPoseOps, RotationValue, SpinPlan, ZERO, UNIT)

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
    # ``z`` is the axial component in the legacy two-component recurrence.
    # A proper cyclic coordinate permutation places it on X, Y or Z without
    # changing any native arithmetic or its existing error enclosure.
    axis: int = 2


@dataclass(frozen=True)
class _FloatPose:
    position: tuple[float, float, float]
    rotation: _FloatRotation
    zeros: tuple[bool, bool, bool]
    depth: int

    @property
    def orientation(self):
        vector = [0.0, 0.0, 0.0]
        vector[self.rotation.axis] = self.rotation.z
        return (self.rotation.w, *vector)


def _cartesian_axis(values):
    """Identify one exact nonzero native component, without normalizing it."""
    if (type(values) is not tuple or len(values) != 3
            or any(type(value) not in (int, float, F)
                   or type(value) is float and not math.isfinite(value) for value in values)):
        return None
    indices = tuple(index for index, value in enumerate(values) if value)
    return indices[0] if len(indices) == 1 else None


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
class _ExactAffinePosition:
    """One current exact source position, not a native approximate law."""
    values: tuple[F, F, F]


@dataclass(frozen=True)
class _BallisticLaw:
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    acceleration: tuple[float, float, float]
    horizon: F
    extent: F
    proved_extent: F


def _checked_compare(left, right, work):
    """Charge every actual rational ordering and retain the native domain."""
    result = compare(left, right, work)
    if work.max_operand_bits != MAX_OPERAND_BITS:
        raise _UnsupportedPlanar("The recording arithmetic domain changed.")
    return result


def _captured_recording_seed_key(proof, frame, time, work):
    """Describe a complete immutable direct calculation, without its result.

    Names and outer translations are absent only where the existing ordered
    orientation recipe proves that they cannot enter the source calculation.
    The temporary map contains structural recipes, never retained poses. The
    actual completed rotation belongs to the ordinary bounded work cache.
    """
    from .reach_phase import (RecordingAngularFrame, RecordingAngularProof,
                              _recording_orientation_recipe)

    if (work.max_operand_bits != MAX_OPERAND_BITS
            or type(proof) is not RecordingAngularProof
            or type(proof.frames) is not MappingProxyType
            or type(proof.start) is not F or type(proof.end) is not F
            or type(frame) is not str or type(time) is not F):
        return None
    recipes, visiting = {}, set()

    def immutable_witness(value):
        # Frozen witnesses use only exact tuple/int/string/None nodes. Do not
        # let Python's bool/int/float equality alias an invalid frozen operand
        # to a previously admitted integer. Unsupported shapes keep the direct
        # decoder and its original error rather than acquiring cache authority.
        pending, count = [(value, 0)], 0
        while pending:
            current, depth = pending.pop()
            if count % 32 == 0:
                work.charge("recording_body_seed_witness_block")
            count += 1
            if count > 512 or depth > 8:
                return False
            if type(current) is tuple:
                if len(current) > 32:
                    return False
                pending.extend((part, depth + 1) for part in current)
            elif current is not None and type(current) not in (int, str):
                return False
        return True

    def recipe(path):
        if path in recipes:
            return recipes[path]
        if path in visiting:
            return None
        record = proof.frames.get(path)
        if (type(record) is not RecordingAngularFrame
                or not immutable_witness(record.witness)):
            return None
        if (record.witness and record.witness[0] == "root"
                and len(record.witness) == 10 and record.witness[8] is not None):
            # A prescribed root spin also consumes a separately admitted
            # source spin-phase plan from the work cache. Its precision and
            # horizon are not supplied by this witness, so retain the direct
            # calculation rather than treating the witness as a complete key.
            return None
        visiting.add(path)
        try:
            parent = recipe(record.parent) if record.parent is not None else None
            result = _recording_orientation_recipe(record, parent, work=work)
        finally:
            visiting.remove(path)
        recipes[path] = result
        return result

    complete = recipe(frame)
    if complete is None or work.max_operand_bits != MAX_OPERAND_BITS:
        return None
    return ("recording_captured_direct_seed_v1", MAX_OPERAND_BITS,
            proof.start, proof.end, time, complete)


def captured_recording_orientation(source_ops, proof, frame, time, *, spin_plans=None):
    """Evaluate a direct private orientation from an admitted frozen witness.

    The caller has checked the current complete witness chain. A seed must use
    those same operands even if a work callback temporarily changes the live
    source. Identical complete calculations may reuse their private exact seed
    in the existing bounded cache. The caller must still admit its live source
    after every cache callback before publishing a body cursor. Only source
    quaternion/coordinate kernels run here; neither unused positions nor any
    ancestor recording cursor are evaluated.
    """
    from .reach_phase import RecordingAngularProof

    work = source_ops.work
    work.charge("recording_body_seed_domain")
    if type(proof) is not RecordingAngularProof or type(time) is not F:
        raise ReachAdmissionError("reach_domain", "A direct carrier seed needs its captured phase and clock.")
    work.guard(time)
    while True:
        cap = work.max_operand_bits
        key = _captured_recording_seed_key(proof, frame, time, work)
        if work.max_operand_bits != cap:
            continue
        if key is not None:
            value = work.lookup(key)
            if work.max_operand_bits != cap:
                continue
            if value is not None:
                work.guard(*value.components, value.error_rad)
                return value
        # The direct source kernel owns its refusals. Only successful work may
        # be replayed after a callback changes the operand cap.
        value = (_captured_recording_orientation_direct(source_ops, proof, frame, time)
                 if spin_plans is None else _captured_recording_orientation_direct(
                     source_ops, proof, frame, time, spin_plans=spin_plans))
        if work.max_operand_bits != cap:
            continue
        if key is not None:
            work.remember(key, value)
        if work.max_operand_bits == cap:
            return value


def _captured_recording_orientation_direct(source_ops, proof, frame, time, *, spin_plans=None):
    """Original complete source calculation for one captured private seed."""
    from .reach_kinematics import recording_pair
    from .reach_phase import RecordingAngularFrame

    work = source_ops.work

    def thaw(value):
        if type(value) is not tuple or not value:
            raise ReachAdmissionError("reach_domain", "A carrier seed operand is not a frozen source value.")
        kind = value[0]
        if kind == "none" and len(value) == 1:
            return None
        if kind == "string" and len(value) == 2 and type(value[1]) is str:
            return value[1]
        if kind == "tuple" and len(value) == 2 and type(value[1]) is tuple and len(value[1]) <= 4:
            return tuple(thaw(part) for part in value[1])
        if kind == "private_rotation" and len(value) == 4:
            return RotationValue(thaw(value[1]), thaw(value[2]),
                frozen_projection=None if value[3] is None else thaw(value[3]))
        work.charge("recording_body_seed_decode")
        if kind == "binary64" and len(value) == 2 and type(value[1]) is str and len(value[1]) <= 32:
            result = float.fromhex(value[1])
            if math.isfinite(result):
                return result
        elif kind == "integer" and len(value) == 2 and type(value[1]) is int:
            work.guard(value[1])
            return value[1]
        elif (kind == "rational" and len(value) == 3
                and type(value[1]) is int and type(value[2]) is int and value[2] > 0):
            work.guard(value[1], value[2])
            return F(value[1], value[2])
        raise ReachAdmissionError("reach_domain", "A direct carrier seed has an invalid captured operand.")

    def elapsed(law):
        saved, since = thaw(law[11]), thaw(law[12])
        if thaw(law[7]) != "running":
            return saved
        return source_ops._op(saved, source_ops._op(time, since, "sub"), "add")

    def coordinate(witness):
        law = witness[9]
        if law is None:
            return thaw(witness[10])
        kind, start, duration = thaw(law[1]), thaw(law[8]), thaw(law[3])
        clock = elapsed(law)
        if kind == "reach_planar":
            pair = recording_pair(start, thaw(law[10]), duration, clock,
                                  running=thaw(law[7]) == "running", work=work)
            shoulder, elbow = thaw(law[6])
            if witness[1] not in (shoulder, elbow):
                raise ReachAdmissionError("reach_domain", "A captured reach does not own this carrier.")
            return pair.coordinates_rad[0 if witness[1] == shoulder else 1]
        if kind != "tween":
            raise ReachAdmissionError("reach_domain", "A captured hinge has an unsupported coordinate law.")
        target = thaw(law[5])
        initial, goal = rational(start, work), rational(target, work)
        difference = source_ops._op(goal, initial, "sub")
        if clock == duration:
            return target
        value = source_ops._op(initial, source_ops._op(
            source_ops._op(difference, clock, "mul"), duration, "div"), "add")
        return round_binary64(value, work=work)

    visiting = set()
    def rotation(path):
        work.charge("recording_body_seed_frame")
        record = proof.frames.get(path)
        if type(record) is not RecordingAngularFrame or path in visiting:
            raise ReachAdmissionError("reach_domain", "A captured carrier seed needs a complete acyclic ancestry.")
        visiting.add(path)
        witness = record.witness
        kind = witness[0]
        if kind == "world":
            value = RotationValue(UNIT)
        elif kind == "root":
            law = witness[8]
            if law is None:
                value = source_ops._rotation(thaw(witness[6]) or thaw(witness[5]))
            else:
                initial = thaw(law[14]) or thaw(law[8])
                omega, clock = thaw(law[4]), elapsed(law)
                plan = (work.lookup(("reach_source_spin_phase", tuple(omega))) if spin_plans is None
                        else spin_plans.get(path))
                if plan is not None and compare(abs(clock), plan.max_elapsed_s, work) > 0:
                    plan = None
                value = source_ops.advance_orientation(initial, omega, clock, phase_plan=plan)
        elif kind in {"site", "follow"}:
            parent = rotation(record.parent)
            local = source_ops._rotation(thaw(witness[-1][1]))
            value = source_ops.multiply(parent, local)
        elif kind == "joint":
            parent = rotation(record.parent)
            local = (source_ops.axis_rotation(thaw(witness[5]), coordinate(witness))
                     if thaw(witness[2]) == "hinge" else RotationValue(UNIT))
            parent = source_ops.multiply(parent, local)
            child = source_ops.inverse_rotation(source_ops._rotation(thaw(witness[8][1])))
            value = source_ops.multiply(parent, child)
        else:
            raise ReachAdmissionError("reach_domain", "A direct carrier seed has an unsupported captured frame.")
        visiting.remove(path)
        return value

    return rotation(frame)


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
                 dynamic_bounds=None, body_cursors=False, cartesian_axes=False):
        if type(body_cursors) is not bool or type(cartesian_axes) is not bool:
            raise ValueError("The native carrier cursor and Cartesian selectors must be boolean.")
        super().__init__(source_ops.work)
        self.source_ops = source_ops
        self.constant_hinges = constant_hinges
        self.constant_hinge_check = constant_hinge_check
        self.share_arithmetic = share_arithmetic
        self.affine_coordinates = affine_coordinates
        self.dynamic_phase = dynamic_phase
        self.dynamic_bounds = dynamic_bounds
        # Only the production sampler opts into complete carrier recurrence.
        # The strict stored-cell diagnostic retains its original local factors.
        self.recording_body_cursors = body_cursors
        self.recording_cartesian_axes = cartesian_axes
        self._recording_cartesian_selector = cartesian_axes
        self._recording_cartesian_dispatch = None
        # A production graph supplies only its currently varying local hinges.
        # This one-traversal structural selector is not a numerical proof or
        # retained cache; explicit low-level callers may leave it unrestricted.
        self.recording_body_hinges = None
        # This per-graph index refers to completed bounded-cache root laws.
        # It is discarded after the sampler call, never retained as a cache.
        self.dynamic_extents = {}

    def _domain(self):
        self.work.charge("recording_float_domain")
        self._require_domain()

    def _require_domain(self):
        """Recheck after the last callback without charging another callback."""
        if self.work.max_operand_bits != MAX_OPERAND_BITS:
            raise _UnsupportedPlanar("The recording arithmetic domain changed.")
        if self.recording_cartesian_axes is not self._recording_cartesian_selector:
            raise _UnsupportedPlanar("The recording Cartesian selector changed.")
        if self._recording_cartesian_dispatch is not None:
            simulator, kind, methods = self._recording_cartesian_dispatch
            if (type(simulator) is not kind or any(name in simulator.__dict__
                    or getattr(kind, name, None) is not method for name, method in methods)):
                raise _UnsupportedPlanar("The captured Cartesian source dispatch changed.")

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
                or type(value.zero_w) is not bool or type(value.zero_z) is not bool
                or type(value.axis) is not int or value.axis not in (0, 1, 2)
                or value.axis != 2 and self.recording_cartesian_axes is not True):
            raise _UnsupportedPlanar("A native planar rotation left its proved domain.")

    @staticmethod
    def _rotation_bits(value):
        # Numerical equality coalesces signed zeros. Include their actual bits
        # so a pure arithmetic hit has exactly the same binary64 operands.
        return struct.pack("<dd??B", value.w, value.z, value.zero_w, value.zero_z, value.axis)

    def _project_rotation(self, rotation, *, structural=True, axis_hint=None):
        rotation = self.source_ops._rotation(rotation)
        if (type(rotation.components) is not tuple or len(rotation.components) != 4
                or any(type(v) is not F for v in rotation.components)):
            raise _UnsupportedPlanar("A recorded rotation needs four private exact components.")
        nonzero = tuple(index for index, value in enumerate(rotation.components[1:]) if value)
        if (len(nonzero) > 1 or axis_hint is not None and
                (type(axis_hint) is not int or axis_hint not in (0, 1, 2))):
            raise _UnsupportedPlanar("A recorded rotation needs one Cartesian axis.")
        axis = nonzero[0] if nonzero else 2 if axis_hint is None else axis_hint
        if (axis_hint is not None and axis != axis_hint
                or axis != 2 and self.recording_cartesian_axes is not True):
            raise _UnsupportedPlanar("A recorded rotation left its admitted Cartesian axis.")
        projection = self.source_ops._unit_projection(rotation)
        self._require_domain()
        if (type(projection) is not tuple or len(projection) != 4
                or any(type(v) is not float or not math.isfinite(v) for v in projection)):
            raise _UnsupportedPlanar("A projected recorded rotation must have four finite binary64 components.")
        w, z = projection[0], projection[axis + 1]
        if (any(value != 0.0 for index, value in enumerate(projection[1:]) if index != axis)
                or any(v == 0.0 and math.copysign(1.0, v) < 0 for v in projection)):
            raise _UnsupportedPlanar("The projected rotation needs one Cartesian axis and canonical zeros.")
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
                      op(decoded[axis + 1], decoded[axis + 1], "mul"), "add")
            defect = abs(op(norm, F(1), "sub"))
            self._require_domain()
            # A correctly rounded unit projection has squared-norm defect
            # <=2u+u^2. Four u leaves a conservative exact admission margin.
            outside = compare(defect, F(1, 2**51), self.work) > 0
            self._require_domain()
            if outside:
                raise _UnsupportedPlanar("The frozen source projection is outside its unit-rounding envelope.")
        result = _FloatRotation(w, z, False, False, axis)
        self._rotation_domain(result)
        return _FloatRotation(w, z,
            structural and not rotation.components[0] and w == 0.0 and math.copysign(1.0, w) > 0,
            structural and not rotation.components[axis + 1] and z == 0.0 and math.copysign(1.0, z) > 0,
            axis)

    def _axis_rotation(self, axis, coordinate, *, structural=True):
        """Reuse one completed controlled kernel and native unit projection.

        Callers have already decoded the exact axis/coordinate and checked the
        scalar/Z domain. Different path cursors still advance independently;
        only this pure function of complete immutable operands is shared.
        """
        self._require_domain()
        self.work.guard(*axis, coordinate)
        index = _cartesian_axis(axis)
        if index is None or index != 2 and self.recording_cartesian_axes is not True:
            raise _UnsupportedPlanar("A native axis projection needs an admitted Cartesian axis.")
        key = (METHOD, "axis_projection", self.work.max_operand_bits,
               axis, coordinate, structural)
        old = self.work.lookup(key)
        self._require_domain()
        if old is not None:
            return old
        result = self._project_rotation(self.source_ops.axis_rotation(axis, coordinate),
                                        structural=structural, axis_hint=index)
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
        return self.recording_affine_coordinate(initial, target, action.duration,
            runtime.elapsed, runtime.running_since, time, running=running)

    def recording_affine_coordinate(self, initial, target, duration, saved_elapsed,
                                    running_since, time, *, running):
        """Evaluate the same admitted law from complete immutable input bindings."""
        law = self._affine_law(initial, target, duration, running=running)
        self.work.charge("recording_affine_clock_domain")
        self._require_domain()
        # Check the actual clock operands before forming a difference, rather
        # than trusting a previously valid clock or an unguarded Fraction sum.
        clocks = (saved_elapsed, time, running_since) if running else (saved_elapsed,)
        self._immutable_scalar_domain(clocks, small=True)
        clocks = tuple(value if type(value) is F else rational(value, self.work) for value in clocks)
        self._immutable_scalar_domain(clocks, small=True)
        if running:
            offset = (clocks[1] if not clocks[2] else
                      self.source_ops._op(clocks[1], clocks[2], "sub"))
            elapsed = offset if not clocks[0] else self.source_ops._op(clocks[0], offset, "add")
        else:
            elapsed = clocks[0]
        self._immutable_scalar_domain((elapsed,), small=True)
        if elapsed.numerator < 0 or _checked_compare(elapsed, law.duration, self.work) > 0:
            raise ReachAdmissionError("reach_numeric", "Invalid recording affine clock.")
        self._require_domain()
        return _AffineCoordinate(law, elapsed, running)

    def _affine_operand_domain(self, coordinate):
        """Admit the complete current clock even for a constant affine law."""
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
        self._require_domain()
        return law, elapsed, running

    def _affine_axis_rotation(self, axis, coordinate, *, context, path, max_steps):
        law, elapsed, running = self._affine_operand_domain(coordinate)
        key = self._recording_cursor_key("bounded_affine_axis", context, path, max_steps,
                                         axis, law, running)
        if not law.slope and law.initial == law.target:
            # Every seed and every zero increment has the identical private
            # value. No path/history-dependent recurrence is executed here;
            # the complete current clock, cursor domain and live cap above
            # remain mandatory. Keep the affine path's conservative zero bits.
            return self._axis_rotation(axis, law.initial, structural=False)
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
        direct = self._direct_identity_source_leaf(position, rotation, inverse)
        if direct is not None:
            return direct
        key = (METHOD, "source_leaf", self.work.max_operand_bits,
               self.recording_cartesian_axes, position, rotation, inverse)
        old = self.work.lookup(key)
        self._require_domain()
        if old is not None:
            return old
        result = self._pose(build(pose, inverse=inverse))
        self.work.remember(key, result)
        self._require_domain()
        return result

    def _direct_identity_source_leaf(self, position, rotation, inverse):
        """Project an already binary64 translation and literal unit rotation.

        The ordinary source constructor decodes these exact finite floats and
        projects them back to the same floats. Its only changed zero bits are
        canonical positive zeros. A nonzero inverse translation still needs
        the original source rotation/grid calculation and stays on that path.
        """
        if (any(type(value) is not float for value in (*position, *rotation))
                or rotation != (1.0, 0.0, 0.0, 0.0)
                or any(abs(value) > _MAX_POSITION for value in position)
                or inverse and any(position)):
            return None
        self._require_domain()
        zeros = tuple(value == 0.0 for value in position)
        result = tuple(0.0 if zero else value for value, zero in zip(position, zeros))
        return _FloatPose(result, _FloatRotation(1.0, 0.0, False, True), zeros, 0)

    def _ballistic_law(self, position, velocity, acceleration, *, anchor_time,
                       phase_interval, root_extent, context, path, scene_duration=None):
        """Prove one actual immutable root law against its whole-phase extent."""
        self.work.charge("recording_ballistic_law_domain")
        self._require_domain()
        if (type(anchor_time) is not F or type(phase_interval) is not tuple
                or len(phase_interval) != 2 or any(type(value) is not F for value in phase_interval)
                or type(context) is not object or type(path) is not str):
            raise _UnsupportedPlanar("A native ballistic law needs exact phase and anchor clocks.")
        if scene_duration is not None and type(scene_duration) is not F:
            raise _UnsupportedPlanar("A native ballistic scene duration must be exact.")
        clocks = (anchor_time, *phase_interval, *((scene_duration,) if scene_duration is not None else ()))
        self._immutable_scalar_domain(clocks, small=True)
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
               anchor_time, phase_interval, scene_duration, root_extent,
               *(struct.pack("<ddd", *vector) for vector in vectors))
        previous = self.work.lookup(key)
        self._require_domain()
        if previous is not None:
            return previous
        # The completed law certifies these immutable clock relations as well
        # as its coefficients and extent. A warm key has the identical exact
        # clocks under the same live cap, so no rational ordering is repeated.
        if (anchor_time.numerator < 0
                or any(_checked_compare(left, right, self.work) > 0
                       for left, right in zip(clocks, clocks[1:]))):
            raise _UnsupportedPlanar("A native ballistic phase must follow its anchor within the scene.")
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
        result = _BallisticLaw(*vectors, horizon, extent, root_extent)
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
        if (_checked_compare(phase[0], time, self.work) > 0
                or _checked_compare(time, phase[1], self.work) > 0):
            raise _UnsupportedPlanar("A native dynamic sample does not belong to its actual source phase.")
        elapsed = self.source_ops._op(time, anchor.time, "sub")
        self._immutable_scalar_domain((elapsed,), small=True)
        initial = anchor.state
        root_bound = self.dynamic_bounds.get(path + ".frame") if self.dynamic_bounds is not None else None
        if root_bound is None:
            raise _UnsupportedPlanar("A native dynamic root is missing its actual source bound.")
        law = self._ballistic_law(initial.position, initial.velocity, simulator._acceleration(path, state),
            anchor_time=anchor.time, phase_interval=phase, root_extent=root_bound.max_position_l1_m,
            context=context, path=path, scene_duration=duration)
        # This helper checks the current elapsed range before evaluating any
        # native arithmetic; the caller does not repeat those comparisons.
        position, zeros = self._ballistic_position(law, elapsed)
        rotation = initial.rotation if hasattr(initial, "rotation") else initial.orientation
        orientation = simulator._advance_orientation(rotation, initial.omega, elapsed,
            recording_context=context, recording_path=METHOD + ":dynamic:" + path, recording_pose_ops=self)
        self._rotation_domain(orientation)
        self._require_domain()
        self.dynamic_extents[path] = law
        return _FloatPose(position, orientation, zeros, 0)

    def _product(self, a, b):
        self._domain()
        self._rotation_domain(a)
        self._rotation_domain(b)
        if (a.w, a.z) == (1.0, 0.0) and a.zero_z:
            return b
        if (b.w, b.z) == (1.0, 0.0) and b.zero_z:
            return a
        if a.axis != b.axis:
            raise _UnsupportedPlanar("Native rotation products require the same Cartesian axis.")
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
        result = _FloatRotation(0.0 if zero_w else real, 0.0 if zero_z else imag,
                                zero_w, zero_z, a.axis)
        if key is not None:
            self.work.remember(key, result)
            self._require_domain()
        return result

    def _rotated_offset(self, rotation, position, zeros):
        """Reuse only the complete pure local arithmetic, never world origins."""
        if (type(rotation.axis) is not int or rotation.axis not in (0, 1, 2)
                or rotation.axis != 2 and self.recording_cartesian_axes is not True):
            raise _UnsupportedPlanar("A native offset needs its admitted Cartesian axis.")
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
        # (u, v, axis) is a proper cyclic permutation. Preserve the exact Z
        # operation order, including sign/zero and positive-unit shortcuts.
        axis = rotation.axis
        u, v = (axis + 1) % 3, (axis + 2) % 3
        x, y, zz = position[u], position[v], position[axis]
        local_zeros = zeros[u], zeros[v], zeros[axis]
        c = op(op(w, w, "mul"), op(z, z, "mul"), "sub")
        s = op(op(w, z, "mul"), 2.0, "mul")
        cross_zero = rotation.zero_w or rotation.zero_z
        if local_zeros[1]:
            # Native multiplication by positive one preserves every finite
            # binary64 bit, including signed zeros and subnormals. The coefficients
            # have just passed their original finite/domain callbacks. Foreign
            # scalar types retain both ordinary arithmetic calls.
            unit = type(x) is float and x == 1.0 and type(c) is float and type(s) is float
            offset = ((c, s, zz) if unit else (op(c, x, "mul"), op(s, x, "mul"), zz))
            offset_zeros = (local_zeros[0], local_zeros[0] or cross_zero, local_zeros[2])
        elif local_zeros[0]:
            self.work.charge("recording_float_sign")
            self._require_domain()
            unit = type(y) is float and y == 1.0 and type(c) is float and type(s) is float
            offset = ((-s, c, zz) if unit else (op(-s, y, "mul"), op(c, y, "mul"), zz))
            offset_zeros = (local_zeros[1] or cross_zero, local_zeros[1], local_zeros[2])
        else:
            offset = (op(op(c, x, "mul"), op(s, y, "mul"), "sub"),
                      op(op(s, x, "mul"), op(c, y, "mul"), "add"), zz)
            offset_zeros = (False, False, local_zeros[2])
        order = (u, v, axis)
        offset = tuple(offset[order.index(index)] for index in range(3))
        offset_zeros = tuple(offset_zeros[order.index(index)] for index in range(3))
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
        axis = self.source_ops._recording_vector(axis)
        self._require_domain()
        index = _cartesian_axis(axis)
        if index is None or index != 2 and self.recording_cartesian_axes is not True:
            raise _UnsupportedPlanar("A native hinge needs an admitted nonzero Cartesian axis.")
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

    def recording_body_orientation(self, seed_builder, axis, rate, time, *, phase_start,
                                   phase_end, context, path, proof_token, max_steps,
                                   source_admission=None, source_records=0, stage_cursor=None,
                                   read_cursor=None):
        """Advance a freshly witnessed complete scalar/Z carrier orientation.

        A seed is the ordinary private complete-world source rotation, with
        every ancestor recording cursor disabled. The source phase proof gives
        its exact ideal body rate; native arithmetic contributes only the
        existing finite cursor enclosure. No parent's approximate orientation
        or exposed quaternion can seed this independent recurrence.
        """
        self._domain()
        if (self.recording_body_cursors is not True or type(proof_token) is not object
                or not callable(seed_builder)
                or axis is not None and (type(axis) is not int or axis not in (0, 1, 2)
                    or axis != 2 and self.recording_cartesian_axes is not True)
                or type(source_records) is not int or source_records < 0
                or source_admission is not None and not callable(source_admission)
                or source_admission is None and source_records
                or stage_cursor is not None and (not callable(stage_cursor)
                    or source_admission is not None or source_records)
                or read_cursor is not None and (not callable(read_cursor)
                    or stage_cursor is None)):
            raise _UnsupportedPlanar("A native carrier needs an enabled scalar/Z body proof.")
        values = (rate, time, phase_start, phase_end)
        self._immutable_scalar_domain(values)
        rate, time, phase_start, phase_end = (
            value if type(value) is F else rational(value, self.work) for value in values)
        self._require_domain()
        if axis is None and rate:
            raise _UnsupportedPlanar("A nonzero carrier rate needs its proved Cartesian axis.")
        if (_checked_compare(phase_start, time, self.work) > 0
                or _checked_compare(time, phase_end, self.work) > 0):
            raise ReachAdmissionError("reach_domain", "A carrier cursor lies outside its proved phase.")
        key = self._recording_cursor_key("certified_binary64_body", context, path, max_steps,
                                        proof_token, phase_start, phase_end, axis, rate)
        self._require_domain()
        previous = self.work.lookup(key) if read_cursor is None else read_cursor(key)
        self._require_domain()
        step_limit = min(max_steps, MAX_FLOAT_ROTATION_STEPS)
        delta = increment = None
        if previous is None or previous[2] >= step_limit:
            self.work.charge("recording_float_body_direct_seed")
            self._require_domain()
            rotation = seed_builder()
            self._require_domain()
            if type(rotation) is not RotationValue:
                raise _UnsupportedPlanar("A native carrier seed must be a private complete rotation.")
            # Even an exact interior zero does not establish a structural zero
            # in another history-dependent recording recurrence.
            result = self._project_rotation(rotation, structural=False, axis_hint=axis)
            count = 1
        else:
            last, rotation, count, old_delta, old_increment = previous
            self.work.charge("recording_float_cursor_guard")
            self._require_domain()
            self.work.guard(last, count)
            self._rotation_domain(rotation)
            if rate and time != last:
                delta = self.source_ops._op(time, last, "sub")
                self._require_domain()
                if delta == old_delta:
                    self.work.charge("recording_float_body_increment_reuse")
                    self._require_domain()
                    increment = old_increment
                    self._rotation_domain(increment)
                else:
                    angle = self.source_ops._op(rate, delta, "mul")
                    unit = tuple(F(1) if index == axis else F(0) for index in range(3))
                    increment = self._axis_rotation(unit, angle, structural=False)
                # A body rate postmultiplies the complete orientation. The
                # prescribed root-spin cursor instead has a world left factor.
                result = self._product(rotation, increment)
            else:
                result = rotation
                delta, increment = old_delta, old_increment
            self.work.charge("recording_float_rotation_step")
            self._require_domain()
            count += 1
        self._require_domain()
        if stage_cursor is not None:
            # A complete captured graph delays these source-bound results
            # until its one final source receipt. Pure arithmetic remains in
            # the ordinary LRU, and the staging owner enforces that same bound.
            stage_cursor(key, previous, (time, result, count, delta, increment))
            self._require_domain()
            return result
        admitted = False
        def admit():
            nonlocal admitted
            self._require_domain()
            if source_admission() is not True:
                raise ReachAdmissionError("reach_domain", "The current carrier source was not admitted.")
            admitted = True
            return True
        if source_admission is not None:
            self.work.charge("recording_angular_witness_guard", source_records)
            self._require_domain()
        self.work.remember(key, (time, result, count, delta, increment),
                           admission=admit if source_admission is not None else None)
        self._require_domain()
        # A reentrant cache callback can decline publication. The current
        # returned value still needs its precharged source admission once.
        if source_admission is not None and not admitted:
            admit()
        return result

    def recording_zero_child_origin(self, position):
        """Admit a literal native zero offset without constructing its rationals.

        None leaves the complete ordinary child-vector path in place. Only
        immutable canonical binary64 zeros can skip that numerical decoding;
        the caller's source receipt still binds the actual current child pose.
        """
        if (self.work.max_operand_bits != MAX_OPERAND_BITS or type(position) is not tuple
                or len(position) != 3
                or any(type(value) is not float or value != 0.0 for value in position)):
            return None
        # Both binary64 zero signs decode to the same exact Fraction zero.
        # All operands are immutable and their ordinary preflights fit the
        # full domain; the existing origin checkpoint checks cancellation and
        # the live cap before the caller uses that result.
        self.work.charge("recording_body_child_origin")
        return self.work.max_operand_bits == MAX_OPERAND_BITS

    def recording_parent_origin(self, parent, rotation):
        """Preserve the native origin of a proved zero-child-offset hinge.

        The two omitted joint compositions both have zero local translation.
        Their depth still counts toward the unchanged native topology ceiling;
        no compound approximate local origin enters the position recurrence.
        """
        self._domain()
        if self.recording_body_cursors is not True:
            raise _UnsupportedPlanar("A native parent origin requires its complete carrier proof.")
        parent = self._pose(parent)
        if (type(parent.depth) is not int or not 0 <= parent.depth <= MAX_FLOAT_DEPTH - 2
                or type(parent.position) is not tuple or len(parent.position) != 3
                or any(type(value) is not float or not math.isfinite(value)
                       or abs(value) > _MAX_POSITION for value in parent.position)
                or type(parent.zeros) is not tuple or len(parent.zeros) != 3
                or any(type(zero) is not bool for zero in parent.zeros)):
            raise _UnsupportedPlanar("A native carrier origin left its finite composition domain.")
        self._rotation_domain(parent.rotation)
        self._rotation_domain(rotation)
        self._require_domain()
        return _FloatPose(parent.position, rotation, parent.zeros, parent.depth + 2)

    def recording_relative_pose(self, signature, build, *, context, path, max_steps):
        """Reuse one complete local calculation under a fresh world origin.

        A site/follow has one translated composition. A rigid joint, or a
        hinge with an actually constant affine law, has a zero-translation
        first composition and one translated child inverse. For these shapes
        the original native algorithm adds the world origin exactly once per
        nonzero component. Evaluate the same ordered local operations at an
        exact zero origin, then repeat that original addition for the current
        occurrence. In particular, never subtract two rounded world positions
        or combine successive translations into a newly rounded offset.

        This is a pure immutable numerical result in the existing bounded
        work cache. The caller still resolves current topology, claims and
        coordinates, and completes every carrier's live source admission.
        Unsupported shapes retain their original builder and path cursors.
        """
        from .model import Pose

        if not self.share_arithmetic:
            return None
        affine = None
        if len(signature) == 3 and signature[0] == "follow":
            kind, parent, local = signature
            extra, depth = (), 1
        elif len(signature) == 2 and type(signature[0]) is _FloatPose:
            kind, (parent, local), extra, depth = "site", signature, (), 1
        elif len(signature) == 7 and signature[0] == "joint":
            _, parent, joint_kind, axis, coordinate, slope, local = signature
            if joint_kind == "hinge":
                if (type(coordinate) is not _AffineCoordinate
                        or type(coordinate.law) is not _AffineLaw
                        or coordinate.law.slope or coordinate.law.initial != coordinate.law.target):
                    return None
                if (type(axis) is not tuple or len(axis) != 3
                        or any(type(value) is not float or not math.isfinite(value) for value in axis)
                        or _cartesian_axis(axis) is None
                        or _cartesian_axis(axis) != 2 and self.recording_cartesian_axes is not True):
                    return None
                affine = coordinate
                # A constant law is independent of its admitted elapsed time;
                # retain every other exact operand and actual axis zero bits.
                extra = (joint_kind, struct.pack("<ddd", *axis), coordinate.law, coordinate.running)
            elif joint_kind in {"rigid", "grip"} and coordinate is None and slope is None:
                extra = (joint_kind,)
            else:
                return None
            kind, depth = "joint", 2
        else:
            return None
        if not (type(parent) is _FloatPose and type(parent.depth) is int
                and 0 <= parent.depth <= MAX_FLOAT_DEPTH - depth
                and type(parent.position) is tuple and len(parent.position) == 3
                and all(type(value) is float and math.isfinite(value)
                        and abs(value) <= _MAX_POSITION for value in parent.position)
                and type(parent.zeros) is tuple and len(parent.zeros) == 3
                and all(type(value) is bool for value in parent.zeros)
                and type(local) is Pose and type(local.position) is tuple and len(local.position) == 3
                and type(local.rotation) is tuple and len(local.rotation) == 4
                and all(type(value) is float and math.isfinite(value)
                        for value in (*local.position, *local.rotation))):
            return None
        self.work.charge("recording_relative_pose_domain")
        self._require_domain()
        self._rotation_domain(parent.rotation)
        self._immutable_scalar_domain((*local.position, *local.rotation))
        if affine is not None:
            self._affine_operand_domain(affine)
            self._recording_cursor_key("bounded_affine_relative", context, path, max_steps)
            self._require_domain()
        key = (METHOD, "native_relative_pose", self.work.max_operand_bits, kind,
               self.recording_cartesian_axes, self._rotation_bits(parent.rotation), parent.depth, extra,
               struct.pack("<ddd", *local.position), struct.pack("<dddd", *local.rotation))
        relative = self.work.lookup(key)
        self._require_domain()
        if relative is None:
            origin = _FloatPose((0.0, 0.0, 0.0), parent.rotation,
                                (True, True, True), parent.depth)
            relative = build(origin)
            self._require_domain()
            # The recognized builders return only complete native leaves.
            # Keep the original path if a future builder changes that shape.
            if (type(relative) is not _FloatPose or relative.depth != parent.depth + depth
                    or type(relative.position) is not tuple or len(relative.position) != 3
                    or any(type(value) is not float or not math.isfinite(value)
                           for value in relative.position)
                    or type(relative.zeros) is not tuple or len(relative.zeros) != 3
                    or any(type(value) is not bool for value in relative.zeros)):
                return None
            self._rotation_domain(relative.rotation)
            self.work.remember(key, relative)
            self._require_domain()
        if all(relative.zeros):
            position, zeros = parent.position, parent.zeros
        else:
            position = tuple(b if az else a if bz else self._native(a, b, "add")
                for a, b, az, bz in zip(parent.position, relative.position, parent.zeros, relative.zeros))
            zeros = tuple(a and b for a, b in zip(parent.zeros, relative.zeros))
            position = tuple(0.0 if zero else value for value, zero in zip(position, zeros))
        self._require_domain()
        return _FloatPose(position, relative.rotation, zeros, relative.depth)

    def _reusable_spin_plan(self, plan):
        """Admit every immutable field before a cursor can retain its proof.

        A completed cursor already passed the ordinary exact reconstruction
        of this same omega and plan. The key contains all plan fields; no
        separate identity-result table or unchecked object-identity hit exists.
        """
        if (type(plan) is not SpinPlan or type(plan.scaled_omega) is not tuple
                or len(plan.scaled_omega) != 3 or type(plan.norm_bounds) is not tuple
                or len(plan.norm_bounds) != 2 or type(plan.pi_bounds) is not tuple
                or len(plan.pi_bounds) != 2 or type(plan.precision_bits) is not int):
            return False
        values = (*plan.scaled_omega, plan.maximum, *plan.norm_bounds,
                  *plan.pi_bounds, plan.max_elapsed_s, plan.argument_error_rad)
        if any(type(value) is not F for value in values):
            return False
        self.work.guard(*values, plan.precision_bits)
        self._require_domain()
        return True

    def recording_advance_orientation(self, initial, omega, elapsed, *, context, path,
                                      max_steps, phase_plan=None, stage_cursor=None, read_cursor=None):
        """Reuse checked scalar/Z spin increments without source pose derivatives."""
        self._domain()
        if (stage_cursor is not None and not callable(stage_cursor)
                or read_cursor is not None and (not callable(read_cursor) or stage_cursor is None)):
            raise _UnsupportedPlanar("A private spin cursor needs a complete staging owner.")
        raw_initial, raw_omega, raw_plan = initial, omega, phase_plan
        lookup = self.work.lookup if read_cursor is None else read_cursor

        def scalar_key(value):
            # This is a callback-free admission of immutable native inputs,
            # not another exact decode. Invalid/unusual values keep the old
            # path, including its diagnostics and original normalization.
            if type(value) is float:
                if not math.isfinite(value):
                    return None
                return "binary64", struct.pack("!d", value)
            if type(value) in (int, F):
                if max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_OPERAND_BITS:
                    return None
                return ("integer" if type(value) is int else "rational"), value
            return None

        def immutable_inputs():
            if type(raw_omega) is not tuple or len(raw_omega) != 3:
                return None
            omega_key = tuple(scalar_key(value) for value in raw_omega)
            if (any(value is None for value in omega_key) or raw_omega[0] or raw_omega[1]
                    or not raw_omega[2]):
                return None
            if type(raw_initial) is RotationValue:
                values, error, projection = (raw_initial.components, raw_initial.error_rad,
                                              raw_initial.frozen_projection)
                if (type(values) is not tuple or len(values) != 4
                        or any(type(value) is not F for value in values) or type(error) is not F
                        or scalar_key(error) is None):
                    return None
                if projection is None:
                    projection_key = None
                elif (type(projection) is tuple and len(projection) == 4
                        and all(type(value) is float and math.isfinite(value) for value in projection)):
                    projection_key = tuple(struct.pack("!d", value) for value in projection)
                else:
                    return None
                initial_key = "private", values, error, projection_key
            elif type(raw_initial) is tuple and len(raw_initial) == 4:
                values = raw_initial
                initial_key = "public", tuple(scalar_key(value) for value in values)
            else:
                return None
            if (any(scalar_key(value) is None for value in values)
                    or values[1] or values[2] or not (values[0] or values[3])):
                return None
            plan = raw_plan
            if (type(plan) is not SpinPlan or type(plan.scaled_omega) is not tuple
                    or len(plan.scaled_omega) != 3 or type(plan.norm_bounds) is not tuple
                    or len(plan.norm_bounds) != 2 or type(plan.pi_bounds) is not tuple
                    or len(plan.pi_bounds) != 2 or type(plan.precision_bits) is not int
                    or plan.precision_bits.bit_length() > MAX_OPERAND_BITS):
                return None
            fields = (*plan.scaled_omega, plan.maximum, *plan.norm_bounds,
                      *plan.pi_bounds, plan.max_elapsed_s, plan.argument_error_rad)
            if any(type(value) is not F or scalar_key(value) is None for value in fields):
                return None
            return initial_key, omega_key, fields, plan.precision_bits

        # A completed moving cursor can carry its original normalization and
        # velocity decoding. All fields remain in this one bounded-cache key;
        # no identity-only receipt or second table is introduced. Zero clocks,
        # stationary laws and unusual inputs retain the original path below.
        inputs = (immutable_inputs() if type(elapsed) is F and elapsed
                  and scalar_key(elapsed) is not None else None)
        if inputs is not None and not self._reusable_spin_plan(phase_plan):
            inputs = None
        if inputs is not None:
            captured_initial = (RotationValue(raw_initial.components, raw_initial.error_rad,
                                              raw_initial.frozen_projection)
                                if type(raw_initial) is RotationValue else raw_initial)
            captured_plan = SpinPlan(raw_plan.scaled_omega, raw_plan.maximum,
                raw_plan.norm_bounds, raw_plan.pi_bounds, raw_plan.max_elapsed_s,
                raw_plan.precision_bits, raw_plan.argument_error_rad)
            elapsed = rational(elapsed, self.work)
            key = self._recording_cursor_key("certified_binary64_spin", context, path, max_steps,
                                            "immutable_operands_v1", inputs)
            self._require_domain()
            previous = lookup(key)
            self._require_domain()
            if immutable_inputs() != inputs:
                raise _UnsupportedPlanar("The current spin operands changed during admission.")
            if previous is None:
                initial = self.source_ops._rotation(captured_initial)
                omega = self.source_ops._recording_vector(raw_omega)
                self._require_domain()
                if initial.components[1] or initial.components[2] or omega[0] or omega[1]:
                    raise _UnsupportedPlanar("Only a complete scalar/Z prescribed spin is planar.")
                self.work.charge("orientation_stationary", 3)
                self._require_domain()
                plan = self.source_ops._checked_spin_plan(omega, elapsed, captured_plan)
            else:
                initial, omega = previous[5:]
                plan = captured_plan
                # Only normalization, fixed velocity decoding and the proved
                # nonstationary law are reused. Every new exact clock still
                # receives its own complete absolute-horizon comparison.
                if _checked_compare(abs(elapsed), plan.max_elapsed_s, self.work) > 0:
                    raise ReachAdmissionError("reach_numeric",
                        "A source sample lies outside its proved spin phase.")
        else:
            initial = self.source_ops._rotation(initial)
            elapsed = rational(elapsed, self.work)
            omega = self.source_ops._recording_vector(omega)
            self._require_domain()
            if initial.components[1] or initial.components[2] or omega[0] or omega[1]:
                raise _UnsupportedPlanar("Only a complete scalar/Z prescribed spin is planar.")
            key = self._recording_cursor_key("certified_binary64_spin", context, path, max_steps,
                                            initial, omega, phase_plan)
            self.work.charge("orientation_stationary", 3)
            if not any(omega) or not elapsed:
                # This branch returns the original initial rotation even if
                # an unrelated supplied phase plan would not be admissible.
                return self._project_rotation(initial)
            self._require_domain()
            if self._reusable_spin_plan(phase_plan):
                previous = lookup(key)
                self._require_domain()
                if previous is None:
                    plan = self.source_ops._checked_spin_plan(omega, elapsed, phase_plan)
                else:
                    if _checked_compare(abs(elapsed), phase_plan.max_elapsed_s, self.work) > 0:
                        raise ReachAdmissionError("reach_numeric",
                            "A source sample lies outside its proved spin phase.")
                    plan = phase_plan
            else:
                plan = self.source_ops._checked_spin_plan(omega, elapsed, phase_plan)
                previous = lookup(key)
        self._require_domain()
        delta, increment = None, None
        step_limit = min(max_steps, MAX_FLOAT_ROTATION_STEPS)
        if previous is not None and previous[2] < step_limit:
            last, rotation, count, old_delta, old_increment = previous[:5]
            self.work.charge("recording_float_cursor_guard")
            self.work.guard(last, count)
            self._rotation_domain(rotation)
            delta = self.source_ops._op(elapsed, last, "sub")
            self._require_domain()
            # Both clocks of this exact moving-law cursor were separately
            # admitted to [-H,H]. In the same half interval their difference
            # is also within H; opposite signs retain the original comparison.
            same_half = (inputs is not None and plan.max_elapsed_s.numerator >= 0
                         and (elapsed.numerator < 0) == (last.numerator < 0))
            if same_half:
                # The ordering is implied, but its prospective cross-products
                # must still fit the original exact-comparison domain. Two
                # separately admissible clocks can have unlike denominators.
                self.work.guard_bits(max(
                    delta.numerator.bit_length() + plan.max_elapsed_s.denominator.bit_length(),
                    plan.max_elapsed_s.numerator.bit_length() + delta.denominator.bit_length()))
            elif compare(abs(delta), plan.max_elapsed_s, self.work) > 0:
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
        value = elapsed, result, count, delta, increment
        admitted = False

        def admit():
            nonlocal admitted
            self._require_domain()
            if immutable_inputs() != inputs:
                raise _UnsupportedPlanar("The current spin operands changed before publication.")
            admitted = True
            return True

        if inputs is not None:
            value += initial, omega
        if stage_cursor is not None:
            if inputs is not None:
                admit()
            stage_cursor(key, previous, value)
            self._require_domain()
            return result
        self.work.remember(key, value, admission=admit if inputs is not None else None)
        self._require_domain()
        if inputs is not None and not admitted:
            admit()
        return result

    def recording_affine(self, initial, rate, elapsed):
        """Evaluate exact root translation without retaining one-use projections.

        This changes neither the equation nor binary64 exposure. The fixed
        small domain proves every omitted zero-product prospective guard fits
        the full cap. All other operands retain the ordinary exact helper.
        """
        self.work.charge("recording_affine_source_domain")
        if (self.work.max_operand_bits != MAX_OPERAND_BITS
                or type(initial) is not tuple or len(initial) != 3
                or type(rate) is not tuple or len(rate) != 3
                or type(elapsed) is not F):
            return self.source_ops.recording_affine(initial, rate, elapsed)
        values = (*initial, *rate, elapsed)
        for value in values:
            if type(value) is float:
                if not math.isfinite(value):
                    return self.source_ops.recording_affine(initial, rate, elapsed)
            elif type(value) not in (int, F) or max(
                    value.numerator.bit_length(), value.denominator.bit_length()) > 2048:
                return self.source_ops.recording_affine(initial, rate, elapsed)
        # Finite binary64 decoding needs at most 1075 bits. Every other input
        # above has at most 2048; exact products and sums need at most 6145.
        self.work.guard_bits(6145)
        key = (METHOD, "exact_affine_source_vectors", self.work.max_operand_bits,
               tuple((type(value), value.hex() if type(value) is float else value)
                     for value in (*initial, *rate)))
        decoded = self.work.lookup(key)
        self._require_domain()
        if decoded is None:
            decoded = (self.source_ops._vector(initial), self.source_ops._vector(rate))
            self._require_domain()
            self.work.remember(key, decoded)
            self._require_domain()
        initial, rate = decoded
        self.work.guard(*initial, *rate, elapsed)
        self.work.charge("pose_scale_identity_check")
        self._require_domain()
        if not elapsed or not any(rate):
            scaled = ZERO
        elif elapsed == 1:
            scaled = rate
        else:
            scaled = tuple(self.source_ops._op(value, elapsed, "mul") if value else F(0)
                           for value in rate)
        self._require_domain()
        self.work.charge("pose_add_zero_check")
        self._require_domain()
        if not any(initial):
            result = scaled
        elif not any(scaled):
            result = initial
        else:
            result = tuple(y if not x else x if not y else self.source_ops._op(x, y, "add")
                           for x, y in zip(initial, scaled))
        self._require_domain()
        return _ExactAffinePosition(result)

    def make_recording(self, position=ZERO, orientation=UNIT):
        self._domain()
        if type(position) is _ExactAffinePosition:
            self.work.charge("recording_affine_position_guard")
            self._require_domain()
            exact_position = position.values
            if (type(exact_position) is not tuple or len(exact_position) != 3
                    or any(type(value) is not F for value in exact_position)):
                raise _UnsupportedPlanar("An exact affine position needs three private rational components.")
            self.work.guard(*exact_position)
            # This tuple is a newly evaluated exact point. Its zero components
            # have the canonical positive-zero image without a rounding call;
            # every nonzero component uses the original exact projection.
            result = tuple(round_binary64(value, work=self.work) if value else 0.0
                           for value in exact_position)
            self._require_domain()
        elif position is ZERO:
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
               self.recording_cartesian_axes, value.exact_position, value.rotation)
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


def _planar_paths(simulator, state, selected, *, dynamic_roots=None, varying_hinges=None):
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
                if (value and varying_hinges is not None and joint.kind == "hinge"
                        and not _constant_hinge(simulator, state, "hinge:" + relation)):
                    varying_hinges.add(relation)
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
        dynamic_bounds=phase_bounds if dynamic_roots is not None else None,
        body_cursors=not require_same_cells and recording_angular_proof is not None)
    try:
        ops._domain()
        captured = None
        if ops.recording_body_cursors and ops.share_arithmetic:
            from .reach_recording_capture import sample_captured_carriers
            captured = sample_captured_carriers(simulator, time, state, selected,
                recording_angular_proof, ops, context)
        if captured is not None:
            private, finish_capture = captured
            supported, frames, excesses = selected, {}, {}
        else:
            finish_capture = None
            varying_hinges = set() if ops.recording_body_cursors else None
            supported_set = _planar_paths(simulator, state, selected, dynamic_roots=dynamic_roots,
                                          varying_hinges=varying_hinges)
            ops.recording_body_hinges = frozenset(varying_hinges or ())
            ops.recording_body_cursors = ops.recording_body_cursors and bool(ops.recording_body_hinges)
            supported = tuple(path for path in selected if path in supported_set)
            ordinary = tuple(path for path in selected if path not in supported_set)
            frames = (simulator.recording_frames(time, state, ordinary, moving_frames=moving_frames,
                      recording_context=context, recording_angular_proof=recording_angular_proof)
                      if ordinary else {})
            excesses = {path: _ZERO_EXCESS for path in ordinary}
            # Ask the existing graph for its private transforms so structural
            # zero proofs survive to the rounding gate. Unsupported graphs
            # retain all their ordinary live-source traversal and admission.
            _, private = simulator._resolve_kinematics(time, state, selected_frames=tuple(supported),
                pose_only=True, recording_only=True, recording_moving_frames=moving_frames,
                recording_context=context, recording_pose_ops=ops,
                recording_angular_proof=recording_angular_proof if ops.recording_body_cursors else None)
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
                law = ops.dynamic_extents.get(root)
                simulator.work.charge("recording_dynamic_path_extent")
                ops._require_domain()
                if (type(law) is not _BallisticLaw or type(law.extent) is not F
                        or type(law.proved_extent) is not F or type(bound.max_position_l1_m) is not F):
                    raise _UnsupportedPlanar("A dynamic path is missing its completed root extent.")
                extent, bound_extent = law.extent, bound.max_position_l1_m
                simulator.work.guard(extent, law.proved_extent, bound_extent)
                # Exact Fraction equality compares canonical integer fields.
                # The law has already completed this identical prospective
                # comparison under the same cap. Different descendant bounds
                # still perform their own guarded rational comparison.
                if (bound_extent != law.proved_extent
                        and _checked_compare(extent, bound_extent, simulator.work) > 0):
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
        if finish_capture is not None:
            finish_capture()
        return CertifiedRecordingFrames(frames, excesses)
    except _UnsupportedPlanar as error:
        if simulator.work.callback_error is error:
            raise
        raise RecordingRoundingAmbiguity(None, reason=str(error)) from error


class _BoundedCapturedPhase:
    """Keep optional native fallback and original callback identity at the boundary."""
    def __init__(self, phase):
        self.phase = phase

    def _run(self, method, *args):
        try:
            return method(*args)
        except _UnsupportedPlanar as error:
            if self.phase.ops.work.callback_error is error:
                raise
            raise RecordingRoundingAmbiguity(None, reason=str(error)) from error

    def sample(self, time):
        return self._run(self.phase.sample, time)

    def finish(self):
        return self._run(self.phase.finish)


def begin_bounded_phase(simulator, times, state, selected_paths, *, context,
                        phase_bounds, phase_interval, recording_angular_proof):
    """Open a private finite phase stream; unsupported graphs retain scalar sampling.

    The caller consumes every exact key using the existing pose-output loop,
    then finishes after its final output callback. No source-bound cursor is
    published before that complete phase receipt. Strict-cell diagnostics do
    not call this optional production path.
    """
    if recording_angular_proof is None or len(times) < 2:
        return None
    from .reach_runtime import ReachSimulator
    # Newly captured Cartesian paths previously dispatched through ordinary
    # sampling. Preserve that dispatch for custom simulators and observers;
    # the established Z-only capture/fallback keeps its previous behavior.
    methods = tuple((name, getattr(ReachSimulator, name))
                    for name in ("_incoming", "_resolve_kinematics", "recording_frames"))
    cartesian = (isinstance(simulator, ReachSimulator) and all(name not in simulator.__dict__
                 and getattr(type(simulator), name, None) is method for name, method in methods))
    ops = Binary64RecordingOps(simulator.pose_ops, share_arithmetic=len(selected_paths) > 16,
        affine_coordinates=True, body_cursors=True, cartesian_axes=cartesian,
        dynamic_phase=phase_interval, dynamic_bounds=phase_bounds)
    if ops.recording_cartesian_axes:
        ops._recording_cartesian_dispatch = simulator, type(simulator), methods
    try:
        ops._domain()
        from .reach_recording_capture import begin_captured_phase, begin_mixed_captured_phase
        phase = begin_captured_phase(simulator, times, state, tuple(selected_paths),
            recording_angular_proof, ops, context, phase_bounds=phase_bounds,
            phase_interval=phase_interval)
        if phase is None:
            phase = begin_mixed_captured_phase(simulator, times, state, tuple(selected_paths),
                recording_angular_proof, ops, context, phase_bounds=phase_bounds,
                phase_interval=phase_interval)
        return _BoundedCapturedPhase(phase) if phase is not None else None
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
