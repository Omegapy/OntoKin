"""Focused tests of audit_numeric.py. The GLBs and references are the project's own synthetic fixtures
(tests/test_static_tray_reader_v01.synthetic and tools/static_tray_reader_v01's audit, loaded by path);
the probe reports are simulated here, from those references, the way the probe builds its rows: the
world positions by Three.js's Vector3.applyMatrix4 of the local positions, the bounds from them.
Children: the interpreter with -I -S -B."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

import mh_support as S

CASES = {"Q01-positive": "Q01", "Q03-positive": "Q03", "Q01-changed-reference": "Q01"}
NOISE = 1e-12
NEGATIVE_NODE = "equipment-tray/pair/left/base"
CHANGED_SCOPE = ("Intentionally changed synthetic reference for a negative importer comparison control; "
                 "not native evidence")


def threshold(field):
    if field.startswith("matrix_"):
        _, i, j = field.split("_")
        return 0.000005 if j == "3" and int(i) < 3 else 0.000001
    return 0.000001 if field.startswith("normal_") else 0.000005


def apply_matrix4(point, m):
    """Vector3.applyMatrix4 of Three.js r186 on the probe's row-major matrix rows M[i][j]."""
    x, y, z = (float(value) for value in point)
    w = 1 / (m[3][0] * x + m[3][1] * y + m[3][2] * z + m[3][3])
    return [(m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3]) * w,
            (m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3]) * w,
            (m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3]) * w]


def simulated_report(label, actual_reference, expected_reference, glb_sha, audit_sha, job):
    """What the probe writes, for an importer whose matrices equal the actual reference's plus a small noise."""
    measurements, findings, retained = [], [], {}

    def near(ident, field, actual, expected):
        limit = threshold(field)
        difference = abs(actual - expected)
        passed = difference <= limit
        measurements.append({"semantic_id": ident, "field": field, "actual": actual, "expected": expected,
                             "difference": difference, "threshold": limit, "passed": passed})
        if not passed:
            findings.append({"semantic_id": ident, "field": field, "actual": actual, "expected": expected,
                             "difference": difference, "threshold": limit})
    for ident in sorted(expected_reference["nodes"]):
        source, expected = actual_reference["nodes"][ident], expected_reference["nodes"][ident]
        matrix = [[float(value) + NOISE for value in row] for row in source["world_matrix"]]
        extras = expected["extras"]
        data = {"original_name": ident, "importer_name": ident.replace("/", ""), "extras": extras,
                "world_matrix": matrix, "children": sorted(expected["children"]),
                "parent": None if extras["role"] == "tray-root" else "/".join(extras["owner_id"])}
        for i in range(4):
            for j in range(4):
                near(ident, "matrix_%d_%d" % (i, j), matrix[i][j], expected["world_matrix"][i][j])
        if "world_vertices" not in expected:
            retained[ident] = data
            continue
        positions = [[float(value) for value in point] for point in source["positions"]]
        vertices = [apply_matrix4(point, matrix) for point in positions]
        normals = [[float(value) for value in normal] for normal in source["normals"]]
        for i in range(len(vertices)):
            for axis in range(3):
                near(ident, "world_vertex_%d_%d" % (i, axis), vertices[i][axis], expected["world_vertices"][i][axis])
                near(ident, "normal_%d_%d" % (i, axis), normals[i][axis], expected["normals"][i][axis])
        bounds = [[min(v[axis] for v in vertices) for axis in range(3)], [max(v[axis] for v in vertices) for axis in range(3)]]
        wanted = [[min(v[axis] for v in expected["world_vertices"]) for axis in range(3)],
                  [max(v[axis] for v in expected["world_vertices"]) for axis in range(3)]]
        for axis in range(3):
            near(ident, "world_min_%d" % axis, bounds[0][axis], wanted[0][axis])
            near(ident, "world_max_%d" % axis, bounds[1][axis], wanted[1][axis])
            near(ident, "world_size_%d" % axis, bounds[1][axis] - bounds[0][axis], wanted[1][axis] - wanted[0][axis])
        data.update(positions=positions, normals=normals, world_vertices=vertices,
                    indices=expected["indices"], material=expected["material"], world_bounds=bounds)
        retained[ident] = data
    passed = not findings
    return {"schema": "ontokin.current-host-readback-result/0.2.0", "contract": "ontokin.current-host-readback/0.2.0",
            "design_revision": 4, "amendments": ["P33-AMENDMENT-001"], "labels": {}, "passed": passed,
            "slot": "CPU-" + label, "case": CASES[label], "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
            "supplemental_manifest_sha256": job["supplemental_manifest_sha256"], "artifact_sha256": glb_sha,
            "audit_sha256": audit_sha, "node": "v24.22.1", "native_starts": 0, "exports": 0, "scope": "synthetic",
            "khronos": {"version": "2.0.0-dev.3.10", "passed": True,
                        "report": {"issues": {"numErrors": 0, "numWarnings": 0, "numInfos": 0, "numHints": 0,
                                              "truncated": False}}},
            "three": {"version": "0.186.1", "revision": "186", "passed": passed, "node_count": 14, "mesh_count": 12,
                      "animations": 0, "findings": findings, "measurements": measurements, "nodes": retained,
                      "position_tolerance_m": 0.000005, "matrix_tolerance": 0.000001, "naming": "synthetic"},
            "input_preserved": True}


def row_of(report, ident, field):
    return next(row for row in report["three"]["measurements"] if (row["semantic_id"], row["field"]) == (ident, field))


def first_mesh(report):
    return next(ident for ident, node in sorted(report["three"]["nodes"].items()) if "positions" in node)


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = S.project_root()
        fixture = S.load_module("mh_reader_fixture", root + "/tests/test_static_tray_reader_v01.py")
        cls.base = os.path.realpath(tempfile.mkdtemp(prefix="mh-audit-", dir=os.path.realpath(tempfile.gettempdir())))
        cls.cohort = cls.base + "/cohort"
        references = {}
        for label, case in CASES.items():
            stage = cls.cohort + "/" + label
            glb = fixture.synthetic(case)
            glb_path = S.write(stage + "/synthetic.glb", glb)
            reference = fixture.audit(Path(glb_path), case)
            assert reference["passed"], reference["findings"]
            references[label] = reference
            if label == "Q01-changed-reference":
                reference = copy.deepcopy(reference)
                reference["nodes"][NEGATIVE_NODE]["world_matrix"][0][3] += .001
                reference["scope"] = CHANGED_SCOPE
            audit_path = S.write(stage + "/synthetic-audit.json", S.canonical(reference))
            job = {"slot": "CPU-" + label, "case": case, "manifest": cls.cohort + "/supplemental-cpu.json",
                   "supplemental_manifest_sha256": "d" * 63 + "e", "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
                   "artifact": glb_path, "artifact_sha256": S.sha256_bytes(glb), "audit": audit_path,
                   "audit_sha256": S.sha256_file(audit_path), "result": stage + "/probe.json"}
            S.write(stage + "/job.json", S.canonical(job))
            report = simulated_report(label, references[label], reference, S.sha256_bytes(glb),
                                      S.sha256_file(audit_path), job)
            S.write(stage + "/probe.json", json.dumps(report).encode())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, True)

    def copy_cohort(self):
        target = S.resolved_temp(self) + "/cohort"
        shutil.copytree(self.cohort, target)
        return target

    def edit_report(self, cohort, label, change):
        path = cohort + "/" + label + "/probe.json"
        report = json.loads(Path(path).read_bytes())
        change(report)
        os.chmod(path, 0o644)
        Path(path).write_bytes(json.dumps(report).encode())

    def audit(self, cohort):
        output = os.path.dirname(cohort) + "/audit-%d.json" % len(os.listdir(os.path.dirname(cohort)))
        completed = S.run_tool("audit_numeric.py", "--cohort-root", cohort, "--output", output, flags=("-I", "-S", "-B"))
        return completed, S.read_json(output)

    def failed(self, record, label):
        return sorted(name for name, value in record["cases"][label]["checks"].items() if not value)

    def test_the_three_cases_pass_with_2060_rows_each_and_one_intended_negative_row(self):
        completed, record = self.audit(self.cohort)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-4000:])
        self.assertTrue(record["passed"])
        for label in CASES:
            self.assertEqual(self.failed(record, label), [], label)
            self.assertEqual(record["cases"][label]["counts"]["expected_rows"], 2060)
            self.assertEqual(record["cases"][label]["counts"]["reported_rows"], 2060)
            geometry = record["cases"][label]["geometry_recomputation"]
            self.assertEqual(len(geometry), 12)
            self.assertTrue(all(row["vertices_equal"] and row["bounds_equal"] for row in geometry.values()))
            self.assertEqual({row["max_absolute_deviation"] for row in geometry.values()}, {0.0})
        negative = record["cases"]["Q01-changed-reference"]
        self.assertEqual([(row["semantic_id"], row["field"]) for row in negative["failed_rows"]],
                         [(NEGATIVE_NODE, "matrix_0_3")])
        self.assertLess(abs(negative["negative_row"]["difference_minus_0_001"]), 1e-9)
        self.assertTrue(record["negative_fixture"]["passed"])
        self.assertEqual(record["loaded_project_files"], [])

    def test_duplicate_missing_and_altered_rows_are_found(self):
        def duplicate(report):
            report["three"]["measurements"].append(dict(report["three"]["measurements"][5]))

        def drop(report):
            del report["three"]["measurements"][7]

        def alter(report):
            report["three"]["measurements"][9]["difference"] += 1e-15

        def threshold_change(report):
            row = next(r for r in report["three"]["measurements"] if r["field"] == "matrix_1_3")
            row["threshold"] = 0.000001
        expectations = {duplicate: "rows_without_duplicates", drop: "rows_complete",
                        alter: "rows_match_recomputation", threshold_change: "rows_match_recomputation"}
        for change, check in expectations.items():
            with self.subTest(change.__name__):
                cohort = self.copy_cohort()
                self.edit_report(cohort, "Q03-positive", change)
                completed, record = self.audit(cohort)
                self.assertEqual(completed.returncode, 1)
                self.assertIn(check, self.failed(record, "Q03-positive"))
                self.assertEqual(self.failed(record, "Q01-positive"), [])

    def test_a_second_failed_row_in_the_negative_is_not_the_intended_negative(self):
        def second(report):
            # A node without vertices, so that its matrix moves no world position (the audit recomputes those).
            ident = next(ident for ident, node in sorted(report["three"]["nodes"].items()) if "positions" not in node)
            row = row_of(report, ident, "matrix_1_1")
            node = report["three"]["nodes"][ident]
            node["world_matrix"][1][1] += 1e-5
            row.update(actual=node["world_matrix"][1][1], difference=abs(node["world_matrix"][1][1] - row["expected"]),
                       passed=False)
            report["three"]["findings"].append({key: row[key] for key in ("semantic_id", "field", "actual", "expected",
                                                                           "difference", "threshold")})
        cohort = self.copy_cohort()
        self.edit_report(cohort, "Q01-changed-reference", second)
        completed, record = self.audit(cohort)
        self.assertEqual(completed.returncode, 1)
        failed = self.failed(record, "Q01-changed-reference")
        self.assertIn("negative_exactly_one_failed_row", failed)
        self.assertNotIn("rows_match_recomputation", failed)
        self.assertNotIn("findings_equal_recomputation", failed)

    def test_non_finite_values_and_spurious_findings_fail_the_positive(self):
        def null_position(report):
            ident = first_mesh(report)
            node = report["three"]["nodes"][ident]
            node["positions"][0][0] = None
            for axis in range(3):
                node["world_vertices"][0][axis] = None
                row = row_of(report, ident, "world_vertex_0_%d" % axis)
                row.update(actual=None, difference=None, passed=False)
                report["three"]["findings"].append({key: row[key] for key in (
                    "semantic_id", "field", "actual", "expected", "difference", "threshold")})
            report["three"]["passed"] = report["passed"] = False

        def spurious(report):
            report["three"]["findings"].append({"semantic_id": "", "field": "mesh_count", "actual": 12, "expected": 12})
        cases = {null_position: {"positive_every_row_passes", "positive_no_finding", "positive_report_passed"},
                 spurious: {"findings_equal_recomputation", "positive_no_finding"}}
        for change, expected in cases.items():
            with self.subTest(change.__name__):
                cohort = self.copy_cohort()
                self.edit_report(cohort, "Q01-positive", change)
                completed, record = self.audit(cohort)
                self.assertEqual(completed.returncode, 1)
                self.assertTrue(expected <= set(self.failed(record, "Q01-positive")), self.failed(record, "Q01-positive"))

    def test_the_negative_must_use_q01s_glb_and_an_otherwise_identical_reference(self):
        cohort = self.copy_cohort()
        path = cohort + "/Q01-changed-reference/synthetic-audit.json"
        reference = json.loads(Path(path).read_bytes())
        reference["nodes"]["equipment-tray/pair/right/base"]["extras"]["role"] = "changed"
        Path(path).write_bytes(S.canonical(reference))
        completed, record = self.audit(cohort)
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(record["negative_fixture"]["otherwise_identical_with_the_changed_scope"])
        self.assertIn("report_binds_reference", self.failed(record, "Q01-changed-reference"))

    def test_a_report_error_is_not_a_scientific_rejection(self):
        cohort = self.copy_cohort()
        self.edit_report(cohort, "Q01-changed-reference",
                         lambda report: report.update(error={"code": "OTRAY-E-DELIVERY", "message": "synthetic"}))
        completed, record = self.audit(cohort)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.failed(record, "Q01-changed-reference"), ["report_without_error"])

    def test_a_missing_stage_refuses(self):
        cohort = self.copy_cohort()
        shutil.rmtree(cohort + "/Q03-positive")
        completed, record = self.audit(cohort)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(record["state"], "REFUSED")

    # TR-15: the world positions from the retained positions and matrix, the bounds from those positions.
    def test_retained_vertices_that_are_not_the_matrix_applied_to_the_positions_fail(self):
        def moved(report):
            ident = first_mesh(report)
            node = report["three"]["nodes"][ident]
            node["world_vertices"][3][1] += 1e-7
            row = row_of(report, ident, "world_vertex_3_1")
            row.update(actual=node["world_vertices"][3][1], difference=abs(node["world_vertices"][3][1] - row["expected"]))
        cohort = self.copy_cohort()
        self.edit_report(cohort, "Q03-positive", moved)
        completed, record = self.audit(cohort)
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        failed = self.failed(record, "Q03-positive")
        self.assertIn("retained_world_vertices_equal_recomputation", failed)
        self.assertIn("rows_match_recomputation", failed)
        self.assertEqual(self.failed(record, "Q01-positive"), [])

    def test_retained_bounds_that_are_not_those_of_the_vertices_fail(self):
        def widened(report):
            ident = first_mesh(report)
            node = report["three"]["nodes"][ident]
            node["world_bounds"][1][0] += 1e-7
            for field, value in (("world_max_0", node["world_bounds"][1][0]),
                                 ("world_size_0", node["world_bounds"][1][0] - node["world_bounds"][0][0])):
                row = row_of(report, ident, field)
                row.update(actual=value, difference=abs(value - row["expected"]))
        cohort = self.copy_cohort()
        self.edit_report(cohort, "Q01-positive", widened)
        completed, record = self.audit(cohort)
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        failed = self.failed(record, "Q01-positive")
        self.assertIn("retained_world_bounds_equal_recomputation", failed)
        self.assertIn("rows_match_recomputation", failed)
        self.assertNotIn("retained_world_vertices_equal_recomputation", failed)

    def test_a_start_without_dash_b_refuses(self):
        """TR-17, in this process with sys.flags as a start without -B shows them; nothing is started."""
        tool = S.load_module("mh_audit_under_test", str(S.TOOLING / "audit_numeric.py"))
        output = S.resolved_temp(self) + "/audit-without-b.json"
        with mock.patch.object(sys, "flags", S.FlagsWithoutB()), contextlib.redirect_stderr(io.StringIO()):
            code = tool.main(["--cohort-root", self.cohort, "--output", output])
        self.assertEqual(code, 2)
        self.assertEqual(S.read_json(output)["refusal"]["rule"], "PYTHON")


if __name__ == "__main__":
    unittest.main()
