#!/usr/bin/env python3
"""Freeze, execute once, and audit the bounded C196 accepted-store transition."""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
C195 = HERE.parent / "ownership-recovery-c195"
PREP = HERE.parent / "contact-preparation-c194"
H = "2143515f358e36c1dd9a1deef83dba2519a99be6141b64d8bd9dae987761fbd0"
G = "ba105a8ca6e9c19dfd06fabd7a06a2254c4ba14d76042dfa88ca365d5de6f7ee"
KEYS = ("canonical-input.json", "native-transforms.json", "raw.glb", "final.glb")
BLENDER_SHA = "5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397"


def now():
    return datetime.now(timezone.utc).isoformat()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(path, value, exclusive=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def identity(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "Expected ordinary file: " + str(path))
    return {"sha256": digest(path), "bytes": path.stat().st_size,
            "mode": format(stat.S_IMODE(path.stat().st_mode), "04o")}


def inventory(root):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        require(not path.is_symlink(), "Symlink in retained evidence: " + str(path))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = identity(path)
    return result


def directories(root):
    return sorted(p.relative_to(root).as_posix() for p in Path(root).rglob("*") if p.is_dir())


def child(root, value):
    path = Path(value)
    require(not path.is_absolute() and ".." not in path.parts and str(path) == value,
            "Unsafe relative path: " + str(value))
    target = (root / path).resolve()
    require(target.is_relative_to(root.resolve()), "Path escapes root")
    return target


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def modules():
    sys.path.insert(0, str(PREP))
    common = load("common", PREP / "common.py")
    setup = load("c196_inherited_preparation", PREP / "run_preparation.py")
    verifier = load("c196_inherited_c195", C195 / "verify_deliveries.py")
    return common, setup, verifier


def preserved(before, after, exceptions=()):
    for name, expected in before.items():
        if name not in exceptions:
            require(after.get(name) == expected, "Preexisting file changed: " + name)
    return sorted(set(after) - set(before))


def state_artifact(store, revision):
    state = read(store / "state.json")
    require(state["schema"] == "ontokin.c193.store/0.1" and state["accepted_revision"] == revision,
            "Wrong accepted store revision or namespace")
    artifact = child(store, state["artifact_directory"])
    manifest = read(artifact / "manifest.json")
    require(digest(artifact / "source.ok") == revision == manifest["source_sha256"],
            "Accepted source and manifest do not identify the revision")
    require(digest(artifact / "canonical-input.json") == state["canonical_input_sha256"] ==
            manifest["canonical_input_sha256"], "Accepted canonical input hash differs")
    require(digest(artifact / "manifest.json") == state["manifest_sha256"], "Accepted manifest hash differs")
    for name, expected in manifest["files"].items():
        path = child(artifact, name)
        require(digest(path) == expected["sha256"] and path.stat().st_size == expected["bytes"],
                "Manifest file differs: " + name)
    require(set(inventory(artifact)) == set(manifest["files"]) | {"manifest.json"},
            "Artifact closure has an undeclared or missing file")
    return state, artifact


def zero_native(result):
    cost = result["cost"]
    require(cost["operation_components"].get("scheduled_native_substeps", 0) == 0,
            "Rejected input scheduled native work")
    for key in ("native_elapsed_ms", "native_result_bytes", "native_log_bytes", "staged_output_bytes"):
        require(cost[key] == 0, "Rejected input produced native cost: " + key)
    require(result["artifact_directory"] is None and not result["artifacts"], "Rejected input produced artifacts")


def verify_inputs():
    manifest = read(HERE / "INPUTS.json")
    for row in manifest["files"]:
        require(identity(child(REPO, row["path"])) == {k: row[k] for k in ("sha256", "bytes", "mode")},
                "Frozen repository input changed: " + row["path"])
    return manifest


def receiving_map(prior, artifact):
    """Bind new G bytes to exact inherited receiving, dependency and visual receipts."""
    receiver = prior / "c195-validation/receiving"
    mapping = read(C195 / "evidence/REPLAY-MAP.json")
    g_row = next(x for x in mapping["rows"] if x["id"] == "ok-repaired")
    old = child(prior, g_row["artifact"])
    require(all(digest(artifact / name) == digest(old / name) for name in KEYS),
            "New delivery differs from accepted C195 G")
    dependencies = read(receiver / "dependencies.json")
    archive = REPO / "docs/engineering/guided-contact-c191/qualification-evidence.tar.xz"
    require(digest(archive) == dependencies["sha256"], "Receiver dependency archive changed")
    with tarfile.open(archive) as source_archive:
        for row in dependencies["files"]:
            if row.get("unchanged_source"):
                data = child(REPO, row["unchanged_source"]).read_bytes()
                require((receiver / row["path"]).read_bytes() == data, "Retained receiver script differs")
            else:
                entry = source_archive.getmember("evidence/r2/coordinator/receiving/" + row["path"])
                require(entry.isfile() and not entry.issparse(), "Nonregular dependency")
                data = source_archive.extractfile(entry).read()
            require(len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"],
                    "Receiver dependency/checker differs: " + row["path"])
    summary = read(receiver / "summary.json")
    require(summary["pass_for_executed_receiving_checks"] and summary["khronos_errors"] ==
            summary["khronos_warnings"] == 0, "Inherited receiver summary failed")
    identities, khronos, three = (read(receiver / n) for n in ("artifact-identities.json", "khronos.json", "three.json"))
    require(three["pass"] and three["threeRevision"] == "186", "Inherited Three.js binding failed")
    outputs = []
    for name in ("raw.glb", "final.glb"):
        label = "deliveries/ok-repaired/" + name
        sha = digest(artifact / name)
        entry = next(x for x in identities if x["path"] == label)
        require(entry["sha256"] == sha == digest(receiver / label), "Receiver artifact identity differs")
        report = khronos[label]
        require(report["sha256"] == sha and report["report"]["issues"]["numErrors"] ==
                report["report"]["issues"]["numWarnings"] == 0, "Inherited Khronos receipt differs")
        report = next(x for x in three["reports"] if x["path"] == label)
        require(report["sha256"] == sha and len(report["poses"]) == 3, "Inherited Three.js receipt differs")
        outputs.append({"new_file": name, "sha256": sha, "inherited_receiver_label": label,
                        "khronos_receipt": "c195-validation/receiving/khronos.json",
                        "three_receipt": "c195-validation/receiving/three.json"})
    imported_path = receiver / "renders/ok-repaired/receipt.json"
    imported = read(imported_path)
    require(imported["label"] == "ok-repaired" and imported["input_sha256"] == digest(artifact / "final.glb")
            and imported["all_sampled_imports_match_glb"] and imported["mesh_count"] == 7 and
            len(imported["frames"]) == 3, "Inherited Blender import receipt differs")
    visual_path = prior / "c195-validation/VISUAL-REVIEW.json"
    visual = read(visual_path)
    require(visual["pass"], "Inherited visual review failed")
    panels = []
    for frame in imported["frames"]:
        path = imported_path.parent / frame["png"]
        rel = path.relative_to(receiver).as_posix()
        declared = next(p for p in visual["panels"] if p["path"] == rel)
        require(digest(path) == frame["png_sha256"] == declared["sha256"] and
                path.stat().st_size == frame["png_bytes"] == declared["bytes"], "Inherited image identity differs")
        panels.append({"path": path.relative_to(prior).as_posix(), **identity(path)})
    accepted_path = prior / "c195-validation/ACCEPTANCE.json"
    accepted = read(accepted_path)
    require(accepted["accepted"] and accepted["visual_review_sha256"] == digest(visual_path) and
            accepted["results_sha256"] == digest(prior / "c195-validation/RESULTS.json"),
            "C195 acceptance does not bind receiving and visual evidence")
    result = read(prior / "c195-validation/RESULTS.json")
    require(result["receiving"]["passed"] and result["receiving"]["summary_sha256"] == digest(receiver / "summary.json"),
            "C195 validation does not bind receiver summary")
    for kind in ("khronos", "three", "blender"):
        receipt = read(receiver / "commands" / (kind + ".json"))
        require(receipt["completed"] and receipt["returncode"] == 0 and receipt["pass"],
                "Inherited receiving process did not pass")
    names = ["summary.json", "dependencies.json", "artifact-identities.json", "khronos.json", "three.json",
             "renders/ok-repaired/receipt.json", "commands/khronos.json", "commands/three.json", "commands/blender.json"]
    receipts = [{"path": (receiver / n).relative_to(prior).as_posix(), **identity(receiver / n)} for n in names]
    receipts.extend({"path": p.relative_to(prior).as_posix(), **identity(p)} for p in (visual_path, accepted_path))
    return {"passed": True, "meaning": "Inherited exact-artifact receiving evidence; no new receiving or visual execution",
            "outputs": outputs, "receipts": receipts, "panels": panels,
            "dependency_archive_sha256": digest(archive), "source_binding": "c193-experimental-0.1",
            "backend_binding": "blender-bullet-c193-0.1", "physical_profile": "guided-box-contact-0.1",
            "destination_binding": "glb-guided-contact-0.1", "new_receiving_executions": 0}


def prepare(args):
    work = args.work.resolve()
    replay = args.prior_replay.resolve()
    prior = replay / "evidence"
    require(read(replay / "REPLAY-RESULT.json")["passed"], "C195 recorded replay did not pass")
    require(read(replay / "REPLAY-RESULT.json")["new_native_builds"] == 0, "Expected recorded-only replay")
    descriptor = read(C195 / "evidence/RECORDED-EVIDENCE.json")
    archive = C195 / "evidence/recorded-evidence.tar.xz"
    require(digest(archive) == descriptor["sha256"], "C195 archive differs")
    # The portable predecessor replay checks bytes but does not restore tar modes.
    # Restore those declared original modes before defining the copied-store snapshot.
    with tarfile.open(archive) as source_archive:
        mode_rows = {}
        for member in source_archive:
            require(member.isfile() and not member.issparse(), "C195 archive contains a nonregular file")
            path = child(prior, member.name)
            mode_rows[member.name] = format(member.mode & 0o7777, "04o")
            os.chmod(path, member.mode & 0o7777)
    expected = {r["path"]: {"sha256": r["sha256"], "bytes": r["bytes"], "mode": mode_rows[r["path"]]}
                for r in descriptor["files"]}
    require(inventory(prior) == expected, "C195 restored evidence inventory differs")
    common, _, verifier = modules()
    common.verify_freeze()
    verifier.public_inputs(REPO)
    common.artifact_reader().verify_frozen()
    require(digest(args.blender) == BLENDER_SHA and os.access(args.blender, os.X_OK), "Unqualified Blender")
    require(platform.system() == "Linux" and platform.machine() == "x86_64", "Linux x86-64 required")
    transition = work / "transition"
    transition.mkdir(parents=True, exist_ok=False)
    original_run = prior / "c195-runs/ok/accepted-run"
    copied_run = transition / "accepted-run"
    shutil.copytree(original_run, copied_run, copy_function=shutil.copy2)
    require(inventory(original_run) == inventory(copied_run), "Copied accepted run differs")
    store = copied_run / "store"
    state, artifact = state_artifact(store, H)
    inputs = work / "inputs"
    inputs.mkdir(exist_ok=False)
    for name, path, sha in (("H.ok", C195 / "authors/ok/accepted-source.ok", H),
                            ("G.ok", C195 / "authors/ok/repaired.ok", G)):
        require(digest(path) == sha, "Accepted input source identity differs")
        shutil.copy2(path, inputs / name)
    require((artifact / "source.ok").read_bytes() == (inputs / "H.ok").read_bytes(), "H store source differs")
    require((inputs / "H.ok").read_bytes().splitlines()[0] == b'ontokin "c193-experimental-0.1";',
            "H first declaration differs from the independently expected stale span")
    stale_span = {"path": "H.ok", "source_sha256": H, "start_byte": 0, "end_byte": 32,
                  "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 33}
    for name in ("C194-ACCEPTANCE.json", "accepted-source.ok"):
        shutil.copy2(prior / "c195-runs/ok" / name, inputs / name)
    shutil.copy2(store / "state.json", inputs / "H-state.json")
    receipts = list((store / "attempts").glob("*/result.json"))
    negatives = [read(p) for p in receipts if not read(p)["successful"]]
    require(len(negatives) == 1, "Expected exactly one retained ownership rejection")
    negative = negatives[0]
    zero_native(negative)
    require(not negative["committed"] and negative["accepted_revision"] == negative["previous_revision"] == H and
            negative["diagnostics"][0]["code"] == "C193_E_OWNERSHIP", "Retained rejection is not the C195 ownership case")
    base_map = read(C195 / "evidence/REPLAY-MAP.json")
    g_row = next(r for r in base_map["rows"] if r["id"] == "ok-repaired")
    reuse = receiving_map(prior, child(prior, g_row["artifact"]))
    write(work / "inherited-receiving-preflight.json", reuse)
    snapshot = {"accepted_run": inventory(copied_run), "store": inventory(store),
                "directories": directories(store), "state": state, "state_identity": identity(store / "state.json"),
                "original_artifact": state["artifact_directory"], "retained_negative_attempt": negative["attempt_id"],
                "prior_evidence_inventory": expected, "input_files": inventory(inputs),
                "stale_expected_span": stale_span}
    write(HERE / "INITIAL-SNAPSHOT.json", snapshot)
    plan = {"schema": "ontokin.c196.execution-plan/0.1", "owner": "c196-accepted-revision-b3a9f7",
            "work": str(work), "prior_replay": str(replay), "automatic_retries": False,
            "native_constructions": ["promotion", "regeneration"],
            "negative_transactions": ["stale-H"], "saved_scene_replays": ["promotion", "regeneration"],
            "construction_limits": {"operations": 1000000, "elapsed_ms": 80000, "outer_seconds": 100},
            "scene_replay_outer_seconds": 80, "stop_on_first_failed_gate": True,
            "new_authors": 0, "new_receiving_executions": 0}
    write(HERE / "EXECUTION-PLAN.json", plan)
    paths = {r["path"] for r in read(C195 / "INPUTS.json")["files"]}
    paths.update(p.relative_to(REPO).as_posix() for p in C195.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for directory in (REPO / "prototypes/guided_contact_v02", common.CONTRACT):
        paths.update(p.relative_to(REPO).as_posix() for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    paths.update((HERE / name).relative_to(REPO).as_posix() for name in
                 ("run_transition.py", "PROTOCOL.md", "EXECUTION-PLAN.json", "INITIAL-SNAPSHOT.json"))
    paths.add("docs/engineering/guided-contact-c191/qualification-evidence.tar.xz")
    for row in read(prior / "c195-validation/receiving/dependencies.json")["files"]:
        if row.get("unchanged_source"):
            paths.add(row["unchanged_source"])
    manifest = {"schema": "ontokin.c196.frozen-inputs/0.1", "prepared_utc": now(), "source_revisions": {"H": H, "G": G},
                "base_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
                "base_git_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=REPO, text=True).strip(),
                "blender": {"path": str(args.blender.resolve()), **identity(args.blender)},
                "prior_archive": descriptor["sha256"], "prior_replay_sha256": digest(replay / "REPLAY-RESULT.json"),
                "files": [{"path": name, **identity(child(REPO, name))} for name in sorted(paths)]}
    write(HERE / "INPUTS.json", manifest)
    preparation = {"schema": "ontokin.c196.preparation/0.1", "passed": True, "prepared_utc": now(),
                   "input_manifest_sha256": digest(HERE / "INPUTS.json"), "protocol_sha256": digest(HERE / "PROTOCOL.md"),
                   "runner_sha256": digest(Path(__file__)), "initial_snapshot_sha256": digest(HERE / "INITIAL-SNAPSHOT.json"),
                   "execution_plan_sha256": digest(HERE / "EXECUTION-PLAN.json"),
                   "prior_recorded_checks": read(replay / "REPLAY-RESULT.json")["checks_passed"],
                   "prior_files": len(expected), "original_modes_restored": True, "copied_store_files": len(snapshot["store"]),
                   "native_constructions": 0, "native_replays": 0, "receiving_executions": 0,
                   "status": "Prepared; independent review and C195 integration reconciliation required before native execution"}
    write(HERE / "PREPARATION.json", preparation)
    print(json.dumps(preparation), flush=True)


def event(stream, kind, **values):
    stream.write(json.dumps({"utc": now(), "event": kind, **values}, sort_keys=True, allow_nan=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def enable_subreaper():
    """Adopt this runner's orphaned descendants, including new-session workers."""
    libc = ctypes.CDLL(None, use_errno=True)
    require(libc.prctl(36, 1, 0, 0, 0) == 0, "Cannot enable bounded descendant supervision")


def process_rows():
    rows = {}
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
            rows[int(path.name)] = {"pid": int(path.name), "ppid": int(fields[1]),
                                    "state": fields[0], "start_ticks": fields[19]}
        except (OSError, ValueError, IndexError):
            continue
    return rows


def owned_descendants():
    rows = process_rows()
    owned = {os.getpid()}
    while True:
        expanded = owned | {pid for pid, row in rows.items() if row["ppid"] in owned}
        if expanded == owned:
            break
        owned = expanded
    return [rows[pid] for pid in sorted(owned - {os.getpid()}) if pid in rows]


def cleanup_descendants(process):
    """Bounded cleanup of this runner's descendants, across process groups."""
    original = owned_descendants()
    record = {"runner_pid": os.getpid(), "direct_pid": process.pid if process else None,
              "subreaper": True, "initial_descendants": original, "signals": [], "reaped": [],
              "cleanup_allowance_seconds": 5, "started_utc": now()}
    for sig, seconds in ((signal.SIGTERM, 2), (signal.SIGKILL, 3)):
        deadline = time.monotonic() + seconds
        signalled = set()
        while True:
            if process is not None:
                process.poll()
            rows = owned_descendants()
            for row in rows:
                token = (row["pid"], row["start_ticks"])
                if token not in signalled and row["state"] != "Z":
                    # Recheck the start time before signalling to exclude PID reuse.
                    current = process_rows().get(row["pid"])
                    if current and current["start_ticks"] == row["start_ticks"]:
                        try:
                            os.kill(row["pid"], sig)
                            record["signals"].append({"pid": row["pid"], "start_ticks": row["start_ticks"], "signal": sig.name})
                        except ProcessLookupError:
                            pass
                    signalled.add(token)
                if process is None or row["pid"] != process.pid:
                    try:
                        pid, status = os.waitpid(row["pid"], os.WNOHANG)
                        if pid:
                            record["reaped"].append({"pid": pid, "wait_status": status})
                    except ChildProcessError:
                        pass
            if not owned_descendants() or time.monotonic() >= deadline:
                break
            time.sleep(0.025)
        if not owned_descendants():
            break
    if process is not None:
        process.poll()
    record["remaining_descendants"] = owned_descendants()
    record["passed"] = not record["remaining_descendants"]
    record["finished_utc"] = now()
    return record


def transaction(label, source, store, expected, blender, out, ledger):
    args = [sys.executable, "-B", "-m", "prototypes.guided_contact_v02", "run", str(source),
            "--store", str(store), "--blender", str(blender), "--host-max-operations", "1000000",
            "--host-max-elapsed-ms", "80000"]
    if expected is not None:
        args += ["--expected-revision", expected]
    directory = out / "commands"
    directory.mkdir(exist_ok=True)
    receipt_path = directory / (label + ".json")
    record = {"argv": args, "cwd": str(REPO), "started_utc": now(), "outer_seconds": 100,
              "source_sha256": digest(source), "expected_revision": expected, "completed": False}
    write(receipt_path, record)
    event(ledger, "transaction_reserved", id=label, native_construction=label != "stale-H", command=record)
    started = time.monotonic()
    process, interrupted = None, None
    with (directory / (label + ".stdout.txt")).open("xb") as stdout, \
            (directory / (label + ".stderr.txt")).open("xb") as stderr:
        try:
            process = subprocess.Popen(args, cwd=REPO, stdout=stdout, stderr=stderr, start_new_session=True)
            record["pid"] = process.pid
            write(receipt_path, record, exclusive=False)
            record["returncode"] = process.wait(timeout=100)
            record["completed"] = True
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
        except BaseException as error:
            interrupted = error
            record["interruption"] = type(error).__name__ + ": " + str(error)
        finally:
            record["cleanup"] = cleanup_descendants(process)
            if process is not None:
                record["returncode"] = process.returncode
    record.update(elapsed_seconds=time.monotonic() - started, finished_utc=now())
    write(receipt_path, record, exclusive=False)
    event(ledger, "transaction_finished", id=label, receipt_sha256=digest(receipt_path), **record)
    require(record["cleanup"]["passed"], "Owned transaction descendants remain after bounded cleanup")
    if interrupted is not None:
        raise interrupted
    require(record["completed"], label + " exceeded its outer watchdog")
    result = read(directory / (label + ".stdout.txt"))
    require(record["returncode"] == (0 if result["successful"] else 1), "Unexpected transaction exit status")
    write(out / (label + "-result.json"), result)
    return result


def positive(result, previous):
    require(result["successful"] and result["committed"] and result["previous_revision"] == previous and
            result["accepted_revision"] == result["source_sha256"] == G, "Positive transaction did not commit G")
    require(not result["diagnostics"], "Positive transaction returned diagnostics")
    cost = result["cost"]
    require(cost["requested_operations"] == cost["host_operations_ceiling"] == 1000000 and
            cost["requested_elapsed_ms"] == cost["host_elapsed_ms_ceiling"] == 80000 and
            cost["operations_consumed"] <= 1000000 and cost["elapsed_ms"] <= 80000,
            "Positive construction budget differs or exceeded")
    require(cost["operation_components"]["scheduled_native_substeps"] == 4800, "Construction native work differs")


def artifact_checks(artifact, reference, common, verifier, out, identifier):
    provenance = verifier.provenance(artifact, "ok", artifact / "source.ok", "G")
    require(provenance["passed"], "Independent provenance audit failed")
    reader = common.artifact_reader()
    reader.verify_frozen()
    numeric = reader.review(artifact, "G", common.CONTRACT / "backend.json", common.BACKEND_SHA, common.SOURCE_BINDING)
    require(numeric["passed"] and not numeric["failures"], "Independent numerical gate failed")
    require(all(digest(artifact / name) == digest(reference / name) for name in KEYS), "C195 G output equality failed")
    trace, baseline = read(artifact / "native-transforms.json"), read(reference / "native-transforms.json")
    require(len(trace) == len(baseline) == 481 and trace == baseline, "Native sample equality failed")
    for part in ("base", "right_carriage", "right_shoe", "right_stop"):
        require(all(a["matrices_blender_m"][part] == b["matrices_blender_m"][part] and
                    a["bounds_gltf_mm"][part] == b["bounds_gltf_mm"][part] for a, b in zip(trace, baseline)),
                "Unrelated native part changed: " + part)
    write(out / "reports" / (identifier + "-provenance.json"), provenance)
    write(out / "reports" / (identifier + "-numerical.json"), numeric)
    return {"passed": True, "artifact_files": {name: digest(artifact / name) for name in KEYS},
            "scene_sha256": digest(artifact / "scene.blend"), "samples": 481,
            "mapping_bound_mm": numeric["mapping_measurements"]["maximumContinuousRawToFinalVertexDeviationBoundMm"]}


def execute(args):
    manifest = verify_inputs()
    preparation = read(HERE / "PREPARATION.json")
    review = read(args.review)
    require(review.get("approved_for_execution") is True and review.get("passed") is True,
            "Independent reviewer has not approved execution")
    bindings = {"input_manifest_sha256": "INPUTS.json", "preparation_sha256": "PREPARATION.json",
                "initial_snapshot_sha256": "INITIAL-SNAPSHOT.json", "protocol_sha256": "PROTOCOL.md",
                "runner_sha256": "run_transition.py", "execution_plan_sha256": "EXECUTION-PLAN.json"}
    for key, name in bindings.items():
        require(review.get(key) == digest(HERE / name), "Independent review does not bind " + name)
    integration = read(args.integration)
    require(review.get("c195_integration_receipt_sha256") == digest(args.integration),
            "C195 integration receipt differs from the independently reviewed observation")
    require(integration.get("number") == 128 and integration.get("merged") is True and
            re.fullmatch(r"[0-9a-f]{40}", integration.get("merge_commit_sha", "")), "C195 integration is not observed")
    plan = read(HERE / "EXECUTION-PLAN.json")
    work, prior = Path(plan["work"]), Path(plan["prior_replay"]) / "evidence"
    require(work.resolve() == args.work.resolve(), "Execution output differs from exclusive plan")
    require(identity(args.blender) == {k: manifest["blender"][k] for k in ("sha256", "bytes", "mode")}, "Blender differs")
    snapshot = read(HERE / "INITIAL-SNAPSHOT.json")
    require(inventory(prior) == snapshot["prior_evidence_inventory"], "Predecessor evidence changed")
    run, store = work / "transition/accepted-run", work / "transition/accepted-run/store"
    require(inventory(run) == snapshot["accepted_run"] and inventory(work / "inputs") == snapshot["input_files"],
            "Prepared state/source changed before execution")
    common, setup, verifier = modules()
    common.verify_freeze()
    verifier.public_inputs(REPO)
    out = work / "execution"
    require(not out.exists(), "Execution evidence already exists")
    enable_subreaper()
    def stop_execution(signum, _frame):
        raise InterruptedError("Execution interrupted by " + signal.Signals(signum).name)
    signal.signal(signal.SIGTERM, stop_execution)
    signal.signal(signal.SIGINT, stop_execution)
    ledger_path = HERE / "EXECUTION.jsonl"
    with ledger_path.open("x") as ledger:
        out.mkdir()
        record = {"schema": "ontokin.c196.transition-result/0.1", "passed": False, "started_utc": now(),
                  "input_manifest_sha256": digest(HERE / "INPUTS.json"), "preparation_sha256": digest(HERE / "PREPARATION.json"),
                  "independent_review_sha256": digest(args.review), "c195_integration_sha256": digest(args.integration),
                  "python": sys.version, "platform": platform.platform(), "blender_sha256": digest(args.blender),
                  "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
                  "native_constructions_started": 0, "native_replays_started": 0, "new_receiving_executions": 0,
                  "new_authors": 0, "automatic_retries": 0, "runs": [], "inherited_legacy_regression": "FAILED; 4239 distinct passes; 13 NOT RUN"}
        event(ledger, "execution_reserved", plan_sha256=digest(HERE / "EXECUTION-PLAN.json"), review_sha256=digest(args.review))
        shutil.copy2(args.review, out / "PREEXECUTION-REVIEW.json")
        shutil.copy2(args.integration, out / "C195-INTEGRATION.json")
        try:
            reference_row = next(x for x in read(C195 / "evidence/REPLAY-MAP.json")["rows"] if x["id"] == "ok-repaired")
            reference = child(prior, reference_row["artifact"])
            before = inventory(run)
            record["native_constructions_started"] += 1
            promotion = transaction("promotion", work / "inputs/G.ok", store, H, args.blender, out, ledger)
            positive(promotion, H)
            state, promoted = state_artifact(store, G)
            require(state["artifact_directory"] != snapshot["original_artifact"], "Promotion reused old H directory")
            after = inventory(run)
            added = preserved(before, after, {"store/state.json"})
            require((work / "inputs/H-state.json").read_bytes() != (store / "state.json").read_bytes(), "State did not advance")
            write(out / "PROMOTION-INVENTORY.json", {"before": before, "after": after, "added": added,
                  "added_directories": sorted(set(directories(store)) - set(snapshot["directories"])), "state": state})
            p_checks = artifact_checks(promoted, reference, common, verifier, out, "promotion")
            p_reuse = receiving_map(prior, promoted)
            record["runs"].append({"id": "promotion", "artifact": promoted.relative_to(work).as_posix(), **p_checks})
            write(out / "promotion-receiving-reuse.json", p_reuse)
            before_stale, dirs_stale = inventory(store), directories(store)
            stale = transaction("stale-H", work / "inputs/H.ok", store, H, args.blender, out, ledger)
            zero_native(stale)
            require(not stale["successful"] and not stale["committed"] and
                    stale["previous_revision"] == stale["accepted_revision"] == G, "Stale call changed accepted revision")
            from prototypes.guided_contact_v02.common import Budget, load_contract
            from prototypes.guided_contact_v02.source import Source
            context = Source(work / "inputs/H.ok", (work / "inputs/H.ok").read_bytes(), Budget(1000000, 80000, None), load_contract())
            context.parse()
            context.validate()
            require(len(stale["diagnostics"]) == 1 and stale["diagnostics"][0]["code"] == "C193_E_STALE_REVISION" and
                    stale["diagnostics"][0]["phase"] == "publish" and stale["diagnostics"][0]["span"] ==
                    context.span(context.header_range) == snapshot["stale_expected_span"],
                    "Stale diagnostic code, phase or actual source span differs")
            after_stale = inventory(store)
            added = preserved(before_stale, after_stale)
            expected_receipt = "attempts/" + stale["attempt_id"] + "/result.json"
            require(added == [expected_receipt], "Stale call added native or undeclared output")
            require(set(directories(store)) - set(dirs_stale) == {"attempts/" + stale["attempt_id"]}, "Stale call added staging/artifact directories")
            require(read(store / expected_receipt) == stale, "Stale separate receipt differs")
            write(out / "STALE-INVENTORY.json", {"before": before_stale, "after": after_stale, "added": added})
            record["stale_rejection"] = {"passed": True, "diagnostic": stale["diagnostics"][0], "cost": stale["cost"]}
            before_readback = inventory(store)
            read_state, read_artifact = state_artifact(store, G)
            read_source = read_artifact / "source.ok"
            data = read_source.read_bytes()
            require(hashlib.sha256(data).hexdigest() == G, "Authoritative readback source differs")
            readback = work / "readback"
            readback.mkdir(exist_ok=False)
            (readback / "accepted.ok").write_bytes(data)
            write(out / "READBACK.json", {"state_sha256": digest(store / "state.json"), "state": read_state,
                  "resolved_source": read_source.relative_to(work).as_posix(), "readback_source": "readback/accepted.ok",
                  "source_sha256": digest(readback / "accepted.ok"), "selected_from_state_pointer": True})
            fresh_store = work / "regenerated/store"
            require(not fresh_store.exists(), "Regeneration store must be fresh")
            record["native_constructions_started"] += 1
            regenerated = transaction("regeneration", readback / "accepted.ok", fresh_store, None, args.blender, out, ledger)
            positive(regenerated, None)
            _, regenerated_artifact = state_artifact(fresh_store, G)
            require(inventory(store) == before_readback, "Readback/regeneration changed promoted store")
            write(out / "READBACK-PRESERVATION.json", {"before": before_readback, "after": inventory(store)})
            r_checks = artifact_checks(regenerated_artifact, reference, common, verifier, out, "regeneration")
            require(all(digest(promoted / name) == digest(regenerated_artifact / name) for name in KEYS), "Two new outputs differ")
            write(out / "regeneration-receiving-reuse.json", receiving_map(prior, regenerated_artifact))
            record["runs"].append({"id": "regeneration", "artifact": regenerated_artifact.relative_to(work).as_posix(), **r_checks})
            for identifier, artifact in (("promotion", promoted), ("regeneration", regenerated_artifact)):
                before_replay = inventory(artifact)
                event(ledger, "saved_scene_replay_reserved", id=identifier, scene_sha256=digest(artifact / "scene.blend"))
                record["native_replays_started"] += 1
                receipt = setup.reopen(artifact, identifier, "ok", "G", args.blender, out)
                require(inventory(artifact) == before_replay, "Independent scene replay changed delivered artifact")
                event(ledger, "saved_scene_replay_finished", id=identifier, receipt=receipt)
                next(r for r in record["runs"] if r["id"] == identifier)["saved_scene_replay"] = receipt
            require(inventory(prior) == snapshot["prior_evidence_inventory"], "Original C195 evidence changed")
            require(inventory(work / "inputs") == snapshot["input_files"], "Copied original source/state/acceptance bytes changed")
            preserved(snapshot["accepted_run"], inventory(run), {"store/state.json"})
            verify_inputs()
            record["passed"] = True
            record["interpretation"] = "Observed accepted H-to-G promotion, actual stale-H rejection and accepted-source readback regeneration"
        except Exception as error:
            record["failure"] = type(error).__name__ + ": " + str(error)
            event(ledger, "stopped_on_failed_gate", failure=record["failure"])
        write(out / "FINAL-INVENTORY.json", {"accepted_run": inventory(run),
              "fresh_store": inventory(work / "regenerated/store") if (work / "regenerated/store").exists() else {},
              "source_inputs": inventory(work / "inputs")})
        record["finished_utc"] = now()
        write(out / "RESULTS.json", record)
        event(ledger, "execution_finished", passed=record["passed"], result_sha256=digest(out / "RESULTS.json"))
    shutil.copy2(ledger_path, out / "EXECUTION.jsonl")
    print(json.dumps({"passed": record["passed"], "failure": record.get("failure"), "results": str(out / "RESULTS.json")}), flush=True)
    return 0 if record["passed"] else 1


def audit(args):
    """Fresh recorded-only checks; never call a constructor or saved-scene process."""
    verify_inputs()
    work, out = args.work.resolve(), args.out.resolve()
    require(not out.exists(), "Audit output must be new")
    out.mkdir(parents=True)
    result = read(work / "execution/RESULTS.json")
    require(result["passed"] and result["native_constructions_started"] == 2 and result["native_replays_started"] == 2,
            "Original bounded execution did not pass")
    snapshot = read(HERE / "INITIAL-SNAPSHOT.json")
    prior = work / "prior-replay/evidence"
    require(inventory(prior) == snapshot["prior_evidence_inventory"], "Original C195 evidence differs")
    common, _, verifier = modules()
    reference_row = next(x for x in read(C195 / "evidence/REPLAY-MAP.json")["rows"] if x["id"] == "ok-repaired")
    reference = child(prior, reference_row["artifact"])
    checks = []
    for row in result["runs"]:
        artifact = child(work, row["artifact"])
        checked = artifact_checks(artifact, reference, common, verifier, out, row["id"])
        receiving_map(prior, artifact)
        reopen = work / "execution/reopens" / row["id"]
        summary = read(reopen / "summary.json")
        require(summary["pass"] and summary["configuration_unchanged"] and summary["cache_clear_completed"] and
                not summary["reconstructed_or_repaired"] and summary["opened_scene_sha256"] == digest(artifact / "scene.blend"),
                "Retained saved-scene receipt differs")
        require(read(artifact / "native-transforms.json") == read(reopen / "native-transforms.json") and
                len(read(reopen / "native-transforms.json")) == 481, "Retained replay samples differ")
        checks.append({"id": row["id"], **checked})
    promotion = read(work / "execution/PROMOTION-INVENTORY.json")
    preserved(promotion["before"], promotion["after"], {"store/state.json"})
    stale = read(work / "execution/STALE-INVENTORY.json")
    preserved(stale["before"], stale["after"])
    zero_native(read(work / "execution/stale-H-result.json"))
    store = work / "transition/accepted-run/store"
    require(inventory(store) == stale["after"], "Accepted store changed after stale refusal")
    state_artifact(store, G)
    readback = read(work / "execution/READBACK.json")
    require(digest(child(work, readback["resolved_source"])) == digest(work / "readback/accepted.ok") == G,
            "Accepted source readback differs")
    require(read(work / "execution/READBACK-PRESERVATION.json")["before"] ==
            read(work / "execution/READBACK-PRESERVATION.json")["after"] == inventory(store), "Readback store preservation differs")
    ledger = [json.loads(line) for line in (work / "execution/EXECUTION.jsonl").read_text().splitlines()]
    require([r["id"] for r in ledger if r["event"] == "transaction_reserved"] == ["promotion", "stale-H", "regeneration"],
            "Transaction attempt accounting differs")
    require([r["id"] for r in ledger if r["event"] == "saved_scene_replay_reserved"] == ["promotion", "regeneration"],
            "Replay attempt accounting differs")
    report = {"schema": "ontokin.c196.recorded-audit/0.1", "passed": True, "runs": checks,
              "prior_files": len(snapshot["prior_evidence_inventory"]), "new_native_constructions": 0,
              "new_scene_replays": 0, "new_receiving_executions": 0, "finished_utc": now(),
              "original_result_sha256": digest(work / "execution/RESULTS.json")}
    write(out / "AUDIT.json", report)
    print(json.dumps(report), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="operation", required=True)
    p = subs.add_parser("prepare")
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--prior-replay", type=Path, required=True)
    p.add_argument("--blender", type=Path, required=True)
    p = subs.add_parser("execute")
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--blender", type=Path, required=True)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--integration", type=Path, required=True)
    p = subs.add_parser("audit")
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    return {"prepare": prepare, "execute": execute, "audit": audit}[args.operation](args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
