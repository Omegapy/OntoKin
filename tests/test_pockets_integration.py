"""Shared .12 selectors, inherited meanings and actual binary32 admission."""
import hashlib
from pathlib import Path
import unittest

from ontokin.budget_runtime import (execute_pockets_export, execute_framed_loft_export,
                                    execute_extrusion_export)
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.gltf import read_glb
from ontokin.profile_capabilities import POCKETS_PROFILE
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions, POCKETS_TARGET
from tests import test_ring_loft_integration as inherited_reader
from tests.test_export import DecodedGLB


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'examples/polygon-pockets'
OPTIONS = ExportOptions(fps=2, end='1', helpers=False)


def bundle(raw, *, modules=()):
    return ProgramBundle(SourceUnit('entry', 'shape.ok', raw), modules)


class PocketsIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = bundle((FIXTURES / 'rectangular-pocket.ok').read_bytes())
        cls.exported = execute_pockets_export(cls.program, options=OPTIONS)
        if cls.exported.data is None:
            raise AssertionError(cls.exported.report)

    def read(self, data):
        ledger = SharedExecutionBudget()
        admit_entry_budget(self.program.entry, ledger, profile=POCKETS_PROFILE)
        return read_glb(data, target_contract=POCKETS_TARGET,
                        work=ReachExecutionWork(execution_budget=ledger))

    def changed_triangle(self, points, normal):
        return inherited_reader.RingLoftIntegrationTests.changed_triangle(self, points, normal)

    def test_actual_reader_preserves_exact_thin_face_orientation(self):
        points = ((2.**-80, 0., 0.), (1., 3., 0.), (15., 45., 0.))
        self.read(self.changed_triangle(points, (0., 0., -1.)))

    def test_actual_reader_refuses_rounded_cross_sign_substitution(self):
        points = ((2.**-80, 0., 0.), (1., 3., 0.), (15., 45., 0.))
        with self.assertRaisesRegex(OntoKinError, 'outward'):
            self.read(self.changed_triangle(points, (0., 0., 1.)))

    def test_actual_reader_refuses_collinear_delivered_face(self):
        points = ((0., 0., 0.), (1., 3., 0.), (15., 45., 0.))
        with self.assertRaisesRegex(OntoKinError, 'degenerate'):
            self.read(self.changed_triangle(points, (0., 0., 1.)))

    def test_explicit_target_and_current_admission_are_required(self):
        for kwargs in ({}, {'target_contract': POCKETS_TARGET}):
            with self.subTest(kwargs=kwargs), self.assertRaises(OntoKinError):
                read_glb(self.exported.data, **kwargs)
        meta = self.read(self.exported.data).document['extras']['ontokin']
        self.assertEqual(meta['profile'], POCKETS_PROFILE)
        self.assertEqual(meta['schema_version'], '0.12')
        self.assertEqual(meta['polygon_pockets_profile']['minimum_remaining_base_m'], .001)

    def test_zero_pocket_geometry_and_motion_binary_streams_equal_unchanged_008(self):
        for name in ('zero-pockets', 'zero-pockets-concave'):
            with self.subTest(name=name):
                new = execute_pockets_export(bundle((FIXTURES / (name + '.ok')).read_bytes()), options=OPTIONS)
                old = execute_extrusion_export(bundle((FIXTURES / (name + '-legacy.ok')).read_bytes()), options=OPTIONS)
                self.assertIsNotNone(new.data, new.report)
                self.assertIsNotNone(old.data, old.report)
                self.assertEqual(DecodedGLB(new.data).binary, DecodedGLB(old.data).binary)

    def test_inherited_families_keep_original_summary_and_geometry_meaning(self):
        for folder, name, version, profile, family in (
            ('polygon-extrusions', 'rectangle.ok', '0.8', 'polygon-extrusion-0.1', 'polygon_extrusion'),
            ('polygon-holes', 'square-hole.ok', '0.9', 'polygon-holes-0.1', 'polygon_holes'),
            ('polygon-lofts', 'constant-solid.ok', '0.10', 'polygon-loft-0.1', 'polygon_loft'),
            ('framed-polygon-lofts', 'identity-solid.ok', '0.11', 'framed-polygon-loft-0.1', 'framed_polygon_loft'),
        ):
            with self.subTest(family=family):
                raw = (ROOT / 'examples' / folder / name).read_bytes()
                raw = raw.replace(('ontokin "' + version + '"').encode(), b'ontokin "0.12"', 1)
                raw = raw.replace(profile.encode(), POCKETS_PROFILE.encode(), 1)
                result = execute_pockets_export(bundle(raw), options=OPTIONS)
                self.assertIsNotNone(result.data, result.report)
                surface = DecodedGLB(result.data).document['nodes'][0]['extras']['ontokin']['surface']
                self.assertEqual(surface['family'], family)
                self.assertEqual(surface['profile'], profile)

    def test_earlier_module_cannot_import_unused_pocket_definitions(self):
        library = (FIXTURES / 'parts.ok').read_bytes()
        digest = hashlib.sha256(library).hexdigest()
        raw = (ROOT / 'examples/framed-polygon-lofts/identity-solid.ok').read_bytes()
        addition = (f'import pockets @ "pockets" from "fixture.pocket-parts" version "1.0.0" '
                    f'digest "sha256:{digest}";\n').encode()
        raw = raw.replace(b'public class Shape', addition + b'public class Shape', 1)
        module = SourceUnit('package:fixture.pocket-parts@1.0.0', 'parts.ok', library,
                            'fixture.pocket-parts', '1.0.0')
        result = execute_framed_loft_export(bundle(raw, modules=(module,)), options=OPTIONS)
        self.assertIsNone(result.data)
        self.assertTrue(any(d.get('details', {}).get('dependency_profile') == POCKETS_PROFILE
                            for d in result.report.get('diagnostics', [])), result.report)

    def test_inherited_framed_pure_functions_retain_carrier_authority(self):
        for name, accepted in (('function-section-and-geometry', True),
                               ('function-cross-owner-escape', False)):
            with self.subTest(name=name):
                raw = (ROOT / 'examples/framed-polygon-lofts' / (name + '.ok')).read_bytes()
                raw = raw.replace(b'ontokin "0.11"', b'ontokin "0.12"', 1)
                raw = raw.replace(b'framed-polygon-loft-0.1', POCKETS_PROFILE.encode(), 1)
                result = execute_pockets_export(bundle(raw), options=OPTIONS)
                if accepted:
                    self.assertIsNotNone(result.data, result.report)
                else:
                    self.assertIsNone(result.data)
                    self.assertTrue(any(d['code'] == 'OKL-E-FRAMED-LOFT-FRAME'
                                        for d in result.report.get('diagnostics', [])), result.report)

    def test_new_constructor_remains_unavailable_in_earlier_source_binding(self):
        result = execute_framed_loft_export(bundle((FIXTURES / 'earlier-version-rejection.ok').read_bytes()))
        self.assertIsNone(result.data)
        self.assertTrue(result.report.get('diagnostics'), result.report)

    def test_explicit_entry_request_does_not_create_host_authority(self):
        program = bundle((FIXTURES / 'maximum-pockets-and-vertices.ok').read_bytes())
        result = execute_pockets_export(program, options=OPTIONS)
        self.assertIsNone(result.data)
        self.assertTrue(result.report.get('diagnostics'), result.report)
        self.assertIsNone(result.report.get('artifact'))

    def test_profile_cannot_be_overridden_through_explicit_entry_point(self):
        with self.assertRaises(TypeError):
            execute_pockets_export(self.program, profile='framed-polygon-loft-0.1')


if __name__ == '__main__':
    unittest.main()
