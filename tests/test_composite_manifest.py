"""Focused failures for the experimental registration and source-binding checks."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

from ontokin.composite_manifest import check_manifest, check_registration


FIXTURE = Path(__file__).resolve().parents[1] / "examples/splat-composite/fixtures/registration-screen.glb"


def registration():
    # Rotate +90 degrees about world Z, then translate (2, 3, 4).
    return {"kind": "rigid", "worldUnit": "metre", "toleranceM": 0,
            "matrix": [0,1,0,0, -1,0,0,0, 0,0,1,0, 2,3,4,1],
            "anchors": [{"name": "zero", "environment": [0,0,0], "world": [2,3,4]},
                        {"name": "x", "environment": [1,0,0], "world": [2,4,4]},
                        {"name": "y", "environment": [0,1,0], "world": [1,3,4]}]}


class RegistrationTests(unittest.TestCase):
    def test_column_major_rigid_and_residual(self):
        reg = registration()
        self.assertEqual(check_registration(reg)["maxResidualM"], 0)
        reg["anchors"][0]["world"][2] += 0.002
        with self.assertRaisesRegex(ValueError, "exceeds tolerance"):
            check_registration(reg)
        reg["toleranceM"] = 0.003
        result = check_registration(reg)
        self.assertAlmostEqual(result["anchorResidualsM"]["zero"], 0.002)
        self.assertAlmostEqual(result["rmsResidualM"], 0.002 / 3**0.5)

    def test_uniform_calibration_is_explicit(self):
        reg = registration()
        for index in (1, 4, 10):
            reg["matrix"][index] *= 2
        reg["anchors"][1]["world"][1] = 5
        reg["anchors"][2]["world"][0] = 0
        with self.assertRaisesRegex(ValueError, "scale"):
            check_registration(reg)
        reg["kind"] = "similarity"
        self.assertEqual(check_registration(reg)["scale"], 2)

    def test_no_reflection_shear_perspective_or_nonfinite_values(self):
        for index, value in ((10, -1), (5, 0.3), (15, 0.9), (13, float("nan")), (10, float("inf"))):
            with self.subTest(index=index, value=value):
                reg = registration()
                reg["matrix"][index] = value
                with self.assertRaises(ValueError):
                    check_registration(reg)

    def test_collinear_or_duplicate_anchors(self):
        for frame in ("environment", "world"):
            reg = registration()
            reg["anchors"][2][frame] = reg["anchors"][0][frame]
            with self.assertRaisesRegex(ValueError, "span a plane"):
                check_registration(reg)
        reg = registration()
        reg["anchors"][2]["name"] = reg["anchors"][0]["name"]
        with self.assertRaisesRegex(ValueError, "unique"):
            check_registration(reg)


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ontokin.budget_runtime import execute_torque_export
        from ontokin.execution_budget import HostPolicy
        from ontokin.scene import ExportOptions
        from ontokin.texture_bundle import load_texture_bundle

        source = FIXTURE.parents[2] / "service-entrance" / "src" / "main.ok"
        cls.source = source.read_bytes()
        bundle = load_texture_bundle({"schema_version": "ontokin.bundle/0.2", "modules": [], "assets": [],
                                      "entry": {"filename": "main.ok", "source": cls.source.decode()}})
        result = execute_torque_export(bundle, policy=HostPolicy(max_operations=1_000_000, max_elapsed_ms=80_000),
                                       options=ExportOptions(end="0.01", fps=32, helpers=False))
        if result.data is None:
            raise RuntimeError(result.report)
        size = struct.unpack_from("<I", result.data, 12)[0]
        cls.original_doc = json.loads(result.data[20:20 + size])
        cls.binary = result.data[28 + size:]

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.root = self.directory / "demo"
        self.root.mkdir()
        shutil.copyfile(FIXTURE, self.root / "screen.glb")
        self.src = self.root / "main.ok"
        self.src.write_bytes(self.source)
        env = self.ref("screen.glb")
        self.doc = copy.deepcopy(self.original_doc)
        glb = self.write_glb()
        self.manifest = {"schema": "ontokin-composite/1", "collisionProxy": None,
                         "registration": registration(),
                         "authored": {"source": self.ref("main.ok"), "glb": glb},
                         "environment": {**env, "name": "screen", "provenance": "synthetic fixture",
                                         "authority": "visual-only", "requiredExtension": "KHR_gaussian_splatting"}}

    def ref(self, name):
        return {"path": name, "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest()}

    def write_glb(self):
        text = json.dumps(self.doc).encode()
        text += b" " * (-len(text) % 4)
        raw = (struct.pack("<4sIII4s", b"glTF", 2, 28 + len(text) + len(self.binary), len(text), b"JSON")
               + text + struct.pack("<I4s", len(self.binary), b"BIN\0") + self.binary)
        (self.root / "animated.glb").write_bytes(raw)
        return self.ref("animated.glb")

    def check(self, value):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(value))
        return check_manifest(path)

    def test_valid_pair_and_all_pins(self):
        self.assertEqual(self.check(self.manifest)["environmentAuthority"], "visual-only")
        for section, key in (("environment", None), ("authored", "source"), ("authored", "glb")):
            changed = copy.deepcopy(self.manifest)
            ref = changed[section] if key is None else changed[section][key]
            ref["sha256"] = "a" * 64
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                self.check(changed)

    def test_rejects_authored_cycles_and_dense_accessor_amplification(self):
        for attack in ("cycle", "empty-implicit", "overlap", "undeclared-splat"):
            with self.subTest(attack=attack):
                self.doc = copy.deepcopy(self.original_doc)
                if attack == "cycle":
                    self.doc["nodes"][0]["children"] = [0]
                elif attack == "empty-implicit":
                    del self.doc["accessors"][0]["bufferView"]
                    self.doc["accessors"][0]["count"] = 1000000
                elif attack == "overlap":
                    self.doc["bufferViews"] += [
                        {"buffer": 0, "byteOffset": 0, "byteLength": len(self.binary)}
                    ] * (1 + 64 * 1024 * 1024 // len(self.binary))
                else:
                    self.doc["meshes"][0]["primitives"][0]["extensions"] = {"KHR_gaussian_splatting": {}}
                self.manifest["authored"]["glb"] = self.write_glb()
                with self.assertRaises(ValueError):
                    self.check(self.manifest)

    def test_stale_source_with_new_pin_is_rejected(self):
        self.src.write_bytes(b"new source")
        self.manifest["authored"]["source"] = self.ref("main.ok")
        with self.assertRaisesRegex(ValueError, "source revision"):
            self.check(self.manifest)

    def test_external_authored_image_is_rejected(self):
        self.doc["images"] = [{"uri": "https://example.test/missing.png"}]
        self.manifest["authored"]["glb"] = self.write_glb()
        with self.assertRaisesRegex(ValueError, "embedded"):
            self.check(self.manifest)

    def test_path_escape_and_uri_are_rejected(self):
        for path in ("../main.ok", "/main.ok", ".hidden.ok", "%2e%2e/main.ok", "https://example.test/scene.ok"):
            changed = copy.deepcopy(self.manifest)
            changed["authored"]["source"]["path"] = path
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "relative asset path"):
                self.check(changed)
        outside = self.directory / "outside.ok"
        self.src.rename(outside)
        self.src.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "outside"):
            self.check(self.manifest)

    def test_no_collision_authority(self):
        for field in ("authority", "collisionProxy"):
            changed = copy.deepcopy(self.manifest)
            if field == "authority":
                changed["environment"]["authority"] = "collision"
            else:
                changed["collisionProxy"] = {"path": "unsafe.glb"}
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.check(changed)


if __name__ == "__main__":
    unittest.main()
