extends RefCounted
## Held root-only attachment source; no playback evaluation or world-pose read.
## The external admitted driver must establish complete diagnostic coverage.

const Preparation = preload("../second-target-c250/playback_preparation.gd")
const Inventory = preload("attached_inventory.gd")
const Facts = preload("../second-target-c246/native_facts.gd")
const Registry = preload("../second-target-c246/registry.gd")
const NODE_COUNT: int = 20
const TREE_SIGNALS: Array = [&"node_added", &"tree_changed"]
const WINDOW_SIGNALS: Array = [&"child_entered_tree", &"child_order_changed"]
var _used: bool = false
var _errors: Array = []
var _result: Dictionary = {}


func _refuse(reason: String) -> void:
	if _errors.is_empty():
		_errors.append(reason)
	_result["phase"] = "REFUSED"
	_result["component_complete"] = false


func _finish() -> Dictionary:
	if OS.get_thread_caller_id() != OS.get_main_thread_id():
		_result["registry_finish"] = {"status": "NOT_OBSERVED", "reason": "unsupported thread; shared registry not inspected"}
		if not _result.has("registry_final"):
			_result["registry_final"] = _result["registry_finish"].duplicate(true)
		_refuse("unsupported thread at finish")
	else:
		_result["registry_final"] = Registry.failure_receipts()
		_result["registry_finish"] = {"status": "OBSERVED"}
		if not _result["registry_final"]["faults"].is_empty():
			_refuse("registry fault at finish")
	_result["errors"] = _errors.duplicate(true)
	return _result.duplicate(true)


func _identity(value: Object) -> Dictionary:
	var reader = Inventory.new()
	var result: Dictionary = reader._identity(value)
	if not reader._errors.is_empty():
		_refuse("invalid native identity")
	return result


func _signal_counts(value: Object, names: Array, out: Array) -> void:
	for name in names:
		var connections: Array = value.get_signal_connection_list(name)
		var row: Dictionary = {"signal": str(name), "receivers": connections.size()}
		out.append(row)
		if not connections.is_empty():
			row["omitted"] = "Callable payload; every selected receiver refuses"
			_refuse("selected lifecycle signal has a receiver")
			return


func _host(root: Node, attached: bool, out: Dictionary) -> Dictionary:
	var loop: MainLoop = Engine.get_main_loop()
	out["main_loop"] = _identity(loop)
	out["editor_hint"] = Engine.is_editor_hint()
	out["caller_thread"] = OS.get_thread_caller_id()
	out["main_thread"] = OS.get_main_thread_id()
	if not _errors.is_empty() or loop == null or not loop is SceneTree or out["editor_hint"] or out["caller_thread"] != out["main_thread"]:
		_refuse("unsupported actual main loop editor or thread")
		return {}
	var tree: SceneTree = loop
	var parent: Window = tree.root
	out["tree_script"] = _identity(tree.get_script())
	out["paused"] = tree.paused
	out["physics_interpolation"] = tree.physics_interpolation
	out["current_scene"] = _identity(tree.current_scene)
	out["parent"] = _identity(parent)
	out["node_count"] = tree.get_node_count()
	out["processed_tweens"] = tree.get_processed_tweens().size()
	if not _errors.is_empty() or not is_instance_valid(parent) or parent.get_class() != "Window":
		_refuse("unsupported root Window")
		return {}
	var facts = Facts.new()
	out["tree_metadata"] = facts.metadata(tree)
	out["parent_metadata"] = facts.metadata(parent)
	out["parent_script"] = _identity(parent.get_script())
	out["parent_parent"] = _identity(parent.get_parent())
	out["parent_owner"] = _identity(parent.owner)
	out["parent_name"] = str(parent.name)
	out["parent_ready"] = parent.is_node_ready()
	out["parent_inside_tree"] = parent.is_inside_tree()
	out["parent_queued"] = parent.is_queued_for_deletion()
	out["parent_blocking_signals"] = parent.is_blocking_signals()
	out["tree_blocking_signals"] = tree.is_blocking_signals()
	out["parent_process_mode"] = parent.process_mode
	out["parent_process_thread_group"] = parent.process_thread_group
	out["parent_interpolation_mode"] = parent.physics_interpolation_mode
	out["parent_interpolated"] = parent.is_physics_interpolated()
	out["parent_can_process"] = parent.can_process()
	out["children"] = []
	var children: Array = parent.get_children(true)
	for child in children:
		out["children"].append(_identity(child))
	if not facts.errors.is_empty():
		out["metadata_errors"] = facts.errors.duplicate(true)
		_refuse("unsupported host metadata")
		return {}
	if not out["paused"] or out["physics_interpolation"] or tree.current_scene != null or out["processed_tweens"] != 0 or parent.get_script() != null or parent.get_parent() != null or parent.owner != null or not out["parent_ready"] or not out["parent_inside_tree"] or parent.get_tree() != tree or out["parent_queued"] or out["parent_blocking_signals"] or out["tree_blocking_signals"]:
		_refuse("host lifecycle isolation refused")
		return {}
	if parent.process_mode != Node.PROCESS_MODE_DISABLED or parent.process_thread_group not in [Node.PROCESS_THREAD_GROUP_INHERIT, Node.PROCESS_THREAD_GROUP_MAIN_THREAD] or parent.physics_interpolation_mode != Node.PHYSICS_INTERPOLATION_MODE_OFF or out["parent_interpolated"] or out["parent_can_process"]:
		_refuse("host processing or interpolation differs from predeclared state")
		return {}
	if (not attached and (not children.is_empty() or out["node_count"] != 1)) or (attached and (children.size() != 1 or children[0] != root or out["node_count"] != NODE_COUNT + 1)):
		_refuse("host children or total node count differs")
		return {}
	out["tree_signals"] = []
	out["parent_signals"] = []
	_signal_counts(tree, TREE_SIGNALS, out["tree_signals"])
	if not _errors.is_empty():
		return {}
	_signal_counts(parent, WINDOW_SIGNALS, out["parent_signals"])
	if not _errors.is_empty():
		return {}
	return {"tree": tree, "parent": parent}


func _local_transform(node: Node3D, out: Dictionary) -> void:
	var native: Transform3D = node.transform
	out["type"] = TYPE_TRANSFORM3D
	out["basis_columns"] = [[native.basis.x.x, native.basis.x.y, native.basis.x.z],
		[native.basis.y.x, native.basis.y.y, native.basis.y.z],
		[native.basis.z.x, native.basis.z.y, native.basis.z.z]]
	out["origin"] = [native.origin.x, native.origin.y, native.origin.z]
	for column in out["basis_columns"]:
		for value in column:
			if not is_finite(value):
				_refuse("nonfinite raw local transform")
	for value in out["origin"]:
		if not is_finite(value):
			_refuse("nonfinite raw local transform")


func _nodes(root: Node, tree: SceneTree, parent: Window, attached: bool, out: Array) -> void:
	var nodes: Array = [root]
	nodes.append_array(root.get_children(true))
	if nodes.size() != NODE_COUNT:
		_refuse("original finite node count differs")
		return
	for node in nodes:
		var row: Dictionary = {"identity": _identity(node)}
		out.append(row)
		if not _errors.is_empty() or not is_instance_valid(node):
			return
		var facts = Facts.new()
		row["metadata"] = facts.metadata(node)
		row["script"] = _identity(node.get_script())
		row["parent"] = _identity(node.get_parent())
		row["owner"] = _identity(node.owner)
		row["name"] = str(node.name)
		row["inside_tree"] = node.is_inside_tree()
		row["ready"] = node.is_node_ready()
		row["queued"] = node.is_queued_for_deletion()
		row["blocking_signals"] = node.is_blocking_signals()
		row["tree"] = _identity(node.get_tree()) if row["inside_tree"] else _identity(null)
		row["process_mode"] = node.process_mode
		row["process_thread_group"] = node.process_thread_group
		row["interpolation_mode"] = node.physics_interpolation_mode
		row["interpolated"] = node.is_physics_interpolated()
		row["can_process"] = node.can_process() if row["inside_tree"] else {"status": "NOT_OBSERVED", "reason": "native getter requires SceneTree membership"}
		row["processing"] = [node.is_processing(), node.is_physics_processing(), node.is_processing_internal(),
			node.is_physics_processing_internal(), node.is_processing_input(), node.is_processing_shortcut_input(),
			node.is_processing_unhandled_input(), node.is_processing_unhandled_key_input()]
		row["groups"] = node.get_groups()
		if not facts.errors.is_empty():
			row["metadata_errors"] = facts.errors.duplicate(true)
			_refuse("unsupported product metadata")
			return
		if not _errors.is_empty() or node.get_script() != null or row["queued"] or row["blocking_signals"] or row["inside_tree"] != attached or row["ready"] != attached or (attached and node.get_tree() != tree) or node.process_mode != Node.PROCESS_MODE_INHERIT or node.process_thread_group != Node.PROCESS_THREAD_GROUP_INHERIT or node.physics_interpolation_mode != Node.PHYSICS_INTERPOLATION_MODE_INHERIT or (attached and row["can_process"] != false) or (attached and row["interpolated"]) or not row["groups"].is_empty() or true in row["processing"]:
			_refuse("product lifecycle processing or interpolation outside finite profile")
			return
		if node is Node3D:
			row["top_level"] = node.is_set_as_top_level()
			row["scale_disabled"] = node.is_scale_disabled()
			row["local_transform"] = {}
			_local_transform(node, row["local_transform"])
			if row["top_level"] or row["scale_disabled"] or not _errors.is_empty():
				_refuse("unsupported local frame state")
				return
		var signal_names: Array = []
		var declarations: Array = node.get_signal_list()
		row["signal_count"] = declarations.size()
		row["signals"] = []
		if declarations.size() > 128:
			_refuse("product signal declaration bound exceeded")
			return
		for declaration in declarations:
			signal_names.append(declaration["name"])
		_signal_counts(node, signal_names, row["signals"])
		if not _errors.is_empty():
			return


func _player_control(player: AnimationPlayer, out: Dictionary) -> void:
	out["identity"] = _identity(player)
	out["internal_idle"] = player.is_processing_internal()
	out["internal_physics"] = player.is_physics_processing_internal()
	out["active"] = player.active
	out["callback_mode_process"] = player.callback_mode_process
	out["playing"] = player.is_playing()
	out["current_animation"] = player.current_animation
	out["assigned_animation"] = str(player.assigned_animation)
	out["autoplay"] = player.autoplay
	out["animation_active"] = player.is_animation_active()
	if not out["animation_active"]:
		out["omitted"] = "position and length need assigned playback pointer"
		_refuse("assigned playback pointer disappeared")
		return
	out["position"] = player.current_animation_position
	out["length"] = player.current_animation_length
	if not _errors.is_empty() or out["internal_idle"] or out["internal_physics"] or not out["active"] or out["callback_mode_process"] != AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL or out["playing"] or not out["current_animation"].is_empty() or not out["autoplay"].is_empty() or out["position"] != 0.0 or out["length"] != 2.0:
		_refuse("prepared stopped player changed at attachment boundary")


func _boundary(root: Node, materials: Dictionary, expected: Dictionary, attached: bool, preparation, receipt: Dictionary) -> Dictionary:
	receipt.merge({"complete": false, "host": {}, "inventory": {}, "nodes": [], "player_control": {}})
	var host: Dictionary = _host(root, attached, receipt["host"])
	if host.is_empty() or not _errors.is_empty():
		return {}
	var reader = Inventory.new()
	reader.attached = attached
	reader.host_parent = host["parent"]
	reader.host_tree = host["tree"]
	preparation._stage_inventory(root, materials, expected, receipt["inventory"], reader)
	if not reader._errors.is_empty():
		receipt["inventory_errors"] = reader._errors.duplicate(true)
		_refuse("policy-aware original inventory refused")
		return {}
	_nodes(root, host["tree"], host["parent"], attached, receipt["nodes"])
	if not _errors.is_empty():
		return {}
	receipt["scene_recheck"] = {}
	var live: Dictionary = reader._scene(root, materials, receipt["scene_recheck"])
	if not reader._errors.is_empty() or receipt["scene_recheck"] != expected["scene"]:
		receipt["inventory_errors"] = reader._errors.duplicate(true)
		_refuse("scene drift before player control")
		return {}
	_player_control(live["player"], receipt["player_control"])
	if not _errors.is_empty():
		return {}
	receipt["inventory_recheck"] = {}
	preparation._stage_inventory(root, materials, expected, receipt["inventory_recheck"], reader)
	if not reader._errors.is_empty():
		receipt["inventory_errors"] = reader._errors.duplicate(true)
		_refuse("late original inventory drift")
		return {}
	receipt["host_recheck"] = {}
	receipt["nodes_recheck"] = []
	var final_host: Dictionary = _host(root, attached, receipt["host_recheck"])
	if final_host.is_empty() or not _errors.is_empty():
		return {}
	_nodes(root, final_host["tree"], final_host["parent"], attached, receipt["nodes_recheck"])
	if not _errors.is_empty() or receipt["host_recheck"] != receipt["host"] or receipt["nodes_recheck"] != receipt["nodes"]:
		_refuse("host or product control drift during boundary")
		return {}
	receipt["player_control_recheck"] = {}
	_player_control(live["player"], receipt["player_control_recheck"])
	if not _errors.is_empty() or receipt["player_control_recheck"] != receipt["player_control"]:
		_refuse("late stopped player control drift")
		return {}
	receipt["registry_faults"] = Registry.failure_receipts()["faults"]
	if not receipt["registry_faults"].is_empty():
		_refuse("registry fault at attachment boundary")
		return {}
	receipt["complete"] = true
	return host


func _attached_inventory(original: Dictionary, parent: Window, root: Node) -> Dictionary:
	var expected: Dictionary = original.duplicate(true)
	for row in expected["scene"]["nodes"]:
		row["inside_tree"] = true
		if row["identity"]["instance_id"] == root.get_instance_id():
			row["parent"] = _identity(parent)
	return expected


func _transition_matches(before: Dictionary, after: Dictionary, root: Node, tree: SceneTree, parent: Window) -> bool:
	var expected_host: Dictionary = before["host"].duplicate(true)
	expected_host["children"] = [_identity(root)]
	expected_host["node_count"] = NODE_COUNT + 1
	var expected_nodes: Array = before["nodes"].duplicate(true)
	for row in expected_nodes:
		row["inside_tree"] = true
		row["ready"] = true
		row["tree"] = _identity(tree)
		row["interpolated"] = false
		row["can_process"] = false
		if row["identity"]["instance_id"] == root.get_instance_id():
			row["parent"] = _identity(parent)
	return after["host"] == expected_host and after["nodes"] == expected_nodes and after["player_control"] == before["player_control"]


func capture_after_generation_return(state: GLTFState, root: Node) -> Dictionary:
	if _used:
		_refuse("attachment is single use; reentry or retry refused")
		return _finish()
	_used = true
	_result = {"schema": "ontokin.c251.native-controlled-attachment/0.1", "phase": "CAPTURING",
		"component_complete": false, "execution_admission": false, "native_acceptance": false,
		"R07": "PENDING", "diagnostic_coverage": "UNESTABLISHED", "mutations": [],
		"value_origin": "native-api-readback", "rollback": "never attempted; partial observed changes remain",
		"omissions": ["seek and world poses", "raw sealing and serialization", "complete diagnostic binding and hard limits"]}
	_result["entry_threads"] = {"caller": OS.get_thread_caller_id(), "main": OS.get_main_thread_id()}
	_result["playback_preparation"] = {"status": "NOT_ATTEMPTED"}
	if _result["entry_threads"]["caller"] != _result["entry_threads"]["main"]:
		_refuse("known non-main-thread caller refused before owned preparation")
		return _finish()
	var preparation = Preparation.new()
	var prepared: Dictionary = preparation.capture_after_generation_return(state, root)
	_result["playback_preparation"] = prepared
	if not prepared.get("component_complete", false) or prepared.get("phase", "") != "DETACHED_MANUAL_STOPPED_ASSIGNMENT_PREPARED_POSES_PENDING" or not _errors.is_empty():
		_refuse("owned detached preparation refused")
		return _finish()
	var materials: Dictionary = prepared["animation_inventory"]["materials"]
	var original: Dictionary = prepared["mutations"][1]["after"]["inventory"]
	_result["before_attachment"] = {}
	var host: Dictionary = _boundary(root, materials, original, false, preparation, _result["before_attachment"])
	if host.is_empty() or not _errors.is_empty():
		_refuse("attachment preflight refused; detached preparation retained")
		return _finish()
	var tree: SceneTree = host["tree"]
	var parent: Window = host["parent"]
	var expected: Dictionary = _attached_inventory(original, parent, root)
	var mutation: Dictionary = {"operation": "add_child", "target_parent": _identity(parent),
		"root": _identity(root), "force_readable_name": false, "internal_mode": Node.INTERNAL_MODE_DISABLED,
		"status": "ATTEMPTED", "before": _result["before_attachment"], "after": {"status": "NOT_OBSERVED"}}
	_result["mutations"].append(mutation)
	parent.add_child(root, false, Node.INTERNAL_MODE_DISABLED)
	mutation["status"] = "RETURNED"
	mutation["after"] = {}
	var after_host: Dictionary = _boundary(root, materials, expected, true, preparation, mutation["after"])
	if after_host.is_empty() or not _errors.is_empty() or not _transition_matches(_result["before_attachment"], mutation["after"], root, tree, parent):
		mutation["outcome"] = "REFUSED_AFTER_ATTEMPT"
		_refuse("attachment readback refused; partial changes retained")
		return _finish()
	mutation["outcome"] = "DECLARED_CHANGE_OBSERVED"
	_result["phase"] = "CONTROLLED_ATTACHMENT_CAPTURED_POSES_PENDING"
	_result["component_complete"] = true
	_result["stability"] = "bounded readbacks under Variant equality; no atomicity transient mutation or lifetime proof"
	return _finish()
