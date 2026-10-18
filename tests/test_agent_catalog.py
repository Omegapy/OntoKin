"""Check discovery against the executable core and compile its shown examples.

These checks do not duplicate the catalog's descriptions. They compare its
name coverage with the actual validator and feed the published expressions
through real source elaboration/evaluation so unusable authoring examples fail.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from ontokin.agent import AgentService
from ontokin.agent_catalog import catalog
from ontokin.agent_runtime import validate_revision
from ontokin.diagnostics import Source
from ontokin.validator import BUILTIN_CALLS, BUILTIN_TYPES, FIELD_TYPES


ROOT = Path(__file__).resolve().parents[1]
ACTION_BUILDERS = {"move", "spin", "tween"}


class AgentCatalogTests(unittest.TestCase):
    def test_discovery_covers_executable_type_callable_and_object_field_registries(self):
        data = catalog()
        self.assertEqual({entry["name"] for entry in data["items"] if entry["kind"] == "type"}, BUILTIN_TYPES)
        self.assertEqual({entry["name"] for entry in data["items"] if entry["kind"] == "builtin"}, BUILTIN_CALLS)
        members = {entry["name"] for entry in data["items"] if entry["kind"] == "member"}
        self.assertLessEqual({"Object." + name for name in FIELD_TYPES}, members)
        identities = [entry["id"] for entry in data["items"]]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertFalse(data["full_product_conformance_certified"])
        json.dumps(data, ensure_ascii=False, allow_nan=False)

    def test_catalog_revision_identifies_content_and_readers_cannot_mutate_it(self):
        original = catalog()
        content = {key: value for key, value in original.items() if key != "revision"}
        encoded = json.dumps(content, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.assertEqual(original["revision"], "sha256:" + hashlib.sha256(encoded).hexdigest())
        changed = catalog()
        changed["items"][0]["domains"].append("a reader's local annotation")
        changed["units"]["base"].clear()
        self.assertEqual(catalog(), original)

    def test_closed_callable_examples_construct_in_real_typed_source(self):
        # Q notation is intentionally polymorphic catalog notation. The shown
        # examples below select these concrete quantity/component types.
        concrete = {"Q": "Length", "Vec3<Q>": "Vec3<Real>",
                    "Vector3<Q>": "Vector3<Speed>", "Range<Q>": "Range<Angle>"}
        checked = set()
        for entry in catalog()["items"]:
            if entry["kind"] != "builtin" or entry["name"] in ACTION_BUILDERS:
                continue
            with self.subTest(builtin=entry["name"]):
                result_type = concrete.get(entry["result_type"], entry["result_type"])
                source = '''ontokin "0.1";
module CatalogCheck @ "catalog-check";
profile "core-0.1";
class Probe @ "probe-type" {
    public param value @ "value": TYPE = EXAMPLE;
}
scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object probe @ "probe": Probe {}
}
'''.replace("TYPE", result_type).replace("EXAMPLE", entry["examples"][0])
                result = validate_revision(Source(source, "catalog-check.ok"), level="constructed")
                self.assertEqual(result["outcome"], "valid", result)
                self.assertEqual(result["achieved_level"], "constructed", result)
                checked.add(entry["name"])
        self.assertEqual(checked, BUILTIN_CALLS - ACTION_BUILDERS)

    def test_action_examples_evaluate_with_their_documented_fixture_bindings(self):
        original = (ROOT / "docs/language-design/core-v0.1/01-independent-parts.ok").read_text(encoding="utf-8")
        move = "move(rig, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s])"
        look = "rig.look(90[deg], 1[s])"
        self.assertEqual(original.count(move), 1)
        self.assertEqual(original.count(look), 1)
        checked = set()
        for entry in catalog()["items"]:
            if entry["kind"] != "builtin" or entry["name"] not in ACTION_BUILDERS:
                continue
            with self.subTest(builtin=entry["name"]):
                self.assertEqual(entry["result_type"], "Action")
                # P01 supplies an independent root orientation channel and its
                # hinge/slider bindings. Replacing one builder preserves the
                # surrounding authored event/action lifecycle without mocks.
                source = original.replace(look if entry["name"] == "tween" else move,
                                          entry["examples"][0])
                result = validate_revision(Source(source, "catalog-actions.ok"), level="evaluated")
                self.assertEqual(result["outcome"], "valid", result)
                self.assertEqual(result["achieved_level"], "evaluated", result)
                self.assertEqual(result["run_state"]["valid_until_seconds"], "3")
                self.assertEqual(result["run_state"]["valid_until_side"], "after")
                checked.add(entry["name"])
        self.assertEqual(checked, ACTION_BUILDERS)

    def test_real_discovery_filters_expose_a_constructor_and_an_unavailable_capability(self):
        with tempfile.TemporaryDirectory(prefix="ontokin-catalog-test-") as directory:
            with AgentService(Path(directory)) as service:
                common = {"schema_version": "ontokin.agent/0.1", "project_id": "catalog-test",
                          "operation": "discover", "profile": "core-0.1", "limit": 1}
                found = service.handle({**common, "request_id": "sphere",
                                        "filter": {"kind": "builtin", "name": "sphere"}}, wait=True)
                self.assertEqual(found["status"], "succeeded", found)
                self.assertEqual([entry["name"] for entry in found["result"]["items"]], ["sphere"])
                self.assertFalse(found["truncated"])
                unsupported = service.handle({**common, "request_id": "contacts",
                                              "filter": {"kind": "capability", "capability": "contact_and_collision_response"}}, wait=True)
                self.assertEqual(unsupported["status"], "succeeded", unsupported)
                item, = unsupported["result"]["items"]
                self.assertEqual(item["availability"], "unsupported")
                self.assertEqual(item["available_levels"], [])


if __name__ == "__main__":
    unittest.main()
