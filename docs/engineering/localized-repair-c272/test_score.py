"""Focused tests of C272's scoring step (TASK-018), on the frozen C210 proof bytes."""
from __future__ import annotations

import ast
import copy
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score  # noqa: E402

PROOF = HERE.parent / "semantic-export-c210/evidence/proof"
O = score.ORACLE
CORPUS = O.load_corpus(HERE.parents[2])
PROGRAM = {"before": "sha256:8f9d976568e2a9fa39573e3fb90f616529097241a098b21d4eb22eabe4b7032f",
           "after": "sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082"}
# Hand-derived from SCORING.md for L = 0.75 m: theta(t) = (pi/4) * min(t, 1);
# centre = (-1 + L cos(theta)/2, 0.2 t + L sin(theta)/2, 0); WXYZ = (cos(theta/2), 0, 0, sin(theta/2)).
HAND = {0.25: ([-0.63220552, 0.12315887, 0.0], [0.99518473, 0.0, 0.0, 0.09801714]),
        1.0: ([-0.73483496, 0.46516504, 0.0], [0.92387953, 0.0, 0.0, 0.38268343]),
        2.0: ([-0.73483496, 0.66516504, 0.0], [0.92387953, 0.0, 0.0, 0.38268343])}


def state(name):
    sources = {"main.ok": (PROOF / f"{name}.main.ok").read_bytes(), "hinges.ok": (PROOF / "hinges.ok").read_bytes()}
    artifacts = {"scene.glb": (PROOF / f"{name}.glb").read_bytes(), "scene.semantic.json": (PROOF / f"{name}.semantic.json").read_bytes()}
    return sources, artifacts


def v1_inputs():
    (s0, a0), (s1, a1) = state("before"), state("after")
    authority = {"schema": O.AUTHORITY_SCHEMA, "attemptId": "test-V1", "caseId": "V1",
                 "start": {"acceptedRevision": "test:start", "programRevision": PROGRAM["before"], "sourceFiles": s0, "artifacts": a0},
                 "candidate": {"candidateId": PROGRAM["after"], "parentAcceptedRevision": "test:start", "sourceFiles": s1, "artifacts": a1},
                 "retained": {"acceptedRevision": "test:final", "programRevision": PROGRAM["after"], "sourceFiles": s1, "artifacts": a1},
                 "rebuild": {"sourceFiles": s1, "artifacts": a1, "cleanWorkspace": True, "declaredInputs": ["hinges.ok", "main.ok"], "determinism": "byte-exact"},
                 "decision": {"status": "accepted", "candidateId": PROGRAM["after"], "parentAcceptedRevision": "test:start",
                              "acceptedRevision": "test:final", "boundary": "staged-before-accepted-replacement",
                              "invalidEverAccepted": False, "diagnostic": None}}
    return authority, score.observe_artifacts(s0, a0), score.observe_artifacts(s1, a1), a1


class Scoring(unittest.TestCase):
    def setUp(self):
        self.authority, self.start, self.final, self.artifacts = v1_inputs()

    def run_score(self, final=None, authority=None):
        return score.score_case(CORPUS, "V1", authority or self.authority, self.start, final or self.final,
                                final or self.final, self.artifacts, {"runner completed": True})

    def test_correct_v1_state_passes_with_a_full_table(self):
        result = self.run_score()
        self.assertTrue(result["passed"], result["c255"]["faults"])
        self.assertTrue(result["c255"]["componentPass"])
        self.assertEqual(sum(r["property"].startswith("semantic.objects[") for r in result["properties"]), 18)
        self.assertEqual(sum(r["property"].startswith("semantic.sites[") for r in result["properties"]), 34)
        self.assertEqual(len(result["poses"]), 126)
        self.assertEqual(result["locality"]["unrelatedObjectsUnchanged"], 16)
        self.assertEqual(result["locality"]["secondRackObjects"], 11)

    def test_three_hand_computed_blade_poses(self):
        expected = {p["time_s"]: p for p in O.expected_state(CORPUS, "V1")["poses"] if p["id"] == score.SELECTED_BLADE}
        observed = {p["time_s"]: p for p in self.final["delivery"]["poses"] if p["id"] == score.SELECTED_BLADE}
        for t, (centre, rotation) in HAND.items():
            for a, b in zip(centre, expected[t]["position_m"]):
                self.assertAlmostEqual(a, b, delta=1e-8)
            for a, b in zip(centre, observed[t]["position_m"]):
                self.assertAlmostEqual(a, b, delta=O.DELIVERY_POSITION)
            self.assertLessEqual(O.quaternion_angle(rotation, expected[t]["rotation_wxyz"]), 1e-7)
            self.assertLessEqual(O.quaternion_angle(rotation, observed[t]["rotation_wxyz"]), O.DELIVERY_ANGLE)

    def test_a_wrong_observed_field_fails_the_case(self):
        cases = {}
        wrong_unit = copy.deepcopy(self.final)
        wrong_unit["semantic"]["semantic"]["units"]["length"] = "mm"
        cases["units"] = wrong_unit
        wrong_pose = copy.deepcopy(self.final)
        row = next(p for p in wrong_pose["delivery"]["poses"] if p["id"] == score.SELECTED_BLADE and p["time_s"] == 1.0)
        row["position_m"][1] += 0.002
        row["matrix"][7] += 0.002
        cases["pose"] = wrong_pose
        sibling = copy.deepcopy(self.final)
        obj = next(o for o in sibling["semantic"]["semantic"]["objects"] if o["path"] == 'second.fingers["top"].blade')
        obj["primitive"]["size_m"][0] = 0.75
        cases["sibling"] = sibling
        missing = copy.deepcopy(self.final)
        missing["semantic"]["semantic"]["sites"].pop()
        cases["missing site"] = missing
        for label, final in cases.items():
            with self.subTest(label):
                result = self.run_score(final=final)
                self.assertFalse(result["passed"])
                self.assertFalse(result["c255"]["componentPass"])
                self.assertTrue(any(r["outcome"] == "failed" for r in result["properties"]))

    def test_an_equivalent_quaternion_sign_is_not_a_change(self):
        flipped = copy.deepcopy(self.final)
        for row in flipped["delivery"]["poses"]:
            row["rotation_wxyz"] = [-x for x in row["rotation_wxyz"]]
        result = score.score_case(CORPUS, "V1", self.authority, self.start, flipped, flipped, self.artifacts,
                                  {"runner completed": True})
        self.assertTrue(result["c255"]["componentPass"])
        self.assertTrue(result["locality"]["passed"], result["locality"])
        self.assertEqual(result["locality"]["movedObjects"], ["/".join(score.SELECTED_BLADE)])
        self.assertTrue(result["passed"])

    def test_a_service_success_field_is_not_the_case_result(self):
        result = score.score_case(CORPUS, "V1", self.authority, self.start, self.final, self.final, self.artifacts,
                                  {"runner completed": True, "service status succeeded": True, "rebuild clean": False})
        self.assertTrue(result["c255"]["componentPass"])
        self.assertFalse(result["passed"])

    def test_no_product_module_is_imported(self):
        tree = ast.parse((HERE / "score.py").read_text())
        names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(any(n.split(".")[0] == "ontokin" for n in names))


if __name__ == "__main__":
    unittest.main()
