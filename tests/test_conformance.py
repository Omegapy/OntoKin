"""End-to-end source outcomes and the published diagnostic schema."""

import json
import re
import unittest

from ontokin.conformance import run_conformance
from ontokin.fixtures import DEFAULT_FIXTURES


def schema_errors(value, schema, root, path="$"):
    """Check the keyword subset used by the repository's diagnostic schema.

    This is a test helper for this artifact, not a general JSON Schema library.
    It has no network resolution or external runtime dependency.
    """
    if "$ref" in schema:
        target = root
        for part in schema["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return schema_errors(value, target, root, path)
    if "anyOf" in schema:
        options = [schema_errors(value, option, root, path) for option in schema["anyOf"]]
        return [] if any(not result for result in options) else [f"{path}: no anyOf alternative matched"]
    errors = []
    types = {
        "object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str), "integer": lambda x: type(x) is int,
        "null": lambda x: x is None,
    }
    if "type" in schema and not types[schema["type"]](value):
        return [f"{path}: wrong type"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: const differs")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: unrecognized enum")
    if isinstance(value, dict):
        for field in schema.get("required", []):
            if field not in value:
                errors.append(f"{path}: missing {field}")
        for key, item in value.items():
            if key in schema.get("properties", {}):
                errors += schema_errors(item, schema["properties"][key], root, path + "." + key)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: extra {key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: too few items")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            errors.append(f"{path}: duplicate items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += schema_errors(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: string too short")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: pattern does not match")
    if isinstance(value, (int, float)) and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: below minimum")
    return errors


class ConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_conformance()

    def test_all_published_cases_and_observations(self):
        self.assertEqual(self.report["summary"]["total"], 43)
        for case in self.report["cases"]:
            with self.subTest(case=case["id"]):
                failures = [c for c in case["checks"] if not c["passed"]]
                self.assertEqual(failures, [])

    def test_actual_diagnostics_match_published_schema_and_registry(self):
        schema = json.loads((DEFAULT_FIXTURES / "diagnostic.schema.json").read_text())
        specification = (DEFAULT_FIXTURES.parent / "OK-LANG-001-core-language-specification.md").read_text()
        codes = set(re.findall(r"`(OKL-[EW]-[A-Z0-9-]+)`", specification))
        for case in self.report["cases"]:
            diagnostic = case["diagnostic"]
            if diagnostic is None:
                continue
            with self.subTest(case=case["id"]):
                self.assertEqual(schema_errors(diagnostic, schema, schema), [])
                self.assertIn(diagnostic["code"], codes)
                self.assertEqual(diagnostic["source_revision"], case["source_revision"])
                self.assertTrue(all(re.fullmatch(r"LANG-(?:00[1-9]|01[0-9]|02[0-8])", rule)
                                    for rule in diagnostic["rule_ids"]))

    def test_source_evidence_does_not_claim_agent_protocol_or_universal_numeric_conformance(self):
        self.assertFalse(self.report["full_core_conformance_certified"])
        self.assertFalse(self.report["agent_protocol_checks"]["executed"])
        self.assertEqual(len(self.report["agent_protocol_checks"]["deferred_case_ids"]), 10)


if __name__ == "__main__":
    unittest.main()
