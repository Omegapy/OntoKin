"""Supplemental read-only Khronos and Three.js checks required by OK-ENG-002.

One Node child runs both checks after each accepted native transaction. This is
a separately frozen, at-most-twelve-check allowance, never a Blender retry or
an extension of the 65-second native transaction.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
import time

from .canonical import ROOT, json_bytes
from .lock import check_file, file_binding, read_json
from .supervisor import Clock, Stop, inventory, run_process, sha256_file

SCHEMA = "ontokin.static-tray.external-readback-lock/0.1.0"
LIMITS = {"maximum_checks": 12, "host_ms": 30000, "child_work_ms": 28000, "cleanup_ms": 2000,
          "glb_bytes": 8 * 1024 * 1024, "result_bytes": 4 * 1024 * 1024, "log_bytes": 4 * 1024 * 1024}
NODE_FLAGS = ["--no-addons", "--max-old-space-size=256"]
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
VALIDATOR_OPTIONS = {"format": "glb", "writeTimestamp": False, "maxIssues": 1000,
                     "allowed_errors": 0, "allowed_warnings": 0, "ignoredIssues": [], "external_resources": "rejected"}
THREE_OPTIONS = {"position_tolerance_m": 0.000005, "matrix_tolerance": 0.000001,
                 "node_count": 14, "mesh_count": 12, "animation_count": 0, "external_resources": "rejected"}


def _alias(path):
    path = Path(path)
    return {"resolved_path": str(path.resolve()), "symlink": path.is_symlink(),
            "link_target": os.readlink(path) if path.is_symlink() else None}


def build_manifest(output, *, node, dependencies_root, schedule_root, host_inventory):
    """Freeze actual installed bytes and commands without running a GLB check."""
    destination, node, deps = Path(output).resolve(), Path(node).resolve(), Path(dependencies_root).resolve()
    schedule = Path(schedule_root).resolve()
    if destination.exists() or schedule.exists():
        raise ValueError("Supplemental manifest and schedule must be new paths")
    version = subprocess.run([str(node), "--version"], env=ENVIRONMENT, capture_output=True, text=True, timeout=5, check=True).stdout.strip()
    if version != "v24.22.1":
        raise ValueError("The selected Node runtime must be the observed v24.22.1")
    dependency_files = {}
    for relative in ("validator/package", "indexer-view/three"):
        directory = deps / relative
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                raise ValueError("Executable dependency closure cannot contain unbound symlinks")
            if path.is_file(): dependency_files[str(path)] = file_binding(path)
    loader = deps / "tools/three_loader.mjs"
    dependency_files[str(loader)] = file_binding(loader)
    for path in (ROOT / "prototypes/static_tray_v01/readback.mjs", ROOT / "prototypes/static_tray_v01/format_check.py"):
        dependency_files[str(path)] = file_binding(path)
    validator = read_json(deps / "validator/package/package.json")
    three = read_json(deps / "indexer-view/three/package.json")
    if validator["version"] != "2.0.0-dev.3.10" or three["version"] != "0.186.1":
        raise ValueError("Retained readback dependency versions differ")
    ldd = subprocess.run(["/usr/bin/ldd", str(node)], env=ENVIRONMENT, capture_output=True, text=True, timeout=5, check=True)
    if "not found" in ldd.stdout:
        raise ValueError("Node shared-library dependency is unavailable")
    paths = {node}
    for line in ldd.stdout.splitlines():
        match = re.search(r"(?:=>\s+)?(/[^\s]+)\s+\(", line)
        if match: paths.add(Path(match.group(1)))
    host_path = Path(host_inventory).resolve()
    host = read_json(host_path, 8 * 1024 * 1024)
    paths |= {Path(row["path"]) for row in host["files"] if "loader_configuration" in row["roles"]}
    aliases = {str(path): _alias(path) for path in sorted(paths)}
    runtime = {str(path.resolve()): {**file_binding(path.resolve()), "mode": oct(stat.S_IMODE(path.resolve().stat().st_mode))} for path in paths}
    slots = read_json(ROOT / "docs/engineering/static-tray-mapping-c198/CONTROLS.json")["future_qualification_native_slots"]
    rows = []
    for slot in slots:
        stage = schedule / "external-readback" / slot["slot"]
        rows.append({"slot": slot["slot"], "case": slot["case"], "route": slot["route"], "maximum_starts": 1,
                     "stage": str(stage), "result": str(stage / "result.json"),
                     "argv": [str(node), *NODE_FLAGS, "--experimental-loader", str(loader),
                              str(ROOT / "prototypes/static_tray_v01/readback.mjs"), "--job", str(stage / "job.json")]})
    result = {"schema": SCHEMA, "profile": "ontokin.static-tray/0.1.0", "schedule_root": str(schedule),
              "dependencies_root": str(deps),
              "scope": "At most twelve separate read-only checks of accepted GLBs; no Blender, exports, simulation or retries",
              "limits": LIMITS, "environment": ENVIRONMENT, "files": dependency_files,
              "runtime": {"executable": str(node), "version": version, "files": runtime, "aliases": aliases,
                          "ldd_stdout": ldd.stdout, "host_inventory": str(host_path), **{"host_inventory_" + k: v for k, v in file_binding(host_path).items()}},
              "validator_version": validator["version"], "three_version": three["version"],
              "validator_entry": str(deps / "validator/package/index.js"), "three_package": str(deps / "indexer-view/three/package.json"),
              "three_entry": str(deps / "indexer-view/three/build/three.webgpu.js"),
              "gltf_loader_entry": str(deps / "indexer-view/three/examples/jsm/loaders/GLTFLoader.js"),
              "module_loader": str(loader), "probe": str(ROOT / "prototypes/static_tray_v01/readback.mjs"),
              "validator_options": VALIDATOR_OPTIONS, "three_options": THREE_OPTIONS,
              "slots": rows}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream: stream.write(json_bytes(result))
    return result, sha256_file(destination)


def verify_manifest(path, *, schedule_root, check=lambda: None):
    manifest = read_json(path, 1024 * 1024)
    if (manifest.get("schema") != SCHEMA or manifest.get("profile") != "ontokin.static-tray/0.1.0"
            or manifest.get("limits") != LIMITS or manifest.get("environment") != ENVIRONMENT
            or manifest.get("validator_options") != VALIDATOR_OPTIONS or manifest.get("three_options") != THREE_OPTIONS
            or manifest.get("schedule_root") != str(Path(schedule_root).resolve())):
        raise Stop("OTRAY-E-BINDING", "Supplemental readback scope, limits or environment differ")
    if manifest.get("validator_version") != "2.0.0-dev.3.10" or manifest.get("three_version") != "0.186.1" or manifest["runtime"]["version"] != "v24.22.1":
        raise Stop("OTRAY-E-BINDING", "Supplemental dependency version differs")
    deps = Path(manifest["dependencies_root"])
    expected_files = {str(p) for relative in ("validator/package", "indexer-view/three") for p in (deps / relative).rglob("*") if p.is_file()}
    expected_files |= {str(deps / "tools/three_loader.mjs"), str(ROOT / "prototypes/static_tray_v01/readback.mjs"), str(ROOT / "prototypes/static_tray_v01/format_check.py")}
    if set(manifest["files"]) != expected_files:
        raise Stop("OTRAY-E-BINDING", "Complete retained readback dependency inventory differs")
    for filename, binding in manifest["files"].items(): check_file(filename, binding, check)
    runtime = manifest["runtime"]
    check_file(runtime["host_inventory"], {"sha256": runtime["host_inventory_sha256"], "size_bytes": runtime["host_inventory_size_bytes"]}, check)
    if runtime["executable"] not in runtime["files"]:
        raise Stop("OTRAY-E-BINDING", "Node executable is outside the runtime closure")
    for filename, alias in manifest["runtime"]["aliases"].items():
        check()
        if _alias(filename) != alias: raise Stop("OTRAY-E-BINDING", "Node runtime alias changed")
    for filename, binding in manifest["runtime"]["files"].items(): check_file(filename, binding, check)
    required = {manifest[k] for k in ("validator_entry", "three_entry", "three_package", "gltf_loader_entry", "module_loader", "probe")}
    if not required <= set(manifest["files"]):
        raise Stop("OTRAY-E-BINDING", "Readback executable role is not hash-bound")
    if manifest["probe"] != str(ROOT / "prototypes/static_tray_v01/readback.mjs"):
        raise Stop("OTRAY-E-BINDING", "Readback probe belongs to another checkout")
    frozen = read_json(ROOT / "docs/engineering/static-tray-mapping-c198/CONTROLS.json")["future_qualification_native_slots"]
    if len(manifest["slots"]) != 12: raise Stop("OTRAY-E-BINDING", "Exactly twelve read-only slots are required")
    for row, slot in zip(manifest["slots"], frozen):
        stage = Path(schedule_root).resolve() / "external-readback" / slot["slot"]
        argv = [manifest["runtime"]["executable"], *NODE_FLAGS, "--experimental-loader", manifest["module_loader"], manifest["probe"], "--job", str(stage / "job.json")]
        if (any(row[k] != slot[k] for k in ("slot", "case", "route", "maximum_starts")) or row["stage"] != str(stage)
                or row["result"] != str(stage / "result.json") or row["argv"] != argv):
            raise Stop("OTRAY-E-BINDING", "Read-only checker launch or fixed slot differs")
    return manifest, sha256_file(path)


def run_check(lock, lock_hash, slot):
    from .store import verify_candidate
    from .transaction import _prior_result, alarm_until, supervised_process_clock, write_new
    clock = Clock(total_ms=LIMITS["host_ms"])
    result = {"schema": "ontokin.static-tray.external-readback-result/0.1.0", "slot": slot,
              "input_lock_sha256": lock_hash, "passed": False, "state": "REJECTED", "checker_starts": 0,
              "native_starts": 0, "exports": 0, "requested_limits": LIMITS, "effective_limits": LIMITS}
    stage = None
    created = False
    try:
        with alarm_until(clock, clock.end):
            binding = lock["external_readback"]
            check_file(binding["path"], binding, clock.check)
            manifest, manifest_hash = verify_manifest(binding["path"], schedule_root=lock["schedule_root"], check=clock.check)
            row = next(r for r in manifest["slots"] if r["slot"] == slot)
            stage = Path(row["stage"])
            stage.mkdir(parents=True, exist_ok=False)
            created = True
            write_new(stage / "finalization.pending", {"slot": slot, "input_lock_sha256": lock_hash})
            write_new(stage / "reserved.json", result)
            _, candidate, before = _prior_result(lock, slot)
            job = {"slot": slot, "case": row["case"], "manifest": binding["path"], "supplemental_manifest_sha256": manifest_hash,
                   "input_lock_sha256": lock_hash, "artifact": str(candidate / "final.glb"), "artifact_sha256": sha256_file(candidate / "final.glb"),
                   "audit": str(candidate / "independent-audit.json"), "audit_sha256": sha256_file(candidate / "independent-audit.json"),
                   "result": str(stage / "probe.json")}
            write_new(stage / "job.json", job)
            def started(process):
                result["checker_starts"] += 1
                write_new(stage / "started.json", {"slot": slot, "input_lock_sha256": lock_hash, "process": process})
            with supervised_process_clock():
                process = run_process(row["argv"], stage=stage, label="external-readback", clock=clock,
                                      stage_end=clock.started + LIMITS["child_work_ms"] / 1000,
                                      env=manifest["environment"], on_started=started)
            result["process"] = process
            clock.check()
            probe = read_json(stage / "probe.json")
            result["probe_sha256"] = sha256_file(stage / "probe.json")
            result["artifact_sha256"] = job["artifact_sha256"]
            result["supplemental_manifest_sha256"] = manifest_hash
            result["original_closure_preserved"] = verify_candidate(candidate) == before
            if (probe.get("passed") is not True or probe.get("input_lock_sha256") != lock_hash
                    or probe.get("artifact_sha256") != job["artifact_sha256"] or not result["original_closure_preserved"]
                    or not process.get("handles_closed") or not process.get("cleanup", {}).get("passed")):
                raise Stop("OTRAY-E-DELIVERY", "Supplemental readback failed or does not bind the accepted actual bytes")
            inventory(stage, clock=clock, stage_end=clock.end)
            clock.check()
            result.update(passed=True, state="ACCEPTED", validator=probe["khronos"]["version"], three=probe["three"]["version"])
    except BaseException as exc:
        result["error"] = exc.as_dict() if isinstance(exc, Stop) else {"code": "OTRAY-E-DELIVERY", "reason": type(exc).__name__ + ": " + str(exc)}
        result["state"] = exc.state if isinstance(exc, Stop) else "REJECTED"
        if hasattr(exc, "process_record"): result["process"] = exc.process_record
        if stage is not None and (stage / "probe.json").is_file():
            result["failed_probe_sha256"] = sha256_file(stage / "probe.json")
    result["elapsed_before_finalization_ms"] = clock.elapsed_ms()
    result["elapsed_ms"] = clock.elapsed_ms()
    if created:
        try:
            if result["passed"]:
                with alarm_until(clock, clock.end):
                    clock.check()
                    write_new(stage / "result.json", result)
                    clock.check()
                    (stage / "finalization.pending").unlink()
                    directory = os.open(stage, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(directory)
                    finally:
                        os.close(directory)
                    clock.check()
            else:
                # Failure evidence never authorizes another checker or native slot.
                write_new(stage / "result.json", result)
        except BaseException as exc:
            result.update(passed=False, state="UNKNOWN", finalization_error=str(exc))
            try:
                if not (stage / "finalization.pending").exists():
                    write_new(stage / "finalization.pending", {"slot": slot, "input_lock_sha256": lock_hash,
                              "reason": "Finalization requires explicit read-only reconciliation"})
                write_new(stage / "finalization.failed.json", {"slot": slot, "error": str(exc), "input_lock_sha256": lock_hash})
            except BaseException as marker_error:
                result["finalization_marker_error"] = str(marker_error)
    result["elapsed_ms"] = clock.elapsed_ms()
    if result["elapsed_ms"] > LIMITS["host_ms"]: result.update(passed=False, state="UNKNOWN")
    return result


def verify_predecessors(lock, lock_hash, slot):
    manifest = read_json(lock["external_readback"]["path"], 1024 * 1024)
    for row in manifest["slots"]:
        if int(row["slot"][1:]) >= int(slot[1:]): continue
        stage = Path(row["stage"])
        if (stage / "finalization.pending").exists() or (stage / "finalization.failed.json").exists():
            raise Stop("OTRAY-E-BINDING", "A preceding read-only result has unresolved finalization")
        result = read_json(row["result"])
        if (result.get("passed") is not True or result.get("slot") != row["slot"]
                or result.get("input_lock_sha256") != lock_hash or result.get("checker_starts") != 1
                or result.get("elapsed_before_finalization_ms", float("inf")) > LIMITS["host_ms"]):
            raise Stop("OTRAY-E-DELIVERY", "A preceding required Khronos/Three.js readback is missing or failed")
