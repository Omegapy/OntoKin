extends RefCounted
## Held material snapshot source only; parsing and native behavior are unexecuted.
## This wrapper owns the single C247 capture and cannot accept a caller-made receipt.

const MeshReader = preload("../second-target-c247/mesh_arrays.gd")
const Registry = preload("../second-target-c246/registry.gd")
const MESHES: Array = [0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]
const MATERIAL_BY_MESH: Array = [0, 0, 1, 1, 1]
const MAX_SCENE_NODES: int = 64
const SUPPORTED_SETTINGS: Dictionary = {
	"blend_mode": 0, "depth_draw_mode": 0, "depth_test": 0, "shading_mode": 1,
	"diffuse_mode": 0, "specular_mode": 0, "metallic_specular": 0.5,
	"billboard_mode": 0, "distance_fade_mode": 0, "proximity_fade_enabled": false,
	"grow": false, "stencil_mode": 0, "stencil_flags": 0, "render_priority": 0,
	"alpha_antialiasing_mode": 0}
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


func _typed(value: Variant) -> Dictionary:
	return {"type": typeof(value), "value": value}


func _identity(value: Object) -> Dictionary:
	if value == null:
		return {"type": TYPE_NIL, "instance_id": 0, "class": "null"}
	if not is_instance_valid(value):
		_refuse("invalid native resource identity")
		return {"type": TYPE_OBJECT, "refused": "invalid object"}
	return {"type": TYPE_OBJECT, "instance_id": value.get_instance_id(), "class": value.get_class()}


func _live_meshes(root: Node, arrays: Dictionary) -> Dictionary:
	var found: Dictionary = {}
	var chain: Dictionary = arrays["chain"]
	if not is_instance_valid(root) or root.get_class() != "Node3D" or root.get_parent() != null or root.get_instance_id() != chain["root"]["instance_id"]:
		_refuse("returned root changed")
		return found
	if arrays["parts"].size() != MESHES.size():
		_refuse("incomplete trusted mesh-array receipt")
		return found
	var wanted: Dictionary = {}
	var retired: Dictionary = {}
	for index in range(MESHES.size()):
		var part: Dictionary = arrays["parts"][index]
		if part["source_node"] != index or part["source_mesh"] != MESHES[index] or part["source_primitive"] != 0 or part["native_surface"] != 0:
			_refuse("trusted primitive or mesh association differs")
			return found
		var identity: int = part["native_node_instance_id"]
		if wanted.has(identity) or identity != chain["finals"][index]["new"]:
			_refuse("ambiguous trusted final identity")
			return found
		wanted[identity] = index
		retired[chain["originals"][index]["old"]] = true
	var pending: Array = [root]
	var seen: Dictionary = {}
	while not pending.is_empty():
		if seen.size() >= MAX_SCENE_NODES:
			_refuse("material scene traversal bound exceeded")
			return found
		var node: Node = pending.pop_back()
		if not is_instance_valid(node):
			_refuse("invalid final scene member")
			return found
		var identity: int = node.get_instance_id()
		if seen.has(identity) or retired.has(identity) or node.get_script() != null or node.get_class() == "ImporterMeshInstance3D":
			_refuse("duplicate retired scripted or unconverted scene member")
			return found
		seen[identity] = true
		if node is MeshInstance3D:
			if node.get_class() != "MeshInstance3D" or not wanted.has(identity):
				_refuse("unmapped or unsupported final mesh")
				return found
			found[wanted[identity]] = node
		var children: Array = node.get_children(true)
		if pending.size() + seen.size() + children.size() > MAX_SCENE_NODES:
			_refuse("material scene traversal bound exceeded")
			return found
		pending.append_array(children)
	if found.size() != MESHES.size():
		_refuse("missing final mesh membership")
	return found


func _unit_float(value: Dictionary) -> bool:
	return value["type"] == TYPE_FLOAT and is_finite(value["value"]) and value["value"] >= 0.0 and value["value"] <= 1.0


func _material(material: Material) -> Dictionary:
	var out: Dictionary = {"identity": _identity(material)}
	if not _errors.is_empty():
		return out
	if material == null or material.get_class() != "StandardMaterial3D":
		_refuse("missing or unsupported native material class")
		return out
	var captured_script: Variant = material.get_script()
	out["script"] = _identity(captured_script)
	if captured_script != null or not _errors.is_empty():
		_refuse("scripted native material unsupported")
		return out
	var native: StandardMaterial3D = material as StandardMaterial3D
	var raw: Dictionary = {"albedo_color": _typed(native.albedo_color),
		"metallic": _typed(native.metallic), "roughness": _typed(native.roughness),
		"cull_mode": _typed(native.cull_mode), "transparency_mode": _typed(native.transparency)}
	out["raw"] = raw
	if raw["albedo_color"]["type"] != TYPE_COLOR:
		_refuse("native albedo Color type required")
		return out
	var color: Color = raw["albedo_color"]["value"]
	raw["components"] = {"r": _typed(color.r), "g": _typed(color.g), "b": _typed(color.b), "alpha": _typed(color.a)}
	# The storage label is a pinned-source declaration, not installed attestation.
	out["albedo_storage"] = "srgb-rgb-linear-alpha"
	out["storage_basis"] = "pinned glTF baseColorFactor linear_to_srgb; no observer conversion"
	var captured_next_pass: Material = native.next_pass
	out["next_pass"] = _identity(captured_next_pass)
	var settings: Dictionary = {}
	out["settings"] = settings
	for name in SUPPORTED_SETTINGS:
		settings[name] = _typed(native.get(name))
	var features: Array = []
	var flags: Array = []
	var textures: Array = []
	out["features"] = features
	out["flags"] = flags
	out["textures"] = textures
	out["enum_counts"] = {"features": BaseMaterial3D.FEATURE_MAX, "flags": BaseMaterial3D.FLAG_MAX, "textures": BaseMaterial3D.TEXTURE_MAX}
	if BaseMaterial3D.FEATURE_MAX != 13 or BaseMaterial3D.FLAG_MAX != 25 or BaseMaterial3D.TEXTURE_MAX != 19:
		out["omitted"] = [{"field": "feature inventories", "reason": "pinned enum count mismatch"}]
		_refuse("native feature inventory differs from pinned API")
		return out
	for index in range(BaseMaterial3D.FEATURE_MAX):
		features.append({"index": index, "raw": _typed(native.get_feature(index))})
	for index in range(BaseMaterial3D.FLAG_MAX):
		flags.append({"index": index, "raw": _typed(native.get_flag(index))})
	for index in range(BaseMaterial3D.TEXTURE_MAX):
		textures.append({"index": index, "identity": _identity(native.get_texture(index))})
		if not _errors.is_empty():
			return out
	for value in raw["components"].values():
		if not _unit_float(value):
			_refuse("nonfinite or out-of-range native color component")
			return out
	if not _unit_float(raw["metallic"]) or not _unit_float(raw["roughness"]):
		_refuse("nonfinite or out-of-range native PBR scalar")
		return out
	if raw["cull_mode"]["type"] != TYPE_INT or raw["cull_mode"]["value"] not in [BaseMaterial3D.CULL_BACK, BaseMaterial3D.CULL_FRONT, BaseMaterial3D.CULL_DISABLED]:
		_refuse("unsupported culling mode")
		return out
	if raw["transparency_mode"]["type"] != TYPE_INT or raw["transparency_mode"]["value"] not in [BaseMaterial3D.TRANSPARENCY_DISABLED, BaseMaterial3D.TRANSPARENCY_ALPHA, BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR]:
		_refuse("unsupported transparency mode")
		return out
	if captured_next_pass != null:
		out["omitted"] = [{"field": "next_pass payload", "reason": "unsupported additional material pass"}]
		_refuse("additional material pass unsupported")
		return out
	for name in SUPPORTED_SETTINGS:
		if settings[name]["type"] != typeof(SUPPORTED_SETTINGS[name]) or settings[name]["value"] != SUPPORTED_SETTINGS[name]:
			_refuse("unsupported material setting " + name)
			return out
	for feature in features:
		if feature["raw"]["type"] != TYPE_BOOL or feature["raw"]["value"] != false:
			_refuse("enabled or malformed additional material feature")
			return out
	for flag in flags:
		var expected: bool = flag["index"] == BaseMaterial3D.FLAG_USE_TEXTURE_REPEAT
		if flag["raw"]["type"] != TYPE_BOOL or flag["raw"]["value"] != expected:
			_refuse("unsupported native material flag")
			return out
	for texture in textures:
		if texture["identity"]["instance_id"] != 0:
			out["omitted"] = [{"field": "texture payload", "index": texture["index"], "reason": "unsupported texture resource"}]
			_refuse("textured native material unsupported")
			return out
	return out


func _surface(node: MeshInstance3D, part: Dictionary) -> Dictionary:
	var out: Dictionary = {"native_surface": 0}
	if not is_instance_valid(node) or node.get_class() != "MeshInstance3D" or node.get_script() != null or node.get_instance_id() != part["native_node_instance_id"]:
		_refuse("final node identity class or script changed")
		return out
	var mesh: Mesh = node.mesh
	out["mesh"] = _identity(mesh)
	if mesh == null or not is_instance_valid(mesh) or mesh.get_class() != "ArrayMesh" or mesh.get_script() != null or mesh.get_instance_id() != part["snapshot"]["mesh_instance_id"]:
		_refuse("native mesh resource differs from trusted array capture")
		return out
	out["surface_count"] = _typed(mesh.get_surface_count())
	out["surface_override_count"] = _typed(node.get_surface_override_material_count())
	if out["surface_count"]["value"] != 1 or out["surface_override_count"]["value"] != 1:
		_refuse("native material surface count differs")
		return out
	var node_override: Material = node.material_override
	var overlay: Material = node.material_overlay
	var surface_override: Material = node.get_surface_override_material(0)
	var mesh_material: Material = mesh.surface_get_material(0)
	var active: Material = node.get_active_material(0)
	out["selection"] = {"node_override": _identity(node_override), "overlay": _identity(overlay),
		"surface_override": _identity(surface_override), "mesh_surface": _identity(mesh_material),
		"active": _identity(active), "precedence": "node override then surface override then mesh surface"}
	out["instance_transparency"] = _typed(node.transparency)
	if not _errors.is_empty():
		return out
	if node_override != null or overlay != null or surface_override != null:
		out["omitted"] = [{"field": "override material payload", "reason": "outside locked import route"}]
		_refuse("native material override or overlay unsupported")
		return out
	if active == null or active != mesh_material:
		_refuse("effective material disagrees with native mesh surface")
		return out
	if out["instance_transparency"]["type"] != TYPE_FLOAT or out["instance_transparency"]["value"] != 0.0:
		_refuse("instance transparency unsupported")
		return out
	out["material"] = _material(active)
	return out


func capture_after_generation_return(state: GLTFState, root: Node) -> Dictionary:
	if _used:
		_refuse("material capture is single use")
		return _finish()
	_used = true
	_result = {"schema": "ontokin.c248.native-materials/0.1", "phase": "CAPTURING",
		"component_complete": false, "execution_admission": false, "native_acceptance": false,
		"R07": "PENDING", "value_origin": "native-api-readback", "parts": []}
	# Fresh private reader: this is the only C247 invocation and registry-consuming path.
	var mesh_reader = MeshReader.new()
	var arrays: Dictionary = mesh_reader.capture_after_generation_return(state, root)
	_result["mesh_arrays"] = arrays
	if not arrays.get("component_complete", false) or arrays.get("phase", "") != "MESH_ARRAYS_CAPTURED_OTHER_RAW_PENDING":
		_refuse("owned mesh-array capture refused")
		return _finish()
	var meshes: Dictionary = _live_meshes(root, arrays)
	if not _errors.is_empty() or not Registry.failure_receipts()["faults"].is_empty():
		_refuse("material capture began with changed scene or registry fault")
		return _finish()
	var seen_materials: Dictionary = {}
	for index in range(MESHES.size()):
		var part: Dictionary = arrays["parts"][index]
		var row: Dictionary = {"source_node": index, "source_mesh": part["source_mesh"],
			"source_primitive": 0, "source_material": MATERIAL_BY_MESH[part["source_mesh"]],
			"native_node_instance_id": part["native_node_instance_id"], "native_surface": 0}
		_result["parts"].append(row)
		row["snapshot"] = _surface(meshes[index], part)
		if not _errors.is_empty():
			return _finish()
		var material: Dictionary = row["snapshot"]["material"]
		var identity: int = material["identity"]["instance_id"]
		if seen_materials.has(identity):
			if seen_materials[identity]["source_material"] != row["source_material"] or seen_materials[identity]["material"] != material:
				_refuse("one native material has conflicting source or raw values")
				return _finish()
		else:
			seen_materials[identity] = {"source_material": row["source_material"], "material": material.duplicate(true)}
	for index in range(MESHES.size()):
		var after: Dictionary = _surface(meshes[index], arrays["parts"][index])
		if not _errors.is_empty() or after != _result["parts"][index]["snapshot"]:
			_result["parts"][index]["after_drift"] = after
			_refuse("native material or selection changed during capture")
			return _finish()
	_live_meshes(root, arrays)
	if not _errors.is_empty() or not Registry.failure_receipts()["faults"].is_empty():
		_refuse("final membership or registry changed during material capture")
		return _finish()
	_result["phase"] = "MATERIAL_PARAMETERS_CAPTURED_OTHER_RAW_PENDING"
	_result["component_complete"] = true
	_result["native_material_count"] = seen_materials.size()
	_result["stability"] = "two equal material reads and final membership; not atomic against concurrent writes"
	return _finish()
