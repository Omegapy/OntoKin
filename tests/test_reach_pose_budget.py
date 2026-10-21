"""Exact projection reuse across separate poses in one bounded request."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachExecutionWork, float_bits
from ontokin.reach_pose import PoseValue, ReachPoseOps, RotationValue, ZERO


def bits(values):
    return tuple(map(float_bits, values))


def pose(ops, rotation, offset=0):
    # Distinct pose-local projection dictionaries keep stationary-pose reuse
    # from concealing whether the shared component projection was reused.
    return PoseValue((F(offset), F(0), F(0)), rotation, ZERO, ZERO, F(0), ops)


class ReachPoseBudgetTests(unittest.TestCase):
    def test_distinct_poses_reuse_exact_components_with_identical_binary64_bits(self):
        calls = 0

        def check():
            nonlocal calls
            calls += 1

        work = ReachExecutionWork(check=check)
        ops = ReachPoseOps(work)
        minimum = float.fromhex("0x0.0000000000001p-1022")
        cases = (
            ((F(1), F(0), F(0), F(0)), (1.0, 0.0, 0.0, 0.0)),
            ((F(3, 5), F(-4, 5), F(0), F(0)), (0.6, -0.8, 0.0, 0.0)),
            ((F(3), F(-4), F(0), F(0)), (0.6, -0.8, 0.0, 0.0)),
            ((F(-3), F(4), F(0), F(0)), (-0.6, 0.8, 0.0, 0.0)),
            ((F(1), F(-1, 1 << 1074), F(-1, 1 << 1075), F(0)),
             (1.0, -minimum, 0.0, 0.0)),
        )
        for index, (components, expected) in enumerate(cases):
            with self.subTest(components=components):
                first = pose(ops, RotationValue(components), 2 * index)
                cold = first.orientation
                self.assertEqual(bits(cold), bits(expected))
                # A different error allowance must stay on its own rotation,
                # while an equal exact component tuple may share public bits.
                second = pose(ops, RotationValue(components, F(1, 1 << 60)), 2 * index + 1)
                self.assertIsNot(first, second)
                self.assertEqual(second._projection, {})
                before = calls
                with patch("ontokin.reach_pose.sqrt_rational_binary64",
                           side_effect=AssertionError("Cached projection recomputed a square root")):
                    cached = second.orientation
                self.assertEqual(bits(cached), bits(cold))
                self.assertEqual(second.rotation.components, components)
                self.assertEqual(second.angular_error_rad, F(1, 1 << 60))
                self.assertGreater(calls, before)
                self.assertEqual(calls, work.operations)
        self.assertEqual(sum(work.counts.values()), work.operations)

    def test_materialized_projection_bypasses_normal_component_cache(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        original = pose(ops, RotationValue((F(3), F(-4), F(0), F(0))))
        anchor = ops.materialize(original)
        saved = anchor.rotation.frozen_projection
        self.assertIsNotNone(saved)
        # Prime the ordinary cache with these same imported exact components.
        ordinary = pose(ops, RotationValue(anchor.rotation.components), 1)
        _ = ordinary.orientation
        before = tuple(work._cache.items())
        advanced = pose(ops, anchor.rotation, 2)
        with patch.object(work, "lookup",
                          side_effect=AssertionError("A frozen anchor consulted the normal cache")):
            actual = advanced.orientation
        self.assertIs(actual, saved)
        self.assertEqual(bits(actual), bits(original.orientation))
        self.assertEqual(tuple(work._cache.items()), before)

    def test_eviction_recomputes_identical_projection_with_bounded_storage(self):
        work = ReachExecutionWork(max_cache_entries=1)
        ops = ReachPoseOps(work)
        rotation = RotationValue((F(3), F(-4), F(0), F(0)))
        first = pose(ops, rotation).orientation
        self.assertEqual(work.record()["cache_entries"], 1)
        other = pose(ops, RotationValue((F(1), F(0), F(0), F(0))), 1)
        self.assertEqual(bits(other.orientation), bits((1.0, 0.0, 0.0, 0.0)))
        self.assertEqual(work.record()["cache_entries"], 1)
        before = work.counts["sqrt_binary64"]
        again = pose(ops, rotation, 2).orientation
        self.assertEqual(bits(again), bits(first))
        self.assertGreater(work.counts["sqrt_binary64"], before)
        self.assertEqual(work.record()["cache_entries"], 1)
        self.assertGreater(work.counts.get("cache_evict", 0), 0)

    def test_cancelled_shared_projection_keeps_new_pose_unpublished(self):
        calls = 0
        cancel_at = None
        marker = RuntimeError("cancel shared quaternion projection")

        def check():
            nonlocal calls
            calls += 1
            if calls == cancel_at:
                raise marker

        work = ReachExecutionWork(check=check, max_cache_entries=2)
        ops = ReachPoseOps(work)
        rotation = RotationValue((F(3), F(-4), F(0), F(0)))
        _ = pose(ops, rotation).orientation
        _ = pose(ops, RotationValue((F(1), F(0), F(0), F(0))), 1).orientation
        before = tuple(work._cache.items())
        next_pose = pose(ops, rotation, 2)
        # Pose lookup and shared lookup succeed; cancellation at promotion
        # must precede any recency mutation or pose-local publication.
        cancel_at = calls + 3
        with self.assertRaises(RuntimeError) as raised:
            _ = next_pose.orientation
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(next_pose._projection, {})
        self.assertEqual(tuple(work._cache.items()), before)
        self.assertEqual(calls, work.operations + 1)
        self.assertEqual(sum(work.counts.values()), work.operations)


if __name__ == "__main__":
    unittest.main()
