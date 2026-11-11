"""Exact executable inputs and independent pre-native approval for C199."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys

from .canonical import ROOT, json_bytes, strict_json
from .errors import CONTRACT, PROFILE
from .supervisor import LIMITS, Stop, sha256_file

SCHEMA = "ontokin.static-tray.input-lock/0.1.0"
APPROVAL_SCHEMA = "ontokin.static-tray.input-approval/0.1.0"
READER_NAMES = {"audit.py", "reader.py", "glb.py", "expected.py", "corrupt.py"}
NATIVE_FLAGS = ["-b", "--factory-startup", "--disable-autoexec", "--threads", "2", "--python-exit-code", "1", "--python-use-system-env"]
BLENDER_SHA = "5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397"
ARCHIVE_SHA = "975c58fcb244273838534bba771e64ad87739216b0f9b39a888531a49a72d845"
ALL_LIMITS = {**LIMITS, "source_operations": 100000, "source_elapsed_ms": 30000}
HOST_ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
                    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PYTHONHASHSEED": "0",
                    "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2"}


def reject_repository_bytecode(root):
    parent = Path(root) / "prototypes"
    cached_parent = [parent / "__init__.pyc", parent / "__init__.pyo", *(parent / "__pycache__").glob("__init__.*")]
    if any(p.is_file() and p.suffix in {".pyc", ".pyo"} for p in cached_parent):
        raise Stop("OTRAY-E-BINDING", "Parent prototypes initializer bytecode is outside the source-only lock")
    for relative in ("ontokin", "prototypes/static_tray_v01", "tools/static_tray_reader_v01"):
        for path in (Path(root) / relative).rglob("*"):
            if path.suffix in {".pyc", ".pyo"}:
                raise Stop("OTRAY-E-BINDING", "Repository bytecode cache is outside the source-only lock: " + str(path))


def read_json(path, limit=4 * 1024 * 1024):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise Stop("OTRAY-E-BINDING", "Unsafe or over-limit JSON input: " + str(path))
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    return strict_json(data, limit=limit)


def file_binding(path):
    path = Path(path)
    return {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def check_file(path, binding, check=lambda: None):
    path = Path(path)
    check()
    if path.is_symlink() or not path.is_file() or path.stat().st_size != binding["size_bytes"]:
        raise Stop("OTRAY-E-BINDING", "Locked file kind or size differs: " + str(path))
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            check()
            digest.update(block)
    if digest.hexdigest() != binding["sha256"]:
        raise Stop("OTRAY-E-BINDING", "Locked file bytes differ: " + str(path))
    if "mode" in binding and oct(stat.S_IMODE(path.stat().st_mode)) != binding["mode"]:
        raise Stop("OTRAY-E-BINDING", "Locked file mode differs: " + str(path))


def _inside(path, root):
    path, root = Path(path), Path(root).resolve()
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise Stop("OTRAY-E-BINDING", "Locked path escapes its declared root") from exc
    return path


def _verify_distribution(section, check):
    check_file(section["archive"], {"sha256": ARCHIVE_SHA, "size_bytes": 377397328}, check)
    if section["archive_sha256"] != ARCHIVE_SHA or section["archive_size_bytes"] != 377397328 or section["executable_sha256"] != BLENDER_SHA:
        raise Stop("OTRAY-E-BINDING", "Blender pins differ from adopted C198 bytes")
    executable = Path(section["executable"])
    check_file(executable, {"sha256": BLENDER_SHA, "size_bytes": section["executable_size_bytes"]}, check)
    inventory = Path(section["distribution_inventory"])
    check_file(inventory, {"sha256": section["distribution_inventory_sha256"], "size_bytes": section["distribution_inventory_size_bytes"]}, check)
    rows = read_json(inventory, 8 * 1024 * 1024)
    base = Path(section["root"]).resolve().parent
    if executable.resolve() != Path(section["root"]).resolve() / "blender":
        raise Stop("OTRAY-E-BINDING", "Blender executable does not belong to the locked distribution")
    expected = set()
    for row in rows:
        check()
        path = _inside(base / row["path"], base)
        expected.add(path.relative_to(base).as_posix())
        typ = row["type"]
        if typ == "file":
            check_file(path, {"sha256": row["sha256"], "size_bytes": row["bytes"], "mode": row["mode"]}, check)
        elif typ == "directory":
            if path.is_symlink() or not path.is_dir() or oct(stat.S_IMODE(path.stat().st_mode)) != row["archive_mode"]:
                raise Stop("OTRAY-E-BINDING", "Distribution directory changed")
        elif typ in {"symlink", "hardlink"}:
            # The selected archive inventory records native library links.
            target = row.get("target", row.get("linkname", row.get("link_target")))
            if typ == "symlink":
                if not path.is_symlink() or os.readlink(path) != target:
                    raise Stop("OTRAY-E-BINDING", "Distribution symbolic link changed")
            elif not path.is_file():
                raise Stop("OTRAY-E-BINDING", "Distribution hard link is absent")
        else:
            raise Stop("OTRAY-E-BINDING", "Unknown distribution entry kind")
    actual = {Path(section["root"]).relative_to(base).as_posix()}
    actual.update(p.relative_to(base).as_posix() for p in Path(section["root"]).rglob("*"))
    if actual != expected:
        raise Stop("OTRAY-E-BINDING", "Distribution file inventory changed")


def _host_bindings(inventory):
    """Normalize the reviewed OS/interpreter inventory without dropping aliases."""
    files, aliases = {}, {}
    for row in inventory["files"]:
        target = row["resolved_path"]
        binding = {"sha256": row["sha256"], "size_bytes": row["bytes"], "mode": row["mode"]}
        if target in files and files[target] != binding:
            raise Stop("OTRAY-E-BINDING", "Conflicting host inventory aliases")
        files[target] = binding
        aliases[row["path"]] = {"resolved_path": target, "symlink": row["symlink"], "link_target": row["link_target"]}
    return files, aliases


def _verify_host(host, check):
    inventory = Path(host["inventory"])
    check_file(inventory, {"sha256": host["inventory_sha256"], "size_bytes": host["inventory_size_bytes"]}, check)
    files, aliases = _host_bindings(read_json(inventory, 8 * 1024 * 1024))
    if files != host["files"] or aliases != host["aliases"]:
        raise Stop("OTRAY-E-BINDING", "Host closure differs from the reviewed complete inventory")
    for filename, alias in sorted(aliases.items()):
        check()
        path = Path(filename)
        if path.is_symlink() != alias["symlink"] or str(path.resolve()) != alias["resolved_path"]:
            raise Stop("OTRAY-E-BINDING", "Host runtime alias changed: " + filename)
        if alias["symlink"] and os.readlink(path) != alias["link_target"]:
            raise Stop("OTRAY-E-BINDING", "Host runtime symbolic link changed: " + filename)
    for filename, binding in sorted(files.items()):
        check_file(filename, binding, check)


def _environment(schedule, slot):
    return {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
            "HOME": str(schedule / "environment" / slot / "home"),
            "XDG_CONFIG_HOME": str(schedule / "environment" / slot / "config"),
            "XDG_CACHE_HOME": str(schedule / "environment" / slot / "cache"),
            "TMPDIR": str(schedule / "environment" / slot / "tmp"),
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "OMP_NUM_THREADS": "2",
            "PYTHONHASHSEED": "0", "PYTHONSAFEPATH": "1", "LIBGL_ALWAYS_SOFTWARE": "1", "LP_NUM_THREADS": "2",
            "OPENBLAS_NUM_THREADS": "2", "BLENDER_USER_CONFIG": str(schedule / "environment" / slot / "blender-config"),
            "BLENDER_USER_SCRIPTS": str(schedule / "environment" / slot / "blender-scripts")}


def _delivered_controls(schedule):
    return [{"case": "D%02d" % i, "after_slot": "N07" if i == 5 else "N01",
             "expected": "Q03" if i == 5 else "Q01", "variant": variant,
             "directory": str(schedule / "delivered-controls" / ("D%02d-%s" % (i, variant)))}
            for i in range(1, 9) for variant in (("copy", "reordered") if i == 8 else ("copy",))]


def verify_lock(path, *, approval=True, check=lambda: None, native_dependencies=True, runtime=False):
    path = Path(path).resolve()
    lock = read_json(path, 8 * 1024 * 1024)
    digest = sha256_file(path)
    if lock.get("schema") != SCHEMA or lock.get("profile") != PROFILE or lock.get("contract") != CONTRACT:
        raise Stop("OTRAY-E-BINDING", "Input-lock identity differs")
    if lock.get("limits") != ALL_LIMITS:
        raise Stop("OTRAY-E-BINDING", "Frozen transaction or source limits differ")
    root = Path(lock["repo_root"]).resolve()
    if root != ROOT.resolve():
        raise Stop("OTRAY-E-BINDING", "Bootstrap checkout differs from the approved checkout")
    reject_repository_bytecode(root)
    if lock.get("host_environment") != HOST_ENVIRONMENT:
        raise Stop("OTRAY-E-BINDING", "Host environment differs from the fixed finite input")
    if runtime and (dict(os.environ) != HOST_ENVIRONMENT or not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode):
        raise Stop("OTRAY-E-BINDING", "Production host must start with -IBS and the exact locked environment")
    if approval:
        approved = read_json(path.with_suffix(".approval.json"))
        gates = {"source_controls", "reader_controls", "lifecycle_controls", "dependency_bytes", "executable_closure"}
        if (approved.get("schema") != APPROVAL_SCHEMA or approved.get("decision") != "APPROVED_FOR_NATIVE"
                or approved.get("input_lock_sha256") != digest or not approved.get("reviewer")
                or set(approved.get("readiness", {})) != gates or any(approved["readiness"][k] is not True for k in gates)
                or set(approved.get("evidence", {})) != gates):
            raise Stop("OTRAY-E-BINDING", "Exact independent pre-native approval is missing or incomplete")
        for gate, evidence in approved["evidence"].items():
            if set(evidence) != {"path", "sha256", "size_bytes"} or not Path(evidence["path"]).is_absolute():
                raise Stop("OTRAY-E-BINDING", "Readiness gate lacks its actual immutable receipt: " + gate)
            check_file(evidence["path"], evidence, check)
    files = lock.get("repository_files")
    if not isinstance(files, dict) or not files:
        raise Stop("OTRAY-E-BINDING", "Complete executable repository closure is absent")
    required = {p.relative_to(root).as_posix() for p in (root / "prototypes/static_tray_v01").glob("*.py")}
    required |= {p.relative_to(root).as_posix() for p in (root / "ontokin").rglob("*.py")}
    required |= {"prototypes/static_tray_v01/" + name for name in ("__init__.py", "errors.py", "canonical.py", "sources.py", "fixtures.py",
                 "cli.py", "lock.py", "transaction.py", "qualification.py", "supervisor.py", "store.py", "worker.py", "receiver.py", "receive_check.py")}
    required |= {"tools/static_tray_reader_v01/" + n for n in READER_NAMES}
    required |= {"prototypes/static_tray_v01/" + n for n in ("export-settings.json", "import-settings.json", "delivery-rules.json")}
    required.add("prototypes/static_tray_v01/readback.mjs")
    required.add("prototypes/__init__.py")
    if not required <= set(files):
        raise Stop("OTRAY-E-BINDING", "An executable role is outside the locked source closure")
    for relative, binding in sorted(files.items()):
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise Stop("OTRAY-E-BINDING", "Nonrelative repository input")
        check_file(_inside(root / relative, root), binding, check)
    host = lock["host"]
    if platform.python_version() != "3.12.14" or sys.platform != "linux" or platform.machine() != "x86_64":
        raise Stop("OTRAY-E-BINDING", "Host interpreter/platform differs from the frozen target")
    if Path(sys.executable).resolve() != Path(host["python"]).resolve():
        raise Stop("OTRAY-E-BINDING", "Host interpreter executable differs")
    check_file(Path(host["python"]).resolve(), {"sha256": host["python_sha256"], "size_bytes": host["python_size_bytes"]}, check)
    _verify_host(host, check)
    reader = lock["independent_reader"]
    if set(reader["files"]) != READER_NAMES:
        raise Stop("OTRAY-E-BINDING", "Independent reader closure is incomplete")
    for name, sha in reader["files"].items():
        if files["tools/static_tray_reader_v01/" + name]["sha256"] != sha:
            raise Stop("OTRAY-E-BINDING", "Independent reader identity disagrees with repository closure")
    if reader["delivery_rules"] != read_json(root / "prototypes/static_tray_v01/delivery-rules.json"):
        raise Stop("OTRAY-E-BINDING", "Delivery rules differ from the locked file")
    controls = read_json(root / "docs/engineering/static-tray-mapping-c198/CONTROLS.json")
    slots = lock["slots"]
    if len(slots) != 12:
        raise Stop("OTRAY-E-BINDING", "Exactly twelve assigned native slots are required")
    schedule = Path(lock["schedule_root"]).resolve()
    if lock.get("delivered_controls") != _delivered_controls(schedule):
        raise Stop("OTRAY-E-BINDING", "Actual delivered controls must use all frozen D01-D08 inputs and both D08 variants")
    from .format_check import verify_manifest
    supplemental = lock["external_readback"]
    check_file(supplemental["path"], supplemental, check)
    verify_manifest(supplemental["path"], schedule_root=schedule, check=check)
    for row, frozen in zip(slots, controls["future_qualification_native_slots"]):
        if any(row[k] != frozen[k] for k in ("slot", "case", "route", "purpose", "maximum_starts")):
            raise Stop("OTRAY-E-BINDING", "Assigned native order, route or purpose differs")
        for key in ("store", "stage", "receiver_stage", "result"):
            _inside(row[key], schedule)
        native = [lock["blender"]["executable"], *NATIVE_FLAGS, "--python", str(root / "prototypes/static_tray_v01/worker.py"), "--", "--job", str(Path(row["stage"]) / "job.json")]
        receiver = [lock["blender"]["executable"], *NATIVE_FLAGS, "--python", str(root / "prototypes/static_tray_v01/receiver.py"), "--", "--job", str(Path(row["receiver_stage"]) / "job.json")]
        if row["native_argv"] != native or row["receiver_argv"] != receiver:
            raise Stop("OTRAY-E-BINDING", "Native launch differs from fixed process arguments")
        if row["environment"] != _environment(schedule, row["slot"]):
            raise Stop("OTRAY-E-BINDING", "Runtime environment differs from the fixed clean values")
        command = [host["python"], "-IBS", str(root / "prototypes/static_tray_v01/cli.py"), "run", "--route", row["route"],
                   "--source", row["source_manifest"], "--lock", str(path), "--slot", row["slot"],
                   "--store", row["store"], "--result", row["result"]]
        if row["command"] != command:
            raise Stop("OTRAY-E-BINDING", "Host transaction command differs from the expanded lock")
    if native_dependencies:
        _verify_distribution(lock["blender"], check)
    check()
    return lock, digest


def independent_modules(lock):
    directory = ROOT / "tools/static_tray_reader_v01"
    for name in ("expected", "glb", "reader", "corrupt"):
        if name in sys.modules and Path(sys.modules[name].__file__).resolve() != (directory / (name + ".py")).resolve():
            raise Stop("OTRAY-E-BINDING", "Ambient module shadows the independent reader")
    previous_path = list(sys.path)
    sys.path.insert(0, str(directory))
    try:
        result = {name: importlib.import_module(name) for name in ("expected", "glb", "reader", "corrupt")}
    finally:
        sys.path[:] = previous_path
    return result


def build_lock(output, *, schedule_root, blender_root, blender_archive, distribution_inventory, host_inventory, format_manifest):
    """Create actual fully expanded inputs; it never manufactures approval."""
    from .sources import lower_source
    root, schedule = ROOT.resolve(), Path(schedule_root).resolve()
    output = Path(output).resolve()
    if output.exists() or schedule.exists():
        raise ValueError("Lock output and execution schedule must be new paths")
    git = lambda *args: subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    implementation = {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}")}
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Tracked implementation files must be committed before sealing")
    reject_repository_bytecode(root)
    control_dir = root / "docs/engineering/static-tray-mapping-c198"
    frozen = read_json(control_dir / "CONTROLS.json")["future_qualification_native_slots"]
    native, slots, revisions = Path(blender_root).resolve() / "blender", [], {}
    for source in frozen:
        row = dict(source)
        slot, route, case = row["slot"], row["route"], row["case"]
        seed = root / "fixtures/static_tray_v01/native" / case / route / "source.json"
        lowered = lower_source(route, seed, PROFILE)
        shared = case in {"Q04", "Q05"} or row["purpose"] == "baseline"
        store = schedule / "stores" / (route if shared else slot)
        stage, receiving = schedule / "stages" / (slot + "-build"), schedule / "stages" / (slot + "-receive")
        source_ref = {"N03": "N01", "N04": "N02"}.get(slot)
        if source_ref:
            original = next(s for s in slots if s["slot"] == source_ref)
            manifest = Path(original["store"]) / "objects" / source_ref / "source" / "source.json"
        else:
            manifest = seed
        predecessor = None
        if case == "Q04": predecessor = revisions["N01" if route == "ontokin" else "N02"]
        if case == "Q05": predecessor = revisions["N09" if route == "ontokin" else "N10"]
        revision = "sha256:" + hashlib.sha256(b"ontokin.static-tray.candidate/0.1.0\0" + slot.encode() + b"\0" + lowered.provenance["candidate_identity"].encode() + b"\0" + lowered.canonical_bytes).hexdigest()
        revisions[slot] = revision
        environment = _environment(schedule, slot)
        row.update(source_manifest=str(manifest), source_reference_slot=source_ref,
                   source_manifest_sha256=sha256_file(seed), source_manifest_size_bytes=seed.stat().st_size,
                   source_files={name: {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)} for name, data in lowered.files.items()},
                   source_identity=lowered.provenance["candidate_identity"], canonical_sha256=hashlib.sha256(lowered.canonical_bytes).hexdigest(),
                   store=str(store), stage=str(stage), receiver_stage=str(receiving), result=str(schedule / "results" / (slot + ".json")),
                   expected_predecessor=predecessor, candidate_revision=revision, environment=environment,
                   native_argv=[str(native), *NATIVE_FLAGS, "--python", str(root / "prototypes/static_tray_v01/worker.py"), "--", "--job", str(stage / "job.json")],
                   receiver_argv=[str(native), *NATIVE_FLAGS, "--python", str(root / "prototypes/static_tray_v01/receiver.py"), "--", "--job", str(receiving / "job.json")])
        row["command"] = [str(Path(sys.executable).resolve()), "-IBS", str(root / "prototypes/static_tray_v01/cli.py"), "run", "--route", route,
                          "--source", str(manifest), "--lock", str(output), "--slot", slot, "--store", str(store), "--result", row["result"]]
        slots.append(row)
    selected = set((root / "ontokin").rglob("*.py")) | set((root / "prototypes/static_tray_v01").glob("*.py"))
    selected.add(root / "prototypes/__init__.py")
    selected |= set((root / "prototypes/static_tray_v01").glob("*.json"))
    selected |= set((root / "prototypes/static_tray_v01").glob("*.mjs"))
    selected |= {root / "tools/static_tray_reader_v01" / name for name in READER_NAMES}
    selected |= {p for p in (root / "fixtures/static_tray_v01").rglob("*") if p.is_file() and not p.is_symlink()}
    selected |= {p for p in control_dir.iterdir() if p.is_file()}
    selected |= set((root / "tests").glob("test_static_tray*.py"))
    files = {p.relative_to(root).as_posix(): file_binding(p) for p in sorted(selected) if "__pycache__" not in p.parts}
    tracked = set(git("ls-files").splitlines())
    if not set(files) <= tracked:
        raise ValueError("All executable inputs and fixtures must be tracked and committed before sealing")
    host_inv = Path(host_inventory).resolve()
    host_files, host_aliases = _host_bindings(read_json(host_inv, 8 * 1024 * 1024))
    python = Path(sys.executable).resolve()
    inv = Path(distribution_inventory).resolve()
    supplemental = Path(format_manifest).resolve()
    from .format_check import verify_manifest
    verify_manifest(supplemental, schedule_root=schedule)
    lock = {"schema": SCHEMA, "profile": PROFILE, "contract": CONTRACT, "repo_root": str(root),
            "implementation": implementation, "schedule_root": str(schedule), "repository_files": files, "host_environment": HOST_ENVIRONMENT,
            "host": {"python": str(python), "python_sha256": sha256_file(python), "python_size_bytes": python.stat().st_size,
                     "version": "3.12.14", "platform": "linux-x86_64", "files": host_files, "aliases": host_aliases,
                     "hash_seed_environment_effect": "Ignored by host -I/-E; canonical ordering is explicit and actual regeneration equality remains required",
                     "inventory": str(host_inv), "inventory_sha256": sha256_file(host_inv), "inventory_size_bytes": host_inv.stat().st_size},
            "blender": {"root": str(Path(blender_root).resolve()), "executable": str(native), "executable_sha256": BLENDER_SHA,
                        "executable_size_bytes": native.stat().st_size, "archive": str(Path(blender_archive).resolve()),
                        "archive_sha256": ARCHIVE_SHA, "archive_size_bytes": 377397328, "distribution_inventory": str(inv),
                        "distribution_inventory_sha256": sha256_file(inv), "distribution_inventory_size_bytes": inv.stat().st_size},
            "limits": ALL_LIMITS,
            "independent_reader": {"files": {name: files["tools/static_tray_reader_v01/" + name]["sha256"] for name in sorted(READER_NAMES)},
                                   "delivery_rules": read_json(root / "prototypes/static_tray_v01/delivery-rules.json")},
            "slots": slots, "external_readback": {"path": str(supplemental), **file_binding(supplemental)},
            "delivered_controls": _delivered_controls(schedule)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json_bytes(lock))
    return lock, sha256_file(output)
