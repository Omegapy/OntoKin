"""Summarize exact retained build bytes; no native or receiving execution."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def right_samples(native):
    return [{"frame": row["frame"], "time_s": row["time_s"],
             "matrices": {name: row["matrices_blender_m"][name] for name in
                          ("right_carriage", "right_shoe", "right_stop")}}
            for row in native["samples"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--retained", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.formal.read_text())
    historical = right_samples(json.loads((args.retained / "native-result.json").read_text()))
    rows = []
    for row in manifest["runs"]:
        original_root = Path(row["build_receipt"]).parents[1]
        artifact = args.formal.resolve().parent / Path(row["artifact_directory"]).relative_to(original_root)
        for name, record in row["artifacts"].items():
            assert digest(artifact / name) == record["sha256"]
        receipt_path = args.formal.resolve().parent / Path(row["build_receipt"]).relative_to(original_root)
        receipt = json.loads(receipt_path.read_text())
        mapping = json.loads((artifact / "post-export.json").read_text())["geometry_deviation"]
        summary = json.loads((artifact / "native-summary.json").read_text())
        native = json.loads((artifact / "native-result.json").read_text())
        assert right_samples(native) == historical
        rows.append({"id": row["id"], "case": row["case"], "route": row["route"],
                     "artifact_directory": str(artifact), "original_artifact_directory": row["artifact_directory"],
                     "self_checks_passed": row["build_successful"],
                     "source_sha256": row["source_sha256"],
                     "canonical_sha256": row["artifacts"]["canonical-input.json"]["sha256"],
                     "native_transforms_sha256": row["artifacts"]["native-transforms.json"]["sha256"],
                     "raw_sha256": row["artifacts"]["raw.glb"]["sha256"],
                     "final_sha256": row["artifacts"]["final.glb"]["sha256"],
                     "native_sample_max_mm": mapping["native_sample_to_final_max_vertex_distance_mm"],
                     "raw_sample_max_mm": mapping["raw_sample_to_final_max_vertex_distance_mm"],
                     "producer_continuous_bound_mm": mapping["continuous_raw_export_to_final_full_clip_bound_mm"],
                     "left_final_travel_mm": summary["lanes"]["left"]["final_travel_mm"],
                     "right_final_travel_mm": summary["lanes"]["right"]["final_travel_mm"],
                     "right_native_samples_equal_historical_C192": True,
                     "cost": receipt["cost"]})
    groups = []
    for case in "ABCDEF":
        members = [row for row in rows if row["case"] == case]
        agreement = {name: len({row[name] for row in members}) == 1 for name in
                     ("canonical_sha256", "native_transforms_sha256", "raw_sha256", "final_sha256")}
        assert all(agreement.values())
        groups.append({"case": case, "members": [row["id"] for row in members], "exact_agreement": agreement})
    report = {"schema": "ontokin.c193.native-build-summary/0.1",
              "implementation_revision": manifest["implementation_revision"],
              "formal_manifest_sha256": digest(args.formal), "adoption_sha256": manifest["adoption_sha256"],
              "backend_sha256": manifest["backend_sha256"], "checker_sha256": digest(Path(__file__)),
              "native_builds": len(rows), "postprocessing_native_executions": 0,
              "all_builds_self_checked": manifest["all_builds_self_checked"],
              "independent_replay_and_receiving": "separately reported; not asserted by this producer summary",
              "historical_right_reference": {"artifact": str(args.retained),
                                             "native_result_sha256": digest(args.retained / "native-result.json")},
              "all_right_samples_match_historical": True, "repeat_and_route_agreement": groups,
              "maximum_native_sample_distance_mm": max(row["native_sample_max_mm"] for row in rows),
              "maximum_producer_continuous_bound_mm": max(row["producer_continuous_bound_mm"] for row in rows),
              "maximum_operations": max(row["cost"]["operations_consumed"] for row in rows),
              "maximum_attempt_elapsed_ms": max(row["cost"]["elapsed_ms"] for row in rows),
              "runs": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("native_builds", "all_builds_self_checked",
                     "maximum_native_sample_distance_mm", "maximum_producer_continuous_bound_mm",
                     "maximum_operations", "maximum_attempt_elapsed_ms", "all_right_samples_match_historical")}))


if __name__ == "__main__":
    main()
