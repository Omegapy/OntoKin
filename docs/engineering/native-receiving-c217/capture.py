"""One explicitly approved C217 native import, save and capture.

The host driver owns start reservation, deadlines and independent continuation.
This script only observes existing imported normals. It never assigns normals,
rebuilds product meshes, executes OntoKin source or exports a new GLB.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
from pathlib import Path
import sys
import traceback

INITIAL_PYCACHE_PREFIX = sys.pycache_prefix
INITIAL_DONT_WRITE_BYTECODE = sys.dont_write_bytecode
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import (ARTIFACT_NAMES, PROFILE, TEXT_NAMES, TIMES, canonical, descriptor,
                    digest, final_lock, read_json, require, verify_run, write_json)

from origin_guard import classify_modules, snapshot_modules

import bpy
from mathutils import Matrix, Vector

C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
INV = C.transposed()


def cache_receipt(run, build, phase, stage):
    """Persist the complete raw inventory before any module classification."""
    raw = {"schema": "ontokin.c217.raw-importer-modules/0.1", "phase": phase, "stage": stage,
           "initialPycachePrefix": INITIAL_PYCACHE_PREFIX,
           "initialDontWriteBytecode": INITIAL_DONT_WRITE_BYTECODE,
           "actualPycachePrefix": sys.pycache_prefix, "dontWriteBytecode": sys.dont_write_bytecode,
           "pythonFlags": {"no_user_site": sys.flags.no_user_site,
                           "ignore_environment": sys.flags.ignore_environment,
                           "isolated": sys.flags.isolated},
           "modules": snapshot_modules(sys.modules)}
    write_json(run / (phase + "-importer-raw-" + stage + ".json"), raw, exclusive=True)
    rows = classify_modules(raw["modules"], build, (INITIAL_PYCACHE_PREFIX, sys.pycache_prefix))
    return {"phase": phase, "stage": stage, "initialPycachePrefix": INITIAL_PYCACHE_PREFIX,
            "initialDontWriteBytecode": INITIAL_DONT_WRITE_BYTECODE,
            "actualPycachePrefix": sys.pycache_prefix, "dontWriteBytecode": sys.dont_write_bytecode,
            "pythonFlags": raw["pythonFlags"], "loadedImporterModules": rows,
            "rawSnapshot": descriptor(canonical(raw) + b"\n"),
            "installedImporterBytecodeFiles": sorted(str(path) for suffix in ("*.pyc", "*.pyo") for path in Path(build["importer_root"]).rglob(suffix))}


def plain(value):
    if hasattr(value, "to_dict"):
        return {k: plain(v) for k, v in value.to_dict().items()}
    if hasattr(value, "to_list"):
        return [plain(v) for v in value.to_list()]
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    require(value is None or type(value) in (str, bool, int, float), "Unsupported native metadata type")
    return value


def product_objects(payload):
    """Bind native meshes by preserved source identity, never object iteration order."""
    expected = {row["path"]: row for row in payload["instances"]}
    result = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            require(obj.name.startswith("C217 review ") and obj.type in ("CAMERA", "LIGHT"), "Unexpected nonproduct object")
            continue
        extras = plain(obj.get("ontokin"))
        require(isinstance(extras, dict), "Native source identity extras missing")
        path = extras.get("path")
        require(path in expected and path not in result, "Unexpected or duplicate source path")
        require(extras.get("element_id") == expected[path]["element_id"], "Native element identity differs")
        require(extras.get("source_mapping", {}).get("path") == path, "Native source mapping differs")
        require(extras.get("source_mapping", {}).get("element_id") == expected[path]["element_id"], "Native source mapping element differs")
        require(not obj.modifiers and not obj.constraints and obj.rigid_body is None, "Unexpected live native behavior")
        result[path] = obj
    require(set(result) == set(expected) and len(result) == 18, "Native product inventory differs")
    return result


def build_identity():
    return {"version": list(bpy.app.version), "build_hash": bpy.app.build_hash.decode(),
            "binary_path": bpy.app.binary_path, "python": sys.version,
            "executable_sha256": digest(Path(bpy.app.binary_path).read_bytes()).split(":", 1)[1]}


def material_values(material):
    require(material is not None and material.use_nodes, "Native material missing")
    nodes = [node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"]
    require(len(nodes) == 1, "Expected one native Principled BSDF")
    node = nodes[0]
    names = ("Base Color", "Metallic", "Roughness", "Alpha")
    require(not any(node.inputs[name].is_linked for name in names), "Unexpected linked native material")
    inputs = {name: list(node.inputs[name].default_value) if name == "Base Color" else node.inputs[name].default_value for name in names}
    raw = {"name": material.name, "use_nodes": material.use_nodes, "bsdf_type": node.type,
           "bsdf_name": node.name, "inputs": inputs, "use_backface_culling": material.use_backface_culling}
    value = {"baseColorFactor": inputs["Base Color"], "metallicFactor": inputs["Metallic"],
             "roughnessFactor": inputs["Roughness"], "alpha": inputs["Alpha"],
             "double_sided": not material.use_backface_culling}
    return raw, value


def observe_objects(payload):
    products = product_objects(payload)
    instances = {row["path"]: row for row in payload["instances"]}
    observations, details = [], []
    for path, obj in sorted(products.items()):
        item, mesh = instances[path], obj.data
        require(all(len(polygon.vertices) == 3 for polygon in mesh.polygons), "Nontriangular native polygon outside C215 profile")
        mesh.calc_loop_triangles()
        triangles, material_indices = [], []
        for triangle in mesh.loop_triangles:
            loops = [int(index) for index in triangle.loops]
            triangles.append({"nativeTriangle": int(triangle.index), "loops": loops,
                "positions": [list(mesh.vertices[index].co) for index in triangle.vertices],
                "normals": [list(mesh.corner_normals[index].vector) for index in loops]})
            material_indices.append(int(triangle.material_index))
        observations.append({"nativeObject": obj.name_full, "nativeMesh": mesh.name_full,
            "sourceNode": item["node"], "sourceMesh": item["mesh"], "sourcePath": path,
            "elementId": item["element_id"], "triangles": triangles})
        materials, values = [], []
        for slot in obj.material_slots:
            raw, value = material_values(slot.material)
            materials.append(raw)
            values.append(value)
        require(len(values) == 1, "Expected one product material slot")
        details.append({"name": path, "native_name": obj.name_full, "native_mesh": mesh.name_full,
            "type": obj.type, "parent": obj.parent.name if obj.parent else None,
            "constraints": [x.type for x in obj.constraints], "modifiers": [x.type for x in obj.modifiers],
            "rigid_body": obj.rigid_body is not None, "vertex_count": len(mesh.vertices),
            "polygon_count": len(mesh.polygons), "triangle_material_indices": material_indices,
            "materials": materials, "material": values[0],
            "semantic_json": obj.get("ontokin_c217_semantic_json"),
            "element_id_json": obj.get("ontokin_c217_element_id_json"),
            "accepted_revision": obj.get("ontokin_c217_accepted_revision"),
            "native_extras": {key: plain(obj[key]) for key in obj.keys() if not key.startswith("ontokin_c217_")}})
    return observations, details


def observe_samples(payload):
    scene = bpy.context.scene
    require(scene.render.fps == 60 and scene.render.fps_base == 1, "Native playback rate changed")
    products = product_objects(payload)
    rows = []
    for time in TIMES:
        frame = time * 60
        scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        objects = {}
        for path, obj in sorted(products.items()):
            native = obj.evaluated_get(depsgraph).matrix_world.copy()
            source = INV @ native @ C
            objects[path] = {"matrix_world_blender": [list(row) for row in native],
                "matrix": [list(row) for row in source], "position_m": list(source.to_translation()),
                "orientation_wxyz": list(source.to_quaternion()), "scale": list(source.to_scale())}
        rows.append({"time_seconds": time, "frame": frame, "objects": objects})
    scene.frame_set(0)
    bpy.context.view_layer.update()
    return rows


def render_settings():
    scene = bpy.context.scene
    return {"engine": scene.render.engine, "device": scene.cycles.device, "samples": scene.cycles.samples,
        "seed": scene.cycles.seed, "use_animated_seed": scene.cycles.use_animated_seed,
        "use_adaptive_sampling": scene.cycles.use_adaptive_sampling,
        "use_denoising": scene.cycles.use_denoising,
        "view_layer_use_denoising": {layer.name: layer.cycles.use_denoising for layer in scene.view_layers},
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "resolution_percentage": scene.render.resolution_percentage, "format": scene.render.image_settings.file_format,
        "color_mode": scene.render.image_settings.color_mode,
        "view_transform": scene.view_settings.view_transform, "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure, "gamma": scene.view_settings.gamma,
        "transparent": scene.render.film_transparent}


def configure_review_scene(plan):
    scene, settings = bpy.context.scene, plan["render"]
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = settings["samples"]
    scene.cycles.seed = 216
    scene.cycles.use_animated_seed = False
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    for layer in scene.view_layers:
        layer.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = settings["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    require(background is not None, "Native world Background missing")
    background.inputs[0].default_value = (0.12, 0.12, 0.12, 1)
    background.inputs[1].default_value = 0.7
    collection = bpy.data.collections.new("C217 review environment")
    scene.collection.children.link(collection)
    for view in settings["views"]:
        data = bpy.data.cameras.new("C217 review " + view["name"])
        obj = bpy.data.objects.new(data.name, data)
        collection.objects.link(obj)
        obj.location = C.to_3x3() @ Vector(view["eye_source_m"])
        target = C.to_3x3() @ Vector(view["target_source_m"])
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
        data.type, data.ortho_scale = "ORTHO", view["ortho_scale"]
        data.clip_start, data.clip_end = 0.001, 100
    data = bpy.data.lights.new("C217 review light", "AREA")
    light = bpy.data.objects.new(data.name, data)
    collection.objects.link(light)
    data.energy, data.shape, data.size = 1400, "DISK", 6
    light.location = C.to_3x3() @ Vector((3, 5, 6))
    light.rotation_euler = (-light.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = bpy.data.objects["C217 review " + settings["views"][0]["name"]]
    scene.frame_set(0)


def verify_authority(run, payload, semantic):
    scene = bpy.context.scene
    require(scene.rigidbody_world is None, "Unexpected native physics world")
    require(scene.unit_settings.system == "METRIC" and scene.unit_settings.scale_length == 1 and scene.unit_settings.length_unit == "METERS", "Native units changed")
    for filename, text_name in TEXT_NAMES.items():
        raw = (run / "inputs" / filename).read_bytes()
        expected = base64.b64encode(raw).decode("ascii") if filename == "after.glb" else raw.decode("utf-8")
        require(text_name in bpy.data.texts and bpy.data.texts[text_name].as_string() == expected, "Retained source text bytes differ: " + filename)
    require(scene["ontokin_c217_semantic_json"] == canonical(semantic).decode(), "Scene semantic metadata changed")
    products = product_objects(payload)
    for item in semantic["objects"]:
        obj = products[item["path"]]
        require(obj["ontokin_c217_semantic_json"] == canonical(item).decode(), "Object semantic metadata changed")
        require(obj["ontokin_c217_element_id_json"] == canonical(item["element_id"]).decode(), "Mapped element identity changed")


def render_views(run, plan, phase):
    scene = bpy.context.scene
    settings = render_settings()
    require(settings["engine"] == "CYCLES" and settings["device"] == "CPU", "Renderer differs")
    require(settings["use_denoising"] is False and all(value is False for value in settings["view_layer_use_denoising"].values()), "Denoising unexpectedly enabled")
    rows = []
    for view in plan["render"]["views"]:
        filename = phase + "-" + view["name"] + ".png"
        target = run / filename
        require(not target.exists(), "Render output already exists")
        scene.camera = bpy.data.objects["C217 review " + view["name"]]
        scene.frame_set(int(view["time_seconds"] * 60))
        scene.render.filepath = str(target)
        write_json(run / (phase + "-render-intents.json"), {"attempted": len(rows) + 1, "next": filename, "completed": rows})
        require(bpy.ops.render.render(write_still=True) == {"FINISHED"}, "Native render did not finish")
        rows.append({"path": filename, "file": descriptor(target.read_bytes()), "view": view,
                     "camera": scene.camera.name, "settings": render_settings()})
        write_json(run / (phase + "-render-receipts.json"), rows)
    scene.frame_set(0)
    return rows


def main(run, phase):
    require(phase == "import", "C217 permits no reopen phase")
    plan, build = verify_run(run, HERE)
    initial = cache_receipt(run, build, phase, "before-cache-isolation")
    write_json(run / (phase + "-importer-initial.json"), initial, exclusive=True)
    require(INITIAL_PYCACHE_PREFIX is None, "Unexpected initial external Python cache prefix")
    require(not initial["installedImporterBytecodeFiles"], "Importer bytecode appeared before capture")
    private_cache = run / "isolated-importer-cache" / phase
    private_cache.mkdir(parents=True, exist_ok=False)
    sys.pycache_prefix = str(private_cache)
    require(list(bpy.app.version) == build["version"] and bpy.app.build_hash.decode() == build["build_hash"], "Runtime build label differs")
    require(Path(bpy.app.binary_path).resolve() == Path(build["executable"]["path"]).resolve(), "Runtime executable path differs")
    require(not bpy.context.preferences.filepaths.use_scripts_auto_execute, "Automatic script execution enabled")
    payload = read_json(run / "inputs/source-payload.json")
    semantic = read_json(run / "inputs/after.semantic.json")
    scene_path = run / "received.blend"
    require(not scene_path.exists(), "Native scene already exists")
    scene = bpy.context.scene
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene.unit_settings.system, scene.unit_settings.scale_length, scene.unit_settings.length_unit = "METRIC", 1, "METERS"
    scene.render.fps, scene.render.fps_base = 60, 1
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    importer_module = sys.modules.get("io_scene_gltf2")
    require(importer_module is not None and Path(importer_module.__file__).resolve() == Path(build["importer_root"]) / "__init__.py", "Loaded importer differs from pinned installation")
    write_json(run / "import-importer-before-call.json", cache_receipt(run, build, phase, "addon-enabled-before-import"), exclusive=True)
    props = {p.identifier for p in bpy.ops.import_scene.gltf.get_rna_type().properties if p.identifier != "rna_type"}
    require(props == set(build["importer_properties"]), "Importer operator property inventory differs")
    settings = read_json(run / "import-settings.json")
    write_json(run / "import-settings-at-call.json", settings, exclusive=True)
    require(bpy.ops.import_scene.gltf(**settings) == {"FINISHED"}, "Native GLB import did not finish")
    write_json(run / "import-importer-after-call.json", cache_receipt(run, build, phase, "after-import"), exclusive=True)
    products = product_objects(payload)
    extras = {path: {key: plain(obj[key]) for key in obj.keys()} for path, obj in products.items()}
    scene_extras = {key: plain(scene[key]) for key in scene.keys()}
    write_json(run / "native-extras-before-mapping.json", extras, exclusive=True)
    for item in semantic["objects"]:
        obj = products[item["path"]]
        obj["ontokin_c217_semantic_json"] = canonical(item).decode()
        obj["ontokin_c217_element_id_json"] = canonical(item["element_id"]).decode()
        obj["ontokin_c217_accepted_revision"] = plan["acceptedRevision"]
    for filename, text_name in TEXT_NAMES.items():
        require(text_name not in bpy.data.texts, "Authority text already exists")
        raw = (run / "inputs" / filename).read_bytes()
        bpy.data.texts.new(text_name).write(base64.b64encode(raw).decode() if filename == "after.glb" else raw.decode())
    scene["ontokin_c217_semantic_json"] = canonical(semantic).decode()
    scene["ontokin_c217_native_extras_json"] = canonical(extras).decode()
    scene["ontokin_c217_native_scene_extras_json"] = canonical(scene_extras).decode()
    scene["ontokin_c217_import_settings_json"] = canonical(settings).decode()
    scene["ontokin_c217_importer_module"] = str(Path(importer_module.__file__).resolve())
    scene["ontokin_c217_prelaunch_plan_sha256"] = digest(canonical(plan))
    configure_review_scene(plan)
    verify_authority(run, payload, semantic)
    require(bpy.ops.wm.save_as_mainfile(filepath=str(scene_path), check_existing=False, compress=False) == {"FINISHED"}, "Native save failed")
    lock = final_lock(run, plan)
    write_json(run / "input-lock.json", lock, exclusive=True)
    scene = bpy.context.scene
    require(scene["ontokin_c217_prelaunch_plan_sha256"] == digest(canonical(plan)), "Native plan identity changed")
    objects, object_details = observe_objects(payload)
    observations = {"schema_version": "ontokin.blender-corner-observations/0.1", "profile": PROFILE,
        "kind": "native-unverified", "inputLockSha256": digest(canonical(lock)),
        "sourcePayloadSha256": plan["sourcePayloadSha256"], "frame": "blender-object-local-right-handed-z-up",
        "phase": phase, "producer": "C217 actual bpy mesh corner capture at " + plan["sourceRevision"], "objects": objects}
    write_json(run / (phase + "-observations.json"), observations, exclusive=True)
    details = {"schema": "ontokin.c217.native-details/0.1", "phase": phase, "build": build_identity(),
        "input_sha256": {name: value["sha256"] for name, value in plan["files"].items()},
        "units": {"system": scene.unit_settings.system, "scale_length": scene.unit_settings.scale_length, "length_unit": scene.unit_settings.length_unit},
        "physics_world": scene.rigidbody_world is not None,
        "native_extras_before_mapping": json.loads(scene["ontokin_c217_native_extras_json"]),
        "native_scene_extras_before_mapping": json.loads(scene["ontokin_c217_native_scene_extras_json"]),
        "import_settings": json.loads(scene["ontokin_c217_import_settings_json"]),
        "semantic_text": bpy.data.texts[TEXT_NAMES["after.semantic.json"]].as_string(),
        "scene_mapping_json": scene["ontokin_c217_semantic_json"], "objects": object_details,
        "samples": observe_samples(payload), "render_settings": render_settings(),
        "authority_texts": {name: descriptor(bpy.data.texts[text].as_string().encode()) for name, text in TEXT_NAMES.items()},
        "scene_file": lock["artifacts"]["scene"], "prelaunch_plan_sha256": digest(canonical(plan)),
        "importer_module_at_import": scene["ontokin_c217_importer_module"],
        "retained_authority_verified": True, "auto_execute_scripts": bpy.context.preferences.filepaths.use_scripts_auto_execute}
    write_json(run / (phase + "-details.json"), details, exclusive=True)
    renders = render_views(run, plan, phase)
    require(final_lock(run, plan) == lock, "Saved scene bytes changed during observation/render")
    write_json(run / (phase + "-importer-final.json"), cache_receipt(run, build, phase, "after-capture-and-render"), exclusive=True)
    require(not any(private_cache.rglob("*")), "Private importer cache unexpectedly gained files")
    verify_run(run, HERE)
    write_json(run / (phase + "-native-complete.json"), {"schema": "ontokin.c217.native-complete/0.1", "phase": phase,
        "planSha256": digest(canonical(plan)), "inputLockSha256": digest(canonical(lock)), "scene": lock["artifacts"]["scene"],
        "observations": descriptor((run / (phase + "-observations.json")).read_bytes()),
        "details": descriptor((run / (phase + "-details.json")).read_bytes()), "renders": renders,
        "claims": "Native capture completed; independent comparison, visual review and receiving decision remain separate"}, exclusive=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--phase", choices=("import",), required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run = args.run.resolve()
    try:
        main(run, args.phase)
    except BaseException as exc:
        write_json(run / (args.phase + "-native-failure.json"), {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
        raise
