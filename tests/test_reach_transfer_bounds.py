"""First-release finite-cell allowances keep source responses and live gates."""
from contextlib import nullcontext
from copy import copy, deepcopy
from dataclasses import replace
from fractions import Fraction as F
import gc
import math
import unittest
import weakref
from unittest.mock import patch

from ontokin import reach_conformance, reach_transfer_bounds as transfer
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, float_bits
from ontokin.reach_phase import AnchorError
from ontokin.reach_reference import Interval, _Arithmetic, _PoseArithmetic, build_reference
from ontokin.reach_runtime import ReachSimulator
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_phase import changed
from test_reach_recurring_endpoint_claims import replace_document


END = F(1, 8)
FIELDS = ("position", "orientation", "velocity", "omega")


def point(value):
    value = F(value)
    return Interval(value, value)


def radius(cells, center):
    return sum((max(abs(cell.lo - value), abs(cell.hi - value))
                for cell, value in zip(cells, center)), F(0))


def separation(first, second):
    return sum((max(abs(a.lo - b.hi), abs(a.hi - b.lo))
                for a, b in zip(first, second)), F(0))


def hamilton(left, right):
    w, x, y, z = left
    a, b, c, d = right
    return (w*a - x*b - y*c - z*d, w*b + x*a + y*d - z*c,
            w*c - x*d + y*a + z*b, w*d + x*c - y*b + z*a)


def rotate_exact(quaternion, vector):
    conjugate = (quaternion[0], *(-value for value in quaternion[1:]))
    return hamilton(hamilton(quaternion, (F(0), *vector)), conjugate)[1:]


def arithmetic(bits=128):
    return _PoseArithmetic(_Arithmetic(work=ReachExecutionWork(), bits=bits))


def release_bundle(*, nonplanar=False):
    bundle = changed(source_case("P16"), "at 2[s] sequence", "at 0.125[s] sequence")
    if nonplanar:
        bundle = changed(bundle, "0[rad/s], 0[rad/s], 0.25[rad/s]",
                         "0[rad/s], 0.25[rad/s], 0[rad/s]")
    return bundle


def force_bundle():
    return changed(release_bundle(),
        'force payload @ "released-push" using vector(world, 1[N], 0[N], 0[N]) for 1[s]; }',
        'force payload @ "released-push" using vector(world, 1[N], 0[N], 0[N]) for 0.125[s]; }\n'
        '    at 0.25[s] sequence { force payload @ "replacement-push" '
        'using vector(world, 1[N], 0[N], 0[N]) for 0.125[s]; }')


def impulse_bundle(*, zero=False):
    impulse = "0" if zero else "0.2"
    return changed(release_bundle(), "release grip using incoming;",
        "release grip using incoming; impulse payload using "
        f"vector(world, 0[N*s], {impulse}[N*s], 0[N*s]) "
        "at point(payload.frame, 0.07[m], 0.02[m], 0[m]);")


def simulator(bundle=None):
    built = compile_construction(release_bundle() if bundle is None else bundle)
    return ReachSimulator(built.model, work=built.reach_work)


def reference(bundle, end):
    built = compile_construction(bundle)
    return build_reference(built.model, end=end, work=built.reach_work)


def native_signature(sim, time):
    anchor = sim.state.dynamic["payload"]
    value = sim._dynamic_kinematics("payload", time, sim.state)
    return (anchor.time, anchor.since,
            tuple(tuple(map(float_bits, getattr(value, name))) for name in FIELDS),
            tuple(sim.state.forces["payload"].net), sim.state.forces["payload"].acceleration)


class ReleaseCellArithmeticTests(unittest.TestCase):
    def test_normalization_bounds_tiny_points_signed_units_and_uncertain_cells(self):
        q = (F(3, 5), F(4, 5), F(0), F(0))
        for scale in (F(1), F(-1), F(1, 1 << 64)):
            ops, proof = arithmetic(), transfer.CellArithmetic(ReachExecutionWork())
            source = tuple(value * scale for value in q)
            center = q if scale > 0 else tuple(-value for value in q)
            actual = ops.quaternion(source)
            with self.subTest(scale=scale):
                self.assertLessEqual(radius(actual, center), proof.normalized_point(source))
        for amount in (transfer.GRID, F(1, 100), F(1, 2)):
            ops, proof = arithmetic(), transfer.CellArithmetic(ReachExecutionWork())
            cells = tuple(Interval(value - amount, value + amount) for value in q)
            actual = ops.quaternion(cells)
            self.assertLessEqual(radius(actual, q), proof.normalize(4 * amount))
        for sign in (-1, 1):
            proof = transfer.CellArithmetic(ReachExecutionWork())
            self.assertEqual(proof.normalized_point((F(sign, 1 << 1074), F(0), F(0), F(0))), 0)

    def test_hamilton_and_both_rotation_expressions_enclose_exact_unit_centers(self):
        a = (F(1, 2),) * 4
        b = (F(3, 5), F(0), F(0), F(-4, 5))
        vector = (F(3, 2), F(-1, 7), F(1, 1 << 200))
        delta, spread = F(7, 1 << 128), F(11, 1 << 128)
        for q in (a, b, tuple(-value for value in a)):
            ops, proof = arithmetic(), transfer.CellArithmetic(ReachExecutionWork())
            left = tuple(Interval(value - delta, value + delta) for value in q)
            right = tuple(Interval(value - spread, value + spread) for value in b)
            actual = ops.multiply(left, right)
            self.assertLessEqual(radius(actual, hamilton(q, b)), proof.product(4*delta, 4*spread))
            # Keep exact axis zeros for the factor path, and uncertain zeros
            # for the full two-Hamilton-product path.
            rotation = tuple(point(value) if value == 0 and q is b else
                             Interval(value - delta, value + delta) for value in q)
            values = tuple(Interval(value - spread, value + spread) for value in vector)
            self.assertLessEqual(radius(ops.rotate(rotation, values), rotate_exact(q, vector)),
                proof.rotate(radius(rotation, q), 3*spread, sum(map(abs, vector), F(0))))
            self.assertEqual(proof.work.operations, sum(proof.work.counts.values()))
            self.assertGreater(proof.work.operations, 0)

    def test_sine_spin_and_ballistic_grid_remainders_cover_finer_cells(self):
        for angle in (F(0), F(-7, 5), F(12345, 7)):
            ops, fine, proof = arithmetic(), arithmetic(256), transfer.CellArithmetic(ReachExecutionWork())
            spread = F(5, 1 << 128)
            actual = ops.a.sincos(Interval(angle - spread, angle + spread))
            expected = fine.a.sincos(point(angle))
            bound = proof.sincos(spread, abs(angle))
            for value, true_cell in zip(actual, expected):
                self.assertLessEqual(separation((value,), (true_cell,)), bound)
        for omega, elapsed in (((F(3, 5), F(4, 5), F(0)), F(3, 7)),
                               ((F(0), F(-1, 4), F(0)), F(5, 3)),
                               ((F(0), F(0), F(0)), F(1))):
            ops, fine, proof = arithmetic(), arithmetic(256), transfer.CellArithmetic(ReachExecutionWork())
            actual, expected = ops.spin(omega, elapsed), fine.spin(omega, elapsed)
            self.assertLessEqual(separation(actual, expected), proof.spin(omega, F(0), F(0), elapsed))
        proof = transfer.CellArithmetic(ReachExecutionWork())
        envelope = transfer.CellEnvelope(F(1, 32), F(0), F(1, 16), F(0), F(2), F(3), F(0))
        anchor = transfer.CellAnchor(F(0), envelope, F(3), F(4), F(0), (), ())
        result = proof.dynamic(anchor, (0., 0., 0.), AnchorError(),
                               (F(1, 3), F(0), F(0)), (F(1, 7), F(0), F(0)), F(1, 2))
        for bound, exact in ((result.position, F(1, 32) + F(1, 32) + F(4, 21)/8 + 12*transfer.GRID),
                             (result.velocity, F(1, 16) + F(2, 21) + 6*transfer.GRID)):
            self.assertGreaterEqual(bound, exact)
            self.assertLess(bound - exact, transfer.PROOF_GRID)

    def test_outward_proof_grid_bounds_repeated_transfers_and_keeps_live_preflights(self):
        work = ReachExecutionWork()
        proof = transfer.CellArithmetic(work)
        for value in (F(0), F(1, 3), F(7, 11), transfer.TINY,
                      F(31, 1 << 128), F((1 << 800) + 3, 17)):
            bound = proof.upper(value)
            with self.subTest(value=value):
                self.assertGreaterEqual(bound, value)
                self.assertLess(bound - value, transfer.PROOF_GRID)
                self.assertLessEqual(bound.denominator.bit_length(), transfer.PROOF_BITS + 1)
                self.assertEqual(bound.denominator & (bound.denominator - 1), 0)
                if value in (F(0), F(31, 1 << 128)):
                    self.assertEqual(bound, value)
        value = F(1, 1 << 90)
        for _ in range(24):
            value = proof.normalize(proof.product(value, F(1, 1 << 100)))
            self.assertLessEqual(value.denominator.bit_length(), transfer.PROOF_BITS + 1)
        self.assertEqual(work.operations, sum(work.counts.values()))
        for cap in (256, 300):
            work = ReachExecutionWork()
            proof = transfer.CellArithmetic(work)

            def narrow():
                if cap == 256 or work.counts.get("transfer_upper_round"):
                    work.max_operand_bits = cap

            work.external_check = narrow
            with self.subTest(cap=cap), self.assertRaises(ReachAdmissionError) as caught:
                proof.upper(F(1 << 100, 3))
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        work = ReachExecutionWork()
        proof = transfer.CellArithmetic(work)
        marker = RuntimeError("cancel outward quotient")

        def cancel():
            if work.counts.get("transfer_upper_round"):
                raise marker

        work.external_check = cancel
        with self.assertRaises(RuntimeError) as caught:
            proof.upper(F(1, 3))
        self.assertIs(caught.exception, marker)

    def test_grid_remainders_and_publication_terms_remain_live_and_bounded(self):
        work = ReachExecutionWork()
        proof = transfer.CellArithmetic(work)
        self.assertEqual(proof.publication(F(0)), 3*transfer.TINY)
        self.assertEqual(proof.publication(F(7)), 7*transfer.EXPOSE + 3*transfer.TINY)
        marker = RuntimeError("cancel transfer scalar proof")
        work.external_check = lambda: (_ for _ in ()).throw(marker)
        with self.assertRaises(RuntimeError) as caught:
            proof.normalize(F(1, 1 << 90))
        self.assertIs(caught.exception, marker)
        work = ReachExecutionWork(max_operand_bits=128)
        with self.assertRaises(ReachAdmissionError):
            transfer.CellArithmetic(work).publication(F(1))


class ReleaseCellTransitionTests(unittest.TestCase):
    def assert_anchor_encloses(self, sim, independent, time):
        proof = sim.state.dynamic_cells["payload"]
        self.assertEqual(proof.clock, time)
        state = independent._state_at(time, "after")
        anchor = state.dynamic["payload"]
        for name, bound in (("position", proof.position_size), ("velocity", proof.velocity_size),
                            ("omega", proof.omega_size)):
            for pose in (anchor.actual, anchor.ideal):
                self.assertLessEqual(sum((value.magnitude for value in getattr(pose, name)), F(0)), bound)
        for name, allowance in zip(FIELDS, (proof.envelope.position, proof.envelope.rotation,
                                           proof.envelope.velocity, proof.envelope.omega)):
            self.assertLessEqual(separation(getattr(anchor.actual, name), getattr(anchor.ideal, name)), 2*allowance)
        error = sim.state.dynamic_errors["payload"]
        for actual, required in ((error.position_m, anchor.position_error),
                                 (error.rotation_rad, anchor.rotation_error),
                                 (error.velocity_m_per_s, anchor.velocity_error),
                                 (error.angular_velocity_rad_per_s, anchor.omega_error)):
            self.assertGreaterEqual(actual, required)
        source = sim.phase_bounds(time, time)["frames"]["payload.frame"]
        required = independent.point_phase("payload", time)
        for actual, expected in ((source.position_error_m, required.source_numeric_position_error),
                                 (source.rotation_error_rad, required.source_numeric_rotation_error),
                                 (source.velocity_error_m_per_s, required.source_numeric_velocity_error),
                                 (source.angular_velocity_error_rad_per_s, required.source_numeric_angular_velocity_error)):
            self.assertGreaterEqual(actual, expected)
        self.assertEqual(sim.work.max_operations, 100000)
        self.assertEqual(sim.work.max_operand_bits, 32768)
        self.assertEqual(sim.work.max_cache_entries, 256)
        self.assertLessEqual(len(sim.work._cache), 256)
        self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))

    def test_short_release_and_nonplanar_ancestry_bound_every_actual_anchor_field(self):
        for nonplanar in (False, True):
            bundle = release_bundle(nonplanar=nonplanar)
            sim = simulator(bundle)
            sim.advance(END, "after")
            independent = reference(bundle, END)
            with self.subTest(nonplanar=nonplanar):
                self.assert_anchor_encloses(sim, independent, END)

    def test_original_p16_release_and_force_completion_have_independent_cell_coverage(self):
        bundle = source_case("P16")
        for time in (F(2), F(3)):
            sim = simulator(bundle)
            sim.advance(time, "after")
            independent = reference(bundle, time)
            with self.subTest(time=time):
                self.assert_anchor_encloses(sim, independent, time)

    def test_equal_force_replacement_moves_only_the_proof_clock(self):
        bundle, time = force_bundle(), F(1, 4)
        sim = simulator(bundle)
        sim.advance(END, "after")
        old_native_time = sim.state.dynamic["payload"].time
        before = sim.advance(time, "before")
        after = sim.advance(time, "after")
        self.assertEqual(sim.state.dynamic["payload"].time, old_native_time)
        for field in ("position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s"):
            self.assertEqual(before["objects"]["payload"][field], after["objects"]["payload"][field])
        self.assert_anchor_encloses(sim, reference(bundle, time), time)

    def test_nonzero_impulse_bounds_the_stored_reader_distance_and_zero_keeps_the_anchor(self):
        for zero in (False, True):
            bundle = impulse_bundle(zero=zero)
            sim = simulator(bundle)
            sim.advance(END, "after")
            independent = reference(bundle, END)
            with self.subTest(zero=zero):
                self.assert_anchor_encloses(sim, independent, END)
                self.assertEqual(sim.state.impulses["payload"].applied_count, 1)
                if not zero:
                    self.assertGreater(sim.work.counts.get("transfer_anchor_publish", 0), 2)
                else:
                    self.assertEqual(sim.work.counts.get("transfer_anchor_publish", 0), 2)

    def test_native_responses_release_records_and_source_clocks_equal_the_ordinary_path(self):
        for bundle, clocks in ((release_bundle(), (END, F(1, 4))),
                               (force_bundle(), (END, F(1, 4), F(3, 8))),
                               (impulse_bundle(), (END, F(1, 4)))):
            values = []
            for enabled in (False, True):
                sim = simulator(bundle)
                observations = []
                with nullcontext() if enabled else patch.object(transfer, "first_release", return_value=None):
                    for time in clocks:
                        sim.advance(time, "after")
                        observations.append((native_signature(sim, time), deepcopy(sim.incoming_releases)))
                values.append(observations)
            self.assertEqual(*values)

    def test_completed_root_lineage_and_oversized_unselected_tables_keep_the_ordinary_path(self):
        bundle = changed(release_bundle(), "at 0[s] sequence { start travel; start turn; start reach; }",
            "at 0[s] sequence { start travel; start turn; start reach; }\n"
            "    at 0.0625[s] sequence { stop turn; }")
        sim = simulator(bundle)
        sim.advance(END, "after")
        self.assertNotIn("payload", sim.state.dynamic_cells)
        sim = simulator()
        sim.advance(END, "before")
        original = sim.model.objects["rig"]
        while sum(len(getattr(sim.model, name)) for name in transfer._TABLES) <= 256:
            name = "unselected_" + str(len(sim.model.objects))
            sim.model.objects[name] = replace(original, path=name, name=name, element_id=(name,))
        self.assertIsNone(transfer.first_release(sim, sim.state, "payload", END))
        self.assertFalse(sim.state.dynamic_cells)


class ReleaseCellAdmissionTests(unittest.TestCase):
    def test_owner_tokens_keep_sources_alive_and_copy_identity_without_owner_methods(self):
        class Owner:
            def __eq__(self, other):
                raise AssertionError("An identity receipt must not compare its source owner.")

            def __deepcopy__(self, memo):
                raise AssertionError("An identity receipt must not copy its source owner.")

        owner = Owner()
        alive = weakref.ref(owner)
        token = transfer._OwnerRef(owner)
        self.assertEqual(token, transfer._OwnerRef(owner))
        self.assertNotEqual(token, transfer._OwnerRef(Owner()))
        self.assertIs(copy(token), token)
        self.assertIs(deepcopy(token), token)
        del owner
        gc.collect()
        self.assertIs(token[0], alive())
        self.assertIsNotNone(alive())
        del token
        gc.collect()
        self.assertIsNone(alive())

    def test_first_release_equal_owner_replacements_reject_even_with_colliding_addresses(self):
        class First(ReachSimulator):
            pass

        class Second(ReachSimulator):
            pass

        changes = ("model_table", "model_row", "model_pose", "physical", "state_table",
                   "action", "solution", "grips", "class")
        for change in changes:
            # Simulate an ABA address collision deterministically. Only this
            # helper's address lookup is replaced; source values stay exact.
            with self.subTest(change=change), patch.object(transfer, "id", return_value=17, create=True):
                sim = simulator()
                sim.__class__ = First
                sim.advance(END, "before")
                captured = transfer.first_release(sim, sim.state, "payload", END)
                self.assertIsNotNone(captured)
                check, changed_once = sim.work.external_check, []

                def mutate():
                    if check is not None:
                        check()
                    if changed_once:
                        return
                    changed_once.append(True)
                    if change == "model_table":
                        sim.model.objects = dict(sim.model.objects)
                    elif change == "model_row":
                        sim.model.objects["payload"] = replace(sim.model.objects["payload"])
                    elif change == "model_pose":
                        sim.model.sites["payload.origin"].pose = replace(sim.model.sites["payload.origin"].pose)
                    elif change == "physical":
                        sim.model.objects["payload"].physical = dict(sim.model.objects["payload"].physical)
                    elif change == "state_table":
                        sim.state.coordinates = dict(sim.state.coordinates)
                    elif change == "action":
                        sim.state.actions["reach"] = replace(sim.state.actions["reach"])
                    elif change == "solution":
                        sim.state.actions["reach"].solution = replace(sim.state.actions["reach"].solution)
                    elif change == "grips":
                        sim.state.active_grips = set(sim.state.active_grips)
                    else:
                        sim.__class__ = Second
                    gc.collect()

                sim.work.external_check = mutate
                with self.assertRaises(ReachAdmissionError):
                    captured.evaluate()
                self.assertTrue(changed_once)
                self.assertFalse(sim.state.dynamic_cells)

    def test_persistent_model_receipt_rejects_equal_replacement_with_colliding_addresses(self):
        for change in ("table", "record", "pose", "physical"):
            with self.subTest(change=change), patch.object(transfer, "id", return_value=17, create=True):
                sim = simulator()
                sim.advance(END, "after")
                proof = sim.state.dynamic_cells["payload"]
                old = weakref.ref(sim.model.objects["payload"])
                if change == "table":
                    sim.model.objects = dict(sim.model.objects)
                elif change == "record":
                    sim.model.objects["payload"] = replace(sim.model.objects["payload"])
                elif change == "pose":
                    sim.model.objects["payload"].placement = replace(sim.model.objects["payload"].placement)
                else:
                    sim.model.objects["payload"].physical = dict(sim.model.objects["payload"].physical)
                gc.collect()
                self.assertIsNotNone(old())
                with self.assertRaises(ReachAdmissionError):
                    transfer.source_sizes(sim, sim.state, "payload", END, F(1, 4))
                self.assertIs(sim.state.dynamic_cells["payload"], proof)

    def test_dynamic_owner_receipts_reject_equal_callback_replacements_with_colliding_addresses(self):
        changes = ("dynamic", "dynamic_errors", "dynamic_error_times", "ideal_accelerations",
                   "forces", "modes", "claims", "anchor", "native", "error", "history")
        for stage in ("transfer_dynamic_guard", "transfer_dynamic_publish"):
            for change in changes:
                with self.subTest(stage=stage, change=change), patch.object(transfer, "id", return_value=17, create=True):
                    sim = simulator()
                    sim.advance(END, "after")
                    state, proof = sim.state, sim.state.dynamic_cells["payload"]
                    check, changed_once, original_charge = sim.work.external_check, [], sim.work.charge

                    def mutate():
                        if check is not None:
                            check()
                        if changed_once:
                            return
                        changed_once.append(True)
                        if change == "anchor":
                            state.dynamic["payload"] = replace(state.dynamic["payload"])
                        elif change == "native":
                            state.dynamic["payload"].state = replace(state.dynamic["payload"].state)
                        elif change == "error":
                            state.dynamic_errors["payload"] = replace(state.dynamic_errors["payload"])
                        elif change == "history":
                            state.forces["payload"] = replace(state.forces["payload"])
                        else:
                            setattr(state, change, dict(getattr(state, change)))
                        gc.collect()

                    def charge(kind="checkpoint", amount=1):
                        if kind == stage:
                            sim.work.external_check = mutate
                        return original_charge(kind, amount)

                    with patch.object(sim.work, "charge", side_effect=charge), self.assertRaises(ReachAdmissionError):
                        transfer.source_sizes(sim, state, "payload", END, F(1, 4))
                    self.assertTrue(changed_once)
                    self.assertIs(state.dynamic_cells["payload"], proof)

    def test_state_deepcopy_keeps_model_tokens_without_retaining_historical_state_owners(self):
        sim = simulator()
        sim.advance(END, "after")
        state, proof = sim.state, sim.state.dynamic_cells["payload"]
        pending, owners = [proof.lineage], []
        while pending:
            value = pending.pop()
            if type(value) is transfer._OwnerRef:
                owners.append(value[0])
            elif type(value) is tuple:
                pending.extend(value)
        forbidden = (state, *vars(state).values(), state.dynamic["payload"],
                     state.dynamic["payload"].state, state.dynamic_errors["payload"], state.forces["payload"])
        self.assertTrue(owners)
        self.assertTrue(any(owner is sim.model for owner in owners))
        self.assertFalse(any(owner is old for owner in owners for old in forbidden))
        copied = deepcopy(state)
        self.assertIsNot(copied, state)
        self.assertIsNot(copied.dynamic_cells, state.dynamic_cells)
        self.assertIs(copied.dynamic_cells["payload"].lineage, proof.lineage)
        self.assertEqual(transfer.source_sizes(sim, copied, "payload", END, F(1, 4)),
                         transfer.source_sizes(sim, state, "payload", END, F(1, 4)))

    def test_planning_observation_hooks_retain_the_exact_source_method_authority(self):
        class Planner(ReachSimulator):
            def _check_object_pose(self, pose):
                self.pose_ops.ensure_finite(pose)

            def snapshot(self, time, side):
                self._kinematics(time, self.state)
                return {}

        built = compile_construction(release_bundle())
        sim = Planner(built.model, work=built.reach_work)
        sim.advance(END, "after")
        self.assertIsInstance(sim.state.dynamic_cells["payload"], transfer.CellAnchor)
        self.assertGreater(sim.work.counts.get("transfer_release_capture", 0), 0)
        self.assertGreater(sim.work.counts.get("transfer_anchor_publish", 0), 0)

        class Foreign(ReachSimulator):
            def _dynamic_kinematics(self, *args, **kwargs):
                return super()._dynamic_kinematics(*args, **kwargs)

        for kind, shadow in ((Foreign, False), (ReachSimulator, True)):
            built = compile_construction(release_bundle())
            sim = kind(built.model, work=built.reach_work)
            sim.advance(END, "before")
            if shadow:
                sim._coordinate = sim._coordinate
            self.assertIsNone(transfer.first_release(sim, sim.state, "payload", END))
            self.assertFalse(sim.state.dynamic_cells)

    def test_inflight_source_class_and_inherited_method_replacement_are_rejected(self):
        class First(ReachSimulator):
            pass

        class Second(ReachSimulator):
            pass

        for change in ("class", "method"):
            built = compile_construction(release_bundle())
            sim = First(built.model, work=built.reach_work)
            sim.advance(END, "before")
            captured = transfer.first_release(sim, sim.state, "payload", END)
            self.assertIsNotNone(captured)
            check, changed_once = sim.work.external_check, []

            def mutate():
                if check is not None:
                    check()
                if changed_once:
                    return
                changed_once.append(True)
                if change == "class":
                    sim.__class__ = Second
                else:
                    First._coordinate = lambda *args, **kwargs: (0., 0.)

            sim.work.external_check = mutate
            try:
                with self.subTest(change=change), self.assertRaises(ReachAdmissionError):
                    captured.evaluate()
                self.assertTrue(changed_once)
                self.assertFalse(sim.state.dynamic_cells)
            finally:
                if "_coordinate" in vars(First):
                    del First._coordinate

    def test_descriptors_cannot_disguise_source_methods_or_context_owners(self):
        calls = []

        class MethodDescriptor:
            def __get__(self, instance, owner):
                calls.append("method")
                return ReachSimulator._coordinate if instance is None else lambda *args: (99., 0.)

        class OwnerDescriptor:
            def __get__(self, instance, owner):
                calls.append("owner")
                return None if instance is None else object.__getattribute__(instance, "__dict__")["model"]

            def __set__(self, instance, value):
                object.__getattribute__(instance, "__dict__")["model"] = value

        class HiddenMethod(ReachSimulator):
            _coordinate = MethodDescriptor()

        class HiddenOwner(ReachSimulator):
            model = OwnerDescriptor()

        for kind in (HiddenMethod, HiddenOwner):
            sim = simulator()
            sim.advance(END, "before")
            sim.__class__ = kind
            with self.subTest(kind=kind.__name__):
                self.assertIsNone(transfer.first_release(sim, sim.state, "payload", END))
                self.assertFalse(sim.state.dynamic_cells)
                self.assertEqual(calls, [])

    def test_first_release_uses_copied_operands_during_a_transient_source_mutation(self):
        sim = simulator()
        sim.advance(END, "before")
        captured = transfer.first_release(sim, sim.state, "payload", END)
        self.assertIsNotNone(captured)
        expected = captured.evaluate()
        original, calls, check = sim.model.actions["turn"].vector, 0, sim.work.external_check
        def transient():
            nonlocal calls
            if check is not None:
                check()
            calls += 1
            if calls == 2:
                sim.model.actions["turn"].vector = (0., 0., 9.)
            elif calls == 7:
                sim.model.actions["turn"].vector = original
        sim.work.external_check = transient
        actual = captured.evaluate()
        self.assertGreater(calls, 7)
        self.assertEqual(actual, expected)
        self.assertFalse(sim.state.dynamic_cells)

    def test_persistent_ancestry_claim_topology_and_callback_owner_changes_are_rejected(self):
        for name in ("claim", "topology", "root_initial", "reach_source", "owner"):
            sim = simulator()
            sim.advance(END, "before")
            captured = transfer.first_release(sim, sim.state, "payload", END)
            if name == "claim":
                sim.state.claims.pop(("rig", "orientation"))
            elif name == "topology":
                sim.model.sites["payload.origin"].owner = "rig"
            elif name == "root_initial":
                sim.state.actions["travel"].initial = (1., 0., 0.)
            elif name == "reach_source":
                reach = sim.model.actions["reach"].reach
                object.__setattr__(reach, "target_m", (1., 0., 0.))
            else:
                sim.pose_ops.work = ReachExecutionWork()
            with self.subTest(change=name), self.assertRaises(ReachAdmissionError):
                captured.evaluate()
            self.assertFalse(sim.state.dynamic_cells)

    def test_dynamic_proof_rejects_every_changed_current_numeric_context(self):
        for name in ("gravity", "force", "error", "anchor", "projection", "proof", "model", "state", "owner", "method", "cap"):
            sim = simulator()
            sim.advance(END, "after")
            state, proof, check, changed_once = sim.state, sim.state.dynamic_cells["payload"], sim.work.external_check, []
            original_charge = sim.work.charge
            def mutate():
                if check is not None:
                    check()
                if changed_once:
                    return
                changed_once.append(True)
                if name == "gravity":
                    sim.model.gravity = (0., 0., 1.)
                elif name == "force":
                    force = next(iter(state.forces["payload"].active.values()))
                    object.__setattr__(force.payload, "force_world_n", (3., 0., 0.))
                elif name == "error":
                    state.dynamic_errors["payload"] = replace(state.dynamic_errors["payload"], position_m=F(0))
                elif name == "anchor":
                    state.dynamic["payload"].time += F(1, 16)
                elif name == "projection":
                    state.dynamic["payload"].state._projection["position"] = (99., 0., 0.)
                elif name == "proof":
                    state.dynamic_cells["payload"] = replace(proof, position_size=F(0))
                elif name == "model":
                    sim.model = deepcopy(sim.model)
                elif name == "state":
                    sim.state = deepcopy(sim.state)
                elif name == "owner":
                    sim.pose_ops.work = ReachExecutionWork()
                elif name == "method":
                    sim._coordinate = sim._coordinate
                else:
                    sim.work.max_operand_bits = 32767
            def charge(kind="checkpoint", amount=1):
                if kind == "transfer_dynamic_publish":
                    sim.work.external_check = mutate
                return original_charge(kind, amount)
            with self.subTest(change=name), patch.object(sim.work, "charge", side_effect=charge):
                with self.assertRaises(ReachAdmissionError):
                    transfer.source_sizes(sim, state, "payload", END, F(1, 4))
            self.assertTrue(changed_once)

    def test_cancelled_publication_rolls_back_the_complete_boundary_and_new_metadata(self):
        sim = simulator()
        sim.advance(END, "before")
        initial, published, marker = deepcopy(sim.state), [], RuntimeError("cancel release proof publication")
        original = transfer._publish
        def publish(*args, **kwargs):
            published.append(args[1])
            check = sim.work.external_check
            def cancel():
                if check is not None:
                    check()
                raise marker
            sim.work.external_check = cancel
            return original(*args, **kwargs)
        with patch.object(transfer, "_publish", side_effect=publish):
            with self.assertRaises(RuntimeError) as caught:
                sim.advance(END, "after")
        self.assertIs(caught.exception, marker)
        self.assertEqual(sim.state, initial)
        self.assertTrue(published)
        self.assertTrue(all(not state.dynamic_cells for state in published))
        self.assertFalse(sim.incoming_releases)

    def test_reentrant_readonly_proofs_use_separate_copied_operands(self):
        sim = simulator()
        sim.advance(END, "after")
        expected = transfer.source_sizes(sim, sim.state, "payload", END, F(1, 4))
        proof, check, calls, nested = sim.state.dynamic_cells["payload"], sim.work.external_check, 0, []
        def reenter():
            nonlocal calls
            if check is not None:
                check()
            calls += 1
            if calls == 4:
                nested.append(transfer.source_sizes(sim, sim.state, "payload", END, F(1, 4)))
        sim.work.external_check = reenter
        actual = transfer.source_sizes(sim, sim.state, "payload", END, F(1, 4))
        self.assertEqual(actual, expected)
        self.assertEqual(nested, [expected])
        self.assertIs(sim.state.dynamic_cells["payload"], proof)

    def test_captured_dynamic_recording_binds_the_complete_transfer_proof(self):
        from test_reach_recording_captured_roots import begin, cursors
        from ontokin.reach_phase import phase_bounds
        sim = simulator()
        sim.advance(END, "after")
        end = F(1, 4)
        all_paths = tuple(path + ".frame" for path in sim.model.objects)
        moving = sim.recording_moving_frames(sim.state, all_paths)
        paths = tuple(path for path in all_paths if path in moving)
        bounds = phase_bounds(sim, END, end, sim.state, selected_frames=paths, recording_proof=True)
        fixture = sim, paths, bounds, moving, object(), (END, end)
        times = (F(5, 32), F(3, 16))
        phase = begin(fixture, times)
        self.assertIsNotNone(phase)
        previous = cursors(sim.work)
        phase.sample(times[0])
        proof = sim.state.dynamic_cells["payload"]
        sim.state.dynamic_cells["payload"] = replace(proof, position_size=proof.position_size + 1)
        phase.sample(times[1])
        with self.assertRaises(ReachAdmissionError):
            phase.finish()
        self.assertEqual(cursors(sim.work), previous)

    def test_unsupported_native_anchor_cannot_hide_its_retained_stale_proof(self):
        from test_reach_recording_captured_dynamic import dynamic_fixture
        from test_reach_recording_captured_roots import begin, cursors
        for change in ("nonplanar_spin", "nonplanar_rotation"):
            fixture = dynamic_fixture()
            sim = fixture[0]
            anchor = sim.state.dynamic["payload"]
            proof = sim.state.dynamic_cells["payload"]
            if change == "nonplanar_spin":
                anchor.state = replace(anchor.state, exact_omega=(F(1), F(0), F(0)))
            else:
                anchor.state = replace(anchor.state, rotation=replace(anchor.state.rotation,
                    components=(F(1), F(1), F(0), F(0))))
            before = sim.work.counts.get("recording_captured_phase_clock", 0)
            previous = cursors(sim.work)
            with self.subTest(change=change), self.assertRaises(ReachAdmissionError):
                begin(fixture, (F(17, 8), F(9, 4)))
            self.assertEqual(before, sim.work.counts.get("recording_captured_phase_clock", 0))
            self.assertEqual(cursors(sim.work), previous)
            self.assertIs(sim.state.dynamic_cells["payload"], proof)


class ReleaseCellExportTests(unittest.TestCase):
    def test_complete_short_release_passes_unchanged_independent_certificate_checks(self):
        built = compile_construction(release_bundle())
        options = ExportOptions(end=END, fps=1, helpers=False)
        observed, original = [], reach_conformance._CertificateBatch.add
        def observe(batch, row, width, stored_width, minima, magnitude):
            observed.append((deepcopy(row), dict(minima)))
            return original(batch, row, width, stored_width, minima, magnitude)
        with patch.object(reach_conformance._CertificateBatch, "add", observe):
            result = export_glb(built.model, options=options,
                               target_contract="ontokin.glb/0.6", work=built.reach_work)
        self.assertEqual(result.report["validation"]["status"], "passed")
        for category in ("transfer_release_capture", "transfer_anchor_publish", "transfer_dynamic_publish"):
            self.assertGreater(built.reach_work.counts.get(category, 0), 0,
                               "The actual recording planner must use the admitted release proof.")
        self.assertEqual(built.reach_work.max_operations, 100000)
        self.assertLessEqual(built.budget.operations, 100000)
        self.assertTrue(observed)
        for row, minima in observed:
            for quantity in ("source_numeric_position_bound_m", "source_numeric_rotation_bound_rad"):
                self.assertGreaterEqual(F(row[quantity]), minima[quantity])
        decoded = read_glb(result.data, target_contract="ontokin.glb/0.6")
        quantity = "source_numeric_position_bound_m"
        row, minima = max((item for item in observed if item[0]["carrier"]["path"] == "payload"),
                          key=lambda item: item[0]["right_key_index"])
        document = deepcopy(decoded.document)
        records = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
        selected = next(value for value in records if value["carrier"] == row["carrier"]
                        and value["left_key_index"] == row["left_key_index"])
        selected[quantity] = math.nextafter(float(minima[quantity]), 0.)
        self.assertLess(F(selected[quantity]), minima[quantity])
        forged = replace_document(document, decoded.binary)
        self.assertEqual(read_glb(forged, target_contract="ontokin.glb/0.6").binary, decoded.binary)
        with self.assertRaises(OntoKinError) as caught:
            reach_conformance.validate_reach_export(forged, built.model, options=options, work=ReachExecutionWork())
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-CERTIFICATE")
        self.assertEqual(caught.exception.diagnostic.details["quantity"], quantity)


if __name__ == "__main__":
    unittest.main()
