"""Per-occurrence certificate proofs keep actual claims and exact fallbacks."""
from contextlib import nullcontext
from copy import deepcopy
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.reach_reference import ReachReference
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_conformance import algebra_record
from test_reach_recurring_endpoint_claims import replace_document
from test_reach_reference_source_batch import prefix


WIDTH = F(1, 128)
MINIMUM_NAMES = (
    "landmark_radius_m", "local_vertex_error_bound_m", "angular_speed_bound_rad_per_s",
    "carrier_acceleration_bound_m_per_s2", "enclosing_carrier_speed_bound_m_per_s",
    "enclosing_carrier_acceleration_bound_m_per_s2", "enclosing_angular_speed_bound_rad_per_s",
    "max_endpoint_time_shift_s", "max_endpoint_position_error_m",
    "max_endpoint_unit_quaternion_error", "stored_quaternion_arc_upper_rad",
    "source_numeric_position_bound_m", "source_numeric_rotation_bound_rad",
)
NAME = "max_endpoint_position_error_m"


def exact_maxima():
    """Select the retained exact maximum, without changing any other proof."""
    return patch.object(reader._CertificateThresholds, "sufficient", return_value=False)


def batch(check=None, *, cap=32768):
    work = Work(check=check, max_operand_bits=cap)
    arithmetic = reader._Bounds(work)
    return reader._CertificateBatch(arithmetic, .001, .001), work


def group_of(batch):
    return next(iter(batch.groups.values()))


class CertificateThresholdTests(unittest.TestCase):
    def assert_independent_error(self, caught):
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-INDEPENDENT-VALIDATION")

    def test_all_actual_minimum_fields_discharge_fresh_values_with_identical_totals(self):
        record = algebra_record()
        outcomes = []
        for enabled in (False, True):
            current, work = batch()
            with nullcontext() if enabled else exact_maxima():
                for divisor in (16, 8, 4):
                    current.add(record, WIDTH, WIDTH,
                                {name: F(record[name]) / divisor for name in MINIMUM_NAMES}, F(0))
                retained = dict(group_of(current)["minima"])
                current.flush()
            outcomes.append((current.max_position, current.max_rotation, dict(work.counts), retained))
            self.assertEqual(work.max_operations, 100000)
            self.assertEqual(work.operations, sum(work.counts.values()))
            self.assertEqual(len(current.groups), 0)
        self.assertEqual(outcomes[0][:2], outcomes[1][:2])
        self.assertEqual(outcomes[0][2]["independent_certificate_member"], 3)
        self.assertEqual(outcomes[0][2]["independent_exact_compare"] - outcomes[1][2]["independent_exact_compare"],
                         2 * len(MINIMUM_NAMES))
        for name in MINIMUM_NAMES:
            self.assertEqual(outcomes[0][3][name], F(record[name]) / 4)
            self.assertEqual(outcomes[1][3][name], F(record[name]) / 16)

    def test_exponent_boundary_uses_a_strict_sufficient_inequality(self):
        name = "landmark_radius_m"
        for claim, minimum, proved in ((2., F(0), True), (2., F(1, 3), True),
                (2., F(3, 2), True), (2., 2 - F(1, 1 << 100), True),
                (2., F(2), False), (2., 2 + F(1, 1 << 100), False),
                (1.5, F(7, 8), True), (1.5, F(7, 5), False), (0., F(0), False),
                (2., F(-1, 8), False)):
            with self.subTest(claim=claim, minimum=minimum):
                record = {**algebra_record(), name: claim}
                current, work = batch()
                current.add(record, WIDTH, WIDTH, {name: F(1, 32)}, F(0))
                before = work.counts.get("independent_exact_compare", 0)
                current.add(record, WIDTH, WIDTH, {name: minimum}, F(0))
                self.assertEqual(work.counts.get("independent_exact_compare", 0) - before, int(not proved))
                self.assertEqual(group_of(current)["thresholds"].used, proved)

    def test_equal_repeated_minimum_keeps_the_existing_zero_comparison_path(self):
        current, work = batch()
        record, minimum = algebra_record(), F(1, 1 << 40)
        for _ in range(4):
            current.add(record, WIDTH, WIDTH, {NAME: minimum}, F(0))
        self.assertEqual(work.counts.get("independent_exact_compare", 0), 0)
        self.assertFalse(group_of(current)["thresholds"].used)
        current.flush()

    def test_late_underreported_minimum_cannot_be_covered_by_earlier_sufficient_members(self):
        record = algebra_record()
        for name in MINIMUM_NAMES:
            with self.subTest(quantity=name):
                current, _ = batch()
                for minimum in (F(record[name]) / 16, F(record[name]) / 8,
                                F(record[name]) + F(1, 1 << 180)):
                    current.add(record, WIDTH, WIDTH, {name: minimum}, F(0))
                self.assertTrue(group_of(current)["thresholds"].used)
                with self.assertRaises(OntoKinError) as caught:
                    current.flush()
                self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-CERTIFICATE")
                self.assertEqual(caught.exception.diagnostic.details["quantity"], name)

    def test_widths_and_magnitude_always_retain_the_exact_maximum(self):
        record = algebra_record()
        for field, value in (("width", F(1, 64)), ("stored_width", F(1, 64)), ("magnitude", F(3, 2))):
            with self.subTest(field=field):
                current, work = batch()
                current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
                arguments = {"width": WIDTH, "stored_width": WIDTH, "magnitude": F(0)}
                arguments[field] = value
                before = work.counts.get("independent_exact_compare", 0)
                current.add(record, minima={NAME: F(record[NAME]) / 8}, **arguments)
                self.assertEqual(group_of(current)[field], value)
                self.assertEqual(work.counts.get("independent_exact_compare", 0) - before, 1)
        for widths, magnitude in (((F(1), WIDTH), F(0)), ((WIDTH, F(1)), F(0)),
                                  ((WIDTH, WIDTH), F(1 << 401))):
            current, _ = batch()
            current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
            current.add(record, *widths, {NAME: F(record[NAME]) / 8}, magnitude)
            with self.assertRaises(OntoKinError):
                current.flush()

    def test_sixty_four_group_limit_and_complete_results_are_unchanged(self):
        current, work = batch()
        record = algebra_record()
        for index in range(70):
            changed = {**record, "max_endpoint_time_shift_s": record["max_endpoint_time_shift_s"] * index / 70}
            for divisor in (16, 8):
                current.add(changed, WIDTH, WIDTH, {NAME: F(record[NAME]) / divisor}, F(0))
            self.assertLessEqual(len(current.groups), 64)
        current.flush()
        self.assertEqual(work.counts["independent_certificate_member"], 140)
        self.assertEqual(work.counts["independent_certificate_group_check"], 70)
        self.assertEqual(current.max_position, F(record["total_position_bound_m"]))
        self.assertEqual(current.max_rotation, F(record["total_rotation_bound_rad"]))
        self.assertEqual(len(work._cache), 0)

    def test_wide_or_nonnative_fresh_minimum_keeps_the_original_comparison(self):
        record = algebra_record()
        class NativeSubclass(F):
            pass
        for minimum in (F(1, 1 << 2048), NativeSubclass(1, 1 << 40)):
            current, work = batch()
            current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
            before = work.counts.get("independent_exact_compare", 0)
            current.add(record, WIDTH, WIDTH, {NAME: minimum}, F(0))
            self.assertEqual(work.counts.get("independent_exact_compare", 0) - before, 1)
            self.assertFalse(group_of(current)["thresholds"].used)

    def test_wide_retained_operand_keeps_the_full_prospective_original_failure(self):
        current, work = batch()
        record = algebra_record()
        name = "landmark_radius_m"
        current.add(record, WIDTH, WIDTH, {name: F(0)}, F(0))
        old = F((1 << 32700) + 1, 1 << 32702)
        current.add(record, WIDTH, WIDTH, {name: old}, F(0))
        fresh = F((1 << 100) + 1, 1 << 103)
        self.assertLess(max(old.numerator.bit_length(), old.denominator.bit_length()), 32768)
        self.assertLess(max(fresh.numerator.bit_length(), fresh.denominator.bit_length()), 32768)
        with self.assertRaises(ReachAdmissionError) as caught:
            current.add(record, WIDTH, WIDTH, {name: fresh}, F(0))
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(work.max_operand_bits, 32768)

    def test_narrow_initial_domain_keeps_exact_comparison(self):
        current, work = batch(cap=1024)
        record = algebra_record()
        for divisor in (16, 8):
            current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / divisor}, F(0))
        self.assertEqual(work.counts.get("independent_exact_compare", 0), 1)
        self.assertNotIn("thresholds", group_of(current))
        current.flush()

    def test_wide_later_member_keeps_discarded_original_maximum_domain(self):
        current, work = batch()
        record, name = {**algebra_record(), "landmark_radius_m": 1.}, "landmark_radius_m"
        current.add(record, WIDTH, WIDTH, {name: F(0)}, F(0))
        omitted = F((1 << 2046) + 1, (1 << 2047) + 1)
        current.add(record, WIDTH, WIDTH, {name: omitted}, F(0))
        self.assertEqual(group_of(current)["minima"][name], 0)
        self.assertTrue(group_of(current)["thresholds"].used)
        fresh = F(1, (1 << 32766) + 1)
        self.assertLessEqual(1 + fresh.denominator.bit_length(), 32768)
        self.assertGreater(omitted.numerator.bit_length() + fresh.denominator.bit_length(), 32768)
        with self.assertRaises(ReachAdmissionError) as caught:
            current.add(record, WIDTH, WIDTH, {name: fresh}, F(0))
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(work.max_operand_bits, 32768)

    def test_determinate_product_failure_preserves_its_original_callback_exception(self):
        state = {"armed": False, "calls": 0}
        marker = RuntimeError("original callback before prospective guard")
        def check():
            if state["armed"]:
                state["calls"] += 1
                if state["calls"] == 2:
                    raise marker
        current, work = batch(check)
        record, name = {**algebra_record(), "landmark_radius_m": 1.}, "landmark_radius_m"
        current.add(record, WIDTH, WIDTH, {name: F(0)}, F(0))
        current.add(record, WIDTH, WIDTH, {name: F((1 << 2046) + 1, (1 << 2047) + 1)}, F(0))
        state["armed"] = True
        with self.assertRaises(RuntimeError) as caught:
            current.add(record, WIDTH, WIDTH, {name: F(1, (1 << 32766) + 1)}, F(0))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(state["calls"], 2)
        self.assertFalse(current.restart_requested)

    def test_continuation_cap_narrowing_cannot_use_smaller_retained_operand(self):
        state = {"armed": False, "calls": 0}
        def check():
            if state["armed"]:
                state["calls"] += 1
                if state["calls"] == 2:
                    work.max_operand_bits = 500
                elif state["calls"] == 3:
                    work.max_operand_bits = 32768
        current, work = batch(check)
        record, name = {**algebra_record(), "landmark_radius_m": 1.}, "landmark_radius_m"
        current.add(record, WIDTH, WIDTH, {name: F(0)}, F(0))
        current.add(record, WIDTH, WIDTH, {name: F((1 << 510) + 1, (1 << 511) + 1)}, F(0))
        state["armed"] = True
        # This value must exceed the claim so the exact comparison executes
        # the callback that narrows the cap. The earlier below-claim fixture
        # was legitimately discharged before reaching that callback.
        fresh = F((1 << 400) + 1, 1 << 400)
        with self.assertRaises(ReachAdmissionError) as caught:
            current.add(record, WIDTH, WIDTH, {name: fresh}, F(0))
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["consumed"], 913)
        self.assertEqual(state["calls"], 2)

    def test_final_flush_retains_discarded_operand_domain_under_narrowing(self):
        state = {"armed": False, "calls": 0}
        def check():
            if state["armed"]:
                state["calls"] += 1
                work.max_operand_bits = 100 if state["calls"] == 1 else 32768
        current, work = batch(check)
        record, name = {**algebra_record(), "landmark_radius_m": 1.}, "landmark_radius_m"
        current.add(record, WIDTH, WIDTH, {name: F(0)}, F(0))
        current.add(record, WIDTH, WIDTH, {name: F((1 << 510) + 1, (1 << 511) + 1)}, F(0))
        state["armed"] = True
        with self.assertRaises(ReachAdmissionError) as caught:
            current.flush()
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(state["calls"], 1)

    def test_inconclusive_envelope_requests_owned_replay_instead_of_new_rejection(self):
        current, _ = batch()
        record, name = {**algebra_record(), "landmark_radius_m": 1.}, "landmark_radius_m"
        current.add(record, WIDTH, WIDTH, {name: F(1, 2)}, F(0))
        # The discarded value has much wider fields, but is below the exact
        # original maximum. Its conservative width envelope cannot reject the
        # later input; complete exact replay must decide it.
        small_wide = F((1 << 1946) + 1, (1 << 2047) + 1)
        current.add(record, WIDTH, WIDTH, {name: small_wide}, F(0))
        fresh = F(1, (1 << 32766) + 1)
        with self.assertRaises(reader._CertificateThresholdRestart) as caught:
            current.add(record, WIDTH, WIDTH, {name: fresh}, F(0))
        self.assertIs(caught.exception, current.restart)
        self.assertTrue(current.restart_requested)
        exact, _ = batch()
        with exact_maxima():
            for minimum in (F(1, 2), small_wide, fresh):
                exact.add(record, WIDTH, WIDTH, {name: minimum}, F(0))
            exact.flush()
        self.assertEqual(exact.max_position, F(record["total_position_bound_m"]))

    def test_repeated_discarded_value_preserves_original_equality_under_narrowing(self):
        name, record = "landmark_radius_m", algebra_record()
        repeated = F((1 << 510) + 1, (1 << 511) + 1)
        for enabled in (False, True):
            state = {"armed": False}
            def check():
                if state["armed"]:
                    state["armed"] = False
                    work.max_operand_bits = 600
            current, work = batch(check)
            with nullcontext() if enabled else exact_maxima():
                current.add(record, WIDTH, WIDTH, {name: F(0)}, F(0))
                current.add(record, WIDTH, WIDTH, {name: repeated}, F(0))
                state["armed"] = True
                if enabled:
                    with self.assertRaises(reader._CertificateThresholdRestart) as caught:
                        current.add(record, WIDTH, WIDTH, {name: repeated}, F(0))
                    self.assertIs(caught.exception, current.restart)
                    self.assertTrue(current.restart_requested)
                else:
                    before = work.counts.get("independent_exact_compare", 0)
                    current.add(record, WIDTH, WIDTH, {name: repeated}, F(0))
                    self.assertEqual(work.counts.get("independent_exact_compare", 0), before)
                    work.max_operand_bits = 32768
                    current.flush()

    def test_narrow_then_restore_during_existing_width_checks_cannot_revive_shortcut(self):
        state = {"armed": False, "calls": 0}
        def check():
            if state["armed"]:
                state["calls"] += 1
                if state["calls"] == 1:
                    work.max_operand_bits = 1024
                elif state["calls"] == 2:
                    work.max_operand_bits = 32768
        current, work = batch(check)
        record = algebra_record()
        current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
        state["armed"] = True
        before = work.counts.get("independent_exact_compare", 0)
        current.add(record, WIDTH * 2, WIDTH, {NAME: F(record[NAME]) / 8}, F(0))
        self.assertEqual(work.counts.get("independent_exact_compare", 0) - before, 2)
        self.assertFalse(group_of(current)["thresholds"].used)
        self.assertEqual(work.max_operand_bits, 32768)

    def test_original_comparison_prospective_failure_precedes_any_restoring_callback(self):
        state = {"armed": False, "calls": 0}
        def check():
            if state["armed"]:
                state["calls"] += 1
                if state["calls"] == 2:
                    work.max_operand_bits = 2000
                elif state["calls"] == 3:
                    work.max_operand_bits = 32768
        current, work = batch(check)
        record, name = algebra_record(), "landmark_radius_m"
        old = F((1 << 1500) + 1, 1 << 1600)
        fresh = F((1 << 1501) + 1, (1 << 1602) + 3)
        current.add(record, WIDTH, WIDTH, {name: old}, F(0))
        state["armed"] = True
        # Force the original exact maximum so its own resource ordering is
        # exercised. The optional threshold otherwise legitimately omits it.
        with exact_maxima(), self.assertRaises(ReachAdmissionError) as caught:
            current.add(record, WIDTH, WIDTH, {name: fresh}, F(0))
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(state["calls"], 2)

    def test_every_surviving_member_callback_preserves_exact_exception_identity(self):
        record = algebra_record()
        def attempt(fail_at=None):
            state = {"armed": False, "calls": 0}
            marker = RuntimeError("original callback marker")
            def check():
                if state["armed"]:
                    state["calls"] += 1
                    if state["calls"] == fail_at:
                        raise marker
            current, work = batch(check)
            current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
            state["armed"] = True
            try:
                current.add(record, WIDTH * 2, WIDTH * 3, {NAME: F(record[NAME])}, F(1))
            except RuntimeError as error:
                self.assertIs(error, marker)
                self.assertIs(work.callback_error, marker)
                return state["calls"]
            self.assertIsNone(fail_at)
            return state["calls"]
        count = attempt()
        self.assertEqual(count, 5)
        for index in range(1, count + 1):
            with self.subTest(callback=index):
                self.assertEqual(attempt(index), index)

    def test_member_callback_cannot_rewrite_its_fresh_minimum(self):
        for field, changed in (("_numerator", True), ("_denominator", False),
                               ("_denominator", 0), ("_numerator", 1 << 3000)):
            with self.subTest(field=field, changed_type=type(changed)):
                state = {"armed": False, "calls": 0}
                fresh = F(1, 1 << 33)
                saved = getattr(fresh, field)
                def check():
                    if state["armed"]:
                        state["calls"] += 1
                        if state["calls"] == 2:
                            object.__setattr__(fresh, field, changed)
                        elif state["calls"] == 3:
                            object.__setattr__(fresh, field, saved)
                current, _ = batch(check)
                record = algebra_record()
                current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
                state["armed"] = True
                try:
                    with self.assertRaises(OntoKinError) as caught:
                        current.add(record, WIDTH * 2, WIDTH, {NAME: fresh}, F(0))
                    self.assert_independent_error(caught)
                    self.assertEqual(state["calls"], 2)
                finally:
                    object.__setattr__(fresh, field, saved)

    def test_member_callback_cannot_erase_a_retained_hostile_minimum(self):
        for field, changed in (("_numerator", 0), ("_numerator", False), ("_denominator", 0)):
            state = {"armed": False, "calls": 0}
            record = algebra_record()
            previous = F(record[NAME]) * 2
            saved = getattr(previous, field)
            def check():
                if state["armed"]:
                    state["calls"] += 1
                    if state["calls"] == 2:
                        object.__setattr__(previous, field, changed)
                    elif state["calls"] == 3:
                        object.__setattr__(previous, field, saved)
            current, _ = batch(check)
            current.add(record, WIDTH, WIDTH, {NAME: previous}, F(0))
            state["armed"] = True
            try:
                with self.subTest(field=field, changed=changed), self.assertRaises(OntoKinError) as caught:
                    current.add(record, WIDTH * 2, WIDTH, {NAME: F(record[NAME]) / 8}, F(0))
                self.assert_independent_error(caught)
                self.assertEqual(state["calls"], 2)
            finally:
                object.__setattr__(previous, field, saved)

    def test_actual_typed_row_or_native_quantity_mutation_is_not_hidden(self):
        for change in ("raw_type", "raw_value", "native_bool", "native_zero_denominator"):
            state = {"armed": False, "calls": 0}
            record = algebra_record()
            def check():
                if state["armed"]:
                    state["calls"] += 1
                    if state["calls"] == 2:
                        if change == "raw_type":
                            record["landmark_radius_m"] = 2
                        elif change == "raw_value":
                            record[NAME] = math.nextafter(record[NAME], 0.)
                        elif change == "native_bool":
                            object.__setattr__(group_of(current)["quantities"][NAME], "_numerator", True)
                        else:
                            object.__setattr__(group_of(current)["quantities"][NAME], "_denominator", 0)
            current, _ = batch(check)
            current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
            state["armed"] = True
            with self.subTest(change=change), self.assertRaises(OntoKinError) as caught:
                current.add(record, WIDTH * 2, WIDTH, {NAME: F(record[NAME]) / 8}, F(0))
            self.assert_independent_error(caught)
            self.assertEqual(state["calls"], 2)

    def test_arithmetic_or_external_callback_owner_changes_are_rejected(self):
        for change in ("arithmetic", "work", "callback"):
            state = {"armed": False, "calls": 0}
            def check():
                if state["armed"]:
                    state["calls"] += 1
                    if state["calls"] == 2:
                        if change == "arithmetic":
                            current.arithmetic = reader._Bounds(work)
                        elif change == "work":
                            current.arithmetic.work = Work()
                        else:
                            work.external_check = lambda: None
            current, work = batch(check)
            record = algebra_record()
            current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
            state["armed"] = True
            with self.subTest(change=change), self.assertRaises(OntoKinError) as caught:
                current.add(record, WIDTH * 2, WIDTH, {NAME: F(record[NAME]) / 8}, F(0))
            self.assert_independent_error(caught)

    def test_initial_foreign_dispatch_keeps_the_original_maximum_path(self):
        for owner, name in ((reader._Bounds, "compare"), (reader._Bounds, "bits"),
                            (reader._Bounds, "value"), (reader._Bounds, "tick"),
                            (reader._CertificateBatch, "maximum")):
            original = getattr(owner, name)
            calls = []
            def foreign(*args, **kwargs):
                calls.append(True)
                return original(*args, **kwargs)
            with self.subTest(operation=name), patch.object(owner, name, foreign):
                current, work = batch()
                record = algebra_record()
                for divisor in (16, 8):
                    current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / divisor}, F(0))
                self.assertNotIn("thresholds", group_of(current))
                self.assertEqual(work.counts.get("independent_exact_compare", 0), 1)
                self.assertEqual(group_of(current)["minima"][NAME], F(record[NAME]) / 8)
                current.flush()
            self.assertTrue(calls)

    def test_changed_compare_dispatch_keeps_the_original_callback_sentinel(self):
        for scope in ("instance", "class"):
            state = {"armed": False, "calls": 0}
            marker = RuntimeError("changed comparison's original callback")
            def changed_compare(*args):
                work.charge("independent_exact_compare")
                raise AssertionError("the original callback must raise")
            def check():
                if state["armed"]:
                    state["calls"] += 1
                    if state["calls"] == 2:
                        setattr(current.arithmetic if scope == "instance" else reader._Bounds,
                                "compare", changed_compare)
                    elif state["calls"] == 3:
                        raise marker
            current, work = batch(check)
            record = algebra_record()
            current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
            original = reader._Bounds.compare
            state["armed"] = True
            try:
                with self.subTest(scope=scope), self.assertRaises(RuntimeError) as caught:
                    current.add(record, WIDTH * 2, WIDTH, {NAME: F(record[NAME]) / 8}, F(0))
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(state["calls"], 3)
                self.assertFalse(group_of(current)["thresholds"].used)
            finally:
                reader._Bounds.compare = original
                current.arithmetic.__dict__.pop("compare", None)

    def test_compare_departure_then_restore_cannot_revive_group_omission(self):
        state = {"armed": False, "calls": 0}
        original = reader._Bounds.compare
        def foreign(arithmetic, *args):
            return original(arithmetic, *args)
        def check():
            if state["armed"]:
                state["calls"] += 1
                if state["calls"] == 2:
                    reader._Bounds.compare = foreign
                elif state["calls"] == 3:
                    reader._Bounds.compare = original
        current, work = batch(check)
        record = algebra_record()
        current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
        state["armed"] = True
        try:
            current.add(record, WIDTH * 2, WIDTH * 2, {NAME: F(record[NAME]) / 8}, F(0))
        finally:
            reader._Bounds.compare = original
        self.assertEqual(work.counts["independent_exact_compare"], 3)
        self.assertFalse(group_of(current)["thresholds"].enabled)
        self.assertFalse(group_of(current)["thresholds"].used)
        self.assertEqual(group_of(current)["minima"][NAME], F(record[NAME]) / 8)

    def test_retained_extent_mutation_cannot_reach_flush(self):
        for name in ("width", "stored_width", "magnitude"):
            state = {"armed": False}
            def check():
                if state["armed"]:
                    state["armed"] = False
                    object.__setattr__(operand, "_numerator", 0 if saved else 1)
            current, _ = batch(check)
            record = algebra_record()
            for divisor in (16, 8):
                current.add(record, F(1, 128), F(1, 128), {NAME: F(record[NAME]) / divisor}, F(0))
            operand = group_of(current)[name]
            saved = operand.numerator
            state["armed"] = True
            try:
                with self.subTest(field=name), self.assertRaises(OntoKinError) as caught:
                    current.flush()
                self.assert_independent_error(caught)
            finally:
                object.__setattr__(operand, "_numerator", saved)

    def test_complete_algebra_reads_detached_extents_through_transient_mutation(self):
        state = {"inside": False, "calls": 0}
        observed = []
        def check():
            if state["inside"]:
                state["calls"] += 1
                if state["calls"] == 1:
                    object.__setattr__(live, "_numerator", 0)
                    observed.append(frozen[0].numerator)
                elif state["calls"] == 2:
                    object.__setattr__(live, "_numerator", saved)
        current, _ = batch(check)
        record = algebra_record()
        for divisor in (16, 8):
            current.add(record, F(1, 128), F(1, 128), {NAME: F(record[NAME]) / divisor}, F(0))
        group = group_of(current)
        live, saved = group["width"], group["width"].numerator
        frozen = []
        original = reader._complete_inequality_values
        def complete(width, stored_width, *args, **kwargs):
            self.assertIsNot(width, group["width"])
            self.assertIsNot(stored_width, group["stored_width"])
            frozen.append(width)
            state["inside"] = True
            try:
                return original(width, stored_width, *args, **kwargs)
            finally:
                state["inside"] = False
        try:
            with patch.object(reader, "_complete_inequality_values", complete):
                current.flush()
        finally:
            object.__setattr__(live, "_numerator", saved)
        self.assertEqual(observed, [saved])
        self.assertGreaterEqual(state["calls"], 2)
        self.assertEqual(current.max_position, F(record["total_position_bound_m"]))

    def test_exact_replay_rejects_a_changed_original_tolerance(self):
        for change in ("replace", "native"):
            current, _ = batch()
            if change == "replace":
                current.position_tolerance = F(1, 10)
            else:
                object.__setattr__(current.rotation_tolerance, "_numerator", 0)
            with self.subTest(change=change), self.assertRaises(OntoKinError) as caught:
                current._prepare_exact_replay()
            self.assert_independent_error(caught)

    def test_changed_quantity_or_group_replacement_cannot_change_discharged_threshold(self):
        for change in ("native", "mapping", "flush_callback"):
            state = {"armed": False}
            def check():
                if state["armed"]:
                    state["armed"] = False
                    object.__setattr__(group_of(current)["quantities"][NAME], "_numerator", 0)
            current, _ = batch(check)
            record = algebra_record()
            for divisor in (16, 8):
                current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / divisor}, F(0))
            self.assertTrue(group_of(current)["thresholds"].used)
            if change == "native":
                object.__setattr__(group_of(current)["quantities"][NAME], "_numerator", 0)
            elif change == "mapping":
                group_of(current)["quantities"] = dict(group_of(current)["quantities"])
            else:
                state["armed"] = True
            with self.subTest(change=change), self.assertRaises(OntoKinError) as caught:
                current.flush()
            self.assert_independent_error(caught)

    def test_changed_metadata_shapes_reject_before_unbounded_walk(self):
        state = {"armed": False}
        record, minima = algebra_record(), {NAME: F(1, 1 << 33)}
        def check():
            if state["armed"]:
                state["armed"] = False
                minima.update({"unexpected" + str(index): F(0) for index in range(1000)})
        current, _ = batch(check)
        current.add(record, WIDTH, WIDTH, {NAME: F(record[NAME]) / 16}, F(0))
        state["armed"] = True
        with self.assertRaises(OntoKinError) as caught:
            current.add(record, WIDTH, WIDTH, minima, F(0))
        self.assert_independent_error(caught)

    def test_original_source_prefix_bytes_and_complete_reports_are_unchanged(self):
        savings = []
        for case in ("P09", "P11", "L03"):
            results = []
            for enabled in (False, True):
                with nullcontext() if enabled else exact_maxima():
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                results.append((result.data, result.report["validation"], compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(results[0][:2], results[1][:2])
                self.assertLessEqual(results[1][2], results[0][2])
            savings.append(results[0][2] - results[1][2])
            print(f"{case} certificate prefix: exact={results[0][2]}, thresholds={results[1][2]}")
        self.assertGreater(sum(savings), 0)

    def test_requested_exact_replay_rebuilds_real_source_prefix_on_same_work(self):
        original, first_compiler = prefix("P09")
        observed, prepared = [], []
        initialize = reader._CertificateBatch.__init__
        def initialize_and_observe(current, arithmetic, position_tolerance, rotation_tolerance, **kwargs):
            initialize(current, arithmetic, position_tolerance, rotation_tolerance, **kwargs)
            observed.append((current, arithmetic, arithmetic.work.operations,
                             current.position_tolerance, current.rotation_tolerance))
        prepare = reader._CertificateBatch._prepare_exact_replay
        def prepare_and_observe(current):
            prepared.append((current, current.arithmetic.work.operations, current.restart_requested))
            return prepare(current)
        def force_once(thresholds, *args):
            thresholds.restart()
        with patch.object(reader._CertificateBatch, "__init__", initialize_and_observe), \
             patch.object(reader._CertificateBatch, "_prepare_exact_replay", prepare_and_observe), \
             patch.object(reader._CertificateThresholds, "sufficient", force_once):
            replayed, compiler = prefix("P09")
        self.assertEqual((replayed.data, replayed.report["validation"]),
                         (original.data, original.report["validation"]))
        self.assertEqual(len(observed), 1)
        self.assertEqual(len(prepared), 1)
        self.assertTrue(prepared[0][2])
        self.assertIs(prepared[0][0], observed[0][0])
        self.assertFalse(observed[0][0].thresholds_enabled)
        self.assertIs(observed[0][0].arithmetic, observed[0][1])
        self.assertIs(observed[0][1].work, compiler.reach_work)
        self.assertIs(observed[0][0].position_tolerance, observed[0][3])
        self.assertIs(observed[0][0].rotation_tolerance, observed[0][4])
        self.assertGreater(prepared[0][1], observed[0][2])
        self.assertGreater(compiler.reach_work.operations, first_compiler.reach_work.operations)
        self.assertEqual(compiler.reach_work.max_operations, 100000)

    def test_real_prefix_replay_preserves_instance_dispatch_callback_sentinel(self):
        marker = RuntimeError("instance comparison sentinel after exact replay")
        state = {"armed": False, "raise": False, "batch": None}
        replayed = []
        def changed_compare(*args):
            state["raise"] = True
            compiler.reach_work.charge("independent_exact_compare")
            raise AssertionError("the unchanged callback must raise its sentinel")
        def check():
            if state["raise"]:
                raise marker
            if state["armed"]:
                state["armed"] = False
                state["batch"].arithmetic.compare = changed_compare
        compiler = compile_construction(source_case("P09"), check=check)
        flush = reader._CertificateBatch.flush
        def arm_flush(current):
            if state["batch"] is None:
                self.assertTrue(any(group.get("thresholds") and group["thresholds"].used
                                    for group in current.groups.values()))
                state["batch"] = current
                state["armed"] = True
            return flush(current)
        prepare = reader._CertificateBatch._prepare_exact_replay
        def observe_replay(current):
            replayed.append((current, current.arithmetic, current.position_tolerance, current.rotation_tolerance))
            return prepare(current)
        with patch.object(reader._CertificateBatch, "flush", arm_flush), \
             patch.object(reader._CertificateBatch, "_prepare_exact_replay", observe_replay):
            with self.assertRaises(RuntimeError) as caught:
                export_glb(compiler.model, options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                           target_contract="ontokin.glb/0.6", work=compiler.reach_work)
        self.assertIs(caught.exception, marker)
        self.assertIs(compiler.reach_work.callback_error, marker)
        self.assertEqual(len(replayed), 1)
        current, arithmetic, position, rotation = replayed[0]
        self.assertIs(current, state["batch"])
        self.assertIs(current.arithmetic, arithmetic)
        self.assertIs(arithmetic.work, compiler.reach_work)
        self.assertIs(arithmetic.compare, changed_compare)
        self.assertIs(current.position_tolerance, position)
        self.assertIs(current.rotation_tolerance, rotation)
        self.assertFalse(current.thresholds_enabled)

    def test_callback_lookalike_restart_exception_propagates_unchanged(self):
        marker = reader._CertificateThresholdRestart("caller-created exception")
        state = {"armed": False}
        def check():
            if state["armed"]:
                raise marker
        compiler = compile_construction(source_case("P09"), check=check)
        initialize = reader._CertificateBatch.__init__
        def initialize_and_arm(current, *args, **kwargs):
            initialize(current, *args, **kwargs)
            state["armed"] = True
        with patch.object(reader._CertificateBatch, "__init__", initialize_and_arm):
            with self.assertRaises(reader._CertificateThresholdRestart) as caught:
                export_glb(compiler.model, options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                           target_contract="ontokin.glb/0.6", work=compiler.reach_work)
        self.assertIs(caught.exception, marker)
        self.assertIs(compiler.reach_work.callback_error, marker)

    def test_callback_raising_already_requested_owned_signal_is_not_retried(self):
        state = {"marker": None}
        def check():
            if state["marker"] is not None:
                raise state["marker"]
        compiler = compile_construction(source_case("P09"), check=check)
        attempts = []
        def arm_and_request(thresholds, *args):
            attempts.append(True)
            state["marker"] = thresholds.restart.__self__.restart
            thresholds.restart()
        with patch.object(reader._CertificateThresholds, "sufficient", arm_and_request):
            with self.assertRaises(reader._CertificateThresholdRestart) as caught:
                export_glb(compiler.model, options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                           target_contract="ontokin.glb/0.6", work=compiler.reach_work)
        self.assertIs(caught.exception, state["marker"])
        self.assertIs(compiler.reach_work.callback_error, state["marker"])
        self.assertEqual(attempts, [True])

    def test_requested_replay_admits_the_abandoned_original_source_ledger(self):
        owners, attempts = [], []
        capture = ReachReference.recording_source_batch
        def capture_reference(reference, context):
            owners.append(reference)
            return capture(reference, context)
        def change_source_and_request(thresholds, *args):
            attempts.append(True)
            reference = owners[-1]
            state = reference._state_at(F(1, 8), "after")
            state.ideal_positions["rig"] = reference.p.vector((1, 0, 0))
            thresholds.restart()
        with patch.object(ReachReference, "recording_source_batch", capture_reference), \
             patch.object(reader._CertificateThresholds, "sufficient", change_source_and_request):
            with self.assertRaises(OntoKinError) as caught:
                prefix("P09")
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-INDEPENDENT-VALIDATION")
        self.assertEqual(caught.exception.diagnostic.details["reference_code"], "identity")
        self.assertEqual(attempts, [True])
        self.assertEqual(len(owners), 1)
        self.assertIsNone(owners[0]._recording_batch)

    def test_forged_actual_late_certificate_still_fails_with_current_reader(self):
        compiler = compile_construction(source_case("P09"))
        options = ExportOptions(end=F(1, 4), fps=4, helpers=False)
        observed, original_add = [], reader._CertificateBatch.add
        def observe(current, record, width, stored_width, minima, magnitude):
            observed.append((record["left_key_index"], deepcopy(record["carrier"]), minima["landmark_radius_m"]))
            return original_add(current, record, width, stored_width, minima, magnitude)
        with patch.object(reader._CertificateBatch, "add", observe):
            result = export_glb(compiler.model, options=options, target_contract="ontokin.glb/0.6",
                                work=compiler.reach_work)
        decoded = read_glb(result.data, target_contract="ontokin.glb/0.6")
        candidates = [item for item in observed if item[0] > 0 and item[2] > 0]
        self.assertTrue(candidates)
        selected, identity, minimum = candidates[-1]
        document = deepcopy(decoded.document)
        rows = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
        changed = [row for row in rows if row["left_key_index"] == selected and row["carrier"] == identity]
        self.assertEqual(len(changed), 1)
        changed[0]["landmark_radius_m"] = math.nextafter(float(minimum), 0.)
        self.assertLess(F(changed[0]["landmark_radius_m"]), minimum)
        forged = replace_document(document, decoded.binary)
        self.assertEqual(read_glb(forged, target_contract="ontokin.glb/0.6").binary, decoded.binary)
        with self.assertRaises(OntoKinError) as caught:
            reader.validate_reach_export(forged, compiler.model, options=options, work=Work())
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-CERTIFICATE")
        self.assertEqual(caught.exception.diagnostic.details["quantity"], "landmark_radius_m")


if __name__ == "__main__":
    unittest.main()
