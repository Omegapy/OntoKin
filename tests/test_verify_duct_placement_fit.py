"""Check occurrence placement recovery on C161 geometry, independent of the third pose."""
from dataclasses import replace
import importlib.util
import struct
from math import cos, dist, radians, sin, sqrt
from pathlib import Path
import unittest

from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import ProgramBundle, load_file_manifest
from ontokin.scene import ExportOptions
from tools.texture_reference import GLB, repack_glb

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples' / 'connected-duct'
spec = importlib.util.spec_from_file_location('fit_placement', EXAMPLE / 'fit_placement.py')
fit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fit)


class FitDuctPlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_file_manifest(EXAMPLE / 'assembly.files.json')

    def export(self, old_q=None):
        source = self.bundle.entry
        if old_q is not None:
            anchor = b'vec3(4[m], 0[m], 4[m]), quat(0.7071067811865476, 0, 0.7071067811865476, 0)'
            self.assertEqual(source.raw.count(anchor), 1)
            placement = 'vec3(9[m], 2[m], -3[m]), quat(' + ', '.join(map(str, old_q)) + ')'
            source = replace(source, raw=source.raw.replace(anchor, placement.encode()))
        result = execute_framed_loft_export(ProgramBundle(source, self.bundle.modules),
                                             options=ExportOptions(fps=2, end='1', helpers=False))
        self.assertIsNotNone(result.data, result.report.get('diagnostics'))
        return result.data

    def check_pose(self, old_q, expected_q):
        actual = fit.solve_placement(self.export(old_q))
        self.assertLess(dist(actual['translation_m'], (4, 0, 4)), 1e-5)
        q = actual['rotation_wxyz']
        self.assertLess(min(dist(q, expected_q), dist(q, [-x for x in expected_q])), 1e-5)

    def test_swing_and_translation(self):
        self.check_pose((1, 0, 0, 0), (sqrt(.5), 0, sqrt(.5), 0))

    def test_quarter_turn_is_nearest_square_match(self):
        # First orient +Z along +X, then roll 80 degrees about +X.
        c, s = cos(radians(40))*sqrt(.5), sin(radians(40))*sqrt(.5)
        self.check_pose((c, s, c, s), (.5, .5, .5, .5))

    def test_opposed_axes_break_four_way_half_turn_tie(self):
        # All four corrections are half turns. For this fixed pose, matching the
        # first world-space outer corners gives a quarter turn around the duct.
        self.check_pose((sqrt(.5), 0, -sqrt(.5), 0), (.5, .5, .5, .5))

    def test_source_identity_mismatch(self):
        glb = GLB(self.export(), target='ontokin.glb/0.11')
        mappings = [glb.document['nodes'][glb.objects()[name]]['extras']['ontokin']['source_mapping']
                    for name in ('straight', 'elbow')]
        mappings[0]['definition'] = mappings[1]['definition']
        with self.assertRaisesRegex(ValueError, 'occurrence identity'):
            fit.solve_placement(repack_glb(glb.document, glb.binary))

    def test_cap_and_material_relabel(self):
        glb = GLB(self.export(), target='ontokin.glb/0.11')
        for primitive in glb.primitives('straight'):
            region = primitive['extras']['ontokin']
            original = region['region_key']
            if original in ('bottom', 'top'):
                new = 'top' if original == 'bottom' else 'bottom'
                region['region_key'] = new
                material = glb.document['materials'][primitive['material']]
                material['name'] = f'straight: {new}'
                material['extras']['ontokin']['source_region_key'] = new
        with self.assertRaisesRegex(ValueError, 'endpoint material'):
            fit.solve_placement(repack_glb(glb.document, glb.binary))

    def test_one_cap_reversed(self):
        glb = GLB(self.export(), target='ontokin.glb/0.11')
        cap = next(p for p in glb.primitives('straight') if p['extras']['ontokin']['region_key'] == 'bottom')
        index = cap['indices']
        accessor = glb.document['accessors'][index]
        view = glb.document['bufferViews'][accessor['bufferView']]
        self.assertEqual(accessor['componentType'], 5123)
        indices = glb.accessor(index)
        for i in range(0, len(indices), 3):
            indices[i], indices[i+1] = indices[i+1], indices[i]
        damaged = bytearray(glb.binary)
        struct.pack_into(f'<{len(indices)}H', damaged, view['byteOffset'], *indices)
        with self.assertRaisesRegex(ValueError, 'winding or rim'):
            fit.solve_placement(repack_glb(glb.document, bytes(damaged)))

    def test_wrong_endpoint(self):
        with self.assertRaisesRegex(ValueError, 'elbow outlet and straight inlet'):
            fit.solve_placement(self.export(), straight_region='top')
