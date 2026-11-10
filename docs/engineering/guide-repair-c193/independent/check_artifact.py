#!/usr/bin/env python3
"""C193 source, sample, peak-vertex and unchanged continuous-gate audit.

Imports only the historical independent readers. No producer code is imported.
New backend bytes are explicit input and must have a separately reviewed hash.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
HISTORICAL = REPO / "docs/engineering/guided-contact-c191/independent"
sys.path.insert(0, str(HISTORICAL / "checker"))
from c190_glb_difference import array, compare, decode, states
from audit_mapping import audit as historical_mapping_audit
import measure_c191

EXPECT = json.loads((HERE / "frozen/expectations.json").read_text())
CASES = {row["id"]: row for row in EXPECT["cases"]}
CASES["N1"] = {"id": "N1", "left_stop_near_face_mm": 372.5,
    "left_shoe_collider_enabled": False, "ideal_first_contact_s": None,
    "left_final_travel_mm": 250, "left_final_signed_gap_mm": -57.5}
PARTS = set(json.loads((HISTORICAL / "source-fixtures/A-canonical.json").read_text())["parts"])
G = np.array([[1., 0, 0, 0], [0, 0, 1., 0], [0, -1., 0, 0], [0, 0, 0, 1.]])
TIMES = (np.arange(481, dtype=float) / 240).astype("<f4").astype(float)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_frozen(repo=REPO):
    checked = []
    for row in json.loads((HERE / "frozen/FREEZE.json").read_text())["files"]:
        path = HERE / "frozen" / row["path"]
        require(digest(path) == row["sha256"] and path.stat().st_size == row["bytes"],
                "C193 freeze differs: " + str(path))
    for row in json.loads((HERE / "frozen/inherited-hashes.json").read_text())["files"]:
        path = repo / row["path"]
        require(digest(path) == row["sha256"] and path.stat().st_size == row["bytes"],
                "Historical input differs: " + row["path"])
        checked.append(row["path"])
    return {"passed": True, "historical_files_verified": len(checked)}


def expected_source(case, binding, backend_sha256, source_binding="c191-experimental-0.1"):
    source = json.loads((HISTORICAL / "source-fixtures/A-canonical.json").read_text())
    source["parts"]["left_stop"]["at_mm"][0] = case["left_stop_near_face_mm"]
    source["colliders"]["contact.left_shoe"]["enabled"] = case["left_shoe_collider_enabled"]
    source["backend"] = binding
    source["backend_sha256"] = backend_sha256
    source["source_binding"] = source_binding
    return source


def check_source(source, case, backend, backend_sha256, source_binding="c191-experimental-0.1"):
    expected = expected_source(case, backend["binding"], backend_sha256, source_binding)
    require(source == expected, "Canonical source differs from independently frozen design/case/binding")
    require(set(source["bodies"]) == {"body.left", "body.right"}, "Moving mass owner inventory")
    require(sum(b["mass_kg"] for b in source["bodies"].values()) == 2, "Moving mass must total 2 kg")
    require(all(b["authority"] == "solver" for b in source["bodies"].values()), "Solver authority required")
    return {"passed": True, "source_design_matches_frozen_case": True,
            "moving_mass_kg": 2, "body_owners": ["body.left", "body.right"],
            "backend_binding": backend["binding"], "backend_sha256": backend_sha256}


def rotation_measure(r):
    skew = np.array([r[2, 1] - r[1, 2], r[0, 2] - r[2, 0], r[1, 0] - r[0, 1]]) / 2
    length = np.linalg.norm(skew)
    angle = np.arctan2(length, (np.trace(r) - 1) / 2)
    return float(angle), (skew / length).tolist() if length else [0., 0., 0.]


def diagnose(artifact):
    """Measure recorded facts without interpreting a geometric gap as contact telemetry."""
    raw, raw_bin = decode(artifact / "raw.glb")
    final, final_bin = decode(artifact / "final.glb")
    native = json.loads((artifact / "native-transforms.json").read_text())
    require(len(native) == 481, "Exactly 481 native samples required")
    require(all(row["frame"] == i and row["time_s"] == i / 240 for i, row in enumerate(native)),
            "Native frame/time sequence differs")
    require(all(set(row["matrices_blender_m"]) == PARTS for row in native), "Native part identity inventory")
    raw_states, final_states = states(raw, raw_bin, TIMES), states(final, final_bin, TIMES)
    matrices = {name: G @ np.array([r["matrices_blender_m"][name] for r in native]) @ G.T for name in PARTS}
    require(all(np.isfinite(m).all() for m in matrices.values()), "Nonfinite native matrix")
    require(all(np.array_equal(m[:, 3, :], np.broadcast_to([0, 0, 0, 1], (481, 4)))
                for m in matrices.values()), "Non-affine native matrix")
    named = {n["name"]: n for n in raw["nodes"] if "mesh" in n}
    peaks = {}
    for name in sorted(PARTS):
        node = named[name]
        local = np.concatenate([array(raw, raw_bin, p["attributes"]["POSITION"])
            for p in raw["meshes"][node["mesh"]]["primitives"]])
        matrix = matrices[name]
        native_vertices = 1000 * (np.einsum("tij,vj->tvi", matrix[:, :3, :3], local)
                                + matrix[:, None, :3, 3])
        final_vertices = final_states[name]["verticesMm"]
        error = native_vertices - final_vertices
        norms = np.linalg.norm(error, axis=2)
        frame, vertex = map(int, np.unravel_index(np.argmax(norms), norms.shape))
        peaks[name] = {"distance_mm": float(norms[frame, vertex]), "frame": frame,
            "native_time_s": frame / 240, "glb_time_s": float(TIMES[frame]), "vertex_index": vertex,
            "local_mesh_vertex_mm": (1000 * local[vertex]).tolist(),
            "native_world_vertex_mm": native_vertices[frame, vertex].tolist(),
            "final_world_vertex_mm": final_vertices[frame, vertex].tolist(),
            "native_minus_final_mm": error[frame, vertex].tolist()}
        if name.startswith(("left_", "right_")) and not name.endswith("stop"):
            lane = name.split("_", 1)[0]
            car = matrices[lane + "_carriage"]
            local_body = np.linalg.inv(car[0]) @ matrix[0] @ np.r_[local[vertex], 1]
            rotation = 1000 * (car[frame, :3, :3] - np.eye(3)) @ local_body[:3]
            translation = 1000 * np.r_[0., car[frame, 1:3, 3] - car[0, 1:3, 3]]
            peaks[name].update(body_local_vertex_mm=(1000 * local_body[:3]).tolist(),
                body_rotation_displacement_mm=rotation.tolist(),
                body_transverse_displacement_mm=translation.tolist(),
                reconstruction_roundoff_mm=(error[frame, vertex] - rotation - translation).tolist())
    lanes = {}
    source = json.loads((artifact / "canonical-input.json").read_text())
    stop = source["parts"]["left_stop"]["at_mm"][0]
    ideal = (stop - 180) / 125
    center_frame = round(ideal * 240)
    for lane in ("left", "right"):
        car = matrices[lane + "_carriage"]
        transverse = 1000 * (car[:, 1:3, 3] - car[0, 1:3, 3])
        norms = np.linalg.norm(transverse, axis=1)
        rotations = [rotation_measure(r) for r in car[:, :3, :3]]
        angles = np.array([r[0] for r in rotations])
        transverse_peak, angular_peak = int(norms.argmax()), int(angles.argmax())
        frames = sorted(set(range(max(0, center_frame - 3), min(481, center_frame + 9)))
                        | {transverse_peak, angular_peak})
        lanes[lane] = {"maximum_center_transverse_mm": float(norms.max()),
            "center_transverse_peak_frame": transverse_peak,
            "maximum_rotation_deg": float(np.rad2deg(angles.max())),
            "rotation_peak_frame": angular_peak,
            "near_contact_and_peak_samples": [{"frame": i, "time_s": i / 240,
                "x_travel_mm": float(1000 * (car[i, 0, 3] - car[0, 0, 3])),
                "center_transverse_mm": transverse[i].tolist(),
                "rotation_deg": float(np.rad2deg(angles[i])), "rotation_axis_source": rotations[i][1]}
                for i in frames]}
    global_peak = max(peaks, key=lambda name: peaks[name]["distance_mm"])
    return {"version": "C193-independent-native-residual-1", "peak_part": global_peak,
        "peak": peaks[global_peak], "part_peaks": peaks, "lanes": lanes,
        "ideal_contact_s": ideal, "ideal_contact_frame_coordinate": ideal * 240,
        "native_sample_count": 481,
        "scope": "Native captured world matrices and recorded GLB vertices. No direct Bullet velocity, contact impulse, manifold, or unrecorded substep claim."}


def review(artifact, case_id, backend_path, backend_sha256, source_binding="c191-experimental-0.1"):
    artifact = Path(artifact)
    backend = json.loads(Path(backend_path).read_text())
    require(digest(backend_path) == backend_sha256, "Reviewed backend hash mismatch")
    require(digest(artifact / "backend.json") == backend_sha256, "Artifact backend differs from reviewed bytes")
    source = json.loads((artifact / "canonical-input.json").read_text())
    result = {"version": "C193-independent-artifact-review-1", "case": case_id,
        "artifact": str(artifact), "passed": False, "failures": [],
        "python": platform.python_version(), "numpy": np.__version__,
        "checker_sha256": digest(__file__)}
    try:
        result["source"] = check_source(source, CASES[case_id], backend, backend_sha256, source_binding)
    except Exception as error:
        result["failures"].append("source: " + str(error))
    measure_c191.CASES[case_id] = CASES[case_id]
    result["playback"] = measure_c191.measure(artifact / "final.glb", case_id)
    if not result["playback"]["pass"]:
        result["failures"].append("playback: " + result["playback"].get("reason", "failed"))
    result["mapping_measurements"] = compare(artifact / "raw.glb", artifact / "final.glb", artifact / "native-transforms.json")
    try:
        result["mapping"] = historical_mapping_audit(artifact / "raw.glb", artifact / "final.glb", artifact / "native-transforms.json")
    except Exception as error:
        result["mapping"] = {"passed": False, "reason": type(error).__name__ + ": " + str(error)}
        result["failures"].append("unchanged historical mapping gate rejected")
    result["diagnosis"] = diagnose(artifact)
    result["artifacts"] = {name: digest(artifact / name) for name in
        ("canonical-input.json", "backend.json", "raw.glb", "final.glb", "native-transforms.json", "scene.blend")}
    result["passed"] = not result["failures"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--backend-sha256", required=True)
    parser.add_argument("--source-binding", choices=("c191-experimental-0.1", "c193-experimental-0.1"), default="c191-experimental-0.1")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--diagnostic", action="store_true", help="Retain an expected failed diagnostic result without a failing command status")
    args = parser.parse_args()
    frozen = verify_frozen()
    result = review(args.artifact, args.case, args.backend, args.backend_sha256, args.source_binding)
    result["inherited_preservation"] = frozen
    require(not args.out.exists(), "Evidence output already exists")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed": result["passed"], "case": args.case,
        "native_peak_mm": result["diagnosis"]["peak"]["distance_mm"],
        "continuous_bound_mm": result["mapping_measurements"]["maximumContinuousRawToFinalVertexDeviationBoundMm"],
        "evidence": str(args.out)}))
    return 0 if result["passed"] or args.diagnostic else 1


if __name__ == "__main__":
    raise SystemExit(main())
