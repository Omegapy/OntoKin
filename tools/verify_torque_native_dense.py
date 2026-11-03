#!/usr/bin/env python3
"""Actual pinned GLTFLoader/.22 playback versus independent source intervals.

Every stored interval is probed at all j/32 clocks, plus frozen common clocks
on both sides. Source pose expectations come exclusively from TorqueReference.
Local geometry construction is disclosed reuse; raw native geometry, PBR, UV
and decoded immutable PNG data are separately checked. Directed binary64
interval operations enclose matrix and source-box/site discrepancies. These
offline checks supplement, and never replace, the complete byte certificate.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import gzip
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import time
import traceback


def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(path, value): path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
def require(value, message):
    if not value: raise AssertionError(message)
def f32(value): return struct.unpack("<f", struct.pack("<f", value))[0]
def ratio(value): return F(int(value["numerator"]), int(value["denominator"]))


class OfflineWork:
    def __init__(self): self.operations = 0; self.started = time.monotonic()
    def tick(self):
        self.operations += 1
        require(self.operations <= 100000000, "Offline independent arithmetic exceeds100million checks")
        require(time.monotonic() - self.started <= 900, "Offline independent case exceeds900seconds")
    def record(self):
        return {"scope": "offline_native_reference_only", "operations": self.operations,
            "maximum_operations": 100000000, "elapsed_seconds": time.monotonic() - self.started,
            "maximum_elapsed_seconds": 900, "production_request_budgets_unchanged": True}


class Directed:
    """Outward binary64 intervals; inputs are exact stored/source cell values."""
    def __init__(self, work): self.work = work
    def point(self, x): return (float(x), float(x))
    def cell(self, cell):
        lo, hi = float(cell.lo), float(cell.hi)
        if F(lo) > cell.lo: lo = math.nextafter(lo, -math.inf)
        if F(hi) < cell.hi: hi = math.nextafter(hi, math.inf)
        return lo, hi
    def add(self, a, b):
        self.work.tick()
        return math.nextafter(a[0] + b[0], -math.inf), math.nextafter(a[1] + b[1], math.inf)
    def neg(self, a): return -a[1], -a[0]
    def sub(self, a, b): return self.add(a, self.neg(b))
    def mul(self, a, b):
        self.work.tick(); values = [a[i] * b[j] for i in (0, 1) for j in (0, 1)]
        return math.nextafter(min(values), -math.inf), math.nextafter(max(values), math.inf)
    def upper(self, values):
        result = 0.0
        for value in values:
            self.work.tick(); result = math.nextafter(result + value, math.inf)
        return result
    def matrix(self, quaternion):
        w, x, y, z = map(self.cell, quaternion); two = self.point(2); one = self.point(1)
        squared = lambda a: self.mul(a, a)
        pair = lambda a, b, c, d, sign: self.mul(two, self.add(self.mul(a, b),
            self.mul(c, d) if sign == 1 else self.neg(self.mul(c, d))))
        return ((self.sub(one, self.mul(two, self.add(squared(y), squared(z)))),
                 pair(x, y, w, z, -1), pair(x, z, w, y, 1)),
                (pair(x, y, w, z, 1), self.sub(one, self.mul(two, self.add(squared(x), squared(z)))),
                 pair(y, z, w, x, -1)),
                (pair(x, z, w, y, -1), pair(y, z, w, x, 1),
                 self.sub(one, self.mul(two, self.add(squared(x), squared(y))))))
    def discrepancy(self, matrix, reference, vertex, position, local_error=(0, 0, 0)):
        components = []
        for row in range(3):
            value = self.sub(self.point(matrix[12 + row]), position[row])
            for column in range(3):
                difference = self.sub(self.point(matrix[4 * column + row]), reference[row][column])
                value = self.add(value, self.mul(difference, self.point(vertex[column])))
            quantization = self.upper(abs(matrix[4 * column + row]) * local_error[column]
                                      for column in range(3))
            components.append(math.nextafter(max(abs(value[0]), abs(value[1])) + quantization, math.inf))
        return self.upper(components)


def unpack(raw):
    require(len(raw) <= 64 * 1024 * 1024, "GLB byte cap")
    require(struct.unpack_from("<III", raw) == (0x46546C67, 2, len(raw)), "GLB header")
    size, kind = struct.unpack_from("<II", raw, 12); require(kind == 0x4E4F534A, "JSON chunk")
    document = json.loads(raw[20:20 + size]); count, kind = struct.unpack_from("<II", raw, 20 + size)
    require(kind == 0x004E4942 and count + size + 28 == len(raw), "BIN chunk")
    return document, raw[28 + size:]


def accessor(document, binary, index):
    a = document["accessors"][index]; v = document["bufferViews"][a["bufferView"]]
    arity = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    fmt, width = {5126: ("f", 4), 5125: ("I", 4), 5123: ("H", 2)}[a["componentType"]]
    require(v.get("byteStride", width * arity) == width * arity, "Packed native accessor")
    offset = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    require(offset + width * arity * a["count"] <= len(binary), "Accessor extent")
    return list(struct.unpack_from("<" + fmt * a["count"] * arity, binary, offset))


def geometry(model, document, binary, inventory, work):
    from ontokin.geometry import box_mesh, sphere_mesh, assembly_marker, joint_marker
    from ontokin.surface_runtime import materialize_surface
    from PIL import Image
    from ontokin.reach_reference import _time_text
    source = {}; expected_native = {}; checks = 0
    for node in document["nodes"]:
        metadata = node["extras"]["ontokin"]
        if metadata["kind"] == "object":
            key = metadata["path"]; obj = model.objects[key]
            require(metadata["element_id"] == list(obj.element_id), "Native source occurrence identity")
            frame = key + ".frame"; kind = obj.geometry["kind"]
            mesh = None if kind == "empty" else box_mesh(obj.geometry["size"]) if kind == "box" else sphere_mesh(obj.geometry["radius"]) if kind == "sphere" else materialize_surface(obj.geometry, max_vertices=250000, check=work.tick)[0]
            sites = [tuple(site.pose.position) for site in model.sites.values() if site.owner == key]
        else:
            require(metadata["kind"] == "visual_helper", "Unknown native carrier kind")
            key = "helper:" + metadata["frame_path"] + ":" + metadata["helper_kind"]
            frame = metadata["frame_path"]; sites = []; obj = None
            if metadata["helper_kind"] == "assembly_origin": mesh = assembly_marker()
            else:
                require(metadata["helper_kind"] == "joint", "Unknown requested helper")
                mesh = joint_marker(model.joints[metadata["joint_path"]].axis)
        points = [] if mesh is None else list(mesh.positions)
        corners = (list(itertools.product(*[(min(p[i] for p in points), max(p[i] for p in points))
                    for i in range(3)])) if points else [(0, 0, 0)])
        errors = tuple(max((abs(f32(p[i]) - p[i]) for p in points), default=0.0) for i in range(3))
        source[key] = {"frame": frame, "corners": corners, "sites": sites,
            "local_quantization": errors, "source_vertices": len(points),
            "element_id": metadata.get("element_id", metadata.get("related_element_id"))}
        if mesh is None:
            require("mesh" not in node, "Empty source occurrence acquired native geometry"); continue
        mesh_index = node["mesh"]; actual_mesh = document["meshes"][mesh_index]
        regions = getattr(mesh, "regions", None)
        indices = [list(r.indices) for r in regions] if regions is not None else [list(mesh.indices)]
        require(len(indices) == len(actual_mesh["primitives"]), "Source/native primitive count")
        for pi, primitive in enumerate(actual_mesh["primitives"]):
            positions = accessor(document, binary, primitive["attributes"]["POSITION"])
            normals = accessor(document, binary, primitive["attributes"]["NORMAL"])
            require(positions == [f32(x) for p in mesh.positions for x in p], "Canonical source/native position stream")
            require(normals == [f32(x) for p in mesh.normals for x in p], "Canonical source/native normal stream")
            actual_indices = accessor(document, binary, primitive["indices"])
            require(actual_indices == indices[pi], "Canonical source/native index stream")
            attributes = {"position": positions, "normal": normals}
            if "TEXCOORD_0" in primitive["attributes"]:
                uv = accessor(document, binary, primitive["attributes"]["TEXCOORD_0"])
                region = regions[pi].key; binding = dict(obj.geometry["texture_bindings"])[region]
                mapping = binding.mapping
                predicted = []
                referenced = set(regions[pi].indices)
                for vertex_index, point in enumerate(mesh.positions):
                    for axis in ("u_per_m", "v_per_m"):
                        if vertex_index not in referenced:
                            predicted.append(0.0)
                            continue
                        value = sum((F(p) - F(o)) * F(scale) for p, o, scale in
                                    zip(point, mapping.origin_m, getattr(mapping, axis)))
                        value += F(mapping.offset[0 if axis == "u_per_m" else 1])
                        predicted.append(f32(float(value)))
                require(uv == predicted, "Independent source affine UV stream"); attributes["uv"] = uv
            material = document["materials"][primitive["material"]]["pbrMetallicRoughness"]
            if obj is not None:
                expected = ({"baseColorFactor": list(regions[pi].material.rgba),
                    "metallicFactor": regions[pi].material.metallic,
                    "roughnessFactor": regions[pi].material.roughness} if regions is not None else
                    {"baseColorFactor": list(obj.appearance), "metallicFactor": 0.0, "roughnessFactor": 0.7})
                require(all(material[k] == v for k, v in expected.items()), "Independent source PBR values")
            expected_native[(key, mesh_index, pi)] = (attributes, actual_indices, material)
            checks += sum(map(len, attributes.values())) + len(actual_indices) + 3
    seen = set()
    for loaded in inventory["meshes"]:
        association = loaded["association"]
        key = (loaded["carrier"], association["meshes"], association.get("primitives", 0))
        require(key not in seen and key in expected_native, "Actual GLTFLoader mesh identity")
        seen.add(key); attributes, indices, material = expected_native[key]
        require(set(loaded["attributes"]) == set(attributes), "Actual native attribute membership")
        for name, values in attributes.items():
            require(loaded["attributes"][name]["values"] == values, "Actual native decoded attribute: " + name)
            require(not loaded["attributes"][name]["normalized"], "Unexpected native attribute normalization")
        require(loaded["indices"] == indices, "Actual native decoded index stream")
        for native_material in loaded["materials"]:
            require(native_material["color"] + [native_material["opacity"]] == material["baseColorFactor"], "Actual native base color")
            require(native_material["metalness"] == material["metallicFactor"] and native_material["roughness"] == material["roughnessFactor"], "Actual native PBR")
            require(native_material["texture"] == ("baseColorTexture" in material), "Actual native texture binding")
    require(seen == set(expected_native), "Actual native complete primitive inventory")
    expected_images = []
    for asset in model.texture_assets.values():
        decoded = Image.open(io.BytesIO(asset.raw)).convert("RGBA")
        expected_images.append((decoded.width, decoded.height, list(decoded.tobytes())))
    for actual in inventory["images"]:
        require((actual["width"], actual["height"], actual["rgba"]) in expected_images,
                "Actual ImageBitmap/canvas decoded immutable PNG pixels")
        require(actual["colorSpace"] == "srgb", "Actual texture color space")
    require(len(inventory["images"]) == len(expected_images), "Complete native image inventory")
    return source, {"status": "passed", "scalar_stream_checks": checks,
        "primitive_count": len(seen), "image_count": len(expected_images),
        "geometry_constructor_reuse": "Inherited local box/sphere/surface/helper constructors only; motion and UV expectations are independently reconstructed.",
        "box_proof": "All eight extrema corners bound every source vertex by convexity; native per-axis binary32 local quantization is added through the actual matrix. Named sites are evaluated separately."}


def run_case(args, case, variant, process, frozen, physics, expectations):
    from ontokin.texture_bundle import load_texture_file_manifest
    from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
    from ontokin.construction import compile_construction
    from ontokin.reach_reference import build_reference
    folder = args.accepted / case["id"] / variant; output = args.output / case["id"] / variant
    output.mkdir(parents=True); result = {"case": case["id"], "variant": variant, "status": "running"}
    def rpc(request):
        process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n"); process.stdin.flush()
        line = process.stdout.readline(); require(bool(line), "Native worker terminated")
        response = json.loads(line); require(response.get("status") == "passed", response)
        return response
    work = OfflineWork()
    try:
        accepted = json.loads((folder / "result.json").read_text()); require(accepted["status"] == "passed", "Accepted input required")
        artifact = folder / "scene.glb"; raw = artifact.read_bytes(); digest = sha(raw)
        require(digest == accepted["artifact"]["sha256"], "Accepted original byte identity")
        document, binary = unpack(raw); bundle = load_texture_file_manifest(frozen / case["file_manifest"])
        require(bundle.program_revision == case["identity"]["program_revision"] == document["extras"]["ontokin"]["program"]["revision"], "Independent immutable source identity")
        ledger = SharedExecutionBudget(HostPolicy(**case["host_policy"]))
        admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
        compiler = compile_construction(bundle, execution_budget=ledger)
        reference = build_reference(compiler.model, end=F(case["options"]["end"]), check=work.tick, mode="recording")
        loaded = rpc({"operation": "load", "artifact": str(artifact), "sha256": digest,
                      "output": str(output), "shared_output": str(args.output / "implementation")})
        sources, geometry_result = geometry(compiler.model, document, binary, loaded["inventory"], work)
        require(set(sources) == {r["path"] for r in loaded["inventory"]["objects"]}, "Native root carrier membership")
        animation = document["animations"][0]; clocks = accessor(document, binary, animation["samplers"][0]["input"])
        require(len(clocks) <= 10000 and all(a < b for a, b in zip(clocks, clocks[1:])), "Actual retained clock order")
        schedule = {(F(a) + (F(b) - F(a)) * F(j, 32), "after")
                    for a, b in zip(clocks, clocks[1:]) for j in range(33)}
        dense_count = len(schedule); common = set()
        for row in physics[case["physics_case"]]["samples"]: common.add((F(row[0]), "after"))
        for row in expectations[case["physics_case"]]["observations"]:
            common.add((F(row["time_fraction"]), row["side"]))
        schedule = sorted(schedule | common, key=lambda x: (x[0], x[1])); require(len(schedule) <= 100000, "Offline sample cap")
        frames = sorted(set(row["frame"] for row in sources.values())); arithmetic = Directed(work)
        maxima = {"origin_m": 0.0, "box_vertex_m": 0.0, "site_m": 0.0, "rotation_rad": 0.0}
        worst = {}; observation_hash = hashlib.sha256(); source_hash = hashlib.sha256(); records = 0
        position_tolerance = case["options"]["position_tolerance_m"]; rotation_tolerance = case["options"]["rotation_tolerance_rad"]
        with gzip.open(output / "actual-native-observations.jsonl.gz", "wt", encoding="utf-8", compresslevel=6) as stream:
            for start in range(0, len(schedule), 128):
                block = schedule[start:start + 128]
                samples = rpc({"operation": "sample", "times": [float(t) for t, _ in block]})["samples"]
                require(len(samples) == len(block), "Native sample cardinality")
                for (clock, side), sample in zip(block, samples):
                    require(sample["time"] == float(clock) and set(sample["carriers"]) == set(sources), "Native sample clock/carriers")
                    poses = reference.recording_pose_enclosures(frames, clock, side)
                    details = []
                    for key, source in sources.items():
                        actual = sample["carriers"][key]; pose = poses[source["frame"]]
                        require(actual["element_id"] == source["element_id"], "Native sample occurrence identity")
                        matrix = actual["matrix"]; require(len(matrix) == 16 and all(math.isfinite(x) for x in matrix), "Finite actual native matrix")
                        ideal_matrix = arithmetic.matrix(pose.orientation); ideal_position = tuple(map(arithmetic.cell, pose.position))
                        origin = arithmetic.discrepancy(matrix, ideal_matrix, (0, 0, 0), ideal_position)
                        vertex = max(arithmetic.discrepancy(matrix, ideal_matrix, point, ideal_position, source["local_quantization"])
                                     for point in source["corners"])
                        site = max((arithmetic.discrepancy(matrix, ideal_matrix, point, ideal_position)
                                    for point in source["sites"]), default=0.0)
                        native_q = (actual["quaternion"][3], *actual["quaternion"][:3])
                        cells = tuple(map(arithmetic.cell, pose.orientation))
                        chord = min(arithmetic.upper(max(abs(sign * x - cell[0]), abs(sign * x - cell[1]))
                                                   for x, cell in zip(native_q, cells)) for sign in (-1, 1))
                        require(chord < .25, "Native quaternion leaves proved short distance")
                        rotation = math.nextafter(8 * chord, math.inf)
                        bounds = {"origin_m": origin, "box_vertex_m": vertex, "site_m": site, "rotation_rad": rotation}
                        require(max(origin, vertex, site) <= position_tolerance and rotation <= rotation_tolerance,
                            {"carrier": key, "time": str(clock), "side": side, "bounds": bounds})
                        for name, value in bounds.items():
                            if value > maxima[name]: maxima[name] = value; worst[name] = {"carrier": key, "time": str(clock), "side": side, "bound": value}
                        details.append({"carrier": key, "position_interval": ideal_position, "quaternion_interval": cells, "bounds": bounds})
                        records += 1
                    row = {"exact_source_time": str(clock), "side": side, "actual": sample}
                    encoded = json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n"
                    stream.write(encoded); observation_hash.update(encoded.encode())
                    source_hash.update((json.dumps(details, separators=(",", ":"), allow_nan=False) + "\n").encode())
                if start % 2048 == 0: print(json.dumps({"case": case["id"], "variant": variant, "samples_done": min(start + 128, len(schedule)), "samples_total": len(schedule)}), flush=True)
        captures = rpc({"operation": "captures", "times": [0, float(reference.end / 2), float(reference.end)]})["captures"]
        result.update(status="passed", artifact_sha256=digest, artifact_bytes=len(raw),
            native_identity=loaded["identity"], geometry=geometry_result,
            actual_retained_keys=len(clocks), dense_unique_clocks=dense_count, frozen_clock_sides=len(common),
            executed_clock_sides=len(schedule), carrier_observations=records,
            source_box_corners_per_sample=sum(len(x["corners"]) for x in sources.values()),
            named_sites_per_sample=sum(len(x["sites"]) for x in sources.values()),
            enclosed_source_vertices=sum(x["source_vertices"] for x in sources.values()),
            maxima=maxima, worst=worst, actual_observation_stream_sha256=observation_hash.hexdigest(),
            independent_interval_and_bound_stream_sha256=source_hash.hexdigest(), captures=captures,
            metrics={"position": "Outward L1 bound on actual native matrix versus independent ideal source matrix, every source box corner plus native local quantization; Euclidean error is no greater.",
                "rotation": "8 times the outward L1 distance of actual quaternion to the closer independent unit representative. For distance<1/4 this conservatively bounds physical rotation of the normalized quaternion."},
            offline_work=work.record())
    except Exception as error:
        result.update(status="failed", error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc(), offline_work=work.record())
    save(output / "result.json", result); print(json.dumps({"case": case["id"], "variant": variant, "status": result["status"], "error": result.get("error")}), flush=True)
    return result


def main():
    p = argparse.ArgumentParser(); p.add_argument("--checkout", type=Path, required=True)
    p.add_argument("--accepted", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--case", action="append"); p.add_argument("--variants", nargs="+", default=["original", "helpers"])
    p.add_argument("--node", default="/tmp/c088-verification-deps/node22/node_modules/node-linux-x64/bin/node")
    args = p.parse_args(); require(not args.output.exists(), "Fresh evidence directory required")
    args.output.mkdir(parents=True); sys.path.insert(0, str(args.checkout))
    frozen = args.checkout / "docs/language-design/torque-v0.1/freeze"
    cases = json.loads((frozen / "delivery-cases.json").read_text())["cases"]
    if args.case: cases = [case for case in cases if case["id"] in args.case]
    require(bool(cases), "At least one frozen case required")
    physics = {row["id"]: row for row in json.loads((frozen / "physics-cases.json").read_text())["cases"]}
    expectations = {row["case"]: row for row in json.loads((frozen / "state-expectations.json").read_text())["cases"]}
    before = {str(path.relative_to(args.checkout)): sha(path.read_bytes()) for path in sorted((args.checkout / "ontokin").glob("*.py"))}
    before.update({str(path.relative_to(args.checkout)): sha(path.read_bytes()) for path in (args.checkout / "tools/torque_destination.mjs", args.checkout / "tools/reach_destination.mjs")})
    save(args.output / "implementation.json", {"source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.checkout, text=True).strip(),
        "input_hashes": before, "harness_sha256": sha(Path(__file__).read_bytes()),
        "browser_harness_sha256": sha(Path(__file__).with_name("torque_browser_probe.mjs").read_bytes()),
        "started_utc": datetime.now(timezone.utc).isoformat()})
    with (args.output / "browser-stderr.log").open("w") as stderr:
        process = subprocess.Popen([args.node, str(Path(__file__).with_name("torque_browser_probe.mjs")),
            "--checkout", str(args.checkout)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True, bufsize=1)
        try:
            rows = [run_case(args, case, variant, process, frozen, physics, expectations)
                    for case in cases for variant in args.variants
                    if variant == "original" or case["helpers_true_repeat"]]
        finally:
            if process.poll() is None:
                process.stdin.write('{"operation":"close"}\n'); process.stdin.flush(); process.stdout.readline()
                process.stdin.close()
            process.wait(timeout=30)
    after = {name: sha((args.checkout / name).read_bytes()) for name in before}
    stable = before == after
    result = {"schema_version": "ontokin.c091-native-dense/1", "status": "passed" if stable and all(row["status"] == "passed" for row in rows) else "failed",
        "source_unchanged": stable, "cases": [{"case": row["case"], "variant": row["variant"], "status": row["status"]} for row in rows],
        "scope": "Actual named controlled .22 native destination and independent source dense evidence; frozen production allocation and complete supplied-byte certificate remain separate mandatory gates."}
    if not stable: result["changed_implementation_files"] = [name for name in before if before[name] != after[name]]
    save(args.output / "summary.json", result); print(json.dumps(result), flush=True)
    return int(result["status"] != "passed")


if __name__ == "__main__": raise SystemExit(main())
