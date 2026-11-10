#!/usr/bin/env python3
"""Independent C191 final-playback checker. No adapter code is imported."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf import Scene, require
from check import certify_shell, swept_overlap

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "frozen"
EXPECT = json.loads((FROZEN / "expectations.json").read_text())
DESIGN = json.loads((FROZEN / "c190-assembly.json").read_text())
CASES = {case["id"]: case for case in EXPECT["cases"]}
LIMIT = EXPECT["limits"]
TIME_ROUNDOFF_S = EXPECT["time_roundoff_s"]
COMMON_TIMES = (np.arange(481, dtype=np.float64) / 240).astype("<f4").astype(float)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def first_threshold(times, gap, threshold):
    if gap[0] <= threshold:
        return float(times[0])
    for index in range(len(times) - 1):
        if gap[index + 1] <= threshold:
            weight = (gap[index] - threshold) / (gap[index] - gap[index + 1])
            return float(times[index] + weight * (times[index + 1] - times[index]))
    return None


def motion_times(scene, name):
    """Recording cadence must belong to the part's actual world-pose chain."""
    index = scene.parts[name][0]
    knots = []
    while index is not None:
        if (index, "translation") in scene.tracks:
            knots.extend(scene.tracks[index, "translation"][0])
        index = scene.parent[index]
    return np.unique(knots)


def evaluate(path, case_id, result):
    case = CASES[case_id]
    parts = {part["id"]: part for part in DESIGN["parts"]}
    scene = Scene(path, set(parts))
    times = scene.knots
    require(np.array_equal(times, COMMON_TIMES), "C191_CADENCE: expected 481 common 240 Hz keys")
    world, _ = scene.transforms(times)
    dt = np.diff(times)
    bounds, moves, speeds = {}, {}, {}
    for name, part in parts.items():
        index, local_triangles, colors = scene.parts[name]
        matrices = world[index]
        basis = matrices[0, :3, :3]
        require(np.isfinite(matrices).all() and np.linalg.det(basis) != 0 and
                np.all(matrices[:, :3, :3] == basis), "C191_BASIS: " + name)
        triangles = 1000 * (local_triangles @ basis.T + matrices[0, :3, 3])
        initial = np.stack([triangles.min((0, 1)), triangles.max((0, 1))])
        expected = np.asarray(part["worldBoundsAt0Mm"], dtype=float).copy()
        if name == "left_stop":
            expected[:, 0] += case["left_stop_near_face_mm"] - 495
        geometry_error = float(np.max(np.abs(initial - expected)))
        dimension_error = float(np.max(np.abs(np.diff(initial, axis=0) - np.diff(expected, axis=0))))
        color_error = float(np.max(np.abs(colors - part["baseColorLinearRGB"])))
        require(geometry_error <= LIMIT["initial_bounds_and_dimensions_mm"] and
                dimension_error <= LIMIT["initial_bounds_and_dimensions_mm"], "C191_GEOMETRY: " + name)
        require(color_error <= LIMIT["linear_color_channel"], "C191_COLOR: " + name)
        shell = certify_shell(name, triangles, initial, int(np.sign(np.linalg.det(basis))))
        displacement = 1000 * (matrices[:, :3, 3] - matrices[0, :3, 3])
        velocity = np.diff(displacement, axis=0) / dt[:, None]
        if part["motion"] == "fixed":
            require(np.max(np.abs(displacement)) <= LIMIT["fixed_part_or_attachment_drift_mm"],
                    "C191_FIXED_DRIFT: " + name)
        else:
            require(np.array_equal(motion_times(scene, name), COMMON_TIMES), "C191_PART_CADENCE: " + name)
            require(np.max(np.abs(displacement[:, 1:])) <= LIMIT["fixed_part_or_attachment_drift_mm"],
                    "C191_TRANSVERSE_DRIFT: " + name)
        bounds[name] = initial + displacement[:, None, :]
        moves[name], speeds[name] = displacement, velocity
        result["parts"][name] = {"bounds_at_0_mm": initial.tolist(), "initial_bounds_error_mm": geometry_error,
            "dimension_error_mm": dimension_error, "color_max_error": color_error,
            "final_displacement_mm": displacement[-1].tolist(), "shell": shell}

    for lane in ("left", "right"):
        car, shoe = lane + "_carriage", lane + "_shoe"
        offset = bounds[shoe].mean(1) - bounds[car].mean(1)
        error = float(np.max(np.abs(offset - offset[0])))
        require(error <= LIMIT["fixed_part_or_attachment_drift_mm"], "C191_ATTACHMENT_DRIFT: " + lane)
        result["attachments"][lane] = {"initial_offset_mm": offset[0].tolist(), "max_drift_mm": error}
        expected_travel = case["left_final_travel_mm"] if lane == "left" else 300
        expected_gap = case["left_final_signed_gap_mm"] if lane == "left" else 15
        gap = bounds[lane + "_stop"][:, 0, 0] - bounds[shoe][:, 1, 0]
        overlap = (np.minimum(bounds[lane + "_stop"][:, 1, 1:], bounds[shoe][:, 1, 1:]) -
                   np.maximum(bounds[lane + "_stop"][:, 0, 1:], bounds[shoe][:, 0, 1:]))
        require(np.all(overlap > 0), "C191_CONTACT_FACE: " + lane)
        for name in (car, shoe):
            require(abs(moves[name][-1, 0] - expected_travel) <= LIMIT["final_travel_mm"],
                    "C191_FINAL_TRAVEL: " + name)
        require(abs(gap[-1] - expected_gap) <= LIMIT["final_signed_gap_mm"], "C191_FINAL_GAP: " + lane)
        result["gaps"][lane] = {"start_mm": float(gap[0]), "final_mm": float(gap[-1]),
            "minimum_mm": float(gap.min()), "max_near_face_penetration_mm": max(0., float(-gap.min()))}
        if lane == "right" or not case["left_shoe_collider_enabled"]:
            nominal = 150 if lane == "right" else 125
            for name in (car, shoe):
                error = float(np.max(np.abs(speeds[name][:, 0] - nominal)))
                require(error <= LIMIT["precontact_and_right_speed_mm_s"], "C191_FEED_SPEED: " + name)
            result["speeds"][lane] = {"all_intervals_nominal_mm_s": nominal,
                "min_mm_s": float(speeds[car][:, 0].min()), "max_mm_s": float(speeds[car][:, 0].max())}
            continue
        ideal = case["ideal_first_contact_s"]
        penetration = max(0., float(-gap.min()))
        require(penetration <= LIMIT["positive_contact_maximum_near_face_penetration_mm"],
                "C191_CONTINUOUS_PENETRATION: affine face gap exceeds 0.5 mm")
        onset = first_threshold(times, gap, LIMIT["final_signed_gap_mm"])
        require(onset is not None and abs(onset - ideal) <= LIMIT["contact_onset_s"], "C191_CONTACT_ONSET")
        pre = times[1:] <= ideal - 1 / 240 + TIME_ROUNDOFF_S
        settle = ideal + LIMIT["postcontact_speed_check_starts_after_ideal_s"]
        post = times[:-1] >= settle - TIME_ROUNDOFF_S
        after_contact = times >= ideal - TIME_ROUNDOFF_S
        lane_report = {}
        for name in (car, shoe):
            velocity = speeds[name][:, 0]
            pre_error = float(np.max(np.abs(velocity[pre] - 125)))
            post_speed = float(np.max(np.abs(velocity[post])))
            retreat = float(np.max(np.maximum.accumulate(moves[name][after_contact, 0]) -
                                   moves[name][after_contact, 0]))
            require(abs(velocity[0] - 125) <= LIMIT["precontact_and_right_speed_mm_s"] and
                    pre_error <= LIMIT["precontact_and_right_speed_mm_s"], "C191_PRECONTACT_SPEED: " + name)
            require(post_speed <= LIMIT["postcontact_speed_mm_s"], "C191_SETTLED_SPEED: " + name)
            require(retreat <= LIMIT["postcontact_rebound_displacement_mm"], "C191_REBOUND: " + name)
            lane_report[name] = {"first_interval_mm_s": float(velocity[0]), "precontact_speed_error_mm_s": pre_error,
                "max_settled_speed_mm_s": post_speed, "maximum_rebound_mm": retreat}
        result["contact"] = {"ideal_s": ideal, "first_gap_band_entry_s": onset,
            "first_zero_gap_s": first_threshold(times, gap, 0), "settling_boundary_s": settle,
            "maximum_penetration_mm": penetration, "interval_extremum_proof": "Affine face gaps attain extrema at interval endpoints",
            "native_collision_event_claimed": False}
        result["speeds"][lane] = lane_report

    pairs = [pair for pair in itertools.combinations(bounds, 2) if set(pair) != {"left_shoe", "left_stop"}]
    require(set(map(frozenset, pairs)) == set(map(frozenset, EXPECT["all_twenty_pairs"])), "C191_PAIR_INVENTORY")
    for first, second in pairs:
        for index in range(len(times) - 1):
            witness = swept_overlap(bounds[first][index], bounds[first][index + 1],
                                    bounds[second][index], bounds[second][index + 1])
            require(witness is None, f"C191_UNRELATED_OVERLAP: {first}/{second} interval {index}")
    result["clearance"] = {"certified_unrelated_pairs": len(pairs), "intervals_per_pair": len(times) - 1,
        "pairs": pairs, "numerical_contact_tolerance_mm": EXPECT["nonoverlap_roundoff_mm"]}
    result["recording"] = {"keys": len(times), "first_s": float(times[0]), "last_s": float(times[-1]),
        "common_key_grid_verified": True}


def measure(path, case):
    result = {"version": "C191-independent-final-playback-1", "case": case, "pass": False,
        "sha256": digest(path), "scope": "Exported final piecewise-linear playback; native causality is separate",
        "parts": {}, "attachments": {}, "gaps": {}, "speeds": {}}
    try:
        evaluate(path, case, result)
        result["pass"] = True
    except (ValueError, OSError, KeyError, IndexError, TypeError, ArithmeticError) as error:
        result["reason"] = str(error)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.candidate, args.case)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in ("case", "pass", "sha256")}, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)
