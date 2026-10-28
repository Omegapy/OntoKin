"""Independent source-bound translation factoring keeps exact proof operands."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_reference import MAX_CACHE, MAX_OPERAND_BITS, Interval, ReferenceError, _Arithmetic, build_reference
from reach_agent_support import source_case


def reference_case(name, end):
    compiler = compile_construction(source_case(name))
    return build_reference(compiler.model, end=end, work=compiler.reach_work), compiler.reach_work


class IndependentSourceBasisAffineTests(unittest.TestCase):
    def forced_basis(self, reference, carrier, start, end, state):
        original = _Arithmetic.lookup

        def no_composition_cache(arithmetic, key):
            if key[0] == "source_bound_compose":
                arithmetic.tick()
                return None
            return original(arithmetic, key)

        with patch.object(_Arithmetic, "lookup", new=no_composition_cache):
            return reference._source_basis(carrier, start, end, copy.deepcopy(state))

    def test_translated_chains_restore_complete_rotation_times_path_offset(self):
        reference, work = reference_case("P23", F(1, 2))
        initial = reference._state_at(F(0), "after")
        first = 'rig.arms["first"].forearm.tip.frame'
        following = 'rig.arms["part-01"].forearm.tip.frame'
        for changed_field in (None, "anchor_rotation", "coordinate"):
            state = copy.deepcopy(initial)
            if changed_field == "anchor_rotation":
                state.rotation_errors["rig"] += F(1, 1000)
            elif changed_field == "coordinate":
                for active in state.actions.values():
                    active.initial = (active.initial[0], .001)
            with self.subTest(changed_field=changed_field):
                baseline = reference._source_basis(first, F(0), F(1, 2), state)
                before = work.operations
                actual = reference._source_basis(following, F(0), F(1, 2), state)
                reused = work.operations - before
                before = work.operations
                forced = self.forced_basis(reference, following, F(0), F(1, 2), state)
                recomputed = work.operations - before
                self.assertEqual(actual, forced)
                self.assertGreater(reused, 0)
                self.assertLess(reused, recomputed)
                self.assertGreater(actual.extent, baseline.extent)
                self.assertGreater(actual.offset, baseline.offset)
                rotation = actual.rotation_error - F(1, 1 << 50)
                correction = ((actual.extent - baseline.extent) / (1 << 53)
                              + (actual.offset - baseline.offset) * rotation)
                self.assertEqual(actual.position_error, baseline.position_error + correction)
                self.assertEqual(replace(actual, extent=baseline.extent, offset=baseline.offset,
                                         position_error=baseline.position_error), baseline)
                self.assertGreater(actual.trig, 0)
                self.assertGreater(actual.products, 0)
                if changed_field == "anchor_rotation":
                    self.assertGreater(actual.anchor_rotation, 0)
                elif changed_field == "coordinate":
                    self.assertGreater(actual.coordinate, 0)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)

    def test_translated_source_states_have_exact_affine_position_allowances(self):
        reference, work = reference_case("P01", F(1, 2))
        state = reference._state_at(F(0), "after")
        carrier, start, end = "rig.tool.frame", F(0), F(1, 2)
        baseline = reference._source_basis(carrier, start, end, state)
        for displacement in (F(1), F(7, 8), F(100)):
            with self.subTest(displacement=displacement):
                shifted = copy.deepcopy(state)
                position = (Interval(displacement, displacement), Interval(F(0), F(0)), Interval(F(0), F(0)))
                shifted.positions["rig"] = shifted.ideal_positions["rig"] = position
                before = work.operations
                actual = reference._source_basis(carrier, start, end, shifted)
                reused = work.operations - before
                before = work.operations
                recomputed = self.forced_basis(reference, carrier, start, end, shifted)
                uncached = work.operations - before
                self.assertEqual(actual, recomputed)
                self.assertEqual(actual.extent, baseline.extent + displacement)
                self.assertEqual(actual.position_error, baseline.position_error + displacement / (1 << 53))
                self.assertEqual(replace(actual, extent=baseline.extent, position_error=baseline.position_error), baseline)
                self.assertGreater(reused, 0)
                self.assertLess(reused, uncached)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)

    def test_changed_anchor_actual_and_ideal_derivatives_keep_distinct_results(self):
        reference, _ = reference_case("P01", F(1, 2))
        state = reference._state_at(F(0), "after")
        carrier, start, end = "rig.tool.frame", F(0), F(1, 2)
        baseline = reference._source_basis(carrier, start, end, state)
        for changed_field in ("rotation_anchor", "actual_coordinate", "ideal_coordinate"):
            changed = copy.deepcopy(state)
            if changed_field == "rotation_anchor":
                changed.rotation_errors["rig"] += F(1, 1000)
            else:
                active = changed.actions["reach"]
                if changed_field == "actual_coordinate":
                    active.initial = (active.initial[0], .001)
                else:
                    active.ideal_initial = (active.ideal_initial[0], F(1, 1000))
            with self.subTest(field=changed_field):
                actual = reference._source_basis(carrier, start, end, changed)
                self.assertEqual(actual, self.forced_basis(reference, carrier, start, end, changed))
                self.assertNotEqual(actual, baseline)
        dynamic, _ = reference_case("P16", F(3))
        released = dynamic._state_at(F(2), "after")
        carrier = "payload.origin.frame"
        baseline = dynamic._source_basis(carrier, F(2), F(5, 2), released)
        for changed_field in ("velocity_error", "omega_error"):
            changed = copy.deepcopy(released)
            anchor = changed.dynamic["payload"]
            setattr(anchor, changed_field, getattr(anchor, changed_field) + F(1, 1000))
            with self.subTest(field=changed_field):
                actual = dynamic._source_basis(carrier, F(2), F(5, 2), changed)
                self.assertEqual(actual, self.forced_basis(dynamic, carrier, F(2), F(5, 2), changed))
                self.assertNotEqual(actual, baseline)

    def test_factor_reuse_keeps_bounded_storage_source_operand_guards_and_callback(self):
        reference, work = reference_case("P01", F(1, 2))
        state = reference._state_at(F(0), "after")
        expected = reference._source_basis("rig.tool.frame", F(0), F(1, 2), state)
        for index in range(MAX_CACHE + 1):
            reference.a.remember(("other", index), F(index))
        self.assertEqual(len(reference.a.cache), MAX_CACHE)
        self.assertEqual(reference._source_basis("rig.tool.frame", F(0), F(1, 2), copy.deepcopy(state)), expected)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        changed = copy.deepcopy(state)
        huge = F(1 << MAX_OPERAND_BITS)
        changed.positions["rig"] = (Interval(huge, huge), Interval(F(0), F(0)), Interval(F(0), F(0)))
        with self.assertRaises(ReferenceError) as caught:
            reference._source_basis("rig.tool.frame", F(0), F(1, 2), changed)
        self.assertEqual(caught.exception.code, "resource")
        marker = RuntimeError("cancel warmed affine source bound")
        with patch.object(work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                reference._source_basis("rig.tool.frame", F(0), F(1, 2), copy.deepcopy(state))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
