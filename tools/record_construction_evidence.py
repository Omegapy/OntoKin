"""Bind actual construction delivery reports to an explicitly reviewed capture.

Run the demo, independent GLB validator and browser verifier first. Inspect the
capture, then supply a factual review. This command verifies retained evidence;
it does not perform a visual review or execute the external tools itself.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.bundle import load_bundle
from ontokin.construction_conformance import file_identity, implementation_identity, verify_external_evidence


def record(demo, evidence_dir, reviewer, observation):
    paths = {
        "source_bundle": demo / "program.bundle.json",
        "workflow": demo / "workflow.json",
        "artifact": demo / "keyed-rack.glb",
        "reference": demo / "keyed-rack.reference.json",
        "external_results": evidence_dir / "external-results.json",
        "viewer_results": evidence_dir / "viewer-results.json",
        "capture": evidence_dir / "keyed-rack.png",
    }
    def read(role):
        return json.loads(paths[role].read_text(encoding="utf-8"))
    program = load_bundle(read("source_bundle"))
    workflow, external, viewer = read("workflow"), read("external_results"), read("viewer_results")
    artifacts = [item for item in external["files"] if "sha256:" + item["sha256"] == file_identity(paths["artifact"])]
    if len(artifacts) != 1:
        raise ValueError("Exactly one independent decoded result must identify the retrieved artifact.")
    artifact = artifacts[0]
    comparison = artifact["three_js"]["comparison"]
    capture_hash = file_identity(paths["capture"])
    manifest = {
        "schema_version": "ontokin.construction-external-gate/0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "implementation": implementation_identity(), "program_revision": program.program_revision,
        "source_manifest": program.manifest(), "artifact_sha256": file_identity(paths["artifact"]),
        "checks": {
            "workflow": {"status": workflow["status"], "checks": len(workflow["checks"]), "operations": workflow["operation_count"]},
            "format": {"status": "passed" if artifact["validator"]["errors"] == artifact["validator"]["warnings"] == 0 else "failed",
                       "errors": artifact["validator"]["errors"], "warnings": artifact["validator"]["warnings"]},
            "geometry": {"status": "passed" if all(item["status"] == "passed" for item in artifact["geometry"]) else "failed",
                         "objects": len(artifact["geometry"])},
            "motion": {"status": comparison["status"], "pose_comparisons": comparison["object_pose_comparisons"],
                       "max_position_error_m": comparison["max_position_error_m"],
                       "max_rotation_error_rad": comparison["max_rotation_error_rad"]},
            "viewer": {"status": viewer["status"], "checks": len(viewer["checks"]),
                       "pose_comparisons": viewer["pose_comparisons"], "capture_sha256": capture_hash,
                       "visual_review": {"status": "reviewed", "reviewer": reviewer, "observation": observation}},
        },
        "provenance": [{"role": role, "path": path.resolve().relative_to(ROOT).as_posix(), "sha256": file_identity(path)}
                       for role, path in paths.items()],
        "basis": "Actual separately executed workflow, format/geometry/playback validation and capture, verified by exact file identities. The stated review is supplied by the identified reviewer.",
    }
    destination = evidence_dir / "external-gate.json"
    pending = evidence_dir / "external-gate.pending.json"
    pending.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    result = verify_external_evidence(pending, implementation=implementation_identity(), expected_program=program)
    if result["status"] != "passed":
        raise ValueError("Retained evidence did not pass verification: " + "; ".join(result["issues"]))
    pending.replace(destination)
    return {"status": "passed", "program_revision": program.program_revision,
            "artifact_sha256": manifest["artifact_sha256"], "output": str(destination)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-dir", type=Path, default=ROOT / "examples/construction")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "docs/engineering/construction-validation")
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--visual-review", required=True, help="Factual observation after inspecting the actual identified capture")
    args = parser.parse_args()
    if not args.reviewer.strip() or not args.visual_review.strip():
        parser.error("A reviewer and an actual visual-review observation are required.")
    print(json.dumps(record(args.demo_dir.resolve(), args.evidence_dir.resolve(), args.reviewer.strip(), args.visual_review.strip()), indent=2))


if __name__ == "__main__":
    main()
