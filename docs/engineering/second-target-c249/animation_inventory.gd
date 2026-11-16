extends RefCounted
## Held read-only animation inventory; never assigns, advances, parses or launches.
## The fresh owned C248 reader is the sole path that consumes C246/C247.

const MaterialReader = preload("../second-target-c248/materials.gd")
const Registry = preload("../second-target-c246/registry.gd")
const Facts = preload("../second-target-c246/native_facts.gd")
const MESHES: Array = [0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]
const MAX_SCENE_NODES: int = 64
const EXPECTED_TRACKS: int = 36
const MAX_KEYS_PER_TRACK: int = 4096
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
	var kind: int = typeof(value)
	if kind == TYPE_NODE_PATH or kind == TYPE_STRING_NAME:
		return {"type": kind, "value": str(value)}
	return {"type": kind, "value": value}


func _identity(value: Object) -> Dictionary:
	if value == null:
		return {"type": TYPE_NIL, "instance_id": 0, "class": "null"}
	if not is_instance_valid(value):
		_refuse("invalid native identity")
		return {"type": TYPE_OBJECT, "refused": "invalid object"}
	return {"type": TYPE_OBJECT, "instance_id": value.get_instance_id(), "class": value.get_class()}


func _object(value: Object, facts, out: Dictionary) -> void:
	out["identity"] = _identity(value)
	if not _errors.is_empty() or value == null:
		_refuse("missing inventory object")
		return
	out["queued_for_deletion"] = value.is_queued_for_deletion()
	var captured_script: Variant = value.get_script()
	out["script"] = _identity(captured_script)
	if captured_script != null or out["queued_for_deletion"]:
		_refuse("scripted or queued inventory object")
		return
	if value is Node:
		out["name"] = _typed(value.name)
	else:
		out["resource_name"] = _typed(value.resource_name)
		out["resource_path"] = _typed(value.resource_path)
	out["metadata"] = facts.metadata(value)
	if not facts.errors.is_empty():
		out["metadata_errors"] = facts.errors.duplicate(true)
		_refuse("unsupported or incomplete native metadata")


func _scene(root: Node, materials: Dictionary, out: Dictionary) -> Dictionary:
	var found: Dictionary = {}
	var arrays: Dictionary = materials["mesh_arrays"]
	var chain: Dictionary = arrays["chain"]
	out["nodes"] = []
	out["material_bindings"] = []
	if not is_instance_valid(root) or root.get_class() != "Node3D" or root.get_parent() != null or root.get_instance_id() != chain["root"]["instance_id"] or root.is_inside_tree():
		_refuse("returned root changed or entered the scene tree")
		return found
	if materials["parts"].size() != MESHES.size():
		_refuse("incomplete owned material receipt")
		return found
	var wanted: Dictionary = {}
	var retired: Dictionary = {}
	for index in range(MESHES.size()):
		var part: Dictionary = materials["parts"][index]
		if part["source_node"] != index or part["source_mesh"] != MESHES[index] or part["source_primitive"] != 0 or part["native_surface"] != 0:
			_refuse("owned source association differs")
			return found
		var identity: int = part["native_node_instance_id"]
		if wanted.has(identity) or identity != chain["finals"][index]["new"]:
			_refuse("ambiguous owned final identity")
			return found
		wanted[identity] = index
		retired[chain["originals"][index]["old"]] = true
	var pending: Array = [root]
	var seen: Dictionary = {}
	var meshes: Dictionary = {}
	var players: Array = []
	while not pending.is_empty():
		if seen.size() >= MAX_SCENE_NODES:
			_refuse("animation scene traversal bound exceeded")
			return found
		var node: Node = pending.pop_back()
		if not is_instance_valid(node):
			_refuse("invalid final scene member")
			return found
		var identity: int = node.get_instance_id()
		var script: Variant = node.get_script()
		var row: Dictionary = {"identity": _identity(node), "script": _identity(script),
			"queued_for_deletion": node.is_queued_for_deletion(), "inside_tree": node.is_inside_tree(),
			"name": _typed(node.name), "parent": _identity(node.get_parent()),
			"owner": _identity(node.owner), "path_from_root": _typed(root.get_path_to(node))}
		out["nodes"].append(row)
		if seen.has(identity) or retired.has(identity) or script != null or row["queued_for_deletion"] or row["inside_tree"]:
			_refuse("duplicate retired scripted queued or attached scene member")
			return found
		seen[identity] = true
		if node != root:
			if node.get_parent() != root:
				_refuse("unexpected finite fixture hierarchy")
				return found
			if node.get_class() == "MeshInstance3D":
				if not wanted.has(identity):
					_refuse("unmapped final mesh")
					return found
				meshes[wanted[identity]] = node
			elif node.get_class() == "AnimationPlayer":
				players.append(node)
			else:
				_refuse("unsupported scene member or additional mixer")
				return found
		var children: Array = node.get_children(true)
		if pending.size() + seen.size() + children.size() > MAX_SCENE_NODES:
			_refuse("animation scene traversal bound exceeded")
			return found
		pending.append_array(children)
	out["player_count"] = players.size()
	if meshes.size() != MESHES.size() or players.size() != 1:
		_refuse("missing mesh or ambiguous animation player")
		return found
	for index in range(MESHES.size()):
		var node: MeshInstance3D = meshes[index]
		var expected: Dictionary = materials["parts"][index]["snapshot"]
		var mesh: Mesh = node.mesh
		var row: Dictionary = {"source_node": index, "node": _identity(node), "mesh": _identity(mesh)}
		out["material_bindings"].append(row)
		if mesh == null or not is_instance_valid(mesh) or mesh.get_class() != "ArrayMesh" or row["mesh"] != expected["mesh"]:
			_refuse("owned mesh binding changed")
			return found
		var mesh_script: Variant = mesh.get_script()
		row["mesh_script"] = _identity(mesh_script)
		row["surface_count"] = mesh.get_surface_count()
		row["surface_override_count"] = node.get_surface_override_material_count()
		if mesh_script != null or mesh.is_queued_for_deletion() or row["surface_count"] != 1 or row["surface_override_count"] != 1:
			_refuse("mesh script lifetime or surface inventory changed")
			return found
		var node_override: Material = node.material_override
		var overlay: Material = node.material_overlay
		var surface_override: Material = node.get_surface_override_material(0)
		var material: Material = mesh.surface_get_material(0)
		var active: Material = node.get_active_material(0)
		row["selection"] = {"node_override": _identity(node_override), "overlay": _identity(overlay),
			"surface_override": _identity(surface_override), "mesh_surface": _identity(material),
			"active": _identity(active), "precedence": "node override then surface override then mesh surface"}
		row["instance_transparency"] = _typed(node.transparency)
		if not _errors.is_empty() or row["selection"] != expected["selection"] or row["instance_transparency"] != expected["instance_transparency"] or material == null or material != active:
			_refuse("owned material or selector binding changed")
			return found
		var material_script: Variant = material.get_script()
		row["material_script"] = _identity(material_script)
		if material_script != null or material.is_queued_for_deletion():
			_refuse("owned material script or lifetime changed")
			return found
	found = {"meshes": meshes, "player": players[0], "source_by_instance": wanted}
	return found


func _inventory(root: Node, materials: Dictionary, out: Dictionary) -> void:
	out["scene"] = {}
	out["tracks"] = []
	var live: Dictionary = _scene(root, materials, out["scene"])
	if not _errors.is_empty():
		return
	var player: AnimationPlayer = live["player"]
	var facts = Facts.new()
	out["player"] = {}
	_object(player, facts, out["player"])
	if not _errors.is_empty():
		return
	var root_path: NodePath = player.root_node
	out["player"]["root_path"] = _typed(root_path)
	if root_path.is_absolute() or root_path.is_empty() or root_path.get_subname_count() != 0:
		out["player"]["omitted"] = ["root lookup after unsupported path shape"]
		_refuse("unsupported animation root path")
		return
	var root_target: Node = player.get_node_or_null(root_path)
	out["player"]["root_target"] = _identity(root_target)
	var settings: Dictionary = {"active": _typed(player.active),
		"callback_mode_process": _typed(player.callback_mode_process),
		"callback_mode_method": _typed(player.callback_mode_method),
		"callback_mode_discrete": _typed(player.callback_mode_discrete),
		"deterministic": _typed(player.deterministic), "autoplay": _typed(player.autoplay),
		"assigned_animation": _typed(player.assigned_animation), "current_animation": _typed(player.current_animation),
		"playing": _typed(player.is_playing()), "queue": facts.typed(player.get_queue()),
		"root_motion_track": _typed(player.root_motion_track), "root_motion_local": _typed(player.root_motion_local),
		"speed_scale": _typed(player.speed_scale), "default_blend_time": _typed(player.playback_default_blend_time),
		"auto_capture": _typed(player.playback_auto_capture), "has_section": _typed(player.has_section())}
	out["player"]["settings"] = settings
	if root_target != root:
		_refuse("animation root path does not resolve to owned root")
		return
	if not facts.errors.is_empty() or settings["playing"]["value"] or settings["has_section"]["value"] or not settings["autoplay"]["value"].is_empty() or not settings["assigned_animation"]["value"].is_empty() or not settings["current_animation"]["value"].is_empty() or not settings["queue"].get("entries", []).is_empty():
		_refuse("player has playback assignment queue or incomplete settings")
		return
	if not settings["root_motion_track"]["value"].is_empty() or settings["root_motion_local"]["value"] or settings["speed_scale"]["value"] != 1.0 or settings["default_blend_time"]["value"] != 0.0:
		_refuse("unsupported root motion speed or blending")
		return
	if settings["active"]["value"] != true or settings["callback_mode_process"]["value"] != AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_IDLE or settings["callback_mode_method"]["value"] != AnimationMixer.ANIMATION_CALLBACK_MODE_METHOD_DEFERRED or settings["callback_mode_discrete"]["value"] != AnimationMixer.ANIMATION_CALLBACK_MODE_DISCRETE_RECESSIVE or settings["deterministic"]["value"] != false or settings["auto_capture"]["value"] != true:
		_refuse("unsupported imported player mode")
		return
	var libraries: Array = player.get_animation_library_list()
	out["library_count"] = libraries.size()
	if libraries.size() != 1:
		out["omitted"] = ["library contents outside single-library bound"]
		_refuse("ambiguous or missing animation library")
		return
	var library_key: StringName = libraries[0]
	out["library_key"] = _typed(library_key)
	if library_key != &"":
		_refuse("unsupported nondefault animation library")
		return
	var library: AnimationLibrary = player.get_animation_library(library_key)
	out["library"] = {}
	_object(library, facts, out["library"])
	if not _errors.is_empty() or library.get_class() != "AnimationLibrary":
		_refuse("unsupported native library class")
		return
	var names: Array = library.get_animation_list()
	var player_names: PackedStringArray = player.get_animation_list()
	out["animation_count"] = library.get_animation_list_size()
	out["library_list_count"] = names.size()
	out["player_animation_count"] = player_names.size()
	if out["animation_count"] != 1 or names.size() != 1 or player_names.size() != 1:
		out["omitted"] = ["animation contents outside single-animation bound"]
		_refuse("ambiguous or missing native animation")
		return
	var animation_key: StringName = names[0]
	out["animation_key"] = _typed(animation_key)
	out["player_animation_key"] = _typed(player_names[0])
	if animation_key.is_empty() or animation_key == &"RESET" or str(animation_key) != player_names[0]:
		_refuse("ambiguous reserved or inconsistent animation key")
		return
	var animation: Animation = library.get_animation(animation_key)
	var player_animation: Animation = player.get_animation(animation_key)
	out["player_animation"] = _identity(player_animation)
	out["animation"] = {}
	_object(animation, facts, out["animation"])
	if not _errors.is_empty() or animation.get_class() != "Animation" or animation != player_animation:
		_refuse("animation resource selection disagrees")
		return
	out["next_animation"] = _typed(player.animation_get_next(animation_key))
	out["self_blend_time"] = _typed(player.get_blend_time(animation_key, animation_key))
	if not out["next_animation"]["value"].is_empty() or out["self_blend_time"]["value"] != 0.0:
		_refuse("unexpected next animation or blend override")
		return
	out["animation"]["length"] = _typed(animation.length)
	out["animation"]["step"] = _typed(animation.step)
	out["animation"]["loop_mode"] = _typed(animation.loop_mode)
	out["animation"]["capture_included"] = _typed(animation.capture_included)
	var markers: PackedStringArray = animation.get_marker_names()
	out["animation"]["marker_count"] = markers.size()
	if not markers.is_empty():
		out["animation"]["omitted"] = ["marker payload outside original imported route"]
		_refuse("unexpected animation markers")
		return
	if out["animation"]["length"]["value"] != 2.0 or not is_finite(out["animation"]["step"]["value"]) or out["animation"]["step"]["value"] <= 0.0 or out["animation"]["loop_mode"]["value"] != Animation.LOOP_NONE or out["animation"]["capture_included"]["value"]:
		_refuse("unsupported animation duration loop step or capture mode")
		return
	out["track_count"] = animation.get_track_count()
	if out["track_count"] != EXPECTED_TRACKS:
		out["omitted"] = ["track contents outside original 36-track bound"]
		_refuse("missing or extra native tracks")
		return
	var pairs: Dictionary = {}
	for index in range(EXPECTED_TRACKS):
		var path: NodePath = animation.track_get_path(index)
		var row: Dictionary = {"track_index": index, "type": _typed(animation.track_get_type(index)),
			"path": _typed(path), "enabled": _typed(animation.track_is_enabled(index)),
			"imported": _typed(animation.track_is_imported(index)),
			"interpolation": _typed(animation.track_get_interpolation_type(index)),
			"loop_wrap": _typed(animation.track_get_interpolation_loop_wrap(index)),
			"compressed": _typed(animation.track_is_compressed(index))}
		out["tracks"].append(row)
		if row["type"]["value"] not in [Animation.TYPE_POSITION_3D, Animation.TYPE_ROTATION_3D] or not row["enabled"]["value"] or not row["imported"]["value"] or row["interpolation"]["value"] != Animation.INTERPOLATION_LINEAR or not row["loop_wrap"]["value"] or row["compressed"]["value"]:
			row["omitted"] = ["target/key metadata after unsupported track route", "key values never read"]
			_refuse("unsupported disabled executable compressed or nonbaseline track")
			return
		if path.is_absolute() or path.is_empty() or path.get_subname_count() != 0:
			row["omitted"] = ["target lookup after unsupported path", "key values never read"]
			_refuse("unsupported absolute empty or property/bone track path")
			return
		var target: Node = root_target.get_node_or_null(path)
		row["target"] = _identity(target)
		if not _errors.is_empty() or target == null or target.get_class() != "MeshInstance3D" or not live["source_by_instance"].has(target.get_instance_id()):
			_refuse("track target is not an owned live part")
			return
		row["source_node"] = live["source_by_instance"][target.get_instance_id()]
		row["source_mesh"] = MESHES[row["source_node"]]
		row["source_channel_path"] = "translation" if row["type"]["value"] == Animation.TYPE_POSITION_3D else "rotation"
		var pair: String = str(row["source_node"]) + ":" + str(row["type"]["value"])
		if pairs.has(pair):
			_refuse("duplicate source-node track role")
			return
		pairs[pair] = index
		row["key_count"] = _typed(animation.track_get_key_count(index))
		if row["key_count"]["value"] <= 0 or row["key_count"]["value"] > MAX_KEYS_PER_TRACK:
			row["omitted"] = ["key times and values outside inventory scope"]
			_refuse("empty or oversized native key inventory")
			return
		row["key_payload"] = "not read; count does not prove key times values or evaluation"
	out["source_animation_index"] = 0
	out["source_association"] = "sole animation under pinned importer route; no public source/native pointer attestation"
	var final_scene: Dictionary = {}
	_scene(root, materials, final_scene)
	if not _errors.is_empty() or final_scene != out["scene"]:
		out["scene_after_drift"] = final_scene
		_refuse("scene or source resource bindings changed during inventory")
		return
	if player.get_animation_library_list() != libraries or player.get_animation_library(library_key) != library or library.get_animation_list() != names or library.get_animation_list_size() != 1 or player.get_animation_list() != player_names or library.get_animation(animation_key) != animation or player.get_animation(animation_key) != animation:
		_refuse("live animation selection changed during inventory")


func capture_after_generation_return(state: GLTFState, root: Node) -> Dictionary:
	if _used:
		_refuse("animation inventory is single use")
		return _finish()
	_used = true
	_result = {"schema": "ontokin.c249.native-animation-inventory/0.1", "phase": "CAPTURING",
		"component_complete": false, "execution_admission": false, "native_acceptance": false,
		"R07": "PENDING", "value_origin": "native-api-readback",
		"omissions": ["key times and values", "playback assignment and advancement control", "seek and 126-pose evaluation", "serialization and raw sealing"]}
	var material_reader = MaterialReader.new()
	var materials: Dictionary = material_reader.capture_after_generation_return(state, root)
	_result["materials"] = materials
	if not materials.get("component_complete", false) or materials.get("phase", "") != "MATERIAL_PARAMETERS_CAPTURED_OTHER_RAW_PENDING":
		_refuse("owned material capture refused")
		return _finish()
	if not Registry.failure_receipts()["faults"].is_empty():
		_refuse("registry fault before animation inventory")
		return _finish()
	_result["inventory"] = {}
	_inventory(root, materials, _result["inventory"])
	if not _errors.is_empty():
		return _finish()
	_result["recheck"] = {}
	_inventory(root, materials, _result["recheck"])
	if not _errors.is_empty() or _result["inventory"] != _result["recheck"]:
		_refuse("native animation inventory changed during capture")
		return _finish()
	if not Registry.failure_receipts()["faults"].is_empty():
		_refuse("registry changed during animation inventory")
		return _finish()
	_result["phase"] = "ANIMATION_INVENTORY_CAPTURED_POSES_PENDING"
	_result["component_complete"] = true
	_result["stability"] = "two equal inventories with final membership/resource lookup rechecks; not atomic against concurrent writes"
	return _finish()
