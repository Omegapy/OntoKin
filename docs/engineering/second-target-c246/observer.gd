extends GLTFDocumentExtension
## Held C246 source: unparsed and unexecuted in Godot.
## This extension has no mutable instance state and overrides only _import_node.

const Registry = preload("registry.gd")


func _import_node(state: GLTFState, gltf_node: GLTFNode, json: Dictionary, node: Node) -> Error:
	return Registry.capture(state, gltf_node, json, node)
