#!/usr/bin/env python3
"""Execute the immutable torque Agent request templates against a real store.

All requests and responses are retained losslessly. This driver never edits a
frozen input, raises its allocation, or infers a pass from a schema alone.
"""
from __future__ import annotations

import argparse
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import traceback
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.agent_store import dumps
from ontokin.execution_budget import HostPolicy
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.torque_agent import TorqueAgentService
from ontokin.torque_protocol import canonical_request


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


class PartialLoop(Exception):
    """An explicit capacity measurement is retained as incomplete evidence."""


def operation_request_validators(validator):
    """Compile unchanged exclusive operation branches, or use the full schema.

    Each admitted branch is an object requiring `operation`, constrained to a
    different string const. For an object with that operation, all other
    branches are therefore false. Replacing oneOf with its sole possible
    branch is equivalent for every instance, including invalid requests.
    No field, reference, bound or nested constraint in that branch is omitted.
    """
    schema = validator.schema
    annotations = {"$id", "$schema", "$defs", "title", "description", "oneOf"}
    if set(schema) - annotations or type(schema.get("oneOf")) is not list:
        return {}
    branches = {}
    for branch in schema["oneOf"]:
        operation = branch.get("properties", {}).get("operation", {})
        if (branch.get("type") != "object" or "operation" not in branch.get("required", [])
                or set(operation) != {"const"} or type(operation["const"]) is not str
                or operation["const"] in branches):
            return {}
        branches[operation["const"]] = branch
    return {operation: validator.evolve(schema={**schema, "oneOf": [branch]})
            for operation, branch in branches.items()}


def operation_response_validator(validator, operation, status):
    """Evaluate only provably fixed operation/status conditionals ahead of time.

    All root properties, definitions, references and value-dependent clauses
    remain unchanged. A conditional with only required header string consts
    has a fixed truth value for this actual header, so its unchanged then/else
    clause is exactly equivalent. Unsupported patterns retain the full clause.
    """
    schema = validator.schema
    if type(operation) is not str or type(status) is not str or type(schema.get("allOf")) is not list:
        return validator
    header = {"operation": operation, "status": status}
    clauses = []
    for clause in schema["allOf"]:
        condition = clause.get("if", {}) if type(clause) is dict else {}
        properties = condition.get("properties", {}) if type(condition) is dict else {}
        if (type(clause) is not dict or set(clause) - {"if", "then", "else"}
                or type(condition) is not dict or set(condition) - {"properties", "required", "type"}
                or condition.get("type", "object") != "object"
                or not properties or set(properties) - set(header)
                or set(condition.get("required", [])) != set(properties)
                or any(type(value) is not dict or set(value) != {"const"} or type(value["const"]) is not str
                       for value in properties.values())):
            clauses.append(clause)
            continue
        matches = all(header[key] == value["const"] for key, value in properties.items())
        selected = clause.get("then" if matches else "else", {})
        if selected != {}:
            clauses.append(selected)
    return validator.evolve(schema={**schema, "allOf": clauses})


def effective_table(root, relative, amendment_name):
    """Apply a published, independently reviewed overlay to a detached value."""
    original = root / relative
    table = read(original)
    directory = root / "docs/language-design/torque-amendments" / amendment_name
    amendment = read(directory / "AMENDMENT.json")
    publication = read(directory / "PUBLICATION.json")
    if publication["status"] != "passed" or amendment["original_table"]["path"] != relative:
        raise AssertionError("The amendment is not published for this exact original table")
    if digest(original.read_bytes()) != amendment["original_table"]["sha256"]:
        raise AssertionError("The immutable original table no longer matches the reviewed overlay")
    if digest((root / "docs/language-design/torque-v0.1/INPUT-FREEZE.json").read_bytes()) != amendment["frozen_manifest_sha256"]:
        raise AssertionError("The original frozen manifest changed")
    for name in ("ADOPTION.md", "AMENDMENT.json", "INDEPENDENT-REVIEW.json"):
        row = next(row for row in publication["files"] if row["path"] == (directory / name).relative_to(root).as_posix())
        if not row["exact_published_readback"] or digest((directory / name).read_bytes()) != row["sha256"]:
            raise AssertionError("Amendment authority differs from its exact published readback")
    for replacement in amendment.get("replacements", []):
        parts = [part.replace("~1", "/").replace("~0", "~") for part in replacement["json_pointer"].split("/")[1:]]
        target = table
        for part in parts[:-1]:
            target = target[int(part)] if isinstance(target, list) else target[part]
        key = int(parts[-1]) if isinstance(target, list) else parts[-1]
        if target[key] != replacement["original"]:
            raise AssertionError("Overlay precondition does not match the exact original field")
        target[key] = copy.deepcopy(replacement["replacement"])
    for addition in amendment.get("additions", []):
        parts = [part.replace("~1", "/").replace("~0", "~") for part in addition["json_pointer"].split("/")[1:]]
        target = table
        for part in parts[:-1]:
            target = target[int(part)] if isinstance(target, list) else target[part]
        if addition["original_present"] is not False or parts[-1] in target:
            raise AssertionError("Overlay addition precondition no longer matches the original table")
        target[parts[-1]] = copy.deepcopy(addition["value"])
    return table


class FrozenAgentRun:
    def __init__(self, args, directory, namespace, *, policy=None, host_check=None, clock=None):
        self.args, self.directory, self.namespace = args, directory, namespace
        directory.mkdir()
        self.frozen = args.source_root / "docs/language-design/torque-v0.1/freeze"
        self.policy = policy or HostPolicy(max_operations=1000000, max_elapsed_ms=30000)
        self.host_check, self.clock = host_check, clock
        self.service = None
        self.requests, self.responses, self.captures = {}, {}, {}
        self.checks = 0
        self.exchanges = 0
        manifest = args.source_root / "docs/language-design/torque-v0.1/INPUT-FREEZE.json"
        self.check(digest(manifest.read_bytes()) == "98df30158c0cd77c542d89652f5dec6b585d03451a06bf7b1baffee0fc2f02eb",
                   "Exact adopted immutable manifest identity")
        self.frozen_by_path = {row["path"]: row for row in read(manifest)["files"]}
        self.materializations = []
        self.log = gzip.open(directory / "exchanges.jsonl.gz", "wt", encoding="utf-8")
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        resources = {}
        for path in (args.schema_root / "docs/language-design").rglob("*.schema.json"):
            value = read(path)
            if "$id" in value:
                resources[value["$id"]] = Resource.from_contents(value)
        registry = Registry().with_resources(resources.items())
        self.registry = registry
        self.validators = {name: Draft202012Validator(read(args.source_root /
            ("docs/language-design/agent-v0.22/" + name + ".schema.json")), registry=registry)
            for name in ("request", "response")}
        self.operation_validators = operation_request_validators(self.validators["request"])
        self.response_validators = {}
        torque_schema = read(args.source_root / "docs/language-design/torque-v0.1/torques.schema.json")
        self.validators["torques"] = Draft202012Validator(torque_schema, registry=registry)
        self.validators["torque-record"] = Draft202012Validator({**torque_schema["$defs"]["record"],
            "$defs": torque_schema["$defs"]}, registry=registry)
        self.validators["torque-catalog"] = Draft202012Validator(read(args.source_root /
            "docs/language-design/torque-v0.1/catalog.schema.json"), registry=registry)
        self.open()

    def open(self):
        self.service = TorqueAgentService(self.directory / "store", host_policy=self.policy,
                                          check=self.host_check, clock=self.clock)

    def close(self):
        if self.service is not None:
            self.service.close()
            self.service = None

    def finish(self):
        self.close()
        self.log.close()
        self.inspect_store()
        write(self.directory / "source-materializations.json", self.materializations)

    def check(self, condition, message):
        self.checks += 1
        if not condition:
            raise AssertionError(message)

    def resolve(self, value, loop=None):
        if isinstance(value, dict):
            if set(value) == {"$bundle_file"}:
                path = self.frozen / value["$bundle_file"]
                files = read(path)
                paths = [path] + [path.parent / item["path"] for item in [files["entry"], *files["modules"], *files["assets"]]]
                for member in paths:
                    actual = member.resolve()
                    relative = actual.relative_to(self.args.source_root).as_posix()
                    row = self.frozen_by_path[relative]
                    raw = actual.read_bytes()
                    self.check(len(raw) == row["bytes"] and digest(raw) == row["sha256"],
                               "Original source/PNG/manifest bytes verified before dispatch: " + relative)
                program = load_texture_file_manifest(path)
                self.materializations.append({"file_manifest": value["$bundle_file"],
                    "program_revision": program.program_revision, "manifest": program.manifest()})
                return program.to_payload()
            if set(value) == {"$response"}:
                scenario, step, *path = value["$response"].split(".")
                result = self.responses[scenario + "." + step]
                for key in path:
                    result = result[int(key)] if isinstance(result, list) else result[key]
                return copy.deepcopy(result)
            if set(value) == {"$capture"}:
                return copy.deepcopy(self.captures[value["$capture"]])
            if set(value) == {"$loop"}:
                return loop[value["$loop"]]
            return {key: self.resolve(item, loop) for key, item in value.items()}
        if isinstance(value, list):
            return [self.resolve(item, loop) for item in value]
        if isinstance(value, str):
            if loop is not None:
                value = value.replace("${index}", str(loop["index"]))
            if value.startswith("c090-"):
                value = self.namespace + "-" + value
            return value
        return value

    def exchange(self, request, *, key=None, expected_status=None, expected_code=None,
                 request_schema=True, wait=True):
        # This Python transport canonicalizes exactly as the service does.
        clean, raw = canonical_request(request)
        if request_schema:
            self.operation_validators.get(clean["operation"], self.validators["request"]).validate(clean)
        response = self.service.handle(clean, wait=wait)
        self.exchanges += 1
        record = {"index": self.exchanges, "key": key, "request": clean, "response": response}
        if not getattr(self.args, "omit_transport_digest", False):
            record["request_canonical_sha256"] = digest(raw.encode())
        self.log.write(dumps(record) + "\n")
        # Keep every exact exchange in the compressed stream. A bounded
        # checkpoint flush avoids a separate zlib sync block per byte request;
        # original SQLite FULL commits still retain every response individually.
        if self.exchanges % 1000 == 0:
            self.log.flush()
        if key is not None:
            self.requests[key] = clean
            self.responses[key] = response
        header = (response.get("operation"), response.get("status"))
        if (all(type(value) is str for value in header)
                and header[0] in self.operation_validators
                and header[1] in self.validators["response"].schema["properties"]["status"]["enum"]):
            if header not in self.response_validators:
                self.response_validators[header] = operation_response_validator(self.validators["response"], *header)
            self.response_validators[header].validate(response)
        else:
            self.validators["response"].validate(response)
        pending = [response]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                if value.get("kind") == "object" and "pose_frame" in value:
                    self.check("torques" in value, "Every available object state retains a complete torque header")
                if "torques" in value:
                    self.validators["torques"].validate(value["torques"])
                if "torque_intervals" in value:
                    self.check(type(value["torque_intervals"]) is list, "Occurrence source history is a native complete array")
                    for record in value["torque_intervals"]:
                        self.validators["torque-record"].validate(record)
                if "torque_interface" in value:
                    self.validators["torque-catalog"].validate(value["torque_interface"])
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        if expected_status is not None:
            self.check(response["status"] == expected_status,
                       f"{key}: expected {expected_status}, received {response['status']}; "
                       f"diagnostics={response.get('diagnostics')}; protocol_error={response.get('protocol_error')}")
        if expected_code is not None:
            codes = [d["code"] for d in response.get("diagnostics", [])]
            if response.get("protocol_error"):
                codes.append(response["protocol_error"]["code"])
            self.check(expected_code in codes, f"{key}: required {expected_code}, received {codes}")
        return response

    def steps(self, scenario, steps):
        for step in steps:
            key = scenario + "." + step["step"]
            if "action" in step:
                self.check(step["action"] == "close_and_reopen_same_store", "Unknown frozen workflow action")
                self.close()
                if "host_policy" in step:
                    self.policy = HostPolicy(**step["host_policy"])
                self.open()
                continue
            if "request_ref" in step:
                request = copy.deepcopy(self.requests[step["request_ref"]])
                request.update(self.resolve(step.get("overrides", {})))
            else:
                request = self.resolve(step["request"])
            self.exchange(request, key=key, expected_status=step.get("expected_status"),
                          expected_code=step.get("expected_code"))

    def inspect_store(self):
        path = self.directory / "store/torque-program-agent.sqlite3"
        if not path.exists():
            return
        output = {"path": path.name, "bytes": path.stat().st_size, "sha256": file_digest(path)}
        with sqlite3.connect("file:" + str(path) + "?mode=ro", uri=True) as db:
            output["metadata"] = dict(db.execute("SELECT name,value FROM metadata"))
            output["integrity"] = db.execute("PRAGMA integrity_check").fetchone()[0]
            self.check(output["integrity"] == "ok", "SQLite integrity")
            self.check(output["metadata"].get("schema_version") == "ontokin.torque-program-agent-store/0.1",
                       "Independent torque store schema")
            output["counts"] = {name: db.execute("SELECT COUNT(*) FROM " + name).fetchone()[0]
                                for name in ("projects", "sources", "runs", "requests", "artifacts")}
            output["projects"] = db.execute("SELECT id,accepted_revision FROM projects ORDER BY id").fetchall()
            for project, revision in output["projects"]:
                if revision is not None:
                    row = db.execute("SELECT accepted_once FROM sources WHERE project_id=? AND revision=?",
                                     (project, revision)).fetchone()
                    self.check(row is not None and row[0] == 1, "Accepted pointer resolves to accepted source")
            output["artifacts"] = []
            for project, ident, revision, raw, report, sha in db.execute(
                    "SELECT project_id,id,source_revision,data,report,sha256 FROM artifacts ORDER BY project_id,id"):
                self.check(digest(raw) == sha.removeprefix("sha256:"), "Stored artifact digest equals actual bytes")
                output["artifacts"].append({"project": project, "id": ident, "program_revision": revision,
                    "bytes": len(raw), "sha256": sha, "report_sha256": digest(report.encode())})
            for project, ident, operation, payload, sha, response, status in db.execute(
                    "SELECT project_id,id,operation,payload,digest,response,state FROM requests"):
                if payload is not None:
                    self.check(digest(payload.encode()) == sha, "Stored canonical request digest")
                response = json.loads(response)
                self.check(isinstance(response, dict), "Stored actual response is an object")
                known_operation = operation in self.validators["response"].schema["properties"]["operation"]["enum"]
                self.check(response["project_id"] == project and response["request_id"] == ident
                           and response["operation"] == (operation if known_operation else None)
                           and response["status"] == status,
                           "Durable receipt preserves its exact request identity and state")
                if not known_operation:
                    self.check(status == "rejected" and response["protocol_error"]["code"] == "OKA-E-REQUEST",
                               "Unknown raw operation retains its inherited closed rejection envelope")
                self.check(response["schema_version"] == "ontokin.agent/0.22", "Stored protocol identity")
                revision = response.get("program_revision")
                if revision is not None and response["status"] == "succeeded":
                    self.check(db.execute("SELECT 1 FROM sources WHERE project_id=? AND revision=?",
                                          (project, revision)).fetchone() is not None,
                               "Successful receipt identifies an actual immutable source row")
                accepted = response.get("accepted_program_revision")
                if accepted is not None:
                    self.check(db.execute("SELECT accepted_once FROM sources WHERE project_id=? AND revision=?",
                                          (project, accepted)).fetchone()[0] == 1,
                               "Historical accepted pointer identifies source accepted in a real transaction")
            for project, ident, revision, descriptor, version in db.execute(
                    "SELECT project_id,id,source_revision,descriptor,version FROM runs"):
                run = json.loads(descriptor)
                self.check(run["run_id"] == ident and run["program_revision"] == revision and version >= 1,
                           "Actual run row binds complete descriptor identity")
                sample = run.get("last_valid_state")
                if sample is not None:
                    self.check(sample["time_seconds"] == run["valid_until_seconds"]
                               and sample["side"] == run["valid_until_side"],
                               "Stored run retains exact observed clock and side")
        write(self.directory / "sqlite-observation.json", output)

    def scope_assertions(self, scenario):
        ident = scenario["id"]
        if ident == "A01":
            catalog = self.responses["A01.discover"]["result"]
            self.check(catalog["torque_interface"] == read(self.args.source_root /
                       "docs/language-design/torque-v0.1/catalog.example.json"), "Complete closed torque catalog")
            membership = catalog["keyed_membership_interface"]["source_expressions"]["has_key"]
            self.check("torque-0.1" in membership["declaring_profiles"], ".22 inherits has_key")
            items = self.responses["A01.inspect-final"]["result"]["items"]
            for item in items:
                self.check("torque_intervals" in item["source"], "Every occurrence has source interval array")
                self.check("torques" in item["state"], "Every available .22 object state has torque header")
                state = item["state"]["torques"]
                if item["identity"].get("path") in ("ball", "sibling") or item.get("path") in ("ball", "sibling"):
                    expected_speed = 2 if item.get("path", item["identity"].get("path")) == "ball" else -1
                    self.check(state["signed_angular_speed_rad_per_s"] == expected_speed, "Frozen final carrier speed")
                    self.check(state["started_count"] == state["completed_count"] == 1, "Complete finite interval counts")
                    self.check(state["rotation_anchor_seconds"] == "2" and state["phase_since_anchor_rad"] == 0,
                               "Completion reanchor is actual boundary")
            world_request = {**self.requests["A01.inspect-self"], "request_id": self.namespace+"-same-clock-world"}
            del world_request["frame"]
            same_clock = self.exchange(world_request, key="A01.same-clock-world", expected_status="succeeded")
            world = {item["path"]: item["state"]["torques"] for item in same_clock["result"]["items"]}
            for item in self.responses["A01.inspect-self"]["result"]["items"]:
                self.check(item["state"]["torques"] == world[item["path"]],
                           "Self frame preserves complete world torque scalars and history")
            self.inspect_source_closure()
        elif ident.startswith("A02-"):
            self.repair_assertions(scenario)
        elif ident == "A03":
            self.check(self.responses["A03.same-create"] == self.responses["A03.create"], "Historical create exact response")
            self.check(self.responses["A03.same-export"] == self.responses["A03.export"], "Historical export exact response")
            result = self.responses["A03.after-reset"]["result"]
            empty = read(self.args.source_root / "docs/language-design/torque-v0.1/torques-empty.example.json")
            for item in result["items"]:
                if item.get("state", {}).get("available"):
                    self.check(item["state"]["torques"] == empty, "Reset cleared complete torque state")
        elif ident == "A04":
            project = self.requests["A04.create"]["project_id"]
            request = {"schema_version": "ontokin.agent/0.22", "project_id": project,
                       "request_id": self.namespace+"-cursor-control", "operation": "discover",
                       "profile": "torque-0.1", "limit": 1}
            original = self.exchange(request, key="A04.cursor-control", expected_status="succeeded")
            cursor = original["next_cursor"]
            self.check(isinstance(cursor, str) and bool(cursor), "Actual bounded discovery cursor exists")
            next_request = {**request, "cursor": cursor, "request_id": self.namespace+"-cursor-continuation"}
            self.exchange(next_request, expected_status="succeeded")
            for name, changes, code in (
                ("filter", {"filter": "torque"}, "OKL-E-REVISION"),
                ("project", {"project_id": project+"-other"}, "OKL-E-REVISION"),
                ("profile", {"profile": "keyed-membership-0.1"}, "OKL-E-CAPABILITY-UNSUPPORTED"),
            ):
                changed = {**next_request, **changes, "request_id": self.namespace+"-cursor-"+name}
                self.exchange(changed, expected_status="rejected", expected_code=code,
                              request_schema=name != "profile")
            old_policy = self.service.host_policy
            self.service.host_policy = HostPolicy(max_operations=999999, max_elapsed_ms=30000)
            try:
                self.exchange({**next_request, "request_id": self.namespace+"-cursor-policy"},
                              expected_status="rejected", expected_code="OKL-E-REVISION")
            finally:
                self.service.host_policy = old_policy
        elif ident == "A05":
            self.check(self.responses["A05.historical-export"] == self.responses["A05.export"],
                       "Reduced current policy retains identified historical outcome")

    @staticmethod
    def physical_fields(value):
        # These immutable provenance fields necessarily name the new accepted
        # source/run. Every physical/visual value and every stable identity is
        # still compared, while complete source bytes are checked separately.
        provenance = {"program_revision", "run_id", "source_location", "operand_location",
                      "duration_location"}
        if isinstance(value, dict):
            return {key: FrozenAgentRun.physical_fields(item) for key, item in value.items()
                    if key not in provenance}
        if isinstance(value, list):
            return [FrozenAgentRun.physical_fields(item) for item in value]
        return value

    def repair_assertions(self, scenario):
        from ontokin.execution_budget import SharedExecutionBudget
        from ontokin.reach_reference import _Arithmetic
        ident = scenario["id"]
        table = read(self.frozen / "agent/workflow-repairs.json")
        repair = next(row for row in table["repairs"] if row["id"] == scenario["repair_record"])
        project = self.requests[ident+".create"]["project_id"]
        original = self.service.read_program(project, repair["from"]["program_revision"])
        candidate = self.service.read_program(project, repair["to"]["program_revision"])
        expected = load_texture_file_manifest(self.frozen / repair["file_manifest"])
        self.check(candidate.to_payload() == expected.to_payload(), "Stored candidate equals exact frozen repaired closure")
        self.check(original.modules == candidate.modules and original.assets == candidate.assets,
                   "Every pinned library and PNG byte remains unchanged")
        edit = repair["patch"]
        patched = (original.entry.raw[:edit["start_byte"]] + edit["replacement"].encode()
                   + original.entry.raw[edit["end_byte"]:])
        self.check(candidate.entry.raw == patched, "All original entry bytes outside exact patch preserved")
        accepted = original if scenario["invalid_rollback"] else candidate
        self.check(self.service.accepted_revision(project) == accepted.program_revision,
                   "Actual durable accepted pointer obeys the valid/invalid edit decision")
        before_run = self.responses[ident+".evaluate-base"]["result"]["run_state"]
        self.check(self.service.get_run(project, before_run["run_id"]) == before_run,
                   "Original accepted run descriptor remains byte-value immutable")
        old_export = self.responses[ident+".export-base"]["result"]
        with self.service._store.connection() as db:
            row = db.execute("SELECT data,report FROM artifacts WHERE project_id=? AND id=?",
                             (project, old_export["artifact_id"])).fetchone()
        self.check(len(row[0]) == old_export["total_bytes"] and "sha256:"+digest(row[0]) == old_export["sha256"],
                   "Original artifact bytes and identity remain immutable after edit")
        self.check(json.loads(row[1]) == old_export["report"], "Original stored artifact report remains unchanged")
        old_slice = self.responses[ident+".old-artifact"]["result"]
        self.check(base64.b64decode(old_slice["data_base64"], validate=True) == row[0][:65536],
                   "Old artifact retrieval returns exact original bytes")
        after_run = self.responses[ident+".evaluate-after"]["result"]["run_state"]
        first = after_run["last_valid_state"]["objects"]["ball"]
        expected_first = scenario["expected_first_carrier"]
        self.check(first["inertia_kg_m2"] == float(Fraction(expected_first["inertia"])), "Frozen repaired inertia")
        self.check(first["torques"]["signed_angular_speed_rad_per_s"] == float(Fraction(expected_first["speed"])),
                   "Frozen repaired canonical speed")
        verification_budget = SharedExecutionBudget()
        arithmetic = _Arithmetic(check=verification_budget.tick)
        sine, cosine = arithmetic.sincos(Fraction(expected_first["phase"])/2)
        expected_q = [cosine, arithmetic.point(0), arithmetic.point(0), sine]
        error = first["torques"]["angular_error_bound_rad"]
        allowance = Fraction(int(error["numerator"]), int(error["denominator"]))
        actual_q = first["orientation_wxyz"]
        agrees = any(all(cell.lo-allowance <= Fraction(sign*actual) <= cell.hi+allowance
                          for cell, actual in zip(expected_q, actual_q)) for sign in (1, -1))
        self.check(agrees, "Frozen repaired phase agrees with independently enclosed quaternion within declared complete error")
        # Observe the sibling at every common semantic clock, in both sides,
        # through real versioned inspection rather than reusing source arrays.
        for clock in ("0", "1", "2"):
            for side in ("before", "after"):
                samples = []
                for label, run in (("base", before_run), ("repaired", after_run)):
                    key = ident+".sibling-"+label+"-"+clock+"-"+side
                    request = {"schema_version": "ontokin.agent/0.22", "project_id": project,
                        "request_id": self.namespace+"-"+key, "operation": "inspect",
                        "program_revision": run["program_revision"], "run_id": run["run_id"],
                        "selector": {"kind": "object"}, "fields": ["identity", "state", "matter"],
                        "limit": 100, "time": {"seconds": clock, "side": side}}
                    response = self.exchange(request, key=key, expected_status="succeeded")
                    samples.append({item["path"]: self.physical_fields(item)
                        for item in response["result"]["items"] if item["path"].startswith("sibling")})
                self.check(samples[0] == samples[1], "Complete sibling physical/visual state unchanged at "+clock+" "+side)
        self.inspect_source_closure()

    def inspect_source_closure(self):
        # Actual SQLite source bytes and their dependency/PNG closure are read
        # independently of producer inspection responses after the service closes.
        self.close()
        path = self.directory / "store/torque-program-agent.sqlite3"
        with sqlite3.connect("file:" + str(path) + "?mode=ro", uri=True) as db:
            for revision, raw, accepted in db.execute("SELECT revision,raw,accepted_once FROM sources"):
                from ontokin.texture_bundle import load_texture_bundle
                source = load_texture_bundle(json.loads(raw))
                self.check(source.program_revision == revision, "Stored bundle independently recomputes exact program revision")
                for asset in source.assets:
                    self.check(asset.sha256 == "sha256:" + digest(asset.raw), "Stored PNG exact hash")
        self.open()

    def interrupted_publication(self, scenario):
        class Sentinel(BaseException):
            pass
        sentinel = Sentinel("C091 exact transaction interruption")
        original = self.service._persist_task_metadata
        captured = {}
        def intercept(db, task):
            if task.artifact is not None:
                self.check(db.in_transaction, "Interruption runs inside the actual transaction")
                captured["artifact"] = copy.deepcopy(task.artifact)
                raise sentinel
            return original(db, task)
        self.service._persist_task_metadata = intercept
        request = self.resolve(scenario["export_request"])
        self.requests["A07.export"] = request
        try:
            self.service.handle(request)
            raise AssertionError("Actual artifact publication fault was not reached")
        except Sentinel as error:
            self.check(error is sentinel, "Original injected BaseException retained")
        finally:
            self.service._persist_task_metadata = original
        raw, report, artifact_id = captured["artifact"]
        (self.directory / "interrupted-prepared.glb").write_bytes(raw)
        self.captures["A07.prepared.artifact_id"] = artifact_id
        write(self.directory / "interruption.json", {"request": request,
            "prepared_artifact_id": artifact_id, "bytes": len(raw), "sha256": digest(raw),
            "prepared_report": report,
            "in_transaction": True, "original_exception_identity_preserved": True})
        with self.service._store.connection() as db:
            self.check(db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0,
                       "Interrupted transaction committed no artifact")
            self.check(db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0,
                       "Interrupted transaction committed no run")
        self.steps("A07", scenario["then"])

    def exact_artifact(self, scenario="A08"):
        response = self.responses[scenario + ".export"]
        ident = response["result"]["artifact_id"]
        project = self.requests[scenario + ".export"]["project_id"]
        with self.service._store.connection() as db:
            row = db.execute("SELECT data,sha256 FROM artifacts WHERE project_id=? AND id=?", (project, ident)).fetchone()
        self.check(row is not None, "Artifact exists in actual committed SQLite")
        self.check(digest(row[0]) == row[1].removeprefix("sha256:"), "Committed artifact bytes match stored hash")
        return row[0]

    def artifact_loop(self, scenario, specification):
        profiler = None
        if getattr(self.args, "profile_chunks", False):
            import cProfile
            profiler = cProfile.Profile()
            profiler.enable()
        try:
            return self._artifact_loop(scenario, specification)
        finally:
            self.log.flush()
            if profiler is not None:
                import pstats
                profiler.disable()
                profiler.dump_stats(self.directory / "chunk-profile.pstats")
                with (self.directory / "chunk-profile.txt").open("w") as stream:
                    pstats.Stats(profiler, stream=stream).sort_stats("cumtime").print_stats(55)

    def _artifact_loop(self, scenario, specification):
        raw = self.exact_artifact()
        started = time.monotonic()
        original_store_bytes = self.service.database_path.stat().st_size
        write(self.directory / "artifact-size.json", {"bytes": len(raw), "sha256": digest(raw),
            "max_bytes": specification["max_bytes"], "minimum_requests": (len(raw)+specification["max_bytes"]-1)//specification["max_bytes"]})
        print(json.dumps({"artifact_bytes": len(raw), "max_bytes": specification["max_bytes"],
                          "directory": str(self.directory)}), flush=True)
        offset, index = 0, 0
        reconstructed = self.directory / "retrieved.glb"
        with reconstructed.open("wb") as stream:
            while offset < len(raw):
                request = self.resolve(specification["request_template"], {"offset": offset, "index": index})
                response = self.exchange(request, expected_status="succeeded")
                result = response["result"]
                chunk = base64.b64decode(result["data_base64"], validate=True)
                self.check(chunk == raw[offset:offset+specification["max_bytes"]], "Every returned chunk equals exact committed range")
                self.check(len(chunk) > 0 and result["total_bytes"] == len(raw), "Complete byte identity remains fixed")
                stream.write(chunk)
                offset += len(chunk)
                self.check(result["next_offset"] == (offset if offset < len(raw) else None), "Exact next-offset and EOF semantics")
                index += 1
                if index % 1000 == 0:
                    self.log.flush()
                    print(json.dumps({"chunks": index, "bytes": offset, "total": len(raw),
                                      "elapsed_seconds": time.monotonic()-started,
                                      "sqlite_bytes": self.service.database_path.stat().st_size,
                                      "directory": str(self.directory)}), flush=True)
                if self.args.max_chunks is not None and index == self.args.max_chunks and offset < len(raw):
                    write(self.directory / "chunk-progress.json", {"status": "incomplete",
                        "chunks": index, "next_offset": offset, "artifact_bytes": len(raw),
                        "artifact_sha256": digest(raw), "max_bytes": specification["max_bytes"],
                        "elapsed_seconds": time.monotonic()-started,
                        "original_sqlite_bytes": original_store_bytes,
                        "current_sqlite_bytes": self.service.database_path.stat().st_size,
                        "remaining_chunk_requests": (len(raw)-offset+specification["max_bytes"]-1)//specification["max_bytes"],
                        "eof_and_past_eof_executed": False})
                    raise PartialLoop("Explicit capacity checkpoint; remaining original requests and EOF are not yet executed")
        self.check(reconstructed.read_bytes() == raw, "Full reconstructed GLB byte equality")
        artifact_chunks = index
        self.captures["A08.exact_total_bytes"] = len(raw)
        self.captures["A08.exact_total_bytes_plus_one"] = len(raw)+1
        eof = self.exchange(self.resolve(scenario["eof_request"]), expected_status="succeeded")
        for key in ("data_base64", "next_offset"):
            self.check(eof["result"][key] == scenario["eof_expected"][key], "Frozen EOF " + key)
        self.check(eof["truncated"] is False, "Frozen EOF nontruncated envelope")
        self.exchange(self.resolve(scenario["past_eof_request"]), expected_status="rejected", expected_code="OKA-E-ARTIFACT")
        asset = scenario["asset_loop"]
        offset, index, returned = 0, 0, bytearray()
        while offset < asset["total_bytes"]:
            response = self.exchange(self.resolve(asset["request_template"], {"offset": offset, "index": index}),
                                     expected_status="succeeded")
            result = response["result"]
            chunk = base64.b64decode(result["data_base64"], validate=True)
            self.check(result["total_bytes"] == asset["total_bytes"] and result["sha256"] == asset["sha256"],
                       "Every asset range retains frozen byte identity")
            returned.extend(chunk)
            offset += len(chunk)
            self.check(result["next_offset"] == (offset if offset < asset["total_bytes"] else None),
                       "Exact immutable asset next offset")
            index += 1
        self.check("sha256:"+digest(bytes(returned)) == asset["sha256"], "Complete reassembled frozen PNG digest")
        (self.directory / "retrieved-label.png").write_bytes(returned)
        expected_requests = len(scenario["steps"]) + artifact_chunks + 2 + index
        self.check(self.exchanges == expected_requests, "Every frozen setup/chunk/EOF/asset request has an actual exchange")
        with self.service._store.connection() as db:
            durable_requests = db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        self.check(durable_requests == expected_requests, "Every actual request has its own durable SQLite receipt")
        write(self.directory / "artifact-completion.json", {"status": "passed", "artifact_bytes": len(raw),
            "artifact_sha256": digest(raw), "max_bytes": specification["max_bytes"],
            "artifact_chunk_requests": artifact_chunks, "asset_chunk_requests": index,
            "actual_exchanges": self.exchanges, "durable_request_rows": durable_requests,
            "eof_and_past_eof_executed": True, "complete_artifact_byte_equality": True,
            "complete_frozen_png_sha256": asset["sha256"], "elapsed_seconds": time.monotonic()-started})

    def transport_cases(self):
        table = read(self.frozen / "agent/transport-cases.json")
        # One separately named original control proves these malformed bundles
        # are refusals of a usable source, rather than failures of the fixture.
        control = self.resolve(table["cases"][0]["base_request"])
        control["project_id"] += "-original-control"
        control["request_id"] += "-original-control"
        self.exchange(control, key="transport.original-control", expected_status="succeeded")
        for case in table["cases"]:
            request = self.resolve(case["base_request"])
            parts = [x for x in case["path"].split("/") if x]
            target = request
            for part in parts[:-1]:
                target = target[int(part)] if isinstance(target, list) else target[part]
            key = (int(parts[-1]) if isinstance(target, list) else parts[-1]) if parts else None
            container = target[key] if key is not None else target
            kind, value = case["mutation"], case["value"]
            if kind == "replace": target[key] = value
            elif kind == "append": target[key] += value
            elif kind == "append-copy-first": container.append(copy.deepcopy(container[0]))
            elif kind == "add-member": container.update(value)
            elif kind == "remove-member": del container[value]
            else: raise AssertionError("Unknown frozen transport mutation")
            response = self.exchange(request, key="transport."+case["id"],
                expected_status=case["expected_status"], expected_code=case["expected_code"], request_schema=False)
            if case["exact_inherited_message"] is not None:
                self.check(response["protocol_error"]["message"] == case["exact_inherited_message"], "Exact inherited transport error")
        with self.service._store.connection() as db:
            for table in ("sources", "runs", "artifacts"):
                self.check(db.execute("SELECT COUNT(*) FROM " + table + " WHERE project_id != ?",
                                      (control["project_id"],)).fetchone()[0] == 0,
                           "Malformed transport creates no " + table)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--schema-root", type=Path, default=ROOT)
    parser.add_argument("--scenarios", nargs="+", default=["A01", "A02-1", "A02-2", "A02-3", "A02-4", "A02-5", "A02-6", "A03", "A04", "A05", "A06", "A07", "transport"])
    parser.add_argument("--chunk-sizes", nargs="+", type=int, default=[1, 17, 65536])
    parser.add_argument("--max-chunks", type=int,
                        help="Retain an incomplete capacity measurement after this many actual chunks")
    parser.add_argument("--profile-chunks", action="store_true",
                        help="Profile only the actual retrieval loop, excluding create/export setup")
    parser.add_argument("--omit-transport-digest", action="store_true",
                        help="Keep complete exact requests/responses; audit canonical request digests from the closed SQLite store")
    args = parser.parse_args()
    args.output = args.output.absolute()
    args.output.mkdir()
    table = effective_table(args.source_root,
        "docs/language-design/torque-v0.1/freeze/agent/request-workflows.json", "c091-agent-cursor-template")
    scenarios = {x["id"]: x for x in table["scenarios"]}
    identity = {"head": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
                "python": sys.version, "platform": sys.platform,
                "runtime": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted((ROOT/"ontokin").glob("*.py"))},
                "harness_files": {str(p.relative_to(ROOT)): digest(p.read_bytes())
                                  for p in sorted((ROOT/"tools").glob("run_torque_agent_*.py"))},
                "request_schema_validation": "Full unchanged unique-const operation branch; root oneOf exclusivity checked before compilation",
                "response_schema_validation": "Full unchanged root and value constraints; only required operation/status const conditionals are evaluated using the actual header",
                "argv": sys.argv, "frozen_workflows_sha256": digest((args.source_root/"docs/language-design/torque-v0.1/freeze/agent/request-workflows.json").read_bytes())}
    write(args.output/"implementation.json", identity)
    results = []
    for name in args.scenarios:
        variants = args.chunk_sizes if name == "A08" else [None]
        for chunk in variants:
            label = name if chunk is None else name+"-chunk-"+str(chunk)
            run = None
            result = {"scenario": name, "variant": label, "status": "running"}
            started = time.monotonic()
            try:
                run = FrozenAgentRun(args, args.output/label, args.output.name+"-"+label)
                if name == "transport":
                    run.transport_cases()
                else:
                    scenario = scenarios[name]
                    run.steps(name, scenario.get("steps", []))
                    if name == "A07": run.interrupted_publication(scenario)
                    elif name == "A08":
                        selected = next(x for x in scenario["artifact_loops"] if x["max_bytes"]==chunk)
                        run.artifact_loop(scenario, selected)
                    elif name in ("A09", "A10", "A11"):
                        raise AssertionError("This scenario requires its separate identified stage/state/store matrix runner")
                    run.scope_assertions(scenario)
                result["status"] = "passed"
            except PartialLoop as error:
                result.update(status="incomplete", reason=str(error))
            except BaseException as error:
                result.update(status="failed", error=type(error).__name__+": "+str(error), traceback=traceback.format_exc())
            finally:
                if run is not None:
                    try:run.finish()
                    except BaseException as error:
                        result.update(status="failed", closing_error=repr(error), closing_traceback=traceback.format_exc())
                    result.update(checks=run.checks, exchanges=run.exchanges)
                result["elapsed_seconds"] = time.monotonic()-started
            results.append(result)
            write(args.output/(label+".json"),result)
            print(json.dumps({k:v for k,v in result.items() if k not in ("traceback","closing_traceback")}),flush=True)
    passed=all(x["status"]=="passed" for x in results)
    write(args.output/"summary.json",{"status":"passed" if passed else "failed", "results":results,
          "complete_torque_release":False,"scope":"Only explicitly selected workflows and checks; other frozen roles remain separate"})
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
