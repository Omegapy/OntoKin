"""Adversarial C249 author controls over fabricated getters and resolver results."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

_SPEC=importlib.util.spec_from_file_location('ontokin_c249_model_tests',Path(__file__).with_name('inert_model.py'))
m=importlib.util.module_from_spec(_SPEC);sys.modules[_SPEC.name]=m;_SPEC.loader.exec_module(m)


class InventoryTests(unittest.TestCase):
    def setup_fixture(self):
        registry,state,root=m.synthetic_fixture();player,library,animation=m.fixture_objects(root)
        return registry,state,root,player,library,animation

    def run_case(self,change=None,ok=False):
        r,s,root,p,l,a=self.setup_fixture()
        if change:change(root,p,l,a,r)
        capture=m.Capture();out=capture.capture(r,s,root)
        self.assertEqual(out['component_complete'],ok,out.get('errors'))
        self.assertFalse(out['native_acceptance']);self.assertFalse(out['execution_admission']);self.assertEqual(out['R07'],'PENDING')
        self.assertEqual(capture.material_calls,1);self.assertEqual(r.close_calls,1)
        self.assertIn('materials',out)
        if not ok:self.assertEqual(out['phase'],'REFUSED');self.assertTrue(out['errors'])
        return out,capture,(r,s,root,p,l,a)

    def test_complete_preserves_chain_and_36_targets(self):
        out,c,items=self.run_case(ok=True)
        self.assertEqual(out['phase'],'ANIMATION_INVENTORY_CAPTURED_POSES_PENDING')
        self.assertEqual(out['inventory'],out['recheck']);self.assertEqual(c.inventory_reads,2)
        rows=out['inventory']['tracks'];self.assertEqual({(r['source_node'],r['type']['value']) for r in rows},{(i,k) for i in range(18) for k in (1,2)})
        self.assertEqual(out['materials']['mesh_arrays']['chain']['component_complete'],True)
        self.assertEqual(items[3].root_lookup_reads,2)

    def test_arbitrary_names_and_track_order_are_not_identity(self):
        def edit(root,p,l,a,r):
            root.children.reverse();a.tracks.reverse();p.name=m.Name('Renamed player');a.name='Unrelated descriptive resource name'
            a2=l.animations.pop(next(iter(l.animations)));l.animations[m.Name('Renamed key')]=a2
        out,_,_=self.run_case(edit,ok=True)
        self.assertEqual(out['inventory']['tracks'][0]['source_node'],17)

    def test_alias_path_routes_to_actual_identity(self):
        def edit(root,p,l,a,r):
            root.resolve_map['actual-route-alias']=root.children[0]
            a.tracks[0].path=m.PathValue('actual-route-alias')
        out,_,_=self.run_case(edit,ok=True);self.assertEqual(out['inventory']['tracks'][0]['source_node'],0)

    def test_detached_receipt_cannot_mutate_reader(self):
        out,c,_=self.run_case(ok=True);out['inventory']['tracks'].clear();self.assertEqual(len(c.result['inventory']['tracks']),36)

    def test_reader_single_use_does_not_reconsume(self):
        _,c,(r,s,root,*_)=self.run_case(ok=True);out=c.capture(r,s,root)
        self.assertFalse(out['component_complete']);self.assertEqual(r.close_calls,1);self.assertEqual(c.material_calls,1)

    def test_preconsumed_state_refuses_without_retry(self):
        r,s,root,*_=self.setup_fixture();m.c248.Capture().capture(r,s,root)
        out=m.Capture().capture(r,s,root);self.assertFalse(out['component_complete']);self.assertEqual(r.close_calls,2)
        self.assertNotIn('inventory',out)

    def test_wrong_state_refusal_retains_owned_partial_receipt(self):
        r,s,root,*_=self.setup_fixture();out=m.Capture().capture(r,object(),root)
        self.assertFalse(out['component_complete']);self.assertIn('materials',out);self.assertNotIn('inventory',out)

    def test_prior_material_failure_is_preserved(self):
        out,_,_=self.run_case(lambda root,p,l,a,r:setattr(root.children[0],'material_overlay',m.c248.ResourceView(9001,'Material')))
        self.assertNotIn('inventory',out);self.assertIn('parts',out['materials'])

    def test_missing_and_extra_players(self):
        for extra in (False,True):
            def edit(root,p,l,a,r):
                if extra:
                    n=m.c247.NodeView(9900,'AnimationPlayer',parent=root);root.children.append(n)
                else:root.children.remove(p)
            with self.subTest(extra=extra):self.run_case(edit)

    def test_extra_mixer_and_other_scene_members(self):
        for kind in ('AnimationMixer','AnimationTree','Node3D','CustomAnimationPlayer'):
            with self.subTest(kind=kind):self.run_case(lambda root,p,l,a,r:root.children.append(m.c247.NodeView(9900,kind,parent=root)))

    def test_queued_nodes(self):
        for index in (0,5,18):
            with self.subTest(index=index):self.run_case(lambda root,p,l,a,r:setattr(root.children[index],'queued',True))

    def test_attached_tree_refuses(self):
        self.run_case(lambda root,p,l,a,r:setattr(root,'inside_tree',True))

    def test_scripted_player_refuses(self):
        self.run_case(lambda root,p,l,a,r:setattr(p,'script',m.ResourceView(9901,'Script')))

    def test_root_path_refused_before_lookup_f01(self):
        for path in (m.PathValue('/root',True),m.PathValue(''),m.PathValue('..:resource',False,1)):
            out,_,items=self.run_case(lambda root,p,l,a,r:setattr(p,'root_path',path))
            self.assertEqual(items[3].root_lookup_reads,0);self.assertNotIn('root_target',out['inventory']['player'])
            self.assertIn('omitted',out['inventory']['player'])

    def test_root_target_must_be_owned_root(self):
        self.run_case(lambda root,p,l,a,r:setattr(p,'root_target',root.children[0]))

    def test_playback_state_rejected(self):
        changes={'playing':True,'has_section':True,'autoplay':m.Name('run'),'assigned_animation':m.Name('run'),
                 'current_animation':m.Name('run'),'queue':[m.Name('run')]}
        for k,v in changes.items():
            with self.subTest(field=k):self.run_case(lambda root,p,l,a,r:p.settings.update({k:v}))

    def test_malformed_settings_preserve_refusal_f02(self):
        for key,value in (("speed_scale",float("nan")),("default_blend_time",float("inf")),("queue",[object()])):
            out,_,_=self.run_case(lambda root,p,l,a,r:p.settings.update({key:value}))
            self.assertIn(key,out["inventory"]["player"]["settings"])

    def test_nonbaseline_modes_rejected(self):
        changes={'active':False,'callback_mode_process':2,'callback_mode_method':1,'callback_mode_discrete':2,'deterministic':True,
                 'root_motion_track':m.PathValue('native_0'),'root_motion_local':True,'speed_scale':2.0,'default_blend_time':0.2,'auto_capture':False}
        for k,v in changes.items():
            with self.subTest(field=k):self.run_case(lambda root,p,l,a,r:p.settings.update({k:v}))

    def test_library_cardinality_and_default_key(self):
        for mode in ('none','extra','nondefault'):
            def edit(root,p,l,a,r):
                if mode=='none':p.libraries.clear()
                elif mode=='extra':p.libraries[m.Name('other')]=l
                else:p.libraries={m.Name('nondefault'):l}
            with self.subTest(mode=mode):self.run_case(edit)

    def test_animation_cardinality_and_reserved_key(self):
        for mode in ('none','extra','RESET','empty','list-disagrees','count-disagrees'):
            def edit(root,p,l,a,r):
                if mode=='none':l.animations.clear()
                elif mode=='extra':l.animations[m.Name('other')]=a
                elif mode in ('RESET','empty'):l.animations={m.Name('RESET' if mode=='RESET' else ''):a}
                elif mode=='list-disagrees':p.player_list_override=['different']
                else:l.reported_count=2
            with self.subTest(mode=mode):self.run_case(edit)

    def test_resource_alias_lookup_must_match_object(self):
        self.run_case(lambda root,p,l,a,r:setattr(p,'player_animation_override',deepcopy(a)))

    def test_scripted_and_queued_resource(self):
        for target in ('library','animation'):
            for setting in ('script','queued'):
                def edit(root,p,l,a,r):setattr(l if target=='library' else a,setting,m.ResourceView(9901,'Script') if setting=='script' else True)
                with self.subTest(target=target,setting=setting):self.run_case(edit)

    def test_script_single_capture_same_reference(self):
        def edit(root,p,l,a,r):a.field_sequences['script']=[m.ResourceView(9999,'Script'),None]
        out,_,items=self.run_case(edit)
        self.assertEqual(out['inventory']['animation']['script']['instance_id'],9999);self.assertEqual(items[5].field_read_counts['script'],1)

    def test_supported_typed_metadata_is_retained(self):
        def edit(root,p,l,a,r):a.metadata={'dict':{'integer':1,'float':1.0,'bool':True,'list':[None,m.Name('tag'),m.PathValue('route')]}}
        out,_,_=self.run_case(edit,ok=True);self.assertEqual(out['inventory']['animation']['metadata'][0]['value']['type'],27)

    def test_unsupported_nonfinite_and_cyclic_metadata(self):
        cycle=[];cycle.append(cycle)
        for v in (object(),float('nan'),cycle):
            with self.subTest(kind=type(v).__name__):self.run_case(lambda root,p,l,a,r:a.metadata.update(bad=v))

    def test_animation_settings_and_markers_refused(self):
        for k,v in {'length':1.9,'step':0.0,'loop_mode':1,'capture_included':True,'markers':['marker']}.items():
            with self.subTest(field=k):self.run_case(lambda root,p,l,a,r:setattr(a,k,v))

    def test_next_animation_and_blending_refused(self):
        self.run_case(lambda root,p,l,a,r:setattr(p,'next_animation',m.Name('next')))
        self.run_case(lambda root,p,l,a,r:setattr(p,'self_blend_time',1.0))

    def test_track_count_refuses_before_inventory(self):
        for delta in (-1,1):
            def edit(root,p,l,a,r):
                if delta<0:a.tracks.pop()
                else:a.tracks.append(deepcopy(a.tracks[0]))
            out,_,_=self.run_case(edit);self.assertEqual(out['inventory']['tracks'],[])

    def test_all_unsupported_track_types(self):
        for kind in (0,3,4,5,6,7,8,99):
            with self.subTest(kind=kind):
                out,_,items=self.run_case(lambda root,p,l,a,r:setattr(a.tracks[0],'kind',kind))
                self.assertEqual(items[5].tracks[0].key_count_reads,0)
                self.assertEqual(len(out['inventory']['tracks']),1)

    def test_track_flags_and_compression_before_keys(self):
        for k,v in {'enabled':False,'imported':False,'interpolation':0,'loop_wrap':False,'compressed':True}.items():
            out,_,items=self.run_case(lambda root,p,l,a,r:setattr(a.tracks[0],k,v));self.assertEqual(items[5].tracks[0].key_count_reads,0)
            self.assertIn('omitted',out['inventory']['tracks'][0])

    def test_track_paths_refused(self):
        for path in (m.PathValue('/absolute',True),m.PathValue(''),m.PathValue('native_0:position',False,1),m.PathValue('missing')):
            with self.subTest(path=path.text):self.run_case(lambda root,p,l,a,r:setattr(a.tracks[0],'path',path))

    def test_duplicate_missing_roles_refused(self):
        self.run_case(lambda root,p,l,a,r:setattr(a.tracks[0],'path',deepcopy(a.tracks[2].path)))
        self.run_case(lambda root,p,l,a,r:setattr(a.tracks[1],'kind',1))

    def test_same_name_wrong_identity_cannot_substitute(self):
        def edit(root,p,l,a,r):
            other=m.c247.NodeView(987654,'MeshInstance3D');root.resolve_map[str(root.children[0].name)]=other
        self.run_case(edit)

    def test_key_count_bounds_and_partial_progress(self):
        for count in (0,4097):
            out,_,_=self.run_case(lambda root,p,l,a,r:setattr(a.tracks[11],'key_count',count))
            self.assertEqual(len(out['inventory']['tracks']),12);self.assertEqual(out['inventory']['tracks'][-1]['key_count']['value'],count)
        self.run_case(lambda root,p,l,a,r:setattr(a.tracks[0],'key_count',4096),ok=True)

    def test_actual_counts_do_not_claim_payload_fidelity(self):
        out,_,_=self.run_case(lambda root,p,l,a,r:setattr(a.tracks[0],'key_count',2),ok=True)
        self.assertEqual(out['inventory']['tracks'][0]['key_count']['value'],2)
        self.assertIn('does not prove',out['inventory']['tracks'][0]['key_payload'])

    def test_track_drift_between_passes(self):
        def edit(root,p,l,a,r):a.tracks[8].mutate_at=lambda t:setattr(t,'key_count',122) if t.reads==2 else None
        out,_,_=self.run_case(edit);self.assertEqual(out['inventory']['tracks'][8]['key_count']['value'],121);self.assertEqual(out['recheck']['tracks'][8]['key_count']['value'],122)

    def test_player_settings_drift(self):
        def edit(root,p,l,a,r):p.inventory_hook=lambda player,n:player.settings.update(playing=True) if n==2 else None
        self.run_case(edit)

    def test_material_identity_drift_after_owned_capture(self):
        def edit(root,p,l,a,r):
            def drift(rt,n):
                if n==2:rt.children[0].mesh.surface_material=deepcopy(rt.children[0].mesh.surface_material);rt.children[0].mesh.surface_material.identity+=1
            root.scene_hook=drift
        self.run_case(edit)

    def test_resource_replacement_during_tracks(self):
        def edit(root,p,l,a,r):a.tracks[-1].mutate_at=lambda t:l.animations.update({next(iter(l.animations)):deepcopy(a)})
        self.run_case(edit)

    def test_registry_fault_after_capture_refuses(self):
        def edit(root,p,l,a,r):a.tracks[-1].mutate_at=lambda t:r.faults.append('late external fault') if t.reads==2 else None
        self.run_case(edit)

    def test_final_scene_membership_drift_retains_partial(self):
        def edit(root,p,l,a,r):
            def drift(rt,n):
                if n==4:rt.children[-1].queued=True
            root.scene_hook=drift
        out,_,_=self.run_case(edit);self.assertIn('scene_after_drift',out['recheck'])


if __name__=='__main__':unittest.main(verbosity=2)
