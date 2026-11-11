"""No-child controls for independently found finalization/alarm defects."""
from copy import deepcopy
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch

from tests import test_static_tray_transaction_v01 as seams
from prototypes.static_tray_v01 import transaction as tx
from prototypes.static_tray_v01.canonical import json_bytes
from prototypes.static_tray_v01.supervisor import Clock, Stop, sha256_file
from prototypes.static_tray_v01.errors import TrayError


class FinalizationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = seams.TransactionSeamTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def next_row(self):
        row = deepcopy(self.fixture.row)
        row["slot"] = "N02"
        self.fixture.lock["slots"].append(row)
        return row

    def test_result_write_failure_blocks_later_slot_and_keeps_pointer_for_reconciliation(self):
        original = tx.write_new
        def fail_result(path, value, **kwargs):
            if Path(path) == Path(self.fixture.row["result"]):
                raise OSError("controlled final receipt write failure")
            return original(path, value, **kwargs)
        with patch.object(tx, "write_new", side_effect=fail_result):
            result = self.fixture.run_one()
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(tx.read_state(self.fixture.row["store"])["revision"], self.fixture.row["candidate_revision"])
        self.assertNotIn("ACCEPTED", [x["state"] for x in tx.read_ledger(self.fixture.schedule)])
        self.assertTrue((self.fixture.schedule / "N01.finalization-pending.json").is_file())
        with self.assertRaises(Stop):
            tx.check_order(self.fixture.lock, self.next_row(), "locked-input-hash")
        self.assertEqual(self.fixture.launches, ["construction", "receiving"])

    def test_durable_result_and_both_closures_are_required_before_next_slot(self):
        result = self.fixture.run_one()
        self.assertEqual(result["state"], "ACCEPTED")
        row = self.next_row()
        tx.check_order(self.fixture.lock, row, "locked-input-hash")
        terminal = tx.read_ledger(self.fixture.schedule)[-1]
        self.assertEqual(terminal["result_sha256"], sha256_file(self.fixture.row["result"]))
        Path(self.fixture.row["result"]).unlink()
        with self.assertRaisesRegex(Stop, "durable prior result"):
            tx.check_order(self.fixture.lock, row, "locked-input-hash")

    def test_changed_current_pointer_stops_after_valid_prior_receipt(self):
        self.assertEqual(self.fixture.run_one()["state"], "ACCEPTED")
        (Path(self.fixture.row["store"]) / "state.json").write_bytes(json_bytes({"revision":"different"}))
        with self.assertRaisesRegex(Stop, "pointer requires reconciliation"):
            tx.check_order(self.fixture.lock, self.next_row(), "locked-input-hash")

    def test_result_persistence_is_charged_to_original_deadline(self):
        written = False
        original = tx.write_new
        class FinalWriteClock(Clock):
            def check(self, *args, **kwargs):
                if written:
                    raise Stop("OTRAY-E-RESOURCE", "controlled elapsed outer deadline", "TIMEOUT")
                return super().check(*args, **kwargs)
        def write(path, value, **kwargs):
            nonlocal written
            result = original(path, value, **kwargs)
            if Path(path) == Path(self.fixture.row["result"]):
                written = True
            return result
        with patch.object(tx, "Clock", FinalWriteClock), patch.object(tx, "write_new", side_effect=write):
            result = self.fixture.run_one()
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertIn("elapsed_before_finalization_ms", result)
        self.assertGreaterEqual(result["elapsed_ms"], result["elapsed_before_finalization_ms"])
        self.assertTrue((self.fixture.schedule / "N01.finalization-pending.json").is_file())
        with self.assertRaises(Stop):
            tx.check_order(self.fixture.lock, self.next_row(), "locked-input-hash")

    def test_host_alarm_is_off_while_supervisor_owns_cleanup(self):
        original = self.fixture.fake_process
        def process(*args, **kwargs):
            self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
            return original(*args, **kwargs)
        self.fixture.process.side_effect = process
        self.assertEqual(self.fixture.run_one()["state"], "ACCEPTED")
        self.assertEqual(self.fixture.launches, ["construction", "receiving"])

    def test_alarm_restores_only_unspent_absolute_time(self):
        with patch.object(tx.signal, "setitimer", return_value=(.2, 0)) as timer, \
                patch.object(tx.time, "monotonic", side_effect=[10, 10.125]):
            with tx.supervised_process_clock():
                pass
        self.assertEqual(timer.call_count, 2)
        self.assertAlmostEqual(timer.call_args.args[1], .075)

    def test_expired_alarm_cannot_interrupt_returning_cleanup_receipt(self):
        with patch.object(tx.signal, "setitimer", return_value=(.05, 0)) as timer, \
                patch.object(tx.time, "monotonic", side_effect=[10, 10.6]):
            with self.assertRaisesRegex(Stop, "supervisor original"):
                with tx.supervised_process_clock():
                    raise Stop("OTRAY-E-RESOURCE", "supervisor original timeout", "TIMEOUT")
        self.assertEqual(timer.call_count, 1)


class LockedManifestTests(unittest.TestCase):
    def test_manifest_staging_preserves_only_exact_bounded_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            original = b'{"preserved": true}\n'
            path.write_bytes(original)
            row = {"source_manifest":str(path),"source_manifest_sha256":sha256_file(path),
                   "source_manifest_size_bytes":len(original)}
            self.assertEqual(tx.read_locked_manifest(row), original)
            path.write_bytes(b'{"preserved":false}\n')
            with self.assertRaisesRegex(Stop, "locked size/hash"):
                tx.read_locked_manifest(row)
            path.write_bytes(b" " * 32769)
            with self.assertRaises(TrayError) as failure:
                tx.read_locked_manifest(row)
            self.assertEqual(failure.exception.code, "OTRAY-E-RESOURCE")


if __name__ == "__main__":
    unittest.main()
