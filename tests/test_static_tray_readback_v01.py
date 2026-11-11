"""Three synthetic Node readback controls; these are not native qualification.

The complete cohort starts three read-only Node checkers plus two dependency
inspection commands (Node --version and ldd). It starts no Blender, exporter,
receiving Blender process, lifecycle stub, browser or renderer.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch

from prototypes.static_tray_v01.canonical import ROOT, json_bytes
from prototypes.static_tray_v01.format_check import build_manifest, verify_manifest
from prototypes.static_tray_v01.supervisor import Clock, Stop, run_process, sha256_file
from tests.test_static_tray_reader_v01 import synthetic, audit
from prototypes.static_tray_v01 import format_check
from prototypes.static_tray_v01.transaction import write_new

NODE = Path("/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node")
DEPS = Path("/workspace/scratch/801d9d641f68/incoming-audit/work/prior-replay/evidence/c195-validation/receiving")
HOST = Path("/workspace/scratch/801d9d641f68/c199-independent-preflight/HOST-RUNTIME-INVENTORY.json")


class ReadbackCoordinatorSeams(unittest.TestCase):
    """Mocked child seams; no additional Node or lifecycle process starts."""
    def run_seam(self, failure=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        candidate = root / "candidate"
        candidate.mkdir()
        (candidate / "final.glb").write_bytes(b"CPU COORDINATOR SEAM")
        (candidate / "independent-audit.json").write_bytes(b"{}")
        stage = root / "schedule/external-readback/N01"
        row = {"slot": "N01", "case": "Q01", "route": "ontokin", "stage": str(stage), "result": str(stage / "result.json"), "argv": ["MOCK-NODE"]}
        manifest = {"slots": [row], "environment": {}}
        manifest_path = root / "manifest.json"
        manifest_path.write_bytes(json_bytes(manifest))
        lock = {"schedule_root": str(root / "schedule"), "external_readback": {"path": str(manifest_path), "sha256": sha256_file(manifest_path), "size_bytes": manifest_path.stat().st_size}}
        observed = {}
        def child(*a, **kw):
            observed["supervisor_alarm_seconds"] = signal.getitimer(signal.ITIMER_REAL)[0]
            process = {"process_group": 123456, "handles_closed": True, "cleanup": {"passed": True}}
            kw["on_started"](process)
            job = json.loads((stage / "job.json").read_bytes())
            (stage / "probe.json").write_bytes(json_bytes({"passed": True, "input_lock_sha256": "lock-hash", "artifact_sha256": job["artifact_sha256"],
                "khronos": {"version": "2.0.0-dev.3.10"}, "three": {"version": "0.186.1"}}))
            return process
        def writer(path, value, **kw):
            if Path(path).name == "result.json":
                observed["finalization_alarm_seconds"] = signal.getitimer(signal.ITIMER_REAL)[0]
                if failure == "write": raise OSError("controlled final result write failure")
            return write_new(path, value, **kw)
        real_unlink = Path.unlink
        def unlink(path, *a, **kw):
            value = real_unlink(path, *a, **kw)
            if failure == "remove" and path.name == "finalization.pending":
                raise OSError("controlled lost reply after pending marker removal")
            return value
        with patch.object(format_check, "check_file"), patch.object(format_check, "verify_manifest", return_value=(manifest, "manifest-hash")), \
                patch.object(format_check, "run_process", side_effect=child) as process, \
                patch("prototypes.static_tray_v01.transaction._prior_result", return_value=({}, candidate, {})), \
                patch("prototypes.static_tray_v01.transaction.write_new", side_effect=writer), \
                patch("prototypes.static_tray_v01.store.verify_candidate", return_value={}), patch.object(Path, "unlink", unlink):
            result = format_check.run_check(lock, "lock-hash", "N01")
        self.assertEqual(process.call_count, 1)
        self.assertEqual(result["checker_starts"], 1)
        return result, stage, lock, observed

    def test_result_write_failure_leaves_predecessor_gate_blocked(self):
        result, stage, lock, _ = self.run_seam("write")
        self.assertFalse(result["passed"])
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertTrue((stage / "finalization.pending").exists())
        with self.assertRaisesRegex(Stop, "unresolved finalization"):
            format_check.verify_predecessors(lock, "lock-hash", "N02")

    def test_host_alarm_cannot_interrupt_supervisor_cleanup(self):
        result, _, _, observed = self.run_seam()
        self.assertTrue(result["passed"])
        self.assertEqual(observed["supervisor_alarm_seconds"], 0)

    def test_success_finalization_uses_remaining_outer_alarm(self):
        result, _, _, observed = self.run_seam()
        self.assertTrue(result["passed"])
        self.assertGreater(observed["finalization_alarm_seconds"], 0)
        self.assertLessEqual(observed["finalization_alarm_seconds"], 30)

    def test_uncertain_marker_removal_recreates_pending(self):
        result, stage, lock, _ = self.run_seam("remove")
        self.assertFalse(result["passed"])
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertTrue((stage / "finalization.pending").exists())
        with self.assertRaisesRegex(Stop, "unresolved finalization"):
            format_check.verify_predecessors(lock, "lock-hash", "N02")


@unittest.skipUnless(NODE.is_file() and DEPS.is_dir() and HOST.is_file(), "Retained exact Node/readback dependencies are unavailable")
class ReadbackCPUControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        destination = os.environ.get("STATIC_TRAY_READBACK_CPU_OUTPUT")
        if destination:
            cls.root = Path(destination)
            cls.root.mkdir(parents=True, exist_ok=False)
            cls.temporary = None
        else:
            cls.temporary = tempfile.TemporaryDirectory(prefix="static-tray-readback-cpu-")
            cls.root = Path(cls.temporary.name)
        cls.manifest_path = cls.root / "supplemental-cpu.json"
        cls.manifest, cls.manifest_hash = build_manifest(cls.manifest_path, node=NODE, dependencies_root=DEPS,
            schedule_root=cls.root / "unused-native-schedule", host_inventory=HOST)
        verify_manifest(cls.manifest_path, schedule_root=cls.root / "unused-native-schedule")

    @classmethod
    def tearDownClass(cls):
        if cls.temporary: cls.temporary.cleanup()

    def check_case(self, case, *, changed_reference=False):
        label = case + ("-changed-reference" if changed_reference else "-positive")
        stage = self.root / label
        stage.mkdir()
        artifact = stage / "synthetic.glb"
        artifact.write_bytes(synthetic(case))
        reference = audit(artifact, case)
        self.assertTrue(reference["passed"], reference["findings"])
        if changed_reference:
            reference = deepcopy(reference)
            reference["nodes"]["equipment-tray/pair/left/base"]["world_matrix"][0][3] += .001
            reference["scope"] = "Intentionally changed synthetic reference for a negative importer comparison control; not native evidence"
        audit_path = stage / "synthetic-audit.json"
        audit_path.write_bytes(json_bytes(reference))
        job = {"slot": "CPU-" + label, "case": case, "manifest": str(self.manifest_path),
               "supplemental_manifest_sha256": self.manifest_hash, "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
               "artifact": str(artifact), "artifact_sha256": sha256_file(artifact),
               "audit": str(audit_path), "audit_sha256": sha256_file(audit_path), "result": str(stage / "probe.json")}
        (stage / "job.json").write_bytes(json_bytes(job))
        argv = self.manifest["slots"][0]["argv"][:-1] + [str(stage / "job.json")]
        clock = Clock(total_ms=30000)
        started = []
        try:
            process = run_process(argv, stage=stage, label="synthetic-readback", clock=clock,
                stage_end=clock.started + 28, env=self.manifest["environment"], on_started=lambda record: started.append(record))
        except Stop as exc:
            process = getattr(exc, "process_record", None)
            if not changed_reference:
                raise
        report = json.loads((stage / "probe.json").read_bytes())
        self.assertEqual(len(started), 1)
        self.assertTrue(process["cleanup"]["passed"])
        self.assertTrue(process["handles_closed"])
        self.assertEqual(report["artifact_sha256"], sha256_file(artifact))
        self.assertEqual(report["khronos"]["version"], "2.0.0-dev.3.10")
        self.assertTrue(report["khronos"]["passed"])
        self.assertEqual(report["three"]["version"], "0.186.1")
        self.assertEqual(report["three"]["node_count"], 14)
        self.assertEqual(report["three"]["mesh_count"], 12)
        self.assertEqual(report["passed"], not changed_reference, report.get("error", report["three"]["findings"]))
        self.assertTrue(report["input_preserved"])
        if changed_reference:
            self.assertTrue(any(row["field"] == "matrix_0_3" for row in report["three"]["findings"]))

    def test_q01_actual_synthetic_meshes_load_in_both_libraries(self):
        self.check_case("Q01")

    def test_q03_actual_synthetic_rotations_load_in_both_libraries(self):
        self.check_case("Q03")

    def test_three_rejects_changed_synthetic_reference(self):
        self.check_case("Q01", changed_reference=True)


if __name__ == "__main__":
    unittest.main()
