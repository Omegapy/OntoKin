"""Independent structural controls for the offline external-environment reader."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from ontokin.external_gltf import preflight_splat_glb


KHR = "KHR_gaussian_splatting"
SH0 = KHR + ":SH_DEGREE_0_COEF_0"


def asset():
    # Two independently readable, 56-byte vertex records, all float32.
    attributes = {"POSITION": 0, KHR + ":ROTATION": 1, KHR + ":SCALE": 2,
                  KHR + ":OPACITY": 3, SH0: 4}
    doc = {
        "asset": {"version": "2.0"}, "extensionsUsed": [KHR],
        "buffers": [{"byteLength": 112}],
        "bufferViews": [{"buffer": 0, "byteLength": 112, "byteStride": 56}],
        "accessors": [{"bufferView": 0, "byteOffset": offset, "type": shape,
                       "componentType": 5126, "count": 2}
                      for offset, shape in [(0, "VEC3"), (12, "VEC4"), (28, "VEC3"),
                                            (40, "SCALAR"), (44, "VEC3")]],
        "meshes": [{"primitives": [{"mode": 0, "attributes": attributes,
                    "extensions": {KHR: {"kernel": "ellipse", "colorSpace": "lin_rec709_display"}}}]}],
        "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}],
    }
    doc["accessors"][0].update(min=[0, 0, 0], max=[1, 0, 0])
    return doc


def encode(doc, extra_bytes=0):
    encoded = json.dumps(doc, allow_nan=False).encode()
    encoded += b" " * (-len(encoded) % 4)
    binary = b"".join(struct.pack("<14f", x, 0, 0, 0, 0, 0, 1, .1, .1, .1, .8, 0, 0, 0)
                      for x in (0, 1)) + bytes(extra_bytes)
    return (struct.pack("<4sIII4s", b"glTF", 2, 28 + len(encoded) + len(binary),
                        len(encoded), b"JSON") + encoded +
            struct.pack("<I4s", len(binary), b"BIN\0") + binary)


class ExternalGLTFTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "environment.glb"

    def check(self, doc, *, extra_bytes=0, **options):
        raw = encode(doc, extra_bytes)
        self.path.write_bytes(raw)
        return preflight_splat_glb(self.path, hashlib.sha256(raw).hexdigest(), **options)

    def test_interleaved_and_instance_counts(self):
        doc = asset()
        doc["nodes"] = [{"children": [1, 2]}, {"mesh": 0}, {"mesh": 0}]
        report = self.check(doc, max_splats=4)
        self.assertEqual((report["splat_count"], report["scene_splat_count"],
                          report["splat_primitives"]), (2, 4, 1))
        self.assertEqual(report["extensionsUsed"], [KHR])
        self.assertEqual(report["extensionsRequired"], [])
        self.assertEqual(report["bytes"], self.path.stat().st_size)
        with self.assertRaisesRegex(ValueError, "splat budget"):
            self.check(doc, max_splats=3)

    def test_allowed_quantized_formats_and_complete_sh(self):
        doc = asset()
        for i, part, norm in [(1, 5120, True), (2, 5123, False), (3, 5121, True)]:
            doc["accessors"][i].update(componentType=part, normalized=norm)
        attrs = doc["meshes"][0]["primitives"][0]["attributes"]
        attrs.update({f"{KHR}:SH_DEGREE_1_COEF_{i}": 4 for i in range(3)})
        self.assertEqual(self.check(doc)["splat_count"], 2)

    def test_hash_and_byte_budget(self):
        report = self.check(asset())
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            preflight_splat_glb(self.path, "a" * 64)
        with self.assertRaisesRegex(ValueError, "byte budget"):
            preflight_splat_glb(self.path, report["sha256"], max_bytes=report["bytes"] - 1)

    def test_aggregate_loader_allocations_are_bounded(self):
        extra = 4096
        for limit in ("bufferView", "accessor", "primitive attribute"):
            with self.subTest(limit=limit):
                doc = asset()
                doc["buffers"][0]["byteLength"] += extra
                # A dense extra view after the two interleaved vertices.
                view = {"buffer": 0, "byteOffset": 112, "byteLength": extra}
                doc["bufferViews"].append(view)
                attr = {"bufferView": 1, "type": "VEC4", "componentType": 5126, "count": 256}
                if limit == "bufferView":
                    doc["bufferViews"].append(view.copy())
                elif limit == "accessor":
                    doc["accessors"].extend([attr, attr.copy()])
                else:
                    # Keep one backed accessor per semantic; bind the mesh data
                    # repeatedly so only the total per-primitive footprint grows.
                    parts = doc["meshes"][0]["primitives"]
                    base = parts[0]
                    doc["accessors"] = [
                        {**a, "bufferView": 1, "byteOffset": 0, "count": 64}
                        for a in doc["accessors"]
                    ]
                    parts.extend([base, base])
                size = len(encode(doc, extra))
                with self.assertRaisesRegex(ValueError, "Aggregate " + limit):
                    self.check(doc, extra_bytes=extra, max_bytes=size)

    def test_container_bounds_before_reading_accessors(self):
        raw = encode(asset())
        for broken in (raw[:19], raw[:-4], raw + b"oops", raw[:16] + b"BIN\0" + raw[20:],
                       raw[:12] + struct.pack("<I", 0xfffffff0) + raw[16:]):
            with self.subTest(length=len(broken)):
                self.path.write_bytes(broken)
                with self.assertRaises(ValueError):
                    preflight_splat_glb(self.path, hashlib.sha256(broken).hexdigest())

    def test_reference_counts_and_formats(self):
        for mutate in (
            lambda d, p: p.update(mode=4),
            lambda d, p: p.update(mode=False),
            lambda d, p: p["extensions"][KHR].pop("kernel"),
            lambda d, p: p["extensions"][KHR].update(colorSpace="sRGB"),
            lambda d, p: p["attributes"].pop(SH0),
            lambda d, p: p["attributes"].update({KHR + ":SH_DEGREE_2_COEF_0": 4}),
            lambda d, p: p["attributes"].update(POSITION=-1),
            lambda d, p: p["attributes"].update(POSITION=False),
            lambda d, p: d["accessors"][0].pop("min"),
            lambda d, p: d["accessors"][1].update(count=1),
            lambda d, p: d["accessors"][2].update(bufferView=2),
            lambda d, p: d["accessors"][3].update(componentType=5123, normalized=False),
            lambda d, p: d["accessors"][4].update(type="VEC4"),
            lambda d, p: d["accessors"][4].update(byteOffset=108),
            lambda d, p: d["bufferViews"][0].update(byteStride=3),
            lambda d, p: d["bufferViews"][0].update(byteLength=200),
            lambda d, p: d["buffers"][0].update(byteLength=96),
        ):
            doc = asset()
            mutate(doc, doc["meshes"][0]["primitives"][0])
            with self.subTest(line=mutate.__code__.co_firstlineno), self.assertRaises(ValueError):
                self.check(doc)

    def test_rejects_unsupported_or_unbounded_content(self):
        for mutate in (
            lambda d: d["buffers"][0].update(uri="../remote.bin"),
            lambda d: d.update(images=[{"uri": "https://example.invalid/texture.png"}]),
            lambda d: d["extensionsUsed"].append("EXT_meshopt_compression"),
            lambda d: d.update(extensionsRequired=["KHR_materials_unlit"]),
            lambda d: d["bufferViews"][0].update(extensions={"EXT_meshopt_compression": {}}),
            lambda d: d["accessors"][0].update(sparse={}),
            lambda d: d["nodes"][0].update(children=[0]),
            lambda d: d.update(scenes=[]),
        ):
            doc = asset()
            mutate(doc)
            with self.subTest(line=mutate.__code__.co_firstlineno), self.assertRaises(ValueError):
                self.check(doc)
