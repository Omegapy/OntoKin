"""Independent scalar expectations for source-authored force destination cases.

No compiler, evaluator, geometry builder, or exporter is imported here. The
closed-form pulse arithmetic supplies checks only; .ok source supplies every
input to the implementation. The original adopted fixtures are never edited.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/language-design/force-v0.1"
ACCEPTANCE_BYTES = (FIXTURES / "acceptance.json").read_bytes()
ACCEPTANCE = json.loads(ACCEPTANCE_BYTES)
CASES = {case["id"]: case for case in ACCEPTANCE["source_cases"]}
FIXTURE_INPUT_BYTES = {name: (FIXTURES / name).read_bytes() for name in
                       ("acceptance.json", "reviewed-acceptance.json", "source-errata.json", "ADOPTION.md")}
SOURCE_ERRATA = json.loads(FIXTURE_INPUT_BYTES["source-errata.json"])
ADOPTED_CASES = copy.deepcopy(CASES)
for _correction in SOURCE_ERRATA["sample_corrections"]:
    _row = next(row for row in ADOPTED_CASES[_correction["id"]]["expected_samples"]
                if all(row[key] == _correction[key] for key in ("time", "side", "target")))
    assert all(_row[key] == value for key, value in _correction["old"].items()), "Adopted erratum precondition changed"
    _row.update(copy.deepcopy(_correction["new"]))
FROZEN_DELIVERY_CASES = tuple(f"P{i:02}" for i in range(1, 18)) + ("P19", "P21", "P22")
HELD_OUT_CASES = ("held-out-oblique", "held-out-spin", "held-out-prefix")
DELIVERY_CASES = FROZEN_DELIVERY_CASES + HELD_OUT_CASES


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def fraction(value):
    if isinstance(value, dict):
        return Fraction(int(value["numerator"]), int(value["denominator"]))
    return Fraction(value)


def seconds(value):
    """Exact finite decimal; float operands keep their source binary64 value."""
    value = fraction(value)
    numerator, denominator = value.numerator, value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2; twos += 1
    while denominator % 5 == 0:
        denominator //= 5; fives += 1
    if denominator != 1:
        raise ValueError("The fixture clock must have a finite decimal expansion")
    places = max(twos, fives)
    integer = abs(numerator) * 2 ** (places - twos) * 5 ** (places - fives)
    sign = "-" if numerator < 0 else ""
    if not places:
        return sign + str(integer)
    digits = str(integer).rjust(places + 1, "0")
    return (sign + digits[:-places] + "." + digits[-places:]).rstrip("0").rstrip(".")


def force(key, start, duration, vector, *, target="ball", sequence=0):
    start, duration = fraction(start), fraction(duration)
    return {"key": key, "target": target, "start_seconds": seconds(start),
            "duration_seconds": seconds(duration), "end_seconds": seconds(start + duration),
            "vector_n": list(vector), "sequence_index": sequence}


def impulse(time, vector, point=(0, 0, 0), *, target="ball", sequence=0):
    return {"time_seconds": seconds(time), "vector_n_s": list(vector),
            "point_self_m": list(point), "target": target, "sequence_index": sequence}


def case_spec(name):
    """A separate scalar reading of the finite source fixtures, not evaluation."""
    spec = {"fixture": name, "mass_kg": 2., "radius_m": .5, "position_m": [0., 0., 0.],
            "velocity_m_per_s": [0., 0., 0.], "gravity_m_per_s2": [0., 0., 0.],
            "forces": [], "impulses": [], "end_seconds": "3", "fps": 12.}
    if name == "P01": spec["forces"] = [force("push", 1, 1, [4, 0, 0])]
    elif name == "P02":
        spec.update(end_seconds="4", forces=[force("a", 0, 2, [4, 0, 0]), force("b", 1, 2, [-2, 0, 0])])
    elif name == "P03": spec["forces"] = [force("a", 0, 2, [4, 0, 0]), force("b", 0, 2, [-4, 0, 0], sequence=1)]
    elif name == "P04": spec["forces"] = [force("a", 0, 1, [4, 0, 0]), force("b", 1, 1, [4, 0, 0])]
    elif name == "P05": spec.update(velocity_m_per_s=[3, 0, 0], forces=[force("push", 1, 1, [0, 0, 0])])
    elif name == "P06": spec.update(gravity_m_per_s2=[0, -10, 0], forces=[force("push", 1, 1, [0, 20, 0])])
    elif name == "P07": spec.update(forces=[force("a", 0, 2, [4, 0, 0])], impulses=[impulse(1, [0, 2, 0], [.5, 0, 0])])
    elif name == "P08": spec.update(forces=[force("a", 0, 1, [4, 0, 0])], impulses=[impulse(1, [2, 0, 0])])
    elif name == "P09":
        spec.update(gravity_m_per_s2=[0, -10, 0], forces=[force("push", 1, 1, [2, 20, 0], sequence=1)],
                    release_seconds="1", fps=60.)
    elif name in ("P10", "P11", "P12", "P13"):
        spec.update(mass_kg=4. if name == "P11" else 2., generated=True,
                    forces=[force("push", 1, .5 if name == "P13" else 1,
                                  [8 if name == "P12" else 4, 0, 0], target='rack.props["first"]'),
                            force("sibling", 1, 1, [4, 0, 0], target='rack.props["second"]', sequence=1)])
    elif name == "P14": spec.update(end_seconds="2", forces=[force("push", 0, 1, [4, 0, 0])])
    elif name == "P15": spec.update(end_seconds="2", forces=[force("push", 2, 1, [4, 0, 0])])
    elif name == "P16": spec.update(end_seconds="1", forces=[force("push", .1, .2, [4, 0, 0])])
    elif name == "P17": spec.update(end_seconds="2", forces=[force("push", 1, 5, [4, 0, 0])])
    elif name == "P19":
        spec.update(end_seconds="2", mass_kg=1e308,
                    forces=[force("a", 0, 1, [1e308, 0, 0]), force("b", 0, 1, [1e308, 0, 0], sequence=1),
                            force("c", 0, 1, [-1e308, 0, 0], sequence=2)])
    elif name == "P21":
        spec.update(end_seconds="1", mass_kg=.5,
                    forces=[force("early", 0, 1, [1, 0, 0]), force("late", 2, 1, [1e308, 0, 0])])
    elif name == "P22":
        spec.update(end_seconds="2.5", mass_kg=3.5, velocity_m_per_s=[.2, -.1, .3],
                    forces=[force("push", .5, 1.25, [1, 3, -2])])
    elif name == "held-out-oblique":
        spec.update(end_seconds="2.5", mass_kg=5., radius_m=.75, position_m=[1, -.5, 2],
                    velocity_m_per_s=[-.4, .2, .1], gravity_m_per_s2=[.3, -.7, .2],
                    forces=[force("slant", .375, 1.125, [3, -4, 2]), force("cross", 1.125, .75, [-1, 2, 3])])
    elif name == "held-out-spin":
        spec.update(end_seconds="2.25", gravity_m_per_s2=[0, -2, 0],
                    forces=[force("drive", 0, .75, [12, 2, 0]), force("brake", .75, 1.25, [-8, 0, 0])],
                    impulses=[impulse(.25, [0, 16, 0], [.5, 0, 0])])
    elif name == "held-out-prefix":
        spec.update(end_seconds="1", declared_duration_seconds="4", mass_kg=3.,
                    forces=[force("still-active", .125, 2, [3, -6, 1])],
                    impulses=[impulse(3, [0, 1e308, 0], [.5, 0, 0])])
    else:
        raise ValueError("No independent destination oracle for " + name)
    if name in CASES:
        assert seconds(CASES[name]["request_horizon"]) == spec["end_seconds"]
    return spec


SECTIONS = [
    {"key": "foot", "station_m": 0., "center_xy_m": [0., 0.], "radii_xy_m": [.5, .35], "region": "clay"},
    {"key": "neck", "station_m": 1., "center_xy_m": [.15, 0.], "radii_xy_m": [.3, .2], "region": "paint"},
    {"key": "tip", "station_m": 1.5, "center_xy_m": [.15, 0.], "radii_xy_m": [.2, .1], "region": "paint"},
]
MATERIALS = {"clay": {"rgba": [.6, .3, .2, 1.], "metallic": 0., "roughness": .8},
             "paint": {"rgba": [.1, .4, .8, 1.], "metallic": .2, "roughness": .4}}


def object_oracle(spec, path):
    motion = copy.deepcopy(spec)
    motion["kind"] = "force_pulses"
    if path == 'rack.props["second"]':
        motion.update(mass_kg=4., position_m=[3., 0., 0.])
    if path == "rack": motion["kind"] = "fixed"
    if path == "carrier": motion["kind"] = "release_carrier"
    if path.startswith("rack.props"):
        keys = ["rack", "props", "first" if '"first"' in path else "second"]
    else:
        keys = [path]
    item = {"path": path, "element_id": ["force-demo", "demo", *keys], "motion": motion}
    if path not in ("rack", "carrier"):
        item.update(physical_kind="sphere_body", body_mass_kg=motion["mass_kg"], body_radius_m=motion["radius_m"],
                    sections=copy.deepcopy(SECTIONS), materials=copy.deepcopy(MATERIALS), facets=16, caps="flat",
                    local_position_m=[0., 0., .1], local_rotation_wxyz=[1., 0., 0., 0.],
                    expected={"triangles": 96, "vertices": 288, "triangles_per_region": {"clay": 48, "paint": 48}})
    return item


def oracle_for(name):
    spec = case_spec(name)
    paths = ['rack.props["first"]', 'rack.props["second"]'] if spec.get("generated") else ["ball"]
    empty = ["rack"] if spec.get("generated") else ["carrier"] if name == "P09" else []
    return {"schema_version": "ontokin.force-fixture-oracle/0.1", "fixture": name,
            "origin": "Independent scalar source reading and analytic constant-acceleration pulse arithmetic; never an exporter input.",
            "acceptance_manifest_sha256": digest(ACCEPTANCE_BYTES),
            "fixture_inputs": {key: digest(raw) for key, raw in FIXTURE_INPUT_BYTES.items()},
            "frozen_fixture": name in CASES, "end_seconds": spec["end_seconds"],
            "case_ids": ["F11"],
            "specification": spec, "shapes": [object_oracle(spec, path) for path in paths],
            "empty_objects": [object_oracle(spec, path) for path in empty],
            "frozen_expected": copy.deepcopy(CASES[name]["expected_samples"]) if name in CASES else [],
            "adopted_expected": copy.deepcopy(ADOPTED_CASES[name]["expected_samples"]) if name in CASES else [],
            "adopted_sample_corrections": [copy.deepcopy(row) for row in SOURCE_ERRATA["sample_corrections"] if row["id"] == name]}


def expected_pose(object_, time):
    """Closed-form pulse superposition, independent of the production solver."""
    motion, path, t = object_["motion"], object_["path"], float(time)
    if motion["kind"] == "fixed": return [0., 0., 0.], [1., 0., 0., 0.]
    if motion["kind"] == "release_carrier":
        angle = -2 + 2 * min(t, 1.)
        return [min(t, 1.), 0., 0.], [math.cos(angle / 2), 0., 0., math.sin(angle / 2)]
    if motion.get("release_seconds") is not None:
        if t < 1:
            angle = -2 + 2 * t
            return [t + .5 * math.cos(angle), .5 * math.sin(angle), 0.], [math.cos(angle / 2), 0., 0., math.sin(angle / 2)]
        dt = t - 1
        position = [1.5 + dt, dt - 5 * dt * dt, 0.]
        angle = 2 * dt
    else:
        position = [p + v * t + .5 * g * t * t for p, v, g in
                    zip(motion["position_m"], motion["velocity_m_per_s"], motion["gravity_m_per_s2"])]
        angle = 0.
    for item in motion["forces"]:
        if item["target"] != path or fraction(time) <= fraction(item["start_seconds"]): continue
        elapsed = t - float(item["start_seconds"])
        duration = float(item["duration_seconds"])
        # Avoid subtracting nearly equal large squares after completion.
        distance_factor = .5 * elapsed * elapsed if elapsed <= duration else duration * (elapsed - .5 * duration)
        for axis in range(3):
            acceleration = float(Fraction(item["vector_n"][axis]) / Fraction(motion["mass_kg"]))
            position[axis] += acceleration * distance_factor
    for item in motion["impulses"]:
        if item["target"] != path or fraction(time) <= fraction(item["time_seconds"]): continue
        dt = t - float(item["time_seconds"])
        for axis in range(3): position[axis] += item["vector_n_s"][axis] / motion["mass_kg"] * dt
        # All declared finite impulse cases have identity orientation at their
        # sole application and a Z-directed lever cross momentum.
        x, y, z = item["point_self_m"]; jx, jy, jz = item["vector_n_s"]
        assert y * jz - z * jy == 0 and z * jx - x * jz == 0
        inertia = .4 * motion["mass_kg"] * motion["radius_m"] ** 2
        angle += (x * jy - y * jx) / inertia * dt
    return position, [math.cos(angle / 2), 0., 0., math.sin(angle / 2)]


def boundary_times(name):
    spec = case_spec(name); end = fraction(spec["end_seconds"])
    times = {Fraction(0), end}
    for item in spec["forces"]:
        times.update(fraction(item[key]) for key in ("start_seconds", "end_seconds") if fraction(item[key]) <= end)
    for item in spec["impulses"]:
        if fraction(item["time_seconds"]) <= end: times.add(fraction(item["time_seconds"]))
    if spec.get("release_seconds"): times.add(fraction(spec["release_seconds"]))
    return [seconds(t) for t in sorted(times)]


def sample_requests(name):
    end = fraction(case_spec(name)["end_seconds"])
    requests = {(fraction(t), side) for t in boundary_times(name) for side in ("before", "after")}
    if name in CASES:
        requests.update((fraction(row["time"]), row["side"]) for row in CASES[name]["expected_samples"])
    for i in range(17): requests.add((end * Fraction(i, 16), "after"))
    return [{"time_seconds": seconds(t), "side": side}
            for t, side in sorted(requests, key=lambda pair: (pair[0], pair[1] == "after"))]
