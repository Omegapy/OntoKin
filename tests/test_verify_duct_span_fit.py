"""Two-ended sizing follows selected meshes under pose, source and selector changes."""
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
    from span_solver import solve
finally:
    sys.path.remove(str(EXAMPLE))


class SpanSolverTests(unittest.TestCase):
    @staticmethod
    def export(bundle):
        result = execute_framed_loft_export(bundle, policy=HostPolicy(200000, 30000),
                                            options=ExportOptions(end='1', fps=2, helpers=False))
        if result.data is None:
            raise ValueError(result.report['diagnostics'])
        return result.data

    @classmethod
    def setUpClass(cls):
        cls.bundle = load_file_manifest(EXAMPLE / 'span-achievable.files.json')
        cls.raw = cls.export(cls.bundle)

    def changed(self, old, new):
        entry = self.bundle.entry
        self.assertIn(old, entry.raw)
        return self.export(replace(self.bundle, entry=replace(entry, raw=entry.raw.replace(old, new))))

    @staticmethod
    def fit(raw, sink='inbound'):
        return solve(raw, 'outbound', 'top', sink, 'bottom', 'link', 'bottom', 'top')

    def test_signed_span_uses_named_end(self):
        pose = self.fit(self.raw)
        self.assertLess(dist(pose['translation_m'], (5, 2, 3)), 1e-5)
        self.assertAlmostEqual(pose['length_m'], 5.75)
        self.assertAlmostEqual(self.fit(self.raw, 'bypass')['length_m'], 10.75)
        raw = self.changed(b'inbound', b'plenum')
        self.assertEqual(self.fit(raw, 'plenum'), pose)

    def test_rotated_scene_and_different_span(self):
        # Rotate both selected elbow frames by world Z+90. The new span is along +Y.
        entry = self.bundle.entry
        raw = entry.raw
        for old, new in [(b'10.75[m], 2[m], 3[m]', b'-2[m], 12[m], 3[m]'),
                         (b'1[m], 2[m], -1[m]', b'-2[m], 1[m], -1[m]'),
                         (b'quat(0.7071067811865476, 0, 0.7071067811865476, 0)', b'quat(0.5, -0.5, 0.5, 0.5)'),
                         (b'quat(1, 0, 0, 0)', b'quat(0.7071067811865476, 0, 0, 0.7071067811865476)')]:
            raw = raw.replace(old, new)
        fitted = self.fit(self.export(replace(self.bundle, entry=replace(entry, raw=raw))))
        self.assertAlmostEqual(fitted['length_m'], 7)
        self.assertLess(dist(fitted['translation_m'], (-2, 5, 3)), 1e-5)

    def test_infeasible_frames(self):
        bad = load_file_manifest(EXAMPLE / 'span-incompatible.files.json')
        with self.assertRaisesRegex(ValueError, 'lateral offset'):
            self.fit(self.export(bad))
        for x in [b'5', b'4']:
            with self.subTest(x=x), self.assertRaisesRegex(ValueError, 'positive'):
                self.fit(self.changed(b'10.75[m]', x + b'[m]'))
        start = b'10.75[m], 2[m], 3[m]), quat(0.7071067811865476, 0, 0.7071067811865476, 0)'
        for rotation, error in [(b'quat(1, 0, 0, 0)', 'normal'),
                                (b'quat(0.6532814824381883, 0.2705980500730985, 0.6532814824381883, 0.2705980500730985)', 'rim')]:
            with self.subTest(rotation=rotation), self.assertRaisesRegex(ValueError, error):
                self.fit(self.changed(start, b'10.75[m], 2[m], 3[m]), ' + rotation))

    def test_nonpositive_authored_length_rejected_by_loft(self):
        for length in (b'0', b'-1'):
            with self.subTest(length=length), self.assertRaisesRegex(ValueError, 'OKL-E-FRAMED-LOFT-PROGRESSION'):
                self.changed(b'span = 4[m]', b'span = ' + length + b'[m]')

    def test_invalid_requests(self):
        for args in [('outbound', 'top', 'inbound', 'bottom', 'link', 'top', 'bottom'),
                     ('outbound', 'top', 'outbound', 'bottom', 'link', 'bottom', 'top'),
                     ('outbound', 'top', 'missing', 'bottom', 'link', 'bottom', 'top')]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                solve(self.raw, *args)
