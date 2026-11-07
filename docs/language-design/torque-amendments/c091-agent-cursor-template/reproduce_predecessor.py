"""Untouched C090 Agent/0.21 cursor placement reproduction."""
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
base = {"schema_version": "ontokin.agent/0.21", "project_id": "a04-predecessor"}
exchanges = []
with KeyedMembershipAgentService(output.parent / "a04-predecessor-store") as service:
    request = {**base, "request_id": "create", "operation": "create",
               "expected_program_revision": None, "requested_level": "constructed",
               "bundle": program.to_payload()}
    response = service.handle(request)
    exchanges.append({"request": request, "response": response})
    assert response["status"] == "succeeded", response
    request = {**base, "request_id": "page", "operation": "inspect",
               "program_revision": program.program_revision, "selector": {"kind": "object"},
               "fields": ["identity", "source", "state", "matter"], "limit": 1}
    response = service.handle(request)
    exchanges.append({"request": request, "response": response})
    assert response["status"] == "succeeded", response
    assert isinstance(response["next_cursor"], str) and response["next_cursor"]
    assert "next_cursor" not in response["result"]
    request = {**request, "request_id": "next-page", "cursor": response["next_cursor"]}
    response = service.handle(request)
    exchanges.append({"request": request, "response": response})
    assert response["status"] == "succeeded", response
table = json.loads((frozen / "agent/request-workflows.json").read_bytes())
case = next(row for row in table["scenarios"] if row["id"] == "A04")
bad = [step["request"]["cursor"]["$response"] for step in case["steps"]
       if "cursor" in step.get("request", {})]
assert bad == ["A04.page.result.next_cursor"] * 2
output.write_text(json.dumps({"status": "reproduced", "basis": basis,
    "unchanged_package_hashes": identities, "program_revision": program.program_revision,
    "frozen_workflows_sha256": hashlib.sha256((frozen / "agent/request-workflows.json").read_bytes()).hexdigest(),
    "frozen_paths": bad, "actual_cursor_path": "A04.page.next_cursor",
    "actual_exchanges": exchanges}, indent=2)+"\n")
print(json.dumps({"status": "reproduced", "basis": basis,
                  "unchanged_package_files": len(identities), "actual_cursor_path": "A04.page.next_cursor"}))
