#!/usr/bin/env python3
"""Independent C088 request, state, immutable SQLite and ledger reader.

No OntoKin module is imported. Original frozen source bytes supply identities,
values, dependencies and source roles. SQLite is opened immutable and read-only
only after verifying the closed snapshot's complete bytes. The entire evidence
tree is inventoried before and after reading, including live-store auxiliaries.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
from pathlib import Path
import sqlite3

from keyed_membership_evidence import (
    Freeze, MEMBERSHIP_STAGES, PROFILE, PROTOCOL, TARGET, canonical, inventory,
    read, save, sha, stamp, standalone_bundle_identity,
)
from verify_keyed_membership_observations import Reader, original_origin
from keyed_membership_amendment import AgentAmendment


FAMILIES = ("transforms", "reductions", "filters", "merges", "zips", "rekeys")


def frozen_payload(root, files):
    descriptor = read(Path(root) / files)
    def unit(item):
        return {key: value for key, value in item.items() if key != "path"} | {
            "source": (Path(root) / item["path"]).read_bytes().decode("utf-8")}
    return {"schema_version": "ontokin.bundle/0.2", "entry": unit(descriptor["entry"]),
            "modules": sorted([unit(item) for item in descriptor["modules"]],
                              key=lambda u: (u["package_id"], u["version"])),
            "assets": sorted([{key: value for key, value in item.items() if key != "path"} | {
                "data_base64": base64.b64encode((Path(root) / item["path"]).read_bytes()).decode()}
                for item in descriptor["assets"]], key=lambda u: u["asset_id"])}


def payload_identity(payload):
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": payload["entry"]["filename"],
              "source_revision": "sha256:" + sha(payload["entry"]["source"].encode())}]
    for item in payload["modules"]:
        units.append({"source_id": "package:" + item["package_id"] + "@" + item["version"],
            "package_id": item["package_id"], "version": item["version"], "filename": item["filename"],
            "source_revision": "sha256:" + sha(item["source"].encode())})
    assets = []
    for item in payload["assets"]:
        raw = base64.b64decode(item["data_base64"], validate=True)
        if "sha256:" + sha(raw) != item["sha256"]:
            raise ValueError("Stored asset bytes do not match their own immutable pin")
        assets.append({key: item[key] for key in ("asset_id", "media_type", "sha256")} | {"byte_length": len(raw)})
    manifest = {"schema_version": "ontokin.bundle/0.2", "entry_source_id": "entry",
                "units": sorted(units, key=lambda x: x["source_id"]),
                "assets": sorted(assets, key=lambda x: x["asset_id"])}
    return manifest, "sha256:" + sha(b"ontokin.bundle/0.2\0" + canonical(manifest))


def diagnostic_codes(response):
    result = [d.get("code") for d in response.get("diagnostics", [])]
    if response.get("protocol_error"):
        result.append(response["protocol_error"].get("code"))
    return result


def public_origin(raw, wanted):
    actual = original_origin(raw, wanted)
    result = {}
    renames = {"input_type": "input_element_type", "output_type": "output_element_type",
               "left_type": "left_element_type", "right_type": "right_element_type"}
    for key, value in actual.items():
        if wanted["family"] == "transforms" and key in ("key", "input_entry") and value is None:
            continue
        if isinstance(value, dict) and "start_byte" in value:
            value = value | {"source_revision": "sha256:" + sha(raw), "filename": "main.ok"}
        elif isinstance(value, dict) and "kind" in value:
            if value["kind"] == "Quantity" and value["dimension"] == [1, 0, 0, 0]:
                value = "Length"
            else:
                value = value["kind"]
        result[renames.get(key, key)] = value
    return result


class AgentReader:
    def __init__(self, reader, root, checkout=None, amendment=None):
        self.r, self.root, self.freeze = reader, Path(root), reader.freeze
        self.amendment = amendment
        self.summary = read(self.root / "summary.json")
        self.contract = amendment.contract if amendment is not None else read(self.freeze.root / "agent/request-workflows.json")
        self.transcript = read(self.root / "agent/transcript.json")
        self.ledgers = read(self.root / "agent/ledger-observations.json")
        self.rows = {row["workflow"] + "." + row["step"]: row for row in self.transcript}
        self.responses = {key: row.get("response") for key, row in self.rows.items()}
        self.payloads, self.expected, self.source_cases = {}, {}, {}
        for case in self.freeze.source["cases"]:
            payload = frozen_payload(self.freeze.root, case["files"])
            self.payloads[case["program_revision"]] = payload
            self.expected[case["program_revision"]] = case
            self.source_cases[case["id"]] = case
        for case in self.freeze.representative["cases"]:
            if case["mode"] != "source":
                continue
            payload = frozen_payload(self.freeze.root / "agent", case["files"])
            self.payloads[case["program_revision"]] = payload
            self.expected[case["program_revision"]] = case
        self.provenance = {case["case_id"]: case for case in self.freeze.provenance["cases"]}
        self.final_states, self.receipts = {}, {}
        self.schemas = None
        if checkout is not None:
            from jsonschema import Draft202012Validator
            from referencing import Registry, Resource
            resources = {}
            fixed_files = {row["path"]: row for row in read(self.root / "source-before.json")["tracked_files"]}
            for path in (Path(checkout) / "docs/language-design").rglob("*.schema.json"):
                relative = path.relative_to(checkout).as_posix()
                if relative not in fixed_files or sha(path.read_bytes()) != fixed_files[relative]["sha256"]:
                    raise ValueError("Independent schema bytes differ from the producer's fixed source cut: " + relative)
                content = read(path)
                if "$id" in content:
                    resources[content["$id"]] = Resource.from_contents(content)
            registry = Registry().with_resources(resources.items())
            self.schemas = {kind: Draft202012Validator(read(Path(checkout) /
                f"docs/language-design/agent-v0.21/{kind}.schema.json"), registry=registry)
                for kind in ("request", "response")}

    def resolve(self, template, loop=None):
        if isinstance(template, dict):
            if set(template) == {"$bundle_file"}:
                return frozen_payload(self.freeze.root / "agent", template["$bundle_file"])
            if set(template) == {"$response"}:
                parts = template["$response"].split(".")
                value = self.responses[".".join(parts[:2])]
                for part in parts[2:]:
                    value = value[int(part)] if isinstance(value, list) else value[part]
                return copy.deepcopy(value)
            if set(template) == {"$capture"}:
                if template["$capture"] != "A07.prepared.artifact_id":
                    raise ValueError("Unknown exact frozen capture reference")
                return self.summary["publication_interruptions"][0]["prepared_only"][0]["artifact_id"]
            if set(template) == {"$loop"}:
                return loop[template["$loop"]]
            return {key: self.resolve(value, loop) for key, value in template.items()}
        if isinstance(template, list):
            return [self.resolve(value, loop) for value in template]
        if isinstance(template, str) and loop is not None:
            return template.replace("${index}", str(loop["index"]))
        return template

    def step(self, scenario, spec):
        if spec.get("action") == "close_and_reopen_same_store":
            return
        key = scenario + "." + spec["step"]
        self.r.case = key
        self.r.require(key in self.rows, "frozen concrete workflow step exists")
        if key not in self.rows:
            return
        row = self.rows[key]
        request = (copy.deepcopy(self.rows[spec["request_ref"]]["request"]) if "request_ref" in spec
                   else self.resolve(spec["request"]))
        request.update(spec.get("override", {}))
        self.r.equal(row["request"], request, "exact frozen request and original response/capture references")
        response = row.get("response", {})
        if "expected_status" in spec:
            self.r.equal(response.get("status"), spec["expected_status"], "frozen public status")
        if "expected_code" in spec:
            self.r.require(spec["expected_code"] in diagnostic_codes(response), "frozen public diagnostic", diagnostic_codes(response), spec["expected_code"])
        if "expected_budget_reason" in spec:
            self.r.require(any(d.get("details", {}).get("budget_reason") == spec["expected_budget_reason"]
                for d in response.get("diagnostics", [])), "frozen authority reason")
        if "expect_exact_response_ref" in spec:
            self.r.equal(response, self.responses[spec["expect_exact_response_ref"]], "exact immutable same-ID response replay")
        if "expected_next_cursor_equals" in spec:
            self.r.equal(response.get("next_cursor"), self.resolve(spec["expected_next_cursor_equals"]), "original first-page cursor survives reopen byte for byte")

    def verify_summary(self):
        r, s = self.r, self.summary
        r.case = "agent-summary"
        r.equal(s.get("schema_version"), "ontokin.c088-agent-observations/1", "producer schema")
        r.equal(s.get("status"), "passed", "complete original producer")
        r.equal(s.get("failures"), [], "no producer failures")
        r.equal(s.get("source_unchanged"), True, "fixed source unchanged")
        r.equal(s.get("frozen_inputs_unchanged"), True, "frozen answers unchanged")
        r.equal(read(self.root / "source-before.json"), read(self.root / "source-after.json"), "complete fixed source before/after")
        inputs = read(self.root / "inputs-before.json")
        r.equal(inputs, read(self.root / "inputs-after.json"), "complete frozen bytes before/after")
        manifest_sha = (self.amendment.lineage()["effective_input_manifest_sha256"] if self.amendment is not None else self.freeze.lineage()["input_manifest_sha256"])
        files = self.amendment.files if self.amendment is not None else self.freeze.before
        r.equal(inputs.get("manifest_sha256"), manifest_sha, "adopted exact effective Agent manifest")
        r.equal(inputs.get("files"), files, "independent full effective Agent inventory")
        r.equal([w["id"] for w in s["workflows"]], [w["id"] for w in self.contract["scenarios"]], "all eleven workflows")
        r.require(all(w["status"] == "observed_as_expected" for w in s["workflows"]), "every workflow completed")
        r.equal(s.get("operation_inventory"), sorted(self.contract["required_operations"]), "all twelve operation names")
        r.equal(sorted({row["request"]["operation"] for row in self.transcript}), sorted(self.contract["required_operations"]), "actual twelve-operation transcript")
        r.equal(len(self.rows), len(self.transcript), "unique workflow step labels")
        for scenario in self.contract["scenarios"]:
            for step in scenario.get("steps", []):
                self.step(scenario["id"], step)
            for step in scenario.get("then", []):
                self.step(scenario["id"], step)
        for reopened in s["reopens"]:
            r.case = "reopen/" + reopened["workflow"]
            r.require(reopened["old_owner"] != reopened["new_owner"], "new service session after real close")
        reopens = {workflow: sum(row["workflow"] == workflow for row in s["reopens"]) for workflow in {row["workflow"] for row in s["reopens"]}}
        warm = next(scenario for scenario in self.contract["scenarios"] if scenario["id"] == "A11")
        r.equal(reopens, {"A03": 1, "A04": 1, "A07": 1, "A08": 1, "A11": len(warm["fresh_projects_from_source_cases"])}, "exact required real reopen inventory")
        warm_requests = []
        for index, name in enumerate(warm["fresh_projects_from_source_cases"]):
            case = self.source_cases[name]
            project = f"c088-a11-{index}"
            def request(suffix, operation, **fields):
                return {"schema_version": PROTOCOL, "project_id": project, "request_id": project + "-" + suffix,
                        "operation": operation, **fields}
            warm_requests.append(request("create", "create", bundle=frozen_payload(self.freeze.root, case["files"]), expected_program_revision=None, requested_level="constructed"))
            for suffix in ("inspect-1", "inspect-2"):
                warm_requests.append(request(suffix, "inspect", program_revision=case["program_revision"], selector={"path": "probe"}, fields=["identity", "source", "values"], limit=1))
            warm_requests.append(request("validate-1", "validate", program_revision=case["program_revision"], requested_level="represented"))
            warm_requests.append(request("inspect-reopened", "inspect", program_revision=case["program_revision"], selector={"path": "probe"}, fields=["identity", "source", "values"], limit=1))
            warm_requests.append(request("validate-reopened", "validate", program_revision=case["program_revision"], requested_level="represented"))
        r.equal([row["request"] for row in self.transcript if row["workflow"] == "A11"], warm_requests, "complete exact nineteen-case fresh/warm/reopened request cohort")

    def verify_transcript(self):
        r = self.r
        seen_requests = set()
        for index, row in enumerate(self.transcript, 1):
            r.case = row["workflow"] + "." + row["step"]
            r.equal(row["sequence"], index, "contiguous actual exchanges")
            r.equal(read(self.root / f"agent/exchange-{index:05}.json"), row, "retained individual exchange bytes")
            request = row["request"]
            for kind in ("request", "response"):
                if kind not in row:
                    r.require(row["workflow"] == "A07" and row["step"] == "export" and kind == "response", "only frozen publication sentinel escapes without response")
                    continue
                raw = (self.root / row[kind + "_file"]).read_bytes()
                r.equal(sha(raw), row[kind + "_sha256"], "retained original " + kind + " byte identity")
                r.equal(json.loads(raw), row[kind], "original " + kind + " decodes to transcript")
                r.equal(row[kind].get("schema_version"), PROTOCOL, "explicit .21 " + kind + " envelope")
                r.equal(row[kind + "_schema_errors"], [], "producer " + kind + " schema validation")
                if self.schemas:
                    r.equal([e.message for e in self.schemas[kind].iter_errors(row[kind])], [], "independent " + kind + " schema validation")
            project_key = row["workflow"], request["project_id"]
            before, after = row["state_before"], row["state_after"]
            if project_key in self.final_states:
                r.equal(before, self.final_states[project_key], "complete accepted state continuity across requests/reopen")
            else:
                r.equal(before["accepted_program_revision"], None, "fresh project initially unaccepted")
                r.equal(before["runs"], [], "fresh project run inventory")
                r.equal(before["artifacts"], [], "fresh project artifact inventory")
            response = row.get("response")
            success = response is not None and response["status"] == "succeeded"
            operation = request["operation"]
            request_key = row["workflow"], request["project_id"], request["request_id"]
            if request_key in seen_requests:
                r.equal(after, before, "same-ID retry never replays publication effects")
            seen_requests.add(request_key)
            if success and operation in ("create", "edit"):
                if operation == "create":
                    payload = request["bundle"]
                else:
                    payload = copy.deepcopy(self.payloads[request["expected_program_revision"]])
                    for patch in sorted(request["patches"], key=lambda x: x["start_byte"], reverse=True):
                        r.equal(patch["source_id"], "entry", "frozen edit owns entry bytes")
                        raw = payload["entry"]["source"].encode()
                        r.equal("sha256:" + sha(raw), patch["source_revision"], "exact original patch source")
                        r.equal(raw[patch["start_byte"]:patch["end_byte"]].decode(), patch["expected_text"], "exact original patch byte span")
                        payload["entry"]["source"] = (raw[:patch["start_byte"]] + patch["replacement"].encode() + raw[patch["end_byte"]:]).decode()
                manifest, revision = payload_identity(payload)
                r.require(revision in self.payloads, "accepted source is an independently frozen program")
                if revision in self.payloads:
                    r.equal(payload, self.payloads[revision], "complete accepted source/image payload")
                r.equal(after["accepted_program_revision"], revision, "independently computed new accepted head")
                r.equal(response.get("program_revision"), revision, "response new revision")
                r.equal(after["accepted_payload_sha256"], sha(canonical(payload)), "accepted payload complete identity")
                r.equal(after["runs"], before["runs"], "source edit preserves immutable old runs")
                r.equal(after["artifacts"], before["artifacts"], "source edit preserves immutable old artifacts")
            else:
                r.equal(after["accepted_program_revision"], before["accepted_program_revision"], "request cannot change accepted source")
                r.equal(after["accepted_payload_sha256"], before["accepted_payload_sha256"], "request preserves exact accepted payload")
                r.equal(after["assets"], before["assets"], "request preserves pinned image attachment")
            if not success or operation not in ("create", "edit", "evaluate", "reset", "export"):
                r.equal(after, before, "read/refusal/cancellation/retry has no accepted publication effects")
            if success and operation in ("evaluate", "reset"):
                r.equal(after["artifacts"], before["artifacts"], "run evaluation preserves complete old artifact inventory")
            if success and operation in ("evaluate", "reset", "export"):
                after_runs = {run["id"]: run for run in after["runs"]}
                for prior in before["runs"]:
                    if prior["id"] != request.get("run_id"):
                        r.equal(after_runs.get(prior["id"]), prior, "unselected old run remains byte-identical")
                after_artifacts = {artifact["id"]: artifact for artifact in after["artifacts"]}
                for prior in before["artifacts"]:
                    r.equal(after_artifacts.get(prior["id"]), prior, "old artifact remains byte-identical")
            if success:
                r.equal(response.get("accepted_program_revision"), after["accepted_program_revision"], "response accepted pointer equals durable state")
            if response:
                r.equal(response.get("request_id"), request["request_id"], "response request identity")
                r.equal(response.get("project_id"), request["project_id"], "response project identity")
                identity = row["workflow"], request["project_id"], request["request_id"]
                if identity not in self.receipts or self.receipts[identity]["status"] in ("queued", "running"):
                    self.receipts[identity] = response
                self.verify_response(row)
            self.final_states[project_key] = after

    def verify_response(self, row):
        r, request, response = self.r, row["request"], row["response"]
        if response["status"] != "succeeded":
            return
        operation, result = request["operation"], response.get("result") or {}
        revision = response.get("program_revision")
        case = self.expected.get(revision)
        if operation == "artifact":
            raw = base64.b64decode(result["data_base64"], validate=True)
            r.equal(result["offset"], request.get("offset", 0), "artifact exact requested offset")
            r.require(len(raw) <= request["max_bytes"], "artifact request byte bound")
            r.equal(result["artifact_id"], request["artifact_id"], "artifact identity is request identity")
            r.require(result["offset"] + len(raw) <= result["total_bytes"], "artifact slice within exact total")
        if operation == "inspect" and case is not None:
            items = result.get("items", [])
            for item in items:
                path = item.get("path")
                values = item.get("values", {})
                if "source" in item:
                    r.equal(item["source"].get("program_revision"), revision, "inspection source context")
                if case.get("mode") == "source":
                    if path in ("first", "sibling") and values:
                        for field, expectation in (("overrides", path + "_overrides"), ("override_flags", path + "_flags"), ("selected", path + "_selected")):
                            if field in values:
                                actual = {entry["key"]: entry["value"]["value"] for entry in values[field]["value"]}
                                r.equal(actual, case[expectation], "representative actual " + path + "." + field)
                        if "override_flags" in values:
                            paths = {d.get("path") for d in values["override_flags"]["dependencies"]}
                            r.require(path + ".overrides" in paths and path + ".dimensions" in paths, "true and false flags retain admitted operand dependencies")
                    if path in case["geometry"]:
                        r.equal(item["element_id"], case["geometry"][path]["element_id"], "surviving occurrence identity")
                        if "state" in item and item["state"].get("available"):
                            r.equal(item["state"]["position_m"], case["geometry"][path]["translation_samples_m"][-1], "old run immutable final position")
                elif path == "probe" and "observed" in values:
                    observed = values["observed"]
                    r.equal(observed.get("type"), "Bool", "public membership result type")
                    r.equal(observed.get("value"), case["expected"]["observed"], "fresh/warm/reopened frozen Bool")
                    r.equal(observed.get("status"), "resolved", "resolved public value")
                    if "expected_member_dependencies" in case:
                        actual = sorted(d["path"] for d in observed["dependencies"] if d["relationship"] == "effective_value_dependency")
                        r.equal(actual, sorted(case["expected_member_dependencies"]), "exact public true/false member dependencies")
                        for d in observed["dependencies"]:
                            if d["relationship"] == "effective_value_dependency":
                                r.equal(d["element_id"], ["membership-probe", "demo", "probe", d["path"].split(".")[-1]], "dependency nominal source identity")
                                r.equal(d["program_revision"], revision, "dependency current immutable revision")
                    if case["id"] in self.provenance:
                        raw = (self.freeze.root / case["source"]).read_bytes()
                        for family in FAMILIES:
                            wanted = [public_origin(raw, origin) for origin in self.provenance[case["id"]]["required_origins"] if origin["family"] == family]
                            r.equal(observed.get("derived_" + family, []), wanted, "exact public detached " + family + " with no fictitious payload selection")
        if operation in ("evaluate", "reset"):
            state = result.get("run_state", {})
            r.equal(state.get("program_revision"), revision, "run descriptor source revision")
            r.equal(state.get("valid_until_seconds"), "0" if operation == "reset" else request["until_seconds"], "exact retained run time")
            r.equal(state.get("valid_until_side"), "before" if operation == "reset" else "after", "exact retained run side")
        if operation == "export":
            r.equal(result.get("destination"), TARGET, "explicit .21 delivery target")
            r.equal(result.get("program_revision"), revision, "export immutable source revision")
            r.require(result.get("total_bytes", 0) > 0, "nonempty actual delivered artifact")

    def verify_ledgers(self):
        r = self.r
        r.case = "agent-ledgers"
        r.equal([x["index"] for x in self.ledgers], list(range(len(self.ledgers))), "ledger inventory indexes")
        r.equal(len({x["ledger_id"] for x in self.ledgers}), len(self.ledgers), "fresh actual retained ledger object per original request")
        rows_by_request = {}
        for row in self.transcript:
            rows_by_request.setdefault((row["workflow"], row["request"]["project_id"], row["request"]["request_id"]), []).append(row)
        for ledger in self.ledgers:
            key = ledger["workflow"], ledger["project_id"], ledger["request_id"]
            r.case = "ledger/" + "/".join(key)
            r.require(key in rows_by_request, "ledger belongs to actual protocol request")
            if key not in rows_by_request:
                continue
            row = rows_by_request[key][0]
            r.equal(ledger["started"], ledger["final_started"], "original clock start survives all stages")
            r.equal(ledger["original_clock_id"], ledger["final_clock_id"], "original request clock retained")
            r.equal(ledger["host_policy"], row["host_policy"], "actual current session authority")
            r.equal(ledger["caller_caps"], {key: value for key, value in row["request"].get("budgets", {}).items() if key in ("max_operations", "max_elapsed_ms")}, "actual caller cap subset")
            budget = ledger["execution_budget"]
            r.equal(budget["host_ceilings"], ledger["host_policy"], "report current host authority")
            r.equal(budget["caller_caps"], ledger["caller_caps"], "report current caller authority")
            if budget["effective"] is not None:
                source = budget["source_request"] or {}
                r.equal(budget["effective"], {key: min(source.get(key, budget["defaults"][key]), ledger["host_policy"][key], ledger["caller_caps"].get(key, ledger["host_policy"][key])) for key in budget["defaults"]}, "independently resolved current authority intersection")
            previous = -1
            calls, current = [], []
            for tick in ledger["ticks"]:
                r.require(tick["operations_before"] >= previous, "monotone actual request counter")
                previous = tick["operations_after"]
                if tick["stage"].startswith("keyed_membership_"):
                    r.equal(tick["amount"], 1, "one actual tick per membership stage")
                    r.equal(tick["string_bytes_before"], tick["string_bytes_after"], "membership cannot reserve String bytes")
                    if not tick.get("exception"):
                        r.equal(tick["operations_after"], tick["operations_before"] + 1, "original ledger increment")
                    if tick["stage"] == MEMBERSHIP_STAGES[0]:
                        if current:
                            calls.append(current)
                        current = []
                    current.append(tick)
                    if tick["stage"] == MEMBERSHIP_STAGES[-1]:
                        calls.append(current); current = []
            if current:
                calls.append(current)
            for call in calls:
                names = [t["stage"] for t in call]
                r.equal(names[0], MEMBERSHIP_STAGES[0], "call begins with actual admission")
                if not call[-1].get("exception"):
                    n, k = names.count(MEMBERSHIP_STAGES[1]), names.count(MEMBERSHIP_STAGES[3])
                    r.equal(names, [MEMBERSHIP_STAGES[0]] + [MEMBERSHIP_STAGES[1]] * n + [MEMBERSHIP_STAGES[2]] + [MEMBERSHIP_STAGES[3]] * k + [MEMBERSHIP_STAGES[4]], "actual Agent n+k+3 stage ordering")
                    r.require(0 <= k <= n <= 256, "bounded actual Agent comparison count")
                    r.equal(call[-1]["operations_after"] - call[0]["operations_before"], n + k + 3, "actual same-ledger membership debit")
            if ledger["workflow"] == "A11":
                revision = row["request"].get("program_revision")
                if revision is None and "bundle" in row["request"]:
                    revision = payload_identity(row["request"]["bundle"])[1]
                case = self.expected[revision]
                r.equal(len(calls), case.get("expected_dynamic_invocations", 1), "fresh/warm/reopened actual membership calls, genuine binding reuse only")
            elif row.get("response", {}).get("status") == "succeeded":
                request = row["request"]
                revision = row["response"].get("program_revision")
                case = self.expected.get(revision, {})
                compiles = request["operation"] in ("create", "edit", "validate", "evaluate", "reset", "export", "surface.mesh_page")
                if request["operation"] == "inspect":
                    compiles = request.get("selector", {}).get("element_id", [None])[0] != "assets"
                if case.get("mode") == "source" and case.get("status") == "passed" and compiles:
                    # Original catalog has three keys; each of two independent
                    # PanelGroup occurrences evaluates flags and selected widths.
                    # Thus 3 keys * 2 authored calls * 2 owners = 12 invocations.
                    r.equal(len(calls), 3 * 2 * 2, "representative fresh/warm/reopened request executes all twelve authored memberships")
            if ledger["workflow"] == "A08" and row["step"].startswith("denied-"):
                r.equal(ledger["host_policy"]["max_operations"], 50000, "reopened lower host policy")
                r.equal(budget["budget_reason"], "host_ceiling_exceeded", "immutable old source grants no reopened authority")
                r.equal(calls, [], "host refusal before dynamic membership")
        for row in self.transcript:
            request = row["request"]
            if row["workflow"] == "A11":
                matching = [x for x in self.ledgers if (x["workflow"], x["project_id"], x["request_id"]) == (row["workflow"], request["project_id"], request["request_id"])]
                r.case = row["workflow"] + "." + row["step"]
                r.equal(len(matching), 1, "every fresh A11 request owns one observed current ledger")

    def verify_interruptions(self):
        r = self.r
        scenario = next(s for s in self.contract["scenarios"] if s["id"] == "A05")
        r.case = "agent-cancellation"
        r.equal([x["stage"] for x in self.summary["cancellation_barriers"]], list(MEMBERSHIP_STAGES), "all five actual cancellation seams")
        for goal, barrier in zip(scenario["repeat_for_each_stage"], self.summary["cancellation_barriers"]):
            r.case = "cancel/" + goal["stage"]
            for prefix, field in (("queue-", "queue_request"), ("cancel-", "cancel_request"), ("terminal-", "queue_request"), ("status-", "status_request")):
                row = self.rows["A05." + prefix + goal["stage"]]
                r.equal(row["request"], goal[field], "exact frozen real cancellation protocol operation")
                expected = goal["expected_queue_status"] if prefix == "queue-" else goal["expected_terminal_status"] if prefix == "terminal-" else "succeeded"
                r.equal(row["response"]["status"], expected, "actual cancellation status")
            r.equal(barrier["reached"], True, "actual dynamic stage reached")
            r.equal(barrier["checkpoint"]["stage"], goal["stage"], "actual original callback barrier stage")
            r.equal(barrier["before"], barrier["after"], "cancelled work publishes no state")
            r.equal(barrier["worker_errors"], [], "original worker cancelled cleanly")
            ledgers = [self.ledgers[i] for i in barrier["ledger_indices"]]
            r.require(any(x["final_callback_error_id"] is not None and any(e["identity"] == x["final_callback_error_id"] for e in x["callback_errors"]) for x in ledgers), "original cancellation exception identity retained")
        r.case = "publication-interruption"
        r.equal(len(self.summary["publication_interruptions"]), 1, "one exact publication sentinel scenario")
        for record in self.summary["publication_interruptions"]:
            r.equal(record["same_exception_object"], True, "same original BaseException sentinel")
            r.equal(record["before"], record["interrupted_state"], "transaction rollback preserves accepted state")
            r.equal(record["actual_status_response"]["result"]["target_status"], "unknown_outcome", "exact durable fenced outcome")
            for prepared in record["prepared_only"]:
                raw = (self.root / prepared["glb"]).read_bytes()
                r.equal(sha(raw), prepared["sha256"], "retained prepared-only bytes")
                r.equal(len(raw), prepared["bytes"], "retained prepared-only byte count")
                r.equal(prepared["sqlite_transaction_active"], True, "sentinel inside actual uncommitted transaction")
            retry = self.rows["A07.same-id-retry"]["response"]
            r.equal(retry["status"], "unknown_outcome", "same-ID interrupted request never replays")
            r.require("OKA-E-UNKNOWN-OUTCOME" in diagnostic_codes(retry), "exact interrupted request fence diagnostic")

    def verify_artifacts(self):
        r = self.r
        for artifact in self.summary["agent_artifacts"]:
            r.case = "artifact/" + artifact["workflow"] + "/" + artifact["name"]
            raw = (self.root / artifact["glb"]).read_bytes()
            r.equal(len(raw), artifact["bytes"], "whole retrieved artifact bytes")
            r.equal(sha(raw), artifact["sha256"], "whole retrieved artifact digest")
            r.equal(artifact["artifact_id"], "artifact:" + sha(raw), "content-addressed artifact ID")
            sequence = self.transcript[artifact["retrieval_first_exchange"] - 1:artifact["retrieval_last_exchange"]]
            chunks, offset = [], 0
            for row in sequence:
                request, response = row["request"], row["response"]
                r.equal(request["operation"], "artifact", "retained whole artifact retrieval only")
                r.equal(request["artifact_id"], artifact["artifact_id"], "one immutable artifact across slices")
                r.equal(request["offset"], offset, "contiguous requested chunk offsets")
                body = response["result"]
                data = base64.b64decode(body["data_base64"], validate=True)
                r.equal(body["offset"], offset, "contiguous returned chunk offsets")
                r.equal(body["program_revision"], artifact["program_revision"], "immutable chunk source revision")
                r.equal(body["total_bytes"], len(raw), "exact total count on every chunk")
                r.require(0 < len(data) <= request["max_bytes"], "bounded forward chunk progress")
                chunks.append(data); offset += len(data)
            r.equal(b"".join(chunks), raw, "all retained chunk bytes reconstruct exact artifact")
        scenario = next(s for s in self.contract["scenarios"] if s["id"] == "A10")
        for name, prefix, goal_size, goal_sha in (("artifact_loop", "slice-", self.responses["A10.export"]["result"]["total_bytes"], self.responses["A10.export"]["result"]["sha256"][7:]),
                                                ("asset_loop", "asset-", scenario["asset_loop"]["expected_bytes"], scenario["asset_loop"]["expected_sha256"])):
            r.case = "A10/" + name
            rows = [row for row in self.transcript if row["workflow"] == "A10" and row["step"].startswith(prefix)]
            chunks, offset = [], 0
            for index, row in enumerate(rows):
                r.equal(row["request"], self.resolve(scenario[name]["request_template"], {"offset": offset, "index": index}), "exact bounded loop request")
                body = row["response"]["result"]
                data = base64.b64decode(body["data_base64"], validate=True)
                r.equal(body["offset"], offset, "loop byte offset")
                r.require(0 < len(data) <= (17 if name == "asset_loop" else 65536), "loop exact byte cap")
                chunks.append(data); offset += len(data)
            r.equal(offset, goal_size, "loop exact complete byte count")
            r.equal(sha(b"".join(chunks)), goal_sha, "loop independent original complete hash")
        r.equal(self.rows["A10.eof"]["response"]["result"]["data_base64"], "", "exact EOF empty slice")
        r.equal(self.rows["A10.eof"]["response"]["result"]["next_offset"], None, "exact EOF ends continuation")
        r.equal(self.rows["A10.past-eof"]["response"]["status"], "rejected", "past EOF refusal")
        r.require("OKA-E-ARTIFACT" in diagnostic_codes(self.rows["A10.past-eof"]["response"]), "past EOF exact error")

    def verify_stores(self):
        r = self.r
        r.case = "immutable-stores"
        r.equal([s["workflow"] for s in self.summary["stores"]], [s["id"] for s in self.contract["scenarios"]], "all eleven immutable store snapshots")
        snapshots = {(s["workflow"], s["project_id"], s["program_revision"]): s for s in self.summary["snapshots"]}
        for store in self.summary["stores"]:
            workflow = store["workflow"]
            r.case = "store/" + workflow
            path = (self.root / store["path"]).resolve()
            r.equal(path.stat().st_size, store["bytes"], "closed snapshot byte count")
            r.equal(sha(path.read_bytes()), store["sha256"], "closed snapshot original digest")
            r.require(not Path(str(path) + "-wal").exists() and not Path(str(path) + "-shm").exists(), "snapshot has no unresolved auxiliary dependency")
            db = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
            db.row_factory = sqlite3.Row
            try:
                r.equal(db.execute("PRAGMA integrity_check").fetchone()[0], "ok", "immutable SQLite integrity")
                tables = {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                r.require({"projects", "sources", "requests", "runs", "artifacts", "acceptance_identities"} <= tables, "durable lifecycle tables")
                for project in db.execute("SELECT id,accepted_revision FROM projects ORDER BY id"):
                    key = workflow, project["id"]
                    r.require(key in self.final_states, "no hidden durable project")
                    if key not in self.final_states:
                        continue
                    expected = self.final_states[key]
                    r.equal(project["accepted_revision"], expected["accepted_program_revision"], "final durable accepted head")
                    run_rows = [dict(row) for row in db.execute("SELECT id,source_revision,descriptor,version FROM runs WHERE project_id=? ORDER BY id", (project["id"],))]
                    r.equal(run_rows, expected["runs"], "complete durable run rows equal last original state observation")
                    for run in run_rows:
                        descriptor = json.loads(run["descriptor"])
                        r.equal(descriptor.get("program_revision"), run["source_revision"], "durable run pins its own source")
                        r.equal(descriptor.get("run_id"), run["id"], "durable run identity")
                        r.require(run["source_revision"] in self.payloads, "durable run original frozen source")
                        r.require(descriptor.get("valid_until_seconds") in ("0", "1"), "durable run predetermined sample time")
                    artifacts = []
                    for row in db.execute("SELECT * FROM artifacts WHERE project_id=? ORDER BY id", (project["id"],)):
                        raw = bytes(row["data"])
                        digest = sha(raw)
                        artifacts.append({"id": row["id"], "program_revision": row["source_revision"], "bytes": len(raw), "sha256": digest, "stored_sha256": row["sha256"]})
                        r.equal(row["sha256"], "sha256:" + digest, "durable artifact raw bytes and stored hash")
                        r.equal(row["id"], "artifact:" + digest, "durable artifact content address")
                        matching = [a for a in self.summary["agent_artifacts"] if a["workflow"] == workflow and a["project_id"] == project["id"] and a["artifact_id"] == row["id"]]
                        r.require(bool(matching), "every durable artifact has actual transport retrieval")
                        for actual in matching:
                            r.equal(raw, (self.root / actual["glb"]).read_bytes(), "SQLite artifact equals whole retrieved bytes")
                            r.equal(row["source_revision"], actual["program_revision"], "SQLite artifact immutable source pin")
                    r.equal(artifacts, expected["artifacts"], "complete durable artifact inventory")
                for row in db.execute("SELECT * FROM sources ORDER BY project_id,revision"):
                    raw = bytes(row["raw"]); payload = json.loads(raw)
                    manifest, revision = payload_identity(payload)
                    r.equal(revision, row["revision"], "durable source revision recomputed from exact bytes")
                    r.require(revision in self.payloads, "all retained source snapshots are frozen original inputs")
                    if revision in self.payloads:
                        r.equal(payload, self.payloads[revision], "entire stored source/image payload")
                    key = workflow, row["project_id"], row["revision"]
                    r.require(key in snapshots, "durable source has retained original byte snapshot")
                    if key in snapshots:
                        pin = snapshots[key]
                        r.equal(raw, (self.root / pin["path"]).read_bytes(), "snapshot raw byte identity")
                        r.equal(sha(raw), pin["sha256"], "snapshot retained original digest")
                    case = self.expected.get(revision, {})
                    if case.get("state") == "invalid-selected":
                        r.equal(row["accepted_once"], 0, "invalid source may be diagnostic-only, never accepted")
                for row in db.execute("SELECT * FROM requests ORDER BY sequence"):
                    key = workflow, row["project_id"], row["id"]
                    r.require(key in self.receipts, "every durable request has original transcript")
                    original_rows = [item for item in self.transcript if
                        (item["workflow"], item["request"]["project_id"], item["request"]["request_id"]) == key]
                    if original_rows:
                        original_request = original_rows[0]["request"]
                        r.equal(row["digest"], sha(canonical(original_request)), "durable original canonical request digest")
                        r.equal(row["operation"], original_request["operation"], "durable original request operation")
                        if row["payload"] is not None:
                            r.equal(json.loads(row["payload"]), original_request, "durable complete original request payload")
                    if key in self.receipts:
                        response = json.loads(row["response"])
                        r.equal(response, self.receipts[key], "durable exact terminal response")
                        r.equal(row["state"], response["status"], "durable state agrees with response")
                    r.require(row["state"] not in ("running", "queued"), "no unresolved original request")
                    r.equal(row["owner"], None, "terminal request has no live owner")
                for row in db.execute("SELECT * FROM acceptance_identities ORDER BY project_id,revision"):
                    r.require(row["revision"] in self.payloads, "acceptance identities original revision")
                    identities = json.loads(row["identities"])
                    case = self.expected[row["revision"]]
                    expected_ids = ([g["element_id"] for g in case["geometry"].values()] + [["sparse-panels", "demo", "first"], ["sparse-panels", "demo", "sibling"]]
                                    if case.get("mode") == "source" else [["membership-probe", "demo", "probe"]])
                    r.equal(sorted(x["element_id"] for x in identities), sorted(expected_ids), "complete immutable acceptance occurrence identities")
            finally:
                db.close()

    def verify(self):
        self.verify_summary()
        self.verify_transcript()
        self.verify_ledgers()
        self.verify_interruptions()
        self.verify_artifacts()
        self.verify_stores()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--agent", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, help="Exact candidate schemas; no product imports")
    parser.add_argument("--agent-amendment", type=Path, help="Exact separately reviewed, published and read-back Agent-only overlay")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve().is_relative_to(args.agent.resolve()):
        raise ValueError("Independent reader output must be fresh and outside evidence")
    args.output.mkdir(parents=True)
    freeze, before = Freeze(args.inputs), inventory(args.agent)
    amendment = AgentAmendment(freeze, args.agent_amendment) if args.agent_amendment else None
    reader = Reader(freeze)
    result = {"schema_version": "ontokin.c088-independent-agent-reader/1", "started_utc": stamp(),
              "frozen_inputs": freeze.lineage(), "original_inventory_before": before,
              "reader_sha256": sha(Path(__file__).read_bytes()), "schema_validation": args.checkout is not None,
              "product_imports": False, "sqlite_mode": "mode=ro&immutable=1 on closed checkpointed snapshots"}
    result["agent_amendment"] = None if amendment is None else amendment.lineage()
    try:
        AgentReader(reader, args.agent, args.checkout, amendment).verify()
    except Exception as error:
        import traceback
        reader.require(False, "independent reader completed", {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}, "no observer/transport failures")
    after = inventory(args.agent)
    reader.case = "original-artifacts"
    reader.equal(before, after, "all original evidence files/SQLite/WAL/SHM bytes unchanged")
    freeze.assert_unchanged()
    if amendment is not None:
        amendment.assert_unchanged()
    result.update(completed_utc=stamp(), status="passed" if not reader.failures else "failed", checks=reader.checks,
                  failures=reader.failures, failure_count=len(reader.failures), original_inventory_after=after,
                  original_artifacts_unchanged=before == after, inputs_unchanged=True)
    save(args.output / "result.json", result)
    print(json.dumps({key: result[key] for key in ("status", "checks", "failure_count", "original_artifacts_unchanged")}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
