"""The recording's narrower output preserves complete source boundary history."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.reach_export import _boundary_record, reach_prefix_plan
from ontokin.reach_runtime import ReachSimulator
from reach_agent_support import source_case


class BoundaryObserver(ReachSimulator):
    def snapshot(self, time, side):
        return self.recording_boundary(time, side)


class RecordingBoundaryTests(unittest.TestCase):
    def test_every_promised_history_matches_complete_source_snapshots(self):
        # Moving roots, two arms, release, impulses/forces, completed handoffs
        # and the large translated-arm source all use the same projection.
        for name, time in (("P01", F(0)), ("P01", F(3)), ("P05", F(1)),
                           ("P11", F(1)), ("P16", F(2)), ("P18", F(2)),
                           ("P19", F(2)), ("L01", F(2)), ("L02", F(1)),
                           ("L03", F(2)), ("P23", F(3))):
            for side in ("before", "after"):
                with self.subTest(case=name, time=time, side=side):
                    complete = compile_construction(source_case(name))
                    full_simulator = ReachSimulator(complete.model, work=complete.reach_work)
                    full = full_simulator.advance(time, side)
                    scoped = compile_construction(source_case(name))
                    scoped_simulator = BoundaryObserver(scoped.model, work=scoped.reach_work)
                    actual = scoped_simulator.advance(time, side)
                    expected_record = _boundary_record(time, full, full,
                        full_simulator.incoming_releases_at(time))
                    actual_record = _boundary_record(time, actual, actual,
                        scoped_simulator.incoming_releases_at(time))
                    self.assertEqual(actual_record, expected_record)
                    self.assertLess(scoped.budget.operations, complete.budget.operations)

    def test_planner_allocates_only_the_promised_boundary_output(self):
        compiler = compile_construction(source_case("P01"))
        with patch.object(ReachSimulator, "snapshot",
                          side_effect=AssertionError("Unrequested complete snapshot")):
            plan = reach_prefix_plan(compiler.model, F(3), work=compiler.reach_work)
        self.assertEqual(plan.boundaries, (F(0), F(2), F(3)))
        self.assertEqual(len(plan.boundary_records), 3)
        for record in plan.boundary_records:
            for side in ("before", "after"):
                self.assertEqual(set(record["pose_authorities_" + side]), set(compiler.model.objects))
                self.assertEqual(set(record["force_states_" + side]), set(compiler.model.objects))
                self.assertEqual(set(record["impulse_states_" + side]), set(compiler.model.objects))
                self.assertEqual(set(record["action_states_" + side]), set(compiler.model.actions))

    def test_unselected_site_finiteness_and_whole_boundary_failures_remain(self):
        marker = RuntimeError("unselected site cannot be exposed")
        compiler = compile_construction(source_case("P01"))
        simulator = BoundaryObserver(compiler.model, work=compiler.reach_work)
        original = simulator._kinematics

        class InvalidFrame:
            @property
            def position(self):
                raise marker

        def invalid_site(time, state):
            objects, frames = original(time, state)
            return objects, {**frames, "unselected.site.frame": InvalidFrame()}

        with patch.object(simulator, "_kinematics", invalid_site):
            with self.assertRaises(RuntimeError) as caught:
                simulator.advance(F(0), "before")
        self.assertIs(caught.exception, marker)
        compiler = compile_construction(source_case("L04"))
        simulator = BoundaryObserver(compiler.model, work=compiler.reach_work)
        with self.assertRaises(OntoKinError) as caught:
            simulator.advance(F(1, 2), "after")
        self.assertEqual(caught.exception.diagnostic.details["reach_code"], "reach_unreachable")

    def test_history_outputs_remain_private_and_cancellation_is_original(self):
        armed = False
        marker = RuntimeError("cancel recording history projection")

        def check():
            if armed:
                raise marker

        compiler = compile_construction(source_case("P16"), check=check)
        simulator = BoundaryObserver(compiler.model, work=compiler.reach_work)
        first = simulator.advance(F(2), "after")
        first["objects"]["payload"]["impulses"]["last_applications"].append({"unexpected": True})
        first["objects"]["payload"]["forces"]["started_count"] = -1
        second = simulator.recording_boundary(F(2), "after")
        self.assertNotIn({"unexpected": True}, second["objects"]["payload"]["impulses"]["last_applications"])
        self.assertGreaterEqual(second["objects"]["payload"]["forces"]["started_count"], 0)
        armed = True
        with self.assertRaises(RuntimeError) as caught:
            simulator.recording_boundary(F(2), "after")
        self.assertIs(caught.exception, marker)
        self.assertIs(compiler.reach_work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
