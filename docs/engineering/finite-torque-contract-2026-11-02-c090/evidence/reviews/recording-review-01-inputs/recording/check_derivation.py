#!/usr/bin/env python3
"""Exact C090 design checks without imports from an OntoKin implementation.

These checks illustrate the mathematical proof in RECORDING.md. They are not
product tests, a replacement for that proof, or an artifact acceptance result.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import platform
from pathlib import Path
import sys


def encode(value):
    if isinstance(value, F):
        return {"numerator": str(value.numerator), "denominator": str(value.denominator)}
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    return value


def run():
    rows = []

    def check(name, condition, **values):
        rows.append({"name": name, "passed": bool(condition), **encode(values)})
        if not condition:
            raise AssertionError(name)

    # w,x,y,z quaternion ordering. Pure axis multiplication is an isometry
    # orthogonal to the input unit quaternion.
    def multiply(p, q):
        w, x, y, z = p
        a, b, c, d = q
        return (w*a-x*b-y*c-z*d, w*b+x*a+y*d-z*c,
                w*c-x*d+y*a+z*b, w*d+x*c-y*b+z*a)

    def dot(p, q):
        return sum((x*y for x, y in zip(p, q)), F(0))

    quaternions = [(F(1), F(0), F(0), F(0)),
                   (F(3, 5), F(4, 5), F(0), F(0)),
                   (F(1, 2), F(1, 2), F(1, 2), F(1, 2))]
    accelerations = [F(-2), F(-1, 512), F(0), F(1, 1024), F(1), F(2), F(7, 4)]
    speeds = [F(-3), F(-1, 1024), F(0), F(1, 2), F(4)]
    for qi, q in enumerate(quaternions):
        check(f"unit-q-{qi}", dot(q, q) == 1)
        for axis in range(3):
            unit_axis = [F(0)] * 4
            unit_axis[axis + 1] = F(1)
            jq = multiply(unit_axis, q)
            check(f"axis-isometry-{qi}-{axis}", dot(jq, jq) == 1 and dot(jq, q) == 0)
            for alpha in accelerations:
                for omega in speeds:
                    second = tuple(alpha*j/2 - omega*omega*x/4 for j, x in zip(jq, q))
                    exact_square = alpha*alpha/4 + omega**4/16
                    upper = abs(alpha)/2 + omega*omega/4
                    check(f"q-second-derivative-{qi}-{axis}-{alpha}-{omega}",
                          dot(second, second) == exact_square <= upper*upper,
                          exact_norm_squared=exact_square, upper_norm=upper)

    for alpha in accelerations:
        for width in [F(1, 8), F(1, 2), F(1), F(2)]:
            for omega in [F(-1), F(0), F(3, 2)]:
                upper = abs(alpha)*width*width/8
                maximum_speed = max(abs(omega), abs(omega + alpha*width))
                for index in range(17):
                    t = width*index/16
                    exact_phase = omega*t + alpha*t*t/2
                    chord = (omega + alpha*width/2)*t
                    difference = exact_phase - chord
                    check(f"phase-chord-{alpha}-{width}-{omega}-{index}",
                          difference == alpha*t*(t-width)/2 and abs(difference) <= upper,
                          difference=difference, upper=upper)
                    check(f"speed-extremum-{alpha}-{width}-{omega}-{index}",
                          abs(omega + alpha*t) <= maximum_speed)
                check(f"phase-midpoint-equality-{alpha}-{width}-{omega}",
                      abs(alpha*(width/2)*(width/2-width)/2) == upper)

    for first_shift in [F(-1, 64), F(0), F(1, 32)]:
        for last_shift in [F(-1, 32), F(0), F(1, 64)]:
            upper = max(abs(first_shift), abs(last_shift))
            for i in range(17):
                u = F(i, 16)
                shift = (1-u)*first_shift + u*last_shift
                check(f"clock-affine-shift-{first_shift}-{last_shift}-{i}", abs(shift) <= upper)

    # An endpoint-only recording loses this quarter-radian interior reversal.
    phase = lambda t: -t + t*t
    check("equal-endpoint-reversal", phase(F(0)) == phase(F(1)) == 0 and phase(F(1, 2)) == F(-1, 4))
    check("reversal-alpha-term-nonzero", F(2, 16) > 0)

    # The C089 large-radius witness is recomputed independently with exact
    # rational lower/upper inequalities. sin(x)>=x-x^3/6 on this small domain.
    rho, alpha, omega, width = F(100), F(1, 512), F(-1, 1024), F(1)
    midpoint_phase = omega/2 + alpha/8
    x = abs(midpoint_phase)/2
    displacement_lower = 2*rho*(x-x**3/6)
    origin_acceleration_upper = rho*(abs(alpha)+max(abs(omega),abs(omega+alpha))**2)
    origin_chord_upper = origin_acceleration_upper*width*width/8
    check("offset-marker-equal-endpoints", omega+alpha/2 == 0)
    check("offset-marker-midphase", midpoint_phase == F(-1, 4096))
    check("offset-marker-orientation-quarter", abs(midpoint_phase) < F(1, 4000))
    check("offset-marker-position-fails", displacement_lower > F(1, 1000), lower=displacement_lower)
    check("offset-marker-radius-bound", origin_chord_upper == F(51225, 2097152), upper=origin_chord_upper)

    for local_radii in [(F(0),), (F(1),), (F(3, 4), F(1, 2)), (F(10), F(20), F(70))]:
        rho = sum(local_radii, F(0))
        for alpha in [F(0), F(1, 512), F(2)]:
            for omega in [F(0), F(1, 1024), F(3)]:
                complete = rho*(alpha+omega*omega)
                sum_edges = sum((r*(alpha+omega*omega) for r in local_radii), F(0))
                check(f"nested-offset-composition-{local_radii}-{alpha}-{omega}", complete == sum_edges)

    # At zero acceleration the extension reduces exactly to the old algebra.
    for width in [F(1, 16), F(1, 2), F(1)]:
        for omega in [F(0), F(1), F(2)]:
            old = omega*omega*width*width/32
            new = F(0)*width*width/16 + old
            check(f"zero-alpha-old-chord-{width}-{omega}", old == new)
            check(f"zero-alpha-old-plan-{width}-{omega}",
                  (F(0)+omega*omega)*width*width/4 == omega*omega*width*width/4)

    packet = Path(__file__).resolve().parents[1]
    quant = json.loads((packet / "recording-quantization.schema.json").read_text())
    cert = quant["properties"]["interval_certificates"]["items"]
    check("closed-certificate-29-fields", cert["additionalProperties"] is False
          and len(cert["properties"]) == 29 and set(cert["required"]) == set(cert["properties"]))
    check("both-alpha-fields-required", all(name in cert["required"] for name in (
        "angular_acceleration_bound_rad_per_s2", "enclosing_angular_acceleration_bound_rad_per_s2")))
    check("quantization-binding", quant["properties"]["schema_version"]["const"] == "ontokin.torque-quantization/0.1")
    check("quantization-shape-closed", quant["additionalProperties"] is False and set(quant["required"]) == set(quant["properties"]))

    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output must be a fresh path")
    rows = run()
    result = {
        "schema_version": "ontokin.c090-recording-design-checks/1",
        "status": "passed",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "production_imports": False,
        "runtime_tests": False,
        "artifact_acceptance": False,
        "scope": "Exact finite design witnesses; the continuous proof is RECORDING.md",
        "assertions": len(rows),
        "rows": rows,
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "assertions": len(rows)}))


if __name__ == "__main__":
    main()
