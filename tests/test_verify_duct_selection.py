"""Exercise the named-joint oracle with a flush decoy and a flush quarter-turn."""
from dataclasses import replace
import json
import re
import unittest

from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import load_file_manifest
from ontokin.scene import ExportOptions
from tools.texture_reference import GLB, repack_glb
from tools.verify_duct_selection import EXAMPLE, roll_candidates, verify


class SelectionOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((EXAMPLE / 'selection-contract.json').read_text())
        cls.bundle = load_file_manifest(EXAMPLE / 'assembly-selection.files.json')
        cls.before = cls.export(cls.bundle)
        cls.after = cls.place('outbound', cls.spec['straight_target_rotation_wxyz'])

    @staticmethod
    def export(bundle):
        result = execute_framed_loft_export(bundle, options=ExportOptions(fps=2, end='1', helpers=False))
        if result.data is None:
            raise ValueError(result.report['diagnostics'])
        return result.data

    @classmethod
    def place(cls, elbow, rotation):
        xyz = ', '.join(f'{v:.17g}[m]' for v in cls.spec['stationary'][elbow]['outlet_center_m'])
        q = ', '.join(f'{v:.17g}' for v in rotation)
        text, count = re.subn(r'(object link [^{}]*\{\s*placement = )[^;]+',
                              rf'\g<1>pose(world, vec3({xyz}), quat({q}))', cls.bundle.entry.text)
        assert count == 1
        return cls.export(replace(cls.bundle, entry=replace(cls.bundle.entry, raw=text.encode())))

    def test_flush_decoy_fails_requested_pair(self):
        wrong = self.place('bypass', self.spec['straight_target_rotation_wxyz'])
        result = verify(self.before, self.after, wrong)
        self.assertAlmostEqual(result['decoy_control']['flush']['rectangular_rim_overlap_m2'], 1, delta=self.spec['area_tolerance_m2'])
        self.assertIn('m from outbound/top', result['decoy_control']['rejected_by_named_contract'])
        with self.assertRaisesRegex(ValueError, 'm from outbound/top'):
            verify(self.before, wrong)

    def test_quarter_turn_fails_roll_check(self):
        _, rotation = roll_candidates(self.spec)[1]
        with self.assertRaisesRegex(ValueError, 'Wrong square-roll solution'):
            verify(self.before, self.place('outbound', rotation))

    def test_misattributed_decoy_region(self):
        glb = GLB(self.after, target='ontokin.glb/0.11')
        primitive = glb.primitives('bypass')[0]
        material = glb.reference('materials', primitive['material'])
        material['extras']['ontokin']['occurrence_path'] = 'outbound'
        with self.assertRaisesRegex(ValueError, 'bypass material occurrence identity differs'):
            verify(self.before, repack_glb(glb.document, glb.binary))

    def test_orphan_occurrence_in_program(self):
        glb = GLB(self.after, target='ontokin.glb/0.11')
        occurrences = glb.document['extras']['ontokin']['program']['occurrences']
        occurrences['extra'] = occurrences['outbound']
        with self.assertRaisesRegex(ValueError, 'occurrence inventory'):
            verify(self.before, repack_glb(glb.document, glb.binary))

    def test_rendered_material_changed(self):
        glb = GLB(self.after, target='ontokin.glb/0.11')
        material = glb.reference('materials', glb.primitives('outbound')[0]['material'])
        material['pbrMetallicRoughness']['baseColorFactor'] = [1, 1, 1, 1]
        with self.assertRaisesRegex(ValueError, 'outbound source material differs'):
            verify(self.before, repack_glb(glb.document, glb.binary))
