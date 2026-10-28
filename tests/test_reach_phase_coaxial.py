"""Topology-proved ideal derivatives preserve all source numeric allowances."""
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace as N
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_runtime import ReachSimulator
from test_reach_phase import source


DERIVATIVES = {
    "carrier_speed_upper_m_per_s", "carrier_acceleration_upper_m_per_s2",
    "angular_speed_upper_rad_per_s", "angular_acceleration_upper_rad_per_s2",
}
IDENTITY = (1.0, 0.0, 0.0, 0.0)


def pose(position=(0.0, 0.0, 0.0), rotation=IDENTITY):
    return N(position=position, rotation=rotation)


def chain(rates=(1.5, -0.5), *, axis=(0.0, 0.0, 1.0),
          second_axis=None, mount=IDENTITY, child=IDENTITY):
    """Two exact affine hinges and their complete small source topology."""
    sites = {
        "rig.base": N(owner="rig", pose=pose()),
        "first.origin": N(owner="first", pose=pose()),
        "first.end": N(owner="first", pose=pose((1.0, 0.0, 0.0), mount)),
        "second.origin": N(owner="second", pose=pose(rotation=child)),
        "second.tip": N(owner="second", pose=pose((1.0, 0.0, 0.0))),
    }
    joints = {
        "shoulder": N(kind="hinge", parent="rig.base", child="first.origin", axis=axis),
        "elbow": N(kind="hinge", parent="first.end", child="second.origin",
                   axis=axis if second_axis is None else second_axis),
    }
    actions = {name: N(kind="tween", target=name, goal=rate, duration=F(1))
               for name, rate in zip(joints, rates)}
    states = {name: N(initial=0.0, ideal_initial=F(0), status="running",
                       running_since=F(0), elapsed=F(0), elapsed_at=lambda time: time)
              for name in joints}
    model = N(duration=F(1), events=(), objects=dict.fromkeys(("rig", "first", "second")),
              sites=sites, joints=joints, follows={}, actions=actions)
    state = N(positions={"rig": (0.0, 0.0, 0.0)},
              ideal_positions={"rig": (F(0), F(0), F(0))}, root_rotation_errors={},
              coordinates=dict.fromkeys(joints, 0.0), ideal_coordinates=dict.fromkeys(joints, F(0)),
              claims={(name, "coordinate"): name for name in joints}, actions=states,
              forces={}, modes={"rig": "prescribed"})
    return N(model=model, state=state, work=ReachExecutionWork(), pose_ops=N(),
             _incoming=lambda state: {"first": ("joint", "shoulder"), "second": ("joint", "elbow")})


def bounds(simulator, *, generic=False):
    if generic:
        with patch.object(reach_phase, "_tighten_angular", side_effect=lambda bound, rate, work: bound):
            return reach_phase.phase_bounds(simulator, F(0), F(1))
    return reach_phase.phase_bounds(simulator, F(0), F(1))


class CoaxialPhaseTests(unittest.TestCase):
    def assert_numeric_equal(self, actual, expected):
        self.assertEqual(actual["joints"], expected["joints"])
        for kind in ("objects", "frames"):
            self.assertEqual(set(actual[kind]), set(expected[kind]))
            for path, bound in actual[kind].items():
                previous = expected[kind][path]
                for name in reach_phase._BOUND_FIELDS:
                    if name not in DERIVATIVES:
                        self.assertEqual(getattr(bound, name), getattr(previous, name), (kind, path, name))
                    else:
                        self.assertLessEqual(getattr(bound, name), getattr(previous, name), (kind, path, name))

    def test_exact_signed_rate_and_zero_alpha_on_each_cartesian_axis(self):
        for axis in ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)):
            for rates in ((1.5, -0.5), (1.5, -1.5), (1.5, 0.5)):
                with self.subTest(axis=axis, rates=rates):
                    actual = bounds(chain(rates, axis=axis))
                    expected = bounds(chain(rates, axis=axis), generic=True)
                    self.assert_numeric_equal(actual, expected)
                    tip = actual["frames"]["second.tip.frame"]
                    self.assertEqual(tip.angular_speed_upper_rad_per_s, abs(sum(map(F, rates), F(0))))
                    self.assertEqual(tip.angular_acceleration_upper_rad_per_s2, 0)
                    self.assertGreater(expected["frames"]["second.tip.frame"].angular_acceleration_upper_rad_per_s2, 0)
                    self.assertGreater(tip.actual_angular_speed_upper_rad_per_s, 0)
                    self.assertGreater(tip.angular_velocity_error_rad_per_s, 0)

    def test_exact_axis_reversing_mount_and_inverse_child_are_retained(self):
        half_turn_x = (0.0, 1.0, 0.0, 0.0)
        simulator = chain((1.5, 0.5), mount=half_turn_x, child=half_turn_x)
        actual = bounds(simulator)
        expected = bounds(chain((1.5, 0.5), mount=half_turn_x, child=half_turn_x), generic=True)
        self.assert_numeric_equal(actual, expected)
        self.assertEqual(actual["objects"]["second"].angular_speed_upper_rad_per_s, F(1))
        self.assertEqual(actual["objects"]["second"].angular_acceleration_upper_rad_per_s2, F(0))
        rate = reach_phase._AxialRate(2, F(-1))
        self.assertEqual(reach_phase._transport_axial_rate(rate, half_turn_x, simulator.work),
                         reach_phase._AxialRate(2, F(1)))

    def test_noncoaxial_joint_or_unproved_mount_keeps_generic_child_recurrence(self):
        for kwargs in ({"second_axis": (1.0, 0.0, 0.0)},
                       {"mount": (0.5, 0.0, 0.5, 0.0)}):
            with self.subTest(kwargs=kwargs):
                actual = bounds(chain(**kwargs))
                expected = bounds(chain(**kwargs), generic=True)
                self.assert_numeric_equal(actual, expected)
                # The first hinge's zero alpha also holds in the generic path.
                self.assertEqual(actual["objects"]["second"], expected["objects"]["second"])
                self.assertGreater(actual["objects"]["second"].angular_acceleration_upper_rad_per_s2, 0)

    def test_canonical_guards_reject_approximate_axes_and_unsupported_quaternions(self):
        work = ReachExecutionWork()
        for vector in ((0.0, 0.0, 0.9999999999999999), (0.0, 0.0, float("inf")),
                       (0, 0, 1), (False, 0.0, 1.0), [0.0, 0.0, 1.0]):
            self.assertIsNone(reach_phase._single_axis(vector, work, unit=True))
        rate = reach_phase._AxialRate(2, F(2))
        for rotation in ((0.0, 0.0, 0.0, 0.0), (float("nan"), 0.0, 0.0, 1.0),
                         (1, 0, 0, 0), (1.0, 0.0, 0.5, 0.0), (1.0, 0.0, 0.0)):
            self.assertIsNone(reach_phase._transport_axial_rate(rate, rotation, work))
        narrow = ReachExecutionWork(max_operand_bits=1024)
        self.assertIsNone(reach_phase._single_axis((0.0, 0.0, 1.0), narrow, unit=True))
        self.assertIsNone(reach_phase._transport_axial_rate(rate, IDENTITY, narrow))

    def test_running_root_spin_requires_an_exact_untransferred_axis(self):
        action = N(vector=(0.0, 0.0, 0.25))
        runtime = N(ideal_rotation_error=F(0), initial_rotation=None, initial=IDENTITY)
        work = ReachExecutionWork()
        self.assertEqual(reach_phase._root_axial_rate(action, runtime, work),
                         reach_phase._AxialRate(2, F(1, 4)))
        runtime.initial = (0.0, 1.0, 0.0, 0.0)
        self.assertEqual(reach_phase._root_axial_rate(action, runtime, work),
                         reach_phase._AxialRate(2, F(-1, 4)))
        for changes in ({"ideal_rotation_error": F(1, 1 << 90)}, {"initial_rotation": object()},
                        {"initial": (0.5, 0.0, 0.5, 0.0)}):
            candidate = N(ideal_rotation_error=F(0), initial_rotation=None, initial=IDENTITY)
            vars(candidate).update(changes)
            self.assertIsNone(reach_phase._root_axial_rate(action, candidate, work))
        self.assertIsNone(reach_phase._root_axial_rate(N(vector=(0.25, 0.0, 0.25)), runtime, work))

    def test_hot_phase_rechecks_changed_mount_axis_and_cache_eviction(self):
        simulator = chain()
        original = bounds(simulator)
        simulator.model.sites["first.end"].pose = pose((1.0, 0.0, 0.0), (0.5, 0.0, 0.5, 0.0))
        actual = bounds(simulator)
        expected = bounds(chain(mount=(0.5, 0.0, 0.5, 0.0)))
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, original)
        simulator.model.sites["first.end"].pose = pose((1.0, 0.0, 0.0))
        simulator.model.joints["elbow"].axis = (0.0, 0.0, -1.0)
        expected = bounds(chain(second_axis=(0.0, 0.0, -1.0)))
        self.assertEqual(bounds(simulator), expected)
        for index in range(simulator.work.max_cache_entries + 1):
            simulator.work.remember(("coaxial_eviction", index), index)
        self.assertEqual(bounds(simulator), expected)
        self.assertLessEqual(len(simulator.work._cache), 256)
        self.assertEqual(simulator.work.operations, sum(simulator.work.counts.values()))

    def test_fresh_tightening_admits_current_rate_after_callback_limit_change(self):
        simulator = chain()
        bounds(simulator)
        original = simulator.work.charge
        before = deepcopy(simulator.state.coordinates), dict(simulator.state.claims)

        def charge(kind="checkpoint", amount=1):
            if kind == "phase_axial_derivative_guard":
                simulator.work.max_operand_bits = 16
            original(kind, amount)

        with patch.object(simulator.work, "charge", charge):
            with self.assertRaises(ReachAdmissionError) as caught:
                bounds(simulator)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual((simulator.state.coordinates, simulator.state.claims), before)

    def test_cancelled_proof_keeps_original_callback_and_source_state(self):
        for checkpoint in ("phase_axial_hinge_guard", "phase_axial_transport_guard", "phase_axial_derivative_guard"):
            with self.subTest(checkpoint=checkpoint):
                simulator = chain()
                expected = bounds(simulator)
                original = simulator.work.charge
                before = deepcopy(simulator.state.coordinates), dict(simulator.state.claims)
                marker = RuntimeError("cancel coaxial source proof")

                def charge(kind="checkpoint", amount=1):
                    if kind == checkpoint:
                        with patch.object(simulator.work, "external_check", side_effect=marker):
                            return original(kind, amount)
                    return original(kind, amount)

                with patch.object(simulator.work, "charge", charge):
                    with self.assertRaises(RuntimeError) as caught:
                        bounds(simulator)
                self.assertIs(caught.exception, marker)
                self.assertIs(simulator.work.callback_error, marker)
                self.assertEqual((simulator.state.coordinates, simulator.state.claims), before)
                self.assertEqual(bounds(simulator), expected)

    def test_source_wrap_and_spinning_release_keep_numeric_allowances_exact(self):
        for case, start, end in (("P09", F(0), F(2)), ("P16", F(0), F(2)), ("P16", F(2), F(3)),
                                 ("L02", F(1, 2), F(3, 2))):
            with self.subTest(case=case, start=start):
                results = []
                for generic in (False, True):
                    built = compile_construction(source(case))
                    simulator = ReachSimulator(built.model, work=built.reach_work)
                    simulator.advance(start, "after")
                    if generic:
                        with patch.object(reach_phase, "_tighten_angular", side_effect=lambda bound, rate, work: bound):
                            result = reach_phase.phase_bounds(simulator, start, end)
                    else:
                        result = reach_phase.phase_bounds(simulator, start, end)
                    results.append(result)
                    self.assertLessEqual(built.budget.operations, 100000)
                self.assert_numeric_equal(*results)
                if case == "P09":
                    payload = simulator.model.actions["reach"].reach
                    slopes = tuple(results[0]["joints"][path].ideal_slope
                                   for path in (payload.shoulder, payload.elbow))
                    tip = results[0]["frames"][payload.tip + ".frame"]
                    self.assertEqual(tip.angular_speed_upper_rad_per_s, abs(sum(slopes, F(0))))
                    self.assertEqual(tip.angular_acceleration_upper_rad_per_s2, F(0))
                    self.assertLess(tip.carrier_acceleration_upper_m_per_s2,
                                    results[1]["frames"][payload.tip + ".frame"].carrier_acceleration_upper_m_per_s2)
                if case == "P16" and start == 2:
                    self.assertEqual(results[0]["objects"]["payload"], results[1]["objects"]["payload"])


if __name__ == "__main__":
    unittest.main()
