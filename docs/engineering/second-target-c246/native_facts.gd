extends RefCounted
## Detached phase-local identity/metadata facts, not the full C241 raw capture.
## Unsupported metadata/callables preserve a refusal marker and poison the session.

const MAX_DEPTH: int = 32
# This bounds visited capture records, not bytes or native API allocations.
# String size and process memory/output enforcement are deferred admission gates.
const MAX_VALUES: int = 100000
var errors: Array = []
var _values: int = 0


func _refuse(reason: String) -> void:
	# One bounded first-error record is enough to poison the enclosing session.
	if errors.is_empty():
		errors.append(reason)


func _consume() -> bool:
	if not errors.is_empty():
		return false
	_values += 1
	if _values > MAX_VALUES:
		_refuse("native fact capture value limit")
		return false
	return true


func typed(value: Variant, depth: int = 0) -> Dictionary:
	var kind: int = typeof(value)
	if not _consume():
		return {"type": kind, "refused": "capture limit or earlier error"}
	if depth > MAX_DEPTH:
		_refuse("metadata depth limit or cycle")
		return {"type": kind, "refused": "capture limit"}
	match kind:
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING:
			return {"type": kind, "value": value}
		TYPE_FLOAT:
			if not is_finite(value):
				_refuse("nonfinite native metadata")
				return {"type": kind, "refused": "nonfinite"}
			return {"type": kind, "value": value}
		TYPE_STRING_NAME, TYPE_NODE_PATH:
			return {"type": kind, "value": str(value)}
		TYPE_ARRAY:
			var entries: Array = []
			for item in value:
				entries.append(typed(item, depth + 1))
				if not errors.is_empty():
					break
			return {"type": kind, "entries": entries}
		TYPE_DICTIONARY:
			var entries: Array = []
			for key in value:
				var captured_key: Dictionary = typed(key, depth + 1)
				if not errors.is_empty():
					entries.append({"key": captured_key, "value_not_read": true})
					break
				entries.append({"key": captured_key, "value": typed(value[key], depth + 1)})
				if not errors.is_empty():
					break
			return {"type": kind, "entries": entries}
		_:
			_refuse("unsupported native metadata Variant type " + str(kind))
			return {"type": kind, "refused": "unsupported type"}


func object_identity(value: Object) -> Dictionary:
	if not _consume():
		return {"refused": "capture limit or earlier error"}
	if value == null:
		return {"instance_id": 0, "class": "null"}
	if not is_instance_valid(value):
		_refuse("invalid live object in native facts")
		return {"refused": "invalid object"}
	return {"instance_id": value.get_instance_id(), "class": value.get_class()}


func metadata(value: Object) -> Array:
	var result: Array = []
	if not errors.is_empty():
		return result
	for key in value.get_meta_list():
		if not _consume():
			break
		var captured_key: Dictionary = typed(key)
		if not errors.is_empty():
			result.append({"key": captured_key, "value_not_read": true})
			break
		result.append({"key": captured_key, "value": typed(value.get_meta(key))})
		if not errors.is_empty():
			break
	return result


func resource_facts(value: Resource) -> Dictionary:
	var result: Dictionary = object_identity(value)
	if not errors.is_empty():
		return result
	result["path"] = value.resource_path
	result["script"] = object_identity(value.get_script())
	if value.get_script() != null:
		_refuse("unexpected script on native resource")
		return result
	if not errors.is_empty():
		return result
	result["metadata"] = metadata(value)
	return result


func connection_facts(connection: Dictionary) -> Dictionary:
	if not _consume():
		return {"refused": "capture limit or earlier error"}
	var target: Callable = connection["callable"]
	var source: Signal = connection["signal"]
	var result: Dictionary = {"source_object_id": source.get_object_id(),
		"target_object_id": target.get_object_id(),
		"flags": connection["flags"], "custom": target.is_custom(),
		"valid": target.is_valid()}
	if target.is_custom() or not target.is_valid():
		_refuse("unsupported custom or invalid original callable")
		return result
	result["signal"] = typed(source.get_name())
	if not errors.is_empty():
		return result
	result["method"] = typed(target.get_method())
	if not errors.is_empty():
		return result
	result["bound"] = typed(target.get_bound_arguments())
	if not errors.is_empty():
		return result
	result["unbound_count"] = target.get_unbound_arguments_count()
	return result


func snapshot(node: Node, root: Node) -> Dictionary:
	var result: Dictionary = object_identity(node)
	result["phase"] = "native-before-this-nodes-observer-connection"
	result["name"] = typed(node.name)
	result["path_from_root"] = typed(root.get_path_to(node))
	result["parent"] = object_identity(node.get_parent())
	result["owner"] = object_identity(node.owner)
	result["script"] = object_identity(node.get_script())
	result["metadata"] = metadata(node)
	if not errors.is_empty():
		return result
	if node.get_script() != null:
		_refuse("unexpected product/root script")
		# Do not invoke script-defined property inventory/getters after this refusal.
		return result
	var signals: Array = []
	result["signals"] = signals
	for signal_info in node.get_signal_list():
		if not _consume():
			return result
		var connections: Array = []
		var declaration: Dictionary = typed(signal_info)
		if not errors.is_empty():
			signals.append({"declaration": declaration, "connections_not_read": true})
			return result
		for connection in node.get_signal_connection_list(signal_info["name"]):
			connections.append(connection_facts(connection))
			if not errors.is_empty():
				break
		signals.append({"declaration": declaration, "connections": connections})
		if not errors.is_empty():
			return result
	var incoming: Array = []
	result["incoming_connections"] = incoming
	for connection in node.get_incoming_connections():
		incoming.append(connection_facts(connection))
		if not errors.is_empty():
			return result
	var resources: Array = []
	result["resource_bindings"] = resources
	for property in node.get_property_list():
		if not _consume():
			return result
		if property["type"] != TYPE_OBJECT:
			continue
		var value: Variant = node.get(property["name"])
		if value is Resource:
			var captured_property: Dictionary = typed(property["name"])
			if not errors.is_empty():
				resources.append({"property": captured_property, "resource_not_read": true})
				return result
			resources.append({"property": captured_property, "resource": resource_facts(value)})
			if not errors.is_empty():
				return result
	result["limits"] = "Resource identity and metadata only; arrays/materials/evaluated poses remain pending"
	return result
