"""Read-only C250 primary-source, inherited-authority and lexical checks.

Python/XML inspection is not a GDScript parser, native start or behavior proof.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def function_text(source, signature):
    return source.split(signature, 1)[1].split('\n}', 1)[0]


def verify(package, supplement=None):
    bindings = json.loads((HERE / 'BINDINGS.json').read_text())
    checks, retained = [], {}

    def check(name, passed):
        if not passed:
            raise ValueError(name)
        checks.append(name)

    for row in bindings['sources']:
        parent = supplement if row['group'] == 'c250-api-review' and supplement else package
        raw = (parent / row['packagePath']).read_bytes()
        check('length ' + row['name'], len(raw) == row['bytes'])
        check('sha256 ' + row['name'], hashlib.sha256(raw).hexdigest() == row['sha256'])
        check('git blob ' + row['name'], hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == row['gitBlobSha1'])
        retained[row['name']] = raw
    for row in bindings['authority']:
        check('authority ' + row['path'], hashlib.sha256((REPO / row['path']).read_bytes()).hexdigest() == row['sha256'])
    xml = {name:ET.fromstring(raw) for name, raw in retained.items() if name.endswith('.xml')}
    expected_methods = {
        'AnimationPlayer.xml': {'is_animation_active':'bool', 'is_playing':'bool'},
        'Object.xml': {'get_signal_connection_list':'Dictionary[]', 'is_blocking_signals':'bool'},
        'Node.xml': {'is_processing_internal':'bool', 'is_physics_processing_internal':'bool'},
    }
    for name, methods in expected_methods.items():
        for method, return_type in methods.items():
            node = xml[name].find('./methods/method[@name="' + method + '"]/return')
            check('public method ' + name + ':' + method, node is not None and node.get('type') == return_type)
    for name in ('current_animation_position', 'current_animation_length', 'assigned_animation'):
        check('public property AnimationPlayer:' + name, xml['AnimationPlayer.xml'].find('./members/member[@name="' + name + '"]') is not None)
    constant = xml['AnimationMixer.xml'].find('./constants/constant[@name="ANIMATION_CALLBACK_MODE_PROCESS_MANUAL"]')
    check('MANUAL public enum value', constant is not None and constant.get('value') == '2')
    mixer, player = retained['animation_mixer.cpp'].decode(), retained['animation_player.cpp'].decode()
    process = function_text(mixer, 'void AnimationMixer::_set_process(bool p_process, bool p_force) {')
    set_mode = function_text(mixer, 'void AnimationMixer::set_callback_mode_process(AnimationCallbackModeProcess p_mode) {')
    active = function_text(mixer, 'void AnimationMixer::set_active(bool p_active) {')
    check('MANUAL does not enable native callback', 'case ANIMATION_CALLBACK_MODE_PROCESS_MANUAL:\n\t\t\tbreak;' in process)
    check('mode setter temporary active restoration', set_mode.index('set_active(false)') < set_mode.index('callback_mode_process = p_mode') < set_mode.index('set_active(true)'))
    check('detached deactivate avoids cache clear', 'if (!active && is_inside_tree())' in active)
    assigned = function_text(player, 'void AnimationPlayer::set_assigned_animation(const StringName &p_animation) {')
    check('assignment playing branch is distinct', 'if (is_playing())' in assigned and 'play(p_animation' in assigned)
    check('stopped assignment sets pointer and zero', 'playback.current.pos = 0;' in assigned and 'playback.current.from = &animation_set[p_animation];' in assigned)
    check('assignment emits inspected signal', 'emit_signal(SNAME("current_animation_changed"), playback.assigned)' in assigned)
    check('public pointer guard exact binding', 'D_METHOD("is_animation_active"), &AnimationPlayer::is_valid' in player)
    check('pointer guard tests resource', 'return (playback.current.from);' in function_text(player, 'bool AnimationPlayer::is_valid() const {'))
    check('stopped current name empty', 'return (is_playing() ? playback.assigned : StringName());' in player)
    for getter in ('position', 'length'):
        check('assigned-only getter guard ' + getter, 'ERR_FAIL_NULL_V_MSG(playback.current.from, 0,' in function_text(player, 'double AnimationPlayer::get_current_animation_' + getter + '() const {'))
    node3d = retained['node_3d.cpp'].decode()
    world = function_text(node3d, 'Transform3D Node3D::get_global_transform() const {')
    check('world getter rejects detached node', 'ERR_FAIL_COND_V(!is_inside_tree(), Transform3D())' in world)
    source = (HERE / 'playback_preparation.gd').read_text()
    model = (HERE / 'inert_model.py').read_text()
    check('one owned C249 capture', source.count('inventory_reader.capture_after_generation_return(state, root)') == 1)
    check('no C246 reconsumption', 'Registry.close_state(' not in source)
    check('no baseline recapture in boundary helper', source.count('.capture_after_generation_return(') == 1)
    check('exact two native setters', source.count('player.set_callback_mode_process(') == 1 and source.count('player.set_assigned_animation(') == 1)
    check('no playback evaluation or attachment', not re.search(r'\.(?:seek|advance|play|play_backwards|stop|set_current_animation|set_active|add_child|reparent|generate_scene|append_from_file|save|execute|create_process|set_meta|set_process_internal|set_physics_process_internal)\s*\(', source))
    check('no world or key payload getter', not re.search(r'\.(?:global_transform|global_position|global_rotation|global_basis|get_global_transform|track_get_key_value|track_get_key_time)\b', source))
    check('no unbound player guard', 'player.is_valid(' not in source and 'player.is_animation_active()' in source)
    check('no native property assignments', not re.search(r'\b(?:player|animation|library|root|node|mesh|material)\.\w+\s*=(?!=)', source))
    check('entire original receipt retained', '_result["animation_inventory"] = inventory' in source)
    check('expected changes are receipt-local', 'original.duplicate(true)' in source and 'expected["player"]["settings"]["assigned_animation"]["value"]' in source)
    check('stage inventory enforces exact other fields', 'out != expected' in source and 'settings != expected["player"]["settings"]' in source)
    check('each attempt is recorded before setter', source.index('_result["mutations"].append(manual)') < source.index('player.set_callback_mode_process(') and source.index('_result["mutations"].append(assignment)') < source.index('player.set_assigned_animation('))
    check('partial attempts preserved', 'REFUSED_AFTER_ATTEMPT' in source and 'never attempted; partial observed changes remain' in source)
    check('position guard precedes first read', source.index('player.is_animation_active()') < source.index('player.current_animation_position'))
    check('signal count and payload omission', 'get_signal_connection_list(&"current_animation_changed")' in source and 'signal Callable payload; every receiver refuses' in source)
    check('both independent process flags observed', 'player.is_processing_internal()' in source and 'player.is_physics_processing_internal()' in source)
    check('late signal state retained', 'control["final_blocking_signals"] = reader._typed(player.is_blocking_signals())' in source and 'control["final_omitted"]' in source)
    check('final assigned getter guard retained', source.index('control["final_animation_active"]["value"] != assigned') < source.index('control["final_position"] =') and 'control["final_length"] =' in source)
    check('inherited scene refusal retains partial readback', 'except c249.Refusal:\n            out[\'scene_after_drift\']' in model and 'out["scene_after_drift"] = final_scene' in source)
    check('admission remains pending', '"execution_admission": false' in source and '"native_acceptance": false' in source and '"R07": "PENDING"' in source)
    check('model composes pinned C249', 'second-target-c249/inert_model.py' in model and 'self.inventory_reader = c249.Capture()' in model)
    inherited_path = HERE.parent / 'second-target-c249/verify_bindings.py'
    spec = importlib.util.spec_from_file_location('c250_inherited_binding_verifier', inherited_path)
    inherited = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inherited)
    inherited_result = inherited.verify(package)
    check('complete inherited binding and original fixture verification', inherited_result['passed'])
    return {'schema':'ontokin.c250.binding-result/0.1', 'passed':True, 'checks':checks, 'count':len(checks),
            'primarySources':len(bindings['sources']), 'authorityFiles':len(bindings['authority']),
            'inheritedC249':{'passed':True, 'checks':inherited_result['count'], 'fixture':inherited_result['fixture']},
            'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir()) if p.is_file()},
            'gdscriptParser':'NOT_RUN', 'native':'NOT_RUN', 'product':'NOT_RUN', 'aggregate':'NOT_RUN',
            'limitations':'Exact bytes, public bindings and lexical controls; no full static analysis, native execution or installed lineage proof'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', type=Path, required=True)
    parser.add_argument('--supplement-root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.package_root, args.supplement_root)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed':result['passed'], 'checks':result['count'], 'inheritedChecks':result['inheritedC249']['checks'], 'native':'NOT_RUN'}))


if __name__ == '__main__':
    main()
