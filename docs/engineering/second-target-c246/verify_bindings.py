"""Read-only C246 upstream/authority/fixture and lexical-source checks.

This uses Python XML/JSON readers, not Godot or a GDScript parser. It launches no
process, regenerates no fixture, and establishes no installed native behavior.
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
MESHES = [0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', required=True, type=Path)
    parser.add_argument('--author-upstream', type=Path)
    parser.add_argument('--review-upstream', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    bindings = json.loads((HERE/'BINDINGS.json').read_text())
    inherited = json.loads((REPO/bindings['inheritedInventory']).read_text())
    checks = []
    def check(name, condition):
        if not condition:
            raise ValueError(name)
        checks.append(name)
    retained = {}
    for record in inherited['sources'] + bindings['sources']:
        file = args.package_root/record['packagePath']
        override = args.author_upstream if record.get('group') == 'author' else args.review_upstream
        if 'group' in record and override is not None:
            file = override/record['name']
        blob = file.read_bytes()
        check('bytes '+record['packagePath'], len(blob) == record['bytes'])
        check('sha256 '+record['packagePath'], hashlib.sha256(blob).hexdigest() == record['sha256'])
        check('git blob '+record['packagePath'], hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest() == record['gitBlobSha1'])
        retained[file.name] = blob
    for record in inherited['authorityDocuments'] + bindings['authority']:
        check('authority '+record['path'], hashlib.sha256((REPO/record['path']).read_bytes()).hexdigest() == record['sha256'])
    methods = {
        'Object.xml': ('get_instance_id','get_class','get_meta_list','get_meta','get_script','get_property_list',
                       'get_signal_list','get_signal_connection_list','get_incoming_connections','connect','disconnect','is_connected','get'),
        'Callable.xml': ('bind','get_object_id','get_method','get_bound_arguments','get_unbound_arguments_count','is_custom','is_valid'),
        'Signal.xml': ('get_object_id','get_name'),
        'Node.xml': ('get_parent','get_children','get_path_to'),
        'GLTFState.xml': ('get_nodes','get_scene_node','get_node_index'),
        'GLTFDocumentExtension.xml': ('_import_node',),
        '@GlobalScope.xml': ('is_instance_valid','is_instance_id_valid','instance_from_id','is_finite'),
    }
    xml = {name: ET.fromstring(blob) for name,blob in retained.items() if name.endswith('.xml')}
    for filename,names in methods.items():
        for name in names:
            check('pinned API '+filename+' '+name, xml[filename].find('./methods/method[@name="'+name+'"]') is not None)
    for filename,name,kind in (('Node.xml','owner','Node'),('GLTFNode.xml','mesh','int'),
                               ('ImporterMeshInstance3D.xml','mesh','ImporterMesh'),('Resource.xml','resource_path','String')):
        entry=xml[filename].find('./members/member[@name="'+name+'"]')
        check('pinned member '+filename+' '+name, entry is not None and entry.get('type')==kind)
    hook=xml['GLTFDocumentExtension.xml'].find('./methods/method[@name="_import_node"]')
    check('exact callback signature', [p.get('type') for p in hook.findall('param')]==['GLTFState','GLTFNode','Dictionary','Node'])
    signal=xml['Node.xml'].find('./signals/signal[@name="replacing_by"]')
    check('exact replacement signal', signal is not None and [p.get('type') for p in signal.findall('param')]==['Node'])
    check('native JSON double source', b'double number = String::to_float' in retained['json.cpp'] and b'r_token.value = number' in retained['json.cpp'])
    glb_pin = next(r for r in json.loads((REPO/'docs/engineering/second-target-c220/evidence/INPUT-BINDINGS.json').read_text())['items'] if r['packagePath'].endswith('after.glb'))
    blob=(args.package_root/glb_pin['packagePath']).read_bytes()
    check('original GLB exact bytes',len(blob)==glb_pin['bytes'] and hashlib.sha256(blob).hexdigest()==glb_pin['sha256'])
    magic,version,size=struct.unpack_from('<4sII',blob)
    length,kind=struct.unpack_from('<II',blob,12)
    check('GLB framing',magic==b'glTF' and version==2 and size==len(blob) and kind==0x4e4f534a)
    document=json.loads(blob[20:20+length])
    check('locked 18 node/mesh pairs',[row['mesh'] for row in document['nodes']]==MESHES)
    check('locked root set',document['scenes'][document.get('scene',0)]['nodes']==list(range(18)))
    scripts={p.name:p.read_text() for p in HERE.glob('*.gd')}
    check('stateless single extension override',re.findall(r'^func (\w+)\(',scripts['observer.gd'],re.M)==['_import_node'] and not re.search(r'^var\s',scripts['observer.gd'],re.M))
    session=scripts['session.gd']
    capture=session.split('func capture_original(',1)[1].split('func _root_replacing(',1)[0]
    remainder=session.replace(capture,'')
    check('map reads confined to preconversion function',session.count('.get_scene_node(')==1 and session.count('.get_node_index(')==1 and '.get_scene_node(' not in remainder and '.get_node_index(' not in remainder)
    check('phase guard before map read',capture.index('_phase != "CAPTURING"')<capture.index('state.get_node_index('))
    check('node facts before direct connection',capture.index('_capture_facts(node, root)')<capture.index('node.connect(&"replacing_by", callback, 0)'))
    check('JSON double without truncation','typeof(raw_mesh) != TYPE_FLOAT' in capture and 'raw_mesh != float(MESHES[index])' in capture and 'int(raw_mesh)' not in capture)
    all_source='\n'.join(scripts.values())
    check('no product writes or launch/registration calls',not re.search(r'\.(?:set_meta|set_script|set_mesh|generate_scene|append_from_file|register_gltf_document_extension|save|execute|create_process)\s*\(',all_source))
    report={'schema':'ontokin.c246.static-binding-result/0.1','passed':True,'checks':checks,'count':len(checks),
            'pinnedSources':len(inherited['sources'])+len(bindings['sources']),'authorityDocuments':len(inherited['authorityDocuments'])+len(bindings['authority']),
            'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*')) if p.is_file()},
            'gdscriptParser':'NOT_RUN','native':'NOT_RUN','product':'NOT_RUN','aggregate':'NOT_RUN',
            'limits':'Hash/XML/fixture and lexical inspection only; not native execution or full static analysis'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(checks),'sources':report['pinnedSources'],'native':'NOT_RUN'}))


if __name__=='__main__':
    main()
