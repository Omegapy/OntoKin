"""Durable C201 reservation accounting, with no child-process launch path.

Reported stage results are caller observations bound to evidence digests. This
module does not verify geometry, accepted closures, cleanup, or promotion, and
cannot grant native readiness or admission. A future reviewed coordinator must
perform those checks before submitting observations and starting any child.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import threading
import uuid
import weakref

from .schedule import (LedgerError, ORDER, PROTOCOL_SHA256, SCHEDULE_ID,
                       SCHEDULE_SHA256, SLOTS, canonical, exact, validate_schedule)


MARKER = SCHEDULE_ID + ".invocation.json"
JOURNAL = SCHEDULE_ID + ".ledger.jsonl"
MAX_JOURNAL_BYTES = 4 * 1024 * 1024
STAGES = ("construction", "receiving", "node")
OUTCOMES = ("passed", "failed", "timeout", "cancelled", "unknown")
_SLOT_BY_NAME = {slot.name: slot for slot in SLOTS}
_ZERO = "0" * 64
_LIVE_LEDGERS = weakref.WeakSet()
_FORK_LOCK = threading.RLock()


def _close_pins(pins):
    """Attempt every owned close once; an uncertain close must not be retried."""
    errors = []
    with _FORK_LOCK:
        while pins:
            name, fd = pins.popitem()
            try:
                os.close(fd)
            except BaseException as exc:
                errors.append((name, exc))
    return errors


def _before_fork():
    _FORK_LOCK.acquire()


def _after_fork_parent():
    _FORK_LOCK.release()


def _after_fork_child():
    """The child owns no live capability and must not retain parent file pins."""
    global _FORK_LOCK
    _FORK_LOCK = threading.RLock()
    for ledger in tuple(_LIVE_LEDGERS):
        ledger._mutex = threading.RLock()
        ledger._stopped = True
        ledger._release_pins()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(before=_before_fork, after_in_parent=_after_fork_parent,
                        after_in_child=_after_fork_child)


def _identity(info):
    return info.st_dev, info.st_ino


def _directory(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise LedgerError("PATH", "Use an absolute existing directory without parent traversal")
    for part in (*reversed(path.parents), path):
        if part.is_symlink() or not part.is_dir():
            raise LedgerError("PATH", "Directory aliases and missing ancestors are forbidden")
    return path, _identity(path.stat())


def _write_all(fd, data):
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("Journal write made no progress")
        view = view[written:]


def _read_regular(dirfd, name, limit):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirfd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
            raise LedgerError("INTEGRITY", "Unsafe reservation file")
        chunks, size = [], 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise LedgerError("INTEGRITY", "Reservation file exceeds its bound")
        return b"".join(chunks), _identity(info)
    finally:
        os.close(fd)


def _digest(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _mutation(method):
    """An interruption cannot leave a stale live capability available to retry."""
    @wraps(method)
    def guarded(self, *args, **kwargs):
        if not self._same_process():
            raise LedgerError("STOPPED", "This capability cannot continue or resume", consumed=True)
        with self._mutex:
            failure = None
            try:
                return method(self, *args, **kwargs)
            except BaseException as exc:
                failure = exc
                self._stopped = True
                if not isinstance(exc, LedgerError) or exc.code == "PERSISTENCE":
                    self._uncertain = True
                raise
            finally:
                if self._stopped or self._complete:
                    self._release_pins(propagate=failure is None)
    return guarded


@dataclass(frozen=True)
class Reservation:
    """Accounting receipt only; it is not authorization to execute a child."""
    invocation_id: str
    sequence: int
    slot: str
    route: str
    stage: str
    native_start_authorized: bool = False


class Ledger:
    """One live in-process capability; existing journals can only be inspected."""

    def __init__(self):
        raise TypeError("Use Ledger.begin for a fresh control-only invocation")

    @classmethod
    def begin(cls, authority, output, schedule):
        validate_schedule(schedule)
        authority, root_identity = _directory(authority)
        output, output_identity = _directory(output)
        if authority == output or authority in output.parents or output in authority.parents:
            raise LedgerError("PATH", "Reservation authority and output must be disjoint")
        if any(output.iterdir()):
            raise LedgerError("PATH", "The invocation output directory must be empty")
        obj = object.__new__(cls)
        obj._authority, obj._output = authority, output
        obj._root_identity, obj._output_identity = root_identity, output_identity
        obj._pid, obj._mutex = os.getpid(), threading.RLock()
        obj._stopped, obj._complete = False, False
        obj._uncertain = False
        obj._cursor, obj._phase, obj._active = 0, 0, None
        obj._counts = dict.fromkeys(STAGES, 0)
        obj._reserved = set()
        obj._journal, obj._last_hash, obj._sequence = b"", _ZERO, 0
        obj._invocation_id = uuid.uuid4().hex
        obj._marker = canonical({
            "schema": "ontokin.c201.control-ledger-invocation/0.1",
            "schedule_id": SCHEDULE_ID, "schedule_sha256": SCHEDULE_SHA256,
            "protocol_sha256": PROTOCOL_SHA256, "invocation_id": obj._invocation_id,
            "authority": str(authority), "output": str(output),
            "component_only": True, "native_readiness": False,
        }) + b"\n"
        obj._pins = {}
        obj._pin_finalizer = weakref.finalize(obj, _close_pins, obj._pins)
        with _FORK_LOCK:
            _LIVE_LEDGERS.add(obj)
        claimed = False
        try:
            dirfd = os.open(authority, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                if _identity(os.fstat(dirfd)) != root_identity:
                    raise LedgerError("INTEGRITY", "Reservation authority changed")
                for name in (MARKER, JOURNAL):
                    try:
                        os.stat(name, dir_fd=dirfd, follow_symlinks=False)
                    except FileNotFoundError:
                        continue
                    raise LedgerError("REPLAY", "The schedule already has reservation evidence", consumed=True)
                with _FORK_LOCK:
                    fd = os.open(MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=dirfd)
                    obj._pins[MARKER] = fd
                claimed = True
                _write_all(fd, obj._marker)
                os.fchmod(fd, 0o444)
                os.fsync(fd)
                obj._marker_identity = _identity(os.fstat(fd))
                os.fsync(dirfd)
                with _FORK_LOCK:
                    fd = os.open(JOURNAL, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=dirfd)
                    obj._pins[JOURNAL] = fd
                os.fsync(fd)
                obj._journal_identity = _identity(os.fstat(fd))
                os.fsync(dirfd)
            except LedgerError:
                raise
            except OSError as exc:
                code = "REPLAY" if isinstance(exc, FileExistsError) else "PERSISTENCE"
                raise LedgerError(code, "Reservation creation failed; preserve all partial evidence",
                                  consumed=claimed or code == "REPLAY") from exc
            finally:
                os.close(dirfd)
            obj._append({"type": "INVOKED", "marker_sha256": hashlib.sha256(obj._marker).hexdigest()})
        except BaseException:
            obj._stopped = True
            obj._release_pins()
            raise
        return obj

    def _release_pins(self, *, propagate=False):
        try:
            with _FORK_LOCK:
                errors = _close_pins(self._pins)
                self._pin_finalizer.detach()
                _LIVE_LEDGERS.discard(self)
        except BaseException:
            self._stopped = self._uncertain = True
            self._complete = False
            if propagate:
                raise
            return
        if errors:
            self._stopped = self._uncertain = True
            self._complete = False
            if propagate:
                for _, exc in errors:
                    if not isinstance(exc, Exception):
                        raise exc
                raise LedgerError("PERSISTENCE", "File handle release is uncertain; continuation is forbidden",
                                  consumed=True) from errors[0][1]

    def _same_process(self):
        if os.getpid() == self._pid:
            return True
        # Check before acquiring an RLock possibly held by a vanished parent thread.
        self._mutex = threading.RLock()
        self._stopped = True
        self._release_pins()
        return False

    def _check_pins(self):
        for name, identity in ((MARKER, self._marker_identity),
                               (JOURNAL, self._journal_identity)):
            fd = self._pins.get(name)
            if fd is None:
                raise LedgerError("INTEGRITY", "Reservation evidence changed or was replaced", consumed=True)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or _identity(info) != identity:
                raise LedgerError("INTEGRITY", "Reservation evidence changed or was replaced", consumed=True)

    def close(self):
        """Dispose once without deleting evidence or granting any resume right."""
        self._same_process()
        with self._mutex:
            if not self._stopped and not self._complete:
                self._stopped = True
                self._uncertain = True
            self._release_pins(propagate=True)

    def __enter__(self):
        if not self._same_process():
            raise LedgerError("STOPPED", "This capability cannot continue or resume", consumed=True)
        with self._mutex:
            self._check_live()
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            self.close()
        except BaseException:
            if exc_type is None:
                raise

    def _check_live(self):
        if self._stopped or self._complete or os.getpid() != self._pid:
            raise LedgerError("STOPPED", "This capability cannot continue or resume", consumed=True)

    def _append(self, event):
        """Only advance memory after a checked append and successful fsync."""
        body = {"sequence": self._sequence, "previous_sha256": self._last_hash,
                "event": event}
        digest = hashlib.sha256(canonical(body)).hexdigest()
        line = canonical({**body, "sha256": digest}) + b"\n"
        dirfd = None
        try:
            _, current_root = _directory(self._authority)
            _, current_output = _directory(self._output)
            if current_root != self._root_identity or current_output != self._output_identity:
                raise LedgerError("INTEGRITY", "A bound directory changed", consumed=True)
            if len(self._journal) + len(line) > MAX_JOURNAL_BYTES:
                raise LedgerError("PERSISTENCE", "Journal byte ceiling reached", consumed=True)
            dirfd = os.open(self._authority, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            if _identity(os.fstat(dirfd)) != self._root_identity:
                raise LedgerError("INTEGRITY", "Reservation authority changed", consumed=True)
            self._check_pins()
            marker, marker_identity = _read_regular(dirfd, MARKER, 16384)
            journal, journal_identity = _read_regular(dirfd, JOURNAL, MAX_JOURNAL_BYTES)
            self._check_pins()
            if (marker != self._marker or marker_identity != self._marker_identity
                    or journal != self._journal or journal_identity != self._journal_identity):
                raise LedgerError("INTEGRITY", "Reservation evidence changed or was replaced", consumed=True)
            fd = os.open(JOURNAL, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirfd)
            try:
                info = os.fstat(fd)
                if _identity(info) != self._journal_identity or info.st_nlink != 1:
                    raise LedgerError("INTEGRITY", "Journal identity changed before append", consumed=True)
                _write_all(fd, line)
                os.fsync(fd)
            finally:
                os.close(fd)
            self._journal += line
            self._last_hash, self._sequence = digest, self._sequence + 1
        except BaseException as exc:
            self._stopped = True
            self._uncertain = True
            if isinstance(exc, (OSError, LedgerError)):
                raise LedgerError("PERSISTENCE", "Journal persistence is uncertain; continuation is forbidden",
                                  consumed=True) from exc
            raise
        finally:
            if dirfd is not None:
                os.close(dirfd)

    def _reject(self, reason):
        self._append({"type": "STOPPED", "outcome": "failed", "reason": reason})
        self._stopped = True
        raise LedgerError("ORDER", reason, consumed=True)

    def _slot(self, slot, route, references):
        expected = ORDER[self._cursor]
        if type(slot) is not str or slot != expected or slot not in _SLOT_BY_NAME:
            self._reject("Wrong slot or unfinished predecessor/control")
        specification = _SLOT_BY_NAME[slot]
        if type(route) is not str or route != specification.route or not exact(references, specification.references()):
            self._reject("Route, accepted-source, predecessor, equality or control binding differs")
        return specification

    @_mutation
    def reserve(self, slot, route, stage, *, references):
        """Durably consume an allowance before a future trusted caller could start."""
        with self._mutex:
            self._check_live()
            self._slot(slot, route, references)
            expected = {0: "construction", 1: "receiving", 3: "node"}.get(self._phase)
            if self._active is not None or stage != expected or stage not in STAGES:
                self._reject("Wrong stage, uncompleted reservation or missing promotion")
            key = (slot, stage)
            if key in self._reserved or self._counts[stage] >= 4:
                self._reject("The assigned stage allowance is already consumed")
            reservation = Reservation(self._invocation_id, self._sequence, slot, route, stage)
            self._reserved.add(key)
            self._counts[stage] += 1
            self._append({"type": "RESERVED", "slot": slot, "route": route, "stage": stage,
                          "references": _SLOT_BY_NAME[slot].references(),
                          "consumed": self._counts[stage]})
            self._active = reservation
            return reservation

    @_mutation
    def finish(self, reservation, outcome, *, cleanup_passed, evidence_sha256):
        """Record bounded caller observations; a negative/unknown result stops all work."""
        with self._mutex:
            self._check_live()
            if reservation is not self._active or self._active is None:
                self._reject("The active reservation receipt differs")
            if outcome not in OUTCOMES or type(cleanup_passed) is not bool or not _digest(evidence_sha256):
                self._reject("A stage requires a known outcome, cleanup observation and evidence digest")
            self._append({"type": "RESULT", "slot": reservation.slot, "stage": reservation.stage,
                          "reservation_sequence": reservation.sequence, "outcome": outcome,
                          "cleanup_passed_observation": cleanup_passed,
                          "evidence_sha256": evidence_sha256})
            self._active = None
            if outcome != "passed" or not cleanup_passed:
                self._append({"type": "STOPPED", "outcome": outcome if outcome != "passed" else "failed",
                              "reason": "Stage or cleanup observation did not pass"})
                self._stopped = True
                return
            self._phase = {"construction": 1, "receiving": 2, "node": 0}[reservation.stage]
            if reservation.stage == "node":
                self._cursor += 1
                if self._cursor == len(ORDER):
                    self._append({"type": "LEDGER_COMPLETE", "native_readiness": False,
                                  "admission_completed": False})
                    self._complete = True

    @_mutation
    def record_promotion(self, slot, route, *, references, outcome,
                         cleanup_passed, conditional_promotion_passed, evidence_sha256):
        """Record a transaction's observations after receiving and before Node.

        This method never mutates an accepted pointer. Pointer compare-and-swap,
        closure/equality checks and their rollback remain transaction work.
        """
        with self._mutex:
            self._check_live()
            self._slot(slot, route, references)
            if self._phase != 2 or self._active is not None:
                self._reject("Promotion requires completed construction and receiving observations")
            if (outcome not in OUTCOMES or type(cleanup_passed) is not bool
                    or type(conditional_promotion_passed) is not bool or not _digest(evidence_sha256)):
                self._reject("Promotion observations or evidence digest are invalid")
            self._append({"type": "PROMOTION_OBSERVATION", "slot": slot, "outcome": outcome,
                          "cleanup_passed_observation": cleanup_passed,
                          "conditional_promotion_passed_observation": conditional_promotion_passed,
                          "evidence_sha256": evidence_sha256})
            if outcome != "passed" or not cleanup_passed or not conditional_promotion_passed:
                self._append({"type": "STOPPED", "outcome": outcome if outcome != "passed" else "failed",
                              "reason": "Promotion observation did not pass"})
                self._stopped = True
                return
            self._phase = 3

    @_mutation
    def record_control(self, control, *, source_slot, outcome, findings,
                       accepted_closure_unchanged, evidence_sha256):
        with self._mutex:
            self._check_live()
            if control not in ("D01", "D03") or ORDER[self._cursor] != control or source_slot != "A01":
                self._reject("Control order or source slot differs")
            if (outcome not in OUTCOMES or type(findings) is not list
                    or any(type(item) is not str for item in findings)
                    or len(findings) > 32 or any(len(item) > 100 for item in findings)
                    or type(accepted_closure_unchanged) is not bool or not _digest(evidence_sha256)):
                self._reject("Control observations or evidence digest are invalid")
            required = {"D01": "CLEARANCE", "D03": "SIBLING"}[control]
            passed = (outcome == "passed" and required in findings and "STRUCTURE" not in findings
                      and accepted_closure_unchanged)
            self._append({"type": "CONTROL_OBSERVATION", "control": control, "source_slot": source_slot,
                          "outcome": outcome, "findings": list(findings), "required_finding": required,
                          "accepted_closure_unchanged_observation": accepted_closure_unchanged,
                          "observation_gate_passed": passed, "evidence_sha256": evidence_sha256})
            if not passed:
                self._append({"type": "STOPPED", "outcome": outcome if outcome != "passed" else "failed",
                              "reason": "Required control observation did not pass"})
                self._stopped = True
                return
            self._cursor += 1

    @_mutation
    def stop(self, reason, *, outcome="unknown"):
        with self._mutex:
            self._check_live()
            if outcome not in OUTCOMES[1:] or type(reason) is not str or not 1 <= len(reason) <= 1000:
                self._reject("Invalid explicit stop record")
            self._append({"type": "STOPPED", "outcome": outcome, "reason": reason})
            self._stopped = True

    def snapshot(self):
        """Report in-memory accounting, with no approval or native-result claim."""
        self._same_process()
        with self._mutex:
            return {"invocation_id": self._invocation_id, "consumed": dict(self._counts),
                    "stopped": self._stopped, "ledger_complete": self._complete,
                    "persistence_or_interruption_uncertain": self._uncertain,
                    "accounting_scope": "In-process reservation attempts, including uncertain persistence; not child starts or permission to run",
                    "next_item": None if self._stopped or self._complete else ORDER[self._cursor],
                    "native_readiness": False, "admission_completed": False}


def inspect(authority):
    """Read-only recovery: never reopen an active capability or permit resumption."""
    root, _ = _directory(authority)
    result = {"consumed": False, "journal_integrity_valid": False, "semantics_verified": False, "events": [],
              "native_readiness": False, "admission_completed": False, "resumable": False}
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in (MARKER, JOURNAL):
            try:
                os.stat(name, dir_fd=fd, follow_symlinks=False)
                result["consumed"] = True
            except FileNotFoundError:
                pass
        if not result["consumed"]:
            return result
        marker, _ = _read_regular(fd, MARKER, 16384)
        data, _ = _read_regular(fd, JOURNAL, MAX_JOURNAL_BYTES)
        marker_value = json.loads(marker)
        expected_marker_keys = {"schema", "schedule_id", "schedule_sha256", "protocol_sha256",
                                "invocation_id", "authority", "output", "component_only", "native_readiness"}
        if (type(marker_value) is not dict or set(marker_value) != expected_marker_keys
                or marker_value["schema"] != "ontokin.c201.control-ledger-invocation/0.1"
                or marker_value["schedule_id"] != SCHEDULE_ID
                or marker_value["schedule_sha256"] != SCHEDULE_SHA256
                or marker_value["protocol_sha256"] != PROTOCOL_SHA256
                or marker_value["authority"] != str(root)
                or marker_value["component_only"] is not True
                or marker_value["native_readiness"] is not False
                or type(marker_value["invocation_id"]) is not str
                or re.fullmatch(r"[0-9a-f]{32}", marker_value["invocation_id"]) is None
                or canonical(marker_value) + b"\n" != marker):
            raise ValueError("Invocation marker is not canonical C201 evidence")
        if not data or not data.endswith(b"\n"):
            raise ValueError("Missing or partial journal")
        prior = _ZERO
        for sequence, line in enumerate(data.splitlines()):
            row = json.loads(line)
            if set(row) != {"sequence", "previous_sha256", "event", "sha256"}:
                raise ValueError("Unexpected journal fields")
            digest = row.pop("sha256")
            if (type(row["sequence"]) is not int or row["sequence"] != sequence
                    or row["previous_sha256"] != prior or hashlib.sha256(canonical(row)).hexdigest() != digest
                    or canonical({**row, "sha256": digest}) != line):
                raise ValueError("Journal sequence or hash differs")
            if sequence == 0 and row["event"] != {
                    "type": "INVOKED", "marker_sha256": hashlib.sha256(marker).hexdigest()}:
                raise ValueError("Invocation marker differs")
            result["events"].append(row["event"])
            prior = digest
        result["journal_integrity_valid"] = True
    except (OSError, ValueError, TypeError, KeyError, LedgerError) as exc:
        result["error"] = str(exc)
    finally:
        os.close(fd)
    return result
