"""Read-only C248 primary-source/API/authority/fixture and lexical checks.

No GDScript parsing, native process, fixture regeneration or numerical material
comparison occurs. Exact source/hash checks do not establish installed lineage.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
MESHES=[0,1,2,3,2,4,2,3,2,3,2,3,2,3,2,3,2,3]
MATERIAL_BY_MESH=[0,0,1,1,1]


def assigned(path,name):
    for node in ast.parse(path.read_text()).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('Missing constant '+name)


def verify(package,author=None,review=None):
    data=json.loads((HERE/'BINDINGS.json').read_text())
    checks=[]
    def check(name,value):
        if not value:raise ValueError(name)
        checks.append(name)
    sources=data['sources']+data['inheritedAndReviewSources']
    retained={}
    for row in sources:
        path=package/row['packagePath']
        if row['group']=='author' and author is not None:path=author/row['name']
        if row['group']=='independent-review' and review is not None:path=review/row['name']
        content=path.read_bytes()
        check('bytes '+row['packagePath'],len(content)==row['bytes'])
        check('sha256 '+row['packagePath'],hashlib.sha256(content).hexdigest()==row['sha256'])
        check('blob '+row['packagePath'],hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()==row['gitBlobSha1'])
        retained[path.name]=content
    for row in data['authority']:
        check('authority '+row['path'],hashlib.sha256((REPO/row['path']).read_bytes()).hexdigest()==row['sha256'])
    xml={name:ET.fromstring(b) for name,b in retained.items() if name.endswith('.xml')}
    check('StandardMaterial3D inherits BaseMaterial3D',xml['StandardMaterial3D.xml'].get('inherits')=='BaseMaterial3D')
    methods={'BaseMaterial3D.xml':{'get_feature':'bool','get_flag':'bool','get_texture':'Texture2D'},
             'MeshInstance3D.xml':{'get_active_material':'Material','get_surface_override_material':'Material','get_surface_override_material_count':'int'},
             'Mesh.xml':{'surface_get_material':'Material','get_surface_count':'int'},
             'Object.xml':{'get_instance_id':'int','get_class':'String','get_script':'Variant','get':'Variant'},
             'Node.xml':{'get_children':'Node[]','get_parent':'Node'},
             '@GlobalScope.xml':{'is_instance_valid':'bool','is_finite':'bool'}}
    for filename,items in methods.items():
        for name,kind in items.items():
            node=xml[filename].find('./methods/method[@name="'+name+'"]')
            check('API '+filename+' '+name,node is not None and node.find('return').get('type')==kind)
    properties={'BaseMaterial3D.xml':{'albedo_color':'Color','metallic':'float','roughness':'float','cull_mode':'int','transparency':'int'},
                'Material.xml':{'next_pass':'Material','render_priority':'int'},
                'GeometryInstance3D.xml':{'material_override':'Material','material_overlay':'Material','transparency':'float'},
                'MeshInstance3D.xml':{'mesh':'Mesh'}}
    settings=assigned(HERE/'inert_model.py','SETTINGS')
    for name,value in settings.items():
        if name!='render_priority':properties['BaseMaterial3D.xml'][name]={bool:'bool',int:'int',float:'float'}[type(value)]
    for filename,items in properties.items():
        implementation=retained['visual_instance_3d.cpp' if filename=='GeometryInstance3D.xml' else
                                'mesh_instance_3d.cpp' if filename=='MeshInstance3D.xml' else 'material.cpp'].decode()
        for name,kind in items.items():
            node=xml[filename].find('./members/member[@name="'+name+'"]')
            check('property '+filename+' '+name,node is not None and node.get('type')==kind)
            getter=node.get('getter')
            check('bound getter '+getter,'D_METHOD("'+getter+'"' in implementation)
    constants={'FEATURE_MAX':13,'FLAG_MAX':25,'TEXTURE_MAX':19,'FLAG_USE_TEXTURE_REPEAT':16,
               'CULL_BACK':0,'CULL_FRONT':1,'CULL_DISABLED':2,'TRANSPARENCY_DISABLED':0,
               'TRANSPARENCY_ALPHA':1,'TRANSPARENCY_ALPHA_SCISSOR':2}
    for name,value in constants.items():
        node=xml['BaseMaterial3D.xml'].find('./constants/constant[@name="'+name+'"]')
        check('constant '+name,node is not None and int(node.get('value'))==value)
    for group,count in [('Feature',13),('Flags',25),('TextureParam',19)]:
        values={int(n.get('value')) for n in xml['BaseMaterial3D.xml'].findall('constants/constant') if n.get('enum')==group and not n.get('name').endswith('_MAX')}
        check('complete contiguous enum '+group,values==set(range(count)))
    material_cpp=retained['material.cpp'].decode();header=retained['material.h'].decode()
    for token in ['return albedo;','return metallic;','return roughness;','return cull_mode;','return transparency;']:
        check('stored getter '+token,token in material_cpp)
    check('native defaults and repeat flag','bool flags[FLAG_MAX] = {}' in header and 'bool features[FEATURE_MAX] = {}' in header and 'flags[FLAG_USE_TEXTURE_REPEAT] = true' in material_cpp)
    selection=retained['mesh_instance_3d.cpp'].decode().split('Ref<Material> MeshInstance3D::get_active_material',1)[1].split('void MeshInstance3D::_mesh_changed',1)[0]
    check('native selection precedence',selection.index('get_material_override()')<selection.index('get_surface_override_material(p_surface)')<selection.index('m->surface_get_material(p_surface)'))
    gltf=retained['gltf_document.cpp'].decode()
    check('source StandardMaterial3D','Ref<StandardMaterial3D> material;' in gltf)
    check('source albedo transfer','Color(arr[0], arr[1], arr[2], arr[3]).linear_to_srgb()' in gltf and 'material->set_albedo(c)' in gltf)
    color=retained['color.h'].decode().split('Color linear_to_srgb()',1)[1].split('}',1)[0]
    check('source color transfer keeps alpha',re.search(r'\ba\s*\)',color) is not None)
    check('ordered native surface material','mesh->surface_set_material(mesh->get_surface_count() - 1, surfaces[i].material)' in retained['importer_mesh.cpp'].decode())
    check('C234 predeclared storage label',assigned(REPO/'tools/second_target_c234/check_materials.py','ALBEDO_STORAGE')=='srgb-rgb-linear-alpha')
    pin=next(x for x in json.loads((REPO/'docs/engineering/second-target-c220/evidence/INPUT-BINDINGS.json').read_text())['items'] if x['packagePath'].endswith('after.glb'))
    blob=(package/pin['packagePath']).read_bytes()
    check('exact original GLB',len(blob)==pin['bytes'] and hashlib.sha256(blob).hexdigest()==pin['sha256'])
    magic,version,size=struct.unpack_from('<4sII',blob);length,ctype=struct.unpack_from('<II',blob,12)
    check('GLB framing',magic==b'glTF' and version==2 and size==len(blob) and ctype==0x4e4f534a)
    fixture=json.loads(blob[20:20+length])
    check('18 native source associations',[n['mesh'] for n in fixture['nodes']]==MESHES)
    check('five source meshes',len(fixture['meshes'])==5)
    for i,mesh in enumerate(fixture['meshes']):
        check('one original primitive '+str(i),len(mesh['primitives'])==1)
        check('primitive material association '+str(i),mesh['primitives'][0]['material']==MATERIAL_BY_MESH[i])
    check('two original source materials',len(fixture['materials'])==2)
    for i,material in enumerate(fixture['materials']):
        check('finite source material fields '+str(i),set(material)=={'name','pbrMetallicRoughness'} and
              set(material['pbrMetallicRoughness'])=={'baseColorFactor','metallicFactor','roughnessFactor'})
    check('source texture and extension absence',not any(k in fixture for k in ['textures','images','extensionsUsed','extensionsRequired']))
    map_rows=json.loads((REPO/'docs/engineering/second-target-c220/evidence/PART-MAP.json').read_text())['entries']
    check('source authority node mesh joins',sorted(x['glbNode'] for x in map_rows)==list(range(18)) and all(x['glbMesh']==MESHES[x['glbNode']] for x in map_rows))
    script=(HERE/'materials.gd').read_text()
    check('fresh private C247 reader once',script.count('MeshReader.new()')==1 and script.count('mesh_reader.capture_after_generation_return(state, root)')==1)
    check('no second registry close or caller receipt','Registry.close_state(' not in script and 'func capture_after_generation_return(state: GLTFState, root: Node)' in script)
    check('no stale loader map',not re.search(r'\.(?:get_nodes|get_scene_node|get_node_index)\s*\(',script))
    check('no native writes launches conversions or serialization',not re.search(r'\.(?:set_meta|set_script|set_mesh|set_albedo|set_metallic|set_roughness|set_texture|set_feature|set_flag|generate_scene|append_from_file|save|execute|create_process|linear_to_srgb|srgb_to_linear)\s*\(',script) and 'JSON.' not in script)
    check('same captured script and next-pass references','if captured_script != null' in script and 'if captured_next_pass != null' in script and script.count('native.next_pass')==1)
    check('instance transparency raw guard','out["instance_transparency"] = _typed(node.transparency)' in script and 'out["instance_transparency"]["value"] != 0.0' in script)
    check('raw repeated material consistency','seen_materials[identity]["source_material"] != row["source_material"]' in script and 'seen_materials[identity]["material"] != material' in script)
    check('partial record before reads',script.index('_result["parts"].append(row)')<script.index('row["snapshot"] = _surface(meshes[index], part)'))
    check('two complete material readbacks','after != _result["parts"][index]["snapshot"]' in script)
    check('no admission on component success','"execution_admission": false' in script and '"native_acceptance": false' in script and '"R07": "PENDING"' in script)
    return {'schema':'ontokin.c248.binding-result/0.1','passed':True,'count':len(checks),'checks':checks,
            'pinnedSources':len(sources),'authorityDocuments':len(data['authority']),
            'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir()) if p.is_file()},
            'gdscriptParser':'NOT_RUN','native':'NOT_RUN','product':'NOT_RUN','aggregate':'NOT_RUN',
            'limits':'Primary hash/API/fixture/lexical checks; not complete static analysis or installed behavior'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root',type=Path,required=True)
    parser.add_argument('--author-upstream',type=Path)
    parser.add_argument('--review-upstream',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=verify(args.package_root,args.author_upstream,args.review_upstream)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':result['count'],'sources':result['pinnedSources'],'native':'NOT_RUN'}))


if __name__=='__main__':main()
