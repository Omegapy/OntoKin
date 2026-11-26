"""Development tests of the 0.2.0 provider, the version dispatch and the 0.2.0 probe's preserved body.

C271-P33 gate MI, worker W5. Standard library only. The inputs are synthetic HOST and configuration
documents and synthetic trees. Substituted boundaries (the Darwin supervisor, the host readers, the
selection, the Python inventory and the runtime check) are labelled: the provider's own results then
carry the label ``mocked``. These are development tests, not the independently frozen controls.

Starts: SourceGitTests start a /bin/sh stand-in for the bound Git implementation, which answers the
source checks' read-only queries from files and logs every invocation; no other test starts a process.
No test starts Node, ldd, codesign or Git itself, and no test runs the probe.
"""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from prototypes.static_tray_v01 import current_host_observation_v02 as observation
from prototypes.static_tray_v01 import current_host_readback_v01 as v01
from prototypes.static_tray_v01 import current_host_readback_v02 as v02
from prototypes.static_tray_v01 import supervisor_darwin_v01
from prototypes.static_tray_v01.format_check import ENVIRONMENT
from prototypes.static_tray_v01.supervisor import Clock, Stop
from tools import check_local

ROOT = v02.ROOT
INTERFACES = ROOT / "docs/engineering/localized-repair-c271/macos-implementation-p33/interfaces"
PROBE_MAP = INTERFACES / "W5-PROBE-MAP.json"
PROBE_V01 = ROOT / "prototypes/static_tray_v01/current_host_readback_v01.mjs"
PROBE_V02 = ROOT / "prototypes/static_tray_v01/current_host_readback_v02.mjs"
CF_VALUE = "0x1F5:0x0:0x0"
BOOT = "00000000-0000-4000-8000-0000000000a1"
OTHER_BOOT = "00000000-0000-4000-8000-0000000000b2"
SCIENTIFIC_V01_LINES = [(1, 38), (679, 679), (683, 691), (695, 809)]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def binding(path):
    data = Path(path).read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "mode": oct(Path(path).stat().st_mode & 0o7777)}


def descriptor(path):
    return {"path": str(path), **binding(path)}


def write(path, data, mode=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if mode is not None:
        path.chmod(mode)
    return path


def resolved_temporary(test, prefix):
    holder = tempfile.TemporaryDirectory(prefix=prefix)
    test.addCleanup(holder.cleanup)
    return Path(os.path.realpath(holder.name))


def utc(offset_seconds):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


def no_process_start(*args, **kwargs):
    raise AssertionError("A development test of the provider started a process")


class World:
    """A synthetic HOST/0.2.0 that is consistent with its configuration; nothing in it is executed."""

    def __init__(self, base):
        self.base = base
        self.runtime = base / "runtime"
        self.node = write(self.runtime / "bin/node", b"synthetic node bytes; never executed\n", 0o755)
        self.archive = write(base / "archives" / v02.NODE_ARCHIVE, b"synthetic official archive bytes\n", 0o644)
        self.archive_sha256 = sha(self.archive)
        node_binding = binding(self.node)
        self.node_source_content = {
            "schema": v02.PREFIX + "node-source/0.2.0", "contract": v02.CONTRACT,
            "archive": {"name": v02.NODE_ARCHIVE, "sha256": self.archive_sha256, "size_bytes": self.archive.stat().st_size},
            "checksum_file": dict(observation.NODE_CHECKSUM_FILE),
            "signature_check": {"status": "not_performed", "detail": "synthetic"},
            "member_inventory_sha256": "ab" * 32,
            "extracted": {"member": observation.NODE_MEMBER, "path": "bin/node", **node_binding}}
        node_source = write(self.runtime / "NODE-SOURCE.json", canonical(self.node_source_content), 0o644)
        install_plan = write(base / "install/plan.json", b"{}", 0o644)
        install_result = write(base / "install/result.json", b"{}", 0o644)
        self.framework = str(base / "framework/Python.framework/Versions/3.12")
        self.venv = str(base / "venv")
        self.launcher = self.venv + "/bin/python"
        self.process_image = self.framework + "/" + observation.PROCESS_IMAGE
        self.inventory = {
            "schema": observation.PYTHON_INVENTORY_SCHEMA,
            "framework": {"root": self.framework, "entries": {
                "bin": {"kind": "directory", "mode": "0o755"},
                "bin/python3.12": {"kind": "file", "sha256": "c1" * 32, "size_bytes": 52000, "mode": "0o755"},
                "lib/python3.12/os.py": {"kind": "file", "sha256": "c2" * 32, "size_bytes": 40000, "mode": "0o644"}}},
            "venv": {"root": self.venv, "entries": {
                "bin/python": {"kind": "symlink", "target": "python3.12"},
                "pyvenv.cfg": {"kind": "file", "sha256": "c3" * 32, "size_bytes": 90, "mode": "0o644"}}},
            "selection": {"launcher": self.launcher, "version_directory": "3.12"},
            "closure": {"external": {}, "images": {}, "links": []}}
        self.inventory_path = write(base / "python-inventory.json", canonical(self.inventory), 0o644)
        self.git = write(base / "git/bin/git", b"#!/bin/sh\n# synthetic Git implementation; never executed here\nexit 1\n", 0o755)
        self.git_record = {"path": str(self.git), **binding(self.git), "version": "git version 2.50.1 (synthetic)"}
        self.deps = base / "deps"
        self.deps.mkdir()
        self.source_inventory = write(base / "source-inventory.json", b"{}", 0o644)
        self.dependency_inventory = write(base / "dependency-inventory.json", b"{}", 0o644)
        self.platform = {"system": "Darwin", "release": "25.6.0", "version": "Darwin Kernel Version 25.6.0: synthetic",
                         "machine": "arm64", "proc_translated": 0, "boot_session_uuid": BOOT}
        plist = {"state": "present", "sha256": "e1" * 32, "size_bytes": 500, "mode": "0o644", "product_name": "macOS",
                 "product_version": "26.6.2", "product_build_version": "25G83", "product_version_extra": None}
        self.os = {"system_version": {**plist, "path": observation.SYSTEM_VERSION_PATH},
                   "cryptex": {**plist, "path": "/System/Volumes/Preboot/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist",
                               "sha256": "e2" * 32, "link_path": observation.CRYPTEX_SYSTEM_VERSION_PATH,
                               "hops": [{"path": "/System/Cryptexes/OS", "target": "../../System/Volumes/Preboot/Cryptexes/OS"}]}}
        self.inspections = {
            "node_version": self.inspection("node", [str(self.node), "--version"], dict(ENVIRONMENT), "v24.22.1\n"),
            "git_version": self.inspection("git", [str(self.git), "--version"], dict(observation.GIT_ENVIRONMENT),
                                           self.git_record["version"] + "\n")}
        self.host = {
            "schema": v02.PREFIX + "host/0.2.0", "contract": v02.CONTRACT, "design_revision": 4,
            "amendments": ["P33-AMENDMENT-001"], "profile": v02.PROFILE, "executor": v02.EXECUTOR,
            "observed_at_utc": utc(-5),
            "plan": descriptor(write(base / "observation-plan.json", b"{}", 0o644)),
            "observer": {"path": str(ROOT / observation.ENTRY_POINT), "sha256": "d0" * 32, "size_bytes": 1, "mode": "0o644"},
            "platform": self.platform, "os": self.os,
            "environment": {"declared": dict(ENVIRONMENT), "cf_user_text_encoding": CF_VALUE},
            "python": {"launcher": self.launcher, "venv": self.venv, "framework": self.framework,
                       "interpreter": {"implementation": sys.implementation.name, "version": platform.python_version(),
                                       "build_string": sys.version, "flags": {}, "executable": self.launcher,
                                       "base_executable": self.framework + "/bin/python3.12", "prefix": self.framework,
                                       "base_prefix": self.framework, "path": [], "process_image": self.process_image},
                       "selection": self.inventory["selection"], "inventory": descriptor(self.inventory_path),
                       "inventory_sha256": sha(self.inventory_path), "packages": dict(observation.PYTHON_PINS),
                       "records": {}, "lock": descriptor(ROOT / v02.MACOS_LOCK)},
            "runtime": {"directory": str(self.runtime), "executable": str(self.node), "version": "v24.22.1",
                        "binding": node_binding, "archive": descriptor(self.archive),
                        "node_source": {**descriptor(node_source), "content": self.node_source_content},
                        "layout": {"root_mode": "0o755", "bin_mode": "0o755", "entries": ["NODE-SOURCE.json", "bin", "bin/node"]},
                        "macho": {"magic": "0xfeedfacf", "filetype": "MH_EXECUTE", "commands": []},
                        "install": {"plan": descriptor(install_plan), "result": descriptor(install_result),
                                    "purpose": "selected-node", "state": "INSTALLED_EXACT"}},
            "git": self.git_record,
            "dependencies": {"root": str(self.deps), "inventory": descriptor(self.dependency_inventory),
                             "archive": descriptor(self.archive), "files": 24, "install": {}},
            "source": {"root": str(ROOT), "commit": "1" * 40, "tree": "2" * 40, "tree_check": "planned value",
                       "inventory": descriptor(self.source_inventory), "head": {}},
            "inspections": {name: descriptor(path) for name, path in self.inspections.items()},
            "starts": {"node": 1, "other": 1}, "labels": None, "claims": dict(observation.CLAIMS)}
        self.host["labels"] = self.host_labels()

    def inspection(self, name, argv, environment, stdout):
        process = {"argv": argv, "cwd": str(self.base / "attempt" / name), "environment": environment,
                   "label": "host-" + name + "-version", "start_monotonic": 10.0, "pid": 4242, "process_group": 4242,
                   "returncode": 0, "observed_log_bytes": len(stdout), "retained_log_bytes": len(stdout),
                   "cleanup": {"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 0},
                   "handles_closed": True, "error": None, "end_monotonic": 10.2}
        receipt = {"schema": v02.PREFIX + "inspection/0.2.0", **v02._identity(), "argv": argv, "environment": environment,
                   "timeout_ms": 5000,
                   "started_at_utc": utc(-30), "finished_at_utc": utc(-29), "process": process, "stdout": stdout, "stderr": ""}
        return write(self.base / ("inspection-" + name + ".json"), canonical(receipt), 0o644)

    def host_labels(self):
        host = self.host
        return {"executor": v02.EXECUTOR, "contract": v02.CONTRACT, "design_revision": 4,
                "amendments": ["P33-AMENDMENT-001"], "profile": v02.PROFILE, "os": v02._os_label(host["os"]),
                "node": {"archive": v02.NODE_ARCHIVE, "archive_sha256": self.archive_sha256,
                         "executable": host["runtime"]["binding"], "signature_check": "not_performed"},
                "python_inventory_sha256": host["python"]["inventory_sha256"],
                "git": {"path": host["git"]["path"], "sha256": host["git"]["sha256"]},
                "run_kind": "host-observation", "boundary": "real"}

    def write_host(self, host=None):
        path = self.base / "HOST.json"
        if path.exists():
            path.unlink()
        return descriptor(write(path, canonical(host or self.host), 0o644))

    def config(self, evidence_root, host=None):
        return {"schema": v02.PREFIX + "config/0.2.0", "contract": v02.CONTRACT,
                "contract_source": descriptor(ROOT / v02.CONTRACT_PATH),
                "amendment_adoption": descriptor(ROOT / v02.AMENDMENT_ADOPTION_PATH),
                "source": {"root": str(ROOT), "commit": "1" * 40, "tree": "2" * 40,
                           "inventory": descriptor(self.source_inventory)},
                "host": self.write_host(host),
                "dependencies": {"root": str(self.deps), "inventory": descriptor(self.dependency_inventory)},
                "runtime": {"executable": str(self.node), "version": "v24.22.1"},
                "methods": descriptor(write(self.base / "methods.json", b"{}", 0o644)),
                "evidence_root": str(evidence_root), "parent": None}

    def state(self, **changes):
        state = {"platform": deepcopy(self.platform), "os": deepcopy(self.os)}
        for key, value in changes.items():
            if key == "boot":
                state["platform"]["boot_session_uuid"] = value
            elif key == "build":
                state["os"]["system_version"]["product_build_version"] = value
            elif key == "cryptex_build":
                state["os"]["cryptex"]["product_build_version"] = value
            elif key == "cryptex_hop":
                state["os"]["cryptex"]["hops"][0]["target"] = value
            else:
                raise KeyError(key)
        return state

    @contextmanager
    def mocked_host(self, *, states=None, inventory=None, runtime=None):
        """Substitute the host readers, the Python inventory and the runtime check; results are labelled mocked."""
        sequence = list(states or [])

        def state(**_):
            return deepcopy(sequence.pop(0) if sequence else self.state())
        with ExitStack() as stack:
            stack.enter_context(patch.object(v02, "NODE_ARCHIVE_SHA256", self.archive_sha256))
            stack.enter_context(patch.object(v02, "host_state", side_effect=state))
            stack.enter_context(patch.object(observation, "read_process_image", return_value=self.process_image))
            stack.enter_context(patch.object(observation, "python_inventory",
                                             side_effect=lambda *a, **k: deepcopy(inventory or self.inventory)))
            stack.enter_context(patch.object(observation, "check_runtime",
                                             side_effect=lambda plan, **k: {**deepcopy(runtime or self.host["runtime"]),
                                                                            "references": []}))
            stack.enter_context(patch.object(v02.sys, "executable", self.launcher))
            stack.enter_context(patch.dict(v02._VERIFIED, {"host": None}))
            yield


class Cohort:
    """A synthetic qualifying cohort: configuration, manifest and one fresh CPU stage; the selection is mocked."""

    def __init__(self, world, *, case="Q01-positive"):
        self.world = world
        self.evidence = world.base / "evidence"
        self.cohort = self.evidence / "cohort"
        (self.cohort / "provider-ledgers").mkdir(parents=True)
        self.config = world.config(self.evidence)
        self.config_path = write(world.base / "selection" / "config.json", canonical(self.config), 0o600)
        self.digest = sha(self.config_path)
        self.selection = {"config": self.config, "path": str(self.config_path), "sha256": self.digest, "host": world.host,
                          "dependencies": {"files": {"tools/three_loader.mjs": {"sha256": "f1" * 32, "size_bytes": 1, "mode": "0o644"}}},
                          "methods": {}, "labels": None}
        self.selection_calls = 0
        self.manifest_path = self.cohort / "supplemental-cpu.json"
        self.schedule = self.cohort / "unused-native-schedule"
        self.stage = self.cohort / case
        self.case = case

    def selection_boundary(self, *, failing_call=None, changed_host=None):
        """The mocked selection; it records the HOST it stands for, as the real verification does."""
        def selected(path, digest, root, **_):
            self.selection_calls += 1
            if failing_call is not None and self.selection_calls == failing_call:
                raise v02.CurrentHostBindingError("SOURCE", "Synthetic source change after preflight")
            assert (str(path), digest) == (str(self.config_path), self.digest)
            selection = deepcopy(self.selection)
            if changed_host is not None and self.selection_calls >= changed_host[0]:
                selection["host"] = changed_host[1]
            selection["labels"] = v02._labels(selection["host"])
            v02._VERIFIED["host"] = selection["host"]
            return selection
        return patch.object(v02, "_selection", side_effect=selected)

    def prepare(self):
        with self.selection_boundary():
            manifest, digest = v02.prepare_case_manifest(self.manifest_path, config_path=self.config_path,
                                                         config_sha256=self.digest, source_root=ROOT,
                                                         schedule_root=self.schedule)
        self.selection_calls = 0
        self.manifest, self.manifest_digest = manifest, digest
        self.stage.mkdir()
        artifact = write(self.stage / "synthetic.glb", b"glTF synthetic bytes", 0o644)
        audit = write(self.stage / "synthetic-audit.json", b'{"passed":true}', 0o644)
        job = {"slot": "CPU-" + self.case, "case": v02.CASES[self.case], "manifest": str(self.manifest_path),
               "supplemental_manifest_sha256": digest, "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
               "artifact": str(artifact), "artifact_sha256": sha(artifact), "audit": str(audit),
               "audit_sha256": sha(audit), "result": str(self.stage / "probe.json")}
        write(self.stage / "job.json", canonical(job), 0o644)
        self.argv = manifest["slots"][0]["argv"][:-1] + [str(self.stage / "job.json")]
        return self

    def environment(self):
        return patch.dict(os.environ, {v02.CONFIG_ENV: str(self.config_path), v02.DIGEST_ENV: self.digest})

    def run(self, *, env=None, facade=False):
        clock = Clock(total_ms=30000)
        started = []
        function = v01.guarded_run_process if facade else v02.guarded_run_process
        result = function(self.argv, stage=self.stage, label="synthetic-readback", clock=clock,
                          stage_end=clock.started + 28, env=dict(ENVIRONMENT) if env is None else env,
                          on_started=started.append)
        return result, started

    def ledger(self):
        return json.loads((self.cohort / "provider-ledgers" / self.case / "result.json").read_bytes())


def delegate(returncode=0):
    """A mocked Darwin supervisor: one recorded start and the original receipt fields; nothing is started."""
    calls = []

    def run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):
        calls.append(argv)
        record = {"argv": argv, "cwd": str(stage), "environment": env, "label": label, "start_monotonic": time.monotonic(),
                  "pid": 4242, "process_group": 4242, "returncode": None, "observed_log_bytes": 0,
                  "retained_log_bytes": 0, "cleanup": None, "handles_closed": False, "error": None}
        on_started(dict(record))
        write(Path(stage) / "probe.json", b'{"passed":true}', 0o600)
        final = {**record, "returncode": returncode, "handles_closed": True, "end_monotonic": time.monotonic(),
                 "cleanup": {"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 0}}
        if returncode:
            failure = Stop("OTRAY-E-BACKEND", "Child exited with status " + str(returncode))
            failure.process_record = {**final, "error": failure.as_dict()}
            raise failure
        return final
    return patch.object(supervisor_darwin_v01, "run_process", side_effect=run_process), calls


class VersionRefusalTests(unittest.TestCase):
    """Each version's entry points refuse the other version's documents (contract section 1)."""

    def setUp(self):
        self.base = resolved_temporary(self, "w5-version-")

    def config_file(self, value):
        path = write(self.base / ("config-" + str(len(list(self.base.iterdir()))) + ".json"), canonical(value), 0o600)
        return path, sha(path)

    def test_v02_entry_points_refuse_a_v01_configuration(self):
        old = {key: None for key in v01.CONFIG_KEYS} | {"schema": v01.PREFIX + "config/0.1.0", "contract": v01.CONTRACT}
        relabelled = {key: None for key in v02.CONFIG_KEYS} | {"schema": v01.PREFIX + "config/0.1.0", "contract": v01.CONTRACT}
        for value in (old, relabelled):
            path, digest = self.config_file(value)
            calls = {
                "validate_selection": lambda: v02.validate_selection(path, digest, ROOT),
                "git_binding_from_selection": lambda: v02.git_binding_from_selection(path, digest),
                "prepare_case_manifest": lambda: v02.prepare_case_manifest(self.base / "m.json", config_path=path,
                                                                           config_sha256=digest, source_root=ROOT,
                                                                           schedule_root=self.base / "s"),
                "verify_case_manifest": lambda: v02.verify_case_manifest(self.base / "m.json", config_path=path,
                                                                         config_sha256=digest, source_root=ROOT,
                                                                         schedule_root=self.base / "s"),
                "derive_workspace_binding": lambda: v02.derive_workspace_binding(path, digest, ROOT, self.base / "w",
                                                                                 self.base / "o", {}, {})}
            for name, call in calls.items():
                with self.subTest(keys=sorted(value)[:3], entry=name), self.assertRaises(v02.CurrentHostBindingError) as caught:
                    call()
                self.assertEqual(caught.exception.code, "CH-SCHEMA")
                self.assertEqual(caught.exception.refusal_record["schema"], v02.PREFIX + "refusal/0.2.0")
            with self.subTest(entry="setup_cpu_cohort"), patch.dict(os.environ, {v02.CONFIG_ENV: str(path), v02.DIGEST_ENV: digest}):
                class Subject:
                    pass
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    v02.setup_cpu_cohort(Subject)
                self.assertEqual(caught.exception.code, "CH-SCHEMA")
                self.assertIsNone(Subject.root)
            with self.subTest(entry="guarded_run_process"), \
                    patch.dict(os.environ, {v02.CONFIG_ENV: str(path), v02.DIGEST_ENV: digest}), \
                    patch.object(supervisor_darwin_v01, "run_process") as process:
                stage = self.base / "Q01-positive"
                argv = ["node"] * 6 + ["--expected-config-sha256", digest, "--job", str(stage / "job.json")]
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    v02.guarded_run_process(argv, stage=stage, label="synthetic-readback", clock=Clock(total_ms=30000),
                                            stage_end=0)
                self.assertEqual(caught.exception.code, "CH-SCHEMA")
                self.assertEqual(caught.exception.refusal_record["actual_checker_starts"], 0)
                process.assert_not_called()

    def test_v01_code_refuses_a_v02_configuration(self):
        new = {key: None for key in v02.CONFIG_KEYS} | {"schema": v02.PREFIX + "config/0.2.0", "contract": v02.CONTRACT}
        path, digest = self.config_file(new)
        original = v01._V010_ENTRY_POINTS
        calls = {
            "validate_selection": lambda: original["validate_selection"](path, digest, ROOT),
            "prepare_case_manifest": lambda: original["prepare_case_manifest"](
                self.base / "m.json", config_path=path, config_sha256=digest, source_root=ROOT, schedule_root=self.base / "s"),
            "verify_case_manifest": lambda: original["verify_case_manifest"](
                self.base / "m.json", config_path=path, config_sha256=digest, source_root=ROOT, schedule_root=self.base / "s"),
            "derive_workspace_binding": lambda: original["derive_workspace_binding"](
                path, digest, ROOT, self.base / "w", self.base / "o", {}, {})}
        for name, call in calls.items():
            with self.subTest(entry=name), self.assertRaises(v01.CurrentHostBindingError) as caught:
                call()
            self.assertEqual(caught.exception.code, "CH-SCHEMA")
            self.assertEqual(caught.exception.refusal_record["schema"], v01.PREFIX + "refusal/0.1.0")

    def test_v02_documents_are_versioned_and_refuse_v01_documents(self):
        world = World(self.base)
        for kind, keys in (("host", v02.HOST_KEYS), ("lock", v02.MANIFEST_KEYS), ("workspace", v02.WORKSPACE_KEYS),
                           ("source", ("schema", "files")), ("dependencies", ("schema", "files", "directories", "archive")),
                           ("methods", ("schema", "source_test", "original_bodies", "discovery")),
                           ("discovery", ("schema", "method_ids", "baseline_map")), ("config", v02.CONFIG_KEYS)):
            document = {key: None for key in keys}
            with self.subTest(kind=kind):
                v02._schema(document | {"schema": v02.PREFIX + kind + "/0.2.0"}, kind, keys)
                with self.assertRaises(v02.CurrentHostBindingError):
                    v02._schema(document | {"schema": v02.PREFIX + kind + "/0.1.0"}, kind, keys)
        old_host = deepcopy(world.host) | {"schema": v02.PREFIX + "host/0.1.0"}
        with self.assertRaises(v02.CurrentHostBindingError) as caught:
            v02._host_document({"host": world.write_host(old_host)})
        self.assertIn("Unsupported host schema", caught.exception.reason)
        receipt = json.loads(world.inspections["node_version"].read_bytes()) | {"schema": v02.PREFIX + "inspection/0.1.0"}
        path = write(self.base / "old-inspection.json", canonical(receipt), 0o644)
        with self.assertRaises(v02.CurrentHostBindingError):
            v02._verify_inspection(descriptor(path), [str(world.node), "--version"], dict(ENVIRONMENT), "v24.22.1\n")


class DispatchTests(unittest.TestCase):
    """Plan section 4.8: the facade dispatches on the schema of the digest-checked configuration."""

    def setUp(self):
        self.base = resolved_temporary(self, "w5-dispatch-")
        # D-20: no test may leave the facade's cohort binding behind.
        self.addCleanup(v01._COHORT_BINDING.__setitem__, "version", None)
        self.v02_path = write(self.base / "v02.json", canonical({"schema": v02.PREFIX + "config/0.2.0"}), 0o600)
        self.v01_path = write(self.base / "v01.json", canonical({"schema": v01.PREFIX + "config/0.1.0"}), 0o600)
        self.other_path = write(self.base / "other.json", canonical({"schema": v01.PREFIX + "config/0.3.0"}), 0o600)

    def calls(self, path, digest):
        kwargs = {"config_path": path, "config_sha256": digest, "source_root": ROOT, "schedule_root": self.base / "s"}
        return {
            "validate_selection": ((path, digest, ROOT), {}),
            "derive_workspace_binding": ((path, digest, ROOT, self.base / "w", self.base / "o", {}, {}), {}),
            "prepare_case_manifest": ((self.base / "m.json",), kwargs),
            "verify_case_manifest": ((self.base / "m.json",), kwargs | {"check": no_process_start}),
        }

    def test_each_entry_point_dispatches_by_the_configuration_schema(self):
        for label, path, expected in (("0.2.0", self.v02_path, "v02"), ("0.1.0", self.v01_path, "v01"),
                                      ("another schema", self.other_path, "v01")):
            for name, (args, kwargs) in self.calls(path, sha(path)).items():
                with self.subTest(schema=label, entry=name), patch.object(v02, name, return_value="v02") as new, \
                        patch.dict(v01._V010_ENTRY_POINTS, {name: lambda *a, **k: "v01"}):
                    self.assertEqual(getattr(v01, name)(*args, **kwargs), expected)
                    self.assertEqual(new.call_count, 1 if expected == "v02" else 0)
                    if expected == "v02":
                        self.assertEqual(new.call_args.args, args)
        with self.subTest(case="digest mismatch keeps the 0.1.0 code"), patch.object(v02, "validate_selection") as new:
            with self.assertRaises(v01.CurrentHostBindingError) as caught:
                v01.validate_selection(self.v02_path, "0" * 64, ROOT)
            self.assertEqual(caught.exception.code, "CH-SELECTION")
            new.assert_not_called()

    def test_environment_entry_points_dispatch_by_the_selected_configuration(self):
        class Subject:
            pass
        stage = self.base / "Q01-positive"
        invocations = {
            "guarded_run_process": lambda: v01.guarded_run_process(["node"], stage=stage, label="synthetic-readback",
                                                                   clock=None, stage_end=0),
            "setup_cpu_cohort": lambda: v01.setup_cpu_cohort(Subject),
            "finish_cpu_cohort": lambda: v01.finish_cpu_cohort(Subject)}
        for label, path, expected in (("0.2.0", self.v02_path, "v02"), ("0.1.0", self.v01_path, "v01")):
            for name, invoke in invocations.items():
                with self.subTest(schema=label, entry=name), \
                        patch.dict(os.environ, {v01.CONFIG_ENV: str(path), v01.DIGEST_ENV: sha(path)}), \
                        patch.object(v02, name, return_value="v02") as new, \
                        patch.dict(v01._V010_ENTRY_POINTS, {name: lambda *a, **k: "v01"}):
                    self.assertEqual(invoke(), expected)
                    self.assertEqual(new.call_count, 1 if expected == "v02" else 0)

    def test_d20_a_cohort_keeps_the_version_its_setup_selected_until_its_accounting(self):
        """Review finding I-01: a configuration that changes after setup does not switch the cohort's version."""
        stage = self.base / "Q01-positive"
        for label, path, chosen, other in (("0.2.0", self.v02_path, "v02", "v01"), ("0.1.0", self.v01_path, "v01", "v02")):
            with self.subTest(schema=label):
                subject = type("Subject", (), {})
                calls = []

                def implementation(name, version):
                    def call(*args, **kwargs):
                        calls.append((name, version))
                        return version + " " + name
                    return call
                originals = {name: implementation(name, "v01") for name in ("setup_cpu_cohort", "guarded_run_process",
                                                                            "finish_cpu_cohort")}
                with patch.dict(os.environ, {v01.CONFIG_ENV: str(path), v01.DIGEST_ENV: sha(path)}), \
                        patch.object(subprocess, "Popen", side_effect=no_process_start), \
                        patch.object(v02, "setup_cpu_cohort", implementation("setup_cpu_cohort", "v02")), \
                        patch.object(v02, "guarded_run_process", implementation("guarded_run_process", "v02")), \
                        patch.object(v02, "finish_cpu_cohort", implementation("finish_cpu_cohort", "v02")), \
                        patch.dict(v01._V010_ENTRY_POINTS, originals):
                    self.assertEqual(v01.setup_cpu_cohort(subject), chosen + " setup_cpu_cohort")
                    self.assertEqual(vars(subject)[v01.DISPATCH_VERSION_ATTRIBUTE], label)
                    original_bytes = path.read_bytes()
                    path.write_bytes(original_bytes + b" ")  # the configuration changes after the setup
                    try:
                        self.assertFalse(v01._environment_selects_v02())
                        self.assertEqual(v01.guarded_run_process(["node"], stage=stage, label="synthetic-readback",
                                                                 clock=None, stage_end=0), chosen + " guarded_run_process")
                        self.assertEqual(v01.finish_cpu_cohort(subject), chosen + " finish_cpu_cohort")
                    finally:
                        path.write_bytes(original_bytes)
                self.assertEqual(calls, [("setup_cpu_cohort", chosen), ("guarded_run_process", chosen),
                                         ("finish_cpu_cohort", chosen)])
                self.assertNotIn(other, {version for _, version in calls})
                self.assertIsNone(v01._COHORT_BINDING["version"])
                self.assertNotIn(v01.DISPATCH_VERSION_ATTRIBUTE, vars(subject))

    def test_d20_the_0_2_0_accounting_records_a_configuration_changed_after_setup(self):
        """Review finding I-01: the real 0.2.0 accounting refuses and writes cohort/0.2.0 with labels; no 0.1.0 document."""
        root = self.base / "cohort"
        (root / "provider-ledgers").mkdir(parents=True)

        def passed_setup(cls):  # stands for a 0.2.0 setup that passed; it starts nothing
            cls.root, cls.temporary, cls.manifest_path = root, None, root / "supplemental-cpu.json"
        subject = type("Subject", (), {})
        with patch.dict(os.environ, {v01.CONFIG_ENV: str(self.v02_path), v01.DIGEST_ENV: sha(self.v02_path)}), \
                patch.object(subprocess, "Popen", side_effect=no_process_start), \
                patch.object(os, "posix_spawn", side_effect=no_process_start), \
                patch.object(v02, "setup_cpu_cohort", side_effect=passed_setup), \
                patch.dict(v01._V010_ENTRY_POINTS, {"finish_cpu_cohort": lambda cls: self.fail("the 0.1.0 accounting ran")}):
            v01.setup_cpu_cohort(subject)
            self.v02_path.write_bytes(self.v02_path.read_bytes() + b" ")
            with self.assertRaises(v02.CurrentHostBindingError):
                v01.finish_cpu_cohort(subject)
        record = json.loads((root / "cohort.json").read_bytes())
        self.assertEqual((record["schema"], record["contract"], record["design_revision"], record["amendments"]),
                         (v02.PREFIX + "cohort/0.2.0", v02.CONTRACT, 4, ["P33-AMENDMENT-001"]))
        self.assertIs(record["passed"], False)
        self.assertIn("labels", record)
        self.assertEqual(sorted(p.name for p in root.iterdir()), ["cohort.json", "provider-ledgers"])
        self.assertIsNone(v01._COHORT_BINDING["version"])

    def test_d20_a_failed_setup_ends_the_binding(self):
        """Review finding I-01: unittest runs no class teardown after a failed setup, so the facade ends the binding."""
        subject = type("Subject", (), {})
        refusal = v02.CurrentHostBindingError("SELECTION", "synthetic setup refusal")
        with patch.dict(os.environ, {v01.CONFIG_ENV: str(self.v02_path), v01.DIGEST_ENV: sha(self.v02_path)}), \
                patch.object(v02, "setup_cpu_cohort", side_effect=refusal):
            with self.assertRaises(v02.CurrentHostBindingError) as caught:
                v01.setup_cpu_cohort(subject)
        self.assertIs(caught.exception, refusal)
        self.assertIsNone(v01._COHORT_BINDING["version"])
        self.assertNotIn(v01.DISPATCH_VERSION_ATTRIBUTE, vars(subject))

    def test_git_binding_from_selection_reads_host_and_starts_nothing(self):
        world = World(self.base)
        config = world.config(self.base)
        path = write(self.base / "selection.json", canonical(config), 0o600)
        with patch.object(subprocess, "Popen", side_effect=no_process_start), patch.object(os, "posix_spawn", side_effect=no_process_start):
            self.assertEqual(v01.git_binding_from_selection(path, sha(path)),
                             {"path": world.git_record["path"], "sha256": world.git_record["sha256"]})
            old = {key: None for key in v01.CONFIG_KEYS} | {"schema": v01.PREFIX + "config/0.1.0", "contract": v01.CONTRACT}
            old_path = write(self.base / "old.json", canonical(old), 0o600)
            self.assertIsNone(v01.git_binding_from_selection(old_path, sha(old_path)))
            for bad, digest in ((path, "0" * 64), (self.other_path, sha(self.other_path))):
                with self.subTest(path=bad.name), self.assertRaises(v01.CurrentHostBindingError):
                    v01.git_binding_from_selection(bad, digest)
            changed = deepcopy(world.host)
            changed["labels"]["git"]["sha256"] = "0" * 64
            config_changed = world.config(self.base, changed)
            changed_path = write(self.base / "changed.json", canonical(config_changed), 0o600)
            with self.assertRaises(v02.CurrentHostBindingError):
                v01.git_binding_from_selection(changed_path, sha(changed_path))
            world.git.write_bytes(b"#!/bin/sh\nexit 2\n")
            path_again = write(self.base / "after-change.json", canonical(world.config(self.base)), 0o600)
            with self.assertRaises(v02.CurrentHostBindingError) as caught:
                v01.git_binding_from_selection(path_again, sha(path_again))
            self.assertIn("bytes differ", caught.exception.reason)


class SelectionRuleTests(unittest.TestCase):
    """S8: an ordinary run fails visibly at setup with the fixed reason; a partial selection is an error."""

    def subject(self):
        class Subject:
            pass
        return Subject

    def test_ordinary_run_setup_fails_visibly_with_the_fixed_reason(self):
        for environment in ({}, {v01.CONFIG_ENV: "", v01.DIGEST_ENV: ""}):
            with self.subTest(environment=sorted(environment)), patch.dict(os.environ, environment, clear=True):
                subject = self.subject()
                with self.assertRaises(v01.CurrentHostBindingError) as caught:
                    v01.setup_cpu_cohort(subject)
                error = caught.exception
                self.assertNotIsInstance(error, unittest.SkipTest)
                self.assertEqual(str(error), v01.ORDINARY_RUN_REASON)
                self.assertEqual(v01.ORDINARY_RUN_REASON,
                                 "No approved current-host readback selection: ordinary run, not a qualification")
                self.assertEqual(error.code, "CH-SELECTION")
                self.assertEqual(error.refusal_record["run_kind"], "ordinary")
                self.assertEqual(error.refusal_record["actual_checker_starts"], 0)
                self.assertFalse(error.refusal_record["evidence_finalized"])
                self.assertIsNone(subject.root)
                direct = self.subject()
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    v02.setup_cpu_cohort(direct)
                self.assertEqual(str(caught.exception), v02.ORDINARY_RUN_REASON)
                self.assertEqual(caught.exception.refusal_record["setup"]["run_kind"], "ordinary")
                self.assertEqual(caught.exception.refusal_record["labels"]["run_kind"], "ordinary")
                self.assertIsNone(direct.root)

    def test_partial_selection_is_an_error_not_an_ordinary_run(self):
        for environment in ({v01.CONFIG_ENV: "/nonexistent/selection.json"}, {v01.DIGEST_ENV: "a" * 64}):
            for module in (v01, v02):
                with self.subTest(environment=sorted(environment), module=module.__name__), \
                        patch.dict(os.environ, environment, clear=True):
                    with self.assertRaises(module.CurrentHostBindingError) as caught:
                        module.setup_cpu_cohort(self.subject())
                    self.assertEqual(caught.exception.code, "CH-SELECTION")
                    self.assertIn("Set both", caught.exception.reason)
                    self.assertNotEqual(caught.exception.reason, v01.ORDINARY_RUN_REASON)


class HostBindingTests(unittest.TestCase):
    """S2, S7, S10 and MC33: the Darwin host binding against a synthetic HOST, with mocked host readers."""

    def setUp(self):
        self.base = resolved_temporary(self, "w5-host-")
        self.world = World(self.base)

    def verify(self, host=None, **mocks):
        config = self.world.config(self.base, host)
        with self.world.mocked_host(**mocks):
            return v02._verify_host(config)

    def refused(self, host=None, **mocks):
        with self.assertRaises(v02.CurrentHostBindingError) as caught:
            self.verify(host, **mocks)
        return caught.exception

    def test_consistent_synthetic_host_is_accepted_and_labels_follow_it(self):
        config = self.world.config(self.base)
        with self.world.mocked_host():
            host = v02._verify_host(config)
            labels = v02._labels(host)
            self.assertIs(v02._VERIFIED["host"], host)
            self.assertEqual(v02._boundary(), "mocked")
        self.assertEqual(labels["executor"], "macos-arm64-local")
        self.assertEqual((labels["design_revision"], labels["amendments"]), (4, ["P33-AMENDMENT-001"]))
        self.assertEqual(labels["os"]["product_build_version"], "25G83")
        self.assertEqual(labels["os"]["cryptex"]["product_build_version"], "25G83")
        self.assertEqual(labels["node"]["archive_sha256"], self.world.archive_sha256)
        self.assertEqual(labels["python_inventory_sha256"], self.world.host["python"]["inventory_sha256"])
        self.assertEqual(labels["git"], {"path": str(self.world.git), "sha256": self.world.git_record["sha256"]})
        self.assertEqual((labels["run_kind"], labels["boundary"]), ("qualifying", "mocked"))

    def test_mc33_declared_node_version_other_than_v24_22_1_refuses_before_any_read(self):
        config = self.world.config(self.base)
        config["runtime"]["version"] = "v24.22.0"
        config["host"] = {"path": str(self.base / "absent-HOST.json"), "sha256": "a" * 64, "size_bytes": 1, "mode": "0o644"}
        with patch.object(supervisor_darwin_v01, "run_process") as process, self.world.mocked_host():
            with self.assertRaises(v02.CurrentHostBindingError) as caught:
                v02._verify_host(config)
            process.assert_not_called()
        self.assertEqual((caught.exception.code, caught.exception.reason), ("CH-RUNTIME", "Only Node v24.22.1 is admitted"))
        host = deepcopy(self.world.host)
        host["runtime"]["version"] = "v24.22.0"
        self.assertEqual(self.refused(host).code, "CH-RUNTIME")

    def test_host_naming_another_contract_revision_amendment_profile_or_executor_refuses(self):
        for key, value in (("contract", v01.CONTRACT), ("design_revision", 3), ("amendments", []),
                           ("profile", "linux-x86_64"), ("executor", "linux-local")):
            host = deepcopy(self.world.host) | {key: value}
            with self.subTest(key=key):
                self.assertEqual(self.refused(host).code, "CH-HOST")
        host = deepcopy(self.world.host)
        del host["design_revision"]
        self.assertEqual(self.refused(host).code, "CH-SCHEMA")

    def test_mc09_simulated_boot_os_build_or_cryptex_change_since_host_refuses(self):
        for change in ({"boot": OTHER_BOOT}, {"build": "25G84"}, {"cryptex_build": "25G84a"},
                       {"cryptex_hop": "../../elsewhere"}):
            with self.subTest(change=change):
                error = self.refused(states=[self.world.state(**change)])
                self.assertEqual(error.code, "CH-HOST")
                self.assertIn("at the host check", error.reason)
        translated = self.world.state()
        translated["platform"]["proc_translated"] = 1
        self.assertIn("Not native", self.refused(states=[translated]).reason)

    def test_mc31_host_environment_record_uses_the_predicate(self):
        accepted = (CF_VALUE, None)
        for recorded in accepted:
            host = deepcopy(self.world.host)
            host["environment"]["cf_user_text_encoding"] = recorded
            with self.subTest(recorded=recorded):
                self.assertEqual(v02._check_environment_record(host), recorded)
        refusals = {
            "extra declared variable": {"declared": dict(ENVIRONMENT) | {"EXTRA": "1"}, "cf_user_text_encoding": None},
            "missing declared variable": {"declared": {k: v for k, v in ENVIRONMENT.items() if k != "TZ"},
                                          "cf_user_text_encoding": None},
            "changed declared value": {"declared": dict(ENVIRONMENT) | {"LANG": "en_US.UTF-8"}, "cf_user_text_encoding": None},
            "CF inside the declared environment": {"declared": dict(ENVIRONMENT) | {observation.CF_NAME: CF_VALUE},
                                                   "cf_user_text_encoding": CF_VALUE},
            "empty CF value": {"declared": dict(ENVIRONMENT), "cf_user_text_encoding": ""},
            "non-string CF value": {"declared": dict(ENVIRONMENT), "cf_user_text_encoding": 245},
            "DYLD variable": {"declared": dict(ENVIRONMENT) | {"DYLD_INSERT_LIBRARIES": "/x"}, "cf_user_text_encoding": None}}
        for name, record in refusals.items():
            host = deepcopy(self.world.host) | {"environment": record}
            with self.subTest(case=name), self.assertRaises(v02.CurrentHostBindingError):
                v02._check_environment_record(host)

    def test_python_installation_trees_are_compared_as_exact_sets(self):
        added, missing, changed = (deepcopy(self.world.inventory) for _ in range(3))
        added["framework"]["entries"]["lib/python3.12/__pycache__/os.cpython-312.pyc"] = {
            "kind": "file", "sha256": "c4" * 32, "size_bytes": 1, "mode": "0o644"}
        del missing["venv"]["entries"]["pyvenv.cfg"]
        changed["framework"]["entries"]["lib/python3.12/os.py"]["sha256"] = "c5" * 32
        for name, inventory in (("added bytecode", added), ("missing pyvenv.cfg", missing), ("changed file", changed)):
            with self.subTest(case=name):
                error = self.refused(inventory=inventory)
                self.assertEqual(error.code, "CH-HOST")
                self.assertIn("exact sets", error.reason)
        with patch.object(v02.sys, "version", sys.version + " (other build)"):
            config = self.world.config(self.base)
            with self.world.mocked_host(), self.assertRaises(v02.CurrentHostBindingError):
                v02._verify_host(config)

    def test_runtime_git_inspection_and_label_drift_refuse(self):
        changed_runtime = deepcopy(self.world.host["runtime"])
        changed_runtime["binding"]["sha256"] = "9" * 64
        self.assertEqual(self.refused(runtime=changed_runtime).code, "CH-RUNTIME")
        host = deepcopy(self.world.host)
        host["runtime"]["archive"]["sha256"] = "8" * 64
        self.assertEqual(self.refused(host).code, "CH-RUNTIME")
        host = deepcopy(self.world.host)
        host["git"]["sha256"] = "7" * 64
        self.assertEqual(self.refused(host).code, "CH-HOST")
        mocked = deepcopy(self.world.host)
        mocked["labels"]["boundary"] = "mocked"
        self.assertIn("mocked boundary", self.refused(mocked).reason)
        receipt = json.loads(self.world.inspections["node_version"].read_bytes())
        receipt["stdout"] = "v24.22.0\n"
        changed = write(self.base / "inspection-node-changed.json", canonical(receipt), 0o644)
        host = deepcopy(self.world.host)
        host["inspections"]["node_version"] = descriptor(changed)
        self.assertIn("output differs", self.refused(host).reason)
        receipt = json.loads(self.world.inspections["git_version"].read_bytes())
        receipt["environment"] = dict(ENVIRONMENT)
        receipt["process"]["environment"] = dict(ENVIRONMENT)
        changed = write(self.base / "inspection-git-changed.json", canonical(receipt), 0o644)
        host = deepcopy(self.world.host)
        host["inspections"]["git_version"] = descriptor(changed)
        self.assertIn("environment", self.refused(host).reason)

    def test_inspection_receipt_of_another_design_revision_refuses(self):
        for key, value in (("design_revision", 3), ("amendments", []), ("contract", v01.CONTRACT)):
            receipt = json.loads(self.world.inspections["node_version"].read_bytes()) | {key: value}
            path = write(self.base / ("inspection-" + key + ".json"), canonical(receipt), 0o644)
            host = deepcopy(self.world.host)
            host["inspections"]["node_version"] = descriptor(path)
            with self.subTest(key=key):
                self.assertIn("another contract, design revision", self.refused(host).reason)

    def test_configuration_binds_the_adopted_contract_and_the_amendment_adoption_record_first(self):
        config = self.world.config(self.base)
        cases = {"adoption record digest": ("amendment_adoption", "sha256", "0" * 64, "Locked file identity differs"),
                 "adoption record of another checkout": ("amendment_adoption", "path", str(self.base / "ADOPTION.json"),
                                                         "belongs to another checkout"),
                 "contract digest": ("contract_source", "sha256", "0" * 64, "Locked file identity differs")}
        for name, (part, key, value, reason) in cases.items():
            changed = deepcopy(config)
            changed[part][key] = value
            path = write(self.base / "selection" / (part + "-" + key + ".json"), canonical(changed), 0o600)
            with self.subTest(case=name), patch.object(v02, "_verify_parent", side_effect=no_process_start), \
                    patch.object(v02, "_host_git", side_effect=no_process_start):
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    v02._selection(path, sha(path), ROOT)
                self.assertIn(reason, caught.exception.reason)
        path = write(self.base / "selection" / "bound.json", canonical(config), 0o600)
        with patch.object(v02, "_verify_parent", side_effect=RuntimeError("reached after both bindings")):
            with self.assertRaisesRegex(RuntimeError, "reached after both bindings"):
                v02._selection(path, sha(path), ROOT)

    def test_host_must_have_observed_the_selected_source_observer_and_reader_tree(self):
        config = self.world.config(self.base)
        inventory = {"files": {observation.ENTRY_POINT: v02._plain(self.world.host["observer"])}}
        v02._cross_bindings(config, self.world.host, inventory)
        cases = {"another commit": ("source", "commit", "6" * 40), "another tree": ("source", "tree", "6" * 40),
                 "another source inventory": ("source", "inventory", descriptor(self.world.inventory_path)),
                 "another root": ("source", "root", str(self.base)),
                 "another reader tree": ("dependencies", "root", str(self.base)),
                 "another observer": ("observer", "sha256", "6" * 64)}
        for name, (part, key, value) in cases.items():
            host = deepcopy(self.world.host)
            host[part][key] = value
            with self.subTest(case=name), self.assertRaises(v02.CurrentHostBindingError) as caught:
                v02._cross_bindings(config, host, inventory)
            self.assertEqual(caught.exception.code, "CH-HOST")

    def test_unverified_labels_say_so_and_the_real_boundary_is_real(self):
        with patch.dict(v02._VERIFIED, {"host": None}):
            labels = v02._labels_now()
            self.assertEqual(v02._boundary(), "real")
        self.assertEqual(labels["boundary"], "real")
        self.assertTrue(all(labels[key] == v02.UNVERIFIED_LABEL for key in ("os", "node", "python_inventory_sha256", "git")))
        for target, name in ((supervisor_darwin_v01, "run_process"), (observation, "read_boot_session_uuid"),
                             (observation, "read_os_identity"), (v02, "_selection"), (v02, "host_state"), (os, "uname")):
            with self.subTest(boundary=name), patch.object(target, name):
                self.assertEqual(v02._boundary(), "mocked")


class RuntimeLayoutTests(unittest.TestCase):
    """MC35 on the provider side: the existing runtime directory, through the observer's real layout check."""

    def setUp(self):
        self.base = resolved_temporary(self, "w5-runtime-")
        self.world = World(self.base)

    def snapshot(self):
        rows = {}
        for parent, directories, files in os.walk(self.world.runtime):
            for name in directories + files:
                path = Path(parent) / name
                info = path.lstat()
                rows[str(path.relative_to(self.world.runtime))] = (stat.S_IFMT(info.st_mode), info.st_size,
                                                                   info.st_ino, path.read_bytes() if path.is_file() and not path.is_symlink() else None)
        return rows

    def check(self):
        with patch.object(v02, "NODE_ARCHIVE_SHA256", self.world.archive_sha256):
            v02._check_runtime(self.world.host, self.world.node)

    def test_unchanged_synthetic_tree_passes_layout_and_pin_and_reaches_the_macho_rules(self):
        with self.assertRaises(v02.CurrentHostBindingError) as caught:
            self.check()
        self.assertEqual(caught.exception.code, "CH-RUNTIME")
        self.assertEqual(caught.exception.cause["code"], "CHO-MACHO")

    def test_mc35_partial_changed_extra_linked_or_inaccessible_runtime_refuses_and_is_not_repaired(self):
        runtime = self.world.runtime
        original = runtime / "bin/node"
        def ds_store():
            write(runtime / ".DS_Store", b"\0")
        def extra_file():
            write(runtime / "bin/npm", b"extra")
        def missing():
            (runtime / "NODE-SOURCE.json").unlink()
        def changed():
            original.write_bytes(b"changed synthetic node bytes; never executed\n")
        def linked():
            original.rename(runtime / "node.real")
            os.symlink(runtime / "node.real", original)
        def inaccessible():
            (runtime / "bin").chmod(0)
            self.addCleanup((runtime / "bin").chmod, 0o755)
        for name, mutate, rule in (("a .DS_Store", ds_store, "TREE-DS-STORE"), ("an extra file", extra_file, "RUNTIME-LAYOUT"),
                                   ("partial", missing, "RUNTIME-LAYOUT"), ("changed", changed, "RUNTIME-PIN"),
                                   ("linked", linked, None), ("inaccessible", inaccessible, None)):
            with self.subTest(case=name):
                self.base = resolved_temporary(self, "w5-runtime-case-")
                self.world = World(self.base)
                runtime, original = self.world.runtime, self.world.runtime / "bin/node"
                mutate()
                before = None if name == "inaccessible" else self.snapshot()
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    self.check()
                self.assertEqual(caught.exception.code, "CH-RUNTIME")
                if rule is not None:
                    self.assertEqual(caught.exception.cause["details"]["rule"], rule)
                self.assertNotEqual(caught.exception.cause["code"], "CHO-MACHO")
                if before is not None:
                    self.assertEqual(self.snapshot(), before, "the provider repaired or replaced the runtime directory")


class SourceGitTests(unittest.TestCase):
    """MC19 on the provider side. Starts a /bin/sh stand-in for the bound Git implementation, once per Git read."""

    def setUp(self):
        self.base = resolved_temporary(self, "w5-source-")
        self.repo = self.base / "checkout"
        for tree in v02.SOURCE_TREES:
            write(self.repo / tree / "placeholder.txt", b"synthetic source\n", 0o644)
        for relative in v02.SOURCE_FILES:
            write(self.repo / relative, b"synthetic role " + relative.encode() + b"\n", 0o644)
        for relative in (v02.PROVIDER, v02.PROBE):
            write(self.repo / relative, b"synthetic " + relative.encode() + b"\n", 0o644)
        self.answers = self.base / "answers"
        self.answers.mkdir()
        self.log = self.base / "git.log"
        self.answer(toplevel=str(self.repo), commit="3" * 40, tree="4" * 40, status="", untracked="")
        script = ("#!/bin/sh\nprintf '%s\\n' \"$*\" >> '" + str(self.log) + "'\n"
                  "case \"$*\" in\n"
                  "  *'rev-parse --show-toplevel'*) cat '" + str(self.answers / "toplevel") + "' ;;\n"
                  "  *'rev-parse --verify HEAD^{commit}'*) cat '" + str(self.answers / "commit") + "' ;;\n"
                  "  *'^{tree}'*) cat '" + str(self.answers / "tree") + "' ;;\n"
                  "  *'status --porcelain=v1 --untracked-files=no'*) cat '" + str(self.answers / "status") + "' ;;\n"
                  "  *'ls-files --others --exclude-standard -z'*) cat '" + str(self.answers / "untracked") + "' ;;\n"
                  "  *) exit 1 ;;\nesac\n")
        self.git = write(self.base / "tools/bin/git", script.encode("ascii"), 0o755)
        self.binding = {"path": str(self.git), "sha256": sha(self.git)}
        inventory = v02.source_inventory(self.repo)
        self.inventory = write(self.base / "source-inventory.json", canonical(inventory), 0o644)
        self.source = {"root": str(self.repo), "commit": "3" * 40, "tree": "4" * 40, "inventory": descriptor(self.inventory)}
        isolated = patch.object(check_local, "_GIT_STATE", None)
        isolated.start()
        self.addCleanup(isolated.stop)

    def answer(self, **values):
        for name, value in values.items():
            (self.answers / name).write_bytes(value.encode("ascii") if isinstance(value, str) else value)

    def starts(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def verify(self, git=None, **kwargs):
        return v02._verify_source(self.source, git=self.binding if git is None else git, own_root=False, **kwargs)

    def test_clean_source_binds_git_and_every_read_runs_the_bound_executable(self):
        self.assertEqual(self.verify()["schema"], v02.PREFIX + "source/0.2.0")
        starts = self.starts()
        self.assertEqual(len(starts), 5, starts)
        self.assertTrue(all(row.startswith("-c core.fsmonitor=false -C " + str(self.repo) + " ") for row in starts), starts)
        self.assertEqual(check_local.git_executable(), str(self.git))
        self.assertEqual(sorted(v02._source_paths(self.repo)), sorted(observation.source_paths(str(self.repo))))

    def test_mc19_dirty_or_untracked_source_refuses(self):
        for name, answers, reason in (("dirty tracked file", {"status": " M tests/placeholder.txt\n"}, "Dirty source"),
                                      ("untracked input", {"untracked": b"notes/new.txt\0"}, "Untracked source input")):
            with self.subTest(case=name):
                self.answer(status="", untracked="")
                self.answer(**answers)
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    self.verify()
                self.assertEqual(caught.exception.code, "CH-SOURCE")
                self.assertIn(reason, caught.exception.reason)

    def test_mc19_other_commit_or_checkout_refuses(self):
        self.answer(commit="5" * 40)
        with self.assertRaises(v02.CurrentHostBindingError) as caught:
            self.verify()
        self.assertIn("commit/tree differs", caught.exception.reason)
        self.answer(commit="3" * 40, toplevel=str(self.base))
        with self.assertRaises(v02.CurrentHostBindingError):
            self.verify()
        with self.assertRaises(v02.CurrentHostBindingError) as caught:
            v02._verify_source(self.source, git=self.binding, own_root=True)
        self.assertEqual(caught.exception.reason, "Provider belongs to another source checkout")

    def test_mc19_changed_provider_or_probe_refuses_before_any_git_start(self):
        for relative in (v02.PROVIDER, v02.PROBE):
            with self.subTest(file=relative):
                path = self.repo / relative
                original = path.read_bytes()
                path.write_bytes(original + b"// changed\n")
                self.addCleanup(path.write_bytes, original)
                self.log.unlink(missing_ok=True)
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    self.verify()
                self.assertIn("Locked file identity differs", caught.exception.reason)
                self.assertEqual(self.starts(), [])
                path.write_bytes(original)

    def test_mc19_unbound_or_unbindable_git_refuses_before_any_git_start(self):
        cases = {"no binding": {}, "dispatcher": {"path": check_local.GIT_DISPATCHER, "sha256": self.binding["sha256"]},
                 "digest mismatch": {"path": str(self.git), "sha256": "0" * 64},
                 "relative path": {"path": "git", "sha256": self.binding["sha256"]}}
        for name, git in cases.items():
            with self.subTest(case=name), patch.object(check_local, "_GIT_STATE", None):
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    self.verify(git=git)
                self.assertEqual(caught.exception.code, "CH-SOURCE")
                self.assertEqual(self.starts(), [])
        other = write(self.base / "other/bin/git", b"#!/bin/sh\nexit 3\n", 0o755)
        with patch.object(check_local, "_GIT_STATE", {"path": str(other), "sha256": sha(other), "bound": True,
                                                      "source": "selection"}):
            with self.assertRaises(v02.CurrentHostBindingError) as caught:
                self.verify()
            self.assertIn("cannot be bound", caught.exception.reason)
        self.assertEqual(self.starts(), [])

    def test_mc19_bound_git_changed_after_binding_never_falls_back(self):
        self.verify()
        self.git.write_bytes(self.git.read_bytes() + b"# changed\n")
        self.log.unlink()
        with self.assertRaises(v02.CurrentHostBindingError):
            self.verify(git={"path": str(self.git), "sha256": self.binding["sha256"]})
        self.assertEqual(self.starts(), [])


class DependencyTreeTests(unittest.TestCase):
    """MC18: the 24 reader files; missing, extra, changed, linked or .DS_Store refuses. Synthetic C199/C195 pins."""

    def setUp(self):
        self.base = resolved_temporary(self, "w5-deps-")
        self.source = self.base / "source"
        self.deps = self.base / "deps"
        names = ["validator/package/package.json", "indexer-view/three/package.json"] + \
                ["readers/file-%02d.js" % index for index in range(22)]
        contents = {name: b"// synthetic reader file " + name.encode() + b"\n" for name in names}
        contents["validator/package/package.json"] = b'{"version":"2.0.0-dev.3.10"}'
        contents["indexer-view/three/package.json"] = b'{"version":"0.186.1"}'
        for name, data in contents.items():
            write(self.deps / name, data, 0o644)
        self.files = {name: binding(self.deps / name) for name in names}
        root = "/historical/receiving"
        manifest = {"dependencies_root": root, "files": {root + "/" + name: {"sha256": row["sha256"], "size_bytes": row["size_bytes"]}
                                                         for name, row in self.files.items()}}
        external = write(self.source / v02.EXTERNAL_INPUTS, canonical(manifest), 0o644)
        self.archive = write(self.base / "c195.tar", b"synthetic retained archive", 0o644)
        directories = {}
        for name in names:
            parts = name.split("/")[:-1]
            for index in range(1, len(parts) + 1):
                directories["/".join(parts[:index])] = oct((self.deps / "/".join(parts[:index])).stat().st_mode & 0o7777)
        inventory = {"schema": v02.PREFIX + "dependencies/0.2.0", "files": self.files, "directories": directories,
                     "archive": descriptor(self.archive)}
        self.inventory = write(self.base / "dependencies.json", canonical(inventory), 0o644)
        self.config = {"source": {"root": str(self.source)},
                       "dependencies": {"root": str(self.deps), "inventory": descriptor(self.inventory)}}
        for name, value in (("EXTERNAL_SHA256", sha(external)), ("ARCHIVE_SHA256", sha(self.archive))):
            pin = patch.object(v02, name, value)
            pin.start()
            self.addCleanup(pin.stop)

    def test_exact_tree_is_accepted(self):
        self.assertEqual(sorted(v02._verify_dependencies(self.config)["files"]), sorted(self.files))

    def test_mc18_missing_extra_changed_linked_or_ds_store_refuses(self):
        target = self.deps / "readers/file-03.js"
        original = target.read_bytes()
        def restore():
            for extra in (self.deps / "readers/.DS_Store", self.deps / "readers/extra.js", self.deps / "file-03.real"):
                extra.unlink(missing_ok=True)
            if target.is_symlink():
                target.unlink()
            target.write_bytes(original)
            target.chmod(0o644)
        cases = {"missing": lambda: target.unlink(), "extra": lambda: write(self.deps / "readers/extra.js", b"x"),
                 "changed": lambda: target.write_bytes(original[:-1] + b"!"),
                 "linked": lambda: (write(self.deps / "file-03.real", original), target.unlink(),
                                    os.symlink(self.deps / "file-03.real", target)),
                 ".DS_Store": lambda: write(self.deps / "readers/.DS_Store", b"\0")}
        for name, mutate in cases.items():
            with self.subTest(case=name):
                mutate()
                with self.assertRaises(v02.CurrentHostBindingError) as caught:
                    v02._verify_dependencies(self.config)
                self.assertEqual(caught.exception.code, "CH-DEPENDENCY")
                restore()
        self.test_exact_tree_is_accepted()


class AttemptTests(unittest.TestCase):
    """The process adapter: MC09 and MC29 (simulated), MC31 on the provider side, labels and the facade route."""

    def setUp(self):
        self.base = resolved_temporary(self, "w5-attempt-")
        self.world = World(self.base)
        self.cohort = Cohort(self.world)
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(subprocess, "Popen", side_effect=no_process_start))
        self.stack = stack

    def attempt(self, *, states=None, returncode=0, env=None, facade=False, **selection):
        with self.world.mocked_host(states=states), self.cohort.environment(), \
                self.cohort.selection_boundary(**selection):
            process, calls = delegate(returncode)
            with process:
                try:
                    result, started = self.cohort.run(env=env, facade=facade)
                    return result, started, calls, None
                except (v02.CurrentHostBindingError, Stop) as exc:
                    return None, None, calls, exc

    def test_positive_attempt_records_boot_around_the_start_and_labels(self):
        self.cohort.prepare()
        result, started, calls, error = self.attempt(facade=True)
        self.assertIsNone(error)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(started), 1)
        self.assertEqual(result["returncode"], 0)
        ledger = self.cohort.ledger()
        self.assertEqual(ledger["schema"], v02.PREFIX + "attempt/0.2.0")
        self.assertEqual((ledger["contract"], ledger["design_revision"], ledger["amendments"]),
                         (v02.CONTRACT, 4, ["P33-AMENDMENT-001"]))
        self.assertEqual(ledger["state"], "COMPLETED")
        self.assertEqual(ledger["actual_checker_starts"], 1)
        for key, stage in (("boot_before", "before the start"), ("boot_after", "after the start")):
            self.assertEqual((ledger[key]["stage"], ledger[key]["boot_session_uuid"]), (stage, BOOT))
            self.assertEqual(ledger[key]["os"]["product_build_version"], "25G83")
        labels = ledger["labels"]
        self.assertEqual((labels["executor"], labels["run_kind"], labels["boundary"]), ("macos-arm64-local", "qualifying", "mocked"))
        self.assertEqual(labels["git"]["path"], str(self.world.git))
        self.assertEqual(labels["python_inventory_sha256"], self.world.host["python"]["inventory_sha256"])
        manifest = json.loads(self.cohort.manifest_path.read_bytes())
        self.assertEqual((manifest["schema"], manifest["design_revision"]), (v02.PREFIX + "lock/0.2.0", 4))
        self.assertEqual(manifest["runtime"], {"executable": str(self.world.node), "version": "v24.22.1",
                                               "binding": self.world.host["runtime"]["binding"]})
        self.assertEqual(manifest["labels"], labels)

    def test_genuine_supervisor_stop_is_reraised_unchanged_after_postflight(self):
        self.cohort.case = "Q01-changed-reference"
        self.cohort.stage = self.cohort.cohort / self.cohort.case
        self.cohort.prepare()
        _, _, calls, error = self.attempt(returncode=1)
        self.assertIsInstance(error, Stop)
        self.assertNotIsInstance(error, v02.CurrentHostBindingError)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.cohort.ledger()["state"], "SUPERVISOR_REFUSAL")

    def test_mc09_simulated_boot_change_before_the_start_refuses_with_zero_starts(self):
        self.cohort.prepare()
        _, _, calls, error = self.attempt(states=[self.world.state(boot=OTHER_BOOT)])
        self.assertIsInstance(error, v02.CurrentHostBindingError)
        self.assertIn("before the start", error.reason)
        self.assertEqual(calls, [])
        self.assertEqual(error.refusal_record["actual_checker_starts"], 0)
        self.assertEqual(self.cohort.ledger()["actual_checker_starts"], 0)

    def test_mc09_simulated_boot_os_build_or_cryptex_change_across_the_start_fails_the_attempt(self):
        for change in ({"boot": OTHER_BOOT}, {"build": "25G84"}, {"cryptex_build": "25G84a"}):
            with self.subTest(change=change):
                self.base = resolved_temporary(self, "w5-attempt-case-")
                self.world = World(self.base)
                self.cohort = Cohort(self.world).prepare()
                _, _, calls, error = self.attempt(states=[self.world.state(), self.world.state(**change)])
                self.assertIsInstance(error, v02.CurrentHostBindingError)
                self.assertEqual(error.code, "CH-HOST")
                self.assertIn("after the start", error.reason)
                self.assertEqual(len(calls), 1)
                ledger = self.cohort.ledger()
                self.assertEqual((ledger["actual_checker_starts"], ledger["boot_after"]), (1, None))
                self.assertEqual(ledger["boot_before"]["boot_session_uuid"], BOOT)
                self.assertEqual(ledger["provider_failure"]["code"], "CH-HOST")
                self.assertIsNotNone(ledger["process"])

    def test_mc29_simulated_change_after_preflight_invalidates_the_attempt_with_zero_starts(self):
        def input_change():
            real = v02._write_new
            def write_new(path, value):
                described = real(path, value)
                if Path(path).name == "preflight.json":
                    (self.cohort.stage / "synthetic.glb").write_bytes(b"changed after preflight")
                return described
            return patch.object(v02, "_write_new", side_effect=write_new)
        changed_host = deepcopy(self.world.host)
        changed_host["os"]["system_version"]["product_build_version"] = "25G84"
        cases = {"input bytes": ({}, input_change), "source, runtime, dependency or configuration": ({"failing_call": 2}, None),
                 "OS build in the selection": ({"changed_host": (2, changed_host)}, None),
                 "OS build at the host": ({}, None)}
        for name, (selection, extra) in cases.items():
            with self.subTest(case=name):
                self.base = resolved_temporary(self, "w5-mc29-")
                self.world = World(self.base)
                self.cohort = Cohort(self.world).prepare()
                states = [self.world.state(build="25G84")] if name == "OS build at the host" else None
                with ExitStack() as stack:
                    if extra is not None:
                        stack.enter_context(extra())
                    _, _, calls, error = self.attempt(states=states, **selection)
                self.assertIsInstance(error, v02.CurrentHostBindingError)
                self.assertEqual(calls, [], "a start followed a change after preflight")
                ledger = self.cohort.ledger()
                self.assertEqual(ledger["actual_checker_starts"], 0)
                self.assertIsNotNone(ledger["preflight"])
                self.assertIsNotNone(ledger["provider_failure"])

    def test_mc31_extra_variable_or_cf_in_the_launch_environment_refuses_with_zero_starts(self):
        for name, env in (("extra variable", dict(ENVIRONMENT) | {"EXTRA": "1"}),
                          ("CF with the recorded value", dict(ENVIRONMENT) | {observation.CF_NAME: CF_VALUE}),
                          ("CF with another value", dict(ENVIRONMENT) | {observation.CF_NAME: "0x0:0x0:0x0"}),
                          ("missing variable", {k: v for k, v in ENVIRONMENT.items() if k != "PATH"})):
            with self.subTest(case=name):
                self.base = resolved_temporary(self, "w5-mc31-")
                self.world = World(self.base)
                self.cohort = Cohort(self.world).prepare()
                _, _, calls, error = self.attempt(env=env)
                self.assertIsInstance(error, v02.CurrentHostBindingError)
                self.assertEqual(error.code, "CH-LAUNCH")
                self.assertEqual(calls, [])

    def test_mc21_missing_partial_malformed_or_mismatched_selection_refuses_with_zero_starts(self):
        self.cohort.prepare()
        malformed = write(self.base / "malformed.json", b"{not json", 0o600)
        cases = {"missing file": {v02.CONFIG_ENV: str(self.base / "absent.json"), v02.DIGEST_ENV: self.cohort.digest},
                 "partial": {v02.CONFIG_ENV: str(self.cohort.config_path)},
                 "malformed digest": {v02.CONFIG_ENV: str(self.cohort.config_path), v02.DIGEST_ENV: self.cohort.digest.upper()},
                 "mismatched digest": {v02.CONFIG_ENV: str(self.cohort.config_path), v02.DIGEST_ENV: "0" * 64},
                 "malformed configuration": {v02.CONFIG_ENV: str(malformed), v02.DIGEST_ENV: sha(malformed)}}
        for name, environment in cases.items():
            with self.subTest(case=name), patch.dict(os.environ, environment, clear=True):
                process, calls = delegate()
                with process, self.assertRaises(v02.CurrentHostBindingError) as caught:
                    self.cohort.run()
                self.assertIn(caught.exception.code, ("CH-SELECTION", "CH-SCHEMA", "CH-LAUNCH"))
                self.assertEqual(calls, [])
                self.assertEqual(caught.exception.refusal_record["actual_checker_starts"], 0)
        for name, (path, digest) in {"missing": (self.base / "absent.json", self.cohort.digest),
                                     "mismatched": (self.cohort.config_path, "0" * 64),
                                     "malformed": (malformed, sha(malformed))}.items():
            with self.subTest(case="validate_selection " + name), self.assertRaises(v02.CurrentHostBindingError) as caught:
                v02.validate_selection(path, digest, ROOT)
            self.assertEqual(caught.exception.code, "CH-SELECTION")


class CohortAccountingTests(unittest.TestCase):
    """Setup records and D-08: the cohort accounting fails the run when one of the three CPU methods did not run."""

    def setUp(self):
        self.base = resolved_temporary(self, "w5-cohort-")
        self.world = World(self.base)
        self.cohort = Cohort(self.world)

    def subject(self):
        class Subject:
            pass
        subject = Subject
        subject.root, subject.temporary = self.cohort.cohort, None
        subject.manifest_path = self.cohort.manifest_path
        return subject

    def ledgers(self, cases, **changes):
        for case in cases:
            # An attempt/0.2.0 ledger with this contract's identity, as guarded_run_process writes it (D-20, I-07).
            row = {"schema": v02.PREFIX + "attempt/0.2.0", **v02._identity(),
                   "actual_checker_starts": 1, "provider_failure": None, "preflight": {"x": 1}, "postflight": {"x": 1},
                   "process": {"handles_closed": True, "cleanup": {"passed": True},
                               "returncode": 1 if case == "Q01-changed-reference" else 0}} | changes
            write(self.cohort.cohort / "provider-ledgers" / case / "result.json", canonical(row), 0o600)

    def finish(self):
        with self.cohort.environment(), patch.object(v02, "verify_case_manifest", return_value=({}, "0" * 64)), \
                self.world.mocked_host():
            subject = self.subject()
            try:
                v02.finish_cpu_cohort(subject)
                error = None
            except v02.CurrentHostBindingError as exc:
                error = exc
        return error, json.loads((self.cohort.cohort / "cohort.json").read_bytes())

    def test_d08_complete_cohort_passes(self):
        self.ledgers(v02.CASES)
        error, record = self.finish()
        self.assertIsNone(error)
        self.assertTrue(record["passed"])
        self.assertEqual((record["schema"], record["design_revision"]), (v02.PREFIX + "cohort/0.2.0", 4))
        self.assertIn("labels", record)

    def test_d08_a_cpu_method_that_did_not_run_fails_the_run(self):
        self.ledgers(["Q01-positive", "Q03-positive"])
        error, record = self.finish()
        self.assertIsInstance(error, v02.CurrentHostBindingError)
        self.assertEqual(error.reason, "Completed cohort is missing or has extra checker attempts")
        self.assertFalse(record["passed"])
        self.assertEqual(record["error"]["code"], "CH-EVIDENCE")

    def test_d08_an_attempt_without_its_start_fails_the_run(self):
        self.ledgers(v02.CASES, actual_checker_starts=0)
        error, record = self.finish()
        self.assertIsInstance(error, v02.CurrentHostBindingError)
        self.assertFalse(record["passed"])

    def test_d20_a_ledger_that_is_not_an_attempt_0_2_0_document_fails_the_run(self):
        """Review finding I-07: the accounting requires attempt/0.2.0 with this contract's identity."""
        variants = {"another schema": {"schema": v02.PREFIX + "attempt/0.1.0"},
                    "no schema": {"schema": None},
                    "another contract": {"contract": "ontokin.current-host-readback/0.1.0"},
                    "another design revision": {"design_revision": 3},
                    "no amendment": {"amendments": []}}
        for number, (label, change) in enumerate(variants.items()):
            with self.subTest(label):
                self.world = World(self.base / ("variant-%d" % number))
                self.cohort = Cohort(self.world)
                self.ledgers(v02.CASES, **change)
                error, record = self.finish()
                self.assertIsInstance(error, v02.CurrentHostBindingError)
                self.assertEqual(error.reason, "A checker attempt ledger is not an attempt/0.2.0 document of this contract")
                self.assertFalse(record["passed"])
                self.assertEqual(record["error"]["code"], "CH-EVIDENCE")

    def test_setup_records_the_boot_before_the_cohort_labels_and_run_kind(self):
        with self.world.mocked_host(), self.cohort.environment(), self.cohort.selection_boundary(), \
                patch.dict(os.environ, {"STATIC_TRAY_READBACK_CPU_OUTPUT": str(self.cohort.evidence / "cohort-setup")}):
            subject = type("Subject", (), {})
            v02.setup_cpu_cohort(subject)
        record = json.loads((subject.root / "setup.json").read_bytes())
        self.assertTrue(record["passed"])
        self.assertEqual((record["schema"], record["run_kind"], record["design_revision"]), (v02.PREFIX + "setup/0.2.0", "qualifying", 4))
        self.assertEqual((record["boot"]["stage"], record["boot"]["boot_session_uuid"]), ("before the cohort", BOOT))
        self.assertEqual(record["labels"]["git"]["path"], str(self.world.git))

    def test_setup_refuses_a_boot_change_before_the_cohort(self):
        with self.world.mocked_host(states=[self.world.state(boot=OTHER_BOOT)]), self.cohort.environment(), \
                self.cohort.selection_boundary(), \
                patch.dict(os.environ, {"STATIC_TRAY_READBACK_CPU_OUTPUT": str(self.cohort.evidence / "cohort-setup")}):
            subject = type("Subject", (), {})
            with self.assertRaises(v02.CurrentHostBindingError) as caught:
                v02.setup_cpu_cohort(subject)
        self.assertIn("before the cohort", caught.exception.reason)
        record = json.loads((subject.root / "setup.json").read_bytes())
        self.assertFalse(record["passed"])
        self.assertEqual(caught.exception.refusal_record["schema"], v02.PREFIX + "refusal/0.2.0")
        self.assertEqual(caught.exception.refusal_record["labels"]["executor"], "macos-arm64-local")


SCAN_PATTERNS = {
    "child_process": r"child_process", "cluster": r"cluster", "worker_threads": r"worker_threads",
    "process.dlopen": r"dlopen", "require call": r"\brequire\s*\(", "createRequire": r"createRequire",
    "import() call": r"\bimport\s*\(", "eval": r"\beval\b", "Function": r"Function",
    "process.binding": r"process\s*\.\s*(?:binding|_linkedBinding)", "Worker": r"\bWorker\b",
    "spawn/fork/exec": r"\b(?:spawn|fork|execFile|exec)\w*\s*\(",
    "static import": r"^\s*import\s.*\bfrom\s+'([^']+)'|^\s*import\s+'([^']+)'"}


def probe_scan(text):
    """MC11 for the probe, development run: every line that names a process-creation route or a dynamic load."""
    hits = []
    for number, line in enumerate(text.splitlines(), 1):
        for name, pattern in SCAN_PATTERNS.items():
            if re.search(pattern, line):
                hits.append({"line": number, "pattern": name, "text": line.strip()})
    return hits


class ProbeSegmentTests(unittest.TestCase):
    """The 0.2.0 probe's preserved segments are byte-identical to the 0.1.0 probe's (P05 section 6)."""

    @classmethod
    def setUpClass(cls):
        cls.map = json.loads(PROBE_MAP.read_bytes())
        cls.v01 = PROBE_V01.read_bytes().splitlines(keepends=True)
        cls.v02 = PROBE_V02.read_bytes().splitlines(keepends=True)

    def text(self, lines, first, last):
        return b"".join(lines[first - 1:last])

    def test_map_binds_both_probe_files(self):
        self.assertEqual(self.map["files"]["v01"]["sha256"], sha(PROBE_V01))
        self.assertEqual(self.map["files"]["v02"]["sha256"], sha(PROBE_V02))
        self.assertEqual((self.map["files"]["v01"]["lines"], self.map["files"]["v02"]["lines"]), (len(self.v01), len(self.v02)))

    def test_every_preserved_segment_is_byte_identical_in_both_files(self):
        for row in self.map["preserved"]:
            with self.subTest(segment=row["id"]):
                old, new = self.text(self.v01, *row["v01"]), self.text(self.v02, *row["v02"])
                self.assertEqual(old, new)
                self.assertEqual(hashlib.sha256(old).hexdigest(), row["v01_sha256"])
                self.assertEqual(hashlib.sha256(new).hexdigest(), row["v02_sha256"])

    def test_segments_partition_both_files_and_cover_the_scientific_body(self):
        for side, lines in (("v01", self.v01), ("v02", self.v02)):
            covered = []
            for row in self.map["preserved"] + self.map["adapted"]:
                first, last = row[side]
                covered.extend(range(first, last + 1))
            self.assertEqual(sorted(covered), list(range(1, len(lines) + 1)), side)
        preserved = {number for row in self.map["preserved"] for number in range(row["v01"][0], row["v01"][1] + 1)}
        for first, last in SCIENTIFIC_V01_LINES:
            self.assertTrue(set(range(first, last + 1)) <= preserved, (first, last))
        self.assertEqual([tuple(row) for row in self.map["scientific_body_v01_lines"]], SCIENTIFIC_V01_LINES)
        for row in self.map["adapted"]:
            self.assertTrue(row["reason"].strip(), row["id"])

    def test_mc11_development_scan_matches_its_reviewed_hits(self):
        hits = probe_scan(PROBE_V02.read_text("ascii"))
        reviewed = [{key: row[key] for key in ("line", "pattern", "text")} for row in self.map["mc11_scan"]["hits"]]
        self.assertEqual(hits, reviewed)
        self.assertTrue(all(row["review"].strip() for row in self.map["mc11_scan"]["hits"]))
        names = {row["pattern"] for row in hits}
        for forbidden in ("child_process", "cluster", "worker_threads", "process.dlopen", "eval", "Worker"):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
