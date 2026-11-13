#!/usr/bin/env python3
"""Prepare a C216 binding, launch one approved phase, or report captured loss.

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
                    verify_run, write_json)


def now():
    return datetime.now(timezone.utc).isoformat()


def git(*arguments):
    return subprocess.check_output(["git", "-C", str(ROOT), *arguments]).decode().strip()


def adapter_module():
    spec = importlib.util.spec_from_file_location("_c216_c215_adapter", HERE.parent / "receiving-adapter-c215/adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_command(run, phase, executable):
    return [executable, "--background", "--factory-startup", "--disable-autoexec", "--threads", "2",
            "--python-exit-code", "19", "--python", str(HERE / "capture.py"), "--", "--run", str(run), "--phase", phase]


def prepare(run):
    require(not run.exists(), "Prepared run directory already exists; never replace an earlier attempt")
    require(not git("status", "--porcelain"), "Capture checkout must be committed and clean")
    revision, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    build = read_json(HERE / "build_bindings.json")
    verify_installed(build)
    adapter = adapter_module()
    original = HERE.parent / "semantic-export-c210/evidence/proof"
    source_names = ("after.glb", "after.program.bundle.json", "after.semantic.json", "after.reference.json")
    source_bytes = {name: (original / name).read_bytes() for name in source_names}
    require(descriptor(source_bytes["after.reference.json"])["sha256"] == "sha256:b8df15b2645caaa523a79116912ddbfb9db1eb293c2f1f6d3e190b212bcd8a55", "Frozen reference bytes differ")
    payload = adapter.source.build_payload(source_bytes["after.glb"], source_bytes["after.program.bundle.json"], source_bytes["after.semantic.json"])
    paths = [HERE / name for name in SOURCE_NAMES]
    paths += [HERE.parent / "receiving-adapter-c215/adapter.py", HERE.parent / "source-normals-c214/prototype.py"]
    source_bundle = {"schema": "ontokin.c216.receiver-source-bytes/0.1", "revision": revision, "tree": tree, "files": {}}
    for path in paths:
        name = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        committed = subprocess.check_output(["git", "-C", str(ROOT), "show", revision + ":" + name])
        require(raw == committed, "Receiver source differs from committed revision: " + name)
        source_bundle["files"][name] = base64.b64encode(raw).decode("ascii")
    run.mkdir(parents=True)
    (run / "inputs").mkdir()
    for name, raw in source_bytes.items():
        (run / "inputs" / name).write_bytes(raw)
    write_json(run / "inputs/source-payload.json", payload, exclusive=True)
    write_json(run / "receiver-source.json", source_bundle, exclusive=True)
    importer = importer_archive(build["importer_root"])
    (run / "importer-source.tar").write_bytes(importer)
    write_json(run / "build-record.json", {"application": "Blender", "version": build["version"],
        "executableSha256": "sha256:" + build["executable"]["sha256"], "buildHash": build["build_hash"],
        "importerSourceSha256": digest(importer)}, exclusive=True)
    settings = {name: value["default"] for name, value in build["importer_properties"].items()}
    settings["filepath"], settings["files"] = str(run / "inputs/after.glb"), []
    write_json(run / "import-settings.json", settings, exclusive=True)
    files = {str(path.relative_to(run)): descriptor(path.read_bytes()) for path in sorted(run.rglob("*")) if path.is_file()}
    plan = {"schema": "ontokin.c216.native-plan/0.1", "preparedAtUtc": now(),
        "sourceRevision": revision, "sourceTree": tree, "captureSourceDirectory": str(HERE), "runDirectory": str(run),
        "acceptedRevision": read_json(run / "inputs/after.semantic.json")["binding"]["accepted_program_revision"],
        "sourcePayloadSha256": digest(canonical(payload)), "sourceInputs": adapter.source.ACCEPTED_INPUTS,
        "files": files, "executable": build["executable"], "importerRoot": build["importer_root"],
        "maxNativeStarts": 2, "maximumSecondsPerStart": 240, "maximumThreads": 2,
        "sequence": ["import", "independent numeric/provenance/visual review", "reopen", "independent final review"],
        "commands": {phase: native_command(run, phase, build["executable"]["path"]) for phase in ("import", "reopen")},
        "render": {"engine": "CYCLES", "device": "CPU", "samples": 16, "resolution": [960, 720],
            "seed": 216, "use_denoising": False, "view_layer_use_denoising": False, "maxImagesPerPhase": 2,
            "views": [{"name": "overview", "time_seconds": 0, "eye_source_m": [4, 3, 7], "target_source_m": [0, 0, 0], "ortho_scale": 5.3},
                      {"name": "sphere-detail", "time_seconds": 0, "eye_source_m": [-0.73, 0.18, 0.45], "target_source_m": [-1, 0, 0], "ortho_scale": 0.32}]},
        "environmentOverrides": {"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "SDL_AUDIODRIVER": "dummy"},
        "isolatedBlenderDirectories": ["BLENDER_USER_CONFIG", "BLENDER_USER_SCRIPTS", "BLENDER_USER_DATAFILES"],
        "importerCachePolicy": "No installed .pyc/.pyo; initial prefix must be null; capture sets a new empty phase-private prefix and disables bytecode writing; actual loaded module source/cache/flag receipts required",
        "normalPolicy": "Exact retained source authority plus measured native shading and disclosed loss; no new normal tolerance and no C211 strict pass",
        "sceneBindingPolicy": "Immutable prelaunch identities first; final C215 lock adds actual saved scene descriptor after native save; independent verifier checks all prelaunch identities unchanged",
        "failureStop": ["Any changed input/source/build/settings", "Missing/ambiguous/invalid exact-position mapping", "Native failure or timeout", "Missing artifact or unusable visual evidence", "Unknown process outcome"],
        "retryPolicy": "No automatic retries. Any attempted or unknown phase reservation is consumed; reconcile before a separately reviewed future task.",
        "python": sys.version, "platform": platform.platform(), "nativeProcessesStarted": 0}
    write_json(run / "plan.json", plan, exclusive=True)
    verify_run(run, HERE)
    return {"prepared": True, "planSha256": digest(canonical(plan)), "revision": revision, "run": str(run), "nativeStarts": 0}


def approval_record(run, plan, phase, path):
    approval = read_json(path)
    require(approval["schema"] == "ontokin.c216.native-approval/0.1", "Unknown approval schema")
    require(approval["decision"] == "APPROVE_NATIVE_START" and approval["phase"] == phase, "Phase approval missing")
    require(approval["sourceRevision"] == plan["sourceRevision"] and approval["planSha256"] == digest(canonical(plan)), "Approval binds different source or plan")
    require(approval["maxNativeStarts"] == 2 and bool(approval["integrator"]), "Invalid integration approval")
    review = approval["independentReview"]
    require(descriptor(Path(review["path"]).read_bytes()) == review["file"], "Independent review bytes differ")
    if phase == "reopen":
        required = {"received.blend", "input-lock.json", "import-process.json", "import-native-complete.json",
                    "import-observations.json", "import-details.json", "import-overview.png", "import-sphere-detail.png"}
        bindings = approval["priorImportEvidence"]
        require(required <= set(bindings), "Reopen approval omits import evidence")
        for name, binding in bindings.items():
            require(Path(name).name == name, "Reopen evidence path must be a run basename")
            require(descriptor((run / name).read_bytes()) == binding, "Independently reviewed import artifact changed: " + name)
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
    require(plan["maxNativeStarts"] == 2 and plan["maximumSecondsPerStart"] == 240, "Finite native budget changed")
    command = native_command(run, phase, build["executable"]["path"])
    require(command == plan["commands"][phase], "Native command changed")
    reservations = list(run.glob("*-reservation.json"))
    if phase == "import":
        require(not reservations, "A native start has already been reserved")
    else:
        require({p.name for p in reservations} == {"import-reservation.json"}, "Reopen requires exactly one prior import reservation")
        previous = read_json(run / "import-process.json")
        require(previous["outcome"] == "COMPLETED" and previous["returncode"] == 0 and not previous["groupStillExists"], "Import outcome is not known complete")
        require(not (run / "import-native-failure.json").exists(), "Import failure forbids reopen")
        require(final_lock(run, plan) == read_json(run / "input-lock.json"), "Saved scene binding changed")
    environment = os.environ.copy()
    environment.update(plan["environmentOverrides"])
    for variable in plan["isolatedBlenderDirectories"]:
        directory = run / "isolated-user" / phase / variable.lower()
        directory.mkdir(parents=True, exist_ok=False)
        environment[variable] = str(directory)
    reservation = {"schema": "ontokin.c216.native-reservation/0.1", "phase": phase, "reservedAtUtc": now(),
        "sourceRevision": plan["sourceRevision"], "planSha256": digest(canonical(plan)),
        "approval": descriptor(Path(approval_path).read_bytes()), "command": command,
        "maximumSeconds": 240, "outcome": "RESERVED_UNKNOWN_UNTIL_PROCESS_RECEIPT", "attemptOrdinal": len(reservations) + 1,
        "installedImporterBytecodeFiles": sorted(str(path) for suffix in ("*.pyc", "*.pyo") for path in Path(build["importer_root"]).rglob(suffix))}
    require(not reservation["installedImporterBytecodeFiles"], "Importer bytecode appeared before reservation")
    write_json(run / (phase + "-approval.json"), approval, exclusive=True)
    write_json(run / (phase + "-reservation.json"), reservation, exclusive=True)
    start = time.monotonic()
    process, timed_out = None, False
    receipt = {"schema": "ontokin.c216.native-process/0.1", "phase": phase, "command": command,
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
        elif process.poll() is not None:
            receipt["returncode"], receipt["groupStillExists"] = process.returncode, group_exists(process.pid)
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
    artifacts["scene"] = (run / "received.blend").read_bytes()
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
    parser.add_argument("--phase", choices=("import", "reopen"))
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    if args.command == "prepare":
        result = prepare(run)
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
