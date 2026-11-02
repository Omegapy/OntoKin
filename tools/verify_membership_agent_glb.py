#!/usr/bin/env python3
"""Read all C088 Agent GLBs against the original source-only artifact oracle.

The sole approved transport amendment changes seven edit scopes. It supplies no
artifact answer. Successful retrievals and the uncommitted prepared-only copy
are explicitly separate. This reader imports no product module.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import traceback

import verify_membership_glb as R


READER_SHA = "ca6c55a2c75812fa1fc8d136c2da054d910762768168fdc542513bfa7c499243"
NATIVE_READBACK_SHA = "7482a92b23bee03e5a34b6ecd1f5d64ba8a55f81bb10885b83eb20f6053ca6dc"
AMENDMENT_SHA = "d53ae7f40659686d0874ced5d342deaa1a1421fd6ce17b9e6dd02b1b68510a54"


def inventory(root, exclude):
    return [{"path": p.relative_to(root).as_posix(), "bytes": len(raw),
             "mode": "100755" if p.stat().st_mode & 0o111 else "100644", "sha256": R.sha(raw)}
            for p in sorted(root.rglob("*")) if p.is_file() and p.name not in exclude
            for raw in (p.read_bytes(),)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference-checkout", "candidate-source", "fixtures", "amendment",
                 "agent-output", "native-output", "native-readback", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    for name, value in vars(args).items():
        setattr(args, name, value.resolve())
    R.require(not args.output.exists() and not args.output.is_relative_to(args.candidate_source), "Fresh external readback output")
    args.output.mkdir(parents=True)
    report = {"schema_version": "ontokin.c088-independent-agent-glb-reader/1", "status": "running",
              "reader_sha256": R.sha(Path(__file__).read_bytes()), "argv": sys.argv,
              "retrieved_artifacts": [], "prepared_only_artifacts": [], "failures": []}
    try:
        R.require(R.sha(Path(R.__file__).read_bytes()) == READER_SHA, "Exact reviewed complete GLB reader")
        report["reference_utilities"] = R.import_references(args.reference_checkout)
        frozen = R.load_frozen(args.fixtures)
        report.update(input_manifest_sha256=R.INPUT_SHA, specification_sha256=R.SPEC_SHA,
                      complete_glb_reader_sha256=READER_SHA)
        raw = (args.native_readback / "summary.json").read_bytes()
        R.require(R.sha(raw) == NATIVE_READBACK_SHA, "Exact accepted original artifact cohort")
        accepted = R.T.loads(raw)
        R.require(accepted["status"] == "passed" and len(accepted["artifacts"]) == 21
                  and len(accepted["pairs"]) == 14 and len(accepted["hostiles"]) == 13, "Complete accepted native evidence")
        recorded = R.T.loads((args.native_readback / "READER-INVENTORY.json").read_bytes())
        actual = [{k: v for k, v in row.items() if k != "mode"}
                  for row in inventory(args.native_readback, {"READER-INVENTORY.json"})]
        R.require(actual == recorded, "Accepted native evidence remains byte-identical")
        accepted_roles = {row["role"]: row for row in accepted["artifacts"]}
        report["accepted_native_summary_sha256"] = R.sha(raw)
        amendment_raw = (args.amendment / "AMENDMENT.json").read_bytes()
        R.require(R.sha(amendment_raw) == AMENDMENT_SHA, "Exact independently reviewed Agent scope amendment")
        amendment = R.T.loads(amendment_raw)
        effective = args.amendment / amendment["effective_root"]
        effective_manifest_raw = (effective / "INPUTS-MANIFEST.json").read_bytes()
        effective_manifest = R.T.loads(effective_manifest_raw)
        rows = inventory(effective, {"INPUTS-MANIFEST.json"})
        R.require(R.sha(effective_manifest_raw) == amendment["effective_input_manifest_sha256"]
                  and rows == effective_manifest["files"]
                  and R.sha(R.canonical(rows)) == amendment["effective_input_inventory_sha256"], "Exact complete effective input bytes/modes")
        inputs_before = R.T.loads((args.agent_output / "inputs-before.json").read_bytes())
        inputs_after = R.T.loads((args.agent_output / "inputs-after.json").read_bytes())
        R.require(inputs_before == inputs_after and inputs_before["files"] == rows
                  and inputs_before["manifest_sha256"] == amendment["effective_input_manifest_sha256"]
                  and inputs_before["inventory_sha256"] == amendment["effective_input_inventory_sha256"], "Agent executed exact amended inputs unchanged")
        report["transport_amendment"] = {"sha256": AMENDMENT_SHA,
            "effective_input_manifest_sha256": amendment["effective_input_manifest_sha256"],
            "semantic_answers": "unchanged original frozen source/geometry/provenance/PNG/motion answers"}
        summary, receipt = R.load_producer(args.agent_output, args.candidate_source, agent=True)
        R.require(not summary["failures"] and len(summary["workflows"]) == 11, "Complete successful eleven-workflow Agent evidence")
        report["agent_producer"] = receipt
        native, receipt = R.load_producer(args.native_output, args.candidate_source)
        report["native_producer"] = receipt
        native_roles = {row["role"]: row for row in native["artifacts"]}
        source_cases = {name: case for name, case in frozen["cases"].items() if case["mode"] == "source" and case["status"] == "passed"}
        workflow = R.T.loads((frozen["root"] / "agent/request-workflows.json").read_bytes())
        expected_exports = {}
        for scenario in workflow["scenarios"]:
            for step in scenario.get("steps", []) + scenario.get("then", []):
                request = step.get("request", {})
                if request.get("operation") == "export" and step.get("expected_status") == "succeeded":
                    expected_exports[(scenario["id"], step["step"])] = request
        actual_exports = {(row["workflow"], row["name"]): row for row in summary["agent_artifacts"]}
        R.require(len(expected_exports) == len(actual_exports) == len(summary["agent_artifacts"]) == 10
                  and set(actual_exports) == set(expected_exports), "All and only ten frozen successful retrieved exports")
        basis = R.Z.implementation_basis(args.candidate_source)
        supplied_paths = set()

        def check(row, expected_request, prepared_only=False):
            revision = expected_request["program_revision"]
            candidates = [c for c in source_cases.values() if c["program_revision"] == revision]
            R.require(candidates, "Expected export revision belongs to an original source case")
            case = candidates[0]
            raw = R.T.ordinary_path(args.agent_output, row["glb"]).read_bytes()
            R.require((len(raw), R.sha(raw), row["artifact_id"]) ==
                      (row["bytes"], row["sha256"], "artifact:" + R.sha(raw)), "Actual complete supplied Agent bytes and artifact identity")
            native_row = native_roles[case["id"]]
            native_raw = R.T.ordinary_path(args.native_output, native_row["path"]).read_bytes()
            R.require(R.sha(native_raw) == native_row["sha256"] == accepted_roles[case["id"]]["sha256"]
                      and raw == native_raw, "Whole Agent GLB equals independently accepted native source bytes")
            checked = R.check_artifact(raw, case, frozen, basis)[2]
            supplied_paths.add(row["glb"])
            return {"path": row["glb"], "bytes": len(raw), "sha256": R.sha(raw),
                    "program_revision": revision, "artifact_id": row["artifact_id"],
                    "expected_request_id": expected_request["request_id"], "native_role": case["id"],
                    "status": "passed", "prepared_only": prepared_only,
                    "whole_native_bytes_identical": True, "complete_semantic_readback": checked}

        for key, request in expected_exports.items():
            row = actual_exports[key]
            R.require(row["program_revision"] == request["program_revision"]
                      and row["export_request_id"] == request["request_id"], "Exact immutable export request/revision identity")
            report["retrieved_artifacts"].append({"workflow": key[0], "name": key[1], **check(row, request)})
            R.save(args.output / "summary.json", report)
        a07 = next(s for s in workflow["scenarios"] if s["id"] == "A07")
        interrupted = summary["publication_interruptions"]
        R.require(len(interrupted) == 1 and len(interrupted[0]["prepared_only"]) == 1, "One separately retained uncommitted artifact")
        row = interrupted[0]["prepared_only"][0]
        R.require(row["request_id"] == a07["export_request"]["request_id"] and row["sqlite_transaction_active"] is True,
                  "Prepared-only row binds the frozen interrupted export")
        report["prepared_only_artifacts"].append({"workflow": "A07", **check(row, a07["export_request"], True),
            "publication_claim": "No accepted run or published artifact is claimed for this prepared-only copy; the separate Agent/SQLite reader checks rollback and refusal."})
        actual_paths = {p.relative_to(args.agent_output).as_posix() for p in args.agent_output.rglob("*.glb")}
        R.require(actual_paths == supplied_paths and len(supplied_paths) == 11, "Complete Agent GLB file inventory")
        R.require(not any(n == "ontokin" or n.startswith("ontokin.") for n in sys.modules), "No product import")
        report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", fatal={"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
    finally:
        report["product_modules_imported"] = [n for n in sys.modules if n == "ontokin" or n.startswith("ontokin.")]
        report["reader_sha256_after"] = R.sha(Path(__file__).read_bytes())
        R.save(args.output / "summary.json", report)
        R.save(args.output / "READER-INVENTORY.json", inventory(args.output, {"READER-INVENTORY.json"}))
    print(R.canonical({"status": report["status"], "retrieved_artifacts": len(report["retrieved_artifacts"]),
                       "prepared_only_artifacts": len(report["prepared_only_artifacts"]),
                       "fatal": report.get("fatal", {}).get("message")}).decode())
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
