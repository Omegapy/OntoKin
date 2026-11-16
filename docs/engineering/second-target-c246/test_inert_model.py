"""Finite C246 synthetic state/failure controls; Godot is never started."""
from dataclasses import replace
import math
import random
import unittest

from inert_model import MESHES, Original, Final, Registry, Session, detached


def original(i):
    return Original(i, MESHES[i], 100+i, 100+i, i, float(MESHES[i]))


def prepared(order=range(18)):
    state = object()
    session = Session(state)
    for i in order:
        assert session.capture(state, original(i))
    return state, session


def replaced(order=range(18)):
    state, session = prepared()
    for i in order:
        assert session.replace(i, 100+i, 200+i)
    return state, session


def finals():
    return [Final(i, 200+i) for i in range(18)]


class TransitionControls(unittest.TestCase):
    def test_complete_component_never_grants_admission(self):
        state, s = replaced()
        self.assertTrue(s.finish(state, 90, finals()))
        result = s.receipt()
        self.assertTrue(result['complete'])
        self.assertFalse(result['admission'])
        self.assertFalse(result['native_acceptance'])
        self.assertEqual(result['diagnostic_coverage'], 'UNESTABLISHED')

    def test_callback_and_replacement_permutations(self):
        for seed in range(18):
            with self.subTest(seed=seed):
                order = list(range(18)); random.Random(seed).shuffle(order)
                state, s = prepared(order)
                for i in reversed(order):
                    self.assertTrue(s.replace(i, 100+i, 200+i))
                f = finals(); random.Random(seed+18).shuffle(f)
                self.assertTrue(s.finish(state, 90, f))

    def test_all_eighteen_native_json_mesh_doubles(self):
        state, s = prepared()
        self.assertEqual(len(s.originals), 18)
        for i in range(18):
            self.assertIs(type(s.originals[i]['row'].json_mesh), float)
            self.assertEqual(s.originals[i]['row'].json_mesh, float(MESHES[i]))

    def test_native_json_mesh_malformed_values(self):
        for value in (0, True, False, '0', None, 0.1, -0.1, math.nan, math.inf, -math.inf, 5.0):
            with self.subTest(value=repr(value)):
                state = object(); s = Session(state)
                self.assertFalse(s.capture(state, replace(original(0), json_mesh=value)))
                self.assertEqual(s.phase, 'FAILED')

    def test_original_map_and_shape_refusals(self):
        changes = ({'mesh': 1}, {'forward': 999}, {'inverse': 1}, {'gltf_identity_matches': False},
                   {'node_count': 17}, {'index': -1}, {'index': 18}, {'index': False},
                   {'index': 0.0}, {'old': 0}, {'old': True}, {'root': 0}, {'root': 100},
                   {'root_class': 'MeshInstance3D'}, {'native_class': 'MeshInstance3D'},
                   {'script': object()}, {'resource_script': True}, {'custom_signal': True},
                   {'signal_valid': False})
        for change in changes:
            with self.subTest(change=change):
                state = object(); s = Session(state)
                self.assertFalse(s.capture(state, replace(original(0), **change)))

    def test_wrong_state_fails_before_map_read(self):
        s = Session(object())
        self.assertFalse(s.capture(object(), original(0)))
        self.assertEqual(s.map_reads, 0)

    def test_duplicate_index_refused(self):
        state = object(); s = Session(state)
        self.assertTrue(s.capture(state, original(0)))
        self.assertFalse(s.capture(state, original(0)))

    def test_duplicate_original_id_refused(self):
        state = object(); s = Session(state)
        self.assertTrue(s.capture(state, original(0)))
        self.assertFalse(s.capture(state, replace(original(1), old=100, forward=100)))

    def test_inconsistent_root_refused(self):
        state = object(); s = Session(state)
        self.assertTrue(s.capture(state, original(0)))
        self.assertFalse(s.capture(state, replace(original(1), root=91)))

    def test_capture_after_complete_or_failure_does_not_read_maps(self):
        state, s = prepared(); count = s.map_reads
        self.assertFalse(s.capture(state, original(0)))
        self.assertEqual(s.map_reads, count)
        self.assertFalse(s.capture(state, original(1)))
        self.assertEqual(s.map_reads, count)

    def test_direct_subscription_flags_and_failures(self):
        for change in ({'flags': 1}, {'flags': 2}, {'flags': 4}, {'flags': False},
                       {'connect_ok': False}, {'root_guard_ok': False}):
            with self.subTest(change=change):
                state = object(); s = Session(state)
                self.assertFalse(s.capture(state, replace(original(0), **change)))

    def test_snapshot_precedes_each_subscription(self):
        _, s = prepared()
        for value in s.originals.values():
            self.assertLess(value['captured'], value['connected'])
        events = [event for _, event in s.log]
        self.assertLess(events.index('root snapshot'), events.index('root direct guard'))

    def test_early_event_latches_and_retires_identity(self):
        state = object(); s = Session(state)
        self.assertTrue(s.capture(state, original(0)))
        self.assertFalse(s.replace(0, 100, 200))
        self.assertIn(100, s.retired)
        self.assertFalse(s.finish(state, 90, finals()))
        self.assertNotIn(100, s.cleanup_ids({90, 100}))

    def test_replacement_type_identity_refusals(self):
        cases = ((False,100,200), (0.0,100,200), (18,100,200), (0,101,200),
                 (0,999,200), (0,100,0), (0,100,True), (0,100,200.0),
                 (0,100,90), (0,100,100), (0,100,101))
        for case in cases:
            with self.subTest(case=case):
                _, s = prepared()
                self.assertFalse(s.replace(*case))

    def test_invalid_replacement_refused(self):
        _, s = prepared()
        self.assertFalse(s.replace(0,100,200,live=False))

    def test_duplicate_edge_latches(self):
        _, s = prepared()
        self.assertTrue(s.replace(0,100,200))
        self.assertFalse(s.replace(0,100,201))

    def test_duplicate_new_identity_refused(self):
        _, s = prepared()
        self.assertTrue(s.replace(0,100,200))
        self.assertFalse(s.replace(1,101,200))

    def test_missing_edge_blocks_finish(self):
        state, s = prepared()
        for i in range(17): self.assertTrue(s.replace(i,100+i,200+i))
        self.assertFalse(s.finish(state,90,finals()))

    def test_missing_capture_blocks_first_edge(self):
        state = object(); s = Session(state)
        for i in range(17): self.assertTrue(s.capture(state,original(i)))
        self.assertFalse(s.replace(0,100,200))

    def test_root_guard_poison_is_terminal(self):
        state, s = prepared()
        self.assertFalse(s.root_replace())
        self.assertFalse(s.replace(0,100,200))
        self.assertFalse(s.finish(state,90,finals()))
        self.assertNotIn(90,s.cleanup_ids({90,100}))

    def test_external_diagnostic_latch_blocks_finalization(self):
        state, s = replaced()
        s.fail('fabricated engine diagnostic')
        self.assertFalse(s.finish(state,90,finals()))
        self.assertFalse(s.receipt()['complete'])

    def test_final_root_refusals(self):
        for change in ({'root':91}, {'root':True}, {'root_class':'MeshInstance3D'},
                       {'root_live':False}, {'parent':42}):
            with self.subTest(change=change):
                state, s = replaced(); args={'root':90};args.update(change)
                self.assertFalse(s.finish(state,finals=finals(),**args))

    def test_return_wrong_state_refused(self):
        _,s=replaced();self.assertFalse(s.finish(object(),90,finals()))

    def test_final_count_missing_extra_and_malformed(self):
        for rows in (finals()[:-1], finals()+[Final(18,218)], None, [None]*18):
            state,s=replaced();self.assertFalse(s.finish(state,90,rows))

    def test_final_identity_membership_and_class_refusals(self):
        for change in ({'identity':999}, {'identity':100}, {'identity':True}, {'identity':200.0},
                       {'index':False}, {'index':18}, {'live':False}, {'member':False},
                       {'native_class':'ImporterMeshInstance3D'}, {'script':object()}):
            with self.subTest(change=change):
                state,s=replaced();rows=finals();rows[0]=replace(rows[0],**change)
                self.assertFalse(s.finish(state,90,rows))

    def test_final_duplicate_index_refused(self):
        state,s=replaced();rows=finals();rows[1]=rows[0]
        self.assertFalse(s.finish(state,90,rows))

    def test_final_native_facts_mandatory_and_typed(self):
        state,s=replaced();rows=finals();rows[5]=replace(rows[5],metadata=object())
        self.assertFalse(s.finish(state,90,rows))
        self.assertEqual(len(s.finals),5)

    def test_repeated_return_refused(self):
        state,s=replaced();self.assertTrue(s.finish(state,90,finals()))
        self.assertFalse(s.finish(state,90,finals()))

    def test_late_event_revokes_component_complete(self):
        state,s=replaced();self.assertTrue(s.finish(state,90,finals()))
        self.assertFalse(s.replace(0,100,250))
        self.assertFalse(s.receipt()['complete'])

    def test_no_modeled_map_reads_after_capture(self):
        state,s=replaced();before=s.map_reads
        self.assertTrue(s.finish(state,90,finals()))
        self.assertEqual(before,s.map_reads)

    def test_cleanup_skips_all_retired_ids_even_if_reported_live(self):
        state,s=replaced();self.assertTrue(s.finish(state,90,finals()))
        self.assertEqual(s.cleanup_ids({90,*range(100,118)}),[90])

    def test_cleanup_before_return_refuses_and_poison(self):
        _,s=prepared();self.assertEqual(s.cleanup_ids({90,100}),[])
        self.assertEqual(s.phase,'FAILED')

    def test_cleanup_handles_missing_edges_without_acceptance(self):
        state,s=prepared();s.replace(0,100,200)
        self.assertFalse(s.finish(state,90,finals()))
        self.assertEqual(s.cleanup_ids({90,100,101}),[90,101])

    def test_detached_metadata_is_immune_to_input_mutation(self):
        data={'list':[1,2]};state=object();s=Session(state)
        self.assertTrue(s.capture(state,replace(original(0),metadata=data)))
        before=s.originals[0]['facts'];data['list'].append(3)
        self.assertEqual(before,s.originals[0]['facts'])
        self.assertIsNone(s.originals[0]['row'].metadata)

    def test_receipt_mutation_does_not_clear_fatal(self):
        s=Session(object());s.fail('failure');r=s.receipt();r['errors'].clear()
        self.assertEqual(len(s.errors),1)
        self.assertFalse(s.receipt()['complete'])


class MetadataControls(unittest.TestCase):
    def test_int_float_bool_remain_distinct(self):
        self.assertEqual(len({detached(1),detached(1.0),detached(True)}),3)

    def test_list_order_and_nested_dictionary(self):
        self.assertNotEqual(detached([1,2]),detached([2,1]))
        self.assertEqual(detached({'a':[None,True,1,1.5,'x']}),
                         detached({'a':[None,True,1,1.5,'x']}))

    def test_unsupported_metadata_is_not_stringified(self):
        for value in (object(),{1,2},b'bytes',(1,2),lambda:None):
            with self.subTest(kind=type(value).__name__),self.assertRaises(ValueError):detached(value)

    def test_nonfinite_refused(self):
        for value in (math.nan,math.inf,-math.inf):
            with self.assertRaises(ValueError):detached(value)

    def test_cycles_refused(self):
        row=[];row.append(row)
        with self.assertRaises(ValueError):detached(row)

    def test_limits_refused(self):
        with self.assertRaises(ValueError):detached([1,2],budget=[1])

    def test_budget_exhaustion_stops_visits(self):
        budget=[2]
        with self.assertRaises(ValueError):detached(list(range(10000)),budget=budget)
        self.assertEqual(budget,[-1])


class RegistryControls(unittest.TestCase):
    def test_exact_object_identity_not_equality(self):
        a={};b={};r=Registry();self.assertTrue(r.bind(a))
        self.assertIsNone(r.lookup(b));self.assertEqual(r.session.phase,'FAILED')

    def test_unknown_callback_without_active_session_is_terminal(self):
        r=Registry();self.assertIsNone(r.lookup(object()));self.assertFalse(r.bind(object()))

    def test_rebinding_and_concurrent_state_refused(self):
        state=object();r=Registry();self.assertTrue(r.bind(state))
        self.assertFalse(r.bind(state));self.assertFalse(r.bind(object()))

    def test_invalid_state_refused(self):
        r=Registry();self.assertFalse(r.bind(None));self.assertFalse(r.bind(object()))

    def test_registry_fault_survives_callback_error_handling(self):
        state=object();r=Registry();r.bind(state);r.poison('unknown callback')
        s=r.lookup(state);self.assertFalse(s.capture(state,original(0)))
        self.assertTrue(r.faults)


if __name__ == '__main__':
    unittest.main(verbosity=2)
