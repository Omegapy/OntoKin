"""Finite positive, refusal, partial-data and drift controls with fabricated values."""
from copy import deepcopy
import math
import random
import struct
import unittest

from inert_model import (Capture, EXPECTED_FORMAT, MAX_INDICES, MAX_RAW_BYTES,
                         MAX_VERTICES, MESHES, NodeView, Packed, Registry,
                         BYTE, FLOAT32, INT32, VECTOR3, synthetic_fixture)


class MeshCaptureControls(unittest.TestCase):
    def result(self, mutate=None):
        registry, state, root = synthetic_fixture()
        if mutate:
            mutate(registry, root)
        reader = Capture()
        return reader.capture(registry, state, root), reader, registry, root

    def refused(self, mutate):
        result, reader, registry, root = self.result(mutate)
        self.assertFalse(result['component_complete'])
        self.assertEqual(result['phase'], 'REFUSED')
        self.assertEqual(len(result['errors']), 1)
        self.assertFalse(result['execution_admission'])
        self.assertFalse(result['native_acceptance'])
        return result, reader, registry, root

    def test_complete_shared_resources_and_exact_associations(self):
        result, reader, registry, root = self.result()
        self.assertTrue(result['component_complete'])
        self.assertEqual(result['phase'], 'MESH_ARRAYS_CAPTURED_OTHER_RAW_PENDING')
        self.assertEqual(len(result['parts']), 18)
        self.assertEqual(reader.mesh_reads, 36)
        self.assertEqual(registry.close_calls, 1)
        self.assertEqual(len({p['snapshot']['mesh_instance_id'] for p in result['parts']}), 5)
        for i, row in enumerate(result['parts']):
            self.assertEqual((row['source_node'], row['source_mesh'], row['source_primitive']), (i, MESHES[i], 0))
            self.assertEqual((row['native_node_instance_id'], row['native_surface']), (200+i, 0))
            self.assertEqual(row['snapshot']['format'], EXPECTED_FORMAT)
            self.assertEqual(row['snapshot']['slot_types'], [36,36,32,0,0,0,0,0,0,0,0,0,30])
            self.assertEqual(row['snapshot']['slot_lengths'], [3,3,12,None,None,None,None,None,None,None,None,None,3])
        self.assertFalse(result['execution_admission'])
        self.assertFalse(result['native_acceptance'])
        self.assertEqual(result['R07'], 'PENDING')

    def test_traversal_permutations_do_not_change_source_identity(self):
        for seed in range(18):
            with self.subTest(seed=seed):
                result, *_ = self.result(lambda g,r: random.Random(seed).shuffle(r.children))
                self.assertTrue(result['component_complete'])
                self.assertEqual([row['native_node_instance_id'] for row in result['parts']], list(range(200,218)))

    def test_raw_values_are_not_normalized_flipped_or_source_filled(self):
        result, *_ = self.result()
        snap = result['parts'][0]['snapshot']
        self.assertEqual(snap['normals'].values, [(0.0,0.0,0.5)]*3)
        self.assertEqual(snap['indices'].values, [0,2,1])
        self.assertEqual(snap['auxiliary_tangents'].values, [0.0,1.0,0.0,-1.0]*3)
        self.assertEqual(struct.pack('>d', snap['positions'].values[0][1]), struct.pack('>d', -0.0))

    def test_detached_results_do_not_mutate_native_model_or_other_parts(self):
        result, reader, registry, root = self.result()
        result['parts'][2]['snapshot']['positions'].values[0] = (99.0,99.0,99.0)
        self.assertNotEqual(result['parts'][2]['snapshot']['positions'].values,
                            result['parts'][4]['snapshot']['positions'].values)
        self.assertNotEqual(result['parts'][2]['snapshot']['positions'].values, root.children[2].mesh.arrays[0].values)
        result['chain']['errors'].append('fake')
        self.assertEqual(registry.chain['errors'], [])

    def test_single_use_failure_is_terminal(self):
        registry, state, root = synthetic_fixture(); reader=Capture()
        self.assertTrue(reader.capture(registry,state,root)['component_complete'])
        self.assertFalse(reader.capture(registry,state,root)['component_complete'])
        self.assertFalse(reader.capture(registry,state,root)['component_complete'])
        self.assertEqual(registry.close_calls,1)

    def test_wrong_state_before_native_reads(self):
        registry,state,root=synthetic_fixture(); reader=Capture()
        result=reader.capture(registry,object(),root)
        self.assertFalse(result['component_complete'])
        self.assertEqual((reader.scene_reads,reader.mesh_reads),(0,0))

    def test_no_retry_from_second_reader_after_consumed_receipt(self):
        registry,state,root=synthetic_fixture()
        self.assertTrue(Capture().capture(registry,state,root)['component_complete'])
        reader=Capture(); result=reader.capture(registry,state,root)
        self.assertFalse(result['component_complete']); self.assertEqual(reader.scene_reads,0)

    def test_unfinished_or_poisoned_chain_before_native_reads(self):
        for field,value in [('component_complete',False),('phase','CAPTURING'),('state_id',0),('errors',['fault'])]:
            with self.subTest(field=field):
                _,reader,_,_=self.refused(lambda g,r: g.chain.__setitem__(field,value))
                self.assertEqual(reader.mesh_reads,0)
        _,reader,_,_=self.refused(lambda g,r: g.faults.append('fault'))
        self.assertEqual(reader.scene_reads,0)

    def test_root_identity_class_parent_and_script_refused(self):
        for field,value in [('identity',91),('native_class','MeshInstance3D'),('parent',object()),('script',object()),('alive',False)]:
            with self.subTest(field=field):self.refused(lambda g,r:setattr(r,field,value))

    def test_missing_extra_retired_duplicate_and_unconverted_members(self):
        for action in [lambda g,r:r.children.pop(),
                       lambda g,r:r.children.append(NodeView(999,mesh=r.children[0].mesh)),
                       lambda g,r:r.children.append(r.children[0]),
                       lambda g,r:setattr(r.children[0],'identity',100),
                       lambda g,r:setattr(r.children[0],'native_class','ImporterMeshInstance3D'),
                       lambda g,r:setattr(r.children[0],'native_class','CustomMeshInstance3D'),
                       lambda g,r:setattr(r.children[0],'script',object()),
                       lambda g,r:setattr(r.children[0],'alive',False)]:
            with self.subTest(action=action):self.refused(action)

    def test_nested_members_remain_mapped(self):
        def move(g,r):
            group=NodeView(700,native_class='Node3D',children=r.children[:],parent=r)
            r.children=[group]
        result,*_=self.result(move)
        self.assertTrue(result['component_complete'])

    def test_scene_cycle_and_limit_refused(self):
        self.refused(lambda g,r:r.children.append(r))
        self.refused(lambda g,r:r.children.extend(NodeView(700+i,native_class='Node3D') for i in range(65)))

    def test_chain_cross_index_or_duplicate_association_refused(self):
        for section,field,value in [('originals','mesh',4),('edges','old',101),('edges','new',201),('finals','new',201)]:
            with self.subTest(section=section,field=field):
                self.refused(lambda g,r:g.chain[section][0].__setitem__(field,value))

    def test_resource_identity_class_script_and_missing_refused(self):
        for field,value in [('identity',9999),('native_class','PrimitiveMesh'),('script',object()),('alive',False)]:
            with self.subTest(field=field):self.refused(lambda g,r:setattr(r.children[0].mesh,field,value))
        self.refused(lambda g,r:setattr(r.children[0],'mesh',None))

    def test_missing_duplicate_or_wrong_final_resource_fact_refused(self):
        self.refused(lambda g,r:g.chain['finals'][0]['native']['resource_bindings'].clear())
        self.refused(lambda g,r:g.chain['finals'][0]['native']['resource_bindings'].append(deepcopy(g.chain['finals'][0]['native']['resource_bindings'][0])))
        self.refused(lambda g,r:g.chain['finals'][0]['native']['resource_bindings'][0]['resource'].__setitem__('class','Mesh'))

    def test_one_surface_and_no_blends_or_shadow(self):
        for field,value in [('surface_count',0),('surface_count',2),('blend_shape_count',1),('shadow_mesh',object())]:
            with self.subTest(field=field,value=value):self.refused(lambda g,r:setattr(r.children[0].mesh,field,value))

    def test_unsupported_format_bits_and_versions_refused(self):
        for bit in [0,1,2,3,4,10,12,25,26,27,28,29,34,35,36,44,62]:
            with self.subTest(bit=bit):self.refused(lambda g,r:setattr(r.children[0].mesh,'format',EXPECTED_FORMAT^(1<<bit)))

    def test_primitive_modes_refused(self):
        for mode in [0,1,2,4,5,-1]:
            with self.subTest(mode=mode):self.refused(lambda g,r:setattr(r.children[0].mesh,'primitive',mode))

    def test_count_bounds_before_raw_copy(self):
        for field,value in [('vertices',0),('vertices',MAX_VERTICES+1),('indices',0),('indices',MAX_INDICES+3),('indices',4)]:
            with self.subTest(field=field,value=value):
                result,*_=self.refused(lambda g,r:setattr(r.children[0].mesh,field,value))
                self.assertNotIn('vertex_data',result['parts'][0]['snapshot'])

    def test_raw_missing_type_and_descriptor_disagreement(self):
        for key in ['vertex_data','index_data','format','primitive','vertex_count','index_count']:
            with self.subTest(key=key):self.refused(lambda g,r:r.children[0].mesh.raw.pop(key))
        for key in ['format','primitive','vertex_count','index_count']:
            with self.subTest(key=key):self.refused(lambda g,r:r.children[0].mesh.raw.__setitem__(key,False))
        for key in ['format','primitive','vertex_count','index_count']:
            with self.subTest(key=key):self.refused(lambda g,r:r.children[0].mesh.raw.__setitem__(key,1))

    def test_raw_unknown_or_unsupported_fields_refused_with_inventory(self):
        for key in ['mystery','attribute_data','skin_data','lods','bone_aabbs','blend_shape_data']:
            with self.subTest(key=key):
                result,*_=self.refused(lambda g,r:r.children[0].mesh.raw.__setitem__(key,[]))
                self.assertIn(key,[x['key'] for x in result['parts'][0]['snapshot']['raw_surface_field_types']])

    def test_raw_buffer_types_empty_and_size_bound(self):
        for value in [None,Packed(INT32,[1]),Packed(BYTE,b''),Packed(BYTE,b'x'*(MAX_RAW_BYTES+1))]:
            with self.subTest(kind=type(value).__name__):self.refused(lambda g,r:r.children[0].mesh.raw.__setitem__('vertex_data',value))

    def test_wrong_slot_count_preserves_actual_lengths(self):
        result,*_=self.refused(lambda g,r:r.children[0].mesh.arrays.pop())
        self.assertEqual(result['parts'][0]['snapshot']['array_count'],12)
        self.assertEqual(result['parts'][0]['snapshot']['slot_lengths'][:3],[3,3,12])
        self.assertIn('positions',result['parts'][0]['snapshot'])

    def test_absent_or_wrong_packed_types_preserve_other_values(self):
        for slot in [0,1,2,12]:
            with self.subTest(slot=slot):
                result,*_=self.refused(lambda g,r:r.children[0].mesh.arrays.__setitem__(slot,None))
                self.assertEqual(result['parts'][0]['snapshot']['slot_types'][slot],0)
                if slot!=0:self.assertIn('positions',result['parts'][0]['snapshot'])
        self.refused(lambda g,r:r.children[0].mesh.arrays.__setitem__(0,Packed(FLOAT32,[0.0]*3)))

    def test_extra_channel_refused_without_dropping_required_arrays(self):
        result,*_=self.refused(lambda g,r:r.children[0].mesh.arrays.__setitem__(4,Packed(FLOAT32,[1.0]*3)))
        self.assertIn('indices',result['parts'][0]['snapshot'])

    def test_mismatched_lengths_preserve_values_and_lengths(self):
        for slot in [0,1,2,12]:
            with self.subTest(slot=slot):
                result,*_=self.refused(lambda g,r:r.children[0].mesh.arrays[slot].values.pop())
                snap=result['parts'][0]['snapshot']
                self.assertEqual(snap['slot_lengths'][slot],2 if slot!=2 else 11)
                self.assertIn('positions',snap);self.assertIn('indices',snap)

    def test_slot_bound_preserves_length_without_excess_copy(self):
        result,*_=self.refused(lambda g,r:setattr(r.children[0].mesh.arrays[0],'values',[(0.0,0.0,0.0)]*(MAX_VERTICES+1)))
        self.assertEqual(result['parts'][0]['snapshot']['slot_lengths'][0],MAX_VERTICES+1)
        self.assertNotIn('positions',result['parts'][0]['snapshot'])
        self.assertEqual(result['parts'][0]['snapshot']['omitted'][0]['count'],MAX_VERTICES+1)

    def test_nonfinite_vector_tangent_and_index_range_refused(self):
        for value in [math.nan,math.inf,-math.inf]:
            for slot in [0,1]:
                with self.subTest(value=value,slot=slot):self.refused(lambda g,r:r.children[0].mesh.arrays[slot].values.__setitem__(0,(value,0.0,0.0)))
            self.refused(lambda g,r:r.children[0].mesh.arrays[2].values.__setitem__(0,value))
        for value in [-1,3,2**31]:
            with self.subTest(value=value):self.refused(lambda g,r:r.children[0].mesh.arrays[12].values.__setitem__(0,value))

    def test_failure_keeps_successful_and_current_partial_rows(self):
        result,*_=self.refused(lambda g,r:setattr(r.children[5].mesh,'primitive',4))
        self.assertEqual(len(result['parts']),6)
        self.assertIn('positions',result['parts'][4]['snapshot'])
        self.assertEqual(result['parts'][5]['snapshot']['primitive_type'],4)

    def test_same_count_vertex_buffer_mutation_detected(self):
        def setup(g,r):
            def mutate(m):
                if m.reads==2:m.raw['vertex_data'].values=b'z'*60
            r.children[0].mesh.mutate_at=mutate
        result,*_=self.refused(setup)
        self.assertIn('after_drift',result['parts'][0])
        self.assertNotEqual(result['parts'][0]['snapshot']['vertex_data'],result['parts'][0]['after_drift']['vertex_data'])

    def test_same_count_api_value_mutation_detected(self):
        def setup(g,r):
            def mutate(m):
                if m.reads==2:m.arrays[1].values[0]=(0.0,0.0,0.25)
            r.children[0].mesh.mutate_at=mutate
        self.refused(setup)

    def test_resource_swap_during_capture_refused(self):
        def setup(g,r):
            def mutate(m):
                if m.reads==2:r.children[1].mesh=r.children[0].mesh
            r.children[0].mesh.mutate_at=mutate
        self.refused(setup)

    def test_membership_or_registry_drift_at_final_phase_refused(self):
        for change in [lambda g,r:r.children.pop(),lambda g,r:g.faults.append('late error')]:
            def setup(g,r):
                def mutate(m):
                    if m.reads==2:change(g,r)
                r.children[0].mesh.mutate_at=mutate
            with self.subTest(change=change):self.refused(setup)

    def test_native_source_expected_shape_not_required(self):
        # These synthetic three-vertex surfaces intentionally differ from the real fixture.
        result,*_=self.result()
        self.assertTrue(result['component_complete'])
        self.assertEqual(result['parts'][0]['snapshot']['vertex_count'],3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
