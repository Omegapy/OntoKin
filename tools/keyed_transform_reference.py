"""Independent finite C081 readers; no production parser or runtime imports.

The expected values are the published preimplementation inputs. The reusable
GLB/PNG readers below are structural byte readers from the preceding independent
verifier, not compiler/export helpers. This module neither executes source nor
uses a candidate artifact to generate expected source answers.
"""
from __future__ import annotations

import base64
from collections import Counter
import copy
import math
from pathlib import Path
import re
import struct

from tools.texture_reference import (GLB, ReferenceError, SAMPLER, bundle_identity,
    canonical, decode_png, digest, exact_uv, f32, file_payload, loads, ordinary_path,
    repack_glb, require, sha)

ROOT = Path(__file__).resolve().parents[1]
FREEZE_COMMIT = "8525e69c5c8bbbb5933bb3b9bf0179e48468a8ae"
FREEZE_SHA256 = "262b9d531a832dbb75cc0fb256ae4b044ce2afab5098100af54fa5ba1029fe80"
TARGET = "ontokin.glb/0.14"
PROFILE = "keyed-transform-0.1"
PROTOCOL = "ontokin.agent/0.14"
STORE_SCHEMA = "ontokin.keyed-transform-program-agent-store/0.1"
DELIVERED_CASES = {"panel-task", "panel-task-repaired", "panel-identity", "panel-task-higher-budget"}
SOURCE_IMPLEMENTATION = (
    "ontokin/reach_numeric.py", "ontokin/reach_kinematics.py", "ontokin/reach_pose.py",
    "ontokin/reach_phase.py", "ontokin/reach_runtime.py", "ontokin/reach_export.py",
    "ontokin/reach_recording_fast.py", "ontokin/reach_recording_capture.py", "ontokin/reach_transfer_bounds.py")
SOURCE_DERIVATION = (
    "docs/engineering/reach-numeric-kernel.md", "docs/engineering/reach-source-kernel.md",
    "docs/engineering/reach-coaxial-phase-bounds.md", "docs/engineering/reach-carrier-rotation-cursors.md",
    "docs/engineering/reach-recording-certified-planar.md", "docs/engineering/reach-deferred-phase-locations.md",
    "docs/engineering/reach-planning-reuse.md", "docs/engineering/reach-release-cell-envelope.md")


def load_fixtures(root=ROOT / "examples/keyed-transform"):
    root = Path(root).resolve()
    repository = root.parent.parent
    freeze_raw = ordinary_path(repository, "docs/language-design/keyed-transform-v0.1/INPUT-FREEZE.json").read_bytes()
    require(sha(freeze_raw) == FREEZE_SHA256, "Published C081 input freeze changed")
    freeze = loads(freeze_raw)
    names, size = set(), 0
    for entry in freeze["files"]:
        require(entry["path"] not in names, "Duplicate frozen path")
        raw = ordinary_path(repository, entry["path"]).read_bytes()
        require(len(raw) == entry["bytes"] and sha(raw) == entry["sha256"], "Frozen bytes changed: " + entry["path"])
        names.add(entry["path"]); size += len(raw)
    require(len(names) == freeze["file_count"] == 309 and size == freeze["total_bytes"] == 489448,
            "Published freeze inventory is incomplete")
    expected = loads(ordinary_path(root, "expected.json").read_bytes())
    cases = {item["name"]: item for item in expected["cases"]}
    require(len(expected["cases"]) == len(cases) == 97 and
            Counter(item["expected_outcome"] for item in cases.values()) == {"valid": 50, "invalid": 47},
            "C081 source corpus inventory differs")
    require({c["name"] for c in cases.values() if c["expected_stage"] == "delivered" and c["expected_outcome"] == "valid"} == DELIVERED_CASES,
            "Frozen delivered-stage scope differs")
    workflows = loads(ordinary_path(root, "workflows.json").read_bytes())
    acceptance = loads(ordinary_path(repository, "docs/language-design/keyed-transform-v0.1/acceptance.json").read_bytes())
    require(len(workflows["workflows"]) == 10 and {w["id"] for w in workflows["workflows"]} == set(acceptance["agent_workflow_ids"]),
            "Frozen Agent inventory differs")
    result = {"root": root, "repository": repository, "freeze": freeze, "expected": expected,
              "cases": cases, "workflows": workflows, "acceptance": acceptance}
    for case in cases.values():
        require(bundle_identity(case_payload(result, case)) == (case["program_revision"], case["canonical_manifest"]),
                "Frozen program identity cannot be independently reproduced: " + case["name"])
        if case["expected_outcome"] == "valid":
            control = case["explicit_c080_control"]
            require(bundle_identity(case_payload(result, case, control=True)) == (control["program_revision"], control["canonical_manifest"]),
                    "Frozen explicit control identity differs: " + case["name"])
    return result


def case_payload(fixtures, case, *, control=False):
    manifest = case["explicit_c080_control"]["file_manifest"] if control else case["file_manifest"]
    return file_payload(fixtures["root"], manifest)


def canonical_probe_type(display):
    # These two documented presentation aliases occur in the frozen corpus.
    # No dimensional or generic leaf type is otherwise weakened or stripped.
    return {"Keyed<Quantity[m^2]>": "Keyed<Area>",
            "Keyed<Point3>": "Keyed<Point3<Length>>"}.get(display, display)


def delivered_by_revision(fixtures):
    selected = [case for case in fixtures["cases"].values()
                if case["expected_outcome"] == "valid" and case["expected_stage"] == "delivered"]
    result = {case["program_revision"]: case for case in selected}
    require(len(result) == len(selected) == 4, "Delivered source identities are incomplete or ambiguous")
    return result


def source_units(payload):
    return {"entry": payload["entry"], **{"package:" + u["package_id"] + "@" + u["version"]: u for u in payload["modules"]}}


def codes(value):
    if isinstance(value, dict):
        return sorted(set(([value["code"]] if isinstance(value.get("code"), str) else []) + [c for v in value.values() for c in codes(v)]))
    if isinstance(value, list):
        return sorted(set(c for v in value for c in codes(v)))
    return []


def walk(value, path=()):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, path + (key,))
    elif isinstance(value, list):
        for key, child in enumerate(value):
            yield from walk(child, path + (key,))


def check_location(location, units, *, allow_null=False):
    if location is None:
        require(allow_null, "Unexpected null source location")
        return None
    require(isinstance(location, dict), "Source location must be an object")
    key = location.get("source_id")
    require(key in units, "Source location refers to an absent unit")
    unit, start_key, end_key = units[key], "start_byte", "end_byte"
    if start_key not in location:
        start_key, end_key = "start", "end"
    start, end = location.get(start_key), location.get(end_key)
    raw = unit["source"].encode("utf-8")
    require(type(start) is int and type(end) is int and 0 <= start <= end <= len(raw), "Source location is out of range")
    # A source span must also terminate on UTF-8 boundaries.
    raw[:start].decode("utf-8"); raw[start:end].decode("utf-8"); raw[end:].decode("utf-8")
    if "source_revision" in location:
        require(location["source_revision"] == digest(raw), "Source span hash differs from original bytes")
    if "filename" in location:
        require(location["filename"] == unit["filename"], "Source span filename differs")
    return raw[start:end]


def same_location(actual, expected, units):
    check_location(actual, units)
    require(all(actual.get(k) == v for k, v in expected.items()), "Exact frozen source span differs")


def check_all_locations(value, units):
    count = 0
    for _, node in walk(value):
        if not isinstance(node, dict) or node.get("source_id") not in units:
            continue
        if ("start_byte" in node and "end_byte" in node) or ("start" in node and "end" in node):
            check_location(node, units); count += 1
        if "source_revision" in node:
            require(node["source_revision"] == digest(units[node["source_id"]]["source"].encode()), "Source revision lost byte binding")
    return count


def panel_transform(case, fixtures):
    return case["expected"].get("transform_provenance", fixtures["cases"]["panel-task"]["expected"]["transform_provenance"])


def check_transforms(records, units, *, expected=None, require_nonempty=True):
    require(isinstance(records, list) and (not require_nonempty or records), "Missing ordered map derivation records")
    count = 0
    for record in records:
        base_fields = {"expression", "body", "input", "input_element_type", "output_element_type"}
        require(isinstance(record, dict) and set(record) in (base_fields, base_fields | {"key", "input_entry"}),
                "Transform projection has an unadopted shape")
        expression = check_location(record["expression"], units)
        require(expression.startswith(b"map_keyed<"), "Derived expression does not identify the authored map")
        check_location(record["body"], units); check_location(record["input"], units)
        for name in ("body", "input"):
            location, outer = record[name], record["expression"]
            require(location["source_id"] == outer["source_id"] and
                    outer["start_byte"] <= location["start_byte"] < location["end_byte"] <= outer["end_byte"],
                    "Map body/input lies outside its exact expression")
        require(all(type(record[k]) is str and record[k] for k in ("input_element_type", "output_element_type")), "Missing map element types")
        if "key" in record:
            require(type(record["key"]) is str and record["key"].isascii() and record["key"], "Derived leaf lost its stable input key")
            raw_entry = check_location(record["input_entry"], units, allow_null=True)
            if raw_entry is not None:
                require(re.match(re.escape(canonical(record["key"])) + rb"\s*:", raw_entry) is not None,
                        "Derived leaf entry span identifies another original key")
        count += 1
    if expected is not None:
        require(len(records) == 1, "Panel fixture must retain exactly its one source map")
        record = records[0]
        for part in ("expression", "body", "input"):
            same_location(record[part], expected[part], units)
        expected_input = "Length" if expected["input_element_kind"] == "Quantity" else expected["input_element_kind"]
        require(record["input_element_type"] == expected_input and record["output_element_type"] == "Length", "Panel map element dimensions differ")
    return count


def check_keyed_leaf_provenance(value, units, *, expected=None):
    """Require the adopted output-leaf projection, not aggregate-only labels."""
    aggregate = value.get("derived_transforms")
    check_transforms(aggregate, units, expected=expected)
    checked = 0
    for entry in value["value"]:
        records = entry["value"].get("derived_transforms")
        check_transforms(records, units)
        current = records[-1]
        require(current.get("key") == entry["key"] and "input_entry" in current,
                "Output leaf lost its original stable key/entry projection")
        require(current["input_entry"] is not None, "Frozen literal input leaf lost its known original entry span")
        require(all(current[field] == aggregate[-1][field] for field in
                    ("expression", "body", "input", "input_element_type", "output_element_type")),
                "Output leaf is not bound to its aggregate's final source map")
        if expected is not None:
            same_location(current["input_entry"], expected["original_key_entries"][entry["key"]], units)
        checked += 1
    return checked


def expected_occurrences(case):
    expected = case["expected"]
    nodes = {}
    for owner, origin, velocity in (("first", [-8, 0, 0], [0, .5, 0]), ("sibling", [2, 0, 0], [0, 0, 0])):
        nodes[owner] = {"path": owner, "element_id": ["panel-task", "demo", owner], "owner": None,
                        "origin": origin, "velocity": velocity, "empty": True, "bindings": {}, "triangle_count": 0, "materials": {}}
    for panel in expected["panels"] + [expected["marker"]]:
        poses = panel["poses"]
        origin = poses[0]["position_m"]
        velocity = [end - start for start, end in zip(origin, poses[-1]["position_m"])]
        is_panel = "input_key" in panel
        nodes[panel["path"]] = {**copy.deepcopy(panel), "origin": origin, "velocity": velocity, "empty": False,
            "element_id": panel.get("element_id", ["panel-task", "demo", "marker"]),
            "owner": panel.get("owner"), "bindings": {"top": {"asset_id": "label", "mapping": expected["mapping"]}} if is_panel else {}}
    return nodes


def check_inspection(actual, control, case, fixtures):
    """Compare public typed values against exact scalar answers/explicit .13 source."""
    payload, baseline = case_payload(fixtures, case), case_payload(fixtures, case, control=True)
    units, old_units = source_units(payload), source_units(baseline)
    require(actual.get("program_revision") == case["program_revision"], "Inspection names another program")
    require(control.get("program_revision") == case["explicit_c080_control"]["program_revision"], "Control inspection names another source")
    require(actual.get("ok") is not False and control.get("ok") is not False and
            not any(c.startswith(("OKL-E-", "OKE-E-")) for c in codes(actual) + codes(control)), "Inspection failed")
    a_items, b_items = actual.get("items", []), control.get("items", [])
    require(a_items and b_items, "Public value inspection did not retain any source records")
    location_count = check_all_locations(actual, units) + check_all_locations(control, old_units)
    transform_count = 0
    for _, node in walk(actual):
        if isinstance(node, dict) and "derived_transforms" in node:
            transform_count += check_transforms(node["derived_transforms"], units)
    require(not any(isinstance(n, dict) and "derived_transforms" in n for _, n in walk(control)), "Legacy inspection projection acquired .14 map fields")

    def member(items, object_path, name):
        matches = [i["values"][name] for i in items if name in i.get("values", {}) and
                   (i.get("path") in (object_path, object_path + "." + name) or i.get("name") == name)]
        require(matches and all(m == matches[0] for m in matches), "Requested public member is absent/ambiguous: " + object_path + "." + name)
        return matches[0]

    def semantic(value, bound_units):
        # These are the documented nonsemantic origin fields only. Every span
        # is checked first; types, frames and complete recipe values remain.
        if isinstance(value, list):
            return [semantic(v, bound_units) for v in value]
        if not isinstance(value, dict):
            return value
        output = {}
        location = value.get("source_id") in bound_units and (("start" in value and "end" in value) or ("start_byte" in value and "end_byte" in value))
        for key, child in value.items():
            if key in ("derived_transforms", "input_entry"):
                continue
            if location and key in ("source_revision", "filename", "start", "end", "start_byte", "end_byte"):
                continue
            output[key] = semantic(child, bound_units)
        return output

    probes = 0
    if "probe" in case:
        probe = case["probe"]
        av, bv = member(a_items, probe["object_path"], probe["member"]), member(b_items, probe["object_path"], probe["member"])
        require(av.get("status") == bv.get("status") == "resolved" and not av.get("stale") and not bv.get("stale"), "Probe is not currently resolved")
        require(av["type"] == bv["type"] and canonical_probe_type(av["type"]) == canonical_probe_type(probe["type"]),
                "Map output type/dimension differs")
        require([entry["key"] for entry in av["value"]] == probe["keys"] == sorted(probe["keys"]), "Map key cardinality/order/case differs")
        avalue, bvalue = semantic(av["value"], units), semantic(bv["value"], old_units)
        # A leaf's key is a provenance extension of .14, not part of the
        # explicit .13 typed data. The enclosing entry key remains compared.
        def leaf_keys(v):
            if isinstance(v, dict):
                return {k: leaf_keys(x) for k, x in v.items() if not (k == "key" and "type" in v)}
            return [leaf_keys(x) for x in v] if isinstance(v, list) else v
        require(leaf_keys(avalue) == leaf_keys(bvalue), "Complete typed leaf values differ from the separately authored explicit control")
        for entry in av["value"]:
            if "scalar_values" in probe:
                wanted = probe["scalar_values"][entry["key"]]
                got = entry["value"]["value"]
                require(got == wanted and (type(got) is type(wanted) or type(got) in (int, float) and type(wanted) in (int, float)), "Independent scalar answer differs")
                probes += 1
        require(transform_count > 0, "Authored map result lost its public derivation")
        check_keyed_leaf_provenance(av, units)
    if "widths_m" in case.get("expected", {}):
        wanted_transform = panel_transform(case, fixtures)
        for owner, widths in case["expected"]["widths_m"].items():
            value = member(a_items, owner, "widths")
            require(value["type"] == "Keyed<Length>" and {e["key"]: e["value"]["value"] for e in value["value"]} == widths, "Panel widths differ from independent source math")
            old_value = member(b_items, owner, "widths")
            require(old_value["type"] == "Keyed<Length>" and {e["key"]: e["value"]["value"] for e in old_value["value"]} == widths,
                    "Explicit control widths differ from independent source math")
            check_keyed_leaf_provenance(value, units, expected=wanted_transform)
            probes += len(widths)
    if "radii_m" in case.get("expected", {}):
        for path, radius in case["expected"]["radii_m"].items():
            value = member(a_items, path, "size")
            require(value["type"] == "Length" and value["value"] == radius, "Generated mapped radius differs")
            old_value = member(b_items, path, "size")
            require(old_value["type"] == "Length" and old_value["value"] == radius, "Explicit control radius differs")
            records = value.get("derived_transforms")
            check_transforms(records, units)
            require(records[-1].get("key") == path.rsplit('["', 1)[-1].split('"', 1)[0] and records[-1].get("input_entry") is not None,
                    "Generated member copy lost the original transformed leaf key/entry")
            probes += 1
    require(probes or "probe" in case or "radii_m" in case.get("expected", {}), "Valid source has no independently checked value probe")
    return {"status": "passed", "typed_probe": case.get("probe", {}).get("type"), "scalar_checks": probes,
            "source_locations": location_count, "derived_transform_records": transform_count,
            "control_program_revision": case["explicit_c080_control"]["program_revision"]}


def implementation_basis(repository):
    def aggregate(paths):
        chunks = []
        for path in paths:
            raw = ordinary_path(repository, path).read_bytes()
            require(len(raw) <= 262144, "Numeric identity component exceeds its finite bound")
            chunks.append(path.encode() + b"\0" + sha(raw).encode() + b"\n")
        return digest(b"".join(chunks))
    return {"source": {"name": "OntoKin controlled source poses", "version": "0.2",
        "implementation_sha256": aggregate(SOURCE_IMPLEMENTATION),
        "method": "ontokin.source-pose-projective-dyadic/0.2", "derivation_sha256": aggregate(SOURCE_DERIVATION)},
        "destination": {"implementation_sha256": digest(ordinary_path(repository, "tools/reach_destination.mjs").read_bytes()),
                        "derivation_sha256": digest(ordinary_path(repository, "docs/engineering/reach-destination-numerics.md").read_bytes())}}


def check_program_metadata(glb, case, fixtures, *, control=False):
    payload = case_payload(fixtures, case, control=control)
    revision, manifest = bundle_identity(payload)
    units = source_units(payload)
    meta = glb.document["extras"]["ontokin"]
    require(meta.get("target_contract") == ("ontokin.glb/0.13" if control else TARGET) and
            meta.get("schema_version") == ("0.13" if control else "0.14") and
            meta.get("profile") == ("textured-surfaces-0.1" if control else PROFILE), "GLB source/target contract mismatch")
    require(meta["source"]["uri"] == payload["entry"]["filename"] == "main.ok" and meta["source"]["entry_source_id"] == "entry" and
            meta["source"]["entry_revision"] == digest(units["entry"]["source"].encode()), "GLB source locator identity differs")
    program = meta["program"]
    require(program["revision"] == revision and program["manifest"] == manifest and program["entry_source_id"] == "entry", "GLB immutable program manifest differs")
    require(set(program["sources"]) == set(units), "GLB source unit set differs")
    for identity, unit in units.items():
        actual = program["sources"][identity]
        match = re.search(r'\bmodule\s+(\w+)\s*@\s*"([^"]+)"', unit["source"])
        require(match is not None, "Frozen source lacks literal module identity")
        expected = {"source_id": identity, "source_revision": digest(unit["source"].encode()), "filename": unit["filename"],
                    "package_id": unit.get("package_id"), "version": unit.get("version"), "module_name": match[1], "module_key": match[2]}
        require(actual == expected, "GLB source unit metadata differs")
    wanted_nodes = expected_occurrences(case)
    require(set(program["occurrences"]) == set(wanted_nodes) == set(glb.objects()), "GLB occurrence/path inventory differs")
    require(set(program["collections"]) == {"first.panels", "sibling.panels"}, "GLB generated collection inventory differs")
    transformed = panel_transform(case, fixtures)
    for owner in ("first", "sibling"):
        collection = program["collections"][owner + ".panels"]
        require(collection["owner_path"] == owner and collection["ordered_keys"] == ["left", "right"] and
                collection["element_id"] == ["panel-task", "demo", owner, "panels"], "Generated collection key/owner identity differs")
        require(set(collection["entries"]) == {"left", "right"}, "Generated entry set differs")
        for key, entry in collection["entries"].items():
            path = owner + '.panels["' + key + '"]'
            require(entry == {"path": path, "element_id": wanted_nodes[path]["element_id"]}, "Generated entry stable identity differs")
    for path, wanted in wanted_nodes.items():
        occurrence = program["occurrences"][path]
        require(occurrence["path"] == path and occurrence["element_id"] == wanted["element_id"] and
                occurrence["owner_path"] == wanted["owner"], "Ordinary/generated occurrence identity differs")
        node = glb.document["nodes"][glb.objects()[path]]
        identity = node["extras"]["ontokin"]
        require(identity["source_mapping"] == occurrence and identity["element_id"] == wanted["element_id"] and
                identity["program_revision"] == revision, "Native node lost its exact source mapping")
        generated = occurrence.get("generated")
        if "input_key" in wanted:
            key = wanted["input_key"]
            require(generated and generated["key"] == key and generated["collection_path"] == wanted["owner"] + ".panels" and
                    generated["unique_declaration_span"] is False, "Generated key provenance differs")
            if not control:
                same_location(generated["input_entry"], transformed["original_key_entries"][key], units)
                check_transforms(generated.get("input_transforms"), units, expected=transformed)
            else:
                require("input_transforms" not in generated, "Legacy generated occurrence acquired a new profile projection")
        else:
            require(generated is None, "Ordinary occurrence is mislabelled generated")
    count = check_all_locations(glb.document, units)
    basis = implementation_basis(fixtures["repository"])
    quantization = meta["reach_quantization"]
    require(quantization["source_numeric_bound_basis"] == basis["source"], "GLB source numeric identity is not the supplied source implementation")
    for name, value in basis["destination"].items():
        require(quantization["destination_numeric_bound_basis"][name] == value, "GLB destination numeric identity differs")
    require(quantization["position_tolerance_m"] <= .001 and quantization["rotation_tolerance_rad"] <= .001 and
            quantization["time_tolerance_s"] <= 1e-6, "Inherited recording tolerances were widened")
    return {"program_revision": revision, "source_locations": count, "generated_occurrences": 4, "ordinary_occurrences": 3}


def near(actual, expected, tolerance, message):
    require(len(actual) == len(expected) and all(math.isfinite(a) and abs(a-b) <= tolerance for a, b in zip(actual, expected)), message)


def check_geometry(glb, case):
    report, used_materials, used_textures, used_images = [], set(), set(), set()
    for path, wanted in expected_occurrences(case).items():
        primitives = glb.primitives(path)
        if wanted["empty"]:
            require(not primitives, "Empty source carrier acquired native geometry")
            continue
        require(len(primitives) == 3, "Rectangular extrusion lost its three material regions")
        corners = {struct.pack("<3f", *point) for point in wanted["raw_corner_set_m"]}
        actual_corners, counts, volume, area = set(), Counter(), 0., 0.
        center = [(a+b)/2 for a,b in zip(*wanted["local_bounds_m"])]
        for primitive in primitives:
            require(primitive.get("mode", 4) == 4 and set(primitive["attributes"]) in ({"POSITION", "NORMAL"}, {"POSITION", "NORMAL", "TEXCOORD_0"}), "Native primitive mode/stream set differs")
            region = primitive["extras"]["ontokin"]["region_key"]
            require(region in wanted["materials"], "Unknown material region")
            positions = glb.accessor(primitive["attributes"]["POSITION"])
            normals = glb.accessor(primitive["attributes"]["NORMAL"])
            indices = glb.accessor(primitive["indices"])
            require(len(positions) == len(normals) and len(indices) % 3 == 0 and indices, "Native geometry cardinality differs")
            require(all(type(i) is int and 0 <= i < len(positions) for i in indices), "Native triangle index is out of range")
            selected = set(indices)
            for i in selected:
                encoded = struct.pack("<3f", *positions[i]); actual_corners.add(encoded)
                require(encoded in corners, "Native vertex is absent from the independent source prism")
                require(abs(sum(n*n for n in normals[i])-1) <= 1e-6, "Native normal is not unit length")
            for offset in range(0, len(indices), 3):
                a,b,c = [positions[i] for i in indices[offset:offset+3]]
                ab, ac = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
                cross = [ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0]]
                magnitude = math.sqrt(sum(x*x for x in cross))
                require(magnitude > 0 and sum(cross[i]*((a[i]+b[i]+c[i])/3-center[i]) for i in range(3)) > 0, "Triangle is degenerate or inward wound")
                for i in indices[offset:offset+3]:
                    near(normals[i], [v/magnitude for v in cross], 1e-6, "Face normal disagrees with triangle winding")
                area += magnitude/2
                volume += sum(a[i] * [b[1]*c[2]-b[2]*c[1], b[2]*c[0]-b[0]*c[2], b[0]*c[1]-b[1]*c[0]][i] for i in range(3))/6
            counts[region] += len(indices)//3
            material_index = primitive["material"]; used_materials.add(material_index)
            material = glb.reference("materials", material_index)
            identity = material["extras"]["ontokin"]
            require(identity["occurrence_path"] == path and identity["source_region_key"] == region, "Material occurrence/region identity differs")
            pbr, wanted_material = material["pbrMetallicRoughness"], wanted["materials"][region]
            require(pbr["baseColorFactor"] == wanted_material["color"] and pbr["metallicFactor"] == wanted_material["metallic"] and
                    pbr["roughnessFactor"] == wanted_material["roughness"] and material.get("alphaMode", "OPAQUE") == "OPAQUE" and
                    not material.get("doubleSided", False), "Native linear material/opacity differs")
            binding = wanted["bindings"].get(region)
            if not binding:
                require("baseColorTexture" not in pbr and "TEXCOORD_0" not in primitive["attributes"], "Untextured region acquired texture coordinates/image")
                continue
            require(set(primitive["attributes"]) == {"POSITION", "NORMAL", "TEXCOORD_0"}, "Textured region lost its UV stream")
            texture_info = pbr["baseColorTexture"]
            require(texture_info.get("texCoord", 0) == 0, "Native texture selects another UV set")
            texture_index = texture_info["index"]; used_textures.add(texture_index)
            texture = glb.reference("textures", texture_index); used_images.add(texture["source"])
            require(glb.reference("samplers", texture["sampler"]) == SAMPLER, "Native sampler is not nearest/clamp")
            image = glb.reference("images", texture["source"])
            require(image["extras"]["ontokin"]["asset_id"] == binding["asset_id"], "Texture references another source image")
            uvs = glb.accessor(primitive["attributes"]["TEXCOORD_0"])
            require(len(uvs) == len(positions), "UV row count differs from geometry")
            for i, uv in enumerate(uvs):
                expected = exact_uv(positions[i], binding["mapping"]) if i in selected else (0.,0.)
                require(struct.pack("<2f", *uv) == struct.pack("<2f", *expected), "Native UV differs from exact rational source affine map")
        require(actual_corners == corners and dict(counts) == wanted["region_triangle_counts"], "Independent complete corner/region triangle inventory differs")
        require(abs(volume-wanted["volume_m3"]) <= 1e-12 and abs(area-wanted["surface_area_m2"]) <= 1e-12, "Independent closed-prism volume/area differs")
        report.append({"path": path, "triangles": sum(counts.values()), "corners": len(corners), "volume_m3": volume, "surface_area_m2": area})
    require(used_materials == set(range(len(glb.document["materials"]))) and used_textures == set(range(len(glb.document.get("textures", [])))) and
            used_images == set(range(len(glb.document.get("images", [])))), "Dangling material/texture/image resource")
    return report


def check_images(glb, payload):
    assets = {a["asset_id"]: base64.b64decode(a["data_base64"], validate=True) for a in payload["assets"]}
    require(len(glb.document["images"]) == len(assets) == 1, "Panel task has exactly one native image")
    report = []
    for image in glb.document["images"]:
        identity = image["extras"]["ontokin"]; name = identity["asset_id"]
        require(name in assets and image.get("name") == name and image["mimeType"] == "image/png" and "uri" not in image,
                "Embedded image identity/transport differs")
        raw = glb.view_bytes(image["bufferView"])
        require(raw == assets[name] and identity["sha256"] == digest(raw) and identity["byte_length"] == len(raw), "Embedded PNG bytes/digest differ from exact source attachment")
        png = decode_png(raw)
        report.append({"asset_id": name, "sha256": sha(raw), "bytes": len(raw), "width": png["width"], "height": png["height"], "decoded_sha256": png["decoded_sha256"]})
    return report


def check_motion(glb, case):
    nodes = expected_occurrences(case)
    require(len(glb.document["animations"]) == 1, "Missing unique recorded animation")
    streams = glb.animation_streams()
    require(set(streams) == {(path, kind) for path in nodes for kind in ("translation", "rotation")}, "Recorded pose stream inventory differs")
    observations = []
    for time in (0., .25, .5, .75, 1.):
        for path, node in nodes.items():
            pose = glb.pose(path, time)
            near(pose["translation"], [x + time*v for x,v in zip(node["origin"], node["velocity"])], .001, "Independent recorded rigid translation differs")
            near(pose["rotation"], [0,0,0,1], .001, "Independent recorded orientation differs")
        observations.append({"time_seconds": time, "objects": len(nodes)})
    return observations


def normalized_document(glb, payload, *, control=False):
    """Normalize only independently verified, explicitly source-derived fields.

    Each changed JSON path is recorded. All other data, including all unknown
    metadata, remains in the exact comparison. Broad removal of extras or all
    source records is deliberately forbidden.
    """
    units = source_units(payload)
    revision, manifest = bundle_identity(payload)
    changes = []
    profile = "textured-surfaces-0.1" if control else PROFILE
    source_hashes = {digest(u["source"].encode()): key for key, u in units.items()}
    def visit(value, path=(), parent=None):
        if isinstance(value, list):
            return [visit(v, path+(i,), value) for i,v in enumerate(value)]
        if not isinstance(value, dict):
            return value
        output = {}
        is_location = value.get("source_id") in units and (("start_byte" in value and "end_byte" in value) or ("start" in value and "end" in value))
        if is_location:
            check_location(value, units)
        for key, child in value.items():
            current, replacement, reason = path+(key,), child, None
            if key in ("input_transforms", "derived_transforms"):
                check_transforms(child, units)
                changes.append({"path": list(current), "kind": "adopted_map_derivation", "value_sha256": sha(canonical(child))})
                continue
            if key == "manifest" and path == ("extras", "ontokin", "program"):
                require(child == manifest, "Unexpected manifest while normalizing")
                replacement, reason = "<independently_bound_program_manifest>", "program_manifest"
            elif key in ("program_revision", "revision") and child == revision:
                replacement, reason = "<independently_bound_program_revision>", "program_revision"
            elif key in ("source_revision", "entry_revision") and child in source_hashes:
                replacement, reason = "<source_revision:"+source_hashes[child]+">", "source_revision"
            elif key == "filename" and value.get("source_id") in units:
                require(child == units[value["source_id"]]["filename"], "Unknown source filename normalization")
                replacement, reason = "<filename:"+value["source_id"]+">", "source_filename"
            elif is_location and key in ("start_byte", "end_byte", "start", "end"):
                replacement, reason = "<validated_source_byte_offset>", "source_location"
            elif current in (("extras", "ontokin", "target_contract"), ("animations", 0, "extras", "ontokin", "target_contract")):
                require(child == ("ontokin.glb/0.13" if control else TARGET), "Unexpected target")
                replacement, reason = "<explicit_profile_target>", "adopted_target"
            elif current == ("extras", "ontokin", "schema_version"):
                require(child == ("0.13" if control else "0.14"), "Unexpected source schema")
                replacement, reason = "<explicit_profile_schema>", "adopted_schema"
            elif current in (("extras", "ontokin", "profile"), ("extras", "ontokin", "reach_profile", "source_profile")):
                require(child == profile, "Unexpected profile binding")
                replacement, reason = "<explicit_source_profile>", "adopted_profile"
            if reason is not None:
                changes.append({"path": list(current), "kind": reason, "value_sha256": sha(canonical(child))})
                output[key] = replacement
            else:
                output[key] = visit(child, current, value)
        return output
    return visit(glb.document), changes


def json_differences(a, b, path=()):
    if type(a) is not type(b):
        return [{"path": list(path), "actual": a, "control": b}]
    if isinstance(a, dict):
        result = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                result.append({"path": list(path+(key,)), "actual": a.get(key), "control": b.get(key)})
            else:
                result.extend(json_differences(a[key], b[key], path+(key,)))
        return result
    if isinstance(a, list):
        if len(a) != len(b):
            return [{"path": list(path), "actual_length": len(a), "control_length": len(b)}]
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in json_differences(x,y,path+(i,))]
    return [] if a == b else [{"path": list(path), "actual": a, "control": b}]


def check_identity(glb, old, case, fixtures):
    require(glb.binary == old.binary, "Complete BIN chunk differs from explicit .13 source control")
    for field in ("accessors", "bufferViews", "buffers"):
        require(glb.document[field] == old.document[field], "Complete accessor/buffer layout differs from explicit control: " + field)
    accessors = []
    for index in range(len(glb.document["accessors"])):
        require(glb.accessor(index) == old.accessor(index) and glb.accessor_bytes(index) == old.accessor_bytes(index), "Decoded accessor differs from explicit control")
        accessors.append({"index": index, "sha256": sha(glb.accessor_bytes(index)), "count": glb.document["accessors"][index]["count"]})
    require(glb.geometry_streams() == old.geometry_streams() and glb.animation_streams() == old.animation_streams(), "Occurrence-bound geometry/motion streams differ")
    new_json, new_changes = normalized_document(glb, case_payload(fixtures, case))
    old_json, old_changes = normalized_document(old, case_payload(fixtures, case, control=True), control=True)
    differences = json_differences(new_json, old_json)
    require(not differences, "Unpermitted identity-control JSON differences: " + str(differences[:4]))
    return {"complete_bin_sha256": sha(glb.binary), "complete_bin_bytes": len(glb.binary), "accessors": accessors,
        "actual_permitted_json_fields": new_changes, "control_permitted_json_fields": old_changes,
        "unpermitted_json_differences": [], "comparison": "full BIN, complete decoded accessors, occurrence-bound streams and all JSON after explicit validated source deltas"}


def check_artifact(raw, case, fixtures, control):
    require(case["name"] in DELIVERED_CASES, "Artifact outside frozen delivered-stage scope")
    glb, old = GLB(raw, target=TARGET), GLB(control, target="ontokin.glb/0.13")
    source = check_program_metadata(glb, case, fixtures)
    baseline = check_program_metadata(old, case, fixtures, control=True)
    geometry = check_geometry(glb, case)
    images = check_images(glb, case_payload(fixtures, case))
    motion = check_motion(glb, case)
    identity = check_identity(glb, old, case, fixtures)
    return {"case": case["name"], "status": "passed", "sha256": sha(raw), "bytes": len(raw), "source": source,
            "control_source": baseline, "geometry": geometry, "images": images, "motion": motion, "identity": identity}
