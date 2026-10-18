#!/usr/bin/env python3
"""Retain an actual Agent/0.3 source-edit, inspection and artifact workflow.

The service receives only exact OntoKin source bundles and documented JSON
operations. This tool never compiles a model, generates a mesh or calls an
exporter directly. Scalar geometry/motion oracles are independent inputs to the
separate destination verifier; GLB bytes are retrieved from artifact responses.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.bundle import ProgramBundle, SourceUnit, load_bundle
from ontokin.program_agent import ProgramAgentService
from tools.build_surface_demo import FIXTURES, TIMES, digest, fixture_cases, write_json

PROTOCOL = "ontokin.agent/0.3"
DESTINATION = "ontokin.glb/0.3"
COMPOSITIONS = FIXTURES / "compositions"
FIRST = ["surface-studio", "studio", "first"]
SECOND = ["surface-studio", "studio", "second"]
PALETTE_OVERRIDE = '''
        palette = keyed<SurfaceMaterial> {
            "clay": surface_material(rgba(0.6, 0.3, 0.2, 1), 0, 0.8),
            "paint": surface_material(rgba(0.8, 0.15, 0.05, 0.75), 0.7, 0.25)
        };
    '''


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def multiply(a, b):
    w, x, y, z = a
    v, i, j, k = b
    return [w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
            w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v]


def rotate(q, vector):
    return multiply(multiply(q, [0, *vector]), [q[0], -q[1], -q[2], -q[3]])[1:]


def expected_pose(record, seconds):
    """Independent source scalar arithmetic; never a scene/evaluator read."""
    motion = record["motion"]
    position = [p + v*seconds for p, v in zip(motion["position_m"], motion["velocity_m_per_s"])]
    if motion["kind"] == "hinge_y_on_translating_z90_parent":
        parent = [math.sqrt(.5), 0, 0, math.sqrt(.5)]
        half = motion["angle_rad_per_second"]*seconds/2
        rotation = multiply(parent, [math.cos(half), 0, math.sin(half), 0])
        position = [p+d for p, d in zip(position, rotate(parent, motion["mount_position_m"]))]
    else:
        require(motion["kind"] in {"affine", "released_uniform_gravity"}, "Unknown independent motion oracle")
        rotation = motion["rotation_wxyz"]
        if motion["kind"] == "released_uniform_gravity":
            dt = max(0, seconds - motion["release_time_s"])
            position = [p + .5*g*dt*dt for p, g in zip(position, motion["gravity_m_per_s2"])]
    return position, rotation


def geometry_data(page):
    return {key: page[key] for key in ("positions_m", "normals", "source_triangle_ordinals", "region_keys")}


class Workflow:
    def __init__(self, output):
        self.output = output
        require(not output.exists() or not any(output.iterdir()), "Use a new empty output directory so evidence cannot mix runs")
        output.mkdir(parents=True, exist_ok=True)
        (output / "exchanges").mkdir()
        self.manifest_bytes = (COMPOSITIONS / "expected.json").read_bytes()
        self.manifest = json.loads(self.manifest_bytes)
        self.acceptance_bytes = (FIXTURES / "acceptance.json").read_bytes()
        require(self.manifest["acceptance_manifest_sha256"] == digest(self.acceptance_bytes), "Frozen acceptance identity changed")
        self.service = ProgramAgentService(output / "service-store", protocol=PROTOCOL)
        self.exchanges = []
        self.snapshots = []
        self.artifacts = []
        self.fixtures = []
        self.checks = []
        self.checkpoints = {}
        self.palettes = []
        self.page_records = {}
        self.pose_comparisons = 0

    def send(self, project, operation, *, status="succeeded", code=None, **fields):
        sequence = len(self.exchanges) + 1
        request = {"schema_version": PROTOCOL, "project_id": project,
                   "request_id": f"surface-workflow-{sequence:04d}", "operation": operation, **fields}
        stem = f"exchanges/{sequence:04d}-{operation.replace('.', '-')}"
        request_file = stem + ".request.json"
        response_file = stem + ".response.json"
        write_json(self.output / request_file, request)
        response = self.service.handle(request)
        write_json(self.output / response_file, response)
        self.exchanges.append({"sequence": sequence, "project_id": project,
            "request_id": request["request_id"], "operation": operation,
            "request_file": request_file, "request_sha256": digest((self.output / request_file).read_bytes()),
            "response_file": response_file, "response_sha256": digest((self.output / response_file).read_bytes())})
        require(response["schema_version"] == PROTOCOL and response["operation"] == operation,
                f"Incorrect response binding for {request['request_id']}")
        if status is not None:
            require(response["status"] == status, f"{request['request_id']} {operation} returned {response['status']}: {response.get('diagnostics')} {response.get('protocol_error')}")
        if code is not None:
            codes = [item["code"] for item in response["diagnostics"]]
            if response["protocol_error"]:
                codes.append(response["protocol_error"]["code"])
            require(response["status"] in {"rejected", "failed"} and code in codes,
                    f"{request['request_id']} did not report {code}: {response}")
        return response

    def checkpoint(self, name, project, bundle, accepted_once=True):
        retained = self.service.read_program(project, bundle.program_revision)
        require(retained.to_payload() == bundle.to_payload(), "Retained source bytes differ from the actual submitted candidate")
        require(self.service._store.source_accepted_once(project, bundle.program_revision) == accepted_once,
                "Durable accepted-once history differs from the workflow claim")
        self.checkpoints[name] = {"project_id": project, "program_revision": bundle.program_revision}
        if any(item["project_id"] == project and item["program_revision"] == bundle.program_revision for item in self.snapshots):
            return
        relative = f"snapshots/{project}/{bundle.program_revision[7:]}"
        directory = self.output / relative
        directory.mkdir(parents=True)
        write_json(directory / "program.bundle.json", retained.to_payload())
        write_json(directory / "source-manifest.json", retained.manifest())
        units = []
        for unit in retained.units:
            require(Path(unit.filename).name == unit.filename, "Fixture filenames must be simple relative basenames")
            (directory / unit.filename).write_bytes(unit.raw)
            units.append({"source_id": unit.source_id, "source_revision": unit.revision,
                          "filename": unit.filename, "file": f"{relative}/{unit.filename}",
                          "sha256": digest(unit.raw), "byte_length": len(unit.raw),
                          "package_id": unit.package_id, "version": unit.version})
        self.snapshots.append({"project_id": project, "program_revision": retained.program_revision,
            "accepted_once": accepted_once, "bundle_file": f"{relative}/program.bundle.json",
            "bundle_sha256": digest((directory / "program.bundle.json").read_bytes()),
            "source_manifest_file": f"{relative}/source-manifest.json",
            "source_manifest_sha256": digest((directory / "source-manifest.json").read_bytes()), "units": units})

    def create(self, name, bundle):
        project = "surface-workflow-" + name
        response = self.send(project, "create", bundle=bundle.to_payload(), expected_program_revision=None,
                             requested_level="constructed")
        require(response["program_revision"] == bundle.program_revision == response["accepted_program_revision"], "Create lost the exact program identity")
        self.checkpoint(name, project, bundle)
        return project

    def inspect(self, project, revision, path, fields=None):
        response = self.send(project, "inspect", program_revision=revision, selector={"path": path},
                             fields=fields or ["identity", "source", "geometry", "support"], limit=1)
        require(response["result"]["total"] == 1 and len(response["result"]["items"]) == 1, f"Missing exact occurrence/property {path}")
        return response["result"]["items"][0]

    def page(self, project, revision, shape):
        counts = (7, 1, 256)
        cursor = None
        offset = 0
        pages = []
        result = {name: [] for name in ("positions_m", "normals", "source_triangle_ordinals", "region_keys")}
        while True:
            response = self.send(project, "surface.mesh_page", program_revision=revision,
                element_id=shape["element_id"], count=counts[min(len(pages), 2)], cursor=cursor)
            page = response["result"]
            require(page["offset"] == offset, "Mesh cursor skipped or repeated triangles")
            require(page["element_id"] == shape["element_id"] and page["program_revision"] == revision, "Mesh page changed occurrence/revision")
            require(page["coordinate_system"] == "carrier_local_after_placement/0.1" and
                    page["ordering"] == "native_triangle_ordinal/0.1", "Unexpected mesh coordinate/order contract")
            size = page["returned_triangles"]
            require(len(page["positions_m"]) == len(page["normals"]) == 3*size, "A page split a triangle")
            require(page["triangles"] == [[3*i, 3*i+1, 3*i+2] for i in range(size)], "Page indices are not complete local triangles")
            require(page["total_triangles"] == page["filtered_triangles"] == shape["expected"]["triangles"], "Actual source triangle count differs from the fixed scalar oracle")
            if pages:
                require(page["geometry_sha256"] == pages[0]["result"]["geometry_sha256"], "Geometry changed inside an immutable mesh query")
            for key in result:
                result[key].extend(page[key])
            pages.append(response)
            offset += size
            cursor = response["next_cursor"]
            require(response["truncated"] == (cursor is not None), "Page truncation is inconsistent")
            if cursor is None:
                break
            require(size > 0 and len(pages) < 1000, "Mesh paging failed to terminate")
        require(result["source_triangle_ordinals"] == list(range(shape["expected"]["triangles"])), "Native source triangle order is incomplete")
        return result, pages

    def export_fixture(self, name, project, bundle, oracle):
        revision = bundle.program_revision
        self.checkpoint(name, project, bundle)
        page_data = {}
        for shape in oracle["shapes"]:
            item = self.inspect(project, revision, shape["path"])
            require(item["element_id"] == shape["element_id"], "Stable source occurrence identity changed")
            summary = item["geometry"]["surface"]
            require(summary["triangle_count"] == shape["expected"]["triangles"] and
                    summary["section_keys"] == [s["key"] for s in shape["sections"]], "Summary differs from the authored source scalar oracle")
            page_data[shape["path"]], pages = self.page(project, revision, shape)
            self.page_records[(name, shape["path"])] = pages
        run = self.send(project, "evaluate", program_revision=revision, run_id=None, until_seconds="2")
        objects = {shape["path"]: shape for shape in oracle["shapes"] + oracle.get("empty_objects", [])}
        samples = []
        for time in TIMES:
            response = self.send(project, "inspect", program_revision=revision, selector={"kind": "object"},
                fields=["identity", "state"], limit=len(objects), run_id=run["run_id"],
                time={"seconds": time, "side": "after"})
            items = response["result"]["items"]
            require(response["result"]["total"] == len(objects) and not response["truncated"], "State inspection omitted source objects")
            sample = {}
            for item in items:
                path, state = item["path"], item["state"]
                require(path in objects and state["available"] and state["program_revision"] == revision, "State is unavailable or belongs to another source")
                expected_position, expected_rotation = expected_pose(objects[path], float(time))
                require(max(abs(a-b) for a, b in zip(state["position_m"], expected_position)) < 1e-9, f"Independent position oracle failed for {name}/{path} at {time}")
                error = min(max(abs(a-sign*b) for a,b in zip(state["orientation_wxyz"], expected_rotation)) for sign in (1,-1))
                require(error < 1e-9, f"Independent rotation oracle failed for {name}/{path} at {time}")
                self.pose_comparisons += 1
                sample[path] = {"position_m": state["position_m"], "orientation_wxyz": state["orientation_wxyz"]}
            require(set(sample) == set(objects), "State inspection aliased an occurrence")
            samples.append({"time_seconds": time, "objects": sample})
        exported = self.send(project, "export", program_revision=revision, destination=DESTINATION, options={"helpers": False})
        result = exported["result"]
        require(exported["program_revision"] == revision and result["report"]["program_revision"] == revision, "Export lost repaired source identity")
        require(result["report"]["validation"]["status"] == "passed", "Source GLB did not pass its exporter checks")
        data = bytearray()
        retrieval_ids = []
        while True:
            response = self.send(project, "artifact", artifact_id=result["artifact_id"], offset=len(data),
                                 max_bytes=4096 if not data else 65536)
            chunk = response["result"]
            require(chunk["offset"] == len(data) and response["program_revision"] == revision, "Artifact chunks changed identity or offset")
            require(chunk["artifact_provenance"]["program_revision"] == revision, "Artifact provenance changed revision")
            data.extend(base64.b64decode(chunk["data_base64"], validate=True))
            retrieval_ids.append(response["request_id"])
            if chunk["next_offset"] is None:
                break
            require(chunk["next_offset"] == len(data), "Artifact chunk cursor is inconsistent")
        require(len(data) == result["total_bytes"] and digest(data) == result["sha256"], "Retrieved artifact bytes differ from the export identity")
        directory = self.output / name
        directory.mkdir()
        for unit in bundle.units:
            (directory / unit.filename).write_bytes(unit.raw)
        write_json(directory / "program.bundle.json", bundle.to_payload())
        (directory / "scene.glb").write_bytes(data)
        write_json(directory / "scene.export.json", result["report"])
        write_json(directory / "oracle.json", {"schema_version": "ontokin.surface-fixture-oracle/0.1",
            "fixture": name, "origin": "Predetermined source scalar values; no evaluated or host-generated geometry.",
            "acceptance_manifest_sha256": digest(self.acceptance_bytes), **oracle})
        write_json(directory / "scene.reference.json", {"schema_version": "ontokin.surface-native-reference/0.1",
            "program_revision": revision, "source_manifest": bundle.manifest(), "artifact_sha256": digest(data),
            "tolerances": result["report"]["tolerances"], "samples": samples})
        self.fixtures.append({"fixture": name, "case_ids": oracle["case_ids"], "program_revision": revision,
                              "artifact_sha256": digest(data), "glb_bytes": len(data)})
        self.artifacts.append({"fixture": name, "project_id": project, "program_revision": revision,
            "artifact_id": result["artifact_id"], "artifact_sha256": digest(data), "byte_length": len(data),
            "export_request_id": exported["request_id"], "retrieval_request_ids": retrieval_ids})
        print(json.dumps({"fixture": name, "status": "retrieved", "glb_bytes": len(data), "program_revision": revision}), flush=True)
        return page_data

    def patch(self, bundle, old, new, *, element_id=SECOND, within=None):
        raw = bundle.entry.raw
        lower, upper = (0, len(raw)) if within is None else (within["start_byte"], within["end_byte"])
        start = raw.index(old.encode("utf-8"), lower, upper)
        require(raw.find(old.encode("utf-8"), start+1, upper) < 0, "Patch text is ambiguous within its inspected source target")
        return {"source_id": "entry", "source_revision": bundle.entry.revision, "element_id": element_id,
                "start_byte": start, "end_byte": start + len(old.encode("utf-8")), "expected_text": old, "replacement": new}

    def edit(self, project, bundle, patches, name, *, code=None):
        payload = bundle.to_payload()
        raw = bundle.entry.raw
        for patch in sorted(patches, key=lambda item: item["start_byte"], reverse=True):
            require(raw[patch["start_byte"]:patch["end_byte"]] == patch["expected_text"].encode("utf-8"), "Independent patch precondition failed")
            raw = raw[:patch["start_byte"]] + patch["replacement"].encode("utf-8") + raw[patch["end_byte"]:]
        payload["entry"]["source"] = raw.decode("utf-8")
        candidate = load_bundle(payload)
        response = self.send(project, "edit", expected_program_revision=bundle.program_revision, patches=patches,
                             requested_level="constructed", status=None if code else "succeeded", code=code)
        require(response["program_revision"] == candidate.program_revision, "Atomic edit differs from an independent UTF-8 patch replay")
        require(response["accepted_program_revision"] == (bundle.program_revision if code else candidate.program_revision), "Failed edit mutated the accepted head")
        require(candidate.modules == bundle.modules, "Occurrence edit changed pinned library bytes")
        self.checkpoint(name, project, candidate, accepted_once=not bool(code))
        return candidate, response

    def check(self, identity, start, **details):
        self.checks.append({"id": identity, "status": "passed", "evidence_request_ids":
                           [item["request_id"] for item in self.exchanges[start:]], "details": details})

    def studio(self, bundle, oracle):
        project = self.create("studio-original", bundle)
        self.send(project, "discover", profile="surface-0.1", program_revision=bundle.program_revision, limit=1000)
        original = self.export_fixture("studio-original", project, bundle, oracle)
        first_source = self.inspect(project, bundle.program_revision, "first", ["source"])["source"]
        rings = self.inspect(project, bundle.program_revision, "second.rings", ["source"])
        span = rings["source"]["initializer_target"]["assignment_span"]
        start = len(self.exchanges)
        invalid, rejected = self.edit(project, bundle, [self.patch(bundle, "0.48[m]", "0[m]", within=span)],
                                      "studio-invalid-radius", code="OKL-E-SURFACE-RADIUS")
        self.checkpoints["radius-invalid"] = self.checkpoints["studio-invalid-radius"]
        candidate_source = self.send(project, "inspect", program_revision=invalid.program_revision,
            selector={"kind": "source", "source_id": "entry"}, fields=["source", "state"], limit=1)
        require(not candidate_source["result"]["index_complete"] and
                not candidate_source["result"]["items"][0]["state"]["available"], "Rejected candidate acquired valid object state")
        for operation, fields in (("surface.mesh_page", {"element_id": SECOND, "count": 7}),
                                  ("evaluate", {"run_id": None, "until_seconds": "2"}),
                                  ("export", {"destination": DESTINATION, "options": {"helpers": False}})):
            self.send(project, operation, program_revision=invalid.program_revision,
                      status=None, code="OKL-E-REVISION", **fields)
        repaired, accepted = self.edit(project, bundle, [self.patch(bundle, "0.48[m]", "0.52[m]", within=span)], "radius-repaired")
        repaired_oracle = copy.deepcopy(oracle)
        repaired_oracle.pop("frozen_source_bytes", None)
        repaired_oracle["case_ids"] = ["M05", "M07", "M09", "M11"]
        repaired_oracle["shapes"][1]["sections"][1]["radii_xy_m"][0] = self.manifest["workflow"]["repaired_radius_x_m"]
        repaired_pages = self.export_fixture("radius-repaired", project, repaired, repaired_oracle)
        require(original["first"] == repaired_pages["first"], "The radius repair changed its untouched sibling mesh")
        require(original["second"] != repaired_pages["second"], "The radius repair did not change the intended occurrence")
        for ordinal in self.manifest["workflow"]["radius_unchanged_triangle_ordinals"]:
            for field in ("positions_m", "normals"):
                require(original["second"][field][3*ordinal:3*ordinal+3] == repaired_pages["second"][field][3*ordinal:3*ordinal+3], "The radius edit changed nonadjacent caps")
        updated_span = self.inspect(project, repaired.program_revision, "first", ["source"])["source"]["span"]
        old_span = first_source["span"]
        require((updated_span["start_byte"], updated_span["end_byte"]) == (old_span["start_byte"], old_span["end_byte"]), "An earlier sibling source byte range changed")
        require(bundle.entry.raw[old_span["start_byte"]:old_span["end_byte"]] ==
                repaired.entry.raw[updated_span["start_byte"]:updated_span["end_byte"]], "The repair changed untouched sibling source bytes")
        require(updated_span["source_revision"] == repaired.entry.revision, "Sibling source location retained a stale containing-file revision")
        self.check("M07-radius-repair", start, invalid_revision=invalid.program_revision,
                   before_revision=bundle.program_revision, after_revision=repaired.program_revision,
                   unchanged_library_sha256=bundle.modules[0].revision)
        start = len(self.exchanges)
        old_cursor = self.page_records[("studio-original", "first")][0]["next_cursor"]
        self.send(project, "surface.mesh_page", program_revision=repaired.program_revision,
                  element_id=FIRST, count=19, cursor=old_cursor, status=None, code="OKL-E-REVISION")
        historical = self.send(project, "surface.mesh_page", program_revision=bundle.program_revision,
                               element_id=FIRST, count=19, cursor=old_cursor)
        require(historical["accepted_program_revision"] == repaired.program_revision and
                historical["result"]["source_triangle_ordinals"] == list(range(7,26)), "Accepted history could not continue its own cursor")
        self.check("mesh-page-accepted-history", start, old_revision=bundle.program_revision, current_revision=repaired.program_revision)
        start = len(self.exchanges)
        palette_target = self.inspect(project, repaired.program_revision, "second.palette", ["source"])["source"]["initializer_target"]
        require(palette_target["available"] and palette_target["assignment_span"] is None, "Palette repair has no inherited initializer target")
        position = palette_target["span"]["end_byte"] - 1
        require(repaired.entry.raw[position:position+1] == b"}", "Palette insertion does not address the inspected occurrence initializer")
        palette_patch = {"source_id": "entry", "source_revision": repaired.entry.revision, "element_id": SECOND,
                         "start_byte": position, "end_byte": position, "expected_text": "", "replacement": PALETTE_OVERRIDE}
        painted, _ = self.edit(project, repaired, [palette_patch], "palette-repaired")
        painted_oracle = copy.deepcopy(repaired_oracle)
        painted_oracle["case_ids"] = ["M04", "M05", "M07", "M09", "M11"]
        # fixture_cases intentionally reuses one palette value for both initial
        # shapes. The instance override must get its own independent scalar map.
        painted_oracle["shapes"][1]["materials"] = copy.deepcopy(painted_oracle["shapes"][1]["materials"])
        painted_oracle["shapes"][1]["materials"]["paint"] = self.manifest["workflow"]["palette_after"]
        painted_pages = self.export_fixture("palette-repaired", project, painted, painted_oracle)
        require(painted_pages == repaired_pages, "An isolated palette override changed positions, topology or normals")
        self.palettes.append({"before_fixture": "radius-repaired", "after_fixture": "palette-repaired", "path": "second", "region": "paint"})
        self.check("M07-palette-repair", start, before_revision=repaired.program_revision, after_revision=painted.program_revision, changed_region="paint", unchanged_geometry=True)
        start = len(self.exchanges)
        assignment_span = self.inspect(project, painted.program_revision, "second.rings", ["source"])["source"]["initializer_target"]["assignment_span"]
        base_text = painted.entry.raw[assignment_span["start_byte"]:assignment_span["end_byte"]].decode("utf-8")
        lines = base_text.splitlines()
        rows = {line.split('"')[1]: line.rstrip().rstrip(',') for line in lines if "loft_section" in line}
        rows["between"] = '            "between": loft_section(0.4[m], vec3(0.1[m], 0[m], 0[m]), 0.55[m], 0.4[m], "clay")'
        def reordered(keys):
            return "\n".join([lines[0], *[rows[key] + ("," if i+1 < len(keys) else "") for i, key in enumerate(keys)], lines[-1]])
        inserted_text = reordered(self.manifest["workflow"]["inserted_ordered_keys"])
        reordered_text = reordered(self.manifest["workflow"]["source_reorder_keys"])
        previous, previous_text = painted, base_text
        inserted_pages = None
        for name, text in (("inserted", inserted_text), ("reordered", reordered_text), ("removed", base_text)):
            changed, _ = self.edit(project, previous, [self.patch(previous, previous_text, text)], name)
            changed_oracle = copy.deepcopy(painted_oracle)
            changed_oracle["case_ids"] = ["M05", "M08", "M09", "M11"]
            if name != "removed":
                changed_oracle["shapes"][1]["sections"].insert(1, self.manifest["workflow"]["inserted_section"])
                changed_oracle["shapes"][1]["expected"] = {"triangles": 128, "vertices": 384}
            pages = self.export_fixture(name, project, changed, changed_oracle)
            require(pages["first"] == original["first"], "A topology edit changed the untouched sibling")
            if name == "inserted":
                inserted_pages = pages
            elif name == "reordered":
                require(pages == inserted_pages, "Source declaration order changed numeric station geometry")
            else:
                require(changed.to_payload() == painted.to_payload() and pages == painted_pages, "Removing the inserted section did not restore the exact earlier source/mesh")
            previous, previous_text = changed, text
        self.check("M08-topology-edits", start, inserted_keys=self.manifest["workflow"]["inserted_ordered_keys"],
                   reordered_source_keys=self.manifest["workflow"]["source_reorder_keys"], restored_revision=painted.program_revision)

    def run(self):
        native = list(fixture_cases())
        _, studio, oracle = native[0]
        require(studio.modules[0].revision == self.manifest["library"]["sha256"], "Companions no longer reuse the frozen library")
        self.studio(studio, oracle)
        native_start = len(self.exchanges)
        for name, bundle, oracle in native[1:]:
            project = self.create(name, bundle)
            self.export_fixture(name, project, bundle, oracle)
        self.palettes.append({"before_fixture": "regional-materials", "after_fixture": "regional-materials-edited", "path": "shell", "region": "middle"})
        composition_start = len(self.exchanges)
        generated_counts = []
        for fixture in self.manifest["fixtures"]:
            entry = SourceUnit("entry", fixture["entry"], (COMPOSITIONS / fixture["entry"]).read_bytes())
            bundle = ProgramBundle(entry, studio.modules)
            require(bundle.program_revision == fixture["program_revision"] and entry.revision == fixture["entry_sha256"], "A companion source differs from its predetermined identity")
            project = self.create(fixture["id"], bundle)
            first_request = len(self.exchanges)-1
            self.send(project, "discover", profile="surface-0.1", program_revision=bundle.program_revision, limit=1000)
            self.export_fixture(fixture["id"], project, bundle, fixture["oracle"])
            if fixture["construction"] == "generated":
                generated_counts.append(fixture["part_count"])
                for path, key in zip(fixture["shape_paths"], fixture["generated_keys"]):
                    item = self.inspect(project, bundle.program_revision, path, ["source"])
                    require(item["source"]["generated"]["input_key"] == key, "Generated occurrence lost its literal source input key")
            if fixture["id"] == "rotated-release":
                self.check("M09-rotated-release", first_request, fixture=fixture["id"],
                           oracle_file="docs/language-design/surface-v0.1/compositions/expected.json")
        require(generated_counts == self.manifest["generated_part_counts"], "The fixed generated counts were not all executed")
        self.check("M05-compositions", composition_start, fixtures=[item["id"] for item in self.manifest["fixtures"]],
                   generated_part_counts=generated_counts, unchanged_library_sha256=studio.modules[0].revision)
        self.check("M06-generated-counts", native_start, held_out_fixtures=[f"held-out-{i}" for i in range(1,5)],
                   generated_part_counts=generated_counts)

    def finish(self, error=None):
        self.service.close()
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
        changes = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
        common = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "git_revision": revision,
                  "working_tree_changes": changes, "builder_sha256": digest(Path(__file__).read_bytes()),
                  "acceptance_manifest_sha256": digest(self.acceptance_bytes),
                  "composition_manifest_sha256": digest(self.manifest_bytes), "implementation": self.service.implementation}
        build = {"schema_version": "ontokin.surface-native-build/0.1", "status": "failed" if error else "built",
                 **common, "fixtures": self.fixtures, "palette_edits": self.palettes,
                 "limits": ["This retained Agent/0.3 corpus does not alone complete M01–M12 or GOAL.",
                            "Independent Khronos, Three.js and browser checks must validate these exact retrieved artifacts.",
                            "No compiler, exporter or mesh-generation API is called by this workflow tool."]}
        workflow = {"schema_version": "ontokin.surface-agent-workflow/0.1", "status": "failed" if error else "passed",
                    **common, "exchanges": self.exchanges, "snapshots": self.snapshots, "artifacts": self.artifacts,
                    "checks": self.checks, "checkpoints": self.checkpoints, "independent_pose_comparisons": self.pose_comparisons,
                    "error": None if error is None else {"type": type(error).__name__, "message": str(error)}}
        write_json(self.output / "build.json", build)
        write_json(self.output / "workflow.json", workflow)
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
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.output_dir)
    print(json.dumps({"status": result["status"], "fixtures": len(result["artifacts"]),
                      "exchanges": len(result["exchanges"]), "pose_comparisons": result["independent_pose_comparisons"],
                      "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
