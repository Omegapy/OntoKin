"""Check geometry-derived two-bend fits and refusal of unsupported frames and spans."""
from dataclasses import replace
from math import dist, inf, nan
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
    from offset_solver import solve
finally:
    sys.path.remove(str(EXAMPLE))

CHAIN = ('outbound', 'lead', 'turn', 'bridge', 'rise', 'tail', 'inbound')


class OffsetFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_file_manifest(EXAMPLE / 'offset-achievable.files.json')
        cls.raw = cls.export(cls.bundle.entry.raw)

    @classmethod
    def export(cls, source):
        result = execute_framed_loft_export(replace(cls.bundle, entry=replace(cls.bundle.entry, raw=source)),
                                            policy=HostPolicy(300000, 30000),
                                            options=ExportOptions(end='1', fps=2, helpers=False))
        if result.data is None:
            raise AssertionError(result.report.get('diagnostics'))
        return result.data

    def test_fit_follows_new_sink_and_renamed_second_bend(self):
        scene = self.bundle.entry.raw.replace(b'10.5[m], 12.5[m], 9.75[m]', b'12[m], 13[m], 10[m]')
        scene = scene.replace(b'rise', b'corner').replace(b'3[m], -4[m], 0[m]), quat(1, 0, 0, 0)',
                                                         b'3[m], -4[m], 0[m]), quat(0, 1, 0, 0)')
        chain = (*CHAIN[:4], 'corner', *CHAIN[5:])
        result = solve(self.export(scene), *chain, middle_direction=(0, 5, 0))
        for name, length in [('lead', 3), ('bridge', 4), ('tail', 6)]:
            self.assertAlmostEqual(result[name]['length_m'], length, places=5)
        self.assertLess(dist(result['corner']['translation_m'], (2, 9, 10)), 1e-5)

    def test_invalid_middle_directions(self):
        for direction, reason in [((0, 1), 'three finite'), ((0, 1, 0, 0), 'three finite'),
                                  ((0, inf, 0), 'three finite'), ((nan, 1, 0), 'three finite'),
                                  ((0, 0, 0), 'Degenerate'), ((0, 1, 1), 'right angle')]:
            with self.subTest(direction=direction), self.assertRaisesRegex(ValueError, reason):
                solve(self.raw, *CHAIN, middle_direction=direction)

    def test_coplanar_directions_do_not_define_three_lengths(self):
        scene = self.bundle.entry.raw.replace(b'quat(0.7071067811865476, 0, 0.7071067811865476, 0)',
                                             b'quat(1, 0, 0, 0)')
        with self.assertRaisesRegex(ValueError, 'linearly independent'):
            solve(self.export(scene), *CHAIN, middle_direction=(0, 1, 0))

    def test_middle_span_must_be_constructible(self):
        for sink_y in (b'8.5[m]', b'9.0005[m]', b'110[m]'):
            scene = self.bundle.entry.raw.replace(b'12.5[m]', sink_y)
            with self.subTest(sink_y=sink_y), self.assertRaisesRegex(ValueError, 'Straight spans'):
                solve(self.export(scene), *CHAIN, middle_direction=(0, 1, 0))
