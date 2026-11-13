#!/usr/bin/env python3
"""Prepare C218 exact saved-scene bindings, launch one reviewed reopen, or report loss.

Preparation/check/report are CPU-only. Only the explicit launch subcommand
can start Blender, and it requires an independent-review/root approval record.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from common import (ARTIFACT_NAMES, SOURCE_NAMES, canonical, descriptor, digest,
                    final_lock, importer_archive, read_json, require, verify_installed,
                    SCENE_DESCRIPTOR, PRIOR_PLAN_SHA256, PRIOR_SOURCE_REVISION, RENDER_RECIPE,
                    REOPEN_ENVIRONMENT, ISOLATED_DIRECTORIES, verify_scene, native_command as expected_native_command,
                    verify_run, write_json)


def now():
    return datetime.now(timezone.utc).isoformat()


def git(*arguments):
    return subprocess.check_output(["git", "-C", str(ROOT), *arguments]).decode().strip()


def adapter_module():
    spec = importlib.util.spec_from_file_location("_c218_c215_adapter", HERE.parent / "receiving-adapter-c215/adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_command(run, phase, executable):
    return expected_native_command(run, phase, executable, HERE)


def prepare(run, prior_run):
    require(not run.exists(), "Prepared run directory already exists; never replace an earlier attempt")
    require(not git("status", "--porcelain"), "Observer checkout must be committed and clean")
    revision, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    build = read_json(HERE / "build_bindings.json")
    verify_installed(build)
    prior_run = Path(prior_run).resolve()
    scene_path = verify_scene(prior_run / "received.blend")
    prior_plan = read_json(prior_run / "plan.json")
    require(digest(canonical(prior_plan)) == PRIOR_PLAN_SHA256 and prior_plan["sourceRevision"] == PRIOR_SOURCE_REVISION,
            "The supplied prior plan is not the closed executed C217 plan")
    require(prior_plan["render"] == RENDER_RECIPE, "C217 recorded render recipe differs")
    prior_lock = read_json(prior_run / "input-lock.json")
    require(prior_lock["artifacts"]["scene"] == SCENE_DESCRIPTOR, "C217 final lock binds another scene")
    for name, entry in prior_plan["files"].items():
        require(descriptor((prior_run / name).read_bytes()) == entry, "Prior prepared artifact changed: " + name)
    prior_complete = read_json(prior_run / "import-native-complete.json")
    require(prior_complete["inputLockSha256"] == digest(canonical(prior_lock))
            and prior_complete["planSha256"] == PRIOR_PLAN_SHA256
            and prior_complete["scene"] == SCENE_DESCRIPTOR, "Prior completion bindings differ")
    for key, name in (("observations", "import-observations.json"), ("details", "import-details.json")):
        require(descriptor((prior_run / name).read_bytes()) == prior_complete[key], "Prior result bytes differ: " + name)
    prior_process = read_json(prior_run / "import-process.json")
    require(prior_process["outcome"] == "COMPLETED" and prior_process["returncode"] == 0
            and prior_process["timedOut"] is False and prior_process["groupStillExists"] is False,
            "Prior import outcome is incomplete or unknown")
    adapter = adapter_module()
    source_names = ("after.glb", "after.program.bundle.json", "after.semantic.json", "after.reference.json", "source-payload.json")
    source_bytes = {name: (prior_run / "inputs" / name).read_bytes() for name in source_names}
    payload = read_json(prior_run / "inputs/source-payload.json")
    rebuilt = adapter.source.build_payload(source_bytes["after.glb"], source_bytes["after.program.bundle.json"], source_bytes["after.semantic.json"])
    require(canonical(payload) == canonical(rebuilt), "Retained source-normal authority differs from accepted source")
    paths = [HERE / name for name in SOURCE_NAMES]
    paths += [HERE.parent / "receiving-adapter-c215/adapter.py", HERE.parent / "source-normals-c214/prototype.py"]
    source_bundle = {"schema": "ontokin.c218.observer-source-bytes/0.1", "revision": revision, "tree": tree, "files": {}}
    for path in paths:
        name, raw = path.relative_to(ROOT).as_posix(), path.read_bytes()
        committed = subprocess.check_output(["git", "-C", str(ROOT), "show", revision + ":" + name])
        require(raw == committed, "Observer source differs from committed revision: " + name)
        source_bundle["files"][name] = base64.b64encode(raw).decode("ascii")
    run.mkdir(parents=True)
    (run / "inputs").mkdir()
    (run / "prior").mkdir()
    for name, raw in source_bytes.items():
        (run / "inputs" / name).write_bytes(raw)
    prior_names = ("plan.json", "input-lock.json", "import-settings.json", "import-native-complete.json",
                   "import-process.json", "import-observations.json", "import-details.json")
    for name in prior_names:
        (run / "prior" / name).write_bytes((prior_run / name).read_bytes())
    write_json(run / "receiver-source.json", source_bundle, exclusive=True)
    importer = importer_archive(build["importer_root"])
    require(importer == (prior_run / "importer-source.tar").read_bytes(), "Installed importer differs from C217 source")
    (run / "importer-source.tar").write_bytes(importer)
    (run / "build-record.json").write_bytes((prior_run / "build-record.json").read_bytes())
    settings = {"operation": "reopen_saved_scene", "filepath": str(scene_path), "load_ui": False, "use_scripts": False,
                "renderRecipe": RENDER_RECIPE, "originalImportSettings": read_json(run / "prior/import-settings.json")}
    write_json(run / "reopen-settings.json", settings, exclusive=True)
    plan = {"schema": "ontokin.c218.native-reopen-plan/0.1", "preparedAtUtc": now(),
        "sourceRevision": revision, "sourceTree": tree, "captureSourceDirectory": str(HERE), "runDirectory": str(run),
        "scenePath": str(scene_path), "sceneArchivePath": "agent-results/namespace-repair/run-01/received.blend", "scene": SCENE_DESCRIPTOR,
        "priorPlanSha256": PRIOR_PLAN_SHA256, "priorSourceRevision": PRIOR_SOURCE_REVISION,
        "acceptedRevision": read_json(run / "inputs/after.semantic.json")["binding"]["accepted_program_revision"],
        "sourcePayloadSha256": digest(canonical(payload)), "sourceInputs": adapter.source.ACCEPTED_INPUTS,
        "executable": build["executable"], "importerRoot": build["importer_root"],
        "maxNativeStarts": 1, "maximumSecondsPerStart": 240, "maximumThreads": 2,
        "sequence": ["reopen", "independent persistence/numeric/provenance/visual review", "handoff and stop"],
        "commands": {"reopen": native_command(run, "reopen", build["executable"]["path"])},
        "render": RENDER_RECIPE, "environmentOverrides": REOPEN_ENVIRONMENT,
        "isolatedBlenderDirectories": ISOLATED_DIRECTORIES,
        "importerCachePolicy": "C217 exact raw-first namespace/concrete guards unchanged; no installed bytecode; new empty private prefix; no module reload",
        "normalPolicy": "Exact source authority and measured native loss; exact import/reopen equality assessed separately; original strict2e-6 gate remains failed; no new tolerance",
        "sceneBindingPolicy": "Exact C217 scene prebound before launch; open once with scripts disabled; no reimport, save, repair, text/mapping or product geometry mutation",
        "denominators": {"objects": 18, "triangles": 7800, "corners": 23400, "times": [0, 0.25, 0.5, 0.75, 1, 1.5, 2], "poses": 126},
        "failureStop": ["Changed source/input/build/settings", "Missing authority or persisted recipe", "Incomplete/invalid geometry or measurements", "Native failure/timeout", "Missing or unusable visual", "Unknown process outcome"],
        "retryPolicy": "At most one start. Any reservation/unknown attempt consumes the allowance; no automatic retry or rerender.",
        "python": sys.version, "platform": platform.platform(), "nativeProcessesStarted": 0}
    write_json(run / "input-lock.json", final_lock(run, plan), exclusive=True)
    plan["files"] = {str(path.relative_to(run)): descriptor(path.read_bytes()) for path in sorted(run.rglob("*")) if path.is_file()}
    write_json(run / "plan.json", plan, exclusive=True)
    verify_run(run, HERE)
    return {"prepared": True, "planSha256": digest(canonical(plan)), "revision": revision, "run": str(run), "nativeStarts": 0, "scene": SCENE_DESCRIPTOR}


def approval_record(run, plan, phase, path):
    require(phase == "reopen", "C218 permits no import approval")
    approval = read_json(path)
    require(approval["schema"] == "ontokin.c218.native-reopen-approval/0.1", "Unknown approval schema")
    require(approval["decision"] == "APPROVE_NATIVE_START" and approval["phase"] == phase, "Phase approval missing")
    require(approval["sourceRevision"] == plan["sourceRevision"] and approval["planSha256"] == digest(canonical(plan)), "Approval binds different source or plan")
    require(approval["maxNativeStarts"] == 1 and bool(approval["integrator"]), "Invalid integration approval")
    review = approval["independentReview"]
    require(descriptor(Path(review["path"]).read_bytes()) == review["file"], "Independent review bytes differ")
    return approval


def group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def launch(run, phase, approval_path):
    plan, build = verify_run(run, HERE)
    require(git("rev-parse", "HEAD") == plan["sourceRevision"] and not git("status", "--porcelain"), "Capture checkout revision/status changed")
    approval = approval_record(run, plan, phase, approval_path)
    require(plan["maxNativeStarts"] == 1 and plan["maximumSecondsPerStart"] == 240, "Finite native budget changed")
    command = native_command(run, phase, build["executable"]["path"])
    require(command == plan["commands"][phase], "Native command changed")
    reservations = list(run.glob("*-reservation.json"))
    require(phase == "reopen" and not reservations, "C218 permits one unreserved reopen start only")
    environment = os.environ.copy()
    environment.update(plan["environmentOverrides"])
    for variable in plan["isolatedBlenderDirectories"]:
        directory = run / "isolated-user" / phase / variable.lower()
        directory.mkdir(parents=True, exist_ok=False)
        environment[variable] = str(directory)
    reservation = {"schema": "ontokin.c218.native-reopen-reservation/0.1", "phase": phase, "reservedAtUtc": now(),
        "sourceRevision": plan["sourceRevision"], "planSha256": digest(canonical(plan)),
        "approval": descriptor(Path(approval_path).read_bytes()), "command": command,
        "maximumSeconds": 240, "outcome": "RESERVED_UNKNOWN_UNTIL_PROCESS_RECEIPT", "attemptOrdinal": len(reservations) + 1,
        "installedImporterBytecodeFiles": sorted(str(path) for suffix in ("*.pyc", "*.pyo") for path in Path(build["importer_root"]).rglob(suffix))}
    require(not reservation["installedImporterBytecodeFiles"], "Importer bytecode appeared before reservation")
    write_json(run / (phase + "-approval.json"), approval, exclusive=True)
    write_json(run / (phase + "-reservation.json"), reservation, exclusive=True)
    start = time.monotonic()
    process, timed_out = None, False
    receipt = {"schema": "ontokin.c218.native-reopen-process/0.1", "phase": phase, "command": command,
        "cwd": str(run), "startedAtUtc": now(), "environmentOverrides": {k: environment[k] for k in list(plan["environmentOverrides"]) + plan["isolatedBlenderDirectories"]},
        "outcome": "UNKNOWN", "pid": None, "returncode": None, "groupStillExists": None}
    try:
        with (run / (phase + "-stdout.log")).open("xb") as stdout, (run / (phase + "-stderr.log")).open("xb") as stderr:
            process = subprocess.Popen(command, cwd=run, env=environment, stdout=stdout, stderr=stderr, start_new_session=True)
            receipt["pid"] = process.pid
            write_json(run / (phase + "-launched.json"), {"pid": process.pid, "phase": phase, "launchedAtUtc": now()}, exclusive=True)
            try:
                process.wait(timeout=240)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
        receipt["returncode"] = process.returncode
        receipt["groupStillExists"] = group_exists(process.pid)
        receipt["outcome"] = "FAILED_TIMEOUT" if timed_out else "FAILED"
        if process.returncode == 0 and not receipt["groupStillExists"] and (run / (phase + "-native-complete.json")).is_file() and not (run / (phase + "-native-failure.json")).exists():
            verify_run(run, HERE)
            require(final_lock(run, plan) == read_json(run / "input-lock.json"), "Post-process scene binding changed")
            receipt["outcome"] = "COMPLETED"
    except BaseException as exc:
        receipt["exception"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        if process is None:
            receipt["outcome"] = "LAUNCH_FAILED_NO_PROCESS_OBSERVED"
        else:
            if process.poll() is None:
                receipt["outcome"] = "EXCEPTION_REQUIRES_OWNED_GROUP_CLEANUP"
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                    receipt["exceptionCleanupSignal"] = "SIGKILL"
                    process.wait(timeout=10)
                except BaseException as cleanup_exc:
                    receipt["exceptionCleanupFailure"] = {"type": type(cleanup_exc).__name__, "message": str(cleanup_exc)}
                    receipt["outcome"] = "UNKNOWN_EXCEPTION_CLEANUP"
            if process.poll() is not None:
                receipt["returncode"], receipt["groupStillExists"] = process.returncode, group_exists(process.pid)
                if receipt["groupStillExists"] is False:
                    receipt["outcome"] = "FAILED_EXCEPTION_PROCESS_STOPPED"
            else:
                receipt["groupStillExists"] = group_exists(process.pid)
        raise
    finally:
        receipt["endedAtUtc"], receipt["elapsedSeconds"], receipt["timedOut"] = now(), time.monotonic() - start, timed_out
        write_json(run / (phase + "-process.json"), receipt, exclusive=True)
    return receipt


def report(run, phase):
    plan, _ = verify_run(run, HERE)
    adapter = adapter_module()
    payload = read_json(run / "inputs/source-payload.json")
    observations = read_json(run / (phase + "-observations.json"))
    lock = read_json(run / "input-lock.json")
    require(lock == final_lock(run, plan), "Final lock differs from actual artifacts")
    artifacts = {name: (run / filename).read_bytes() for name, filename in ARTIFACT_NAMES.items()}
    artifacts["scene"] = verify_scene(plan["scenePath"]).read_bytes()
    result = adapter.build_report(payload, observations, (run / "inputs/after.glb").read_bytes(),
        (run / "inputs/after.program.bundle.json").read_bytes(), (run / "inputs/after.semantic.json").read_bytes(), input_lock=lock, artifacts=artifacts)
    write_json(run / (phase + "-loss-report.json"), result, exclusive=True)
    return {"phase": phase, "summary": result["summary"], "nativeFidelityEstablished": result["nativeFidelityEstablished"],
        "receivingEvidence": result["receivingEvidence"], "provenanceAuthenticated": result["provenanceAuthenticated"],
        "shadingAcceptance": result["shadingAcceptance"], "report": str(run / (phase + "-loss-report.json"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "check", "launch", "report"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--phase", choices=("reopen",))
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--prior-run", type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    if args.command == "prepare":
        require(args.prior_run is not None, "Preparation requires the exact prior run directory")
        result = prepare(run, args.prior_run.resolve())
    elif args.command == "check":
        plan, _ = verify_run(run, HERE)
        result = {"verified": True, "planSha256": digest(canonical(plan)), "nativeStarts": len(list(run.glob("*-reservation.json")))}
    elif args.command == "launch":
        require(args.phase is not None and args.approval is not None, "Launch requires phase and exact approval")
        result = launch(run, args.phase, args.approval.resolve())
    else:
        require(args.phase is not None, "Report requires phase")
        result = report(run, args.phase)
    print(canonical(result).decode())
    if args.command == "launch" and result["outcome"] != "COMPLETED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
