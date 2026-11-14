#!/usr/bin/env python3
"""Author controls for C238; fixture construction is independent of checker helpers."""

from __future__ import annotations

import argparse
import ast
import base64
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
REPO = Path(__file__).absolute().parents[3]
SPEC = importlib.util.spec_from_file_location("c238_author_checker", REPO / "tools/second_target_c238/check_envelope.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
PACKAGE_ROOT = None
EVIDENCE = None
CASES = []
ROLE_SCHEMAS = {
    "geometry": "ontokin.c222.geometry-observations/0.1",
    "materials": "ontokin.c234.material-observations/0.1",
    "normals": "ontokin.c235.normal-observations/0.1",
    "poses": "ontokin.c236.pose-observations/0.1",
    "semantics": "ontokin.second-target.c237.observations/0.1",
    "corner_map": "ontokin.c238.declared-corner-map/0.1",
}
MAP_FIELDS = ["gltf_node", "gltf_primitive", "raw_triangle", "raw_corner", "raw_vertex",
              "source_mesh", "source_primitive", "source_triangle", "source_corner", "source_vertex"]


def encode(value, pretty=False):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=None if pretty else (",", ":"),
                      indent=2 if pretty else None, allow_nan=False).encode("utf-8")


def binding(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def fixtures(package_root):
    inputs = Path(package_root) / "agent-results/namespace-repair/run-01/inputs"
    raw_glb = (inputs / "after.glb").read_bytes()
    json_length = struct.unpack_from("<I", raw_glb, 12)[0]
    glb, binary = json.loads(raw_glb[20:20 + json_length]), raw_glb[28 + json_length:]
    semantic = json.loads((inputs / "after.semantic.json").read_bytes())
    reference = json.loads((inputs / "after.reference.json").read_bytes())
    objects = {value["geometry_binding"]["node"]: value for value in semantic["objects"]}
    identity = {"declared_origin": "synthetic",
                "accepted_program_revision": semantic["binding"]["accepted_program_revision"],
                "glb_sha256": hashlib.sha256(raw_glb).hexdigest()}

    def accessor(index, format_string):
        spec = glb["accessors"][index]
        view = glb["bufferViews"][spec["bufferView"]]
        offset = view.get("byteOffset", 0) + spec.get("byteOffset", 0)
        width = struct.calcsize(format_string)
        return [list(struct.unpack_from(format_string, binary, offset + item * width)) for item in range(spec["count"])]

    def matrix(t, q):
        norm = sum(value * value for value in q)
        w, x, y, z = q
        return [(w*w+x*x-y*y-z*z)/norm, 2*(x*y-w*z)/norm, 2*(x*z+w*y)/norm, t[0],
                2*(x*y+w*z)/norm, (w*w-x*x+y*y-z*z)/norm, 2*(y*z-w*x)/norm, t[1],
                2*(x*z-w*y)/norm, 2*(y*z+w*x)/norm, (w*w-x*x-y*y+z*z)/norm, t[2],
                0, 0, 0, 1]

    full_parts, geometry_parts, material_parts, pose_parts, semantic_parts, mapping, normal_rows = [], [], [], [], [], [], []
    for node in sorted(objects):
        obj = objects[node]
        mesh = glb["nodes"][node]["mesh"]
        common = {"gltf_node": node, "gltf_mesh": mesh, "element_id": obj["element_id"],
                  "source_path": obj["path"], "native_node_id": "c238-author-node-" + str(node)}
        full_parts.append({**common, "definition_id": obj["definition_id"]})
        geometry_surfaces, material_surfaces = [], []
        for primitive, source in enumerate(glb["meshes"][mesh]["primitives"]):
            original_indices = [value[0] for value in accessor(source["indices"], "<H")]
            positions = accessor(source["attributes"]["POSITION"], "<3f")
            normals = accessor(source["attributes"]["NORMAL"], "<3f")
            reversed_indices = []
            for offset in range(0, len(original_indices), 3):
                for raw_corner, source_corner in enumerate((0, 2, 1)):
                    vertex = original_indices[offset + source_corner]
                    reversed_indices.append(vertex)
                    key = [node, primitive, offset // 3, raw_corner, vertex]
                    mapping.append([*key, mesh, primitive, offset // 3, source_corner, vertex])
                    normal_rows.append({"key": key, "normal": normals[vertex]})
            geometry_surfaces.append({"gltf_primitive": primitive, "material_index": source["material"],
                                      "positions": positions, "normals": normals, "indices": reversed_indices})
            material = glb["materials"][source["material"]]["pbrMetallicRoughness"]
            color = material["baseColorFactor"]
            encoded = [12.92*c if c <= 0.0031308 else 1.055*c**(1/2.4)-0.055 for c in color[:3]]
            material_surfaces.append({"gltf_primitive": primitive, "material_index": source["material"],
                "native_material_id": "c238-author-material-" + str(node),
                "raw": {"albedo_storage": "srgb-rgb-linear-alpha", "albedo_rgb": encoded, "alpha": color[3],
                        "metallic": material["metallicFactor"], "roughness": material["roughnessFactor"],
                        "cull_mode": "back", "transparency_mode": "disabled"}})
        geometry_parts.append({**common, "display_name": "Synthetic source-byte observation", "surfaces": geometry_surfaces})
        material_parts.append({**common, "surfaces": material_surfaces})
        samples = []
        for sample in reference["samples"]:
            pose = sample["objects"][obj["path"]]
            t, q = pose["position_m"], pose["orientation_wxyz"]
            samples.append({"reference_time_seconds": sample["time_seconds"], "observed_time_seconds": float(sample["time_seconds"]),
                            "translation_m": t, "rotation_wxyz": q, "scale": [1, 1, 1], "world_matrix": matrix(t, q)})
        pose_parts.append({**common, "definition_id": obj["definition_id"], "samples": samples})
        semantic_parts.append({"sourceNode": node, "sourceMesh": mesh, "elementId": obj["element_id"],
                               "definitionId": obj["definition_id"], "sourcePath": obj["path"],
                               "destinationLabel": common["native_node_id"]})
    features = []
    for original in semantic["features"]:
        name = original["feature"]
        if name == "source_closure":
            provenance, capability = "retained_external", "retained_source"
        elif name in ("action_execution", "live_physics", "source_reconstruction"):
            provenance, capability = "unsupported", "unsupported"
        elif name in ("primitive_geometry", "numeric_precision"):
            provenance, capability = "observer_copied", "approximated_representation"
        elif name == "world_motion":
            provenance, capability = "observer_copied", "baked_playback"
        else:
            provenance, capability = "observer_copied", "descriptive_metadata"
        features.append({**original, "provenance": provenance, "capability": capability})
    semantic_value = {
        "schema": ROLE_SCHEMAS["semantics"], "producer": {"kind": "synthetic", "name": "C238 independent author byte decoder"},
        "programRevision": identity["accepted_program_revision"], "parts": semantic_parts,
        "semantics": semantic, "features": features,
        "retainedFiles": [{"kind": kind, "base64": base64.b64encode((inputs / filename).read_bytes()).decode("ascii")}
                         for kind, filename in (("program_bundle", "after.program.bundle.json"), ("glb", "after.glb"),
                                                ("semantic_sidecar", "after.semantic.json"), ("source_normal_payload", "source-payload.json"))],
        "capabilities": {"liveFollowing": False, "liveHinges": False, "actionExecution": False, "livePhysics": False,
                         "sourceReconstruction": False, "rigidBodyCount": 0, "controllerCount": 0,
                         "representedBodyMassKg": 0.0, "motionAuthority": semantic["scene"]["motion_authority"]}}
    values = {
        "geometry": {"schema": ROLE_SCHEMAS["geometry"], **identity,
                     "coordinate_system": {"position_unit": "m", "basis": "gltf-rh-y-up-identity", "winding": "godot-clockwise-reverse-once"},
                     "parts": geometry_parts},
        "materials": {"schema": ROLE_SCHEMAS["materials"], **identity, "geometry_observation": {}, "parts": material_parts},
        "normals": {"schema": ROLE_SCHEMAS["normals"], **identity, "normal_frame": "gltf-object-local-right-handed-y-up",
                    "geometry_observation": {}, "records": normal_rows},
        "poses": {"schema": ROLE_SCHEMAS["poses"], **identity,
                  "coordinate_system": {"position_unit": "m", "time_unit": "s", "basis": "gltf-rh-y-up-identity",
                                        "quaternion_order": "wxyz", "matrix_layout": "row-major-4x4"}, "parts": pose_parts},
        "semantics": semantic_value,
        "corner_map": {"schema": ROLE_SCHEMAS["corner_map"], **identity, "geometry_observation": {},
                       "corner_map_fields": MAP_FIELDS, "corner_map": mapping}}
    envelope = {"schema": "ontokin.c238.observation-envelope/0.1", "capture": {"kind": "synthetic", "label": "C238 author fixture"},
                "authority": {key: identity[key] for key in ("accepted_program_revision", "glb_sha256")},
                "parts": full_parts, "members": []}
    return envelope, values


def write_set(root, envelope, values, update_dependencies=True, pretty=False):
    root.mkdir(parents=True, exist_ok=True)
    raw_geometry = encode(values["geometry"], pretty)
    if update_dependencies:
        geometry_binding = binding(raw_geometry)
        for role in ("materials", "corner_map"):
            values[role]["geometry_observation"] = copy.deepcopy(geometry_binding)
        values["normals"]["geometry_observation"] = {
            **geometry_binding, "corner_map_sha256": hashlib.sha256(encode(values["corner_map"]["corner_map"])).hexdigest()}
    envelope["members"] = []
    for role in ROLE_SCHEMAS:
        raw = raw_geometry if role == "geometry" else encode(values[role], pretty)
        filename = role + ".json"
        (root / filename).write_bytes(raw)
        envelope["members"].append({"role": role, "path": filename, "schema": ROLE_SCHEMAS[role], **binding(raw)})
    (root / "envelope.json").write_bytes(encode(envelope, pretty))
    return root / "envelope.json"


def record(label, report):
    encoded = encode(report)
    CASES.append({"label": label, "result": report["result"], "error": report.get("error"),
                  "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(),
                  "component_results": report["component_results"],
                  "corners": len(report.get("corner_map_projection", {}).get("corner_map", []))})


class EnvelopeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_envelope, cls.original_values = fixtures(PACKAGE_ROOT)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="c238-author-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.envelope = copy.deepcopy(self.original_envelope)
        self.values = copy.deepcopy(self.original_values)
        self.path = write_set(self.root, self.envelope, self.values)

    def rewrite(self, **options):
        self.path = write_set(self.root, self.envelope, self.values, **options)

    def envelope_only(self):
        self.path.write_bytes(encode(self.envelope))

    def passed(self, label=None, path=None):
        report = checker.check_envelope(PACKAGE_ROOT, path or self.path)
        record(label or self.id(), report)
        self.assertEqual("PASS_CPU_ENVELOPE_ADMISSION", report["result"])
        self.assertEqual({"NOT_RUN"}, set(report["component_results"].values()))
        self.assertTrue(all(status == "PASS" for status in report["stages"].values()))
        self.assertFalse(report["limits"]["full_r07_acceptance"])
        return report

    def refused(self, code=None, label=None, path=None, root=None):
        with self.assertRaises(checker.CheckError) as raised:
            checker.check_envelope(root or PACKAGE_ROOT, path or self.path)
        report = raised.exception.report
        record(label or self.id(), report)
        self.assertEqual("FAIL_CLOSED", report["result"])
        if code is not None:
            self.assertEqual(code, raised.exception.code)
        self.assertEqual({"NOT_RUN"}, set(report["component_results"].values()))
        return report

    def test_complete_synthetic_report(self):
        report = self.passed()
        self.assertEqual(self.envelope["parts"], report["parts"])
        self.assertEqual(self.values["corner_map"]["corner_map"], report["corner_map_projection"]["corner_map"])
        self.assertEqual(23400, report["normal_projection"]["corners"])
        self.assertEqual(126, report["pose_projection"]["samples"])
        self.assertEqual(14, report["semantic_projection"]["features"])
        for role in ROLE_SCHEMAS:
            observed = next(row for row in report["members"] if row["role"] == role)
            self.assertEqual(binding((self.root / (role + ".json")).read_bytes()), observed["inspected_binding"])
        for role in ("geometry_projection", "material_projection"):
            for row in report[role]["part_projections"]:
                expected = next(p for p in self.envelope["parts"] if p["gltf_node"] == row["gltf_node"])
                self.assertEqual(expected["definition_id"], row["authority_derived_fields"]["definition_id"])
        if EVIDENCE:
            (EVIDENCE / "positive-report.json").write_bytes(encode(report))
            retained = EVIDENCE / "fixture"
            retained.mkdir(exist_ok=True)
            for item in self.root.iterdir():
                shutil.copy2(item, retained / item.name)

    def test_unattested_origin_stays_unattested(self):
        self.envelope["capture"]["kind"] = "unattested-native"
        for role, value in self.values.items():
            if role == "semantics":
                value["producer"]["kind"] = "declared_destination"
            else:
                value["declared_origin"] = "unattested-native"
        self.rewrite()
        report = self.passed()
        self.assertFalse(report["capture_declaration"]["attested"])
        self.assertFalse(report["limits"]["native_receiving_evidence"])

    def test_outer_reordering_and_reserialization(self):
        self.envelope["parts"].reverse()
        for role in ("geometry", "materials", "poses", "semantics"):
            self.values[role]["parts"].reverse()
        self.values["normals"]["records"].reverse()
        self.values["semantics"]["features"].reverse()
        self.values["semantics"]["retainedFiles"].reverse()
        self.rewrite(pretty=True)
        self.envelope["members"].reverse()
        self.envelope_only()
        self.passed()

    def test_original_display_name_domain(self):
        part = self.values["geometry"]["parts"][0]
        for value in ("\x00", "é" * 4096, ""):
            part["display_name"] = value
            self.rewrite()
            self.passed("display allowed " + str(len(value)))
        for value in ("é" * 4097, False):
            part["display_name"] = value
            self.rewrite()
            self.refused("TEXT", "display rejected")

    def test_original_material_label_domain(self):
        surface = self.values["materials"]["parts"][0]["surfaces"][0]
        surface["native_material_id"] = "é" * 4096
        self.rewrite()
        self.passed("material allowed 4096 Unicode characters")
        for value in ("é" * 4097, "\x00", ""):
            surface["native_material_id"] = value
            self.rewrite()
            self.refused("TEXT", "material label rejected")

    def test_original_semantic_producer_name_domain(self):
        for value in ("\x00", "é" * (1024 * 1024 // 2)):
            self.values["semantics"]["producer"]["name"] = value
            self.rewrite()
            self.passed("producer allowed " + str(len(value)))
        self.values["semantics"]["producer"]["name"] = ""
        self.rewrite()
        self.refused("TEXT", "empty producer name")
        self.values["semantics"]["producer"]["name"] = "é" * (1024 * 1024 // 2 + 1)
        self.rewrite()
        self.refused("JSON_BOUNDS", "producer exceeds UTF8 string limit")

    def test_lossy_values_remain_pending(self):
        self.values["geometry"]["parts"][0]["surfaces"][0]["positions"][0][0] += 99
        self.values["materials"]["parts"][0]["surfaces"][0]["raw"]["cull_mode"] = "front"
        sample = self.values["poses"]["parts"][0]["samples"][0]
        sample["translation_m"] = [999, 888, 777]
        sample["world_matrix"] = [9] * 16
        sample["scale"] = [2, 2, 2]
        self.values["semantics"]["semantics"]["scene"]["motion_authority"] = "changed declaration"
        self.values["semantics"]["retainedFiles"][0]["base64"] = ""
        self.rewrite()
        report = self.passed()
        self.assertEqual("NOT_RUN", report["pose_projection"]["matrix_consistency"])
        self.assertEqual("NOT_RUN", report["semantic_projection"]["semantic_equality"])
        self.assertTrue(any(row["bytes"] == 0 for row in report["semantic_projection"]["decoded_retained_bindings"]))

    def test_consistent_triangle_permutation_is_declaration_only(self):
        rows = self.values["corner_map"]["corner_map"]
        selected = [row for row in rows if row[0] == rows[0][0]]
        first, second = selected[:3], selected[3:6]
        source_a, source_b = [row[5:] for row in first], [row[5:] for row in second]
        for i in range(3):
            first[i][5:], second[i][5:] = source_b[i], source_a[i]
        self.rewrite()
        report = self.passed()
        self.assertEqual("NOT_RUN", report["corner_map_projection"]["geometric_correspondence"])

    def test_missing_members(self):
        for index, role in enumerate(ROLE_SCHEMAS):
            with self.subTest(role=role):
                self.rewrite()
                (self.root / (role + ".json")).unlink()
                report = self.refused("MISSING_MEMBER", role)
                self.assertEqual(index, len(report["members"]))

    def test_duplicate_and_missing_descriptors(self):
        self.envelope["members"].pop()
        self.envelope_only()
        self.refused("COUNT", "missing descriptor")
        self.rewrite()
        self.envelope["members"][-1] = copy.deepcopy(self.envelope["members"][0])
        self.envelope_only()
        self.refused("IDENTITY", "duplicate descriptor")

    def test_path_refusals(self):
        for path in ("../geometry.json", "/geometry.json", "folder/geometry.json", ".hidden", "geometry\\json", "", "a/../b"):
            with self.subTest(path=path):
                self.rewrite()
                self.envelope["members"][0]["path"] = path
                self.envelope_only()
                self.refused("PATH", path)
        self.rewrite()
        self.refused("PATH", "traversal envelope", path=str(self.root / ".." / self.root.name / "envelope.json"))

    def test_member_byte_bindings(self):
        for field, value in (("bytes", True), ("bytes", 1), ("sha256", "0" * 64), ("sha256", "A" * 64)):
            with self.subTest(field=field, value=value):
                self.rewrite()
                self.envelope["members"][0][field] = value
                self.envelope_only()
                self.refused(label=field + str(value))

    def test_corruption_and_stale_dependency(self):
        with (self.root / "geometry.json").open("ab") as output:
            output.write(b" ")
        self.refused("MEMBER_BINDING", "changed member")
        self.rewrite()
        self.values["geometry"]["parts"][0]["display_name"] += " changed"
        self.rewrite(update_dependencies=False)
        self.refused("DEPENDENCY", "stale dependent geometry digest")

    def test_unknown_schemas(self):
        self.envelope["schema"] = "unknown"
        self.envelope_only()
        self.refused("SCHEMA", "envelope")
        self.envelope["schema"] = "ontokin.c238.observation-envelope/0.1"
        for role in ROLE_SCHEMAS:
            with self.subTest(role=role):
                original = self.values[role]["schema"]
                self.values[role]["schema"] = "unknown"
                self.rewrite()
                report = self.refused("SCHEMA", role)
                self.assertEqual(role, report["members"][-1]["role"])
                self.assertEqual("NOT_RUN", report["members"][-1]["schema_admission"])
                self.values[role]["schema"] = original

    def test_source_identity_changes(self):
        for role in ("geometry", "materials", "poses", "semantics"):
            for field in (("sourceNode", "sourceMesh", "elementId", "definitionId", "sourcePath") if role == "semantics" else
                          ("gltf_node", "gltf_mesh", "element_id", "source_path") + (("definition_id",) if role == "poses" else ())):
                with self.subTest(role=role, field=field):
                    saved = copy.deepcopy(self.values[role]["parts"][0][field])
                    self.values[role]["parts"][0][field] = 999 if type(saved) is int else ["wrong"] if type(saved) is list else "wrong"
                    self.rewrite()
                    self.refused(label=role + "/" + field)
                    self.values[role]["parts"][0][field] = saved

    def test_envelope_full_identities_and_bool_indices(self):
        for field in ("gltf_node", "gltf_mesh", "element_id", "definition_id", "source_path"):
            saved = copy.deepcopy(self.envelope["parts"][0][field])
            self.envelope["parts"][0][field] = True if type(saved) is int else ["wrong"] if type(saved) is list else "wrong"
            self.envelope_only()
            self.refused(label=field)
            self.envelope["parts"][0][field] = saved
        self.envelope["parts"][0] = copy.deepcopy(self.envelope["parts"][1])
        self.envelope_only()
        self.refused("IDENTITY", "duplicate full part")

    def test_revision_and_artifact_bindings(self):
        for role in ROLE_SCHEMAS:
            field = "programRevision" if role == "semantics" else "accepted_program_revision"
            saved = self.values[role][field]
            self.values[role][field] = "sha256:" + "0" * 64
            self.rewrite()
            self.refused("IDENTITY", role + " revision")
            self.values[role][field] = saved

    def test_mixed_origins(self):
        for role in ROLE_SCHEMAS:
            value = self.values[role]
            saved = copy.deepcopy(value)
            if role == "semantics":
                value["producer"]["kind"] = "declared_destination"
            else:
                value["declared_origin"] = "unattested-native"
            self.rewrite()
            self.refused("PROVENANCE", role)
            self.values[role] = saved

    def test_native_labels(self):
        for role in ("geometry", "materials", "poses", "semantics"):
            field = "destinationLabel" if role == "semantics" else "native_node_id"
            saved = self.values[role]["parts"][0][field]
            self.values[role]["parts"][0][field] = "wrong-native-label"
            self.rewrite()
            self.refused("IDENTITY", role)
            self.values[role]["parts"][0][field] = saved

    def test_geometry_inventory_and_indices(self):
        surface = self.values["geometry"]["parts"][0]["surfaces"][0]
        mutations = [("indices", surface["indices"][:-1]), ("indices", [True] + surface["indices"][1:]),
                     ("indices", [10**9] + surface["indices"][1:]), ("normals", surface["normals"][:-1]),
                     ("positions", [[1, 2]] + surface["positions"][1:])]
        for field, value in mutations:
            saved = copy.deepcopy(surface[field])
            surface[field] = value
            self.rewrite()
            self.refused(label=field + str(len(value)))
            surface[field] = saved

    def test_complete_declared_corner_map(self):
        mapping = self.values["corner_map"]["corner_map"]
        mutations = [mapping[:-1], [mapping[0]] + mapping[:-1], list(reversed(mapping))]
        for changed in mutations:
            self.values["corner_map"]["corner_map"] = changed
            self.rewrite()
            self.refused(label="map inventory")
        self.values["corner_map"]["corner_map"] = mapping
        for column, value in ((0, 999), (4, 99999), (5, 999), (6, 999), (7, 99999), (8, 9), (9, 99999), (0, True)):
            saved = mapping[0][column]
            mapping[0][column] = value
            self.rewrite()
            self.refused(label="map column " + str(column))
            mapping[0][column] = saved

    def test_map_winding_and_hash(self):
        mapping = self.values["corner_map"]["corner_map"]
        mapping[1][7:], mapping[2][7:] = mapping[2][7:], mapping[1][7:]
        self.rewrite()
        self.refused("WINDING", "wrong winding")
        mapping[1][7:], mapping[2][7:] = mapping[2][7:], mapping[1][7:]
        self.values["normals"]["geometry_observation"]["corner_map_sha256"] = "0" * 64
        self.rewrite(update_dependencies=False)
        self.refused("DEPENDENCY", "map digest")

    def test_normal_keys_and_raw_copy(self):
        records = self.values["normals"]["records"]
        records[0]["key"][0] = 999
        self.rewrite()
        self.refused("CORNER_IDENTITY", "normal key")
        self.values["normals"] = copy.deepcopy(self.original_values["normals"])
        self.values["normals"]["records"][0]["normal"] = [9, 8, 7]
        self.rewrite()
        self.refused("RAW_NORMAL_BINDING", "normal copy")
        self.values["normals"]["records"][0]["normal"] = [0, 0, 0]
        self.rewrite()
        self.refused("VECTOR", "zero normal")

    def test_material_domains_and_resource_alias(self):
        surface = self.values["materials"]["parts"][0]["surfaces"][0]
        for field, value in (("metallic", True), ("roughness", 2), ("albedo_storage", "linear"), ("cull_mode", "unknown")):
            saved = surface["raw"][field]
            surface["raw"][field] = value
            self.rewrite()
            self.refused(label="material " + field)
            surface["raw"][field] = saved
        other = self.values["materials"]["parts"][1]["surfaces"][0]
        other["native_material_id"] = surface["native_material_id"]
        other["raw"]["roughness"] = 0.12345
        self.rewrite()
        self.refused("RESOURCE_BINDING", "material resource")

    def test_pose_slots_and_domains(self):
        samples = self.values["poses"]["parts"][0]["samples"]
        for field, value in (("reference_time_seconds", "999"), ("observed_time_seconds", True),
                             ("rotation_wxyz", [0, 0, 0, 0]), ("scale", [0, 1, 1]), ("world_matrix", [1] * 15)):
            saved = samples[0][field]
            samples[0][field] = value
            self.rewrite()
            self.refused(label="pose " + field)
            samples[0][field] = saved
        samples[1] = copy.deepcopy(samples[0])
        self.rewrite()
        self.refused("IDENTITY", "duplicate pose time")

    def test_semantic_shape_provenance_capabilities(self):
        self.values["semantics"]["semantics"]["invented"] = 1
        self.rewrite()
        self.refused("SCHEMA", "semantic shape")
        del self.values["semantics"]["semantics"]["invented"]
        self.values["semantics"]["capabilities"]["livePhysics"] = True
        self.rewrite()
        self.refused("PROVENANCE", "live physics")
        self.values["semantics"]["capabilities"]["livePhysics"] = False
        self.values["semantics"]["features"][0]["provenance"] = "invented"
        self.rewrite()
        self.refused("PROVENANCE", "invented provenance")

    def test_retained_base64_and_sets(self):
        row = self.values["semantics"]["retainedFiles"][0]
        for value in ("YQ", "YQ== ", "YQ==\n", "!!", "é", "YR=="):
            row["base64"] = value
            self.rewrite()
            self.refused("ENCODING", value)
        self.values["semantics"]["retainedFiles"].pop()
        self.rewrite()
        self.refused("COUNT", "missing retained file")

    def test_unknown_and_missing_fields(self):
        for role in ROLE_SCHEMAS:
            self.values[role]["unexpected"] = True
            self.rewrite()
            self.refused("SCHEMA", role)
            del self.values[role]["unexpected"]

    def test_json_failure_cases(self):
        for raw in (b'{"schema":1,"schema":2}', b'{"value":NaN}', b'{"value":1e999}', b'{"value":"\\ud800"}', b"{", b"\xff"):
            self.path.write_bytes(raw)
            self.refused("JSON", repr(raw))
        self.path.write_bytes(encode({"nested": [[[[1]]]]}))
        self.refused("SCHEMA", "wrong schema shape")

    def test_json_depth_value_and_string_limits(self):
        self.path.write_bytes(b'{"x":' + b"["*66 + b"0" + b"]"*66 + b"}")
        self.refused("JSON_BOUNDS", "depth")
        self.path.write_bytes(encode({"x": [0] * 10001}))
        self.refused("JSON_BOUNDS", "value count")
        self.rewrite()
        self.values["semantics"]["producer"]["name"] = "a" * (1024*1024 + 1)
        self.rewrite()
        self.refused("JSON_BOUNDS", "string bytes")

    def test_empty_and_oversize_files(self):
        self.path.write_bytes(b"")
        self.refused("SIZE", "empty")
        self.path.write_bytes(b" " * (64*1024 + 1))
        self.refused("SIZE", "oversize envelope")
        self.rewrite()
        with (self.root / "materials.json").open("wb") as output:
            output.truncate(256*1024 + 1)
        self.refused("SIZE", "oversize material")

    def test_symlinks_nonregular_and_hardlinks(self):
        target = self.root / "geometry.json"
        backup = self.root / "original.json"
        target.rename(backup)
        target.symlink_to(backup.name)
        self.refused("FILE", "file symlink")
        target.unlink()
        os.mkfifo(target)
        self.refused("FILE", "fifo")
        target.unlink()
        target.mkdir()
        self.refused("FILE", "directory")
        target.rmdir()
        backup.rename(target)
        other = self.root / "corner_map.json"
        other.unlink()
        os.link(self.root / "normals.json", other)
        descriptor = next(item for item in self.envelope["members"] if item["role"] == "corner_map")
        descriptor.update(binding(other.read_bytes()))
        self.envelope_only()
        self.refused("ALIAS", "hardlink")

    def test_ancestor_symlink(self):
        with tempfile.TemporaryDirectory(prefix="c238-author-link-") as root:
            alias = Path(root) / "alias"
            alias.symlink_to(self.root, target_is_directory=True)
            self.refused(path=alias / "envelope.json", label="ancestor symlink")

    def test_midread_metadata_change(self):
        original = checker.os.read
        changed = False
        def alter(fd, size):
            nonlocal changed
            raw = original(fd, size)
            if not changed and raw.startswith(b'{"authority"'):
                changed = True
                current = self.path.stat()
                os.utime(self.path, ns=(current.st_atime_ns, current.st_mtime_ns + 1000000))
            return raw
        with mock.patch.object(checker.os, "read", side_effect=alter):
            self.refused("CHANGED", "midread change")
        self.assertTrue(changed)

    def test_final_directory_entry_replacement(self):
        original = checker._Snapshot.finish
        def replace(snapshot):
            path = self.root / "poses.json"
            replacement = self.root / "replacement.json"
            replacement.write_bytes(path.read_bytes())
            replacement.replace(path)
            return original(snapshot)
        with mock.patch.object(checker._Snapshot, "finish", replace):
            self.refused("CHANGED", "final replacement")

    def test_fresh_authority_each_call(self):
        copied = self.root / "authority"
        for relative in checker.c221.INPUT_PATHS:
            destination = copied / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(PACKAGE_ROOT) / relative, destination)
        report = checker.check_envelope(copied, self.path)
        record("fresh first", report)
        original = copied / checker.c221.INPUT_PATHS[0]
        raw = bytearray(original.read_bytes())
        raw[-1] ^= 1
        original.write_bytes(raw)
        report = self.refused(root=copied, label="fresh second refused")
        self.assertEqual("authority", report["error"]["stage"])
        self.assertEqual("NOT_RUN", report["stages"]["envelope"])

    def test_cli_success_refusal_and_arguments(self):
        command = [sys.executable, "-IB", str(REPO / "tools/second_target_c238/check_envelope.py")]
        for arguments, expected in ((["--package-root", str(PACKAGE_ROOT), "--envelope", str(self.path)], 0),
                                    (["--package-root", str(PACKAGE_ROOT), "--envelope", str(self.root / "absent.json")], 1),
                                    (["--package-root", str(PACKAGE_ROOT)], 2)):
            completed = subprocess.run(command + arguments, text=True, capture_output=True, timeout=60)
            self.assertEqual(expected, completed.returncode, completed.stderr)
            self.assertEqual("", completed.stderr)
            report = json.loads(completed.stdout)
            record("CLI " + str(expected), report)
            self.assertEqual(1, len(completed.stdout.splitlines()))

    def test_no_component_or_native_execution(self):
        tree = ast.parse((REPO / "tools/second_target_c238/check_envelope.py").read_text())
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        self.assertFalse(any(name and (name.startswith("ontokin") or name in ("subprocess", "socket")) for name in imports))
        text = (REPO / "tools/second_target_c238/check_envelope.py").read_text()
        for forbidden in ("c222.check_observations(", "check_materials(", "check_normals(", "check_poses(", "check_semantics("):
            self.assertNotIn(forbidden, text)
        before = set(self.root.iterdir())
        self.passed()
        self.assertEqual(before, set(self.root.iterdir()))


def main(argv=None):
    global PACKAGE_ROOT, EVIDENCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--evidence-dir")
    args = parser.parse_args(argv)
    PACKAGE_ROOT = Path(args.package_root).absolute()
    EVIDENCE = Path(args.evidence_dir).absolute() if args.evidence_dir else None
    if EVIDENCE:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EnvelopeControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {"schema": "ontokin.c238.author-controls/0.1", "tests": result.testsRun,
               "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
               "successful": result.wasSuccessful(), "cases": CASES,
               "environment": {"python": sys.version, "executable": sys.executable,
                               "platform": platform.platform(), "machine": platform.machine()},
               "source_sha256": hashlib.sha256((REPO / "tools/second_target_c238/check_envelope.py").read_bytes()).hexdigest(),
               "controls_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if EVIDENCE:
        (EVIDENCE / "SUMMARY.json").write_bytes(encode(summary))
    print(json.dumps({key: summary[key] for key in ("tests", "failures", "errors", "skips", "successful")}, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

