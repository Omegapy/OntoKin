"""Pinned Blender-only constructor for the finite static-tray record.

No source parsing, physics, simulation, source-derived expectations, or reader
imports occur here.  The host validates and binds the record before launch.
"""
import sys

sys.dont_write_bytecode = True

import hashlib
import json
import logging
from pathlib import Path
import shutil
import struct
import bpy
from mathutils import Matrix, Quaternion, Vector


C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
PARTS = ("back", "base", "front", "left-wall", "payload", "right-wall")
COLORS = {"tray": (0.25, 0.5, 0.75, 1), "payload": (0.75, 0.5, 0.25, 1)}
PINNED_EXPORTER_SHA256 = "82428a0415e11c27a285fd950f63e874add5ba2f8bacc6806ed762614560fa2e"
FILTER_PROPERTIES = ("gltf_action_filter", "gltf_action_filter_active")


def scalar(bits):
    return struct.unpack(">d", bytes.fromhex(bits))[0]


def vector(bits):
    return Vector(tuple(scalar(value) for value in bits))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False))


def python_startup():
    flags = {name:getattr(sys.flags,name) for name in
             ("isolated","ignore_environment","no_user_site","no_site","safe_path","hash_randomization","dont_write_bytecode")}
    required = {"isolated":0,"ignore_environment":0,"no_user_site":1,"safe_path":True,
                "hash_randomization":0,"dont_write_bytecode":1}
    if any(flags[key] != value for key,value in required.items()) or not sys.dont_write_bytecode:
        raise RuntimeError("Actual embedded Python startup differs from the frozen environment")
    return {"flags":flags,"dont_write_bytecode":sys.dont_write_bytecode,"sys_path":list(sys.path),
            "executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,
            "python_version":sys.version}


def materials():
    values = {}
    for key, color in COLORS.items():
        material = bpy.data.materials.new(key)
        material.diffuse_color = color
        material.use_nodes = True
        material.use_backface_culling = True
        node = material.node_tree.nodes.get("Principled BSDF")
        node.inputs["Base Color"].default_value = color
        node.inputs["Metallic"].default_value = 0
        node.inputs["Roughness"].default_value = 0.75
        node.inputs["Alpha"].default_value = 1
        values[key] = material
    return values


def metadata(obj, row, part=False):
    obj["semantic_id"] = list(row["id"])
    obj["owner_id"] = list(row["owner_id"])
    obj["role"] = row["role"]
    if part:
        obj["follow_id"] = list(row["following"]["id"])
        obj["follow_parent_id"] = list(row["following"]["parent_id"])


def box(row):
    sx, sy, sz = [scalar(value) / 2 for value in row["geometry"]["size_m"]]
    source = [(-sx,-sy,-sz),(sx,-sy,-sz),(sx,sy,-sz),(-sx,sy,-sz),
              (-sx,-sy,sz),(sx,-sy,sz),(sx,sy,sz),(-sx,sy,sz)]
    vertices = [tuple(C @ Vector(point)) for point in source]
    quads = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]
    triangles = [triangle for a,b,c,d in quads for triangle in [(a,b,c),(a,c,d)]]
    mesh = bpy.data.meshes.new("/".join(row["id"])+"/mesh")
    mesh.from_pydata(vertices, [], triangles)
    mesh.update()
    for face in mesh.polygons:
        face.use_smooth = False
    return mesh


def assert_operator(operator, settings):
    runtime = {prop.identifier for prop in operator.get_rna_type().properties if prop.identifier != "rna_type"}
    if runtime != set(settings):
        raise RuntimeError("Frozen operator property coverage differs: missing="+
                           str(sorted(runtime-set(settings)))+" extra="+str(sorted(set(settings)-runtime)))


def exporter_compatibility(settings):
    """Bind the pinned exporter's logging branch and inactive-filter policy."""
    assert_operator(bpy.ops.export_scene.gltf, settings)
    if (settings.get("export_loglevel") != -1 or settings.get("export_action_filter") is not False
            or settings.get("export_animations") is not False or settings.get("will_save_settings") is not False):
        raise RuntimeError("Pinned static exporter compatibility settings differ")
    addon = sys.modules.get("io_scene_gltf2")
    if addon is None or digest(addon.__file__) != PINNED_EXPORTER_SHA256:
        raise RuntimeError("Pinned exporter implementation differs")
    debug = {name:getattr(bpy.app, name) for name in ("debug", "debug_python", "debug_value")}
    if debug != {"debug":False, "debug_python":False, "debug_value":0}:
        raise RuntimeError("Pinned exporter debug state differs")
    resolved_log_level = addon.set_debug_log()
    if resolved_log_level != logging.INFO:
        raise RuntimeError("Pinned exporter effective logging differs")
    return addon, {"exporter_sha256":PINNED_EXPORTER_SHA256,
                   "operator_context":"EXEC_DEFAULT", "operator_property_count":len(settings),
                   "debug":debug, "requested_log_level":-1, "resolved_log_level":resolved_log_level,
                   "action_filter":False,
                   "action_filter_policy":"initialize-empty-properties-before-explicit-false",
                   "omitted_operator_properties":[]}


def prepare_inactive_action_filter(addon):
    """Initialize the empty state that the pinned False callback removes."""
    scene = bpy.context.scene
    if len(bpy.data.scenes) != 1 or bpy.data.scenes[0] != scene or len(bpy.data.actions) != 0:
        raise RuntimeError("Inactive action filter requires the single action-free static scene")
    if any(hasattr(bpy.types.Scene, name) or hasattr(scene, name) for name in FILTER_PROPERTIES):
        raise RuntimeError("Unexpected preexisting action-filter state")
    bpy.types.Scene.gltf_action_filter = bpy.props.CollectionProperty(type=addon.GLTF2_filter_action)
    bpy.types.Scene.gltf_action_filter_active = bpy.props.IntProperty()
    observed = {"action_count":len(bpy.data.actions), "scene_count":len(bpy.data.scenes),
                "filter_count":len(scene.gltf_action_filter),
                "active_index":scene.gltf_action_filter_active}
    if observed != {"action_count":0, "scene_count":1, "filter_count":0, "active_index":0}:
        raise RuntimeError("Empty inactive action-filter initialization differs")
    return observed


def export_with_startup_receipt(settings, startup, job, out):
    """Retain measured startup before export, including a failed export."""
    addon, policy = exporter_compatibility(settings)
    initialized = prepare_inactive_action_filter(addon)
    write_json(out/"native-startup.json", {
        "schema":"ontokin.static-tray.native-startup/0.1.0", "phase":"BEFORE_EXPORT",
        "delivery_state":"NOT_EXPORTED", "blender_version":list(bpy.app.version),
        "build_hash":bpy.app.build_hash.decode(), "python_startup":startup,
        "operator_settings":settings, "exporter_policy":policy,
        "action_filter_initialization":initialized,
        "record_sha256":job["record_sha256"], "settings_sha256":job["settings_sha256"]})
    status = bpy.ops.export_scene.gltf("EXEC_DEFAULT", **settings)
    if status != {"FINISHED"}:
        raise RuntimeError("GLB export did not finish")
    if any(hasattr(bpy.types.Scene, name) or hasattr(bpy.context.scene, name) for name in FILTER_PROPERTIES):
        raise RuntimeError("Inactive action-filter callback did not remove its transient state")
    if len(bpy.data.actions) != 0:
        raise RuntimeError("Static export unexpectedly created action state")
    _, after = exporter_compatibility(settings)
    if after != policy:
        raise RuntimeError("Exporter policy changed during export")
    logging_observed = {"logger_level":logging.getLogger("glTFImporter").level,
                        "error_logger_level":logging.getLogger("glTFImporter_errors").level}
    if logging_observed != {"logger_level":logging.INFO, "error_logger_level":logging.ERROR}:
        raise RuntimeError("Actual exporter logger levels differ")
    return {**policy, "logging_observed":logging_observed,
            "action_filter_properties_removed":True,
            "startup_receipt_sha256":digest(out/"native-startup.json")}


def main():
    args = sys.argv[sys.argv.index("--")+1:]
    if len(args) != 2 or args[0] != "--job":
        raise ValueError("Expected one locked job file")
    job = json.loads(Path(args[1]).read_bytes())
    out = Path.cwd().resolve()
    if Path(job["output_directory"]).resolve() != out:
        raise RuntimeError("Output directory differs from the private stage")
    if tuple(bpy.app.version) != (4,5,3) or bpy.app.build_hash.decode() != "67807e1800cc":
        raise RuntimeError("Blender version/build mismatch")
    startup = python_startup()
    if digest(job["record_path"]) != job["record_sha256"] or digest(job["settings_path"]) != job["settings_sha256"]:
        raise RuntimeError("Locked input binding mismatch")
    record = json.loads(Path(job["record_path"]).read_bytes())
    settings = json.loads(Path(job["settings_path"]).read_bytes())
    settings["filepath"] = str(out / "raw.glb")
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    assert_operator(bpy.ops.export_scene.gltf, settings)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)
    scene = bpy.context.scene
    scene.name = "StaticTray"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1
    scene.gravity = (0,0,0)
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    mats = materials()
    for tray in record["trays"]:
        name = "/".join(tray["id"])
        root = bpy.data.objects.new(name, None)
        scene.collection.objects.link(root)
        root.location = C @ vector(tray["root_pose"]["translation_m"])
        source_rotation = Quaternion(tuple(scalar(v) for v in tray["root_pose"]["rotation_wxyz"])).to_matrix()
        root.rotation_mode = "QUATERNION"
        root.rotation_quaternion = (C @ source_rotation @ C.transposed()).to_quaternion()
        metadata(root, tray)
        if [row["key"] for row in tray["parts"]] != list(PARTS):
            raise RuntimeError("Record part order changed")
        for row in tray["parts"]:
            obj = bpy.data.objects.new("/".join(row["id"]), box(row))
            scene.collection.objects.link(obj)
            obj.parent = root
            obj.matrix_parent_inverse = Matrix.Identity(4)
            obj.location = C @ vector(row["following"]["offset"]["translation_m"])
            obj.data.materials.append(mats[row["material"]])
            metadata(obj, row, True)
    bpy.context.view_layer.update()
    for obj in scene.objects:
        obj.select_set(True)
    if len(scene.objects) != 14 or scene.rigidbody_world is not None:
        raise RuntimeError("Constructed scene violates finite static inventory")
    bpy.context.view_layer.objects.active = bpy.data.objects["equipment-tray/pair/left"]
    bpy.context.preferences.filepaths.save_version = 0
    saved = bpy.ops.wm.save_as_mainfile(filepath=str(out/"scene.blend"), check_existing=False, compress=False)
    if saved != {"FINISHED"}:
        raise RuntimeError("Native scene save failed")
    exporter = export_with_startup_receipt(settings, startup, job, out)
    shutil.copyfile(out/"raw.glb", out/"final.glb")
    write_json(out/"native-result.json", {
        "schema": "ontokin.static-tray.native/0.1.0", "passed": True,
        "blender_version": list(bpy.app.version), "build_hash": bpy.app.build_hash.decode(),
        "python_version": sys.version, "python_startup":startup, "threads": 2,
        "operator_settings": settings, "exporter_policy":exporter,
        "objects": sorted(obj.name for obj in scene.objects),
        "record_sha256": job["record_sha256"], "physics_world": False,
        "artifacts": {name:{"sha256":digest(out/name),"size_bytes":(out/name).stat().st_size}
                      for name in ["raw.glb","final.glb","scene.blend"]}})


if __name__ == "__main__":
    main()
