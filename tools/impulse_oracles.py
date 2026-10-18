"""Independent scalar oracles for the frozen impulse delivery fixtures.

These values describe the already pinned .ok corpus. They are not compiler
inputs, host geometry or an alternative simulation engine. The actual artifact
must come from the Agent accepting and evaluating the complete source bundle.
"""

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/language-design/impulse-v0.1"
ACCEPTANCE_BYTES = (FIXTURES / "acceptance.json").read_bytes()
ACCEPTANCE = json.loads(ACCEPTANCE_BYTES)
CASES = {case["id"]: case for case in ACCEPTANCE["source_cases"]}
DELIVERY_CASES = tuple(case["id"] for case in CASES.values() if case["delivery_required"])


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _multiply(a, b):
    w, x, y, z = a
    v, i, j, k = b
    return [w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
            w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v]


def _turn(axis, radians):
    result = [math.cos(radians/2), 0., 0., 0.]
    result[axis+1] = math.sin(radians/2)
    return result


def expected_pose(object_, seconds):
    """Closed-form fixture arithmetic, independent of production evaluation."""
    case, path = object_["motion"]["fixture"], object_["path"]
    t, dt = float(seconds), max(0., float(seconds)-1)
    identity = [1., 0., 0., 0.]
    if case == "P04":
        if path == "carrier":
            return [min(t, 1), 0., 0.], _turn(2, -2+2*min(t, 1))
        if t < 1:
            angle = -2+2*t
            return [t+.5*math.cos(angle), .5*math.sin(angle), 0.], _turn(2, angle)
        return [1.5+dt, 2*dt-5*dt*dt, 0.], _turn(2, 7*dt)
    if case in ("P08", "P09", "P10"):
        if path == "rack":
            return [0., 0., 0.], identity
        first = path == 'rack.props["first"]'
        speed = (.5 if case == "P09" else 1.) if first else .5
        spin = {"P08": 5., "P09": 2.5, "P10": 1.25}[case] if first else 2.5
        return [0. if first else 3., speed*dt, 0.], _turn(2, spin*dt)
    if case == "P01":
        return [3*dt, 0., 0.], identity
    if case == "P02":
        return [0., dt, 0.], _turn(2, 5*dt)
    if case == "P03":
        return [0., dt, 0.], _multiply(_turn(0, 5*dt), _turn(1, math.pi/2))
    if case == "P07":
        return [0., 5-5*t*t if t < 1 else -5*dt*dt, 0.], identity
    if case == "P11":
        return [0., 8*dt, 0.], _turn(2, 40*dt)
    raise ValueError("No destination oracle is declared for " + case)


def _shape(case, path, keys, mass=2., radius=.5):
    return {
        "path": path, "element_id": ["impulse-demo", "demo", *keys],
        "physical_kind": "sphere_body", "body_mass_kg": mass, "body_radius_m": radius,
        "sections": [
            {"key": "foot", "station_m": 0., "center_xy_m": [0., 0.], "radii_xy_m": [.5, .35], "region": "clay"},
            {"key": "neck", "station_m": 1., "center_xy_m": [.15, 0.], "radii_xy_m": [.3, .2], "region": "paint"},
            {"key": "tip", "station_m": 1.5, "center_xy_m": [.15, 0.], "radii_xy_m": [.2, .1], "region": "paint"},
        ],
        "facets": 16, "caps": "flat", "local_position_m": [0., 0., .1],
        "local_rotation_wxyz": [1., 0., 0., 0.],
        "materials": {
            "clay": {"rgba": [.6, .3, .2, 1.], "metallic": 0., "roughness": .8},
            "paint": {"rgba": [.1, .4, .8, 1.], "metallic": .2, "roughness": .4},
        },
        "expected": {"triangles": 96, "vertices": 288, "triangles_per_region": {"clay": 48, "paint": 48}},
        "motion": {"kind": "impulse_fixture", "fixture": case},
    }


def oracle_for(case):
    if case not in DELIVERY_CASES:
        raise ValueError("This fixture has no promised GLB delivery: " + case)
    empty = []
    if case in ("P08", "P09", "P10"):
        shapes = [_shape(case, 'rack.props["first"]', ["rack", "props", "first"],
                         4. if case == "P09" else 2., 1. if case == "P10" else .5),
                  _shape(case, 'rack.props["second"]', ["rack", "props", "second"], 4.)]
        empty = [{"path": "rack", "element_id": ["impulse-demo", "demo", "rack"],
                  "motion": {"kind": "impulse_fixture", "fixture": case}}]
    else:
        shapes = [_shape(case, "ball", ["ball"])]
        if case == "P04":
            empty = [{"path": "carrier", "element_id": ["impulse-demo", "demo", "carrier"],
                      "motion": {"kind": "impulse_fixture", "fixture": case}}]
    return {
        "schema_version": "ontokin.impulse-fixture-oracle/0.1", "fixture": case,
        "origin": "Independent scalar reading of frozen .ok library and adopted analytic fixture expectations.",
        "acceptance_manifest_sha256": digest(ACCEPTANCE_BYTES),
        "case_ids": CASES[case]["gates"], "program_revision": CASES[case]["program_revision"],
        "shapes": shapes, "empty_objects": empty,
        "frozen_expected": copy.deepcopy(CASES[case]["expected"]),
    }


def sample_requests(case):
    """Retain frozen sides and add deterministic playback/metadata probes."""
    requests = {(Fraction(sample["time_seconds"]), sample["side"]): sample["time_seconds"]
                for sample in CASES[case]["expected"]["samples"]}
    if case in DELIVERY_CASES:
        for i in range(9):
            seconds = str(i/4).removesuffix(".0")
            requests[(Fraction(seconds), "after")] = seconds
        for seconds in ("0", "1", "2"):
            for side in ("before", "after"):
                requests[(Fraction(seconds), side)] = seconds
    return [{"seconds": requests[(seconds, side)], "side": side}
            for seconds, side in sorted(requests, key=lambda item: (item[0], item[1] == "after"))]
