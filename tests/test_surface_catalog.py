"""Native discovery from real source declarations and executable examples.

These checks protect the published 0.2 catalog identity, the frozen surface
limits and source-module profile boundaries. They do not certify a release.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from ontokin.agent_catalog import catalog as core_catalog
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.construction import compile_construction
from ontokin.construction_catalog import catalog
from ontokin.diagnostics import OntoKinError
from ontokin.linker import link_program
from ontokin.surface_runtime import SURFACE_CALLS, SURFACE_TYPES
from tests.test_construction_catalog import declarations, rack_bundle
from tests.test_surface_source import bundle as studio_bundle


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/language-design/surface-v0.1"
PROFILE = "surface-0.1"
OLD_CATALOG_REVISION = "sha256:7c997692ee8d2516bc897ad898f34d101affb97ccb4a7eb95921bcd3b5f9f490"


def mixed_bundle(alias="legacy"):
    original = studio_bundle()
    source = b'''ontokin "0.2";
module Legacy @ "legacy";
profile "construction-0.1";
public fn marker_radius @ "marker-radius"() -> Length { return 0.1[m]; }
public class Marker @ "marker" {
    public param radius @ "radius": Length = marker_radius();
    geometry = sphere(self.radius);
}
'''
    dependency = SourceUnit("package:fixture.legacy@1.0.0", "legacy.ok", source,
                            "fixture.legacy", "1.0.0")
    text = original.entry.raw.decode("utf-8").replace(
        'profile "surface-0.1";', 'profile "surface-0.1";\n' +
        f'import {alias} @ "legacy-import" from "fixture.legacy" version "1.0.0" digest "{dependency.revision}";')
    text = text.replace('scene Studio @ "studio" {',
                        f'scene Studio @ "studio" {{\n    object marker @ "marker": {alias}.Marker {{}}')
    return ProgramBundle(SourceUnit("entry", original.entry.filename, text.encode("utf-8")),
                         (*original.modules, dependency))


class SurfaceCatalogTests(unittest.TestCase):
    def test_explicit_surface_selection_preserves_older_default_catalog_identity(self):
        old = catalog()
        core = core_catalog()
        self.assertEqual(old["revision"], OLD_CATALOG_REVISION)
        self.assertEqual(catalog(profile="construction-0.1"), old)
        data = catalog(profile=PROFILE)
        self.assertEqual(data["schema_version"], "ontokin.agent-catalog/0.3")
        self.assertEqual(data["language_version"], "0.3")
        self.assertEqual(data["profile"], PROFILE)
        self.assertEqual(data["agent_contract"], "ontokin.agent/0.3")
        self.assertEqual(data["delivery_targets"], ["ontokin.glb/0.3"])
        self.assertFalse(data["full_product_conformance_certified"])
        self.assertEqual(catalog(), old)
        self.assertEqual(core_catalog(), core)
        for kind, additions in (("type", SURFACE_TYPES), ("builtin", SURFACE_CALLS)):
            old_names = {item["name"] for item in old["items"] if item["kind"] == kind}
            new_names = {item["name"] for item in data["items"] if item["kind"] == kind}
            self.assertEqual(new_names, old_names | additions)
        keyed = next(item for item in data["items"] if item["name"] == "Keyed")
        old_keyed = next(item for item in old["items"] if item["name"] == "Keyed")
        self.assertEqual(keyed["element_types"], old_keyed["element_types"] + ["LoftSection", "SurfaceMaterial"])
        self.assertEqual(len({item["id"] for item in data["items"]}), len(data["items"]))
        self.assertTrue(all(item["profile"] == PROFILE for item in data["items"]))

    def test_catalog_limits_and_example_pins_match_the_untouched_acceptance_manifest(self):
        frozen = json.loads((FIXTURES / "acceptance.json").read_text())
        data = catalog(profile=PROFILE)
        mapping = {
            "min_surface_sections": "min_sections", "max_surface_sections": "max_sections",
            "min_surface_palette_keys": "min_materials", "max_surface_palette_keys": "max_materials",
            "min_surface_facets": "min_facets", "max_surface_facets": "max_facets",
            "surface_facets_multiple": "facets_multiple", "min_surface_radius_m": "min_radius_m",
            "max_surface_radius_m": "max_radius_m", "min_surface_station_separation_m": "min_station_gap_m",
            "max_surface_coordinate_abs_m": "max_coordinate_abs_m",
            "max_aggregate_mesh_vertices": "max_aggregate_vertices", "max_glb_bytes": "max_glb_bytes",
        }
        for catalog_name, frozen_name in mapping.items():
            self.assertEqual(data["limits"][catalog_name], frozen["limits"][frozen_name])
        self.assertEqual(data["limits"]["max_surface_triangles_per_loft"], 2 * 64 * 64)
        self.assertEqual(data["limits"]["max_surface_vertices_per_loft"], 6 * 64 * 64)
        self.assertEqual(data["limits"]["max_surface_page_triangles"], 256)
        self.assertEqual(data["limits"]["max_surface_page_vertices"], 768)
        example = data["example_bundles"][0]
        dependency = example["dependencies"][0]
        self.assertEqual(Path(example["entry"]).name, frozen["source_bundle"]["entry"])
        self.assertEqual(Path(dependency["path"]).name, frozen["source_bundle"]["library"])
        self.assertEqual(dependency["source_revision"], "sha256:" + frozen["source_bundle"]["sha256"])
        self.assertEqual(hashlib.sha256((ROOT / dependency["path"]).read_bytes()).hexdigest(), frozen["source_bundle"]["sha256"])
        compiler = compile_construction(studio_bundle(), level="evaluated")
        self.assertEqual(compiler.model.profile, PROFILE)
        self.assertEqual(set(compiler.surface_meshes), {"first", "second"})
        for record in compiler.surface_meshes.values():
            self.assertEqual(record["mesh"].triangle_count, 2 * 3 * 16)

    def test_discovery_names_supported_pbr_and_keeps_appearance_and_physics_omissions_explicit(self):
        data = catalog(profile=PROFILE)
        by_name = {item["name"]: item for item in data["items"]}
        for name in ("native_loft_surfaces", "regional_pbr_materials", "rigid_visual_placement", "surface_mesh_inspection"):
            self.assertEqual(by_name[name]["availability"], "available_in_bounded_profile")
        omissions = set(data["unavailable_capabilities"])
        self.assertNotIn("textures_and_regional_materials", omissions)
        self.assertNotIn("regional_pbr_materials", omissions)
        self.assertLessEqual({"textures_and_uv_coordinates", "advanced_or_animated_materials",
                              "smooth_or_freeform_surfaces", "automatic_surface_physics",
                              "contact_and_collision_response", "skinning_and_deformation",
                              "live_destination_physics", "general_rigid_body_dynamics"}, omissions)
        self.assertIn("palette", " ".join(by_name["Object.appearance"]["domains"]))
        self.assertIn("sphere proxy", " ".join(by_name["Object.physical"]["domains"]))
        self.assertEqual({item["name"] for item in data["items"] if item["kind"] == "protocol"}, {"ontokin.agent/0.3"})
        protocol = by_name["ontokin.agent/0.3"]
        self.assertEqual(protocol["store_filename"], "surface-program-agent.sqlite3")
        self.assertEqual(protocol["store_schema"], "ontokin.surface-program-agent-store/0.1")
        self.assertEqual(protocol["diagnostic_contract"], "ontokin.diagnostic/0.2")
        page = by_name["surface.mesh_page"]
        self.assertEqual(page["count_unit"], "triangles")
        self.assertEqual(page["available_levels"], ["constructed"])
        self.assertEqual(page["coordinate_system"], "carrier_local_after_placement/0.1")
        self.assertEqual(page["ordering"], "native_triangle_ordinal/0.1")
        self.assertEqual(by_name["geometry.surface"]["summary_contract"], "ontokin.surface-summary/0.1")

    def test_mixed_module_declarations_keep_their_own_versions_profiles_and_original_source_spans(self):
        program = mixed_bundle()
        linked = link_program(program)
        data = catalog(linked_program=linked, profile=PROFILE)
        self.assertEqual(data["program_context"]["program_revision"], program.program_revision)
        for item in declarations(data):
            module = linked.modules[item["source_id"]]
            self.assertEqual(item["profile"], module.ast.profile)
            self.assertEqual(item["language_version"], module.ast.version)
            self.assertTrue(item["id"].startswith(module.ast.profile + "/declaration/"))
            self.assertEqual(item["source_revision"], module.unit.revision)
            span = item["source_span"]
            self.assertEqual(span["file"], module.unit.filename)
            self.assertTrue(module.unit.raw[span["start_byte"]:span["end_byte"]])
            self.assertEqual(item["available_levels"], [])
            self.assertTrue(item["validation_required"])
        by_name = {item["name"]: item for item in declarations(data)}
        for name in ("Legacy", "Marker", "Marker.radius", "marker_radius"):
            self.assertEqual(by_name[name]["profile"], "construction-0.1")
        for name in ("SurfaceStudio", "SurfaceParts", "Shell", "Shell.rings", "Shell.palette"):
            self.assertEqual(by_name[name]["profile"], PROFILE)
        compiler = compile_construction(program, level="evaluated")
        self.assertEqual(compiler.model.objects["marker"].geometry, {"kind": "sphere", "radius": .1})
        self.assertEqual(set(compiler.surface_meshes), {"first", "second"})

    def test_import_alias_edit_changes_catalog_context_without_relabeling_definition_identity(self):
        before = catalog(linked_program=link_program(mixed_bundle("legacy")), profile=PROFILE)
        after = catalog(linked_program=link_program(mixed_bundle("older")), profile=PROFILE)
        self.assertNotEqual(before["revision"], after["revision"])
        self.assertNotEqual(before["program_context"]["program_revision"], after["program_context"]["program_revision"])
        old_records = {item["name"]: item for item in declarations(before) if item["source_id"] != "entry"}
        new_records = {item["name"]: item for item in declarations(after) if item["source_id"] != "entry"}
        for name, record in old_records.items():
            for field in ("id", "element_id", "nominal_id", "profile", "language_version", "source_revision", "source_span"):
                self.assertEqual(record[field], new_records[name][field])
        self.assertEqual(new_records["Legacy"]["import_paths"], [{"from_source_id": "entry", "alias": "older"}])

    def test_native_catalog_returns_are_detached_and_revision_hashes_the_actual_content(self):
        for linked in (None, link_program(studio_bundle())):
            with self.subTest(linked=linked is not None):
                original = catalog(linked_program=linked, profile=PROFILE)
                content = {key: value for key, value in original.items() if key != "revision"}
                encoded = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
                self.assertEqual(original["revision"], "sha256:" + hashlib.sha256(encoded).hexdigest())
                changed = catalog(linked_program=linked, profile=PROFILE)
                changed["items"][0]["domains"].clear()
                changed["example_bundles"][0]["dependencies"].clear()
                if linked is not None:
                    declarations(changed)[0]["element_id"].clear()
                self.assertEqual(catalog(linked_program=linked, profile=PROFILE), original)
        self.assertEqual(catalog()["revision"], OLD_CATALOG_REVISION)

    def test_cancellation_propagates_and_unknown_or_mismatched_profiles_are_not_relabelled(self):
        class Cancelled(Exception):
            pass

        calls = 0
        def cancel():
            nonlocal calls
            calls += 1
            if calls == 50:
                raise Cancelled("cancel bounded catalog work")

        with self.assertRaises(Cancelled):
            catalog(linked_program=link_program(studio_bundle()), profile=PROFILE, check=cancel)
        self.assertEqual(calls, 50)
        for fields in ({"profile": "unknown-profile"},
                       {"profile": PROFILE, "linked_program": link_program(rack_bundle())}):
            with self.subTest(fields=fields.keys()), self.assertRaises(OntoKinError) as raised:
                catalog(**fields)
            self.assertEqual(raised.exception.diagnostic.code, "OKL-E-CAPABILITY-UNSUPPORTED")
        self.assertEqual(catalog()["revision"], OLD_CATALOG_REVISION)


if __name__ == "__main__":
    unittest.main()
