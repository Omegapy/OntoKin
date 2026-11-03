"""Independent C092 reader checks against the adopted preimplementation freeze."""
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
import json
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.reach_reference import _Arithmetic, ReferenceError, build_reference
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin import torque_axis_exact as exact
from ontokin import torque_axis_reference as angular


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "docs/language-design/torque-amendments/c092-canonical-spin-selection/inputs"
EXPECTED = json.loads((INPUTS / "EXPECTED-SELECTOR-RESULTS.json").read_text())


def fraction(value):
    return F(int(value["numerator"]), int(value["denominator"]))


def arithmetic():
    steps = [0]
    def check():
        steps[0] += 1
        if steps[0] > 100000:
            raise AssertionError("Independent numerical test exhausted its unchanged bound")
    return _Arithmetic(check=check), steps


def source(name, *, text=None):
    bundle = load_texture_file_manifest(
        ROOT / "docs/language-design/torque-v0.1/freeze/p28-release-then-torque.files.json")
    raw = (INPUTS / name).read_bytes() if text is None else text.encode()
    bundle = replace(bundle, entry=replace(bundle.entry, raw=raw))
    ledger = SharedExecutionBudget()
    admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
    compiler = compile_construction(bundle, execution_budget=ledger)
    return compiler, ledger


def reader(name, end, *, text=None):
    compiler, ledger = source(name, text=text)
    result = build_reference(compiler.model, end=F(end), mode="observation", work=compiler.reach_work)
    return result, ledger


class CanonicalSpinKernelTests(unittest.TestCase):
    def test_all_frozen_precision_boundaries_and_signed_point_values(self):
        a, steps = arithmetic()
        for row in EXPECTED["stage_boundaries"]:
            with self.subTest(case=row["id"]):
                omega = tuple(map(fraction, row["omega"]))
                elapsed = fraction(row["elapsed"])
                if row["outcome"] == "selected":
                    self.assertEqual(exact.spin_plan(omega, elapsed, a)[0], row["selected_precision"])
                    q = exact.spin_rotation(omega, elapsed, a)
                    self.assertEqual([str(int(value * exact.GRID)) for value in q],
                                     row["quaternion_grid_integers"])
                else:
                    with self.assertRaises(ReferenceError) as caught:
                        exact.spin_plan(omega, elapsed, a)
                    self.assertEqual(caught.exception.code, "numeric")
        self.assertLess(steps[0], 100000)

    def test_selected_reduction_failure_is_terminal(self):
        a, _ = arithmetic()
        with patch.object(exact, "pi_bounds", wraps=exact.pi_bounds) as pi, \
             patch.object(exact, "reduced_sincos", return_value=None) as reduction:
            with self.assertRaises(ReferenceError) as caught:
                exact.spin_rotation((F(1), F(0), F(0)), F(1), a)
        self.assertEqual(caught.exception.code, "numeric")
        self.assertIn("selected source spin", str(caught.exception))
        self.assertEqual([call.args[0] for call in pi.call_args_list], [96])
        self.assertEqual(reduction.call_count, 1)

    def test_resource_and_callback_failures_are_not_stage_retries(self):
        for sentinel in (ReferenceError("resource", "original domain failure"),
                         RuntimeError("original callback failure")):
            with self.subTest(error=type(sentinel).__name__):
                a, _ = arithmetic()
                with patch.object(exact, "sqrt_bounds", side_effect=sentinel) as sqrt:
                    with self.assertRaises(type(sentinel)) as caught:
                        exact.spin_rotation((F(1), F(0), F(0)), F(1), a)
                self.assertIs(caught.exception, sentinel)
                self.assertEqual(sqrt.call_count, 1)

    def test_cached_plan_does_not_bypass_a_narrowed_current_domain(self):
        a, _ = arithmetic()
        exact.spin_plan((F(1), F(0), F(0)), F(1), a)
        a.work = SimpleNamespace(max_operand_bits=96)
        with self.assertRaises(ReferenceError) as caught:
            exact.spin_plan((F(1), F(0), F(0)), F(1), a)
        self.assertEqual(caught.exception.code, "resource")

    def test_materialized_projection_and_stationary_origin_are_retained(self):
        a, _ = arithmetic()
        q = exact.rotation((F(3), F(4), F(2), F(1)), a)
        original = angular.AngularSupport(F(0), angular.constants(q), angular.ZERO,
            q, (F(0),)*3, rotation_error=angular.PRODUCT_ERROR)
        saved = angular.materialize(original, a)
        with patch.object(exact, "materialized", side_effect=AssertionError("renormalized saved projection")):
            again = angular.materialize(saved, a)
            stationary = angular._advance(saved, (F(0),)*3, F(7), F(7), a)
        self.assertEqual(again.exact_quaternion, saved.exact_quaternion)
        self.assertEqual(again.frozen_projection, saved.frozen_projection)
        self.assertEqual(again.rotation_error, saved.rotation_error + angular.EXPOSED_ERROR)
        self.assertIs(stationary.exact_quaternion, saved.exact_quaternion)
        self.assertIs(stationary.frozen_projection, saved.frozen_projection)
        self.assertEqual(stationary.rotation_error, saved.rotation_error)


class CanonicalAngularSourceTests(unittest.TestCase):
    def test_history_witness_has_one_independent_source_result_on_shared_work(self):
        compiler, ledger = source("same_source_history.ok")
        results = []
        # These are complete independent reconstructions sharing the original
        # admitted work and bounded pure cache, never a refreshed allowance.
        for end in (F(1), F(16384), F(1), F(1)):
            ref = build_reference(compiler.model, end=end, mode="observation", work=compiler.reach_work)
            state = ref._state_at(F(1), "after")
            value = angular.root_support(ref, "ball", F(1), state)
            self.assertEqual(value.exact_omega, (F(0),)*3)
            self.assertEqual(state.torques["ball"].axis, "world_x")
            self.assertEqual(state.torques["ball"].started, 1)
            results.append((value.exact_quaternion, value.frozen_projection, value.rotation_error))
        self.assertTrue(all(value == results[0] for value in results))
        self.assertLess(ledger.operations, 100000)

    def test_pause_resume_uses_accumulated_elapsed_and_original_origin(self):
        ref, _ = reader("paused-resumed-origin.ok", F(3, 2))
        state = ref._state_at(F(3, 2), "after")
        self.assertEqual(state.torques["ball"].support.exact_omega, (F(0),)*3)
        self.assertEqual(state.torques["ball"].axis, "world_x")
        self.assertEqual(state.actions["turn"].elapsed_at(F(3, 2)), F(1))
        self.assertEqual(state.torques["carrier"].support.time, F(0))

    def test_error_only_force_boundaries_preserve_discriminating_full_recipe(self):
        ref, _ = reader("unchanged-force-origin.ok", F(1))
        state = ref._state_at(F(1), "after")
        self.assertEqual(state.torques["ball"].support.time, F(0))
        value = angular.root_support(ref, "ball", F(1), state)
        row = EXPECTED["unchanged_force_source_origin"]
        q = [str(int(component * exact.GRID)) for component in value.exact_quaternion]
        self.assertEqual(q, row["expected_quaternion_grid_integers"])
        self.assertNotEqual(q, row["incorrect_half_plus_half_quaternion_grid_integers"])
        self.assertEqual(value.exact_omega, (F(0), F(0), F(1, 4)))

    def test_evolving_permutation_has_exact_canonical_release_rate(self):
        ref, _ = reader("evolved-permutation.ok", F(1))
        before = ref._state_at(F(1), "before")
        pre = angular.frame_support(ref, "ball.frame", F(1), before)
        expected = EXPECTED["source_permutations_and_parallel_impulse"]["evolved-permutation.ok"]
        self.assertEqual([str(int(v * exact.GRID)) for v in pre.exact_quaternion],
                         expected["pre_release_quaternion_grid_integers"])
        state = ref._state_at(F(1), "after")
        self.assertEqual(state.torques["ball"].support.exact_omega, (F(0), F(3, 2), F(0)))
        self.assertEqual(state.torques["ball"].axis, "world_y")
        self.assertGreater(state.dynamic["ball"].omega_error, 0)

    def test_nonzero_parallel_impulse_keeps_exact_zero_and_real_transfer(self):
        ref, _ = reader("nonzero-parallel-impulse.ok", F(0))
        state = ref._state_at(F(0), "after")
        self.assertEqual(state.torques["ball"].support.exact_omega, (F(0),)*3)
        self.assertEqual(state.impulses["ball"]["applied_count"], 1)
        self.assertGreater(state.dynamic["ball"].omega_error, 0)
        self.assertGreater(state.dynamic["ball"].actual.velocity[0].lo, 0)

    def test_signed_true_off_axis_values_are_both_refused(self):
        for name in ("off-axis-positive.ok", "off-axis-negative.ok"):
            with self.subTest(source=name), self.assertRaises(ReferenceError) as caught:
                reader(name, F(0))
            self.assertEqual(caught.exception.details["torque_reason"], "incoming_axis")

    def test_legacy_nonzero_central_impulse_still_materializes_rotation(self):
        text = (INPUTS / "unchanged-force-origin.ok").read_text()
        text = text.replace('force ball @ "zero-force" using vector(world, 0[N], 0[N], 0[N]) for 0.25[s];',
            'impulse ball using vector(world, 1[N*s], 0[N*s], 0[N*s]) at point(ball.frame, 0[m], 0[m], 0[m]);')
        self.assertIn("impulse ball", text)
        ref, _ = reader("unchanged-force-origin.ok", F(1), text=text)
        support = ref._state_at(F(1), "after").torques["ball"].support
        self.assertEqual(support.time, F(1, 2))
        self.assertIsNotNone(support.frozen_projection)
        self.assertEqual(support.exact_omega, (F(0), F(0), F(1, 4)))

    def test_angular_walk_has_no_smaller_recipe_encoding_depth(self):
        a, steps = arithmetic()
        unit = (F(1), F(0), F(0), F(0))
        pose = SimpleNamespace(rotation=unit)
        sites, joints, incoming = {}, {}, {}
        for index in range(100):
            sites[f"o{index}.in"] = SimpleNamespace(owner=f"o{index}", pose=pose)
            sites[f"o{index}.out"] = SimpleNamespace(owner=f"o{index}", pose=pose)
            if index:
                joints[f"j{index}"] = SimpleNamespace(kind="fixed", parent=f"o{index-1}.out",
                                                       child=f"o{index}.in")
                incoming[f"o{index}"] = ("joint", f"j{index}")
        q = exact.rotation(unit, a)
        support = angular.AngularSupport(F(0), angular.IDENTITY, angular.ZERO,
            q, (F(0),)*3, rotation_error=angular.PRODUCT_ERROR)
        state = SimpleNamespace(modes={"o0": "prescribed"}, claims={},
            torques={"o0": SimpleNamespace(support=support)})
        ref = SimpleNamespace(a=a, model=SimpleNamespace(sites=sites, joints=joints, follows={}),
                              _incoming=lambda state: incoming)
        result = angular.frame_support(ref, "o99.out.frame", F(0), state)
        self.assertEqual(result.exact_omega, (F(0),)*3)
        self.assertEqual(result.exact_quaternion, q)
        self.assertLess(steps[0], 100000)


if __name__ == "__main__":
    unittest.main()
