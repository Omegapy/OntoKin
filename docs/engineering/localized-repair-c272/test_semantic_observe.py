"""Focused tests of C272's delivered-semantic reader (G3, TASK-017)."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glb_edit  # noqa: E402
import observe  # noqa: E402
import semantic_observe as so  # noqa: E402

PROOF = HERE.parent / "semantic-export-c210/evidence/proof"
BLADE = 'first.fingers["middle"].blade'
ORACLE = observe.pinned("c255_oracle")
CORPUS = ORACLE.load_corpus(HERE.parents[2])


def endpoint(name):
    sources = {"main.ok": (PROOF / f"{name}.main.ok").read_bytes(), "hinges.ok": (PROOF / "hinges.ok").read_bytes()}
    return sources, (PROOF / f"{name}.glb").read_bytes(), (PROOF / f"{name}.semantic.json").read_bytes()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rebind(sidecar: bytes, glb: bytes) -> bytes:
    value = json.loads(sidecar)
    value["binding"]["artifact"].update(sha256="sha256:" + hashlib.sha256(glb).hexdigest(), bytes=len(glb))
    return canonical(value)


def judge(sources, glb, sidecar, length):
    """The workflow's layered judgment: decoded delivery, G3 cross-checks, then C255's semantic comparison."""
    delivery = observe.observe_delivery(sources, glb, "scene.glb")
    if not delivery["valid"]:
        return "delivery", delivery["faults"][0]["code"]
    result = so.observe_semantic(sources, glb, sidecar, delivery)
    if result["fault"]:
        return "reader", result["fault"]["code"]
    failed = [c["check"] for c in result["crossChecks"] if not c["passed"]]
    expected = ORACLE.semantic_state(length)
    try:
        ORACLE.semantic_check(result["semantic"], expected)
        c255 = None
    except ORACLE.Fault as error:
        c255 = error.code
    if failed:
        return "cross-check", failed[0]
    if c255:
        return "c255", c255
    return "accepted", None


class Reading(unittest.TestCase):
    def test_both_endpoints_match_the_independent_expectations(self):
        for name, length in (("before", 0.65), ("after", 0.75)):
            self.assertEqual(judge(*endpoint(name), length), ("accepted", None))

    def test_negated_stored_rotations_are_the_same_motion(self):
        """Review M2: an equivalent quaternion sign in the actual GLB bytes must be accepted end to end."""
        sources, glb, sidecar = endpoint("after")
        document, _ = glb_edit.split(glb)
        for path in (BLADE, 'second.fingers["top"].blade', "first"):
            node = glb_edit.node_index(document, path)
            accessor = glb_edit.channel(document, node, "rotation")["output"]
            count = document["accessors"][accessor]["count"]
            for element in range(count):
                values = glb_edit.read_floats(glb, accessor, element, 4)
                glb = glb_edit.edit_floats(glb, accessor, element, [-x for x in values], 4)
        self.assertEqual(judge(sources, glb, rebind(sidecar, glb), 0.75), ("accepted", None))

    def test_wrong_length_expectation_is_refused(self):
        self.assertEqual(judge(*endpoint("after"), 0.65)[0], "c255")

    def test_every_field_carries_its_artifact_pointer_and_literals_carry_spans(self):
        sources, glb, sidecar = endpoint("after")
        result = so.observe_semantic(sources, glb, sidecar, observe.observe_delivery(sources, glb, "scene.glb"))
        self.assertTrue(result["valid"])
        for origins in result["origins"].values():
            for origin in origins:
                self.assertIn(origin["artifact"], ("scene.glb", "scene.semantic.json"))
                self.assertEqual(origin["sha256"], hashlib.sha256(glb if origin["artifact"] == "scene.glb" else sidecar).hexdigest())
                self.assertTrue(origin["pointer"].startswith("/"))
        self.assertEqual(len(result["sourceLiterals"]), 4)
        for span in result["sourceLiterals"]:
            raw = sources[span["file"]]
            self.assertLess(span["startByte"], span["endByteExclusive"])
            self.assertTrue(raw[span["startByte"]:span["endByteExclusive"]])
        self.assertEqual(len(result["derived"]), 18 + 34 + 8)
        for origins in result["origins"].values():
            for origin in origins:
                self.assertNotIn("*", origin["pointer"])
                self.assertNotIn(",", origin["pointer"])
        kinds = {c["check"].split(":")[0] for c in result["crossChecks"]}
        self.assertIn("hinge sites coincide in the decoded motion", kinds)
        self.assertIn("follow offset holds in the decoded motion", kinds)

    def test_single_field_faults_are_rejected(self):
        sources, glb, sidecar = endpoint("after")
        side = json.loads(sidecar)
        document, _ = glb_edit.split(glb)
        node = glb_edit.node_index(document, BLADE)

        def side_edit(change):
            value = copy.deepcopy(side)
            change(value)
            return glb, canonical(value)

        def glb_change(change):
            mutated = glb_edit.edit_json(glb, change)
            return mutated, rebind(sidecar, mutated)

        site = next(i for i, s in enumerate(side["sites"]) if s["path"] == BLADE + ".base")
        travel = next(i for i, a in enumerate(side["actions"]) if a["kind"] == "move")
        flex = next(i for i, a in enumerate(side["actions"]) if a["kind"] == "tween")
        racks = next(i for i, o in enumerate(side["objects"]) if o["path"] == "first")
        cases = {
            "site position": side_edit(lambda v: v["sites"][site]["pose"]["position_m"].__setitem__(0, -0.3)),
            "action velocity": side_edit(lambda v: v["actions"][travel]["velocity_m_per_s"].__setitem__(1, 0.25)),
            "tween goal": side_edit(lambda v: v["actions"][flex].__setitem__("hinge_goal_rad", 0.8)),
            "event target": side_edit(lambda v: v["events"][0]["events"].reverse()),
            "placement": side_edit(lambda v: v["objects"][racks]["placement"]["position_m"].__setitem__(0, -1.1)),
            "initial velocity": side_edit(lambda v: v["objects"][racks]["motion"]["initial_velocity_m_per_s"].__setitem__(0, 0.1)),
            "site interface": side_edit(lambda v: v["sites"][site].__setitem__("interface", "rigid.origin")),
            "hinge axis": glb_change(lambda d: d["extras"]["ontokin"]["joints"][0].__setitem__("axis", [0.0, 1.0, 0.0])),
            "hinge limit": glb_change(lambda d: d["extras"]["ontokin"]["joints"][0]["limits"].__setitem__(1, 0.7)),
            "follow offset": glb_change(lambda d: d["extras"]["ontokin"]["follows"][0]["offset_position_m"].__setitem__(1, -0.5)),
            "material colour": glb_change(lambda d: d["materials"][1]["pbrMetallicRoughness"]["baseColorFactor"].__setitem__(0, 0.3)),
            "blade length property": glb_change(lambda d: d["nodes"][node]["extras"]["ontokin"]["properties"]["length"].__setitem__("value", 0.7)),
            "declared primitive": glb_change(lambda d: d["nodes"][node]["extras"]["ontokin"]["geometry"]["size"].__setitem__(0, 0.7)),
            "gravity": glb_change(lambda d: d["extras"]["ontokin"].__setitem__("gravity_m_per_s2", [0.0, -9.81, 0.0])),
        }
        for label, (mutated_glb, mutated_sidecar) in cases.items():
            with self.subTest(label):
                layer, reason = judge(sources, mutated_glb, mutated_sidecar, 0.75)
                self.assertNotEqual(layer, "accepted", label)

    def test_stale_and_malformed_inputs_get_typed_refusals(self):
        sources, glb, sidecar = endpoint("after")
        _, _, old_sidecar = endpoint("before")
        delivery = observe.observe_delivery(sources, glb, "scene.glb")
        side = json.loads(sidecar)
        extra = copy.deepcopy(side)
        extra["sites"] = extra["sites"] * 9  # 306 sites
        duplicate = b'{"status":"duplicate",' + sidecar.lstrip()[1:]
        cases = {"stale sidecar": (old_sidecar, "STALE_SIDECAR"),
                 "excessive sites": (canonical(extra), "RESOURCE_LIMIT"),
                 "duplicate JSON key": (duplicate, "JSON_DUPLICATE"),
                 "nonfinite value": (sidecar.replace(b"0.2,", b"NaN,", 1), "NONFINITE"),
                 "not JSON": (b"\xff\xfe", "JSON_MALFORMED")}
        for label, (mutated, code) in cases.items():
            with self.subTest(label):
                result = so.observe_semantic(sources, glb, mutated, delivery)
                self.assertFalse(result["valid"])
                self.assertEqual(result["fault"]["code"], code, result["fault"])
        truncated = glb[:-200]
        self.assertFalse(observe.observe_delivery(sources, truncated, "scene.glb")["valid"])
        result = so.observe_semantic(sources, truncated, sidecar, observe.observe_delivery(sources, truncated, "scene.glb"))
        self.assertEqual(result["fault"]["code"], "DELIVERY_INVALID")

    def test_no_product_module_is_imported(self):
        for name in ("semantic_observe.py", "glb_edit.py"):
            tree = ast.parse((HERE / name).read_text())
            names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            names |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
            self.assertFalse(any(n.split(".")[0] == "ontokin" for n in names), name)


if __name__ == "__main__":
    unittest.main()
