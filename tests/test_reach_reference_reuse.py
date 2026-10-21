"""Independent interval reuse retains exact meanings and shared work."""
from fractions import Fraction as F
import unittest

from ontokin.reach_reference import (
    Interval, MAX_CACHE, ReferenceError, _Arithmetic, _PoseArithmetic, build_reference,
)
from ontokin.construction import compile_construction
from reach_agent_support import source_case


class Work:
    def __init__(self):
        self.operations = 0
        self.cancel = None

    def tick(self):
        self.operations += 1
        if self.cancel is not None:
            raise self.cancel
        if self.operations > 100000:
            raise RuntimeError("shared work exhausted")


class IndependentPoseReuseTests(unittest.TestCase):
    def setUp(self):
        self.work = Work()
        self.a = _Arithmetic(work=self.work)
        self.p = _PoseArithmetic(self.a)

    def test_zero_vectors_and_scalar_quaternions_preserve_exact_answers(self):
        zero = self.p.vector((0, 0, 0))
        vector = self.p.vector((F(3, 7), -2, 5))
        self.assertEqual(self.p.cross(zero, vector), zero)
        self.assertEqual(self.p.add(zero, vector), vector)
        self.assertEqual(self.p.scale(vector, 0), zero)
        self.assertEqual(self.p.scale(vector, 1), vector)
        for scale, expected in ((7, 1), (-7, -1)):
            q = self.p.quaternion((scale, 0, 0, 0))
            self.assertEqual(q, self.p.vector((expected, 0, 0, 0)))
            self.assertEqual(self.p.rotate(q, vector), vector)
        with self.assertRaises(ReferenceError):
            self.p.quaternion((0, 0, 0, 0))

    def test_cached_composition_charges_and_preserves_callback_identity(self):
        parent = self.p.make(position=(1, 2, 3), omega=(0, 0, 2))
        local = self.p.make(position=(3, 0, 0))
        result = self.p.compose(parent, local)
        self.assertEqual(result.position, self.p.vector((4, 2, 3)))
        self.assertEqual(result.velocity, self.p.vector((0, 6, 0)))
        before = self.work.operations
        self.assertIs(self.p.compose(parent, local), result)
        self.assertGreater(self.work.operations, before)
        interruption = RuntimeError("cancel cached independent composition")
        self.work.cancel = interruption
        with self.assertRaises(RuntimeError) as caught:
            self.p.compose(parent, local)
        self.assertIs(caught.exception, interruption)

    def test_equal_poses_share_pure_results_but_changed_rates_do_not(self):
        parent = self.p.make(omega=(0, 0, 2))
        local = self.p.make(position=(3, 0, 0))
        result = self.p.compose(parent, local)
        self.assertIs(self.p.compose(self.p.make(omega=(0, 0, 2)), local), result)
        changed = self.p.compose(self.p.make(omega=(0, 0, -2)), local)
        self.assertEqual(changed.position, result.position)
        self.assertEqual(changed.velocity, self.p.vector((0, -6, 0)))
        self.assertNotEqual(changed.omega, result.omega)

    def test_saturated_cache_recomputes_pi_without_allocating_extra_capacity(self):
        expected = self.a.pi()
        for index in range(MAX_CACHE + 1):
            self.a.remember(("test", index), Interval(F(index), F(index)))
        self.assertEqual(len(self.a.cache), MAX_CACHE)
        self.assertEqual(self.a.pi(), expected)
        self.assertEqual(len(self.a.cache), MAX_CACHE)


class IndependentRecordingPoseTests(unittest.TestCase):
    def test_recording_poses_preserve_full_enclosures_without_exposing_rates(self):
        for name, time, carrier in (("P01", F(1, 4), "rig.arm.forearm.tip.frame"),
                                    ("P16", F(5, 2), "payload.frame")):
            compiler = compile_construction(source_case(name))
            reference = build_reference(compiler.model, end=time, work=compiler.reach_work)
            for side in ("before", "after"):
                selected = reference.recording_pose_enclosure(carrier, time, side)
                self.assertFalse(hasattr(selected, "velocity"))
                self.assertFalse(hasattr(selected, "omega"))
                full = reference.pose_enclosure(carrier, time, side)
                self.assertEqual(selected.position, full.position)
                self.assertEqual(selected.orientation, full.orientation)
                self.assertTrue(any(value.magnitude for value in (*full.velocity, *full.omega)))
                # Full observations and point bounds still use the complete
                # derivative path after a pose-only cache entry exists.
                snapshot = reference.sample(time, side)
                self.assertIn("velocity_m_per_s", snapshot["objects"][carrier.split(".")[0]])

    def test_recording_selection_does_not_admit_unknown_carriers_or_sides(self):
        compiler = compile_construction(source_case("P01"))
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        for carrier, side in (("missing.frame", "after"), ("world", "left")):
            with self.subTest(carrier=carrier, side=side), self.assertRaises(ReferenceError):
                reference.recording_pose_enclosure(carrier, F(1, 4), side)


if __name__ == "__main__":
    unittest.main()
