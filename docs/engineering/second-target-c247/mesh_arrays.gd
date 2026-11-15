extends RefCounted
## Held source only: no parser, native execution or admission has been performed.
## Receipts retain native API values; they are not source-equivalence assertions.

const Registry = preload("../second-target-c246/registry.gd")
const MESHES: Array = [0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]
const EXPECTED_FORMAT: int = Mesh.ARRAY_FORMAT_VERTEX | Mesh.ARRAY_FORMAT_NORMAL | Mesh.ARRAY_FORMAT_TANGENT | Mesh.ARRAY_FORMAT_INDEX | RenderingServer.ARRAY_FLAG_FORMAT_CURRENT_VERSION
const MAX_SCENE_NODES: int = 64
const MAX_VERTICES: int = 100000
const MAX_INDICES: int = 300000
const MAX_RAW_BYTES: int = 16000000
var _used: bool = false
var _errors: Array = []
var _result: Dictionary = {}


func _refuse(reason: String) -> void:
	if _errors.is_empty():
		_errors.append(reason)
	_result["phase"] = "REFUSED"
	_result["component_complete"] = false


func _finish() -> Dictionary:
	_result["errors"] = _errors.duplicate(true)
	return _result.duplicate(true)


func _live_meshes(root: Node, chain: Dictionary) -> Dictionary:
	var meshes: Dictionary = {}
	if not is_instance_valid(root) or root.get_class() != "Node3D" or root.get_parent() != null:
		_refuse("invalid returned root class or parent")
		return meshes
	if root.get_instance_id() != chain["root"]["instance_id"]:
		_refuse("returned root identity changed")
		return meshes
	var wanted: Dictionary = {}
	var retired: Dictionary = {}
	for index in range(MESHES.size()):
		var original: Dictionary = chain["originals"][index]
		var edge: Dictionary = chain["edges"][index]
		var final: Dictionary = chain["finals"][index]
		if original["mesh"] != MESHES[index] or edge["old"] != original["old"] or edge["new"] != final["new"]:
			_refuse("inconsistent trusted chain association")
			return meshes
		if wanted.has(final["new"]) or final["new"] == root.get_instance_id():
			_refuse("duplicate final or root identity")
			return meshes
		wanted[final["new"]] = index
		retired[original["old"]] = true
	var pending: Array = [root]
	var seen: Dictionary = {}
	while not pending.is_empty():
		if seen.size() >= MAX_SCENE_NODES:
			_refuse("scene traversal bound exceeded")
			return meshes
		var node: Node = pending.pop_back()
		if not is_instance_valid(node):
			_refuse("invalid current scene member")
			return meshes
		var identity: int = node.get_instance_id()
		if seen.has(identity) or retired.has(identity) or node.get_script() != null:
			_refuse("duplicate retired or scripted scene member")
			return meshes
		seen[identity] = true
		if node.get_class() == "ImporterMeshInstance3D":
			_refuse("unconverted scene member")
			return meshes
		if node is MeshInstance3D:
			if node.get_class() != "MeshInstance3D" or not wanted.has(identity):
				_refuse("unmapped or unsupported mesh member")
				return meshes
			meshes[wanted[identity]] = node
		var children: Array = node.get_children(true)
		if pending.size() + children.size() + seen.size() > MAX_SCENE_NODES:
			_refuse("scene traversal bound exceeded")
			return meshes
		pending.append_array(children)
	if meshes.size() != MESHES.size():
		_refuse("missing final live mesh membership")
	return meshes


func _mesh_binding(node: MeshInstance3D, final: Dictionary) -> ArrayMesh:
	if not is_instance_valid(node) or node.get_class() != "MeshInstance3D" or node.get_script() != null or node.get_instance_id() != final["new"]:
		_refuse("final node identity changed")
		return null
	var value: Mesh = node.mesh
	if value == null or not is_instance_valid(value) or value.get_class() != "ArrayMesh" or value.get_script() != null:
		_refuse("missing scripted or unsupported native mesh resource")
		return null
	var found: int = 0
	for binding in final["native"]["resource_bindings"]:
		var property: Dictionary = binding["property"]
		if property["type"] in [TYPE_STRING, TYPE_STRING_NAME] and property["value"] == "mesh":
			found += 1
			if binding["resource"]["class"] != "ArrayMesh" or binding["resource"]["instance_id"] != value.get_instance_id():
				_refuse("mesh resource differs from final chain facts")
				return null
	if found != 1:
		_refuse("missing or ambiguous final mesh binding")
		return null
	return value as ArrayMesh


func _surface(mesh: ArrayMesh) -> Dictionary:
	var out: Dictionary = {"mesh_instance_id": mesh.get_instance_id(), "mesh_class": mesh.get_class(),
		"surface_count": mesh.get_surface_count(), "blend_shape_count": mesh.get_blend_shape_count(),
		"shadow_mesh_present": mesh.shadow_mesh != null}
	if out["surface_count"] != 1 or out["blend_shape_count"] != 0 or out["shadow_mesh_present"]:
		_refuse("surface count blend shape or shadow mesh unsupported")
		return out
	out["surface"] = 0
	out["format"] = mesh.surface_get_format(0)
	out["primitive_type"] = mesh.surface_get_primitive_type(0)
	out["vertex_count"] = mesh.surface_get_array_len(0)
	out["index_count"] = mesh.surface_get_array_index_len(0)
	if out["format"] != EXPECTED_FORMAT or out["primitive_type"] != Mesh.PRIMITIVE_TRIANGLES:
		_refuse("unsupported raw format version channels flags or primitive")
		return out
	if out["vertex_count"] <= 0 or out["vertex_count"] > MAX_VERTICES or out["index_count"] <= 0 or out["index_count"] > MAX_INDICES or out["index_count"] % 3 != 0:
		_refuse("invalid or excessive native array counts")
		return out
	# Bound public API supplies LOD presence; ArrayMesh.surface_get_lods is not bound.
	var raw: Dictionary = RenderingServer.mesh_get_surface(mesh.get_rid(), 0)
	var field_types: Array = []
	for key in raw:
		field_types.append({"key": key, "type": typeof(raw[key])})
	out["raw_surface_field_types"] = field_types
	for key in raw:
		if typeof(key) != TYPE_STRING or key not in ["primitive", "format", "vertex_data", "vertex_count", "index_data", "index_count", "aabb", "uv_scale", "material", "attribute_data", "skin_data", "lods", "bone_aabbs", "blend_shape_data"]:
			_refuse("unknown raw native surface field")
			return out
	for key in ["format", "primitive", "vertex_count", "index_count", "vertex_data", "index_data"]:
		if not raw.has(key):
			_refuse("missing native raw surface field " + key)
			return out
	for key in ["format", "primitive", "vertex_count", "index_count"]:
		if typeof(raw[key]) != TYPE_INT:
			_refuse("native raw descriptor type mismatch")
			return out
	out["raw_buffer_lengths"] = {}
	for key in ["vertex_data", "index_data"]:
		if typeof(raw[key]) != TYPE_PACKED_BYTE_ARRAY:
			_refuse("unsupported raw native buffer type")
			return out
		out["raw_buffer_lengths"][key] = raw[key].size()
		if raw[key].is_empty() or raw[key].size() > MAX_RAW_BYTES:
			out["omitted"] = [{"field": key, "count": raw[key].size(), "type": typeof(raw[key]),
				"reason": "empty or over raw buffer bound", "cap": MAX_RAW_BYTES}]
			_refuse("empty or excessive raw native buffer")
			return out
		out[key] = raw[key].duplicate()
	if raw["format"] != out["format"] or raw["primitive"] != out["primitive_type"] or raw["vertex_count"] != out["vertex_count"] or raw["index_count"] != out["index_count"]:
		_refuse("raw and resource surface descriptors disagree")
		return out
	for key in ["attribute_data", "skin_data", "lods", "bone_aabbs", "blend_shape_data"]:
		if raw.has(key):
			_refuse("unsupported native surface field " + key)
			return out
	var arrays: Array = mesh.surface_get_arrays(0)
	out["array_type"] = typeof(arrays)
	out["array_count"] = arrays.size()
	var kinds: Array = []
	var lengths: Array = []
	var supported: Dictionary = {Mesh.ARRAY_VERTEX: TYPE_PACKED_VECTOR3_ARRAY,
		Mesh.ARRAY_NORMAL: TYPE_PACKED_VECTOR3_ARRAY, Mesh.ARRAY_TANGENT: TYPE_PACKED_FLOAT32_ARRAY,
		Mesh.ARRAY_INDEX: TYPE_PACKED_INT32_ARRAY}
	var names: Dictionary = {Mesh.ARRAY_VERTEX: "positions", Mesh.ARRAY_NORMAL: "normals",
		Mesh.ARRAY_TANGENT: "auxiliary_tangents", Mesh.ARRAY_INDEX: "indices"}
	var caps: Dictionary = {Mesh.ARRAY_VERTEX: MAX_VERTICES, Mesh.ARRAY_NORMAL: MAX_VERTICES,
		Mesh.ARRAY_TANGENT: 4 * MAX_VERTICES, Mesh.ARRAY_INDEX: MAX_INDICES}
	for slot in range(mini(arrays.size(), Mesh.ARRAY_MAX)):
		kinds.append(typeof(arrays[slot]))
		if typeof(arrays[slot]) in [TYPE_PACKED_VECTOR3_ARRAY, TYPE_PACKED_FLOAT32_ARRAY, TYPE_PACKED_INT32_ARRAY]:
			lengths.append(arrays[slot].size())
		else:
			lengths.append(null)
	out["slot_types"] = kinds
	out["slot_lengths"] = lengths
	# Preserve bounded supported observations before cross-slot refusal.
	for slot in range(mini(arrays.size(), Mesh.ARRAY_MAX)):
		if supported.has(slot) and typeof(arrays[slot]) == supported[slot]:
			if arrays[slot].size() > caps[slot]:
				out["omitted"] = [{"field": names[slot], "count": arrays[slot].size(),
					"type": typeof(arrays[slot]), "reason": "over slot bound", "cap": caps[slot]}]
				_refuse("native slot exceeds capture bound")
				return out
			out[names[slot]] = arrays[slot].duplicate()
	if arrays.size() != Mesh.ARRAY_MAX:
		_refuse("wrong native slot count")
		return out
	for slot in range(Mesh.ARRAY_MAX):
		if supported.has(slot):
			if typeof(arrays[slot]) != supported[slot]:
				_refuse("wrong packed native array type")
				return out
		elif arrays[slot] != null:
			_refuse("unexpected native channel")
			return out
	if arrays[Mesh.ARRAY_VERTEX].size() != out["vertex_count"] or arrays[Mesh.ARRAY_NORMAL].size() != out["vertex_count"] or arrays[Mesh.ARRAY_TANGENT].size() != 4 * out["vertex_count"] or arrays[Mesh.ARRAY_INDEX].size() != out["index_count"]:
		_refuse("native packed lengths disagree with descriptors")
		return out
	for slot in ["positions", "normals"]:
		for value in out[slot]:
			if not is_finite(value.x) or not is_finite(value.y) or not is_finite(value.z):
				_refuse("nonfinite native vector")
				return out
	for value in out["auxiliary_tangents"]:
		if not is_finite(value):
			_refuse("nonfinite auxiliary tangent")
			return out
	for value in out["indices"]:
		if value < 0 or value >= out["vertex_count"]:
			_refuse("native index out of bounds")
			return out
	return out


func capture_after_generation_return(state: GLTFState, root: Node) -> Dictionary:
	if _used:
		_refuse("capture is single use")
		return _finish()
	_used = true
	_result = {"schema": "ontokin.c247.native-mesh-arrays/0.1", "phase": "CAPTURING",
		"component_complete": false, "execution_admission": false, "native_acceptance": false,
		"R07": "PENDING", "value_origin": "native-api-readback", "parts": []}
	# Caller must already have notified C246 only after synchronous generation returns.
	# Receipt is obtained from the registry, never supplied as caller-created evidence.
	var chain: Dictionary = Registry.close_state(state)
	_result["chain"] = chain
	if not is_instance_valid(state) or not chain.get("component_complete", false) or chain.get("phase", "") != "CHAIN_COMPLETE_RAW_PENDING" or chain.get("state_id", 0) != state.get_instance_id():
		_refuse("registry did not supply a completed exact-state chain")
		return _finish()
	if not chain["errors"].is_empty() or not Registry.failure_receipts()["faults"].is_empty():
		_refuse("registry or chain already poisoned")
		return _finish()
	var meshes: Dictionary = _live_meshes(root, chain)
	if not _errors.is_empty():
		return _finish()
	for index in range(MESHES.size()):
		var row: Dictionary = {"source_node": index, "source_mesh": chain["originals"][index]["mesh"],
			"source_primitive": 0, "native_node_instance_id": chain["finals"][index]["new"],
			"native_surface": 0, "association_basis": "single primitive plus pinned ordered conversion and live replacement chain"}
		_result["parts"].append(row)
		var mesh: ArrayMesh = _mesh_binding(meshes[index], chain["finals"][index])
		if not _errors.is_empty():
			return _finish()
		row["snapshot"] = _surface(mesh)
		if not _errors.is_empty():
			return _finish()
	# Recheck each exact resource and its entire captured values, then membership.
	# This detects lasting drift; it is not an atomic snapshot against concurrent writes.
	for index in range(MESHES.size()):
		var mesh: ArrayMesh = _mesh_binding(meshes[index], chain["finals"][index])
		if not _errors.is_empty():
			return _finish()
		var after: Dictionary = _surface(mesh)
		if not _errors.is_empty() or after != _result["parts"][index]["snapshot"]:
			_result["parts"][index]["after_drift"] = after
			_refuse("native surface changed during capture")
			return _finish()
	_live_meshes(root, chain)
	if not _errors.is_empty() or not Registry.failure_receipts()["faults"].is_empty():
		_refuse("final scene or registry changed during capture")
		return _finish()
	_result["phase"] = "MESH_ARRAYS_CAPTURED_OTHER_RAW_PENDING"
	_result["component_complete"] = true
	_result["stability"] = "two equal reads and final membership; not atomic against concurrent writes"
	return _finish()
