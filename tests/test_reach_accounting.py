"""Inherited scalar/force operations consume the same bounded reach request."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as Q
from pathlib import Path
import unittest

from ontokin.bundle import ProgramBundle, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_runtime import ReachSimulator


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"


def simulator(case, old, new):
    bundle = load_file_manifest(DATA / (case.lower() + ".files.json"))
    if bundle.entry.text.count(old) != 1:
        raise AssertionError("An accounting test must edit one actual source occurrence.")
    entry = replace(bundle.entry, raw=bundle.entry.text.replace(old, new).encode())
    built = compile_construction(ProgramBundle(entry, bundle.modules))
    return ReachSimulator(built.model, work=built.reach_work)


class ReachAccountingTests(unittest.TestCase):
    def test_ordinary_tween_preserves_canonical_values_and_cannot_bypass_work_limit(self):
        sim = simulator("P01", '    at 0[s] sequence { start reach; }',
            '    action ordinary @ "ordinary" = tween(rig.arm.shoulder, 1[rad], 3[s]);\n'
            '    at 0[s] sequence { start ordinary; }')
        sim.advance(Q(0), "after")
        coordinate, rate = sim._coordinate("rig.arm.shoulder", Q(1, 3), sim.state)
        self.assertEqual(coordinate, float(Q(1, 9)))
        self.assertEqual(rate, float(Q(1, 3)))
        consumed = sim.work.operations
        sim.work.max_operations = consumed + 1
        with self.assertRaises(ReachAdmissionError) as caught:
            sim._coordinate("rig.arm.shoulder", Q(1, 3), sim.state)
        self.assertEqual(caught.exception.reach_code, "reach_resource")
        self.assertEqual(sim.work.operations, consumed + 1)

    def test_force_aggregation_rounds_net_before_acceleration_and_obeys_shared_limit(self):
        sim = simulator("P16",
            'force payload @ "released-push" using vector(world, 1[N], 0[N], 0[N]) for 1[s];',
            'force payload @ "released-push" using vector(world, 0.1[N], 0[N], 0[N]) for 1[s]; '
            'force payload @ "second-push" using vector(world, 0.2[N], 0[N], 0[N]) for 1[s];')
        sim.advance(Q(2), "after")
        net, acceleration = sim._force_components("payload", sim.state)
        expected_net = float(Q(0.1) + Q(0.2))
        self.assertEqual(net, (expected_net, 0.0, 0.0))
        self.assertEqual(acceleration,
                         (float(Q(expected_net) / Q(sim.model.objects["payload"].mass)), 0.0, 0.0))
        consumed = sim.work.operations
        sim.work.max_operations = consumed + 1
        with self.assertRaises(ReachAdmissionError) as caught:
            sim._force_components("payload", sim.state)
        self.assertEqual(caught.exception.reach_code, "reach_resource")
        self.assertEqual(sim.work.operations, consumed + 1)


if __name__ == "__main__":
    unittest.main()
