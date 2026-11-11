#!/usr/bin/env python3
"""Execute only the four predeclared coordinator builds and their receiving checks.

No automatic retries or alternate targets are supported. The source-directory
ledger reserves this single experiment before the first native process starts.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tarfile
import time
from common import (BACKEND_SHA, BLENDER_SHA, CASES, C193, CONTRACT, HERE, REPO,
                    SOURCE_BINDING, artifact_reader, digest, load_module,
                    require, verify_freeze, write)

MATRIX = [(route + "-" + case, route, case) for case in ("G", "H") for route in ("ok", "python")]
EQUAL_FILES = ("canonical-input.json", "native-transforms.json", "raw.glb", "final.glb")


def command(label, argv, out, timeout):
    record = {"argv": list(map(str, argv)), "cwd": str(REPO), "deadline_s": timeout,
              "started_utc": datetime.now(timezone.utc).isoformat(), "completed": False}
    receipt = out / "commands" / (label + ".json")
    write(receipt, record, exclusive=True)
    started = time.monotonic()
    with (receipt.parent / (label + ".stdout.txt")).open("xb") as stdout, \
            (receipt.parent / (label + ".stderr.txt")).open("xb") as stderr:
        process = subprocess.Popen(record["argv"], cwd=REPO, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        record["pid"] = process.pid
        write(receipt, record)
        try:
            record["returncode"] = process.wait(timeout=timeout)
            record["completed"] = True
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            record.update(returncode=process.returncode, timed_out=True)
    record.update(elapsed_s=time.monotonic() - started, finished_utc=datetime.now(timezone.utc).isoformat())
    record["passed"] = record["completed"] and record["returncode"] == 0
    write(receipt, record)
    return record


def retained_artifact(destination, route, receipt):
    if receipt.get("artifact_directory"):
        artifact = Path(receipt["artifact_directory"]).resolve()
    elif route == "python":
        artifact = destination / "artifact"
    else:
        stages = list((destination / "store/attempts").glob("*/failed-stage"))
        require(len(stages) == 1, "Failed build does not identify exactly one retained stage")
        artifact = stages[0].resolve()
    require(artifact.is_relative_to(destination.resolve()), "Artifact escaped its declared run")
    require(artifact.is_dir(), "Retained artifact is missing")
    return artifact


def provenance(artifact, route, submitted):
    sys.path.insert(0, str(C193 / "independent"))
    module = load_module("c194_inherited_provenance", C193 / "independent/audit_provenance.py")
    report = module.audit(artifact, CONTRACT, C193 / "independent/evidence/candidate-review.json")
    source = artifact / ("source.ok" if route == "ok" else "source.py")
    require(source.read_bytes() == submitted.read_bytes(), "Retained source differs from frozen submission")
    require(json.loads((artifact / "canonical-input.json").read_text()) ==
            json.loads((HERE / ("frozen/" + submitted.stem + "-canonical.json")).read_text()),
            "Canonical source differs from C194 frozen input")
    if route == "ok":
        store = artifact.parent.parent
        state = json.loads((store / "state.json").read_text())
        require(state["schema"] == "ontokin.c193.store/0.1", "Wrong store namespace")
        require((store / state["artifact_directory"]).resolve() == artifact.resolve(), "Store points elsewhere")
        require(state["manifest_sha256"] == digest(artifact / "manifest.json"), "Store manifest hash differs")
    return report


def reopen(artifact, identifier, route, case, blender, out):
    source = artifact / ("source.ok" if route == "ok" else "source.py")
    dest = out / "reopens" / identifier
    argv = [blender, "--factory-startup", "-b", artifact / "scene.blend", "-t", "2",
            "--python-exit-code", "1", "--python", HERE / "inspect_scene.py", "--",
            "--out", dest, "--backend", CONTRACT / "backend.json", "--backend-sha256", BACKEND_SHA,
            "--source-binding", SOURCE_BINDING, "--source", source,
            "--canonical", artifact / "canonical-input.json", "--case", case, "--guide-frame", "carriage_center"]
    process = command("reopen-" + identifier, argv, out, 80)
    require(process["passed"], "Independent saved-scene process failed")
    summary = json.loads((dest / "summary.json").read_text())
    require(summary["pass"] and summary["cache_clear_completed"] and summary["configuration_unchanged"],
            "Saved-scene replay/configuration failed")
    require(not summary["reconstructed_or_repaired"], "Inspector reconstructed or repaired scene")
    require(summary["opened_scene_sha256"] == digest(artifact / "scene.blend"), "Inspector used another scene")
    require(summary["source_sha256"] == digest(source), "Inspector used another source")
    require(summary["canonical_input_sha256"] == digest(artifact / "canonical-input.json"), "Inspector canonical differs")
    require(summary["backend_sha256"] == BACKEND_SHA, "Inspector backend differs")
    require(summary["inspector_sha256"] == digest(C193 / "independent/inspect_scene.py"), "Inspector bytes differ")
    original = json.loads((artifact / "native-transforms.json").read_text())
    again = json.loads((dest / "native-transforms.json").read_text())
    require(len(original) == len(again) == 481 and original == again, "Reopened native sample sequence differs")
    return {"passed": True, "exact_481_sample_records_equal": True,
            "original_trace_sha256": digest(artifact / "native-transforms.json"),
            "reopened_trace_sha256": digest(dest / "native-transforms.json"),
            "summary_sha256": digest(dest / "summary.json"),
            "configuration_sha256": digest(dest / "configuration-before.json")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    args = parser.parse_args()
    frozen = verify_freeze()
    blender = args.blender.resolve()
    require(digest(blender) == BLENDER_SHA, "Pinned Blender executable differs")
    require(platform.system() == "Linux" and platform.machine() == "x86_64", "Linux x86-64 required")
    require(not args.out.exists(), "Output must be a new directory")
    ledger = {"schema": "ontokin.c194.execution-ledger/0.1", "reserved_utc": datetime.now(timezone.utc).isoformat(),
              "freeze_sha256": frozen["freeze_sha256"], "output": str(args.out.resolve()),
              "planned_builds": [row[0] for row in MATRIX], "started_builds": [],
              "automatic_retry_allowed": False, "native_target_results_previously_known": False}
    write(HERE / "EXECUTION-LEDGER.json", ledger, exclusive=True)
    args.out.mkdir(parents=True, exist_ok=False)
    out = args.out.resolve()
    write(out / "INPUT-LOCK.json", frozen, exclusive=True)
    manifest = {"schema": "ontokin.c194.coordinator-qualification/0.1",
                "started_utc": datetime.now(timezone.utc).isoformat(), "frozen_inputs": frozen,
                "implementation_revision": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
                "python": sys.version, "platform": platform.platform(), "blender_sha256": BLENDER_SHA,
                "coordinator_setup_only": True, "author_trials": 0,
                "planned_builds": 4, "runs": [], "automated_gates_passed": False,
                "qualified_for_author_dispatch": False, "visual_review_required": True}
    write(out / "RESULTS.json", manifest)
    reader = artifact_reader()
    reader.verify_frozen()
    artifacts, traces = {}, {}
    receiving_entries = []
    for identifier, route, case in MATRIX:
        verify_freeze()
        suffix = ".ok" if route == "ok" else ".py"
        source = HERE / ("sources/" + case + suffix)
        destination = out / "builds" / identifier
        ledger["started_builds"].append({"id": identifier, "started_utc": datetime.now(timezone.utc).isoformat()})
        write(HERE / "EXECUTION-LEDGER.json", ledger)
        row = {"id": identifier, "route": route, "case": case, "passed": False, "failures": [],
               "source_sha256": digest(source), "source": str(source.relative_to(REPO))}
        argv = [sys.executable, "-B", C193 / "native/build.py", "--repo", REPO, "--route", route,
                "--source", source, "--out", destination, "--blender", blender]
        process = command("build-" + identifier, argv, out, 110)
        try:
            receipt = json.loads((destination / "delivery.json").read_text())
            row["build_receipt"] = str((destination / "delivery.json").relative_to(out))
            row["build_successful"] = process["passed"] and receipt["successful"]
            row["cost"] = receipt.get("cost")
            row["build_elapsed_s"] = receipt.get("elapsed_s")
            if not row["build_successful"]:
                row["failures"].append("Producer build failed; retained diagnostics cannot make this a passing build")
            artifact = retained_artifact(destination, route, receipt)
            artifacts[identifier] = artifact
            row["artifact"] = str(artifact.relative_to(out))
            row["artifacts"] = {name: digest(artifact / name) for name in EQUAL_FILES if (artifact / name).is_file()}
            try:
                audit = provenance(artifact, route, source)
                write(out / "reports" / (identifier + "-provenance.json"), audit, exclusive=True)
                row["provenance_passed"] = True
            except Exception as error:
                row["provenance_passed"] = False
                row["failures"].append("provenance: " + type(error).__name__ + ": " + str(error))
            try:
                numerical = reader.review(artifact, case, CONTRACT / "backend.json", BACKEND_SHA, SOURCE_BINDING)
                write(out / "reports" / (identifier + "-artifact.json"), numerical, exclusive=True)
                row["numerical_passed"] = numerical["passed"]
                row["numerical_failures"] = numerical["failures"]
                row["mapping"] = numerical["mapping_measurements"]
                if not numerical["passed"]:
                    row["failures"].extend(numerical["failures"])
            except Exception as error:
                row["numerical_passed"] = False
                row["failures"].append("numerical: " + type(error).__name__ + ": " + str(error))
            try:
                row["reopen"] = reopen(artifact, identifier, route, case, blender, out)
            except Exception as error:
                row["reopen"] = {"passed": False, "failure": type(error).__name__ + ": " + str(error)}
                row["failures"].append("reopen: " + row["reopen"]["failure"])
            if (artifact / "native-transforms.json").exists():
                traces[identifier] = json.loads((artifact / "native-transforms.json").read_text())
            if all((artifact / name).is_file() for name in ("raw.glb", "final.glb")):
                receiving_entries.append({"id": identifier, "artifact": str(artifact),
                    "contact_s": CASES[case]["ideal_first_contact_s"], "final_gap_mm": 0, "render": True})
        except Exception as error:
            row["failures"].append("retained build: " + type(error).__name__ + ": " + str(error))
        row["passed"] = not row["failures"]
        manifest["runs"].append(row)
        write(out / "RESULTS.json", manifest)
        print(json.dumps({"id": identifier, "passed": row["passed"], "failures": row["failures"]}), flush=True)
    equality = []
    for case in ("G", "H"):
        cohort = [r for r in manifest["runs"] if r["case"] == case]
        equal = {name: len(cohort) == 2 and all(name in r.get("artifacts", {}) for r in cohort) and
                 len({r["artifacts"][name] for r in cohort}) == 1 for name in EQUAL_FILES}
        equality.append({"case": case, "equal": equal, "passed": all(equal.values())})
    manifest["route_equality"] = equality
    baseline_archive = REPO / "docs/engineering/contact-comparison-c192/evidence.tar.xz"
    baseline_member = "c192-runs/python/reuse-build-01/artifact/native-transforms.json"
    with tarfile.open(baseline_archive) as archive:
        baseline = json.loads(archive.extractfile(baseline_member).read())
    unchanged = {}
    for identifier, _, _ in MATRIX:
        trace = traces.get(identifier, [])
        unchanged[identifier] = {name: len(trace) == len(baseline) == 481 and all(
            a["matrices_blender_m"][name] == b["matrices_blender_m"][name] and
            a["bounds_gltf_mm"][name] == b["bounds_gltf_mm"][name] for a, b in zip(baseline, trace))
            for name in ("base", "right_carriage", "right_shoe", "right_stop")}
    manifest["unrelated_native_parts_equal_to_retained_baseline"] = unchanged
    manifest["baseline"] = {"archive": str(baseline_archive.relative_to(REPO)), "sha256": digest(baseline_archive), "member": baseline_member}
    write(out / "receiving-manifest.json", receiving_entries, exclusive=True)
    try:
        require(len(receiving_entries) == 4, "Not all four actual deliveries are available for receiving checks")
        receiver = command("receiving", [sys.executable, "-B", C193 / "tools/receive.py", "--repo", REPO,
            "--manifest", out / "receiving-manifest.json", "--blender", blender, "--out", out / "receiving"], out, 570)
        require(receiver["passed"], "Actual receiving execution failed")
        receiving = json.loads((out / "receiving/summary.json").read_text())
        require(receiving["pass_for_executed_receiving_checks"] and receiving["khronos_errors"] == 0 and
                receiving["khronos_warnings"] == 0 and receiving["glb_paths"] == 8 and
                receiving["three_poses"] == 24 and receiving["blender_import_jobs"] == 4,
                "Required receiving count or acceptance differs")
        manifest["receiving"] = {"passed": True, "summary": receiving,
                                 "summary_sha256": digest(out / "receiving/summary.json")}
    except Exception as error:
        manifest["receiving"] = {"passed": False, "failure": type(error).__name__ + ": " + str(error)}
    manifest["automated_gates_passed"] = (len(manifest["runs"]) == 4 and all(r["passed"] for r in manifest["runs"])
        and all(r["passed"] for r in equality) and all(all(row.values()) for row in unchanged.values())
        and manifest["receiving"]["passed"])
    manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["input_preservation_after_execution"] = verify_freeze()
    manifest["author_dispatch"] = "PENDING visual review and explicit final qualification" if manifest["automated_gates_passed"] else "STOP: at least one required preparation gate failed"
    write(out / "RESULTS.json", manifest)
    ledger.update(finished_utc=manifest["finished_utc"], results_sha256=digest(out / "RESULTS.json"),
                  automatic_retry_allowed=False, author_dispatch=manifest["author_dispatch"])
    write(HERE / "EXECUTION-LEDGER.json", ledger)
    write(out / "EXECUTION-LEDGER.json", ledger, exclusive=True)
    print(json.dumps({"automated_gates_passed": manifest["automated_gates_passed"],
                      "author_dispatch": manifest["author_dispatch"], "results": str(out / "RESULTS.json")}), flush=True)
    return 0 if manifest["automated_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

