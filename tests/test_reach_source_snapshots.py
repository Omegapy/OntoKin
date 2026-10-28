"""Source-node cache signatures and builders retain the same actual operands."""
from contextlib import contextmanager
from fractions import Fraction as F
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ontokin.model import ActionModel, FollowModel, JointModel, ObjectModel, Pose, SiteModel
from ontokin.reach_numeric import MAX_OPERAND_BITS, MAX_OPERATIONS, ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_runtime import ReachSimulator, _ReachActionState, _ReachRunState


def fixture(kind, *, translated=False, moving=False):
    paths = ['root'] if kind == 'site' else ['root', 'child']
    if translated:
        paths += [f'unselected_{index}' for index in range(256)]
    objects = {path: ObjectModel(path, path, 'Part', (path,)) for path in paths}
    sites, follows, joints, actions = {}, {}, {}, {}
    if kind == 'site':
        source = sites['leaf'] = SiteModel('leaf', ('leaf',), 'root', Pose(position=(1., 0., 0.)))
        target = 'leaf.frame'
    elif kind == 'follow':
        source = follows['follow'] = FollowModel('follow', 'follow', ('follow',),
            'root.frame', 'child', Pose(position=(1., 0., 0.)))
        target = 'child.frame'
    else:
        sites['root_mount'] = SiteModel('root_mount', ('root_mount',), 'root', Pose())
        sites['child_mount'] = SiteModel('child_mount', ('child_mount',), 'child', Pose())
        source = joints['joint'] = JointModel('joint', 'joint', ('joint',), kind,
            'root_mount', 'child_mount', axis=(1., 0., 0.), initial=0.25)
        target = 'child.frame'
    model = SimpleNamespace(objects=objects, sites=sites, follows=follows, joints=joints,
        actions=actions, program_revision='source-snapshot-fixture', profile='planar-reach-0.1', span=None)
    state = _ReachRunState(modes={path: 'prescribed' for path in paths},
        positions={path: (0., 0., 0.) for path in paths},
        orientations={path: (1., 0., 0., 0.) for path in paths},
        coordinates={'joint': 0.25} if joints else {})
    if moving:
        actions['drive'] = ActionModel('drive', 'drive', ('drive',), 'tween', 'joint', F(1), goal=1.)
        state.actions['drive'] = _ReachActionState(status='running', initial=0., ideal_initial=F(0))
        state.claims[('joint', 'coordinate')] = 'drive'
    simulator = object.__new__(ReachSimulator)
    simulator.work = ReachExecutionWork()
    simulator.pose_ops = ReachPoseOps(simulator.work)
    simulator.model, simulator.state = model, state
    simulator.check = simulator._work_check
    simulator._pose_cache = {}
    simulator._pair_cache = {}
    simulator._derived_pose_cache = {}
    simulator._terminal_pose_context = None
    simulator._identity_pose = simulator.pose_ops.identity()
    return simulator, source, target


def resolve(simulator, target):
    return simulator._resolve_kinematics(F(1, 4), simulator.state,
        selected_frames=(target,))[1][target]


def node_key(simulator, kind, target, translated, key):
    if translated:
        return len(key) > 2 and key[0] == 'reach_source_translated_node' and key[2] == (
            kind if kind in {'site', 'follow'} else 'joint')
    path = target if kind == 'site' else target.removesuffix('.frame')
    return key == ('reach_source_pose', simulator.model.program_revision, path)


@contextmanager
def source_callbacks(simulator, kind, target, translated, *, lookup=None, insert=None):
    """Select real callback boundaries without replacing numeric/cache work."""
    work = simulator.work
    ordinary_lookup, ordinary_remember, ordinary_check = work.lookup, work.remember, work.external_check
    stage = None
    fired = set()
    hooks = {'lookup': lookup, 'insert': insert}

    def check():
        if ordinary_check is not None:
            ordinary_check()
        hook = hooks.get(stage)
        if hook is not None and stage not in fired:
            fired.add(stage)
            hook()

    def checked_lookup(key):
        nonlocal stage
        previous = stage
        stage = 'lookup' if node_key(simulator, kind, target, translated, key) else None
        try:
            return ordinary_lookup(key)
        finally:
            stage = previous

    def checked_remember(key, value, **kwargs):
        nonlocal stage
        previous = stage
        stage = 'insert' if node_key(simulator, kind, target, translated, key) else None
        try:
            return ordinary_remember(key, value, **kwargs)
        finally:
            stage = previous

    with patch.object(work, 'lookup', checked_lookup), patch.object(work, 'remember', checked_remember), \
            patch.object(work, 'external_check', check):
        yield fired


class ReachSourceSnapshotTests(unittest.TestCase):
    def assert_limits(self, simulator):
        work = simulator.work
        self.assertEqual((work.max_operations, work.max_operand_bits, work.max_cache_entries),
                         (MAX_OPERATIONS, MAX_OPERAND_BITS, 256))
        self.assertEqual(work.max_operations, 100000)
        self.assertLess(work.operations, work.max_operations)
        self.assertLessEqual(len(work._cache), work.max_cache_entries)

    def test_lookup_callback_cannot_build_changed_source_under_an_earlier_key(self):
        cases = (
            ('site', 'pose', Pose(position=(2., 0., 0.))),
            ('follow', 'offset', Pose(position=(2., 0., 0.))),
            ('hinge', 'axis', (0., 1., 0.)),
            ('slider', 'axis', (0., 1., 0.)),
            ('slider', 'kind', 'hinge'),
        )
        for translated in (False, True):
            for kind, field, changed in cases:
                with self.subTest(translated=translated, kind=kind, field=field):
                    simulator, source, target = fixture(kind, translated=translated)
                    fresh, fresh_source, fresh_target = fixture(kind, translated=translated)
                    original = getattr(source, field)
                    expected = resolve(fresh, fresh_target)
                    with source_callbacks(simulator, kind, target, translated,
                            lookup=lambda: setattr(source, field, changed)) as fired:
                        first = resolve(simulator, target)
                    self.assertEqual(fired, {'lookup'})
                    self.assertEqual(getattr(source, field), changed)
                    self.assertEqual(first, expected)
                    setattr(source, field, original)
                    simulator._invalidate()
                    self.assertEqual(resolve(simulator, target), expected)
                    # A later distinct source law still gets its own result.
                    setattr(source, field, changed)
                    setattr(fresh_source, field, changed)
                    simulator._invalidate()
                    fresh._invalidate()
                    self.assertEqual(resolve(simulator, target), resolve(fresh, fresh_target))
                    self.assert_limits(simulator)

    def test_transient_source_change_restored_at_publication_cannot_poison_a_key(self):
        for translated in (False, True):
            with self.subTest(translated=translated):
                simulator, source, target = fixture('site', translated=translated)
                fresh, _, fresh_target = fixture('site', translated=translated)
                expected = resolve(fresh, fresh_target)
                original, changed = source.pose, Pose(position=(2., 0., 0.))
                with source_callbacks(simulator, 'site', target, translated,
                        lookup=lambda: setattr(source, 'pose', changed),
                        insert=lambda: setattr(source, 'pose', original)) as fired:
                    first = resolve(simulator, target)
                self.assertEqual(fired, {'lookup', 'insert'})
                self.assertIs(source.pose, original)
                self.assertEqual(first, expected)
                simulator._invalidate()
                self.assertEqual(resolve(simulator, target), expected)
                self.assert_limits(simulator)

    def test_slider_callback_cannot_change_axis_between_position_and_velocity(self):
        for translated in (False, True):
            with self.subTest(translated=translated):
                simulator, source, target = fixture('slider', translated=translated, moving=True)
                fresh, _, fresh_target = fixture('slider', translated=translated, moving=True)
                expected = resolve(fresh, fresh_target)
                original_axis = source.axis
                ordinary_scale = simulator.pose_ops.scale
                armed = False
                changed = False

                def check():
                    nonlocal changed
                    if armed and not changed:
                        source.axis = (0., 1., 0.)
                        changed = True

                def scale(vector, factor):
                    nonlocal armed
                    armed = factor == F(1, 4) and not changed
                    try:
                        return ordinary_scale(vector, factor)
                    finally:
                        armed = False

                with patch.object(simulator.pose_ops, 'scale', scale), \
                        patch.object(simulator.work, 'external_check', check):
                    first = resolve(simulator, target)
                self.assertTrue(changed)
                self.assertEqual(expected.exact_position, (F(1, 4), F(0), F(0)))
                self.assertEqual(expected.exact_velocity, (F(1), F(0), F(0)))
                self.assertEqual(first, expected)
                source.axis = original_axis
                simulator._invalidate()
                self.assertEqual(resolve(simulator, target), expected)
                self.assert_limits(simulator)

    def test_source_lookup_cancellation_keeps_completed_node_entries(self):
        for translated in (False, True):
            for warm in (False, True):
                with self.subTest(translated=translated, warm=warm):
                    simulator, _, target = fixture('site', translated=translated)
                    if warm:
                        resolve(simulator, target)
                    before = {key: value for key, value in simulator.work._cache.items()
                              if node_key(simulator, 'site', target, translated, key)}
                    marker = RuntimeError('cancel source snapshot lookup')

                    def cancel():
                        raise marker

                    with source_callbacks(simulator, 'site', target, translated, lookup=cancel), \
                            self.assertRaises(RuntimeError) as caught:
                        resolve(simulator, target)
                    self.assertIs(caught.exception, marker)
                    self.assertIs(simulator.work.callback_error, marker)
                    after = {key: value for key, value in simulator.work._cache.items()
                             if node_key(simulator, 'site', target, translated, key)}
                    self.assertEqual(set(after), set(before))
                    for key, value in before.items():
                        self.assertIs(after[key], value)
                    self.assert_limits(simulator)

    def test_source_snapshot_keeps_the_live_operand_cap(self):
        for translated in (False, True):
            with self.subTest(translated=translated):
                simulator, _, target = fixture('site', translated=translated)
                resolve(simulator, target)
                with source_callbacks(simulator, 'site', target, translated,
                        lookup=lambda: setattr(simulator.work, 'max_operand_bits', 128)), \
                        self.assertRaises(ReachAdmissionError) as caught:
                    resolve(simulator, target)
                self.assertEqual(caught.exception.details['budget'], 'numeric_operand_bits')
                self.assertEqual(caught.exception.details['limit'], 128)
                self.assertEqual(simulator.work.max_operations, 100000)


if __name__ == '__main__':
    unittest.main()
