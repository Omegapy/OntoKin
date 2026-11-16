"""Finite adversarial controls for synthetic playback-preparation boundaries."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

_SPEC = importlib.util.spec_from_file_location('c250_author_model', Path(__file__).with_name('inert_model.py'))
m = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = m
_SPEC.loader.exec_module(m)


class PreparationTests(unittest.TestCase):
    def fixture(self):
        r, state, root = m.synthetic_fixture()
        p, library, animation = m.fixture_objects(root)
        return r, state, root, p, library, animation

    def run_fixture(self, items, capture=None, complete=False):
        r, state, root, p, _, _ = items
        c = capture or m.Capture()
        result = c.capture(r, state, root)
        self.assertEqual(result['component_complete'], complete, result.get('errors'))
        self.assertFalse(result['execution_admission'])
        self.assertFalse(result['native_acceptance'])
        self.assertEqual(result['R07'], 'PENDING')
        self.assertEqual(c.inventory_calls, 1)
        self.assertEqual(r.close_calls, 1)
        self.assertIn('animation_inventory', result)
        if not complete:
            self.assertEqual(result['phase'], 'REFUSED')
            self.assertTrue(result['errors'])
        return result, c

    def test_complete_retains_original_and_exact_two_intentional_changes(self):
        items = self.fixture()
        out, c = self.run_fixture(items, complete=True)
        p = items[3]
        original = out['animation_inventory']['inventory']
        final = out['mutations'][-1]['after']['inventory']
        expected = deepcopy(original)
        expected['player']['settings']['callback_mode_process']['value'] = 2
        expected['player']['settings']['assigned_animation']['value'] = original['animation_key']['value']
        self.assertEqual(final, expected)
        self.assertEqual(out['animation_inventory']['inventory'], out['animation_inventory']['recheck'])
        self.assertEqual(p.mutation_calls, ['set_callback_mode_process', 'set_assigned_animation'])
        self.assertEqual(c.boundary_reads, 4)
        self.assertEqual(p.position_reads, 2)
        self.assertTrue(p.settings['active'])
        self.assertFalse(p.settings['playing'])
        self.assertEqual(p.settings['current_animation'], '')
        self.assertIsNone(items[2].parent)
        self.assertFalse(items[2].inside_tree)
        for row in out['mutations']:
            self.assertEqual(row['status'], 'RETURNED')
            self.assertEqual(row['outcome'], 'DECLARED_CHANGE_OBSERVED')
            self.assertTrue(row['before']['complete'])
            self.assertTrue(row['after']['complete'])

    def test_actual_key_and_track_order_are_retained(self):
        items = self.fixture()
        r, state, root, p, library, animation = items
        library.animations = {m.Name('observed key / actual'):animation}
        animation.tracks.reverse()
        out, _ = self.run_fixture(items, complete=True)
        self.assertEqual(out['mutations'][1]['requested'], 'observed key / actual')
        self.assertEqual(out['mutations'][1]['after']['inventory']['tracks'][0]['source_node'], 17)

    def test_wrong_state_retains_prior_partial_receipt_without_mutating(self):
        items = list(self.fixture())
        items[1] = object()
        out, _ = self.run_fixture(items)
        self.assertFalse(out['animation_inventory']['component_complete'])
        self.assertIn('materials', out['animation_inventory'])
        self.assertEqual(items[3].mutation_calls, [])
        self.assertEqual(out['mutations'], [])

    def test_prior_material_refusal_is_not_repaired(self):
        items = self.fixture()
        items[2].children[0].material_overlay = m.c249.c248.ResourceView(99001, 'Material')
        out, _ = self.run_fixture(items)
        self.assertIn('parts', out['animation_inventory']['materials'])
        self.assertEqual(items[3].mutation_calls, [])

    def test_signal_receivers_and_processing_prestate_refuse_before_setter(self):
        cases = [('signal_connections', [object()]), ('internal_idle', True),
                 ('internal_physics', True), ('blocking_signals', True), ('animation_active', True)]
        for name, value in cases:
            with self.subTest(field=name):
                items = self.fixture()
                setattr(items[3], name, value)
                out, _ = self.run_fixture(items)
                self.assertEqual(items[3].mutation_calls, [])
                self.assertEqual(items[3].position_reads, 0)
                self.assertIn('control', out['before_manual'])
                if name == 'signal_connections':
                    self.assertEqual(out['before_manual']['control']['assignment_signal_connection_count'], 1)
                    self.assertIn('omitted', out['before_manual']['control'])

    def test_unexpected_player_prestate_stays_visible(self):
        for field, value in [('playing', True), ('assigned_animation', m.Name('preassigned')),
                             ('active', False), ('callback_mode_process', 2), ('queue', [m.Name('queued')])]:
            with self.subTest(field=field):
                items = self.fixture()
                items[3].settings[field] = value
                out, _ = self.run_fixture(items)
                self.assertEqual(items[3].mutation_calls, [])
                self.assertEqual(items[3].settings[field], value)
                self.assertFalse(out['animation_inventory']['component_complete'])

    def test_manual_setter_noop_is_not_success(self):
        items = self.fixture()
        c = m.Capture()
        c.set_manual = lambda player: player.mutation_calls.append('synthetic-noop-manual')
        out, _ = self.run_fixture(items, c)
        self.assertEqual(len(out['mutations']), 1)
        self.assertEqual(out['mutations'][0]['status'], 'RETURNED')
        self.assertEqual(out['mutations'][0]['outcome'], 'REFUSED_AFTER_ATTEMPT')
        self.assertEqual(items[3].settings['callback_mode_process'], 1)

    def test_manual_partial_change_is_retained_without_assignment(self):
        for field, value in [('active', False), ('callback_mode_method', 1), ('speed_scale', 2.0)]:
            with self.subTest(field=field):
                items = self.fixture()
                items[3].mutation_hook = lambda operation, p, c: p.settings.update({field:value})
                out, _ = self.run_fixture(items)
                self.assertEqual(items[3].settings['callback_mode_process'], 2)
                self.assertEqual(items[3].settings[field], value)
                self.assertEqual(items[3].mutation_calls, ['set_callback_mode_process'])
                self.assertFalse(out['mutations'][0]['after']['complete'])

    def test_internal_flag_and_receiver_drift_after_manual_refuse(self):
        for field, value in [('internal_idle', True), ('internal_physics', True), ('signal_connections', [object()])]:
            with self.subTest(field=field):
                items = self.fixture()
                items[3].mutation_hook = lambda operation, p, c: setattr(p, field, value)
                out, _ = self.run_fixture(items)
                self.assertEqual(len(out['mutations']), 1)
                self.assertEqual(items[3].settings['callback_mode_process'], 2)
                self.assertEqual(getattr(items[3], field), value)

    def test_live_scene_and_resource_drift_after_manual_refuse(self):
        cases = {
            'player-freed': lambda r, p, l, a: setattr(p, 'alive', False),
            'player-queued': lambda r, p, l, a: setattr(p, 'queued', True),
            'tree-entry': lambda r, p, l, a: setattr(r, 'inside_tree', True),
            'target-freed': lambda r, p, l, a: setattr(r.children[0], 'alive', False),
            'target-map': lambda r, p, l, a: r.resolve_map.update(native_0=r.children[1]),
            'library-replaced': lambda r, p, l, a: p.libraries.update({m.Name(''):m.c249.LibraryView(99002, 'AnimationLibrary', animations=l.animations)}),
            'animation-replaced': lambda r, p, l, a: l.animations.update({next(iter(l.animations)):m.c249.AnimationView(99003, 'Animation', tracks=a.tracks)}),
            'material-selector': lambda r, p, l, a: setattr(r.children[0], 'material_overlay', m.c249.c248.ResourceView(99004, 'Material')),
            'track-path': lambda r, p, l, a: setattr(a.tracks[0], 'path', m.PathValue('native_1')),
            'metadata': lambda r, p, l, a: a.metadata.update(changed='observed drift'),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                items = self.fixture()
                r, state, root, p, l, a = items
                p.mutation_hook = lambda operation, player, c: change(root, player, l, a)
                out, _ = self.run_fixture(items)
                self.assertEqual(len(out['mutations']), 1)
                self.assertFalse(out['mutations'][0]['after']['complete'])
                self.assertEqual(p.mutation_calls, ['set_callback_mode_process'])

    def test_assignment_noop_retains_completed_manual_change(self):
        items = self.fixture()
        c = m.Capture()
        c.assign_stopped = lambda p, key: p.mutation_calls.append('synthetic-noop-assignment')
        out, _ = self.run_fixture(items, c)
        self.assertEqual(len(out['mutations']), 2)
        self.assertEqual(out['mutations'][0]['outcome'], 'DECLARED_CHANGE_OBSERVED')
        self.assertEqual(out['mutations'][1]['outcome'], 'REFUSED_AFTER_ATTEMPT')
        self.assertEqual(items[3].position_reads, 0)
        self.assertEqual(items[3].settings['callback_mode_process'], 2)

    def test_bad_assignment_readbacks_guard_position_getter(self):
        for field, value in [('animation_active', False), ('current_position', 0.5), ('current_length', 9.0)]:
            with self.subTest(field=field):
                items = self.fixture()
                def hook(operation, p, c):
                    if operation == 'set_assigned_animation': setattr(p, field, value)
                items[3].mutation_hook = hook
                out, _ = self.run_fixture(items)
                self.assertEqual(len(out['mutations']), 2)
                self.assertTrue(items[3].settings['assigned_animation'])
                self.assertEqual(items[3].position_reads, 0 if field == 'animation_active' else 1)
                self.assertFalse(out['mutations'][1]['after']['complete'])

    def test_assignment_callback_cannot_hide_playback_resource_or_registry_drift(self):
        for name in ('playing', 'current', 'receiver', 'queued', 'library', 'registry'):
            with self.subTest(case=name):
                items = self.fixture()
                r, state, root, p, l, a = items
                def hook(operation, player, capture):
                    if operation != 'set_assigned_animation': return
                    if name == 'playing': player.settings['playing'] = True
                    elif name == 'current': player.settings['current_animation'] = m.Name('unexpected')
                    elif name == 'receiver': player.signal_connections.append(object())
                    elif name == 'queued': player.queued = True
                    elif name == 'library': l.identity += 1
                    else: r.faults.append('late synthetic external fault')
                p.mutation_hook = hook
                out, _ = self.run_fixture(items)
                self.assertEqual(len(out['mutations']), 2)
                self.assertEqual(p.mutation_calls, ['set_callback_mode_process', 'set_assigned_animation'])
                self.assertTrue(p.settings['assigned_animation'])
                self.assertFalse(out['mutations'][1]['after']['complete'])

    def test_drift_between_setters_refuses_before_assignment(self):
        items = self.fixture()
        c = m.Capture()
        original = c.boundary
        def boundary(registry, root, materials, expected, assigned):
            if c.boundary_reads == 2:
                items[3].signal_connections.append(object())
            return original(registry, root, materials, expected, assigned)
        c.boundary = boundary
        out, _ = self.run_fixture(items, c)
        self.assertEqual(len(out['mutations']), 1)
        self.assertTrue(out['mutations'][0]['after']['complete'])
        self.assertFalse(out['before_assignment']['complete'])
        self.assertEqual(items[3].settings['assigned_animation'], '')

    def test_attempt_record_exists_during_setter(self):
        items = self.fixture()
        seen = []
        def hook(operation, p, c):
            seen.append((operation, c.result['mutations'][-1]['status'], c.result['mutations'][-1]['after']['status']))
        items[3].mutation_hook = hook
        self.run_fixture(items, complete=True)
        self.assertEqual(seen, [('set_callback_mode_process','ATTEMPTED','NOT_OBSERVED'), ('set_assigned_animation','ATTEMPTED','NOT_OBSERVED')])

    def test_reentrant_attempt_latches_failure_without_recapture(self):
        for operation in ('set_callback_mode_process', 'set_assigned_animation'):
            with self.subTest(operation=operation):
                items = self.fixture()
                r, state, root, p, l, a = items
                nested = []
                def hook(current, player, capture):
                    if current == operation: nested.append(capture.capture(r, state, root))
                p.mutation_hook = hook
                out, _ = self.run_fixture(items)
                self.assertEqual(len(nested), 1)
                self.assertFalse(nested[0]['component_complete'])
                self.assertIn('reentry', out['errors'][0])
                self.assertEqual(len(out['mutations']), 1 if operation == 'set_callback_mode_process' else 2)

    def test_repeated_reader_retains_success_history_but_refuses(self):
        items = self.fixture()
        out, c = self.run_fixture(items, complete=True)
        retry = c.capture(*items[:3])
        self.assertFalse(retry['component_complete'])
        self.assertEqual(retry['mutations'], out['mutations'])
        self.assertEqual(c.inventory_calls, 1)
        self.assertEqual(items[0].close_calls, 1)
        self.assertEqual(len(items[3].mutation_calls), 2)

    def test_preconsumed_state_does_not_retry_after_refusal(self):
        items = self.fixture()
        prior = m.c249.Capture().capture(*items[:3])
        self.assertTrue(prior['component_complete'])
        c = m.Capture()
        out = c.capture(*items[:3])
        self.assertFalse(out['component_complete'])
        self.assertEqual(items[0].close_calls, 2)
        c.capture(*items[:3])
        self.assertEqual(items[0].close_calls, 2)
        self.assertEqual(items[3].mutation_calls, [])

    def test_returned_receipt_is_detached_from_internal_history(self):
        items = self.fixture()
        out, c = self.run_fixture(items, complete=True)
        out['animation_inventory']['inventory']['tracks'].clear()
        out['mutations'][0]['before']['inventory']['tracks'].clear()
        self.assertEqual(len(c.result['animation_inventory']['inventory']['tracks']), 36)
        self.assertEqual(len(c.result['mutations'][0]['before']['inventory']['tracks']), 36)

    def test_late_control_drift_retains_values_and_omissions_s01(self):
        for field in ('blocking_signals', 'signal_connections'):
            with self.subTest(field=field):
                items = self.fixture()
                reads = []
                def hook(player, inventory_read):
                    reads.append(inventory_read)
                    if len(reads) == 4:
                        setattr(player, field, True if field == 'blocking_signals' else [object()])
                items[3].inventory_hook = hook
                out, _ = self.run_fixture(items)
                control = out['before_manual']['control']
                self.assertEqual(items[3].mutation_calls, [])
                if field == 'blocking_signals':
                    self.assertFalse(control['blocking_signals']['value'])
                    self.assertTrue(control['final_blocking_signals']['value'])
                else:
                    self.assertEqual(control['assignment_signal_connection_count'], 0)
                    self.assertEqual(control['final_assignment_signal_connection_count'], 1)
                    self.assertIn('Callable', control['final_omitted'][0])

    def test_final_scene_partial_refusal_is_retained_s02(self):
        items = self.fixture()
        r, state, root, p, library, animation = items
        def mutation(operation, player, capture):
            if operation == 'set_callback_mode_process':
                def scene_hook(node, scene_read):
                    if capture.boundary_reads == 2 and scene_read == 2:
                        node.children[0].native_class = 'Node3D'
                root.scene_hook = scene_hook
        p.mutation_hook = mutation
        out, _ = self.run_fixture(items)
        self.assertEqual(len(out['mutations']), 1)
        self.assertIn('scene_after_drift', out['mutations'][0]['after']['inventory'])
        self.assertTrue(out['mutations'][0]['after']['inventory']['scene_after_drift']['nodes'])

    def test_late_assigned_position_and_length_drift_are_observed(self):
        for field, value in [('current_position', 0.125), ('current_length', 3.0), ('animation_active', False)]:
            with self.subTest(field=field):
                items = self.fixture()
                def mutation(operation, player, capture):
                    if operation == 'set_assigned_animation':
                        def inventory_hook(p, inventory_read):
                            if inventory_read == 2:
                                setattr(p, field, value)
                        player.inventory_hook = inventory_hook
                items[3].mutation_hook = mutation
                out, _ = self.run_fixture(items)
                after = out['mutations'][1]['after']['control']
                self.assertEqual(after['position']['value'], 0.0)
                if field == 'animation_active':
                    self.assertNotIn('final_position', after)
                    self.assertFalse(after['final_animation_active']['value'])
                elif field == 'current_position':
                    self.assertEqual(after['final_position']['value'], value)
                else:
                    self.assertEqual(after['final_length']['value'], value)


if __name__ == '__main__':
    unittest.main(verbosity=2)
