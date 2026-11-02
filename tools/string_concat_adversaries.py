"""Isolated hostile changes to actual supplied .20 GLBs, never expected answers.

Targets and applicability come from the frozen C087 supplied-byte contract.
The two native generated-lineage projections are changed together so lineage
adversaries cannot pass merely by being caught as a duplicate-copy mismatch.
"""
from __future__ import annotations

import copy
import json
import struct

from tools.string_concat_reference import GLB, TARGET, require, sha



def repack_preserving_member_order(document, binary):
    """Retain all unrelated JSON order, compact encoding, padding and framing."""
    document["buffers"][0]["byteLength"] = len(binary)
    text = json.dumps(document, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    text += b" " * (-len(text) % 4)
    padded = binary + b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(padded)
    return (struct.pack("<III", 0x46546c67, 2, total) + struct.pack("<II", len(text), 0x4e4f534a) +
            text + struct.pack("<II", len(padded), 0x004e4942) + padded)


def _target_mapping(document, occurrence):
    """Resolve the frozen authored scene locator, not an arbitrary output node."""
    scene, separator, path = occurrence.partition(".")
    require(separator and scene and path, "Frozen target lacks a scene and occurrence path")
    matches = []
    for node in document["nodes"]:
        ontokin = node.get("extras", {}).get("ontokin", {})
        mapping = ontokin.get("source_mapping", {})
        identity = ontokin.get("element_id", [])
        if (mapping.get("path") == path and isinstance(identity, list) and
                len(identity) >= 2 and identity[1] == scene and mapping.get("generated")):
            matches.append(mapping)
    require(len(matches) == 1, "Frozen supplied-byte occurrence must resolve to exactly one native node: " + occurrence)
    return matches[0]


def _projections(document, mapping):
    """Select the duplicate native mapping copies without changing either yet."""
    targets = [mapping["generated"],
               document["extras"]["ontokin"]["program"]["occurrences"][mapping["path"]]["generated"]]
    require(targets[0] == targets[1], "Unchanged native generated projections differ")
    return targets


def _rekey_indices(records):
    required = {"expression", "input", "body", "element_type", "old_key", "new_key", "input_entry"}
    require(records and all(set(record) == required for record in records),
            "Unchanged input lacks exact seven-field rekey records")
    aggregate = [i for i, record in enumerate(records) if record["old_key"] is None]
    selected = [i for i, record in enumerate(records) if record["old_key"] is not None]
    require(len(aggregate) == len(selected) == 1, "Frozen panel has one aggregate and one selected rekey origin")
    require(records[aggregate[0]]["new_key"] is None and records[aggregate[0]]["input_entry"] is None,
            "Unchanged aggregate rekey contributor fields must be null")
    return aggregate[0], selected[0]


def build_mutations(raw, case, *, specification=None, fixtures=None):
    """Build the frozen applicable H01-H27 changes to actual supplied bytes."""
    from tools.string_concat_reference import load_fixtures
    from tools.string_concat_delivery_reference import panel_sources
    fixtures = load_fixtures() if fixtures is None else fixtures
    specification = fixtures["adversaries"] if specification is None else specification
    require(specification == fixtures["adversaries"], "Hostile inventory differs from exact published bytes")
    name = case["name"] if isinstance(case, dict) else case
    case = fixtures["agent_cases"][name]
    require(name in specification["source_cases"], "Unknown frozen hostile-byte source case")
    requirements = specification["requirements"]
    require([row["id"] for row in requirements] == [f"H{i:02}" for i in range(1, 28)], "Frozen hostile inventory differs")
    original = GLB(raw, target=TARGET)
    declared_binary = original.binary[:original.document["buffers"][0]["byteLength"]]
    require(repack_preserving_member_order(copy.deepcopy(original.document), declared_binary) == raw,
            "Unchanged supplied-byte baseline cannot be repacked without an unrelated JSON/framing change")
    applicable = [row for row in requirements if name in row.get("applicable_source_cases", specification["source_cases"])]
    records = []
    for requirement in applicable:
        ordinal = int(requirement["id"][1:])
        document = copy.deepcopy(original.document)
        binary = bytearray(declared_binary)
        primitive = next(p for mesh in document["meshes"] for p in mesh["primitives"] if "TEXCOORD_0" in p["attributes"])
        selected_indices = original.accessor(primitive["indices"])

        def offset(index, row=0):
            accessor = document["accessors"][index]
            view = document["bufferViews"][accessor["bufferView"]]
            component = {5123: 2, 5125: 4, 5126: 4}[accessor["componentType"]]
            size = component * {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
            return view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + row * view.get("byteStride", size)

        if ordinal in (1, 3):
            role = "POSITION" if ordinal == 1 else "TEXCOORD_0"
            at = offset(primitive["attributes"][role], selected_indices[0])
            struct.pack_into("<f", binary, at, struct.unpack_from("<f", binary, at)[0] + .125)
        elif ordinal == 2:
            index = primitive["indices"]
            fmt = {5123: "H", 5125: "I"}[document["accessors"][index]["componentType"]]
            struct.pack_into("<" + fmt, binary, offset(index, 1), selected_indices[0])
        elif ordinal == 4:
            view = document["bufferViews"][document["images"][0]["bufferView"]]
            binary[view.get("byteOffset", 0) + 32] ^= 1
        elif ordinal == 5:
            document["materials"][primitive["material"]]["pbrMetallicRoughness"]["baseColorFactor"][0] = .375
        elif ordinal == 6:
            document["samplers"][0].update(minFilter=9729, wrapS=10497)
        elif ordinal == 7:
            # Right survives the first-occurrence rename in all three frozen
            # source cases. Change only its generated key in both projections.
            mapping = _target_mapping(document, 'demo.first.panels[' + json.dumps(case['first_prefix']+'right') + ']')
            for generated in _projections(document, mapping):
                require(generated["key"] == case["first_prefix"]+"right", "Frozen surviving generated key differs")
                generated["key"] = "substituted"
        elif ordinal == 8:
            animation = document["animations"][0]
            channel = next(c for c in animation["channels"] if c["target"]["path"] == "translation")
            index = animation["samplers"][channel["sampler"]]["output"]
            at = offset(index, document["accessors"][index]["count"] - 1)
            struct.pack_into("<f", binary, at, struct.unpack_from("<f", binary, at)[0] + .125)
        elif ordinal == 9:
            document["extras"]["ontokin"]["program"]["revision"] = "sha256:" + "0" * 64
        elif ordinal == 10 or 13 <= ordinal <= 24:
            target = requirement.get("target")
            if target is not None:
                require(name == "panel-task-repaired" and target["record_role"] == "selected",
                        "The two renamed-key adversaries apply only to the frozen repaired selected record")
                mapping = _target_mapping(document, target["occurrence"])
            else:
                # The repair key is selected from the frozen source case name.
                # Neither target discovery nor applicability is output driven.
                owner = "sibling" if ordinal == 22 and name == "panel-task-inserted" else "first"
                key = case[owner+"_prefix"]+"left"
                mapping = _target_mapping(document, "demo."+owner+'.panels[' + json.dumps(key) + ']')
            targets = _projections(document, mapping)
            for generated in targets:
                rekeys = generated["input_rekeys"]
                aggregate, selected = _rekey_indices(rekeys)
                if ordinal == 10:
                    rekeys[aggregate]["expression"]["start_byte"] += 1
                elif ordinal == 13:
                    rekeys[selected]["old_key"] = "right" if rekeys[selected]["old_key"] == "left" else "left"
                elif ordinal == 14:
                    rekeys[selected]["new_key"] = "substituted"
                elif ordinal == 15:
                    rekeys[selected]["input_entry"]["start_byte"] += 1
                elif ordinal == 16:
                    rekeys[aggregate]["body"]["start_byte"] += 1
                elif ordinal == 17:
                    rekeys[aggregate]["element_type"] = "Int" if rekeys[aggregate]["element_type"] != "Int" else "Bool"
                elif ordinal == 18:
                    rekeys[aggregate].update(old_key=rekeys[selected]["old_key"],
                        new_key=rekeys[selected]["new_key"],
                        input_entry=copy.deepcopy(rekeys[selected]["input_entry"]))
                elif ordinal == 19:
                    rekeys[aggregate]["unadopted_identity"] = "invented"
                elif ordinal == 20:
                    rekeys.pop(aggregate)
                elif ordinal == 21:
                    rekeys[aggregate], rekeys[selected] = rekeys[selected], rekeys[aggregate]
                elif ordinal == 22:
                    record = next(r for r in generated["input_merges"] if r["input_side"] != "both")
                    record["input_side"] = "right" if record["input_side"] == "left" else "left"
                elif ordinal == 23:
                    record = rekeys[selected]
                    require(record["old_key"] == target["old_key"] and record["new_key"] == target["new_key"] and
                            generated["key"] == target["new_key"], "Frozen repaired old/new-key target differs")
                    record["old_key"], record["new_key"] = record["new_key"], record["old_key"]
                elif ordinal == 24:
                    require(rekeys[selected]["old_key"] == target["original_zip_key"] and
                            rekeys[selected]["new_key"] == target["false_relabel"] and
                            generated["key"] == target["false_relabel"], "Frozen repaired inherited-zip target differs")
                    selected_zips = [record for record in generated["input_zips"]
                                     if record["key"] == target["original_zip_key"]]
                    require(len(selected_zips) == 1, "Frozen repaired panel has one selected inherited zip origin")
                    selected_zips[0]["key"] = target["false_relabel"]
        elif ordinal == 11:
            document["extras"]["ontokin"]["unadopted_metadata"] = {"selection_claim": "unverified"}
        elif ordinal == 25:
            index = original.objects()["first"]
            require(document["nodes"][index]["extras"]["ontokin"]["properties"]["prefix"] ==
                    {"type":"String", "value":case["first_prefix"]},
                    "Frozen first prefix property differs")
            document["nodes"][index]["extras"]["ontokin"]["properties"]["prefix"]["value"] = "false."
        elif ordinal == 26:
            mapping = _target_mapping(document, 'demo.first.panels['+json.dumps(case["first_prefix"]+"left")+']')
            control_body = panel_sources(case, fixtures, control=True)["rekey"]["body"]
            for generated in _projections(document, mapping):
                for record in generated["input_rekeys"]:
                    record["body"] = copy.deepcopy(control_body)
        elif ordinal == 27:
            require(name == "panel-task-inserted", "Middle-origin hostile belongs only to inserted state")
            mapping = _target_mapping(document, 'demo.first.panels["front.middle"]')
            left = panel_sources(case, fixtures)["owner_entries"]["first"]["left"]
            for generated in _projections(document, mapping):
                generated["input_entry"] = copy.deepcopy(left)
                for record in generated["input_rekeys"]:
                    if record["old_key"] is not None:
                        record["input_entry"] = copy.deepcopy(left)
                for record in generated["input_zips"]:
                    if record["key"] is not None:
                        record["left_entry"] = copy.deepcopy(left)
                        record["right_entry"] = copy.deepcopy(left)
        elif ordinal != 12:
            raise AssertionError(ordinal)
        changed = raw + b"\0\0\0\0" if ordinal == 12 else repack_preserving_member_order(document, bytes(binary))
        require(changed != raw, "Supplied-byte adversary did not change the successful baseline")
        records.append({"id": requirement["id"], "case": name, "mutation": requirement["mutation"],
                        "base_sha256": sha(raw), "sha256": sha(changed), "bytes": len(changed), "data": changed})
    require(len(records) == {"panel-task":24, "panel-task-repaired":26, "panel-task-inserted":25}[name],
            "Frozen per-case hostile-byte inventory differs")
    return records
