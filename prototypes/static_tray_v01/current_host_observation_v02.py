"""M0 and M1 host observation for ontokin.current-host-readback/0.2.0, darwin-arm64-v1.

This module replaces the Linux inspector (current_host_inspection_v01.py) for the
macOS arm64 executor class of the adopted 0.2.0 contract, sections 3, 4, 7 and 10.
It uses the Python standard library only. Importing it performs no project
import, no process start and no write.

Operational invocation (the main path), from the declared clean environment:

    PYTHON -I -S -B THIS_FILE static  --plan PLAN --plan-sha256 EXTERNAL_DIGEST
    PYTHON -I -S -B THIS_FILE observe --plan PLAN --plan-sha256 EXTERNAL_DIGEST
    PYTHON -I -S -B THIS_FILE python-inventory --venv VENV --framework DIR --output OUT
    PYTHON -I -S -B THIS_FILE source-inventory --root ROOT --output OUT

* ``static`` validates the plan and every static binding, and starts and writes
  nothing.
* ``observe`` runs M0 (every static binding, then one bounded Git ``--version``
  start) and M1 (one bounded Node ``--version`` start, after Node's byte and
  Mach-O binding), both through the Darwin supervisor, and publishes the HOST
  document under the plan's absent attempt directory.
* The two inventory commands author documents that a plan freezes. They start
  nothing and write only their absent output path.

The plan's digest is always supplied outside the plan. A HOST document is an
observed, unapproved candidate; nothing in this module approves an input.

Trust boundaries: Apple's signed system volume, System Integrity Protection and
the dyld shared cache are assumed, not verified, and system libraries are
identified only by the recorded OS build. The Mach-O parser binds files and
load commands, not runtime behaviour. Universal (fat) files are refused.
Focused tests with mocked boundaries cannot establish any of these properties.
"""
from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import errno
import hashlib
import io
import json
import os
import posixpath
import re
import stat
import struct
import sys
import time
from types import MappingProxyType


# ---------------------------------------------------------------------------
# Identity constants (contract sections 1, 3, 4, 7 and 10)
# ---------------------------------------------------------------------------

CONTRACT = "ontokin.current-host-readback/0.2.0"
PROFILE = "darwin-arm64-v1"
EXECUTOR = "macos-arm64-local"
PREFIX = "ontokin.current-host-readback-"
VERSION = "/0.2.0"
ENTRY_POINT = "prototypes/static_tray_v01/current_host_observation_v02.py"
RUN_KIND = "host-observation"

PLAN_SCHEMA = PREFIX + "observation-plan" + VERSION
HOST_SCHEMA = PREFIX + "host" + VERSION
INSPECTION_SCHEMA = PREFIX + "inspection" + VERSION
ATTEMPT_SCHEMA = PREFIX + "observation-attempt" + VERSION
START_SCHEMA = PREFIX + "observation-start" + VERSION
FAILURE_SCHEMA = PREFIX + "observation-failure" + VERSION
RESERVATION_SCHEMA = PREFIX + "observation-reservation" + VERSION
PREFLIGHT_SCHEMA = PREFIX + "observation-preflight" + VERSION
RESULT_SCHEMA = PREFIX + "observation-result" + VERSION
COMPLETION_SCHEMA = PREFIX + "observation-completion" + VERSION
REFUSAL_SCHEMA = PREFIX + "observation-refusal" + VERSION
PYTHON_INVENTORY_SCHEMA = PREFIX + "python-inventory" + VERSION
SOURCE_SCHEMA = PREFIX + "source" + VERSION
DEPENDENCIES_SCHEMA = PREFIX + "dependencies" + VERSION
NODE_SOURCE_SCHEMA = PREFIX + "node-source" + VERSION
INSTALL_SCHEMA = PREFIX + "install" + VERSION
INSTALL_RESULT_SCHEMA = PREFIX + "install-result" + VERSION

NODE_VERSION = "v24.22.1"
NODE_VERSION_STDOUT = b"v24.22.1\n"
NODE_ARCHIVE = "node-v24.22.1-darwin-arm64.tar.gz"
NODE_ARCHIVE_SHA256 = "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"
NODE_CHECKSUM_FILE = MappingProxyType({
    "url": "https://nodejs.org/dist/v24.22.1/SHASUMS256.txt",
    "sha256": "fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4",
    "size_bytes": 3171})
NODE_MEMBER = "node-v24.22.1-darwin-arm64/bin/node"
NODE_SOURCE_NAME = "NODE-SOURCE.json"
NODE_SOURCE_KEYS = ("schema", "contract", "archive", "checksum_file", "signature_check",
                    "member_inventory_sha256", "extracted")
SIGNATURE_STATES = ("not_performed", "verified", "failed")
RUNTIME_LAYOUT = MappingProxyType({"bin": "directory", "bin/node": "file", NODE_SOURCE_NAME: "file"})

ENVIRONMENT = MappingProxyType({"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                                "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"})
CF_NAME = "__CF_USER_TEXT_ENCODING"
GIT_ENVIRONMENT = MappingProxyType({**ENVIRONMENT, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
                                    "GIT_TERMINAL_PROMPT": "0", "GIT_ATTR_NOSYSTEM": "1",
                                    "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"})
# Diagnostic classes only. The predicate admits nothing outside the declared
# environment apart from CF_NAME with the recorded value.
FORBIDDEN_NAMES = ("__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE", "NODE_OPTIONS", "NODE_PATH", "PYTHONPATH",
                   "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONBREAKPOINT", "PYTHONUSERBASE",
                   "PYTHONPYCACHEPREFIX", "LD_PRELOAD", "LD_LIBRARY_PATH")
FORBIDDEN_PREFIXES = ("DYLD_", "NODE_", "PYTHON")

GIT_DISPATCHER = "/usr/bin/git"
GIT_VERSION_LINE = re.compile(rb"git version [\x20-\x7e]{1,200}\n")
GIT_STDOUT_PREDICATE = "git-version-line-v1"

SYSTEM_VERSION_PATH = "/System/Library/CoreServices/SystemVersion.plist"
CRYPTEX_SYSTEM_VERSION_PATH = "/System/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist"
SYSTEM_LINKS = MappingProxyType({"/tmp": "/private/tmp", "/var": "/private/var", "/etc": "/private/etc"})
SYSTEM_LIBRARY_PREFIXES = ("/usr/lib/", "/System/Library/")
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"
RENAME_EXCL = 0x00000004  # macOS SDK <sys/stdio.h>: #define RENAME_EXCL 0x00000004
UUID_TEXT = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")

LIMITS = MappingProxyType({
    "command_ms": 5000, "active_work_ms": 3000, "cleanup_ms": 2000, "log_bytes": 4 * 1024 * 1024,
    "document_bytes": 16 * 1024 * 1024, "host_bytes": 8 * 1024 * 1024, "inspection_bytes": 8 * 1024 * 1024,
    "static_ms": 60000, "publication_ms": 30000, "tree_entries": 65536, "tree_file_bytes": 512 * 1024 * 1024,
    "plist_bytes": 65536, "macho_commands": 4096, "macho_command_bytes": 4 * 1024 * 1024, "link_hops": 40})
COMMAND_IDS = ("git_version", "node_version")
LABELS = MappingProxyType({"git_version": "host-git-version", "node_version": "host-node-version"})

SOURCE_TREES = ("ontokin", "tests", "prototypes/static_tray_v01", "tools/static_tray_reader_v01")
SOURCE_OPTIONAL = ("prototypes/__init__.py", "tools/__init__.py", "tests/__init__.py")
MACOS_LOCK = "tools/native-reader-verification-macos-arm64-cp312.lock"
EXTERNAL_INPUTS = "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json"
EXTERNAL_SHA256 = "21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5"
SOURCE_FILES = (
    "tools/check_local.py", "tools/prepare_current_host_readback.py", "tools/storage_identity.py",
    "tools/force-agent-verification-requirements.txt", "tools/native-reader-verification-linux-cp312.lock",
    MACOS_LOCK, "pyproject.toml", "docs/engineering/static-tray-mapping-c198/CONTROLS.json", EXTERNAL_INPUTS,
    "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md",
    "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json",
    "docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json",
    "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip",
    "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md",
    "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json",
    "docs/engineering/localized-repair-c271/macos-contract-design-p31/ADOPTION.json")
SUPERVISOR_MODULE = "prototypes.static_tray_v01.supervisor_darwin_v01"
SUPERVISOR_FILES = MappingProxyType({
    "prototypes": "prototypes/__init__.py",
    "prototypes.static_tray_v01": "prototypes/static_tray_v01/__init__.py",
    "prototypes.static_tray_v01.supervisor": "prototypes/static_tray_v01/supervisor.py",
    SUPERVISOR_MODULE: "prototypes/static_tray_v01/supervisor_darwin_v01.py"})
DEPENDENCY_ARCHIVE_SHA256 = "b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9"
DEPENDENCY_VERSIONS = (("validator/package/package.json", "2.0.0-dev.3.10"),
                       ("indexer-view/three/package.json", "0.186.1"))
DEPENDENCY_FILE_COUNT = 24

PYTHON_PINS = MappingProxyType({
    "attrs": "26.1.0", "jsonschema": "4.26.0", "jsonschema-specifications": "2025.9.1",
    "referencing": "0.37.0", "rpds-py": "2026.5.1", "typing_extensions": "4.16.0", "Pillow": "13.0.0"})
PROCESS_IMAGE = "Resources/Python.app/Contents/MacOS/Python"
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")

CLAIMS = MappingProxyType({
    "closure": ("The Node executable's bytes and load commands are bound, and so is the interpreter installation "
                "within the limits of contract section 4. The system libraries come from the OS build's dyld shared "
                "cache in the signed system volume and the OS cryptex and are identified only by the recorded OS "
                "product version, build and cryptex version, not by per-file hashes. Apple's sealed system volume "
                "and System Integrity Protection are assumed, not verified. This is weaker than the Linux plan's "
                "file-by-file closure."),
    "python": ("Binds the files of the interpreter installation and the non-system libraries that its Mach-O files "
               "reference; not their runtime behaviour, nor files that libraries load at run time by their own "
               "logic. Weaker than E4's single image pin."),
    "boot": "The provider, not the probe, binds the boot identity around each start (stated weakening of E19).",
    "status": "OBSERVED_UNAPPROVED: an observed candidate. It approves nothing and selects nothing."})


# ---------------------------------------------------------------------------
# Mach-O constants (<mach-o/loader.h>, <mach-o/fat.h>, <mach/machine.h>)
# ---------------------------------------------------------------------------

MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C
CPU_SUBTYPE_ARM64_ALL = 0
LC_REQ_DYLD = 0x80000000
FILE_TYPES = MappingProxyType({1: "MH_OBJECT", 2: "MH_EXECUTE", 3: "MH_FVMLIB", 4: "MH_CORE", 5: "MH_PRELOAD",
                               6: "MH_DYLIB", 7: "MH_DYLINKER", 8: "MH_BUNDLE", 9: "MH_DYLIB_STUB", 10: "MH_DSYM",
                               11: "MH_KEXT_BUNDLE", 12: "MH_FILESET"})
LOAD_COMMANDS = MappingProxyType({
    0x1: "LC_SEGMENT", 0x2: "LC_SYMTAB", 0x3: "LC_SYMSEG", 0x4: "LC_THREAD", 0x5: "LC_UNIXTHREAD",
    0x6: "LC_LOADFVMLIB", 0x7: "LC_IDFVMLIB", 0x8: "LC_IDENT", 0x9: "LC_FVMFILE", 0xA: "LC_PREPAGE",
    0xB: "LC_DYSYMTAB", 0xC: "LC_LOAD_DYLIB", 0xD: "LC_ID_DYLIB", 0xE: "LC_LOAD_DYLINKER",
    0xF: "LC_ID_DYLINKER", 0x10: "LC_PREBOUND_DYLIB", 0x11: "LC_ROUTINES", 0x12: "LC_SUB_FRAMEWORK",
    0x13: "LC_SUB_UMBRELLA", 0x14: "LC_SUB_CLIENT", 0x15: "LC_SUB_LIBRARY", 0x16: "LC_TWOLEVEL_HINTS",
    0x17: "LC_PREBIND_CKSUM", 0x18 | LC_REQ_DYLD: "LC_LOAD_WEAK_DYLIB", 0x19: "LC_SEGMENT_64",
    0x1A: "LC_ROUTINES_64", 0x1B: "LC_UUID", 0x1C | LC_REQ_DYLD: "LC_RPATH", 0x1D: "LC_CODE_SIGNATURE",
    0x1E: "LC_SEGMENT_SPLIT_INFO", 0x1F | LC_REQ_DYLD: "LC_REEXPORT_DYLIB", 0x20: "LC_LAZY_LOAD_DYLIB",
    0x21: "LC_ENCRYPTION_INFO", 0x22: "LC_DYLD_INFO", 0x22 | LC_REQ_DYLD: "LC_DYLD_INFO_ONLY",
    0x23 | LC_REQ_DYLD: "LC_LOAD_UPWARD_DYLIB", 0x24: "LC_VERSION_MIN_MACOSX",
    0x25: "LC_VERSION_MIN_IPHONEOS", 0x26: "LC_FUNCTION_STARTS", 0x27: "LC_DYLD_ENVIRONMENT",
    0x28 | LC_REQ_DYLD: "LC_MAIN", 0x29: "LC_DATA_IN_CODE", 0x2A: "LC_SOURCE_VERSION",
    0x2B: "LC_DYLIB_CODE_SIGN_DRS", 0x2C: "LC_ENCRYPTION_INFO_64", 0x2D: "LC_LINKER_OPTION",
    0x2E: "LC_LINKER_OPTIMIZATION_HINT", 0x2F: "LC_VERSION_MIN_TVOS", 0x30: "LC_VERSION_MIN_WATCHOS",
    0x31: "LC_NOTE", 0x32: "LC_BUILD_VERSION", 0x33 | LC_REQ_DYLD: "LC_DYLD_EXPORTS_TRIE",
    0x34 | LC_REQ_DYLD: "LC_DYLD_CHAINED_FIXUPS", 0x35 | LC_REQ_DYLD: "LC_FILESET_ENTRY", 0x36: "LC_ATOM_INFO"})
LC = MappingProxyType({name: value for value, name in LOAD_COMMANDS.items()})
NODE_ALLOWED_COMMANDS = frozenset((
    "LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
    "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
    "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
    "LC_DYLD_EXPORTS_TRIE"))
NODE_REFUSED_COMMANDS = frozenset(("LC_RPATH", "LC_DYLD_ENVIRONMENT", "LC_LOAD_UPWARD_DYLIB", "LC_REEXPORT_DYLIB"))
PYTHON_ALLOWED_COMMANDS = NODE_ALLOWED_COMMANDS | {"LC_ID_DYLIB", "LC_RPATH"}
PYTHON_REFUSED_COMMANDS = frozenset(("LC_DYLD_ENVIRONMENT", "LC_LOAD_UPWARD_DYLIB"))
PYTHON_FILE_TYPES = frozenset(("MH_EXECUTE", "MH_DYLIB", "MH_BUNDLE"))
SINGLE_COMMANDS = frozenset((
    "LC_LOAD_DYLINKER", "LC_MAIN", "LC_UUID", "LC_SYMTAB", "LC_DYSYMTAB", "LC_CODE_SIGNATURE",
    "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS", "LC_DYLD_EXPORTS_TRIE", "LC_FUNCTION_STARTS",
    "LC_DATA_IN_CODE", "LC_SOURCE_VERSION", "LC_ID_DYLIB"))
DYLIB_COMMANDS = frozenset(("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_ID_DYLIB", "LC_REEXPORT_DYLIB",
                            "LC_LOAD_UPWARD_DYLIB", "LC_LAZY_LOAD_DYLIB"))
REFERENCE_COMMANDS = frozenset(("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB"))
LINKEDIT_COMMANDS = frozenset(("LC_CODE_SIGNATURE", "LC_SEGMENT_SPLIT_INFO", "LC_FUNCTION_STARTS",
                               "LC_DATA_IN_CODE", "LC_DYLIB_CODE_SIGN_DRS", "LC_LINKER_OPTIMIZATION_HINT",
                               "LC_DYLD_EXPORTS_TRIE", "LC_DYLD_CHAINED_FIXUPS", "LC_ATOM_INFO"))
AT_PREFIXES = ("@rpath/", "@loader_path/", "@executable_path/")


# ---------------------------------------------------------------------------
# Errors and canonical values
# ---------------------------------------------------------------------------

class ObservationError(RuntimeError):
    """Refusal of the observer; unrelated to supervisor.Stop, whose record stays attached as cause."""

    def __init__(self, category, reason, *, cause=None, state="REJECTED", details=None):
        self.category = category
        self.code = "CHO-" + category
        self.reason, self.state = reason, state
        self.cause = cause
        self.details = dict(details or {})
        self.result = None
        self.attempt = None
        super().__init__(reason)

    def as_dict(self):
        return {"code": self.code, "reason": self.reason, "state": self.state,
                "cause": _failure(self.cause), "details": self.details}


def _failure(exc):
    if exc is None:
        return None
    if hasattr(exc, "as_dict"):
        try:
            return exc.as_dict()
        except Exception:  # a foreign as_dict must not hide the original refusal
            pass
    return {"type": type(exc).__name__, "reason": str(exc)}


def _require(condition, category, reason, **kwargs):
    if not condition:
        raise ObservationError(category, reason, **kwargs)


def _macho(condition, rule, reason):
    if not condition:
        raise ObservationError("MACHO", reason, details={"rule": rule})


def _keys(value, expected, category):
    _require(type(value) is dict and set(value) == set(expected), category,
             "Missing or unknown object members; expected " + ", ".join(sorted(expected)))


def _canonical(value):
    """Sorted, compact, ASCII JSON; the same bytes as supervisor.json_bytes."""
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                          allow_nan=False).encode("ascii")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ObservationError("EVIDENCE", "Value has no canonical JSON form", cause=exc) from exc


def _canonical_ascii(value):
    """The bytes of prototypes/static_tray_v01/canonical.json_bytes (non-ASCII data refuses)."""
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                          allow_nan=False).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ObservationError("RUNTIME", "Value has no canonical ASCII JSON form", cause=exc) from exc


def _loads(raw, category):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, category, "Duplicate JSON member: " + key)
            result[key] = value
        return result

    def constant(text):
        raise ValueError("Nonfinite JSON constant: " + text)
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except ObservationError:
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ObservationError(category, "Invalid bounded JSON", cause=exc) from exc


def _decode(raw, category):
    value = _loads(raw, category)
    _require(_canonical(value) == raw, category, "JSON is not in the frozen canonical serialization")
    return value


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _digest(value, category):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, category,
             "Expected a lowercase SHA-256 digest")
    _require(re.fullmatch(r"(.)\1{63}", value) is None, category, "Placeholder digest refused")
    return value


def _mode(info):
    return "0o%03o" % stat.S_IMODE(info.st_mode)


def _utc():
    return datetime.now(timezone.utc).isoformat()


class _Deadline:
    """A bounded outer allowance for static work; it never extends a child deadline."""

    def __init__(self, milliseconds, category="CLOCK"):
        self.deadline = time.monotonic() + milliseconds / 1000
        self.category = category

    def __call__(self):
        _require(time.monotonic() < self.deadline, self.category, "Bounded static allowance exhausted", state="TIMEOUT")


def _no_check():
    return None


# ---------------------------------------------------------------------------
# Canonical paths (contract section 7)
# ---------------------------------------------------------------------------

def _normalized(value, category="PATH"):
    _require(type(value) is str and value.startswith("/") and not value.startswith("//") and "\0" not in value
             and 0 < len(value) <= 1024 and (value == "/" or not value.endswith("/"))
             and posixpath.normpath(value) == value, category, "Expected a normalized absolute path: " + repr(value))
    return value


def canonical_path(value, *, allow_absent=False):
    """Return ``value``'s realpath after the contract section 7 check.

    ``value`` must be a normalized absolute path. Its only admitted
    symbolic-link components are the top-level system links ``/tmp``, ``/var``
    and ``/etc`` (into ``/private``), and only as ancestors: any other link,
    including ``value`` itself, refuses. Every existing ancestor must be a
    directory. With ``allow_absent`` the last component may be missing (an
    absent output path); a missing ancestor always refuses. The result is
    checked against the single system-link substitution, so ``canonical_path(p)
    == p`` exactly when ``p`` is already canonical.
    """
    text = _normalized(value)
    parts = [] if text == "/" else text.split("/")[1:]
    current, system = "", None
    for index, name in enumerate(parts):
        current += "/" + name
        last = index == len(parts) - 1
        try:
            info = os.lstat(current)
        except FileNotFoundError as exc:
            _require(last and allow_absent, "PATH", "Bound path or ancestor is missing: " + current)
            del exc
            break
        except OSError as exc:
            raise ObservationError("PATH", "Cannot inspect path component: " + current, cause=exc) from exc
        if stat.S_ISLNK(info.st_mode):
            _require(index == 0 and not last and current in SYSTEM_LINKS, "PATH",
                     "Symbolic-link component other than a /tmp, /var or /etc ancestor: " + current,
                     details={"rule": "PATH-SYMLINK", "component": current})
            system = current
        elif not last:
            _require(stat.S_ISDIR(info.st_mode), "PATH", "Path ancestor is not a directory: " + current)
    expected = SYSTEM_LINKS[system] + text[len(system):] if system else text
    resolved = os.path.realpath(text)
    _require(resolved == expected, "PATH", "Canonical form differs from its single system-link resolution: " + text,
             details={"rule": "PATH-RESOLUTION"})
    return resolved


def _canonical_value(value, category, *, allow_absent=False):
    _require(type(value) is str, category, "Expected a canonical absolute path")
    _require(canonical_path(value, allow_absent=allow_absent) == value, category,
             "Plan path is not in canonical form: " + value, details={"rule": "PATH-CANONICAL"})
    return value


def _inside(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def _relative(value, category):
    _require(type(value) is str and value and "\0" not in value and "\\" not in value and not value.startswith("/")
             and posixpath.normpath(value) == value and value != "." and ".." not in value.split("/"),
             category, "Unsafe relative name: " + repr(value))
    return value


# ---------------------------------------------------------------------------
# Bounded file reads
# ---------------------------------------------------------------------------

def _identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_file(path, maximum, *, category, private=False, keep=False, prefix=0, check=_no_check):
    """Hash one regular file through one descriptor.

    Refuses a symbolic link, a special file, a byte count above ``maximum``,
    and a change of identity during the read. Returns (bytes or None, binding,
    the first ``prefix`` bytes).
    """
    fd = None
    try:
        check()
        named = os.lstat(path)
        _require(not stat.S_ISLNK(named.st_mode), category, "Bound file is a symbolic link: " + path,
                 details={"rule": "FILE-SYMLINK"})
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
        before = os.fstat(fd)
        _require(stat.S_ISREG(before.st_mode), category, "Expected a regular file: " + path)
        _require(not private or before.st_nlink == 1, category, "Expected a private regular file with one link: " + path)
        _require(before.st_size <= maximum, category, "File exceeds its byte allowance: " + path)
        digest, chunks, head, length = hashlib.sha256(), [], b"", 0
        while True:
            check()
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            length += len(block)
            _require(length <= maximum, category, "File grew beyond its byte allowance: " + path)
            digest.update(block)
            if keep:
                chunks.append(block)
            if len(head) < prefix:
                head += block[:prefix - len(head)]
        after, again = os.fstat(fd), os.lstat(path)
        _require(_identity(before) == _identity(after) == _identity(again) and length == before.st_size, category,
                 "File changed while being read: " + path)
        binding = {"sha256": digest.hexdigest(), "size_bytes": length, "mode": _mode(before)}
        return (b"".join(chunks) if keep else None), binding, head
    except ObservationError:
        raise
    except OSError as exc:
        raise ObservationError(category, "Cannot read bound file: " + path, cause=exc) from exc
    finally:
        if fd is not None:
            os.close(fd)


def _binding_shape(value, category, *, descriptor=False):
    _keys(value, ("sha256", "size_bytes", "mode") + (("path",) if descriptor else ()), category)
    _digest(value["sha256"], category)
    _require(type(value["size_bytes"]) is int and value["size_bytes"] >= 0, category, "Invalid byte count")
    _require(type(value["mode"]) is str and re.fullmatch(r"0o[0-7]{3,4}", value["mode"]) is not None, category,
             "Invalid file mode")
    if descriptor:
        _canonical_value(value["path"], category)
    return value


def _binding(value):
    return {"sha256": value["sha256"], "size_bytes": value["size_bytes"], "mode": value["mode"]}


def _bound(path, expected, *, category, private=False, check=_no_check, rule="FILE-BINDING"):
    # A bounded allowance above the expected size, so that a replaced file reports its rule.
    maximum = max(expected["size_bytes"], LIMITS["tree_file_bytes"])
    _, actual, _ = read_file(path, maximum, category=category, private=private, check=check)
    _require(actual == _binding(expected), category, "Bound file identity differs: " + path,
             details={"rule": rule, "expected": _binding(expected), "actual": actual})
    return actual


def _document(descriptor, maximum, category, *, canonical=True, check=_no_check):
    _binding_shape(descriptor, category, descriptor=True)
    raw, actual, _ = read_file(descriptor["path"], maximum, category=category, keep=True, check=check)
    _require(actual == _binding(descriptor), category, "Document identity differs: " + descriptor["path"],
             details={"rule": "DOCUMENT-BINDING"})
    return (_decode(raw, category) if canonical else _loads(raw, category)), raw


def _descriptor(path, binding):
    return {"path": path, **_binding(binding)}


# ---------------------------------------------------------------------------
# Environment predicate (contract section 7, S10)
# ---------------------------------------------------------------------------

def environment_admitted(observed, declared, recorded_cf):
    """True exactly when ``observed`` equals ``declared``, or ``declared`` plus
    ``__CF_USER_TEXT_ENCODING`` with the value ``recorded_cf`` (a non-empty
    string). ``declared`` never contains that name. Malformed input is False.
    """
    try:
        observed, declared = dict(observed), dict(declared)
    except (TypeError, ValueError):
        return False
    if not all(type(key) is str and type(value) is str
               for mapping in (observed, declared) for key, value in mapping.items()):
        return False
    if CF_NAME in declared:
        return False
    if observed == declared:
        return True
    return type(recorded_cf) is str and recorded_cf != "" and observed == {**declared, CF_NAME: recorded_cf}


def _forbidden_class(name):
    if name.startswith("DYLD_"):
        return "dyld"
    if name in ("__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE"):
        return "python-launcher"
    if name.startswith("NODE_"):
        return "node"
    if name.startswith("PYTHON"):
        return "python-startup"
    if name.startswith("LD_"):
        return "loader"
    return "extra"


def check_environment(observed, declared):
    """M0's predicate for its own process. Returns the observed CF value or None.

    Diagnostics carry names only, never values.
    """
    observed = dict(observed)
    recorded = observed.get(CF_NAME)
    if environment_admitted(observed, declared, recorded):
        return recorded
    extra = sorted(set(observed) - set(declared) - {CF_NAME})
    details = {"rule": "ENVIRONMENT-EXACT", "extra": extra,
               "forbidden": sorted(name for name in extra if _forbidden_class(name) != "extra"),
               "classes": {name: _forbidden_class(name) for name in extra},
               "missing": sorted(set(declared) - set(observed)),
               "differing": sorted(name for name in set(declared) & set(observed) if observed[name] != declared[name]),
               "cf_user_text_encoding": "absent" if recorded is None else ("empty" if recorded == "" else "present")}
    raise ObservationError("ENVIRONMENT", "The process environment is not exactly the declared environment, "
                           "optionally plus __CF_USER_TEXT_ENCODING with a non-empty value", details=details)


# ---------------------------------------------------------------------------
# Platform, translation, boot and OS identity
# ---------------------------------------------------------------------------

def _libsystem():
    import ctypes
    return ctypes, ctypes.CDLL(LIBSYSTEM, use_errno=True)


def _sysctlbyname(name, size):
    ctypes, libc = _libsystem()
    function = libc.sysctlbyname
    function.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                         ctypes.c_size_t]
    function.restype = ctypes.c_int
    length = ctypes.c_size_t(0)
    _require(function(name.encode("ascii"), None, ctypes.byref(length), None, 0) == 0, "PLATFORM",
             "sysctlbyname cannot size " + name, details={"errno": ctypes.get_errno()})
    _require(0 < length.value <= size, "PLATFORM", "Unexpected sysctl value size for " + name)
    buffer = ctypes.create_string_buffer(length.value)
    _require(function(name.encode("ascii"), buffer, ctypes.byref(length), None, 0) == 0, "PLATFORM",
             "sysctlbyname cannot read " + name, details={"errno": ctypes.get_errno()})
    return buffer.raw[:length.value]


def read_proc_translated():
    """``sysctl.proc_translated`` through sysctlbyname: 0 native, 1 translated. Unreadable refuses."""
    raw = _sysctlbyname("sysctl.proc_translated", 8)
    _require(len(raw) == 4, "PLATFORM", "sysctl.proc_translated has an unexpected width")
    value = struct.unpack("=i", raw)[0]
    _require(value in (0, 1), "PLATFORM", "sysctl.proc_translated has an unexpected value")
    return value


def read_boot_session_uuid():
    """``kern.bootsessionuuid`` through sysctlbyname, as its UUID text."""
    raw = _sysctlbyname("kern.bootsessionuuid", 64)
    _require(raw.endswith(b"\0") and b"\0" not in raw[:-1], "PLATFORM", "kern.bootsessionuuid is not a C string")
    text = raw[:-1].decode("ascii", "replace")
    _require(UUID_TEXT.fullmatch(text) is not None, "PLATFORM", "kern.bootsessionuuid is not a UUID")
    return text


def read_process_image():
    """The current process image through libproc's proc_pidpath."""
    ctypes, libc = _libsystem()
    function = libc.proc_pidpath
    function.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    function.restype = ctypes.c_int
    buffer = ctypes.create_string_buffer(4096)
    length = function(os.getpid(), buffer, 4096)
    _require(0 < length < 4096, "PYTHON", "proc_pidpath cannot read the process image",
             details={"errno": ctypes.get_errno()})
    return os.fsdecode(buffer.raw[:length])


def _plist_identity(path, *, check=_no_check):
    import plistlib
    try:
        _require(canonical_path(path) == path, "OS", "OS identity path is not canonical: " + path)
    except ObservationError as exc:
        if exc.category == "OS":
            raise
        raise ObservationError("OS", "OS identity file is missing, linked or not canonical: " + path, cause=exc,
                               details={"rule": "OS-PATH"}) from exc
    raw, binding, _ = read_file(path, LIMITS["plist_bytes"], category="OS", keep=True, check=check)
    try:
        value = plistlib.loads(raw)
    except Exception as exc:
        raise ObservationError("OS", "OS identity file is not a property list: " + path, cause=exc) from exc
    _require(type(value) is dict, "OS", "OS identity property list is not a dictionary: " + path)
    fields = {}
    for key, name in (("ProductName", "product_name"), ("ProductVersion", "product_version"),
                      ("ProductBuildVersion", "product_build_version")):
        _require(type(value.get(key)) is str and value[key], "OS", "OS identity lacks " + key + ": " + path)
        fields[name] = value[key]
    extra = value.get("ProductVersionExtra")
    _require(extra is None or type(extra) is str, "OS", "ProductVersionExtra is not a string: " + path)
    return {"state": "present", "path": path, **binding, **fields, "product_version_extra": extra}


def read_os_identity(*, system_path=SYSTEM_VERSION_PATH, cryptex_path=CRYPTEX_SYSTEM_VERSION_PATH, check=_no_check):
    """``SystemVersion.plist`` and, if present, the OS cryptex's copy, each by bytes and fields.

    The system file must be canonical. The cryptex copy is named by its
    conventional path, which on macOS 26 passes through the link
    ``/System/Cryptexes/OS -> ../../System/Volumes/Preboot/Cryptexes/OS``.
    Contract section 7 admits no such link in a bound path, so the copy is bound
    by its canonical path (``path``), and the conventional name (``link_path``)
    and every link hop on the way (``hops``) are recorded beside it.
    """
    system = _plist_identity(system_path, check=check)
    chain = resolve_link_chain(cryptex_path, category="OS")
    if chain["state"] == "absent":
        cryptex = {"state": "absent", "path": cryptex_path, "hops": chain["hops"]}
    else:
        _require(chain["state"] == "file", "OS", "The cryptex copy is not a regular file: " + cryptex_path,
                 details={"rule": "OS-CRYPTEX"})
        cryptex = _plist_identity(chain["path"], check=check)
        cryptex.update(link_path=cryptex_path, hops=chain["hops"])
    return {"system_version": system, "cryptex": cryptex}


def _os_label(identity):
    system, cryptex = identity["system_version"], identity["cryptex"]
    return {"product_version": system["product_version"], "product_build_version": system["product_build_version"],
            "product_version_extra": system["product_version_extra"],
            "cryptex": ({"state": "absent"} if cryptex["state"] == "absent" else
                        {"state": "present", "product_version": cryptex["product_version"],
                         "product_build_version": cryptex["product_build_version"],
                         "product_version_extra": cryptex["product_version_extra"]})}


def _platform(host):
    info = host.uname()
    return {"system": info.sysname, "release": info.release, "version": info.version, "machine": info.machine,
            "proc_translated": host.proc_translated(), "boot_session_uuid": host.boot_session_uuid()}


def check_platform(observed, planned):
    """MC08: Darwin, arm64, not translated, and the planned release and boot."""
    _require(observed["system"] == "Darwin", "PLATFORM", "System other than Darwin", details={"rule": "PLATFORM-SYSTEM"})
    _require(observed["machine"] == "arm64", "PLATFORM", "Machine other than arm64", details={"rule": "PLATFORM-MACHINE"})
    _require(observed["proc_translated"] == 0, "PLATFORM", "Translated execution (sysctl.proc_translated is not 0)",
             details={"rule": "PLATFORM-TRANSLATED"})
    for key in ("release", "boot_session_uuid"):
        _require(observed[key] == planned[key], "PLATFORM", "Observed " + key + " differs from the plan",
                 details={"rule": "PLATFORM-" + key.upper()})


# ---------------------------------------------------------------------------
# Mach-O parser (contract sections 3, 4 and 7; reviewed by N34-M before MH)
# ---------------------------------------------------------------------------

def macho_magic_kind(head):
    """Classify the first four bytes: 'macho64', 'fat', 'macho32', 'macho64-be' or None."""
    magic = head[:4]
    if magic in (b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"):
        return "fat"
    if magic == b"\xcf\xfa\xed\xfe":
        return "macho64"
    if magic in (b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce"):
        return "macho32"
    if magic == b"\xfe\xed\xfa\xcf":
        return "macho64-be"
    return None


def _macho_extent(head, file_size):
    kind = macho_magic_kind(head)
    _macho(kind != "fat", "MACHO-FAT", "Universal (fat) Mach-O files are refused")
    _macho(kind == "macho64", "MACHO-MAGIC", "Not a thin 64-bit little-endian Mach-O file")
    _macho(len(head) >= 32 and file_size >= 32, "MACHO-MALFORMED", "Truncated Mach-O header")
    ncmds, sizeofcmds = struct.unpack_from("<II", head, 16)
    _macho(0 < ncmds <= LIMITS["macho_commands"] and 0 < sizeofcmds <= LIMITS["macho_command_bytes"]
           and 32 + sizeofcmds <= file_size, "MACHO-MALFORMED", "Load command table is empty or escapes the file")
    return 32 + sizeofcmds


def _version(value):
    return "%d.%d.%d" % (value >> 16, (value >> 8) & 0xFF, value & 0xFF)


def _lc_string(body, field, minimum):
    _macho(len(body) >= minimum, "MACHO-MALFORMED", "Load command is shorter than its structure")
    offset = struct.unpack_from("<I", body, field)[0]
    _macho(minimum <= offset < len(body), "MACHO-MALFORMED", "Load command string offset escapes the command")
    end = body.find(b"\0", offset)
    _macho(end > offset, "MACHO-MALFORMED", "Load command string is empty or unterminated")
    raw = body[offset:end]
    _macho(all(0x20 <= byte <= 0x7E for byte in raw), "MACHO-MALFORMED", "Load command string is not printable ASCII")
    return raw.decode("ascii")


def _within(offset, size, file_size):
    _macho(offset + size <= file_size, "MACHO-MALFORMED", "Load command data escapes the file")


def _command(cmd, body, file_size):
    name = LOAD_COMMANDS.get(cmd)
    row = {"cmd": "0x%08x" % cmd, "name": name, "cmdsize": len(body)}
    if name == "LC_SEGMENT_64":
        _macho(len(body) >= 72, "MACHO-MALFORMED", "Short LC_SEGMENT_64")
        segname = body[8:24].split(b"\0", 1)[0]
        _macho(all(0x20 <= byte <= 0x7E for byte in segname), "MACHO-MALFORMED", "Segment name is not ASCII")
        vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, _flags = struct.unpack_from("<QQQQiiII", body, 24)
        _macho(len(body) == 72 + 80 * nsects, "MACHO-MALFORMED", "LC_SEGMENT_64 size disagrees with its sections")
        _within(fileoff, filesize, file_size)
        row.update(segname=segname.decode("ascii"), vmaddr=vmaddr, vmsize=vmsize, fileoff=fileoff, filesize=filesize,
                   maxprot=maxprot, initprot=initprot, nsects=nsects)
    elif name == "LC_SYMTAB":
        _macho(len(body) == 24, "MACHO-MALFORMED", "LC_SYMTAB size differs")
        symoff, nsyms, stroff, strsize = struct.unpack_from("<IIII", body, 8)
        _within(symoff, nsyms * 16, file_size)
        _within(stroff, strsize, file_size)
        row.update(nsyms=nsyms, strsize=strsize)
    elif name == "LC_DYSYMTAB":
        _macho(len(body) == 80, "MACHO-MALFORMED", "LC_DYSYMTAB size differs")
    elif name in ("LC_LOAD_DYLINKER", "LC_ID_DYLINKER", "LC_DYLD_ENVIRONMENT"):
        row["path"] = _lc_string(body, 8, 12)
    elif name == "LC_RPATH":
        row["path"] = _lc_string(body, 8, 12)
    elif name in DYLIB_COMMANDS:
        row["path"] = _lc_string(body, 8, 24)
        _timestamp, current, compatibility = struct.unpack_from("<III", body, 12)
        row.update(current_version=_version(current), compatibility_version=_version(compatibility))
    elif name == "LC_UUID":
        _macho(len(body) == 24, "MACHO-MALFORMED", "LC_UUID size differs")
        text = body[8:24].hex().upper()
        row["uuid"] = "-".join((text[:8], text[8:12], text[12:16], text[16:20], text[20:]))
    elif name == "LC_BUILD_VERSION":
        _macho(len(body) >= 24, "MACHO-MALFORMED", "Short LC_BUILD_VERSION")
        platform, minos, sdk, ntools = struct.unpack_from("<IIII", body, 8)
        _macho(len(body) == 24 + 8 * ntools, "MACHO-MALFORMED", "LC_BUILD_VERSION size disagrees with its tools")
        row.update(platform=platform, minos=_version(minos), sdk=_version(sdk),
                   tools=[{"tool": tool, "version": _version(version)}
                          for tool, version in struct.iter_unpack("<II", body[24:])])
    elif name == "LC_SOURCE_VERSION":
        _macho(len(body) == 16, "MACHO-MALFORMED", "LC_SOURCE_VERSION size differs")
        value = struct.unpack_from("<Q", body, 8)[0]
        row["version"] = ".".join(str(part) for part in (value >> 40, (value >> 30) & 0x3FF, (value >> 20) & 0x3FF,
                                                          (value >> 10) & 0x3FF, value & 0x3FF))
    elif name == "LC_MAIN":
        _macho(len(body) == 24, "MACHO-MALFORMED", "LC_MAIN size differs")
        entryoff, stacksize = struct.unpack_from("<QQ", body, 8)
        _macho(entryoff < file_size, "MACHO-MALFORMED", "LC_MAIN entry offset escapes the file")
        row.update(entryoff=entryoff, stacksize=stacksize)
    elif name in LINKEDIT_COMMANDS:
        _macho(len(body) == 16, "MACHO-MALFORMED", name + " size differs")
        dataoff, datasize = struct.unpack_from("<II", body, 8)
        _within(dataoff, datasize, file_size)
        row.update(dataoff=dataoff, datasize=datasize)
    elif name in ("LC_DYLD_INFO", "LC_DYLD_INFO_ONLY"):
        _macho(len(body) == 48, "MACHO-MALFORMED", name + " size differs")
        values = struct.unpack_from("<10I", body, 8)
        for index in range(0, 10, 2):
            _within(values[index], values[index + 1], file_size)
    return row


def parse_macho(data, file_size):
    """Parse the header and every load command of a thin arm64 Mach-O image.

    ``data`` holds at least the first 32 + sizeofcmds bytes of a file of
    ``file_size`` bytes. Refuses fat, 32-bit and big-endian files, other CPU
    types and subtypes, and every structural inconsistency. Unknown commands
    are recorded with a null name; the Node and Python rules refuse them.
    """
    extent = _macho_extent(data, file_size)
    _macho(len(data) >= extent, "MACHO-MALFORMED", "Load command bytes were not supplied")
    _magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _reserved = struct.unpack_from("<8I", data, 0)
    _macho(cputype == CPU_TYPE_ARM64, "MACHO-CPU", "CPU type other than arm64")
    _macho(cpusubtype == CPU_SUBTYPE_ARM64_ALL, "MACHO-CPU", "CPU subtype other than CPU_SUBTYPE_ARM64_ALL")
    commands, offset, end = [], 32, extent
    for _ in range(ncmds):
        _macho(offset + 8 <= end, "MACHO-MALFORMED", "Load command header escapes the table")
        cmd, cmdsize = struct.unpack_from("<II", data, offset)
        _macho(cmdsize >= 8 and cmdsize % 8 == 0 and offset + cmdsize <= end, "MACHO-MALFORMED",
               "Load command size is invalid or escapes the table")
        commands.append(_command(cmd, data[offset:offset + cmdsize], file_size))
        offset += cmdsize
    _macho(offset == end, "MACHO-MALFORMED", "Load command sizes do not add up to sizeofcmds")
    return {"magic": "MH_MAGIC_64", "cputype": "0x%08x" % cputype, "cpusubtype": "0x%08x" % cpusubtype,
            "filetype": FILE_TYPES.get(filetype, "0x%08x" % filetype), "flags": "0x%08x" % flags,
            "ncmds": ncmds, "sizeofcmds": sizeofcmds, "commands": commands}


def read_macho(path, *, maximum, private=False, category="MACHO", check=_no_check, expected=None):
    """Read, hash and parse one Mach-O file; returns (binding, summary)."""
    _, binding, head = read_file(path, maximum, category=category, private=private, prefix=65536, check=check)
    if expected is not None:
        _require(binding == _binding(expected), category, "Mach-O file changed after its binding: " + path,
                 details={"rule": "FILE-BINDING"})
    try:
        extent = _macho_extent(head, binding["size_bytes"])
        if extent > len(head):
            _, again, head = read_file(path, maximum, category=category, private=private, prefix=extent, check=check)
            _require(again == binding, category, "Mach-O file changed while being parsed: " + path)
        return binding, parse_macho(head, binding["size_bytes"])
    except ObservationError as exc:
        if exc.category == "MACHO":
            exc.details.setdefault("path", path)
        raise


def _counted(summary):
    counts = {}
    for row in summary["commands"]:
        if row["name"] is not None:
            counts[row["name"]] = counts.get(row["name"], 0) + 1
    duplicated = sorted(name for name, count in counts.items() if count > 1 and name in SINGLE_COMMANDS)
    _macho(not duplicated, "MACHO-DUPLICATE", "Load command occurs more than once: " + ", ".join(duplicated))
    return counts


def _absolute_dylib(path):
    return path.startswith("/") and posixpath.normpath(path) == path and not path.startswith("//")


def check_node_macho(summary):
    """Contract section 7: the closed allow-list for the Node executable."""
    _macho(summary["filetype"] == "MH_EXECUTE", "MACHO-FILETYPE", "Node must be an MH_EXECUTE file")
    for row in summary["commands"]:
        name = row["name"]
        _macho(name not in NODE_REFUSED_COMMANDS, "MACHO-REFUSED-COMMAND", "Refused load command: " + str(name))
        _macho(name in NODE_ALLOWED_COMMANDS, "MACHO-COMMAND",
               "Load command outside the closed allow-list: " + (name or row["cmd"]))
        if name == "LC_LOAD_DYLINKER":
            _macho(row["path"] == "/usr/lib/dyld", "MACHO-DYLINKER", "LC_LOAD_DYLINKER is not /usr/lib/dyld")
        if name in REFERENCE_COMMANDS:
            _macho(not row["path"].startswith("@"), "MACHO-AT-PATH", "@-relative dylib reference: " + row["path"])
            _macho(_absolute_dylib(row["path"]) and row["path"].startswith(SYSTEM_LIBRARY_PREFIXES),
                   "MACHO-DYLIB-PATH", "Dylib outside /usr/lib/ and /System/Library/: " + row["path"])
    counts = _counted(summary)
    _macho(counts.get("LC_LOAD_DYLINKER") == 1 and counts.get("LC_MAIN") == 1, "MACHO-STRUCTURE",
           "Node needs exactly one LC_LOAD_DYLINKER and one LC_MAIN")
    return {"references": [row["path"] for row in summary["commands"] if row["name"] in REFERENCE_COMMANDS]}


def _at_kind(path):
    for prefix in AT_PREFIXES:
        if path.startswith(prefix) and len(path) > len(prefix):
            return prefix[:-1]
    return None


def check_python_macho(summary):
    """Contract section 4: the Python-side rules; returns ids, rpaths and references for resolution."""
    _macho(summary["filetype"] in PYTHON_FILE_TYPES, "MACHO-FILETYPE",
           "Python Mach-O file type other than MH_EXECUTE, MH_DYLIB or MH_BUNDLE: " + summary["filetype"])
    identity, rpaths, references = None, [], []
    for row in summary["commands"]:
        name = row["name"]
        _macho(name not in PYTHON_REFUSED_COMMANDS, "MACHO-REFUSED-COMMAND", "Refused load command: " + str(name))
        _macho(name in PYTHON_ALLOWED_COMMANDS, "MACHO-COMMAND",
               "Load command outside the Python allow-list: " + (name or row["cmd"]))
        if name == "LC_LOAD_DYLINKER":
            _macho(row["path"] == "/usr/lib/dyld", "MACHO-DYLINKER", "LC_LOAD_DYLINKER is not /usr/lib/dyld")
        elif name == "LC_ID_DYLIB":
            identity = row["path"]
        elif name == "LC_RPATH":
            path = row["path"]
            if path.startswith("@"):
                _macho(path.startswith(("@loader_path/", "@executable_path/")) or path in ("@loader_path",
                       "@executable_path"), "MACHO-RPATH", "Unsupported @-relative LC_RPATH: " + path)
            else:
                _macho(_absolute_dylib(path), "MACHO-RPATH", "LC_RPATH is neither absolute nor @-relative: " + path)
            rpaths.append(path)
        elif name in REFERENCE_COMMANDS:
            path = row["path"]
            if path.startswith("@"):
                _macho(_at_kind(path) is not None, "MACHO-AT-PATH", "Unsupported @-relative reference: " + path)
            else:
                _macho(_absolute_dylib(path), "MACHO-DYLIB-PATH", "Dylib reference is not a normalized absolute path: "
                       + path)
            references.append({"command": name, "path": path})
    counts = _counted(summary)
    if summary["filetype"] == "MH_EXECUTE":
        _macho(counts.get("LC_LOAD_DYLINKER") == 1 and counts.get("LC_MAIN") == 1, "MACHO-STRUCTURE",
               "An executable needs exactly one LC_LOAD_DYLINKER and one LC_MAIN")
    else:
        _macho("LC_MAIN" not in counts and "LC_LOAD_DYLINKER" not in counts, "MACHO-STRUCTURE",
               "Only an executable may carry LC_MAIN or LC_LOAD_DYLINKER")
    if summary["filetype"] == "MH_DYLIB":
        _macho(counts.get("LC_ID_DYLIB") == 1, "MACHO-STRUCTURE", "A dylib needs exactly one LC_ID_DYLIB")
    return {"filetype": summary["filetype"], "id": identity, "rpaths": rpaths, "references": references,
            "commands": [row["name"] for row in summary["commands"]]}


def macho_summary(summary):
    """A compact, reviewable projection for HOST: header and every command with its decoded fields."""
    return {key: summary[key] for key in ("magic", "cputype", "cpusubtype", "filetype", "flags", "ncmds",
                                          "sizeofcmds", "commands")}


# ---------------------------------------------------------------------------
# Trees and symbolic-link resolution
# ---------------------------------------------------------------------------

def _name(name, category, path):
    _require(name not in (".", "..") and "/" not in name and "\0" not in name and name.isprintable(), category,
             "Unsupported entry name in " + path)


def tree_entries(root, *, category, check=_no_check, refuse_ds_store=False, private=False, symlinks=True,
                 on_file=None, prefix=0, maximum_entries=LIMITS["tree_entries"],
                 file_maximum=LIMITS["tree_file_bytes"]):
    """Exact entry map of one tree, never following a link.

    Each entry is {kind: file, sha256, size_bytes, mode}, {kind: symlink,
    target} or {kind: directory, mode}. Special files refuse; a directory that
    changes while it is listed refuses.
    """
    try:
        root_info = os.lstat(root)
    except OSError as exc:
        raise ObservationError(category, "Tree root is missing or unreadable: " + root, cause=exc) from exc
    _require(stat.S_ISDIR(root_info.st_mode), category, "Tree root is not a directory: " + root)
    entries, pending = {}, [""]
    try:
        while pending:
            check()
            relative = pending.pop()
            directory = root + "/" + relative if relative else root
            before = os.lstat(directory)
            with os.scandir(directory) as iterator:
                names = sorted(entry.name for entry in iterator)
            for name in names:
                check()
                _name(name, category, directory)
                rel = relative + "/" + name if relative else name
                path = root + "/" + rel
                _require(len(entries) < maximum_entries, category, "Tree exceeds its entry allowance: " + root)
                _require(not (refuse_ds_store and name == ".DS_Store"), category,
                         "A .DS_Store file refuses this tree: " + path, details={"rule": "TREE-DS-STORE"})
                info = os.lstat(path)
                if stat.S_ISLNK(info.st_mode):
                    _require(symlinks, category, "Symbolic link in a tree that admits none: " + path,
                             details={"rule": "TREE-SYMLINK"})
                    entries[rel] = {"kind": "symlink", "target": os.readlink(path)}
                elif stat.S_ISDIR(info.st_mode):
                    entries[rel] = {"kind": "directory", "mode": _mode(info)}
                    pending.append(rel)
                elif stat.S_ISREG(info.st_mode):
                    _, binding, head = read_file(path, file_maximum, category=category, private=private,
                                                 prefix=prefix, check=check)
                    entries[rel] = {"kind": "file", **binding}
                    if on_file is not None:
                        on_file(rel, path, binding, head)
                else:
                    raise ObservationError(category, "Special file in a bound tree: " + path,
                                           details={"rule": "TREE-SPECIAL"})
            after = os.lstat(directory)
            _require((before.st_dev, before.st_ino, before.st_mtime_ns, before.st_ctime_ns)
                     == (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_ctime_ns), category,
                     "Directory changed while it was listed: " + directory)
    except ObservationError:
        raise
    except OSError as exc:
        raise ObservationError(category, "Cannot list bound tree: " + root, cause=exc) from exc
    return entries


def resolve_link_chain(path, *, category="PATH"):
    """Resolve an absolute path component by component, as the kernel does.

    Returns {state, path, hops}: state is file, directory, other or absent; path
    is the canonical result (or the first missing path); hops lists every
    symbolic link followed, as {path, target}, in order.
    """
    _require(type(path) is str and path.startswith("/") and "\0" not in path, category,
             "Expected an absolute path to resolve: " + repr(path))
    pending = [name for name in path.split("/") if name]
    resolved, hops = "/", []
    while pending:
        name = pending.pop(0)
        if name == ".":
            continue
        if name == "..":
            resolved = posixpath.dirname(resolved)
            continue
        candidate = posixpath.join(resolved, name)
        try:
            info = os.lstat(candidate)
        except FileNotFoundError:
            return {"state": "absent", "path": candidate, "hops": hops}
        except OSError as exc:
            raise ObservationError(category, "Cannot inspect link chain component: " + candidate, cause=exc) from exc
        if stat.S_ISLNK(info.st_mode):
            _require(len(hops) < LIMITS["link_hops"], category, "Excessive or circular link chain: " + path)
            target = os.readlink(candidate)
            hops.append({"path": candidate, "target": target})
            if target.startswith("/"):
                resolved = "/"
            pending = [part for part in target.split("/") if part] + pending
            continue
        if pending and not stat.S_ISDIR(info.st_mode):
            return {"state": "absent", "path": candidate + "/" + "/".join(pending), "hops": hops}
        resolved = candidate
    try:
        info = os.lstat(resolved)
    except OSError as exc:
        raise ObservationError(category, "Resolved path vanished: " + resolved, cause=exc) from exc
    state = "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "other"
    return {"state": state, "path": resolved, "hops": hops}


# ---------------------------------------------------------------------------
# Python installation-tree inventory (contract section 4)
# ---------------------------------------------------------------------------

def _framework_version(framework):
    version = posixpath.basename(framework)
    _require(re.fullmatch(r"3\.\d+", version) is not None and posixpath.basename(posixpath.dirname(framework))
             == "Versions" and posixpath.basename(posixpath.dirname(posixpath.dirname(framework))) == "Python.framework",
             "PYTHON", "Not a Python.framework version directory: " + framework)
    return version


def _parse_pyvenv(raw):
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ObservationError("PYTHON", "pyvenv.cfg is not UTF-8", cause=exc) from exc
    values = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        _require("=" in line, "PYTHON", "Unsupported pyvenv.cfg line")
        key, value = (part.strip() for part in line.split("=", 1))
        _require(key and key not in values, "PYTHON", "Empty or duplicate pyvenv.cfg key")
        values[key] = value
    return values


def interpreter_selection(venv, framework, framework_entries, venv_entries):
    """The selection chain from .venv/bin/python, including pyvenv.cfg's home."""
    short = _framework_version(framework)
    launcher_name = "python" + short
    expected = framework + "/bin/" + launcher_name
    _require(framework_entries.get("bin/" + launcher_name, {}).get("kind") == "file", "PYTHON",
             "The framework launcher is missing: " + expected)
    _require(framework_entries.get(PROCESS_IMAGE, {}).get("kind") == "file", "PYTHON",
             "The framework process image is missing: " + framework + "/" + PROCESS_IMAGE)
    _require(venv_entries.get("bin/python", {}).get("kind") == "symlink" and
             venv_entries.get("pyvenv.cfg", {}).get("kind") == "file", "PYTHON",
             "The venv lacks bin/python as a link or pyvenv.cfg")
    launcher = venv + "/bin/python"
    chain = resolve_link_chain(launcher, category="PYTHON")
    _require(chain["state"] == "file" and chain["path"] == expected, "PYTHON",
             "The venv's python does not select the framework launcher", details={"rule": "PYTHON-SELECTION"})
    raw, binding, _ = read_file(venv + "/pyvenv.cfg", 65536, category="PYTHON", keep=True)
    _require(binding == _binding(venv_entries["pyvenv.cfg"]), "PYTHON", "pyvenv.cfg changed while inventoried")
    cfg = _parse_pyvenv(raw)
    _require({"home", "include-system-site-packages", "version"} <= set(cfg), "PYTHON",
             "pyvenv.cfg lacks home, include-system-site-packages or version")
    _require(cfg["include-system-site-packages"] == "false", "PYTHON", "The venv includes system site-packages")
    _require(re.fullmatch(re.escape(short) + r"\.\d+", cfg["version"]) is not None, "PYTHON",
             "pyvenv.cfg version disagrees with the framework")
    home = resolve_link_chain(cfg["home"], category="PYTHON")
    _require(home["state"] == "directory", "PYTHON", "pyvenv.cfg home is not a directory")
    home_launcher = resolve_link_chain(cfg["home"].rstrip("/") + "/" + launcher_name, category="PYTHON")
    _require(home_launcher["state"] == "file" and home_launcher["path"] == expected, "PYTHON",
             "pyvenv.cfg home does not select the framework launcher", details={"rule": "PYTHON-HOME"})
    executable = None
    if "executable" in cfg:
        executable = resolve_link_chain(cfg["executable"], category="PYTHON")
        _require(executable["state"] == "file" and executable["path"] == expected, "PYTHON",
                 "pyvenv.cfg executable does not select the framework launcher")
    return {"launcher": launcher, "launcher_chain": chain, "pyvenv_cfg": cfg, "home_chain": home,
            "home_launcher_chain": home_launcher, "executable_chain": executable,
            "process_image": framework + "/" + PROCESS_IMAGE, "version_directory": short}


def _tree_of(path, framework, venv):
    if _inside(path, framework):
        return "framework", path[len(framework) + 1:]
    if _inside(path, venv):
        return "venv", path[len(venv) + 1:]
    return None, None


def python_inventory(venv, framework, *, check=_no_check):
    """The exact installation-tree inventory of contract section 4.

    Both trees by path (files by SHA-256, size and mode, links by target,
    directories by mode), the interpreter selection chain, and the transitive
    closure of every Mach-O file's non-system references, with every link hop.
    Its digest is the SHA-256 of its canonical JSON bytes.
    """
    venv, framework = canonical_path(venv), canonical_path(framework)
    _require(not _inside(venv, framework) and not _inside(framework, venv), "PYTHON", "The venv and framework overlap")
    images = {}

    def collect(tree):
        def on_file(_rel, path, binding, head):
            kind = macho_magic_kind(head)
            if kind is None:
                return
            _macho(kind != "fat", "MACHO-FAT", "Universal (fat) Mach-O file in a Python tree: " + path)
            _macho(kind == "macho64", "MACHO-MAGIC", "Non-arm64 Mach-O file in a Python tree: " + path)
            images[path] = (tree, binding)
        return on_file
    framework_entries = tree_entries(framework, category="PYTHON", check=check, on_file=collect("framework"), prefix=4)
    venv_entries = tree_entries(venv, category="PYTHON", check=check, on_file=collect("venv"), prefix=4)
    selection = interpreter_selection(venv, framework, framework_entries, venv_entries)
    closure = _python_closure(images, framework, venv, framework_entries, venv_entries, selection["process_image"],
                              check)
    return {"schema": PYTHON_INVENTORY_SCHEMA, "framework": {"root": framework, "entries": framework_entries},
            "venv": {"root": venv, "entries": venv_entries}, "selection": selection, "closure": closure}


def _search_directory(raw, loader_dirs, executable_dir):
    """Resolve one LC_RPATH entry as a directory, from every loader spelling."""
    if raw.startswith("@loader_path"):
        bases = sorted(loader_dirs)
        suffix = raw[len("@loader_path"):]
    elif raw.startswith("@executable_path"):
        bases, suffix = [executable_dir], raw[len("@executable_path"):]
    else:
        bases, suffix = [""], raw
    outcomes = [resolve_link_chain((base + suffix) if base else suffix, category="PYTHON") for base in bases]
    _macho(len({(row["state"], row["path"]) for row in outcomes}) == 1, "MACHO-AT-AMBIGUOUS",
           "@loader_path resolves differently through the image's spellings: " + raw)
    return {"raw": raw, **outcomes[0]}


def _python_closure(images, framework, venv, framework_entries, venv_entries, process_image, check):
    """Repeat the closure until every image's set of spellings is stable.

    ``@loader_path`` is resolved from the canonical directory of the image and
    from the directory of every spelling by which another image references it;
    all must agree. A later pass sees the spellings that an earlier pass found.
    """
    seed = {path: {path} for path in images}
    for _ in range(8):
        closure, used, final = _closure_pass(images, framework, venv, framework_entries, venv_entries,
                                             process_image, check, seed)
        if all(used.get(path) == names for path, names in final.items()):
            return closure
        seed = {path: set(names) for path, names in final.items()}
    raise ObservationError("MACHO", "Image spellings did not stabilize", details={"rule": "MACHO-AT-AMBIGUOUS"})


def _closure_pass(images, framework, venv, framework_entries, venv_entries, process_image, check, seed):
    known = dict(images)
    spellings = {path: set(names) for path, names in seed.items()}
    used = {}
    queue, closure_images, external, links = sorted(images), {}, {}, {}
    entries = {"framework": framework_entries, "venv": venv_entries}
    while queue:
        check()
        path = queue.pop(0)
        if path in closure_images:
            continue
        tree, binding = known[path]
        _, summary = read_macho(path, maximum=LIMITS["tree_file_bytes"], category="PYTHON", check=check,
                                expected=binding)
        rules = check_python_macho(summary)
        spellings.setdefault(path, set())
        used[path] = set(spellings[path])
        loader_dirs = {posixpath.dirname(path)} | {posixpath.dirname(name) for name in spellings[path]}
        executable_dir = posixpath.dirname(path if rules["filetype"] == "MH_EXECUTE" else process_image)
        rpaths = [_search_directory(raw, loader_dirs, executable_dir) for raw in rules["rpaths"]]
        for row in rpaths:
            for hop in row["hops"]:
                links[(hop["path"], hop["target"])] = hop
        references = []
        for reference in rules["references"]:
            raw = reference["path"]
            if not raw.startswith("@") and raw.startswith(SYSTEM_LIBRARY_PREFIXES):
                references.append({"command": reference["command"], "raw": raw, "kind": "system"})
                continue
            candidates = []
            kind = _at_kind(raw)
            if kind == "@rpath":
                selected = None
                for row in rpaths:
                    candidate = row["path"] + raw[len("@rpath"):]
                    outcome = (resolve_link_chain(candidate, category="PYTHON") if row["state"] == "directory"
                               else {"state": "absent", "path": candidate, "hops": []})
                    candidates.append({"rpath": row["raw"], "candidate": candidate, "state": outcome["state"]})
                    if outcome["state"] != "absent":
                        selected = (candidate, outcome)
                        break
                _macho(selected is not None, "MACHO-AT-UNRESOLVED", "@rpath reference does not resolve to a bound "
                       "file: " + raw + " in " + path)
                spelling, outcome = selected
            elif kind == "@loader_path":
                outcomes = {}
                for base in sorted(loader_dirs):
                    spelling = base + raw[len("@loader_path"):]
                    outcomes[spelling] = resolve_link_chain(spelling, category="PYTHON")
                _macho(len({(row["state"], row["path"]) for row in outcomes.values()}) == 1, "MACHO-AT-AMBIGUOUS",
                       "@loader_path reference resolves differently through the image's spellings: " + raw)
                spelling, outcome = sorted(outcomes.items())[0]
            elif kind == "@executable_path":
                spelling = executable_dir + raw[len("@executable_path"):]
                outcome = resolve_link_chain(spelling, category="PYTHON")
            else:
                spelling, outcome = raw, resolve_link_chain(raw, category="PYTHON")
            _macho(outcome["state"] == "file", "MACHO-AT-UNRESOLVED" if kind else "MACHO-DEPENDENCY-MISSING",
                   "Reference does not resolve to a bound regular file: " + raw + " in " + path)
            target = outcome["path"]
            _macho(not target.startswith(SYSTEM_LIBRARY_PREFIXES), "MACHO-AT-PATH",
                   "A non-system reference resolves into the system tree: " + raw)
            for hop in outcome["hops"]:
                links[(hop["path"], hop["target"])] = hop
            owner, rel = _tree_of(target, framework, venv)
            if owner is not None:
                _macho(entries[owner].get(rel, {}).get("kind") == "file", "MACHO-AT-UNRESOLVED",
                       "Reference resolves to an unbound tree path: " + target)
                _macho(target in known, "MACHO-DEPENDENCY-NOT-MACHO", "Reference resolves to a non-Mach-O file: "
                       + target)
            elif target not in known:
                _, bound, head = read_file(target, LIMITS["tree_file_bytes"], category="PYTHON", prefix=4,
                                           check=check)
                _macho(macho_magic_kind(head) == "macho64", "MACHO-DEPENDENCY-NOT-MACHO",
                       "Dependency is not a thin arm64 Mach-O file: " + target)
                known[target] = ("external", bound)
                external[target] = bound
                queue.append(target)
            spellings.setdefault(target, set()).add(spelling)
            row = {"command": reference["command"], "raw": raw, "kind": "bound", "path": target,
                   "hops": outcome["hops"]}
            if candidates:
                row["candidates"] = candidates
            references.append(row)
        closure_images[path] = {"tree": tree, "filetype": rules["filetype"], "id": rules["id"],
                                "commands": rules["commands"], "rpaths": rpaths, "references": references}
    for path, names in spellings.items():
        if path in closure_images and names - {path}:
            closure_images[path]["spellings"] = sorted(names)
    closure = {"images": closure_images, "external": external, "links": [links[key] for key in sorted(links)]}
    return closure, used, spellings


def python_inventory_digest(inventory):
    return _sha256(_canonical(inventory))


def compare_inventory(expected, actual):
    """Exact-set comparison of two Python inventories; returns the sorted differences (empty when equal)."""
    rows = []
    for tree in ("framework", "venv"):
        old = (expected.get(tree) or {}) if type(expected) is dict else {}
        new = (actual.get(tree) or {}) if type(actual) is dict else {}
        if old.get("root") != new.get("root"):
            rows.append({"part": tree, "path": ".", "change": "root"})
        old_entries, new_entries = old.get("entries") or {}, new.get("entries") or {}
        for name in sorted(set(old_entries) | set(new_entries)):
            if name not in new_entries:
                rows.append({"part": tree, "path": name, "change": "missing"})
            elif name not in old_entries:
                rows.append({"part": tree, "path": name, "change": "added"})
            elif old_entries[name] != new_entries[name]:
                rows.append({"part": tree, "path": name, "change": "changed"})
    old_closure, new_closure = expected.get("closure") or {}, actual.get("closure") or {}
    for part in ("external", "images"):
        old, new = old_closure.get(part) or {}, new_closure.get(part) or {}
        for name in sorted(set(old) | set(new)):
            if name not in new:
                rows.append({"part": part, "path": name, "change": "missing"})
            elif name not in old:
                rows.append({"part": part, "path": name, "change": "added"})
            elif old[name] != new[name]:
                rows.append({"part": part, "path": name, "change": "changed"})
    old_links = {(row["path"], row["target"]) for row in old_closure.get("links") or []}
    new_links = {(row["path"], row["target"]) for row in new_closure.get("links") or []}
    for path, target in sorted(old_links - new_links):
        rows.append({"part": "links", "path": path, "change": "missing", "target": target})
    for path, target in sorted(new_links - old_links):
        rows.append({"part": "links", "path": path, "change": "added", "target": target})
    if expected.get("selection") != actual.get("selection"):
        old, new = expected.get("selection") or {}, actual.get("selection") or {}
        for key in sorted(set(old) | set(new)):
            if old.get(key) != new.get(key):
                rows.append({"part": "selection", "path": key, "change": "changed"})
    if expected.get("schema") != actual.get("schema"):
        rows.append({"part": "schema", "path": ".", "change": "changed"})
    return rows


def read_lock_pins(raw):
    """Parse the macOS lock: exactly the seven contract pins."""
    pins = {}
    try:
        text = raw.decode("ascii")
    except UnicodeError as exc:
        raise ObservationError("PYTHON", "The lock is not ASCII", cause=exc) from exc
    for original in text.splitlines():
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if re.fullmatch(r"--hash=sha256:[0-9a-f]{64}(?:\s*\\)?", line):
            _require(bool(pins), "PYTHON", "Hash continuation without a requirement")
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s\\]+)(?:\s+--hash=sha256:[0-9a-f]{64})*(?:\s*\\)?", line)
        _require(match is not None and match[1] not in pins, "PYTHON", "Unsupported or duplicate lock line")
        pins[match[1]] = match[2]
    _require(pins == dict(PYTHON_PINS), "PYTHON", "The lock's pins differ from the seven contract pins")
    return pins


def _normalized_name(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _metadata_header(raw):
    try:
        header = raw.decode("utf-8").split("\n\n", 1)[0]
    except UnicodeError as exc:
        raise ObservationError("PYTHON", "Package METADATA is not UTF-8", cause=exc) from exc
    names = re.findall(r"^Name: ([^\r\n]+)$", header, flags=re.MULTILINE)
    versions = re.findall(r"^Version: ([^\r\n]+)$", header, flags=re.MULTILINE)
    _require(len(names) == 1 and len(versions) == 1, "PYTHON", "Package METADATA lacks one Name and one Version")
    return names[0].strip(), versions[0].strip()


def verify_packages(venv, venv_entries, pins, version_directory):
    """Read package metadata by explicit path and verify every RECORD against the inventoried bytes.

    Every file under site-packages must be owned by exactly one of the seven
    RECORD files. Unhashed rows are admitted only for RECORD itself and for
    bytecode under __pycache__, whose bytes the exact-set inventory binds.
    """
    site = "lib/python" + version_directory + "/site-packages"
    _require(venv_entries.get(site, {}).get("kind") == "directory", "PYTHON", "The venv lacks " + site)
    metadata_dirs = sorted(rel for rel, entry in venv_entries.items() if entry["kind"] == "directory"
                           and posixpath.dirname(rel) == site and rel.endswith((".dist-info", ".egg-info")))
    _require(all(rel.endswith(".dist-info") for rel in metadata_dirs), "PYTHON", "Unsupported .egg-info metadata")
    wanted = {_normalized_name(name): (name, version) for name, version in pins.items()}
    packages, records, owned = {}, {}, {}
    for directory in metadata_dirs:
        for required in ("METADATA", "RECORD"):
            _require(venv_entries.get(directory + "/" + required, {}).get("kind") == "file", "PYTHON",
                     "Package metadata lacks " + required + ": " + directory)
        raw, binding, _ = read_file(venv + "/" + directory + "/METADATA", 4 * 1024 * 1024, category="PYTHON", keep=True)
        _require(binding == _binding(venv_entries[directory + "/METADATA"]), "PYTHON", "METADATA changed")
        name, version = _metadata_header(raw)
        key = _normalized_name(name)
        _require(key in wanted and key not in packages, "PYTHON", "Unexpected or duplicate package: " + name,
                 details={"rule": "PYTHON-PACKAGE"})
        _require(version == wanted[key][1], "PYTHON", "Package version differs from its pin: " + name,
                 details={"rule": "PYTHON-PACKAGE"})
        raw, binding, _ = read_file(venv + "/" + directory + "/RECORD", 16 * 1024 * 1024, category="PYTHON", keep=True)
        _require(binding == _binding(venv_entries[directory + "/RECORD"]), "PYTHON", "RECORD changed")
        try:
            rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
        except (UnicodeError, csv.Error) as exc:
            raise ObservationError("PYTHON", "Unreadable RECORD: " + directory, cause=exc) from exc
        hashed = unhashed = 0
        for row in rows:
            if not row:
                continue
            _require(len(row) == 3, "PYTHON", "RECORD row does not have three fields: " + directory)
            name_field, hash_field, size_field = row
            _require(name_field and not name_field.startswith("/") and "\\" not in name_field, "PYTHON",
                     "Unsafe RECORD path: " + directory)
            rel = posixpath.normpath(site + "/" + name_field)
            _require(rel != ".." and not rel.startswith("../") and not rel.startswith("/"), "PYTHON",
                     "RECORD path leaves the venv: " + name_field)
            entry = venv_entries.get(rel)
            _require(entry is not None and entry["kind"] == "file", "PYTHON", "RECORD names a missing file: " + rel,
                     details={"rule": "PYTHON-RECORD"})
            _require(rel not in owned, "PYTHON", "File is owned by more than one RECORD row: " + rel)
            if hash_field:
                algorithm, _, value = hash_field.partition("=")
                expected = base64.urlsafe_b64encode(bytes.fromhex(entry["sha256"])).rstrip(b"=").decode("ascii")
                _require(algorithm == "sha256" and value == expected and size_field == str(entry["size_bytes"]),
                         "PYTHON", "RECORD row disagrees with the file's bytes: " + rel,
                         details={"rule": "PYTHON-RECORD"})
                hashed += 1
            else:
                _require(size_field == "" and (rel == directory + "/RECORD" or
                         (rel.endswith(".pyc") and "/__pycache__/" in "/" + rel)), "PYTHON",
                         "Unhashed RECORD row for a file that must be hashed: " + rel, details={"rule": "PYTHON-RECORD"})
                unhashed += 1
            owned[rel] = key
        _require(owned.get(directory + "/RECORD") == key, "PYTHON", "RECORD does not list itself: " + directory)
        packages[wanted[key][0]] = version
        records[wanted[key][0]] = {"dist_info": directory, "record": _binding(venv_entries[directory + "/RECORD"]),
                                   "hashed_rows": hashed, "unhashed_rows": unhashed}
    unowned = sorted(rel for rel, entry in venv_entries.items() if entry["kind"] == "file"
                     and _inside(rel, site) and rel not in owned)
    _require(not unowned, "PYTHON", "Files under site-packages that no RECORD owns", details={
        "rule": "PYTHON-UNOWNED", "files": unowned[:50]})
    _require(packages == dict(pins), "PYTHON", "The seven pinned packages are not exactly installed",
             details={"rule": "PYTHON-PACKAGE", "observed": packages})
    return packages, records


def launcher_state():
    """The observing interpreter's identity: version, build string, sys.flags and paths."""
    return {"implementation": sys.implementation.name, "platform": sys.platform,
            "version": "%d.%d.%d" % sys.version_info[:3], "build_string": sys.version,
            "flags": {name: getattr(sys.flags, name) for name in FLAG_NAMES},
            "site_imported": "site" in sys.modules, "executable": sys.executable,
            "base_executable": getattr(sys, "_base_executable", None), "prefix": sys.prefix,
            "base_prefix": sys.base_prefix, "path": list(sys.path), "process_image": read_process_image()}


def loaded_module_files():
    rows = []
    for name, module in sorted(tuple(sys.modules.items())):
        path = getattr(module, "__file__", None)
        if type(path) is str:
            cached = getattr(module, "__cached__", None)
            rows.append({"name": name, "file": path, "cached": cached if type(cached) is str else None})
    return rows


def check_launcher(state, venv, framework, version):
    flags = state["flags"]
    _require(flags["isolated"] == 1 and flags["no_site"] == 1 and flags["dont_write_bytecode"] == 1
             and flags["ignore_environment"] == 1 and flags["no_user_site"] == 1 and flags["safe_path"] is True
             and not state["site_imported"], "PYTHON", "The observer must run under -I -S -B without site",
             details={"rule": "PYTHON-LAUNCHER"})
    launcher = framework + "/bin/python" + _framework_version(framework)
    _require(state["implementation"] == "cpython" and state["platform"] == "darwin" and state["version"] == version,
             "PYTHON", "The observing interpreter is not the planned CPython", details={"rule": "PYTHON-VERSION"})
    _require(state["executable"] == venv + "/bin/python" and type(state["base_executable"]) is str
             and os.path.realpath(state["base_executable"]) == launcher
             and os.path.realpath(state["prefix"]) == framework and os.path.realpath(state["base_prefix"]) == framework,
             "PYTHON", "The observer was not launched through the planned venv", details={"rule": "PYTHON-SELECTION"})
    _require(state["process_image"] == framework + "/" + PROCESS_IMAGE, "PYTHON",
             "The process image is not the framework's Python.app executable", details={"rule": "PYTHON-IMAGE"})
    _require(all(_inside(os.path.realpath(item), framework) for item in state["path"]), "PYTHON",
             "sys.path leaves the framework before the source binding", details={"rule": "PYTHON-PATH"})


def check_loaded_modules(rows, inventory, source_root, source_files):
    """Every loaded module file is a bound framework file or a bound source file without bytecode."""
    framework = inventory["framework"]["root"]
    entries = inventory["framework"]["entries"]
    for row in rows:
        path = os.path.realpath(row["file"])
        if _inside(path, framework):
            _require(entries.get(path[len(framework) + 1:], {}).get("kind") == "file", "PYTHON",
                     "Loaded module file is not in the framework inventory: " + path, details={"rule": "PYTHON-MODULE"})
            if row["cached"] and os.path.lexists(row["cached"]):
                cached = os.path.realpath(row["cached"])
                _require(_inside(cached, framework) and entries.get(cached[len(framework) + 1:], {}).get("kind")
                         == "file", "PYTHON", "Loaded module bytecode is unbound: " + cached,
                         details={"rule": "PYTHON-MODULE"})
        elif _inside(path, source_root):
            rel = path[len(source_root) + 1:]
            _require(rel in source_files, "PYTHON", "Loaded repository module is not in the source inventory: " + rel,
                     details={"rule": "PYTHON-MODULE"})
            _require(not (row["cached"] and os.path.lexists(row["cached"])), "PYTHON",
                     "Repository bytecode exists for a loaded module: " + rel, details={"rule": "PYTHON-MODULE"})
        else:
            raise ObservationError("PYTHON", "Loaded module file is outside every bound tree: " + path,
                                   details={"rule": "PYTHON-MODULE"})


# ---------------------------------------------------------------------------
# Source, dependencies, runtime and Git
# ---------------------------------------------------------------------------

def source_paths(root, *, check=_no_check):
    """The execution source inventory's path set (the 0.1.0 trees, plus the 0.2.0 roles)."""
    root = canonical_path(root)
    found = set()
    for tree in SOURCE_TREES:
        entries = tree_entries(root + "/" + tree, category="SOURCE", check=check, refuse_ds_store=True,
                               symlinks=False, file_maximum=LIMITS["tree_file_bytes"])
        for rel, entry in entries.items():
            name = posixpath.basename(rel)
            _require(name != "__pycache__", "SOURCE", "Unbound source bytecode directory: " + tree + "/" + rel,
                     details={"rule": "SOURCE-BYTECODE"})
            if entry["kind"] == "file":
                _require(not rel.endswith((".pyc", ".pyo")), "SOURCE", "Unbound source bytecode: " + rel,
                         details={"rule": "SOURCE-BYTECODE"})
                found.add(tree + "/" + rel)
    for rel in SOURCE_FILES:
        path = root + "/" + rel
        canonical_path(path)
        _require(os.path.isfile(path) and not os.path.islink(path), "SOURCE", "Required source role is missing: " + rel)
        found.add(rel)
    found.update(rel for rel in SOURCE_OPTIONAL if os.path.lexists(root + "/" + rel))
    return sorted(found)


def source_inventory(root, *, check=_no_check):
    root = canonical_path(root)
    files = {}
    for rel in source_paths(root, check=check):
        _, binding, _ = read_file(root + "/" + rel, LIMITS["tree_file_bytes"], category="SOURCE", check=check)
        files[rel] = binding
    return {"schema": SOURCE_SCHEMA, "files": files}


def git_head(root):
    """HEAD's commit from the checkout's Git files, statically and without starting Git."""
    dotgit = root + "/.git"
    try:
        info = os.lstat(dotgit)
    except OSError as exc:
        raise ObservationError("SOURCE", "The source root is not a Git checkout", cause=exc) from exc
    files = {}

    def read(path, maximum):
        raw, binding, _ = read_file(path, maximum, category="SOURCE", keep=True)
        files[path] = binding
        return raw
    if stat.S_ISDIR(info.st_mode):
        gitdir = dotgit
    else:
        _require(stat.S_ISREG(info.st_mode), "SOURCE", "Unsupported .git entry")
        text = read(dotgit, 4096).decode("utf-8", "replace").strip()
        _require(text.startswith("gitdir: "), "SOURCE", "Unsupported .git file")
        gitdir = text[len("gitdir: "):]
        if not gitdir.startswith("/"):
            gitdir = posixpath.normpath(root + "/" + gitdir)
    gitdir = canonical_path(gitdir)
    common = gitdir
    if os.path.lexists(gitdir + "/commondir"):
        relative = read(gitdir + "/commondir", 4096).decode("utf-8", "replace").strip()
        common = canonical_path(relative if relative.startswith("/") else posixpath.normpath(gitdir + "/" + relative))
    head = read(gitdir + "/HEAD", 4096).decode("ascii", "replace").strip()
    reference = None
    if head.startswith("ref: "):
        reference = head[5:]
        _relative(reference, "SOURCE")
        _require(reference.startswith("refs/"), "SOURCE", "HEAD names a ref outside refs/")
        commit = None
        for base in (gitdir, common):
            if os.path.lexists(base + "/" + reference):
                commit = read(base + "/" + reference, 4096).decode("ascii", "replace").strip()
                break
        if commit is None and os.path.lexists(common + "/packed-refs"):
            for line in read(common + "/packed-refs", 64 * 1024 * 1024).decode("utf-8", "replace").splitlines():
                parts = line.split(" ")
                if len(parts) == 2 and parts[1] == reference:
                    commit = parts[0]
        _require(commit is not None, "SOURCE", "HEAD's ref cannot be resolved statically: " + reference)
    else:
        commit = head
    _require(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is not None, "SOURCE", "HEAD is not a commit name")
    return {"gitdir": gitdir, "common_dir": common, "ref": reference, "commit": commit,
            "files": {path: files[path] for path in sorted(files)}}


def check_source(plan, observer_path, *, check=_no_check):
    source = plan["source"]
    root = source["root"]
    inventory, _ = _document(source["inventory"], LIMITS["document_bytes"], "SOURCE", check=check)
    _keys(inventory, ("schema", "files"), "SOURCE")
    _require(inventory["schema"] == SOURCE_SCHEMA and type(inventory["files"]) is dict, "SOURCE",
             "Unsupported source inventory")
    actual = source_paths(root, check=check)
    _require(set(inventory["files"]) == set(actual), "SOURCE", "Complete source inventory differs", details={
        "rule": "SOURCE-SET", "missing": sorted(set(inventory["files"]) - set(actual))[:50],
        "added": sorted(set(actual) - set(inventory["files"]))[:50]})
    for rel, binding in sorted(inventory["files"].items()):
        _relative(rel, "SOURCE")
        _binding_shape(binding, "SOURCE")
        _bound(root + "/" + rel, binding, category="SOURCE", private=True, check=check, rule="SOURCE-BINDING")
    _require(inventory["files"].get(ENTRY_POINT) == _binding(plan["observer"]), "SOURCE",
             "The observer is not bound by the source inventory")
    _require(observer_path == plan["observer"]["path"], "SOURCE", "The running observer is not the planned file",
             details={"rule": "SOURCE-OBSERVER"})
    _bound(observer_path, plan["observer"], category="SOURCE", rule="SOURCE-OBSERVER")
    head = git_head(root)
    _require(head["commit"] == source["commit"], "SOURCE", "HEAD differs from the planned commit",
             details={"rule": "SOURCE-COMMIT"})
    raw, binding, _ = read_file(root + "/" + MACOS_LOCK, 65536, category="SOURCE", keep=True)
    _require(binding == inventory["files"].get(MACOS_LOCK), "SOURCE", "The macOS lock is not the bound one")
    pins = read_lock_pins(raw)
    return {"inventory": inventory, "head": head, "pins": pins}


def _historical_dependencies(source_root):
    raw, binding, _ = read_file(source_root + "/" + EXTERNAL_INPUTS, 1024 * 1024, category="DEPENDENCY", keep=True)
    _require(binding["sha256"] == EXTERNAL_SHA256, "DEPENDENCY", "Historical dependency pin source changed")
    manifest = _loads(raw, "DEPENDENCY")
    _require(type(manifest) is dict and type(manifest.get("dependencies_root")) is str
             and type(manifest.get("files")) is dict, "DEPENDENCY", "Unsupported historical dependency manifest")
    prefix = manifest["dependencies_root"] + "/"
    expected = {name[len(prefix):]: row for name, row in manifest["files"].items() if name.startswith(prefix)}
    _require(len(expected) == DEPENDENCY_FILE_COUNT, "DEPENDENCY", "Expected the exact retained 24 dependency files")
    return expected


INSTALL_PLAN_KEYS = ("schema", "contract", "purpose", "source_root", "archive", "destination", "root_mode", "files",
                     "directories", "members", "node_source", "report")
INSTALL_RESULT_KEYS = ("schema", "contract", "purpose", "passed", "state", "apply_requested", "execution_counts",
                       "operations", "pins", "labels", "preparer_source", "archive", "before")


def _install_receipts(install, *, source_root, destination, purpose, archive, files, directories, root_mode, category):
    """The 0.1.0 receipt rule of _check_installation, adapted to install/0.2.0 (decision D-05).

    It compares the 0.1.0 rule's fields, in the shapes of W2's interface note:
    - the plan's closed keys, schema, contract, purpose, source_root, destination,
      root mode, files, directories, retained archive and report path;
    - the result's closed keys by state, schema, contract, purpose, the two receipt
      states (INSTALLED_EXACT applied with an exact after-readback,
      ALREADY_PRESENT_EXACT with an exact before-readback), zero starts, and the
      adopted pins (a receipt made through the synthetic test seam refuses);
    - the archive summary (digest, size, member count, expanded bytes and member
      inventory digest) against the plan, and the retained archive's bytes.
    Returns the record HOST keeps, and the plan's members digest and node_source.
    """
    _keys(install, ("plan", "result"), category)
    plan, _ = _document(install["plan"], LIMITS["document_bytes"], category, canonical=False)
    result, _ = _document(install["result"], LIMITS["document_bytes"], category, canonical=False)
    rule = {"rule": "INSTALL-PLAN"}
    _require(type(plan) is dict and set(plan) == set(INSTALL_PLAN_KEYS), category,
             "Installation plan members differ from install/0.2.0", details=rule)
    members = plan["members"]
    _require(plan["schema"] == INSTALL_SCHEMA and plan["contract"] == CONTRACT and plan["purpose"] == purpose
             and plan["source_root"] == source_root and plan["destination"] == destination
             and plan["root_mode"] == root_mode and plan["files"] == files and plan["directories"] == directories
             and plan["archive"] == archive and plan["report"] == install["result"]["path"]
             and type(members) is dict and members
             and all(type(row) is dict and type(row.get("size_bytes")) is int for row in members.values()),
             category, "Installation plan is not the 0.2.0 plan of this source, destination, archive and tree",
             details=rule)
    rule = {"rule": "INSTALL-RESULT"}
    state = result.get("state") if type(result) is dict else None
    _require(state in ("INSTALLED_EXACT", "ALREADY_PRESENT_EXACT"), category,
             "Installation result is not a receipt state", details=rule)
    expected = set(INSTALL_RESULT_KEYS) | ({"after", "publication"} if state == "INSTALLED_EXACT" else set())
    _require(set(result) == expected, category, "Installation result members differ for its state", details=rule)
    pins = result["pins"]
    _require(result["schema"] == INSTALL_RESULT_SCHEMA and result["contract"] == CONTRACT
             and result["purpose"] == purpose and result["passed"] is True
             and result["execution_counts"] == {"node": 0, "ldd": 0, "checkers": 0}
             and type(result["operations"]) is list and type(pins) is dict
             and pins.get("origin") == "adopted-contract" and pins.get("node_archive_sha256") == NODE_ARCHIVE_SHA256
             and pins.get("dependency_archive_sha256") == DEPENDENCY_ARCHIVE_SHA256, category,
             "Installation result is not an exact receipt with zero starts and the adopted pins", details=rule)
    if state == "INSTALLED_EXACT":
        _require(result["apply_requested"] is True and type(result["after"]) is dict
                 and result["after"].get("state") == "complete_exact", category,
                 "Installation was not applied and read back exact", details=rule)
    else:
        _require(type(result["before"]) is dict and result["before"].get("state") == "complete_exact", category,
                 "The existing installation was not read back exact", details=rule)
    summary = result["archive"]
    members_sha256 = _sha256(_canonical_ascii(members))
    _require(type(summary) is dict and summary.get("sha256") == archive["sha256"]
             and summary.get("size_bytes") == archive["size_bytes"] and summary.get("members") == len(members)
             and summary.get("expanded_bytes") == sum(row["size_bytes"] for row in members.values())
             and summary.get("member_inventory_sha256") == members_sha256, category,
             "Installation result's archive summary differs from the plan", details=rule)
    _bound(archive["path"], archive, category=category, rule="INSTALL-ARCHIVE")
    return {"plan": dict(install["plan"]), "result": dict(install["result"]), "purpose": purpose, "state": state,
            "member_inventory_sha256": members_sha256, "node_source": plan["node_source"]}


def check_dependencies(plan, *, check=_no_check):
    """The exact 24-file reader tree, against the C199 pins and the frozen inventory."""
    deps = plan["dependencies"]
    root = deps["root"]
    historical = _historical_dependencies(plan["source"]["root"])
    inventory, _ = _document(deps["inventory"], 1024 * 1024, "DEPENDENCY", check=check)
    _keys(inventory, ("schema", "files", "directories", "archive"), "DEPENDENCY")
    _require(inventory["schema"] == DEPENDENCIES_SCHEMA, "DEPENDENCY", "Unsupported dependency inventory")
    _require(type(inventory["files"]) is dict and set(inventory["files"]) == set(historical), "DEPENDENCY",
             "The exact 24 dependency paths differ")
    for name, row in historical.items():
        _binding_shape(inventory["files"][name], "DEPENDENCY")
        _require({"sha256": inventory["files"][name]["sha256"], "size_bytes": inventory["files"][name]["size_bytes"]}
                 == row, "DEPENDENCY", "Dependency bytes differ from their historical pin: " + name)
    _require(type(inventory["directories"]) is dict, "DEPENDENCY", "Invalid dependency directory inventory")
    necessary = {posixpath.dirname(name) for name in inventory["files"]}
    necessary = {"/".join(name.split("/")[:index]) for name in necessary for index in range(1, len(name.split("/")) + 1)}
    _require(set(inventory["directories"]) == necessary - {""}, "DEPENDENCY", "Dependency directories are not exact")
    _binding_shape(inventory["archive"], "DEPENDENCY", descriptor=True)
    _require(inventory["archive"]["sha256"] == DEPENDENCY_ARCHIVE_SHA256, "DEPENDENCY", "Retained archive differs")
    _bound(inventory["archive"]["path"], inventory["archive"], category="DEPENDENCY", check=check)
    entries = tree_entries(root, category="DEPENDENCY", check=check, refuse_ds_store=True, private=True,
                           symlinks=False)
    actual_files = {rel: _binding(entry) for rel, entry in entries.items() if entry["kind"] == "file"}
    actual_dirs = {rel: entry["mode"] for rel, entry in entries.items() if entry["kind"] == "directory"}
    _require(actual_files == {name: _binding(row) for name, row in inventory["files"].items()}
             and actual_dirs == inventory["directories"], "DEPENDENCY", "The installed reader tree is not exact",
             details={"rule": "DEPENDENCY-TREE", "missing": sorted(set(inventory["files"]) - set(actual_files)),
                      "added": sorted(set(actual_files) - set(inventory["files"]))})
    for name, version in DEPENDENCY_VERSIONS:
        package = _loads(read_file(root + "/" + name, 32768, category="DEPENDENCY", keep=True)[0], "DEPENDENCY")
        _require(type(package) is dict and package.get("version") == version, "DEPENDENCY",
                 "Dependency package version differs: " + name)
    receipts = _install_receipts(deps["install"], source_root=plan["source"]["root"], destination=root,
                                 purpose="retained-dependencies", archive=inventory["archive"],
                                 files={name: _binding(row) for name, row in inventory["files"].items()},
                                 directories=inventory["directories"], root_mode=_mode(os.lstat(root)),
                                 category="DEPENDENCY")
    planned_source, _ = receipts.pop("node_source"), receipts.pop("member_inventory_sha256")
    _require(planned_source is None, "DEPENDENCY", "A reader-tree plan carries node_source",
             details={"rule": "INSTALL-PLAN"})
    return {"root": root, "inventory": dict(deps["inventory"]), "archive": dict(inventory["archive"]),
            "files": len(actual_files), "install": receipts}


def check_node_source(raw, executable):
    """Plan section 4.2: NODE-SOURCE.json's canonical bytes and content."""
    value = _loads(raw, "RUNTIME")
    _require(type(value) is dict and _canonical_ascii(value) == raw, "RUNTIME",
             "NODE-SOURCE.json is not canonical JSON", details={"rule": "NODE-SOURCE"})
    _keys(value, NODE_SOURCE_KEYS, "RUNTIME")
    _require(value["schema"] == NODE_SOURCE_SCHEMA and value["contract"] == CONTRACT, "RUNTIME",
             "NODE-SOURCE.json schema or contract differs", details={"rule": "NODE-SOURCE"})
    archive = value["archive"]
    _keys(archive, ("name", "sha256", "size_bytes"), "RUNTIME")
    _require(archive["name"] == NODE_ARCHIVE and archive["sha256"] == NODE_ARCHIVE_SHA256
             and type(archive["size_bytes"]) is int and archive["size_bytes"] > 0, "RUNTIME",
             "NODE-SOURCE.json archive differs from the pin", details={"rule": "NODE-SOURCE"})
    _require(value["checksum_file"] == dict(NODE_CHECKSUM_FILE), "RUNTIME", "Checksum-file identity differs",
             details={"rule": "NODE-SOURCE"})
    signature = value["signature_check"]
    _keys(signature, ("status", "detail"), "RUNTIME")
    _require(signature["status"] in SIGNATURE_STATES and type(signature["detail"]) is str and signature["detail"],
             "RUNTIME", "Invalid signature-check record", details={"rule": "NODE-SOURCE"})
    _digest(value["member_inventory_sha256"], "RUNTIME")
    extracted = value["extracted"]
    _keys(extracted, ("member", "path", "sha256", "size_bytes", "mode"), "RUNTIME")
    _require(extracted["member"] == NODE_MEMBER and extracted["path"] == "bin/node"
             and _binding(extracted) == _binding(executable), "RUNTIME",
             "NODE-SOURCE.json does not describe the bound executable", details={"rule": "NODE-SOURCE"})
    return value


def check_runtime(plan, *, check=_no_check):
    """MC05: exact layout, the executable pin, the thin arm64 Mach-O rules and NODE-SOURCE.json."""
    runtime = plan["runtime"]
    directory = runtime["directory"]
    entries = tree_entries(directory, category="RUNTIME", check=check, refuse_ds_store=True, private=True,
                           symlinks=False, file_maximum=max(runtime["executable"]["size_bytes"],
                                                            LIMITS["tree_file_bytes"]))
    _require({rel: entry["kind"] for rel, entry in entries.items()} == dict(RUNTIME_LAYOUT), "RUNTIME",
             "The runtime directory is not exactly {bin/, bin/node, NODE-SOURCE.json}",
             details={"rule": "RUNTIME-LAYOUT", "entries": sorted(entries)})
    info = os.lstat(directory)
    _require(_mode(info) == runtime["root_mode"] and entries["bin"]["mode"] == runtime["bin_mode"], "RUNTIME",
             "Runtime directory modes differ", details={"rule": "RUNTIME-LAYOUT"})
    executable = directory + "/bin/node"
    _require(_binding(entries["bin/node"]) == _binding(runtime["executable"]), "RUNTIME",
             "Node's SHA-256, size or mode differs from the frozen plan", details={"rule": "RUNTIME-PIN"})
    binding, summary = read_macho(executable, maximum=runtime["executable"]["size_bytes"], private=True,
                                  category="RUNTIME", check=check, expected=runtime["executable"])
    rules = check_node_macho(summary)
    raw, source_binding, _ = read_file(directory + "/" + NODE_SOURCE_NAME, 65536, category="RUNTIME", private=True,
                                       keep=True, check=check)
    _require(source_binding == _binding(runtime["node_source"]), "RUNTIME", "NODE-SOURCE.json bytes differ from the "
             "frozen plan", details={"rule": "NODE-SOURCE"})
    content = check_node_source(raw, runtime["executable"])
    receipts = _install_receipts(runtime["install"], source_root=plan["source"]["root"], destination=directory,
                                 purpose="selected-node", archive=runtime["archive"],
                                 files={"bin/node": _binding(runtime["executable"]),
                                        NODE_SOURCE_NAME: _binding(runtime["node_source"])},
                                 directories={"bin": runtime["bin_mode"]}, root_mode=runtime["root_mode"],
                                 category="RUNTIME")
    planned_source, members_sha256 = receipts.pop("node_source"), receipts.pop("member_inventory_sha256")
    _require(planned_source == {"signature_check": content["signature_check"]}
             and members_sha256 == content["member_inventory_sha256"]
             and content["archive"]["size_bytes"] == runtime["archive"]["size_bytes"], "RUNTIME",
             "NODE-SOURCE.json disagrees with the installation plan", details={"rule": "NODE-SOURCE"})
    return {"directory": directory, "executable": executable, "version": NODE_VERSION, "binding": binding,
            "archive": dict(runtime["archive"]),
            "node_source": {"path": directory + "/" + NODE_SOURCE_NAME, **source_binding, "content": content},
            "layout": {"root_mode": runtime["root_mode"], "bin_mode": runtime["bin_mode"],
                       "entries": sorted(entries)},
            "macho": macho_summary(summary), "references": rules["references"], "install": receipts}


def check_git_binding(git, *, dispatcher=GIT_DISPATCHER, check=_no_check):
    """The Git implementation used for source reads: absolute, canonical, regular, never the dispatcher."""
    path = git["path"]
    _require(path != dispatcher, "GIT", "The /usr/bin/git dispatcher is never the bound Git implementation",
             details={"rule": "GIT-DISPATCHER"})
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise ObservationError("GIT", "The bound Git implementation is missing: " + path, cause=exc,
                               details={"rule": "GIT-PATH"}) from exc
    _require(not stat.S_ISLNK(info.st_mode), "GIT", "The bound Git path is a symbolic link: " + path,
             details={"rule": "GIT-SYMLINK"})
    try:
        _require(canonical_path(path) == path, "GIT", "The bound Git path is not canonical: " + path)
    except ObservationError as exc:
        raise ObservationError("GIT", "The bound Git path is not canonical: " + path, cause=exc,
                               details={"rule": "GIT-PATH"}) from exc
    _, actual, _ = read_file(path, max(git["size_bytes"], LIMITS["tree_file_bytes"]), category="GIT", check=check)
    _require(actual == _binding(git), "GIT", "The Git implementation's bytes differ from the binding",
             details={"rule": "GIT-DIGEST", "expected": _binding(git), "actual": actual})
    try:
        other = os.stat(dispatcher)
    except OSError:
        other = None
    if other is not None:
        _require((other.st_dev, other.st_ino) != (info.st_dev, info.st_ino), "GIT",
                 "The bound Git path is a hard link of the dispatcher", details={"rule": "GIT-DISPATCHER"})
        try:
            _, dispatcher_binding, _ = read_file(dispatcher, 64 * 1024 * 1024, category="GIT")
        except ObservationError:
            dispatcher_binding = None
        _require(dispatcher_binding is None or dispatcher_binding["sha256"] != actual["sha256"], "GIT",
                 "The bound Git bytes are the dispatcher's bytes", details={"rule": "GIT-DISPATCHER"})
    return {"path": path, **actual}


# ---------------------------------------------------------------------------
# Plan (ontokin.current-host-readback-observation-plan/0.2.0)
# ---------------------------------------------------------------------------

PLAN_KEYS = ("schema", "contract", "profile", "executor", "environment", "platform", "os", "source", "observer",
             "python", "runtime", "dependencies", "git", "commands", "evidence", "failure_capture", "limits")
COMMAND_KEYS = ("id", "kind", "argv", "cwd", "label", "environment", "timeout_ms", "active_work_ms", "cleanup_ms",
                "expected_direct_starts", "stdout_predicate", "stderr_predicate")
UNRESOLVED = re.compile(r"(?i)\b(todo|tbd|fixme|xxx)\b|[*?\[\]{}~`$]")


def output_paths(attempt):
    """The sole admitted output topology under the absent attempt directory; creates nothing."""
    outputs = {key: attempt + "/" + key + ".json" for key in ("reserved", "preflight", "result", "completion",
                                                                 "failure")}
    outputs["host"] = attempt + "/HOST.json"
    for name in COMMAND_IDS:
        stage, label = attempt + "/" + name, LABELS[name]
        outputs[name] = {"stage": stage, "intent": stage + "/intent.json", "started": stage + "/started.json",
                         "inspection": stage + "/inspection.json", "postflight": stage + "/postflight.json",
                         "failure": stage + "/failure.json", "stdout": stage + "/" + label + ".stdout.log",
                         "stderr": stage + "/" + label + ".stderr.log", "process": stage + "/" + label + ".process.json"}
    return outputs


def expected_commands(plan):
    attempt = plan["evidence"]["attempt"]
    node = plan["runtime"]["directory"] + "/bin/node"
    common = {"timeout_ms": LIMITS["command_ms"], "active_work_ms": LIMITS["active_work_ms"],
              "cleanup_ms": LIMITS["cleanup_ms"], "expected_direct_starts": 1, "stderr_predicate": ""}
    return [
        {"id": "git_version", "kind": "other", "argv": [plan["git"]["path"], "--version"],
         "cwd": attempt + "/git_version", "label": LABELS["git_version"], "environment": dict(GIT_ENVIRONMENT),
         "stdout_predicate": GIT_STDOUT_PREDICATE, **common},
        {"id": "node_version", "kind": "node", "argv": [node, "--version"], "cwd": attempt + "/node_version",
         "label": LABELS["node_version"], "environment": dict(ENVIRONMENT),
         "stdout_predicate": NODE_VERSION_STDOUT.decode("ascii"), **common}]


def _resolved(value, path="plan"):
    """P07 section 2: no null, no float, no TODO, wildcard or shell expansion anywhere in the plan."""
    _require(value is not None, "PLAN", "Unresolved null field: " + path, details={"rule": "PLAN-UNRESOLVED"})
    _require(type(value) is not float, "PLAN", "Non-integer number: " + path, details={"rule": "PLAN-UNRESOLVED"})
    if type(value) is dict:
        for key, item in value.items():
            _resolved(item, path + "." + key)
    elif type(value) is list:
        for index, item in enumerate(value):
            _resolved(item, path + "[" + str(index) + "]")
    elif type(value) is str:
        _require(UNRESOLVED.search(value) is None, "PLAN", "Unresolved, wildcard or shell-expansion text: " + path,
                 details={"rule": "PLAN-UNRESOLVED"})


def _ancestors(path):
    rows = []
    current = path
    while True:
        info = os.lstat(current)
        _require(stat.S_ISDIR(info.st_mode), "PATH", "Evidence ancestor is not a directory: " + current)
        rows.append({"path": current, "device": info.st_dev, "inode": info.st_ino, "mode": _mode(info)})
        if current == "/":
            break
        current = posixpath.dirname(current)
    return sorted(rows, key=lambda row: row["path"])


def _plan_shape(plan, host):
    _keys(plan, PLAN_KEYS, "PLAN")
    _require(plan["schema"] == PLAN_SCHEMA, "PLAN", "Unsupported observation plan schema (another version's documents "
             "are refused)", details={"rule": "PLAN-SCHEMA"})
    _require(plan["contract"] == CONTRACT and plan["profile"] == PROFILE and plan["executor"] == EXECUTOR, "PLAN",
             "Contract, profile or executor label differs")
    _require(plan["environment"] == dict(ENVIRONMENT), "PLAN", "The declared environment differs from the contract's",
             details={"rule": "PLAN-ENVIRONMENT"})
    _require(plan["limits"] == dict(LIMITS), "PLAN", "Limits differ from the fixed values")
    platform = plan["platform"]
    _keys(platform, ("system", "release", "machine", "proc_translated", "boot_session_uuid"), "PLAN")
    _require(platform["system"] == "Darwin" and platform["machine"] == "arm64" and platform["proc_translated"] == 0
             and type(platform["release"]) is str and re.fullmatch(r"\d+\.\d+\.\d+", platform["release"])
             and type(platform["boot_session_uuid"]) is str and UUID_TEXT.fullmatch(platform["boot_session_uuid"]),
             "PLAN", "Planned platform is not native Darwin arm64 with a release and boot")
    os_plan = plan["os"]
    _keys(os_plan, ("system_version", "cryptex"), "PLAN")
    _binding_shape(os_plan["system_version"], "PLAN", descriptor=True)
    _require(os_plan["system_version"]["path"] == host.system_version_path, "PLAN", "SystemVersion.plist path differs")
    cryptex = os_plan["cryptex"]
    _require(type(cryptex) is dict and cryptex.get("state") in ("present", "absent"), "PLAN",
             "Cryptex copy must be declared present or absent")
    if cryptex["state"] == "present":
        # The canonical path of the copy that host.cryptex_path resolves to. Only
        # its form is checked here; the resolution is the OS-CRYPTEX observation.
        _keys(cryptex, ("state", "path", "sha256", "size_bytes", "mode"), "PLAN")
        _binding_shape(_binding(cryptex), "PLAN")
        _canonical_value(cryptex["path"], "PLAN", allow_absent=True)
    else:
        _keys(cryptex, ("state", "path"), "PLAN")
        _require(cryptex["path"] == host.cryptex_path, "PLAN", "Cryptex SystemVersion.plist path differs")
    source = plan["source"]
    _keys(source, ("root", "commit", "tree", "inventory"), "PLAN")
    root = _canonical_value(source["root"], "SOURCE")
    for key in ("commit", "tree"):
        _require(type(source[key]) is str and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", source[key]), "SOURCE",
                 "Invalid source " + key)
    _binding_shape(source["inventory"], "PLAN", descriptor=True)
    _binding_shape(plan["observer"], "PLAN", descriptor=True)
    _require(plan["observer"]["path"] == root + "/" + ENTRY_POINT, "SOURCE", "Observer path is not under the source root")
    python = plan["python"]
    _keys(python, ("venv", "framework", "version", "inventory"), "PLAN")
    venv = _canonical_value(python["venv"], "PYTHON")
    framework = _canonical_value(python["framework"], "PYTHON")
    _require(venv == root + "/.venv", "PYTHON", "The venv must be the source checkout's own .venv")
    _framework_version(framework)
    _require(type(python["version"]) is str and re.fullmatch(re.escape(posixpath.basename(framework)) + r"\.\d+",
             python["version"]), "PYTHON", "Planned Python version disagrees with the framework")
    _binding_shape(python["inventory"], "PLAN", descriptor=True)
    runtime = plan["runtime"]
    _keys(runtime, ("directory", "version", "root_mode", "bin_mode", "executable", "node_source", "archive", "install"),
          "PLAN")
    directory = _canonical_value(runtime["directory"], "RUNTIME")
    _require(runtime["version"] == NODE_VERSION, "RUNTIME", "Declared Node version other than v24.22.1",
             details={"rule": "RUNTIME-VERSION"})
    for key in ("root_mode", "bin_mode"):
        _require(type(runtime[key]) is str and re.fullmatch(r"0o[0-7]{3,4}", runtime[key]), "PLAN", "Invalid " + key)
    _binding_shape(runtime["executable"], "PLAN")
    _require(runtime["executable"]["size_bytes"] > 0, "PLAN", "Empty Node pin")
    _binding_shape(runtime["node_source"], "PLAN")
    _binding_shape(runtime["archive"], "PLAN", descriptor=True)
    _require(runtime["archive"]["sha256"] == NODE_ARCHIVE_SHA256, "RUNTIME", "The retained Node archive is not the pin",
             details={"rule": "RUNTIME-ARCHIVE"})
    for owner in (runtime, plan["dependencies"]):
        _keys(owner["install"], ("plan", "result"), "PLAN")
        for key in ("plan", "result"):
            _binding_shape(owner["install"][key], "PLAN", descriptor=True)
    deps = plan["dependencies"]
    _keys(deps, ("root", "inventory", "install"), "PLAN")
    dependencies = _canonical_value(deps["root"], "DEPENDENCY")
    _binding_shape(deps["inventory"], "PLAN", descriptor=True)
    git = plan["git"]
    _keys(git, ("path", "sha256", "size_bytes", "mode"), "PLAN")
    _require(type(git["path"]) is str, "PLAN", "Git path must be a string")
    _require(git["path"] != host.git_dispatcher, "GIT", "The /usr/bin/git dispatcher is never the bound Git",
             details={"rule": "GIT-DISPATCHER"})
    _require(not os.path.islink(git["path"]), "GIT", "The bound Git path is a symbolic link: " + git["path"],
             details={"rule": "GIT-SYMLINK"})
    _binding_shape(git, "PLAN", descriptor=True)
    evidence = plan["evidence"]
    _keys(evidence, ("parent", "ancestors", "attempt", "outputs"), "PLAN")
    parent = _canonical_value(evidence["parent"], "PATH")
    _require(type(evidence["attempt"]) is str and posixpath.dirname(evidence["attempt"]) == parent
             and evidence["attempt"] != parent, "PATH", "The attempt must be a direct child of the evidence parent")
    _canonical_value(evidence["attempt"], "PATH", allow_absent=True)
    _require(evidence["outputs"] == output_paths(evidence["attempt"]), "PATH", "Output paths differ from the fixed "
             "topology")
    _require(type(evidence["ancestors"]) is list and evidence["ancestors"], "PATH", "Evidence ancestors are missing")
    for row in evidence["ancestors"]:
        _keys(row, ("path", "device", "inode", "mode"), "PATH")
    _keys(plan["failure_capture"], ("procedure",), "PLAN")
    _binding_shape(plan["failure_capture"]["procedure"], "PLAN", descriptor=True)
    _require(not _inside(plan["failure_capture"]["procedure"]["path"], evidence["attempt"]), "PATH",
             "The failure-capture procedure cannot be inside the attempt")
    for name, path in (("runtime", directory), ("dependencies", dependencies), ("framework", framework)):
        _require(not _inside(path, root) and not _inside(root, path), "PATH", "The " + name + " root overlaps the source")
    for first, second in ((directory, dependencies), (directory, framework), (dependencies, framework)):
        _require(not _inside(first, second) and not _inside(second, first), "PATH", "Bound roots overlap")
    for protected in (root, venv, framework, directory, dependencies, posixpath.dirname(plan["git"]["path"])):
        _require(not _inside(parent, protected) and not _inside(protected, parent), "PATH",
                 "The evidence parent overlaps a bound input root: " + protected)
    _require(type(plan["commands"]) is list and len(plan["commands"]) == len(COMMAND_IDS), "PLAN",
             "Exactly two ordered commands are required")
    for command in plan["commands"]:
        _keys(command, COMMAND_KEYS, "PLAN")
    _require(plan["commands"] == expected_commands(plan), "PLAN", "Commands differ from the frozen literal commands",
             details={"rule": "PLAN-COMMANDS"})


class ValidatedPlan:
    """An authenticated plan; it cannot grant approval."""
    __slots__ = ("plan", "descriptor")

    def __init__(self, plan, descriptor):
        self.plan, self.descriptor = plan, descriptor


def validate_plan(plan_path, plan_sha256, *, host=None):
    """Authenticate the plan's bytes against the externally supplied digest, then its shape (zero starts)."""
    host = host or Host()
    _digest(plan_sha256, "PLAN")
    path = _canonical_value(plan_path, "PLAN")
    raw, binding, _ = read_file(path, LIMITS["document_bytes"], category="PLAN", keep=True)
    _require(binding["sha256"] == plan_sha256, "PLAN", "Plan differs from the independently supplied digest",
             details={"rule": "PLAN-DIGEST"})
    plan = _decode(raw, "PLAN")
    _resolved(plan)
    _plan_shape(plan, host)
    return ValidatedPlan(plan, _descriptor(path, binding))


# ---------------------------------------------------------------------------
# The host boundary (real by default; tests substitute a mocked one)
# ---------------------------------------------------------------------------

class Host:
    """Real host readers. A subclass must set ``boundary = "mocked"``; every record then says so."""
    boundary = "real"
    system_version_path = SYSTEM_VERSION_PATH
    cryptex_path = CRYPTEX_SYSTEM_VERSION_PATH
    git_dispatcher = GIT_DISPATCHER

    def uname(self):
        return os.uname()

    def proc_translated(self):
        return read_proc_translated()

    def boot_session_uuid(self):
        return read_boot_session_uuid()

    def environment(self):
        return dict(os.environ)

    def launcher(self):
        return launcher_state()

    def loaded_modules(self):
        return loaded_module_files()

    def observer_path(self):
        return os.path.realpath(__file__)

    def supervisor(self, root, inventory):
        return load_darwin_supervisor(root, inventory)


def _check_boundary(host):
    _require(host.boundary in ("real", "mocked"), "PLAN", "Unknown host boundary label")
    _require(host.boundary == "mocked" or type(host) is Host, "PLAN", "A substituted host must be labelled mocked")
    return host.boundary


def load_darwin_supervisor(root, inventory):
    """Import the Darwin supervisor lazily, after the source inventory bound its bytes."""
    import importlib
    files = inventory["files"]
    for name, rel in SUPERVISOR_FILES.items():
        _require(rel in files, "SOURCE", "Supervisor module is outside the source inventory: " + rel,
                 details={"rule": "SUPERVISOR-UNBOUND"})
    added = root not in sys.path
    if added:
        sys.path.insert(0, root)
    try:
        module = importlib.import_module(SUPERVISOR_MODULE)
    except ObservationError:
        raise
    except Exception as exc:
        raise ObservationError("SOURCE", "The Darwin supervisor cannot be imported", cause=exc,
                               details={"rule": "SUPERVISOR-IMPORT"}) from exc
    finally:
        if added and root in sys.path:
            sys.path.remove(root)
    for name, rel in SUPERVISOR_FILES.items():
        loaded = sys.modules.get(name)
        path = getattr(loaded, "__file__", None)
        _require(type(path) is str and os.path.realpath(path) == root + "/" + rel, "SOURCE",
                 "Loaded supervisor module is not the bound file: " + name, details={"rule": "SUPERVISOR-UNBOUND"})
        _bound(root + "/" + rel, files[rel], category="SOURCE", rule="SUPERVISOR-UNBOUND")
        cached = getattr(loaded, "__cached__", None)
        _require(not (type(cached) is str and os.path.lexists(cached)), "SOURCE",
                 "Repository bytecode exists for the supervisor: " + rel, details={"rule": "SUPERVISOR-UNBOUND"})
    run_process = getattr(module, "run_process", None)
    code = getattr(run_process, "__code__", None)
    _require(code is not None and os.path.realpath(code.co_filename) == root + "/" + SUPERVISOR_FILES[SUPERVISOR_MODULE]
             and callable(getattr(module, "Clock", None)) and isinstance(getattr(module, "Stop", None), type),
             "SOURCE", "The Darwin supervisor lacks the bound run_process, Clock or Stop",
             details={"rule": "SUPERVISOR-UNBOUND"})
    return module


# ---------------------------------------------------------------------------
# Static observation (M0 without its start) and rechecks
# ---------------------------------------------------------------------------

def _python_static(plan, host, source, *, check):
    python = plan["python"]
    venv, framework = python["venv"], python["framework"]
    launcher = host.launcher()
    check_launcher(launcher, venv, framework, python["version"])
    expected, expected_raw = _document(python["inventory"], 256 * 1024 * 1024, "PYTHON", check=check)
    _require(type(expected) is dict and expected.get("schema") == PYTHON_INVENTORY_SCHEMA, "PYTHON",
             "Unsupported frozen Python inventory")
    actual = python_inventory(venv, framework, check=check)
    differences = compare_inventory(expected, actual)
    _require(not differences, "PYTHON", "The Python installation differs from its frozen inventory", details={
        "rule": "PYTHON-INVENTORY", "differences": differences[:100], "count": len(differences)})
    actual_raw = _canonical(actual)
    _require(actual_raw == expected_raw, "PYTHON", "The Python inventory's canonical bytes differ",
             details={"rule": "PYTHON-INVENTORY"})
    packages, records = verify_packages(venv, actual["venv"]["entries"], source["pins"],
                                        actual["selection"]["version_directory"])
    check_loaded_modules(host.loaded_modules(), actual, plan["source"]["root"], source["inventory"]["files"])
    return {"inventory": actual, "inventory_sha256": _sha256(actual_raw), "launcher": launcher,
            "packages": packages, "records": records}


def static_observation(validated, host, *, check=None):
    """Every M0 binding before any start; returns the facts that HOST records and rechecks compare."""
    check = check or _Deadline(LIMITS["static_ms"])
    plan = validated.plan
    boundary = _check_boundary(host)
    cf = check_environment(host.environment(), plan["environment"])
    platform = _platform(host)
    check_platform(platform, plan["platform"])
    identity = read_os_identity(system_path=host.system_version_path, cryptex_path=host.cryptex_path, check=check)
    _require(_binding(identity["system_version"]) == _binding(plan["os"]["system_version"]), "OS",
             "SystemVersion.plist differs from the plan", details={"rule": "OS-SYSTEM-VERSION"})
    planned = plan["os"]["cryptex"]
    _require(identity["cryptex"]["state"] == planned["state"] and identity["cryptex"]["path"] == planned["path"]
             and (planned["state"] == "absent" or _binding(identity["cryptex"]) == _binding(planned)), "OS",
             "The cryptex SystemVersion.plist differs from the plan", details={"rule": "OS-CRYPTEX"})
    source = check_source(plan, host.observer_path(), check=check)
    python = _python_static(plan, host, source, check=check)
    runtime = check_runtime(plan, check=check)
    dependencies = check_dependencies(plan, check=check)
    git = check_git_binding(plan["git"], dispatcher=host.git_dispatcher, check=check)
    _bound(plan["failure_capture"]["procedure"]["path"], plan["failure_capture"]["procedure"], category="PATH",
           check=check)
    evidence = plan["evidence"]
    _require(_ancestors(evidence["parent"]) == evidence["ancestors"], "PATH", "Evidence ancestor identities differ",
             details={"rule": "EVIDENCE-ANCESTORS"})
    _require(not os.path.lexists(evidence["attempt"]), "PATH", "The attempt directory already exists; "
             "reconciliation is required", details={"rule": "EVIDENCE-FRESH"})
    check()
    return {"boundary": boundary, "cf": cf, "platform": platform, "os": identity, "source": source,
            "python": python, "runtime": runtime, "dependencies": dependencies, "git": git}


def _fingerprint(facts):
    """The comparable part of the static facts (the launcher state is a property of this process)."""
    python = facts["python"]
    return _canonical({"cf": facts["cf"], "platform": facts["platform"], "os": facts["os"],
                       "source": {"inventory": facts["source"]["inventory"], "head": facts["source"]["head"]},
                       "python": {"inventory_sha256": python["inventory_sha256"], "packages": python["packages"]},
                       "runtime": facts["runtime"], "dependencies": facts["dependencies"], "git": facts["git"]})


class _Context:
    def __init__(self, validated, host, facts):
        self.validated, self.plan, self.descriptor = validated, validated.plan, validated.descriptor
        self.host, self.facts, self.boundary = host, facts, facts["boundary"]
        self.fingerprint = _fingerprint(facts)
        self.supervisor = None
        self.evidence = None

    def recheck(self, stage):
        """Recompute every static binding; any difference invalidates the attempt (zero new starts)."""
        try:
            _bound(self.descriptor["path"], self.descriptor, category="DRIFT")
            facts = static_after_start(self.validated, self.host)
        except ObservationError as exc:
            raise ObservationError("DRIFT", "A bound input changed or became unreadable at " + stage, cause=exc,
                                   details={"rule": "DRIFT", "stage": stage}) from exc
        _require(_fingerprint(facts) == self.fingerprint, "DRIFT", "A bound input changed at " + stage,
                 details={"rule": "DRIFT", "stage": stage})
        return {"stage": stage, "passed": True, "checked_at_utc": _utc(), "facts_sha256": _sha256(self.fingerprint)}

    def launch_check(self, command, clock, stage_end):
        """Final binding inside the command's own clock: the executable's bytes, platform and boot."""
        clock.check(stage_end)
        expected = self.plan["git"] if command["id"] == "git_version" else self.plan["runtime"]["executable"]
        _bound(command["argv"][0], expected, category="DRIFT", private=command["id"] == "node_version",
               check=lambda: clock.check(stage_end), rule="DRIFT")
        _require(_platform(self.host) == self.facts["platform"], "DRIFT", "Platform or boot changed before launch",
                 details={"rule": "DRIFT"})
        clock.check(stage_end)


def static_after_start(validated, host):
    """The static bindings again, without the freshness of the attempt directory."""
    plan = validated.plan
    check = _Deadline(LIMITS["static_ms"], "DRIFT")
    cf = check_environment(host.environment(), plan["environment"])
    platform = _platform(host)
    check_platform(platform, plan["platform"])
    identity = read_os_identity(system_path=host.system_version_path, cryptex_path=host.cryptex_path, check=check)
    source = check_source(plan, host.observer_path(), check=check)
    python = plan["python"]
    inventory = python_inventory(python["venv"], python["framework"], check=check)
    packages, _ = verify_packages(python["venv"], inventory["venv"]["entries"], source["pins"],
                                  inventory["selection"]["version_directory"])
    return {"cf": cf, "platform": platform, "os": identity, "source": source,
            "python": {"inventory_sha256": python_inventory_digest(inventory), "packages": packages},
            "runtime": check_runtime(plan, check=check), "dependencies": check_dependencies(plan, check=check),
            "git": check_git_binding(plan["git"], dispatcher=host.git_dispatcher, check=check)}


# ---------------------------------------------------------------------------
# Evidence: exclusive directories and no-replace publication (renamex_np)
# ---------------------------------------------------------------------------

def rename_exclusive(source, destination):
    """renamex_np(source, destination, RENAME_EXCL); never a fallback to a plain rename."""
    ctypes, libc = _libsystem()
    function = libc.renamex_np
    function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(os.fsencode(source), os.fsencode(destination), RENAME_EXCL) != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), destination)


def _path_readback(path):
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return {"path": path, "state": "absent"}
    except OSError as exc:
        return {"path": path, "state": "UNKNOWN", "failure": _failure(exc)}
    return {"path": path, "state": "present", "kind": stat.filemode(info.st_mode), "size_bytes": info.st_size}


class _Evidence:
    def __init__(self, plan, rename=rename_exclusive):
        evidence = plan["evidence"]
        self.parent, self.ancestors, self.root = evidence["parent"], evidence["ancestors"], evidence["attempt"]
        self.outputs, self.rename = evidence["outputs"], rename
        self.allowed, self.owned, self.publications = set(), {}, []

        def visit(value):
            if type(value) is str:
                self.allowed.add(value)
            elif type(value) is dict:
                for item in value.values():
                    visit(item)
        visit(self.outputs)

    def check_parent(self):
        _require(_ancestors(self.parent) == self.ancestors, "EVIDENCE", "The evidence parent changed", state="UNKNOWN")
        for path, identity in self.owned.items():
            info = os.lstat(path)
            _require(stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino, _mode(info)) == identity, "EVIDENCE",
                     "An owned evidence directory changed", state="UNKNOWN")

    @staticmethod
    def _fsync_directory(path):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def mkdir(self, path):
        self.check_parent()
        try:
            os.mkdir(path, 0o700)
        except FileExistsError as exc:
            raise ObservationError("PATH", "Evidence directory already exists; nothing is replaced: " + path,
                                   cause=exc) from exc
        info = os.lstat(path)
        _require(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700, "EVIDENCE",
                 "Private evidence directory mode differs", state="UNKNOWN")
        self.owned[path] = (info.st_dev, info.st_ino, _mode(info))
        self._fsync_directory(path)
        self._fsync_directory(posixpath.dirname(path))

    def create(self):
        self.mkdir(self.root)
        for name in COMMAND_IDS:
            self.mkdir(self.outputs[name]["stage"])

    def publish(self, path, value, *, maximum=LIMITS["document_bytes"]):
        _require(path in self.allowed and posixpath.dirname(path) in self.owned, "EVIDENCE",
                 "Unplanned evidence destination: " + path, state="UNKNOWN")
        raw = _canonical(value)
        _require(len(raw) <= maximum, "OUTPUT", "Evidence exceeds its byte limit: " + path)
        temporary = posixpath.join(posixpath.dirname(path), "." + posixpath.basename(path) + "." + os.urandom(8).hex()
                                   + ".tmp")
        expected = {"sha256": _sha256(raw), "size_bytes": len(raw), "mode": "0o600"}
        intent = {"source": temporary, "destination": path, "binding": expected, "state": "INTENT", "retry": False}
        self.publications.append(intent)
        fd = None
        try:
            self.check_parent()
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
                         0o600)
            offset = 0
            while offset < len(raw):
                written = os.write(fd, raw[offset:])
                _require(written > 0, "EVIDENCE", "Short evidence write", state="UNKNOWN")
                offset += written
            os.fsync(fd)
            os.close(fd)
            fd = None
            _bound(temporary, expected, category="EVIDENCE")
            self.rename(temporary, path)
            self._fsync_directory(posixpath.dirname(path))
            _bound(path, expected, category="EVIDENCE")
            self.check_parent()
            intent["state"] = "COMMITTED"
            return {"path": path, **expected}
        except BaseException as exc:
            intent.update(state="UNKNOWN", failure=_failure(exc), source_after=_path_readback(temporary),
                          destination_after=_path_readback(path))
            if isinstance(exc, OSError) and exc.errno == errno.EEXIST:
                category, reason = "PATH", "No-replace publication found an existing destination; nothing replaced"
            elif isinstance(exc, OSError) and exc.errno in (errno.ENOTSUP, getattr(errno, "EOPNOTSUPP", errno.ENOTSUP)):
                category, reason = "EVIDENCE", "The volume does not support RENAME_EXCL; no fallback rename"
            else:
                category, reason = "EVIDENCE", "Exclusive evidence publication failed; readback retained, no retry"
            raise ObservationError(category, reason, cause=exc, state="UNKNOWN", details=dict(intent)) from exc
        finally:
            if fd is not None:
                os.close(fd)

    def check_tree(self):
        """Contract section 7: the attempt holds only owned directories and planned files (no .DS_Store)."""
        entries = tree_entries(self.root, category="EVIDENCE", refuse_ds_store=True, private=True, symlinks=False,
                               maximum_entries=256)
        for rel, entry in entries.items():
            path = self.root + "/" + rel
            _require(path in (self.owned if entry["kind"] == "directory" else self.allowed), "EVIDENCE",
                     "Unplanned entry in the evidence tree: " + path, details={"rule": "EVIDENCE-TREE"})
        self.check_parent()

    def read_retained(self, path, maximum):
        _require(path in self.allowed, "EVIDENCE", "Unplanned retained artifact: " + path)
        raw, binding, _ = read_file(path, maximum, category="EVIDENCE", private=True, keep=True)
        return raw, {"path": path, **binding}


# ---------------------------------------------------------------------------
# M0's Git start and M1's Node start, through the Darwin supervisor
# ---------------------------------------------------------------------------

PROCESS_KEYS = ("argv", "cwd", "environment", "label", "start_monotonic", "pid", "process_group", "returncode",
                "observed_log_bytes", "retained_log_bytes", "cleanup", "handles_closed", "error", "end_monotonic")


def _process_success(process, command, stdout, stderr):
    _keys(process, PROCESS_KEYS, "PROCESS")
    _keys(process["cleanup"], ("passed", "process_group_absent", "reaped", "elapsed_ms"), "PROCESS")
    _require(process["argv"] == command["argv"] and process["cwd"] == command["cwd"]
             and process["environment"] == command["environment"] and process["label"] == command["label"], "PROCESS",
             "The process receipt's command binding differs")
    _require(type(process["pid"]) is int and process["pid"] > 0 and process["process_group"] == process["pid"]
             and process["returncode"] == 0 and process["handles_closed"] is True and process["error"] is None
             and process["cleanup"]["passed"] is True and process["cleanup"]["process_group_absent"] is True
             and process["cleanup"]["reaped"] is True, "PROCESS", "Missing, failed or unknown process outcome")
    _require(type(process["start_monotonic"]) in (int, float) and type(process["end_monotonic"]) in (int, float)
             and 0 <= process["end_monotonic"] - process["start_monotonic"] <= LIMITS["command_ms"] / 1000, "PROCESS",
             "The start exceeded its five-second allowance", state="TIMEOUT")
    _require(process["observed_log_bytes"] == process["retained_log_bytes"] == len(stdout) + len(stderr), "PROCESS",
             "Captured log byte counts disagree with the retained logs")


def _predicate(command, stdout, stderr):
    _require(stderr == b"", "OUTPUT", "The start wrote to stderr", details={"rule": "OUTPUT-STDERR"})
    if command["id"] == "node_version":
        _require(stdout == NODE_VERSION_STDOUT, "OUTPUT", "Observed Node version differs from v24.22.1",
                 details={"rule": "OUTPUT-NODE-VERSION", "observed": stdout[:64].decode("ascii", "replace")})
    else:
        _require(GIT_VERSION_LINE.fullmatch(stdout) is not None, "OUTPUT", "Git --version output is not one version "
                 "line", details={"rule": "OUTPUT-GIT-VERSION", "observed": stdout[:256].decode("ascii", "replace")})


def _run_start(context, command):
    paths = context.plan["evidence"]["outputs"][command["id"]]
    store, supervisor = context.evidence, context.supervisor
    record = {"schema": ATTEMPT_SCHEMA, "plan": context.descriptor, "command_id": command["id"], "kind": command["kind"],
              "argv": command["argv"], "expected_direct_starts": 1, "actual_direct_starts": None,
              "observed_direct_starts": 0, "start_count_state": "UNKNOWN", "state": "UNKNOWN", "start": None,
              "process": None, "supervisor_failure": None, "artifacts": {}, "preflight": None, "postflight": None,
              "boundary": context.boundary, "failure": None}
    entered, process, failure = False, None, None
    callback = {"count": 0, "error": None, "record": None}

    def observed(actual):
        if type(actual) is dict and type(actual.get("pid")) is int and actual["pid"] > 0:
            record.update(actual_direct_starts=1, observed_direct_starts=1, start_count_state="OBSERVED_ONE")
    try:
        store.publish(paths["intent"], record)
        record["preflight"] = context.recheck("before " + command["id"])
        clock = supervisor.Clock(total_ms=LIMITS["command_ms"])
        stage_end = clock.started + LIMITS["active_work_ms"] / 1000
        context.launch_check(command, clock, stage_end)
        started_at = _utc()

        def on_started(actual):
            callback["count"] += 1
            callback["record"] = json.loads(_canonical(actual))
            observed(actual)
            try:
                _require(callback["count"] == 1 and type(actual.get("pid")) is int
                         and actual.get("process_group") == actual.get("pid"), "PROCESS",
                         "Invalid or repeated start callback")
                clock.check(stage_end)
                record["start"] = store.publish(paths["started"], {
                    "schema": START_SCHEMA, "plan": context.descriptor, "command_id": command["id"],
                    "process": callback["record"], "observed_at_utc": _utc(), "boundary": context.boundary})
            except BaseException as exc:
                callback["error"] = exc
                raise
        entered = True
        try:
            process = supervisor.run_process(list(command["argv"]), stage=command["cwd"], label=command["label"],
                                             clock=clock, stage_end=stage_end, env=dict(command["environment"]),
                                             on_started=on_started, cancel_after_ms=None)
        except BaseException as exc:  # the supervisor's Stop and its record stay attached, never re-labelled
            failure, process = exc, getattr(exc, "process_record", None)
        finished_at = _utc()
        observed(process)
        record["process"] = json.loads(_canonical(process)) if type(process) is dict else None
        record["supervisor_failure"] = _failure(failure)
        streams = {}
        for key in ("stdout", "stderr", "process"):
            if os.path.lexists(paths[key]):
                streams[key], record["artifacts"][key] = store.read_retained(paths[key], LIMITS["log_bytes"])
        record["postflight"] = context.recheck("after " + command["id"])
        if callback["error"] is not None:
            raise ObservationError("PROCESS", "The start could not be durably recorded", cause=callback["error"],
                                   state="UNKNOWN")
        if failure is not None:
            raise ObservationError("PROCESS", "The supervisor did not complete the start", cause=failure,
                                   state=getattr(failure, "state", "UNKNOWN"))
        _require(callback["count"] == 1 and record["start_count_state"] == "OBSERVED_ONE", "PROCESS",
                 "No complete start evidence", state="UNKNOWN")
        _require(all(callback["record"].get(key) == process.get(key) for key in
                     ("pid", "process_group", "argv", "cwd", "environment", "label", "start_monotonic")), "PROCESS",
                 "The start callback and the final receipt disagree")
        stdout, stderr = streams.get("stdout", b""), streams.get("stderr", b"")
        _process_success(process, command, stdout, stderr)
        _require(streams.get("process") is not None and _loads(streams["process"], "PROCESS") == record["process"],
                 "PROCESS", "The supervisor's raw receipt disagrees with its returned record")
        _predicate(command, stdout, stderr)
        receipt = {"schema": INSPECTION_SCHEMA, "argv": command["argv"], "environment": command["environment"],
                   "timeout_ms": LIMITS["command_ms"], "started_at_utc": started_at, "finished_at_utc": finished_at,
                   "process": record["process"], "stdout": stdout.decode("ascii"), "stderr": stderr.decode("ascii")}
        inspection = store.publish(paths["inspection"], receipt, maximum=LIMITS["inspection_bytes"])
        record["artifacts"]["inspection"] = inspection
        record.update(state="COMPLETED")
        final = store.publish(paths["postflight"], record)
        return {"inspection": inspection, "attempt": final, "record": record, "stdout": stdout.decode("ascii"),
                "finished_at_utc": finished_at}
    except BaseException as exc:
        if not entered:
            record.update(actual_direct_starts=0, observed_direct_starts=0, start_count_state="PROVEN_ZERO")
        if isinstance(exc, ObservationError):
            error = exc
        else:
            error = ObservationError("PROCESS" if entered else "EVIDENCE", "The start attempt failed", cause=exc,
                                     state="UNKNOWN")
        record.update(state="UNKNOWN" if record["start_count_state"] == "UNKNOWN" else error.state,
                      failure=error.as_dict())
        if entered and record["postflight"] is None:
            try:
                record["postflight"] = context.recheck("after failed " + command["id"])
            except BaseException as post:
                record["postflight"] = {"passed": False, "failure": _failure(post)}
        try:
            store.publish(paths["failure"], {"schema": FAILURE_SCHEMA, "plan": context.descriptor,
                                             "command_id": command["id"], "failure": error.as_dict(),
                                             "process": record["process"], "boundary": context.boundary})
            record["attempt_descriptor"] = store.publish(paths["postflight"], record)
        except BaseException as evidence:
            record["evidence_failure"] = _failure(evidence)
        error.attempt = record
        raise error


def _starts(records):
    result = {}
    for kind in ("node", "other"):
        rows = [row for row in records if row["kind"] == kind]
        result[kind] = {"exact": None if any(row["actual_direct_starts"] is None for row in rows)
                        else sum(row["actual_direct_starts"] for row in rows),
                        "observed_lower_bound": sum(row["observed_direct_starts"] for row in rows)}
    return result


def _labels(facts, boundary):
    runtime = facts["runtime"]
    return {"executor": EXECUTOR, "contract": CONTRACT, "profile": PROFILE, "os": _os_label(facts["os"]),
            "node": {"archive": NODE_ARCHIVE, "archive_sha256": NODE_ARCHIVE_SHA256,
                     "executable": _binding(runtime["binding"]),
                     "signature_check": runtime["node_source"]["content"]["signature_check"]["status"]},
            "python_inventory_sha256": facts["python"]["inventory_sha256"],
            "git": {"path": facts["git"]["path"], "sha256": facts["git"]["sha256"]},
            "run_kind": RUN_KIND, "boundary": boundary}


def host_document(context, git_result, node_result):
    facts, plan = context.facts, context.plan
    python, runtime, source = facts["python"], facts["runtime"], facts["source"]
    host = {
        "schema": HOST_SCHEMA, "contract": CONTRACT, "profile": PROFILE, "executor": EXECUTOR,
        "observed_at_utc": _utc(), "plan": context.descriptor, "observer": dict(plan["observer"]),
        "platform": facts["platform"], "os": facts["os"],
        "environment": {"declared": dict(plan["environment"]), "cf_user_text_encoding": facts["cf"]},
        "python": {"launcher": plan["python"]["venv"] + "/bin/python", "venv": plan["python"]["venv"],
                   "framework": plan["python"]["framework"],
                   "interpreter": {key: python["launcher"][key] for key in
                                   ("implementation", "version", "build_string", "flags", "executable",
                                    "base_executable", "prefix", "base_prefix", "path", "process_image")},
                   "selection": python["inventory"]["selection"], "inventory": dict(plan["python"]["inventory"]),
                   "inventory_sha256": python["inventory_sha256"], "packages": python["packages"],
                   "records": python["records"], "lock": {"path": plan["source"]["root"] + "/" + MACOS_LOCK,
                                                          **source["inventory"]["files"][MACOS_LOCK]}},
        "runtime": {key: runtime[key] for key in ("directory", "executable", "version", "binding", "archive",
                                                  "node_source", "layout", "macho", "install")},
        "git": {**facts["git"], "version": git_result["stdout"][:-1]},
        "dependencies": facts["dependencies"],
        "source": {"root": plan["source"]["root"], "commit": plan["source"]["commit"], "tree": plan["source"]["tree"],
                   "tree_check": "planned value; M0 starts no Git read, and the provider's bound Git reads verify it",
                   "inventory": dict(plan["source"]["inventory"]), "head": source["head"]},
        "inspections": {"git_version": git_result["inspection"], "node_version": node_result["inspection"]},
        "starts": {"node": 1, "other": 1},
        "labels": _labels(facts, context.boundary), "claims": dict(CLAIMS)}
    finished = max(datetime.fromisoformat(row["finished_at_utc"]) for row in (git_result, node_result))
    _require(datetime.fromisoformat(host["observed_at_utc"]) >= finished, "OUTPUT",
             "HOST must follow its inspection receipts")
    return host


def static_check(plan_path, plan_sha256, *, host=None):
    """Validate the plan and every static binding; zero starts and zero writes."""
    host = host or Host()
    validated = validate_plan(plan_path, plan_sha256, host=host)
    facts = static_observation(validated, host)
    load = host.supervisor(validated.plan["source"]["root"], facts["source"]["inventory"])
    _require(load is not None, "SOURCE", "The Darwin supervisor is unavailable")
    return {"schema": RESULT_SCHEMA, "plan": validated.descriptor, "mode": "static", "state": "STATIC_READY",
            "starts": {"node": {"exact": 0, "observed_lower_bound": 0}, "other": {"exact": 0, "observed_lower_bound": 0}},
            "attempts": [], "host": None, "evidence_finalized": False, "failures": [],
            "labels": _labels(facts, facts["boundary"]), "facts_sha256": _sha256(_fingerprint(facts))}


def observe_host(plan_path, plan_sha256, *, host=None, rename=rename_exclusive):
    """M0 then M1. Success publishes HOST, result and completion; HOST stays OBSERVED_UNAPPROVED."""
    host = host or Host()
    _require(rename is rename_exclusive or _check_boundary(host) == "mocked", "PLAN",
             "A substituted publication function needs a host labelled mocked")
    validated = validate_plan(plan_path, plan_sha256, host=host)
    facts = static_observation(validated, host)
    context = _Context(validated, host, facts)
    context.supervisor = host.supervisor(validated.plan["source"]["root"], facts["source"]["inventory"])
    check_loaded_modules(host.loaded_modules(), facts["python"]["inventory"], validated.plan["source"]["root"],
                         facts["source"]["inventory"]["files"])
    outputs = validated.plan["evidence"]["outputs"]
    result = {"schema": RESULT_SCHEMA, "plan": validated.descriptor, "mode": "observe", "state": "UNKNOWN",
              "starts": _starts([]), "attempts": [], "host": None, "evidence_finalized": False, "failures": [],
              "labels": _labels(facts, context.boundary)}
    records, store = [], _Evidence(validated.plan, rename=rename)
    context.evidence = store
    try:
        store.create()
        result["reserved"] = store.publish(outputs["reserved"], {
            "schema": RESERVATION_SCHEMA, "plan": validated.descriptor, "attempt": store.root,
            "owned_directories": sorted(store.owned), "expected_starts": {"node": 1, "other": 1},
            "boundary": context.boundary})
        result["preflight"] = store.publish(outputs["preflight"], {
            "schema": PREFLIGHT_SCHEMA, "plan": validated.descriptor, "facts_sha256": _sha256(context.fingerprint),
            "python_inventory_sha256": facts["python"]["inventory_sha256"], "boundary": context.boundary})
        results = {}
        for command in validated.plan["commands"]:
            try:
                outcome = _run_start(context, command)
            except ObservationError as exc:
                if exc.attempt is not None:
                    records.append(exc.attempt)
                    result["attempts"].append(exc.attempt.get("attempt_descriptor"))
                raise
            records.append(outcome["record"])
            result["attempts"].append(outcome["attempt"])
            results[command["id"]] = outcome
        context.recheck("before HOST")
        store.check_tree()
        host_value = host_document(context, results["git_version"], results["node_version"])
        result["host"] = store.publish(outputs["host"], host_value, maximum=LIMITS["host_bytes"])
        result["starts"] = _starts(records)
        _require(result["starts"] == {"node": {"exact": 1, "observed_lower_bound": 1},
                                      "other": {"exact": 1, "observed_lower_bound": 1}}, "PROCESS",
                 "Start counts are incomplete")
        result["state"] = "PENDING_COMPLETION"
        descriptor = store.publish(outputs["result"], result)
        store.check_tree()
        completion = store.publish(outputs["completion"], {
            "schema": COMPLETION_SCHEMA, "plan": validated.descriptor, "state": "OBSERVED_UNAPPROVED",
            "result": descriptor, "host": result["host"], "starts": result["starts"], "evidence_finalized": True,
            "boundary": context.boundary})
        result.update(state="OBSERVED_UNAPPROVED", evidence_finalized=True, result=descriptor, completion=completion)
        return result
    except BaseException as exc:
        error = exc if isinstance(exc, ObservationError) else ObservationError(
            "EVIDENCE", "The observation failed", cause=exc, state="UNKNOWN")
        result.update(state=error.state, host=None, starts=_starts(records), evidence_finalized=False)
        result["failures"].append(error.as_dict())
        result["publications"] = store.publications
        if store.owned and not os.path.lexists(outputs["result"]) and \
                not any(row["destination"] == outputs["result"] for row in store.publications):
            try:
                store.publish(outputs["failure"], {"schema": FAILURE_SCHEMA, "plan": validated.descriptor,
                                                   "failure": error.as_dict(), "boundary": context.boundary})
                store.publish(outputs["result"], result)
            except BaseException as final:
                result["failures"].append(_failure(final))
                result["state"] = "UNKNOWN"
        error.result = result
        raise error


# ---------------------------------------------------------------------------
# Authoring commands for documents that a plan freezes (zero starts)
# ---------------------------------------------------------------------------

def write_new(path, value):
    """Exclusive creation of one absent output (O_EXCL), fsynced with its parent."""
    path = _canonical_value(path, "EVIDENCE", allow_absent=True)
    raw = _canonical(value)
    _require(len(raw) <= 256 * 1024 * 1024, "OUTPUT", "Output exceeds its byte limit")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0), 0o644)
        try:
            offset = 0
            while offset < len(raw):
                offset += os.write(fd, raw[offset:])
            os.fsync(fd)
        finally:
            os.close(fd)
        _Evidence._fsync_directory(posixpath.dirname(path))
    except OSError as exc:
        raise ObservationError("EVIDENCE", "Exclusive output creation failed: " + path, cause=exc) from exc
    _, binding, _ = read_file(path, len(raw), category="EVIDENCE")
    return {"path": path, **binding}


def _check_authoring_launcher():
    _require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode, "PYTHON",
             "Run under -I -S -B so that no bytecode is written into an inventoried tree",
             details={"rule": "PYTHON-LAUNCHER"})


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ObservationError("PLAN", "Invalid arguments: " + message)


def main(argv=None):
    parser = _Parser(prog="current_host_observation_v02", allow_abbrev=False,
                     description="M0 and M1 host observation for " + CONTRACT)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for name in ("static", "observe"):
        sub = commands.add_parser(name)
        sub.add_argument("--plan", required=True)
        sub.add_argument("--plan-sha256", required=True)
    sub = commands.add_parser("python-inventory")
    sub.add_argument("--venv", required=True)
    sub.add_argument("--framework", required=True)
    sub.add_argument("--output", required=True)
    sub = commands.add_parser("source-inventory")
    sub.add_argument("--root", required=True)
    sub.add_argument("--output", required=True)
    try:
        args = parser.parse_args(argv)
        _check_authoring_launcher()
        if args.command == "static":
            result = static_check(args.plan, args.plan_sha256)
        elif args.command == "observe":
            result = observe_host(args.plan, args.plan_sha256)
        elif args.command == "python-inventory":
            inventory = python_inventory(args.venv, args.framework, check=_Deadline(LIMITS["static_ms"]))
            result = {"schema": PYTHON_INVENTORY_SCHEMA, "output": write_new(args.output, inventory),
                      "starts": {"node": 0, "other": 0}}
        else:
            result = {"schema": SOURCE_SCHEMA, "output": write_new(args.output, source_inventory(args.root)),
                      "starts": {"node": 0, "other": 0}}
        sys.stdout.write(_canonical(result).decode("ascii") + "\n")
        return 0
    except ObservationError as exc:
        refusal = {"schema": REFUSAL_SCHEMA, "passed": False, "error": exc.as_dict(),
                   "evidence_finalized": bool(exc.result and exc.result.get("evidence_finalized")),
                   "result": exc.result}
        raw = _canonical(refusal)
        if len(raw) > LIMITS["document_bytes"]:
            raw = _canonical({"schema": REFUSAL_SCHEMA, "passed": False, "error": {"code": exc.code,
                              "reason": exc.reason, "state": exc.state}, "evidence_finalized": False,
                              "detail": "The refusal exceeded its capture bound"})
        sys.stderr.write(raw.decode("ascii") + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
