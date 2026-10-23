"""Selected release ancestry preserves complete independent state transfer."""
from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_reference import ReachReference, ReferenceError, build_reference
from reach_agent_support import source_case
from test_reach_phase import changed


@contextmanager
def complete_release_maps(enabled=True):
    """Run the preceding full-map algorithm only inside each release."""
    if not enabled:
        yield
        return
    release = ReachReference._release

    def complete(reference, *args, **kwargs):
        pose_map = reference._pose_map

        def all_frames(*values, **options):
            options["selected"] = None
            return pose_map(*values, **options)

        with patch.object(reference, "_pose_map", all_frames):
            return release(reference, *args, **kwargs)

    with patch.object(ReachReference, "_release", complete):
        yield


def reference(bundle, *, complete=False, end=F(4), mode="recording"):
    built = compile_construction(bundle)
    with complete_release_maps(complete):
        result = build_reference(built.model, end=end, mode=mode, work=built.reach_work)
    return built, result


def offset_bundle():
    bundle = changed(source_case("P16"), 'scene Demo @ "demo" {',
        'class OffsetPayload @ "offset-payload" extends shapes.Payload {\n'
        '    public site attachment @ "attachment" {\n'
        '        pose = pose(self.frame, vec3(0.1[m], -0.2[m], 0.03[m]),\n'
        '                    axis_angle(vec3(1, 0, 0), 15[deg]));\n'
        '        interface = "rigid.origin";\n'
        '        size = 0[m];\n'
        '    }\n'
        '}\n\nscene Demo @ "demo" {')
    bundle = changed(bundle, 'object payload @ "payload": shapes.Payload {}',
                     'object payload @ "payload": OffsetPayload {}')
    return changed(bundle, 'child = payload.origin;', 'child = payload.attachment;')


def multiple_bundle():
    bundle = changed(source_case("P16"), 'object payload @ "payload": shapes.Payload {}',
        'object payload @ "payload": shapes.Payload {}\n'
        '    object second @ "second": shapes.Payload {}\n'
        '    joint second_grip @ "second-grip": grip {\n'
        '        parent = rig.arm.forearm.tip;\n'
        '        child = second.origin;\n'
        '    }')
    return changed(bundle, 'release grip using incoming;',
                   'release grip using incoming; release second_grip using incoming;')


class IndependentReleaseSelectionTests(unittest.TestCase):
    def assert_same_ledger(self, actual, expected):
        self.assertEqual(actual.boundaries, expected.boundaries)
        self.assertEqual(actual._before, expected._before)
        self.assertEqual(actual._after, expected._after)
        self.assertEqual(actual._release_records, expected._release_records)
        self.assertEqual(actual._history_weight, expected._history_weight)
        self.assertEqual(actual.model.program_revision, expected.model.program_revision)

    def test_original_release_and_force_ledger_equal_complete_maps(self):
        for mode in ("recording", "observation"):
            with self.subTest(mode=mode):
                built, actual = reference(source_case("P16"), mode=mode)
                baseline, expected = reference(source_case("P16"), complete=True, mode=mode)
                self.assert_same_ledger(actual, expected)
                self.assertLess(built.budget.operations, baseline.budget.operations)
                self.assertLess(built.reach_work.operations, baseline.reach_work.operations)
                self.assertEqual(built.reach_work.operations, sum(built.reach_work.counts.values()))
                self.assertEqual(built.reach_work.max_operations, 100000)
                self.assertLessEqual(len(actual.a.cache), 256)
                for time, side in ((F(2), "before"), (F(2), "after"), (F(3), "after")):
                    self.assertEqual(actual.pose_enclosure("payload", time, side),
                                     expected.pose_enclosure("payload", time, side))
                    self.assertEqual(actual.point_phase("payload", time, side),
                                     expected.point_phase("payload", time, side))

    def test_complete_source_history_retains_every_nonancestor_object_and_site(self):
        _, actual = reference(source_case("P16"), end=F(2))
        _, expected = reference(source_case("P16"), complete=True, end=F(2))
        self.assertEqual(actual.boundary_states(), expected.boundary_states())
        for path in ("rig.column.frame", "rig.tool.frame", "rig.arm.pivot.frame"):
            self.assertEqual(actual.pose_enclosure(path, F(2)), expected.pose_enclosure(path, F(2)))
        record = actual._release_records[F(2)][0]
        self.assertTrue(record["reach_contributors"])
        self.assertEqual(record["target"]["path"], "payload")
        self.assertEqual(len(record["incoming_linear_velocity_world_m_per_s"]), 3)
        self.assertEqual(len(record["incoming_angular_velocity_world_rad_per_s"]), 3)

    def test_nonzero_child_transform_and_full_spatial_derivatives_equal_complete_maps(self):
        bundle = offset_bundle()
        _, actual = reference(bundle)
        _, expected = reference(bundle, complete=True)
        self.assert_same_ledger(actual, expected)
        anchor = actual._state_at(F(2), "after").dynamic["payload"]
        self.assertTrue(any(cell.lo != 0 or cell.hi != 0 for cell in anchor.actual.velocity))
        self.assertTrue(any(cell.lo != 0 or cell.hi != 0 for cell in anchor.actual.omega))
        self.assertTrue(any(cell.lo != 0 or cell.hi != 0 for cell in anchor.actual.orientation[1:3]))
        for time in (F(2), F(5, 2), F(3), F(4)):
            self.assertEqual(actual.pose_enclosure("payload", time), expected.pose_enclosure("payload", time))

    def test_two_releases_at_one_boundary_keep_separate_complete_anchors(self):
        bundle = multiple_bundle()
        built, actual = reference(bundle)
        baseline, expected = reference(bundle, complete=True)
        self.assert_same_ledger(actual, expected)
        rows = actual._release_records[F(2)]
        self.assertEqual([row["target"]["path"] for row in rows], ["payload", "second"])
        self.assertEqual([row["sequence_index"] for row in rows], [0, 1])
        self.assertIsNot(actual._state_at(F(2), "after").dynamic["payload"],
                         actual._state_at(F(2), "after").dynamic["second"])
        self.assertLess(built.budget.operations, baseline.budget.operations)

    def test_earlier_dependency_changes_and_duplicate_release_keep_source_failures(self):
        for replacement, message in (
            ("stop turn; release grip using incoming;", "Earlier statements changed"),
            ("release grip using incoming; release grip using incoming;", "requires an active grip"),
        ):
            bundle = changed(source_case("P16"), "release grip using incoming;", replacement)
            failures = []
            for complete in (False, True):
                with self.subTest(replacement=replacement, complete=complete), self.assertRaises(ReferenceError) as caught:
                    reference(bundle, complete=complete)
                self.assertEqual(caught.exception.code, "source_admission")
                self.assertIn(message, str(caught.exception))
                failures.append((caught.exception.code, str(caught.exception), caught.exception.details))
            self.assertEqual(failures[0], failures[1])

    def test_cancelled_actual_or_ideal_ancestry_preserves_committed_ledger(self):
        for ideal in (False, True):
            for complete in (False, True):
                built = compile_construction(source_case("P16"))
                marker = RuntimeError("cancel independent release ancestry")
                captured = []
                pose_map = ReachReference._pose_map

                def interrupt(reader, time, state, **options):
                    if time == F(2) and options.get("ideal") is ideal and not options.get("pose_only", False):
                        captured.append((reader, state, deepcopy(reader._state)))
                        check = built.reach_work.external_check

                        def cancel():
                            if check is not None:
                                check()
                            raise marker

                        built.reach_work.external_check = cancel
                    return pose_map(reader, time, state, **options)

                with self.subTest(ideal=ideal, complete=complete), \
                     patch.object(ReachReference, "_pose_map", interrupt), complete_release_maps(complete):
                    with self.assertRaises(RuntimeError) as caught:
                        build_reference(built.model, end=F(4), work=built.reach_work)
                self.assertIs(caught.exception, marker)
                self.assertIs(built.reach_work.callback_error, marker)
                self.assertEqual(len(captured), 1)
                reader, incoming, before = captured[0]
                self.assertIs(reader._state, incoming)
                self.assertEqual(reader._state, before)
                self.assertNotIn("payload", reader._state.dynamic)
                self.assertNotIn(F(2), reader._release_records)

    def test_narrowed_cap_during_ancestry_keeps_resource_failure_and_no_release(self):
        for ideal in (False, True):
            for complete in (False, True):
                built = compile_construction(source_case("P16"))
                captured = []
                pose_map = ReachReference._pose_map

                def narrow(reader, time, state, **options):
                    if time == F(2) and options.get("ideal") is ideal and not options.get("pose_only", False):
                        captured.append((reader, state, deepcopy(reader._state)))
                        check = built.reach_work.external_check

                        def lower():
                            if check is not None:
                                check()
                            built.reach_work.max_operand_bits = 128

                        built.reach_work.external_check = lower
                    return pose_map(reader, time, state, **options)

                with self.subTest(ideal=ideal, complete=complete), \
                     patch.object(ReachReference, "_pose_map", narrow), complete_release_maps(complete):
                    with self.assertRaises(ReferenceError) as caught:
                        build_reference(built.model, end=F(4), work=built.reach_work)
                self.assertEqual(caught.exception.code, "resource")
                self.assertEqual(built.reach_work.max_operand_bits, 128)
                self.assertEqual(len(captured), 1)
                reader, incoming, before = captured[0]
                self.assertIs(reader._state, incoming)
                self.assertEqual(reader._state, before)
                self.assertNotIn("payload", reader._state.dynamic)
                self.assertNotIn(F(2), reader._release_records)


if __name__ == "__main__":
    unittest.main()
