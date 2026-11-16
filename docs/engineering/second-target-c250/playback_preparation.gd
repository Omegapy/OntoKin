extends RefCounted
## Held preparation only: detached, stopped, no evaluation or scene attachment.
## Every prior receipt comes from one fresh owned C249 path, never caller input.

const InventoryReader = preload("../second-target-c249/animation_inventory.gd")
const Registry = preload("../second-target-c246/registry.gd")
const Facts = preload("../second-target-c246/native_facts.gd")
const MESHES: Array = [0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]
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


func _stage_inventory(root: Node, materials: Dictionary, expected: Dictionary, out: Dictionary, reader) -> void:
	out["scene"] = {}
	out["tracks"] = []
	var live: Dictionary = reader._scene(root, materials, out["scene"])
	if not reader._errors.is_empty():
		return
	var player: AnimationPlayer = live["player"]
	var facts = Facts.new()
	out["player"] = {}
	reader._object(player, facts, out["player"])
	if not reader._errors.is_empty():
		return
	var root_path: NodePath = player.root_node
	out["player"]["root_path"] = reader._typed(root_path)
	if root_path.is_absolute() or root_path.is_empty() or root_path.get_subname_count() != 0:
		out["player"]["omitted"] = ["root lookup after unsupported path shape"]
		reader._refuse("unsupported animation root path")
		return
	var root_target: Node = player.get_node_or_null(root_path)
	out["player"]["root_target"] = reader._identity(root_target)
	var settings: Dictionary = {"active": reader._typed(player.active),
		"callback_mode_process": reader._typed(player.callback_mode_process),
		"callback_mode_method": reader._typed(player.callback_mode_method),
		"callback_mode_discrete": reader._typed(player.callback_mode_discrete),
		"deterministic": reader._typed(player.deterministic), "autoplay": reader._typed(player.autoplay),
		"assigned_animation": reader._typed(player.assigned_animation), "current_animation": reader._typed(player.current_animation),
		"playing": reader._typed(player.is_playing()), "queue": facts.typed(player.get_queue()),
		"root_motion_track": reader._typed(player.root_motion_track), "root_motion_local": reader._typed(player.root_motion_local),
		"speed_scale": reader._typed(player.speed_scale), "default_blend_time": reader._typed(player.playback_default_blend_time),
		"auto_capture": reader._typed(player.playback_auto_capture), "has_section": reader._typed(player.has_section())}
	out["player"]["settings"] = settings
	if root_target != root:
		reader._refuse("animation root path does not resolve to owned root")
		return
	if not facts.errors.is_empty() or settings != expected["player"]["settings"]:
		reader._refuse("player settings differ from declared stage")
		return
	var libraries: Array = player.get_animation_library_list()
	out["library_count"] = libraries.size()
	if libraries.size() != 1:
		out["omitted"] = ["library contents outside single-library bound"]
		reader._refuse("ambiguous or missing animation library")
		return
	var library_key: StringName = libraries[0]
	out["library_key"] = reader._typed(library_key)
	if library_key != &"":
		reader._refuse("unsupported nondefault animation library")
		return
	var library: AnimationLibrary = player.get_animation_library(library_key)
	out["library"] = {}
	reader._object(library, facts, out["library"])
	if not reader._errors.is_empty() or library.get_class() != "AnimationLibrary":
		reader._refuse("unsupported native library class")
		return
	var names: Array = library.get_animation_list()
	var player_names: PackedStringArray = player.get_animation_list()
	out["animation_count"] = library.get_animation_list_size()
	out["library_list_count"] = names.size()
	out["player_animation_count"] = player_names.size()
	if out["animation_count"] != 1 or names.size() != 1 or player_names.size() != 1:
		out["omitted"] = ["animation contents outside single-animation bound"]
		reader._refuse("ambiguous or missing native animation")
		return
	var animation_key: StringName = names[0]
	out["animation_key"] = reader._typed(animation_key)
	out["player_animation_key"] = reader._typed(player_names[0])
	if animation_key.is_empty() or animation_key == &"RESET" or str(animation_key) != player_names[0]:
		reader._refuse("ambiguous reserved or inconsistent animation key")
		return
	var animation: Animation = library.get_animation(animation_key)
	var player_animation: Animation = player.get_animation(animation_key)
	out["player_animation"] = reader._identity(player_animation)
	out["animation"] = {}
	reader._object(animation, facts, out["animation"])
	if not reader._errors.is_empty() or animation.get_class() != "Animation" or animation != player_animation:
		reader._refuse("animation resource selection disagrees")
		return
	out["next_animation"] = reader._typed(player.animation_get_next(animation_key))
	out["self_blend_time"] = reader._typed(player.get_blend_time(animation_key, animation_key))
	if not out["next_animation"]["value"].is_empty() or out["self_blend_time"]["value"] != 0.0:
		reader._refuse("unexpected next animation or blend override")
		return
	out["animation"]["length"] = reader._typed(animation.length)
	out["animation"]["step"] = reader._typed(animation.step)
	out["animation"]["loop_mode"] = reader._typed(animation.loop_mode)
	out["animation"]["capture_included"] = reader._typed(animation.capture_included)
	var markers: PackedStringArray = animation.get_marker_names()
	out["animation"]["marker_count"] = markers.size()
	if not markers.is_empty():
		out["animation"]["omitted"] = ["marker payload outside original imported route"]
		reader._refuse("unexpected animation markers")
		return
	if out["animation"]["length"]["value"] != 2.0 or not is_finite(out["animation"]["step"]["value"]) or out["animation"]["step"]["value"] <= 0.0 or out["animation"]["loop_mode"]["value"] != Animation.LOOP_NONE or out["animation"]["capture_included"]["value"]:
		reader._refuse("unsupported animation duration loop step or capture mode")
		return
	out["track_count"] = animation.get_track_count()
	if out["track_count"] != EXPECTED_TRACKS:
		out["omitted"] = ["track contents outside original 36-track bound"]
		reader._refuse("missing or extra native tracks")
		return
	var pairs: Dictionary = {}
	for index in range(EXPECTED_TRACKS):
		var path: NodePath = animation.track_get_path(index)
		var row: Dictionary = {"track_index": index, "type": reader._typed(animation.track_get_type(index)),
			"path": reader._typed(path), "enabled": reader._typed(animation.track_is_enabled(index)),
			"imported": reader._typed(animation.track_is_imported(index)),
			"interpolation": reader._typed(animation.track_get_interpolation_type(index)),
			"loop_wrap": reader._typed(animation.track_get_interpolation_loop_wrap(index)),
			"compressed": reader._typed(animation.track_is_compressed(index))}
		out["tracks"].append(row)
		if row["type"]["value"] not in [Animation.TYPE_POSITION_3D, Animation.TYPE_ROTATION_3D] or not row["enabled"]["value"] or not row["imported"]["value"] or row["interpolation"]["value"] != Animation.INTERPOLATION_LINEAR or not row["loop_wrap"]["value"] or row["compressed"]["value"]:
			row["omitted"] = ["target/key metadata after unsupported track route", "key values never read"]
			reader._refuse("unsupported disabled executable compressed or nonbaseline track")
			return
		if path.is_absolute() or path.is_empty() or path.get_subname_count() != 0:
			row["omitted"] = ["target lookup after unsupported path", "key values never read"]
			reader._refuse("unsupported absolute empty or property/bone track path")
			return
		var target: Node = root_target.get_node_or_null(path)
		row["target"] = reader._identity(target)
		if not reader._errors.is_empty() or target == null or target.get_class() != "MeshInstance3D" or not live["source_by_instance"].has(target.get_instance_id()):
			reader._refuse("track target is not an owned live part")
			return
		row["source_node"] = live["source_by_instance"][target.get_instance_id()]
		row["source_mesh"] = MESHES[row["source_node"]]
		row["source_channel_path"] = "translation" if row["type"]["value"] == Animation.TYPE_POSITION_3D else "rotation"
		var pair: String = str(row["source_node"]) + ":" + str(row["type"]["value"])
		if pairs.has(pair):
			reader._refuse("duplicate source-node track role")
			return
		pairs[pair] = index
		row["key_count"] = reader._typed(animation.track_get_key_count(index))
		if row["key_count"]["value"] <= 0 or row["key_count"]["value"] > MAX_KEYS_PER_TRACK:
			row["omitted"] = ["key times and values outside inventory scope"]
			reader._refuse("empty or oversized native key inventory")
			return
		row["key_payload"] = "not read; count does not prove key times values or evaluation"
	out["source_animation_index"] = 0
	out["source_association"] = "sole animation under pinned importer route; no public source/native pointer attestation"
	var final_scene: Dictionary = {}
	reader._scene(root, materials, final_scene)
	if not reader._errors.is_empty() or final_scene != out["scene"]:
		out["scene_after_drift"] = final_scene
		reader._refuse("scene or source resource bindings changed during inventory")
		return
	if player.get_animation_library_list() != libraries or player.get_animation_library(library_key) != library or library.get_animation_list() != names or library.get_animation_list_size() != 1 or player.get_animation_list() != player_names or library.get_animation(animation_key) != animation or player.get_animation(animation_key) != animation:
		reader._refuse("live animation selection changed during inventory")

	if not reader._errors.is_empty() or out != expected:
		reader._refuse("native inventory differs from retained inventory and declared changes")


func _boundary(root: Node, materials: Dictionary, expected: Dictionary, assigned: bool) -> Dictionary:
	# Fresh helper reads bindings only and never captures or consumes the registry
	var reader = InventoryReader.new()
	var receipt: Dictionary = {"complete": false, "inventory": {}, "control": {}, "errors": []}
	_stage_inventory(root, materials, expected, receipt["inventory"], reader)
	if not reader._errors.is_empty():
		receipt["errors"] = reader._errors.duplicate(true)
		receipt["omitted"] = ["control getters after incomplete live inventory"]
		return {"receipt": receipt, "player": null}
	var live_scene: Dictionary = {}
	var live: Dictionary = reader._scene(root, materials, live_scene)
	if not reader._errors.is_empty() or live_scene != expected["scene"]:
		receipt["scene_after_drift"] = live_scene
		receipt["errors"] = ["scene changed before control boundary"]
		return {"receipt": receipt, "player": null}
	var player: AnimationPlayer = live["player"]
	var control: Dictionary = receipt["control"]
	control["player"] = reader._identity(player)
	control["internal_idle"] = reader._typed(player.is_processing_internal())
	control["internal_physics"] = reader._typed(player.is_physics_processing_internal())
	control["blocking_signals"] = reader._typed(player.is_blocking_signals())
	var receivers: Array = player.get_signal_connection_list(&"current_animation_changed")
	control["assignment_signal_connection_count"] = receivers.size()
	if not receivers.is_empty():
		control["omitted"] = ["signal Callable payload; every receiver refuses"]
		receipt["errors"] = ["assignment signal has a receiver"]
		return {"receipt": receipt, "player": null}
	if control["internal_idle"]["value"] or control["internal_physics"]["value"] or control["blocking_signals"]["value"]:
		receipt["errors"] = ["unexpected internal processing or blocked signals"]
		return {"receipt": receipt, "player": null}
	# The public binding of C++ is_valid is is_animation_active
	control["animation_active"] = reader._typed(player.is_animation_active())
	if control["animation_active"]["value"] != assigned:
		receipt["errors"] = ["assignment pointer state differs from declared stage"]
		return {"receipt": receipt, "player": null}
	if assigned:
		control["position"] = reader._typed(player.current_animation_position)
		control["length"] = reader._typed(player.current_animation_length)
		if control["position"]["value"] != 0.0 or control["length"]["value"] != 2.0:
			receipt["errors"] = ["stopped assignment position or length differs"]
			return {"receipt": receipt, "player": null}
	else:
		control["omitted"] = ["position and length require an assigned playback pointer"]
	# Repeat live scene and resource/target inventory after control getter reads
	var final_inventory: Dictionary = {}
	_stage_inventory(root, materials, expected, final_inventory, reader)
	receipt["inventory_recheck"] = final_inventory
	if not reader._errors.is_empty():
		receipt["errors"] = reader._errors.duplicate(true)
		return {"receipt": receipt, "player": null}
	var final_receivers: Array = player.get_signal_connection_list(&"current_animation_changed")
	control["final_assignment_signal_connection_count"] = final_receivers.size()
	control["final_internal_idle"] = reader._typed(player.is_processing_internal())
	control["final_internal_physics"] = reader._typed(player.is_physics_processing_internal())
	control["final_animation_active"] = reader._typed(player.is_animation_active())
	control["final_blocking_signals"] = reader._typed(player.is_blocking_signals())
	if not final_receivers.is_empty():
		control["final_omitted"] = ["signal Callable payload; every receiver refuses"]
	if not final_receivers.is_empty() or control["final_internal_idle"]["value"] or control["final_internal_physics"]["value"] or control["final_animation_active"]["value"] != assigned or control["final_blocking_signals"]["value"]:
		receipt["errors"] = ["control or signal drift at mutation boundary"]
		return {"receipt": receipt, "player": null}
	if assigned:
		control["final_position"] = reader._typed(player.current_animation_position)
		control["final_length"] = reader._typed(player.current_animation_length)
		if control["final_position"]["value"] != 0.0 or control["final_length"]["value"] != 2.0:
			receipt["errors"] = ["stopped assignment position or length drift at final boundary"]
			return {"receipt": receipt, "player": null}
	if not Registry.failure_receipts()["faults"].is_empty():
		receipt["errors"] = ["registry fault at mutation boundary"]
		return {"receipt": receipt, "player": null}
	receipt["complete"] = true
	return {"receipt": receipt, "player": player}


func _expected_inventory(original: Dictionary, process_mode: int, assignment: StringName) -> Dictionary:
	var expected: Dictionary = original.duplicate(true)
	expected["player"]["settings"]["callback_mode_process"]["value"] = process_mode
	expected["player"]["settings"]["assigned_animation"]["value"] = str(assignment)
	return expected


func capture_after_generation_return(state: GLTFState, root: Node) -> Dictionary:
	if _used:
		_refuse("playback preparation is single use; reentry or retry refused")
		return _finish()
	_used = true
	_result = {"schema": "ontokin.c250.native-playback-preparation/0.1", "phase": "CAPTURING",
		"component_complete": false, "execution_admission": false, "native_acceptance": false,
		"R07": "PENDING", "value_origin": "native-api-readback", "mutations": [],
		"rollback": "never attempted; partial observed changes remain",
		"omissions": ["seek and advancement", "world transforms and 126 poses", "tree attachment", "serialization and raw sealing"]}
	var inventory_reader = InventoryReader.new()
	var inventory: Dictionary = inventory_reader.capture_after_generation_return(state, root)
	_result["animation_inventory"] = inventory
	if not inventory.get("component_complete", false) or inventory.get("phase", "") != "ANIMATION_INVENTORY_CAPTURED_POSES_PENDING" or not _errors.is_empty():
		_refuse("owned animation inventory refused")
		return _finish()
	var materials: Dictionary = inventory["materials"]
	var original: Dictionary = inventory["inventory"]
	var key: StringName = StringName(original["animation_key"]["value"])
	var before_manual: Dictionary = _boundary(root, materials, original, false)
	_result["before_manual"] = before_manual["receipt"]
	if not before_manual["receipt"]["complete"] or not _errors.is_empty():
		_refuse("manual-control boundary refused")
		return _finish()
	var player: AnimationPlayer = before_manual["player"]
	var manual: Dictionary = {"operation": "set_callback_mode_process", "requested": AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL,
		"status": "ATTEMPTED", "before": before_manual["receipt"], "after": {"status": "NOT_OBSERVED"}}
	_result["mutations"].append(manual)
	player.set_callback_mode_process(AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL)
	manual["status"] = "RETURNED"
	var manual_expected: Dictionary = _expected_inventory(original, AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL, &"")
	var after_manual: Dictionary = _boundary(root, materials, manual_expected, false)
	manual["after"] = after_manual["receipt"]
	if not after_manual["receipt"]["complete"] or not _errors.is_empty():
		manual["outcome"] = "REFUSED_AFTER_ATTEMPT"
		_refuse("manual-control readback refused; changes retained")
		return _finish()
	manual["outcome"] = "DECLARED_CHANGE_OBSERVED"
	# This new boundary closes the first setter before preparing the second setter
	var before_assignment: Dictionary = _boundary(root, materials, manual_expected, false)
	_result["before_assignment"] = before_assignment["receipt"]
	if not before_assignment["receipt"]["complete"] or not _errors.is_empty():
		_refuse("stopped-assignment boundary refused; manual change retained")
		return _finish()
	player = before_assignment["player"]
	var assignment: Dictionary = {"operation": "set_assigned_animation", "requested": str(key),
		"status": "ATTEMPTED", "before": before_assignment["receipt"], "after": {"status": "NOT_OBSERVED"}}
	_result["mutations"].append(assignment)
	player.set_assigned_animation(key)
	assignment["status"] = "RETURNED"
	var assigned_expected: Dictionary = _expected_inventory(original, AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL, key)
	var after_assignment: Dictionary = _boundary(root, materials, assigned_expected, true)
	assignment["after"] = after_assignment["receipt"]
	if not after_assignment["receipt"]["complete"] or not _errors.is_empty():
		assignment["outcome"] = "REFUSED_AFTER_ATTEMPT"
		_refuse("stopped-assignment readback refused; changes retained")
		return _finish()
	assignment["outcome"] = "DECLARED_CHANGE_OBSERVED"
	_result["phase"] = "DETACHED_MANUAL_STOPPED_ASSIGNMENT_PREPARED_POSES_PENDING"
	_result["component_complete"] = true
	_result["stability"] = "bounded before/after live readbacks; no atomicity or transient-mutation guarantee"
	return _finish()
