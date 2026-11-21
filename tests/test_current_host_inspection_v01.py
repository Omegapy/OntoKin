"""Finite C271 P08 controls: real isolated files and mocked process boundaries.

No fixture is a real host observation. All process creation, waiting and process
group operations are forbidden by the test guard. Operational Node/archive/pin
facts are synthetic inputs at explicitly named seams. The original seven tests
and P06 consumers are neither edited nor executed by this module.

The independent expectation source is CONTROL-FREEZE-002.json, SHA-256
55ccbcf49c0a7f283813345ec66e07936f3d777076d4b28db74bc46d56111887.
This file fixes the logical fixture recipes, bytes, mutations and mock behavior.
Actual roots, filesystem inode/time identities, publication UUIDs and UTC clock
samples vary by run. ONTOKIN_HI_RETAIN_ROOT retains each complete fixture tree
and a manifest of its actual identities; exact source snapshots accompany runs.
"""
from __future__ import annotations

from contextlib import ExitStack, contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import runpy
import stat
import struct
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
import tempfile

from prototypes.static_tray_v01 import current_host_inspection_v01 as inspection


CONTROL_VARIANTS = {
    "HI01": "ABCDEFGH", "HI02": "AB", "HI03": "ABCDEFGHI", "HI04": "ABCDEFG",
    "HI05": "ABCDE", "HI06": "ABCDEFG", "HI07": "ABCDEFG", "HI08": "ABCDEF",
    "HI09": "ABCDE", "HI10": "ABC", "HI11": "ABC", "HI12": "ABCD", "HI13": "ABCDEFG",
    "HI14": "ABCD", "HI15": "ABCDE", "HI16": "ABCD", "HI17": "ABCDE",
    "HI18": "ABCDEFG", "HI19": "ABCDEF", "HI20": "ABCDE"}
PINNED_NODE = {"sha256": "acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa",
               "size_bytes": 126951512, "mode": "0o755"}
PINNED_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
PINNED_LIMITS = {"direct_starts": 2, "command_ms": 5000, "active_work_ms": 3000, "cleanup_ms": 2000,
    "log_bytes": 4194304, "inspection_bytes": 8388608, "host_bytes": 8388608, "document_bytes": 16777216,
    "stage_bytes": 67108864, "stage_entries": 2048, "static_ms": 60000, "publication_ms": 30000}
PINNED_PACKAGES = {"attrs": "26.1.0", "jsonschema": "4.26.0", "jsonschema-specifications": "2025.9.1",
    "referencing": "0.37.0", "rpds-py": "2026.5.1", "typing_extensions": "4.16.0", "Pillow": "13.0.0"}
PINNED_SOURCE_TREES = ("ontokin", "tests", "prototypes/static_tray_v01", "tools/static_tray_reader_v01")
PINNED_SOURCE_OPTIONAL = ("prototypes/__init__.py", "tools/__init__.py", "tests/__init__.py")
PINNED_SOURCE_FILES = ("tools/check_local.py", "tools/prepare_current_host_readback.py", "tools/storage_identity.py",
    "tools/force-agent-verification-requirements.txt", "tools/native-reader-verification-linux-cp312.lock", "pyproject.toml",
    "docs/engineering/static-tray-mapping-c198/CONTROLS.json", "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json",
    "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md", "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json",
    "docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json", "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip")
FIXED_TIME = "2026-11-21T00:00:00+00:00"
FIXED_FINISH = "2026-11-21T00:00:00.100000+00:00"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def file_binding(path):
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data), "mode": oct(stat.S_IMODE(path.stat().st_mode))}


def descriptor(path):
    return {"path": str(path), **file_binding(path)}


def put(path, data=b"synthetic fixture\n", mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)
    return path


def json_file(path, value):
    return descriptor(put(path, canonical(value)))


def evidence_snapshot(root):
    """Complete finite fixture inventory, including added paths/directories."""
    result = {}
    for path in (root, *sorted(root.rglob("*"))):
        info = path.lstat()
        kind = "link" if stat.S_ISLNK(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "file"
        result[str(path)] = (kind, info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode),
                             os.readlink(path) if kind == "link" else path.read_bytes() if kind == "file" else None)
    return result


def synthetic_elf(path, *, interpreter=None, needed=(), soname=None, rpath=None, runpath=None,
                  extra_tags=(), machine=62, duplicate_interp=False, dynamic_displacement=0):
    """Independent tiny ELF64 fixture; no executable code and no OS execution."""
    raw = bytearray(0x900)
    raw[:16] = b"\x7fELF\x02\x01\x01" + b"\0" * 9
    count = 2 + (1 if interpreter else 0) + (1 if duplicate_interp else 0)
    struct.pack_into("<HHIQQQIHHHHHH", raw, 16, 3, machine, 1, 0, 64, 0, 0, 64, 56, count, 0, 0, 0)
    strings = bytearray(b"\0")
    tags = []
    for tag, text in [(1, value) for value in needed] + ([(14, soname)] if soname else []) + ([(15, rpath)] if rpath is not None else []) + ([(29, runpath)] if runpath is not None else []):
        tags.append((tag, len(strings)))
        strings.extend(text.encode("ascii") + b"\0")
    tags = [(5, 0x400500), (10, len(strings))] + tags + list(extra_tags) + [(0, 0)]
    dyn = b"".join(struct.pack("<qQ", tag, value) for tag, value in tags)
    rows = [(1, 5, 0, 0x400000, 0, len(raw), len(raw), 4096),
            (2, 4, 0x300, 0x400300 + dynamic_displacement, 0, len(dyn), len(dyn), 8)]
    if interpreter:
        data = interpreter.encode("ascii") + b"\0"
        raw[0x200:0x200 + len(data)] = data
        rows.append((3, 4, 0x200, 0x400200, 0, len(data), len(data), 1))
        if duplicate_interp:
            rows.append(rows[-1])
    for index, row in enumerate(rows):
        struct.pack_into("<IIQQQQQQ", raw, 64 + 56 * index, *row)
    raw[0x300:0x300 + len(dyn)] = dyn
    raw[0x500:0x500 + len(strings)] = strings
    put(path, bytes(raw), 0o755)
    expected = {"class": 64, "endian": "little", "machine": machine, "type": 3,
                "interpreter": interpreter, "needed": list(needed), "soname": soname,
                "rpath": [] if rpath is None else rpath.split(":"), "runpath": [] if runpath is None else runpath.split(":")}
    return expected


class Fixture:
    """Synthetic plan, isolated source bytes and observation fixture topology."""
    def __init__(self, base, rename, supervisor):
        self.base, self.rename, self.supervisor = base, rename, supervisor
        self.source, self.evidence = base / "source", base / "evidence"
        self.runtime, self.dependencies = base / "runtime", base / "dependencies"
        for directory in (self.source, self.evidence, self.dependencies, self.runtime / "bin"):
            directory.mkdir(parents=True)
        for directory in inspection.SOURCE_TREES:
            (self.source / directory).mkdir(parents=True, exist_ok=True)
        for name in inspection.SOURCE_FILES + (inspection.ENTRY_POINT, "prototypes/static_tray_v01/current_host_readback_v01.py",
                                               "prototypes/static_tray_v01/supervisor.py"):
            put(self.source / name, ("synthetic source: " + name + "\n").encode())
        put(self.source / ".git/HEAD", b"a" * 40 + b"\n")
        put(self.source / ".git/index", b"synthetic index, never passed to Git")
        inventory = {"schema": "ontokin.current-host-readback-source/0.1.0", "files": {
            path.relative_to(self.source).as_posix(): file_binding(path) for path in self.source.rglob("*")
            if path.is_file() and ".git" not in path.parts}}
        self.inventory = inventory
        source_descriptor = json_file(base / "source-inventory.json", inventory)
        self.node = put(self.runtime / "bin/node", b"inert Node fixture", 0o755)
        self.python = put(base / "python", b"inert Python fixture", 0o755)
        self.git = put(base / "git", b"inert Git fixture", 0o755)
        self.drift = put(base / "drift-input", b"stable")
        self.archive = put(base / "archive.tar", b"inert archive")
        self.dummy = json_file(base / "document.json", {"fixture": True})
        self.source_value = {"root": str(self.source), "commit": "a" * 40, "tree": "b" * 40, "inventory": source_descriptor}
        self.platform = {"system": "Linux", "release": "synthetic-kernel", "machine": "x86_64", "libc": ["glibc", "2.39"], "boot_id": "1" * 8 + "-" + "1" * 4 + "-" + "1" * 4 + "-" + "1" * 4 + "-" + "1" * 12}
        self.library, self.loader = "/fixture/lib/libc.so.6", "/fixture/lib/ld-linux-x86-64.so.2"
        self.resolution = {"libraries": {"libc.so.6": self.library}, "interpreter": self.loader, "vdso": ["linux-vdso.so.1"]}
        self.ldd_stdout = ("\tlinux-vdso.so.1 (0x7fff3000)\n\tlibc.so.6 => " + self.library + " (0x7f1000)\n\t" + self.loader + " (0x7f2000)\n").encode()
        attempt = self.evidence / "attempt"
        outputs = inspection.output_paths(attempt)
        roles = {"node": str(self.node), "python": str(self.python), "ldd": "/usr/bin/ldd", "inspector_interpreter": "/fixture/bin/sh",
                 "elf_interpreter": self.loader, "loader_configuration": ["/fixture/ld.so.cache"],
                 "shared_libraries": [self.library], "inspector_runtime": ["/fixture/bin/utility", str(self.git)]}
        named = {roles[key] for key in inspection.ROLE_SCALARS}
        for key in inspection.ROLE_LISTS:
            named.update(roles[key])
        files = {name: {"sha256": "c" * 64, "size_bytes": 12, "mode": "0o644"} for name in named}
        files[str(self.node)] = deepcopy(PINNED_NODE)
        files[str(self.git)] = file_binding(self.git)
        author = {"entry_point": str(self.source / inspection.ENTRY_POINT), "source_descriptor": descriptor(self.source / inspection.ENTRY_POINT),
                  "python_descriptor": descriptor(self.python), "python_version": "3.12.8", "runtime_inventory": self.dummy,
                  "metadata_inventory": self.dummy, "git_descriptor": descriptor(self.git), "source_commands": inspection.source_commands(self.source_value)}
        self.plan = {"schema": "ontokin.current-host-readback-inspection-plan/0.1.0", "contract": "ontokin.current-host-readback/0.1.0",
            "source": self.source_value, "author": author,
            "runtime": {"executable": str(self.node), "version": "v24.22.1", "candidate": deepcopy(PINNED_NODE),
                        "source_archive": {"path": str(self.archive), "sha256": "100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5", "size_bytes": 45186132, "mode": "0o600"}, "install_receipt": self.dummy},
            "dependencies": {"root": str(self.dependencies), "inventory": self.dummy, "install_receipt": self.dummy},
            "host_static": {"platform": self.platform, "files": files,
                            "aliases": {name: {"resolved_path": name, "symlink": False, "link_target": None} for name in named},
                            "roles": roles, "resolution": {"profile": "linux-glibc-declared-closure-v1", "images": [], "needed_edges": [],
                            "loader_inputs": [], "search_directories": [], "inspector_commands": {}, "ignored_kernel_rows": ["linux-vdso.so.1"], "rationale": self.dummy}, "path_guards": []},
            "environment": deepcopy(PINNED_ENV), "commands": [],
            "evidence": {"parent": str(self.evidence), "attempt_root": str(attempt), "ancestor_identities": inspection._ancestors(self.evidence),
                         "outputs": outputs, "outer_capture": {"authority": self.dummy, "log": descriptor(put(base / "outer.log", b"outer-start\n"))}},
            "limits": deepcopy(inspection.LIMITS)}
        for name in ("node_version", "shared_libraries"):
            self.plan["commands"].append({"id": name, "argv": [str(self.node), "--version"] if name == "node_version" else ["/usr/bin/ldd", str(self.node)],
                "cwd": str(attempt / name), "label": "host-node-version" if name == "node_version" else "host-shared-libraries",
                "timeout_ms": 5000, "active_work_ms": 3000, "cleanup_ms": 2000, "expected_direct_starts": 1,
                "stdout_predicate": "v24.22.1\n" if name == "node_version" else "linux-glibc-declared-closure-v1", "stderr_predicate": ""})
        self.plan_path = base / "plan.json"
        self.save_plan()

    def save_plan(self):
        self.plan_descriptor = json_file(self.plan_path, self.plan)
        return self.plan_descriptor["sha256"]

    def validated(self, controller=None):
        helpers = (None, controller or self.supervisor, None, self.rename, None)
        runtime = {"files": {}, "aliases": {}, "extension_files": []}
        metadata = {"packages": {"package" + str(index): "1.0" for index in range(7)}, "expected_resolution": self.resolution,
                    "input_snapshot": {str(self.drift): {"identity": list(inspection._identity(self.drift.lstat())), "resolved": str(self.drift)}},
                    "paths": [], "extra_paths": []}
        source_outputs = [str(self.source), self.plan["source"]["commit"], self.plan["source"]["tree"], "", ""]
        source_reads = [{**row, "stdout": output, "completed": True}
                        for row, output in zip(self.plan["author"]["source_commands"], source_outputs)]
        return inspection.ValidatedPlan(self.plan, self.plan_descriptor, source_reads, {}, helpers, runtime, metadata)


class FakeClock:
    def __init__(self, *, total_ms):
        if total_ms != 5000:
            raise AssertionError("Changed command budget")
        self.started, self.end = 1000.0, 1005.0
        self.total_ms, self.elapsed = total_ms, 100.0
        self.failure = None

    def check(self, stage_end=None):
        if stage_end is not None and stage_end != 1003.0:
            raise AssertionError("Changed active-work deadline")
        if self.failure:
            raise self.failure

    def elapsed_ms(self):
        return self.elapsed


class MockedSupervisor:
    """One fixture callback per call unless a predeclared fault says otherwise."""
    Clock = FakeClock

    def __init__(self, fixture, stop_type, variant=None, mutation=None):
        self.fixture, self.Stop, self.variant, self.mutation = fixture, stop_type, variant, mutation
        self.calls, self.starts, self.raw_receipts = [], [], []
        self.last_failure = None

    def run_process(self, argv, *, stage, label, clock, stage_end, env, on_started, cancel_after_ms):
        if env != PINNED_ENV or stage_end != clock.started + 3 or cancel_after_ms is not None:
            raise AssertionError("Changed fixed supervisor arguments")
        name = "node_version" if label == "host-node-version" else "shared_libraries"
        self.calls.append(name)
        if self.variant in ("HI14-C", "HI18-F"):
            raise OSError("mocked lost launch-to-callback/final-receipt window")
        output = b"v24.22.1\n" if name == "node_version" else self.fixture.ldd_stdout
        error = b""
        process = {"argv": list(argv), "cwd": str(stage), "environment": deepcopy(env), "label": label,
                   "start_monotonic": 1000.0, "pid": 4241 + len(self.calls), "process_group": 4241 + len(self.calls),
                   "returncode": 0, "observed_log_bytes": len(output), "retained_log_bytes": len(output),
                   "cleanup": {"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 1.0},
                   "handles_closed": True, "error": None, "end_monotonic": 1000.1}
        group_kind = (self.variant or "").removeprefix("HI17-C-start-group-")
        if group_kind in ("bool", "float", "int"):
            process["pid"] = process["process_group"] = 1
        start = deepcopy(process)
        start.update(returncode=None, cleanup=None, handles_closed=False, observed_log_bytes=0, retained_log_bytes=0)
        start.pop("end_monotonic")
        if group_kind in ("bool", "float", "int"):
            start["process_group"] = True if group_kind == "bool" else 1.0 if group_kind == "float" else 1
        self.starts.append(deepcopy(start))
        callback_error = None
        try:
            if self.variant == "HI15-E":
                clock.failure = self.Stop("MOCK-TIMEOUT", "Mocked callback timeout", "TIMEOUT")
            on_started(start)
            if self.variant == "HI14-D":
                another = deepcopy(start)
                another["pid"] += 100
                another["process_group"] += 100
                self.starts.append(deepcopy(another))
                on_started(another)
            if self.variant == "HI14-B":
                raise ValueError("mocked unrelated callback boundary failure")
        except BaseException as exc:
            callback_error = exc
        clock.failure = None
        if self.mutation:
            output, error, process = self.mutation(name, output, error, process)
        if self.variant == "HI17-D":
            raise OSError("mocked lost final supervisor write")
        put(stage / (label + ".stdout.log"), output)
        put(stage / (label + ".stderr.log"), error)
        raw = canonical(process)
        if self.variant == "HI18-G-partial":
            raw = raw[:37]
        elif self.variant == "HI18-G-disagree":
            changed = deepcopy(process)
            changed["returncode"] = 8
            raw = canonical(changed)
        put(stage / (label + ".process.json"), raw)
        self.raw_receipts.append((stage / (label + ".process.json"), deepcopy(process), raw))
        if self.variant in ("HI15-A", "HI15-E", "HI11-C") or callback_error:
            timed_out = (self.variant or "").startswith("HI15")
            cause = self.Stop("MOCK-TIMEOUT" if timed_out else "MOCK-FAILURE",
                              str(callback_error) if callback_error else "Mocked supervisor failure",
                              "TIMEOUT" if timed_out else "REJECTED")
            cause.process_record = process
            self.last_failure = cause
            raise cause
        return process


class ClosureFixture:
    """Inert ELF/script/config closure; /etc file access is redirected to fixtures."""
    def __init__(self, fixture):
        self.fixture = fixture
        self.root = fixture.base / "closure"
        self.lib = self.root / "lib"; self.lib.mkdir(parents=True)
        self.loader = self.lib / "ld-linux-x86-64.so.2"
        self.library = self.lib / "libc.so.6"
        self.shell = self.root / "shell"
        self.git = self.root / "git"
        self.node = self.root / "node"
        self.python = self.root / "python"
        self.utility = self.root / "utility"
        self.script = self.root / "ldd"
        self.conf = put(self.root / "ld.so.conf", (str(self.lib) + "\n").encode())
        self.cache = put(self.root / "ld.so.cache", b"independently reviewed opaque cache fixture")
        self.preload = self.root / "ld.so.preload"
        self.mapping = {"/etc/ld.so.conf": self.conf, "/etc/ld.so.cache": self.cache, "/etc/ld.so.preload": self.preload}
        self.metadata = {}
        for path in (self.loader, self.library):
            self.metadata[str(path)] = synthetic_elf(path)
        for path in (self.shell, self.git, self.node, self.python, self.utility):
            self.metadata[str(path)] = synthetic_elf(path, interpreter=str(self.loader), needed=("libc.so.6",))
        put(self.script, ("#!" + str(self.shell) + "\nRTLDLIST=\"" + str(self.loader) + "\"\n# inert script, never executed\n").encode(), 0o755)
        self.plan = deepcopy(fixture.plan)
        self.plan["author"]["git_descriptor"] = descriptor(self.git)
        self.plan["runtime"]["executable"] = str(self.node)
        roles = {"node": str(self.node), "python": str(self.python), "ldd": "/usr/bin/ldd", "inspector_interpreter": str(self.shell),
                 "elf_interpreter": str(self.loader), "loader_configuration": ["/etc/ld.so.conf", "/etc/ld.so.cache"],
                 "shared_libraries": [str(self.library)], "inspector_runtime": [str(self.git), str(self.utility)]}
        aliases = {str(path): {"resolved_path": str(path), "symlink": False, "link_target": None}
                   for path in (self.node, self.python, self.shell, self.loader, self.library, self.git, self.utility)}
        for name, path in {"/usr/bin/ldd": self.script, "/etc/ld.so.conf": self.conf, "/etc/ld.so.cache": self.cache}.items():
            aliases[name] = {"resolved_path": str(path), "symlink": False, "link_target": None}
        files = {row["resolved_path"]: file_binding(Path(row["resolved_path"])) for row in aliases.values()}
        images, edges = [], []
        for name, metadata in self.metadata.items():
            mapping = {needed: str(self.library) for needed in metadata["needed"]}
            images.append({"file": descriptor(Path(name)), "metadata": metadata, "resolved_needed": mapping})
            edges.extend({"image": name, "soname": needed, "resolved_path": str(self.library)} for needed in metadata["needed"])
        self.resolution = {"profile": "linux-glibc-declared-closure-v1", "images": images, "needed_edges": edges,
            "loader_inputs": [{"path": name, "state": "file", "binding": file_binding(path), "includes": []}
                              for name, path in (("/etc/ld.so.conf", self.conf), ("/etc/ld.so.cache", self.cache))] +
                             [{"path": "/etc/ld.so.preload", "state": "absent", "parent": "/etc"}],
            "search_directories": [inspection._directory_entries(self.lib)],
            "inspector_commands": {"script": descriptor(self.script), "interpreter": descriptor(self.shell), "commands": [descriptor(self.utility)],
                                   "rtld_candidates": [{"path": str(self.loader), "state": "file", "binding": file_binding(self.loader)}]},
            "ignored_kernel_rows": ["linux-vdso.so.1"], "rationale": descriptor(put(self.root / "review.txt", b"Synthetic independent review fixture; no operational authority."))}
        self.plan["host_static"] = {"platform": fixture.platform, "roles": roles, "files": files, "aliases": aliases,
                                   "resolution": self.resolution, "path_guards": []}
        self.author_runtime = {"extension_files": [str(self.library)]}

    @contextmanager
    def mapped_files(self):
        original_read, original_bound = inspection._read_file, inspection._bound
        original_exists, original_symlink = Path.exists, Path.is_symlink
        def translate(path):
            return self.mapping.get(str(path), path)
        def read(path, *args, **kwargs):
            return original_read(translate(path), *args, **kwargs)
        def bound(path, *args, **kwargs):
            return original_bound(translate(path), *args, **kwargs)
        def exists(path):
            return original_exists(translate(path))
        def is_symlink(path):
            return original_symlink(translate(path))
        with patch.object(inspection, "_read_file", side_effect=read), patch.object(inspection, "_bound", side_effect=bound), \
             patch.object(Path, "exists", new=exists), patch.object(Path, "is_symlink", new=is_symlink):
            yield

    def check(self):
        with self.mapped_files():
            return inspection._check_resolution(self.plan, self.author_runtime)


class HostInspectionControls(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        retained = os.environ.get("ONTOKIN_HI_RETAIN_ROOT")
        if retained:
            self.base = Path(retained) / self._testMethodName
            self.base.mkdir(parents=True, exist_ok=False)
        else:
            self.temp = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="ontokin-hi-control-"))
            self.base = Path(self.temp)
        self.process_guards = []
        for name in ("Popen", "run", "check_output", "call", "check_call"):
            guard = self.stack.enter_context(patch.object(subprocess, name, side_effect=AssertionError("Actual process operation forbidden: " + name)))
            self.process_guards.append(guard)
        for name in ("system", "fork", "posix_spawn", "posix_spawnp", "killpg", "waitpid"):
            if hasattr(os, name):
                guard = self.stack.enter_context(patch.object(os, name, side_effect=AssertionError("Actual process operation forbidden: " + name)))
                self.process_guards.append(guard)
        self.real_supervisor = importlib.import_module("prototypes.static_tray_v01.supervisor")
        self.preparer = importlib.import_module("tools.prepare_current_host_readback")
        self.fixture = Fixture(self.base, self.preparer.rename_without_replacement, self.real_supervisor)

    def tearDown(self):
        for guard in self.process_guards:
            self.assertEqual(guard.call_count, 0, "A forbidden actual process operation was attempted")
        if os.environ.get("ONTOKIN_HI_RETAIN_ROOT"):
            rows = []
            for path in sorted(self.base.rglob("*")):
                info = path.lstat()
                row = {"relative_path": str(path.relative_to(self.base)), "device": info.st_dev, "inode": info.st_ino,
                       "mode": oct(stat.S_IMODE(info.st_mode)), "links": info.st_nlink, "size_bytes": info.st_size,
                       "mtime_ns": info.st_mtime_ns, "ctime_ns": info.st_ctime_ns}
                if path.is_symlink():
                    row.update(kind="symlink", target=os.readlink(path))
                elif stat.S_ISREG(info.st_mode):
                    digest = hashlib.sha256()
                    with path.open("rb") as stream:
                        for block in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(block)
                    row.update(kind="file", sha256=digest.hexdigest())
                else:
                    row["kind"] = "directory" if stat.S_ISDIR(info.st_mode) else "special"
                rows.append(row)
            json_file(self.base.parent / "manifests" / (self._testMethodName + ".json"),
                      {"test": self._testMethodName, "root": str(self.base), "actual_process_operations": 0, "entries": rows})

    def refuses(self, code, function, *args, **kwargs):
        with self.assertRaises(inspection.HostInspectionError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    @contextmanager
    def source_root(self):
        with patch.object(inspection, "ROOT", self.fixture.source):
            yield

    def shape(self, plan=None):
        with self.source_root():
            return inspection._plan_shape(self.fixture.plan if plan is None else plan)

    def call_plan(self, raw=None, digest=None):
        if raw is not None:
            put(self.fixture.plan_path, raw)
        actual = file_binding(self.fixture.plan_path)["sha256"]
        with self.source_root(), patch.object(inspection, "_load_helpers", side_effect=AssertionError("Unauthenticated bootstrap")) as helper:
            try:
                return inspection.validate_inspection_plan(self.fixture.plan_path, digest if digest is not None else actual)
            finally:
                self.assertFalse(helper.called, "A malformed input reached project bootstrap")

    @contextmanager
    def observation(self, variant=None, mutation=None, recheck=None, launch=None, write_fault=None):
        controller = MockedSupervisor(self.fixture, self.real_supervisor.Stop, variant, mutation)
        validated = self.fixture.validated(controller)
        original_write = inspection._EvidenceStore.write
        writes = []
        def writing(store, path, value, **kwargs):
            writes.append(str(path))
            if write_fault:
                write_fault(store, Path(path), value, writes)
            return original_write(store, path, value, **kwargs)
        with ExitStack() as stack:
            stack.enter_context(patch.object(inspection, "validate_inspection_plan", return_value=validated))
            stack.enter_context(patch.object(inspection, "_recheck", side_effect=recheck or (lambda *a, **k: inspection._guard_receipt(validated))))
            stack.enter_context(patch.object(inspection, "_platform", return_value=self.fixture.platform))
            if launch:
                stack.enter_context(patch.object(inspection, "_launch_check", side_effect=launch))
            stack.enter_context(patch.object(inspection, "_EvidenceStore.write", new=writing))
            yield validated, controller, writes

    def observe(self):
        return inspection.inspect_host(self.fixture.plan_path, self.fixture.plan_descriptor["sha256"], observe=True)

    def assert_failed_observation(self, code, *, starts=1, unknown=False, state=None, **options):
        with self.observation(**options) as (validated, controller, writes):
            error = self.refuses(code, self.observe)
        self.assertEqual(len(controller.starts), starts)
        counts = error.refusal_record["actual_counts"]["direct_starts"]
        self.assertEqual(counts["exact"], None if unknown else starts)
        self.assertEqual(counts["observed_lower_bound"], starts)
        if state is not None:
            self.assertEqual(error.state, state)
        elif (options.get("variant") or "").startswith("HI18-G"):
            self.assertEqual(error.state, "REJECTED")
        elif unknown or code == "CHI-EVIDENCE" or options.get("variant") == "HI17-D":
            self.assertEqual(error.state, "UNKNOWN")
        elif options.get("variant") in ("HI15-A", "HI15-E"):
            self.assertEqual(error.state, "TIMEOUT")
        else:
            self.assertEqual(error.state, "REJECTED")
        for name in ("node_version", "shared_libraries"):
            retained = Path(self.fixture.plan["evidence"]["outputs"][name]["postflight"])
            if retained.exists():
                record = json.loads(retained.read_bytes())
                expected = "UNKNOWN" if unknown and name == "node_version" else "OBSERVED_ONE" if any(row["label"] == ("host-node-version" if name == "node_version" else "host-shared-libraries") for row in controller.starts) else "PROVEN_ZERO"
                self.assertEqual(record["start_count_state"], expected)
        self.assertFalse(error.refusal_record["evidence_finalized"])
        self.assertFalse(Path(self.fixture.plan["evidence"]["outputs"]["completion"]).exists())
        if starts < 2:
            self.assertNotIn("shared_libraries", controller.calls)
        for path, process, raw in controller.raw_receipts:
            self.assertEqual(path.read_bytes(), raw, "Raw supervisor bytes were repaired or replaced")
        return error, controller

    def reset_observation(self):
        # Each subcase gets a distinct never-reused evidence root. No failed
        # attempt is deleted or repaired during the test method.
        count = len(list(self.fixture.evidence.iterdir()))
        json_file(self.base / "plan-history" / ("before-reset-" + str(count) + ".json"), self.fixture.plan)
        attempt = self.fixture.evidence / ("attempt-" + str(count + 1))
        self.fixture.plan["evidence"]["attempt_root"] = str(attempt)
        self.fixture.plan["evidence"]["outputs"] = inspection.output_paths(attempt)
        for command in self.fixture.plan["commands"]:
            command["cwd"] = str(attempt / command["id"])
        self.fixture.save_plan()

    def run_control(self, control):
        group, variant = control.split("-")
        return getattr(self, "case_" + group)(variant)

    def case_HI01(self, variant):
        f = self.fixture
        if variant in ("A", "B"):
            args = [] if variant == "A" else ["--plan", str(f.plan_path)]
            with redirect_stderr(io.StringIO()) as capture:
                self.assertEqual(inspection.main(args), 1)
            self.assertEqual(json.loads(capture.getvalue())["error"]["code"], "CHI-PLAN")
        elif variant == "C":
            self.refuses("CHI-PLAN", self.call_plan, digest="d" * 64)
        elif variant == "D":
            f.plan["schema"] = "ontokin.c271.p07-qualification-design/1"
            self.refuses("CHI-PLAN", self.call_plan, canonical(f.plan))
        elif variant == "E":
            for kind in ("extra", "missing"):
                plan = deepcopy(f.plan)
                if kind == "extra":
                    plan["unexpected"] = True
                else:
                    plan.pop("author")
                with self.subTest(kind=kind):
                    self.refuses("CHI-PLAN", self.call_plan, canonical(plan))
        elif variant == "F":
            for value in (None, "UNRESOLVED_TEMPLATE"):
                plan = deepcopy(f.plan)
                plan["schema"] = value
                with self.subTest(value=value):
                    self.refuses("CHI-PLAN", self.call_plan, canonical(plan))
        elif variant == "G":
            self.refuses("CHI-PLAN", inspection.validate_inspection_plan, "relative.json", "d" * 64)
            plan = deepcopy(f.plan)
            plan["source"]["inventory"]["path"] = "relative.json"
            self.refuses("CHI-PLAN", self.call_plan, canonical(plan))
            with redirect_stderr(io.StringIO()) as capture:
                self.assertEqual(inspection.main(["--plan", str(f.plan_path), "--plan-sha256", "d" * 64, "--force"]), 1)
            self.assertEqual(json.loads(capture.getvalue())["error"]["code"], "CHI-PLAN")
        else:
            for key in ("raw", "committed", "unexpected"):
                plan = deepcopy(f.plan)
                pair = plan["evidence"]["outputs"]["node_version"]["supervisor_outcome"]
                if key == "unexpected":
                    pair[key] = str(f.base / "extra")
                else:
                    pair.pop(key)
                with self.subTest(key=key):
                    self.refuses("CHI-PLAN", self.call_plan, canonical(plan))
        self.assertFalse(Path(f.plan["evidence"]["attempt_root"]).exists())

    def case_HI02(self, variant):
        plan = deepcopy(self.fixture.plan)
        if variant == "A":
            original = self.fixture.plan_descriptor["sha256"]
            plan["author"]["python_version"] = "3.12.9"
            self.refuses("CHI-PLAN", self.call_plan, canonical(plan), original)
        else:
            for key in ("approved", "expected-plan-digest", "signature"):
                changed = deepcopy(plan)
                changed[key] = True
                with self.subTest(key=key):
                    self.refuses("CHI-PLAN", self.call_plan, canonical(changed))

    def case_HI03(self, variant):
        f = self.fixture
        if variant == "A":
            link = f.base / "linked-plan"
            link.symlink_to(f.plan_path)
            self.refuses("CHI-PLAN", inspection.validate_inspection_plan, link, f.plan_descriptor["sha256"])
        elif variant == "B":
            fifo = f.base / "fifo"
            os.mkfifo(fifo)
            self.refuses("CHI-PLAN", inspection.validate_inspection_plan, fifo, "d" * 64)
            self.refuses("CHI-PLAN", inspection.validate_inspection_plan, f.base, "d" * 64)
        elif variant == "C":
            os.link(f.plan_path, f.base / "hardlink")
            self.refuses("CHI-PLAN", inspection.validate_inspection_plan, f.plan_path, f.plan_descriptor["sha256"])
        elif variant == "D":
            self.assertEqual(inspection._decode(b'{"schema":1}'), {"schema": 1})
            self.assertEqual(inspection._decode(b'{"x":{"a":1}}'), {"x": {"a": 1}})
            for raw in (b'{"schema":1,"schema":2}', b'{"x":{"a":1,"a":2}}'):
                self.refuses("CHI-PLAN", inspection._decode, raw)
        elif variant == "E":
            self.refuses("CHI-PLAN", self.call_plan, b'{"bad":"\xff"}')
        elif variant == "F":
            self.assertEqual(inspection._decode(b'{"bad":1}'), {"bad": 1})
            for token in (b"NaN", b"Infinity", b"-Infinity", b"1e999"):
                self.refuses("CHI-PLAN", inspection._decode, b'{"bad":' + token + b"}")
        elif variant == "G":
            self.refuses("CHI-PLAN", self.call_plan, b"x" * (16 * 1024 * 1024 + 1))
        elif variant == "H":
            original_read = os.read
            mutated = False
            def synchronized(fd, size):
                nonlocal mutated
                value = original_read(fd, size)
                if not mutated:
                    mutated = True
                    f.plan_path.write_bytes(b"{}"); f.plan_path.chmod(0o600)
                return value
            with patch.object(inspection.os, "read", side_effect=synchronized):
                self.refuses("CHI-PLAN", inspection._read_file, f.plan_path, 16 * 1024 * 1024)
            self.assertTrue(mutated)
        else:
            plan = deepcopy(f.plan)
            plan["source"]["inventory"]["size_bytes"] = True
            self.refuses("CHI-PLAN", self.call_plan, canonical(plan))
            self.refuses("CHI-PLAN", self.call_plan, json.dumps(f.plan, indent=2).encode())
            plan = deepcopy(f.plan); plan["limits"]["direct_starts"] = 2.0
            self.refuses("CHI-PLAN", self.call_plan, canonical(plan))

    def git_control(self, *, outputs=None, plan=None):
        f = self.fixture
        selected = deepcopy(f.plan) if plan is None else plan
        expected = [str(f.source), "a" * 40, "b" * 40, "", ""] if outputs is None else outputs
        driver = SimpleNamespace(git_read=Mock(side_effect=expected), git_environment=lambda root: inspection._git_environment(root))
        with self.source_root(), patch.object(inspection, "_selected_git", return_value=f.git), patch.object(inspection, "_git_state", return_value={}):
            try:
                return inspection._check_git(selected, (None, None, driver), check=inspection._Deadline(60000))
            finally:
                self.assertLessEqual(driver.git_read.call_count, 5)
                for call in driver.git_read.call_args_list:
                    self.assertLessEqual(call.kwargs["timeout"], 5)

    def case_HI04(self, variant):
        f = self.fixture
        if variant == "A":
            plan = deepcopy(f.plan); plan["source"]["root"] = str(f.base / "other")
            self.refuses("CHI-SOURCE", self.shape, plan)
        elif variant == "B":
            for index in (1, 2):
                rows = [str(f.source), "a" * 40, "b" * 40, "", ""]
                rows[index] = "c" * 40
                self.refuses("CHI-SOURCE", self.git_control, outputs=rows)
        elif variant == "C":
            for name in (inspection.ENTRY_POINT, "prototypes/static_tray_v01/current_host_readback_v01.py",
                         "prototypes/static_tray_v01/supervisor.py", "tools/prepare_current_host_readback.py"):
                path = f.source / name
                before = path.read_bytes()
                for missing in (False, True):
                    with self.subTest(name=name, missing=missing):
                        if missing:
                            path.unlink()
                        else:
                            put(path, b"changed source")
                        with self.source_root():
                            self.refuses("CHI-SOURCE", inspection._check_source_files, f.plan)
                        put(path, before)
        elif variant == "D":
            for extra in (False, True):
                value = deepcopy(f.inventory)
                if extra:
                    value["files"]["extra.py"] = file_binding(f.drift)
                else:
                    value["files"].pop("tools/check_local.py")
                plan = deepcopy(f.plan)
                plan["source"]["inventory"] = json_file(f.base / ("inventory-extra" if extra else "inventory-missing"), value)
                with self.source_root():
                    self.refuses("CHI-SOURCE", inspection._check_source_files, plan)
        elif variant == "E":
            for index, output in ((3, " M tests/changed.py"), (4, "untracked.py\0")):
                rows = [str(f.source), "a" * 40, "b" * 40, "", ""]
                rows[index] = output
                self.refuses("CHI-SOURCE", self.git_control, outputs=rows)
        else:
            for mutation in ("argv", "extra", "timeout") if variant == "G" else ("argv", "extra"):
                plan = deepcopy(f.plan)
                if mutation == "argv":
                    plan["author"]["source_commands"][0]["argv"][-1] = "fetch"
                elif mutation == "extra":
                    plan["author"]["source_commands"].append(deepcopy(plan["author"]["source_commands"][0]))
                else:
                    plan["author"]["source_commands"][0]["timeout_ms"] = 5001
                self.refuses("CHI-SOURCE", self.git_control, plan=plan)

    def case_HI05(self, variant):
        f = self.fixture
        if variant == "A":
            for key, value in (("sha256", "d" * 64), ("size_bytes", 126951513), ("mode", "0o644"), ("size_bytes", 126951512.0)):
                plan = deepcopy(f.plan); plan["runtime"]["candidate"][key] = value
                code = "CHI-PLAN" if type(value) is float else "CHI-RUNTIME"
                self.refuses(code, self.shape, plan)
        elif variant == "B":
            for value in ("relative/node", str(f.source / "node")):
                plan = deepcopy(f.plan); plan["runtime"]["executable"] = value
                self.refuses("CHI-RUNTIME", self.shape, plan)
            link = f.base / "node-link"; link.symlink_to(f.node)
            plan = deepcopy(f.plan); plan["runtime"]["executable"] = str(link)
            self.refuses("CHI-RUNTIME", self.shape, plan)
            os.link(f.node, f.base / "node-hardlink")
            self.refuses("CHI-RUNTIME", inspection._bound, f.node, file_binding(f.node), category="RUNTIME")
        elif variant == "C":
            plan = deepcopy(f.plan); plan["runtime"]["version"] = "v24.22.0"
            self.refuses("CHI-RUNTIME", self.shape, plan)
        elif variant == "D":
            for key, value in (("sha256", "e" * 64), ("size_bytes", 45186133)):
                plan = deepcopy(f.plan); plan["runtime"]["source_archive"][key] = value
                self.refuses("CHI-RUNTIME", self.shape, plan)
        else:
            selected = {"purpose": "selected-node", "source": deepcopy(f.plan["source"]), "report": str(f.base / "install-report.json")}
            selected["source"]["root"] = str(f.base / "wrong-source")
            report = {"schema": "ontokin.current-host-readback-install-result/0.1.0", "passed": True, "state": "ALREADY_PRESENT_EXACT"}
            receipt = {"schema": "ontokin.current-host-readback-inspection-installation/0.1.0",
                       "plan": json_file(f.base / "install-plan.json", selected), "report": json_file(f.base / "install-report.json", report)}
            self.refuses("CHI-RUNTIME", inspection._check_installation, json_file(f.base / "install-index.json", receipt), f.plan,
                         "selected-node", (None, None, None, None, SimpleNamespace(_plan_shape=lambda value: None)))

    def case_HI12(self, variant):
        outputs = {"A": [(b"v24.22.0\n", b"")], "B": [(b"v24.22.1\nextra\n", b""), (b"v24.22.1", b""),
                    (b" v24.22.1\n", b""), (b"v24.22.1 \n", b"")], "C": [(b"v24.22.1\n", b"warning\n")],
                   "D": [(b"\xff\n", b""), (b"v24.22.1\n", b"\xff")]}[variant]
        for output, error in outputs:
            with self.subTest(output=output, error=error):
                def mutate(name, oldout, olderr, process):
                    process["observed_log_bytes"] = process["retained_log_bytes"] = len(output) + len(error)
                    return output, error, process
                self.assert_failed_observation("CHI-OUTPUT", mutation=mutate)
                self.reset_observation()

    def case_HI13(self, variant):
        valid = self.fixture.ldd_stdout
        library, loader = self.fixture.library.encode(), self.fixture.loader.encode()
        cases = {
            "A": [(b"libc.so.6 => not found\n", b""), (b"statically linked\n", b""), (b"not a dynamic executable\n", b"")],
            "B": [(valid, b"warning\n"), (valid, b"not found\n")],
            "C": [(b"", b""), (valid + b"\n", b""), (valid.replace(library, b"relative/libc.so.6"), b""),
                  (valid.replace(b"(0x7f1000)", b"(0xZZ)"), b""), (valid.replace(b"(0x7f1000)", b"0x7f1000)"), b""), (valid + b"warning\n", b"")],
            "D": [(valid + b"libc.so.6 => " + library + b" (0x7f1)\n", b""),
                  (valid + b"other.so => " + library + b" (0x7f2)\n", b""),
                  (valid + loader + b" (0x7f3)\n", b""), (valid + b"linux-vdso.so.1 (0x7f4)\n", b"")],
            "E": [(b"\n".join(valid.split(b"\n")[:-2]) + b"\n", b""),
                  (valid.splitlines(keepends=True)[0] + valid.splitlines(keepends=True)[2], b""),
                  (valid + b"libnew.so => /fixture/lib/new.so (0x1)\n", b"")],
            "F": [(valid.replace(b"linux-vdso.so.1", b"linux-gate.so.1"), b""), (valid.replace(library, b"/fixture/lib/with space"), b""),
                  (valid.replace(library, b"/fixture/lib/../lib/libc.so.6"), b""), (valid.replace(library, library + b"\0"), b""), (valid + b"\xff\n", b"")]}
        if variant == "G":
            def mutation(name, output, error, process):
                if name == "shared_libraries":
                    output += b"new.so => /fixture/lib/new.so (0x99)\n"
                    process["observed_log_bytes"] = process["retained_log_bytes"] = len(output)
                return output, error, process
            self.assert_failed_observation("CHI-OUTPUT", starts=2, mutation=mutation)
        else:
            for output, error in cases[variant]:
                before = (output, error)
                self.refuses("CHI-OUTPUT", inspection.parse_ldd_output, output, error, self.fixture.resolution)
                self.assertEqual((output, error), before)
            if variant == "F":
                invalid = deepcopy(self.fixture.resolution); invalid["vdso"] = "linux-vdso.so.1"
                self.refuses("CHI-OUTPUT", inspection.parse_ldd_output, valid, b"", invalid)

    def case_HI14(self, variant):
        if variant == "A":
            def before(*args):
                raise inspection.HostInspectionError("PROCESS", "Frozen prelaunch refusal", state="NO_START")
            self.assert_failed_observation("CHI-PROCESS", starts=0, state="NO_START", launch=before)
        elif variant == "B":
            self.assert_failed_observation("CHI-PROCESS", variant="HI14-B")
        elif variant == "C":
            self.assert_failed_observation("CHI-PROCESS", starts=0, unknown=True, variant="HI14-C")
        else:
            for later in (None, "drift", "outcome", "failure"):
                if later is not None:
                    self.new_fixture("multiple-then-" + later)
                checks = []
                def recheck(validated, **kwargs):
                    checks.append(1)
                    if later == "drift" and len(checks) == 3:
                        raise inspection.HostInspectionError("DRIFT", "Frozen later postflight failure")
                    return inspection._guard_receipt(validated)
                def write_fault(store, path, value, writes):
                    if later == "outcome" and path.name == "supervisor-outcome.json" or later == "failure" and path.name == "failure.json":
                        raise inspection.HostInspectionError("EVIDENCE", "Frozen later persistence failure", state="UNKNOWN")
                with self.observation(variant="HI14-D", recheck=recheck, write_fault=write_fault) as (_, controller, writes):
                    error = self.refuses("CHI-DRIFT" if later == "drift" else "CHI-EVIDENCE" if later in ("outcome", "failure") else "CHI-PROCESS", self.observe)
                self.assertEqual(len(controller.starts), 2)
                self.assertEqual(error.state, "UNKNOWN" if later in ("outcome", "failure") else "REJECTED")
                self.assertNotIn("shared_libraries", controller.calls)
                self.assertEqual(error.refusal_record["actual_counts"]["direct_starts"], {"exact": None, "observed_lower_bound": 2})
                anomaly = error.details["contract_violation"]
                self.assertEqual(anomaly["callback_receipts"], controller.starts)
                self.assertEqual(anomaly["observed_distinct_start_count"], {"exact": 2, "observed_lower_bound": 2})
                self.assertEqual(anomaly["observed_start_lower_bound"], 2)
                self.assertFalse(anomaly["normal_count_projection_available"])
                self.assertFalse(anomaly["total_direct_start_count_complete"])
                for path, process, raw in controller.raw_receipts:
                    self.assertEqual(path.read_bytes(), raw)
                self.assertFalse(Path(self.fixture.plan["evidence"]["outputs"]["node_version"]["postflight"]).exists())

    def case_HI15(self, variant):
        if variant in ("A", "E"):
            self.assert_failed_observation("CHI-PROCESS", variant="HI15-" + variant)
        elif variant == "B":
            for end in (1005.0001, 999.9):
                def mutation(name, output, error, process):
                    process["end_monotonic"] = end
                    return output, error, process
                self.assert_failed_observation("CHI-PROCESS", mutation=mutation)
                self.reset_observation()
        elif variant == "C":
            def mutation(name, output, error, process):
                process["cleanup"]["elapsed_ms"] = 2000.001
                return output, error, process
            self.assert_failed_observation("CHI-PROCESS", mutation=mutation)
        else:
            original = inspection._launch_check
            def timeout(validated, clock, stage_end):
                clock.failure = self.real_supervisor.Stop("MOCK-TIMEOUT", "Before launch", "TIMEOUT")
                return original(validated, clock, stage_end)
            error, _ = self.assert_failed_observation("CHI-PROCESS", starts=0, state="TIMEOUT", launch=timeout)
            self.assertEqual(error.state, "TIMEOUT")

    def case_HI16(self, variant):
        if variant == "A":
            def mutation(name, output, error, process):
                output = b"x" * (4 * 1024 * 1024 + 1)
                process["observed_log_bytes"] = process["retained_log_bytes"] = len(output)
                return output, error, process
            self.assert_failed_observation("CHI-OUTPUT", mutation=mutation)
        elif variant in ("B", "D"):
            values = (0, 10) if variant == "B" else (-1, True, 9.0, 4 * 1024 * 1024 + 1)
            for key in ("observed_log_bytes", "retained_log_bytes"):
                for value in values:
                    def mutation(name, output, error, process):
                        process[key] = value
                        return output, error, process
                    with self.subTest(key=key, value=value):
                        self.assert_failed_observation("CHI-OUTPUT", mutation=mutation)
                        self.reset_observation()
        else:
            validated = self.fixture.validated()
            store = inspection._EvidenceStore(validated)
            self.refuses("CHI-OUTPUT", store.write, self.fixture.plan["evidence"]["outputs"]["reserved"], {"text": "x" * (16 * 1024 * 1024)})
            # Escaped UTF-8 control characters can serialize beyond 8 MiB even
            # when raw capture is within 4 MiB. The accepted output predicate
            # is isolated here; the bounded serialization guard stays active.
            process = self.process_fixture()
            output = b"\x01" * (2 * 1024 * 1024)
            process["observed_log_bytes"] = process["retained_log_bytes"] = len(output)
            command = deepcopy(self.fixture.plan["commands"][1])
            process.update(argv=command["argv"], cwd=command["cwd"], label=command["label"])
            with patch.object(inspection, "parse_ldd_output", return_value={"fixture_only": True}):
                self.refuses("CHI-OUTPUT", inspection._inspection, process, command, output, b"", FIXED_TIME, FIXED_FINISH, self.fixture.resolution)

    def process_fixture(self):
        command = self.fixture.plan["commands"][0]
        return {"argv": command["argv"], "cwd": command["cwd"], "environment": deepcopy(PINNED_ENV), "label": command["label"],
                "start_monotonic": 1000.0, "pid": 4242, "process_group": 4242, "returncode": 0,
                "observed_log_bytes": 9, "retained_log_bytes": 9, "cleanup": {"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 1.0},
                "handles_closed": True, "error": None, "end_monotonic": 1000.1}

    def case_HI17(self, variant):
        if variant == "D":
            self.assert_failed_observation("CHI-PROCESS", variant="HI17-D")
            return
        if variant == "E":
            cases = [("2026-11-21T00:00:00", FIXED_FINISH), (FIXED_FINISH, FIXED_TIME),
                     (FIXED_TIME, "2999-01-01T00:00:00+00:00"), (FIXED_TIME, "2026-11-21T00:00:10+00:00")]
            for start, end in cases:
                with patch.object(inspection, "_utc", side_effect=[start, start, end]):
                    self.assert_failed_observation("CHI-PROCESS")
                self.reset_observation()
            return
        changes = {"A": [("returncode", 1), ("error", {"reason": "mock failure"})],
                   "B": [("handles_closed", False), ("cleanup.passed", False), ("cleanup.process_group_absent", False), ("cleanup.reaped", False)],
                   "C": [("pid", None), ("pid", "MISSING"), ("process_group", 99), ("end_monotonic", "MISSING"),
                         ("argv", ["/wrong"]), ("environment", {"EVIL": "1"}), ("cwd", "/wrong"), ("label", "wrong")]}[variant]
        for key, value in changes:
            def mutation(name, output, error, process):
                target = process
                if "." in key:
                    parent, leaf = key.split("."); target = process[parent]
                else:
                    leaf = key
                if value == "MISSING":
                    target.pop(leaf)
                else:
                    target[leaf] = value
                return output, error, process
            with self.subTest(key=key, value=value):
                self.assert_failed_observation("CHI-PROCESS", mutation=mutation)
                self.reset_observation()

    def case_HI18(self, variant):
        if variant == "A":
            for name in ("reserved.json", "preflight.json", "intent.json"):
                for operation in ("write", "file-fsync", "directory-fsync"):
                    with self.io_failure(name, operation):
                        self.assert_failed_observation("CHI-EVIDENCE", starts=0)
                    self.reset_observation()
        elif variant in ("B", "C"):
            names = ("started.json",) if variant == "B" else ("supervisor-outcome.json", "postflight.json", "failure.json")
            for name in names:
                def fault(store, path, value, writes):
                    if path.name == name:
                        raise inspection.HostInspectionError("EVIDENCE", "Mocked post-start evidence failure", state="UNKNOWN")
                options = {"write_fault": fault}
                if name == "failure.json":
                    options["variant"] = "HI15-A"
                self.assert_failed_observation("CHI-EVIDENCE", **options)
                self.reset_observation()
            if variant == "C":
                for name in ("supervisor-outcome.json", "postflight.json", "failure.json"):
                    with self.io_failure(name, "directory-fsync"):
                        self.assert_failed_observation("CHI-EVIDENCE", variant="HI15-A" if name == "failure.json" else None)
                    self.reset_observation()
        elif variant == "D":
            for state in ("equal", "conflict", "absent"):
                validated = self.fixture.validated()
                store = inspection._EvidenceStore(validated)
                path = Path(self.fixture.plan["evidence"]["outputs"]["reserved"])
                calls = []
                def uncertain(source, destination):
                    calls.append((source, destination))
                    if state == "equal":
                        self.preparer.rename_without_replacement(source, destination)
                    elif state == "conflict":
                        put(destination, b"another writer")
                    raise OSError(5, "Lost rename reply")
                store.rename = uncertain
                error = self.refuses("CHI-EVIDENCE", store.write, path, {"frozen": True})
                self.assertEqual(len(calls), 1)
                self.assertIn("source_after", error.details)
                if state == "conflict":
                    self.assertEqual(path.read_bytes(), b"another writer")
                self.reset_observation()
        elif variant == "E":
            for operation in ("write", "file-fsync", "directory-fsync"):
                with self.io_failure("completion.json", operation):
                    with self.observation() as (validated, controller, writes):
                        error = self.refuses("CHI-EVIDENCE", self.observe)
                self.assertEqual(len(controller.starts), 2)
                self.assertEqual(error.state, "UNKNOWN")
                self.assertFalse(error.refusal_record["evidence_finalized"])
                self.assertEqual(error.refusal_record["actual_counts"]["direct_starts"]["exact"], 2)
                pending = json.loads(Path(self.fixture.plan["evidence"]["outputs"]["result"]).read_bytes())
                self.assertEqual(pending["state"], "PENDING_COMPLETION")
                self.assertFalse(pending["evidence_finalized"])
                if operation == "directory-fsync":
                    self.assertTrue(Path(self.fixture.plan["evidence"]["outputs"]["completion"]).exists())
                    with patch.object(inspection, "_validate", return_value=validated):
                        retained = inspection.reconcile_attempt(self.fixture.plan_path, self.fixture.plan_descriptor["sha256"], self.fixture.plan["evidence"]["attempt_root"])
                    self.assertEqual(retained["state"], "OBSERVED_UNAPPROVED_AS_RECORDED")
                    self.assertEqual(retained["durability_state"], "UNKNOWN")
                    self.assertFalse(retained["evidence_finalized"])
                    self.assertFalse(retained["approved"])
                self.reset_observation()
        elif variant == "F":
            def fault(store, path, value, writes):
                if path.name in ("failure.json", "supervisor-outcome.json"):
                    raise inspection.HostInspectionError("EVIDENCE", "Mocked unavailable disk", state="UNKNOWN")
            self.assert_failed_observation("CHI-EVIDENCE", starts=0, unknown=True, variant="HI18-F", write_fault=fault)
        else:
            for value in ("HI18-G-partial", "HI18-G-disagree"):
                self.assert_failed_observation("CHI-EVIDENCE", variant=value)
                self.reset_observation()

    def case_HI19(self, variant):
        f = self.fixture
        validated = f.validated()
        store = inspection._EvidenceStore(validated)
        outputs = f.plan["evidence"]["outputs"]
        store.write(outputs["reserved"], {"schema": "ontokin.current-host-readback-inspection-reservation/0.1.0",
                    "plan": deepcopy(f.plan_descriptor), "attempt_root": f.plan["evidence"]["attempt_root"], "owned_directories": store.owned,
                    "state": "RESERVED", "expected_direct_starts": 2, "checker_starts": 0})
        command = f.plan["commands"][0]
        record = inspection._new_attempt(validated, command, None)
        store.write(outputs["node_version"]["intent"], record)
        if variant in ("C", "D"):
            started = self.process_fixture()
            started.pop("end_monotonic")
            started.update(returncode=None, cleanup=None, handles_closed=False, observed_log_bytes=0, retained_log_bytes=0)
            store.write(outputs["node_version"]["started"], {"schema": "ontokin.current-host-readback-inspection-start/0.1.0",
                "plan": deepcopy(f.plan_descriptor), "command_id": "node_version", "process": started, "observed_at_utc": FIXED_TIME})
        if variant == "A":
            failure = {"code": "CHI-PROCESS", "reason": "Frozen refusal before supervisor entry"}
            record.update(actual_direct_starts=0, observed_direct_starts=0, start_count_state="PROVEN_ZERO", state="NO_START", failure=failure, evidence_finalized=True)
            store.write(outputs["node_version"]["failure"], {"schema": "ontokin.current-host-readback-inspection-failure/0.1.0",
                "plan": deepcopy(f.plan_descriptor), "command_id": "node_version", "failure": failure,
                "process": None, "observed_start": None, "publications": []})
            store.write(outputs["node_version"]["postflight"], record)
        elif variant == "D":
            put(Path(outputs["node_version"]["postflight"]), b'{"partial":')
        elif variant == "E":
            put(Path(outputs["host"]), b"uncommitted destination exists")
        before = evidence_snapshot(Path(f.plan["evidence"]["attempt_root"]))
        with patch.object(inspection, "_validate", return_value=validated) as validate, patch.object(inspection._EvidenceStore, "write", side_effect=AssertionError("Reconcile wrote evidence")):
            result = inspection.reconcile_attempt(f.plan_path, f.plan_descriptor["sha256"], f.plan["evidence"]["attempt_root"])
        self.assertFalse(validate.call_args.kwargs["git_reads"])
        self.assertEqual(result["writes"], 0)
        self.assertEqual(result["new_preparation_starts"], 0)
        self.assertFalse(result["approved"])
        self.assertFalse(result["relaunch_permitted"])
        self.assertEqual(result["durability_state"], "UNKNOWN")
        self.assertFalse(result["evidence_finalized"])
        row = result["commands"][0]
        self.assertEqual(row["actual_direct_starts"], 0 if variant == "A" else 1 if variant in ("C", "D") else None)
        self.assertEqual(row["observed_direct_starts"], 1 if variant in ("C", "D") else 0)
        self.assertEqual(before, evidence_snapshot(Path(f.plan["evidence"]["attempt_root"])))
        self.assertEqual(row["start_count_state"], "PROVEN_ZERO" if variant == "A" else "OBSERVED_ONE" if variant in ("C", "D") else "UNKNOWN")
        self.assertEqual(row["state"], "NO_START" if variant == "A" else "UNKNOWN" if variant != "C" else "INCOMPLETE_OR_FAILED")
        if variant == "D":
            for kind in ("failure-disk", "missing-artifact"):
                self.new_fixture("reconcile-" + kind)
                package = self.historical_package()
                paths = self.fixture.plan["evidence"]["outputs"]["node_version"]
                if kind == "failure-disk":
                    put(Path(paths["failure"]), b'{"partial":')
                else:
                    Path(paths["stderr"]).unlink()
                self.refuses("CHI-EVIDENCE", self.reconcile_historical, package)
        if variant == "F":
            def changed_boot(*args, **kwargs):
                with patch.object(inspection, "_platform", return_value={**f.platform, "boot_id": "changed-boot"}):
                    inspection._check_host_static(f.plan)
            with patch.object(inspection.os, "killpg", return_value=None) as absent_group:
                with patch.object(inspection, "_validate", return_value=validated):
                    unknown = inspection.reconcile_attempt(f.plan_path, f.plan_descriptor["sha256"], f.plan["evidence"]["attempt_root"])
                self.assertEqual(unknown["state"], "UNKNOWN")
                self.assertEqual(unknown["current_process_group_state"], "NOT_OBSERVED")
                self.assertFalse(absent_group.called)
            with patch.object(inspection, "_validate", side_effect=changed_boot):
                self.refuses("CHI-EVIDENCE", inspection.reconcile_attempt, f.plan_path, f.plan_descriptor["sha256"], f.plan["evidence"]["attempt_root"])

    def new_fixture(self, name):
        self.fixture = Fixture(self.base / name, self.preparer.rename_without_replacement, self.real_supervisor)
        return self.fixture

    @contextmanager
    def io_failure(self, name, operation):
        original_write, write, fsync = inspection._EvidenceStore.write, os.write, os.fsync
        armed, injected = False, []
        def failing_write(fd, data):
            if armed and operation == "write":
                injected.append(operation)
                raise OSError(28, "Frozen isolated short/full-disk write failure")
            return write(fd, data)
        def failing_fsync(fd):
            kind = "directory-fsync" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file-fsync"
            if armed and operation == kind:
                injected.append(operation)
                raise OSError(5, "Frozen isolated fsync failure")
            return fsync(fd)
        def publish(store, path, value, **kwargs):
            nonlocal armed
            armed = Path(path).name == name
            try:
                return original_write(store, path, value, **kwargs)
            finally:
                armed = False
        with patch.object(inspection._EvidenceStore, "write", new=publish), \
             patch.object(inspection.os, "write", side_effect=failing_write), patch.object(inspection.os, "fsync", side_effect=failing_fsync):
            yield
        self.assertTrue(injected, "The frozen I/O operation was not reached")

    def historical_package(self, guard_mutation=None):
        """Independent synthetic retained records; zero process/writer delegation."""
        f = self.fixture
        names = set()
        for item in f.plan["evidence"]["outer_capture"].values():
            path = Path(item["path"])
            names.update((path, *path.parents))
        f.plan["host_static"]["path_guards"] = []
        for path in sorted(names):
            info = path.lstat()
            f.plan["host_static"]["path_guards"].append({"path": str(path), "kind": "directory" if path.is_dir() else "file",
                "device": info.st_dev, "inode": info.st_ino, "mode": oct(stat.S_IMODE(info.st_mode)), "target": None})
        if guard_mutation is not None:
            guard_mutation(f.plan["host_static"]["path_guards"])
        f.save_plan()
        validated, outputs = f.validated(), f.plan["evidence"]["outputs"]
        root = Path(f.plan["evidence"]["attempt_root"])
        owned = {}
        for path in (root, root / "node_version", root / "shared_libraries"):
            path.mkdir(mode=0o700)
            info = path.stat()
            owned[str(path)] = [info.st_dev, info.st_ino, 0o700]
        selected = deepcopy(f.plan_descriptor)
        guard = {"passed": True, "plan": selected, "source_commit": f.plan["source"]["commit"], "boot_id": f.platform["boot_id"]}
        reservation = {"schema": "ontokin.current-host-readback-inspection-reservation/0.1.0", "plan": selected,
            "attempt_root": str(root), "owned_directories": owned, "state": "RESERVED", "expected_direct_starts": 2, "checker_starts": 0}
        reserved_descriptor = json_file(Path(outputs["reserved"]), reservation)
        source_reads = inspection._thaw(validated._source_reads)
        preflight = {"schema": "ontokin.current-host-readback-inspection-preflight/0.1.0", "plan": selected,
                     "source_reads": source_reads, "binding": guard}
        preflight_descriptor = json_file(Path(outputs["preflight"]), preflight)
        command_descriptors, inspections, rows = [], {}, {}
        for index, command in enumerate(f.plan["commands"]):
            name, paths = command["id"], outputs[command["id"]]
            stdout = b"v24.22.1\n" if index == 0 else f.ldd_stdout
            process = {"argv": command["argv"], "cwd": command["cwd"], "environment": deepcopy(PINNED_ENV), "label": command["label"],
                "start_monotonic": 1000.0, "pid": 4242 + index, "process_group": 4242 + index, "returncode": 0,
                "observed_log_bytes": len(stdout), "retained_log_bytes": len(stdout),
                "cleanup": {"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 1.0},
                "handles_closed": True, "error": None, "end_monotonic": 1000.1}
            started = deepcopy(process); started.pop("end_monotonic")
            started.update(returncode=None, cleanup=None, handles_closed=False, observed_log_bytes=0, retained_log_bytes=0)
            intent = {"schema": "ontokin.current-host-readback-inspection-attempt/0.1.0", "plan": selected, "command_id": name,
                "expected_argv": command["argv"], "expected_direct_starts": 1, "actual_direct_starts": None,
                "observed_direct_starts": 0, "start_count_state": "UNKNOWN", "state": "UNKNOWN", "preflight": preflight_descriptor,
                "start": None, "supervisor_process": None, "supervisor_failure": None, "postflight": None,
                "artifacts": {}, "evidence_finalized": False, "failure": None}
            json_file(Path(paths["intent"]), intent)
            start = {"schema": "ontokin.current-host-readback-inspection-start/0.1.0", "plan": selected,
                     "command_id": name, "process": started, "observed_at_utc": FIXED_TIME}
            start_descriptor = json_file(Path(paths["started"]), start)
            artifacts = {"raw_process": json_file(Path(paths["supervisor_outcome"]["raw"]), process),
                         "stdout": descriptor(put(Path(paths["stdout"]), stdout)), "stderr": descriptor(put(Path(paths["stderr"]), b""))}
            outcome = {"schema": "ontokin.current-host-readback-inspection-supervisor-outcome/0.1.0", "plan": selected,
                "command_id": name, "process": process, "supervisor_failure": None, "observed_start": started,
                "artifacts": artifacts, "faults": [], "decoded_raw_process": process}
            outcome_descriptor = json_file(Path(paths["supervisor_outcome"]["committed"]), outcome)
            receipt = {"schema": "ontokin.current-host-readback-inspection/0.1.0", "argv": command["argv"], "environment": deepcopy(PINNED_ENV),
                "timeout_ms": 5000, "started_at_utc": FIXED_TIME, "finished_at_utc": FIXED_FINISH,
                "process": process, "stdout": stdout.decode(), "stderr": ""}
            inspections[name] = json_file(Path(paths["inspection"]), receipt)
            final = deepcopy(intent)
            final.update(actual_direct_starts=1, observed_direct_starts=1, start_count_state="OBSERVED_ONE", state="COMPLETED",
                         start=start_descriptor, supervisor_process=outcome_descriptor, postflight=guard,
                         artifacts={**artifacts, "inspection": inspections[name]}, evidence_finalized=True)
            command_descriptors.append(json_file(Path(paths["postflight"]), final))
            rows[name] = {"start": start, "outcome": outcome, "final": final, "intent": intent, "receipt": receipt}
        host = {"schema": "ontokin.current-host-readback-host/0.1.0", "observed_at_utc": "2026-11-21T00:00:00.200000+00:00",
            "platform": deepcopy(f.platform), "python": {"executable": str(f.python), "version": f.plan["author"]["python_version"],
            "packages": inspection._thaw(validated._metadata)["packages"]},
            "runtime": {"executable": str(f.node), "version": "v24.22.1", "candidate_sha256": PINNED_NODE["sha256"],
                        "candidate_size_bytes": PINNED_NODE["size_bytes"], "candidate_mode": PINNED_NODE["mode"],
                        "source_archive": deepcopy(f.plan["runtime"]["source_archive"])},
            "files": deepcopy(f.plan["host_static"]["files"]), "aliases": deepcopy(f.plan["host_static"]["aliases"]),
            "roles": deepcopy(f.plan["host_static"]["roles"]), "environment": deepcopy(PINNED_ENV), "inspections": inspections}
        counts = {"direct_starts": {"exact": 2, "observed_lower_bound": 2}, "attempted_launches": {"exact": 2, "observed_lower_bound": 2},
                  "checker_starts": {"exact": 0, "observed_lower_bound": 0}, "node_version": {"exact": 1, "observed_lower_bound": 1},
                  "shared_libraries": {"exact": 1, "observed_lower_bound": 1}}
        host_descriptor = json_file(Path(outputs["host"]), host)
        result = {"schema": "ontokin.current-host-readback-inspection-result/0.1.0", "plan": selected, "mode": "observe",
            "state": "PENDING_COMPLETION", "command_attempts": command_descriptors, "actual_counts": counts,
            "artifacts": {"source_validation": source_reads, "reserved": reserved_descriptor, "preflight": preflight_descriptor},
            "host": host_descriptor, "evidence_finalized": False, "failures": []}
        completion = {"schema": "ontokin.current-host-readback-inspection-completion/0.1.0", "plan": selected,
            "state": "OBSERVED_UNAPPROVED", "result": json_file(Path(outputs["result"]), result), "host": host_descriptor,
            "command_attempts": command_descriptors, "actual_counts": counts, "evidence_finalized": True}
        json_file(Path(outputs["completion"]), completion)
        return {"validated": validated, "host": host, "result": result, "completion": completion, "commands": rows,
                "reservation": reservation, "preflight": preflight}

    def rewrite_historical(self, package, *, command=False):
        outputs = self.fixture.plan["evidence"]["outputs"]
        if command:
            row = package["commands"]["node_version"]
            value = json_file(Path(outputs["node_version"]["postflight"]), row["final"])
            package["result"]["command_attempts"][0] = value
            package["completion"]["command_attempts"][0] = value
        package["completion"]["result"] = json_file(Path(outputs["result"]), package["result"])
        json_file(Path(outputs["completion"]), package["completion"])

    def reconcile_historical(self, package, *, capture=False, deadline=None):
        f, validated = self.fixture, package["validated"]
        def selected(path, digest, *, fresh, git_reads):
            self.assertFalse(fresh)
            self.assertFalse(git_reads)
            if capture:
                self.assertEqual(digest, validated.descriptor["sha256"])
                inspection._bound(path, inspection._binding(validated.descriptor))
                check = deadline or inspection._Deadline(60000)
                inspection._check_evidence(f.plan, fresh=False, check=check)
                required = inspection._required_paths(f.plan, {"aliases": {}}, {"paths": []}, [])
                outer = [row["path"] for row in f.plan["evidence"]["outer_capture"].values()]
                self.assertTrue(set(outer) <= set(required))
                inspection._check_guards(f.plan["host_static"]["path_guards"], outer, check=check)
            return validated
        before = evidence_snapshot(Path(f.plan["evidence"]["attempt_root"]))
        try:
            with patch.object(inspection, "_validate", side_effect=selected), \
                 patch.object(inspection._EvidenceStore, "write", side_effect=AssertionError("Reconcile attempted a write")):
                return inspection.reconcile_attempt(f.plan_path, f.plan_descriptor["sha256"], f.plan["evidence"]["attempt_root"])
        except inspection.HostInspectionError as error:
            self.assertEqual(error.state, "UNKNOWN")
            raise
        finally:
            self.assertEqual(before, evidence_snapshot(Path(f.plan["evidence"]["attempt_root"])))

    def case_HI20(self, variant):
        definitions = inspection._p06_definitions()
        if variant in ("A", "E"):
            process = self.process_fixture()
            receipt = {"schema": "ontokin.current-host-readback-inspection/0.1.0", "argv": process["argv"], "environment": deepcopy(PINNED_ENV),
                       "timeout_ms": 5000, "started_at_utc": FIXED_TIME, "finished_at_utc": FIXED_FINISH, "process": process,
                       "stdout": "v24.22.1\n", "stderr": ""}
            for group in ("inspection", "process", "cleanup") if variant == "A" else ("inspection",):
                for extra in (False, True):
                    changed = deepcopy(receipt)
                    target = changed if group == "inspection" else changed["process"] if group == "process" else changed["process"]["cleanup"]
                    if extra:
                        target["approved"] = True
                    else:
                        target.pop(next(iter(target)))
                    self.refuses("CHI-COMPAT", inspection._schema_check, changed, definitions["inspection"], definitions)
            if variant == "A":
                return
        package = self.historical_package()
        validated, host = package["validated"], package["host"]
        if variant == "B":
            for group in (None, "runtime", "platform", "python", "roles"):
                for extra in (False, True):
                    changed = deepcopy(host); target = changed if group is None else changed[group]
                    if extra:
                        target["unknown"] = True
                    else:
                        target.pop(next(iter(target)))
                    self.refuses("CHI-COMPAT", inspection._validate_host_projection, changed, validated)
        elif variant == "C":
            changes = []
            changed = deepcopy(host); changed["aliases"].pop(next(iter(changed["aliases"]))); changes.append(changed)
            changed = deepcopy(host); changed["files"].pop(next(iter(changed["files"]))); changes.append(changed)
            for value in ([], [self.fixture.library, self.fixture.library], [self.fixture.library, self.fixture.loader]):
                changed = deepcopy(host); changed["roles"]["shared_libraries"] = value; changes.append(changed)
            for changed in changes:
                self.refuses("CHI-COMPAT", inspection._validate_host_projection, changed, validated)
        elif variant == "D":
            for timestamp in ("1900-01-01T00:00:00+00:00", "2999-01-01T00:00:00+00:00", "2026-11-21T00:00:00"):
                changed = deepcopy(host); changed["observed_at_utc"] = timestamp
                self.refuses("CHI-COMPAT", inspection._validate_host_projection, changed, validated)
            changed = deepcopy(host); changed["platform"]["boot_id"] = "different-boot"
            self.refuses("CHI-COMPAT", inspection._validate_host_projection, changed, validated)
        else:
            host["approved"] = True
            self.refuses("CHI-COMPAT", inspection._validate_host_projection, host, validated)

    def metadata_fixture(self):
        f = self.fixture
        original_lock = inspection.ROOT / "tools/native-reader-verification-linux-cp312.lock"
        put(f.source / "tools/native-reader-verification-linux-cp312.lock", original_lock.read_bytes())
        pins = self.preparer.provider._python_pins(f.source)
        packages = []
        for index, (name, version) in enumerate(pins.items()):
            root = f.base / "metadata" / ("package" + str(index) + ".dist-info")
            put(root / "METADATA", ("Metadata-Version: 2.1\nName: " + name + "\nVersion: " + version + "\n\nSynthetic metadata only.\n").encode())
            packages.append({"name": name, "version": version, "distribution_root": str(root), "metadata_files": {"METADATA": file_binding(root / "METADATA")}})
        value = {"schema": "ontokin.current-host-readback-author-metadata/0.1.0", "lock": descriptor(f.source / "tools/native-reader-verification-linux-cp312.lock"), "packages": packages}
        plan = deepcopy(f.plan)
        plan["author"]["metadata_inventory"] = json_file(f.base / "metadata.json", value)
        return plan, value

    def author_fixture(self):
        f = self.fixture
        paths = [f.python, put(f.base / "author-loader", b"inert loader"), put(f.base / "startup.py", b"# inert startup"),
                 put(f.base / "extension.so", b"inert extension"), put(f.base / "author-cache", b"inert cache")]
        runtime = {"schema": "ontokin.current-host-readback-author-runtime/0.1.0", "executable": descriptor(f.python),
            "interpreter": str(paths[1]), "files": {str(path): file_binding(path) for path in paths},
            "aliases": {str(path): {"resolved_path": str(path), "symlink": False, "link_target": None} for path in paths},
            "startup_files": [str(paths[2])], "extension_files": [str(paths[3])], "loader_inputs": [str(paths[4])], "environment": deepcopy(PINNED_ENV)}
        plan = deepcopy(f.plan)
        plan["author"]["python_version"] = ".".join(map(str, inspection.sys.version_info[:3]))
        plan["author"]["runtime_inventory"] = json_file(f.base / "author-runtime.json", runtime)
        return plan, runtime

    def check_author_fixture(self, plan, runtime, *, loaded=False, modules=None):
        with patch.object(inspection, "_check_launcher"), patch.object(inspection.sys, "executable", str(self.fixture.python)), \
             patch.object(inspection, "read_elf_metadata", return_value={"interpreter": runtime["interpreter"]}), \
             patch.object(inspection.sys, "modules", {} if modules is None else modules):
            return inspection._check_author_runtime(plan, {"files": {}}, loaded=loaded)

    def case_HI06(self, variant):
        f = self.fixture
        if variant == "A":
            for path in (put(f.base / "inspector", b"#!/bound/interpreter\n", 0o755), put(f.base / "interpreter", b"inert", 0o755)):
                binding = file_binding(path)
                path.write_bytes(b"changed")
                self.refuses("CHI-INSPECTOR", inspection._bound, path, binding, category="INSPECTOR")
                path.unlink()
                self.refuses("CHI-INSPECTOR", inspection._bound, path, binding, category="INSPECTOR")
        elif variant == "B":
            script = f.base / "script"
            for shebang in ("#!/bound/interpreter -x", "#!/usr/bin/env bash", "#!/different/interpreter"):
                put(script, (shebang + "\n").encode())
                self.refuses("CHI-INSPECTOR", inspection._check_inspector_script, script, "/bound/interpreter")
        elif variant == "C":
            plan, runtime = self.author_fixture()
            changed = deepcopy(plan); changed["author"]["python_version"] = "0.0.1"
            self.refuses("CHI-INSPECTOR", self.check_author_fixture, changed, runtime)
            changed = deepcopy(plan); changed["author"]["python_descriptor"]["path"] = str(f.base / "other-python")
            self.refuses("CHI-INSPECTOR", self.check_author_fixture, changed, runtime)
            for name in runtime["startup_files"] + runtime["extension_files"] + runtime["loader_inputs"]:
                path = Path(name); raw = path.read_bytes(); put(path, b"changed")
                self.refuses("CHI-INSPECTOR", self.check_author_fixture, plan, runtime)
                put(path, raw)
        elif variant == "D":
            plan, value = self.metadata_fixture()
            for action in ("version", "missing", "duplicate", "unbound"):
                changed = deepcopy(value)
                if action == "version":
                    changed["packages"][0]["version"] = "0.0.0"
                elif action == "missing":
                    changed["packages"].pop()
                elif action == "duplicate":
                    changed["packages"][-1] = deepcopy(changed["packages"][0])
                else:
                    changed["packages"][0]["metadata_files"].pop("METADATA")
                plan["author"]["metadata_inventory"] = json_file(f.base / ("metadata-" + action), changed)
                with self.source_root():
                    self.refuses("CHI-INSPECTOR", inspection._check_metadata, plan, (self.preparer.provider,))
        elif variant == "E":
            expected = descriptor(f.git)
            put(f.git, b"changed Git bytes", 0o755)
            with self.source_root(), patch.object(inspection, "_selected_git", return_value=f.git):
                self.refuses("CHI-INSPECTOR", inspection._check_git, f.plan, (None, None, None), check=inspection._Deadline(60000))
            f.git.unlink()
            with self.source_root(), patch.object(inspection, "_selected_git", return_value=None):
                self.refuses("CHI-INSPECTOR", inspection._check_git, f.plan, (None, None, None), check=inspection._Deadline(60000))
        elif variant == "F":
            with patch.dict(os.environ, PINNED_ENV | {"PYTHONPATH": "/unreviewed"}, clear=True):
                self.refuses("CHI-INSPECTOR", inspection._check_launcher, PINNED_ENV)
            plan, runtime = self.author_fixture()
            unbound = put(f.base / "unreviewed-startup.py", b"# inert, never imported")
            self.refuses("CHI-INSPECTOR", self.check_author_fixture, plan, runtime, loaded=True,
                         modules={"unreviewed": SimpleNamespace(__file__=str(unbound), __cached__=None)})
            plan, metadata = self.metadata_fixture()
            root = Path(metadata["packages"][0]["distribution_root"])
            put(root / "startup.pth", b"import forbidden\n")
            with self.source_root():
                self.refuses("CHI-INSPECTOR", inspection._check_metadata, plan, (self.preparer.provider,))
        else:
            script = put(f.base / "script", b"#!/bound/interpreter\n")
            link = f.base / "script-link"; link.symlink_to(script)
            self.refuses("CHI-INSPECTOR", inspection._check_inspector_script, link, "/bound/interpreter")
            os.link(script, f.base / "script-hardlink")
            self.refuses("CHI-INSPECTOR", inspection._check_inspector_script, script, "/bound/interpreter")

    def case_HI07(self, variant):
        f = ClosureFixture(self.fixture)
        if variant == "A":
            row = next(row for row in f.resolution["images"] if row["file"]["path"] == str(f.node))
            row["metadata"] = synthetic_elf(f.node, interpreter=str(f.loader), needed=("libc.so.6", "unbound.so"))
            row["file"] = descriptor(f.node); f.plan["host_static"]["files"][str(f.node)] = file_binding(f.node)
            self.refuses("CHI-LOADER", f.check)
        elif variant == "B":
            row = next(row for row in f.resolution["images"] if row["file"]["path"] == str(f.node))
            row["metadata"] = synthetic_elf(f.node, interpreter="/unbound/interpreter", needed=("libc.so.6",))
            row["file"] = descriptor(f.node); f.plan["host_static"]["files"][str(f.node)] = file_binding(f.node)
            self.refuses("CHI-LOADER", f.check)
        elif variant == "C":
            for path in (f.conf, f.cache):
                before = path.read_bytes(); put(path, b"changed configuration")
                self.refuses("CHI-LOADER", f.check)
                put(path, before)
            include = put(f.root / "included.conf", b"# frozen include\n")
            f.resolution["loader_inputs"].append({"path": str(include), "state": "file", "binding": file_binding(include), "includes": []})
            f.plan["host_static"]["roles"]["loader_configuration"].append(str(include))
            f.plan["host_static"]["aliases"][str(include)] = {"resolved_path": str(include), "symlink": False, "link_target": None}
            f.plan["host_static"]["files"][str(include)] = file_binding(include)
            put(include, b"changed include\n")
            self.refuses("CHI-LOADER", f.check)
            put(include, b"# frozen include\n")
            absent = f.root / "required-absent.conf"
            f.resolution["loader_inputs"].append({"path": str(absent), "state": "absent", "parent": str(absent.parent)})
            put(absent, b"appeared\n")
            self.refuses("CHI-LOADER", f.check)
        elif variant == "D":
            extra = put(f.lib / "new-library-entry", b"extra")
            self.refuses("CHI-LOADER", f.check); extra.unlink()
            saved = f.library.read_bytes(); f.library.unlink()
            self.refuses("CHI-LOADER", f.check); put(f.library, saved, 0o755)
            f.resolution["search_directories"] = [inspection._directory_entries(f.lib)]
            f.library.chmod(0o700)
            self.refuses("CHI-LOADER", f.check); f.library.chmod(0o755)
            target = put(self.base / "target", b"a")
            replacement = put(self.base / "replacement", b"b")
            alias = self.base / "alias"; alias.symlink_to(target)
            aliases = {str(alias): inspection._alias(alias)}
            alias.unlink(); alias.symlink_to(replacement)
            self.refuses("CHI-LOADER", inspection._check_alias_files, {str(target): file_binding(target)}, aliases, {str(alias)})
        elif variant == "E":
            extra = f.root / "extra-loader"
            synthetic_elf(extra)
            f.plan["host_static"]["aliases"][str(extra)] = {"resolved_path": str(extra), "symlink": False, "link_target": None}
            f.plan["host_static"]["files"][str(extra)] = file_binding(extra)
            f.plan["host_static"]["roles"]["inspector_runtime"].append(str(extra))
            f.resolution["inspector_commands"]["rtld_candidates"].append({"path": str(extra), "state": "file", "binding": file_binding(extra)})
            put(f.script, ("#!" + str(f.shell) + "\nRTLDLIST=\"" + str(f.loader) + " " + str(extra) + "\"\n").encode(), 0o755)
            f.resolution["inspector_commands"]["script"] = descriptor(f.script)
            f.plan["host_static"]["files"][str(f.script)] = file_binding(f.script)
            self.refuses("CHI-LOADER", f.check)
            g = ClosureFixture(self.new_fixture("inspector-command-extra"))
            command = g.root / "extra-command"
            synthetic_elf(command, interpreter=str(g.loader), needed=("libc.so.6",))
            g.resolution["inspector_commands"]["commands"].append(descriptor(command))
            g.plan["host_static"]["roles"]["inspector_runtime"].append(str(command))
            g.plan["host_static"]["aliases"][str(command)] = {"resolved_path": str(command), "symlink": False, "link_target": None}
            g.plan["host_static"]["files"][str(command)] = file_binding(command)
            self.refuses("CHI-LOADER", g.check)
        elif variant == "F":
            put(f.preload, b"injected preload")
            self.refuses("CHI-LOADER", f.check)
            put(f.preload, b"")
            row = next(row for row in f.resolution["loader_inputs"] if row["path"] == "/etc/ld.so.preload")
            row.clear(); row.update(path="/etc/ld.so.preload", state="file", binding=file_binding(f.preload), includes=[])
            f.plan["host_static"]["roles"]["loader_configuration"].append("/etc/ld.so.preload")
            f.plan["host_static"]["aliases"]["/etc/ld.so.preload"] = {"resolved_path": str(f.preload), "symlink": False, "link_target": None}
            f.plan["host_static"]["files"][str(f.preload)] = file_binding(f.preload)
            put(f.preload, b"changed nonempty preload")
            self.refuses("CHI-LOADER", f.check)
        else:
            put(f.library, b"changed transitive library", 0o755)
            # Keep the directory entry inventory fresh to reach the actual
            # bound ELF byte predicate, not the earlier directory guard.
            f.resolution["search_directories"] = [inspection._directory_entries(f.lib)]
            self.refuses("CHI-LOADER", f.check)
            f.library.unlink()
            f.resolution["search_directories"] = [inspection._directory_entries(f.lib)]
            self.refuses("CHI-LOADER", f.check)
            g = ClosureFixture(self.new_fixture("missing-absence-guard"))
            g.resolution["loader_inputs"] = [row for row in g.resolution["loader_inputs"] if row["path"] != "/etc/ld.so.preload"]
            self.refuses("CHI-LOADER", g.check)

    def case_HI08(self, variant):
        f = self.fixture
        if variant == "A":
            for key, value in (("system", "Darwin"), ("libc", ["musl", "1.0"])):
                plan = deepcopy(f.plan); plan["host_static"]["platform"][key] = value
                self.refuses("CHI-UNSUPPORTED", inspection._check_host_static, plan)
        elif variant in ("B", "C", "D"):
            path = f.base / "elf"
            if variant == "B":
                for field, value in ((0, 0), (4, 1), (5, 2)):
                    synthetic_elf(path, interpreter="/bound/loader")
                    raw = bytearray(path.read_bytes()); raw[field] = value; put(path, raw, 0o755)
                    self.refuses("CHI-UNSUPPORTED", inspection.read_elf_metadata, path, require_interpreter=True)
                synthetic_elf(path)
                self.refuses("CHI-UNSUPPORTED", inspection.read_elf_metadata, path, require_interpreter=True)
                synthetic_elf(path, interpreter="/bound/loader", duplicate_interp=True)
                self.refuses("CHI-UNSUPPORTED", inspection.read_elf_metadata, path, require_interpreter=True)
                synthetic_elf(path, interpreter="/bound/loader", dynamic_displacement=0x100)
                self.refuses("CHI-UNSUPPORTED", inspection.read_elf_metadata, path)
                expected = synthetic_elf(path, interpreter="/bound/loader")
                self.assertEqual(inspection.read_elf_metadata(path), expected)
                raw = bytearray(path.read_bytes())
                struct.pack_into("<Q", raw, 64 + 16, 0x400001)
                struct.pack_into("<Q", raw, 64 + 56 + 16, 0x400301)
                struct.pack_into("<Q", raw, 64 + 112 + 16, 0x400201)
                struct.pack_into("<Q", raw, 0x308, 0x400501)
                put(path, raw, 0o755)
                error = self.refuses("CHI-UNSUPPORTED", inspection.read_elf_metadata, path)
                self.assertIn("alignment", error.reason)
            elif variant == "C":
                for kind in ("straddr", "strsize", "unterminated", "bounds"):
                    synthetic_elf(path, interpreter="/bound/loader", needed=("libc.so.6",))
                    raw = bytearray(path.read_bytes())
                    if kind == "straddr":
                        struct.pack_into("<Q", raw, 0x308, 0x900000)
                    elif kind == "strsize":
                        struct.pack_into("<Q", raw, 0x318, 4 * 1024 * 1024 + 1)
                    elif kind == "unterminated":
                        struct.pack_into("<qQ", raw, 0x330, 1, 1)
                    else:
                        struct.pack_into("<Q", raw, 32, len(raw) - 1)
                    put(path, raw, 0o755)
                    self.refuses("CHI-UNSUPPORTED", inspection.read_elf_metadata, path)
                synthetic_elf(path, interpreter="/bound/loader", extra_tags=[(5, 0x400510)])
                self.refuses("CHI-UNSUPPORTED", inspection.read_elf_metadata, path)
            else:
                for options in ({"extra_tags": [(0x6FFFFEFC, 1)]}, {"extra_tags": [(0x7FFFFFFF, 1)]},
                                {"rpath": "$ORIGIN/lib"}, {"rpath": "/a", "runpath": "/b"}, {"machine": 3}):
                    synthetic_elf(path, interpreter="/bound/loader", **options)
                    self.refuses("CHI-UNSUPPORTED", inspection.read_elf_metadata, path)
        elif variant == "E":
            self.refuses("CHI-UNSUPPORTED", inspection._bounded_include, str(f.base / "**/*.conf"))
            parent = f.base / "many"; parent.mkdir()
            for number in range(2049):
                put(parent / (str(number) + ".conf"), b"")
            self.refuses("CHI-UNSUPPORTED", inspection._bounded_include, str(parent / "*.conf"))
            closure = ClosureFixture(f)
            (closure.lib / "glibc-hwcaps").mkdir()
            closure.resolution["search_directories"] = [inspection._directory_entries(closure.lib)]
            self.refuses("CHI-UNSUPPORTED", closure.check)
        else:
            for path in ("/fixture/lib/with space", "/fixture/lib/../bad", "/fixture/lib/nu\0l"):
                plan = deepcopy(f.plan); plan["host_static"]["roles"]["shared_libraries"] = [path]
                with patch.object(inspection, "_platform", return_value=f.platform):
                    self.refuses("CHI-UNSUPPORTED", inspection._check_host_static, plan)
            target = put(f.base / "payload", b"inert")
            (f.base / "walk").mkdir()
            alias = f.base / "parent-hop"; alias.symlink_to("walk/../payload")
            self.refuses("CHI-UNSUPPORTED", inspection._existing_chain, alias)

    def case_HI09(self, variant):
        f = self.fixture
        if variant == "A":
            for value in ("relative", str(f.source / "evidence"), str(f.runtime / "evidence"), str(f.dependencies / "evidence")):
                plan = deepcopy(f.plan)
                plan["evidence"]["parent"] = value
                plan["evidence"]["attempt_root"] = str(Path(value) / "attempt")
                self.refuses("CHI-PATH", self.shape, plan)
        elif variant == "B":
            attempt = Path(f.plan["evidence"]["attempt_root"])
            sentinel = put(attempt / "sentinel", b"another writer")
            self.refuses("CHI-PATH", inspection._check_evidence, f.plan)
            self.assertEqual(sentinel.read_bytes(), b"another writer")
            for name in ("stage", "output"):
                other = self.new_fixture("preexisting-" + name)
                path = Path(other.plan["evidence"]["attempt_root"]) / "node_version"
                sentinel = put(path / ("sentinel" if name == "stage" else "intent.json"), b"another writer")
                self.refuses("CHI-PATH", inspection._check_evidence, other.plan)
                self.assertEqual(sentinel.read_bytes(), b"another writer")
        elif variant == "C":
            for key in ("device", "inode", "mode"):
                plan = deepcopy(f.plan)
                row = next(row for row in plan["evidence"]["ancestor_identities"] if row["path"] == str(f.evidence))
                row[key] = "0o000" if key == "mode" else row[key] + 1
                self.refuses("CHI-PATH", inspection._check_evidence, plan)
        elif variant == "D":
            store = inspection._EvidenceStore(f.validated())
            path = Path(f.plan["evidence"]["outputs"]["reserved"])
            calls = []
            def race(source, destination):
                calls.append(destination)
                put(destination, b"another writer")
                return self.preparer.rename_without_replacement(source, destination)
            store.rename = race
            self.refuses("CHI-PATH", store.write, path, {"planned": True})
            self.assertEqual(len(calls), 1)
            self.assertEqual(path.read_bytes(), b"another writer")
        else:
            for kind in ("swap", "equal", "wrong", "alias"):
                plan = deepcopy(f.plan)
                pair = plan["evidence"]["outputs"]["node_version"]["supervisor_outcome"]
                if kind == "swap":
                    pair["raw"], pair["committed"] = pair["committed"], pair["raw"]
                elif kind == "equal":
                    pair["committed"] = pair["raw"]
                elif kind == "wrong":
                    pair["raw"] = str(f.base / "wrong.process.json")
                else:
                    pair["committed"] = pair["raw"] + "/../alias"
                self.refuses("CHI-PATH", self.shape, plan)

    def case_HI10(self, variant):
        f = self.fixture
        original = inspection._launch_check
        absent = f.base / "required-absent"
        def launch(validated, clock, stage_end):
            if variant == "A":
                put(f.drift, b"changed before launch")
            elif variant == "B":
                data = f.drift.read_bytes(); f.drift.unlink(); put(f.drift, data)
            else:
                put(absent, b"appeared")
            return original(validated, clock, stage_end)
        if variant == "C":
            original_validated = f.validated
            def selected(controller=None):
                value = original_validated(controller)
                metadata = inspection._thaw(value._metadata)
                metadata["input_snapshot"][str(absent)] = {"absent": True}
                return inspection.ValidatedPlan(f.plan, f.plan_descriptor, [], {}, value._helpers, inspection._thaw(value._runtime), metadata)
            with patch.object(f, "validated", side_effect=selected):
                self.assert_failed_observation("CHI-DRIFT", starts=0, launch=launch)
        else:
            self.assert_failed_observation("CHI-DRIFT", starts=0, launch=launch)

    def case_HI11(self, variant):
        for kind in ("source", "runtime", "dependency") if variant == "A" else ("loader", "alias", "boot") if variant == "B" else ("source",):
            f = self.new_fixture("postflight-" + kind)
            dependency = put(f.dependencies / "retained-file", b"frozen dependency")
            watched = f.source / "tools/check_local.py" if kind == "source" else f.node if kind == "runtime" else dependency if kind == "dependency" else f.drift
            expected = file_binding(watched)
            alias = f.base / "postflight-alias"; alias.symlink_to(f.drift)
            f.plan["host_static"]["path_guards"] = [inspection._path_row(Path(name)) for name in sorted(inspection._existing_chain(alias))]
            f.save_plan()
            platform = deepcopy(f.platform)
            original_recheck, original_bound = inspection._recheck, inspection._bound
            runtime = {"files": {}, "aliases": {}, "interpreter": f.loader, "startup_files": [], "extension_files": [], "loader_inputs": []}
            def host_bound(path, binding, **kwargs):
                # Only synthetic host executable facts are outside this test.
                if str(path) in f.plan["host_static"]["files"]:
                    return binding
                return original_bound(path, binding, **kwargs)
            def runtime_inputs(*args, **kwargs):
                if kind in ("runtime", "dependency"):
                    original_bound(watched, expected, category="RUNTIME", check=kwargs.get("check", lambda: None))
                return []
            def resolution(*args, **kwargs):
                if kind == "loader":
                    original_bound(watched, expected, category="LOADER", check=kwargs.get("check", lambda: None))
                return deepcopy(f.resolution), []
            def recheck(validated, **kwargs):
                with self.source_root(), ExitStack() as stack:
                    stack.enter_context(patch.object(inspection, "_bound", side_effect=host_bound))
                    stack.enter_context(patch.object(inspection, "_git_state", return_value={}))
                    stack.enter_context(patch.object(inspection, "_check_author_runtime", return_value=runtime))
                    stack.enter_context(patch.object(inspection, "_check_metadata", return_value={"paths": []}))
                    stack.enter_context(patch.object(inspection, "_check_runtime_dependencies", side_effect=runtime_inputs))
                    stack.enter_context(patch.object(inspection, "_check_resolution", side_effect=resolution))
                    stack.enter_context(patch.object(inspection, "_check_alias_files"))
                    stack.enter_context(patch.object(inspection, "_check_inspector_script"))
                    stack.enter_context(patch.object(inspection, "_platform", return_value=platform))
                    stack.enter_context(patch.object(inspection, "_required_paths", return_value=[str(alias)]))
                    return original_recheck(validated, **kwargs)
            def mutation(name, output, error, process):
                if kind == "alias":
                    alias.unlink(); alias.symlink_to(put(f.base / "different-loader", b"inert"))
                elif kind == "boot":
                    platform["boot_id"] = "changed-boot"
                else:
                    put(watched, b"changed after retained start", int(expected["mode"], 8))
                return output, error, process
            error, controller = self.assert_failed_observation("CHI-DRIFT", variant="HI11-C" if variant == "C" else None,
                                                              recheck=recheck, mutation=mutation)
            self.assertIsNotNone(error.process_record)
            self.assertTrue(Path(f.plan["evidence"]["outputs"]["node_version"]["supervisor_outcome"]["committed"]).exists())
            if variant == "C":
                self.assertIs(error.supervisor_exception, controller.last_failure)
                self.assertIs(error.process_record, controller.last_failure.process_record)

    @contextmanager
    def static_admission(self):
        """Live source/plan/author/metadata checks; explicit synthetic host facts."""
        f = self.fixture
        plan, runtime = self.author_fixture()
        metadata_plan, metadata = self.metadata_fixture()
        plan["author"]["metadata_inventory"] = metadata_plan["author"]["metadata_inventory"]
        plan["host_static"]["aliases"].update(deepcopy(runtime["aliases"]))
        plan["host_static"]["files"].update(deepcopy(runtime["files"]))
        runtime_names = [name for name in runtime["aliases"] if name != str(f.python)]
        plan["host_static"]["roles"]["inspector_runtime"].extend(runtime_names)
        f.inventory["files"] = {name: file_binding(f.source / name) for name in f.inventory["files"]}
        plan["source"]["inventory"] = json_file(f.base / "source-inventory.json", f.inventory)
        put(f.source / inspection.P06_SCHEMA_PATH, (inspection.ROOT / inspection.P06_SCHEMA_PATH).read_bytes(), 0o644)
        f.plan = plan
        f.save_plan()
        replies = [str(f.source), plan["source"]["commit"], plan["source"]["tree"], "", ""]
        calls, events = [], []
        def git_read(root, *args, timeout):
            self.assertIn("closure", events)
            self.assertIn("guards", events)
            events.append("git")
            calls.append((str(root), list(args), timeout))
            return replies[(len(calls) - 1) % 5]
        driver = SimpleNamespace(git_read=Mock(side_effect=git_read), git_environment=lambda root: inspection._git_environment(root))
        driver.events = events
        helpers = (self.preparer.provider, self.real_supervisor, driver, self.preparer.rename_without_replacement, self.preparer)
        snapshot = {str(f.drift): {"identity": list(inspection._identity(f.drift.lstat())), "resolved": str(f.drift)}}
        with self.source_root(), ExitStack() as stack:
            stack.enter_context(patch.object(inspection, "_load_helpers", return_value=helpers))
            stack.enter_context(patch.object(inspection, "_check_launcher"))
            stack.enter_context(patch.object(inspection.sys, "executable", str(f.python)))
            stack.enter_context(patch.object(inspection.sys, "modules", {}))
            stack.enter_context(patch.object(inspection, "read_elf_metadata", return_value={"interpreter": runtime["interpreter"]}))
            stack.enter_context(patch.object(inspection, "_check_runtime_dependencies", return_value=[]))
            stack.enter_context(patch.object(inspection, "_check_host_static"))
            def closure_fact(*args, **kwargs):
                events.append("closure"); return f.resolution, []
            def guard_fact(*args, **kwargs):
                events.append("guards"); return {}
            stack.enter_context(patch.object(inspection, "_check_resolution", side_effect=closure_fact))
            stack.enter_context(patch.object(inspection, "_check_guards", side_effect=guard_fact))
            stack.enter_context(patch.object(inspection, "_input_snapshot", return_value=snapshot))
            stack.enter_context(patch.object(inspection, "_selected_git", return_value=f.git))
            yield driver, runtime, calls

    def test_HI_P01(self):
        with self.static_admission() as (driver, runtime, calls):
            validated = inspection.validate_inspection_plan(self.fixture.plan_path, self.fixture.plan_descriptor["sha256"])
            self.assertEqual(len(calls), 5)
            with self.assertRaises(TypeError):
                validated.plan["source"]["commit"] = "forbidden"
            with self.assertRaises(AttributeError):
                validated.plan = {}
            result = inspection.inspect_host(self.fixture.plan_path, self.fixture.plan_descriptor["sha256"])
            self.assertEqual(len(calls), 10)
        self.assertEqual(result["state"], "STATIC_READY")
        self.assertEqual(result["actual_counts"]["direct_starts"]["exact"], 0)
        self.assertFalse(Path(self.fixture.plan["evidence"]["attempt_root"]).exists())
        self.assertEqual(inspection.NODE, PINNED_NODE)
        self.assertEqual(inspection.ENVIRONMENT, PINNED_ENV)
        self.assertEqual(inspection.NODE_VERSION, "v24.22.1")
        self.assertEqual(inspection.NODE_ARCHIVE_SHA256, "100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5")
        self.assertEqual(inspection.NODE_ARCHIVE_BYTES, 45186132)
        self.assertEqual(inspection.LIMITS, PINNED_LIMITS)
        self.assertEqual(inspection.SOURCE_TREES, PINNED_SOURCE_TREES)
        self.assertEqual(inspection.SOURCE_FILES, PINNED_SOURCE_FILES)
        self.assertEqual(inspection.SOURCE_OPTIONAL, PINNED_SOURCE_OPTIONAL)
        self.assertEqual(self.preparer.provider._python_pins(inspection.ROOT), PINNED_PACKAGES)

    def test_HI_P02(self):
        raw = self.fixture.ldd_stdout
        for stdout in (raw, b"".join(raw.splitlines(keepends=True)[1:])):
            expected = deepcopy(self.fixture.resolution)
            if stdout != raw:
                expected["vdso"] = []
            result = inspection.parse_ldd_output(stdout, b"", expected)
            self.assertEqual(result["libraries"], {"libc.so.6": self.fixture.library})
            self.assertEqual(result["interpreter"], self.fixture.loader)
            self.assertEqual(self.fixture.ldd_stdout, raw)

    def test_HI_P03(self):
        with self.observation() as (validated, controller, writes):
            result = self.observe()
        self.assertEqual(controller.calls, ["node_version", "shared_libraries"])
        self.assertEqual(len(controller.starts), 2)
        self.assertEqual(result["state"], "OBSERVED_UNAPPROVED")
        self.assertTrue(result["evidence_finalized"])
        self.assertEqual(result["actual_counts"]["direct_starts"]["exact"], 2)
        self.assertEqual(writes[-1], self.fixture.plan["evidence"]["outputs"]["completion"])
        host = json.loads(Path(result["host"]["path"]).read_bytes())
        self.assertEqual(len(host), 10)
        self.assertNotIn("approved", host)
        for path, process, raw in controller.raw_receipts:
            self.assertEqual(path.read_bytes(), raw)
            name = "node_version" if process["label"] == "host-node-version" else "shared_libraries"
            receipt = json.loads(Path(host["inspections"][name]["path"]).read_bytes())
            self.assertEqual(receipt["process"], process)
            self.assertEqual(len(receipt), 9)
        before = evidence_snapshot(Path(self.fixture.plan["evidence"]["attempt_root"]))
        with patch.object(inspection, "_validate", return_value=validated), patch.object(inspection._EvidenceStore, "write", side_effect=AssertionError("Read-only reconcile wrote")):
            reconciled = inspection.reconcile_attempt(self.fixture.plan_path, self.fixture.plan_descriptor["sha256"], self.fixture.plan["evidence"]["attempt_root"])
        self.assertEqual(reconciled["state"], "OBSERVED_UNAPPROVED_AS_RECORDED")
        self.assertEqual(reconciled["durability_state"], "UNKNOWN")
        self.assertFalse(reconciled["evidence_finalized"])
        self.assertEqual(before, evidence_snapshot(Path(self.fixture.plan["evidence"]["attempt_root"])))
        self.assertFalse(reconciled["approved"])

    def test_HI_P04(self):
        store = inspection._EvidenceStore(self.fixture.validated())
        original_fsync = os.fsync
        synced = []
        def fsync(fd):
            synced.append(stat.S_IFMT(os.fstat(fd).st_mode))
            return original_fsync(fd)
        path = Path(self.fixture.plan["evidence"]["outputs"]["reserved"])
        with patch.object(inspection.os, "fsync", side_effect=fsync), patch.object(store, "rename", wraps=store.rename) as rename:
            recorded = store.write(path, {"independent_fixture": True})
        self.assertEqual(rename.call_count, 1)
        self.assertIn(stat.S_IFREG, synced)
        self.assertIn(stat.S_IFDIR, synced)
        self.assertEqual(recorded, descriptor(path))
        self.assertEqual(path.read_bytes(), b'{"independent_fixture":true}')
        self.refuses("CHI-PATH", store.write, path, {"replacement": True})
        self.assertEqual(path.read_bytes(), b'{"independent_fixture":true}')

    def test_HI_P05(self):
        before = evidence_snapshot(self.fixture.evidence)
        imported = runpy.run_path(inspection.__file__, run_name="isolated_inspection_import")
        self.assertIn("inspect_host", imported)
        self.assertEqual(before, evidence_snapshot(self.fixture.evidence))
        for explicit in (False, True):
            args = ["--plan", str(self.fixture.plan_path), "--plan-sha256", self.fixture.plan_descriptor["sha256"]]
            if explicit:
                args.append("--observe")
            with patch.object(inspection, "inspect_host", return_value={"fixture": True}) as inspect, redirect_stdout(io.StringIO()):
                self.assertEqual(inspection.main(args), 0)
            self.assertEqual(inspect.call_args.kwargs, {"observe": explicit})
        self.assertFalse(Path(self.fixture.plan["evidence"]["attempt_root"]).exists())

    def test_SUP_01(self):
        original_resolution, original_elf = inspection._check_resolution, inspection.read_elf_metadata
        closure = ClosureFixture(self.fixture)
        git_image = next(row for row in closure.resolution["images"] if row["file"]["path"] == str(closure.git))
        git_image["resolved_needed"].pop("libc.so.6")
        with self.static_admission() as (driver, runtime, calls):
            def closure_boundary(*args, **kwargs):
                with closure.mapped_files(), patch.object(inspection, "read_elf_metadata", new=original_elf):
                    return original_resolution(closure.plan, closure.author_runtime, **kwargs)
            with patch.object(inspection, "_check_resolution", side_effect=closure_boundary):
                self.refuses("CHI-LOADER", inspection.validate_inspection_plan, self.fixture.plan_path, self.fixture.plan_descriptor["sha256"])
            self.assertEqual(calls, [])

    def test_SUP_02(self):
        plan, runtime = self.author_fixture()
        plan["author"]["python_descriptor"]["sha256"] = runtime["executable"]["sha256"] = "d" * 64
        plan["author"]["runtime_inventory"] = json_file(self.base / "false-python-runtime.json", runtime)
        self.refuses("CHI-INSPECTOR", self.check_author_fixture, plan, runtime)

    def test_SUP_03(self):
        with self.static_admission() as (driver, runtime, calls):
            name = runtime["startup_files"][0]
            self.fixture.plan["host_static"]["roles"]["inspector_runtime"].remove(name)
            self.fixture.plan["host_static"]["aliases"].pop(name)
            self.fixture.plan["host_static"]["files"].pop(name)
            self.fixture.save_plan()
            self.refuses("CHI-INSPECTOR", inspection.validate_inspection_plan, self.fixture.plan_path, self.fixture.plan_descriptor["sha256"])
            self.assertEqual(calls, [])

    def test_SUP_04(self):
        def mutation(name, stdout, stderr, process):
            process["pid"] = process["process_group"] = 5252
            return stdout, stderr, process
        error, controller = self.assert_failed_observation("CHI-PROCESS", mutation=mutation)
        start = json.loads(Path(self.fixture.plan["evidence"]["outputs"]["node_version"]["started"]).read_bytes())
        self.assertEqual(start["process"], controller.starts[0])
        self.assertNotEqual(start["process"]["pid"], controller.raw_receipts[0][1]["pid"])
        self.assertEqual(error.refusal_record["actual_counts"]["direct_starts"], {"exact": 1, "observed_lower_bound": 1})

    def test_SUP_05(self):
        original = inspection._EvidenceStore.write
        attempts = []
        def write(store, path, value, **kwargs):
            if Path(path).name != "result.json":
                return original(store, path, value, **kwargs)
            attempts.append(str(path))
            old = store.rename
            def uncertain(source, destination):
                raise OSError(5, "Lost result publication reply; destination absent")
            store.rename = uncertain
            try:
                return original(store, path, value, **kwargs)
            finally:
                store.rename = old
        with patch.object(inspection._EvidenceStore, "write", new=write):
            error, controller = self.assert_failed_observation("CHI-EVIDENCE", starts=2)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(error.details["destination_after"]["state"], "absent")
        self.assertFalse(Path(self.fixture.plan["evidence"]["outputs"]["completion"]).exists())

    def test_SUP_06(self):
        for index, kind in enumerate(("empty", "one", "three", "reverse")):
            self.new_fixture("cardinality-" + str(index))
            package = self.historical_package()
            values = list(package["result"]["command_attempts"])
            changed = [] if kind == "empty" else values[:1] if kind == "one" else values + values[:1] if kind == "three" else values[::-1]
            package["result"]["command_attempts"] = changed
            package["completion"]["command_attempts"] = changed
            self.rewrite_historical(package)
            self.refuses("CHI-EVIDENCE", self.reconcile_historical, package)

    def test_SUP_07(self):
        for name in ("result", "host"):
            f = self.new_fixture("alternate-" + name)
            package = self.historical_package()
            alternate = json_file(f.base / ("alternate-" + name + ".json"), package[name])
            package["completion"][name] = alternate
            if name == "host":
                package["result"]["host"] = alternate
                package["completion"]["result"] = json_file(Path(f.plan["evidence"]["outputs"]["result"]), package["result"])
            json_file(Path(f.plan["evidence"]["outputs"]["completion"]), package["completion"])
            self.refuses("CHI-EVIDENCE", self.reconcile_historical, package)

    def test_SUP_08(self):
        for kind in ("start", "outcome", "preflight", "artifact", "raw", "identity"):
            f = self.new_fixture("record-link-" + kind)
            package = self.historical_package()
            row, paths = package["commands"]["node_version"], f.plan["evidence"]["outputs"]["node_version"]
            if kind in ("start", "outcome", "preflight"):
                data = package["preflight"] if kind == "preflight" else row[kind]
                row["final"][{"start": "start", "outcome": "supervisor_process", "preflight": "preflight"}[kind]] = json_file(f.base / ("alternate-" + kind), data)
            elif kind == "artifact":
                row["outcome"]["artifacts"]["stdout"] = descriptor(put(f.base / "alternate-stdout", b"v24.22.1\n"))
                row["final"]["artifacts"]["stdout"] = row["outcome"]["artifacts"]["stdout"]
            elif kind == "raw":
                raw = deepcopy(row["outcome"]["process"])
                raw["pid"] = raw["process_group"] = 5252
                row["outcome"]["artifacts"]["raw_process"] = json_file(Path(paths["supervisor_outcome"]["raw"]), raw)
                row["final"]["artifacts"]["raw_process"] = row["outcome"]["artifacts"]["raw_process"]
            else:
                row["start"]["process"]["pid"] = row["start"]["process"]["process_group"] = 5252
                row["outcome"]["observed_start"] = deepcopy(row["start"]["process"])
                row["final"]["start"] = json_file(Path(paths["started"]), row["start"])
            if kind in ("artifact", "raw", "identity"):
                row["final"]["supervisor_process"] = json_file(Path(paths["supervisor_outcome"]["committed"]), row["outcome"])
            self.rewrite_historical(package, command=True)
            self.refuses("CHI-EVIDENCE", self.reconcile_historical, package)

    def test_SUP_09(self):
        for kind in ("empty", "missing", "extra", "intent-plan", "intent-command", "preflight-schema", "preflight-plan", "preflight-binding"):
            f = self.new_fixture("meaning-" + kind)
            package = self.historical_package()
            outputs = f.plan["evidence"]["outputs"]
            if kind in ("empty", "missing", "extra"):
                owned = package["reservation"]["owned_directories"]
                if kind == "empty":
                    owned.clear()
                elif kind == "missing":
                    owned.pop(str(Path(f.plan["evidence"]["attempt_root"]) / "node_version"))
                else:
                    owned[str(f.base / "unrelated")] = [1, 2, 0o700]
                package["result"]["artifacts"]["reserved"] = json_file(Path(outputs["reserved"]), package["reservation"])
            elif kind.startswith("intent"):
                row = package["commands"]["node_version"]["intent"]
                if kind == "intent-plan":
                    row["plan"] = deepcopy(row["plan"]); row["plan"]["sha256"] = "d" * 64
                else:
                    row["command_id"] = "shared_libraries"
                json_file(Path(outputs["node_version"]["intent"]), row)
            else:
                row = package["preflight"]
                if kind == "preflight-schema":
                    row["schema"] = "wrong"
                elif kind == "preflight-plan":
                    row["plan"] = deepcopy(row["plan"]); row["plan"]["sha256"] = "d" * 64
                else:
                    row["binding"] = deepcopy(row["binding"]); row["binding"]["source_commit"] = "d" * 40
                changed = json_file(Path(outputs["preflight"]), row)
                for name in ("node_version", "shared_libraries"):
                    for record in ("intent", "final"):
                        package["commands"][name][record]["preflight"] = changed
                        path = outputs[name]["intent" if record == "intent" else "postflight"]
                        bound = json_file(Path(path), package["commands"][name][record])
                        if record == "final":
                            index = 0 if name == "node_version" else 1
                            package["result"]["command_attempts"][index] = bound
                            package["completion"]["command_attempts"][index] = bound
                package["result"]["artifacts"]["preflight"] = changed
            self.rewrite_historical(package)
            self.refuses("CHI-EVIDENCE", self.reconcile_historical, package)

    def test_SUP_10(self):
        package = self.historical_package()
        for group, key, value in (("python", "executable", "/different/python"), ("python", "version", "3.12.9"),
                                  ("python", "packages", {"package" + str(i): "2.0" for i in range(7)}),
                                  ("runtime", "executable", "/different/node"),
                                  ("runtime", "source_archive", {**self.fixture.plan["runtime"]["source_archive"], "path": "/different/archive"})):
            host = deepcopy(package["host"]); host[group][key] = value
            self.refuses("CHI-COMPAT", inspection._validate_host_projection, host, package["validated"])

    def test_SUP_11(self):
        package = self.historical_package()
        row = package["commands"]["node_version"]["receipt"]
        row["argv"] = ["/different/node", "--version"]
        path = Path(self.fixture.plan["evidence"]["outputs"]["node_version"]["inspection"])
        package["host"]["inspections"]["node_version"] = json_file(path, row)
        raw = path.read_bytes()
        self.refuses("CHI-COMPAT", inspection._validate_host_projection, package["host"], package["validated"])
        self.assertEqual(path.read_bytes(), raw)

    def test_SUP_12(self):
        package = self.historical_package()
        log = Path(self.fixture.plan["evidence"]["outer_capture"]["log"]["path"])
        before = self.fixture.plan_path.read_bytes()
        with log.open("ab") as stream:
            stream.write(b"observation-result\n")
        result = self.reconcile_historical(package, capture=True)
        self.assertEqual(result["state"], "OBSERVED_UNAPPROVED_AS_RECORDED")
        self.assertEqual(result["durability_state"], "UNKNOWN")
        self.assertFalse(result["evidence_finalized"])
        self.assertFalse(result["approved"])
        self.assertFalse(result["relaunch_permitted"])
        self.assertEqual(self.fixture.plan_path.read_bytes(), before)
        self.assertEqual(log.read_bytes(), b"outer-start\nobservation-result\n")

    def test_SUP_13(self):
        for value, label in ((b"Xuter-start\n", "altered"), (b"outer", "truncated")):
            f = self.new_fixture("prefix-" + label)
            package = self.historical_package()
            log = Path(f.plan["evidence"]["outer_capture"]["log"]["path"])
            log.write_bytes(value)
            self.refuses("CHI-EVIDENCE", self.reconcile_historical, package, capture=True)
            self.assertEqual(log.read_bytes(), value)

    def test_SUP_14(self):
        for kind in ("inode", "symlink", "hardlink", "mode", "ancestor", "authority", "missing-guard"):
            f = self.new_fixture("capture-" + kind)
            log = Path(f.plan["evidence"]["outer_capture"]["log"]["path"])
            def guard_mutation(guards):
                if kind == "ancestor":
                    next(row for row in guards if row["path"] == str(log.parent))["inode"] += 1
                elif kind == "missing-guard":
                    guards[:] = [row for row in guards if row["path"] != str(log)]
            package = self.historical_package(guard_mutation=guard_mutation)
            if kind == "inode":
                log.rename(f.base / "original-log"); put(log, b"outer-start\n")
            elif kind == "symlink":
                log.rename(f.base / "original-log"); log.symlink_to(f.base / "original-log")
            elif kind == "hardlink":
                os.link(log, f.base / "extra-log-link")
            elif kind == "mode":
                log.chmod(0o644)
            elif kind == "authority":
                put(Path(f.plan["evidence"]["outer_capture"]["authority"]["path"]), b"changed immutable authority")
            if kind in ("ancestor", "missing-guard"):
                # The selected descriptor and historical graph are coherent;
                # only the live capture guard is supposed to reject this row.
                coherent = self.reconcile_historical(package)
                self.assertEqual(coherent["state"], "OBSERVED_UNAPPROVED_AS_RECORDED")
            self.refuses("CHI-EVIDENCE", self.reconcile_historical, package, capture=True)

    def test_SUP_15(self):
        for kind in ("within", "above", "deadline"):
            f = self.new_fixture("capture-bound-" + kind)
            package = self.historical_package()
            log = Path(f.plan["evidence"]["outer_capture"]["log"]["path"])
            with log.open("r+b") as stream:
                stream.truncate(64 * 1024 * 1024 + (1 if kind == "above" else 0))
            real_read, read_bytes = os.read, []
            def bounded_read(fd, maximum):
                if os.fstat(fd).st_ino == log.stat().st_ino:
                    before = os.lseek(fd, 0, os.SEEK_CUR)
                    self.assertGreater(maximum, 0)
                    self.assertLessEqual(before + maximum, len(b"outer-start\n"))
                    data = real_read(fd, maximum); read_bytes.append(len(data)); return data
                return real_read(fd, maximum)
            def expired():
                raise inspection.HostInspectionError("PATH", "Frozen exhausted capture deadline", state="TIMEOUT")
            with patch.object(inspection.os, "read", side_effect=bounded_read):
                if kind == "within":
                    result = self.reconcile_historical(package, capture=True)
                    self.assertEqual(result["state"], "OBSERVED_UNAPPROVED_AS_RECORDED")
                    self.assertEqual(sum(read_bytes), len(b"outer-start\n"))
                else:
                    self.refuses("CHI-EVIDENCE", self.reconcile_historical, package, capture=True,
                                 deadline=expired if kind == "deadline" else None)
            self.assertLessEqual(sum(read_bytes), len(b"outer-start\n"))

    def test_SUP_16(self):
        self.case_HI11("C")
        self.new_fixture("later-finalization")
        def fault(store, path, value, writes):
            if path.name == "failure.json":
                raise OSError(28, "Mocked failure-evidence full disk")
        error, controller = self.assert_failed_observation("CHI-EVIDENCE", variant="HI11-C", write_fault=fault)
        self.assertIs(error.supervisor_exception, controller.last_failure)
        self.assertIs(error.process_record, controller.last_failure.process_record)
        self.assertIn("original_failure", error.details)

    def test_PRE_04_bounded_exact_trees(self):
        for kind in ("valid", "missing", "extra", "file-mode", "directory-mode"):
            root = self.base / ("exact-tree-" + kind)
            path = put(root / "nested/data", b"frozen bytes")
            files, directories = {"nested/data": file_binding(path)}, {"nested": oct(stat.S_IMODE(path.parent.stat().st_mode))}
            if kind == "missing":
                path.unlink()
            elif kind == "extra":
                put(root / "extra", b"not in selected inventory")
            elif kind == "file-mode":
                path.chmod(0o644)
            elif kind == "directory-mode":
                path.parent.chmod(0o700 if directories["nested"] != "0o700" else 0o755)
            if kind == "valid":
                inspection._check_installed_tree(root, files, directories)
            else:
                self.refuses("CHI-RUNTIME", inspection._check_installed_tree, root, files, directories)
        root = self.base / "bounded-entries"
        for name in ("one", "two", "three"):
            put(root / name, b"inert")
        self.refuses("CHI-RUNTIME", list, inspection._walk_bounded(root, 2, category="RUNTIME"))
        calls = []
        def stop():
            calls.append(1)
            if len(calls) == 3:
                raise inspection.HostInspectionError("RUNTIME", "Frozen traversal deadline", state="TIMEOUT")
        self.refuses("CHI-RUNTIME", list, inspection._walk_bounded(root, 2048, check=stop, category="RUNTIME"))
        validated = self.fixture.validated()
        store = inspection._EvidenceStore(validated)
        large = Path(self.fixture.plan["evidence"]["attempt_root"]) / "oversized"
        with large.open("wb") as stream:
            stream.truncate(67108865)
        self.refuses("CHI-EVIDENCE", store.budget)
        historical = self.preparer.provider.dependency_inventory(inspection.ROOT)
        self.assertEqual(len(historical), 24)

    def test_REVIEW_outcome_only_count(self):
        for kind in ("valid", "pid-only", "wrong-command", "missing-raw-descriptor", "partial-raw"):
            f = self.new_fixture("outcome-only-" + kind)
            package = self.historical_package()
            paths, outputs = f.plan["evidence"]["outputs"]["node_version"], f.plan["evidence"]["outputs"]
            for path in (paths["intent"], paths["started"], paths["postflight"], outputs["completion"]):
                Path(path).unlink()
            outcome = package["commands"]["node_version"]["outcome"]
            if kind == "pid-only":
                outcome["process"] = {"pid": 4242}
            elif kind == "wrong-command":
                process = deepcopy(outcome["process"]); process["argv"] = ["/unrelated/command"]
                outcome["process"] = outcome["decoded_raw_process"] = process
                outcome["artifacts"]["raw_process"] = json_file(Path(paths["supervisor_outcome"]["raw"]), process)
            elif kind == "missing-raw-descriptor":
                outcome["artifacts"].pop("raw_process")
            elif kind == "partial-raw":
                outcome["artifacts"]["raw_process"] = descriptor(put(Path(paths["supervisor_outcome"]["raw"]), b'{"pid":'))
            json_file(Path(paths["supervisor_outcome"]["committed"]), outcome)
            if kind == "valid":
                result = self.reconcile_historical(package)
                self.assertEqual(result["commands"][0]["actual_direct_starts"], 1)
                self.assertEqual(result["commands"][0]["observed_direct_starts"], 1)
                self.assertEqual(result["state"], "UNKNOWN")
                self.assertFalse(result["evidence_finalized"])
            else:
                self.refuses("CHI-EVIDENCE", self.reconcile_historical, package)

    def test_REVIEW_empty_evidence_directory(self):
        for name in ("empty", "node_version/empty"):
            f = self.new_fixture("directory-" + name.replace("/", "-"))
            package = self.historical_package()
            extra = Path(f.plan["evidence"]["attempt_root"]) / name
            extra.mkdir(mode=0o700)
            self.refuses("CHI-EVIDENCE", self.reconcile_historical, package)
            self.assertTrue(extra.is_dir())

    def test_REVIEW_named_git_alias(self):
        for kind in ("missing-alias", "changed-alias", "missing-guard"):
            self.new_fixture("named-git-" + kind)
            original_guards = inspection._check_guards
            with self.static_admission() as (driver, runtime, calls):
                f = self.fixture
                if kind == "missing-alias":
                    alias = f.base / "canonical-only-git-alias"; alias.symlink_to(f.git)
                    f.plan["host_static"]["roles"]["inspector_runtime"].remove(str(f.git))
                    f.plan["host_static"]["roles"]["inspector_runtime"].append(str(alias))
                    f.plan["host_static"]["aliases"].pop(str(f.git))
                    f.plan["host_static"]["aliases"][str(alias)] = inspection._alias(alias)
                elif kind == "changed-alias":
                    f.plan["host_static"]["aliases"][str(f.git)]["symlink"] = True
                    f.plan["host_static"]["aliases"][str(f.git)]["link_target"] = "changed-target"
                else:
                    guards = [inspection._path_row(Path(name)) for name in inspection._existing_chain(f.git)]
                    f.plan["host_static"]["path_guards"] = [row for row in guards if row["path"] != str(f.git)]
                f.save_plan()
                if kind == "missing-guard":
                    def actual_guard(rows, required, **kwargs):
                        self.assertIn(str(f.git), required)
                        return original_guards(rows, [str(f.git)], **kwargs)
                    with patch.object(inspection, "_check_guards", side_effect=actual_guard):
                        self.refuses("CHI-PATH", inspection.validate_inspection_plan, f.plan_path, f.plan_descriptor["sha256"])
                else:
                    self.refuses("CHI-INSPECTOR", inspection.validate_inspection_plan, f.plan_path, f.plan_descriptor["sha256"])
                self.assertEqual(calls, [])

    def test_REVIEW_process_group_type(self):
        for kind in ("bool", "float", "int"):
            self.new_fixture("callback-group-" + kind)
            variant = "HI17-C-start-group-" + kind
            if kind == "int":
                with self.observation(variant=variant) as (_, controller, writes):
                    result = self.observe()
                self.assertEqual(result["state"], "OBSERVED_UNAPPROVED")
                self.assertEqual(len(controller.starts), 2)
            else:
                error, controller = self.assert_failed_observation("CHI-PROCESS", variant=variant)
                self.assertEqual(controller.starts[0]["pid"], 1)
                self.assertIs(type(controller.starts[0]["process_group"]), bool if kind == "bool" else float)
                self.assertEqual(error.process_record["pid"], 1)
                self.assertIs(type(error.process_record["process_group"]), int)
                outcome = json.loads(Path(self.fixture.plan["evidence"]["outputs"]["node_version"]["supervisor_outcome"]["committed"]).read_bytes())
                self.assertEqual(outcome["observed_start"], controller.starts[0])
                self.assertEqual(outcome["process"], error.process_record)
            f = self.new_fixture("retained-group-" + kind)
            package = self.historical_package()
            paths, outputs = f.plan["evidence"]["outputs"]["node_version"], f.plan["evidence"]["outputs"]
            for path in (paths["postflight"], paths["supervisor_outcome"]["committed"], outputs["completion"]):
                Path(path).unlink()
            started = package["commands"]["node_version"]["start"]
            started["process"]["pid"] = 1
            started["process"]["process_group"] = True if kind == "bool" else 1.0 if kind == "float" else 1
            json_file(Path(paths["started"]), started)
            if kind == "int":
                retained = self.reconcile_historical(package)
                self.assertEqual(retained["commands"][0]["actual_direct_starts"], 1)
                self.assertEqual(retained["commands"][0]["observed_direct_starts"], 1)
                self.assertEqual(retained["state"], "UNKNOWN")
            else:
                self.refuses("CHI-EVIDENCE", self.reconcile_historical, package)


def _control_test(control):
    def test(self):
        self.run_control(control)
    test.__name__ = "test_" + control.replace("-", "_")
    test.__doc__ = "Frozen independent control " + control + "; synthetic/filesystem/mocked only."
    return test


for _group, _variants in CONTROL_VARIANTS.items():
    for _variant in _variants:
        _control = _group + "-" + _variant
        setattr(HostInspectionControls, "test_" + _control.replace("-", "_"), _control_test(_control))


if __name__ == "__main__":
    unittest.main()
