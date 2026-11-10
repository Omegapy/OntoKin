#!/usr/bin/env python3
"""Run the 37 separately translated frozen source expectations against C193.

The five run-mode fixtures must reject before worker execution. This is source
and boundary conformance, not fresh native qualification or lifecycle release.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.repo.resolve()))
    from prototypes.guided_contact_v02.api import run, validate_source
    from prototypes.guided_contact_v01.api import validate_source as old_validate
    fixtures = HERE / "frozen/source-fixtures"
    manifest = json.loads((fixtures / "manifest.json").read_text())
    records, worker_attempts, canonicals = [], [], {}

    def forbid_native(argv, stage):
        worker_attempts.append({"argv": argv, "stage": str(stage)})
        raise RuntimeError("Source conformance fixture unexpectedly reached native worker")

    for fixture in manifest["fixtures"]:
        source = fixtures / fixture["file"]
        assert digest(source) == fixture["sha256"]
        entry = {"id": fixture["id"], "mode": fixture["mode"], "source_sha256": digest(source), "passed": False}
        folder = args.out / fixture["id"]
        folder.mkdir()
        try:
            if fixture["mode"] == "validate":
                canonical = folder / "canonical-input.json"
                result = validate_source(source, host_max_operations=1000000, host_max_elapsed_ms=80000,
                                         canonical_out=canonical)
            else:
                runtime = args.blender
                if fixture["id"] == "N12-missing-backend":
                    runtime = folder / "nonexistent-blender"
                    assert not runtime.exists()
                elif fixture["id"] == "N36-mismatched-backend":
                    runtime = Path("/bin/true")
                ceilings = fixture.get("host_ceilings", {})
                result = run(source, store=folder / "store", blender=runtime,
                    host_max_operations=ceilings.get("operations", 1000000),
                    host_max_elapsed_ms=ceilings.get("elapsed_ms", 80000),
                    hooks={"worker_command": forbid_native})
            (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
            assert result["successful"] == fixture["expected_success"]
            assert result["source_sha256"] == digest(source)
            assert result["committed"] is False and result["levels"]["destination_validated"] is False
            if fixture["expected_success"]:
                assert result["diagnostics"] == []
                canonicals[fixture["id"]] = canonical.read_bytes()
                expected_path = fixtures / (fixture["id"] + "-canonical.json")
                if expected_path.exists():
                    assert json.loads(canonical.read_text()) == json.loads(expected_path.read_text())
                if "same_canonical_input_as" in fixture:
                    assert canonical.read_bytes() == canonicals[fixture["same_canonical_input_as"]]
            else:
                diagnostic, = result["diagnostics"]
                assert diagnostic["code"] == fixture["expected_code"]
                assert diagnostic["phase"] == fixture["expected_phase"]
                assert diagnostic["blocked_levels"] == fixture["expected_blocked_levels"]
                assert diagnostic["span"] == fixture["expected_span"]
                assert all(not result["levels"][level] for level in fixture["expected_blocked_levels"])
            if fixture["mode"] == "run":
                assert not (folder / "store/state.json").exists()
                assert not list((folder / "store").rglob("native-command.json"))
            entry["passed"] = True
        except Exception as error:
            entry["failure"] = type(error).__name__ + ": " + str(error)
        records.append(entry)
    old_source = REPO / "docs/language-design/guided-contact-v0.1/examples/A.ok"
    cross = []
    for label, function, source, code in (
        ("v02-rejects-v01-source", validate_source, old_source, "C193_E_BINDING"),
        ("v01-rejects-v02-source", old_validate, fixtures / "A.ok", "C191_E_BINDING")):
        result = function(source, host_max_operations=1000000, host_max_elapsed_ms=80000)
        (args.out / (label + ".json")).write_text(json.dumps(result, indent=2) + "\n")
        passed = not result["successful"] and result["diagnostics"][0]["code"] == code
        cross.append({"id": label, "passed": passed})
    report = {"version": "C193-independent-source-conformance-1", "python": platform.python_version(),
        "candidate_repo": str(args.repo.resolve()), "candidate_contract_manifest_sha256": digest(args.repo / "docs/language-design/guided-contact-v0.2/CONTRACT-FILES.json"),
        "source_fixture_manifest_sha256": digest(fixtures / "manifest.json"),
        "checker_sha256": digest(__file__), "fixtures": records, "count": len(records),
        "validation_only_count": sum(r["mode"] == "validate" for r in records),
        "pre_native_run_rejections_count": sum(r["mode"] == "run" for r in records),
        "cross_binding_controls": cross, "native_worker_attempts": worker_attempts,
        "passed": all(r["passed"] for r in records + cross) and not worker_attempts}
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "fixtures": len(records),
        "cross_binding_controls": len(cross), "failed": [r for r in records if not r["passed"]],
        "native_worker_attempts": len(worker_attempts)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
