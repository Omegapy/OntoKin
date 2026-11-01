"""Verify source/version isolation and actual inherited .16 binary streams."""
from __future__ import annotations

import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

from ontokin.budget_runtime import execute_keyed_filter_export, execute_keyed_reduction_export
from ontokin.bundle import SourceUnit
from ontokin.cli import main as cli_main
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.gltf import export_glb, validate_export
from ontokin.profile_capabilities import KEYED_FILTER_PROFILE, KEYED_REDUCTION_PROFILE
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions
from ontokin.texture_bundle import TextureBundle, load_texture_file_manifest
from tests.test_texture_delivery import decode, encode


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-filter"
TARGET = "ontokin.glb/0.16"
OPTIONS = ExportOptions(fps=4, end="1", helpers=False)
AUTHORITY_PATHS = (("extras",), ("extras", "ontokin"), ("extras", "ontokin", "source"),
    ("nodes", 0, "extras"), ("nodes", 0, "extras", "ontokin"),
    ("animations", 0, "extras"), ("animations", 0, "extras", "ontokin"),
    ("asset", "extras"), ("scenes", 0, "extras"), ("meshes", 0, "extras"),
    ("meshes", 0, "primitives", 0, "extras"), ("materials", 0, "extras"))


class KeyedFilterDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = load_texture_file_manifest(FIXTURES / "panel-identity.files.json")
        cls.control = load_texture_file_manifest(FIXTURES / "control-panel-identity.files.json")
        cls.result = execute_keyed_filter_export(cls.program, options=OPTIONS)
        cls.old = execute_keyed_reduction_export(cls.control, options=OPTIONS)
        if cls.result.data is None or cls.old.data is None:
            raise AssertionError((cls.result.report, cls.old.report))
        cls.document, cls.binary = decode(cls.result.data)
        cls.old_document, cls.old_binary = decode(cls.old.data)

    def compile(self, program=None, profile=KEYED_FILTER_PROFILE):
        program = self.program if program is None else program
        ledger = SharedExecutionBudget()
        admit_entry_budget(program.entry, ledger, profile=profile)
        compiler = compile_construction(program, level="evaluated", execution_budget=ledger)
        return compiler, ReachExecutionWork(execution_budget=ledger)

    def test_equivalent_filter_preserves_complete_bin_and_layouts(self):
        self.assertEqual(self.binary, self.old_binary)
        self.assertEqual(self.document["accessors"], self.old_document["accessors"])
        self.assertEqual(self.document["bufferViews"], self.old_document["bufferViews"])
        self.assertEqual(self.document["textures"], self.old_document["textures"])
        self.assertEqual(self.document["samplers"], self.old_document["samplers"])
        self.assertEqual(self.document["animations"][0]["samplers"], self.old_document["animations"][0]["samplers"])
        self.assertEqual(self.document["animations"][0]["channels"], self.old_document["animations"][0]["channels"])
        self.assertEqual(self.document["extras"]["ontokin"]["target_contract"], TARGET)
        self.assertEqual(self.document["extras"]["ontokin"]["profile"], KEYED_FILTER_PROFILE)
        self.assertEqual(self.old_document["extras"]["ontokin"]["target_contract"], "ontokin.glb/0.15")
        self.assertNotEqual(self.result.data, self.old.data)

    def test_inherited_texture_obligations_reject_supplied_mutations_with_honest_target(self):
        for mutation in ("sampler", "png", "normal_map"):
            with self.subTest(mutation=mutation):
                document, binary = copy.deepcopy(self.document), bytearray(self.binary)
                if mutation == "sampler":
                    document["samplers"][0]["wrapS"] = 10497
                elif mutation == "png":
                    view = document["bufferViews"][document["images"][0]["bufferView"]]
                    binary[view["byteOffset"] + 32] ^= 1
                else:
                    document["materials"][0]["normalTexture"] = {"index": 0}
                compiler, work = self.compile()
                with self.assertRaises(OntoKinError) as caught:
                    validate_export(encode(document, bytes(binary)), compiler.model,
                        options=OPTIONS, target_contract=TARGET, work=work)
                self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")
                self.assertEqual(caught.exception.diagnostic.details.get("target_contract"), TARGET)

    def test_supplied_unknown_authority_fields_are_refused_without_changing_positive_bytes(self):
        compiler, work = self.compile()
        self.assertEqual(validate_export(self.result.data, compiler.model, options=OPTIONS,
            target_contract=TARGET, work=work)["status"], "passed")
        for path in AUTHORITY_PATHS:
            with self.subTest(path=path):
                document = copy.deepcopy(self.document)
                owner = document
                for key in path:
                    owner = owner.setdefault(key, {}) if isinstance(owner, dict) else owner[key]
                owner["extension_claim"] = {"arbitrary": True}
                compiler, work = self.compile()
                with self.assertRaises(OntoKinError) as caught:
                    validate_export(encode(document, self.binary), compiler.model, options=OPTIONS,
                        target_contract=TARGET, work=work)
                self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")
                self.assertEqual(caught.exception.diagnostic.details.get("target_contract"), TARGET)

    def test_legitimate_visual_helper_metadata_remains_supported(self):
        options = ExportOptions(fps=4, end="1", helpers=True)
        result = execute_keyed_filter_export(self.program, options=options)
        self.assertIsNotNone(result.data, result.report)
        document, _ = decode(result.data)
        self.assertTrue(any(node["extras"]["ontokin"]["kind"] == "visual_helper"
                            for node in document["nodes"]))
        compiler, work = self.compile()
        self.assertEqual(validate_export(result.data, compiler.model, options=options,
            target_contract=TARGET, work=work)["status"], "passed")

    def test_recognized_metadata_names_cannot_move_to_another_geometry_or_helper_kind(self):
        options = ExportOptions(fps=4, end="1", helpers=True)
        result = execute_keyed_filter_export(self.program, options=options)
        self.assertIsNotNone(result.data, result.report)
        original, binary = decode(result.data)
        for mutation in ("empty_surface", "assembly_joint_path", "assembly_meaning",
                         "helper_primitive_region", "helper_material_region"):
            with self.subTest(mutation=mutation):
                document = copy.deepcopy(original)
                helper = next(node for node in document["nodes"]
                    if node["extras"]["ontokin"].get("helper_kind") == "assembly_origin")
                if mutation == "empty_surface":
                    node = next(node for node in document["nodes"]
                        if node["extras"]["ontokin"].get("geometry", {}).get("kind") == "empty")
                    node["extras"]["ontokin"]["surface"] = {}
                elif mutation.startswith("assembly_"):
                    helper["extras"]["ontokin"][mutation.removeprefix("assembly_")] = "unrelated"
                else:
                    primitive = document["meshes"][helper["mesh"]]["primitives"][0]
                    if mutation == "helper_primitive_region":
                        primitive["extras"] = {"ontokin": {"region_key": "top"}}
                    else:
                        document["materials"][primitive["material"]]["extras"] = {
                            "ontokin": {"source_region_key": "top", "occurrence_path": "first",
                                        "element_id": [], "program_revision": self.program.program_revision}}
                compiler, work = self.compile()
                with self.assertRaises(OntoKinError) as caught:
                    validate_export(encode(document, binary), compiler.model, options=options,
                        target_contract=TARGET, work=work)
                self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")

    def test_primitive_geometry_and_both_helper_kinds_keep_their_legitimate_metadata(self):
        source = '''ontokin "0.16";
module Helpers @ "helpers";
profile "keyed-filter-0.1";
public class Tip @ "tip-class" {
 geometry = box(vec3(1[m], 0.2[m], 0.2[m]));
 physical = no_body();
}
public class Rig @ "rig-class" {
 geometry = empty();
 physical = no_body();
 public part tip @ "tip": Tip {}
 public joint turn @ "turn": hinge {
  parent = self.origin;
  child = self.tip.origin;
  axis = vec3(0, 0, 1);
  limits = range(-1[rad], 1[rad]);
  initial = 0[rad];
 }
}
scene Demo @ "demo" {
 duration = 1[s];
 gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
 object rig @ "rig": Rig {}
}
'''
        program = TextureBundle(SourceUnit("entry", "helpers.ok", source.encode()), ())
        options = ExportOptions(fps=4, end="1", helpers=True)
        result = execute_keyed_filter_export(program, options=options)
        self.assertIsNotNone(result.data, result.report)
        document, binary = decode(result.data)
        helpers = [node["extras"]["ontokin"] for node in document["nodes"]
                   if node["extras"]["ontokin"]["kind"] == "visual_helper"]
        self.assertEqual({row["helper_kind"] for row in helpers}, {"assembly_origin", "joint_parent_site"})
        compiler, work = self.compile(program)
        self.assertEqual(validate_export(result.data, compiler.model, options=options,
            target_contract=TARGET, work=work)["status"], "passed")
        joint_helper = next(row for row in helpers if row["helper_kind"] == "joint_parent_site")
        joint_helper["object_path"] = "rig"
        compiler, work = self.compile(program)
        with self.assertRaises(OntoKinError) as caught:
            validate_export(encode(document, binary), compiler.model, options=options,
                target_contract=TARGET, work=work)
        self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")

    def test_legacy_supplied_metadata_policy_is_unchanged(self):
        for path in AUTHORITY_PATHS:
            with self.subTest(path=path):
                document = copy.deepcopy(self.old_document)
                owner = document
                for key in path:
                    owner = owner.setdefault(key, {}) if isinstance(owner, dict) else owner[key]
                owner["extension_claim"] = {"arbitrary": True}
                compiler, work = self.compile(self.control, KEYED_REDUCTION_PROFILE)
                self.assertEqual(validate_export(encode(document, self.old_binary), compiler.model,
                    options=OPTIONS, target_contract="ontokin.glb/0.15", work=work)["status"], "passed")

    def test_metadata_validation_preserves_current_callback_exception(self):
        from ontokin.texture_gltf import _ACTIVE_TARGET
        class Cancelled(Exception):
            pass
        failure = Cancelled("stop during .16 metadata validation")
        compiler, work = self.compile()
        def cancel():
            if _ACTIVE_TARGET.get() == TARGET:
                raise failure
        work.execution_budget.check = cancel
        with self.assertRaises(Cancelled) as caught:
            validate_export(self.result.data, compiler.model, options=OPTIONS,
                target_contract=TARGET, work=work)
        self.assertIs(caught.exception, failure)
        self.assertIs(work.execution_budget.callback_error, failure)
        self.assertNotEqual(_ACTIVE_TARGET.get(), TARGET)

    def test_explicit_versions_refuse_each_others_source_and_default_remains_core(self):
        self.assertIsNone(execute_keyed_reduction_export(self.program, options=OPTIONS).data)
        self.assertIsNone(execute_keyed_filter_export(self.control, options=OPTIONS).data)
        compiler, work = self.compile()
        with self.assertRaises(OntoKinError):
            export_glb(compiler.model, options=OPTIONS)

    def test_current_caller_cap_cannot_publish_partial_binary(self):
        result = execute_keyed_filter_export(self.program, options=OPTIONS, caller_caps={"max_operations": 1})
        self.assertIsNone(result.data)
        self.assertIn("OKL-E-RESOURCE", [d["code"] for d in result.report["diagnostics"]])
        self.assertNotEqual(result.report["outcome"], "valid")

    def test_cli_explicit_files_transport_delivers_and_preserves_source_assets(self):
        with tempfile.TemporaryDirectory(prefix="ontokin-c083-cli-") as directory:
            target = Path(directory) / "panel.glb"
            output = io.StringIO()
            original_asset = (FIXTURES / "assets/label.png").read_bytes()
            with redirect_stdout(output):
                code = cli_main(["export", str(FIXTURES / "panel-identity.files.json"), "--bundle",
                    "--target", TARGET, "--output", str(target), "--fps", "4", "--end", "1", "--no-helpers"])
            self.assertEqual(code, 0, output.getvalue())
            document, binary = decode(target.read_bytes())
            self.assertEqual(binary, self.binary)
            self.assertEqual(document["extras"]["ontokin"]["target_contract"], TARGET)
            self.assertEqual((FIXTURES / "assets/label.png").read_bytes(), original_asset)
            rejected = Path(directory) / "wrong-default.glb"
            with redirect_stdout(io.StringIO()):
                code = cli_main(["export", str(FIXTURES / "panel-identity.files.json"), "--bundle", "--output", str(rejected)])
            self.assertNotEqual(code, 0)
            self.assertFalse(rejected.exists())


if __name__ == "__main__":
    unittest.main()
