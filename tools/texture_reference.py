"""Independent readers for C080 frozen source, PNG and supplied GLB bytes.

Only Python's standard library is imported. Production parsing, geometry,
mapping, PNG and export helpers never provide expected answers. This finite
reader derives logical corner candidates from the literal frozen fixtures;
it is not a replacement OntoKin compiler or a universal glTF validator.
"""
from __future__ import annotations

import base64
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct
import zlib

FREEZE_COMMIT = "4e5da7152e775b065299f2000ca80d51301bcd21"
FREEZE_SHA256 = "27705dc723d388fc92fe5fda58f97de75e492618ce1330dbfe51ae4ddeb08015"
CORRECTION_SHA256 = "326bc42a792e18d36452f04432a18cf40be4b011995f1372c2f58ba9daa0b755"
CORRECTION_COMMIT = "a9289559d47f988725b64a222eb0ff4c52c74c88"
TARGET = "ontokin.glb/0.13"
PROFILE = "textured-surfaces-0.1"
PROTOCOL = "ontokin.agent/0.13"
MAX_GLB_BYTES = 64 * 1024 * 1024
MAX_PNG_BYTES = 300000
SAMPLER = {"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071}


class ReferenceError(ValueError):
    def __init__(self, message, *, code="OKE-E-TEXTURE"):
        super().__init__(message)
        self.code = code


def require(condition, message, *, code="OKE-E-TEXTURE"):
    if not condition:
        raise ReferenceError(message, code=code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(data):
    return "sha256:" + sha(data)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def loads(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise ReferenceError("Nonfinite JSON value: " + value)
    def number(value):
        result = float(value)
        require(math.isfinite(result), "Nonfinite JSON numeric literal")
        return result
    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite, parse_float=number)


def ordinary_path(root, relative):
    require(type(relative) is str and relative and "\\" not in relative, "Invalid fixture/evidence path")
    parsed = PurePosixPath(relative)
    require(not parsed.is_absolute() and str(parsed) == relative and
            all(p not in ("", ".", "..") for p in relative.split("/")), "Unsafe fixture/evidence path")
    path = root.joinpath(*parsed.parts)
    require(not path.is_symlink() and path.is_file(), "Expected ordinary input file: " + relative)
    require(path.resolve().is_relative_to(root.resolve()), "Input resolves outside its root")
    return path


def load_fixtures(root, corrections=None):
    root = Path(root).resolve()
    raw = ordinary_path(root, "acceptance-freeze.json").read_bytes()
    require(sha(raw) == FREEZE_SHA256, "C080 fixture freeze differs from published identity")
    freeze = loads(raw)
    names = set()
    for item in freeze["files"]:
        require(item["path"] not in names, "Duplicate frozen path")
        names.add(item["path"])
        path = ordinary_path(root, item["path"])
        data = path.read_bytes()
        require(len(data) == item["size"] and sha(data) == item["sha256"], "Frozen bytes differ: " + item["path"])
        require(path.stat().st_mode & 0o777 == 0o644 and item["mode"] == "100644", "Frozen mode differs")
    expected = loads(ordinary_path(root, "expected.json").read_bytes())
    require(len(expected["cases"]) == freeze["case_count"] == 102, "Incomplete frozen source case set")
    require(dict(Counter(x["expected_outcome"] for x in expected["cases"])) == freeze["outcome_counts"], "Frozen outcome counts differ")
    require(len(names) == freeze["file_count"], "Frozen inventory count differs")
    result = {"root": root, "freeze": freeze, "expected": expected, "corpus_version": 1,
            "cases": {c["name"]: c for c in expected["cases"]},
            "transport": loads((root / "transport-cases.json").read_bytes())["cases"],
            "file_transport": loads((root / "file-transport-cases.json").read_bytes()),
            "workflows": loads((root / "workflow-controls.json").read_bytes())}
    if corrections is None:
        return result
    correction_root = Path(corrections).resolve()
    raw = ordinary_path(correction_root, "correction-freeze.json").read_bytes()
    require(sha(raw) == CORRECTION_SHA256, "Correction input manifest differs from explicit reviewed identity")
    correction = loads(raw)
    require(correction["original_input_commit"] == FREEZE_COMMIT and
            correction["original_manifest_sha256"] == FREEZE_SHA256, "Correction refers to another original freeze")
    names = set()
    for item in correction["files"]:
        require(item["path"] not in names, "Duplicate corrected input path")
        names.add(item["path"])
        path = ordinary_path(correction_root, item["path"])
        data = path.read_bytes()
        require(len(data) == item["size"] and sha(data) == item["sha256"] and
                path.stat().st_mode & 0o777 == 0o644, "Corrected input bytes/mode differ")
    require(len(names) == correction["file_count"], "Correction inventory incomplete")
    document = correction["erratum_document"]
    require(sha(ordinary_path(root.parent.parent, document["path"]).read_bytes()) == document["sha256"],
            "Correction's published explanation differs")
    active = loads(ordinary_path(correction_root, "active-corpus.json").read_bytes())
    require(sha((correction_root / "active-corpus.json").read_bytes()) == correction["active_corpus_sha256"] and
            active["corpus_version"] == 2 and active["case_count"] == 102, "Active correction corpus identity differs")
    require([(x["id"], x["name"]) for x in active["cases"]] == [(x["id"], x["name"]) for x in expected["cases"]],
            "Correction reordered, dropped or added source cases")
    revised, changed = [], []
    for selection in active["cases"]:
        original = result["cases"][selection["name"]]
        require(original["program_revision"] == selection["original_program_revision"], "Correction lost original case identity")
        if selection["origin"] == "original_published_freeze":
            revised.append(original)
            continue
        require(selection["origin"] == "input_erratum_001" and selection["name"] in
                ("inherited-loft", "older-user-function-png-asset"), "Unreviewed correction selection")
        case = loads(ordinary_path(correction_root, selection["expected_file"]).read_bytes())
        require(case["id"] == original["id"] and case["name"] == original["name"] and
                case["program_revision"] == selection["corrected_program_revision"] and
                case["erratum"]["original_program_revision"] == original["program_revision"], "Corrected case provenance differs")
        require(sha(ordinary_path(correction_root, selection["first_failure"]["receipt"]).read_bytes()) ==
                selection["first_failure"]["sha256"], "Original failed receipt was rewritten")
        case["_fixture_root"] = correction_root
        revised.append(case); changed.append(case["name"])
    require(len(changed) == 2 and len(revised) - len(changed) == 100, "Version 2 must be exactly 100 original plus two corrected cases")
    result["original_expected"] = expected
    result["expected"] = {**expected, "cases": revised}
    result["cases"] = {c["name"]: c for c in revised}
    result.update(corpus_version=2, correction_root=correction_root, correction=correction,
                  correction_manifest_sha256=sha(raw), correction_input_commit=CORRECTION_COMMIT,
                  active_corpus=active)
    return result


def case_root(fixtures, case):
    return case.get("_fixture_root", fixtures["root"])


def case_payload(fixtures, case, *, legacy=False):
    manifest = case["untextured_control"]["file_manifest"] if legacy else case["file_manifest"]
    return file_payload(case_root(fixtures, case), manifest, legacy=legacy)


def file_payload(root, manifest_name, *, legacy=False):
    manifest = loads(ordinary_path(root, manifest_name).read_bytes())
    expected_schema = "ontokin.files/0.1" if legacy else "ontokin.files/0.2"
    require(manifest.get("schema_version") == expected_schema, "Unexpected fixture manifest version")
    result = {"schema_version": "ontokin.bundle/0.1" if legacy else "ontokin.bundle/0.2",
              "entry": {"filename": manifest["entry"]["filename"],
                        "source": ordinary_path(root, manifest["entry"]["path"]).read_text(encoding="utf-8")},
              "modules": [{"package_id": unit["package_id"], "version": unit["version"],
                           "filename": unit["filename"],
                           "source": ordinary_path(root, unit["path"]).read_text(encoding="utf-8")}
                          for unit in manifest["modules"]]}
    if not legacy:
        result["assets"] = [{"asset_id": a["asset_id"], "sha256": a["sha256"], "media_type": a["media_type"],
                             "data_base64": base64.b64encode(ordinary_path(root, a["path"]).read_bytes()).decode("ascii")}
                            for a in manifest["assets"]]
    return result


def bundle_identity(payload):
    schema = payload["schema_version"]
    require(schema in ("ontokin.bundle/0.1", "ontokin.bundle/0.2"), "Unknown bundle identity domain")
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": payload["entry"]["filename"], "source_revision": digest(payload["entry"]["source"].encode("utf-8"))}]
    for unit in payload["modules"]:
        units.append({"source_id": "package:" + unit["package_id"] + "@" + unit["version"],
                      "package_id": unit["package_id"], "version": unit["version"], "filename": unit["filename"],
                      "source_revision": digest(unit["source"].encode("utf-8"))})
    manifest = {"schema_version": schema, "entry_source_id": "entry",
                "units": sorted(units, key=lambda x: x["source_id"])}
    if schema.endswith("/0.2"):
        assets = []
        ids = set()
        for item in payload["assets"]:
            require(item["asset_id"] not in ids, "Duplicate supplied asset ID")
            ids.add(item["asset_id"])
            raw = base64.b64decode(item["data_base64"], validate=True)
            require(base64.b64encode(raw).decode() == item["data_base64"], "Noncanonical asset base64")
            require(digest(raw) == item["sha256"], "Asset bytes differ from transport digest")
            assets.append({"asset_id": item["asset_id"], "media_type": item["media_type"],
                           "sha256": item["sha256"], "byte_length": len(raw)})
        manifest["assets"] = sorted(assets, key=lambda x: x["asset_id"])
    return digest(schema.encode() + b"\0" + canonical(manifest)), manifest


def decode_png(data):
    """Decode the adopted finite PNG subset with independent bounded loops."""
    def png_require(condition, message):
        require(condition, message, code="OKL-E-PNG")
    png_require(type(data) is bytes and 0 < len(data) <= MAX_PNG_BYTES, "PNG encoded-byte limit")
    png_require(data[:8] == b"\x89PNG\r\n\x1a\n", "PNG signature")
    position, chunks, payloads, phase = 8, [], [], "header"
    width = height = channels = None
    while position < len(data):
        png_require(position + 12 <= len(data), "Truncated PNG chunk")
        length = struct.unpack_from(">I", data, position)[0]
        kind = data[position + 4:position + 8]
        finish = position + 12 + length
        png_require(finish <= len(data), "PNG chunk exceeds file")
        payload = data[position + 8:position + 8 + length]
        crc = struct.unpack_from(">I", data, position + 8 + length)[0]
        png_require(zlib.crc32(kind + payload) & 0xffffffff == crc, "PNG CRC differs")
        chunks.append(kind.decode("ascii", "replace"))
        if kind == b"IHDR":
            png_require(phase == "header" and len(chunks) == 1 and length == 13, "PNG IHDR order/length")
            width, height, depth, color, method, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            png_require(1 <= width <= 256 and 1 <= height <= 256, "PNG dimensions")
            png_require(depth == 8 and color in (2, 6) and (method, filtering, interlace) == (0, 0, 0), "Unsupported PNG format")
            channels = 3 if color == 2 else 4
            phase = "image"
        elif kind == b"IDAT":
            png_require(phase == "image" and len(payloads) < 64, "PNG IDAT order/count")
            payloads.append(payload)
        elif kind == b"IEND":
            png_require(phase == "image" and payloads and length == 0 and finish == len(data), "PNG IEND order/content/tail")
            phase = "end"
        else:
            raise ReferenceError("Unsupported PNG chunk " + repr(kind), code="OKL-E-PNG")
        position = finish
    png_require(phase == "end" and width is not None, "Incomplete PNG")
    encoded = b"".join(payloads)
    stride = width * channels
    expected = height * (stride + 1)
    png_require(width * height * channels <= 262144 and expected <= 262400, "PNG decoded-byte bound")
    try:
        decoder = zlib.decompressobj()
        filtered = decoder.decompress(encoded, expected + 1)
    except zlib.error as error:
        raise ReferenceError("Invalid PNG zlib stream: " + str(error), code="OKL-E-PNG") from error
    png_require(len(filtered) == expected and decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
                "PNG output length or compressed-stream termination differs")
    pixels, filters = bytearray(width * height * channels), []
    for y in range(height):
        method = filtered[y * (stride + 1)]
        png_require(0 <= method <= 4, "Unsupported PNG row filter")
        filters.append(method)
        start = y * stride
        for x in range(stride):
            left = pixels[start + x - channels] if x >= channels else 0
            above = pixels[start - stride + x] if y else 0
            diagonal = pixels[start - stride + x - channels] if y and x >= channels else 0
            if method == 0:
                prediction = 0
            elif method == 1:
                prediction = left
            elif method == 2:
                prediction = above
            elif method == 3:
                prediction = (left + above) // 2
            else:
                projected = left + above - diagonal
                prediction = min(enumerate((left, above, diagonal)), key=lambda pair: (abs(projected - pair[1]), pair[0]))[1]
            pixels[start + x] = (filtered[y * (stride + 1) + 1 + x] + prediction) & 255
    if channels == 4:
        png_require(all(pixels[i] == 255 for i in range(3, len(pixels), 4)), "Nonopaque PNG alpha")
    return {"width": width, "height": height, "channels": channels, "pixels": bytes(pixels),
            "row_filters": filters, "chunks": chunks, "encoded_sha256": digest(data),
            "decoded_sha256": digest(pixels), "encoded_bytes": len(data), "decoded_bytes": len(pixels)}


class GLB:
    def __init__(self, data, *, target=TARGET):
        require(type(data) is bytes and 28 <= len(data) <= MAX_GLB_BYTES, "GLB size")
        require(struct.unpack_from("<III", data) == (0x46546c67, 2, len(data)), "GLB header")
        json_size, kind = struct.unpack_from("<II", data, 12)
        require(kind == 0x4e4f534a and json_size % 4 == 0 and 20 + json_size + 8 <= len(data), "GLB JSON chunk")
        self.document = loads(data[20:20 + json_size])
        start = 20 + json_size
        binary_size, kind = struct.unpack_from("<II", data, start)
        require(kind == 0x004e4942 and binary_size % 4 == 0 and start + 8 + binary_size == len(data), "GLB BIN chunk")
        self.binary = data[start + 8:]
        self.data = data
        buffers = self.document["buffers"]
        require(len(buffers) == 1 and "uri" not in buffers[0], "GLB must embed one buffer")
        size = buffers[0]["byteLength"]
        require(type(size) is int and 0 <= binary_size - size <= 3 and not any(self.binary[size:]), "GLB buffer length/padding")
        require(self.document.get("asset", {}).get("version") == "2.0", "Unexpected glTF version")
        meta = self.document.get("extras", {}).get("ontokin", {})
        require(meta.get("target_contract") == target, "Wrong destination contract")
        if target == TARGET:
            require(meta.get("profile") == PROFILE and meta.get("schema_version") == "0.13", "Wrong source profile/version")
        for node in self.document.get("nodes", []):
            require(node.get("scale", [1, 1, 1]) == [1, 1, 1] and "matrix" not in node and not node.get("children"), "Unexpected carrier deformation/hierarchy")

    def reference(self, table, index):
        values = self.document.get(table, [])
        require(type(index) is int and 0 <= index < len(values), "Invalid " + table + " reference")
        return values[index]

    def view_bytes(self, index):
        view = self.reference("bufferViews", index)
        start, size = view.get("byteOffset", 0), view["byteLength"]
        require(view.get("buffer", 0) == 0 and type(start) is int and type(size) is int and start >= 0 and size >= 0,
                "Invalid buffer view shape")
        require(start + size <= self.document["buffers"][0]["byteLength"], "Buffer view overruns declared buffer")
        return self.binary[start:start + size]

    def accessor_parts(self, index):
        item = self.reference("accessors", index)
        require("sparse" not in item and not item.get("normalized", False), "Unsupported adapter accessor representation")
        require(item["componentType"] in (5123, 5125, 5126), "Unsupported component type")
        require(item["type"] in ("SCALAR", "VEC2", "VEC3", "VEC4"), "Unsupported accessor vector type")
        fmt, width = {5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}[item["componentType"]]
        components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[item["type"]]
        view = self.reference("bufferViews", item["bufferView"])
        raw = self.view_bytes(item["bufferView"])
        offset, count = item.get("byteOffset", 0), item["count"]
        stride = view.get("byteStride", width * components)
        require(all(type(x) is int and x >= 0 for x in (offset, count, stride)) and count > 0,
                "Invalid accessor bounds")
        require(stride >= width * components and stride % width == 0 and
                (view.get("byteOffset", 0) + offset) % width == 0, "Invalid accessor alignment/stride")
        require(offset + (count - 1) * stride + width * components <= len(raw), "Accessor overruns view")
        rows = [raw[offset + i * stride:offset + i * stride + width * components] for i in range(count)]
        return item, fmt, components, rows

    def accessor(self, index):
        item, fmt, components, raw = self.accessor_parts(index)
        values = [struct.unpack("<" + fmt * components, row) for row in raw]
        require(all(math.isfinite(x) for row in values for x in row), "Nonfinite supplied accessor")
        return [row[0] for row in values] if components == 1 else values

    def accessor_bytes(self, index):
        return b"".join(self.accessor_parts(index)[3])

    def objects(self):
        result = {}
        for index, node in enumerate(self.document["nodes"]):
            meta = node.get("extras", {}).get("ontokin", {})
            require(meta.get("kind") == "object" and type(meta.get("path")) is str, "Unknown carrier identity")
            require(meta["path"] not in result, "Duplicate carrier identity")
            result[meta["path"]] = index
        return result

    def primitives(self, path):
        node = self.document["nodes"][self.objects()[path]]
        if "mesh" not in node:
            return []
        return self.reference("meshes", node["mesh"])["primitives"]

    def geometry_streams(self):
        result = {}
        for path in self.objects():
            seen = set()
            for primitive in self.primitives(path):
                region = primitive.get("extras", {}).get("ontokin", {}).get("region_key")
                require(type(region) is str and region not in seen and primitive.get("mode", 4) == 4, "Invalid regional primitive")
                seen.add(region)
                for role in ("POSITION", "NORMAL"):
                    index = primitive["attributes"][role]
                    item = self.reference("accessors", index)
                    require(item["componentType"] == 5126 and item["type"] == "VEC3", "Invalid native vector stream")
                    result[(path, region, role)] = self.accessor_bytes(index)
                result[(path, region, "indices")] = self.accessor_bytes(primitive["indices"])
        return result

    def animation_streams(self):
        result = {}
        objects = {index: path for path, index in self.objects().items()}
        require(len(self.document.get("animations", [])) == 1, "Expected one recorded animation")
        animation = self.document["animations"][0]
        for channel in animation["channels"]:
            target = channel["target"]
            require(target["node"] in objects and target["path"] in ("translation", "rotation"), "Unexpected animation target")
            key = (objects[target["node"]], target["path"])
            require(key not in result, "Duplicate animation target")
            i = channel["sampler"]
            require(type(i) is int and 0 <= i < len(animation["samplers"]), "Invalid animation sampler")
            sampler = animation["samplers"][i]
            require(sampler.get("interpolation", "LINEAR") == "LINEAR", "Unexpected recorded interpolation")
            result[key] = (self.accessor_bytes(sampler["input"]), self.accessor_bytes(sampler["output"]))
        return result

    def pose(self, path, time):
        index = self.objects()[path]
        node = self.document["nodes"][index]
        result = {"translation": node.get("translation", [0, 0, 0]), "rotation": node.get("rotation", [0, 0, 0, 1])}
        animation = self.document["animations"][0]
        for channel in animation["channels"]:
            if channel["target"]["node"] != index:
                continue
            sampler = animation["samplers"][channel["sampler"]]
            times, rows = self.accessor(sampler["input"]), self.accessor(sampler["output"])
            require(len(times) == len(rows) and all(b > a for a, b in zip(times, times[1:])), "Invalid recorded clock order")
            upper = next((i for i, t in enumerate(times) if t >= time), len(times) - 1)
            if upper == 0 or times[upper] == time:
                value = rows[upper]
            else:
                fraction = (time - times[upper - 1]) / (times[upper] - times[upper - 1])
                value = [a + (b - a) * fraction for a, b in zip(rows[upper - 1], rows[upper])]
            result[channel["target"]["path"]] = value
        return result


def f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def exact_uv(point, mapping):
    delta = [Fraction(float(x)) - Fraction(float(o)) for x, o in zip(point, mapping["origin_m"])]
    values = []
    for row, offset in zip((mapping["u_per_m"], mapping["v_per_m"]), mapping["offset"]):
        exact = sum((Fraction(float(a)) * b for a, b in zip(row, delta)), Fraction(float(offset)))
        value = float(exact)
        require(math.isfinite(value) and abs(value) <= 4096, "Independent referenced UV bound")
        values.append(f32(value))
    return tuple(values)


def source_calls(text, name):
    """Read balanced literal constructor arguments in the pinned fixture subset."""
    found = []
    for match in re.finditer(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"\s*\(", text):
        start, depth, quoted, escaped, segments, segment = match.end(), 1, False, False, [], match.end()
        for index in range(start, len(text)):
            char = text[index]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char in "({[":
                depth += 1
            elif char in ")}]":
                depth -= 1
                if depth == 0:
                    segments.append(text[segment:index].strip())
                    found.append(segments)
                    break
            elif char == "," and depth == 1:
                segments.append(text[segment:index].strip()); segment = index + 1
        else:
            raise ReferenceError("Unbalanced frozen constructor")
    return found


def quantity(text, unit="m"):
    match = re.fullmatch(r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\[" + re.escape(unit) + r"\]", text.strip())
    require(match is not None, "Expected literal frozen quantity: " + text)
    return float(match.group(1))


def raw_points(fixtures, case):
    """Finite source corner candidates, independent of produced triangulation."""
    payload = case_payload(fixtures, case)
    texts = [payload["entry"]["source"], *[unit["source"] for unit in payload["modules"]]]
    text = "\n".join(texts)
    planar = [tuple(quantity(x) for x in args) for args in source_calls(text, "planar_point")]
    family = case["family"]
    if family == "pockets":
        require(len(planar) == 8, "Unexpected frozen pocket boundary count")
        return [(x, y, z) for x, y in planar[:4] for z in (0., 2.)] + [(x, y, z) for x, y in planar[4:] for z in (1.5, 2.)]
    if family in ("extrusion", "holes"):
        require(planar, "Missing frozen planar vertices")
        return sorted(set((x, y, z) for x, y in planar for z in (0., .25)))
    if family in ("ring_loft", "framed_loft"):
        require(planar, "Missing frozen loft vertices")
        return sorted(set((x, y, z) for x, y in planar for z in (0., 1.)))
    if family == "loft":
        facets = case.get("loft_facets", 4)
        calls = source_calls(text, "loft")
        require(len(calls) == 1 and int(calls[0][2]) == facets, "Frozen loft facet literal differs from selected input version")
        points = []
        for z in (0., 1.):
            points.append((0., 0., z))
            points.extend((math.cos(2 * math.pi * i / facets), math.sin(2 * math.pi * i / facets), z) for i in range(facets))
        return points
    raise ReferenceError("Unknown frozen fixture geometry family")


def expected_occurrences(case):
    if "occurrences" not in case:
        return {"shape": {"origin": [0, 0, 0], "velocity": [0, .5, 0],
                          "bindings": {b["region"]: b for b in case.get("texture_bindings", [])}}}
    result = {}
    for occurrence in case["occurrences"]:
        if "object_key" in occurrence:
            path = occurrence["object_key"]
        else:
            path = occurrence["root_object_key"] + "." + occurrence["part_slot_key"] + "[" + json.dumps(occurrence["instance_key"]) + "]"
        result[path] = {"origin": occurrence["initial_world_position_m"], "velocity": occurrence["velocity_m_per_s"],
                        "bindings": {occurrence["texture_region"]: {"asset_id": occurrence["asset_id"], "mapping": occurrence["mapping"]}}}
    if case["name"].startswith("generated"):
        result["array"] = {"origin": [-5, 0, 0], "velocity": [0, .5, 0], "bindings": {}, "empty": True}
    return result


def check_geometry(decoded, path, case, lookup):
    """Finite analytic solids and welded oriented edges, from frozen recipes."""
    vertices, edges, volume6, area, triangles = set(), Counter(), 0., 0., 0
    for primitive in decoded.primitives(path):
        points = decoded.accessor(primitive["attributes"]["POSITION"])
        normals = decoded.accessor(primitive["attributes"]["NORMAL"])
        indices = decoded.accessor(primitive["indices"])
        require(len(points) == len(normals) and len(indices) % 3 == 0, "Geometry stream cardinality")
        for start in range(0, len(indices), 3):
            ids = indices[start:start + 3]
            require(all(type(i) is int and 0 <= i < len(points) for i in ids), "Native triangle index bounds")
            a, b, c = (tuple(points[i]) for i in ids)
            require(all(p in lookup for p in (a, b, c)), "Native corner absent from independent source identities")
            vertices.update((a, b, c))
            ab, ac = [y - x for x, y in zip(a, b)], [y - x for x, y in zip(a, c)]
            cross = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]]
            length = math.hypot(*cross)
            require(length > 0 and math.isfinite(length), "Degenerate supplied native triangle")
            for i in ids:
                normal = normals[i]
                require(abs(math.hypot(*normal) - 1) <= 1e-5 and
                        sum(x * y for x, y in zip(cross, normal)) / length >= 1 - 1e-5,
                        "Normal does not agree with outward supplied triangle")
            area += length / 2
            volume6 += sum(a[i] * (b[(i + 1) % 3] * c[(i + 2) % 3] - b[(i + 2) % 3] * c[(i + 1) % 3]) for i in range(3))
            for first, second in ((a, b), (b, c), (c, a)):
                edges[(first, second)] += 1
            triangles += 1
    require(triangles > 0, "Expected nonempty native solid")
    require(all(count == 1 and edges.get((second, first)) == 1 for (first, second), count in edges.items()),
            "Welded native surface is not a closed consistently oriented two-manifold")
    family = case["family"]
    if family == "pockets":
        expected_volume, expected_area, expected_triangles, expected_vertices = 15., 43., 28, 16
    elif family == "holes":
        expected_volume, expected_area, expected_triangles, expected_vertices = 1.5, 16.5, 32, 16
    elif family in ("ring_loft", "framed_loft"):
        expected_volume, expected_area, expected_triangles, expected_vertices = 8., 28., 12, 8
    elif family == "loft":
        n = case.get("loft_facets", 4)
        expected_volume = n * math.sin(2 * math.pi / n) / 2
        expected_area = n * math.sin(2 * math.pi / n) + 2 * n * math.sin(math.pi / n)
        expected_triangles, expected_vertices = 4 * n, 2 * n + 2
    elif family == "extrusion":
        width = 3.9 if case["name"] == "exact-rational-uv" else 4.
        expected_volume, expected_area = width * 2 * .25, 2 * (width * 2 + width * .25 + 2 * .25)
        expected_triangles, expected_vertices = 12, 8
    else:
        raise ReferenceError("Unknown analytic source solid")
    volume = volume6 / 6
    require(triangles == expected_triangles and len(vertices) == expected_vertices, "Analytic source triangle/corner count differs")
    require(abs(volume - expected_volume) <= 1e-5 * max(1, expected_volume) and
            abs(area - expected_area) <= 1e-5 * max(1, expected_area), "Analytic source volume/area differs")
    return {"triangles": triangles, "logical_vertices": len(vertices), "volume_m3": volume,
            "surface_area_m2": area, "closed_oriented_edges": len(edges) // 2}


def check_artifact(data, case, fixtures, control_data):
    """Validate exact appearance plus unchanged actual .12 geometry/motion streams."""
    decoded = GLB(data)
    control = GLB(control_data, target="ontokin.glb/0.12")
    payload = case_payload(fixtures, case)
    revision, manifest = bundle_identity(payload)
    require(revision == case["program_revision"], "Independent fixture revision differs")
    require(decoded.document["extras"]["ontokin"]["program"]["revision"] == revision, "GLB source/asset revision differs")
    wanted = expected_occurrences(case)
    require(set(decoded.objects()) == set(control.objects()) == set(wanted), "Carrier inventory differs from source")
    geometry = decoded.geometry_streams()
    require(geometry == control.geometry_streams(), "Position/normal/index streams differ from actual .12 source control")
    require(decoded.animation_streams() == control.animation_streams(), "Animation streams differ from actual .12 source control")
    assets = {a["asset_id"]: base64.b64decode(a["data_base64"], validate=True) for a in payload["assets"]}
    candidates = raw_points(fixtures, case)
    if case["name"] == "placed-mapping":
        lookup = {tuple(map(f32, (p[2] + 2, p[0] - 3, p[1] + 1))): p for p in candidates}
    else:
        lookup = {tuple(map(f32, p)): p for p in candidates}
    used_assets, image_assignments, used_images, used_textures, used_samplers = set(), {}, set(), set(), set()
    observations, region_reports, geometry_reports, uv_rows = [], [], {}, 0
    original_end = max((v.get("byteOffset", 0) + v["byteLength"] for v in control.document["bufferViews"]), default=0)
    for path, expected in wanted.items():
        if expected.get("empty"):
            require(not decoded.primitives(path), "Declared empty carrier gained geometry")
        else:
            geometry_reports[path] = check_geometry(decoded, path, case, lookup)
        for t in (0., .05, .1, .15, .2, .25, .3, .35, .4, .45, .5, .55, .6, .65, .7, .75, .8, .85, .9, .95, 1.):
            actual = decoded.pose(path, t)
            position = [a + t * b for a, b in zip(expected["origin"], expected["velocity"])]
            require(all(abs(a - b) <= .001 for a, b in zip(actual["translation"], position)), "Recorded translation differs")
            rotation = actual["rotation"]
            require(len(rotation) == 4 and abs(math.hypot(*rotation) - 1) <= 1e-5 and
                    2 * math.atan2(math.hypot(*rotation[:3]), abs(rotation[3])) <= .001, "Recorded rotation differs")
            observations.append({"path": path, "time_seconds": t, "position": actual["translation"], "rotation_xyzw": rotation})
        for primitive in decoded.primitives(path):
            region = primitive["extras"]["ontokin"]["region_key"]
            positions = decoded.accessor(primitive["attributes"]["POSITION"])
            indices = decoded.accessor(primitive["indices"])
            require(len(indices) % 3 == 0 and all(type(i) is int and 0 <= i < len(positions) for i in indices), "Invalid triangle index")
            material = decoded.reference("materials", primitive["material"])
            identity = material.get("extras", {}).get("ontokin", {})
            require(identity.get("source_region_key") == region and identity.get("occurrence_path") == path and
                    identity.get("program_revision") == revision, "Material provenance differs")
            pbr = material.get("pbrMetallicRoughness", {})
            factors = case["expected_material_factors"]
            require(all(pbr.get(key) == value for key, value in factors.items()), "Authored PBR factors differ")
            binding = expected["bindings"].get(region)
            if binding is None:
                require("baseColorTexture" not in pbr and "TEXCOORD_0" not in primitive["attributes"], "Untextured region gained appearance")
                continue
            require(material.get("alphaMode", "OPAQUE") == "OPAQUE" and material.get("doubleSided", False) is False,
                    "Textured opacity/back-face behavior differs")
            require("baseColorTexture" in pbr and "TEXCOORD_0" in primitive["attributes"], "Missing actual texture binding")
            texture_info = pbr["baseColorTexture"]
            require(texture_info.get("texCoord", 0) == 0 and "extensions" not in texture_info, "Wrong UV set or implicit transform")
            tex_index = texture_info["index"]
            texture = decoded.reference("textures", tex_index)
            image_index, sampler_index = texture["source"], texture["sampler"]
            image = decoded.reference("images", image_index)
            sampler = decoded.reference("samplers", sampler_index)
            require(all(sampler.get(key) == value for key, value in SAMPLER.items()), "Sampler differs")
            require(image.get("mimeType") == "image/png" and "uri" not in image and "bufferView" in image,
                    "Image is not an embedded original PNG")
            image_view = decoded.reference("bufferViews", image["bufferView"])
            require(image_view.get("byteOffset", 0) >= original_end and "target" not in image_view,
                    "Image overlaps existing streams or declares vertex/index use")
            image_bytes = decoded.view_bytes(image["bufferView"])
            asset_id = binding["asset_id"]
            require(asset_id in assets and image_bytes == assets[asset_id], "Embedded image bytes differ from declared source asset")
            require(image.get("name") == asset_id and image.get("extras") == {"ontokin": {
                "asset_id": asset_id, "sha256": digest(assets[asset_id]),
                "byte_length": len(assets[asset_id]), "program_revision": revision}},
                "Embedded image provenance differs from the selected source attachment")
            decode_png(image_bytes)
            if asset_id in image_assignments:
                require(image_assignments[asset_id] == image_index, "Same asset ID emitted more than once")
            image_assignments[asset_id] = image_index
            used_assets.add(asset_id); used_images.add(image_index); used_textures.add(tex_index); used_samplers.add(sampler_index)
            uv_index = primitive["attributes"]["TEXCOORD_0"]
            uv_accessor = decoded.reference("accessors", uv_index)
            require(uv_accessor["componentType"] == 5126 and uv_accessor["type"] == "VEC2" and
                    uv_accessor["count"] == len(positions), "Texture accessor type/count differs")
            uv_view = decoded.reference("bufferViews", uv_accessor["bufferView"])
            require(uv_view.get("byteOffset", 0) >= original_end, "UV stream precedes original stream end")
            uvs = decoded.accessor(uv_index)
            selected = set(indices)
            raw_uv = decoded.accessor_parts(uv_index)[3]
            for i, (position, uv) in enumerate(zip(positions, uvs)):
                if i not in selected:
                    require(raw_uv[i] == b"\0" * 8, "Unreferenced regional UV is not positive zero")
                    continue
                require(tuple(position) in lookup, "Supplied corner is absent from independent raw source identities")
                expected_uv = exact_uv(lookup[tuple(position)], binding["mapping"])
                require(struct.pack("<2f", *uv) == struct.pack("<2f", *expected_uv), "Actual UV differs from exact authored affine map")
                uv_rows += 1
            region_reports.append({"path": path, "region": region, "asset_id": asset_id,
                                   "png_sha256": digest(image_bytes), "uv_rows": len(selected),
                                   "uv_accessor_sha256": digest(decoded.accessor_bytes(uv_index))})
    require(len(image_assignments) == len(set(image_assignments.values())), "Distinct asset IDs merged into one image")
    require([item.get("name") for item in decoded.document.get("images", [])] == sorted(used_assets),
            "Embedded image identities are not in canonical asset-ID order")
    require(used_images == set(range(len(decoded.document.get("images", [])))) and
            used_textures == set(range(len(decoded.document.get("textures", [])))) and
            used_samplers == set(range(len(decoded.document.get("samplers", [])))), "Dangling texture resources")
    return {"status": "passed", "case": case["name"], "program_revision": revision,
            "glb_sha256": sha(data), "control_sha256": sha(control_data), "uv_rows_checked": uv_rows,
            "regions": region_reports, "embedded_asset_ids": sorted(used_assets),
            "analytic_geometry": geometry_reports,
            "geometry_streams_equal": True, "animation_streams_equal": True,
            "observations": observations,
            "scope": "Exact frozen PNG/UV/reference/sampler/PBR checks, finite raw corner identity checks, byte preservation against actual .12 controls, and 21-time recorded poses. Complete inherited geometric contact proofs remain separate."}


def repack_glb(document, binary):
    """Encode adversarial supplied bytes; never a production artifact builder."""
    document = loads(canonical(document))
    document["buffers"][0]["byteLength"] = len(binary)
    text = canonical(document)
    text += b" " * (-len(text) % 4)
    padded = binary + b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(padded)
    return struct.pack("<III", 0x46546c67, 2, total) + struct.pack("<II", len(text), 0x4e4f534a) + text + struct.pack("<II", len(padded), 0x004e4942) + padded
