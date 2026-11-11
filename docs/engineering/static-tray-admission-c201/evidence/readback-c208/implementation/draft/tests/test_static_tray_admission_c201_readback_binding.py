"""CPU-only C208 binding controls with synthetic Node observations and no child."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from prototypes.static_tray_admission_c201 import readback_binding as rb
from prototypes.static_tray_admission_c201 import transaction as tx
from prototypes.static_tray_admission_c201.schedule import SLOTS, canonical
from tests.test_static_tray_admission_c201_transaction import TransactionFixture


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ReadbackFixture:
    """Explicit file fixture; the probe and process records are never execution evidence."""

    def __init__(self, root):
        self.native = TransactionFixture(root)
        self.bindings = rb.bind_readbacks(self.native.session)

    def prepare(self, slot="A01"):
        accepted = self.native.accept(slot)
        prepared = rb.prepare_readback(self.bindings, slot, accepted=accepted)
        return prepared

    def probe(self, prepared):
        job = json.loads(prepared.job_bytes)
        audit = json.loads(Path(job["audit"]["path"]).read_bytes())
        nodes, measurements = {}, []

        def measure(name, field, value, expected, threshold):
            measurements.append({"semantic_id": name, "field": field, "actual": value,
                                 "expected": expected, "difference": abs(value - expected),
                                 "threshold": threshold, "passed": abs(value - expected) <= threshold})

        for name, ref in sorted(audit["nodes"].items()):
            row = {"original_name": name, "importer_name": name.replace("/", "_"),
                   "extras": deepcopy(ref["extras"]), "world_matrix": deepcopy(ref["world_matrix"]),
                   "children": sorted(ref["children"]),
                   "parent": None if ref["extras"]["role"] == "tray-root" else "/".join(ref["extras"]["owner_id"])}
            nodes[name] = row
            for i in range(4):
                for j in range(4):
                    measure(name, f"matrix_{i}_{j}", row["world_matrix"][i][j], ref["world_matrix"][i][j],
                            0.000005 if j == 3 and i < 3 else 0.000001)
            if "world_vertices" not in ref:
                continue
            row.update({key: deepcopy(ref[key]) for key in ("positions", "normals", "world_vertices", "indices", "material")})
            for i, point in enumerate(ref["world_vertices"]):
                for axis, coordinate in enumerate(point):
                    measure(name, f"world_vertex_{i}_{axis}", coordinate, coordinate, 0.000005)
                    normal = ref["normals"][i][axis]
                    measure(name, f"normal_{i}_{axis}", normal, normal, 0.000001)
            bounds = [[fn(point[axis] for point in ref["world_vertices"]) for axis in range(3)] for fn in (min, max)]
            row["world_bounds"] = bounds
            for axis in range(3):
                measure(name, f"world_min_{axis}", bounds[0][axis], bounds[0][axis], 0.000005)
                measure(name, f"world_max_{axis}", bounds[1][axis], bounds[1][axis], 0.000005)
                size = bounds[1][axis] - bounds[0][axis]
                measure(name, f"world_size_{axis}", size, size, 0.000005)
        probe = {k: deepcopy(job[k]) for k in ("purpose", "slot", "route", "case", "source", "protocol_sha256",
                 "schedule_sha256", "input_lock_sha256", "accepted_revision", "accepted_pointer_sha256",
                 "transaction_receipt_sha256", "checks", "limits", "scope")}
        probe.update(schema=rb.PROBE_SCHEMA, state="PASSED", passed=True, job_sha256=sha(prepared.job_bytes),
                     artifact_sha256=job["artifact"]["sha256"], audit_sha256=job["audit"]["sha256"],
                     node="v24.22.1", native_starts=0, exports=0, input_preserved=True,
                     khronos={"version": "2.0.0-dev.3.10", "passed": True,
                              "report": {"validatorVersion": "2.0.0-dev.3.10", "uri": "final.glb",
                                         "issues": {"numErrors": 0, "numWarnings": 0, "numInfos": 0, "numHints": 0,
                                                    "messages": [], "truncated": False}}},
                     three={"version": "0.186.1", "revision": "186", "passed": True,
                            "node_count": 14, "mesh_count": 12, "animations": 0, "scenes": 1, "cameras": 0,
                            "findings": [], "measurements": measurements, "nodes": nodes,
                            "position_tolerance_m": 0.000005, "matrix_tolerance": 0.000001, "naming": rb.NAMING,
                            "unsupported_objects": [], "textures": [], "external_resources": []})
        return probe

    def populate(self, prepared, probe=None):
        job = json.loads(prepared.job_bytes)
        Path(job["outputs"]["probe"]).write_bytes(canonical(self.probe(prepared) if probe is None else probe))
        for role in ("stdout", "stderr"):
            Path(job["outputs"][role]).write_bytes(b"Synthetic CPU observation; Node was not started\n")
        self.native.write_process_record(prepared.slot, "node")
        observation = self.native.process(prepared.slot, "node")
        observation.update(requested_limits=dict(rb.LIMITS), effective_limits=dict(rb.LIMITS))
        return observation


class ReadbackBindingControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ontokin-c208-readback-")
        self.addCleanup(self.temp.cleanup)
        for target in ("subprocess.Popen", "os.fork", "os.system", "os.posix_spawn", "os.posix_spawnp"):
            self.enterContext(mock.patch(target, side_effect=AssertionError("No child may start")))
        self.fixture = ReadbackFixture(self.temp.name)
        self.prepared = self.fixture.prepare()
        self.job = json.loads(self.prepared.job_bytes)
        self.pointer = Path(self.fixture.native.inputs.lock["stores"]["A01"]) / "state.json"
        self.pointer_before = self.pointer.read_bytes()

    def reject(self, operation, code=None, state="REJECTED"):
        with self.assertRaises(rb.ReadbackError) as caught:
            operation()
        if code:
            self.assertEqual(caught.exception.code, "C201-READBACK-" + code)
        self.assertEqual(caught.exception.state, state)
        self.assertEqual(self.pointer.read_bytes(), self.pointer_before)
        return caught.exception

    def bad_probe(self, change, code="RESULT"):
        probe = self.fixture.probe(self.prepared)
        change(probe)
        process = self.fixture.populate(self.prepared, probe)
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), code)

    def test_actual_four_slot_bindings_and_measurements_without_authority(self):
        prepared = self.prepared
        for slot in SLOTS:
            if slot.name != "A01":
                prepared = self.fixture.prepare(slot.name)
            result = rb.verify_readback_result(prepared, process=self.fixture.populate(prepared))
            self.assertEqual(result.state, "BINDINGS_VERIFIED")
            self.assertEqual(result.measurement_count, 2060)
            self.assertEqual(len(result.output_bindings), 5)
            self.assertEqual(result.accepted_pointer_sha256, sha(prepared.accepted.state_bytes))
            for key in ("authenticated_execution", "node_start_authorized", "native_start_authorized",
                        "native_readiness", "admission_completed", "next_slot_authorized"):
                self.assertFalse(getattr(result, key))
            self.assertEqual(rb.inspect_readback_job(prepared), json.loads(prepared.job_bytes))

    def test_job_names_exact_accepted_bytes_outputs_flags_limits(self):
        self.assertEqual(self.job["command"]["cwd"], self.job["command"]["output"])
        self.assertEqual(self.job["command"]["argv"][-1], self.job["outputs"]["job"])
        self.assertEqual(self.job["command"]["argv"][1:3], ["--no-addons", "--max-old-space-size=256"])
        self.assertEqual(self.job["limits"]["child_work_ms"], 28000)
        self.assertEqual(self.job["artifact"]["sha256"], sha(Path(self.job["artifact"]["path"]).read_bytes()))
        self.assertEqual(self.job["audit"]["sha256"], sha(Path(self.job["audit"]["path"]).read_bytes()))
        self.assertFalse(self.prepared.next_slot_authorized)

    def test_factory_rejects_arbitrary_constructor(self):
        self.reject(lambda: rb.ReadbackBindings(self.fixture.native.session), "BINDING")

    def test_wrong_slot_handle_cannot_prepare(self):
        self.reject(lambda: rb.prepare_readback(self.fixture.bindings, "A02", accepted=self.prepared.accepted), "REFERENCE")

    def test_duplicate_prepare_rejects(self):
        self.reject(lambda: rb.prepare_readback(self.fixture.bindings, "A01", accepted=self.prepared.accepted), "REPLAY")

    def test_reconstructed_handle_rejects(self):
        self.reject(lambda: rb.inspect_readback_job(replace(self.prepared)), "REPLAY")

    def test_edited_job_rejects(self):
        changed = deepcopy(self.job);changed["accepted_revision"] = "sha256:" + "0" * 64
        Path(self.job["outputs"]["job"]).write_bytes(canonical(changed))
        self.reject(lambda: rb.inspect_readback_job(self.prepared), "JOB")

    def test_result_wrong_slot_rejects(self):
        self.bad_probe(lambda p: p.update(slot="A02"))

    def test_historical_twelve_slot_result_rejects(self):
        self.bad_probe(lambda p: p.update(schema="ontokin.static-tray.external-readback/0.1.0", slot="N01"))

    def test_result_wrong_source_revision_rejects(self):
        self.bad_probe(lambda p: p["source"].update(commit="3" * 40))

    def test_result_wrong_accepted_revision_rejects(self):
        self.bad_probe(lambda p: p.update(accepted_revision="sha256:" + "0" * 64))

    def test_result_wrong_job_digest_rejects(self):
        self.bad_probe(lambda p: p.update(job_sha256="0" * 64))

    def test_result_wrong_measurement_digest_rejects(self):
        self.bad_probe(lambda p: p.update(audit_sha256="0" * 64))

    def test_result_wrong_artifact_digest_rejects(self):
        self.bad_probe(lambda p: p.update(artifact_sha256="0" * 64))

    def test_bare_pass_boolean_rejects(self):
        process = self.fixture.populate(self.prepared, {"passed": True})
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "RESULT")

    def test_failed_probe_stops_same_session_and_preserves_accepted_state(self):
        self.bad_probe(lambda p: p.update(state="FAILED", passed=False))
        accepted = self.fixture.native.accept("A02")
        self.reject(lambda: rb.prepare_readback(self.fixture.bindings, "A02", accepted=accepted), "REPLAY")
        self.assertEqual(tx.inspect_accepted(self.fixture.native.session, self.prepared.accepted)["state"], "TRANSACTION_ACCEPTED")

    def test_unknown_probe_is_unknown_and_not_retryable(self):
        process = self.fixture.populate(self.prepared, {"state": "UNKNOWN"})
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "RESULT", "UNKNOWN")
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "REPLAY")

    def test_success_cannot_be_consumed_twice(self):
        process = self.fixture.populate(self.prepared)
        rb.verify_readback_result(self.prepared, process=process)
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "REPLAY")

    def test_changed_accepted_glb_rejects_without_replacing_pointer(self):
        path = Path(self.job["artifact"]["path"])
        path.chmod(0o600);path.write_bytes(path.read_bytes() + b"changed");path.chmod(0o444)
        self.reject(lambda: rb.inspect_readback_job(self.prepared), "BINDING")

    def test_changed_accepted_measurements_rejects(self):
        path = Path(self.job["audit"]["path"])
        path.chmod(0o600);path.write_bytes(path.read_bytes() + b" ");path.chmod(0o444)
        self.reject(lambda: rb.inspect_readback_job(self.prepared), "BINDING")

    def test_result_missing_output_rejects(self):
        process = self.fixture.populate(self.prepared)
        Path(self.job["outputs"]["stderr"]).unlink()
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "OUTPUT")

    def test_result_extra_output_rejects(self):
        process = self.fixture.populate(self.prepared)
        Path(self.job["outputs"]["probe"]).with_name("extra.json").write_text("{}")
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "OUTPUT")

    def test_result_symlink_rejects(self):
        process = self.fixture.populate(self.prepared)
        path = Path(self.job["outputs"]["probe"])
        saved = Path(self.temp.name) / "outside.json";path.rename(saved);path.symlink_to(saved)
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "BINDING")

    def test_result_hardlink_rejects(self):
        process = self.fixture.populate(self.prepared)
        (Path(self.temp.name) / "outside.json").hardlink_to(self.job["outputs"]["probe"])
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "BINDING")

    def test_result_size_limit_rejects(self):
        process = self.fixture.populate(self.prepared)
        with Path(self.job["outputs"]["probe"]).open("wb") as stream:stream.truncate(rb.LIMITS["result_bytes"] + 1)
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "BINDING")

    def test_boolean_start_count_rejects(self):
        self.bad_probe(lambda p: p.update(native_starts=False))

    def test_changed_requested_checks_rejects(self):
        self.bad_probe(lambda p: p["checks"]["khronos"].update(allowed_warnings=1))

    def test_changed_child_budget_rejects(self):
        self.bad_probe(lambda p: p["limits"].update(child_work_ms=30000))

    def test_khronos_warning_cannot_hide_behind_passed(self):
        self.bad_probe(lambda p: p["khronos"]["report"]["issues"].update(numWarnings=1), "KHRONOS")

    def test_khronos_truncation_rejects(self):
        self.bad_probe(lambda p: p["khronos"]["report"]["issues"].update(truncated=True), "KHRONOS")

    def test_khronos_inconsistent_message_counts_reject(self):
        self.bad_probe(lambda p: p["khronos"]["report"]["issues"].update(numInfos=1), "KHRONOS")

    def test_wrong_three_dependency_version_rejects(self):
        self.bad_probe(lambda p: p["three"].update(version="0.0.0"), "THREE")

    def test_missing_imported_node_rejects(self):
        self.bad_probe(lambda p: p["three"]["nodes"].pop("equipment-tray/pair/right/payload"), "THREE")

    def test_wrong_parent_rejects(self):
        self.bad_probe(lambda p: p["three"]["nodes"]["equipment-tray/pair/right/payload"].update(parent="equipment-tray/pair/left"), "THREE")

    def test_changed_world_vertex_rejects(self):
        self.bad_probe(lambda p: p["three"]["nodes"]["equipment-tray/pair/left/payload"]["world_vertices"][0].__setitem__(0, 99), "MEASUREMENT")

    def test_changed_normal_rejects(self):
        self.bad_probe(lambda p: p["three"]["nodes"]["equipment-tray/pair/left/payload"]["normals"][0].__setitem__(0, 0), "MEASUREMENT")

    def test_changed_local_positions_reject(self):
        self.bad_probe(lambda p: p["three"]["nodes"]["equipment-tray/pair/left/payload"]["positions"][0].__setitem__(0, 99), "MEASUREMENT")

    def test_changed_triangle_indices_reject(self):
        self.bad_probe(lambda p: p["three"]["nodes"]["equipment-tray/pair/left/payload"]["indices"].reverse(), "THREE")

    def test_changed_material_rejects(self):
        self.bad_probe(lambda p: p["three"]["nodes"]["equipment-tray/pair/left/payload"]["material"].update(roughnessFactor=0.1), "THREE")

    def test_missing_required_measurement_rejects(self):
        self.bad_probe(lambda p: p["three"]["measurements"].pop(), "MEASUREMENT")

    def test_false_measurement_pass_flag_rejects(self):
        self.bad_probe(lambda p: p["three"]["measurements"][0].update(passed=False), "MEASUREMENT")

    def test_wrong_measurement_threshold_rejects(self):
        self.bad_probe(lambda p: p["three"]["measurements"][0].update(threshold=0.1), "MEASUREMENT")

    def test_extra_probe_field_rejects(self):
        self.bad_probe(lambda p: p.update(admission_completed=True))

    def test_node_receipt_wrong_command_rejects(self):
        process = self.fixture.populate(self.prepared)
        process["command"]["argv"][1] = "--inspect"
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "PROCESS")

    def test_node_receipt_changed_log_rejects(self):
        process = self.fixture.populate(self.prepared)
        Path(self.job["outputs"]["stdout"]).write_bytes(b"changed")
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "PROCESS")

    def test_node_failed_exit_rejects(self):
        process = self.fixture.populate(self.prepared);process["returncode"] = 1
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "PROCESS")

    def test_node_unknown_cleanup_rejects(self):
        process = self.fixture.populate(self.prepared);process["cleanup"]["reaped"] = None
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "PROCESS")

    def test_node_outer_deadline_rejects(self):
        process = self.fixture.populate(self.prepared);process["completed_monotonic"] = 32
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "PROCESS")

    def test_replaced_node_directory_rejects(self):
        stage = Path(self.job["outputs"]["job"]).parent
        stage.rename(stage.with_name(stage.name + "-original"));stage.mkdir()
        self.reject(lambda: rb.inspect_readback_job(self.prepared), "PATH")

    def test_interruption_returns_unknown_and_blocks_retry(self):
        process = self.fixture.populate(self.prepared)
        with mock.patch.object(rb, "_probe", side_effect=KeyboardInterrupt("controlled interruption")):
            self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "INTERRUPTED", "UNKNOWN")
        self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "REPLAY")

    def test_outputs_changed_during_verification_reject(self):
        process = self.fixture.populate(self.prepared)
        original = rb._probe
        def mutate(*args):
            value = original(*args)
            Path(self.job["outputs"]["probe"]).write_bytes(Path(self.job["outputs"]["probe"]).read_bytes() + b" ")
            return value
        with mock.patch.object(rb, "_probe", side_effect=mutate):
            self.reject(lambda: rb.verify_readback_result(self.prepared, process=process), "OUTPUT")


if __name__ == "__main__":
    unittest.main()
