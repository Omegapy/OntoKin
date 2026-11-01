"""Repeatable hostile changes to actual supplied .17 GLBs, never expected answers."""
from __future__ import annotations

import copy
import json
import struct

from tools.keyed_merge_reference import GLB, TARGET, require, sha

MUTATIONS = (
    'Complete BIN position scalar changed while JSON metadata remains exact',
    'Triangle index changed in actual supplied BIN',
    'UV scalar changed in actual supplied BIN',
    'Embedded PNG byte changed and structural lengths retained',
    'Material color changed in raw JSON',
    'Sampler wrap or filtering changed in raw JSON',
    'One surviving generated identity renamed',
    'Recorded motion sample changed',
    'Declared program/source revision changed',
    'Merge provenance original source expression or operand span changed',
    'Unknown JSON metadata added or changed outside permitted paths',
    'Chunk framing/length altered or trailing bytes appended',
    'Contributing merge input_side changed from left to right or right to left without changing geometry',
    'Canonical common merge element_type replaced by another admitted type',
    'Merge left and right original source locations swapped',
    'Unknown field added to a merge provenance record',
    'Required aggregate or contributing-entry merge provenance record removed',
    'Inherited filter origin changed while new merge provenance stays exact',
    'Required aggregate and contributing-entry merge records swapped in actual supplied GLB provenance order while retaining every record, field and geometry byte',
)


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
    """Build H01–H19 from retained successful bytes, without predicting a result."""
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
        elif ordinal == 10 or 13 <= ordinal <= 19:
            node = next(n for n in document["nodes"] if
                (n.get("extras", {}).get("ontokin", {}).get("source_mapping", {}).get("generated") or {}).get("input_merges"))
            mapping = node["extras"]["ontokin"]["source_mapping"]
            # Preserve equality of the two native source-mapping projections.
            # These mutations isolate the adopted provenance contract instead
            # of relying on a mismatched duplicate to trigger a refusal.
            targets = [mapping["generated"], document["extras"]["ontokin"]["program"]["occurrences"][mapping["path"]]["generated"]]
            for generated in targets:
                merges = generated["input_merges"]
                if ordinal == 10:
                    merges[0]["expression"]["start_byte"] += 1
                elif ordinal == 13:
                    contributing = next(record for record in merges if record["input_side"] != "both")
                    contributing["input_side"] = "right" if contributing["input_side"] == "left" else "left"
                elif ordinal == 14:
                    merges[0]["element_type"] = "Real"
                elif ordinal == 15:
                    merges[0]["left"], merges[0]["right"] = merges[0]["right"], merges[0]["left"]
                elif ordinal == 16:
                    merges[0]["unadopted_identity"] = "invented"
                elif ordinal == 17:
                    merges.pop(next(index for index, record in enumerate(merges) if record["input_side"] != "both"))
                elif ordinal == 18:
                    generated["input_filters"][0]["element_type"] = "Real"
                elif ordinal == 19:
                    aggregate = next(index for index, record in enumerate(merges) if record["input_side"] == "both")
                    contributing = next(index for index, record in enumerate(merges) if record["input_side"] != "both")
                    merges[aggregate], merges[contributing] = merges[contributing], merges[aggregate]
        elif ordinal == 11:
            document["extras"]["ontokin"]["unadopted_metadata"] = {"selection_claim": "unverified"}
        elif ordinal != 12:
            raise AssertionError(ordinal)
        changed = raw + b"\0\0\0\0" if ordinal == 12 else repack_preserving_member_order(document, bytes(binary))
        require(changed != raw, "Supplied-byte adversary did not change the successful baseline")
        records.append({"id": f"H{ordinal:02}", "case": name, "mutation": mutation, "base_sha256": sha(raw),
                        "sha256": sha(changed), "bytes": len(changed), "data": changed})
    return records
