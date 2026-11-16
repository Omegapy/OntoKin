extends "../second-target-c249/animation_inventory.gd"
## Separate C251 predicate; inherited C249 detachment rules remain unchanged.
## Attached branch copies the pinned C249 scene reads with explicit parent/tree changes.

var attached: bool = false
var host_parent: Window
var host_tree: SceneTree


func _scene(root: Node, materials: Dictionary, out: Dictionary) -> Dictionary:
	if not attached:
		return super._scene(root, materials, out)
	var found: Dictionary = {}
	var arrays: Dictionary = materials["mesh_arrays"]
	var chain: Dictionary = arrays["chain"]
	out["nodes"] = []
	out["material_bindings"] = []
	if not is_instance_valid(root) or root.get_class() != "Node3D" or root.get_parent() != host_parent or root.get_instance_id() != chain["root"]["instance_id"] or not root.is_inside_tree() or root.get_tree() != host_tree:
		_refuse("attached root identity parent or tree differs")
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
		if seen.has(identity) or retired.has(identity) or script != null or row["queued_for_deletion"] or not row["inside_tree"] or node.get_tree() != host_tree:
			_refuse("duplicate retired scripted queued or wrongly attached scene member")
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
