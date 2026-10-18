"""Independent module closure, nominal identity, and execution acceptance."""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import unittest

from ontokin.bundle import BundleError, load_bundle, load_file_manifest
from ontokin.diagnostics import OntoKinError
from ontokin.linker import link_program


ROOT = Path(__file__).resolve().parents[1] / "docs/language-design/construction-v0.1"
SCENE = 'scene Demo @ "demo" { duration=1[s]; gravity=vector(world,0[m/s^2],0[m/s^2],0[m/s^2]); }'
ZERO_PIN = "sha256:" + "0" * 64


def source(body="", *, name="Library", key="library", scene=False):
    return f'ontokin "0.2"; module {name} @ "{key}"; profile "construction-0.1";\n' + body + ("\n" + SCENE if scene else "")


def module(package, text, *, version="1.0.0", filename=None):
    return {"package_id": package, "version": version, "filename": filename or package + ".ok", "source": text}


def revision(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def imported(alias, package, text=None, *, version="1.0.0", digest=None, key=None):
    return f'import {alias} @ "{key or alias}" from "{package}" version "{version}" digest "{digest or revision(text)}";\n'


def bundle(entry, modules=()):
    return load_bundle({"schema_version": "ontokin.bundle/0.1", "entry": {"filename": "main.ok", "source": entry}, "modules": list(modules)})


def fixture(name):
    return load_file_manifest(ROOT / name / "program.files.json")


def chain(depth, *, direct_last=False):
    records = []
    next_source = None
    for number in range(depth, 0, -1):
        body = "" if next_source is None else imported("next", "p" + str(number + 1), next_source)
        current = source(body, name="Layer" + str(number), key="layer" + str(number))
        records.append(module("p" + str(number), current))
        next_source = current
    body = imported("first", "p1", next_source)
    if direct_last:
        body = imported("short", "p" + str(depth), records[0]["source"]) + body
    return bundle(source(body, name="Entry", key="entry", scene=True), records)


class LinkerTests(unittest.TestCase):
    def rejected(self, value, code, reason=None):
        with self.assertRaises(OntoKinError) as result:
            link_program(value)
        self.assertEqual(result.exception.code, code)
        if reason is not None:
            self.assertEqual(result.exception.diagnostic.details.get("reason"), reason)
        return result.exception.diagnostic

    def test_c01_reusable_library_has_original_namespace_and_private_boundary(self):
        value = fixture("01-keyed-rack")
        linked = link_program(value)
        self.assertEqual(len(linked.modules), 2)
        self.assertEqual(len(linked.definitions), 4)
        finger = linked.resolve_definition("entry", "mech.Finger", kind="class")
        self.assertEqual(finger.element_id, ("package", "example.hinges", "hinges", "definitions", "finger"))
        self.assertEqual(linked.resolve_definition(finger.source_id, "Blade").visibility, "private")
        with self.assertRaises(OntoKinError) as result:
            linked.resolve_definition("entry", "mech.Blade")
        self.assertEqual(result.exception.code, "OKL-E-ACCESS")
        self.assertEqual(result.exception.diagnostic.node.source_id, "entry")
        self.assertEqual(result.exception.diagnostic.related[0].source_id, finger.source_id)

    def test_c02_equal_lexical_names_and_module_keys_are_package_scoped(self):
        linked = link_program(fixture("02-namespaces"))
        left = linked.resolve_definition("entry", "left.Marker")
        right = linked.resolve_definition("entry", "right.Marker")
        self.assertEqual(left.name, right.name)
        self.assertEqual(left.key, right.key)
        self.assertNotEqual(left.element_id, right.element_id)
        self.assertEqual(linked.modules[left.source_id].ast.module_key,
                         linked.modules[right.source_id].ast.module_key)
        self.assertNotEqual(linked.resolve_definition(left.source_id, "sample").element_id,
                            linked.resolve_definition("entry", "sample").element_id)

    def test_c03_transitive_and_diamond_resolution_use_supplied_exact_units_once(self):
        value = fixture("03-transitive")
        linked = link_program(value)
        expected = json.loads((ROOT / "03-transitive/expected.json").read_text())
        self.assertEqual(list(linked.dependency_order), expected["dependency_order"])
        payload = value.to_payload()
        arithmetic = next(unit for unit in value.modules if unit.package_id == "example.arithmetic")
        payload["entry"]["source"] = payload["entry"]["source"].replace('import shapes',
            imported("arithmetic", arithmetic.package_id, arithmetic.text) + 'import shapes', 1)
        diamond = link_program(load_bundle(payload))
        self.assertEqual(set(diamond.definitions), set(linked.definitions))
        self.assertEqual(len(diamond.source_registry), 3)
        self.assertEqual(diamond.dependency_order.count(arithmetic.source_id), 1)

    def test_alias_rename_and_two_aliases_do_not_create_nominal_types(self):
        value = fixture("02-namespaces")
        old = link_program(value)
        changed = value.to_payload()
        changed["entry"]["source"] = changed["entry"]["source"].replace('import left @', 'import renamed @').replace('left.', 'renamed.')
        renamed = link_program(load_bundle(changed))
        self.assertEqual(old.resolve_definition("entry", "left.Marker").element_id,
                         renamed.resolve_definition("entry", "renamed.Marker").element_id)
        left = next(unit for unit in value.modules if unit.package_id == "example.left")
        changed["entry"]["source"] = changed["entry"]["source"].replace('import renamed',
            imported("also", left.package_id, left.text) + 'import renamed', 1)
        twice = link_program(load_bundle(changed))
        self.assertIs(twice.resolve_definition("entry", "also.Marker"),
                      twice.resolve_definition("entry", "renamed.Marker"))

    def test_c10_missing_wrong_changed_and_extra_content_rejects_with_candidate_identity(self):
        value = fixture("01-keyed-rack")
        missing = value.to_payload()
        missing["modules"] = []
        missing_bundle = load_bundle(missing)
        self.assertNotEqual(missing_bundle.program_revision, value.program_revision)
        self.rejected(missing_bundle, "OKL-E-NAME", "missing_dependency")
        wrong = value.to_payload()
        wrong["entry"]["source"] = wrong["entry"]["source"].replace(value.modules[0].revision, ZERO_PIN)
        diagnostic = self.rejected(load_bundle(wrong), "OKL-E-REVISION", "pin_mismatch")
        self.assertEqual(diagnostic.node.source_id, "entry")
        self.assertEqual(diagnostic.related[0].source_id, value.modules[0].source_id)
        changed = value.to_payload()
        changed["modules"][0]["source"] += "\n// content changed under the same filename\n"
        candidate = load_bundle(changed)
        self.assertEqual(candidate.entry.revision, value.entry.revision)
        self.assertNotEqual(candidate.program_revision, value.program_revision)
        self.rejected(candidate, "OKL-E-REVISION", "pin_mismatch")
        extra = value.to_payload()
        extra["modules"].append(module("example.extra", source()))
        self.rejected(load_bundle(extra), "OKL-E-NAME", "unreachable_dependency")

    def test_import_pin_literal_domains_are_source_diagnostics(self):
        library = source()
        valid = source(imported("lib", "example.library", library), scene=True)
        for old, new, code in [('"example.library"', '"Invalid.Package"', "OKL-E-NAME"),
                               ('"1.0.0"', '"latest"', "OKL-E-REVISION"),
                               (revision(library), 'sha256:ABC', "OKL-E-REVISION")]:
            with self.subTest(value=new):
                diagnostic = self.rejected(bundle(valid.replace(old, new), [module("example.library", library)]), code)
                self.assertEqual(diagnostic.node.source_id, "entry")
                raw = valid.replace(old, new).encode("utf-8")
                self.assertIn(new.strip('"'), raw[diagnostic.node.start:diagnostic.node.end].decode("utf-8"))

    def test_c11_cycles_are_detected_before_impossible_digest_fixed_points(self):
        a = source(imported("b", "example.b", digest=ZERO_PIN), name="A", key="a")
        b = source(imported("a", "example.a", digest=ZERO_PIN), name="B", key="b")
        entry = source(imported("a", "example.a", a), scene=True)
        diagnostic = self.rejected(bundle(entry, [module("example.a", a), module("example.b", b)]),
                                   "OKL-E-DEPENDENCY-CYCLE", "import_cycle")
        self.assertEqual(diagnostic.details["cycle"], ["package:example.a@1.0.0", "package:example.b@1.0.0", "package:example.a@1.0.0"])
        self.assertEqual(diagnostic.node.source_id, "package:example.b@1.0.0")
        self.assertEqual(diagnostic.related[0].source_id, "package:example.a@1.0.0")

    def test_conflicting_versions_are_revision_bound_semantic_rejection(self):
        a = source(name="A", key="a")
        b = source(name="B", key="b")
        entry = source(imported("a", "example.a", a) + imported("b", "example.a", b, version="2.0.0"), scene=True)
        value = bundle(entry, [module("example.a", a), module("example.a", b, version="2.0.0")])
        self.assertEqual(len(value.source_registry), 3)
        self.rejected(value, "OKL-E-REVISION", "conflicting_package_versions")

    def test_imported_scene_missing_entry_scene_and_unsupported_profiles(self):
        executable = source(scene=True)
        self.rejected(bundle(source(imported("lib", "example.library", executable), scene=True),
                             [module("example.library", executable)]), "OKL-E-TYPE")
        self.rejected(bundle(source()), "OKL-E-SYNTAX")
        for library in [source().replace('"0.2"', '"0.1"'), source().replace('"construction-0.1"', '"core-0.1"')]:
            diagnostic = self.rejected(bundle(source(imported("lib", "example.library", library), scene=True),
                                              [module("example.library", library)]), "OKL-E-CAPABILITY-UNSUPPORTED")
            self.assertEqual(diagnostic.node.source_id, "package:example.library@1.0.0")

    def test_module_lookup_scope_disallows_collisions_unqualified_imports_and_reexports(self):
        library = source('class C @ "c" {}')
        for body, code in [(imported("lib", "example.library", library) + 'class lib @ "type" {}', "OKL-E-NAME"),
                           (imported("len", "example.library", library), "OKL-E-NAME"),
                           (imported("lib", "example.library", library) + 'class C @ "lib" {}', "OKL-E-ID")]:
            with self.subTest(body=body):
                self.rejected(bundle(source(body, scene=True), [module("example.library", library)]), code)
        linked = link_program(bundle(source(imported("lib", "example.library", library), scene=True),
                                     [module("example.library", library)]))
        for name in ["C", "lib.other.C", "missing.C"]:
            with self.subTest(name=name), self.assertRaises(OntoKinError) as rejected:
                linked.resolve_definition("entry", name)
            self.assertEqual(rejected.exception.code, "OKL-E-NAME")
        with self.assertRaises(OntoKinError) as wrong_kind:
            linked.resolve_definition("entry", "lib.C", kind="function")
        self.assertEqual(wrong_kind.exception.code, "OKL-E-TYPE")

    def test_module_and_longest_import_depth_boundaries(self):
        self.assertEqual(len(link_program(chain(8, direct_last=True)).modules), 9)
        diagnostic = self.rejected(chain(9, direct_last=True), "OKL-E-RESOURCE")
        self.assertEqual(diagnostic.details["consumed"], 9)
        libraries = [module("p" + str(i), source(name="L" + str(i), key="same")) for i in range(16)]
        entry = source(''.join(imported("a" + str(i), item["package_id"], item["source"]) for i, item in enumerate(libraries)), scene=True)
        self.assertEqual(len(link_program(bundle(entry, libraries)).modules), 17)

    def test_total_token_budget_is_not_reset_for_each_dependency(self):
        # Each dependency is below 200k tokens and the total source is below2MB.
        # The closed graph nevertheless exceeds the request-wide token limit.
        locals_ = ''.join(f'let value{i}:Int=1;' for i in range(14300))
        library = source('fn work @ "work"()->Int {' + locals_ + 'return 1;}')
        records = [module("example.a", library), module("example.b", library)]
        entry = source(imported("a", "example.a", library) + imported("b", "example.b", library), scene=True)
        diagnostic = self.rejected(bundle(entry, records), "OKL-E-RESOURCE")
        self.assertGreater(diagnostic.details["consumed"], 200000)
        self.assertEqual(diagnostic.node.source_id, "package:example.b@1.0.0")

    def test_whole_closure_requires_and_caller_cancellation_are_preserved(self):
        library = source('requires "contacts";')
        value = bundle(source(imported("lib", "example.library", library), scene=True), [module("example.library", library)])
        linked = link_program(value)
        self.assertEqual([(item.value, item.source_id) for item in linked.capabilities],
                         [("contacts", "package:example.library@1.0.0")])
        marker = RuntimeError("cancel linking")
        def stop():
            raise marker
        with self.assertRaises(RuntimeError) as rejected:
            link_program(value, check=stop)
        self.assertIs(rejected.exception, marker)

    def test_c19_supplied_snapshot_hash_precedes_any_link_error(self):
        initial = fixture("03-transitive")
        data = initial.to_payload()
        data["modules"] = list(reversed(data["modules"]))
        self.assertEqual(load_bundle(data).program_revision, initial.program_revision)
        data["modules"][0]["source"] += '\nclass Broken @ "broken" {'
        candidate = load_bundle(data)
        self.assertEqual(load_bundle(candidate.to_payload()).program_revision, candidate.program_revision)
        self.assertNotEqual(candidate.program_revision, initial.program_revision)
        diagnostic = self.rejected(candidate, "OKL-E-SYNTAX")
        self.assertEqual(diagnostic.node.source_id, "package:example.geometry@1.0.0")

    def test_manifest_seals_concrete_cases_and_expected_failure_origins(self):
        from ontokin.construction import compile_construction
        manifest = json.loads((ROOT / "module-cases.json").read_text())
        self.assertEqual([case["case_id"] for case in manifest["cases"]],
                         ["C01", "C02", "C03", "C10", "C11", "C19"])
        for case in manifest["cases"]:
            for name in case["tests"]:
                module_name, class_name, method_name = name.split(".")
                self.assertTrue(callable(getattr(getattr(importlib.import_module(module_name), class_name), method_name)))
            for scenario in case["scenarios"]:
                with self.subTest(case=case["case_id"], scenario=scenario["id"]):
                    expected = scenario["expected"]
                    path = ROOT / scenario["source"]
                    if expected["outcome"] == "transport_error":
                        with self.assertRaises(BundleError) as rejected:
                            load_file_manifest(path)
                        self.assertEqual(rejected.exception.code, expected["code"])
                        self.assertFalse(hasattr(rejected.exception, "diagnostic"))
                        continue
                    value = (load_file_manifest(path) if scenario["loader"] == "files"
                             else load_bundle(json.loads(path.read_text())))
                    self.assertEqual(value.program_revision, expected["program_revision"])
                    self.assertEqual({unit.source_id: unit.revision for unit in value.units}, expected["source_revisions"])
                    if expected["outcome"] == "valid":
                        compile_construction(value, level=scenario["level"])
                        if "fixture_expectations" in expected:
                            oracle = json.loads((ROOT / expected["fixture_expectations"]).read_text())
                            self.assertEqual(oracle["program_revision"], value.program_revision)
                    else:
                        diagnostic = self.rejected(value, expected["code"], expected.get("reason"))
                        self.assertEqual(getattr(diagnostic.node, "source_id", None), expected["primary_source_id"])


class ModuleExecutionTests(unittest.TestCase):
    def compile(self, value, level="constructed"):
        from ontokin.construction import compile_construction
        return compile_construction(value, level=level)

    def test_c01_actual_reused_component_instances_are_independent(self):
        compiled = self.compile(fixture("01-keyed-rack"))
        self.assertEqual(len(compiled.model.objects), 18)
        self.assertEqual((len(compiled.model.joints), len(compiled.model.follows)), (8, 8))
        objects = compiled.model.objects
        self.assertEqual(objects['first.fingers["middle"]'].class_name, objects['second.fingers["middle"]'].class_name)
        self.assertEqual(objects['first.fingers["middle"].blade'].geometry["size"][0], 0.75)
        self.assertEqual(objects['second.fingers["middle"].blade'].geometry["size"][0], 0.6)

    def test_c02_c03_execute_declaring_module_helpers_and_nominal_references(self):
        for folder in ["02-namespaces", "03-transitive"]:
            value = fixture(folder)
            expected = json.loads((ROOT / folder / "expected.json").read_text())
            compiled = self.compile(value)
            with self.subTest(folder=folder):
                self.assertEqual(len(compiled.model.objects), expected["object_count"])
                self.assertEqual(compiled.model.profile, "construction-0.1")
                for path, item in expected["objects"].items():
                    obj = compiled.model.objects[path]
                    self.assertEqual(obj.element_id, tuple(item["element_id"]))
                    self.assertEqual(compiled.definition_id(obj.class_name), tuple(item["definition_id"]))
                    self.assertAlmostEqual(obj.geometry["radius"], item["radius_m"], delta=1e-9)
                    self.assertEqual(obj.owner, item["owner"])

    def test_alias_change_preserves_constructed_types_and_strict_nominal_argument_check(self):
        value = fixture("02-namespaces")
        initial = self.compile(value)
        data = value.to_payload()
        data["entry"]["source"] = data["entry"]["source"].replace('import left @', 'import renamed @').replace('left.', 'renamed.')
        renamed = self.compile(load_bundle(data))
        self.assertEqual([(o.path, o.class_name, o.geometry) for o in initial.model.objects.values()],
                         [(o.path, o.class_name, o.geometry) for o in renamed.model.objects.values()])
        data = value.to_payload()
        data["entry"]["source"] = data["entry"]["source"].replace('base = left_value(a);', 'base = left_value(b);')
        with self.assertRaises(OntoKinError) as rejected:
            self.compile(load_bundle(data))
        self.assertEqual(rejected.exception.code, "OKL-E-TYPE")

    def test_unused_imported_function_body_and_capability_requirements_are_not_ignored(self):
        invalid = source('fn invalid @ "invalid"()->Length { return 1[s]; }')
        value = bundle(source(imported("lib", "example.library", invalid), scene=True), [module("example.library", invalid)])
        with self.assertRaises(OntoKinError) as rejected:
            self.compile(value)
        self.assertEqual(rejected.exception.code, "OKL-E-UNIT")
        self.assertEqual(rejected.exception.diagnostic.node.source_id, "package:example.library@1.0.0")
        unsupported = source('requires "contacts";')
        value = bundle(source(imported("lib", "example.library", unsupported), scene=True), [module("example.library", unsupported)])
        self.compile(value, level="represented")
        with self.assertRaises(OntoKinError) as rejected:
            self.compile(value, level="constructed")
        self.assertEqual(rejected.exception.code, "OKL-E-CAPABILITY-UNSUPPORTED")
        self.assertEqual(rejected.exception.diagnostic.node.source_id, "package:example.library@1.0.0")


if __name__ == "__main__":
    unittest.main()
