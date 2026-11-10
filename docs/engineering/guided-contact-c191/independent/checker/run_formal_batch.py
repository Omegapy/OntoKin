#!/usr/bin/env python3
"""Two clean C191 builds per case, identity control and independent reopens."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_mapping import audit
from measure_c191 import measure

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "source-fixtures"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root):
    return {str(path.relative_to(root)): {"sha256": digest(path), "bytes": path.stat().st_size}
        for path in sorted(root.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}


def run_command(command, cwd, directory, name, timeout):
    started = time.time()
    completed = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout)
    (directory / (name + ".stdout.txt")).write_bytes(completed.stdout)
    (directory / (name + ".stderr.txt")).write_bytes(completed.stderr)
    record = {"argv": command, "cwd": str(cwd), "started_unix_s": started,
        "elapsed_s": time.time() - started, "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest()}
    (directory / (name + ".command.json")).write_text(json.dumps(record, indent=2) + "\n")
    return completed


def run(repo, destination, revision, blender):
    destination.mkdir(parents=True, exist_ok=False)
    contract = repo / "docs/language-design/guided-contact-v0.1"
    lock = {"implementation_revision": revision, "python": platform.python_version(), "numpy": np.__version__,
        "blender": str(blender), "blender_sha256": digest(blender),
        "prototype_files": inventory(repo / "prototypes/guided_contact_v01"),
        "contract_files": inventory(contract), "fixture_manifest_sha256": digest(FIXTURES / "manifest.json"),
        "source_freeze_sha256": digest(HERE.parent / "frozen/SOURCE-FREEZE.json"),
        "checker_files": inventory(HERE), "trusted_host_hooks_used": False}
    assert lock["blender_sha256"] == "5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397"
    (destination / "INPUT-LOCK.json").write_text(json.dumps(lock, indent=2) + "\n")
    builds = []
    failures = []
    for case, repeat in [(case, repeat) for case in "ABCD" for repeat in (1, 2)] + [("E", 1)]:
        label = f"{case}-{repeat}"
        directory = destination / label
        directory.mkdir()
        source = FIXTURES / ("E-rename-reorder.ok" if case == "E" else case + ".ok")
        canonical = FIXTURES / (("A" if case == "E" else case) + "-canonical.json")
        command = [sys.executable, "-B", "-m", "prototypes.guided_contact_v01", "run", str(source),
            "--store", str(directory / "store"), "--blender", str(blender),
            "--host-max-operations", "1000000", "--host-max-elapsed-ms", "80000"]
        record = {"case": case, "repeat": repeat, "source": str(source), "source_sha256": digest(source),
            "canonical_expected_sha256": digest(canonical), "pass": False}
        try:
            completed = run_command(command, repo, directory, "build", 100)
            result = json.loads(completed.stdout)
            (directory / "build.result.json").write_text(json.dumps(result, indent=2) + "\n")
            assert completed.returncode == 0 and result["successful"] and result["committed"], "Build did not commit successfully"
            assert result["diagnostics"] == [] and not result["levels"]["destination_validated"]
            assert result["source_sha256"] == digest(source)
            artifacts = Path(result["artifact_directory"])
            record["artifact_directory"] = str(artifacts)
            assert (artifacts / "canonical-input.json").read_bytes() == canonical.read_bytes()
            assert (artifacts / "source.ok").read_bytes() == source.read_bytes()
            context = json.loads((artifacts / "attempt-context.json").read_text())
            assert context["formal_native_qualification_run"] and context["trusted_host_test_hooks"] == []
            final_report = measure(artifacts / "final.glb", "A" if case == "E" else case)
            (directory / "final-playback.json").write_text(json.dumps(final_report, indent=2) + "\n")
            assert final_report["pass"], final_report.get("reason")
            mapping = audit(artifacts / "raw.glb", artifacts / "final.glb", artifacts / "native-transforms.json")
            (directory / "mapping-audit.json").write_text(json.dumps(mapping, indent=2) + "\n")
            record["artifacts"] = {name: {"sha256": digest(artifacts / name), "bytes": (artifacts / name).stat().st_size}
                for name in ("source.ok", "canonical-input.json", "raw.glb", "final.glb", "scene.blend", "native-transforms.json", "mapping.json")}
            record["maximum_continuous_mapping_mm"] = mapping["maximumContinuousRawToFinalVertexDeviationBoundMm"]
            record["maximum_native_sample_mapping_mm"] = mapping["maximumNativeSampleToFinalVertexDistanceMm"]
            record["cost"] = result["cost"]
            reopen_command = [str(blender), "--factory-startup", "-b", str(artifacts / "scene.blend"), "-t", "2",
                "--python-exit-code", "1", "--python", str(HERE / "inspect_native.py"), "--", "--case", "A" if case == "E" else case,
                "--out", str(directory / "reopen"), "--contract", str(contract), "--source", str(source), "--canonical", str(canonical)]
            reopened = run_command(reopen_command, repo, directory, "reopen", 80)
            assert reopened.returncode == 0, "Independent native reopen failed; inspect preserved stderr/configuration"
            native_summary = json.loads((directory / "reopen/summary.json").read_text())
            assert native_summary["pass"] and native_summary["cache_clear_completed"] and not native_summary["reconstructed_or_repaired"]
            original = json.loads((artifacts / "native-transforms.json").read_text())
            again = json.loads((directory / "reopen/native-transforms.json").read_text())
            assert len(original) == len(again) == 481
            assert all(x["time_s"] == y["time_s"] and x["frame"] == y["frame"] for x, y in zip(original, again))
            x_differences = {lane: max(abs(x["matrices_blender_m"][lane + "_carriage"][0][3] -
                y["matrices_blender_m"][lane + "_carriage"][0][3]) * 1000 for x, y in zip(original, again)) for lane in ("left", "right")}
            record["reopen"] = {"pass": True, "scene_sha256": digest(artifacts / "scene.blend"),
                "native_trace_sha256": digest(directory / "reopen/native-transforms.json"),
                "all_native_samples_equal": original == again, "max_carriage_x_difference_mm": x_differences,
                "summary_path": str(directory / "reopen/summary.json"), "lanes": native_summary["lanes"],
                "cache_cleared": True, "scene_reconstructed_or_repaired": False}
            record["pass"] = True
        except (AssertionError, ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
            record["failure"] = str(error)
            failures.append({"run": label, "reason": str(error)})
        builds.append(record)
        (destination / "progress.json").write_text(json.dumps({"builds": builds, "failures": failures}, indent=2) + "\n")
        print(json.dumps({"run": label, "pass": record["pass"], "failure": record.get("failure")}), flush=True)
        if failures:
            break
    repeats = []
    identity = None
    causal = None
    if not failures and len(builds) == 9:
        for case in "ABCD":
            first, second = [row for row in builds if row["case"] == case]
            checks = {name: first["artifacts"][name]["sha256"] == second["artifacts"][name]["sha256"]
                for name in ("canonical-input.json", "final.glb", "raw.glb", "native-transforms.json")}
            passed = checks["canonical-input.json"] and checks["final.glb"]
            if not passed:
                failures.append({"run": case + "-repeat", "reason": "Formal repeated canonical input or final GLB is not deterministic"})
            repeats.append({"case": case, "pass": passed, "equality": checks, "blend_byte_identity_required": False})
        first, renamed = builds[0], builds[-1]
        identity = {"source_revisions_differ": first["source_sha256"] != renamed["source_sha256"],
            "canonical_inputs_equal": first["artifacts"]["canonical-input.json"]["sha256"] == renamed["artifacts"]["canonical-input.json"]["sha256"],
            "final_glb_bytes_equal": first["artifacts"]["final.glb"]["sha256"] == renamed["artifacts"]["final.glb"]["sha256"]}
        identity["pass"] = all(identity.values())
        if not identity["pass"]:
            failures.append({"run": "E-identity", "reason": "Rename/reorder changed semantic output"})
        a = json.loads((Path(first["artifact_directory"]) / "native-transforms.json").read_text())
        disabled = next(row for row in builds if row["case"] == "D")
        d = json.loads((Path(disabled["artifact_directory"]) / "native-transforms.json").read_text())
        invariant = ["base", "left_stop", "right_carriage", "right_shoe", "right_stop"]
        causal = {"invariant_native_parts": {name: all(x["matrices_blender_m"][name] == y["matrices_blender_m"][name]
            and x["bounds_gltf_mm"][name] == y["bounds_gltf_mm"][name] for x, y in zip(a, d)) for name in invariant},
            "A_left_final_mm": first["reopen"]["lanes"]["left"]["final_travel_mm"],
            "D_left_final_mm": disabled["reopen"]["lanes"]["left"]["final_travel_mm"]}
        causal["pass"] = all(causal["invariant_native_parts"].values())
        if not causal["pass"]:
            failures.append({"run": "A-D-causal-control", "reason": "Collider disable changed an unrelated native trajectory"})
    unchanged = inventory(repo / "prototypes/guided_contact_v01") == lock["prototype_files"] and inventory(contract) == lock["contract_files"]
    return {"version": "C191-independent-formal-batch-1", "implementation_revision": revision,
        "input_lock_sha256": digest(destination / "INPUT-LOCK.json"), "snapshot_inputs_unchanged": unchanged,
        "builds": builds, "repeat_checks": repeats, "identity": identity, "causal_control": causal,
        "failures": failures, "pass": not failures and len(builds) == 9 and unchanged,
        "maximum_continuous_mapping_mm": max((row.get("maximum_continuous_mapping_mm", 0) for row in builds), default=None),
        "maximum_native_sample_mapping_mm": max((row.get("maximum_native_sample_mapping_mm", 0) for row in builds), default=None)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--blender", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.repo.resolve(), args.out.resolve(), args.revision, args.blender.resolve())
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"pass": report["pass"], "runs": len(report["builds"]), "failures": report["failures"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)
