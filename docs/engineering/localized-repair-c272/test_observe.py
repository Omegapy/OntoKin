"""Focused tests of C272's observation of delivered bytes (TASK-016)."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glb_edit  # noqa: E402
import observe  # noqa: E402

PROOF = HERE.parent / "semantic-export-c210/evidence/proof"
BLADE = 'first.fingers["middle"].blade'


def endpoint(name: str):
    sources = {"main.ok": (PROOF / f"{name}.main.ok").read_bytes(), "hinges.ok": (PROOF / "hinges.ok").read_bytes()}
    return sources, (PROOF / f"{name}.glb").read_bytes()


class Observation(unittest.TestCase):
    def test_both_endpoints_give_126_poses_and_18_meshes_bound_to_the_artifact(self):
        for name in ("before", "after"):
            sources, glb = endpoint(name)
            result = observe.observe_delivery(sources, glb, "scene.glb")
            self.assertTrue(result["valid"], result["faults"])
            digest = hashlib.sha256(glb).hexdigest()
            self.assertEqual(len(result["poses"]), 126)
            self.assertEqual(len(result["geometry"]), 18)
            self.assertEqual({(tuple(p["id"]), p["time_s"]) for p in result["poses"]}.__len__(), 126)
            for row in result["poses"] + result["geometry"]:
                self.assertEqual(row["origin"]["sha256"], digest)
                self.assertEqual(row["origin"]["artifact"], "scene.glb")
                self.assertTrue(row["origin"]["location"].strip())
            self.assertTrue(all(a["consistent"] for a in result["agreements"].values()))

    def test_the_same_path_reproduces_c256s_historical_reader(self):
        reader = observe.pinned("c256_reader")
        for name in ("before", "after"):
            sources, glb = endpoint(name)
            ours = observe.observe_delivery(sources, glb, f"{name}.glb")
            historical = reader.read_bound_endpoint(HERE.parents[2], name)
            self.assertEqual(ours["geometry"], historical["geometry"])
            self.assertEqual(ours["poses"], historical["poses"])

    def test_invalid_artifacts_fail_and_are_not_normalized(self):
        sources, glb = endpoint("after")
        document, _ = glb_edit.split(glb)
        node = glb_edit.node_index(document, BLADE)
        rotation = glb_edit.channel(document, node, "rotation")["output"]
        translation = glb_edit.channel(document, node, "translation")["output"]
        times = glb_edit.channel(document, node, "translation")["input"]
        mesh_position = document["meshes"][document["nodes"][node]["mesh"]]["primitives"][0]["attributes"]["POSITION"]
        first_time = glb_edit.read_floats(glb, times, 0, 1)[0]
        cases = {
            "nonfinite position": glb_edit.edit_floats(glb, translation, 3, [float("nan"), 0.0, 0.0], 3),
            "nonfinite vertex": glb_edit.edit_floats(glb, mesh_position, 0, [float("inf"), 0.0, 0.0], 3),
            "zero quaternion": glb_edit.edit_floats(glb, rotation, 3, [0.0, 0.0, 0.0, 0.0], 4),
            "duplicate time": glb_edit.edit_floats(glb, times, 1, [first_time], 1),
            "unintended scale": glb_edit.edit_json(glb, lambda d: d["nodes"][node].__setitem__("scale", [1.0, 1.0, 1.5])),
            "matrix node": glb_edit.edit_json(glb, lambda d: d["nodes"][node].__setitem__("matrix", [1.0, 0, 0, 0, 0, -1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0])),
            "duplicate identity": glb_edit.edit_json(glb, lambda d: d["nodes"][0]["extras"]["ontokin"].__setitem__(
                "element_id", d["nodes"][1]["extras"]["ontokin"]["element_id"])),
            "changed owner": glb_edit.edit_json(glb, lambda d: d["nodes"][node]["extras"]["ontokin"].__setitem__("owner", "second")),
        }
        for label, mutated in cases.items():
            with self.subTest(label):
                result = observe.observe_delivery(sources, mutated, "scene.glb")
                self.assertFalse(result["valid"], label)
                self.assertTrue(result["faults"])

    def test_no_product_module_is_imported(self):
        tree = ast.parse((HERE / "observe.py").read_text())
        names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(any(n.split(".")[0] == "ontokin" for n in names))
        script = ("import sys, json; sys.path.insert(0, sys.argv[1]); import observe; from pathlib import Path; "
                  "p=Path(sys.argv[2]); r=observe.observe_delivery({'main.ok':(p/'after.main.ok').read_bytes(),"
                  "'hinges.ok':(p/'hinges.ok').read_bytes()},(p/'after.glb').read_bytes(),'scene.glb'); "
                  "print(json.dumps([r['valid'], sorted(m for m in sys.modules if m.split('.')[0]=='ontokin')]))")
        out = subprocess.run([sys.executable, "-I", "-c", script, str(HERE), str(PROOF)], capture_output=True, text=True,
                             cwd="/", check=True).stdout
        self.assertEqual(json.loads(out), [True, []])

    def test_a_changed_component_refuses_to_load(self):
        relative, digest = observe.PINS["c256_reader"]
        self.assertEqual(hashlib.sha256((observe.ENGINEERING / relative).read_bytes()).hexdigest(), digest)
        original = dict(observe.PINS)
        try:
            observe.PINS["c256_reader"] = (relative, "0" * 64)
            sys.modules.pop("_c272_c256_reader", None)
            with self.assertRaises(observe.ObservationFault):
                observe.pinned("c256_reader")
        finally:
            observe.PINS.clear()
            observe.PINS.update(original)
            sys.modules.pop("_c272_c256_reader", None)


if __name__ == "__main__":
    unittest.main()
