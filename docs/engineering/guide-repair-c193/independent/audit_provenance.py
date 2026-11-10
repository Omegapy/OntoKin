#!/usr/bin/env python3
"""Supplemental C193 provenance audit; earlier numerical freeze stays unchanged."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile

from check_artifact import CASES, digest, expected_source, require


def required_closure(contract):
    manifest = json.loads((contract / "CONTRACT-FILES.json").read_text())
    closure = list(manifest["files"])
    amendment = contract / "amendments/C191-A1.md"
    closure.append({"path": "amendments/C191-A1.md", "bytes": amendment.stat().st_size, "sha256": digest(amendment)})
    for row in closure:
        path = contract / row["path"]
        require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], "Contract dependency differs: " + row["path"])
    return closure


def source_manifest_check(artifact, contract, contract_sha):
    require(digest(contract / "CONTRACT-FILES.json") == contract_sha, "Reviewed contract bytes changed")
    source_files = [artifact / name for name in ("source.ok", "source.py") if (artifact / name).is_file()]
    require(len(source_files) == 1, "Exactly one retained authoring source required")
    source = source_files[0]
    manifest = json.loads((artifact / "source-manifest.json").read_text())
    require(manifest["source_sha256"] == digest(source), "Source manifest source hash differs")
    require(manifest["canonical_input_sha256"] == digest(artifact / "canonical-input.json"), "Canonical input hash differs")
    require(manifest.get("contract_manifest_sha256") == contract_sha, "Source manifest names wrong contract")
    closure = required_closure(contract)
    require(manifest.get("dependency_closure") == closure, "Source dependency closure differs from reviewed bytes")
    canonical = json.loads((artifact / "canonical-input.json").read_text())
    backend_sha = digest(contract / "backend.json")
    require(canonical["source_binding"] == "c193-experimental-0.1", "Wrong source selector")
    require(canonical["backend"] == "blender-bullet-c193-0.1", "Wrong backend selector")
    require(canonical["backend_sha256"] == backend_sha == digest(artifact / "backend.json"), "Canonical backend identity differs")
    if source.suffix == ".py":
        require(manifest.get("backend_sha256") == backend_sha, "Direct source manifest backend identity differs")
        receipt = json.loads((artifact / "build-receipt.json").read_text())
        require(receipt.get("contract_manifest_sha256") == contract_sha, "Direct build receipt names wrong contract")
        require(receipt.get("backend_sha256") == backend_sha, "Direct build receipt backend identity differs")
    return {"passed": True, "source_sha256": digest(source), "canonical_input_sha256": digest(artifact / "canonical-input.json"),
            "contract_manifest_sha256": contract_sha, "backend_sha256": backend_sha,
            "dependency_files": len(closure), "route": "python" if source.suffix == ".py" else "ok"}


def audit(artifact, contract, candidate_review):
    review = json.loads(candidate_review.read_text())
    require(review["passed_for_adoption_and_qualification"], "Candidate review is not approved")
    result = source_manifest_check(artifact, contract, review["contract_manifest_sha256"])
    implementation = json.loads((artifact / "implementation-manifest.json").read_text())
    approved = {Path(row["path"]).name: row["sha256"] for row in review["implementation_files"]}
    require(set(implementation["files"]) == set(approved), "Retained implementation inventory differs")
    for name, sha in approved.items():
        path = artifact / "implementation" / name
        require(digest(path) == sha == implementation["files"][name]["sha256"], "Executed implementation bytes differ: " + name)
        require(path.stat().st_size == implementation["files"][name]["bytes"], "Implementation size differs")
    command = json.loads((artifact / "native-command.json").read_text())
    require(command["trusted_test_hooks"] == [], "Formal native build used test hooks")
    require(command["returncode"] == 0 and command["stop_reason"] is None, "Native command did not finish normally")
    require(command["poll_ms"] == 50 and command["terminate_grace_ms"] == 500, "Supervisor bounds changed")
    if result["route"] == "ok":
        context = json.loads((artifact / "attempt-context.json").read_text())
        require(context["formal_native_qualification_run"] and not context["trusted_host_test_hooks"], "Nonformal .ok native attempt")
    inventory = json.loads((artifact / "manifest.json").read_text())["files"]
    for name, row in inventory.items():
        path = (artifact / name).resolve()
        require(path.is_relative_to(artifact.resolve()) and path.is_file(), "Artifact manifest escapes or misses a file")
        require(digest(path) == row["sha256"] and path.stat().st_size == row["bytes"], "Artifact inventory differs: " + name)
    result.update(version="C193-independent-provenance-audit-1", implementation_files_verified=len(approved),
        manifest_files_verified=len(inventory), candidate_review_sha256=digest(candidate_review),
        retained_worker_sha256=approved["native_worker.py"], native_formal_no_test_hooks=True)
    return result


def controls(contract, source, out):
    require(not out.exists(), "Refusing to overwrite control report")
    contract_sha = digest(contract / "CONTRACT-FILES.json")
    canonical = expected_source(CASES["A"], "blender-bullet-c193-0.1", digest(contract / "backend.json"), "c193-experimental-0.1")
    rows = []
    with tempfile.TemporaryDirectory(prefix="c193-provenance-control-") as temporary:
        artifact = Path(temporary)
        (artifact / "source.ok").write_bytes(source.read_bytes())
        (artifact / "backend.json").write_bytes((contract / "backend.json").read_bytes())
        (artifact / "canonical-input.json").write_text(json.dumps(canonical, sort_keys=True, separators=(",", ":")) + "\n")
        valid = {"source_sha256": digest(artifact / "source.ok"), "canonical_input_sha256": digest(artifact / "canonical-input.json"),
                 "contract_manifest_sha256": contract_sha, "dependency_closure": required_closure(contract)}
        for name in ("current-contract", "stale-C191-contract", "altered-dependency-hash"):
            manifest = copy.deepcopy(valid)
            if name == "stale-C191-contract":
                manifest["contract_manifest_sha256"] = "bc85696002d641122322313cf5167f84eb1ae377599930112e3afd0f054b0137"
            elif name == "altered-dependency-hash":
                manifest["dependency_closure"][0]["sha256"] = "0" * 64
            (artifact / "source-manifest.json").write_text(json.dumps(manifest) + "\n")
            try:
                source_manifest_check(artifact, contract, contract_sha)
                accepted, reason = True, None
            except ValueError as error:
                accepted, reason = False, str(error)
            rows.append({"case": name, "expected_acceptance": name == "current-contract", "accepted": accepted,
                         "passed": accepted == (name == "current-contract"), "reason": reason})
    report = {"version": "C193-provenance-control-1", "passed": all(r["passed"] for r in rows), "controls": rows,
              "checker_sha256": digest(__file__), "native_executions": 0,
              "scope": "Synthetic manifest guard controls only; formal artifact audit remains required."}
    out.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--candidate-review", type=Path)
    parser.add_argument("--controls-source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.controls_source:
        report = controls(args.contract, args.controls_source, args.out)
    else:
        require(not args.out.exists(), "Refusing to overwrite provenance evidence")
        report = audit(args.artifact, args.contract, args.candidate_review)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "evidence": str(args.out)}))


if __name__ == "__main__":
    main()
