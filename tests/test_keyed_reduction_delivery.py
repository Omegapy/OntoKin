"""Verify source/version isolation and actual inherited .15 binary streams."""
from __future__ import annotations

import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

from ontokin.budget_runtime import execute_keyed_reduction_export, execute_keyed_transform_export
from ontokin.cli import main as cli_main
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.gltf import export_glb, validate_export
from ontokin.profile_capabilities import KEYED_REDUCTION_PROFILE
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions
from ontokin.texture_bundle import load_texture_file_manifest
from tests.test_texture_delivery import decode, encode


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-reduction"
TARGET = "ontokin.glb/0.15"
OPTIONS = ExportOptions(fps=4, end="1", helpers=False)


class KeyedReductionDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = load_texture_file_manifest(FIXTURES / "panel-identity.files.json")
        cls.control = load_texture_file_manifest(FIXTURES / "control-panel-identity.files.json")
        cls.result = execute_keyed_reduction_export(cls.program, options=OPTIONS)
        cls.old = execute_keyed_transform_export(cls.control, options=OPTIONS)
        if cls.result.data is None or cls.old.data is None:
            raise AssertionError((cls.result.report, cls.old.report))
        cls.document, cls.binary = decode(cls.result.data)
        cls.old_document, cls.old_binary = decode(cls.old.data)

    def compile(self):
        ledger = SharedExecutionBudget()
        admit_entry_budget(self.program.entry, ledger, profile=KEYED_REDUCTION_PROFILE)
        compiler = compile_construction(self.program, level="evaluated", execution_budget=ledger)
        return compiler, ReachExecutionWork(execution_budget=ledger)

    def test_equivalent_reduction_preserves_complete_bin_and_layouts(self):
        self.assertEqual(self.binary, self.old_binary)
        self.assertEqual(self.document["accessors"], self.old_document["accessors"])
        self.assertEqual(self.document["bufferViews"], self.old_document["bufferViews"])
        self.assertEqual(self.document["textures"], self.old_document["textures"])
        self.assertEqual(self.document["samplers"], self.old_document["samplers"])
        self.assertEqual(self.document["animations"][0]["samplers"], self.old_document["animations"][0]["samplers"])
        self.assertEqual(self.document["animations"][0]["channels"], self.old_document["animations"][0]["channels"])
        self.assertEqual(self.document["extras"]["ontokin"]["target_contract"], TARGET)
        self.assertEqual(self.document["extras"]["ontokin"]["profile"], KEYED_REDUCTION_PROFILE)
        self.assertEqual(self.old_document["extras"]["ontokin"]["target_contract"], "ontokin.glb/0.14")
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

    def test_explicit_versions_refuse_each_others_source_and_default_remains_core(self):
        self.assertIsNone(execute_keyed_transform_export(self.program, options=OPTIONS).data)
        self.assertIsNone(execute_keyed_reduction_export(self.control, options=OPTIONS).data)
        compiler, work = self.compile()
        with self.assertRaises(OntoKinError):
            export_glb(compiler.model, options=OPTIONS)

    def test_current_caller_cap_cannot_publish_partial_binary(self):
        result = execute_keyed_reduction_export(self.program, options=OPTIONS, caller_caps={"max_operations": 1})
        self.assertIsNone(result.data)
        self.assertIn("OKL-E-RESOURCE", [d["code"] for d in result.report["diagnostics"]])
        self.assertNotEqual(result.report["outcome"], "valid")

    def test_cli_explicit_files_transport_delivers_and_preserves_source_assets(self):
        with tempfile.TemporaryDirectory(prefix="ontokin-c082-cli-") as directory:
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
