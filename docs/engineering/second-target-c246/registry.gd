extends RefCounted
## External one-session registry, separate from every extension instance.
## No loader, process, registration, persistence or admission operation exists here.

const Session = preload("session.gd")
static var _sessions: Dictionary = {}
static var _faults: Array = []
static var _receipts: Array = []
static var _ever_bound: bool = false


static func _poison(reason: String) -> Error:
	_faults.append(reason)
	for session in _sessions.values():
		session.fail("registry: " + reason)
	return ERR_INVALID_DATA


static func bind_state(state: GLTFState) -> Error:
	if not _faults.is_empty() or _ever_bound or not is_instance_valid(state):
		return _poison("invalid, repeated or poisoned session binding")
	_ever_bound = true
	var session = Session.new(state)
	_sessions[state.get_instance_id()] = session
	return OK


static func _lookup(state: GLTFState):
	if not is_instance_valid(state):
		_poison("invalid state")
		return null
	var key: int = state.get_instance_id()
	if not _sessions.has(key) or _sessions[key].state != state:
		_poison("unbound or wrong exact state")
		return null
	if not _faults.is_empty():
		_sessions[key].fail("registry already poisoned")
	return _sessions[key]


static func capture(state: GLTFState, gltf_node: GLTFNode, json: Dictionary, node: Node) -> Error:
	var session = _lookup(state)
	if session == null:
		return ERR_INVALID_DATA
	return session.capture_original(state, gltf_node, json, node)


static func generation_returned(state: GLTFState, root: Node) -> Error:
	# A future reviewed caller must invoke this only after generate_scene returns.
	var session = _lookup(state)
	if session == null:
		return ERR_INVALID_DATA
	return session.generation_returned(state, root)


static func close_state(state: GLTFState) -> Dictionary:
	var session = _lookup(state)
	if session == null:
		return {"component_complete": false, "faults": _faults.duplicate(true)}
	if not session.has_returned:
		_poison("cleanup before generation returned is forbidden")
		return session.receipt()
	var receipt: Dictionary = session.close_after_return()
	_receipts.append(receipt.duplicate(true))
	_sessions.erase(state.get_instance_id())
	return receipt


static func failure_receipts() -> Dictionary:
	var active: Array = []
	for session in _sessions.values():
		active.append(session.receipt())
	return {"faults": _faults.duplicate(true), "closed": _receipts.duplicate(true), "active": active}
