"""Complete exact identity poses preserve independent interval equations."""
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_reference import (
    Interval, MAX_CACHE, PoseEnclosure, ReferenceError, _Arithmetic,
    _PoseArithmetic, build_reference,
)
from reach_agent_support import source_case


Z = Interval(F(0), F(0))
U = Interval(F(1), F(1))
IDENTITY = PoseEnclosure((Z, Z, Z), (U, Z, Z, Z), (Z, Z, Z), (Z, Z, Z))


def point(value):
    value = F(value)
    return Interval(value, value)


def original_compose(pose, parent, local):
    """Retain the pre-elision equations as a separate exact comparison path."""
    key = pose._key("compose", parent, local)
    cached = pose.a.lookup(key)
    if cached is not None:
        return cached
    offset = pose.rotate(parent.orientation, local.position)
    position = pose.add(parent.position, offset)
    orientation = pose.multiply(parent.orientation, local.orientation)
    rates = (parent.velocity, parent.omega, local.velocity, local.omega)
    if all(len(vector) == 3 and pose._zero(vector) for vector in rates):
        return pose.a.remember(key, PoseEnclosure(position, orientation, parent.velocity, parent.omega))
    return pose.a.remember(key, PoseEnclosure(position, orientation,
        pose.add(pose.add(parent.velocity, pose.cross(parent.omega, offset)),
                 pose.rotate(parent.orientation, local.velocity)),
        pose.add(parent.omega, pose.rotate(parent.orientation, local.omega))))


def arithmetic(cap=32768):
    return _PoseArithmetic(_Arithmetic(work=ReachExecutionWork(max_operand_bits=cap), bits=8))


class ReachReferenceIdentityTests(unittest.TestCase):
    def test_both_orders_preserve_all_enclosure_endpoints_and_spatial_derivatives(self):
        fixtures = (
            IDENTITY,
            PoseEnclosure((point(F(1, 3)), Interval(F(-2, 7), F(5, 11)), Z),
                (Interval(F(1, 3), F(2, 3)), point(F(1, 7)), Z, Interval(F(-1, 2), F(1, 4))),
                (point(3), Interval(F(-5, 3), F(7, 4)), Z),
                (point(-2), Z, Interval(F(-3, 5), F(4, 5)))),
            # Nonunit quaternion intervals also retain the exact original
            # algebra; only the other pose needs to be the complete identity.
            PoseEnclosure((point(1), point(-2), point(F(1, 1 << 80))),
                (point(-2), point(3), point(-4), point(5)),
                (Z, Z, Z), (Z, Z, Z)),
        )
        for other in fixtures:
            for parent, local in ((IDENTITY, other), (other, IDENTITY)):
                with self.subTest(other=other, identity_first=parent is IDENTITY):
                    actual_ops, expected_ops = arithmetic(), arithmetic()
                    actual = actual_ops.compose(parent, local)
                    expected = original_compose(expected_ops, parent, local)
                    self.assertEqual(actual, expected)
                    self.assertIs(actual, other)
                    self.assertEqual(actual_ops.a.cache, {})
                    self.assertLess(actual_ops.a.work.operations, expected_ops.a.work.operations)

    def test_near_identity_negative_unit_and_nonzero_rates_keep_original_equations(self):
        moving = PoseEnclosure((point(F(1, 3)), point(2), point(-3)),
            (point(F(1, 2)), point(F(1, 2)), point(F(1, 2)), point(F(1, 2))),
            (point(1), point(-2), Z), (point(2), Z, point(-1)))
        near = (
            replace(IDENTITY, position=(Z, Z, point(F(1, 1 << 80)))),
            replace(IDENTITY, velocity=(Z, Z, point(F(1, 1 << 80)))),
            replace(IDENTITY, omega=(Z, Z, point(F(1, 1 << 80)))),
            replace(IDENTITY, orientation=(point(-1), Z, Z, Z)),
            replace(IDENTITY, position=(Z, Z, Interval(F(-1, 1 << 80), F(1, 1 << 80)))),
        )
        for almost in near:
            for parent, local in ((almost, moving), (moving, almost)):
                with self.subTest(almost=almost, first=parent is almost):
                    actual = arithmetic().compose(parent, local)
                    expected = original_compose(arithmetic(), parent, local)
                    self.assertEqual(actual, expected)
                    self.assertIsNot(actual, moving)

    def test_other_shapes_retain_original_coercion_and_failure_behavior(self):
        malformed = (
            replace(IDENTITY, position=(Z, Z)),
            replace(IDENTITY, orientation=(U, Z, Z)),
            replace(IDENTITY, velocity=(Interval(False, False), Z, Z)),
        )
        for candidate in malformed:
            for parent, local in ((IDENTITY, candidate), (candidate, IDENTITY)):
                outcomes = []
                for fast in (False, True):
                    ops = arithmetic()
                    try:
                        value = ops.compose(parent, local) if fast else original_compose(ops, parent, local)
                    except Exception as error:
                        outcomes.append((type(error), str(error)))
                    else:
                        outcomes.append(value)
                self.assertEqual(outcomes[0], outcomes[1])

    def test_narrow_caps_admit_all_four_fields_before_reuse(self):
        ordinary = replace(IDENTITY, position=(point(F(1, 3)), point(-7), Z),
                           velocity=(point(5), Z, Z))
        for cap in (9, 32, 64, 128, 32768):
            for parent, local in ((IDENTITY, ordinary), (ordinary, IDENTITY)):
                self.assertEqual(arithmetic(cap).compose(parent, local),
                                 original_compose(arithmetic(cap), parent, local))
        for field in ("position", "orientation", "velocity", "omega"):
            values = list(getattr(ordinary, field))
            values[0] = point(1 << 80)
            invalid = replace(ordinary, **{field: tuple(values)})
            for parent, local in ((IDENTITY, invalid), (invalid, IDENTITY)):
                for fast in (False, True):
                    ops = arithmetic(64)
                    with self.subTest(field=field, fast=fast), self.assertRaises(ReferenceError) as caught:
                        ops.compose(parent, local) if fast else original_compose(ops, parent, local)
                    self.assertEqual(caught.exception.code, "resource")

    def test_cancellation_and_lookup_callback_narrowing_cannot_publish_a_reused_pose(self):
        ops = arithmetic()
        marker = RuntimeError("cancel independent identity composition")
        with patch.object(ops.a.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                ops.compose(IDENTITY, IDENTITY)
        self.assertIs(caught.exception, marker)
        self.assertIs(ops.a.work.callback_error, marker)
        self.assertEqual(ops.a.cache, {})
        ops = arithmetic()
        wide = replace(IDENTITY, omega=(point(1 << 80), Z, Z))
        def narrow():
            ops.a.work.max_operand_bits = 64
        with patch.object(ops.a.work, "external_check", side_effect=narrow):
            with self.assertRaises(ReferenceError) as caught:
                ops.compose(IDENTITY, wide)
        self.assertEqual(caught.exception.code, "resource")
        self.assertEqual(ops.a.cache, {})

    def test_repeated_identity_edges_need_no_additional_numerical_cache(self):
        ops = arithmetic()
        moving = replace(IDENTITY, position=(point(F(1, 3)), point(F(2, 7)), point(3)),
                         omega=(Z, Z, point(2)))
        for _ in range(300):
            self.assertIs(ops.compose(IDENTITY, moving), moving)
            self.assertIs(ops.compose(moving, IDENTITY), moving)
        self.assertEqual(ops.a.cache, {})
        self.assertLessEqual(len(ops.a.cache), MAX_CACHE)
        self.assertEqual(ops.a.work.operations, 600)
        self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))

    def test_actual_independent_recording_poses_and_histories_keep_identical_enclosures(self):
        for case, end, times in (("P01", F(3, 4), (F(1, 4), F(3, 4))),
                                 ("P16", F(1, 4), (F(1, 8), F(1, 4))),
                                 ("L02", F(3, 4), (F(1, 4), F(3, 4)))):
            results = []
            for fast in (False, True):
                compiled = compile_construction(source_case(case))
                if fast:
                    reference = build_reference(compiled.model, end=end, work=compiled.reach_work)
                    paths = tuple(path + ".frame" for path in compiled.model.objects)
                    values = [reference.recording_pose_enclosures(paths, time) for time in times]
                    histories = reference.boundary_states()
                else:
                    with patch.object(_PoseArithmetic, "compose", original_compose):
                        reference = build_reference(compiled.model, end=end, work=compiled.reach_work)
                        paths = tuple(path + ".frame" for path in compiled.model.objects)
                        values = [reference.recording_pose_enclosures(paths, time) for time in times]
                        histories = reference.boundary_states()
                self.assertLessEqual(compiled.budget.operations, 100000)
                results.append((values, histories))
            with self.subTest(case=case):
                self.assertEqual(results[0], results[1])


if __name__ == "__main__":
    unittest.main()
