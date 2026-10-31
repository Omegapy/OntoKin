"""Actual source closure, immutable recipes, and independently frozen UVs."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.bundle import ProgramBundle, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.surface import SurfaceError
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.texture_png import validate_png
from ontokin.texture_runtime import (PlanarUVData, TextureBindingData, TextureImageData,
                                     TEXTURE_PROFILE, texture_coordinates, texture_metadata)
from ontokin.values import bounded_data


FIXTURES = Path(__file__).resolve().parents[1] / "examples/textured-surfaces"
CORRECTIONS = FIXTURES.with_name("textured-surfaces-corrections")
CASES = {case["name"]: case for case in json.loads((FIXTURES / "expected.json").read_text())["cases"]}


def compile_case(name, *, policy=None, corrected=False):
    # Selection is explicit: the original failed positive inputs never change
    # meaning or silently acquire the separately published correction bytes.
    base = CORRECTIONS if corrected else FIXTURES
    case = json.loads((base / "cases" / (name + ".expected.json")).read_bytes()) if corrected else CASES[name]
    bundle = load_texture_file_manifest(base / case["file_manifest"])
    authority = HostPolicy(**case["host_policy"]) if policy is None else policy
    ledger = SharedExecutionBudget(authority)
    admit_entry_budget(bundle.entry, ledger, profile=TEXTURE_PROFILE)
    return compile_construction(bundle, level="represented", execution_budget=ledger)


def direct_geometry(*, origin=(0., 0., 0.), u=(1., 0., 0.), v=(0., 1., 0.), offset=(0., 0.)):
    mapping = PlanarUVData(origin, u, v, offset, "sha256:" + "0" * 64, "entry", 10, 20)
    binding = TextureBindingData(TextureImageData("label", "sha256:" + "1" * 64),
                                 mapping, "entry", 5, 25)
    return {"kind": "extrusion", "texture_bindings": (("top", binding),)}


def direct_mesh(positions, indices=(0, 1, 2)):
    return SimpleNamespace(positions=tuple(positions),
                           regions=(SimpleNamespace(key="top", indices=indices),))


class TextureRuntimeTests(unittest.TestCase):
    def test_frozen_mapping_probes_match_exact_binary64_on_raw_corners(self):
        for name in ("rgb-panel", "reflection", "shear", "offset-clamp", "origin-boundary",
                     "basis-and-uv-boundary", "offset-boundary", "exact-rank-no-epsilon",
                     "uv-binary32-underflow", "exact-rational-uv", "placed-mapping",
                     "uv-line-projection", "marked-tray"):
            with self.subTest(case=name):
                compiler = compile_case(name)
                obj = compiler.model.objects["shape"]
                mesh = compiler.surface_meshes["shape"]["mesh"]
                actual = texture_coordinates(obj.geometry, mesh)
                metadata = texture_metadata(obj.geometry)
                for binding in CASES[name]["texture_bindings"]:
                    region = next(region for region in mesh.regions if region.key == binding["region"])
                    coordinates = actual[region.key]
                    self.assertEqual(len(coordinates), len(mesh.positions))
                    self.assertEqual(metadata[region.key]["asset_id"], binding["asset_id"])
                    for probe in binding["uv_probes"]:
                        indices = [index for index in region.indices
                                   if mesh.positions[index] == tuple(probe["position_m"])]
                        self.assertTrue(indices, probe)
                        for index in indices:
                            self.assertEqual([value.hex() for value in coordinates[index]],
                                             probe["uv_binary64_hex"])

    def test_texture_wrapper_preserves_the_entire_legacy_raw_mesh(self):
        compiler = compile_case("rgb-panel")
        bundle = load_file_manifest(FIXTURES / CASES["rgb-panel"]["untextured_control"]["file_manifest"])
        ledger = SharedExecutionBudget()
        admit_entry_budget(bundle.entry, ledger, profile="polygon-pockets-0.1")
        control = compile_construction(bundle, level="represented", execution_budget=ledger)
        self.assertEqual(compiler.surface_meshes["shape"]["mesh"],
                         control.surface_meshes["shape"]["mesh"])
        geometry = compiler.model.objects["shape"].geometry
        self.assertEqual(geometry["kind"], "extrusion")
        encoded = json.dumps(bounded_data(geometry), allow_nan=False)
        self.assertNotIn("data_base64", encoded)
        self.assertNotIn("pixel_sha256", encoded)
        exposed = texture_metadata(geometry)
        exposed["top"]["origin_m"][0] = 100
        self.assertEqual(texture_metadata(geometry)["top"]["origin_m"][0], 0)

    def test_all_reachable_definitions_declare_images_but_each_image_decodes_once(self):
        for name in ("assembly", "generated", "uninstantiated-declaration", "repeated-same-declaration"):
            with self.subTest(case=name), patch("ontokin.texture_runtime.validate_png", wraps=validate_png) as decode:
                compiler = compile_case(name)
                self.assertEqual(decode.call_count, len(compiler.bundle.assets))
                self.assertEqual(set(compiler.model.texture_assets), set(compiler.model.texture_info))
                self.assertEqual(set(compiler.texture_requirements), set(compiler.model.texture_assets))
                for ident, nodes in compiler.texture_requirements.items():
                    self.assertTrue(nodes, ident)
                    self.assertTrue(all(node.source_id in compiler.linked.modules for node in nodes))
        self.assertEqual(set(compile_case("assembly").model.texture_assets), {"label", "alternate"})

    def test_older_user_functions_comments_and_strings_do_not_declare_assets(self):
        for name, corrected in (("older-user-function-png-asset", True), ("empty-assets-untextured", False)):
            with self.subTest(case=name):
                compiler = compile_case(name, corrected=corrected)
                self.assertEqual(compiler.model.texture_assets, {})
                self.assertEqual(compiler.texture_requirements, {})
                if corrected:
                    self.assertEqual(compiler.bundle.program_revision,
                                     "sha256:d1502ccd632d4353721ec2ea5503228222c53d261f6cfc15f5b91ad756e413b8")
        commented = compile_case("comments-and-strings")
        self.assertEqual(set(commented.texture_requirements), {"label"})
        self.assertEqual(set(commented.model.texture_assets), {"label"})

    def test_original_invalid_positive_inputs_keep_their_observed_refusals(self):
        for name, code in (("older-user-function-png-asset", "OKL-E-SYNTAX"),
                           ("inherited-loft", "OKL-E-SURFACE-FACETS")):
            with self.subTest(original_case=name):
                self.assertEqual(CASES[name]["expected_outcome"], "valid")
                with self.assertRaises(OntoKinError) as rejected:
                    compile_case(name)
                self.assertEqual(rejected.exception.code, code)

    def test_published_corrected_loft_preserves_its_separate_eight_facet_control(self):
        self.assertEqual(hashlib.sha256((CORRECTIONS / "correction-freeze.json").read_bytes()).hexdigest(),
                         "326bc42a792e18d36452f04432a18cf40be4b011995f1372c2f58ba9daa0b755")
        compiler = compile_case("inherited-loft", corrected=True)
        self.assertEqual(compiler.bundle.program_revision,
                         "sha256:cc5a7407912b4e723b40f91d10a5b2649ba7eb758cbee6d35377ad790a89a1a9")
        case = json.loads((CORRECTIONS / "cases/inherited-loft.expected.json").read_bytes())
        bundle = load_file_manifest(CORRECTIONS / case["untextured_control"]["file_manifest"])
        ledger = SharedExecutionBudget()
        admit_entry_budget(bundle.entry, ledger, profile="polygon-pockets-0.1")
        control = compile_construction(bundle, level="represented", execution_budget=ledger)
        mesh = compiler.surface_meshes["shape"]["mesh"]
        self.assertEqual(mesh, control.surface_meshes["shape"]["mesh"])
        self.assertEqual((mesh.triangle_count, len(set(mesh.positions))), (32, 18))
        coordinates = texture_coordinates(compiler.model.objects["shape"].geometry, mesh)["side"]
        for probe in case["texture_bindings"][0]["uv_probes"]:
            indices = [index for index, point in enumerate(mesh.positions)
                       if point == tuple(probe["position_m"])]
            self.assertTrue(indices, probe)
            for index in indices:
                self.assertEqual([value.hex() for value in coordinates[index]], probe["uv_binary64_hex"])

    def test_unused_palette_binding_still_admits_image_but_emits_no_uv_rows(self):
        compiler = compile_case("unused-palette-binding")
        geometry = compiler.model.objects["shape"].geometry
        mesh = compiler.surface_meshes["shape"]["mesh"]
        self.assertEqual(texture_coordinates(geometry, mesh), {})
        self.assertEqual(set(texture_metadata(geometry)), {"unused"})
        self.assertEqual(set(compiler.model.texture_info), {"label"})

    def test_frozen_closure_mapping_region_and_type_refusals_keep_diagnostics(self):
        codes = {"OKL-E-ASSET-CLOSURE", "OKL-E-TEXTURE-MAPPING", "OKL-E-TEXTURE-REGION", "OKL-E-TYPE"}
        for name, case in CASES.items():
            if case["expected_code"] not in codes:
                continue
            with self.subTest(case=name), self.assertRaises(OntoKinError) as rejected:
                compile_case(name)
            self.assertEqual(rejected.exception.code, case["expected_code"])
            self.assertIsNotNone(rejected.exception.diagnostic.node.source_id)

    def test_png_failure_has_the_declaring_call_source_span(self):
        with self.assertRaises(OntoKinError) as rejected:
            compile_case("png-nonopaque-alpha")
        self.assertEqual(rejected.exception.code, "OKL-E-PNG")
        node = rejected.exception.diagnostic.node
        self.assertEqual(node.source_id, "entry")
        self.assertEqual(node.kind, "call")
        self.assertEqual(node.callee.name, "png_asset")

    def test_texture_signature_dimension_errors_use_the_adopted_type_family(self):
        for name in ("wrong-origin-unit", "wrong-basis-unit"):
            with self.subTest(case=name):
                with self.assertRaises(OntoKinError) as rejected:
                    compile_case(name)
                self.assertEqual(rejected.exception.code, "OKL-E-TYPE")
                self.assertEqual(rejected.exception.diagnostic.phase, "type")

    def test_explicit_bundle_profile_and_current_host_authority_are_required(self):
        source = load_texture_file_manifest(FIXTURES / "empty-assets-untextured.files.json")
        old = ProgramBundle(source.entry, source.modules)
        ledger = SharedExecutionBudget()
        admit_entry_budget(old.entry, ledger, profile=TEXTURE_PROFILE)
        with self.assertRaises(OntoKinError) as rejected:
            compile_construction(old, execution_budget=ledger)
        self.assertEqual(rejected.exception.code, "OKL-E-ASSET-CLOSURE")
        with self.assertRaises(OntoKinError) as rejected:
            compile_case("maximum-decoded-default-budget")
        self.assertEqual(rejected.exception.code, "OKL-E-RESOURCE")
        first = compile_case("maximum-decoded-one")
        self.assertGreater(first.budget.execution_budget.operations, 262144)
        with self.assertRaises(OntoKinError) as rejected:
            compile_case("maximum-decoded-one", policy=HostPolicy())
        self.assertEqual(rejected.exception.code, "OKL-E-RESOURCE")

    def test_exact_dot_product_rounds_once_and_ignores_unreferenced_corners(self):
        geometry = direct_geometry(origin=(-.2, 0., 0.), offset=(-.3, 0.))
        mesh = direct_mesh(((.1, 0., 0.), (0., 1., 0.), (0., 0., 1.), (1.e100, 1.e100, 1.e100)))
        coordinates = texture_coordinates(geometry, mesh)["top"]
        self.assertEqual(coordinates[0][0], 2. ** -55)
        self.assertNotEqual(coordinates[0][0], (.1 - -.2) - .3)
        self.assertEqual(coordinates[3], (0., 0.))
        placed = {"kind": "placed", "surface": geometry, "local_position": (100., 50., -4.),
                  "local_rotation": (0., 0., 0., 1.)}
        self.assertEqual(texture_coordinates(placed, mesh)["top"], coordinates)

    def test_exact_rank_subnormal_underflow_and_uv_line_are_accepted(self):
        tiny = float.fromhex("0x0.0000000000001p-1022")
        geometry = direct_geometry(u=(tiny, 0., 0.), v=(0., tiny, 0.))
        mesh = direct_mesh(((.5, 0., 0.), (1., 0., 0.), (0., 1., 0.)))
        coordinates = texture_coordinates(geometry, mesh)["top"]
        self.assertEqual(coordinates, ((0., 0.), (tiny, 0.), (0., tiny)))
        line = direct_mesh(((0., 0., 0.), (1., 0., 0.), (0., 0., 1.)))
        self.assertEqual(texture_coordinates(direct_geometry(), line)["top"],
                         ((0., 0.), (1., 0.), (0., 0.)))

    def test_numeric_operand_limit_and_callback_errors_remain_visible(self):
        mesh = direct_mesh(((1 << 32768, 0, 0), (0, 1, 0), (0, 0, 1)))
        with self.assertRaises(SurfaceError) as rejected:
            texture_coordinates(direct_geometry(), mesh)
        self.assertEqual(rejected.exception.code, "OKL-E-RESOURCE")
        cancelled = RuntimeError("cancel current UV work")

        def cancel(_amount):
            raise cancelled

        with self.assertRaises(RuntimeError) as rejected:
            texture_coordinates(direct_geometry(), direct_mesh(((0, 0, 0),) * 3), charge=cancel)
        self.assertIs(rejected.exception, cancelled)

    def test_direct_admitted_callback_surface_errors_keep_identity_during_png_and_mapping(self):
        import ontokin.texture_runtime as runtime
        for phase, function_name in (("png", "validate_png"), ("mapping", "_make_mapping")):
            with self.subTest(phase=phase):
                source = load_texture_file_manifest(FIXTURES / "rgb-panel.files.json")
                failure = SurfaceError("OKL-E-PNG", "caller interruption using a semantic exception class")
                active = False

                def caller_check():
                    if active:
                        raise failure

                ordinary = getattr(runtime, function_name)

                def marked_phase(*args, **kwargs):
                    nonlocal active
                    active = True
                    try:
                        return ordinary(*args, **kwargs)
                    finally:
                        active = False

                ledger = SharedExecutionBudget(check=caller_check)
                admit_entry_budget(source.entry, ledger, profile=TEXTURE_PROFILE)
                with patch("ontokin.texture_runtime." + function_name, side_effect=marked_phase):
                    with self.assertRaises(SurfaceError) as rejected:
                        compile_construction(source, execution_budget=ledger)
                self.assertIs(rejected.exception, failure)
                self.assertIs(ledger.callback_error, failure)


if __name__ == "__main__":
    unittest.main()
