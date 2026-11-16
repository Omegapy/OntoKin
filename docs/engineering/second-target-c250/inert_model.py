"""Synthetic C250 preparation model, composing the unchanged C249 capture.

All identities, native reads and setter effects are fabricated Python inputs.
No GDScript, callback, NodePath parser, native animation or pose is executed.
"""
from copy import deepcopy
import importlib.util
import math
from pathlib import Path
import sys

_SPEC = importlib.util.spec_from_file_location('ontokin_c250_c249_model',
    Path(__file__).resolve().parents[1] / 'second-target-c249/inert_model.py')
c249 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = c249
_SPEC.loader.exec_module(c249)
Name, PathValue, Facts, typed = c249.Name, c249.PathValue, c249.Facts, c249.typed
MESHES, EXPECTED_TRACKS, MAX_KEYS_PER_TRACK = c249.MESHES, c249.EXPECTED_TRACKS, c249.MAX_KEYS_PER_TRACK


class Refusal(Exception):
    pass


class BoundaryReader(c249.Capture):
    """Read-only policy-aware view; does not call capture or consume a registry."""

    def inventory(self, root, materials, out, expected):
        self.inventory_reads+=1
        out.update(scene={},tracks=[])
        live=self.scene(root,materials,out['scene']);player=live['player'];facts=Facts()
        if player.inventory_hook is not None:player.inventory_hook(player,self.inventory_reads)
        out['player']={};self.object(player,facts,out['player'])
        root_path=player.root_path
        out['player']['root_path']=typed(root_path)
        if root_path.absolute or not root_path.text or root_path.subnames!=0:
            out['player']['omitted']=['root lookup after unsupported path shape'];self.refuse('unsupported animation root path')
        player.root_lookup_reads+=1;root_target=player.root_target
        out['player']['root_target']=self.identity(root_target)
        settings={};out['player']['settings']=settings
        for k,v in player.settings.items():
            try:settings[k]=facts.typed(v) if k=='queue' else typed(v)
            except ValueError as exc:
                settings[k]={'refused':str(exc)}
                out['player']['settings_errors']=[str(exc)]
                self.refuse('player has playback assignment queue or incomplete settings')
        self.check(root_target is root,'root path does not resolve to owned root')
        raw=player.settings
        self.check(settings==expected['player']['settings'],'player settings differ from declared stage')
        libraries=list(player.libraries);out['library_count']=len(libraries)
        if len(libraries)!=1:
            out['omitted']=['library contents outside single-library bound'];self.refuse('ambiguous or missing library')
        library_key=libraries[0];out['library_key']=typed(library_key)
        self.check(library_key==Name(''),'unsupported nondefault library')
        library=player.libraries[library_key];out['library']={};self.object(library,facts,out['library'])
        self.check(library.native_class=='AnimationLibrary','unsupported native library class')
        names=list(library.animations);player_names=self.player_names(player)
        count=library.reported_count if library.reported_count is not None else len(names)
        out.update(animation_count=count,library_list_count=len(names),player_animation_count=len(player_names))
        if count!=1 or len(names)!=1 or len(player_names)!=1:
            out['omitted']=['animation contents outside single-animation bound'];self.refuse('ambiguous or missing native animation')
        key=names[0];out.update(animation_key=typed(key),player_animation_key=typed(player_names[0]))
        self.check(bool(key) and key!=Name('RESET') and str(key)==player_names[0],'ambiguous reserved or inconsistent key')
        animation=library.animations[key];player_animation=self.player_animation(player,key)
        out['player_animation']=self.identity(player_animation);out['animation']={};self.object(animation,facts,out['animation'])
        self.check(animation.native_class=='Animation' and animation is player_animation,'animation resource selection disagrees')
        out.update(next_animation=typed(player.next_animation),self_blend_time=typed(player.self_blend_time))
        self.check(not player.next_animation and player.self_blend_time==0.0,'unexpected next animation or blend override')
        out['animation'].update({k:typed(getattr(animation,k)) for k in ('length','step','loop_mode','capture_included')})
        out['animation']['marker_count']=len(animation.markers)
        if animation.markers:
            out['animation']['omitted']=['marker payload outside original imported route'];self.refuse('unexpected animation markers')
        self.check(animation.length==2.0 and math.isfinite(animation.step) and animation.step>0 and animation.loop_mode==0
                   and not animation.capture_included,'unsupported duration loop step or capture mode')
        out['track_count']=len(animation.tracks)
        if len(animation.tracks)!=EXPECTED_TRACKS:
            out['omitted']=['track contents outside original 36-track bound'];self.refuse('missing or extra native tracks')
        pairs={}
        for i,track in enumerate(animation.tracks):
            track.read();path=track.path
            row={'track_index':i,'type':typed(track.kind),'path':typed(path),**{k:typed(getattr(track,k)) for k in ('enabled','imported','interpolation','loop_wrap','compressed')}}
            out['tracks'].append(row)
            if track.kind not in (1,2) or not track.enabled or not track.imported or track.interpolation!=1 or not track.loop_wrap or track.compressed:
                row['omitted']=['target/key metadata after unsupported track route','key values never read'];self.refuse('unsupported disabled executable compressed or nonbaseline track')
            if path.absolute or not path.text or path.subnames!=0:
                row['omitted']=['target lookup after unsupported path','key values never read'];self.refuse('unsupported track path')
            target=root.resolve_map.get(path.text);row['target']=self.identity(target)
            self.check(target is not None and target.native_class=='MeshInstance3D' and target.identity in live['source_by_instance'],'track target not an owned live part')
            source=live['source_by_instance'][target.identity]
            row.update(source_node=source,source_mesh=MESHES[source],source_channel_path='translation' if track.kind==1 else 'rotation')
            pair=(source,track.kind);self.check(pair not in pairs,'duplicate source-node track role');pairs[pair]=i
            track.key_count_reads+=1;row['key_count']=typed(track.key_count)
            if track.key_count<=0 or track.key_count>MAX_KEYS_PER_TRACK:
                row['omitted']=['key times and values outside inventory scope'];self.refuse('empty or oversized key inventory')
            row['key_payload']='not read; count does not prove key times values or evaluation'
        out.update(source_animation_index=0,source_association='sole animation under pinned importer route; no public source/native pointer attestation')
        final_scene={}
        try:self.scene(root,materials,final_scene)
        except c249.Refusal:
            out['scene_after_drift']=final_scene;raise
        if final_scene!=out['scene']:
            out['scene_after_drift']=final_scene;self.refuse('scene or source resource bindings changed during inventory')
        self.check(list(player.libraries)==libraries and player.libraries.get(library_key) is library and list(library.animations)==names
                   and (library.reported_count if library.reported_count is not None else len(library.animations))==1
                   and self.player_names(player)==player_names and library.animations.get(key) is animation
                   and self.player_animation(player,key) is animation,'live animation selection changed during inventory')

        self.check(out==expected,'native inventory differs from retained inventory and declared changes')


class Capture:
    def __init__(self):
        self.used = False
        self.errors = []
        self.result = {}
        self.inventory_reader = c249.Capture()
        self.inventory_calls = 0
        self.boundary_reads = 0

    def refuse(self, reason):
        if not self.errors:
            self.errors.append(reason)
        self.result.update(phase='REFUSED', component_complete=False)
        raise Refusal(reason)

    def check(self, condition, reason):
        if not condition:
            self.refuse(reason)

    @staticmethod
    def expected_inventory(original, mode, assignment):
        expected = deepcopy(original)
        expected['player']['settings']['callback_mode_process']['value'] = mode
        expected['player']['settings']['assigned_animation']['value'] = str(assignment)
        return expected

    def boundary(self, registry, root, materials, expected, assigned):
        self.boundary_reads += 1
        reader = BoundaryReader()
        receipt = {'complete':False, 'inventory':{}, 'control':{}, 'errors':[]}
        player = None
        try:
            reader.inventory(root, materials, receipt['inventory'], expected)
            live_scene = {}
            live = reader.scene(root, materials, live_scene)
            reader.check(live_scene == expected['scene'], 'scene changed before control boundary')
            player = live['player']
            control = receipt['control']
            control.update(player=reader.identity(player), internal_idle=typed(player.internal_idle),
                           internal_physics=typed(player.internal_physics), blocking_signals=typed(player.blocking_signals),
                           assignment_signal_connection_count=len(player.signal_connections))
            if player.signal_connections:
                control['omitted'] = ['signal Callable payload; every receiver refuses']
                reader.refuse('assignment signal has a receiver')
            reader.check(not player.internal_idle and not player.internal_physics and not player.blocking_signals,
                         'unexpected internal processing or blocked signals')
            control['animation_active'] = typed(player.animation_active)
            reader.check(player.animation_active == assigned, 'assignment pointer state differs from declared stage')
            if assigned:
                player.position_reads += 1
                player.length_reads += 1
                control.update(position=typed(player.current_position), length=typed(player.current_length))
                reader.check(player.current_position == 0.0 and player.current_length == 2.0,
                             'stopped assignment position or length differs')
            else:
                control['omitted'] = ['position and length require an assigned playback pointer']
            receipt['inventory_recheck'] = {}
            reader.inventory(root, materials, receipt['inventory_recheck'], expected)
            control.update(final_assignment_signal_connection_count=len(player.signal_connections),
                           final_internal_idle=typed(player.internal_idle), final_internal_physics=typed(player.internal_physics),
                           final_animation_active=typed(player.animation_active), final_blocking_signals=typed(player.blocking_signals))
            if player.signal_connections:
                control['final_omitted'] = ['signal Callable payload; every receiver refuses']
            reader.check(not player.signal_connections and not player.internal_idle and not player.internal_physics
                         and player.animation_active == assigned and not control['final_blocking_signals']['value'],
                         'control or signal drift at mutation boundary')
            if assigned:
                player.position_reads += 1
                player.length_reads += 1
                control.update(final_position=typed(player.current_position), final_length=typed(player.current_length))
                reader.check(player.current_position == 0.0 and player.current_length == 2.0,
                             'stopped assignment position or length drift at final boundary')
            reader.check(not registry.faults, 'registry fault at mutation boundary')
            receipt['complete'] = True
        except c249.Refusal:
            receipt['errors'] = reader.errors[:]
            if not receipt['control']:
                receipt['omitted'] = ['control getters after incomplete live inventory']
        return receipt, player

    def set_manual(self, player):
        """Fabricated native effects, followed by a test-only adversarial hook."""
        player.mutation_calls.append('set_callback_mode_process')
        player.settings['active'] = False
        player.internal_idle = False
        player.settings['callback_mode_process'] = 2
        player.settings['active'] = True
        if player.mutation_hook is not None:
            player.mutation_hook('set_callback_mode_process', player, self)

    def assign_stopped(self, player, key):
        """Fabricated stopped setter, without evaluating any track or transform."""
        player.mutation_calls.append('set_assigned_animation')
        player.settings['assigned_animation'] = Name(key)
        player.animation_active = True
        player.current_position = 0.0
        player.current_length = 2.0
        if player.mutation_hook is not None:
            player.mutation_hook('set_assigned_animation', player, self)

    def capture(self, registry, state, root):
        try:
            if self.used:
                self.refuse('playback preparation is single use; reentry or retry refused')
            self.used = True
            self.result = {'schema':'ontokin.c250.native-playback-preparation/0.1', 'phase':'CAPTURING',
                           'component_complete':False, 'execution_admission':False, 'native_acceptance':False,
                           'R07':'PENDING', 'value_origin':'native-api-readback', 'mutations':[],
                           'rollback':'never attempted; partial observed changes remain',
                           'omissions':['seek and advancement','world transforms and 126 poses','tree attachment','serialization and raw sealing']}
            self.inventory_calls += 1
            inventory = self.inventory_reader.capture(registry, state, root)
            self.result['animation_inventory'] = inventory
            self.check(inventory.get('component_complete') is True and inventory.get('phase') == 'ANIMATION_INVENTORY_CAPTURED_POSES_PENDING'
                       and not self.errors, 'owned animation inventory refused')
            original, materials = inventory['inventory'], inventory['materials']
            key = Name(original['animation_key']['value'])
            before_manual, player = self.boundary(registry, root, materials, original, False)
            self.result['before_manual'] = before_manual
            self.check(before_manual['complete'] and not self.errors, 'manual-control boundary refused')
            manual = {'operation':'set_callback_mode_process', 'requested':2, 'status':'ATTEMPTED',
                      'before':before_manual, 'after':{'status':'NOT_OBSERVED'}}
            self.result['mutations'].append(manual)
            self.set_manual(player)
            manual['status'] = 'RETURNED'
            manual_expected = self.expected_inventory(original, 2, Name(''))
            manual['after'], _ = self.boundary(registry, root, materials, manual_expected, False)
            if not manual['after']['complete'] or self.errors:
                manual['outcome'] = 'REFUSED_AFTER_ATTEMPT'
                self.refuse('manual-control readback refused; changes retained')
            manual['outcome'] = 'DECLARED_CHANGE_OBSERVED'
            before_assignment, player = self.boundary(registry, root, materials, manual_expected, False)
            self.result['before_assignment'] = before_assignment
            self.check(before_assignment['complete'] and not self.errors, 'stopped-assignment boundary refused; manual change retained')
            assignment = {'operation':'set_assigned_animation', 'requested':str(key), 'status':'ATTEMPTED',
                          'before':before_assignment, 'after':{'status':'NOT_OBSERVED'}}
            self.result['mutations'].append(assignment)
            self.assign_stopped(player, key)
            assignment['status'] = 'RETURNED'
            assigned_expected = self.expected_inventory(original, 2, key)
            assignment['after'], _ = self.boundary(registry, root, materials, assigned_expected, True)
            if not assignment['after']['complete'] or self.errors:
                assignment['outcome'] = 'REFUSED_AFTER_ATTEMPT'
                self.refuse('stopped-assignment readback refused; changes retained')
            assignment['outcome'] = 'DECLARED_CHANGE_OBSERVED'
            self.result.update(phase='DETACHED_MANUAL_STOPPED_ASSIGNMENT_PREPARED_POSES_PENDING', component_complete=True,
                               stability='bounded before/after live readbacks; no atomicity or transient-mutation guarantee')
        except Refusal:
            pass
        self.result['errors'] = self.errors[:]
        return deepcopy(self.result)


def synthetic_fixture():
    registry, state, root = c249.synthetic_fixture()
    player, _, _ = c249.fixture_objects(root)
    player.internal_idle = False
    player.internal_physics = False
    player.blocking_signals = False
    player.signal_connections = []
    player.animation_active = False
    player.current_position = None
    player.current_length = None
    player.position_reads = 0
    player.length_reads = 0
    player.mutation_calls = []
    player.mutation_hook = None
    return registry, state, root


def fixture_objects(root):
    """Test convenience only; not an admission or prior-receipt interface."""
    return c249.fixture_objects(root)
