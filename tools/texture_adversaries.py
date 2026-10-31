"""Concrete C080 supplied-byte mutations, independent of production code.

Inputs are actual successful artifacts. Each retained mutation changes those
bytes and leaves the frozen source/image expectations intact.
"""
from __future__ import annotations

import copy
import struct

from tools.texture_reference import GLB, exact_uv, repack_glb, require, sha


def generate(fixtures, artifacts):
    records = []
    for ordinal, spec in enumerate(fixtures["workflows"]["supplied_glb_adversaries"], 1):
        mutation = spec["mutation"]
        case_name = ("placed-mapping" if mutation == "use placed/world coordinates for UVs" else
                     "assembly-image-repaired" if mutation == "swap material image references" else
                     "generated" if mutation == "merge distinct mapping UV accessors incorrectly" else
                     "rgb-panel")
        raw = artifacts[case_name]
        original = GLB(raw)
        document, binary = copy.deepcopy(original.document), bytearray(original.binary[:original.document["buffers"][0]["byteLength"]])
        textured = [p for m in document["meshes"] for p in m["primitives"] if "TEXCOORD_0" in p["attributes"]]
        primitive = textured[0]
        index = primitive["attributes"]["TEXCOORD_0"]
        accessor = document["accessors"][index]
        view = document["bufferViews"][accessor["bufferView"]]
        offset, stride = view.get("byteOffset", 0) + accessor.get("byteOffset", 0), view.get("byteStride", 8)
        referenced = original.accessor(primitive["indices"])
        row = referenced[0]
        position = offset + row * stride
        material = document["materials"][primitive["material"]]
        image = document["images"][0]
        image_view = document["bufferViews"][image["bufferView"]]
        if mutation == "change one referenced UV":
            u, v = struct.unpack_from("<2f", binary, position)
            struct.pack_into("<2f", binary, position, u + .125, v)
        elif mutation in ("swap U and V", "invert V orientation"):
            for row in sorted(set(referenced)):
                start = offset + row * stride
                u, v = struct.unpack_from("<2f", binary, start)
                struct.pack_into("<2f", binary, start, *((v, u) if mutation.startswith("swap") else (u, 1 - v)))
        elif mutation == "use placed/world coordinates for UVs":
            mapping = fixtures["cases"][case_name]["texture_bindings"][0]["mapping"]
            positions = original.accessor(primitive["attributes"]["POSITION"])
            for row in sorted(set(referenced)):
                struct.pack_into("<2f", binary, offset + row * stride, *exact_uv(positions[row], mapping))
        elif mutation == "nonzero unreferenced UV row":
            row = next(i for i in range(accessor["count"]) if i not in set(referenced))
            struct.pack_into("<2f", binary, offset + row * stride, .25, .5)
        elif mutation == "wrong UV accessor count/type/component type":
            accessor["count"] -= 1
        elif mutation == "replace embedded PNG with different valid bytes":
            png = (fixtures["root"] / fixtures["expected"]["images"]["asymmetric-rgba"]["path"]).read_bytes()
            binary.extend(b"\0" * (-len(binary) % 4))
            image_view["byteOffset"], image_view["byteLength"] = len(binary), len(png)
            binary.extend(png)
        elif mutation == "alter embedded PNG CRC":
            binary[image_view["byteOffset"] + 32] ^= 1
        elif mutation == "external image URI":
            del image["bufferView"]
            image["uri"] = "https://never-fetch.invalid/hostile.png"
        elif mutation == "wrong image MIME":
            image["mimeType"] = "image/jpeg"
        elif mutation == "swap material image references":
            require(len(textured) >= 2, "Image-reference mutation requires two actual textured primitives")
            a, b = [document["materials"][p["material"]]["pbrMetallicRoughness"]["baseColorTexture"] for p in textured[:2]]
            require(a["index"] != b["index"], "Image-reference mutation must change distinct actual images")
            a["index"], b["index"] = b["index"], a["index"]
        elif mutation == "change minFilter or wrapS":
            document["samplers"][0]["minFilter"] = 9729
            document["samplers"][0]["wrapS"] = 10497
        elif mutation == "drop TEXCOORD_0":
            del primitive["attributes"]["TEXCOORD_0"]
        elif mutation == "change texCoord set":
            material["pbrMetallicRoughness"]["baseColorTexture"]["texCoord"] = 1
        elif mutation == "omit baseColorTexture":
            del material["pbrMetallicRoughness"]["baseColorTexture"]
        elif mutation == "change baseColorFactor":
            material["pbrMetallicRoughness"]["baseColorFactor"][0] = .375
        elif mutation == "remove image provenance":
            del image["extras"]
        elif mutation == "merge distinct mapping UV accessors incorrectly":
            require(len(textured) >= 2 and textured[0]["attributes"]["TEXCOORD_0"] != textured[1]["attributes"]["TEXCOORD_0"],
                    "Mapping mutation requires separate actual regional streams")
            textured[1]["attributes"]["TEXCOORD_0"] = textured[0]["attributes"]["TEXCOORD_0"]
        elif mutation == "add dangling unused image or texture":
            document["images"].append(copy.deepcopy(image))
            document["textures"].append({"source": len(document["images"]) - 1, "sampler": 0})
        else:
            raise AssertionError("Unimplemented frozen supplied-byte adversary: " + mutation)
        changed = repack_glb(document, bytes(binary))
        require(changed != raw, "A hostile fixture must really change supplied bytes")
        records.append({"id": f"G{ordinal:02}", "case": case_name, "mutation": mutation,
                        "base_sha256": sha(raw), "sha256": sha(changed), "bytes": len(changed),
                        "expected_code": spec["expected_code"], "expected_stage": spec["expected_stage"],
                        "data": changed})
    return records
