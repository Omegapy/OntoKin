"""Native GLB CLI delivery protects source files and identifies exact bytes."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.cli import main
from tests.test_construction import RELEASE_SOURCE
from tests.test_export import DecodedGLB
from tests.test_surface_export import CONTRACT, single_source
from tests.test_surface_source import ROOT, bundle as studio_bundle


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_studio(directory):
    """Keep source identity filenames stable while varying transport paths."""
    root = Path(directory)
    entry, library = root / "src" / "studio.ok", root / "lib" / "surfaces.ok"
    entry.parent.mkdir()
    library.parent.mkdir()
    entry.write_bytes((ROOT / "02-studio.ok").read_bytes())
    library.write_bytes((ROOT / "01-surface-parts.ok").read_bytes())
    manifest = root / "program.files.json"
    manifest.write_text(json.dumps({
        "schema_version": "ontokin.files/0.1",
        "entry": {"filename": "02-studio.ok", "path": "src/studio.ok"},
        "modules": [{"package_id": "fixture.surface-parts", "version": "1.0.0",
                     "filename": "01-surface-parts.ok", "path": "lib/surfaces.ok"}],
    }), encoding="utf-8")
    return manifest, entry, library


class NativeSurfaceExportCLITests(unittest.TestCase):
    def invoke(self, args):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = main([str(arg) for arg in args])
        return status, json.loads(stdout.getvalue())

    def native_file(self, directory, text=None):
        path = Path(directory) / "source.ok"
        path.write_text(single_source(duration=.25) if text is None else text, encoding="utf-8")
        return path

    def assertUnchanged(self, expected):
        for path, content in expected.items():
            self.assertEqual(path.read_bytes(), content, str(path))

    def assertNoStaging(self, root):
        self.assertFalse(list(Path(root).rglob(".ontokin-*.tmp")))

    def assertArtifact(self, result, output, report, expected_revision=None):
        self.assertEqual(result, json.loads(report.read_text("utf-8")))
        data = output.read_bytes()
        self.assertEqual(result["artifact"]["sha256"], digest(data))
        self.assertEqual(result["artifact"]["byte_length"], len(data))
        self.assertEqual(result["target_contract"], CONTRACT)
        self.assertEqual(result["validation"]["status"], "passed")
        self.assertEqual(result["outcome"], "valid")
        if expected_revision is not None:
            self.assertEqual(result["program_revision"], expected_revision)
        decoded = DecodedGLB(data)
        metadata = decoded.document["extras"]["ontokin"]
        self.assertEqual(metadata["target_contract"], CONTRACT)
        self.assertEqual(metadata["program"]["revision"], result["program_revision"])
        self.assertEqual(metadata["source"]["entry_revision"], result["source_revision"])
        return decoded

    def test_single_source_export_preserves_exact_utf8_and_writes_bound_sidecar(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.ok"
            raw = ("// café: unchanged source bytes\n" + single_source(duration=.25)).replace("\n", "\r\n").encode("utf-8")
            source.write_bytes(raw)
            output = Path(directory) / "result" / "native.glb"
            status, result = self.invoke(["export", source, "--target", CONTRACT,
                                          "--output", output, "--no-helpers"])
            self.assertEqual(status, 0)
            decoded = self.assertArtifact(result, output, output.with_suffix(".export.json"))
            self.assertEqual(result["source_revision"], digest(raw))
            self.assertEqual(result["program"]["sources"]["entry"]["source_revision"], digest(raw))
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(len(decoded.document["meshes"]), 1)
            self.assertEqual(decoded.document["nodes"][0]["extras"]["ontokin"]["surface"]["triangle_count"], 64)
            self.assertNoStaging(directory)

    def test_pinned_manifest_export_identifies_the_complete_frozen_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, entry, library = write_studio(directory)
            original = {path: path.read_bytes() for path in (manifest, entry, library)}
            output = Path(directory) / "animation.glb"
            report = Path(directory) / "evidence" / "native.json"
            status, result = self.invoke(["export", manifest, "--bundle", "--target", CONTRACT,
                "--output", output, "--report", report, "--end", "1.25", "--fps", "16", "--no-helpers"])
            self.assertEqual(status, 0)
            sealed = studio_bundle()
            decoded = self.assertArtifact(result, output, report, sealed.program_revision)
            self.assertEqual(result["program"]["manifest"], sealed.manifest())
            self.assertEqual(result["source_revision"], digest(original[entry]))
            self.assertNotEqual(result["program_revision"], result["source_revision"])
            self.assertEqual(result["program"]["sources"]["package:fixture.surface-parts@1.0.0"]["source_revision"],
                             digest(original[library]))
            self.assertEqual(result["sampling"]["requested_fps"], 16)
            self.assertEqual(result["sampling"]["end_seconds"], "1.25")
            self.assertTrue(result["retention"]["outside_interval_omitted"])
            self.assertEqual(result["geometry"]["helper_nodes"], 0)
            self.assertEqual(decoded.node_pose("first", 1.25)["translation"], (-2, .625, 0))
            self.assertFalse(output.with_suffix(".export.json").exists())
            self.assertUnchanged(original)
            self.assertNoStaging(directory)

    def test_explicit_construction_target_remains_available(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.native_file(directory, RELEASE_SOURCE)
            original = source.read_bytes()
            output = Path(directory) / "construction.glb"
            status, result = self.invoke(["export", source, "--target", "ontokin.glb/0.2",
                "--output", output, "--end", "0.125", "--no-helpers"])
            self.assertEqual(status, 0)
            self.assertEqual(result["target_contract"], "ontokin.glb/0.2")
            self.assertEqual(result["scene"]["profile"], "construction-0.1")
            self.assertEqual(result["artifact"]["sha256"], digest(output.read_bytes()))
            self.assertEqual(result["source_revision"], digest(original))
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(len(DecodedGLB(output.read_bytes()).document["nodes"]), 3)

    def test_default_target_does_not_migrate_native_source_or_accept_bundles(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.native_file(directory)
            original = source.read_bytes()
            output = Path(directory) / "native.glb"
            status, result = self.invoke(["export", source, "--output", output])
            self.assertNotEqual(status, 0)
            self.assertEqual(result["requested_level"], "delivered")
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".export.json").exists())
        for explicit in (False, True):
            with self.subTest(explicit=explicit), tempfile.TemporaryDirectory() as directory:
                manifest, entry, library = write_studio(directory)
                originals = {path: path.read_bytes() for path in (manifest, entry, library)}
                output = Path(directory) / "native.glb"
                args = ["export", manifest, "--bundle", "--output", output]
                if explicit:
                    args += ["--target", "ontokin.glb/0.1"]
                status, result = self.invoke(args)
                self.assertEqual(status, 2)
                self.assertEqual(result["outcome"], "invalid_request")
                self.assertEqual(result["target_contract"], "ontokin.glb/0.1")
                self.assertEqual(result["error"]["code"], "OKA-E-REQUEST")
                self.assertUnchanged(originals)
                self.assertFalse(output.exists())
                self.assertNoStaging(directory)

    def test_manifest_flag_is_explicit_and_does_not_guess_input_type(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, entry, library = write_studio(directory)
            originals = {path: path.read_bytes() for path in (manifest, entry, library)}
            output = Path(directory) / "native.glb"
            status, result = self.invoke(["export", manifest, "--target", CONTRACT, "--output", output])
            self.assertNotEqual(status, 0)
            self.assertEqual(result["requested_level"], "delivered")
            self.assertUnchanged(originals)
            self.assertFalse(output.exists())
            self.assertNoStaging(directory)

    def test_destinations_cannot_alias_manifest_entry_dependency_or_each_other(self):
        targets = ("manifest", "entry", "dependency", "output")
        for kind in ("symlink", "hardlink"):
            for target in targets:
                for destination in ("output", "report"):
                    if target == destination:
                        continue
                    with self.subTest(kind=kind, target=target, destination=destination), tempfile.TemporaryDirectory() as directory:
                        manifest, entry, library = write_studio(directory)
                        output, report = Path(directory) / "native.glb", Path(directory) / "native.json"
                        paths = {"manifest": manifest, "entry": entry, "dependency": library,
                                 "output": output, "report": report}
                        expected = {path: path.read_bytes() for path in (manifest, entry, library)}
                        original, alias = paths[target], paths[destination]
                        if target == "output":
                            original.write_bytes(b"previous complete artifact")
                            expected[original] = original.read_bytes()
                        if kind == "symlink":
                            alias.symlink_to(original)
                        else:
                            os.link(original, alias)
                        expected[alias] = original.read_bytes()
                        status, result = self.invoke(["export", manifest, "--bundle", "--target", CONTRACT,
                                                      "--output", output, "--report", report])
                        self.assertEqual(status, 3)
                        diagnostic = result["diagnostics"][0]
                        self.assertEqual(diagnostic["category"], "unsupported")
                        self.assertEqual(diagnostic["details"]["target_contract"], CONTRACT)
                        self.assertEqual(diagnostic["details"]["export_code"], "OKE-E-OUTPUT-PATH")
                        self.assertUnchanged(expected)
                        for path in (output, report):
                            if path not in expected:
                                self.assertFalse(path.exists())
                        self.assertNoStaging(directory)

    def test_report_cannot_replace_its_source_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, entry, library = write_studio(directory)
            originals = {path: path.read_bytes() for path in (manifest, entry, library)}
            output = Path(directory) / "native.glb"
            status, result = self.invoke(["export", manifest, "--bundle", "--target", CONTRACT,
                                          "--output", output, "--report", manifest])
            self.assertEqual(status, 3)
            self.assertEqual(result["diagnostics"][0]["details"]["export_code"], "OKE-E-OUTPUT-PATH")
            self.assertUnchanged(originals)
            self.assertFalse(output.exists())

    def test_output_suffix_and_numeric_errors_preserve_existing_pair_and_target(self):
        cases = ((".gltf", ".json", (), 3, "unsupported"),
                 (".glb", ".txt", (), 3, "unsupported"),
                 (".glb", ".json", ("--fps", "0"), 2, "invalid"),
                 (".glb", ".json", ("--position-tolerance", "nan"), 2, "invalid"),
                 (".glb", ".json", ("--end", "3"), 2, "invalid"))
        for suffix, report_suffix, options, expected_status, category in cases:
            for existing in (False, True):
                with self.subTest(suffix=suffix, options=options, existing=existing), tempfile.TemporaryDirectory() as directory:
                    source = self.native_file(directory)
                    output = Path(directory) / ("native" + suffix)
                    report = Path(directory) / ("evidence" + report_suffix)
                    originals = {source: source.read_bytes()}
                    if existing:
                        output.write_bytes(b"previous complete artifact")
                        report.write_bytes(b"previous complete report")
                        originals.update({output: output.read_bytes(), report: report.read_bytes()})
                    status, result = self.invoke(["export", source, "--target", CONTRACT,
                                                  "--output", output, "--report", report, *options])
                    self.assertEqual(status, expected_status)
                    diagnostic = result["diagnostics"][0]
                    self.assertEqual(result["requested_level"], "delivered")
                    self.assertEqual(diagnostic["category"], category)
                    self.assertEqual(diagnostic["details"]["target_contract"], CONTRACT)
                    self.assertUnchanged(originals)
                    if not existing:
                        self.assertFalse(output.exists())
                        self.assertFalse(report.exists())
                    self.assertNoStaging(directory)

    def test_invalid_pin_and_native_source_fail_before_replacing_destinations(self):
        for invalid in ("pin", "surface"):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                manifest, entry, library = write_studio(directory)
                if invalid == "pin":
                    library.write_bytes(library.read_bytes() + b"\n// A changed dependency must be repinned.\n")
                else:
                    old_hash = digest(library.read_bytes())
                    library.write_bytes(library.read_bytes().replace(b"0.5[m], 0.35[m]", b"0[m], 0.35[m]"))
                    entry.write_bytes(entry.read_bytes().replace(old_hash.encode(), digest(library.read_bytes()).encode()))
                output, report = Path(directory) / "native.gltf", Path(directory) / "native.json"
                output.write_bytes(b"previous complete artifact")
                report.write_bytes(b"previous complete report")
                originals = {path: path.read_bytes() for path in (manifest, entry, library, output, report)}
                status, result = self.invoke(["export", manifest, "--bundle", "--target", CONTRACT,
                                              "--output", output, "--report", report])
                self.assertEqual(status, 2)
                diagnostic = result["diagnostics"][0]
                self.assertEqual(diagnostic["code"], "OKL-E-REVISION" if invalid == "pin" else "OKL-E-SURFACE-RADIUS")
                self.assertEqual(diagnostic["details"]["target_contract"], CONTRACT)
                self.assertEqual(diagnostic["program_revision"], load_file_manifest(manifest).program_revision)
                self.assertUnchanged(originals)
                self.assertNoStaging(directory)

    def test_invalid_transport_is_reported_without_any_artifact_write(self):
        for invalid in ("bad_json", "unknown_schema", "missing_module", "escape", "invalid_utf8"):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                manifest, entry, library = write_studio(directory)
                if invalid == "bad_json":
                    manifest.write_bytes(b"{")
                elif invalid == "unknown_schema":
                    manifest.write_text(manifest.read_text().replace("ontokin.files/0.1", "ontokin.files/0.9"))
                elif invalid == "missing_module":
                    library.unlink()
                elif invalid == "escape":
                    manifest.write_text(manifest.read_text().replace("lib/surfaces.ok", "../outside.ok"))
                else:
                    library.write_bytes(b"\xff invalid UTF-8")
                originals = {path: path.read_bytes() for path in (manifest, entry, library) if path.exists()}
                output = Path(directory) / "native.glb"
                status, result = self.invoke(["export", manifest, "--bundle", "--target", CONTRACT, "--output", output])
                self.assertEqual(status, 2)
                self.assertEqual(result["outcome"], "invalid_request")
                self.assertEqual(result["target_contract"], CONTRACT)
                self.assertEqual(result["error"]["code"], "OKA-E-REQUEST")
                self.assertUnchanged(originals)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix(".export.json").exists())
                self.assertNoStaging(directory)

    def test_manifest_change_during_snapshot_load_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, entry, library = write_studio(directory)
            originals = {path: path.read_bytes() for path in (entry, library)}
            output = Path(directory) / "native.glb"
            def change_manifest(path):
                program = load_file_manifest(path)
                manifest.write_bytes(manifest.read_bytes() + b"\n ")
                return program
            with patch("ontokin.bundle.load_file_manifest", side_effect=change_manifest):
                status, result = self.invoke(["export", manifest, "--bundle", "--target", CONTRACT, "--output", output])
            self.assertEqual(status, 2)
            self.assertEqual(result["outcome"], "invalid_request")
            self.assertEqual(result["error"]["code"], "OKA-E-REQUEST")
            self.assertIn("changed", result["error"]["message"])
            self.assertUnchanged(originals)
            self.assertFalse(output.exists())
            self.assertNoStaging(directory)

    def test_native_staging_failure_preserves_sources_and_previous_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, entry, library = write_studio(directory)
            output, report = Path(directory) / "native.glb", Path(directory) / "native.json"
            output.write_bytes(b"previous complete artifact")
            report.write_bytes(b"previous complete report")
            originals = {path: path.read_bytes() for path in (manifest, entry, library, output, report)}
            with patch("ontokin.cli.os.fsync", side_effect=[None, OSError("test storage failure")]):
                status, result = self.invoke(["export", manifest, "--bundle", "--target", CONTRACT,
                                              "--output", output, "--report", report])
            self.assertEqual(status, 1)
            self.assertEqual(result["outcome"], "io_error")
            self.assertUnchanged(originals)
            self.assertNoStaging(directory)

    def test_capabilities_identify_versioned_surface_delivery_and_agent_contracts(self):
        status, result = self.invoke(["capabilities"])
        self.assertEqual(status, 0)
        self.assertEqual(result["language_version"], "0.1")
        self.assertEqual(result["profile"], "core-0.1")
        self.assertEqual(set(result["export_targets"]), {"ontokin.glb/0.1", "ontokin.glb/0.2", CONTRACT, "ontokin.glb/0.4"})
        surface = result["surface_interface"]
        self.assertEqual(surface["language_version"], "0.3")
        self.assertEqual(surface["profile"], "surface-0.1")
        self.assertEqual(surface["delivery_contract"], CONTRACT)
        self.assertIn("--bundle", surface["pinned_bundle_command"])
        self.assertEqual(surface["agent_contract"], "ontokin.agent/0.3")
        self.assertIn("surface.mesh_page", surface["operations"])
        self.assertEqual(result["export_targets"][CONTRACT]["surface_vertex_tolerance_m"], 1e-5)


if __name__ == "__main__":
    unittest.main()
