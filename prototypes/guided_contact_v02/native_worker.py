"""Pinned Blender worker. Source data supplies design; backend.json supplies mapping.

This file runs only in the supervised Blender subprocess. It never reads the
historical native scene, a stopping schedule, or any expected result.
"""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector


PARTS = ("base", "left_carriage", "left_shoe", "left_stop",
         "right_carriage", "right_shoe", "right_stop")
SCENE_TAGS = ("source_sha256", "canonical_input_sha256", "source_binding", "profile_binding",
              "backend_binding", "output_binding", "module_key", "scene_key")
OBJECT_TAGS = ("part_id", "body_id", "collider_id", "helper_role", "source_occurrence")


def native_point(point_mm):
    return (point_mm[0] / 1000, -point_mm[2] / 1000, point_mm[1] / 1000)


def gltf_point(point_m):
    return [1000 * point_m[0], 1000 * point_m[2], -1000 * point_m[1]]


def select(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def mesh_box(name, box_mm):
    x, y, z = [value / 2 for value in box_mm]
    corners = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
               (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata([native_point(corner) for corner in corners], [], faces)
    mesh.update()
    return mesh


def tag_object(obj, mapping, source):
    part = mapping.get("source_part") or ""
    body = mapping.get("source_body") or ""
    collider = mapping.get("source_collider") or ""
    obj["part_id"] = part
    obj["body_id"] = body
    obj["collider_id"] = collider
    obj["helper_role"] = mapping["kind"]
    obj["source_occurrence"] = "/".join([source["module_key"], source["scene_key"], part or body])


def add_body(obj, body_type, shape, backend):
    select(obj)
    bpy.ops.rigidbody.object_add()
    body = obj.rigid_body
    body.type = body_type
    body.collision_shape = shape
    for name, value in backend["rigid_body_defaults"].items():
        setattr(body, name, value)
    return body


def add_constraint(scene, lane, kind, source, backend, mappings):
    name = "_" + lane + "_" + kind.lower()
    carriage = scene.objects[lane + "_carriage"]
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.location = carriage.location
    obj.hide_render = True
    tag_object(obj, mappings[name], source)
    select(obj)
    bpy.ops.rigidbody.constraint_add()
    joint = obj.rigid_body_constraint
    joint.type = kind
    joint.object1 = scene.objects["base"]
    joint.object2 = carriage
    rule = backend["guide" if kind == "GENERIC" else "motor"]
    for key in ("disable_collisions", "use_override_solver_iterations", "solver_iterations"):
        setattr(joint, key, rule[key])
    joint.use_motor_ang = False
    if kind == "GENERIC":
        joint.use_limit_lin_x = False
        for axis in ("y", "z"):
            setattr(joint, "use_limit_lin_" + axis, True)
            setattr(joint, "limit_lin_" + axis + "_lower", 0.0)
            setattr(joint, "limit_lin_" + axis + "_upper", 0.0)
        for axis in ("x", "y", "z"):
            setattr(joint, "use_limit_ang_" + axis, True)
            setattr(joint, "limit_ang_" + axis + "_lower", 0.0)
            setattr(joint, "limit_ang_" + axis + "_upper", 0.0)
        for key, value in backend["inactive_constraint_defaults"]["generic"].items():
            setattr(joint, key, value)
    else:
        inactive = backend["inactive_constraint_defaults"]["motor"]
        for axis in "xyz":
            for mode, full in (("lin", "linear"), ("ang", "angular")):
                setattr(joint, "use_limit_" + mode + "_" + axis, False)
                for edge in ("lower", "upper"):
                    setattr(joint, f"limit_{mode}_{axis}_{edge}", inactive[f"all_{full}_{edge}"])
        joint.use_motor_lin = rule["use_motor_lin"]
        joint.motor_lin_target_velocity = -source["bodies"]["body." + lane]["feed_mm_s"] / 1000
        joint.motor_lin_max_impulse = rule["motor_lin_max_impulse"]
        drive = joint.driver_add("motor_lin_target_velocity").driver
        drive.type = "SCRIPTED"
        variable = drive.variables.new()
        variable.name = rule["driver_variable_name"]
        variable.type = rule["driver_variable_type"]
        variable.targets[0].id = carriage
        variable.targets[0].data_path = rule["driver_variable_data_path"]
        drive.expression = rule["driver_expression"]
    return obj


def construct(source, manifest, backend):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    settings = backend["world"]
    for name in ("frame_start", "frame_end"):
        setattr(scene, name, settings[name])
    scene.render.fps = settings["fps"]
    scene.render.fps_base = settings["fps_base"]
    scene.gravity = source["gravity_m_s2"]
    mappings = {row["name"]: row for row in backend["native_objects"]}
    origins = {key: part["at_mm"] for key, part in source["parts"].items() if "at_mm" in part}
    for follow in source["follows"].values():
        origins[follow["child"]] = [a + b for a, b in zip(origins[follow["parent"]], follow["offset_mm"])]
    for name in backend["construction_order"]["visible_parts"]:
        part = source["parts"][name]
        obj = bpy.data.objects.new(name, mesh_box(name, part["box_mm"]))
        scene.collection.objects.link(obj)
        center = [value + size / 2 for value, size in zip(origins[name], part["box_mm"])]
        obj.location = native_point(center)
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = part["rotation_wxyz"]
        tag_object(obj, mappings[name], source)
        material = bpy.data.materials.new(name + "_material")
        material.diffuse_color = part["color_linear_rgba"]
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = part["color_linear_rgba"]
        shader.inputs["Metallic"].default_value = backend["glb_material"]["metallicFactor"]
        shader.inputs["Roughness"].default_value = backend["glb_material"]["roughnessFactor"]
        obj.data.materials.append(material)
    for follow in source["follows"].values():
        child, parent = scene.objects[follow["child"]], scene.objects[follow["parent"]]
        child.parent = parent
        child.matrix_parent_inverse = Matrix.Identity(4)
        child.location = native_point([follow["offset_mm"][i] + source["parts"][child.name]["box_mm"][i] / 2
                                       - source["parts"][parent.name]["box_mm"][i] / 2 for i in range(3)])
    for body in source["bodies"].values():
        obj = scene.objects[body["part"]]
        obj["speed_mm_s"] = float(body["feed_mm_s"])
        obj["motion_authority"] = body["authority"]
    stop = scene.objects["left_stop"]
    stop["near_face_mm"] = float(source["parts"]["left_stop"]["at_mm"][0])
    stop["half_width_mm"] = source["parts"]["left_stop"]["box_mm"][0] / 2
    drive = stop.driver_add("location", 0).driver
    drive.type = "SCRIPTED"
    for name in backend["stop_driver"]["variables"]:
        variable = drive.variables.new()
        variable.name = name
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = stop
        variable.targets[0].data_path = '["' + name + '"]'
    drive.expression = backend["stop_driver"]["expression"]
    stop.update_tag()
    scene.frame_set(0)
    bpy.context.view_layer.update()
    for name in backend["construction_order"]["fixed_bodies"]:
        add_body(scene.objects[name], "PASSIVE", "BOX", backend)
    for lane in backend["construction_order"]["moving_lanes"]:
        carriage, shoe = scene.objects[lane + "_carriage"], scene.objects[lane + "_shoe"]
        body = add_body(carriage, "ACTIVE", "COMPOUND", backend)
        body.mass = source["bodies"]["body." + lane]["mass_kg"]
        add_body(shoe, "ACTIVE", "BOX", backend)
        proxy_name = "_" + lane + "_carriage_collision"
        proxy = bpy.data.objects.new(proxy_name, carriage.data.copy())
        scene.collection.objects.link(proxy)
        proxy.parent = carriage
        proxy.matrix_parent_inverse = Matrix.Identity(4)
        proxy.location = (0, 0, 0)
        proxy.hide_render = True
        proxy.display_type = "WIRE"
        tag_object(proxy, mappings[proxy_name], source)
        add_body(proxy, "ACTIVE", "BOX", backend)
        add_constraint(scene, lane, "GENERIC", source, backend, mappings)
        add_constraint(scene, lane, "MOTOR", source, backend, mappings)
    if not source["colliders"]["contact.left_shoe"]["enabled"]:
        select(scene.objects["left_shoe"])
        bpy.ops.rigidbody.object_remove()
    world = scene.rigidbody_world
    for name in ("time_scale", "substeps_per_frame", "solver_iterations", "use_split_impulse"):
        setattr(world, name, settings[name])
    world.point_cache.frame_start = settings["cache_frame_start"]
    world.point_cache.frame_end = settings["cache_frame_end"]
    # Do not assign use_disk_cache: the archived C190 build records a crash for
    # that redundant assignment in this pinned Blender. Its default is checked.
    tags = {"source_sha256": manifest["source_sha256"],
            "canonical_input_sha256": manifest["canonical_input_sha256"],
            "source_binding": source["source_binding"], "profile_binding": source["profile"],
            "backend_binding": source["backend"], "output_binding": source["output"],
            "module_key": source["module_key"], "scene_key": source["scene_key"]}
    for name, value in tags.items():
        scene[name] = value
    scene.frame_set(0)
    bpy.context.view_layer.update()
    return scene


def configuration(scene):
    objects = {}
    for obj in sorted(scene.objects, key=lambda item: item.name):
        rb = None
        if obj.rigid_body:
            names = ("type", "collision_shape", "mass", "kinematic", "enabled", "friction", "restitution",
                     "linear_damping", "angular_damping", "use_margin", "collision_margin", "use_deactivation")
            rb = {name: getattr(obj.rigid_body, name) for name in names}
            rb["collision_collections"] = list(obj.rigid_body.collision_collections)
        joint = None
        if obj.rigid_body_constraint:
            native = obj.rigid_body_constraint
            names = ["type", "disable_collisions", "use_override_solver_iterations", "solver_iterations",
                     "use_motor_lin", "use_motor_ang", "motor_lin_target_velocity", "motor_lin_max_impulse"]
            for axis in "xyz":
                for mode in ("lin", "ang"):
                    names += [f"use_limit_{mode}_{axis}", f"limit_{mode}_{axis}_lower", f"limit_{mode}_{axis}_upper"]
            joint = {name: getattr(native, name) for name in names}
            joint.update(object1=native.object1.name, object2=native.object2.name)
        drivers = []
        if obj.animation_data:
            for fcurve in obj.animation_data.drivers:
                driver = fcurve.driver
                drivers.append({"data_path": fcurve.data_path, "array_index": fcurve.array_index,
                                "type": driver.type, "expression": driver.expression,
                                "variables": [{"name": variable.name, "type": variable.type,
                                               "target_id": variable.targets[0].id.name,
                                               "data_path": variable.targets[0].data_path}
                                              for variable in driver.variables]})
        vertices = [list(vertex.co) for vertex in obj.data.vertices] if obj.type == "MESH" else None
        bounds = [[min(v[a] for v in vertices) for a in range(3)],
                  [max(v[a] for v in vertices) for a in range(3)]] if vertices else None
        props = {name: obj[name] for name in OBJECT_TAGS}
        for name in ("motion_authority", "speed_mm_s", "near_face_mm", "half_width_mm"):
            if name in obj:
                props[name] = obj[name]
        objects[obj.name] = {"type": obj.type, "parent": obj.parent.name if obj.parent else None,
                             "hide_render": obj.hide_render, "location": list(obj.location),
                             "rotation_quaternion_wxyz": list(obj.rotation_quaternion), "scale": list(obj.scale),
                             "matrix_parent_inverse": [list(row) for row in obj.matrix_parent_inverse],
                             "matrix_world": [list(row) for row in obj.matrix_world], "properties": props,
                             "mesh_vertices": vertices, "mesh_local_bounds": bounds, "rigid_body": rb,
                             "constraint": joint, "drivers": drivers,
                             "has_action": bool(obj.animation_data and obj.animation_data.action)}
    world = scene.rigidbody_world
    return {"scene_tags": {name: scene[name] for name in SCENE_TAGS}, "objects": objects,
            "world": {"frame_start": scene.frame_start, "frame_end": scene.frame_end,
                      "fps": scene.render.fps, "fps_base": scene.render.fps_base, "gravity": list(scene.gravity),
                      "time_scale": world.time_scale, "substeps_per_frame": world.substeps_per_frame,
                      "solver_iterations": world.solver_iterations, "use_split_impulse": world.use_split_impulse,
                      "cache_frame_start": world.point_cache.frame_start, "cache_frame_end": world.point_cache.frame_end,
                      "cache_is_baked": world.point_cache.is_baked,
                      "body_collection": sorted(obj.name for obj in world.collection.objects),
                      "constraint_collection": sorted(obj.name for obj in world.constraints.objects)}}


def capture(scene, backend):
    samples = []
    scheduled_substeps = 0
    start, end = backend["capture"]["sequential_frames"]
    fps = backend["world"]["fps"] / backend["world"]["fps_base"]
    for frame in range(start, end + 1):
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        matrices, bounds = {}, {}
        for name in PARTS:
            obj = scene.objects[name]
            matrix = obj.evaluated_get(graph).matrix_world.copy()
            matrices[name] = [list(row) for row in matrix]
            vertices = [gltf_point(matrix @ Vector(corner)) for corner in obj.bound_box]
            bounds[name] = [[min(v[a] for v in vertices) for a in range(3)],
                            [max(v[a] for v in vertices) for a in range(3)]]
        samples.append({"frame": frame, "time_s": frame / fps,
                        "matrices_blender_m": matrices, "bounds_gltf_mm": bounds})
        if frame > start:
            scheduled_substeps += backend["world"]["substeps_per_frame"]
        if len(samples) > backend["limits"]["native_samples"] or scheduled_substeps > backend["limits"]["scheduled_native_substeps"]:
            raise RuntimeError("Native capture ceiling exceeded")
    return samples, scheduled_substeps


def main():
    input_name, manifest_name, backend_name, output_name, *extra = sys.argv[sys.argv.index("--") + 1:]
    source = json.loads(Path(input_name).read_text())
    manifest = json.loads(Path(manifest_name).read_text())
    backend = json.loads(Path(backend_name).read_text())
    output = Path(output_name)
    if list(bpy.app.version) != backend["runtime"]["blender_version"] or bpy.app.build_hash.decode() != backend["runtime"]["build_hash"]:
        raise RuntimeError("Pinned Blender identity mismatch")
    if extra:
        if len(extra) != 2 or extra[0] != "--reopen":
            raise ValueError("Unsupported worker arguments")
        bpy.ops.wm.open_mainfile(filepath=extra[1])
        scene = bpy.context.scene
        scene.frame_set(0)
        # Fresh process plus explicit native cache clearing, without reconstruction.
        bpy.ops.ptcache.free_bake_all()
        scene.frame_set(0)
        bpy.context.view_layer.update()
    else:
        scene = construct(source, manifest, backend)
    if len(scene.objects) > backend["limits"]["native_objects"]:
        raise RuntimeError("Native object ceiling exceeded")
    config = configuration(scene)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "scene.blend"))
    samples, scheduled_substeps = capture(scene, backend)
    result = {"schema": "ontokin.c193.native-result/0.1", "source_sha256": manifest["source_sha256"],
              "canonical_input_sha256": manifest["canonical_input_sha256"],
              "blender_version": list(bpy.app.version), "blender_build_hash": bpy.app.build_hash.decode(),
              "nominal_scheduled_substeps": scheduled_substeps, "configuration": config, "samples": samples}
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if len(encoded) > backend["limits"]["native_result_bytes"]:
        raise RuntimeError("Native result byte ceiling exceeded")
    (output / "native-result.json").write_bytes(encoded)
    print("C193 native capture complete:", len(samples), "samples;", scheduled_substeps, "scheduled substeps")


if __name__ == "__main__":
    main()
