"""Exercise C163's independent verifier against altered geometry, placement, and source identity."""
from dataclasses import replace
import json
import math
import struct
import unittest

from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import load_file_manifest
from ontokin.scene import ExportOptions
from tools.texture_reference import GLB, repack_glb
from tools.verify_duct_placement import CONTRACT, verify


class PlacementOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(CONTRACT.read_text())
        cls.bundle = load_file_manifest(CONTRACT.with_name('assembly-misplaced.files.json'))
        cls.before = cls.export(cls.bundle)
        cls.after = cls.export_straight(cls.spec['straight_inlet_center_m'], cls.spec['straight_target_rotation_wxyz'])

    @staticmethod
    def export(bundle):
        result = execute_framed_loft_export(bundle, options=ExportOptions(fps=2, end='1', helpers=False))
        if result.data is None:
            raise ValueError(result.report['diagnostics'])
        return result.data

    @classmethod
    def export_straight(cls, position, rotation):
        source = cls.bundle.entry
        old = [line for line in source.raw.splitlines() if b'placement = pose(' in line][-1]
        coords = ', '.join(f'{v:.17g}[m]' for v in position)
        quat = ', '.join(f'{v:.17g}' for v in rotation)
        new = f'        placement = pose(world, vec3({coords}), quat({quat}));'.encode()
        return cls.export(replace(cls.bundle, entry=replace(source, raw=source.raw.replace(old, new))))

    def test_frozen_pose(self):
        self.assertAlmostEqual(verify(self.before, self.after)['repaired']['rectangular_rim_overlap_m2'], 1, places=5)

    def test_before_contains_both_active_ducts(self):
        glb = GLB(self.before, target='ontokin.glb/0.11')
        glb.document['scenes'][0]['nodes'] = [glb.objects()['straight']]
        with self.assertRaisesRegex(ValueError, 'active scene'):
            verify(repack_glb(glb.document, glb.binary), self.after)

    def test_before_has_no_extra_lateral_offset(self):
        raw = GLB(self.before, target='ontokin.glb/0.11')
        straight = raw.document['nodes'][raw.objects()['straight']]
        # The oracle's second column lies in the elbow's outlet plane.
        t = [v + .2 * row[1] for v, row in zip(straight['translation'], self.spec['rotation_rows'])]
        x, y, z, w = straight['rotation']
        norm = math.hypot(x, y, z, w)
        shifted = self.export_straight(t, [v/norm for v in (w, x, y, z)])
        with self.assertRaisesRegex(ValueError, 'inlet displacement'):
            verify(shifted, self.after)

    def test_after_changed_straight_definition(self):
        glb = GLB(self.after, target='ontokin.glb/0.11')
        nodes = glb.document['nodes']
        elbow, straight = [nodes[glb.objects()[name]]['extras']['ontokin'] for name in ('elbow', 'straight')]
        straight['source_mapping']['definition'] = elbow['source_mapping']['definition']
        with self.assertRaisesRegex(ValueError, 'source mapping'):
            verify(self.before, repack_glb(glb.document, glb.binary))

    def test_after_changed_elbow_side_wall(self):
        glb = GLB(self.after, target='ontokin.glb/0.11')
        wall = next(p for p in glb.primitives('elbow') if p['extras']['ontokin']['region_key'] == 'outer')
        accessor = glb.reference('accessors', wall['attributes']['POSITION'])
        view = glb.reference('bufferViews', accessor['bufferView'])
        offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        binary = bytearray(glb.binary)
        x, = struct.unpack_from('<f', binary, offset)
        struct.pack_into('<f', binary, offset, x+.25)
        with self.assertRaisesRegex(ValueError, 'Local duct geometry streams changed'):
            verify(self.before, repack_glb(glb.document, bytes(binary)))
