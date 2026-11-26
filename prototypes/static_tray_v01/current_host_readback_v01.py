"""Explicit current-host CPU readback; historical/native entry points stay separate.

An expected configuration digest is an input supplied by the independently
reviewed execution plan. This module never manufactures approval from a file's
observed digest. No validation function starts Node or a dependency inspector.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
import uuid

from . import supervisor
from .format_check import ENVIRONMENT, LIMITS, NODE_FLAGS, THREE_OPTIONS, VALIDATOR_OPTIONS

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "ontokin.current-host-readback/0.1.0"
PREFIX = "ontokin.current-host-readback-"
VERSION = "/0.1.0"
CONFIG_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG"
DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
PROVIDER = "prototypes/static_tray_v01/current_host_readback_v01.py"
PROBE = "prototypes/static_tray_v01/current_host_readback_v01.mjs"
CONTRACT_PATH = "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md"
BASELINE_MAP = "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip"
EXTERNAL_INPUTS = "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json"
EXTERNAL_SHA256 = "21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5"
ARCHIVE_SHA256 = "b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9"
NODE_SHA256 = "acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa"
NODE_BYTES = 126951512
NODE_VERSION = "v24.22.1"
NODE_ARCHIVE_SHA256 = "100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5"
NODE_ARCHIVE_BYTES = 45186132
SOURCE_TREES = ("ontokin", "tests", "prototypes/static_tray_v01", "tools/static_tray_reader_v01")
SOURCE_OPTIONAL = ("prototypes/__init__.py", "tools/__init__.py", "tests/__init__.py")
SOURCE_FILES = (
    "tools/check_local.py", "tools/prepare_current_host_readback.py", "tools/storage_identity.py",
    "tools/force-agent-verification-requirements.txt", "tools/native-reader-verification-linux-cp312.lock", "pyproject.toml",
    "docs/engineering/static-tray-mapping-c198/CONTROLS.json", EXTERNAL_INPUTS, CONTRACT_PATH,
    "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json",
    "docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json", BASELINE_MAP,
)
ORIGINAL_BODIES = {
    "ReadbackCoordinatorSeams.run_seam": "2f39cde2f0f4a18eb54b003e2628b22c47d49495d862d25e38223b5a056817a5",
    "ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked": "222b654a8da505965f0821be4e7b61eefeb1a5f12e767c72e6123feba909f06d",
    "ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup": "29665028886624307beacb4debb33b8582f91bf60951149c0160ae957ed68f98",
    "ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm": "f4a5d8242e91d3792039b94f2f75c8002b7cc5e1b432ce3cc91d46d65d3f1f55",
    "ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending": "5e3041a6f1e57db4c4c03e97927e1aa88c6d8dfe2b431e71b38319e3851b75bc",
    "ReadbackCPUControls.check_case": "53a03c60a7473af90ba88f2fddf225713036d417cf3c13a0c1e8a6a3105946a4",
    "ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries": "e7793b38ebedd196c228ce6841642c2546c8ef1f5db552b1b1f824a30087fd34",
    "ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries": "e09a9c173e4879558da9206549f085a840639a314c22e525fccabc498c7e3dd4",
    "ReadbackCPUControls.test_three_rejects_changed_synthetic_reference": "8b2de031c533e1308efeef130047b0a2b4fcfc1cb6cd2f576e7b3ef832ec05d9",
}
METHOD_IDS = sorted("test_static_tray_readback_v01." + name for name in ORIGINAL_BODIES if ".test_" in name)
CASES = {"Q01-positive": "Q01", "Q03-positive": "Q03", "Q01-changed-reference": "Q01"}
CONFIG_KEYS = "schema contract contract_source source host dependencies runtime methods evidence_root parent".split()
MANIFEST_KEYS = "schema contract profile schedule_root cohort_root dependencies_root scope limits environment files runtime validator_version three_version validator_entry three_package three_entry gltf_loader_entry module_loader probe validator_options three_options slots selection source host methods dependencies".split()
SCOPE = "Three original synthetic CPU cases only; twelve native slots are structural, never execution authority"


class CurrentHostBindingError(RuntimeError):
    """Provider refusal, deliberately unrelated to supervisor.Stop."""

    def __init__(self, category, reason, *, cause=None, process_record=None, state="REJECTED"):
        self.code, self.reason, self.state = "CH-" + category, reason, state
        self.cause = _failure(cause) if cause is not None else None
        self.process_record = process_record
        self.refusal_record = {"schema": PREFIX + "refusal" + VERSION, "passed": False,
                               "error": {"code": self.code, "reason": reason, "state": state, "cause": self.cause},
                               "authorized_evidence_destination": "unavailable", "evidence_finalized": False}
        super().__init__(reason)

    def as_dict(self):
        return {"code": self.code, "reason": self.reason, "state": self.state, "cause": self.cause}


def _failure(exc):
    if hasattr(exc, "as_dict"):
        return exc.as_dict()
    return {"type": type(exc).__name__, "reason": str(exc)}


def _require(condition, category, reason):
    if not condition:
        raise CurrentHostBindingError(category, reason)


def _keys(value, expected, category="SCHEMA"):
    _require(type(value) is dict and set(value) == set(expected), category,
             "Object has missing or unknown members; expected " + ", ".join(sorted(expected)))


def _schema(value, kind, keys, category="SCHEMA"):
    _keys(value, keys, category)
    _require(value["schema"] == PREFIX + kind + VERSION, category, "Unsupported " + kind + " schema")


def _digest(value, category="SCHEMA"):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             category, "Expected a lowercase SHA-256 digest")
    return value


def _absolute(value, *, category="SCHEMA", symlinks=False):
    _require(isinstance(value, (str, Path)), category, "Expected an absolute path")
    text = str(value)
    path = Path(text)
    _require(path.is_absolute() and str(path) == text and ".." not in path.parts,
             category, "Expected a normalized absolute path: " + text)
    if not symlinks:
        for item in (path, *path.parents):
            _require(not item.is_symlink(), category, "Symlink path component: " + str(item))
    return path


def _relative(value):
    _require(type(value) is str and value and "\\" not in value, "SCHEMA", "Invalid relative path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and str(path) == value and ".." not in path.parts and value != ".",
             "SCHEMA", "Unsafe relative path: " + value)
    return path


def _inside(path, parent, category="SCHEMA"):
    path, parent = _absolute(path, category=category), _absolute(parent, category=category)
    _require(path != parent and path.is_relative_to(parent), category, "Path is outside its declared parent")
    return path


def _tick(check):
    try:
        check()
    except supervisor.Stop as exc:
        raise CurrentHostBindingError("CLOCK", "Provider validation exhausted the existing clock", cause=exc,
                                      state=exc.state) from exc


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def _binding_shape(binding, *, descriptor=False):
    _keys(binding, ["sha256", "size_bytes", "mode"] + (["path"] if descriptor else []))
    _digest(binding["sha256"])
    _require(type(binding["size_bytes"]) is int and binding["size_bytes"] >= 0,
             "SCHEMA", "Invalid file size")
    _require(type(binding["mode"]) is str and re.fullmatch(r"0o[0-7]{3,4}", binding["mode"]) is not None,
             "SCHEMA", "Invalid file mode")
    if descriptor:
        _absolute(binding["path"])


def file_binding(path, *, maximum=None, check=lambda: None, private=True, category="SCHEMA"):
    """Hash an opened regular file and reject replacement/mutation during the read."""
    path = _absolute(path, category=category)
    _tick(check)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            before = os.fstat(descriptor)
            _require(stat.S_ISREG(before.st_mode) and (not private or before.st_nlink == 1),
                     category, "Expected a private regular file: " + str(path))
            _require(maximum is None or before.st_size <= maximum, category, "File byte limit exceeded: " + str(path))
            digest = hashlib.sha256()
            length = 0
            while True:
                _tick(check)
                block = os.read(descriptor, 1024 * 1024)
                if not block:
                    break
                length += len(block)
                _require(maximum is None or length <= maximum, category, "File grew beyond its byte limit")
                digest.update(block)
            after, named = os.fstat(descriptor), path.lstat()
            identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mode, st.st_nlink, st.st_mtime_ns, st.st_ctime_ns)
            _require(identity(before) == identity(after) == identity(named) and length == before.st_size,
                     category, "File changed while being read: " + str(path))
            return {"sha256": digest.hexdigest(), "size_bytes": length, "mode": oct(stat.S_IMODE(before.st_mode))}
        finally:
            os.close(descriptor)
    except CurrentHostBindingError:
        raise
    except OSError as exc:
        raise CurrentHostBindingError(category, "Cannot authenticate file: " + str(path), cause=exc) from exc


def _bound(path, expected, *, maximum=None, check=lambda: None, private=True, category="SCHEMA"):
    _binding_shape(expected)
    actual = file_binding(path, maximum=maximum, check=check, private=private, category=category)
    _require(actual == expected, category, "Locked file identity differs: " + str(path))
    return actual


def _read_bytes(path, maximum, *, check=lambda: None, category="SCHEMA"):
    path = _absolute(path, category=category)
    _tick(check)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            opened = os.fstat(fd)
            _require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1 and opened.st_size <= maximum,
                     category, "JSON must be a bounded private regular file")
            blocks, length = [], 0
            while True:
                _tick(check)
                block = os.read(fd, min(1024 * 1024, maximum - length + 1))
                if not block:
                    break
                length += len(block)
                _require(length <= maximum, category, "JSON exceeded its byte allowance while reading")
                blocks.append(block)
            after, named = os.fstat(fd), path.lstat()
            identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mode, st.st_nlink, st.st_mtime_ns, st.st_ctime_ns)
            _require(identity(opened) == identity(after) == identity(named) and length == opened.st_size,
                     category, "JSON path or contents changed while reading")
            raw = b"".join(blocks)
            before = {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": length,
                      "mode": oct(stat.S_IMODE(opened.st_mode))}
        finally:
            os.close(fd)
    except CurrentHostBindingError:
        raise
    except OSError as exc:
        raise CurrentHostBindingError(category, "Cannot read bounded JSON file: " + str(path), cause=exc) from exc
    return raw, before


def _read(path, maximum, *, check=lambda: None, category="SCHEMA"):
    raw, before = _read_bytes(path, maximum, check=check, category=category)
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, category, "Duplicate JSON member: " + key)
            result[key] = value
        return result
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise CurrentHostBindingError(category, "Invalid bounded JSON", cause=exc) from exc
    _bound(path, before, check=check, category=category)
    return value, before


def _document(descriptor, maximum, *, check=lambda: None, category="SCHEMA"):
    _binding_shape(descriptor, descriptor=True)
    value, actual = _read(descriptor["path"], maximum, check=check, category=category)
    _require(actual == {key: descriptor[key] for key in ("sha256", "size_bytes", "mode")},
             category, "Document identity differs: " + descriptor["path"])
    return value


def _describe(path, *, check=lambda: None):
    return {"path": str(_absolute(path)), **file_binding(path, check=check)}


def _write_new(path, value):
    path = _absolute(path, category="EVIDENCE")
    raw = _canonical(value)
    _require(len(raw) <= 16 * 1024 * 1024, "EVIDENCE", "Evidence exceeds its bounded size")
    _require(path.parent.is_dir(), "EVIDENCE", "Evidence parent is missing")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, "wb", closefd=False) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(fd)
        finally:
            os.close(fd)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        raise CurrentHostBindingError("EVIDENCE", "Exclusive evidence write failed: " + str(path),
                                      cause=exc, state="UNKNOWN") from exc
    return _describe(path)


def _source_paths(root):
    rows = set()
    for relative in SOURCE_TREES:
        directory = _absolute(root / relative, category="SOURCE")
        _require(directory.is_dir(), "SOURCE", "Execution source directory is missing: " + relative)
        for parent, directories, files in os.walk(directory, followlinks=False):
            for name in directories:
                item = Path(parent) / name
                _require(not item.is_symlink() and name != "__pycache__", "SOURCE", "Unbound source directory or bytecode cache")
            for name in files:
                path = Path(parent) / name
                _require(path.suffix not in (".pyc", ".pyo"), "SOURCE", "Repository bytecode is outside the source-only lock")
                _absolute(path, category="SOURCE")
                rows.add(path.relative_to(root).as_posix())
    for relative in SOURCE_FILES:
        _require((root / relative).is_file(), "SOURCE", "Required source role is missing: " + relative)
        rows.add(relative)
    rows.update(relative for relative in SOURCE_OPTIONAL if (root / relative).exists())
    return sorted(rows)


def source_inventory(root, *, check=lambda: None):
    root = _absolute(root, category="SOURCE")
    return {"schema": PREFIX + "source" + VERSION,
            "files": {relative: file_binding(root / relative, check=check, category="SOURCE")
                      for relative in _source_paths(root)}}


def _verify_source(source, *, derived=False, own_root=True, check=lambda: None):
    _keys(source, ("root", "commit", "tree", "inventory"))
    root = _absolute(source["root"], category="SOURCE")
    _require(not own_root or root == ROOT, "SOURCE", "Provider belongs to another source checkout")
    for key in ("commit", "tree"):
        _require(type(source[key]) is str and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", source[key]) is not None,
                 "SOURCE", "Invalid source Git identity")
    expected = _document(source["inventory"], 16 * 1024 * 1024, check=check, category="SOURCE")
    _schema(expected, "source", ("schema", "files"))
    _require(type(expected["files"]) is dict and set(expected["files"]) == set(_source_paths(root)),
             "SOURCE", "Complete CPU source inventory differs")
    for relative, binding in expected["files"].items():
        _relative(relative)
        _bound(root / relative, binding, check=check, category="SOURCE")
    # The driver owns its broader immutable copied-input definition. Do not
    # introduce a second set of generated exceptions here.
    from tools.check_local import git_read, immutable_workspace_inputs
    def git(*args):
        _tick(check)
        remaining = getattr(check, "deadline", float("inf")) - time.monotonic()
        _require(remaining > 0, "CLOCK", "No remaining allowance for source identity inspection")
        try:
            result = git_read(root, *args, timeout=min(5, remaining))
        except (OSError, subprocess.SubprocessError) as exc:
            _tick(check)
            raise CurrentHostBindingError("SOURCE", "Bounded source Git inspection failed", cause=exc) from exc
        _tick(check)
        return result
    _require(git("rev-parse", "--show-toplevel") == str(root)
             and git("rev-parse", "--verify", "HEAD^{commit}") == source["commit"]
             and git("rev-parse", "--verify", source["commit"] + "^{tree}") == source["tree"],
             "SOURCE", "Source commit/tree differs or is unavailable")
    for line in git("status", "--porcelain=v1", "--untracked-files=no").splitlines():
        name = line[3:]
        allowed = derived and not immutable_workspace_inputs({"files": [{"path": name}]})["files"]
        _require(allowed and " -> " not in name and not name.startswith('"'), "SOURCE", "Dirty source: " + line)
    untracked = git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    for name in filter(None, untracked):
        allowed = derived and not immutable_workspace_inputs({"files": [{"path": name}]})["files"]
        _require(allowed, "SOURCE", "Untracked source input: " + name)
    _tick(check)
    return expected


def _alias(path):
    path = _absolute(path, category="HOST", symlinks=True)
    return {"resolved_path": str(path.resolve(strict=True)), "symlink": path.is_symlink(),
            "link_target": os.readlink(path) if path.is_symlink() else None}


def _elf_interpreter(path, *, check=lambda: None):
    """Read the declared ELF PT_INTERP without executing the binary."""
    path = _absolute(path, category="RUNTIME")
    _tick(check)
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= NODE_BYTES, "RUNTIME", "Unsafe ELF input")
        head = os.pread(fd, 64, 0)
        _require(len(head) == 64, "RUNTIME", "Truncated ELF header")
        _require(head[:4] == b"\x7fELF" and head[4] in (1, 2) and head[5] in (1, 2), "RUNTIME", "Invalid ELF executable")
        endian = "<" if head[5] == 1 else ">"
        wide = head[4] == 2
        offset = struct.unpack_from(endian + ("Q" if wide else "I"), head, 32 if wide else 28)[0]
        size, count = struct.unpack_from(endian + "HH", head, 54 if wide else 42)
        _require(count <= 256 and size >= (56 if wide else 32), "RUNTIME", "Unsupported ELF program table")
        found = []
        for number in range(count):
            _tick(check)
            _require(offset + (number + 1) * size <= before.st_size, "RUNTIME", "ELF program table escapes file")
            row = os.pread(fd, size, offset + number * size)
            _require(len(row) == size, "RUNTIME", "Truncated ELF program table")
            if struct.unpack_from(endian + "I", row)[0] == 3:
                start = struct.unpack_from(endian + ("Q" if wide else "I"), row, 8 if wide else 4)[0]
                length = struct.unpack_from(endian + ("Q" if wide else "I"), row, 32 if wide else 16)[0]
                _require(1 < length <= 4096, "RUNTIME", "ELF interpreter exceeds bound")
                _require(start + length <= before.st_size, "RUNTIME", "ELF interpreter escapes file")
                raw = os.pread(fd, length, start)
                _require(len(raw) == length and raw[-1:] == b"\0" and b"\0" not in raw[:-1], "RUNTIME", "Invalid ELF interpreter")
                found.append(raw[:-1].decode("ascii"))
        _require(len(found) == 1, "RUNTIME", "Expected exactly one ELF interpreter")
        after, named = os.fstat(fd), path.lstat()
        identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mode, st.st_mtime_ns, st.st_ctime_ns)
        _require(identity(before) == identity(after) == identity(named), "RUNTIME", "ELF changed while inspected")
        _tick(check)
        return found[0]
    finally:
        os.close(fd)


def _verify_inspection(descriptor, argv, *, check=lambda: None):
    receipt = _document(descriptor, 8 * 1024 * 1024, check=check, category="HOST")
    _schema(receipt, "inspection", "schema argv environment timeout_ms started_at_utc finished_at_utc process stdout stderr".split())
    _require(receipt["argv"] == argv and receipt["environment"] == ENVIRONMENT and receipt["timeout_ms"] == 5000,
             "HOST", "Inspection command, environment or allowance differs")
    process = receipt["process"]
    _require(type(process) is dict and process.get("argv") == argv and process.get("environment") == ENVIRONMENT
             and type(process.get("pid")) is int and process["pid"] > 0 and process.get("process_group") == process["pid"]
             and process.get("returncode") == 0 and process.get("handles_closed") is True
             and process.get("cleanup", {}).get("passed") is True
             and process.get("cleanup", {}).get("process_group_absent") is True
             and process.get("cleanup", {}).get("reaped") is True and not process.get("error"),
             "HOST", "Inspection did not retain a successful bounded actual process receipt")
    _require(type(process.get("start_monotonic")) in (int, float) and type(process.get("end_monotonic")) in (int, float)
             and 0 <= process["end_monotonic"] - process["start_monotonic"] <= 5,
             "HOST", "Inspection exceeded its five-second allowance")
    start, finish = (datetime.fromisoformat(receipt[key].replace("Z", "+00:00")) for key in ("started_at_utc", "finished_at_utc"))
    _require(start.tzinfo is not None and finish.tzinfo is not None and start <= finish <= datetime.now(timezone.utc),
             "HOST", "Invalid inspection timestamps")
    _require(type(receipt["stdout"]) is str and type(receipt["stderr"]) is str
             and len(receipt["stdout"].encode()) + len(receipt["stderr"].encode()) <= 4 * 1024 * 1024,
             "HOST", "Inspection output exceeds its bound")
    return receipt


def _python_pins(root, *, check=lambda: None):
    pins = {}
    raw, _ = _read_bytes(Path(root) / "tools/native-reader-verification-linux-cp312.lock", 65536, check=check, category="HOST")
    for original in raw.decode("ascii").splitlines():
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if re.fullmatch(r"--hash=sha256:[0-9a-f]{64}(?:\s*\\)?", line):
            _require(bool(pins), "HOST", "Hash continuation has no requirement declaration")
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s\\]+)(?:\s+--hash=sha256:[0-9a-f]{64})?(?:\s*\\)?", line)
        _require(match is not None and match[1] not in pins, "HOST", "Unsupported or duplicate verification requirement")
        pins[match[1]] = match[2]
    _require(len(pins) == 7, "HOST", "The exact seven verification package pins are required")
    return pins


def _verify_host(config, *, check=lambda: None):
    host = _document(config["host"], 8 * 1024 * 1024, check=check, category="HOST")
    _schema(host, "host", "schema observed_at_utc platform python runtime files aliases roles environment inspections".split())
    _keys(config["runtime"], ("executable", "version"))
    node = _absolute(config["runtime"]["executable"], category="RUNTIME")
    _require(config["runtime"]["version"] == NODE_VERSION, "RUNTIME", "Only Node v24.22.1 is admitted")
    _keys(host["runtime"], "executable version candidate_sha256 candidate_size_bytes candidate_mode source_archive".split())
    _require(host["runtime"] | {"source_archive": None} == {
        "executable": str(node), "version": NODE_VERSION, "candidate_sha256": NODE_SHA256,
        "candidate_size_bytes": NODE_BYTES, "candidate_mode": "0o755", "source_archive": None},
        "RUNTIME", "The selected Node build differs")
    _binding_shape(host["runtime"]["source_archive"], descriptor=True)
    _require(host["runtime"]["source_archive"]["sha256"] == NODE_ARCHIVE_SHA256
             and host["runtime"]["source_archive"]["size_bytes"] == NODE_ARCHIVE_BYTES,
             "RUNTIME", "Selected Node archive differs from the preserved P05 input")
    _bound(host["runtime"]["source_archive"]["path"], {k: host["runtime"]["source_archive"][k] for k in ("sha256", "size_bytes", "mode")}, check=check, category="RUNTIME")
    _keys(host["platform"], ("system", "release", "machine", "libc", "boot_id"))
    actual_platform = {"system": platform.system(), "release": platform.release(), "machine": platform.machine(),
                       "libc": list(platform.libc_ver()), "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}
    _require(actual_platform["system"] == "Linux" and host["platform"] == actual_platform,
             "HOST", "Current platform/boot identity differs")
    _keys(host["python"], ("executable", "version", "packages"))
    pins = _python_pins(ROOT, check=check)
    _require(host["python"] == {"executable": str(Path(sys.executable).resolve()), "version": platform.python_version(),
                                   "packages": {name: metadata.version(name) for name in pins}}
             and host["python"]["packages"] == pins, "HOST", "Python executable/version/package pins differ")
    _require(host["environment"] == ENVIRONMENT, "HOST", "Inspection environment differs")
    _keys(host["roles"], ("node", "python", "ldd", "inspector_interpreter", "elf_interpreter", "loader_configuration", "shared_libraries", "inspector_runtime"))
    roles = host["roles"]
    _require(roles["node"] == str(node) and roles["python"] == str(Path(sys.executable).resolve())
             and roles["ldd"] == "/usr/bin/ldd", "HOST", "Executable or inspector role differs")
    scalar = [roles[key] for key in ("node", "python", "ldd", "inspector_interpreter", "elf_interpreter")]
    arrays = []
    for key in ("loader_configuration", "shared_libraries", "inspector_runtime"):
        _require(type(roles[key]) is list and roles[key] and len(roles[key]) == len(set(roles[key])), "HOST", "Missing or duplicate runtime role inventory")
        arrays.extend(roles[key])
    named = set(scalar + arrays)
    _require(type(host["aliases"]) is dict and set(host["aliases"]) == named, "HOST", "Complete runtime alias inventory differs")
    actual_files = set()
    for name, expected in host["aliases"].items():
        _tick(check)
        _keys(expected, ("resolved_path", "symlink", "link_target"))
        try:
            actual = _alias(name)
        except OSError as exc:
            raise CurrentHostBindingError("HOST", "Runtime alias cannot be resolved", cause=exc) from exc
        _require(actual == expected, "RUNTIME" if name == str(node) else "HOST", "Runtime alias changed: " + name)
        actual_files.add(expected["resolved_path"])
    _require(type(host["files"]) is dict and set(host["files"]) == actual_files, "HOST", "Runtime file set is incomplete or extra")
    for path, binding in host["files"].items():
        _bound(path, binding, check=check, private=False, category="RUNTIME" if path == str(node) else "HOST")
    _require(host["files"].get(str(node)) == {"sha256": NODE_SHA256, "size_bytes": NODE_BYTES, "mode": "0o755"},
             "RUNTIME", "Selected executable is not the exact pinned member of the runtime closure")
    _require(_elf_interpreter(node, check=check) == roles["elf_interpreter"], "HOST", "ELF interpreter binding differs")
    _bound(node, host["files"][str(node)], check=check, private=False, category="RUNTIME")
    ldd_bytes, ldd_binding = _read_bytes(roles["ldd"], 4 * 1024 * 1024, check=check, category="HOST")
    _require(ldd_binding == host["files"][host["aliases"][roles["ldd"]]["resolved_path"]], "HOST", "Inspector changed before parsing")
    shebang = ldd_bytes.split(b"\n", 1)[0].decode("ascii").strip()
    _require(shebang == "#!" + roles["inspector_interpreter"], "HOST", "ldd interpreter is not explicitly bound")
    _keys(host["inspections"], ("node_version", "shared_libraries"))
    version = _verify_inspection(host["inspections"]["node_version"], [str(node), "--version"], check=check)
    closure = _verify_inspection(host["inspections"]["shared_libraries"], ["/usr/bin/ldd", str(node)], check=check)
    _require(version["stdout"].strip() == NODE_VERSION and "not found" not in closure["stdout"],
             "HOST", "Observed version or shared-library inspection differs")
    parsed = set(re.findall(r"(?:=>\s+)?(/[^\s]+)\s+\(", closure["stdout"]))
    _require(parsed == set(roles["shared_libraries"]) | {roles["elf_interpreter"]}, "HOST", "Observed shared-library closure differs")
    observed = datetime.fromisoformat(host["observed_at_utc"].replace("Z", "+00:00"))
    _require(observed.tzinfo is not None and observed <= datetime.now(timezone.utc)
             and all(datetime.fromisoformat(row["finished_at_utc"].replace("Z", "+00:00")) <= observed for row in (version, closure)),
             "HOST", "Host observation does not follow its fresh inspection receipts")
    return host


def dependency_inventory(root):
    """Obtain immutable relative digest/size identities from the original manifest."""
    path = Path(root) / EXTERNAL_INPUTS
    manifest, binding = _read(path, 1024 * 1024, category="DEPENDENCY")
    _require(binding["sha256"] == EXTERNAL_SHA256, "DEPENDENCY", "Historical dependency pin source changed")
    prefix = manifest["dependencies_root"] + "/"
    expected = {name[len(prefix):]: row for name, row in manifest["files"].items() if name.startswith(prefix)}
    _require(len(expected) == 24, "DEPENDENCY", "Expected the exact retained 24 dependency files")
    return expected


def _tree_state(root, files, directories, *, check=lambda: None, category="DEPENDENCY"):
    root = _absolute(root, category=category)
    _require(root.is_dir(), category, "Dependency directory is missing")
    actual_files, actual_dirs = set(), set()
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in dirs:
            path = Path(parent) / name
            _absolute(path, category=category)
            actual_dirs.add(path.relative_to(root).as_posix())
        for name in names:
            path = Path(parent) / name
            _absolute(path, category=category)
            actual_files.add(path.relative_to(root).as_posix())
    _require(actual_files == set(files) and actual_dirs == set(directories), category, "Complete dependency tree differs")
    necessary = {str(parent) for name in files for parent in _relative(name).parents if str(parent) != "."}
    _require(set(directories) == necessary, category, "Dependency directory inventory has missing or extra entries")
    for name, mode in directories.items():
        _tick(check)
        _require(oct(stat.S_IMODE((root / name).stat().st_mode)) == mode, category, "Dependency directory mode differs")
    for name, binding in files.items():
        _bound(root / name, binding, check=check, category=category)


def _verify_dependencies(config, *, check=lambda: None):
    _keys(config["dependencies"], ("root", "inventory"))
    root = _absolute(config["dependencies"]["root"], category="DEPENDENCY")
    _require(not root.is_relative_to(Path(config["source"]["root"])), "DEPENDENCY", "Dependencies must remain outside source")
    inventory = _document(config["dependencies"]["inventory"], 1024 * 1024, check=check, category="DEPENDENCY")
    _schema(inventory, "dependencies", ("schema", "files", "directories", "archive"))
    historical = dependency_inventory(config["source"]["root"])
    _require(type(inventory["files"]) is dict and set(inventory["files"]) == set(historical), "DEPENDENCY", "The exact 24 dependency paths differ")
    for name, expected in historical.items():
        _binding_shape(inventory["files"][name])
        _require({k: inventory["files"][name][k] for k in ("sha256", "size_bytes")} == expected,
                 "DEPENDENCY", "Dependency digest/size differs from its immutable historical pin")
    _binding_shape(inventory["archive"], descriptor=True)
    _require(inventory["archive"]["sha256"] == ARCHIVE_SHA256, "DEPENDENCY", "Retained archive identity differs")
    _bound(inventory["archive"]["path"], {key: inventory["archive"][key] for key in ("sha256", "size_bytes", "mode")}, check=check, category="DEPENDENCY")
    _tree_state(root, inventory["files"], inventory["directories"], check=check)
    for name, version in (("validator/package/package.json", "2.0.0-dev.3.10"), ("indexer-view/three/package.json", "0.186.1")):
        package, _ = _read(root / name, 32768, check=check, category="DEPENDENCY")
        _require(package.get("version") == version, "DEPENDENCY", "Dependency package version differs")
    return inventory


def _verify_methods(config, *, check=lambda: None):
    methods = _document(config["methods"], 1024 * 1024, check=check, category="SOURCE")
    _schema(methods, "methods", ("schema", "source_test", "original_bodies", "discovery"))
    _require(methods["source_test"] == "tests/test_static_tray_readback_v01.py" and methods["original_bodies"] == ORIGINAL_BODIES,
             "SOURCE", "Original method/helper identity declaration differs")
    path = Path(config["source"]["root"]) / methods["source_test"]
    raw, actual_source = _read_bytes(path, 4 * 1024 * 1024, check=check, category="SOURCE")
    expected_source = _document(config["source"]["inventory"], 16 * 1024 * 1024, check=check, category="SOURCE")
    _require(actual_source == expected_source["files"][methods["source_test"]], "SOURCE", "Method source changed before parsing")
    parsed = ast.parse(raw)
    actual = {}
    for group in parsed.body:
        if isinstance(group, ast.ClassDef):
            for node in group.body:
                name = group.name + "." + getattr(node, "name", "")
                if name in ORIGINAL_BODIES and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    actual[name] = hashlib.sha256(ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False).encode()).hexdigest()
    _require(actual == ORIGINAL_BODIES, "SOURCE", "Original test/helper body changed or is missing")
    discovery = _document(methods["discovery"], 8 * 1024 * 1024, check=check, category="SOURCE")
    _schema(discovery, "discovery", ("schema", "method_ids", "baseline_map"))
    ids = discovery["method_ids"]
    _require(type(ids) is list and all(type(item) is str for item in ids) and ids == sorted(set(ids))
             and all(item in ids for item in METHOD_IDS), "SOURCE", "Original/default method inventory is incomplete or duplicated")
    map_root = config["parent"]["source_root"] if config["parent"] is not None else config["source"]["root"]
    _require(discovery["baseline_map"] == _describe(Path(map_root) / BASELINE_MAP, check=check),
             "SOURCE", "Original method/discovery source map differs")
    _bound(Path(config["source"]["root"]) / BASELINE_MAP,
           {key: discovery["baseline_map"][key] for key in ("sha256", "size_bytes", "mode")},
           check=check, category="SOURCE")
    return methods


def _verify_parent(config, *, check=lambda: None):
    parent = config["parent"]
    if parent is None:
        return
    _keys(parent, ("config", "source_root", "workspace_binding"), "WORKSPACE")
    original = _document(parent["config"], 1024 * 1024, check=check, category="WORKSPACE")
    _schema(original, "config", CONFIG_KEYS)
    _require(original["parent"] is None and original["source"]["root"] == parent["source_root"],
             "WORKSPACE", "Workspace parent is not the immutable original selection")
    binding = _document(parent["workspace_binding"], 16 * 1024 * 1024, check=check, category="WORKSPACE")
    _schema(binding, "workspace", "schema identity parent_config source_root workspace_root commit tree source_inventory source_before workspace_inventory immutable_inventory_sha256 provider probe".split())
    _require(type(binding["identity"]) is str and re.fullmatch(r"[0-9a-f]{32}", binding["identity"]) is not None,
             "WORKSPACE", "Missing fresh workspace identity")
    expected = deepcopy(original)
    expected["source"]["root"] = config["source"]["root"]
    expected["contract_source"]["path"] = str(Path(config["source"]["root"]) / CONTRACT_PATH)
    expected["parent"] = parent
    _require(config == expected, "WORKSPACE", "Derived config changed more than the explicit workspace binding")
    _require(binding["parent_config"] == parent["config"] and binding["source_root"] == parent["source_root"]
             and binding["workspace_root"] == config["source"]["root"] and binding["commit"] == config["source"]["commit"]
             and binding["tree"] == config["source"]["tree"] and binding["source_inventory"] == config["source"]["inventory"]
             and binding["provider"] == str(Path(config["source"]["root"]) / PROVIDER)
             and binding["probe"] == str(Path(config["source"]["root"]) / PROBE), "WORKSPACE", "Derived source roles or identities differ")
    from tools.check_local import immutable_workspace_inputs
    before = _document(binding["source_before"], 32 * 1024 * 1024, check=check, category="WORKSPACE")
    copied = _document(binding["workspace_inventory"], 32 * 1024 * 1024, check=check, category="WORKSPACE")
    _require(before == copied and immutable_workspace_inputs(before)["sha256"] == binding["immutable_inventory_sha256"],
             "WORKSPACE", "Complete copied immutable-source proof differs")


def _selection(config_path, config_sha256, source_root, *, check=lambda: None, own_root=True):
    _digest(config_sha256, "SELECTION")
    path = _absolute(config_path, category="SELECTION")
    config, actual = _read(path, 1024 * 1024, check=check, category="SELECTION")
    _require(actual["sha256"] == config_sha256, "SELECTION", "Configuration differs from the independently supplied expected digest")
    _schema(config, "config", CONFIG_KEYS)
    _require(config["contract"] == CONTRACT, "SCHEMA", "Unsupported current-host contract")
    _keys(config["source"], ("root", "commit", "tree", "inventory"))
    root = _absolute(source_root, category="SOURCE")
    _require(config["source"]["root"] == str(root), "SOURCE", "Selected source root differs")
    _require(not path.is_relative_to(root), "SELECTION", "Operational config must remain outside source")
    _binding_shape(config["contract_source"], descriptor=True)
    _require(config["contract_source"]["path"] == str(root / CONTRACT_PATH), "SOURCE", "Contract source belongs to another checkout")
    _bound(root / CONTRACT_PATH, {key: config["contract_source"][key] for key in ("sha256", "size_bytes", "mode")}, check=check, category="SOURCE")
    evidence = _absolute(config["evidence_root"], category="EVIDENCE")
    _require(evidence.is_dir() and not evidence.is_relative_to(root), "EVIDENCE", "An external predeclared evidence parent is required")
    _verify_parent(config, check=check)
    _verify_source(config["source"], derived=config["parent"] is not None, own_root=own_root, check=check)
    host = _verify_host(config, check=check)
    dependencies = _verify_dependencies(config, check=check)
    methods = _verify_methods(config, check=check)
    _bound(path, actual, check=check, category="SELECTION")
    return {"config": config, "path": str(path), "sha256": config_sha256, "host": host,
            "dependencies": dependencies, "methods": methods}


def validate_selection(config_path, config_sha256, source_root):
    """Validate explicit approved inputs statically; never run preparation probes."""
    try:
        return _selection(config_path, config_sha256, source_root)["config"]
    except CurrentHostBindingError:
        raise
    except Exception as exc:
        raise CurrentHostBindingError("SELECTION", "Selection validation failed", cause=exc) from exc


def selection_from_environment():
    path, digest = os.environ.get(CONFIG_ENV), os.environ.get(DIGEST_ENV)
    _require(bool(path) and bool(digest), "SELECTION", "Set both " + CONFIG_ENV + " and " + DIGEST_ENV + " from the independently reviewed execution plan")
    _absolute(path, category="SELECTION")
    _digest(digest, "SELECTION")
    return path, digest


def derive_workspace_binding(config_path, config_sha256, source_root, workspace_root, output, source_before, workspace_inventory):
    selection = _selection(config_path, config_sha256, source_root)
    config = selection["config"]
    _require(config["parent"] is None, "WORKSPACE", "Only an original selection can be derived")
    workspace = _absolute(workspace_root, category="WORKSPACE")
    _require(workspace != Path(source_root), "WORKSPACE", "An isolated workspace must have a distinct root")
    from tools.check_local import inventory, immutable_workspace_inputs, git_metadata
    _require(source_before == workspace_inventory == inventory(workspace) == inventory(Path(source_root)),
             "WORKSPACE", "Complete copied-source inventories are not equal")
    git = git_metadata(workspace)
    _require(git.get("available") and git["local_head"] == config["source"]["commit"] and git["local_tree"] == config["source"]["tree"],
             "WORKSPACE", "Isolated source Git identity differs")
    directory = _inside(output, config["evidence_root"], "WORKSPACE")
    directory.mkdir(mode=0o700, exist_ok=False)
    parent = _describe(config_path)
    before = _write_new(directory / "source-before.json", source_before)
    copied = _write_new(directory / "workspace-inventory.json", workspace_inventory)
    row = {"schema": PREFIX + "workspace" + VERSION, "identity": uuid.uuid4().hex,
           "parent_config": parent, "source_root": str(source_root), "workspace_root": str(workspace),
           "commit": config["source"]["commit"], "tree": config["source"]["tree"],
           "source_inventory": config["source"]["inventory"], "source_before": before, "workspace_inventory": copied,
           "immutable_inventory_sha256": immutable_workspace_inputs(source_before)["sha256"],
           "provider": str(workspace / PROVIDER), "probe": str(workspace / PROBE)}
    binding = _write_new(directory / "workspace-binding.json", row)
    derived = deepcopy(config)
    derived["source"]["root"] = str(workspace)
    derived["contract_source"]["path"] = str(workspace / CONTRACT_PATH)
    derived["parent"] = {"config": parent, "source_root": str(source_root), "workspace_binding": binding}
    selected = _write_new(directory / "selection.json", derived)
    _selection(selected["path"], selected["sha256"], workspace, own_root=False)
    _bound(config_path, {key: parent[key] for key in ("sha256", "size_bytes", "mode")}, category="WORKSPACE")
    return {"config_path": selected["path"], "config_sha256": selected["sha256"],
            "parent_config_sha256": config_sha256, "workspace_binding_path": binding["path"],
            "workspace_binding_sha256": binding["sha256"]}


def _manifest(selection, output, schedule_root):
    config, host = selection["config"], selection["host"]
    output = _absolute(output, category="MANIFEST")
    cohort = _inside(output.parent, config["evidence_root"], "MANIFEST")
    schedule = _absolute(schedule_root, category="MANIFEST")
    _require(schedule == cohort / "unused-native-schedule" and not schedule.exists(), "MANIFEST", "Native schedule must be the unused absent structural path")
    source, deps = Path(config["source"]["root"]), Path(config["dependencies"]["root"])
    files = {str(deps / name): binding for name, binding in selection["dependencies"]["files"].items()}
    for relative in (PROVIDER, PROBE):
        files[str(source / relative)] = file_binding(source / relative, category="SOURCE")
    loader, probe = str(deps / "tools/three_loader.mjs"), str(source / PROBE)
    controls, _ = _read(source / "docs/engineering/static-tray-mapping-c198/CONTROLS.json", 1024 * 1024)
    slots = controls["future_qualification_native_slots"]
    _require(len(slots) == 12, "MANIFEST", "Exactly twelve original structural slots are required")
    rows = []
    for slot in slots:
        stage = schedule / "external-readback" / slot["slot"]
        rows.append({"slot": slot["slot"], "case": slot["case"], "route": slot["route"], "maximum_starts": 1,
                     "stage": str(stage), "result": str(stage / "result.json"),
                     "argv": [config["runtime"]["executable"], *NODE_FLAGS, "--experimental-loader", loader, probe,
                              "--expected-config-sha256", selection["sha256"], "--job", str(stage / "job.json")]})
    return {"schema": PREFIX + "lock" + VERSION, "contract": CONTRACT, "profile": "ontokin.static-tray/0.1.0",
            "schedule_root": str(schedule), "cohort_root": str(cohort), "dependencies_root": str(deps), "scope": SCOPE,
            "limits": LIMITS, "environment": ENVIRONMENT, "files": files,
            "runtime": {**config["runtime"], "files": host["files"], "aliases": host["aliases"]},
            "validator_version": "2.0.0-dev.3.10", "three_version": "0.186.1",
            "validator_entry": str(deps / "validator/package/index.js"), "three_package": str(deps / "indexer-view/three/package.json"),
            "three_entry": str(deps / "indexer-view/three/build/three.webgpu.js"),
            "gltf_loader_entry": str(deps / "indexer-view/three/examples/jsm/loaders/GLTFLoader.js"),
            "module_loader": loader, "probe": probe, "validator_options": VALIDATOR_OPTIONS, "three_options": THREE_OPTIONS,
            "slots": rows, "selection": {"path": selection["path"], "sha256": selection["sha256"]},
            "source": config["source"], "host": config["host"], "methods": config["methods"], "dependencies": config["dependencies"]}


def prepare_case_manifest(output, *, config_path, config_sha256, source_root, schedule_root):
    selection = _selection(config_path, config_sha256, source_root)
    manifest = _manifest(selection, output, schedule_root)
    _require(not Path(output).exists(), "MANIFEST", "Manifest must be a fresh path")
    descriptor = _write_new(output, manifest)
    verify_case_manifest(output, config_path=config_path, config_sha256=config_sha256,
                         source_root=source_root, schedule_root=schedule_root)
    return manifest, descriptor["sha256"]


def verify_case_manifest(path, *, config_path, config_sha256, source_root, schedule_root, check=lambda: None):
    selection = _selection(config_path, config_sha256, source_root, check=check)
    manifest, binding = _read(path, 1024 * 1024, check=check, category="MANIFEST")
    _schema(manifest, "lock", MANIFEST_KEYS, "MANIFEST")
    expected = _manifest(selection, path, schedule_root)
    _require(manifest == expected, "MANIFEST", "Manifest differs from the exact approved source/input/slot bindings")
    _tick(check)
    return manifest, binding["sha256"]


def _job(argv, stage, label, env, selection_path, selection_digest, clock, stage_end, cancel_after_ms, *, post=False):
    _require(type(argv) is list and len(argv) == 10, "LAUNCH", "Exact current-host argv is required")
    _require(argv[-4:] == ["--expected-config-sha256", selection_digest, "--job", str(Path(stage) / "job.json")],
             "LAUNCH", "Job argv or externally approved digest differs")
    _require(label == "synthetic-readback" and env == ENVIRONMENT and cancel_after_ms is None,
             "LAUNCH", "CPU environment, label or undeclared cancellation differs")
    _require(isinstance(clock, supervisor.Clock) and clock.requested_ms == 30000 and clock.cancel_file is None
             and clock.end == clock.started + 30 and stage_end == clock.started + 28,
             "CLOCK", "The original 30,000/28,000-ms clock and deadlines are required")
    check = lambda: clock.check(clock.end if post else stage_end)
    check.deadline = clock.end if post else stage_end
    _tick(check)
    stage = _absolute(stage, category="JOB")
    _require(stage.name in CASES and stage.is_dir(), "JOB", "Only the three original CPU stages are admitted")
    job, binding = _read(stage / "job.json", 32768, check=check, category="JOB")
    _keys(job, "slot case manifest supplemental_manifest_sha256 input_lock_sha256 artifact artifact_sha256 audit audit_sha256 result".split(), "JOB")
    _require(job["slot"] == "CPU-" + stage.name and job["case"] == CASES[stage.name]
             and job["input_lock_sha256"] == "CPU-ONLY-SYNTHETIC-NOT-NATIVE"
             and job["artifact"] == str(stage / "synthetic.glb") and job["audit"] == str(stage / "synthetic-audit.json")
             and job["result"] == str(stage / "probe.json") and Path(job["manifest"]).parent == stage.parent,
             "JOB", "Case, route, input or result path differs")
    actual_manifest = file_binding(job["manifest"], maximum=1024 * 1024, check=check, category="MANIFEST")
    _require(actual_manifest["sha256"] == _digest(job["supplemental_manifest_sha256"], "JOB"),
             "JOB", "Job does not bind the actual manifest bytes")
    manifest, digest = verify_case_manifest(job["manifest"], config_path=selection_path, config_sha256=selection_digest,
                                           source_root=ROOT, schedule_root=stage.parent / "unused-native-schedule", check=check)
    _require(manifest["cohort_root"] == str(stage.parent) and digest == job["supplemental_manifest_sha256"],
             "MANIFEST", "Job manifest digest or cohort root differs")
    _require(argv == manifest["slots"][0]["argv"][:-1] + [str(stage / "job.json")], "LAUNCH", "Executable, flags, loader or probe differs")
    original = {"synthetic.glb", "synthetic-audit.json", "job.json"}
    if not post:
        _require({p.name for p in stage.iterdir()} == original, "JOB", "Checker stage must contain only its three fresh inputs")
    artifacts = {}
    for key, maximum in (("artifact", 8 * 1024 * 1024), ("audit", 4 * 1024 * 1024)):
        artifacts[key] = file_binding(job[key], maximum=maximum, check=check, category="JOB")
        _require(artifacts[key]["sha256"] == _digest(job[key + "_sha256"], "JOB"), "JOB", "Actual CPU input digest differs")
    supervisor.inventory(stage, clock=clock, stage_end=clock.end if post else stage_end)
    _tick(check)
    return {"job": job, "job_binding": binding, "manifest_sha256": digest, "inputs": artifacts,
            "config_sha256": selection_digest, "source": manifest["source"]}


def guarded_run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):
    """One unchanged supervisor call, with bounded pre/postflight and durable evidence."""
    stage = Path(stage)
    ledger = {"schema": PREFIX + "attempt" + VERSION, "expected_argv": argv, "expected_checker_starts": 1,
              "actual_checker_starts": 0, "preflight": None, "postflight": None,
              "process": None, "supervisor_failure": None, "provider_failure": None, "state": "PENDING"}
    directory = None
    result = None
    delegated = None
    failure = None
    callback_failure = None
    try:
        selected_path, selected_digest = selection_from_environment()
        _require(type(argv) is list and len(argv) == 10 and argv[-4:] == ["--expected-config-sha256", selected_digest, "--job", str(stage / "job.json")],
                 "LAUNCH", "Actual argv does not carry the independently selected configuration digest")
        # Read enough authenticated selection to locate durable evidence before
        # full validation, so even a failed preflight has a no-start ledger.
        raw, identity = _read(selected_path, 1024 * 1024, category="SELECTION")
        _require(identity["sha256"] == selected_digest, "SELECTION", "Configuration digest differs before evidence preparation")
        _schema(raw, "config", CONFIG_KEYS)
        _inside(stage.parent, raw["evidence_root"], "EVIDENCE")
        evidence = _inside(stage.parent / "provider-ledgers", raw["evidence_root"], "EVIDENCE")
        _require(evidence.is_dir(), "EVIDENCE", "Setup provider evidence directory is missing")
        directory = evidence / stage.name
        directory.mkdir(mode=0o700, exist_ok=False)
        _write_new(directory / "reserved.json", ledger)
        ledger["preflight"] = _job(argv, stage, label, env, selected_path, selected_digest, clock, stage_end, cancel_after_ms)
        _write_new(directory / "preflight.json", ledger["preflight"])
        def started(record):
            nonlocal callback_failure
            ledger["actual_checker_starts"] += 1
            ledger["started_record"] = deepcopy(record)
            try:
                _write_new(directory / "started.json", {"process": record, "actual_checker_starts": ledger["actual_checker_starts"]})
            except BaseException as exc:
                callback_failure = exc
            if on_started is not None:
                on_started(record)
            if callback_failure is not None:
                raise callback_failure
        try:
            launch = _job(argv, stage, label, env, selected_path, selected_digest, clock, stage_end, cancel_after_ms)
            _require(launch == ledger["preflight"], "JOB", "Input changed after preflight evidence was written")
            _tick(lambda: clock.check(stage_end))
            result = supervisor.run_process(argv, stage=stage, label=label, clock=clock, stage_end=stage_end,
                                            env=env, on_started=started, cancel_after_ms=cancel_after_ms)
            ledger["process"] = result
        except CurrentHostBindingError:
            raise
        except BaseException as exc:
            delegated = exc
            ledger["supervisor_failure"] = _failure(exc)
            ledger["process"] = getattr(exc, "process_record", None)
        # Persist the original receipt before any later verification can fail.
        _write_new(directory / "supervisor-outcome.json", {"process": ledger["process"], "failure": ledger["supervisor_failure"],
                                                         "actual_checker_starts": ledger["actual_checker_starts"]})
        ledger["postflight"] = _job(argv, stage, label, env, selected_path, selected_digest, clock, stage_end, cancel_after_ms, post=True)
        _require(ledger["postflight"] == ledger["preflight"], "JOB", "Inputs changed across the actual checker")
        if callback_failure is not None:
            raise CurrentHostBindingError("EVIDENCE", "Provider start evidence failed", cause=callback_failure,
                                          process_record=ledger["process"], state="UNKNOWN")
        _require(ledger["actual_checker_starts"] == 1, "LAUNCH", "Expected exactly one observed checker start")
        _require(ledger["process"] is not None, "EVIDENCE", "Supervisor returned no actual process receipt")
        ledger["artifacts_after"] = {path.name: file_binding(path, check=lambda: clock.check(), category="EVIDENCE")
                                     for path in sorted(stage.iterdir()) if path.is_file()}
        _tick(lambda: clock.check())
        ledger["state"] = "SUPERVISOR_REFUSAL" if delegated else "COMPLETED"
    except BaseException as exc:
        failure = exc if isinstance(exc, CurrentHostBindingError) else CurrentHostBindingError(
            "CLOCK" if isinstance(exc, supervisor.Stop) else "EVIDENCE", "Provider attempt failed", cause=exc,
            process_record=ledger["process"], state=getattr(exc, "state", "REJECTED"))
        failure.process_record = ledger["process"]
        if delegated:
            failure.supervisor_cause = delegated
        ledger["provider_failure"], ledger["state"] = failure.as_dict(), failure.state
    finally:
        ledger["elapsed_ms"] = clock.elapsed_ms()
        if directory is not None:
            try:
                _write_new(directory / "result.json", ledger)
                if failure is None:
                    _tick(lambda: clock.check())
            except BaseException as exc:
                failure = exc if isinstance(exc, CurrentHostBindingError) and exc.code == "CH-CLOCK" else CurrentHostBindingError(
                    "EVIDENCE", "Provider ledger finalization failed", cause=exc, process_record=ledger["process"], state="UNKNOWN")
                failure.process_record = ledger["process"]
                try:
                    _write_new(directory / "finalization.failed.json", {"error": failure.as_dict(), "attempt": ledger})
                except BaseException as marker:
                    failure.finalization_marker_error = _failure(marker)
    if failure:
        failure.ledger_path = str(directory) if directory else None
        failure.refusal_record.update(actual_checker_starts=ledger["actual_checker_starts"], process=ledger["process"],
                                      authorized_evidence_destination=str(directory) if directory else "unavailable",
                                      evidence_finalized=bool(directory and (directory / "result.json").is_file()), attempt=ledger)
        raise failure from delegated
    if delegated is not None:
        if isinstance(delegated, supervisor.Stop):
            raise delegated
        raise CurrentHostBindingError("EVIDENCE", "Supervisor failed outside its declared Stop interface", cause=delegated,
                                      process_record=ledger["process"], state="UNKNOWN") from delegated
    return result


class _OwnedTemporaryCohort:
    """Explicit cleanup only: interpreter exit cannot erase interrupted evidence."""

    def __init__(self, parent):
        self.name = tempfile.mkdtemp(prefix="current-host-cpu-", dir=parent)
        info = Path(self.name).lstat()
        self.identity = (info.st_dev, info.st_ino)

    def cleanup(self):
        path = _absolute(self.name, category="EVIDENCE")
        info = path.lstat()
        _require((info.st_dev, info.st_ino) == self.identity, "EVIDENCE", "Owned temporary cohort changed identity")
        shutil.rmtree(path)


def _preserve_temporary(cls):
    if cls.temporary is None:
        return None
    root = _absolute(cls.root, category="EVIDENCE")
    supervisor.inventory(root)
    before = {p.relative_to(root).as_posix(): file_binding(p, category="EVIDENCE")
              for p in sorted(root.rglob("*")) if p.is_file()}
    retained = root.parent / (root.name + "-preserved-" + uuid.uuid4().hex)
    shutil.copytree(root, retained, symlinks=True)
    supervisor.inventory(retained)
    copied = {p.relative_to(retained).as_posix(): file_binding(p, category="EVIDENCE")
              for p in sorted(retained.rglob("*")) if p.is_file()}
    after = {p.relative_to(root).as_posix(): file_binding(p, category="EVIDENCE")
             for p in sorted(root.rglob("*")) if p.is_file()}
    _require(before == copied == after, "EVIDENCE", "Temporary cohort preservation is incomplete or changed")
    _write_new(retained / "PRESERVATION.json", {"schema": PREFIX + "preserved-cohort" + VERSION,
               "original_root": str(root), "retained_root": str(retained), "files": copied,
               "reason": "Byte-preserved evidence before explicit owned temporary cleanup"})
    cls.retained_evidence = retained
    cls.temporary.cleanup()
    _write_new(retained / "CLEANUP.json", {"owned_temporary_root": str(root), "removed": not root.exists()})
    return retained


def setup_cpu_cohort(cls):
    """Class lifecycle seam; failed setup self-finalizes before unittest aborts it."""
    cls.temporary = None
    cls.root = None
    record = {"schema": PREFIX + "setup" + VERSION, "passed": False, "checker_starts": 0}
    destination = None
    failure = None
    try:
        selected_path, selected_digest = selection_from_environment()
        raw, actual = _read(selected_path, 1024 * 1024, category="SELECTION")
        _require(actual["sha256"] == selected_digest, "SELECTION", "Selected configuration digest differs")
        _schema(raw, "config", CONFIG_KEYS)
        parent = _absolute(raw["evidence_root"], category="EVIDENCE")
        _require(parent.is_dir() and not parent.is_relative_to(ROOT), "EVIDENCE", "External evidence parent is missing")
        override = os.environ.get("STATIC_TRAY_READBACK_CPU_OUTPUT")
        if override:
            cls.root = _inside(override, parent, "EVIDENCE")
            cls.root.mkdir(mode=0o700, exist_ok=False)
        else:
            cls.temporary = _OwnedTemporaryCohort(parent)
            cls.root = Path(cls.temporary.name)
        destination = cls.root / "setup.json"
        (cls.root / "provider-ledgers").mkdir(mode=0o700)
        _write_new(cls.root / "setup.pending.json", record)
        cls.manifest_path = cls.root / "supplemental-cpu.json"
        cls.manifest, cls.manifest_hash = prepare_case_manifest(cls.manifest_path,
            config_path=selected_path, config_sha256=selected_digest, source_root=ROOT,
            schedule_root=cls.root / "unused-native-schedule")
        record.update(passed=True, config_path=selected_path, config_sha256=selected_digest,
                      manifest_sha256=cls.manifest_hash, source_root=str(ROOT))
    except BaseException as exc:
        failure = exc if isinstance(exc, CurrentHostBindingError) else CurrentHostBindingError("EVIDENCE", "CPU setup failed", cause=exc)
        record["error"] = failure.as_dict()
    finally:
        if destination is not None:
            try:
                _write_new(destination, record)
            except BaseException as exc:
                failure = CurrentHostBindingError("EVIDENCE", "Setup evidence finalization failed", cause=exc, state="UNKNOWN")
    if failure:
        if cls.temporary is not None:
            try:
                retained = _preserve_temporary(cls)
                destination = retained / "setup.json" if retained else destination
            except BaseException as preservation:
                failure.preservation_error = _failure(preservation)
                failure.state = "UNKNOWN"
        failure.ledger_path = str(destination) if destination else None
        failure.refusal_record.update(actual_checker_starts=0, setup=record,
                                      authorized_evidence_destination=str(destination) if destination else "unavailable",
                                      evidence_finalized=bool(destination and destination.is_file()))
        raise failure


def finish_cpu_cohort(cls):
    """Reconcile the three durable attempts; never delete failed evidence."""
    record = {"schema": PREFIX + "cohort" + VERSION, "passed": False, "expected_cases": sorted(CASES)}
    failure = None
    try:
        path, digest = selection_from_environment()
        verify_case_manifest(cls.manifest_path, config_path=path, config_sha256=digest, source_root=ROOT,
                             schedule_root=cls.root / "unused-native-schedule")
        directory = cls.root / "provider-ledgers"
        _require({p.name for p in directory.iterdir()} == set(CASES), "EVIDENCE", "Completed cohort is missing or has extra checker attempts")
        rows = {}
        for label in CASES:
            row, _ = _read(directory / label / "result.json", 8 * 1024 * 1024, category="EVIDENCE")
            _require(row["actual_checker_starts"] == 1 and row["provider_failure"] is None and row["postflight"] == row["preflight"]
                     and row["process"]["handles_closed"] and row["process"]["cleanup"]["passed"]
                     and not (directory / label / "finalization.failed.json").exists(), "EVIDENCE", "A CPU provider attempt failed or is unknown")
            expected_status = 1 if label == "Q01-changed-reference" else 0
            _require(row["process"]["returncode"] == expected_status, "EVIDENCE", "Original CPU case exit differs")
            rows[label] = _describe(directory / label / "result.json")
        record.update(passed=True, attempts=rows, actual_checker_starts=3)
    except BaseException as exc:
        failure = exc if isinstance(exc, CurrentHostBindingError) else CurrentHostBindingError("EVIDENCE", "Cohort finalization failed", cause=exc)
        record["error"] = failure.as_dict()
    finally:
        try:
            _write_new(cls.root / "cohort.json", record)
        finally:
            _preserve_temporary(cls)
    if failure:
        raise failure


# ---------------------------------------------------------------------------
# Version dispatch: C271-P33 gate MI, plan sections 4.6 and 4.8, and section 8 (S8) of
# ontokin.current-host-readback/0.2.0. The 0.1.0 definitions above are unchanged and stay
# reachable through _V010_ENTRY_POINTS. The facade below takes their module-level names:
# a configuration whose bytes match the expected digest and whose schema is
# ontokin.current-host-readback-config/0.2.0 goes to current_host_readback_v02; every
# other call takes the unchanged 0.1.0 code, whose own checks refuse anything that is not
# a 0.1.0 selection. Calls between 0.1.0 entry points pass through the same dispatch,
# which sends a 0.1.0 selection back to the 0.1.0 code. Nothing here starts a process.
# ---------------------------------------------------------------------------

ORDINARY_RUN_REASON = "No approved current-host readback selection: ordinary run, not a qualification"
V02_CONFIG_SCHEMA = PREFIX + "config/0.2.0"
_V010_ENTRY_POINTS = {
    "validate_selection": validate_selection, "derive_workspace_binding": derive_workspace_binding,
    "prepare_case_manifest": prepare_case_manifest, "verify_case_manifest": verify_case_manifest,
    "guarded_run_process": guarded_run_process, "setup_cpu_cohort": setup_cpu_cohort,
    "finish_cpu_cohort": finish_cpu_cohort}


def _v02():
    from . import current_host_readback_v02
    return current_host_readback_v02


def _configured_schema(config_path, config_sha256):
    """The schema of the configuration whose bytes match the expected digest, else None; never raises."""
    try:
        if type(config_sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", config_sha256) is None:
            return None
        config, actual = _read(config_path, 1024 * 1024, category="SELECTION")
    except Exception:
        return None
    if actual["sha256"] != config_sha256 or type(config) is not dict or type(config.get("schema")) is not str:
        return None
    return config["schema"]


def _selects_v02(config_path, config_sha256):
    return _configured_schema(config_path, config_sha256) == V02_CONFIG_SCHEMA


def _environment_selects_v02():
    path, digest = os.environ.get(CONFIG_ENV), os.environ.get(DIGEST_ENV)
    return bool(path) and bool(digest) and _selects_v02(path, digest)


def _ordinary_run(cls):
    """S8: neither selection variable is set; the readback class fails visibly at setup and is never skipped."""
    cls.temporary = None
    cls.root = None
    record = {"schema": PREFIX + "setup" + VERSION, "passed": False, "checker_starts": 0, "run_kind": "ordinary"}
    failure = CurrentHostBindingError("SELECTION", ORDINARY_RUN_REASON)
    record["error"] = failure.as_dict()
    failure.ledger_path = None
    failure.refusal_record.update(actual_checker_starts=0, setup=record, run_kind="ordinary",
                                  authorized_evidence_destination="unavailable", evidence_finalized=False)
    raise failure


def git_binding_from_selection(config_path, config_sha256):
    """The Git binding of a digest-checked selection, which a qualifying run binds before its first Git start.

    Returns {"path", "sha256"} from the HOST document of a 0.2.0 selection, and None for a 0.1.0
    selection, whose Git stays the one PATH resolves. Any other configuration refuses. It reads
    files only and starts no Git and no other process (plan section 4.5).
    """
    _digest(config_sha256, "SELECTION")
    config, actual = _read(_absolute(config_path, category="SELECTION"), 1024 * 1024, category="SELECTION")
    _require(actual["sha256"] == config_sha256, "SELECTION", "Configuration differs from the independently supplied expected digest")
    if type(config) is dict and config.get("schema") == V02_CONFIG_SCHEMA:
        return _v02().git_binding_from_selection(config_path, config_sha256)
    _schema(config, "config", CONFIG_KEYS)
    _require(config["contract"] == CONTRACT, "SCHEMA", "Unsupported current-host contract")
    return None


def validate_selection(config_path, config_sha256, source_root):
    """Facade: a 0.2.0 selection goes to the 0.2.0 provider, every other one to the 0.1.0 code."""
    if _selects_v02(config_path, config_sha256):
        return _v02().validate_selection(config_path, config_sha256, source_root)
    return _V010_ENTRY_POINTS["validate_selection"](config_path, config_sha256, source_root)


def derive_workspace_binding(config_path, config_sha256, source_root, workspace_root, output, source_before, workspace_inventory):
    """Facade of derive_workspace_binding, dispatched by the selected configuration's schema."""
    implementation = (_v02().derive_workspace_binding if _selects_v02(config_path, config_sha256)
                      else _V010_ENTRY_POINTS["derive_workspace_binding"])
    return implementation(config_path, config_sha256, source_root, workspace_root, output, source_before, workspace_inventory)


def prepare_case_manifest(output, *, config_path, config_sha256, source_root, schedule_root):
    """Facade of prepare_case_manifest, dispatched by the selected configuration's schema."""
    implementation = (_v02().prepare_case_manifest if _selects_v02(config_path, config_sha256)
                      else _V010_ENTRY_POINTS["prepare_case_manifest"])
    return implementation(output, config_path=config_path, config_sha256=config_sha256, source_root=source_root,
                          schedule_root=schedule_root)


def verify_case_manifest(path, *, config_path, config_sha256, source_root, schedule_root, check=lambda: None):
    """Facade of verify_case_manifest, dispatched by the selected configuration's schema."""
    implementation = (_v02().verify_case_manifest if _selects_v02(config_path, config_sha256)
                      else _V010_ENTRY_POINTS["verify_case_manifest"])
    return implementation(path, config_path=config_path, config_sha256=config_sha256, source_root=source_root,
                          schedule_root=schedule_root, check=check)


# Decision D-20 (independent review finding I-01): the version that a class's setup selects stays
# bound until that class's cohort accounting has run. A configuration that changes in between is
# then reconciled by the provider that set the cohort up, which refuses and records the change, and
# never by the other version's code. Outside a cohort every call is dispatched by the selection.
DISPATCH_VERSION_ATTRIBUTE = "readback_dispatch_version"
_COHORT_BINDING = {"version": None}


def _environment_version():
    return "0.2.0" if _environment_selects_v02() else "0.1.0"


def _bound_version():
    return _COHORT_BINDING["version"] or _environment_version()


def _end_binding(cls):
    _COHORT_BINDING["version"] = None
    if DISPATCH_VERSION_ATTRIBUTE in vars(cls):
        delattr(cls, DISPATCH_VERSION_ATTRIBUTE)


def guarded_run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):
    """Facade of the process adapter: the version bound by the cohort's setup, else the environment's selection."""
    implementation = (_v02().guarded_run_process if _bound_version() == "0.2.0"
                      else _V010_ENTRY_POINTS["guarded_run_process"])
    return implementation(argv, stage=stage, label=label, clock=clock, stage_end=stage_end, env=env,
                          on_started=on_started, cancel_after_ms=cancel_after_ms)


def setup_cpu_cohort(cls):
    """Facade of the class setup: an ordinary run fails visibly (S8); a selection is dispatched by its schema.

    The version selected here stays bound to the class until finish_cpu_cohort has run (D-20).
    """
    if not os.environ.get(CONFIG_ENV) and not os.environ.get(DIGEST_ENV):
        _ordinary_run(cls)
    version = _environment_version()
    implementation = _v02().setup_cpu_cohort if version == "0.2.0" else _V010_ENTRY_POINTS["setup_cpu_cohort"]
    setattr(cls, DISPATCH_VERSION_ATTRIBUTE, version)
    _COHORT_BINDING["version"] = version
    try:
        return implementation(cls)
    except BaseException:
        # unittest runs no class teardown after a failed class setup, so the binding ends here.
        _end_binding(cls)
        raise


def finish_cpu_cohort(cls):
    """Facade of the cohort accounting: the version its setup bound, else the environment's selection (D-20)."""
    version = vars(cls).get(DISPATCH_VERSION_ATTRIBUTE) or _bound_version()
    implementation = _v02().finish_cpu_cohort if version == "0.2.0" else _V010_ENTRY_POINTS["finish_cpu_cohort"]
    try:
        return implementation(cls)
    finally:
        _end_binding(cls)
