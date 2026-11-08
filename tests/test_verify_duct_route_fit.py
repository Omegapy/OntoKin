"""Exercise the GLB-derived elbow route under changes to the frozen source."""
from dataclasses import replace
from math import dist
from pathlib import Path
import sys
import unittest

from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import load_file_manifest
from ontokin.execution_budget import HostPolicy
from ontokin.scene import ExportOptions

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples' / 'connected-duct'
sys.path.insert(0, str(EXAMPLE))
try:
    from route_solver import solve
finally:
    sys.path.remove(str(EXAMPLE))


class RouteFitTests(unittest.TestCase):
    def exported(self, changes=(), case='achievable'):
        bundle = load_file_manifest(EXAMPLE / f'route-{case}.files.json')
        raw = bundle.entry.raw
        for old, new in changes:
            self.assertIn(old, raw)
            raw = raw.replace(old, new)
        result = execute_framed_loft_export(replace(bundle, entry=replace(bundle.entry, raw=raw)),
                                            policy=HostPolicy(300000, 30000),
                                            options=ExportOptions(end='1', fps=2, helpers=False))
        self.assertIsNotNone(result.data, result.report.get('diagnostics'))
        return result.data

    @staticmethod
    def fit(raw, bend='turn'):
        return solve(raw, 'outbound', 'lead', bend, 'tail', 'inbound')

    def test_frozen_route(self):
        result = self.fit(self.exported())
        self.assertAlmostEqual(result['lead']['length_m'], 2.75, places=5)
        self.assertAlmostEqual(result['tail']['length_m'], 4.5, places=5)
        for name, expected in [('lead', (2, 1, 3)), ('turn', (2, 1, 5.75)), ('tail', (6, 1, 9.75))]:
            self.assertLess(dist(result[name]['translation_m'], expected), 1e-5)

    def test_rotated_exit_and_renamed_reversed_initial_bend(self):
        # A +Y route and a reversed initial bend exercise both independent rotation axes.
        source = self.exported([
            (b'10.5[m], 1[m], 9.75[m]), quat(0.7071067811865476, 0, 0.7071067811865476, 0)',
             b'2[m], 12[m], 10[m]), quat(0.7071067811865476, -0.7071067811865476, 0, 0)'),
            (b'0[m], 1[m], 1[m]), quat(1, 0, 0, 0)', b'0[m], 1[m], 1[m]), quat(0, 1, 0, 0)'),
            (b'turn', b'corner')])
        result = self.fit(source, 'corner')
        self.assertAlmostEqual(result['lead']['length_m'], 3, places=5)
        self.assertAlmostEqual(result['tail']['length_m'], 7, places=5)
        self.assertLess(dist(result['corner']['translation_m'], (2, 1, 6)), 1e-5)
        self.assertLess(dist(result['tail']['translation_m'], (2, 5, 10)), 1e-5)

    def test_incompatible_geometry(self):
        with self.assertRaisesRegex(ValueError, 'skew.*0.25'):
            self.fit(self.exported(case='incompatible'))
        with self.assertRaisesRegex(ValueError, 'positive'):
            self.fit(self.exported([(b'10.5[m]', b'5[m]')]))
        with self.assertRaisesRegex(ValueError, 'right angle'):
            self.fit(self.exported([(b'quat(0.7071067811865476, 0, 0.7071067811865476, 0)',
                                     b'quat(1, 0, 0, 0)')]))
