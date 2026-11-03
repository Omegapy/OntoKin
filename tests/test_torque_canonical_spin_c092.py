"""C092 regressions against independently frozen source and arithmetic inputs.

The published inputs were derived before candidate implementation. Runtime
observations here never replace those expectations or the original C090 set.
"""
import copy
from dataclasses import replace
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import _simulator, evaluate_prefix
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, round_dyadic
from ontokin.reach_pose import (ARGUMENT_ERROR, AXIS_ERROR, METHOD, PRODUCT_ERROR,
                               ReachPoseOps, RotationValue, UNIT)
from ontokin.texture_bundle import load_texture_file_manifest


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / 'docs/language-design/torque-amendments/c092-canonical-spin-selection/inputs'
ORIGINAL = ROOT / 'docs/language-design/torque-v0.1/freeze'
EXPECTED_SHA256 = '7d21f989106c4ad2406b2850b1a9d1d4430f2068584c52ebfd1c17fb64d56271'
EXPECTED_RAW = (INPUTS / 'EXPECTED-SELECTOR-RESULTS.json').read_bytes()
assert hashlib.sha256(EXPECTED_RAW).hexdigest() == EXPECTED_SHA256
EXPECTED = json.loads(EXPECTED_RAW)
LITERALS = json.loads((INPUTS / 'LITERAL-SOURCES.json').read_bytes())
SOURCE_ROWS = {row['path']: row for row in LITERALS['sources']}
GRID = 1 << 96


def fraction(value):
    return F(int(value['numerator']), int(value['denominator']))


def grid(components):
    result = tuple(x * GRID for x in components)
    assert all(x.denominator == 1 for x in result)
    return [str(x.numerator) for x in result]


def literal(name):
    row = SOURCE_ROWS[name]
    raw = (INPUTS / name).read_bytes()
    assert len(raw) == row['bytes']
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    bundle = load_texture_file_manifest(ROOT / row['dependencies_from'])
    return replace(bundle, entry=replace(bundle.entry, raw=raw))


def original(name, *, append=''):
    bundle = load_texture_file_manifest(ORIGINAL / (name + '.files.json'))
    if append:
        head, tail = bundle.entry.text.rsplit('}', 1)
        bundle = replace(bundle, entry=replace(bundle.entry, raw=(head + append + '}' + tail).encode()))
    return bundle


def compile_bundle(bundle, *, check=None, profile='torque-0.1'):
    ledger = SharedExecutionBudget(check=check)
    admit_entry_budget(bundle.entry, ledger, profile=profile)
    compiler = compile_construction(bundle, execution_budget=ledger)
    return compiler, ledger


def simulator(bundle, *, check=None):
    compiler, ledger = compile_bundle(bundle, check=check)
    return _simulator(compiler.model, work=compiler.reach_work), ledger


class C092FrozenPointTests(unittest.TestCase):
    def test_all_thirty_signed_stage_transition_neighbours(self):
        self.assertEqual(len(EXPECTED['stage_boundaries']), 30)
        for row in EXPECTED['stage_boundaries']:
            with self.subTest(case=row['id']):
                work = ReachExecutionWork()
                ops = ReachPoseOps(work)
                omega = tuple(map(fraction, row['omega']))
                elapsed = fraction(row['elapsed'])
                if row['outcome'] != 'selected':
                    with self.assertRaises(ReachAdmissionError) as caught:
                        ops.spin_rotation(omega, elapsed)
                    self.assertEqual(caught.exception.reach_code, 'reach_numeric')
                    self.assertIn('Finite source spin phase reduction', str(caught.exception))
                else:
                    plan = ops.spin_plan(omega, abs(elapsed))
                    self.assertEqual(plan.precision_bits, row['selected_precision'])
                    self.assertEqual(plan.argument_error_rad, fraction(row['tried'][-1]['argument_error']))
                    self.assertLessEqual(plan.argument_error_rad, ARGUMENT_ERROR)
                    q = ops.spin_rotation(omega, elapsed)
                    self.assertEqual(grid(q.components), row['quaternion_grid_integers'])
                    self.assertEqual(q.error_rad, AXIS_ERROR + PRODUCT_ERROR)
                self.assertLessEqual(work.operations, 100000)
                self.assertEqual(work.operations, sum(work.counts.values()))
                self.assertLessEqual(len(work._cache), 256)

    def test_six_signed_rounding_ties_keep_even_grid_integer(self):
        for row in EXPECTED['rounding_ties']:
            with self.subTest(input=row['input']):
                work = ReachExecutionWork()
                value = round_dyadic(fraction(row['input']), 96, work=work)
                self.assertEqual(str((value * GRID).numerator), row['expected_grid_integer'])

    def test_selected_reduction_failure_is_terminal_and_not_another_stage(self):
        ops = ReachPoseOps(ReachExecutionWork())
        control = EXPECTED['selected_reduction_failure_control']
        self.assertIsNone(ops._reduced_sincos(fraction(control['lower']),
            fraction(control['upper']), ops._pi(control['precision'])))
        # The malformed enclosure above is a primitive control, not a source
        # domain witness. Inject the same selected-reduction disposition to
        # check that the caller never searches another candidate stage.
        with patch.object(ops, '_reduced_sincos', return_value=None) as reduction:
            with patch.object(ops, 'spin_plan', wraps=ops.spin_plan) as selection:
                with self.assertRaises(ReachAdmissionError) as caught:
                    ops.spin_rotation((F(1), F(0), F(0)), F(1))
        self.assertEqual(caught.exception.reach_code, 'reach_numeric')
        self.assertIn('proved spin phase did not enclose', str(caught.exception))
        self.assertEqual(selection.call_count, 1)
        self.assertEqual(reduction.call_count, 1)

    def test_callback_exception_identity_and_consumed_work_survive_selector(self):
        owner = {}
        sentinel = RuntimeError('C092 original selector callback')
        def check():
            work = owner.get('work')
            if work is not None and work.counts.get('phase_quadrant_ceiling', 0):
                owner['consumed'] = work.operations
                raise sentinel
        work = ReachExecutionWork(check=check)
        owner['work'] = work
        with self.assertRaises(RuntimeError) as caught:
            ReachPoseOps(work).spin_plan((F(1), F(0), F(0)), F(16384))
        self.assertIs(caught.exception, sentinel)
        self.assertIs(work.callback_error, sentinel)
        self.assertEqual(work.operations, owner['consumed'])

    def test_finite_selector_does_not_replace_operation_or_operand_refusal(self):
        for kwargs, budget in (({'max_operations': 1}, 'max_operations'),
                               ({'max_operand_bits': 32}, 'numeric_operand_bits')):
            with self.subTest(budget=budget):
                work = ReachExecutionWork(**kwargs)
                with self.assertRaises(ReachAdmissionError) as caught:
                    ReachPoseOps(work).spin_plan((F(1), F(0), F(0)), F(16384))
                self.assertEqual(caught.exception.reach_code, 'reach_resource')
                self.assertEqual(caught.exception.details['budget'], budget)


class C092SourceHistoryTests(unittest.TestCase):
    def assert_admitted(self, result, axis='world_x', omega=None):
        self.assertIsNone(result['failure'])
        self.assertEqual(result['valid_until_side'], 'after')
        ball = result['last_valid_state']['objects']['ball']
        self.assertEqual(ball['torques']['axis'], axis)
        if omega is not None:
            self.assertEqual([float(x).hex() for x in ball['angular_velocity_rad_per_s']], omega)
        return ball

    def test_public_same_source_history_order_and_repetition(self):
        expected = EXPECTED['witness_under_proposed_rule']
        common = None
        for history in ((1,), (16384, 1), (1, 16384, 1), (1, 1, 1)):
            with self.subTest(history=history):
                compiler, ledger = compile_bundle(literal('same_source_history.ok'))
                last_count = ledger.operations
                for clock in history:
                    result = evaluate_prefix(compiler.model, str(clock), work=compiler.reach_work)
                    self.assertIsNone(result['failure'])
                    self.assertGreater(ledger.operations, last_count)
                    last_count = ledger.operations
                    if clock == 1:
                        ball = self.assert_admitted(result, omega=expected['released_omega_binary64_hex'])
                        self.assertEqual(ball['torques']['started_count'], 1)
                        if common is None:
                            common = result['last_valid_state']
                        self.assertEqual(result['last_valid_state'], common)
                self.assertEqual(dict(ledger.limits), {'max_operations': 100000, 'max_elapsed_ms': 30000})
                self.assertLessEqual(ledger.operations, 100000)
                self.assertLessEqual(len(compiler.reach_work._cache), 256)

    def test_same_point_with_frozen_helper_and_no_helper_sources(self):
        expected = EXPECTED['witness_under_proposed_rule']
        for name in ('same_source_history.ok', 'helper_force.ok', 'no_helper.ok'):
            with self.subTest(source=name):
                compiler, _ = compile_bundle(literal(name))
                clock = '1' if name == 'same_source_history.ok' else '16385'
                self.assert_admitted(evaluate_prefix(compiler.model, clock, work=compiler.reach_work),
                                     omega=expected['released_omega_binary64_hex'])

    def test_segmented_simulator_preserves_complete_direct_state(self):
        direct, _ = simulator(literal('same_source_history.ok'))
        expected = direct.advance(F(1), 'after')
        segmented, _ = simulator(literal('same_source_history.ok'))
        for clock, side in ((F(0), 'after'), (F(1, 4), 'after'),
                            (F(1, 2), 'after'), (F(1), 'before'), (F(1), 'after')):
            observed = segmented.advance(clock, side)
        self.assertEqual(observed, expected)

    def test_dynamic_zero_force_keeps_original_rotation_and_separate_error_time(self):
        sim, _ = simulator(literal('unchanged-force-origin.ok'))
        sim.advance(F(0))
        anchor = sim.state.dynamic['ball']
        initial_rotation = (anchor.state.rotation if hasattr(anchor.state, 'rotation')
                            else anchor.state.orientation)
        for clock in (F(1, 2), F(3, 4), F(1)):
            sim.advance(clock)
            self.assertEqual(sim.state.dynamic['ball'].time, F(0))
            current = sim.state.dynamic['ball'].state
            self.assertEqual(current.rotation if hasattr(current, 'rotation') else current.orientation,
                             initial_rotation)
        objects, _ = sim._resolve_kinematics(F(1), sim.state)
        case = EXPECTED['unchanged_force_source_origin']
        self.assertEqual(grid(objects['ball'].rotation.components), case['expected_quaternion_grid_integers'])
        self.assertNotEqual(grid(objects['ball'].rotation.components), case['incorrect_half_plus_half_quaternion_grid_integers'])
        self.assertEqual(sim.state.dynamic_error_times['ball'], F(3, 4))

    def test_paused_prescribed_spin_uses_accumulated_running_elapsed(self):
        sim, _ = simulator(literal('paused-resumed-origin.ok'))
        sim.advance(F(0))
        origin = sim.state.actions['turn'].initial
        sim.advance(F(1, 4))
        self.assertEqual(sim.state.actions['turn'].elapsed_at(F(1, 2)), F(1, 4))
        sim.advance(F(3, 4))
        before = sim.advance(F(3, 2), 'before')
        self.assertEqual(sim.state.actions['turn'].elapsed_at(F(3, 2)), F(1))
        self.assertEqual(sim.state.actions['turn'].initial, origin)
        self.assertEqual(before['objects']['ball']['angular_velocity_rad_per_s'], [0.0, 0.0, 0.0])
        after = sim.advance(F(3, 2), 'after')['objects']['ball']
        self.assertEqual(after['torques']['axis'], 'world_x')
        self.assertEqual(after['torques']['started_count'], 1)

    def test_evolved_nonidentity_parent_uses_frozen_exact_quaternions(self):
        sim, _ = simulator(literal('evolved-permutation.ok'))
        sim.advance(F(1), 'before')
        objects, _ = sim._resolve_kinematics(F(1), sim.state)
        case = EXPECTED['source_permutations_and_parallel_impulse']['evolved-permutation.ok']
        self.assertEqual(grid(objects['carrier'].rotation.components), case['parent_quaternion_grid_integers'])
        self.assertEqual(grid(objects['ball'].rotation.components), case['pre_release_quaternion_grid_integers'])
        after = sim.advance(F(1), 'after')['objects']['ball']
        self.assertEqual([float(x).hex() for x in after['angular_velocity_rad_per_s']], case['released_omega_binary64_hex'])
        self.assertEqual(after['torques']['axis'], case['axis'])

    def test_frozen_nonzero_parallel_impulse_has_exact_zero_cross(self):
        compiler, _ = compile_bundle(literal('nonzero-parallel-impulse.ok'))
        case = EXPECTED['source_permutations_and_parallel_impulse']['nonzero-parallel-impulse.ok']
        ball = self.assert_admitted(evaluate_prefix(compiler.model, case['clock'], work=compiler.reach_work),
                                   axis=case['axis'], omega=case['released_omega_binary64_hex'])
        self.assertEqual(ball['impulses']['applied_count'], case['applied_count'])
        self.assertNotEqual(ball['velocity_m_per_s'], [0.0, 0.0, 0.0])

    def test_both_true_signed_two_to_minus96_residuals_refuse_before_latch(self):
        for name, expected_y in (('off-axis-positive.ok', '0x1.0000000000000p-96'),
                                  ('off-axis-negative.ok', '-0x1.0000000000000p-96')):
            with self.subTest(source=name):
                compiler, _ = compile_bundle(literal(name))
                result = evaluate_prefix(compiler.model, '0', work=compiler.reach_work)
                self.assertEqual(result['failure'].diagnostic.code, 'OKL-E-FRAME')
                self.assertEqual(result['failure'].diagnostic.details['torque_reason'], 'incoming_axis')
                self.assertEqual(result['valid_until_side'], 'before')
                ball = result['last_valid_state']['objects']['ball']
                self.assertEqual(float(ball['angular_velocity_rad_per_s'][1]).hex(), expected_y)
                self.assertIsNone(ball['torques']['axis'])
                self.assertEqual(ball['torques']['started_count'], 0)

    def test_stationary_override_preserves_entire_materialized_anchor(self):
        sim, _ = simulator(literal('unchanged-force-origin.ok'))
        initial = RotationValue(UNIT, F(1, 1 << 72), (1.0, 0.0, 0.0, 0.0))
        for omega, elapsed in (((0.6, 0.8, 0.0), F(0)), ((0.0, 0.0, 0.0), F(16384))):
            with self.subTest(omega=omega, elapsed=elapsed):
                self.assertIs(sim._advance_orientation(initial, omega, elapsed), initial)

    def test_direct_recording_graph_keeps_point_values_after_phase_warming(self):
        compiler, _ = compile_bundle(literal('same_source_history.ok'))
        warm = evaluate_prefix(compiler.model, '16384', work=compiler.reach_work)
        self.assertIsNone(warm['failure'])
        sim = _simulator(compiler.model, work=compiler.reach_work)
        source = sim.advance(F(1), 'before')
        frames = sim.recording_frames(F(1), sim.state, ['carrier.frame', 'ball.frame'],
                                      recording_context=object())
        self.assertEqual(frames['carrier.frame'].orientation, tuple(source['objects']['carrier']['orientation_wxyz']))
        self.assertEqual(frames['ball.frame'].orientation, tuple(source['objects']['ball']['orientation_wxyz']))

    def test_zero_and_nonzero_split_neutral_impulses_preserve_rotation_origin(self):
        for vector, point, neutral in (('0[N*s], 0[N*s], 0[N*s]', '1[m], 0[m], 0[m]', True),
                                       ('1[N*s], 0[N*s], 0[N*s]', '0[m], 0[m], 0[m]', False),
                                       ('0[N*s], 0[N*s], 1[N*s]', '0[m], 0[m], 2[m]', False)):
            with self.subTest(vector=vector, point=point):
                extra = '\n    at 1[s] sequence { impulse ball using vector(world, ' + vector + ') at point(ball.frame, ' + point + '); }\n'
                sim, _ = simulator(original('p01-spin-up', append=extra))
                sim.advance(F(1), 'before')
                prior = copy.deepcopy(sim.state.torques['ball'])
                before = sim.angular_state('ball', F(1), sim.state)[0]
                sim.advance(F(1), 'after')
                after = sim.state.torques['ball']
                self.assertEqual(after.rotation, prior.rotation)
                self.assertEqual(after.rotation.time, F(0))
                self.assertEqual(sim.angular_state('ball', F(1), sim.state)[0], before)
                if neutral:
                    self.assertEqual(after.reference, prior.reference)
                else:
                    self.assertEqual(after.reference.time, F(1))
                    self.assertGreater(after.reference.angle_error, prior.reference.angle_error)
                later = sim.advance(F(3, 2))['objects']['ball']
                self.assertEqual(later['torques']['rotation_anchor_seconds'], '0')
                self.assertEqual(later['angular_velocity_rad_per_s'], [0.0, 0.0, 3.0])

    def test_six_original_C3_controls_preserve_all_common_physical_observations(self):
        physics = {row['id']: row for row in json.loads((ORIGINAL / 'physics-cases.json').read_bytes())['cases']}
        observations = {row['case']: row['observations'] for row in
                        json.loads((ORIGINAL / 'state-expectations.json').read_bytes())['cases']}
        count = 0
        for frozen in EXPECTED['c3_literal_compatibility']:
            name = frozen['id']
            with self.subTest(case=name):
                self.assertEqual(hashlib.sha256((ROOT / frozen['path']).read_bytes()).hexdigest(), frozen['sha256'])
                sim, ledger = simulator(original(name))
                control_bundle = load_texture_file_manifest(ORIGINAL / physics[name]['predecessor_control']['file_manifest'])
                control_compiler, control_ledger = compile_bundle(control_bundle, profile='keyed-membership-0.1')
                control = _simulator(control_compiler.model, work=control_compiler.reach_work)
                for row in observations[name]:
                    clock = F(row['time_seconds'])
                    actual = sim.advance(clock, row['side'])
                    prior = control.advance(clock, row['side'])
                    for path in actual['objects']:
                        for field in ('position_m', 'orientation_wxyz', 'velocity_m_per_s', 'angular_velocity_rad_per_s'):
                            self.assertEqual(actual['objects'][path][field], prior['objects'][path][field], (name, clock, row['side'], path, field))
                        if path in sim.state.dynamic:
                            left, right = sim.state.dynamic[path], control.state.dynamic[path]
                            self.assertEqual((left.time, left.since), (right.time, right.since))
                            for field in ('position', 'orientation', 'velocity', 'omega'):
                                self.assertEqual(getattr(left.state, field), getattr(right.state, field))
                    self.assertEqual(sim.state.dynamic_errors, control.state.dynamic_errors)
                    self.assertEqual(sim.state.dynamic_error_times, control.state.dynamic_error_times)
                    self.assertIsNone(sim.state.torques['ball'].rotation)
                    torque = actual['objects']['ball']['torques']
                    for field, value in row['exact_fields'].items():
                        self.assertEqual(torque[field], value, (name, clock, row['side'], field))
                    for field, limits in row['error_constraints'].items():
                        if torque['axis'] is None:
                            self.assertIsNone(torque[field])
                        else:
                            error = fraction(torque[field])
                            self.assertGreaterEqual(error, fraction(limits['minimum']))
                            self.assertLessEqual(error, fraction(limits['maximum']))
                    count += 1
                self.assertLessEqual(ledger.operations, 100000)
                self.assertLessEqual(control_ledger.operations, 100000)
        self.assertEqual(count, 38)

    def test_original_callback_cannot_substitute_a_later_stage_in_warm_point_cache(self):
        owner = {'armed': False, 'changes': 0}
        omega = (F(0.6), F(0.8), F(0))
        key = (METHOD, 'spin_plan', omega, F(1))
        def check():
            if owner['armed'] and key in owner['work']._cache:
                if owner['work']._cache[key] is not owner['long_plan']:
                    owner['work']._cache[key] = owner['long_plan']
                    owner['changes'] += 1
        compiler, ledger = compile_bundle(literal('same_source_history.ok'), check=check)
        owner['work'] = compiler.reach_work
        self.assert_admitted(evaluate_prefix(compiler.model, '1', work=compiler.reach_work),
                             omega=EXPECTED['witness_under_proposed_rule']['released_omega_binary64_hex'])
        owner['long_plan'] = ReachPoseOps(compiler.reach_work).spin_plan(omega, F(16384))
        self.assertEqual(owner['long_plan'].precision_bits, 192)
        owner['armed'] = True
        result = evaluate_prefix(compiler.model, '1', work=compiler.reach_work)
        self.assertGreater(owner['changes'], 0)
        if result['failure'] is None:
            self.assert_admitted(result, omega=EXPECTED['witness_under_proposed_rule']['released_omega_binary64_hex'])
        else:
            self.assertEqual(result['failure'].diagnostic.code, 'OKL-E-RESOURCE')
        self.assertIs(ledger.check, check)
        self.assertLessEqual(ledger.operations, 100000)


if __name__ == '__main__':
    unittest.main()
