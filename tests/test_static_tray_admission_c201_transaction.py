"""Actual C201 file/closure controls, with synthetic geometry and no children."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from prototypes.static_tray_admission_c201 import transaction as tx
from prototypes.static_tray_admission_c201.schedule import SLOTS, canonical
from tests.test_static_tray_admission_c201_input_lock import Fixture
from tests.test_static_tray_reader_v01 import synthetic
from tests.test_static_tray_receiving_v01 import observations


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class TransactionFixture:
    """File-only stand-in for external stages; never native or readiness evidence."""

    def __init__(self, root):
        self.inputs = Fixture(root)
        self.session = tx.bind_transactions(self.inputs.lock_path, self.inputs.approval_path,
                                            context=self.inputs.context)
        self.accepted = []

    def prepare(self, slot):
        row = next(s for s in SLOTS if s.name == slot)
        return tx.prepare_transaction(self.session, slot, route=row.route,
                                      references=row.references(), accepted=tuple(self.accepted))

    def process(self, slot, stage):
        path = Path(self.inputs.lock["outputs"][slot][stage]) / (stage + ".process.json")
        if not path.exists():
            name = slot if stage == "construction" else slot + "-receiving"
            path = Path(self.inputs.lock["stores"][slot]) / "objects" / name / (stage + ".process.json")
        return {"schema": tx.PROCESS_SCHEMA, "purpose": self.session.validation.purpose, "slot": slot,
                "stage": stage, "input_lock_sha256": self.session.validation.lock_sha256,
                "command": deepcopy(self.inputs.lock["commands"][slot][stage]),
                "process_id": 12345, "started_monotonic": 1.0, "completed_monotonic": 1.5,
                "returncode": 0, "handles_closed": True,
                "cleanup": {"passed": True, "process_group_absent": True, "reaped": True},
                "supervisor_record_sha256": sha(path.read_bytes())}

    def write_process_record(self, slot, stage):
        output = Path(self.inputs.lock["outputs"][slot][stage])
        command = self.inputs.lock["commands"][slot][stage]
        size = sum((output / (stage + suffix)).stat().st_size for suffix in (".stdout.log", ".stderr.log"))
        value = {"argv": command["argv"], "cwd": str(output), "environment": command["environment"],
                 "label": stage, "start_monotonic": 1.0, "pid": 12345, "process_group": 12345,
                 "returncode": 0, "observed_log_bytes": size, "retained_log_bytes": size,
                 "cleanup": {"passed": True, "elapsed_ms": 0.5, "process_group_absent": True, "reaped": True},
                 "handles_closed": True, "error": None, "end_monotonic": 1.5}
        (output / (stage + ".process.json")).write_bytes(canonical(value))

    def build(self, prepared):
        stage = Path(self.inputs.lock["outputs"][prepared.slot]["construction"])
        glb = synthetic("Q01")
        for name, raw in {"raw.glb": glb, "final.glb": glb,
                          "scene.blend": b"Synthetic CPU native container; Blender was not started"}.items():
            (stage / name).write_bytes(raw)
        artifacts = {name: {"sha256": sha((stage / name).read_bytes()),
                            "size_bytes": (stage / name).stat().st_size} for name in tx.ARTIFACTS}
        job = json.loads((stage / "job.json").read_bytes())
        settings = json.loads(Path(job["settings_path"]).read_bytes())
        settings["filepath"] = str(stage / "raw.glb")
        python = {"flags": {"isolated": 0, "ignore_environment": 0, "no_user_site": 1, "no_site": 0,
                            "safe_path": True, "hash_randomization": 0, "dont_write_bytecode": 1},
                  "dont_write_bytecode": True, "sys_path": ["/fixture-only"], "executable": "/fixture-python",
                  "prefix": "/fixture", "base_prefix": "/fixture", "python_version": "Synthetic CPU receipt"}
        policy = {"exporter_sha256": "82428a0415e11c27a285fd950f63e874add5ba2f8bacc6806ed762614560fa2e",
                  "operator_context": "EXEC_DEFAULT", "operator_property_count": len(settings),
                  "debug": {"debug": False, "debug_python": False, "debug_value": 0},
                  "requested_log_level": -1, "resolved_log_level": 20, "action_filter": False,
                  "action_filter_policy": "initialize-empty-properties-before-explicit-false",
                  "omitted_operator_properties": []}
        startup = {"schema": "ontokin.static-tray.native-startup/0.1.0", "phase": "BEFORE_EXPORT",
                   "delivery_state": "NOT_EXPORTED", "blender_version": [4, 5, 3], "build_hash": "67807e1800cc",
                   "python_startup": python, "operator_settings": settings, "exporter_policy": policy,
                   "action_filter_initialization": {"action_count": 0, "scene_count": 1, "filter_count": 0, "active_index": 0},
                   "record_sha256": sha(prepared.canonical_bytes), "settings_sha256": job["settings_sha256"]}
        (stage / "native-startup.json").write_bytes(canonical(startup))
        exporter = {**policy, "logging_observed": {"logger_level": 20, "error_logger_level": 40},
                    "action_filter_properties_removed": True, "startup_receipt_sha256": sha(canonical(startup))}
        nodes = sorted("equipment-tray/pair/" + side + suffix for side in ("left", "right")
                       for suffix in ("", "/back", "/base", "/front", "/left-wall", "/payload", "/right-wall"))
        (stage / "native-result.json").write_bytes(canonical({"schema": "ontokin.static-tray.native/0.1.0",
            "passed": True, "blender_version": [4, 5, 3], "build_hash": "67807e1800cc", "python_version": python["python_version"],
            "python_startup": python, "threads": 2, "operator_settings": settings, "exporter_policy": exporter,
            "objects": nodes, "record_sha256": sha(prepared.canonical_bytes), "physics_world": False, "artifacts": artifacts}))
        for name in ("construction.stdout.log", "construction.stderr.log"):
            (stage / name).write_bytes(b"Synthetic CPU fixture\n")
        self.write_process_record(prepared.slot, "construction")
        return stage

    def construct(self, prepared):
        self.build(prepared)
        return tx.seal_construction(prepared, process=self.process(prepared.slot, "construction"))

    def receive(self, constructed):
        slot = constructed.prepared.slot
        stage = Path(self.inputs.lock["outputs"][slot]["receiving"])
        candidate = Path(self.inputs.lock["stores"][slot]) / "objects" / slot
        audit = json.loads((candidate / "independent-audit.json").read_bytes())
        measured = observations(audit)
        measured["input_sha256"] = {n: sha((candidate / n).read_bytes()) for n in ("scene.blend", "final.glb")}
        (stage / "observations.json").write_bytes(canonical(measured))
        (stage / "review.png").write_bytes(b"Synthetic CPU image; not a rendered view")
        for name in ("receiving.stdout.log", "receiving.stderr.log"):
            (stage / name).write_bytes(b"Synthetic CPU fixture\n")
        self.write_process_record(slot, "receiving")
        return stage

    def accept(self, slot):
        prepared = self.prepare(slot)
        constructed = self.construct(prepared)
        self.receive(constructed)
        handle = tx.complete_transaction(constructed, process=self.process(slot, "receiving"))
        self.accepted.append(handle)
        return handle


class TransactionControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ontokin-c206-cpu-")
        self.addCleanup(self.temp.cleanup)
        for target in ("subprocess.Popen", "os.fork", "os.system", "os.posix_spawn", "os.posix_spawnp"):
            self.enterContext(mock.patch(target, side_effect=AssertionError("No child may start")))
        self.fixture = TransactionFixture(self.temp.name)

    def reject(self, operation, code=None, state="REJECTED"):
        with self.assertRaises(tx.TransactionError) as caught:
            operation()
        if code:
            self.assertEqual(caught.exception.code, "C201-" + code)
        self.assertEqual(caught.exception.state, state)
        return caught.exception

    def state(self, slot):
        p = Path(self.fixture.inputs.lock["stores"][slot]) / "state.json"
        return p.read_bytes() if p.exists() else None

    def mutate_file(self, path, data):
        path.chmod(0o600)
        path.write_bytes(data)
        path.chmod(0o444)

    def test_four_real_component_transactions_from_synthetic_stage_files(self):
        handles = [self.fixture.accept(slot.name) for slot in SLOTS]
        for handle in handles:
            receipt = tx.inspect_accepted(self.fixture.session, handle)
            self.assertEqual(receipt["state"], "TRANSACTION_ACCEPTED")
            self.assertFalse(handle.native_start_authorized)
            self.assertFalse(handle.native_readiness)
            self.assertFalse(handle.admission_completed)
        for current, baseline in (("A03", "A01"), ("A04", "A02")):
            candidate = Path(self.fixture.inputs.lock["stores"][current]) / "objects" / current
            source = json.loads((candidate / "source-provenance.json").read_bytes())["source_path"]
            self.assertEqual(Path(source), Path(self.fixture.inputs.lock["stores"][baseline]) / "objects" / baseline / "source")
            self.assertEqual(json.loads((candidate / "equality-checks.json").read_bytes())[0]["reference"], baseline)
        self.assertEqual([h.state_bytes for h in handles[:2]], [self.state("A01"), self.state("A02")])

    def test_wrong_route_rejected_before_staging(self):
        self.reject(lambda: tx.prepare_transaction(self.fixture.session, "A01", route="direct-python", references=SLOTS[0].references()), "REFERENCE")
        self.assertEqual(os.listdir(self.fixture.inputs.lock["stores"]["A01"]), [])

    def test_wrong_schedule_predecessor_rejected(self):
        references = SLOTS[0].references()
        references["completed_predecessor"] = "A02"
        self.reject(lambda: tx.prepare_transaction(self.fixture.session, "A01", route="ontokin", references=references), "REFERENCE")

    def test_wrong_regeneration_reference_rejected(self):
        references = SLOTS[2].references()
        references["accepted_source_reference"] = "A02"
        self.reject(lambda: tx.prepare_transaction(self.fixture.session, "A03", route="ontokin", references=references), "REFERENCE")

    def test_wrong_equality_reference_rejected(self):
        references = SLOTS[3].references()
        references["equality_references"] = ["A03", "A02"]
        self.reject(lambda: tx.prepare_transaction(self.fixture.session, "A04", route="direct-python", references=references), "REFERENCE")

    def test_missing_prior_rejected(self):
        self.reject(lambda: self.fixture.prepare("A02"), "REFERENCE")

    def test_extra_or_duplicate_prior_rejected(self):
        fake = tx.AcceptedTransaction("A01", "0" * 64, b"{}")
        self.reject(lambda: tx.prepare_transaction(self.fixture.session, "A02", route="direct-python",
             references=SLOTS[1].references(), accepted=(fake, fake)), "REFERENCE")

    def test_wrong_prior_type_rejected(self):
        self.reject(lambda: tx.prepare_transaction(self.fixture.session, "A02", route="direct-python",
             references=SLOTS[1].references(), accepted=({},)), "REFERENCE")

    def test_unknown_or_historical_slot_rejected(self):
        for name in ("A05", "N01", None):
            with self.subTest(name=name):
                self.reject(lambda: tx.prepare_transaction(self.fixture.session, name, route="ontokin", references=SLOTS[0].references()), "REFERENCE")

    def test_changed_runtime_dependency_after_binding_rejected(self):
        (self.fixture.inputs.host / "transitive-library").write_text("changed")
        self.reject(lambda: self.fixture.prepare("A01"))

    def test_missing_runtime_dependency_after_binding_rejected(self):
        (self.fixture.inputs.host / "transitive-library").unlink()
        self.reject(lambda: self.fixture.prepare("A01"))

    def test_changed_frozen_source_after_binding_rejected(self):
        path = self.fixture.inputs.repo / "fixtures/static_tray_v01/native/Q01/ontokin/main.ok"
        path.write_bytes(path.read_bytes() + b"\n")
        self.reject(lambda: self.fixture.prepare("A01"))

    def test_replaced_store_directory_rejected(self):
        store = Path(self.fixture.inputs.lock["stores"]["A01"])
        store.rename(store.with_name("old-store"))
        store.mkdir()
        self.reject(lambda: self.fixture.prepare("A01"), "PATH")

    def test_symlink_store_rejected(self):
        store = Path(self.fixture.inputs.lock["stores"]["A01"])
        other = store.with_name("other-store")
        store.rename(other)
        store.symlink_to(other, target_is_directory=True)
        self.reject(lambda: self.fixture.prepare("A01"))

    def test_repeat_prepare_rejected(self):
        self.fixture.prepare("A01")
        self.reject(lambda: self.fixture.prepare("A01"), "REPLAY")

    def test_unrelated_null_revision_pointer_is_not_empty(self):
        prepared = self.fixture.prepare("A01")
        self.fixture.build(prepared)
        path = Path(self.fixture.inputs.lock["stores"]["A01"]) / "state.json"
        old = canonical({"revision": None, "unrelated": True})
        path.write_bytes(old)
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "POINTER")
        self.assertEqual(path.read_bytes(), old)

    def test_missing_artifact_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        (stage / "scene.blend").unlink()
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "CLOSURE")
        self.assertIsNone(self.state("A01"))

    def test_extra_artifact_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        (stage / "unbound.txt").write_text("unbound")
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "CLOSURE")

    def test_changed_native_receipt_binding_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        native = json.loads((stage / "native-result.json").read_bytes())
        native["artifacts"]["final.glb"]["sha256"] = "0" * 64
        (stage / "native-result.json").write_bytes(canonical(native))
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "RECEIPT")

    def test_changed_source_before_sealing_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        (stage / "source/tray.ok").write_text("changed")
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "SOURCE")

    def test_fifo_artifact_rejected_without_blocking(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        (stage / "raw.glb").unlink()
        os.mkfifo(stage / "raw.glb")
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")))

    def test_hardlinked_artifact_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        os.link(stage / "raw.glb", Path(self.temp.name) / "alias")
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")))

    def test_failed_construction_cleanup_rejected(self):
        prepared = self.fixture.prepare("A01")
        self.fixture.build(prepared)
        process = self.fixture.process("A01", "construction")
        process["cleanup"]["process_group_absent"] = False
        self.reject(lambda: tx.seal_construction(prepared, process=process), "CLEANUP")
        self.assertIsNone(self.state("A01"))

    def test_unrelated_process_observation_rejected(self):
        prepared = self.fixture.prepare("A01")
        self.fixture.build(prepared)
        process = self.fixture.process("A01", "construction")
        process["slot"] = "A02"
        self.reject(lambda: tx.seal_construction(prepared, process=process), "PROCESS")

    def test_failed_receiver_measurements_preserve_pointer(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        receiving = self.fixture.receive(constructed)
        measured = json.loads((receiving / "observations.json").read_bytes())
        measured["native_scene"]["nodes"]["equipment-tray/pair/right/base"]["world_vertices"][0][0] += 0.01
        (receiving / "observations.json").write_bytes(canonical(measured))
        self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "RECEIVING")
        self.assertIsNone(self.state("A01"))

    def test_unrelated_receiver_inputs_rejected(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        receiving = self.fixture.receive(constructed)
        measured = json.loads((receiving / "observations.json").read_bytes())
        measured["input_sha256"]["scene.blend"] = "0" * 64
        (receiving / "observations.json").write_bytes(canonical(measured))
        self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "RECEIPT")

    def test_failed_receiver_cleanup_preserves_pointer(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        self.fixture.receive(constructed)
        process = self.fixture.process("A01", "receiving")
        process["handles_closed"] = False
        self.reject(lambda: tx.complete_transaction(constructed, process=process), "PROCESS")
        self.assertIsNone(self.state("A01"))

    def test_unrelated_pointer_preserved_before_promotion(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        self.fixture.receive(constructed)
        pointer = Path(self.fixture.inputs.lock["stores"]["A01"]) / "state.json"
        original = canonical({"revision": "other", "candidate": "foreign"})
        pointer.write_bytes(original)
        self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "POINTER")
        self.assertEqual(pointer.read_bytes(), original)

    def test_pointer_commit_failure_preserves_absence(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        self.fixture.receive(constructed)
        with mock.patch.object(tx.os, "replace", side_effect=OSError("Controlled pre-commit failure")):
            self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")))
        self.assertIsNone(self.state("A01"))
        self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "REPLAY")

    def test_post_commit_readback_failure_is_unknown(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        self.fixture.receive(constructed)
        original = tx._pointer
        def lost_reply(store):
            result = original(store)
            if result is not None:
                raise OSError("Controlled reply loss after committed replacement")
            return result
        with mock.patch.object(tx, "_pointer", side_effect=lost_reply):
            error = self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "PROMOTION", "UNKNOWN")
        self.assertIsNotNone(self.state("A01"))
        self.assertIsNone(error.observed_state)
        self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "REPLAY")

    def test_changed_accepted_source_blocks_regeneration(self):
        self.fixture.accept("A01")
        self.fixture.accept("A02")
        candidate = Path(self.fixture.inputs.lock["stores"]["A01"]) / "objects/A01"
        self.mutate_file(candidate / "source/tray.ok", b"changed")
        self.reject(lambda: self.fixture.prepare("A03"))
        self.assertIsNone(self.state("A03"))

    def test_missing_accepted_dependency_blocks_regeneration(self):
        self.fixture.accept("A01")
        self.fixture.accept("A02")
        source = Path(self.fixture.inputs.lock["stores"]["A01"]) / "objects/A01/source"
        source.chmod(0o755)
        (source / "tray.ok").unlink()
        self.reject(lambda: self.fixture.prepare("A03"), "CLOSURE")

    def test_same_revision_changed_pointer_blocks_regeneration(self):
        self.fixture.accept("A01")
        self.fixture.accept("A02")
        pointer = Path(self.fixture.inputs.lock["stores"]["A01"]) / "state.json"
        state = json.loads(pointer.read_bytes())
        state["candidate"] = "objects/unrelated"
        pointer.write_bytes(canonical(state))
        self.reject(lambda: self.fixture.prepare("A03"), "POINTER")

    def test_changed_retained_receipt_blocks_regeneration(self):
        self.fixture.accept("A01")
        self.fixture.accept("A02")
        receipt = Path(self.fixture.inputs.lock["stores"]["A01"]) / "objects/A01/native-result.json"
        self.mutate_file(receipt, b"{}")
        self.reject(lambda: self.fixture.prepare("A03"))

    def test_baseline_pointer_mutation_during_regeneration_blocks_promotion(self):
        self.fixture.accept("A01")
        self.fixture.accept("A02")
        constructed = self.fixture.construct(self.fixture.prepare("A03"))
        self.fixture.receive(constructed)
        pointer = Path(self.fixture.inputs.lock["stores"]["A01"]) / "state.json"
        pointer.write_bytes(pointer.read_bytes() + b"\n")
        self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A03", "receiving")), "POINTER")
        self.assertIsNone(self.state("A03"))

    def test_read_only_inspection_rejects_forged_handle(self):
        handle = self.fixture.accept("A01")
        self.reject(lambda: tx.inspect_accepted(self.fixture.session, replace(handle, receipt_sha256="0" * 64)), "RECEIPT")

    def test_failed_native_validation_is_terminal(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        (stage / "final.glb").unlink()
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")))
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "REPLAY")

    def test_changed_construction_job_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        job = json.loads((stage / "job.json").read_bytes())
        job["settings_path"] = "/unrelated/settings.json"
        (stage / "job.json").write_bytes(canonical(job))
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "RECEIPT")

    def test_changed_source_provenance_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        value = json.loads((stage / "source-provenance.json").read_bytes())
        value["references"]["accepted_source_reference"] = "A02"
        (stage / "source-provenance.json").write_bytes(canonical(value))
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "RECEIPT")

    def test_changed_receiving_job_rejected(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        receiving = self.fixture.receive(constructed)
        job = json.loads((receiving / "job.json").read_bytes())
        job["candidate"] = "/unrelated/candidate"
        (receiving / "job.json").write_bytes(canonical(job))
        self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "RECEIPT")
        self.assertIsNone(self.state("A01"))

    def test_changed_native_startup_policy_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        startup = json.loads((stage / "native-startup.json").read_bytes())
        startup["exporter_policy"]["action_filter"] = True
        (stage / "native-startup.json").write_bytes(canonical(startup))
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "RECEIPT")

    def test_unrelated_underlying_supervisor_receipt_rejected(self):
        prepared = self.fixture.prepare("A01")
        stage = self.fixture.build(prepared)
        record = json.loads((stage / "construction.process.json").read_bytes())
        record["cwd"] = "/unrelated/output"
        (stage / "construction.process.json").write_bytes(canonical(record))
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), "PROCESS")

    def test_actual_replace_then_interruption_is_unknown(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        self.fixture.receive(constructed)
        original = tx.os.replace
        def interrupted(*args, **kwargs):
            original(*args, **kwargs)
            raise KeyboardInterrupt("Controlled interruption after actual replacement")
        with mock.patch.object(tx.os, "replace", side_effect=interrupted):
            self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "PROMOTION", "UNKNOWN")
        self.assertIsNotNone(self.state("A01"))

    def test_completed_promotion_then_lost_return_is_unknown(self):
        constructed = self.fixture.construct(self.fixture.prepare("A01"))
        self.fixture.receive(constructed)
        original = tx._promote
        def interrupted(*args, **kwargs):
            original(*args, **kwargs)
            raise KeyboardInterrupt("Controlled lost return after successful promotion")
        with mock.patch.object(tx, "_promote", side_effect=interrupted):
            self.reject(lambda: tx.complete_transaction(constructed, process=self.fixture.process("A01", "receiving")), "FINALIZATION", "UNKNOWN")
        self.assertIsNotNone(self.state("A01"))

    def test_constructor_cannot_bypass_validated_factory(self):
        fixture = self.fixture.inputs
        self.reject(lambda: tx.TransactionBindings(fixture.lock_path.read_bytes(), fixture.approval_path.read_bytes(),
                                                   fixture.context, fixture.validate()), "BINDING")

    def test_production_shaped_cpu_transactions_grant_no_native_authority(self):
        # These purpose strings exercise the binding path using synthetic files
        fixture = self.fixture.inputs
        fixture.context = replace(fixture.context, purpose="production-inputs")
        fixture.lock["purpose"] = "production-inputs"
        fixture.lock["host"]["mode"] = "current-host"
        for gate, binding in fixture.lock["gate_receipts"].items():
            path = fixture.host / binding["path"]
            value = json.loads(path.read_bytes())
            value["purpose"] = "production-inputs"
            path.write_bytes(canonical(value))
            fixture.lock["gate_receipts"][gate] = fixture.binding(path, "host")
        fixture.repin()
        fixture.approval["purpose"] = "production-inputs"
        fixture.approval["decision"] = "APPROVE_INPUT_BINDINGS_ONLY"
        fixture.save_approval()
        self.assertEqual(fixture.validate().purpose, "production-inputs")
        self.fixture.session = tx.bind_transactions(fixture.lock_path, fixture.approval_path,
                                                    context=fixture.context)
        self.assertFalse(self.fixture.session.validation.native_start_authorized)
        self.assertFalse(self.fixture.session.validation.native_readiness)
        self.assertFalse(self.fixture.session.validation.admission_completed)
        self.assertEqual(os.listdir(fixture.lock["stores"]["A01"]), [])
        for slot in SLOTS:
            handle = self.fixture.accept(slot.name)
            receipt = tx.inspect_accepted(self.fixture.session, handle)
            self.assertEqual(receipt["purpose"], "production-inputs")
            self.assertFalse(handle.native_start_authorized)
            self.assertFalse(handle.native_readiness)
            self.assertFalse(handle.admission_completed)

    def test_expired_original_clock_cannot_be_restarted(self):
        prepared = self.fixture.prepare("A01")
        self.fixture.build(prepared)
        prepared._clock.end = prepared._clock.started
        self.reject(lambda: tx.seal_construction(prepared, process=self.fixture.process("A01", "construction")), state="TIMEOUT")


if __name__ == "__main__":
    unittest.main()
