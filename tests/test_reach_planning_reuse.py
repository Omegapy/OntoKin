"""Prefix planning shares pure metadata, never source state or public outputs."""
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import fields, is_dataclass
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_export
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_runtime import ReachSimulator
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def ordinary_planning(stack):
    selected = reach_export._PrefixFrameSelection.selected
    stack.enter_context(patch.object(reach_export._UnchangedBoundaryProjection,
                                     "capture", return_value=None))
    stack.enter_context(patch.object(reach_export._PrefixFrameSelection, "selected",
        lambda _, simulator: selected(reach_export._PrefixFrameSelection(), simulator)))


def plan(case, end, *, reuse=True, check=None):
    compiled = compile_construction(source_case(case), check=check)
    with ExitStack() as stack:
        if not reuse:
            ordinary_planning(stack)
        result = reach_export.reach_prefix_plan(compiled.model, end, work=compiled.reach_work)
    return compiled, result


def admitted_state_value(simulator, state):
    """Compare state values after retaining each proof's actual source owner.

    Independently compiled models deliberately have different strong owner
    tokens. First admit every cell against its own current source, then retain
    each token's complete source roles and alias relationships in the value
    comparison. No production identity check or numeric proof field is removed.
    """
    from ontokin import reach_transfer_bounds as transfer

    owners = {}
    if state.dynamic_cells:
        for path, proof in state.dynamic_cells.items():
            transfer._source_guard(simulator, state, path, proof, charged=False)
        lineage = transfer._model_snapshot(simulator)[1]

        def owner_roles(value, path=(), depth=0):
            if depth > 24:
                raise AssertionError("The source-owner receipt exceeded its original depth bound")
            if type(value) is transfer._OwnerRef:
                if len(value) != 1:
                    raise AssertionError("Malformed strong source owner")
                owner = value[0]
                saved, roles = owners.setdefault(id(owner), (owner, []))
                if saved is not owner:
                    raise AssertionError("A source owner address was reused")
                roles.append(path)
            elif type(value) is tuple:
                for index, part in enumerate(value):
                    owner_roles(part, (*path, index), depth + 1)

        owner_roles(lineage)

    remaining = 250000

    def value(item, depth=0):
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 64:
            raise AssertionError("The state comparison exceeded its bounded traversal")
        kind = type(item)
        name = (kind.__module__, kind.__qualname__)
        if kind is transfer._OwnerRef:
            if len(item) != 1:
                raise AssertionError("Malformed strong source owner")
            owner = item[0]
            saved = owners.get(id(owner))
            if saved is None or saved[0] is not owner:
                raise AssertionError("A proof owner is outside its admitted current source")
            return (name, (type(owner).__module__, type(owner).__qualname__), tuple(saved[1]))
        if item is None or kind in (bool, int, str):
            return name, item
        if kind is float:
            return name, item.hex()
        if kind is F:
            return name, value(item.numerator, depth + 1), value(item.denominator, depth + 1)
        if is_dataclass(item):
            # Match the original dataclass equality contract. The excluded
            # PoseValue owner/projection caches were never state-value fields.
            return name, tuple((field.name, value(getattr(item, field.name), depth + 1))
                               for field in fields(item) if field.compare)
        if kind is dict:
            return name, tuple((value(key, depth + 1), value(part, depth + 1))
                               for key, part in item.items())
        if isinstance(item, tuple) or kind is list:
            return name, tuple(value(part, depth + 1) for part in item)
        if kind in (set, frozenset):
            return name, frozenset(value(part, depth + 1) for part in item)
        raise AssertionError("Unexpected private state value: " + kind.__qualname__)

    return value(state)


class ReachPlanningReuseTests(unittest.TestCase):
    def test_complete_prefixes_equal_ordinary_projections_and_phase_selection(self):
        from ontokin import reach_transfer_bounds as transfer
        from ontokin.reach_numeric import ReachAdmissionError

        for case, end in (("P01", F(1, 4)), ("P01", F(3)), ("P05", F(1)),
                          ("P16", F(3)), ("L04", F(1, 4)), ("P23", F(3))):
            with self.subTest(case=case, end=end):
                baseline, expected = plan(case, end, reuse=False)
                compiled, actual = plan(case, end)
                self.assertEqual(actual.boundaries, expected.boundaries)
                self.assertEqual(actual.boundary_records, expected.boundary_records)
                self.assertEqual(actual.phases, expected.phases)
                self.assertEqual(len(actual.phase_states), len(expected.phase_states))
                before_comparison = (compiled.budget.operations, baseline.budget.operations,
                                     compiled.reach_work.record(), baseline.reach_work.record())
                for current, ordinary in (*zip(actual.phase_states, expected.phase_states),
                                          (actual.final_state, expected.final_state)):
                    self.assertEqual(admitted_state_value(actual.simulator, current),
                                     admitted_state_value(expected.simulator, ordinary))
                    # Equal physical/source values never confer authority to
                    # borrow a proof from another independently compiled model.
                    for simulator, foreign in ((actual.simulator, ordinary),
                                               (expected.simulator, current)):
                        for path, proof in foreign.dynamic_cells.items():
                            with self.assertRaisesRegex(ReachAdmissionError, "changed source"):
                                transfer._source_guard(simulator, foreign, path, proof, charged=False)
                self.assertEqual(before_comparison,
                    (compiled.budget.operations, baseline.budget.operations,
                     compiled.reach_work.record(), baseline.reach_work.record()))
                self.assertLess(compiled.budget.operations, baseline.budget.operations)
                self.assertLessEqual(compiled.budget.operations, 100000)
                self.assertLessEqual(len(compiled.reach_work._cache), 256)
                if case in ("P01", "P23") and end == 3:
                    self.assertEqual(compiled.reach_work.counts["recording_phase_frame"],
                                     len(compiled.model.objects) + len(compiled.model.joints))
                    self.assertEqual(compiled.reach_work.counts["recording_phase_selection_reuse"], 1)
                    self.assertIn("recording_boundary_side", compiled.reach_work.counts)

    def test_actual_glb_bytes_with_helpers_equal_ordinary_planning(self):
        outputs = []
        for reuse in (False, True):
            compiled = compile_construction(source_case("P01"))
            with ExitStack() as stack:
                if not reuse:
                    ordinary_planning(stack)
                result = export_glb(compiled.model,
                    options=ExportOptions(end=F(1, 4), fps=1, helpers=True),
                    target_contract="ontokin.glb/0.6", work=compiled.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            outputs.append(result.data)
        self.assertEqual(outputs[0], outputs[1])

    def test_before_after_outputs_are_fresh_complete_graphs(self):
        compiled, result = plan("P01", F(1, 4))
        record = result.boundary_records[-1]
        original = deepcopy(record)
        for category in ("joint_states", "action_states", "pose_authorities", "impulse_states",
                         "force_states", "reach_states"):
            before, after = record[category + "_before"], record[category + "_after"]
            self.assertIsNot(before, after)
            for path in before:
                self.assertIsNot(before[path], after[path])
        before = record["reach_states_before"]["reach"]["current"]["value"]
        after = record["reach_states_after"]["reach"]["current"]["value"]
        self.assertEqual(before["observation"]["side"], "before")
        self.assertEqual(after["observation"]["side"], "after")
        after["joint_coordinates_rad"][0] = 999.0
        path = next(iter(record["force_states_after"]))
        record["force_states_after"][path]["active"].append({"external": True})
        self.assertEqual(record["reach_states_before"], original["reach_states_before"])
        self.assertEqual(record["force_states_before"], original["force_states_before"])
        self.assertEqual(compiled.model.program_revision, result.simulator.model.program_revision)
        self.assertNotIn({"external": True}, result.simulator.state.forces[path].active.values())

    def test_callback_in_place_mutation_after_before_projection_forces_fresh_after(self):
        outputs = []
        original = ReachSimulator.advance
        for reuse in (False, True):
            live = {"simulator": None, "armed": False, "changed": False}
            def check():
                if live["armed"] and not live["changed"]:
                    simulator = live["simulator"]
                    path = next(iter(simulator.state.impulses))
                    simulator.state.impulses[path].applied_count += 1
                    live["changed"] = True
            def advance(simulator, time, side="after"):
                live["simulator"] = simulator
                live["armed"] = time == F(1, 4) and side == "after"
                return original(simulator, time, side)
            with patch.object(ReachSimulator, "advance", advance):
                _, result = plan("P01", F(1, 4), reuse=reuse, check=check)
            self.assertTrue(live["changed"])
            record = result.boundary_records[-1]
            path = next(iter(record["impulse_states_before"]))
            self.assertEqual(record["impulse_states_before"][path]["applied_count"], 0)
            self.assertEqual(record["impulse_states_after"][path]["applied_count"], 1)
            outputs.append(result.boundary_records)
        self.assertEqual(outputs[0], outputs[1])

    def test_receipt_rejects_mutation_of_previously_visited_state_field(self):
        compiled = compile_construction(source_case("P23"))
        simulator = ReachSimulator(compiled.model, work=compiled.reach_work)
        simulator.advance(F(0), "after")
        calls = 0
        path = next(iter(simulator.state.modes))
        original = simulator.state.modes[path]
        def mutate():
            nonlocal calls
            calls += 1
            if calls == 2:
                simulator.state.modes[path] = "changed_during_receipt"
        with patch.object(simulator.work, "external_check", mutate):
            receipt = reach_export._UnchangedBoundaryProjection.capture(simulator)
        self.assertGreaterEqual(calls, 2)
        self.assertIsNone(receipt)
        simulator.state.modes[path] = original

    def test_after_history_callback_model_mutations_use_fresh_source_fields(self):
        outputs = []
        original = ReachSimulator.recording_boundary
        for reuse in (False, True):
            live = {"simulator": None, "armed": False, "changed": False}
            def check():
                if live["armed"] and not live["changed"]:
                    simulator = live["simulator"]
                    joint = next(iter(simulator.model.joints.values()))
                    joint.limits = (-2.0, 2.0)
                    simulator.model.actions["reach"].duration = F(4)
                    live["changed"] = True
            def boundary(simulator, time, side, **kwargs):
                live["simulator"] = simulator
                # Mutation happens inside an actual after-side callback, after
                # both ordinary advances and the completed before projection.
                live["armed"] = time == F(1, 4) and side == "after"
                return original(simulator, time, side, **kwargs)
            with patch.object(ReachSimulator, "recording_boundary", boundary):
                _, result = plan("P01", F(1, 4), reuse=reuse, check=check)
            self.assertTrue(live["changed"])
            record = result.boundary_records[-1]
            joint = next(iter(record["joint_states_after"]))
            self.assertEqual(record["joint_states_after"][joint]["limits"], [-2.0, 2.0])
            self.assertEqual(record["action_states_after"]["reach"]["duration_seconds"], "4")
            self.assertEqual(record["reach_states_after"]["reach"]["duration_seconds"], "4")
            self.assertNotEqual(record["joint_states_before"][joint]["limits"], [-2.0, 2.0])
            outputs.append(result.boundary_records)
        self.assertEqual(outputs[0], outputs[1])

    def test_callback_during_output_copy_rebuilds_the_current_after_state(self):
        live = {"armed": False, "changed": False, "simulator": None}
        def check():
            if live["armed"] and not live["changed"]:
                simulator = live["simulator"]
                path = next(iter(simulator.state.impulses))
                simulator.state.impulses[path].applied_count += 1
                live["changed"] = True
        compiled = compile_construction(source_case("P01"), check=check)
        simulator = ReachSimulator(compiled.model, work=compiled.reach_work)
        live["simulator"] = simulator
        simulator.advance(F(1, 4), "before")
        receipt = reach_export._UnchangedBoundaryProjection.capture(simulator)
        self.assertIsNotNone(receipt)
        before = simulator.recording_boundary(F(1, 4), "before")
        simulator.advance(F(1, 4), "after")
        original = simulator._snapshot_data
        def materialize(value, time, side):
            result = original(value, time, side)
            if side == "after" and not live["changed"]:
                live["armed"] = True
                simulator.work.tick()
            return result
        with patch.object(simulator, "_snapshot_data", materialize):
            after = simulator.recording_boundary(F(1, 4), "after", _reuse=(receipt, before))
        self.assertTrue(live["changed"])
        path = next(iter(simulator.state.impulses))
        self.assertEqual(before["objects"][path]["impulses"]["applied_count"], 0)
        self.assertEqual(after["objects"][path]["impulses"]["applied_count"], 1)
        self.assertEqual(after, simulator.recording_boundary(F(1, 4), "after"))

    def test_changed_live_domain_and_unsupported_state_do_not_reuse(self):
        compiled = compile_construction(source_case("P01"))
        simulator = ReachSimulator(compiled.model, work=compiled.reach_work)
        simulator.advance(F(0), "after")
        receipt = reach_export._UnchangedBoundaryProjection.capture(simulator)
        self.assertIsNotNone(receipt)
        simulator.work.max_operand_bits = 128
        self.assertFalse(receipt.matches(check=True))
        self.assertIsNone(reach_export._UnchangedBoundaryProjection.capture(simulator))
        simulator.work.max_operand_bits = 32768
        original = simulator.work.charge
        calls = 0
        def narrow(kind="checkpoint", amount=1):
            nonlocal calls
            if kind == "recording_boundary_state_block":
                calls += 1
                simulator.work.max_operand_bits = 128 if calls == 1 else 32768
            return original(kind, amount)
        with patch.object(simulator.work, "charge", side_effect=narrow):
            self.assertFalse(receipt.matches(check=True))
        self.assertEqual(calls, 1)
        self.assertEqual(simulator.work.max_operand_bits, 128)
        simulator.work.max_operand_bits = 32768
        simulator.state.actions["reach"].terminal = {"custom": object()}
        self.assertIsNone(reach_export._UnchangedBoundaryProjection.capture(simulator))
        simulator.state.actions["reach"].terminal = {}
        simulator.state.actions["reach"].terminal["cycle"] = simulator.state.actions["reach"].terminal
        self.assertIsNone(reach_export._UnchangedBoundaryProjection.capture(simulator))

    def test_after_side_keeps_complete_unselected_frame_finiteness_check(self):
        original = ReachSimulator._kinematics
        marker = RuntimeError("after-side unselected site is invalid")
        def kinematics(simulator, time, state):
            objects, frames = original(simulator, time, state)
            if time == F(1, 4) and getattr(simulator, "_inject_after_frame", False):
                class InvalidFrame:
                    @property
                    def position(self):
                        raise marker
                return objects, {**frames, "unselected.site.frame": InvalidFrame()}
            return objects, frames
        original_boundary = ReachSimulator.recording_boundary
        def boundary(simulator, time, side, **kwargs):
            simulator._inject_after_frame = side == "after"
            return original_boundary(simulator, time, side, **kwargs)
        with patch.object(ReachSimulator, "_kinematics", kinematics), \
                patch.object(ReachSimulator, "recording_boundary", boundary):
            with self.assertRaises(RuntimeError) as caught:
                plan("P01", F(1, 4))
        self.assertIs(caught.exception, marker)

    def test_receipt_cancellation_keeps_original_exception_and_state(self):
        compiled = compile_construction(source_case("P01"))
        simulator = ReachSimulator(compiled.model, work=compiled.reach_work)
        simulator.advance(F(0), "after")
        before = deepcopy(simulator.state)
        marker = RuntimeError("cancel endpoint ownership receipt")
        with patch.object(simulator.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                reach_export._UnchangedBoundaryProjection.capture(simulator)
        self.assertIs(caught.exception, marker)
        self.assertIs(simulator.work.callback_error, marker)
        self.assertEqual(simulator.state, before)

    def test_selection_tracks_actual_topology_and_binds_model_and_work(self):
        compiled = compile_construction(source_case("P01"))
        simulator = ReachSimulator(compiled.model, work=compiled.reach_work)
        selector = reach_export._PrefixFrameSelection()
        first = selector.selected(simulator)
        self.assertIs(first, selector.selected(simulator))
        joint = next(iter(simulator.model.joints.values()))
        joint.parent = "changed.parent"
        changed = selector.selected(simulator)
        self.assertIn("changed.parent.frame", changed)
        self.assertIsNot(first, changed)
        other = compile_construction(source_case("P01"))
        simulator.model, simulator.work = other.model, other.reach_work
        self.assertEqual(selector.selected(simulator), first)
        self.assertIs(selector.owner[0], other.model)
        self.assertIs(selector.owner[1], other.reach_work)

    def test_cold_selection_rebuilds_an_earlier_parent_changed_by_a_later_callback(self):
        compiled = compile_construction(source_case("P01"))
        simulator = ReachSimulator(compiled.model, work=compiled.reach_work)
        selector = reach_export._PrefixFrameSelection()
        joint = next(iter(simulator.model.joints.values()))
        original = simulator.work.charge
        visited = 0
        trigger = len(simulator.model.objects) + 2

        def charge(kind="checkpoint", amount=1):
            nonlocal visited
            if kind == "recording_phase_frame":
                visited += 1
                if visited == trigger:
                    joint.parent = "changed.parent"
            return original(kind, amount)

        with patch.object(simulator.work, "charge", charge):
            selected = selector.selected(simulator)
        self.assertGreater(visited, len(simulator.model.objects) + len(simulator.model.joints))
        self.assertIn("changed.parent.frame", selected)
        self.assertEqual(selected, reach_export._PrefixFrameSelection().selected(simulator))
        self.assertIs(selected, selector.selected(simulator))

    def test_wrong_clock_or_side_receipt_rebuilds_current_endpoint(self):
        for wrong_clock in (True, False):
            with self.subTest(wrong_clock=wrong_clock):
                compiled = compile_construction(source_case("P01"))
                simulator = ReachSimulator(compiled.model, work=compiled.reach_work)
                simulator.advance(F(1, 4), "before")
                receipt = reach_export._UnchangedBoundaryProjection.capture(simulator)
                self.assertIsNotNone(receipt)
                before = simulator.recording_boundary(F(1, 4), "before")
                time = F(1, 2) if wrong_clock else F(1, 4)
                if not wrong_clock:
                    before["side"] = "after"
                simulator.advance(time, "after")
                with patch.object(simulator, "_reach_map", wraps=simulator._reach_map) as project:
                    after = simulator.recording_boundary(time, "after", _reuse=(receipt, before))
                self.assertGreater(project.call_count, 0)
                self.assertEqual(after, simulator.recording_boundary(time, "after"))


if __name__ == "__main__":
    unittest.main()
