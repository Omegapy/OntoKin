"""Immutable candidate closures and one expected-predecessor commit point."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import uuid

from .supervisor import Stop, inventory, json_bytes, sha256_file


def read_state(store):
    path = Path(store) / "state.json"
    if not path.exists():
        return None
    if path.is_symlink() or path.stat().st_nlink != 1 or path.stat().st_size > 32768:
        raise Stop("OTRAY-E-BINDING", "Unsafe accepted pointer")
    return json.loads(path.read_bytes())


def revision(state):
    return None if state is None else state["revision"]


def seal_candidate(stage, store, identity):
    stage, store = Path(stage), Path(store)
    rows = inventory(stage)
    for name, row in rows.items():
        row["sha256"] = sha256_file(stage / name)
    manifest = {"schema": "ontokin.static-tray.candidate/0.1.0", "files": rows}
    data = json_bytes(manifest)
    (stage / "closure.json").write_bytes(data)
    destination = store / "objects" / identity
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise Stop("OTRAY-E-BINDING", "Immutable candidate already exists")
    for path in stage.rglob("*"):
        if path.is_file():
            with path.open("rb") as stream:
                os.fsync(stream.fileno())
            path.chmod(0o444)
    stage.rename(destination)
    for path in sorted(destination.rglob("*"), reverse=True):
        if path.is_dir():
            path.chmod(0o555)
    destination.chmod(0o555)
    return destination, hashlib.sha256(data).hexdigest()


def verify_candidate(candidate):
    candidate = Path(candidate)
    manifest = json.loads((candidate / "closure.json").read_bytes())
    actual = inventory(candidate)
    if set(actual) != set(manifest["files"]) | {"closure.json"}:
        raise Stop("OTRAY-E-BINDING", "Sealed candidate inventory changed")
    for name, row in manifest["files"].items():
        path = candidate / name
        if path.stat().st_size != row["size_bytes"] or sha256_file(path) != row["sha256"]:
            raise Stop("OTRAY-E-BINDING", "Sealed candidate bytes changed: " + name)
        if stat.S_IMODE(path.stat().st_mode) != 0o444:
            raise Stop("OTRAY-E-BINDING", "Sealed candidate mode changed: " + name)
    return manifest


def promote(store, *, expected, state, clock, cleanup_records, lost_reply=False):
    """Serialize only pointer promotion; all process cleanup precedes this call."""
    store = Path(store)
    if not cleanup_records or any(not p.get("handles_closed") or not p.get("cleanup", {}).get("passed")
                                  for p in cleanup_records):
        raise Stop("OTRAY-E-BACKEND", "Unverified cleanup blocks promotion")
    deadline = clock.stage(3000)
    with (store / ".promotion-lock").open("a+b") as guard:
        while True:
            clock.check(deadline)
            try:
                fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(0.01)
        if revision(read_state(store)) != expected:
            raise Stop("OTRAY-E-STALE", "Accepted predecessor changed before promotion")
        temp = store / (".state-" + uuid.uuid4().hex)
        replaced = False
        try:
            with temp.open("xb") as stream:
                stream.write(json_bytes(state))
                stream.flush()
                os.fsync(stream.fileno())
            clock.check(deadline)
            os.replace(temp, store / "state.json")
            replaced = True
            descriptor = os.open(store, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if lost_reply:
                raise Stop("OTRAY-E-BINDING", "Controlled lost promotion reply", "UNKNOWN")
            return {"promoted": True, "state": read_state(store)}
        except BaseException as exc:
            if replaced:
                unknown = Stop("OTRAY-E-BINDING", "Promotion reply is uncertain after pointer replacement: " + str(exc), "UNKNOWN")
                unknown.intended_state = state
                try:
                    unknown.observed_state = read_state(store)
                except BaseException:
                    unknown.observed_state = None
                raise unknown from exc
            raise
        finally:
            if temp.exists():
                temp.unlink()


def append_event(path, event, *, clock):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise Stop("OTRAY-E-BINDING", "Ledger cannot be a symlink")
    with path.open("a+b") as stream:
        while True:
            clock.check()
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(0.01)
        stream.seek(0, os.SEEK_END)
        if stream.tell() > 4*1024*1024:
            raise Stop("OTRAY-E-RESOURCE", "Attempt ledger exceeds its fixed bound")
        stream.seek(0)
        records = [json.loads(line) for line in stream if line.strip()]
        slot_records = [row for row in records if row["slot"] == event["slot"]]
        terminals = {"ACCEPTED", "REJECTED", "TIMEOUT", "CANCELLED", "UNKNOWN"}
        if any(row["state"] in terminals for row in slot_records):
            raise Stop("OTRAY-E-RESOURCE", "An attempt already has a terminal outcome")
        if event["state"] == "RESERVED" and slot_records:
            raise Stop("OTRAY-E-RESOURCE", "Assigned attempt slot is already reserved")
        allowed = {None:{"RESERVED"}, "RESERVED":{"STARTED","REJECTED","TIMEOUT","CANCELLED","UNKNOWN"},
                   "STARTED":{"BUILT_PENDING_RECEIVING","REJECTED","TIMEOUT","CANCELLED","UNKNOWN"},
                   "BUILT_PENDING_RECEIVING":{"RECEIVING","REJECTED","TIMEOUT","CANCELLED","UNKNOWN"},
                   "RECEIVING":terminals}
        previous = slot_records[-1]["state"] if slot_records else None
        if event["state"] not in allowed.get(previous,set()):
            raise Stop("OTRAY-E-BINDING", "Illegal attempt-state transition")
        stream.seek(0, os.SEEK_END)
        payload = json_bytes(event) + b"\n"
        if stream.tell()+len(payload) > 4*1024*1024:
            raise Stop("OTRAY-E-RESOURCE", "Attempt ledger append exceeds its fixed bound")
        clock.check()
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())

