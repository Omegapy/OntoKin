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


def rational_record(value) -> dict[str, str]:
    value = Fraction(value)
    if value < 0:
        raise ValueError("A recording clock must be nonnegative")
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


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
        before = ReachSimulator.snapshot(simulator, time, "before")
        simulator.advance(time, "after")
        after = ReachSimulator.snapshot(simulator, time, "after")
        records.append(_boundary_record(time, before, after, simulator.incoming_releases_at(time)))
        times.append(time)
        if time == end:
            break
        following = simulator._next_boundary()
        stop = end if following is None or following > end else following
        if stop <= time:
            _fail("OKE-E-PHASE-COVERAGE", "The validated prefix did not advance to a later boundary.", model=model)
        recording_stage("planning_phase", work=work)
        source = simulator.phase_bounds(time, stop)["frames"]
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
            # A stricter initial allocation leaves explicit room for the
            # actual controlled destination approximation and endpoint terms.
            curvature = bound.acceleration / 8 + radius * bound.angular_speed ** 2 / 4
            steps = max(steps, _ceil(width * bound.angular_speed / ANGULAR_STEP),
                        _ceil_sqrt(width ** 2 * bound.angular_speed ** 2 * 4 / rotation_tolerance),
                        _ceil_sqrt(width ** 2 * curvature * 16 / position_tolerance))
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
        item = {"authored_seconds": rational_record(time), "stored_seconds": stored,
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


def interval_certificates(model, options, plan, nodes, geometry_bounds, exact, times, *, work):
    """Produce a complete conservative row for every carrier/key pair."""
    if (len(exact) - 1) * len(nodes) > MAX_CERTIFICATES:
        _fail("OKE-E-CERTIFICATE-BUDGET", "Complete interval certificate coverage exceeds its cap.", model=model, kind="resource")
    result = []
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
        for node, (radius, vertex_error) in zip(nodes, geometry_bounds):
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
            nsp = _source_max(plan, numeric_selected, frame, "position_error_m")
            nsr = _source_max(plan, numeric_selected, frame, "rotation_error_rad")
            p = [_stored_vector(node.translations[k], model) for k in (index, index + 1)]
            q = [_stored_vector(node.rotations_xyzw[k], model) for k in (index, index + 1)]
            magnitude = max(sum((abs(Fraction(value)) for value in point), Fraction(0)) for point in p)
            ep = max(norm_upper((Fraction(stored) - Fraction(actual) for stored, actual in zip(value, node.translations[k])), work=work)
                     for value, k in zip(p, (index, index + 1))) + nsp
            eq = max(norm_upper((Fraction(stored) - Fraction(actual) for stored, actual in zip(
                normalized_quaternion(value, work=work), normalized_quaternion(node.rotations_xyzw[k], work=work))), work=work)
                     for value, k in zip(q, (index, index + 1))) + 2 * NORMALIZATION_ERROR + nsr
            arc = quaternion_arc_upper(*q, work=work)
            ndp, ndr = destination_numeric_bounds(arc, magnitude, radius, vertex_error, work=work)
            totals = complete_interval_bounds(width=right - left, bound=bound, enclosing=enclosing,
                radius=radius, vertex_error=vertex_error, endpoint_position_error=ep,
                endpoint_quaternion_error=eq, stored_arc=arc, time_shift=shift,
                source_position_error=nsp, source_rotation_error=nsr,
                destination_position_error=ndp, destination_rotation_error=ndr)
            if totals["total_position_bound_m"] > Fraction(options.position_tolerance_m) or totals["total_rotation_bound_rad"] > Fraction(options.rotation_tolerance_rad):
                _fail("OKE-E-NUMERIC-BOUND", "The complete continuous recording bound exceeds the requested tolerance.", model=model,
                      details={"carrier": node.name, "left_key_index": index,
                               **{name: str(value) for name, value in totals.items()}})
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
            rounded_totals = complete_interval_bounds(width=right - left, bound=rounded_bound,
                enclosing=rounded_enclosing, radius=q("landmark_radius_m"),
                vertex_error=q("local_vertex_error_bound_m"),
                endpoint_position_error=q("max_endpoint_position_error_m"),
                endpoint_quaternion_error=q("max_endpoint_unit_quaternion_error"),
                stored_arc=q("stored_quaternion_arc_upper_rad"), time_shift=q("max_endpoint_time_shift_s"),
                source_position_error=q("source_numeric_position_bound_m"),
                source_rotation_error=q("source_numeric_rotation_bound_rad"),
                destination_position_error=q("destination_numeric_position_bound_m"),
                destination_rotation_error=q("destination_numeric_rotation_bound_rad"))
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
            if (q("total_position_bound_m") > Fraction(options.position_tolerance_m)
                    or q("total_rotation_bound_rad") > Fraction(options.rotation_tolerance_rad)):
                _fail("OKE-E-NUMERIC-BOUND", "Outward serialized bounds exceed the requested tolerance.", model=model)
            result.append({"left_key_index": index, "right_key_index": index + 1,
                           "carrier": _carrier_ref(node), "source_phase_indices": list(selected),
                           "h_authored_seconds": rational_record(right - left), "h_stored_seconds": rational_record(s1 - s0),
                           **quantities})
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


def _build_reach_scene(model, *, options, source_uri, source_sha256, work):
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
    plan = reach_prefix_plan(model, end, work=work)
    recording_stage("geometry", work=work)
    nodes = _nodes(model, options, check=work.tick)
    if not nodes:
        _fail("OKE-E-EMPTY-SCENE", "Reach recording requires at least one actual object occurrence.", model=model, kind="unsupported")
    geometry = node_geometry_bounds(model, nodes, work=work)
    exact, times, retained = reach_timeline(model, options, plan, nodes, geometry, work=work)
    recording_stage("sampling", work=work)
    for time in exact:
        _charge(work, "recording_sample")
        index = bisect_right(plan.boundaries, time) - 1
        state = plan.final_state if index >= len(plan.phase_states) else plan.phase_states[index]
        _, frames = plan.simulator._kinematics(time, state)
        for node in nodes:
            _charge(work, "recording_pose")
            pose = frames[node.frame_path]
            node.translations.append(tuple(pose.position))
            w, x, y, z = pose.orientation
            quaternion = (x, y, z, w)
            if node.rotations_xyzw and sum((Fraction(a) * Fraction(b) for a, b in
                                            zip(node.rotations_xyzw[-1], quaternion)), Fraction(0)) < 0:
                quaternion = tuple(-value for value in quaternion)
            node.rotations_xyzw.append(quaternion)
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
                      check=None, work=None):
    from .reach_numeric import ReachExecutionWork, ReachAdmissionError
    from .reach_source import reach_error
    work = work if work is not None else ReachExecutionWork(check=check)
    try:
        return _build_reach_scene(model, options=options, source_uri=source_uri,
                                  source_sha256=source_sha256, work=work)
    except ReachAdmissionError as error:
        if error is work.callback_error:
            raise
        raise reach_error(error.reach_code, str(error), model.span, phase="evaluation",
                          details=error.details, blocks=["delivered"]) from error
