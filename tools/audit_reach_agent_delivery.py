#!/usr/bin/env python3
"""Independently audit retained Agent/0.6 delivery evidence, without execution.

This reader never imports the Agent service, compiler, simulator, exporter or
production JSON counter. It resolves the frozen protocol templates against
observed replies, checks actual chunk bytes, and reconciles the closed SQLite
store in read-only mode. Native/browser and the complete release audit remain
separate gates. Only immutable source bundle identity code is shared.
"""
from __future__ import annotations

import argparse
import base64
import copy
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path, PurePosixPath
import re
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.bundle import ProgramBundle, load_bundle, load_file_manifest

DATA = ROOT / "docs/language-design/planar-reach-v0.1"
PROTOCOL = "ontokin.agent/0.6"
TARGET = "ontokin.glb/0.6"
CASES = ("P01", "P11", "P13", "P20", "P16", "P17", "L01", "L02", "L03", "L04")
ENDS = {"P16": "4", "P17": "2", "L01": "4", "L02": "2", "L03": "4", "L04": "0.25"}
MAX_MEMBER = 64 * 1024 * 1024
MAX_ENVELOPE = 4 * 1024 * 1024
MAX_ENTRIES = 100000
MAX_DEPTH = 128
STORE_NAME = "service-store/planar-reach-program-agent.sqlite3"
STORE_SCHEMA = "ontokin.planar-reach-program-agent-store/0.1"


class EvidenceError(ValueError):
    """Retained bytes do not establish the claimed finite workflow."""


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def json_entries(value, *, limit=MAX_ENTRIES, depth_limit=MAX_DEPTH):
    """Count each value/container occurrence; keys charge bytes, not entries.

    Enter/leave markers distinguish cycles from repeated references. This is
    deliberately independent of ontokin.json_limits and all producer counters.
    """
    count, active = 0, set()
    stack = [(value, 0, False)]
    while stack:
        item, depth, leaving = stack.pop()
        if leaving:
            active.remove(id(item))
            continue
        count += 1
        require(count <= limit and depth <= depth_limit, "JSON entry/depth bound exceeded")
        kind = type(item)
        if kind in (dict, list):
            require(depth < depth_limit, "JSON container-depth bound exceeded")
            require(id(item) not in active, "Cyclic JSON value")
            active.add(id(item))
            stack.append((item, depth, True))
            if kind is dict:
                for key in item:
                    require(type(key) is str, "Nonstring JSON object key")
                    key.encode("utf-8")
                children = item.values()
            else:
                children = item
            stack.extend((child, depth + 1, False) for child in children)
        elif kind is str:
            item.encode("utf-8")
        elif kind is float:
            require(math.isfinite(item), "Nonfinite JSON number")
        elif kind is int:
            require(item.bit_length() <= 14000, "JSON integer exceeds its bounded numeric encoding")
        else:
            require(kind in (int, bool, type(None)), "Non-JSON value or subclass")
    return count


def envelope_bound(value):
    count = json_entries(value)
    require(len(canonical(value)) <= MAX_ENVELOPE, "Complete JSON envelope exceeds 4 MiB")
    return count


def decode(raw, *, envelope=False):
    require(len(raw) <= MAX_MEMBER, "Evidence JSON exceeds the member limit")
    def pairs(items):
        result = {}
        for key, item in items:
            require(key not in result, "Duplicate JSON object key")
            result[key] = item
        return result
    def invalid(value):
        raise EvidenceError("Nonfinite JSON constant: " + value)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    if envelope:
        envelope_bound(value)
    else:
        json_entries(value, limit=4000000)
    return value


def safe_path(root, name):
    require(type(name) is str and name and "\\" not in name and "\0" not in name,
            "Invalid evidence member path")
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and str(relative) == name
            and all(part not in (".", "..", "") for part in relative.parts), "Escaping evidence path")
    path = root
    for part in relative.parts:
        path = path / part
        require(not path.is_symlink(), "Symlink evidence members are not accepted")
    require(path.is_file() and path.resolve().is_relative_to(root), "Missing evidence member: " + name)
    return path


def read_raw(path, maximum=MAX_MEMBER):
    before = path.stat()
    require(before.st_size <= maximum, "Evidence member exceeds its byte bound")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.stat()
    require(len(raw) == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            "Evidence changed while reading")
    return raw


def descriptor(raw, name):
    return {"path": name, "bytes": len(raw), "sha256": sha(raw)}


def file_identity(path, name, maximum=4 * 1024 * 1024 * 1024):
    before, digest, size = path.stat(), hashlib.sha256(), 0
    require(before.st_size <= maximum, "Retained store exceeds its explicit audit byte bound")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            require(size <= maximum, "Retained store grew beyond its byte bound")
            digest.update(chunk)
    after = path.stat()
    require(size == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            "Retained store changed while hashing")
    return {"path": name, "bytes": size, "sha256": "sha256:" + digest.hexdigest()}


def implementation():
    digest = hashlib.sha256()
    for path in sorted((ROOT / "ontokin").glob("*.py")):
        digest.update(path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    version = re.search(r'__version__\s*=\s*[\'"]([^\'"]+)',
                        (ROOT / "ontokin/__init__.py").read_text()).group(1)
    return {"name": "ontokin-reference", "version": version,
            "source_code_sha256": "sha256:" + digest.hexdigest()}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def source_identity():
    require(not git("status", "--porcelain=v1", "--untracked-files=all"), "Audit from a clean committed checkout")
    return {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}")}


class Schemas:
    """Closed registry using the exact frozen schema manifest and package pins."""
    def __init__(self):
        self.packages = {}
        for line in (ROOT / "tools/force-agent-verification-requirements.txt").read_text().splitlines():
            if "==" not in line or line.lstrip().startswith("#"):
                continue
            name, version = line.strip().split("==")
            actual = importlib.metadata.version(name)
            require(actual == version, "Verification package pin differs: " + name)
            self.packages[name] = actual
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from referencing.exceptions import NoSuchResource
        def deny(uri):
            raise NoSuchResource(ref=uri)
        registry = Registry(retrieve=deny)
        manifest = decode((DATA / "schema-drafts/schema-drafts-manifest.json").read_bytes())
        documents, self.hashes = {}, {}
        for group, base in (("members", DATA / "schema-drafts"), ("inherited_inputs", DATA)):
            for item in manifest[group]:
                path = base / item["path"]
                raw = path.read_bytes()
                require(sha(raw) == item["sha256"] and len(raw) == item.get("bytes", len(raw)),
                        "Frozen schema bytes differ")
                doc = decode(raw)
                Draft202012Validator.check_schema(doc)
                require(doc["$id"] not in documents, "Duplicate schema identity")
                documents[doc["$id"]] = doc
                self.hashes[path.resolve().relative_to(ROOT).as_posix()] = sha(raw)
                registry = registry.with_resource(doc["$id"], Resource.from_contents(doc))
        self.validators = {name: Draft202012Validator(
            documents["https://omegapy.github.io/OntoKin/proposals/planar-reach-v0.1/" + name + ".schema.json"],
            registry=registry) for name in ("agent-request", "agent-response", "reach-projection")}

    def check(self, name, value):
        for error in self.validators[name].iter_errors(value):
            raise EvidenceError(f"{name} schema at {list(error.absolute_path)}: {error.message[:400]}")


class Sources:
    def __init__(self):
        self.cases, self.bundles, self.paths = {}, {}, {}
        for base in (DATA, DATA / "draft2-supplements"):
            for item in decode((base / "acceptance.json").read_bytes())["source_cases"]:
                name = item["id"]
                require(name not in self.cases, "Duplicate frozen case")
                path = base / item["file_manifest"]
                require(sha(path.read_bytes()) == item["file_manifest_sha256"], "Frozen source manifest changed")
                bundle = load_file_manifest(path)
                require(bundle.program_revision == item["program_revision"], "Frozen source bundle changed")
                self.cases[name], self.bundles[name] = item, bundle
                self.paths[name] = path.relative_to(ROOT).as_posix()
        self.revisions = {bundle.program_revision: bundle for bundle in self.bundles.values()}

    def candidate(self, request):
        if request["operation"] == "create":
            return load_bundle(request["bundle"])
        if request["operation"] != "edit":
            return None
        require(not request.get("module_changes"), "Unexpected dependency edit in this fixed workflow")
        base = self.revisions.get(request["expected_program_revision"])
        require(base is not None, "Edit has no fixed immutable source base")
        # Reconstruction needs immutable SourceUnit identities and metadata;
        # base.sources exposes detached legacy parser Source objects instead.
        units, changes = {unit.source_id: unit for unit in base.units}, {}
        for patch in request["patches"]:
            unit = units.get(patch["source_id"])
            require(unit is not None and unit.revision == patch["source_revision"], "Patch source revision differs")
            left, right = patch["start_byte"], patch["end_byte"]
            require(type(left) is int and type(right) is int and 0 <= left <= right <= len(unit.raw), "Invalid byte patch")
            require(unit.raw[left:right].decode("utf-8") == patch["expected_text"], "Patch byte precondition differs")
            changes.setdefault(unit.source_id, []).append(patch)
        for key, patches in changes.items():
            unit, ceiling = units[key], len(units[key].raw) + 1
            raw = unit.raw
            for patch in sorted(patches, key=lambda item: item["start_byte"], reverse=True):
                left, right = patch["start_byte"], patch["end_byte"]
                require(right < ceiling, "Overlapping source patches")
                raw = raw[:left] + patch["replacement"].encode("utf-8") + raw[right:]
                ceiling = left
            units[key] = replace(unit, raw=raw)
        return ProgramBundle(units["entry"], tuple(units[unit.source_id] for unit in base.modules))


def resolve(value, bindings, sources):
    if type(value) is dict:
        if set(value) == {"$fixture_bundle"}:
            return sources.bundles[value["$fixture_bundle"]].to_payload()
        for marker, adjustment in (("$binding", 0), ("$binding_minus_one", -1)):
            if set(value) == {marker}:
                require(value[marker] in bindings, "Template uses an uncaptured actual binding")
                result = copy.deepcopy(bindings[value[marker]])
                if adjustment:
                    require(type(result) is int, "Entry binding is not an integer")
                    result += adjustment
                return result
        return {key: resolve(item, bindings, sources) for key, item in value.items()}
    if type(value) is list:
        return [resolve(item, bindings, sources) for item in value]
    return value


def frozen_request(actual, template, bindings, sources):
    require(actual == resolve(template, bindings, sources), "Actual request differs from its frozen template")


def complete_source_units(program, returned_units, expected_identities):
    """Check complete reads against immutable units with their package identity."""
    units = {unit.source_id: unit for unit in program.units}
    identities, found = [], {}
    require(type(returned_units) is list, "Complete source read is not a unit list")
    for returned in returned_units:
        source_id = returned["source_id"]
        unit = units.get(source_id)
        require(unit is not None and source_id not in found, "Unknown or repeated complete source unit")
        require(returned["source"].encode("utf-8") == unit.raw and returned["filename"] == unit.filename
                and returned["source_revision"] == unit.revision, "Complete source read changed bytes")
        identities.append({"source_id": unit.source_id, "source_revision": unit.revision,
                           "filename": unit.filename, "package_id": unit.package_id, "version": unit.version})
        found[source_id] = returned
    require(identities == expected_identities, "Complete source read omitted or reordered a unit")
    return found


def retained_run(record, final_state, final_version):
    before, after = record["before"], record["after"]
    require(type(before) is list and len(before) == 2 and before == after, "Historical run or version changed")
    require(before[0] == final_state and type(before[1]) is int and before[1] == final_version,
            "Retained history does not resolve to the actual final run/version")


def codes(response):
    values = [item["code"] for item in response["diagnostics"]]
    if response.get("protocol_error"):
        values.append(response["protocol_error"]["code"])
    return values


def failure(response, code):
    require(response["status"] in ("failed", "rejected") and code in codes(response), "Required failure is absent: " + code)
    require(response["achieved_level"] != "delivered" and "artifact_id" not in (response.get("result") or {}),
            "Failed request exposes a delivered artifact")


def action_records(response):
    return [action for item in (response.get("result") or {}).get("items", [])
            for action in item.get("actions", []) if action.get("kind") == "reach_planar"]


def action(response, path="reach"):
    rows = [item for item in response["result"]["items"] if item["path"] == path]
    require(len(rows) == 1, "Missing or duplicate action item: " + path)
    values = [value for value in rows[0]["actions"] if value.get("kind") == "reach_planar"]
    require(len(values) == 1, "Missing or duplicate complete reach projection")
    return values[0]


def null_admission(state):
    require(state["lifecycle"] == "pending" and state["claimed_joint_ids"] == [], "Pending state acquired claims")
    for key in ("resolved_joint_targets_rad", "start_coordinates_rad", "start_time_seconds", "elapsed_seconds",
                "completion_time_seconds", "current_residual_m", "terminal_result"):
        require(state[key] is None, "Pending admission field was fabricated: " + key)
    require(state["action_joint_rates_rad_per_s"] == [0, 0], "Pending action acquired an action rate")


def frozen_equal(actual, expected, path=()):
    """Compare frozen state data; angle/rate tolerance is the frozen 2e-15.

    Source position/residual fields use the adopted 1e-9 metre tolerance. This
    checks recorded observations only; it is not independent rate acceptance.
    """
    if type(expected) is dict:
        require(type(actual) is dict and set(actual) == set(expected), "Frozen state field set differs: " + str(path))
        for key, value in expected.items():
            frozen_equal(actual[key], value, path + (key,))
    elif type(expected) is list:
        require(type(actual) is list and len(actual) == len(expected), "Frozen state list differs: " + str(path))
        for index, value in enumerate(expected):
            frozen_equal(actual[index], value, path + (index,))
    elif type(expected) in (int, float):
        require(type(actual) in (int, float) and math.isfinite(actual), "Nonfinite state number")
        angle = any(type(key) is str and ("_rad" in key or "orientation" in key) for key in path)
        require(abs(actual - expected) <= (2e-15 if angle else 1e-9), "Frozen numeric observation differs: " + str(path))
    else:
        require(type(actual) is type(expected) and actual == expected, "Frozen observation differs: " + str(path))


def joined_chunks(exchanges, retrieval, export_request, export_response):
    """Rebuild actual bytes; do not trust closure flags or claimed chunk counts."""
    result, offset, chunks, seen = export_response["result"], 0, [], set()
    total = result["total_bytes"]
    require(type(total) is int and 0 < total <= MAX_MEMBER, "Artifact byte count is invalid")
    provenance = {"exporter": result["report"]["exporter"],
                  "source_code_sha256": "sha256:" + result["report"]["source_code_sha256"],
                  "program_revision": result["program_revision"]}
    wanted = {"project_id": export_request["project_id"], "run_id": export_response["run_id"],
              "artifact_id": result["artifact_id"], "sha256": result["sha256"], "bytes": total,
              "chunk_bytes": 32768, "provenance": provenance}
    require(all(retrieval.get(key) == value for key, value in wanted.items()), "Retrieval identity/provenance differs")
    roles = retrieval["chunk_roles"]
    require(type(roles) is list and 0 < len(roles) <= MAX_MEMBER // 32768, "Invalid retrieval chunk inventory")
    for role in roles:
        require(role not in seen and role in exchanges, "Duplicate or missing chunk role")
        seen.add(role)
        request, response = exchanges[role][:2]
        require(request == {"schema_version": PROTOCOL, "project_id": export_request["project_id"],
                            "request_id": request["request_id"], "operation": "artifact",
                            "artifact_id": result["artifact_id"], "offset": offset, "max_bytes": 32768},
                "Actual chunk request changed project/artifact/offset/size")
        require(response["status"] == "succeeded", "Chunk request failed")
        part = response["result"]
        try:
            chunk = base64.b64decode(part["data_base64"], validate=True)
        except (ValueError, TypeError) as error:
            raise EvidenceError("Invalid chunk base64") from error
        require(part["offset"] == offset and part["total_bytes"] == total and part["sha256"] == result["sha256"]
                and part["artifact_provenance"] == provenance, "Actual chunk metadata differs")
        require(0 < len(chunk) <= 32768 and offset + len(chunk) <= total, "Chunk is empty or exceeds artifact")
        offset += len(chunk)
        require(part["next_offset"] == (offset if offset < total else None), "Chunk gap, overlap or false EOF")
        chunks.append(chunk)
    raw = b"".join(chunks)
    require(offset == total and sha(raw) == result["sha256"], "Actual retrieved bytes do not close the artifact")
    return raw


class Reader:
    def __init__(self, directory, *, schemas=None, sources=None):
        self.root = Path(directory).resolve()
        self.schemas, self.sources = schemas or Schemas(), sources or Sources()
        self.files, self.exchanges, self.used = {}, {}, set()
        self.bindings, self.heads, self.accepted, self.ledger = {}, {}, set(), {}
        self.runs, self.run_versions, self.artifacts, self.retained = {}, {}, {}, {}
        self.implementation = implementation()
        self.projections = 0

    def read(self, name, expected=None, *, binary=False, envelope=False, maximum=MAX_MEMBER):
        raw = read_raw(safe_path(self.root, name), maximum)
        receipt = descriptor(raw, name)
        if expected is not None:
            require(type(expected) is dict and all(expected.get(key) == value for key, value in receipt.items()),
                    "Evidence descriptor differs: " + name)
        require(name not in self.files or self.files[name] == receipt, "Evidence changed between reads")
        self.files[name] = receipt
        return raw if binary else decode(raw, envelope=envelope)

    def member(self, item, **kwargs):
        require(type(item) is dict and set(item) >= {"path", "bytes", "sha256"}, "Incomplete evidence descriptor")
        return self.read(item["path"], item, **kwargs)

    def at(self, role):
        require(role in self.exchanges, "Missing required actual exchange: " + role)
        self.used.add(role)
        return self.exchanges[role][:2]

    def recursive(self, value, *, legacy_action=False, projection=False, response_path=None):
        if projection:
            require(type(value) is dict, "A complete reach projection must be an object")
        if type(value) is dict:
            if "implementation" in value:
                require(value["implementation"] == self.implementation, "Mixed implementation in actual response")
            if value.get("schema_version") == PROTOCOL:
                self.schemas.check("agent-response", value)
                response_path = ()
            if projection or (value.get("kind") == "reach_planar" and not legacy_action):
                self.schemas.check("reach-projection", value)
                bundle = self.sources.revisions.get(value["program_revision"])
                require(bundle is not None, "Projection identifies an unknown source program")
                location = value["source_location"]
                unit = bundle.sources.get(location["source_id"])
                require(unit is not None and unit.revision == location["source_revision"]
                        and 0 <= location["start_byte"] < location["end_byte"] <= len(unit.raw),
                        "Projection source location differs")
                self.projections += 1
            if "source_manifest" in value:
                bundle = self.sources.revisions.get(value.get("program_revision"))
                require(bundle is not None and value["source_manifest"] == bundle.manifest(),
                        "Returned source manifest differs from immutable bytes")
            snapshot = response_path in (("result", "initial_state"),
                                         ("result", "run_state", "last_valid_state"))
            if snapshot:
                require(type(value.get("time_seconds")) is str and value.get("side") in ("before", "after")
                        and all(type(value.get(key)) is dict for key in
                                ("objects", "frames", "joints", "actions", "reaches")),
                        "A complete source snapshot requires its clock and named state maps")
            for key, item in value.items():
                if snapshot and key in {"actions", "reaches"}:
                    # The inherited actions[path] table has a generic action
                    # summary; reaches[path] carries the complete 0.6 record.
                    # Inspect actions[] remains a complete projection. Select
                    # by the actual response path, never by omitted fields
                    # that a malformed reach record could use to evade checks.
                    for record in item.values():
                        self.recursive(record, legacy_action=key == "actions", projection=key == "reaches")
                else:
                    path = None if response_path is None else response_path + (key,)
                    self.recursive(item, response_path=path)
        elif type(value) is list:
            for item in value:
                path = None if response_path is None else response_path + ("*",)
                self.recursive(item, response_path=path)

    def trace(self, rows):
        require(type(rows) is list and 0 < len(rows) <= 30000, "Invalid exchange inventory")
        for sequence, row in enumerate(rows, 1):
            role = row["role"]
            require(row["sequence"] == sequence and role not in self.exchanges and row["method"] in ("handle", "submit"),
                    "Duplicate/out-of-order/unexecuted exchange")
            request = self.member(row["request"], envelope=True)
            response = self.member(row["response"], envelope=True)
            # LP04.07 deliberately asks for an unsupported field. Its exact
            # frozen request and rejection are checked below, never repaired.
            if role != "LP04.07":
                self.schemas.check("agent-request", request)
            self.schemas.check("agent-response", response)
            require(all(response.get(key) == request.get(key) for key in
                        ("schema_version", "project_id", "request_id", "operation")), "Request/response echo differs")
            require(response["schema_version"] == PROTOCOL, "Wrong Agent binding")
            start, end = datetime.fromisoformat(row["started_at"]), datetime.fromisoformat(row["finished_at"])
            require(start.tzinfo is not None and end >= start, "Invalid exchange timing")
            self.recursive(response)
            self.exchanges[role] = (request, response, row)
            project, request_id = request["project_id"], request["request_id"]
            key = (project, request_id)
            if key in self.ledger:
                old_request, old_response = self.ledger[key]
                if canonical(request) == canonical(old_request):
                    require(response == old_response, "Canonical retry changed the immutable terminal receipt")
                else:
                    failure(response, "OKL-E-REQUEST-ID")
                continue
            self.ledger[key] = (request, response)
            previous = self.heads.get(project)
            if request["operation"] in ("create", "edit") and response["status"] == "succeeded":
                candidate = self.sources.candidate(request)
                require(candidate.program_revision in self.sources.revisions
                        and candidate.to_payload() == self.sources.revisions[candidate.program_revision].to_payload(),
                        "Accepted edit/create differs from its frozen source bytes")
                require(request["expected_program_revision"] == previous, "Source acceptance used a stale expected head")
                previous = candidate.program_revision
                require(response["program_revision"] == previous, "Accepted candidate revision differs")
                self.accepted.add((project, previous))
            require(response["accepted_program_revision"] == previous, "Unrequested accepted-source change")
            self.heads[project] = previous
            result = response.get("result") or {}
            run = result.get("run_state")
            if run is not None:
                run_key = (project, run["run_id"])
                require(response["run_id"] == run["run_id"] and run["program_revision"] in self.sources.revisions,
                        "Run identity/source differs from its receipt")
                mutating = request["operation"] in ("create", "edit", "evaluate", "reset", "export", "validate")
                mutating &= response["status"] == "succeeded" or any(code == "OKL-E-REACH" for code in codes(response))
                if mutating:
                    self.runs[run_key] = copy.deepcopy(run)
                    self.run_versions[run_key] = self.run_versions.get(run_key, 0) + 1
                else:
                    require(run_key in self.runs and run == self.runs[run_key], "Read/rejection changed or invented a run")
            if "artifact_id" in result and request["operation"] != "artifact":
                require(request["operation"] == "export" and response["status"] == "succeeded"
                        and response["achieved_level"] == "delivered", "Artifact appeared outside successful explicit delivery")
                artifact_key = (project, result["artifact_id"])
                require(artifact_key not in self.artifacts, "Unexpected duplicate independent export artifact")
                self.artifacts[artifact_key] = (request, response)

    def expected(self, request, response, expected):
        for key in ("status", "accepted_program_revision", "program_revision", "truncated", "next_cursor"):
            if key in expected:
                require(response[key] == expected[key], "Frozen response field differs: " + key)
        if "diagnostic_code" in expected:
            failure(response, expected["diagnostic_code"])
        if "protocol_error_code" in expected:
            require((response.get("protocol_error") or {}).get("code") == expected["protocol_error_code"],
                    "Required protocol error differs")
        for key in ("category", "phase"):
            if key in expected:
                require(any(item[key] == expected[key] for item in response["diagnostics"]), "Frozen diagnostic differs: " + key)
        if "reach_code" in expected:
            require(any(item.get("details", {}).get("reach_code") == expected["reach_code"]
                        for item in response["diagnostics"]), "Wrong reach failure")
        result = response.get("result") or {}
        run = result.get("run_state")
        for key in ("valid_until_seconds", "valid_until_side"):
            if key in expected:
                require(run is not None and run[key] == expected[key], "Frozen retained interval differs")
        if "run_status" in expected:
            require(run is not None and run["status"] == expected["run_status"], "Frozen run status differs")
        if "same_run_as" in expected:
            require(response["run_id"] == self.bindings[expected["same_run_as"]], "Run continuation changed identity")
        if expected.get("new_run_identity"):
            old = {value for key, value in self.bindings.items() if key.endswith("_run") and type(value) is str}
            require(type(response["run_id"]) is str and response["run_id"] not in old, "Fresh run reused a prior identity")
        if "receipt_equals" in expected:
            require(response == self.bindings[expected["receipt_equals"]], "Frozen retry receipt changed")
        if "target_terminal_response_equals" in expected:
            require(result["target"] == self.bindings[expected["target_terminal_response_equals"]], "Status changed historical receipt")
        if expected.get("no_new_artifact"):
            require("artifact_id" not in result and response["achieved_level"] != "delivered", "Unexpected artifact")
        if "effects_committed" in expected:
            details = (response.get("protocol_error") or {}).get("details", {})
            if "effects_committed" in details or expected.get("failure_stage"):
                require(details.get("effects_committed") is expected["effects_committed"],
                        "Failure does not establish its publication rollback")
            else:
                # The frozen tiny-budget case permits an earlier inherited
                # resource guard. Its unchanged effects are established from
                # the exact retained run and complete closed-store inventory.
                require(expected.get("resource_failure_required") is True,
                        "Missing explicit publication rollback evidence")
        records = action_records(response)
        if "returned_action_count" in expected:
            require(len(records) == result["total"] == expected["returned_action_count"], "Incomplete action projection inventory")
        for record in records:
            require(record["program_revision"] == request["program_revision"]
                    and record["accepted_program_revision"] == response["accepted_program_revision"]
                    and record["context_origin"] == "agent", "Action projection has another source/publication context")
            if "candidate_only" in expected:
                require(record["candidate_only"] is expected["candidate_only"], "Wrong current candidate context")
            if "projection_candidate_only" in expected:
                require(record["candidate_only"] is expected["projection_candidate_only"], "Historical marker leaked into current projection")
            current = record["current"]
            if "current" in expected:
                require(current == expected["current"], "Unsampled action fabricated current state")
            if "current_available" in expected:
                require(current["available"] is expected["current_available"], "Wrong current availability")
            if current["available"]:
                value = current["value"]
                require(value["observation"] == {"context_kind": "run_sample", "run_id": request["run_id"],
                                                  "side": request["time"]["side"], "time_seconds": request["time"]["seconds"]},
                        "Action observation differs from actual requested run/sample")
                lifecycle = expected.get("lifecycle", expected.get("current_lifecycle"))
                if lifecycle is not None:
                    require(value["lifecycle"] == lifecycle, "Frozen lifecycle differs")
                if expected.get("admission_fields_null"):
                    null_admission(value)
        if run is not None and "candidate_only" in expected:
            require(run["candidate_only"] is expected["candidate_only"], "Historical run candidate marker differs")
        if expected.get("admission_not_run"):
            state = result.get("initial_state") or (run or {}).get("last_valid_state")
            require(state is not None and state["time_seconds"] == "0" and state["side"] == "before",
                    "Construction/reset performed admission")
            for record in state["reaches"].values():
                null_admission(record["current"]["value"])
        if "expected_sample" in expected:
            case_id, sample = expected["expected_sample"].split("@")
            seconds, side = sample.split(":")
            self.lifecycle_sample(response, case_id, seconds, side, request["run_id"])

    def lifecycle_sample(self, response, case_id, seconds, side, run_id):
        matches = [sample for sample in self.sources.cases[case_id]["samples"]
                   if sample["time_seconds"] == seconds and sample["side"] == side]
        require(len(matches) == 1, "Missing frozen lifecycle sample")
        expected = matches[0]["reaches"]
        actual = {item["path"]: action(response, item["path"]) for item in response["result"]["items"]}
        require(set(actual) == set(expected), "Lifecycle projection omitted a named action")
        for path, record in expected.items():
            want = copy.deepcopy(record)
            want.update(context_origin="agent", candidate_only=False,
                        accepted_program_revision=response["accepted_program_revision"])
            want["current"]["value"]["observation"].update(context_kind="run_sample", run_id=run_id)
            frozen_equal(actual[path], want)

    def protocol(self):
        document = decode((DATA / "draft2-supplements/protocol-cases.json").read_bytes())
        require([len(case["steps"]) for case in document["protocol_cases"]] == [9, 9, 5, 7, 12], "Frozen LP inventory changed")
        steps, sequence = [], 0
        for case in document["protocol_cases"]:
            for step in case["steps"]:
                role = step["id"]
                request, response = self.at(role)
                frozen_request(request, step["request_template"], self.bindings, self.sources)
                actual_sequence = self.exchanges[role][2]["sequence"]
                require(actual_sequence > sequence, "Frozen LP steps were reordered")
                sequence = actual_sequence
                expected = resolve(step["expected"], self.bindings, self.sources)
                self.expected(request, response, expected)
                if "canonical_request_identical_to" in expected:
                    require(canonical(request) == canonical(self.at(expected["canonical_request_identical_to"])[0]), "Frozen retry differs")
                for name, expression in step["capture_bindings"].items():
                    if expression == "response.run_id":
                        value = response["run_id"]
                        require(type(value) is str, "Missing actual captured run")
                    elif expression in ("complete immutable terminal response", "complete response"):
                        value = response
                    elif expression == "actual returned source.initializer_target":
                        value = response["result"]["items"][0]["source"]["initializer_target"]
                    elif expression == "logical_json_entries(complete response)":
                        value = envelope_bound(response)
                    else:
                        raise EvidenceError("Unknown frozen binding expression")
                    self.bindings[case["id"] + "." + name] = copy.deepcopy(value)
                steps.append(role)
        require(len(steps) == len(set(steps)) == 42, "The actual LP evidence does not contain all 42 unique steps")
        require(self.member(self.record["protocol_bindings"]) == self.bindings, "Claimed bindings differ from actual prior responses")
        self.lp02(document)
        require(self.at("LP03/failure-retry") == self.at("LP03.02"), "Admission failure retry changed history")
        self.q03()
        self.lp05()
        self.protocol_steps = steps

    def lp02(self, document):
        inspect = self.at("LP02.02")[1]
        item = inspect["result"]["items"][0]
        authority = item["source"]["initializer_target"]
        request, response = self.at("LP02.05")
        patch = request["patches"][0]
        expected = document["protocol_cases"][1]["steps"][1]["expected"]
        require(len(inspect["result"]["items"]) == 1 and authority["available"] is True
                and authority["element_id"] == expected["initializer_target_element_id"]
                and authority["rendered_path"] == expected["rendered_path"] and patch == expected["expected_patch"],
                "Scoped repair differs from the inspected root initializer")
        span = authority["span"]
        require(patch["source_id"] == span["source_id"] and patch["source_revision"] == span["source_revision"]
                and span["start_byte"] <= patch["start_byte"] <= patch["end_byte"] <= span["end_byte"],
                "Scoped repair exceeds actual inspected source authority")
        old, new = self.sources.bundles["P13"], self.sources.bundles["P20"]
        require(self.sources.candidate(request).to_payload() == new.to_payload() and old.modules == new.modules,
                "Scoped repair did not preserve libraries and produce exact P20")
        siblings, units = [], []
        for role, case_id in (("LP02.08", "P13"), ("LP02.09", "P20")):
            query, reply = self.at(role)
            record = action_records(reply)
            require(len(record) == 1 and record[0]["candidate_only"] is False, "Historical/new source projection differs")
            wanted = self.sources.cases[case_id]["expected"]
            samples = [sample for sample in wanted["samples"] if sample["side"] == "after"
                       and Fraction(int(sample["time"]["numerator"]), int(sample["time"]["denominator"])) == Fraction(3, 2)]
            require(len(samples) == 1, "Missing frozen generated-arm sample")
            current = record[0]["current"]["value"]
            for key in ("joint_coordinates_rad", "joint_rates_rad_per_s"):
                frozen_equal(current[key], samples[0][key], (key,))
            frozen_equal(current["resolved_joint_targets_rad"], wanted["independent_solution"]["resolved_joint_targets_rad"],
                         ("resolved_joint_targets_rad",))
            step = next(step for step in document["protocol_cases"][1]["steps"] if step["id"] == role)
            require(len(step["required_evidence_reads"]) == 5, "Frozen sibling/source inventory changed")
            sibling, source_units = {}, {}
            program = self.sources.bundles[case_id]
            for index, evidence in enumerate(step["required_evidence_reads"]):
                q, r = self.at(f"{role}/evidence/{index}")
                require(q == resolve(evidence["request_template"], self.bindings, self.sources), "Sibling/source query was substituted")
                result, e = r["result"], evidence["expected"]
                require(r["status"] == "succeeded" and r["truncated"] is False and r["next_cursor"] is None
                        and len(result["items"]) == e["returned_item_count"], "Incomplete sibling/source evidence")
                if "canonical_length_m" in e:
                    returned = result["items"][0]
                    value = copy.deepcopy(returned["values"]["forearm_length"])
                    require(value["value"] == e["canonical_length_m"], "Untouched sibling value changed")
                    origin = value["origin"]
                    require(origin["source_id"] != "entry" and origin["source_revision"] == program.sources[origin["source_id"]].revision,
                            "Untouched sibling no longer has its pinned library origin")
                    for dependency in value["dependencies"]:
                        require(dependency.pop("program_revision") == program.program_revision, "Sibling dependency uses another source")
                    sibling[tuple(returned["element_id"])] = {"path": returned["path"], "identity": returned["identity"],
                        "value": value, **{key: returned["source"][key] for key in ("source_id", "source_revision", "definition_span")}}
                else:
                    source_units.update(complete_source_units(program, result["source_units"], e["exact_source_unit_identities"]))
            require(len(sibling) == len(source_units) == 4, "Missing four siblings or complete source closure")
            siblings.append(sibling)
            units.append({key: value for key, value in source_units.items() if key != "entry"})
        require(siblings[0] == siblings[1] and units[0] == units[1], "Scoped edit changed an untouched sibling/library")

    def workflow_result(self, name):
        rows = [row for row in self.record["workflow_roles"] if row["role"] == name]
        require(len(rows) == 1, "Missing or duplicate workflow record: " + name)
        row = rows[0]
        actual = self.member(row["record"])
        require(actual == {key: value for key, value in row.items() if key != "record"}, "Workflow role descriptor differs")
        return row["result"]

    def q03(self):
        default = self.at("LP04.03")[1]
        n = envelope_bound(default)
        require(n == self.bindings["LP04.N"] and n <= MAX_ENTRIES, "Q03 independent N differs")
        expected_paths = self.sources.cases["P24"]["expected"]["reach_action_paths"]
        require(len(expected_paths) == len(set(expected_paths)) == 128, "Frozen P24 action inventory differs")
        initial = self.at("LP04.01")[1]["result"]["initial_state"]["reaches"]
        require(set(initial) == set(expected_paths), "P24 construction omitted a named action")
        for role in ("LP04.03", "LP04.04"):
            q, r = self.at(role)
            items = r["result"]["items"]
            require({item["path"] for item in items} == set(expected_paths) and len(items) == 128
                    and len(action_records(r)) == 128 and r["truncated"] is False and r["next_cursor"] is None,
                    "Q03 omitted/duplicated/truncated a complete action group")
            require(envelope_bound(r) == n, "Q03 successful envelope changed its exact entry count")
        measured = self.member(self.workflow_result("LP04")["measurements"])
        require(measured["complete_response_entries"] == n and set(measured["requests"]) == {"LP04.03", "LP04.04", "LP04.05"},
                "Q03 transparent observation inventory differs")
        query_fields = ("program_revision", "run_id", "selector", "fields", "limit", "time")
        original = self.at("LP04.03")[0]
        for role, observation in measured["requests"].items():
            q, r = self.at(role)
            require({key: q[key] for key in query_fields} == {key: original[key] for key in query_fields}, "Q03 query changed")
            require(observation["prepared_statuses"] == ["succeeded"], "Q03 failed before complete successful preparation")
            constructors = observation["constructor_cumulative_entries"]
            materializations = observation["materialization_entry_counts"]
            require(constructors and all(type(value) is int and 0 < value < n for value in constructors), "Q03 exhausted an earlier constructor")
            require(materializations and all(item["kind"] in ("data", "json") and type(item["entries"]) is int
                        and 0 <= item["entries"] < n for item in materializations), "Q03 exhausted an earlier materializer")
            require({"status": "succeeded", "phase": "complete", "entries": n} in observation["complete_response_guards"],
                    "Q03 never reached the final complete-response guard")
        failed = self.at("LP04.05")[1]
        require(failed["result"] is None and failed["run_id"] is None, "Q03 final publication failure retained effects")
        tiny = self.at("LP04.06")[1]
        require({"OKL-E-RESOURCE", "OKA-E-RESOURCE"} & set(codes(tiny)), "Q03 tiny bound did not reach a real resource guard")
        require(len({self.at(role)[0]["request_id"] for role in ("LP04.03", "LP04.04", "LP04.05")}) == 3, "Q03 reused a cached request")
        self.q03_entries = n

    def lp05(self):
        candidate = self.at("LP05.02")[1]
        run_id = candidate["run_id"]
        require(candidate["result"]["run_state"]["candidate_only"] is True, "Candidate failure was accepted")
        current = action(self.at("LP05.09")[1])
        require(current["candidate_only"] is False and self.runs[(candidate["project_id"], run_id)]["candidate_only"] is True,
                "Later source acceptance rewrote the historical candidate marker")
        q, r = self.at("LP05/candidate-retry")
        require(q == self.at("LP05.02")[0] and r == candidate, "Candidate retry rewrote its historical receipt")

    def q22(self):
        probes = decode((DATA / "draft2-supplements/release-probes.json").read_bytes())["probes"]
        probe = next(row for row in probes if row["id"] == "Q22-same-project-repair-and-stale-history")
        for role, template, expected in (("Q22.01", "edit_request_template", "expected_edit"),
                                          ("Q22.02", "mismatch_request_template", "expected_mismatch"),
                                          ("Q22.03", "historical_control_request_template", "expected_historical_control")):
            q, r = self.at(role)
            frozen_request(q, probe[template], self.bindings, self.sources)
            self.expected(q, r, probe[expected])
        edit, reply = self.at("Q22.01")
        candidate = self.sources.candidate(edit)
        require(candidate.to_payload() == self.sources.bundles["L02"].to_payload()
                and candidate.modules == self.sources.bundles["L04"].modules, "Q22 did not produce exact L02 with unchanged libraries")
        failed_run = self.bindings["LP01.failed_run"]
        require(reply["run_id"] not in (failed_run, self.bindings["LP01.prefix_run"]), "Q22 repair reused a historical run")
        self.lifecycle_sample(self.at("Q22.03")[1], "L04", "0.5", "before", failed_run)
        authority_q, authority_r = self.at("Q22/authority")
        item = authority_r["result"]["items"][0]
        patch = edit["patches"][0]
        require(authority_q["project_id"] == edit["project_id"] and authority_q["program_revision"] == edit["expected_program_revision"]
                and item["element_id"] == patch["element_id"], "Q22 has no matching inspected source authority")
        require(any(span["source_id"] == patch["source_id"] and span["source_revision"] == patch["source_revision"]
                    and span["start_byte"] <= patch["start_byte"] <= patch["end_byte"] <= span["end_byte"]
                    for span in item["source"]["writable_spans"]), "Q22 patch exceeds inspected writable bytes")
        require(self.at("Q22/retry") == (edit, reply), "Q22 retry changed request/receipt")
        status_q, status_r = self.at("Q22/status")
        require(status_q["target_request_id"] == edit["request_id"] and status_r["result"]["target"] == reply, "Q22 status differs")
        self.workflow_result("Q22")

    def snapshots(self):
        labels = set()
        for row in self.record["snapshots"]:
            require(row["label"] not in labels, "Duplicate source snapshot label")
            labels.add(row["label"])
            bundle = self.sources.revisions.get(row["program_revision"])
            require(bundle is not None, "Snapshot identifies an unexpected source")
            require(self.member(row["bundle"]) == bundle.to_payload() and self.member(row["manifest"]) == bundle.manifest(),
                    "Retained source bundle/manifest differs from exact frozen bytes")
            require(len(row["units"]) == len(bundle.units), "Source snapshot omitted a unit")
            for actual, expected in zip(row["units"], bundle.units):
                wanted = {"source_id": expected.source_id, "source_revision": expected.revision,
                          "filename": expected.filename, "package_id": expected.package_id, "version": expected.version}
                require(all(actual.get(key) == value for key, value in wanted.items())
                        and self.member(actual["file"], binary=True) == expected.raw, "Source snapshot unit changed")
        required = {"LP01-L04", "LP02-P13", "LP02-P20", "LP03-N06", "LP03-P10", "LP05-N06",
                    "Q22-original-L04", "Q22-repaired-L02", "Q02-P23-after-cancel", "P01", "P11", "P16", "P17", "L01", "L03"}
        require(labels == required, "Required retained source snapshot closure differs")

    def retained_runs(self):
        required = {"LP01-failure", "LP02-old-run", "LP03-failure", "LP04-P24", "LP05-candidate", "Q22-old-failure",
                    "L04-post-delivery-failed", "P01-after-delivery-failures", "Q02-prior-P01-run"}
        required.update(case_id + "-prior-to-delivery" for case_id in CASES)
        actual = {path.stem for path in (self.root / "retained-runs").glob("*.json")}
        require(actual == required, "Retained run evidence inventory differs")
        for label in sorted(required):
            row = self.read("retained-runs/" + label + ".json")
            key = (row["project_id"], row["run_id"])
            require(key in self.runs, "Retained history identifies an unknown run")
            retained_run(row, self.runs[key], self.run_versions[key])
            self.retained[label] = row

    def retrieve(self, description, export_role, artifact=None):
        q, r = self.at(export_role)
        closure = self.member(description) if "path" in description else description
        for role in closure["chunk_roles"]:
            self.at(role)
            require(self.exchanges[role][2]["sequence"] > self.exchanges[export_role][2]["sequence"], "Chunk read preceded its export")
        raw = joined_chunks(self.exchanges, closure, q, r)
        if artifact is not None:
            require(self.member(artifact, binary=True) == raw, "Saved artifact differs from actual reassembled chunks")
        return raw

    def deliveries(self):
        rows = self.record["deliveries"]
        require(len(rows) == 10 and {row["case_id"] for row in rows} == set(CASES), "The ten required Agent deliveries are incomplete")
        self.delivered = {}
        for row in rows:
            case_id, role = row["case_id"], row["export_role"]
            require(role == case_id + "/export", "Delivery export role was substituted")
            q, r = self.at(role)
            bundle = self.sources.bundles[case_id]
            options = row["options"]
            require(set(options) == {"end", "fps", "helpers", "position_tolerance_m", "rotation_tolerance_rad", "time_tolerance_s"}
                    and options["end"] == ENDS.get(case_id, "3") and options["fps"] == 1 and options["helpers"] is False,
                    "Agent corpus request settings differ from the declared finite execution")
            for name, upper in (("position_tolerance_m", .001), ("rotation_tolerance_rad", .001), ("time_tolerance_s", .000001)):
                require(type(options[name]) in (int, float) and 0 < options[name] <= upper, "Delivery tolerance was weakened")
            require(q == {"schema_version": PROTOCOL, "project_id": row["project_id"], "request_id": q["request_id"],
                          "operation": "export", "program_revision": bundle.program_revision, "destination": TARGET,
                          "options": options}, "Actual export request differs from the frozen case/settings")
            require(row["source_files"] == self.sources.paths[case_id]
                    and row["program_revision"] == bundle.program_revision, "Delivery source case differs")
            require(row["source_snapshot"] in self.record["snapshots"]
                    and row["source_snapshot"]["project_id"] == q["project_id"]
                    and row["source_snapshot"]["program_revision"] == bundle.program_revision,
                    "Delivery source snapshot belongs to another project or program")
            manifest = read_raw(ROOT / row["source_files"])
            require(row["source_manifest"] == descriptor(manifest, row["source_files"]), "Delivery source file descriptor differs")
            result = r["result"]
            require(r["status"] == "succeeded" and r["achieved_level"] == "delivered"
                    and result["destination"] == TARGET and r["program_revision"] == result["program_revision"] == bundle.program_revision,
                    "Explicit delivery/source binding was not achieved")
            require(row["run_id"] == r["run_id"] and row["artifact_id"] == result["artifact_id"]
                    and row["accepted_program_revision"] == r["accepted_program_revision"], "Delivery row does not identify the actual receipt")
            require(self.member(row["export_report"]) == result["report"]
                    and result["report"]["program_revision"] == bundle.program_revision
                    and result["report"]["source_code_sha256"] == self.implementation["source_code_sha256"][7:],
                    "Export report source/implementation differs")
            require(result["report"]["validation"]["status"] == "passed", "Exporter did not validate its supplied bytes")
            run = result["run_state"]
            require(run["status"] == "ready" and run["failure"] is None and run["candidate_only"] is False
                    and run["valid_until_seconds"] == options["end"] and run["valid_until_side"] == "after"
                    and Fraction(result["report"]["sampling"]["end_seconds"]) == Fraction(options["end"]),
                    "Delivery used the wrong or failed prefix")
            prior = row["prior_run_id"]
            require(type(prior) is str and prior != r["run_id"]
                    and (q["project_id"], prior) in self.runs, "Delivery did not use a fresh separate run")
            require(row["prior_workflow_roles"] and all(self.exchanges[name][2]["sequence"] < self.exchanges[role][2]["sequence"]
                    for name in row["prior_workflow_roles"]), "Delivery preceded its actual source workflow")
            if case_id in ("P01", "P11", "P16", "P17", "L01", "L03"):
                cq, cr = self.at(case_id + "/create")
                eq, er = self.at(case_id + "/evaluate")
                require(cq["bundle"] == bundle.to_payload() and cq["requested_level"] == "constructed" and cq["project_id"] == q["project_id"]
                        and cr["status"] == "succeeded" and eq["operation"] == "evaluate"
                        and eq["project_id"] == q["project_id"] and eq["program_revision"] == bundle.program_revision
                        and eq["until_seconds"] == options["end"] and eq["run_id"] is None
                        and er["status"] == "succeeded" and er["run_id"] == prior, "Missing actual source construction/evaluation before delivery")
            if case_id == "P13":
                require(prior == self.bindings["LP02.old_run"], "P13 delivery lost its pre-repair run")
            elif case_id == "P20":
                require(prior == self.bindings["LP02.new_run"], "P20 delivery lost its actual repaired run")
            elif case_id == "L02":
                require(prior == self.at("Q22.01")[1]["run_id"], "L02 delivery did not use the actual same-project repair")
            elif case_id == "L04":
                require(q["request_id"] == "L04-release.01" and q["project_id"] == "reach-reconstruction-lp01"
                        and prior == self.bindings["LP01.prefix_run"] == self.bindings["LP01.reset_run"]
                        and r["run_id"] != self.bindings["LP01.failed_run"]
                        and r["accepted_program_revision"] == bundle.program_revision,
                        "L04 recovery substituted source, failed run or reset/prefix history")
                require(self.exchanges["LP01.09"][2]["sequence"] < self.exchanges[role][2]["sequence"]
                        < self.exchanges["Q22.01"][2]["sequence"], "L04 was not delivered between actual recovery and same-project repair")
            raw = self.retrieve(row["retrieval"], role, row["artifact"])
            if case_id == "L04":
                closure = self.member(row["retrieval"])
                require(all(self.exchanges[name][2]["sequence"] < self.exchanges["Q22.01"][2]["sequence"]
                            for name in closure["chunk_roles"]), "L04 recovery retrieval did not finish before the same-project repair")
            require(result["artifact_id"] == "artifact:" + hashlib.sha256(raw).hexdigest(), "Artifact content identity differs")
            receipt = self.member(row["request_result"])
            require(receipt == {key: value for key, value in row.items() if key != "request_result"}, "Delivery row was changed after recording")
            self.delivered[case_id] = row

    def delivery_failures(self):
        q, r = self.at("P01/export")
        require(self.at("delivery/exact-retry") == (q, r), "Export retry changed request or receipt")
        collision_q, collision_r = self.at("delivery/changed-request-id")
        changed = copy.deepcopy(q)
        changed["options"]["fps"] += 1
        require(collision_q == changed, "Changed-payload collision probe was substituted")
        failure(collision_r, "OKL-E-REQUEST-ID")
        sq, sr = self.at("delivery/status")
        require(sq["project_id"] == q["project_id"] and sq["target_request_id"] == q["request_id"]
                and sr["result"]["target"] == r, "Export status does not reconcile immutable delivery")
        for role in ("delivery/foreign-artifact", "delivery/invalid-offset"):
            iq, ir = self.at(role)
            failure(ir, "OKA-E-ARTIFACT")
            require(iq["artifact_id"] == r["result"]["artifact_id"], "Invalid retrieval probe names another artifact")
            if role.endswith("foreign-artifact"):
                require(iq["project_id"] != q["project_id"], "Foreign-project retrieval stayed in original project")
            else:
                require(iq["project_id"] == q["project_id"] and iq["offset"] == r["result"]["total_bytes"] + 1,
                        "Invalid-offset probe used a valid byte interval")
        generic_q, generic_r = self.at("delivery/generic-level")
        require(generic_q["operation"] == "validate" and generic_q["requested_level"] == "delivered"
                and "destination" not in generic_q, "Generic-level probe acquired a destination")
        failure(generic_r, "OKL-E-CAPABILITY-UNSUPPORTED")
        for case_id, end, boundary in (("P17", "4", "3"), ("L04", "2", "0.5")):
            fq, fr = self.at(case_id + "/full-failure")
            failure(fr, "OKL-E-REACH")
            require(fq["operation"] == "export" and fq["destination"] == TARGET
                    and fq["program_revision"] == self.sources.bundles[case_id].program_revision
                    and fq["options"]["end"] == end and fq["options"]["fps"] == 1 and fq["options"]["helpers"] is False,
                    "Full-prefix failure probe was substituted")
            run = fr["result"]["run_state"]
            require(run["status"] == "failed" and run["valid_until_seconds"] == boundary and run["valid_until_side"] == "before"
                    and any(item.get("details", {}).get("reach_code") == "reach_unreachable" for item in fr["diagnostics"]),
                    "Full request failed for the wrong reason or boundary")
            path = "cases/" + case_id + "/retrieval-after-failure.json"
            closure = self.read(path)
            require(all(self.exchanges[role][2]["sequence"] > self.exchanges[case_id + "/full-failure"][2]["sequence"]
                        for role in closure["chunk_roles"]), "Retained artifact was retrieved before the later failure")
            self.retrieve(closure, case_id + "/export", self.delivered[case_id]["artifact"])
        nq, nr = self.at("N06/selected-branch-delivery-failure")
        failure(nr, "OKL-E-REACH")
        require(nq["project_id"] == "reach-reconstruction-lp03" and nq["program_revision"] == self.sources.bundles["N06"].program_revision
                and nq["destination"] == TARGET and nq["options"] == {"end": "0.25", "fps": 1, "helpers": False}
                and any(item.get("details", {}).get("reach_code") == "reach_limit" for item in nr["diagnostics"]),
                "Selected-branch delivery failure was substituted")
        self.workflow_result("delivery-failures")

    def q02(self):
        cq, cr = self.at("Q02/create-P23")
        q, r = self.at("Q02/export")
        revision = self.sources.bundles["P23"].program_revision
        require(cq["bundle"] == self.sources.bundles["P23"].to_payload() and cr["status"] == "succeeded"
                and cr["accepted_program_revision"] == revision and q["program_revision"] == revision
                and cq["project_id"] == q["project_id"] and q["operation"] == "export"
                and q["destination"] == TARGET and q["options"] == {"end": "0.25", "fps": 1, "helpers": False},
                "Q02 did not request the actual accepted P23 quarter prefix")
        require(r["status"] == "cancelled" and r["run_id"] is None and r["result"] is None
                and r["achieved_level"] is None and r["accepted_program_revision"] == revision,
                "Q02 exposed interrupted delivery effects")
        progress = r["progress"]
        require(progress["cancellation_requested"] is True and progress["phase"] == "cancelled_before_commit",
                "Q02 cancelled before work rather than during planning")
        outer = self.exchanges["Q02/export"][2]
        for role in ("Q02/running-status", "Q02/cancel"):
            iq, ir = self.at(role)
            inner = self.exchanges[role][2]
            require(iq["project_id"] == q["project_id"] and iq["target_request_id"] == q["request_id"]
                    and ir["status"] == "succeeded" and ir["result"]["target_status"] == "running",
                    "Q02 control did not observe the actual running export")
            target = ir["result"]["target"]
            require(target["request_id"] == q["request_id"] and target["project_id"] == q["project_id"]
                    and target["accepted_program_revision"] == revision and target["run_id"] is None
                    and target["result"] is None and target["achieved_level"] is None,
                    "Q02 exposed uncommitted state while the export was running")
            require(datetime.fromisoformat(outer["started_at"]) <= datetime.fromisoformat(inner["started_at"])
                    <= datetime.fromisoformat(inner["finished_at"]) <= datetime.fromisoformat(outer["finished_at"]),
                    "Q02 control did not occur inside the export interval")
        require(self.at("Q02/cancel")[1]["result"]["disposition"] == "cancellation_requested", "Q02 did not request cancellation of running work")
        require(self.at("Q02/exact-retry") == (q, r), "Q02 retry changed the cancelled receipt")
        tq, tr = self.at("Q02/terminal-status")
        require(tq["target_request_id"] == q["request_id"] and tr["result"]["target"] == r, "Q02 status changed the cancelled receipt")
        order = [self.exchanges[role][2]["sequence"] for role in
                 ("Q02/export", "Q02/running-status", "Q02/cancel", "Q02/terminal-status", "Q02/exact-retry")]
        require(order == sorted(set(order)), "Q02 control/terminal/retry order differs")
        record = self.member(self.workflow_result("Q02")["cancellation"])
        require(record["actual_source_case"] == "P23" and record["program_revision"] == revision
                and len(record["observations"]) == 1, "Q02 actual planning observation is missing")
        observation = record["observations"][0]
        work = observation["work"]
        require(observation["stage"] == "planning_phase" and type(observation["work_operations"]) is int
                and type(work["operations"]) is int and 0 < observation["work_operations"] == work["operations"] <= 100000
                and type(work["cache_entries"]) is int and 0 <= work["cache_entries"] <= 256
                and all(type(value) is int and value > 0 for value in work["counts"].values())
                and work["counts"].get("recording_boundary_preflight", 0) > 0
                and sum(work["counts"].values()) == work["operations"], "Q02 did not reach bounded accepted planning")
        closure = record["prior_artifact_retrieval"]
        require(all(self.exchanges[role][2]["sequence"] > self.exchanges["Q02/terminal-status"][2]["sequence"]
                    for role in closure["chunk_roles"]), "Prior artifact was not actually retrieved after cancellation")
        self.retrieve(closure, "P01/export", self.delivered["P01"]["artifact"])

    def store(self):
        """Reconcile every retained row, never invoking production store code.

        The writer must be closed and checkpointed. An active WAL is rejected;
        immutable=1 therefore cannot silently hide uncheckpointed effects.
        """
        path = safe_path(self.root, STORE_NAME)
        for suffix in ("-wal", "-journal"):
            sidecar = path.with_name(path.name + suffix)
            require(not sidecar.exists() or (not sidecar.is_symlink() and sidecar.stat().st_size == 0),
                    "Close/checkpoint the actual service store before independent audit")
        receipt = file_identity(path, STORE_NAME)
        self.files[STORE_NAME] = receipt
        expected_sources = set()
        for (project, _), (q, r) in self.ledger.items():
            if q["operation"] == "create":
                expected_sources.add((project, load_bundle(q["bundle"]).program_revision))
            elif q["operation"] == "edit" and r.get("program_revision") not in (None, q["expected_program_revision"]):
                candidate = self.sources.candidate(q)
                require(candidate.program_revision == r["program_revision"], "Retained edit candidate differs from its actual bytes")
                expected_sources.add((project, candidate.program_revision))
        connection = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            require(connection.execute("PRAGMA quick_check").fetchall()[0][0] == "ok", "Closed SQLite store failed integrity checking")
            schema = connection.execute("SELECT value FROM metadata WHERE name='schema_version'").fetchone()
            require(schema is not None and schema[0] == STORE_SCHEMA, "Wrong isolated Agent store schema")
            sessions = connection.execute("SELECT closed FROM sessions").fetchall()
            require(sessions and all(row[0] == 1 for row in sessions), "The retained store has an open service session")
            actual_heads = {row["id"]: row["accepted_revision"] for row in connection.execute("SELECT id,accepted_revision FROM projects")}
            require(actual_heads == self.heads, "Closed store accepted heads differ from actual transaction history")
            requests = connection.execute("SELECT * FROM requests ORDER BY sequence").fetchall()
            require(len(requests) == len(self.ledger), "Closed store has hidden or missing request identities")
            seen = set()
            for row in requests:
                key = (row["project_id"], row["id"])
                require(key in self.ledger and key not in seen, "Closed store request is absent from actual trace")
                seen.add(key)
                q, r = self.ledger[key]
                require(row["operation"] == q["operation"] and row["digest"] == hashlib.sha256(canonical(q)).hexdigest()
                        and decode(row["payload"].encode("utf-8"), envelope=True) == q
                        and decode(row["response"].encode("utf-8"), envelope=True) == r
                        and row["state"] == r["status"] and row["owner"] is None
                        and decode(row["engine"].encode("utf-8")) == self.implementation,
                        "Closed store changed request, terminal receipt, engine or owner")
                require(row["state"] in ("succeeded", "failed", "rejected", "cancelled"), "Nonterminal store request")
                expected_cancel = int(key == (self.at("Q02/export")[0]["project_id"], self.at("Q02/export")[0]["request_id"]))
                require(row["cancel_requested"] == expected_cancel, "Durable cancellation flag differs from actual cancel request")
            rows = connection.execute("SELECT * FROM sources").fetchall()
            require({(row["project_id"], row["revision"]) for row in rows} == expected_sources, "Hidden or missing immutable source snapshot")
            for row in rows:
                key = (row["project_id"], row["revision"])
                require(row["revision"] in self.sources.revisions and row["filename"] == "<program-bundle>", "Unbound store source")
                bundle = self.sources.revisions[row["revision"]]
                require(decode(bytes(row["raw"])) == bundle.to_payload() and row["accepted_once"] == int(key in self.accepted),
                        "Stored source bytes or acceptance history changed")
            rows = connection.execute("SELECT * FROM runs").fetchall()
            require({(row["project_id"], row["id"]) for row in rows} == set(self.runs), "Hidden or missing committed run")
            for row in rows:
                key = (row["project_id"], row["id"])
                require(decode(row["descriptor"].encode("utf-8")) == self.runs[key]
                        and row["version"] == self.run_versions[key]
                        and row["source_revision"] == self.runs[key]["program_revision"]
                        and (row["project_id"], row["source_revision"]) in expected_sources,
                        "Retained run/version/source differs")
            artifact_keys = {(row["project_id"], row["id"]) for row in connection.execute("SELECT project_id,id FROM artifacts")}
            require(artifact_keys == set(self.artifacts) and len(artifact_keys) == 10, "Hidden, missing or failed-request artifact")
            for key in sorted(artifact_keys):
                row = connection.execute("SELECT * FROM artifacts WHERE project_id=? AND id=?", key).fetchone()
                q, r = self.artifacts[key]
                raw, result = bytes(row["data"]), r["result"]
                require(0 < len(raw) == result["total_bytes"] <= MAX_MEMBER and sha(raw) == row["sha256"] == result["sha256"]
                        and row["source_revision"] == q["program_revision"]
                        and decode(row["report"].encode("utf-8")) == result["report"], "Closed store artifact bytes/report/source differ")
            q02 = self.at("Q02/export")[0]["project_id"]
            require(not any(key[0] == q02 for key in self.runs) and not any(key[0] == q02 for key in self.artifacts),
                    "Accepted-work cancellation committed a run or artifact")
            p24 = self.at("LP04.02")[0]["project_id"]
            require(sum(key[0] == p24 for key in self.runs) == 1 and not any(key[0] == p24 for key in self.artifacts),
                    "Q03 result-budget inspection changed run/artifact effects")
            self.store_counts = {"projects": len(actual_heads), "requests": len(requests), "sources": len(expected_sources),
                                 "runs": len(self.runs), "artifacts": len(artifact_keys), "closed_sessions": len(sessions)}
        finally:
            connection.close()
        require(file_identity(path, STORE_NAME) == receipt, "Read-only store audit changed or raced retained evidence")

    def input_cut(self):
        before, after = self.read("inputs-before.json"), self.read("inputs-after.json")
        require(before == after, "Producer tracked inputs changed during execution")
        identity = source_identity()
        require(before["git"] == {**identity, "status": ""}
                and self.record["source_commit"] == identity["commit"] and self.record["source_tree"] == identity["tree"],
                "Producer and auditor source cuts differ; an explicit input-equivalence audit is required")
        names = sorted(name for name in subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"]).decode().split("\0") if name)
        rows = before["files"]
        require([row["path"] for row in rows] == names, "Producer input manifest omits tracked files")
        for row in rows:
            require(descriptor(read_raw(safe_path(ROOT, row["path"]), maximum=MAX_MEMBER), row["path"]) == row,
                    "Current tracked bytes differ from producer inputs: " + row["path"])
        self.source_cut = identity

    def audit(self):
        self.record = self.read("producer-record.json")
        require(self.record["schema_version"] == "ontokin.reach-agent-delivery-workflow/0.1"
                and self.record["protocol"] == PROTOCOL and self.record["target_contract"] == TARGET
                and self.record["source_kind"] == "agent_retrieved_artifact", "Unsupported producer contract")
        require(self.record["implementation"] == self.implementation, "Producer implementation source bytes differ")
        self.input_cut()
        for name, field in (("protocol-cases.json", "protocol_inputs"), ("release-probes.json", "release_probe_inputs")):
            path = DATA / "draft2-supplements" / name
            require(self.record[field] == descriptor(path.read_bytes(), path.relative_to(ROOT).as_posix()), "Frozen protocol/probe input differs")
        self.trace(self.record["exchanges"])
        q, r = self.at("discovery")
        require(q["operation"] == "discover" and q["profile"] == "planar-reach-0.1" and r["status"] == "succeeded", "Actual reach discovery is absent")
        self.protocol()
        self.q22()
        self.snapshots()
        self.deliveries()
        self.delivery_failures()
        self.q02()
        self.retained_runs()
        self.store()
        for role in ("discovery", "LP01", "LP02", "LP03", "LP05"):
            self.workflow_result(role)
        require({row["role"] for row in self.record["workflow_roles"]}
                == {"discovery", "LP01", "LP02", "LP03", "LP04", "LP05", "Q22", "Q02", "delivery-failures"},
                "Unexpected or missing workflow role")
        require(self.used == set(self.exchanges), "Unchecked actual exchange roles: " + str(sorted(set(self.exchanges) - self.used)))
        for name, receipt in list(self.files.items()):
            path = safe_path(self.root, name)
            actual = file_identity(path, name) if name == STORE_NAME else descriptor(read_raw(path), name)
            require(actual == receipt, "Audited evidence changed during verification")
        require(source_identity() == self.source_cut and implementation() == self.implementation, "Audit implementation changed during verification")
        return {"source_cut": self.source_cut, "implementation": self.implementation,
                "frozen_protocol_steps": self.protocol_steps, "frozen_protocol_step_count": len(self.protocol_steps),
                "additional_sibling_source_reads": len([role for role in self.used if role.startswith(("LP02.08/evidence/", "LP02.09/evidence/"))]),
                "q03_complete_response_entries": self.q03_entries,
                "q02_accepted_work_cancellation": "passed", "q22_same_project_repair": "passed",
                "actual_exchange_count": len(self.exchanges), "complete_projection_schema_checks": self.projections,
                "retrieved_cases": list(CASES), "closed_store": self.store_counts,
                "verification_packages": self.schemas.packages, "schema_hashes": self.schemas.hashes,
                "evidence_members": [self.files[name] for name in sorted(self.files)]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", type=Path, help="Complete actual producer directory, including its closed service store")
    parser.add_argument("--output", type=Path, required=True, help="Fresh report outside the checkout and evidence directory")
    args = parser.parse_args(argv)
    output = args.output.absolute()
    require(not output.exists() and not output.resolve().is_relative_to(ROOT)
            and not output.resolve().is_relative_to(args.workflow.resolve()), "Use a fresh external audit output")
    for path in (output, *output.parents):
        require(not path.is_symlink(), "Audit output cannot use symlink components")
    report = {"schema_version": "ontokin.reach-agent-delivery-audit/0.1", "status": "running",
              "scope": "42 frozen LP steps, Q02/Q03/Q22, ten deliveries, actual retrieval and closed-store transactions",
              "started_at": datetime.now(timezone.utc).isoformat(), "provider": "local",
              "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
              "execution": {"python": sys.version, "executable": sys.executable},
              "agent_transport_audited": False, "native_validation": "not_established_by_this_audit",
              "browser_validation": "not_established_by_this_audit", "rate_acceptance": "separate_gate",
              "release_acceptance": False, "full_product_goal_completed": False}
    reader = None
    try:
        reader = Reader(args.workflow)
        report.update(reader.audit(), status="passed", agent_transport_audited=True)
    except Exception as error:
        report.update(status="failed", failure={"type": type(error).__name__, "message": str(error)})
        if reader is not None:
            report["partial_evidence_members"] = [reader.files[name] for name in sorted(reader.files)]
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write((json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "output": str(output), "failure": report.get("failure")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
