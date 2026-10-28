"""Adopted reach source binding and profile isolation, before admission."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"


def bundle(name):
    return load_file_manifest(DATA / (name.lower() + ".files.json"))


def edited(source, old, new):
    if source.entry.text.count(old) != 1:
        raise AssertionError("The test edit must name one exact source occurrence.")
    return ProgramBundle(replace(source.entry, raw=source.entry.text.replace(old, new).encode()), source.modules)


class ReachSourceTests(unittest.TestCase):
    def test_real_chain_payload_is_frozen_and_has_no_admission(self):
        compiler = compile_construction(bundle("P01"))
        action = compiler.model.actions["reach"]
        payload = action.reach
        self.assertEqual(compiler.model.profile, "planar-reach-0.1")
        self.assertEqual(payload.shoulder, "rig.arm.shoulder")
        self.assertEqual(payload.elbow, "rig.arm.elbow")
        self.assertEqual(payload.tip, "rig.arm.forearm.tip")
        self.assertEqual(payload.base_frame, "rig.arm.pivot.frame")
        self.assertEqual(payload.lengths_m, (1.0, 1.0))
        self.assertEqual(payload.target_m, (1.0, 1.0, 0.0))
        self.assertEqual(payload.description_identity, action.element_id)
        self.assertIsNotNone(compiler.reach_work)
        self.assertFalse(hasattr(payload, "target_rad"))
        self.assertFalse(hasattr(compiler.model, "reach_work"))
        with self.assertRaises(FrozenInstanceError):
            payload.branch = "elbow_negative"

    def test_admission_failures_are_not_elaboration(self):
        for case in ("N01", "N02", "N03", "N06", "N09"):
            with self.subTest(case=case):
                compiler = compile_construction(bundle(case))
                self.assertTrue(compiler.model.actions["reach"].reach)

    def test_frozen_structural_and_type_failures(self):
        cases = {"N04": "reach_frame", "N05": "reach_frame", "N07": "reach_domain",
                 "N08": "reach_type", "N10": "reach_chain", "N11": "reach_resource",
                 "N12": "reach_domain", "N13": "reach_resource", "N14": "reach_domain",
                 "N15": "reach_chain"}
        for case, expected in cases.items():
            with self.subTest(case=case), self.assertRaises(OntoKinError) as caught:
                compile_construction(bundle(case))
            self.assertEqual(caught.exception.diagnostic.details.get("reach_code"), expected)

    def test_named_aliases_share_description_but_not_occurrence(self):
        source = bundle("P01")
        source = edited(source, '    at 0[s] sequence { start reach; }',
                        '    action alias @ "alias" = reach;\n    at 0[s] sequence { start reach; }')
        model = compile_construction(source).model
        first, alias = model.actions["reach"], model.actions["alias"]
        self.assertNotEqual(first.element_id, alias.element_id)
        self.assertEqual(first.reach.description_identity, alias.reach.description_identity)
        self.assertEqual(first.reach.source_location, alias.reach.source_location)

    def test_new_names_remain_ordinary_names_in_older_profile(self):
        text = '''ontokin "0.5";
module Older @ "older";
profile "force-0.1";
public fn elbow_positive @ "ordinary"(reach_planar: Int) -> Int { return reach_planar; }
scene Demo @ "demo" { duration = 1[s]; gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]); }
'''
        compiler = compile_construction(ProgramBundle(SourceUnit("entry", "older.ok", text.encode())))
        self.assertEqual(compiler.model.profile, "force-0.1")
        self.assertIsNone(compiler.reach_work)

    def test_older_entry_cannot_import_reach_definition(self):
        source = bundle("P01")
        source = edited(source, 'ontokin "0.6";', 'ontokin "0.5";')
        source = edited(source, 'profile "planar-reach-0.1";', 'profile "force-0.1";')
        with self.assertRaises(OntoKinError) as caught:
            compile_construction(source)
        self.assertEqual(caught.exception.diagnostic.category, "unsupported")
        self.assertEqual(caught.exception.diagnostic.details.get("dependency_profile"), "planar-reach-0.1")

    def test_source_budget_and_callback_are_not_numeric_success(self):
        marker = RuntimeError("request interrupted")
        def check():
            raise marker
        with self.assertRaises(RuntimeError) as caught:
            compile_construction(bundle("P01"), check=check)
        self.assertIs(caught.exception, marker)
        with self.assertRaises(OntoKinError) as caught:
            compile_construction(bundle("P01"), budgets={"max_operations": 1})
        self.assertEqual(caught.exception.diagnostic.category, "resource_limit")


if __name__ == "__main__":
    unittest.main()
