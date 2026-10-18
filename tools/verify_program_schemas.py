"""Independently validate published schemas and actual program-agent messages.

Development-only dependency: jsonschema==4.25.1. The runtime remains stdlib-only.
All schema references resolve from the explicit local registry; no network
resolution is permitted. Runtime semantic/byte checks remain separate gates.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]


def identity(path):
    return {"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()}


def verify(demo):
    schema_dir = ROOT / "docs/language-design"
    paths = [schema_dir / "construction-v0.1" / name for name in ("bundle.schema.json", "file-manifest.schema.json")]
    paths += [schema_dir / "agent-v0.2" / name for name in ("request.schema.json", "response.schema.json", "diagnostic.schema.json")]
    schemas = [json.loads(path.read_text()) for path in paths]
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas)
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
    validators = [Draft202012Validator(schema, registry=registry) for schema in schemas]
    bundle, files, request, response, diagnostic = validators
    workflow_path = demo / "workflow.json"
    workflow = json.loads(workflow_path.read_text())
    bundle.validate(json.loads((demo / "program.bundle.json").read_text()))
    files.validate(json.loads((demo / "program.files.json").read_text()))
    counts = {"schemas": len(schemas), "bundles": 1, "file_manifests": 1, "requests": 0, "responses": 0, "diagnostics": 0}
    for operation in workflow["operations"]:
        request.validate(operation["request"])
        response.validate(operation["response"])
        counts["requests"] += 1
        counts["responses"] += 1
        for item in operation["response"]["diagnostics"]:
            diagnostic.validate(item)
            counts["diagnostics"] += 1
    valid = workflow["operations"][0]["request"]
    negatives = []
    for label, changes in [
        ("old protocol in a new request", {"schema_version": "ontokin.agent/0.1"}),
        ("unknown request field", {"undocumented_field": True}),
        ("single-file revision replacing program context", {"source_revision": "sha256:" + "0" * 64}),
    ]:
        candidate = copy.deepcopy(valid)
        candidate.update(changes)
        if request.is_valid(candidate):
            raise AssertionError("Schema unexpectedly accepted " + label)
        negatives.append(label)
    return {"schema_version": "ontokin.schema-validation/0.1", "status": "passed",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "validator": {"name": "jsonschema", "version": version("jsonschema"), "draft": "2020-12"},
            "dependencies": {name: version(name) for name in ["attrs", "jsonschema-specifications", "referencing", "rpds-py", "typing-extensions"]},
            "counts": counts, "rejected_negative_shapes": negatives,
            "schema_files": [identity(path) for path in paths], "workflow": identity(workflow_path),
            "source_bundle": identity(demo / "program.bundle.json"),
            "program_revision": workflow["accepted_program_revision"], "implementation": workflow["implementation"],
            "limits": ["Schema shape/reference checks do not replace semantic, UTF-8 byte, resource, identity, or concurrency validation.",
                       "Messages cover this actual workflow; other operations are exercised by protocol and transaction tests.",
                       "All references resolved locally; schema IDs do not claim a hosted schema service."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-dir", type=Path, default=ROOT / "examples/construction")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.demo_dir.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "counts": report["counts"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
