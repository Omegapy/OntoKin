"""Render checked samples of actual GLB imports with pinned Blender CPU Cycles.

Run with Blender, not ordinary Python:
  blender --background --factory-startup --threads 8 --python render_frames.py -- \
    --output /fresh/output --job route-case /path/to/final.glb 1.6

Repeat --job for a batch. Each job renders t=0, its supplied ideal-contact time,
and t=2. All three imported poses must match a separate GLB decoder first.
No geometry, material, animation or physics is rebuilt from source parameters.
"""
import argparse
import bisect
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Matrix, Vector


EXPECTED_IDS = {"base", "left_carriage", "left_shoe", "left_stop",
                "right_carriage", "right_shoe", "right_stop"}
EYE = (0.46, 0.90, 0.96)
TARGET = (0.19, 0.014, 0.09)
UP = (0.0, 1.0, 0.0)
FPS = 60
WIDTH, HEIGHT = 720, 410
BOUNDS_TOLERANCE_M = 0.00005


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def map_to_blender(p):
    return (p[0], -p[2], p[1])


def map_to_gltf(p):
    return (p[0], p[2], -p[1])


def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def transform(matrix, p):
    return tuple(sum(matrix[i][j] * p[j] for j in range(3)) + matrix[i][3] for i in range(3))


def trs(t, q, s):
    x, y, z, w = q
    norm = math.sqrt(x*x + y*y + z*z + w*w)
    x, y, z, w = (v / norm for v in (x, y, z, w))
    r = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
         [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
         [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    return [[r[i][j] * s[j] for j in range(3)] + [t[i]] for i in range(3)] + [[0, 0, 0, 1]]


def bounds(points):
    return [list(map(min, zip(*points))), list(map(max, zip(*points)))]


class GlbReader:
    """Small independent reader for these rigid, unskinned glTF recordings."""

    def __init__(self, path):
        data = Path(path).read_bytes()
        magic, version, length = struct.unpack_from("<4sII", data)
        assert magic == b"glTF" and version == 2 and length == len(data)
        offset = 12
        chunks = {}
        while offset < len(data):
            size, kind = struct.unpack_from("<I4s", data, offset)
            assert kind not in chunks
            chunks[kind] = data[offset + 8:offset + 8 + size]
            offset += 8 + size
        self.doc = json.loads(chunks[b"JSON"])
        self.binary = chunks[b"BIN\x00"]
        assert len(self.doc["buffers"]) == 1 and "uri" not in self.doc["buffers"][0]
        assert not self.doc.get("skins")
        self.nodes = self.doc["nodes"]
        self.parents = {}
        for i, node in enumerate(self.nodes):
            for child in node.get("children", []):
                assert child not in self.parents
                self.parents[child] = i
        self.mesh_nodes = {node["name"]: i for i, node in enumerate(self.nodes) if "mesh" in node}
        assert set(self.mesh_nodes) == EXPECTED_IDS and len(self.mesh_nodes) == 7
        self.tracks = {}
        animation, = self.doc["animations"]
        for channel in animation["channels"]:
            target = channel["target"]
            assert target["path"] in ("translation", "rotation", "scale")
            sampler = animation["samplers"][channel["sampler"]]
            interpolation = sampler.get("interpolation", "LINEAR")
            assert interpolation in ("LINEAR", "STEP")
            times = [v[0] for v in self.accessor(sampler["input"])]
            assert times == sorted(set(times))
            assert times[0] == 0 and times[-1] == 2
            self.tracks[target["node"], target["path"]] = (
                times, self.accessor(sampler["output"]), interpolation)
        self.positions = {}
        for name, index in self.mesh_nodes.items():
            mesh = self.doc["meshes"][self.nodes[index]["mesh"]]
            assert mesh.get("name") == name
            self.positions[name] = [p for prim in mesh["primitives"]
                for p in self.accessor(prim["attributes"]["POSITION"])]

    def accessor(self, index):
        a = self.doc["accessors"][index]
        assert "sparse" not in a and not a.get("normalized", False)
        view = self.doc["bufferViews"][a["bufferView"]]
        assert view.get("buffer", 0) == 0
        scalar = {5126: "f", 5125: "I", 5123: "H", 5121: "B"}[a["componentType"]]
        width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        fmt = struct.Struct("<" + scalar * width)
        start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = view.get("byteStride", fmt.size)
        return [fmt.unpack_from(self.binary, start + i * stride) for i in range(a["count"])]

    def sample(self, node, path, time, default):
        track = self.tracks.get((node, path))
        if track is None:
            return default
        times, values, kind = track
        i = min(max(bisect.bisect_right(times, time) - 1, 0), len(times) - 1)
        if i == len(times) - 1 or kind == "STEP":
            return values[i]
        u = (time - times[i]) / (times[i + 1] - times[i])
        a, b = values[i], values[i + 1]
        if path == "rotation":
            dot = sum(x*y for x, y in zip(a, b))
            if dot < 0:
                b = tuple(-v for v in b)
                dot = -dot
            if dot < 0.9995:
                angle = math.acos(min(1, dot))
                den = math.sin(angle)
                return tuple((math.sin((1-u)*angle)*x + math.sin(u*angle)*y)/den for x, y in zip(a, b))
            q = tuple((1-u)*x + u*y for x, y in zip(a, b))
            norm = math.sqrt(sum(v*v for v in q))
            return tuple(v/norm for v in q)
        return tuple((1-u)*x + u*y for x, y in zip(a, b))

    def world_bounds(self, time):
        matrices = {}

        def matrix(index):
            if index in matrices:
                return matrices[index]
            node = self.nodes[index]
            if "matrix" in node:
                assert not any((index, key) in self.tracks for key in ("translation", "rotation", "scale"))
                m = [[node["matrix"][j*4+i] for j in range(4)] for i in range(4)]
            else:
                m = trs(self.sample(index, "translation", time, node.get("translation", [0, 0, 0])),
                    self.sample(index, "rotation", time, node.get("rotation", [0, 0, 0, 1])),
                    self.sample(index, "scale", time, node.get("scale", [1, 1, 1])))
            if index in self.parents:
                m = multiply(matrix(self.parents[index]), m)
            matrices[index] = m
            return m

        return {name: bounds([transform(matrix(index), p) for p in self.positions[name]])
                for name, index in self.mesh_nodes.items()}


def imported_bounds():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    result = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        result[obj.name] = bounds([map_to_gltf(evaluated.matrix_world @ vertex.co)
                                   for vertex in evaluated.data.vertices])
    assert set(result) == EXPECTED_IDS and len(result) == 7
    return result


def set_time(time):
    frame = time * FPS
    integer = math.floor(frame)
    bpy.context.scene.frame_set(integer, subframe=frame-integer)
    bpy.context.view_layer.update()
    return frame


def linear_channel(s):
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def look_at(obj, eye, target, up):
    eye, target, up = Vector(eye), Vector(target), Vector(up)
    direction = (target - eye).normalized()
    right = direction.cross(up).normalized()
    corrected_up = right.cross(direction).normalized()
    basis = Matrix((right, corrected_up, -direction)).transposed().to_4x4()
    basis.translation = eye
    obj.matrix_world = basis


def configure_renderer(samples, threads, light_scale):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.seed = 190
    scene.cycles.use_animated_seed = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1

    camera_data = bpy.data.cameras.new("C187_camera")
    camera = bpy.data.objects.new("C187_camera", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "PERSP"
    camera_data.sensor_fit = "VERTICAL"
    camera_data.sensor_height = 32
    camera_data.lens = 32 / (2 * math.tan(math.radians(34) / 2))
    camera_data.clip_start = 0.01
    camera_data.clip_end = 30
    look_at(camera, map_to_blender(EYE), map_to_blender(TARGET), map_to_blender(UP))
    scene.camera = camera
    assert abs(math.degrees(camera_data.angle_y) - 34) < 0.0001

    world = bpy.data.worlds.new("C190_capture_world")
    scene.world = world
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputWorld")
    mix = nodes.new("ShaderNodeMixShader")
    light_path = nodes.new("ShaderNodeLightPath")
    camera_bg = nodes.new("ShaderNodeBackground")
    camera_bg.inputs["Color"].default_value = tuple(linear_channel(v/255) for v in (33, 50, 61)) + (1,)
    camera_bg.inputs["Strength"].default_value = 1
    ambient = nodes.new("ShaderNodeBackground")
    ambient.inputs["Color"].default_value = (1, 1, 1, 1)
    ambient.inputs["Strength"].default_value = 0.2
    links.new(light_path.outputs["Is Camera Ray"], mix.inputs[0])
    links.new(ambient.outputs[0], mix.inputs[1])
    links.new(camera_bg.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    lighting = []
    for name, eye, energy, size in [
            ("capture_key", (0.0, 1.5, 0.8), 200, 2),
            ("capture_fill", (-0.8, 0.6, -0.8), 80, 2)]:
        light_data = bpy.data.lights.new(name, "AREA")
        light_data.energy = energy * light_scale
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new(name, light_data)
        scene.collection.objects.link(light)
        look_at(light, map_to_blender(eye), map_to_blender((0.19, 0.08, 0)), map_to_blender(UP))
        lighting.append({"name": name, "type": "AREA_DISK", "position_gltf_m": eye,
                         "energy_w": energy * light_scale, "size_m": size})
    return {"eye_gltf_m": EYE, "target_gltf_m": TARGET, "up_gltf": UP,
        "gltf_to_blender": "(x, y, z) -> (x, -z, y)",
        "vertical_fov_degrees_requested": 34, "vertical_fov_degrees_actual": math.degrees(camera_data.angle_y),
        "near_m": camera_data.clip_start, "far_m": camera_data.clip_end,
        "resolution_px": [WIDTH, HEIGHT], "background_srgb_hex": "#21323d",
        "matrix_world_blender": [list(row) for row in camera.matrix_world],
        "ambient_world_strength": 0.2, "lighting": lighting,
        "color_management": {"view_transform": "Standard", "look": "None", "exposure": 0, "gamma": 1}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--job", action="append", nargs=3, metavar=("LABEL", "GLB", "IDEAL_CONTACT_S"), required=True)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--light-scale", type=float, default=0.1)
    parser.add_argument("--attempt", default="corrected-low-light")
    parser.add_argument("--append", action="store_true", help="Add new jobs to a matching existing receipt")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    assert bpy.app.version == (4, 5, 3), "This capture contract requires pinned Blender 4.5.3."
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    receipt = {"task": "C191 actual GLB import renders", "started_utc": utc(),
        "attempt": args.attempt, "area_light_scale": args.light_scale,
        "capture_kind": "Blender CPU-rendered frames of imported delivered GLBs",
        "browser_capture": False, "browser_playback_claim": False,
        "renderer_change": "C187 camera preserved; CPU Cycles differs from the C189 browser renderer.",
        "engine": "CYCLES", "device": "CPU", "samples": args.samples, "threads": args.threads,
        "blender_version": bpy.app.version_string, "blender_build_hash": bpy.app.build_hash.decode(),
        "blender_executable": bpy.app.binary_path, "blender_executable_sha256": digest(bpy.app.binary_path),
        "script_sha256": digest(__file__), "command_argv": sys.argv,
        "import_scene_fps": FPS, "frame_origin": "t=0 maps to Blender frame 0",
        "import_vs_glb_bounds_tolerance_m": BOUNDS_TOLERANCE_M, "jobs": []}
    if args.append:
        old = json.loads((output / "receipt.json").read_text())
        for key in ["script_sha256", "attempt", "area_light_scale", "engine", "device", "samples", "threads"]:
            assert old[key] == receipt[key], (key, old[key], receipt[key])
        old.setdefault("command_history", [old["command_argv"]]).append(sys.argv)
        receipt = old
    for label, filename, contact_text in args.job:
        assert label.replace("-", "").replace("_", "").isalnum()
        path = Path(filename).resolve()
        contact = float(contact_text)
        assert 0 < contact < 2
        directory = output / label
        directory.mkdir(exist_ok=False)
        reader = GlbReader(path)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        scene.render.fps = FPS
        scene.render.fps_base = 1
        bpy.ops.import_scene.gltf(filepath=str(path))
        meshes = [obj for obj in scene.objects if obj.type == "MESH"]
        assert {obj.name for obj in meshes} == EXPECTED_IDS and len(meshes) == 7
        assert not scene.rigidbody_world and not any(obj.rigid_body for obj in meshes)
        job = {"label": label, "input_glb": str(path), "input_sha256": digest(path),
            "mesh_names": sorted(obj.name for obj in meshes), "mesh_count": len(meshes),
            "imported_actions": [{"name": a.name, "frame_range": list(a.frame_range)} for a in bpy.data.actions],
            "all_sampled_imports_match_glb": False, "frames": []}
        for time in [0.0, contact, 2.0]:
            frame = set_time(time)
            actual = imported_bounds()
            expected = reader.world_bounds(time)
            error = max(abs(a-b) for name in EXPECTED_IDS
                        for actual_corner, expected_corner in zip(actual[name], expected[name])
                        for a, b in zip(actual_corner, expected_corner))
            assert error <= BOUNDS_TOLERANCE_M, (label, time, error, actual, expected)
            job["frames"].append({"time_seconds": time, "blender_frame": frame,
                "maximum_import_vs_glb_bounds_error_m": error,
                "expected_glb_world_bounds_m": expected, "imported_world_bounds_gltf_m": actual,
                "left_signed_gap_mm": 1000*(actual["left_stop"][0][0] - actual["left_shoe"][1][0]),
                "right_signed_gap_mm": 1000*(actual["right_stop"][0][0] - actual["right_shoe"][1][0])})
        job["all_sampled_imports_match_glb"] = True
        job["camera"] = configure_renderer(args.samples, args.threads, args.light_scale)
        write_json(directory / "receipt.json", job)
        for record in job["frames"]:
            set_time(record["time_seconds"])
            image = directory / f"t-{record['time_seconds']:.3f}.png"
            scene.render.filepath = str(image)
            bpy.ops.render.render(write_still=True)
            record["png"] = image.name
            record["png_sha256"] = digest(image)
            record["png_bytes"] = image.stat().st_size
            write_json(directory / "receipt.json", job)
        job["finished_utc"] = utc()
        write_json(directory / "receipt.json", job)
        receipt["jobs"].append(job)
        write_json(output / "receipt.json", receipt)
        print(f"C191_CAPTURE_COMPLETE {label} {len(job['frames'])} frames", flush=True)
    receipt["finished_utc"] = utc()
    receipt["rendered_png_count"] = sum(len(j["frames"]) for j in receipt["jobs"])
    receipt["outcome"] = "all requested imported samples verified and rendered"
    write_json(output / "receipt.json", receipt)
    print(json.dumps({"outcome": receipt["outcome"], "png_count": receipt["rendered_png_count"]}), flush=True)


if __name__ == "__main__":
    main()
