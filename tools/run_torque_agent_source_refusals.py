#!/usr/bin/env python3
"""Execute every frozen source refusal through its actual versioned Agent.

The original frozen source/asset bytes and expected diagnostics are retained.
Only the separately published n28 span amendment is applied to a detached
expectation. The .21 case uses the actual inherited .21 service.
"""
from __future__ import annotations

import argparse
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


ROOT = Path(__file__).resolve().parents[1]
FREEZE_SHA = "98df30158c0cd77c542d89652f5dec6b585d03451a06bf7b1baffee0fc2f02eb"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--schema-root", type=Path, default=ROOT)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.source_root = args.source_root.resolve()
    args.output.mkdir()
    sys.path.insert(0, str(args.source_root))
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from ontokin.agent_store import dumps
    from ontokin.execution_budget import HostPolicy
    from ontokin.keyed_membership_agent import KeyedMembershipAgentService
    from ontokin.keyed_membership_protocol import KeyedMembershipProtocol
    from ontokin.texture_bundle import load_texture_file_manifest, load_texture_bundle
    from ontokin.torque_agent import TorqueAgentService
    from ontokin.torque_protocol import TorqueProtocol

    frozen = args.source_root / "docs/language-design/torque-v0.1/freeze"
    manifest_path = frozen.parent / "INPUT-FREEZE.json"
    assert sha(manifest_path.read_bytes()) == FREEZE_SHA
    frozen_paths = {row["path"]: row for row in read(manifest_path)["files"]}
    table_path = frozen / "refusal-cases.json"
    cases = [case for case in read(table_path)["cases"]
             if case["expected"]["phase"] not in ("admission", "evaluation")]
    assert len(cases) == 18
    amendment_dir = args.source_root / "docs/language-design/torque-amendments/c091-grouped-expression-span"
    amendment = read(amendment_dir / "AMENDMENT.json")
    publication = read(amendment_dir / "PUBLICATION.json")
    assert publication["status"] == "passed"
    assert publication["actual_remote_contents_and_modes_equal"]
    assert publication["independent_review_passed"] and publication["frozen_original_unchanged"]
    assert amendment["frozen_manifest_sha256"] == FREEZE_SHA
    assert amendment["original_table"]["sha256"] == sha(table_path.read_bytes())
    for name in ("ADOPTION.md", "AMENDMENT.json", "INDEPENDENT-REVIEW.json"):
        path = amendment_dir / name
        row = next(row for row in publication["files"] if row["path"] == path.relative_to(args.source_root).as_posix())
        assert row["bytes"] == path.stat().st_size and row["sha256"] == sha(path.read_bytes())
    resources = {}
    for path in (args.schema_root / "docs/language-design").rglob("*.schema.json"):
        value = read(path)
        if "$id" in value:
            resources[value["$id"]] = Resource.from_contents(value)
    registry = Registry().with_resources(resources.items())
    validators = {version: {kind: Draft202012Validator(read(args.schema_root /
        f"docs/language-design/agent-v{version}/{kind}.schema.json"), registry=registry)
        for kind in ("request", "response")} for version in ("0.21", "0.22")}
    write(args.output / "implementation.json", {
        "head": subprocess.check_output(["git", "-C", str(args.source_root), "rev-parse", "HEAD"], text=True).strip(),
        "source_root": str(args.source_root), "python": sys.version, "platform": sys.platform,
        "runtime": {str(path.relative_to(args.source_root)): sha(path.read_bytes())
                    for path in sorted((args.source_root / "ontokin").glob("*.py"))},
        "harness_sha256": sha(Path(__file__).read_bytes()), "argv": sys.argv,
        "frozen_manifest_sha256": FREEZE_SHA, "table_sha256": sha(table_path.read_bytes()),
        "amendment_sha256": sha((amendment_dir / "AMENDMENT.json").read_bytes()),
        "host_policy": {"max_operations": 1000000, "max_elapsed_ms": 30000},
        "source_budgets": "Exact frozen inputs; no source or caller allowance changes"})

    results = []
    for case in cases:
        directory = args.output / case["id"]
        directory.mkdir()
        checks, exchanges = 0, []
        service = None
        result = {"case": case["id"], "status": "running"}
        started = time.monotonic()
        def check(condition, message):
            nonlocal checks
            checks += 1
            if not condition:
                raise AssertionError(message)
        def load(filename):
            path = frozen / filename
            files = read(path)
            members = [path] + [path.parent / item["path"]
                               for item in [files["entry"], *files["modules"], *files["assets"]]]
            for member in members:
                relative = member.resolve().relative_to(args.source_root).as_posix()
                expected = frozen_paths[relative]
                raw = member.read_bytes()
                check(len(raw) == expected["bytes"] and sha(raw) == expected["sha256"], "Exact frozen member: " + relative)
            return load_texture_file_manifest(path)
        try:
            inherited = case["id"] == "n19-earlier-profile"
            version = "0.21" if inherited else "0.22"
            service_type = KeyedMembershipAgentService if inherited else TorqueAgentService
            protocol = KeyedMembershipProtocol if inherited else TorqueProtocol
            policy = HostPolicy(max_operations=1000000, max_elapsed_ms=30000)
            program = load(case["file_manifest"])
            control = load("control-spin-up.files.json" if inherited else "p01-spin-up.files.json")
            check(program.program_revision == case["identity"]["program_revision"], "Exact frozen negative program identity")
            check(program.manifest() == case["identity"]["manifest"], "Exact frozen negative dependency/asset closure")
            expected = copy.deepcopy(case["expected"])
            if case["id"] == amendment["case_id"]:
                check(expected["primary_source"] == amendment["original"], "Published n28 amendment exact original precondition")
                expected["primary_source"] = copy.deepcopy(amendment["replacement"])
            write(directory / "effective-expectation.json", expected)
            service = service_type(directory / "store", host_policy=policy)
            def send(request):
                clean, payload = protocol.canonical_request(request)
                validators[version]["request"].validate(clean)
                response = service.handle(clean)
                exchanges.append({"index": len(exchanges)+1, "request": clean,
                                  "request_canonical_sha256": sha(payload.encode()), "response": response})
                validators[version]["response"].validate(response)
                return response
            def create(project, request_id, bundle):
                return {"schema_version": "ontokin.agent/"+version, "project_id": project,
                        "request_id": request_id, "operation": "create", "bundle": bundle.to_payload(),
                        "expected_program_revision": None, "requested_level": "constructed"}
            control_request = create("unchanged-control", "control-create", control)
            control_response = send(control_request)
            check(control_response["status"] == "succeeded", "Actual unchanged positive control constructs")
            check(control_response["accepted_program_revision"] == control.program_revision, "Control accepted exact source")
            with service._store.connection() as db:
                before_control = db.execute("SELECT accepted_revision FROM projects WHERE id='unchanged-control'").fetchone()[0]
                before_raw = bytes(db.execute("SELECT raw FROM sources WHERE project_id='unchanged-control'").fetchone()[0])
            request = create(case["id"], "frozen-source-refusal", program)
            response = send(request)
            check(len(response["diagnostics"]) == 1, "One original source diagnostic is returned")
            diagnostic = response["diagnostics"][0]
            check(response["status"] == ("failed" if diagnostic["category"] in ("numerical_failure", "resource_limit") else "rejected"),
                  "Actual inherited diagnostic category determines terminal refusal")
            check(response["program_revision"] == program.program_revision, "Refusal binds complete immutable program")
            check(response["accepted_program_revision"] is None and response["run_id"] is None, "Refused source publishes no acceptance or run")
            for name in ("code", "message", "phase"):
                if name in expected:
                    check(diagnostic[name] == expected[name], "Exact frozen diagnostic " + name)
            primary = diagnostic["primary"]
            for name, value in expected["primary_source"].items():
                if name != "text":
                    check(primary[name] == value, "Exact frozen primary " + name)
            unit = program.sources[primary["source_id"]]
            check(unit.raw[primary["start_byte"]:primary["end_byte"]].decode() == expected["primary_source"]["text"], "Exact original source span bytes")
            for name, value in expected.get("required_details", {}).items():
                check(diagnostic["details"][name] == value, "Exact frozen diagnostic detail " + name)
            if "diagnostic_projection" in expected:
                check(diagnostic == expected["diagnostic_projection"], "Entire inherited diagnostic projection stays unchanged")
            if "required_related" in expected:
                related = diagnostic["related"]
                check(bool(related), "Duplicate-key diagnostic retains its actual earlier source location")
                locations = [item.get("location", item) for item in related]
                check(any(location.get("source_id") == primary["source_id"] and location.get("start_byte", primary["start_byte"]) < primary["start_byte"]
                          for location in locations), "Related location is the earlier declaration")
            database_path = service.database_path
            service.close()
            service = service_type(directory / "store", host_policy=policy)
            check(send(request) == response, "Reopen and same-ID retry returns the exact durable refusal")
            check(send(control_request) == control_response, "Unchanged accepted control retains its historical exact receipt")
            service.close()
            service = None
            database_before = sha(database_path.read_bytes())
            with sqlite3.connect("file:"+str(database_path)+"?mode=ro", uri=True) as db:
                check(db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "Closed SQLite integrity")
                check(db.execute("SELECT accepted_revision FROM projects WHERE id='unchanged-control'").fetchone()[0] == before_control, "Control accepted pointer unchanged")
                check(bytes(db.execute("SELECT raw FROM sources WHERE project_id='unchanged-control'").fetchone()[0]) == before_raw, "Control exact source and asset bytes unchanged")
                check(db.execute("SELECT accepted_revision FROM projects WHERE id=?", (case["id"],)).fetchone()[0] is None, "Closed store confirms no failed-source acceptance")
                check(db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0 and db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0, "Source refusals create no runs or artifacts")
                for revision, raw, accepted in db.execute("SELECT revision,raw,accepted_once FROM sources"):
                    bundle = load_texture_bundle(json.loads(raw))
                    check(bundle.program_revision == revision, "Independent stored source/asset identity")
                    check(bool(accepted) == (revision == control.program_revision), "Only the unchanged control was accepted")
                rows = list(db.execute("SELECT project_id,id,operation,payload,digest,response,state FROM requests ORDER BY sequence"))
                check(len(rows) == 2, "Retries create no extra durable requests")
                for project, ident, operation, payload, hashed, stored_response, state in rows:
                    original = next(row for row in exchanges if row["request"]["project_id"] == project and row["request"]["request_id"] == ident)
                    check(sha(payload.encode()) == hashed == original["request_canonical_sha256"], "Exact canonical request digest in SQLite")
                    check(json.loads(payload) == original["request"] and json.loads(stored_response) == original["response"], "Actual retained exchange equals its durable row")
                    check(operation == "create" and state == original["response"]["status"], "Durable operation and terminal state")
            check(sha(database_path.read_bytes()) == database_before, "Independent closed-store audit did not mutate SQLite")
            write(directory / "sqlite-observation.json", {"path": str(database_path), "sha256": database_before,
                "bytes": database_path.stat().st_size, "requests": 2, "exchanges": len(exchanges),
                "control_revision": control.program_revision, "negative_revision": program.program_revision,
                "control_unchanged": True, "negative_accepted": False})
            result["status"] = "passed"
        except BaseException as error:
            result.update(status="failed", error=repr(error), traceback=traceback.format_exc())
        finally:
            if service is not None:
                service.close()
            with gzip.open(directory / "exchanges.jsonl.gz", "wt", encoding="utf-8") as stream:
                for exchange in exchanges:
                    stream.write(dumps(exchange)+"\n")
            result.update(checks=checks, exchanges=len(exchanges), elapsed_seconds=time.monotonic()-started)
            write(directory / "result.json", result)
            results.append(result)
            print(json.dumps({key: value for key, value in result.items() if key != "traceback"}), flush=True)
    passed = all(result["status"] == "passed" for result in results)
    write(args.output / "summary.json", {"status": "passed" if passed else "failed", "cases": len(results),
        "checks": sum(result["checks"] for result in results), "exchanges": sum(result["exchanges"] for result in results),
        "results": results, "scope": "All 18 source-phase refusal cases via actual versioned Agent; runtime and delivery refusals remain separately identified"})
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
