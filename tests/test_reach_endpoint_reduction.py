"""Every supplied endpoint contributes to conservative component reductions."""
import copy
from fractions import Fraction as F
import math
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from ontokin import reach_export
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def endpoints(count=25):
    return [NS(translations=[(i * .1, (count - i) * -.13, (i % 3) * .17)
                             for i in range(count)],
               rotations_xyzw=[(.6 if i % 2 else .8, 0.0, 0.0, .8 if i % 2 else .6)
                               for i in range(count)])]


class ReachEndpointReductionTests(unittest.TestCase):
    def test_all_actual_endpoint_errors_are_covered_with_less_exact_work(self):
        nodes = endpoints()
        before = copy.deepcopy(nodes)
        reduced, ordinary = ReachExecutionWork(), ReachExecutionWork()
        actual = reach_export._endpoint_group_maxima(nodes, range(25), None, work=reduced)
        expected = reach_export._endpoint_group_maxima_exact(nodes, range(25), None, work=ordinary)
        for bound, minimum in zip(actual[0], expected[0]):
            self.assertGreaterEqual(bound, minimum)
        self.assertLess(reduced.operations * 2, ordinary.operations)
        self.assertEqual(nodes[0].__dict__, before[0].__dict__)
        self.assertEqual(reduced.counts['recording_endpoint_group_domain'], 25)
        self.assertEqual(reduced.operations, sum(reduced.counts.values()))
        self.assertFalse(reduced._cache)

    def test_maxima_at_different_keys_remain_conservative_for_each_coordinate(self):
        nodes = [NS(translations=[(1.1, 0.0, 0.0), (0.0, -2.2, 0.0), (0.0, 0.0, 3.3)],
                    rotations_xyzw=[(.6, 0.0, 0.0, .8), (0.0, .6, 0.0, .8),
                                    (0.0, 0.0, .6, .8)])]
        result = reach_export._endpoint_group_maxima(nodes, (0, 1, 2), None, work=ReachExecutionWork())[0]
        errors, magnitudes, quaternion_errors = [], [], []
        for node in nodes:
            for position, quaternion in zip(node.translations, node.rotations_xyzw):
                stored_p = reach_export._stored_vector(position, None)
                stored_q = reach_export._stored_vector(quaternion, None)
                errors.append(tuple(abs(F(a) - F(b)) for a, b in zip(position, stored_p)))
                magnitudes.append(tuple(abs(F(value)) for value in stored_p))
                quaternion_errors.append(tuple(abs(F(a) - F(b)) for a, b in zip(quaternion, stored_q)))
        self.assertEqual(result[0], sum(max(values) for values in zip(*errors)))
        self.assertEqual(result[1], 4 * sum(max(values) for values in zip(*quaternion_errors))
                         + 2 * reach_export.NORMALIZATION_ERROR)
        self.assertEqual(result[2], sum(max(values) for values in zip(*magnitudes)))

    def test_subnormal_signed_zero_and_large_finite_positions_have_exact_residuals(self):
        nodes = endpoints(3)
        nodes[0].translations = [(math.ulp(0.0), -0.0, -math.ulp(0.0)),
                                 (3e38, -3e38, 1e-320), (0.0, 1e-40, -1e-40)]
        actual = reach_export._endpoint_group_maxima(nodes, range(3), None, work=ReachExecutionWork())
        expected = reach_export._endpoint_group_maxima_exact(nodes, range(3), None, work=ReachExecutionWork())
        self.assertTrue(all(a >= b for a, b in zip(actual[0], expected[0])))
        self.assertEqual(math.copysign(1, nodes[0].translations[0][1]), -1)

    def test_small_norm_quaternion_replays_the_complete_original_group(self):
        nodes = endpoints(3)
        nodes[0].rotations_xyzw[1] = (.125, .125, .125, .125)
        work = ReachExecutionWork()
        actual = reach_export._endpoint_group_maxima(nodes, range(3), None, work=work)
        expected = reach_export._endpoint_group_maxima_exact(nodes, range(3), None, work=ReachExecutionWork())
        self.assertEqual(actual, expected)
        self.assertEqual(work.counts['recording_endpoint_group_domain'], 2)
        self.assertEqual(work.counts['recording_endpoint_domain'], 3)

    def test_narrow_domain_keeps_original_admission_and_results(self):
        nodes = endpoints(3)
        for cap in (128, 1075, 2048):
            outcomes = []
            for operation in (reach_export._endpoint_group_maxima_exact, reach_export._endpoint_group_maxima):
                work = ReachExecutionWork(max_operand_bits=cap)
                try:
                    result = operation(nodes, range(3), None, work=work)
                    outcomes.append(('value', result, work.counts))
                except ReachAdmissionError as error:
                    outcomes.append(('error', error.reach_code, error.details, work.counts))
            self.assertEqual(*outcomes)

    def test_changed_domain_during_scan_or_final_sum_replays_current_inputs(self):
        for event in ('recording_endpoint_group_domain', 'recording_endpoint_sum_domain'):
            nodes, work = endpoints(3), ReachExecutionWork()
            original = work.charge
            changed = []
            def narrow(kind='checkpoint', amount=1):
                if kind == event and not changed:
                    changed.append(True)
                    work.external_check = lambda: setattr(work, 'max_operand_bits', 2048)
                return original(kind, amount)
            with patch.object(work, 'charge', side_effect=narrow):
                actual = reach_export._endpoint_group_maxima(nodes, range(3), None, work=work)
            expected = reach_export._endpoint_group_maxima_exact(nodes, range(3), None,
                work=ReachExecutionWork(max_operand_bits=2048))
            self.assertTrue(changed)
            self.assertEqual(actual, expected)
            self.assertEqual(work.counts['recording_endpoint_domain'], 3)

    def test_callback_failure_identity_and_existing_cache_are_preserved(self):
        for event in ('recording_endpoint_group_domain', 'recording_endpoint_sum_domain'):
            for marker in (RuntimeError('cancel reduction'), reach_export._EndpointReductionFallback()):
                nodes, work = endpoints(3), ReachExecutionWork(max_cache_entries=1)
                work.remember(('unrelated',), F(7))
                previous = tuple(work._cache.items())
                original = work.charge
                def cancel(kind='checkpoint', amount=1):
                    if kind == event:
                        work.external_check = lambda: (_ for _ in ()).throw(marker)
                    return original(kind, amount)
                with patch.object(work, 'charge', side_effect=cancel):
                    with self.assertRaises(type(marker)) as caught:
                        reach_export._endpoint_group_maxima(nodes, range(3), None, work=work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(tuple(work._cache.items()), previous)

    def test_every_occurrence_is_freshly_admitted_after_a_prior_group(self):
        nodes, work = endpoints(3), ReachExecutionWork()
        reach_export._endpoint_group_maxima(nodes, range(3), None, work=work)
        for field, bad in (('translations', (math.inf, 0.0, 0.0)),
                           ('rotations_xyzw', (0.0, 0.0, 0.0, True))):
            changed = copy.deepcopy(nodes)
            getattr(changed[0], field)[2] = bad
            with self.assertRaisesRegex(ValueError, 'finite binary64 pose components'):
                reach_export._endpoint_group_maxima(changed, range(3), None, work=work)
        changed = copy.deepcopy(nodes)
        changed[0].translations[2] = (1000.1, 0.0, 0.0)
        original = reach_export._endpoint_group_maxima(nodes, range(3), None, work=work)
        current = reach_export._endpoint_group_maxima(changed, range(3), None, work=work)
        self.assertGreater(current[0][2], original[0][2])

    def test_empty_group_keeps_zero_maxima(self):
        nodes = endpoints(1)
        self.assertEqual(reach_export._endpoint_group_maxima(nodes, (), None, work=ReachExecutionWork()),
                         ((F(0), F(0), F(0)),))

    def test_actual_pose_bytes_clocks_and_geometry_are_unchanged_and_independently_accepted(self):
        for case, end in (('P01', F(3)), ('L01', F(3, 4)), ('P16', F(1, 4))):
            outputs, operations = [], []
            original = reach_export._endpoint_group_axes
            for reduced in (False, True):
                compiler = compile_construction(source_case(case))
                with patch.object(reach_export, '_endpoint_group_axes',
                                  original if reduced else lambda *a, **k: None):
                    result = export_glb(compiler.model, options=ExportOptions(end=end, fps=1, helpers=False),
                        target_contract='ontokin.glb/0.6', work=compiler.reach_work)
                self.assertEqual(result.report['validation']['status'], 'passed')
                self.assertLessEqual(compiler.budget.operations, 100000)
                outputs.append(read_glb(result.data))
                operations.append(compiler.budget.operations)
            self.assertEqual(outputs[0].binary, outputs[1].binary)
            for field in ('nodes', 'meshes', 'materials', 'bufferViews', 'accessors', 'animations'):
                self.assertEqual(outputs[0].document[field], outputs[1].document[field])
            self.assertLess(operations[1], operations[0])


if __name__ == '__main__':
    unittest.main()
