"""Inspect C251 pinned bytes, public APIs, explicit scene predicate and scope.

This is Python/XML and lexical inspection, never a GDScript/native parser.
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


def verify(package, new_source_root=None):
    bindings = json.loads((HERE / 'BINDINGS.json').read_text())
    checks, retained = [], {}

    def check(name, passed):
        if not passed:
            raise ValueError(name)
        checks.append(name)

    for row in bindings['sources']:
        path = package / row['packagePath']
        if row['group'] == 'c251-api-review' and new_source_root:
            path = new_source_root / row['name']
        raw = path.read_bytes()
        check('length ' + row['name'], len(raw) == row['bytes'])
        check('sha256 ' + row['name'], hashlib.sha256(raw).hexdigest() == row['sha256'])
        check('git blob ' + row['name'], hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == row['gitBlobSha1'])
        retained[row['name']] = raw
    for row in bindings['authority']:
        check('authority ' + row['path'], hashlib.sha256((REPO / row['path']).read_bytes()).hexdigest() == row['sha256'])
    xml = {name: ET.fromstring(raw) for name, raw in retained.items() if name.endswith('.xml')}
    methods = {
        'Engine.xml': {'get_main_loop': 'MainLoop', 'is_editor_hint': 'bool'},
        'OS.xml': {'get_thread_caller_id': 'int', 'get_main_thread_id': 'int'},
        'SceneTree.xml': {'get_node_count': 'int', 'get_processed_tweens': 'Tween[]'},
        'Node.xml': {name: 'bool' for name in ('is_node_ready', 'is_physics_interpolated', 'can_process',
                    'is_processing', 'is_physics_processing', 'is_processing_internal', 'is_physics_processing_internal',
                    'is_processing_input', 'is_processing_shortcut_input', 'is_processing_unhandled_input', 'is_processing_unhandled_key_input')},
        'Node3D.xml': {'is_set_as_top_level': 'bool', 'is_scale_disabled': 'bool'},
        'Object.xml': {'get_signal_list': 'Dictionary[]', 'get_signal_connection_list': 'Dictionary[]'},
    }
    for name, rows in methods.items():
        for method, return_type in rows.items():
            node = xml[name].find('./methods/method[@name="' + method + '"]/return')
            if node is None:
                node = xml[name].find('./members/member[@getter="' + method + '"]')
            check('public method ' + name + ':' + method, node is not None and node.get('type') == return_type)
    for name, expected_type in {'root': 'Window', 'physics_interpolation': 'bool', 'paused': 'bool', 'current_scene': 'Node'}.items():
        node = xml['SceneTree.xml'].find('./members/member[@name="' + name + '"]')
        check('host property ' + name, node is not None and node.get('type') == expected_type)
    for name, value in {'PROCESS_MODE_DISABLED': '4', 'PROCESS_MODE_INHERIT': '0', 'PROCESS_THREAD_GROUP_MAIN_THREAD': '1',
                        'PROCESS_THREAD_GROUP_INHERIT': '0', 'PHYSICS_INTERPOLATION_MODE_OFF': '2',
                        'PHYSICS_INTERPOLATION_MODE_INHERIT': '0', 'INTERNAL_MODE_DISABLED': '0'}.items():
        node = xml['Node.xml'].find('./constants/constant[@name="' + name + '"]')
        check('public enum ' + name, node is not None and node.get('value') == value)
    cpp = retained['node.cpp'].decode()
    entry = function_text(cpp, 'void Node::_propagate_enter_tree() {')
    ready = function_text(cpp, 'void Node::_propagate_ready() {')
    add = function_text(cpp, 'void Node::_add_child_nocheck(Node *p_child, const StringName &p_name, InternalMode p_internal_mode) {')
    add_guard = function_text(cpp, 'void Node::add_child(RequiredParam<Node> rp_child, bool p_force_readable_name, InternalMode p_internal) {')
    set_tree = function_text(cpp, 'void Node::_set_tree(SceneTree *p_tree) {')
    for name, token in {'entry notification': 'notification(NOTIFICATION_ENTER_TREE)', 'entry signal': 'tree_entered',
                        'tree node-added notification': 'data.tree->node_added(this)', 'parent entry signal': 'child_entered_tree'}.items():
        check(name, token in entry)
    check('ready children first', ready.index('K.value->_propagate_ready()') < ready.index('notification(NOTIFICATION_READY)'))
    check('ready signals remain', 'emit_signal(SceneStringName(ready))' in ready)
    check('ready parent governs synchronous ready propagation', 'data.parent->data.ready_notified' in set_tree and '_propagate_ready()' in set_tree)
    check('add parents before tree entry', add.index('p_child->data.parent = this') < add.index('p_child->_set_tree(data.tree)'))
    check('parent order signal follows entry', add.index('p_child->_set_tree(data.tree)') < add.index('emit_signal(SNAME("child_order_changed"))'))
    check('native main thread and busy-parent refusal', '!Thread::is_main_thread()' in add_guard and 'data.blocked > 0' in add_guard)
    check('tree topology signal retained', 'tree_changed_b->tree_changed()' in set_tree)
    can_process = function_text(cpp, 'bool Node::can_process() const {')
    check('detached can_process emits error fallback', 'ERR_FAIL_COND_V(!is_inside_tree(), false)' in can_process)
    check('disabled processing is a notification policy', 'if (process_mode == PROCESS_MODE_DISABLED)' in function_text(cpp, 'bool Node::_can_process(bool p_paused) const {'))
    mixer = retained['animation_mixer.cpp'].decode()
    check('mixer enter clears caches', '_clear_caches();' in mixer.split('case NOTIFICATION_ENTER_TREE:', 1)[1].split('} break;', 1)[0])
    check('cache clear emits signal', 'emit_signal(SNAME("caches_cleared"))' in function_text(mixer, 'void AnimationMixer::_clear_caches() {'))
    player = retained['animation_player.cpp'].decode()
    check('player ready can autoplay', 'animation_set.has(autoplay)' in function_text(player, 'void AnimationPlayer::_notification(int p_what) {'))
    node3d = retained['node_3d.cpp'].decode()
    check('top-level public native getter binding', 'D_METHOD("is_set_as_top_level"), &Node3D::is_set_as_top_level' in node3d)
    world = function_text(node3d, 'Transform3D Node3D::get_global_transform() const {')
    check('global getter requires tree membership', 'ERR_FAIL_COND_V(!is_inside_tree(), Transform3D())' in world)
    check('non-Node3D parent adds no 3D transform', 'data.parent = Object::cast_to<Node3D>(p)' in node3d and 'new_global = data.local_transform' in world)
    tree_cpp = retained['scene_tree.cpp'].decode()
    check('native root is Window', 'root = memnew(Window)' in tree_cpp)
    check('tree node_added emits signal', 'emit_signal(node_added_name, p_node)' in tree_cpp)
    source = (HERE / 'attachment.gd').read_text()
    attached = (HERE / 'attached_inventory.gd').read_text()
    check('one owned C250 capture', source.count('preparation.capture_after_generation_return(state, root)') == 1 and source.count('.capture_after_generation_return(') == 1)
    check('entire preparation receipt retained', '_result["playback_preparation"] = prepared' in source)
    finish = source.split('func _finish()', 1)[1].split('\n\nfunc ', 1)[0]
    check('complete registry receipt retained on permitted-thread finish', '_result["registry_final"] = Registry.failure_receipts()' in finish and '_refuse("registry fault at finish")' in finish)
    check('unsupported thread registry read explicitly omitted', '"reason": "unsupported thread; shared registry not inspected"' in finish and 'if not _result.has("registry_final")' in finish)
    check('no registry reconsumption', 'Registry.close_state(' not in source + attached)
    check('actual main-loop host', 'Engine.get_main_loop()' in source and 'var parent: Window = tree.root' in source)
    check('main-thread preflight bound', 'OS.get_thread_caller_id()' in source and 'OS.get_main_thread_id()' in source)
    check('wrong thread refused before owned native preparation', source.index('_result["entry_threads"]') < source.index('var preparation = Preparation.new()') and '"status": "NOT_ATTEMPTED"' in source)
    check('exact single attachment call', source.count('parent.add_child(root, false, Node.INTERNAL_MODE_DISABLED)') == 1)
    check('attempt retained before call', source.index('_result["mutations"].append(mutation)') < source.index('parent.add_child('))
    check('partial refusal never rolls back', 'REFUSED_AFTER_ATTEMPT' in source and 'never attempted; partial observed changes remain' in source)
    check('detached can_process omitted', 'node.can_process() if row["inside_tree"] else {"status": "NOT_OBSERVED"' in source)
    check('raw local columns and origin', 'native.basis.x.x' in source and 'native.basis.z.z' in source and 'native.origin.x' in source and '"local_transform"' in source)
    check('local frame controls observed', 'node.is_set_as_top_level()' in source and 'node.is_scale_disabled()' in source)
    check('complete product signals bounded', 'node.get_signal_list()' in source and 'declarations.size() > 128' in source and '_signal_counts(node, signal_names' in source)
    check('actual cache clearing signal included in native inventory', any(n.get('name') == 'caches_cleared' for n in xml['AnimationMixer.xml'].findall('./signals/signal')))
    check('late player control retained', 'receipt["player_control_recheck"]' in source and 'receipt["nodes_recheck"]' in source and 'receipt["host_recheck"]' in source)
    check('diagnostic limits explicit', '"diagnostic_coverage": "UNESTABLISHED"' in source and '"execution_admission": false' in source and '"native_acceptance": false' in source)
    check('no native pose evaluation or additional mutation', not re.search(r'\.(?:seek|advance|play|stop|reparent|remove_child|set_meta|set_owner|set_process_mode|set_physics_interpolation_mode|set_callback_mode_process|set_assigned_animation|generate_scene|append_from_file|save|execute|create_process)\s*\(', source + attached))
    check('no global transform or key payload read', not re.search(r'\.(?:global_transform|global_position|global_rotation|global_basis|get_global_transform|track_get_key_value|track_get_key_time)\b', source + attached))
    check('no native property assignment', not re.search(r'\b(?:player|root|node|parent|tree|mesh|material|animation|library)\.\w+\s*=(?!=)', source + attached))
    original = (HERE.parent / 'second-target-c249/animation_inventory.gd').read_text()
    scene = original[original.index('func _scene('):original.index('\n\nfunc _inventory(')]
    scene = scene.replace('func _scene(root: Node, materials: Dictionary, out: Dictionary) -> Dictionary:\n', 'func _scene(root: Node, materials: Dictionary, out: Dictionary) -> Dictionary:\n\tif not attached:\n\t\treturn super._scene(root, materials, out)\n')
    scene = scene.replace('root.get_parent() != null', 'root.get_parent() != host_parent').replace('or root.is_inside_tree():', 'or not root.is_inside_tree() or root.get_tree() != host_tree:')
    scene = scene.replace('returned root changed or entered the scene tree', 'attached root identity parent or tree differs')
    scene = scene.replace('or row["inside_tree"]:', 'or not row["inside_tree"] or node.get_tree() != host_tree:').replace('duplicate retired scripted queued or attached scene member', 'duplicate retired scripted queued or wrongly attached scene member')
    check('attached predicate changes only declared C249 parent/tree tests', attached.split('func _scene(', 1)[1].strip() == scene.split('func _scene(', 1)[1].strip())
    spec = importlib.util.spec_from_file_location('c251_inherited_binding_verifier', HERE.parent / 'second-target-c250/verify_bindings.py')
    inherited = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inherited)
    result = inherited.verify(package)
    check('inherited source and original fixture bindings pass', result['passed'])
    return {'schema': 'ontokin.c251.binding-result/0.1', 'passed': True, 'checks': checks, 'count': len(checks),
            'primarySources': len(bindings['sources']), 'authorityFiles': len(bindings['authority']),
            'inheritedC250': {'passed': True, 'checks': result['count'], 'inheritedC249': result['inheritedC249']},
            'sourceHashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir()) if p.is_file()},
            'gdscriptParser': 'NOT_RUN', 'native': 'NOT_RUN', 'product': 'NOT_RUN', 'aggregate': 'NOT_RUN',
            'limitations': 'Pinned bytes, XML and lexical checks; no full static analysis, installed binding or native behavior proof'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', type=Path, required=True)
    parser.add_argument('--new-source-root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.package_root, args.new_source_root)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': result['count'], 'inheritedChecks': result['inheritedC250']['checks'], 'native': 'NOT_RUN'}))


if __name__ == '__main__':
    main()
