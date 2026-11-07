"""Exact torque runtime regressions using the immutable C090 source cohort."""
import copy
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
import unittest

from ontokin.construction import compile_construction
from ontokin.evaluator import _simulator
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.diagnostics import OntoKinError
from ontokin.torque_runtime import TorqueSimulator
from ontokin.texture_bundle import load_texture_file_manifest


FREEZE = Path(__file__).resolve().parents[1] / "docs/language-design/torque-v0.1/freeze"


def source(name):
    return load_texture_file_manifest(FREEZE / (name + ".files.json"))


def simulator(bundle, *, profile="torque-0.1", check=None):
    ledger = SharedExecutionBudget(check=check)
    admit_entry_budget(bundle.entry, ledger, profile=profile)
    compiler = compile_construction(bundle, execution_budget=ledger)
    return _simulator(compiler.model, work=compiler.reach_work), ledger


def translation(sim, path="ball"):
    anchor = sim.state.dynamic[path]
    error = sim.state.dynamic_errors[path]
    return (anchor.time, anchor.since, anchor.state.position, anchor.state.velocity,
            error.position_m, error.velocity_m_per_s,
            sim.state.dynamic_error_times[path], sim.state.ideal_accelerations[path])


class TorqueRuntimeTests(unittest.TestCase):
    def test_completion_can_create_the_first_split_anchor(self):
        sim, _ = simulator(source("p09-completion-starts-rotation"))
        before = sim.advance(F(1), "before")["objects"]["ball"]["torques"]
        self.assertEqual(before["rotation_route"], "legacy")
        after = sim.advance(F(1), "after")["objects"]["ball"]["torques"]
        self.assertEqual(after["rotation_route"], "split")
        self.assertEqual(after["rotation_anchor_seconds"], "1")
        self.assertEqual(after["completed_count"], 1)

    def test_underflow_keeps_legacy_motion_and_nonzero_exact_shadow(self):
        sim, _ = simulator(source("p24-underflow-is-neutral"))
        value = sim.advance(F(1), "before")["objects"]["ball"]["torques"]
        self.assertEqual(value["rotation_route"], "legacy")
        self.assertEqual(value["angular_acceleration_rad_per_s2"], 0.0)
        ratio = value["angular_acceleration_reference_rad_per_s2"]
        self.assertEqual(F(int(ratio["numerator"]), int(ratio["denominator"])), F(1, 1 << 1075))
        error = value["angular_speed_error_bound_rad_per_s"]
        self.assertGreaterEqual(F(int(error["numerator"]), int(error["denominator"])), F(1, 1 << 1075))

    def test_torque_boundary_does_not_reanchor_com_rounding_tie(self):
        sim, _ = simulator(source("p15-translation-tie"))
        value = sim.advance(F(1))["objects"]["ball"]
        self.assertEqual(value["position_m"][0].hex(), "0x1.0000000000001p+0")
        self.assertEqual(value["pose_authority"]["trajectory_anchor_seconds"], "0")

    def test_world_axis_is_a_left_product_of_full_initial_rotation(self):
        sim, _ = simulator(source("p31-noncommuting-initial-rotation"))
        value = sim.advance(F(1))["objects"]["ball"]["orientation_wxyz"]
        self.assertEqual(value[0], 0.0)
        self.assertEqual(value[3], 0.0)
        self.assertGreater(value[1] * value[2], 0.0)

    def test_neutral_force_keeps_complete_inherited_anchor_error(self):
        sim, _ = simulator(source("p16-neutral-com-force"))
        control, _ = simulator(source("control-neutral-com-force"), profile="keyed-membership-0.1")
        for time in (F(0), F(1, 2), F(1), F(3)):
            sim.advance(time); control.advance(time)
            self.assertEqual(translation(sim), translation(control))
            self.assertEqual(sim.state.dynamic_errors["ball"], control.state.dynamic_errors["ball"])
            self.assertIsNone(sim.state.torques["ball"].rotation)

    def test_release_keeps_inherited_translation_cell_and_error(self):
        sim, _ = simulator(source("p28-release-then-torque"))
        control, _ = simulator(source("control-release-then-torque"), profile="keyed-membership-0.1")
        for time in (F(1), F(3, 2), F(2), F(3)):
            sim.advance(time); control.advance(time)
            self.assertEqual(translation(sim), translation(control))
            self.assertIn("ball", sim.state.dynamic_cells)

    def test_released_split_body_accepts_later_axis_preserving_impulse(self):
        bundle = source("p28-release-then-torque")
        extra = ('    at 1.5[s] sequence {\n'
                 '        impulse ball using vector(world, 0[N*s], 1[N*s], 0[N*s]) '
                 'at point(ball.frame, 1[m], 0[m], 0[m]);\n    }\n')
        text = bundle.entry.text.rstrip()[:-1] + extra + '}\n'
        bundle = replace(bundle, entry=replace(bundle.entry, raw=text.encode()))
        sim, _ = simulator(bundle)
        before = sim.advance(F(3, 2), "before")["objects"]["ball"]
        after = sim.advance(F(3, 2), "after")["objects"]["ball"]
        self.assertEqual(before["orientation_wxyz"], after["orientation_wxyz"])
        self.assertGreater(after["angular_velocity_rad_per_s"][2], before["angular_velocity_rad_per_s"][2])
        self.assertEqual(after["torques"]["rotation_anchor_seconds"], "1.5")
        sim.advance(F(3))
        self.assertIn("ball", sim.state.dynamic_cells)

    def test_original_commit_callback_failure_preserves_accepted_state(self):
        owner = {}
        sentinel = RuntimeError("original callback")
        def check():
            sim = owner.get("sim")
            if sim is not None and owner["ledger"].stage == "torque_boundary_commit":
                owner["before"] = (sim.state, copy.deepcopy(sim.state), sim.event_index)
                raise sentinel
        sim, ledger = simulator(source("p04-overlap"), check=check)
        owner.update(sim=sim, ledger=ledger)
        with self.assertRaises(RuntimeError) as caught:
            sim.advance(F(3))
        self.assertIs(caught.exception, sentinel)
        accepted, saved, index = owner["before"]
        self.assertIs(sim.state, accepted)
        self.assertEqual(sim.state, saved)
        self.assertEqual(sim.event_index, index)
        self.assertEqual(ledger.stage, "execution")

    def test_source_dictionary_mutation_after_callback_cannot_enter_history(self):
        owner = {}
        def check():
            sim = owner.get("sim")
            if sim is not None and owner["ledger"].stage == "torque_activation":
                sim.events[0].events[0].torque.source["start_byte"] += 1
        sim, ledger = simulator(source("p01-spin-up"), check=check)
        owner.update(sim=sim, ledger=ledger)
        accepted = sim.state
        with self.assertRaises(OntoKinError) as caught:
            sim.advance(F(1))
        self.assertEqual(caught.exception.diagnostic.code, "OKL-E-RESOURCE")
        self.assertIs(sim.state, accepted)
        self.assertEqual(sim.state.torques["ball"].started_count, 0)
        self.assertEqual(ledger.stage, "execution")

    def test_original_callback_owner_cannot_be_replaced_during_activation(self):
        owner = {}
        def replacement():
            pass
        def check():
            ledger = owner.get("ledger")
            if ledger is not None and ledger.stage == "torque_activation":
                ledger.check = replacement
        sim, ledger = simulator(source("p01-spin-up"), check=check)
        owner.update(sim=sim, ledger=ledger)
        accepted = sim.state
        with self.assertRaises(OntoKinError) as caught:
            sim.advance(F(1))
        self.assertEqual(caught.exception.diagnostic.code, "OKL-E-RESOURCE")
        self.assertIs(sim.state, accepted)
        self.assertEqual(sim.event_index, 0)

    def test_own_inertia_cannot_change_during_aggregate_callback(self):
        owner = {}
        def check():
            sim = owner.get("sim")
            if sim is not None and owner["ledger"].stage == "torque_aggregate_begin":
                sim.model.objects["ball"].physical["inertia"] = 2.0
        sim, ledger = simulator(source("p01-spin-up"), check=check)
        owner.update(sim=sim, ledger=ledger)
        accepted = sim.state
        with self.assertRaises(OntoKinError) as caught:
            sim.advance(F(1))
        self.assertEqual(caught.exception.diagnostic.code, "OKL-E-RESOURCE")
        self.assertIs(sim.state, accepted)
        self.assertEqual(sim.state.torques["ball"].started_count, 0)

    def test_custom_history_container_is_rejected_before_iteration(self):
        class Foreign(dict):
            def items(self):
                raise AssertionError("foreign iteration must not run")
        sim, _ = simulator(source("p01-spin-up"))
        sim.state.torques["ball"].active = Foreign()
        with self.assertRaises(ValueError):
            sim.advance(F(1))

    def test_native_scalar_and_original_context_are_required(self):
        sim, _ = simulator(source("p01-spin-up"))
        with self.assertRaises(OntoKinError):
            TorqueSimulator(sim.model)
        event = sim.events[0].events[0]
        event.torque = replace(event.torque, sequence_index=True)
        with self.assertRaises(ValueError):
            TorqueSimulator(sim.model, work=sim.work)


if __name__ == "__main__":
    unittest.main()
