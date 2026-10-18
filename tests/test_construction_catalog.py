"""Exercise discovery through real linked sources and executable examples.

Discovery is a source interface, so these checks use exact pinned bundles,
independent source-byte slices, alias changes, and actual construction. They
do not replace the linker or compiler with fabricated catalog records.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import unittest

from ontokin.agent_catalog import catalog as core_catalog
from ontokin.bundle import load_bundle
from ontokin.construction import compile_construction
from ontokin.construction_catalog import catalog
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import evaluate
from ontokin.linker import link_program
from ontokin.validator import BUILTIN_CALLS, BUILTIN_TYPES, FIELD_TYPES


ROOT = Path(__file__).resolve().parents[1]
RACK = ROOT / "docs/language-design/construction-v0.1/01-keyed-rack"


def revision(source: str) -> str:
    return "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()


def bundle(entry: str, *modules: tuple[str, str]):
    return load_bundle({
        "schema_version": "ontokin.bundle/0.1",
        "entry": {"filename": "main.ok", "source": entry},
        "modules": [{"package_id": package, "version": "1.0.0",
                     "filename": "library.ok", "source": source}
                    for package, source in modules],
    })


def import_line(alias: str, package: str, source: str) -> str:
    return (f'import {alias} @ "{alias}" from "{package}" version "1.0.0" '
            f'digest "{revision(source)}";\n')


HEADER = 'ontokin "0.2"; module CatalogCheck @ "catalog-check"; profile "construction-0.1";\n'
SCENE = '''scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
}
'''


def rack_bundle():
    return load_bundle(json.loads((RACK / "program.bundle.json").read_text(encoding="utf-8")))


def declarations(data):
    return [item for item in data["items"] if "source_id" in item]


class ConstructionCatalogTests(unittest.TestCase):
    def test_global_metadata_preserves_core_and_covers_executable_names(self):
        previous = core_catalog()
        data = catalog()
        self.assertEqual(core_catalog(), previous)
        self.assertEqual({item["name"] for item in data["items"] if item["kind"] == "type"},
                         BUILTIN_TYPES | {"Keyed"})
        self.assertEqual({item["name"] for item in data["items"] if item["kind"] == "builtin"},
                         BUILTIN_CALLS | {"len"})
        members = {item["name"] for item in data["items"] if item["kind"] == "member"}
        self.assertLessEqual({"Object." + name for name in FIELD_TYPES}, members)
        identities = [item["id"] for item in data["items"]]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(data["language_version"], "0.2")
        self.assertEqual(data["profile"], "construction-0.1")
        self.assertEqual(data["agent_contract"], "ontokin.agent/0.2")
        self.assertEqual(data["delivery_targets"], ["ontokin.glb/0.2"])
        self.assertIsNone(data["program_context"])
        self.assertFalse(data["full_product_conformance_certified"])
        unsupported = set(data["unavailable_capabilities"])
        self.assertNotIn("modules_packages_and_procedural_generators", unsupported)
        self.assertLessEqual({"general_procedural_algorithms", "network_package_resolution",
                              "nested_keyed_values", "contact_and_collision_response"}, unsupported)
        json.dumps(data, ensure_ascii=False, allow_nan=False)

    def test_catalog_revisions_identify_content_and_returns_are_detached(self):
        linked = link_program(rack_bundle())
        for context in (None, linked):
            with self.subTest(linked=context is not None):
                original = catalog(linked_program=context)
                content = {key: value for key, value in original.items() if key != "revision"}
                encoded = json.dumps(content, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode("utf-8")
                self.assertEqual(original["revision"], "sha256:" + hashlib.sha256(encoded).hexdigest())
                changed = catalog(linked_program=context)
                changed["items"][0]["domains"].append("a reader's local annotation")
                changed["units"]["base"].clear()
                if context is not None:
                    changed["program_context"]["source_manifest"]["units"].clear()
                    declarations(changed)[0]["element_id"].clear()
                self.assertEqual(catalog(linked_program=context), original)

    def test_linked_rack_exposes_public_declarations_at_exact_original_spans(self):
        linked = link_program(rack_bundle())
        data = catalog(linked_program=linked)
        items = declarations(data)
        by_name = {item["name"]: item for item in items}
        self.assertLessEqual({"Rack", "Finger", "three_mounts", "Rack.fingers",
                             "Finger.bend_to", "Finger.flex"}, set(by_name))
        self.assertNotIn("Blade", by_name)
        self.assertNotIn("Finger.blade", by_name)
        self.assertNotIn("Blade.length", by_name)
        with self.assertRaises(OntoKinError) as private:
            linked.resolve_definition("entry", ("mech", "Blade"), kind="class")
        self.assertEqual(private.exception.diagnostic.code, "OKL-E-ACCESS")
        self.assertEqual(by_name["Hinges"]["import_paths"], [{"from_source_id": "entry", "alias": "mech"}])
        self.assertEqual(by_name["Finger"]["nominal_id"],
                         ["package", "example.hinges", "hinges", "definitions", "finger"])
        self.assertEqual(by_name["Rack.fingers"]["part_definition_id"], by_name["Finger"]["nominal_id"])
        self.assertEqual(by_name["Rack.fingers"]["value_type"], "Keyed<Ref<mech.Finger>>")
        self.assertEqual(by_name["Finger.bend_to"]["signature"],
                         "Finger.bend_to(angle: Angle, duration: Time) -> Action")
        self.assertEqual(by_name["three_mounts"]["result_type"], "Keyed<Vec3<Length>>")
        self.assertEqual(by_name["Rack.mounts"]["default_expression"]["text"], "mech.three_mounts(0.6[m])")
        for item in items:
            with self.subTest(declaration=item["name"]):
                unit = linked.modules[item["source_id"]].unit
                span = item["source_span"]
                exact = unit.raw[span["start_byte"]:span["end_byte"]].decode("utf-8")
                self.assertTrue(exact)
                self.assertEqual(span["file"], unit.filename)
                self.assertEqual(item["source_revision"], unit.revision)
                self.assertEqual(item["program_revision"], linked.program_revision)
                self.assertTrue(item["validation_required"])
                self.assertEqual(item["available_levels"], [])
                self.assertEqual(item["availability"], "linked_declaration_requires_validation")
                if "default_expression" in item:
                    default = item["default_expression"]
                    default_span = default["source_span"]
                    raw = unit.raw[default_span["start_byte"]:default_span["end_byte"]]
                    self.assertFalse(default["truncated"])
                    self.assertEqual(default["source_bytes"], len(raw))
                    self.assertEqual(default["text"].encode("utf-8"), raw)

    def test_alias_changes_preserve_imported_nominal_identity_and_source_provenance(self):
        original = rack_bundle()
        changed = original.to_payload()
        changed["entry"]["source"] = changed["entry"]["source"].replace("mech", "component")
        new_program = load_bundle(changed)
        old = catalog(linked_program=link_program(original))
        new = catalog(linked_program=link_program(new_program))
        self.assertNotEqual(old["revision"], new["revision"])
        self.assertNotEqual(original.program_revision, new_program.program_revision)
        old_items = {item["name"]: item for item in declarations(old)}
        new_items = {item["name"]: item for item in declarations(new)}
        for field in ("id", "element_id", "nominal_id", "source_id", "source_revision", "source_span"):
            self.assertEqual(old_items["Finger"][field], new_items["Finger"][field])
        self.assertEqual(new_items["Hinges"]["import_paths"], [{"from_source_id": "entry", "alias": "component"}])
        self.assertEqual(new_items["Rack.fingers"]["part_class_name"], "component.Finger")

    def test_unrelated_packages_may_share_module_names_keys_and_filenames(self):
        library = '''ontokin "0.2"; module Shared @ "shared"; profile "construction-0.1";
public class Finger @ "finger" { geometry = sphere(0.1[m]); }
'''
        entry = (HEADER + import_line("left", "example.left", library)
                 + import_line("right", "example.right", library) + SCENE)
        linked = link_program(bundle(entry, ("example.left", library), ("example.right", library)))
        fingers = [item for item in declarations(catalog(linked_program=linked)) if item["name"] == "Finger"]
        self.assertEqual(len(fingers), 2)
        self.assertEqual({item["source_span"]["file"] for item in fingers}, {"library.ok"})
        self.assertEqual(len({tuple(item["nominal_id"]) for item in fingers}), 2)
        self.assertEqual(len({item["id"] for item in fingers}), 2)
        for alias in ("left", "right"):
            target = linked.resolve_definition("entry", (alias, "Finger"), kind="class")
            self.assertIn(list(target.element_id), [item["nominal_id"] for item in fingers])

    def test_utf8_source_previews_are_bounded_without_fabricated_characters(self):
        literal = json.dumps("星" * 500, ensure_ascii=False)
        library = ('// é 星\nontokin "0.2"; module TextLibrary @ "text-library"; '
                   'profile "construction-0.1";\npublic class Label @ "label" {\n'
                   f'public param text @ "text": String = {literal};\n}}\n')
        linked = link_program(bundle(HEADER + import_line("labels", "example.labels", library) + SCENE,
                                     ("example.labels", library)))
        item, = [item for item in declarations(catalog(linked_program=linked)) if item["name"] == "Label.text"]
        preview = item["default_expression"]
        span = preview["source_span"]
        self.assertEqual(library.encode("utf-8")[span["start_byte"]:span["end_byte"]], literal.encode("utf-8"))
        self.assertTrue(preview["truncated"])
        self.assertLessEqual(len(preview["text"].encode("utf-8")), 1024)
        self.assertTrue(literal.startswith(preview["text"]))
        self.assertNotIn("\ufffd", preview["text"])
        self.assertEqual(preview["source_bytes"], len(literal.encode("utf-8")))

    def test_closed_keyed_and_len_examples_construct_real_geometry(self):
        data = catalog()
        examples = {(item["kind"], item["name"]): item["examples"][0]
                    for item in data["items"] if item["examples"]}
        cases = (
            ("Keyed", "Keyed<Length>", examples["type", "Keyed"], 'self.value["right"]', .3),
            ("len", "Int", examples["builtin", "len"], "real(self.value) * 0.1[m]", .2),
            ("index", "Length", examples["member", "Keyed.index"], "self.value", .2),
        )
        for name, type_name, expression, radius, expected in cases:
            with self.subTest(example=name):
                source = HEADER + f'''public class Probe @ "probe" {{
    public param value @ "value": {type_name} = {expression};
    geometry = sphere({radius});
}}
scene Demo @ "demo" {{
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object probe @ "probe": Probe {{}}
}}
'''
                compiler = compile_construction(bundle(source), level="evaluated")
                output = evaluate(compiler.model, [0, 1])
                self.assertEqual(output["outcome"], "valid")
                self.assertEqual(compiler.model.profile, "construction-0.1")
                self.assertAlmostEqual(compiler.model.objects["probe"].geometry["radius"], expected)

    def test_complete_import_parts_override_and_action_example_evaluates(self):
        self.assertIn(str((RACK / "program.bundle.json").relative_to(ROOT)), catalog()["complete_examples"])
        compiler = compile_construction(rack_bundle(), level="evaluated")
        self.assertEqual(len(compiler.model.objects), 18)
        self.assertEqual(len(compiler.model.follows), 8)
        self.assertEqual(len(compiler.model.joints), 8)
        selected = 'first.fingers["middle"].blade'
        self.assertEqual(compiler.model.objects[selected].geometry["size"], (.75, .08, .08))
        self.assertEqual(compiler.model.objects['second.fingers["middle"].blade'].geometry["size"], (.6, .08, .08))
        result = evaluate(compiler.model, [.5, 1, 2])
        self.assertEqual(result["outcome"], "valid")
        for sample, t in zip(result["samples"], (.5, 1, 2)):
            theta = math.pi / 4 * min(t, 1)
            expected = (-1 + .375 * math.cos(theta), .2 * t + .375 * math.sin(theta), 0)
            for actual, coordinate in zip(sample["objects"][selected]["position_m"], expected):
                self.assertAlmostEqual(actual, coordinate, places=9)
            self.assertEqual(sample["objects"]['second.fingers["middle"].blade']["position_m"], [1.3, 0, 0])

    def test_cancellation_and_materialization_limits_do_not_return_partial_success(self):
        class Cancelled(Exception):
            pass

        calls = 0

        def cancel():
            nonlocal calls
            calls += 1
            if calls == 50:
                raise Cancelled("request cancelled")

        before = catalog()
        with self.assertRaises(Cancelled):
            catalog(linked_program=link_program(rack_bundle()), check=cancel)
        self.assertEqual(calls, 50)
        self.assertEqual(catalog(), before)
        # This is a valid, bounded source module. Its expanded public interface
        # exceeds the separate discovery materialization budget.
        library = ('ontokin "0.2"; module Many @ "many"; profile "construction-0.1";\n'
                   + "\n".join(f'public fn value{i} @ "v{i}"() -> Int {{ return {i}; }}'
                               for i in range(2000)))
        linked = link_program(bundle(HEADER + import_line("many", "example.many", library) + SCENE,
                                     ("example.many", library)))
        with self.assertRaises(OntoKinError) as limited:
            catalog(linked_program=linked)
        self.assertEqual(limited.exception.diagnostic.code, "OKL-E-RESOURCE")
        self.assertEqual(limited.exception.diagnostic.phase, "inspection")
        self.assertEqual(catalog(), before)


if __name__ == "__main__":
    unittest.main()
