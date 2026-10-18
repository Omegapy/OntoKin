"""Exercise export files, provenance, path aliases, and write failures."""

from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ontokin.cli import main
from ontokin.fixtures import DEFAULT_FIXTURES
from test_export import DecodedGLB


class ExportCLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep the original source fixture untouched. A short observation
        # horizon still exercises the assembly, joints, and independent motion.
        cls.source_text = (DEFAULT_FIXTURES / "01-independent-parts.ok").read_text().replace(
            "duration = 3[s];", "duration = 0.25[s];")

    def invoke(self, args):
        output = io.StringIO()
        with redirect_stdout(output):
            status = main([str(arg) for arg in args])
        return status, json.loads(output.getvalue())

    def source_file(self, directory, text=None):
        path = Path(directory) / "scene.ok"
        path.write_text(self.source_text if text is None else text, encoding="utf-8")
        return path

    def assertUnchanged(self, expected):
        for path, content in expected.items():
            self.assertEqual(path.read_bytes(), content, str(path))

    def test_export_writes_complete_glb_hash_bound_sidecar_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.source_file(directory)
            original = source.read_bytes()
            output = Path(directory) / "nested" / "animation.glb"
            report_path = output.with_suffix(".export.json")
            status, result = self.invoke(["export", source, "--output", output])
            self.assertEqual(status, 0)
            data = output.read_bytes()
            self.assertEqual(result, json.loads(report_path.read_text()))
            self.assertEqual(result["artifact"]["sha256"], "sha256:" + hashlib.sha256(data).hexdigest())
            self.assertEqual(result["artifact"]["byte_length"], len(data))
            self.assertEqual(result["source_revision"], "sha256:" + hashlib.sha256(original).hexdigest())
            self.assertEqual(result["source"]["revision"], result["source_revision"])
            self.assertEqual(result["validation"]["status"], "passed")
            self.assertEqual(result["target_contract"], "ontokin.glb/0.1")
            glb = DecodedGLB(data)
            self.assertTrue(glb.document["animations"][0]["channels"])
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse(list(output.parent.glob(".ontokin-*.tmp")))

    def test_custom_report_short_interval_and_no_helpers_are_effective(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.source_file(directory)
            output = Path(directory) / "animation.glb"
            report_path = Path(directory) / "evidence" / "animation.json"
            status, result = self.invoke(["export", source, "--output", output, "--report", report_path,
                                          "--end", "0.125", "--fps", "32", "--no-helpers"])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(report_path.read_text()), result)
            self.assertFalse(output.with_suffix(".export.json").exists())
            self.assertEqual(result["sampling"]["end_seconds"], "0.125")
            self.assertEqual(result["sampling"]["requested_fps"], 32)
            self.assertTrue(result["retention"]["outside_interval_omitted"])
            self.assertEqual(result["geometry"]["helper_nodes"], 0)
            glb = DecodedGLB(output.read_bytes())
            self.assertTrue(all(node["extras"]["ontokin"]["kind"] == "object"
                                for node in glb.document["nodes"]))
            self.assertEqual(max(glb.animation_times()), 0.125)

    def test_symlink_and_hardlink_aliases_cannot_overwrite_source_or_pair(self):
        for link_kind in ("symlink", "hardlink"):
            for target in ("output_to_source", "report_to_source", "report_to_output"):
                with self.subTest(link_kind=link_kind, target=target), tempfile.TemporaryDirectory() as directory:
                    source = self.source_file(directory)
                    output = Path(directory) / "animation.glb"
                    report_path = Path(directory) / "animation.json"
                    expected = {source: source.read_bytes()}
                    if target == "output_to_source":
                        alias, original = output, source
                    elif target == "report_to_source":
                        alias, original = report_path, source
                    else:
                        output.write_bytes(b"previous complete output")
                        expected[output] = output.read_bytes()
                        alias, original = report_path, output
                    if link_kind == "symlink":
                        alias.symlink_to(original)
                    else:
                        os.link(original, alias)
                    expected[alias] = original.read_bytes()
                    status, result = self.invoke(["export", source, "--output", output, "--report", report_path])
                    self.assertEqual(status, 3)
                    self.assertEqual(result["diagnostics"][0]["details"]["export_code"], "OKE-E-OUTPUT-PATH")
                    self.assertUnchanged(expected)
                    for path in (output, report_path):
                        if path not in expected:
                            self.assertFalse(path.exists())

    def test_bad_paths_and_numeric_options_write_nothing_or_preserve_existing_pair(self):
        cases = (
            ("wrong_output_suffix", (), ".gltf", ".json", 3),
            ("wrong_report_suffix", (), ".glb", ".txt", 3),
            ("fps_zero", ("--fps", "0"), ".glb", ".json", 2),
            ("fps_nonfinite", ("--fps", "nan"), ".glb", ".json", 2),
            ("end_outside_horizon", ("--end", "0.5"), ".glb", ".json", 2),
            ("end_negative", ("--end=-1",), ".glb", ".json", 2),
            ("position_tolerance", ("--position-tolerance", "-1"), ".glb", ".json", 2),
            ("rotation_tolerance", ("--rotation-tolerance", "nan"), ".glb", ".json", 2),
            ("time_tolerance", ("--time-tolerance", "0"), ".glb", ".json", 2),
        )
        for name, args, output_suffix, report_suffix, expected_status in cases:
            for existing in (False, True):
                with self.subTest(case=name, existing=existing), tempfile.TemporaryDirectory() as directory:
                    source = self.source_file(directory)
                    output = Path(directory) / ("animation" + output_suffix)
                    report_path = Path(directory) / ("evidence" + report_suffix)
                    expected = {source: source.read_bytes()}
                    if existing:
                        output.write_bytes(b"previous complete glb")
                        report_path.write_bytes(b"previous complete report")
                        expected.update({output: output.read_bytes(), report_path: report_path.read_bytes()})
                    status, result = self.invoke(["export", source, "--output", output,
                                                  "--report", report_path, *args])
                    self.assertEqual(status, expected_status)
                    self.assertEqual(result["requested_level"], "delivered")
                    self.assertUnchanged(expected)
                    if not existing:
                        self.assertFalse(output.exists())
                        self.assertFalse(report_path.exists())
                    self.assertFalse(list(Path(directory).glob(".ontokin-*.tmp")))

    def test_invalid_source_is_primary_and_cannot_replace_existing_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.source_file(directory, self.source_text.replace("Length = 0.2[m];", "Length = 1[kg];"))
            output = Path(directory) / "animation.gltf"
            report_path = Path(directory) / "animation.json"
            output.write_bytes(b"previous complete glb")
            report_path.write_bytes(b"previous complete report")
            expected = {p: p.read_bytes() for p in (source, output, report_path)}
            status, result = self.invoke(["export", source, "--output", output, "--report", report_path])
            self.assertEqual(status, 2)
            self.assertEqual(result["diagnostics"][0]["code"], "OKL-E-UNIT")
            self.assertUnchanged(expected)

    def test_staging_failure_preserves_both_destinations_and_cleans_temporary_files(self):
        for failing_stage in (0, 1):
            with self.subTest(stage=failing_stage), tempfile.TemporaryDirectory() as directory:
                source = self.source_file(directory)
                output = Path(directory) / "animation.glb"
                report_path = Path(directory) / "animation.json"
                output.write_bytes(b"previous complete glb")
                report_path.write_bytes(b"previous complete report")
                expected = {p: p.read_bytes() for p in (source, output, report_path)}
                failures = [None] * failing_stage + [OSError("simulated storage failure")]
                with patch("ontokin.cli.os.fsync", side_effect=failures):
                    status, result = self.invoke(["export", source, "--output", output, "--report", report_path])
                self.assertEqual(status, 1)
                self.assertEqual(result["outcome"], "io_error")
                self.assertUnchanged(expected)
                self.assertFalse(list(Path(directory).glob(".ontokin-*.tmp")))

    def test_replacement_failure_reports_error_and_never_leaves_partial_glb_bytes(self):
        for failing_replacement in (0, 1):
            with self.subTest(replacement=failing_replacement), tempfile.TemporaryDirectory() as directory:
                source = self.source_file(directory)
                output = Path(directory) / "animation.glb"
                report_path = Path(directory) / "animation.json"
                output.write_bytes(b"previous complete glb")
                report_path.write_bytes(b"previous complete report")
                expected = {p: p.read_bytes() for p in (source, output, report_path)}
                replace = os.replace
                calls = 0

                def fail_one_replace(temporary, destination):
                    nonlocal calls
                    index = calls
                    calls += 1
                    if index == failing_replacement:
                        raise OSError("simulated rename failure")
                    return replace(temporary, destination)

                with patch("ontokin.cli.os.replace", side_effect=fail_one_replace):
                    status, result = self.invoke(["export", source, "--output", output, "--report", report_path])
                self.assertEqual(status, 1)
                self.assertEqual(result["outcome"], "io_error")
                self.assertEqual(source.read_bytes(), expected[source])
                self.assertEqual(report_path.read_bytes(), expected[report_path])
                if failing_replacement == 0:
                    self.assertEqual(output.read_bytes(), expected[output])
                else:
                    # Two destination paths cannot be replaced in one atomic
                    # operation. A new GLB may remain, but it must be complete;
                    # the old sidecar cannot match the new artifact's hash.
                    glb = DecodedGLB(output.read_bytes())
                    self.assertEqual(glb.document["asset"]["version"], "2.0")
                self.assertFalse(list(Path(directory).glob(".ontokin-*.tmp")))


if __name__ == "__main__":
    unittest.main()
