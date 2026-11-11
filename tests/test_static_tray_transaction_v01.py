"""CPU-only transaction seams. No Blender or controlled child is launched.

Mocked artifact bytes cannot establish geometry qualification. These tests check
the real ledger, sealing, clock, predecessor and promotion behavior around the
separately qualified supervisor and independently qualified reader.
"""
from __future__ import annotations

from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from prototypes.static_tray_v01.canonical import ROOT, json_bytes
from prototypes.static_tray_v01.errors import PROFILE
from prototypes.static_tray_v01.lock import _environment, _host_bindings, check_file, reject_repository_bytecode, NATIVE_FLAGS
from prototypes.static_tray_v01.qualification import run_qualification, verify_delivered_predecessors
from prototypes.static_tray_v01.sources import lower_source
from prototypes.static_tray_v01.store import read_state, verify_candidate
from prototypes.static_tray_v01.supervisor import Clock, Stop, sha256_file
from prototypes.static_tray_v01 import transaction as tx


class TransactionSeamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="static-tray-cpu-transaction-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.schedule = self.root / "schedule"
        source = ROOT / "fixtures/static_tray_v01/native/Q01/ontokin/source.json"
        self.lowered = lower_source("ontokin", source, PROFILE)
        self.row = {"slot": "N01", "case": "Q01", "route": "ontokin", "purpose": "baseline",
                    "source_manifest": str(source), "source_manifest_sha256": sha256_file(source),
                    "source_manifest_size_bytes": source.stat().st_size,
                    "source_identity": self.lowered.provenance["candidate_identity"],
                    "canonical_sha256": hashlib.sha256(self.lowered.canonical_bytes).hexdigest(),
                    "source_files": {n: {"sha256": hashlib.sha256(v).hexdigest(), "size_bytes": len(v)} for n, v in self.lowered.files.items()},
                    "expected_predecessor": None, "candidate_revision": "test-revision-N01",
                    "store": str(self.schedule / "stores/ontokin"), "stage": str(self.schedule / "stages/N01-build"),
                    "receiver_stage": str(self.schedule / "stages/N01-receive"), "result": str(self.schedule / "results/N01.json"),
                    "environment": _environment(self.schedule, "N01"), "command": ["mock-host-command"],
                    "native_argv": ["mock-construction"], "receiver_argv": ["mock-receiver"]}
        self.lock = {"schedule_root": str(self.schedule), "slots": [self.row], "implementation": {"commit": "seam-only", "tree": "seam-only"},
                     "host": {"python": "mock-host", "platform": "linux-x86_64"}, "independent_reader": {"files": {}, "delivery_rules": {}},
                     "delivered_controls": []}
        self.lock_path = self.root / "lock.json"
        self.lock_path.write_bytes(json_bytes(self.lock))
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.verify = self.stack.enter_context(patch.object(tx, "verify_lock", return_value=(self.lock, "locked-input-hash")))
        self.reader = SimpleNamespace(audit=lambda *a: {"passed": True, "nodes": {}, "findings": []})
        self.stack.enter_context(patch.object(tx, "independent_modules", return_value={"reader": self.reader, "expected": SimpleNamespace(expected_bounds=lambda case: [[-1, -1, -1], [1, 1, 1]])}))
        self.stack.enter_context(patch.object(tx, "compare", return_value={"passed": True, "findings": []}))
        self.process = self.stack.enter_context(patch.object(tx, "run_process", side_effect=self.fake_process))
        self.launches = []

    def fake_process(self, argv, *, stage, label, clock, stage_end, env, on_started):
        self.launches.append(label)
        process = {"argv": argv, "process_group": 123456, "start_monotonic": time.monotonic(),
                   "handles_closed": True, "cleanup": {"passed": True}, "exit_code": 0}
        on_started(process)
        job = json.loads((Path(stage) / "job.json").read_bytes())
        if label == "construction":
            for name, data in {"raw.glb": b"MOCK GLB CPU SEAM", "final.glb": b"MOCK GLB CPU SEAM", "scene.blend": b"MOCK NATIVE SCENE CPU SEAM"}.items():
                (Path(stage) / name).write_bytes(data)
            artifacts = {name: {"sha256": sha256_file(Path(stage) / name), "size_bytes": (Path(stage) / name).stat().st_size} for name in ("raw.glb", "final.glb", "scene.blend")}
            (Path(stage) / "native-result.json").write_bytes(json_bytes({"passed": True, "record_sha256": job["record_sha256"], "artifacts": artifacts}))
        else:
            self.assertIsNone(read_state(self.row["store"]))
            self.assertEqual(tx.read_ledger(self.schedule)[-2]["state"], "BUILT_PENDING_RECEIVING")
            verify_candidate(job["candidate"])
            (Path(stage) / "observations.json").write_bytes(json_bytes({"input_sha256": job["input_sha256"]}))
            (Path(stage) / "review.png").write_bytes(b"MOCK IMAGE CPU SEAM")
        return process

    def run_one(self):
        return tx.run_transaction(self.lock_path, "N01", route="ontokin", source=self.row["source_manifest"],
                                  store=self.row["store"], result_path=self.row["result"])

    def test_sealed_pending_receiver_then_single_cas(self):
        result = self.run_one()
        self.assertEqual(result["state"], "ACCEPTED", result.get("error"))
        self.assertEqual(self.launches, ["construction", "receiving"])
        self.assertEqual([r["state"] for r in tx.read_ledger(self.schedule)], ["RESERVED", "STARTED", "BUILT_PENDING_RECEIVING", "RECEIVING", "ACCEPTED"])
        self.assertEqual(read_state(self.row["store"])["revision"], self.row["candidate_revision"])
        self.assertEqual((Path(result["candidate"]) / "canonical-input.json").read_bytes(), self.lowered.canonical_bytes)
        for name, data in self.lowered.files.items():
            self.assertEqual((Path(result["candidate"]) / "source" / name).read_bytes(), data)
        verify_candidate(result["candidate"])
        verify_candidate(result["receiving_candidate"])
        self.assertTrue(self.verify.call_args.kwargs["runtime"])

    def test_missing_approval_cannot_launch_or_reserve(self):
        self.verify.side_effect = Stop("OTRAY-E-BINDING", "Exact approval absent")
        result = self.run_one()
        self.assertEqual(result["state"], "REJECTED")
        self.assertEqual(result["native_starts"], 0)
        self.process.assert_not_called()
        self.assertEqual(tx.read_ledger(self.schedule), [])

    def test_locked_command_mismatch_cannot_launch(self):
        result = tx.run_transaction(self.lock_path, "N01", route="direct-python")
        self.assertEqual(result["error"]["code"], "OTRAY-E-BINDING")
        self.process.assert_not_called()
        self.assertEqual(tx.read_ledger(self.schedule), [])

    def test_failed_child_consumes_slot_without_retry(self):
        def fail(*args, **kwargs):
            process = {"process_group": 123456, "start_monotonic": time.monotonic(), "handles_closed": True, "cleanup": {"passed": True}}
            kwargs["on_started"](process)
            error = Stop("OTRAY-E-BACKEND", "Controlled in-process start seam failure")
            error.process_record = process
            raise error
        self.process.side_effect = fail
        first = self.run_one()
        self.assertEqual(first["state"], "REJECTED")
        self.assertEqual(first["native_starts"], 1)
        original = Path(self.row["result"]).read_bytes()
        second = self.run_one()
        self.assertEqual(second["native_starts"], 0)
        self.assertEqual(self.process.call_count, 1)
        self.assertEqual(Path(self.row["result"]).read_bytes(), original)
        self.assertEqual([r["state"] for r in tx.read_ledger(self.schedule)], ["RESERVED", "STARTED", "REJECTED"])

    def test_receiving_failure_preserves_predecessor(self):
        with patch.object(tx, "compare", return_value={"passed": False, "findings": [{"code": "RECEIVING"}]}):
            result = self.run_one()
        self.assertEqual(result["state"], "REJECTED")
        self.assertEqual(result["native_starts"], 1)
        self.assertEqual(result["receiving_starts"], 1)
        self.assertIsNone(read_state(self.row["store"]))
        verify_candidate(result["candidate"])

    def test_unverified_cleanup_blocks_promotion(self):
        def not_clean(*args, **kwargs):
            record = self.fake_process(*args, **kwargs)
            if kwargs["label"] == "receiving":
                record["cleanup"]["passed"] = False
            return record
        self.process.side_effect = not_clean
        result = self.run_one()
        self.assertEqual(result["state"], "REJECTED")
        self.assertEqual(result["error"]["code"], "OTRAY-E-BACKEND")
        self.assertIsNone(read_state(self.row["store"]))

    def test_stale_predecessor_rejected_before_any_child(self):
        store = Path(self.row["store"])
        store.mkdir(parents=True)
        original = json_bytes({"revision": "another-writer"})
        (store / "state.json").write_bytes(original)
        result = self.run_one()
        self.assertEqual(result["error"]["code"], "OTRAY-E-STALE")
        self.process.assert_not_called()
        self.assertEqual((store / "state.json").read_bytes(), original)

    def test_lock_verification_time_is_charged_to_original_clock(self):
        clocks = []
        def checked_lock(*a, **kw):
            clocks.append(kw["check"].__closure__)
            raise Stop("OTRAY-E-RESOURCE", "Input verification consumed construction deadline", "TIMEOUT")
        self.verify.side_effect = checked_lock
        result = self.run_one()
        self.assertEqual(result["state"], "TIMEOUT")
        self.assertEqual(result["requested_limits"]["transaction_ms"], 65000)
        self.assertEqual(result["effective_limits"]["construction_ms"], 30000)
        self.assertTrue(clocks)
        self.process.assert_not_called()

    def test_read_only_reconciliation_does_not_retry_uncertain_promotion(self):
        def unknown(store, *, expected, state, clock, cleanup_records):
            (Path(store) / "state.json").write_bytes(json_bytes(state))
            error = Stop("OTRAY-E-BINDING", "Mocked lost reply after replacement", "UNKNOWN")
            error.intended_state = state
            error.observed_state = state
            raise error
        with patch.object(tx, "promote", side_effect=unknown) as promotion:
            result = self.run_one()
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(promotion.call_count, 1)
        self.assertEqual(result["observed_state_after_failure"], result["intended_state_after_unknown"])
        self.assertEqual(result["promotion_readback"], result["intended_state_after_unknown"])


class InputAndScheduleTests(unittest.TestCase):
    def test_native_startup_uses_only_explicit_safe_python_environment(self):
        self.assertEqual(NATIVE_FLAGS.count("--python-use-system-env"), 1)
        environment = _environment(Path("/locked/schedule"), "N01")
        self.assertEqual({k: environment[k] for k in ("PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "PYTHONSAFEPATH")},
                         {"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0", "PYTHONSAFEPATH": "1"})
        self.assertNotIn("PYTHONPATH", environment)
        self.assertNotIn("PYTHONHOME", environment)
        self.assertEqual(environment["BLENDER_USER_SCRIPTS"], "/locked/schedule/environment/N01/blender-scripts")

    def test_source_only_bootstrap_rejects_parent_initializer_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / "prototypes/__pycache__"
            cache.mkdir(parents=True)
            unrelated = cache / "unrelated.cpython-312.pyc"
            unrelated.write_bytes(b"unrelated prototype")
            reject_repository_bytecode(temp)
            (cache / "__init__.cpython-312.pyc").write_bytes(b"unbound parent initializer")
            with self.assertRaisesRegex(Stop, "Parent prototypes initializer"):
                reject_repository_bytecode(temp)

    def test_host_aliases_deduplicate_content_without_omitting_aliases(self):
        common = {"resolved_path": "/runtime/library", "sha256": "a" * 64, "bytes": 7, "mode": "0o644"}
        files, aliases = _host_bindings({"files": [dict(common, path="/runtime/library", symlink=False, link_target=None),
                                                  dict(common, path="/runtime/alias", symlink=True, link_target="library")]})
        self.assertEqual(len(files), 1)
        self.assertEqual(len(aliases), 2)
        self.assertEqual(aliases["/runtime/alias"]["link_target"], "library")

    def test_mutated_file_rejected_by_actual_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input"
            path.write_bytes(b"abc")
            binding = {"sha256": sha256_file(path), "size_bytes": 3}
            check_file(path, binding)
            path.write_bytes(b"abd")
            with self.assertRaisesRegex(Stop, "bytes differ"):
                check_file(path, binding)

    def test_individual_slot_cannot_skip_failed_delivered_control(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "result.json").write_bytes(json_bytes({"case": "D01", "variant": "copy", "passed": False}))
            lock = {"delivered_controls": [{"case": "D01", "variant": "copy", "after_slot": "N01", "directory": str(root)}]}
            verify_delivered_predecessors(lock, "N01")
            with self.assertRaises(Stop):
                verify_delivered_predecessors(lock, "N02")

    def test_qualification_stops_at_first_unexpected_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "new"
            rows = [{"slot": "N%02d" % i, "case": "Q01", "route": "ontokin", "source_manifest": "source", "store": "store", "result": "result"} for i in range(1, 13)]
            lock = {"schedule_root": str(root), "slots": rows, "implementation": {}, "delivered_controls": []}
            failed = {"slot": "N01", "case": "Q01", "route": "ontokin", "state": "REJECTED", "native_starts": 1, "receiving_starts": 0}
            with patch("prototypes.static_tray_v01.qualification.verify_lock", return_value=(lock, "hash")), patch("prototypes.static_tray_v01.qualification.run_transaction", return_value=failed) as transaction:
                report = run_qualification("lock")
            self.assertEqual(transaction.call_count, 1)
            self.assertEqual(report["native_starts"], 1)
            self.assertFalse(report["qualified"])
            self.assertFalse(report["measured_gates_passed"])
            self.assertEqual(report["stopped_at"], {"kind": "transaction", "slot": "N01"})

    def test_qualification_stops_after_overdue_accepted_return(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "new"
            row = {"slot": "N01", "case": "Q01", "route": "ontokin", "source_manifest": "source", "store": "store", "result": "result"}
            lock = {"schedule_root": str(root), "slots": [row], "implementation": {}, "delivered_controls": []}
            overdue = {"slot": "N01", "state": "ACCEPTED", "native_starts": 1, "receiving_starts": 1, "elapsed_ms": 65001}
            with patch("prototypes.static_tray_v01.qualification.verify_lock", return_value=(lock, "hash")), \
                    patch("prototypes.static_tray_v01.qualification.run_transaction", return_value=overdue), \
                    patch("prototypes.static_tray_v01.format_check.run_check") as checker:
                report = run_qualification("lock")
            checker.assert_not_called()
            self.assertFalse(report["measured_gates_passed"])
            self.assertEqual(report["stopped_at"], {"kind": "transaction", "slot": "N01"})


if __name__ == "__main__":
    unittest.main()
