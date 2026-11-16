extends RefCounted
## Held source for the finite 18-node replacement chain, not native admission.

const Facts = preload("native_facts.gd")
const MESHES: Array = [0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]
var state: GLTFState
var has_returned: bool = false
var _phase: String = "CAPTURING"
var _errors: Array = []
var _sequence: int = 0
var _root_id: int = 0
var _root_retired: bool = false
var _root_facts: Dictionary = {}
var _root_callable: Callable
var _originals: Dictionary = {}
var _old_ids: Dictionary = {}
var _edges: Dictionary = {}
var _new_ids: Dictionary = {}
var _retired: Dictionary = {}
var _connections: Dictionary = {}
var _finals: Dictionary = {}
var _cleanup: Array = []
var _returned_at: int = -1


func _init(exact_state: GLTFState) -> void:
	state = exact_state


func _tick() -> int:
	_sequence += 1
	return _sequence


func fail(reason: String) -> Error:
	_errors.append({"sequence": _tick(), "reason": reason})
	_phase = "FAILED"
	return ERR_INVALID_DATA


func _capture_facts(node: Node, root: Node) -> Dictionary:
	var reader = Facts.new()
	var result: Dictionary = reader.snapshot(node, root)
	result["sequence"] = _tick()
	if not reader.errors.is_empty():
		result["capture_errors"] = reader.errors.duplicate(true)
		fail("native fact capture refused")
	return result


func _bind_root(node: Node) -> Node:
	var root: Node = node
	while root.get_parent() != null:
		root = root.get_parent()
	if root == node or root.get_class() != "Node3D":
		fail("product mesh root or unexpected root class")
		return null
	if _root_id == 0:
		_root_id = root.get_instance_id()
		_root_facts = _capture_facts(root, root)
		if _phase == "FAILED":
			return null
		_root_callable = Callable(self, "_root_replacing")
		if root.connect(&"replacing_by", _root_callable, 0) != OK:
			fail("root guard subscription failed")
			return null
		_root_facts["guard_connected_sequence"] = _tick()
	elif root.get_instance_id() != _root_id:
		fail("inconsistent synthetic root")
		return null
	return root


func capture_original(exact_state: GLTFState, gltf_node: GLTFNode, json: Dictionary, node: Node) -> Error:
	# The phase guard is before every loader-map access.
	if _phase != "CAPTURING" or has_returned or exact_state != state:
		return fail("late, repeated or wrong-state import callback")
	if not is_instance_valid(node) or not is_instance_valid(gltf_node):
		return fail("invalid original node")
	if node.get_class() != "ImporterMeshInstance3D":
		return fail("unexpected original native class")
	var nodes: Array = state.get_nodes()
	if nodes.size() != MESHES.size():
		return fail("wrong glTF node count")
	var index: int = state.get_node_index(node)
	if index < 0 or index >= MESHES.size():
		return fail("unmapped original node")
	if state.get_scene_node(index) != node or nodes[index] != gltf_node:
		return fail("live forward/inverse/GLTFNode association mismatch")
	if gltf_node.mesh != MESHES[index] or not json.has("mesh"):
		return fail("wrong locked mesh association")
	# Pinned Godot JSON parses all numeric tokens as double, including mesh indices.
	# Preserve that raw native type/value and compare exactly without truncation.
	var raw_mesh: Variant = json["mesh"]
	if typeof(raw_mesh) != TYPE_FLOAT or not is_finite(raw_mesh) or raw_mesh != float(MESHES[index]):
		return fail("wrong callback JSON mesh association")
	var old_id: int = node.get_instance_id()
	if _originals.has(index) or _old_ids.has(old_id):
		return fail("duplicate original index or native identity")
	var root: Node = _bind_root(node)
	if root == null:
		return ERR_INVALID_DATA
	var native: Dictionary = _capture_facts(node, root)
	_originals[index] = {"index": index, "mesh": MESHES[index], "old": old_id, "native": native,
		"callback_json_mesh": {"type": typeof(raw_mesh), "value": raw_mesh}}
	_old_ids[old_id] = index
	if _phase == "FAILED":
		return ERR_INVALID_DATA
	var callback: Callable = Callable(self, "_replacing").bind(index, old_id)
	if node.connect(&"replacing_by", callback, 0) != OK:
		return fail("product subscription failed")
	_connections[old_id] = callback
	_originals[index]["connected_sequence"] = _tick()
	_originals[index]["flags"] = 0
	if _originals.size() == MESHES.size():
		_phase = "AWAIT_REPLACEMENTS"
	return OK


func _root_replacing(_replacement: Node) -> void:
	_root_retired = true
	fail("synthetic root replacement is forbidden")


func _replacing(replacement: Node, index: int, old_id: int) -> void:
	# Never recover or dereference an old node here; only the live replacement ID is read.
	# Even a refused event retires a known old identity for later safe cleanup.
	if _old_ids.has(old_id):
		_retired[old_id] = true
	if _phase not in ["AWAIT_REPLACEMENTS", "REPLACING"] or has_returned:
		fail("replacement outside the complete-capture phase")
		return
	if not _originals.has(index) or _originals[index]["old"] != old_id or _edges.has(index):
		fail("unknown, duplicate or cross-index replacement")
		return
	if not is_instance_valid(replacement):
		fail("invalid replacement")
		return
	var new_id: int = replacement.get_instance_id()
	if new_id == _root_id or _old_ids.has(new_id) or _new_ids.has(new_id):
		fail("root, old/new alias, cycle or duplicate replacement identity")
		return
	_edges[index] = {"index": index, "old": old_id, "new": new_id, "sequence": _tick()}
	_new_ids[new_id] = index
	_phase = "REPLACING"


func generation_returned(exact_state: GLTFState, root: Node) -> Error:
	# No state map access is allowed from this point onward.
	if has_returned:
		return fail("duplicate return notification")
	has_returned = true
	_returned_at = _tick()
	if exact_state != state or _phase != "REPLACING" or _edges.size() != MESHES.size():
		return fail("wrong state, prior fatal error or incomplete replacement chain")
	if _root_retired or not is_instance_valid(root):
		return fail("retired or missing returned root")
	if root.get_instance_id() != _root_id or root.get_class() != "Node3D" or root.get_parent() != null:
		return fail("returned root identity/class/parent mismatch")
	_phase = "FINAL_CAPTURE"
	var queue: Array = [root]
	var seen: Dictionary = {}
	var live_meshes: Dictionary = {}
	while not queue.is_empty():
		var current: Node = queue.pop_back()
		if not is_instance_valid(current):
			return fail("invalid final scene member")
		var identity: int = current.get_instance_id()
		if seen.has(identity) or _old_ids.has(identity):
			return fail("duplicate or retired original in returned scene")
		seen[identity] = true
		if current.get_script() != null or current.get_class() == "ImporterMeshInstance3D":
			return fail("unexpected script or unconverted final member")
		if current is MeshInstance3D:
			if current.get_class() != "MeshInstance3D" or not _new_ids.has(identity):
				return fail("unexpected final mesh identity/class")
			live_meshes[identity] = current
		queue.append_array(current.get_children(true))
	if live_meshes.size() != MESHES.size():
		return fail("missing or extra final mesh membership")
	for index in range(MESHES.size()):
		var new_id: int = _edges[index]["new"]
		if not live_meshes.has(new_id):
			return fail("replacement is outside returned scene")
		var native: Dictionary = _capture_facts(live_meshes[new_id], root)
		native["phase"] = "native-final-after-generation-return"
		_finals[index] = {"index": index, "new": new_id, "native": native}
		if _phase == "FAILED":
			return ERR_INVALID_DATA
	_phase = "CHAIN_COMPLETE_RAW_PENDING"
	return OK


func receipt() -> Dictionary:
	return {"phase": _phase, "component_complete": _phase == "CHAIN_COMPLETE_RAW_PENDING",
		"execution_admission": false, "native_acceptance": false, "R07": "PENDING",
		"diagnostic_coverage": "UNESTABLISHED", "state_id": state.get_instance_id(),
		"errors": _errors.duplicate(true), "root": _root_facts.duplicate(true),
		"originals": _originals.duplicate(true), "edges": _edges.duplicate(true),
		"finals": _finals.duplicate(true), "returned_at": _returned_at,
		"cleanup": _cleanup.duplicate(true)}


func close_after_return() -> Dictionary:
	if not has_returned:
		fail("cleanup requires caller return")
		return receipt()
	for old_id in _connections:
		if _retired.has(old_id):
			_cleanup.append({"id": old_id, "action": "retired identity never dereferenced"})
			continue
		_disconnect_if_live(old_id, _connections[old_id])
	if not _root_retired and _root_id != 0:
		_disconnect_if_live(_root_id, _root_callable)
	else:
		_cleanup.append({"id": _root_id, "action": "root not dereferenced"})
	_connections.clear()
	var result: Dictionary = receipt()
	_phase = "CLOSED"
	return result


func _disconnect_if_live(identity: int, callback: Callable) -> void:
	# This branch is never reached for any observed retired identity.
	if is_instance_id_valid(identity):
		var live: Object = instance_from_id(identity)
		if live is Node and live.is_connected(&"replacing_by", callback):
			live.disconnect(&"replacing_by", callback)
		_cleanup.append({"id": identity, "action": "live connection removed or absent"})
	else:
		_cleanup.append({"id": identity, "action": "invalid identity never dereferenced"})
