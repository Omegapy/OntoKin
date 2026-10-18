#!/usr/bin/env python3
"""Retain the adopted source-impulse workflow through actual Agent/0.4 JSON.

All geometry, evaluated state and GLB bytes come from the selected service. This
builder does not call a parser, compiler, evaluator, mesh generator or exporter.
The separate scalar oracle supplies checks only; it never supplies runtime data.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.bundle import load_bundle, load_file_manifest
from ontokin.program_agent import ProgramAgentService
from tools.impulse_oracles import (ACCEPTANCE_BYTES, CASES, DELIVERY_CASES,
    FIXTURES, digest, expected_pose, oracle_for, sample_requests)


PROTOCOL = "ontokin.agent/0.4"
DESTINATION = "ontokin.glb/0.4"
POSITIVE_CASES = tuple(name for name in CASES if name.startswith("P"))
BALL = ["impulse-demo", "demo", "ball"]
RACK = ["impulse-demo", "demo", "rack"]
A03_TESTS = [
    "test_impulse_agent_protocol.ImpulseAgentProtocolTests.test_all_four_stores_keep_identical_request_ids_independent",
    "test_impulse_agent_protocol.ImpulseAgentProtocolTests.test_wrong_store_version_rejects_before_journal_or_ddl_changes",
    "test_impulse_agent.ImpulseAgentTests.test_run_provenance_rejects_wrong_revision_and_implementation",
    "test_impulse_cli.ImpulseCLITests.test_corrupt_or_directory_store_reports_controlled_selected_protocol_error",
]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")


def source_case(name):
    bundle = load_file_manifest(FIXTURES / CASES[name]["file_manifest"])
    require(bundle.program_revision == CASES[name]["program_revision"],
            f"{name} no longer matches its adopted source revision")
    return bundle


def patch_between(before, after, identity):
    """Replay one minimal contiguous byte difference in an inspected scope."""
    require(before.modules == after.modules, "A source repair changed pinned libraries")
    left, right = before.entry.raw, after.entry.raw
    start = 0
    while start < min(len(left), len(right)) and left[start] == right[start]:
        start += 1
    end_left, end_right = len(left), len(right)
    while end_left > start and end_right > start and left[end_left-1] == right[end_right-1]:
        end_left -= 1; end_right -= 1
    require(start < max(end_left, end_right), "Source patch has no change")
    return {"source_id": "entry", "source_revision": before.entry.revision,
            "element_id": identity, "start_byte": start, "end_byte": end_left,
            "expected_text": left[start:end_left].decode("utf-8"),
            "replacement": right[start:end_right].decode("utf-8")}


def compare_fixed(actual, expected, label):
    """Check every frozen expected field without changing its numeric domain."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict), label + " is not an object")
        for name, value in expected.items():
            if name == "sequence_indices":
                observed = [record["sequence_index"] for record in actual["last_applications"]]
                require(observed == value, label + " application order differs")
            elif name == "orientation_wxyz":
                vector = actual[name]
                error = min(max(abs(a-sign*b) for a, b in zip(vector, value)) for sign in (-1, 1))
                require(len(vector) == 4 and error < 1e-9, label + " quaternion differs")
            else:
                require(name in actual, label + "." + name + " is absent")
                compare_fixed(actual[name], value, label + "." + name)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), label + " has the wrong length")
        for index, (a, e) in enumerate(zip(actual, expected)):
            compare_fixed(a, e, f"{label}[{index}]")
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        require(type(actual) in (int, float) and math.isfinite(actual) and
                math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9), label + " differs")
    else:
        require(actual == expected, label + " differs")


class Workflow:
    def __init__(self, output):
        self.output = Path(output)
        require(not self.output.exists() or not any(self.output.iterdir()),
                "Use a new empty output directory so evidence cannot mix runs")
        self.output.mkdir(parents=True, exist_ok=True)
        (self.output / "exchanges").mkdir()
        self.service = ProgramAgentService(self.output / "service-store", protocol=PROTOCOL)
        self.exchanges = []; self.snapshots = []; self.artifacts = []
        self.fixtures = []; self.checks = []; self.native_fixtures = []
        self.checkpoints = {}; self.projects = {}; self.bundles = {}; self.runs = {}; self.durations = {}
        self.samples = {}; self.meshes = {}; self.pose_comparisons = 0
        self.closed = False

    def exchange(self, request, *, status="succeeded", code=None):
        sequence = len(self.exchanges) + 1
        stem = f"exchanges/{sequence:04d}-{request['operation'].replace('.', '-')}"
        request_file, response_file = stem + ".request.json", stem + ".response.json"
        write_json(self.output / request_file, request)
        response = self.service.handle(request)
        write_json(self.output / response_file, response)
        self.exchanges.append({"sequence": sequence, "project_id": request["project_id"],
            "request_id": request["request_id"], "operation": request["operation"],
            "request_file": request_file, "request_sha256": digest((self.output / request_file).read_bytes()),
            "response_file": response_file, "response_sha256": digest((self.output / response_file).read_bytes())})
        require(response["schema_version"] == PROTOCOL and response["operation"] == request["operation"],
                f"Selected protocol/operation changed for exchange {sequence}")
        if status is not None:
            require(response["status"] == status,
                    f"Exchange {sequence} {request['operation']} returned {response['status']}: "
                    f"{response.get('protocol_error')} {response.get('diagnostics')}")
        if code is not None:
            codes = [item["code"] for item in response["diagnostics"]]
            if response["protocol_error"]: codes.append(response["protocol_error"]["code"])
            require(response["status"] in ("failed", "rejected") and code in codes,
                    f"Exchange {sequence} did not report expected {code}")
        return response

    def send(self, project, operation, *, status="succeeded", code=None, **fields):
        request = {"schema_version": PROTOCOL, "project_id": project,
                   "request_id": f"impulse-workflow-{len(self.exchanges)+1:04d}",
                   "operation": operation, **fields}
        return self.exchange(request, status=status, code=code)

    def checkpoint(self, label, project, bundle, *, accepted_once=True):
        retained = self.service.read_program(project, bundle.program_revision)
        require(retained.to_payload() == bundle.to_payload(), "Retained source bytes differ from the actual request")
        require(self.service._store.source_accepted_once(project, bundle.program_revision) == accepted_once,
                "Durable accepted-once state differs from the retained workflow")
        self.checkpoints[label] = {"project_id": project, "program_revision": bundle.program_revision}
        if any(s["project_id"] == project and s["program_revision"] == bundle.program_revision for s in self.snapshots):
            return
        relative = f"snapshots/{project}/{bundle.program_revision[7:]}"
        directory = self.output / relative; directory.mkdir(parents=True)
        write_json(directory / "program.bundle.json", retained.to_payload())
        write_json(directory / "source-manifest.json", retained.manifest())
        units = []
        for unit in retained.units:
            require(Path(unit.filename).name == unit.filename, "Frozen source filenames must be simple basenames")
            (directory / unit.filename).write_bytes(unit.raw)
            units.append({"source_id": unit.source_id, "source_revision": unit.revision,
                "filename": unit.filename, "file": f"{relative}/{unit.filename}",
                "sha256": digest(unit.raw), "byte_length": len(unit.raw),
                "package_id": unit.package_id, "version": unit.version})
        self.snapshots.append({"project_id": project, "program_revision": bundle.program_revision,
            "accepted_once": accepted_once, "bundle_file": f"{relative}/program.bundle.json",
            "bundle_sha256": digest((directory / "program.bundle.json").read_bytes()),
            "source_manifest_file": f"{relative}/source-manifest.json",
            "source_manifest_sha256": digest((directory / "source-manifest.json").read_bytes()), "units": units})

    def inspect(self, project, bundle, path, *, fields=None, **extra):
        response = self.send(project, "inspect", program_revision=bundle.program_revision,
            selector={"path": path}, fields=fields or ["identity", "source", "geometry", "support"], limit=1, **extra)
        require(response["result"]["total"] == 1 and len(response["result"]["items"]) == 1,
                "Inspection did not identify exactly one requested source occurrence")
        return response["result"]["items"][0], response

    def pages(self, project, bundle, shape):
        item, _ = self.inspect(project, bundle, shape["path"])
        require(item["element_id"] == shape["element_id"], "Stable occurrence identity changed")
        summary = item["geometry"]["surface"]
        require(summary["profile"] == "surface-0.1" and
                summary["triangle_count"] == shape["expected"]["triangles"], "Native summary changed profile or count")
        require(item["support"]["profile"] == "impulse-0.1" and
                item["support"]["named_destination"] == DESTINATION, "Entry support lost its explicit binding")
        result = {key: [] for key in ("positions_m", "normals", "source_triangle_ordinals", "region_keys")}
        cursor = None; offset = 0; digest_ = None; page_number = 0; first = None
        while True:
            response = self.send(project, "surface.mesh_page", program_revision=bundle.program_revision,
                element_id=shape["element_id"], count=(7, 1, 256)[min(page_number, 2)], cursor=cursor)
            page = response["result"]; size = page["returned_triangles"]
            if first is None: first = response
            require(page["profile"] == "surface-0.1" and "entry_profile" not in page,
                    "Public inherited mesh capability was relabelled")
            require(page["program_revision"] == bundle.program_revision and page["element_id"] == shape["element_id"],
                    "Mesh page changed source identity")
            require(page["offset"] == offset and page["coordinate_system"] == "carrier_local_after_placement/0.1"
                    and page["ordering"] == "native_triangle_ordinal/0.1", "Mesh cursor/order context changed")
            require(page["total_triangles"] == page["filtered_triangles"] == shape["expected"]["triangles"],
                    "Triangle count differs from the fixed source oracle")
            require(len(page["positions_m"]) == len(page["normals"]) == 3*size and
                    page["triangles"] == [[3*i, 3*i+1, 3*i+2] for i in range(size)], "Mesh page split a triangle")
            require(digest_ is None or digest_ == page["geometry_sha256"], "Geometry changed during immutable paging")
            digest_ = page["geometry_sha256"]
            for key in result: result[key].extend(page[key])
            offset += size; page_number += 1; cursor = response["next_cursor"]
            require(response["truncated"] == (cursor is not None), "Mesh continuation flags disagree")
            if cursor is None: break
            require(size > 0 and page_number < 1000, "Mesh pagination did not terminate")
        require(result["source_triangle_ordinals"] == list(range(shape["expected"]["triangles"])),
                "Complete source triangle ordinals were not retained")
        return {"geometry": item["geometry"], "triangles": result}, first

    def evaluate_and_inspect(self, name, project, bundle):
        duration = self.durations[project]
        run = self.send(project, "evaluate", program_revision=bundle.program_revision, run_id=None, until_seconds=duration)
        require(run["program_revision"] == bundle.program_revision and
                run["result"]["run_state"]["implementation"] == self.service.implementation,
                "Run provenance changed source or implementation")
        require((run["result"]["run_state"]["valid_until_seconds"], run["result"]["run_state"]["valid_until_side"]) ==
                (duration, "after"), "Evaluation did not cover the complete constructed scene duration")
        samples = []; inspect_ids = []
        oracle = oracle_for(name) if name in DELIVERY_CASES else None
        objects = {} if oracle is None else {o["path"]: o for o in oracle["shapes"] + oracle["empty_objects"]}
        for request in sample_requests(name):
            response = self.send(project, "inspect", program_revision=bundle.program_revision,
                run_id=run["run_id"], selector={"kind": "object"}, fields=["identity", "state"],
                limit=100, time=request)
            require(not response["truncated"] and len(response["result"]["items"]) == response["result"]["total"],
                    "State inspection omitted source objects")
            observed = {item["path"]: item["state"] for item in response["result"]["items"]}
            for path, state in observed.items():
                require(state["available"] and state["program_revision"] == bundle.program_revision and
                        state["run_id"] == run["run_id"], "State lost exact run provenance")
                require(set(state["impulses"]) == {"applied_count", "last_application_time_seconds", "last_applications"},
                        "Object lacks the complete bounded influence projection")
                for record in state["impulses"]["last_applications"]:
                    require(len(record) == 13 and record["target_path"] == path and
                            record["target_element_id"] == state["element_id"], "Impulse record lost source target identity")
                    location = record["source_location"]
                    unit = bundle.sources[location["source_id"]]
                    require(location["source_revision"] == unit.revision, "Impulse source revision is stale")
                    frozen = next((s for s in CASES[name]["source_impulse_statements"]
                        if s["source_location"] == location and s["sequence_index"] == record["sequence_index"]), None)
                    require(frozen is not None and unit.raw[location["start_byte"]:location["end_byte"]].decode() == frozen["expected_text"],
                            "Impulse record does not identify its exact authored statement")
                if oracle is not None:
                    require(path in objects, "An unpredicted object appeared in the destination fixture")
                    position, rotation = expected_pose(objects[path], request["seconds"])
                    compare_fixed(state, {"position_m": position, "orientation_wxyz": rotation}, f"{name}/{path}/{request}")
                    self.pose_comparisons += 1
            if oracle is not None: require(set(observed) == set(objects), "A destination carrier or shape is missing")
            for expected in CASES[name]["expected"]["samples"]:
                if (Fraction(expected["time_seconds"]), expected["side"]) == (Fraction(request["seconds"]), request["side"]):
                    compare_fixed(observed, expected["objects"], f"{name}/{request}")
            samples.append({"time_seconds": request["seconds"], "side": request["side"], "objects": observed})
            inspect_ids.append(response["request_id"])
        return run, samples, inspect_ids

    def export_fixture(self, name, project, bundle, samples):
        oracle = oracle_for(name)
        meshes = {}
        for shape in oracle["shapes"]:
            meshes[shape["path"]], _ = self.pages(project, bundle, shape)
        options = {"helpers": False, **CASES[name]["expected"].get("export_options", {})}
        exported = self.send(project, "export", program_revision=bundle.program_revision,
                             destination=DESTINATION, options=options)
        result = exported["result"]
        require(result["report"]["program_revision"] == bundle.program_revision and
                result["report"]["validation"]["status"] == "passed", "Delivery lost revision or failed its exporter checks")
        data = bytearray(); retrieval_ids = []
        while True:
            response = self.send(project, "artifact", artifact_id=result["artifact_id"],
                                 offset=len(data), max_bytes=4096 if not data else 65536)
            chunk = response["result"]
            require(chunk["offset"] == len(data) and response["program_revision"] == bundle.program_revision and
                    chunk["artifact_provenance"]["program_revision"] == bundle.program_revision,
                    "Artifact chunks changed offset or source provenance")
            data.extend(base64.b64decode(chunk["data_base64"], validate=True)); retrieval_ids.append(response["request_id"])
            if chunk["next_offset"] is None: break
            require(chunk["next_offset"] == len(data), "Artifact retrieval cursor is inconsistent")
        require(len(data) == result["total_bytes"] and digest(data) == result["sha256"], "Retrieved artifact bytes changed identity")
        directory = self.output / name; directory.mkdir()
        for unit in bundle.units: (directory / unit.filename).write_bytes(unit.raw)
        write_json(directory / "program.bundle.json", bundle.to_payload())
        (directory / "scene.glb").write_bytes(data)
        write_json(directory / "scene.export.json", result["report"])
        write_json(directory / "oracle.json", oracle)
        write_json(directory / "scene.reference.json", {"schema_version": "ontokin.impulse-native-reference/0.1",
            "implementation": self.service.implementation, "program_revision": bundle.program_revision,
            "source_manifest": bundle.manifest(), "artifact_sha256": digest(data),
            "tolerances": result["report"]["tolerances"], "samples": samples})
        self.artifacts.append({"fixture": name, "project_id": project, "program_revision": bundle.program_revision,
            "artifact_id": result["artifact_id"], "artifact_sha256": digest(data), "byte_length": len(data),
            "export_request_id": exported["request_id"], "retrieval_request_ids": retrieval_ids})
        self.native_fixtures.append({"fixture": name, "case_ids": CASES[name]["gates"],
            "program_revision": bundle.program_revision, "artifact_sha256": digest(data), "glb_bytes": len(data),
            "options": options})
        self.meshes[name] = meshes
        print(json.dumps({"fixture": name, "status": "retrieved", "glb_bytes": len(data),
                          "program_revision": bundle.program_revision}), flush=True)
        return meshes

    def fixture(self, name, *, deliver=True):
        require(name in POSITIVE_CASES and name not in self.projects, "Fixture is unknown or already executed")
        start = len(self.exchanges); project = "impulse-workflow-" + name.lower()
        final = source_case(name); base = source_case("P08") if name in ("P09", "P10") else final
        created = self.send(project, "create", bundle=base.to_payload(), expected_program_revision=None,
                            requested_level="constructed")
        require(created["accepted_program_revision"] == base.program_revision, "Created source identity differs")
        self.durations[project] = created["result"]["duration_seconds"]
        self.checkpoint(name + "-created", project, base)
        edit_ids = []; evaluate_ids = []; inspect_ids = []; before_meshes = {}
        accepted = created
        if name in ("P09", "P10"):
            base_run, _, base_inspections = self.evaluate_and_inspect("P08", project, base)
            evaluate_ids.append(base_run["request_id"]); inspect_ids += base_inspections
            for shape in oracle_for("P08")["shapes"]:
                before_meshes[shape["path"]], _ = self.pages(project, base, shape)
            root, root_response = self.inspect(project, base, "rack", fields=["identity", "source"])
            inspect_ids.append(root_response["request_id"])
            patch = patch_between(base, final, RACK)
            require(patch["expected_text"] == ("2" if name == "P09" else "0.5") and
                    patch["replacement"] == ("4" if name == "P09" else "1"), "The fixed repair ceased to be one source value")
            require(any(span["start_byte"] <= patch["start_byte"] < patch["end_byte"] <= span["end_byte"]
                        for span in root["source"]["writable_spans"]), "Repair is outside its inspected root initializer")
            accepted = self.send(project, "edit", expected_program_revision=base.program_revision,
                                 patches=[patch], requested_level="constructed")
            require(accepted["program_revision"] == accepted["accepted_program_revision"] == final.program_revision,
                    "Actual patch did not produce the exact frozen target")
            edit_ids.append(accepted["request_id"])
            self.checkpoint(name, project, final)
        run, samples, current_inspections = self.evaluate_and_inspect(name, project, final)
        evaluate_ids.append(run["request_id"]); inspect_ids += current_inspections
        if deliver and name in DELIVERY_CASES:
            after_meshes = self.export_fixture(name, project, final, samples)
            if before_meshes:
                require(after_meshes == before_meshes, "A mass/radius repair changed source geometry or PBR")
        elif before_meshes:
            after_meshes = {s["path"]: self.pages(project, final, s)[0] for s in oracle_for(name)["shapes"]}
            require(after_meshes == before_meshes, "A mass/radius repair changed source geometry or PBR")
        self.fixtures.append({"fixture": name, "project_id": project, "program_revision": final.program_revision,
            "create_request_id": created["request_id"], "accepted_request_id": accepted["request_id"],
            "edit_request_ids": edit_ids, "evaluate_request_ids": evaluate_ids, "inspect_request_ids": inspect_ids})
        self.projects[name] = project; self.bundles[name] = final; self.runs[name] = run; self.samples[name] = samples
        self.checkpoint(name, project, final)
        return start

    def add_check(self, name, start, *, status="passed", **details):
        self.checks.append({"id": name, "status": status,
            "evidence_request_ids": [e["request_id"] for e in self.exchanges[start:]], "details": details})

    def rejection_and_history(self):
        start = len(self.exchanges); project = self.projects["P01"]; original = self.bundles["P01"]
        invalid = source_case("N19")
        self.send(project, "inspect", program_revision=original.program_revision,
                  selector={"kind": "source", "source_id": "entry"}, fields=["source"], limit=1)
        request = {"schema_version": PROTOCOL, "project_id": project,
            "request_id": f"impulse-workflow-{len(self.exchanges)+1:04d}", "operation": "edit",
            "expected_program_revision": original.program_revision,
            "patches": [patch_between(original, invalid, ["sources", "entry"])], "requested_level": "evaluated"}
        rejected = self.exchange(request, status=None, code="OKL-E-MOTION-MODE")
        first_sequence = len(self.exchanges)
        require(rejected["program_revision"] == invalid.program_revision and
                rejected["accepted_program_revision"] == original.program_revision, "Rejected candidate changed the accepted source")
        run = rejected["result"]["run_state"]
        require(run["candidate_only"] and run["status"] == "failed" and
                (run["valid_until_seconds"], run["valid_until_side"]) == ("1", "before"),
                "Failed boundary was published as a successful accepted run")
        ball = run["last_valid_state"]["objects"]["ball"]
        require(ball["velocity_m_per_s"] == [0., 0., 0.] and ball["impulses"]["applied_count"] == 0 and
                ball["pose_authority"]["trajectory_anchor_seconds"] == "0", "Failed sequence did not roll back its earlier impulse")
        self.checkpoint("N19-candidate", project, invalid, accepted_once=False)
        identical = self.exchange(copy.deepcopy(request), status=None, code="OKL-E-MOTION-MODE")
        require(identical == rejected, "Identical request-ID retry changed the exact retained response")
        self.exchange({**request, "requested_level": "constructed"}, status=None, code="OKL-E-REQUEST-ID")
        for operation, fields in (("surface.mesh_page", {"element_id": BALL, "count": 7}),
                                  ("evaluate", {"run_id": None, "until_seconds": "2"}),
                                  ("export", {"destination": DESTINATION})):
            self.send(project, operation, program_revision=invalid.program_revision, status=None, code="OKL-E-REVISION", **fields)
        payload = original.to_payload(); payload["entry"]["source"] += "// accepted history identity\n"
        later = load_bundle(payload)
        edit = self.send(project, "edit", expected_program_revision=original.program_revision,
                         patches=[patch_between(original, later, ["sources", "entry"])], requested_level="evaluated")
        require(edit["accepted_program_revision"] == later.program_revision, "Later source was not accepted")
        self.checkpoint("P01-later-accepted", project, later)
        historical, _ = self.inspect(project, original, "ball", fields=["identity", "state"],
            run_id=self.runs["P01"]["run_id"], time={"seconds": "2", "side": "after"})
        compare_fixed(historical["state"], {"position_m": [3., 0., 0.], "velocity_m_per_s": [3., 0., 0.]}, "Accepted historical P01")
        self.send(project, "surface.mesh_page", program_revision=original.program_revision, element_id=BALL, count=7)
        self.add_check("A02", start, accepted_revision=original.program_revision, invalid_revision=invalid.program_revision,
            later_accepted_revision=later.program_revision, retry_sequences=[first_sequence, first_sequence+1, first_sequence+2],
            retry_request_id=request["request_id"], invalid_candidate_accepted_once=False)
        provenance_start = len(self.exchanges)
        self.send(project, "inspect", program_revision=later.program_revision, run_id=self.runs["P01"]["run_id"],
                  selector={"path": "ball"}, fields=["state"], limit=1, status=None, code="OKL-E-SAMPLE")
        self.add_check("A03", provenance_start, status="partial", protocol=PROTOCOL,
            store_filename=self.service._store.database_name, store_schema=self.service._store.schema_version,
            required_test_ids=A03_TESTS,
            executed="Actual different-revision run rejection; all retained successful states identify the selected implementation and source.",
            pending="The named current tests must actually execute for store isolation, wrong-store immutability, stale engine and controlled CLI startup; metadata alone does not prove these requirements.")

    def mesh_context(self):
        start = len(self.exchanges); project = self.projects["P02"]; bundle = self.bundles["P02"]
        _, first = self.pages(project, bundle, oracle_for("P02")["shapes"][0])
        decoded = json.loads(base64.urlsafe_b64decode(first["next_cursor"] + "="*(-len(first["next_cursor"]) % 4))[32:])
        context = decoded["context"]
        require(context["protocol"] == PROTOCOL and context["entry_profile"] == "impulse-0.1" and
                context["implementation"] == self.service.implementation, "Private cursor omits its selected entry binding")
        variations = {"program_revision": "sha256:" + "f"*64, "element_id": RACK,
            "region": "paint", "protocol": "ontokin.agent/0.3", "entry_profile": "surface-0.1",
            "implementation": {**self.service.implementation, "version": "stale-probe"}}
        for field, value in variations.items():
            token = self.service._cursor({**context, field: value}, decoded["offset"])
            self.send(project, "surface.mesh_page", program_revision=bundle.program_revision, element_id=BALL,
                      count=1, cursor=token, status=None, code="OKL-E-REVISION")
        self.send(project, "surface.mesh_page", program_revision=bundle.program_revision,
                  element_id=BALL, count=1, cursor=first["next_cursor"])
        discovery = self.send(project, "discover", profile="impulse-0.1", program_revision=bundle.program_revision, limit=1000)
        expected = {"entry": ("0.4", "impulse-0.1"),
            "package:fixture.impulse-parts@1.0.0": ("0.4", "impulse-0.1"),
            "package:fixture.surface-parts@1.0.0": ("0.3", "surface-0.1"),
            "package:fixture.impulse-vectors@1.0.0": ("0.2", "construction-0.1")}
        require(not discovery["truncated"], "Mixed source catalog was truncated")
        declarations = [i for i in discovery["result"]["items"] if "source_id" in i]
        require({i["source_id"] for i in declarations} == set(expected), "Mixed source catalog omitted a pinned unit")
        for item in declarations:
            require((item["language_version"], item["profile"]) == expected[item["source_id"]],
                    "Imported declaration profile was relabelled")
        self.add_check("A04", start, public_profile="surface-0.1", private_entry_profile="impulse-0.1",
                       rejected_context_fields=list(variations), fixture="P02")

    def frame_projection(self):
        start = len(self.exchanges); project = self.projects["P03"]; bundle = self.bundles["P03"]
        args = {"fields": ["identity", "state"], "run_id": self.runs["P03"]["run_id"],
                "time": {"seconds": "2", "side": "after"}}
        world, _ = self.inspect(project, bundle, "ball", frame="world", **args)
        local, _ = self.inspect(project, bundle, "ball", frame="ball.frame", **args)
        require(world["state"]["orientation_wxyz"] != local["state"]["orientation_wxyz"] and
                local["state"]["position_m"] == [0., 0., 0.], "Ordinary frame projection did not occur")
        require(json.dumps(world["state"]["impulses"], sort_keys=True) == json.dumps(local["state"]["impulses"], sort_keys=True),
                "Explicit world/self influence records changed under a top-level frame projection")
        self.add_check("A05", start, fixture="P03", frames=["world", "ball.frame"],
                       explicit_impulse_records_byte_equivalent=True)

    def run(self):
        starts = {}
        for name in POSITIVE_CASES:
            starts[name] = self.fixture(name)
        repair_ids = [e["request_id"] for e in self.exchanges
                      if e["project_id"] in (self.projects["P09"], self.projects["P10"])]
        self.checks.append({"id": "A01", "status": "passed", "evidence_request_ids": repair_ids,
            "details": {"base_fixture": "P08", "repaired_fixtures": ["P09", "P10"],
                        "same_unchanged_pinned_libraries": True, "geometry_and_pbr_unchanged": True,
                        "repair_scope": "One scalar value in each independently inspected rack occurrence initializer."}})
        self.rejection_and_history(); self.mesh_context(); self.frame_projection()

    def finish(self, error=None):
        if not self.closed:
            self.service.close(); self.closed = True
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                                  capture_output=True, check=True).stdout.strip()
        changes = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True,
                                 capture_output=True, check=True).stdout.splitlines()
        complete = ({f["fixture"] for f in self.fixtures} == set(POSITIVE_CASES) and
                    {a["fixture"] for a in self.artifacts} == set(DELIVERY_CASES) and
                    {c["id"] for c in self.checks} == {f"A{i:02d}" for i in range(1, 6)})
        common = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "git_revision": revision,
            "working_tree_changes": changes, "implementation": self.service.implementation,
            "builder_sha256": digest(Path(__file__).read_bytes()),
            "oracle_builder_sha256": digest((ROOT / "tools/impulse_oracles.py").read_bytes()),
            "acceptance_manifest_sha256": digest(ACCEPTANCE_BYTES)}
        workflow = {"schema_version": "ontokin.impulse-agent-demo/0.1",
            "status": "failed" if error else "passed" if complete else "partial", **common,
            "exchanges": self.exchanges, "snapshots": self.snapshots, "artifacts": self.artifacts,
            "checks": self.checks, "fixtures": self.fixtures, "checkpoints": self.checkpoints,
            "independent_pose_comparisons": self.pose_comparisons,
            "error": None if error is None else {"type": type(error).__name__, "message": str(error)}}
        native = {"schema_version": "ontokin.impulse-native-build/0.1",
            "status": "failed" if error else "built" if complete else "partial", **common,
            "fixtures": self.native_fixtures,
            "limits": ["These retained requests and GLBs alone do not complete the impulse release or GOAL.",
                "A03 deliberately remains partial until its identified store/CLI tests execute under the current implementation.",
                "Independent current destination, browser, inherited release and CI evidence remains mandatory.",
                "P12 is evaluation-only; no finite-float32 destination promise was added."]}
        write_json(self.output / "workflow.json", workflow)
        write_json(self.output / "native-build.json", native)
        return workflow


def build(output):
    workflow = Workflow(output)
    try:
        workflow.run()
    except BaseException as error:
        workflow.finish(error)
        raise
    return workflow.finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output_dir)
    print(json.dumps({"status": result["status"], "fixtures": len(result["fixtures"]),
        "artifacts": len(result["artifacts"]), "exchanges": len(result["exchanges"]),
        "pose_comparisons": result["independent_pose_comparisons"], "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
