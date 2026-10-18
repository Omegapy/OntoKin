"""Independent CON-011/013 source-origin, scope and nominal edit checks."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from ontokin.bundle import load_bundle
from ontokin.diagnostics import Diagnostic, OntoKinError, Source
from ontokin.program_agent import ProgramAgentService
from ontokin.program_diagnostics import diagnostic_dict
from ontokin.program_runtime import apply_patches, inspect_revision, validate_revision


ROOT = Path(__file__).resolve().parents[1] / "docs/language-design/construction-v0.1"


def payload(folder):
    return json.loads((ROOT / folder / "program.bundle.json").read_text())


def digest(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def change_library(data, package, transform):
    unit = next(unit for unit in data["modules"] if unit["package_id"] == package)
    previous = digest(unit["source"])
    unit["source"] = transform(unit["source"])
    current = digest(unit["source"])
    for importer in [data["entry"], *data["modules"]]:
        importer["source"] = importer["source"].replace(previous, current)


def source_patch(program, source_id, before, after, element_id):
    source = program.sources[source_id]
    start = source.raw.index(before.encode("utf-8"))
    return {"source_id": source_id, "source_revision": source.revision,
            "element_id": element_id, "start_byte": start,
            "end_byte": start + len(before.encode("utf-8")),
            "expected_text": before, "replacement": after}


class SourceProjectionReviewTests(unittest.TestCase):
    def item(self, program, path):
        response = inspect_revision(program, selector={"path": path}, fields=["identity", "source", "values"], limit=1)
        self.assertEqual(response["outcome"], "valid", response)
        self.assertEqual(response["total"], 1)
        return response["items"][0]

    def test_equal_filenames_offsets_and_text_do_not_grant_cross_unit_write_scope(self):
        data = payload("02-namespaces")
        for unit in data["modules"]:
            unit["filename"] = "shared.ok"
        program = load_bundle(data)
        left_id, right_id = "package:example.left@1.0.0", "package:example.right@1.0.0"
        left, right = program.sources[left_id], program.sources[right_id]
        self.assertEqual(left.raw.index(b"0.1[m]"), right.raw.index(b"0.1[m]"))
        wrong = source_patch(program, right_id, "0.1[m]", "0.15[m]",
                             ["package", "example.left", "components", "definitions", "marker", "base"])
        with self.assertRaises(OntoKinError) as rejected:
            apply_patches(program, [wrong])
        self.assertEqual(rejected.exception.code, "OKL-E-REVISION")
        diagnostic = diagnostic_dict(rejected.exception.diagnostic, program)
        self.assertEqual(diagnostic["primary"]["source_id"], right_id)
        self.assertEqual(diagnostic["primary"]["source_revision"], right.revision)
        self.assertEqual(diagnostic["primary"]["file"], "shared.ok")

        correct = copy.deepcopy(wrong)
        correct["element_id"][1] = "example.right"
        changed_text = right.text.replace("0.1[m]", "0.15[m]")
        pin = source_patch(program, "entry", right.revision, digest(changed_text),
                           ["entry", "namespaces", "imports", "right-import"])
        candidate = apply_patches(program, [correct, pin])
        self.assertEqual(validate_revision(candidate, level="constructed")["outcome"], "valid")
        self.assertEqual(candidate.sources[right_id].raw, changed_text.encode())
        self.assertEqual(candidate.sources[left_id].raw, left.raw)
        self.assertEqual(program.to_payload(), data)

    def test_imported_utf8_diagnostic_and_cross_file_related_span_use_original_units(self):
        data = payload("02-namespaces")
        change_library(data, "example.left", lambda text: "// café 🦾\r\n" + text.replace("\n", "\r\n"))
        for unit in data["modules"]:
            unit["filename"] = "shared.ok"
        invalid = copy.deepcopy(data)
        change_library(invalid, "example.left", lambda text: text.replace("return 2 * value;", "return 1[s];"))
        candidate = load_bundle(invalid)
        response = validate_revision(candidate, level="represented")
        self.assertEqual(response["outcome"], "invalid")
        diagnostic = response["diagnostics"][0]
        self.assertEqual(diagnostic["code"], "OKL-E-UNIT")
        primary = diagnostic["primary"]
        self.assertEqual(primary["source_id"], "package:example.left@1.0.0")
        source = candidate.sources[primary["source_id"]]
        self.assertEqual(primary["source_revision"], source.revision)
        self.assertEqual(source.raw[primary["start_byte"]:primary["end_byte"]], b"1[s]")
        self.assertEqual(primary["element_id"], ["package", "example.left", "components", "definitions", "radius"])
        self.assertEqual(diagnostic["program_revision"], candidate.program_revision)

        inaccessible = copy.deepcopy(data)
        inaccessible["entry"]["source"] = inaccessible["entry"]["source"].replace("return 99 * value;", "return left.radius(value);")
        program = load_bundle(inaccessible)
        diagnostic = validate_revision(program)["diagnostics"][0]
        self.assertEqual(diagnostic["code"], "OKL-E-ACCESS")
        self.assertEqual(diagnostic["primary"]["source_id"], "entry")
        related = diagnostic["related"][0]
        self.assertEqual(related["source_id"], "package:example.left@1.0.0")
        source = program.sources[related["source_id"]]
        self.assertEqual(related["source_revision"], source.revision)
        self.assertIn(b'fn radius @ "radius"', source.raw[related["start_byte"]:related["end_byte"]])
        self.assertNotEqual(diagnostic["primary"]["source_revision"], related["source_revision"])

    def test_program_conditions_do_not_invent_locations_or_mutate_core_diagnostics(self):
        program = load_bundle(payload("01-keyed-rack"))
        diagnostic = Diagnostic("OKL-E-SAMPLE", "No available run.", phase="inspection")
        legacy_source = Source("source bytes", "legacy.ok")
        previous = diagnostic.to_dict(legacy_source)
        current = diagnostic_dict(diagnostic, program, "run:test")
        self.assertEqual(current["schema_version"], "ontokin.diagnostic/0.2")
        self.assertEqual(current["program_revision"], program.program_revision)
        self.assertIsNone(current["primary"])
        self.assertIsNone(current["source_id"])
        self.assertIsNone(current["source_revision"])
        self.assertEqual(current["location_status"], "program_condition_without_source_span")
        self.assertEqual(diagnostic.to_dict(legacy_source), previous)
        self.assertEqual(previous["schema_version"], "ontokin.diagnostic/0.1")
        self.assertEqual(previous["source_revision"], legacy_source.revision)
        self.assertNotIn("program_revision", previous)

    def test_generated_collection_and_occurrence_scopes_are_distinct_from_shared_definitions(self):
        program = load_bundle(payload("01-keyed-rack"))
        generated = self.item(program, 'first.fingers["middle"]')
        collection = self.item(program, "first.fingers")
        public = self.item(program, 'first.fingers["middle"].length')
        private = self.item(program, 'first.fingers["middle"].blade.length')
        self.assertIsNone(generated["source"]["span"])
        self.assertFalse(generated["source"]["generated"]["unique_declaration_span"])
        self.assertEqual(generated["source"]["generated"]["input_entry_span"]["source_id"], "package:example.hinges@1.0.0")
        self.assertTrue(public["source"]["initializer_target"]["available"])
        self.assertEqual(public["source"]["initializer_target"]["element_id"], ["keyed-rack", "demo", "first"])
        self.assertFalse(private["source"]["initializer_target"]["available"])
        for record in [generated, collection, public, private]:
            self.assertEqual(record["source"]["writable_spans"], [])
        for record in [generated, collection]:
            patch = source_patch(program, "entry", "length = self.finger_length;", "length = 0.7[m];", record["element_id"])
            with self.assertRaises(OntoKinError) as rejected:
                apply_patches(program, [patch])
            self.assertEqual(rejected.exception.code, "OKL-E-REVISION")
        definition = generated["source"]["generated"]["collection_definition_id"]
        candidate = apply_patches(program, [source_patch(program, "entry", "length = self.finger_length;", "length = 0.7[m];", definition)])
        self.assertEqual(validate_revision(candidate, level="constructed")["outcome"], "valid")
        self.assertEqual(candidate.modules[0].raw, program.modules[0].raw)


class ProgramEditReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = ProgramAgentService(Path(self.temp.name))
        self.sequence = 0

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def send(self, operation, **fields):
        self.sequence += 1
        return self.service.handle({"schema_version": "ontokin.agent/0.2", "project_id": "source-review",
                                    "request_id": str(self.sequence), "operation": operation, **fields})

    def create(self, data):
        response = self.send("create", bundle=data, expected_program_revision=None, requested_level="constructed")
        self.assertEqual(response["status"], "succeeded", response)
        return response["program_revision"]

    def item(self, revision, path):
        response = self.send("inspect", program_revision=revision, selector={"path": path},
                             fields=["identity", "source", "values", "geometry"], limit=1)
        self.assertEqual(response["status"], "succeeded", response)
        self.assertEqual(response["result"]["total"], 1)
        return response["result"]["items"][0]

    def test_c09_utf8_dot_key_candidate_failure_and_accepted_head_repair(self):
        data = payload("01-keyed-rack")
        change_library(data, "example.hinges", lambda text: "// bibliothèque 🦾\r\n" + text.replace('"middle"', '"left.eye"').replace("\n", "\r\n"))
        data["entry"]["source"] = "// café 🦾\r\n" + data["entry"]["source"].replace('"middle"', '"left.eye"').replace("\n", "\r\n")
        program = load_bundle(data)
        accepted = self.create(data)
        path = 'first.fingers["left.eye"].length'
        item = self.item(accepted, path)
        target = item["source"]["initializer_target"]
        self.assertEqual(target["parameter_path"][1], {"kind": "key", "value": "left.eye"})
        span = target["assignment_span"]
        self.assertEqual(program.entry.raw[span["start_byte"]:span["end_byte"]], b'fingers["left.eye"].length = 0.75[m];')
        self.assertGreater(span["start_byte"], program.entry.text.index('fingers["left.eye"].length'))
        bad = source_patch(program, "entry", "0.75[m]", "0.75[kg]", target["element_id"])
        response = self.send("edit", expected_program_revision=accepted, patches=[bad], requested_level="constructed")
        self.assertEqual(response["status"], "rejected", response)
        self.assertEqual(response["diagnostics"][0]["code"], "OKL-E-UNIT")
        candidate = self.service.read_program("source-review", response["program_revision"])
        diagnostic = response["diagnostics"][0]
        primary = diagnostic["primary"]
        self.assertEqual(primary["source_id"], "entry")
        self.assertEqual(primary["source_revision"], candidate.entry.revision)
        self.assertIn(b"0.75[kg]", candidate.entry.raw[primary["start_byte"]:primary["end_byte"]])
        self.assertEqual(self.service.accepted_revision("source-review"), accepted)
        self.assertEqual(self.service.read_program("source-review", accepted).to_payload(), data)
        repaired = self.send("edit", expected_program_revision=accepted,
                             patches=[source_patch(program, "entry", "0.75[m]", "0.9[m]", target["element_id"])], requested_level="constructed")
        self.assertEqual(repaired["status"], "succeeded", repaired)
        revision = repaired["program_revision"]
        self.assertEqual(self.item(revision, path)["values"]["length"]["value"], .9)
        self.assertEqual(self.item(revision, 'second.fingers["left.eye"].length')["values"]["length"]["value"], .6)
        self.assertEqual(self.service.read_program("source-review", revision).modules[0].raw, program.modules[0].raw)

    def test_c13_alias_rename_retains_nominal_identity_but_class_replacement_rejects(self):
        data = payload("02-namespaces")
        accepted = self.create(data)
        program = load_bundle(data)
        original = self.item(accepted, "a")
        text = program.entry.text.replace("import left @", "import renamed @").replace("left.", "renamed.")
        alias_edit = source_patch(program, "entry", program.entry.text, text, ["sources", "entry"])
        changed = self.send("edit", expected_program_revision=accepted, patches=[alias_edit], requested_level="constructed")
        self.assertEqual(changed["status"], "succeeded", changed)
        revision = changed["program_revision"]
        renamed = self.item(revision, "a")
        self.assertEqual(renamed["element_id"], original["element_id"])
        self.assertEqual(renamed["identity"]["definition_id"], original["identity"]["definition_id"])
        self.assertEqual(renamed["source"]["definition_span"], original["source"]["definition_span"])
        self.assertEqual(renamed["geometry"], original["geometry"])
        program = self.service.read_program("source-review", revision)
        text = program.entry.text.replace('object a @ "a": renamed.Marker', 'object a @ "a": right.Marker').replace('Ref<renamed.Marker>', 'Ref<right.Marker>')
        replacement = self.send("edit", expected_program_revision=revision,
                                patches=[source_patch(program, "entry", program.entry.text, text, ["sources", "entry"])], requested_level="constructed")
        self.assertEqual(replacement["status"], "rejected", replacement)
        self.assertEqual(replacement["diagnostics"][0]["code"], "OKL-E-ID")
        self.assertEqual(replacement["diagnostics"][0]["details"]["changed_occurrences"], [["namespaces", "demo", "a"]])
        self.assertEqual(self.service.accepted_revision("source-review"), revision)
        self.assertEqual(self.item(revision, "a")["geometry"], original["geometry"])


if __name__ == "__main__":
    unittest.main()
