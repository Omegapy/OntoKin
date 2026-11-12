#!/usr/bin/env python3
"""Prove a bounded semantic export/edit workflow through the actual Agent/0.2.

The original keyed-rack fixtures and their expected results remain unchanged.
Use a new output directory; this driver refuses to overwrite prior evidence.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.bundle import load_bundle
from ontokin.diagnostics import OntoKinError
from ontokin.program_agent import ProgramAgentService
from ontokin.semantic_export import (SemanticExportError, build_semantic_manifest,
                                     canonical_bytes, verify_semantic_manifest)


FIXTURE = ROOT / "docs/language-design/construction-v0.1/01-keyed-rack"
TARGET = 'first.fingers["middle"]'
BLADE = TARGET + ".blade"
REQUIRED = ["stable_identities", "dimensions_units_frames"]


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def _rotate_x(q, length):
    w, x, y, z = q
    return [length * (1 - 2 * (y*y + z*z)),
            length * 2 * (x*y + w*z), length * 2 * (x*z - w*y)]


def reference(bundle, data, report, oracle, *, before):
    """Frozen independent oracle, with only the declared half-length adjustment."""
    geometry = copy.deepcopy(oracle["objects"])
    if before:
        next(item for item in geometry if item["path"] == BLADE)["geometry"]["size_m"][0] = .65
    samples = []
    for original in oracle["samples"]:
        objects = {}
        for item in original["objects"]:
            position = list(item["position_m"])
            if before and item["path"] == BLADE:
                correction = _rotate_x(item["rotation_wxyz"], (.65 - .75) / 2)
                position = [a + b for a, b in zip(position, correction)]
            objects[item["path"]] = {"position_m": position, "orientation_wxyz": item["rotation_wxyz"]}
        samples.append({"time_seconds": original["seconds"], "objects": objects})
    return {"schema_version": "ontokin.viewer-reference/0.2", "program_revision": bundle.program_revision,
            "source_manifest": bundle.manifest(), "artifact_sha256": digest(data),
            "geometry": geometry, "samples": samples, "tolerances": report["tolerances"],
            "independent_oracle": {"path": str((FIXTURE / "expected.json").relative_to(ROOT)),
                                   "sha256": digest((FIXTURE / "expected.json").read_bytes()),
                                   "before_adjustment": "Only selected blade X size=.65 m; center shift=rotation_wxyz*(-.05,0,0) m." if before else "Unchanged frozen oracle."}}


def build(output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose an empty output directory; prior evidence is never overwritten.")
    output.mkdir(parents=True, exist_ok=True)
    final_payload = json.loads((FIXTURE / "program.bundle.json").read_text())
    oracle = json.loads((FIXTURE / "expected.json").read_text())
    seed = copy.deepcopy(final_payload)
    assert seed["entry"]["source"].count("0.75[m]") == 1
    seed["entry"]["source"] = seed["entry"]["source"].replace("0.75[m]", "0.65[m]")
    initial_bundle = load_bundle(seed)
    checks, transcript = [], []

    def check(name, condition, **observed):
        if not condition:
            raise AssertionError(f"{name}: {observed}")
        checks.append({"name": name, "passed": True, "observed": observed})

    def rejection(name, function, expected_code=None):
        try:
            function()
        except (SemanticExportError, OntoKinError) as error:
            code = error.code
            check(name, expected_code is None or code == expected_code, code=code)
            return error.to_dict() if isinstance(error, SemanticExportError) else {
                "status": "rejected", "code": code, "message": str(error)}
        raise AssertionError(f"{name}: unexpectedly accepted")

    with tempfile.TemporaryDirectory(prefix="ontokin-semantic-agent-") as temporary:
        with ProgramAgentService(Path(temporary)) as service:
            project, serial = "semantic-export-c210", 0

            def send(request, expected="succeeded"):
                response = service.handle(request)
                retained = copy.deepcopy(response)
                if "data_base64" in retained.get("result", {}):
                    raw = base64.b64decode(retained["result"].pop("data_base64"), validate=True)
                    retained["result"]["omitted_artifact_chunk"] = {"bytes": len(raw), "sha256": digest(raw)}
                transcript.append({"request": copy.deepcopy(request), "response_summary": retained})
                if response["status"] != expected:
                    raise AssertionError(f"{request['operation']}: {response}")
                return response

            def call(operation, *, expected="succeeded", **fields):
                nonlocal serial
                serial += 1
                request = {"schema_version": "ontokin.agent/0.2", "project_id": project,
                           "request_id": f"c210-{serial:03d}-{operation}", "operation": operation, **fields}
                return send(request, expected), request

            def artifact(artifact_id, revision):
                data, offset = bytearray(), 0
                while offset is not None:
                    response, _ = call("artifact", artifact_id=artifact_id, offset=offset, max_bytes=65536)
                    result = response["result"]
                    check("Artifact chunk retains exact program and byte position",
                          result["program_revision"] == revision and result["offset"] == len(data))
                    data.extend(base64.b64decode(result["data_base64"], validate=True))
                    offset = result["next_offset"]
                return bytes(data)

            def export(revision):
                response, _ = call("export", program_revision=revision, destination="ontokin.glb/0.2",
                                   options={"helpers": False})
                result = response["result"]
                data = artifact(result["artifact_id"], revision)
                check("Actual exported GLB matches delivery report",
                      digest(data) == result["report"]["artifact"]["sha256"]
                      and result["report"]["program_revision"] == revision)
                return data, result

            discovered, _ = call("discover", profile="construction-0.1", bundle=seed,
                                 filter={"kind": "class", "name": "Finger"}, limit=10)
            check("Discover pinned reusable Finger", bool(discovered["result"]["items"]))
            created, _ = call("create", bundle=seed, expected_program_revision=None, requested_level="evaluated")
            before_revision = created["program_revision"]
            check("Actual accepted state equals initial exact bundle",
                  service.accepted_revision(project) == before_revision == initial_bundle.program_revision)
            before_data, before_result = export(before_revision)
            before_bundle = service.read_program(project, before_revision)
            before = build_semantic_manifest(before_bundle, before_data,
                                            accepted_program_revision=service.accepted_revision(project),
                                            required_features=REQUIRED)
            inspect, _ = call("inspect", program_revision=before_revision,
                              selector={"path": TARGET + ".length"}, fields=["identity", "source", "values"], limit=1)
            target = inspect["result"]["items"][0]["source"]["initializer_target"]
            check("Generated occurrence exposes its scoped initializer target", target["available"])
            start = before_bundle.entry.raw.index(b"0.65[m]")

            def patch(replacement):
                return {"source_id": "entry", "source_revision": before_bundle.entry.revision,
                        "element_id": target["element_id"], "start_byte": start,
                        "end_byte": start + len(b"0.65[m]"), "expected_text": "0.65[m]", "replacement": replacement}

            invalid, invalid_request = call("edit", expected="rejected", expected_program_revision=before_revision,
                                            requested_level="evaluated", patches=[patch("0.75[kg]")])
            invalid_retry = send(invalid_request, "rejected")
            check("Invalid units and identical retry preserve accepted source",
                  invalid["accepted_program_revision"] == before_revision
                  and invalid_retry == invalid and service.accepted_revision(project) == before_revision
                  and service.read_program(project, before_revision).to_payload() == before_bundle.to_payload()
                  and any(item["code"] == "OKL-E-UNIT" for item in invalid["diagnostics"]))
            check("Invalid edit preserves previously accepted artifact bytes",
                  artifact(before_result["artifact_id"], before_revision) == before_data)
            rejected_bundle = service.read_program(project, invalid["program_revision"])
            (output / "rejected-candidate.ok").write_bytes(rejected_bundle.entry.raw)
            write_json(output / "invalid-edit.json", invalid)
            after_response, edit_request = call("edit", expected_program_revision=before_revision,
                                               requested_level="evaluated", patches=[patch("0.75[m]")])
            after_revision = after_response["program_revision"]
            after_retry = send(edit_request)
            check("Successful edit changes revision once and idempotent retry retains result",
                  after_revision != before_revision and after_retry == after_response
                  and service.accepted_revision(project) == after_revision)
            changed_request = copy.deepcopy(edit_request)
            changed_request["patches"][0]["replacement"] = "0.85[m]"
            changed_retry = send(changed_request, "rejected")
            check("Changed-payload retry rejects without accepted-state mutation",
                  changed_retry["protocol_error"] is not None and service.accepted_revision(project) == after_revision)
            stale, _ = call("edit", expected="rejected", expected_program_revision=before_revision,
                            requested_level="evaluated", patches=[patch("0.85[m]")])
            check("Stale edit rejects without accepted-state mutation",
                  stale["accepted_program_revision"] == after_revision and service.accepted_revision(project) == after_revision)
            after_bundle = service.read_program(project, after_revision)
            after_data, after_result = export(after_revision)
            after = build_semantic_manifest(after_bundle, after_data,
                                           accepted_program_revision=service.accepted_revision(project), required_features=REQUIRED)
            check("Accepted repaired source equals unchanged frozen final fixture", after_bundle.to_payload() == final_payload)
            check("Source revision changes and pinned library stays exact",
                  before_bundle.entry.revision != after_bundle.entry.revision
                  and before_bundle.modules[0].raw == after_bundle.modules[0].raw
                  and before["binding"]["artifact"]["sha256"] != after["binding"]["artifact"]["sha256"])
            before_objects = {item["path"]: item for item in before["objects"]}
            after_objects = {item["path"]: item for item in after["objects"]}
            check("All18 semantic identities survive the targeted edit",
                  len(after_objects) == 18 and set(before_objects) == set(after_objects)
                  and all(before_objects[path]["element_id"] == item["element_id"] for path, item in after_objects.items()))
            unchanged = []
            for path in sorted(set(after_objects) - {TARGET, BLADE}):
                left, right = before_objects[path], after_objects[path]
                excluded = {"provenance", "geometry_binding", "motion_binding"}
                check("Unchanged semantic object and delivered geometry/motion: " + path,
                      {key: value for key, value in left.items() if key not in excluded}
                      == {key: value for key, value in right.items() if key not in excluded}
                      and left["geometry_binding"]["content_sha256"] == right["geometry_binding"]["content_sha256"]
                      and left["motion_binding"]["content_sha256"] == right["motion_binding"]["content_sha256"])
                unchanged.append(path)
            check("Sixteen unrelated objects include entire eleven-object sibling",
                  len(unchanged) == 16 and sum(path == "second" or path.startswith("second.") for path in unchanged) == 11)
            before_sites = {item["path"]: item for item in before["sites"]}
            changed_sites = []
            for item in after["sites"]:
                left = {key: value for key, value in before_sites[item["path"]].items() if key != "source_location"}
                right = {key: value for key, value in item.items() if key != "source_location"}
                if left != right:
                    changed_sites.append(item["path"])
            check("Only selected blade base site changes its declared pose", changed_sites == [BLADE + ".base"])
            for name in ("joints", "follows", "actions", "events"):
                def without_locations(value):
                    if isinstance(value, dict):
                        return {key: without_locations(child) for key, child in value.items() if key != "source_location"}
                    return [without_locations(child) for child in value] if isinstance(value, list) else value
                check("Declared " + name + " remain semantically unchanged", without_locations(before[name]) == without_locations(after[name]))
            verified = verify_semantic_manifest(after, after_bundle, after_data,
                                               accepted_program_revision=after_revision, required_features=REQUIRED)
            check("Recomputed sidecar binds actual source and GLB", verified["status"] == "passed")
            stale_pair = rejection("Stale source/artifact pairing rejects",
                                   lambda: build_semantic_manifest(after_bundle, before_data,
                                                                  accepted_program_revision=after_revision))
            broken = copy.deepcopy(after)
            broken["objects"][0]["geometry_binding"]["mesh"] = 999999
            broken_result = rejection("Broken geometry reference rejects",
                                      lambda: verify_semantic_manifest(broken, after_bundle, after_data,
                                                                       accepted_program_revision=after_revision), "OKS-E-MISMATCH")
            unsupported = rejection("Required live physics fails explicitly",
                                    lambda: build_semantic_manifest(after_bundle, after_data,
                                                                   accepted_program_revision=after_revision,
                                                                   required_features=["live_physics"]), "OKS-E-UNSUPPORTED")
            write_json(output / "unsupported-required-feature.json", unsupported)
            write_json(output / "negative-controls.json", {"stale_pairing": stale_pair, "broken_reference": broken_result})
            check("Default feature report explicitly marks nonexecuted behaviors",
                  {item["feature"] for item in after["features"] if item["treatment"] == "unsupported"}
                  == {"action_execution", "live_physics", "source_reconstruction"})
            for name, bundle, data, result, manifest in (
                    ("before", before_bundle, before_data, before_result, before),
                    ("after", after_bundle, after_data, after_result, after)):
                (output / (name + ".glb")).write_bytes(data)
                (output / (name + ".main.ok")).write_bytes(bundle.entry.raw)
                write_json(output / (name + ".program.bundle.json"), bundle.to_payload())
                write_json(output / (name + ".semantic.json"), manifest)
                write_json(output / (name + ".export.json"), result["report"])
                write_json(output / (name + ".reference.json"), reference(bundle, data, result["report"], oracle, before=name == "before"))
            (output / "hinges.ok").write_bytes(after_bundle.modules[0].raw)
        with ProgramAgentService(Path(temporary) / "clean-regeneration") as regenerated_service:
            request = {"schema_version": "ontokin.agent/0.2", "project_id": "clean-regeneration", "request_id": "create",
                       "operation": "create", "bundle": after_bundle.to_payload(), "expected_program_revision": None,
                       "requested_level": "delivered", "destination": "ontokin.glb/0.2", "options": {"helpers": False}}
            result = regenerated_service.handle(request)
            transcript.append({"request": request, "response_summary": result})
            check("Fresh Agent store accepts identical source at delivered level", result["status"] == "succeeded")
            regenerated, offset, serial = bytearray(), 0, 0
            while offset is not None:
                serial += 1
                response = regenerated_service.handle({"schema_version": "ontokin.agent/0.2", "project_id": "clean-regeneration",
                    "request_id": f"artifact-{serial}", "operation": "artifact", "artifact_id": result["result"]["artifact_id"],
                    "offset": offset, "max_bytes": 65536})
                check("Fresh regenerated artifact retrieval succeeds", response["status"] == "succeeded")
                regenerated.extend(base64.b64decode(response["result"]["data_base64"], validate=True))
                offset = response["result"]["next_offset"]
            regenerated = bytes(regenerated)
            regenerated_manifest = build_semantic_manifest(after_bundle, regenerated,
                accepted_program_revision=regenerated_service.accepted_revision("clean-regeneration"), required_features=REQUIRED)
            check("Clean regeneration reproduces exact GLB bytes and canonical sidecar",
                  regenerated == after_data and canonical_bytes(regenerated_manifest) == canonical_bytes(after))
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    inputs = {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in (
        ROOT / "ontokin/semantic_export.py", Path(__file__), FIXTURE / "program.bundle.json", FIXTURE / "expected.json")}
    proof = {"schema_version": "ontokin.semantic-export-proof/0.1", "status": "passed", "implementation_commit": git_commit,
             "input_hashes": inputs, "environment": {"python": platform.python_version(), "platform": platform.platform()},
             "command": "python3 tools/build_semantic_export_demo.py --output-dir <new-directory>",
             "before_program_revision": before_revision, "after_program_revision": after_revision,
             "before_artifact_sha256": digest(before_data), "after_artifact_sha256": digest(after_data),
             "unchanged_object_paths": unchanged, "changed_site_paths": changed_sites,
             "manifest_verification": verified, "checks": checks,
             "regeneration": {"glb_sha256": digest(regenerated), "canonical_manifest_sha256": digest(canonical_bytes(regenerated_manifest))},
             "limits": ["Experimental finite construction-primitives profile.",
                        "Independent Khronos/Three.js and visual checks are separate required evidence.",
                        "No Unreal execution, destination physics, native C201 admission or authoring-benefit comparison."]}
    write_json(output / "proof.json", proof)
    write_json(output / "workflow.json", {"schema_version": "ontokin.semantic-agent-evidence/0.1", "status": "passed",
        "artifact_chunk_encoding": "Base64 omitted from response_summary; original chunk hash/size retained and exact assembled GLBs saved.",
        "exchanges": transcript})
    return {"status": "passed", "checks": len(checks), "before_revision": before_revision,
            "after_revision": after_revision, "objects": len(after_objects), "unchanged_objects": len(unchanged),
            "output_dir": str(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(tempfile.gettempdir()) / "ontokin-semantic-export-c210")
    print(json.dumps(build(parser.parse_args().output_dir), indent=2))
