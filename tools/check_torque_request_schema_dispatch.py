#!/usr/bin/env python3
"""Prove header dispatch and compare every retained request and response."""
from __future__ import annotations

import argparse
import copy
import gzip
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from run_torque_agent_workflows import (ROOT, digest, dumps, operation_request_validators,
                                       operation_response_validator, read, write)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-root", type=Path, required=True)
    parser.add_argument("--logs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir()
    schema_path = ROOT / "docs/language-design/agent-v0.22/request.schema.json"
    schema = read(schema_path)
    resources = {}
    for path in (args.schema_root / "docs/language-design").rglob("*.schema.json"):
        value = read(path)
        if "$id" in value:
            resources[value["$id"]] = Resource.from_contents(value)
    validator = Draft202012Validator(schema, registry=Registry().with_resources(resources.items()))
    response_path = ROOT / "docs/language-design/agent-v0.22/response.schema.json"
    response_validator = Draft202012Validator(read(response_path), registry=Registry().with_resources(resources.items()))
    dispatched = operation_request_validators(validator)
    assert len(dispatched) == 12
    examples, response_examples = {}, {}
    checks = 0
    with gzip.open(args.output / "comparisons.jsonl.gz", "wt", encoding="utf-8") as evidence:
        def compare(request, origin):
            nonlocal checks
            operation = request.get("operation") if isinstance(request, dict) else None
            candidate = dispatched.get(operation, validator) if type(operation) is str else validator
            full = validator.is_valid(request)
            selected = candidate.is_valid(request)
            evidence.write(dumps({"origin": origin, "request": request,
                "full_schema_valid": full, "selected_unchanged_branch_valid": selected}) + "\n")
            checks += 1
            assert full == selected, (origin, request)
            if full:
                examples.setdefault(operation, request)
        def compare_response(response, origin):
            nonlocal checks
            operation = response.get("operation") if type(response) is dict else None
            status = response.get("status") if type(response) is dict else None
            candidate = operation_response_validator(response_validator, operation, status)
            full = response_validator.is_valid(response)
            selected = candidate.is_valid(response)
            evidence.write(dumps({"origin": origin, "response": response,
                "full_schema_valid": full, "selected_unchanged_clauses_valid": selected}) + "\n")
            checks += 1
            assert full == selected, (origin, response)
            if full:
                response_examples.setdefault((operation, status), response)
        for path in args.logs:
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                for index, line in enumerate(stream, 1):
                    record = json.loads(line)
                    compare(record["request"], {"log": str(path), "line": index})
                    compare_response(record["response"], {"log": str(path), "line": index})
        assert set(examples) == set(dispatched), sorted(set(dispatched) - set(examples))
        for operation, request in examples.items():
            for key in request:
                removed = copy.deepcopy(request)
                del removed[key]
                compare(removed, {"operation": operation, "mutation": "remove", "field": key})
                for value in (None, False, 0, -1, "", [], {}, "invalid-value"):
                    replaced = copy.deepcopy(request)
                    replaced[key] = value
                    compare(replaced, {"operation": operation, "mutation": "replace", "field": key, "value": value})
            for selected in dispatched:
                compare({**request, "operation": selected}, {"operation": operation, "mutation": "different-operation"})
            compare({**request, "unknown_extra_field": True}, {"operation": operation, "mutation": "extra-field"})
        for value in (None, False, 0, "artifact", [], {}, {"operation": []}, {"operation": {}}):
            compare(value, "nonobject-or-unknown-operation")
            compare_response(value, "nonobject-or-unknown-operation")
        for header, response in list(response_examples.items()):
            for key in response:
                removed = copy.deepcopy(response)
                del removed[key]
                compare_response(removed, {"header": header, "mutation": "remove", "field": key})
                for value in (None, False, 0, -1, "", [], {}, "invalid-value"):
                    replaced = copy.deepcopy(response)
                    replaced[key] = value
                    compare_response(replaced, {"header": header, "mutation": "replace", "field": key, "value": value})
            for operation in dispatched:
                compare_response({**response, "operation": operation}, {"header": header, "mutation": "operation"})
            for status in response_validator.schema["properties"]["status"]["enum"]:
                compare_response({**response, "status": status}, {"header": header, "mutation": "status"})
            compare_response({**response, "unknown_extra_field": True}, {"header": header, "mutation": "extra-field"})
            if type(response.get("result")) is dict:
                for changes in ({"asset_id": "invalid", "data_base64": ""},
                                {"schema_version": "ontokin.surface-mesh-page/0.1"}):
                    compare_response({**response, "result": {**response["result"], **changes}},
                                     {"header": header, "mutation": "value-dependent-condition", "changes": changes})
    for mutation in ("duplicate-const", "operation-not-required", "extra-root-constraint", "nonobject-branch"):
        altered = copy.deepcopy(schema)
        if mutation == "duplicate-const":
            altered["oneOf"][1]["properties"]["operation"] = altered["oneOf"][0]["properties"]["operation"]
        elif mutation == "operation-not-required":
            altered["oneOf"][0]["required"].remove("operation")
        elif mutation == "extra-root-constraint":
            altered["maxProperties"] = 1
        else:
            del altered["oneOf"][0]["type"]
        assert operation_request_validators(validator.evolve(schema=altered)) == {}, mutation
        checks += 1
    result = {"status": "passed", "checks": checks, "operations": sorted(examples),
        "schema_sha256": digest(schema_path.read_bytes()), "schema_path": str(schema_path.relative_to(ROOT)),
        "response_schema_sha256": digest(response_path.read_bytes()),
        "driver_sha256": digest(Path(__file__).read_bytes()),
        "proof": "Request root has only oneOf and annotations. Every branch requires an object operation with a distinct string const, so every other branch is false. Missing/nonstring/unknown operations use the original full schema. Response root/value constraints are unchanged; only if conditions whose sole predicates are required operation/status string consts are evaluated using those actual fields, retaining the unchanged then/else clause. Every other conditional remains. Proof-precondition changes disable the affected shortcut.",
        "logs": [{"path": str(path), "sha256": digest(path.read_bytes())} for path in args.logs]}
    write(args.output / "summary.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
