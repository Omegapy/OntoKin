"""CPU filesystem controls; no native or lifecycle child is ever started."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

from prototypes.static_tray_admission_c201 import ledger as module
from prototypes.static_tray_admission_c201.ledger import JOURNAL, MARKER, Ledger, Reservation, inspect
from prototypes.static_tray_admission_c201.schedule import (
    LedgerError, ORDER, PROTOCOL_SHA256, SCHEDULE_SHA256, SLOTS,
    expected_schedule, read_protocol, validate_schedule,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/engineering/static-tray-admission-c201/ADMISSION.json"
EVIDENCE = hashlib.sha256(b"CPU-only synthetic observation, not native evidence").hexdigest()
BY_NAME = {slot.name: slot for slot in SLOTS}


class LedgerControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-c201-cpu-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.counter = 0
        for target in ("subprocess.Popen", "os.fork", "os.system"):
            self.enterContext(mock.patch(target, side_effect=AssertionError("A child start is forbidden")))

    def directories(self):
        self.counter += 1
        root = self.root / str(self.counter)
        root.mkdir()
        authority, output = root / "authority", root / "output"
        authority.mkdir(mode=0o700)
        output.mkdir()
        return authority, output

    def begin(self):
        authority, output = self.directories()
        return Ledger.begin(authority, output, expected_schedule()), authority, output

    def reserve(self, ledger, slot="A01", stage="construction", **overrides):
        row = BY_NAME[slot]
        args = {"references": row.references(), **overrides}
        return ledger.reserve(slot, row.route, stage, **args)

    def finish(self, ledger, receipt, **overrides):
        args = {"outcome": "passed", "cleanup_passed": True, "evidence_sha256": EVIDENCE,
                **overrides}
        ledger.finish(receipt, **args)

    def promotion(self, ledger, slot="A01", **overrides):
        row = BY_NAME[slot]
        args = {"references": row.references(), "outcome": "passed", "cleanup_passed": True,
                "conditional_promotion_passed": True, "evidence_sha256": EVIDENCE, **overrides}
        ledger.record_promotion(slot, row.route, **args)

    def complete_slot(self, ledger, slot="A01"):
        for stage in ("construction", "receiving"):
            self.finish(ledger, self.reserve(ledger, slot, stage))
        self.promotion(ledger, slot)
        self.finish(ledger, self.reserve(ledger, slot, "node"))

    def control(self, ledger, control="D01", **overrides):
        args = {"source_slot": "A01", "outcome": "passed",
                "findings": [{"D01": "CLEARANCE", "D03": "SIBLING"}[control]],
                "accepted_closure_unchanged": True, "evidence_sha256": EVIDENCE, **overrides}
        ledger.record_control(control, **args)

    def stopped(self, ledger):
        self.assertTrue(ledger.snapshot()["stopped"])
        with self.assertRaises(LedgerError):
            self.reserve(ledger)

    def test_exact_approved_protocol_and_fixed_schedule(self):
        self.assertEqual(read_protocol(PROTOCOL), expected_schedule())
        self.assertEqual(hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(), PROTOCOL_SHA256)
        self.assertEqual(validate_schedule(expected_schedule()), SCHEDULE_SHA256)

    def test_rejects_malformed_or_changed_schedule_before_invocation(self):
        changes = [
            lambda d: d["slots"].pop(),
            lambda d: d["slots"].append(copy.deepcopy(d["slots"][0])),
            lambda d: d["slots"].reverse(),
            lambda d: d["slots"].__setitem__(1, copy.deepcopy(d["slots"][0])),
            lambda d: d["slots"][0].__setitem__("route", "direct-python"),
            lambda d: d["slots"][0].__setitem__("maximum_native_starts", True),
            lambda d: d["slots"][0].__setitem__("maximum_native_starts", 1.0),
            lambda d: d["slots"][2].__setitem__("accepted_source_reference", "A02"),
            lambda d: d["slots"][3].__setitem__("equality_references", ["A03", "A02"]),
            lambda d: d["slots"][1].__setitem__("required_completed_controls", ["D03", "D01"]),
            lambda d: d["ceilings"].__setitem__("native_starts", 12),
            lambda d: d["ceilings"].__setitem__("automatic_retries", 1),
            lambda d: d.__setitem__("current_executable_invocation", "run.py"),
            lambda d: d.__setitem__("one_use_invocation_required", 1),
            lambda d: d.__setitem__("order", tuple(ORDER)),
            lambda d: d.__setitem__("schedule_id", "C200"),
            lambda d: d.__setitem__("extra", True),
        ]
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                authority, output = self.directories()
                plan = expected_schedule()
                change(plan)
                with self.assertRaises(LedgerError):
                    Ledger.begin(authority, output, plan)
                self.assertEqual(list(authority.iterdir()), [])

    def test_rejects_historical_twelve_slot_schedule(self):
        plan = expected_schedule()
        plan["slots"] = [{"slot": "N%02d" % i} for i in range(1, 13)]
        with self.assertRaises(LedgerError):
            validate_schedule(plan)

    def test_changed_protocol_bytes_are_not_approved(self):
        path = self.root / "protocol.json"
        path.write_bytes(PROTOCOL.read_bytes() + b"\n")
        with self.assertRaises(LedgerError):
            read_protocol(path)

    def test_mutating_caller_schedule_cannot_change_live_contract(self):
        authority, output = self.directories()
        plan = expected_schedule()
        ledger = Ledger.begin(authority, output, plan)
        plan["slots"][0]["route"] = "direct-python"
        self.assertEqual(self.reserve(ledger).route, "ontokin")
        self.assertEqual(expected_schedule()["slots"][0]["route"], "ontokin")

    def test_complete_observation_schedule_consumes_exactly_four_each(self):
        ledger, authority, _ = self.begin()
        self.complete_slot(ledger)
        self.control(ledger, "D01")
        self.control(ledger, "D03")
        for slot in ("A02", "A03", "A04"):
            self.complete_slot(ledger, slot)
        state = ledger.snapshot()
        self.assertEqual(state["consumed"], dict.fromkeys(module.STAGES, 4))
        self.assertTrue(state["ledger_complete"])
        self.assertFalse(state["native_readiness"])
        self.assertFalse(state["admission_completed"])
        self.assertIsNone(state["next_item"])
        observed = inspect(authority)
        self.assertTrue(observed["journal_integrity_valid"])
        self.assertFalse(observed["semantics_verified"])
        self.assertFalse(observed["resumable"])
        self.assertEqual(observed["events"][-1]["type"], "LEDGER_COMPLETE")
        self.assertEqual(stat.S_IMODE((authority / MARKER).stat().st_mode), 0o444)
        self.assertEqual(len([r for r in observed["events"] if r["type"] == "RESERVED"]), 12)
        with self.assertRaises(LedgerError):
            ledger.reserve("A05", "ontokin", "construction", references={})

    def test_wrong_slot_route_or_reference_stops_before_reservation(self):
        variants = [
            ("A02", "direct-python", BY_NAME["A02"].references()),
            ("A01", "direct-python", BY_NAME["A01"].references()),
            ("N01", "ontokin", BY_NAME["A01"].references()),
            ("A01", "ontokin", {}),
            ("A01", "ontokin", {**BY_NAME["A01"].references(), "completed_predecessor": False}),
            ("A01", "ontokin", {**BY_NAME["A01"].references(), "equality_references": ()}),
        ]
        for slot, route, refs in variants:
            with self.subTest(slot=slot, route=route, refs=refs):
                ledger, _, _ = self.begin()
                with self.assertRaises(LedgerError):
                    ledger.reserve(slot, route, "construction", references=refs)
                self.stopped(ledger)
                self.assertEqual(ledger.snapshot()["consumed"]["construction"], 0)

    def test_receiving_node_and_promotion_cannot_skip_predecessors(self):
        for stage in ("receiving", "node", "promotion"):
            with self.subTest(stage=stage):
                ledger, _, _ = self.begin()
                with self.assertRaises(LedgerError):
                    self.promotion(ledger) if stage == "promotion" else self.reserve(ledger, stage=stage)
                self.stopped(ledger)

    def test_node_cannot_skip_conditional_promotion(self):
        ledger, _, _ = self.begin()
        for stage in ("construction", "receiving"):
            self.finish(ledger, self.reserve(ledger, stage=stage))
        with self.assertRaises(LedgerError):
            self.reserve(ledger, stage="node")
        self.stopped(ledger)

    def test_active_reservation_cannot_be_repeated_or_completed_with_forged_receipt(self):
        for mode in ("repeat", "forged"):
            with self.subTest(mode=mode):
                ledger, _, _ = self.begin()
                receipt = self.reserve(ledger)
                self.assertFalse(receipt.native_start_authorized)
                with self.assertRaises(LedgerError):
                    if mode == "repeat":
                        self.reserve(ledger)
                    else:
                        self.finish(ledger, Reservation(**receipt.__dict__))
                self.assertEqual(ledger.snapshot()["consumed"]["construction"], 1)
                self.stopped(ledger)

    def test_concurrent_reservation_cannot_double_consume(self):
        ledger, _, _ = self.begin()
        def attempt():
            try:
                return self.reserve(ledger)
            except LedgerError as exc:
                return exc
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: attempt(), range(2)))
        self.assertEqual(sum(isinstance(r, Reservation) for r in results), 1)
        self.assertEqual(ledger.snapshot()["consumed"]["construction"], 1)
        self.stopped(ledger)

    def test_each_failed_unknown_timeout_or_cancelled_stage_is_consumed(self):
        for stage in module.STAGES:
            for outcome in ("failed", "unknown", "timeout", "cancelled"):
                with self.subTest(stage=stage, outcome=outcome):
                    ledger, authority, _ = self.begin()
                    if stage in ("receiving", "node"):
                        self.finish(ledger, self.reserve(ledger))
                    if stage == "node":
                        self.finish(ledger, self.reserve(ledger, stage="receiving"))
                        self.promotion(ledger)
                    self.finish(ledger, self.reserve(ledger, stage=stage), outcome=outcome)
                    self.assertEqual(ledger.snapshot()["consumed"][stage], 1)
                    self.stopped(ledger)
                    self.assertEqual(inspect(authority)["events"][-1]["outcome"], outcome)

    def test_failed_cleanup_blocks_receiving_or_promotion_or_next_slot(self):
        for stage in module.STAGES:
            with self.subTest(stage=stage):
                ledger, _, _ = self.begin()
                if stage != "construction":
                    self.finish(ledger, self.reserve(ledger))
                if stage == "node":
                    self.finish(ledger, self.reserve(ledger, stage="receiving"))
                    self.promotion(ledger)
                self.finish(ledger, self.reserve(ledger, stage=stage), cleanup_passed=False)
                self.stopped(ledger)

    def test_invalid_stage_evidence_or_cleanup_type_stops(self):
        for override in ({"cleanup_passed": 1}, {"evidence_sha256": ""}, {"outcome": "retry"}):
            with self.subTest(override=override):
                ledger, _, _ = self.begin()
                receipt = self.reserve(ledger)
                with self.assertRaises(LedgerError):
                    self.finish(ledger, receipt, **override)
                self.stopped(ledger)

    def test_promotion_failure_or_uncertainty_blocks_node(self):
        variants = ({"outcome": "failed"}, {"outcome": "unknown"},
                    {"cleanup_passed": False}, {"conditional_promotion_passed": False})
        for variant in variants:
            with self.subTest(variant=variant):
                ledger, _, _ = self.begin()
                for stage in ("construction", "receiving"):
                    self.finish(ledger, self.reserve(ledger, stage=stage))
                self.promotion(ledger, **variant)
                self.stopped(ledger)
                self.assertEqual(ledger.snapshot()["consumed"]["node"], 0)

    def test_controls_must_follow_a01_node_and_d01_then_d03(self):
        for scenario in ("before-a01", "d03-first", "a02-early"):
            with self.subTest(scenario=scenario):
                ledger, _, _ = self.begin()
                if scenario != "before-a01":
                    self.complete_slot(ledger)
                with self.assertRaises(LedgerError):
                    if scenario == "a02-early":
                        self.reserve(ledger, "A02")
                    else:
                        self.control(ledger, "D03" if scenario == "d03-first" else "D01")
                self.stopped(ledger)

    def test_control_requires_named_finding_and_accepted_closure_preservation(self):
        for control in ("D01", "D03"):
            for variant in ({"findings": ["GEOMETRY"]}, {"accepted_closure_unchanged": False},
                            {"outcome": "unknown"}):
                with self.subTest(control=control, variant=variant):
                    ledger, _, _ = self.begin()
                    self.complete_slot(ledger)
                    if control == "D03":
                        self.control(ledger)
                    self.control(ledger, control, **variant)
                    self.stopped(ledger)
                    self.assertEqual(ledger.snapshot()["consumed"], dict.fromkeys(module.STAGES, 1))

    def test_structural_failure_cannot_substitute_for_a_delivered_control(self):
        for control, finding in (("D01", "CLEARANCE"), ("D03", "SIBLING")):
            with self.subTest(control=control):
                ledger, _, _ = self.begin()
                self.complete_slot(ledger)
                if control == "D03":
                    self.control(ledger)
                self.control(ledger, control, findings=[finding, "STRUCTURE"])
                self.stopped(ledger)

    def test_regeneration_must_bind_its_exact_baseline_and_predecessor(self):
        ledger, _, _ = self.begin()
        self.complete_slot(ledger)
        self.control(ledger)
        self.control(ledger, "D03")
        self.complete_slot(ledger, "A02")
        references = BY_NAME["A03"].references()
        references["accepted_source_reference"] = "A02"
        with self.assertRaises(LedgerError):
            self.reserve(ledger, "A03", references=references)
        self.stopped(ledger)
        self.assertEqual(ledger.snapshot()["consumed"]["construction"], 2)

    def test_directory_change_does_not_allow_second_invocation(self):
        ledger, authority, output = self.begin()
        before = {p.name: p.read_bytes() for p in authority.iterdir()}
        second_output = output.parent / "different-output"
        second_output.mkdir()
        with self.assertRaises(LedgerError) as raised:
            Ledger.begin(authority, second_output, expected_schedule())
        self.assertEqual(raised.exception.code, "REPLAY")
        self.assertEqual(before, {p.name: p.read_bytes() for p in authority.iterdir()})
        self.assertFalse(ledger.snapshot()["stopped"])

    def test_missing_or_cleared_journal_never_resets_invocation(self):
        for clear in (False, True):
            with self.subTest(clear=clear):
                ledger, authority, output = self.begin()
                if clear:
                    (authority / JOURNAL).write_bytes(b"")
                else:
                    (authority / JOURNAL).unlink()
                with self.assertRaises(LedgerError):
                    Ledger.begin(authority, output, expected_schedule())
                result = inspect(authority)
                self.assertTrue(result["consumed"])
                self.assertFalse(result["journal_integrity_valid"])
                with self.assertRaises(LedgerError):
                    self.reserve(ledger)
                self.stopped(ledger)

    def test_orphaned_journal_also_blocks_new_invocation(self):
        _, authority, output = self.begin()
        (authority / MARKER).unlink()
        with self.assertRaises(LedgerError):
            Ledger.begin(authority, output, expected_schedule())
        self.assertFalse((authority / MARKER).exists())
        self.assertTrue(inspect(authority)["consumed"])

    def test_marker_sync_failure_preserves_consumed_authority(self):
        authority, output = self.directories()
        with mock.patch.object(module.os, "fsync", side_effect=OSError("controlled fsync failure")):
            with self.assertRaises(LedgerError) as raised:
                Ledger.begin(authority, output, expected_schedule())
        self.assertTrue(raised.exception.consumed)
        self.assertTrue((authority / MARKER).exists())
        with self.assertRaises(LedgerError):
            Ledger.begin(authority, output, expected_schedule())

    def test_directory_sync_failure_does_not_erase_marker(self):
        authority, output = self.directories()
        original = os.fsync
        calls = 0
        def fail_directory(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("controlled directory sync failure")
            return original(fd)
        with mock.patch.object(module.os, "fsync", side_effect=fail_directory):
            with self.assertRaises(LedgerError):
                Ledger.begin(authority, output, expected_schedule())
        self.assertTrue((authority / MARKER).exists())
        self.assertFalse((authority / JOURNAL).exists())

    def test_partial_append_is_preserved_and_poisoned(self):
        ledger, authority, _ = self.begin()
        before = (authority / JOURNAL).read_bytes()
        def partial(fd, data):
            os.write(fd, data[:13])
            raise OSError("controlled partial append")
        with mock.patch.object(module, "_write_all", side_effect=partial):
            with self.assertRaises(LedgerError):
                self.reserve(ledger)
        self.assertEqual(len((authority / JOURNAL).read_bytes()), len(before) + 13)
        self.assertEqual(ledger.snapshot()["consumed"]["construction"], 1)
        self.stopped(ledger)
        self.assertFalse(inspect(authority)["journal_integrity_valid"])

    def test_lost_append_sync_result_never_returns_a_reservation(self):
        ledger, authority, _ = self.begin()
        with mock.patch.object(module.os, "fsync", side_effect=OSError("controlled lost durability result")):
            with self.assertRaises(LedgerError):
                self.reserve(ledger)
        self.assertEqual(ledger.snapshot()["consumed"]["construction"], 1)
        self.stopped(ledger)
        self.assertEqual(inspect(authority)["events"][-1]["type"], "RESERVED")
        self.assertFalse(inspect(authority)["resumable"])

    def test_result_persistence_failure_preserves_prior_consumption(self):
        ledger, _, _ = self.begin()
        receipt = self.reserve(ledger)
        with mock.patch.object(module.os, "fsync", side_effect=OSError("controlled result failure")):
            with self.assertRaises(LedgerError):
                self.finish(ledger, receipt)
        self.assertEqual(ledger.snapshot()["consumed"]["construction"], 1)
        self.stopped(ledger)

    def test_interrupt_after_durable_event_poisons_every_public_mutation(self):
        for operation in ("reserve", "finish", "promotion", "control", "stop"):
            with self.subTest(operation=operation):
                ledger, authority, _ = self.begin()
                if operation == "finish":
                    receipt = self.reserve(ledger)
                elif operation == "promotion":
                    for stage in ("construction", "receiving"):
                        self.finish(ledger, self.reserve(ledger, stage=stage))
                elif operation == "control":
                    self.complete_slot(ledger)
                original = ledger._append
                def durable_then_interrupt(event):
                    original(event)
                    raise KeyboardInterrupt("Controlled interruption after persistence")
                with mock.patch.object(ledger, "_append", side_effect=durable_then_interrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        if operation == "reserve":
                            self.reserve(ledger)
                        elif operation == "finish":
                            self.finish(ledger, receipt)
                        elif operation == "promotion":
                            self.promotion(ledger)
                        elif operation == "control":
                            self.control(ledger)
                        else:
                            ledger.stop("Controlled stop")
                self.stopped(ledger)
                self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])
                self.assertFalse(inspect(authority)["resumable"])
                if operation == "reserve":
                    self.assertEqual(ledger.snapshot()["consumed"]["construction"], 1)
                    rows = inspect(authority)["events"]
                    self.assertEqual(sum(r["type"] == "RESERVED" for r in rows), 1)

    def test_interrupted_finalization_is_not_reported_as_completed(self):
        ledger, authority, _ = self.begin()
        self.complete_slot(ledger)
        self.control(ledger)
        self.control(ledger, "D03")
        self.complete_slot(ledger, "A02")
        self.complete_slot(ledger, "A03")
        for stage in ("construction", "receiving"):
            self.finish(ledger, self.reserve(ledger, "A04", stage))
        self.promotion(ledger, "A04")
        receipt = self.reserve(ledger, "A04", "node")
        original = ledger._append
        def interrupt_completion(event):
            original(event)
            if event["type"] == "LEDGER_COMPLETE":
                raise KeyboardInterrupt("Controlled lost finalization reply")
        with mock.patch.object(ledger, "_append", side_effect=interrupt_completion):
            with self.assertRaises(KeyboardInterrupt):
                self.finish(ledger, receipt)
        self.stopped(ledger)
        self.assertFalse(ledger.snapshot()["ledger_complete"])
        self.assertFalse(ledger.snapshot()["admission_completed"])
        self.assertFalse(inspect(authority)["semantics_verified"])

    def test_fifo_reservation_files_are_rejected_without_open_blocking(self):
        for name in (MARKER, JOURNAL):
            with self.subTest(name=name):
                ledger, authority, _ = self.begin()
                (authority / name).unlink()
                os.mkfifo(authority / name)
                self.assertFalse(inspect(authority)["journal_integrity_valid"])
                with self.assertRaises(LedgerError):
                    self.reserve(ledger)
                self.stopped(ledger)

    def test_corrupt_replaced_aliased_or_missing_files_poison_live_capability(self):
        for name in (MARKER, JOURNAL):
            for mutation in ("corrupt", "replace", "symlink", "hardlink", "missing"):
                with self.subTest(name=name, mutation=mutation):
                    ledger, authority, output = self.begin()
                    path = authority / name
                    original = path.read_bytes()
                    if mutation == "corrupt":
                        path.chmod(0o600)
                        path.write_bytes(original + b" ")
                    elif mutation == "hardlink":
                        os.link(path, output / "alias")
                    else:
                        path.unlink()
                        if mutation == "replace":
                            path.write_bytes(original)
                        elif mutation == "symlink":
                            target = output / "alias"
                            target.write_bytes(original)
                            path.symlink_to(target)
                    with self.assertRaises(LedgerError):
                        self.reserve(ledger)
                    self.stopped(ledger)

    def test_replaced_authority_or_output_directory_poison_live_capability(self):
        for replace_authority in (True, False):
            with self.subTest(authority=replace_authority):
                ledger, authority, output = self.begin()
                path = authority if replace_authority else output
                path.rename(path.with_name(path.name + "-old"))
                path.mkdir()
                with self.assertRaises(LedgerError):
                    self.reserve(ledger)
                self.stopped(ledger)

    def test_path_aliases_overlap_and_nonempty_output_fail_before_claim(self):
        for case in ("symlink", "overlap", "nonempty", "relative"):
            with self.subTest(case=case):
                authority, output = self.directories()
                requested = authority
                if case == "symlink":
                    requested = authority.with_name("alias")
                    requested.symlink_to(authority, target_is_directory=True)
                elif case == "overlap":
                    output = authority / "output"
                    output.mkdir()
                elif case == "nonempty":
                    (output / "previous-result").write_text("preserve")
                else:
                    requested = Path("relative-authority")
                with self.assertRaises(LedgerError):
                    Ledger.begin(requested, output, expected_schedule())
                self.assertFalse((authority / MARKER).exists())

    def test_explicit_unknown_stop_and_journal_bound_are_terminal(self):
        ledger, _, _ = self.begin()
        ledger.stop("Controlled interruption before any child", outcome="unknown")
        self.stopped(ledger)
        ledger, authority, _ = self.begin()
        with mock.patch.object(module, "MAX_JOURNAL_BYTES", len((authority / JOURNAL).read_bytes()) + 1):
            with self.assertRaises(LedgerError):
                self.reserve(ledger)
        self.stopped(ledger)

    def test_readonly_inspection_never_creates_or_resumes_capability(self):
        authority, _ = self.directories()
        self.assertFalse(inspect(authority)["consumed"])
        self.assertEqual(list(authority.iterdir()), [])
        _, authority, _ = self.begin()
        before = {p.name: p.read_bytes() for p in authority.iterdir()}
        self.assertFalse(inspect(authority)["resumable"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in authority.iterdir()})
        with self.assertRaises(TypeError):
            Ledger()

    def test_inspection_rejects_partial_or_noncanonical_journal(self):
        for mutate in (lambda b: b[:-1], lambda b: b.replace(b'"sequence":0', b'"sequence":0,"sequence":0')):
            ledger, authority, _ = self.begin()
            path = authority / JOURNAL
            path.write_bytes(mutate(path.read_bytes()))
            self.assertFalse(inspect(authority)["journal_integrity_valid"])
            self.assertFalse(inspect(authority)["resumable"])


if __name__ == "__main__":
    unittest.main()
