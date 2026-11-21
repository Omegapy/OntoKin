#!/usr/bin/env python3
"""Inert until Director-authorized launch; exactly the two C271-P10 modules.

Read-only Git preflight precedes all project imports. Process guards remain
installed throughout project import, loading, execution, and evidence capture.
No command-line test selectors, discovery, child runner, or automatic retry.
"""
from contextlib import ExitStack
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import time
import traceback
import unittest
from unittest.mock import patch

MODULES = ('tests.test_current_host_inspection_v01', 'tests.test_current_host_elf_mapping_v01')
ORIGINAL_TEST_SHA256 = '797eb208670f6f74f14c9b5849485bd6cf3522a265d4129618c4b50ddc0a739a'
GIT = '/usr/bin/git'
PROCESS_APIS = {
    subprocess: ('Popen', 'run', 'check_output', 'call', 'check_call'),
    os: ('system', 'popen', 'fork', 'forkpty', 'posix_spawn', 'posix_spawnp',
         'spawnl', 'spawnle', 'spawnlp', 'spawnlpe', 'spawnv', 'spawnve', 'spawnvp', 'spawnvpe',
         'execl', 'execle', 'execlp', 'execlpe', 'execv', 'execve', 'execvp', 'execvpe',
         'kill', 'killpg', 'setsid', 'setpgid', 'getpgid', 'getpgrp', 'getsid',
         'wait', 'waitpid', 'waitid', 'wait3', 'wait4'),
}
AUDIT_EVENTS = {'subprocess.Popen', 'os.system', 'os.fork', 'os.forkpty', 'os.posix_spawn',
                'os.exec', 'os.kill', 'os.killpg'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def binding(path):
    info = path.lstat()
    row = {'path': str(path), 'mode': oct(stat.S_IMODE(info.st_mode)),
           'bytes': info.st_size, 'device': info.st_dev, 'inode': info.st_ino,
           'links': info.st_nlink, 'mtime_ns': info.st_mtime_ns}
    if stat.S_ISREG(info.st_mode):
        row.update(kind='file', sha256=digest(path))
    elif stat.S_ISLNK(info.st_mode):
        row.update(kind='symlink', target=os.readlink(path))
    else:
        row['kind'] = 'directory' if stat.S_ISDIR(info.st_mode) else 'special'
    return row


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def absolute(value):
    p = Path(value)
    if not p.is_absolute() or p != p.resolve():
        raise ValueError('An explicit canonical absolute path is required: ' + value)
    return p


def leaves(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from leaves(item)
        else:
            yield item


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, journal, **kwargs):
        super().__init__(*args, **kwargs)
        self.journal, self.records, self.current = journal, [], None
        self.scope_records = []

    def startTest(self, test):
        super().startTest(test)
        self.current = {'id': test.id(), 'started_at_utc': utc(), 'start_monotonic': time.monotonic(),
                        'status': 'running', 'subtests': [], 'details': []}
        self.journal.write(json.dumps({'event': 'start', **self.current}) + '\n')
        self.journal.flush()

    def outcome(self, status, detail=None, test=None):
        if self.current is None:
            row = {'id': test.id() if test is not None else 'scope', 'status': status, 'detail': detail, 'at_utc': utc()}
            self.scope_records.append(row)
            self.journal.write(json.dumps({'event': 'scope_outcome', **row}) + '\n')
            self.journal.flush()
            return
        self.current['status'] = status
        if detail is not None:
            self.current['details'].append(detail)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcome('passed')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcome('failed', self._exc_info_to_string(err, test), test)

    def addError(self, test, err):
        super().addError(test, err)
        self.outcome('error', self._exc_info_to_string(err, test), test)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcome('skipped', reason, test)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.outcome('expected_failure', self._exc_info_to_string(err, test), test)

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.outcome('unexpected_success')

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        row = {'id': subtest.id(), 'passed': err is None}
        if err is not None:
            row['detail'] = self._exc_info_to_string(err, test)
            self.outcome('subtest_failed', row['detail'])
        self.current['subtests'].append(row)

    def stopTest(self, test):
        self.current['finished_at_utc'] = utc()
        self.current['elapsed_seconds'] = time.monotonic() - self.current['start_monotonic']
        self.records.append(self.current)
        self.journal.write(json.dumps({'event': 'finish', **self.current}) + '\n')
        self.journal.flush()
        os.fsync(self.journal.fileno())
        super().stopTest(test)
        self.current = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'output', 'fixtures', 'expected-head', 'freeze', 'freeze-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    repo, output, fixtures, freeze_path = map(absolute, (args.repo, args.output, args.fixtures, args.freeze))
    if not repo.is_dir() or output.exists() or fixtures.exists():
        raise ValueError('Authentic existing repository and fresh output/fixture directories required')
    if output.is_relative_to(repo) or fixtures.is_relative_to(repo) or output == fixtures or output.is_relative_to(fixtures):
        raise ValueError('Evidence must be outside repository; output cannot be within fixtures')
    output.mkdir(mode=0o700)
    report = {'schema': 'ontokin.c271.p10-focused-run/1', 'started_at_utc': utc(),
              'argv': list(sys.orig_argv), 'cwd': os.getcwd(), 'selected_modules': list(MODULES),
              'state': 'preflight', 'passed': False, 'pre_guard_git_commands': [], 'guards_installed': False,
              'product_tests_started': False, 'current_unknown_operations': []}
    source_files, guard_mocks, audit_calls, blocked_imports = [], [], [], []
    result, exit_code = None, 2
    stdout = (output / 'stdout.log').open('x', encoding='utf-8')
    stderr = (output / 'stderr.log').open('x', encoding='utf-8')
    saved_fds = (os.dup(1), os.dup(2))
    sys.stdout.flush(); sys.stderr.flush()
    os.dup2(stdout.fileno(), 1); os.dup2(stderr.fileno(), 2)
    try:
        expected_env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC',
                        'PYTHONDONTWRITEBYTECODE': '1', 'ONTOKIN_HI_RETAIN_ROOT': str(fixtures / 'inspection'),
                        'ONTOKIN_ELF_RETAIN_ROOT': str(fixtures / 'elf')}
        actual_env = dict(os.environ)
        report['environment'] = {k: actual_env.get(k) for k in expected_env}
        report['unexpected_environment_keys'] = sorted(set(actual_env) - set(expected_env))
        if actual_env != expected_env or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
            raise RuntimeError('Use the documented exact env -i and Python -I -S -B launch')
        report['python'] = {'executable': sys.executable, 'resolved_executable': str(Path(sys.executable).resolve()),
                            'version': sys.version, 'binding': binding(Path(sys.executable).resolve()),
                            'platform': sys.platform, 'uname': list(os.uname())}
        report['git_executable'] = binding(Path(GIT))
        git_dir = output / 'git-preflight'; git_dir.mkdir()

        def git(label, *command):
            argv = [GIT, '-C', str(repo), *command]
            completed = subprocess.run(argv, capture_output=True, check=False, timeout=30, env=expected_env)
            for stream in ('stdout', 'stderr'):
                (git_dir / (label + '.' + stream)).write_bytes(getattr(completed, stream))
            report['pre_guard_git_commands'].append({'argv': argv, 'exit_code': completed.returncode,
                                                     'stdout': label + '.stdout', 'stderr': label + '.stderr'})
            if completed.returncode:
                raise RuntimeError('Read-only Git preflight failed: ' + label)
            return completed.stdout

        top = git('root', 'rev-parse', '--show-toplevel').decode().strip()
        if Path(top) != repo:
            raise RuntimeError('Explicit repo does not name the authentic Git root')
        head, tree = git('identity', 'rev-parse', 'HEAD', 'HEAD^{tree}').decode().splitlines()
        status = git('status', 'status', '--porcelain=v1', '-z', '--untracked-files=all')
        changed = git('changed', 'diff', '--no-renames', '--name-only', '-z', 'HEAD')
        untracked = git('untracked', 'ls-files', '--others', '--exclude-standard', '-z')
        patch_bytes = git('patch', 'diff', '--binary', '--no-ext-diff', 'HEAD')
        (output / 'dirty.patch').write_bytes(patch_bytes)
        dirty = []
        dirty_root = output / 'dirty-source'; dirty_root.mkdir()
        for name in sorted(set((changed + untracked).split(b'\0')) - {b''}):
            rel = os.fsdecode(name); path = repo / rel
            row = binding(path) if path.exists() or path.is_symlink() else {'path': str(path), 'kind': 'deleted'}
            row['repository_path'] = rel
            if row['kind'] == 'file':
                snapshot = dirty_root / rel; snapshot.parent.mkdir(parents=True, exist_ok=True); snapshot.write_bytes(path.read_bytes())
            dirty.append(row)
        save(output / 'DIRTY-MANIFEST.json', {'head': head, 'tree': tree, 'status_hex': status.hex(), 'files': dirty})
        report['source'] = {'repo': str(repo), 'head': head, 'tree': tree, 'dirty': bool(status),
                            'dirty_manifest': 'DIRTY-MANIFEST.json', 'preflight_only': True}
        freeze_bytes = freeze_path.read_bytes()
        if hashlib.sha256(freeze_bytes).hexdigest() != args.freeze_sha256:
            raise RuntimeError('Freeze bytes differ from independently supplied digest')
        frozen = json.loads(freeze_bytes)
        (output / 'FROZEN-INPUTS.json').write_bytes(freeze_bytes)
        if status or head != args.expected_head or frozen['source_head'] != head or frozen['source_tree'] != tree:
            raise RuntimeError('Clean exact published candidate head/tree required before test imports')
        new_count = frozen['expected_new_methods']
        if type(new_count) is not int or new_count < 1:
            raise RuntimeError('Independent freeze must declare the positive exact new-method count')
        snapshots = output / 'frozen-inputs'; snapshots.mkdir()
        for index, item in enumerate(frozen['files']):
            value = item['path']; raw = Path(value)
            if not raw.is_absolute() and ('..' in PurePosixPath(value).parts or str(PurePosixPath(value)) != value):
                raise RuntimeError('Noncanonical relative frozen path')
            path = absolute(value) if raw.is_absolute() else repo / raw
            if path.is_symlink() or not path.is_file() or path.resolve() != path:
                raise RuntimeError('Frozen inputs must be canonical regular files: ' + str(path))
            row = binding(path)
            if row['bytes'] != item['bytes'] or row['sha256'] != item['sha256']:
                raise RuntimeError('Frozen input mismatch: ' + str(path))
            snapshot = snapshots / ('%04d-' % index + path.name)
            snapshot.write_bytes(path.read_bytes())
            source_files.append({'source': row, 'snapshot': str(snapshot.relative_to(output))})
        paths = [x['source']['path'] for x in source_files]
        required = [repo / 'prototypes/static_tray_v01/current_host_inspection_v01.py',
                    repo / 'tests/test_current_host_inspection_v01.py', repo / 'tests/test_current_host_elf_mapping_v01.py', Path(__file__).resolve()]
        if len(paths) != len(set(paths)) or any(str(p) not in paths for p in required):
            raise RuntimeError('Freeze must uniquely include production source, both tests and this runner')
        if digest(repo / 'tests/test_current_host_inspection_v01.py') != ORIGINAL_TEST_SHA256:
            raise RuntimeError('Original 135-method test module changed')
        report['frozen_source_files'] = source_files
        fixtures.mkdir(parents=True, mode=0o700)
        (fixtures / 'inspection').mkdir(mode=0o700); (fixtures / 'elf').mkdir(mode=0o700)
        sys.path.insert(0, str(repo))

        class OnlySelectedTestModules:
            def find_spec(self, fullname, path=None, target=None):
                if fullname.startswith('tests.') and fullname not in MODULES:
                    blocked_imports.append(fullname)
                    raise ImportError('Unselected test module forbidden: ' + fullname)
                return None

        def audit(event, arguments):
            if event in AUDIT_EVENTS:
                audit_calls.append(event)
                raise AssertionError('Actual project process operation forbidden: ' + event)

        with ExitStack() as stack:
            for module, names in PROCESS_APIS.items():
                for name in names:
                    if hasattr(module, name):
                        label = module.__name__ + '.' + name
                        guard = stack.enter_context(patch.object(module, name, side_effect=AssertionError('Actual process operation forbidden: ' + label)))
                        guard_mocks.append((label, guard))
            sys.addaudithook(audit)
            sys.meta_path.insert(0, OnlySelectedTestModules())
            report['guards_installed'] = True
            report['guards_installed_before_project_imports_at_utc'] = utc()
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromNames(MODULES)
            cases = list(leaves(suite))
            ids = [case.id() for case in cases]
            counts = {m: sum(case.__class__.__module__ == m for case in cases) for m in MODULES}
            save(output / 'SELECTED-METHODS.json', {'modules': list(MODULES), 'ids': ids, 'counts': counts, 'loader_errors': loader.errors})
            if loader.errors or len(ids) != len(set(ids)) or counts != {MODULES[0]: 135, MODULES[1]: new_count} or len(cases) != 135 + new_count:
                raise RuntimeError('Exact two-module test inventory differs from independent freeze')
            with (output / 'METHOD-EVENTS.jsonl').open('x', encoding='utf-8') as journal:
                report['state'] = 'running'; report['product_tests_started'] = True
                save(output / 'RUN-STARTED.json', report)
                factory = lambda *a, **kw: RecordingResult(*a, journal=journal, **kw)
                result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, failfast=False, buffer=False, resultclass=factory).run(suite)
            save(output / 'METHOD-RESULTS.json', result.records)
            save(output / 'METHOD-SCOPE-RESULTS.json', result.scope_records)
            report['tests_run'] = result.testsRun
            for key in ('failures', 'errors', 'skipped', 'expectedFailures', 'unexpectedSuccesses'):
                report[key] = len(getattr(result, key))
            report['outer_process_guard_calls'] = {name: mock.call_count for name, mock in guard_mocks}
            report['blocked_process_audit_events'] = audit_calls
            report['blocked_test_module_imports'] = blocked_imports
            post = [{'path': x['source']['path'], 'matches_frozen': binding(Path(x['source']['path']))['sha256'] == x['source']['sha256']} for x in source_files]
            report['frozen_input_postflight'] = post
            report['environment_restored'] = dict(os.environ) == expected_env
            report['passed'] = (result.wasSuccessful() and result.testsRun == len(cases)
                                and all(x['status'] == 'passed' for x in result.records)
                                and not any(report['outer_process_guard_calls'].values()) and not audit_calls and not blocked_imports
                                and all(x['matches_frozen'] for x in post) and report['environment_restored'])
            report['state'] = 'completed'; exit_code = 0 if report['passed'] else 1
    except BaseException:
        report['fatal_exception'] = traceback.format_exc()
        traceback.print_exc()
        report['state'] = 'failed'; exit_code = 2
    finally:
        report['finished_at_utc'] = utc()
        report['outer_process_guard_calls'] = {name: mock.call_count for name, mock in guard_mocks}
        report['blocked_process_audit_events'] = audit_calls
        report['blocked_test_module_imports'] = blocked_imports
        report['actual_project_process_operations'] = 0 if report['guards_installed'] else 'not_started'
        retained = []
        if fixtures.exists():
            for folder, dirs, files in os.walk(fixtures, followlinks=False):
                for name in sorted(dirs + files):
                    path = Path(folder) / name; row = binding(path); row['relative_path'] = str(path.relative_to(fixtures)); retained.append(row)
        save(output / 'FIXTURE-MANIFEST.json', {'root': str(fixtures), 'entries': retained, 'cleanup_performed': False})
        sys.stdout.flush(); sys.stderr.flush(); stdout.flush(); stderr.flush()
        os.fsync(stdout.fileno()); os.fsync(stderr.fileno())
        os.dup2(saved_fds[0], 1); os.dup2(saved_fds[1], 2)
        os.close(saved_fds[0]); os.close(saved_fds[1]); stdout.close(); stderr.close()
        report['logs'] = [binding(output / name) for name in ('stdout.log', 'stderr.log')]
        report['exit_code'] = exit_code
        report['retry_permitted'] = False
        report['source_identity_boundary'] = 'Git HEAD/tree/status observed before guards; frozen input bytes checked after tests. Director rechecks live Git state separately.'
        save(output / 'OUTCOME.json', report)
    print(json.dumps({'passed': report['passed'], 'state': report['state'], 'exit_code': exit_code, 'outcome': str(output / 'OUTCOME.json')}))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
