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


def reach_profile_metadata():
    return {"schema_version": "ontokin.reach-recording/0.1", "source_profile": "planar-reach-0.1",
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


def recording_phase_bounds(simulator, start, end):
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
        selected, seen = [], set()
        for path in simulator.model.objects:
            _charge(simulator.work, "recording_phase_frame")
            frame = path + ".frame"
            selected.append(frame)
            seen.add(frame)
        for joint in simulator.model.joints.values():
            _charge(simulator.work, "recording_phase_frame")
            frame = joint.parent + ".frame"
            if frame not in seen:
                selected.append(frame)
                seen.add(frame)
        # The ordinary exact phase traversal still follows all required
        # site/ownership/joint paths and prepares every root's spin plan.
        return phase_bounds(simulator, start, end, selected_frames=selected)["frames"]
    except ReachAdmissionError as error:
        simulator._numeric_error(error, time=Fraction(start))


def reach_prefix_plan(model, end, *, work) -> ReachPrefixPlan:
    """Validate the requested prefix once and retain bounded phase anchors.

    No event after end is evaluated. States are retained only after the complete
    boundary-history forecast passes; immutable numeric cache values stay owned
    by this same request. Baking later reads these validated phases directly.
    """
    from .reach_runtime import ReachSimulator, boundary_history_bound
    from .scene import MAX_KEYFRAMES

    class PlanningSimulator(ReachSimulator):
        def snapshot(self, time, side):
            self._kinematics(time, self.state)
            return {}

    recording_stage("planning", work=work)
    simulator = PlanningSimulator(model, work=work)
    times, phases, states, records = [], [], [], []
    time = Fraction(0)
    while True:
        _charge(work, "recording_boundary_preflight")
        if len(times) >= MAX_KEYFRAMES:
            _fail("OKE-E-KEYFRAME-BUDGET", "Semantic boundaries exceed the recording key budget.", model=model, kind="resource")
        boundary_history_bound(model, [*times, time], horizon=end, check=work.tick)
        simulator.advance(time, "before")
        before = simulator.recording_boundary(time, "before")
        simulator.advance(time, "after")
        after = simulator.recording_boundary(time, "after")
        records.append(_boundary_record(time, before, after, simulator.incoming_releases_at(time)))
        times.append(time)
        if time == end:
            break
        following = simulator._next_boundary()
        stop = end if following is None or following > end else following
        if stop <= time:
            _fail("OKE-E-PHASE-COVERAGE", "The validated prefix did not advance to a later boundary.", model=model)
        recording_stage("planning_phase", work=work)
        source = recording_phase_bounds(simulator, time, stop)
        carriers = {path: MotionBound(value.carrier_speed_upper_m_per_s,
                                     value.carrier_acceleration_upper_m_per_s2,
                                     value.angular_speed_upper_rad_per_s)
                    for path, value in source.items()}
        phases.append(ReachPhase(time, stop, carriers, source))
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


def _carrier_ref(node):
    return {"path": node.name,
            "element_id": list(node.metadata.get("element_id", node.metadata.get("related_element_id", ())))}


def _stored_vector(values, model):
    from .scene import float32
    return tuple(float32(value, model) for value in values)


def _endpoint_rounding(position, quaternion, model, *, work):
    """Bound conversion of one actual source endpoint, with charged reuse."""
    _charge(work, "recording_endpoint_domain")
    if (len(position) != 3 or len(quaternion) != 4
            or any(type(value) is not float or not math.isfinite(value)
                   for value in (*position, *quaternion))):
        raise ValueError("A recording endpoint requires finite binary64 pose components")
    work.guard_bits(1075)
    def calculate():
        stored_p = _stored_vector(position, model)
        stored_q = _stored_vector(quaternion, model)
        if not any(stored_q):
            _fail("OKE-E-QUATERNION", "A stored zero quaternion has no normalized interpretation.", model=model)
        # A finite binary64 source minus its correctly rounded binary32 value
        # is exact in binary64 (zero, or same-sign Sterbenz operands). L1 then
        # bounds Euclidean error without repeated exact squares and roots.
        ep = _sum((_rational(abs(a - b), work) for a, b in zip(position, stored_p)), work)
        large_norm = max(abs(value) for value in quaternion) >= .5
        if not large_norm:
            q = _vector(quaternion, work, size=4)
            squared = _sum((_exact(value, value, "mul", work) for value in q), work)
            large_norm = squared >= Fraction(1, 4)
        if large_norm:
            # ||normalize(a)-normalize(b)|| <= 2||a-b||/||a||.
            # The checked lower norm 1/2 gives a rational bound without
            # computing either normalized endpoint or a floating square root.
            eq = _exact(Fraction(4), _sum((_rational(abs(a - b), work)
                        for a, b in zip(quaternion, stored_q)), work), "mul", work)
        else:
            eq = norm_upper((_exact(_rational(a, work), _rational(b, work), "sub", work)
                             for a, b in zip(normalized_quaternion(q, work=work),
                                             normalized_quaternion(stored_q, work=work))), work=work)
        eq = _exact(eq, 2 * NORMALIZATION_ERROR, "add", work)
        magnitude = _sum((_rational(abs(value), work) for value in stored_p), work)
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
    ndp, ndr = destination_numeric_bounds(arc, magnitude, radius, vertex_error, work=work)
    quantities = {"landmark_radius_m": radius, "local_vertex_error_bound_m": vertex_error,
        "angular_speed_bound_rad_per_s": bound.angular_speed,
        "carrier_acceleration_bound_m_per_s2": bound.acceleration,
        "enclosing_carrier_speed_bound_m_per_s": enclosing.speed,
        "enclosing_carrier_acceleration_bound_m_per_s2": enclosing.acceleration,
        "enclosing_angular_speed_bound_rad_per_s": enclosing.angular_speed,
        "max_endpoint_time_shift_s": shift, "max_endpoint_position_error_m": ep,
        "max_endpoint_unit_quaternion_error": eq, "stored_quaternion_arc_upper_rad": arc,
        "source_numeric_position_bound_m": nsp, "source_numeric_rotation_bound_rad": nsr,
        "destination_numeric_position_bound_m": ndp, "destination_numeric_rotation_bound_rad": ndr}
    # A consumer must be able to check the inequalities using the
    # reported upper bounds themselves. Round primitive quantities
    # outward first, then propagate those rounded values through every
    # dependent bound. Independently rounding the exact final sum can
    # otherwise make the displayed certificate fail by one ulp.
    quantities = {name: upper_binary64(value, work=work, model=model)
                  for name, value in quantities.items()}
    def q(name):
        return Fraction(quantities[name])
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


def interval_certificates(model, options, plan, nodes, geometry_bounds, exact, times, *, work):
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
    proofs = {}
    for group_key, group in groups.items():
        source_index, selected = group_key
        phase = plan.phases[source_index]
        for carrier, (node, (radius, vertex_error)) in enumerate(zip(nodes, geometry_bounds)):
            _charge(work, "recording_certificate_group")
            frame = node.frame_path
            bound = phase.carriers[frame]
            enclosing = MotionBound(max(plan.phases[i].carriers[frame].speed for i in selected),
                                    max(plan.phases[i].carriers[frame].acceleration for i in selected),
                                    max(plan.phases[i].carriers[frame].angular_speed for i in selected))
            nsp = _source_max(plan, group["numeric_selected"], frame, "position_error_m")
            nsr = _source_max(plan, group["numeric_selected"], frame, "rotation_error_rad")
            ep = eq = magnitude = Fraction(0)
            for key_index in sorted(group["keys"]):
                p_error, q_error, p_magnitude = _endpoint_rounding(
                    tuple(node.translations[key_index]), tuple(node.rotations_xyzw[key_index]), model, work=work)
                ep, eq, magnitude = max(ep, p_error), max(eq, q_error), max(magnitude, p_magnitude)
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
        authored_width = rational_record(right - left, work=work)
        stored_width = rational_record(s1 - s0, work=work)
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


def _build_reach_scene(model, *, options, source_uri, source_sha256, work, reach_plan=None):
    from . import __version__
    from .evaluator import time_text
    from .reach_pose import source_numeric_basis
    from .scene import (BakedScene, ExportOptions, SurfaceMesh, MAX_KEYFRAMES, MAX_BAKED_POSES,
                        MAX_VALIDATION_POSES, MAX_MESH_VERTICES, MAX_GLB_BYTES,
                        _nodes, checked_contract, program_metadata, relationship_metadata,
                        force_profile_metadata)

    checked_contract(model, REACH_TARGET)
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
    frame_paths = tuple(node.frame_path for node in nodes)
    previous_state = None
    moving_frames = frozenset()
    for time in exact:
        _charge(work, "recording_sample")
        index = bisect_right(plan.boundaries, time) - 1
        state = plan.final_state if index >= len(plan.phase_states) else plan.phase_states[index]
        new_phase = state is not previous_state
        if new_phase:
            moving_frames = plan.simulator.recording_moving_frames(state, frame_paths)
        selected_frames = frame_paths if new_phase else tuple(path for path in frame_paths if path in moving_frames)
        frames = plan.simulator.recording_frames(time, state, selected_frames,
                                                moving_frames=moving_frames)
        for node in nodes:
            _charge(work, "recording_pose")
            if not new_phase and node.frame_path not in moving_frames:
                # The complete source dependency law is constant in this
                # phase. Copy the preceding retained immutable output, keeping
                # every key, pose, quaternion lift and interval certificate.
                node.translations.append(node.translations[-1])
                node.rotations_xyzw.append(node.rotations_xyzw[-1])
                continue
            pose = frames[node.frame_path]
            node.translations.append(tuple(pose.position))
            w, x, y, z = pose.orientation
            quaternion = (x, y, z, w)
            if node.rotations_xyzw and sum((Fraction(a) * Fraction(b) for a, b in
                                            zip(node.rotations_xyzw[-1], quaternion)), Fraction(0)) < 0:
                quaternion = tuple(-value for value in quaternion)
            node.rotations_xyzw.append(quaternion)
        previous_state = state
    recording_stage("certification", work=work)
    certificates = interval_certificates(model, options, plan, nodes, geometry, exact, times, work=work)
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
    metadata = {"target_contract": REACH_TARGET, "schema_version": "0.6", "source": source,
        "module": model.module_name, "scene": model.scene_name, "profile": model.profile,
        "coordinates": {"handedness": "right", "up": "+Y", "length_unit": "m", "time_unit": "s"},
        "transform_policy": "all_nodes_are_roots_with_baked_world_poses", **relationship_metadata(model),
        "boundary_states": list(plan.boundary_records), "gravity_m_per_s2": list(model.gravity),
        "motion_authority": "OntoKin semantic evaluator; playback contains no live solver",
        "program": program, "force_profile": force_profile_metadata(), "surface_profile": surface_profile,
        "reach_profile": reach_profile_metadata(), "reach_quantization": quantization}
    report = {"schema_version": "ontokin.glb-report/0.6", "target_contract": REACH_TARGET,
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
    return BakedScene(model.module_name, model.scene_name, exact, times, list(plan.boundaries), nodes,
                      metadata, report, options, contract=REACH_TARGET, schema_version="0.6")


def build_reach_scene(model, *, options=None, source_uri=None, source_sha256=None,
                      check=None, work=None, reach_plan=None):
    from .reach_numeric import ReachExecutionWork, ReachAdmissionError
    from .reach_source import reach_error
    work = work if work is not None else ReachExecutionWork(check=check)
    try:
        return _build_reach_scene(model, options=options, source_uri=source_uri,
                                  source_sha256=source_sha256, work=work, reach_plan=reach_plan)
    except ReachAdmissionError as error:
        if error is work.callback_error:
            raise
        raise reach_error(error.reach_code, str(error), model.span, phase="evaluation",
                          details=error.details, blocks=["delivered"]) from error
