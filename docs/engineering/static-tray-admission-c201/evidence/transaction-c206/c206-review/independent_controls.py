"""Independent C206 fault controls using labeled file-only fixture scaffolding.

The scaffold constructs temporary inputs and synthetic stage files. Every oracle,
mutation and interruption below is reviewer-owned. No product child may start.
"""
from __future__ import annotations
import argparse
from contextlib import ExitStack
from dataclasses import replace
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import traceback
from unittest import mock

parser = argparse.ArgumentParser()
parser.add_argument("--repo", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
repo = Path(args.repo).resolve()
output = Path(args.output).resolve()
output.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(repo))
from prototypes.static_tray_admission_c201 import transaction as tx
from prototypes.static_tray_admission_c201 import input_lock
from prototypes.static_tray_admission_c201.schedule import SLOTS, canonical
from tests.test_static_tray_admission_c201_input_lock import Fixture
from tests.test_static_tray_admission_c201_transaction import TransactionFixture


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*argv):
    return subprocess.check_output(["git", "-C", str(repo), *argv], text=True).strip()


source = {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
          "status": git("status", "--porcelain")}
subject_paths = ["prototypes/static_tray_admission_c201/transaction.py",
                 "tests/test_static_tray_admission_c201_transaction.py"]
before = {name: sha((repo / name).read_bytes()) for name in subject_paths}
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
results = []
child_attempts = []


def reject(operation, code=None, state="REJECTED"):
    try:
        operation()
    except tx.TransactionError as exc:
        assert exc.state == state, (exc.state, state, str(exc))
        if code:
            assert exc.code == "C201-" + code, (exc.code, code, str(exc))
        return exc
    raise AssertionError("Invalid input was accepted")


def pointer(fixture, slot="A01"):
    path = Path(fixture.inputs.lock["stores"][slot]) / "state.json"
    return path.read_bytes() if path.exists() else None


def ready(fixture, slot="A01"):
    prepared = fixture.prepare(slot)
    constructed = fixture.construct(prepared)
    stage = fixture.receive(constructed)
    return prepared, constructed, stage


def mutate(path, change):
    value = json.loads(path.read_bytes())
    change(value)
    path.chmod(0o600)
    path.write_bytes(canonical(value))
    return value


def production_fixture(base):
    fixture = Fixture(base)
    fixture.lock["purpose"] = "production-inputs"
    fixture.lock["host"]["mode"] = "current-host"
    fixture.context = replace(fixture.context, purpose="production-inputs")
    for gate in input_lock.GATES:
        path = fixture.host / (gate + ".json")
        value = json.loads(path.read_bytes())
        value["purpose"] = "production-inputs"
        path.write_bytes(canonical(value))
        fixture.lock["gate_receipts"][gate] = fixture.binding(path, "host")
    fixture.repin()
    fixture.approval["purpose"] = "production-inputs"
    fixture.approval["decision"] = "APPROVE_INPUT_BINDINGS_ONLY"
    fixture.save_approval()
    return fixture


def case(name, operation, *, scaffold=True):
    record = {"name": name, "passed": False}
    try:
        with tempfile.TemporaryDirectory(prefix="c206-independent-") as base:
            operation(TransactionFixture(base) if scaffold else Path(base))
        record["passed"] = True
    except BaseException as exc:
        record["error"] = type(exc).__name__ + ": " + str(exc)
        record["traceback"] = traceback.format_exc()
    results.append(record)


def four_slots(fixture):
    expected = {
        "A01": ("ontokin", None, None, []),
        "A02": ("direct-python", "A01", None, ["A01"]),
        "A03": ("ontokin", "A02", "A01", ["A01"]),
        "A04": ("direct-python", "A03", "A02", ["A02", "A03"]),
    }
    original = {}
    for slot, (route, predecessor, source_slot, equality) in expected.items():
        accepted = fixture.accept(slot)
        receipt = tx.inspect_accepted(fixture.session, accepted)
        assert receipt["route"] == route
        assert receipt["references"]["completed_predecessor"] == predecessor
        assert receipt["references"]["accepted_source_reference"] == source_slot
        assert receipt["references"]["equality_references"] == equality
        assert not accepted.native_start_authorized and not accepted.native_readiness and not accepted.admission_completed
        store = Path(fixture.inputs.lock["stores"][slot])
        build = store / "objects" / slot
        receive = store / "objects" / (slot + "-receiving")
        assert (build / "native-startup.json").is_file()
        assert (build / "construction.process.json").is_file()
        assert (receive / "receiving.process.json").is_file()
        if source_slot:
            prior = Path(fixture.inputs.lock["stores"][source_slot]) / "objects" / source_slot
            provenance = json.loads((build / "source-provenance.json").read_bytes())
            assert provenance["source_path"] == str(prior / "source")
            for path in (prior / "source").iterdir():
                assert (build / "source" / path.name).read_bytes() == path.read_bytes()
            for filename in ("canonical-input.json", "raw.glb", "final.glb"):
                assert (build / filename).read_bytes() == (prior / filename).read_bytes()
        for earlier, raw in original.items():
            assert pointer(fixture, earlier) == raw
        original[slot] = pointer(fixture, slot)


def production_gate(base):
    fixture = production_fixture(base)
    validated = fixture.validate()
    assert validated.purpose == "production-inputs" and not validated.native_start_authorized
    reject(lambda: tx.bind_transactions(fixture.lock_path, fixture.approval_path,
                                        context=fixture.context), "NATIVE-CWD")


def constructor_gate(base):
    fixture = production_fixture(base)
    validated = fixture.validate()
    try:
        session = tx.TransactionBindings(fixture.lock_path.read_bytes(), fixture.approval_path.read_bytes(),
                                         fixture.context, validated)
        tx.prepare_transaction(session, "A01", route="ontokin", references=SLOTS[0].references())
    except (tx.TransactionError, TypeError):
        return
    raise AssertionError("Direct public construction bypassed the production binding gate")


def build_job(fixture):
    prepared = fixture.prepare("A01")
    stage = fixture.build(prepared)
    mutate(stage / "job.json", lambda row: row.update(settings_path="/unrelated/settings.json"))
    reject(lambda: tx.seal_construction(prepared, process=fixture.process("A01", "construction")), "RECEIPT")
    assert pointer(fixture) is None


def receive_job(fixture):
    _, built, stage = ready(fixture)
    mutate(stage / "job.json", lambda row: row.update(candidate="/unrelated/candidate"))
    reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")), "RECEIPT")
    assert pointer(fixture) is None


def provenance(fixture):
    prepared = fixture.prepare("A01")
    stage = fixture.build(prepared)
    mutate(stage / "source-provenance.json", lambda row: row.update(source_path="/unrelated/source"))
    reject(lambda: tx.seal_construction(prepared, process=fixture.process("A01", "construction")), "RECEIPT")


def missing_startup(fixture):
    prepared = fixture.prepare("A01")
    stage = fixture.build(prepared)
    (stage / "native-startup.json").unlink()
    reject(lambda: tx.seal_construction(prepared, process=fixture.process("A01", "construction")), "CLOSURE")


def log_receipt(fixture):
    prepared = fixture.prepare("A01")
    stage = fixture.build(prepared)
    with (stage / "construction.stdout.log").open("ab") as stream:
        stream.write(b"unaccounted retained output")
    reject(lambda: tx.seal_construction(prepared, process=fixture.process("A01", "construction")), "PROCESS")


def underlying_pid(fixture):
    prepared = fixture.prepare("A01")
    stage = fixture.build(prepared)
    mutate(stage / "construction.process.json", lambda row: row.update(pid=789))
    reject(lambda: tx.seal_construction(prepared, process=fixture.process("A01", "construction")), "PROCESS")


def source_change(fixture):
    fixture.accept("A01")
    fixture.accept("A02")
    path = Path(fixture.inputs.lock["stores"]["A01"]) / "objects/A01/source/tray.ok"
    path.chmod(0o600)
    path.write_bytes(path.read_bytes() + b"\n")
    path.chmod(0o444)
    reject(lambda: fixture.prepare("A03"))
    assert pointer(fixture, "A03") is None


def wrong_reference(fixture):
    fixture.accept("A01")
    fixture.accept("A02")
    refs = SLOTS[2].references()
    refs["accepted_source_reference"] = "A02"
    reject(lambda: tx.prepare_transaction(fixture.session, "A03", route="ontokin", references=refs,
                                         accepted=tuple(fixture.accepted)), "REFERENCE")


def same_revision_pointer(fixture):
    handle = fixture.accept("A01")
    store = Path(fixture.inputs.lock["stores"]["A01"])
    current = json.loads(handle.state_bytes)
    current["candidate"] = "objects/unrelated"
    (store / "state.json").write_bytes(canonical(current))
    reject(lambda: tx.inspect_accepted(fixture.session, handle), "POINTER")


def precommit_failure(fixture):
    _, built, _ = ready(fixture)
    with mock.patch.object(tx.os, "replace", side_effect=OSError("controlled precommit failure")):
        reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")))
    assert pointer(fixture) is None
    reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")), "REPLAY")


def lost_replace(fixture):
    _, built, _ = ready(fixture)
    original = tx.os.replace
    def replace_then_interrupt(*values, **keywords):
        original(*values, **keywords)
        raise KeyboardInterrupt("controlled interruption after real commit")
    with mock.patch.object(tx.os, "replace", side_effect=replace_then_interrupt):
        error = reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")),
                       state="UNKNOWN")
    assert pointer(fixture) is not None
    assert error.observed_state == error.intended_state == json.loads(pointer(fixture))
    reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")), "REPLAY")


def lost_promote_reply(fixture):
    _, built, _ = ready(fixture)
    original = tx._promote
    def commit_then_interrupt(*values, **keywords):
        original(*values, **keywords)
        raise KeyboardInterrupt("controlled interruption after promotion returned")
    with mock.patch.object(tx, "_promote", side_effect=commit_then_interrupt):
        error = reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")),
                       state="UNKNOWN")
    assert error.observed_state == error.intended_state == json.loads(pointer(fixture))


def failed_cleanup(fixture):
    _, built, stage = ready(fixture)
    mutate(stage / "receiving.process.json", lambda row: row["cleanup"].update(elapsed_ms=2001))
    reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")), "CLEANUP")
    assert pointer(fixture) is None


def receiving_geometry(fixture):
    _, built, stage = ready(fixture)
    def alter(row):
        node = row["native_scene"]["nodes"]["equipment-tray/pair/right/front"]
        node["world_vertices"][0][2] += 0.002
    mutate(stage / "observations.json", alter)
    reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")), "RECEIVING")
    assert pointer(fixture) is None


def fifo_supervisor(fixture):
    prepared = fixture.prepare("A01")
    stage = fixture.build(prepared)
    observation = fixture.process("A01", "construction")
    path = stage / "construction.process.json"
    path.unlink()
    os.mkfifo(path)
    reject(lambda: tx.seal_construction(prepared, process=observation))


def replaced_authority(fixture):
    root = fixture.inputs.authority
    root.rename(root.with_name("old-authority"))
    root.mkdir()
    reject(lambda: fixture.prepare("A01"), "PATH")


def expired_clock(fixture):
    prepared, built, _ = ready(fixture)
    prepared._clock.end = prepared._clock.started - 1
    reject(lambda: tx.complete_transaction(built, process=fixture.process("A01", "receiving")), state="TIMEOUT")
    assert pointer(fixture) is None


def extra_retained_file(fixture):
    handle = fixture.accept("A01")
    directory = Path(fixture.inputs.lock["stores"]["A01"]) / "objects/A01-receipt"
    directory.chmod(0o755)
    (directory / "unbound.json").write_bytes(b"{}")
    reject(lambda: tx.inspect_accepted(fixture.session, handle), "CLOSURE")


def accepted_source_alias(fixture):
    handle = fixture.accept("A01")
    candidate = Path(fixture.inputs.lock["stores"]["A01"]) / "objects/A01"
    candidate.chmod(0o755)
    (candidate / "source").rename(candidate / "source-original")
    (candidate / "source").symlink_to(candidate / "source-original", target_is_directory=True)
    reject(lambda: tx.inspect_accepted(fixture.session, handle))


controls = [
    ("four-slot closure and reference semantics", four_slots, True),
    ("validated production shape remains blocked", production_gate, False),
    ("direct construction cannot bypass binding gate", constructor_gate, False),
    ("construction job mutation", build_job, True),
    ("receiving job mutation", receive_job, True),
    ("source provenance mutation", provenance, True),
    ("missing qualified native startup", missing_startup, True),
    ("underlying process log mismatch", log_receipt, True),
    ("underlying process identity mismatch", underlying_pid, True),
    ("accepted reusable dependency mutation", source_change, True),
    ("wrong regeneration source with real predecessors", wrong_reference, True),
    ("same-revision unrelated accepted pointer", same_revision_pointer, True),
    ("precommit failure preserves prior absence", precommit_failure, True),
    ("real replace followed by interruption is unknown", lost_replace, True),
    ("promotion reply loss is unknown", lost_promote_reply, True),
    ("underlying cleanup overrun", failed_cleanup, True),
    ("actual receiving geometry mismatch", receiving_geometry, True),
    ("FIFO supervisor receipt rejects without blocking", fifo_supervisor, True),
    ("replaced reservation authority rejects", replaced_authority, True),
    ("original transaction deadline cannot restart", expired_clock, True),
    ("extra retained receipt inventory rejects", extra_retained_file, True),
    ("retained source directory alias rejects", accepted_source_alias, True),
]


def blocked_child(*values, **keywords):
    child_attempts.append("blocked")
    raise AssertionError("No product child may start")


with ExitStack() as stack:
    for target in ("subprocess.Popen", "os.fork", "os.system", "os.posix_spawn", "os.posix_spawnp"):
        stack.enter_context(mock.patch(target, side_effect=blocked_child))
    for name, operation, scaffold in controls:
        case(name, operation, scaffold=scaffold)

after = {name: sha((repo / name).read_bytes()) for name in subject_paths}
report = {"schema": "ontokin.c206.independent-cpu-controls/0.1", "source": source,
          "started_at_utc": started, "completed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "python": platform.python_version(), "platform": platform.platform(), "command": sys.argv,
          "before_bindings": before, "after_bindings": after, "input_bytes_unchanged": before == after,
          "fixture_scaffold": "tests.test_static_tray_admission_c201_transaction.TransactionFixture",
          "fixture_only": True, "production_shape_control_is_synthetic": True,
          "native_starts": 0, "receiver_starts": 0, "node_starts": 0,
          "lifecycle_starts": 0, "timed_author_starts": 0, "product_child_start_attempts": len(child_attempts),
          "controls": results, "passed": all(r["passed"] for r in results) and before == after and not child_attempts}
(output / "independent-controls.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"controls": len(results), "passed": sum(r["passed"] for r in results),
                  "failures": [r["name"] for r in results if not r["passed"]],
                  "source_bytes_unchanged": before == after, "child_attempts": len(child_attempts)}))
sys.exit(0 if report["passed"] else 1)
