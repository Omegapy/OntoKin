"""Independent CPU probes of the retained initial C206 draft; no children."""
from __future__ import annotations
from contextlib import ExitStack
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest import mock

REPO = Path(sys.argv[1]).resolve()
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from tests.test_static_tray_admission_c201_input_lock import Fixture
from tests.test_static_tray_reader_v01 import synthetic
from tests.test_static_tray_receiving_v01 import observations
from prototypes.static_tray_admission_c201.schedule import SLOTS, canonical
from prototypes.static_tray_v01.supervisor import Clock

loader = importlib.machinery.SourceFileLoader(
    "prototypes.static_tray_admission_c201.retained_draft_transaction",
    str(HERE / "transaction.draft-observed.py.txt"))
spec = importlib.util.spec_from_loader(loader.name, loader)
code = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = code
loader.exec_module(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def process(fixture, stage):
    return {"schema": code.PROCESS_SCHEMA, "purpose": "fixture-only", "slot": "A01",
            "stage": stage, "input_lock_sha256": fixture.context.lock_sha256,
            "command": copy.deepcopy(fixture.lock["commands"]["A01"][stage]),
            "process_id": 1, "started_monotonic": 10.0, "completed_monotonic": 10.1,
            "returncode": 0, "handles_closed": True,
            "cleanup": {"passed": True, "process_group_absent": True, "reaped": True}}


def setup(base):
    fixture = Fixture(base)
    session = code.bind_transactions(fixture.lock_path, fixture.approval_path, context=fixture.context)
    prepared = code.prepare_transaction(session, "A01", route="ontokin", references=SLOTS[0].references())
    return fixture, session, prepared


def construction(fixture, prepared):
    stage = Path(fixture.lock["outputs"]["A01"]["construction"])
    artifacts = {"raw.glb": synthetic(), "final.glb": synthetic(),
                 "scene.blend": b"CPU-SYNTHETIC-NATIVE-SCENE; not a Blender file\n"}
    for name, data in artifacts.items():
        (stage / name).write_bytes(data)
    native = {"passed": True, "record_sha256": sha(prepared.canonical_bytes),
              "artifacts": {name: {"sha256": sha(data), "size_bytes": len(data)}
                            for name, data in artifacts.items()}}
    (stage / "native-result.json").write_bytes(canonical(native))
    for name in ("construction.stdout.log", "construction.stderr.log"):
        (stage / name).write_bytes(b"")
    return stage


def receiving(fixture, constructed):
    store = Path(fixture.lock["stores"]["A01"])
    candidate = store / "objects/A01"
    stage = Path(fixture.lock["outputs"]["A01"]["receiving"])
    audit = json.loads((candidate / "independent-audit.json").read_bytes())
    observed = observations(audit)
    observed["input_sha256"] = {name: sha((candidate / name).read_bytes())
                                  for name in ("scene.blend", "final.glb")}
    (stage / "observations.json").write_bytes(canonical(observed))
    (stage / "review.png").write_bytes(b"CPU-SYNTHETIC-IMAGE; not a rendered review\n")
    for name in ("receiving.stdout.log", "receiving.stderr.log"):
        (stage / name).write_bytes(b"")
    return stage


results = []
with ExitStack() as stack:
    for target in ("subprocess.Popen", "os.fork", "os.system"):
        stack.enter_context(mock.patch(target, side_effect=AssertionError("No product child may start")))

    with tempfile.TemporaryDirectory(prefix="c206-independent-draft-") as base:
        fixture, session, prepared = setup(base)
        stage = construction(fixture, prepared)
        job = json.loads((stage / "job.json").read_bytes())
        job["settings_path"] = "/unrelated/settings.json"
        (stage / "job.json").write_bytes(canonical(job))
        result = {"id": "R2-build-job", "expected": "reject altered prepared job"}
        try:
            code.seal_construction(prepared, process=process(fixture, "construction"))
            result.update(observed="accepted altered job", finding_confirmed=True)
        except Exception as exc:
            result.update(observed=type(exc).__name__ + ": " + str(exc), finding_confirmed=False)
        results.append(result)

    with tempfile.TemporaryDirectory(prefix="c206-independent-draft-") as base:
        fixture, session, prepared = setup(base)
        stage = construction(fixture, prepared)
        for name in ("native-startup.json", "construction.process.json"):
            (stage / name).write_bytes(canonical({"fixture": "qualified output filename; CPU only"}))
        result = {"id": "R1-qualified-output-inventory", "expected": "allow qualified output filenames before receipt validation"}
        try:
            code.seal_construction(prepared, process=process(fixture, "construction"))
            result.update(observed="allowed", finding_confirmed=False)
        except code.TransactionError as exc:
            result.update(observed=exc.code + ": " + str(exc),
                          finding_confirmed=exc.code == "C201-CLOSURE")
        results.append(result)

    with tempfile.TemporaryDirectory(prefix="c206-independent-draft-") as base:
        fixture, session, prepared = setup(base)
        construction(fixture, prepared)
        built = code.seal_construction(prepared, process=process(fixture, "construction"))
        stage = receiving(fixture, built)
        job = json.loads((stage / "job.json").read_bytes())
        job["candidate"] = "/unrelated/candidate"
        (stage / "job.json").write_bytes(canonical(job))
        result = {"id": "R2-receiving-job", "expected": "reject altered receiver job"}
        try:
            accepted = code.complete_transaction(built, process=process(fixture, "receiving"), clock=Clock())
            result.update(observed="accepted altered receiver job", finding_confirmed=True,
                          admission_completed=accepted.admission_completed)
        except Exception as exc:
            result.update(observed=type(exc).__name__ + ": " + str(exc), finding_confirmed=False)
        results.append(result)

    with tempfile.TemporaryDirectory(prefix="c206-independent-draft-") as base:
        fixture, session, prepared = setup(base)
        construction(fixture, prepared)
        built = code.seal_construction(prepared, process=process(fixture, "construction"))
        receiving(fixture, built)
        original_replace = code.os.replace

        def commit_then_interrupt(*args, **kwargs):
            original_replace(*args, **kwargs)
            raise KeyboardInterrupt("controlled lost reply after actual pointer replacement")

        result = {"id": "R3-post-replace-interruption", "expected": "UNKNOWN after pointer commit with lost reply"}
        try:
            with mock.patch.object(code.os, "replace", side_effect=commit_then_interrupt):
                code.complete_transaction(built, process=process(fixture, "receiving"), clock=Clock())
            result.update(observed="returned success", finding_confirmed=True)
        except BaseException as exc:
            present = (Path(fixture.lock["stores"]["A01"]) / "state.json").exists()
            result.update(observed=type(exc).__name__ + ": " + str(exc),
                          state=getattr(exc, "state", None), pointer_committed=present,
                          finding_confirmed=present and getattr(exc, "state", None) != "UNKNOWN")
        results.append(result)

report = {"schema": "ontokin.c206.independent-draft-controls/0.1",
          "source_sha256": sha((HERE / "transaction.draft-observed.py.txt").read_bytes()),
          "fixture_only": True, "native_starts": 0, "receiver_starts": 0,
          "node_starts": 0, "lifecycle_starts": 0, "timed_author_starts": 0,
          "controls": results}
(HERE / "draft-controls.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"controls": len(results), "confirmed": sum(r["finding_confirmed"] for r in results)}))
