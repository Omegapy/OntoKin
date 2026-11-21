#!/usr/bin/env python3
"""Safely stage a separately approved current-host readback input tree.

Dry-run is the default. This tool never executes Node, ldd or recovered files.
The plan and its complete archive inventory must be frozen independently before
use. Installation is absent-or-complete-exact with Linux atomic no-replace
publication. Runtime qualification remains a separate explicitly selected gate.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from prototypes.static_tray_v01 import current_host_readback_v01 as provider

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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        provider._digest(args.plan_sha256, "SELECTION")
        plan, binding = provider._read(args.plan, 16 * 1024 * 1024, category="INSTALL")
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
