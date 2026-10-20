"""Exact clocks and conservative arithmetic for recorded planar reach delivery.

This implementation does not import the frozen contract preparation programs.
Its ideal rotation interpolant is normalized-endpoint shortest-arc SLERP. The
separately identified destination approximates that interpolant by a controlled
normalized chord; its complete error is an explicit certificate term.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import struct
from typing import Any


REACH_TARGET = "ontokin.glb/0.6"
CLOCK_CONVERSION = "binary32_rne_ties_to_even_from_exact_rational"
MAX_CERTIFICATES = 100000
MAX_ARITHMETIC_BITS = 32768
# Strict rational lower bound on pi/4, also below the schema's binary64 maximum.
ANGULAR_STEP = Fraction(7853981633974483, 10**16)
DESTINATION_NAME = "ontokin-controlled-three-recording"
DESTINATION_VERSION = "0.1.0"
DESTINATION_COMPONENT_LIMIT = Fraction(1 << 400)
NORMALIZATION_ERROR = Fraction(1, 1 << 51)


def _charge(work=None, kind="recording_arithmetic"):
    if work is not None:
        work.charge(kind)


def _guard(value: Fraction, work=None):
    if work is not None:
        work.guard(value)
    elif max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > MAX_ARITHMETIC_BITS:
        _fail("OKE-E-NUMERIC-BUDGET", "Recording arithmetic exceeds its finite operand bound.",
              kind="resource", details={"max_operand_bits": MAX_ARITHMETIC_BITS})


def _fail(code, message, *, model=None, kind="numeric", details=None):
    # Lazy import keeps scene's explicit adapter dispatch acyclic.
    from .scene import export_error
    export_error(code, message, model, kind=kind, details=details)


def _floor_log2_ratio(n: int, d: int) -> int:
    exponent = n.bit_length() - d.bit_length()
    if (n < d << exponent) if exponent >= 0 else (n << -exponent < d):
        exponent -= 1
    return exponent


def _nearest_even(n: int, d: int) -> int:
    q, remainder = divmod(n, d)
    twice = remainder * 2
    return q + int(twice > d or (twice == d and q & 1))


def direct_binary32(value, *, work=None, model=None) -> tuple[float, str]:
    """Round a nonnegative exact clock directly to binary32, including ties.

    No binary64 intermediate participates in choosing the stored bits. The
    final unpack only exposes the already selected binary32 value to Python.
    """
    _charge(work, "clock_conversion")
    value = Fraction(value)
    _guard(value, work)
    if value < 0:
        _fail("OKE-E-CLOCK", "A recorded clock must be nonnegative.", model=model)
    if not value:
        return 0.0, "00000000"
    exponent = _floor_log2_ratio(value.numerator, value.denominator)
    if exponent > 127:
        _fail("OKE-E-FLOAT32", "The exact clock rounds outside finite binary32.", model=model)
    shift = 149 if exponent < -126 else 23 - exponent
    numerator, denominator = value.numerator, value.denominator
    if shift >= 0:
        numerator <<= shift
    else:
        denominator <<= -shift
    significand = _nearest_even(numerator, denominator)
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
    _charge(work)
    value = Fraction(value)
    _guard(value, work)
    if value < 0:
        raise ValueError("A certificate upper bound cannot be negative")
    try:
        result = float(value)
    except OverflowError:
        result = math.inf
    if math.isfinite(result) and Fraction(result) < value:
        result = math.nextafter(result, math.inf)
    if not math.isfinite(result):
        _fail("OKE-E-NUMERIC-BOUND", "A proved bound exceeds finite report precision.", model=model)
    return result


def sqrt_upper(value, *, work=None, bits=96) -> Fraction:
    """An outward dyadic square-root bound obtained solely by integer isqrt."""
    _charge(work)
    value = Fraction(value)
    _guard(value, work)
    if value < 0:
        raise ValueError("Negative square root")
    scaled_numerator = value.numerator << (2 * bits)
    if work is not None:
        work.guard_bits(scaled_numerator.bit_length())
    root = math.isqrt(scaled_numerator // value.denominator)
    return Fraction(root + int(root * root * value.denominator < scaled_numerator), 1 << bits)


def norm_upper(values, *, work=None) -> Fraction:
    values = tuple(Fraction(value) for value in values)
    _charge(work)
    for value in values:
        _guard(value, work)
    return sqrt_upper(sum((value * value for value in values), Fraction(0)), work=work)


def normalized_component(component, squared_norm, *, work=None) -> float:
    """Correctly rounded component/sqrt(norm2), with an exact midpoint test."""
    _charge(work, "destination_normalization")
    component, squared_norm = Fraction(component), Fraction(squared_norm)
    _guard(component, work)
    _guard(squared_norm, work)
    if squared_norm <= 0:
        _fail("OKE-E-QUATERNION", "A stored quaternion must have positive finite norm.")
    if not component:
        return 0.0
    square = component * component / squared_norm
    if square > 1:
        raise ValueError("Component exceeds the supplied squared norm")
    exponent = _floor_log2_ratio(square.numerator, square.denominator) // 2
    shift = 1074 if exponent < -1022 else 52 - exponent
    numerator = square.numerator << (2 * shift)
    denominator = square.denominator
    if work is not None:
        work.guard_bits(numerator.bit_length())
    q = math.isqrt(numerator // denominator)
    midpoint_left = numerator * 4
    midpoint_right = denominator * (2 * q + 1) ** 2
    if midpoint_left > midpoint_right or (midpoint_left == midpoint_right and q & 1):
        q += 1
    answer = math.ldexp(float(q), -shift)
    return -answer if component < 0 else answer


def normalized_quaternion(values, *, work=None) -> tuple[float, ...]:
    values = tuple(Fraction(value) for value in values)
    if len(values) != 4:
        _fail("OKE-E-QUATERNION", "A stored rotation requires four finite components.")
    for value in values:
        _guard(value, work)
    squared = sum((value * value for value in values), Fraction(0))
    if not squared:
        _fail("OKE-E-QUATERNION", "A zero quaternion has no normalized interpretation.")
    return tuple(normalized_component(value, squared, work=work) for value in values)


def quaternion_arc_upper(first, last, *, work=None) -> Fraction:
    """Bound the S^3 short arc, not the doubled SO(3) rotation angle."""
    raw_first, raw_last = tuple(map(Fraction, first)), tuple(map(Fraction, last))
    if sum((a * b for a, b in zip(raw_first, raw_last)), Fraction(0)) < 0:
        _fail("OKE-E-QUATERNION-LIFT", "Stored quaternions must retain one coherent short lift.")
    a, b = normalized_quaternion(raw_first, work=work), normalized_quaternion(raw_last, work=work)
    chord = norm_upper((Fraction(x) - Fraction(y) for x, y in zip(a, b)), work=work)
    chord += 2 * NORMALIZATION_ERROR
    if chord > Fraction(1, 2):
        _fail("OKE-E-ROTATION-ALIAS", "The normalized endpoint chord exceeds the proved short-arc range.")
    # 2 asin(d/2) <= d/sqrt(1-d*d/4) <= d/(1-d*d/4).
    arc = chord / (1 - chord * chord / 4)
    if arc > ANGULAR_STEP:
        _fail("OKE-E-ROTATION-ALIAS", "The stored quaternion arc exceeds pi/4.")
    return arc


def controlled_destination_sample(first_position, last_position, first_quaternion,
                                  last_quaternion, amount, *, work=None):
    """Reference port of the identified destination's integer interpolation.

    This function is additional playback checking. Its samples do not establish
    the continuous certificate, whose algebraic terms are computed separately.
    """
    amount = min(Fraction(1), max(Fraction(0), Fraction(amount)))
    a, b = normalized_quaternion(first_quaternion, work=work), normalized_quaternion(last_quaternion, work=work)
    if sum((Fraction(x) * Fraction(y) for x, y in zip(a, b)), Fraction(0)) < 0:
        b = tuple(-value for value in b)
    position = tuple(float((1 - amount) * Fraction(x) + amount * Fraction(y))
                     for x, y in zip(first_position, last_position))
    chord = tuple((1 - amount) * Fraction(x) + amount * Fraction(y) for x, y in zip(a, b))
    return position, normalized_quaternion(chord, work=work)


def destination_numeric_bounds(arc, translation_magnitude, radius, vertex_error,
                               *, work=None) -> tuple[Fraction, Fraction]:
    """Uniform actual destination error, including nonorthogonal matrix error."""
    _charge(work, "destination_bound")
    arc, magnitude, radius, vertex_error = map(Fraction, (arc, translation_magnitude, radius, vertex_error))
    if min(arc, magnitude, radius, vertex_error) < 0 or arc > ANGULAR_STEP:
        _fail("OKE-E-NUMERIC-BOUND", "Destination operands exceed the proved range.")
    if magnitude + radius + vertex_error > DESTINATION_COMPONENT_LIMIT:
        _fail("OKE-E-NUMERIC-BOUND", "Destination magnitude exceeds its finite arithmetic proof.")
    # Exact-endpoint normalized chord vs SLERP plus correctly rounded unit
    # component errors. Matrix defect and matrix/vector rounding are positional.
    rotation = arc * arc + Fraction(1, 1 << 44)
    position = (magnitude + radius + vertex_error + 1) / (1 << 38)
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
                             destination_position_error, destination_rotation_error):
    """The adopted nonzero-endpoint inequalities, with exact rational sums."""
    width, radius, vertex_error, ep, eq, arc, shift, nsp, nsr, ndp, ndr = map(Fraction,
        (width, radius, vertex_error, endpoint_position_error, endpoint_quaternion_error,
         stored_arc, time_shift, source_position_error, source_rotation_error,
         destination_position_error, destination_rotation_error))
    if min(width, radius, vertex_error, ep, eq, arc, shift, nsp, nsr, ndp, ndr) < 0:
        raise ValueError("Negative certificate input")
    difference = eq + bound.angular_speed ** 2 * width ** 2 / 32 + arc ** 2 / 8
    if difference > Fraction(1, 2):
        _fail("OKE-E-NUMERIC-BOUND", "The quaternion comparison exceeds its proved local range.")
    rotation = 4 * difference + nsr + ndr + enclosing.angular_speed * shift
    carrier = ep + bound.acceleration * width ** 2 / 8 + nsp + ndp + enclosing.speed * shift
    return {"unit_quaternion_difference_bound": difference,
            "ideal_rotation_bound_rad": bound.angular_speed ** 2 * width ** 2 / 4,
            "ideal_position_bound_m": bound.acceleration * width ** 2 / 8,
            "carrier_position_bound_m": carrier,
            "total_rotation_bound_rad": rotation,
            "total_position_bound_m": carrier + radius * rotation + vertex_error}


def destination_numeric_basis() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    implementation = root / "tools/reach_destination.mjs"
    derivation = root / "docs/engineering/reach-destination-numerics.md"
    return {"name": DESTINATION_NAME, "version": DESTINATION_VERSION,
            "implementation_sha256": "sha256:" + hashlib.sha256(implementation.read_bytes()).hexdigest(),
            "derivation_sha256": "sha256:" + hashlib.sha256(derivation.read_bytes()).hexdigest(),
            "method": "Exact rational time and translation; integer RNE quaternion normalization; bounded normalized-chord approximation to short SLERP; separately bounded Three CPU matrix and vertex arithmetic."}
