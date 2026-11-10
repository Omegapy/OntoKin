"""Validate the finite native interchange before recording or publication."""
from collections import Counter
import csv
import hashlib
import math
import os
import struct

from .common import Failure, PARTS, canonical_bytes, schema_check, sha256, strict_json


def near(value, expected, tolerance=1e-7):
    if isinstance(expected, list):
        return isinstance(value, list) and len(value) == len(expected) and all(near(a, b, tolerance) for a, b in zip(value, expected))
    if type(expected) in (float, int):
        return type(value) in (float, int) and math.isfinite(value) and abs(value - expected) <= tolerance
    return value == expected


def native(vector):
    return [vector[0] / 1000, -vector[2] / 1000, vector[1] / 1000]


def source_centers(source):
    origins = {key: value["at_mm"] for key, value in source["parts"].items() if "at_mm" in value}
    for follow in source["follows"].values():
        origins[follow["child"]] = [a + b for a, b in zip(origins[follow["parent"]], follow["offset_mm"])]
    return {key: [origins[key][a] + part["box_mm"][a] / 2 for a in range(3)] for key, part in source["parts"].items()}


def validate_scene_artifact(path, context, budget, contract):
    """Validate the complete pinned .blend envelope; reopen is a separate gate.

    A valid trace cannot stand in for the editable saved scene promised by the
    output contract. Walk every uncompressed 64-bit block, require complete
    payloads and the final ENDB, and reject trailing bytes. Payload semantics and
    replay are intentionally left to the independent native reopening gate.
    """
    span = context.span(context.headers["backend"])
    budget.check()
    if not path.is_file():
        raise Failure("E_NATIVE_FAILURE", "Native worker did not create scene.blend", span)
    try:
        block_header = struct.Struct("<4siQii")
        counts = Counter()
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            total_bytes = os.fstat(stream.fileno()).st_size
            if total_bytes > contract["backend"]["limits"]["staged_output_bytes"]:
                raise Failure("E_RESOURCE_LIMIT", "Saved native scene exceeds output ceiling", budget.anchor)
            header = stream.read(12)
            major, minor, _ = contract["backend"]["runtime"]["blender_version"]
            expected = b"BLENDER-v" + f"{major}{minor:02d}".encode("ascii")
            if header != expected:
                raise ValueError("Saved native scene has no compatible Blender file header")
            digest.update(header)
            position = len(header)
            while True:
                budget.charge("native_scene_block_fields", 5)
                encoded = stream.read(block_header.size)
                if len(encoded) != block_header.size:
                    raise ValueError("Saved native scene has a truncated block header or missing ENDB")
                digest.update(encoded)
                position += len(encoded)
                code, payload_size, old_address, dna_index, count = block_header.unpack(encoded)
                counts[code] += 1
                if payload_size < 0 or dna_index < 0 or count < 0:
                    raise ValueError("Saved native scene has negative block fields")
                if code == b"ENDB":
                    if (payload_size, old_address, dna_index, count) != (0, 0, 0, 0):
                        raise ValueError("Saved native scene has a malformed ENDB block")
                    if position != total_bytes or stream.read(1):
                        raise ValueError("Saved native scene has bytes after ENDB")
                    break
                if payload_size > total_bytes - position:
                    raise ValueError("Saved native scene block payload extends beyond EOF")
                if code == b"DNA1" and payload_size < 4:
                    raise ValueError("Saved native scene has an incomplete DNA block")
                remaining = payload_size
                first_chunk = True
                while remaining:
                    budget.check()
                    chunk = stream.read(min(65536, remaining))
                    if not chunk:
                        raise ValueError("Saved native scene has a truncated block payload")
                    if code == b"DNA1" and first_chunk and chunk[:4] != b"SDNA":
                        raise ValueError("Saved native scene has no SDNA payload marker")
                    first_chunk = False
                    digest.update(chunk)
                    remaining -= len(chunk)
                    position += len(chunk)
            if counts[b"GLOB"] != 1 or counts[b"DNA1"] != 1:
                raise ValueError("Saved native scene must have one global and one DNA block")
            if any(not counts[code] for code in (b"SC\x00\x00", b"OB\x00\x00", b"ME\x00\x00")):
                raise ValueError("Saved native scene lacks scene/object/mesh blocks")
        report = {"source_sha256": context.sha, "scene_sha256": digest.hexdigest(),
                  "bytes_checked": position, "blocks_checked": sum(counts.values()),
                  "block_counts": {code.rstrip(b"\x00").decode("ascii", "backslashreplace"): count
                                   for code, count in sorted(counts.items())},
                  "method": "Complete bounded uncompressed 64-bit little-endian .blend block envelope through ENDB, with no trailing bytes; each block and payload chunk checks the attempt budget.",
                  "scope_limit": "No DNA/scene semantics or replay claim. Fresh pinned Blender opening, configuration inspection and native re-simulation remain separate gates."}
        (path.parent / "native-scene-validation.json").write_bytes(canonical_bytes(report))
    except (OSError, ValueError, struct.error) as exc:
        raise Failure("E_NATIVE_RESULT", str(exc), span) from exc
    budget.check()


def validate_native(path, context, budget, contract):
    span = context.span(context.headers["backend"])
    try:
        size = path.stat().st_size
        budget.native_result_bytes = size
        if size > contract["backend"]["limits"]["native_result_bytes"]:
            raise Failure("E_RESOURCE_LIMIT", "Native result byte ceiling exceeded", budget.anchor)
        with path.open("rb") as stream:
            data = stream.read(contract["backend"]["limits"]["native_result_bytes"] + 1)
        if len(data) > contract["backend"]["limits"]["native_result_bytes"]:
            raise Failure("E_RESOURCE_LIMIT", "Native result grew beyond its byte ceiling", budget.anchor)
        result = strict_json(data)
        schema_check(result, contract["native_schema"], budget=budget)
        validate_configuration(result["configuration"], context, contract)
        if result["source_sha256"] != context.sha or result["canonical_input_sha256"] != context.canonical_sha:
            raise ValueError("Native result revision or canonical-input mismatch")
        initial = result["samples"][0]
        centers = source_centers(context.canonical)
        maximum_attachment_deviation_mm = 0.0
        for frame, record in enumerate(result["samples"]):
            if record["frame"] != frame or record["time_s"] != frame / 240:
                raise ValueError("Native sample sequence/time mismatch")
            for name, matrix in record["matrices_blender_m"].items():
                budget.charge("native_matrix_scalars", 16)
                if matrix[3] != [0, 0, 0, 1] or any(abs(v) > 10 for row in matrix for v in row):
                    raise ValueError("Native matrix is not a bounded affine transform")
                for a in range(3):
                    for b in range(3):
                        dot = sum(matrix[k][a] * matrix[k][b] for k in range(3))
                        if abs(dot - (1 if a == b else 0)) > 1e-5:
                            raise ValueError("Native matrix contains scale/shear")
                determinant = (matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
                               - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
                               + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]))
                if abs(determinant - 1) > 1e-5:
                    raise ValueError("Native transform is not a proper rotation")
                if frame == 0 and not near([matrix[a][3] for a in range(3)], native(centers[name])):
                    raise ValueError("Initial native frame differs from source: " + name)
                if frame == 0 and not near(matrix, result["configuration"]["objects"][name]["matrix_world"]):
                    raise ValueError("Initial evaluated matrix differs from saved configuration")
                if name in ("base", "left_stop", "right_stop") and matrix != initial["matrices_blender_m"][name]:
                    raise ValueError("Native fixed part moved: " + name)
                bounds = record["bounds_gltf_mm"][name]
                if any(bounds[0][a] > bounds[1][a] for a in range(3)):
                    raise ValueError("Native bounds are inverted")
                points = []
                for vertex in result["configuration"]["objects"][name]["mesh_vertices"]:
                    budget.charge("native_bound_vertex_checks")
                    point = [sum(matrix[a][k] * vertex[k] for k in range(3)) + matrix[a][3] for a in range(3)]
                    points.append([point[0] * 1000, point[2] * 1000, -point[1] * 1000])
                expected_bounds = [[min(point[a] for point in points) for a in range(3)],
                                   [max(point[a] for point in points) for a in range(3)]]
                if not near(bounds, expected_bounds, tolerance=0.0002):
                    raise ValueError("Native bounds disagree with recorded matrices/geometry")
            for lane in ("left", "right"):
                parent_name, child_name = lane + "_carriage", lane + "_shoe"
                parent = record["matrices_blender_m"][parent_name]
                child = record["matrices_blender_m"][child_name]
                child_config = result["configuration"]["objects"][child_name]
                offset = child_config["location"]
                for vertex in child_config["mesh_vertices"]:
                    budget.charge("native_attachment_vertex_checks")
                    actual = [sum(child[a][k] * vertex[k] for k in range(3)) + child[a][3] for a in range(3)]
                    expected = [sum(parent[a][k] * (vertex[k] + offset[k]) for k in range(3)) + parent[a][3] for a in range(3)]
                    deviation_mm = 1000 * math.sqrt(sum((a - b) ** 2 for a, b in zip(actual, expected)))
                    maximum_attachment_deviation_mm = max(maximum_attachment_deviation_mm, deviation_mm)
                    if deviation_mm > 0.1:
                        raise ValueError("Native shoe/body attachment exceeds 0.1 mm: " + child_name)
        for lane in ("left", "right"):
            name = lane + "_carriage"
            first_speed = (result["samples"][1]["matrices_blender_m"][name][0][3]
                           - initial["matrices_blender_m"][name][0][3]) * 1000 * 240
            if abs(first_speed - context.canonical["bodies"]["body." + lane]["feed_mm_s"]) > 0.5:
                raise ValueError("Native first-interval feed differs from source")
        (path.parent / "native-validation.json").write_bytes(canonical_bytes({
            "source_sha256": context.sha, "native_result_sha256": sha256(data),
            "samples_checked": len(result["samples"]),
            "maximum_attachment_vertex_deviation_mm": maximum_attachment_deviation_mm,
            "attachment_limit_mm": 0.1,
            "method": "At every recorded state, compare each shoe vertex transformed by its own native world matrix with the same vertex through its frozen body-local offset and owning carriage native matrix."}))
        return result
    except Failure:
        raise
    except (ValueError, TypeError, KeyError, OSError, IndexError, OverflowError, RecursionError) as exc:
        raise Failure("E_NATIVE_RESULT", str(exc), span) from exc


def validate_configuration(configuration, context, contract):
    source, backend = context.canonical, contract["backend"]
    tags = {"source_sha256": context.sha, "canonical_input_sha256": context.canonical_sha,
            "source_binding": source["source_binding"], "profile_binding": source["profile"],
            "backend_binding": source["backend"], "output_binding": source["output"],
            "module_key": source["module_key"], "scene_key": source["scene_key"]}
    if configuration["scene_tags"] != tags:
        raise ValueError("Persisted source/backend identity differs")
    world = configuration["world"]
    for name in world:
        if name in backend["world"] and not near(world[name], backend["world"][name]):
            raise ValueError("Unqualified world setting: " + name)
    rows = {row["name"]: row for row in backend["native_objects"]}
    objects = configuration["objects"]
    if set(objects) != set(rows):
        raise ValueError("Native object inventory differs")
    expected_bodies, expected_constraints = [], []
    centers = source_centers(source)
    identity = [[1 if a == b else 0 for b in range(4)] for a in range(4)]
    for name, row in rows.items():
        obj = objects[name]
        expected_type = "EMPTY" if row["kind"] == "constraint" else "MESH"
        if obj["type"] != expected_type:
            raise ValueError("Native object type differs from its declared role: " + name)
        part, body, collider = row.get("source_part") or "", row.get("source_body") or "", row.get("source_collider") or ""
        expected_props = {"part_id": part, "body_id": body, "collider_id": collider,
                          "helper_role": row["kind"], "source_occurrence": f'{source["module_key"]}/{source["scene_key"]}/{part or body}'}
        if name in ("left_carriage", "right_carriage"):
            expected_props.update(speed_mm_s=source["bodies"][body]["feed_mm_s"], motion_authority="solver")
        if name == "left_stop":
            expected_props.update(near_face_mm=source["parts"][name]["at_mm"][0], half_width_mm=source["parts"][name]["box_mm"][0] / 2)
        if set(obj["properties"]) != set(expected_props) or any(not near(obj["properties"][k], v) for k, v in expected_props.items()):
            raise ValueError("Native source tags/properties differ: " + name)
        if obj["parent"] != row.get("parent") or obj["hide_render"] != row.get("hide_render", False):
            raise ValueError("Native parent/visibility differs: " + name)
        if obj["has_action"] or not near(obj["scale"], [1, 1, 1]) or not near(obj["rotation_quaternion_wxyz"], [1, 0, 0, 0]):
            raise ValueError("Native transform authority/initial orientation differs: " + name)
        if not near(obj["matrix_parent_inverse"], identity):
            raise ValueError("Native parent inverse differs: " + name)
        expected_center = native(centers[part]) if part else native(centers[source["bodies"][body]["part"]])
        expected_world = [row[:] for row in identity]
        for axis in range(3):
            expected_world[axis][3] = expected_center[axis]
        if not near(obj["matrix_world"], expected_world):
            raise ValueError("Native initial world frame differs: " + name)
        expected_location = expected_center
        if row["kind"] == "hidden_compound_child":
            expected_location = [0, 0, 0]
        elif row.get("parent"):
            expected_location = native([centers[part][a] - centers[row["parent"]][a] for a in range(3)])
        if not near(obj["location"], expected_location):
            raise ValueError("Native local/body frame differs: " + name)
        if part:
            box = source["parts"][part]["box_mm"]
            half = [box[0] / 2000, box[2] / 2000, box[1] / 2000]
            if not near(obj["mesh_local_bounds"], [[-v for v in half], half]):
                raise ValueError("Native geometry differs from declared box: " + name)
            expected_vertices = [[x, y, z] for x in (-half[0], half[0])
                                 for y in (-half[1], half[1]) for z in (-half[2], half[2])]
            if not near(sorted(obj["mesh_vertices"]), sorted(expected_vertices)):
                raise ValueError("Native vertices do not form the declared box: " + name)
        elif obj["mesh_vertices"] is not None:
            raise ValueError("Constraint unexpectedly has geometry")
        disabled = collider and not source["colliders"][collider]["enabled"]
        if row["kind"] != "constraint" and not disabled:
            expected_bodies.append(name)
            expected_rb = dict(backend["rigid_body_defaults"])
            expected_rb.update(type="PASSIVE" if name in ("base", "left_stop", "right_stop") else "ACTIVE",
                               collision_shape="COMPOUND" if name in ("left_carriage", "right_carriage") else "BOX")
            if obj["rigid_body"] is None or set(obj["rigid_body"]) != set(expected_rb) or any(not near(obj["rigid_body"][k], v) for k, v in expected_rb.items()):
                raise ValueError("Native body/mass/filter differs: " + name)
        elif obj["rigid_body"] is not None:
            raise ValueError("Unexpected independent body: " + name)
        if row["kind"] == "constraint":
            expected_constraints.append(name)
            lane = body.removeprefix("body.")
            kind = row["constraint_type"]
            rule = backend["guide" if kind == "GENERIC" else "motor"]
            expected = {"type": kind, "object1": "base", "object2": lane + "_carriage",
                        "disable_collisions": True, "use_override_solver_iterations": True,
                        "solver_iterations": rule["solver_iterations"], "use_motor_ang": False,
                        "use_motor_lin": kind == "MOTOR",
                        "motor_lin_target_velocity": -source["bodies"][body]["feed_mm_s"] / 1000 if kind == "MOTOR" else 1,
                        "motor_lin_max_impulse": rule["motor_lin_max_impulse"] if kind == "MOTOR" else 1}
            for axis in "xyz":
                for mode in ("lin", "ang"):
                    locked = kind == "GENERIC" and (mode == "ang" or axis != "x")
                    expected[f"use_limit_{mode}_{axis}"] = locked
                    bound = 0 if locked else (1 if mode == "lin" else 0.7853981852531433)
                    expected[f"limit_{mode}_{axis}_lower"] = -bound
                    expected[f"limit_{mode}_{axis}_upper"] = bound
            if set(obj["constraint"]) != set(expected) or any(not near(obj["constraint"][k], v) for k, v in expected.items()):
                raise ValueError("Native guide/motor differs: " + name)
        elif obj["constraint"] is not None:
            raise ValueError("Unexpected native constraint")
        if name.endswith("_motor"):
            lane = body.removeprefix("body.")
            expected_drivers = [{"data_path": "rigid_body_constraint.motor_lin_target_velocity", "array_index": 0,
                                 "type": "SCRIPTED", "expression": backend["motor"]["driver_expression"],
                                 "variables": [{"name": "speed_mm_s", "type": "SINGLE_PROP", "target_id": lane + "_carriage", "data_path": '["speed_mm_s"]'}]}]
        elif name == "left_stop":
            expected_drivers = [{"data_path": "location", "array_index": 0, "type": "SCRIPTED", "expression": backend["stop_driver"]["expression"],
                                 "variables": [{"name": variable, "type": "SINGLE_PROP", "target_id": "left_stop", "data_path": '["' + variable + '"]'}
                                               for variable in backend["stop_driver"]["variables"]]}]
        else:
            expected_drivers = []
        if obj["drivers"] != expected_drivers:
            raise ValueError("Native driver/authority differs: " + name)
    if world["body_collection"] != sorted(expected_bodies) or world["constraint_collection"] != sorted(expected_constraints):
        raise ValueError("Native solver collections differ")


def write_native_evidence(stage, result, context):
    (stage / "native-transforms.json").write_bytes(canonical_bytes(result["samples"]))
    (stage / "native-configuration.json").write_bytes(canonical_bytes(result["configuration"]))
    initial = result["samples"][0]
    previous = {}
    rows = []
    for record in result["samples"]:
        row = {"frame": record["frame"], "time_s": record["time_s"]}
        for lane in ("left", "right"):
            name = lane + "_carriage"
            x = record["matrices_blender_m"][name][0][3] * 1000
            gap = record["bounds_gltf_mm"][lane + "_stop"][0][0] - record["bounds_gltf_mm"][lane + "_shoe"][1][0]
            row[lane + "_carriage_travel_mm"] = x - initial["matrices_blender_m"][name][0][3] * 1000
            row[lane + "_gap_mm"] = gap
            row[lane + "_vx_fd_mm_s"] = None if lane not in previous else (x - previous[lane]) * 240
            row[lane + "_geometric_contact_0p01mm"] = abs(gap) <= 0.01
            previous[lane] = x
        rows.append(row)
    with (stage / "native-trace.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {"source_sha256": context.sha, "canonical_input_sha256": context.canonical_sha,
               "backend": context.canonical["backend"], "samples": len(rows), "sample_hz": 240,
               "nominal_scheduled_substeps": result["nominal_scheduled_substeps"],
               "observability": "Native evaluated poses; geometric gaps and finite-difference velocities are derived. Bullet manifolds/impulses/direct velocity are not exposed.",
               "lanes": {lane: {"mass_kg": context.canonical["bodies"]["body." + lane]["mass_kg"],
                                  "final_travel_mm": rows[-1][lane + "_carriage_travel_mm"],
                                  "final_gap_mm": rows[-1][lane + "_gap_mm"],
                                  "minimum_gap_mm": min(row[lane + "_gap_mm"] for row in rows)} for lane in ("left", "right")}}
    (stage / "native-summary.json").write_bytes(canonical_bytes(summary))
