"""Independent ledger sharing keeps history, rollback and logical bounds."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_reference import ReachReference, ReferenceError, build_reference
from reach_agent_support import source_case


class IndependentStateSharingTests(unittest.TestCase):
    def test_coordinate_and_mixed_ledgers_equal_complete_private_copies(self):
        original = ReachReference._coordinate_boundary_plan

        def complete_copies(reference, time):
            completions, _, changed, coordinates = original(reference, time)
            return completions, False, changed, coordinates

        for name in ("P01", "P16", "L01", "L02", "P23"):
            with self.subTest(case=name):
                shared = compile_construction(source_case(name))
                actual = build_reference(shared.model, end=shared.model.duration,
                    mode="observation", work=shared.reach_work)
                complete = compile_construction(source_case(name))
                with patch.object(ReachReference, "_coordinate_boundary_plan", complete_copies):
                    expected = build_reference(complete.model, end=complete.model.duration,
                        mode="observation", work=complete.reach_work)
                self.assertEqual(actual.boundaries, expected.boundaries)
                self.assertEqual(actual._before, expected._before)
                self.assertEqual(actual._after, expected._after)
                self.assertEqual(actual._release_records, expected._release_records)
                self.assertLessEqual(shared.budget.operations, complete.budget.operations)
                if name != "P16":
                    self.assertLess(shared.budget.operations, complete.budget.operations)

    def test_interrupted_coordinate_completion_cannot_change_retained_history(self):
        compiler = compile_construction(source_case("P01"))
        marker = RuntimeError("interrupt after staging coordinate completion")
        captured = []
        original = ReachReference._finish

        def interrupt(reference, *args):
            before = copy.deepcopy(reference._state)
            original(reference, *args)
            captured.append((reference, before))
            raise marker

        with patch.object(ReachReference, "_finish", interrupt):
            with self.assertRaises(RuntimeError) as caught:
                build_reference(compiler.model, end=3, work=compiler.reach_work)
        self.assertIs(caught.exception, marker)
        self.assertEqual(len(captured), 1)
        reference, before = captured[0]
        self.assertEqual(reference._state, before)
        self.assertEqual(reference._after[-1], before)
        self.assertEqual(reference._state.actions["reach"].status, "running")
        self.assertIsNone(reference._state.actions["reach"].terminal)

    def test_shared_noop_boundaries_retain_original_logical_state_limit(self):
        compiler = compile_construction(source_case("P23"))
        prototype = compiler.model.events[0]
        # Synthetic extra observation boundaries contain no source mutations.
        # Sharing physical storage must not admit an unbounded logical ledger.
        compiler.model.events = [replace(prototype, time=F(index, 64), events=[])
                                 for index in range(129)]
        with self.assertRaises(ReferenceError) as caught:
            build_reference(compiler.model, end=3, mode="observation", work=compiler.reach_work)
        self.assertEqual(caught.exception.code, "resource")
        self.assertIn("retained-state limit", str(caught.exception))
        self.assertLess(compiler.budget.operations, 100000)

    def test_coordinate_copy_retains_original_callback_exception(self):
        armed = False
        marker = RuntimeError("cancel coordinate state allocation")

        def check():
            if armed:
                raise marker

        compiler = compile_construction(source_case("P01"), check=check)
        original = ReachReference._copy_coordinate_state

        def cancel(reference, *args):
            nonlocal armed
            armed = True
            return original(reference, *args)

        with patch.object(ReachReference, "_copy_coordinate_state", cancel):
            with self.assertRaises(RuntimeError) as caught:
                build_reference(compiler.model, end=3, work=compiler.reach_work)
        self.assertIs(caught.exception, marker)
        self.assertIs(compiler.reach_work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
