"""C073 shared output work, supplied-byte authority and physical inheritance."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import evaluate_prefix
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.gltf import export_glb, read_glb, validate_export
from ontokin.profile_capabilities import BUDGET_PROFILE
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_conformance import check_complete_inequalities
from ontokin.reach_export import BUDGET_SOURCE_ERROR_RESERVE, BUDGET_DERIVATIVE_RESERVE
from ontokin.reach_reference import build_reference
from ontokin.scene import BUDGET_REACH_TARGET, ExportOptions


ROOT = Path(__file__).resolve().parents[1]
OPTIONS = ExportOptions(fps=2, end="0.25", helpers=False)
BOX_SOURCE = '''ontokin "0.7";
module BudgetBox @ "budget-box";
profile "planar-reach-budget-0.1";
execution { max_operations = 400000; max_elapsed = 80[s]; }
class Carrier @ "carrier-class" {
    geometry = box(vec3(1[m], 2[m], 3[m]));
    physical = no_body();
}
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object carrier @ "carrier": Carrier {}
}
'''

# This new entry composes unchanged pinned libraries with newly authored
# budget, impulse and force declarations. No historical fixture is rewritten.
INHERITED_SOURCE = '''ontokin "0.7";
module BudgetPhysics @ "budget-physics";
profile "planar-reach-budget-0.1";
execution { max_operations = 400000; max_elapsed = 80[s]; }
import assets @ "assets" from "proposal.reach-assets" version "0.1.0"
    digest "sha256:6551d3dd5a772e85e92547d71db081e6ae7c21a0f3d57424b01c64a18191d6ba";
import shapes @ "shapes" from "proposal.reach-exterior" version "0.1.0"
    digest "sha256:3b94fc91ca96f8fb0b21a90a1d6b4d78cdbd19600383a10cb6a3646ba67af763";
class Ball @ "ball-class" {
    geometry = sphere(0.5[m]);
    physical = sphere_body(0.5[m], 2[kg]);
    motion = dynamic;
    collision = disabled;
}
scene Demo @ "demo" {
    duration = 3[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object rig @ "rig": assets.BenchArm {}
    object ball @ "ball": Ball {
        placement = pose(world, vec3(5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
    action reach @ "reach" = reach_planar(rig.arm.shoulder, rig.arm.elbow,
        rig.arm.forearm.tip, point(rig.arm.reach_frame, 1[m], 1[m], 0[m]), 2[s], elbow_positive);
    at 0[s] sequence {
        start reach;
        impulse ball using vector(world, 0[N*s], 2[N*s], 0[N*s]) at point(ball.frame, 0[m], 0[m], 0[m]);
        force ball @ "push" using vector(world, 4[N], 0[N], 0[N]) for 1[s];
    }
}
'''


def source(text=BOX_SOURCE, modules=()):
    return ProgramBundle(SourceUnit("entry", "budget-export.ok", text.encode()), modules)


def admit(bundle, *, check=None, clock=None, caller_caps=None):
    ledger = SharedExecutionBudget(HostPolicy(400000, 80000), caller_caps,
                                   check=check, clock=clock)
    admit_entry_budget(bundle.entry, ledger)
    return ledger


def compile_source(bundle=None, **kwargs):
    bundle = source() if bundle is None else bundle
    ledger = admit(bundle, **kwargs)
    return bundle, compile_construction(bundle, execution_budget=ledger), ledger


def rewrite_json(data, change):
    length, = struct.unpack_from("<I", data, 12)
    document = json.loads(data[20:20 + length])
    change(document)
    encoded = json.dumps(document, separators=(",", ":"), allow_nan=False).encode()
    encoded += b" " * (-len(encoded) % 4)
    binary_chunk = data[20 + length:]
    total = 20 + len(encoded) + len(binary_chunk)
    return (struct.pack("<III", 0x46546C67, 2, total)
            + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded + binary_chunk)


class BudgetExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle, cls.compiler, cls.ledger = compile_source()
        cls.result = export_glb(cls.compiler.model, options=OPTIONS,
                                target_contract=BUDGET_REACH_TARGET,
                                work=cls.compiler.reach_work)

    def reader_work(self, *, check=None, caps=None):
        ledger = admit(self.bundle, check=check, caller_caps=caps)
        return ledger, ReachExecutionWork(execution_budget=ledger)

    def test_eb12_compile_record_export_and_readback_share_the_remaining_work(self):
        bundle, compiler, ledger = compile_source()
        started, after_compile = ledger.started, ledger.operations
        with patch("ontokin.reach_export._LocalArithmeticWork",
                   side_effect=AssertionError("A stage replenished work")):
            result = export_glb(compiler.model, options=OPTIONS,
                                target_contract=BUDGET_REACH_TARGET, work=compiler.reach_work)
            after_export = ledger.operations
            checked = validate_export(result.data, compiler.model, options=OPTIONS,
                                      target_contract=BUDGET_REACH_TARGET, work=compiler.reach_work)
        self.assertEqual(checked["status"], "passed")
        self.assertGreater(after_export, after_compile)
        self.assertGreater(ledger.operations, after_export)
        self.assertEqual(compiler.budget.operations, ledger.operations)
        self.assertEqual(compiler.reach_work.started, started)
        self.assertEqual(ledger.started, started)
        self.assertLess(compiler.reach_work.operations, ledger.operations)
        self.assertGreater(compiler.reach_work.counts["recording_stage_encoding"], 0)
        self.assertGreater(compiler.reach_work.counts["independent_metadata_identity"], 0)

    def test_eb22_explicit_output_identity_and_exact_native_box_dimensions(self):
        ledger, work = self.reader_work()
        decoded = read_glb(self.result.data, target_contract=BUDGET_REACH_TARGET, work=work)
        metadata = decoded.document["extras"]["ontokin"]
        self.assertEqual(metadata["target_contract"], BUDGET_REACH_TARGET)
        self.assertEqual(metadata["schema_version"], "0.7")
        self.assertEqual(metadata["profile"], BUDGET_PROFILE)
        self.assertEqual(metadata["reach_profile"]["source_profile"], BUDGET_PROFILE)
        animation = decoded.document["animations"][0]
        self.assertEqual(animation["extras"]["ontokin"]["target_contract"], BUDGET_REACH_TARGET)
        mesh = decoded.document["meshes"][decoded.document["nodes"][0]["mesh"]]
        positions = decoded.accessor(mesh["primitives"][0]["attributes"]["POSITION"])
        widths = [max(v[i] for v in positions) - min(v[i] for v in positions) for i in range(3)]
        self.assertEqual(widths, [1, 2, 3])
        self.assertGreater(ledger.operations, work.operations)

    def test_eb23_budget_metadata_cannot_create_reader_authority(self):
        changed = rewrite_json(self.result.data, lambda doc: doc["extras"]["ontokin"].update(
            execution_budget={"trusted": True, "max_operations": 900000000, "max_elapsed_ms": 900000000}))
        for call in (
            lambda: read_glb(changed, target_contract=BUDGET_REACH_TARGET),
            lambda: validate_export(changed, self.compiler.model, options=OPTIONS,
                                    target_contract=BUDGET_REACH_TARGET),
            lambda: export_glb(self.compiler.model, options=OPTIONS, target_contract=BUDGET_REACH_TARGET),
        ):
            with self.subTest(call=call), self.assertRaises(OntoKinError) as caught:
                call()
            self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
        ledger, work = self.reader_work(caps={"max_operations": 1000})
        ledger.tick(amount=1000 - ledger.operations - 2)
        with self.assertRaises(OntoKinError) as caught:
            read_glb(changed, target_contract=BUDGET_REACH_TARGET, work=work)
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "operation_budget_exhausted")
        self.assertEqual(ledger.limits["max_operations"], 1000)
        self.assertEqual(ledger.operations, 1001)

    def test_eb23_tampered_source_identity_is_rejected_by_independent_readback(self):
        def change(doc):
            doc["extras"]["ontokin"]["profile"] = "planar-reach-0.1"
        changed = rewrite_json(self.result.data, change)
        _, work = self.reader_work()
        with self.assertRaises(OntoKinError) as caught:
            validate_export(changed, self.compiler.model, options=OPTIONS,
                            target_contract=BUDGET_REACH_TARGET, work=work)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-PROVENANCE")

    def test_eb23_conservative_reserve_preserves_exact_inequalities_and_tolerances(self):
        self.assertEqual(BUDGET_SOURCE_ERROR_RESERVE, Fraction(2))
        self.assertEqual(BUDGET_DERIVATIVE_RESERVE, 1 + Fraction(1, 1 << 48))
        _, work = self.reader_work()
        decoded = read_glb(self.result.data, target_contract=BUDGET_REACH_TARGET, work=work)
        certificates = decoded.document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
        for record in certificates:
            for name in ("angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2",
                         "enclosing_carrier_speed_bound_m_per_s", "enclosing_carrier_acceleration_bound_m_per_s2",
                         "enclosing_angular_speed_bound_rad_per_s"):
                self.assertEqual(record[name], 0)
            bounds = check_complete_inequalities(record, position_tolerance=OPTIONS.position_tolerance_m,
                                                 rotation_tolerance=OPTIONS.rotation_tolerance_rad, work=work)
            self.assertLessEqual(bounds["position_bound_m"], Fraction(OPTIONS.position_tolerance_m))
            self.assertLessEqual(bounds["rotation_bound_rad"], Fraction(OPTIONS.rotation_tolerance_rad))
        def reduce_source(doc):
            record = doc["extras"]["ontokin"]["reach_quantization"]["interval_certificates"][0]
            record["source_numeric_position_bound_m"] = 0
        changed = rewrite_json(self.result.data, reduce_source)
        with self.assertRaises(OntoKinError) as caught:
            validate_export(changed, self.compiler.model, options=OPTIONS,
                            target_contract=BUDGET_REACH_TARGET, work=work)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-CERTIFICATE")
        oversized = {**certificates[0], "total_position_bound_m": 1}
        with self.assertRaises(OntoKinError):
            check_complete_inequalities(oversized, position_tolerance=OPTIONS.position_tolerance_m,
                                        rotation_tolerance=OPTIONS.rotation_tolerance_rad, work=work)

    def test_eb23_structurally_valid_changed_vertices_fail_the_source_oracle(self):
        data = bytearray(self.result.data)
        length, = struct.unpack_from("<I", data, 12)
        document = json.loads(data[20:20 + length])
        primitive = document["meshes"][0]["primitives"][0]
        index = primitive["attributes"]["POSITION"]
        accessor = document["accessors"][index]
        view = document["bufferViews"][accessor["bufferView"]]
        offset = 28 + length + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = view.get("byteStride", 12)
        for vertex in range(accessor["count"]):
            at = offset + vertex * stride
            x, = struct.unpack_from("<f", data, at)
            struct.pack_into("<f", data, at, x * 2)
        def bounds(doc):
            for field in ("min", "max"):
                doc["accessors"][index][field][0] *= 2
        changed = rewrite_json(data, bounds)
        _, work = self.reader_work()
        read_glb(changed, target_contract=BUDGET_REACH_TARGET, work=work)
        with self.assertRaises(OntoKinError) as caught:
            validate_export(changed, self.compiler.model, options=OPTIONS,
                            target_contract=BUDGET_REACH_TARGET, work=work)
        self.assertIn(caught.exception.diagnostic.details["export_code"],
                      {"OKE-E-GEOMETRY", "OKE-E-GEOMETRY-PRECISION"})

    def test_eb21_earlier_or_implicit_reader_selection_rejects_budget_artifact(self):
        for target in (None, "ontokin.glb/0.6", "ontokin.glb/0.5"):
            with self.subTest(target=target), self.assertRaises(OntoKinError):
                read_glb(self.result.data, target_contract=target)
        for values in ({"max_operations": 200000}, {"max_elapsed_ms": 60000}):
            with self.assertRaises(ValueError):
                ReachExecutionWork(**values)

    def test_eb21_legacy_malformed_shapes_keep_materialization_checkpoint(self):
        for document in (["malformed"], {"asset": {"version": "2.0"}, "extras": []}):
            with self.subTest(document=document):
                encoded = json.dumps(document).encode()
                encoded += b" " * (-len(encoded) % 4)
                data = (struct.pack("<III", 0x46546C67, 2, 28 + len(encoded))
                        + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
                        + struct.pack("<II", 0, 0x004E4942))
                calls = 0
                marker = RuntimeError("cancel inherited metadata materialization")
                def cancel():
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        raise marker
                with self.assertRaises(RuntimeError) as caught:
                    read_glb(data, check=cancel)
                self.assertIs(caught.exception, marker)
                self.assertEqual(calls, 2)

    def test_eb19_reader_preserves_caller_exception_identity(self):
        for marker in (ValueError("cancel reader"), OntoKinError("OKL-E-RESOURCE", "host cancellation")):
            with self.subTest(kind=type(marker).__name__):
                active = False
                calls = 0
                def cancel():
                    nonlocal calls
                    if active:
                        calls += 1
                        if calls == 3:
                            raise marker
                _, work = self.reader_work(check=cancel)
                active = True
                with self.assertRaises(type(marker)) as caught:
                    read_glb(self.result.data, target_contract=BUDGET_REACH_TARGET, work=work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)

    def test_eb19_nested_context_checkpoint_preserves_caller_identity_and_details(self):
        for marker in (ValueError("cancel context"), OntoKinError("OKL-E-RESOURCE", "host cancellation")):
            with self.subTest(kind=type(marker).__name__):
                active = False
                calls = 0
                before = dict(marker.diagnostic.details) if isinstance(marker, OntoKinError) else None
                def cancel():
                    nonlocal calls
                    if active:
                        calls += 1
                        if calls == 2:
                            raise marker
                _, work = self.reader_work(check=cancel)
                active = True
                with self.assertRaises(type(marker)) as caught:
                    validate_export(self.result.data, self.compiler.model, options=OPTIONS,
                                    target_contract=BUDGET_REACH_TARGET, work=work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                if before is not None:
                    self.assertEqual(marker.diagnostic.details, before)

    def test_eb13_numeric_local_limits_stay_separate_from_execution_limits(self):
        ledger, work = self.reader_work()
        self.assertEqual(work.max_operations, 400000)
        self.assertEqual(work.max_elapsed_ms, 80000)
        self.assertEqual(work.max_operand_bits, 32768)
        self.assertEqual(work.max_cache_entries, 256)
        with self.assertRaises(ReachAdmissionError) as caught:
            work.guard(1 << 32768)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        for i in range(270):
            work.remember(("bounded-cache", i), i)
        self.assertEqual(len(work._cache), 256)
        with self.assertRaises(ValueError):
            ReachExecutionWork(execution_budget=ledger, max_cache_entries=257)
        local = work.admission()
        for _ in range(100000):
            local.interval()
        with self.assertRaises(ReachAdmissionError) as caught:
            local.interval()
        self.assertEqual(caught.exception.details["budget"], "numeric_interval_operations")
        self.assertEqual(caught.exception.details["limit"], 100000)
        self.assertLess(ledger.operations, 400000)

    def test_eb12_numeric_adapter_keeps_original_deadline_and_debits_once(self):
        now = [10.0]
        bundle = source()
        ledger = admit(bundle, clock=lambda: now[0])
        before = ledger.operations
        work = ReachExecutionWork(execution_budget=ledger)
        work.charge("new_numeric", 7)
        self.assertEqual(ledger.operations, before + 7)
        self.assertEqual(work.operations, 7)
        now[0] = 90.0
        work.tick()
        now[0] = 90.001
        with self.assertRaises(OntoKinError) as caught:
            work.tick()
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_deadline_exceeded")
        self.assertEqual(ledger.started, 10.0)

    def test_eb22_inherited_reach_surface_impulse_and_force_semantics(self):
        old_bundle = load_file_manifest(ROOT / "docs/language-design/planar-reach-v0.1/p01.files.json")
        bundle, compiler, ledger = compile_source(source(INHERITED_SOURCE, old_bundle.modules))
        prefix = evaluate_prefix(compiler.model, "0.25", check=ledger.tick, work=compiler.reach_work)
        self.assertIsNone(prefix["failure"])
        state = prefix["last_valid_state"]
        ball = state["objects"]["ball"]
        # x = x0 + (F / 2m)t² and y = (J / m)t from independent elementary equations
        self.assertEqual(ball["position_m"], [5.0625, 0.25, 0])
        self.assertEqual(ball["velocity_m_per_s"], [0.5, 1, 0])
        self.assertEqual(ball["angular_velocity_rad_per_s"], [0, 0, 0])
        self.assertEqual(ball["forces"]["started_count"], 1)
        self.assertEqual(ball["impulses"]["applied_count"], 1)
        self.assertEqual(compiler.model.actions["reach"].kind, "reach_planar")
        self.assertTrue(compiler.surface_meshes)
        result = export_glb(compiler.model, options=OPTIONS,
                            target_contract=BUDGET_REACH_TARGET, work=compiler.reach_work)
        self.assertEqual(result.report["validation"]["status"], "passed")
        self.assertGreater(result.report["geometry"]["native_surface_nodes"], 0)
        self.assertEqual(result.report["reach_profile"]["source_profile"], BUDGET_PROFILE)
        self.assertGreater(result.report["validation"]["interval_certificates_checked"], 0)

    def test_eb22_exact_center_impulse_preserves_prior_spin_and_noncenter_adds_torque(self):
        old_bundle = load_file_manifest(ROOT / "docs/language-design/planar-reach-v0.1/p01.files.json")
        for application, expected_spin in (("0[m]", 5), ("0.5[m]", 10)):
            with self.subTest(application=application):
                impulse = "        impulse ball using vector(world, 0[N*s], 2[N*s], 0[N*s]) "
                text = INHERITED_SOURCE.replace(
                    impulse + "at point(ball.frame, 0[m], 0[m], 0[m]);",
                    impulse + "at point(ball.frame, 0.5[m], 0[m], 0[m]);\n"
                    + impulse + f"at point(ball.frame, {application}, 0[m], 0[m]);")
                _, compiler, ledger = compile_source(source(text, old_bundle.modules))
                prefix = evaluate_prefix(compiler.model, "0.25", check=ledger.tick, work=compiler.reach_work)
                self.assertIsNone(prefix["failure"])
                actual = prefix["last_valid_state"]["objects"]["ball"]["angular_velocity_rad_per_s"]
                self.assertEqual(actual, [0, 0, expected_spin])
                reference = build_reference(compiler.model, end=Fraction(1, 4), work=compiler.reach_work)
                omega = reference.sample(Fraction(1, 4))["objects"]["ball"]["angular_velocity_rad_per_s"]
                self.assertTrue(all(value.contains(expected) for value, expected in zip(omega, actual)))
                self.assertGreater(omega[2].lo, 0)


if __name__ == "__main__":
    unittest.main()
