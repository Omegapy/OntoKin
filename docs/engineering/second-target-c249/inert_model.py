"""Synthetic C249 inventory composed with the unchanged C248 Python reader.

Fake identities, resolver results and getters model boundaries. No GDScript,
NodePath parser, native resource, callback, key payload or pose is executed.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import importlib.util
import math
from pathlib import Path
import sys

_SPEC = importlib.util.spec_from_file_location('ontokin_c249_c248_model',
    Path(__file__).resolve().parents[1] / 'second-target-c248/inert_model.py')
c248 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = c248
_SPEC.loader.exec_module(c248)
c247 = c248.c247
MESHES = c248.MESHES
MAX_SCENE_NODES = 64
EXPECTED_TRACKS = 36
MAX_KEYS_PER_TRACK = 4096


class Name(str):
    """A fabricated native StringName, preserving its distinct type tag."""


@dataclass
class PathValue:
    text: str
    absolute: bool = False
    subnames: int = 0


@dataclass
class TrackView:
    path: PathValue
    kind: int
    enabled: bool = True
    imported: bool = True
    interpolation: int = 1
    loop_wrap: bool = True
    compressed: bool = False
    key_count: int = 121
    reads: int = 0
    key_count_reads: int = 0
    mutate_at: object = None

    def read(self):
        self.reads += 1
        if self.mutate_at is not None:self.mutate_at(self)


@dataclass
class ResourceView:
    identity: int
    native_class: str
    name: str = ''
    path: str = ''
    script: object = None
    metadata: dict = field(default_factory=dict)
    alive: bool = True
    queued: bool = False
    reads: int = 0
    mutate_at: object = None
    field_sequences: dict = field(default_factory=dict)
    field_read_counts: dict = field(default_factory=dict)

    def read(self):
        self.reads += 1
        if self.mutate_at is not None:self.mutate_at(self)

    def read_field(self, name):
        self.field_read_counts[name] = self.field_read_counts.get(name, 0) + 1
        sequence = self.field_sequences.get(name)
        return sequence.pop(0) if sequence else getattr(self, name)


@dataclass
class AnimationView(ResourceView):
    length: float = 2.0
    step: float = 1.0 / 60.0
    loop_mode: int = 0
    capture_included: bool = False
    markers: list = field(default_factory=list)
    tracks: list = field(default_factory=list)


@dataclass
class LibraryView(ResourceView):
    animations: dict = field(default_factory=dict)
    reported_count: object = None


SETTINGS = {'active':True,'callback_mode_process':1,'callback_mode_method':0,
            'callback_mode_discrete':1,'deterministic':False,'autoplay':Name(''),
            'assigned_animation':Name(''),'current_animation':Name(''),'playing':False,
            'queue':[],'root_motion_track':PathValue(''),'root_motion_local':False,
            'speed_scale':1.0,'default_blend_time':0.0,'auto_capture':True,'has_section':False}


def typed(value):
    if isinstance(value,Name):return {'type':21,'value':str(value)}
    if type(value) is PathValue:return {'type':22,'value':value.text}
    return {'type':{type(None):0,bool:1,int:2,float:3,str:4}.get(type(value),-1),'value':deepcopy(value)}


class Refusal(Exception):pass


class Facts:
    """Bounded fabricated counterpart of native_facts.gd typed metadata."""
    def __init__(self):self.values=0

    def consume(self):
        self.values+=1
        if self.values>100000:raise ValueError('native fact capture value limit')

    def typed(self,value,depth=0):
        self.consume()
        if depth>32:raise ValueError('metadata depth limit or cycle')
        if type(value) in (type(None),bool,int,str) or isinstance(value,Name) or type(value) is PathValue:return typed(value)
        if type(value) is float:
            if not math.isfinite(value):raise ValueError('nonfinite metadata')
            return typed(value)
        if type(value) is list:return {'type':28,'entries':[self.typed(v,depth+1) for v in value]}
        if type(value) is dict:return {'type':27,'entries':[{'key':self.typed(k,depth+1),'value':self.typed(v,depth+1)} for k,v in value.items()]}
        raise ValueError('unsupported metadata type')

    def metadata(self,value,out):
        for k,v in value.metadata.items():
            self.consume()
            row={'key':self.typed(Name(k))};out.append(row)
            row['value']=self.typed(v)


class Capture:
    def __init__(self):
        self.used=False
        self.errors=[]
        self.result={}
        self.material_reader=c248.Capture()
        self.material_calls=0
        self.scene_reads=0
        self.inventory_reads=0

    def refuse(self,reason):
        if not self.errors:self.errors.append(reason)
        self.result.update(phase='REFUSED',component_complete=False)
        raise Refusal(reason)

    def check(self,condition,reason):
        if not condition:self.refuse(reason)

    def identity(self,value):
        if value is None:return {'type':0,'instance_id':0,'class':'null'}
        self.check(value.alive,'invalid native identity')
        return {'type':24,'instance_id':value.identity,'class':value.native_class}

    def object(self,value,facts,out):
        if value is not None and hasattr(value,'read'):value.read()
        out['identity']=self.identity(value)
        self.check(value is not None,'missing inventory object')
        out['queued_for_deletion']=getattr(value,'queued',False)
        script=value.read_field('script') if hasattr(value,'read_field') else value.script
        out['script']=self.identity(script)
        self.check(script is None and not out['queued_for_deletion'],'scripted or queued inventory object')
        if type(value) is c247.NodeView:out['name']=typed(value.name)
        else:out.update(resource_name=typed(value.name),resource_path=typed(value.path))
        out['metadata']=[]
        try:facts.metadata(value,out['metadata'])
        except ValueError as exc:
            out['metadata_errors']=[str(exc)]
            self.refuse('unsupported or incomplete native metadata')

    def scene(self,root,materials,out):
        self.scene_reads+=1
        if getattr(root,'scene_hook',None) is not None:root.scene_hook(root,self.scene_reads)
        arrays=materials['mesh_arrays'];chain=arrays['chain']
        out.update(nodes=[],material_bindings=[])
        self.check(type(root) is c247.NodeView and root.alive and root.native_class=='Node3D' and root.parent is None
                   and root.identity==chain['root']['instance_id'] and not root.inside_tree,'returned root changed or entered tree')
        self.check(len(materials['parts'])==18,'incomplete owned material receipt')
        wanted,retired={},set()
        for i,part in enumerate(materials['parts']):
            self.check((part['source_node'],part['source_mesh'],part['source_primitive'],part['native_surface'])==(i,MESHES[i],0,0),'owned source association differs')
            identity=part['native_node_instance_id']
            self.check(identity not in wanted and identity==chain['finals'][i]['new'],'ambiguous owned identity')
            wanted[identity]=i;retired.add(chain['originals'][i]['old'])
        pending,seen,meshes,players=[root],set(),{},[]
        while pending:
            self.check(len(seen)<MAX_SCENE_NODES,'animation scene traversal bound exceeded')
            node=pending.pop()
            self.check(type(node) is c247.NodeView and node.alive,'invalid final scene member')
            script=node.script
            row={'identity':self.identity(node),'script':self.identity(script),'queued_for_deletion':getattr(node,'queued',False),
                 'inside_tree':getattr(node,'inside_tree',False),'name':typed(getattr(node,'name',Name(''))),
                 'parent':self.identity(node.parent),'owner':self.identity(getattr(node,'owner',None)),
                 'path_from_root':typed(PathValue('.' if node is root else str(getattr(node,'name',''))))}
            out['nodes'].append(row)
            self.check(node.identity not in seen and node.identity not in retired and script is None and not row['queued_for_deletion']
                       and not row['inside_tree'],'duplicate retired scripted queued or attached member')
            seen.add(node.identity)
            if node is not root:
                self.check(node.parent is root,'unexpected finite fixture hierarchy')
                if node.native_class=='MeshInstance3D':
                    self.check(node.identity in wanted,'unmapped final mesh');meshes[wanted[node.identity]]=node
                elif node.native_class=='AnimationPlayer':players.append(node)
                else:self.refuse('unsupported scene member or additional mixer')
            self.check(len(pending)+len(seen)+len(node.children)<=MAX_SCENE_NODES,'animation scene traversal bound exceeded')
            pending.extend(node.children)
        out['player_count']=len(players)
        self.check(len(meshes)==18 and len(players)==1,'missing mesh or ambiguous animation player')
        for i in range(18):
            node=meshes[i];expected=materials['parts'][i]['snapshot'];mesh=node.mesh
            row={'source_node':i,'node':self.identity(node),'mesh':self.identity(mesh)};out['material_bindings'].append(row)
            self.check(mesh is not None and mesh.native_class=='ArrayMesh' and row['mesh']==expected['mesh'],'owned mesh binding changed')
            script=mesh.script
            row.update(mesh_script=self.identity(script),surface_count=mesh.surface_count,surface_override_count=node.surface_override_count)
            self.check(script is None and not getattr(mesh,'queued',False) and mesh.surface_count==1 and node.surface_override_count==1,'mesh script lifetime or inventory changed')
            material=mesh.surface_material
            active=node.active_override if node.override_active else node.material_override or node.surface_override or material
            row['selection']={'node_override':self.identity(node.material_override),'overlay':self.identity(node.material_overlay),
                              'surface_override':self.identity(node.surface_override),'mesh_surface':self.identity(material),
                              'active':self.identity(active),'precedence':'node override then surface override then mesh surface'}
            row['instance_transparency']=typed(node.instance_transparency)
            self.check(row['selection']==expected['selection'] and row['instance_transparency']==expected['instance_transparency']
                       and material is not None and material is active,'owned material or selector binding changed')
            script=material.read_field('script');row['material_script']=self.identity(script)
            self.check(script is None and not getattr(material,'queued',False),'owned material script or lifetime changed')
        return {'meshes':meshes,'player':players[0],'source_by_instance':wanted}

    def player_names(self,player):
        if player.player_list_override is not None:return player.player_list_override[:]
        return [str((str(k)+'/' if k else '')+str(n)) for k,v in player.libraries.items() for n in v.animations]

    def player_animation(self,player,key):
        if player.player_animation_override is not None:return player.player_animation_override
        return player.libraries.get(Name('')).animations.get(key)

    def inventory(self,root,materials,out):
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
        self.check(not raw['playing'] and not raw['has_section'] and not raw['autoplay'] and not raw['assigned_animation']
                   and not raw['current_animation'] and not raw['queue'],'player has playback assignment queue or incomplete settings')
        self.check(not raw['root_motion_track'].text and not raw['root_motion_local'] and raw['speed_scale']==1.0
                   and raw['default_blend_time']==0.0,'unsupported root motion speed or blending')
        self.check(raw['active'] is True and raw['callback_mode_process']==1 and raw['callback_mode_method']==0 and raw['callback_mode_discrete']==1
                   and raw['deterministic'] is False and raw['auto_capture'] is True,'unsupported imported player mode')
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
        except Refusal:
            out['scene_after_drift']=final_scene;raise
        if final_scene!=out['scene']:
            out['scene_after_drift']=final_scene;self.refuse('scene or source resource bindings changed during inventory')
        self.check(list(player.libraries)==libraries and player.libraries.get(library_key) is library and list(library.animations)==names
                   and (library.reported_count if library.reported_count is not None else len(library.animations))==1
                   and self.player_names(player)==player_names and library.animations.get(key) is animation
                   and self.player_animation(player,key) is animation,'live animation selection changed during inventory')

    def capture(self,registry,state,root):
        try:
            if self.used:self.refuse('animation inventory is single use')
            self.used=True
            self.result={'schema':'ontokin.c249.native-animation-inventory/0.1','phase':'CAPTURING','component_complete':False,
                         'execution_admission':False,'native_acceptance':False,'R07':'PENDING','value_origin':'native-api-readback',
                         'omissions':['key times and values','playback assignment and advancement control','seek and 126-pose evaluation','serialization and raw sealing']}
            self.material_calls+=1
            materials=self.material_reader.capture(registry,state,root);self.result['materials']=materials
            self.check(materials.get('component_complete') is True and materials.get('phase')=='MATERIAL_PARAMETERS_CAPTURED_OTHER_RAW_PENDING','owned material capture refused')
            self.check(not registry.faults,'registry fault before animation inventory')
            self.result['inventory']={};self.inventory(root,materials,self.result['inventory'])
            self.result['recheck']={};self.inventory(root,materials,self.result['recheck'])
            self.check(self.result['inventory']==self.result['recheck'],'native animation inventory changed during capture')
            self.check(not registry.faults,'registry changed during animation inventory')
            self.result.update(phase='ANIMATION_INVENTORY_CAPTURED_POSES_PENDING',component_complete=True,
                               stability='two equal inventories with final membership/resource lookup rechecks; not atomic against concurrent writes')
        except Refusal:pass
        self.result['errors']=self.errors[:]
        return deepcopy(self.result)


def synthetic_fixture():
    registry,state,root=c248.synthetic_fixture()
    root.name=Name('ImportedRoot');root.inside_tree=False;root.queued=False;root.owner=None;root.scene_hook=None;root.resolve_map={}
    tracks=[]
    for i,node in enumerate(root.children):
        node.name=Name('native_'+str(i));node.inside_tree=False;node.queued=False;node.owner=root
        root.resolve_map[str(node.name)]=node
        tracks.extend(TrackView(PathValue(str(node.name)),kind) for kind in (1,2))
    animation=AnimationView(7002,'Animation',name='descriptive native animation',tracks=tracks)
    library=LibraryView(7001,'AnimationLibrary',animations={Name('arbitrary animation key'):animation})
    player=c247.NodeView(7000,native_class='AnimationPlayer',parent=root)
    player.name=Name('arbitrary native player');player.owner=root;player.inside_tree=False;player.queued=False;player.metadata={}
    player.root_path=PathValue('..');player.root_target=root;player.root_lookup_reads=0;player.settings=deepcopy(SETTINGS)
    player.libraries={Name(''):library};player.next_animation=Name('');player.self_blend_time=0.0
    player.player_list_override=None;player.player_animation_override=None;player.inventory_hook=None
    root.children.append(player)
    return registry,state,root


def fixture_objects(root):
    """Test convenience only; not an admission or receipt API."""
    player=next(n for n in root.children if n.native_class=='AnimationPlayer')
    library=player.libraries[Name('')];animation=next(iter(library.animations.values()))
    return player,library,animation
