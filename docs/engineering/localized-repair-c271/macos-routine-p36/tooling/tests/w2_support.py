"""Shared helpers of the MR tooling's focused tests: the standard library only, no machine path, no start.

The tests run from the tooling directory with the framework interpreter and -B (N-09):

    python3 -I -S -B -m unittest discover -s tests -v

They start no process: every tool is loaded from its file beside this directory and its main() is
called in this process. Synthetic unit-stage logs are written by this interpreter's own
unittest.TextTestRunner, so their format is unittest's, with text written into the same stream
to stand for the output that tests and their children put into the driver's log. An audit hook
counts every process-creation event of this test process; the hygiene test requires zero.

W2_TOOLING_UNDER_TEST=<directory> runs the same tests against another copy of the tools, such as
the rejected revision 001. Against a tool that predates a fix, a test writes its input in that
version's form where the form changed (an attribution, for example), so that it fails on what the
fix changes and not on the input's form.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import types
import unittest

TOOLING = (Path(os.environ["W2_TOOLING_UNDER_TEST"]).resolve() if os.environ.get("W2_TOOLING_UNDER_TEST")
           else Path(__file__).resolve().parents[1])
PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                            "os.system", "os.startfile"))
STARTS = []


def _audit(event, args):
    if event in PROCESS_EVENTS:
        STARTS.append(event)


sys.addaudithook(_audit)
_MODULES = {}


def tool(name):
    """The tool module loaded from its file beside tests/ (its -B guard runs only as __main__)."""
    if name not in _MODULES:
        spec = importlib.util.spec_from_file_location("w2_tool_" + name, TOOLING / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _MODULES[name] = module
    return _MODULES[name]


def run_tool(name, argv):
    """(exit code, stderr text) of the tool's main(argv), run in this process."""
    stream = io.StringIO()
    with contextlib.redirect_stderr(stream):
        code = tool(name).main(argv)
    return code, stream.getvalue()


def legacy(name, marker):
    """True when the tool under test is an earlier version, recognized by a marker missing from its source."""
    return marker not in (TOOLING / (name + ".py")).read_text(encoding="utf-8")


def driver_reading(raw):
    """What tools/check_local.py reads from a log's bytes, computed here independently of the tools:
    Path.read_text decodes with universal newlines, then the driver's three regular expressions."""
    text = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", errors="replace", newline=None).read()
    executions = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", text, re.MULTILINE)
    endings = re.findall(r"^(?:OK|FAILED)(?: \(([^\n]*)\))?$", text, re.MULTILINE)
    counts = {name.strip(): value for name, value in re.findall(r"([a-z ]+)=(\d+)", endings[-1])} if endings else {}
    skipped, expected_failures = int(counts.get("skipped", 0)), int(counts.get("expected failures", 0))
    count = int(executions[-1][0]) if executions else 0
    return {"tests_run": count, "skipped": skipped, "expected_failures": expected_failures,
            "executed_without_skips": max(0, count - skipped)}


def temp_dir(test):
    """A fresh resolved temporary directory, removed after the test."""
    base = os.path.realpath(tempfile.gettempdir())
    path = os.path.realpath(tempfile.mkdtemp(prefix="w2-tooling-", dir=base))
    test.addCleanup(shutil.rmtree, path, True)
    return path


def write(path, data):
    """Write bytes (or text) to a new file; returns its SHA-256."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as stream:
        stream.write(data)
    return hashlib.sha256(data).hexdigest()


def sha256(data):
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def read_json(path):
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def binding(path):
    data = Path(path).read_bytes()
    return {"sha256": sha256(data), "size_bytes": len(data), "mode": "0o%03o" % (os.stat(path).st_mode & 0o777)}


# ---------------------------------------------------------------------------
# Synthetic unit-stage logs written by unittest itself
# ---------------------------------------------------------------------------

class Noise:
    """Text written into the runner's own stream, as a test's output or a child's lands in the driver's log."""
    stream = None

    @classmethod
    def write(cls, text):
        cls.stream.write(text)


SEPARATOR1, SEPARATOR2 = "=" * 70, "-" * 70


class Outcomes(unittest.TestCase):
    __module__ = "test_synth"

    def test_pass(self):
        pass

    def test_fail(self):
        self.assertEqual(1, 2)

    def test_error(self):
        raise ValueError("broken value")

    @unittest.skip("not today")
    def test_skip_decorated(self):
        pass

    def test_skip_in_body(self):
        self.skipTest("it's \"quoted\"\nand on two lines")

    @unittest.expectedFailure
    def test_expected_failure(self):
        self.assertTrue(False)

    @unittest.expectedFailure
    def test_unexpected_success(self):
        pass

    def test_subtests(self):
        for number in range(3):
            with self.subTest(i=number):
                if number == 1:
                    self.assertEqual(number, 0)
                if number == 2:
                    raise KeyError("missing key")

    def test_subtest_skip(self):
        with self.subTest(case="a"):
            self.skipTest("subtest skipped")
        with self.subTest(case="b"):
            pass

    def test_docstring_pass(self):
        """First docstring line.

        More text that unittest does not print.
        """

    def test_docstring_fail(self):
        """Docstring of a failing test."""
        self.fail("failed with a docstring")

    def test_docstring_subtests(self):
        """Docstring with subtests."""
        for number in (1, 2):
            with self.subTest("message", n=number):
                self.assertLess(number, 2)

    def test_multiline_reason(self):
        self.assertEqual([1, 2, 3], [1, 2, 4])

    def test_chained(self):
        try:
            {}["k"]
        except KeyError as exc:
            raise RuntimeError("outer failure") from exc


class TearDownError(unittest.TestCase):
    __module__ = "test_synth"

    def tearDown(self):
        raise OSError("teardown broke")

    def test_fail_then_teardown_error(self):
        self.fail("first the failure")


class SetUpClassError(unittest.TestCase):
    __module__ = "test_synth"

    @classmethod
    def setUpClass(cls):
        raise RuntimeError("class setup broke")

    def test_never_runs(self):
        pass


class TearDownClassError(unittest.TestCase):
    __module__ = "test_synth"

    @classmethod
    def tearDownClass(cls):
        raise RuntimeError("class teardown broke")

    def test_runs(self):
        pass


class SetUpClassSkip(unittest.TestCase):
    __module__ = "test_synth"

    @classmethod
    def setUpClass(cls):
        raise unittest.SkipTest("the whole class is skipped")

    def test_never_either(self):
        pass


class ModuleFixtureCase(unittest.TestCase):
    __module__ = "test_synth_module"

    def test_not_run_after_module_setup(self):
        pass


class Interleaved(unittest.TestCase):
    __module__ = "test_synth"

    def test_full_lines_between_start_and_status(self):
        Noise.write("printed line one\nprinted line two\n")

    def test_partial_line_glued_before_status(self):
        Noise.write("a block-buffered chunk that ends mid-line")

    def test_warning_like_lines(self):
        Noise.write("<file>:12: DeprecationWarning: something\n  pid = os.fork()\nchild says hello\n")

    def test_noise_with_dots_and_parentheses(self):
        Noise.write("not a test (really) ... no\nprogress ... 50% ... ok so far\n")

    def test_partial_then_fail(self):
        Noise.write("chunk without an end")
        self.fail("failure after partial noise")

    def test_fake_footer_in_output(self):
        Noise.write("\n" + SEPARATOR2 + "\nRan 1 test in 0.000s\n\nOK\n")

    def test_reason_with_a_foreign_header(self):
        self.fail("text\n" + SEPARATOR1 + "\nFAIL: test_other (elsewhere.Other.test_other)\n" + SEPARATOR2 + "\nend")


class TwoCandidates(unittest.TestCase):
    """Printed text that leaves two status candidates after a start, with equal or different values (TR-05)."""
    __module__ = "test_synth"

    def test_noise_ending_like_a_status(self):
        Noise.write("this line ends with look\n")

    def test_noise_ending_with_another_status(self):
        Noise.write("the last status was ERROR\n")


class Swap(unittest.TestCase):
    """W3's probe PR-3: two printed imitations that would swap a skipped and a passing test."""
    __module__, __qualname__ = "test_probe", "Swap"

    def test_a_really_skipped(self):
        Noise.write("\nok\npartial")
        self.skipTest("the real reason")

    def test_b_really_passes(self):
        Noise.write("\nskipped 'an imitation'\npartial")


class SkipReason(unittest.TestCase):
    """W3's probe PR-3b: a printed imitation that would replace a recorded skip reason."""
    __module__, __qualname__ = "test_probe", "SkipReason"

    def test_c_skip_reason(self):
        Noise.write("\nskipped 'printed by the test'\npartial")
        self.skipTest("the real reason")


class GluedStart(unittest.TestCase):
    __module__ = "test_synth"

    @classmethod
    def setUpClass(cls):
        Noise.write("class setup chunk without a line end")

    def test_after_glued_noise(self):
        pass


def module_with_failing_setup():
    module = types.ModuleType("test_synth_module")

    def setUpModule():
        raise RuntimeError("module setup broke")
    module.setUpModule = setUpModule
    return module


def failed_import(name):
    """unittest's own test for a module that failed to import, named as discovery names it (dotted in a package)."""
    try:
        raise ImportError("synthetic import failure of " + name)
    except ImportError:
        return unittest.loader._make_failed_import_test(name, unittest.TestSuite)[0]


def unittest_log(*cases, trailing="", import_failure=None, module_setup_error=False, duplicate=None, extra_tests=()):
    """Run the cases with this interpreter's TextTestRunner (verbosity 2, as -v) and return its text."""
    stream = io.StringIO()
    Noise.stream = stream
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for case in cases:
        suite.addTests(loader.loadTestsFromTestCase(case))
    if duplicate is not None:
        suite.addTests(loader.loadTestsFromTestCase(duplicate))
    for test in extra_tests:
        suite.addTest(test)
    if import_failure:
        suite.addTests(loader.loadTestsFromName(import_failure))
    saved = sys.modules.get("test_synth_module")
    if module_setup_error:
        sys.modules["test_synth_module"] = module_with_failing_setup()
        suite.addTests(loader.loadTestsFromTestCase(ModuleFixtureCase))
    try:
        unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    finally:
        if module_setup_error:
            if saved is None:
                sys.modules.pop("test_synth_module", None)
            else:
                sys.modules["test_synth_module"] = saved
    stream.write(trailing)
    return stream.getvalue()


def collect(test, text, *extra, name="unit-tests.log", directory=None):
    """Write a log, run `collect` on it, and return (exit code, output document, stderr, log path)."""
    directory = directory or temp_dir(test)
    log = os.path.join(directory, name)
    digest = write(log, text)
    output = os.path.join(directory, name + ".outcomes.json")
    code, stderr = run_tool("unit_log_outcomes", ["collect", "--log", log, "--log-sha256", digest, *extra,
                                                  "--output", output])
    return code, read_json(output), stderr, log


# ---------------------------------------------------------------------------
# Synthetic driver summaries
# ---------------------------------------------------------------------------

def summary(output, log_sha256, log_bytes, *, test_execution, documents="passed", pending=None, steps=None,
            source_root=None, python=None, surface_summary=None):
    """A summary.json document of tools/check_local.py's schema for one run, with the fields the tools read."""
    pending = [{"step": "surface", "report": "reports/surface.json", "id": "M01", "reasons": ["external"]}] \
        if pending is None else pending
    surface = {"total": 12, "pending": len(pending)} if surface_summary is None else surface_summary
    rows = [{"id": "unit-tests", "argv": ["python", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
             "cwd": output + "/workspace", "status": "failed", "returncode": 1, "process_started": True,
             "log": "logs/unit-tests.log", "log_identity": {"sha256": "sha256:" + log_sha256, "bytes": log_bytes},
             "test_execution": test_execution, "reports": []},
            {"id": "surface", "cwd": output + "/workspace", "status": "passed", "returncode": 0, "process_started": True,
             "reports": [{"path": "reports/surface.json", "sha256": "sha256:" + "0" * 64, "bytes": 1,
                          "outcomes": {"status": "passed", "summary": surface},
                          "pending_cases": [{"id": row["id"], "reasons": row["reasons"]} for row in pending]}]},
            {"id": "documents", "cwd": output + "/workspace", "status": documents, "returncode": 0,
             "process_started": True, "reports": []}]
    return {"schema_version": "ontokin.local-checks/0.1", "profile": "core", "selected_roles": ["core"],
            "status": "failed", "exit_code": 1, "source_root": source_root or output + "/checkout",
            "environment": {"python": "3.12", "python_executable": python or output + "/checkout/.venv/bin/python",
                            "platform": "synthetic", "architecture": "arm64"},
            "planned_steps": [row["id"] for row in (steps or rows)], "steps": steps or rows,
            "pending_external_cases": pending, "not_executed_steps": [], "readback_selection": {"status": "absent",
                                                                                             "run_kind": "ordinary"}}


def driver_run(test, directory, text, **options):
    """A run directory holding logs/unit-tests.log and summary.json; returns the paths and digests."""
    os.makedirs(os.path.join(directory, "logs"))
    log = os.path.join(directory, "logs", "unit-tests.log")
    log_sha256 = write(log, text)
    reading = driver_reading(text.encode("utf-8"))
    document = summary(directory, log_sha256, len(text.encode("utf-8")), test_execution=dict(
        reading, complete_regression_passed=False), **options)
    path = os.path.join(directory, "summary.json")
    summary_sha256 = write(path, json.dumps(document, indent=2))
    return {"log": log, "log_sha256": log_sha256, "summary": path, "summary_sha256": summary_sha256,
            "output": directory, "document": document}


ATTRIBUTIONS_V2 = "ontokin.c271.p36-attributions/2"


def attribution_file(directory, name, rows):
    """An attribution file for the comparator under test; returns (path, SHA-256).

    rows are revision 2's complete statements. Against revision 001, whose only form is
    {id, outcome, reason_first_line}, each row is written in that form with its first own reason
    (or else its first failing subtest's), so that a test fails on the defect and not on the form.
    """
    if legacy("unit_log_outcomes", ATTRIBUTIONS_V2):
        old = []
        for row in rows:
            reasons = [event.get("reason_first_line") for event in row["events"] if event["status"] in ("FAIL", "ERROR")]
            reasons += [event["reason_first_line"] for event in row["failing_subtests"]]
            old.append({"id": row["id"], "outcome": row["outcome"], "reason_first_line": reasons[0] if reasons else None})
        document = {"schema": "ontokin.c271.p36-attributions/1", "attributions": old}
    else:
        document = {"schema": ATTRIBUTIONS_V2, "attributions": rows}
    path = os.path.join(directory, name)
    return path, write(path, json.dumps(document))


def compare_argv(baseline, candidate, output, *extra):
    return ["compare", "--baseline-log", baseline["log"], "--baseline-log-sha256", baseline["log_sha256"],
            "--baseline-summary", baseline["summary"], "--baseline-summary-sha256", baseline["summary_sha256"],
            "--candidate-log", candidate["log"], "--candidate-log-sha256", candidate["log_sha256"],
            "--candidate-summary", candidate["summary"], "--candidate-summary-sha256", candidate["summary_sha256"],
            *extra, "--output", output]


# ---------------------------------------------------------------------------
# Synthetic provider records of a qualifying run
# ---------------------------------------------------------------------------

PREFIX, VERSION = "ontokin.current-host-readback-", "/0.2.0"
IDENTITY = {"contract": "ontokin.current-host-readback/0.2.0", "design_revision": 4, "amendments": ["P33-AMENDMENT-001"]}
LABELS = {"boundary": "real", "run_kind": "qualifying", "executor": "macos-arm64-local", **IDENTITY}
CASES = {"Q01-positive": ("Q01", False), "Q03-positive": ("Q03", False), "Q01-changed-reference": ("Q01", True)}
NEGATIVE = {"code": "OTRAY-E-BACKEND", "reason": "Child exited with status 1", "state": "REJECTED"}
AUDIT_TOOL_SHA256 = "a" * 64
PROVIDER = "prototypes/static_tray_v01/current_host_readback_v02.py"
PROBE = "prototypes/static_tray_v01/current_host_readback_v02.mjs"


def json_file(path, value):
    return write(path, json.dumps(value, sort_keys=True, separators=(",", ":")))


def make_cohort(evidence, *, preserved, config_path, config_sha256, workspace, source):
    """A consistent cohort root as the provider leaves it; returns (cohort root, original root)."""
    original = os.path.join(evidence, "current-host-cpu-abcd1234" if preserved else "cohort")
    root = original + "-preserved-" + "e" * 32 if preserved else original
    node, loader = os.path.join(evidence, "runtime", "bin", "node"), os.path.join(evidence, "reader", "three_loader.mjs")
    probe = workspace + "/" + PROBE
    template = [node, "--no-addons", "--max-old-space-size=256", "--experimental-loader", loader, probe,
                "--expected-config-sha256", config_sha256, "--job", original + "/unused-native-schedule/N01/job.json"]
    manifest = {"schema": PREFIX + "lock" + VERSION, **IDENTITY, "labels": LABELS, "cohort_root": original,
                "schedule_root": original + "/unused-native-schedule",
                "selection": {"path": config_path, "sha256": config_sha256},
                "slots": [{"slot": "N%02d" % index, "argv": template} for index in range(1, 13)],
                "runtime": {"executable": node}, "probe": probe}
    manifest_sha256 = json_file(os.path.join(root, "supplemental-cpu.json"), manifest)
    boot = {"boot_session_uuid": "BOOT-0001", "stage": "before the cohort"}
    json_file(os.path.join(root, "setup.pending.json"), {"schema": PREFIX + "setup" + VERSION, **IDENTITY,
                                                         "passed": False, "checker_starts": 0, "run_kind": "qualifying"})
    json_file(os.path.join(root, "setup.json"), {"schema": PREFIX + "setup" + VERSION, **IDENTITY, "labels": LABELS,
                                                 "run_kind": "qualifying", "passed": True, "checker_starts": 0,
                                                 "boot": boot, "config_path": config_path,
                                                 "config_sha256": config_sha256, "manifest_sha256": manifest_sha256,
                                                 "source_root": workspace})
    attempts = {}
    for number, (label, (case, negative)) in enumerate(CASES.items()):
        stage, ledger = os.path.join(root, label), os.path.join(root, "provider-ledgers", label)
        original_stage = original + "/" + label
        glb = write(os.path.join(stage, "synthetic.glb"), b"GLB " + label.encode())
        audit = json_file(os.path.join(stage, "synthetic-audit.json"), {"case": case})
        job = {"slot": "CPU-" + label, "case": case, "manifest": original + "/supplemental-cpu.json",
               "supplemental_manifest_sha256": manifest_sha256, "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
               "artifact": original_stage + "/synthetic.glb", "artifact_sha256": glb,
               "audit": original_stage + "/synthetic-audit.json", "audit_sha256": audit,
               "result": original_stage + "/probe.json"}
        json_file(os.path.join(stage, "job.json"), job)
        json_file(os.path.join(stage, "probe.json"), {"passed": not negative, "artifact_sha256": glb,
                                                      "input_preserved": True, "slot": "CPU-" + label})
        argv = template[:-1] + [original_stage + "/job.json"]
        pid = 4100 + number
        started = {"argv": argv, "cwd": original_stage, "label": "synthetic-readback", "pid": pid,
                   "process_group": pid, "returncode": None, "cleanup": None, "handles_closed": False,
                   "error": None, "start_monotonic": 10.0 + number}
        failure = NEGATIVE if negative else None
        receipt = dict(started, returncode=1 if negative else 0, handles_closed=True, error=failure,
                       cleanup={"passed": True, "process_group_absent": True, "reaped": True}, end_monotonic=11.0 + number)
        json_file(os.path.join(stage, "synthetic-readback.process.json"), receipt)
        write(os.path.join(stage, "synthetic-readback.stdout.log"), b"")
        write(os.path.join(stage, "synthetic-readback.stderr.log"), b"")
        preflight = {"job": job, "job_binding": binding(os.path.join(stage, "job.json")),
                     "inputs": {"artifact": binding(os.path.join(stage, "synthetic.glb")),
                                "audit": binding(os.path.join(stage, "synthetic-audit.json"))},
                     "manifest_sha256": manifest_sha256, "config_sha256": config_sha256, "source": source}
        after = {name: binding(os.path.join(stage, name)) for name in sorted(os.listdir(stage))}
        ledger_base = {"schema": PREFIX + "attempt" + VERSION, **IDENTITY, "labels": LABELS, "expected_argv": argv,
                       "expected_checker_starts": 1}
        json_file(os.path.join(ledger, "reserved.json"), dict(ledger_base, state="PENDING", actual_checker_starts=0))
        json_file(os.path.join(ledger, "preflight.json"), preflight)
        json_file(os.path.join(ledger, "started.json"), {"process": started, "actual_checker_starts": 1})
        json_file(os.path.join(ledger, "supervisor-outcome.json"), {"process": receipt, "failure": failure,
                                                                    "actual_checker_starts": 1})
        json_file(os.path.join(ledger, "result.json"), dict(
            ledger_base, state="SUPERVISOR_REFUSAL" if negative else "COMPLETED", actual_checker_starts=1,
            provider_failure=None, supervisor_failure=failure, preflight=preflight, postflight=preflight,
            process=receipt, boot_before=dict(boot, stage="before the start"),
            boot_after=dict(boot, stage="after the start"), artifacts_after=after))
        attempts[label] = {"path": original + "/provider-ledgers/" + label + "/result.json",
                           **binding(os.path.join(ledger, "result.json"))}
    json_file(os.path.join(root, "cohort.json"), {"schema": PREFIX + "cohort" + VERSION, **IDENTITY, "labels": LABELS,
                                                  "passed": True, "expected_cases": sorted(CASES),
                                                  "attempts": attempts, "actual_checker_starts": 3})
    if preserved:
        files = {}
        for directory, _, names in os.walk(root):
            for name in names:
                path = os.path.join(directory, name)
                files[os.path.relpath(path, root)] = binding(path)
        json_file(os.path.join(root, "PRESERVATION.json"), {"schema": PREFIX + "preserved-cohort" + VERSION, **IDENTITY,
                                                            "original_root": original, "retained_root": root,
                                                            "files": files, "reason": "synthetic"})
        json_file(os.path.join(root, "CLEANUP.json"), {"owned_temporary_root": original, "removed": True})
    return root, original


def audit_record(root, *, tool_sha256=AUDIT_TOOL_SHA256, passed=True):
    """A numerical-audit record of MH's schema for the cohort root, binding its current bytes."""
    names = {"reference": "synthetic-audit.json", "report": "probe.json", "glb": "synthetic.glb", "job": "job.json"}
    cases = {}
    for label in CASES:
        cases[label] = {"passed": passed, "counts": {"expected_rows": 2060, "failed_rows": 1 if CASES[label][1] else 0},
                        "checks": {"rows_complete": True},
                        "inputs": {key: {"path": root + "/" + label + "/" + name,
                                         **binding(os.path.join(root, label, name))} for key, name in names.items()}}
    return {"schema": "ontokin.c271.p35-numerical-audit/2",
            "tool": {"path": "/tooling/audit_numeric.py", "sha256": tool_sha256, "size_bytes": 1, "mode": "0o644"},
            "invocation": {"python": {"flags": {"dont_write_bytecode": 1}}}, "cohort_root": root,
            "all_three_cases": True, "cases": cases, "negative_fixture": {"passed": True}, "passed": passed}


def make_driver_run(test, *, preserved=True):
    """A qualifying driver output with its readback binding, and its cohort; returns every path the reader takes."""
    base = temp_dir(test)
    evidence = os.path.join(base, "evidence")
    output = os.path.join(evidence, "r1")
    workspace, checkout = output + "/workspace", os.path.join(base, "checkout")
    os.makedirs(workspace)
    os.makedirs(checkout)
    original_config = os.path.join(base, "plans", "config.json")
    original_sha256 = write(original_config, b'{"schema": "ontokin.current-host-readback-config/0.2.0"}')
    inventory = {"sha256": "sha256:" + "1" * 64, "file_count": 1,
                 "files": [{"path": "README.md", "sha256": "sha256:" + "2" * 64, "bytes": 3}]}
    driver_before = write(os.path.join(output, "source-before.json"), json.dumps(inventory, indent=2) + "\n")
    directory = os.path.join(output, "readback-binding")
    head, tree = "3" * 40, "4" * 40
    descriptors = {}
    for name in ("source-before.json", "workspace-inventory.json"):
        json_file(os.path.join(directory, name), inventory)
        descriptors[name] = {"path": os.path.join(directory, name), **binding(os.path.join(directory, name))}
    parent_config = {"path": original_config, **binding(original_config)}
    workspace_binding = {"schema": PREFIX + "workspace" + VERSION, **IDENTITY, "identity": "5" * 32,
                         "parent_config": parent_config, "source_root": checkout, "workspace_root": workspace,
                         "commit": head, "tree": tree, "source_inventory": {"sha256": "6" * 64},
                         "source_before": descriptors["source-before.json"],
                         "workspace_inventory": descriptors["workspace-inventory.json"],
                         "immutable_inventory_sha256": "sha256:" + "7" * 64,
                         "provider": workspace + "/" + PROVIDER, "probe": workspace + "/" + PROBE}
    binding_path = os.path.join(directory, "workspace-binding.json")
    binding_sha256 = json_file(binding_path, workspace_binding)
    source = {"root": workspace, "commit": head, "tree": tree, "inventory": {"sha256": "6" * 64}}
    selection = {"schema": PREFIX + "config" + VERSION, "contract": IDENTITY["contract"], "source": source,
                 "evidence_root": evidence,
                 "parent": {"config": parent_config, "source_root": checkout,
                            "workspace_binding": {"path": binding_path, **binding(binding_path)}}}
    selection_path = os.path.join(directory, "selection.json")
    selection_sha256 = json_file(selection_path, selection)
    root, original = make_cohort(evidence, preserved=preserved, config_path=selection_path,
                                 config_sha256=selection_sha256, workspace=workspace, source=source)
    document = {"schema_version": "ontokin.local-checks/0.1", "status": "passed", "source_root": checkout,
                "git": {"available": True, "local_head": head, "local_tree": tree},
                "source_inventory": {"path": "source-before.json", "sha256": "sha256:" + driver_before,
                                     "inventory_sha256": inventory["sha256"], "file_count": 1},
                "readback_selection": {"status": "workspace_bound", "run_kind": "qualifying",
                                       "config_path": original_config, "expected_config_sha256": original_sha256,
                                       "config_sha256": original_sha256,
                                       "observed_identity": {"sha256": "sha256:" + original_sha256, "bytes": 1},
                                       "derived": {"config_path": selection_path, "config_sha256": selection_sha256,
                                                   "parent_config_sha256": original_sha256,
                                                   "workspace_binding_path": binding_path,
                                                   "workspace_binding_sha256": binding_sha256}},
                "steps": [{"id": "unit-tests", "cwd": workspace, "status": "passed", "returncode": 0,
                           "process_started": True, "removed_injection_environment_names": [],
                           "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
                                                     "ONTOKIN_CURRENT_HOST_READBACK_CONFIG": selection_path,
                                                     "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256": selection_sha256},
                           "test_execution": {"tests_run": 10, "skipped": 0, "expected_failures": 0}}]}
    summary_path = os.path.join(output, "summary.json")
    summary_sha256 = write(summary_path, json.dumps(document, indent=2) + "\n")
    audit_path = os.path.join(base, "audit-numeric.json")
    audit_sha256 = write(audit_path, json.dumps(audit_record(root)))
    return {"base": base, "evidence": evidence, "output": output, "summary": summary_path,
            "summary_sha256": summary_sha256, "cohort": root, "original": original, "audit": audit_path,
            "audit_sha256": audit_sha256, "workspace": workspace, "selection": selection_path,
            "original_config": original_config}


def reader_argv(run, output, *, command="run", audit=None, audit_sha256=None, tool_sha256=AUDIT_TOOL_SHA256):
    argv = [command]
    if command == "run":
        argv += ["--summary", run["summary"], "--summary-sha256", run["summary_sha256"]]
    return argv + ["--cohort-root", run["cohort"], "--audit", audit or run["audit"],
                   "--audit-sha256", audit_sha256 or run["audit_sha256"], "--audit-tool-sha256", tool_sha256,
                   "--output", output]


def rewrite_json(path, change):
    """Replace a JSON file's value by change(value), keeping its form (compact, sorted)."""
    value = read_json(path)
    value = change(value) or value
    os.remove(path)
    return json_file(path, value)
