"""Read a saved native scene, then independently import its delivered GLB.

The receiver reports actual native vertices, triangles, transforms and materials.
Host-side independent-reader data decides whether these observations pass.
No geometry is rebuilt, exported or simulated by this process.
"""
import sys

sys.dont_write_bytecode = True

import hashlib
import json
from pathlib import Path
import bpy
from mathutils import Matrix, Vector


C = Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))


def python_startup():
    flags = {name:getattr(sys.flags,name) for name in
             ("isolated","ignore_environment","no_user_site","no_site","safe_path","hash_randomization","dont_write_bytecode")}
    required = {"isolated":0,"ignore_environment":0,"no_user_site":1,"safe_path":True,
                "hash_randomization":0,"dont_write_bytecode":1}
    if any(flags[key] != value for key,value in required.items()) or not sys.dont_write_bytecode:
        raise RuntimeError("Actual receiving Python startup differs from the frozen environment")
    return {"flags":flags,"dont_write_bytecode":sys.dont_write_bytecode,"sys_path":list(sys.path),
            "executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,
            "python_version":sys.version}


def plain(value):
    if hasattr(value, "to_list"):
        return [plain(x) for x in value.to_list()]
    if hasattr(value, "to_dict"):
        return {k:plain(v) for k,v in value.to_dict().items()}
    if isinstance(value, (list,tuple)):
        return [plain(x) for x in value]
    return value


def mat_values(material):
    node = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None
    if node is None:
        raise RuntimeError("Receiving material has no measurable Principled values")
    return {"name":material.name,"baseColorFactor":list(node.inputs["Base Color"].default_value),
            "metallicFactor":node.inputs["Metallic"].default_value,
            "roughnessFactor":node.inputs["Roughness"].default_value,
            "alphaMode":"OPAQUE" if node.inputs["Alpha"].default_value == 1 else "NONOPAQUE",
            "doubleSided":not material.use_backface_culling}


def measure_scene():
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    nodes = {}
    if scene.rigidbody_world is not None:
        raise RuntimeError("Receiving scene unexpectedly contains a physics world")
    for obj in sorted(scene.objects, key=lambda obj:obj.name):
        if obj.type not in {"EMPTY","MESH"} or obj.constraints or obj.modifiers or obj.animation_data:
            raise RuntimeError("Receiving scene contains unsupported behavior")
        matrix = C.transposed() @ obj.matrix_world @ C
        row = {"name":obj.name,"parent":obj.parent.name if obj.parent else None,
               "children":sorted(child.name for child in obj.children),
               "extras":{key:plain(obj[key]) for key in obj.keys()},
               "world_matrix":[list(v) for v in matrix]}
        if obj.type == "MESH":
            if len(obj.data.materials) != 1:
                raise RuntimeError("Receiving mesh material inventory differs")
            obj.data.calc_loop_triangles()
            row["world_vertices"] = [list((C.transposed() @ obj.matrix_world) @ vertex.co) for vertex in obj.data.vertices]
            row["triangles"] = [list(face.vertices) for face in obj.data.loop_triangles]
            row["material"] = mat_values(obj.data.materials[0])
        nodes[obj.name] = row
    return {"nodes":nodes,"object_count":len(nodes),"scene":scene.name,
            "physics_world":False,"measurement_frame":"source-rh-y-up-metres"}


def scalar_settings(owner):
    """Record effective scalar/vector RNA values, including pinned defaults."""
    values = {}
    for prop in sorted(owner.bl_rna.properties, key=lambda item:item.identifier):
        if prop.type not in {"BOOLEAN","INT","FLOAT","STRING","ENUM"}:
            continue
        value = getattr(owner, prop.identifier)
        if isinstance(value, set):
            value = sorted(value)
        elif getattr(prop, "is_array", False):
            value = list(value)
        values[prop.identifier] = value
    return values


def render_review(bounds, output):
    # Bounds come from the independent reader's frozen mathematical fixture.
    # They are not inferred from potentially missing receiving geometry.
    minimum, maximum = [Vector(point) for point in bounds]
    source_center = (minimum+maximum)/2
    center = C.to_3x3() @ source_center
    direction = C.to_3x3() @ Vector((1.5,1.2,1.5)).normalized()
    span = max(maximum[i]-minimum[i] for i in range(3))
    camera_data = bpy.data.cameras.new("review-camera")
    camera = bpy.data.objects.new("review-camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = center + direction * max(2.0, span*3)
    camera.rotation_euler = (center-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type = "ORTHO"
    # This conservative scale frames every frozen expected corner in either axis.
    camera.data.ortho_scale = max(0.1,(maximum-minimum).length*1.35)
    camera.data.clip_start = 0.001
    camera.data.clip_end = 200
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1
    scene.render.pixel_aspect_y = 1
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    scene.render.filepath = str(output)
    scene.render.film_transparent = False
    scene.render.dither_intensity = 0
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.view_settings.use_curve_mapping = False
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "paint.sl"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = False
    scene.display.shading.show_cavity = False
    scene.display.shading.show_object_outline = False
    scene.display.shading.show_specular_highlight = False
    scene.display.shading.background_type = "WORLD"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("ReviewWorld")
    scene.world.color = (0.08,0.08,0.08)
    effective = {
        "camera":scalar_settings(camera.data),
        "render":scalar_settings(scene.render),
        "image":scalar_settings(scene.render.image_settings),
        "display":scalar_settings(scene.display),
        "shading":scalar_settings(scene.display.shading),
        "display_colorspace":scalar_settings(scene.display_settings),
        "view_colorspace":scalar_settings(scene.view_settings),
        "world_color":list(scene.world.color),
    }
    status = bpy.ops.render.render(write_still=True)
    if status != {"FINISHED"}:
        raise RuntimeError("Static receiving render failed")
    return {"resolution":[1024,768],"engine":"BLENDER_WORKBENCH","projection":"ORTHO",
            "source_direction":[1.5,1.2,1.5],"expected_source_bounds":bounds,
            "native_location":list(camera.location),"native_rotation_euler":list(camera.rotation_euler),
            "ortho_scale":camera.data.ortho_scale,"effective_settings":effective,
            "sha256":hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    args = sys.argv[sys.argv.index("--")+1:]
    if len(args) != 2 or args[0] != "--job":
        raise ValueError("Expected one frozen receiver job")
    job = json.loads(Path(args[1]).read_bytes())
    stage = Path.cwd().resolve()
    if stage != Path(job["output_directory"]).resolve():
        raise RuntimeError("Receiver directory binding mismatch")
    if tuple(bpy.app.version) != (4,5,3) or bpy.app.build_hash.decode() != "67807e1800cc":
        raise RuntimeError("Receiving Blender version/build mismatch")
    startup = python_startup()
    candidate = Path(job["candidate"])
    for name,digest in job["input_sha256"].items():
        if hashlib.sha256((candidate/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Receiving input bytes changed: "+name)
    if hashlib.sha256(Path(job["settings_path"]).read_bytes()).hexdigest() != job["settings_sha256"]:
        raise RuntimeError("Receiving operator settings changed")
    settings = json.loads(Path(job["settings_path"]).read_bytes())
    settings["filepath"] = str(candidate/"final.glb")
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    runtime = {p.identifier for p in bpy.ops.import_scene.gltf.get_rna_type().properties if p.identifier != "rna_type"}
    if runtime != set(settings):
        raise RuntimeError("Frozen importer property coverage mismatch: missing="+
                           str(sorted(runtime-set(settings)))+" extra="+str(sorted(set(settings)-runtime)))
    if bpy.ops.wm.open_mainfile(filepath=str(candidate/"scene.blend"),load_ui=False,use_scripts=False) != {"FINISHED"}:
        raise RuntimeError("Native scene reopening failed")
    native = measure_scene()
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)
    if bpy.ops.import_scene.gltf(**settings) != {"FINISHED"}:
        raise RuntimeError("Receiving GLB import failed")
    imported = measure_scene()
    render = render_review(job["expected_world_bounds"],stage/"review.png")
    report = {"schema":"ontokin.static-tray.receiving-observations/0.1.0",
              "blender_version":list(bpy.app.version),"build_hash":bpy.app.build_hash.decode(),
              "python_startup":startup,
              "native_scene":native,"imported_glb":imported,"render":render,
              "operator_settings":settings,"input_sha256":job["input_sha256"],
              "note":"Measurements only; host independent comparison is the acceptance gate"}
    (stage/"observations.json").write_text(json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False))


if __name__ == "__main__":
    main()
