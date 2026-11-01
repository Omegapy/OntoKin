"""Repeatable hostile changes to actual supplied .18 GLBs, never expected answers."""
from __future__ import annotations

import copy
import json
import struct

from tools.keyed_zip_reference import GLB, TARGET, require, sha

MUTATIONS = ('Complete BIN position scalar changed while JSON metadata remains exact', 'Triangle index changed in actual supplied BIN', 'UV scalar changed in actual supplied BIN', 'Embedded PNG byte changed and structural lengths retained', 'Material color changed in raw JSON', 'Sampler wrap or filtering changed in raw JSON', 'One surviving generated identity renamed', 'Recorded motion sample changed', 'Declared program/source revision changed', 'Zip original expression or operand source span changed', 'Unknown JSON metadata added or changed outside permitted paths', 'Chunk framing/length altered or trailing bytes appended', 'Paired zip key changed to another stable key while geometry stays exact', 'Left original contributing entry source span changed', 'Right original contributing entry source span changed', 'Body original source span changed', 'One canonical left/right/output element type changed', 'Aggregate zip key or entry location changed from null to fabricated contributor', 'Unknown field added to ten-field zip record', 'Required aggregate or paired-entry zip record removed', 'Aggregate and paired records reordered while every field and geometry byte remain', 'Inherited merge contributor input_side changed while zip records remain exact', 'Left and right original zip operand locations swapped', 'Left and right original zip entry locations swapped')



def repack_preserving_member_order(document, binary):
    """Mutate only prescribed data; retain all unrelated JSON member order."""
    document["buffers"][0]["byteLength"] = len(binary)
    text = json.dumps(document, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    text += b" " * (-len(text) % 4)
    padded = binary + b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(padded)
    return (struct.pack("<III", 0x46546c67, 2, total) + struct.pack("<II", len(text), 0x4e4f534a) +
            text + struct.pack("<II", len(padded), 0x004e4942) + padded)


def build_mutations(raw, case):
    """Build H01–H24 from retained successful bytes, without predicting a result."""
    name = case["name"] if isinstance(case, dict) else case
    original = GLB(raw, target=TARGET)
    declared_binary = original.binary[:original.document["buffers"][0]["byteLength"]]
    require(repack_preserving_member_order(copy.deepcopy(original.document), declared_binary) == raw,
            "Unchanged supplied-byte baseline cannot be repacked without an unrelated JSON/framing change")
    records = []
    for ordinal, mutation in enumerate(MUTATIONS, 1):
        document = copy.deepcopy(original.document)
        binary = bytearray(original.binary[:document["buffers"][0]["byteLength"]])
        primitive = next(p for mesh in document["meshes"] for p in mesh["primitives"] if "TEXCOORD_0" in p["attributes"])
        selected = original.accessor(primitive["indices"])

        def offset(index, row=0):
            accessor = document["accessors"][index]
            view = document["bufferViews"][accessor["bufferView"]]
            component = {5123: 2, 5125: 4, 5126: 4}[accessor["componentType"]]
            size = component * {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
            return view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + row * view.get("byteStride", size)

        if ordinal in (1, 3):
            role = "POSITION" if ordinal == 1 else "TEXCOORD_0"
            at = offset(primitive["attributes"][role], selected[0])
            struct.pack_into("<f", binary, at, struct.unpack_from("<f", binary, at)[0] + .125)
        elif ordinal == 2:
            index = primitive["indices"]
            fmt = {5123: "H", 5125: "I"}[document["accessors"][index]["componentType"]]
            struct.pack_into("<" + fmt, binary, offset(index, 1), selected[0])
        elif ordinal == 4:
            view = document["bufferViews"][document["images"][0]["bufferView"]]
            binary[view.get("byteOffset", 0) + 32] ^= 1
        elif ordinal == 5:
            document["materials"][primitive["material"]]["pbrMetallicRoughness"]["baseColorFactor"][0] = .375
        elif ordinal == 6:
            document["samplers"][0].update(minFilter=9729, wrapS=10497)
        elif ordinal == 7:
            node = next(n for n in document["nodes"] if n.get("extras", {}).get("ontokin", {}).get("source_mapping", {}).get("generated"))
            node["extras"]["ontokin"]["source_mapping"]["generated"]["key"] = "substituted"
        elif ordinal == 8:
            animation = document["animations"][0]
            channel = next(c for c in animation["channels"] if c["target"]["path"] == "translation")
            index = animation["samplers"][channel["sampler"]]["output"]
            at = offset(index, document["accessors"][index]["count"] - 1)
            struct.pack_into("<f", binary, at, struct.unpack_from("<f", binary, at)[0] + .125)
        elif ordinal == 9:
            document["extras"]["ontokin"]["program"]["revision"] = "sha256:" + "0" * 64
        elif ordinal == 10 or 13 <= ordinal <= 24:
            node = next(n for n in document["nodes"] if
                (n.get("extras", {}).get("ontokin", {}).get("source_mapping", {}).get("generated") or {}).get("input_zips"))
            mapping = node["extras"]["ontokin"]["source_mapping"]
            # Keep the two native mapping projections equal so the corruption
            # isolates original paired provenance, not a duplicate mismatch.
            targets = [mapping["generated"], document["extras"]["ontokin"]["program"]["occurrences"][mapping["path"]]["generated"]]
            for generated in targets:
                zips = generated["input_zips"]
                aggregate = next(i for i,r in enumerate(zips) if r["key"] is None)
                paired = next(i for i,r in enumerate(zips) if r["key"] is not None)
                if ordinal == 10:
                    zips[aggregate]["expression"]["start_byte"] += 1
                elif ordinal == 13:
                    zips[paired]["key"] = "right" if zips[paired]["key"] == "left" else "left"
                elif ordinal == 14:
                    zips[paired]["left_entry"]["start_byte"] += 1
                elif ordinal == 15:
                    zips[paired]["right_entry"]["end_byte"] -= 1
                elif ordinal == 16:
                    zips[aggregate]["body"]["start_byte"] += 1
                elif ordinal == 17:
                    zips[aggregate]["output_element_type"] = "Int"
                elif ordinal == 18:
                    zips[aggregate].update(key=zips[paired]["key"],left_entry=copy.deepcopy(zips[paired]["left_entry"]))
                elif ordinal == 19:
                    zips[aggregate]["unadopted_identity"] = "invented"
                elif ordinal == 20:
                    zips.pop(aggregate)
                elif ordinal == 21:
                    zips[aggregate],zips[paired] = zips[paired],zips[aggregate]
                elif ordinal == 22:
                    record = next(r for r in generated["input_merges"] if r["input_side"] != "both")
                    record["input_side"] = "right" if record["input_side"] == "left" else "left"
                elif ordinal == 23:
                    zips[aggregate]["left"],zips[aggregate]["right"] = zips[aggregate]["right"],zips[aggregate]["left"]
                elif ordinal == 24:
                    zips[paired]["left_entry"],zips[paired]["right_entry"] = zips[paired]["right_entry"],zips[paired]["left_entry"]
        elif ordinal == 11:
            document["extras"]["ontokin"]["unadopted_metadata"] = {"selection_claim": "unverified"}
        elif ordinal != 12:
            raise AssertionError(ordinal)
        changed = raw + b"\0\0\0\0" if ordinal == 12 else repack_preserving_member_order(document, bytes(binary))
        require(changed != raw, "Supplied-byte adversary did not change the successful baseline")
        records.append({"id": f"H{ordinal:02}", "case": name, "mutation": mutation, "base_sha256": sha(raw),
                        "sha256": sha(changed), "bytes": len(changed), "data": changed})
    return records
