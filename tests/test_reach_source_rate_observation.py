"""Selected source rates retain complete source execution and finite frames."""
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.reach_runtime import ReachSimulator
from tools.reach_source_rates import (
    RateAuditError, execute_source_rate_audit, observation_from_snapshot,
    observe_source_rates,
)


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"
TIP = "rig.arm.forearm.tip.frame"


def source(name):
    root = DATA / "draft2-supplements" if name.startswith("l") else DATA
    return load_file_manifest(root / (name + ".files.json"))


class SelectedSourceRateObservationTests(unittest.TestCase):
    def test_selected_values_equal_complete_actual_source_snapshots(self):
        for name, time, side, carriers in (
                ("p01", F(1, 4), "after", ["world", TIP]),
                ("p16", F(9, 4), "after", ["payload.frame", TIP]),
                ("l02", F(3, 4), "after", [TIP]),
                ("l04", F(1, 2), "before", [TIP])):
            with self.subTest(case=name, time=time, side=side):
                complete = compile_construction(source(name))
                snapshot = ReachSimulator(complete.model, work=complete.reach_work).advance(time, side)
                expected = observation_from_snapshot(complete.model, snapshot,
                    carriers=carriers, work=complete.reach_work)
                selected = compile_construction(source(name))
                with patch.object(ReachSimulator, "snapshot",
                                  side_effect=AssertionError("Unrequested full snapshot was built")):
                    actual = observe_source_rates(selected.model, time=time, side=side,
                        carriers=carriers, work=selected.reach_work)
                self.assertEqual(actual, expected)
                self.assertLess(selected.budget.operations, complete.budget.operations)

    def test_unselected_frame_failure_and_projection_cancellation_propagate(self):
        marker = RuntimeError("unselected source site cannot be exposed")
        built = compile_construction(source("p01"))

        class InvalidFrame:
            @property
            def position(self):
                raise marker

        original = ReachSimulator._kinematics

        def with_invalid_site(simulator, time, state):
            objects, frames = original(simulator, time, state)
            if time == F(1, 4):
                frames = dict(frames)
                frames["unselected.site.frame"] = InvalidFrame()
            return objects, frames

        with patch.object(ReachSimulator, "_kinematics", with_invalid_site):
            with self.assertRaises(RuntimeError) as caught:
                observe_source_rates(built.model, time=F(1, 4), side="after",
                                     carriers=["world"], work=built.reach_work)
        self.assertIs(caught.exception, marker)

        armed = False
        interruption = RuntimeError("cancel selected source projection")

        def check():
            if armed:
                raise interruption

        built = compile_construction(source("p01"), check=check)

        def cancel_at_projection(simulator, time, state):
            nonlocal armed
            result = original(simulator, time, state)
            if time == F(1, 4):
                armed = True
            return result

        with patch.object(ReachSimulator, "_kinematics", cancel_at_projection):
            with self.assertRaises(RuntimeError) as caught:
                observe_source_rates(built.model, time=F(1, 4), side="after",
                                     carriers=["world"], work=built.reach_work)
        self.assertIs(caught.exception, interruption)
        self.assertIs(built.reach_work.callback_error, interruption)

    def test_whole_boundary_failure_still_rejects_an_unrelated_selected_carrier(self):
        built = compile_construction(source("l04"))
        with self.assertRaises(OntoKinError) as caught:
            observe_source_rates(built.model, time=F(1, 2), side="after",
                                 carriers=["world"], work=built.reach_work)
        self.assertEqual(caught.exception.diagnostic.details["reach_code"], "reach_unreachable")

    def test_selection_rejects_duplicates_aliases_and_invalid_shapes(self):
        for carriers in ([], [TIP, TIP], ["rig.arm.forearm.tip"], ["absent.frame"],
                         [False], ["world"] * 4097, {"world"}):
            with self.subTest(carriers=repr(carriers)[:80]):
                built = compile_construction(source("p01"))
                with self.assertRaises(RateAuditError):
                    observe_source_rates(built.model, time=F(0), side="before",
                                         carriers=carriers, work=built.reach_work)

        for time, side in ((True, "after"), (0.25, "after"), ("1e99", "after"),
                           (F(-1), "after"), (F(4), "after"), (F(0), "left")):
            with self.subTest(time=time, side=side):
                built = compile_construction(source("p01"))
                with self.assertRaises(RateAuditError):
                    observe_source_rates(built.model, time=time, side=side,
                                         carriers=["world"], work=built.reach_work)

    def test_terminal_p23_rates_keep_the_original_shared_request_budget(self):
        carriers = ['rig.arms["first"].forearm.tip.frame',
                    'rig.arms["first"].forearm.frame']
        for time, side in ((F(2), "after"), (F(3), "before"), (F(3), "after")):
            with self.subTest(time=time, side=side):
                result = execute_source_rate_audit(source("p23"), time=time, side=side,
                                                  carriers=carriers)
                self.assertEqual(result["status"], "proved")
                self.assertEqual(result["request_operation_limit"], 100000)
                self.assertLessEqual(result["request_operations"], 100000)
                self.assertEqual(result["source_snapshot_scope"],
                                 "selected_rates_with_complete_kinematic_finiteness")
                self.assertEqual(result["criterion_status"], "proposed_not_adopted")
                self.assertFalse(result["release_acceptance"])


if __name__ == "__main__":
    unittest.main()
