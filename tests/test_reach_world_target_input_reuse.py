"""Raw target receipts retain the original decode and component semantics."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_pose
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError
from test_reach_relative_observations import prepared
from test_reach_world_target_components import bits, component_key, ordinary, target


def outcome(simulator, base, payload, *, direct=False):
    try:
        return bits(ordinary(simulator, base, payload) if direct else target(simulator, base, payload).position)
    except ReachAdmissionError as error:
        return error.reach_code, str(error), error.details


class ReachWorldTargetInputReuseTests(unittest.TestCase):
    def test_32_native_targets_keep_exact_points_without_repeating_decodes(self):
        costs, outputs = [], []
        for native in (True, False):
            simulator = prepared()
            payload = simulator.model.actions["reach"].reach
            if not native:
                payload = replace(payload, target_m=list(payload.target_m))
            base = simulator.pose_ops.make(orientation=simulator.pose_ops.axis_rotation((1, 1, 1), F(2, 7)))
            target(simulator, base, payload)
            before = simulator.work.operations
            decodes = simulator.work.counts.get("binary64_decode", 0)
            values = []
            for index in range(32):
                moved = replace(base, exact_position=(F(0), F(index, 4), F(0)))
                values.append(bits(target(simulator, moved, payload).position))
            costs.append(simulator.work.operations - before)
            outputs.append(values)
            if native:
                self.assertEqual(simulator.work.counts.get("binary64_decode", 0), decodes)
            else:
                self.assertEqual(simulator.work.counts.get("binary64_decode", 0) - decodes, 96)
            self.assertEqual(simulator.work.operations, sum(simulator.work.counts.values()))
            self.assertLessEqual(len(simulator.work._cache), simulator.work.max_cache_entries)
        self.assertEqual(outputs[0], outputs[1])
        self.assertLess(costs[0], costs[1])

    def test_native_keys_bind_every_actual_component_and_signed_zero(self):
        simulator = prepared()
        payload = simulator.model.actions["reach"].reach
        base = simulator.pose_ops.make(position=(F(2), F(3), F(5)))
        variants = ((1.0, 1.0, 0.0), (2.0, 1.0, 0.0), (1.0, 2.0, 0.0),
                    (1.0, 1.0, 0.5), (1.0, 1.0, -0.0))
        for values in variants:
            request = replace(payload, target_m=values)
            actual = target(simulator, base, request)
            self.assertEqual(bits(actual.position), bits(ordinary(simulator, base, request)))
            self.assertIs(target(simulator, base, request), actual)
        entries = [(key, value) for key, value in simulator.work._cache.items() if component_key(key)]
        self.assertEqual(len(entries), len(variants))
        for _, value in entries:
            self.assertIs(type(value.target), tuple)
            self.assertTrue(all(type(component) is F for component in value.target))

    def test_changed_type_finiteness_shape_and_large_values_keep_original_failures(self):
        class ForeignFloat(float):
            pass

        variants = ((True, 1.0, 0.0), (math.nan, 1.0, 0.0), (math.inf, 1.0, 0.0),
                    (1.0, 1.0), (1 << 40000, 1, 0), (ForeignFloat(1.0), 1.0, 0.0),
                    [1.0, 1.0, 0.0], (1, 1, 0), (F(1), F(1), F(0)))
        for index, values in enumerate(variants):
            with self.subTest(index=index):
                simulator = prepared()
                payload = simulator.model.actions["reach"].reach
                base = simulator.pose_ops.make()
                target(simulator, base, payload)
                request = replace(payload, target_m=values)
                self.assertEqual(outcome(simulator, base, request),
                                 outcome(simulator, base, request, direct=True))

    def test_missing_decoded_receipt_replays_the_original_scalar_conversion(self):
        simulator = prepared()
        payload = simulator.model.actions["reach"].reach
        base = simulator.pose_ops.make()
        first = target(simulator, base, payload)
        key, value = next((key, value) for key, value in simulator.work._cache.items() if component_key(key))
        simulator.work._cache[key] = replace(value, target=None)
        before = simulator.work.counts.get("binary64_decode", 0)
        actual = target(simulator, base, payload)
        self.assertEqual(simulator.work.counts["binary64_decode"] - before, 3)
        self.assertEqual(bits(actual.position), bits(first.position))
        self.assertIsNot(actual, first)
        self.assertEqual(simulator.work._cache[key].target, tuple(map(F, payload.target_m)))

    def test_initial_checkpoint_reads_the_current_target_before_lookup(self):
        simulator = prepared()
        original = simulator.model.actions["reach"].reach
        payload = SimpleNamespace(base_frame=original.base_frame, target_m=original.target_m)
        base = simulator.pose_ops.make()
        first = target(simulator, base, payload)
        expected_payload = replace(original, target_m=(2.0, -1.0, 0.0))
        expected = bits(ordinary(simulator, base, expected_payload))
        changed = False

        def change():
            nonlocal changed
            if not changed:
                payload.target_m = expected_payload.target_m
                changed = True

        with patch.object(simulator.work, "external_check", change):
            actual = target(simulator, base, payload)
        self.assertTrue(changed)
        self.assertEqual(bits(actual.position), expected)
        self.assertNotEqual(bits(actual.position), bits(first.position))

    def test_mutable_target_keeps_ordinary_callback_read_order(self):
        simulator = prepared()
        original = simulator.model.actions["reach"].reach
        raw = list(original.target_m)
        payload = replace(original, target_m=raw)
        base = simulator.pose_ops.make()
        target(simulator, base, original)
        original_charge = simulator.work.charge
        seen = 0

        def charge(kind="checkpoint", amount=1):
            nonlocal seen
            if kind == "pose_vector_domain":
                seen += 1
                if seen == 2:
                    raw[0] = 2.0
            return original_charge(kind, amount)

        with patch.object(simulator.work, "charge", charge):
            actual = target(simulator, base, payload)
        self.assertEqual(raw[0], 2.0)
        self.assertEqual(bits(actual.position), bits(ordinary(simulator, base, payload)))

    def test_newly_narrowed_native_admission_replays_current_domain_decodes(self):
        for during_admission in (False, True):
            with self.subTest(during_admission=during_admission):
                simulator = prepared()
                payload = simulator.model.actions["reach"].reach
                base = simulator.pose_ops.make()
                target(simulator, base, payload)
                original_charge = simulator.work.charge
                seen = 0

                def charge(kind="checkpoint", amount=1):
                    nonlocal seen
                    if kind == "pose_vector_domain":
                        seen += 1
                        if during_admission and seen == 2:
                            simulator.work.max_operand_bits = 512
                    return original_charge(kind, amount)

                if not during_admission:
                    simulator.work.max_operand_bits = 512
                with patch.object(simulator.work, "charge", charge):
                    actual = outcome(simulator, base, payload)
                expected = outcome(simulator, base, payload, direct=True)
                self.assertEqual(actual, expected)
                self.assertEqual(actual[2]["budget"], "numeric_operand_bits")
                self.assertEqual(actual[2]["consumed"], 1075)

    def test_narrow_then_widen_preserves_the_original_decode_exception(self):
        simulator = prepared()
        payload = simulator.model.actions["reach"].reach
        base = simulator.pose_ops.make()
        target(simulator, base, payload)
        simulator.work.max_operand_bits = 512
        original = reach_pose.rational
        errors = []

        def decode(value, work):
            try:
                return original(value, work)
            except ReachAdmissionError as error:
                errors.append(error)
                work.max_operand_bits = MAX_OPERAND_BITS
                raise

        with patch.object(reach_pose, "rational", decode):
            with self.assertRaises(ReachAdmissionError) as caught:
                target(simulator, base, payload)
        self.assertEqual(len(errors), 1)
        self.assertIs(caught.exception, errors[0])
        self.assertEqual(simulator.work.max_operand_bits, MAX_OPERAND_BITS)

    def test_cancelled_native_admission_preserves_completed_point_and_state(self):
        simulator = prepared()
        payload = simulator.model.actions["reach"].reach
        base = simulator.pose_ops.make()
        first = target(simulator, base, payload)
        previous = copy.deepcopy(simulator.state)
        cache = tuple(simulator.work._cache.items())
        marker = RuntimeError("cancel target input admission")
        original_charge = simulator.work.charge
        seen = 0

        def charge(kind="checkpoint", amount=1):
            nonlocal seen
            if kind == "pose_vector_domain":
                seen += 1
                if seen == 2:
                    with patch.object(simulator.work, "external_check", side_effect=marker):
                        return original_charge(kind, amount)
            return original_charge(kind, amount)

        with patch.object(simulator.work, "charge", charge):
            with self.assertRaises(RuntimeError) as caught:
                target(simulator, base, payload)
        self.assertIs(caught.exception, marker)
        self.assertIs(simulator.work.callback_error, marker)
        self.assertEqual(simulator.state, previous)
        self.assertEqual(tuple(simulator.work._cache.items()), cache)
        self.assertIs(target(simulator, base, payload), first)


if __name__ == "__main__":
    unittest.main()
