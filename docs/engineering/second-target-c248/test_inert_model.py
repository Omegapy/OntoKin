"""C248 finite synthetic controls, including actual composition with C247's CPU model."""
from copy import deepcopy
import math
import random
import struct
import unittest

from inert_model import (Capture, ColorValue, MaterialView, ResourceView, MESHES,
                         MATERIAL_BY_MESH, SETTINGS, c247, synthetic_fixture)


class MaterialControls(unittest.TestCase):
    def result(self, mutate=None):
        registry,state,root=synthetic_fixture()
        if mutate:mutate(registry,root)
        capture=Capture()
        return capture.capture(registry,state,root),capture,registry,root

    def refused(self,mutate):
        result,capture,registry,root=self.result(mutate)
        self.assertFalse(result['component_complete']);self.assertEqual(result['phase'],'REFUSED')
        self.assertEqual(len(result['errors']),1)
        self.assertFalse(result['execution_admission']);self.assertFalse(result['native_acceptance'])
        self.assertEqual(result['R07'],'PENDING')
        return result,capture,registry,root

    def test_complete_18_parts_two_shared_materials_and_no_admission(self):
        result,capture,registry,root=self.result()
        self.assertTrue(result['component_complete']);self.assertEqual(len(result['parts']),18)
        self.assertEqual(result['phase'],'MATERIAL_PARAMETERS_CAPTURED_OTHER_RAW_PENDING')
        self.assertEqual(result['native_material_count'],2)
        self.assertEqual((capture.mesh_calls,capture.material_reads,registry.close_calls),(1,36,1))
        self.assertTrue(result['mesh_arrays']['component_complete'])
        self.assertFalse(result['execution_admission']);self.assertFalse(result['native_acceptance'])
        self.assertEqual(result['R07'],'PENDING')
        for i,row in enumerate(result['parts']):
            self.assertEqual((row['source_node'],row['source_mesh'],row['source_primitive'],row['source_material']),
                             (i,MESHES[i],0,MATERIAL_BY_MESH[MESHES[i]]))
            self.assertEqual((row['native_node_instance_id'],row['native_surface']),(200+i,0))
            material=row['snapshot']['material']
            self.assertEqual(material['identity']['instance_id'],5000+row['source_material'])
            self.assertEqual((len(material['features']),len(material['flags']),len(material['textures'])),(13,25,19))
            self.assertEqual(material['raw']['albedo_color']['type'],20)
            self.assertEqual(material['raw']['metallic']['type'],3)

    def test_traversal_order_does_not_replace_observed_identity(self):
        for seed in range(18):
            with self.subTest(seed=seed):
                result,*_=self.result(lambda g,r:random.Random(seed).shuffle(r.children))
                self.assertTrue(result['component_complete'])
                self.assertEqual([x['source_node'] for x in result['parts']],list(range(18)))

    def test_raw_values_and_alpha_are_not_converted_or_filled(self):
        def change(g,r):r.children[0].mesh.surface_material.color=ColorValue(-0.0,0.123456789,0.875,0.3125)
        result,*_=self.result(change)
        self.assertTrue(result['component_complete'])
        raw=result['parts'][0]['snapshot']['material']['raw']
        self.assertEqual(raw['components']['g']['value'],0.123456789)
        self.assertEqual(raw['components']['alpha']['value'],0.3125)
        self.assertEqual(struct.pack('>d',raw['components']['r']['value']),struct.pack('>d',-0.0))
        self.assertEqual(raw['metallic']['value'],0.25)
        self.assertEqual(raw['roughness']['value'],0.75)

    def test_known_wrong_modes_remain_raw_without_comparison(self):
        for cull in [0,1,2]:
            for transparency in [0,1,2]:
                def change(g,r):
                    m=r.children[0].mesh.surface_material;m.cull=cull;m.transparency=transparency
                with self.subTest(cull=cull,transparency=transparency):
                    result,*_=self.result(change)
                    self.assertTrue(result['component_complete'])
                    raw=result['parts'][0]['snapshot']['material']['raw']
                    self.assertEqual(raw['cull_mode']['value'],cull)
                    self.assertEqual(raw['transparency_mode']['value'],transparency)

    def test_distinct_material_copies_for_same_source_are_allowed(self):
        def copies(g,r):
            for i,node in enumerate(r.children):
                mesh=deepcopy(node.mesh);mesh.identity=2000+i;mesh.surface_material.identity=7000+i
                # Deliberately different represented values; later comparison owns equality.
                mesh.surface_material.roughness=(i+1)/20.0
                node.mesh=mesh
                g.chain['finals'][i]['native']['resource_bindings'][0]['resource']['instance_id']=mesh.identity
        result,*_=self.result(copies)
        self.assertTrue(result['component_complete']);self.assertEqual(result['native_material_count'],18)

    def test_one_material_cannot_claim_two_source_indices(self):
        result,*_=self.refused(lambda g,r:setattr(r.children[0].mesh,'surface_material',r.children[2].mesh.surface_material))
        self.assertIn('conflicting material sharing',result['errors'][0])

    def test_same_native_id_cannot_have_inconsistent_raw_values(self):
        def change(g,r):
            def drift(m):
                if m.reads==2:m.roughness=0.5
            r.children[0].mesh.surface_material.mutate_at=drift
        result,*_=self.refused(change)
        self.assertEqual(len(result['parts']),2)
        self.assertEqual(result['parts'][0]['snapshot']['material']['raw']['roughness']['value'],0.75)
        self.assertEqual(result['parts'][1]['snapshot']['material']['raw']['roughness']['value'],0.5)

    def test_detached_material_rows_and_mesh_arrays(self):
        result,capture,registry,root=self.result()
        result['parts'][0]['snapshot']['material']['raw']['components']['alpha']['value']=0.0
        self.assertEqual(result['parts'][1]['snapshot']['material']['raw']['components']['alpha']['value'],1.0)
        self.assertEqual(root.children[0].mesh.surface_material.color.a,1.0)
        result['mesh_arrays']['parts'][0]['snapshot']['indices'].values[0]=1
        self.assertEqual(root.children[0].mesh.arrays[12].values[0],0)

    def test_c248_calls_c247_once_and_repeated_use_never_recloses(self):
        registry,state,root=synthetic_fixture();capture=Capture()
        self.assertTrue(capture.capture(registry,state,root)['component_complete'])
        self.assertFalse(capture.capture(registry,state,root)['component_complete'])
        self.assertFalse(capture.capture(registry,state,root)['component_complete'])
        self.assertEqual((capture.mesh_calls,registry.close_calls),(1,1))

    def test_preconsumed_c247_receipt_does_not_admit_materials(self):
        registry,state,root=synthetic_fixture()
        self.assertTrue(c247.Capture().capture(registry,state,root)['component_complete'])
        capture=Capture();result=capture.capture(registry,state,root)
        self.assertFalse(result['component_complete']);self.assertEqual(capture.material_reads,0)
        self.assertFalse(result['mesh_arrays']['component_complete'])

    def test_wrong_state_or_incomplete_chain_stops_before_material_getters(self):
        registry,state,root=synthetic_fixture();capture=Capture()
        self.assertFalse(capture.capture(registry,object(),root)['component_complete'])
        self.assertEqual(capture.material_reads,0)
        result,capture,*_=self.refused(lambda g,r:g.chain.__setitem__('component_complete',False))
        self.assertEqual(capture.material_reads,0)
        self.assertEqual(result['parts'],[])

    def test_inner_mesh_failure_is_preserved(self):
        result,capture,*_=self.refused(lambda g,r:setattr(r.children[0].mesh,'primitive',4))
        self.assertEqual(capture.material_reads,0)
        self.assertIn('snapshot',result['mesh_arrays']['parts'][0])
        self.assertEqual(result['mesh_arrays']['parts'][0]['snapshot']['primitive_type'],4)

    def test_final_node_membership_and_script_checks_are_composed(self):
        for mutate in [lambda g,r:r.children.pop(),lambda g,r:setattr(r.children[0],'identity',100),
                       lambda g,r:setattr(r.children[0],'script',ResourceView(9,'GDScript')),
                       lambda g,r:r.children.append(r)]:
            with self.subTest(mutate=mutate):
                _,capture,*_=self.refused(mutate);self.assertEqual(capture.material_reads,0)

    def test_overrides_and_overlay_preserve_selector_ids_then_refuse(self):
        for field,key in [('material_override','node_override'),('surface_override','surface_override'),('material_overlay','overlay')]:
            with self.subTest(field=field):
                result,capture,*_=self.refused(lambda g,r:setattr(r.children[0],field,MaterialView(8000)))
                snap=result['parts'][0]['snapshot']
                self.assertEqual(snap['selection'][key]['instance_id'],8000)
                self.assertIn('omitted',snap);self.assertEqual(capture.material_reads,0)

    def test_active_material_null_or_disagreement_refused(self):
        for value in [None,MaterialView(8001)]:
            def change(g,r):r.children[0].override_active=True;r.children[0].active_override=value
            with self.subTest(value=value):self.refused(change)

    def test_surface_override_count_refused(self):
        for value in [0,2]:
            with self.subTest(value=value):self.refused(lambda g,r:setattr(r.children[0],'surface_override_count',value))

    def test_instance_transparency_raw_value_kept_on_refusal(self):
        for value in [0.01,1.0,math.nan,False,0]:
            with self.subTest(value=value):
                result,*_=self.refused(lambda g,r:setattr(r.children[0],'instance_transparency',value))
                self.assertIn('instance_transparency',result['parts'][0]['snapshot'])

    def test_missing_shader_orm_or_scripted_material_refused(self):
        self.refused(lambda g,r:setattr(r.children[0].mesh,'surface_material',None))
        for native_class in ['ShaderMaterial','ORMMaterial3D','BaseMaterial3D','PlaceholderMaterial']:
            with self.subTest(native_class=native_class):self.refused(lambda g,r:setattr(r.children[0].mesh.surface_material,'native_class',native_class))
        self.refused(lambda g,r:setattr(r.children[0].mesh.surface_material,'script',ResourceView(8002,'GDScript')))

    def test_recorded_script_cannot_be_excused_by_later_null_getter(self):
        def change(g,r):
            r.children[0].mesh.surface_material.field_sequences['script']=[ResourceView(8003,'GDScript'),None]
        result,capture,_,root=self.refused(change)
        mat=root.children[0].mesh.surface_material
        self.assertEqual(mat.field_read_counts['script'],1)
        self.assertEqual(result['parts'][0]['snapshot']['material']['script']['instance_id'],8003)
        self.assertEqual(capture.material_reads,0)

    def test_recorded_next_pass_cannot_be_excused_by_later_null_getter(self):
        def change(g,r):
            r.children[0].mesh.surface_material.field_sequences['next_pass']=[MaterialView(8004),None]
        result,_,_,root=self.refused(change)
        self.assertEqual(root.children[0].mesh.surface_material.field_read_counts['next_pass'],1)
        self.assertEqual(result['parts'][0]['snapshot']['material']['next_pass']['instance_id'],8004)
        self.assertIn('omitted',result['parts'][0]['snapshot']['material'])

    def test_next_pass_cycle_is_recorded_without_traversal(self):
        def change(g,r):m=r.children[0].mesh.surface_material;m.next_pass=m
        result,*_=self.refused(change)
        material=result['parts'][0]['snapshot']['material']
        self.assertEqual(material['next_pass'],material['identity'])
        self.assertEqual(material['omitted'][0]['field'],'next_pass payload')

    def test_every_additional_feature_refused_with_raw_inventory(self):
        for i in range(13):
            with self.subTest(feature=i):
                result,*_=self.refused(lambda g,r:r.children[0].mesh.surface_material.features.__setitem__(i,True))
                material=result['parts'][0]['snapshot']['material']
                self.assertEqual(len(material['features']),13)
                self.assertIs(material['features'][i]['raw']['value'],True)

    def test_every_flag_change_refused(self):
        for i in range(25):
            with self.subTest(flag=i):self.refused(lambda g,r:r.children[0].mesh.surface_material.flags.__setitem__(i,i!=16))

    def test_every_texture_slot_refused_with_identity_and_payload_omission(self):
        for i in range(19):
            with self.subTest(texture=i):
                result,*_=self.refused(lambda g,r:r.children[0].mesh.surface_material.textures.__setitem__(i,ResourceView(9000+i)))
                material=result['parts'][0]['snapshot']['material']
                self.assertEqual(material['textures'][i]['identity']['instance_id'],9000+i)
                self.assertEqual(material['omitted'][0]['index'],i)

    def test_fixed_inventory_counts_bound_traversal(self):
        for field in ['features','flags','textures']:
            with self.subTest(field=field):
                result,*_=self.refused(lambda g,r:getattr(r.children[0].mesh.surface_material,field).append(None))
                material=result['parts'][0]['snapshot']['material']
                self.assertIn('omitted',material)
                self.assertEqual(material['features'],[])
                self.assertEqual(material['enum_counts'][field],{'features':14,'flags':26,'textures':20}[field])

    def test_known_guard_settings_type_and_value_refused(self):
        for name,default in SETTINGS.items():
            value=not default if type(default) is bool else default+1
            with self.subTest(name=name):self.refused(lambda g,r:r.children[0].mesh.surface_material.settings.__setitem__(name,value))
        self.refused(lambda g,r:r.children[0].mesh.surface_material.settings.__setitem__('metallic_specular',False))
        self.refused(lambda g,r:r.children[0].mesh.surface_material.settings.pop('depth_test'))

    def test_invalid_raw_color_type_and_components_are_not_repaired(self):
        self.refused(lambda g,r:setattr(r.children[0].mesh.surface_material,'color',[0.0,0.0,0.0,1.0]))
        for name in ['r','g','b','a']:
            for value in [math.nan,math.inf,-math.inf,-0.01,1.01,True,1]:
                with self.subTest(name=name,value=value):self.refused(lambda g,r:setattr(r.children[0].mesh.surface_material.color,name,value))

    def test_invalid_metallic_roughness_and_modes_are_retained(self):
        for name in ['metallic','roughness']:
            for value in [math.nan,math.inf,-1.0,1.1,True,0]:
                with self.subTest(name=name,value=value):
                    result,*_=self.refused(lambda g,r:setattr(r.children[0].mesh.surface_material,name,value))
                    self.assertIn(name,result['parts'][0]['snapshot']['material']['raw'])
        for name in ['cull','transparency']:
            for value in [-1,3,4,5,False,0.0]:
                with self.subTest(name=name,value=value):self.refused(lambda g,r:setattr(r.children[0].mesh.surface_material,name,value))

    def test_valid_unit_bounds_remain_observations(self):
        for value in [0.0,1.0]:
            def change(g,r):
                m=r.children[0].mesh.surface_material;m.color=ColorValue(value,value,value,value);m.metallic=value;m.roughness=value
            with self.subTest(value=value):self.assertTrue(self.result(change)[0]['component_complete'])

    def test_feature_boolean_types_cannot_be_numeric_aliases(self):
        self.refused(lambda g,r:r.children[0].mesh.surface_material.features.__setitem__(0,0))
        self.refused(lambda g,r:r.children[0].mesh.surface_material.flags.__setitem__(16,1))

    def test_second_read_value_drift_retains_before_after(self):
        def change(g,r):
            def drift(m):
                if m.reads==3:m.color.a=0.5
            r.children[0].mesh.surface_material.mutate_at=drift
        result,*_=self.refused(change)
        before=result['parts'][0]['snapshot']['material']['raw']['components']['alpha']['value']
        after=result['parts'][0]['after_drift']['material']['raw']['components']['alpha']['value']
        self.assertEqual((before,after),(1.0,0.5))

    def test_second_read_resource_selection_drift_refused(self):
        def change(g,r):
            def drift(m):
                if m.reads==3:r.children[1].mesh.surface_material=MaterialView(7777)
            r.children[0].mesh.surface_material.mutate_at=drift
        result,*_=self.refused(change)
        self.assertIn('after_drift',result['parts'][1])

    def test_late_scene_or_registry_fault_refuses(self):
        for change in [lambda g,r:r.children.pop(),lambda g,r:g.faults.append('late fault')]:
            def install(g,r):
                def drift(m):
                    if m.reads==3:change(g,r)
                r.children[0].mesh.surface_material.mutate_at=drift
            with self.subTest(change=change):self.refused(install)

    def test_partial_current_material_survives_refusal(self):
        def change(g,r):r.children[2].mesh.surface_material.metallic=math.nan
        result,*_=self.refused(change)
        self.assertEqual(len(result['parts']),3)
        self.assertEqual(result['parts'][1]['snapshot']['material']['raw']['metallic']['value'],0.25)
        self.assertTrue(math.isnan(result['parts'][2]['snapshot']['material']['raw']['metallic']['value']))
        self.assertEqual(len(result['parts'][2]['snapshot']['material']['textures']),19)


if __name__=='__main__':unittest.main(verbosity=2)
