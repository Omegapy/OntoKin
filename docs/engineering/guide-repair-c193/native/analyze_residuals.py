"""Locate recorded guide residuals without starting Blender or changing a trace."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def magnitude(values):
    return math.sqrt(sum(value * value for value in values))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(artifact, repo):
    projection_path = repo / "prototypes/guided_contact_v01/playback_projection.py"
    spec = importlib.util.spec_from_file_location("retained_projection", projection_path)
    projection = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(projection)
    native_path = artifact / "native-result.json"
    result = json.loads(native_path.read_text())
    records = result["samples"]
    source = json.loads((artifact / "canonical-input.json").read_text())
    _, model, binary = projection.decode(artifact / "final.glb")
    nodes = {node["name"]: node for node in model["nodes"]}
    tracks = {}
    for channel in model["animations"][0]["channels"]:
        node = model["nodes"][channel["target"]["node"]]
        sampler = model["animations"][0]["samplers"][channel["sampler"]]
        tracks[node["name"]] = projection.accessor(model, binary, sampler["output"])[0]
    rows, lanes = [], {}
    for lane in ("left", "right"):
        carriage, shoe = lane + "_carriage", lane + "_shoe"
        initial = records[0]["matrices_blender_m"][carriage]
        peak = {"distance_mm": -1}
        lane_rows = []
        for sample_index, record in enumerate(records):
            matrix = record["matrices_blender_m"][carriage]
            skew = [matrix[2][1] - matrix[1][2], matrix[0][2] - matrix[2][0],
                    matrix[1][0] - matrix[0][1]]
            cosine = (sum(matrix[i][i] for i in range(3)) - 1) / 2
            angle = math.atan2(magnitude(skew) / 2, cosine)
            transverse = [0, 1000 * (matrix[2][3] - initial[2][3]),
                          -1000 * (matrix[1][3] - initial[1][3])]
            sample_peak = {"distance_mm": -1}
            for part in (carriage, shoe):
                node = nodes[part]
                primitive, = model["meshes"][node["mesh"]]["primitives"]
                vertices = projection.accessor(model, binary, primitive["attributes"]["POSITION"])[0]
                local_offset = node.get("translation", [0, 0, 0]) if part == shoe else [0, 0, 0]
                native_matrix = record["matrices_blender_m"][part]
                for vertex_index, vertex in enumerate(vertices):
                    native_local = [vertex[0], -vertex[2], vertex[1]]
                    native = [sum(native_matrix[a][k] * native_local[k] for k in range(3))
                              + native_matrix[a][3] for a in range(3)]
                    native = [native[0], native[2], -native[1]]
                    final = [tracks[carriage][sample_index][a] + local_offset[a] + vertex[a]
                             for a in range(3)]
                    delta = [1000 * (native[a] - final[a]) for a in range(3)]
                    distance = magnitude(delta)
                    if distance > sample_peak["distance_mm"]:
                        sample_peak = {"distance_mm": distance, "part": part,
                                       "vertex_index": vertex_index,
                                       "part_local_vertex_mm": [1000 * value for value in vertex],
                                       "native_minus_final_xyz_mm": delta,
                                       "native_world_xyz_mm": [1000 * value for value in native],
                                       "final_world_xyz_mm": [1000 * value for value in final]}
            row = {"lane": lane, "frame": record["frame"], "time_s": record["time_s"],
                   "carriage_x_mm": 1000 * matrix[0][3],
                   "transverse_source_xyz_mm": transverse,
                   "transverse_norm_mm": magnitude(transverse),
                   "rotation_angle_rad": angle,
                   "rotation_skew_native_xyz": skew,
                   "peak_vertex": sample_peak}
            lane_rows.append(row)
            if sample_peak["distance_mm"] > peak["distance_mm"]:
                peak = dict(sample_peak, frame=record["frame"], time_s=record["time_s"],
                            carriage_transverse_norm_mm=magnitude(transverse),
                            carriage_rotation_angle_rad=angle)
        rows.extend(lane_rows)
        ideal = ((source["parts"]["left_stop"]["at_mm"][0] - 180) / 125
                 if lane == "left" else None)
        lanes[lane] = {"peak_vertex": peak,
                       "maximum_transverse_norm_mm": max(r["transverse_norm_mm"] for r in lane_rows),
                       "maximum_rotation_angle_rad": max(r["rotation_angle_rad"] for r in lane_rows),
                       "ideal_contact_s": ideal,
                       "contact_window": [r for r in lane_rows if ideal is not None and
                                          ideal - .02 <= r["time_s"] <= ideal + .06]}
    config = result["configuration"]
    return {"schema": "ontokin.c193.recorded-guide-diagnosis/0.1",
            "artifact": str(artifact), "native_execution_performed": False,
            "identities": {name: digest(artifact / name) for name in
                           ("canonical-input.json", "native-result.json", "raw.glb", "final.glb")},
            "analysis_implementation_sha256": digest(Path(__file__)),
            "inherited_projection_sha256": digest(projection_path),
            "world_settings": config["world"],
            "construction": {name: config["objects"][name] for name in config["objects"]
                             if name.startswith("_left") or name in ("left_carriage", "left_shoe", "left_stop")},
            "lanes": lanes, "samples": rows,
            "limits": "Recorded poses only; no Bullet impulse, manifold, or unrecorded substep claim."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.artifact.resolve(), args.repo.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "lanes": {
        name: {key: value for key, value in lane.items() if key != "contact_window"}
        for name, lane in report["lanes"].items()}}, indent=2))


if __name__ == "__main__":
    main()
