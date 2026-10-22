"""Certificates bound the reported destination operands in one complete pass."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_export as export
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork


def quantities(work):
    bound = export.MotionBound(F(2, 3), F(1, 7), F(1, 3))
    return export._certificate_quantities(None, bound, bound, F(1, 3),
        F(1, 10**9), F(1, 2**60), F(1, 2**60), F(1, 1000),
        F(1, 10**10), F(1, 2**30), F(1, 2**30), F(7, 3), work=work)


class ReachCertificateSinglePassTests(unittest.TestCase):
    def test_destination_uses_exposed_primitives_once_and_bounds_their_error(self):
        work = ReachExecutionWork()
        with patch.object(export, "destination_numeric_bounds",
                          wraps=export.destination_numeric_bounds) as checked:
            rows = quantities(work)
        result = dict(rows)
        self.assertEqual(checked.call_count, 1)
        arc, magnitude, radius, vertex = checked.call_args.args
        self.assertEqual(arc, F(result["stored_quaternion_arc_upper_rad"]))
        self.assertEqual(radius, F(result["landmark_radius_m"]))
        self.assertEqual(vertex, F(result["local_vertex_error_bound_m"]))
        self.assertGreaterEqual(radius, F(1, 3))
        self.assertGreaterEqual(vertex, F(1, 10**9))
        self.assertGreaterEqual(F(result["destination_numeric_position_bound_m"]),
                                (magnitude + radius + vertex + 1) / 2**38)
        self.assertGreaterEqual(F(result["destination_numeric_rotation_bound_rad"]),
                                arc * arc + F(1, 2**44))
        names = [name for name, value in rows]
        self.assertEqual(names.index("destination_numeric_position_bound_m"),
                         names.index("source_numeric_rotation_bound_rad") + 1)
        self.assertEqual(names.index("destination_numeric_rotation_bound_rad"),
                         names.index("destination_numeric_position_bound_m") + 1)
        self.assertEqual(sum(work.counts.values()), work.operations)

    def test_cancellation_preserves_original_exception_at_each_actual_checkpoint(self):
        measured = ReachExecutionWork()
        quantities(measured)
        for stop in range(1, measured.operations + 1):
            marker = RuntimeError("cancel certificate")
            calls = 0
            def cancel():
                nonlocal calls
                calls += 1
                if calls == stop:
                    raise marker
            with self.subTest(stop=stop):
                with self.assertRaises(RuntimeError) as caught:
                    quantities(ReachExecutionWork(check=cancel))
                self.assertIs(caught.exception, marker)

    def test_lowered_and_callback_narrowed_caps_still_reject_actual_arithmetic(self):
        for during in (False, True):
            work = ReachExecutionWork(max_operand_bits=32768 if during else 32)
            if during:
                def narrow():
                    if work.counts.get("destination_bound"):
                        work.max_operand_bits = 32
                work.external_check = narrow
            with self.subTest(during=during):
                with self.assertRaises(ReachAdmissionError) as caught:
                    quantities(work)
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")


if __name__ == "__main__":
    unittest.main()
