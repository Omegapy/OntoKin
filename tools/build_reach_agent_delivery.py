#!/usr/bin/env python3
"""Retain actual Agent/0.6 lifecycle, repair and artifact-retrieval evidence.

The documented service performs every source operation and export. This
producer does not invoke a compiler, evaluator, geometry builder or GLB writer.
Its actual request/response files remain inputs to a separate transport audit;
native supplied-byte and browser validation are also separate roles.
"""
from __future__ import annotations

import argparse
import base64
import copy
from fractions import Fraction
import json
from pathlib import Path
import platform
import sys
import time
import traceback
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.reach_delivery_inventory import (
    AGENT_CASES, BASE, MAX_BYTES, ROOT, decode, descriptor, finish_inputs,
    fresh_output, frozen_cases, read_bounded, require, selected_cases, settings,
    sha, snapshot, source_files, utc, write_json,
)

SCHEMA = "ontokin.reach-agent-delivery-workflow/0.1"
PROTOCOL = "ontokin.agent/0.6"
TARGET = "ontokin.glb/0.6"
PROTOCOL_FILE = f"{BASE}/draft2-supplements/protocol-cases.json"
RELEASE_PROBES_FILE = f"{BASE}/draft2-supplements/release-probes.json"
CHUNK_BYTES = 32768


def reach_records(response):
    return [record for item in response["result"].get("items", [])
            for record in item.get("actions", []) if record.get("kind") == "reach_planar"]


def projection(response, path="reach"):
    items = [item for item in response["result"]["items"] if item["path"] == path]
    require(len(items) == 1 and len(items[0]["actions"]) == 1, "Expected one complete named reach")
    return items[0]["actions"][0]


def current(response, path="reach"):
    value = projection(response, path)["current"]
    require(value["available"] is True, "An actual available reach sample is required")
    return value["value"]


class Recorder:
    def __init__(self, output, report):
        from ontokin.bundle import load_file_manifest
        from ontokin.program_agent import ProgramAgentService

        self.output, self.report = output, report
        self.service = ProgramAgentService(output / "service-store", protocol=PROTOCOL)
        self.load_file_manifest = load_file_manifest
        self.frozen = frozen_cases()
        self.programs = {}
        self.bindings, self.requests, self.responses = {}, {}, {}
        self.contexts = {}
        self.trace = report["exchanges"]
        self.serial = 0
        self.protocol_cases = decode(read_bounded(ROOT / PROTOCOL_FILE))["protocol_cases"]
        self.release_probes = {row["id"]: row for row in
                               decode(read_bounded(ROOT / RELEASE_PROBES_FILE))["probes"]}
        self.steps = {step["id"]: step for case in self.protocol_cases for step in case["steps"]}
        require([len(case["steps"]) for case in self.protocol_cases] == [9, 9, 5, 7, 12]
                and len(self.steps) == 42, "The frozen 42-step protocol inventory differs")
        report.update(implementation=copy.deepcopy(self.service.implementation),
                      protocol_inputs=descriptor(ROOT / PROTOCOL_FILE, relative_to=ROOT),
                      release_probe_inputs=descriptor(ROOT / RELEASE_PROBES_FILE, relative_to=ROOT))

    def write(self, name, value):
        path = self.output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, value)
        return descriptor(path, relative_to=self.output)

    def bundle(self, case_id):
        if case_id not in self.programs:
            base = ROOT / BASE / ("draft2-supplements" if case_id.startswith("L") else "")
            item = self.frozen[case_id]
            program = self.load_file_manifest(base / item["file_manifest"])
            require(program.program_revision == item["program_revision"], "Frozen source revision differs: " + case_id)
            self.programs[case_id] = program
        return self.programs[case_id]

    def request(self, project, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": project,
                "request_id": f"reach-delivery-{self.serial:05d}", "operation": operation, **fields}

    def exchange(self, role, request, *, expected="succeeded", code=None, method="handle"):
        require(role not in self.requests, "Repeated exchange role: " + role)
        require(method in ("handle", "submit"), "Only actual service entry points may be recorded")
        sequence = len(self.trace) + 1
        stem = f"exchanges/{sequence:05d}"
        row = {"role": role, "sequence": sequence, "method": method, "started_at": utc(),
               "request": self.write(stem + ".request.json", request)}
        # Reserve the sequence before dispatch. The real cancellation hook
        # records nested status/cancel requests while the export is running.
        self.trace.append(row)
        self.requests[role] = copy.deepcopy(request)
        try:
            response = getattr(self.service, method)(copy.deepcopy(request))
            row["response"] = self.write(stem + ".response.json", response)
            self.responses[role] = copy.deepcopy(response)
            statuses = (expected,) if isinstance(expected, str) else expected
            require(response["status"] in statuses,
                    f"{role}: expected {statuses}, received {response['status']}: "
                    f"{response.get('protocol_error')}; {response.get('diagnostics')}")
            require(response["schema_version"] == PROTOCOL, "Wrong response binding: " + role)
            if code is not None:
                codes = [item["code"] for item in response["diagnostics"]]
                if response.get("protocol_error"):
                    codes.append(response["protocol_error"]["code"])
                require(code in codes, f"{role}: expected {code}, received {codes}")
            row["checks"] = "passed"
            return response
        except Exception as error:
            row["checks"] = "failed"
            row["failure"] = {"type": type(error).__name__, "message": str(error)}
            raise
        finally:
            row["finished_at"] = utc()

    def send(self, role, project, operation, *, expected="succeeded", code=None, **fields):
        return self.exchange(role, self.request(project, operation, **fields), expected=expected, code=code)

    def effects(self, project):
        with self.service._store.connection() as database:
            counts = {name: database.execute("SELECT count(*) FROM " + name + " WHERE project_id=?",
                                             (project,)).fetchone()[0] for name in ("runs", "artifacts")}
        return {**counts, "accepted_program_revision": self.service.accepted_revision(project)}

    def retain_source(self, label, project, program):
        actual = self.service.read_program(project, program.program_revision)
        require(actual.to_payload() == program.to_payload(), "Retained source bytes changed: " + label)
        record = {"label": label, "project_id": project, "program_revision": program.program_revision,
                  "bundle": self.write(f"snapshots/{label}/program.bundle.json", actual.to_payload()),
                  "manifest": self.write(f"snapshots/{label}/source-manifest.json", actual.manifest()),
                  "units": []}
        for index, unit in enumerate(actual.units):
            path = self.output / f"snapshots/{label}/source-{index:02d}.ok"
            with path.open("xb") as stream:
                stream.write(unit.raw)
            record["units"].append({"source_id": unit.source_id, "source_revision": unit.revision,
                                    "filename": unit.filename, "package_id": unit.package_id,
                                    "version": unit.version, "file": descriptor(path, relative_to=self.output)})
        self.report["snapshots"].append(record)
        return record

    def retained_run(self, project, run_id):
        require(type(run_id) is str, "An actual retained run identity is required")
        return copy.deepcopy(self.service._store.read_run(project, run_id))

    def require_retained(self, label, project, run_id, original):
        after = self.retained_run(project, run_id)
        require(after == original, "Historical run changed: " + label)
        return self.write(f"retained-runs/{label}.json",
                          {"project_id": project, "run_id": run_id, "before": original, "after": after})

    def resolve(self, value):
        if type(value) is dict:
            if set(value) == {"$fixture_bundle"}:
                return self.bundle(value["$fixture_bundle"]).to_payload()
            if set(value) == {"$binding"}:
                return copy.deepcopy(self.bindings[value["$binding"]])
            if set(value) == {"$binding_minus_one"}:
                return self.bindings[value["$binding_minus_one"]] - 1
            return {key: self.resolve(item) for key, item in value.items()}
        if type(value) is list:
            return [self.resolve(item) for item in value]
        return value

    def step(self, identity):
        from ontokin.json_limits import measure_json

        row = self.steps[identity]
        expected = row["expected"]
        response = self.exchange(identity, self.resolve(row["request_template"]), expected=expected["status"],
                                 code=expected.get("diagnostic_code", expected.get("protocol_error_code")))
        for name in ("accepted_program_revision", "program_revision"):
            if name in expected:
                require(response[name] == expected[name], identity + ": wrong " + name)
        diagnostics = response["diagnostics"]
        for name in ("category", "phase"):
            if name in expected:
                require(expected[name] in [item[name] for item in diagnostics], identity + ": wrong " + name)
        if "reach_code" in expected:
            require(expected["reach_code"] in [item.get("details", {}).get("reach_code") for item in diagnostics],
                    identity + ": wrong reach diagnostic")
        run = (response.get("result") or {}).get("run_state")
        for name in ("valid_until_seconds", "valid_until_side"):
            if name in expected:
                require(run[name] == expected[name], identity + ": wrong " + name)
        if "run_status" in expected:
            require(run["status"] == expected["run_status"], identity + ": wrong retained run status")
        if "same_run_as" in expected:
            require(response["run_id"] == self.bindings[expected["same_run_as"]], identity + ": changed run identity")
        if "receipt_equals" in expected:
            require(response == self.bindings[expected["receipt_equals"]], identity + ": retry changed receipt")
        if "target_terminal_response_equals" in expected:
            require(response["result"]["target"] == self.bindings[expected["target_terminal_response_equals"]],
                    identity + ": status changed terminal receipt")
        if "canonical_request_identical_to" in expected:
            require(self.requests[identity] == self.requests[expected["canonical_request_identical_to"]],
                    identity + ": frozen retry is not canonical-identical")
        prefix = identity.split(".")[0]
        for name, expression in row["capture_bindings"].items():
            if expression == "response.run_id":
                value = response["run_id"]
                require(value is not None, identity + ": missing captured run")
            elif expression in ("complete immutable terminal response", "complete response"):
                value = response
            elif expression == "actual returned source.initializer_target":
                value = response["result"]["items"][0]["source"]["initializer_target"]
            elif expression == "logical_json_entries(complete response)":
                value = measure_json(response)["entries"]
            else:
                raise ValueError("Unknown frozen capture expression: " + expression)
            self.bindings[prefix + "." + name] = copy.deepcopy(value)
        return response

    def run_lp01(self):
        project, program = "reach-reconstruction-lp01", self.bundle("L04")
        self.step("LP01.01")
        failed = self.step("LP01.02")
        retained = self.retained_run(project, failed["run_id"])
        before = self.step("LP01.03")
        a, b = current(before, "reach_a"), current(before, "reach_b")
        require(a["lifecycle"] == "running" and len(a["claimed_joint_ids"]) == 2, "L04 lost original claims")
        require(b["lifecycle"] == "pending" and b["resolved_joint_targets_rad"] is None
                and b["claimed_joint_ids"] == [], "Failed L04 handoff partially admitted the new action")
        for identity in ("LP01.04", "LP01.05", "LP01.06"):
            self.step(identity)
        reset, prefix = self.step("LP01.07"), self.step("LP01.08")
        require(reset["run_id"] != failed["run_id"] and prefix["run_id"] == reset["run_id"],
                "L04 reset/prefix run identities differ")
        require(current(self.step("LP01.09"), "reach_a")["lifecycle"] == "running", "L04 prefix is unavailable")
        require(self.effects(project)["artifacts"] == 0, "The original LP01 steps must not export")
        history = self.require_retained("LP01-failure", project, failed["run_id"], retained)
        source = self.retain_source("LP01-L04", project, program)
        self.contexts["L04"] = {"project": project, "program": program, "source_snapshot": source,
                               "prior_run": prefix["run_id"], "failed_run": failed["run_id"],
                               "failed_snapshot": retained, "prefix_snapshot": self.retained_run(project, prefix["run_id"]),
                               "protocol_roles": [f"LP01.{number:02d}" for number in range(1, 10)]}
        return {"retained_failure": history, "reset_run": reset["run_id"], "prefix_run": prefix["run_id"],
                "original_steps_exported": False}

    def lp02_evidence(self, identity, program):
        siblings, sources = {}, {}
        rows = self.steps[identity]["required_evidence_reads"]
        require(len(rows) == 5, "LP02 requires four sibling reads and one complete source read")
        for index, row in enumerate(rows):
            response = self.exchange(f"{identity}/evidence/{index}", self.resolve(row["request_template"]))
            items, expected = response["result"]["items"], row["expected"]
            require(len(items) == expected["returned_item_count"] and not response["truncated"]
                    and response["next_cursor"] is None, "LP02 evidence is incomplete")
            if "canonical_length_m" in expected:
                item = items[0]
                value = copy.deepcopy(item["values"]["forearm_length"])
                require(value["value"] == expected["canonical_length_m"], "An unchanged sibling length differs")
                origin = value["origin"]
                require(origin["source_id"] != "entry"
                        and origin["source_revision"] == program.sources[origin["source_id"]].revision,
                        "A sibling no longer has the unchanged library origin")
                for dependency in value["dependencies"]:
                    require(dependency.pop("program_revision") == program.program_revision,
                            "Sibling dependency context identifies another program")
                siblings[tuple(item["element_id"])] = {
                    "path": item["path"], "identity": item["identity"], "value": value,
                    **{key: item["source"][key] for key in ("source_id", "source_revision", "definition_span")}}
            else:
                units = {unit.source_id: unit for unit in program.units}
                identities = []
                for returned in response["result"]["source_units"]:
                    unit = units[returned["source_id"]]
                    require(returned["source"].encode("utf-8") == unit.raw and returned["filename"] == unit.filename
                            and returned["source_revision"] == unit.revision, "LP02 returned different source bytes")
                    identities.append({"source_id": unit.source_id, "source_revision": unit.revision,
                                       "filename": unit.filename, "package_id": unit.package_id, "version": unit.version})
                    sources[unit.source_id] = returned
                require(identities == expected["exact_source_unit_identities"], "LP02 source-unit identities differ")
        require(len(siblings) == 4 and len(sources) == 4, "LP02 omitted sibling or source-unit evidence")
        return siblings, sources

    def run_lp02(self):
        project = "reach-reconstruction-lp02"
        first = self.step("LP02.01")
        retained = self.retained_run(project, first["run_id"])
        old, new = self.bundle("P13"), self.bundle("P20")
        old_source = self.retain_source("LP02-P13", project, old)
        authority = self.step("LP02.02")["result"]["items"][0]["source"]["initializer_target"]
        change = self.steps["LP02.05"]["request_template"]["patches"][0]
        require(authority["available"] and authority["rendered_path"] == 'arms["first"].forearm_length',
                "LP02 did not return actual writable initializer authority")
        require(change["element_id"] == authority["element_id"]
                and change["source_id"] == authority["span"]["source_id"]
                and change["source_revision"] == authority["span"]["source_revision"]
                and authority["span"]["start_byte"] <= change["start_byte"]
                and change["end_byte"] <= authority["span"]["end_byte"], "LP02 patch exceeds inspected authority")
        self.step("LP02.03")
        self.step("LP02.04")
        edited = self.step("LP02.05")
        effects = self.effects(project)
        self.step("LP02.06")
        self.step("LP02.07")
        require(self.effects(project) == effects, "LP02 retry/status caused another edit or run")
        old_reply, new_reply = self.step("LP02.08"), self.step("LP02.09")
        old_records, new_records = reach_records(old_reply), reach_records(new_reply)
        require(len(old_records) == len(new_records) == 1
                and old_records[0]["element_id"] == new_records[0]["element_id"], "LP02 changed action identities")
        for case_id, record in (("P13", old_records[0]), ("P20", new_records[0])):
            expectation = self.frozen[case_id]["expected"]
            sample = next(item for item in expectation["samples"] if item["side"] == "after"
                          and Fraction(int(item["time"]["numerator"]), int(item["time"]["denominator"])) == Fraction(3, 2))
            actual = record["current"]["value"]
            for field in ("joint_coordinates_rad", "joint_rates_rad_per_s"):
                require(actual[field] == sample[field], "LP02 differs from the exact frozen " + field)
            require(actual["resolved_joint_targets_rad"] == expectation["independent_solution"]["resolved_joint_targets_rad"],
                    "LP02 resolved targets differ from the frozen case")
            require(record["accepted_program_revision"] == new.program_revision and not record["candidate_only"],
                    "LP02 historical projection confused current head with source identity")
        old_siblings, old_sources = self.lp02_evidence("LP02.08", old)
        new_siblings, new_sources = self.lp02_evidence("LP02.09", new)
        require(old_siblings == new_siblings, "LP02 changed one of the four untouched siblings")
        require({key: value for key, value in old_sources.items() if key != "entry"}
                == {key: value for key, value in new_sources.items() if key != "entry"}, "LP02 changed library bytes")
        new_source = self.retain_source("LP02-P20", project, new)
        history = self.require_retained("LP02-old-run", project, first["run_id"], retained)
        for name, program, source, run in (("P13", old, old_source, first["run_id"]),
                                           ("P20", new, new_source, edited["run_id"])):
            self.contexts[name] = {"project": project, "program": program, "source_snapshot": source,
                                   "prior_run": run, "protocol_roles": [f"LP02.{number:02d}" for number in range(1, 10)]}
        return {"retained_old_run": history, "unchanged_siblings": 4, "complete_source_reads": 2,
                "additional_evidence_reads": 10, "old_program_revision": old.program_revision,
                "repaired_program_revision": new.program_revision}

    def run_lp03(self):
        project, old, new = "reach-reconstruction-lp03", self.bundle("N06"), self.bundle("P10")
        self.step("LP03.01")
        failure = self.step("LP03.02")
        retained = self.retained_run(project, failure["run_id"])
        sample = current(self.step("LP03.03"))
        require(sample["lifecycle"] == sample["goal_outcome"] == "pending"
                and sample["claimed_joint_ids"] == [] and sample["resolved_joint_targets_rad"] is None,
                "Failed admission published partial state")
        changed = self.step("LP03.04")
        record = projection(self.step("LP03.05"))
        require(record["program_revision"] == old.program_revision
                and record["accepted_program_revision"] == new.program_revision
                and not record["candidate_only"], "LP03 lost accepted source/history distinction")
        require(changed["program_revision"] == new.program_revision, "LP03 repair differs from exact P10")
        self.retain_source("LP03-N06", project, old)
        self.retain_source("LP03-P10", project, new)
        self.exchange("LP03/failure-retry", self.requests["LP03.02"], expected="rejected", code="OKL-E-REACH")
        require(self.responses["LP03/failure-retry"] == failure, "LP03 failure retry changed")
        return {"retained_failure": self.require_retained("LP03-failure", project, failure["run_id"], retained)}

    def measured_q03_step(self, identity):
        from ontokin.construction import ConstructionBudget
        from ontokin.json_limits import measure_json
        from ontokin import program_runtime

        constructors, materializations, prepared, guards = [], [], [], []
        real_init = ConstructionBudget.__init__
        real_data, real_json = program_runtime._Budget.data, program_runtime._Budget.json
        execute, guard = self.service._execute, self.service._check_task_response

        def init(budget, *args, **kwargs):
            real_init(budget, *args, **kwargs)
            constructors.append(budget)

        def data(budget, value):
            result = real_data(budget, value)
            materializations.append({"kind": "data", "entries": measure_json(result)["entries"]})
            return result

        def json_value(budget, value):
            result = real_json(budget, value)
            materializations.append({"kind": "json", "entries": measure_json(result)["entries"]})
            return result

        def completed(task, check):
            execute(task, check)
            prepared.append(task.response["status"])

        def checked(task):
            guards.append({"status": task.response["status"], "phase": (task.response.get("progress") or {}).get("phase"),
                           "entries": measure_json(task.response)["entries"]})
            guard(task)

        with patch.object(ConstructionBudget, "__init__", init), \
                patch.object(program_runtime._Budget, "data", data), \
                patch.object(program_runtime._Budget, "json", json_value), \
                patch.object(self.service, "_execute", completed), \
                patch.object(self.service, "_check_task_response", checked):
            response = self.step(identity)
        return response, {"constructor_cumulative_entries": [budget.value_entries for budget in constructors],
                          "materialization_entry_counts": materializations,
                          "prepared_statuses": prepared, "complete_response_guards": guards}

    def run_lp04(self):
        from ontokin.json_limits import measure_json

        project = "reach-reconstruction-lp04"
        self.step("LP04.01")
        evaluated = self.step("LP04.02")
        retained = self.retained_run(project, evaluated["run_id"])
        measurements = {}
        for identity in ("LP04.03", "LP04.04", "LP04.05"):
            response, measurements[identity] = self.measured_q03_step(identity)
            if identity != "LP04.05":
                require(len(reach_records(response)) == 128 and response["result"]["total"] == 128
                        and not response["truncated"] and response["next_cursor"] is None,
                        "Q03 must return all 128 complete action groups")
            else:
                require(response["result"] is None and response["run_id"] is None
                        and response["protocol_error"]["details"]["effects_committed"] is False,
                        "Q03 final-response failure committed effects")
        n = self.bindings["LP04.N"]
        require(measure_json(self.responses["LP04.04"])["entries"] == n, "The exact N query changed size")
        query_fields = ("program_revision", "run_id", "selector", "fields", "limit", "time")
        for identity, measured in measurements.items():
            require(measured["prepared_statuses"] == ["succeeded"], "Q03 failed before complete preparation")
            require(measured["constructor_cumulative_entries"]
                    and all(0 < count < n for count in measured["constructor_cumulative_entries"]),
                    "Q03 exhausted an earlier construction entry budget")
            require(measured["materialization_entry_counts"]
                    and all(item["entries"] < n for item in measured["materialization_entry_counts"]),
                    "Q03 exhausted an earlier materialization entry budget")
            require({field: self.requests[identity][field] for field in query_fields}
                    == {field: self.requests["LP04.03"][field] for field in query_fields}, "Q03 changed the fixed query")
        require({"status": "succeeded", "phase": "complete", "entries": n}
                in measurements["LP04.05"]["complete_response_guards"], "Q03 N-1 did not reach final publication")
        tiny = self.step("LP04.06")
        codes = [item["code"] for item in tiny["diagnostics"]]
        if tiny["protocol_error"]:
            codes.append(tiny["protocol_error"]["code"])
        require(bool({"OKL-E-RESOURCE", "OKA-E-RESOURCE"} & set(codes)), "Tiny budget did not fail by its real resource guard")
        self.step("LP04.07")
        require(self.effects(project)["runs"] == 1 and self.effects(project)["artifacts"] == 0,
                "Q03 inspection mutated runs or artifacts")
        return {"measurements": self.write("q03-measurements.json", {"complete_response_entries": n,
                    "requests": measurements, "instrumentation": "transparent observers; all original constructors, "
                    "materializers, execution and final guards called unchanged"}),
                "retained_run": self.require_retained("LP04-P24", project, evaluated["run_id"], retained)}

    def run_lp05(self):
        project = "reach-reconstruction-lp05"
        self.step("LP05.01")
        candidate = self.step("LP05.02")
        run_id = candidate["run_id"]
        retained = self.retained_run(project, run_id)
        require(retained[0]["candidate_only"], "Candidate run was prematurely accepted")
        unrun = projection(self.step("LP05.03"))
        require(unrun["candidate_only"] and unrun["current"] == {
            "available": False, "reason": "run_required", "value": None}, "LP05 fabricated an unsampled state")
        before = projection(self.step("LP05.04"))
        require(before["candidate_only"] and before["current"]["value"]["lifecycle"] == "pending",
                "LP05 lost candidate before-zero state")
        for identity in ("LP05.05", "LP05.06", "LP05.07"):
            self.step(identity)
        require(self.effects(project)["artifacts"] == 0, "Never-accepted candidate exported an artifact")
        accepted = self.step("LP05.08")
        now = projection(self.step("LP05.09"))
        require(now["program_revision"] == self.bundle("N06").program_revision
                and now["accepted_program_revision"] == accepted["program_revision"] and not now["candidate_only"]
                and self.service.get_run(project, run_id)["candidate_only"], "Candidate history/current context was relabeled")
        self.step("LP05.10")
        stale = self.step("LP05.11")
        require(stale["result"]["run_state"] == retained[0], "Stale operation changed the historical candidate run")
        reset = self.step("LP05.12")
        require(reset["run_id"] != run_id and not reset["result"]["run_state"]["candidate_only"],
                "Constructed acceptance did not produce a fresh reset context")
        self.exchange("LP05/candidate-retry", self.requests["LP05.02"], expected="rejected", code="OKL-E-REACH")
        require(self.responses["LP05/candidate-retry"] == candidate, "Candidate retry changed its terminal response")
        self.retain_source("LP05-N06", project, self.bundle("N06"))
        return {"retained_candidate": self.require_retained("LP05-candidate", project, run_id, retained),
                "fresh_reset_run": reset["run_id"]}

    def run_q22(self):
        require("L04" in self.contexts, "Q22 requires the completed original LP01 workflow")
        context = self.contexts["L04"]
        project, old, new = context["project"], context["program"], self.bundle("L02")
        probe = self.release_probes["Q22-same-project-repair-and-stale-history"]
        request = self.resolve(probe["edit_request_template"])
        failed_run, retained = self.bindings["LP01.failed_run"], context["failed_snapshot"]
        require(project == request["project_id"] and context["failed_run"] == failed_run
                and request["expected_program_revision"] == old.program_revision
                and self.service.accepted_revision(project) == old.program_revision,
                "Q22 must repair the original accepted LP01 L04 and retain its failed run")
        authority = self.send("Q22/authority", project, "inspect", program_revision=old.program_revision,
                              selector={"path": "reach_b"}, fields=["identity", "source", "actions"], limit=1)
        item = authority["result"]["items"][0]
        require(item["element_id"] == ["planar-reach-lifecycle", "demo", "reach-b"],
                "Q22 did not inspect the exact action occurrence")
        require(len(request["patches"]) == 1, "Q22 requires its exact one-expression patch")
        change = request["patches"][0]
        raw = old.entry.raw
        require(change["element_id"] == item["element_id"] and change["source_id"] == "entry"
                and change["source_revision"] == old.entry.revision
                and raw[change["start_byte"]:change["end_byte"]].decode("utf-8") == change["expected_text"]
                and raw[:change["start_byte"]] + change["replacement"].encode("utf-8")
                    + raw[change["end_byte"]:] == new.entry.raw,
                "The frozen Q22 expression patch must produce the exact complete L02 entry")
        require(any(span["source_id"] == change["source_id"]
                    and span["start_byte"] <= change["start_byte"] <= change["end_byte"] <= span["end_byte"]
                    for span in item["source"]["writable_spans"]), "Q22 patch exceeds actual inspected authority")
        require({key: unit.raw for key, unit in old.sources.items() if key != "entry"}
                == {key: unit.raw for key, unit in new.sources.items() if key != "entry"},
                "Q22 expected repair changed a frozen library")
        before = self.effects(project)
        edited = self.exchange("Q22.01", request, expected=probe["expected_edit"]["status"])
        require(edited["program_revision"] == edited["accepted_program_revision"] == new.program_revision,
                "Q22 did not produce the exact L02 program in the same project")
        require(type(edited["run_id"]) is str and edited["run_id"] not in (failed_run, context["prior_run"])
                and edited["result"]["run_state"]["status"] == "ready"
                and self.effects(project) == {"runs": before["runs"] + 1, "artifacts": before["artifacts"],
                                              "accepted_program_revision": new.program_revision},
                "Q22 must retain exactly one fresh successful edit run without an artifact")
        mismatch = self.exchange("Q22.02", self.resolve(probe["mismatch_request_template"]),
                                 expected=probe["expected_mismatch"]["status"],
                                 code=probe["expected_mismatch"]["diagnostic_code"])
        require(probe["expected_mismatch"]["category"] in [item["category"] for item in mismatch["diagnostics"]],
                "Q22 mismatch must reject the stale run context")
        control = self.exchange("Q22.03", self.resolve(probe["historical_control_request_template"]),
                                expected=probe["expected_historical_control"]["status"])
        require(control["program_revision"] == old.program_revision
                and control["accepted_program_revision"] == new.program_revision and control["run_id"] == failed_run,
                "Q22 historical control lost the old source/run or the current accepted head")
        previous = {tuple(record["element_id"]): record for record in reach_records(self.responses["LP01.03"])}
        historical = {tuple(record["element_id"]): record for record in reach_records(control)}
        require(previous.keys() == historical.keys() and previous, "Q22 historical control omitted old reach actions")
        for identity, record in historical.items():
            require(record["accepted_program_revision"] == new.program_revision
                    and {key: value for key, value in record.items() if key != "accepted_program_revision"}
                        == {key: value for key, value in previous[identity].items() if key != "accepted_program_revision"},
                    "Q22 historical control changed the retained failed-boundary sample")
        effects = self.effects(project)
        require(self.exchange("Q22/retry", request) == edited, "Q22 edit retry changed")
        status = self.send("Q22/status", project, "status", target_request_id=request["request_id"])
        require(status["result"]["target"] == edited and self.effects(project) == effects,
                "Q22 status/retry changed the retained edit or effects")
        self.retain_source("Q22-original-L04", project, old)
        source = self.retain_source("Q22-repaired-L02", project, new)
        self.contexts["L02"] = {"project": project, "program": new, "source_snapshot": source,
                               "prior_run": edited["run_id"],
                               "protocol_roles": [*context["protocol_roles"], "Q22/authority", "Q22.01",
                                                  "Q22.02", "Q22.03", "Q22/retry", "Q22/status"]}
        return {"project_id": project, "old_program_revision": old.program_revision,
                "program_revision": new.program_revision, "old_run_id": failed_run,
                "new_run_id": edited["run_id"], "patch": change, "release_probe_id": probe["id"],
                "edit_role": "Q22.01", "mismatch_role": "Q22.02", "historical_control_role": "Q22.03",
                "retained_failure": self.require_retained("Q22-old-failure", project, failed_run, retained)}

    def prepare_delivery(self, case_id, options):
        if case_id in ("P13", "P20", "L04", "L02"):
            require(case_id in self.contexts, case_id + " requires its actual prior repair/reset workflow")
            return self.contexts[case_id]
        project, program = "reach-delivery-case-" + case_id.lower(), self.bundle(case_id)
        self.send(case_id + "/create", project, "create", bundle=program.to_payload(),
                  expected_program_revision=None, requested_level="constructed")
        evaluated = self.send(case_id + "/evaluate", project, "evaluate", program_revision=program.program_revision,
                              run_id=None, until_seconds=options["end"])
        source = self.retain_source(case_id, project, program)
        self.contexts[case_id] = {"project": project, "program": program, "source_snapshot": source,
                                  "prior_run": evaluated["run_id"],
                                  "protocol_roles": [case_id + "/create", case_id + "/evaluate"]}
        return self.contexts[case_id]

    def retrieve(self, role_prefix, project, response):
        result = response["result"]
        require(type(result["total_bytes"]) is int and 0 < result["total_bytes"] <= MAX_BYTES,
                "The actual artifact exceeds this recorder's declared byte limit")
        roles, chunks, offset = [], [], 0
        expected_provenance = {
            "exporter": result["report"]["exporter"],
            "source_code_sha256": "sha256:" + result["report"]["source_code_sha256"],
            "program_revision": result["program_revision"]}
        while offset < result["total_bytes"]:
            require(len(roles) < MAX_BYTES // CHUNK_BYTES, "The artifact exceeded the bounded chunk count")
            role = f"{role_prefix}/{len(roles):04d}"
            reply = self.send(role, project, "artifact", artifact_id=result["artifact_id"],
                              offset=offset, max_bytes=CHUNK_BYTES)
            part = reply["result"]
            raw = base64.b64decode(part["data_base64"], validate=True)
            require(0 < len(raw) <= CHUNK_BYTES and part["offset"] == offset
                    and part["total_bytes"] == result["total_bytes"] and part["sha256"] == result["sha256"],
                    "An actual artifact chunk has a conflicting offset, length or hash")
            require(part["artifact_provenance"] == expected_provenance, "Artifact chunk provenance changed")
            require(offset + len(raw) <= result["total_bytes"], "Artifact chunk exceeds the declared file")
            chunks.append(raw)
            roles.append(role)
            offset += len(raw)
            require(part["next_offset"] == (offset if offset < result["total_bytes"] else None),
                    "Artifact retrieval omitted or overlapped a byte interval")
        raw = b"".join(chunks)
        require(len(raw) == result["total_bytes"] and sha(raw) == result["sha256"],
                "Retrieved bytes differ from the actual export receipt")
        return raw, {"project_id": project, "run_id": response["run_id"], "artifact_id": result["artifact_id"],
                     "sha256": result["sha256"], "bytes": len(raw), "chunk_bytes": CHUNK_BYTES,
                     "chunk_roles": roles, "provenance": expected_provenance,
                     "complete_contiguous_retrieval": True}

    def deliver(self, case_id, fps):
        options = settings(case_id, fps=fps)
        row = {"case_id": case_id, "status": "running", "source_files": source_files(case_id),
               "program_revision": self.frozen[case_id]["program_revision"], "options": options,
               "started_at": utc(), "request_budget": {"max_operations": 100000, "source": "unchanged inherited default"}}
        self.report["deliveries"].append(row)
        started = time.monotonic()
        try:
            context = self.prepare_delivery(case_id, options)
            project, program = context["project"], context["program"]
            row.update(project_id=project, source_manifest=descriptor(ROOT / source_files(case_id), relative_to=ROOT),
                       prior_workflow_roles=context["protocol_roles"], prior_run_id=context["prior_run"])
            prior = self.retained_run(project, context["prior_run"])
            if case_id == "L04":
                request = self.resolve(self.release_probes["L04-tenth-agent-artifact"]["request_template"])
                require(request["project_id"] == project and request["program_revision"] == program.program_revision
                        and request["options"]["end"] == options["end"]
                        and self.service.accepted_revision(project) == program.program_revision,
                        "L04 recovery must use unchanged accepted LP01 source before the Q22 repair")
                request["options"] = options
            else:
                request = self.request(project, "export", program_revision=program.program_revision,
                                       destination=TARGET, options=options)
            response = self.exchange(case_id + "/export", request)
            result = response["result"]
            require(response["achieved_level"] == "delivered" and result["destination"] == TARGET,
                    "The actual export did not achieve the explicit delivered level")
            require(result["program_revision"] == program.program_revision
                    and result["report"]["program_revision"] == program.program_revision,
                    "Export receipt identifies another source revision")
            require(result["report"]["validation"]["status"] == "passed", "Exporter supplied-byte validation did not pass")
            run = result["run_state"]
            require(run["valid_until_side"] == "after"
                    and Fraction(run["valid_until_seconds"]) == Fraction(options["end"])
                    and Fraction(result["report"]["sampling"]["end_seconds"]) == Fraction(options["end"]),
                    "Delivery did not stop at its exact requested endpoint")
            require(response["run_id"] != context["prior_run"]
                    and self.service.get_run(project, response["run_id"]) == run,
                    "Delivery did not retain a fresh run matching its receipt")
            self.require_retained(case_id + "-prior-to-delivery", project, context["prior_run"], prior)
            if case_id == "L04":
                require(response["run_id"] != context["failed_run"], "L04 artifact reused the failed run")
                self.require_retained("L04-post-delivery-failed", project, context["failed_run"], context["failed_snapshot"])
                require(self.retained_run(project, context["prior_run"]) == context["prefix_snapshot"],
                        "L04 artifact mutated the reset/prefix run")
                row.update(recovery_failed_run_id=context["failed_run"],
                           recovery_reset_prefix_run_id=context["prior_run"], separate_tenth_recovery_artifact=True)
            raw, retrieval = self.retrieve(case_id + "/artifact", project, response)
            directory = self.output / "cases" / case_id
            directory.mkdir(parents=True)
            with (directory / "scene.glb").open("xb") as stream:
                stream.write(raw)
            retrieval_file = self.write(f"cases/{case_id}/retrieval.json", retrieval)
            export_file = self.write(f"cases/{case_id}/export-report.json", result["report"])
            require(self.service.read_program(project, program.program_revision).to_payload() == program.to_payload(),
                    "Delivered source snapshot changed")
            row.update(status="passed", run_id=response["run_id"], artifact_id=result["artifact_id"],
                       artifact=descriptor(directory / "scene.glb", relative_to=self.output),
                       export_role=case_id + "/export", retrieval=retrieval_file, export_report=export_file,
                       source_snapshot=context["source_snapshot"], accepted_program_revision=response["accepted_program_revision"])
        except Exception as error:
            row.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                       traceback=traceback.format_exc())
        finally:
            row.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started)
            row["request_result"] = self.write(f"delivery-results/{case_id}.json", row)
            print(f"Agent {case_id}: {row['status']}", flush=True)
        return row

    def run_delivery_failures(self):
        p01 = next(row for row in self.report["deliveries"] if row["case_id"] == "P01")
        require(p01["status"] == "passed", "Delivery failure retention requires the actual P01 artifact")
        project = p01["project_id"]
        request, delivered = self.requests["P01/export"], self.responses["P01/export"]
        before = self.effects(project)
        retained = self.retained_run(project, delivered["run_id"])
        require(self.exchange("delivery/exact-retry", request) == delivered, "Export retry changed its actual receipt")
        collision = copy.deepcopy(request)
        collision["options"]["fps"] = request["options"]["fps"] + 1
        self.exchange("delivery/changed-request-id", collision, expected="rejected", code="OKL-E-REQUEST-ID")
        status = self.send("delivery/status", project, "status", target_request_id=request["request_id"])
        require(status["result"]["target"] == delivered, "Status did not reconcile the immutable export")
        self.send("delivery/foreign-artifact", "reach-delivery-foreign", "artifact",
                  artifact_id=delivered["result"]["artifact_id"], max_bytes=64,
                  expected=("failed", "rejected"), code="OKA-E-ARTIFACT")
        self.send("delivery/invalid-offset", project, "artifact", artifact_id=delivered["result"]["artifact_id"],
                  offset=delivered["result"]["total_bytes"] + 1, max_bytes=64,
                  expected=("failed", "rejected"), code="OKA-E-ARTIFACT")
        self.send("delivery/generic-level", project, "validate", program_revision=p01["program_revision"],
                  requested_level="delivered", expected=("failed", "rejected"), code="OKL-E-CAPABILITY-UNSUPPORTED")
        require(self.effects(project) == before, "Delivery retry, status or invalid retrieval changed effects")
        failure_roles = []
        for case_id, endpoint, reach_code in (("P17", "4", "reach_unreachable"),
                                               ("L04", "2", "reach_unreachable")):
            require(case_id in self.contexts and self.responses.get(case_id + "/export", {}).get("status") == "succeeded",
                    case_id + " full failure requires its already retrieved valid prefix")
            context = self.contexts[case_id]
            project_id, program = context["project"], context["program"]
            effects = self.effects(project_id)
            options = {**settings(case_id), "end": endpoint}
            role = case_id + "/full-failure"
            reply = self.send(role, project_id, "export", program_revision=program.program_revision,
                              destination=TARGET, options=options, expected="rejected", code="OKL-E-REACH")
            require(reply["achieved_level"] != "delivered"
                    and reach_code in [item.get("details", {}).get("reach_code") for item in reply["diagnostics"]],
                    "Full prefix did not fail at its real reach boundary")
            run = reply["result"]["run_state"]
            expected_time = "3" if case_id == "P17" else "0.5"
            require((run["valid_until_seconds"], run["valid_until_side"]) == (expected_time, "before"),
                    "Full request lost the exact failed boundary")
            require(self.effects(project_id)["artifacts"] == effects["artifacts"],
                    "Failed full request committed an artifact")
            raw, retrieval = self.retrieve(case_id + "/retained-after-failure", project_id, self.responses[case_id + "/export"])
            original = next(item for item in self.report["deliveries"] if item["case_id"] == case_id)
            require(sha(raw) == original["artifact"]["sha256"] and len(raw) == original["artifact"]["bytes"],
                    "A valid prefix artifact changed after the later failure")
            self.write(f"cases/{case_id}/retrieval-after-failure.json", retrieval)
            failure_roles.append(role)
        n06 = self.bundle("N06")
        role = "N06/selected-branch-delivery-failure"
        n06_project = "reach-reconstruction-lp03"
        effects = self.effects(n06_project)
        failed = self.send(role, n06_project, "export", program_revision=n06.program_revision,
                           destination=TARGET, options={"end": "0.25", "fps": 1, "helpers": False},
                           expected="rejected", code="OKL-E-REACH")
        require("reach_limit" in [item.get("details", {}).get("reach_code") for item in failed["diagnostics"]]
                and self.effects(n06_project)["artifacts"] == effects["artifacts"],
                "N06 selected-branch failure was replaced by another failure or an artifact")
        self.require_retained("P01-after-delivery-failures", p01["project_id"], delivered["run_id"], retained)
        return {"retained_artifact": p01["artifact"], "full_prefix_failure_roles": failure_roles + [role],
                "exact_retry_and_status": True, "retrieval_scope_and_offset_rejections": True}

    def run_q02(self):
        from ontokin import reach_export

        prior = next(row for row in self.report["deliveries"] if row["case_id"] == "P01")
        require(prior["status"] == "passed", "Q02 requires the actual preexisting P01 artifact")
        prior_response = self.responses["P01/export"]
        prior_effects = self.effects(prior["project_id"])
        prior_run = self.retained_run(prior["project_id"], prior["run_id"])
        program, project = self.bundle("P23"), "reach-delivery-q02"
        self.send("Q02/create-P23", project, "create", bundle=program.to_payload(),
                  expected_program_revision=None, requested_level="constructed")
        before = self.effects(project)
        request = self.request(project, "export", program_revision=program.program_revision,
                               destination=TARGET, options={"end": "0.25", "fps": 1, "helpers": False})
        execution, observed = {}, []
        execute, stage = self.service._execute, reach_export.recording_stage

        def observe_execution(task, check):
            if task.request["request_id"] == request["request_id"]:
                execution["check"] = check
            return execute(task, check)

        def cancel_inside_plan(name, *, work=None, check=None):
            stage(name, work=work, check=check)
            if name != "planning_phase" or observed:
                return
            running = self.send("Q02/running-status", project, "status", target_request_id=request["request_id"])
            require(running["result"]["target_status"] == "running"
                    and self.service.accepted_revision(project) == program.program_revision
                    and work.counts.get("recording_boundary_preflight", 0) > 0,
                    "Q02 did not reach actual accepted bounded P23 planning")
            observed.append({"stage": name, "work_operations": work.operations, "work": work.record()})
            cancelled = self.send("Q02/cancel", project, "cancel", target_request_id=request["request_id"])
            require(cancelled["result"]["disposition"] == "cancellation_requested", "Q02 cancellation was not accepted")
            # Only the ordinary durable-flag poll is advanced. The next real
            # cooperative checkpoint supplies the cancellation exception.
            execution["check"].last_poll = 0

        with patch.object(self.service, "_execute", observe_execution), \
                patch.object(reach_export, "recording_stage", cancel_inside_plan):
            response = self.exchange("Q02/export", request, expected="cancelled")
        require(len(observed) == 1 and observed[0]["work_operations"] > 0
                and response["run_id"] is None and response["result"] is None, "Q02 exposed interrupted delivery state")
        status = self.send("Q02/terminal-status", project, "status", target_request_id=request["request_id"])
        require(status["result"]["target"] == response
                and self.exchange("Q02/exact-retry", request, expected="cancelled") == response,
                "Q02 cancellation receipt was not immutable")
        require(self.effects(project) == before and self.effects(prior["project_id"]) == prior_effects,
                "Q02 cancellation changed source/run/artifact effects")
        self.retain_source("Q02-P23-after-cancel", project, program)
        self.require_retained("Q02-prior-P01-run", prior["project_id"], prior["run_id"], prior_run)
        raw, retrieval = self.retrieve("Q02/retained-P01-artifact", prior["project_id"], prior_response)
        require(sha(raw) == prior["artifact"]["sha256"] and len(raw) == prior["artifact"]["bytes"],
                "Q02 changed the complete prior artifact")
        return {"cancellation": self.write("q02-cancellation.json", {
                    "actual_source_case": "P23", "program_revision": program.program_revision,
                    "observations": observed, "prior_artifact_retrieval": retrieval,
                    "instrumentation": "stage and execute observers call original code; actual status/cancel "
                    "requests set the durable flag; next ordinary poll observes it"}),
                "prior_artifact": prior["artifact"]}

    def run_role(self, name, function):
        row = {"role": name, "status": "running", "started_at": utc(), "exchange_start": len(self.trace) + 1}
        self.report["workflow_roles"].append(row)
        started = time.monotonic()
        try:
            row["result"] = function()
            row["status"] = "passed"
        except Exception as error:
            row.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                       traceback=traceback.format_exc())
        finally:
            row.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started, exchange_end=len(self.trace))
            row["record"] = self.write(f"workflow-roles/{name}.json", row)
            print(f"Agent {name}: {row['status']}", flush=True)
        return row

    def run(self, cases, fps):
        self.run_role("discovery", lambda: self.send("discovery", "reach-delivery-discovery", "discover",
                                                     profile="planar-reach-0.1", limit=1000))
        for name in ("LP01", "LP02", "LP03", "LP04", "LP05"):
            self.run_role(name, getattr(self, "run_" + name.lower()))
            if name == "LP01" and "L04" in cases:
                self.deliver("L04", fps)
        self.run_role("Q22", self.run_q22)
        for case_id in cases:
            if case_id != "L04":
                self.deliver(case_id, fps)
        if set(("P01", "P17", "L04")) <= set(cases):
            self.run_role("delivery-failures", self.run_delivery_failures)
        if "P01" in cases:
            self.run_role("Q02", self.run_q02)
        self.report["executed_frozen_protocol_steps"] = [identity for identity in self.steps if identity in self.responses]
        self.report["frozen_protocol_step_count"] = 42
        self.report["exchange_count"] = len(self.trace)
        self.report["protocol_bindings"] = self.write("protocol-bindings.json", self.bindings)
        self.report["status"] = ("passed" if all(row["status"] == "passed" for row in
            (*self.report["workflow_roles"], *self.report["deliveries"])) else "failed")
        self.report["complete_agent_delivery_corpus"] = (self.report["status"] == "passed"
            and tuple(cases) == AGENT_CASES and len(self.report["executed_frozen_protocol_steps"]) == 42)


def build(output, cases, fps):
    output = fresh_output(output)
    report = {"schema_version": SCHEMA, "status": "running", "source_kind": "agent_retrieved_artifact",
              "provider": "local", "protocol": PROTOCOL, "target_contract": TARGET,
              "started_at": utc(), "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
              "working_directory": str(ROOT), "execution": {"python": sys.version, "executable": sys.executable,
                                                            "platform": platform.platform()},
              "required_cases": list(AGENT_CASES), "selected_cases": list(cases),
              "deliveries": [], "exchanges": [], "snapshots": [], "workflow_roles": [],
              "complete_agent_delivery_corpus": False, "release_acceptance": False,
              "agent_transport_audited": False, "native_validation": "pending", "browser_validation": "pending",
              "full_product_goal_completed": False,
              "limits": ["This producer records actual finite Agent operations and exact retrieved bytes.",
                         "Independent transport, source/reference/rate, native/browser, compatibility, inherited "
                         "and complete R01-R12/Q01-Q22 audits remain separate mandatory roles.",
                         "Recorded playback does not supply live destination actions or physics."]}
    before = recorder = None
    try:
        before = snapshot()
        write_json(output / "inputs-before.json", before)
        report.update(source_commit=before["git"]["commit"], source_tree=before["git"]["tree"])
        recorder = Recorder(output, report)
        recorder.run(cases, fps)
    except Exception as error:
        report.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                      traceback=traceback.format_exc())
    finally:
        if recorder is not None:
            recorder.service.close()
        finish_inputs(output, before, report)
        if report["status"] != "passed":
            report["complete_agent_delivery_corpus"] = False
        report["finished_at"] = utc()
        write_json(output / "producer-record.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--fps", type=float, default=1)
    arguments = parser.parse_args(argv)
    require(0 < arguments.fps <= 10000, "Requested fps must be finite, positive and at most 10000")
    report = build(arguments.output_dir, selected_cases("agent_retrieved_artifact", arguments.case), arguments.fps)
    print(json.dumps({key: report[key] for key in ("schema_version", "status", "complete_agent_delivery_corpus")}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
