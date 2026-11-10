#!/usr/bin/env python3
"""Author C191-R2 probes for optional-output aliases and accepted byte safety."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    return {str(path.relative_to(directory)): digest(path)
            for path in sorted(directory.rglob("*")) if path.is_file()}


def run(repo, seed, output, blender):
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.api import run as adapter_run, validate_source
    records = []
    example = repo / "docs/language-design/guided-contact-v0.1/examples/A.ok"
    invalid = repo / "docs/engineering/guided-contact-c191/independent/source-fixtures/N10-initial-overlap.ok"
    for case in ("invalid-state", "invalid-artifact", "invalid-source", "invalid-state-symlink",
                 "invalid-artifact-hardlink", "valid-state", "valid-source", "valid-external", "valid-late-alias"):
        directory = output / case
        directory.mkdir()
        store = directory / "store"
        shutil.copytree(seed.parents[1], store)
        state_before = (store / "state.json").read_bytes()
        old = json.loads(state_before)
        artifacts = store / old["artifact_directory"]
        prior_inventory = inventory(artifacts)
        source = directory / "candidate.ok"
        source.write_bytes((invalid if case.startswith("invalid-") else example).read_bytes())
        source_before = source.read_bytes()
        if case.endswith("state"):
            result_path = store / "state.json"
        elif case.endswith("artifact"):
            result_path = artifacts / "final.glb"
        elif case.endswith("source"):
            result_path = source
        else:
            result_path = directory / "optional-result.json"
        if case.endswith("state-symlink"):
            result_path.symlink_to(store / "state.json")
        if case.endswith("artifact-hardlink"):
            result_path.hardlink_to(artifacts / "final.glb")
        invoked = []
        def worker(argv, stage):
            invoked.append(True)
            code = ("import pathlib,shutil,sys; a=pathlib.Path(sys.argv[1]); b=pathlib.Path(sys.argv[2]); "
                    "shutil.copyfile(a/'native-result.json',b/'native-result.json'); "
                    "shutil.copyfile(a/'scene.blend',b/'scene.blend')")
            return [sys.executable, "-B", "-c", code, str(seed), str(stage)]
        hooks = {"worker_command": worker}
        if case == "valid-late-alias":
            hooks["before_publication_validation"] = lambda stage: result_path.symlink_to(store / "state.json")
        result = adapter_run(source, store=store, blender=blender,
                             host_max_operations=1000000, host_max_elapsed_ms=80000,
                             expected_revision=old["accepted_revision"], result_path=result_path, hooks=hooks)
        (directory / "returned-result.json").write_text(json.dumps(result, indent=2) + "\n")
        success = case in ("valid-external", "valid-late-alias")
        expected_code = None if success else "C191_E_INITIAL_OVERLAP" if case.startswith("invalid-") else "C191_E_PUBLICATION"
        actual_codes = [item["code"] for item in result["diagnostics"]]
        try:
            after = json.loads((store / "state.json").read_bytes())
            state_valid = after.get("schema") == "ontokin.c191.store/0.1"
        except (ValueError, OSError):
            state_valid = False
        state_preserved = success or (store / "state.json").read_bytes() == state_before
        bytes_preserved = inventory(artifacts) == prior_inventory and source.read_bytes() == source_before
        passed = (result["successful"] == result["committed"] == success
                  and actual_codes == ([] if success else [expected_code])
                  and state_valid and state_preserved and bytes_preserved
                  and bool(invoked) == success)
        records.append({"case": case, "expected_code": expected_code, "actual_codes": actual_codes,
                        "committed": result["committed"], "worker_invoked": bool(invoked),
                        "state_valid": state_valid, "rejected_state_preserved": state_preserved,
                        "previous_artifact_and_source_bytes_preserved": bytes_preserved, "pass": passed,
                        "returned_result_sha256": digest(directory / "returned-result.json")})
    for case in ("validate-canonical-source", "validate-result-source", "validate-shared-output"):
        directory = output / case
        directory.mkdir()
        source = directory / "candidate.ok"
        source.write_bytes(example.read_bytes())
        source_before = source.read_bytes()
        shared = directory / "shared.json"
        options = ({"canonical_out": source} if case.endswith("canonical-source") else
                   {"result_path": source} if case.endswith("result-source") else
                   {"canonical_out": shared, "result_path": shared})
        result = validate_source(source, host_max_operations=1000000, host_max_elapsed_ms=80000, **options)
        (directory / "returned-result.json").write_text(json.dumps(result, indent=2) + "\n")
        actual_codes = [item["code"] for item in result["diagnostics"]]
        preserved = source.read_bytes() == source_before and not shared.exists()
        records.append({"case": case, "expected_code": "C191_E_IO", "actual_codes": actual_codes,
                        "source_and_output_preserved": preserved,
                        "pass": not result["successful"] and actual_codes == ["C191_E_IO"] and preserved,
                        "returned_result_sha256": digest(directory / "returned-result.json")})
    revision = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()
    return {"version": "C191-R2-author-output-alias-audit-1", "implementation_revision": revision,
            "implementation_files": {path.name: digest(path) for path in sorted((repo / "prototypes/guided_contact_v01").glob("*.py"))},
            "script_sha256": digest(Path(__file__)), "seed_native_result_sha256": digest(seed / "native-result.json"),
            "method": "Actual API with copying worker for valid transactions; invalid-source cases do not invoke a worker",
            "cases": records, "passed": sum(row["pass"] for row in records), "total": len(records),
            "pass": all(row["pass"] for row in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.repo.resolve(), args.seed.resolve(), args.output.resolve(), args.blender.resolve())
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"pass": report["pass"], "passed": report["passed"], "total": report["total"],
                      "cases": report["cases"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)
