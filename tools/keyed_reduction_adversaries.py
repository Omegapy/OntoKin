"""Repeatable changes to actual supplied .15 bytes, never expected answers."""
from __future__ import annotations

import copy
import struct

from tools.keyed_reduction_reference import GLB, TARGET, repack_glb, require, sha

MUTATIONS = (
    "position accessor altered", "normal accessor altered", "triangle/index data altered",
    "UV coordinate altered", "PNG bytes changed", "PNG identity/digest metadata changed",
    "sampler wrap/filter changed", "material factor changed", "animation sample changed",
    "stable occurrence key changed", "source/profile contract changed", "missing or substituted required stream")


def build_mutations(raw, case):
    """Return twelve real supplied-byte adversaries for one delivered fixture.

    The caller retains these exact data bytes and asks the public supplied-byte
    validator to read them. No success/failure label is invented here.
    """
    name = case["name"] if isinstance(case, dict) else case
    original = GLB(raw, target=TARGET)
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
        if mutation in ("position accessor altered", "normal accessor altered", "UV coordinate altered"):
            role = {"position accessor altered": "POSITION", "normal accessor altered": "NORMAL", "UV coordinate altered": "TEXCOORD_0"}[mutation]
            at = offset(primitive["attributes"][role], selected[0])
            value = struct.unpack_from("<f", binary, at)[0]
            struct.pack_into("<f", binary, at, value + .125)
        elif mutation == "triangle/index data altered":
            index = primitive["indices"]
            fmt = {5123: "H", 5125: "I"}[document["accessors"][index]["componentType"]]
            struct.pack_into("<"+fmt, binary, offset(index, 1), selected[0])
        elif mutation == "PNG bytes changed":
            view = document["bufferViews"][document["images"][0]["bufferView"]]
            binary[view.get("byteOffset", 0)+32] ^= 1
        elif mutation == "PNG identity/digest metadata changed":
            document["images"][0]["extras"]["ontokin"]["sha256"] = "sha256:" + "0"*64
        elif mutation == "sampler wrap/filter changed":
            document["samplers"][0].update(minFilter=9729, wrapS=10497)
        elif mutation == "material factor changed":
            document["materials"][primitive["material"]]["pbrMetallicRoughness"]["baseColorFactor"][0] = .375
        elif mutation == "animation sample changed":
            animation = document["animations"][0]
            channel = next(c for c in animation["channels"] if c["target"]["path"] == "translation")
            index = animation["samplers"][channel["sampler"]]["output"]
            at = offset(index, document["accessors"][index]["count"]-1)
            struct.pack_into("<f", binary, at, struct.unpack_from("<f", binary, at)[0]+.125)
        elif mutation == "stable occurrence key changed":
            node = next(n for n in document["nodes"] if n.get("extras", {}).get("ontokin", {}).get("source_mapping", {}).get("generated"))
            node["extras"]["ontokin"]["source_mapping"]["generated"]["key"] = "substituted"
        elif mutation == "source/profile contract changed":
            document["extras"]["ontokin"]["profile"] = "keyed-transform-0.1"
        elif mutation == "missing or substituted required stream":
            del primitive["attributes"]["NORMAL"]
        else:
            raise AssertionError(mutation)
        changed = repack_glb(document, bytes(binary))
        require(changed != raw, "Supplied-byte adversary did not actually change its successful base")
        records.append({"id": f"G{ordinal:02}", "case": name, "mutation": mutation, "base_sha256": sha(raw),
                        "sha256": sha(changed), "bytes": len(changed), "data": changed})
    return records
