"""Private source centers retain independent radii, ownership and finite work."""
from contextlib import nullcontext
from dataclasses import replace
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachExecutionWork as Work
from ontokin.reach_reference import (
    Interval, MAX_CACHE, ReachReference, ReferenceError, _Arithmetic, _PoseArithmetic,
    _RecordingBodyRate, _recording_source_signature,
)
from ontokin.reach_reference_center import (
    _CenteredPose, _ChangedDomain, _Guard, _OriginalFailure, _cursor_seal,
    _offset, _orientation, _seed, admit_source, guard_cursor,
)
from ontokin.reach_reference_plan import _PendingCursors
from test_reach_reference_source_batch import prefix
from test_reach_reference_world_recording import reference_case


E, R, G = F(1, 1 << 112), F(1, 1 << 104), F(1, 1 << 128)
ZERO, UNIT = (F(0),) * 3, (F(1), F(0), F(0), F(0))


def point(value):
    value = F(value)
    return Interval(value, value)


def harness(check=None):
    a = _Arithmetic(work=Work(check=check))
    reference = SimpleNamespace(a=a, p=_PoseArithmetic(a))
    plan = SimpleNamespace(admit_owners=lambda reference: None)
    batch = SimpleNamespace(admit_owners=lambda: None)
    return reference, plan, batch


def direct_quaternion(a, axis, rate, clock, initial=F(0)):
    angle = a.exact(initial, a.exact(rate, clock, "mul"), "add")
    sine, cosine = a.sincos(point(a.exact(angle, 2, "div")))
    result = [cosine, point(0), point(0), point(0)]
    result[axis + 1] = sine
    return tuple(result)


class Curve:
    def __init__(self, axis=2, rate=F(1), initial=F(0), check=None):
        self.reference, self.plan, self.batch = harness(check)
        self.axis, self.rate, self.initial = axis, rate, initial
        self.context, self.seeds = (object(), object(), 0, "after"), []
        self.node = SimpleNamespace(path="carrier.frame")
        self.install(rate)

    def install(self, rate, witness=("independent analytic source",)):
        self.rate = rate
        def direct(clock):
            self.seeds.append(clock)
            return direct_quaternion(self.reference.a, self.axis, rate, clock, self.initial)
        self.node.body = _RecordingBodyRate(self.axis, rate, bool(rate), witness,
                                            self.node.path, direct, ())

    @property
    def key(self):
        return self.reference.p._key("recording_center_body_orientation", (self.context, self.node.path))

    def sample(self, clock):
        guard = _Guard(self.reference, self.plan, self.batch)
        pending = _PendingCursors(self.reference.a)
        value = _orientation(self.node, clock, self.context, self.reference, guard, pending)
        pending.publish()
        return value


def hamilton(first, last):
    """Exact four-component oracle, independent of the planar implementation."""
    w, x, y, z = first
    a, b, c, d = last
    return (w*a - x*b - y*c - z*d,
            w*b + x*a + y*d - z*c,
            w*c - x*d + y*a + z*b,
            w*d + x*c - y*b + z*a)


def center_cursors(reference):
    return {key: value for key, value in reference.a.cache.items()
            if key[:1] == ("reference_pose",) and key[3] == "recording_center_body_orientation"}


def admitted_carriers(reference, case):
    # Complete selections include deliberately unsupported static rotated
    # branches. P11's identity arm mounts also have L1=1.1; the initial private
    # proof covers its head/eyes, while its arms keep ordinary enclosures.
    if case == "P11":
        return tuple(path for path in reference.model.objects if path.startswith("rig.head"))
    return tuple(path for path in reference.model.objects if path != "rig.column")


class CenteredKernelTests(unittest.TestCase):
    def assert_ball_contains(self, center, radius, cells):
        squared = sum(max(abs(value - cell.lo), abs(value - cell.hi)) ** 2
                      for value, cell in zip(center, cells))
        self.assertLessEqual(squared, radius * radius)

    def test_all_axes_signed_updates_enclose_finer_direct_oracle_and_reseed(self):
        for axis, rate in ((0, F(7, 8)), (1, F(-9, 8)), (2, F(11, 8))):
            curve = Curve(axis, rate)
            fine = _Arithmetic(work=Work(), bits=256)
            for index in range(68):
                clock = F(index, 256)
                center, radius, actual_axis = curve.sample(clock)
                with self.subTest(axis=axis, index=index):
                    self.assertEqual(actual_axis, axis)
                    self.assertEqual(curve.reference.a.cache[curve.key].steps,
                                     index if index <= 64 else index - 65)
                    if index in (0, 1, 2, 32, 63, 64, 65, 67):
                        self.assert_ball_contains(center, radius,
                            direct_quaternion(fine, axis, rate, clock))
                self.assertLessEqual(len(curve.reference.a.cache), MAX_CACHE)
            self.assertEqual(curve.seeds, [F(0), F(65, 256)])
            self.assertEqual(curve.reference.a.work.max_operations, 100000)
            self.assertEqual(curve.reference.a.work.operations,
                             sum(curve.reference.a.work.counts.values()))

    def test_true_seed_widths_and_inactive_exact_zeros_control_admission(self):
        for width in (F(0), G, E):
            reference, plan, batch = harness()
            cells = (Interval(F(1) - width, F(1)), point(0), point(0), point(0))
            center, radius = _seed(cells, 2, _Guard(reference, plan, batch))
            self.assertEqual(center, (F(1) - width, F(0), F(0), F(0)))
            self.assertEqual(radius, width)
        reference, plan, batch = harness()
        for cells in ((Interval(1-E-G, F(1)), point(0), point(0), point(0)),
                      (point(1), Interval(-G, G), point(0), point(0))):
            with self.subTest(cells=cells), self.assertRaises(_ChangedDomain):
                _seed(cells, 2, _Guard(reference, plan, batch))

    def test_changing_increments_rewinds_contexts_and_eviction_use_honest_seeds(self):
        curve = Curve()
        fine = _Arithmetic(work=Work(), bits=256)
        for clock in (F(0), F(1, 64), F(3, 64), F(7, 64)):
            center, radius, _ = curve.sample(clock)
            self.assert_ball_contains(center, radius, direct_quaternion(fine, 2, F(1), clock))
        self.assertEqual(len(curve.seeds), 1)
        self.assertEqual(curve.reference.a.cache[curve.key].steps, 3)
        curve.sample(F(1, 64))
        self.assertEqual(curve.reference.a.cache[curve.key].steps, 0)
        curve.context = (object(), object(), 0, "after")
        curve.sample(F(2, 64))
        curve.install(F(-1), ("changed negative source",))
        curve.sample(F(3, 64))
        self.assertEqual(curve.reference.a.cache[curve.key].steps, 0)
        for index in range(MAX_CACHE + 1):
            curve.reference.a.remember(("actual eviction", index), F(index))
        self.assertNotIn(curve.key, curve.reference.a.cache)
        curve.sample(F(4, 64))
        self.assertEqual(curve.reference.a.cache[curve.key].steps, 0)
        self.assertEqual(len(curve.reference.a.cache), MAX_CACHE)
        self.assertEqual(len(curve.seeds), 5)

    def test_zero_rate_and_paused_nonzero_angle_keep_uncertainty(self):
        curve = Curve(rate=F(0), initial=F(1, 8))
        first = curve.sample(F(0))
        self.assertGreater(first[1], 0)
        self.assertLessEqual(first[1], E)
        later = curve.sample(F(1, 8))
        self.assertEqual(later, first)
        self.assertEqual(curve.reference.a.cache[curve.key].steps, 1)
        parent = _CenteredPose(ZERO, later[0], F(0), later[1], later[2])
        guard = _Guard(curve.reference, curve.plan, curve.batch)
        offset, uncertain = _offset(guard.pose(parent), (F(1), F(0), F(0)), guard)
        self.assertTrue(uncertain)
        fine = _Arithmetic(work=Work(), bits=256)
        rotation = direct_quaternion(fine, 2, F(0), F(1, 8), F(1, 8))
        expected = _PoseArithmetic(fine).rotate(rotation, tuple(map(point, (1, 0, 0))))
        self.assert_ball_contains(offset, 4*R, expected)

    def test_general_signed_offsets_match_exact_hamilton_projection_and_final_floors(self):
        for axis in range(3):
            for scalar, active in ((F(3, 4), F(1, 2)), (F(-3, 4), F(1, 2)),
                                   (F(1), F(0)), (F(0), F(-1))):
                rotation = [F(0)] * 4
                rotation[0], rotation[axis + 1] = scalar, active
                for vector in ((F(-1, 4), F(1, 2), F(1, 4)),
                               (F(1, 8), F(-3, 8), F(1, 2)),
                               tuple(F(int(index == axis)) for index in range(3)), ZERO):
                    reference, plan, batch = harness()
                    guard = _Guard(reference, plan, batch)
                    parent = _CenteredPose(ZERO, tuple(rotation), F(0), R, axis)
                    actual, uncertain = _offset(guard.pose(parent), guard.vector(vector), guard)
                    conjugate = (rotation[0], *(-value for value in rotation[1:]))
                    exact = hamilton(hamilton(tuple(rotation), (F(0), *vector)), conjugate)[1:]
                    expected = tuple(vector[index] if index == axis else
                                     F((value.numerator << 128) // value.denominator, 1 << 128)
                                     for index, value in enumerate(exact))
                    with self.subTest(axis=axis, scalar=scalar, active=active, vector=vector):
                        self.assertEqual(actual, expected)
                        self.assertEqual(uncertain, any(value for index, value in enumerate(vector)
                                                       if index != axis))

    def test_cursor_radius_and_increment_mutation_cannot_borrow_a_seal(self):
        for change in ("radius", "increment", "steps"):
            curve = Curve()
            curve.sample(F(0))
            curve.sample(F(1, 16))
            previous = curve.reference.a.cache[curve.key]
            if change == "radius":
                object.__setattr__(previous.radius, "_numerator", 0)
            elif change == "increment":
                object.__setattr__(previous.increment[-1], "_numerator", 7)
            else:
                curve.reference.a.cache[curve.key] = replace(previous, steps=0,
                    seal=_cursor_seal(replace(previous, steps=0)))
            with self.subTest(change=change), self.assertRaises(ReferenceError) as caught:
                curve.sample(F(1, 8))
            self.assertEqual(caught.exception.code, "identity")

    def test_changed_cursor_shapes_are_rejected_before_recursive_sealing(self):
        for field, replacement in (("orientation", (F(0),) * 10000),
                                   ("increment", (F(0),) * 10000),
                                   ("increment", (((((F(0),),),),),)),
                                   ("radius", (F(0),) * 10000)):
            curve = Curve()
            curve.sample(F(0))
            previous = curve.reference.a.cache[curve.key]
            object.__setattr__(previous, field, replacement)
            before = curve.reference.a.work.operations
            with self.subTest(field=field), self.assertRaises(ReferenceError) as caught:
                guard_cursor(curve.reference.a, previous)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(curve.reference.a.work.operations, before)

    def test_every_offset_callback_preserves_cancellation_and_latches_domain_change(self):
        def calculate(check=None):
            reference, plan, batch = harness(check)
            guard = _Guard(reference, plan, batch)
            parent = guard.pose(_CenteredPose(ZERO, (F(3, 4), F(0), F(0), F(1, 2)),
                                             F(0), R, 2))
            vector = guard.vector((F(1, 4), F(-1, 2), F(1, 4)))
            return reference, guard, lambda: _offset(parent, vector, guard)
        baseline, _, run = calculate()
        run()
        count = baseline.a.work.operations
        self.assertGreater(count, 4)
        for fail_at in range(1, count + 1):
            for mutation in ("cancel", "cap", "precision", "operand"):
                calls, saved = [0], []
                marker = RuntimeError("cancel exact centered offset")
                def check():
                    calls[0] += 1
                    if calls[0] == fail_at:
                        if mutation == "cancel":
                            raise marker
                        if mutation == "cap":
                            reference.a.work.max_operand_bits = 32767
                        elif mutation == "precision":
                            reference.a.scale = 1 << 127
                        else:
                            operand = guard.leaves[0][0]
                            saved.append((operand, operand.numerator))
                            object.__setattr__(operand, "_numerator", operand.numerator + 1)
                    elif calls[0] > fail_at:
                        self.fail("a rejected optional callback was followed by another callback")
                reference, guard, run = calculate(check)
                expected = RuntimeError if mutation == "cancel" else (
                    ReferenceError if mutation == "operand" else _ChangedDomain)
                try:
                    with self.subTest(fail_at=fail_at, mutation=mutation), self.assertRaises(expected) as caught:
                        run()
                    if mutation == "cancel":
                        self.assertIs(caught.exception, marker)
                        self.assertIs(reference.a.work.callback_error, marker)
                    self.assertEqual(calls[0], fail_at)
                finally:
                    for operand, numerator in saved:
                        object.__setattr__(operand, "_numerator", numerator)


class CenteredOriginalOracleTests(unittest.TestCase):
    def test_scoped_observer_preserves_original_cells_charges_and_check_owner(self):
        outputs = []
        for observed in (False, True):
            reference, plan, batch = harness()
            original_check = reference.a.check
            if observed:
                result = _Guard(reference, plan, batch).original(reference.a.sincos, point(F(1, 8)))
            else:
                result = reference.a.sincos(point(F(1, 8)))
            self.assertIs(reference.a.check, original_check)
            self.assertIsNone(reference.a._recording_after_tick)
            outputs.append((result, reference.a.work.operations, reference.a.work.counts))
        self.assertEqual(outputs[0], outputs[1])

    def test_scale_mutation_at_final_cosine_grid_rejects_before_a_later_restore(self):
        armed, calls, restored = [False], [0], []
        def check():
            if armed[0]:
                calls[0] += 1
                if calls[0] == 1:
                    reference.a.scale = 1 << 127
                else:
                    restored.append(True)
                    reference.a.scale = 1 << 128
        reference, plan, batch = harness(check)
        original = reference.a.grid
        def grid(low, high):
            if F(9, 10) < low <= high < 1:
                armed[0] = True
            return original(low, high)
        with patch.object(reference.a, "grid", side_effect=grid), self.assertRaises(_ChangedDomain):
            _Guard(reference, plan, batch).original(reference.a.sincos, point(F(1, 8)))
        self.assertTrue(armed[0])
        self.assertEqual(calls[0], 1)
        self.assertFalse(restored)
        self.assertIsNone(reference.a._recording_after_tick)

    def test_cap_narrow_restore_is_latched_after_success_without_omitting_original_work(self):
        calls = [0]
        def check():
            calls[0] += 1
            reference.a.work.max_operand_bits = 32767 if calls[0] == 1 else 32768
        reference, plan, batch = harness(check)
        guard = _Guard(reference, plan, batch)
        def original():
            first = reference.a.exact(F(1), F(2), "add")
            return reference.a.exact(first, F(3), "add")
        with self.assertRaises(_ChangedDomain):
            guard.original(original)
        self.assertEqual(calls[0], 2)
        self.assertEqual(reference.a.work.operations, 2)
        self.assertEqual(reference.a.work.max_operand_bits, 32768)
        self.assertTrue(guard.invalidated)
        self.assertIsNone(reference.a._recording_after_tick)

    def test_original_resource_failure_is_not_skipped_by_the_optional_cap_latch(self):
        calls, failures = [0], []
        def check():
            calls[0] += 1
            reference.a.work.max_operand_bits = 8 if calls[0] == 1 else 32768
        reference, plan, batch = harness(check)
        def original():
            try:
                return reference.a.exact(F(1 << 12), F(2), "mul")
            except ReferenceError as error:
                failures.append(error)
                raise
        with self.assertRaises(_OriginalFailure) as caught:
            _Guard(reference, plan, batch).original(original)
        self.assertEqual(calls[0], 1)
        self.assertEqual(len(failures), 1)
        self.assertIs(caught.exception.error, failures[0])
        self.assertEqual(failures[0].code, "resource")
        self.assertIsNone(reference.a._recording_after_tick)

    def test_original_callback_exceptions_and_observer_replacements_keep_ownership(self):
        for marker in (RuntimeError("oracle cancellation"), ReferenceError("resource", "caller refusal")):
            def check():
                raise marker
            reference, plan, batch = harness(check)
            with self.subTest(marker=type(marker).__name__):
                try:
                    _Guard(reference, plan, batch).original(reference.a.sincos, point(F(1, 8)))
                except _OriginalFailure as error:
                    self.assertIs(error.error, marker)
                except RuntimeError as error:
                    self.assertIs(error, marker)
                else:
                    self.fail("original callback failure was hidden")
                self.assertIs(reference.a.work.callback_error, marker)
                self.assertIsNone(reference.a._recording_after_tick)
        foreign = lambda: None
        def replace_observer():
            reference.a._recording_after_tick = foreign
        reference, plan, batch = harness(replace_observer)
        with self.assertRaises(_OriginalFailure) as caught:
            _Guard(reference, plan, batch).original(reference.a.exact, F(1), F(2), "add")
        self.assertEqual(caught.exception.error.code, "identity")
        self.assertIs(reference.a._recording_after_tick, foreign)


class CenteredSourcePlanTests(unittest.TestCase):
    def test_actual_source_centers_enclose_finer_public_observations_and_keep_public_cells(self):
        for case in ("P09", "P11", "L03"):
            reference, _ = reference_case(case, F(1, 2))
            finer, _ = reference_case(case, F(1, 2), bits=256)
            context, carriers = object(), admitted_carriers(reference, case)
            with reference.recording_source_batch(context):
                self.assertIsNone(reference._recording_centered_poses(tuple(reference.model.objects), F(0),
                                                                      recording_context=context))
                for index in range(12):
                    clock = F(index, 64)
                    actual = reference._recording_centered_poses(carriers, clock, recording_context=context)
                    self.assertIsNotNone(actual, (case, index, carriers))
                    if index not in (0, 1, 5, 11):
                        continue
                    expected = finer.recording_pose_enclosures(carriers, clock)
                    ordinary = reference.recording_pose_enclosures(carriers, clock, recording_context=context)
                    for carrier in actual:
                        with self.subTest(case=case, index=index, carrier=carrier):
                            self.assertIs(type(actual[carrier]), _CenteredPose)
                            self.assertTrue(all(type(cell) is Interval for cell in ordinary[carrier].position))
                            self.assertTrue(all(type(cell) is Interval for cell in ordinary[carrier].orientation))
                            if case == "P11" and carrier == "rig.head.frame":
                                # Source Y-axis rotation fixes the Y-only
                                # inverse base offset exactly. The ordinary
                                # Hamilton box has dependency overestimation,
                                # so its wider box need not fit a singleton.
                                joint = next(joint for joint in reference.model.joints.values()
                                             if reference.model.sites[joint.child].owner == "rig.head")
                                neck, base = (reference.model.sites[path] for path in (joint.parent, joint.child))
                                root = reference.model.objects[neck.owner]
                                self.assertEqual((joint.kind, joint.axis), ("hinge", (0., 1., 0.)))
                                self.assertEqual((root.path, root.placement.frame), ("rig", "world"))
                                self.assertEqual(root.placement.position, (0., 1.25, 0.))
                                self.assertEqual(neck.pose.position, (0., 1., 0.))
                                self.assertEqual(base.pose.position, (0., -.25, 0.))
                                self.assertTrue(all(item.rotation == (1., 0., 0., 0.)
                                                    for item in (root.placement, neck.pose, base.pose)))
                                state = reference._state_at(clock, "after")
                                self.assertIsNone(state.claims.get(("rig", "translation")))
                                self.assertIsNone(state.claims.get(("rig", "orientation")))
                                exact = tuple(F(root.placement.position[k]) + F(neck.pose.position[k])
                                              - F(base.pose.position[k]) for k in range(3))
                                self.assertEqual(exact, (F(0), F(5, 2), F(0)))
                                self.assertEqual(actual[carrier].position, exact)
                                self.assertEqual(actual[carrier].position_radius, 0)
                                self.assertTrue(all(cell.contains(value) for cell, value
                                                    in zip(expected[carrier].position, exact)))
                            else:
                                CenteredKernelTests.assert_ball_contains(self, actual[carrier].position,
                                    actual[carrier].position_radius, expected[carrier].position)
                            CenteredKernelTests.assert_ball_contains(self, actual[carrier].orientation,
                                actual[carrier].orientation_radius, expected[carrier].orientation)
            self.assertIsNone(reference._recording_batch)
            self.assertLessEqual(len(reference.a.cache), MAX_CACHE)

    def test_source_prefix_bytes_and_full_validation_reports_are_unchanged(self):
        for case in ("P09", "P11", "L03"):
            outcomes = []
            for enabled in (False, True):
                context = nullcontext() if enabled else patch.object(ReachReference, "_recording_centered_poses", return_value=None)
                with context:
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                outcomes.append((result.data, result.report["validation"], compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            print(f"{case} centered prefix: ordinary={outcomes[0][2]}, centered={outcomes[1][2]}")

    def test_capture_detaches_fraction_interval_aliases_but_keeps_live_typed_receipt(self):
        reference, _ = reference_case("P09", F(1, 2))
        leaf = F(1, 8)
        cell = Interval(leaf, leaf)
        source = ("native source", (leaf, cell))
        receipt = reference._recording_capture(lambda: source)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.values, source)
        self.assertIsNot(receipt.values[1][0], leaf)
        self.assertIsNot(receipt.values[1][1], cell)
        self.assertIsNot(receipt.values[1][1].lo, leaf)
        original = leaf.numerator
        try:
            object.__setattr__(leaf, "_numerator", 3)
            self.assertEqual(receipt.values[1][0], F(1, 8))
            self.assertNotEqual(_recording_source_signature(receipt.read()), receipt.signature)
            self.assertEqual(_recording_source_signature(receipt.values), receipt.signature)
        finally:
            object.__setattr__(leaf, "_numerator", original)

    def test_fresh_signatures_keep_the_original_bounded_source_shapes(self):
        reference, _ = reference_case("P09", F(1, 2))
        depth_three = (F(0),)
        for _ in range(3):
            depth_three = (depth_three,)
        depth_four = (depth_three,)
        accepted = ((F(0),) * 16, ((F(0),) * 8,), depth_three,
                    ((Interval(F(0), F(1)),),))
        rejected = ((F(0),) * 17, ((F(0),) * 9,), depth_four,
                    ((F(0),) * 10000,))
        for values in accepted:
            with self.subTest(values=values):
                self.assertIsNotNone(reference._recording_source_witness(*values))
                self.assertIsNotNone(_recording_source_signature(values))
        for values in rejected:
            self.assertIsNone(reference._recording_source_witness(*values))
            with self.assertRaises(ReferenceError) as caught:
                _recording_source_signature(values)
            self.assertEqual(caught.exception.code, "identity")
        cell = Interval(F(0), F(1))
        object.__setattr__(cell, "lo", cell)
        with self.assertRaises(ReferenceError):
            _recording_source_signature((cell,))

    def test_final_source_leaf_admission_precedes_signature_work(self):
        reference, _ = reference_case("P09", F(1, 2))
        current = [("captured source", F(1))]
        receipt = reference._recording_capture(lambda: current[0])
        plan = SimpleNamespace(receipts=(receipt,))
        too_deep = (F(0),)
        for _ in range(4):
            too_deep = (too_deep,)
        for invalid in (F(1 << 1024), float("nan"), (F(0),) * 10000, too_deep):
            current[0] = ("captured source", invalid)
            with self.subTest(kind=type(invalid).__name__), \
                    patch("ontokin.reach_reference_center._recording_source_signature",
                          side_effect=AssertionError("source leaf must be admitted first")), \
                    self.assertRaises(ReferenceError) as caught:
                admit_source(plan, reference)
            self.assertEqual(caught.exception.code, "identity")

    def test_final_live_source_mutation_discards_centered_body_and_stationary_writes(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), admitted_carriers(reference, "P09")
        owned = {}
        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context) as batch:
                self.assertIsNotNone(reference._recording_centered_poses(carriers, F(1, 8), recording_context=context))
                self.assertIsNotNone(reference._recording_centered_poses(carriers, F(1, 4), recording_context=context))
                owned.update(batch.cursors)
                self.assertTrue(any(key[0] == "reference_centered_stationary_pose" for key in owned))
                self.assertTrue(center_cursors(reference))
                state = reference._state_at(F(1, 4), "after")
                state.ideal_positions["rig"] = tuple(map(point, (F(1, 8), 0, 0)))
        self.assertEqual(caught.exception.code, "identity")
        self.assertTrue(owned)
        self.assertTrue(all(reference.a.cache.get(key) is not value for key, value in owned.items()))
        self.assertIsNone(reference._recording_batch)

    def test_root_magnitude_and_grid_restrictions_use_the_ordinary_same_work_path(self):
        for root in ((F(65), F(0), F(0)), (F(1, 3), F(0), F(0))):
            reference, _ = reference_case("P09", F(1, 2))
            clock, context, carriers = F(1, 8), object(), admitted_carriers(reference, "P09")
            state = reference._state_at(clock, "after")
            state.ideal_positions["rig"] = tuple(map(point, root))
            work = reference.a.work
            with self.subTest(root=root), reference.recording_source_batch(context):
                self.assertIsNone(reference._recording_centered_poses(carriers, clock, recording_context=context))
                ordinary = reference.recording_pose_enclosures(carriers, clock, recording_context=context)
                self.assertTrue(ordinary)
                self.assertTrue(all(type(cell) is Interval for value in ordinary.values() for cell in value.position))
                self.assertIs(reference.a.work, work)
            self.assertEqual(work.max_operations, 100000)

    def test_local_offset_l1_boundary_and_grid_restrictions_are_compiled_before_use(self):
        for vector, admitted in (((F(1, 4), F(1, 2), F(1, 4)), True),
                                 ((F(1, 4), F(1, 2), F(1, 4) + G), False),
                                 ((F(1, 3), F(0), F(0)), False)):
            reference, _ = reference_case("P09", F(1, 2))
            relation = reference.model.actions["reach"].reach.elbow
            site = reference.model.sites[reference.model.joints[relation].parent]
            site.pose = replace(site.pose, position=vector)
            clock, context, carriers = F(1, 8), object(), admitted_carriers(reference, "P09")
            work = reference.a.work
            with self.subTest(vector=vector), reference.recording_source_batch(context):
                centered = reference._recording_centered_poses(carriers, clock, recording_context=context)
                self.assertEqual(centered is not None, admitted)
                ordinary = reference.recording_pose_enclosures(carriers, clock, recording_context=context)
                self.assertTrue(ordinary)
                self.assertIs(reference.a.work, work)
                self.assertTrue(all(type(cell) is Interval for value in ordinary.values() for cell in value.position))


if __name__ == "__main__":
    unittest.main()
