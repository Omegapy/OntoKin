"""P29's independently frozen P27 controls; no host admission or native starts.

The immutable oracle is the adopted P27 control plan. Actual inert reads,
synthetic raw primitives, selectors, mocked relations and mocked caller flow are
reported separately. Neither a synthetic pin declaration nor a mocked binding
observation establishes actual file admission. No production pin is patched.
"""
from __future__ import annotations

import ast
from contextlib import ExitStack, contextmanager
from copy import deepcopy
import errno
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from prototypes.static_tray_v01 import current_host_inspection_v01 as inspection

REPO = Path(__file__).resolve().parents[1]
CONTROL_ROOT = REPO / 'docs/engineering/localized-repair-c271/required-images-p29/controls'
PLAN_PATH = REPO / 'docs/engineering/localized-repair-c271/required-image-design-p27/design/CONTROL-PLAN.json'
PLAN_SHA256 = '55dc8e776253232e7eb23e51593754f9b69cf72e23732246424adb6ed58ba89f'
FIXTURE_MANIFEST_SHA256 = 'e98978fe2df14a8862aa7065952068012e2825dc612c5b6c70a939c0376865a5'
ZERO_STARTS = {'node': 0, 'ldd': 0, 'direct_loader': 0, 'cpu_checker': 0}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def authenticate():
    raw = PLAN_PATH.read_bytes()
    if sha256(raw) != PLAN_SHA256:
        raise AssertionError('Adopted P27 plan changed')
    manifest_raw = (CONTROL_ROOT / 'FIXTURE-MANIFEST.json').read_bytes()
    if sha256(manifest_raw) != FIXTURE_MANIFEST_SHA256:
        raise AssertionError('Independent fixture manifest changed')
    manifest = json.loads(manifest_raw)
    expected = {row['path'] for row in manifest['files']}
    actual = {p.relative_to(CONTROL_ROOT).as_posix() for p in CONTROL_ROOT.rglob('*') if p.is_file()}
    if actual != expected | {'FIXTURE-MANIFEST.json', 'FREEZE.json'}:
        raise AssertionError('Complete fixture inventory changed')
    for row in manifest['files']:
        p = CONTROL_ROOT / row['path']
        data = p.read_bytes()
        if (p.is_symlink() or len(data) != row['size_bytes'] or sha256(data) != row['sha256']
                or oct(stat.S_IMODE(p.stat().st_mode)) != row['mode']):
            raise AssertionError('Frozen fixture differs: ' + row['path'])
    for row in read_json(CONTROL_ROOT / 'COMPANIONS.json')['files']:
        p = REPO / row['path']
        data = p.read_bytes()
        if len(data) != row['size_bytes'] or sha256(data) != row['sha256']:
            raise AssertionError('Frozen inherited companion differs: ' + row['path'])
    plan = json.loads(raw)
    cases = read_json(CONTROL_ROOT / 'CONTROL-CROSSWALK.json')['cases']
    if len(cases) != 116 or len({c['id'] for c in cases}) != 116:
        raise AssertionError('116 one-to-one obligations required')
    original = {c['id']: c for c in plan['cases']}
    if set(original) != {c['id'] for c in cases}:
        raise AssertionError('Obligation IDs changed')
    for case in cases:
        if (case['source_case_sha256'] != sha256(canonical(original[case['id']]))
                or case['expected'] != original[case['id']]['expected']
                or case['target_starts'] != ZERO_STARTS or case['operational'] is not False):
            raise AssertionError('Literal oracle or claim boundary changed: ' + case['id'])
    return cases


CASES = authenticate()
BASE = read_json(CONTROL_ROOT / 'BASE-CONTEXT.json')
INHERITED = read_json(CONTROL_ROOT / 'INHERITED-INVENTORIES.json')['methods']
MOCK_COMMAND = read_json(CONTROL_ROOT / 'MOCK-COMMAND.json')
MOCK_PRELAUNCH = read_json(CONTROL_ROOT / 'MOCK-PRELAUNCH.json')
INHERITED_METADATA_STUB = read_json(CONTROL_ROOT / 'INHERITED-METADATA-STUB.json')


class FrozenClock:
    def __init__(self, *, total_ms):
        if total_ms != 5000:
            raise AssertionError('Changed command allowance')
        self.started = 1000.0

    def check(self, stage_end=None):
        if stage_end is not None and stage_end != 1003.0:
            raise AssertionError('Changed active-work allowance')

    def elapsed_ms(self):
        return 100.0


class FrozenStop(Exception):
    state = 'TIMEOUT'


class HelperBoundaryReached(RuntimeError):
    pass


class MemoryStore:
    """Exactly frozen fake publications; neither durable IO nor a process proof."""
    def __init__(self, validated, fixture=MOCK_COMMAND):
        self.validated = validated
        self.fixture = fixture
        self.plan = inspection._thaw(validated.plan)
        self.publications = []
        self.values = {}
        self.expected = {row['path']: row for row in fixture['expected_publications']}

    def write(self, path, value, **kwargs):
        row = self.expected[path]
        if canonical(value) != canonical(row['payload']):
            raise AssertionError('Publication differs from preexecution literal: ' + path)
        if path in self.values:
            raise AssertionError('Repeated mocked publication')
        check = kwargs.get('check')
        if check:
            check()
        self.values[path] = deepcopy(value)
        self.publications.append({'destination': path})
        return deepcopy(row['descriptor'])

    def retain_raw(self, path, *, maximum):
        raw = self.fixture['raw_ascii'][path].encode('ascii')
        if len(raw) > maximum:
            raise AssertionError('Changed retention bound')
        return raw, {'path': path, 'sha256': sha256(raw), 'size_bytes': len(raw), 'mode': '0o600'}


class ReadProbe:
    """Observe actual descriptor ownership/read ranges; inject fixed OS faults."""
    def __init__(self, case):
        self.case = case
        self.opened = []
        self.closed = []
        self.reads = []
        self.fstats = 0
        self.stages = []
        self.stage = None
        self.callbacks = 0
        self.sentinel = None
        if case['route'] == 'private_callback_fault':
            kind = case['input']['exception_type']
            self.sentinel = (inspection.HostInspectionError('PLAN', 'Frozen callback sentinel') if kind == 'HostInspectionError'
                             else {'RuntimeError': RuntimeError, 'ValueError': ValueError, 'OSError': OSError}[kind]('Frozen callback sentinel'))
        elif case['route'] in ('private_metadata_read_fault', 'private_metadata_close_fault'):
            self.sentinel = OSError(errno.EIO, 'Frozen EIO sentinel')

    def callback(self):
        self.callbacks += 1
        if self.case['route'] == 'private_callback_fault' and self.stage == self.case['input']['checkpoint']:
            raise self.sentinel

    @contextmanager
    def observe(self):
        original_open, original_close = os.open, os.close
        original_pread, original_fstat = os.pread, os.fstat
        original_checkpoint = inspection._required_image_checkpoint
        def opened(path, *args, **kwargs):
            fd = original_open(path, *args, **kwargs)
            self.opened.append(fd)
            return fd
        def closed(fd):
            self.closed.append(fd)
            result = original_close(fd)
            if self.case['route'] == 'private_metadata_close_fault':
                raise self.sentinel
            return result
        def pread(fd, size, offset):
            self.reads.append([offset, size])
            if self.case['route'] == 'private_metadata_read_fault' and len(self.reads) == 2:
                raise self.sentinel
            return original_pread(fd, size, offset)
        def fstat(fd):
            info = original_fstat(fd)
            self.fstats += 1
            if self.case['route'] == 'private_metadata_identity_drift' and self.fstats == 2:
                fields = {k: getattr(info, k) for k in dir(info) if k.startswith('st_')}
                fields['st_ino'] += 1
                return SimpleNamespace(**fields)
            return info
        def checkpoint(check, stage):
            self.stages.append(stage)
            prior, self.stage = self.stage, stage
            try:
                return original_checkpoint(check, stage)
            finally:
                self.stage = prior
        with ExitStack() as stack:
            for name, value in [('open', opened), ('close', closed), ('pread', pread), ('fstat', fstat)]:
                stack.enter_context(patch.object(os, name, value))
            stack.enter_context(patch.object(inspection, '_required_image_checkpoint', checkpoint))
            yield self


class CallerProbe:
    """Stipulated inherited observations around real new bindings and callers."""
    def __init__(self, context, *, drift=False):
        self.context = deepcopy(context)
        self.plan, self.runtime = self.context['plan'], self.context['runtime']
        self.events, self.binding_reads, self.policies = [], [], []
        self.entries = 0
        self.in_constructor = False
        self.drift = drift
        self.git_reads = self.helper_imports = self.fake_process_calls = 0
        self.git_state_calls = self.git_command_calls = 0
        self.stage_calls = []
        self.recheck_entries = 0
        self.active_recheck = None
        self.resolution_entries = []
        self.plan_raw = canonical(self.plan)
        self.plan_descriptor = {'path': self.context['plan_path'], 'sha256': sha256(self.plan_raw), 'size_bytes': len(self.plan_raw), 'mode': '0o644'}

    def validated(self):
        return inspection.ValidatedPlan(self.plan, self.plan_descriptor, [], self.context['git_state'],
                                        (None, SimpleNamespace(Clock=FrozenClock, Stop=FrozenStop)), self.runtime,
                                        {'expected_resolution': self.context['expected_resolution'], 'rtld_path_snapshot': self.context['rtld_snapshot'], 'input_snapshot': {}})

    def read_file(self, path, maximum, *, category='PLAN', private=True, check=lambda: None, keep=True):
        name = str(path)
        check()
        if name == self.context['plan_path']:
            return (self.plan_raw if keep else None), inspection._binding(self.plan_descriptor)
        rationale = self.plan['host_static']['resolution']['rationale']
        if name == rationale['path']:
            raw = self.context['rationale_raw_ascii'].encode('ascii')
            return (raw if keep else None), inspection._binding(rationale)
        value = deepcopy(self.plan['host_static']['files'][name])
        if self.in_constructor:
            self.binding_reads.append({'path': name, 'maximum': maximum, 'category': category, 'private': private, 'keep': keep})
            if (maximum != value['size_bytes'] or category != 'INSPECTOR' or private is not False or keep is not False):
                raise AssertionError('New binding read changed its inherited seam')
            if self.drift and name == '/required-images/libdl.so.2':
                value['sha256'] = '0' * 64
        return None, value

    @contextmanager
    def observe(self, *, stop_at_helpers=False):
        c, p, r = self.context, self.plan, self.plan['host_static']['resolution']
        original_constructor = inspection._prepare_required_images_policy
        original_dispatch = inspection._read_plan_elf_metadata
        original_required_raw = inspection._read_required_image_elf_metadata
        original_require = inspection._require
        original_resolution = inspection._check_resolution
        original_recheck = inspection._recheck
        original_resolve, original_symlink = Path.resolve, Path.is_symlink
        rows = {row['file']['path']: row for row in r['images']}
        subject_paths = {d['path']: key for key, d in r['required_images']['subjects'].items()}
        logical = set(p['host_static']['aliases']) | set(p['host_static']['files'])
        logical.update(row['path'] for row in r['rtld_paths']['components'])
        def stage(name):
            self.stage_calls.append({'stage': name, 'real_recheck': self.active_recheck})
        def resolution(*args, **kwargs):
            prior_entries = [event for event in self.resolution_entries if event['real_recheck'] == self.active_recheck]
            entry = {'real_recheck': self.active_recheck, 'ordinal': len(prior_entries) + 1}
            self.resolution_entries.append(entry)
            stage('_check_resolution')
            return original_resolution(*args, **kwargs)
        def recheck(*args, **kwargs):
            self.recheck_entries += 1
            previous, self.active_recheck = self.active_recheck, self.recheck_entries
            try:
                return original_recheck(*args, **kwargs)
            finally:
                self.active_recheck = previous
        def observed(name, result=None):
            def call(*args, **kwargs):
                stage(name)
                return deepcopy(result)
            return call
        def git_state(*args, **kwargs):
            self.git_reads += 1
            self.git_state_calls += 1
            stage('_git_state')
            return deepcopy(c['git_state'])
        def resolve(path, *args, **kwargs):
            name = str(path)
            if name in logical or name.startswith('/required-'):
                return Path(p['host_static']['aliases'].get(name, {'resolved_path': name})['resolved_path'])
            return original_resolve(path, *args, **kwargs)
        def is_symlink(path):
            name = str(path)
            if name in logical or name.startswith('/required-') or name in ('/', '/usr', '/usr/bin', '/usr/lib'):
                return False
            return original_symlink(path)
        def constructor(*args, **kwargs):
            self.entries += 1
            self.events.append('required_policy_entry')
            self.in_constructor = True
            try:
                result = original_constructor(*args, **kwargs)
                self.policies.append(result)
                self.events.append('all_five_required_subject_proof')
                return result
            finally:
                self.in_constructor = False
        def dispatch(path, policy, **kwargs):
            name = str(path)
            if name == p['author']['python_descriptor']['path']:
                self.events.append('actual_python_read')
                return deepcopy(c['actual_python_metadata'])
            if name in subject_paths:
                self.events.append('private_required_image_read:' + subject_paths[name])
                return original_dispatch(path, policy, **kwargs)
            return deepcopy(rows[name]['metadata'])
        def required_raw(path, key, **kwargs):
            if str(path) != r['required_images']['subjects'][key]['path']:
                raise AssertionError('Required dispatch lost the canonical subject')
            inert = REPO / ('docs/engineering/localized-repair-c271/required-image-design-p27/design/sources/package-images/' + key + '.inert')
            return original_required_raw(inert, key, **kwargs)
        def libc_policy(*args, **kwargs):
            self.events.append('unchanged_libc_loader_proof')
            return inspection._freeze(c['libc_policy'])
        def require(condition, category, reason, **kwargs):
            result = original_require(condition, category, reason, **kwargs)
            if reason == 'Declared ELF metadata differs' and self.events and self.events[-1] == 'actual_python_read':
                self.events.append('declared_python_metadata_equality')
            return result
        def origin_rule(*args, **kwargs):
            self.events.append('full_inherited_origin_resolution_guards')
        def helpers(*args, **kwargs):
            self.helper_imports += 1
            self.events.append('helpers_or_git_may_follow')
            if stop_at_helpers:
                raise HelperBoundaryReached('Stop before operational validation success')
            raise AssertionError('Unexpected helper load')
        def git_reads(*args, **kwargs):
            self.git_reads += 1
            self.git_command_calls += 1
            stage('_check_git')
            raise AssertionError('No Git process reads in caller controls')
        patches = {
            'ROOT': Path('/required-source'), '_read_file': self.read_file,
            '_prepare_required_images_policy': constructor, '_read_plan_elf_metadata': dispatch,
            '_read_required_image_elf_metadata': required_raw, '_require': require,
            '_check_resolution': resolution, '_recheck': recheck,
            '_check_source_files': lambda *a, **k: deepcopy(c['source_inventory']),
            '_check_author_runtime': lambda *a, **k: deepcopy(self.runtime),
            '_check_host_static': lambda *a, **k: None,
            '_prepare_origin_policy': lambda *a, **k: inspection._freeze(c['origin_policy']),
            '_check_origin_bounds': lambda *a, **k: None, '_prepare_libc_plt_policy': libc_policy,
            '_check_origin_rule': origin_rule,
            '_directory_entries': lambda path, **k: deepcopy(next(x for x in r['search_directories'] if x['path'] == str(path))),
            '_check_loader_inputs': lambda *a, **k: [],
            '_check_rtld_operational_paths': observed('_check_rtld_operational_paths', c['rtld_snapshot']),
            '_check_plan_guards': observed('_check_plan_guards'), '_load_helpers': helpers, '_check_git': git_reads,
            '_git_state': git_state,
            '_check_metadata': observed('_check_metadata', {'paths': []}),
            '_check_runtime_dependencies': observed('_check_runtime_dependencies', []),
            '_check_evidence': observed('_check_evidence'),
            '_ancestors': lambda *a, **k: [], '_compare_rtld_snapshot': lambda actual, expected: self.assert_equal_snapshot(actual, expected),
        }
        with ExitStack() as stack:
            for name, value in patches.items():
                stack.enter_context(patch.object(inspection, name, value))
            stack.enter_context(patch.object(Path, 'resolve', resolve))
            stack.enter_context(patch.object(Path, 'is_symlink', is_symlink))
            yield self

    @staticmethod
    def assert_equal_snapshot(actual, expected):
        if actual != expected:
            raise AssertionError('Frozen RTLD snapshot projection changed')


class RequiredImageControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        selected = os.environ.get('ONTOKIN_REQUIRED_IMAGES_RETAIN_ROOT')
        if selected:
            cls.evidence = Path(selected)
            cls.evidence.mkdir(parents=True, exist_ok=False)
        else:
            temporary = tempfile.TemporaryDirectory(prefix='ontokin-required-image-controls-')
            cls.addClassCleanup(temporary.cleanup)
            cls.evidence = Path(temporary.name)
        (cls.evidence / 'RUN-INPUTS.json').write_text(json.dumps({
            'python': sys.version, 'plan_sha256': PLAN_SHA256, 'fixture_manifest_sha256': FIXTURE_MANIFEST_SHA256,
            'production_sha256': sha256((REPO / 'prototypes/static_tray_v01/current_host_inspection_v01.py').read_bytes()),
            'adapter_sha256': sha256(Path(__file__).read_bytes()), 'operational': False,
            'ids': [case['id'] for case in CASES]}, indent=2) + '\n')

    def setUp(self):
        self.forbidden_calls = []
        self.observed = {}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        def forbidden(*args, **kwargs):
            self.forbidden_calls.append(repr(args[:1]))
            raise AssertionError('Native/process launch forbidden by P27 controls')
        for name in ('Popen', 'run', 'check_output', 'check_call'):
            self.stack.enter_context(patch.object(subprocess, name, forbidden))
        for name in ('system', 'fork', 'posix_spawn', 'posix_spawnp', 'execv', 'execve', 'execvp', 'execvpe'):
            if hasattr(os, name):
                self.stack.enter_context(patch.object(os, name, forbidden))

    def assert_error(self, error, expected):
        self.assertIsInstance(error, inspection.HostInspectionError)
        literal = {key: expected[key] for key in ('code', 'reason', 'state', 'details')}
        literal['cause'] = expected.get('cause_selector', expected.get('cause'))
        self.assertEqual(error.as_dict(), literal)
        self.observed['error'] = error.as_dict()

    def fixture_path(self, case):
        row = case['fixture']
        p = (CONTROL_ROOT if row['scope'] == 'controls' else REPO) / row['path']
        raw = p.read_bytes()
        self.assertEqual((len(raw), sha256(raw), oct(stat.S_IMODE(p.stat().st_mode))),
                         (row['size_bytes'], row['sha256'], row['mode']))
        return p

    def raw_case(self, case):
        path = self.fixture_path(case)
        key = case['input'].get('mutation', {}).get('catalog_key', case['input'].get('catalog_key', 'libdl.so.2'))
        probe = ReadProbe(case)
        error = result = None
        with probe.observe():
            try:
                result = inspection._read_required_image_elf_metadata(path, key, check=probe.callback, require_interpreter=False)
            except BaseException as exc:
                error = exc
        self.observed.update(opened=probe.opened, close_attempts=probe.closed, read_ranges=probe.reads,
                             checkpoint_counts={stage: probe.stages.count(stage) for stage in set(probe.stages)},
                             callbacks=probe.callbacks, result=result)
        self.assertEqual(probe.closed, probe.opened)
        self.assertEqual(len(probe.opened), 0 if case['route'] == 'private_metadata_mode' else 1)
        if case['route'] == 'private_callback_fault':
            self.assertIs(error, probe.sentinel)
            self.assertEqual(probe.stages[-1], case['input']['checkpoint'])
            self.assertIsNone(result)
            self.observed['same_callback_object'] = True
        elif case['route'] == 'private_metadata_close_fault':
            self.assertIs(error, probe.sentinel)
            self.assertEqual(len(probe.closed), 1)
            self.assertIsNone(result)
        elif case['route'] == 'private_metadata_read_fault':
            self.assertIsInstance(error, inspection.HostInspectionError)
            self.assertIs(error.cause, probe.sentinel)
            expected = {**case['expected'], 'cause': {'type': 'OSError', 'reason': str(probe.sentinel)}}
            self.assert_error(error, expected)
        elif case['expected'].get('outcome') == 'METADATA':
            if error is not None:
                raise error
            self.assertEqual(result, case['expected']['metadata'])
            self.assertEqual(set(result), set(case['expected']['metadata']))
            if 'layout' in case['fixture']:
                layout = case['fixture']['layout']
                self.assertEqual(probe.reads, layout['pread_ranges'])
                for stage in ('during_required_image_tag_scan', 'during_required_image_flags'):
                    self.assertEqual(probe.stages.count(stage), layout['nonnull_dynamic_entries'])
                self.assertEqual(probe.stages.count('before_required_image_final_identity'), 1)
        else:
            self.assert_error(error, case['expected'])
        self.assertEqual(sha256(path.read_bytes()), case['fixture']['sha256'])

    def selector_case(self, case, context):
        p = context['plan']
        with patch.object(os, 'open', side_effect=AssertionError('Selector opened a file')), \
             patch.object(Path, 'is_symlink', side_effect=AssertionError('Selector observed a filesystem path')):
            try:
                result = inspection._select_required_images_profile(p['schema'], p['host_static']['resolution'])
            except inspection.HostInspectionError as error:
                self.assert_error(error, case['expected'])
            else:
                self.assertEqual(case['expected']['outcome'], 'SELECTED_CLOSED_POLICY')
                self.assertEqual(inspection._thaw(result), p['host_static']['resolution']['required_images'])
                self.assertEqual(p['schema'], case['expected']['schema_preserved'])

    def relation_case(self, case, context):
        probe = CallerProbe(context)
        callback_stage = None
        checkpoint_events = []
        open_calls = []
        self.observed['relation_checkpoint_events'] = checkpoint_events
        self.observed['relation_open_calls'] = open_calls
        self.observed['relation_binding_reads'] = probe.binding_reads
        sentinel = RuntimeError('Frozen relation callback sentinel')
        original_checkpoint = inspection._required_image_checkpoint
        def callback():
            if callback_stage == 'required_policy_each_subject' and checkpoint_events.count(callback_stage) == 3:
                raise sentinel
        def checkpoint(check, stage):
            nonlocal callback_stage
            callback_stage = stage
            checkpoint_events.append(stage)
            return original_checkpoint(check, stage)
        def guarded_open(*args, **kwargs):
            open_calls.append({'args': [str(value) for value in args], 'kwargs': {k: str(v) for k, v in kwargs.items()}})
            raise AssertionError('Relation callback fault must precede every descriptor open')
        with probe.observe(), patch.object(inspection, '_required_image_checkpoint', checkpoint), ExitStack() as local:
            if case['route'] == 'pure_relation_callback_fault':
                local.enter_context(patch.object(os, 'open', guarded_open))
            error = None
            policy = None
            try:
                policy = inspection._prepare_required_images_policy(probe.plan, probe.runtime, context['actual_python_metadata'],
                            inspection._freeze(context['libc_policy']), check=callback if case['route'] == 'pure_relation_callback_fault' else lambda: None)
            except BaseException as exc:
                error = exc
            if case['route'] == 'pure_relation_callback_fault':
                self.assertIs(error, sentinel)
                self.assertEqual(len(probe.binding_reads), 0)
                self.assertEqual(open_calls, [])
                self.assertIsNone(policy)
                self.assertEqual(probe.policies, [])
                self.assertEqual(checkpoint_events, ['required_policy_entry'] + ['required_policy_each_subject'] * 3)
            elif case['kind'] == 'refusal' and case['route'] == 'mocked_relation_and_policy':
                self.assert_error(error, case['expected'])
                self.assertEqual(probe.binding_reads, [])
            else:
                if error is not None:
                    raise error
                self.assertEqual(inspection._thaw(policy), {
                    'schema': context['plan']['schema'],
                    'subjects': context['plan']['host_static']['resolution']['required_images']['subjects'],
                    'loader': context['plan']['host_static']['resolution']['required_images']['loader'],
                })
                self.assertEqual(set(policy), {'schema', 'subjects', 'loader'})
                self.assertEqual(policy['schema'], probe.plan['schema'])
                self.assertEqual(list(policy['subjects']), sorted(context['plan']['host_static']['resolution']['required_images']['subjects']))
                with self.assertRaises(TypeError):
                    policy['schema'] = 'changed'
                with self.assertRaises(TypeError):
                    policy['subjects']['libdl.so.2']['sha256'] = 'changed'
                with self.assertRaises(TypeError):
                    policy['loader']['sha256'] = 'changed'
                expected_paths = [context['plan']['host_static']['resolution']['required_images']['subjects'][key]['path'] for key in sorted(policy['subjects'])] + [policy['loader']['path']]
                self.assertEqual([row['path'] for row in probe.binding_reads], expected_paths)
                if case['route'] == 'mocked_dispatch':
                    self.dispatch_case(context, policy)
                elif case['route'] == 'mocked_post_metadata_relation':
                    altered = deepcopy(context['plan']['host_static']['resolution']['images'][0]['metadata'])
                    altered['soname'] = case['input']['actual_metadata_soname']
                    with patch.object(inspection, '_read_required_image_elf_metadata', return_value=altered):
                        with self.assertRaises(inspection.HostInspectionError) as caught:
                            inspection._read_plan_elf_metadata(policy['subjects']['libdl.so.2']['path'], None, required_policy=policy)
                    self.assert_error(caught.exception, case['expected'])
        self.observed.update(binding_reads=probe.binding_reads, real_constructor_entries=probe.entries,
                             policy_count=len(probe.policies), checkpoints=checkpoint_events)

    def dispatch_case(self, context, policy):
        # This control observes dispatch only; all returned metadata is labelled
        # stipulated. The new constructor above remains the actual constructor.
        selected = []
        def required(path, key, **kwargs):
            selected.append(('required', str(path), key))
            return deepcopy(next(row['metadata'] for row in context['plan']['host_static']['resolution']['images'] if row['file']['path'] == str(path)))
        libc_policy = inspection._freeze(context['libc_policy'])
        origin = inspection._freeze(context['origin_policy'])
        # Bypass CallerProbe's outer dispatcher observation only by restoring the
        # product function captured in the adapter's module, not a new refusal.
        product_dispatch = _PRODUCT_DISPATCH
        with patch.object(inspection, '_read_required_image_elf_metadata', required), \
             patch.object(inspection, '_read_libc_static_tls_elf_metadata', return_value={'route': 'libc'}) as libc, \
             patch.object(inspection, '_read_origin_elf_metadata', return_value={'route': 'origin'}) as origin_raw, \
             patch.object(inspection, 'read_elf_metadata', return_value={'route': 'ordinary'}) as ordinary:
            for key, descriptor in policy['subjects'].items():
                result = product_dispatch(descriptor['path'], origin, libc_policy=libc_policy, required_policy=policy)
                self.assertEqual(result['soname'], key)
            self.assertEqual(product_dispatch(libc_policy['subject']['path'], origin, libc_policy=libc_policy, required_policy=policy), {'route': 'libc'})
            self.assertEqual(product_dispatch(origin['subject']['path'], origin, libc_policy=libc_policy, required_policy=policy), {'route': 'origin'})
            self.assertEqual(product_dispatch('/required-images/ordinary.so', origin, libc_policy=libc_policy, required_policy=policy), {'route': 'ordinary'})
            self.assertEqual((libc.call_count, origin_raw.call_count, ordinary.call_count), (1, 1, 1))
        self.assertEqual(selected, [('required', policy['subjects'][key]['path'], key) for key in sorted(policy['subjects'])])
        self.assertEqual(set(inspection._thaw(policy)), {'schema', 'subjects', 'loader'})

    def caller_case(self, case, context):
        cid = case['id']
        probe = CallerProbe(context, drift=cid in ('RI-C04', 'RI-C06'))
        self.observed['caller_events'] = probe.events
        self.observed['caller_binding_reads'] = probe.binding_reads
        self.observed['caller_stage_calls'] = probe.stage_calls
        self.observed['caller_resolution_entries'] = probe.resolution_entries
        if cid == 'RI-C05':
            with tempfile.TemporaryDirectory(prefix='ri-snapshot-') as temp:
                fixture = MOCK_PRELAUNCH['snapshot_fixture']
                path = Path(temp) / fixture['relative_name']
                path.write_bytes(fixture['before_ascii'].encode('ascii'))
                path.chmod(int(fixture['mode'], 8))
                before = list(inspection._identity(path.lstat()))
                path.write_bytes(fixture['after_ascii'].encode('ascii'))
                validated = probe.validated()
                self.assertEqual(inspection._thaw(validated.descriptor), MOCK_PRELAUNCH['plan_descriptor'])
                object.__setattr__(validated, '_metadata', inspection._freeze({'input_snapshot': {str(path): {'identity': before, 'resolved': str(path)}}}))
                boundaries = {'stipulated_preflight_calls': 0, 'real_launch_check_calls': 0, 'fake_process_calls': 0, 'later_guard_calls': []}
                self.observed['prelaunch_boundaries'] = boundaries
                def preflight(*args, **kwargs):
                    boundaries['stipulated_preflight_calls'] += 1
                    return deepcopy(MOCK_PRELAUNCH['preflight'])
                product_launch = inspection._launch_check
                def launch(*args, **kwargs):
                    boundaries['real_launch_check_calls'] += 1
                    return product_launch(*args, **kwargs)
                def fake_process(*args, **kwargs):
                    boundaries['fake_process_calls'] += 1
                    raise AssertionError('Changed snapshot reached the fake process boundary')
                def later_guard(name):
                    def fail(*args, **kwargs):
                        boundaries['later_guard_calls'].append(name)
                        raise AssertionError('Changed snapshot reached later launch guard: ' + name)
                    return fail
                object.__setattr__(validated, '_helpers', (None, SimpleNamespace(Clock=FrozenClock, Stop=FrozenStop, run_process=fake_process)))
                store = MemoryStore(validated, MOCK_PRELAUNCH)
                with ExitStack() as local:
                    local.enter_context(patch.object(inspection, '_recheck', preflight))
                    local.enter_context(patch.object(inspection, '_launch_check', launch))
                    for name in ('_platform', '_check_guards', '_origin_subject_observation', '_check_kernel_origin', '_check_rtld_operational_paths'):
                        local.enter_context(patch.object(inspection, name, later_guard(name)))
                    with self.assertRaises(inspection.HostInspectionError) as caught:
                        inspection._run_command(validated, deepcopy(MOCK_PRELAUNCH['command']), store, deepcopy(MOCK_PRELAUNCH['preflight']))
                error = caught.exception
                self.assert_error(error, case['expected'])
                self.assertEqual(boundaries, {'stipulated_preflight_calls': 1, 'real_launch_check_calls': 1, 'fake_process_calls': 0, 'later_guard_calls': []})
                self.assertIsNone(error.process_record)
                self.assertIsNone(error.supervisor_exception)
                record = error.refusal_record['attempt']
                self.assertEqual((record['actual_direct_starts'], record['observed_direct_starts'], record['start_count_state']), (0, 0, 'PROVEN_ZERO'))
                self.assertTrue(error.refusal_record['evidence_finalized'])
                self.assertEqual(set(store.values), {row['path'] for row in MOCK_PRELAUNCH['expected_publications']})
                self.observed['launch_boundary_entered'] = boundaries['fake_process_calls'] != 0
                self.observed['refusal_record'] = error.refusal_record
                self.observed['publications'] = store.publications
            return
        with probe.observe(stop_at_helpers=cid in ('RI-C01', 'RI-C02')):
            if cid in ('RI-C01', 'RI-C02'):
                try:
                    inspection._validate(context['plan_path'], probe.plan_descriptor['sha256'], fresh=True)
                except HelperBoundaryReached:
                    self.assertEqual(cid, 'RI-C01')
                except inspection.HostInspectionError as error:
                    self.assertEqual(cid, 'RI-C02')
                    self.assert_error(error, case['expected']['underlying'])
                else:
                    self.fail('Caller control must stop before operational success')
                if cid == 'RI-C01':
                    positions = [probe.events.index(event) for event in ('actual_python_read', 'declared_python_metadata_equality', 'unchanged_libc_loader_proof', 'all_five_required_subject_proof')]
                    positions += [min(i for i, event in enumerate(probe.events) if event.startswith('private_required_image_read:')), probe.events.index('full_inherited_origin_resolution_guards'), probe.events.index('helpers_or_git_may_follow')]
                    self.assertEqual(positions, sorted(positions))
                    self.assertEqual(sum(event.startswith('private_required_image_read:') for event in probe.events), 5)
                    self.assertEqual(probe.helper_imports, 1)
                else:
                    self.assertEqual((probe.entries, probe.helper_imports, probe.git_reads, len(probe.binding_reads)), (1, 0, 0, 0))
            elif cid == 'RI-C03':
                validated = probe.validated()
                for _ in range(2):
                    self.assertTrue(inspection._recheck(validated)['passed'])
                self.assertEqual(probe.entries, 4)  # Early and final proof on each complete recheck.
                self.assertEqual(len({id(policy) for policy in probe.policies}), 4)
                self.assertEqual(probe.events.count('actual_python_read'), 4)
                expected = [context['plan']['host_static']['resolution']['required_images']['subjects'][key]['path'] for key in sorted(context['plan']['host_static']['resolution']['required_images']['subjects'])] + [context['libc_policy']['loader']['path']]
                self.assertEqual([row['path'] for row in probe.binding_reads], expected * 4)
            elif cid == 'RI-C04':
                with self.assertRaises(inspection.HostInspectionError) as caught:
                    inspection._recheck(probe.validated())
                self.assert_error(caught.exception, case['expected'])
                self.assertEqual((probe.entries, len(probe.binding_reads), probe.helper_imports, probe.git_reads), (1, 1, 0, 0))
                self.assertFalse(any(event.startswith('private_required_image_read:') for event in probe.events))
                self.assert_failed_recheck_boundaries(probe, 1)
            elif cid == 'RI-C06':
                validated = probe.validated()
                self.assertEqual(inspection._thaw(validated.descriptor), MOCK_COMMAND['plan_descriptor'])
                def fake_process(argv, *, stage, label, clock, stage_end, env, on_started, cancel_after_ms):
                    probe.fake_process_calls += 1
                    self.assertEqual(argv, MOCK_COMMAND['command']['argv'])
                    self.assertEqual(str(stage), MOCK_COMMAND['command']['cwd'])
                    self.assertEqual(label, MOCK_COMMAND['command']['label'])
                    self.assertEqual(env, MOCK_COMMAND['process']['environment'])
                    self.assertEqual(stage_end, 1003.0)
                    self.assertIsNone(cancel_after_ms)
                    process = deepcopy(MOCK_COMMAND['process'])
                    on_started(process)
                    return process
                object.__setattr__(validated, '_helpers', (None, SimpleNamespace(Clock=FrozenClock, Stop=FrozenStop, run_process=fake_process)))
                real_recheck = inspection._recheck
                rechecks = []
                def recheck(value, **kwargs):
                    rechecks.append(1)
                    if len(rechecks) == 1:
                        return deepcopy(MOCK_COMMAND['preflight'])
                    return real_recheck(value, **kwargs)
                store = MemoryStore(validated)
                with patch.object(inspection, '_recheck', recheck), \
                     patch.object(inspection, '_launch_check', return_value=None), \
                     patch.object(inspection, '_utc', return_value=MOCK_COMMAND['utc']):
                    with self.assertRaises(inspection.HostInspectionError) as caught:
                        inspection._run_command(validated, deepcopy(MOCK_COMMAND['command']), store, deepcopy(MOCK_COMMAND['preflight']))
                error = caught.exception
                self.assert_error(error, case['expected'])
                self.assertEqual(error.process_record, MOCK_COMMAND['process'])
                self.assertIsNone(error.supervisor_exception)
                record = error.refusal_record['attempt']
                self.assertEqual((record['actual_direct_starts'], record['observed_direct_starts'], record['start_count_state']), (1, 1, 'OBSERVED_ONE'))
                self.assertTrue(error.refusal_record['evidence_finalized'])
                self.assertEqual((probe.entries, probe.fake_process_calls, len(rechecks)), (2, 1, 3))
                self.assertEqual(len(probe.binding_reads), 2)
                self.assert_failed_recheck_boundaries(probe, 2)
                self.assertFalse(any(path.endswith('inspection.json') for path in store.values))
                self.assertEqual(set(store.values), {row['path'] for row in MOCK_COMMAND['expected_publications']})
                self.observed.update(fake_process_calls=probe.fake_process_calls, mock_start_count=record['observed_direct_starts'],
                                     recheck_call_count=len(rechecks), stipulated_initial_preflight_calls=len(rechecks)-probe.recheck_entries,
                                     mock_receipt=error.process_record, refusal_record=error.refusal_record, publications=store.publications)
        self.observed.update(events=probe.events, binding_reads=probe.binding_reads, real_constructor_entries=probe.entries,
                             helper_imports=probe.helper_imports, git_reads=probe.git_reads,
                             git_state_calls=probe.git_state_calls, git_command_calls=probe.git_command_calls,
                             real_recheck_entries=probe.recheck_entries)

    def assert_failed_recheck_boundaries(self, probe, count):
        self.assertEqual(probe.recheck_entries, count)
        self.assertEqual(probe.resolution_entries, [{'real_recheck': n, 'ordinal': 1} for n in range(1, count + 1)])
        self.assertEqual(probe.stage_calls, [{'stage': '_check_resolution', 'real_recheck': n} for n in range(1, count + 1)])
        self.assertEqual((probe.git_state_calls, probe.git_command_calls, probe.helper_imports), (0, 0, 0))
        self.assertFalse(any(event.startswith('private_required_image_read:') for event in probe.events))

    def old_route_case(self, case):
        path = self.fixture_path(case)
        route = case['input']['route']
        origin = inspection._freeze(BASE['origin_policy'])
        policy = deepcopy(BASE['libc_policy'])
        if route == 'public_default':
            call = lambda: inspection.read_elf_metadata(path)
        else:
            version = route[len('plan_'):].split('_')[0]
            policy['schema'] = 'ontokin.current-host-readback-inspection-plan/' + version
            call = lambda: inspection._read_plan_elf_metadata(path, None if version == '0.1.0' else origin,
                      libc_policy=inspection._freeze(policy) if version in ('0.1.2', '0.1.3', '0.1.4') else None)
        with patch.object(inspection, '_required_image_checkpoint', side_effect=AssertionError('Old route used new checkpoint')):
            with self.assertRaises(inspection.HostInspectionError) as caught:
                call()
        self.assert_error(caught.exception, case['expected'])

    def old_shape_case(self, case, context):
        with patch.object(inspection, 'ROOT', Path('/required-source')), patch.object(Path, 'is_symlink', return_value=False), \
             patch.object(inspection, '_prepare_required_images_policy', side_effect=AssertionError('Old shape dispatched new policy')):
            with self.assertRaises(inspection.HostInspectionError) as caught:
                inspection._plan_shape(context['plan'])
        self.assert_error(caught.exception, case['expected'])

    def inherited_case(self, case):
        names = (['test_current_host_libc_plt_metadata_v01', 'test_current_host_libc_static_tls_flags_v01']
                 if case['route'] == 'old_route_libc' else ['test_current_host_rtld_paths_v01'])
        results = []
        for name in names:
            module = importlib.import_module(name)
            suite = unittest.defaultTestLoader.loadTestsFromModule(module)
            def flatten(value):
                for item in value:
                    if isinstance(item, unittest.TestSuite):
                        yield from flatten(item)
                    else:
                        yield item.id()
            ids = sorted(flatten(suite))
            self.assertEqual(ids, INHERITED[name])
            result = unittest.TestResult()
            evidence = self.evidence / ('inherited-' + name)
            env = {'ONTOKIN_LIBC_RETAIN_ROOT': str(evidence), 'ONTOKIN_RTLD_RETAIN_ROOT': str(evidence)}
            metadata_stub = None
            with ExitStack() as inherited_stack:
                inherited_stack.enter_context(patch.dict(os.environ, env))
                inherited_stack.enter_context(patch.object(inspection, '_required_image_checkpoint', side_effect=AssertionError('Old corpus used new checkpoint')))
                if case['id'] == INHERITED_METADATA_STUB['control_id']:
                    self.assertEqual(name, INHERITED_METADATA_STUB['module'])
                    self.assertEqual(case['route'], 'old_route_rtld')
                    original_platform = module.platform.platform
                    metadata_stub = inherited_stack.enter_context(patch.object(
                        module.platform, 'platform', return_value=INHERITED_METADATA_STUB['value']))
                suite.run(result)
            observed = {'module': name, 'method_ids': ids, 'tests_run': result.testsRun,
                        'failures': result.failures, 'errors': result.errors, 'skipped': result.skipped}
            if metadata_stub is not None:
                observed['recording_metadata_stub'] = {
                    'leaf': INHERITED_METADATA_STUB['leaf'], 'synthetic_value': INHERITED_METADATA_STUB['value'],
                    'call_count': metadata_stub.call_count,
                    'calls': [{'args': list(call.args), 'kwargs': call.kwargs} for call in metadata_stub.call_args_list],
                    'restored_after_suite': module.platform.platform is original_platform}
            results.append(observed)
            self.observed['inherited_corpora'] = results
            self.assertEqual(result.testsRun, len(ids))
            self.assertEqual((result.failures, result.errors, result.skipped), ([], [], []))
            if metadata_stub is not None:
                self.assertEqual(metadata_stub.call_count, INHERITED_METADATA_STUB['expected_call_count'])
                metadata_stub.assert_called_once_with()
                self.assertTrue(observed['recording_metadata_stub']['restored_after_suite'])
                inputs = read_json(evidence / INHERITED_METADATA_STUB['recording_file'])
                recorded = inputs[INHERITED_METADATA_STUB['recording_key']]
                observed['recording_metadata_stub']['recorded_value'] = recorded
                self.assertEqual(recorded, INHERITED_METADATA_STUB['value'])
        self.observed['inherited_corpora'] = results

    def run_case(self, case):
        passed = False
        try:
            context = read_json(CONTROL_ROOT / case['context']) if 'context' in case else None
            route = case['route']
            if route.startswith('private_'):
                self.raw_case(case)
            elif route == 'pure_selector':
                self.selector_case(case, context)
            elif route in ('mocked_relation_and_policy', 'mocked_dispatch', 'mocked_post_metadata_relation', 'pure_relation_callback_fault'):
                self.relation_case(case, context)
            elif case['id'].startswith('RI-C'):
                self.caller_case(case, context)
            elif route == 'old_route_dispatch':
                self.old_route_case(case)
            elif route == 'old_schema_closed_shape':
                self.old_shape_case(case, context)
            elif route in ('old_route_libc', 'old_route_rtld'):
                self.inherited_case(case)
            else:
                self.fail('Unimplemented frozen route: ' + route)
            self.assertEqual(self.forbidden_calls, [])
            passed = True
        except BaseException as error:
            self.observed['raised'] = (error.as_dict() if isinstance(error, inspection.HostInspectionError)
                                       else {'type': type(error).__name__, 'reason': str(error)})
            raise
        finally:
            record = {'id': case['id'], 'route': case['route'], 'operational': False, 'passed': passed,
                      'expected': case['expected'], 'source_case_sha256': case['source_case_sha256'],
                      'actual_target_starts': ZERO_STARTS, 'forbidden_calls': self.forbidden_calls,
                      'observations': self.observed, 'claim_limit': case['claim_limit']}
            (self.evidence / (case['id'] + '.json')).write_text(json.dumps(record, indent=2, default=str) + '\n')


# Captured production dispatch is used only when a dispatch-specific control
# deliberately bypasses the separately labelled caller observation wrapper.
_PRODUCT_DISPATCH = inspection._read_plan_elf_metadata


def install(case):
    def test(self):
        self.run_case(case)
    test.__name__ = case['test_method']
    test.__doc__ = case['route'] + ': ' + case['claim_limit']
    setattr(RequiredImageControls, test.__name__, test)


for _case in CASES:
    install(_case)


if __name__ == '__main__':
    unittest.main()
