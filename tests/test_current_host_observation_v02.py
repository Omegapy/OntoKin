"""Development tests of the M0 and M1 observer (C271-P33, worker W3).

These are the implementer's development tests, not frozen controls: the
independent control author freezes those later, from the contract. Every input
is synthetic and lives under a fresh temporary directory:

* Mach-O bytes from the builder below (thin arm64 executables, dylibs and
  bundles with chosen load commands, and a fat header);
* framework, venv, runtime, reader and source trees, property lists and receipts;
* a fake Git implementation, a small shell script that no test executes.

Starts. No test starts Node, ldd, codesign, Git or the Darwin supervisor, and no
test imports prototypes.static_tray_v01.supervisor_darwin_v01. A mocked
supervisor records the starts it is asked for and writes synthetic logs; every
result it produces carries the boundary label "mocked". Two command-line tests
each start one Python interpreter (this observer, under -I -B) and say so. Some
tests call renamex_np on temporary files (a real system call, no process).
Constants that pin real historical bytes (the C199 manifest and C195 archive
digests) are patched to synthetic digests where a test needs them, and each such
test is labelled simulated.
"""
from __future__ import annotations

import ast
import base64
import errno
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from prototypes.static_tray_v01 import current_host_observation_v02 as observation


REPOSITORY = Path(__file__).resolve().parents[1]
OBSERVER = REPOSITORY / "prototypes/static_tray_v01/current_host_observation_v02.py"
DARWIN = sys.platform == "darwin"
BOOT = "0A1B2C3D-4E5F-4A6B-8C7D-9E0F1A2B3C4D"
CF_VALUE = "0x1F5:0x0:0x0"
GIT_STDOUT = b"git version 2.0.0 (synthetic)\n"
FILETYPE = {"MH_OBJECT": 1, "MH_EXECUTE": 2, "MH_DYLIB": 6, "MH_DYLINKER": 7, "MH_BUNDLE": 8}
LC = observation.LC


# ---------------------------------------------------------------------------
# Synthetic Mach-O builder
# ---------------------------------------------------------------------------

def lc(cmd, payload=b""):
    size = 8 + len(payload)
    pad = (-size) % 8
    return struct.pack("<II", cmd, size + pad) + payload + b"\0" * pad


def lc_named(name, payload=b""):
    return lc(LC[name], payload)


def dylib(name, path, current=0x10000, compatibility=0x10000):
    return lc_named(name, struct.pack("<IIII", 24, 2, current, compatibility) + path.encode() + b"\0")


def lc_path(name, path):
    return lc_named(name, struct.pack("<I", 12) + path.encode() + b"\0")


def segment(name, fileoff=0, filesize=0, nsects=0):
    payload = name.encode().ljust(16, b"\0") + struct.pack("<QQQQiiII", 0, 0x4000, fileoff, filesize, 5, 5, nsects, 0)
    return lc_named("LC_SEGMENT_64", payload + b"\0" * (80 * nsects))


def linkedit(name, offset=0, size=0):
    return lc_named(name, struct.pack("<II", offset, size))


def uuid_command():
    return lc_named("LC_UUID", bytes(range(16)))


def main_command(entry=0x200):
    return lc_named("LC_MAIN", struct.pack("<QQ", entry, 0))


def build_version():
    return lc_named("LC_BUILD_VERSION", struct.pack("<IIII", 1, 0x000E0000, 0x000F0500, 1) + struct.pack("<II", 3, 0x04000000))


def source_version():
    return lc_named("LC_SOURCE_VERSION", struct.pack("<Q", (1 << 40) | (2 << 30)))


def symtab():
    return lc_named("LC_SYMTAB", struct.pack("<IIII", 0, 0, 0, 0))


def dysymtab():
    return lc_named("LC_DYSYMTAB", b"\0" * 72)


def common_commands():
    return [segment("__PAGEZERO"), segment("__TEXT", 0, 256), segment("__LINKEDIT"),
            linkedit("LC_DYLD_CHAINED_FIXUPS"), linkedit("LC_DYLD_EXPORTS_TRIE"), symtab(), dysymtab(),
            uuid_command(), build_version(), source_version()]


def tail_commands():
    return [linkedit("LC_FUNCTION_STARTS"), linkedit("LC_DATA_IN_CODE"), linkedit("LC_CODE_SIGNATURE")]


def node_commands(*extra, dylinker="/usr/lib/dyld"):
    return (common_commands() + [lc_path("LC_LOAD_DYLINKER", dylinker), main_command(),
            dylib("LC_LOAD_DYLIB", "/usr/lib/libSystem.B.dylib"),
            dylib("LC_LOAD_DYLIB", "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation"),
            dylib("LC_LOAD_WEAK_DYLIB", "/usr/lib/libc++.1.dylib")] + list(extra) + tail_commands())


def macho(filetype="MH_EXECUTE", commands=None, *, cputype=observation.CPU_TYPE_ARM64, cpusubtype=0,
          magic=observation.MH_MAGIC_64, pad=4096, ncmds=None, sizeofcmds=None):
    commands = node_commands() if commands is None else commands
    body = b"".join(commands)
    header = struct.pack("<8I", magic, cputype, cpusubtype, FILETYPE.get(filetype, filetype),
                         len(commands) if ncmds is None else ncmds, len(body) if sizeofcmds is None else sizeofcmds,
                         0x00200085, 0)
    return header + body + b"\0" * pad


def fat(thin):
    header = struct.pack(">II", 0xCAFEBABE, 1) + struct.pack(">IIIII", observation.CPU_TYPE_ARM64, 0, 4096,
                                                             len(thin), 14)
    return header + b"\0" * (4096 - len(header)) + thin


def dylib_image(identity, *references, rpaths=()):
    commands = common_commands() + [dylib("LC_ID_DYLIB", identity)]
    commands += [dylib("LC_LOAD_DYLIB", path) for path in references]
    commands += [lc_path("LC_RPATH", path) for path in rpaths]
    return macho("MH_DYLIB", commands + tail_commands())


def bundle_image(*references, rpaths=()):
    commands = common_commands() + [dylib("LC_LOAD_DYLIB", path) for path in references]
    commands += [lc_path("LC_RPATH", path) for path in rpaths]
    return macho("MH_BUNDLE", commands + tail_commands())


def executable_image(*references, rpaths=()):
    commands = common_commands() + [lc_path("LC_LOAD_DYLINKER", "/usr/lib/dyld"), main_command()]
    commands += [dylib("LC_LOAD_DYLIB", path) for path in references]
    commands += [lc_path("LC_RPATH", path) for path in rpaths]
    return macho("MH_EXECUTE", commands + tail_commands())


def parse(data):
    return observation.parse_macho(data, len(data))


# ---------------------------------------------------------------------------
# Synthetic host workspace
# ---------------------------------------------------------------------------

def write(path, data, mode=0o644):
    """Create or replace one file (a replaced file gets a new inode, as an editor's save would)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        os.unlink(path)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    os.chmod(path, mode)
    return str(path)


def link(path, target):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    os.symlink(target, path)


def b64(data):
    return base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def binding(path):
    data = Path(path).read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "mode": "0o%03o" % stat.S_IMODE(os.lstat(path).st_mode)}


def descriptor(path):
    return {"path": str(path), **binding(path)}


REMOVED = object()
REMOVED_VALUE = object()
REVISION = {"contract": observation.CONTRACT, "design_revision": 4, "amendments": ["P33-AMENDMENT-001"]}
OS_LABEL = {"product_version": "26.6.2", "product_build_version": "25G83", "product_version_extra": None,
            "cryptex": {"state": "present", "product_version": "26.6.2", "product_build_version": "25G83",
                        "product_version_extra": None}}
PACKAGES = (("attrs", "26.1.0", "attrs", "attr"), ("jsonschema", "4.26.0", "jsonschema", "jsonschema"),
            ("jsonschema-specifications", "2025.9.1", "jsonschema_specifications", "jsonschema_specifications"),
            ("referencing", "0.37.0", "referencing", "referencing"), ("rpds-py", "2026.5.1", "rpds_py", "rpds"),
            ("typing_extensions", "4.16.0", "typing_extensions", "typing_extensions_pkg"),
            ("Pillow", "13.0.0", "pillow", "PIL"))


class MockedClock:
    def __init__(self, *, total_ms=65000, cancel_file=None):
        import time
        self.started = time.monotonic()
        self.end = self.started + total_ms / 1000
        self.requested_ms = total_ms

    def check(self, stage_end=None):
        return None

    def elapsed_ms(self):
        return 1.0


class MockedStop(Exception):
    def __init__(self, code, reason, state="REJECTED"):
        self.code, self.reason, self.state = code, reason, state
        super().__init__(reason)

    def as_dict(self):
        return {"code": self.code, "reason": self.reason, "state": self.state}


class MockedSupervisor:
    """Stands in for supervisor_darwin_v01 at the command boundary; it starts nothing."""
    Clock = MockedClock
    Stop = MockedStop

    def __init__(self):
        self.calls, self.outputs, self.before = [], {}, {}

    def run_process(self, argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):
        kind = "node" if argv[0].endswith("/bin/node") else "git"
        self.calls.append({"kind": kind, "argv": list(argv), "label": label, "env": dict(env),
                           "cancel_after_ms": cancel_after_ms})
        if kind in self.before:
            self.before[kind]()
        stdout, stderr, returncode, stop = self.outputs.get(kind, (GIT_STDOUT if kind == "git" else b"v24.22.1\n",
                                                                   b"", 0, None))
        stage = os.path.realpath(stage)
        record = {"argv": argv, "cwd": stage, "environment": env, "label": label, "start_monotonic": clock.started,
                  "pid": 4242 + len(self.calls), "process_group": 4242 + len(self.calls), "returncode": None,
                  "observed_log_bytes": 0, "retained_log_bytes": 0, "cleanup": None, "handles_closed": False,
                  "error": None}
        on_started(dict(record))
        for suffix, data in (("stdout.log", stdout), ("stderr.log", stderr)):
            with open(os.path.join(stage, label + "." + suffix), "xb") as stream:
                stream.write(data)
        record.update(observed_log_bytes=len(stdout) + len(stderr), retained_log_bytes=len(stdout) + len(stderr),
                      returncode=returncode, handles_closed=True, end_monotonic=clock.started + 0.01)
        failure = None
        if stop is not None:
            failure = MockedStop("OTRAY-E-BACKEND", stop)
        elif returncode != 0:
            failure = MockedStop("OTRAY-E-BACKEND", "Child exited with status " + str(returncode))
        if failure is not None:
            record["error"] = failure.as_dict()
            record["cleanup"] = {"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 1}
        else:
            record["cleanup"] = {"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 0}
        with open(os.path.join(stage, label + ".process.json"), "wb") as stream:
            stream.write(canonical(record))
        if failure is not None:
            failure.process_record = record
            raise failure
        return record


class MockedHost(observation.Host):
    """The host boundary with synthetic readers; every record is labelled mocked."""
    boundary = "mocked"

    def __init__(self, workspace):
        self.workspace = workspace
        self.system_version_path = workspace.system_plist
        self.cryptex_path = workspace.cryptex_plist
        self.git_dispatcher = workspace.dispatcher
        self.sysname, self.machine, self.release, self.translated = "Darwin", "arm64", "25.6.0", 0
        self.boot = BOOT
        self.env = {**observation.ENVIRONMENT, observation.CF_NAME: CF_VALUE}
        self.mocked_supervisor = MockedSupervisor()
        self.launch_flags = {name: 0 for name in observation.FLAG_NAMES}
        self.launch_flags.update(isolated=1, no_site=1, dont_write_bytecode=1, ignore_environment=1, no_user_site=1,
                                 safe_path=True, dev_mode=False, hash_randomization=1, int_max_str_digits=4300)

    def uname(self):
        return SimpleNamespace(sysname=self.sysname, release=self.release, version="Darwin Kernel Version synthetic",
                               machine=self.machine)

    def proc_translated(self):
        if self.translated is None:
            raise observation.ObservationError("PLATFORM", "sysctl.proc_translated is unreadable")
        return self.translated

    def boot_session_uuid(self):
        return self.boot

    def environment(self):
        return dict(self.env)

    def launcher(self):
        framework = self.workspace.framework
        return {"implementation": "cpython", "platform": "darwin", "version": "3.12.13",
                "build_string": "3.12.13 (synthetic)", "flags": dict(self.launch_flags), "site_imported": False,
                "executable": self.workspace.venv + "/bin/python", "base_executable": framework + "/bin/python3.12",
                "prefix": framework, "base_prefix": framework,
                "path": [framework + "/lib/python312.zip", framework + "/lib/python3.12",
                         framework + "/lib/python3.12/lib-dynload"],
                "process_image": framework + "/" + observation.PROCESS_IMAGE}

    def loaded_modules(self):
        framework = self.workspace.framework
        return [{"name": "os", "file": framework + "/lib/python3.12/os.py",
                 "cached": framework + "/lib/python3.12/__pycache__/os.cpython-312.pyc"},
                {"name": "__main__", "file": self.workspace.observer, "cached": None}]

    def observer_path(self):
        return self.workspace.observer

    def supervisor(self, root, inventory):
        return self.mocked_supervisor


class Workspace:
    """One complete synthetic host: trees, documents and an observation plan."""

    def __init__(self, test):
        self.test = test
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="w3-observer-"))
        test.addCleanup(shutil.rmtree, self.base, True)
        self.counter = 0
        self.prefix = self.base + "/prefix"
        self.framework = self.prefix + "/Cellar/python/3.12.13/Frameworks/Python.framework/Versions/3.12"
        self.source = self.base + "/source"
        self.venv = self.source + "/.venv"
        self.runtime = self.base + "/runtime"
        self.dependencies = self.base + "/reader"
        self.evidence = self.base + "/evidence"
        self.attempt = self.evidence + "/attempt-1"
        self.git = self.base + "/git/bin/git"
        self.dispatcher = self.base + "/dispatcher/git"
        self.system_plist = self.base + "/os/System/Library/CoreServices/SystemVersion.plist"
        # As on macOS 26: the conventional name passes through System/Cryptexes/OS, a relative link.
        self.cryptex_plist = self.base + "/os/System/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist"
        self.cryptex_canonical = (self.base + "/os/System/Volumes/Preboot/Cryptexes/OS/System/Library/CoreServices/"
                                  "SystemVersion.plist")
        self.observer = self.source + "/" + observation.ENTRY_POINT
        self.commit = "1" * 39 + "2"
        self.tree = "3" * 39 + "4"
        # Simulated pins: the retained archives are synthetic bytes, so the pins are patched to them.
        self.node_archive = write(self.base + "/archives/node-v24.22.1-darwin-arm64.tar.gz", b"synthetic node archive")
        self.archive = write(self.base + "/archives/c195-synthetic.zip", b"synthetic retained archive")
        self.patch("NODE_ARCHIVE_SHA256", binding(self.node_archive)["sha256"])
        self.patch("DEPENDENCY_ARCHIVE_SHA256", binding(self.archive)["sha256"])
        self.receipts = self.base + "/receipts"
        self.build_python()
        self.build_source()
        self.build_runtime()
        self.build_dependencies()
        self.build_host_files()
        self.patch("EXTERNAL_SHA256", binding(self.source + "/" + observation.EXTERNAL_INPUTS)["sha256"])
        self.host = MockedHost(self)

    def patch(self, name, value):
        patcher = patch.object(observation, name, value)
        patcher.start()
        self.test.addCleanup(patcher.stop)

    # -- trees ---------------------------------------------------------------
    def build_python(self):
        framework, prefix = self.framework, self.prefix
        write(framework + "/Python", dylib_image(prefix + "/opt/python/Frameworks/Python.framework/Versions/3.12/Python",
              "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation",
              "/usr/lib/libSystem.B.dylib", rpaths=(prefix + "/lib",)), 0o755)
        write(framework + "/bin/python3.12", executable_image(framework + "/Python", "/usr/lib/libSystem.B.dylib"), 0o755)
        write(framework + "/" + observation.PROCESS_IMAGE, executable_image(
              "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation", framework + "/Python",
              "/usr/lib/libSystem.B.dylib", rpaths=(prefix + "/lib",)), 0o755)
        write(framework + "/lib/python3.12/lib-dynload/_dep.cpython-312-darwin.so",
              bundle_image(prefix + "/opt/dep/lib/libdep.1.dylib", "/usr/lib/libSystem.B.dylib",
                           rpaths=(prefix + "/lib",)), 0o755)
        write(framework + "/lib/python3.12/os.py", "# synthetic os\n")
        write(framework + "/lib/python3.12/__pycache__/os.cpython-312.pyc", b"\x00synthetic bytecode")
        write(framework + "/include/python3.12/Python.h", "/* synthetic */\n")
        link(framework + "/Headers", "include/python3.12")
        link(framework + "/lib/python3.12/site-packages", "../../../../../../lib/python3.12/site-packages")
        link(prefix + "/Cellar/python/3.12.13/bin/python3.12", "../Frameworks/Python.framework/Versions/3.12/bin/python3.12")
        link(prefix + "/opt/python", "../Cellar/python/3.12.13")
        write(prefix + "/Cellar/dep/1.0/lib/libdep.1.0.dylib", dylib_image(prefix + "/opt/dep/lib/libdep.1.dylib",
              "/usr/lib/libSystem.B.dylib", rpaths=("@loader_path/../lib",)), 0o444)
        link(prefix + "/Cellar/dep/1.0/lib/libdep.1.dylib", "libdep.1.0.dylib")
        link(prefix + "/opt/dep", "../Cellar/dep/1.0")
        venv = self.venv
        link(venv + "/bin/python", "python3.12")
        link(venv + "/bin/python3", "python3.12")
        link(venv + "/bin/python3.12", prefix + "/opt/python/bin/python3.12")
        write(venv + "/bin/activate", "# synthetic activate\n")
        Path(venv + "/include/python3.12").mkdir(parents=True)
        write(venv + "/pyvenv.cfg", "home = %s/opt/python/bin\ninclude-system-site-packages = false\nversion = 3.12.13\n"
              "executable = %s/bin/python3.12\n" % (prefix, framework))
        self.site = venv + "/lib/python3.12/site-packages"
        for name, version, dist, module in PACKAGES:
            self.add_package(name, version, dist, module)

    def add_package(self, name, version, dist, module, *, extra_rows=(), corrupt=None):
        site = self.site
        files = {module + "/__init__.py": ("# %s\n" % name).encode(),
                 dist + "-" + version + ".dist-info/METADATA": ("Metadata-Version: 2.1\nName: %s\nVersion: %s\n\nBody\n"
                                                                % (name, version)).encode(),
                 dist + "-" + version + ".dist-info/INSTALLER": b"pip\n"}
        if module == "PIL":
            files["PIL/.dylibs/libsynthetic.1.dylib"] = dylib_image("@rpath/libsynthetic.1.dylib",
                                                                    "/usr/lib/libSystem.B.dylib")
            files["PIL/_imaging.cpython-312-darwin.so"] = bundle_image("@loader_path/.dylibs/libsynthetic.1.dylib",
                                                                       "/usr/lib/libSystem.B.dylib")
        rows = []
        for rel, data in files.items():
            write(site + "/" + rel, data, 0o755 if rel.endswith((".so", ".dylib")) else 0o644)
            rows.append("%s,sha256=%s,%d" % (rel, b64(data), len(data)))
        write(site + "/" + module + "/__pycache__/__init__.cpython-312.pyc", b"\x00bytecode")
        rows.append(module + "/__pycache__/__init__.cpython-312.pyc,,")
        rows.extend(extra_rows)
        record = dist + "-" + version + ".dist-info/RECORD"
        rows.append(record + ",,")
        text = "\n".join(rows) + "\n"
        if corrupt is not None:
            text = corrupt(text)
        write(site + "/" + record, text)

    def build_source(self):
        source = self.source
        write(self.observer, OBSERVER.read_bytes())
        write(source + "/prototypes/__init__.py", '"""synthetic"""\n')
        write(source + "/prototypes/static_tray_v01/__init__.py", '"""synthetic"""\n')
        write(source + "/prototypes/static_tray_v01/supervisor.py", "class Clock:\n    pass\n\n\nclass Stop(Exception):\n"
              "    pass\n")
        write(source + "/prototypes/static_tray_v01/supervisor_darwin_v01.py", "from .supervisor import Clock, Stop\n\n\n"
              "def run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):\n"
              "    raise RuntimeError('synthetic supervisor; never called')\n")
        write(source + "/ontokin/__init__.py", '"""synthetic"""\n')
        write(source + "/tests/test_synthetic.py", "# synthetic\n")
        write(source + "/tools/static_tray_reader_v01/reader.mjs", "// synthetic\n")
        for rel in observation.SOURCE_FILES:
            if rel == observation.MACOS_LOCK:
                write(source + "/" + rel, (REPOSITORY / rel).read_bytes())
            elif rel != observation.EXTERNAL_INPUTS:
                write(source + "/" + rel, "synthetic " + rel + "\n")
        write(source + "/.git/HEAD", "ref: refs/heads/main\n")
        write(source + "/.git/refs/heads/main", self.commit + "\n")

    def build_runtime(self):
        Path(self.runtime + "/bin").mkdir(parents=True)
        os.chmod(self.runtime, 0o755)
        os.chmod(self.runtime + "/bin", 0o755)
        self.node_bytes = macho("MH_EXECUTE", node_commands())
        write(self.runtime + "/bin/node", self.node_bytes, 0o755)
        self.refresh_runtime()

    def node_members(self):
        root = "node-v24.22.1-darwin-arm64"
        return {root: {"kind": "directory", "size_bytes": 0, "mode": "0o755", "link_target": None},
                root + "/bin/node": {"kind": "file", "size_bytes": len(Path(self.runtime + "/bin/node").read_bytes()),
                                     "mode": "0o755", "link_target": None},
                root + "/bin/npm": {"kind": "symlink", "size_bytes": 0, "mode": "0o755",
                                    "link_target": "../lib/node_modules/npm/bin/npm-cli.js"}}

    def refresh_runtime(self, signature="not_performed", plan_changes=None, **result_changes):
        """NODE-SOURCE.json and the synthetic preparer documents, consistent with the runtime's bytes."""
        signature_check = {"status": signature, "detail": "synthetic: no release key consulted"}
        self.write_node_source(self.node_source_value(signature_check=signature_check))
        files = {"bin/node": binding(self.runtime + "/bin/node"),
                 observation.NODE_SOURCE_NAME: binding(self.runtime + "/" + observation.NODE_SOURCE_NAME)}
        self.runtime_install = self.install(self.runtime, "runtime", "selected-node", self.node_archive, files,
                                            {"bin": "0o755"}, self.node_members(),
                                            {"signature_check": signature_check}, plan_changes, **result_changes)

    def node_source_value(self, executable=None, signature_check=None):
        executable = executable or binding(self.runtime + "/bin/node")
        members = json.dumps(self.node_members(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return {"schema": observation.NODE_SOURCE_SCHEMA, "contract": observation.CONTRACT,
                "archive": {"name": observation.NODE_ARCHIVE, "sha256": observation.NODE_ARCHIVE_SHA256,
                            "size_bytes": binding(self.node_archive)["size_bytes"]},
                "checksum_file": dict(observation.NODE_CHECKSUM_FILE),
                "signature_check": signature_check or {"status": "not_performed",
                                                       "detail": "synthetic: no release key consulted"},
                "member_inventory_sha256": hashlib.sha256(members).hexdigest(),
                "extracted": {"member": observation.NODE_MEMBER, "path": "bin/node", **executable}}

    def write_node_source(self, value=None, raw=None):
        path = self.runtime + "/" + observation.NODE_SOURCE_NAME
        if os.path.lexists(path):
            os.unlink(path)
        value = value or self.node_source_value()
        data = raw if raw is not None else json.dumps(value, sort_keys=True, separators=(",", ":"),
                                                      ensure_ascii=False).encode("ascii")
        write(path, data)

    def install(self, destination, name, purpose, archive_file, files, directories, members, node_source,
                plan_changes=None, **result_changes):
        """Synthetic preparer documents in the shapes of W2's interface note; no preparer runs."""
        self.counter += 1
        result_path = "%s/%02d-%s-install-result.json" % (self.receipts, self.counter, name)
        plan = {"schema": observation.INSTALL_SCHEMA, "contract": observation.CONTRACT, "purpose": purpose,
                "source_root": self.source, "archive": descriptor(archive_file), "destination": destination,
                "root_mode": "0o755", "files": files, "directories": directories, "members": members,
                "node_source": node_source, "report": result_path, **(plan_changes or {})}
        plan_path = write("%s/%02d-%s-install-plan.json" % (self.receipts, self.counter, name), canonical(plan))
        member_bytes = json.dumps(members, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        revision = {"contract": observation.CONTRACT, "design_revision": 4, "amendments": ["P33-AMENDMENT-001"]}
        pins = ({"origin": "adopted-contract", "node_archive_sha256": observation.NODE_ARCHIVE_SHA256,
                 "node_executable": files["bin/node"]} if purpose == "selected-node" else
                {"origin": "adopted-contract", "dependency_archive_sha256": observation.DEPENDENCY_ARCHIVE_SHA256})
        summary = {"sha256": binding(archive_file)["sha256"], "size_bytes": binding(archive_file)["size_bytes"],
                   "members": len(members), "expanded_bytes": sum(row["size_bytes"] for row in members.values()),
                   "symlinks": sum(row["kind"] == "symlink" for row in members.values()),
                   "member_inventory_sha256": hashlib.sha256(member_bytes).hexdigest(), "extracted_members": 1}
        if purpose == "selected-node":
            summary["executable"] = {"member": observation.NODE_MEMBER, "path": "bin/node", **files["bin/node"],
                                     "macho": {"magic": "0xfeedfacf", "cputype": "0x0100000c", "cpusubtype": "0x00000000",
                                               "filetype": "MH_EXECUTE"}}
        result = {"schema": observation.INSTALL_RESULT_SCHEMA, **revision, "purpose": purpose,
                  "passed": True, "state": "INSTALLED_EXACT", "apply_requested": True,
                  "execution_counts": {"node": 0, "ldd": 0, "checkers": 0},
                  "operations": [{"operation": "created_owned_stage", "path": destination + ".stage", "device": 1,
                                  "inode": 2}, {"operation": "removed_owned_stage", "path": destination + ".stage"}],
                  "pins": {"origin": "adopted-contract", "node_archive_sha256": observation.NODE_ARCHIVE_SHA256,
                           "dependency_archive_sha256": observation.DEPENDENCY_ARCHIVE_SHA256},
                  "labels": {"executor": "macos-arm64-local", **revision, "profile": "darwin-arm64-v1", "pins": pins,
                             "os": dict(OS_LABEL)},
                  "preparer_source": {"root": self.source, "files_at_start": {}}, "archive": summary,
                  "before": {"state": "absent"},
                  "after": {"state": "complete_exact", "files": files, "directories": directories},
                  "publication": {"call": "renamex_np", "library": "/usr/lib/libSystem.B.dylib", "flag": "RENAME_EXCL",
                                  "flag_value": 4}}
        result.update(result_changes)
        result = {key: value for key, value in result.items() if value is not REMOVED}
        write(result_path, canonical(result))
        return {"plan": descriptor(plan_path), "result": descriptor(result_path)}

    def build_dependencies(self):
        names = ["validator/package/package.json", "indexer-view/three/package.json", "tools/three_loader.mjs"]
        names += ["validator/package/file%02d.js" % index for index in range(10)]
        names += ["indexer-view/three/build/file%02d.js" % index for index in range(11)]
        self.dependency_names = names
        manifest = {"dependencies_root": "/synthetic/receiving", "files": {}}
        for name in names:
            data = (json.dumps({"version": "2.0.0-dev.3.10"}) if name.startswith("validator/package/package") else
                    json.dumps({"version": "0.186.1"}) if name.startswith("indexer-view/three/package") else
                    "// synthetic " + name + "\n").encode()
            write(self.dependencies + "/" + name, data)
            manifest["files"]["/synthetic/receiving/" + name] = {"sha256": hashlib.sha256(data).hexdigest(),
                                                                 "size_bytes": len(data)}
        for directory in sorted({str(Path(self.dependencies + "/" + name).parent) for name in names}):
            path = Path(directory)
            while str(path) != self.dependencies:
                os.chmod(path, 0o755)
                path = path.parent
        write(self.source + "/" + observation.EXTERNAL_INPUTS, json.dumps(manifest, indent=1))
        os.chmod(self.dependencies, 0o755)
        inventory = self.dependency_inventory()
        members = {"receiving/" + name: {"kind": "file", "size_bytes": row["size_bytes"], "sha256": row["sha256"],
                                         "mode": "0o644", "target": name} for name, row in inventory["files"].items()}
        self.dependency_members = members
        self.refresh_dependencies()

    def refresh_dependencies(self, plan_changes=None, **result_changes):
        inventory = self.dependency_inventory()
        self.dependency_install = self.install(self.dependencies, "reader", "retained-dependencies", self.archive,
                                               inventory["files"], inventory["directories"], self.dependency_members,
                                               None, plan_changes, **result_changes)

    def build_host_files(self):
        write(self.git, "#!/bin/sh\necho 'git version 2.0.0 (synthetic)'\n", 0o755)
        write(self.dispatcher, "#!/bin/sh\necho 'synthetic dispatcher'\n", 0o755)
        identity = {"ProductName": "macOS", "ProductVersion": "26.6.2", "ProductBuildVersion": "25G83",
                    "ProductCopyright": "synthetic", "BuildID": "synthetic"}
        write(self.system_plist, plistlib.dumps(identity), 0o444)
        write(self.cryptex_canonical, plistlib.dumps(identity), 0o444)
        link(self.base + "/os/System/Cryptexes/OS", "../../System/Volumes/Preboot/Cryptexes/OS")
        Path(self.evidence).mkdir()
        self.procedure = write(self.base + "/procedure/FAILURE-CAPTURE.md", "synthetic approved capture procedure\n")

    # -- frozen documents and the plan -----------------------------------------
    def frozen(self, name, value):
        self.counter += 1
        path = "%s/frozen/%02d-%s" % (self.base, self.counter, name)
        Path(path).parent.mkdir(exist_ok=True)
        return observation.write_new(path, value)

    def dependency_inventory(self):
        files = {name: binding(self.dependencies + "/" + name) for name in self.dependency_names}
        directories = {}
        for name in self.dependency_names:
            parts = name.split("/")[:-1]
            for index in range(1, len(parts) + 1):
                rel = "/".join(parts[:index])
                directories[rel] = "0o%03o" % stat.S_IMODE(os.lstat(self.dependencies + "/" + rel).st_mode)
        return {"schema": observation.DEPENDENCIES_SCHEMA, "files": files, "directories": directories,
                "archive": descriptor(self.archive)}

    def plan(self, **changes):
        source_inventory = self.frozen("source.json", observation.source_inventory(self.source))
        python_inventory = self.frozen("python.json", observation.python_inventory(self.venv, self.framework))
        dependency_inventory = self.frozen("dependencies.json", self.dependency_inventory())
        plan = {
            "schema": observation.PLAN_SCHEMA, "contract": observation.CONTRACT, "profile": observation.PROFILE,
            "executor": observation.EXECUTOR, "environment": dict(observation.ENVIRONMENT),
            "platform": {"system": "Darwin", "release": "25.6.0", "machine": "arm64", "proc_translated": 0,
                         "boot_session_uuid": BOOT},
            "os": {"system_version": descriptor(self.system_plist),
                   "cryptex": {"state": "present", **descriptor(self.cryptex_canonical)}},
            "source": {"root": self.source, "commit": self.commit, "tree": self.tree, "inventory": source_inventory},
            "observer": descriptor(self.observer),
            "python": {"venv": self.venv, "framework": self.framework, "version": "3.12.13",
                       "inventory": python_inventory},
            "runtime": {"directory": self.runtime, "version": "v24.22.1", "root_mode": "0o755", "bin_mode": "0o755",
                        "executable": binding(self.runtime + "/bin/node"),
                        "node_source": binding(self.runtime + "/" + observation.NODE_SOURCE_NAME),
                        "archive": descriptor(self.node_archive), "install": self.runtime_install},
            "dependencies": {"root": self.dependencies, "inventory": dependency_inventory,
                             "install": self.dependency_install},
            "git": descriptor(self.git),
            "commands": [],
            "evidence": {"parent": self.evidence, "ancestors": observation._ancestors(self.evidence),
                         "attempt": self.attempt, "outputs": observation.output_paths(self.attempt)},
            "failure_capture": {"procedure": descriptor(self.procedure)},
            "limits": dict(observation.LIMITS)}
        plan["commands"] = observation.expected_commands(plan)
        for key, value in changes.items():
            plan[key] = value
        return plan

    def write_plan(self, plan):
        self.counter += 1
        path = "%s/plan-%02d.json" % (self.base, self.counter)
        raw = canonical(plan)
        write(path, raw)
        return path, hashlib.sha256(raw).hexdigest()


def needs_darwin(test):
    return unittest.skipUnless(DARWIN, "renamex_np and the Darwin layout exist only on macOS")(test)


class RefusalMixin:
    def refused(self, category, rule=None, callable_=None, *args, **kwargs):
        with self.assertRaises(observation.ObservationError) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(caught.exception.code, "CHO-" + category, caught.exception.as_dict())
        if rule is not None:
            self.assertEqual(caught.exception.details.get("rule"), rule, caught.exception.as_dict())
        return caught.exception


# ---------------------------------------------------------------------------
# Mach-O parser: MC05 (Mach-O part) and MC06
# ---------------------------------------------------------------------------

class MachOParserTests(RefusalMixin, unittest.TestCase):
    """Pure parsing of synthetic bytes; no file system and no start."""

    def test_mc05_thin_arm64_executable_is_accepted(self):
        summary = parse(macho())
        self.assertEqual((summary["magic"], summary["cputype"], summary["cpusubtype"], summary["filetype"]),
                         ("MH_MAGIC_64", "0x0100000c", "0x00000000", "MH_EXECUTE"))
        rules = observation.check_node_macho(summary)
        self.assertEqual(rules["references"], ["/usr/lib/libSystem.B.dylib",
                         "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation",
                         "/usr/lib/libc++.1.dylib"])
        names = [row["name"] for row in summary["commands"]]
        self.assertTrue(set(names) <= observation.NODE_ALLOWED_COMMANDS)
        uuid = [row for row in summary["commands"] if row["name"] == "LC_UUID"][0]["uuid"]
        self.assertEqual(uuid, "00010203-0405-0607-0809-0A0B0C0D0E0F")
        version = [row for row in summary["commands"] if row["name"] == "LC_BUILD_VERSION"][0]
        self.assertEqual((version["minos"], version["sdk"], version["tools"]), ("14.0.0", "15.5.0",
                         [{"tool": 3, "version": "1024.0.0"}]))

    def test_mc05_dyld_info_only_is_in_the_allow_list(self):
        observation.check_node_macho(parse(macho(commands=node_commands(lc_named("LC_DYLD_INFO_ONLY", b"\0" * 40)))))

    def test_mc05_fat_header_is_refused(self):
        self.refused("MACHO", "MACHO-FAT", parse, fat(macho()))
        self.refused("MACHO", "MACHO-FAT", parse, struct.pack(">II", 0xCAFEBABF, 1) + b"\0" * 64)

    def test_mc05_other_magic_is_refused(self):
        self.refused("MACHO", "MACHO-MAGIC", parse, macho(magic=0xFEEDFACE))
        self.refused("MACHO", "MACHO-MAGIC", parse, macho(magic=0xCFFAEDFE))
        self.refused("MACHO", "MACHO-MAGIC", parse, b"#!/bin/sh\n" + b"\0" * 64)

    def test_mc05_other_cpu_or_subtype_is_refused(self):
        self.refused("MACHO", "MACHO-CPU", parse, macho(cputype=0x01000007))
        self.refused("MACHO", "MACHO-CPU", parse, macho(cpusubtype=2))
        self.refused("MACHO", "MACHO-CPU", parse, macho(cpusubtype=0x80000000))

    def test_mc05_node_must_be_an_executable(self):
        summary = parse(dylib_image("/usr/lib/libx.dylib"))
        self.refused("MACHO", "MACHO-FILETYPE", observation.check_node_macho, summary)

    def test_malformed_tables_are_refused(self):
        good = macho()
        self.refused("MACHO", "MACHO-MALFORMED", parse, good[:20])
        self.refused("MACHO", "MACHO-MALFORMED", parse, macho(sizeofcmds=10 ** 6, pad=0))
        self.refused("MACHO", "MACHO-MALFORMED", parse, macho(ncmds=0))
        self.refused("MACHO", "MACHO-MALFORMED", parse, macho(ncmds=5))
        bad_size = struct.pack("<II", LC["LC_UUID"], 20) + b"\0" * 12
        self.refused("MACHO", "MACHO-MALFORMED", parse, macho(commands=[bad_size] + node_commands()[1:]))
        unterminated = struct.pack("<III", LC["LC_LOAD_DYLINKER"], 24, 12) + b"/usr/lib/dyldX"[:12]
        self.refused("MACHO", "MACHO-MALFORMED", parse, macho(commands=[unterminated]))
        escaping = segment("__TEXT", 0, 10 ** 9)
        self.refused("MACHO", "MACHO-MALFORMED", parse, macho(commands=[escaping]))
        sections = struct.pack("<II", LC["LC_SEGMENT_64"], 72) + b"__TEXT".ljust(16, b"\0") + struct.pack(
            "<QQQQiiII", 0, 0, 0, 0, 5, 5, 1, 0)
        self.refused("MACHO", "MACHO-MALFORMED", parse, macho(commands=[sections]))

    def test_mc06_refused_commands_for_node(self):
        for command in (lc_path("LC_RPATH", "/usr/lib"), lc_path("LC_DYLD_ENVIRONMENT", "DYLD_X=1"),
                        dylib("LC_LOAD_UPWARD_DYLIB", "/usr/lib/libx.dylib"),
                        dylib("LC_REEXPORT_DYLIB", "/usr/lib/libx.dylib")):
            with self.subTest(command=struct.unpack_from("<I", command)[0]):
                summary = parse(macho(commands=node_commands(command)))
                self.refused("MACHO", "MACHO-REFUSED-COMMAND", observation.check_node_macho, summary)

    def test_mc06_unknown_and_unlisted_commands_for_node(self):
        for command in (lc(0x99, b"\0" * 8), lc(0x37, b"\0" * 8), dylib("LC_ID_DYLIB", "/usr/lib/libnode.dylib"),
                        lc_named("LC_VERSION_MIN_MACOSX", b"\0" * 8), lc_named("LC_UNIXTHREAD", b"\0" * 16),
                        dylib("LC_LAZY_LOAD_DYLIB", "/usr/lib/libx.dylib"), lc_named("LC_ATOM_INFO", b"\0" * 8)):
            with self.subTest(command=struct.unpack_from("<I", command)[0]):
                summary = parse(macho(commands=node_commands(command)))
                self.refused("MACHO", "MACHO-COMMAND", observation.check_node_macho, summary)

    def test_mc06_dylinker_must_be_usr_lib_dyld(self):
        for path in ("/usr/lib/dyld2", "/tmp/dyld", "@loader_path/dyld"):
            summary = parse(macho(commands=node_commands(dylinker=path)))
            self.refused("MACHO", "MACHO-DYLINKER", observation.check_node_macho, summary)

    def test_mc06_dylib_outside_system_prefixes(self):
        for path in ("/opt/example/lib/libuv.dylib", "/usr/local/lib/libx.dylib", "/usr/lib/../../opt/x.dylib",
                     "/usr/libx.dylib", "/System/LibraryX/x.dylib", "libx.dylib", "//usr/lib/libx.dylib",
                     "/usr/lib/./libx.dylib"):
            for command in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB"):
                with self.subTest(path=path, command=command):
                    summary = parse(macho(commands=node_commands(dylib(command, path))))
                    self.refused("MACHO", "MACHO-DYLIB-PATH", observation.check_node_macho, summary)

    def test_mc06_at_relative_references_for_node(self):
        for path in ("@rpath/libnode.dylib", "@loader_path/libx.dylib", "@executable_path/../lib/x.dylib",
                     "@other/x.dylib"):
            with self.subTest(path=path):
                summary = parse(macho(commands=node_commands(dylib("LC_LOAD_WEAK_DYLIB", path))))
                self.refused("MACHO", "MACHO-AT-PATH", observation.check_node_macho, summary)

    def test_single_commands_and_entry_structure(self):
        summary = parse(macho(commands=node_commands(main_command())))
        self.refused("MACHO", "MACHO-DUPLICATE", observation.check_node_macho, summary)
        commands = [row for row in node_commands() if struct.unpack_from("<I", row)[0] != LC["LC_MAIN"]]
        self.refused("MACHO", "MACHO-STRUCTURE", observation.check_node_macho, parse(macho(commands=commands)))

    def test_python_rules_accept_executable_dylib_and_bundle(self):
        image = dylib_image("@rpath/libx.dylib", "/usr/lib/libSystem.B.dylib", "@loader_path/../lib/liby.dylib",
                            rpaths=("@loader_path/../lib", "/opt/x/lib"))
        rules = observation.check_python_macho(parse(image))
        self.assertEqual((rules["filetype"], rules["id"], rules["rpaths"]),
                         ("MH_DYLIB", "@rpath/libx.dylib", ["@loader_path/../lib", "/opt/x/lib"]))
        self.assertEqual([row["path"] for row in rules["references"]],
                         ["/usr/lib/libSystem.B.dylib", "@loader_path/../lib/liby.dylib"])
        observation.check_python_macho(parse(bundle_image("/opt/x/lib/libz.dylib")))
        observation.check_python_macho(parse(executable_image("/opt/x/Python", rpaths=("/opt/x/lib",))))

    def test_python_rules_refuse_other_file_types(self):
        for filetype in ("MH_OBJECT", "MH_DYLINKER"):
            summary = parse(macho(filetype, common_commands() + tail_commands()))
            self.refused("MACHO", "MACHO-FILETYPE", observation.check_python_macho, summary)

    def test_python_rules_refuse_environment_upward_reexport_and_unknown(self):
        cases = ((lc_path("LC_DYLD_ENVIRONMENT", "DYLD_X=1"), "MACHO-REFUSED-COMMAND"),
                 (dylib("LC_LOAD_UPWARD_DYLIB", "/usr/lib/libx.dylib"), "MACHO-REFUSED-COMMAND"),
                 (dylib("LC_REEXPORT_DYLIB", "/usr/lib/libx.dylib"), "MACHO-COMMAND"),
                 (lc(0x99, b"\0" * 8), "MACHO-COMMAND"))
        for command, rule in cases:
            with self.subTest(rule=rule):
                image = macho("MH_BUNDLE", common_commands() + [command] + tail_commands())
                self.refused("MACHO", rule, observation.check_python_macho, parse(image))

    def test_python_rules_refuse_unsupported_paths(self):
        cases = (("@other/libx.dylib", "MACHO-AT-PATH"), ("@rpath", "MACHO-AT-PATH"), ("libx.dylib", "MACHO-DYLIB-PATH"),
                 ("/opt/x/../y/libx.dylib", "MACHO-DYLIB-PATH"))
        for path, rule in cases:
            with self.subTest(path=path):
                self.refused("MACHO", rule, observation.check_python_macho, parse(bundle_image(path)))
        for rpath in ("@rpath/x", "lib", "/opt/x/../lib"):
            with self.subTest(rpath=rpath):
                self.refused("MACHO", "MACHO-RPATH", observation.check_python_macho,
                             parse(bundle_image(rpaths=(rpath,))))

    def test_python_dylib_needs_one_identity_and_no_entry_point(self):
        image = macho("MH_DYLIB", common_commands() + tail_commands())
        self.refused("MACHO", "MACHO-STRUCTURE", observation.check_python_macho, parse(image))
        image = macho("MH_BUNDLE", common_commands() + [main_command()] + tail_commands())
        self.refused("MACHO", "MACHO-STRUCTURE", observation.check_python_macho, parse(image))

    def test_read_macho_binds_the_file_it_parses(self):
        base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, base, True)
        path = write(base + "/node", macho(), 0o755)
        bound, summary = observation.read_macho(os.path.realpath(path), maximum=10 ** 6)
        self.assertEqual(bound, binding(os.path.realpath(path)))
        self.assertEqual(summary["filetype"], "MH_EXECUTE")
        fat_path = write(base + "/fat", fat(macho()), 0o755)
        error = self.refused("MACHO", "MACHO-FAT", observation.read_macho, os.path.realpath(fat_path), maximum=10 ** 6)
        self.assertEqual(error.details["path"], os.path.realpath(fat_path))


# ---------------------------------------------------------------------------
# Canonical paths: MC20
# ---------------------------------------------------------------------------

class CanonicalPathTests(RefusalMixin, unittest.TestCase):
    """Synthetic directories and links under the resolved temporary directory."""

    def setUp(self):
        self.base = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base, True)
        os.makedirs(self.base + "/real/inner")
        write(self.base + "/real/inner/file", "x")

    def test_mc20_canonical_path_is_returned_unchanged(self):
        path = self.base + "/real/inner/file"
        self.assertEqual(observation.canonical_path(path), path)
        self.assertEqual(observation.canonical_path(self.base + "/real/absent", allow_absent=True),
                         self.base + "/real/absent")

    @unittest.skipUnless(DARWIN and tempfile.gettempdir().startswith("/private/var/"), "needs /var -> /private/var")
    def test_mc20_system_link_ancestor_is_admitted_and_resolved(self):
        spelled = self.base[len("/private"):] + "/real/inner/file"
        self.assertTrue(spelled.startswith("/var/"))
        self.assertEqual(observation.canonical_path(spelled), self.base + "/real/inner/file")
        with self.assertRaises(observation.ObservationError):
            observation._canonical_value(spelled, "PATH")

    def test_mc20_other_symlinked_ancestor_is_refused(self):
        os.symlink(self.base + "/real", self.base + "/alias")
        self.refused("PATH", "PATH-SYMLINK", observation.canonical_path, self.base + "/alias/inner/file")
        self.refused("PATH", "PATH-SYMLINK", observation.canonical_path, self.base + "/alias/absent", allow_absent=True)

    def test_mc20_symbolic_link_itself_is_refused(self):
        os.symlink("inner/file", self.base + "/real/link")
        self.refused("PATH", "PATH-SYMLINK", observation.canonical_path, self.base + "/real/link")

    def test_non_normalized_or_missing_paths_are_refused(self):
        for value in ("relative/x", self.base + "/real/../real", self.base + "//real", self.base + "/real/",
                      self.base + "/./real", "", 3):
            with self.subTest(value=value):
                with self.assertRaises(observation.ObservationError):
                    observation.canonical_path(value)
        self.refused("PATH", None, observation.canonical_path, self.base + "/real/absent")
        self.refused("PATH", None, observation.canonical_path, self.base + "/missing/absent", allow_absent=True)
        self.refused("PATH", None, observation.canonical_path, self.base + "/real/inner/file/below")


# ---------------------------------------------------------------------------
# Environment predicate: MC07, MC30 (M0 side) and MC31
# ---------------------------------------------------------------------------

class EnvironmentTests(RefusalMixin, unittest.TestCase):
    """Synthetic mappings only; values never appear in a refusal."""
    declared = dict(observation.ENVIRONMENT)

    def test_mc30_mc31_predicate_truth_table(self):
        admitted = observation.environment_admitted
        cf = observation.CF_NAME
        self.assertTrue(admitted(self.declared, self.declared, None))
        self.assertTrue(admitted(self.declared, self.declared, CF_VALUE))
        self.assertTrue(admitted({**self.declared, cf: CF_VALUE}, self.declared, CF_VALUE))
        self.assertFalse(admitted({**self.declared, cf: CF_VALUE}, self.declared, None))
        self.assertFalse(admitted({**self.declared, cf: CF_VALUE}, self.declared, "0x0:0x0:0x0"))
        self.assertFalse(admitted({**self.declared, cf: ""}, self.declared, ""))
        self.assertFalse(admitted({**self.declared, "EXTRA": "1"}, self.declared, CF_VALUE))
        self.assertFalse(admitted({**self.declared, cf: CF_VALUE}, {**self.declared, cf: CF_VALUE}, CF_VALUE))
        missing = dict(self.declared)
        del missing["TZ"]
        self.assertFalse(admitted(missing, self.declared, None))
        self.assertFalse(admitted({**self.declared, "TZ": "EST"}, self.declared, None))
        self.assertFalse(admitted(None, self.declared, None))
        self.assertFalse(admitted({**self.declared, "N": 1}, self.declared, None))

    def test_mc07_each_forbidden_variable_is_refused(self):
        names = ("DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH", "DYLD_FALLBACK_LIBRARY_PATH",
                 "DYLD_PRINT_LIBRARIES", "DYLD_IMAGE_SUFFIX", "__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE",
                 "NODE_OPTIONS", "NODE_PATH", "NODE_EXTRA_CA_CERTS", "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP",
                 "PYTHONINSPECT", "PYTHONBREAKPOINT", "PYTHONUSERBASE", "PYTHONPYCACHEPREFIX", "PYTHONSAFEPATH",
                 "LD_PRELOAD", "LD_LIBRARY_PATH")
        for name in names:
            for cf in ({}, {observation.CF_NAME: CF_VALUE}):
                with self.subTest(name=name, cf=bool(cf)):
                    observed = {**self.declared, **cf, name: "secret-value"}
                    error = self.refused("ENVIRONMENT", "ENVIRONMENT-EXACT", observation.check_environment, observed,
                                         self.declared)
                    self.assertEqual(error.details["forbidden"], [name])
                    self.assertNotIn("secret-value", json.dumps(error.as_dict()))

    def test_mc30_m0_admits_declared_with_and_without_cf(self):
        """The case without the variable is a simulated boundary (labelled mocked in M0 records)."""
        self.assertIsNone(observation.check_environment(self.declared, self.declared))
        self.assertEqual(observation.check_environment({**self.declared, observation.CF_NAME: CF_VALUE},
                                                       self.declared), CF_VALUE)

    def test_mc31_extra_variable_or_empty_cf_is_refused(self):
        error = self.refused("ENVIRONMENT", "ENVIRONMENT-EXACT", observation.check_environment,
                             {**self.declared, "HOME": "/x"}, self.declared)
        self.assertEqual((error.details["extra"], error.details["forbidden"]), (["HOME"], []))
        error = self.refused("ENVIRONMENT", "ENVIRONMENT-EXACT", observation.check_environment,
                             {**self.declared, observation.CF_NAME: ""}, self.declared)
        self.assertEqual(error.details["cf_user_text_encoding"], "empty")
        changed = {**self.declared, "LANG": "en_US.UTF-8"}
        error = self.refused("ENVIRONMENT", "ENVIRONMENT-EXACT", observation.check_environment, changed, self.declared)
        self.assertEqual(error.details["differing"], ["LANG"])


# ---------------------------------------------------------------------------
# Platform, translation and boot: MC08 (mocked readers)
# ---------------------------------------------------------------------------

class PlatformTests(RefusalMixin, unittest.TestCase):
    planned = {"system": "Darwin", "release": "25.6.0", "machine": "arm64", "proc_translated": 0,
               "boot_session_uuid": BOOT}

    def observed(self, **changes):
        return {"system": "Darwin", "release": "25.6.0", "version": "synthetic", "machine": "arm64",
                "proc_translated": 0, "boot_session_uuid": BOOT, **changes}

    def test_mc08_translated_other_machine_or_system_is_refused(self):
        """Simulated at the reader boundary: the values are synthetic, labelled mocked."""
        observation.check_platform(self.observed(), self.planned)
        for changes, rule in (({"proc_translated": 1}, "PLATFORM-TRANSLATED"), ({"machine": "x86_64"}, "PLATFORM-MACHINE"),
                              ({"system": "Linux"}, "PLATFORM-SYSTEM"), ({"release": "25.7.0"}, "PLATFORM-RELEASE"),
                              ({"boot_session_uuid": BOOT.replace("0A", "0B")}, "PLATFORM-BOOT_SESSION_UUID")):
            with self.subTest(rule=rule):
                self.refused("PLATFORM", rule, observation.check_platform, self.observed(**changes), self.planned)

    @unittest.skipUnless(DARWIN, "sysctlbyname and proc_pidpath exist only on macOS")
    def test_real_readers_return_their_shapes(self):
        """Reads this host's sysctl values and its own process image; asserts only types and shapes."""
        self.assertIn(observation.read_proc_translated(), (0, 1))
        self.assertRegex(observation.read_boot_session_uuid(), observation.UUID_TEXT)
        self.assertTrue(os.path.isabs(observation.read_process_image()))


# ---------------------------------------------------------------------------
# OS identity with and without the cryptex copy
# ---------------------------------------------------------------------------

class OSIdentityTests(RefusalMixin, unittest.TestCase):
    def setUp(self):
        self.base = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base, True)
        self.values = {"ProductName": "macOS", "ProductVersion": "26.6.2", "ProductBuildVersion": "25G83"}
        self.system = write(self.base + "/system/SystemVersion.plist", plistlib.dumps(self.values))
        self.cryptex = self.base + "/cryptex/OS/SystemVersion.plist"

    def test_identity_with_the_cryptex_copy(self):
        write(self.cryptex, plistlib.dumps({**self.values, "ProductVersionExtra": "(a)"}, fmt=plistlib.FMT_BINARY))
        identity = observation.read_os_identity(system_path=self.system, cryptex_path=self.cryptex)
        self.assertEqual(identity["system_version"]["product_build_version"], "25G83")
        self.assertIsNone(identity["system_version"]["product_version_extra"])
        self.assertEqual((identity["cryptex"]["state"], identity["cryptex"]["product_version_extra"]), ("present", "(a)"))
        self.assertEqual(_without(identity["cryptex"], "state", "product_name", "product_version",
                                  "product_build_version", "product_version_extra", "link_path", "hops"),
                         descriptor(self.cryptex))
        self.assertEqual((identity["cryptex"]["link_path"], identity["cryptex"]["hops"]), (self.cryptex, []))
        label = observation._os_label(identity)
        self.assertEqual(label["cryptex"], {"state": "present", "product_version": "26.6.2",
                                            "product_build_version": "25G83", "product_version_extra": "(a)"})

    def test_cryptex_copy_behind_the_conventional_link_is_bound_canonically(self):
        """The macOS 26 layout: System/Cryptexes/OS -> ../../System/Volumes/Preboot/Cryptexes/OS (synthetic)."""
        canonical = write(self.base + "/System/Volumes/Preboot/Cryptexes/OS/SystemVersion.plist",
                          plistlib.dumps(self.values))
        link(self.base + "/System/Cryptexes/OS", "../../System/Volumes/Preboot/Cryptexes/OS")
        conventional = self.base + "/System/Cryptexes/OS/SystemVersion.plist"
        identity = observation.read_os_identity(system_path=self.system, cryptex_path=conventional)
        self.assertEqual((identity["cryptex"]["path"], identity["cryptex"]["link_path"]), (canonical, conventional))
        self.assertEqual(identity["cryptex"]["hops"], [{"path": self.base + "/System/Cryptexes/OS",
                                                        "target": "../../System/Volumes/Preboot/Cryptexes/OS"}])
        self.refused("PATH", "PATH-SYMLINK", observation.canonical_path, conventional)

    def test_identity_without_the_cryptex_copy(self):
        identity = observation.read_os_identity(system_path=self.system, cryptex_path=self.cryptex)
        self.assertEqual(identity["cryptex"], {"state": "absent", "path": self.cryptex, "hops": []})
        self.assertEqual(observation._os_label(identity)["cryptex"], {"state": "absent"})
        os.makedirs(self.base + "/cryptex/OS")
        identity = observation.read_os_identity(system_path=self.system, cryptex_path=self.cryptex)
        self.assertEqual(identity["cryptex"]["state"], "absent")
        os.makedirs(self.base + "/real")
        os.symlink(self.base + "/real", self.base + "/alias")
        identity = observation.read_os_identity(system_path=self.system,
                                                cryptex_path=self.base + "/alias/SystemVersion.plist")
        self.assertEqual(identity["cryptex"]["hops"], [{"path": self.base + "/alias", "target": self.base + "/real"}])

    def test_os_label_state_matches_the_code_and_the_preparer(self):
        """Correction W3-C3: a present cryptex label carries state "present" beside the three fields."""
        write(self.cryptex, plistlib.dumps(self.values))
        label = observation._os_label(observation.read_os_identity(system_path=self.system, cryptex_path=self.cryptex))
        self.assertEqual(label["cryptex"], {"state": "present", "product_version": "26.6.2",
                                            "product_build_version": "25G83", "product_version_extra": None})
        self.assertTrue(observation.check_os_label(label))
        self.assertTrue(observation.check_os_label(dict(label, cryptex={"state": "absent"})))
        without_state = {key: value for key, value in label["cryptex"].items() if key != "state"}
        for value in (dict(label, cryptex=without_state), dict(label, cryptex={"state": "absent", "product_version": "x"}),
                      dict(label, cryptex={"state": "unknown"}), dict(label, extra=1), None,
                      dict(label, product_version="")):
            with self.subTest(value=value):
                self.assertFalse(observation.check_os_label(value))

    def test_identity_refusals(self):
        os.symlink(self.system, self.base + "/linked.plist")
        self.refused("OS", "OS-PATH", observation.read_os_identity, system_path=self.base + "/linked.plist",
                     cryptex_path=self.cryptex)
        self.refused("OS", "OS-PATH", observation.read_os_identity, system_path=self.base + "/missing.plist",
                     cryptex_path=self.cryptex)
        partial = write(self.base + "/partial.plist", plistlib.dumps({"ProductName": "macOS", "ProductVersion": "26"}))
        self.refused("OS", None, observation.read_os_identity, system_path=partial, cryptex_path=self.cryptex)
        garbage = write(self.base + "/garbage.plist", b"not a property list")
        self.refused("OS", None, observation.read_os_identity, system_path=garbage, cryptex_path=self.cryptex)
        os.makedirs(self.cryptex)
        self.refused("OS", "OS-CRYPTEX", observation.read_os_identity, system_path=self.system,
                     cryptex_path=self.cryptex)


def _without(row, *keys):
    return {key: value for key, value in row.items() if key not in keys}


# ---------------------------------------------------------------------------
# Git binding refusals
# ---------------------------------------------------------------------------

class GitBindingTests(RefusalMixin, unittest.TestCase):
    """A fake Git implementation (a shell script that is never executed)."""

    def setUp(self):
        self.base = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base, True)
        self.git = write(self.base + "/tools/bin/git", "#!/bin/sh\necho 'git version 2.0.0'\n", 0o755)
        self.dispatcher = write(self.base + "/usr/bin/git", "#!/bin/sh\necho dispatcher\n", 0o755)

    def test_fake_git_script_is_bound(self):
        bound = observation.check_git_binding(descriptor(self.git), dispatcher=self.dispatcher)
        self.assertEqual(bound, descriptor(self.git))

    def test_usr_bin_git_dispatcher_is_refused(self):
        self.refused("GIT", "GIT-DISPATCHER", observation.check_git_binding, {"path": "/usr/bin/git", **binding(self.git)})
        self.refused("GIT", "GIT-DISPATCHER", observation.check_git_binding, descriptor(self.dispatcher),
                     dispatcher=self.dispatcher)

    def test_symbolic_link_is_refused(self):
        os.symlink(self.git, self.base + "/tools/bin/git-link")
        self.refused("GIT", "GIT-SYMLINK", observation.check_git_binding,
                     {"path": self.base + "/tools/bin/git-link", **binding(self.git)}, dispatcher=self.dispatcher)
        os.symlink(self.base + "/tools", self.base + "/alias")
        self.refused("GIT", "GIT-PATH", observation.check_git_binding,
                     {"path": self.base + "/alias/bin/git", **binding(self.git)}, dispatcher=self.dispatcher)

    def test_digest_mismatch_is_refused(self):
        expected = descriptor(self.git)
        write(self.git, "#!/bin/sh\necho 'git version 9.9.9'\n", 0o755)
        self.refused("GIT", "GIT-DIGEST", observation.check_git_binding, expected, dispatcher=self.dispatcher)
        os.chmod(self.git, 0o700)
        self.refused("GIT", "GIT-DIGEST", observation.check_git_binding, {**descriptor(self.git), "mode": "0o755"},
                     dispatcher=self.dispatcher)
        write(self.git, "#!/bin/sh\necho 'git version 2.0.0 with a longer replacement line'\n", 0o755)
        self.refused("GIT", "GIT-DIGEST", observation.check_git_binding, expected, dispatcher=self.dispatcher)

    def test_dispatcher_hard_link_or_bytes_are_refused(self):
        os.link(self.dispatcher, self.base + "/tools/bin/git-hard")
        self.refused("GIT", "GIT-DISPATCHER", observation.check_git_binding, descriptor(self.base + "/tools/bin/git-hard"),
                     dispatcher=self.dispatcher)
        copy = write(self.base + "/tools/bin/git-copy", Path(self.dispatcher).read_bytes(), 0o755)
        self.refused("GIT", "GIT-DISPATCHER", observation.check_git_binding, descriptor(copy), dispatcher=self.dispatcher)


# ---------------------------------------------------------------------------
# Python installation-tree inventory: MC32 and RECORD verification
# ---------------------------------------------------------------------------

class PythonInventoryTests(RefusalMixin, unittest.TestCase):
    """Synthetic framework, venv and external dependency trees."""

    def setUp(self):
        self.ws = Workspace(self)
        self.frozen = observation.python_inventory(self.ws.venv, self.ws.framework)

    def again(self):
        return observation.python_inventory(self.ws.venv, self.ws.framework)

    def changes(self, actual=None):
        return {(row["part"], row["path"], row["change"]) for row in observation.compare_inventory(
            self.frozen, actual or self.again())}

    def test_inventory_is_exact_and_binds_links_and_dependencies(self):
        self.assertEqual(observation.compare_inventory(self.frozen, self.again()), [])
        self.assertEqual(observation.python_inventory_digest(self.frozen), observation.python_inventory_digest(self.again()))
        prefix, framework = self.ws.prefix, self.ws.framework
        entries = self.frozen["framework"]["entries"]
        self.assertEqual(entries["Headers"], {"kind": "symlink", "target": "include/python3.12"})
        self.assertEqual(entries["lib/python3.12/__pycache__/os.cpython-312.pyc"]["kind"], "file")
        closure = self.frozen["closure"]
        dependency = prefix + "/Cellar/dep/1.0/lib/libdep.1.0.dylib"
        self.assertEqual(sorted(closure["external"]), [dependency])
        self.assertIn({"path": prefix + "/opt/dep", "target": "../Cellar/dep/1.0"}, closure["links"])
        self.assertIn({"path": prefix + "/Cellar/dep/1.0/lib/libdep.1.dylib", "target": "libdep.1.0.dylib"},
                      closure["links"])
        bundle = closure["images"][framework + "/lib/python3.12/lib-dynload/_dep.cpython-312-darwin.so"]
        self.assertEqual([row["kind"] for row in bundle["references"]], ["bound", "system"])
        self.assertEqual(closure["images"][dependency]["rpaths"][0]["state"], "directory")
        self.assertEqual(closure["images"][dependency]["spellings"], [prefix + "/opt/dep/lib/libdep.1.dylib"])
        pil = closure["images"][self.ws.site + "/PIL/_imaging.cpython-312-darwin.so"]
        self.assertEqual(pil["references"][0]["path"], self.ws.site + "/PIL/.dylibs/libsynthetic.1.dylib")
        selection = self.frozen["selection"]
        self.assertEqual(selection["launcher_chain"]["path"], framework + "/bin/python3.12")
        self.assertEqual([hop["path"] for hop in selection["launcher_chain"]["hops"]],
                         [self.ws.venv + "/bin/python", self.ws.venv + "/bin/python3.12", prefix + "/opt/python",
                          prefix + "/Cellar/python/3.12.13/bin/python3.12"])
        self.assertEqual(selection["pyvenv_cfg"]["home"], prefix + "/opt/python/bin")

    def test_mc32_changed_file(self):
        write(self.ws.framework + "/lib/python3.12/os.py", "# changed\n")
        self.assertEqual(self.changes(), {("framework", "lib/python3.12/os.py", "changed")})

    def test_mc32_added_and_missing_files(self):
        write(self.ws.framework + "/lib/python3.12/added.py", "# added\n")
        os.unlink(self.ws.venv + "/bin/activate")
        self.assertEqual(self.changes(), {("framework", "lib/python3.12/added.py", "added"),
                                          ("venv", "bin/activate", "missing")})

    def test_mc32_added_bytecode_file(self):
        write(self.ws.framework + "/lib/python3.12/__pycache__/added.cpython-312.pyc", b"\x00bytecode")
        self.assertEqual(self.changes(), {("framework", "lib/python3.12/__pycache__/added.cpython-312.pyc", "added")})

    def test_mc32_changed_pyvenv_cfg(self):
        path = self.ws.venv + "/pyvenv.cfg"
        write(path, Path(path).read_text() + "prompt = synthetic\n")
        changes = self.changes()
        self.assertIn(("venv", "pyvenv.cfg", "changed"), changes)
        self.assertIn(("selection", "pyvenv_cfg", "changed"), changes)

    def test_mc32_retargeted_link_hop(self):
        prefix = self.ws.prefix
        shutil.copytree(prefix + "/Cellar/dep/1.0", prefix + "/Cellar/dep/2.0", symlinks=True)
        os.unlink(prefix + "/opt/dep")
        os.symlink("../Cellar/dep/2.0", prefix + "/opt/dep")
        changes = self.changes()
        self.assertIn(("links", prefix + "/opt/dep", "added"), changes)
        self.assertIn(("links", prefix + "/opt/dep", "missing"), changes)
        self.assertIn(("external", prefix + "/Cellar/dep/2.0/lib/libdep.1.0.dylib", "added"), changes)

    def test_mc32_retargeted_selection_hop(self):
        os.unlink(self.ws.venv + "/bin/python")
        os.symlink("python3", self.ws.venv + "/bin/python")
        changes = self.changes()
        self.assertIn(("venv", "bin/python", "changed"), changes)
        self.assertIn(("selection", "launcher_chain", "changed"), changes)

    def test_mc32_at_relative_load_that_does_not_resolve(self):
        cases = ((bundle_image("@loader_path/missing.dylib"), "MACHO-AT-UNRESOLVED"),
                 (bundle_image("@rpath/libmissing.dylib"), "MACHO-AT-UNRESOLVED"),
                 (bundle_image("@rpath/libmissing.dylib", rpaths=("@loader_path/nowhere",)), "MACHO-AT-UNRESOLVED"),
                 (bundle_image("@executable_path/../missing.dylib"), "MACHO-AT-UNRESOLVED"),
                 (bundle_image(self.ws.prefix + "/opt/dep/lib/libmissing.dylib"), "MACHO-DEPENDENCY-MISSING"))
        target = self.ws.framework + "/lib/python3.12/lib-dynload/_case.cpython-312-darwin.so"
        for image, rule in cases:
            with self.subTest(rule=rule):
                write(target, image, 0o755)
                self.refused("MACHO", rule, self.again)
        write(target, bundle_image("@loader_path/../os.py"), 0o755)
        self.refused("MACHO", "MACHO-DEPENDENCY-NOT-MACHO", self.again)

    def test_at_relative_loads_that_resolve_are_bound(self):
        framework = self.ws.framework
        write(framework + "/lib/python3.12/lib-dynload/_rpath.cpython-312-darwin.so",
              bundle_image("@rpath/Python", rpaths=("@loader_path/nowhere", "@loader_path/../../..")), 0o755)
        write(framework + "/lib/python3.12/lib-dynload/_exec.cpython-312-darwin.so",
              bundle_image("@executable_path/../../../../Python"), 0o755)
        inventory = self.again()
        image = inventory["closure"]["images"][framework + "/lib/python3.12/lib-dynload/_rpath.cpython-312-darwin.so"]
        self.assertEqual(image["references"][0]["path"], framework + "/Python")
        self.assertEqual([row["state"] for row in image["references"][0]["candidates"]], ["absent", "file"])
        image = inventory["closure"]["images"][framework + "/lib/python3.12/lib-dynload/_exec.cpython-312-darwin.so"]
        self.assertEqual(image["references"][0]["path"], framework + "/Python")

    def test_fat_or_foreign_files_in_a_python_tree_are_refused(self):
        target = self.ws.framework + "/lib/python3.12/lib-dynload/_fat.cpython-312-darwin.so"
        write(target, fat(bundle_image()), 0o755)
        self.refused("MACHO", "MACHO-FAT", self.again)
        write(target, macho("MH_BUNDLE", common_commands(), cputype=0x01000007), 0o755)
        self.refused("MACHO", "MACHO-CPU", self.again)
        write(target, macho("MH_OBJECT", common_commands()), 0o644)
        self.refused("MACHO", "MACHO-FILETYPE", self.again)

    def test_package_records_are_verified(self):
        packages, records = observation.verify_packages(self.ws.venv, self.frozen["venv"]["entries"],
                                                        dict(observation.PYTHON_PINS), "3.12")
        self.assertEqual(packages, dict(observation.PYTHON_PINS))
        self.assertEqual((records["Pillow"]["hashed_rows"], records["Pillow"]["unhashed_rows"]), (5, 2))

    def verify(self):
        inventory = self.again()
        return observation.verify_packages(self.ws.venv, inventory["venv"]["entries"], dict(observation.PYTHON_PINS),
                                           "3.12")

    def test_record_mismatch_is_refused(self):
        write(self.ws.site + "/attr/__init__.py", "# altered after installation\n")
        self.refused("PYTHON", "PYTHON-RECORD", self.verify)

    def test_unowned_file_under_site_packages_is_refused(self):
        write(self.ws.site + "/injected.pth", "import os\n")
        self.refused("PYTHON", "PYTHON-UNOWNED", self.verify)

    def test_unhashed_row_for_ordinary_file_is_refused(self):
        dist = self.ws.site + "/attrs-26.1.0.dist-info/RECORD"
        text = Path(dist).read_text().replace("attr/__init__.py,sha256=", "attr/__init__.py,,#", 1)
        text = "\n".join(line.split("#")[0] if line.startswith("attr/__init__.py,,") else line
                         for line in text.splitlines()) + "\n"
        write(dist, text)
        self.refused("PYTHON", "PYTHON-RECORD", self.verify)

    def test_package_set_and_versions_are_exact(self):
        shutil.rmtree(self.ws.site + "/referencing-0.37.0.dist-info")
        shutil.rmtree(self.ws.site + "/referencing")
        self.refused("PYTHON", "PYTHON-PACKAGE", self.verify)
        self.ws.add_package("referencing", "0.36.0", "referencing", "referencing")
        self.refused("PYTHON", "PYTHON-PACKAGE", self.verify)

    def test_lock_must_hold_the_seven_contract_pins(self):
        raw = (REPOSITORY / observation.MACOS_LOCK).read_bytes()
        self.assertEqual(observation.read_lock_pins(raw), dict(observation.PYTHON_PINS))
        self.refused("PYTHON", None, observation.read_lock_pins, raw.replace(b"attrs==26.1.0", b"attrs==26.0.0"))
        self.refused("PYTHON", None, observation.read_lock_pins, raw + b"extra==1.0\n")

    def test_selection_refusals(self):
        os.unlink(self.ws.venv + "/bin/python3.12")
        os.symlink("/usr/bin/false", self.ws.venv + "/bin/python3.12")
        self.refused("PYTHON", "PYTHON-SELECTION", self.again)

    def test_home_must_select_the_framework_launcher(self):
        path = self.ws.venv + "/pyvenv.cfg"
        write(path, Path(path).read_text().replace("include-system-site-packages = false",
                                                   "include-system-site-packages = true"))
        self.refused("PYTHON", None, self.again)
        write(path, "home = /usr/bin\ninclude-system-site-packages = false\nversion = 3.12.13\n")
        self.refused("PYTHON", "PYTHON-HOME", self.again)

    def test_launcher_and_loaded_module_checks(self):
        host = self.ws.host
        state = host.launcher()
        observation.check_launcher(state, self.ws.venv, self.ws.framework, "3.12.13")
        for key, value in (("flags", {**state["flags"], "no_site": 0}), ("site_imported", True),
                           ("executable", self.ws.framework + "/bin/python3.12"), ("version", "3.12.12"),
                           ("process_image", self.ws.framework + "/bin/python3.12"),
                           ("path", state["path"] + [self.ws.source])):
            with self.subTest(key=key):
                self.refused("PYTHON", None, observation.check_launcher, {**state, key: value}, self.ws.venv,
                             self.ws.framework, "3.12.13")
        files = {observation.ENTRY_POINT: {}}
        observation.check_loaded_modules(host.loaded_modules(), self.frozen, self.ws.source, files)
        for row in ({"name": "x", "file": self.ws.base + "/elsewhere.py", "cached": None},
                    {"name": "y", "file": self.ws.source + "/tests/test_synthetic.py", "cached": None},
                    {"name": "z", "file": self.ws.framework + "/lib/python3.12/unbound.py", "cached": None}):
            with self.subTest(module=row["name"]):
                self.refused("PYTHON", "PYTHON-MODULE", observation.check_loaded_modules, [row], self.frozen,
                             self.ws.source, files)


# ---------------------------------------------------------------------------
# Runtime directory, executable pin and NODE-SOURCE.json: MC05
# ---------------------------------------------------------------------------

class RuntimeTests(RefusalMixin, unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)

    def check(self, plan=None):
        return observation.check_runtime(plan or self.ws.plan())

    def test_runtime_is_bound_with_its_layout_and_summary(self):
        runtime = self.check()
        self.assertEqual(runtime["binding"], binding(self.ws.runtime + "/bin/node"))
        self.assertEqual(runtime["layout"]["entries"], ["NODE-SOURCE.json", "bin", "bin/node"])
        self.assertEqual(runtime["macho"]["filetype"], "MH_EXECUTE")
        self.assertEqual(runtime["node_source"]["content"]["extracted"]["path"], "bin/node")
        self.assertEqual(runtime["install"]["state"], "INSTALLED_EXACT")

    def test_mc05_executable_digest_size_or_mode_differs(self):
        plan = self.ws.plan()
        write(self.ws.runtime + "/bin/node", self.ws.node_bytes[:-1] + b"\x01", 0o755)
        self.refused("RUNTIME", "RUNTIME-PIN", self.check, plan)
        write(self.ws.runtime + "/bin/node", self.ws.node_bytes + b"\0", 0o755)
        self.refused("RUNTIME", "RUNTIME-PIN", self.check, plan)
        write(self.ws.runtime + "/bin/node", self.ws.node_bytes, 0o700)
        self.refused("RUNTIME", "RUNTIME-PIN", self.check, plan)

    def test_mc05_executable_not_thin_arm64_macho(self):
        for data, rule in ((fat(self.ws.node_bytes), "MACHO-FAT"), (macho(cputype=0x01000007), "MACHO-CPU"),
                           (b"#!/bin/sh\nexit 0\n", "MACHO-MAGIC"), (macho(commands=node_commands(
                               lc_path("LC_RPATH", "@loader_path"))), "MACHO-REFUSED-COMMAND")):
            with self.subTest(rule=rule):
                write(self.ws.runtime + "/bin/node", data, 0o755)
                executable = binding(self.ws.runtime + "/bin/node")
                self.ws.write_node_source(self.ws.node_source_value(executable))
                self.refused("MACHO", rule, self.check)

    def test_layout_refusals(self):
        for action, rule in ((lambda: write(self.ws.runtime + "/bin/npm", "x", 0o755), "RUNTIME-LAYOUT"),
                             (lambda: write(self.ws.runtime + "/.DS_Store", b"\0"), "TREE-DS-STORE"),
                             (lambda: os.symlink("node", self.ws.runtime + "/bin/node-link"), "TREE-SYMLINK"),
                             (lambda: os.chmod(self.ws.runtime + "/bin", 0o700), "RUNTIME-LAYOUT")):
            with self.subTest(rule=rule):
                ws = Workspace(self)
                self.ws = ws
                plan = ws.plan()
                action()
                self.refused("RUNTIME", rule, self.check, plan)

    def test_node_source_content_checks(self):
        value = self.ws.node_source_value()
        cases = ((dict(value, archive=dict(value["archive"], sha256="ab" * 32)), "NODE-SOURCE"),
                 (dict(value, signature_check={"status": "unknown", "detail": "x"}), "NODE-SOURCE"),
                 (dict(value, signature_check={"status": "verified", "detail": ""}), "NODE-SOURCE"),
                 (dict(value, extracted=dict(value["extracted"], size_bytes=1)), "NODE-SOURCE"),
                 (dict(value, checksum_file=dict(value["checksum_file"], size_bytes=3170)), "NODE-SOURCE"),
                 (dict(value, contract="ontokin.current-host-readback/0.1.0"), "NODE-SOURCE"))
        for changed, rule in cases:
            with self.subTest(rule=rule):
                self.ws.write_node_source(changed)
                self.refused("RUNTIME", rule, self.check)
        self.ws.write_node_source(raw=json.dumps(value, indent=1).encode())
        self.refused("RUNTIME", "NODE-SOURCE", self.check)

    def test_node_source_bytes_must_equal_the_frozen_binding(self):
        plan = self.ws.plan()
        value = self.ws.node_source_value()
        value["signature_check"]["detail"] = "another detail"
        self.ws.write_node_source(value)
        self.refused("RUNTIME", "NODE-SOURCE", self.check, plan)

    def test_receipt_follows_w2_confirmed_shapes(self):
        """Decisions D-11 to D-13: the result's revision fields, labels, pins, preparer and readbacks."""
        labels = dict(json.loads(Path(self.ws.runtime_install["result"]["path"]).read_bytes())["labels"])
        without_state = dict(OS_LABEL, cryptex={key: value for key, value in OS_LABEL["cryptex"].items() if key != "state"})
        dependency_pins = {"origin": "adopted-contract", "dependency_archive_sha256": observation.DEPENDENCY_ARCHIVE_SHA256}
        cases = (({"design_revision": REMOVED}, "the closed set lacks design_revision"),
                 ({"amendments": REMOVED}, "the closed set lacks amendments"),
                 ({"design_revision": 3}, "another design revision"),
                 ({"amendments": []}, "no amendment"),
                 ({"state": "UNKNOWN", "passed": False, "report_error": {"reason": "write failed"},
                   "error": {"code": "CH-EVIDENCE"}}, "a failed report write (correction C4)"),
                 ({"passed": False}, "a receipt state without passed true"),
                 ({"labels": dict(labels, os=REMOVED_VALUE)}, "labels without os"),
                 ({"labels": dict(labels, os=without_state)}, "an OS label whose cryptex lacks state"),
                 ({"labels": dict(labels, os=None)}, "an unread OS label"),
                 ({"labels": dict(labels, pins=dependency_pins)}, "the pins of the other purpose"),
                 ({"labels": dict(labels, pins=dict(labels["pins"], node_executable={"sha256": "ab" * 32,
                   "size_bytes": 1, "mode": "0o755"}))}, "another executable pin"),
                 ({"labels": dict(labels, design_revision=3)}, "labels of another revision"),
                 ({"labels": dict(labels, run_kind="not applicable")}, "a withdrawn placeholder label"),
                 ({"preparer_source": None}, "no preparer record"),
                 ({"preparer_source": {"root": "/elsewhere", "files_at_start": {}}}, "another checkout's preparer"),
                 ({"publication": {"call": "renamex_np", "library": "/usr/lib/libSystem.B.dylib",
                                   "flag": "RENAME_SWAP", "flag_value": 2}}, "another publication call"),
                 ({"before": {"state": "complete_exact", "files": {}, "directories": {}}}, "installed over a tree"),
                 ({"after": {"state": "complete_exact"}}, "an after readback without its tree"),
                 ({"operations": [{"operation": "replaced_destination"}]}, "an unknown operation"),
                 ({"pins": {"origin": "adopted-contract", "node_archive_sha256": observation.NODE_ARCHIVE_SHA256}},
                  "pins without the dependency pin"))
        for changes, label in cases:
            with self.subTest(case=label):
                changes = {key: (REMOVED if value is REMOVED_VALUE else value) for key, value in changes.items()}
                if "labels" in changes and isinstance(changes["labels"], dict):
                    changes["labels"] = {key: value for key, value in changes["labels"].items() if value is not REMOVED_VALUE}
                self.ws.refresh_runtime(**changes)
                self.refused("RUNTIME", "INSTALL-RESULT", self.check)
        result = json.loads(Path(self.ws.runtime_install["result"]["path"]).read_bytes())
        summary = dict(result["archive"])
        del summary["executable"]
        self.ws.refresh_runtime(archive=summary)
        self.refused("RUNTIME", "INSTALL-RESULT", self.check)
        executable = dict(result["archive"]["executable"], macho={"magic": "0xfeedfacf"})
        self.ws.refresh_runtime(archive=dict(result["archive"], executable=executable))
        self.refused("RUNTIME", "INSTALL-RESULT", self.check)
        self.ws.refresh_runtime()
        self.assertEqual(self.check()["install"]["state"], "INSTALLED_EXACT")

    def test_reader_tree_receipt_carries_its_own_pins(self):
        plan = self.ws.plan()
        self.assertEqual(observation.check_dependencies(plan)["install"]["state"], "INSTALLED_EXACT")
        labels = json.loads(Path(self.ws.dependency_install["result"]["path"]).read_bytes())["labels"]
        node_pins = {"origin": "adopted-contract", "node_archive_sha256": observation.NODE_ARCHIVE_SHA256,
                     "node_executable": binding(self.ws.runtime + "/bin/node")}
        self.ws.refresh_dependencies(labels=dict(labels, pins=node_pins))
        self.refused("DEPENDENCY", "INSTALL-RESULT", observation.check_dependencies, self.ws.plan())
        result = json.loads(Path(self.ws.dependency_install["result"]["path"]).read_bytes())
        self.ws.refresh_dependencies(archive=dict(result["archive"], executable={}))
        self.refused("DEPENDENCY", "INSTALL-RESULT", observation.check_dependencies, self.ws.plan())

    def test_failed_signature_check_is_recorded_not_refused(self):
        """Decision D-02: the pin is the trust anchor; a failed check is recorded (and resolved at MP)."""
        self.ws.refresh_runtime(signature="failed")
        runtime = self.check()
        self.assertEqual(runtime["node_source"]["content"]["signature_check"]["status"], "failed")

    def test_install_receipts_follow_the_adapted_0_1_0_rule(self):
        """Decision D-05: the 0.1.0 rule's fields, source_root included, in W2's install/0.2.0 shapes."""
        dependency_archive = descriptor(self.ws.archive)
        cases = (({"execution_counts": {"node": 1, "ldd": 0, "checkers": 0}}, None, "INSTALL-RESULT"),
                 ({"state": "DRY_RUN_READY"}, None, "INSTALL-RESULT"),
                 ({"pins": {"origin": "synthetic-test-seam"}}, None, "INSTALL-RESULT"),
                 ({"error": {"code": "x"}}, None, "INSTALL-RESULT"),
                 ({"apply_requested": False}, None, "INSTALL-RESULT"),
                 ({"after": {"state": "partial"}}, None, "INSTALL-RESULT"),
                 ({"state": "ALREADY_PRESENT_EXACT", "after": REMOVED, "publication": REMOVED}, None, "INSTALL-RESULT"),
                 ({"archive": {"members": 1}}, None, "INSTALL-RESULT"),
                 ({}, {"source_root": self.ws.base}, "INSTALL-PLAN"),
                 ({}, {"purpose": "retained-dependencies"}, "INSTALL-PLAN"),
                 ({}, {"archive": dependency_archive}, "INSTALL-PLAN"),
                 ({}, {"directories": {"bin": "0o700"}}, "INSTALL-PLAN"),
                 ({}, {"report": self.ws.base + "/elsewhere.json"}, "INSTALL-PLAN"),
                 ({}, {"node_source": {"signature_check": {"status": "verified", "detail": "x"}}}, "NODE-SOURCE"))
        for result_changes, plan_changes, rule in cases:
            with self.subTest(rule=rule, result=sorted(result_changes), plan=sorted(plan_changes or {})):
                self.ws.refresh_runtime(plan_changes=plan_changes, **result_changes)
                self.refused("RUNTIME", rule, self.check)
        files = {"bin/node": binding(self.ws.runtime + "/bin/node"),
                 observation.NODE_SOURCE_NAME: binding(self.ws.runtime + "/" + observation.NODE_SOURCE_NAME)}
        self.ws.refresh_runtime(state="ALREADY_PRESENT_EXACT", after=REMOVED, publication=REMOVED,
                                before={"state": "complete_exact", "files": files, "directories": {"bin": "0o755"}})
        self.assertEqual(self.check()["install"]["state"], "ALREADY_PRESENT_EXACT")
        self.ws.refresh_runtime()
        plan = self.ws.plan()
        write(self.ws.node_archive, b"synthetic node archive, altered")
        self.refused("RUNTIME", "INSTALL-ARCHIVE", self.check, plan)


# ---------------------------------------------------------------------------
# Plan rules (P07 section 2, MC33)
# ---------------------------------------------------------------------------

class PlanTests(RefusalMixin, unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)
        self.plan = self.ws.plan()

    def validate(self, plan):
        path, digest = self.ws.write_plan(plan)
        return observation.validate_plan(path, digest, host=self.ws.host)

    def test_valid_plan_is_authenticated(self):
        validated = self.validate(self.plan)
        self.assertEqual(validated.plan, self.plan)
        self.assertEqual(validated.descriptor["sha256"], hashlib.sha256(canonical(self.plan)).hexdigest())

    def test_digest_is_checked_before_decoding(self):
        path = write(self.ws.base + "/garbage.json", b"{not json")
        self.refused("PLAN", "PLAN-DIGEST", observation.validate_plan, path, "ab" * 32, host=self.ws.host)
        good, digest = self.ws.write_plan(self.plan)
        self.refused("PLAN", None, observation.validate_plan, good, "a" * 64, host=self.ws.host)
        self.refused("PLAN", None, observation.validate_plan, good, digest.upper(), host=self.ws.host)
        write(self.ws.base + "/indented.json", json.dumps(self.plan, indent=1))
        indented = self.ws.base + "/indented.json"
        self.refused("PLAN", None, observation.validate_plan, indented,
                     hashlib.sha256(Path(indented).read_bytes()).hexdigest(), host=self.ws.host)

    def test_unresolved_fields_are_refused(self):
        cases = (("tree", None), ("tree", "TODO"), ("commit", "abc*"), ("root", self.ws.source + "/$HOME"))
        for key, value in cases:
            with self.subTest(key=key, value=value):
                plan = json.loads(json.dumps(self.plan))
                plan["source"][key] = value
                self.refused("PLAN", "PLAN-UNRESOLVED", self.validate, plan)
        plan = json.loads(json.dumps(self.plan))
        plan["runtime"]["executable"]["size_bytes"] = 1.5
        self.refused("PLAN", "PLAN-UNRESOLVED", self.validate, plan)
        plan = json.loads(json.dumps(self.plan))
        plan["runtime"]["executable"]["sha256"] = "0" * 64
        self.refused("PLAN", None, self.validate, plan)

    def test_mc33_declared_node_version_other_than_v24_22_1(self):
        for version in ("v24.22.0", "v24.22.1 ", "24.22.1"):
            with self.subTest(version=version):
                plan = json.loads(json.dumps(self.plan))
                plan["runtime"]["version"] = version
                self.refused("RUNTIME", "RUNTIME-VERSION", self.validate, plan)

    def test_other_version_and_unknown_members_are_refused(self):
        plan = dict(self.plan, schema="ontokin.current-host-readback-inspection-plan/0.1.5")
        self.refused("PLAN", "PLAN-SCHEMA", self.validate, plan)
        plan = dict(self.plan, approved=True)
        self.refused("PLAN", None, self.validate, plan)
        plan = dict(self.plan)
        del plan["failure_capture"]
        self.refused("PLAN", None, self.validate, plan)

    def test_declared_environment_and_limits_are_fixed(self):
        for environment in ({**observation.ENVIRONMENT, observation.CF_NAME: CF_VALUE},
                            {**observation.ENVIRONMENT, "NODE_OPTIONS": "--inspect"},
                            {**observation.ENVIRONMENT, "PATH": "/usr/local/bin:/usr/bin:/bin"}):
            with self.subTest(names=sorted(environment)):
                self.refused("PLAN", "PLAN-ENVIRONMENT", self.validate, dict(self.plan, environment=environment))
        self.refused("PLAN", None, self.validate, dict(self.plan, limits=dict(observation.LIMITS, command_ms=6000)))

    def test_commands_and_outputs_are_the_fixed_literals(self):
        plan = json.loads(json.dumps(self.plan))
        plan["commands"][1]["argv"].append("--inspect")
        self.refused("PLAN", "PLAN-COMMANDS", self.validate, plan)
        plan = json.loads(json.dumps(self.plan))
        plan["commands"].reverse()
        self.refused("PLAN", "PLAN-COMMANDS", self.validate, plan)
        plan = json.loads(json.dumps(self.plan))
        plan["evidence"]["outputs"]["host"] = self.ws.attempt + "/OTHER.json"
        self.refused("PATH", None, self.validate, plan)

    def test_paths_must_be_canonical_and_separate(self):
        os.symlink(self.ws.runtime, self.ws.base + "/runtime-alias")
        plan = json.loads(json.dumps(self.plan))
        plan["runtime"]["directory"] = self.ws.base + "/runtime-alias"
        plan["commands"] = observation.expected_commands(plan)
        self.refused("PATH", "PATH-SYMLINK", self.validate, plan)
        plan = json.loads(json.dumps(self.plan))
        plan["evidence"]["parent"] = self.ws.runtime
        plan["evidence"]["attempt"] = self.ws.runtime + "/attempt"
        plan["evidence"]["outputs"] = observation.output_paths(self.ws.runtime + "/attempt")
        plan["commands"] = observation.expected_commands(plan)
        self.refused("PATH", None, self.validate, plan)
        plan = json.loads(json.dumps(self.plan))
        plan["python"]["venv"] = self.ws.base
        self.refused("PYTHON", None, self.validate, plan)

    def test_git_dispatcher_and_link_are_refused_in_the_plan(self):
        plan = json.loads(json.dumps(self.plan))
        plan["git"]["path"] = self.ws.dispatcher
        plan["commands"] = observation.expected_commands(plan)
        self.refused("GIT", "GIT-DISPATCHER", self.validate, plan)
        os.symlink(self.ws.git, self.ws.base + "/git/bin/git-link")
        plan["git"]["path"] = self.ws.base + "/git/bin/git-link"
        plan["commands"] = observation.expected_commands(plan)
        self.refused("GIT", "GIT-SYMLINK", self.validate, plan)


# ---------------------------------------------------------------------------
# M0 and M1 end to end through the mocked supervisor (MC10 and the start order)
# ---------------------------------------------------------------------------

@needs_darwin
class ObservationTests(RefusalMixin, unittest.TestCase):
    """Complete synthetic host; the supervisor and every reader are mocked and labelled so."""

    def setUp(self):
        self.ws = Workspace(self)
        self.path, self.digest = self.ws.write_plan(self.ws.plan())
        self.supervisor = self.ws.host.mocked_supervisor

    def observe(self, **kwargs):
        return observation.observe_host(self.path, self.digest, host=self.ws.host, **kwargs)

    def document(self, path):
        return json.loads(Path(path).read_bytes())

    def test_observe_publishes_host_with_every_field(self):
        result = self.observe()
        self.assertEqual((result["state"], result["evidence_finalized"]), ("OBSERVED_UNAPPROVED", True))
        self.assertEqual(result["starts"], {"node": {"exact": 1, "observed_lower_bound": 1},
                                            "other": {"exact": 1, "observed_lower_bound": 1}})
        self.assertEqual([call["kind"] for call in self.supervisor.calls], ["git", "node"])
        self.assertEqual(self.supervisor.calls[0]["argv"], [self.ws.git, "--version"])
        self.assertEqual(self.supervisor.calls[1]["argv"], [self.ws.runtime + "/bin/node", "--version"])
        self.assertEqual(self.supervisor.calls[1]["env"], dict(observation.ENVIRONMENT))
        self.assertEqual(self.supervisor.calls[0]["env"], dict(observation.GIT_ENVIRONMENT))
        host = self.document(result["host"]["path"])
        self.assertEqual(set(host), {"schema", "contract", "design_revision", "amendments", "profile", "executor",
                                     "observed_at_utc", "plan", "observer",
                                     "platform", "os", "environment", "python", "runtime", "git", "dependencies",
                                     "source", "inspections", "starts", "labels", "claims"})
        self.assertEqual((host["schema"], host["executor"]), (observation.HOST_SCHEMA, "macos-arm64-local"))
        self.assertEqual(host["environment"], {"declared": dict(observation.ENVIRONMENT),
                                               "cf_user_text_encoding": CF_VALUE})
        self.assertEqual(host["git"], {**descriptor(self.ws.git), "version": "git version 2.0.0 (synthetic)"})
        self.assertNotEqual(host["git"]["path"], "/usr/bin/git")
        self.assertEqual(host["platform"]["boot_session_uuid"], BOOT)
        self.assertEqual((host["os"]["cryptex"]["state"], host["os"]["cryptex"]["path"],
                          host["os"]["cryptex"]["link_path"]), ("present", self.ws.cryptex_canonical,
                                                                self.ws.cryptex_plist))
        self.assertEqual([hop["path"] for hop in host["os"]["cryptex"]["hops"]],
                         [self.ws.base + "/os/System/Cryptexes/OS"])
        self.assertEqual(host["runtime"]["binding"], binding(self.ws.runtime + "/bin/node"))
        self.assertEqual(set(host["runtime"]), {"directory", "executable", "version", "binding", "archive",
                                                "node_source", "layout", "macho", "install"})
        self.assertEqual(host["runtime"]["archive"], descriptor(self.ws.node_archive))
        self.assertEqual((host["runtime"]["install"]["purpose"], host["dependencies"]["install"]["purpose"]),
                         ("selected-node", "retained-dependencies"))
        self.assertEqual(host["labels"]["node"]["signature_check"], "not_performed")
        self.assertEqual(host["python"]["packages"], dict(observation.PYTHON_PINS))
        self.assertEqual(host["python"]["inventory_sha256"], host["python"]["inventory"]["sha256"])
        self.assertEqual(host["source"]["head"]["commit"], self.ws.commit)
        labels = host["labels"]
        self.assertEqual((labels["boundary"], labels["run_kind"], labels["contract"]),
                         ("mocked", "host-observation", observation.CONTRACT))
        self.assertEqual(labels["node"]["archive_sha256"], observation.NODE_ARCHIVE_SHA256)
        self.assertEqual(labels["git"], {"path": self.ws.git, "sha256": descriptor(self.ws.git)["sha256"]})
        node = self.document(host["inspections"]["node_version"]["path"])
        self.assertEqual((node["schema"], node["stdout"], node["stderr"], node["timeout_ms"]),
                         (observation.INSPECTION_SCHEMA, "v24.22.1\n", "", 5000))
        completion = self.document(result["completion"]["path"])
        self.assertEqual((completion["state"], completion["boundary"]), ("OBSERVED_UNAPPROVED", "mocked"))
        self.assertEqual(stat.S_IMODE(os.lstat(self.ws.attempt).st_mode), 0o700)
        leftovers = [name for _, _, names in os.walk(self.ws.attempt) for name in names if name.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def assert_revision(self, document, where):
        self.assertEqual({key: document.get(key) for key in REVISION}, REVISION, where)

    def observer_documents(self):
        """Every JSON document in the attempt except the supervisor's own unchanged receipt."""
        for root, _, names in os.walk(self.ws.attempt):
            for name in sorted(names):
                if name.endswith(".json") and not name.endswith(".process.json"):
                    yield os.path.join(root, name), self.document(os.path.join(root, name))

    def test_every_observer_document_carries_the_design_revision(self):
        """Decisions D-12 and D-13: contract, design_revision 4 and amendments, also in HOST's labels."""
        result = self.observe()
        documents = dict(self.observer_documents())
        top = {"reserved", "preflight", "HOST", "result", "completion"}
        stage = {"intent", "started", "inspection", "postflight"}
        self.assertEqual(set(documents), {self.ws.attempt + "/" + name + ".json" for name in top}
                         | {self.ws.attempt + "/" + command + "/" + name + ".json" for command in observation.COMMAND_IDS
                            for name in stage})
        for where, document in documents.items():
            self.assert_revision(document, where)
        host = documents[self.ws.attempt + "/HOST.json"]
        self.assert_revision(host["labels"], "HOST labels")
        self.assert_revision(result, "returned result")
        self.assert_revision(documents[self.ws.attempt + "/node_version/inspection.json"], "inspection receipt")
        self.assertNotIn("design_revision", json.loads(Path(self.ws.runtime + "/NODE-SOURCE.json").read_bytes()))
        raw = Path(self.ws.attempt + "/node_version/host-node-version.process.json").read_bytes()
        self.assertNotIn(b"design_revision", raw)

    def test_refusal_documents_carry_the_design_revision(self):
        self.supervisor.outputs["node"] = (b"v24.22.0\n", b"", 0, None)
        error = self.refused("OUTPUT", "OUTPUT-NODE-VERSION", self.observe)
        self.assert_revision(error.result, "refusal result")
        for where, document in self.observer_documents():
            self.assert_revision(document, where)
        self.assertTrue(os.path.lexists(self.ws.attempt + "/node_version/failure.json"))

    def test_mc30_observe_without_cf_records_null(self):
        """Simulated boundary: the observing process has no __CF_USER_TEXT_ENCODING (labelled mocked)."""
        self.ws.host.env.pop(observation.CF_NAME)
        host = self.document(self.observe()["host"]["path"])
        self.assertIsNone(host["environment"]["cf_user_text_encoding"])

    def test_mc10_node_version_differs(self):
        """Simulated at the command boundary and labelled mocked: failed preparation, no HOST."""
        self.supervisor.outputs["node"] = (b"v24.22.0\n", b"", 0, None)
        error = self.refused("OUTPUT", "OUTPUT-NODE-VERSION", self.observe)
        result = error.result
        self.assertEqual((result["state"], result["host"], result["evidence_finalized"]), ("REJECTED", None, False))
        self.assertEqual(result["starts"], {"node": {"exact": 1, "observed_lower_bound": 1},
                                            "other": {"exact": 1, "observed_lower_bound": 1}})
        self.assertFalse(os.path.lexists(self.ws.attempt + "/HOST.json"))
        self.assertFalse(os.path.lexists(self.ws.attempt + "/completion.json"))
        self.assertEqual(self.document(self.ws.attempt + "/result.json")["state"], "REJECTED")
        failure = self.document(self.ws.attempt + "/node_version/failure.json")
        self.assertEqual((failure["boundary"], failure["failure"]["code"]), ("mocked", "CHO-OUTPUT"))

    def test_git_version_must_be_one_line_without_stderr(self):
        for output, rule in (((b"not git\n", b"", 0, None), "OUTPUT-GIT-VERSION"),
                             ((GIT_STDOUT, b"warning\n", 0, None), "OUTPUT-STDERR")):
            with self.subTest(rule=rule):
                self.setUp()
                self.supervisor.outputs["git"] = output
                error = self.refused("OUTPUT", rule, self.observe)
                self.assertEqual([call["kind"] for call in self.supervisor.calls], ["git"])
                self.assertEqual(error.result["starts"]["node"], {"exact": 0, "observed_lower_bound": 0})

    def test_supervisor_stop_is_retained(self):
        self.supervisor.outputs["git"] = (b"", b"", 0, "Child exited while an owned descendant remained")
        error = self.refused("PROCESS", None, self.observe)
        self.assertEqual(error.cause.code, "OTRAY-E-BACKEND")
        attempt = self.document(self.ws.attempt + "/git_version/postflight.json")
        self.assertEqual((attempt["start_count_state"], attempt["supervisor_failure"]["reason"]),
                         ("OBSERVED_ONE", "Child exited while an owned descendant remained"))

    def test_drift_between_starts_refuses_before_node(self):
        def mutate():
            write(self.ws.framework + "/lib/python3.12/__pycache__/late.cpython-312.pyc", b"\x00late")
        self.supervisor.before["git"] = mutate
        error = self.refused("DRIFT", "DRIFT", self.observe)
        self.assertEqual([call["kind"] for call in self.supervisor.calls], ["git"])
        self.assertEqual(error.result["starts"]["node"]["exact"], 0)

    def test_unplanned_file_in_the_evidence_tree_refuses(self):
        def ds_store_file():
            write(self.ws.attempt + "/.DS_Store", b"\0")
        self.supervisor.before["node"] = ds_store_file
        error = self.refused("EVIDENCE", "TREE-DS-STORE", self.observe)
        self.assertEqual((error.result["host"], os.path.lexists(self.ws.attempt + "/HOST.json")), (None, False))
        self.setUp()
        self.supervisor.before["node"] = lambda: write(self.ws.attempt + "/node_version/notes.txt", "x")
        self.refused("EVIDENCE", "EVIDENCE-TREE", self.observe)

    def test_static_check_starts_and_writes_nothing(self):
        result = observation.static_check(self.path, self.digest, host=self.ws.host)
        self.assertEqual({key: result[key] for key in REVISION}, REVISION)
        self.assertEqual({key: result["labels"][key] for key in REVISION}, REVISION)
        self.assertEqual((result["state"], result["starts"]["node"]["exact"], result["starts"]["other"]["exact"]),
                         ("STATIC_READY", 0, 0))
        self.assertEqual(self.supervisor.calls, [])
        self.assertFalse(os.path.lexists(self.ws.attempt))

    def test_existing_attempt_and_changed_inputs_refuse_before_any_start(self):
        os.mkdir(self.ws.attempt)
        self.refused("PATH", "EVIDENCE-FRESH", self.observe)
        os.rmdir(self.ws.attempt)
        write(self.ws.framework + "/lib/python3.12/os.py", "# changed after the freeze\n")
        self.refused("PYTHON", "PYTHON-INVENTORY", self.observe)
        self.assertEqual(self.supervisor.calls, [])

    def test_mc08_platform_refuses_before_any_start(self):
        """Simulated reader values, labelled mocked."""
        for attribute, value in (("translated", 1), ("translated", None), ("machine", "x86_64"), ("sysname", "Linux")):
            with self.subTest(attribute=attribute):
                self.setUp()
                setattr(self.ws.host, attribute, value)
                self.refused("PLATFORM", None, self.observe)
                self.assertEqual(self.supervisor.calls, [])

    def test_mc07_forbidden_variable_refuses_before_any_start(self):
        self.ws.host.env["DYLD_INSERT_LIBRARIES"] = "/tmp/x.dylib"
        self.refused("ENVIRONMENT", "ENVIRONMENT-EXACT", self.observe)
        self.assertEqual(self.supervisor.calls, [])

    def test_os_build_change_refuses(self):
        write(self.ws.cryptex_plist, plistlib.dumps({"ProductName": "macOS", "ProductVersion": "26.6.3",
                                                     "ProductBuildVersion": "25G90"}), 0o444)
        self.refused("OS", "OS-CRYPTEX", self.observe)
        os.unlink(self.ws.cryptex_plist)
        self.refused("OS", "OS-CRYPTEX", self.observe)
        self.assertEqual(self.supervisor.calls, [])

    def test_retargeted_cryptex_link_refuses(self):
        other = self.ws.base + "/os/System/Volumes/Other/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist"
        write(other, Path(self.ws.cryptex_canonical).read_bytes(), 0o444)
        os.unlink(self.ws.base + "/os/System/Cryptexes/OS")
        os.symlink("../../System/Volumes/Other/Cryptexes/OS", self.ws.base + "/os/System/Cryptexes/OS")
        self.refused("OS", "OS-CRYPTEX", self.observe)
        self.assertEqual(self.supervisor.calls, [])

    def test_enotsup_publication_has_no_fallback(self):
        def unsupported(source, destination):
            raise OSError(errno.ENOTSUP, "Operation not supported", destination)
        error = self.refused("EVIDENCE", None, self.observe, rename=unsupported)
        self.assertIn("no fallback", error.reason)
        self.assertFalse(os.path.lexists(self.ws.attempt + "/reserved.json"))
        self.assertTrue(any(name.startswith(".reserved.json.") for name in os.listdir(self.ws.attempt)))
        self.assertEqual(self.supervisor.calls, [])

    def test_substituted_boundaries_must_be_labelled_mocked(self):
        class Unlabelled(MockedHost):
            boundary = "real"
        host = Unlabelled(self.ws)
        self.refused("PLAN", None, observation.observe_host, self.path, self.digest, host=host)
        self.refused("PLAN", None, observation.observe_host, self.path, self.digest,
                     rename=lambda source, destination: None)
        self.assertEqual(host.mocked_supervisor.calls + self.supervisor.calls, [])

    def test_existing_destination_is_never_replaced(self):
        def conflicting(source, destination):
            with open(destination, "x") as stream:
                stream.write("pre-existing")
            observation.rename_exclusive(source, destination)
        error = self.refused("PATH", None, self.observe, rename=conflicting)
        self.assertEqual(error.cause.errno, errno.EEXIST)
        self.assertEqual(Path(self.ws.attempt + "/reserved.json").read_text(), "pre-existing")


@needs_darwin
class RenameTests(unittest.TestCase):
    """renamex_np with RENAME_EXCL on temporary files (a system call, no process)."""

    def test_rename_exclusive_publishes_and_never_replaces(self):
        base = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base, True)
        source, destination = write(base + "/source", "new"), base + "/destination"
        observation.rename_exclusive(source, destination)
        self.assertEqual((Path(destination).read_text(), os.path.lexists(source)), ("new", False))
        other = write(base + "/other", "other")
        with self.assertRaises(OSError) as caught:
            observation.rename_exclusive(other, destination)
        self.assertEqual(caught.exception.errno, errno.EEXIST)
        self.assertEqual((Path(destination).read_text(), Path(other).read_text()), ("new", "other"))
        self.assertEqual(observation.RENAME_EXCL, 0x00000004)


# ---------------------------------------------------------------------------
# Lazy supervisor import and the module's own import surface
# ---------------------------------------------------------------------------

class SupervisorImportTests(RefusalMixin, unittest.TestCase):
    """Imports only synthetic stand-ins from the synthetic root; never the real Darwin supervisor."""

    def setUp(self):
        self.ws = Workspace(self)
        self.inventory = observation.source_inventory(self.ws.source)

    def isolated_modules(self):
        context = patch.dict(sys.modules)
        context.start()
        self.addCleanup(context.stop)
        for name in [name for name in sys.modules if name == "prototypes" or name.startswith("prototypes.")]:
            del sys.modules[name]

    def test_bound_stand_in_is_imported_lazily_from_the_bound_root(self):
        self.isolated_modules()
        module = observation.load_darwin_supervisor(self.ws.source, self.inventory)
        self.assertEqual(module.__file__, self.ws.source + "/prototypes/static_tray_v01/supervisor_darwin_v01.py")
        self.assertNotIn(self.ws.source, sys.path)

    def test_module_claiming_the_bound_path_with_other_code_is_refused(self):
        self.isolated_modules()
        for name, rel in observation.SUPERVISOR_FILES.items():
            fake = SimpleNamespace(__file__=self.ws.source + "/" + rel, __cached__=None)
            sys.modules[name] = fake
        sys.modules[observation.SUPERVISOR_MODULE].run_process = lambda *args, **kwargs: None
        sys.modules[observation.SUPERVISOR_MODULE].Clock = MockedClock
        sys.modules[observation.SUPERVISOR_MODULE].Stop = MockedStop
        self.refused("SOURCE", "SUPERVISOR-UNBOUND", observation.load_darwin_supervisor, self.ws.source, self.inventory)

    def test_supervisor_outside_the_inventory_is_refused(self):
        inventory = {"files": dict(self.inventory["files"])}
        del inventory["files"]["prototypes/static_tray_v01/supervisor_darwin_v01.py"]
        self.refused("SOURCE", "SUPERVISOR-UNBOUND", observation.load_darwin_supervisor, self.ws.source, inventory)

    def test_observer_imports_only_the_standard_library_at_top_level(self):
        tree = ast.parse(OBSERVER.read_text())
        names = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                names.add(node.module.split(".")[0])
        self.assertTrue(names <= set(sys.stdlib_module_names) | {"__future__"}, names)
        self.assertNotIn("importlib.metadata", OBSERVER.read_text())


# ---------------------------------------------------------------------------
# Source inventory and static HEAD
# ---------------------------------------------------------------------------

class SourceTests(RefusalMixin, unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(self)

    def test_source_inventory_and_head(self):
        inventory = observation.source_inventory(self.ws.source)
        self.assertIn(observation.ENTRY_POINT, inventory["files"])
        self.assertIn(observation.MACOS_LOCK, inventory["files"])
        self.assertNotIn(".venv/pyvenv.cfg", inventory["files"])
        head = observation.git_head(self.ws.source)
        self.assertEqual((head["ref"], head["commit"]), ("refs/heads/main", self.ws.commit))

    def test_bytecode_symlink_and_ds_store_files_refuse_the_source(self):
        for action, rule in ((lambda: write(self.ws.source + "/tests/__pycache__/x.cpython-312.pyc", b"x"),
                              "SOURCE-BYTECODE"),
                             (lambda: write(self.ws.source + "/ontokin/.DS_Store", b"x"), "TREE-DS-STORE"),
                             (lambda: os.symlink("__init__.py", self.ws.source + "/ontokin/alias.py"), "TREE-SYMLINK")):
            with self.subTest(rule=rule):
                self.ws = Workspace(self)
                action()
                self.refused("SOURCE", rule, observation.source_paths, self.ws.source)

    def test_worktree_git_file_and_packed_refs(self):
        gitdir = self.ws.base + "/main/.git/worktrees/w"
        write(gitdir + "/HEAD", "ref: refs/heads/topic\n")
        write(gitdir + "/commondir", "../..\n")
        write(self.ws.base + "/main/.git/packed-refs", "# pack-refs\n" + "5" * 40 + " refs/heads/topic\n")
        shutil.rmtree(self.ws.source + "/.git")
        write(self.ws.source + "/.git", "gitdir: " + gitdir + "\n")
        head = observation.git_head(self.ws.source)
        self.assertEqual((head["commit"], head["common_dir"]), ("5" * 40, self.ws.base + "/main/.git"))

    @needs_darwin
    def test_changed_source_or_head_refuses(self):
        plan = self.ws.plan()
        path, digest = self.ws.write_plan(plan)
        write(self.ws.source + "/ontokin/__init__.py", "# changed\n")
        self.refused("SOURCE", "SOURCE-BINDING", observation.static_check, path, digest, host=self.ws.host)
        self.ws = Workspace(self)
        path, digest = self.ws.write_plan(self.ws.plan())
        write(self.ws.source + "/.git/refs/heads/main", "6" * 40 + "\n")
        self.refused("SOURCE", "SOURCE-COMMIT", observation.static_check, path, digest, host=self.ws.host)

    def test_dependency_tree_is_exact(self):
        """Uses synthetic pins in place of the C199 manifest digest (labelled simulated)."""
        plan = self.ws.plan()
        result = observation.check_dependencies(plan)
        self.assertEqual(result["files"], 24)
        write(self.ws.dependencies + "/validator/package/extra.js", "// extra\n")
        self.refused("DEPENDENCY", "DEPENDENCY-TREE", observation.check_dependencies, plan)
        os.unlink(self.ws.dependencies + "/validator/package/extra.js")
        write(self.ws.dependencies + "/.DS_Store", b"\0")
        self.refused("DEPENDENCY", "TREE-DS-STORE", observation.check_dependencies, plan)


# ---------------------------------------------------------------------------
# Command line (each test starts one Python interpreter: this observer)
# ---------------------------------------------------------------------------

class CommandLineTests(unittest.TestCase):
    environment = dict(observation.ENVIRONMENT)

    def run_observer(self, *arguments, flags=("-I", "-S", "-B")):
        completed = subprocess.run([sys.executable, *flags, str(OBSERVER), *arguments], env=self.environment,
                                   cwd=tempfile.gettempdir(), capture_output=True, timeout=60, check=False)
        return completed.returncode, completed.stdout, json.loads(completed.stderr) if completed.stderr else None

    def test_missing_plan_is_refused_with_a_structured_record(self):
        """Starts one Python (-I -S -B observer static); no plan exists, so nothing else starts."""
        absent = os.path.realpath(tempfile.gettempdir()) + "/w3-absent-plan-%d.json" % os.getpid()
        code, stdout, refusal = self.run_observer("static", "--plan", absent, "--plan-sha256", "ab" * 32)
        self.assertEqual((code, stdout), (1, b""))
        self.assertEqual((refusal["schema"], refusal["passed"], refusal["evidence_finalized"]),
                         (observation.REFUSAL_SCHEMA, False, False))
        self.assertEqual({key: refusal[key] for key in REVISION}, REVISION)
        self.assertEqual(refusal["error"]["code"], "CHO-PATH")

    def test_launch_without_no_site_is_refused(self):
        """Starts one Python with -I -B but without -S; -B keeps bytecode out of every tree."""
        code, _, refusal = self.run_observer("static", "--plan", "/x", "--plan-sha256", "ab" * 32, flags=("-I", "-B"))
        self.assertEqual(code, 1)
        self.assertEqual((refusal["error"]["code"], refusal["error"]["details"]["rule"]), ("CHO-PYTHON", "PYTHON-LAUNCHER"))

    def test_inventory_commands_write_only_their_absent_outputs(self):
        """Starts one Python per run (-I -S -B observer python-inventory twice, then source-inventory)
        on the synthetic trees; the outputs equal the in-process documents."""
        ws = Workspace(self)
        output = ws.base + "/frozen-python.json"
        code, stdout, refusal = self.run_observer("python-inventory", "--venv", ws.venv, "--framework", ws.framework,
                                                  "--output", output)
        self.assertEqual((code, refusal), (0, None), refusal)
        self.assertEqual(json.loads(stdout)["output"], descriptor(output))
        self.assertEqual({key: json.loads(stdout)[key] for key in REVISION}, REVISION)
        self.assertNotIn("design_revision", json.loads(Path(output).read_bytes()))
        self.assertEqual(Path(output).read_bytes(), canonical(observation.python_inventory(ws.venv, ws.framework)))
        code, _, refusal = self.run_observer("python-inventory", "--venv", ws.venv, "--framework", ws.framework,
                                             "--output", output)
        self.assertEqual((code, refusal["error"]["code"]), (1, "CHO-EVIDENCE"))
        output = ws.base + "/frozen-source.json"
        code, stdout, refusal = self.run_observer("source-inventory", "--root", ws.source, "--output", output)
        self.assertEqual((code, refusal), (0, None), refusal)
        self.assertEqual(Path(output).read_bytes(), canonical(observation.source_inventory(ws.source)))


if __name__ == "__main__":
    unittest.main()
