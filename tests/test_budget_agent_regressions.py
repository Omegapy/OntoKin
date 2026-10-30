"""Regressions for host clocks, exact discovery and tentative delivery claims."""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ontokin.budget_agent import BudgetAgentService
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.execution_budget import HostPolicy


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "ontokin.agent/0.7"
PROFILE = "planar-reach-budget-0.1"
POLICY = HostPolicy(400000, 80000, "clock-and-discovery-regression")
TEXT = '''ontokin "0.7";
module Regression @ "regression";
profile "planar-reach-budget-0.1";
execution { max_operations = 200000; max_elapsed = 60[s]; }
public class Local @ "local-class" {
    geometry = box(vec3(1[m], 1[m], 1[m]));
    physical = no_body();
}
scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object item @ "item": Local {}
}
'''


def request(operation, identity="r", **fields):
    return {"schema_version": PROTOCOL, "project_id": "regressions", "request_id": identity,
            "operation": operation, **fields}


def program():
    return ProgramBundle(SourceUnit("entry", "regressions.ok", TEXT.encode()))


def delivered_edit(identity, original, old, replacement):
    start = original.entry.raw.index(old.encode())
    return request("edit", identity, expected_program_revision=original.program_revision,
        requested_level="delivered", destination="ontokin.glb/0.7",
        options={"fps": 2, "end": "0.5", "helpers": False},
        patches=[{"source_id": "entry", "source_revision": original.entry.revision,
                  "element_id": ["sources", "entry"], "start_byte": start,
                  "end_byte": start + len(old.encode()), "expected_text": old,
                  "replacement": replacement}])


class BudgetAgentRegressionTests(unittest.TestCase):
    def assert_no_delivery_claim(self, response):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        self.assertEqual(response["requested_level"], "delivered")
        self.assertNotEqual(response["achieved_level"], "delivered")
        result = response.get("result") or {}
        self.assertNotEqual(result.get("achieved_level"), "delivered")
        self.assertEqual(result.get("delivery"), "failed")
        forbidden = {"artifact_id", "report", "total_bytes", "sha256", "mime_type", "destination",
                     "data_base64", "artifact_provenance", "producer_request_id"}
        self.assertEqual(forbidden & set(result), set(), result)

    def assert_cancelled_without_effects(self, service, original):
        response = service.handle(copy.deepcopy(original))
        self.assertEqual(response["status"], "cancelled", response)
        self.assertIsNone(service.accepted_revision("regressions"))
        with service._store.connection() as db:
            retained = service._store.request(db, "regressions", original["request_id"])
            self.assertEqual(retained["state"], "cancelled")
            self.assertIsNone(retained["owner"])
            for table in ("runs", "artifacts", "acceptance_identities"):
                self.assertEqual(db.execute("SELECT count(*) FROM " + table).fetchone()[0], 0)
        return response

    def test_late_host_clock_exception_is_preserved_and_retry_never_reads_clock(self):
        marker = RuntimeError("host clock disappeared after successful work")
        state = {"armed": False, "calls": 0, "raises": 0}

        def clock():
            state["calls"] += 1
            if state["armed"]:
                state["raises"] += 1
                raise marker
            return 12.0

        with tempfile.TemporaryDirectory() as directory, BudgetAgentService(
                directory, host_policy=POLICY, clock=clock) as service:
            original = request("create", bundle=program().to_payload(), expected_program_revision=None,
                               requested_level="constructed")
            execute, prepared = service._execute, []

            def arm_after_computation(task, check):
                execute(task, check)
                prepared.append(task.accept)
                state["armed"] = True

            with patch.object(service, "_execute", side_effect=arm_after_computation):
                with self.assertRaises(RuntimeError) as caught:
                    service.handle(original)
            self.assertIs(caught.exception, marker)
            self.assertEqual(prepared, [True])
            self.assertGreater(state["calls"], 2)
            self.assertEqual(state["raises"], 1)
            reads = state["calls"]
            response = self.assert_cancelled_without_effects(service, original)
            self.assertEqual(response["execution_budget"]["budget_reason"], "host_clock_failed")
            self.assertEqual(response["execution_budget"]["started_monotonic_seconds"], 12.0)
            self.assertEqual(state["calls"], reads)
            self.assertEqual(service.handle(original), response)
            self.assertEqual(state["calls"], reads)

    def test_nonfinite_or_backward_clock_is_durably_cancelled_after_valid_start(self):
        for invalid in (float("nan"), float("inf"), float("-inf"), 4.0):
            with self.subTest(value=invalid):
                calls = [0]

                def clock():
                    calls[0] += 1
                    return 5.0 if calls[0] == 1 else invalid

                with tempfile.TemporaryDirectory() as directory, BudgetAgentService(
                        directory, host_policy=POLICY, clock=clock) as service:
                    original = request("create", bundle=program().to_payload(), expected_program_revision=None,
                                       requested_level="constructed")
                    with self.assertRaisesRegex(ValueError, "finite monotonic"):
                        service.handle(original)
                    self.assertEqual(calls[0], 2)
                    response = self.assert_cancelled_without_effects(service, original)
                    self.assertEqual(response["execution_budget"]["budget_reason"], "host_clock_failed")
                    self.assertEqual(response["execution_budget"]["started_monotonic_seconds"], 5.0)
                    self.assertEqual(calls[0], 2)

    def test_discovery_names_exact_header_service_store_and_file_edit_domain(self):
        with tempfile.TemporaryDirectory() as directory, BudgetAgentService(directory, host_policy=POLICY) as service:
            response = service.handle(request("discover", profile=PROFILE, limit=1000))
            self.assertEqual(response["status"], "succeeded", response)
            result = response["result"]
            self.assertEqual(result["source_header"],
                'ontokin "0.7"; module Example @ "example"; profile "planar-reach-budget-0.1";')
            self.assertEqual(result["language_version"], "0.7")
            self.assertEqual(result["agent_contract"], PROTOCOL)
            item = next(item for item in result["items"] if item.get("kind") == "protocol")
            self.assertEqual(item["name"], PROTOCOL)
            self.assertEqual(item["store_filename"], service.database_path.name)
            self.assertEqual(item["store_schema"], service._store.schema_version)
            self.assertEqual(item["signature"], "BudgetAgentService(store, host_policy=HostPolicy(...))")
            self.assertIn("Only complete-file source identities authorize exact UTF-8 byte patches", item["domains"])
            self.assertNotIn('protocol="ontokin.agent/0.6"', item["signature"])
            interface = result["budget_agent_interface"]
            self.assertEqual(interface["edit_scope"]["element_id"], ["sources", "<source_id>"])
            self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
            self.assertEqual(result["execution_defaults"], interface["defaults"])
            self.assertEqual(interface["host_ceilings"], {"max_operations": 400000, "max_elapsed_ms": 80000})
            self.assertEqual(interface["max_representable_limit"], (1 << 53) - 1)
            self.assertNotIn("max_operations", result["limits"])
            self.assertNotIn("max_elapsed_ms", result["limits"])
            self.assertEqual(interface["fixed_budgets"]["max_objects"], 1000)
            for key in ("request_schema", "response_schema"):
                self.assertTrue((ROOT / interface[key]).is_file(), interface[key])

    def test_linked_discovery_preserves_six_and_seven_definition_profiles_and_real_specs(self):
        modules = []
        imports = []
        for suffix, language, profile in (("six", "0.6", "planar-reach-0.1"), ("seven", "0.7", PROFILE)):
            raw = (f'ontokin "{language}"; module Library_{suffix} @ "library-{suffix}";\n'
                   f'profile "{profile}";\n'
                   f'public class Box_{suffix} @ "box-{suffix}" {{\n'
                   ' geometry = box(vec3(1[m], 1[m], 1[m])); physical = no_body();\n}\n').encode()
            package = "regression." + suffix
            unit = SourceUnit("package:" + package + "@0.1.0", suffix + ".ok", raw, package, "0.1.0")
            modules.append(unit)
            imports.append(f'import {suffix} @ "{suffix}" from "{package}" version "0.1.0" digest "{unit.revision}";')
        entry = TEXT.replace('public class Local', "\n".join(imports) + "\npublic class Local")
        bundle = ProgramBundle(SourceUnit("entry", "linked-discovery.ok", entry.encode()), tuple(modules))
        with tempfile.TemporaryDirectory() as directory, BudgetAgentService(directory, host_policy=POLICY) as service:
            response = service.handle(request("discover", profile=PROFILE, limit=1000, bundle=bundle.to_payload()))
            self.assertEqual(response["status"], "succeeded", response)
            result = response["result"]
            self.assertIn("planar-reach-0.1", result["compatible_definition_profiles"])
            self.assertIn(PROFILE, result["compatible_definition_profiles"])
            self.assertEqual(result["program_context"]["program_revision"], bundle.program_revision)
            for unit, language, profile in ((modules[0], "0.6", "planar-reach-0.1"), (modules[1], "0.7", PROFILE)):
                matched = [item for item in result["items"]
                           if item.get("source_id") == unit.source_id and item.get("kind") == "class"]
                self.assertEqual(len(matched), 1)
                self.assertEqual(matched[0]["language_version"], language)
                self.assertEqual(matched[0]["profile"], profile)
                self.assertEqual(matched[0]["source_revision"], unit.revision)
            for item in result["items"]:
                path = item.get("specification")
                if path is not None:
                    self.assertTrue((ROOT / path.split("#", 1)[0]).is_file(), path)
            for path in result["complete_examples"]:
                self.assertTrue((ROOT / path).is_file(), path)

    def test_nominal_identity_rejection_after_export_has_no_published_delivery_claim(self):
        original = program()
        with tempfile.TemporaryDirectory() as directory, BudgetAgentService(directory, host_policy=POLICY) as service:
            baseline = service.handle(request("create", "create", bundle=original.to_payload(),
                expected_program_revision=None, requested_level="delivered", destination="ontokin.glb/0.7",
                options={"fps": 2, "end": "0.5", "helpers": False}))
            self.assertEqual(baseline["status"], "succeeded", baseline)
            old_artifact = baseline["result"]["artifact_id"]
            old_run = copy.deepcopy(service.get_run("regressions", baseline["run_id"]))
            edited = delivered_edit("nominal-change", original, '"local-class"', '"replacement-class"')
            export, tentative = service._export, []

            def observe_real_export(task, check, **kwargs):
                export(task, check, **kwargs)
                tentative.append(task.artifact[2])

            with patch.object(service, "_export", side_effect=observe_real_export):
                failed = service.handle(edited)
            self.assertEqual(len(tentative), 1)
            self.assertNotEqual(tentative[0], old_artifact)
            self.assertIn("OKL-E-ID", [item["code"] for item in failed["diagnostics"]])
            self.assert_no_delivery_claim(failed)
            self.assertEqual(failed["accepted_program_revision"], original.program_revision)
            self.assertEqual(service.accepted_revision("regressions"), original.program_revision)
            self.assertEqual(service.get_run("regressions", baseline["run_id"]), old_run)
            missing = service.handle(request("artifact", "candidate-artifact", artifact_id=tentative[0]))
            self.assertEqual(missing["protocol_error"]["code"], "OKA-E-ARTIFACT", missing)
            preserved = service.handle(request("artifact", "old-artifact", artifact_id=old_artifact, max_bytes=64))
            self.assertEqual(preserved["status"], "succeeded", preserved)
            self.assertEqual(preserved["result"]["sha256"], baseline["result"]["sha256"])
            self.assertEqual(service.handle(copy.deepcopy(edited)), failed)

    def test_competing_accepted_edit_removes_losing_tentative_delivery_claim(self):
        original = program()
        winner = ProgramBundle(SourceUnit("entry", original.entry.filename,
            TEXT.replace("vec3(1[m], 1[m], 1[m])", "vec3(2[m], 1[m], 1[m])").encode()))
        loser = ProgramBundle(SourceUnit("entry", original.entry.filename,
            TEXT.replace("vec3(1[m], 1[m], 1[m])", "vec3(3[m], 1[m], 1[m])").encode()))
        with tempfile.TemporaryDirectory() as directory, BudgetAgentService(directory, host_policy=POLICY) as service, \
                BudgetAgentService(directory, host_policy=POLICY) as competitor:
            created = service.handle(request("create", "create", bundle=original.to_payload(),
                                             expected_program_revision=None, requested_level="constructed"))
            self.assertEqual(created["status"], "succeeded", created)
            first = delivered_edit("losing-edit", original, "vec3(1[m], 1[m], 1[m])", "vec3(3[m], 1[m], 1[m])")
            second = delivered_edit("winning-edit", original, "vec3(1[m], 1[m], 1[m])", "vec3(2[m], 1[m], 1[m])")
            commit, winners, tentative = service._commit_task, [], []

            def publish_second_first(task):
                if task.request["request_id"] == first["request_id"] and not winners:
                    self.assertEqual(task.response["status"], "succeeded")
                    self.assertIsNotNone(task.artifact)
                    tentative.append(task.artifact[2])
                    winning = competitor.handle(second)
                    self.assertEqual(winning["status"], "succeeded", winning)
                    winners.append(winning)
                return commit(task)

            with patch.object(service, "_commit_task", side_effect=publish_second_first):
                failed = service.handle(first)
            self.assertEqual(len(winners), 1)
            self.assertIn("OKL-E-REVISION", [item["code"] for item in failed["diagnostics"]])
            self.assert_no_delivery_claim(failed)
            self.assertEqual(failed["accepted_program_revision"], winner.program_revision)
            self.assertEqual(failed["program_revision"], loser.program_revision)
            self.assertEqual(service.accepted_revision("regressions"), winner.program_revision)
            self.assertNotEqual(tentative[0], winners[0]["result"]["artifact_id"])
            missing = service.handle(request("artifact", "loser-artifact", artifact_id=tentative[0]))
            self.assertEqual(missing["protocol_error"]["code"], "OKA-E-ARTIFACT", missing)
            retrieved = service.handle(request("artifact", "winner-artifact",
                artifact_id=winners[0]["result"]["artifact_id"], max_bytes=64))
            self.assertEqual(retrieved["status"], "succeeded", retrieved)
            self.assertEqual(retrieved["program_revision"], winner.program_revision)
            self.assertEqual(service.handle(copy.deepcopy(first)), failed)
            with service._store.connection() as db:
                self.assertEqual(db.execute("SELECT count(*) FROM artifacts").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
