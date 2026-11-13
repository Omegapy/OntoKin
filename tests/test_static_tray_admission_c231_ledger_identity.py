"""C231 CPU file-object lifetime controls; no native application is started."""
from __future__ import annotations

import errno
import gc
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
import weakref

from prototypes.static_tray_admission_c201 import ledger as module
from prototypes.static_tray_admission_c201.schedule import LedgerError, SLOTS, expected_schedule


EVIDENCE = hashlib.sha256(b"C231 synthetic CPU observation").hexdigest()
BY_NAME = {slot.name: slot for slot in SLOTS}


class IdentityLifecycleControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-c231-cpu-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.counter = 0

    def directories(self):
        self.counter += 1
        root = self.root / str(self.counter)
        root.mkdir()
        authority, output = root / "authority", root / "output"
        authority.mkdir()
        output.mkdir()
        return authority, output

    def begin(self):
        authority, output = self.directories()
        ledger = module.Ledger.begin(authority, output, expected_schedule())
        self.addCleanup(ledger.close)
        return ledger, authority, output

    def reserve(self, ledger, slot="A01", stage="construction"):
        row = BY_NAME[slot]
        return ledger.reserve(slot, row.route, stage, references=row.references())

    def finish(self, ledger, receipt, **overrides):
        arguments = {"outcome": "passed", "cleanup_passed": True,
                     "evidence_sha256": EVIDENCE, **overrides}
        ledger.finish(receipt, **arguments)

    def promotion(self, ledger, slot="A01", **overrides):
        row = BY_NAME[slot]
        arguments = {"references": row.references(), "outcome": "passed", "cleanup_passed": True,
                     "conditional_promotion_passed": True, "evidence_sha256": EVIDENCE, **overrides}
        ledger.record_promotion(slot, row.route, **arguments)

    def complete_slot(self, ledger, slot="A01"):
        for stage in ("construction", "receiving"):
            self.finish(ledger, self.reserve(ledger, slot, stage))
        self.promotion(ledger, slot)
        self.finish(ledger, self.reserve(ledger, slot, "node"))

    def control(self, ledger, control="D01", **overrides):
        arguments = {"source_slot": "A01", "outcome": "passed", "evidence_sha256": EVIDENCE,
                     "findings": [{"D01": "CLEARANCE", "D03": "SIBLING"}[control]],
                     "accepted_closure_unchanged": True, **overrides}
        ledger.record_control(control, **arguments)

    def closed(self, descriptors):
        for fd in descriptors:
            with self.assertRaises(OSError) as caught:
                os.fstat(fd)
            self.assertEqual(caught.exception.errno, errno.EBADF)

    def stopped(self, ledger):
        self.assertTrue(ledger.snapshot()["stopped"])
        with self.assertRaises(LedgerError) as caught:
            self.reserve(ledger)
        self.assertEqual(caught.exception.code, "STOPPED")

    def track_creations(self, records):
        original = os.open
        def opening(path, flags, *args, **kwargs):
            fd = original(path, flags, *args, **kwargs)
            if path in (module.MARKER, module.JOURNAL) and flags & os.O_CREAT:
                records.append((path, fd))
            return fd
        return mock.patch.object(module.os, "open", side_effect=opening)

    def test_original_objects_remain_pinned_and_noninheritable(self):
        ledger, authority, _ = self.begin()
        self.assertEqual(set(ledger._pins), {module.MARKER, module.JOURNAL})
        for name, fd in ledger._pins.items():
            held = os.fstat(fd)
            current = (authority / name).stat()
            self.assertEqual((held.st_dev, held.st_ino), (current.st_dev, current.st_ino))
            self.assertEqual(held.st_nlink, 1)
            self.assertFalse(os.get_inheritable(fd))
        self.reserve(ledger)
        self.assertFalse(ledger.snapshot()["stopped"])

    def test_numeric_identity_collision_cannot_admit_same_content_replacement(self):
        for name in (module.MARKER, module.JOURNAL):
            with self.subTest(name=name):
                ledger, authority, _ = self.begin()
                descriptors = tuple(ledger._pins.values())
                path = authority / name
                original_bytes, original = path.read_bytes(), path.stat()
                path.unlink()
                self.assertEqual(os.fstat(ledger._pins[name]).st_nlink, 0)
                path.write_bytes(original_bytes)
                replaced = path.stat()
                original_identity = (original.st_dev, original.st_ino)
                recreated_identity = (replaced.st_dev, replaced.st_ino)
                true_identity = module._identity
                def collision(info):
                    observed = true_identity(info)
                    return original_identity if observed == recreated_identity else observed
                with mock.patch.object(module, "_identity", side_effect=collision):
                    with self.assertRaises(LedgerError) as caught:
                        self.reserve(ledger)
                self.assertEqual(caught.exception.code, "PERSISTENCE")
                self.assertEqual(ledger.snapshot()["consumed"]["construction"], 1)
                self.closed(descriptors)
                self.stopped(ledger)

    def test_replacement_during_path_read_is_rejected_before_append(self):
        for name in (module.MARKER, module.JOURNAL):
            with self.subTest(name=name):
                ledger, authority, _ = self.begin()
                descriptors = tuple(ledger._pins.values())
                journal_before = (authority / module.JOURNAL).read_bytes()
                original = module._read_regular
                def read_then_replace(dirfd, current, limit):
                    result = original(dirfd, current, limit)
                    if current == module.JOURNAL:
                        path = authority / name
                        data = path.read_bytes()
                        path.unlink()
                        path.write_bytes(data)
                    return result
                with mock.patch.object(module, "_read_regular", side_effect=read_then_replace):
                    with self.assertRaises(LedgerError):
                        self.reserve(ledger)
                self.assertEqual((authority / module.JOURNAL).read_bytes(), journal_before)
                self.closed(descriptors)
                self.stopped(ledger)

    def test_negative_stage_and_cleanup_observations_close_pins(self):
        for overrides in ({"outcome": "failed"}, {"outcome": "timeout"},
                          {"outcome": "cancelled"}, {"outcome": "unknown"},
                          {"cleanup_passed": False}):
            with self.subTest(overrides=overrides):
                ledger, _, _ = self.begin()
                descriptors = tuple(ledger._pins.values())
                self.finish(ledger, self.reserve(ledger), **overrides)
                self.closed(descriptors)
                self.stopped(ledger)

    def test_negative_promotion_and_control_observations_close_pins(self):
        for case in ("promotion", "control"):
            with self.subTest(case=case):
                ledger, _, _ = self.begin()
                descriptors = tuple(ledger._pins.values())
                if case == "promotion":
                    for stage in ("construction", "receiving"):
                        self.finish(ledger, self.reserve(ledger, stage=stage))
                    self.promotion(ledger, conditional_promotion_passed=False)
                else:
                    self.complete_slot(ledger)
                    self.control(ledger, accepted_closure_unchanged=False)
                self.closed(descriptors)
                self.stopped(ledger)

    def test_invalid_mutation_and_explicit_stop_close_pins(self):
        for case in ("invalid", "stop"):
            with self.subTest(case=case):
                ledger, _, _ = self.begin()
                descriptors = tuple(ledger._pins.values())
                if case == "invalid":
                    with self.assertRaises(LedgerError):
                        self.reserve(ledger, stage="node")
                else:
                    ledger.stop("C231 synthetic stop", outcome="unknown")
                self.closed(descriptors)
                self.stopped(ledger)

    def test_normal_schedule_completion_closes_pins(self):
        ledger, authority, _ = self.begin()
        descriptors = tuple(ledger._pins.values())
        self.complete_slot(ledger)
        self.control(ledger)
        self.control(ledger, "D03")
        for slot in ("A02", "A03", "A04"):
            self.complete_slot(ledger, slot)
        self.closed(descriptors)
        self.assertTrue(ledger.snapshot()["ledger_complete"])
        self.assertFalse(ledger.snapshot()["persistence_or_interruption_uncertain"])
        self.assertEqual(module.inspect(authority)["events"][-1]["type"], "LEDGER_COMPLETE")

    def test_explicit_close_is_idempotent_and_preserves_consumed_evidence(self):
        ledger, authority, output = self.begin()
        descriptors = tuple(ledger._pins.values())
        before = {p.name: p.read_bytes() for p in authority.iterdir()}
        ledger.close()
        self.closed(descriptors)
        with mock.patch.object(module.os, "close", side_effect=AssertionError("Repeated close")):
            ledger.close()
        self.stopped(ledger)
        self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in authority.iterdir()})
        with self.assertRaises(LedgerError) as caught:
            module.Ledger.begin(authority, output, expected_schedule())
        self.assertEqual(caught.exception.code, "REPLAY")
        self.assertFalse(module.inspect(authority)["resumable"])

    def test_context_exit_closes_on_normal_and_exceptional_exit(self):
        for interrupt in (False, True):
            with self.subTest(interrupt=interrupt):
                authority, output = self.directories()
                try:
                    with module.Ledger.begin(authority, output, expected_schedule()) as ledger:
                        descriptors = tuple(ledger._pins.values())
                        self.reserve(ledger)
                        if interrupt:
                            raise KeyboardInterrupt("Controlled context interruption")
                except KeyboardInterrupt:
                    self.assertTrue(interrupt)
                self.closed(descriptors)
                self.stopped(ledger)
                self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])

    def test_context_body_exception_survives_secondary_cleanup_failure(self):
        for body_error in (ValueError("Controlled body failure"),
                           KeyboardInterrupt("Controlled body interruption")):
            with self.subTest(body_error=type(body_error).__name__):
                authority, output = self.directories()
                ledger = module.Ledger.begin(authority, output, expected_schedule())
                descriptors = tuple(ledger._pins.values())
                original, calls = os.close, []
                def close_then_fail(fd):
                    original(fd)
                    calls.append(fd)
                    if len(calls) == 1:
                        raise KeyboardInterrupt("Controlled secondary cleanup interruption")
                with mock.patch.object(module.os, "close", side_effect=close_then_fail):
                    with self.assertRaises(type(body_error)) as caught:
                        with ledger:
                            raise body_error
                self.assertIs(caught.exception, body_error)
                self.assertCountEqual(calls, descriptors)
                self.closed(descriptors)
                self.stopped(ledger)
                self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])

    def test_abandoned_object_finalizer_does_not_retain_capability(self):
        authority, output = self.directories()
        ledger = module.Ledger.begin(authority, output, expected_schedule())
        descriptors = tuple(ledger._pins.values())
        reference = weakref.ref(ledger)
        del ledger
        gc.collect()
        self.assertIsNone(reference())
        self.closed(descriptors)
        self.assertTrue(module.inspect(authority)["consumed"])
        self.assertFalse(module.inspect(authority)["resumable"])

    def test_each_creation_sync_failure_closes_all_acquired_pins(self):
        for failure_index in range(1, 5):
            with self.subTest(fsync=failure_index):
                authority, output = self.directories()
                records, calls = [], 0
                original = os.fsync
                def failing(fd):
                    nonlocal calls
                    calls += 1
                    if calls == failure_index:
                        raise OSError("Controlled creation sync failure")
                    return original(fd)
                with self.track_creations(records), mock.patch.object(module.os, "fsync", side_effect=failing):
                    with self.assertRaises(LedgerError) as caught:
                        module.Ledger.begin(authority, output, expected_schedule())
                self.assertTrue(caught.exception.consumed)
                self.assertEqual(len(records), 1 if failure_index <= 2 else 2)
                self.closed(fd for _, fd in records)
                self.assertTrue((authority / module.MARKER).exists())

    def test_partial_creation_interruptions_close_pins_without_deleting_authority(self):
        for location in ("marker_write", "journal_sync"):
            with self.subTest(location=location):
                authority, output = self.directories()
                records = []
                original_sync = os.fsync
                def syncing(fd):
                    if location == "journal_sync" and len(records) == 2:
                        raise KeyboardInterrupt("Controlled journal interruption")
                    return original_sync(fd)
                original_write = module._write_all
                def writing(fd, data):
                    if location == "marker_write":
                        os.write(fd, data[:13])
                        raise KeyboardInterrupt("Controlled marker interruption")
                    return original_write(fd, data)
                with self.track_creations(records), mock.patch.object(module.os, "fsync", side_effect=syncing), \
                        mock.patch.object(module, "_write_all", side_effect=writing):
                    with self.assertRaises(KeyboardInterrupt):
                        module.Ledger.begin(authority, output, expected_schedule())
                self.closed(fd for _, fd in records)
                self.assertTrue((authority / module.MARKER).exists())

    def test_initial_append_failure_and_lost_reply_close_both_pins(self):
        for after_append in (False, True):
            with self.subTest(after_append=after_append):
                authority, output = self.directories()
                records = []
                original = module.Ledger._append
                def broken(ledger, event):
                    if after_append:
                        original(ledger, event)
                    raise KeyboardInterrupt("Controlled initial append interruption")
                with self.track_creations(records), mock.patch.object(module.Ledger, "_append", broken):
                    with self.assertRaises(KeyboardInterrupt):
                        module.Ledger.begin(authority, output, expected_schedule())
                self.assertEqual(len(records), 2)
                self.closed(fd for _, fd in records)
                self.assertEqual(module.inspect(authority)["journal_integrity_valid"], after_append)

    def test_later_persistence_failure_closes_pins_and_forbids_retry(self):
        for partial in (False, True):
            with self.subTest(partial=partial):
                ledger, authority, _ = self.begin()
                descriptors = tuple(ledger._pins.values())
                if partial:
                    def writing(fd, data):
                        os.write(fd, data[:13])
                        raise OSError("Controlled partial append")
                    patch = mock.patch.object(module, "_write_all", side_effect=writing)
                else:
                    patch = mock.patch.object(module.os, "fsync", side_effect=OSError("Controlled lost sync"))
                with patch:
                    with self.assertRaises(LedgerError):
                        self.reserve(ledger)
                self.closed(descriptors)
                self.stopped(ledger)
                self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])
                self.assertEqual(ledger.snapshot()["consumed"]["construction"], 1)

    def test_post_append_interruptions_close_every_public_mutation(self):
        for operation in ("reserve", "finish", "promotion", "control", "stop"):
            with self.subTest(operation=operation):
                ledger, _, _ = self.begin()
                if operation == "finish":
                    receipt = self.reserve(ledger)
                elif operation == "promotion":
                    for stage in ("construction", "receiving"):
                        self.finish(ledger, self.reserve(ledger, stage=stage))
                elif operation == "control":
                    self.complete_slot(ledger)
                descriptors = tuple(ledger._pins.values())
                original = ledger._append
                def interrupted(event):
                    original(event)
                    raise KeyboardInterrupt("Controlled durable append interruption")
                with mock.patch.object(ledger, "_append", side_effect=interrupted):
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
                            ledger.stop("Controlled durable stop")
                self.closed(descriptors)
                self.stopped(ledger)
                self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])

    def test_interrupted_completion_closes_pins_without_claiming_completion(self):
        ledger, _, _ = self.begin()
        self.complete_slot(ledger)
        self.control(ledger)
        self.control(ledger, "D03")
        self.complete_slot(ledger, "A02")
        self.complete_slot(ledger, "A03")
        for stage in ("construction", "receiving"):
            self.finish(ledger, self.reserve(ledger, "A04", stage))
        self.promotion(ledger, "A04")
        receipt = self.reserve(ledger, "A04", "node")
        descriptors = tuple(ledger._pins.values())
        original = ledger._append
        def interrupted(event):
            original(event)
            if event["type"] == "LEDGER_COMPLETE":
                raise KeyboardInterrupt("Controlled completion interruption")
        with mock.patch.object(ledger, "_append", side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):
                self.finish(ledger, receipt)
        self.closed(descriptors)
        self.stopped(ledger)
        self.assertFalse(ledger.snapshot()["ledger_complete"])

    def test_uncertain_close_is_not_retried_and_other_pin_is_attempted(self):
        ledger, _, _ = self.begin()
        descriptors = tuple(ledger._pins.values())
        original, calls = os.close, []
        def lost_reply(fd):
            calls.append(fd)
            original(fd)
            if len(calls) == 1:
                raise InterruptedError("Controlled lost close result")
        with mock.patch.object(module.os, "close", side_effect=lost_reply):
            with self.assertRaises(LedgerError) as caught:
                ledger.close()
            self.assertEqual(caught.exception.code, "PERSISTENCE")
            ledger.close()
        self.assertCountEqual(calls, descriptors)
        self.closed(descriptors)
        self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])

    def test_cleanup_interrupt_poisoning_preserves_original_failure(self):
        for original_failure in (False, True):
            with self.subTest(original_failure=original_failure):
                ledger, _, _ = self.begin()
                descriptors = tuple(ledger._pins.values())
                original, closed = os.close, []
                def interrupted_close(fd):
                    result = original(fd)
                    if fd in descriptors:
                        closed.append(fd)
                        if len(closed) == 1:
                            raise KeyboardInterrupt("Controlled cleanup interruption")
                    return result
                with mock.patch.object(module.os, "close", side_effect=interrupted_close):
                    if original_failure:
                        with self.assertRaises(LedgerError) as caught:
                            self.reserve(ledger, stage="node")
                        self.assertEqual(caught.exception.code, "ORDER")
                    else:
                        with self.assertRaises(KeyboardInterrupt):
                            ledger.stop("Controlled stop before cleanup interruption")
                self.assertCountEqual(closed, descriptors)
                self.closed(descriptors)
                self.stopped(ledger)
                self.assertFalse(ledger.snapshot()["ledger_complete"])
                self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])

    def test_completion_cleanup_interruption_cannot_report_completion(self):
        ledger, _, _ = self.begin()
        self.complete_slot(ledger)
        self.control(ledger)
        self.control(ledger, "D03")
        self.complete_slot(ledger, "A02")
        self.complete_slot(ledger, "A03")
        for stage in ("construction", "receiving"):
            self.finish(ledger, self.reserve(ledger, "A04", stage))
        self.promotion(ledger, "A04")
        receipt = self.reserve(ledger, "A04", "node")
        descriptors = tuple(ledger._pins.values())
        original, calls = os.close, []
        def interrupted_close(fd):
            result = original(fd)
            if fd in descriptors:
                calls.append(fd)
                if len(calls) == 1:
                    raise KeyboardInterrupt("Controlled completion cleanup interruption")
            return result
        with mock.patch.object(module.os, "close", side_effect=interrupted_close):
            with self.assertRaises(KeyboardInterrupt):
                self.finish(ledger, receipt)
        self.assertCountEqual(calls, descriptors)
        self.closed(descriptors)
        self.stopped(ledger)
        self.assertFalse(ledger.snapshot()["ledger_complete"])
        self.assertTrue(ledger.snapshot()["persistence_or_interruption_uncertain"])

    def test_interrupted_cleanup_lock_retains_handles_and_original_error(self):
        for original_failure in (False, True):
            with self.subTest(original_failure=original_failure):
                ledger, _, _ = self.begin()
                descriptors = tuple(ledger._pins.values())
                true_lock = module._FORK_LOCK
                class InterruptOnce:
                    interrupted = False
                    def __enter__(self):
                        if not self.interrupted:
                            self.interrupted = True
                            raise KeyboardInterrupt("Controlled cleanup lock interruption")
                        return true_lock.__enter__()
                    def __exit__(self, *arguments):
                        return true_lock.__exit__(*arguments)
                with mock.patch.object(module, "_FORK_LOCK", InterruptOnce()):
                    if original_failure:
                        with self.assertRaises(LedgerError) as caught:
                            self.reserve(ledger, stage="node")
                        self.assertEqual(caught.exception.code, "ORDER")
                    else:
                        with self.assertRaises(KeyboardInterrupt):
                            ledger.close()
                    self.assertTrue(ledger._pin_finalizer.alive)
                    self.assertCountEqual(ledger._pins.values(), descriptors)
                    for fd in descriptors:
                        self.assertEqual(os.fstat(fd).st_nlink, 1)
                    state = ledger.snapshot()
                    self.assertTrue(state["stopped"])
                    self.assertTrue(state["persistence_or_interruption_uncertain"])
                    self.assertFalse(state["ledger_complete"])
                    ledger.close()
                    self.closed(descriptors)
                    self.assertFalse(ledger._pin_finalizer.alive)

    def test_pid_mismatch_rejects_before_acquiring_inherited_mutex(self):
        ledger, _, _ = self.begin()
        descriptors = tuple(ledger._pins.values())
        unusable = mock.MagicMock()
        unusable.__enter__.side_effect = AssertionError("Inherited mutex must not be acquired")
        ledger._mutex = unusable
        with mock.patch.object(module.os, "getpid", return_value=ledger._pid + 100000):
            with self.assertRaises(LedgerError) as caught:
                self.reserve(ledger)
            self.assertEqual(caught.exception.code, "STOPPED")
            self.assertTrue(ledger.snapshot()["stopped"])
        unusable.__enter__.assert_not_called()
        self.closed(descriptors)

    def test_fork_child_releases_pins_and_parent_capability_remains_live(self):
        self.assertTrue(hasattr(os, "fork") and hasattr(os, "register_at_fork"),
                        "This POSIX lifecycle control requires actual fork hooks")
        ledger, _, _ = self.begin()
        descriptors = tuple(ledger._pins.values())
        locked, release = threading.Event(), threading.Event()
        def hold_parent_mutex():
            with ledger._mutex:
                locked.set()
                release.wait(12)
        thread = threading.Thread(target=hold_parent_mutex)
        thread.start()
        authority, output = self.directories()
        acquisition_paused, release_acquisition = threading.Event(), threading.Event()
        acquired, created, creation_errors = [], [], []
        true_open = os.open
        def pause_owned_open(path, flags, *args, **kwargs):
            fd = true_open(path, flags, *args, **kwargs)
            if path in (module.MARKER, module.JOURNAL) and flags & os.O_CREAT:
                acquired.append(fd)
                if path == module.MARKER:
                    acquisition_paused.set()
                    release_acquisition.wait(3)
            return fd
        def create_concurrently():
            try:
                created.append(module.Ledger.begin(authority, output, expected_schedule()))
            except BaseException as exc:
                creation_errors.append(type(exc).__name__)
        patch = mock.patch.object(module.os, "open", side_effect=pause_owned_open)
        patch.start()
        creator = threading.Thread(target=create_concurrently)
        creator.start()
        timer = threading.Timer(0.1, release_acquisition.set)
        reader, writer = os.pipe()
        pid, reaped, timed_out, status, data = None, False, False, None, b""
        try:
            self.assertTrue(locked.wait(2))
            self.assertTrue(acquisition_paused.wait(2))
            timer.start()
            pid = os.fork()
            if pid == 0:
                os.close(reader)
                try:
                    closed = []
                    for fd in (*descriptors, *acquired):
                        try:
                            os.fstat(fd)
                            closed.append(False)
                        except OSError as exc:
                            closed.append(exc.errno == errno.EBADF)
                    try:
                        self.reserve(ledger)
                        rejection = None
                    except LedgerError as exc:
                        rejection = exc.code
                    result = {"closed": closed, "rejection": rejection,
                              "stopped": ledger.snapshot()["stopped"]}
                    os.write(writer, json.dumps(result).encode("utf-8"))
                    os._exit(0)
                except BaseException:
                    os._exit(9)
            os.close(writer)
            writer = None
            if not select.select([reader], [], [], 4)[0]:
                timed_out = True
            else:
                data = os.read(reader, 4096)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                observed, status = os.waitpid(pid, os.WNOHANG)
                if observed == pid:
                    reaped = True
                    break
                time.sleep(0.01)
            if not reaped:
                timed_out = True
        finally:
            if pid and not reaped:
                os.kill(pid, signal.SIGKILL)
                _, status = os.waitpid(pid, 0)
                reaped = True
            release.set()
            release_acquisition.set()
            timer.cancel()
            thread.join(2)
            creator.join(2)
            patch.stop()
            for other in created:
                other.close()
            os.close(reader)
            if writer is not None:
                os.close(writer)
            print("C231 CPU fork " + json.dumps({"pid": pid, "reaped": reaped,
                  "timed_out": timed_out, "wait_status": status}), file=sys.stderr)
        self.assertFalse(thread.is_alive())
        self.assertFalse(creator.is_alive())
        self.assertEqual(creation_errors, [])
        self.assertTrue(reaped)
        self.assertFalse(timed_out)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        result = json.loads(data)
        self.assertGreaterEqual(len(result["closed"]), 3)
        self.assertTrue(all(result["closed"]))
        self.assertEqual(result["rejection"], "STOPPED")
        self.assertTrue(result["stopped"])
        for fd in descriptors:
            self.assertEqual(os.fstat(fd).st_nlink, 1)
        self.assertFalse(ledger.snapshot()["stopped"])
        self.reserve(ledger)


if __name__ == "__main__":
    unittest.main()
