"""Exact clocks and conservative arithmetic for recorded planar reach delivery.

This implementation does not import the frozen contract preparation programs.
Its ideal rotation interpolant is normalized-endpoint shortest-arc SLERP. The
separately identified destination approximates that interpolant by a controlled
normalized chord; its complete error is an explicit certificate term.
"""
from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_right
import copy
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import struct
from typing import Any

from .profile_capabilities import BUDGET_PROFILE, EXTRUSION_PROFILE, HOLES_PROFILE, RING_LOFT_PROFILE, EXECUTION_PROFILES, REACH_PROFILES


REACH_TARGET = "ontokin.glb/0.6"
CLOCK_CONVERSION = "binary32_rne_ties_to_even_from_exact_rational"
MAX_CERTIFICATES = 100000
MAX_ARITHMETIC_BITS = 32768
# Strict rational lower bound on pi/4, also below the schema's binary64 maximum.
ANGULAR_STEP = Fraction(0.7853981633974483)
DESTINATION_NAME = "ontokin-controlled-three-recording"
DESTINATION_VERSION = "0.1.0"
DESTINATION_COMPONENT_LIMIT = Fraction(1 << 400)
NORMALIZATION_ERROR = Fraction(1, 1 << 51)
# The .07 writer publishes wider error enclosures than the production kernel's
# actual-anchor bounds. An independent reader propagates intervals, including
# an incoming vector error on every component, so its error-width minimum can
# exceed the production minimum by more than a rounding ULP. Derivative bounds
# describe physical magnitudes and receive a separate small relative reserve.
# These finite reserves only increase upper bounds. They do not guarantee that
# arbitrary histories become deliverable: the unchanged reader still proves
# every supplied minimum and every complete inequality at the fixed tolerance.
BUDGET_SOURCE_ERROR_RESERVE = Fraction(2)
BUDGET_DERIVATIVE_RESERVE = Fraction((1 << 48) + 1, 1 << 48)


class _LocalArithmeticWork:
    """Bound standalone helper calls; production supplies its inherited work."""
    def __init__(self):
        self.operations = 0

    def charge(self, kind="recording_arithmetic"):
        if self.operations >= 100000:
            _fail("OKE-E-NUMERIC-BUDGET", "Recording arithmetic exhausted its operation bound.",
                  kind="resource", details={"max_operations": 100000})
        self.operations += 1

    def guard_bits(self, width):
        if width > MAX_ARITHMETIC_BITS:
            _fail("OKE-E-NUMERIC-BUDGET", "Recording arithmetic exceeds its finite operand bound.",
                  kind="resource", details={"max_operand_bits": MAX_ARITHMETIC_BITS})

    def guard(self, *values):
        for value in values:
            self.guard_bits(max(value.numerator.bit_length(), value.denominator.bit_length())
                            if isinstance(value, Fraction) else value.bit_length())


def _arithmetic_work(work):
    return _LocalArithmeticWork() if work is None else work


def _reuse(work, key, calculate):
    """Reuse immutable arithmetic in the same bounded request cache.

    Callers validate and bound every input before building a key. The shared
    cache charges its lookup, promotion, insertion and eviction, including the
    original cancellation callback. Standalone protocol implementations without
    a cache still execute the same arithmetic directly.
    """
    if not hasattr(work, "lookup") or not hasattr(work, "remember"):
        return calculate()
    key = ("reach_recording_arithmetic_v1", *key)
    result = work.lookup(key)
    if result is None:
        result = calculate()
        work.remember(key, result)
    return result


def _charge(work=None, kind="recording_arithmetic"):
    if work is not None:
        work.charge(kind)


def _guard(value: Fraction, work=None):
    if work is not None:
        work.guard(value)
    elif max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_ARITHMETIC_BITS:
        _fail("OKE-E-NUMERIC-BUDGET", "Recording arithmetic exceeds its finite operand bound.",
              kind="resource", details={"max_operand_bits": MAX_ARITHMETIC_BITS})


def _guard_bits(width, work):
    work.guard_bits(width)


def _rational(value, work):
    _charge(work, "recording_decode")
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise ValueError("Recording arithmetic requires an exact or finite numeric value")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Recording arithmetic requires finite operands")
        # Every finite binary64 decoder fits within 1075 bits.
        work.guard_bits(1075)
    else:
        if isinstance(value, int):
            work.guard_bits(value.bit_length())
        work.guard(value)
    result = Fraction(value)
    _guard(result, work)
    return result


def _exact(left, right, operation, work):
    _charge(work, "recording_exact_" + operation)
    work.guard(left, right)
    an, ad = left.numerator.bit_length(), left.denominator.bit_length()
    bn, bd = right.numerator.bit_length(), right.denominator.bit_length()
    if operation in {"add", "sub"}:
        width = max(an + bd, bn + ad, ad + bd) + 1
    elif operation == "mul":
        width = max(an + bn, ad + bd)
    elif operation == "div":
        if not right:
            raise ZeroDivisionError("Zero exact recording divisor")
        width = max(an + bd, ad + bn)
    else:
        raise ValueError("Unknown recording arithmetic operation")
    _guard_bits(width, work)
    result = {"add": Fraction.__add__, "sub": Fraction.__sub__,
              "mul": Fraction.__mul__, "div": Fraction.__truediv__}[operation](left, right)
    _guard(result, work)
    return result


def _compare(left, right, work):
    _charge(work, "recording_exact_compare")
    work.guard(left, right)
    _guard_bits(max(left.numerator.bit_length() + right.denominator.bit_length(),
                    right.numerator.bit_length() + left.denominator.bit_length()), work)
    return (left > right) - (left < right)


def _sum(values, work):
    total = Fraction(0)
    for value in values:
        total = _exact(total, value, "add", work)
    return total


def _vector(values, work, *, size=None):
    result = []
    for index, value in enumerate(values):
        _charge(work, "recording_vector_component")
        if index >= (4 if size is None else size):
            raise ValueError("Recording arithmetic vector exceeds its fixed dimension")
        result.append(_rational(value, work))
    if size is not None and len(result) != size:
        raise ValueError("Recording arithmetic vector has the wrong dimension")
    return tuple(result)


def _shift(value, amount, work):
    _charge(work, "recording_integer_shift")
    work.guard_bits(value.bit_length())
    work.guard(value)
    if type(amount) is not int or amount < 0:
        raise ValueError("An integer left shift requires a nonnegative count")
    _guard_bits(value.bit_length() + amount, work)
    return value << amount


def _integer_sqrt(value, work):
    _charge(work, "recording_integer_sqrt")
    work.guard_bits(value.bit_length())
    work.guard(value)
    result = math.isqrt(value)
    _charge(work, "recording_integer_sqrt_return")
    return result


def _fail(code, message, *, model=None, kind="numeric", details=None):
    # Lazy import keeps scene's explicit adapter dispatch acyclic.
    from .scene import export_error
    export_error(code, message, model, kind=kind, details=details)


def _floor_log2_ratio(n: int, d: int, work) -> int:
    _charge(work, "recording_binary_exponent")
    work.guard(n, d)
    exponent = n.bit_length() - d.bit_length()
    if (n < _shift(d, exponent, work)) if exponent >= 0 else (_shift(n, -exponent, work) < d):
        exponent -= 1
    return exponent


def _nearest_even(n: int, d: int, work) -> int:
    _charge(work, "recording_integer_round")
    work.guard(n, d)
    _guard_bits(max(n.bit_length(), d.bit_length()) + 1, work)
    q, remainder = divmod(n, d)
    twice = remainder * 2
    _charge(work, "recording_integer_round_return")
    return q + int(twice > d or (twice == d and q & 1))


def rational_record(value, *, work=None) -> dict[str, str]:
    work = _arithmetic_work(work)
    value = _rational(value, work)
    if value < 0:
        raise ValueError("A recording clock must be nonnegative")
    # Fixed-size chunks avoid interpreter-wide integer-string limits and keep
    # every division/cancellation checkpoint within this request's work.
    def decimal(integer):
        chunks = []
        while integer:
            _charge(work, "recording_decimal_chunk")
            integer, remainder = divmod(integer, 1_000_000_000)
            chunks.append(remainder)
        _charge(work, "recording_decimal_result")
        if not chunks:
            return "0"
        return str(chunks[-1]) + "".join(f"{chunk:09d}" for chunk in reversed(chunks[:-1]))
    return {"numerator": decimal(value.numerator), "denominator": decimal(value.denominator)}


def _interval_clock_record(value, *, work):
    """Reuse completed decimal digits for repeated exact interval widths.

    Authored keys keep their ordinary single-use serialization. Widths recur
    throughout one phase, so their immutable digit pair can use the same
    bounded request cache as other completed pure calculations. Each row gets
    a fresh dictionary and the original decoder/guard still runs on every use.
    """
    if not hasattr(work, "lookup") or not hasattr(work, "remember"):
        return rational_record(value, work=work)
    while True:
        exact = _rational(value, work)
        if exact < 0:
            raise ValueError("A recording clock must be nonnegative")
        cap = work.max_operand_bits
        key = ("reach_interval_clock_digits_v1", cap, exact)
        digits = work.lookup(key)
        if work.max_operand_bits != cap:
            continue
        if digits is None:
            record = rational_record(exact, work=work)
            digits = (record["numerator"], record["denominator"])
            if work.max_operand_bits != cap:
                continue
            work.remember(key, digits)
            if work.max_operand_bits != cap:
                continue
        return {"numerator": digits[0], "denominator": digits[1]}


def direct_binary32(value, *, work=None, model=None) -> tuple[float, str]:
    """Round a nonnegative exact clock directly to binary32, including ties.

    No binary64 intermediate participates in choosing the stored bits. The
    final unpack only exposes the already selected binary32 value to Python.
    """
    work = _arithmetic_work(work)
    _charge(work, "clock_conversion")
    value = _rational(value, work)
    if value < 0:
        _fail("OKE-E-CLOCK", "A recorded clock must be nonnegative.", model=model)
    if not value:
        return 0.0, "00000000"
    exponent = _floor_log2_ratio(value.numerator, value.denominator, work)
    if exponent > 127:
        _fail("OKE-E-FLOAT32", "The exact clock rounds outside finite binary32.", model=model)
    shift = 149 if exponent < -126 else 23 - exponent
    numerator, denominator = value.numerator, value.denominator
    if shift >= 0:
        numerator = _shift(numerator, shift, work)
    else:
        denominator = _shift(denominator, -shift, work)
    significand = _nearest_even(numerator, denominator, work)
    if exponent < -126:
        bits = significand
    else:
        if significand == 1 << 24:
            significand >>= 1
            exponent += 1
        if exponent > 127:
            _fail("OKE-E-FLOAT32", "The exact clock rounds outside finite binary32.", model=model)
        bits = ((exponent + 127) << 23) | (significand - (1 << 23))
    return struct.unpack("<f", struct.pack("<I", bits))[0], f"{bits:08x}"


def upper_binary64(value, *, work=None, model=None) -> float:
    """Expose a nonnegative rational upper bound without rounding it down."""
    work = _arithmetic_work(work)
    value = _rational(value, work)
    if value < 0:
        raise ValueError("A certificate upper bound cannot be negative")
    if not value and getattr(work, "max_operand_bits", MAX_ARITHMETIC_BITS) == MAX_ARITHMETIC_BITS:
        # The freshly admitted exact zero already has the canonical finite
        # binary64 image. No conversion, ordering or cache operation is needed.
        # Narrow domains retain the complete original conversion preflights.
        return 0.0
    def calculate():
        try:
            result = float(value)
        except OverflowError:
            result = math.inf
        _charge(work, "recording_bound_float_return")
        if math.isfinite(result) and _compare(_rational(result, work), value, work) < 0:
            _charge(work, "recording_bound_nextafter")
            result = math.nextafter(result, math.inf)
        if not math.isfinite(result):
            _fail("OKE-E-NUMERIC-BOUND", "A proved bound exceeds finite report precision.", model=model)
        return result
    return _reuse(work, ("upper_binary64", value), calculate)


def sqrt_upper(value, *, work=None, bits=96) -> Fraction:
    """An outward dyadic square-root bound obtained solely by integer isqrt."""
    work = _arithmetic_work(work)
    value = _rational(value, work)
    _charge(work, "recording_sqrt_precision")
    if type(bits) is not int or not 0 <= bits <= 1536:
        raise ValueError("The recording square-root precision must be within the finite schedule extent")
    if value < 0:
        raise ValueError("Negative square root")
    scaled_numerator = _shift(value.numerator, 2 * bits, work)
    _charge(work, "recording_sqrt_quotient")
    root = _integer_sqrt(scaled_numerator // value.denominator, work)
    _guard_bits(2 * root.bit_length() + value.denominator.bit_length(), work)
    _charge(work, "recording_sqrt_exactness")
    return Fraction(root + int(root * root * value.denominator < scaled_numerator), _shift(1, bits, work))


def norm_upper(values, *, work=None) -> Fraction:
    work = _arithmetic_work(work)
    values = _vector(values, work)
    return _reuse(work, ("norm_upper", values), lambda: sqrt_upper(
        _sum((_exact(value, value, "mul", work) for value in values), work), work=work))


def normalized_component(component, squared_norm, *, work=None) -> float:
    """Correctly rounded component/sqrt(norm2), with an exact midpoint test."""
    work = _arithmetic_work(work)
    _charge(work, "destination_normalization")
    component, squared_norm = _rational(component, work), _rational(squared_norm, work)
    if squared_norm <= 0:
        _fail("OKE-E-QUATERNION", "A stored quaternion must have positive finite norm.")
    if not component:
        return 0.0
    square = _exact(_exact(component, component, "mul", work), squared_norm, "div", work)
    if _compare(square, Fraction(1), work) > 0:
        raise ValueError("Component exceeds the supplied squared norm")
    exponent = _floor_log2_ratio(square.numerator, square.denominator, work) // 2
    shift = 1074 if exponent < -1022 else 52 - exponent
    numerator = _shift(square.numerator, 2 * shift, work)
    denominator = square.denominator
    _charge(work, "recording_sqrt_quotient")
    q = _integer_sqrt(numerator // denominator, work)
    midpoint_left = _shift(numerator, 2, work)
    _guard_bits(denominator.bit_length() + 2 * (q.bit_length() + 2), work)
    _charge(work, "recording_sqrt_midpoint")
    midpoint_right = denominator * (2 * q + 1) ** 2
    if midpoint_left > midpoint_right or (midpoint_left == midpoint_right and q & 1):
        q += 1
    answer = math.ldexp(float(q), -shift)
    _charge(work, "recording_normalization_return")
    return -answer if component < 0 and answer else answer


def normalized_quaternion(values, *, work=None) -> tuple[float, ...]:
    work = _arithmetic_work(work)
    values = _vector(values, work, size=4)
    def calculate():
        squared = _sum((_exact(value, value, "mul", work) for value in values), work)
        if not squared:
            _fail("OKE-E-QUATERNION", "A zero quaternion has no normalized interpretation.")
        return tuple(normalized_component(value, squared, work=work) for value in values)
    return _reuse(work, ("normalized_quaternion", values), calculate)


def quaternion_arc_upper(first, last, *, work=None) -> Fraction:
    """Bound the S^3 short arc, not the doubled SO(3) rotation angle."""
    work = _arithmetic_work(work)
    raw_first, raw_last = _vector(first, work, size=4), _vector(last, work, size=4)
    dot = _sum((_exact(a, b, "mul", work) for a, b in zip(raw_first, raw_last)), work)
    if dot < 0:
        _fail("OKE-E-QUATERNION-LIFT", "Stored quaternions must retain one coherent short lift.")
    a, b = normalized_quaternion(raw_first, work=work), normalized_quaternion(raw_last, work=work)
    chord = norm_upper((_exact(_rational(x, work), _rational(y, work), "sub", work)
                        for x, y in zip(a, b)), work=work)
    chord = _exact(chord, _exact(Fraction(2), NORMALIZATION_ERROR, "mul", work), "add", work)
    if _compare(chord, Fraction(1, 2), work) > 0:
        _fail("OKE-E-ROTATION-ALIAS", "The normalized endpoint chord exceeds the proved short-arc range.")
    # 2 asin(d/2) <= d/sqrt(1-d*d/4) <= d/(1-d*d/4).
    arc = _exact(chord, _exact(Fraction(1), _exact(_exact(chord, chord, "mul", work),
                 Fraction(4), "div", work), "sub", work), "div", work)
    if _compare(arc, ANGULAR_STEP, work) > 0:
        _fail("OKE-E-ROTATION-ALIAS", "The stored quaternion arc exceeds pi/4.")
    return arc


def controlled_destination_sample(first_position, last_position, first_quaternion,
                                  last_quaternion, amount, *, work=None):
    """Reference port of the identified destination's integer interpolation.

    This function is additional playback checking. Its samples do not establish
    the continuous certificate, whose algebraic terms are computed separately.
    """
    work = _arithmetic_work(work)
    amount = _rational(amount, work)
    amount = Fraction(0) if _compare(amount, Fraction(0), work) < 0 else amount
    amount = Fraction(1) if _compare(amount, Fraction(1), work) > 0 else amount
    complement = _exact(Fraction(1), amount, "sub", work)
    a, b = normalized_quaternion(first_quaternion, work=work), normalized_quaternion(last_quaternion, work=work)
    a, b = _vector(a, work, size=4), _vector(b, work, size=4)
    if _sum((_exact(x, y, "mul", work) for x, y in zip(a, b)), work) < 0:
        _charge(work, "recording_quaternion_sign")
        b = tuple(-value for value in b)
    first_position, last_position = _vector(first_position, work, size=3), _vector(last_position, work, size=3)
    interpolate = lambda x, y: _exact(_exact(complement, x, "mul", work), _exact(amount, y, "mul", work), "add", work)
    position_values = tuple(interpolate(x, y) for x, y in zip(first_position, last_position))
    position = []
    for value in position_values:
        _charge(work, "recording_translation_round")
        result = float(value)
        _charge(work, "recording_translation_round_return")
        if not math.isfinite(result):
            _fail("OKE-E-NUMERIC-BOUND", "A destination position is not finite.")
        position.append(0.0 if result == 0 else result)
    chord = tuple(interpolate(x, y) for x, y in zip(a, b))
    return tuple(position), normalized_quaternion(chord, work=work)


def destination_numeric_bounds(arc, translation_magnitude, radius, vertex_error,
                               *, work=None) -> tuple[Fraction, Fraction]:
    """Uniform actual destination error, including nonorthogonal matrix error."""
    work = _arithmetic_work(work)
    _charge(work, "destination_bound")
    arc, magnitude, radius, vertex_error = tuple(_rational(v, work) for v in
                                                (arc, translation_magnitude, radius, vertex_error))
    if any(v < 0 for v in (arc, magnitude, radius, vertex_error)) or _compare(arc, ANGULAR_STEP, work) > 0:
        _fail("OKE-E-NUMERIC-BOUND", "Destination operands exceed the proved range.")
    extent = _sum((magnitude, radius, vertex_error), work)
    if _compare(extent, DESTINATION_COMPONENT_LIMIT, work) > 0:
        _fail("OKE-E-NUMERIC-BOUND", "Destination magnitude exceeds its finite arithmetic proof.")
    # Exact-endpoint normalized chord vs SLERP plus correctly rounded unit
    # component errors. Matrix defect and matrix/vector rounding are positional.
    rotation = _exact(_exact(arc, arc, "mul", work), Fraction(1, 1 << 44), "add", work)
    position = _exact(_exact(extent, Fraction(1), "add", work), Fraction(1 << 38), "div", work)
    return position, rotation


@dataclass(frozen=True)
class MotionBound:
    speed: Fraction
    acceleration: Fraction
    angular_speed: Fraction


@dataclass(frozen=True)
class ReachPhase:
    start: Fraction
    end: Fraction
    carriers: dict[str, MotionBound]
    source: dict[str, Any] | None = None
    recording_angular_proof: Any = None


@dataclass
class ReachPrefixPlan:
    boundaries: tuple[Fraction, ...]
    phases: tuple[ReachPhase, ...]
    phase_states: tuple[Any, ...]
    final_state: Any
    boundary_records: tuple[dict[str, Any], ...]
    simulator: Any


def recording_stage(name, *, work=None, check=None):
    """A real cooperative stage boundary, also observable by cancellation tests."""
    if work is not None:
        work.charge("recording_stage_" + name)
    elif check is not None:
        check()


def reach_profile_metadata(profile="planar-reach-0.1"):
    if profile not in REACH_PROFILES:
        raise ValueError("Unsupported recorded reach source profile")
    return {"schema_version": "ontokin.reach-recording/0.1", "source_profile": profile,
            "motion_model": "two_prescribed_planar_hinges", "rotation_interpolation": "shortest_arc_slerp",
            "goal_residual_max_m": 1e-9, "bound_chain_tuple_max": 32,
            "named_reach_action_max": 128, "live_solver_embedded": False}


def _boundary_record(time, before, after, incoming):
    from .evaluator import time_text
    result = {"source_seconds": time_text(time), "incoming_releases": incoming}
    for side, sample in (("before", before), ("after", after)):
        result["joint_states_" + side] = sample["joints"]
        result["action_states_" + side] = sample["actions"]
        result["pose_authorities_" + side] = {path: value["pose_authority"] for path, value in sample["objects"].items()}
        result["impulse_states_" + side] = {path: value["impulses"] for path, value in sample["objects"].items()}
        result["force_states_" + side] = {path: value["forces"] for path, value in sample["objects"].items()}
        result["reach_states_" + side] = sample["reaches"]
    return result


class _PrefixFrameSelection:
    """One prefix's structural carrier list without numerical memoization."""

    def __init__(self):
        self.owner = self.inputs = self.frames = None

    def selected(self, simulator):
        model, work = simulator.model, simulator.work
        # Reuse construction and deduplication of the same ordered identities.
        # The phase walk below still checks every actual source occurrence.
        if self.owner is not None and self.owner[0] is model and self.owner[1] is work:
            _charge(work, "recording_phase_selection_reuse")
            model, work = simulator.model, simulator.work
            inputs = (tuple(model.objects), tuple(joint.parent for joint in model.joints.values()))
            if (inputs == self.inputs and self.owner[0] is simulator.model
                    and self.owner[1] is simulator.work):
                return self.frames
        selected, seen, parents, objects = [], set(), [], []
        for path in model.objects:
            _charge(work, "recording_phase_frame")
            objects.append(path)
            frame = path + ".frame"
            selected.append(frame)
            seen.add(frame)
        for joint in model.joints.values():
            _charge(work, "recording_phase_frame")
            parents.append(joint.parent)
            frame = joint.parent + ".frame"
            if frame not in seen:
                selected.append(frame)
                seen.add(frame)
        inputs = (tuple(objects), tuple(parents))
        # A cold construction also contains callbacks. Do not publish a mixed
        # selection if one of them changed an earlier identity or either owner.
        if (model is not simulator.model or work is not simulator.work
                or inputs != (tuple(model.objects), tuple(joint.parent for joint in model.joints.values()))):
            return self.selected(simulator)
        self.owner, self.inputs, self.frames = (model, work), inputs, tuple(selected)
        return self.frames


def _boundary_state_contents(state, *, work=None):
    """Bounded exact operands for an already validated static endpoint.

    Only known plain records are eligible. The final callback-free comparison
    detects mutation of an earlier field by a later checkpoint callback.
    """
    from .evaluator import _ImpulseState
    from .force_runtime import _ActiveForce, _ForceState
    from .model import ForcePayload, ReachPayload, ReachSourceLocation
    from .reach_kinematics import PlanarSolution
    from .reach_phase import AnchorError
    from .reach_pose import RotationValue
    from .reach_runtime import _ReachActionState, _ReachRunState

    records = (_ReachRunState, _ReachActionState, _ImpulseState, _ForceState,
               _ActiveForce, ForcePayload, PlanarSolution, RotationValue, AnchorError,
               ReachPayload, ReachSourceLocation)
    visited, active = 0, set()

    class Ineligible(Exception):
        pass

    def freeze(value, depth=0):
        nonlocal visited
        visited += 1
        if visited > 16384 or depth > 32:
            raise Ineligible
        if work is not None and visited % 128 == 1:
            _charge(work, "recording_boundary_state_block")
            if work.max_operand_bits != MAX_ARITHMETIC_BITS:
                # A later callback cannot restore a domain and thereby hide
                # the fact that this receipt crossed a narrowed domain.
                raise Ineligible
        kind = type(value)
        if value is None or kind in (str, bool):
            if kind is str and len(value) > 4096:
                raise Ineligible
            return kind, value
        if kind is int:
            if value.bit_length() > MAX_ARITHMETIC_BITS:
                raise Ineligible
            return kind, value
        if kind is float:
            if not math.isfinite(value):
                raise Ineligible
            return kind, struct.pack(">d", value)
        if kind is Fraction:
            if max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_ARITHMETIC_BITS:
                raise Ineligible
            return kind, value.numerator, value.denominator
        if kind in records:
            return kind, freeze(vars(value), depth + 1)
        if kind not in (dict, list, tuple, set) or len(value) > 16384 - visited:
            raise Ineligible
        if id(value) in active:
            raise Ineligible
        active.add(id(value))
        try:
            if kind is dict:
                return kind, tuple((freeze(key, depth + 1), freeze(child, depth + 1))
                                   for key, child in tuple(value.items()))
            if kind is set:
                if any(type(item) is not str for item in value):
                    raise Ineligible
                values = sorted(value)
            else:
                values = tuple(value)
            return kind, tuple(freeze(item, depth + 1) for item in values)
        finally:
            active.remove(id(value))

    try:
        return freeze(state)
    except Ineligible:
        return None


def _boundary_projection_model(model, *, work=None):
    """Bind every source operand and identity used by retained projections."""
    from .model import ActionModel, FollowModel, JointModel, ObjectModel, Pose, SceneModel, SiteModel

    if type(model) is not SceneModel:
        return None
    collections = ((model.objects, ObjectModel), (model.sites, SiteModel),
                   (model.joints, JointModel), (model.follows, FollowModel), (model.actions, ActionModel))
    if (any(type(values) is not dict or len(values) > 4096 for values, _ in collections)
            or sum(len(values) for values, _ in collections) > 4096):
        return None
    if any(type(value) is not kind for values, kind in collections for value in values.values()):
        return None
    if (any(type(obj.physical) is not dict for obj in model.objects.values())
            or any(type(site.pose) is not Pose for site in model.sites.values())
            or any(type(follow.offset) is not Pose for follow in model.follows.values())):
        return None

    def pose(value):
        return value.frame, value.position, value.rotation

    values = (
        model.module_name, model.module_key, model.scene_name, model.scene_key, model.profile,
        model.program_revision, model.duration, model.gravity, model.source_provenance,
        tuple((path, obj.path, obj.owner, obj.element_id, obj.mass) for path, obj in model.objects.items()),
        tuple((path, site.path, site.element_id, site.owner, pose(site.pose))
              for path, site in model.sites.items()),
        tuple((path, joint.path, joint.element_id, joint.kind, joint.parent, joint.child,
               joint.axis, joint.limits, joint.initial) for path, joint in model.joints.items()),
        tuple((path, follow.path, follow.parent, follow.child, pose(follow.offset))
              for path, follow in model.follows.items()),
        tuple((path, action.path, action.element_id, action.kind, action.target,
               action.duration, action.vector, action.goal, action.reach) for path, action in model.actions.items()))
    return _boundary_state_contents(values, work=work)


class _UnchangedBoundaryProjection:
    """One private before output, reusable only across no actual transition."""

    @staticmethod
    def owners(simulator):
        return (simulator.model, simulator.work, simulator.pose_ops, simulator.pose_ops.work,
                simulator.state, simulator.check, simulator.work.external_check)

    @staticmethod
    def scope(simulator):
        from . import force_runtime
        return (simulator.context_kind, simulator.work.max_operand_bits, force_runtime.MAX_OUTPUT_RECORDS,
                force_runtime.MAX_JSON_BYTES, simulator.event_index, simulator.zero_pending,
                simulator.last_boundary, tuple(simulator.boundaries))

    @classmethod
    def capture(cls, simulator):
        from .reach_runtime import _ReachRunState

        if (type(simulator.state) is not _ReachRunState or simulator.state.dynamic
                or simulator._pending_reach_output is not None
                or simulator.work.max_operand_bits != MAX_ARITHMETIC_BITS):
            return None
        result = cls()
        result.owner = simulator
        result.bindings = cls.owners(simulator)
        result.domain = cls.scope(simulator)
        result.contents = _boundary_state_contents(simulator.state, work=simulator.work)
        if result.contents is None:
            return None
        result.source = _boundary_projection_model(simulator.model, work=simulator.work)
        if result.source is None or not result.matches(check=False):
            return None
        return result

    def matches(self, *, check):
        from .reach_runtime import _ReachRunState

        simulator = self.owner
        if (type(simulator.state) is not _ReachRunState
                or any(old is not current for old, current in zip(self.bindings, self.owners(simulator)))
                or self.domain != self.scope(simulator) or simulator.state.dynamic
                or simulator._pending_reach_output is not None):
            return False
        contents = _boundary_state_contents(simulator.state, work=simulator.work if check else None)
        if contents is None:
            return False
        source = _boundary_projection_model(simulator.model, work=simulator.work if check else None)
        # No callback occurs between the final reads and comparisons. A later
        # checkpoint cannot hide mutation of an already visited source field.
        return (contents == self.contents and source == self.source and self.domain == self.scope(simulator)
                and all(old is current for old, current in zip(self.bindings, self.owners(simulator)))
                and (not check or (contents == _boundary_state_contents(simulator.state)
                    and source == _boundary_projection_model(simulator.model))))

    def after(self, before, time, *, objects):
        from .evaluator import time_text

        simulator = self.owner
        _charge(simulator.work, "recording_boundary_projection_guard")
        if (type(before) is not dict or before.get("side") != "before"
                or before.get("time_seconds") != time_text(time) or not self.matches(check=True)):
            return None
        # The full after materializer copies and counts every occurrence.
        # Retain the freshly checked object/force/impulse histories supplied by
        # recording_boundary; only unchanged joint/action/reach work is shared.
        reaches = {}
        for path, projection in before["reaches"].items():
            _charge(simulator.work, "recording_boundary_side")
            current = projection["current"]
            if current["available"]:
                value = current["value"]
                observation = {**value["observation"], "side": "after"}
                current = {**current, "value": {**value, "observation": observation}}
            reaches[path] = {**projection, "current": current}
        result = simulator._snapshot_data({**before, "side": "after", "objects": objects,
                                           "reaches": reaches}, time, "after")
        return result if self.matches(check=True) else None


def recording_phase_bounds(simulator, start, end, *, recording_proof=False, state=None):
    """Prove every deliverable carrier and its complete source dependencies.

    A carrier certificate includes every local vertex/site through its geometry
    radius. An unused site's separate world-frame bound is not another delivered
    carrier. Include every object and every possible joint-parent helper even
    after release, so the same retained plan supports either helper setting.
    Complete source boundary evaluation remains outside this narrower proof map.
    """
    from .reach_numeric import ReachAdmissionError
    from .reach_phase import phase_bounds

    try:
        selector = getattr(simulator, "_recording_frame_selection", None)
        if selector is None:
            selector = _PrefixFrameSelection()
        selected = selector.selected(simulator)
        # The ordinary exact phase traversal still follows all required
        # site/ownership/joint paths and prepares every root's spin plan.
        result = phase_bounds(simulator, start, end, state, selected_frames=selected,
                              recording_proof=recording_proof)
        return ((result["frames"], result["recording_angular_proof"]) if recording_proof
                else result["frames"])
    except ReachAdmissionError as error:
        simulator._numeric_error(error, time=Fraction(start))


def reach_prefix_plan(model, end, *, work) -> ReachPrefixPlan:
    """Validate the requested prefix once and retain bounded phase anchors.

    No event after end is evaluated. States are retained only after the complete
    boundary-history forecast passes; immutable numeric cache values stay owned
    by this same request. Baking later reads these validated phases directly.
    """
    from .reach_runtime import ReachSimulator, _BoundaryHistoryPreflight
    from .scene import MAX_KEYFRAMES

    class PlanningSimulator(ReachSimulator):
        def _check_object_pose(self, pose):
            # H06 retains authority/history rather than every object's p/q/v/w
            # tuples. Prove unused fields admissible without allocating them;
            # observations and release anchors still use their normal getters.
            self.pose_ops.ensure_finite(pose)

        def snapshot(self, time, side):
            self._kinematics(time, self.state)
            return {}

    recording_stage("planning", work=work)
    simulator = PlanningSimulator(model, work=work)
    simulator._recording_frame_selection = _PrefixFrameSelection()
    history = _BoundaryHistoryPreflight(model, horizon=end, check=work.tick)
    times, phases, states, records = [], [], [], []
    time = Fraction(0)
    endpoint_without_transition = False
    while True:
        _charge(work, "recording_boundary_preflight")
        if len(times) >= MAX_KEYFRAMES:
            _fail("OKE-E-KEYFRAME-BUDGET", "Semantic boundaries exceed the recording key budget.", model=model, kind="resource")
        history.append(time)
        simulator.advance(time, "before")
        reuse = (_UnchangedBoundaryProjection.capture(simulator)
                 if endpoint_without_transition else None)
        before = simulator.recording_boundary(time, "before")
        if reuse is not None and not reuse.matches(check=False):
            reuse = None
        simulator.advance(time, "after")
        if reuse is None:
            after = simulator.recording_boundary(time, "after")
        else:
            after = simulator.recording_boundary(time, "after", _reuse=(reuse, before))
        records.append(_boundary_record(time, before, after, simulator.incoming_releases_at(time)))
        times.append(time)
        if time == end:
            break
        following = simulator._next_boundary()
        stop = end if following is None or following > end else following
        endpoint_without_transition = following is None or following > end
        if stop <= time:
            _fail("OKE-E-PHASE-COVERAGE", "The validated prefix did not advance to a later boundary.", model=model)
        recording_stage("planning_phase", work=work)
        source, angular_proof = recording_phase_bounds(simulator, time, stop, recording_proof=True)
        carriers = {path: MotionBound(value.carrier_speed_upper_m_per_s,
                                     value.carrier_acceleration_upper_m_per_s2,
                                     value.angular_speed_upper_rad_per_s)
                    for path, value in source.items()}
        phases.append(ReachPhase(time, stop, carriers, source, angular_proof))
        states.append(copy.deepcopy(simulator.state))
        time = stop
    return ReachPrefixPlan(tuple(times), tuple(phases), tuple(states), copy.deepcopy(simulator.state),
                           tuple(records), simulator)


def _ceil(value):
    value = Fraction(value)
    return -(-value.numerator // value.denominator)


def _ceil_sqrt(value):
    value = Fraction(value)
    root = math.isqrt(value.numerator // value.denominator)
    return root + int(root * root * value.denominator < value.numerator)


def node_geometry_bounds(model, nodes, *, work):
    """Bound every actual source vertex and promised local site before keys."""
    from .scene import float32
    result = []
    for node in nodes:
        _charge(work, "recording_geometry_bound")
        radius = Fraction(0)
        error_axes = [Fraction(0)] * 3
        positions = () if node.mesh is None else node.mesh.positions
        for index, point in enumerate(positions):
            if index % 128 == 0:
                _charge(work, "recording_vertex_block")
            radius = max(radius, sum(map(lambda x: abs(Fraction(x)), point), Fraction(0)))
            for axis, value in enumerate(point):
                error_axes[axis] = max(error_axes[axis], abs(Fraction(float32(value, model)) - Fraction(value)))
        if node.metadata["kind"] == "object":
            path = node.metadata["path"]
            for site in model.sites.values():
                if site.owner == path:
                    radius = max(radius, sum((abs(Fraction(x)) for x in site.pose.position), Fraction(0)))
        result.append((radius, norm_upper(error_axes, work=work)))
    return tuple(result)


def reach_timeline(model, options, plan, nodes, geometry_bounds, *, work):
    """Plan exact rational keys before allocating any baked pose array."""
    from .scene import MAX_KEYFRAMES, MAX_BAKED_POSES
    maximum = min(MAX_KEYFRAMES, MAX_BAKED_POSES // max(1, len(nodes)),
                  MAX_CERTIFICATES // max(1, len(nodes)) + 1)
    if len(plan.boundaries) > maximum:
        _fail("OKE-E-CERTIFICATE-BUDGET", "Required boundaries exceed simultaneous key/pose/certificate budgets.", model=model, kind="resource")
    position_tolerance, rotation_tolerance = Fraction(options.position_tolerance_m), Fraction(options.rotation_tolerance_rad)
    subdivisions, count = [], 1
    for phase in plan.phases:
        _charge(work, "recording_subdivision_plan")
        width = phase.end - phase.start
        steps = max(1, _ceil(width * Fraction(options.fps)))
        for node, (radius, _) in zip(nodes, geometry_bounds):
            bound = phase.carriers[node.frame_path]
            # Meet the adopted quarter-allocation inequalities directly. The
            # complete outward-rounded certificate below still checks source,
            # destination, endpoint and clock errors against the full limits.
            curvature = bound.acceleration / 8 + radius * bound.angular_speed ** 2 / 4
            steps = max(steps, _ceil(width * bound.angular_speed / ANGULAR_STEP),
                        _ceil_sqrt(width ** 2 * bound.angular_speed ** 2 / rotation_tolerance),
                        _ceil_sqrt(width ** 2 * curvature * 4 / position_tolerance))
        count += steps
        if count > maximum:
            _fail("OKE-E-KEYFRAME-BUDGET", "The bounded motion requires too many retained recording keys.",
                  model=model, kind="resource", details={"required_keys": count, "maximum_keys_for_scene": maximum})
        subdivisions.append(steps)
    semantic = set(plan.boundaries)
    authored = [plan.boundaries[0]]
    for phase, steps in zip(plan.phases, subdivisions):
        for index in range(1, steps + 1):
            _charge(work, "recording_key")
            authored.append(phase.start + (phase.end - phase.start) * index / steps)
    retained = []
    for time in authored:
        stored, bits = direct_binary32(time, work=work, model=model)
        if abs(Fraction(stored) - time) > Fraction(options.time_tolerance_s):
            _fail("OKE-E-TIME-PRECISION", "An exact retained clock exceeds the requested binary32 time tolerance.", model=model)
        item = {"authored_seconds": rational_record(time, work=work), "stored_seconds": stored,
                "stored_binary32_bits": bits, "semantic_boundary": time in semantic}
        if retained and stored == retained[-1]["stored_seconds"]:
            if item["semantic_boundary"] and retained[-1]["semantic_boundary"]:
                _fail("OKE-E-TIMES-COLLAPSED", "Distinct semantic boundaries collapse to one binary32 clock.", model=model)
            if item["semantic_boundary"]:
                retained[-1] = item
            continue
        if retained and stored < retained[-1]["stored_seconds"]:
            _fail("OKE-E-CLOCK", "Stored recording clocks are not strictly ordered.", model=model)
        retained.append(item)
    exact = [Fraction(int(item["authored_seconds"]["numerator"]), int(item["authored_seconds"]["denominator"]))
             for item in retained]
    if not semantic.issubset(exact):
        _fail("OKE-E-PHASE-COVERAGE", "Every semantic boundary must survive clock retention.", model=model)
    return exact, [item["stored_seconds"] for item in retained], retained


def _source_max(plan, selected, frame, field):
    return max((getattr(plan.phases[index].source[frame], field) for index in selected), default=Fraction(0))


def _recording_endpoint_excess(bound, *, work):
    """Cover bounded incremental rotations without changing source bounds.

    Each sampled hinge/spin starts with the ordinary direct kernel. Every
    subsequent cursor step contributes at most one axis-kernel error and two
    product errors. A cache miss or the fixed cursor cap reseeds directly.
    All ancestor angular errors can move a descendant origin by at most their
    sum times the existing whole-path offset bound. The certificate's separate
    radius-times-rotation term also covers every promised local point.
    """
    from .reach_pose import AXIS_ERROR, PRODUCT_ERROR
    from .scene import MAX_KEYFRAMES

    _charge(work, "recording_endpoint_recurrence_domain")
    count, offset = bound.trig_count, bound.path_offset_l1_m
    if type(count) is not int or count < 0 or type(offset) is not Fraction:
        raise ValueError("Recording endpoint recurrence requires exact nonnegative source path bounds")
    work.guard(count, offset, MAX_KEYFRAMES, AXIS_ERROR, PRODUCT_ERROR)
    if _compare(offset, Fraction(0), work) < 0:
        raise ValueError("Recording endpoint recurrence requires a nonnegative source path offset")

    def calculate():
        if not count:
            return Fraction(0), Fraction(0)
        extra_steps = _exact(Fraction(MAX_KEYFRAMES - 1), Fraction(count), "mul", work)
        step_error = _exact(AXIS_ERROR, _exact(Fraction(2), PRODUCT_ERROR, "mul", work), "add", work)
        rotation = _exact(extra_steps, step_error, "mul", work)
        position = _exact(offset, rotation, "mul", work)
        return position, rotation

    # The operands are validated before a warm lookup. A narrowed arithmetic
    # cap cannot reuse a result calculated under a larger allocation limit.
    key = ("recording_endpoint_recurrence", getattr(work, "max_operand_bits", MAX_ARITHMETIC_BITS),
           MAX_KEYFRAMES, count, offset)
    return _reuse(work, key, calculate)


def _carrier_ref(node):
    return {"path": node.name,
            "element_id": list(node.metadata.get("element_id", node.metadata.get("related_element_id", ())))}


def _stored_vector(values, model):
    from .scene import float32
    return tuple(float32(value, model) for value in values)


def _endpoint_l1(values, *, work):
    """Sum a fixed nonnegative binary64 vector without decoding exact zeros.

    These are actual conversion differences or stored component magnitudes.
    All components are checked before the sparse sum; omitted zero decodes and
    additions allocate no rational intermediate and do not affect its value.
    """
    _charge(work, "recording_endpoint_sum_domain")
    if (type(values) is not tuple or len(values) not in (3, 4)
            or any(type(value) is not float or not math.isfinite(value) or value < 0
                   for value in values)):
        raise ValueError("Endpoint magnitudes require a fixed finite nonnegative vector")
    work.guard_bits(1075)
    result = Fraction(0)
    for value in values:
        if value:
            term = _rational(value, work)
            result = _exact(result, term, "add", work) if result else term
    return result


def _position_rounding(position, model, *, work):
    def calculate():
        work.guard_bits(1075)
        stored = _stored_vector(position, model)
        error = _endpoint_l1(tuple(abs(a - b) for a, b in zip(position, stored)), work=work)
        magnitude = _endpoint_l1(tuple(abs(value) for value in stored), work=work)
        return error, magnitude
    return _reuse(work, ("endpoint_position_rounding", position), calculate)


def _quaternion_rounding(quaternion, model, *, work):
    def calculate():
        work.guard_bits(1075)
        stored = _stored_vector(quaternion, model)
        if not any(stored):
            _fail("OKE-E-QUATERNION", "A stored zero quaternion has no normalized interpretation.", model=model)
        large_norm = max(abs(value) for value in quaternion) >= .5
        if not large_norm:
            q = _vector(quaternion, work, size=4)
            squared = _sum((_exact(value, value, "mul", work) for value in q), work)
            large_norm = squared >= Fraction(1, 4)
        if large_norm:
            error = _exact(Fraction(4), _endpoint_l1(
                tuple(abs(a - b) for a, b in zip(quaternion, stored)), work=work), "mul", work)
        else:
            error = norm_upper((_exact(_rational(a, work), _rational(b, work), "sub", work)
                for a, b in zip(normalized_quaternion(q, work=work),
                                normalized_quaternion(stored, work=work))), work=work)
        return _exact(error, 2 * NORMALIZATION_ERROR, "add", work)
    return _reuse(work, ("endpoint_quaternion_rounding", quaternion), calculate)


def _endpoint_rounding(position, quaternion, model, *, work):
    """Bound conversion of one actual source endpoint, with charged reuse."""
    _charge(work, "recording_endpoint_domain")
    if (len(position) != 3 or len(quaternion) != 4
            or any(type(value) is not float or not math.isfinite(value)
                   for value in (*position, *quaternion))):
        raise ValueError("A recording endpoint requires finite binary64 pose components")
    work.guard_bits(1075)
    def calculate():
        # A finite binary64 source minus its correctly rounded binary32 value
        # is exact in binary64 (zero, or same-sign Sterbenz operands). L1 then
        # bounds Euclidean error without repeated exact squares and roots.
        # Position and rotation conversions are independent pure functions.
        # Sharing one across translated/rigid carriers retains the actual
        # endpoint tuple and every independently checked output occurrence.
        ep, magnitude = _position_rounding(position, model, work=work)
        eq = _quaternion_rounding(quaternion, model, work=work)
        return ep, eq, magnitude
    return _reuse(work, ("endpoint_rounding", position, quaternion), calculate)


def _certificate_quantities(model, bound, enclosing, radius, vertex_error,
                            nsp, nsr, width, shift, ep, eq, magnitude, *, work):
    """Pure numerical fields; caller-specific identities and clocks stay fresh."""
    ep = _exact(ep, nsp, "add", work)
    eq = _exact(eq, nsr, "add", work)
    if eq > Fraction(1, 2):
        _fail("OKE-E-NUMERIC-BOUND", "The endpoint comparison exceeds its proved local range.", model=model)
    # The ideal S^3 path length is at most angular_speed * width / 2.
    # Each endpoint's unit chord error e <= 1/2 has S^3 arc <= 2e;
    # triangle inequality therefore adds at most 4e for both endpoints.
    chord = _exact(_exact(_exact(bound.angular_speed, width, "mul", work), Fraction(2), "div", work),
                   _exact(Fraction(4), eq, "mul", work), "add", work)
    if chord > Fraction(1, 2):
        _fail("OKE-E-ROTATION-ALIAS", "The endpoint chord exceeds the proved short-arc range.", model=model)
    # The source path also bounds the endpoint chord. Apply the monotone
    # rational chord-to-arc envelope used by the independent supplied-byte
    # proof; merely bounding the true arc need not bound that outward envelope.
    arc = _exact(chord, _exact(Fraction(1), _exact(_exact(chord, chord, "mul", work),
                 Fraction(4), "div", work), "sub", work), "div", work)
    if arc > ANGULAR_STEP:
        _fail("OKE-E-ROTATION-ALIAS", "The stored quaternion arc exceeds pi/4.", model=model)
    quantities = {"landmark_radius_m": radius, "local_vertex_error_bound_m": vertex_error,
        "angular_speed_bound_rad_per_s": bound.angular_speed,
        "carrier_acceleration_bound_m_per_s2": bound.acceleration,
        "enclosing_carrier_speed_bound_m_per_s": enclosing.speed,
        "enclosing_carrier_acceleration_bound_m_per_s2": enclosing.acceleration,
        "enclosing_angular_speed_bound_rad_per_s": enclosing.angular_speed,
        "max_endpoint_time_shift_s": shift, "max_endpoint_position_error_m": ep,
        "max_endpoint_unit_quaternion_error": eq, "stored_quaternion_arc_upper_rad": arc,
        "source_numeric_position_bound_m": nsp, "source_numeric_rotation_bound_rad": nsr}
    # A consumer must be able to check the inequalities using the
    # reported upper bounds themselves. Round primitive quantities
    # outward first, then propagate those rounded values through every
    # dependent bound. Independently rounding the exact final sum can
    # otherwise make the displayed certificate fail by one ulp.
    quantities = {name: upper_binary64(value, work=work, model=model)
                  for name, value in quantities.items()}
    def q(name):
        return Fraction(quantities[name])
    # Destination bounds depend on the exposed outward-rounded primitives.
    # Computing them from the preceding exact values would be discarded here;
    # this one calculation validates and bounds the actual reported operands.
    ndp, ndr = destination_numeric_bounds(q("stored_quaternion_arc_upper_rad"), magnitude,
        q("landmark_radius_m"), q("local_vertex_error_bound_m"), work=work)
    quantities["destination_numeric_position_bound_m"] = upper_binary64(ndp, work=work, model=model)
    quantities["destination_numeric_rotation_bound_rad"] = upper_binary64(ndr, work=work, model=model)
    rounded_bound = MotionBound(bound.speed, q("carrier_acceleration_bound_m_per_s2"),
                                q("angular_speed_bound_rad_per_s"))
    rounded_enclosing = MotionBound(q("enclosing_carrier_speed_bound_m_per_s"),
        q("enclosing_carrier_acceleration_bound_m_per_s2"), q("enclosing_angular_speed_bound_rad_per_s"))
    rounded_totals = complete_interval_bounds(width=width, bound=rounded_bound,
        enclosing=rounded_enclosing, radius=q("landmark_radius_m"),
        vertex_error=q("local_vertex_error_bound_m"),
        endpoint_position_error=q("max_endpoint_position_error_m"),
        endpoint_quaternion_error=q("max_endpoint_unit_quaternion_error"),
        stored_arc=q("stored_quaternion_arc_upper_rad"), time_shift=q("max_endpoint_time_shift_s"),
        source_position_error=q("source_numeric_position_bound_m"),
        source_rotation_error=q("source_numeric_rotation_bound_rad"),
        destination_position_error=q("destination_numeric_position_bound_m"),
        destination_rotation_error=q("destination_numeric_rotation_bound_rad"), work=work)
    for name in ("unit_quaternion_difference_bound", "ideal_rotation_bound_rad", "ideal_position_bound_m",
                 "carrier_position_bound_m"):
        quantities[name] = upper_binary64(rounded_totals[name], work=work, model=model)
    quantities["total_rotation_bound_rad"] = upper_binary64(
        4 * q("unit_quaternion_difference_bound") + q("source_numeric_rotation_bound_rad")
        + q("destination_numeric_rotation_bound_rad")
        + q("enclosing_angular_speed_bound_rad_per_s") * q("max_endpoint_time_shift_s"),
        work=work, model=model)
    quantities["total_position_bound_m"] = upper_binary64(q("carrier_position_bound_m")
        + q("landmark_radius_m") * q("total_rotation_bound_rad") + q("local_vertex_error_bound_m"),
        work=work, model=model)
    return tuple(quantities.items())


class _EndpointReductionFallback(Exception):
    """A changed arithmetic domain abandons an incomplete group reduction."""


class _EndpointReductionWork:
    """Check the live full domain after every real reduction checkpoint."""

    def __init__(self, work):
        self.work = work
        self.fallback = _EndpointReductionFallback()

    def charge(self, kind):
        self.work.charge(kind)
        if getattr(self.work, "max_operand_bits", MAX_ARITHMETIC_BITS) != MAX_ARITHMETIC_BITS:
            raise self.fallback

    def guard(self, *values):
        self.work.guard(*values)

    def guard_bits(self, width):
        self.work.guard_bits(width)


def _endpoint_group_axes(nodes, keys, model, *, work):
    """Reduce actual component maxima before doing exact L1 arithmetic.

    This is bounded output-reduction state, not another numerical cache. A
    complete occurrence is admitted before its seven stored components are
    converted. Small-norm quaternions and changed/narrow domains replay the
    original complete endpoint reduction, retaining all attempted work.
    """
    if getattr(work, "max_operand_bits", MAX_ARITHMETIC_BITS) != MAX_ARITHMETIC_BITS:
        return None
    scope = _EndpointReductionWork(work)
    # Position residuals, quaternion residuals, stored position magnitudes.
    maxima = [[0.0] * 10 for _ in nodes]
    try:
        for key_index in sorted(keys):
            for node, retained in zip(nodes, maxima):
                scope.charge("recording_endpoint_group_domain")
                position = tuple(node.translations[key_index])
                quaternion = tuple(node.rotations_xyzw[key_index])
                if (len(position) != 3 or len(quaternion) != 4
                        or any(type(value) is not float or not math.isfinite(value)
                               for value in (*position, *quaternion))):
                    raise ValueError("A recording endpoint requires finite binary64 pose components")
                scope.guard_bits(1075)
                stored_position = _stored_vector(position, model)
                stored_quaternion = _stored_vector(quaternion, model)
                if not any(stored_quaternion):
                    _fail("OKE-E-QUATERNION", "A stored zero quaternion has no normalized interpretation.", model=model)
                if max(abs(value) for value in quaternion) < .5:
                    return None
                for axis, (value, stored) in enumerate(zip(position, stored_position)):
                    retained[axis] = max(retained[axis], abs(value - stored))
                    retained[axis + 7] = max(retained[axis + 7], abs(stored))
                for axis, (value, stored) in enumerate(zip(quaternion, stored_quaternion)):
                    retained[axis + 3] = max(retained[axis + 3], abs(value - stored))
        result = []
        for retained in maxima:
            position = _endpoint_l1(tuple(retained[:3]), work=scope)
            quaternion = _exact(Fraction(4), _endpoint_l1(tuple(retained[3:7]), work=scope), "mul", scope)
            quaternion = _exact(quaternion, 2 * NORMALIZATION_ERROR, "add", scope)
            magnitude = _endpoint_l1(tuple(retained[7:]), work=scope)
            result.append((position, quaternion, magnitude))
        return tuple(result)
    except _EndpointReductionFallback as error:
        if error is not scope.fallback or getattr(work, "callback_error", None) is error:
            raise
        return None


def _endpoint_group_maxima_exact(nodes, keys, model, *, work):
    """Visit adjacent carriers together while retaining each actual endpoint.

    Rigidly related carriers frequently share a quaternion at the same key.
    A carrier-major traversal can evict that conversion before the next
    carrier reaches the same key. Key-major traversal keeps the existing
    bounded numerical cache useful; only the three required maxima per
    output carrier are retained outside it.
    """
    maxima = [[Fraction(0), Fraction(0), Fraction(0)] for _ in nodes]
    for key_index in sorted(keys):
        for node, retained in zip(nodes, maxima):
            values = _endpoint_rounding(tuple(node.translations[key_index]),
                tuple(node.rotations_xyzw[key_index]), model, work=work)
            for axis, value in enumerate(values):
                retained[axis] = max(retained[axis], value)
    return tuple(tuple(values) for values in maxima)


def _endpoint_group_maxima(nodes, keys, model, *, work):
    """Cover every endpoint with a completed component or ordinary reduction."""
    keys = tuple(keys)
    if not keys:
        return _endpoint_group_maxima_exact(nodes, keys, model, work=work)
    result = _endpoint_group_axes(nodes, keys, model, work=work)
    return (_endpoint_group_maxima_exact(nodes, keys, model, work=work)
            if result is None else result)


def interval_certificates(model, options, plan, nodes, geometry_bounds, exact, times, *, work,
                          recording_excess=None):
    """Produce every row from conservative per-phase endpoint maxima.

    Every actual endpoint contributes. A group only shares arithmetic when its
    source phase and enclosing phase set agree. All coefficients are
    nonnegative, so combining endpoint/width/error maxima remains conservative
    even when those maxima occur in different rows. Coverage, identities and
    exact authored/stored clocks remain per-row data.
    """
    if (len(exact) - 1) * len(nodes) > MAX_CERTIFICATES:
        _fail("OKE-E-CERTIFICATE-BUDGET", "Complete interval certificate coverage exceeds its cap.", model=model, kind="resource")
    intervals, groups = [], {}
    for index, (left, right) in enumerate(zip(exact, exact[1:])):
        _charge(work, "recording_interval")
        s0, s1 = Fraction(times[index]), Fraction(times[index + 1])
        source_index = min(bisect_right(plan.boundaries, left) - 1, len(plan.phases) - 1)
        phase = plan.phases[source_index]
        if not phase.start <= left < right <= phase.end:
            _fail("OKE-E-PHASE-COVERAGE", "An authored key pair crosses an unretained semantic boundary.", model=model)
        selected = enclosing_phases(plan.phases, left, right, s0, s1, prefix_end=exact[-1], work=work)
        # Endpoints can take an adjacent after-state. Include its numerical
        # allowance as well, while positive-width phase coverage stays exact.
        numeric_selected = set(selected)
        endpoint_index = bisect_right(plan.boundaries, right) - 1
        if endpoint_index < len(plan.phases):
            numeric_selected.add(endpoint_index)
        shift = max(abs(s0 - left), abs(s1 - right))
        group_key = (source_index, tuple(selected))
        group = groups.setdefault(group_key, {"keys": set(), "width": Fraction(0),
            "shift": Fraction(0), "numeric_selected": set()})
        group["keys"].update((index, index + 1))
        group["width"] = max(group["width"], right - left)
        group["shift"] = max(group["shift"], shift)
        group["numeric_selected"].update(numeric_selected)
        intervals.append((index, group_key, s0, s1))
    # The retained final key samples final_state AFTER its complete boundary.
    # A completed spin, release or authored transition can transfer additional
    # anchor error there. It is not another positive-width motion phase, and
    # its allowance cannot be recovered from the preceding phase alone.
    final_source = (recording_phase_bounds(plan.simulator, exact[-1], exact[-1],
                    state=plan.final_state) if intervals else None)
    proofs = {}
    for group_key, group in groups.items():
        source_index, selected = group_key
        phase = plan.phases[source_index]
        endpoint_maxima = _endpoint_group_maxima(nodes, group["keys"], model, work=work)
        for carrier, (node, (radius, vertex_error)) in enumerate(zip(nodes, geometry_bounds)):
            _charge(work, "recording_certificate_group")
            frame = node.frame_path
            bound = phase.carriers[frame]
            enclosing = MotionBound(max(plan.phases[i].carriers[frame].speed for i in selected),
                                    max(plan.phases[i].carriers[frame].acceleration for i in selected),
                                    max(plan.phases[i].carriers[frame].angular_speed for i in selected))
            nsp = _source_max(plan, group["numeric_selected"], frame, "position_error_m")
            nsr = _source_max(plan, group["numeric_selected"], frame, "rotation_error_rad")
            if len(exact) - 1 in group["keys"]:
                nsp = max(nsp, final_source[frame].position_error_m)
                nsr = max(nsr, final_source[frame].rotation_error_rad)
            if model.profile in EXECUTION_PROFILES:
                nsp = _exact(nsp, BUDGET_SOURCE_ERROR_RESERVE, "mul", work)
                nsr = _exact(nsr, BUDGET_SOURCE_ERROR_RESERVE, "mul", work)
                def derivative_reserve(value):
                    _charge(work, "recording_budget_reserve")
                    # Keep certified zero derivatives exact; no artificial
                    # motion or acceleration is introduced by publication.
                    return (_exact(value, BUDGET_DERIVATIVE_RESERVE, "mul", work)
                            if value else value)
                bound = MotionBound(bound.speed, derivative_reserve(bound.acceleration),
                                    derivative_reserve(bound.angular_speed))
                enclosing = MotionBound(derivative_reserve(enclosing.speed),
                    derivative_reserve(enclosing.acceleration), derivative_reserve(enclosing.angular_speed))
            ep, eq, magnitude = endpoint_maxima[carrier]
            extra_position = extra_rotation = Fraction(0)
            for phase_index in sorted(group["numeric_selected"]):
                p_extra, q_extra = _recording_endpoint_excess(plan.phases[phase_index].source[frame], work=work)
                if recording_excess is not None:
                    float_position, float_rotation = recording_excess.get(phase_index, {}).get(
                        frame, (Fraction(0), Fraction(0)))
                    if float_position:
                        p_extra = _exact(p_extra, float_position, "add", work)
                    if float_rotation:
                        q_extra = _exact(q_extra, float_rotation, "add", work)
                if _compare(p_extra, extra_position, work) > 0:
                    extra_position = p_extra
                if _compare(q_extra, extra_rotation, work) > 0:
                    extra_rotation = q_extra
            # Rotation angle also bounds the coherently selected unit
            # quaternion chord. The ordinary source nsp/nsr added below are
            # unchanged; these extra terms belong to recorded endpoints.
            # The final after-state has its own fresh context and direct seed,
            # so it contributes no additional recurrence history.
            ep = _exact(ep, extra_position, "add", work)
            eq = _exact(eq, extra_rotation, "add", work)
            proof_width = group["width"] if bound.acceleration or bound.angular_speed else Fraction(0)
            proof_shift = group["shift"] if enclosing.speed or enclosing.angular_speed else Fraction(0)
            key = ("certificate_group", bound, enclosing, radius, vertex_error, nsp, nsr,
                   proof_width, proof_shift, ep, eq, magnitude)
            quantities = dict(_reuse(work, key, lambda: _certificate_quantities(
                model, bound, enclosing, radius, vertex_error, nsp, nsr, proof_width,
                proof_shift, ep, eq, magnitude, work=work)))
            quantities["max_endpoint_time_shift_s"] = upper_binary64(group["shift"], work=work, model=model)
            if (Fraction(quantities["total_position_bound_m"]) > Fraction(options.position_tolerance_m)
                    or Fraction(quantities["total_rotation_bound_rad"]) > Fraction(options.rotation_tolerance_rad)):
                _fail("OKE-E-NUMERIC-BOUND", "Outward serialized bounds exceed the requested tolerance.", model=model,
                      details={"carrier": node.name, "source_phase_index": source_index})
            proofs[group_key, carrier] = quantities
    result = []
    for index, group_key, s0, s1 in intervals:
        source_index, selected = group_key
        phase = plan.phases[source_index]
        left, right = exact[index], exact[index + 1]
        authored_width = _interval_clock_record(right - left, work=work)
        stored_width = _interval_clock_record(s1 - s0, work=work)
        for carrier, (node, (radius, _)) in enumerate(zip(nodes, geometry_bounds)):
            _charge(work, "recording_certificate")
            frame = node.frame_path
            bound = phase.carriers[frame]
            enclosing = MotionBound(max(plan.phases[i].carriers[frame].speed for i in selected),
                                    max(plan.phases[i].carriers[frame].acceleration for i in selected),
                                    max(plan.phases[i].carriers[frame].angular_speed for i in selected))
            if not all(planning_inequalities(width, candidate, radius, options.position_tolerance_m,
                                            options.rotation_tolerance_rad)
                       for width, candidate in ((right - left, bound), (s1 - s0, enclosing))):
                _fail("OKE-E-POSITION-ALIAS", "Authored or stored key spacing exceeds the required quarter-allocation plan.", model=model)
            result.append({"left_key_index": index, "right_key_index": index + 1,
                           "carrier": _carrier_ref(node), "source_phase_indices": list(selected),
                           "h_authored_seconds": dict(authored_width), "h_stored_seconds": dict(stored_width),
                           **proofs[group_key, carrier]})
    return result


def enclosing_phases(phases, authored_start, authored_end, stored_start, stored_end,
                     *, prefix_end, work=None) -> tuple[int, ...]:
    """Include every positive-width neighboring phase; hold only final tails."""
    low = max(Fraction(0), min(Fraction(authored_start), Fraction(stored_start)))
    high = min(Fraction(prefix_end), max(Fraction(authored_end), Fraction(stored_end)))
    selected = []
    for index, phase in enumerate(phases):
        _charge(work, "phase_coverage")
        if max(low, phase.start) < min(high, phase.end):
            selected.append(index)
    if high > low and not selected:
        _fail("OKE-E-PHASE-COVERAGE", "No source phase proves the stored interval.")
    return tuple(selected)


def planning_inequalities(width, bound: MotionBound, radius, position_tolerance,
                          rotation_tolerance) -> bool:
    width, radius = Fraction(width), Fraction(radius)
    position_tolerance, rotation_tolerance = Fraction(position_tolerance), Fraction(rotation_tolerance)
    angle = bound.angular_speed * width
    rotation = angle * angle / 4
    carrier = bound.acceleration * width * width / 8
    return (width > 0 and angle <= ANGULAR_STEP and rotation <= rotation_tolerance / 4
            and carrier <= position_tolerance / 4
            and carrier + radius * rotation <= position_tolerance / 4)


def complete_interval_bounds(*, width, bound: MotionBound, enclosing: MotionBound,
                             radius, vertex_error, endpoint_position_error,
                             endpoint_quaternion_error, stored_arc, time_shift,
                             source_position_error, source_rotation_error,
                             destination_position_error, destination_rotation_error, work=None):
    """The adopted nonzero-endpoint inequalities, with exact rational sums."""
    work = _arithmetic_work(work)
    width, radius, vertex_error, ep, eq, arc, shift, nsp, nsr, ndp, ndr = tuple(_rational(value, work) for value in
        (width, radius, vertex_error, endpoint_position_error, endpoint_quaternion_error,
         stored_arc, time_shift, source_position_error, source_rotation_error,
         destination_position_error, destination_rotation_error))
    acceleration, angular, enclosing_speed, enclosing_angular = tuple(_rational(value, work) for value in
        (bound.acceleration, bound.angular_speed, enclosing.speed, enclosing.angular_speed))
    if any(value < 0 for value in (width, radius, vertex_error, ep, eq, arc, shift, nsp, nsr, ndp, ndr,
                                   acceleration, angular, enclosing_speed, enclosing_angular)):
        raise ValueError("Negative certificate input")
    op = lambda a, b, kind: _exact(a, b, kind, work)
    width_squared = op(width, width, "mul")
    angular_width_squared = op(op(angular, angular, "mul"), width_squared, "mul")
    curvature = op(op(acceleration, width_squared, "mul"), Fraction(8), "div")
    difference = _sum((eq, op(angular_width_squared, Fraction(32), "div"),
                       op(op(arc, arc, "mul"), Fraction(8), "div")), work)
    if _compare(difference, Fraction(1, 2), work) > 0:
        _fail("OKE-E-NUMERIC-BOUND", "The quaternion comparison exceeds its proved local range.")
    rotation = _sum((op(Fraction(4), difference, "mul"), nsr, ndr,
                     op(enclosing_angular, shift, "mul")), work)
    carrier = _sum((ep, curvature, nsp, ndp, op(enclosing_speed, shift, "mul")), work)
    return {"unit_quaternion_difference_bound": difference,
            "ideal_rotation_bound_rad": op(angular_width_squared, Fraction(4), "div"),
            "ideal_position_bound_m": curvature,
            "carrier_position_bound_m": carrier,
            "total_rotation_bound_rad": rotation,
            "total_position_bound_m": _sum((carrier, op(radius, rotation, "mul"), vertex_error), work)}


def destination_numeric_basis() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    implementation = root / "tools/reach_destination.mjs"
    derivation = root / "docs/engineering/reach-destination-numerics.md"
    return {"name": DESTINATION_NAME, "version": DESTINATION_VERSION,
            "implementation_sha256": "sha256:" + hashlib.sha256(implementation.read_bytes()).hexdigest(),
            "derivation_sha256": "sha256:" + hashlib.sha256(derivation.read_bytes()).hexdigest(),
            "method": "Exact rational time and translation; integer RNE quaternion normalization; bounded normalized-chord approximation to short SLERP; separately bounded Three CPU matrix and vertex arithmetic."}


def _recording_lift_relation(left, right, *, work, require_margin=False):
    """Return the exact dot sign and, when requested, its strict cell margin.

    Same-sign nonzero component pairs prove a sign without forming products.
    A pair whose two magnitudes are at least one half also proves magnitude
    at least one quarter. Mixed signs, a smaller optional margin, and narrowed
    operand domains retain all original exact products and additions.
    """
    _charge(work, "recording_hemisphere_domain")
    if (getattr(work, "max_operand_bits", MAX_ARITHMETIC_BITS) == MAX_ARITHMETIC_BITS
            and type(left) is tuple and type(right) is tuple and len(left) == len(right) == 4
            and all(type(value) is float and math.isfinite(value) for value in (*left, *right))):
        positive = negative = large_pair = False
        for a, b in zip(left, right):
            if a and b:
                if (a < 0) == (b < 0):
                    positive = True
                else:
                    negative = True
                large_pair = large_pair or ((a >= 0.5 or a <= -0.5) and
                                             (b >= 0.5 or b <= -0.5))
        if not (positive and negative) and (not require_margin or large_pair or not (positive or negative)):
            return int(positive) - int(negative), large_pair
    a, b = _vector(left, work, size=4), _vector(right, work, size=4)
    dot = _sum((_exact(x, y, "mul", work) for x, y in zip(a, b)), work)
    sign = _compare(dot, Fraction(0), work)
    separated = (not require_margin or
                 _compare(abs(dot), Fraction(1, 1 << 16), work) > 0)
    return sign, separated


def _sample_recording_nodes(plan, nodes, exact, *, work, allow_fast=True,
                            require_same_cells=False):
    """Retain bounded samples and restart unsupported phases exactly.

    The first key in every phase and the final after-state use the original
    controlled recording graph. Each faster interior value carries its own
    proved additional endpoint error in the ordinary supplied-byte certificate.
    The optional strict-cell diagnostic additionally requires original stored
    bits and replays ambiguous phases. Unsupported phases always retain the
    original algorithm, with all attempted work still charged.
    """
    from bisect import bisect_left
    from .reach_recording_fast import (RecordingRoundingAmbiguity, begin_bounded_phase,
                                       sample_bounded_frames, sample_certified_frames)

    sample_fast = sample_certified_frames if require_same_cells else sample_bounded_frames

    frame_paths = tuple(node.frame_path for node in nodes)
    previous_state = None
    moving_frames = frozenset()
    recording_context = None
    exact_phases = set()
    recording_excess = {}
    key_index = 0
    phase_start_key = 0
    accelerated = False
    captured_phase = None
    captured_phase_stop = 0
    while key_index < len(exact):
        time = exact[key_index]
        _charge(work, "recording_sample")
        index = bisect_right(plan.boundaries, time) - 1
        state = plan.final_state if index >= len(plan.phase_states) else plan.phase_states[index]
        new_phase = state is not previous_state
        if new_phase:
            _charge(work, "recording_phase_context")
            recording_context = object()
            moving_frames = plan.simulator.recording_moving_frames(state, frame_paths)
            phase_start_key = key_index
            captured_phase = None
        selected_frames = frame_paths if new_phase else tuple(path for path in frame_paths if path in moving_frames)
        angular_proof = (plan.phases[index].recording_angular_proof
                         if index < len(plan.phases) else None)
        if (allow_fast and not new_phase and selected_frames
                and index < len(plan.phases) and index not in exact_phases):
            try:
                if not require_same_cells and key_index == phase_start_key + 1:
                    captured_phase_stop = bisect_left(exact, plan.boundaries[index + 1])
                    captured_phase = begin_bounded_phase(plan.simulator,
                        tuple(exact[key_index:captured_phase_stop]), state, selected_frames,
                        context=recording_context, phase_bounds=plan.phases[index].source,
                        phase_interval=(plan.boundaries[index], plan.boundaries[index + 1]),
                        recording_angular_proof=angular_proof)
                result = (captured_phase.sample(time) if captured_phase is not None else
                    sample_fast(plan.simulator, time, state, selected_frames,
                        context=recording_context, moving_frames=moving_frames,
                        phase_bounds=plan.phases[index].source,
                        phase_interval=(plan.boundaries[index], plan.boundaries[index + 1]),
                        recording_angular_proof=angular_proof))
            except RecordingRoundingAmbiguity as error:
                if work.callback_error is error:
                    raise
                _charge(work, "recording_fast_phase_restart")
                # Samples are private until the whole bake and independent
                # supplied-byte check pass. Discard every candidate key from
                # this phase, including unchanged tracks, before rebuilding.
                exact_phases.add(index)
                recording_excess.pop(index, None)
                for node in nodes:
                    _charge(work, "recording_fast_phase_truncate")
                    del node.translations[phase_start_key:]
                    del node.rotations_xyzw[phase_start_key:]
                previous_state = None
                captured_phase = None
                key_index = phase_start_key
                continue
            frames = result.frames
            # A captured phase has one immutable bound per actual frame. Its
            # complete source and bound receipt follows every pose callback;
            # later keys require no repeated identical maximum calculation.
            allowances = (result.excess_by_frame.items()
                if captured_phase is None or key_index == phase_start_key + 1 else ())
            for frame, excess in allowances:
                _charge(work, "recording_fast_endpoint_allowance")
                if frame not in selected_frames:
                    raise ValueError("A recording allowance must belong to a selected source frame")
                position, rotation = excess.position_m, excess.rotation_rad
                if type(position) is not Fraction or type(rotation) is not Fraction:
                    raise ValueError("Recording endpoint allowances must be exact fractions")
                work.guard(position, rotation)
                if position < 0 or rotation < 0:
                    raise ValueError("Recording endpoint allowances must be nonnegative")
                previous = recording_excess.setdefault(index, {}).get(frame, (Fraction(0), Fraction(0)))
                # Complete exact values have already passed the live width
                # guard. Identical enclosure values need no cross-product
                # ordering; a changed value still takes the exact comparison.
                if position != previous[0]:
                    position = position if _compare(position, previous[0], work) > 0 else previous[0]
                if rotation != previous[1]:
                    rotation = rotation if _compare(rotation, previous[1], work) > 0 else previous[1]
                work.guard(position, rotation)
                recording_excess[index][frame] = (position, rotation)
                accelerated = accelerated or bool(position or rotation)
        else:
            frames = plan.simulator.recording_frames(time, state, selected_frames,
                moving_frames=moving_frames, recording_context=recording_context,
                recording_angular_proof=angular_proof)
        restart_all = False
        for node in nodes:
            _charge(work, "recording_pose")
            if not new_phase and node.frame_path not in moving_frames:
                node.translations.append(node.translations[-1])
                node.rotations_xyzw.append(node.rotations_xyzw[-1])
                continue
            pose = frames[node.frame_path]
            node.translations.append(tuple(pose.position))
            w, x, y, z = pose.orientation
            quaternion = (x, y, z, w)
            if node.rotations_xyzw:
                strict_lift = accelerated and allow_fast and require_same_cells
                sign, separated = _recording_lift_relation(node.rotations_xyzw[-1], quaternion,
                    work=work, require_margin=strict_lift)
                if strict_lift:
                    _charge(work, "recording_fast_lift_guard")
                    # Equal binary32 cells for components of magnitude <=2
                    # give a binary64 component difference at most 2^-22.
                    # The two four-component dot products therefore differ
                    # by less than 2^-17. A strict 2^-16 margin proves the
                    # original sampler chooses this same hemisphere lift.
                    if not separated:
                        _charge(work, "recording_fast_lift_restart")
                        # An adjacent key may belong to the preceding phase.
                        # Replay the whole bake exactly to cover that boundary
                        # as well; previous attempted work remains consumed.
                        allow_fast = accelerated = False
                        recording_excess.clear()
                        for previous_node in nodes:
                            _charge(work, "recording_fast_phase_truncate")
                            previous_node.translations.clear()
                            previous_node.rotations_xyzw.clear()
                        previous_state = None
                        key_index = 0
                        restart_all = True
                        break
                if sign < 0:
                    lifted = []
                    for value in quaternion:
                        _charge(work, "recording_hemisphere_negate")
                        if getattr(work, "max_operand_bits", MAX_ARITHMETIC_BITS) != MAX_ARITHMETIC_BITS:
                            _rational(value, work)
                        lifted.append(-value)
                    quaternion = tuple(lifted)
            node.rotations_xyzw.append(quaternion)
        if restart_all:
            continue
        if captured_phase is not None and key_index + 1 == captured_phase_stop:
            try:
                # The output arrays are still private. Admit every actual
                # source and fixed bound after the last pose/hemisphere
                # callback, then publish the complete cursor group together.
                captured_phase.finish()
            except RecordingRoundingAmbiguity as error:
                if work.callback_error is error:
                    raise
                _charge(work, "recording_fast_phase_restart")
                exact_phases.add(index)
                recording_excess.pop(index, None)
                for node in nodes:
                    _charge(work, "recording_fast_phase_truncate")
                    del node.translations[phase_start_key:]
                    del node.rotations_xyzw[phase_start_key:]
                previous_state = None
                captured_phase = None
                key_index = phase_start_key
                continue
            captured_phase = None
        previous_state = state
        key_index += 1
    return recording_excess



def _build_reach_scene(model, *, options, source_uri, source_sha256, work, reach_plan=None,
                       target_contract=REACH_TARGET):
    from . import __version__
    from .evaluator import time_text
    from .reach_pose import source_numeric_basis
    from .scene import (BakedScene, ExportOptions, SurfaceMesh, MAX_KEYFRAMES, MAX_BAKED_POSES,
                        MAX_VALIDATION_POSES, MAX_MESH_VERTICES, MAX_GLB_BYTES,
                        _nodes, checked_contract, program_metadata, relationship_metadata,
                        force_profile_metadata, extrusion_profile_metadata, holes_profile_metadata, ring_loft_profile_metadata)

    version = checked_contract(model, target_contract)
    options = options or ExportOptions()
    end = options.checked_end(model)
    if options.time_tolerance_s > 1e-6:
        _fail("OKE-E-OPTIONS", "Reach recording time tolerance must be at most 1e-6 seconds.", model=model, kind="options")
    program = program_metadata(model, check=work.tick)
    if source_sha256 is not None and source_sha256 != program["sources"]["entry"]["source_revision"]:
        _fail("OKE-E-PROVENANCE", "The entry source hash must match the immutable program bundle.", model=model, kind="unsupported")
    if reach_plan is None:
        plan = reach_prefix_plan(model, end, work=work)
    else:
        _charge(work, "recording_plan_identity")
        if (not isinstance(reach_plan, ReachPrefixPlan)
                or reach_plan.simulator.model is not model
                or reach_plan.simulator.work is not work
                or not reach_plan.boundaries
                or reach_plan.boundaries[0] != 0
                or reach_plan.boundaries[-1] != end
                or len(reach_plan.boundary_records) != len(reach_plan.boundaries)
                or len(reach_plan.phases) != len(reach_plan.boundaries) - 1
                or len(reach_plan.phase_states) != len(reach_plan.phases)):
            raise ValueError("A retained recording plan must match the model, request work and complete prefix.")
        plan = reach_plan
    recording_stage("geometry", work=work)
    nodes = _nodes(model, options, check=work.tick, work=work)
    if not nodes:
        _fail("OKE-E-EMPTY-SCENE", "Reach recording requires at least one actual object occurrence.", model=model, kind="unsupported")
    geometry = node_geometry_bounds(model, nodes, work=work)
    exact, times, retained = reach_timeline(model, options, plan, nodes, geometry, work=work)
    recording_stage("sampling", work=work)
    recording_excess = _sample_recording_nodes(plan, nodes, exact, work=work)
    recording_stage("certification", work=work)
    certificates = interval_certificates(model, options, plan, nodes, geometry, exact, times, work=work,
                                        recording_excess=recording_excess)
    basis = source_numeric_basis(work=work)
    source_basis = {"name": basis.name, "version": basis.version,
                    "implementation_sha256": basis.implementation, "method": basis.method,
                    "derivation_sha256": basis.derivation}
    quantization = {"schema_version": "ontokin.reach-quantization/0.1",
        "rotation_interpolation": "shortest_arc_slerp", "clock_conversion": CLOCK_CONVERSION,
        "position_tolerance_m": options.position_tolerance_m,
        "rotation_tolerance_rad": options.rotation_tolerance_rad,
        "time_tolerance_s": options.time_tolerance_s,
        "source_numeric_bound_basis": source_basis,
        "destination_numeric_bound_basis": destination_numeric_basis(),
        "retained_keys": retained, "interval_certificates": certificates,
        # This is the certificate's assertion, not its evidence. export_glb
        # publishes no bytes until the independent supplied-byte checker passes.
        "all_values_independently_recomputed": True, "unknown_error_bound_policy": "reject",
        "certificate_scope": "specified source and supplied bytes; separately identified destination numeric behavior"}
    source = {"uri": source_uri, "uri_kind": "caller_supplied_bundle_locator", "entry_source_id": "entry",
              "entry_revision": program["sources"]["entry"]["source_revision"],
              "editable_source_of_truth": "pinned .ok source bundle",
              "provenance": "Compiler supplied exact source identities; source text is not embedded."}
    surface_profile = {"name": "surface-0.1", "local_loft_axis": "+Z",
        "local_placement": "baked_once_into_vertices_and_normals_in_carrier_frame",
        "regional_materials": "explicit_linear_rgba_metallic_roughness",
        "physical_participation": "visual_meshes_add_no_matter_or_motion_authority",
        "quantization_tolerance_m": min(1e-5, options.position_tolerance_m),
        "limitations": ["flat_shading", "polygonal_elliptical_sections", "no_textures_or_skin_deformation",
                        "no_automatic_collision_or_mass", "recorded_rigid_animation_only"]}
    metadata = {"target_contract": target_contract, "schema_version": version, "source": source,
        "module": model.module_name, "scene": model.scene_name, "profile": model.profile,
        "coordinates": {"handedness": "right", "up": "+Y", "length_unit": "m", "time_unit": "s"},
        "transform_policy": "all_nodes_are_roots_with_baked_world_poses", **relationship_metadata(model),
        "boundary_states": list(plan.boundary_records), "gravity_m_per_s2": list(model.gravity),
        "motion_authority": "OntoKin semantic evaluator; playback contains no live solver",
        "program": program, "force_profile": force_profile_metadata(), "surface_profile": surface_profile,
        "reach_profile": reach_profile_metadata(model.profile), "reach_quantization": quantization}
    if model.profile == EXTRUSION_PROFILE:
        metadata["polygon_extrusion_profile"] = extrusion_profile_metadata()
    if model.profile == HOLES_PROFILE:
        metadata["polygon_holes_profile"] = holes_profile_metadata()
    if model.profile == RING_LOFT_PROFILE:
        metadata["polygon_loft_profile"] = ring_loft_profile_metadata()
    report = {"schema_version": "ontokin.glb-report/" + version, "target_contract": target_contract,
        "outcome": "baked_pending_binary_validation",
        "exporter": {"name": "OntoKin reference GLB exporter", "version": __version__},
        "source": source, "program_revision": model.program_revision, "program": program,
        "scene": {"module": model.module_name, "name": model.scene_name, "profile": model.profile,
                  "declared_duration_seconds": time_text(model.duration)},
        "sampling": {"requested_fps": options.fps, "start_seconds": "0", "end_seconds": time_text(end),
            "keyframe_count": len(times), "boundary_times_seconds": [time_text(t) for t in plan.boundaries],
            "boundary_time_mapping": [item for item in retained if item["semantic_boundary"]],
            "max_time_quantization_error_seconds": upper_binary64(max((abs(Fraction(t) - a) for t, a in zip(times, exact)), default=Fraction(0)), work=work),
            "evaluated_horizon": "requested_prefix_inclusive_after_side",
            "clock_conversion": CLOCK_CONVERSION, "interval_certificate_count": len(certificates),
            "phase_count": len(plan.phases)},
        "tolerances": {"position_m": options.position_tolerance_m, "rotation_rad": options.rotation_tolerance_rad,
            "time_seconds": options.time_tolerance_s, "surface_local_vertex_m": min(1e-5, options.position_tolerance_m),
            "scope": "recorded carrier/landmark delivery; source goal residual remains 1e-9 m"},
        "representation": {"coordinates": metadata["coordinates"], "hierarchy": metadata["transform_policy"],
            "translation_interpolation": "LINEAR", "rotation_interpolation": "shortest-path SLERP",
            "stored_components": "IEEE 754 binary32", "quaternion_order": "XYZW",
            "identified_destination": destination_numeric_basis()},
        "geometry": {"object_nodes": len(model.objects),
            "authored_mesh_nodes": sum(node.mesh is not None for node in nodes if node.metadata["kind"] == "object"),
            "helper_nodes": sum(node.metadata["kind"] == "visual_helper" for node in nodes),
            "aggregate_occurrence_vertices": sum(len(node.mesh.positions) for node in nodes if node.mesh is not None),
            "native_surface_nodes": sum(isinstance(node.mesh, SurfaceMesh) for node in nodes),
            "surface_profile": surface_profile},
        "retention": {"preserved_metadata": ["complete pinned source and occurrence identity", "native geometry and regional PBR",
            "both sides of every exact semantic boundary", "complete force, impulse and reach histories", "incoming release poses and tangent contributors"],
            "baked": ["world carrier poses", "two prescribed planar hinge coordinates", "released sphere trajectories"],
            "not_executable_in_glb": ["source code and edits", "reach solver and coordinate claims", "live physics and constraints"],
            "losses": ["Exact source clocks and transforms are converted to binary32.",
                       "Continuous source motion is replaced by bounded recorded interpolation.",
                       "The pinned source bundle remains authoritative and is not reconstructable from the artifact.",
                       "The named destination's numerical bound does not certify arbitrary other players."],
            "outside_interval_omitted": end < model.duration},
        "budgets": {"max_keyframes": MAX_KEYFRAMES, "max_baked_poses": MAX_BAKED_POSES,
            "max_validation_poses": MAX_VALIDATION_POSES, "max_mesh_vertices": MAX_MESH_VERTICES,
            "max_glb_bytes": MAX_GLB_BYTES, "max_boundary_state_records": 100000,
            "max_interval_certificates": MAX_CERTIFICATES,
            "boundary_accounting": "H06 complete both-side weighted source histories plus incoming releases",
            "mesh_accounting": "every occurrence, including repeated geometry and requested helpers"},
        "reach_profile": metadata["reach_profile"], "reach_quantization": quantization}
    if model.profile == EXTRUSION_PROFILE:
        report["geometry"]["polygon_extrusion_profile"] = metadata["polygon_extrusion_profile"]
    if model.profile == HOLES_PROFILE:
        report["geometry"]["polygon_holes_profile"] = metadata["polygon_holes_profile"]
    if model.profile == RING_LOFT_PROFILE:
        report["geometry"]["polygon_loft_profile"] = metadata["polygon_loft_profile"]
    return BakedScene(model.module_name, model.scene_name, exact, times, list(plan.boundaries), nodes,
                      metadata, report, options, contract=target_contract, schema_version=version)


def build_reach_scene(model, *, options=None, source_uri=None, source_sha256=None,
                      check=None, work=None, reach_plan=None, target_contract=REACH_TARGET):
    from .reach_numeric import ReachExecutionWork, ReachAdmissionError, require_execution_work
    from .scene import EXECUTION_TARGETS, REACH_TARGETS
    if target_contract not in REACH_TARGETS:
        raise ValueError("A reach recording requires an explicit reach destination")
    if target_contract in EXECUTION_TARGETS:
        require_execution_work(work, target_contract=target_contract)
    from .reach_source import reach_error
    work = work if work is not None else ReachExecutionWork(check=check)
    try:
        return _build_reach_scene(model, options=options, source_uri=source_uri,
                                  source_sha256=source_sha256, work=work, reach_plan=reach_plan,
                                  target_contract=target_contract)
    except ReachAdmissionError as error:
        if error is work.callback_error:
            raise
        raise reach_error(error.reach_code, str(error), model.span, phase="evaluation",
                          details=error.details, blocks=["delivered"]) from error
