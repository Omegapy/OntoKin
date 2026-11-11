"""Independent C207 CPU controls; no product child, Blender or Node execution."""
from __future__ import annotations

import argparse
import ast
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
REPO = args.repo.resolve()
OUT = args.out.resolve()
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))

from prototypes.static_tray_admission_c201 import input_lock as lock_module
from prototypes.static_tray_admission_c201 import transaction as tx
from prototypes.static_tray_admission_c201.schedule import SLOTS, canonical
from prototypes.static_tray_v01 import supervisor
from tests.test_static_tray_admission_c201_input_lock import Fixture
from tests.test_static_tray_admission_c201_transaction import TransactionFixture


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


UNEXPECTED_CHILD_CALLS = []
INTERCEPTED_SUPERVISOR_CALLS = []
DETAILS = []


def child_blocked(*a, **kw):
    UNEXPECTED_CHILD_CALLS.append({"arguments": repr(a), "keywords": repr(kw)})
    raise AssertionError("C207 independent review forbids product child launches")


class ReviewControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="c207-independent-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.counter = 0
        for target in ("subprocess.Popen", "os.fork", "os.system", "os.posix_spawn", "os.posix_spawnp"):
            self.enterContext(mock.patch(target, side_effect=child_blocked))

    def fixture(self, transaction=False):
        self.counter += 1
        path = self.base / str(self.counter)
        path.mkdir()
        return TransactionFixture(path) if transaction else Fixture(path)

    def repin_plan(self, fixture):
        # Deliberate synthetic reapproval lets policy checks run independently
        # of the outer digest; this is never a real approval or host assertion.
        fixture.context = replace(fixture.context, launch_plan_sha256=lock_module.launch_plan_digest(fixture.lock))
        fixture.repin()

    def lock_reject(self, fixture, code="COMMAND"):
        with self.assertRaises(lock_module.InputLockError) as found:
            fixture.validate()
        self.assertEqual(found.exception.code, code)
        for value in fixture.lock["stores"].values():
            self.assertEqual(list(Path(value).iterdir()), [])

    def transaction_reject(self, operation, code, state="REJECTED"):
        with self.assertRaises(tx.TransactionError) as found:
            operation()
        self.assertEqual(found.exception.code, "C201-" + code)
        self.assertEqual(found.exception.state, state)
        return found.exception

    def pointer(self, fixture, slot="A01"):
        p = Path(fixture.inputs.lock["stores"][slot]) / "state.json"
        return p.read_bytes() if p.exists() else None

    def test_coherent_twelve_stage_plans_remain_unauthorized(self):
        f = self.fixture()
        result = f.validate()
        for slot in (s.name for s in SLOTS):
            for stage in lock_module.STAGES:
                command = f.lock["commands"][slot][stage]
                self.assertEqual(command["cwd"], f.lock["outputs"][slot][stage])
                self.assertEqual(command["output"], command["cwd"])
                self.assertEqual(command["argv"][-2:], ["--job", str(Path(command["cwd"]) / "job.json")])
        self.assertFalse(result.native_start_authorized)
        self.assertFalse(result.native_readiness)
        self.assertFalse(result.admission_completed)

    def test_old_repository_cwd_rejected_for_every_slot_stage(self):
        for slot in (s.name for s in SLOTS):
            for stage in lock_module.STAGES:
                with self.subTest(slot=slot, stage=stage):
                    f = self.fixture()
                    f.lock["commands"][slot][stage]["cwd"] = str(f.repo)
                    self.repin_plan(f)
                    self.lock_reject(f)

    def test_cwd_lexical_alias_rejected_for_each_stage(self):
        for stage in lock_module.STAGES:
            with self.subTest(stage=stage):
                f = self.fixture()
                f.lock["commands"]["A01"][stage]["cwd"] += "/."
                self.repin_plan(f)
                self.lock_reject(f)

    def test_relative_cwd_rejected_for_each_stage(self):
        for stage in lock_module.STAGES:
            f = self.fixture()
            f.lock["commands"]["A01"][stage]["cwd"] = "."
            self.repin_plan(f)
            self.lock_reject(f)

    def test_cross_stage_cwd_rejected_for_each_stage(self):
        for i, stage in enumerate(lock_module.STAGES):
            f = self.fixture()
            other = lock_module.STAGES[(i + 1) % 3]
            f.lock["commands"]["A01"][stage]["cwd"] = f.lock["outputs"]["A01"][other]
            self.repin_plan(f)
            self.lock_reject(f)

    def test_cross_slot_output_alias_rejected(self):
        f = self.fixture()
        old = f.lock["outputs"]["A02"]["construction"]
        new = f.lock["outputs"]["A01"]["construction"]
        f.lock["outputs"]["A02"]["construction"] = new
        command = f.lock["commands"]["A02"]["construction"]
        command["cwd"] = command["output"] = new
        command["argv"][-1] = str(Path(new) / "job.json")
        self.repin_plan(f)
        self.lock_reject(f, "PATH")

    def test_wrong_job_argument_rejected_for_each_stage(self):
        for stage in lock_module.STAGES:
            f = self.fixture()
            f.lock["commands"]["A01"][stage]["argv"][-1] = str(f.repo / "job.json")
            self.repin_plan(f)
            self.lock_reject(f)

    def test_wrong_declared_output_rejected_for_each_stage(self):
        for stage in lock_module.STAGES:
            f = self.fixture()
            f.lock["commands"]["A01"][stage]["output"] = str(f.repo)
            self.repin_plan(f)
            self.lock_reject(f)

    def test_new_coherent_directory_rejected_by_unchanged_trusted_plan(self):
        f = self.fixture()
        path = f.base / "new-unreviewed-output"
        path.mkdir()
        f.lock["outputs"]["A01"]["construction"] = str(path)
        command = f.lock["commands"]["A01"]["construction"]
        command["cwd"] = command["output"] = str(path)
        command["argv"][-1] = str(path / "job.json")
        f.repin()
        self.lock_reject(f)

    def test_replaced_output_directory_rejected_before_preparation_all_stages(self):
        for stage in lock_module.STAGES:
            f = self.fixture(transaction=True)
            output = Path(f.inputs.lock["outputs"]["A01"][stage])
            output.rename(output.with_name(output.name + "-original"))
            output.mkdir()
            self.transaction_reject(lambda: f.prepare("A01"), "PATH")
            self.assertEqual(list(Path(f.inputs.lock["stores"]["A01"]).iterdir()), [])
            self.assertIsNone(self.pointer(f))

    def test_output_symlink_rejected_before_preparation_all_stages(self):
        for stage in lock_module.STAGES:
            f = self.fixture(transaction=True)
            output = Path(f.inputs.lock["outputs"]["A01"][stage])
            original = output.with_name(output.name + "-original")
            output.rename(original)
            output.symlink_to(original, target_is_directory=True)
            self.transaction_reject(lambda: f.prepare("A01"), "BINDING")
            self.assertIsNone(self.pointer(f))

    def test_actual_supervisor_launch_seam_uses_each_planned_stage(self):
        f = self.fixture()
        f.validate()
        for stage in lock_module.STAGES:
            command = f.lock["commands"]["A01"][stage]
            calls = []
            def intercept(argv, **kw):
                calls.append((argv, kw))
                INTERCEPTED_SUPERVISOR_CALLS.append({"stage": stage, "cwd": str(kw["cwd"]), "launched": False})
                raise OSError("Intentional CPU interception before any child exists")
            with mock.patch.object(supervisor.ctypes, "CDLL", return_value=types.SimpleNamespace(prctl=lambda *a: 0)), \
                 mock.patch.object(supervisor.subprocess, "Popen", side_effect=intercept):
                clock = supervisor.Clock()
                with self.assertRaises(supervisor.Stop):
                    supervisor.run_process(command["argv"], stage=command["output"], label=stage,
                                           clock=clock, stage_end=clock.started + 5, env=command["environment"])
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0], command["argv"])
            self.assertEqual(str(calls[0][1]["cwd"]), command["cwd"])
            self.assertEqual(calls[0][1]["env"], command["environment"])
            record = json.loads((Path(command["output"]) / (stage + ".process.json")).read_bytes())
            self.assertEqual(record["cwd"], command["cwd"])
            self.assertIsNone(record["pid"])

    def native_main_prefix(self, filename, matches):
        # Compile the exact main AST, then stop at its first Blender API access.
        # No import of bpy or native process occurs.
        source = REPO / "prototypes/static_tray_v01" / filename
        parsed = ast.parse(source.read_text())
        main = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        module = ast.Module(body=[main], type_ignores=[])
        stage = self.base / (filename + ("-valid" if matches else "-invalid"))
        stage.mkdir()
        job = stage / "job.json"
        job.write_text(json.dumps({"output_directory": str(stage if matches else self.base)}))
        class ReachedNativeBoundary(Exception):
            pass
        class NoBlender:
            @property
            def app(self):
                raise ReachedNativeBoundary("Stopped before any Blender operation")
        namespace = {"Path": Path, "json": json,
                     "sys": types.SimpleNamespace(argv=["fixture", "--", "--job", str(job)]), "bpy": NoBlender()}
        exec(compile(module, str(source), "exec"), namespace)
        with mock.patch.object(Path, "cwd", return_value=stage):
            if matches:
                with self.assertRaises(ReachedNativeBoundary):
                    namespace["main"]()
            else:
                with self.assertRaises(RuntimeError) as caught:
                    namespace["main"]()
                self.assertIn("directory", str(caught.exception).lower())

    def test_actual_worker_cwd_prefix_accepts_same_stage(self):
        self.native_main_prefix("worker.py", True)

    def test_actual_worker_cwd_prefix_rejects_different_stage(self):
        self.native_main_prefix("worker.py", False)

    def test_actual_receiver_cwd_prefix_accepts_same_stage(self):
        self.native_main_prefix("receiver.py", True)

    def test_actual_receiver_cwd_prefix_rejects_different_stage(self):
        self.native_main_prefix("receiver.py", False)

    def test_prepared_jobs_equal_exact_bound_command_paths(self):
        f = self.fixture(transaction=True)
        prepared = f.prepare("A01")
        construction = f.inputs.lock["commands"]["A01"]["construction"]
        job = json.loads(Path(construction["argv"][-1]).read_bytes())
        self.assertEqual(job["output_directory"], construction["cwd"])
        self.assertEqual(job["record_path"], str(Path(construction["cwd"]) / "canonical-input.json"))
        constructed = f.construct(prepared)
        receiving = f.inputs.lock["commands"]["A01"]["receiving"]
        job = json.loads(Path(receiving["argv"][-1]).read_bytes())
        self.assertEqual(job["output_directory"], receiving["cwd"])
        self.assertNotEqual(construction["cwd"], receiving["cwd"])
        self.assertEqual(job["candidate"], str(Path(f.inputs.lock["stores"]["A01"]) / "objects/A01"))

    def test_changed_construction_job_output_rejected(self):
        f = self.fixture(transaction=True)
        p = f.prepare("A01")
        stage = f.build(p)
        path = stage / "job.json"
        job = json.loads(path.read_bytes())
        job["output_directory"] = str(f.inputs.repo)
        path.write_bytes(canonical(job))
        self.transaction_reject(lambda: tx.seal_construction(p, process=f.process("A01", "construction")), "RECEIPT")
        self.assertIsNone(self.pointer(f))

    def test_changed_receiving_job_output_rejected(self):
        f = self.fixture(transaction=True)
        c = f.construct(f.prepare("A01"))
        stage = f.receive(c)
        path = stage / "job.json"
        job = json.loads(path.read_bytes())
        job["output_directory"] = str(f.inputs.repo)
        path.write_bytes(canonical(job))
        self.transaction_reject(lambda: tx.complete_transaction(c, process=f.process("A01", "receiving")), "RECEIPT")
        self.assertIsNone(self.pointer(f))

    def test_outer_construction_cwd_mismatch_rejected(self):
        f = self.fixture(transaction=True)
        p = f.prepare("A01")
        f.build(p)
        process = f.process("A01", "construction")
        process["command"]["cwd"] = str(f.inputs.repo)
        self.transaction_reject(lambda: tx.seal_construction(p, process=process), "PROCESS")
        self.assertIsNone(self.pointer(f))

    def test_outer_receiving_cwd_mismatch_rejected(self):
        f = self.fixture(transaction=True)
        c = f.construct(f.prepare("A01"))
        f.receive(c)
        process = f.process("A01", "receiving")
        process["command"]["cwd"] = str(f.inputs.repo)
        self.transaction_reject(lambda: tx.complete_transaction(c, process=process), "PROCESS")
        self.assertIsNone(self.pointer(f))

    def test_underlying_construction_cwd_mismatch_rejected(self):
        f = self.fixture(transaction=True)
        p = f.prepare("A01")
        stage = f.build(p)
        path = stage / "construction.process.json"
        record = json.loads(path.read_bytes())
        record["cwd"] = str(f.inputs.repo)
        path.write_bytes(canonical(record))
        self.transaction_reject(lambda: tx.seal_construction(p, process=f.process("A01", "construction")), "PROCESS")
        self.assertIsNone(self.pointer(f))

    def test_underlying_receiving_cwd_mismatch_rejected(self):
        f = self.fixture(transaction=True)
        c = f.construct(f.prepare("A01"))
        stage = f.receive(c)
        path = stage / "receiving.process.json"
        record = json.loads(path.read_bytes())
        record["cwd"] = str(f.inputs.repo)
        path.write_bytes(canonical(record))
        self.transaction_reject(lambda: tx.complete_transaction(c, process=f.process("A01", "receiving")), "PROCESS")
        self.assertIsNone(self.pointer(f))

    def test_failed_receiving_keeps_prior_accepted_baseline_exact(self):
        f = self.fixture(transaction=True)
        handle = f.accept("A01")
        before = self.pointer(f)
        c = f.construct(f.prepare("A02"))
        f.receive(c)
        process = f.process("A02", "receiving")
        process["cleanup"]["reaped"] = False
        self.transaction_reject(lambda: tx.complete_transaction(c, process=process), "CLEANUP")
        self.assertEqual(self.pointer(f), before)
        self.assertIsNone(self.pointer(f, "A02"))
        self.assertEqual(tx.inspect_accepted(f.session, handle)["slot"], "A01")

    def test_exact_four_transactions_and_accepted_source_reuse(self):
        f = self.fixture(transaction=True)
        handles = [f.accept(slot.name) for slot in SLOTS]
        for h in handles:
            receipt = tx.inspect_accepted(f.session, h)
            self.assertEqual(receipt["state"], "TRANSACTION_ACCEPTED")
            self.assertFalse(receipt["native_readiness"])
            self.assertFalse(receipt["admission_completed"])
            self.assertFalse(h.native_start_authorized)
        for later, baseline in (("A03", "A01"), ("A04", "A02")):
            store = Path(f.inputs.lock["stores"][later]) / "objects" / later
            prior = Path(f.inputs.lock["stores"][baseline]) / "objects" / baseline
            provenance = json.loads((store / "source-provenance.json").read_bytes())
            self.assertEqual(provenance["source_path"], str(prior / "source"))
            for name in ("canonical-input.json", "raw.glb", "final.glb"):
                self.assertEqual((store / name).read_bytes(), (prior / name).read_bytes())

    def test_changed_accepted_source_rejected_without_pointer_mutation(self):
        f = self.fixture(transaction=True)
        handle = f.accept("A01")
        before = self.pointer(f)
        source = Path(f.inputs.lock["stores"]["A01"]) / "objects/A01/source/tray.ok"
        source.chmod(0o600)
        source.write_bytes(source.read_bytes() + b"\n")
        source.chmod(0o444)
        with self.assertRaises(tx.TransactionError):
            tx.inspect_accepted(f.session, handle)
        self.assertEqual(self.pointer(f), before)

    def test_failed_precommit_preserves_absent_pointer(self):
        f = self.fixture(transaction=True)
        c = f.construct(f.prepare("A01"))
        f.receive(c)
        original = tx.os.replace
        commit_calls = []
        def fail_pointer_only(*a, **kw):
            if len(a) > 1 and a[1] == "state.json":
                commit_calls.append(a)
                raise OSError("Synthetic precommit pointer failure")
            return original(*a, **kw)
        with mock.patch.object(tx.os, "replace", side_effect=fail_pointer_only):
            self.transaction_reject(lambda: tx.complete_transaction(c, process=f.process("A01", "receiving")), "BINDING")
        self.assertEqual(len(commit_calls), 1)
        self.assertIsNone(self.pointer(f))
        self.transaction_reject(lambda: tx.complete_transaction(c, process=f.process("A01", "receiving")), "REPLAY")

    def test_committed_replace_then_interruption_remains_unknown(self):
        f = self.fixture(transaction=True)
        c = f.construct(f.prepare("A01"))
        f.receive(c)
        original = tx.os.replace
        def interrupted(*a, **kw):
            original(*a, **kw)
            raise KeyboardInterrupt("Synthetic interruption after actual pointer replacement")
        with mock.patch.object(tx.os, "replace", side_effect=interrupted):
            self.transaction_reject(lambda: tx.complete_transaction(c, process=f.process("A01", "receiving")), "PROMOTION", "UNKNOWN")
        self.assertIsNotNone(self.pointer(f))
        self.transaction_reject(lambda: tx.complete_transaction(c, process=f.process("A01", "receiving")), "REPLAY")

    def test_synthetic_production_shaped_bindings_pass_without_readiness(self):
        f = self.fixture()
        f.context = replace(f.context, purpose="production-inputs")
        f.lock["purpose"] = "production-inputs"
        f.lock["host"]["mode"] = "current-host"
        for gate in lock_module.GATES:
            path = f.host / (gate + ".json")
            value = json.loads(path.read_bytes())
            value["purpose"] = "production-inputs"
            path.write_bytes(canonical(value))
            f.lock["gate_receipts"][gate] = f.binding(path, "host")
        f.repin()
        f.approval["purpose"] = "production-inputs"
        f.approval["decision"] = "APPROVE_INPUT_BINDINGS_ONLY"
        f.save_approval()
        session = tx.bind_transactions(f.lock_path, f.approval_path, context=f.context)
        self.assertEqual(session.validation.purpose, "production-inputs")
        self.assertFalse(session.validation.native_start_authorized)
        self.assertFalse(session.validation.native_readiness)
        self.assertFalse(session.validation.admission_completed)
        prepared = tx.prepare_transaction(session, "A01", route=SLOTS[0].route, references=SLOTS[0].references())
        self.assertEqual(prepared.slot, "A01")
        self.assertFalse((Path(f.lock["stores"]["A01"]) / "state.json").exists())
        DETAILS.append({"control": self.id(), "classification": "Synthetic fixture carrying production-shaped strings; no real host or approval", "nativeStarts": 0})


def git(*arguments):
    result = subprocess.run(["git", "--no-optional-locks", "-C", str(REPO), *arguments], capture_output=True, text=True, check=True)
    return result.stdout.strip()


head, tree, status = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"), git("status", "--porcelain=v1")
files = ["prototypes/static_tray_admission_c201/input_lock.py", "prototypes/static_tray_admission_c201/transaction.py",
         "tests/test_static_tray_admission_c201_input_lock.py", "tests/test_static_tray_admission_c201_transaction.py",
         "tests/test_static_tray_reader_v01.py", "tests/test_static_tray_receiving_v01.py"]
files += [p.relative_to(REPO).as_posix() for p in (REPO / "prototypes/static_tray_admission_c201").glob("*.py")]
protocol = json.loads((REPO / lock_module.PROTOCOL_PATH).read_bytes())
review = json.loads((REPO / lock_module.PROTOCOL_REVIEW_PATH).read_bytes())
files += [r["path"] for r in protocol["qualified_role_bindings"].values()]
files += [r["path"] for r in review["documentBindings"]]
files += [lock_module.PROTOCOL_REVIEW_PATH]
files += git("diff", "--name-only", "2a1ac8ccbdc290942e88504c640790b1bda9229c", "HEAD").splitlines()
bindings = [{"path": name, "sizeBytes": (REPO / name).stat().st_size, "sha256": sha((REPO / name).read_bytes())}
            for name in sorted(set(files))]
(OUT / "SOURCE-BINDINGS.json").write_text(json.dumps({"head": head, "tree": tree, "status": status, "files": bindings}, indent=2) + "\n")

stream = io.StringIO()
suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReviewControls)
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
(OUT / "controls.log").write_text(stream.getvalue())
record = {"schema": "ontokin.c207.independent-cwd-controls/0.1", "observedAtUtc": datetime.now(timezone.utc).isoformat(),
          "repository": str(REPO), "head": head, "tree": tree, "workingTreeStatus": status,
          "python": sys.version, "platform": platform.platform(), "testsRun": result.testsRun,
          "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
          "passed": result.wasSuccessful() and not UNEXPECTED_CHILD_CALLS,
          "unexpectedProductChildCalls": UNEXPECTED_CHILD_CALLS,
          "interceptedSupervisorCalls": INTERCEPTED_SUPERVISOR_CALLS,
          "actualNativeStarts": 0, "actualReceivingStarts": 0, "actualNodeStarts": 0,
          "lifecycleStarts": 0, "timedAuthors": 0, "details": DETAILS,
          "limits": ["CPU fixtures only", "No true process provenance, host seal, readiness or admission", "Node plan consistency only; no C201 readback implementation"]}
(OUT / "RESULT.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({k: record[k] for k in ("head", "testsRun", "failures", "errors", "skips", "passed")}))
raise SystemExit(0 if record["passed"] else 1)
