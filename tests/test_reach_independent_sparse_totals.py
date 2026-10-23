"""A complete scalar domain permits exact zero additions to be omitted."""
from contextlib import nullcontext
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_conformance import _Bounds
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def direct_total(arithmetic, values):
    result = F(0)
    for value in values:
        result = arithmetic.add(result, value)
    return result


class IndependentSparseTotalTests(unittest.TestCase):
    def test_ordered_exact_sums_match_with_only_executed_scalar_additions_charged(self):
        sequences = ((0,) * 16, (0, 3, 0, -3, 0, 7, 0),
                     (F(1, 7), 0, F(-2, 13), 0, F(3, 17)),
                     (F(1, 7), F(2, 13), F(3, 17)), (0,), (7,), ())
        for raw in sequences:
            with self.subTest(raw=raw):
                values = tuple(map(F, raw))
                work, previous = Work(), Work()
                actual = _Bounds(work).total(values)
                expected = direct_total(_Bounds(previous), values)
                self.assertEqual(actual, expected)
                self.assertEqual(actual, sum(values, F(0)))
                self.assertLessEqual(work.operations, previous.operations)
                if len(values) > 1 and any(not value for value in values):
                    self.assertLess(work.operations, previous.operations)
                self.assertEqual(work.operations, sum(work.counts.values()))
                self.assertEqual(work.record()['cache_entries'], 0)

    def test_unsupported_shapes_and_small_caps_keep_original_output_and_cost(self):
        class FractionChild(F):
            pass
        cases = [(32768, [F(0), F(2), F(0)]), (32768, (0, 2, 0)),
                 (32768, (0., 2., 0.)), (32768, (F(0), FractionChild(2), F(0))),
                 (32768, (F(0), F(1 << 257), F(0))), (32768, (F(0),) * 17),
                 (32767, (F(0), F(2), F(0))), (64, (F(0), F(2), F(0)))]
        for cap, values in cases:
            with self.subTest(cap=cap, values=values):
                work, previous = Work(max_operand_bits=cap), Work(max_operand_bits=cap)
                self.assertEqual(_Bounds(work).total(values), direct_total(_Bounds(previous), values))
                self.assertEqual(work.operations, previous.operations)
        work, previous = Work(), Work()
        self.assertEqual(_Bounds(work).total(F(x) for x in (0, 2, 0)),
                         direct_total(_Bounds(previous), (F(x) for x in (0, 2, 0))))
        self.assertEqual(work.operations, previous.operations)

    def test_original_prospective_width_failures_remain_identical_in_narrow_domains(self):
        for cap, values in ((1, (F(0), F(0))), (64, (F(0), F(1, 1 << 63))),
                            (128, (F(0), F((1 << 127) - 1), F(0)))):
            outcomes = []
            for optimized in (False, True):
                work = Work(max_operand_bits=cap)
                with self.subTest(cap=cap, optimized=optimized), self.assertRaises(ReachAdmissionError) as caught:
                    (_Bounds(work).total(values) if optimized else direct_total(_Bounds(work), values))
                outcomes.append((caught.exception.reach_code, caught.exception.details, work.operations))
            self.assertEqual(outcomes[0], outcomes[1])

    def test_live_narrowing_at_each_callback_uses_current_original_arithmetic(self):
        values = tuple(map(F, (0, 3, 0, 4, 0, 5)))
        count = Work()
        _Bounds(count).total(values)
        for fail_at in range(1, count.operations + 1):
            work, calls = Work(), 0
            def narrow():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    work.max_operand_bits = 32767
            work.external_check = narrow
            self.assertEqual(_Bounds(work).total(values), direct_total(_Bounds(Work(max_operand_bits=32767)), values))
            self.assertEqual(work.max_operand_bits, 32767)
            self.assertEqual(work.record()['cache_entries'], 0)

    def test_first_domain_callback_cannot_hide_a_width_failure_by_restoring_the_cap(self):
        work, calls = Work(), 0
        def change():
            nonlocal calls
            calls += 1
            work.max_operand_bits = 1 if calls == 1 else 32768
        work.external_check = change
        with self.assertRaises(ReachAdmissionError) as caught:
            _Bounds(work).total((F(0), F(0), F(0)))
        self.assertEqual(caught.exception.details['budget'], 'numeric_operand_bits')
        self.assertEqual(calls, 1)
        self.assertEqual(work.max_operand_bits, 1)

    def test_cancellation_keeps_its_identity_and_no_result_cache(self):
        values = tuple(map(F, (0, 3, 0, 4, 0, 5)))
        count = Work()
        _Bounds(count).total(values)
        for fail_at in range(1, count.operations + 1):
            for marker in (RuntimeError("cancel sparse independent total"),
                           ReachAdmissionError("reach_resource", "caller refusal")):
                work, calls = Work(), 0
                def cancel():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        raise marker
                work.external_check = cancel
                with self.assertRaises(type(marker)) as caught:
                    _Bounds(work).total(values)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(work.record()['cache_entries'], 0)

    def test_actual_glb_bytes_and_independent_verification_match_with_less_work(self):
        for case in ("P01", "P18"):
            outcomes = []
            for optimized in (False, True):
                compiler = compile_construction(source_case(case))
                context = nullcontext() if optimized else patch.object(_Bounds, "total", new=direct_total)
                with context:
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                outcomes.append((result.data, result.report["validation"], compiler.budget.operations))
            self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            self.assertLess(outcomes[1][2], outcomes[0][2])


if __name__ == '__main__':
    unittest.main()
