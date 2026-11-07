"""Exercise explicit port selection, renamed occurrences and occurrence-scoped editing."""
from dataclasses import replace
from math import dist
from pathlib import Path
import sys
import unittest

from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import load_file_manifest
from ontokin.scene import ExportOptions
from tools.texture_reference import GLB, repack_glb

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples' / 'connected-duct'
sys.path.insert(0, str(EXAMPLE))
try:
    from agent_select import occurrences, placement_patch
    from fit_placement import SelectionError, solve_placement
finally:
    sys.path.remove(str(EXAMPLE))


class SelectionFitTests(unittest.TestCase):
    @staticmethod
    def export(bundle):
        exported = execute_framed_loft_export(bundle, options=ExportOptions(fps=2, end='1', helpers=False))
        if exported.data is None:
            raise ValueError(exported.report['diagnostics'])
        return exported.data

    @classmethod
    def setUpClass(cls):
        cls.bundle = load_file_manifest(EXAMPLE / 'assembly-selection.files.json')
        cls.raw = cls.export(cls.bundle)

    def test_renamed_target_and_moving_instance(self):
        source = self.bundle.entry
        renamed = replace(source, raw=source.raw.replace(b'outbound', b'to_plenum').replace(b'link', b'branch'))
        actual = solve_placement(self.export(replace(self.bundle, entry=renamed)), elbow='to_plenum', straight='branch')
        self.assertEqual(actual, solve_placement(self.raw, elbow='outbound', straight='link'))

    def test_explicit_choice_between_instances_of_same_class(self):
        requested = solve_placement(self.raw, elbow='outbound', straight='link')
        decoy = solve_placement(self.raw, elbow='bypass', straight='link')
        self.assertAlmostEqual(dist(requested['translation_m'], decoy['translation_m']), 4, places=5)

    def test_reject_unresolvable_or_wrong_role_selectors(self):
        class_id = occurrences(self.raw)['outbound']['class_id']
        for selector, error in [('missing', 'Unknown'), (class_id, 'Ambiguous'), ('link', 'wrong class')]:
            with self.subTest(elbow=selector), self.assertRaisesRegex(SelectionError, error):
                solve_placement(self.raw, elbow=selector, straight='link')
        for region in ['bottom', 'unknown']:
            with self.subTest(region=region), self.assertRaisesRegex(SelectionError, 'elbow outlet'):
                solve_placement(self.raw, elbow='outbound', straight='link', elbow_region=region)

    def test_all_three_occurrences_require_both_stationary_tracks(self):
        doc = GLB(self.raw, target='ontokin.glb/0.11')
        doc.document['animations'][0]['channels'].pop()
        with self.assertRaisesRegex(ValueError, 'Missing transform channel'):
            solve_placement(repack_glb(doc.document, doc.binary), elbow='outbound', straight='link')

    def test_patch_chooses_correct_occurrence_with_duplicate_placement_text(self):
        lines = self.bundle.entry.raw.splitlines(keepends=True)
        placements = [i for i, line in enumerate(lines) if b'placement = pose' in line]
        lines[placements[0]] = lines[placements[-1]]
        bundle = replace(self.bundle, entry=replace(self.bundle.entry, raw=b''.join(lines)))
        raw = self.export(bundle)
        pose = solve_placement(raw, elbow='outbound', straight='link')
        mappings = occurrences(raw)
        patch = placement_patch(bundle, mappings['link'], pose)
        old = patch['expected_text'].encode()
        self.assertEqual(bundle.entry.raw.count(old), 2)
        self.assertEqual(patch['start_byte'], bundle.entry.raw.rindex(old))
        self.assertGreater(patch['start_byte'], mappings['bypass']['declaration']['end_byte'])

    def test_counterfeit_signed_endpoints(self):
        for name in ('outbound', 'link'):
            with self.subTest(name=name):
                glb = GLB(self.raw, target='ontokin.glb/0.11')
                caps = {p['extras']['ontokin']['region_key']: p for p in glb.primitives(name)}
                top, bottom = caps['top'], caps['bottom']
                top['indices'], bottom['indices'] = bottom['indices'], top['indices']
                meta = glb.document['nodes'][glb.objects()[name]]['extras']['ontokin']
                sections = meta['surface']['sections']
                a, b = sections[0], sections[-1]
                a['origin_m'], b['origin_m'] = b['origin_m'], a['origin_m']
                recipe = meta['geometry']['sections']
                a, b = recipe[0]['frame'], recipe[-1]['frame']
                a['position'], b['position'] = b['position'], a['position']
                with self.assertRaisesRegex(ValueError, 'signed inlet winding'):
                    solve_placement(repack_glb(glb.document, glb.binary), elbow='outbound', straight='link')
