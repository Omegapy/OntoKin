"""Untouched C090 timed-inspection run prerequisite reproduction."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

code, repository, output = map(Path, sys.argv[1:])
sys.path.insert(0, str(code))
from ontokin.keyed_membership_agent import KeyedMembershipAgentService
from ontokin.texture_bundle import load_texture_file_manifest

basis = "94a7796a54725ca764b2027deb43f09204f8a6de"
identities = {}
for path in sorted((code / "ontokin").glob("*.py")):
    relative = path.relative_to(code).as_posix()
    expected = subprocess.check_output(["git", "-C", str(repository), "show", basis+":"+relative])
    assert expected == path.read_bytes(), relative
    identities[relative] = hashlib.sha256(expected).hexdigest()
frozen = repository / "docs/language-design/torque-v0.1/freeze"
program = load_texture_file_manifest(frozen / "control-spin-up.files.json")
base = {"schema_version": "ontokin.agent/0.21", "project_id": "r13-predecessor"}
exchanges = []
with KeyedMembershipAgentService(output.parent / "r13-predecessor-store") as service:
    def send(request):
        response = service.handle(request)
        exchanges.append({"request": request, "response": response})
        return response
    created = send({**base, "request_id": "create", "operation": "create",
        "expected_program_revision": None, "requested_level": "constructed", "bundle": program.to_payload()})
    assert created["status"] == "succeeded" and created["run_id"] is None
    request = {**base, "request_id": "inspect-without-run", "operation": "inspect",
        "program_revision": program.program_revision, "selector": {"kind": "object"},
        "fields": ["state"], "limit": 100, "time": {"seconds": "1", "side": "after"}}
    rejected = send(request)
    assert rejected["status"] == "rejected"
    assert rejected["diagnostics"][0]["code"] == "OKL-E-SAMPLE"
    assert rejected["diagnostics"][0]["message"] == "A current-state time requires a matching program run."
    evaluated = send({**base, "request_id": "evaluate", "operation": "evaluate",
        "program_revision": program.program_revision, "until_seconds": "1", "run_id": None})
    assert evaluated["status"] == "succeeded" and evaluated["run_id"]
    accepted = send({**request, "request_id": "inspect-with-actual-run", "run_id": evaluated["run_id"]})
    assert accepted["status"] == "succeeded"
table_path = frozen / "agent/resource-cases.json"
table = json.loads(table_path.read_bytes())
case = table["cases"][12]
assert case["id"] == "R13" and case["setup"]["request"]["requested_level"] == "constructed"
assert "run_id" not in case["task_request"] and case["task_request"]["time"] == {"seconds": "1", "side": "after"}
output.write_text(json.dumps({"status": "reproduced", "basis": basis,
    "unchanged_package_hashes": identities, "program_revision": program.program_revision,
    "frozen_resource_sha256": hashlib.sha256(table_path.read_bytes()).hexdigest(),
    "frozen_case": case, "actual_exchanges": exchanges,
    "proposed_minimal_overlay": {"additional_setup": {
        "step": "evaluate-prefix", "expected_status": "succeeded", "request": {
            "schema_version": "ontokin.agent/0.22", "project_id": "c090-r13",
            "request_id": "c090-r13-evaluate-prefix", "operation": "evaluate",
            "program_revision": case["task_request"]["program_revision"],
            "run_id": None, "until_seconds": "1"}},
        "task_run_id": {"$response": "R13.evaluate-prefix.run_id"}}}, indent=2)+"\n")
print(json.dumps({"status": "reproduced", "basis": basis, "unchanged_package_files": len(identities),
                  "without_run": rejected["status"], "actual_run": accepted["status"]}))
