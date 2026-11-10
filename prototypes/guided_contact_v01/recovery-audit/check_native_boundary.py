#!/usr/bin/env python3
"""Supplemental C191-R2 native-envelope and required-scene failure probes.

This author audit uses a controlled copying worker and an identified real native
seed. It tests transaction rejection, never claims another native simulation.
Expectations were written before the candidate mutations were executed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


CASES = (
    ("valid-copy-control", None),
    ("mesh-reported-as-empty", "C191_E_NATIVE_RESULT"),
    ("constraint-reported-as-mesh", "C191_E_NATIVE_RESULT"),
    ("missing-native-scene", "C191_E_NATIVE_FAILURE"),
    ("empty-native-scene", "C191_E_NATIVE_RESULT"),
    ("invalid-native-scene-header", "C191_E_NATIVE_RESULT"),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    return {str(item.relative_to(path)): digest(item)
            for item in sorted(path.rglob("*")) if item.is_file()}


def run(repo, seed, output, blender):
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.api import run as adapter_run

    revision = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()
    implementation = {item.name: digest(item)
                      for item in sorted((repo / "prototypes/guided_contact_v01").glob("*.py"))}
    seed_store = seed.parents[1]
    records = []
    for case, expected_code in CASES:
        directory = output / case
        directory.mkdir()
        store = directory / "store"
        shutil.copytree(seed_store, store)
        state_before = (store / "state.json").read_bytes()
        prior = json.loads(state_before)
        old_artifacts = store / prior["artifact_directory"]
        old_inventory = inventory(old_artifacts)

        def copy_command(argv, stage):
            code = ("import pathlib,shutil,sys; "
                    "seed=pathlib.Path(sys.argv[1]); stage=pathlib.Path(sys.argv[2]); "
                    "shutil.copyfile(seed/'native-result.json',stage/'native-result.json'); "
                    "shutil.copyfile(seed/'scene.blend',stage/'scene.blend')")
            return [sys.executable, "-B", "-c", code, str(seed), str(stage)]

        def mutate(stage):
            native = stage / "native-result.json"
            if case in ("mesh-reported-as-empty", "constraint-reported-as-mesh"):
                data = json.loads(native.read_text())
                name, kind = (("left_carriage", "EMPTY") if case.startswith("mesh-")
                              else ("_left_generic", "MESH"))
                data["configuration"]["objects"][name]["type"] = kind
                native.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")
            elif case == "missing-native-scene":
                (stage / "scene.blend").unlink()
            elif case == "empty-native-scene":
                (stage / "scene.blend").write_bytes(b"")
            elif case == "invalid-native-scene-header":
                (stage / "scene.blend").write_bytes(b"not a Blender file")

        source = repo / "docs/language-design/guided-contact-v0.1/examples/A.ok"
        result = adapter_run(source, store=store, blender=blender,
                             host_max_operations=1000000, host_max_elapsed_ms=80000,
                             expected_revision=prior["accepted_revision"],
                             hooks={"worker_command": copy_command, "before_native_validation": mutate})
        (directory / "returned-result.json").write_text(json.dumps(result, indent=2) + "\n")
        actual_codes = [item["code"] for item in result["diagnostics"]]
        pointer_changed = (store / "state.json").read_bytes() != state_before
        old_unchanged = inventory(old_artifacts) == old_inventory
        expected_success = expected_code is None
        correct = (result["successful"] == result["committed"] == expected_success
                   and actual_codes == ([] if expected_success else [expected_code])
                   and pointer_changed == expected_success and old_unchanged)
        if not expected_success:
            correct = correct and all(not result["levels"][level]
                                      for diagnostic in result["diagnostics"]
                                      for level in diagnostic["blocked_levels"])
        records.append({"case": case, "expected_code": expected_code,
                        "actual_codes": actual_codes, "successful": result["successful"],
                        "committed": result["committed"], "pointer_changed": pointer_changed,
                        "previous_artifacts_unchanged": old_unchanged, "pass": correct,
                        "returned_result_sha256": digest(directory / "returned-result.json")})

    return {"version": "C191-R2-author-native-boundary-audit-1", "implementation_revision": revision,
            "implementation_files": implementation, "script_sha256": digest(Path(__file__)),
            "seed_directory": str(seed), "seed_native_result_sha256": digest(seed / "native-result.json"),
            "seed_final_glb_sha256": digest(seed / "final.glb"),
            "method": "Actual transaction and supervisor with trusted copying-worker faults; no fresh native claim",
            "cases": records, "passed": sum(row["pass"] for row in records),
            "total": len(records), "pass": all(row["pass"] for row in records)}


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
