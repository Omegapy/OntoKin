"""Isolated hostile changes to actual supplied .19 GLBs, never expected answers.

Targets and applicability come from the frozen C086 supplied-byte contract.
The two native generated-lineage projections are changed together so lineage
adversaries cannot pass merely by being caught as a duplicate-copy mismatch.
"""
from __future__ import annotations

import copy
import json
import struct

from tools.keyed_rekey_reference import GLB, TARGET, require, sha

MUTATIONS = ('Complete BIN position scalar changed while JSON metadata remains exact', 'Triangle index changed in actual supplied BIN', 'UV scalar changed in actual supplied BIN', 'Embedded PNG byte changed and structural lengths retained', 'Material color changed in raw JSON', 'Sampler wrap or filtering changed in raw JSON', 'One surviving generated identity renamed', 'Recorded motion sample changed', 'Declared program/source revision changed', 'Rekey original expression or input source span changed', 'Unknown JSON metadata added or changed outside permitted paths', 'Chunk framing/length altered or trailing bytes appended', 'Selected rekey old_key changed while new_key and geometry remain exact', 'Selected rekey new_key changed while generated identity remains exact', 'Original contributing payload entry source span changed', 'Callback body original source span changed', 'Canonical rekey element_type changed', 'Aggregate rekey old_key, new_key or input_entry changed from null to fabricated contributor', 'Unknown field added to seven-field rekey record', 'Required aggregate or selected rekey record removed', 'Aggregate and selected rekey records reordered while all fields and geometry bytes remain', 'Inherited merge contributor input_side changed while rekey records remain exact', 'Selected rekey old_key and new_key swapped in repaired state', 'Inherited zip key relabeled from original old key to computed new key')

DEFAULT_SPECIFICATION = {'source_cases': ['panel-task', 'panel-task-repaired', 'panel-task-higher-budget'], 'requirements': [{'id': 'H01', 'mutation': 'Complete BIN position scalar changed while JSON metadata remains exact', 'expected': 'refused'}, {'id': 'H02', 'mutation': 'Triangle index changed in actual supplied BIN', 'expected': 'refused'}, {'id': 'H03', 'mutation': 'UV scalar changed in actual supplied BIN', 'expected': 'refused'}, {'id': 'H04', 'mutation': 'Embedded PNG byte changed and structural lengths retained', 'expected': 'refused'}, {'id': 'H05', 'mutation': 'Material color changed in raw JSON', 'expected': 'refused'}, {'id': 'H06', 'mutation': 'Sampler wrap or filtering changed in raw JSON', 'expected': 'refused'}, {'id': 'H07', 'mutation': 'One surviving generated identity renamed', 'expected': 'refused'}, {'id': 'H08', 'mutation': 'Recorded motion sample changed', 'expected': 'refused'}, {'id': 'H09', 'mutation': 'Declared program/source revision changed', 'expected': 'refused'}, {'id': 'H10', 'mutation': 'Rekey original expression or input source span changed', 'expected': 'refused'}, {'id': 'H11', 'mutation': 'Unknown JSON metadata added or changed outside permitted paths', 'expected': 'refused'}, {'id': 'H12', 'mutation': 'Chunk framing/length altered or trailing bytes appended', 'expected': 'refused'}, {'id': 'H13', 'mutation': 'Selected rekey old_key changed while new_key and geometry remain exact', 'expected': 'refused'}, {'id': 'H14', 'mutation': 'Selected rekey new_key changed while generated identity remains exact', 'expected': 'refused'}, {'id': 'H15', 'mutation': 'Original contributing payload entry source span changed', 'expected': 'refused'}, {'id': 'H16', 'mutation': 'Callback body original source span changed', 'expected': 'refused'}, {'id': 'H17', 'mutation': 'Canonical rekey element_type changed', 'expected': 'refused'}, {'id': 'H18', 'mutation': 'Aggregate rekey old_key, new_key or input_entry changed from null to fabricated contributor', 'expected': 'refused'}, {'id': 'H19', 'mutation': 'Unknown field added to seven-field rekey record', 'expected': 'refused'}, {'id': 'H20', 'mutation': 'Required aggregate or selected rekey record removed', 'expected': 'refused'}, {'id': 'H21', 'mutation': 'Aggregate and selected rekey records reordered while all fields and geometry bytes remain', 'expected': 'refused'}, {'id': 'H22', 'mutation': 'Inherited merge contributor input_side changed while rekey records remain exact', 'expected': 'refused'}, {'id': 'H23', 'mutation': 'Selected rekey old_key and new_key swapped in repaired state', 'expected': 'refused', 'applicable_source_cases': ['panel-task-repaired'], 'target': {'occurrence': 'demo.first.panels["front.left"]', 'old_key': 'left', 'new_key': 'front.left', 'record_role': 'selected'}}, {'id': 'H24', 'mutation': 'Inherited zip key relabeled from original old key to computed new key', 'expected': 'refused', 'applicable_source_cases': ['panel-task-repaired'], 'target': {'occurrence': 'demo.first.panels["front.left"]', 'original_zip_key': 'left', 'false_relabel': 'front.left', 'record_role': 'selected'}}], 'expected_isolated_refusals': 68}


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


def build_mutations(raw, case, *, specification=None):
    """Build the exact applicable H01–H24 subset from actual delivered bytes.

    Pass fixtures["adversaries"] to use the verified frozen object directly.
    The default embeds those same preimplementation requirements for callers
    retaining the predecessor two-argument interface. It does not infer a
    mutation's applicability or target from candidate artifact contents.
    """
    name = case["name"] if isinstance(case, dict) else case
    specification = DEFAULT_SPECIFICATION if specification is None else specification
    require(name in specification["source_cases"], "Unknown frozen hostile-byte source case: " + str(name))
    requirements = specification["requirements"]
    require([row["id"] for row in requirements] == [f"H{i:02}" for i in range(1, 25)],
            "Frozen hostile-byte requirement inventory differs")
    require(tuple(row["mutation"] for row in requirements) == MUTATIONS,
            "Frozen hostile-byte mutation meanings differ")
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
            mapping = _target_mapping(document, 'demo.first.panels["right"]')
            for generated in _projections(document, mapping):
                require(generated["key"] == "right", "Frozen surviving generated key differs")
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
                key = "front.left" if name == "panel-task-repaired" else "left"
                mapping = _target_mapping(document, 'demo.first.panels[' + json.dumps(key) + ']')
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
        elif ordinal != 12:
            raise AssertionError(ordinal)
        changed = raw + b"\0\0\0\0" if ordinal == 12 else repack_preserving_member_order(document, bytes(binary))
        require(changed != raw, "Supplied-byte adversary did not change the successful baseline")
        records.append({"id": requirement["id"], "case": name, "mutation": requirement["mutation"],
                        "base_sha256": sha(raw), "sha256": sha(changed), "bytes": len(changed), "data": changed})
    require(len(records) == (24 if name == "panel-task-repaired" else 22),
            "Frozen per-case hostile-byte inventory differs")
    return records
