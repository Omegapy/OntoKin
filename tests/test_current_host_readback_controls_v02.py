"""Independently frozen controls of gate MI for ontokin.current-host-readback/0.2.0 (darwin-arm64-v1).

C271-P33, worker W6, the independent control author, who wrote none of the implementation. Every
expected outcome comes from the adopted contract (docs/engineering/localized-repair-c271/
macos-contract-design-p31/CONTRACT.md and CONTRACT.json) as amended by P33-AMENDMENT-001 (design
revision 4), from the implementation plan's control assignment and from the Director's decisions.
docs/engineering/localized-repair-c271/macos-implementation-p33/CONTROLS-FROZEN.json records each
case's exact inputs, label, entry point, expected outcome, start counts, post-test checks and sources;
CONTROLS-REFREEZE-001.json beside it records the cases refrozen since, and why.
One test method is one case, named test_mcNN_<case>; its docstring starts with its label.

Labels. "Real": the code under test runs with no boundary substituted; the inputs may be synthetic,
and the driver cases' one-stage plan is such an input. "Simulated": one named boundary is made to
produce the case's condition. "Mocked": a named component is replaced by a stand-in, as the
contract labels MC10 and the case of MC30 without the variable; the 0.2.0 provider then labels its
own records "mocked".

Starts. No test starts Node, ldd or codesign. The supervisor controls MC12, MC13 and MC37 to MC39 start
Python children only, as sys.executable -I -S -B -c, and the teardown of each such test removes every
process it started, escaped descendants included. Their post-test checks apply the amended rule: a
group probe that answers EPERM means present. MC19 starts Git through a logging stand-in executable on
a synthetic repository. The driver controls start the driver's own unit-stage children (Python, -I -S
-B -c) and, in an ordinary run, the driver's read-only Git metadata reads of a temporary directory.
The driver's environment record reads platform.platform(), which starts uname -p and file -b on its
first call in a process only: MC21's driver cases mock that metadata leaf (refreeze 001), and MC22
counts only its unit and Node starts. Every other test starts nothing, and a guard fails it if it tries.

Temporary directories are resolved (realpath). No machine path is hard-coded.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import ctypes
import errno
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import plistlib
import re
import select
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import time
import tokenize
from types import SimpleNamespace
import unittest
from unittest import mock

from prototypes.static_tray_v01 import current_host_observation_v02 as observation
from prototypes.static_tray_v01 import current_host_readback_v01 as facade
from prototypes.static_tray_v01 import current_host_readback_v02 as provider
from prototypes.static_tray_v01 import format_check
from prototypes.static_tray_v01 import supervisor as original
from prototypes.static_tray_v01 import supervisor_darwin_v01 as darwin
from tools import check_local
from tools import prepare_current_host_readback as preparer


# ---------------------------------------------------------------------------
# Values fixed by the contract, the amendment and the plan (CONTROLS-FROZEN.json gives the sources)
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "ontokin.current-host-readback/0.2.0"
NODE_VERSION = "v24.22.1"
NODE_RELEASE = "node-v24.22.1-darwin-arm64"
NODE_MEMBER = NODE_RELEASE + "/bin/node"
NODE_ARCHIVE_NAME = NODE_RELEASE + ".tar.gz"
NODE_ARCHIVE_PIN = "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"
CHECKSUM_FILE = {"url": "https://nodejs.org/dist/v24.22.1/SHASUMS256.txt",
                 "sha256": "fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4", "size_bytes": 3171}
DECLARED_ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
                        "UV_THREADPOOL_SIZE": "2"}
CF_NAME = "__CF_USER_TEXT_ENCODING"
CF_VALUE = "0x1F5:0x0:0x0"
ORDINARY_REASON = "No approved current-host readback selection: ordinary run, not a qualification"
# The driver's environment record reads platform.platform(); MC21's driver cases mock that metadata leaf with
# the value the project's driver tests give it (113e1b85). Refreeze 001, C-02.
PLATFORM_METADATA_LEAF = "mocked platform metadata leaf"
DESCENDANT_REASON = "Child exited while an owned descendant remained"
CEILING_REASON = "Owned process group cleanup exceeded stage or transaction ceiling"
CLEANUP_CEILING_MS = 2000
# supervisor.py stays byte-identical (AMENDMENT-001 section 3.1); this is its recorded SHA-256
# (docs/engineering/localized-repair-c271/libc-flags-p17/design/PROTECTED-SOURCES.json).
ORIGINAL_SUPERVISOR_SHA256 = "c47b84ab464e89d4c8673d7541679a45ddf3fc4816a906aff4546e074b4c5a10"
DRIVER_REMOVED_NAMES = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONBREAKPOINT",
                        "PYTHONUSERBASE", "PYTHONPYCACHEPREFIX", "LD_PRELOAD", "LD_LIBRARY_PATH", "NODE_OPTIONS",
                        "NODE_PATH", "__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE")
CONFIG_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG"
DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
CONTRACT_MD = "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md"
ADOPTION_RECORD = "docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json"
INSTALL_SCHEMA = "ontokin.current-host-readback-install/0.2.0"
INSTALL_RESULT_SCHEMA = "ontokin.current-host-readback-install-result/0.2.0"
NODE_SOURCE_SCHEMA = "ontokin.current-host-readback-node-source/0.2.0"
SOURCE_SCHEMA = "ontokin.current-host-readback-source/0.2.0"
DEPENDENCIES_SCHEMA = "ontokin.current-host-readback-dependencies/0.2.0"
CONFIG_SCHEMA = "ontokin.current-host-readback-config/0.2.0"
PLAN_SCHEMA = "ontokin.current-host-readback-observation-plan/0.2.0"
ZERO_PREPARATION_STARTS = {"node": 0, "ldd": 0, "checkers": 0}
PYTHON_CHILD = (sys.executable, "-I", "-S", "-B", "-c")
BINDING_ERRORS = (facade.CurrentHostBindingError, provider.CurrentHostBindingError)
SIGNATURE = {"status": "not_performed", "detail": "Synthetic control archive of gate MI; no release signature exists."}
SUPERVISOR_PATH = ROOT / "prototypes/static_tray_v01/supervisor.py"
DARWIN_SUPERVISOR_PATH = ROOT / "prototypes/static_tray_v01/supervisor_darwin_v01.py"
PROBE_PATH = ROOT / "prototypes/static_tray_v01/current_host_readback_v02.mjs"
READBACK_TESTS = ROOT / "tests/test_static_tray_readback_v01.py"
ORIGINAL_RECEIPT_KEYS = {"argv", "cwd", "environment", "label", "start_monotonic", "pid", "process_group",
                         "returncode", "observed_log_bytes", "retained_log_bytes", "cleanup", "handles_closed",
                         "error", "end_monotonic"}
PASSED_CLEANUP_KEYS = {"passed", "process_group_absent", "reaped", "elapsed_ms"}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    """Sorted keys, compact separators, ASCII only: the canonical JSON bytes of plan section 4.2."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def write(path, data, mode=0o644):
    """Create or replace one file with exactly these bytes and this mode."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        os.unlink(path)
    path.write_bytes(data)
    os.chmod(path, mode)
    return path


def binding(path):
    data = Path(path).read_bytes()
    return {"sha256": sha256(data), "size_bytes": len(data), "mode": oct(stat.S_IMODE(os.lstat(path).st_mode))}


def descriptor(path):
    return {"path": str(path), **binding(path)}


def evidence(case, **values):
    """One line of execution evidence on stderr, kept in the Director's retained log."""
    sys.stderr.write("CONTROL-EVIDENCE " + json.dumps({"case": case, **values}, sort_keys=True, default=str) + "\n")


def read_numbers(path):
    try:
        text = Path(path).read_text(encoding="ascii")
        return [int(part) for part in text.split()]
    except (OSError, ValueError):
        return None


def snapshot(root):
    """Every entry under root, never following a link: kind, mode, inode, link count, and bytes or target."""
    root = str(root)
    if not os.path.lexists(root):
        return None

    def row(path):
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            return ("symlink", os.readlink(path), info.st_ino)
        if stat.S_ISDIR(info.st_mode):
            return ("directory", oct(stat.S_IMODE(info.st_mode)), info.st_ino)
        if stat.S_ISREG(info.st_mode):
            return ("file", oct(stat.S_IMODE(info.st_mode)), info.st_ino, info.st_nlink,
                    sha256(Path(path).read_bytes()))
        return ("other", oct(info.st_mode), info.st_ino)
    rows = {".": row(root)}
    if rows["."][0] == "directory":
        for parent, directories, files in os.walk(root):
            for name in directories + files:
                path = os.path.join(parent, name)
                rows[os.path.relpath(path, root)] = row(path)
    return rows


def tree_shape(root):
    """snapshot without inodes and link counts: kinds, modes, and bytes or link targets."""
    shape = {}
    for rel, value in (snapshot(root) or {}).items():
        if value[0] == "file":
            shape[rel] = ("file", value[1], value[4])
        else:
            shape[rel] = value[:2]
    return shape


def wait_until(predicate, seconds):
    deadline = time.monotonic() + seconds
    while True:
        if predicate():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


# ---------------------------------------------------------------------------
# Synthetic Mach-O bytes (<mach-o/loader.h>); never executed
# ---------------------------------------------------------------------------

LC_REQ_DYLD = 0x80000000
LC = {"LC_SYMTAB": 0x2, "LC_DYSYMTAB": 0xB, "LC_LOAD_DYLIB": 0xC, "LC_ID_DYLIB": 0xD, "LC_LOAD_DYLINKER": 0xE,
      "LC_LOAD_WEAK_DYLIB": 0x18 | LC_REQ_DYLD, "LC_SEGMENT_64": 0x19, "LC_UUID": 0x1B,
      "LC_RPATH": 0x1C | LC_REQ_DYLD, "LC_CODE_SIGNATURE": 0x1D, "LC_REEXPORT_DYLIB": 0x1F | LC_REQ_DYLD,
      "LC_LOAD_UPWARD_DYLIB": 0x23 | LC_REQ_DYLD, "LC_VERSION_MIN_MACOSX": 0x24, "LC_FUNCTION_STARTS": 0x26,
      "LC_DYLD_ENVIRONMENT": 0x27, "LC_MAIN": 0x28 | LC_REQ_DYLD, "LC_DATA_IN_CODE": 0x29,
      "LC_SOURCE_VERSION": 0x2A, "LC_LINKER_OPTION": 0x2D, "LC_BUILD_VERSION": 0x32,
      "LC_DYLD_EXPORTS_TRIE": 0x33 | LC_REQ_DYLD, "LC_DYLD_CHAINED_FIXUPS": 0x34 | LC_REQ_DYLD}
MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C
CPU_TYPE_X86_64 = 0x01000007
MH_EXECUTE, MH_DYLIB, MH_BUNDLE = 2, 6, 8


def load_command(name, payload=b""):
    cmd = LC[name] if isinstance(name, str) else name
    size = 8 + len(payload)
    padded = size + (-size) % 8
    return struct.pack("<II", cmd, padded) + payload + b"\0" * (padded - size)


def path_command(name, path):
    """LC_LOAD_DYLINKER, LC_RPATH and LC_DYLD_ENVIRONMENT: one string at offset 12."""
    return load_command(name, struct.pack("<I", 12) + path.encode("ascii") + b"\0")


def dylib_command(name, path):
    """A dylib_command: name offset 24, timestamp, current and compatibility versions, then the path."""
    return load_command(name, struct.pack("<IIII", 24, 2, 0x10000, 0x10000) + path.encode("ascii") + b"\0")


def segment_command(name, fileoff=0, filesize=0):
    return load_command("LC_SEGMENT_64", name.encode("ascii").ljust(16, b"\0")
                        + struct.pack("<QQQQiiII", 0, 0x4000, fileoff, filesize, 5, 5, 0, 0))


def linkedit_command(name):
    return load_command(name, struct.pack("<II", 0, 0))


def node_commands(*extra, dylinker="/usr/lib/dyld"):
    """Only allow-listed commands (contract section 7), with system dylibs only."""
    return [segment_command("__PAGEZERO"), segment_command("__TEXT", 0, 256), segment_command("__LINKEDIT"),
            linkedit_command("LC_DYLD_CHAINED_FIXUPS"), linkedit_command("LC_DYLD_EXPORTS_TRIE"),
            load_command("LC_SYMTAB", struct.pack("<IIII", 0, 0, 0, 0)), load_command("LC_DYSYMTAB", b"\0" * 72),
            path_command("LC_LOAD_DYLINKER", dylinker), load_command("LC_UUID", bytes(range(16))),
            load_command("LC_BUILD_VERSION", struct.pack("<IIII", 1, 0x000E0000, 0x000F0000, 0)),
            load_command("LC_SOURCE_VERSION", struct.pack("<Q", 0)),
            load_command("LC_MAIN", struct.pack("<QQ", 0x200, 0)),
            dylib_command("LC_LOAD_DYLIB", "/usr/lib/libSystem.B.dylib"),
            dylib_command("LC_LOAD_DYLIB", "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation"),
            dylib_command("LC_LOAD_WEAK_DYLIB", "/usr/lib/libc++.1.dylib"), *extra,
            linkedit_command("LC_FUNCTION_STARTS"), linkedit_command("LC_DATA_IN_CODE"),
            linkedit_command("LC_CODE_SIGNATURE")]


def macho(commands, *, filetype=MH_EXECUTE, cputype=CPU_TYPE_ARM64, pad=4096):
    body = b"".join(commands)
    return (struct.pack("<8I", MH_MAGIC_64, cputype, 0, filetype, len(commands), len(body), 0x00200085, 0)
            + body + b"\0" * pad)


def dylib_image(identity, references=(), rpaths=()):
    commands = [dylib_command("LC_ID_DYLIB", identity)]
    commands += [dylib_command("LC_LOAD_DYLIB", path) for path in references]
    commands += [path_command("LC_RPATH", path) for path in rpaths]
    return macho(commands, filetype=MH_DYLIB, pad=64)


def bundle_image(references, rpaths=()):
    commands = [dylib_command("LC_LOAD_DYLIB", path) for path in references]
    commands += [path_command("LC_RPATH", path) for path in rpaths]
    return macho(commands, filetype=MH_BUNDLE, pad=64)


NODE_EXECUTABLE = macho(node_commands())
NODE_REFERENCES = ["/usr/lib/libSystem.B.dylib",
                   "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation",
                   "/usr/lib/libc++.1.dylib"]
NON_CONFORMING_EXECUTABLES = {
    "universal (fat) file": b"\xca\xfe\xba\xbe" + struct.pack(">I", 1) + b"\0" * 120,
    "32-bit Mach-O": struct.pack("<8I", 0xFEEDFACE, 12, 0, MH_EXECUTE, 0, 0, 0, 0) + b"\0" * 64,
    "big-endian 64-bit Mach-O": struct.pack(">8I", MH_MAGIC_64, CPU_TYPE_ARM64, 0, MH_EXECUTE, 0, 0, 0, 0) + b"\0" * 64,
    "x86_64 Mach-O": macho(node_commands(), cputype=CPU_TYPE_X86_64),
    "arm64 dylib": macho(node_commands(), filetype=MH_DYLIB),
    "truncated header": NODE_EXECUTABLE[:16],
    "script": b"#!/bin/sh\nexit 0\n"}


# Refreeze 002, review finding I-08: LC_DYLD_INFO_ONLY (<mach-o/loader.h>), which the contract's closed allow-list
# admits (section 7); the baseline above uses chained fixups and the exports trie instead.
LC_DYLD_INFO_ONLY = 0x22 | LC_REQ_DYLD


def dyld_info_only_command():
    """A dyld_info_command of 48 bytes: the rebase, bind, weak-bind, lazy-bind and export (offset, size) pairs."""
    return load_command(LC_DYLD_INFO_ONLY, struct.pack("<10I", *([0] * 10)))


def node_commands_with_dyld_info():
    """The baseline's commands with LC_DYLD_INFO_ONLY in place of LC_DYLD_CHAINED_FIXUPS and LC_DYLD_EXPORTS_TRIE."""
    replaced = {linkedit_command("LC_DYLD_CHAINED_FIXUPS"), linkedit_command("LC_DYLD_EXPORTS_TRIE")}
    commands = node_commands()
    position = next(index for index, command in enumerate(commands) if command in replaced)
    kept = [command for command in commands if command not in replaced]
    return kept[:position] + [dyld_info_only_command()] + kept[position:]


# ---------------------------------------------------------------------------
# Synthetic archives with the official member names; never executed or extracted by the controls
# ---------------------------------------------------------------------------

TAR_TYPES = {"file": tarfile.REGTYPE, "directory": tarfile.DIRTYPE, "symlink": tarfile.SYMTYPE,
             "hardlink": tarfile.LNKTYPE, "fifo": tarfile.FIFOTYPE, "character-device": tarfile.CHRTYPE,
             "block-device": tarfile.BLKTYPE}


def member(kind, name, mode, data=b"", target=None):
    return {"kind": kind, "name": name, "mode": mode, "data": data, "target": target}


def write_archive(path, members):
    with tarfile.open(path, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for item in members:
            info = tarfile.TarInfo(item["name"])
            info.type, info.mode, info.mtime = TAR_TYPES[item["kind"]], item["mode"], 0
            if item["kind"] in ("symlink", "hardlink"):
                info.linkname = item["target"]
            if item["kind"].endswith("device"):
                info.devmajor, info.devminor = 1, 3
            if item["kind"] == "file":
                info.size = len(item["data"])
                archive.addfile(info, io.BytesIO(item["data"]))
            else:
                archive.addfile(info)
    os.chmod(path, 0o600)
    return Path(path)


def node_members(executable=NODE_EXECUTABLE):
    """The official layout's names, with two declared in-archive links (contract section 3, item 4)."""
    r = NODE_RELEASE
    return [member("directory", r, 0o755), member("directory", r + "/bin", 0o755),
            member("file", NODE_MEMBER, 0o755, executable),
            member("symlink", r + "/bin/npm", 0o755, target="../lib/node_modules/npm/bin/npm-cli.js"),
            member("symlink", r + "/bin/npx", 0o755, target="../lib/node_modules/npm/bin/npx-cli.js"),
            member("directory", r + "/lib", 0o755), member("directory", r + "/lib/node_modules", 0o755),
            member("directory", r + "/lib/node_modules/npm", 0o755),
            member("directory", r + "/lib/node_modules/npm/bin", 0o755),
            member("file", r + "/lib/node_modules/npm/bin/npm-cli.js", 0o755, b"// synthetic npm entry; never executed\n"),
            member("file", r + "/lib/node_modules/npm/bin/npx-cli.js", 0o755, b"// synthetic npx entry; never executed\n"),
            member("file", r + "/README.md", 0o644, b"Synthetic control archive of gate MI.\n")]


def node_inventory(members):
    """The frozen member inventory: name to kind, size, mode and link target (contract section 3, item 3)."""
    return {item["name"]: {"kind": item["kind"], "size_bytes": len(item["data"]) if item["kind"] == "file" else 0,
                           "mode": oct(item["mode"]),
                           "link_target": item["target"] if item["kind"] == "symlink" else None}
            for item in members}


def node_source_bytes(archive, members, executable, signature):
    """NODE-SOURCE.json as plan section 4.2 fixes it, built here independently of the preparer."""
    return canonical({"schema": NODE_SOURCE_SCHEMA, "contract": CONTRACT,
                      "archive": {"name": NODE_ARCHIVE_NAME, "sha256": archive["sha256"],
                                  "size_bytes": archive["size_bytes"]},
                      "checksum_file": dict(CHECKSUM_FILE), "signature_check": dict(signature),
                      "member_inventory_sha256": sha256(canonical(members)),
                      "extracted": {"member": NODE_MEMBER, "path": "bin/node", "sha256": executable["sha256"],
                                    "size_bytes": executable["size_bytes"], "mode": executable["mode"]}})


DEPENDENCY_PREFIX = "receiving/"
DEPENDENCY_FILES = {
    "validator/package/package.json": b'{"name":"gltf-validator","version":"2.0.0-dev.3.10"}\n',
    "validator/package/index.js": b"// synthetic validator entry of the gate MI controls; never executed\n",
    "indexer-view/three/package.json": b'{"name":"three","version":"0.186.1"}\n'}
DEPENDENCY_DIRECTORIES = ("validator", "validator/package", "indexer-view", "indexer-view/three")
DEPENDENCY_NOTICE = DEPENDENCY_PREFIX + "NOTICE.txt"


def dependency_members():
    rows = [member("directory", "receiving", 0o755)]
    rows += [member("directory", DEPENDENCY_PREFIX + name, 0o755) for name in DEPENDENCY_DIRECTORIES]
    rows += [member("file", DEPENDENCY_PREFIX + name, 0o644, data) for name, data in DEPENDENCY_FILES.items()]
    rows.append(member("file", DEPENDENCY_NOTICE, 0o644, b"Synthetic unmapped member of the reader archive.\n"))
    return rows


def dependency_inventory_rows(members):
    """P05 section 5's frozen rows for the reader archive: kind, size, digest, mode and target."""
    rows = {}
    for item in members:
        target = item["name"][len(DEPENDENCY_PREFIX):] if item["name"].startswith(DEPENDENCY_PREFIX) else None
        if item["name"] == DEPENDENCY_NOTICE:
            target = None
        if item["kind"] == "directory":
            rows[item["name"]] = {"kind": "directory", "size_bytes": 0, "sha256": None, "mode": oct(item["mode"]),
                                  "target": target}
        else:
            rows[item["name"]] = {"kind": item["kind"], "size_bytes": len(item["data"]), "sha256": sha256(item["data"]),
                                  "mode": oct(item["mode"]), "target": target}
    return rows


# ---------------------------------------------------------------------------
# Process helpers for the supervisor controls (AMENDMENT-001 section 4: EPERM means present)
# ---------------------------------------------------------------------------

def group_probe(pgid):
    """The raw answer of killpg(pgid, 0): 'present' (it returned), 'EPERM' or 'ESRCH'."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return "ESRCH"
    except PermissionError:
        return "EPERM"
    return "present"


def group_absent(pgid):
    """The amended post-test rule: only ESRCH is absence; an EPERM answer means present."""
    return group_probe(pgid) == "ESRCH"


def descendant_present(pid, session):
    """A reported descendant is present while a process with its pid is still in the owned session."""
    try:
        return os.getsid(pid) == session
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class OwnedProcesses:
    """Every process a control starts, and each descendant it reports; the teardown removes all of them."""

    def __init__(self, test):
        self.direct, self.groups, self.descendants = [], [], []
        test.addCleanup(self.teardown)

    def add_direct(self, process):
        self.direct.append(process)
        self.add_group(process.pid)

    def add_group(self, pid):
        if pid not in self.groups:
            self.groups.append(pid)

    def add_descendant(self, pid, session):
        if pid is not None and session is not None and (pid, session) not in self.descendants:
            self.descendants.append((pid, session))

    def remaining(self):
        rows = [("group", pgid, group_probe(pgid)) for pgid in self.groups if not group_absent(pgid)]
        rows += [("descendant", pid, "present") for pid, session in self.descendants
                 if descendant_present(pid, session)]
        return rows

    def kill_all(self):
        for pid, session in self.descendants:
            if descendant_present(pid, session):
                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.kill(pid, signal.SIGKILL)
        for pgid in self.groups:
            if not group_absent(pgid):
                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.killpg(pgid, signal.SIGKILL)
        for process in self.direct:
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
        for pgid in self.groups:
            # A direct child started inside run_process is this process's child: reap it if it was left.
            with contextlib.suppress(OSError):
                os.waitpid(pgid, os.WNOHANG)

    def teardown(self):
        deadline = time.monotonic() + 5
        while True:
            self.kill_all()
            left = self.remaining()
            if not left or time.monotonic() >= deadline:
                break
            time.sleep(0.02)
        for process in self.direct:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
        if left:
            raise AssertionError("Processes started by this control remain (an EPERM answer means present): %r"
                                 % (left,))


def wait_for_exit_without_reaping(pid, release, seconds=10):
    """Establish a process's exit through kqueue EVFILT_PROC with NOTE_EXIT, never reaping it.

    The filter is registered while the process cannot exit yet; release() then lets it exit. This is
    independent of the code under test (AMENDMENT-001, rows MC37 and MC38).
    """
    queue = select.kqueue()
    try:
        queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                                     flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                     fflags=select.KQ_NOTE_EXIT)], 0, 0)
        release()
        events = queue.control(None, 1, seconds)
    finally:
        queue.close()
    return [event for event in events
            if event.ident == pid and event.filter == select.KQ_FILTER_PROC and event.fflags & select.KQ_NOTE_EXIT]


class FakeLibSystem:
    """The sysctlbyname boundary of the Darwin precondition, simulated (contract section 5)."""

    def __init__(self, *, value=1, status=0, width=4, symbol=True):
        self.names = []
        if symbol:
            def sysctlbyname(name, oldp, oldlenp, newp, newlen):
                self.names.append(name)
                if status == 0:
                    oldp._obj.value = value
                    oldlenp._obj.value = width
                return status
            self.sysctlbyname = sysctlbyname


DESCENDANT_CODE = textwrap.dedent('''
    import os, time
    control = %r
    descendant = os.fork()
    if descendant == 0:
        null = os.open(os.devnull, os.O_RDWR)
        for target in (0, 1, 2):
            os.dup2(null, target)
        os.close(null)
        path = os.path.join(control, "descendant.pid")
        with open(path + ".tmp", "w") as stream:
            stream.write(str(os.getpid()))
        os.rename(path + ".tmp", path)
        time.sleep(15)
        os._exit(0)
    deadline = time.monotonic() + 10
    while not os.path.exists(os.path.join(control, "descendant.pid")) and time.monotonic() < deadline:
        time.sleep(0.01)
    os._exit(0)
    ''')

ESCAPE_CODE = textwrap.dedent('''
    import os, select, time
    control = %r
    def record(name, text):
        path = os.path.join(control, name)
        with open(path + ".tmp", "w") as stream:
            stream.write(text)
        os.rename(path + ".tmp", path)
    read_end, write_end = os.pipe()
    descendant = os.fork()
    if descendant == 0:
        null = os.open(os.devnull, os.O_RDWR)
        for target in (0, 1, 2):
            os.dup2(null, target)
        os.close(null)
        unreaped = os.fork()
        if unreaped == 0:
            os.close(write_end)
            os.read(read_end, 1)
            os._exit(0)
        os.close(read_end)
        queue = select.kqueue()
        queue.control([select.kevent(unreaped, filter=select.KQ_FILTER_PROC,
                                     flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                     fflags=select.KQ_NOTE_EXIT)], 0, 0)
        os.setpgid(0, 0)
        os.close(write_end)
        queue.control(None, 1, 10)
        record("escaped.pids", "%%d %%d" %% (os.getpid(), unreaped))
        time.sleep(20)
        os._exit(0)
    os.close(read_end)
    os.close(write_end)
    record("descendant.pid", str(descendant))
    deadline = time.monotonic() + 10
    while not os.path.exists(os.path.join(control, "escaped.pids")) and time.monotonic() < deadline:
        time.sleep(0.01)
    os._exit(0)
    ''')

SLEEPING_CODE = "import time\ntime.sleep(15)\n"
STDIN_CODE = "import sys\nsys.stdin.buffer.read()\n"


# ---------------------------------------------------------------------------
# Source helpers
# ---------------------------------------------------------------------------

def function_source(path, name):
    """The exact source lines of one top-level function, read from the file by path."""
    text = Path(path).read_text(encoding="utf-8")
    nodes = [node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise AssertionError("Expected exactly one top-level function %s in %s" % (name, path))
    lines = text.splitlines(keepends=True)
    return "".join(lines[nodes[0].lineno - 1:nodes[0].end_lineno])


def token_rows(source):
    """Every token, comments, docstrings, NL, NEWLINE, INDENT and DEDENT included, by type and text."""
    return [(token.type, token.string) for token in tokenize.generate_tokens(io.StringIO(source).readline)]


def class_test_methods(path, class_name):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return [item.name for item in node.body
                    if isinstance(item, ast.FunctionDef) and item.name.startswith("test_")]
    raise AssertionError("No class " + class_name + " in " + str(path))


ORIGINAL_PRECONDITION = ('    libc = ctypes.CDLL(None, use_errno=True)\n'
                         '    if libc.prctl(36, 1, 0, 0, 0) != 0:\n'
                         '        raise Stop("OTRAY-E-BACKEND", "Cannot establish Linux descendant reaping")\n')
ORIGINAL_SEND_CLAUSE = "except ProcessLookupError:"
AMENDED_SEND_CLAUSE = "except (ProcessLookupError, PermissionError):"
ORIGINAL_PROBE_CLAUSE = "    except ProcessLookupError:\n"
AMENDED_PROBE_CLAUSE = "    except PermissionError:\n        return True\n    except ProcessLookupError:\n"

# MC11: the scan rule of contract section 5 ("No descendant"); its limit: a scan of names cannot exclude
# every dynamic route.
PROCESS_CREATION_PATTERNS = (("child_process", re.compile(r"child_process")),
                             ("cluster", re.compile(r"(?<![\w$])cluster(?![\w$])")),
                             ("worker_threads", re.compile(r"worker_threads")),
                             ("process.dlopen", re.compile(r"dlopen")))
DYNAMIC_PATTERNS = (("eval", re.compile(r"eval")), ("Function", re.compile(r"Function")),
                    ("createRequire", re.compile(r"createRequire")))
CALL_PATTERNS = (("require-call", re.compile(r"(?<![\w$.])require\s*\(")),
                 ("import-call", re.compile(r"(?<![\w$.])import\s*\(")))
LITERAL_ARGUMENT = re.compile(r"""\s*(['"])([^'"\\]*)\1\s*\)""")
STATIC_SPECIFIER = re.compile(r"""^\s*(?:import|export)\b[^'";]*?\bfrom\s*(['"])([^'"]+)\1|^\s*import\s*(['"])([^'"]+)\3""")
# The reviewed hits of the 0.2.0 probe (CONTROLS-FROZEN.json, MC11, review of each construct).
MC11_REVIEWED_PROBE_DYNAMIC = (
    ("createRequire", "import { createRequire } from 'node:module';"),
    ("createRequire", "const require = createRequire(import.meta.url);"),
    ("require-call", "const validator = require(manifest.validator_entry);"),
    ("Function", "externalResourceFunction: async () => { throw Error('External resources are forbidden'); }"),
    ("import-call", "const THREE = await import(pathToFileURL(manifest.three_entry).href);"),
    ("import-call", "const { GLTFLoader } = await import(pathToFileURL(manifest.gltf_loader_entry).href);"))
MC11_REVIEWED_PROBE_SPECIFIERS = ("node:fs", "node:path", "node:crypto", "node:module", "node:url", "node:url",
                                  "node:os")


def scan_javascript(text):
    """The MC11 scan of one JavaScript file: process-creation names, dynamic constructs, static specifiers."""
    found = {"process_creation": [], "dynamic": [], "static_specifiers": []}
    for line in text.splitlines():
        stripped = line.strip()
        for kind, pattern in PROCESS_CREATION_PATTERNS:
            found["process_creation"] += [(kind, stripped) for _ in pattern.finditer(line)]
        for kind, pattern in DYNAMIC_PATTERNS:
            found["dynamic"] += [(kind, stripped) for _ in pattern.finditer(line)]
        for kind, pattern in CALL_PATTERNS:
            for match in pattern.finditer(line):
                literal = LITERAL_ARGUMENT.match(line, match.end())
                if literal is not None:
                    found["static_specifiers"].append(literal.group(2))
                else:
                    found["dynamic"].append((kind, stripped))
        static = STATIC_SPECIFIER.match(line)
        if static is not None:
            found["static_specifiers"].append(static.group(2) or static.group(4))
    return found


# ---------------------------------------------------------------------------
# Base case
# ---------------------------------------------------------------------------

class ControlCase(unittest.TestCase):
    """A resolved temporary directory per test; a guarded class fails any process start."""

    GUARDED = True

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        parent = os.path.realpath(tempfile.gettempdir())
        self.base = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="ontokin-w6-", dir=parent)))
        self.assertEqual(str(self.base), os.path.realpath(str(self.base)), "the temporary directory is not resolved")
        self.counter = 0
        if self.GUARDED:
            self.forbid_process_starts()

    def directory(self, stem):
        self.counter += 1
        path = self.base / ("%s-%d" % (stem, self.counter))
        path.mkdir()
        return path

    def forbid_process_starts(self):
        guards = []
        for name in ("Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput"):
            guards.append(self.stack.enter_context(mock.patch.object(
                subprocess, name, side_effect=AssertionError("process start: subprocess." + name))))
        for name in ("system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp", "execv", "execve",
                     "execvp", "execvpe", "spawnv", "spawnve", "spawnvp", "spawnvpe"):
            if hasattr(os, name):
                guards.append(self.stack.enter_context(mock.patch.object(
                    os, name, side_effect=AssertionError("process start: os." + name))))
        self.guards = guards
        self.addCleanup(self.assert_no_process_start)

    def assert_no_process_start(self):
        self.assertEqual([guard.call_count for guard in self.guards], [0] * len(self.guards),
                         "a process start was attempted")


# ---------------------------------------------------------------------------
# MC01 to MC05, MC15, MC16, MC34, MC35: the 0.2.0 preparer (contract sections 3 and 6)
# ---------------------------------------------------------------------------

class PreparerFixtures:
    """Builders and assertions of the preparer controls; entry point install_plan_v02, which starts nothing."""

    def node_case(self, archive_members=None, *, declared=None, executable=NODE_EXECUTABLE, frozen=None, edit=None):
        baseline = node_members(executable)
        archive_members = baseline if archive_members is None else archive_members
        declared = baseline if declared is None else declared
        archive_path = write_archive(self.directory("node-archive") / NODE_ARCHIVE_NAME, archive_members)
        archive = {"path": str(archive_path), **binding(archive_path)}
        parent, reports = self.directory("destination-parent"), self.directory("reports")
        executable_binding = ({"sha256": sha256(executable), "size_bytes": len(executable), "mode": "0o755"}
                              if frozen is None else dict(frozen))
        plan = {"schema": INSTALL_SCHEMA, "contract": CONTRACT, "purpose": "selected-node",
                "source_root": str(preparer.ROOT), "archive": archive, "destination": str(parent / "runtime"),
                "root_mode": "0o755", "files": {"bin/node": executable_binding}, "directories": {"bin": "0o755"},
                "members": node_inventory(declared), "node_source": {"signature_check": dict(SIGNATURE)},
                "report": str(reports / "install-result.json")}
        if edit is not None:
            edit(plan)
        raw = node_source_bytes(plan["archive"], plan["members"], plan["files"]["bin/node"],
                                plan["node_source"]["signature_check"])
        plan["files"]["NODE-SOURCE.json"] = {"sha256": sha256(raw), "size_bytes": len(raw), "mode": "0o644"}
        pins = preparer.SyntheticPins(
            node_archive_sha256=archive["sha256"],
            dependency_archive_sha256=sha256(b"unused synthetic dependency archive pin"),
            dependency_files={"validator/package/package.json": {"sha256": sha256(b"unused synthetic pin"),
                                                                 "size_bytes": 20}})
        return SimpleNamespace(plan=plan, pins=pins, raw=raw, executable=executable, parent=parent,
                               destination=parent / "runtime", archive=archive_path)

    def dependency_case(self, archive_members=None, *, edit=None):
        baseline = dependency_members()
        archive_members = baseline if archive_members is None else archive_members
        archive_path = write_archive(self.directory("reader-archive") / "c195-synthetic.tar.gz", archive_members)
        archive = {"path": str(archive_path), **binding(archive_path)}
        files = {name: {"sha256": sha256(data), "size_bytes": len(data), "mode": "0o644"}
                 for name, data in DEPENDENCY_FILES.items()}
        parent, reports = self.directory("destination-parent"), self.directory("reports")
        plan = {"schema": INSTALL_SCHEMA, "contract": CONTRACT, "purpose": "retained-dependencies",
                "source_root": str(preparer.ROOT), "archive": archive, "destination": str(parent / "readers"),
                "root_mode": "0o755", "files": files,
                "directories": {name: "0o755" for name in DEPENDENCY_DIRECTORIES},
                "members": dependency_inventory_rows(baseline), "node_source": None,
                "report": str(reports / "install-result.json")}
        if edit is not None:
            edit(plan)
        pins = preparer.SyntheticPins(
            node_archive_sha256=sha256(b"unused synthetic node archive pin"),
            dependency_archive_sha256=archive["sha256"],
            dependency_files={name: {"sha256": row["sha256"], "size_bytes": row["size_bytes"]}
                              for name, row in files.items()})
        return SimpleNamespace(plan=plan, pins=pins, parent=parent, destination=parent / "readers",
                               archive=archive_path)

    def install(self, case, *, apply=True, seam=True, report=None):
        plan = copy.deepcopy(case.plan)
        if report is not None:
            plan["report"] = str(report)
        try:
            return preparer.install_plan_v02(plan, apply=apply, synthetic_pins=case.pins if seam else None), None
        except BINDING_ERRORS as exc:
            return None, exc

    @contextlib.contextmanager
    def tar_reads(self):
        opened, extracted = [], []
        real_open, real_extract = tarfile.open, tarfile.TarFile.extractfile

        def spy_open(*args, **kwargs):
            opened.append(True)
            return real_open(*args, **kwargs)

        def spy_extract(archive, item, *args, **kwargs):
            extracted.append(getattr(item, "name", item))
            return real_extract(archive, item, *args, **kwargs)
        with mock.patch.object(tarfile, "open", spy_open), mock.patch.object(tarfile.TarFile, "extractfile", spy_extract):
            yield SimpleNamespace(opened=opened, extracted=extracted)

    @contextlib.contextmanager
    def no_fallback_rename(self):
        spies = {}
        with contextlib.ExitStack() as stack:
            for owner, name in ((os, "rename"), (os, "replace"), (os, "renames"), (os, "link"), (os, "symlink"),
                                (shutil, "move")):
                spies[owner.__name__ + "." + name] = stack.enter_context(
                    mock.patch.object(owner, name, side_effect=AssertionError("fallback: " + name)))
            yield spies

    def assert_no_fallback(self, spies):
        self.assertEqual({name: spy.call_count for name, spy in spies.items()}, {name: 0 for name in spies},
                         "a fallback rename, move or link was attempted")

    def assert_refused(self, result, error):
        self.assertIsNone(result, "the preparation was accepted")
        self.assertIsInstance(error, BINDING_ERRORS)
        self.assertEqual(error.state, "REJECTED", error.as_dict())
        record = error.refusal_record
        self.assertEqual(record["schema"], INSTALL_RESULT_SCHEMA)
        self.assertIs(record["passed"], False)
        self.assertEqual(record["state"], "REJECTED")
        self.assertEqual(record["execution_counts"], ZERO_PREPARATION_STARTS)
        return record

    def assert_refused_nothing_extracted(self, case, result, error):
        record = self.assert_refused(result, error)
        self.assertEqual(os.listdir(case.parent), [], "a destination or a stage exists: something was extracted")
        return record

    def assert_ready(self, case, result, error):
        self.assertIsNone(error, error.as_dict() if error is not None else None)
        self.assertEqual(result["state"], "DRY_RUN_READY")
        self.assertIs(result["passed"], True)
        self.assertEqual(result["execution_counts"], ZERO_PREPARATION_STARTS)
        self.assertEqual(os.listdir(case.parent), [])

    def assert_node_installed(self, case, result, error):
        self.assertIsNone(error, error.as_dict() if error is not None else None)
        self.assertEqual(result["state"], "INSTALLED_EXACT")
        self.assertIs(result["passed"], True)
        self.assertEqual(result["execution_counts"], ZERO_PREPARATION_STARTS)
        self.assertEqual(tree_shape(case.destination), {
            ".": ("directory", "0o755"), "bin": ("directory", "0o755"),
            "bin/node": ("file", "0o755", sha256(case.executable)),
            "NODE-SOURCE.json": ("file", "0o644", sha256(case.raw))})

    def assert_baseline_node_ready(self):
        case = self.node_case()
        result, error = self.install(case, apply=False)
        self.assert_ready(case, result, error)

    def refuse_node_archive(self, extra=(), replace=None):
        """The baseline inventory is frozen; the archive gains or replaces members; nothing may be extracted."""
        baseline = node_members()
        archive_members = [replace.get(item["name"], item) if replace else item for item in baseline] + list(extra)
        case = self.node_case(archive_members, declared=baseline)
        with self.tar_reads() as reads:
            result, error = self.install(case)
        self.assert_refused_nothing_extracted(case, result, error)
        return reads


class PreparationControls(PreparerFixtures, ControlCase):
    """MC01 to MC05, MC15, MC16, MC34 and MC35 at tools/prepare_current_host_readback.install_plan_v02."""

    # MC01 ------------------------------------------------------------------

    def test_mc01_adopted_pin_archive_bytes_differ_refused_before_any_member_is_read(self):
        """Label: real (the adopted pin; a synthetic archive whose bytes differ from it).

        The plan names the adopted pin; the archive's bytes have another SHA-256. Refused before any
        member is read: the archive is never opened as a tar stream and nothing is extracted.
        """
        def adopted(plan):
            plan["archive"]["sha256"] = NODE_ARCHIVE_PIN
        case = self.node_case(edit=adopted)
        with self.tar_reads() as reads:
            result, error = self.install(case, seam=False)
        self.assert_refused_nothing_extracted(case, result, error)
        self.assertEqual(reads.opened, [])
        self.assertEqual(reads.extracted, [])

    def test_mc01_plan_naming_another_digest_than_the_pin_refused_before_the_archive_is_opened(self):
        """Label: real (the adopted pin; the plan names the synthetic archive's own digest)."""
        case = self.node_case()
        with self.tar_reads() as reads:
            result, error = self.install(case, seam=False)
        self.assert_refused_nothing_extracted(case, result, error)
        self.assertEqual(reads.opened, [])
        self.assertEqual(reads.extracted, [])

    def test_mc01_simulated_pin_archive_changed_after_freezing_refused_before_any_member_is_read(self):
        """Label: simulated (pin boundary: the SyntheticPins seam names the frozen digest).

        One byte of the archive changes after the plan froze its digest.
        """
        self.assert_baseline_node_ready()
        case = self.node_case()
        data = bytearray(case.archive.read_bytes())
        data[-1] ^= 0x01
        write(case.archive, bytes(data), 0o600)
        with self.tar_reads() as reads:
            result, error = self.install(case)
        self.assert_refused_nothing_extracted(case, result, error)
        self.assertEqual(reads.opened, [])
        self.assertEqual(reads.extracted, [])

    # MC02 ------------------------------------------------------------------

    def test_mc02_absolute_member_name_refuses_the_archive_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). An absolute member name in the archive."""
        self.assert_baseline_node_ready()
        self.refuse_node_archive(extra=[member("file", "/" + NODE_RELEASE + "/absolute.txt", 0o644, b"absolute\n")])

    def test_mc02_traversing_member_name_refuses_the_archive_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). A traversing member name in the archive."""
        self.assert_baseline_node_ready()
        for name in ("../escape.txt", NODE_RELEASE + "/../escape.txt", NODE_RELEASE + "/bin/../../escape.txt"):
            with self.subTest(name=name):
                self.refuse_node_archive(extra=[member("file", name, 0o644, b"traversing\n")])

    def test_mc02_duplicate_member_name_refuses_the_archive_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). The README member occurs twice."""
        self.assert_baseline_node_ready()
        self.refuse_node_archive(extra=[member("file", NODE_RELEASE + "/README.md", 0o644,
                                               b"Synthetic control archive of gate MI.\n")])

    def test_mc02_hard_link_member_refuses_the_archive_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). A hard-link member to bin/node."""
        self.assert_baseline_node_ready()
        self.refuse_node_archive(extra=[member("hardlink", NODE_RELEASE + "/bin/node-hardlink", 0o755,
                                               target=NODE_MEMBER)])

    def test_mc02_device_member_refuses_the_archive_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). A character and a block device member."""
        self.assert_baseline_node_ready()
        for kind in ("character-device", "block-device"):
            with self.subTest(kind=kind):
                self.refuse_node_archive(extra=[member(kind, NODE_RELEASE + "/device", 0o644)])

    def test_mc02_fifo_member_refuses_the_archive_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). A FIFO member."""
        self.assert_baseline_node_ready()
        self.refuse_node_archive(extra=[member("fifo", NODE_RELEASE + "/fifo", 0o644)])

    def test_mc02_undeclared_member_refuses_the_archive_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). A regular file the frozen inventory does not declare."""
        self.assert_baseline_node_ready()
        self.refuse_node_archive(extra=[member("file", NODE_RELEASE + "/UNDECLARED.txt", 0o644, b"undeclared\n")])

    def test_mc02_escaping_link_target_refuses_the_archive_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). A link whose target leaves the archive root."""
        self.assert_baseline_node_ready()
        for target in ("../../outside", "/absolute/target", "../.."):
            with self.subTest(target=target):
                self.refuse_node_archive(extra=[member("symlink", NODE_RELEASE + "/bin/escape", 0o755,
                                                       target=target)])

    def test_mc02_inventory_declaring_a_forbidden_member_is_refused_and_nothing_is_extracted(self):
        """Label: simulated (pin boundary: SyntheticPins). The frozen inventory itself declares a forbidden member."""
        self.assert_baseline_node_ready()
        forbidden = {
            "an absolute name": ("/" + NODE_RELEASE + "/absolute.txt",
                                 {"kind": "file", "size_bytes": 9, "mode": "0o644", "link_target": None}),
            "a traversing name": (NODE_RELEASE + "/../escape.txt",
                                  {"kind": "file", "size_bytes": 9, "mode": "0o644", "link_target": None}),
            "a hard link": (NODE_RELEASE + "/bin/node-hardlink",
                            {"kind": "hardlink", "size_bytes": 0, "mode": "0o755", "link_target": None}),
            "a FIFO": (NODE_RELEASE + "/fifo", {"kind": "fifo", "size_bytes": 0, "mode": "0o644", "link_target": None}),
            "a device": (NODE_RELEASE + "/device",
                         {"kind": "character-device", "size_bytes": 0, "mode": "0o644", "link_target": None}),
            "an escaping link target": (NODE_RELEASE + "/bin/escape",
                                        {"kind": "symlink", "size_bytes": 0, "mode": "0o755",
                                         "link_target": "../../outside"})}
        for label, (name, row) in forbidden.items():
            with self.subTest(label):
                def declare(plan, name=name, row=row):
                    plan["members"][name] = dict(row)
                case = self.node_case(edit=declare)
                result, error = self.install(case)
                self.assert_refused_nothing_extracted(case, result, error)

    # MC03 ------------------------------------------------------------------

    def test_mc03_declared_link_members_are_accepted_not_extracted_or_followed_in_a_dry_run(self):
        """Label: simulated (pin boundary: SyntheticPins). Declared links bin/npm and bin/npx; dry run."""
        case = self.node_case()
        links = sorted(name for name, row in case.plan["members"].items() if row["kind"] == "symlink")
        self.assertEqual(links, [NODE_RELEASE + "/bin/npm", NODE_RELEASE + "/bin/npx"])
        with self.tar_reads() as reads:
            result, error = self.install(case, apply=False)
        self.assert_ready(case, result, error)
        self.assertEqual(set(reads.extracted), {NODE_MEMBER}, "a member other than bin/node was read or followed")

    def test_mc03_real_install_extracts_only_bin_node_and_publishes_node_source(self):
        """Label: simulated (pin boundary: SyntheticPins); the publication is a real renamex_np call."""
        case = self.node_case()
        with self.tar_reads() as reads:
            result, error = self.install(case)
        self.assert_node_installed(case, result, error)
        self.assertEqual(set(reads.extracted), {NODE_MEMBER})
        self.assertEqual((case.destination / "bin/node").read_bytes(), case.executable)
        self.assertEqual((case.destination / "NODE-SOURCE.json").read_bytes(), case.raw)
        self.assertEqual(sorted(os.listdir(case.parent)), ["runtime"])

    def test_mc03_exact_existing_tree_is_reused_already_present_exact(self):
        """Label: simulated (pin boundary: SyntheticPins). A second preparation finds the exact tree."""
        case = self.node_case()
        result, error = self.install(case)
        self.assert_node_installed(case, result, error)
        before = snapshot(case.destination)
        with mock.patch.object(preparer, "rename_exclusive",
                               side_effect=AssertionError("a reuse must not publish")) as publication:
            again, failure = self.install(case, report=self.directory("reports") / "reuse.json")
        self.assertIsNone(failure, failure.as_dict() if failure is not None else None)
        self.assertEqual(again["state"], "ALREADY_PRESENT_EXACT")
        self.assertIs(again["passed"], True)
        self.assertEqual(again["execution_counts"], ZERO_PREPARATION_STARTS)
        self.assertEqual(publication.call_count, 0)
        self.assertEqual(snapshot(case.destination), before)

    # MC04 ------------------------------------------------------------------

    def test_mc04_node_member_missing_is_refused(self):
        """Label: simulated (pin boundary: SyntheticPins). bin/node absent from the archive."""
        self.assert_baseline_node_ready()
        baseline = node_members()
        without = [item for item in baseline if item["name"] != NODE_MEMBER]
        for label, archive_members, declared in (("absent from the archive and the inventory", without, without),
                                                 ("absent from the archive only", without, baseline)):
            with self.subTest(label):
                case = self.node_case(archive_members, declared=declared)
                result, error = self.install(case)
                self.assert_refused_nothing_extracted(case, result, error)

    def test_mc04_node_member_not_a_declared_regular_file_is_refused(self):
        """Label: simulated (pin boundary: SyntheticPins). bin/node is a link, a hard link or a directory."""
        self.assert_baseline_node_ready()
        baseline = node_members()

        def replaced(kind, **values):
            return [dict(item, kind=kind, data=b"", **values) if item["name"] == NODE_MEMBER else item
                    for item in baseline]
        variants = (("a declared symbolic link", replaced("symlink", target="../README.md"), None),
                    ("a hard link in the archive", replaced("hardlink", target=NODE_RELEASE + "/README.md"), baseline),
                    ("a declared directory", replaced("directory", mode=0o755), None))
        for label, archive_members, declared in variants:
            with self.subTest(label):
                case = self.node_case(archive_members, declared=archive_members if declared is None else declared)
                result, error = self.install(case)
                self.assert_refused_nothing_extracted(case, result, error)

    # MC05 ------------------------------------------------------------------

    def test_mc05_executable_not_thin_arm64_macho_is_refused_before_m1(self):
        """Label: simulated (pin boundary: SyntheticPins). The extracted member is not a thin arm64 Mach-O executable."""
        self.assert_baseline_node_ready()
        for label, data in NON_CONFORMING_EXECUTABLES.items():
            with self.subTest(label):
                case = self.node_case(executable=data)
                result, error = self.install(case)
                self.assert_refused_nothing_extracted(case, result, error)

    def test_mc05_executable_digest_or_size_other_than_the_frozen_plan_is_refused_before_m1(self):
        """Label: simulated (pin boundary: SyntheticPins). The frozen SHA-256 or size differs from the bytes."""
        self.assert_baseline_node_ready()
        for label, frozen in (("SHA-256 differs", {"sha256": sha256(b"another executable"),
                                                   "size_bytes": len(NODE_EXECUTABLE), "mode": "0o755"}),
                              ("size differs", {"sha256": sha256(NODE_EXECUTABLE),
                                                "size_bytes": len(NODE_EXECUTABLE) + 1, "mode": "0o755"})):
            with self.subTest(label):
                case = self.node_case(frozen=frozen)
                result, error = self.install(case)
                self.assert_refused_nothing_extracted(case, result, error)

    def test_mc05_frozen_executable_mode_other_than_the_extracted_mode_is_refused_before_m1(self):
        """Label: simulated (pin boundary: SyntheticPins). The plan freezes mode 0o700 for bin/node."""
        self.assert_baseline_node_ready()
        case = self.node_case(frozen={"sha256": sha256(NODE_EXECUTABLE), "size_bytes": len(NODE_EXECUTABLE),
                                      "mode": "0o700"})
        result, error = self.install(case)
        self.assert_refused_nothing_extracted(case, result, error)

    def test_mc05_simulated_staged_executable_mode_change_is_refused_before_publication(self):
        """Label: simulated (os.fchmod boundary gives the staged bin/node mode 0o700; pins through SyntheticPins)."""
        self.assert_baseline_node_ready()
        case = self.node_case()
        real_fchmod = os.fchmod

        def fchmod(fd, mode):
            return real_fchmod(fd, 0o700 if mode == 0o755 else mode)
        with mock.patch.object(os, "fchmod", fchmod), mock.patch.object(
                preparer, "rename_exclusive", side_effect=AssertionError("published")) as publication:
            result, error = self.install(case)
        self.assert_refused_nothing_extracted(case, result, error)
        self.assertEqual(publication.call_count, 0)

    # MC15 ------------------------------------------------------------------

    def test_mc15_real_renamex_np_refuses_an_existing_destination_and_leaves_it_untouched(self):
        """Label: real (renamex_np with RENAME_EXCL through the preparer's rename_exclusive)."""
        def empty(path):
            path.mkdir()

        def populated(path):
            write(path / "kept.txt", b"another writer's content\n")

        def regular(path):
            write(path, b"another writer's file\n")
        for label, prepare in (("an empty directory", empty), ("a populated directory", populated),
                               ("a regular file", regular)):
            with self.subTest(label):
                folder = self.directory("conflict")
                source, destination = folder / "staged", folder / "destination"
                write(source / "bin/node", NODE_EXECUTABLE, 0o755)
                prepare(destination)
                before_source, before_destination = snapshot(source), snapshot(destination)
                with self.assertRaises(OSError) as caught:
                    preparer.rename_exclusive(source, destination)
                self.assertEqual(caught.exception.errno, errno.EEXIST)
                self.assertEqual(snapshot(destination), before_destination, "the existing destination changed")
                self.assertEqual(snapshot(source), before_source)

    def test_mc15_real_conflict_destination_appearing_before_publication_is_refused_untouched(self):
        """Label: real (renamex_np); the other writer is this control, acting immediately before the call."""
        case = self.node_case()
        real = preparer.rename_exclusive
        calls, observed = [], {}

        def other_writer_then_publish(source, destination):
            calls.append(str(destination))
            write(Path(destination) / "other-writer.txt", b"content of another writer\n")
            observed["before"] = snapshot(destination)
            return real(source, destination)
        with mock.patch.object(preparer, "rename_exclusive", other_writer_then_publish), \
                self.no_fallback_rename() as fallbacks:
            result, error = self.install(case)
        record = self.assert_refused(result, error)
        self.assertEqual(calls, [str(case.destination)], "no retry")
        self.assertIn("destination_after_error", record, "no readback of the destination after the conflict")
        self.assertEqual(snapshot(case.destination), observed["before"], "the existing content was touched")
        self.assertEqual(sorted(os.listdir(case.parent)), ["runtime"], "the owned stage was not removed")
        self.assert_no_fallback(fallbacks)

    # MC16 ------------------------------------------------------------------

    def cross_volume_target(self):
        """A never-created name on the checkout's volume, while the temporary directory is on another volume."""
        checkout_device, temporary_device = os.stat(ROOT).st_dev, os.stat(self.base).st_dev
        self.assertNotEqual(checkout_device, temporary_device,
                            "the real failing call of MC16 needs the checkout and the temporary directory on two volumes")
        self.assertEqual(os.stat(ROOT.parent).st_dev, checkout_device)
        target = ROOT.parent / (".ontokin-w6-mc16-" + os.urandom(8).hex())
        self.assertFalse(os.path.lexists(target))

        def remove_if_created():
            if os.path.isdir(target) and not os.path.islink(target):
                shutil.rmtree(target)
            elif os.path.lexists(target):
                os.unlink(target)
        self.addCleanup(remove_if_created)
        return target

    def test_mc16_real_cross_volume_renamex_np_fails_and_there_is_no_fallback(self):
        """Label: real (a cross-volume renamex_np from the temporary directory to the checkout's volume)."""
        target = self.cross_volume_target()
        source = self.directory("staged")
        write(source / "bin/node", NODE_EXECUTABLE, 0o755)
        before = snapshot(source)
        with self.no_fallback_rename() as fallbacks:
            with self.assertRaises(OSError) as caught:
                preparer.rename_exclusive(source, target)
        self.assertEqual(caught.exception.errno, errno.EXDEV)
        self.assertFalse(os.path.lexists(target))
        self.assertEqual(snapshot(source), before)
        self.assert_no_fallback(fallbacks)

    def test_mc16_real_failing_call_inside_the_flow_is_refused_without_fallback(self):
        """Label: real (renamex_np fails with EXDEV); the control redirects the call's destination to the checkout's volume."""
        target = self.cross_volume_target()
        case = self.node_case()
        real = preparer.rename_exclusive
        calls = []

        def redirected(source, destination):
            calls.append(str(destination))
            return real(source, target)
        with mock.patch.object(preparer, "rename_exclusive", redirected), self.no_fallback_rename() as fallbacks:
            result, error = self.install(case)
        self.assert_refused_nothing_extracted(case, result, error)
        self.assertEqual(calls, [str(case.destination)], "no retry")
        self.assertFalse(os.path.lexists(target))
        self.assert_no_fallback(fallbacks)

    def enotsup_boundary(self):
        calls = []

        def renamex_np(source, destination, flags):
            calls.append((source, destination, flags))
            ctypes.set_errno(errno.ENOTSUP)
            return -1
        return calls, mock.patch.object(preparer, "_libsystem_renamex_np", return_value=renamex_np)

    def test_mc16_simulated_volume_without_rename_excl_support_fails_and_there_is_no_fallback(self):
        """Label: simulated (libSystem renamex_np boundary returns -1 with ENOTSUP)."""
        folder = self.directory("enotsup")
        source, destination = folder / "staged", folder / "destination"
        write(source / "bin/node", NODE_EXECUTABLE, 0o755)
        calls, boundary = self.enotsup_boundary()
        with boundary, self.no_fallback_rename() as fallbacks:
            with self.assertRaises(OSError) as caught:
                preparer.rename_exclusive(source, destination)
        self.assertEqual(caught.exception.errno, errno.ENOTSUP)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][2], 0x00000004, "the call does not carry RENAME_EXCL")
        self.assertFalse(os.path.lexists(destination))
        self.assertTrue((source / "bin/node").is_file())
        self.assert_no_fallback(fallbacks)

    def test_mc16_simulated_enotsup_inside_the_flow_is_refused_without_fallback(self):
        """Label: simulated (libSystem renamex_np boundary returns -1 with ENOTSUP; pins through SyntheticPins)."""
        case = self.node_case()
        calls, boundary = self.enotsup_boundary()
        with boundary, self.no_fallback_rename() as fallbacks:
            result, error = self.install(case)
        self.assert_refused_nothing_extracted(case, result, error)
        self.assertEqual(len(calls), 1, "no retry")
        self.assert_no_fallback(fallbacks)

    # MC34 ------------------------------------------------------------------

    def test_mc34_baseline_reader_archive_installs_exactly(self):
        """Label: simulated (pin boundary: SyntheticPins names the synthetic reader archive and files); real renamex_np."""
        case = self.dependency_case()
        result, error = self.install(case)
        self.assertIsNone(error, error.as_dict() if error is not None else None)
        self.assertEqual(result["state"], "INSTALLED_EXACT")
        expected = {".": ("directory", "0o755")}
        expected.update({name: ("directory", "0o755") for name in DEPENDENCY_DIRECTORIES})
        expected.update({name: ("file", "0o644", sha256(data)) for name, data in DEPENDENCY_FILES.items()})
        self.assertEqual(tree_shape(case.destination), expected)

    def refuse_reader_archive(self, extra=(), replace=None):
        baseline = dependency_members()
        archive_members = [replace.get(item["name"], item) if replace else item for item in baseline] + list(extra)
        case = self.dependency_case(archive_members)
        result, error = self.install(case)
        self.assert_refused_nothing_extracted(case, result, error)

    def notice_as(self, kind, **values):
        return {DEPENDENCY_NOTICE: dict(member(kind, DEPENDENCY_NOTICE, 0o644), **values)}

    def test_mc34_absolute_or_traversing_entry_refuses_before_extraction(self):
        """Label: simulated (pin boundary: SyntheticPins). An absolute or traversing entry in the reader archive."""
        for name in ("/receiving/absolute.js", "../escape.js", "receiving/../escape.js"):
            with self.subTest(name=name):
                self.refuse_reader_archive(extra=[member("file", name, 0o644, b"// escaping entry\n")])

    def test_mc34_duplicate_entry_refuses_before_extraction(self):
        """Label: simulated (pin boundary: SyntheticPins). A declared entry occurs twice."""
        self.refuse_reader_archive(extra=[member("file", DEPENDENCY_NOTICE, 0o644,
                                                 b"Synthetic unmapped member of the reader archive.\n")])

    def test_mc34_linked_entry_refuses_before_extraction(self):
        """Label: simulated (pin boundary: SyntheticPins). A declared file arrives as a symbolic or hard link."""
        for kind, target in (("symlink", "../outside"), ("hardlink", DEPENDENCY_PREFIX + "validator/package/index.js")):
            with self.subTest(kind=kind):
                self.refuse_reader_archive(replace=self.notice_as(kind, target=target))

    def test_mc34_special_entry_refuses_before_extraction(self):
        """Label: simulated (pin boundary: SyntheticPins). A declared file arrives as a FIFO or a device."""
        for kind in ("fifo", "character-device"):
            with self.subTest(kind=kind):
                self.refuse_reader_archive(replace=self.notice_as(kind))

    def test_mc34_unexpected_mode_refuses_before_extraction(self):
        """Label: simulated (pin boundary: SyntheticPins). An entry's mode differs from the frozen inventory."""
        for mode in (0o666, 0o4644):
            with self.subTest(mode=oct(mode)):
                self.refuse_reader_archive(replace={DEPENDENCY_NOTICE: member(
                    "file", DEPENDENCY_NOTICE, mode, b"Synthetic unmapped member of the reader archive.\n")})

    def test_mc34_inventory_declaring_links_special_entries_or_unexpected_modes_is_refused(self):
        """Label: simulated (pin boundary: SyntheticPins). The frozen reader inventory declares a forbidden row."""
        edits = {"a symbolic link": ("kind", "symlink"), "a FIFO": ("kind", "fifo"),
                 "a group-writable mode": ("mode", "0o664"), "a set-user-ID mode": ("mode", "0o4644")}
        for label, (key, value) in edits.items():
            with self.subTest(label):
                def declare(plan, key=key, value=value):
                    plan["members"][DEPENDENCY_NOTICE][key] = value
                case = self.dependency_case(edit=declare)
                result, error = self.install(case)
                self.assert_refused_nothing_extracted(case, result, error)
        with self.subTest("an absolute name"):
            def absolute(plan):
                plan["members"]["/receiving/absolute.js"] = {"kind": "file", "size_bytes": 3, "sha256": sha256(b"abs"),
                                                            "mode": "0o644", "target": None}
            case = self.dependency_case(edit=absolute)
            result, error = self.install(case)
            self.assert_refused_nothing_extracted(case, result, error)

    # MC35 ------------------------------------------------------------------

    def installed_node(self):
        case = self.node_case()
        result, error = self.install(case)
        self.assert_node_installed(case, result, error)
        return case

    def assert_existing_destination_refused_unrepaired(self, mutate, inaccessible=None):
        """Install exactly, change the destination, prepare again: refused; nothing repaired or replaced."""
        case = self.installed_node()
        mutate(case)
        before = snapshot(case.destination)
        restore = None
        if inaccessible is not None:
            path, restore = inaccessible(case)
            os.chmod(path, 0)
            self.addCleanup(lambda: os.path.lexists(path) and os.chmod(path, restore))
        with mock.patch.object(preparer, "rename_exclusive",
                               side_effect=AssertionError("an existing destination was published over")) as publication:
            result, error = self.install(case, report=self.directory("reports") / "again.json")
        if inaccessible is not None:
            self.assertEqual(stat.S_IMODE(os.lstat(path).st_mode), 0, "the inaccessible entry was repaired")
            os.chmod(path, restore)
        self.assert_refused(result, error)
        self.assertEqual(publication.call_count, 0)
        self.assertEqual(snapshot(case.destination), before, "the existing destination was repaired or replaced")
        self.assertEqual(sorted(os.listdir(case.parent)), ["runtime"], "a stage remains")

    def test_mc35_partial_existing_destination_is_refused_and_not_repaired(self):
        """Label: simulated (pin boundary: SyntheticPins); the first installation is a real renamex_np publication."""
        for name in ("NODE-SOURCE.json", "bin/node"):
            with self.subTest(missing=name):
                self.assert_existing_destination_refused_unrepaired(lambda case, name=name: os.unlink(case.destination / name))

    def test_mc35_changed_existing_destination_is_refused_and_not_repaired(self):
        """Label: simulated (pin boundary: SyntheticPins). Bytes or modes of the existing tree changed."""
        def node_bytes(case):
            data = bytearray(NODE_EXECUTABLE)
            data[-1] ^= 0x01
            write(case.destination / "bin/node", bytes(data), 0o755)
        changes = {"bin/node bytes": node_bytes,
                   "bin/node mode": lambda case: os.chmod(case.destination / "bin/node", 0o700),
                   "NODE-SOURCE.json bytes": lambda case: write(case.destination / "NODE-SOURCE.json",
                                                                case.raw + b" ", 0o644),
                   "root mode": lambda case: os.chmod(case.destination, 0o700),
                   "bin mode": lambda case: os.chmod(case.destination / "bin", 0o700)}
        for label, change in changes.items():
            with self.subTest(label):
                self.assert_existing_destination_refused_unrepaired(change)

    def test_mc35_extra_entry_in_the_existing_destination_is_refused_and_not_repaired(self):
        """Label: simulated (pin boundary: SyntheticPins). An extra file, directory or .DS_Store."""
        extras = {".DS_Store at the root": lambda case: write(case.destination / ".DS_Store", b"\0\0\0\1Bud1"),
                  "an extra file in bin": lambda case: write(case.destination / "bin/extra.txt", b"extra\n"),
                  "an extra directory": lambda case: (case.destination / "extra-directory").mkdir()}
        for label, extra in extras.items():
            with self.subTest(label):
                self.assert_existing_destination_refused_unrepaired(extra)

    def test_mc35_linked_existing_destination_is_refused_and_not_repaired(self):
        """Label: simulated (pin boundary: SyntheticPins). A symbolic or hard link in place of a tree entry."""
        def node_link(case):
            copy_path = write(self.directory("elsewhere") / "node", NODE_EXECUTABLE, 0o755)
            os.unlink(case.destination / "bin/node")
            os.symlink(copy_path, case.destination / "bin/node")

        def bin_link(case):
            copy_path = self.directory("elsewhere") / "bin"
            shutil.copytree(case.destination / "bin", copy_path, symlinks=True)
            shutil.rmtree(case.destination / "bin")
            os.symlink(copy_path, case.destination / "bin")

        def destination_link(case):
            copy_path = self.directory("elsewhere") / "runtime"
            shutil.copytree(case.destination, copy_path, symlinks=True)
            shutil.rmtree(case.destination)
            os.symlink(copy_path, case.destination)

        def node_hard_link(case):
            os.link(case.destination / "bin/node", self.directory("elsewhere") / "node-hard-link")
        links = {"bin/node as a symbolic link": node_link, "bin as a symbolic link": bin_link,
                 "the destination as a symbolic link": destination_link, "bin/node with a second hard link": node_hard_link}
        for label, change in links.items():
            with self.subTest(label):
                self.assert_existing_destination_refused_unrepaired(change)

    def test_mc35_inaccessible_existing_destination_is_refused_and_not_repaired(self):
        """Label: simulated (pin boundary: SyntheticPins). An entry of the existing tree has mode 0."""
        entries = {"bin": lambda case: (case.destination / "bin", 0o755),
                   "the root": lambda case: (case.destination, 0o755),
                   "NODE-SOURCE.json": lambda case: (case.destination / "NODE-SOURCE.json", 0o644)}
        for label, entry in entries.items():
            with self.subTest(label):
                self.assert_existing_destination_refused_unrepaired(lambda case: None, inaccessible=entry)


# ---------------------------------------------------------------------------
# M0 and M1: the observer's plan, environment, platform, Mach-O and Python bindings (contract sections 4 and 7)
# ---------------------------------------------------------------------------

class PlanWorld:
    """A synthetic world in which an observation-plan/0.2.0 is shape-valid; none of its files is executed."""

    RELEASE = "25.6.0"
    KERNEL = "Darwin Kernel Version 25.6.0: synthetic control kernel"
    BOOT = "6F1B2C3D-4E5F-4A6B-8C7D-9E0F1A2B3C4D"

    def __init__(self, top):
        self.top = top
        self.root = top / "source"
        (self.root / ".venv").mkdir(parents=True)
        self.observer = write(self.root / observation.ENTRY_POINT, b"# synthetic stand-in at the observer path\n")
        self.framework = top / "framework/Python.framework/Versions/3.12"
        self.framework.mkdir(parents=True)
        self.runtime = top / "runtime"
        self.node = write(self.runtime / "bin/node", NODE_EXECUTABLE, 0o755)
        self.dependencies = top / "dependencies"
        self.dependencies.mkdir()
        self.git = write(top / "git/bin/git", b"#!/bin/sh\n# synthetic Git implementation; never executed\nexit 1\n", 0o755)
        inputs = top / "inputs"
        self.source_inventory = write(inputs / "source-inventory.json", canonical({"schema": SOURCE_SCHEMA, "files": {}}))
        self.python_inventory = write(inputs / "python-inventory.json", b"{}\n")
        self.archive = write(inputs / NODE_ARCHIVE_NAME, b"synthetic archive; the plan names the adopted pin\n")
        self.node_source = write(inputs / "node-source.json", b"{}\n")
        self.lock = write(inputs / "macos.lock", b"# synthetic lock\n")
        self.install = {name: write(inputs / (name + ".json"), b"{}\n")
                        for name in ("runtime-plan", "runtime-result", "dependencies-plan", "dependencies-result")}
        self.dependency_inventory = write(inputs / "dependencies-inventory.json", b"{}\n")
        self.failure_capture = write(inputs / "failure-capture.txt", b"synthetic failure-capture procedure\n")
        self.system_version = write(top / "os/SystemVersion.plist", plistlib.dumps(
            {"ProductName": "macOS", "ProductVersion": "26.6.2", "ProductBuildVersion": "25G83"}))
        self.cryptex_absent = str(top / "os/absent-cryptex/SystemVersion.plist")
        self.evidence = top / "evidence"
        self.evidence.mkdir()
        self.attempt = str(self.evidence / "attempt")
        self.plans = top / "plans"
        self.plans.mkdir()
        self.plan = self.build_plan()

    @staticmethod
    def ancestors(path):
        rows, current = [], str(path)
        while True:
            info = os.lstat(current)
            rows.append({"path": current, "device": info.st_dev, "inode": info.st_ino,
                         "mode": "0o%03o" % stat.S_IMODE(info.st_mode)})
            if current == "/":
                break
            current = os.path.dirname(current)
        return sorted(rows, key=lambda row: row["path"])

    def build_plan(self):
        plan = {"schema": PLAN_SCHEMA, "contract": CONTRACT, "profile": "darwin-arm64-v1", "executor": "macos-arm64-local",
                "environment": dict(DECLARED_ENVIRONMENT),
                "platform": {"system": "Darwin", "release": self.RELEASE, "machine": "arm64", "proc_translated": 0,
                             "boot_session_uuid": self.BOOT},
                "os": {"system_version": descriptor(self.system_version),
                       "cryptex": {"state": "absent", "path": self.cryptex_absent}},
                "source": {"root": str(self.root), "commit": hashlib.sha1(b"synthetic control commit").hexdigest(),
                           "tree": hashlib.sha1(b"synthetic control tree").hexdigest(),
                           "inventory": descriptor(self.source_inventory)},
                "observer": descriptor(self.observer),
                "python": {"venv": str(self.root / ".venv"), "framework": str(self.framework), "version": "3.12.13",
                           "inventory": descriptor(self.python_inventory)},
                "runtime": {"directory": str(self.runtime), "version": NODE_VERSION, "root_mode": "0o755",
                            "bin_mode": "0o755", "executable": binding(self.node), "node_source": binding(self.node_source),
                            "archive": dict(descriptor(self.archive), sha256=NODE_ARCHIVE_PIN),
                            "install": {"plan": descriptor(self.install["runtime-plan"]),
                                        "result": descriptor(self.install["runtime-result"])}},
                "dependencies": {"root": str(self.dependencies), "inventory": descriptor(self.dependency_inventory),
                                 "install": {"plan": descriptor(self.install["dependencies-plan"]),
                                             "result": descriptor(self.install["dependencies-result"])}},
                "git": descriptor(self.git),
                "evidence": {"parent": str(self.evidence), "ancestors": self.ancestors(self.evidence),
                             "attempt": self.attempt, "outputs": observation.output_paths(self.attempt)},
                "failure_capture": {"procedure": descriptor(self.failure_capture)},
                "limits": dict(observation.LIMITS)}
        plan["commands"] = observation.expected_commands(plan)
        return plan

    def write_plan(self, plan):
        raw = canonical(plan)
        path = self.plans / ("plan-%d.json" % len(os.listdir(self.plans)))
        path.write_bytes(raw)
        os.chmod(path, 0o644)
        return str(path), sha256(raw)

    def facts(self):
        """Synthetic static M0 facts, standing for the bindings that exist only after MP (labelled mocked).

        Refreeze 001, C-01: the Python part has the observer's own shape. Its inventory is the full document
        that python_inventory computes, here of the synthetic installation that install_synthetic_python
        places at the plan's venv and framework, and its digest is that document's digest.
        """
        plan = self.plan
        framework, venv = plan["python"]["framework"], plan["python"]["venv"]
        inventory = observation.python_inventory(venv, framework)
        return {
            "boundary": "mocked", "cf": None,
            "platform": {"system": "Darwin", "release": self.RELEASE, "version": self.KERNEL, "machine": "arm64",
                         "proc_translated": 0, "boot_session_uuid": self.BOOT},
            "os": {"system_version": {"state": "present", **descriptor(self.system_version), "product_name": "macOS",
                                      "product_version": "26.6.2", "product_build_version": "25G83",
                                      "product_version_extra": None},
                   "cryptex": {"state": "absent", "path": self.cryptex_absent, "hops": []}},
            "source": {"inventory": {"schema": SOURCE_SCHEMA, "files": {observation.MACOS_LOCK: binding(self.lock)}},
                       "head": {"gitdir": str(self.root) + "/.git", "common_dir": str(self.root) + "/.git",
                                "ref": "refs/heads/control", "commit": plan["source"]["commit"], "files": {}},
                       "pins": dict(observation.PYTHON_PINS)},
            "python": {"inventory": inventory, "inventory_sha256": observation.python_inventory_digest(inventory),
                       "launcher": {"implementation": "cpython", "version": "3.12.13", "build_string": "synthetic build",
                                    "flags": {}, "executable": venv + "/bin/python",
                                    "base_executable": framework + "/bin/python3.12", "prefix": framework,
                                    "base_prefix": framework, "path": [],
                                    "process_image": framework + "/Resources/Python.app/Contents/MacOS/Python"},
                       "packages": dict(observation.PYTHON_PINS), "records": {}},
            "runtime": {"directory": plan["runtime"]["directory"], "executable": plan["runtime"]["directory"] + "/bin/node",
                        "version": NODE_VERSION, "binding": dict(plan["runtime"]["executable"]),
                        "archive": dict(plan["runtime"]["archive"]),
                        "node_source": {"path": plan["runtime"]["directory"] + "/NODE-SOURCE.json",
                                        **plan["runtime"]["node_source"],
                                        "content": {"signature_check": {"status": "not_performed", "detail": "synthetic"}}},
                        "layout": {"root_mode": "0o755", "bin_mode": "0o755",
                                   "entries": ["NODE-SOURCE.json", "bin", "bin/node"]},
                        "macho": {"magic": "MH_MAGIC_64", "filetype": "MH_EXECUTE", "commands": []},
                        "install": {"purpose": "selected-node", "state": "INSTALLED_EXACT"}, "references": []},
            "dependencies": {"root": plan["dependencies"]["root"], "files": 24},
            "git": dict(plan["git"])}


class ControlHost(observation.Host):
    """The observer's host boundary, substituted and labelled mocked as the observer requires."""

    boundary = "mocked"

    def __init__(self, world, *, environment=None, sysname="Darwin", machine="arm64", translated=0, supervisor=None):
        self.world = world
        self.system_version_path = str(world.system_version)
        self.cryptex_path = world.cryptex_absent
        self.observed_environment = dict(DECLARED_ENVIRONMENT) if environment is None else dict(environment)
        self.platform = SimpleNamespace(sysname=sysname, nodename="control", release=world.RELEASE,
                                        version=world.KERNEL, machine=machine)
        self.translated = translated
        self.supervisor_module = supervisor
        self.calls = []

    def uname(self):
        self.calls.append("uname")
        return self.platform

    def proc_translated(self):
        self.calls.append("proc_translated")
        return self.translated

    def boot_session_uuid(self):
        self.calls.append("boot_session_uuid")
        return self.world.BOOT

    def environment(self):
        self.calls.append("environment")
        return dict(self.observed_environment)

    def launcher(self):
        self.calls.append("launcher")
        raise AssertionError("The interpreter binding is not reached by this control")

    def loaded_modules(self):
        self.calls.append("loaded_modules")
        return []

    def observer_path(self):
        return str(self.world.observer)

    def supervisor(self, root, inventory):
        self.calls.append("supervisor")
        if self.supervisor_module is None:
            raise AssertionError("The Darwin supervisor was loaded although this case refuses before any start")
        return self.supervisor_module


class CommandBoundary:
    """The M0 and M1 command boundary, mocked: no process starts; each label answers its simulated output."""

    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = []
        self.Clock = original.Clock
        self.Stop = original.Stop

    def run_process(self, argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):
        self.calls.append(label)
        stdout = self.outputs[label]
        stage = Path(stage)
        pid = 424240 + len(self.calls)
        record = {"argv": argv, "cwd": str(stage), "environment": env, "label": label,
                  "start_monotonic": time.monotonic(), "pid": pid, "process_group": pid, "returncode": None,
                  "observed_log_bytes": 0, "retained_log_bytes": 0, "cleanup": None, "handles_closed": False,
                  "error": None}
        if on_started is not None:
            on_started(dict(record))
        write(stage / (label + ".stdout.log"), stdout, 0o600)
        write(stage / (label + ".stderr.log"), b"", 0o600)
        final = dict(record, returncode=0, observed_log_bytes=len(stdout), retained_log_bytes=len(stdout),
                     cleanup={"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 1.0},
                     handles_closed=True, end_monotonic=time.monotonic())
        write(stage / (label + ".process.json"), original.json_bytes(final), 0o600)
        return final


class PythonWorld:
    """A synthetic framework version directory and venv with three Mach-O images and two link hops."""

    def __init__(self, top):
        self.top = top
        self.framework = top / "framework/Python.framework/Versions/3.12"
        self.venv = top / "venv"
        fw = self.framework
        write(fw / "bin/python3.12", b"#!synthetic framework launcher; never executed\n", 0o755)
        write(fw / "Resources/Python.app/Contents/MacOS/Python", b"synthetic process image; never executed\n", 0o755)
        write(fw / "lib/python3.12/os.py", b"# synthetic standard library module\n")
        write(fw / "lib/python3.12/__pycache__/os.cpython-312.pyc", b"synthetic bytecode\n")
        self.external = top / "opt/ext/lib/libext.dylib"
        write(top / "cellar/ext/1.0/lib/libext.dylib", dylib_image(str(self.external)))
        (top / "opt").mkdir()
        os.symlink(str(top / "cellar/ext/1.0"), str(top / "opt/ext"))
        write(fw / "lib/libmc32.dylib", dylib_image("@rpath/libmc32.dylib", ["/usr/lib/libSystem.B.dylib"]))
        self.bundle = fw / "lib/python3.12/lib-dynload/_mc32.cpython-312-darwin.so"
        self.write_bundle("@rpath/libmc32.dylib")
        (self.venv / "bin").mkdir(parents=True)
        os.symlink(str(fw / "bin/python3.12"), str(self.venv / "bin/python"))
        self.write_pyvenv("3.12.13")
        write(self.venv / "lib/python3.12/site-packages/mc32_module.py", b"# synthetic package module\n")

    def write_bundle(self, reference):
        write(self.bundle, bundle_image([reference, str(self.external), "/usr/lib/libSystem.B.dylib"],
                                        rpaths=["@loader_path/../.."]), 0o755)

    def write_pyvenv(self, version):
        write(self.venv / "pyvenv.cfg", ("home = %s\ninclude-system-site-packages = false\nversion = %s\n"
                                         % (self.framework / "bin", version)).encode("ascii"))

    def inventory(self):
        return observation.python_inventory(str(self.venv), str(self.framework))


def install_synthetic_python(world):
    """MC10, refreeze 001 (C-01): a synthetic Python installation at the plan's own venv and framework.

    Nothing in it is executed. Its layout is PythonWorld's, without the Mach-O images. The plan then
    freezes the canonical bytes of its inventory document, as M0's _python_static requires of a real
    installation, so that the facts PlanWorld.facts builds from it agree with the plan.
    """
    framework, venv = Path(world.plan["python"]["framework"]), Path(world.plan["python"]["venv"])
    write(framework / "bin/python3.12", b"#!synthetic framework launcher; never executed\n", 0o755)
    write(framework / "Resources/Python.app/Contents/MacOS/Python", b"synthetic process image; never executed\n", 0o755)
    write(framework / "lib/python3.12/os.py", b"# synthetic standard library module\n")
    (venv / "bin").mkdir()
    os.symlink(str(framework / "bin/python3.12"), str(venv / "bin/python"))
    write(venv / "pyvenv.cfg", ("home = %s\ninclude-system-site-packages = false\nversion = %s\n"
                                % (framework / "bin", world.plan["python"]["version"])).encode("ascii"))
    write(world.python_inventory, canonical(observation.python_inventory(str(venv), str(framework))))
    world.plan = world.build_plan()


class HostObservationControls(ControlCase):
    """MC06, MC07, MC08, MC10 and MC30 to MC33 at the observer (M0 and M1)."""

    def plan_world(self):
        return PlanWorld(self.directory("m0-world"))

    def static_refusal(self, world, host, plan=None):
        """The real M0 entry static_check with a substituted host; the refusal comes before any start."""
        path, digest = world.write_plan(world.plan if plan is None else plan)
        with self.assertRaises(observation.ObservationError) as caught:
            observation.static_check(path, digest, host=host)
        self.assertNotIn("supervisor", host.calls, "the Darwin supervisor was loaded")
        self.assertFalse(os.path.lexists(world.attempt), "an attempt directory was created")
        return caught.exception

    def node_rules(self, data):
        path = write(self.directory("macho") / "node", data, 0o755)
        _, summary = observation.read_macho(str(path), maximum=len(data), private=True, category="RUNTIME")
        return observation.check_node_macho(summary)

    def assert_node_rule_refusal(self, data, rule):
        with self.assertRaises(observation.ObservationError) as caught:
            self.node_rules(data)
        self.assertEqual(caught.exception.category, "MACHO")
        self.assertEqual(caught.exception.details.get("rule"), rule, caught.exception.as_dict())

    # MC06 ------------------------------------------------------------------

    def test_mc06_allow_listed_node_executable_is_accepted(self):
        """Label: real (the observer's Mach-O parser and Node rules on synthetic bytes). The baseline."""
        self.assertEqual(self.node_rules(NODE_EXECUTABLE)["references"], NODE_REFERENCES)

    def test_mc06_refused_load_commands_refuse_the_node_executable(self):
        """Label: real (synthetic bytes). LC_RPATH, LC_DYLD_ENVIRONMENT, LC_LOAD_UPWARD_DYLIB, LC_REEXPORT_DYLIB."""
        commands = {"LC_RPATH": path_command("LC_RPATH", "@executable_path/../lib"),
                    "LC_DYLD_ENVIRONMENT": path_command("LC_DYLD_ENVIRONMENT", "DYLD_INSERT_LIBRARIES=/x/y.dylib"),
                    "LC_LOAD_UPWARD_DYLIB": dylib_command("LC_LOAD_UPWARD_DYLIB", "/usr/lib/libz.1.dylib"),
                    "LC_REEXPORT_DYLIB": dylib_command("LC_REEXPORT_DYLIB", "/usr/lib/libz.1.dylib")}
        for name, command in commands.items():
            with self.subTest(name):
                self.assert_node_rule_refusal(macho(node_commands(command)), "MACHO-REFUSED-COMMAND")

    def test_mc06_load_command_outside_the_allow_list_refuses_the_node_executable(self):
        """Label: real (synthetic bytes). Known commands outside the closed list, and an unknown command."""
        commands = {"LC_VERSION_MIN_MACOSX": load_command("LC_VERSION_MIN_MACOSX", struct.pack("<II", 0x000E0000, 0x000F0000)),
                    "LC_LINKER_OPTION": load_command("LC_LINKER_OPTION", struct.pack("<I", 0) + b"\0" * 4),
                    "unknown command 0x7f": load_command(0x7F, b"\0" * 8)}
        for name, command in commands.items():
            with self.subTest(name):
                self.assert_node_rule_refusal(macho(node_commands(command)), "MACHO-COMMAND")

    def test_mc06_dylinker_other_than_usr_lib_dyld_refuses_the_node_executable(self):
        """Label: real (synthetic bytes). LC_LOAD_DYLINKER names another path."""
        self.assert_node_rule_refusal(macho(node_commands(dylinker="/usr/local/lib/dyld")), "MACHO-DYLINKER")

    def test_mc06_dylib_outside_usr_lib_and_system_library_refuses_the_node_executable(self):
        """Label: real (synthetic bytes). A dependency outside /usr/lib/ and /System/Library/."""
        commands = {"an absolute vendor path": dylib_command("LC_LOAD_DYLIB", "/opt/vendor/lib/libextra.dylib"),
                    "a weak dependency in /usr/local": dylib_command("LC_LOAD_WEAK_DYLIB", "/usr/local/lib/libweak.dylib"),
                    "a non-normalized path": dylib_command("LC_LOAD_DYLIB", "/usr/lib/../local/lib/libz.dylib")}
        for name, command in commands.items():
            with self.subTest(name):
                self.assert_node_rule_refusal(macho(node_commands(command)), "MACHO-DYLIB-PATH")

    def test_mc06_at_relative_dylib_path_refuses_the_node_executable(self):
        """Label: real (synthetic bytes). @rpath, @loader_path and @executable_path references."""
        for path in ("@rpath/libnode.dylib", "@loader_path/libnode.dylib", "@executable_path/../lib/libnode.dylib"):
            with self.subTest(path):
                self.assert_node_rule_refusal(macho(node_commands(dylib_command("LC_LOAD_DYLIB", path))),
                                              "MACHO-AT-PATH")

    def test_mc06_allow_listed_dyld_info_only_node_executable_is_accepted(self):
        """Label: real (synthetic bytes). LC_DYLD_INFO_ONLY in place of chained fixups and the exports trie.

        Refreeze 002, review finding I-08: the contract's closed allow-list admits LC_DYLD_INFO_ONLY (section 7),
        and the baseline uses chained fixups, so this variant shows the allow-listed alternative accepted.
        """
        data = macho(node_commands_with_dyld_info())
        names = [row["name"] for row in observation.parse_macho(data, len(data))["commands"]]
        self.assertEqual(names.count("LC_DYLD_INFO_ONLY"), 1, "premise: the image carries one LC_DYLD_INFO_ONLY")
        self.assertNotIn("LC_DYLD_CHAINED_FIXUPS", names)
        self.assertNotIn("LC_DYLD_EXPORTS_TRIE", names)
        self.assertEqual(self.node_rules(data)["references"], NODE_REFERENCES)

    # MC07 ------------------------------------------------------------------

    def assert_m0_predicate_refuses(self, names):
        for name in names:
            for with_cf in (False, True):
                with self.subTest(name=name, with_cf=with_cf):
                    observed = {**DECLARED_ENVIRONMENT, name: "/synthetic/control-value"}
                    if with_cf:
                        observed[CF_NAME] = CF_VALUE
                    with self.assertRaises(observation.ObservationError) as caught:
                        observation.check_environment(dict(observed), dict(DECLARED_ENVIRONMENT))
                    self.assertEqual(caught.exception.category, "ENVIRONMENT")
                    self.assertIs(observation.environment_admitted(dict(observed), dict(DECLARED_ENVIRONMENT), CF_VALUE),
                                  False)

    def test_mc07_dyld_variable_is_refused_by_m0(self):
        """Label: simulated (the observed environment is a synthetic mapping). Any DYLD_* variable."""
        self.assert_m0_predicate_refuses(("DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH",
                                          "DYLD_FALLBACK_LIBRARY_PATH", "DYLD_PRINT_LIBRARIES"))

    def test_mc07_python_launcher_variable_is_refused_by_m0(self):
        """Label: simulated (synthetic mapping). __PYVENV_LAUNCHER__ and PYTHONEXECUTABLE."""
        self.assert_m0_predicate_refuses(("__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE"))

    def test_mc07_node_variable_is_refused_by_m0(self):
        """Label: simulated (synthetic mapping). NODE_OPTIONS, NODE_PATH and another NODE_* variable."""
        self.assert_m0_predicate_refuses(("NODE_OPTIONS", "NODE_PATH", "NODE_EXTRA_CA_CERTS"))

    def test_mc07_python_startup_variable_is_refused_by_m0(self):
        """Label: simulated (synthetic mapping). The Python startup variables."""
        self.assert_m0_predicate_refuses(("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT",
                                          "PYTHONBREAKPOINT", "PYTHONUSERBASE", "PYTHONPYCACHEPREFIX",
                                          "PYTHONSAFEPATH", "PYTHONNOUSERSITE"))

    def test_mc07_m0_entry_refuses_a_dyld_variable_before_any_start(self):
        """Label: mocked (host boundary: ControlHost; its environment holds DYLD_INSERT_LIBRARIES)."""
        world = self.plan_world()
        baseline = self.static_refusal(world, ControlHost(world))
        self.assertEqual(baseline.category, "SOURCE", "the baseline must pass the environment, platform and OS checks")
        host = ControlHost(world, environment={**DECLARED_ENVIRONMENT, "DYLD_INSERT_LIBRARIES": "/synthetic/control.dylib"})
        self.assertEqual(self.static_refusal(world, host).category, "ENVIRONMENT")

    # MC08 ------------------------------------------------------------------

    def test_mc08_simulated_translated_execution_is_refused_by_m0_before_any_start(self):
        """Label: simulated (host boundary: ControlHost answers sysctl.proc_translated = 1)."""
        world = self.plan_world()
        self.assertEqual(self.static_refusal(world, ControlHost(world)).category, "SOURCE")
        self.assertEqual(self.static_refusal(world, ControlHost(world, translated=1)).category, "PLATFORM")

    def test_mc08_simulated_machine_other_than_arm64_is_refused_by_m0_before_any_start(self):
        """Label: simulated (host boundary: ControlHost answers machine x86_64)."""
        world = self.plan_world()
        self.assertEqual(self.static_refusal(world, ControlHost(world)).category, "SOURCE")
        self.assertEqual(self.static_refusal(world, ControlHost(world, machine="x86_64")).category, "PLATFORM")

    def test_mc08_simulated_system_other_than_darwin_is_refused_by_m0_before_any_start(self):
        """Label: simulated (host boundary: ControlHost answers system Linux)."""
        world = self.plan_world()
        self.assertEqual(self.static_refusal(world, ControlHost(world)).category, "SOURCE")
        self.assertEqual(self.static_refusal(world, ControlHost(world, sysname="Linux")).category, "PLATFORM")

    # MC10 ------------------------------------------------------------------

    def observe_with_version(self, node_stdout):
        world = self.plan_world()
        install_synthetic_python(world)
        boundary = CommandBoundary({observation.LABELS["git_version"]: b"git version 2.39.5 (synthetic control)\n",
                                    observation.LABELS["node_version"]: node_stdout})
        host = ControlHost(world, supervisor=boundary)
        path, digest = world.write_plan(world.plan)
        facts = world.facts()
        self.assertEqual(facts["python"]["inventory_sha256"], world.plan["python"]["inventory"]["sha256"],
                         "premise: the synthetic facts' Python inventory is the plan's frozen inventory")
        with mock.patch.object(observation, "static_observation", return_value=facts), \
                mock.patch.object(observation, "static_after_start", return_value=facts):
            try:
                return world, boundary, observation.observe_host(path, digest, host=host), None
            except observation.ObservationError as exc:
                return world, boundary, None, exc

    def test_mc10_mocked_m1_answering_v24_22_1_reaches_host_baseline(self):
        """Label: mocked (command boundary: CommandBoundary; M0's static bindings: synthetic facts). The baseline.

        Refreeze 001, C-01: the facts' Python inventory is the observer's own inventory document of a synthetic
        installation at the plan's paths, as real facts hold it.
        """
        world, boundary, result, error = self.observe_with_version(b"v24.22.1\n")
        self.assertIsNone(error, error.as_dict() if error is not None else None)
        self.assertEqual(result["state"], "OBSERVED_UNAPPROVED")
        host = json.loads(Path(world.attempt + "/HOST.json").read_bytes())
        self.assertEqual(host["labels"]["boundary"], "mocked")
        self.assertEqual(host["runtime"]["version"], NODE_VERSION)
        self.assertEqual(boundary.calls, [observation.LABELS["git_version"], observation.LABELS["node_version"]])

    def test_mc10_mocked_m1_version_differs_fails_preparation_without_host(self):
        """Label: mocked (command boundary: the Node --version output is simulated; static facts synthetic).

        Refreeze 001, C-01: the facts' Python inventory is the observer's own inventory document of a synthetic
        installation at the plan's paths, as real facts hold it.
        """
        for stdout in (b"v24.22.0\n", b"v24.22.1"):
            with self.subTest(stdout=stdout):
                world, boundary, result, error = self.observe_with_version(stdout)
                self.assertIsNone(result, "the observation was accepted")
                self.assertIsInstance(error, observation.ObservationError)
                self.assertEqual(error.category, "OUTPUT")
                self.assertIsNotNone(error.result)
                self.assertIsNone(error.result["host"])
                self.assertNotEqual(error.result["state"], "OBSERVED_UNAPPROVED")
                self.assertIs(error.result["evidence_finalized"], False)
                self.assertEqual(error.result["labels"]["boundary"], "mocked")
                self.assertFalse(os.path.lexists(world.attempt + "/HOST.json"), "a HOST document was published")
                self.assertFalse(os.path.lexists(world.attempt + "/completion.json"))
                self.assertEqual(boundary.calls, [observation.LABELS["git_version"], observation.LABELS["node_version"]])

    # MC30 ------------------------------------------------------------------

    def test_mc30_declared_environment_is_the_contracts(self):
        """Label: real. The declared environment of the observer and of the provider is the contract's."""
        self.assertEqual(dict(observation.ENVIRONMENT), DECLARED_ENVIRONMENT)
        self.assertEqual(dict(format_check.ENVIRONMENT), DECLARED_ENVIRONMENT)
        self.assertEqual(observation.CF_NAME, CF_NAME)

    def test_mc30_m0_predicate_admits_the_declared_environment_with_and_without_the_variable(self):
        """Label: mocked (the observed environment is a synthetic mapping; the case without the variable is the contract's simulated boundary)."""
        self.assertIsNone(observation.check_environment(dict(DECLARED_ENVIRONMENT), dict(DECLARED_ENVIRONMENT)))
        self.assertEqual(observation.check_environment({**DECLARED_ENVIRONMENT, CF_NAME: CF_VALUE},
                                                       dict(DECLARED_ENVIRONMENT)), CF_VALUE)

    def test_mc30_shared_predicate_admits_the_declared_environment_and_the_recorded_value(self):
        """Label: mocked (synthetic mappings and recorded values)."""
        for observed, recorded in ((DECLARED_ENVIRONMENT, CF_VALUE), ({**DECLARED_ENVIRONMENT, CF_NAME: CF_VALUE}, CF_VALUE),
                                   (DECLARED_ENVIRONMENT, None)):
            with self.subTest(observed=sorted(observed), recorded=recorded):
                self.assertIs(observation.environment_admitted(dict(observed), dict(DECLARED_ENVIRONMENT), recorded), True)

    def test_mc30_m0_entry_accepts_the_declared_environment_with_and_without_the_variable(self):
        """Label: mocked (host boundary: ControlHost). The first refusal is the absent synthetic source tree."""
        for label, environment in (("without the variable", dict(DECLARED_ENVIRONMENT)),
                                   ("with the variable", {**DECLARED_ENVIRONMENT, CF_NAME: CF_VALUE})):
            with self.subTest(label):
                world = self.plan_world()
                self.assertEqual(self.static_refusal(world, ControlHost(world, environment=environment)).category, "SOURCE")

    # MC31 ------------------------------------------------------------------

    def test_mc31_m0_predicate_refuses_an_extra_variable_or_an_empty_value(self):
        """Label: simulated (synthetic mappings)."""
        cases = {"an extra variable": {**DECLARED_ENVIRONMENT, "ONTOKIN_EXTRA_CONTROL": "1"},
                 "an extra variable beside the variable": {**DECLARED_ENVIRONMENT, "ONTOKIN_EXTRA_CONTROL": "1",
                                                           CF_NAME: CF_VALUE},
                 "the variable with an empty value": {**DECLARED_ENVIRONMENT, CF_NAME: ""}}
        for label, observed in cases.items():
            with self.subTest(label):
                with self.assertRaises(observation.ObservationError) as caught:
                    observation.check_environment(dict(observed), dict(DECLARED_ENVIRONMENT))
                self.assertEqual(caught.exception.category, "ENVIRONMENT")

    def test_mc31_m0_predicate_refuses_a_missing_or_changed_declared_variable(self):
        """Label: simulated (synthetic mappings). Exactly the declared environment is admitted."""
        cases = {"a declared variable missing": {k: v for k, v in DECLARED_ENVIRONMENT.items() if k != "TZ"},
                 "a declared variable changed": {**DECLARED_ENVIRONMENT, "LANG": "en_US.UTF-8"}}
        for label, observed in cases.items():
            with self.subTest(label):
                with self.assertRaises(observation.ObservationError) as caught:
                    observation.check_environment(dict(observed), dict(DECLARED_ENVIRONMENT))
                self.assertEqual(caught.exception.category, "ENVIRONMENT")

    def test_mc31_shared_predicate_refuses_a_value_other_than_the_recorded_one(self):
        """Label: simulated (synthetic mappings and recorded values)."""
        cases = {"another value than recorded": ({**DECLARED_ENVIRONMENT, CF_NAME: "0x0:0x0:0x0"}, CF_VALUE),
                 "the variable although none was recorded": ({**DECLARED_ENVIRONMENT, CF_NAME: CF_VALUE}, None),
                 "an extra variable": ({**DECLARED_ENVIRONMENT, "ONTOKIN_EXTRA_CONTROL": "1"}, CF_VALUE)}
        for label, (observed, recorded) in cases.items():
            with self.subTest(label):
                self.assertIs(observation.environment_admitted(dict(observed), dict(DECLARED_ENVIRONMENT), recorded), False)

    def test_mc31_m0_entry_refuses_an_extra_variable_or_an_empty_value_before_any_start(self):
        """Label: mocked (host boundary: ControlHost)."""
        for label, environment in (("an extra variable", {**DECLARED_ENVIRONMENT, "ONTOKIN_EXTRA_CONTROL": "1"}),
                                   ("an empty value", {**DECLARED_ENVIRONMENT, CF_NAME: ""})):
            with self.subTest(label):
                world = self.plan_world()
                self.assertEqual(self.static_refusal(world, ControlHost(world, environment=environment)).category,
                                 "ENVIRONMENT")

    # MC32 ------------------------------------------------------------------

    def python_world(self):
        world = PythonWorld(self.directory("python-world"))
        frozen = world.inventory()
        return world, frozen

    def assert_python_refused(self, world, frozen, *rows):
        actual = world.inventory()
        differences = observation.compare_inventory(frozen, actual)
        for row in rows:
            self.assertIn(row, differences)
        self.assertNotEqual(observation.python_inventory_digest(actual), observation.python_inventory_digest(frozen))

    def test_mc32_unchanged_trees_compare_equal_baseline(self):
        """Label: real (the observer's inventory of a synthetic framework and venv). The baseline."""
        world, frozen = self.python_world()
        again = world.inventory()
        self.assertEqual(observation.compare_inventory(frozen, again), [])
        self.assertEqual(observation.python_inventory_digest(again), observation.python_inventory_digest(frozen))
        self.assertIn(str(world.top / "opt/ext"), [row["path"] for row in frozen["closure"]["links"]])
        self.assertEqual(len(frozen["closure"]["images"]), 3)

    def test_mc32_changed_file_is_refused(self):
        """Label: real (synthetic trees). A framework file's bytes change."""
        world, frozen = self.python_world()
        write(world.framework / "lib/python3.12/os.py", b"# changed synthetic standard library module\n")
        self.assert_python_refused(world, frozen, {"part": "framework", "path": "lib/python3.12/os.py", "change": "changed"})

    def test_mc32_added_file_is_refused(self):
        """Label: real (synthetic trees). A file is added to the framework and to the venv."""
        for tree, rel in (("framework", "lib/python3.12/added.py"), ("venv", "lib/python3.12/site-packages/added_mc32.py")):
            with self.subTest(tree=tree):
                world, frozen = self.python_world()
                write((world.framework if tree == "framework" else world.venv) / rel, b"# added\n")
                self.assert_python_refused(world, frozen, {"part": tree, "path": rel, "change": "added"})

    def test_mc32_missing_file_is_refused(self):
        """Label: real (synthetic trees). A framework file is removed."""
        world, frozen = self.python_world()
        os.unlink(world.framework / "lib/python3.12/os.py")
        self.assert_python_refused(world, frozen, {"part": "framework", "path": "lib/python3.12/os.py", "change": "missing"})

    def test_mc32_added_bytecode_file_is_refused(self):
        """Label: real (synthetic trees). A __pycache__ file is added."""
        world, frozen = self.python_world()
        rel = "lib/python3.12/__pycache__/added.cpython-312.pyc"
        write(world.framework / rel, b"added synthetic bytecode\n")
        self.assert_python_refused(world, frozen, {"part": "framework", "path": rel, "change": "added"})

    def test_mc32_changed_pyvenv_cfg_is_refused(self):
        """Label: real (synthetic trees). pyvenv.cfg changes."""
        world, frozen = self.python_world()
        world.write_pyvenv("3.12.14")
        self.assert_python_refused(world, frozen, {"part": "venv", "path": "pyvenv.cfg", "change": "changed"})

    def test_mc32_retargeted_dependency_link_hop_is_refused(self):
        """Label: real (synthetic trees). The link hop to an external dependency is retargeted to identical bytes."""
        world, frozen = self.python_world()
        hop = world.top / "opt/ext"
        old_target, new_target = str(world.top / "cellar/ext/1.0"), str(world.top / "cellar/ext/2.0")
        write(world.top / "cellar/ext/2.0/lib/libext.dylib", (world.top / "cellar/ext/1.0/lib/libext.dylib").read_bytes())
        os.unlink(hop)
        os.symlink(new_target, str(hop))
        self.assert_python_refused(world, frozen,
                                   {"part": "links", "path": str(hop), "change": "missing", "target": old_target},
                                   {"part": "links", "path": str(hop), "change": "added", "target": new_target})

    def test_mc32_retargeted_selection_link_hop_is_refused(self):
        """Label: real (synthetic trees). .venv/bin/python is retargeted through another link to the same launcher."""
        world, frozen = self.python_world()
        os.symlink(str(world.framework), str(world.top / "opt/py"))
        os.unlink(world.venv / "bin/python")
        os.symlink(str(world.top / "opt/py/bin/python3.12"), str(world.venv / "bin/python"))
        self.assert_python_refused(world, frozen, {"part": "venv", "path": "bin/python", "change": "changed"})

    def test_mc32_at_relative_load_that_does_not_resolve_to_a_bound_file_is_refused(self):
        """Label: real (synthetic trees). An @rpath reference with no bound file behind it."""
        world, frozen = self.python_world()
        self.assertTrue(frozen["closure"]["images"])
        world.write_bundle("@rpath/libmissing.dylib")
        with self.assertRaises(observation.ObservationError) as caught:
            world.inventory()
        self.assertEqual(caught.exception.category, "MACHO")
        self.assertEqual(caught.exception.details.get("rule"), "MACHO-AT-UNRESOLVED")

    # MC33 ------------------------------------------------------------------

    def test_mc33_m0_plan_declaring_another_node_version_is_refused_before_any_start(self):
        """Label: mocked (host boundary: ControlHost; never consulted). The plan declares v24.22.0."""
        world = self.plan_world()
        path, digest = world.write_plan(world.plan)
        self.assertIsInstance(observation.validate_plan(path, digest, host=ControlHost(world)), observation.ValidatedPlan)
        plan = copy.deepcopy(world.plan)
        plan["runtime"]["version"] = "v24.22.0"
        path, digest = world.write_plan(plan)
        host = ControlHost(world)
        with self.assertRaises(observation.ObservationError) as caught:
            observation.observe_host(path, digest, host=host)
        self.assertEqual(caught.exception.category, "RUNTIME")
        self.assertEqual(caught.exception.details.get("rule"), "RUNTIME-VERSION")
        self.assertEqual(host.calls, [], "the host was observed or a start was prepared")
        self.assertFalse(os.path.lexists(world.attempt))


# ---------------------------------------------------------------------------
# MC20: canonical paths (contract section 7)
# ---------------------------------------------------------------------------

class PathControls(PreparerFixtures, ControlCase):
    """M0's canonical_path, the provider's bound-file reads and the preparer's plan paths."""

    def linked_ancestor(self):
        real = self.directory("real")
        write(real / "bound.txt", b"bound\n")
        link = self.base / "linked-ancestor"
        os.symlink(str(real), str(link))
        return real, link

    def test_mc20_m0_refuses_a_bound_path_with_a_symlinked_ancestor(self):
        """Label: real (a symbolic link created in the resolved temporary directory)."""
        _, link = self.linked_ancestor()
        with self.assertRaises(observation.ObservationError) as caught:
            observation.canonical_path(str(link / "bound.txt"))
        self.assertEqual(caught.exception.category, "PATH")

    def test_mc20_m0_refuses_a_bound_path_that_is_itself_a_link(self):
        """Label: real. The last component is a symbolic link."""
        real, _ = self.linked_ancestor()
        os.symlink(str(real / "bound.txt"), str(real / "bound-link.txt"))
        with self.assertRaises(observation.ObservationError) as caught:
            observation.canonical_path(str(real / "bound-link.txt"))
        self.assertEqual(caught.exception.category, "PATH")

    def test_mc20_m0_admits_the_tmp_system_link_as_an_ancestor_and_records_the_canonical_form(self):
        """Label: real. /tmp is one of the three admitted system links."""
        system_tmp = os.path.realpath("/tmp")
        self.assertNotEqual(system_tmp, "/tmp")
        folder = tempfile.mkdtemp(prefix="ontokin-w6-mc20-", dir=system_tmp)
        self.addCleanup(shutil.rmtree, folder)
        write(Path(folder) / "bound.txt", b"bound\n")
        spelled = "/tmp/" + os.path.basename(folder) + "/bound.txt"
        self.assertEqual(observation.canonical_path(spelled), folder + "/bound.txt")

    def test_mc20_provider_refuses_a_bound_file_with_a_symlinked_ancestor(self):
        """Label: real. The provider's bounded file read of a path through a linked ancestor."""
        _, link = self.linked_ancestor()
        with self.assertRaises(provider.CurrentHostBindingError):
            provider.file_binding(link / "bound.txt", category="SOURCE")

    def test_mc20_preparer_refuses_a_destination_with_a_symlinked_ancestor_and_creates_nothing(self):
        """Label: simulated (pin boundary: SyntheticPins). The plan's destination lies below a linked ancestor."""
        case = self.node_case()
        real, link = self.linked_ancestor()
        case.plan["destination"] = str(link / "runtime")
        result, error = self.install(case)
        self.assert_refused(result, error)
        self.assertEqual(sorted(os.listdir(real)), ["bound.txt"], "something was created below the linked ancestor")


# ---------------------------------------------------------------------------
# MC12, MC13, MC37, MC38, MC39: the Darwin supervisor with real Python children (contract section 5 as amended)
# ---------------------------------------------------------------------------

class SupervisorProcessControls(ControlCase):
    """Real Python children only (sys.executable -I -S -B -c); the teardown removes every process started."""

    GUARDED = False

    def setUp(self):
        super().setUp()
        self.owned = OwnedProcesses(self)

    @contextlib.contextmanager
    def counted_starts(self):
        real = subprocess.Popen
        starts = []
        owned = self.owned

        def counting(*args, **kwargs):
            process = real(*args, **kwargs)
            starts.append({"argv": list(args[0] if args else kwargs["args"]), "pid": process.pid})
            owned.add_group(process.pid)
            return process
        with mock.patch.object(subprocess, "Popen", counting):
            yield starts

    def run_supervised(self, code, *, stage_seconds=20.0, cancel_after_ms=None):
        stage = self.directory("stage")
        clock = original.Clock(total_ms=30000)
        started, failure, record = [], None, None
        begun = time.monotonic()
        with self.counted_starts() as starts:
            try:
                record = darwin.run_process(list(PYTHON_CHILD) + [code], stage=stage, label="control-child",
                                            clock=clock, stage_end=time.monotonic() + stage_seconds,
                                            env=dict(DECLARED_ENVIRONMENT),
                                            on_started=lambda row: started.append(dict(row)),
                                            cancel_after_ms=cancel_after_ms)
            except original.Stop as exc:
                failure, record = exc, getattr(exc, "process_record", None)
        return SimpleNamespace(stage=stage, record=record, failure=failure, starts=starts, started=started,
                               elapsed=time.monotonic() - begun,
                               group=starts[0]["pid"] if starts else None)

    def assert_one_python_start(self, run):
        self.assertEqual(len(run.starts), 1, "no retry: exactly one start")
        self.assertEqual(run.starts[0]["argv"][:5], list(PYTHON_CHILD))
        self.assertEqual([row["pid"] for row in run.started], [run.starts[0]["pid"]])

    def assert_original_receipt(self, run, extra=()):
        self.assertIsNotNone(run.record, "no process receipt")
        self.assertEqual(set(run.record), ORIGINAL_RECEIPT_KEYS | set(extra))
        self.assertIs(run.record["handles_closed"], True)
        self.assertEqual(run.record["pid"], run.group)
        self.assertEqual(run.record["process_group"], run.group)
        self.assertEqual((run.stage / "control-child.process.json").read_bytes(), original.json_bytes(run.record))

    def assert_passed_cleanup(self, record):
        cleanup = record["cleanup"]
        self.assertEqual(set(cleanup), PASSED_CLEANUP_KEYS)
        self.assertIs(cleanup["passed"], True)
        self.assertIs(cleanup["process_group_absent"], True)
        self.assertIs(cleanup["reaped"], True)
        self.assertLessEqual(cleanup["elapsed_ms"], CLEANUP_CEILING_MS)

    def assert_ceiling_failure(self, run):
        self.assertIsNotNone(run.failure, "the run was accepted")
        self.assertEqual(run.failure.as_dict(), {"code": "OTRAY-E-BACKEND", "reason": CEILING_REASON, "state": "REJECTED"})
        self.assertEqual(run.record["cleanup"], {"passed": False, "reason": CEILING_REASON})
        self.assertEqual(run.record["error"], run.failure.as_dict())
        self.assertNotEqual(run.record["cleanup"].get("process_group_absent"), True)

    def unreaped_child(self):
        """The test's own direct child in a new session, exited and not reaped; its exit established through kqueue."""
        child = subprocess.Popen(list(PYTHON_CHILD) + [STDIN_CODE], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True, env=dict(DECLARED_ENVIRONMENT))
        self.owned.add_direct(child)
        self.assertIs(darwin.group_exists(child.pid), True, "the live child must count as present")
        events = wait_for_exit_without_reaping(child.pid, child.stdin.close)
        self.assertEqual(len(events), 1, "kqueue did not establish the child's exit")
        self.assertIsNone(child.returncode, "the child was reaped")
        return child

    def test_mc12_descendant_left_in_the_group_is_refused_and_the_group_terminated_within_2000_ms(self):
        """Label: real. One Python child forks a descendant that stays in its group, then exits."""
        control = self.directory("control")
        run = self.run_supervised(DESCENDANT_CODE % str(control))
        descendant = (read_numbers(control / "descendant.pid") or [None])[0]
        self.owned.add_descendant(descendant, run.group)
        self.assertIsNotNone(run.failure, "the run was accepted")
        self.assertEqual(run.failure.as_dict(), {"code": "OTRAY-E-BACKEND", "reason": DESCENDANT_REASON, "state": "REJECTED"})
        self.assert_original_receipt(run)
        self.assertEqual(run.record["error"], run.failure.as_dict())
        self.assert_passed_cleanup(run.record)
        self.assertEqual(run.record["returncode"], 0)
        self.assert_one_python_start(run)
        self.assertIsNotNone(descendant, "the child did not record its descendant")
        self.assertTrue(wait_until(lambda: group_absent(run.group), 2.0), "the owned group remains (EPERM means present)")
        self.assertTrue(wait_until(lambda: not descendant_present(descendant, run.group), 2.0))
        evidence("MC12", cleanup=run.record["cleanup"], descendant=descendant)

    def test_mc13_timeout_cleanup_keeps_the_original_limits_and_receipt_without_retry(self):
        """Label: real. One sleeping Python child; the stage deadline ends it after 300 ms."""
        self.assertIs(darwin.LIMITS, original.LIMITS)
        self.assertEqual(darwin.LIMITS["cleanup_ms"], CLEANUP_CEILING_MS)
        run = self.run_supervised(SLEEPING_CODE, stage_seconds=0.3)
        self.assertIsNotNone(run.failure, "the run was accepted")
        self.assertEqual(run.failure.as_dict(), {"code": "OTRAY-E-RESOURCE", "reason": "Monotonic stage or transaction deadline",
                                                 "state": "TIMEOUT"})
        self.assert_original_receipt(run)
        self.assertEqual(run.record["error"], run.failure.as_dict())
        self.assert_passed_cleanup(run.record)
        self.assertEqual(run.record["returncode"], -signal.SIGTERM)
        self.assert_one_python_start(run)
        self.assertTrue(wait_until(lambda: group_absent(run.group), 2.0))
        evidence("MC13-timeout", cleanup=run.record["cleanup"], elapsed_s=run.elapsed)

    def test_mc13_cancellation_cleanup_keeps_the_original_limits_and_receipt_without_retry(self):
        """Label: real. One sleeping Python child; a controlled cancellation 150 ms after the start."""
        run = self.run_supervised(SLEEPING_CODE, cancel_after_ms=150)
        self.assertIsNotNone(run.failure, "the run was accepted")
        self.assertEqual(run.failure.as_dict(), {"code": "OTRAY-E-CANCELLED", "reason": "Controlled cancellation after child start",
                                                 "state": "CANCELLED"})
        self.assert_original_receipt(run, extra=("cancellation_completion_ms",))
        self.assertEqual(run.record["error"], run.failure.as_dict())
        self.assert_passed_cleanup(run.record)
        self.assertLessEqual(run.record["cancellation_completion_ms"], CLEANUP_CEILING_MS)
        self.assert_one_python_start(run)
        self.assertTrue(wait_until(lambda: group_absent(run.group), 2.0))
        evidence("MC13-cancellation", cleanup=run.record["cleanup"],
                 cancellation_completion_ms=run.record["cancellation_completion_ms"])

    def test_mc37_exited_unreaped_direct_child_counts_as_present_until_it_is_reaped(self):
        """Label: real. The test's own direct child, exited and not reaped; kqueue establishes the exit."""
        child = self.unreaped_child()
        raw_unreaped = group_probe(child.pid)
        present = darwin.group_exists(child.pid)
        self.assertIsNone(child.returncode)
        child.wait(timeout=5)
        raw_reaped = group_probe(child.pid)
        absent = darwin.group_exists(child.pid)
        evidence("MC37", raw_unreaped=raw_unreaped, raw_reaped=raw_reaped)
        self.assertIs(present, True, "an exited, unreaped child counted as absent")
        self.assertNotEqual(raw_unreaped, "ESRCH")
        self.assertIs(absent, False, "the reaped child still counts as present")
        self.assertEqual(raw_reaped, "ESRCH")

    def test_mc38_terminate_group_on_an_exited_unreaped_child_returns_the_original_passed_receipt(self):
        """Label: real. terminate_group on the test's exited, unreaped direct child; os.killpg is recorded, never altered."""
        child = self.unreaped_child()
        real_killpg, calls = os.killpg, []

        def recording(pid, sig):
            try:
                real_killpg(pid, sig)
            except OSError as exc:
                calls.append([int(sig), exc.errno])
                raise
            calls.append([int(sig), 0])
        with mock.patch.object(os, "killpg", recording):
            receipt = darwin.terminate_group(child, original.Clock(total_ms=30000))
        evidence("MC38", calls=calls, receipt=receipt)
        self.assertEqual(set(receipt), PASSED_CLEANUP_KEYS)
        self.assertIs(receipt["passed"], True)
        self.assertIs(receipt["process_group_absent"], True)
        self.assertIs(receipt["reaped"], True)
        self.assertLessEqual(receipt["elapsed_ms"], CLEANUP_CEILING_MS)
        self.assertEqual(child.returncode, 0)
        self.assertEqual(calls[0], [int(signal.SIGTERM), errno.EPERM],
                         "premise: the real SIGTERM send is refused with EPERM, so the case covers that handling")
        self.assertTrue(group_absent(child.pid))

    def test_mc39a_escaped_descendant_keeping_an_unreaped_child_in_the_group_fails_at_the_cleanup_ceiling(self):
        """Label: real. A descendant moves into its own group and never reaps its exited child, which stays in the owned group."""
        control = self.directory("control")
        run = self.run_supervised(ESCAPE_CODE % str(control))
        descendant = (read_numbers(control / "descendant.pid") or [None])[0]
        pids = read_numbers(control / "escaped.pids")
        for pid in [descendant] + list(pids or []):
            self.owned.add_descendant(pid, run.group)
        self.assert_ceiling_failure(run)
        self.assert_original_receipt(run)
        self.assertEqual(run.record["returncode"], 0)
        self.assert_one_python_start(run)
        self.assertGreaterEqual(run.elapsed, CLEANUP_CEILING_MS / 1000)
        self.assertIsNotNone(pids, "the descendant did not record itself and its unreaped child")
        escaped, unreaped = pids
        self.assertEqual(group_probe(run.group), "EPERM", "premise: the owned group keeps answering EPERM")
        self.assertTrue(descendant_present(escaped, run.group), "the escaped descendant survives (AMENDMENT-001 3.3)")
        evidence("MC39a", escaped=escaped, unreaped=unreaped, cleanup=run.record["cleanup"], elapsed_s=run.elapsed)
        self.owned.teardown()
        self.assertTrue(group_absent(run.group))
        self.assertFalse(descendant_present(escaped, run.group))
        self.assertFalse(descendant_present(unreaped, run.group))

    def test_mc39b_simulated_lasting_eperm_probe_fails_at_the_cleanup_ceiling(self):
        """Label: simulated (os.killpg boundary: killpg(pid, 0) fails with PermissionError; real signals pass through)."""
        real_killpg, sends = os.killpg, []

        def simulated(pid, sig):
            if sig == 0:
                raise PermissionError(errno.EPERM, "simulated EPERM at the os.killpg boundary")
            try:
                real_killpg(pid, sig)
            except OSError as exc:
                sends.append([int(sig), exc.errno])
                raise
            sends.append([int(sig), 0])
        with mock.patch.object(os, "killpg", simulated):
            run = self.run_supervised(SLEEPING_CODE, stage_seconds=0.3)
        evidence("MC39b", sends=sends, cleanup=run.record and run.record["cleanup"], elapsed_s=run.elapsed)
        self.assert_ceiling_failure(run)
        self.assert_original_receipt(run)
        self.assertEqual([row[0] for row in sends], [int(signal.SIGTERM), int(signal.SIGKILL), int(signal.SIGKILL)])
        self.assertEqual(sends[0][1], 0, "the real SIGTERM did not reach the live child")
        self.assertEqual(run.record["returncode"], -signal.SIGTERM)
        self.assert_one_python_start(run)
        self.assertTrue(wait_until(lambda: group_absent(run.group), 2.0))


# ---------------------------------------------------------------------------
# MC14 and MC17: the Darwin supervisor's source and precondition (no start)
# ---------------------------------------------------------------------------

class SupervisorStaticControls(ControlCase):
    """MC14's token-level comparison and MC17's precondition; nothing starts."""

    def test_mc14_run_process_differs_from_the_original_only_by_the_precondition_site(self):
        """Label: real (token comparison of the two files' sources). Site 1 of AMENDMENT-001 section 3.2."""
        before = function_source(SUPERVISOR_PATH, "run_process")
        after = function_source(DARWIN_SUPERVISOR_PATH, "run_process")
        self.assertEqual(before.count(ORIGINAL_PRECONDITION), 1)
        prefix, suffix = before.split(ORIGINAL_PRECONDITION)
        self.assertTrue(after.startswith(prefix), "a change before site 1")
        self.assertTrue(after.endswith(suffix), "a change after site 1")
        self.assertGreater(len(after), len(prefix) + len(suffix))
        replacement = after[len(prefix):len(after) - len(suffix)]
        self.assertNotEqual(replacement, ORIGINAL_PRECONDITION)
        self.assertNotIn("prctl", replacement)
        ast.parse(textwrap.dedent(replacement))
        rows = token_rows(textwrap.dedent(replacement))
        strings = [text for _, text in rows]
        self.assertTrue(any(strings[index:index + 5] == ["raise", "Stop", "(", '"OTRAY-E-BACKEND"', ","]
                            for index in range(len(strings))), "site 1 does not raise Stop(\"OTRAY-E-BACKEND\", ...)")
        self.assertEqual(token_rows(after), token_rows(prefix + replacement + suffix))
        self.assertEqual(token_rows(prefix + ORIGINAL_PRECONDITION + suffix), token_rows(before))

    def test_mc14_group_exists_differs_from_the_original_only_by_the_inserted_eperm_clause(self):
        """Label: real (token comparison). Site 2: except PermissionError: / return True before except ProcessLookupError:."""
        before = function_source(SUPERVISOR_PATH, "group_exists")
        after = function_source(DARWIN_SUPERVISOR_PATH, "group_exists")
        self.assertEqual(before.count(ORIGINAL_PROBE_CLAUSE), 1)
        expected = before.replace(ORIGINAL_PROBE_CLAUSE, AMENDED_PROBE_CLAUSE)
        self.assertEqual(token_rows(after), token_rows(expected), "tokens differ outside site 2")
        self.assertEqual(after, expected, "the source differs from the original plus site 2")

    def test_mc14_terminate_group_differs_from_the_original_only_by_the_three_send_sites(self):
        """Label: real (token comparison). Sites 3 to 5: each send also passes over PermissionError."""
        before = function_source(SUPERVISOR_PATH, "terminate_group")
        after = function_source(DARWIN_SUPERVISOR_PATH, "terminate_group")
        lines = before.splitlines()
        sites = [index for index, line in enumerate(lines) if line.strip() == ORIGINAL_SEND_CLAUSE]
        self.assertEqual(len(sites), 3)
        for index in sites:
            self.assertEqual(lines[index - 2].strip(), "try:")
            self.assertTrue(lines[index - 1].strip().startswith("os.killpg(process.pid, signal.SIG"))
        expected = before.replace(ORIGINAL_SEND_CLAUSE, AMENDED_SEND_CLAUSE)
        self.assertEqual(token_rows(after), token_rows(expected), "tokens differ outside sites 3 to 5")
        self.assertEqual(after, expected, "the source differs from the original plus sites 3 to 5")

    def test_mc14_imports_are_the_originals_and_the_original_supervisor_stays_byte_identical(self):
        """Label: real. AMENDMENT-001 section 3.1 and the names of site 1."""
        self.assertEqual(sha256(SUPERVISOR_PATH.read_bytes()), ORIGINAL_SUPERVISOR_SHA256)
        for name in ("Clock", "Stop", "LIMITS", "inventory", "json_bytes", "_reap"):
            self.assertIs(getattr(darwin, name), getattr(original, name), name)
        for name in ("run_process", "group_exists", "terminate_group"):
            function = getattr(darwin, name)
            self.assertIsNot(function, getattr(original, name))
            self.assertEqual(function.__module__, darwin.__name__)
            self.assertEqual(inspect.signature(function), inspect.signature(getattr(original, name)))
        self.assertIs(darwin.run_process.__globals__["group_exists"], darwin.group_exists)
        self.assertIs(darwin.run_process.__globals__["terminate_group"], darwin.terminate_group)
        self.assertIs(darwin.terminate_group.__globals__["group_exists"], darwin.group_exists)

    def assert_stopped_before_any_start(self, *patches):
        stage = self.directory("stage")
        started = []
        with contextlib.ExitStack() as stack:
            for item in patches:
                stack.enter_context(item)
            popen = stack.enter_context(mock.patch.object(subprocess, "Popen", side_effect=AssertionError("MC17: a start")))
            with self.assertRaises(original.Stop) as caught:
                darwin.run_process(list(PYTHON_CHILD) + ["pass"], stage=stage, label="control-child",
                                   clock=original.Clock(total_ms=30000), stage_end=time.monotonic() + 20,
                                   env=dict(DECLARED_ENVIRONMENT), on_started=started.append)
            self.assertEqual(popen.call_count, 0, "a start was attempted")
        self.assertEqual(caught.exception.code, "OTRAY-E-BACKEND")
        self.assertEqual(caught.exception.state, "REJECTED")
        self.assertEqual(started, [])
        self.assertEqual(os.listdir(stage), [], "a receipt or log was written: the run went past the precondition")
        return caught.exception

    def test_mc17_real_precondition_holds_on_the_executor(self):
        """Label: real. The executor of darwin-arm64-v1 is native Darwin arm64 (baseline of the simulated cases)."""
        self.assertEqual(sys.platform, "darwin")
        self.assertEqual(os.uname().machine, "arm64")
        self.assertEqual(darwin.proc_translated(), 0)
        self.assertIsNone(darwin.darwin_precondition())

    def test_mc17_simulated_non_darwin_platform_stops_before_any_start(self):
        """Label: simulated (sys.platform boundary answers linux)."""
        self.assert_stopped_before_any_start(mock.patch.object(sys, "platform", "linux"))

    def test_mc17_simulated_machine_other_than_arm64_stops_before_any_start(self):
        """Label: simulated (os.uname boundary answers machine x86_64)."""
        uname = SimpleNamespace(sysname="Darwin", nodename="control", release="25.6.0", version="synthetic",
                                machine="x86_64")
        self.assert_stopped_before_any_start(mock.patch.object(os, "uname", return_value=uname))

    def test_mc17_simulated_translated_process_stops_before_any_start(self):
        """Label: simulated (sysctlbyname boundary answers sysctl.proc_translated = 1)."""
        library = FakeLibSystem(value=1)
        self.assert_stopped_before_any_start(mock.patch.object(darwin, "_libsystem", return_value=library))
        self.assertEqual(library.names, [b"sysctl.proc_translated"])

    def test_mc17_simulated_unreadable_translation_fails_closed_before_any_start(self):
        """Label: simulated (sysctlbyname boundary: status -1, a 2-byte answer, a load failure, a missing symbol)."""
        variants = {"status -1": mock.patch.object(darwin, "_libsystem", return_value=FakeLibSystem(status=-1)),
                    "a 2-byte answer": mock.patch.object(darwin, "_libsystem", return_value=FakeLibSystem(value=0, width=2)),
                    "the library cannot load": mock.patch.object(darwin, "_libsystem", side_effect=OSError("simulated")),
                    "the symbol is missing": mock.patch.object(darwin, "_libsystem", return_value=FakeLibSystem(symbol=False))}
        for label, boundary in variants.items():
            with self.subTest(label):
                self.assert_stopped_before_any_start(boundary)


# ---------------------------------------------------------------------------
# MC09, MC18, MC21, MC22, MC29, MC30, MC31, MC33 at the 0.2.0 provider (contract sections 7 and 8)
# ---------------------------------------------------------------------------

class ProviderWorld:
    """A synthetic 0.2.0 selection whose host, source, dependency and method verifications are substituted.

    The configuration file and its digest, the contract and adoption-record bindings, the evidence root,
    the manifest, the job checks, the clock, the boot binding around the start and the ledgers are the
    provider's own. The Darwin supervisor is mocked; the provider labels its records "mocked".
    """

    BOOT = "8C1B2C3D-4E5F-4A6B-8C7D-9E0F1A2B3C4D"
    OTHER_BOOT = "9D2C3B4A-5F6E-4B7A-8D9C-0F1E2D3C4B5A"

    def __init__(self, test, *, runtime_version=NODE_VERSION):
        top = test.directory("provider-world")
        self.evidence = top / "evidence"
        self.cohort = self.evidence / "cohort"
        (self.cohort / "provider-ledgers").mkdir(parents=True)
        self.case = "Q01-positive"
        self.stage = self.cohort / self.case
        self.manifest_path = self.cohort / "supplemental-cpu.json"
        self.schedule = self.cohort / "unused-native-schedule"
        frozen = write(top / "inputs/frozen-input.json", b"{}\n")
        plist = {"state": "present", "sha256": sha256(b"synthetic SystemVersion.plist"), "size_bytes": 512, "mode": "0o644",
                 "product_name": "macOS", "product_version": "26.6.2", "product_build_version": "25G83",
                 "product_version_extra": None}
        os_identity = {"system_version": dict(plist, path="/System/Library/CoreServices/SystemVersion.plist"),
                       "cryptex": dict(plist, sha256=sha256(b"synthetic cryptex SystemVersion.plist"),
                                       path="/synthetic/cryptex/SystemVersion.plist",
                                       link_path="/synthetic/cryptex-name/SystemVersion.plist", hops=[])}
        label = {"product_version": "26.6.2", "product_build_version": "25G83", "product_version_extra": None}
        executable = {"sha256": sha256(b"synthetic node executable"), "size_bytes": 4096, "mode": "0o755"}
        self.host = {"platform": {"system": "Darwin", "release": "25.6.0",
                                  "version": "Darwin Kernel Version 25.6.0: synthetic control kernel", "machine": "arm64",
                                  "proc_translated": 0, "boot_session_uuid": self.BOOT},
                     "os": os_identity, "runtime": {"binding": dict(executable)},
                     "labels": {"os": dict(label, cryptex=dict(label, state="present")),
                                "node": {"archive": NODE_ARCHIVE_NAME, "archive_sha256": NODE_ARCHIVE_PIN,
                                         "executable": dict(executable), "signature_check": "not_performed"}},
                     "python": {"inventory_sha256": sha256(b"synthetic python inventory")},
                     "git": {"path": "/synthetic/git/bin/git", "sha256": sha256(b"synthetic git")}}
        self.dependency_files = {"tools/three_loader.mjs": {"sha256": sha256(b"synthetic loader"), "size_bytes": 16,
                                                            "mode": "0o644"}}
        self.config = {"schema": CONFIG_SCHEMA, "contract": CONTRACT,
                       "contract_source": descriptor(ROOT / CONTRACT_MD),
                       "amendment_adoption": descriptor(ROOT / ADOPTION_RECORD),
                       "source": {"root": str(provider.ROOT), "commit": hashlib.sha1(b"synthetic commit").hexdigest(),
                                  "tree": hashlib.sha1(b"synthetic tree").hexdigest(), "inventory": descriptor(frozen)},
                       "host": descriptor(frozen),
                       "dependencies": {"root": str(top / "readers"), "inventory": descriptor(frozen)},
                       "runtime": {"executable": str(top / "runtime/bin/node"), "version": runtime_version},
                       "methods": descriptor(frozen), "evidence_root": str(self.evidence), "parent": None}
        self.config_path = write(top / "selection/config.json", canonical(self.config), 0o600)
        self.digest = sha256(self.config_path.read_bytes())
        self.states = []
        self.source_change = None
        self.starts = []

    def state(self, **_):
        if self.states:
            return copy.deepcopy(self.states.pop(0))
        return {"platform": copy.deepcopy(self.host["platform"]), "os": copy.deepcopy(self.host["os"])}

    def changed(self, field):
        state = {"platform": copy.deepcopy(self.host["platform"]), "os": copy.deepcopy(self.host["os"])}
        if field == "boot identity":
            state["platform"]["boot_session_uuid"] = self.OTHER_BOOT
        elif field == "OS build":
            state["os"]["system_version"]["product_build_version"] = "25G84"
        elif field == "cryptex version":
            state["os"]["cryptex"]["product_build_version"] = "25G84"
        else:
            raise KeyError(field)
        return state

    def verify_source(self, source, **_):
        if self.source_change is not None:
            raise provider.CurrentHostBindingError("SOURCE", self.source_change)
        return {"schema": SOURCE_SCHEMA, "files": {}}

    def verify_host(self, config, **_):
        host = copy.deepcopy(self.host)
        provider._VERIFIED["host"] = host
        return host

    def delegate(self, argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):
        self.starts.append(list(argv))
        record = {"argv": argv, "cwd": str(stage), "environment": env, "label": label,
                  "start_monotonic": time.monotonic(), "pid": 424242, "process_group": 424242, "returncode": None,
                  "observed_log_bytes": 0, "retained_log_bytes": 0, "cleanup": None, "handles_closed": False,
                  "error": None}
        on_started(dict(record))
        write(Path(stage) / "probe.json", b'{"passed":true}', 0o600)
        return dict(record, returncode=0, handles_closed=True, end_monotonic=time.monotonic(),
                    cleanup={"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 0})

    @contextlib.contextmanager
    def boundaries(self, *, real_host=False, after_write=None):
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.dict(provider._VERIFIED, {"host": None}))
            stack.enter_context(mock.patch.object(provider, "_host_git", side_effect=lambda config, **_: {
                "path": self.host["git"]["path"], "sha256": self.host["git"]["sha256"]}))
            stack.enter_context(mock.patch.object(provider, "_verify_source", side_effect=self.verify_source))
            if not real_host:
                stack.enter_context(mock.patch.object(provider, "_verify_host", side_effect=self.verify_host))
            stack.enter_context(mock.patch.object(provider, "_cross_bindings", return_value=None))
            stack.enter_context(mock.patch.object(provider, "_verify_dependencies", side_effect=lambda config, **_: {
                "files": copy.deepcopy(self.dependency_files)}))
            stack.enter_context(mock.patch.object(provider, "_verify_methods", return_value={}))
            self.host_state = stack.enter_context(mock.patch.object(provider, "host_state", side_effect=self.state))
            stack.enter_context(mock.patch.object(darwin, "run_process", side_effect=self.delegate))
            stack.enter_context(mock.patch.object(original, "run_process",
                                                  side_effect=AssertionError("the Linux supervisor was started")))
            if after_write is not None:
                real_write = provider._write_new

                def hooked(path, value):
                    written = real_write(path, value)
                    after_write(Path(path))
                    return written
                stack.enter_context(mock.patch.object(provider, "_write_new", side_effect=hooked))
            yield

    def prepare(self):
        with self.boundaries():
            manifest, digest = provider.prepare_case_manifest(self.manifest_path, config_path=self.config_path,
                                                              config_sha256=self.digest, source_root=provider.ROOT,
                                                              schedule_root=self.schedule)
        self.stage.mkdir()
        artifact = write(self.stage / "synthetic.glb", b"glTF synthetic control bytes", 0o644)
        audit = write(self.stage / "synthetic-audit.json", b'{"passed":true}', 0o644)
        job = {"slot": "CPU-" + self.case, "case": "Q01", "manifest": str(self.manifest_path),
               "supplemental_manifest_sha256": digest, "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
               "artifact": str(artifact), "artifact_sha256": sha256(artifact.read_bytes()), "audit": str(audit),
               "audit_sha256": sha256(audit.read_bytes()), "result": str(self.stage / "probe.json")}
        write(self.stage / "job.json", canonical(job), 0o644)
        self.argv = manifest["slots"][0]["argv"][:-1] + [str(self.stage / "job.json")]
        return self

    def run(self, *, env=None, environment=None, after_write=None):
        """One attempt through the facade's guarded_run_process; environment replaces the two selection variables."""
        selection = {CONFIG_ENV: str(self.config_path), DIGEST_ENV: self.digest} if environment is None else environment
        clock = original.Clock(total_ms=30000)
        started = []
        with self.boundaries(after_write=after_write), mock.patch.dict(os.environ):
            for name in (CONFIG_ENV, DIGEST_ENV):
                os.environ.pop(name, None)
            os.environ.update(selection)
            try:
                result = facade.guarded_run_process(self.argv, stage=self.stage, label="synthetic-readback", clock=clock,
                                                    stage_end=clock.started + 28,
                                                    env=dict(DECLARED_ENVIRONMENT) if env is None else env,
                                                    on_started=started.append)
            except BINDING_ERRORS as exc:
                return SimpleNamespace(result=None, error=exc, started=started)
        return SimpleNamespace(result=result, error=None, started=started)

    def ledger(self):
        path = self.cohort / "provider-ledgers" / self.case / "result.json"
        return json.loads(path.read_bytes()) if path.is_file() else None


class ProviderControls(ControlCase):
    """The 0.2.0 provider's attempt, selection, HOST comparison and reader-tree binding."""

    def world(self, **kwargs):
        return ProviderWorld(self, **kwargs).prepare()

    def assert_attempt_failed_without_start(self, world, outcome):
        self.assertIsNone(outcome.result, "the attempt was accepted")
        self.assertIsInstance(outcome.error, BINDING_ERRORS)
        self.assertEqual(world.starts, [], "a start happened")
        self.assertEqual(outcome.started, [])
        self.assertEqual(outcome.error.refusal_record.get("actual_checker_starts"), 0)
        ledger = world.ledger()
        if ledger is not None:
            self.assertEqual(ledger["actual_checker_starts"], 0)
            self.assertNotEqual(ledger["state"], "COMPLETED")
            self.assertEqual(ledger["labels"]["boundary"], "mocked")

    def test_mc09_baseline_attempt_records_the_boot_identity_around_the_start(self):
        """Label: mocked (Darwin supervisor; host, source, dependency and method verifications); host_state simulated unchanged."""
        world = self.world()
        outcome = world.run()
        self.assertIsNone(outcome.error, outcome.error.as_dict() if outcome.error is not None else None)
        self.assertEqual(len(world.starts), 1)
        ledger = world.ledger()
        self.assertEqual(ledger["state"], "COMPLETED")
        self.assertEqual(ledger["actual_checker_starts"], 1)
        self.assertEqual(ledger["boot_before"]["boot_session_uuid"], world.BOOT)
        self.assertEqual(ledger["boot_after"]["boot_session_uuid"], world.BOOT)
        self.assertEqual(ledger["labels"]["boundary"], "mocked")

    def assert_change_before_the_start(self, field):
        world = self.world()
        world.states = [world.changed(field)]
        outcome = world.run()
        self.assert_attempt_failed_without_start(world, outcome)
        self.assertIsNone(world.ledger()["boot_before"])

    def assert_change_across_the_start(self, field):
        world = self.world()
        world.states = [world.state(), world.changed(field)]
        outcome = world.run()
        self.assertIsNone(outcome.result, "the attempt was accepted")
        self.assertIsInstance(outcome.error, BINDING_ERRORS)
        self.assertEqual(len(world.starts), 1)
        ledger = world.ledger()
        self.assertNotEqual(ledger["state"], "COMPLETED")
        self.assertIsNotNone(ledger["provider_failure"])
        self.assertEqual(ledger["actual_checker_starts"], 1)
        self.assertIsNone(ledger["boot_after"])

    def test_mc09_simulated_boot_identity_change_before_the_start_fails_the_attempt(self):
        """Label: simulated (host_state boundary answers another kern.bootsessionuuid before the start); supervisor mocked."""
        self.assert_change_before_the_start("boot identity")

    def test_mc09_simulated_os_build_change_before_the_start_fails_the_attempt(self):
        """Label: simulated (host_state boundary answers another OS build before the start); supervisor mocked."""
        self.assert_change_before_the_start("OS build")

    def test_mc09_simulated_cryptex_version_change_before_the_start_fails_the_attempt(self):
        """Label: simulated (host_state boundary answers another cryptex version before the start); supervisor mocked."""
        self.assert_change_before_the_start("cryptex version")

    def test_mc09_simulated_boot_identity_change_across_the_start_fails_the_attempt(self):
        """Label: simulated (host_state boundary answers another kern.bootsessionuuid after the start); supervisor mocked."""
        self.assert_change_across_the_start("boot identity")

    def test_mc09_simulated_os_build_change_across_the_start_fails_the_attempt(self):
        """Label: simulated (host_state boundary answers another OS build after the start); supervisor mocked."""
        self.assert_change_across_the_start("OS build")

    def test_mc09_simulated_cryptex_version_change_across_the_start_fails_the_attempt(self):
        """Label: simulated (host_state boundary answers another cryptex version after the start); supervisor mocked."""
        self.assert_change_across_the_start("cryptex version")

    # MC29 ------------------------------------------------------------------

    def assert_changed_after_preflight(self, change):
        world = self.world()
        applied = []

        def after_write(path):
            if path.name == "preflight.json" and not applied:
                applied.append(path)
                change(world)
        outcome = world.run(after_write=after_write)
        self.assertEqual(len(applied), 1, "the preflight record was never written")
        self.assert_attempt_failed_without_start(world, outcome)

    def test_mc29_job_input_change_after_preflight_invalidates_the_attempt_with_zero_starts(self):
        """Label: mocked (Darwin supervisor; host, source, dependency and method verifications).

        The change itself is real: a bound job input file is rewritten after preflight.
        """
        self.assert_changed_after_preflight(lambda world: write(world.stage / "synthetic.glb", b"glTF changed bytes", 0o644))

    def test_mc29_configuration_change_after_preflight_invalidates_the_attempt_with_zero_starts(self):
        """Label: mocked (Darwin supervisor; host, source, dependency and method verifications).

        The change itself is real: the selected configuration's bytes change after preflight.
        """
        def change(world):
            write(world.config_path, world.config_path.read_bytes() + b" ", 0o600)
        self.assert_changed_after_preflight(change)

    def test_mc29_simulated_source_change_after_preflight_invalidates_the_attempt_with_zero_starts(self):
        """Label: simulated (the source verification boundary reports a change at the launch check)."""
        def change(world):
            world.source_change = "Simulated: the bound source changed after preflight"
        self.assert_changed_after_preflight(change)

    def test_mc29_simulated_runtime_change_after_preflight_invalidates_the_attempt_with_zero_starts(self):
        """Label: simulated (the HOST verification boundary answers another Node executable pin at the launch check)."""
        def change(world):
            world.host["runtime"]["binding"]["sha256"] = sha256(b"another node executable")
        self.assert_changed_after_preflight(change)

    def test_mc29_simulated_dependency_change_after_preflight_invalidates_the_attempt_with_zero_starts(self):
        """Label: simulated (the reader-tree verification boundary answers another file binding at the launch check)."""
        def change(world):
            world.dependency_files["tools/three_loader.mjs"]["sha256"] = sha256(b"another loader")
        self.assert_changed_after_preflight(change)

    def test_mc29_simulated_os_build_change_after_preflight_invalidates_the_attempt_with_zero_starts(self):
        """Label: simulated (host_state boundary answers another OS build after preflight)."""
        def change(world):
            world.states = [world.changed("OS build")]
        self.assert_changed_after_preflight(change)

    # MC29 with contract section 1: a cohort keeps the version its setup selected (refreeze 002, I-01) -----

    def test_mc29_configuration_change_after_setup_is_refused_and_accounted_by_the_0_2_0_cohort_only(self):
        """Label: mocked (Darwin supervisor; host, source, dependency and method verifications). The change is real.

        Refreeze 002, review finding I-01 (D-20): the facade's setup selects 0.2.0; the configuration's bytes then
        change, so that the selection alone would no longer select 0.2.0. One attempt and the cohort accounting
        follow through the facade, as the readback class's first method and its teardown call them. Both are the
        0.2.0 provider's and refuse; no 0.1.0 document is written; the 0.2.0 accounting records the refusal with
        its labels; the binding ends after the accounting.
        """
        world = ProviderWorld(self)
        started = []
        Cohort = type("Cohort", (), {"__doc__": "Stands for the readback CPU class that the facade's seams take."})
        with world.boundaries(), mock.patch.dict(os.environ), \
                mock.patch.dict(facade._COHORT_BINDING, {"version": None}):
            os.environ.pop("STATIC_TRAY_READBACK_CPU_OUTPUT", None)
            os.environ.update({CONFIG_ENV: str(world.config_path), DIGEST_ENV: world.digest})
            facade.setup_cpu_cohort(Cohort)
            setup_version = vars(Cohort).get(facade.DISPATCH_VERSION_ATTRIBUTE)
            setup_record = json.loads((Cohort.root / "setup.json").read_bytes())
            stage = Cohort.root / "Q01-positive"
            stage.mkdir()
            artifact = write(stage / "synthetic.glb", b"glTF synthetic control bytes", 0o644)
            audit = write(stage / "synthetic-audit.json", b'{"passed":true}', 0o644)
            job = {"slot": "CPU-Q01-positive", "case": "Q01", "manifest": str(Cohort.manifest_path),
                   "supplemental_manifest_sha256": Cohort.manifest_hash,
                   "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE", "artifact": str(artifact),
                   "artifact_sha256": sha256(artifact.read_bytes()), "audit": str(audit),
                   "audit_sha256": sha256(audit.read_bytes()), "result": str(stage / "probe.json")}
            write(stage / "job.json", canonical(job), 0o644)
            argv = Cohort.manifest["slots"][0]["argv"][:-1] + [str(stage / "job.json")]
            write(world.config_path, world.config_path.read_bytes() + b" ", 0o600)
            selected_after_change, bound_after_change = facade._environment_version(), facade._bound_version()
            clock = original.Clock(total_ms=30000)
            with self.assertRaises(BINDING_ERRORS) as attempt:
                facade.guarded_run_process(argv, stage=stage, label="synthetic-readback", clock=clock,
                                           stage_end=clock.started + 28, env=dict(Cohort.manifest["environment"]),
                                           on_started=started.append)
            with self.assertRaises(BINDING_ERRORS) as accounting:
                facade.finish_cpu_cohort(Cohort)
            binding_after, bound_after = dict(facade._COHORT_BINDING), facade._bound_version()
        documents = {}
        for path in sorted(world.evidence.rglob("*.json")):
            value = json.loads(path.read_bytes())
            if type(value) is dict and type(value.get("schema")) is str:
                documents[path.relative_to(world.evidence).as_posix()] = value
        schemas = {rel: value["schema"] for rel, value in documents.items()}
        evidence("MC29-I-01", attempt=attempt.exception.as_dict(), accounting=accounting.exception.as_dict(),
                 schemas=schemas, binding_after=binding_after)
        # Premises: the setup was the 0.2.0 provider's and passed; the change alone would select 0.1.0.
        self.assertEqual(setup_version, "0.2.0")
        self.assertEqual(setup_record["schema"], "ontokin.current-host-readback-setup/0.2.0")
        self.assertIs(setup_record["passed"], True, setup_record.get("error"))
        self.assertEqual(selected_after_change, "0.1.0", "premise: the changed bytes no longer select 0.2.0")
        self.assertEqual(bound_after_change, "0.2.0", "the cohort did not keep the version its setup selected")
        # The attempt: refused by the 0.2.0 provider for the changed configuration, with zero starts.
        self.assertIs(type(attempt.exception), provider.CurrentHostBindingError, "the attempt was not the 0.2.0 provider's")
        self.assertEqual(attempt.exception.code, "CH-SELECTION", attempt.exception.as_dict())
        self.assertEqual(attempt.exception.refusal_record["schema"], "ontokin.current-host-readback-refusal/0.2.0")
        self.assertEqual(attempt.exception.refusal_record["actual_checker_starts"], 0)
        self.assertEqual(attempt.exception.refusal_record["labels"]["boundary"], "mocked")
        self.assertEqual(world.starts, [], "a start happened")
        self.assertEqual(started, [])
        # The accounting: refused by the 0.2.0 provider and recorded as cohort/0.2.0 with its labels.
        self.assertIs(type(accounting.exception), provider.CurrentHostBindingError,
                      "the accounting was not the 0.2.0 provider's")
        self.assertEqual(accounting.exception.code, "CH-SELECTION", accounting.exception.as_dict())
        self.assertEqual(accounting.exception.refusal_record["schema"], "ontokin.current-host-readback-refusal/0.2.0")
        self.assertFalse([rel for rel, schema in schemas.items() if schema.endswith("/0.1.0")], schemas)
        self.assertTrue(all(schema.startswith("ontokin.current-host-readback-") and schema.endswith("/0.2.0")
                            for schema in schemas.values()), schemas)
        cohorts = [value for rel, value in documents.items() if Path(rel).name == "cohort.json"]
        self.assertTrue(cohorts, "the accounting recorded no cohort document")
        host = world.host
        for record in cohorts:
            self.assertEqual(record["schema"], "ontokin.current-host-readback-cohort/0.2.0")
            self.assertEqual([record.get(key) for key in ("contract", "design_revision", "amendments")],
                             [CONTRACT, 4, ["P33-AMENDMENT-001"]])
            self.assertIs(record["passed"], False)
            self.assertEqual(record["error"]["code"], "CH-SELECTION", record["error"])
            self.assertEqual(record["labels"], {
                "executor": "macos-arm64-local", "contract": CONTRACT, "design_revision": 4,
                "amendments": ["P33-AMENDMENT-001"], "profile": "darwin-arm64-v1", "run_kind": "qualifying",
                "boundary": "mocked", "os": host["labels"]["os"], "node": host["labels"]["node"],
                "python_inventory_sha256": host["python"]["inventory_sha256"],
                "git": {"path": host["git"]["path"], "sha256": host["git"]["sha256"]}})
        # The binding ended after the accounting: the facade follows the selection again.
        self.assertEqual(binding_after, {"version": None}, "the module's cohort binding did not end")
        self.assertNotIn(facade.DISPATCH_VERSION_ATTRIBUTE, vars(Cohort), "the class's binding did not end")
        self.assertEqual(bound_after, "0.1.0")

    # MC21 at the provider --------------------------------------------------

    def test_mc21_provider_missing_selection_file_refuses_with_zero_starts(self):
        """Label: mocked (Darwin and Linux supervisors). The selected path names no file."""
        world = self.world()
        outcome = world.run(environment={CONFIG_ENV: str(world.config_path.parent / "absent.json"),
                                         DIGEST_ENV: world.digest})
        self.assert_attempt_failed_without_start(world, outcome)

    def test_mc21_provider_partial_selection_refuses_with_zero_starts(self):
        """Label: mocked (supervisors). Exactly one of the two selection variables."""
        for label, environment in (("only the path", {CONFIG_ENV: "config"}), ("only the digest", {DIGEST_ENV: "digest"})):
            with self.subTest(label):
                world = self.world()
                values = {name: (str(world.config_path) if name == CONFIG_ENV else world.digest) for name in environment}
                self.assert_attempt_failed_without_start(world, world.run(environment=values))

    def test_mc21_provider_malformed_selection_refuses_with_zero_starts(self):
        """Label: mocked (supervisors). A digest that is not lowercase hexadecimal, or a configuration that is not JSON."""
        world = self.world()
        self.assert_attempt_failed_without_start(world, world.run(environment={CONFIG_ENV: str(world.config_path),
                                                                               DIGEST_ENV: world.digest.upper()}))
        world = self.world()
        broken = write(world.config_path.parent / "not-json.json", b"not json\n", 0o600)
        self.assert_attempt_failed_without_start(world, world.run(environment={
            CONFIG_ENV: str(broken), DIGEST_ENV: sha256(broken.read_bytes())}))

    def test_mc21_provider_mismatched_selection_digest_refuses_with_zero_starts(self):
        """Label: mocked (supervisors). The supplied digest is another file's."""
        world = self.world()
        self.assert_attempt_failed_without_start(world, world.run(environment={
            CONFIG_ENV: str(world.config_path), DIGEST_ENV: sha256(b"another configuration")}))

    def test_mc21_provider_partial_selection_fails_setup_and_is_not_an_ordinary_run(self):
        """Label: real (the facade's class setup). Exactly one selection variable."""
        class Cohort:
            pass
        with mock.patch.dict(os.environ):
            os.environ.pop(DIGEST_ENV, None)
            os.environ[CONFIG_ENV] = str(self.base / "config.json")
            with self.assertRaises(BINDING_ERRORS) as caught:
                facade.setup_cpu_cohort(Cohort)
        self.assertNotEqual(caught.exception.reason, ORDINARY_REASON)
        self.assertNotIsInstance(caught.exception, unittest.SkipTest)

    # MC22 at the provider --------------------------------------------------

    def assert_ordinary_setup(self, setup):
        class Cohort:
            pass
        with mock.patch.dict(os.environ):
            os.environ.pop(CONFIG_ENV, None)
            os.environ.pop(DIGEST_ENV, None)
            with self.assertRaises(BINDING_ERRORS) as caught:
                setup(Cohort)
        error = caught.exception
        self.assertNotIsInstance(error, unittest.SkipTest)
        self.assertEqual(error.reason, ORDINARY_REASON)
        self.assertEqual(str(error), ORDINARY_REASON)
        self.assertEqual(error.refusal_record["run_kind"], "ordinary")
        self.assertEqual(error.refusal_record["actual_checker_starts"], 0)
        self.assertIsNone(Cohort.root)

    def test_mc22_facade_setup_of_an_ordinary_run_fails_visibly_with_the_fixed_reason(self):
        """Label: real (the facade setup_cpu_cohort that the readback class calls). Neither selection variable."""
        self.assert_ordinary_setup(facade.setup_cpu_cohort)

    def test_mc22_v02_setup_of_an_ordinary_run_fails_visibly_with_the_fixed_reason(self):
        """Label: real (current_host_readback_v02.setup_cpu_cohort invoked directly). Neither selection variable."""
        self.assert_ordinary_setup(provider.setup_cpu_cohort)

    # MC30 and MC31 at the provider -----------------------------------------

    def test_mc30_provider_host_comparison_admits_the_declared_environment_with_and_without_the_variable(self):
        """Label: mocked (synthetic HOST environment records; the record without the variable is the contract's simulated case)."""
        for recorded in (CF_VALUE, None):
            with self.subTest(recorded=recorded):
                host = {"environment": {"declared": dict(DECLARED_ENVIRONMENT), "cf_user_text_encoding": recorded}}
                self.assertEqual(provider._check_environment_record(host), recorded)

    def test_mc31_provider_host_comparison_refuses_an_extra_variable_or_a_malformed_record(self):
        """Label: simulated (synthetic HOST environment records)."""
        records = {"an extra declared variable": ({**DECLARED_ENVIRONMENT, "ONTOKIN_EXTRA_CONTROL": "1"}, CF_VALUE),
                   "the variable among the declared ones": ({**DECLARED_ENVIRONMENT, CF_NAME: CF_VALUE}, CF_VALUE),
                   "an empty recorded value": (dict(DECLARED_ENVIRONMENT), "")}
        for label, (declared, recorded) in records.items():
            with self.subTest(label):
                with self.assertRaises(provider.CurrentHostBindingError):
                    provider._check_environment_record({"environment": {"declared": declared,
                                                                        "cf_user_text_encoding": recorded}})

    def test_mc31_provider_launch_environment_other_than_the_declared_one_refuses_with_zero_starts(self):
        """Label: mocked (Darwin supervisor; verifications). The launch environment carries an extra variable or the variable."""
        for label, env in (("an extra variable", {**DECLARED_ENVIRONMENT, "ONTOKIN_EXTRA_CONTROL": "1"}),
                           ("the variable", {**DECLARED_ENVIRONMENT, CF_NAME: CF_VALUE})):
            with self.subTest(label):
                world = self.world()
                self.assert_attempt_failed_without_start(world, world.run(env=env))

    # MC33 at the provider --------------------------------------------------

    def test_mc33_provider_configuration_declaring_another_node_version_is_refused_before_any_start(self):
        """Label: mocked (source verification and supervisors); the HOST verification is the provider's own."""
        world = ProviderWorld(self, runtime_version="v24.22.0")
        with world.boundaries(real_host=True), mock.patch.object(
                provider, "_host_document", side_effect=AssertionError("HOST was read")) as host_document:
            with self.assertRaises(provider.CurrentHostBindingError):
                provider.validate_selection(world.config_path, world.digest, provider.ROOT)
            self.assertEqual(host_document.call_count, 0)
            self.assertEqual(world.host_state.call_count, 0)
        self.assertEqual(world.starts, [])

    # MC18 ------------------------------------------------------------------

    def reader_world(self):
        names = sorted(provider.dependency_inventory(ROOT))
        root = self.directory("readers")
        versions = {"validator/package/package.json": b'{"name":"gltf-validator","version":"2.0.0-dev.3.10"}\n',
                    "indexer-view/three/package.json": b'{"name":"three","version":"0.186.1"}\n'}
        for name in names:
            write(root / name, versions.get(name, ("// synthetic reader file %s; never executed\n" % name).encode("ascii")))
        directories = sorted({"/".join(name.split("/")[:index]) for name in names
                              for index in range(1, len(name.split("/")))})
        for name in directories:
            os.chmod(root / name, 0o755)
        os.chmod(root, 0o755)
        archive = write(self.directory("archives") / "c195-synthetic.tar.gz", b"synthetic reader archive bytes\n")
        inventory = {"schema": DEPENDENCIES_SCHEMA, "files": {name: binding(root / name) for name in names},
                     "directories": {name: oct(stat.S_IMODE(os.lstat(root / name).st_mode)) for name in directories},
                     "archive": descriptor(archive)}
        inventory_path = write(self.directory("inventories") / "dependencies.json", canonical(inventory))
        return SimpleNamespace(root=root, names=names, archive=archive,
                               pins={name: {"sha256": row["sha256"], "size_bytes": row["size_bytes"]}
                                     for name, row in inventory["files"].items()},
                               config={"dependencies": {"root": str(root), "inventory": descriptor(inventory_path)},
                                       "source": {"root": str(ROOT)}})

    def verify_readers(self, world):
        with mock.patch.object(provider, "dependency_inventory", return_value=copy.deepcopy(world.pins)), \
                mock.patch.object(provider, "ARCHIVE_SHA256", sha256(world.archive.read_bytes())):
            return provider._verify_dependencies(world.config)

    def assert_readers_refused(self, world):
        with self.assertRaises(provider.CurrentHostBindingError) as caught:
            self.verify_readers(world)
        self.assertEqual(caught.exception.code, "CH-DEPENDENCY")

    def test_mc18_exact_reader_tree_is_accepted_baseline(self):
        """Label: simulated (the C199 pin source and the C195 archive pin name the synthetic 24 files)."""
        world = self.reader_world()
        self.assertEqual(len(world.names), 24)
        self.assertEqual(set(self.verify_readers(world)["files"]), set(world.names))

    def test_mc18_missing_reader_file_is_refused(self):
        """Label: simulated (pin source). One of the 24 files is missing."""
        world = self.reader_world()
        os.unlink(world.root / world.names[0])
        self.assert_readers_refused(world)

    def test_mc18_extra_reader_file_is_refused(self):
        """Label: simulated (pin source). An extra file in the reader tree."""
        world = self.reader_world()
        write(world.root / "extra.js", b"// extra\n")
        self.assert_readers_refused(world)

    def test_mc18_changed_reader_file_is_refused(self):
        """Label: simulated (pin source). One file's bytes change."""
        world = self.reader_world()
        name = world.names[-1]
        data = bytearray((world.root / name).read_bytes())
        data[0] ^= 0x01
        write(world.root / name, bytes(data))
        self.assert_readers_refused(world)

    def test_mc18_symlinked_reader_file_is_refused(self):
        """Label: simulated (pin source). One file is replaced by a link to identical bytes."""
        world = self.reader_world()
        name = world.names[1]
        copy_path = write(self.directory("elsewhere") / "copy", (world.root / name).read_bytes())
        os.unlink(world.root / name)
        os.symlink(str(copy_path), str(world.root / name))
        self.assert_readers_refused(world)

    def test_mc18_ds_store_in_the_reader_tree_is_refused(self):
        """Label: simulated (pin source). A .DS_Store at the root and in a subdirectory."""
        for where in (".DS_Store", "validator/package/.DS_Store"):
            with self.subTest(where=where):
                world = self.reader_world()
                write(world.root / where, b"\0\0\0\1Bud1")
                self.assert_readers_refused(world)


# ---------------------------------------------------------------------------
# MC19: the source binding with a bound Git (contract sections 7 and S9; plan section 4.5)
# ---------------------------------------------------------------------------

class SourceRepository:
    """A synthetic Git checkout holding the /0.2.0 source path set; the provider reads it through a stand-in Git."""

    def __init__(self, top):
        self.top = top
        self.root = top / "checkout"
        self.git_path = shutil.which("git")
        if self.git_path is None:
            raise AssertionError("MC19 needs a Git on PATH to build its synthetic repository")
        self.git_path = os.path.abspath(self.git_path)
        files = list(observation.SOURCE_FILES) + [
            "ontokin/__init__.py", "tests/test_synthetic_source.py", "tools/static_tray_reader_v01/README.md",
            "prototypes/static_tray_v01/current_host_readback_v02.py",
            "prototypes/static_tray_v01/current_host_readback_v02.mjs"]
        for rel in files:
            write(self.root / rel, ("synthetic MC19 source: %s\n" % rel).encode("ascii"))
        self.environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
        self.git("-c", "init.defaultBranch=control", "init", "-q")
        self.git("add", "-A")
        self.git("-c", "user.name=ontokin-control", "-c", "user.email=control@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-q", "-m", "MC19 synthetic source")
        self.commit = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        self.log = top / "git-stand-in.log"
        self.standin = write(top / "bin/git-stand-in", ("#!/bin/sh\nprintf '%%s\\n' \"$*\" >> '%s'\nexec '%s' \"$@\"\n"
                                                        % (self.log, self.git_path)).encode("ascii"), 0o755)
        self.inventories = top / "inventories"
        self.inventories.mkdir()

    def git(self, *args):
        return subprocess.run([self.git_path, "-C", str(self.root), *args], check=True, capture_output=True, text=True,
                              env=self.environment, timeout=60).stdout.strip()

    def source(self):
        """The source record with an inventory document frozen from the checkout's current bytes."""
        files = {rel: binding(self.root / rel) for rel in observation.source_paths(str(self.root))}
        path = write(self.inventories / ("source-%d.json" % len(os.listdir(self.inventories))),
                     canonical({"schema": SOURCE_SCHEMA, "files": files}))
        return {"root": str(self.root), "commit": self.commit, "tree": self.tree, "inventory": descriptor(path)}

    def binding(self):
        return {"path": str(self.standin), "sha256": sha256(self.standin.read_bytes())}

    def stand_in_calls(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []


class SourceControls(ControlCase):
    """The provider's _verify_source with the selection's Git bound by check_local.bind_git."""

    GUARDED = False

    def setUp(self):
        super().setUp()
        self.repository = SourceRepository(self.directory("source"))

    def verify(self, source, *, git="stand-in", own_root=False):
        git = self.repository.binding() if git == "stand-in" else git
        real_check_output, starts = subprocess.check_output, []

        def counting(args, **kwargs):
            starts.append(list(args))
            return real_check_output(args, **kwargs)
        with mock.patch.object(check_local, "_GIT_STATE", None), mock.patch.object(subprocess, "check_output", counting):
            try:
                return provider._verify_source(source, git=git, derived=False, own_root=own_root), None, starts
            except provider.CurrentHostBindingError as exc:
                return None, exc, starts

    def assert_source_refused(self, outcome, *, zero_git_starts=False):
        result, error, starts = outcome
        self.assertIsNone(result, "the source was accepted")
        self.assertIsInstance(error, provider.CurrentHostBindingError)
        self.assertEqual(error.code, "CH-SOURCE", error.as_dict())
        if zero_git_starts:
            self.assertEqual(starts, [], "a Git start happened")
            self.assertEqual(self.repository.stand_in_calls(), [])
        return error

    def test_mc19_clean_bound_source_is_accepted_and_every_git_read_runs_the_bound_executable(self):
        """Label: real (Git through a logging stand-in executable; synthetic repository). The baseline."""
        source = self.repository.source()
        result, error, starts = self.verify(source)
        self.assertIsNone(error, error.as_dict() if error is not None else None)
        self.assertEqual(result["schema"], SOURCE_SCHEMA)
        self.assertTrue(starts)
        self.assertEqual({row[0] for row in starts}, {str(self.repository.standin)})
        self.assertEqual(len(self.repository.stand_in_calls()), len(starts))

    def test_mc19_other_checkout_is_refused_before_any_git_start(self):
        """Label: real. The selected root is not the provider's own checkout."""
        self.assert_source_refused(self.verify(self.repository.source(), own_root=True), zero_git_starts=True)

    def test_mc19_dirty_tracked_source_is_refused(self):
        """Label: real (Git through the stand-in). A tracked file changed after the commit."""
        for label in ("the inventory follows the dirty bytes", "the inventory was frozen at the commit"):
            with self.subTest(label):
                self.repository = SourceRepository(self.directory("source"))
                frozen = self.repository.source()
                path = self.repository.root / "tests/test_synthetic_source.py"
                write(path, path.read_bytes() + b"# dirty change\n")
                source = self.repository.source() if label.startswith("the inventory follows") else frozen
                self.assert_source_refused(self.verify(source))

    def test_mc19_untracked_executable_source_is_refused(self):
        """Label: real (Git through the stand-in). An untracked Python file inside a source tree."""
        for label in ("the inventory includes it", "the inventory was frozen at the commit"):
            with self.subTest(label):
                self.repository = SourceRepository(self.directory("source"))
                frozen = self.repository.source()
                write(self.repository.root / "tests/test_untracked_source.py", b"# untracked executable source\n")
                source = self.repository.source() if label == "the inventory includes it" else frozen
                self.assert_source_refused(self.verify(source))

    def test_mc19_changed_provider_or_probe_is_refused(self):
        """Label: real. The bound provider or probe file changes after the inventory froze it."""
        for rel in ("prototypes/static_tray_v01/current_host_readback_v02.py",
                    "prototypes/static_tray_v01/current_host_readback_v02.mjs"):
            with self.subTest(rel):
                self.repository = SourceRepository(self.directory("source"))
                source = self.repository.source()
                path = self.repository.root / rel
                write(path, path.read_bytes() + b"// changed\n")
                self.assert_source_refused(self.verify(source))

    def test_mc19_unbound_or_unbindable_git_is_refused_before_any_git_start(self):
        """Label: real. No Git binding, the /usr/bin/git dispatcher, another digest, a relative path, a link."""
        source = self.repository.source()
        stand_in = self.repository.binding()
        link = self.base / "git-link"
        os.symlink(str(self.repository.standin), str(link))
        variants = {"no binding": None, "the dispatcher": {"path": "/usr/bin/git", "sha256": stand_in["sha256"]},
                    "another digest": {"path": stand_in["path"], "sha256": sha256(b"other bytes")},
                    "a relative path": {"path": "git-stand-in", "sha256": stand_in["sha256"]},
                    "a symbolic link": {"path": str(link), "sha256": stand_in["sha256"]}}
        for label, git in variants.items():
            with self.subTest(label):
                self.assert_source_refused(self.verify(source, git=git), zero_git_starts=True)

    def test_mc19_bound_git_changed_after_binding_is_refused_without_falling_back(self):
        """Label: real. The bound executable's bytes change right after the binding."""
        source = self.repository.source()
        real_bind = check_local.bind_git

        def bind_then_change(path, digest):
            record = real_bind(path, digest)
            write(self.repository.standin, self.repository.standin.read_bytes() + b"# changed after binding\n", 0o755)
            return record
        with mock.patch.object(check_local, "bind_git", bind_then_change):
            self.assert_source_refused(self.verify(source), zero_git_starts=True)


# ---------------------------------------------------------------------------
# MC07 (driver part), MC21, MC22 and MC23 at the driver tools/check_local.py (contract sections 7 and 8)
# ---------------------------------------------------------------------------

UNIT_RUNNER = ("import sys, unittest\n"
               "%s\n"
               "suite = unittest.defaultTestLoader.loadTestsFromTestCase(Cohort)\n"
               "result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)\n"
               "sys.exit(0 if result.wasSuccessful() else 1)\n")


def cohort(q03=None, extra=""):
    """A synthetic three-method readback cohort; q03 replaces its second method."""
    q03 = "    def test_q03_positive(self):\n        pass\n" if q03 is None else q03
    return ("class Cohort(unittest.TestCase):\n" + extra + "    def test_q01_positive(self):\n        pass\n" + q03
            + "    def test_q01_changed_reference(self):\n        pass\n")


SYNTHETIC_UNIT_RESULTS = {
    "a skipped method": cohort("    def test_q03_positive(self):\n        self.skipTest('synthetic skip')\n"),
    "a class-level skip": cohort(extra="    @classmethod\n    def setUpClass(cls):\n        raise unittest.SkipTest('synthetic class skip')\n"),
    "an erroring method": cohort("    def test_q03_positive(self):\n        raise RuntimeError('synthetic error')\n"),
    "a failing method": cohort("    def test_q03_positive(self):\n        self.fail('synthetic failure')\n"),
    "an expected failure": cohort("    @unittest.expectedFailure\n    def test_q03_positive(self):\n        self.fail('synthetic expected failure')\n"),
    "an unexpected success": cohort("    @unittest.expectedFailure\n    def test_q03_positive(self):\n        pass\n"),
    "a class-level setup error": cohort(extra="    @classmethod\n    def setUpClass(cls):\n        raise RuntimeError('synthetic setup error')\n"),
    "a missing method reported by the cohort accounting": cohort(
        "", extra="    @classmethod\n    def tearDownClass(cls):\n        raise RuntimeError('synthetic accounting: a CPU method did not run')\n"),
    "no method at all": "class Cohort(unittest.TestCase):\n    pass\n"}


class DriverControls(ControlCase):
    """The driver's selection rule, unit environment and unit-stage decision; its children are Python (-I -S -B -c)."""

    GUARDED = False

    def setUp(self):
        super().setUp()
        self.stack.enter_context(mock.patch.object(check_local, "_GIT_STATE", None))

    def unit_stage(self, body, *, qualifying=True):
        workspace, output = self.directory("workspace"), self.directory("output")
        step = check_local.Step("unit-tests", tuple(PYTHON_CHILD) + (UNIT_RUNNER % body,))
        selection = None
        if qualifying:
            config = write(self.directory("selection") / "config.json", b'{"synthetic": "unit-stage selection"}\n', 0o600)
            selection = {"config_path": str(config), "config_sha256": sha256(config.read_bytes())}
        record = check_local.execute_step(step, workspace, output, {}, 120, readback_selection=selection)
        return record, (output / record["log"]).read_text(encoding="utf-8", errors="replace")

    def driver_run(self, step, **selection):
        root = self.directory("driver-root")
        write(root / "README.md", b"Synthetic driver root of the gate MI controls.\n")
        self.counter += 1
        output = self.base / ("driver-output-%d" % self.counter)
        real, starts = subprocess.Popen, []

        def counting(*args, **kwargs):
            starts.append(list(args[0] if args else kwargs["args"]))
            return real(*args, **kwargs)
        with mock.patch.object(check_local, "build_plan", return_value=[step]), \
                mock.patch.object(subprocess, "Popen", counting), contextlib.redirect_stdout(io.StringIO()):
            code = check_local.run(root, output, False, 300, **selection)
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        return code, summary, starts, output

    def preparation_run(self, step, **selection):
        """driver_run with the platform.platform() metadata leaf of the environment record mocked.

        Refreeze 001, C-02: the leaf starts uname -p and file -b on its first call in a process only, so a
        count that included it depended on the order of the tests. It is neither a Git start nor a stage
        start. The project's driver tests mock it the same way (113e1b85), as P29's
        INHERITED-METADATA-STUB.json does.
        """
        with mock.patch.object(check_local.platform, "platform", return_value=PLATFORM_METADATA_LEAF) as leaf:
            outcome = self.driver_run(step, **selection)
        evidence("MC21-driver", platform_metadata_leaf_calls=leaf.call_count,
                 recorded_platform=outcome[1].get("environment", {}).get("platform"))
        return outcome

    # MC07 (driver part) ----------------------------------------------------

    def test_mc07_driver_removal_list_removes_the_contracts_names_and_every_dyld_name(self):
        """Label: real (check_local.unit_environment_removals on a synthetic mapping)."""
        environment = {**DECLARED_ENVIRONMENT, **{name: "control" for name in DRIVER_REMOVED_NAMES},
                       "DYLD_INSERT_LIBRARIES": "control", "DYLD_FALLBACK_LIBRARY_PATH": "control", "KEEP_CONTROL": "1"}
        removed = check_local.unit_environment_removals(environment)
        self.assertEqual(sorted(removed), sorted(set(DRIVER_REMOVED_NAMES) | {"DYLD_INSERT_LIBRARIES",
                                                                             "DYLD_FALLBACK_LIBRARY_PATH"}))
        self.assertEqual(len(removed), len(set(removed)))

    def test_mc07_driver_removes_the_names_from_a_qualifying_unit_process(self):
        """Label: real (the driver's execute_step starts one Python unit child, -I -S -B -c, of a qualifying run)."""
        injected = {name: str(self.base / "absent-control-value") for name in DRIVER_REMOVED_NAMES}
        injected.update(DYLD_FALLBACK_LIBRARY_PATH=str(self.base / "absent-library-directory"),
                        DYLD_FALLBACK_FRAMEWORK_PATH=str(self.base / "absent-framework-directory"))
        body = ("class Cohort(unittest.TestCase):\n"
                "    def test_injection_names_are_absent(self):\n"
                "        import os\n"
                "        names = %r\n"
                "        present = sorted(name for name in os.environ if name.startswith('DYLD_') or name in names)\n"
                "        self.assertEqual(present, [])\n") % (DRIVER_REMOVED_NAMES,)
        real, captured = subprocess.Popen, []

        def capturing(*args, **kwargs):
            captured.append(dict(kwargs.get("env") or {}))
            return real(*args, **kwargs)
        with mock.patch.dict(os.environ, injected), mock.patch.object(subprocess, "Popen", capturing):
            record, log = self.unit_stage(body)
        self.assertEqual(len(captured), 1)
        self.assertEqual(sorted(name for name in captured[0] if name in injected), [], "an injection name reached the unit process")
        self.assertTrue(set(injected) <= set(record["removed_injection_environment_names"]))
        self.assertEqual(record["status"], "passed", log)

    # MC21 at the driver ----------------------------------------------------

    def assert_failed_preparation(self, outcome, *, qualifying):
        code, summary, starts, _ = outcome
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["steps"], [], "a stage ran")
        self.assertEqual(starts, [], "a process started before the preparation failed")
        selection = summary["readback_selection"]
        self.assertEqual(selection["status"], "preparation_pending")
        self.assertIn("preparation_or_execution_error", selection)
        if qualifying:
            self.assertEqual(selection.get("run_kind"), "qualifying")
        else:
            self.assertNotIn("run_kind", selection)

    def ordinary_step(self):
        return check_local.Step("unit-tests", tuple(PYTHON_CHILD) + (UNIT_RUNNER % cohort(),))

    def test_mc21_driver_missing_selection_file_fails_preparation(self):
        """Label: mocked (platform.platform metadata leaf; one-stage plan). The configuration file is absent.

        Refreeze 001, C-02: the environment record's platform.platform() metadata leaf is mocked, so that
        zero starts means no Git, stage or other start, whatever the order of the tests.
        """
        outcome = self.preparation_run(self.ordinary_step(), readback_config=self.base / "absent-config.json",
                                       readback_config_sha256=sha256(b"absent"))
        self.assert_failed_preparation(outcome, qualifying=True)

    def test_mc21_driver_partial_selection_fails_preparation(self):
        """Label: mocked (platform.platform metadata leaf; one-stage plan). Exactly one selection argument.

        Refreeze 001, C-02: the environment record's platform.platform() metadata leaf is mocked, so that
        zero starts means no Git, stage or other start, whatever the order of the tests.
        """
        config = write(self.directory("selection") / "config.json", b"{}\n", 0o600)
        for label, selection in (("only the configuration", {"readback_config": config}),
                                 ("only the digest", {"readback_config_sha256": sha256(config.read_bytes())})):
            with self.subTest(label):
                self.assert_failed_preparation(self.preparation_run(self.ordinary_step(), **selection),
                                               qualifying=False)

    def test_mc21_driver_malformed_selection_fails_preparation(self):
        """Label: mocked (platform.platform metadata leaf; one-stage plan). A malformed digest, a relative path, non-JSON or another schema.

        Refreeze 001, C-02: the environment record's platform.platform() metadata leaf is mocked, so that
        zero starts means no Git, stage or other start, whatever the order of the tests.
        """
        folder = self.directory("selection")
        not_json = write(folder / "not-json.json", b"not json\n", 0o600)
        other = write(folder / "other-schema.json", canonical({"schema": "ontokin.current-host-readback-config/9.9.9"}), 0o600)
        variants = {"a digest that is not lowercase hexadecimal": {"readback_config": other,
                                                                    "readback_config_sha256": "ABC"},
                    "a relative configuration path": {"readback_config": Path("relative-config.json"),
                                                      "readback_config_sha256": sha256(other.read_bytes())},
                    "a configuration that is not JSON": {"readback_config": not_json,
                                                         "readback_config_sha256": sha256(not_json.read_bytes())},
                    "a configuration of another schema": {"readback_config": other,
                                                          "readback_config_sha256": sha256(other.read_bytes())}}
        for label, selection in variants.items():
            with self.subTest(label):
                self.assert_failed_preparation(self.preparation_run(self.ordinary_step(), **selection),
                                               qualifying=True)

    def test_mc21_driver_mismatched_selection_digest_fails_preparation(self):
        """Label: mocked (platform.platform metadata leaf; one-stage plan). The supplied digest is another file's.

        Refreeze 001, C-02: the environment record's platform.platform() metadata leaf is mocked, so that
        zero starts means no Git, stage or other start, whatever the order of the tests.
        """
        config = write(self.directory("selection") / "config.json", b"{}\n", 0o600)
        outcome = self.preparation_run(self.ordinary_step(), readback_config=config,
                                       readback_config_sha256=sha256(b"another configuration"))
        self.assert_failed_preparation(outcome, qualifying=True)

    # MC22 at the driver ----------------------------------------------------

    def test_mc22_ordinary_run_proceeds_and_the_readback_setup_fails_visibly_without_a_skip(self):
        """Label: real (the driver's run; its plan is substituted by one unit stage that runs the real readback module)."""
        code_text = ("import sys, unittest\n"
                     "sys.path.insert(0, %r)\n"
                     "suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_static_tray_readback_v01')\n"
                     "result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)\n"
                     "sys.exit(0 if result.wasSuccessful() else 1)\n") % str(ROOT)
        step = check_local.Step("unit-tests", tuple(PYTHON_CHILD) + (code_text,))
        with mock.patch.dict(os.environ):
            os.environ.pop(CONFIG_ENV, None)
            os.environ.pop(DIGEST_ENV, None)
            code, summary, starts, output = self.driver_run(step)
        self.assertEqual(summary["readback_selection"], {"status": "absent", "run_kind": "ordinary"})
        self.assertNotIn("error", summary, "the driver refused to proceed")
        self.assertEqual([row["id"] for row in summary["steps"]], ["unit-tests"])
        stage = summary["steps"][0]
        self.assertIs(stage["process_started"], True)
        self.assertEqual(stage["status"], "failed")
        self.assertEqual(stage["test_execution"]["skipped"], 0, "a skip was reported")
        self.assertEqual(stage["test_execution"]["expected_failures"], 0)
        self.assertIs(stage["test_execution"]["complete_regression_passed"], False)
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "failed")
        log = (output / stage["log"]).read_text(encoding="utf-8", errors="replace")
        self.assertIn(ORDINARY_REASON, log)
        self.assertIn("setUpClass", log)
        self.assertIn("ReadbackCPUControls", log)
        for name in class_test_methods(READBACK_TESTS, "ReadbackCPUControls"):
            self.assertNotIn(name, log, "a readback CPU method was run or reported")
        for name in class_test_methods(READBACK_TESTS, "ReadbackCoordinatorSeams"):
            self.assertRegex(log, re.escape(name) + r" \(.*\) \.\.\. ok", "a coordinator seam did not run")
        unit_starts = [argv for argv in starts if argv[:5] == list(PYTHON_CHILD)]
        self.assertEqual(len(unit_starts), 1)
        self.assertFalse([argv for argv in starts if os.path.basename(argv[0]) == "node"])

    # MC23 (the driver's decision on synthetic unit results) ----------------

    def test_mc23_passing_synthetic_cohort_passes_the_qualifying_unit_stage_baseline(self):
        """Label: real (execute_step of a qualifying run; one synthetic Python unit child). The baseline."""
        record, log = self.unit_stage(cohort())
        self.assertEqual(record["status"], "passed", log)
        self.assertEqual(record["test_execution"], {"tests_run": 3, "skipped": 0, "expected_failures": 0,
                                                    "executed_without_skips": 3, "complete_regression_passed": True})

    def assert_unit_stage_not_qualified(self, label):
        record, log = self.unit_stage(SYNTHETIC_UNIT_RESULTS[label])
        self.assertEqual(record["status"], "failed", log)
        self.assertIs(record["test_execution"]["complete_regression_passed"], False)
        return record

    def test_mc23_skipped_method_fails_the_qualifying_unit_stage(self):
        """Label: real (synthetic unit result). One method skips."""
        self.assertGreaterEqual(self.assert_unit_stage_not_qualified("a skipped method")["test_execution"]["skipped"], 1)

    def test_mc23_class_level_skip_fails_the_qualifying_unit_stage(self):
        """Label: real (synthetic unit result). The class setup raises SkipTest."""
        self.assert_unit_stage_not_qualified("a class-level skip")

    def test_mc23_erroring_method_fails_the_qualifying_unit_stage(self):
        """Label: real (synthetic unit result). One method errors."""
        self.assert_unit_stage_not_qualified("an erroring method")

    def test_mc23_failing_method_fails_the_qualifying_unit_stage(self):
        """Label: real (synthetic unit result). One method fails."""
        self.assert_unit_stage_not_qualified("a failing method")

    def test_mc23_expected_failure_fails_the_qualifying_unit_stage(self):
        """Label: real (synthetic unit result). One method is an expected failure (exit status 0)."""
        record = self.assert_unit_stage_not_qualified("an expected failure")
        self.assertGreaterEqual(record["test_execution"]["expected_failures"], 1)

    def test_mc23_unexpected_success_fails_the_qualifying_unit_stage(self):
        """Label: real (synthetic unit result). An expected failure passes."""
        self.assert_unit_stage_not_qualified("an unexpected success")

    def test_mc23_class_level_setup_error_fails_the_qualifying_unit_stage(self):
        """Label: real (synthetic unit result). The class setup raises."""
        self.assert_unit_stage_not_qualified("a class-level setup error")

    def test_mc23_missing_method_reported_by_the_cohort_accounting_fails_the_qualifying_unit_stage(self):
        """Label: simulated (the provider's cohort accounting is simulated by a class teardown error, D-08)."""
        self.assert_unit_stage_not_qualified("a missing method reported by the cohort accounting")

    def test_mc23_unit_stage_that_runs_no_method_fails_the_qualifying_unit_stage(self):
        """Label: real (synthetic unit result). No method is discovered or run."""
        self.assert_unit_stage_not_qualified("no method at all")


# ---------------------------------------------------------------------------
# MC11: the reviewed static scan (contract section 5, "No descendant")
# ---------------------------------------------------------------------------

class StaticScanControls(ControlCase):
    """The scan of the 0.2.0 probe at MI; the module loader and the 24 reader files are scanned at MH."""

    def test_mc11_probe_scan_finds_no_process_creation_and_only_reviewed_dynamic_constructs(self):
        """Label: real (a name scan of the 0.2.0 probe's bytes). Its limit: a scan of names cannot exclude every dynamic route."""
        scan = scan_javascript(PROBE_PATH.read_text(encoding="utf-8"))
        evidence("MC11", probe_sha256=sha256(PROBE_PATH.read_bytes()), scan=scan)
        self.assertEqual(scan["process_creation"], [], "a process-creation name occurs in the probe")
        self.assertEqual(sorted(scan["dynamic"]), sorted(MC11_REVIEWED_PROBE_DYNAMIC),
                         "a dynamic construct was added, removed or changed and needs review")
        self.assertEqual(sorted(scan["static_specifiers"]), sorted(MC11_REVIEWED_PROBE_SPECIFIERS),
                         "a module specifier was added, removed or changed and needs review")


if __name__ == "__main__":
    unittest.main()
