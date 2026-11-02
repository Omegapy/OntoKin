"""Independent C087 source-role and whole-delivery byte comparison.

Expected source roles are reconstructed from original literal annotations and
byte delimiters. The panel dimensions, motion and PNG come from the published
input freeze. No produced artifact is used to author an expected answer.
"""
from __future__ import annotations
import copy
import json
import re
import struct

from tools.string_concat_reference import (
    GLB, TARGET, PROFILE, DELIVERED_CASES, require, sha, digest, canonical,
    bundle_identity, case_payload, source_units, expected_occurrences,
    check_geometry, check_images, check_motion, implementation_basis,
    check_all_locations, check_rekeys, check_zips, check_merges, check_location,
    exact_location, exact_public_location, original_keyed_entries, intrinsic_locations, merge_source_shape,
    zip_source_shape, rekey_source_shape, json_differences, compact_json_bytes,
    check_raw_framing, _source_tokens, _closing_delimiter, _location_identity,
)

PANEL_UNIT = "package:fixture.rekey-panels@1.0.0"
CATALOG_UNIT = "package:fixture.rekey-catalog@1.0.0"


def location(units, source_id, start, end):
    unit = units[source_id]
    return {"source_id": source_id, "source_revision": digest(unit["source"].encode()),
            "filename": unit["filename"], "start_byte": start, "end_byte": end}


def declaration(units, source_id, kind, name):
    raw = units[source_id]["source"].encode()
    pattern = rb"(?:public\s+)?" + kind.encode() + rb"\s+" + re.escape(name.encode()) + rb"\s*@\s*\"([^\"]+)\""
    matches = list(re.finditer(pattern, raw))
    require(len(matches) == 1, "Ambiguous original declaration: " + name)
    match = matches[0]
    tokens = _source_tokens(raw[match.start():])
    opening = next(index for index, token in enumerate(tokens) if token[0] == b"{")
    closing = _closing_delimiter(tokens, opening)
    return location(units, source_id, match.start(), match.start() + tokens[closing][2]), match[1].decode()


def call_location(units, source_id, name):
    raw = units[source_id]["source"].encode(); tokens = _source_tokens(raw)
    indices = [index for index, token in enumerate(tokens[:-1]) if token[0] == name.encode() and tokens[index+1][0] == b"("]
    require(len(indices) == 1, "Ambiguous original source call: " + name)
    start = indices[0]; end = _closing_delimiter(tokens, start + 1)
    return location(units, source_id, tokens[start][1], tokens[end][2])


def enriched(record, units, fields):
    return {**record, **{field: None if record[field] is None else
            {**record[field], "filename": units[record[field]["source_id"]]["filename"]}
            for field in fields}}


def panel_sources(case, fixtures, *, control=False):
    units = source_units(case_payload(fixtures, case, control=control))
    module = re.search(r'\bmodule\s+PanelTask\s*@\s*"([^"]+)"', units["entry"]["source"])
    scene = re.search(r'\bscene\s+Demo\s*@\s*"([^"]+)"', units["entry"]["source"])
    require(module and scene and module[1] == "panel-task" and scene[1] == "demo",
            "Frozen occurrence root annotations differ")
    group, group_key = declaration(units, PANEL_UNIT, "class", "PanelGroup")
    panel, panel_key = declaration(units, PANEL_UNIT, "class", "Panel")
    parts, parts_key = declaration(units, PANEL_UNIT, "parts", "panels")
    part_raw = check_location(parts, units)
    match = re.search(rb'\bin\s+(self\.renamed)\s*\{', part_raw)
    require(match is not None, "Generated input lost the original renamed member read")
    input_location = location(units, PANEL_UNIT, parts["start_byte"] + match.start(1), parts["start_byte"] + match.end(1))
    declarations = {}
    object_keys = {}
    for name in ("first", "sibling", "marker"):
        declarations[name], object_keys[name] = declaration(units, "entry", "object", name)
        require(name == object_keys[name], "Frozen object annotation differs")
    result = {"units": units, "root_id": [module[1], scene[1]], "declarations": declarations,
        "group_definition": group, "panel_definition": panel, "parts_declaration": parts,
        "group_id": ["package", "fixture.rekey-panels", "panels", "definitions", group_key],
        "panel_id": ["package", "fixture.rekey-panels", "panels", "definitions", panel_key],
        "parts_key": parts_key, "input": input_location, "panel_geometry": call_location(units, PANEL_UNIT, "extrude"),
        "marker_geometry": call_location(units, "entry", "extrude"),
        "texture_binding": call_location(units, PANEL_UNIT, "texture_binding"),
        "planar_uv": call_location(units, PANEL_UNIT, "planar_uv")}
    entries = original_keyed_entries(units)
    for role, source_id, element_type in (("catalog", CATALOG_UNIT, "String"),
            ("dimensions", "package:fixture.pair-dimensions@1.0.0", "Length"),
            ("finishes", "package:fixture.pair-finishes@1.0.0", "SurfaceMaterial")):
        calls = intrinsic_locations({source_id: units[source_id]}, b"merge_keyed")
        require(len(calls) == 1, "Frozen source merge inventory differs: " + role)
        shape = merge_source_shape(calls[0], units)
        record = enriched({"expression": calls[0], **shape["parts"], "element_type": element_type,
                           "input_side": "both"}, units, ("expression", "left", "right"))
        check_merges([record], units)
        contributors = {}
        for side in ("left", "right"):
            operand = record[side]
            matches = [entry for entry in entries.values() if entry["location"]["source_id"] == source_id and
                operand["start_byte"] <= entry["location"]["start_byte"] < entry["location"]["end_byte"] <= operand["end_byte"]]
            require(len(matches) == 1, "Each authored merge side has one original leaf")
            item = matches[0]
            contributors[item["key"]] = {"entry": {**item["location"], "filename": units[source_id]["filename"]}, "side": side}
        require(set(contributors) == {"left", "right"}, "Authored merge input keys differ")
        result[role] = {"record": record, "contributors": contributors}
    calls = intrinsic_locations({PANEL_UNIT: units[PANEL_UNIT]}, b"zip_keyed")
    require(len(calls) == 1, "Panel has exactly one inherited zip")
    shape = zip_source_shape(calls[0], units)
    zip_record = {"expression": calls[0], **shape["parts"],
        "left_element_type": "String", "right_element_type": "String", "output_element_type": "String",
        "key": None, "left_entry": None, "right_entry": None}
    result["zip"] = enriched(zip_record, units, ("expression", "left", "right", "body", "left_entry", "right_entry"))
    check_zips([result["zip"]], units, aggregate=True)
    calls = intrinsic_locations({PANEL_UNIT: units[PANEL_UNIT]}, b"rekey_keyed")
    require(len(calls) == 1, "Panel has exactly one inherited rekey")
    expression = {**calls[0], "filename": units[PANEL_UNIT]["filename"]}
    shape = rekey_source_shape(expression, units)
    require(shape["binders"] == ["old_name", "original_name"] and shape["element_type"] == "String",
            "Authored panel rekey binder/type roles differ")
    record = {"expression": expression, **shape["parts"], "element_type": "String",
              "old_key": None, "new_key": None, "input_entry": None}
    check_rekeys([record], units, aggregate=True)
    result["rekey"] = record
    # Each source override is independently located within its authored object
    # declaration. A default retains the original catalog merge contributors;
    # reordered/inserted/removed first-member literals retain their own entries.
    result["owner_entries"], result["owner_merged"] = {}, {}
    for owner in ("first", "sibling"):
        span = declarations[owner]
        selected = [entry for entry in entries.values() if entry["location"]["source_id"] == "entry" and
            span["start_byte"] < entry["location"]["start_byte"] < entry["location"]["end_byte"] < span["end_byte"]]
        authored = case["first_members_in_authored_order"] if owner == "first" else case["sibling_members"]
        if selected:
            selected.sort(key=lambda entry: entry["location"]["start_byte"])
            require([entry["key"] for entry in selected] == authored, "Authored member override inventory differs")
            result["owner_entries"][owner] = {entry["key"]: {**entry["location"], "filename": units["entry"]["filename"]}
                                               for entry in selected}
            result["owner_merged"][owner] = False
        else:
            require(set(authored) == set(result["catalog"]["contributors"]), "Default catalog member inventory differs")
            result["owner_entries"][owner] = {key: item["entry"] for key,item in result["catalog"]["contributors"].items()}
            result["owner_merged"][owner] = True
    return result


def old_key_for(path):
    key = json.loads(path.split("[", 1)[1][:-1])
    prefix, separator, old = key.partition(".")
    require(separator and prefix in ("front", "back", "repair") and old in ("left", "middle", "right"),
            "Unknown frozen computed key")
    return old


def primary_panel_entry(case, fixtures, path, *, control=False, sources=None):
    sources = sources or panel_sources(case, fixtures, control=control)
    return sources["owner_entries"][path.split(".",1)[0]][old_key_for(path)]


def panel_rekey_records(sources, path=None):
    result = [copy.deepcopy(sources["rekey"])]
    if path is not None:
        old = old_key_for(path); new = json.loads(path.split("[", 1)[1][:-1])
        result.append(dict(sources["rekey"], old_key=old, new_key=new,
                           input_entry=sources["owner_entries"][path.split(".",1)[0]][old]))
    return result


def panel_zip_records(sources, path=None):
    result = [copy.deepcopy(sources["zip"])]
    if path is not None:
        key = old_key_for(path); entry = sources["owner_entries"][path.split(".",1)[0]][key]
        result.append(dict(sources["zip"], key=key, left_entry=entry, right_entry=entry))
    return result


def panel_merge_records(sources, owner):
    # Inherited .18 zip admits both aggregate inputs, then every old-key leaf.
    # Both calls name the same source merge, so whole-record dedup keeps one
    # aggregate and its canonical left-key/right-key contributors in that order.
    if not sources["owner_merged"][owner.split(".",1)[0]]:
        return []
    catalog = sources["catalog"]
    return [catalog["record"]] + [dict(catalog["record"], input_side=catalog["contributors"][key]["side"])
                                  for key in ("left", "right")]


def expected_source_projection(case, fixtures, *, control=False):
    sources = panel_sources(case, fixtures, control=control)
    occurrences, collections = {}, {}
    nodes = expected_occurrences(case)
    for path, wanted in nodes.items():
        generated = "input_key" in wanted
        owner = wanted["owner"]
        root = owner if generated else path
        definition_id = sources["panel_id"] if generated else sources["group_id"] if path != "marker" else ["@system", "Object"]
        class_id = "/".join(definition_id) if path != "marker" else "Object"
        declaration_location = sources["parts_declaration"] if generated else sources["declarations"][path]
        definition_location = sources["panel_definition"] if generated else sources["group_definition"] if path != "marker" else None
        steps = [{"kind": "member", "value": root}]
        if generated:
            steps += [{"kind": "member", "value": "panels"}, {"kind": "key", "value": wanted["input_key"]}]
        mapping = {"path": path, "element_id": wanted["element_id"], "owner_path": owner, "root_path": root,
            "path_steps": steps, "definition_id": definition_id, "class_id": class_id,
            "declaration": declaration_location, "definition": definition_location,
            "declaration_definition_id": sources["group_id"] + [sources["parts_key"]] if generated else None,
            "generated": None, "generated_ancestor": path if generated else None}
        if generated:
            detail = {"collection_path": owner + ".panels", "collection_id": sources["root_id"] + [owner, "panels"],
                "collection_definition_id": sources["group_id"] + ["panels"], "key": wanted["input_key"],
                "input": sources["input"], "input_entry": primary_panel_entry(case, fixtures, path, control=control, sources=sources),
                "unique_declaration_span": False}
            detail.update(input_rekeys=panel_rekey_records(sources, path), input_zips=panel_zip_records(sources, path))
            merges = panel_merge_records(sources, owner)
            if merges:
                detail["input_merges"] = merges
            mapping["generated"] = detail
        occurrences[path] = mapping
    for owner in ("first", "sibling"):
        keys = sorted(case["expected"]["widths_m"][owner])
        path = owner + ".panels"
        collections[path] = {"path": path, "name": "panels", "element_id": sources["root_id"] + [owner, "panels"],
            "owner_path": owner, "definition_id": sources["group_id"] + ["panels"],
            "declaration": sources["parts_declaration"], "input": sources["input"], "ordered_keys": keys,
            "entries": {key: {"path": owner + '.panels[' + json.dumps(key) + ']',
                "element_id": sources["root_id"] + [owner, "panels", key]} for key in keys},
            "physical_participation": "none"}
    return {"sources": sources, "occurrences": occurrences, "collections": collections}


def check_program_metadata(glb, case, fixtures, *, control=False):
    payload = case_payload(fixtures, case, control=control)
    revision, manifest = bundle_identity(payload); units = source_units(payload)
    meta = glb.document["extras"]["ontokin"]
    target, version, profile = ("ontokin.glb/0.19", "0.19", "keyed-rekey-0.1") if control else (TARGET, "0.20", PROFILE)
    require(meta["target_contract"] == target and meta["schema_version"] == version and meta["profile"] == profile,
            "Artifact target/source binding differs")
    require(meta["source"]["uri"] == payload["entry"]["filename"] == "main.ok" and
            meta["source"]["entry_source_id"] == "entry" and
            meta["source"]["entry_revision"] == digest(units["entry"]["source"].encode()),
            "Artifact original entry locator differs")
    program = meta["program"]
    require(program["revision"] == revision and program["manifest"] == manifest and program["entry_source_id"] == "entry",
            "Artifact immutable source manifest differs")
    require(set(program["sources"]) == set(units), "Artifact source unit inventory differs")
    for source_id, unit in units.items():
        match = re.search(r'\bmodule\s+(\w+)\s*@\s*"([^"]+)"', unit["source"])
        require(match is not None, "Original source lost literal module identity")
        expected = {"source_id": source_id, "source_revision": digest(unit["source"].encode()),
            "filename": unit["filename"], "package_id": unit.get("package_id"), "version": unit.get("version"),
            "module_name": match[1], "module_key": match[2]}
        require(program["sources"][source_id] == expected, "Artifact original source unit identity differs")
    wanted = expected_source_projection(case, fixtures, control=control)
    require(program["occurrences"] == wanted["occurrences"],
            "Exact generated/ordinary source projection differs: " + str(json_differences(program["occurrences"], wanted["occurrences"])[:2]))
    require(program["collections"] == wanted["collections"], "Exact generated source collection projection differs")
    require(set(glb.objects()) == set(wanted["occurrences"]), "Native occurrence inventory differs")
    for path, index in glb.objects().items():
        node = glb.document["nodes"][index]["extras"]["ontokin"]
        require(node["source_mapping"] == wanted["occurrences"][path] and
                node["element_id"] == wanted["occurrences"][path]["element_id"] and
                node["program_revision"] == revision, "Node/source projection differs")
    count = check_all_locations(glb.document, units)
    basis = implementation_basis(fixtures.get("control_basis_repository" if control else "basis_repository", fixtures["repository"]))
    quantization = meta["reach_quantization"]
    require(quantization["source_numeric_bound_basis"] == basis["source"], "Source numeric basis identity differs")
    for name, value in basis["destination"].items():
        require(quantization["destination_numeric_bound_basis"][name] == value, "Destination numeric basis identity differs")
    require(quantization["position_tolerance_m"] <= .001 and quantization["rotation_tolerance_rad"] <= .001 and
            quantization["time_tolerance_s"] <= 1e-6, "Recording tolerances widened")
    return {"program_revision": revision, "source_locations": count, "ordinary_occurrences": 3,
            "generated_occurrences": len(case["expected"]["panels"])}


def _mapping_tail(path):
    if len(path) >= 5 and path[0] == "nodes" and type(path[1]) is int and path[2:5] == ("extras", "ontokin", "source_mapping"):
        return path[5:]
    if len(path) >= 5 and path[:4] == ("extras", "ontokin", "program", "occurrences"):
        return path[5:]
    return None


def _source_role(path, glb, projection):
    """Return one exact independently derived location for an allowed path."""
    sources = projection["sources"]
    tail = _mapping_tail(path)
    if tail is not None:
        name = glb.document["nodes"][path[1]]["extras"]["ontokin"]["path"] if path[0] == "nodes" else path[4]
        expected = projection["occurrences"][name]
        if tail in (("declaration",), ("definition",)):
            return expected[tail[0]], "source:" + name + ":" + tail[0]
        if tail in (("generated", "input"), ("generated", "input_entry")):
            return expected["generated"][tail[1]], "source:" + name + ":" + tail[1]
    if len(path) == 6 and path[:4] == ("extras", "ontokin", "program", "collections") and path[5] in ("declaration", "input"):
        return projection["collections"][path[4]][path[5]], "source:" + path[4] + ":" + path[5]
    if len(path) >= 5 and path[0] == "nodes" and type(path[1]) is int and path[2:4] == ("extras", "ontokin"):
        name = glb.document["nodes"][path[1]]["extras"]["ontokin"]["path"]
        tail = path[4:]
        if name in ("first", "sibling"):
            return None
        geometry = sources["marker_geometry"] if name == "marker" else sources["panel_geometry"]
        if tail in (("geometry",), ("surface", "source_location")):
            return geometry, "source:" + name + ":geometry"
        if name != "marker" and tail == ("geometry", "texture_bindings", 0, 1):
            return sources["texture_binding"], "source:" + name + ":texture_binding"
        if name != "marker" and tail == ("geometry", "texture_bindings", 0, 1, "mapping"):
            return sources["planar_uv"], "source:" + name + ":planar_uv"
    return None


def normalized_document(glb, payload, *, case, fixtures, control=False):
    """Only enumerated and individually checked metadata fields may differ."""
    units = source_units(payload); revision, manifest = bundle_identity(payload)
    projection = expected_source_projection(case, fixtures, control=control)
    source_hashes = {digest(unit["source"].encode()): source_id for source_id, unit in units.items()}
    changes = []
    def visit(value, path=()):
        if isinstance(value, list):
            return [visit(child, path + (index,)) for index, child in enumerate(value)]
        if not isinstance(value, dict):
            return value
        role = _source_role(path, glb, projection)
        if role and role[0] is not None:
            expected, label = role
            require(value.get("source_id") == expected["source_id"], "Allowed source role names another source")
            if "start_byte" in value:
                require(value["start_byte"] == expected["start_byte"] and value["end_byte"] == expected["end_byte"],
                        "Allowed source location differs from exact original role")
            else:
                require(value["start"] == expected["start_byte"] and value["end"] == expected["end_byte"],
                        "Allowed geometry/mapping source location differs")
            if "source_revision" in value:
                require(value["source_revision"] == expected["source_revision"], "Allowed location revision differs")
            if "filename" in value:
                require(value["filename"] == expected["filename"], "Allowed location filename differs")
        output = {}
        for key, child in value.items():
            current = path + (key,); replacement, reason = child, None
            if key.startswith("input_") and _mapping_tail(path) == ("generated",) and key in (
                    "input_rekeys", "input_zips", "input_merges", "input_filters", "input_transforms", "input_reductions"):
                name = glb.document["nodes"][path[1]]["extras"]["ontokin"]["path"] if path[0] == "nodes" else path[4]
                expected = projection["occurrences"][name]["generated"]
                require(key in expected and child == expected[key], "Inherited/current generated origin differs before replacement")
                changes.append({"path": list(current), "kind": "validated_" + key, "value_sha256": sha(canonical(child))})
                continue
            if role and role[0] is not None and key in ("source_id", "source_revision", "filename", "start", "end", "start_byte", "end_byte"):
                replacement = "<" + role[1] + ":" + key + ">"; reason = "exact_original_source_role"
            elif current == ("extras", "ontokin", "program", "manifest"):
                require(child == manifest, "Unvalidated program manifest replacement")
                replacement, reason = "<exact_original_bundle_manifest>", "bundle_manifest"
            elif current == ("extras", "ontokin", "program", "revision") or (
                    len(path) == 4 and path[0] in ("nodes", "materials", "images") and type(path[1]) is int and
                    path[2:] == ("extras", "ontokin") and key == "program_revision"):
                require(child == revision, "Unvalidated program revision replacement")
                replacement, reason = "<exact_original_bundle_revision>", "bundle_revision"
            elif current == ("extras", "ontokin", "source", "entry_revision"):
                require(child == digest(units["entry"]["source"].encode()), "Unvalidated entry revision replacement")
                replacement, reason = "<exact_original_entry_revision>", "entry_revision"
            elif len(path) == 5 and path[:4] == ("extras", "ontokin", "program", "sources") and key in ("source_revision", "filename"):
                source_id = path[4]
                wanted = digest(units[source_id]["source"].encode()) if key == "source_revision" else units[source_id]["filename"]
                require(child == wanted, "Unvalidated original unit identity replacement")
                replacement, reason = "<source:" + source_id + ":" + key + ">", "source_unit_identity"
            elif current in (("extras", "ontokin", "target_contract"), ("animations", 0, "extras", "ontokin", "target_contract")):
                require(child == ("ontokin.glb/0.19" if control else TARGET), "Unvalidated target replacement")
                replacement, reason = "<explicit_target>", "explicit_target"
            elif current == ("extras", "ontokin", "schema_version"):
                require(child == ("0.19" if control else "0.20"), "Unvalidated source schema replacement")
                replacement, reason = "<explicit_schema>", "explicit_schema"
            elif current in (("extras", "ontokin", "profile"), ("extras", "ontokin", "reach_profile", "source_profile")):
                require(child == ("keyed-rekey-0.1" if control else PROFILE), "Unvalidated profile replacement")
                replacement, reason = "<explicit_profile>", "explicit_profile"
            elif current in (("extras", "ontokin", "reach_quantization", "source_numeric_bound_basis", "implementation_sha256"),
                             ("extras", "ontokin", "reach_quantization", "destination_numeric_bound_basis", "implementation_sha256")):
                basis = implementation_basis(fixtures.get("control_basis_repository" if control else "basis_repository", fixtures["repository"]))
                kind = "source" if path[-1] == "source_numeric_bound_basis" else "destination"
                require(child == basis[kind]["implementation_sha256"], "Unvalidated implementation fingerprint replacement")
                replacement, reason = "<independently_computed_" + kind + "_implementation>", "implementation_fingerprint"
            if reason:
                changes.append({"path": list(current), "kind": reason, "value_sha256": sha(canonical(child))})
                output[key] = replacement
            else:
                output[key] = visit(child, current)
        return output
    return visit(glb.document), changes


def check_identity(glb, old, case, fixtures):
    framing, old_framing = check_raw_framing(glb), check_raw_framing(old)
    require(glb.binary == old.binary, "Complete BIN chunk differs from explicit .19 control")
    for key in ("accessors", "bufferViews", "buffers"):
        require(glb.document[key] == old.document[key], "Complete native buffer layout differs: " + key)
    accessors = []
    for index in range(len(glb.document["accessors"])):
        require(glb.accessor(index) == old.accessor(index) and glb.accessor_bytes(index) == old.accessor_bytes(index),
                "Complete decoded/raw accessor differs")
        accessors.append({"index": index, "bytes": len(glb.accessor_bytes(index)), "sha256": sha(glb.accessor_bytes(index))})
    require(glb.geometry_streams() == old.geometry_streams() and glb.animation_streams() == old.animation_streams(),
            "Occurrence-bound geometry/motion streams differ")
    actual, actual_changes = normalized_document(glb, case_payload(fixtures, case), case=case, fixtures=fixtures)
    control, control_changes = normalized_document(old, case_payload(fixtures, case, control=True), case=case, fixtures=fixtures, control=True)
    differences = json_differences(actual, control)
    require(not differences, "Unpermitted complete JSON differences: " + str(differences[:4]))
    raw, old_raw = compact_json_bytes(actual), compact_json_bytes(control)
    require(raw == old_raw, "Raw JSON member order/encoding differs after permitted replacements")
    return {"complete_bin_sha256": sha(glb.binary), "complete_bin_bytes": len(glb.binary),
        "accessors": accessors, "actual_raw_framing": framing, "control_raw_framing": old_framing,
        "normalized_json_sha256": sha(raw), "normalized_json_bytes": len(raw),
        "actual_permitted_json_fields": actual_changes, "control_permitted_json_fields": control_changes,
        "unpermitted_json_differences": [], "comparison": "Complete BIN, all raw accessors, occurrence-bound geometry/motion, exact compact JSON member order and framing after individually source-validated enumerated metadata replacements"}


def check_artifact(raw, case, fixtures, control):
    require(case["name"] in DELIVERED_CASES, "Artifact outside frozen delivery scope")
    glb, old = GLB(raw, target=TARGET), GLB(control, target="ontokin.glb/0.19")
    source = check_program_metadata(glb, case, fixtures)
    old_source = check_program_metadata(old, case, fixtures, control=True)
    geometry = check_geometry(glb, case); images = check_images(glb, case_payload(fixtures, case))
    motion = check_motion(glb, case); identity = check_identity(glb, old, case, fixtures)
    return {"case": case["name"], "status": "passed", "sha256": sha(raw), "bytes": len(raw),
            "source": source, "control_source": old_source, "geometry": geometry, "images": images,
            "motion": motion, "identity": identity}


def check_panel_values(items, case, fixtures, units=None, *, control=False):
    from tools.string_concat_reference import inspect_member, check_keyed_membership, semantic_value
    sources = panel_sources(case, fixtures, control=control); units = units or sources["units"]
    checks = 0
    for owner in ("first", "sibling"):
        dimensions = inspect_member(items, owner, "dimensions")
        require(dimensions["type"] == "Keyed<Length>", "Panel dimension type differs")
        checks += check_keyed_membership(dimensions, ["left", "middle", "right"], scalars={"left": 1, "middle": 1.5, "right": 2})
        finishes = inspect_member(items, owner, "finishes")
        require(finishes["type"] == "Keyed<SurfaceMaterial>", "Panel material type differs")
        checks += check_keyed_membership(finishes, ["left", "middle", "right"])
        for entry in finishes["value"]:
            require(entry["value"]["value"] == [[.25, .5, .75, 1], 0, .7], "Panel finish differs from authored material")
        mounts = inspect_member(items, owner, "mounts")
        checks += check_keyed_membership(mounts, ["left", "middle", "right"], scalars={"left": 0, "middle": 2, "right": 4})
        prefix = inspect_member(items, owner, "prefix")
        require(prefix["type"] == "String" and prefix["value"] == case[owner+"_prefix"], "Resolved prefix differs from authored source")
        old_keys = sorted(case["first_members_in_authored_order"] if owner == "first" else case["sibling_members"])
        members = inspect_member(items, owner, "member_names")
        checks += check_keyed_membership(members, old_keys, scalars={key:key for key in old_keys})
        original = inspect_member(items, owner, "original_members")
        require(original["type"] == "Keyed<String>", "Original member payload type differs")
        checks += check_keyed_membership(original, old_keys, scalars={key:key for key in old_keys})
        check_zips(original.get("derived_zips", []), units, expected=[sources["zip"]], exact=True, aggregate=True)
        expected_merges = panel_merge_records(sources, owner)
        if expected_merges:
            check_merges(original.get("derived_merges", []), units, expected=expected_merges, exact=True)
        else:
            require(not original.get("derived_merges"), "Literal source override acquired catalog merge origins")
        require("derived_rekeys" not in original, "Original member aggregate was contaminated by renamed output")
        renamed = inspect_member(items, owner, "renamed")
        keys = sorted(case["expected"]["widths_m"][owner])
        payloads = dict(case["expected_keyed_values"][owner+".renamed"]["entries"])
        require(renamed["type"] == "Keyed<String>", "Renaming changed immutable payload type")
        checks += check_keyed_membership(renamed, keys, scalars=payloads)
        check_rekeys(renamed.get("derived_rekeys", []), units, expected=panel_rekey_records(sources), exact=True, aggregate=True)
        check_zips(renamed.get("derived_zips", []), units, expected=[sources["zip"]], exact=True, aggregate=True)
        if expected_merges:
            check_merges(renamed.get("derived_merges", []), units, expected=expected_merges, exact=True)
        else:
            require(not renamed.get("derived_merges"), "Literal source override acquired catalog merge origins")
        dependencies = copy.deepcopy(case["expected_renamed_inspection_dependencies"][owner]["dependencies"])
        if control:
            for dependency in dependencies:
                dependency["program_revision"] = case["explicit_c086_control"]["program_revision"]
        require(renamed.get("dependencies") == dependencies, "Complete actual prefix/member/definition dependencies differ")
        for entry in renamed["value"]:
            path = owner + '.panels[' + json.dumps(entry["key"]) + ']'
            leaf = entry["value"]
            check_rekeys(leaf.get("derived_rekeys", []), units, expected=panel_rekey_records(sources, path), exact=True)
            check_zips(leaf.get("derived_zips", []), units, expected=panel_zip_records(sources, path), exact=True)
        selected = inspect_member(items, owner, "selected_total")
        require(selected["type"] == "Length" and selected["value"] == 4.5 and "derived_rekeys" not in selected,
                "Unrelated dimension reduction changed or acquired rekey origins")
        checks += 1
    objects = {item["path"]: item for item in items if item.get("kind") == "object"}
    require(len(objects) == case["expected"]["object_count"] and set(objects) == set(expected_occurrences(case)), "Public occurrence inventory differs")
    for path, wanted in expected_occurrences(case).items():
        item = objects[path]
        require(item["element_id"] == wanted["element_id"], "Public generated identity does not follow computed key")
        generated = item.get("source", {}).get("generated")
        if "input_key" not in wanted:
            require(not generated, "Ordinary object acquired generated identity")
            continue
        require(generated and generated["input_key"] == wanted["input_key"] and generated["unique_declaration_span"] is False,
                "Public generated key/readonly source identity differs")
        exact_public_location(generated["input_entry_span"], primary_panel_entry(case, fixtures, path, control=control, sources=sources), units)
        check_rekeys(generated.get("input_rekeys", []), units, expected=panel_rekey_records(sources, path), exact=True)
        check_zips(generated.get("input_zips", []), units, expected=panel_zip_records(sources, path), exact=True)
        expected_merges = panel_merge_records(sources, path)
        if expected_merges:
            check_merges(generated.get("input_merges", []), units, expected=expected_merges, exact=True)
        else:
            require(not generated.get("input_merges"), "Literal source override acquired generated catalog merge origins")
        width = inspect_member(items, path, "width")
        coat = inspect_member(items, path, "coat")
        require(width["type"] == "Length" and width["value"] == wanted["width_m"] and
                coat["type"] == "SurfaceMaterial" and coat["value"] == [[.25, .5, .75, 1], 0, .7],
                "Renaming changed generated panel dimensions/material payload")
        checks += 2
    return checks


def check_agent_inspection(actual, control, case, fixtures):
    from tools.string_concat_reference import check_origin_projection, codes, inspect_member, semantic_value
    units = source_units(case_payload(fixtures, case)); old_units = source_units(case_payload(fixtures, case, control=True))
    require(actual.get("program_revision") == case["program_revision"] and
            control.get("program_revision") == case["explicit_c086_control"]["program_revision"], "Agent source inspection revision differs")
    require(not any(code.startswith(("OKL-E-", "OKE-E-")) for code in codes(actual) + codes(control)), "Panel source/control inspection failed")
    counts = check_origin_projection(actual, units); check_origin_projection(control, old_units)
    count = check_panel_values(actual["items"], case, fixtures, units)
    count += check_panel_values(control["items"], case, fixtures, old_units, control=True)
    for path in expected_occurrences(case):
        members = ("prefix", "member_names", "left_width", "warm_finish", "dimensions", "finishes", "mounts", "original_members", "renamed", "selected_total") if path in ("first", "sibling") else ("width", "coat", "mount_x") if "panels[" in path else ()
        for name in members:
            value = inspect_member(actual["items"], path, name); previous = inspect_member(control["items"], path, name)
            require(value["type"] == previous["type"] and semantic_value(value["value"], units) == semantic_value(previous["value"], old_units),
                    "Complete authored panel typed property differs from literal .19 control")
    return {"status": "passed", "typed_checks": count, "origin_records": counts,
            "source_locations": check_all_locations(actual, units) + check_all_locations(control, old_units)}
