#!/usr/bin/env python3
"""C239 complete author controls using separately decoded original fixture bytes."""

from __future__ import annotations

import argparse
import ast
import base64
import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
import lzma
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import struct
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.dont_write_bytecode = True
REPO = Path(__file__).absolute().parents[3]
SPEC = importlib.util.spec_from_file_location("c239_author_checker", REPO / "tools/second_target_c239/check_combined.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
PACKAGE_ROOT = None
EVIDENCE = None
REPORT_STREAM = None
CASES = []
ASSERTIONS = 0

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
                  "source_path": obj["path"], "native_node_id": "c239-author-node-" + str(node)}
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
                "native_material_id": "c239-author-material-" + str(node),
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
        "schema": ROLE_SCHEMAS["semantics"], "producer": {"kind": "synthetic", "name": "C239 author source-byte decoder"},
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
    envelope = {"schema": "ontokin.c238.observation-envelope/0.1", "capture": {"kind": "synthetic", "label": "C239 author fixture"},
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
    raw = encode(report)
    CASES.append({"case": label, "result": report["result"], "result_class": report["result_class"],
                  "error": report.get("error"), "report_bytes": len(raw), "report_sha256": hashlib.sha256(raw).hexdigest(),
                  "components": {tag: {k: row[k] for k in ("state", "result", "classification")} for tag, row in report["components"].items()},
                  "snapshot_valid": report["snapshot_valid"]})
    if REPORT_STREAM is not None:
        REPORT_STREAM.write(encode({"case": label, "report": report}) + b"\n")


def independent_matrix(t, q, scale):
    magnitude = max(map(abs, q))
    scaled = [float(value / magnitude) for value in q]
    length = math.sqrt(sum(value * value for value in scaled))
    w, x, y, z = [value / length for value in scaled]
    return [(1-2*y*y-2*z*z)*scale[0], (2*x*y-2*w*z)*scale[1], (2*x*z+2*w*y)*scale[2], t[0],
            (2*x*y+2*w*z)*scale[0], (1-2*x*x-2*z*z)*scale[1], (2*y*z-2*w*x)*scale[2], t[1],
            (2*x*z-2*w*y)*scale[0], (2*y*z+2*w*x)*scale[1], (1-2*x*x-2*y*y)*scale[2], t[2],
            0, 0, 0, 1]


class CombinedControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.envelope, cls.values = fixtures(PACKAGE_ROOT)
        cls.modules = checker._load_components()
        cls.expected_map = copy.deepcopy(cls.values["corner_map"]["corner_map"])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="c239-author-control-")
        self.root = Path(self.temporary.name)
        self.e, self.v = copy.deepcopy(self.envelope), copy.deepcopy(self.values)

    def tearDown(self):
        self.temporary.cleanup()

    def call(self, label, expected, e=None, v=None, package_root=None, pretty=False, inspect=True):
        e, v = self.e if e is None else e, self.v if v is None else v
        path = write_set(self.root / "input", e, v, pretty=pretty)
        report = checker.check_combined(package_root or PACKAGE_ROOT, path)
        record(label, report)
        self.assertEqual(report["result"], expected, report.get("error") or report["component_refusals"])
        self.assertTrue(report["scratch_cleanup"]["removed"])
        self.assertEqual(report["limits"], checker._base_report()["limits"])
        if inspect and report["snapshot_valid"]:
            self.inspect_complete(report)
        return report

    def inspect_complete(self, report):
        global ASSERTIONS
        self.assertEqual(len(report["parts"]), 18)
        self.assertEqual(len(report["snapshot"]["files"]), 15)
        self.assertEqual(len(report["snapshot_boundaries"]), 13)
        self.assertEqual(report["admission"]["component_results"], {tag: "NOT_RUN" for tag in checker.COMPONENTS})
        self.assertEqual(report["source_binding"], report["source_binding_after"])
        self.assertEqual(len(report["source_binding"]["inherited_files"]), 7)
        self.assertTrue(report["source_binding"]["module_origins"])
        for part, expected in zip(report["parts"], self.envelope["parts"]):
            self.assertEqual(part, expected)
            ASSERTIONS += 1
        for tag, row in report["components"].items():
            self.assertEqual(row["state"], "EXECUTED")
            self.assertTrue(row["snapshot_valid"])
            component = row["report"]
            if component is None or row["classification"] == "structural_refusal":
                continue
            if tag == "C222":
                self.assertEqual(component["structure"]["corners"], 23400)
                self.assertEqual(component["correspondence"]["corner_map"], self.expected_map)
                self.assertEqual(report["correspondence"]["derived_map"], self.expected_map)
                for actual, expected in zip(component["correspondence"]["corner_map"], self.expected_map):
                    self.assertEqual(actual, expected)
                    ASSERTIONS += 1
            elif tag == "C234":
                self.assertEqual(component["comparison"]["numeric_components_compared"], 108)
                self.assertEqual(component["comparison"]["exact_mode_checks"], 36)
                self.assertEqual(len(component["comparison"]["rows"]), 18)
            elif tag == "C235":
                self.assertEqual(len(component["comparison"]["rows"]), 23400)
                for actual, mapping in zip(component["comparison"]["rows"], self.expected_map):
                    self.assertEqual(actual["raw_key"], mapping[:5])
                    self.assertEqual(actual["source_key"], [mapping[0], *mapping[5:9]])
                    self.assertEqual(actual["source_vertex"], mapping[9])
                    ASSERTIONS += 3
            elif tag == "C236":
                self.assertEqual(len(component["comparison"]["rows"]), 126)
            else:
                self.assertEqual(len(component["partComparisons"]), 18)
                self.assertEqual(len(component["featureComparisons"]), 14)
                self.assertEqual(len(component["retentionComparisons"]), 4)
                self.assertEqual(len(component["sourceUnitInspection"]["expected"]["units"]), 2)

    def normal_loss(self, amount=0.0001, axis=0):
        part = self.v["geometry"]["parts"][0]
        surface = part["surfaces"][0]
        vertex = surface["indices"][0]
        surface["normals"][vertex][axis] += amount
        for row in self.v["normals"]["records"]:
            if row["key"][0] == part["gltf_node"] and row["key"][1] == surface["gltf_primitive"] and row["key"][4] == vertex:
                row["normal"] = copy.deepcopy(surface["normals"][vertex])

    def pose_loss(self, kind="position"):
        sample = self.v["poses"]["parts"][0]["samples"][0]
        if kind == "position":
            sample["translation_m"][0] += 0.002
        elif kind == "time":
            sample["observed_time_seconds"] += 0.000002
        elif kind == "scale":
            sample["scale"][0] = 1.0000001
        else:
            sample["rotation_wxyz"] = [math.cos(0.001), 0, 0, math.sin(0.001)]
        sample["world_matrix"] = independent_matrix(sample["translation_m"], sample["rotation_wxyz"], sample["scale"])

    def wrong_map(self):
        rows = self.v["corner_map"]["corner_map"]
        original = copy.deepcopy(rows[:6])
        for offset in range(3):
            rows[offset][5:] = original[offset+3][5:]
            rows[offset+3][5:] = original[offset][5:]

    def private_authority(self):
        result = self.root / "authority"
        pins, _ = self.modules["C221"].load_authority()
        for pin in pins["items"]:
            path = result / pin["packagePath"]
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(PACKAGE_ROOT) / pin["packagePath"], path)
        return result

    def test_01_complete_synthetic(self):
        report = self.call("complete-synthetic", "PASS_CPU_COMBINED")
        self.assertEqual(report["component_losses"], [])
        self.assertEqual(report["component_refusals"], [])
        self.assertEqual(report["correspondence"]["mismatches"], [])

    def test_02_complete_unattested_native(self):
        self.e["capture"]["kind"] = "unattested-native"
        for role in ROLE_SCHEMAS:
            if role == "semantics":
                self.v[role]["producer"]["kind"] = "declared_destination"
            else:
                self.v[role]["declared_origin"] = "unattested-native"
        self.call("complete-unattested-native", "PASS_CPU_COMBINED")

    def test_03_outer_keyed_order(self):
        self.e["parts"].reverse()
        for role in ("geometry", "materials", "poses", "semantics"):
            self.v[role]["parts"].reverse()
        self.v["normals"]["records"].reverse()
        for field in ("features", "retainedFiles"):
            self.v["semantics"][field].reverse()
        self.call("outer-keyed-order", "PASS_CPU_COMBINED")

    def test_04_reserialized_exact_dependencies(self):
        self.call("reserialized-rebound", "PASS_CPU_COMBINED", pretty=True)

    def test_05_material_numeric_and_mode_loss(self):
        for name, value in (("alpha", 0.9), ("cull_mode", "front")):
            with self.subTest(name=name):
                self.e, self.v = copy.deepcopy(self.envelope), copy.deepcopy(self.values)
                self.v["materials"]["parts"][0]["surfaces"][0]["raw"][name] = value
                report = self.call("material-" + name, "FAIL_COMPONENT_LOSS")
                row = report["components"]["C234"]
                self.assertEqual(row["result"], "FAIL_CLOSED")
                self.assertEqual(row["report"]["comparison"]["result"], "FAIL_MATERIAL_PARAMETERS")
                self.assertEqual(row["classification"], "measured_loss")

    def test_06_normal_strict_loss(self):
        self.normal_loss()
        report = self.call("normal-strict-loss", "FAIL_COMPONENT_LOSS")
        self.assertEqual(report["components"]["C235"]["result"], "FAIL_STRICT_NORMAL_LIMIT")

    def test_07_normal_public_boundary(self):
        for value, expected in ((0.000002, "PASS_CPU_COMBINED"), (math.nextafter(0.000002, math.inf), "FAIL_COMPONENT_LOSS")):
            with self.subTest(value=value):
                self.e, self.v = copy.deepcopy(self.envelope), copy.deepcopy(self.values)
                self.assertEqual(self.v["geometry"]["parts"][0]["surfaces"][0]["normals"][0][1], 0.0)
                self.assertEqual(Fraction(value) <= Fraction(1, 500000), expected == "PASS_CPU_COMBINED")
                self.normal_loss(value, axis=1)
                self.call("normal-boundary-" + repr(value), expected)

    def test_08_pose_losses(self):
        for kind in ("position", "time", "orientation", "scale"):
            with self.subTest(kind=kind):
                self.e, self.v = copy.deepcopy(self.envelope), copy.deepcopy(self.values)
                self.pose_loss(kind)
                report = self.call("pose-" + kind, "FAIL_COMPONENT_LOSS")
                self.assertEqual(report["components"]["C236"]["result"], "FAIL_SCALE_PROFILE" if kind == "scale" else "FAIL_POSE_LIMIT")

    def test_09_matrix_structural_refusal(self):
        self.v["poses"]["parts"][0]["samples"][0]["world_matrix"][3] += 1
        report = self.call("matrix-structural-refusal", "FAIL_COMPONENT_REFUSAL")
        self.assertEqual(report["components"]["C236"]["report"]["comparison"]["result"], "NOT_RUN")
        self.assertEqual(report["components"]["C237"]["classification"], "pass")

    def test_10_semantic_and_feature_losses(self):
        self.v["semantics"]["semantics"]["objects"][0]["path"] += "-changed"
        self.v["semantics"]["features"][0]["reason"] += " changed"
        report = self.call("semantic-feature-loss", "FAIL_COMPONENT_LOSS")
        self.assertEqual(report["components"]["C237"]["result"], "FAIL_MEASURED_SEMANTIC_RETENTION")

    def test_11_retained_files_and_source_units(self):
        for kind in ("program_bundle", "glb", "semantic_sidecar", "source_normal_payload"):
            with self.subTest(kind=kind):
                self.e, self.v = copy.deepcopy(self.envelope), copy.deepcopy(self.values)
                row = next(r for r in self.v["semantics"]["retainedFiles"] if r["kind"] == kind)
                row["base64"] = ""
                report = self.call("retention-empty-" + kind, "FAIL_COMPONENT_LOSS")
                component = report["components"]["C237"]["report"]
                match = next(r for r in component["retentionComparisons"] if r["kind"] == kind)
                self.assertEqual(match["status"], "absent")
                self.assertEqual(component["sourceUnitInspection"]["equal"], kind != "program_bundle")

    def test_12_retained_reserialization(self):
        row = self.v["semantics"]["retainedFiles"][0]
        row["base64"] = base64.b64encode(base64.b64decode(row["base64"]) + b"\n").decode()
        report = self.call("retained-reserialization", "FAIL_COMPONENT_LOSS")
        self.assertTrue(report["components"]["C237"]["report"]["sourceUnitInspection"]["equal"])

    def test_13_all_independent_losses(self):
        self.v["materials"]["parts"][0]["surfaces"][0]["raw"]["roughness"] = 0.1
        self.normal_loss()
        self.pose_loss()
        self.v["semantics"]["retainedFiles"][0]["base64"] = ""
        report = self.call("simultaneous-independent-losses", "FAIL_COMPONENT_LOSS")
        self.assertEqual(report["component_losses"], ["C234", "C235", "C236", "C237"])

    def test_14_wrong_declared_map_and_mixed_loss(self):
        self.wrong_map()
        self.v["materials"]["parts"][0]["surfaces"][0]["raw"]["alpha"] = 0.9
        self.pose_loss()
        self.v["semantics"]["retainedFiles"][0]["base64"] = ""
        report = self.call("wrong-map-with-independent-losses", "FAIL_COMPONENT_REFUSAL")
        self.assertEqual(report["correspondence"]["result"], "FAIL_DECLARED_CORRESPONDENCE")
        self.assertEqual(len(report["correspondence"]["mismatches"]), 6)
        self.assertEqual(report["component_refusals"], ["C235"])
        self.assertEqual(report["component_losses"], ["C234", "C236", "C237"])

    def test_15_geometry_refusal_continues_independent_checks(self):
        self.v["geometry"]["parts"][0]["surfaces"][0]["positions"][0][0] += 0.000001
        self.pose_loss()
        self.v["semantics"]["retainedFiles"][0]["base64"] = ""
        report = self.call("geometry-refusal-with-independent-losses", "FAIL_COMPONENT_REFUSAL")
        self.assertEqual(report["component_refusals"], ["C222", "C234", "C235"])
        self.assertEqual(report["component_losses"], ["C236", "C237"])
        self.assertEqual(report["correspondence"]["result"], "NOT_RUN")

    def test_16_stale_mixed_and_swapped_admission(self):
        mutations = (
            ("stale-envelope", lambda: self.e["authority"].__setitem__("accepted_program_revision", "sha256:" + "0"*64)),
            ("mixed-origin", lambda: self.v["poses"].__setitem__("declared_origin", "unattested-native")),
            ("swapped-identity", lambda: self.v["materials"]["parts"][0].__setitem__("element_id", self.v["materials"]["parts"][1]["element_id"])),
            ("raw-normal-mismatch", lambda: self.v["normals"]["records"][0].__setitem__("normal", [0.25, 0.0, 0.0])),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                self.e, self.v = copy.deepcopy(self.envelope), copy.deepcopy(self.values)
                mutate()
                with mock.patch.object(checker, "_invoke_component", side_effect=AssertionError("Unexpected component start")) as invoked:
                    self.call(label, "FAIL_CLOSED")
                invoked.assert_not_called()

    def test_17_missing_corrupt_and_wrong_bindings(self):
        for label in ("missing", "corrupt", "wrong-length", "wrong-digest", "missing-envelope-member"):
            with self.subTest(label=label):
                path = write_set(self.root / "input", copy.deepcopy(self.envelope), copy.deepcopy(self.values))
                target = path.parent / "geometry.json"
                if label == "missing":
                    target.unlink()
                elif label == "corrupt":
                    target.write_bytes(target.read_bytes() + b" ")
                else:
                    doc = json.loads(path.read_bytes())
                    if label == "wrong-length":
                        doc["members"][0]["bytes"] += 1
                    elif label == "wrong-digest":
                        doc["members"][0]["sha256"] = "0"*64
                    else:
                        doc["members"].pop()
                    path.write_bytes(encode(doc))
                report = checker.check_combined(PACKAGE_ROOT, path)
                record(label, report)
                self.assertEqual(report["result"], "FAIL_CLOSED")
                self.assertTrue(all(r["state"] == "NOT_RUN" for r in report["components"].values()))

    def test_18_unsafe_input_files(self):
        for label in ("symlink-member", "symlink-ancestor", "fifo-member", "alias-member", "traversal"):
            with self.subTest(label=label):
                directory = self.root / label
                path = write_set(directory, copy.deepcopy(self.envelope), copy.deepcopy(self.values))
                target = directory / "geometry.json"
                if label == "symlink-member":
                    copy_path = directory / "original-geometry"
                    target.rename(copy_path)
                    target.symlink_to(copy_path)
                elif label == "symlink-ancestor":
                    link = self.root / "linked-directory"
                    link.symlink_to(directory, target_is_directory=True)
                    path = link / "envelope.json"
                elif label == "fifo-member":
                    target.unlink()
                    os.mkfifo(target)
                elif label == "alias-member":
                    other = directory / "normals.json"
                    other.unlink()
                    os.link(target, other)
                else:
                    path = directory / ".." / label / "envelope.json"
                report = checker.check_combined(PACKAGE_ROOT, path)
                record(label, report)
                self.assertEqual(report["result"], "FAIL_CLOSED")
                self.assertTrue(all(r["state"] == "NOT_RUN" for r in report["components"].values()))

    def test_19_parser_bounds_and_invalid_arguments(self):
        for label, raw in (("duplicate-envelope-key", b'{"schema":"x","schema":"y"}'),
                           ("oversized-envelope", b" "*(64*1024+1)), ("nonfinite-envelope", b'{"schema":NaN}')):
            path = self.root / (label + ".json")
            path.write_bytes(raw)
            report = checker.check_combined(PACKAGE_ROOT, path)
            record(label, report)
            self.assertEqual(report["result"], "FAIL_CLOSED")
        report = checker.check_combined(PACKAGE_ROOT, {"result": "PASS_CPU_ENVELOPE_ADMISSION"})
        record("cached-admission-is-not-a-path", report)
        self.assertEqual(report["result"], "FAIL_CLOSED")

    def test_20_original_mutation_between_admission_capture(self):
        original = checker._capture_inputs
        def mutate(package_root, envelope_path, admission, modules):
            target = Path(envelope_path).parent / "geometry.json"
            target.write_bytes(target.read_bytes() + b" ")
            return original(package_root, envelope_path, admission, modules)
        with mock.patch.object(checker, "_capture_inputs", side_effect=mutate):
            report = self.call("original-changed-before-capture", "FAIL_CLOSED")
        self.assertEqual(report["error"]["stage"], "capture")
        self.assertTrue(all(r["state"] == "NOT_RUN" for r in report["components"].values()))

    def test_21_external_mutation_after_capture_uses_private_copy(self):
        authority = self.private_authority()
        original = checker._write_private
        def mutate(root, files):
            original(root, files)
            target = self.root / "input" / "geometry.json"
            target.write_bytes(target.read_bytes() + b" ")
            pin = self.modules["C221"].INPUT_PATHS[0]
            (authority / pin).write_bytes(b"external-original-changed")
        with mock.patch.object(checker, "_write_private", side_effect=mutate):
            self.call("external-changed-after-capture", "PASS_CPU_COMBINED", package_root=authority)

    def test_22_private_replacement_addition_and_authority_changes(self):
        original = checker._invoke_component
        for kind in ("replacement", "addition", "authority"):
            with self.subTest(kind=kind):
                def mutate(tag, modules, authority_root, paths):
                    result = original(tag, modules, authority_root, paths)
                    if tag == "C222":
                        if kind == "addition":
                            (paths["geometry"].parent / "unexpected-file").write_text("extra")
                        else:
                            target = paths["geometry"] if kind == "replacement" else authority_root / modules["C221"].INPUT_PATHS[0]
                            replacement = target.with_name("replacement-file")
                            replacement.write_bytes(target.read_bytes())
                            replacement.chmod(target.stat().st_mode & 0o777)
                            replacement.replace(target)
                    return result
                with mock.patch.object(checker, "_invoke_component", side_effect=mutate):
                    report = self.call("private-" + kind, "FAIL_CLOSED")
                self.assertEqual(report["components"]["C222"]["result"], "PASS_CPU_CORRESPONDENCE")
                self.assertFalse(report["components"]["C222"]["snapshot_valid"])
                self.assertEqual(report["components"]["C234"]["state"], "NOT_RUN")

    def test_23_transitive_module_origin_change(self):
        module = self.modules["C237"].authority
        original = module.__file__
        try:
            module.__file__ = "/unrelated/stale-checkout/check_bindings.py"
            report = self.call("stale-transitive-module-origin", "FAIL_CLOSED")
            self.assertEqual(report["error"]["code"], "MODULE_ORIGIN")
        finally:
            module.__file__ = original

    def test_24_unexpected_component_exception(self):
        original = checker._invoke_component
        def fail(tag, *args):
            if tag == "C234":
                raise RuntimeError("controlled unexpected error")
            return original(tag, *args)
        with mock.patch.object(checker, "_invoke_component", side_effect=fail):
            report = self.call("unexpected-component-exception", "FAIL_CLOSED")
        self.assertEqual(report["error"]["code"], "COMPONENT_EXCEPTION")
        self.assertEqual(report["components"]["C222"]["result"], "PASS_CPU_CORRESPONDENCE")
        self.assertEqual(report["components"]["C234"]["state"], "ERROR")
        self.assertEqual(report["components"]["C235"]["state"], "NOT_RUN")

    def test_25_component_binding_mismatch(self):
        original = checker._invoke_component
        def fail(tag, *args):
            result = original(tag, *args)
            if tag == "C222":
                result["observation_sha256"] = "0"*64
            return result
        with mock.patch.object(checker, "_invoke_component", side_effect=fail):
            report = self.call("component-reported-binding-mismatch", "FAIL_CLOSED")
        self.assertEqual(report["error"]["code"], "COMPONENT_BINDING")
        self.assertEqual(report["components"]["C234"]["state"], "NOT_RUN")

    def test_26_fresh_authority_every_invocation(self):
        authority = self.private_authority()
        self.call("fresh-authority-before-mutation", "PASS_CPU_COMBINED", package_root=authority)
        target = authority / self.modules["C221"].INPUT_PATHS[0]
        raw = target.read_bytes()
        target.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
        report = self.call("fresh-authority-after-mutation", "FAIL_CLOSED", package_root=authority)
        self.assertEqual(report["admission"]["error"]["stage"], "authority")
        self.assertTrue(all(r["state"] == "NOT_RUN" for r in report["components"].values()))

    def test_27_inherited_source_and_cache_refusal(self):
        for kind in ("source", "cache", "self-after-load"):
            with self.subTest(kind=kind):
                source = self.root / kind
                names = [row[0] for row in checker.CHECKER_PINS.values()] + ["tools/second_target_c239/check_combined.py", checker.CONTRACT_PATH]
                names += [self.modules["C221"].AUTHORITY_DIRECTORY + "/" + name for name in self.modules["C221"].AUTHORITY_PINS]
                for name in names:
                    destination = source / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(REPO / name, destination)
                if kind == "source":
                    pin = source / checker.CHECKER_PINS["C235"][0]
                    pin.write_bytes(pin.read_bytes() + b"\n")
                elif kind == "cache":
                    (source / checker.CHECKER_PINS["C235"][0]).parent.joinpath("__pycache__").mkdir()
                program = "import importlib.util,json,pathlib,sys\np=pathlib.Path(sys.argv[1]);s=importlib.util.spec_from_file_location('isolated_c239',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
                if kind == "self-after-load":
                    program += "p.write_bytes(p.read_bytes()+b'\\n')\n"
                program += "print(json.dumps(m.check_combined(sys.argv[2],sys.argv[3]),sort_keys=True))\n"
                path = write_set(self.root / "input", copy.deepcopy(self.envelope), copy.deepcopy(self.values))
                run = subprocess.run([sys.executable, "-IB", "-c", program, str(source / "tools/second_target_c239/check_combined.py"), str(PACKAGE_ROOT), str(path)],
                                     capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stderr)
                report = json.loads(run.stdout)
                record("inherited-" + kind, report)
                self.assertEqual(report["result"], "FAIL_CLOSED")
                self.assertEqual(report["error"]["code"], {"source":"SOURCE_PIN", "cache":"SOURCE_CACHE", "self-after-load":"SOURCE_CHANGED"}[kind])

    def test_28_cli_pass_loss_refusal_arguments(self):
        for kind, code in (("pass", 0), ("loss", 1), ("refusal", 2), ("arguments", 2)):
            with self.subTest(kind=kind):
                self.e, self.v = copy.deepcopy(self.envelope), copy.deepcopy(self.values)
                if kind == "loss":
                    self.v["materials"]["parts"][0]["surfaces"][0]["raw"]["alpha"] = 0.9
                elif kind == "refusal":
                    self.e["authority"]["glb_sha256"] = "0"*64
                path = write_set(self.root / "input", self.e, self.v)
                args = [sys.executable, "-IB", str(REPO / "tools/second_target_c239/check_combined.py")]
                if kind != "arguments":
                    args += ["--package-root", str(PACKAGE_ROOT), "--envelope", str(path)]
                run = subprocess.run(args, capture_output=True, text=True, timeout=60)
                self.assertEqual(run.returncode, code, run.stderr)
                report = json.loads(run.stdout)
                record("cli-" + kind, report)
                self.assertEqual(run.stderr, "")
                self.assertEqual(report["result_class"], "pass" if kind == "pass" else "measured_loss" if kind == "loss" else "structural_refusal")

    def test_29_no_native_or_aggregate_imports(self):
        source = (REPO / "tools/second_target_c239/check_combined.py").read_text()
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        self.assertFalse({"subprocess", "ontokin", "bpy", "godot"} & set(imports))


def main(argv=None):
    global PACKAGE_ROOT, EVIDENCE, REPORT_STREAM
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--tests", nargs="*")
    args = parser.parse_args(argv)
    PACKAGE_ROOT, EVIDENCE = Path(args.package_root).absolute(), Path(args.evidence_dir).absolute()
    EVIDENCE.mkdir(parents=True, exist_ok=False)
    source_names = [row[0] for row in checker.CHECKER_PINS.values()] + ["tools/second_target_c239/check_combined.py", "tools/second_target_c239/tests/run_controls.py", checker.CONTRACT_PATH]
    before = {name: binding((REPO / name).read_bytes()) for name in source_names}
    pins, _ = checker._load_components()["C221"].load_authority()
    inputs_before = {row["packagePath"]: binding((PACKAGE_ROOT / row["packagePath"]).read_bytes()) for row in pins["items"]}
    started = time.monotonic()
    with lzma.open(EVIDENCE / "full-reports.jsonl.xz", "wb", preset=6) as stream:
        REPORT_STREAM = stream
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(["CombinedControls."+name for name in args.tests], sys.modules[__name__]) if args.tests else loader.loadTestsFromTestCase(CombinedControls)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    REPORT_STREAM = None
    summary = {"schema":"ontokin.c239.author-controls/0.1", "passed":result.wasSuccessful(), "methods":result.testsRun,
               "failures":len(result.failures), "errors":len(result.errors), "skips":len(result.skipped), "cases":len(CASES),
               "inspected_row_assertions":ASSERTIONS, "elapsed_seconds":time.monotonic()-started,
               "python":sys.version, "executable":sys.executable, "platform":platform.platform(),
               "source_commit":subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"],text=True).strip(),
               "source_tree":subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD^{tree}"],text=True).strip(),
               "source_files_before":before, "source_files_after":{name:binding((REPO/name).read_bytes()) for name in source_names},
               "original_inputs_before":inputs_before,
               "original_inputs_after":{row["packagePath"]:binding((PACKAGE_ROOT/row["packagePath"]).read_bytes()) for row in pins["items"]},
               "native_starts":0, "aggregate_runs":0, "case_results":CASES}
    summary["source_unchanged"] = summary["source_files_before"] == summary["source_files_after"]
    summary["original_inputs_unchanged"] = inputs_before == summary["original_inputs_after"]
    (EVIDENCE / "RESULT.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({k:summary[k] for k in ("passed","methods","failures","errors","skips","cases","inspected_row_assertions","elapsed_seconds","source_commit","source_unchanged","original_inputs_unchanged")}))
    return 0 if result.wasSuccessful() and summary["source_unchanged"] and summary["original_inputs_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
