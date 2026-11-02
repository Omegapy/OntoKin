#!/usr/bin/env python3
"""Exercise captured helpers only in hermetic synthetic Git repositories."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile

OUT = Path('/workspace/scratch/05c3f95a49c1/c090-reviews')
REAL_GIT = shutil.which('git')
ENV = {**os.environ, 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1',
       'GIT_ATTR_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0', 'PYTHONDONTWRITEBYTECODE': '1',
       'GIT_AUTHOR_NAME': 'C090 independent synthetic review',
       'GIT_AUTHOR_EMAIL': 'review@example.invalid',
       'GIT_COMMITTER_NAME': 'C090 independent synthetic review',
       'GIT_COMMITTER_EMAIL': 'review@example.invalid',
       'GIT_AUTHOR_DATE': '2026-11-02T00:00:00+00:00',
       'GIT_COMMITTER_DATE': '2026-11-02T00:00:00+00:00'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo, *args, data=None):
    return subprocess.check_output([REAL_GIT, '-C', str(repo), *args], input=data, env=ENV).decode().strip()


def put(repo, path, data, mode=0o644):
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    target.chmod(mode)


def make_repo():
    directory = Path(tempfile.mkdtemp(prefix='c090-helper-review-'))
    repo = directory / 'repository'
    subprocess.run([REAL_GIT, 'init', '--quiet', '--template=', '-b', 'main', str(repo)], env=ENV, check=True)
    git(repo, 'config', 'core.hooksPath', '/dev/null')
    for name, data, mode in [('STATUS.md', b'old status\n', 0o644),
                             ('docs/README.md', b'old navigation\n', 0o644),
                             ('runtime.txt', b'untouched runtime\n', 0o644),
                             ('runtime_exec.py', b'#!/usr/bin/env python3\n', 0o755)]:
        put(repo, name, data, mode)
    git(repo, 'add', '.')
    tree = git(repo, 'write-tree')
    commit = git(repo, 'commit-tree', tree, data=b'synthetic baseline\n')
    git(repo, 'update-ref', 'refs/heads/main', commit)
    return directory, repo, commit


def wrapper(directory, repo):
    shim = directory / 'shim'
    shim.mkdir()
    blob = git(repo, 'hash-object', '-w', '--stdin', data=b'late staged bytes\n')
    program = '''#!PYTHON
import os,subprocess,sys
from pathlib import Path
r=subprocess.run([os.environ['REVIEW_REAL_GIT'],*sys.argv[1:]],capture_output=True)
if r.returncode == 0 and 'ls-tree' in sys.argv:
 p=Path(os.environ['REVIEW_COUNTER']); n=int(p.read_text())+1 if p.exists() else 1;p.write_text(str(n))
 if n == 2:
  subprocess.run([os.environ['REVIEW_REAL_GIT'],'-C',os.environ['REVIEW_REPO'],'update-index','--add','--cacheinfo','100644',os.environ['REVIEW_BLOB'],'docs/language-design/torque-v0.1/late.txt'],check=True)
sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);raise SystemExit(r.returncode)
'''.replace('PYTHON', sys.executable)
    (shim / 'git').write_text(program)
    (shim / 'git').chmod(0o755)
    return {**ENV, 'PATH': str(shim) + os.pathsep + ENV['PATH'],
            'REVIEW_REAL_GIT': REAL_GIT, 'REVIEW_COUNTER': str(directory / 'counter'),
            'REVIEW_REPO': str(repo), 'REVIEW_BLOB': blob}


def run_case(version, name, operation, expected_ok, setup=None, inspect=None, mutate_index=False):
    directory, repo, baseline = make_repo()
    target = baseline
    if setup is not None:
        value = setup(directory, repo, baseline)
        if value is not None:
            target = value
    output = directory / 'result.json'
    if name == 'fresh-output-existing-file':
        output.write_bytes(b'preserve existing bytes\n')
    if name == 'fresh-output-dangling-symlink':
        output.symlink_to(directory / 'symlink-target.json')
    helper = OUT / f'integration-helper-review{version:02d}-inputs' / (operation + '.py')
    command = [sys.executable, '-B', str(helper), '--repository', str(repo), '--output', str(output)]
    if operation == 'prepare_publication':
        command += ['--parent', 'HEAD' if name == 'symbolic-parent-identity' else baseline]
    else:
        command += ['--baseline', baseline, '--ref', 'HEAD' if name == 'symbolic-target-identity' else target]
    index_before = git(repo, 'write-tree')
    process = subprocess.run(command, env=wrapper(directory, repo) if mutate_index else ENV,
                             text=True, capture_output=True, timeout=30)
    actual_ok = process.returncode == 0
    row = {'id': name, 'helper_version': version, 'operation': operation,
           'expected_success': expected_ok, 'actual_success': actual_ok,
           'returncode': process.returncode, 'passed': actual_ok == expected_ok,
           'argv': command, 'baseline_commit': baseline, 'requested_target': target,
           'index_before': index_before, 'index_after': git(repo, 'write-tree'),
           'stdout': process.stdout, 'stderr': process.stderr,
           'output_exists': output.exists(), 'output_is_symlink': output.is_symlink()}
    if actual_ok:
        row['result'] = json.loads(output.read_bytes())
    if name == 'fresh-output-existing-file':
        row['original_output_bytes_unchanged'] = output.read_bytes() == b'preserve existing bytes\n'
        row['passed'] &= row['original_output_bytes_unchanged']
    if name == 'fresh-output-dangling-symlink':
        row['dangling_target_created'] = (directory / 'symlink-target.json').exists()
        row['passed'] &= row['dangling_target_created'] == (version == 1)
    if inspect is not None and actual_ok:
        extra = inspect(row['result'], directory, repo, baseline, target)
        row['independent_checks'] = extra
        row['passed'] &= all(extra.values())
    # These repositories are fully generated disposable fixtures, never source
    # checkouts. Exact source literals, mutation recipes and all commands are in
    # this retained driver; native identities and complete helper results remain.
    shutil.rmtree(directory)
    return row


def main():
    rows = []
    def add(name, operation, old_ok, new_ok, setup=None, inspect=None, mutate_index=False):
        for version, expectation in [(1, old_ok), (2, new_ok)]:
            rows.append(run_case(version, name, operation, expectation, setup, inspect, mutate_index))
    def valid(directory, repo, baseline):
        put(repo, 'STATUS.md', b'new status\n')
        for name, data, mode in [
            ('unicode.txt', 'é漢🙂\r\ntext\n'.encode(), 0o644),
            ('empty.txt', b'', 0o644), ('nul.bin', b'a\0b', 0o644),
            ('nonutf8.bin', b'\xff\xfe\x80', 0o644),
            ('executable.py', b'#!/usr/bin/env python3\n', 0o755),
        ]:
            put(repo, 'docs/language-design/torque-v0.1/' + name, data, mode)
        git(repo, 'add', '.')
        return git(repo, 'write-tree')
    def inspect_description(result, directory, repo, baseline, target):
        checks = {'tree_matches_index': result['tree'] == git(repo, 'write-tree'),
                  'parent_matches_exact_baseline': result['parent'] == baseline,
                  'changed_file_count': len(result['elements']) == 6,
                  'binary_count': len(result['binary_blobs']) == 2}
        for element in result['elements']:
            data = (repo / element['path']).read_bytes()
            expected = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            descriptor = next(r for r in result['identities'] if r['path'] == element['path'])
            checks['identity:' + element['path']] = descriptor['sha'] == expected and descriptor['sha256'] == hashlib.sha256(data).hexdigest()
            checks['transport:' + element['path']] = element['content'].encode() == data if 'content' in element else element['sha'] == expected
        return checks
    add('mixed-exact-blob-description', 'prepare_publication', True, True, valid, inspect_description)
    add('valid-preservation-and-scoped-changes', 'verify_source_snapshot', True, True, valid)
    def chmod_normal(directory, repo, baseline):
        (repo / 'runtime.txt').chmod(0o600)
    add('noncanonical-nonexecutable-permissions', 'verify_source_snapshot', True, False, chmod_normal)
    def chmod_executable(directory, repo, baseline):
        (repo / 'runtime_exec.py').chmod(0o744)
    add('noncanonical-executable-permissions', 'verify_source_snapshot', True, False, chmod_executable)
    def index_only(directory, repo, baseline):
        blob = git(repo, 'hash-object', '-w', '--stdin', data=b'index-only unreviewed file\n')
        git(repo, 'update-index', '--add', '--cacheinfo', '100644', blob, 'unauthorized.txt')
    add('index-differs-from-reviewed-ref', 'verify_source_snapshot', True, False, index_only)
    def deletion(directory, repo, baseline):
        git(repo, 'rm', '--quiet', 'runtime.txt')
        return git(repo, 'write-tree')
    add('source-deletion', 'prepare_publication', False, False, deletion)
    def runtime_change(directory, repo, baseline):
        put(repo, 'runtime.txt', b'altered runtime\n');git(repo, 'add', '.')
        return git(repo, 'write-tree')
    add('changed-old-runtime', 'verify_source_snapshot', False, False, runtime_change)
    def outside_scope(directory, repo, baseline):
        put(repo, 'unapproved/new.txt', b'outside scope\n');git(repo, 'add', '.')
        return git(repo, 'write-tree')
    add('new-path-outside-scope', 'verify_source_snapshot', False, False, outside_scope)
    def worktree_change(directory, repo, baseline):
        put(repo, 'runtime.txt', b'changed only on disk\n')
    add('worktree-byte-mismatch', 'verify_source_snapshot', False, False, worktree_change)
    def untracked(directory, repo, baseline):
        put(repo, 'untracked.txt', b'untracked bytes\n')
    add('untracked-source', 'verify_source_snapshot', False, False, untracked)
    def symlink(directory, repo, baseline):
        link = repo / 'docs/language-design/torque-v0.1/link'
        link.parent.mkdir(parents=True);link.symlink_to(directory / 'outside')
        git(repo, 'add', '.');return git(repo, 'write-tree')
    add('nonordinary-native-entry', 'prepare_publication', False, False, symlink)
    add('fresh-output-existing-file', 'prepare_publication', False, False)
    add('fresh-output-dangling-symlink', 'prepare_publication', True, False)
    add('symbolic-parent-identity', 'prepare_publication', True, True,
        inspect=lambda r,d,p,b,t: {'immutable_parent_if_amended': r['parent'] in (b, 'HEAD')})
    add('symbolic-target-identity', 'verify_source_snapshot', True, True,
        inspect=lambda r,d,p,b,t: {'ref_resolves_to_actual_tree': r['tree'] == git(p, 'rev-parse', b + '^{tree}')})
    add('index-changed-during-capture', 'prepare_publication', True, False, mutate_index=True)
    add('index-changed-during-verification', 'verify_source_snapshot', True, False, mutate_index=True)
    result = {'schema_version': 'ontokin.c090-independent-integration-helper-probes/1',
              'recorded_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'passed' if all(r['passed'] for r in rows) else 'failed',
              'scope': 'Hermetic synthetic Git repositories only; no network, production execution or project source mutation',
              'passed_checks': sum(r['passed'] for r in rows),
              'failed_checks': sum(not r['passed'] for r in rows), 'checks': rows,
              'driver_sha256': sha(Path(__file__)), 'python': sys.version, 'platform': platform.platform(),
              'git_version': subprocess.check_output([REAL_GIT, '--version'], env=ENV).decode().strip(),
              'initial_helpers_source_capture': 'Reconstructed exact initial observed text; capture timing caveat retained in integration-helper-review01-inputs/INPUTS.json',
              'current_amended_helpers_match_snapshot': {name: sha(OUT / 'integration-helper-review02-inputs' / name) == sha(Path('/workspace/scratch/05c3f95a49c1/c090-tools') / name) for name in ('prepare_publication.py', 'verify_source_snapshot.py')}}
    (OUT / 'integration-helper-probes01.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k:result[k] for k in ('status','passed_checks','failed_checks','current_amended_helpers_match_snapshot')}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
