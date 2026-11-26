#!/usr/bin/env python3
"""Safely stage a separately approved current-host readback input tree.

Dry-run is the default. This tool never executes Node, ldd or recovered files.
The plan and its complete archive inventory must be frozen independently before
use. Installation is absent-or-complete-exact with atomic no-replace
publication. The plan's schema selects the route, and each route refuses the
other route's plans:
- install/0.1.0 (contract 0.1.0): Linux renameat2(RENAME_NOREPLACE), unchanged;
- install/0.2.0 (contract 0.2.0, darwin-arm64-v1): Darwin renamex_np with
  RENAME_EXCL, the official Node archive's member policy and the planned
  NODE-SOURCE.json.
Runtime qualification remains a separate explicitly selected gate.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import sys
import tarfile
import tempfile
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from prototypes.static_tray_v01 import current_host_readback_v01 as provider
from prototypes.static_tray_v01 import canonical
from prototypes.static_tray_v01.errors import TrayError

SCHEMA = "ontokin.current-host-readback-install/0.1.0"
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_EXPANDED_BYTES = 1024 * 1024 * 1024
MAX_MEMBERS = 32768
MAX_FILES = 32768


def _require(condition, reason):
    provider._require(condition, "INSTALL", reason)


def _relative(name):
    _require(type(name) is str and name and "\\" not in name, "Invalid archive path")
    value = name[:-1] if name.endswith("/") else name
    path = PurePosixPath(value)
    _require(not path.is_absolute() and str(path) == value and ".." not in path.parts and value != ".",
             "Unsafe archive path: " + name)
    return value


def _mode(value):
    _require(type(value) is str and value in {oct(number) for number in range(0o1000)}, "Invalid extraction mode")
    mode = int(value, 8)
    _require(mode & 0o7000 == 0 and mode & 0o022 == 0, "Group/world-writable or privileged extraction mode")
    return mode


def _parent_identity(path):
    path = provider._absolute(path, category="INSTALL")
    _require(path.is_dir(), "Destination parent is missing")
    result = {}
    for item in (path, *path.parents):
        info = item.lstat()
        _require(stat.S_ISDIR(info.st_mode), "Ancestor is not an actual directory")
        result[str(item)] = {"device": info.st_dev, "inode": info.st_ino, "mode": stat.S_IMODE(info.st_mode)}
    return result


def existing_tree(destination, inventory):
    destination = provider._absolute(destination, category="INSTALL")
    if not destination.exists():
        return {"state": "absent"}
    _require(destination.is_dir(), "Existing destination is not a directory")
    provider._tree_state(destination, inventory["files"], inventory["directories"], category="INSTALL")
    _require(oct(stat.S_IMODE(destination.stat().st_mode)) == inventory["root_mode"], "Existing destination root mode differs")
    return {"state": "complete_exact", "files": len(inventory["files"]), "directories": len(inventory["directories"])}


def _plan_shape(plan):
    provider._keys(plan, ("schema", "purpose", "source", "archive", "destination", "root_mode", "files", "directories", "members", "report"), "INSTALL")
    _require(plan["schema"] == SCHEMA, "Unsupported installation schema")
    _require(plan["purpose"] in ("retained-dependencies", "selected-node", "isolated-control"), "Unknown installation purpose")
    provider._binding_shape(plan["archive"], descriptor=True)
    _require(plan["archive"]["size_bytes"] <= MAX_ARCHIVE_BYTES, "Archive byte allowance exceeded")
    provider._absolute(plan["destination"], category="INSTALL")
    provider._absolute(plan["report"], category="INSTALL")
    _mode(plan["root_mode"])
    _require(type(plan["files"]) is dict and 0 < len(plan["files"]) <= MAX_FILES,
             "Missing or excessive target file inventory")
    for name, binding in plan["files"].items():
        _relative(name)
        provider._binding_shape(binding)
        _mode(binding["mode"])
    _require(type(plan["directories"]) is dict, "Invalid target directory inventory")
    necessary = {str(parent) for name in plan["files"] for parent in PurePosixPath(name).parents if str(parent) != "."}
    _require(set(plan["directories"]) == necessary, "Target directory inventory is not exact")
    for name, mode in plan["directories"].items():
        _relative(name)
        _require(_mode(mode) & 0o500 == 0o500, "Directory owner must be able to inspect and traverse")
    _require(type(plan["members"]) is dict and 0 < len(plan["members"]) <= MAX_MEMBERS,
             "Missing or excessive full archive member inventory")
    targets = {}
    for name, item in plan["members"].items():
        _relative(name)
        provider._keys(item, ("kind", "size_bytes", "sha256", "mode", "target"), "INSTALL")
        _require(item["kind"] in ("file", "directory"), "Links and special archive members are forbidden")
        _mode(item["mode"])
        _require(type(item["size_bytes"]) is int and item["size_bytes"] >= 0, "Invalid archive member size")
        if item["kind"] == "file":
            provider._digest(item["sha256"], "INSTALL")
        else:
            _require(item["size_bytes"] == 0 and item["sha256"] is None, "Invalid directory member binding")
        if item["target"] is not None:
            target = _relative(item["target"])
            _require(target not in targets, "Duplicate destination member")
            targets[target] = item
            expected = plan["files"].get(target) if item["kind"] == "file" else plan["directories"].get(target)
            if item["kind"] == "file":
                _require(expected == {key: item[key] for key in ("sha256", "size_bytes", "mode")}, "Archive-to-target file binding differs")
            else:
                _require(expected == item["mode"], "Archive-to-target directory binding differs")
    _require({name for name, item in targets.items() if item["kind"] == "file"} == set(plan["files"]),
             "Missing or extra mapped destination file")
    # Parent directories may be implicit in a tar; their exact frozen modes are
    # still materialized and checked. Extra mapped directories are forbidden.
    _require({name for name, item in targets.items() if item["kind"] == "directory"} <= set(plan["directories"]),
             "Extra mapped destination directory")
    _require(sum(row["size_bytes"] for row in plan["members"].values()) <= MAX_EXPANDED_BYTES,
             "Expanded archive byte allowance exceeded")


@contextmanager
def _safe_archive_stream(binding):
    path = provider._absolute(binding["path"], category="INSTALL")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= MAX_ARCHIVE_BYTES,
                 "Archive must be a bounded private regular file")
        def authenticate():
            stream.seek(0)
            digest, length = hashlib.sha256(), 0
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                length += len(block)
                _require(length <= MAX_ARCHIVE_BYTES, "Archive grew beyond its allowance")
                digest.update(block)
            actual = {"sha256": digest.hexdigest(), "size_bytes": length, "mode": oct(stat.S_IMODE(before.st_mode))}
            _require(actual == {key: binding[key] for key in ("sha256", "size_bytes", "mode")}, "Opened archive identity differs")
            after, named = os.fstat(stream.fileno()), path.lstat()
            identity = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mode, row.st_nlink, row.st_mtime_ns, row.st_ctime_ns)
            _require(identity(before) == identity(after) == identity(named), "Archive path or contents changed while open")
            stream.seek(0)
        authenticate()
        yield stream
        authenticate()


def verify_archive(plan, *, destination=None):
    """Validate every member and stream only declared regular files to staging."""
    binding = plan["archive"]
    provider._bound(binding["path"], {key: binding[key] for key in ("sha256", "size_bytes", "mode")},
                    maximum=MAX_ARCHIVE_BYTES, category="INSTALL")
    seen, expanded = set(), 0
    with _safe_archive_stream(binding) as source, tarfile.open(fileobj=source, mode="r:*") as archive:
        for member in archive:
            name = _relative(member.name)
            _require(name not in seen and len(seen) < MAX_MEMBERS, "Duplicate or excessive archive member")
            seen.add(name)
            _require(name in plan["members"], "Unexpected archive member: " + name)
            expected = plan["members"][name]
            _require(member.isfile() or member.isdir(), "Archive links and special files are forbidden")
            kind = "file" if member.isfile() else "directory"
            _require(expected["kind"] == kind and member.size == expected["size_bytes"]
                     and oct(member.mode) == expected["mode"] and not member.sparse,
                     "Archive kind, mode, size or sparse representation differs: " + name)
            expanded += member.size
            _require(expanded <= MAX_EXPANDED_BYTES, "Archive expanded byte allowance exceeded")
            if kind == "directory":
                continue
            stream = archive.extractfile(member)
            _require(stream is not None, "Cannot read declared archive file")
            digest, count, output = hashlib.sha256(), 0, None
            try:
                if destination is not None and expected["target"] is not None:
                    path = destination / expected["target"]
                    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                    output = os.fdopen(fd, "wb")
                while True:
                    data = stream.read(min(1024 * 1024, member.size - count + 1))
                    if not data:
                        break
                    count += len(data)
                    _require(count <= member.size, "Archive member exceeds declared size")
                    digest.update(data)
                    if output is not None:
                        output.write(data)
                _require(count == member.size and digest.hexdigest() == expected["sha256"], "Archive member bytes differ: " + name)
                if output is not None:
                    output.flush()
                    os.fchmod(output.fileno(), _mode(expected["mode"]))
                    os.fsync(output.fileno())
            finally:
                stream.close()
                if output is not None:
                    output.close()
    _require(seen == set(plan["members"]), "Archive is missing declared members")
    provider._bound(binding["path"], {key: binding[key] for key in ("sha256", "size_bytes", "mode")}, category="INSTALL")
    return {"members": len(seen), "expanded_bytes": expanded}


def rename_without_replacement(source, destination):
    library = ctypes.CDLL(None, use_errno=True)
    function = getattr(library, "renameat2", None)
    _require(function is not None, "Atomic no-replace publication is unavailable")
    function.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    function.restype = ctypes.c_int
    if function(-100, os.fsencode(source), -100, os.fsencode(destination), 1):
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(destination))


def _source(plan):
    # Isolated controls are an explicitly marked finite filesystem test API,
    # never an admissible runtime/dependency preparation plan at the CLI.
    if plan["purpose"] == "isolated-control":
        _require(plan["source"] is None, "Isolated control cannot claim a source qualification")
        return
    provider._verify_source(plan["source"], own_root=True)
    destination = Path(plan["destination"])
    _require(not destination.is_relative_to(ROOT), "Installed inputs must be outside source")
    if plan["purpose"] == "retained-dependencies":
        _require(plan["archive"]["sha256"] == provider.ARCHIVE_SHA256, "Retained dependency archive differs")
        expected = provider.dependency_inventory(ROOT)
        _require(set(plan["files"]) == set(expected), "Exact 24 dependency targets are required")
        for name, row in expected.items():
            _require({key: plan["files"][name][key] for key in ("sha256", "size_bytes")} == row,
                     "Retained dependency bytes differ")
    else:
        _require(plan["archive"]["sha256"] == provider.NODE_ARCHIVE_SHA256
                 and plan["archive"]["size_bytes"] == provider.NODE_ARCHIVE_BYTES,
                 "Selected runtime archive differs from the saved P05 input")
        _require(set(plan["files"]) == {"bin/node", "SOURCE.json"}, "Selected runtime archive layout differs")
        _require(plan["files"]["bin/node"] == {"sha256": provider.NODE_SHA256, "size_bytes": provider.NODE_BYTES, "mode": "0o755"},
                 "Selected runtime bytes/mode differ")


def install_plan(plan, *, apply=False):
    """Execute a predeclared static install; no recovered process can start."""
    report = {"schema": "ontokin.current-host-readback-install-result/0.1.0", "passed": False,
              "apply_requested": apply, "execution_counts": {"node": 0, "ldd": 0, "checkers": 0},
              "operations": [], "state": "REJECTED"}
    staged = None
    staged_identity = None
    report_path = None
    failure = None
    try:
        _plan_shape(plan)
        destination = provider._absolute(plan["destination"], category="INSTALL")
        report_path = provider._absolute(plan["report"], category="INSTALL")
        _require(not report_path.is_relative_to(destination) and not report_path.is_relative_to(ROOT)
                 and not report_path.exists(), "Fresh report must be outside source and destination")
        ancestors = _parent_identity(destination.parent)
        _source(plan)
        report["archive"] = verify_archive(plan)
        report["before"] = existing_tree(destination, plan)
        provider._write_new(report_path.with_name(report_path.name + ".preflight.json"), report)
        if report["before"]["state"] == "complete_exact":
            report.update(passed=True, state="ALREADY_PRESENT_EXACT")
        elif not apply:
            report.update(passed=True, state="DRY_RUN_READY")
        else:
            _require(sys.platform == "linux", "Atomic installation is supported only on Linux")
            staged = Path(tempfile.mkdtemp(prefix=".current-host-stage-", dir=destination.parent))
            info = staged.lstat()
            staged_identity = (info.st_dev, info.st_ino)
            report["operations"].append({"operation": "created_owned_stage", "path": str(staged), "device": info.st_dev, "inode": info.st_ino})
            for name in sorted(plan["directories"], key=lambda value: (len(PurePosixPath(value).parts), value)):
                (staged / name).mkdir(mode=0o700)
            verify_archive(plan, destination=staged)
            for name in sorted(plan["directories"], key=lambda value: (-len(PurePosixPath(value).parts), value)):
                os.chmod(staged / name, _mode(plan["directories"][name]))
            os.chmod(staged, _mode(plan["root_mode"]))
            existing_tree(staged, plan)
            _require(_parent_identity(destination.parent) == ancestors, "Destination ancestors changed before publication")
            # Preserve intended source and target before a potentially uncertain
            # syscall. A retry is never automatic.
            provider._write_new(report_path.with_name(report_path.name + ".publication.json"),
                                {"source": str(staged), "destination": str(destination), "owned_stage": staged_identity,
                                 "mode": "RENAME_NOREPLACE", "state": "INTENT_RECORDED"})
            try:
                rename_without_replacement(staged, destination)
            except OSError as exc:
                report["publication_error"] = {"errno": exc.errno, "reason": str(exc)}
                try:
                    report["destination_after_error"] = existing_tree(destination, plan)
                except BaseException as observed:
                    report["destination_after_error"] = {"state": "REFUSED", "error": provider._failure(observed)}
                if exc.errno == errno.EEXIST:
                    raise provider.CurrentHostBindingError("INSTALL", "Publication race: destination retained; readback recorded, no retry", cause=exc)
                raise provider.CurrentHostBindingError("INSTALL", "Publication outcome requires explicit reconciliation", cause=exc, state="UNKNOWN") from exc
            staged = None  # The former owned path no longer exists; never remove destination.
            _require(_parent_identity(destination.parent) == ancestors, "Destination ancestors changed across publication")
            report["after"] = existing_tree(destination, plan)
            fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            report.update(passed=True, state="INSTALLED_EXACT")
    except BaseException as exc:
        failure = exc if isinstance(exc, provider.CurrentHostBindingError) else provider.CurrentHostBindingError("INSTALL", "Safe preparation failed", cause=exc)
        report.update(passed=False, state=failure.state, error=failure.as_dict())
    finally:
        if staged is not None:
            try:
                info = staged.lstat()
                _require(not staged.is_symlink() and (info.st_dev, info.st_ino) == staged_identity,
                         "Owned stage identity changed; cleanup refused")
                shutil.rmtree(staged)
                report["operations"].append({"operation": "removed_owned_stage", "path": str(staged)})
            except BaseException as exc:
                report.update(passed=False, state="UNKNOWN", cleanup_error=provider._failure(exc))
                failure = provider.CurrentHostBindingError("INSTALL", "Owned staging cleanup is unresolved", cause=exc, state="UNKNOWN")
        if report_path is not None:
            try:
                provider._write_new(report_path, report)
            except BaseException as exc:
                failure = provider.CurrentHostBindingError("EVIDENCE", "Preparation report write failed", cause=exc, state="UNKNOWN")
                failure.refusal_record = report
    if failure:
        failure.refusal_record = report
        raise failure
    return report


# ---------------------------------------------------------------------------
# Route 0.2.0: contract ontokin.current-host-readback/0.2.0, profile
# darwin-arm64-v1, change S6 (CONTRACT.md sections 3 and 6 of C271-P31).
# The 0.1.0 functions above are unchanged. This route reuses only their helpers
# _require, _relative, _mode, _parent_identity, _safe_archive_stream and
# existing_tree, and the 0.1.0 extractor verify_archive for the C195 reader
# archive, whose P05 section 5 rules the contract keeps unchanged (MC34).
# ---------------------------------------------------------------------------

SCHEMA_V02 = "ontokin.current-host-readback-install/0.2.0"
RESULT_SCHEMA_V02 = "ontokin.current-host-readback-install-result/0.2.0"
CONTRACT_V02 = "ontokin.current-host-readback/0.2.0"
EXECUTOR_V02 = "macos-arm64-local"
PURPOSES_V02 = ("selected-node", "retained-dependencies")
PLAN_KEYS_V02 = ("schema", "contract", "purpose", "source_root", "archive", "destination", "root_mode",
                 "files", "directories", "members", "node_source", "report")
NODE_RELEASE_V02 = "node-v24.22.1-darwin-arm64"
NODE_ARCHIVE_NAME_V02 = NODE_RELEASE_V02 + ".tar.gz"
# The adopted pin (contract section 3). Only SyntheticPins, passed explicitly to
# install_plan_v02, can substitute another value; plans, the CLI and the
# environment cannot.
NODE_ARCHIVE_SHA256_V02 = "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"
NODE_CHECKSUM_FILE_V02 = MappingProxyType({"url": "https://nodejs.org/dist/v24.22.1/SHASUMS256.txt",
                                           "sha256": "fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4",
                                           "size_bytes": 3171})
NODE_MEMBER_V02 = NODE_RELEASE_V02 + "/bin/node"
NODE_EXECUTABLE_V02 = "bin/node"
NODE_EXECUTABLE_MODE_V02 = "0o755"
NODE_SOURCE_V02 = "NODE-SOURCE.json"
NODE_SOURCE_SCHEMA_V02 = "ontokin.current-host-readback-node-source/0.2.0"
NODE_MEMBER_KEYS_V02 = ("kind", "size_bytes", "mode", "link_target")
NODE_MEMBER_KINDS_V02 = ("file", "directory", "symlink")
DEPENDENCY_MEMBER_KEYS_V02 = ("kind", "size_bytes", "sha256", "mode", "target")
MEMBER_MODES_V02 = frozenset(oct(number) for number in range(0o10000))
SIGNATURE_STATES_V02 = ("not_performed", "verified", "failed")
MAX_DETAIL_CHARS_V02 = 4096
PREPARER_FILES_V02 = ("tools/prepare_current_host_readback.py",
                      "prototypes/static_tray_v01/current_host_readback_v01.py",
                      "prototypes/static_tray_v01/canonical.py")
# Minimal Mach-O header predicate (MC05); the observer owns the load commands.
MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C
MH_EXECUTE = 2
MACH_HEADER_64_BYTES = 32
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"
# RENAME_EXCL is bound from the macOS SDK header, read by path (xcrun was not
# run): <SDK>/usr/include/stdio.h includes <_stdio.h>, which includes
# <sys/stdio.h>, whose line 37 is "#define RENAME_EXCL 0x00000004" (spacing
# condensed); both installed SDKs agree. Paths, sizes and SHA-256 values are in
# docs/engineering/localized-repair-c271/macos-implementation-p33/interfaces/W2-PREPARER.md.
RENAME_EXCL = 0x00000004


@dataclass(frozen=True)
class SyntheticPins:
    """The explicit test seam: pins for synthetic archives, never operational.

    Only a direct caller of install_plan_v02 can pass it. Its result is labelled
    pins.origin == "synthetic-test-seam" and is not a preparation receipt.
    """
    node_archive_sha256: str
    dependency_archive_sha256: str
    dependency_files: dict


def _pins_v02(synthetic_pins):
    if synthetic_pins is None:
        return {"origin": "adopted-contract", "node_archive_sha256": NODE_ARCHIVE_SHA256_V02,
                "dependency_archive_sha256": provider.ARCHIVE_SHA256, "dependency_files": None}
    _require(type(synthetic_pins) is SyntheticPins, "The pin seam accepts only SyntheticPins")
    provider._digest(synthetic_pins.node_archive_sha256, "INSTALL")
    provider._digest(synthetic_pins.dependency_archive_sha256, "INSTALL")
    files = synthetic_pins.dependency_files
    _require(type(files) is dict and files, "Synthetic dependency pins need files")
    rows = {}
    for name, row in files.items():
        _require(_relative(name) == name, "Invalid synthetic dependency path")
        provider._keys(row, ("sha256", "size_bytes"), "INSTALL")
        provider._digest(row["sha256"], "INSTALL")
        _require(type(row["size_bytes"]) is int and row["size_bytes"] >= 0, "Invalid synthetic dependency size")
        rows[name] = {"sha256": row["sha256"], "size_bytes": row["size_bytes"]}
    return {"origin": "synthetic-test-seam", "node_archive_sha256": synthetic_pins.node_archive_sha256,
            "dependency_archive_sha256": synthetic_pins.dependency_archive_sha256, "dependency_files": rows}


def _json_bytes_v02(value):
    try:
        return canonical.json_bytes(value)
    except TrayError as exc:
        raise provider.CurrentHostBindingError("INSTALL", "Value has no canonical ASCII JSON form", cause=exc) from exc


def member_inventory_sha256_v02(members):
    """SHA-256 of the frozen inventory's canonical JSON bytes (canonical.json_bytes).

    The inventory is the plan's members object: member name to its row. Sorted
    keys, compact separators and ASCII-only text make the bytes canonical.
    """
    return hashlib.sha256(_json_bytes_v02(members)).hexdigest()


def node_source_document_v02(plan):
    """The NODE-SOURCE.json value, built only from a selected-node plan's values."""
    executable = plan["files"][NODE_EXECUTABLE_V02]
    check = plan["node_source"]["signature_check"]
    return {"schema": NODE_SOURCE_SCHEMA_V02, "contract": CONTRACT_V02,
            "archive": {"name": NODE_ARCHIVE_NAME_V02, "sha256": plan["archive"]["sha256"],
                        "size_bytes": plan["archive"]["size_bytes"]},
            "checksum_file": dict(NODE_CHECKSUM_FILE_V02),
            "signature_check": {"status": check["status"], "detail": check["detail"]},
            "member_inventory_sha256": member_inventory_sha256_v02(plan["members"]),
            "extracted": {"member": NODE_MEMBER_V02, "path": NODE_EXECUTABLE_V02, "sha256": executable["sha256"],
                          "size_bytes": executable["size_bytes"], "mode": executable["mode"]}}


def node_source_bytes_v02(plan):
    return _json_bytes_v02(node_source_document_v02(plan))


def _link_target_v02(name, target):
    """Resolve a relative link target lexically; it must stay inside the archive root."""
    _require(type(target) is str and target and "\\" not in target and "\0" not in target
             and not target.startswith("/"), "Absolute or malformed link target: " + name)
    parts = list(PurePosixPath(name).parts[:-1])
    for part in target.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            _require(len(parts) > 1, "Escaping link target: " + name)
            parts.pop()
        else:
            parts.append(part)
    _require(bool(parts) and parts[0] == NODE_RELEASE_V02, "Escaping link target: " + name)
    return "/".join(parts)


def _signature_check_v02(node_source):
    provider._keys(node_source, ("signature_check",), "INSTALL")
    check = node_source["signature_check"]
    provider._keys(check, ("status", "detail"), "INSTALL")
    _require(check["status"] in SIGNATURE_STATES_V02, "Unknown signature-check status")
    _require(type(check["detail"]) is str and 0 < len(check["detail"]) <= MAX_DETAIL_CHARS_V02
             and check["detail"].isascii(), "Signature-check detail must be bounded ASCII text")


def _node_plan_v02(plan, pins):
    """Contract section 3: the official archive's frozen member inventory."""
    _require(plan["archive"]["sha256"] == pins["node_archive_sha256"], "Node archive differs from the adopted pin")
    _require(set(plan["files"]) == {NODE_EXECUTABLE_V02, NODE_SOURCE_V02} and set(plan["directories"]) == {"bin"},
             "Selected runtime layout must be exactly bin/, bin/node and NODE-SOURCE.json")
    executable = plan["files"][NODE_EXECUTABLE_V02]
    _require(executable["mode"] == NODE_EXECUTABLE_MODE_V02, "The Node executable mode must be 0o755")
    members, expanded = plan["members"], 0
    for name, row in members.items():
        _require(_relative(name) == name, "Unsafe or non-normalized archive member name: " + name)
        _require(name == NODE_RELEASE_V02 or name.startswith(NODE_RELEASE_V02 + "/"),
                 "Archive member outside the archive root: " + name)
        provider._keys(row, NODE_MEMBER_KEYS_V02, "INSTALL")
        _require(row["kind"] in NODE_MEMBER_KINDS_V02,
                 "Hard links, devices, FIFOs and other special members are forbidden: " + name)
        _require(type(row["size_bytes"]) is int and row["size_bytes"] >= 0, "Invalid archive member size: " + name)
        _require(type(row["mode"]) is str and row["mode"] in MEMBER_MODES_V02, "Invalid archive member mode: " + name)
        if row["kind"] == "symlink":
            _link_target_v02(name, row["link_target"])
        else:
            _require(row["link_target"] is None, "Only a link member has a link target: " + name)
        _require(row["kind"] == "file" or row["size_bytes"] == 0, "Directory and link members carry no data: " + name)
        expanded += row["size_bytes"]
    _require(expanded <= MAX_EXPANDED_BYTES, "Expanded archive byte allowance exceeded")
    for name in members:
        for parent in PurePosixPath(name).parents:
            if str(parent) in members:
                _require(members[str(parent)]["kind"] == "directory", "Archive member below a link or file: " + name)
    node = members.get(NODE_MEMBER_V02)
    _require(node is not None and node["kind"] == "file", "The Node member must be a declared regular file")
    _require(node["size_bytes"] == executable["size_bytes"], "Declared Node member size differs from the frozen executable")
    _signature_check_v02(plan["node_source"])
    raw, frozen = node_source_bytes_v02(plan), plan["files"][NODE_SOURCE_V02]
    _require(hashlib.sha256(raw).hexdigest() == frozen["sha256"] and len(raw) == frozen["size_bytes"],
             "NODE-SOURCE.json bytes differ from the plan's frozen digest and size")


def _dependency_plan_v02(plan, pins):
    """P05 section 5's rules for the C195 archive, unchanged from the 0.1.0 route."""
    _require(plan["node_source"] is None, "Retained dependencies carry no Node provenance")
    _require(plan["archive"]["sha256"] == pins["dependency_archive_sha256"], "Retained dependency archive differs")
    expected = pins["dependency_files"] if pins["dependency_files"] is not None else provider.dependency_inventory(ROOT)
    _require(set(plan["files"]) == set(expected), "Exact dependency targets are required")
    for name, row in expected.items():
        _require({key: plan["files"][name][key] for key in ("sha256", "size_bytes")}
                 == {key: row[key] for key in ("sha256", "size_bytes")}, "Retained dependency bytes differ")
    targets = {}
    for name, item in plan["members"].items():
        _require(_relative(name) == name, "Unsafe or non-normalized archive member name: " + name)
        provider._keys(item, DEPENDENCY_MEMBER_KEYS_V02, "INSTALL")
        _require(item["kind"] in ("file", "directory"), "Links and special archive members are forbidden")
        _mode(item["mode"])
        _require(type(item["size_bytes"]) is int and item["size_bytes"] >= 0, "Invalid archive member size")
        if item["kind"] == "file":
            provider._digest(item["sha256"], "INSTALL")
        else:
            _require(item["size_bytes"] == 0 and item["sha256"] is None, "Invalid directory member binding")
        if item["target"] is not None:
            target = _relative(item["target"])
            _require(target not in targets, "Duplicate destination member")
            targets[target] = item
            if item["kind"] == "file":
                _require(plan["files"].get(target) == {key: item[key] for key in ("sha256", "size_bytes", "mode")},
                         "Archive-to-target file binding differs")
            else:
                _require(plan["directories"].get(target) == item["mode"], "Archive-to-target directory binding differs")
    _require({name for name, item in targets.items() if item["kind"] == "file"} == set(plan["files"]),
             "Missing or extra mapped destination file")
    _require({name for name, item in targets.items() if item["kind"] == "directory"} <= set(plan["directories"]),
             "Extra mapped destination directory")
    _require(sum(row["size_bytes"] for row in plan["members"].values()) <= MAX_EXPANDED_BYTES,
             "Expanded archive byte allowance exceeded")


def _plan_shape_v02(plan, pins):
    _require(type(plan) is dict and plan.get("schema") == SCHEMA_V02,
             "The 0.2.0 preparer refuses a plan of another schema version")
    provider._keys(plan, PLAN_KEYS_V02, "INSTALL")
    _require(plan["contract"] == CONTRACT_V02, "Installation plan names another contract")
    _require(plan["purpose"] in PURPOSES_V02, "Unknown 0.2.0 installation purpose")
    _require(provider._absolute(plan["source_root"], category="INSTALL") == ROOT,
             "Installation plan belongs to another source checkout")
    provider._binding_shape(plan["archive"], descriptor=True)
    _require(plan["archive"]["size_bytes"] <= MAX_ARCHIVE_BYTES, "Archive byte allowance exceeded")
    destination = provider._absolute(plan["destination"], category="INSTALL")
    _require(not destination.is_relative_to(ROOT), "Installed inputs must be outside source")
    provider._absolute(plan["report"], category="INSTALL")
    _mode(plan["root_mode"])
    _require(type(plan["files"]) is dict and 0 < len(plan["files"]) <= MAX_FILES,
             "Missing or excessive target file inventory")
    for name, binding in plan["files"].items():
        _require(_relative(name) == name, "Unsafe or non-normalized target file name")
        provider._binding_shape(binding)
        _mode(binding["mode"])
    _require(type(plan["directories"]) is dict, "Invalid target directory inventory")
    necessary = {str(parent) for name in plan["files"] for parent in PurePosixPath(name).parents if str(parent) != "."}
    _require(set(plan["directories"]) == necessary, "Target directory inventory is not exact")
    for name, mode in plan["directories"].items():
        _require(_mode(mode) & 0o500 == 0o500, "Directory owner must be able to inspect and traverse")
    _require(type(plan["members"]) is dict and 0 < len(plan["members"]) <= MAX_MEMBERS,
             "Missing or excessive full archive member inventory")
    if plan["purpose"] == "selected-node":
        _node_plan_v02(plan, pins)
    else:
        _dependency_plan_v02(plan, pins)


def validate_plan_v02(plan):
    """Refuse any plan that is not a valid 0.2.0 plan under the adopted pins."""
    _plan_shape_v02(plan, _pins_v02(None))


def _node_member_kind_v02(member):
    _require(not member.islnk(), "Hard link archive members are forbidden: " + member.name)
    _require(not (member.ischr() or member.isblk()), "Device archive members are forbidden: " + member.name)
    _require(not member.isfifo(), "FIFO archive members are forbidden: " + member.name)
    if member.issym():
        return "symlink"
    if member.isdir():
        return "directory"
    _require(member.isfile() and not member.sparse, "Special or sparse archive members are forbidden: " + member.name)
    return "file"


def _thin_arm64_executable_v02(header):
    """Thin 64-bit little-endian arm64 Mach-O executable header, or refuse."""
    _require(len(header) >= MACH_HEADER_64_BYTES, "The Node executable is shorter than a 64-bit Mach-O header")
    magic, cputype, cpusubtype, filetype = struct.unpack_from("<4I", header)
    _require(magic == MH_MAGIC_64, "The Node executable is not a thin 64-bit little-endian Mach-O file")
    _require(cputype == CPU_TYPE_ARM64, "The Node executable is not an arm64 Mach-O file")
    _require(filetype == MH_EXECUTE, "The Node executable is not a Mach-O executable (MH_EXECUTE)")
    return {"magic": "0x%08x" % magic, "cputype": "0x%08x" % cputype, "cpusubtype": "0x%08x" % cpusubtype,
            "filetype": filetype}


def _node_executable_v02(plan, archive, member, destination):
    """Read the only extracted member; stage it at bin/node when a stage is given."""
    frozen = plan["files"][NODE_EXECUTABLE_V02]
    stream = archive.extractfile(member)
    _require(stream is not None, "Cannot read the declared Node member")
    digest, count, header, output = hashlib.sha256(), 0, b"", None
    try:
        if destination is not None:
            fd = os.open(destination / NODE_EXECUTABLE_V02, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            output = os.fdopen(fd, "wb")
        while True:
            data = stream.read(min(1024 * 1024, member.size - count + 1))
            if not data:
                break
            count += len(data)
            _require(count <= member.size, "Archive member exceeds declared size")
            if len(header) < MACH_HEADER_64_BYTES:
                header += data[:MACH_HEADER_64_BYTES - len(header)]
            digest.update(data)
            if output is not None:
                output.write(data)
        _require(count == member.size == frozen["size_bytes"] and digest.hexdigest() == frozen["sha256"],
                 "Node executable bytes differ from the frozen plan")
        macho = _thin_arm64_executable_v02(header)
        if output is not None:
            output.flush()
            os.fchmod(output.fileno(), _mode(frozen["mode"]))
            os.fsync(output.fileno())
    finally:
        stream.close()
        if output is not None:
            output.close()
    return {"member": NODE_MEMBER_V02, "path": NODE_EXECUTABLE_V02,
            **{key: frozen[key] for key in ("sha256", "size_bytes", "mode")}, "macho": macho}


def _verify_node_archive_v02(plan, *, destination=None):
    """Authenticate the pinned bytes, then check every member against the frozen inventory.

    The archive's SHA-256 is compared with the plan, which equals the pin, before
    tarfile reads any member. Only the Node member's data is read; nothing else
    is extracted, and no link is created or followed.
    """
    binding = plan["archive"]
    identity = {key: binding[key] for key in ("sha256", "size_bytes", "mode")}
    provider._bound(binding["path"], identity, maximum=MAX_ARCHIVE_BYTES, category="INSTALL")
    members, seen, expanded, links, executable = plan["members"], set(), 0, 0, None
    with _safe_archive_stream(binding) as source, tarfile.open(fileobj=source, mode="r:*") as archive:
        for member in archive:
            name = _relative(member.name)
            _require(name not in seen and len(seen) < MAX_MEMBERS, "Duplicate or excessive archive member")
            seen.add(name)
            kind = _node_member_kind_v02(member)
            if kind == "symlink":
                _link_target_v02(name, member.linkname)
                links += 1
            _require(name in members, "Undeclared archive member: " + name)
            expected = members[name]
            _require(kind == expected["kind"] and member.size == expected["size_bytes"]
                     and oct(member.mode) == expected["mode"]
                     and (member.linkname if kind == "symlink" else None) == expected["link_target"],
                     "Archive member differs from the frozen inventory: " + name)
            expanded += member.size
            _require(expanded <= MAX_EXPANDED_BYTES, "Archive expanded byte allowance exceeded")
            if name == NODE_MEMBER_V02:
                executable = _node_executable_v02(plan, archive, member, destination)
    _require(seen == set(members), "Archive is missing declared members")
    _require(executable is not None, "The Node member was not read")
    provider._bound(binding["path"], identity, category="INSTALL")
    return {"sha256": binding["sha256"], "size_bytes": binding["size_bytes"], "members": len(seen),
            "expanded_bytes": expanded, "symlinks": links, "member_inventory_sha256": member_inventory_sha256_v02(members),
            "extracted_members": [NODE_MEMBER_V02], "executable": executable}


def _verify_dependency_archive_v02(plan, *, destination=None):
    result = verify_archive(plan, destination=destination)
    return {"sha256": plan["archive"]["sha256"], "size_bytes": plan["archive"]["size_bytes"], **result,
            "symlinks": 0, "member_inventory_sha256": member_inventory_sha256_v02(plan["members"]),
            "extracted_members": sorted(name for name, row in plan["members"].items()
                                        if row["kind"] == "file" and row["target"] is not None)}


def _staged_executable_v02(path):
    """Read the staged executable's header again before publication (MC05)."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        header = b""
        while len(header) < MACH_HEADER_64_BYTES:
            block = os.read(fd, MACH_HEADER_64_BYTES - len(header))
            if not block:
                break
            header += block
    finally:
        os.close(fd)
    return _thin_arm64_executable_v02(header)


def _write_planned_v02(path, raw, binding):
    """Exclusively create a planned non-archive file whose bytes the plan froze."""
    _require(hashlib.sha256(raw).hexdigest() == binding["sha256"] and len(raw) == binding["size_bytes"],
             "Planned file bytes differ from the plan")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fchmod(stream.fileno(), _mode(binding["mode"]))
        os.fsync(stream.fileno())


def _libsystem_renamex_np():
    library = ctypes.CDLL(LIBSYSTEM, use_errno=True)
    function = getattr(library, "renamex_np", None)
    _require(function is not None, "libSystem renamex_np is unavailable")
    function.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
    function.restype = ctypes.c_int
    return function


def rename_exclusive(source, destination):
    """renamex_np(source, destination, RENAME_EXCL) from libSystem; there is no fallback.

    Any failure, ENOTSUP included, raises OSError with the call's errno.
    """
    _require(sys.platform == "darwin", "Exclusive publication requires Darwin's renamex_np")
    function = _libsystem_renamex_np()
    ctypes.set_errno(0)
    if function(os.fsencode(source), os.fsencode(destination), RENAME_EXCL) != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(destination))


def _publication_failure_v02(report, exc, staged, staged_identity, destination, plan):
    """Read back the destination and the owned stage; return the refusal and whether the stage remains."""
    report["publication_error"] = {"errno": exc.errno, "name": errno.errorcode.get(exc.errno, "UNKNOWN"),
                                   "reason": str(exc)}
    try:
        report["destination_after_error"] = existing_tree(destination, plan)
    except BaseException as observed:
        report["destination_after_error"] = {"state": "REFUSED", "error": provider._failure(observed)}
    try:
        info = staged.lstat()
        owned = stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino) == tuple(staged_identity)
        report["stage_after_error"] = {"state": "owned_stage_present" if owned else "stage_identity_differs"}
        present = True
    except FileNotFoundError:
        owned = present = False
        report["stage_after_error"] = {"state": "absent"}
    except OSError as observed:
        owned, present = False, True
        report["stage_after_error"] = {"state": "unreadable", "error": provider._failure(observed)}
    name = report["publication_error"]["name"]
    if exc.errno == errno.EEXIST:
        failure = provider.CurrentHostBindingError(
            "INSTALL", "Publication conflict: renamex_np refused an existing destination; readback recorded, no retry",
            cause=exc)
    elif owned and report["destination_after_error"]["state"] == "absent":
        failure = provider.CurrentHostBindingError(
            "INSTALL", "Exclusive publication failed (" + name + "); nothing was published and there is no fallback rename",
            cause=exc)
    else:
        failure = provider.CurrentHostBindingError("INSTALL", "Publication outcome requires explicit reconciliation",
                                                   cause=exc, state="UNKNOWN")
    return failure, present


def _labels_v02(plan):
    node = plan is not None and plan["purpose"] == "selected-node"
    unknown = "not established" if plan is None else "not applicable: retained-dependencies"
    return {"executor": EXECUTOR_V02,
            "node_archive_sha256": plan["archive"]["sha256"] if node else unknown,
            "node_executable": dict(plan["files"][NODE_EXECUTABLE_V02]) if node else unknown,
            "os_identity": "not observed by the preparer",
            "python_inventory": "not observed by the preparer",
            "git_binding": "not used: the preparer starts no process",
            "run_kind": "not applicable: installation preparation"}


def _report_v02(apply):
    return {"schema": RESULT_SCHEMA_V02, "contract": CONTRACT_V02, "purpose": None, "passed": False,
            "apply_requested": apply, "execution_counts": {"node": 0, "ldd": 0, "checkers": 0},
            "operations": [], "state": "REJECTED", "pins": None, "labels": _labels_v02(None),
            "preparer_source": None}


def install_plan_v02(plan, *, apply=False, synthetic_pins=None):
    """Execute a predeclared 0.2.0 static install; no process starts.

    synthetic_pins is the explicit test seam (SyntheticPins). The CLI never
    passes it, so operational plans always meet the adopted pins.
    """
    report = _report_v02(apply)
    staged = staged_identity = report_path = failure = None
    try:
        pins = _pins_v02(synthetic_pins)
        report["pins"] = {key: pins[key] for key in ("origin", "node_archive_sha256", "dependency_archive_sha256")}
        report["preparer_source"] = {"root": str(ROOT), "files_at_start": {
            name: provider.file_binding(ROOT / name, category="INSTALL") for name in PREPARER_FILES_V02}}
        _plan_shape_v02(plan, pins)
        report.update(purpose=plan["purpose"], labels=_labels_v02(plan))
        node = plan["purpose"] == "selected-node"
        destination = provider._absolute(plan["destination"], category="INSTALL")
        candidate = provider._absolute(plan["report"], category="INSTALL")
        _require(not candidate.is_relative_to(destination) and not candidate.is_relative_to(ROOT)
                 and not candidate.exists() and candidate.parent.is_dir(),
                 "Fresh report must be outside source and destination")
        # Bound only now, so a refused report path is never written.
        report_path = candidate
        ancestors = _parent_identity(destination.parent)
        report["archive"] = _verify_node_archive_v02(plan) if node else _verify_dependency_archive_v02(plan)
        report["before"] = existing_tree(destination, plan)
        provider._write_new(report_path.with_name(report_path.name + ".preflight.json"), report)
        if report["before"]["state"] == "complete_exact":
            report.update(passed=True, state="ALREADY_PRESENT_EXACT")
        elif not apply:
            report.update(passed=True, state="DRY_RUN_READY")
        else:
            _require(sys.platform == "darwin", "Exclusive installation is supported only on Darwin")
            staged = Path(tempfile.mkdtemp(prefix=".current-host-stage-", dir=destination.parent))
            info = staged.lstat()
            staged_identity = (info.st_dev, info.st_ino)
            report["operations"].append({"operation": "created_owned_stage", "path": str(staged), "device": info.st_dev, "inode": info.st_ino})
            _require(info.st_dev == destination.parent.lstat().st_dev, "Stage is not on the destination's volume")
            for name in sorted(plan["directories"], key=lambda value: (len(PurePosixPath(value).parts), value)):
                (staged / name).mkdir(mode=0o700)
            if node:
                _verify_node_archive_v02(plan, destination=staged)
                _write_planned_v02(staged / NODE_SOURCE_V02, node_source_bytes_v02(plan), plan["files"][NODE_SOURCE_V02])
            else:
                _verify_dependency_archive_v02(plan, destination=staged)
            for name in sorted(plan["directories"], key=lambda value: (-len(PurePosixPath(value).parts), value)):
                os.chmod(staged / name, _mode(plan["directories"][name]))
            os.chmod(staged, _mode(plan["root_mode"]))
            existing_tree(staged, plan)
            if node:
                _staged_executable_v02(staged / NODE_EXECUTABLE_V02)
            _require(_parent_identity(destination.parent) == ancestors, "Destination ancestors changed before publication")
            # Preserve intended source and target before a potentially uncertain
            # call. A retry is never automatic.
            provider._write_new(report_path.with_name(report_path.name + ".publication.json"),
                                {"contract": CONTRACT_V02, "source": str(staged), "destination": str(destination),
                                 "owned_stage": staged_identity, "call": "renamex_np", "mode": "RENAME_EXCL",
                                 "state": "INTENT_RECORDED"})
            try:
                rename_exclusive(staged, destination)
            except OSError as exc:
                refusal, present = _publication_failure_v02(report, exc, staged, staged_identity, destination, plan)
                if not present:
                    staged = None  # Nothing remains at the owned path; never remove the destination.
                raise refusal from exc
            staged = None  # The former owned path no longer exists; never remove destination.
            _require(_parent_identity(destination.parent) == ancestors, "Destination ancestors changed across publication")
            report["after"] = existing_tree(destination, plan)
            fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            report.update(passed=True, state="INSTALLED_EXACT", publication={
                "call": "renamex_np", "library": LIBSYSTEM, "flag": "RENAME_EXCL", "flag_value": RENAME_EXCL})
    except BaseException as exc:
        failure = exc if isinstance(exc, provider.CurrentHostBindingError) else provider.CurrentHostBindingError("INSTALL", "Safe preparation failed", cause=exc)
        report.update(passed=False, state=failure.state, error=failure.as_dict())
    finally:
        if staged is not None:
            try:
                info = staged.lstat()
                _require(not staged.is_symlink() and (info.st_dev, info.st_ino) == staged_identity,
                         "Owned stage identity changed; cleanup refused")
                shutil.rmtree(staged)
                report["operations"].append({"operation": "removed_owned_stage", "path": str(staged)})
            except BaseException as exc:
                report.update(passed=False, state="UNKNOWN", cleanup_error=provider._failure(exc))
                failure = provider.CurrentHostBindingError("INSTALL", "Owned staging cleanup is unresolved", cause=exc, state="UNKNOWN")
        if report_path is not None:
            try:
                provider._write_new(report_path, report)
            except BaseException as exc:
                failure = provider.CurrentHostBindingError("EVIDENCE", "Preparation report write failed", cause=exc, state="UNKNOWN")
                failure.refusal_record = report
    if failure:
        failure.refusal_record = report
        raise failure
    return report


def _main_v02(plan, binding, args):
    """CLI route for a 0.2.0 plan: adopted pins only, 0.2.0 refusal records."""
    if binding["sha256"] != args.plan_sha256:
        failure = provider.CurrentHostBindingError("INSTALL", "Plan differs from independently frozen expected digest")
        report = _report_v02(args.apply)
        report["error"] = failure.as_dict()
        failure.refusal_record = report
        raise failure
    report = install_plan_v02(plan, apply=args.apply)
    print(json.dumps({"passed": report["passed"], "state": report["state"], "report": plan["report"]}))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        provider._digest(args.plan_sha256, "SELECTION")
        plan, binding = provider._read(args.plan, 16 * 1024 * 1024, category="INSTALL")
        if type(plan) is dict and plan.get("schema") == SCHEMA_V02:
            return _main_v02(plan, binding, args)
        _require(binding["sha256"] == args.plan_sha256, "Plan differs from independently frozen expected digest")
        _require(plan.get("purpose") != "isolated-control", "Isolated controls cannot install operational inputs through the CLI")
        report = install_plan(plan, apply=args.apply)
        print(json.dumps({"passed": report["passed"], "state": report["state"], "report": plan["report"]}))
        return 0
    except provider.CurrentHostBindingError as exc:
        print(json.dumps({"passed": False, "error": exc.as_dict(), "refusal_record": getattr(exc, "refusal_record", None)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
