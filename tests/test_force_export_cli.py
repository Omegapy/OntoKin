"""Explicit force CLI export, exact source identity and complete file writes."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.cli import capabilities, main
from test_export import DecodedGLB


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'docs/language-design/force-v0.1'
CASES = {case['id']: case for case in json.loads((FIXTURES / 'acceptance.json').read_text())['source_cases']}
TARGET = 'ontokin.glb/0.5'
SOURCE = '''ontokin "0.5";
module ForceFile @ "force-file";
profile "force-0.1";
class Ball @ "ball-type" {
    geometry = sphere(0.5[m]);
    physical = sphere_body(0.5[m], 2[kg]);
    motion = dynamic;
    collision = disabled;
}
scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object ball @ "ball": Ball {}
    at 0[s] sequence {
        force ball @ "push" using vector(world, 4[N], 0[N], 0[N]) for 1[s];
    }
}
'''


class ForceExportCLITests(unittest.TestCase):
    def invoke(self, args):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main([str(arg) for arg in args])
        return code, json.loads(output.getvalue())

    def assertArtifact(self, path, report, program_revision=None):
        data = path.read_bytes()
        self.assertEqual(json.loads(path.with_suffix('.export.json').read_text()), report)
        self.assertEqual(report['artifact']['sha256'], 'sha256:' + hashlib.sha256(data).hexdigest())
        self.assertEqual(report['artifact']['byte_length'], len(data))
        self.assertEqual(report['target_contract'], TARGET)
        self.assertEqual(report['validation']['status'], 'passed')
        if program_revision is not None:
            self.assertEqual(report['program_revision'], program_revision)
        decoded = DecodedGLB(data)
        self.assertEqual(decoded.document['extras']['ontokin']['target_contract'], TARGET)
        self.assertEqual(decoded.document['extras']['ontokin']['program']['revision'], report['program_revision'])
        return decoded

    def test_pinned_force_manifest_exports_exact_sources_and_materials(self):
        manifest = FIXTURES / CASES['P01']['file_manifest']
        program = load_file_manifest(manifest)
        original = {unit.source_id: unit.raw for unit in program.units}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'force.glb'
            code, report = self.invoke(['export', manifest, '--bundle', '--target', TARGET,
                '--output', output, '--fps', '2', '--end', '2.5', '--no-helpers'])
            self.assertEqual(code, 0, report)
            decoded = self.assertArtifact(output, report, program.program_revision)
            self.assertEqual(report['program']['manifest'], program.manifest())
            self.assertEqual(report['sampling']['end_seconds'], '2.5')
            self.assertAlmostEqual(decoded.node_pose('ball', 1.5)['translation'][0], .25, delta=.001)
            self.assertTrue(decoded.document['materials'])
            self.assertFalse(list(Path(directory).glob('.ontokin-*.tmp')))
        self.assertEqual({unit.source_id: unit.raw for unit in load_file_manifest(manifest).units}, original)

    def test_single_file_force_source_keeps_original_utf8_and_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.ok'
            raw = ('// café: preserve exact input\n' + SOURCE).replace('\n', '\r\n').encode('utf-8')
            source.write_bytes(raw)
            output = Path(directory) / 'force.glb'
            code, report = self.invoke(['export', source, '--target', TARGET,
                '--output', output, '--fps', '2', '--no-helpers'])
            self.assertEqual(code, 0, report)
            decoded = self.assertArtifact(output, report)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(report['source_revision'], 'sha256:' + hashlib.sha256(raw).hexdigest())
            self.assertEqual(report['scene']['profile'], 'force-0.1')
            self.assertAlmostEqual(decoded.node_pose('ball', .5)['translation'][0], .25, delta=.001)

    def test_explicit_prefix_does_not_evaluate_later_invalid_force(self):
        manifest = FIXTURES / CASES['P21']['file_manifest']
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'prefix.glb'
            code, report = self.invoke(['export', manifest, '--bundle', '--target', TARGET,
                '--output', output, '--end', '1', '--fps', '2', '--no-helpers'])
            self.assertEqual(code, 0, report)
            decoded = self.assertArtifact(output, report, CASES['P21']['program_revision'])
            self.assertEqual(report['sampling']['end_seconds'], '1')
            self.assertEqual(max(decoded.animation_times()), 1)
            self.assertEqual(decoded.node_pose('ball', 1)['translation'], (1, 0, 0))
            previous = {path: path.read_bytes() for path in (output, output.with_suffix('.export.json'))}
            code, report = self.invoke(['export', manifest, '--bundle', '--target', TARGET,
                '--output', output, '--fps', '2', '--no-helpers'])
            self.assertNotEqual(code, 0)
            self.assertEqual(report['diagnostics'][0]['code'], 'OKL-E-NUMERIC')
            for path, content in previous.items():
                self.assertEqual(path.read_bytes(), content)

    def test_older_target_rejection_preserves_existing_output_pair(self):
        manifest = FIXTURES / CASES['P01']['file_manifest']
        for target in ('ontokin.glb/0.2', 'ontokin.glb/0.3', 'ontokin.glb/0.4'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'old.glb'
                sidecar = output.with_suffix('.export.json')
                output.write_bytes(b'previous complete GLB')
                sidecar.write_bytes(b'previous complete report')
                code, report = self.invoke(['export', manifest, '--bundle', '--target', target,
                    '--output', output])
                self.assertNotEqual(code, 0)
                self.assertEqual(report['diagnostics'][0]['details']['target_contract'], target)
                self.assertEqual(output.read_bytes(), b'previous complete GLB')
                self.assertEqual(sidecar.read_bytes(), b'previous complete report')

    def test_invalid_end_and_tolerance_write_no_artifact(self):
        manifest = FIXTURES / CASES['P01']['file_manifest']
        for arguments in (('--end', '4'), ('--end=-1',), ('--position-tolerance', '-1')):
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'failed.glb'
                code, _ = self.invoke(['export', manifest, '--bundle', '--target', TARGET,
                    '--output', output, *arguments])
                self.assertNotEqual(code, 0)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix('.export.json').exists())
                self.assertFalse(list(Path(directory).glob('.ontokin-*.tmp')))

    def test_force_export_staging_failure_preserves_previous_complete_pair(self):
        manifest = FIXTURES / CASES['P01']['file_manifest']
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'old.glb'
            sidecar = output.with_suffix('.export.json')
            output.write_bytes(b'previous complete GLB')
            sidecar.write_bytes(b'previous complete report')
            with patch('ontokin.cli.os.fsync', side_effect=OSError('simulated staging failure')):
                code, report = self.invoke(['export', manifest, '--bundle', '--target', TARGET,
                    '--output', output, '--end', '1.5', '--fps', '2', '--no-helpers'])
            self.assertEqual(code, 1)
            self.assertEqual(report['outcome'], 'io_error')
            self.assertEqual(output.read_bytes(), b'previous complete GLB')
            self.assertEqual(sidecar.read_bytes(), b'previous complete report')
            self.assertFalse(list(Path(directory).glob('.ontokin-*.tmp')))

    def test_force_capabilities_are_explicit_and_keep_prior_defaults(self):
        result = capabilities()
        self.assertEqual((result['language_version'], result['profile']), ('0.1', 'core-0.1'))
        self.assertEqual(result['agent_interface']['schema_version'], 'ontokin.agent/0.1')
        self.assertEqual(result['construction_interface']['schema_version'], 'ontokin.agent/0.2')
        self.assertEqual(result['surface_interface']['agent_contract'], 'ontokin.agent/0.3')
        self.assertEqual(result['impulse_interface']['agent_contract'], 'ontokin.agent/0.4')
        self.assertEqual(result['force_interface']['agent_contract'], 'ontokin.agent/0.5')
        self.assertEqual(result['force_interface']['delivery_contract'], TARGET)
        self.assertEqual(result['export_targets'][TARGET]['profile'], 'force-0.1')
        self.assertEqual(result['runtime_dependencies'], [])


if __name__ == '__main__':
    unittest.main()
