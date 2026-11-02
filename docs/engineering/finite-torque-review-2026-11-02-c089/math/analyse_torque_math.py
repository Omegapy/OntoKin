#!/usr/bin/env python3
"""Independent C089 design witnesses; no OntoKin production imports.

These exact scalar calculations inspect the proposed fixed-axis model. They
are not an adopted conformance corpus, candidate-runtime tests, or evidence
that OntoKin implements finite torque. Expected state tables are literal.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path

BASELINE = "7b6900baa0357ab96c4639ac5c2ebe4e1791833e"
ROOT = f"https://github.com/Omegapy/OntoKin/blob/{BASELINE}/"
CHECKS: list[dict] = []


def exact(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {key: exact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [exact(item) for item in value]
    return value


def equal(label, actual, expected):
    passed = actual == expected
    CHECKS.append({"label": label, "passed": passed,
                   "actual": exact(actual), "expected": exact(expected)})
    if not passed:
        raise AssertionError(label)


@dataclass(frozen=True)
class Interval:
    start: F
    end: F
    torque: F


def inertia(mass: F, radius: F) -> F:
    assert mass > 0 and radius > 0
    return F(2, 5) * mass * radius * radius


def state(moment: F, initial_speed: F, intervals: tuple[Interval, ...],
          time: F, initial_angle: F = F(0)) -> dict:
    """Integrate piecewise constant torque with exact event clocks.

    Midpoints select the active set of each open interval. Endpoint state is
    continuous because these examples contain no angular impulse.
    """
    assert moment > 0 and time >= 0
    boundaries = {F(0), time}
    for event in intervals:
        assert event.start >= 0 and event.end > event.start
        boundaries.update(t for t in (event.start, event.end) if 0 < t < time)
    clocks = sorted(boundaries)
    angle, speed, work = initial_angle, initial_speed, F(0)
    segments = []
    for start, end in zip(clocks, clocks[1:]):
        midpoint = (start + end) / 2
        torque = sum((event.torque for event in intervals
                      if event.start <= midpoint < event.end), F(0))
        acceleration = torque / moment
        duration = end - start
        displacement = speed * duration + acceleration * duration * duration / 2
        old_speed = speed
        angle += displacement
        speed += acceleration * duration
        work += torque * displacement
        segments.append({"start": start, "end": end, "net_torque": torque,
                         "acceleration": acceleration, "initial_speed": old_speed,
                         "final_speed": speed, "angle_change": displacement})
    return {"angle": angle, "speed": speed, "work": work,
            "kinetic_energy_change": moment * (speed * speed - initial_speed * initial_speed) / 2,
            "segments": segments}


def scenario(name, mass, radius, initial_speed, intervals, samples, initial_angle=F(0)):
    moment = inertia(mass, radius)
    results = []
    for time, expected_angle, expected_speed, expected_work in samples:
        actual = state(moment, initial_speed, intervals, time, initial_angle)
        equal(f"{name}@{time}: angle", actual["angle"], expected_angle)
        equal(f"{name}@{time}: speed", actual["speed"], expected_speed)
        equal(f"{name}@{time}: work", actual["work"], expected_work)
        equal(f"{name}@{time}: work-energy", actual["work"], actual["kinetic_energy_change"])
        results.append({"time": time, **actual})
    return {"name": name, "mass_kg": mass, "radius_m": radius,
            "inertia_kg_m2": moment, "initial_speed_rad_per_s": initial_speed,
            "initial_angle_rad": initial_angle,
            "torque_intervals": [vars(event) for event in intervals], "samples": results}


def main() -> dict:
    one = F(1)
    moment = inertia(F(5, 2), one)
    equal("unit moment of inertia", moment, one)
    cases = [
        scenario("spin_up_and_coast", F(5, 2), one, F(0), (Interval(F(0), F(2), F(2)),),
                 [(F(0), F(0), F(0), F(0)), (F(1, 2), F(1, 4), F(1), F(1, 2)),
                  (F(1), F(1), F(2), F(2)), (F(2), F(4), F(4), F(8)),
                  (F(3), F(8), F(4), F(8))]),
        scenario("braking_through_zero_equal_endpoints", F(5, 2), one, F(2),
                 (Interval(F(0), F(2), F(-2)),),
                 [(F(0), F(0), F(2), F(0)), (F(1, 2), F(3, 4), F(1), F(-3, 2)),
                  (F(1), F(1), F(0), F(-2)), (F(3, 2), F(3, 4), F(-1), F(-3, 2)),
                  (F(2), F(0), F(-2), F(0))]),
        scenario("overlapping_torques", F(5, 2), one, F(0),
                 (Interval(F(0), F(3), F(2)), Interval(F(1), F(2), F(-1))),
                 [(F(1), F(1), F(2), F(2)), (F(2), F(7, 2), F(3), F(9, 2)),
                  (F(3), F(15, 2), F(5), F(25, 2)), (F(4), F(25, 2), F(5), F(25, 2))]),
        scenario("exact_cancelling_overlap", F(5, 2), one, F(1, 2),
                 (Interval(F(0), F(2), F(3)), Interval(F(0), F(2), F(-3))),
                 [(F(1), F(1, 2), F(1, 2), F(0)), (F(2), F(1), F(1, 2), F(0)),
                  (F(3), F(3, 2), F(1, 2), F(0))]),
        scenario("different_mass_radius", F(5), F(1, 2), F(0),
                 (Interval(F(0), F(2), F(1)),),
                 [(F(1), F(1), F(2), F(1)), (F(2), F(4), F(4), F(4))]),
        scenario("negative_torque", F(5, 2), one, F(0),
                 (Interval(F(0), F(1), F(-3)),),
                 [(F(1), F(-3, 2), F(-3), F(9, 2)), (F(2), F(-9, 2), F(-3), F(9, 2))]),
        scenario("zero_torque_zero_speed", F(5, 2), one, F(0),
                 (Interval(F(0), F(2), F(0)),),
                 [(F(1), F(1, 4), F(0), F(0)), (F(3), F(1, 4), F(0), F(0))], F(1, 4)),
        scenario("adjacent_acceleration_braking", F(5, 2), one, F(0),
                 (Interval(F(0), F(1), F(2)), Interval(F(1), F(2), F(-2))),
                 [(F(1), F(1), F(2), F(2)), (F(3, 2), F(7, 4), F(1), F(1, 2)),
                  (F(2), F(2), F(0), F(0))]),
    ]
    whole = (Interval(F(0), F(2), F(1)),)
    divided = (Interval(F(0), F(1), F(1)), Interval(F(1), F(2), F(1)))
    segmented = []
    for time in (F(1, 2), F(1), F(3, 2), F(2), F(3)):
        a = state(one, F(1, 3), whole, time)
        b = state(one, F(1, 3), divided, time)
        for field in ("angle", "speed", "work", "kinetic_energy_change"):
            equal(f"equivalent segmentation@{time}: {field}", a[field], b[field])
        segmented.append({"time": time, "whole": a, "segmented": b})

    # The proof is algebraic; this finite grid checks the stated identity and
    # equality at the midpoint for several signs, magnitudes and durations.
    interpolation = []
    for alpha in (F(-3), F(-2), F(0), F(1, 3), F(2)):
        for duration in (F(1, 10), F(1, 2), F(2)):
            theta0, omega0 = F(2, 7), F(-3, 5)
            theta_end = theta0 + omega0 * duration + alpha * duration ** 2 / 2
            bound = abs(alpha) * duration ** 2 / 8
            greatest = F(0)
            for numerator in range(17):
                elapsed = duration * F(numerator, 16)
                theta = theta0 + omega0 * elapsed + alpha * elapsed ** 2 / 2
                chord = theta0 + (theta_end - theta0) * elapsed / duration
                error = theta - chord
                equal(f"chord identity {alpha},{duration},{numerator}",
                      error, alpha * elapsed * (elapsed - duration) / 2)
                equal(f"chord bound {alpha},{duration},{numerator}", abs(error) <= bound, True)
                greatest = max(greatest, abs(error))
            equal(f"midpoint attains chord bound {alpha},{duration}", greatest, bound)
            interpolation.append({"alpha": alpha, "duration": duration,
                                  "max_angle_error": greatest, "analytic_bound": bound})

    # A zero-crossing example proves that endpoint angle alone cannot bound
    # motion. The full interval has zero displacement and two radians travel.
    equal("reversal endpoint displacement", F(2) * F(2) - F(2) ** 2, F(0))
    equal("reversal interior angle", F(2) * F(1) - F(1) ** 2, F(1))
    equal("reversal absolute travel", F(1) + F(1), F(2))
    # A conservative endpoint-speed travel bound is max(abs(w0),abs(w1))*h.
    equal("reversal conservative travel bound", max(abs(F(2)), abs(F(-2))) * F(2), F(4))

    axis = (0.6, 0.8, 0.0)
    a = tuple(F(component) for component in axis)
    alpha = tuple(2 * component for component in a)
    elapsed = F(1, 10)
    omega_exact = tuple(component + acceleration * elapsed for component, acceleration in zip(a, alpha))
    omega_rounded = tuple(float(component) for component in omega_exact)
    rounded = tuple(F(component) for component in omega_rounded)

    def cross(left, right):
        return (left[1] * right[2] - left[2] * right[1],
                left[2] * right[0] - left[0] * right[2],
                left[0] * right[1] - left[1] * right[0])

    equal("initial speed exactly collinear with stored axis", cross(a, a), (F(0), F(0), F(0)))
    equal("acceleration exactly collinear with stored axis", cross(a, alpha), (F(0), F(0), F(0)))
    equal("exact updated speed remains collinear", cross(a, omega_exact), (F(0), F(0), F(0)))
    expected_residual = F(1080863910568919, 81129638414606681695789005144064)
    equal("rounded updated speed loses exact collinearity", cross(a, rounded),
          (F(0), F(0), expected_residual))
    equal("rounding residual is nonzero", expected_residual != 0, True)
    axis_witness = {"axis_binary64": axis, "axis_hex": [x.hex() for x in axis],
                    "binary64_hypot": math.hypot(*axis),
                    "axis_exact_squared_norm": sum((x*x for x in a), F(0)),
                    "initial_speed": a, "angular_acceleration": alpha, "elapsed": elapsed,
                    "exact_updated_speed": omega_exact, "rounded_updated_speed": omega_rounded,
                    "rounded_updated_speed_hex": [x.hex() for x in omega_rounded],
                    "exact_cross_product": cross(a, rounded)}

    # Reproduce only the Fraction -> binary64 scalar formula visible in the
    # baseline; no OntoKin production module is imported or executed here.
    p0, v0, acceleration = F(0), F(1), F(0)
    split_time, target_time = F(3, 10), F(2, 5)
    direct = float(p0 + v0 * target_time + acceleration * target_time ** 2 / 2)
    stored_p = float(p0 + v0 * split_time + acceleration * split_time ** 2 / 2)
    stored_v = float(v0 + acceleration * split_time)
    remainder = target_time - split_time
    reanchored = float(F(stored_p) + F(stored_v) * remainder + acceleration * remainder ** 2 / 2)
    equal("uninterrupted translation hex", direct.hex(), "0x1.999999999999ap-2")
    equal("gratuitously reanchored translation hex", reanchored.hex(), "0x1.9999999999999p-2")
    equal("translation difference", F(reanchored) - F(direct), F(-1, 18014398509481984))
    equal("translation one-ULP difference", F(direct) - F(reanchored), F(math.ulp(direct)))
    translation_witness = {"position0_m": p0, "velocity0_m_per_s": v0,
                           "acceleration_m_per_s2": acceleration, "split_time_s": split_time,
                           "target_time_s": target_time, "direct_position": direct,
                           "direct_hex": direct.hex(), "stored_split_position": stored_p,
                           "stored_split_hex": stored_p.hex(), "reanchored_position": reanchored,
                           "reanchored_hex": reanchored.hex(),
                           "difference_m": F(reanchored) - F(direct)}

    return exact({"status": "passed", "scope": "independent analytic design witnesses only",
                  "production_runtime_tested": False, "torque_adopted": False,
                  "release_input_freeze": False, "baseline_commit": BASELINE,
                  "python": sys.version, "platform": platform.platform(),
                  "sources": [ROOT + "ontokin/evaluator.py", ROOT + "ontokin/force_runtime.py",
                              ROOT + "ontokin/force_export.py",
                              ROOT + "docs/engineering/keyed-membership-2026-11-02-c088/NEXT-TASK.md"],
                  "scenarios": cases, "equivalent_segmentation": segmented,
                  "interpolation_grid": interpolation, "axis_rounding_witness": axis_witness,
                  "translation_anchor_witness": translation_witness,
                  "check_count": len(CHECKS), "checks": CHECKS})


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 analyse_torque_math.py FRESH_OUTPUT.json")
    report = main()
    report["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output = Path(sys.argv[1])
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "check_count": report["check_count"],
                      "output": str(output), "scope": report["scope"]}, sort_keys=True))
