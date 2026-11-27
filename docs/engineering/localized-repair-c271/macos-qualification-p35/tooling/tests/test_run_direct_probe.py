"""Focused tests of run_direct_probe.py. It loads the project's real Darwin supervisor from its verified
bytes. The stand-in "Node" executables are /usr/bin/true, /bin/sh, and scripts that this interpreter
runs with -B; some of those fork once. Children: the interpreter with -I -S -B, which starts the
stand-ins through the supervisor.

Against an earlier runner (rows schema /1), the rows are written in that schema, so that each test of
a fix fails on what the fix changes, not on the schema."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import time
import unittest

import mh_support as S

SUPERVISOR_FILES = ("prototypes/__init__.py", "prototypes/static_tray_v01/__init__.py",
                    "prototypes/static_tray_v01/supervisor.py", "prototypes/static_tray_v01/supervisor_darwin_v01.py")
NODE_FLAGS = ["--no-addons", "--max-old-space-size=256"]
OLD_EXPECTED = ("returncode", "stdout_includes", "stderr_includes", "absent_paths", "present_paths", "file_includes")
STAND_IN = "stand-in python -B via the supervisor"

DESCENDANT = """import os, time
if os.fork() == 0:
    null = os.open("/dev/null", os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(null, fd)
    time.sleep(3)
    os._exit(0)
os._exit(0)
"""
STAGED_LINK = """import os
os.symlink("probe.json", "staged-link")
os._exit(0)
"""
SLEEPER = """import time
time.sleep(20)
"""
REFUSING_PROBE = """import json, os
document = {"passed": False, "error": {"message": "synthetic refusal"}}
if os.path.basename(os.getcwd()) == "with-khronos":
    document["khronos"] = {"passed": False}
with open("probe.json", "x") as stream:
    json.dump(document, stream)
os._exit(1)
"""


def changes_other_rows(job, stage):
    return """import os, sys
if "--check" in sys.argv:
    with open(%r, "ab") as stream:
        stream.write(b" ")
    open(%r, "x").close()
os._exit(0)
""" % (job, stage + "/late.txt")


class RunnerWorld:
    def __init__(self, test, node=None, *, root=None, stand_in=None):
        self.test, self.base = test, S.resolved_temp(test)
        self.root = root or S.project_root()
        self.node = node or S.stand_in(self.base + "/inputs/node-stand-in", stand_in)
        self.stand_in = stand_in is not None
        self.probe = S.write(self.base + "/inputs/probe.mjs", b"// synthetic probe; the stand-ins never read it\n")
        self.loader = S.write(self.base + "/inputs/three_loader.mjs", b"// synthetic module loader\n")
        self.bindings = {rel: S.sha256_file(self.root + "/" + rel) for rel in SUPERVISOR_FILES}
        self.legacy = S.legacy("run_direct_probe.py", 'direct-probe-rows/1"')

    def stage(self, name, files=None):
        path = self.base + "/stages/" + name
        os.makedirs(path)
        for rel, data in (files or {}).items():
            S.write(path + "/" + rel, data)
        return path

    @staticmethod
    def frozen(stage):
        """The stage's frozen input descriptors and its exact entries, as they are now."""
        inputs, entries = [], []
        for parent, directories, names in os.walk(stage):
            for name in directories:
                entries.append({"path": os.path.relpath(os.path.join(parent, name), stage), "kind": "directory"})
            for name in names:
                full = os.path.join(parent, name)
                entries.append({"path": os.path.relpath(full, stage), "kind": "file"})
                inputs.append(S.descriptor(full))
        return sorted(inputs, key=lambda row: row["path"]), sorted(entries, key=lambda row: row["path"])

    @staticmethod
    def expected(returncode=0, **overrides):
        value = {"returncode": returncode,
                 "supervisor_error": None if returncode == 0 else {
                     "code": "OTRAY-E-BACKEND", "reason": "Child exited with status %d" % returncode, "state": "REJECTED"},
                 "stdout_exact": None, "stderr_exact": None, "stdout_includes": [], "stdout_excludes": [],
                 "stderr_includes": [], "stderr_excludes": [], "absent_paths": [], "present_paths": [],
                 "file_includes": {}, "json_members": {}}
        value.update(overrides)
        return value

    def row(self, ident, stage, expected=None, **overrides):
        if ident == "probe-syntax-check":
            argv, label = [self.node, "--check", self.probe], "probe-syntax"
        else:
            argv = [self.node, *NODE_FLAGS, "--experimental-loader", self.loader, self.probe,
                    "--expected-config-sha256", "a" * 63 + "b", "--job", stage + "/job.json"]
            label = "direct-probe"
        inputs, entries = self.frozen(stage)
        row = {"id": ident, "argv": argv, "stage": stage, "label": label, "environment": dict(S.DECLARED),
               "total_ms": 30000, "stage_ms": 28000, "inputs": inputs, "stage_entries": entries,
               "expected": expected or self.expected()}
        row.update(overrides)
        return row

    def document(self, rows, independent):
        if not self.legacy:
            return {"schema": "ontokin.c271.p35-direct-probe-rows/2", "rows_independent": independent, "rows": rows}
        old = []
        for row in rows:
            entry = {key: row[key] for key in ("id", "argv", "stage", "label", "environment", "total_ms", "stage_ms")}
            entry["expected"] = {key: row["expected"][key] for key in OLD_EXPECTED}
            old.append(entry)
        return {"schema": "ontokin.c271.p35-direct-probe-rows/1", "rows_independent": independent, "rows": old}

    def arguments(self, rows, *, independent=False, bindings=None, node_digest=None, rows_digest=None, raw_rows=None,
                  root=None):
        index = len(os.listdir(self.base))
        document = raw_rows if raw_rows is not None else self.document(rows, independent)
        rows_path = S.write(self.base + "/rows-%d.json" % index, json.dumps(document).encode())
        output = self.base + "/run-%d" % index
        args = ["--root", root or self.root]
        for rel, digest in (bindings or self.bindings).items():
            args += ["--bind", rel + "=" + digest]
        args += ["--rows", rows_path, "--rows-sha256", rows_digest or S.sha256_file(rows_path),
                 "--node", self.node, "--node-sha256", node_digest or S.sha256_file(self.node),
                 "--probe", self.probe, "--probe-sha256", S.sha256_file(self.probe),
                 "--loader", self.loader, "--loader-sha256", S.sha256_file(self.loader), "--output-dir", output]
        return args, output

    def record(self, output):
        record = S.read_json(output + "/run.json") if os.path.isfile(output + "/run.json") else None
        if record is not None:
            S.count_tool_starts(STAND_IN if self.stand_in else self.node, len(record.get("process_events", [])))
        return record

    def run(self, rows, *, tool_path=None, **kwargs):
        args, output = self.arguments(rows, **kwargs)
        completed = S.run_tool("run_direct_probe.py", *args, flags=("-I", "-S", "-B"),
                               env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}, tool_path=tool_path)
        return completed, self.record(output), output


def outcome(output, ident):
    return S.read_json(output + "/" + ident + "/outcome.json")


class RunnerTests(unittest.TestCase):
    def test_one_start_through_the_real_darwin_supervisor_with_its_receipt_and_started_record(self):
        world = RunnerWorld(self, "/usr/bin/true")
        stage = world.stage("syntax")
        completed, record, output = world.run([world.row("probe-syntax-check", stage, world.expected(
            absent_paths=[stage + "/probe.json"], stdout_exact="", stderr_exact=""))])
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        self.assertEqual(record["state"], "ALL_ROWS_MET")
        self.assertEqual(record["node_starts"], {"exact": 1, "observed_lower_bound": 1})
        self.assertTrue(all(row["compiled_from_verified_bytes"] for row in record["loaded_project_files"]))
        self.assertEqual(sorted(Path(row["path"]).name for row in record["loaded_project_files"]),
                         ["__init__.py", "__init__.py", "supervisor.py", "supervisor_darwin_v01.py"])
        self.assertIsNone(record["darwin_precondition_before_rows"])
        # TR-01 in either place (IP-01): the root here is the project root. From the author's directory the runner
        # lies outside it, and admits nothing; at its committed place it lies inside it, and admits exactly its own
        # __main__, by realpath.
        place = S.admission_place("run_direct_probe.py", world.root)
        self.assertEqual(record["own_main_admitted"], S.expected_admission("run_direct_probe.py", world.root),
                         "the runner lies " + place)
        self.assertTrue(record["supervisor_checks"]["json_bytes_is_the_original"])
        row = outcome(output, "probe-syntax-check")
        self.assertEqual((row["state"], row["start_count_state"], row["actual_starts"]), ("COMPLETED", "OBSERVED_ONE", 1))
        self.assertTrue(row["receipt_file_matches_record"])
        self.assertTrue(row["cleanup_complete"])
        self.assertEqual(row["process"]["environment"], S.DECLARED)
        self.assertEqual(row["process"]["cwd"], stage)
        started = S.read_json(output + "/probe-syntax-check/started-1.json")
        self.assertEqual(started["process"]["pid"], row["process"]["pid"])
        self.assertTrue(os.path.isfile(stage + "/probe-syntax.process.json"))
        self.assertEqual(row["process_events"][0]["argv"], [world.node, "--check", world.probe])
        # TR-10: the boot session around the row; TR-02: no supervisor error, as the row expects.
        self.assertTrue(row["boot_unchanged"])
        self.assertIsNotNone(row["boot_before"])
        self.assertEqual(row["boot_before"], record["boot_session_uuid_before_rows"])
        self.assertTrue(row["predicates"]["supervisor_error_raised"] and row["predicates"]["supervisor_error_in_receipt"])
        self.assertTrue(row["predicates"]["stdout_exact"] and row["predicates"]["stderr_exact"])
        self.assertEqual(row["verified_before_start"]["stage_entries"], [])
        self.assertEqual(row["verified_before_start"]["targets_absent_at_intent"], [])

    def test_a_nonzero_exit_is_kept_raw_and_an_unmet_row_stops_the_later_rows(self):
        world = RunnerWorld(self, "/bin/sh")
        first, second, third = (world.stage(name, {"job.json": b"{}"}) for name in ("h01", "h02", "mc36"))
        rows = [world.row("P06-H01", first, world.expected(2, stderr_includes=["--no-addons: invalid option"])),
                world.row("P06-H02", second, world.expected(1)),
                world.row("MC36", third, world.expected(2))]
        completed, record, output = world.run(rows)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual([row["state"] for row in record["rows"]], ["COMPLETED", "COMPLETED", "NOT_RUN"])
        self.assertEqual([row.get("expectation_met") for row in record["rows"][:2]], [True, False])
        self.assertEqual(record["node_starts"]["exact"], 2)
        h01 = outcome(output, "P06-H01")
        self.assertEqual(h01["process"]["returncode"], 2)
        self.assertEqual(h01["supervisor_failure"], {"code": "OTRAY-E-BACKEND", "reason": "Child exited with status 2",
                                                     "state": "REJECTED"})
        self.assertEqual(h01["receipt_error"], h01["supervisor_failure"])
        self.assertIn("--no-addons: invalid option", h01["stderr"]["text"])
        self.assertEqual(h01["verified_before_start"]["inputs"][0]["path"], first + "/job.json")
        h02 = outcome(output, "P06-H02")
        self.assertFalse(h02["predicates"]["returncode"])
        self.assertFalse(h02["predicates"]["supervisor_error_raised"], "status 2 is not the expected status 1's error")
        self.assertFalse(os.path.exists(output + "/MC36"), "a row after an unmet row was started")

    def test_independent_rows_all_run(self):
        world = RunnerWorld(self, "/bin/sh")
        rows = [world.row("P06-H01", world.stage("a", {"job.json": b"{}"}), world.expected(1)),
                world.row("MC30-probe", world.stage("b", {"job.json": b"{}"}), world.expected(2))]
        completed, record, _ = world.run(rows, independent=True)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual([row["expectation_met"] for row in record["rows"]], [False, True])
        self.assertEqual(record["node_starts"]["exact"], 2)

    def test_bound_inputs_and_row_shapes_refuse_before_any_start(self):
        world = RunnerWorld(self, "/usr/bin/true")
        wrong = dict(world.bindings)
        wrong["prototypes/static_tray_v01/supervisor.py"] = "0" * 63 + "1"
        count = iter(range(1000))

        def fresh(files=None):
            """Each case its own stages, so that no earlier start leaves outputs in a later case's stage."""
            return world.stage("s%d" % next(count), files)

        def syntax(**overrides):
            return world.row("probe-syntax-check", fresh(), **overrides)

        def job_row(ident="P06-H01", **overrides):
            return world.row(ident, fresh({"job.json": b"{}"}), **overrides)

        def shared_stage():
            stage = fresh()
            return [world.row("probe-syntax-check", stage), world.row("P06-H01", stage)]

        def input_digest():
            stage = fresh({"job.json": b"{}"})
            return [world.row("P06-H01", stage, inputs=[dict(S.descriptor(stage + "/job.json"), sha256="0" * 63 + "1")])]
        cases = {
            "supervisor digest": (lambda: [syntax()], lambda: dict(bindings=wrong), "SUPERVISOR"),
            "node digest": (lambda: [syntax()], lambda: dict(node_digest="0" * 63 + "1"), "BINDING"),
            "rows digest": (lambda: [syntax()], lambda: dict(rows_digest="0" * 63 + "1"), "ROWS"),
            "argv shape": (lambda: [syntax(argv=[world.node, world.probe])], dict, "ROWS"),
            "environment": (lambda: [syntax(environment=dict(S.DECLARED, EXTRA="1"))], dict, "ROWS"),
            "limits": (lambda: [syntax(stage_ms=29000)], dict, "ROWS"),
            "unknown row": (lambda: [syntax(id="P06-H03")], dict, "ROWS"),
            "duplicate row": (lambda: [syntax(), syntax(label="other")], dict, "ROWS"),
            "schema": (lambda: None, lambda: dict(raw_rows={"schema": "other", "rows_independent": False,
                                                            "rows": [syntax()]}), "ROWS"),
            "supervisor error not implied by the status (TR-02)":
                (lambda: [syntax(expected=world.expected(1, supervisor_error=None))], dict, "ROWS"),
            "shared stage (TR-10)": (shared_stage, dict, "ROWS"),
            "input digest (TR-03)": (input_digest, dict, "ROW-INPUT"),
            "unbound stage file (TR-03)": (lambda: [job_row(inputs=[])], dict, "ROWS"),
            "stage entries (TR-03)": (lambda: [job_row("MC36", stage_entries=[])], dict, "ROW-STAGE")}
        for name, (rows, arguments, rule) in cases.items():
            with self.subTest(name):
                completed, record, _ = world.run(rows(), **arguments())
                self.assertEqual(completed.returncode, 2, completed.stderr.decode())
                self.assertEqual((record["state"], record["refusal"]["rule"]), ("REFUSED", rule))
                self.assertNotIn("process_events", record)
        stage = fresh()
        S.write(stage + "/probe-syntax.stdout.log", b"")
        completed, record, _ = world.run([world.row("probe-syntax-check", stage)])
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "ROW-TARGET"))
        self.assertEqual(os.listdir(stage), ["probe-syntax.stdout.log"])


class SupervisorRefusalTests(unittest.TestCase):
    """TR-02: a supervisor Stop other than the expected exit status misses the row."""

    def test_a_remaining_descendant_misses_the_row_although_the_child_exited_zero(self):
        world = RunnerWorld(self, stand_in=DESCENDANT)
        completed, record, output = world.run([world.row("probe-syntax-check", world.stage("syntax"))])
        S.count_tool_starts("fork of a stand-in", 1)
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        self.assertEqual(record["state"], "ROWS_UNMET")
        row = outcome(output, "probe-syntax-check")
        self.assertEqual(row["process"]["returncode"], 0)
        self.assertEqual(row["supervisor_failure"]["reason"], "Child exited while an owned descendant remained")
        self.assertEqual(row["receipt_error"], row["supervisor_failure"])
        self.assertFalse(row["predicates"]["supervisor_error_raised"])
        self.assertFalse(row["predicates"]["supervisor_error_in_receipt"])
        self.assertTrue(row["predicates"]["returncode"])
        self.assertTrue(row["cleanup_complete"], "the supervisor ended the descendant's group")
        self.assertFalse(row["expectation_met"])

    def test_a_staged_link_misses_the_row_although_the_child_exited_zero(self):
        world = RunnerWorld(self, stand_in=STAGED_LINK)
        completed, record, output = world.run([world.row("probe-syntax-check", world.stage("syntax"))])
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        row = outcome(output, "probe-syntax-check")
        self.assertEqual(row["process"]["returncode"], 0)
        self.assertEqual(row["supervisor_failure"], {"code": "OTRAY-E-BINDING", "reason": "A staged path is a symlink",
                                                     "state": "REJECTED"})
        self.assertFalse(row["predicates"]["supervisor_error_raised"])
        self.assertFalse(row["expectation_met"])


class FrozenStateTests(unittest.TestCase):
    """TR-03: predicate targets absent at intent; inputs and stage entries verified just before the start."""

    def test_a_target_that_exists_before_the_start_refuses_the_row_before_any_start(self):
        world = RunnerWorld(self, "/bin/sh")
        stage = world.stage("mc36", {"job.json": b"{}", "probe.json": b'{"error": {"message": "synthetic marker"}}'})
        row = world.row("MC36", stage, world.expected(2, file_includes={stage + "/probe.json": ["synthetic marker"]}))
        completed, record, output = world.run([row])
        self.assertEqual(completed.returncode, 2, completed.stderr.decode()[-3000:])
        self.assertEqual((record["state"], record["refusal"]["rule"]), ("REFUSED", "ROW-TARGET"))
        self.assertEqual(record["refusal"]["details"]["paths"], [stage + "/probe.json"])
        self.assertNotIn("process_events", record)
        self.assertFalse(os.path.exists(output + "/MC36"))

    def test_inputs_and_stage_entries_are_verified_again_immediately_before_each_start(self):
        world = RunnerWorld(self, "/usr/bin/true")
        h01 = world.stage("h01", {"job.json": b"{}"})
        h02 = world.stage("h02", {"job.json": b"{}"})
        # The first row's stand-in changes the second row's input and adds an entry to the third row's stage.
        world.node = S.stand_in(world.base + "/inputs/node-stand-in", changes_other_rows(h01 + "/job.json", h02))
        world.stand_in = True
        rows = [world.row("probe-syntax-check", world.stage("syntax")), world.row("P06-H01", h01),
                world.row("P06-H02", h02)]
        completed, record, output = world.run(rows, independent=True)
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        self.assertEqual([row["state"] for row in record["rows"]],
                         ["COMPLETED", "REFUSED_BEFORE_START", "REFUSED_BEFORE_START"])
        self.assertEqual(record["node_starts"]["exact"], 1)
        self.assertEqual(outcome(output, "P06-H01")["refusal"]["rule"], "ROW-INPUT")
        stage_refusal = outcome(output, "P06-H02")["refusal"]
        self.assertEqual((stage_refusal["rule"], stage_refusal["details"]["extra"]), ("ROW-STAGE", ["late.txt"]))
        self.assertTrue(os.path.isfile(output + "/P06-H01/intent.json"))
        self.assertFalse(os.path.exists(output + "/P06-H01/started-1.json"))


class PredicateTests(unittest.TestCase):
    """TR-10: exact and negative predicates, the JSON members of probe.json."""

    def test_exact_streams_and_json_members_equal_or_absent(self):
        world = RunnerWorld(self, stand_in=REFUSING_PROBE)
        plain = world.stage("plain", {"job.json": b"{}"})
        khronos = world.stage("with-khronos", {"job.json": b"{}"})

        def expected(stage):
            return world.expected(1, stdout_exact="", stderr_exact="", stderr_excludes=["Traceback"],
                                  json_members={stage + "/probe.json": [
                                      {"pointer": "/passed", "equals": False},
                                      {"pointer": "/error/message", "equals": "synthetic refusal"},
                                      {"pointer": "/khronos", "absent": True}]})
        rows = [world.row("P06-H01", plain, expected(plain)), world.row("P06-H02", khronos, expected(khronos))]
        completed, record, output = world.run(rows, independent=True)
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        self.assertEqual([row["expectation_met"] for row in record["rows"]], [True, False])
        members = outcome(output, "P06-H02")["predicates"]["json_members"][khronos + "/probe.json"]["members"]
        self.assertEqual([member["met"] for member in members], [True, True, False])
        self.assertEqual(outcome(output, "P06-H01")["verified_before_start"]["targets_absent_at_intent"],
                         [plain + "/probe.json"])


class PlaceAndLoadingTests(unittest.TestCase):
    def test_it_runs_from_its_committed_place_inside_the_root(self):
        """TR-01: its own __main__ lies under the root; it is admitted by realpath and recorded."""
        base = S.resolved_temp(self)
        root = base + "/root"
        for rel in SUPERVISOR_FILES:
            S.write(root + "/" + rel, Path(S.project_root() + "/" + rel).read_bytes())
        copy = S.in_place(root, "run_direct_probe.py")
        world = RunnerWorld(self, "/usr/bin/true", root=root)
        completed, record, _ = world.run([world.row("probe-syntax-check", world.stage("syntax"))], tool_path=copy)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-3000:])
        self.assertEqual(record["state"], "ALL_ROWS_MET")
        self.assertEqual(record["own_main_admitted"]["path"], copy)
        self.assertTrue(record["own_main_admitted"]["admitted"])
        self.assertEqual(sorted(row["path"] for row in record["loaded_project_files"]),
                         sorted(root + "/" + rel for rel in SUPERVISOR_FILES))

    def test_a_supervisor_without_json_bytes_is_not_the_original(self):
        """TR-10: json_bytes_is_the_original needs 'is not None'; such a supervisor refuses before any row."""
        base = S.resolved_temp(self)
        root = base + "/fake"
        S.write(root + "/prototypes/__init__.py", b"")
        S.write(root + "/prototypes/static_tray_v01/__init__.py", b"")
        S.write(root + "/prototypes/static_tray_v01/supervisor.py", b"class Clock:\n    pass\n\n\n"
                                                                    b"class Stop(Exception):\n    pass\n")
        S.write(root + "/prototypes/static_tray_v01/supervisor_darwin_v01.py",
                b"from prototypes.static_tray_v01.supervisor import Clock, Stop\n\n\n"
                b"def run_process(*args, **kwargs):\n    raise RuntimeError('never called')\n")
        world = RunnerWorld(self, "/usr/bin/true", root=root)
        completed, record, _ = world.run([world.row("probe-syntax-check", world.stage("syntax"))])
        self.assertEqual(completed.returncode, 2, completed.stderr.decode()[-3000:])
        self.assertEqual(record["refusal"]["rule"], "SUPERVISOR")
        self.assertFalse(record["refusal"]["details"]["checks"]["json_bytes_is_the_original"])
        self.assertNotIn("process_events", record)


class InterruptionTests(unittest.TestCase):
    """TR-18: an interruption after a start; the supervisor's cleanup ends the child, and nothing else runs."""

    def interrupt(self, number):
        world = RunnerWorld(self, stand_in=SLEEPER)
        rows = [world.row("probe-syntax-check", world.stage("syntax")),
                world.row("P06-H01", world.stage("h01", {"job.json": b"{}"}))]
        args, output = world.arguments(rows, independent=True)
        process = S.start_tool("run_direct_probe.py", *args, flags=("-I", "-S", "-B"),
                               env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
        try:
            deadline = time.monotonic() + 20
            while not os.path.exists(output + "/probe-syntax-check/started-1.json"):
                self.assertIsNone(process.poll(), "the runner ended before its start")
                self.assertLess(time.monotonic(), deadline, "no started record")
                time.sleep(0.05)
            time.sleep(0.3)
            process.send_signal(number)
            _, stderr = process.communicate(timeout=60)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
        record = world.record(output)
        return process.returncode, stderr, record, output

    def test_sigint_and_sigterm_after_a_start(self):
        for number in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=signal.Signals(number).name):
                code, stderr, record, output = self.interrupt(number)
                self.assertEqual(code, 3, stderr.decode()[-3000:])
                self.assertEqual(record["state"], "UNKNOWN")
                self.assertTrue(record["interrupted"])
                row = outcome(output, "probe-syntax-check")
                self.assertTrue(row["interrupted"])
                self.assertTrue(row["supervisor_failure"]["reason"].startswith("KeyboardInterrupt"))
                self.assertTrue(row["cleanup_complete"], "the supervisor ended the started child's group")
                self.assertFalse(row["expectation_met"])
                self.assertEqual(record["rows"][1]["state"], "NOT_RUN")
                self.assertEqual(record["node_starts"]["exact"], 1)


if __name__ == "__main__":
    unittest.main()
