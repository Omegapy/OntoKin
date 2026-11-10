"""One source/build/artifact commit point; failures retain previous accepted bytes."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

from .api import _envelope, _failure, _read_source
from .common import Budget, CONTRACT, Failure, canonical_bytes, load_contract, schema_check, sha256, strict_json
from .glb import encode_raw, project, verify_mapping
from .native_validation import validate_native, validate_scene_artifact, write_native_evidence
from .supervisor import check_sizes, staged_size, supervise


def file_hash(path, budget=None):
    with Path(path).open("rb") as stream:
        digest = hashlib.sha256()
        while True:
            if budget:
                budget.check()
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        if budget:
            budget.check()
        return digest.hexdigest()


def load_state(store):
    path = store / "state.json"
    if not path.exists():
        return None
    state = strict_json(path.read_bytes())
    required = {"schema", "accepted_revision", "canonical_input_sha256", "artifact_directory", "manifest_sha256"}
    if set(state) != required or state["schema"] != "ontokin.c191.store/0.1":
        raise ValueError("Malformed accepted store state")
    if not (store / state["artifact_directory"]).resolve().is_relative_to(store.resolve()):
        raise ValueError("Accepted artifact path escapes store")
    return state


def verify_backend(blender, context, result, backend, budget):
    path = Path(blender)
    span = context.span(context.headers["backend"])
    if not path.is_file() or not os.access(path, os.X_OK):
        raise Failure("E_BACKEND_MISSING", "Pinned Blender executable is unavailable", span)
    digest = file_hash(path, budget)
    result["runtime"]["executable_sha256"] = digest
    if digest != backend["runtime"]["executable_sha256"] or platform.system() != "Linux" or platform.machine() != "x86_64":
        raise Failure("E_BACKEND_MISMATCH", "Backend executable or platform is unqualified", span)
    return path.resolve()


def write_mapping(stage, native_result, context, backend):
    rows = []
    for item in backend["native_objects"]:
        name = item["name"]
        obj = native_result["configuration"]["objects"][name]
        collider = item.get("source_collider")
        rows.append({"source_revision": context.sha, "source_occurrence": obj["properties"]["source_occurrence"],
                     "source_part": item.get("source_part"), "body_id": item.get("source_body"),
                     "collider_id": collider, "native_object": name, "native_parent": obj["parent"],
                     "native_shape": obj["rigid_body"]["collision_shape"] if obj["rigid_body"] else None,
                     "native_absent": bool(collider and obj["rigid_body"] is None),
                     "mass_contribution_kg": item.get("mass_count_kg", 0),
                     "role": item["kind"], "geometry_derivation": item.get("geometry"),
                     "frame_derivation": item.get("frame"), "native_initial_matrix_m": obj["matrix_world"],
                     "native_local_translation_m": obj["location"]})
    mapping = {"source_sha256": context.sha, "canonical_input_sha256": context.canonical_sha,
               "backend": context.canonical["backend"], "axis_mapping": backend["axis_mapping"],
               "moving_mass_total_kg": sum(body["mass_kg"] for body in context.canonical["bodies"].values()),
               "source_colliders": context.canonical["colliders"], "rows": rows}
    (stage / "mapping.json").write_bytes(canonical_bytes(mapping))


def _sync_file(path):
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def write_receipt(path, value, committed):
    """A receipt delivery error cannot change the store's commit outcome."""
    try:
        Path(path).write_bytes(canonical_bytes(value))
        return None
    except OSError as exc:
        message = str(exc)
        print("C191 receipt delivery failed at " + str(path)
              + "; committed=" + str(committed).lower()
              + "; accepted store state is unchanged: " + message, file=sys.stderr)
        return message


def retain_implementation(stage, budget):
    package = Path(__file__).parent
    destination = stage / "implementation"
    destination.mkdir()
    files = {}
    for path in sorted(package.glob("*.py")):
        budget.check()
        data = path.read_bytes()
        (destination / path.name).write_bytes(data)
        files[path.name] = {"sha256": sha256(data), "bytes": len(data)}
    repo = package.parents[1]
    identity = {}
    for key, arguments in (("git_head", ["rev-parse", "HEAD"]),
                           ("worktree_status", ["status", "--porcelain", "--untracked-files=normal", "--", "prototypes/guided_contact_v01"])):
        command = subprocess.run(["git", "-C", str(repo), *arguments], capture_output=True, text=True, timeout=1)
        identity[key] = command.stdout.strip() if command.returncode == 0 else None
    identity["files"] = files
    identity["meaning"] = "Exact executed implementation file bytes; git_head alone does not identify dirty worktree bytes. Native worker runs the retained script copy."
    (stage / "implementation-manifest.json").write_bytes(canonical_bytes(identity))


def run_transaction(source, *, store, blender, host_max_operations=100000, host_max_elapsed_ms=30000,
                    expected_revision=None, cancel_file=None, reopen=None, result_path=None, hooks=None):
    hooks = hooks or {}
    budget = Budget(host_max_operations, host_max_elapsed_ms, cancel_file)
    contract = load_contract()
    backend = contract["backend"]
    attempt = uuid.uuid4().hex
    result = _envelope(attempt, budget)
    store = Path(store).resolve()
    context = None
    stage = None
    candidate = None
    lock = None
    attempt_dir = None
    committed = False
    try:
        store.mkdir(parents=True, exist_ok=True)
        attempt_dir = store / "attempts" / attempt
        attempt_dir.mkdir(parents=True)
        lock = (store / ".write-lock").open("a+b")
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                budget.check()
                time.sleep(0.05)
        previous = load_state(store)
        result["accepted_revision"] = result["previous_revision"] = previous["accepted_revision"] if previous else None
        context = _read_source(source, budget, contract, result)
        if expected_revision is not None and expected_revision != result["accepted_revision"]:
            raise Failure("E_STALE_REVISION", "Expected accepted revision is stale", context.span(context.header_range))
        executable = verify_backend(blender, context, result, backend, budget)
        budget.check()
        stage = store / ".staging" / attempt
        stage.mkdir(parents=True)
        (stage / "source.ok").write_bytes(context.data)
        (stage / "canonical-input.json").write_bytes(context.canonical_bytes)
        (stage / "source-manifest.json").write_bytes(canonical_bytes(context.source_manifest))
        (stage / "backend.json").write_bytes((CONTRACT / "backend.json").read_bytes())
        if reopen and Path(reopen).stat().st_size > backend["limits"]["staged_output_bytes"]:
            raise Failure("E_RESOURCE_LIMIT", "Native reopen input exceeds output ceiling", budget.anchor)
        retain_implementation(stage, budget)
        (stage / "attempt-context.json").write_bytes(canonical_bytes({"attempt_id": attempt,
            "source_sha256": context.sha, "canonical_input_sha256": context.canonical_sha,
            "trusted_host_test_hooks": sorted(hooks), "formal_native_qualification_run": not bool(hooks),
            "reopen_input": str(Path(reopen).resolve()) if reopen else None,
            "reopen_input_sha256": file_hash(reopen, budget) if reopen else None}))
        command = [str(executable), "--factory-startup", "-b", "-t", str(backend["runtime"]["threads"]),
                   "--python-exit-code", str(backend["runtime"]["python_exit_code"]), "--python",
                   str(stage / "implementation" / "native_worker.py"), "--", str(stage / "canonical-input.json"),
                   str(stage / "source-manifest.json"), str(stage / "backend.json"), str(stage)]
        if reopen:
            command += ["--reopen", str(Path(reopen).resolve())]
        budget.charge("scheduled_native_substeps", backend["limits"]["scheduled_native_substeps"])
        supervise(command, stage, budget, backend, context.span(context.headers["backend"]), hooks)
        if file_hash(executable, budget) != backend["runtime"]["executable_sha256"]:
            raise Failure("E_BACKEND_MISMATCH", "Backend executable changed during attempt", context.span(context.headers["backend"]))
        budget.check()
        if "before_native_validation" in hooks:
            hooks["before_native_validation"](stage)
        check_sizes(stage, budget, backend["limits"])
        native = validate_native(stage / "native-result.json", context, budget, contract)
        validate_scene_artifact(stage / "scene.blend", context, budget, contract)
        result["runtime"]["build_hash"] = native["blender_build_hash"]
        result["levels"]["constructed"] = result["levels"]["evaluated"] = True
        write_native_evidence(stage, native, context)
        write_mapping(stage, native, context, backend)
        encode_raw(stage, native, context, budget, backend)
        if "before_projection" in hooks:
            hooks["before_projection"](stage)
        try:
            project(stage, budget)
        except Failure:
            raise
        except (ValueError, AssertionError, KeyError, TypeError, IndexError) as exc:
            raise Failure("E_MAPPING", str(exc), context.span(context.headers["output"])) from exc
        if "before_mapping_validation" in hooks:
            hooks["before_mapping_validation"](stage)
        verify_mapping(stage, native, context, budget)
        result["levels"]["exported"] = True
        if "before_publication_validation" in hooks:
            hooks["before_publication_validation"](stage)
        budget.check()
        check_sizes(stage, budget, backend["limits"])
        if load_state(store) != previous:
            raise Failure("E_STALE_REVISION", "Accepted revision changed before publication", context.span(context.header_range))
        files = {str(path.relative_to(stage)): {"sha256": file_hash(path, budget), "bytes": path.stat().st_size}
                 for path in sorted(stage.rglob("*")) if path.is_file()}
        (stage / "manifest.json").write_bytes(canonical_bytes({"source_sha256": context.sha,
            "canonical_input_sha256": context.canonical_sha, "files": files}))
        files["manifest.json"] = {"sha256": file_hash(stage / "manifest.json", budget), "bytes": (stage / "manifest.json").stat().st_size}
        check_sizes(stage, budget, backend["limits"])
        for path in stage.rglob("*"):
            if path.is_file():
                _sync_file(path)
        candidate = store / "artifacts" / attempt
        candidate.parent.mkdir(parents=True, exist_ok=True)
        os.rename(stage, candidate)
        stage = None
        state = {"schema": "ontokin.c191.store/0.1", "accepted_revision": context.sha,
                 "canonical_input_sha256": context.canonical_sha,
                 "artifact_directory": str(candidate.relative_to(store)), "manifest_sha256": files["manifest.json"]["sha256"]}
        state_temp = store / (".state-" + attempt + ".json")
        state_temp.write_bytes(canonical_bytes(state))
        _sync_file(state_temp)
        budget.check()
        try:
            hooks.get("replace_state", os.replace)(state_temp, store / "state.json")
        except OSError as exc:
            raise Failure("E_PUBLICATION", str(exc), context.span(context.headers["output"])) from exc
        # This pointer replacement is the sole commit point. Do not turn later
        # optional receipt delivery errors into a fictitious rollback.
        committed = True
        result.update(successful=True, committed=True, accepted_revision=context.sha,
                      artifact_directory=str(candidate), artifacts=files)
    except Failure as exc:
        _failure(result, exc, contract)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        code = "E_PUBLICATION" if candidate else "E_IO"
        span = context.span(context.headers["output"] if candidate else context.header_range) if context else None
        _failure(result, Failure(code, str(exc), span), contract)
    finally:
        if lock is not None:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()
    result["cost"] = budget.cost()
    schema_check(result, contract["output_schema"])
    if attempt_dir is not None:
        if stage is not None and stage.exists():
            try:
                os.rename(stage, attempt_dir / "failed-stage")
            except OSError:
                pass
        if not committed and candidate is not None:
            write_receipt(attempt_dir / "unreferenced-candidate.json",
                          {"directory": str(candidate), "accepted": False}, committed)
        write_receipt(attempt_dir / "result.json", result, committed)
    if result_path:
        message = write_receipt(result_path, result, committed)
        if message is not None and attempt_dir is not None:
            write_receipt(attempt_dir / "optional-result-error.json",
                          {"message": message, "committed": committed}, committed)
    return result
