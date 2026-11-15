"""Read-only pinned API, source, authority, original fixture and lexical checks.

This does not parse GDScript, run native code, evaluate poses or compare key values.
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


def verify(package,author=None):
    bindings=json.loads((HERE/'BINDINGS.json').read_text())
    checks=[];retained={}
    def check(name,value):
        if not value:raise ValueError(name)
        checks.append(name)
    for row in bindings['sources']:
        path=package/row['packagePath']
        if row['group']=='author' and author is not None:path=author/row['name']
        b=path.read_bytes()
        check('length '+row['name'],len(b)==row['bytes'])
        check('sha256 '+row['name'],hashlib.sha256(b).hexdigest()==row['sha256'])
        check('blob '+row['name'],hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['gitBlobSha1'])
        retained[row['name']]=b
    for row in bindings['authority']:
        check('authority '+row['path'],hashlib.sha256((REPO/row['path']).read_bytes()).hexdigest()==row['sha256'])
    xml={k:ET.fromstring(v) for k,v in retained.items() if k.endswith('.xml')}
    check('AnimationPlayer inherits mixer',xml['AnimationPlayer.xml'].get('inherits')=='AnimationMixer')
    methods={
      'Animation.xml':{'get_track_count':'int','get_marker_names':'PackedStringArray','track_get_type':'int','track_get_path':'NodePath',
                       'track_is_enabled':'bool','track_is_imported':'bool','track_is_compressed':'bool','track_get_interpolation_type':'int',
                       'track_get_interpolation_loop_wrap':'bool','track_get_key_count':'int'},
      'AnimationPlayer.xml':{'is_playing':'bool','has_section':'bool','get_queue':'StringName[]','animation_get_next':'StringName','get_blend_time':'float'},
      'AnimationMixer.xml':{'get_animation_library_list':'StringName[]','get_animation_list':'PackedStringArray','get_animation_library':'AnimationLibrary','get_animation':'Animation'},
      'AnimationLibrary.xml':{'get_animation_list':'StringName[]','get_animation_list_size':'int','get_animation':'Animation'},
      'NodePath.xml':{'is_absolute':'bool','is_empty':'bool','get_subname_count':'int'},'StringName.xml':{'is_empty':'bool'},
      'Node.xml':{'get_node_or_null':'Node','get_children':'Node[]','get_parent':'Node','get_path_to':'NodePath','is_inside_tree':'bool'},
      'Object.xml':{'get_instance_id':'int','get_class':'String','get_script':'Variant','get_meta_list':'StringName[]','get_meta':'Variant','is_queued_for_deletion':'bool'},
      'Mesh.xml':{'get_surface_count':'int','surface_get_material':'Material'},
      'MeshInstance3D.xml':{'get_surface_override_material_count':'int','get_surface_override_material':'Material','get_active_material':'Material'}}
    cpp_for={'Animation.xml':'animation.cpp','AnimationPlayer.xml':'animation_player.cpp','AnimationMixer.xml':'animation_mixer.cpp',
             'AnimationLibrary.xml':'animation_library.cpp','Node.xml':'node.cpp','MeshInstance3D.xml':'mesh_instance_3d.cpp'}
    for filename,entries in methods.items():
        for name,kind in entries.items():
            node=xml[filename].find('./methods/method[@name="'+name+'"]')
            check('API '+filename+' '+name,node is not None and node.find('return').get('type')==kind)
            if filename in cpp_for:
                check('native binding '+filename+' '+name,'D_METHOD("'+name+'"' in retained[cpp_for[filename]].decode())
    properties={
      'Animation.xml':{'length':'float','step':'float','loop_mode':'int','capture_included':'bool'},
      'AnimationPlayer.xml':{'autoplay':'StringName','assigned_animation':'StringName','current_animation':'StringName',
                             'speed_scale':'float','playback_default_blend_time':'float','playback_auto_capture':'bool'},
      'AnimationMixer.xml':{'root_node':'NodePath','active':'bool','callback_mode_process':'int','callback_mode_method':'int',
                            'callback_mode_discrete':'int','deterministic':'bool','root_motion_track':'NodePath','root_motion_local':'bool'},
      'Resource.xml':{'resource_name':'String','resource_path':'String'},'Node.xml':{'name':'StringName','owner':'Node'},
      'MeshInstance3D.xml':{'mesh':'Mesh'},'GeometryInstance3D.xml':{'material_override':'Material','material_overlay':'Material','transparency':'float'}}
    for filename,entries in properties.items():
        for name,kind in entries.items():
            node=xml[filename].find('./members/member[@name="'+name+'"]')
            check('property '+filename+' '+name,node is not None and node.get('type')==kind)
            if filename in cpp_for:
                check('property getter '+filename+' '+name,'D_METHOD("'+node.get('getter')+'"' in retained[cpp_for[filename]].decode())
    for filename,entries in {'Animation.xml':{'TYPE_POSITION_3D':1,'TYPE_ROTATION_3D':2,'INTERPOLATION_LINEAR':1,'LOOP_NONE':0},
        'AnimationMixer.xml':{'ANIMATION_CALLBACK_MODE_PROCESS_IDLE':1,'ANIMATION_CALLBACK_MODE_METHOD_DEFERRED':0,'ANIMATION_CALLBACK_MODE_DISCRETE_RECESSIVE':1}}.items():
        for name,val in entries.items():
            n=xml[filename].find('./constants/constant[@name="'+name+'"]');check('enum '+name,n is not None and int(n.get('value'))==val)
    for name,default in {'active':'true','callback_mode_process':'1','callback_mode_method':'0','callback_mode_discrete':'1','deterministic':'false','root_motion_local':'false'}.items():
        check('mixer default '+name,xml['AnimationMixer.xml'].find('./members/member[@name="'+name+'"]').get('default')==default)
    for name,default in {'speed_scale':'1.0','playback_default_blend_time':'0.0','playback_auto_capture':'true'}.items():
        check('player default '+name,xml['AnimationPlayer.xml'].find('./members/member[@name="'+name+'"]').get('default')==default)
    gltf=retained['gltf_document.cpp'].decode();mixer=retained['animation_mixer.cpp'].decode();node_cpp=retained['node.cpp'].decode()
    generation=gltf.split('Node *GLTFDocument::generate_scene(',1)[1].split('Error GLTFDocument::',1)[0]
    check('imported player constructed once',generation.count('memnew(AnimationPlayer)')==1 and 'godot_root_node->add_child(anim_player, true)' in generation)
    check('one import call per state animation','i < p_state->animations.size()' in generation and '_import_animation(p_state, anim_player, i,' in generation)
    imported=gltf.split('void GLTFDocument::_import_animation(',1)[1].split('void GLTFDocument::_convert_mesh_instances',1)[0]
    check('default library object association','p_animation_player->add_animation_library("", library)' in imported and 'library->add_animation(anim_name, animation)' in imported)
    check('transform target built from actual mapped node','scene_root->get_path_to(node_element->value)' in imported and 'transform_node_path = node_path' in imported)
    for typ in ('TYPE_POSITION_3D','TYPE_ROTATION_3D'):
        check('native importer track '+typ,'animation->add_track(Animation::'+typ+')' in imported)
    check('immutable tracks retained condition','if (!p_remove_immutable_tracks || !is_default)' in imported)
    check('source imported flag','animation->track_set_imported(position_idx, true)' in imported and 'animation->track_set_imported(rotation_idx, true)' in imported)
    check('state animation players are export only',all('only used during the export process' in ''.join(xml['GLTFState.xml'].find('./methods/method[@name="'+name+'"]').itertext()) for name in ('get_animation_player','get_animation_players_count')))
    check('actual mixer root resolver','Node *parent = get_node_or_null(root_node)' in mixer)
    check('actual mixer track resolver','Node *child = parent->get_node_and_resource(path, resource, leftover_path)' in mixer)
    resolver=node_cpp.split('Node *Node::get_node_and_resource(',1)[1].split('\n}',1)[0]
    check('node-only resolver delegates','get_node_or_null(p_path)' in resolver and 'subname_count' in resolver)
    check('absolute detached lookup diagnosis','absolute paths from outside the active scene tree.' in node_cpp)
    check('RESET is behavioral key','has_animation(SceneStringName(RESET))' in mixer)
    player=retained['animation_player.cpp'].decode()
    check('current name conditional on playing','return (is_playing() ? playback.assigned : StringName())' in player)
    check('assigned name separate','StringName AnimationPlayer::get_assigned_animation() const {\n\treturn playback.assigned;' in player)
    header=retained['animation.h'].decode()
    check('native default linear loop flags','InterpolationType interpolation = INTERPOLATION_LINEAR' in header and 'bool loop_wrap = true' in header and 'bool enabled = true' in header)
    pin=next(x for x in json.loads((REPO/'docs/engineering/second-target-c220/evidence/INPUT-BINDINGS.json').read_text())['items'] if x['packagePath'].endswith('after.glb'))
    b=(package/pin['packagePath']).read_bytes()
    check('exact original GLB',len(b)==pin['bytes'] and hashlib.sha256(b).hexdigest()==pin['sha256'])
    magic,version,total=struct.unpack_from('<4sII',b);length,kind=struct.unpack_from('<II',b,12)
    check('original GLB framing',magic==b'glTF' and version==2 and total==len(b) and kind==0x4e4f534a)
    fixture=json.loads(b[20:20+length]);binary_len,binary_type=struct.unpack_from('<II',b,20+length);binary=b[28+length:]
    check('binary fixture framing',binary_type==0x004e4942 and len(binary)==binary_len)
    check('single original animation',len(fixture['animations'])==1)
    animation=fixture['animations'][0]
    check('36 original channels and samplers',len(animation['channels'])==36 and len(animation['samplers'])==36)
    check('exact original channel coverage',{(c['target']['node'],c['target']['path']) for c in animation['channels']}=={(i,p) for i in range(18) for p in ('translation','rotation')})
    check('source node mesh map',[n['mesh'] for n in fixture['nodes']]==[0,1,2,3,2,4,2,3,2,3,2,3,2,3,2,3,2,3])
    check('no source transform parents',all('children' not in n and 'matrix' not in n for n in fixture['nodes']))
    for i,sampler in enumerate(animation['samplers']):
        accessor=fixture['accessors'][sampler['input']];view=fixture['bufferViews'][accessor['bufferView']]
        check('linear sampler '+str(i),sampler.get('interpolation')=='LINEAR')
        check('input metadata '+str(i),accessor['componentType']==5126 and accessor['type']=='SCALAR' and accessor['count']==121 and 'sparse' not in accessor and view.get('byteStride',4)==4)
        offset=view.get('byteOffset',0)+accessor.get('byteOffset',0)
        times=struct.unpack_from('<121f',binary,offset)
        check('source duration and times '+str(i),times[0]==0.0 and times[-1]==2.0 and all(a<b for a,b in zip(times,times[1:])))
    source=(HERE/'animation_inventory.gd').read_text();model=(HERE/'inert_model.py').read_text()
    check('fresh owned C248 one call',source.count('MaterialReader.new()')==1 and source.count('material_reader.capture_after_generation_return(state, root)')==1)
    check('no second consumed registry close','Registry.close_state(' not in source)
    check('no source node map or export-only player API',not re.search(r'\.(?:get_nodes|get_scene_node|get_node_index|get_animation_player|get_animation_players_count)\s*\(',source))
    check('no execution playback assignments or key values',not re.search(r'\.(?:seek|advance|play|play_backwards|stop|set_assigned_animation|set_current_animation|set_active|set_callback_mode_process|track_get_key_value|track_get_key_time|generate_scene|append_from_file|save|execute|create_process|set_meta)\s*\(',source))
    check('no native writable property assignments',not re.search(r'\b(?:player|animation|library|root|node|mesh|material)\.\w+\s*=(?!=)',source))
    check('malformed root path rejected before lookup',source.index('root_path.is_absolute()')<source.index('player.get_node_or_null(root_path)') and 'root lookup after unsupported path shape' in source)
    check('reserved RESET refused','animation_key == &"RESET"' in source)
    check('assigned and current are separately captured','_typed(player.assigned_animation)' in source and '_typed(player.current_animation)' in source)
    check('no unassigned position getter','current_animation_position' not in source and 'current_animation_length' not in source)
    check('compressed refused before count',source.index('row["compressed"]["value"]')<source.index('animation.track_get_key_count(index)'))
    check('track target exact observed identity','live["source_by_instance"].has(target.get_instance_id())' in source)
    check('whole-scene queue script and tree guards','row["queued_for_deletion"]' in source and 'row["inside_tree"]' in source and 'unsupported scene member or additional mixer' in source)
    check('partial track before refusals',source.index('out["tracks"].append(row)')<source.index('row["type"]["value"] not in'))
    check('two full inventory comparisons','_result["inventory"] != _result["recheck"]' in source)
    check('final selection identities rechecked','library.get_animation(animation_key) != animation' in source and 'player.get_animation(animation_key) != animation' in source)
    check('result admission remains false','"execution_admission": false' in source and '"native_acceptance": false' in source and '"R07": "PENDING"' in source)
    check('model composes actual unchanged C248','second-target-c248/inert_model.py' in model and 'self.material_reader=c248.Capture()' in model)
    parsed=ast.parse(model)
    for name,value in [('MAX_SCENE_NODES',64),('EXPECTED_TRACKS',36),('MAX_KEYS_PER_TRACK',4096)]:
        found=next(ast.literal_eval(n.value) for n in parsed.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
        check('finite model/source constant '+name,found==value and 'const '+name+': int = '+str(value) in source)
    return {'schema':'ontokin.c249.binding-result/0.1','passed':True,'count':len(checks),'checks':checks,
            'primarySources':len(bindings['sources']),'authorityFiles':len(bindings['authority']),
            'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir()) if p.is_file()},
            'fixture':{'animationCount':1,'sourceAnimationName':animation.get('name'),'channels':36,'nodes':18,'sourceInputSamplesPerTrack':121,'durationSeconds':2},
            'gdscriptParser':'NOT_RUN','native':'NOT_RUN','product':'NOT_RUN','aggregate':'NOT_RUN',
            'limitations':'Exact bytes/API/fixture and lexical checks; no complete static analysis, installed behavior or key/pose fidelity claim'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root',type=Path,required=True)
    parser.add_argument('--author-upstream',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=verify(args.package_root,args.author_upstream)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':result['count'],'sources':result['primarySources'],'native':'NOT_RUN'}))


if __name__=='__main__':main()
