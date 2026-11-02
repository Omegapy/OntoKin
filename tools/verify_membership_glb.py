#!/usr/bin/env python3
"""Independent C088 complete GLB comparison and thirteen supplied-byte adversaries.

Only frozen original sources and expectations supply answers. The three pinned
C087 reader modules provide byte/PNG/delimiter utilities; no product module is
imported. Every metadata container and lineage array survives normalization.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import copy
import hashlib
import importlib
from itertools import product
import json
import math
from pathlib import Path
import platform
import re
import struct
import subprocess
import sys
import traceback


SPEC_SHA = "e9a55ae015b1892453217deea38ea85e269e2551608ab5ed7aa7d21bea337d0b"
INPUT_SHA = "7ef04b64d93a45a4fac681b632a9c02bdb936a34d4565faa44452ce27c07aca1"
C087 = "a969a668f9fdf021793366ac5f5b9a8f9cd0fa56"
READER_HASHES = {
    "tools/texture_reference.py": "71cb727ef8a9700f288b1ceb04e65c563302278917bd6536f1bc03616d2ada50",
    "tools/keyed_zip_reference.py": "d87fb03569f0bb48b8b2ae22b5d41ea6693ac43e48b67a9923b393264c098329",
    "tools/string_concat_source_reference.py": "ca60431dff92f6ce9453c9266c20eed5a59886049cf1c7d1b1da5fa58f989a63",
}
PANEL = "package:fixture.membership-panels@1.0.0"
CATALOG = "package:fixture.membership-catalog@1.0.0"
TARGETS = {"source": "ontokin.glb/0.21", "reduction": "ontokin.glb/0.20", "literal": "ontokin.glb/0.20"}
PROFILES = {"source": "keyed-membership-0.1", "reduction": "string-concat-0.1", "literal": "string-concat-0.1"}
GLB_HOSTILES = (
    "glb-position", "glb-normal", "glb-index", "glb-material", "glb-uv", "glb-image",
    "glb-node-key", "glb-motion", "glb-profile", "glb-source-location", "glb-source-pin",
    "glb-lineage", "glb-framing",
)
T = Z = S = None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def require(condition, message):
    if not condition:
        raise T.ReferenceError(message) if T is not None else AssertionError(message)


def git_identity(root):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root).decode().strip()
    return {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
            "status": git("status", "--porcelain")}


def import_references(root):
    global T, Z, S
    identity = git_identity(root)
    require(identity["commit"] == C087 and not identity["status"], "Reference utility checkout must be exact clean C087")
    rows = []
    for rel, expected in READER_HASHES.items():
        raw = (root / rel).read_bytes()
        require(sha(raw) == expected, "Pinned independent utility differs: " + rel)
        rows.append({"path": rel, "bytes": len(raw), "sha256": sha(raw)})
    sys.path.insert(0, str(root))
    T = importlib.import_module("tools.texture_reference")
    Z = importlib.import_module("tools.keyed_zip_reference")
    S = importlib.import_module("tools.string_concat_source_reference")
    require(not any(n == "ontokin" or n.startswith("ontokin.") for n in sys.modules), "Product import is prohibited")
    return {"checkout": str(root), **identity, "modules": rows}


def load_frozen(root):
    raw = (root / "INPUTS-MANIFEST.json").read_bytes()
    require(sha(raw) == INPUT_SHA, "Exact adopted input-manifest identity")
    manifest = T.loads(raw)
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "INPUTS-MANIFEST.json":
            continue
        data = path.read_bytes()
        rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(data),
                     "mode": "100755" if path.stat().st_mode & 0o111 else "100644", "sha256": sha(data)})
    require(rows == manifest["files"] and sha(canonical(rows)) == manifest["inventory_sha256"],
            "Complete frozen bytes/modes/inventory")
    delivery = T.loads((root / "agent/delivery-expected.json").read_bytes())
    expected = T.loads((root / "agent/expected.json").read_bytes())
    hostiles = T.loads((root / "hostile-expected.json").read_bytes())
    for document in (delivery, hostiles):
        require(document["specification_sha256"] == SPEC_SHA and document["candidate_observations_used"] is False,
                "Frozen independent authority")
    require(expected["candidate_observations_used"] is False, "Frozen representative answers precede candidate observations")
    require(delivery["native_role_count"] == len(delivery["native_roles"]) == 21, "Exact native role inventory")
    require({r["id"] for r in hostiles["mutations"] if r["id"].startswith("glb-")} == set(GLB_HOSTILES),
            "Exact thirteen GLB hostile classes")
    cases = {case["id"]: case for case in expected["cases"]}
    require(len(cases) == 24, "Exact representative case inventory")
    return {"root": root, "manifest": manifest, "delivery": delivery, "expected": expected,
            "cases": cases, "input_manifest_sha256": sha(raw),
            "input_inventory_sha256": manifest["inventory_sha256"]}


def source_location(units, source_id, start, end):
    unit = units[source_id]
    return {"source_id": source_id, "source_revision": T.digest(unit["source"].encode()),
            "filename": unit["filename"], "start_byte": start, "end_byte": end}


def declaration(units, source_id, kind, name):
    raw = units[source_id]["source"].encode()
    pattern = rb"(?:public\s+)?" + kind.encode() + rb"\s+" + name.encode() + rb'\s*@\s*"([^\"]+)"'
    matches = list(re.finditer(pattern, raw))
    require(len(matches) == 1, "Unique original declaration: " + name)
    match = matches[0]
    tokens = S._source_tokens(raw[match.start():])
    opening = next(i for i, token in enumerate(tokens) if token[0] == b"{")
    closing = S._closing_delimiter(tokens, opening)
    return source_location(units, source_id, match.start(), match.start() + tokens[closing][2]), match[1].decode()


def call_location(units, source_id, name):
    tokens = S._source_tokens(units[source_id]["source"].encode())
    starts = [i for i, token in enumerate(tokens[:-1]) if token[0] == name.encode() and tokens[i + 1][0] == b"("]
    require(len(starts) == 1, "Unique original call: " + name)
    start = starts[0]
    end = S._closing_delimiter(tokens, start + 1)
    return source_location(units, source_id, tokens[start][1], tokens[end][2])


def enriched(value, units):
    return {**value, "filename": units[value["source_id"]]["filename"]}


def original_sources(case, frozen):
    payload = T.file_payload(frozen["root"] / "agent", case["files"])
    revision, manifest = T.bundle_identity(payload)
    require((revision, manifest) == (case["program_revision"], case["canonical_manifest"]),
            "Independent frozen source canonical identity: " + case["id"])
    units = S.source_units(payload)
    require(sha(units["entry"]["source"].encode()) == case["source_sha256"], "Frozen entry bytes")
    group, group_key = declaration(units, PANEL, "class", "PanelGroup")
    panel, panel_key = declaration(units, PANEL, "class", "Panel")
    parts, parts_key = declaration(units, PANEL, "parts", "panels")
    defaults, _ = declaration(units, CATALOG, "fn", "defaults")
    require((group_key, panel_key, parts_key) == ("panel-group", "panel", "panels"), "Original definition keys")
    part_bytes = S.check_location(parts, units)
    match = re.search(rb"\bin\s+(self\.names)\s*\{", part_bytes)
    require(match is not None, "Original generated input is exactly self.names")
    input_span = source_location(units, PANEL, parts["start_byte"] + match.start(1),
                                 parts["start_byte"] + match.end(1))
    entries = {}
    for entry in S.original_keyed_entries({CATALOG: units[CATALOG]}).values():
        span = entry["location"]
        if defaults["start_byte"] < span["start_byte"] < span["end_byte"] < defaults["end_byte"]:
            require(entry["key"] not in entries, "Unique original default key")
            entries[entry["key"]] = enriched(span, units)
    require(set(entries) == {"left", "middle", "right"}, "Exact original catalog entries")
    maps = S.intrinsic_locations({PANEL: units[PANEL]}, b"map_keyed")
    chosen = []
    for loc in maps:
        shape = S.intrinsic_source_shape(loc, units, b"map_keyed")
        if S.check_location(shape["parts"]["body"], units) == b"catalog_key":
            chosen.append((loc, shape))
    require(len(chosen) == 1, "Unique original names transformation")
    loc, shape = chosen[0]
    require(shape["element_type"] == "String" and S.check_location(shape["parts"]["input"], units) == b"self.dimensions",
            "Original names map type/input roles")
    transform = {"expression": enriched(loc, units), "body": enriched(shape["parts"]["body"], units),
                 "input": enriched(shape["parts"]["input"], units),
                 "input_element_type": "Length", "output_element_type": "String"}
    rekeys = S.intrinsic_locations({PANEL: units[PANEL]}, b"rekey_keyed")
    require(len(rekeys) == 1, "Unique original names rekey")
    # The generic byte delimiter reader has no declaring-version policy. The
    # frozen header/profile above and role checks below supply .21 admission.
    shape = S.intrinsic_source_shape(rekeys[0], units, b"rekey_keyed")
    require(shape["element_type"] == "String" and S.check_location(shape["parts"]["input"], units) == b"self.original_names"
            and S.check_location(shape["parts"]["body"], units) == b"self.prefix+old_key", "Original rekey roles")
    rekey = {"expression": enriched(rekeys[0], units), "input": enriched(shape["parts"]["input"], units),
             "body": enriched(shape["parts"]["body"], units), "element_type": "String",
             "old_key": None, "new_key": None, "input_entry": None}
    declared = {name: declaration(units, "entry", "object", name)[0] for name in ("first", "sibling", "marker")}
    return {"payload": payload, "units": units, "revision": revision, "manifest": manifest,
            "group": group, "panel": panel, "parts": parts, "input": input_span,
            "entries": entries, "transform": transform, "rekey": rekey, "declarations": declared,
            "group_id": ["package", "fixture.membership-panels", "membership-panels", "definitions", "panel-group"],
            "panel_id": ["package", "fixture.membership-panels", "membership-panels", "definitions", "panel"],
            "panel_geometry": call_location(units, PANEL, "extrude"),
            "marker_geometry": call_location(units, "entry", "box"),
            "texture_binding": call_location(units, PANEL, "texture_binding"),
            "planar_uv": call_location(units, PANEL, "planar_uv")}


def expected_projection(case, sources):
    occurrences, collections = {}, {}
    paths = ["first", "sibling", *case["geometry"]]
    require(len(paths) == 9 and len(set(paths)) == 9, "Exact nine authored occurrences")
    for path in paths:
        generated = ".panels[" in path
        owner = path.split(".", 1)[0] if generated else None
        root = owner if generated else path
        key = json.loads(path.split("[", 1)[1][:-1]) if generated else None
        definition = sources["panel_id"] if generated else sources["group_id"] if path != "marker" else ["@system", "Object"]
        steps = [{"kind": "member", "value": root}]
        if generated:
            steps += [{"kind": "member", "value": "panels"}, {"kind": "key", "value": key}]
        identity = case["geometry"][path]["element_id"] if path in case["geometry"] else ["sparse-panels", "demo", path]
        mapping = {"path": path, "element_id": identity, "owner_path": owner, "root_path": root,
                   "path_steps": steps, "definition_id": definition,
                   "class_id": "/".join(definition) if path != "marker" else "Object",
                   "declaration": sources["parts"] if generated else sources["declarations"][path],
                   "definition": sources["panel"] if generated else sources["group"] if path != "marker" else None,
                   "declaration_definition_id": sources["group_id"] + ["panels"] if generated else None,
                   "generated": None, "generated_ancestor": path if generated else None}
        if generated:
            old = key.split(".", 1)[1]
            require(key in case["generated_keys"][owner] and old in sources["entries"], "Exact generated stable key")
            # C087 _finish_value_flow coalesces map origins on a Keyed result
            # to an aggregate key=None record. The rekeyed leaf retains its
            # original selected contributor. Generated selection then removes
            # the matching aggregate, keeping this exact original key only.
            transforms = [{**sources["transform"], "key": old, "input_entry": sources["entries"][old]}]
            mapping["generated"] = {"collection_path": owner + ".panels",
                "collection_id": ["sparse-panels", "demo", owner, "panels"],
                "collection_definition_id": sources["group_id"] + ["panels"], "key": key,
                "input": sources["input"], "input_entry": sources["entries"][old],
                "unique_declaration_span": False, "input_transforms": transforms,
                "input_rekeys": [sources["rekey"], {**sources["rekey"], "old_key": old,
                                                    "new_key": key, "input_entry": sources["entries"][old]}]}
        occurrences[path] = mapping
    for owner in ("first", "sibling"):
        path = owner + ".panels"
        keys = case["generated_keys"][owner]
        require(keys == sorted(keys), "Frozen generated canonical keys")
        collections[path] = {"path": path, "name": "panels", "element_id": ["sparse-panels", "demo", owner, "panels"],
            "owner_path": owner, "definition_id": sources["group_id"] + ["panels"],
            "declaration": sources["parts"], "input": sources["input"], "ordered_keys": keys,
            "entries": {key: {"path": owner + ".panels[" + json.dumps(key) + "]",
                              "element_id": ["sparse-panels", "demo", owner, "panels", key]} for key in keys},
            "physical_participation": "none"}
    return {"occurrences": occurrences, "collections": collections}


def location_matches(actual, expected, *, short=False):
    require(actual["source_id"] == expected["source_id"], "Exact original location source")
    start, end = ("start", "end") if short else ("start_byte", "end_byte")
    require(actual[start] == expected["start_byte"] and actual[end] == expected["end_byte"], "Exact original source role bounds")
    if "source_revision" in actual:
        require(actual["source_revision"] == expected["source_revision"], "Exact original source role revision")
    if "filename" in actual:
        require(actual["filename"] == expected["filename"], "Exact original source role filename")


def check_metadata(glb, case, sources, basis):
    document, revision, units = glb.document, case["program_revision"], sources["units"]
    meta = document["extras"]["ontokin"]
    mode = case["mode"]
    version = "0.21" if mode == "source" else "0.20"
    require(meta["target_contract"] == TARGETS[mode] and meta["profile"] == PROFILES[mode]
            and meta["schema_version"] == version, "Exact mode/source/target identity")
    require(meta["reach_profile"]["source_profile"] == PROFILES[mode], "Exact source-profile authority")
    require(document["animations"][0]["extras"]["ontokin"]["target_contract"] == TARGETS[mode], "Exact animation target")
    require(meta["source"]["uri"] == "main.ok" and meta["source"]["entry_source_id"] == "entry"
            and meta["source"]["entry_revision"] == "sha256:" + case["source_sha256"], "Exact entry identity")
    program = meta["program"]
    require(program["revision"] == revision and program["manifest"] == sources["manifest"]
            and program["entry_source_id"] == "entry", "Complete canonical source manifest")
    require(set(program["sources"]) == set(units), "Exact source unit closure")
    for source_id, unit in units.items():
        match = re.search(r'\bmodule\s+(\w+)\s*@\s*"([^"]+)"', unit["source"])
        require(match is not None, "Original module annotations")
        expected = {"source_id": source_id, "source_revision": T.digest(unit["source"].encode()),
                    "filename": unit["filename"], "package_id": unit.get("package_id"), "version": unit.get("version"),
                    "module_name": match[1], "module_key": match[2]}
        require(program["sources"][source_id] == expected, "Complete original module identity")
    projection = expected_projection(case, sources)
    require(program["occurrences"] == projection["occurrences"], "Complete original occurrence/source/lineage projection: " +
            str(Z.json_differences(program["occurrences"], projection["occurrences"])[:2]))
    require(program["collections"] == projection["collections"], "Complete original collection projection")
    require(set(glb.objects()) == set(projection["occurrences"]), "Exact native occurrence inventory")
    for path, index in glb.objects().items():
        node = document["nodes"][index]["extras"]["ontokin"]
        expected = projection["occurrences"][path]
        require(node["source_mapping"] == expected and node["element_id"] == expected["element_id"]
                and node["owner"] == expected["owner_path"] and node["program_revision"] == revision,
                "Exact node identity/source/ownership: " + path)
        if path == "marker":
            # Inherited box() emits the closed ordinary recipe only. Its
            # source authority remains the fully checked object declaration;
            # unlike native extrusion it does not expose a geometry span.
            require(node["geometry"] == {"kind": "box", "size": case["geometry"][path]["box_size_m"]},
                    "Exact original marker box recipe")
        elif path not in ("first", "sibling"):
            loc = sources["panel_geometry"]
            location_matches(node["geometry"], loc, short=True)
            location_matches(node["surface"]["source_location"], loc)
            binding = node["geometry"]["texture_bindings"]
            require(len(binding) == 1 and binding[0][0] == "top", "Exact top texture binding")
            location_matches(binding[0][1], sources["texture_binding"], short=True)
            location_matches(binding[0][1]["mapping"], sources["planar_uv"], short=True)
    for kind in ("materials", "images"):
        for item in document.get(kind, []):
            info = item.get("extras", {}).get("ontokin")
            if info is not None:
                require(info.get("program_revision") == revision, "Resource immutable program binding")
    quantization = meta["reach_quantization"]
    require(quantization["source_numeric_bound_basis"] == basis["source"], "Independent source numeric fingerprint")
    for key, value in basis["destination"].items():
        require(quantization["destination_numeric_bound_basis"][key] == value, "Independent destination numeric fingerprint")
    require(quantization["position_tolerance_m"] <= .001 and quantization["rotation_tolerance_rad"] <= .001
            and quantization["time_tolerance_s"] <= 1e-6, "No widened recording tolerance")
    return {"program_revision": revision, "source_locations": S.check_all_locations(document, units),
            "occurrences": len(projection["occurrences"]), "collections": len(projection["collections"]),
            "complete_source_projection_sha256": sha(canonical(projection))}


def typed(value, type_name, expected):
    require(value == {"type": type_name, "value": expected}, "Exact typed value: " + type_name)


def keyed(value, type_name, expected):
    require(set(value) == {"type", "value"} and value["type"] == "Keyed<" + type_name + ">", "Exact keyed value type")
    require([row["key"] for row in value["value"]] == sorted(expected), "Exact canonical keyed value members")
    for row in value["value"]:
        require(set(row) == {"key", "value"}, "Closed keyed entry")
        typed(row["value"], type_name, expected[row["key"]])


def check_properties(glb, case):
    for path, index in glb.objects().items():
        props = glb.document["nodes"][index]["extras"]["ontokin"]["properties"]
        require(list(props) == case["property_names"][path], "Exact declared property names and order: " + path)
        if path in ("first", "sibling"):
            prefix = "front." if path == "first" else "back."
            typed(props["prefix"], "String", prefix)
            keyed(props["overrides"], "Length", case[path + "_overrides"])
            keyed(props["dimensions"], "Length", {"left": 1., "middle": 1.5, "right": 2.})
            keyed(props["mounts"], "Length", {"left": 0., "middle": 3., "right": 6.})
            keyed(props["original_names"], "String", {key: key for key in ("left", "middle", "right")})
            keyed(props["names"], "String", {prefix + key: key for key in ("left", "middle", "right")})
            keyed(props["override_flags"], "Bool", case[path + "_flags"])
            keyed(props["selected"], "Length", case[path + "_selected"])
        elif path != "marker":
            wanted = case["geometry"][path]
            typed(props["width"], "Length", wanted["width_m"])
            old = json.loads(path.split("[", 1)[1][:-1]).split(".", 1)[1]
            typed(props["mount_x"], "Length", {"left": 0., "middle": 3., "right": 6.}[old])
    return {"complete_property_order_verified": True, "typed_membership_results_verified": True}


def check_geometry(glb, case):
    reports, used_materials, used_textures, used_images, used_samplers = [], set(), set(), set(), set()
    for path, index in glb.objects().items():
        primitives = glb.primitives(path)
        if path in ("first", "sibling"):
            require(not primitives, "Empty owner carrier has no geometry")
            continue
        wanted = case["geometry"][path]
        marker = path == "marker"
        if marker:
            size = wanted["box_size_m"]
            bounds = [[-v / 2 for v in size], [v / 2 for v in size]]
            points = list(product(*[(-v / 2, v / 2) for v in size]))
        else:
            size = [wanted["width_m"], wanted["height_m"], wanted["depth_m"]]
            bounds = [[0., 0., 0.], size]
            points = wanted["corners_m"]
        corners = {struct.pack("<3f", *p) for p in points}
        center = [(a + b) / 2 for a, b in zip(*bounds)]
        require(len(primitives) == (1 if marker else 3), "Exact native material-region count")
        actual_corners, counts, volume, area = set(), Counter(), 0., 0.
        for primitive in primitives:
            attributes = primitive["attributes"]
            require(primitive.get("mode", 4) == 4 and set(attributes) in ({"POSITION", "NORMAL"}, {"POSITION", "NORMAL", "TEXCOORD_0"}),
                    "Exact primitive mode/streams")
            region = "box" if marker else primitive["extras"]["ontokin"]["region_key"]
            require(region in ({"box"} if marker else {"bottom", "side", "top"}), "Exact source material region")
            positions, normals, indices = glb.accessor(attributes["POSITION"]), glb.accessor(attributes["NORMAL"]), glb.accessor(primitive["indices"])
            require(len(positions) == len(normals) and indices and len(indices) % 3 == 0, "Geometry cardinalities")
            require(all(type(i) is int and 0 <= i < len(positions) for i in indices), "Triangle indices")
            selected = set(indices)
            for i in selected:
                encoded = struct.pack("<3f", *positions[i])
                require(encoded in corners, "Position belongs to the independent source prism")
                actual_corners.add(encoded)
                require(abs(sum(n * n for n in normals[i]) - 1.) <= 1e-6, "Unit native normal")
            for offset in range(0, len(indices), 3):
                a, b, c = [positions[i] for i in indices[offset:offset + 3]]
                ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
                cross = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]]
                magnitude = math.sqrt(sum(v * v for v in cross))
                require(magnitude > 0 and sum(cross[i] * ((a[i] + b[i] + c[i]) / 3 - center[i]) for i in range(3)) > 0,
                        "Nondegenerate outward triangle")
                for i in indices[offset:offset + 3]:
                    Z.near(normals[i], [v / magnitude for v in cross], 1e-6, "Native flat face normal")
                area += magnitude / 2
                volume += sum(a[i] * [b[1] * c[2] - b[2] * c[1], b[2] * c[0] - b[0] * c[2], b[0] * c[1] - b[1] * c[0]][i]
                              for i in range(3)) / 6
            counts[region] += len(indices) // 3
            material_id = primitive["material"]
            material = glb.reference("materials", material_id)
            used_materials.add(material_id)
            if not marker:
                info = material["extras"]["ontokin"]
                require(info["occurrence_path"] == path and info["source_region_key"] == region, "Material identity")
            color = [.5, .5, .5, 1.] if marker else wanted["side_color"] if region == "side" else wanted["cap_color"]
            pbr = material["pbrMetallicRoughness"]
            require(pbr["baseColorFactor"] == color and pbr["metallicFactor"] == 0 and pbr["roughnessFactor"] == .7
                    and material.get("alphaMode", "OPAQUE") == "OPAQUE" and not material.get("doubleSided", False), "Exact PBR/opacity")
            if marker or region != "top":
                require("baseColorTexture" not in pbr and "TEXCOORD_0" not in attributes, "Untextured source region")
                continue
            require(set(attributes) == {"POSITION", "NORMAL", "TEXCOORD_0"}, "Complete top UV stream")
            uv_item = glb.reference("accessors", attributes["TEXCOORD_0"])
            require(uv_item["componentType"] == 5126 and uv_item["type"] == "VEC2", "Exact UV representation")
            texture_info = pbr["baseColorTexture"]
            require(texture_info.get("texCoord", 0) == 0, "Only source UV set zero")
            used_textures.add(texture_info["index"])
            texture = glb.reference("textures", texture_info["index"])
            used_images.add(texture["source"]); used_samplers.add(texture["sampler"])
            require(glb.reference("samplers", texture["sampler"]) == T.SAMPLER, "Exact nearest/clamp sampler")
            require(glb.reference("images", texture["source"])["extras"]["ontokin"]["asset_id"] == "label", "Original source PNG identity")
            uvs = glb.accessor(attributes["TEXCOORD_0"])
            require(len(uvs) == len(positions), "Complete UV count")
            for i, uv in enumerate(uvs):
                expected = (T.f32(.5 * positions[i][0]), T.f32(1 - .5 * positions[i][1])) if i in selected else (0., 0.)
                require(struct.pack("<2f", *uv) == struct.pack("<2f", *expected), "Exact independently authored top UV")
        require(actual_corners == corners and dict(counts) == ({"box": 12} if marker else {"bottom": 2, "side": 8, "top": 2}),
                "Complete source corner/triangle inventory")
        w, h, d = size
        require(abs(volume - w * h * d) <= 1e-12 and abs(area - 2 * (w * h + w * d + h * d)) <= 1e-12, "Independent closed-prism volume and area")
        reports.append({"path": path, "triangles": sum(counts.values()), "corners": len(corners), "volume_m3": volume, "area_m2": area})
    for table, used in (("materials", used_materials), ("textures", used_textures), ("images", used_images), ("samplers", used_samplers)):
        require(used == set(range(len(glb.document.get(table, [])))), "No dangling native resource: " + table)
    return reports


def check_motion(glb, case):
    objects = glb.objects()
    streams = glb.animation_streams()
    require(set(streams) == {(path, channel) for path in objects for channel in ("translation", "rotation")}, "Complete recorded motion channels")
    samples = []
    for offset, time in enumerate((0., .25, .5, .75, 1.)):
        for path in objects:
            source_path = (path + '.panels["' + ("front.left" if path == "first" else "back.left") + '"]') if path in ("first", "sibling") else path
            expected = case["geometry"][source_path]["translation_samples_m"][offset]
            pose = glb.pose(path, time)
            Z.near(pose["translation"], expected, .001, "Frozen world translation: " + path)
            Z.near(pose["rotation"], [0., 0., 0., 1.], .001, "Frozen world quaternion: " + path)
        samples.append({"time_seconds": time, "objects": len(objects)})
    return {"samples": samples, "channels": len(streams),
            "stream_sha256": {path + ":" + kind: {"time": sha(value[0]), "value": sha(value[1])}
                              for (path, kind), value in streams.items()}}


def allowed_patterns(delivery):
    patterns = []
    for group in delivery["allowed_scalar_differences"]:
        for text in group["paths"]:
            parts = re.sub(r"\[(\*|[0-9]+)\]", r".\1", text).split(".")
            require(all("[" not in part and "]" not in part for part in parts), "Closed frozen scalar-path grammar")
            choices = [part[1:-1].split(",") if part.startswith("{") and part.endswith("}") else [part]
                       for part in parts]
            patterns.extend(tuple(row) for row in product(*choices))
    return patterns


def normalize(glb, frozen):
    patterns, changes = allowed_patterns(frozen["delivery"]), []
    def matches(path):
        return any(len(pattern) == len(path) and all(part == "*" or part == str(item) for part, item in zip(pattern, path))
                   for pattern in patterns)
    def visit(value, path=()):
        if isinstance(value, dict):
            return {key: visit(child, path + (key,)) for key, child in value.items()}
        if isinstance(value, list):
            return [visit(child, path + (index,)) for index, child in enumerate(value)]
        if matches(path):
            require(type(value) in (int, float, str), "An allowed path must be an independently validated scalar")
            changes.append({"path": list(path), "original": value})
            return "<validated:" + json.dumps(path, ensure_ascii=False, separators=(",", ":")) + ">"
        return value
    return visit(glb.document), changes


def check_artifact(raw, case, frozen, basis):
    glb = T.GLB(raw, target=TARGETS[case["mode"]])
    framing = Z.check_raw_framing(glb)
    sources = original_sources(case, frozen)
    metadata = check_metadata(glb, case, sources, basis)
    properties = check_properties(glb, case)
    geometry = check_geometry(glb, case)
    images = Z.check_images(glb, sources["payload"])
    image_expected = frozen["expected"]["texture"]
    require(len(images) == 1 and all(images[0][key] == image_expected[key] for key in ("sha256", "bytes", "width", "height")),
            "Frozen entire PNG and dimensions")
    motion = check_motion(glb, case)
    accessors = []
    for i in range(len(glb.document["accessors"])):
        glb.accessor(i)
        accessors.append({"index": i, "bytes": len(glb.accessor_bytes(i)), "sha256": sha(glb.accessor_bytes(i))})
    normalized, changes = normalize(glb, frozen)
    report = {"role": case["id"], "status": "passed", "bytes": len(raw), "sha256": sha(raw), "framing": framing,
              "metadata": metadata, "properties": properties, "geometry": geometry, "images": images, "motion": motion,
              "accessors": accessors, "complete_bin_sha256": sha(glb.binary),
              "normalized_json_sha256": sha(Z.compact_json_bytes(normalized)), "permitted_scalar_replacements": changes}
    return glb, normalized, report


def compare(left, right):
    a, a_normalized, a_report = left
    b, b_normalized, b_report = right
    require(a.binary == b.binary, "Entire paired BIN chunk differs")
    for key in ("accessors", "bufferViews", "buffers"):
        require(a.document[key] == b.document[key], "Entire paired buffer/accessor layout differs: " + key)
    require(a_report["accessors"] == b_report["accessors"], "Every paired raw accessor differs")
    for index in range(len(a.document["accessors"])):
        require(a.accessor(index) == b.accessor(index), "Every paired decoded accessor differs")
    differences = Z.json_differences(a_normalized, b_normalized)
    require(not differences, "Unpermitted complete paired JSON differences: " + str(differences[:4]))
    require(Z.compact_json_bytes(a_normalized) == Z.compact_json_bytes(b_normalized), "Paired JSON member order/compact bytes differ")
    return {"source": a_report["role"], "control": b_report["role"], "status": "passed",
            "complete_bin_sha256": sha(a.binary), "complete_bin_bytes": len(a.binary),
            "normalized_json_sha256": a_report["normalized_json_sha256"], "accessors": len(a_report["accessors"]),
            "metadata_objects_or_arrays_removed": 0, "unpermitted_differences": []}


def repack(document, binary):
    """Keep every original JSON member order and buffer length while mutating."""
    text = Z.compact_json_bytes(document)
    text += b" " * (-len(text) % 4)
    require(len(binary) % 4 == 0, "Mutation retains original padded BIN")
    size = 12 + 8 + len(text) + 8 + len(binary)
    return struct.pack("<III", 0x46546C67, 2, size) + struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(binary), 0x004E4942) + binary


def mutate(original, kind, case, frozen):
    glb = T.GLB(original, target=TARGETS[case["mode"]])
    document, binary = copy.deepcopy(glb.document), bytearray(glb.binary)
    path = 'first.panels["front.left"]'
    node_index = glb.objects()[path]
    mesh = document["meshes"][document["nodes"][node_index]["mesh"]]
    primitive = mesh["primitives"][0]
    top = next(p for p in mesh["primitives"] if p["extras"]["ontokin"]["region_key"] == "top")
    mutation = {"id": kind}
    if kind in ("glb-position", "glb-normal", "glb-index", "glb-uv", "glb-motion"):
        row_index = 0
        if kind == "glb-index":
            accessor = primitive["indices"]
        elif kind == "glb-uv":
            accessor = top["attributes"]["TEXCOORD_0"]
            row_index = glb.accessor(top["indices"])[0]
        elif kind == "glb-motion":
            animation = document["animations"][0]
            channel = next(c for c in animation["channels"] if c["target"] == {"node": node_index, "path": "translation"})
            accessor = animation["samplers"][channel["sampler"]]["output"]
        else:
            accessor = primitive["attributes"]["POSITION" if kind == "glb-position" else "NORMAL"]
            row_index = glb.accessor(primitive["indices"])[0]
        item = document["accessors"][accessor]
        view = document["bufferViews"][item["bufferView"]]
        fmt = {5123: "H", 5125: "I", 5126: "f"}[item["componentType"]]
        components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[item["type"]]
        stride = view.get("byteStride", struct.calcsize("<" + fmt) * components)
        offset = view.get("byteOffset", 0) + item.get("byteOffset", 0) + row_index * stride
        before = struct.unpack_from("<" + fmt, binary, offset)[0]
        after = glb.accessor(accessor)[1] if kind == "glb-index" else before + .125
        require(before != after, "Actual single-component hostile change")
        struct.pack_into("<" + fmt, binary, offset, after)
        mutation.update(kind="single_binary_component", accessor=accessor, row_index=row_index, bin_offset=offset,
                        component_type=item["componentType"], before=before, after=after)
    elif kind == "glb-image":
        image = document["images"][0]
        view = document["bufferViews"][image["bufferView"]]
        offset = view.get("byteOffset", 0) + 12
        before = binary[offset]; binary[offset] ^= 1
        mutation.update(kind="single_embedded_png_byte", bin_offset=offset, before=before, after=binary[offset])
    elif kind == "glb-material":
        index = primitive["material"]
        before = document["materials"][index]["pbrMetallicRoughness"]["roughnessFactor"]
        document["materials"][index]["pbrMetallicRoughness"]["roughnessFactor"] = .8
        mutation.update(kind="single_json_scalar", path=["materials", index, "pbrMetallicRoughness", "roughnessFactor"], before=before, after=.8)
    elif kind == "glb-node-key":
        target = document["nodes"][node_index]["extras"]["ontokin"]["element_id"]
        before = target[-1]; target[-1] = "front.invented"
        mutation.update(kind="single_json_scalar", path=["nodes", node_index, "extras", "ontokin", "element_id", len(target) - 1], before=before, after=target[-1])
    elif kind == "glb-profile":
        before = document["extras"]["ontokin"]["target_contract"]
        document["extras"]["ontokin"]["target_contract"] = "ontokin.glb/0.20"
        mutation.update(kind="single_json_scalar", path=["extras", "ontokin", "target_contract"], before=before, after="ontokin.glb/0.20")
    elif kind == "glb-source-pin":
        target = document["extras"]["ontokin"]["program"]["manifest"]["units"][0]
        before = target["source_revision"]; target["source_revision"] = "sha256:" + "0" * 64
        mutation.update(kind="single_json_scalar", path=["extras", "ontokin", "program", "manifest", "units", 0, "source_revision"], before=before, after=target["source_revision"])
    elif kind == "glb-source-location":
        target = document["nodes"][node_index]["extras"]["ontokin"]["source_mapping"]["generated"]["input_transforms"][0]
        before = copy.deepcopy(target["expression"])
        sources = original_sources(case, frozen)
        calls = S.intrinsic_locations({PANEL: sources["units"][PANEL]}, b"map_keyed")
        other = next(c for c in calls if c["start_byte"] != before["start_byte"])
        after = enriched(other, sources["units"])
        target["expression"] = after
        mutation.update(kind="one_complete_source_location", path=["nodes", node_index, "extras", "ontokin", "source_mapping", "generated", "input_transforms", 0, "expression"], before=before, after=after)
    elif kind == "glb-lineage":
        target = document["nodes"][node_index]["extras"]["ontokin"]["source_mapping"]["generated"]["input_transforms"]
        before = copy.deepcopy(target[0]); del target[0]
        mutation.update(kind="one_removed_origin_record", path=["nodes", node_index, "extras", "ontokin", "source_mapping", "generated", "input_transforms", 0], before=before)
    elif kind == "glb-framing":
        mutation.update(kind="one_trailing_byte", file_offset=len(original), appended_hex="00")
        return original + b"\0", mutation
    else:
        raise AssertionError("Unknown frozen hostile class")
    raw = repack(document, bytes(binary))
    require(raw != original, "Mutation bytes must differ")
    mutation["json_leaf_differences"] = Z.json_differences(glb.document, document)
    mutation["changed_bin_byte_offsets"] = [i for i, (a, b) in enumerate(zip(glb.binary, binary)) if a != b]
    return raw, mutation


def check_hostiles(original, case, frozen, basis, output):
    results = []
    original_hash = sha(original)
    for kind in GLB_HOSTILES:
        row = {"id": kind, "original_sha256": original_hash, "original_bytes": len(original)}
        try:
            check_artifact(original, case, frozen, basis)
            row["original_accepted"] = True
            changed, mutation = mutate(original, kind, case, frozen)
            path = output / "hostiles" / (kind + ".glb")
            path.parent.mkdir(parents=True, exist_ok=True)
            require(not path.exists(), "Fresh isolated hostile copy")
            path.write_bytes(changed)
            row.update(mutated_path=path.relative_to(output).as_posix(), mutated_sha256=sha(changed),
                       mutated_bytes=len(changed), mutation=mutation)
            try:
                check_artifact(changed, case, frozen, basis)
            except T.ReferenceError as error:
                row.update(status="refused", refusal={"type": type(error).__name__, "message": str(error), "code": error.code})
            else:
                row.update(status="failed", reason="Independent reader accepted a frozen hostile mutation")
            require(sha(original) == original_hash, "Original remains byte-identical")
            check_artifact(original, case, frozen, basis)
            row["original_still_accepted"] = True
        except Exception as error:
            row.update(status="preparation_or_reader_error", error_type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        save(output / "hostiles" / (kind + ".json"), row)
        results.append(row)
    return results


def load_producer(directory, source, *, agent=False):
    summary_raw = (directory / "summary.json").read_bytes()
    summary = T.loads(summary_raw)
    before = T.loads((directory / "source-before.json").read_bytes())
    after = T.loads((directory / "source-after.json").read_bytes())
    identity = git_identity(source)
    require(before == after and not identity["status"], "Executing source before/after identity")
    require(before.get("commit", before.get("head")) == identity["commit"] and before["tree"] == identity["tree"],
            "Executing source matches the explicit checkout")
    require(summary["source_unchanged"] is True, "Producer source unchanged")
    if agent:
        require(summary["status"] == "passed" and summary["frozen_inputs_unchanged"] is True, "Completed Agent producer")
    else:
        require(summary["full_cohort"] is True and summary["inputs_unchanged"] is True
                and summary["input_manifest_sha256"] == INPUT_SHA and summary["specification_sha256"] == SPEC_SHA,
                "Completed frozen source producer")
    return summary, {"path": str(directory), "summary_sha256": sha(summary_raw), "executing_source": identity}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference-checkout", "candidate-source", "control-source", "fixtures", "candidate-output", "control-output", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--agent-output", type=Path)
    args = parser.parse_args()
    for key, value in vars(args).items():
        if isinstance(value, Path):
            setattr(args, key, value.resolve())
    require(not args.output.exists() and not args.output.is_relative_to(args.candidate_source)
            and not args.output.is_relative_to(args.control_source), "Fresh independent output directory")
    args.output.mkdir(parents=True)
    report = {"schema_version": "ontokin.c088-independent-glb-reader/1", "status": "running",
              "reader": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).read_bytes())},
              "argv": sys.argv, "python": sys.version, "platform": platform.platform(),
              "artifacts": [], "pairs": [], "agent_artifacts": [], "hostiles": [], "failures": []}
    try:
        report["reference_utilities"] = import_references(args.reference_checkout)
        frozen = load_frozen(args.fixtures)
        report.update(input_manifest_sha256=INPUT_SHA, input_inventory_sha256=frozen["input_inventory_sha256"], specification_sha256=SPEC_SHA)
        summaries = {}
        for name, directory, source in (("candidate", args.candidate_output, args.candidate_source),
                                        ("control", args.control_output, args.control_source)):
            summaries[name], receipt = load_producer(directory, source)
            report[name + "_producer"] = receipt
        bases = {"source": Z.implementation_basis(args.candidate_source),
                 "reduction": Z.implementation_basis(args.control_source), "literal": Z.implementation_basis(args.control_source)}
        entries = {}
        for family, summary in summaries.items():
            directory = args.candidate_output if family == "candidate" else args.control_output
            for row in summary["artifacts"]:
                require(row["role"] not in entries, "Unique original native artifact role")
                entries[row["role"]] = (directory, row)
        roles = frozen["delivery"]["native_roles"]
        require(set(entries) == {row["role"] for row in roles}, "All and only twenty-one frozen native roles")
        checked, raw_roles = {}, {}
        for role in roles:
            name = role["role"]
            case = frozen["cases"][name]
            directory, row = entries[name]
            raw = T.ordinary_path(directory, row["path"]).read_bytes()
            try:
                require((len(raw), sha(raw), row["program_revision"]) == (row["bytes"], row["sha256"], case["program_revision"]), "Recorded artifact identity")
                checked[name] = check_artifact(raw, case, frozen, bases[case["mode"]])
                raw_roles[name] = raw
                report["artifacts"].append(checked[name][2])
            except Exception as error:
                report["failures"].append({"stage": "artifact", "role": name, "type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
            save(args.output / "summary.json", report)
        for names in frozen["delivery"]["same_state_control_pairs"]:
            for control in names[1:]:
                try:
                    require(names[0] in checked and control in checked, "Both original paired artifacts accepted")
                    report["pairs"].append(compare(checked[names[0]], checked[control]))
                except Exception as error:
                    report["failures"].append({"stage": "pair", "roles": [names[0], control], "type": type(error).__name__, "message": str(error)})
        if args.agent_output is not None:
            summary, receipt = load_producer(args.agent_output, args.candidate_source, agent=True)
            report["agent_producer"] = receipt
            by_revision = {c["program_revision"]: c for c in frozen["cases"].values() if c["mode"] == "source" and c["status"] == "passed"}
            for row in summary["agent_artifacts"]:
                try:
                    case = by_revision[row["program_revision"]]
                    raw = T.ordinary_path(args.agent_output, row["glb"]).read_bytes()
                    require(len(raw) == row["bytes"] and sha(raw) == row["sha256"], "Actual complete retrieved artifact identity")
                    result = check_artifact(raw, case, frozen, bases["source"])
                    require(raw == raw_roles[case["id"]], "Complete Agent artifact equals its exact native-source role")
                    report["agent_artifacts"].append({"workflow": row["workflow"], "name": row["name"], "artifact_id": row["artifact_id"],
                        "program_revision": case["program_revision"], "sha256": sha(raw), "bytes": len(raw), "status": "passed", "native_role": case["id"],
                        "semantic_report_sha256": sha(canonical(result[2]))})
                except Exception as error:
                    report["failures"].append({"stage": "agent_artifact", "workflow": row["workflow"], "name": row["name"], "type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
        if "base" in checked:
            report["hostiles"] = check_hostiles(raw_roles["base"], frozen["cases"]["base"], frozen, bases["source"], args.output)
        else:
            report["failures"].append({"stage": "hostiles", "message": "Original base was not independently accepted; no mutation refusal can pass"})
        require(len(report["artifacts"]) == 21 and len(report["pairs"]) == 14, "Complete native original and paired cohort")
        require(len(report["hostiles"]) == 13 and all(r["status"] == "refused" and r.get("original_still_accepted") for r in report["hostiles"]),
                "All thirteen original-accepted hostile copies refused")
        require(not report["failures"], "Independent reader has retained failures")
        require(not any(n == "ontokin" or n.startswith("ontokin.") for n in sys.modules), "No product imports")
        report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", fatal={"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
    finally:
        report["product_modules_imported"] = [n for n in sys.modules if n == "ontokin" or n.startswith("ontokin.")]
        report["reader_sha256_after"] = sha(Path(__file__).read_bytes())
        save(args.output / "summary.json", report)
        inventory = [{"path": p.relative_to(args.output).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
                     for p in sorted(args.output.rglob("*")) if p.is_file()]
        save(args.output / "READER-INVENTORY.json", inventory)
    print(json.dumps({"status": report["status"], "artifacts": len(report["artifacts"]), "pairs": len(report["pairs"]),
                      "agent_artifacts": len(report["agent_artifacts"]), "hostiles": len(report["hostiles"]), "failures": len(report["failures"]),
                      "fatal": report.get("fatal", {}).get("message")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
