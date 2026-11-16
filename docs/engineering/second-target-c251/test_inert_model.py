"""Adversarial controls for fabricated C251 attachment and retained readbacks."""
from copy import deepcopy
import importlib.util
import math
from pathlib import Path
import sys
import unittest

_SPEC = importlib.util.spec_from_file_location('c251_author_model', Path(__file__).with_name('inert_model.py'))
m = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = m
_SPEC.loader.exec_module(m)


class AttachmentTests(unittest.TestCase):
    def fixture(self):
        registry, state, root, host = m.synthetic_fixture()
        player, library, animation = m.fixture_objects(root)
        return registry, state, root, host, player, library, animation

    def run_fixture(self, items, capture=None, complete=False):
        registry, state, root, host = items[:4]
        capture = capture or m.Capture()
        result = capture.capture(registry, state, root, host)
        self.assertEqual(result['component_complete'], complete, result['errors'])
        self.assertFalse(result['execution_admission'])
        self.assertFalse(result['native_acceptance'])
        self.assertEqual(result['R07'], 'PENDING')
        self.assertEqual(result['diagnostic_coverage'], 'UNESTABLISHED')
        self.assertEqual(capture.preparation_calls, 1)
        self.assertEqual(registry.close_calls, 1)
        self.assertIn('playback_preparation', result)
        if not complete:
            self.assertEqual(result['phase'], 'REFUSED')
            self.assertTrue(result['errors'])
        return result, capture

    def test_complete_has_one_owned_preparation_and_one_root_attachment(self):
        items = self.fixture()
        registry, state, root, host, player, library, animation = items
        out, capture = self.run_fixture(items, complete=True)
        self.assertEqual(capture.attachment_calls, 1)
        self.assertEqual(capture.boundary_reads, 2)
        self.assertIs(root.parent, host.window)
        self.assertEqual(host.window.children, [root])
        self.assertEqual(player.mutation_calls, ['set_callback_mode_process', 'set_assigned_animation'])
        self.assertTrue(out['playback_preparation']['component_complete'])
        mutation = out['mutations'][0]
        self.assertEqual(len(out['mutations']), 1)
        self.assertEqual((mutation['status'], mutation['outcome']), ('RETURNED', 'DECLARED_CHANGE_OBSERVED'))
        self.assertTrue(mutation['before']['complete'])
        self.assertTrue(mutation['after']['complete'])
        self.assertTrue(out['mutations'][0]['after']['complete'])
        self.assertFalse(player.settings['playing'])
        self.assertEqual(player.current_position, 0.0)
        self.assertEqual(len(out['mutations'][0]['after']['inventory']['tracks']), 36)
        self.assertEqual(len(out['before_attachment']['nodes']), 20)
        self.assertEqual(sum('local_transform' in row for row in out['before_attachment']['nodes']), 19)

    def test_explicit_inventory_change_is_only_inside_tree_and_root_parent(self):
        items = self.fixture()
        out, _ = self.run_fixture(items, complete=True)
        expected = deepcopy(out['playback_preparation']['mutations'][-1]['after']['inventory'])
        for row in expected['scene']['nodes']:
            row['inside_tree'] = True
            if row['identity']['instance_id'] == items[2].identity:
                row['parent'] = {'type':24, 'instance_id':items[3].window.identity, 'class':'Window'}
        self.assertEqual(out['mutations'][0]['after']['inventory'], expected)
        self.assertEqual(out['mutations'][0]['after']['inventory'], expected)

    def test_raw_local_values_and_metadata_are_retained_without_recomposition(self):
        items = self.fixture()
        root = items[2]
        root.metadata = {'source':m.Name('original'), 'typed':[1, True, 1.0, -0.0]}
        root.local_transform = [2.0, 0.1, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 4.0, -0.0, 7.25, -9.0]
        out, _ = self.run_fixture(items, complete=True)
        before = out['before_attachment']['nodes'][0]
        after = out['mutations'][0]['after']['nodes'][0]
        self.assertEqual(before['local_transform'], root.local_transform)
        self.assertEqual(before['local_transform'], after['local_transform'])
        self.assertLess(math.copysign(1.0, after['local_transform'][9]), 0)
        self.assertEqual(before['metadata'], after['metadata'])
        self.assertEqual(after['local_transform_layout'], 'basis columns x/y/z then origin; raw 12 components')

    def test_scene_tree_script_is_retained_while_window_script_is_refused(self):
        items = self.fixture()
        items[3].script = m.c249.ResourceView(8500, 'GDScript')
        out, _ = self.run_fixture(items, complete=True)
        self.assertEqual(out['before_attachment']['host']['script']['instance_id'], 8500)
        items = self.fixture()
        items[3].window.script = m.c249.ResourceView(8501, 'GDScript')
        out, capture = self.run_fixture(items)
        self.assertEqual(capture.attachment_calls, 0)
        self.assertEqual(out['before_attachment']['host']['window']['script']['instance_id'], 8501)

    def test_actual_animation_key_and_track_order_remain_observations(self):
        items = self.fixture()
        items[5].animations = {m.Name('real / observed key'):items[6]}
        items[6].tracks.reverse()
        out, _ = self.run_fixture(items, complete=True)
        inventory = out['mutations'][0]['after']['inventory']
        self.assertEqual(inventory['animation_key']['value'], 'real / observed key')
        self.assertEqual(inventory['tracks'][0]['source_node'], 17)

    def test_wrong_state_retains_prior_partial_receipt_and_never_attaches(self):
        items = list(self.fixture())
        items[1] = object()
        out, capture = self.run_fixture(items)
        self.assertFalse(out['playback_preparation']['component_complete'])
        self.assertIn('animation_inventory', out['playback_preparation'])
        self.assertEqual(out['mutations'], [])
        self.assertEqual(capture.attachment_calls, 0)
        self.assertIsNone(items[2].parent)

    def test_prior_setter_refusal_preserves_manual_partial_changes(self):
        items = self.fixture()
        items[4].mutation_hook = lambda operation, player, capture: player.settings.update(active=False)
        out, capture = self.run_fixture(items)
        prior = out['playback_preparation']
        self.assertFalse(prior['component_complete'])
        self.assertEqual(prior['mutations'][0]['outcome'], 'REFUSED_AFTER_ATTEMPT')
        self.assertEqual(items[4].settings['callback_mode_process'], 2)
        self.assertFalse(items[4].settings['active'])
        self.assertEqual(capture.attachment_calls, 0)

    def test_wrong_thread_refuses_before_preparation_reads_setters_or_consumption(self):
        items = self.fixture()
        registry, state, root, host, player = items[:5]
        host.caller_thread_id = host.main_thread_id + 1
        capture = m.Capture()
        out = capture.capture(registry, state, root, host)
        self.assertFalse(out['component_complete'])
        self.assertEqual(out['phase'], 'REFUSED')
        self.assertFalse(out['execution_admission'])
        self.assertEqual(out['playback_preparation'], {'status':'NOT_ATTEMPTED'})
        self.assertEqual(out['entry_threads'], {'caller_thread':2, 'main_thread':1})
        self.assertEqual(capture.preparation_calls, 0)
        self.assertEqual(capture.boundary_reads, 0)
        self.assertEqual(capture.attachment_calls, 0)
        self.assertEqual(registry.close_calls, 0)
        self.assertFalse(registry.closed)
        self.assertEqual(player.mutation_calls, [])
        self.assertEqual(player.root_lookup_reads, 0)
        self.assertEqual(out['mutations'], [])
        self.assertIsNone(root.parent)
        self.assertFalse(root.inside_tree)

    def test_wrong_host_and_host_state_refuse_without_attachment(self):
        cases = [('main_loop', object()), ('native_class', 'OtherTree'), ('alive', False),
                 ('queued', True), ('paused', False), ('physics_interpolation', True),
                 ('editor_hint', True), ('blocking_signals', True),
                 ('node_count', 2), ('processed_tweens', 1)]
        for field, value in cases:
            with self.subTest(field=field):
                items = self.fixture()
                setattr(items[3], field, value)
                out, capture = self.run_fixture(items)
                self.assertEqual(capture.attachment_calls, 0)
                self.assertEqual(out['mutations'], [])
                self.assertTrue(out['playback_preparation']['component_complete'])
                self.assertIsNone(items[2].parent)

    def test_nonempty_host_and_current_scene_refuse(self):
        for which in ('child', 'current_scene'):
            with self.subTest(which=which):
                items = self.fixture()
                other = m.c247.NodeView(9900, native_class='Node')
                if which == 'child':
                    items[3].window.children.append(other)
                else:
                    items[3].current_scene = other
                out, capture = self.run_fixture(items)
                self.assertEqual(capture.attachment_calls, 0)

    def test_host_window_policy_is_observed_and_never_repaired(self):
        cases = [('native_class', 'SubViewport'), ('queued', True), ('inside_tree', False),
                 ('ready', False), ('tree', None), ('process_mode', 0),
                 ('process_thread_group', 2), ('physics_interpolation_mode', 0),
                 ('interpolated', True), ('can_process', True), ('blocking_signals', True)]
        for field, value in cases:
            with self.subTest(field=field):
                items = self.fixture()
                setattr(items[3].window, field, value)
                out, capture = self.run_fixture(items)
                self.assertEqual(getattr(items[3].window, field), value)
                self.assertEqual(capture.attachment_calls, 0)
                self.assertEqual(out['mutations'], [])

    def test_preexisting_tree_window_and_product_receivers_refuse(self):
        targets = [('tree', s) for s in m.TREE_SIGNALS]
        targets += [('window', s) for s in m.WINDOW_SIGNALS]
        targets += [('product', s) for s in m.NODE_SIGNALS]
        for target, signal in targets:
            with self.subTest(target=target, signal=signal):
                items = self.fixture()
                value = items[3] if target == 'tree' else items[3].window if target == 'window' else items[4]
                value.signal_counts[signal] = 1
                out, capture = self.run_fixture(items)
                self.assertEqual(capture.attachment_calls, 0)
                self.assertEqual(value.signal_counts[signal], 1)

    def test_product_processing_readiness_and_transform_policy_refuse(self):
        cases = [('ready', True), ('process_mode', 4), ('process_thread_group', 1),
                 ('physics_interpolation_mode', 2), ('groups', [m.Name('external-group')]),
                 ('blocking_signals', True), ('top_level', True), ('scale_disabled', True)]
        cases += [(field, True) for field in m.PROCESS_FLAGS]
        for field, value in cases:
            with self.subTest(field=field):
                items = self.fixture()
                setattr(items[2].children[0], field, value)
                out, capture = self.run_fixture(items)
                self.assertEqual(capture.attachment_calls, 0)
                self.assertEqual(getattr(items[2].children[0], field), value)

    def test_malformed_or_nonfinite_local_transform_refuses_with_raw_values(self):
        cases = [[], [0.0]*11, m.IDENTITY_TRANSFORM[:-1]+[float('nan')],
                 m.IDENTITY_TRANSFORM[:-1]+[float('inf')], m.IDENTITY_TRANSFORM[:-1]+[True]]
        for values in cases:
            with self.subTest(values=repr(values)):
                items = self.fixture()
                items[2].local_transform = values
                out, capture = self.run_fixture(items)
                self.assertEqual(capture.attachment_calls, 0)
                self.assertIn('local_transform', out['before_attachment']['nodes'][0])

    def test_unsupported_metadata_refuses_with_partial_capture(self):
        items = self.fixture()
        items[2].metadata = {'first':1, 'unsupported':object()}
        out, capture = self.run_fixture(items)
        rows = out['before_attachment']['nodes'][0]['metadata']
        self.assertEqual(rows[0]['value']['value'], 1)
        self.assertEqual(rows[1]['key']['value'], 'unsupported')
        self.assertEqual(capture.attachment_calls, 0)

    def test_noop_attachment_is_returned_but_refused_with_actual_membership(self):
        items = self.fixture()
        capture = m.Capture()
        def noop(host, root):
            capture.attachment_calls += 1
        capture.attach = noop
        out, _ = self.run_fixture(items, capture)
        mutation = out['mutations'][0]
        self.assertEqual(mutation['status'], 'RETURNED')
        self.assertEqual(mutation['outcome'], 'REFUSED_AFTER_ATTEMPT')
        self.assertEqual(mutation['after']['host']['window']['children'], [])
        self.assertIsNone(items[2].parent)
        self.assertEqual(capture.attachment_calls, 1)

    def test_partial_attachment_never_rolls_back_or_retries(self):
        items = self.fixture()
        capture = m.Capture()
        def partial(host, root):
            capture.attachment_calls += 1
            root.parent = host.window
            host.window.children.append(root)
        capture.attach = partial
        out, _ = self.run_fixture(items, capture)
        self.assertIs(items[2].parent, items[3].window)
        self.assertFalse(items[2].inside_tree)
        self.assertFalse(out['mutations'][0]['after']['complete'])
        self.assertEqual(capture.attachment_calls, 1)
        self.assertEqual(out['mutations'][0]['outcome'], 'REFUSED_AFTER_ATTEMPT')

    def test_late_attachment_lifecycle_or_signal_drift_remains_visible(self):
        cases = {
            'root-freed':lambda items:setattr(items[2], 'alive', False),
            'target-freed':lambda items:setattr(items[2].children[0], 'alive', False),
            'target-ready':lambda items:setattr(items[2].children[0], 'ready', False),
            'target-queued':lambda items:setattr(items[2].children[0], 'queued', True),
            'target-tree':lambda items:setattr(items[2].children[0], 'tree', None),
            'target-interpolated':lambda items:setattr(items[2].children[0], 'interpolated', True),
            'player-cache-receiver':lambda items:items[4].signal_counts.update(caches_cleared=1),
            'tree-receiver':lambda items:items[3].signal_counts.update(node_added=1),
            'window-receiver':lambda items:items[3].window.signal_counts.update(child_entered_tree=1),
            'host-resumed':lambda items:setattr(items[3], 'paused', False),
            'registry-fault':lambda items:items[0].faults.append('observed synthetic engine fault'),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                items = self.fixture()
                capture = m.Capture()
                capture.attachment_hook = lambda host, root, current:change(items)
                out, _ = self.run_fixture(items, capture)
                self.assertEqual(capture.attachment_calls, 1)
                self.assertEqual(out['mutations'][0]['status'], 'RETURNED')
                self.assertEqual(out['mutations'][0]['outcome'], 'REFUSED_AFTER_ATTEMPT')
                self.assertEqual(len(items[3].window.children), 1)

    def test_transforms_metadata_ownership_and_names_cannot_drift_silently(self):
        cases = {
            'transform':lambda items:items[2].children[0].local_transform.__setitem__(9, 8.0),
            'metadata':lambda items:items[2].metadata.update(new='late'),
            'owner':lambda items:setattr(items[2].children[0], 'owner', None),
            'renamed':lambda items:setattr(items[2], 'name', m.Name('silently-renamed')),
            'host-metadata':lambda items:items[3].metadata.update(new='late'),
            'host-window-identity':lambda items:setattr(items[3].window, 'identity', 9999),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                items = self.fixture()
                capture = m.Capture()
                capture.attachment_hook = lambda host, root, current:change(items)
                out, _ = self.run_fixture(items, capture)
                self.assertEqual(out['mutations'][0]['outcome'], 'REFUSED_AFTER_ATTEMPT')
                self.assertIs(items[2].parent, items[3].window)

    def test_player_controls_are_rechecked_after_lifecycle(self):
        cases = [('internal_idle', True), ('internal_physics', True), ('animation_active', False),
                 ('current_position', 0.25), ('current_length', 3.0), ('signal_connections', [object()])]
        for field, value in cases:
            with self.subTest(field=field):
                items = self.fixture()
                capture = m.Capture()
                capture.attachment_hook = lambda host, root, current:setattr(items[4], field, value)
                out, _ = self.run_fixture(items, capture)
                self.assertFalse(out['mutations'][0]['after']['complete'])
                self.assertEqual(getattr(items[4], field), value)

    def test_inventory_resource_and_target_drift_refuses_after_attachment(self):
        cases = {
            'mode':lambda items:items[4].settings.update(callback_mode_process=1),
            'active':lambda items:items[4].settings.update(active=False),
            'playing':lambda items:items[4].settings.update(playing=True),
            'current':lambda items:items[4].settings.update(current_animation=m.Name('wrong')),
            'assigned':lambda items:items[4].settings.update(assigned_animation=m.Name('wrong')),
            'library':lambda items:setattr(items[5], 'identity', 9900),
            'animation':lambda items:setattr(items[6], 'identity', 9901),
            'track-target':lambda items:items[2].resolve_map.update(native_0=items[2].children[1]),
            'track-path':lambda items:setattr(items[6].tracks[0], 'path', m.PathValue('native_1')),
            'material-overlay':lambda items:setattr(items[2].children[0], 'material_overlay', m.c249.c248.ResourceView(9902, 'Material')),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                items = self.fixture()
                capture = m.Capture()
                capture.attachment_hook = lambda host, root, current:change(items)
                out, _ = self.run_fixture(items, capture)
                self.assertFalse(out['mutations'][0]['after']['complete'])
                self.assertEqual(capture.attachment_calls, 1)

    def test_mutation_attempt_is_visible_before_attachment_effect_returns(self):
        items = self.fixture()
        capture = m.Capture()
        seen = []
        capture.attachment_hook = lambda host, root, current:seen.append(
            (current.result['mutations'][0]['status'], current.result['mutations'][0]['after']['status']))
        self.run_fixture(items, capture, complete=True)
        self.assertEqual(seen, [('ATTEMPTED', 'NOT_OBSERVED')])

    def test_reentry_latches_refusal_after_partial_effect_without_recapture(self):
        items = self.fixture()
        capture = m.Capture()
        nested = []
        capture.attachment_hook = lambda host, root, current:nested.append(current.capture(*items[:4]))
        out, _ = self.run_fixture(items, capture)
        self.assertEqual(len(nested), 1)
        self.assertFalse(nested[0]['component_complete'])
        self.assertIn('reentry', out['errors'][0])
        self.assertEqual(capture.attachment_calls, 1)
        self.assertIs(items[2].parent, items[3].window)

    def test_repeat_refuses_with_preserved_success_history(self):
        items = self.fixture()
        out, capture = self.run_fixture(items, complete=True)
        repeated = capture.capture(*items[:4])
        self.assertFalse(repeated['component_complete'])
        self.assertEqual(repeated['phase'], 'REFUSED')
        self.assertEqual(repeated['mutations'], out['mutations'])
        self.assertEqual(capture.preparation_calls, 1)
        self.assertEqual(capture.attachment_calls, 1)
        self.assertEqual(items[0].close_calls, 1)

    def test_postboundary_repeat_detects_late_local_drift_and_keeps_initial_values(self):
        items = self.fixture()
        capture = m.Capture()
        def late_inventory(player, count):
            if count == 2:
                items[2].children[0].local_transform[9] += 1.0
        capture.attachment_hook = lambda host, root, current:setattr(items[4], 'inventory_hook', late_inventory)
        out, _ = self.run_fixture(items, capture)
        after = out['mutations'][0]['after']
        self.assertFalse(after['complete'])
        self.assertEqual(out['mutations'][0]['outcome'], 'REFUSED_AFTER_ATTEMPT')
        self.assertNotEqual(after['nodes'], after['nodes_recheck'])

    def test_detached_can_process_getter_is_never_read(self):
        items = self.fixture()
        capture = m.Capture()
        observed = []
        def hook(host, root, current):
            observed.append([node.can_process_reads for node in [root]+root.children])
        capture.attachment_hook = hook
        out, _ = self.run_fixture(items, capture, complete=True)
        self.assertEqual(observed, [[0]*20])
        self.assertTrue(all(node.can_process_reads == 2 for node in [items[2]]+items[2].children))
        for row in out['before_attachment']['nodes']:
            self.assertEqual(row['can_process']['status'], 'NOT_OBSERVED')
        for row in out['mutations'][0]['after']['nodes']:
            self.assertIs(row['can_process'], False)

    def test_partial_boundary_is_attached_to_result_before_its_reads(self):
        items = self.fixture()
        capture = m.Capture()
        observed = []
        def hook(number, attached, current):
            field = current.result['mutations'][0]['after'] if attached else current.result['before_attachment']
            observed.append((number, field['complete'], field['nodes'][:]))
        capture.boundary_hook = hook
        self.run_fixture(items, capture, complete=True)
        self.assertEqual(observed, [(1, False, []), (2, False, [])])

    def test_same_identity_material_value_drift_is_an_explicit_limit_witness(self):
        items = self.fixture()
        material = items[2].children[0].mesh.surface_material
        capture = m.Capture()
        capture.attachment_hook = lambda host, root, current:setattr(material, 'metallic', 0.9)
        out, _ = self.run_fixture(items, capture, complete=True)
        self.assertEqual(material.metallic, 0.9)
        self.assertFalse(out['native_acceptance'])
        self.assertFalse(out['execution_admission'])

    def test_transient_mutation_can_be_invisible_to_boundary_reads(self):
        items = self.fixture()
        capture = m.Capture()
        def hook(host, root, current):
            root.metadata['transient'] = True
            del root.metadata['transient']
        capture.attachment_hook = hook
        out, _ = self.run_fixture(items, capture, complete=True)
        self.assertIn('no atomicity', out['stability'])

    def test_final_registry_fault_survives_early_postattachment_host_refusal(self):
        for field, value in [('node_count', 22), ('main_loop', object())]:
            with self.subTest(field=field):
                items = self.fixture()
                capture = m.Capture()
                def hook(host, root, current):
                    items[0].faults.append('new diagnostic during attachment')
                    setattr(host, field, value)
                capture.attachment_hook = hook
                out, _ = self.run_fixture(items, capture)
                self.assertFalse(out['mutations'][0]['after']['complete'])
                self.assertEqual(out['registry_final']['faults'], ['new diagnostic during attachment'])
                self.assertEqual(out['registry_finish'], {'status':'OBSERVED'})
                self.assertNotIn('component finish', out['errors'][0])
                self.assertEqual(capture.attachment_calls, 1)
                self.assertIs(items[2].parent, items[3].window)

    def test_fault_after_last_boundary_is_latched_by_final_snapshot(self):
        items = self.fixture()
        capture = m.Capture()
        actual_boundary = capture.boundary
        def boundary(registry, root, host, materials, expected, attached, receipt=None):
            result = actual_boundary(registry, root, host, materials, expected, attached, receipt)
            if attached and result['complete']:
                registry.faults.append('final-only synthetic fault')
            return result
        capture.boundary = boundary
        out, _ = self.run_fixture(items, capture)
        self.assertTrue(out['mutations'][0]['after']['complete'])
        self.assertEqual(out['mutations'][0]['outcome'], 'DECLARED_CHANGE_OBSERVED')
        self.assertEqual(out['registry_final']['faults'], ['final-only synthetic fault'])
        self.assertIn('component finish', out['errors'][0])

    def test_unsupported_thread_finish_omits_registry_without_reading_it(self):
        items = self.fixture()
        class UnreadableRegistry:
            close_calls = 0
            @property
            def faults(self):
                raise AssertionError('registry faults must not be read on unsupported thread')
        registry = UnreadableRegistry()
        items[3].caller_thread_id = 2
        capture = m.Capture()
        out = capture.capture(registry, items[1], items[2], items[3])
        self.assertFalse(out['component_complete'])
        self.assertEqual(out['playback_preparation'], {'status':'NOT_ATTEMPTED'})
        self.assertEqual(out['registry_finish'], {'status':'NOT_OBSERVED', 'reason':'unsupported thread'})
        self.assertEqual(out['registry_final'], {'status':'NOT_OBSERVED', 'reason':'unsupported thread'})
        self.assertEqual(capture.preparation_calls, 0)
        self.assertEqual(registry.close_calls, 0)

    def test_repeat_on_wrong_thread_keeps_previous_registry_evidence(self):
        items = self.fixture()
        out, capture = self.run_fixture(items, complete=True)
        previous = deepcopy(out['registry_final'])
        items[3].caller_thread_id = 2
        repeated = capture.capture(*items[:4])
        self.assertFalse(repeated['component_complete'])
        self.assertEqual(repeated['registry_final'], previous)
        self.assertEqual(repeated['registry_finish'], {'status':'NOT_OBSERVED', 'reason':'unsupported thread'})
        self.assertEqual(capture.preparation_calls, 1)
        self.assertEqual(capture.attachment_calls, 1)

    def test_inherited_detached_validator_still_refuses_attached_tree(self):
        items = self.fixture()
        out, _ = self.run_fixture(items, complete=True)
        reader = m.c249.Capture()
        materials = out['playback_preparation']['animation_inventory']['materials']
        with self.assertRaises(m.c249.Refusal):
            reader.scene(items[2], materials, {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
