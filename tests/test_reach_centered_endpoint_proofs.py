"""Only sufficient radius-aware proofs may bypass ordinary endpoint cells."""
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.reach_conformance import (
    _Bounds, _Cell, _key_comparisons, _recording_centered_comparison,
)
from ontokin.reach_numeric import ReachExecutionWork as Work
from ontokin.reach_reference_center import _CenteredPose


def pose(position=(0, 0, 0), quaternion=(1, 0, 0, 0), *, pr=0, qr=0, axis=2):
    return _CenteredPose(tuple(F(value) for value in position), tuple(F(value) for value in quaternion),
                         F(pr.numerator, pr.denominator) if type(pr) is F else F(pr),
                         F(qr.numerator, qr.denominator) if type(qr) is F else F(qr), axis)


def point(value):
    value = F(value)
    return _Cell(value, value)


def compare(ideal, position=(0., 0., 0.), quaternion=(0., 0., 0., 1.),
            limits=(.001, .001), *, work=None, previous=None, completed=()):
    arithmetic = _Bounds(work if work is not None else Work(), cache_intermediates=False)
    return _recording_centered_comparison(ideal, position, quaternion, limits, arithmetic,
                                         previous=previous, completed=completed)


class CenteredEndpointTests(unittest.TestCase):
    def test_radius_is_in_both_actual_inequalities_and_antipodes_remain_valid(self):
        radius = F(1, 1 << 104)
        ideal = pose((-radius, 0, 0), (1-radius, 0, 0, 0), pr=radius, qr=radius)
        result = compare(ideal)
        self.assertIsNotNone(result)
        self.assertEqual(result["position_error"], 2*radius)
        self.assertEqual(result["quaternion_error"], 4*radius)
        opposite = compare(ideal, quaternion=(0., 0., 0., -1.))
        self.assertEqual(opposite["position_error"], result["position_error"])
        self.assertEqual(opposite["quaternion_error"], result["quaternion_error"])
        self.assertIsNone(compare(ideal, limits=(0, .001)))
        self.assertIsNone(compare(ideal, limits=(.001, 0)))

    def test_zero_near_zero_and_hostile_values_never_receive_a_sufficient_proof(self):
        ideal = pose()
        for raw in ((0., 0., 0., 0.), (0., 0., 0., 2.0**-100), (0., 0., 1., 0.)):
            with self.subTest(raw=raw):
                self.assertIsNone(compare(ideal, quaternion=raw))
        self.assertIsNone(compare(ideal, position=(.1, 0., 0.), limits=(.001, .001)))
        self.assertIsNone(compare(ideal, quaternion=(.1, 0., 0., 1.), limits=(.001, .001)))
        self.assertIsNone(compare(ideal, quaternion=(0., 0., 0., 0.), limits=(1., 100.)))

    def test_tight_claim_uses_complete_ordinary_enclosures_on_the_same_work(self):
        work, reads = Work(), []
        arithmetic = _Bounds(work, cache_intermediates=False)
        centered = pose(qr=F(1, 1 << 104))
        ordinary = SimpleNamespace(position=tuple(map(point, (0, 0, 0))),
                                   orientation=tuple(map(point, (1, 0, 0, 0))))
        def enclosures(carriers, time, side, recording_context=None):
            reads.append((tuple(carriers), time, side, work.operations))
            return {carrier: ordinary for carrier in carriers}
        reference = SimpleNamespace(
            _recording_centered_poses=lambda carriers, *args, **kwargs: {carrier: centered for carrier in carriers},
            recording_pose_enclosures=enclosures, recording_stationary_frames=lambda *args, **kwargs: frozenset())
        geometry = {0: {"frame": "carrier.frame"}}
        tracks = {0: {"translation": [(0., 0., 0.)], "rotation": [(0., 0., 0., 1.)]}}
        rows = {(0, 0): {"max_endpoint_position_error_m": 0,
                         "max_endpoint_unit_quaternion_error": 0}}
        result = _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic,
                                   recording_context=object(), endpoint_rows=rows)
        self.assertEqual(len(reads), 1)
        self.assertGreater(reads[0][-1], 0)
        self.assertEqual(result[0]["position_error"], 0)
        self.assertEqual(result[0]["quaternion_error"], 0)
        self.assertNotIn("_centered_orientation_proof", result[0])
        self.assertIs(arithmetic.work, work)
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.operations, sum(work.counts.values()))

    def test_current_typed_values_radii_and_claims_bind_each_reuse_receipt(self):
        ideal = pose(position=(1, 2, 3))
        prior = compare(ideal, position=(1., 2., 3.))
        work = Work()
        reused = compare(ideal, position=(1., 2., 3.), work=work, previous=prior, completed=(prior,))
        self.assertEqual(reused["position_error"], prior["position_error"])
        self.assertEqual(reused["quaternion_error"], prior["quaternion_error"])
        self.assertEqual(work.counts.get("independent_centered_endpoint_reuse"), 2)
        for changed in ("position", "position_type", "position_radius", "orientation_radius", "claim"):
            selected, position, limits = ideal, (1., 2., 3.), (.001, .001)
            if changed == "position":
                position = (1.0001, 2., 3.)
            elif changed == "position_type":
                position = (1, 2, 3)
            elif changed == "position_radius":
                selected = pose(position=(1, 2, 3), pr=F(1, 1 << 104))
            elif changed == "orientation_radius":
                selected = pose(position=(1, 2, 3), qr=F(1, 1 << 104))
            else:
                limits = (.0001, .0001)
            work = Work()
            actual = compare(selected, position=position, limits=limits, work=work, previous=prior, completed=(prior,))
            fresh = compare(selected, position=position, limits=limits)
            with self.subTest(changed=changed):
                self.assertEqual(actual, fresh)
                self.assertLess(work.counts.get("independent_centered_endpoint_reuse", 0), 2)

    def test_malformed_current_supplied_values_and_center_shapes_are_rejected(self):
        ideal = pose()
        for vector in ((True, 0., 0.), (float("nan"), 0., 0.), (0., 0.)):
            with self.subTest(vector=vector), self.assertRaises(OntoKinError):
                compare(ideal, position=vector)
        for field, replacement in (("position", ((F(0),) * 1000, F(0), F(0))),
                                   ("orientation", (F(1),) * 1000),
                                   ("position_radius", (F(0),) * 1000)):
            ideal = pose()
            object.__setattr__(ideal, field, replacement)
            with self.subTest(field=field), self.assertRaises(OntoKinError):
                compare(ideal)

    def test_every_new_endpoint_callback_preserves_cancellation_and_latches_departures(self):
        def calculate(check=None):
            work = Work(check=check)
            arithmetic = _Bounds(work, cache_intermediates=False)
            ideal = pose((F(1, 8), F(-1, 4), F(1, 2)), pr=F(1, 1 << 104), qr=F(1, 1 << 104))
            def run():
                return _recording_centered_comparison(ideal, (.125, -.25, .5),
                    (0., 0., 0., 1.), (.001, .001), arithmetic)
            return work, arithmetic, ideal, run
        baseline, _, _, run = calculate()
        self.assertIsNotNone(run())
        count = baseline.operations
        self.assertGreater(count, 5)
        for fail_at in range(1, count + 1):
            for change in ("cancel", "cap", "radius", "owner"):
                calls, saved = [0], []
                marker = RuntimeError("cancel centered endpoint")
                def check():
                    calls[0] += 1
                    if calls[0] == fail_at:
                        if change == "cancel":
                            raise marker
                        if change == "cap":
                            work.max_operand_bits = 32767
                        elif change == "radius":
                            saved.append((ideal.orientation_radius, ideal.orientation_radius.numerator))
                            object.__setattr__(ideal.orientation_radius, "_numerator", 0)
                        else:
                            arithmetic.work = Work()
                    elif calls[0] > fail_at:
                        self.fail("a rejected endpoint callback was followed by another callback")
                work, arithmetic, ideal, run = calculate(check)
                try:
                    with self.subTest(fail_at=fail_at, change=change):
                        if change == "cap":
                            self.assertIsNone(run())
                        else:
                            with self.assertRaises(RuntimeError if change == "cancel" else OntoKinError) as caught:
                                run()
                            if change == "cancel":
                                self.assertIs(caught.exception, marker)
                                self.assertIs(work.callback_error, marker)
                        self.assertEqual(calls[0], fail_at)
                finally:
                    for operand, numerator in saved:
                        object.__setattr__(operand, "_numerator", numerator)

    def test_reuse_callback_cannot_mutate_then_restore_a_previous_numeric_result(self):
        ideal = pose(position=(1, 2, 3))
        prior = compare(ideal, position=(1., 2., 3.))
        payload = prior["_centered_position_proof"][0]
        original = payload[4].numerator
        work = Work()
        charge = work.charge
        def changed(kind="checkpoint", amount=1):
            result = charge(kind, amount)
            if kind == "independent_centered_endpoint_reuse":
                object.__setattr__(payload[4], "_numerator", 1)
            return result
        try:
            with patch.object(work, "charge", side_effect=changed), self.assertRaises(OntoKinError):
                compare(ideal, position=(1., 2., 3.), work=work, previous=prior)
        finally:
            object.__setattr__(payload[4], "_numerator", original)


if __name__ == "__main__":
    unittest.main()
