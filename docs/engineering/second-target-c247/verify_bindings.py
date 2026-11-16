"""Verify preserved primary sources, unchanged authority, fixture shape and finite API claims.

This checks Python/XML/JSON/text only. It is not a GDScript parser or a native
run; lexical assertions do not prove source correctness or installed lineage.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MESHES = [0,1,2,3,2,4,2,3,2,3,2,3,2,3,2,3,2,3]


def verify(package, upstream=None):
    bindings=json.loads((HERE/'BINDINGS.json').read_text())
    inherited=json.loads((REPO/bindings['inheritedInventory']).read_text())
    checks=[]
    def check(name,condition):
        if not condition:raise ValueError(name)
        checks.append(name)
    retained={}
    sources=inherited['sources']+bindings['sources']+bindings['inheritedApiSources']
    for row in sources:
        path=package/row['packagePath']
        if upstream is not None and row in bindings['sources']:path=upstream/row['name']
        data=path.read_bytes()
        check('bytes '+row['packagePath'],len(data)==row['bytes'])
        check('sha256 '+row['packagePath'],hashlib.sha256(data).hexdigest()==row['sha256'])
        check('git blob '+row['packagePath'],hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['gitBlobSha1'])
        retained[path.name]=data
    for row in bindings['authority']:
        check('authority '+row['path'],hashlib.sha256((REPO/row['path']).read_bytes()).hexdigest()==row['sha256'])
    xml={name:ET.fromstring(data) for name,data in retained.items() if name.endswith('.xml')}
    methods={
        'ArrayMesh.xml':{'surface_get_format':'int','surface_get_primitive_type':'int',
                         'surface_get_array_len':'int','surface_get_array_index_len':'int','get_blend_shape_count':'int'},
        'Mesh.xml':{'surface_get_arrays':'Array','get_surface_count':'int'},
        'RenderingServer.xml':{'mesh_get_surface':'Dictionary'},
        'Resource.xml':{'get_rid':'RID'},
        'Node.xml':{'get_children':'Node[]','get_parent':'Node'},
        '@GlobalScope.xml':{'is_instance_valid':'bool','is_finite':'bool','mini':'int'},
    }
    for filename,names in methods.items():
        for name,kind in names.items():
            entry=xml[filename].find('./methods/method[@name="'+name+'"]')
            check('API '+filename+' '+name,entry is not None and entry.find('return').get('type')==kind)
    constants={'Mesh.xml':{'ARRAY_MAX':13,'ARRAY_VERTEX':0,'ARRAY_NORMAL':1,'ARRAY_TANGENT':2,'ARRAY_INDEX':12,
                            'PRIMITIVE_TRIANGLES':3,'ARRAY_FORMAT_VERTEX':1,'ARRAY_FORMAT_NORMAL':2,
                            'ARRAY_FORMAT_TANGENT':4,'ARRAY_FORMAT_INDEX':4096},
               'RenderingServer.xml':{'ARRAY_FLAG_FORMAT_CURRENT_VERSION':1<<35,'ARRAY_FLAG_FORMAT_VERSION_SHIFT':35},
               '@GlobalScope.xml':{'TYPE_ARRAY':28,'TYPE_PACKED_BYTE_ARRAY':29,'TYPE_PACKED_INT32_ARRAY':30,
                                   'TYPE_PACKED_FLOAT32_ARRAY':32,'TYPE_PACKED_VECTOR3_ARRAY':36}}
    for filename,names in constants.items():
        for name,value in names.items():
            element=xml[filename].find('./constants/constant[@name="'+name+'"]')
            check('constant '+name,element is not None and int(element.get('value'))==value)
    for filename,name,kind in [('MeshInstance3D.xml','mesh','Mesh'),('ArrayMesh.xml','shadow_mesh','ArrayMesh')]:
        entry=xml[filename].find('./members/member[@name="'+name+'"]')
        check('member '+filename+' '+name,entry is not None and entry.get('type')==kind)
    engine={name:data.decode() for name,data in retained.items() if name.endswith(('.cpp','.h'))}
    check('primitive order to importer surface','for (int j = 0; j < primitives.size(); j++)' in engine['gltf_document.cpp'] and 'import_mesh->add_surface(primitive, array, morphs,' in engine['gltf_document.cpp'])
    check('surface order to cached ArrayMesh','for (int i = 0; i < surfaces.size(); i++)' in engine['importer_mesh.cpp'] and 'mesh->add_surface_from_arrays(surfaces[i].primitive, surfaces[i].arrays' in engine['importer_mesh.cpp'])
    check('native replacement resource assignment','mesh_instance_node_3d->set_mesh(array_mesh)' in engine['gltf_document_extension_convert_importer_mesh.cpp'])
    check('bound raw surface API','D_METHOD("mesh_get_surface", "mesh", "surface")' in engine['rendering_server.cpp'])
    check('native auxiliary tangent storage','// We must use tangents if using normals.' in engine['rendering_server.cpp'])
    check('native decoded normals','w[j] = Vector3::octahedron_decode(' in engine['rendering_server.cpp'])
    check('public surface_get_lods absent from Mesh','D_METHOD("surface_get_lods"' not in engine['mesh.cpp'])
    pin=next(row for row in json.loads((REPO/'docs/engineering/second-target-c220/evidence/INPUT-BINDINGS.json').read_text())['items'] if row['packagePath'].endswith('after.glb'))
    data=(package/pin['packagePath']).read_bytes()
    check('original GLB bytes',len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'])
    magic,version,size=struct.unpack_from('<4sII',data);length,ctype=struct.unpack_from('<II',data,12)
    check('original GLB framing',magic==b'glTF' and version==2 and size==len(data) and ctype==0x4e4f534a)
    gltf=json.loads(data[20:20+length])
    check('18 source-node mesh joins',[n['mesh'] for n in gltf['nodes']]==MESHES)
    check('five original mesh definitions',len(gltf['meshes'])==5)
    for i,mesh in enumerate(gltf['meshes']):
        check('one primitive '+str(i),len(mesh['primitives'])==1)
        primitive=mesh['primitives'][0]
        check('indexed POSITION NORMAL TRIANGLES '+str(i),primitive.get('mode',4)==4 and 'indices' in primitive and set(primitive['attributes'])=={'POSITION','NORMAL'})
        check('no morph targets '+str(i),'targets' not in primitive)
    check('no source skins','skins' not in gltf and all('skin' not in n for n in gltf['nodes']))
    part_map=json.loads((REPO/'docs/engineering/second-target-c220/evidence/PART-MAP.json').read_text())
    check('source authority node joins',sorted(row['glbNode'] for row in part_map['entries'])==list(range(18)))
    check('source authority mesh joins',all(row['glbMesh']==MESHES[row['glbNode']] for row in part_map['entries']))
    script=(HERE/'mesh_arrays.gd').read_text()
    check('trusted receipt before native traversal',script.index('Registry.close_state(state)')<script.index('var meshes: Dictionary = _live_meshes(root, chain)'))
    check('no stale map calls',not re.search(r'\.(?:get_scene_node|get_node_index|get_nodes)\s*\(',script))
    check('no source numeric repair or launch',not re.search(r'\.(?:set_meta|set_script|set_mesh|set_transform|normalized|normalize|generate_scene|append_from_file|register_gltf_document_extension|save|execute|create_process)\s*\(',script))
    check('bound raw dictionary not unbound LOD call','RenderingServer.mesh_get_surface(mesh.get_rid(), 0)' in script and '.surface_get_lods(' not in script)
    check('detached arrays without JSON conversion','.duplicate()' in script and 'JSON.' not in script and 'to_byte_array(' not in script)
    check('exact native flags include current version','RenderingServer.ARRAY_FLAG_FORMAT_CURRENT_VERSION' in script and 'out["format"] != EXPECTED_FORMAT' in script)
    check('partial slot lengths retained before cross checks',script.index('out["slot_lengths"] = lengths')<script.index('if arrays.size() != Mesh.ARRAY_MAX'))
    check('full values checked for lasting drift','after != _result["parts"][index]["snapshot"]' in script)
    check('non-admission result remains explicit','"execution_admission": false' in script and '"native_acceptance": false' in script and '"R07": "PENDING"' in script)
    return {'schema':'ontokin.c247.static-bindings-result/0.1','passed':True,'checks':checks,'count':len(checks),
            'pinnedSources':len(sources),'uniqueSourceBasenames':len(retained),'authorityDocuments':len(bindings['authority']),
            'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir()) if p.is_file()},
            'gdscriptParser':'NOT_RUN','native':'NOT_RUN','product':'NOT_RUN','aggregate':'NOT_RUN',
            'limits':'Hash/XML/fixture/lexical checks only; not native proof or full static analysis'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root',required=True,type=Path)
    parser.add_argument('--author-upstream',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=verify(args.package_root,args.author_upstream)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':result['count'],'sources':result['pinnedSources'],'native':'NOT_RUN'}))


if __name__=='__main__':main()
