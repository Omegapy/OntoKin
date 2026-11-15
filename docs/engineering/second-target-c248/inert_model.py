"""Synthetic C248 material capture composed with the unchanged C247 CPU model.

No GDScript parsing, native callbacks, color codec, renderer, or diagnostics are
emulated. Raw Color/scalars here are fabricated represented Python values.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import importlib.util
import math
from pathlib import Path
import sys

_SPEC = importlib.util.spec_from_file_location('ontokin_c248_c247_model',
    Path(__file__).resolve().parents[1] / 'second-target-c247/inert_model.py')
c247 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = c247
_SPEC.loader.exec_module(c247)
MESHES = c247.MESHES
MATERIAL_BY_MESH = (0,0,1,1,1)
MAX_SCENE_NODES = 64
SETTINGS = {'blend_mode':0,'depth_draw_mode':0,'depth_test':0,'shading_mode':1,
            'diffuse_mode':0,'specular_mode':0,'metallic_specular':0.5,'billboard_mode':0,
            'distance_fade_mode':0,'proximity_fade_enabled':False,'grow':False,
            'stencil_mode':0,'stencil_flags':0,'render_priority':0,'alpha_antialiasing_mode':0}


@dataclass
class ColorValue:
    r: float
    g: float
    b: float
    a: float


@dataclass
class ResourceView:
    identity: int
    native_class: str = 'Texture2D'
    alive: bool = True


@dataclass
class MaterialView:
    identity: int
    native_class: str = 'StandardMaterial3D'
    script: object = None
    color: object = field(default_factory=lambda:ColorValue(0.125,0.375,0.625,1.0))
    metallic: object = 0.25
    roughness: object = 0.75
    cull: object = 0
    transparency: object = 0
    next_pass: object = None
    settings: dict = field(default_factory=lambda:deepcopy(SETTINGS))
    features: list = field(default_factory=lambda:[False]*13)
    flags: list = field(default_factory=lambda:[False]*16+[True]+[False]*8)
    textures: list = field(default_factory=lambda:[None]*19)
    alive: bool = True
    reads: int = 0
    mutate_at: object = None

    field_sequences: dict = field(default_factory=dict)
    field_read_counts: dict = field(default_factory=dict)

    def read_field(self, name):
        self.field_read_counts[name]=self.field_read_counts.get(name,0)+1
        sequence=self.field_sequences.get(name)
        if sequence:return sequence.pop(0)
        return getattr(self,name)

    def read(self):
        self.reads += 1
        if self.mutate_at is not None:self.mutate_at(self)


def typed(value):
    return {'type':{type(None):0,bool:1,int:2,float:3,str:4,ColorValue:20}.get(type(value),-1),
            'value':deepcopy(value)}


def unit_float(value):
    return value['type']==3 and math.isfinite(value['value']) and 0.0<=value['value']<=1.0


class Refusal(Exception):pass


class Capture:
    def __init__(self):
        self.used=False
        self.errors=[]
        self.result={}
        self.mesh_reader=c247.Capture()
        self.mesh_calls=0
        self.material_reads=0

    def refuse(self,reason):
        if not self.errors:self.errors.append(reason)
        self.result.update(phase='REFUSED',component_complete=False)
        raise Refusal(reason)

    def check(self,condition,reason):
        if not condition:self.refuse(reason)

    def identity(self,value):
        if value is None:return {'type':0,'instance_id':0,'class':'null'}
        self.check(value.alive,'invalid native resource identity')
        return {'type':24,'instance_id':value.identity,'class':value.native_class}

    def live_meshes(self,root,arrays):
        chain=arrays['chain']
        self.check(type(root) is c247.NodeView and root.alive and root.native_class=='Node3D'
                   and root.parent is None and root.identity==chain['root']['instance_id'],'returned root changed')
        self.check(len(arrays['parts'])==18,'incomplete trusted array receipt')
        wanted,retired={},set()
        for i,part in enumerate(arrays['parts']):
            self.check((part['source_node'],part['source_mesh'],part['source_primitive'],part['native_surface'])==
                       (i,MESHES[i],0,0),'trusted primitive or mesh differs')
            identity=part['native_node_instance_id']
            self.check(identity not in wanted and identity==chain['finals'][i]['new'],'ambiguous trusted identity')
            wanted[identity]=i;retired.add(chain['originals'][i]['old'])
        found,seen,pending={},set(),[root]
        while pending:
            self.check(len(seen)<MAX_SCENE_NODES,'scene traversal bound exceeded')
            node=pending.pop()
            self.check(type(node) is c247.NodeView and node.alive,'invalid final scene member')
            self.check(node.identity not in seen and node.identity not in retired and node.script is None
                       and node.native_class!='ImporterMeshInstance3D','duplicate retired scripted unconverted member')
            seen.add(node.identity)
            if node.native_class in ('MeshInstance3D','CustomMeshInstance3D'):
                self.check(node.native_class=='MeshInstance3D' and node.identity in wanted,'unmapped final mesh')
                found[wanted[node.identity]]=node
            self.check(len(pending)+len(seen)+len(node.children)<=MAX_SCENE_NODES,'scene traversal bound exceeded')
            pending.extend(node.children)
        self.check(len(found)==18,'missing final mesh membership')
        return found

    def material(self,material,out):
        out['identity']=self.identity(material)
        self.check(type(material) is MaterialView and material.native_class=='StandardMaterial3D','unsupported material class')
        captured_script=material.read_field('script')
        out['script']=self.identity(captured_script)
        self.check(captured_script is None,'scripted material unsupported')
        self.material_reads+=1;material.read()
        raw={'albedo_color':typed(material.color),'metallic':typed(material.metallic),'roughness':typed(material.roughness),
             'cull_mode':typed(material.cull),'transparency_mode':typed(material.transparency)}
        out['raw']=raw
        self.check(raw['albedo_color']['type']==20,'native Color required')
        color=material.color
        raw['components']={k:typed(v) for k,v in [('r',color.r),('g',color.g),('b',color.b),('alpha',color.a)]}
        out['albedo_storage']='srgb-rgb-linear-alpha'
        out['storage_basis']='pinned glTF baseColorFactor linear_to_srgb; no observer conversion'
        captured_next_pass=material.read_field('next_pass')
        out['next_pass']=self.identity(captured_next_pass)
        out['settings']={name:typed(material.settings.get(name)) for name in SETTINGS}
        out.update(features=[],flags=[],textures=[])
        out['enum_counts']={'features':len(material.features),'flags':len(material.flags),'textures':len(material.textures)}
        if (len(material.features),len(material.flags),len(material.textures))!=(13,25,19):
            out['omitted']=[{'field':'feature inventories','reason':'pinned enum count mismatch'}]
            self.refuse('native feature inventory differs')
        out['features']=[{'index':i,'raw':typed(v)} for i,v in enumerate(material.features)]
        out['flags']=[{'index':i,'raw':typed(v)} for i,v in enumerate(material.flags)]
        for i,value in enumerate(material.textures):out['textures'].append({'index':i,'identity':self.identity(value)})
        self.check(all(unit_float(v) for v in raw['components'].values()),'invalid color component')
        self.check(unit_float(raw['metallic']) and unit_float(raw['roughness']),'invalid PBR scalar')
        self.check(raw['cull_mode']['type']==2 and material.cull in (0,1,2),'unsupported culling')
        self.check(raw['transparency_mode']['type']==2 and material.transparency in (0,1,2),'unsupported transparency')
        if captured_next_pass is not None:
            out['omitted']=[{'field':'next_pass payload','reason':'unsupported additional material pass'}]
            self.refuse('additional pass unsupported')
        for name,expected in SETTINGS.items():
            value=out['settings'][name]
            self.check(value['type']==typed(expected)['type'] and value['value']==expected,'unsupported setting '+name)
        self.check(all(v['raw']['type']==1 and v['raw']['value'] is False for v in out['features']),'additional feature')
        self.check(all(v['raw']['type']==1 and v['raw']['value'] is (v['index']==16) for v in out['flags']),'unsupported flag')
        for item in out['textures']:
            if item['identity']['instance_id']!=0:
                out['omitted']=[{'field':'texture payload','index':item['index'],'reason':'unsupported texture resource'}]
                self.refuse('textured material unsupported')

    def surface(self,node,part,out):
        out['native_surface']=0
        self.check(node.alive and node.native_class=='MeshInstance3D' and node.script is None
                   and node.identity==part['native_node_instance_id'],'final node changed')
        mesh=node.mesh;out['mesh']=self.identity(mesh)
        self.check(type(mesh) is c247.MeshView and mesh.alive and mesh.native_class=='ArrayMesh' and mesh.script is None
                   and mesh.identity==part['snapshot']['mesh_instance_id'],'mesh resource changed')
        out['surface_count']=typed(mesh.surface_count)
        out['surface_override_count']=typed(node.surface_override_count)
        self.check(mesh.surface_count==node.surface_override_count==1,'surface count differs')
        selected=node.material_override or node.surface_override or mesh.surface_material
        active=node.active_override if node.override_active else selected
        out['selection']={'node_override':self.identity(node.material_override),'overlay':self.identity(node.material_overlay),
                          'surface_override':self.identity(node.surface_override),'mesh_surface':self.identity(mesh.surface_material),
                          'active':self.identity(active),'precedence':'node override then surface override then mesh surface'}
        out['instance_transparency']=typed(node.instance_transparency)
        if node.material_override is not None or node.material_overlay is not None or node.surface_override is not None:
            out['omitted']=[{'field':'override material payload','reason':'outside locked import route'}]
            self.refuse('override or overlay unsupported')
        self.check(active is not None and active is mesh.surface_material,'active material disagrees')
        self.check(type(node.instance_transparency) is float and node.instance_transparency==0.0,'instance transparency unsupported')
        out['material']={}
        self.material(active,out['material'])

    def capture(self,registry,state,root):
        try:
            if self.used:self.refuse('material capture is single use')
            self.used=True
            self.result={'schema':'ontokin.c248.native-materials/0.1','phase':'CAPTURING','component_complete':False,
                         'execution_admission':False,'native_acceptance':False,'R07':'PENDING','value_origin':'native-api-readback','parts':[]}
            self.mesh_calls+=1
            arrays=self.mesh_reader.capture(registry,state,root)
            self.result['mesh_arrays']=arrays
            self.check(arrays.get('component_complete') is True and arrays.get('phase')=='MESH_ARRAYS_CAPTURED_OTHER_RAW_PENDING',
                       'owned mesh-array capture refused')
            meshes=self.live_meshes(root,arrays)
            self.check(not registry.faults,'registry fault before material capture')
            seen={}
            for i,part in enumerate(arrays['parts']):
                row={'source_node':i,'source_mesh':part['source_mesh'],'source_primitive':0,
                     'source_material':MATERIAL_BY_MESH[part['source_mesh']],
                     'native_node_instance_id':part['native_node_instance_id'],'native_surface':0}
                self.result['parts'].append(row);row['snapshot']={}
                self.surface(meshes[i],part,row['snapshot'])
                mat=row['snapshot']['material'];identity=mat['identity']['instance_id']
                value={'source_material':row['source_material'],'material':mat}
                self.check(identity not in seen or seen[identity]==value,'conflicting material sharing')
                seen[identity]=deepcopy(value)
            for i,part in enumerate(arrays['parts']):
                after={}
                try:
                    self.surface(meshes[i],part,after)
                    self.check(after==self.result['parts'][i]['snapshot'],'material or selection changed')
                except Refusal:
                    self.result['parts'][i]['after_drift']=after
                    raise
            self.live_meshes(root,arrays)
            self.check(not registry.faults,'registry changed during material capture')
            self.result.update(phase='MATERIAL_PARAMETERS_CAPTURED_OTHER_RAW_PENDING',component_complete=True,
                               native_material_count=len(seen),stability='two equal material reads and final membership; not atomic against concurrent writes')
        except Refusal:pass
        self.result['errors']=self.errors[:]
        return deepcopy(self.result)


def synthetic_fixture():
    registry,state,root=c247.synthetic_fixture()
    materials=[MaterialView(5000),MaterialView(5001,color=ColorValue(0.25,0.5,0.75,0.875),metallic=0.0,roughness=1.0)]
    for i,node in enumerate(root.children):
        node.mesh.surface_material=materials[MATERIAL_BY_MESH[MESHES[i]]]
        node.material_override=None;node.material_overlay=None;node.surface_override=None
        node.instance_transparency=0.0;node.surface_override_count=1
        node.override_active=False;node.active_override=None
    return registry,state,root
