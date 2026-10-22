"""Independent endpoint maxima survive bounded-cache traversal changes."""
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_export as export
from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions


def carrier_major(nodes, keys, model, *, work):
    result = []
    for node in nodes:
        retained = [F(0), F(0), F(0)]
        for key in sorted(keys):
            values = export._endpoint_rounding(tuple(node.translations[key]),
                tuple(node.rotations_xyzw[key]), model, work=work)
            retained = [max(a, b) for a, b in zip(retained, values)]
        result.append(tuple(retained))
    return tuple(result)


def translated_tracks(count=160):
    rotations = tuple((index / 997., 0., 0., 1.) for index in range(count))
    return tuple(SimpleNamespace(
        translations=tuple((carrier + index / 991., 0., 0.) for index in range(count)),
        rotations_xyzw=rotations) for carrier in range(4))


class ReachEndpointTraversalTests(unittest.TestCase):
    def test_long_tracks_reuse_only_identical_components_without_cache_growth(self):
        nodes = translated_tracks()
        old, new = ReachExecutionWork(), ReachExecutionWork()
        keys = set(range(len(nodes[0].translations)))
        expected = carrier_major(nodes, keys, None, work=old)
        actual = export._endpoint_group_maxima(nodes, keys, None, work=new)
        self.assertEqual(actual, expected)
        self.assertLess(new.operations, old.operations)
        self.assertLessEqual(len(new._cache), 256)
        self.assertEqual(new.operations, sum(new.counts.values()))
        self.assertEqual(len(set(row[2] for row in actual)), 4)

    def test_each_requested_endpoint_contributes_to_its_own_carrier(self):
        nodes = translated_tracks(7)
        keys = {0, 3, 6}
        actual = export._endpoint_group_maxima(nodes, keys, None, work=ReachExecutionWork())
        for carrier, node in enumerate(nodes):
            decoded = [export._endpoint_rounding(node.translations[key], node.rotations_xyzw[key],
                       None, work=ReachExecutionWork()) for key in keys]
            self.assertEqual(actual[carrier], tuple(max(row[axis] for row in decoded) for axis in range(3)))

    def test_cancellation_preserves_input_tracks_and_propagates_original_exception(self):
        nodes = translated_tracks(7)
        original = tuple((node.translations, node.rotations_xyzw) for node in nodes)
        marker = RuntimeError("cancel during endpoint traversal")
        calls = 0
        def cancel():
            nonlocal calls
            calls += 1
            if calls == 83:
                raise marker
        with self.assertRaises(RuntimeError) as caught:
            export._endpoint_group_maxima(nodes, range(7), None, work=ReachExecutionWork(check=cancel))
        self.assertIs(caught.exception, marker)
        self.assertEqual(original, tuple((node.translations, node.rotations_xyzw) for node in nodes))

    def test_complete_p01_bytes_equal_carrier_major_proofs(self):
        root = Path(__file__).resolve().parents[1]
        def build():
            compiler = compile_construction(load_file_manifest(
                root / "docs/language-design/planar-reach-v0.1/p01.files.json"), level="constructed")
            return export_glb(compiler.model, options=ExportOptions(end=F(3), fps=1, helpers=False),
                              target_contract="ontokin.glb/0.6", work=compiler.reach_work)
        current = build()
        with patch.object(export, "_endpoint_group_maxima", new=carrier_major):
            previous = build()
        self.assertEqual(current.data, previous.data)
        self.assertEqual(current.report["validation"], previous.report["validation"])


if __name__ == "__main__":
    unittest.main()
