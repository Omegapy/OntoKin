"""Focused tests of control_harness.py.

* The command boundary's receipts are checked against the observer's own receipt and output rules.
* mc10 runs in a child exactly as M0 is launched (the declared environment, -I -S -B). Its synthetic
  plans are refused by the real static checks, at the plan digest or at the source binding. One plan
  binds this checkout's real source and Python installation, so that the real checks reach the
  observer's loaded-module rule (PYTHON-MODULE): once with the harness's exclusion of its own
  __main__ row, and once with a copy of the harness without it (TR-13).
* mc29 runs in this process with the provider's host, source, dependency and method verifications
  substituted by this test (as MI's frozen MC29 cases substitute them), because the real ones need
  MH's frozen inputs; the harness then reports, correctly, that those detectors were not the
  provider's own. The process environment is exactly the frozen one given to it (TR-06).
* host-state runs in a child against HOST documents built from this host's own readings.

Children: the interpreter with -B (and -I -S for mc10). Nothing starts Node, Git or any other process.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import stat
import sys
import unittest
from unittest import mock

import mh_support as S

MC10_FILES = ("prototypes/__init__.py", "prototypes/static_tray_v01/__init__.py",
              "prototypes/static_tray_v01/supervisor.py", "prototypes/static_tray_v01/current_host_observation_v02.py")
CONFIG_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG"
DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
ROOT = S.project_root()
HARNESS = S.load_module("mh_control_harness", str(S.TOOLING / "control_harness.py"))
OBSERVER = S.load_module("mh_observer", ROOT + "/prototypes/static_tray_v01/current_host_observation_v02.py")
EXCLUSION = 'if row["name"] == "__main__" and os.path.realpath(row["file"]) == own:'


def load_supervisor():
    """The real supervisor.py, loaded by path (it imports only the standard library)."""
    return S.load_module("mh_supervisor", ROOT + "/prototypes/static_tray_v01/supervisor.py")


@contextlib.contextmanager
def no_process_start():
    with mock.patch("subprocess.Popen", side_effect=AssertionError("a process start")), \
            mock.patch("os.posix_spawn", side_effect=AssertionError("a process start")):
        yield


class CommandBoundaryTests(unittest.TestCase):
    def test_the_simulated_receipt_meets_the_observers_own_rules_and_starts_nothing(self):
        base = load_supervisor()
        stage = S.resolved_temp(self) + "/node_version"
        os.mkdir(stage)
        label = OBSERVER.LABELS["node_version"]
        command = {"id": "node_version", "argv": ["/synthetic/bin/node", "--version"], "cwd": stage, "label": label,
                   "environment": dict(OBSERVER.ENVIRONMENT)}
        for stdout, accepted in ((b"v24.22.1\n", True), (b"v24.22.0\n", False)):
            with self.subTest(stdout=stdout):
                for name in os.listdir(stage):
                    os.remove(stage + "/" + name)
                boundary = HARNESS.CommandBoundary(base, {label: stdout})
                started = []
                with mock.patch("subprocess.Popen", side_effect=AssertionError("a process start")):
                    record = boundary.run_process(list(command["argv"]), stage=stage, label=label,
                                                  clock=base.Clock(total_ms=5000), stage_end=None,
                                                  env=dict(command["environment"]), on_started=started.append)
                self.assertEqual(len(started), 1)
                self.assertGreater(record["pid"], 99999, "the mock receipt names no possible process")
                logs = {key: Path(stage + "/" + label + "." + key + ".log").read_bytes() for key in ("stdout", "stderr")}
                OBSERVER._process_success(record, command, logs["stdout"], logs["stderr"])
                self.assertEqual(Path(stage + "/" + label + ".process.json").read_bytes(), base.json_bytes(record))
                if accepted:
                    OBSERVER._predicate(command, logs["stdout"], logs["stderr"])
                else:
                    with self.assertRaises(OBSERVER.ObservationError) as caught:
                        OBSERVER._predicate(command, logs["stdout"], logs["stderr"])
                    self.assertEqual(caught.exception.category, "OUTPUT")

    def test_job_bytes_are_the_supervisors_json_bytes_and_the_recorder_starts_nothing(self):
        base = load_supervisor()
        value = {"b": [1, 2.5, "x"], "a": {"z": None, "y": True}}
        self.assertEqual(HARNESS.canonical_job_bytes(value), base.json_bytes(value))
        recorder = HARNESS.SupervisorRecorder()
        with self.assertRaises(RuntimeError):
            recorder(["/synthetic/node"], stage="/synthetic", label="x")
        self.assertEqual(len(recorder.calls), 1)


def mc10_plan(test, *, real_static=False):
    """A shape-valid observation plan with this host's real platform and OS identity and a synthetic world.

    With real_static, the plan binds this checkout's real source (its inventory, HEAD and observer) and its
    real Python installation (venv, framework and inventory), so that M0's static checks pass them and
    refuse at the synthetic runtime after the loaded-module rule.
    """
    top = S.resolved_temp(test)
    root = top + "/source"
    os.makedirs(root + "/.venv")
    observer = S.write(root + "/" + OBSERVER.ENTRY_POINT, b"# synthetic stand-in at the observer path\n")
    inputs = {name: S.write(top + "/inputs/" + name, ("synthetic " + name + "\n").encode())
              for name in ("python-inventory.json", "node-source.json", "runtime-plan.json", "runtime-result.json",
                           "dependencies-plan.json", "dependencies-result.json", "dependencies-inventory.json",
                           "failure-capture.md", OBSERVER.NODE_ARCHIVE)}
    source_inventory = S.write(top + "/inputs/source-inventory.json",
                               S.canonical({"schema": OBSERVER.SOURCE_SCHEMA, "files": {}}))
    node = S.write(top + "/runtime/bin/node", b"synthetic node executable; never executed\n", 0o755)
    os.makedirs(top + "/dependencies")
    git = S.write(top + "/git/bin/git", b"#!/bin/sh\n# synthetic Git; never executed\nexit 1\n", 0o755)
    evidence = top + "/evidence"
    os.makedirs(evidence)
    rows, current = [], evidence
    while True:
        info = os.lstat(current)
        rows.append({"path": current, "device": info.st_dev, "inode": info.st_ino,
                     "mode": "0o%03o" % stat.S_IMODE(info.st_mode)})
        if current == "/":
            break
        current = os.path.dirname(current)
    identity = OBSERVER.read_os_identity()
    cryptex = identity["cryptex"]
    cryptex_plan = ({key: cryptex[key] for key in ("state", "path", "sha256", "size_bytes", "mode")}
                    if cryptex["state"] == "present" else {"state": "absent", "path": cryptex["path"]})
    framework = os.path.realpath(sys.base_prefix)
    commit = hashlib.sha1(b"synthetic commit").hexdigest()
    venv = root + "/.venv"
    python_inventory = inputs["python-inventory.json"]
    if real_static:
        root, venv = ROOT, ROOT + "/.venv"
        observer = ROOT + "/" + OBSERVER.ENTRY_POINT
        source_inventory = S.write(top + "/inputs/real-source-inventory.json",
                                   OBSERVER._canonical(OBSERVER.source_inventory(ROOT)))
        commit = OBSERVER.git_head(ROOT)["commit"]
        python_inventory = S.write(top + "/inputs/real-python-inventory.json",
                                   OBSERVER._canonical(OBSERVER.python_inventory(venv, framework)))
    attempt = evidence + "/attempt"
    plan = {"schema": OBSERVER.PLAN_SCHEMA, "contract": OBSERVER.CONTRACT, "profile": OBSERVER.PROFILE,
            "executor": OBSERVER.EXECUTOR, "environment": dict(OBSERVER.ENVIRONMENT),
            "platform": {"system": "Darwin", "release": os.uname().release, "machine": "arm64", "proc_translated": 0,
                         "boot_session_uuid": OBSERVER.read_boot_session_uuid()},
            "os": {"system_version": {key: identity["system_version"][key]
                                      for key in ("path", "sha256", "size_bytes", "mode")}, "cryptex": cryptex_plan},
            "source": {"root": root, "commit": commit,
                       "tree": hashlib.sha1(b"synthetic tree").hexdigest(), "inventory": S.descriptor(source_inventory)},
            "observer": S.descriptor(observer),
            "python": {"venv": venv, "framework": framework, "version": platform.python_version(),
                       "inventory": S.descriptor(python_inventory)},
            "runtime": {"directory": top + "/runtime", "version": "v24.22.1", "root_mode": "0o755", "bin_mode": "0o755",
                        "executable": S.binding(node), "node_source": S.binding(inputs["node-source.json"]),
                        "archive": dict(S.descriptor(inputs[OBSERVER.NODE_ARCHIVE]),
                                        sha256=OBSERVER.NODE_ARCHIVE_SHA256),
                        "install": {"plan": S.descriptor(inputs["runtime-plan.json"]),
                                    "result": S.descriptor(inputs["runtime-result.json"])}},
            "dependencies": {"root": top + "/dependencies", "inventory": S.descriptor(inputs["dependencies-inventory.json"]),
                             "install": {"plan": S.descriptor(inputs["dependencies-plan.json"]),
                                         "result": S.descriptor(inputs["dependencies-result.json"])}},
            "git": S.descriptor(git),
            "evidence": {"parent": evidence, "ancestors": sorted(rows, key=lambda row: row["path"]), "attempt": attempt,
                         "outputs": OBSERVER.output_paths(attempt)},
            "failure_capture": {"procedure": S.descriptor(inputs["failure-capture.md"])},
            "limits": dict(OBSERVER.LIMITS)}
    plan["commands"] = OBSERVER.expected_commands(plan)
    path = S.write(top + "/plan.json", S.canonical(plan))
    return top, path, attempt


class MC10Tests(unittest.TestCase):
    def run_mc10(self, top, plan, digest, *, bindings=None, flags=("-I", "-S", "-B"), env=None, tool_path=None):
        output = top + "/mc10-%d.json" % len(os.listdir(top))
        bound = bindings or {rel: S.sha256_file(ROOT + "/" + rel) for rel in MC10_FILES}
        args = ["mc10", "--root", ROOT, "--plan", plan, "--plan-sha256", digest]
        for rel, value in bound.items():
            args += ["--bind", rel + "=" + value]
        args += ["--git-stdout-hex", b"git version 2.0.0 (synthetic)\n".hex(), "--node-stdout-hex", b"v24.22.0\n".hex(),
                 "--expect", "refused-output", "--output", output]
        completed = S.run_tool("control_harness.py", *args, flags=flags, env=dict(S.DECLARED) if env is None else env,
                               tool_path=tool_path)
        return completed, S.read_json(output)

    def test_the_real_static_checks_run_with_only_the_command_boundary_substituted(self):
        top, plan, attempt = mc10_plan(self)
        completed, record = self.run_mc10(top, plan, S.sha256_file(plan))
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        self.assertEqual(record["state"], "NOT_EXPECTED")
        self.assertEqual(record["observation_error"]["category"], "SOURCE",
                         "the plan's platform, boot and OS identity passed the real checks; the synthetic source refused")
        self.assertEqual(record["process_events"], [])
        self.assertEqual(record["boundary_calls"], [])
        self.assertFalse(os.path.exists(attempt))
        self.assertTrue(all(row["compiled_from_verified_bytes"] for row in record["loaded_project_files"]))
        self.assertIn("the M0/M1 command boundary (Host.supervisor returns CommandBoundary; no start)",
                      record["substituted"])

    def test_a_plan_digest_from_outside_the_plan_is_required(self):
        top, plan, _ = mc10_plan(self)
        completed, record = self.run_mc10(top, plan, "0" * 63 + "1")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(record["observation_error"]["code"], "CHO-PLAN")
        self.assertEqual(record["process_events"], [])

    def test_launch_bindings_and_environment_are_preconditions(self):
        top, plan, _ = mc10_plan(self)
        wrong = {rel: S.sha256_file(ROOT + "/" + rel) for rel in MC10_FILES}
        wrong["prototypes/static_tray_v01/supervisor.py"] = "0" * 63 + "1"
        for name, kwargs, rule in (("binding", {"bindings": wrong}, "BINDING"),
                                   ("launcher", {"flags": ("-B",)}, "PYTHON"),
                                   ("environment", {"env": dict(S.DECLARED, EXTRA="1")}, "ENVIRONMENT")):
            with self.subTest(name):
                completed, record = self.run_mc10(top, plan, S.sha256_file(plan), **kwargs)
                self.assertEqual(completed.returncode, 2, completed.stderr.decode()[-2000:])
                self.assertEqual((record["state"], record["refusal"]["rule"]), ("REFUSED", rule))

    def test_the_loaded_module_rule_is_reached_with_and_without_the_exclusion(self):
        """TR-13: without the exclusion of its own __main__ row the harness meets PYTHON-MODULE; with it, the
        real checks pass that rule and refuse later, at the synthetic runtime."""
        top, plan, attempt = mc10_plan(self, real_static=True)
        completed, record = self.run_mc10(top, plan, S.sha256_file(plan))
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        error = record["observation_error"]
        self.assertEqual(error["category"], "RUNTIME", error)
        self.assertEqual([row["name"] for row in record["excluded_loaded_module_rows"]], ["__main__"])
        self.assertEqual(os.path.realpath(record["excluded_loaded_module_rows"][0]["file"]),
                         str((S.TOOLING / "control_harness.py").resolve()))
        self.assertEqual(record["process_events"], [])
        self.assertFalse(os.path.exists(attempt))
        text = (S.TOOLING / "control_harness.py").read_text(encoding="utf-8")
        self.assertEqual(text.count(EXCLUSION), 1)
        without = S.write(top + "/without-exclusion/control_harness.py", text.replace(EXCLUSION, "if False:"))
        completed, record = self.run_mc10(top, plan, S.sha256_file(plan), tool_path=without)
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        error = record["observation_error"]
        self.assertEqual((error["category"], error["as_dict"]["details"]["rule"]), ("PYTHON", "PYTHON-MODULE"))
        self.assertIn(without, error["reason"])
        self.assertEqual(record["excluded_loaded_module_rows"], [])

    def test_the_attempt_listing_never_follows_a_link(self):
        """TR-13: the listing opens files with O_NOFOLLOW and records a link as a link."""
        top = S.resolved_temp(self)
        outside = S.write(top + "/outside.txt", b"never read through the link")
        attempt = top + "/attempt"
        S.write(attempt + "/result.json", b"{}")
        os.symlink(outside, attempt + "/HOST.json")
        listing = HARNESS.attempt_listing(attempt)
        self.assertEqual(listing["HOST.json"], {"kind": "symlink", "target": outside})
        self.assertEqual(listing["result.json"]["sha256"], S.sha256_bytes(b"{}"))
        self.assertEqual(listing["result.json"]["kind"], "file")


class MC29Tests(unittest.TestCase):
    """The harness's MC29 flow in this process, with the provider's verifications substituted by this test."""

    PATCHED = ("_host_git", "_verify_source", "_verify_host", "_cross_bindings", "_verify_dependencies",
               "_verify_methods", "host_state")

    def setUp(self):
        self.saved_path, self.saved_cwd = list(sys.path), os.getcwd()
        self.addCleanup(os.chdir, self.saved_cwd)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), self.saved_path))

    def world(self):
        top = S.resolved_temp(self)
        image = S.process_image()
        launcher = S.PYTHON
        plist = {"state": "present", "sha256": S.sha256_bytes(b"synthetic plist"), "size_bytes": 512, "mode": "0o644",
                 "product_name": "macOS", "product_version": "26.6.2", "product_build_version": "25G83",
                 "product_version_extra": None}
        os_identity = {"system_version": dict(plist, path="/System/Library/CoreServices/SystemVersion.plist"),
                       "cryptex": dict(plist, path="/synthetic/cryptex/SystemVersion.plist",
                                       link_path="/synthetic/cryptex-name/SystemVersion.plist", hops=[])}
        label = {"product_version": "26.6.2", "product_build_version": "25G83", "product_version_extra": None}
        executable = {"sha256": S.sha256_bytes(b"synthetic node"), "size_bytes": 4096, "mode": "0o755"}
        host = {"schema": "ontokin.current-host-readback-host/0.2.0",
                "platform": {"system": "Darwin", "release": "25.6.0", "version": "synthetic kernel", "machine": "arm64",
                             "proc_translated": 0, "boot_session_uuid": "8C1B2C3D-4E5F-4A6B-8C7D-9E0F1A2B3C4D"},
                "os": os_identity, "runtime": {"binding": executable},
                "labels": {"os": dict(label, cryptex=dict(label, state="present")),
                           "node": {"archive": "node-v24.22.1-darwin-arm64.tar.gz", "archive_sha256": "8" * 63 + "9",
                                    "executable": executable, "signature_check": "not_performed"}},
                "python": {"launcher": launcher, "venv": os.path.dirname(os.path.dirname(launcher)),
                           "inventory_sha256": S.sha256_bytes(b"synthetic inventory"),
                           "interpreter": {"implementation": sys.implementation.name,
                                           "version": platform.python_version(), "build_string": sys.version,
                                           "process_image": image}},
                "git": {"path": "/synthetic/git/bin/git", "sha256": S.sha256_bytes(b"synthetic git")}}
        host_path = S.write(top + "/selection/HOST.json", json.dumps(host).encode())
        frozen = S.write(top + "/selection/frozen.json", b"{}\n")
        evidence = top + "/evidence"
        os.makedirs(evidence)
        config = {"schema": "ontokin.current-host-readback-config/0.2.0", "contract": "ontokin.current-host-readback/0.2.0",
                  "contract_source": S.descriptor(ROOT + "/docs/engineering/localized-repair-c271/"
                                                  "macos-contract-design-p31/CONTRACT.md"),
                  "amendment_adoption": S.descriptor(ROOT + "/docs/engineering/localized-repair-c271/"
                                                     "macos-implementation-p33/ADOPTION-AMENDMENT-001.json"),
                  "source": {"root": ROOT, "commit": hashlib.sha1(b"c").hexdigest(), "tree": hashlib.sha1(b"t").hexdigest(),
                             "inventory": S.descriptor(frozen)},
                  "host": S.descriptor(host_path), "dependencies": {"root": top + "/readers", "inventory": S.descriptor(frozen)},
                  "runtime": {"executable": top + "/runtime/bin/node", "version": "v24.22.1"},
                  "methods": S.descriptor(frozen), "evidence_root": evidence, "parent": None}
        config_path = S.write(top + "/selection/config.json", S.canonical(config), 0o600)
        glb = S.write(top + "/fixtures/synthetic.glb", b"glTF synthetic control bytes")
        audit = S.write(top + "/fixtures/synthetic-audit.json", b'{"passed":true}')
        return top, host, config_path, glb, audit

    @contextlib.contextmanager
    def substituted_verifications(self, host):
        import prototypes.static_tray_v01.current_host_readback_v02 as provider  # noqa: E402 (the root is on sys.path)

        def verify_host(config, **_):
            provider._VERIFIED["host"] = copy.deepcopy(host)
            return copy.deepcopy(host)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.dict(provider._VERIFIED, {"host": None}))
            stack.enter_context(mock.patch.object(provider, "_host_git", side_effect=lambda config, **_: dict(host["git"])))
            stack.enter_context(mock.patch.object(provider, "_verify_source",
                                                  side_effect=lambda source, **_: {"schema": "x", "files": {}}))
            stack.enter_context(mock.patch.object(provider, "_verify_host", side_effect=verify_host))
            stack.enter_context(mock.patch.object(provider, "_cross_bindings", return_value=None))
            stack.enter_context(mock.patch.object(provider, "_verify_dependencies", side_effect=lambda config, **_: {
                "files": {"tools/three_loader.mjs": {"sha256": S.sha256_bytes(b"l"), "size_bytes": 1, "mode": "0o644"}}}))
            stack.enter_context(mock.patch.object(provider, "_verify_methods", return_value={}))
            stack.enter_context(mock.patch.object(provider, "host_state", side_effect=lambda **_: {
                "platform": copy.deepcopy(host["platform"]), "os": copy.deepcopy(host["os"])}))
            yield

    def arguments(self, top, config, glb, audit, change, code, frozen):
        environment, digest = S.frozen_environment(top + "/environment-%d.json" % len(os.listdir(top)), frozen)
        return argparse.Namespace(root=ROOT, config=config, config_sha256=S.sha256_file(config), glb=glb,
                                  glb_sha256=S.sha256_file(glb), audit=audit, audit_sha256=S.sha256_file(audit),
                                  change=change, expect_code=code, environment=environment,
                                  environment_sha256=digest)

    def selection(self, config):
        return S.child_environment(**{CONFIG_ENV: config, DIGEST_ENV: S.sha256_file(config)})

    def run_mc29(self, change, code):
        top, host, config, glb, audit = self.world()
        frozen = self.selection(config)
        args = self.arguments(top, config, glb, audit, change, code, frozen)
        sys.path.insert(0, ROOT)
        record = {}
        with mock.patch.dict(os.environ, frozen, clear=True), self.substituted_verifications(host):
            checks = HARNESS.mc29(args, record)
        self.assertEqual(record["environment"]["names"], sorted(frozen), "the frozen environment, by its names")
        self.assertIsNone(record["environment"]["admitted_cf_user_text_encoding"])
        return checks, record

    def assert_refused_with_zero_starts(self, checks, record):
        failed = sorted(name for name, value in checks.items() if not value)
        self.assertEqual(failed, ["detectors_are_the_providers_own"], record.get("attempt_error"))
        self.assertEqual(sorted(name for name, own in record["detectors_are_the_providers_own"].items() if not own),
                         sorted(self.PATCHED))
        self.assertEqual(record["supervisor_calls"], [])
        self.assertEqual(record["process_events"], [])
        self.assertEqual(record["ledger"]["actual_checker_starts"], 0)
        self.assertEqual(record["boundary_during"], "mocked")

    def test_a_configuration_change_after_preflight_is_refused_with_zero_starts(self):
        checks, record = self.run_mc29("configuration", "CH-SELECTION")
        self.assert_refused_with_zero_starts(checks, record)
        self.assertEqual(record["finish_error"]["code"], "CH-SELECTION")

    def test_a_job_input_change_after_preflight_is_refused_with_zero_starts(self):
        checks, record = self.run_mc29("job-input", "CH-JOB")
        self.assert_refused_with_zero_starts(checks, record)
        self.assertEqual(record["finish_error"]["code"], "CH-EVIDENCE")

    def test_the_process_environment_must_be_exactly_the_frozen_one(self):
        """TR-06: an exact frozen environment, without HOME; refused before the provider is imported."""
        top, host, config, glb, audit = self.world()
        frozen = self.selection(config)
        cases = {"an extra name": (dict(frozen, MH_EXTRA="x"), frozen, "ENVIRONMENT"),
                 "HOME in the frozen environment": (dict(frozen, HOME=top), dict(frozen, HOME=top), "ENVIRONMENT"),
                 "another selection": (dict(frozen, **{DIGEST_ENV: "0" * 64}), dict(frozen, **{DIGEST_ENV: "0" * 64}),
                                       "SELECTION")}
        for name, (actual, written, rule) in cases.items():
            with self.subTest(name):
                args = self.arguments(top, config, glb, audit, "configuration", None, written)
                with mock.patch.dict(os.environ, actual, clear=True), no_process_start():
                    with self.assertRaises(HARNESS.Refusal) as caught:
                        HARNESS.mc29(args, {})
                self.assertEqual(caught.exception.rule, rule)


class HostStateTests(unittest.TestCase):
    def host(self, top, boot=None):
        state = {"platform": {"system": os.uname().sysname, "release": os.uname().release, "version": os.uname().version,
                              "machine": os.uname().machine, "proc_translated": OBSERVER.read_proc_translated(),
                              "boot_session_uuid": boot or OBSERVER.read_boot_session_uuid()},
                 "os": OBSERVER.read_os_identity()}
        return S.write(top + "/HOST-%d.json" % len(os.listdir(top)),
                       json.dumps({"schema": "ontokin.current-host-readback-host/0.2.0", **state}).encode())

    def run_host_state(self, top, host):
        output = top + "/host-state-%d.json" % len(os.listdir(top))
        completed = S.run_tool("control_harness.py", "host-state", "--root", ROOT, "--host", host,
                               "--host-sha256", S.sha256_file(host), "--output", output)
        return completed, S.read_json(output)

    def test_the_providers_real_host_state_equals_a_host_of_this_boot(self):
        top = S.resolved_temp(self)
        completed, record = self.run_host_state(top, self.host(top))
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-3000:])
        self.assertEqual(record["checks"], {"boundary_real": True, "state_equals_host": True, "zero_process_starts": True})
        self.assertEqual(record["substituted"], [])

    def test_another_boot_identity_is_refused_by_the_providers_own_comparison(self):
        top = S.resolved_temp(self)
        completed, record = self.run_host_state(top, self.host(top, boot="00000000-0000-4000-8000-000000000001"))
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(record["checks"]["state_equals_host"])
        self.assertEqual(record["refusal"]["code"], "CH-HOST")


class CommonTests(unittest.TestCase):
    def test_every_command_refuses_a_start_without_dash_b(self):
        """TR-17, in this process with sys.flags as a start without -B shows them; nothing is started."""
        top = S.resolved_temp(self)
        host = S.write(top + "/HOST.json", b"{}")
        output = top + "/host-state-without-b.json"
        with mock.patch.object(sys, "flags", S.FlagsWithoutB()), contextlib.redirect_stderr(io.StringIO()), \
                no_process_start():
            code = HARNESS.main(["host-state", "--root", ROOT, "--host", host, "--host-sha256", S.sha256_file(host),
                                 "--output", output])
        self.assertEqual(code, 2)
        self.assertEqual(S.read_json(output)["refusal"]["rule"], "PYTHON")

    def test_a_childs_environment_is_recorded_by_names_and_a_digest(self):
        """TR-06: the audit hook writes no value of a child's environment."""
        row = HARNESS.describe_process_event("subprocess.Popen", ("/usr/bin/true", ["/usr/bin/true"], None,
                                                                  {"MH_VALUE_NAME": "value-never-written"}))
        self.assertEqual(row["environment"]["names"], ["MH_VALUE_NAME"])
        self.assertFalse("value-never-written" in json.dumps(row), "a value was written")


if __name__ == "__main__":
    unittest.main()
