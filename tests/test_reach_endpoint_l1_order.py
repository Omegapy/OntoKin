"""Farthest source endpoints retain actual operands, callbacks and width guards."""
from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


def points(values):
    return tuple(reader._Cell(F(value), F(value)) for value in values)


def ordinary_l1(actual, expected, arithmetic, *, admitted_cells=False):
    """The preceding complete endpoint kernel, including original admission."""
    arithmetic.tick("independent_sufficient_endpoint_domain")
    if len(actual) != len(expected) or len(actual) not in (3, 4):
        reader._error("OKE-E-CERTIFICATE", "An independent vector comparison has incompatible dimensions.")
    if reader._bound_domain(arithmetic) != reader.MAX_OPERAND_BITS:
        return None
    actual = tuple(F(0) if type(value) in (int, float, F) and value == 0
                   else arithmetic.value(value) for value in actual)
    if (admitted_cells and type(expected) is tuple
            and all(type(cell) is reader._Cell and type(cell.lo) is F
                    and type(cell.hi) is F for cell in expected)):
        arithmetic._cache_operand_domain(expected)
        for cell in expected:
            if cell.lo > cell.hi:
                reader._error("OKE-E-INDEPENDENT-VALIDATION", "An independent reference returned a reversed enclosure.")
    else:
        expected = arithmetic.cells(expected)
    if (reader._bound_domain(arithmetic) != reader.MAX_OPERAND_BITS
            or not reader._small_proof_values((*actual, *(value for cell in expected for value in (cell.lo, cell.hi))))):
        return None
    result = F(0)
    for value, cell in zip(actual, expected):
        if cell.lo == cell.hi:
            error = F(0) if value == cell.lo else abs(arithmetic.sub(value, cell.lo))
        else:
            first, last = abs(arithmetic.sub(value, cell.lo)), abs(arithmetic.sub(value, cell.hi))
            error = first if arithmetic.compare(first, last) >= 0 else last
        if error:
            result = arithmetic.add(result, error) if result else error
    return result


@contextmanager
def ordinary_endpoints():
    with patch.object(reader, "_optional_endpoint_l1", ordinary_l1), \
            patch.object(reader, "_ENDPOINT_TWO", 2):
        yield


def outcome(calculate):
    try:
        return ("value", calculate())
    except ReachAdmissionError as error:
        return ("resource", error.details)
    except OntoKinError as error:
        return ("diagnostic", error.diagnostic)


class IndependentEndpointL1OrderTests(unittest.TestCase):
    def test_exact_l1_for_outside_inside_and_boundary_operands(self):
        cases = (
            ((4, -4, 0), ((1, 2), (-2, -1), (-1, 1)), 2),
            ((1, 2, -2), ((1, 2), (1, 2), (-2, -1)), 3),
            ((0., -0., 0), ((0, 1), (-1, 0), (-1, 1)), 2),
            ((F(1, 3), F(-5, 7), F(2, 9)), ((0, 1), (-2, -1), (0, F(1, 9))), 2),
            ((0, 0, 0, 1), ((-1, 1), (-1, 0), (0, 1), (1, 2)), 3),
            ((1, -2, 3), ((1, 1), (-2, -2), (3, 3)), 0),
        )
        for actual, intervals, removed in cases:
            expected = tuple(reader._Cell(F(low), F(high)) for low, high in intervals)
            results, counts = [], []
            for kernel in (ordinary_l1, reader._optional_endpoint_l1):
                work = Work()
                results.append(kernel(actual, expected, reader._Bounds(work)))
                counts.append(work.counts)
                self.assertEqual(work.operations, sum(work.counts.values()))
                self.assertEqual(work.max_operations, 100000)
                self.assertFalse(work._cache)
            with self.subTest(actual=actual, intervals=intervals):
                self.assertEqual(results[0], results[1])
                self.assertEqual(results[1], sum(max(abs(F(value) - low), abs(F(value) - high))
                                                for value, (low, high) in zip(actual, intervals)))
                self.assertEqual(counts[0].get("independent_exact_compare", 0) -
                                 counts[1].get("independent_exact_compare", 0), removed)
                self.assertEqual({key: value for key, value in counts[0].items()
                                  if key != "independent_exact_compare"},
                                 {key: value for key, value in counts[1].items()
                                  if key != "independent_exact_compare"})

    def test_inside_cell_keeps_the_original_comparison_callback(self):
        work = Work()
        charge = work.charge
        marker = RuntimeError("cancel the required inside-cell comparison")
        def cancel(kind="checkpoint", amount=1):
            if kind == "independent_exact_compare":
                work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(work, "charge", cancel), self.assertRaises(RuntimeError) as caught:
            reader._optional_endpoint_l1((0, 0, 0),
                (reader._Cell(F(-1), F(1)), *points((0, 0))), reader._Bounds(work))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertFalse(work._cache)

    def test_original_comparison_operand_and_cross_width_preflights_remain(self):
        actual = (F(5, 7), 0, 0)
        expected = (reader._Cell(-F((1 << 254) - 1, (1 << 255) - 1),
                                 F(1, (1 << 255) - 1)), *points((0, 0)))
        results, guards, counts = [], [], []
        for kernel in (ordinary_l1, reader._optional_endpoint_l1):
            work, arithmetic = Work(), reader._Bounds()
            arithmetic.work = work
            with patch.object(arithmetic, "bits", wraps=arithmetic.bits) as bits:
                results.append(kernel(actual, expected, arithmetic, admitted_cells=True))
            guards.append([call.args for call in bits.call_args_list])
            counts.append(work.counts)
        self.assertEqual(results[0], results[1])
        self.assertEqual(guards[0], guards[1])
        self.assertEqual(counts[0]["independent_exact_compare"], 1)
        self.assertNotIn("independent_exact_compare", counts[1])
        self.assertGreater(max(max(args) for args in guards[1]), 500)

    def test_live_narrowing_keeps_the_original_cross_width_failure(self):
        outcomes, counts = [], []
        for kernel in (ordinary_l1, reader._optional_endpoint_l1):
            actual = (F(5, 7), 0, 0)
            expected = (reader._Cell(-F((1 << 254) - 1, (1 << 255) - 1),
                                     F(1, (1 << 255) - 1)), *points((0, 0)))
            work, seen = Work(), 0
            charge = work.charge
            def narrow(kind="checkpoint", amount=1):
                nonlocal seen
                if kind == "independent_exact_sub":
                    seen += 1
                    if seen == 2:
                        work.max_operand_bits = 300
                return charge(kind, amount)
            with patch.object(work, "charge", narrow):
                outcomes.append(outcome(lambda: kernel(actual, expected, reader._Bounds(work), admitted_cells=True)))
            counts.append(work.counts)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[1][0], "resource")
        self.assertEqual(outcomes[1][1]["budget"], "numeric_operand_bits")
        self.assertGreater(outcomes[1][1]["consumed"], 300)
        self.assertEqual(counts[0], counts[1])

    def test_narrowed_foreign_or_restored_domains_use_the_ordinary_comparison(self):
        for change in ("first", "last", "restored", "foreign"):
            results, counts = [], []
            for kernel in (ordinary_l1, reader._optional_endpoint_l1):
                work, seen = Work(), 0
                charge = work.charge
                def change_cap(kind="checkpoint", amount=1):
                    nonlocal seen
                    if kind == "independent_exact_sub":
                        seen += 1
                        if ((seen == 1 and change in ("first", "restored"))
                                or (seen == 2 and change == "last")):
                            work.max_operand_bits = 128
                        if seen == 1 and change == "foreign":
                            work.max_operand_bits = float(reader.MAX_OPERAND_BITS)
                        if seen == 2 and change == "restored":
                            work.max_operand_bits = reader.MAX_OPERAND_BITS
                    return charge(kind, amount)
                with patch.object(work, "charge", change_cap):
                    results.append(kernel((2, 0, 0),
                        (reader._Cell(F(0), F(1)), *points((0, 0))), reader._Bounds(work)))
                counts.append(work.counts)
            with self.subTest(change=change):
                self.assertEqual(results, [F(2), F(2)])
                self.assertEqual(counts[0], counts[1])
                self.assertEqual(counts[1]["independent_exact_compare"], 1)

    def test_callback_source_replacement_and_fraction_mutation_use_actual_operands(self):
        for change in ("high_before_first", "high_during_last", "low_during_last"):
            results, counts = [], []
            for kernel in (ordinary_l1, reader._optional_endpoint_l1):
                source = reader._Cell(F(0), F(2))
                work, seen = Work(), 0
                charge = work.charge
                def mutate(kind="checkpoint", amount=1):
                    nonlocal seen
                    if kind == "independent_exact_sub":
                        seen += 1
                        if seen == 1 and change == "high_before_first":
                            object.__setattr__(source, "hi", F(-4))
                        if seen == 2 and change == "high_during_last":
                            object.__setattr__(source.hi, "_numerator", -4)
                        if seen == 2 and change == "low_during_last":
                            object.__setattr__(source, "lo", F(5))
                    return charge(kind, amount)
                with patch.object(work, "charge", mutate):
                    results.append(kernel((1, 0, 0), (source, *points((0, 0))),
                                          reader._Bounds(work), admitted_cells=True))
                counts.append(work.counts)
            with self.subTest(change=change):
                self.assertEqual(results[0], results[1])
                self.assertEqual(results[1], 1 if change == "low_during_last" else 5)
                self.assertEqual(counts[0], counts[1])
                self.assertEqual(counts[1]["independent_exact_compare"], 1)

    def test_callback_actual_fraction_mutation_preserves_the_first_absolute_value(self):
        results, counts = [], []
        for kernel in (ordinary_l1, reader._optional_endpoint_l1):
            work, arithmetic, seen, decoded = Work(), reader._Bounds(), 0, []
            arithmetic.work = work
            charge, decode = work.charge, arithmetic.value
            def remember(value):
                result = decode(value)
                decoded.append(result)
                return result
            def mutate(kind="checkpoint", amount=1):
                nonlocal seen
                if kind == "independent_exact_sub":
                    seen += 1
                    if seen == 2:
                        object.__setattr__(decoded[0], "_numerator", 6)
                return charge(kind, amount)
            with patch.object(work, "charge", mutate), patch.object(arithmetic, "value", remember):
                results.append(kernel((1, 0, 0),
                    (reader._Cell(F(0), F(2)), *points((0, 0))), arithmetic, admitted_cells=True))
            counts.append(work.counts)
        self.assertEqual(results, [F(4), F(4)])
        self.assertEqual(counts[0], counts[1])
        self.assertEqual(counts[1]["independent_exact_compare"], 1)

    def test_earlier_callback_cannot_replace_a_later_component_order_proof(self):
        results, counts = [], []
        for kernel in (ordinary_l1, reader._optional_endpoint_l1):
            expected = (reader._Cell(F(0), F(1)), reader._Cell(F(0), F(2)), *points((0,)))
            work, seen = Work(), 0
            charge = work.charge
            def mutate(kind="checkpoint", amount=1):
                nonlocal seen
                if kind == "independent_exact_sub":
                    seen += 1
                    if seen == 1:
                        object.__setattr__(expected[1], "hi", F(-4))
                return charge(kind, amount)
            with patch.object(work, "charge", mutate):
                results.append(kernel((2, 1, 0), expected, reader._Bounds(work), admitted_cells=True))
            counts.append(work.counts)
        self.assertEqual(results, [F(7), F(7)])
        self.assertEqual(counts[0]["independent_exact_compare"], 2)
        self.assertEqual(counts[1]["independent_exact_compare"], 1)

    def test_changed_work_owner_keeps_the_comparison_in_the_current_domain(self):
        for kernel in (ordinary_l1, reader._optional_endpoint_l1):
            first, last = Work(), Work()
            arithmetic = reader._Bounds(first)
            charge = first.charge
            def transfer(kind="checkpoint", amount=1):
                if kind == "independent_exact_sub":
                    arithmetic.work = last
                return charge(kind, amount)
            with patch.object(first, "charge", transfer):
                result = kernel((2, 0, 0),
                    (reader._Cell(F(0), F(1)), *points((0, 0))), arithmetic, admitted_cells=True)
            self.assertEqual(result, F(2))
            self.assertEqual(last.counts["independent_exact_compare"], 1)
            self.assertFalse(first._cache)
            self.assertFalse(last._cache)

    def test_each_retained_subtraction_preserves_cancellation_identity_and_cache(self):
        for stop in (1, 2):
            for kernel in (ordinary_l1, reader._optional_endpoint_l1):
                work, seen = Work(), 0
                work.remember(("unrelated",), (F(7),))
                cache = deepcopy(work._cache)
                marker = RuntimeError("cancel actual endpoint subtraction")
                charge = work.charge
                def cancel(kind="checkpoint", amount=1):
                    nonlocal seen
                    if kind == "independent_exact_sub":
                        seen += 1
                        if seen == stop:
                            work.external_check = lambda: (_ for _ in ()).throw(marker)
                    return charge(kind, amount)
                with self.subTest(stop=stop, kernel=kernel.__name__), patch.object(work, "charge", cancel), \
                        self.assertRaises(RuntimeError) as caught:
                    kernel((2, 0, 0), (reader._Cell(F(0), F(1)), *points((0, 0))),
                           reader._Bounds(work), admitted_cells=True)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(work._cache, cache)

    def test_malformed_reversed_large_and_initially_narrow_domains_match(self):
        class ForeignCell(reader._Cell):
            pass
        examples = (
            ((False, 0, 0), points((0, 0, 0)), 32768),
            ((float("nan"), 0, 0), points((0, 0, 0)), 32768),
            ((float("inf"), 0, 0), points((0, 0, 0)), 32768),
            ((0, 0, 0), (reader._Cell(F(2), F(1)), *points((0, 0))), 32768),
            ((0, 0, 0), points((1 << 32768, 0, 0)), 32768),
            ((1 << 256, 0, 0), points((0, 0, 0)), 32768),
            ((2, 0, 0), (ForeignCell(F(0), F(1)), *points((0, 0))), 32768),
            ((2, 0, 0), (reader._Cell(0, 1), *points((0, 0))), 32768),
            ((2, 0, 0), points((0, 0, 0)), 128),
            ((2, 0), points((0, 0, 0)), 32768),
        )
        for actual, expected, cap in examples:
            results, counts = [], []
            for kernel in (ordinary_l1, reader._optional_endpoint_l1):
                work = Work(max_operand_bits=cap)
                results.append(outcome(lambda: kernel(actual, expected, reader._Bounds(work))))
                counts.append(work.counts)
            with self.subTest(actual=actual, cap=cap, cell_type=type(expected[0])):
                self.assertEqual(results[0], results[1])
                if type(expected[0]) is ForeignCell or results[0][0] != "value" or results[0][1] is None:
                    self.assertEqual(counts[0], counts[1])

    def test_factor_two_reuses_only_the_full_native_domain_constant(self):
        for cap in (32768, 128):
            results, counts = [], []
            for ordinary in (True, False):
                work = Work(max_operand_bits=cap)
                arithmetic = reader._Bounds(work)
                calculate = lambda: reader._recording_orientation_bound(
                    (0., 0., 0., 1.), points((0, 0, 0, 1)), 1e-5, arithmetic)
                if ordinary:
                    with ordinary_endpoints():
                        results.append(outcome(calculate))
                else:
                    results.append(outcome(calculate))
                counts.append(work.counts)
            with self.subTest(cap=cap):
                self.assertEqual(results[0], results[1])
                if cap == 32768:
                    self.assertEqual(counts[0]["independent_bound_decode"] -
                                     counts[1]["independent_bound_decode"], 1)
                else:
                    self.assertEqual(results[0][0], "resource")
                    self.assertEqual(counts[0], counts[1])

    def test_mul_callback_cannot_mutate_the_factor_through_the_global_fraction(self):
        for replacement in (0, -2, 1 << 32768):
            results, counts = [], []
            for ordinary in (True, False):
                constant = F(2)
                work = Work()
                charge = work.charge
                def mutate(kind="checkpoint", amount=1):
                    if kind == "independent_exact_mul":
                        object.__setattr__(constant, "_numerator", replacement)
                    return charge(kind, amount)
                calculate = lambda: reader._recording_orientation_bound(
                    (0., 0., 0., 1. + 2. ** -24), points((0, 0, 0, 1)), 1e-5, reader._Bounds(work))
                with patch.object(reader, "_ENDPOINT_TWO", constant), patch.object(work, "charge", mutate):
                    if ordinary:
                        with ordinary_endpoints():
                            results.append(calculate())
                    else:
                        results.append(calculate())
                counts.append(work.counts)
            with self.subTest(replacement_bits=replacement.bit_length(), replacement_sign=replacement < 0):
                self.assertEqual(results, [(None, F(1, 1 << 23))] * 2)
                self.assertEqual(counts[0]["independent_bound_decode"] -
                                 counts[1]["independent_bound_decode"], 1)

    def test_altered_constant_takes_the_original_integer_decoder(self):
        class ForeignFraction(F):
            pass
        for constant in (F(0), F(-2), F(1 << 32768), ForeignFraction(2), F(3, 2)):
            results, counts = [], []
            for ordinary in (True, False):
                work = Work()
                calculate = lambda: reader._recording_orientation_bound(
                    (0., 0., 0., 1. + 2. ** -24), points((0, 0, 0, 1)), 1e-5, reader._Bounds(work))
                with patch.object(reader, "_ENDPOINT_TWO", constant):
                    if ordinary:
                        with ordinary_endpoints():
                            results.append(calculate())
                    else:
                        results.append(calculate())
                counts.append(work.counts)
            with self.subTest(constant_type=type(constant), numerator_bits=constant.numerator.bit_length()):
                self.assertEqual(results, [(None, F(1, 1 << 23))] * 2)
                self.assertEqual(counts[0], counts[1])

    def test_before_error_keeps_cold_warm_and_normalized_fallback_order(self):
        for ordinary in (True, False):
            for warm in (False, True):
                for limit in (1e-5, 0.):
                    work = Work()
                    arithmetic = reader._Bounds(work)
                    marker = RuntimeError("current position must still execute")
                    raw = (0., 0., .6, .8 + 2. ** -24)
                    source = points((0, 0, F(3, 5), F(4, 5)))
                    events = []
                    normalize = arithmetic.normalize
                    def normalized(value):
                        events.append("normalize")
                        return normalize(value)
                    def position():
                        events.append("position")
                        raise marker
                    def check():
                        if warm:
                            reader._recording_orientation_bound(raw, source, limit, arithmetic)
                        with patch.object(arithmetic, "normalize", normalized), \
                                self.assertRaises(RuntimeError) as caught:
                            reader._recording_orientation_bound(raw, source, limit, arithmetic,
                                                                before_error=position)
                        self.assertIs(caught.exception, marker)
                    with self.subTest(ordinary=ordinary, warm=warm, limit=limit):
                        if ordinary:
                            with ordinary_endpoints():
                                check()
                        else:
                            check()
                        self.assertEqual(events, ["normalize", "position"] if not warm and not limit else ["position"])

    def test_complete_same_key_carriers_share_only_the_existing_orientation_entry(self):
        def calculate(ordinary):
            epsilon = F(1, 1 << 80)
            def intervals(values):
                return tuple(reader._Cell(F(value), F(value) + epsilon) for value in values)
            work = Work()
            arithmetic = reader._Bounds(work, cache_intermediates=False)
            geometry = {index: {"frame": str(index)} for index in range(3)}
            positions = {index: (float(index) + 1.25, -2.5, 3.75) for index in geometry}
            tracks = {index: {"translation": [positions[index]],
                              "rotation": [(0., 0., 0., 1.)]} for index in geometry}
            rows = {(0, index): {"max_endpoint_position_error_m": .001,
                                "max_endpoint_unit_quaternion_error": 1e-5} for index in geometry}
            reference = SimpleNamespace(recording_pose_enclosures=lambda carriers, time, side,
                recording_context=None: {frame: SimpleNamespace(
                    position=intervals(positions[int(frame)]),
                    orientation=intervals((1, 0, 0, 0))) for frame in carriers})
            def key():
                return reader._key_comparisons(reference, geometry, tracks, F(0), 0,
                                              arithmetic, endpoint_rows=rows)
            if ordinary:
                with ordinary_endpoints():
                    result = key()
            else:
                result = key()
            return result, work
        expected, before = calculate(True)
        result, after = calculate(False)
        self.assertEqual(result, expected)
        self.assertEqual(before.counts["independent_exact_compare"] - after.counts["independent_exact_compare"], 13)
        self.assertEqual(before.counts["independent_bound_decode"] - after.counts["independent_bound_decode"], 1)
        self.assertEqual(before.operations - after.operations, 14)
        self.assertEqual(before._cache, after._cache)
        self.assertEqual(len(after._cache), 1)
        self.assertEqual(after.max_cache_entries, 256)


if __name__ == "__main__":
    unittest.main()
