"""Reopen, independently inspect, clear caches and replay a delivered C191 scene.

Run only through pinned Blender. This module imports no adapter implementation,
creates no objects, and never repairs a scene or changes its design properties.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PARTS = ("base", "left_carriage", "left_shoe", "left_stop", "right_carriage", "right_shoe", "right_stop")
STOPS = {"A": 380., "B": 355., "C": 367.5, "D": 380.}


def plain(value):
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return [plain(v) for v in value]


def drivers(obj):
    if obj.animation_data is None:
        return []
    return [{"data_path": f.data_path, "array_index": f.array_index,
        "expression": f.driver.expression, "type": f.driver.type,
        "variables": [{"name": variable.name, "type": variable.type,
            "targets": [{"id": target.id.name if target.id else None, "data_path": target.data_path}
                        for target in variable.targets]} for variable in f.driver.variables]}
        for f in obj.animation_data.drivers]


def config(scene, backend):
    body_fields = tuple(backend["rigid_body_defaults"]) + ("type", "collision_shape")
    objects = {}
    for obj in sorted(scene.objects, key=lambda item: item.name):
        row = {"type": obj.type, "parent": obj.parent.name if obj.parent else None,
            "hide_render": obj.hide_render, "location": list(obj.location),
            "matrix_world": [list(r) for r in obj.matrix_world],
            "matrix_parent_inverse": [list(r) for r in obj.matrix_parent_inverse],
            "rotation_quaternion_wxyz": list(obj.rotation_quaternion), "scale": list(obj.scale),
            "properties": {k: plain(v) for k, v in obj.items() if isinstance(v, (bool, int, float, str))},
            "drivers": drivers(obj), "action": obj.animation_data.action.name
                if obj.animation_data and obj.animation_data.action else None,
            "rigid_body": {key: plain(getattr(obj.rigid_body, key)) for key in body_fields}
                if obj.rigid_body else None}
        if obj.type == "MESH":
            row["vertices"] = [list(vertex.co) for vertex in obj.data.vertices]
            row["local_bounds"] = [[min(vertex.co[a] for vertex in obj.data.vertices) for a in range(3)],
                                   [max(vertex.co[a] for vertex in obj.data.vertices) for a in range(3)]]
        if obj.rigid_body_constraint:
            joint = obj.rigid_body_constraint
            fields = ["type", "disable_collisions", "use_override_solver_iterations", "solver_iterations",
                "use_motor_lin", "use_motor_ang", "motor_lin_target_velocity", "motor_lin_max_impulse"]
            for axis in "xyz":
                fields.extend(["use_limit_lin_" + axis, "limit_lin_" + axis + "_lower", "limit_lin_" + axis + "_upper",
                    "use_limit_ang_" + axis, "limit_ang_" + axis + "_lower", "limit_ang_" + axis + "_upper"])
            row["constraint"] = {key: getattr(joint, key) for key in fields}
            row["constraint"].update(object1=joint.object1.name if joint.object1 else None,
                                     object2=joint.object2.name if joint.object2 else None)
        objects[obj.name] = row
    world = scene.rigidbody_world
    return {"scene_tags": {key: plain(scene.get(key)) for key in backend["native_tags"]["scene"]},
        "objects": objects, "world": {"frame_start": scene.frame_start, "frame_end": scene.frame_end,
            "fps": scene.render.fps, "fps_base": scene.render.fps_base, "gravity": list(scene.gravity),
            "time_scale": world.time_scale, "substeps_per_frame": world.substeps_per_frame,
            "solver_iterations": world.solver_iterations, "use_split_impulse": world.use_split_impulse,
            "cache_frame_start": world.point_cache.frame_start, "cache_frame_end": world.point_cache.frame_end,
            "cache_is_baked": world.point_cache.is_baked,
            "body_collection": sorted(obj.name for obj in world.collection.objects),
            "constraint_collection": sorted(obj.name for obj in world.constraints.objects)}}


def verify_configuration(configuration, backend, source_path, canonical_path, case):
    assert bpy.app.version == (4, 5, 3) and bpy.app.build_hash.decode() == "67807e1800cc"
    expected_tags = {"source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "canonical_input_sha256": hashlib.sha256(canonical_path.read_bytes()).hexdigest(),
        "source_binding": "c191-experimental-0.1", "profile_binding": "guided-box-contact-0.1",
        "backend_binding": "blender-bullet-c190-0.1", "output_binding": "glb-guided-contact-0.1",
        "module_key": "gauge", "scene_key": "slide"}
    assert configuration["scene_tags"] == expected_tags, "Stored source/profile identity mismatch"
    world = configuration["world"]
    for key, value in backend["world"].items():
        if key in world:
            assert world[key] == value, "Stored world setting mismatch: " + key
    objects = configuration["objects"]
    assert set(objects) == {row["name"] for row in backend["native_objects"]}
    assert len(objects) == 13
    assert sum(row["type"] == "MESH" and not row["hide_render"] for row in objects.values()) == 7
    assert len(world["body_collection"]) == (8 if case == "D" else 9)
    roots = [name for name, row in objects.items() if row["rigid_body"] and
             row["rigid_body"]["type"] == "ACTIVE" and row["parent"] is None]
    assert set(roots) == {"left_carriage", "right_carriage"}
    assert sum(objects[name]["rigid_body"]["mass"] for name in roots) == 2
    for mapping in backend["native_objects"]:
        name = mapping["name"]
        row = objects[name]
        assert row["action"] is None, "Stored transform action on " + name
        props = row["properties"]
        assert props["part_id"] == (mapping.get("source_part") or "")
        assert props["body_id"] == (mapping.get("source_body") or "")
        assert props["collider_id"] == (mapping.get("source_collider") or "")
        occurrence = props["source_occurrence"]
        assert "gauge" in occurrence and "slide" in occurrence
        source_keys = [mapping.get(key) for key in ("source_collider", "source_part", "source_body") if mapping.get(key)]
        assert any(key in occurrence for key in source_keys), "Unbound source occurrence on " + name
        assert row["parent"] == mapping.get("parent")
        if mapping["kind"] == "constraint":
            assert row["type"] == "EMPTY" and row["rigid_body"] is None and row["hide_render"]
            continue
        assert row["type"] == "MESH" and len(row["vertices"]) == 8
        assert row["hide_render"] == bool(mapping.get("hide_render", False))
        if name == "left_shoe" and case == "D":
            assert row["rigid_body"] is None
        else:
            body = row["rigid_body"]
            assert body is not None
            for key, value in backend["rigid_body_defaults"].items():
                assert body[key] == value, name + ": " + key
            expected_type = "ACTIVE" if "ACTIVE" in mapping["native_type"] else "PASSIVE"
            expected_shape = "COMPOUND" if name in roots else "BOX"
            assert body["type"] == expected_type and body["collision_shape"] == expected_shape
    for lane, speed in (("left", 125), ("right", 150)):
        car, shoe, proxy = (objects[lane + "_carriage"], objects[lane + "_shoe"], objects["_" + lane + "_carriage_collision"])
        assert not car["drivers"] and not shoe["drivers"] and not proxy["drivers"]
        assert car["properties"]["motion_authority"] == "solver"
        assert car["properties"]["speed_mm_s"] == speed
        assert proxy["vertices"] == car["vertices"]
        assert proxy["location"] == [0, 0, 0] and proxy["scale"] == [1, 1, 1]
        assert proxy["matrix_parent_inverse"] == [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        for kind in ("generic", "motor"):
            row = objects["_" + lane + "_" + kind]
            joint = row["constraint"]
            assert joint["object1"] == "base" and joint["object2"] == lane + "_carriage"
            assert joint["disable_collisions"] and joint["use_override_solver_iterations"]
            assert joint["solver_iterations"] == 100
            if kind == "generic":
                assert joint["type"] == "GENERIC" and not joint["use_limit_lin_x"]
                assert not row["drivers"]
                for axis in "yz":
                    assert joint["use_limit_lin_" + axis]
                    assert joint["limit_lin_" + axis + "_lower"] == joint["limit_lin_" + axis + "_upper"] == 0
                for axis in "xyz":
                    assert joint["use_limit_ang_" + axis]
                    assert joint["limit_ang_" + axis + "_lower"] == joint["limit_ang_" + axis + "_upper"] == 0
            else:
                assert joint["type"] == "MOTOR" and joint["use_motor_lin"] and not joint["use_motor_ang"]
                assert abs(joint["motor_lin_target_velocity"] + speed / 1000) < 1e-7
                assert joint["motor_lin_max_impulse"] == 100000
                drive, = row["drivers"]
                variable, = drive["variables"]
                target, = variable["targets"]
                assert drive["data_path"] == "rigid_body_constraint.motor_lin_target_velocity"
                assert drive["expression"] == "-speed_mm_s / 1000.0"
                assert variable["name"] == "speed_mm_s" and variable["type"] == "SINGLE_PROP"
                assert target == {"id": lane + "_carriage", "data_path": '["speed_mm_s"]'}
    stop = objects["left_stop"]
    assert stop["properties"]["near_face_mm"] == STOPS[case]
    assert stop["properties"]["half_width_mm"] == 15
    drive, = stop["drivers"]
    assert drive["data_path"] == "location" and drive["array_index"] == 0
    assert drive["expression"] == "(near_face_mm + half_width_mm) / 1000.0"
    assert {v["name"] for v in drive["variables"]} == {"near_face_mm", "half_width_mm"}
    for variable in drive["variables"]:
        assert variable["type"] == "SINGLE_PROP" and len(variable["targets"]) == 1
        assert variable["targets"][0] == {"id": "left_stop", "data_path": '["' + variable["name"] + '"]'}
    for name in ("base", "right_stop"):
        assert not objects[name]["drivers"]


def capture(scene):
    samples = []
    for frame in range(481):
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        matrices, bounds = {}, {}
        for name in PARTS:
            obj = scene.objects[name]
            matrix = obj.evaluated_get(graph).matrix_world.copy()
            points = [matrix @ Vector(corner) for corner in obj.bound_box]
            source = [[point.x * 1000, point.z * 1000, -point.y * 1000] for point in points]
            matrices[name] = [list(row) for row in matrix]
            bounds[name] = [[min(point[a] for point in source) for a in range(3)],
                            [max(point[a] for point in source) for a in range(3)]]
        samples.append({"frame": frame, "time_s": frame / 240, "matrices_blender_m": matrices, "bounds_gltf_mm": bounds})
    return samples


def summarize(samples, case):
    ideal = (STOPS[case] - 180) / 125
    lanes = {}
    for lane, speed in (("left", 125), ("right", 150)):
        x = [row["matrices_blender_m"][lane + "_carriage"][0][3] * 1000 for row in samples]
        travel = [value - x[0] for value in x]
        velocity = [(x[i + 1] - x[i]) * 240 for i in range(480)]
        gaps = [row["bounds_gltf_mm"][lane + "_stop"][0][0] - row["bounds_gltf_mm"][lane + "_shoe"][1][0]
                for row in samples]
        expected_travel = 300 if lane == "right" else (250 if case == "D" else STOPS[case] - 180)
        expected_gap = 15 if lane == "right" else (-50 if case == "D" else 0)
        assert abs(travel[-1] - expected_travel) <= .5
        assert abs(gaps[-1] - expected_gap) <= .5
        assert abs(velocity[0] - speed) <= .5, "First native interval does not provide requested feed"
        report = {"final_travel_mm": travel[-1], "final_gap_mm": gaps[-1], "minimum_sample_gap_mm": min(gaps),
            "first_interval_speed_mm_s": velocity[0], "velocity_min_mm_s": min(velocity), "velocity_max_mm_s": max(velocity)}
        if lane == "left" and case != "D":
            pre = [v for i, v in enumerate(velocity) if (i + 1) / 240 <= ideal - 1 / 240 + 3e-7]
            post = [v for i, v in enumerate(velocity) if i / 240 >= ideal + .025 - 3e-7]
            assert max(abs(v - 125) for v in pre) <= .5
            assert max(map(abs, post)) <= .5
            assert min(gaps) >= -.5
            report["settled_max_abs_speed_mm_s"] = max(map(abs, post))
            report["settled_gate_s"] = ideal + .025
        else:
            assert max(abs(v - speed) for v in velocity) <= .5
        lanes[lane] = report
    return {"case": case, "pass": True, "samples": 481, "lanes": lanes,
        "recorded_cadence_hz": 240, "nominal_solver_step_s": 1 / 2400,
        "scope": "Native evaluated poses and finite differences; no direct Bullet velocity, manifold or impulse telemetry"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--case", choices=tuple(STOPS), required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    args.out.mkdir(parents=True, exist_ok=False)
    backend = json.loads((args.contract / "backend.json").read_text())
    scene = bpy.context.scene
    scene.frame_set(0)
    bpy.context.view_layer.update()
    before = config(scene, backend)
    (args.out / "configuration-before.json").write_text(json.dumps(before, indent=2) + "\n")
    verify_configuration(before, backend, args.source, args.canonical, args.case)
    cleared = bpy.ops.ptcache.free_bake_all()
    assert cleared == {"FINISHED"}, "Native point-cache clearing did not complete"
    scene.frame_set(0)
    bpy.context.view_layer.update()
    after = config(scene, backend)
    assert after == before, "Cache clear or initialization changed persisted configuration"
    samples = capture(scene)
    (args.out / "native-transforms.json").write_text(json.dumps(samples, separators=(",", ":"), allow_nan=False) + "\n")
    summary = summarize(samples, args.case)
    summary.update(cache_clear_operation="bpy.ops.ptcache.free_bake_all", cache_clear_completed=True,
        configuration_unchanged=True, reconstructed_or_repaired=False,
        opened_scene_sha256=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
        canonical_input_sha256=hashlib.sha256(args.canonical.read_bytes()).hexdigest())
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("C191_INDEPENDENT_REOPEN " + json.dumps(summary))


if __name__ == "__main__":
    main()
