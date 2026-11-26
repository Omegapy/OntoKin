"""Explicit current-host CPU readback under ontokin.current-host-readback/0.2.0 (darwin-arm64-v1).

This is the 0.1.0 provider (current_host_readback_v01.py) adapted to the adopted macOS arm64
contract, docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md, and
written to its design revision 4 (P33-AMENDMENT-001). It keeps every 0.1.0 rule that the
contract keeps and changes only what the contract changes:

* every provider document schema is versioned /0.2.0, and each entry point refuses the
  documents of 0.1.0 (contract section 1);
* the host binding consumes HOST/0.2.0 through the observer's exported helpers: platform,
  translation, boot identity, OS identity with the cryptex copy, the Python installation
  inventory compared as exact sets, the runtime directory with NODE-SOURCE.json, the Git
  binding and the environment predicate (S2, S7, S10); there is no ELF, ldd or alias logic;
* the source check's Git reads run the selection's Git, bound through
  tools.check_local.bind_git before the first Git start (S9);
* the boot identity, OS build and cryptex version are read before the cohort, and before and
  after each start (MC09);
* the process adapter delegates once to supervisor_darwin_v01.run_process (S4);
* results and refusals carry the labels of contract section 10 and the design revision.

An expected configuration digest is an input supplied by the independently reviewed execution
plan. This module never manufactures approval from a file's observed digest. No validation
function starts Node; the only starts are the bound Git reads of the source check and the
single delegated supervisor call per checker.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid

from . import current_host_observation_v02 as observation
from . import supervisor, supervisor_darwin_v01
from .format_check import ENVIRONMENT, LIMITS, NODE_FLAGS, THREE_OPTIONS, VALIDATOR_OPTIONS

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "ontokin.current-host-readback/0.2.0"
PROFILE = "darwin-arm64-v1"
EXECUTOR = "macos-arm64-local"
# Decision D-03 under P33-AMENDMENT-001: every document this module writes names both.
DESIGN_REVISION = 4
AMENDMENTS = ("P33-AMENDMENT-001",)
PREFIX = "ontokin.current-host-readback-"
VERSION = "/0.2.0"
CONFIG_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG"
DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
ORDINARY_RUN_REASON = "No approved current-host readback selection: ordinary run, not a qualification"
PROVIDER = "prototypes/static_tray_v01/current_host_readback_v02.py"
PROBE = "prototypes/static_tray_v01/current_host_readback_v02.mjs"
CONTRACT_PATH = "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md"
# The amendment's adoption record, bound by path, SHA-256, size and mode through the configuration.
AMENDMENT_ADOPTION_PATH = "docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json"
BASELINE_MAP = "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip"
EXTERNAL_INPUTS = "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json"
EXTERNAL_SHA256 = "21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5"
ARCHIVE_SHA256 = "b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9"
NODE_VERSION = "v24.22.1"
NODE_ARCHIVE = "node-v24.22.1-darwin-arm64.tar.gz"
NODE_ARCHIVE_SHA256 = "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"
# The Node executable's own pin is frozen at preparation and comes from HOST, never from here.
MACOS_LOCK = "tools/native-reader-verification-macos-arm64-cp312.lock"
# The /0.2.0 source inventory is the observer's: one definition, so HOST and the provider agree.
SOURCE_TREES = observation.SOURCE_TREES
SOURCE_OPTIONAL = observation.SOURCE_OPTIONAL
SOURCE_FILES = observation.SOURCE_FILES
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
CONFIG_KEYS = "schema contract contract_source amendment_adoption source host dependencies runtime methods evidence_root parent".split()
MANIFEST_KEYS = "schema contract design_revision amendments labels profile schedule_root cohort_root dependencies_root scope limits environment files runtime validator_version three_version validator_entry three_package three_entry gltf_loader_entry module_loader probe validator_options three_options slots selection source host methods dependencies".split()
WORKSPACE_KEYS = "schema contract design_revision amendments identity parent_config source_root workspace_root commit tree source_inventory source_before workspace_inventory immutable_inventory_sha256 provider probe".split()
# HOST/0.2.0 as the observer writes it at design revision 4 (interfaces/W3-OBSERVER.md section 3; D-12, D-13).
HOST_KEYS = "schema contract design_revision amendments profile executor observed_at_utc plan observer platform os environment python runtime git dependencies source inspections starts labels claims".split()
HOST_PLATFORM_KEYS = ("system", "release", "version", "machine", "proc_translated", "boot_session_uuid")
HOST_PYTHON_KEYS = ("launcher", "venv", "framework", "interpreter", "selection", "inventory", "inventory_sha256", "packages", "records", "lock")
HOST_RUNTIME_KEYS = ("directory", "executable", "version", "binding", "archive", "node_source", "layout", "macho", "install")
HOST_LABEL_KEYS = ("executor", "contract", "design_revision", "amendments", "profile", "os", "node",
                   "python_inventory_sha256", "git", "run_kind", "boundary")
INSPECTION_KEYS = ("schema", "contract", "design_revision", "amendments", "argv", "environment", "timeout_ms",
                   "started_at_utc", "finished_at_utc", "process", "stdout", "stderr")
SCOPE = "Three original synthetic CPU cases only; twelve native slots are structural, never execution authority"
UNVERIFIED_LABEL = "unavailable: no HOST document has been verified in this process"


class CurrentHostBindingError(RuntimeError):
    """Provider refusal, deliberately unrelated to supervisor.Stop."""

    def __init__(self, category, reason, *, cause=None, process_record=None, state="REJECTED"):
        self.code, self.reason, self.state = "CH-" + category, reason, state
        self.cause = _failure(cause) if cause is not None else None
        self.process_record = process_record
        self.refusal_record = {"schema": PREFIX + "refusal" + VERSION, **_identity(), "labels": _labels_now(),
                               "passed": False,
                               "error": {"code": self.code, "reason": reason, "state": state, "cause": self.cause},
                               "authorized_evidence_destination": "unavailable", "evidence_finalized": False}
        super().__init__(reason)

    def as_dict(self):
        return {"code": self.code, "reason": self.reason, "state": self.state, "cause": self.cause}


def _failure(exc):
    if hasattr(exc, "as_dict"):
        return exc.as_dict()
    return {"type": type(exc).__name__, "reason": str(exc)}


def _identity():
    """The contract, design revision and adopted amendments that every 0.2.0 document names (D-03)."""
    return {"contract": CONTRACT, "design_revision": DESIGN_REVISION, "amendments": list(AMENDMENTS)}


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


def _observed(category, function, *args, check=None, **kwargs):
    """Call one of the observer's exported helpers; its refusal becomes a provider refusal of ``category``."""
    if check is not None:
        kwargs["check"] = lambda: _tick(check)
    try:
        return function(*args, **kwargs)
    except observation.ObservationError as exc:
        raise CurrentHostBindingError(category, exc.reason, cause=exc) from exc


def _binding_shape(binding, *, descriptor=False):
    _keys(binding, ["sha256", "size_bytes", "mode"] + (["path"] if descriptor else []))
    _digest(binding["sha256"])
    _require(type(binding["size_bytes"]) is int and binding["size_bytes"] >= 0,
             "SCHEMA", "Invalid file size")
    _require(type(binding["mode"]) is str and re.fullmatch(r"0o[0-7]{3,4}", binding["mode"]) is not None,
             "SCHEMA", "Invalid file mode")
    if descriptor:
        _absolute(binding["path"])


def _plain(binding):
    return {key: binding[key] for key in ("sha256", "size_bytes", "mode")}


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


# ---------------------------------------------------------------------------
# Labels and boundary (contract section 10 with P33-AMENDMENT-001 row 13; D-03, D-04)
# ---------------------------------------------------------------------------

# The last HOST document this process verified completely; it supplies the labels of later refusals.
_VERIFIED = {"host": None}


def _boundary_functions():
    """The host, supervisor and selection boundaries whose substitution makes a result mocked."""
    return {"run_process": supervisor_darwin_v01.run_process, "uname": os.uname,
            "proc_translated": observation.read_proc_translated,
            "boot_session_uuid": observation.read_boot_session_uuid,
            "os_identity": observation.read_os_identity, "process_image": observation.read_process_image,
            "python_inventory": observation.python_inventory, "check_runtime": observation.check_runtime,
            "check_git_binding": observation.check_git_binding, "host_state": globals().get("host_state"),
            "selection": globals().get("_selection"), "verify_host": globals().get("_verify_host")}


def _boundary():
    """``real`` only while every boundary is the module's own object; any substitute labels a result ``mocked``."""
    real = globals().get("_REAL_BOUNDARY")
    current = _boundary_functions()
    return "real" if real is not None and all(current[name] is real[name] for name in real) else "mocked"


def _os_label(identity):
    system, cryptex = identity["system_version"], identity["cryptex"]
    return {"product_version": system["product_version"], "product_build_version": system["product_build_version"],
            "product_version_extra": system["product_version_extra"],
            "cryptex": ({"state": "absent"} if cryptex["state"] == "absent" else
                        {"state": "present", "product_version": cryptex["product_version"],
                         "product_build_version": cryptex["product_build_version"],
                         "product_version_extra": cryptex["product_version_extra"]})}


def _labels(host=None, *, run_kind="qualifying"):
    """The labels of contract section 10, from a verified HOST; unobserved ones say so."""
    labels = {"executor": EXECUTOR, **_identity(), "profile": PROFILE, "run_kind": run_kind, "boundary": _boundary()}
    if host is None:
        labels.update(os=UNVERIFIED_LABEL, node=UNVERIFIED_LABEL, python_inventory_sha256=UNVERIFIED_LABEL,
                      git=UNVERIFIED_LABEL)
    else:
        labels.update(os=host["labels"]["os"], node=host["labels"]["node"],
                      python_inventory_sha256=host["python"]["inventory_sha256"],
                      git={"path": host["git"]["path"], "sha256": host["git"]["sha256"]})
    return labels


def _labels_now(run_kind="qualifying"):
    try:
        return _labels(_VERIFIED["host"], run_kind=run_kind)
    except Exception as exc:  # a refusal must never fail to describe itself
        return {"executor": EXECUTOR, **_identity(), "run_kind": run_kind, "unavailable": _failure(exc)}


# ---------------------------------------------------------------------------
# Source (contract section 7; MC19)
# ---------------------------------------------------------------------------

def _source_paths(root, *, check=lambda: None):
    """The /0.2.0 source path set: the observer's definition, so HOST and the provider agree."""
    return _observed("SOURCE", observation.source_paths, str(root), check=check)


def source_inventory(root, *, check=lambda: None):
    root = _absolute(root, category="SOURCE")
    return {"schema": PREFIX + "source" + VERSION,
            "files": {relative: file_binding(root / relative, check=check, category="SOURCE")
                      for relative in _source_paths(root, check=check)}}


def _bind_git(git):
    """S9: bind the selection's Git through the driver's binding; every later Git start runs it."""
    _require(type(git) is dict and set(git) == {"path", "sha256"}, "SOURCE",
             "Source reads require the selection's bound Git executable")
    from tools import check_local
    try:
        record = check_local.bind_git(git["path"], git["sha256"])
        executable = check_local.git_executable()
    except (ValueError, OSError) as exc:
        raise CurrentHostBindingError("SOURCE", "The selection's Git executable cannot be bound", cause=exc) from exc
    _require(record == {**git, "bound": True, "source": "selection"} and executable == git["path"], "SOURCE",
             "The bound Git executable is not the selection's")
    return record


def _verify_source(source, *, git, derived=False, own_root=True, check=lambda: None):
    _keys(source, ("root", "commit", "tree", "inventory"))
    root = _absolute(source["root"], category="SOURCE")
    _require(not own_root or root == ROOT, "SOURCE", "Provider belongs to another source checkout")
    for key in ("commit", "tree"):
        _require(type(source[key]) is str and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", source[key]) is not None,
                 "SOURCE", "Invalid source Git identity")
    # S9: the selection's Git is bound before the source reads; an unbound Git refuses here.
    _bind_git(git)
    expected = _document(source["inventory"], 16 * 1024 * 1024, check=check, category="SOURCE")
    _schema(expected, "source", ("schema", "files"))
    _require(type(expected["files"]) is dict and set(expected["files"]) == set(_source_paths(root, check=check)),
             "SOURCE", "Complete CPU source inventory differs")
    for relative, binding in expected["files"].items():
        _relative(relative)
        _bound(root / relative, binding, check=check, category="SOURCE")
    # The driver owns its broader immutable copied-input definition. Do not
    # introduce a second set of generated exceptions here.
    from tools.check_local import git_read, immutable_workspace_inputs
    def git_call(*args):
        _tick(check)
        remaining = getattr(check, "deadline", float("inf")) - time.monotonic()
        _require(remaining > 0, "CLOCK", "No remaining allowance for source identity inspection")
        try:
            result = git_read(root, *args, timeout=min(5, remaining))
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            _tick(check)
            raise CurrentHostBindingError("SOURCE", "Bounded source Git inspection failed", cause=exc) from exc
        _tick(check)
        return result
    _require(git_call("rev-parse", "--show-toplevel") == str(root)
             and git_call("rev-parse", "--verify", "HEAD^{commit}") == source["commit"]
             and git_call("rev-parse", "--verify", source["commit"] + "^{tree}") == source["tree"],
             "SOURCE", "Source commit/tree differs or is unavailable")
    for line in git_call("status", "--porcelain=v1", "--untracked-files=no").splitlines():
        name = line[3:]
        allowed = derived and not immutable_workspace_inputs({"files": [{"path": name}]})["files"]
        _require(allowed and " -> " not in name and not name.startswith('"'), "SOURCE", "Dirty source: " + line)
    untracked = git_call("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    for name in filter(None, untracked):
        allowed = derived and not immutable_workspace_inputs({"files": [{"path": name}]})["files"]
        _require(allowed, "SOURCE", "Untracked source input: " + name)
    _tick(check)
    return expected


# ---------------------------------------------------------------------------
# HOST/0.2.0 (contract sections 3, 4 and 7; S1, S2, S7, S9, S10)
# ---------------------------------------------------------------------------

def _host_document(config, *, check=lambda: None):
    host = _document(config["host"], 8 * 1024 * 1024, check=check, category="HOST")
    _schema(host, "host", HOST_KEYS)
    _require(host["contract"] == CONTRACT and host["design_revision"] == DESIGN_REVISION
             and host["amendments"] == list(AMENDMENTS) and host["profile"] == PROFILE and host["executor"] == EXECUTOR,
             "HOST", "HOST names another contract, design revision, amendment set, profile or executor")
    return host


def host_state(*, check=lambda: None):
    """Platform, translation, boot identity and OS identity with the cryptex copy, as read now (S7, MC09)."""
    info = os.uname()
    return {"platform": {"system": info.sysname, "release": info.release, "version": info.version,
                         "machine": info.machine,
                         "proc_translated": _observed("HOST", observation.read_proc_translated),
                         "boot_session_uuid": _observed("HOST", observation.read_boot_session_uuid)},
            "os": _observed("HOST", observation.read_os_identity, check=check)}


def _check_state(expected, state, stage):
    """MC09: the boot, OS build and cryptex version must equal HOST's; a change fails the attempt."""
    actual = state["platform"]
    _require(actual["system"] == "Darwin" and actual["machine"] == "arm64" and actual["proc_translated"] == 0,
             "HOST", "Not native Darwin arm64 at " + stage)
    _require(actual == expected["platform"], "HOST",
             "Boot identity, kernel release or translation differs from HOST at " + stage)
    _require(state["os"] == expected["os"], "HOST",
             "OS build, cryptex version or cryptex link differs from HOST at " + stage)
    return {"stage": stage, "boot_session_uuid": actual["boot_session_uuid"], "os": _os_label(state["os"])}


def _check_environment_record(host):
    """S10: HOST's environment record against the declared environment, through the observer's predicate."""
    environment = host["environment"]
    _keys(environment, ("declared", "cf_user_text_encoding"), "HOST")
    recorded, declared = environment["cf_user_text_encoding"], environment["declared"]
    _require(recorded is None or (type(recorded) is str and recorded != ""), "HOST",
             "HOST's __CF_USER_TEXT_ENCODING record is malformed")
    _require(type(declared) is dict and observation.CF_NAME not in declared, "HOST",
             "HOST's declared environment is malformed or names __CF_USER_TEXT_ENCODING")
    # M0's process environment as HOST records it: the declared map, plus the variable when CoreFoundation added it.
    observed = {**declared, **({observation.CF_NAME: recorded} if recorded is not None else {})}
    _require(observation.environment_admitted(observed, ENVIRONMENT, recorded), "HOST",
             "HOST's environment is not exactly the declared environment, optionally plus __CF_USER_TEXT_ENCODING")
    return recorded


def _check_python(host, *, check=lambda: None):
    """S2: this process is the bound interpreter, and both installation trees equal the frozen inventory."""
    python = host["python"]
    _keys(python, HOST_PYTHON_KEYS, "HOST")
    interpreter = python["interpreter"]
    _require(type(interpreter) is dict and interpreter.get("implementation") == sys.implementation.name
             and interpreter.get("version") == platform.python_version() and interpreter.get("build_string") == sys.version,
             "HOST", "The unit process is not the bound CPython build")
    _require(type(python["venv"]) is str and sys.executable == python["launcher"] == python["venv"] + "/bin/python",
             "HOST", "The unit process does not run the bound venv launcher")
    _require(_observed("HOST", observation.read_process_image) == interpreter.get("process_image"), "HOST",
             "The unit process image differs from HOST")
    _binding_shape(python["inventory"], descriptor=True)
    _require(_digest(python["inventory_sha256"], "HOST") == python["inventory"]["sha256"], "HOST",
             "HOST's inventory digest differs from its frozen inventory")
    frozen = _document(python["inventory"], 32 * 1024 * 1024, check=check, category="HOST")
    started = time.monotonic()
    actual = _observed("HOST", observation.python_inventory, python["venv"], python["framework"], check=check)
    elapsed_ms = (time.monotonic() - started) * 1000
    differences = observation.compare_inventory(frozen, actual)
    _require(not differences and observation.python_inventory_digest(actual) == python["inventory_sha256"], "HOST",
             "The Python installation trees differ from the frozen inventory, compared as exact sets: "
             + json.dumps(differences[:8], sort_keys=True))
    raw, lock = _read_bytes(ROOT / MACOS_LOCK, 65536, check=check, category="HOST")
    pins = _observed("HOST", observation.read_lock_pins, raw)
    _binding_shape(python["lock"], descriptor=True)
    _require(python["packages"] == pins and _plain(python["lock"]) == lock, "HOST",
             "The macOS lock or its seven pins differ from HOST")
    return {"inventory_sha256": python["inventory_sha256"], "elapsed_ms": elapsed_ms}


def _check_runtime(host, node, *, check=lambda: None):
    """S1, S6 and MC35: the runtime directory, executable pin, Mach-O and NODE-SOURCE.json, again."""
    runtime = host["runtime"]
    _keys(runtime, HOST_RUNTIME_KEYS, "HOST")
    _require(runtime["version"] == NODE_VERSION and runtime["executable"] == str(node)
             and type(runtime["directory"]) is str and runtime["directory"] + "/bin/node" == str(node),
             "RUNTIME", "The selected Node build differs")
    _binding_shape(runtime["archive"], descriptor=True)
    _require(runtime["archive"]["sha256"] == NODE_ARCHIVE_SHA256 and Path(runtime["archive"]["path"]).name == NODE_ARCHIVE,
             "RUNTIME", "The retained Node archive differs from the adopted pin")
    _binding_shape(runtime["binding"])
    layout, source, install = runtime["layout"], runtime["node_source"], runtime["install"]
    _require(type(layout) is dict and type(source) is dict and type(install) is dict, "HOST", "HOST runtime is malformed")
    plan = {"source": {"root": host["source"]["root"]},
            "runtime": {"directory": runtime["directory"], "version": NODE_VERSION,
                        "root_mode": layout.get("root_mode"), "bin_mode": layout.get("bin_mode"),
                        "executable": runtime["binding"], "node_source": _plain(source), "archive": runtime["archive"],
                        "install": {"plan": install.get("plan"), "result": install.get("result")}}}
    actual = _observed("RUNTIME", observation.check_runtime, plan, check=check)
    actual.pop("references", None)
    _require(actual == runtime, "RUNTIME",
             "The runtime directory, executable, NODE-SOURCE.json or installation receipt differs from HOST")
    return runtime


def _check_git(host, *, check=lambda: None):
    """S9: the Git implementation of source reads, by bytes; never the /usr/bin/git dispatcher."""
    git = host["git"]
    _keys(git, ("path", "sha256", "size_bytes", "mode", "version"), "HOST")
    _require(type(git["version"]) is str and git["version"].isascii()
             and observation.GIT_VERSION_LINE.fullmatch((git["version"] + "\n").encode("ascii")) is not None,
             "HOST", "HOST's Git version is not one version line")
    expected = {key: git[key] for key in ("path", "sha256", "size_bytes", "mode")}
    actual = _observed("HOST", observation.check_git_binding, expected, check=check)
    _require(actual == expected, "HOST", "The Git implementation differs from HOST")
    return {"path": git["path"], "sha256": git["sha256"]}


def _host_git(config, *, check=lambda: None):
    """HOST's Git binding for a digest-checked configuration; reads files only and starts no Git."""
    host = _host_document(config, check=check)
    binding = _check_git(host, check=check)
    _require(type(host["labels"]) is dict and host["labels"].get("git") == binding, "HOST",
             "HOST's Git label differs from its binding")
    return binding


def _utc_time(value):
    _require(type(value) is str, "HOST", "Invalid timestamp")
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CurrentHostBindingError("HOST", "Invalid timestamp", cause=exc) from exc
    _require(moment.tzinfo is not None, "HOST", "Timestamp has no zone")
    return moment


def _verify_inspection(descriptor, argv, environment, stdout, *, check=lambda: None):
    receipt = _document(descriptor, 8 * 1024 * 1024, check=check, category="HOST")
    _schema(receipt, "inspection", INSPECTION_KEYS)
    _require({key: receipt[key] for key in ("contract", "design_revision", "amendments")} == _identity(), "HOST",
             "Inspection receipt names another contract, design revision or amendment set")
    _require(receipt["argv"] == argv and receipt["environment"] == environment and receipt["timeout_ms"] == 5000,
             "HOST", "Inspection command, environment or allowance differs")
    process = receipt["process"]
    cleanup = process.get("cleanup") if type(process) is dict else None
    cleanup = cleanup if type(cleanup) is dict else {}
    _require(type(process) is dict and process.get("argv") == argv and process.get("environment") == environment
             and type(process.get("pid")) is int and process["pid"] > 0 and process.get("process_group") == process["pid"]
             and process.get("returncode") == 0 and process.get("handles_closed") is True
             and cleanup.get("passed") is True and cleanup.get("process_group_absent") is True
             and cleanup.get("reaped") is True and not process.get("error"),
             "HOST", "Inspection did not retain a successful bounded actual process receipt")
    _require(type(process.get("start_monotonic")) in (int, float) and type(process.get("end_monotonic")) in (int, float)
             and 0 <= process["end_monotonic"] - process["start_monotonic"] <= 5,
             "HOST", "Inspection exceeded its five-second allowance")
    start, finish = _utc_time(receipt["started_at_utc"]), _utc_time(receipt["finished_at_utc"])
    _require(start <= finish <= datetime.now(timezone.utc), "HOST", "Invalid inspection timestamps")
    _require(receipt["stdout"] == stdout and receipt["stderr"] == "", "HOST", "Observed inspection output differs")
    return receipt


def _check_inspections(host, node, git, *, check=lambda: None):
    """M0's Git --version and M1's Node --version receipts; the ldd receipt of 0.1.0 has no analogue."""
    inspections = host["inspections"]
    _keys(inspections, ("git_version", "node_version"), "HOST")
    version = _verify_inspection(inspections["node_version"], [str(node), "--version"], ENVIRONMENT,
                                 NODE_VERSION + "\n", check=check)
    tool = _verify_inspection(inspections["git_version"], [git["path"], "--version"], dict(observation.GIT_ENVIRONMENT),
                              host["git"]["version"] + "\n", check=check)
    observed = _utc_time(host["observed_at_utc"])
    _require(observed <= datetime.now(timezone.utc)
             and all(_utc_time(row["finished_at_utc"]) <= observed for row in (version, tool)),
             "HOST", "Host observation does not follow its fresh inspection receipts")


def _check_host_labels(host):
    labels, runtime = host["labels"], host["runtime"]
    _keys(labels, HOST_LABEL_KEYS, "HOST")
    signature = runtime["node_source"].get("content", {}).get("signature_check", {}).get("status") \
        if type(runtime["node_source"].get("content")) is dict else None
    expected = {"executor": EXECUTOR, **_identity(), "profile": PROFILE, "os": _os_label(host["os"]),
                "node": {"archive": NODE_ARCHIVE, "archive_sha256": NODE_ARCHIVE_SHA256,
                         "executable": _plain(runtime["binding"]), "signature_check": signature},
                "python_inventory_sha256": host["python"]["inventory_sha256"],
                "git": {"path": host["git"]["path"], "sha256": host["git"]["sha256"]},
                "run_kind": "host-observation", "boundary": "real"}
    _require(labels == expected, "HOST",
             "HOST's labels differ from its bindings, or HOST was observed through a mocked boundary")


def _verify_host(config, *, check=lambda: None):
    _keys(config["runtime"], ("executable", "version"))
    _require(config["runtime"]["version"] == NODE_VERSION, "RUNTIME", "Only Node v24.22.1 is admitted")
    node = _absolute(config["runtime"]["executable"], category="RUNTIME")
    host = _host_document(config, check=check)
    _keys(host["platform"], HOST_PLATFORM_KEYS, "HOST")
    _check_state(host, host_state(check=check), "the host check")
    _check_environment_record(host)
    _check_python(host, check=check)
    _check_runtime(host, node, check=check)
    git = _check_git(host, check=check)
    _check_inspections(host, node, git, check=check)
    _check_host_labels(host)
    _require(host["starts"] == {"node": 1, "other": 1} and host["claims"] == dict(observation.CLAIMS), "HOST",
             "HOST's start counts or stated claims differ")
    _VERIFIED["host"] = host
    return host


def _cross_bindings(config, host, source_inventory_document):
    """HOST observed the selected source, observer and reader tree."""
    source, original_root = config["source"], (config["parent"]["source_root"] if config["parent"] is not None
                                               else config["source"]["root"])
    recorded = host["source"]
    _keys(recorded, ("root", "commit", "tree", "tree_check", "inventory", "head"), "HOST")
    _require(recorded["root"] == original_root and recorded["commit"] == source["commit"]
             and recorded["tree"] == source["tree"] and recorded["inventory"] == source["inventory"], "HOST",
             "HOST's source binding differs from the selected source")
    observer = host["observer"]
    _binding_shape(observer, descriptor=True)
    _require(_plain(observer) == source_inventory_document["files"].get(observation.ENTRY_POINT), "HOST",
             "HOST was not written by the bound source's observer")
    dependencies = host["dependencies"]
    _keys(dependencies, ("root", "inventory", "archive", "files", "install"), "HOST")
    _require(dependencies["root"] == config["dependencies"]["root"]
             and dependencies["inventory"] == config["dependencies"]["inventory"] and dependencies["files"] == 24,
             "HOST", "HOST's reader tree differs from the selected dependencies")


# ---------------------------------------------------------------------------
# Dependencies and methods (unchanged rules at /0.2.0; MC18)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Selection and workspace derivation
# ---------------------------------------------------------------------------

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
    _schema(binding, "workspace", WORKSPACE_KEYS)
    _require(type(binding["identity"]) is str and re.fullmatch(r"[0-9a-f]{32}", binding["identity"]) is not None,
             "WORKSPACE", "Missing fresh workspace identity")
    _require({key: binding[key] for key in ("contract", "design_revision", "amendments")} == _identity(),
             "WORKSPACE", "Workspace binding names another contract or design revision")
    expected = deepcopy(original)
    expected["source"]["root"] = config["source"]["root"]
    expected["contract_source"]["path"] = str(Path(config["source"]["root"]) / CONTRACT_PATH)
    expected["amendment_adoption"]["path"] = str(Path(config["source"]["root"]) / AMENDMENT_ADOPTION_PATH)
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
    _binding_shape(config["amendment_adoption"], descriptor=True)
    _require(config["amendment_adoption"]["path"] == str(root / AMENDMENT_ADOPTION_PATH), "SOURCE",
             "Amendment adoption record belongs to another checkout")
    _bound(root / AMENDMENT_ADOPTION_PATH, _plain(config["amendment_adoption"]), check=check, category="SOURCE")
    evidence = _absolute(config["evidence_root"], category="EVIDENCE")
    _require(evidence.is_dir() and not evidence.is_relative_to(root), "EVIDENCE", "An external predeclared evidence parent is required")
    _verify_parent(config, check=check)
    git = _host_git(config, check=check)
    source = _verify_source(config["source"], git=git, derived=config["parent"] is not None, own_root=own_root, check=check)
    host = _verify_host(config, check=check)
    _cross_bindings(config, host, source)
    dependencies = _verify_dependencies(config, check=check)
    methods = _verify_methods(config, check=check)
    _bound(path, actual, check=check, category="SELECTION")
    return {"config": config, "path": str(path), "sha256": config_sha256, "host": host,
            "dependencies": dependencies, "methods": methods, "labels": _labels(host)}


def validate_selection(config_path, config_sha256, source_root):
    """Validate explicit approved inputs statically; never run preparation probes."""
    try:
        return _selection(config_path, config_sha256, source_root)["config"]
    except CurrentHostBindingError:
        raise
    except Exception as exc:
        raise CurrentHostBindingError("SELECTION", "Selection validation failed", cause=exc) from exc


def git_binding_from_selection(config_path, config_sha256):
    """{"path", "sha256"} of HOST's Git for a digest-checked 0.2.0 selection (plan section 4.5).

    It reads the configuration and its HOST document and starts no Git and no other process.
    """
    try:
        _digest(config_sha256, "SELECTION")
        path = _absolute(config_path, category="SELECTION")
        config, actual = _read(path, 1024 * 1024, category="SELECTION")
        _require(actual["sha256"] == config_sha256, "SELECTION", "Configuration differs from the independently supplied expected digest")
        _schema(config, "config", CONFIG_KEYS)
        _require(config["contract"] == CONTRACT, "SCHEMA", "Unsupported current-host contract")
        return _host_git(config)
    except CurrentHostBindingError:
        raise
    except Exception as exc:
        raise CurrentHostBindingError("SELECTION", "The selection's Git binding cannot be read", cause=exc) from exc


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
    row = {"schema": PREFIX + "workspace" + VERSION, **_identity(), "identity": uuid.uuid4().hex,
           "parent_config": parent, "source_root": str(source_root), "workspace_root": str(workspace),
           "commit": config["source"]["commit"], "tree": config["source"]["tree"],
           "source_inventory": config["source"]["inventory"], "source_before": before, "workspace_inventory": copied,
           "immutable_inventory_sha256": immutable_workspace_inputs(source_before)["sha256"],
           "provider": str(workspace / PROVIDER), "probe": str(workspace / PROBE)}
    binding = _write_new(directory / "workspace-binding.json", row)
    derived = deepcopy(config)
    derived["source"]["root"] = str(workspace)
    derived["contract_source"]["path"] = str(workspace / CONTRACT_PATH)
    derived["amendment_adoption"]["path"] = str(workspace / AMENDMENT_ADOPTION_PATH)
    derived["parent"] = {"config": parent, "source_root": str(source_root), "workspace_binding": binding}
    selected = _write_new(directory / "selection.json", derived)
    _selection(selected["path"], selected["sha256"], workspace, own_root=False)
    _bound(config_path, {key: parent[key] for key in ("sha256", "size_bytes", "mode")}, category="WORKSPACE")
    return {"config_path": selected["path"], "config_sha256": selected["sha256"],
            "parent_config_sha256": config_sha256, "workspace_binding_path": binding["path"],
            "workspace_binding_sha256": binding["sha256"]}


# ---------------------------------------------------------------------------
# Manifest, jobs and the single delegated supervisor call
# ---------------------------------------------------------------------------

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
    return {"schema": PREFIX + "lock" + VERSION, **_identity(), "labels": selection["labels"],
            "profile": "ontokin.static-tray/0.1.0",
            "schedule_root": str(schedule), "cohort_root": str(cohort), "dependencies_root": str(deps), "scope": SCOPE,
            "limits": LIMITS, "environment": ENVIRONMENT, "files": files,
            "runtime": {**config["runtime"], "binding": _plain(host["runtime"]["binding"])},
            "validator_version": "2.0.0-dev.3.10", "three_version": "0.186.1",
            "validator_entry": str(deps / "validator/package/index.js"), "three_package": str(deps / "indexer-view/three/package.json"),
            "three_entry": str(deps / "indexer-view/three/build/three.webgpu.js"),
            "gltf_loader_entry": str(deps / "indexer-view/three/examples/jsm/loaders/GLTFLoader.js"),
            "module_loader": loader, "probe": probe, "validator_options": VALIDATOR_OPTIONS, "three_options": THREE_OPTIONS,
            "slots": rows, "selection": {"path": selection["path"], "sha256": selection["sha256"]},
            "source": config["source"], "host": config["host"], "methods": config["methods"], "dependencies": config["dependencies"]}


def _prepare_case_manifest(output, *, config_path, config_sha256, source_root, schedule_root):
    selection = _selection(config_path, config_sha256, source_root)
    manifest = _manifest(selection, output, schedule_root)
    _require(not Path(output).exists(), "MANIFEST", "Manifest must be a fresh path")
    descriptor = _write_new(output, manifest)
    verified = _selection(config_path, config_sha256, source_root)
    _verified_manifest(output, verified, schedule_root)
    return manifest, descriptor["sha256"], verified


def prepare_case_manifest(output, *, config_path, config_sha256, source_root, schedule_root):
    manifest, digest, _ = _prepare_case_manifest(output, config_path=config_path, config_sha256=config_sha256,
                                                 source_root=source_root, schedule_root=schedule_root)
    return manifest, digest


def _verified_manifest(path, selection, schedule_root, *, check=lambda: None):
    manifest, binding = _read(path, 1024 * 1024, check=check, category="MANIFEST")
    _schema(manifest, "lock", MANIFEST_KEYS, "MANIFEST")
    expected = _manifest(selection, path, schedule_root)
    _require(manifest == expected, "MANIFEST", "Manifest differs from the exact approved source/input/slot bindings")
    _tick(check)
    return manifest, binding["sha256"]


def verify_case_manifest(path, *, config_path, config_sha256, source_root, schedule_root, check=lambda: None):
    selection = _selection(config_path, config_sha256, source_root, check=check)
    return _verified_manifest(path, selection, schedule_root, check=check)


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
    selection = _selection(selection_path, selection_digest, ROOT, check=check)
    manifest, digest = _verified_manifest(job["manifest"], selection, stage.parent / "unused-native-schedule", check=check)
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
            "config_sha256": selection_digest, "source": manifest["source"],
            "host_state": {"platform": selection["host"]["platform"], "os": selection["host"]["os"]}}


def guarded_run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):
    """One delegated Darwin supervisor call, with bounded pre/postflight, the boot binding and durable evidence."""
    stage = Path(stage)
    ledger = {"schema": PREFIX + "attempt" + VERSION, **_identity(), "labels": _labels_now(),
              "expected_argv": argv, "expected_checker_starts": 1,
              "actual_checker_starts": 0, "preflight": None, "postflight": None, "boot_before": None, "boot_after": None,
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
        ledger["labels"] = _labels_now()
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
            # MC09: the boot, OS build and cryptex version immediately before the start.
            ledger["boot_before"] = _check_state(launch["host_state"], host_state(check=lambda: clock.check(stage_end)),
                                                 "before the start")
            _tick(lambda: clock.check(stage_end))
            result = supervisor_darwin_v01.run_process(argv, stage=stage, label=label, clock=clock, stage_end=stage_end,
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
        # MC09: the same identity after the start; a change fails the attempt whatever the supervisor reported.
        ledger["boot_after"] = _check_state(ledger["preflight"]["host_state"], host_state(check=lambda: clock.check()),
                                            "after the start")
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
        ledger["labels"] = _labels_now()
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
                                      evidence_finalized=bool(directory and (directory / "result.json").is_file()),
                                      attempt=ledger, labels=_labels_now())
        raise failure from delegated
    if delegated is not None:
        if isinstance(delegated, supervisor.Stop):
            raise delegated
        raise CurrentHostBindingError("EVIDENCE", "Supervisor failed outside its declared Stop interface", cause=delegated,
                                      process_record=ledger["process"], state="UNKNOWN") from delegated
    return result


# ---------------------------------------------------------------------------
# Class lifecycle seams: setup and the cohort accounting (S8, D-08)
# ---------------------------------------------------------------------------

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
    _write_new(retained / "PRESERVATION.json", {"schema": PREFIX + "preserved-cohort" + VERSION, **_identity(),
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
    ordinary = not os.environ.get(CONFIG_ENV) and not os.environ.get(DIGEST_ENV)
    run_kind = "ordinary" if ordinary else "qualifying"
    record = {"schema": PREFIX + "setup" + VERSION, **_identity(), "labels": _labels_now(run_kind), "run_kind": run_kind,
              "passed": False, "checker_starts": 0, "boot": None}
    destination = None
    failure = None
    try:
        # S8: without any selection this is an ordinary run; the class fails visibly and is never skipped.
        _require(not ordinary, "SELECTION", ORDINARY_RUN_REASON)
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
        cls.manifest, cls.manifest_hash, selection = _prepare_case_manifest(cls.manifest_path,
            config_path=selected_path, config_sha256=selected_digest, source_root=ROOT,
            schedule_root=cls.root / "unused-native-schedule")
        # MC09: the boot, OS build and cryptex version before the cohort.
        record["boot"] = _check_state({"platform": selection["host"]["platform"], "os": selection["host"]["os"]},
                                      host_state(), "before the cohort")
        record.update(passed=True, config_path=selected_path, config_sha256=selected_digest,
                      manifest_sha256=cls.manifest_hash, source_root=str(ROOT))
    except BaseException as exc:
        failure = exc if isinstance(exc, CurrentHostBindingError) else CurrentHostBindingError("EVIDENCE", "CPU setup failed", cause=exc)
        record["error"] = failure.as_dict()
    finally:
        record["labels"] = _labels_now(run_kind)
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
        failure.refusal_record.update(actual_checker_starts=0, setup=record, run_kind=run_kind,
                                      authorized_evidence_destination=str(destination) if destination else "unavailable",
                                      evidence_finalized=bool(destination and destination.is_file()),
                                      labels=_labels_now(run_kind))
        raise failure


def finish_cpu_cohort(cls):
    """Reconcile the three durable attempts; a missing method fails the run (D-08); never delete failed evidence."""
    record = {"schema": PREFIX + "cohort" + VERSION, **_identity(), "labels": _labels_now(),
              "passed": False, "expected_cases": sorted(CASES)}
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
        record["labels"] = _labels_now()
        try:
            _write_new(cls.root / "cohort.json", record)
        finally:
            _preserve_temporary(cls)
    if failure:
        raise failure


# The boundary objects as defined here; a substitute of any of them labels results "mocked".
_REAL_BOUNDARY = _boundary_functions()
