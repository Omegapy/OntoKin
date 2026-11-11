"""C207 CPU working-directory controls; no native or Node process is started."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from prototypes.static_tray_admission_c201 import input_lock, transaction
from prototypes.static_tray_admission_c201.schedule import SLOTS, canonical
from tests.test_static_tray_admission_c201_input_lock import Fixture
from tests.test_static_tray_admission_c201_transaction import TransactionFixture


class WorkingDirectoryControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-c207-cpu-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        for target in ("subprocess.Popen", "os.fork", "os.system", "os.posix_spawn", "os.posix_spawnp"):
            self.enterContext(mock.patch(target, side_effect=AssertionError("No child may start")))

    def fixture(self, name):
        root = self.base / name
        root.mkdir()
        return Fixture(root)

    def transaction_fixture(self, name):
        root = self.base / name
        root.mkdir()
        return TransactionFixture(root)

    def repin_plan(self, fixture):
        fixture.context = replace(fixture.context,
                                  launch_plan_sha256=input_lock.launch_plan_digest(fixture.lock))
        fixture.repin()

    def reject_before_writes(self, fixture, code="COMMAND"):
        with self.assertRaises(input_lock.InputLockError) as caught:
            fixture.validate()
        self.assertEqual(caught.exception.code, code)
        for path in (*fixture.lock["stores"].values(), *fixture.lock["environments"].values(),
                     *(p for rows in fixture.lock["outputs"].values() for p in rows.values())):
            self.assertEqual(os.listdir(path), [])

    def test_all_twelve_plans_bind_stage_cwd_output_and_job(self):
        fixture = self.fixture("all-plans")
        result = fixture.validate()
        self.assertFalse(result.native_start_authorized)
        for slot in SLOTS:
            for stage in input_lock.STAGES:
                with self.subTest(slot=slot.name, stage=stage):
                    output = fixture.lock["outputs"][slot.name][stage]
                    command = fixture.lock["commands"][slot.name][stage]
                    self.assertEqual(command["cwd"], output)
                    self.assertEqual(command["output"], output)
                    self.assertEqual(command["argv"][-2:], ["--job", str(Path(output) / "job.json")])
                    self.assertTrue(Path(output).is_absolute())

    def test_repository_cwd_rejected_for_every_slot_stage_even_with_resealed_plan(self):
        for slot in SLOTS:
            for stage in input_lock.STAGES:
                with self.subTest(slot=slot.name, stage=stage):
                    fixture = self.fixture(slot.name + "-" + stage)
                    fixture.lock["commands"][slot.name][stage]["cwd"] = str(fixture.repo)
                    self.repin_plan(fixture)
                    self.reject_before_writes(fixture)

    def test_other_stage_cwd_rejected_even_with_resealed_plan(self):
        for stage in input_lock.STAGES:
            with self.subTest(stage=stage):
                fixture = self.fixture(stage)
                other = next(s for s in input_lock.STAGES if s != stage)
                fixture.lock["commands"]["A01"][stage]["cwd"] = fixture.lock["outputs"]["A01"][other]
                self.repin_plan(fixture)
                self.reject_before_writes(fixture)

    def test_other_slot_cwd_rejected_even_with_resealed_plan(self):
        for stage in input_lock.STAGES:
            with self.subTest(stage=stage):
                fixture = self.fixture(stage)
                fixture.lock["commands"]["A01"][stage]["cwd"] = fixture.lock["outputs"]["A02"][stage]
                self.repin_plan(fixture)
                self.reject_before_writes(fixture)

    def test_noncanonical_cwd_rejected_even_with_resealed_plan(self):
        for index, spelling in enumerate(("relative", "double-slash", "trailing-slash")):
            with self.subTest(spelling=spelling):
                fixture = self.fixture(str(index))
                command = fixture.lock["commands"]["A01"]["construction"]
                command["cwd"] = {"relative": "A01-construction", "double-slash": "/" + command["cwd"],
                                  "trailing-slash": command["cwd"] + "/"}[spelling]
                self.repin_plan(fixture)
                self.reject_before_writes(fixture)

    def test_wrong_command_output_rejected_even_with_resealed_plan(self):
        for stage in input_lock.STAGES:
            with self.subTest(stage=stage):
                fixture = self.fixture(stage)
                fixture.lock["commands"]["A01"][stage]["output"] = fixture.lock["outputs"]["A02"][stage]
                self.repin_plan(fixture)
                self.reject_before_writes(fixture)

    def test_changed_declared_output_rejected_even_with_resealed_plan(self):
        for stage in input_lock.STAGES:
            with self.subTest(stage=stage):
                fixture = self.fixture(stage)
                new = fixture.base / "replacement-output"
                new.mkdir()
                fixture.lock["outputs"]["A01"][stage] = str(new)
                self.repin_plan(fixture)
                self.reject_before_writes(fixture)

    def test_changed_job_argument_rejected_for_each_stage_even_with_resealed_plan(self):
        for stage in input_lock.STAGES:
            with self.subTest(stage=stage):
                fixture = self.fixture(stage)
                fixture.lock["commands"]["A01"][stage]["argv"][-1] = str(fixture.base / "wrong-job.json")
                self.repin_plan(fixture)
                self.reject_before_writes(fixture)

    def test_consistent_path_change_still_requires_independently_reviewed_plan(self):
        fixture = self.fixture("changed-plan")
        new = fixture.base / "replacement-output"
        new.mkdir()
        command = fixture.lock["commands"]["A01"]["construction"]
        command["cwd"] = command["output"] = str(new)
        command["argv"][-1] = str(new / "job.json")
        fixture.lock["outputs"]["A01"]["construction"] = str(new)
        fixture.repin()
        self.reject_before_writes(fixture)

    def test_replaced_stage_directory_rejected_before_source_is_staged(self):
        for stage in input_lock.STAGES:
            with self.subTest(stage=stage):
                fixture = self.transaction_fixture(stage)
                output = Path(fixture.inputs.lock["outputs"]["A01"][stage])
                output.rename(output.with_name(output.name + "-original"))
                output.mkdir()
                with self.assertRaises(transaction.TransactionError) as caught:
                    fixture.prepare("A01")
                self.assertEqual(caught.exception.code, "C201-PATH")
                self.assertEqual(os.listdir(fixture.inputs.lock["stores"]["A01"]), [])
                self.assertEqual(os.listdir(fixture.inputs.lock["outputs"]["A01"]["construction"]), [])

    def test_changed_retained_plan_rejected_before_staging(self):
        for field in ("cwd", "output", "argv"):
            with self.subTest(field=field):
                fixture = self.transaction_fixture(field)
                lock = fixture.session._lock()
                command = lock["commands"]["A01"]["construction"]
                if field == "argv":
                    command[field][-1] = str(fixture.inputs.base / "changed-job.json")
                else:
                    command[field] = str(fixture.inputs.repo)
                fixture.session._lock_bytes = canonical(lock)
                with self.assertRaises(transaction.TransactionError) as caught:
                    fixture.prepare("A01")
                self.assertEqual(caught.exception.code, "C201-BINDING")
                self.assertEqual(os.listdir(fixture.inputs.lock["stores"]["A01"]), [])

    def test_native_jobs_and_process_receipts_share_the_planned_cwd(self):
        fixture = self.transaction_fixture("native-paths")
        prepared = fixture.prepare("A01")
        construction = fixture.build(prepared)
        job = json.loads((construction / "job.json").read_bytes())
        process = fixture.process("A01", "construction")
        underlying = json.loads((construction / "construction.process.json").read_bytes())
        self.assertEqual(job["output_directory"], process["command"]["cwd"])
        self.assertEqual(underlying["cwd"], process["command"]["cwd"])
        constructed = transaction.seal_construction(prepared, process=process)
        receiving = fixture.receive(constructed)
        job = json.loads((receiving / "job.json").read_bytes())
        process = fixture.process("A01", "receiving")
        underlying = json.loads((receiving / "receiving.process.json").read_bytes())
        self.assertEqual(job["output_directory"], process["command"]["cwd"])
        self.assertEqual(underlying["cwd"], process["command"]["cwd"])
        accepted = transaction.complete_transaction(constructed, process=process)
        self.assertFalse(accepted.native_start_authorized)
        self.assertFalse(accepted.native_readiness)

    def test_wrong_construction_job_directory_rejected_without_promotion(self):
        fixture = self.transaction_fixture("construction-job")
        prepared = fixture.prepare("A01")
        directory = fixture.build(prepared)
        job = json.loads((directory / "job.json").read_bytes())
        job["output_directory"] = str(fixture.inputs.repo)
        (directory / "job.json").write_bytes(canonical(job))
        with self.assertRaises(transaction.TransactionError) as caught:
            transaction.seal_construction(prepared, process=fixture.process("A01", "construction"))
        self.assertEqual(caught.exception.code, "C201-RECEIPT")
        self.assertFalse((Path(fixture.inputs.lock["stores"]["A01"]) / "state.json").exists())

    def test_wrong_receiving_job_directory_rejected_without_promotion(self):
        fixture = self.transaction_fixture("receiving-job")
        constructed = fixture.construct(fixture.prepare("A01"))
        directory = fixture.receive(constructed)
        job = json.loads((directory / "job.json").read_bytes())
        job["output_directory"] = str(fixture.inputs.repo)
        (directory / "job.json").write_bytes(canonical(job))
        with self.assertRaises(transaction.TransactionError) as caught:
            transaction.complete_transaction(constructed, process=fixture.process("A01", "receiving"))
        self.assertEqual(caught.exception.code, "C201-RECEIPT")
        self.assertFalse((Path(fixture.inputs.lock["stores"]["A01"]) / "state.json").exists())

    def test_wrong_supervisor_cwd_rejected_for_both_native_stages(self):
        for stage in ("construction", "receiving"):
            with self.subTest(stage=stage):
                fixture = self.transaction_fixture(stage)
                prepared = fixture.prepare("A01")
                if stage == "construction":
                    directory = fixture.build(prepared)
                    finish = lambda process: transaction.seal_construction(prepared, process=process)
                else:
                    constructed = fixture.construct(prepared)
                    directory = fixture.receive(constructed)
                    finish = lambda process: transaction.complete_transaction(constructed, process=process)
                path = directory / (stage + ".process.json")
                record = json.loads(path.read_bytes())
                record["cwd"] = str(fixture.inputs.repo)
                path.write_bytes(canonical(record))
                with self.assertRaises(transaction.TransactionError) as caught:
                    finish(fixture.process("A01", stage))
                self.assertEqual(caught.exception.code, "C201-PROCESS")
                self.assertFalse((Path(fixture.inputs.lock["stores"]["A01"]) / "state.json").exists())

    def test_wrong_observed_command_cwd_rejected_for_both_native_stages(self):
        for stage in ("construction", "receiving"):
            with self.subTest(stage=stage):
                fixture = self.transaction_fixture(stage)
                prepared = fixture.prepare("A01")
                if stage == "construction":
                    fixture.build(prepared)
                    finish = lambda process: transaction.seal_construction(prepared, process=process)
                else:
                    constructed = fixture.construct(prepared)
                    fixture.receive(constructed)
                    finish = lambda process: transaction.complete_transaction(constructed, process=process)
                process = deepcopy(fixture.process("A01", stage))
                process["command"]["cwd"] = str(fixture.inputs.repo)
                with self.assertRaises(transaction.TransactionError) as caught:
                    finish(process)
                self.assertEqual(caught.exception.code, "C201-PROCESS")
                self.assertFalse((Path(fixture.inputs.lock["stores"]["A01"]) / "state.json").exists())


if __name__ == "__main__":
    unittest.main()
