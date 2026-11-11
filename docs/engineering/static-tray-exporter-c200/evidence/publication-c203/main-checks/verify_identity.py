"""Bind the actual merged main worktree to reviewed and tested source bytes."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

ROOT = Path('/workspace/scratch/a4d9132036d4')
REPO = ROOT / 'main-verification'
OUT = ROOT / 'work-c203/main-checks'
PREFIX = 'docs/engineering/static-tray-exporter-c200/'
MAIN = '2b2f3e7de7595099ad5f9e0176c5596220c0c2dc'
TREE = '7e1ab341160cf5b86807e8ffec2cc3bb7b47db92'
REVIEWED = '125353836119e50215287c27d80e99cef6d85e8f'
BASE = '2cad7ecfece83295a3534d8afc97ab127a665ded'
EXECUTED = '62b2316cc3f88db187f69fbd7fdb2cf0997a97de'

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()

def read(path):
    return json.loads(path.read_bytes())

def binding(path):
    assert path.is_file() and not path.is_symlink(), str(path)
    raw = path.read_bytes()
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}

stage = sys.argv[1]
assert stage in {'before', 'after'}
OUT.mkdir(exist_ok=True, parents=True)
assert git('rev-parse', 'HEAD') == MAIN
assert git('rev-parse', 'HEAD^{tree}') == TREE
assert git('status', '--porcelain=v1', '--untracked-files=all') == ''
remote_path = ROOT / 'work-c203/C200-MERGE-READBACK.json'
remote = read(remote_path)
assert remote['main']['object']['sha'] == MAIN == remote['merge']['sha']
assert remote['merge']['tree']['sha'] == TREE
assert remote['pr']['number'] == 137 and remote['pr']['merged'] is True
assert remote['pr']['state'] == 'closed' and remote['pr']['merge_commit_sha'] == MAIN
assert remote['issue']['number'] == 136 and remote['issue']['state'] == 'closed'
parents = [row['sha'] for row in remote['merge']['parents']]
assert git('show', '-s', '--format=%P', MAIN).split() == parents
assert parents[0] == BASE
assert git('rev-parse', parents[1] + '^{tree}') == TREE
review_dir = REPO / PREFIX / 'evidence/publication-c203/independent-review'
original_dir = ROOT / 'work-c203/integration-review'
names = ['REVIEW.md', 'REVIEW.json', 'CONTENT-AUDIT.json', 'audit_candidate.py', 'FIRST-ATTEMPT.json']
review_files = []
for name in names:
    current = binding(review_dir / name)
    assert current == binding(original_dir / name), name
    review_files.append({'path': str((review_dir / name).relative_to(REPO)), **current})
delta = git('diff', '--name-status', '--no-renames', REVIEWED, MAIN).splitlines()
expected_delta = sorted('A\t' + row['path'] for row in review_files)
assert sorted(delta) == expected_delta
lock_path = REPO / PREFIX / 'EXECUTABLE-INPUTS.json'
lock = read(lock_path)
lock_binding = binding(lock_path)
assert lock_binding['sha256'] == 'e22d12703926740c2c4cb8596781192b9f0412836e3fba7c6f353bedfc60e0e0'
locked = []
for relative, expected in sorted(lock['repository_files'].items()):
    actual = binding(REPO / relative)
    assert actual == {'sha256': expected['sha256'], 'size_bytes': expected['size_bytes']}, relative
    locked.append({'path': relative, **actual})
assert len(locked) == 301
tested_path = REPO / PREFIX / 'evidence/publication-c203/checks/TESTED-SOURCE-MANIFEST.json'
tested = read(tested_path)
assert tested['count'] == 301 and tested['files'] == locked
protected = ['ontokin', 'tools', 'fixtures', 'schemas', 'grammar', '.github', 'pyproject.toml', 'setup.cfg', 'setup.py', 'requirements.txt', '.gitignore']
protected_diff = git('diff', '--name-status', BASE, MAIN, '--', *protected).splitlines()
assert protected_diff == []
execution_diff = git('diff', '--name-status', EXECUTED, MAIN, '--', 'ontokin', 'prototypes', 'tools', 'fixtures', 'schemas', 'grammar', '.github', 'tests', ':(glob)' + PREFIX + '*.py').splitlines()
assert execution_diff == []
pinned_root = Path('/workspace/scratch/ef5ae272e66e/deps/blender-4.5.3-linux-x64/4.5/scripts/addons_core/io_scene_gltf2')
pinned_expected = {'__init__.py': ('82428a0415e11c27a285fd950f63e874add5ba2f8bacc6806ed762614560fa2e', 84361), 'io/com/debug.py': ('a0112a1488ce1520f6554f1c337494845ab0aea9b683a73b0b747505d6a2fa94', 3783)}
pinned = []
for name, (sha, size) in pinned_expected.items():
    actual = binding(pinned_root / name)
    assert actual == {'sha256': sha, 'size_bytes': size}
    pinned.append({'path': str(pinned_root / name), **actual})
report = {
    'schema': 'ontokin.c203.actual-main-identity/0.1',
    'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'stage': stage, 'passed': True,
    'main_commit': MAIN, 'main_tree': TREE, 'parents': parents,
    'worktree_clean': True, 'reviewed_candidate': REVIEWED,
    'remote_readback_source': {'path': str(remote_path), **binding(remote_path)},
    'remote_readback_scope': 'Independent comparison to the integrator-captured post-merge GitHub API readback; this checker performs no new network request.',
    'remote_main_and_merge_and_tree_equal_worktree': True,
    'merged_pr': 137, 'closed_issue': 136,
    'merged_source_head': parents[1], 'merged_source_tree_equals_main': True,
    'changes_since_reviewed_candidate': delta,
    'independent_review_artifacts': review_files,
    'independent_review_artifacts_equal_approved_copies': True,
    'input_lock': lock_binding,
    'locked_input_count': len(locked), 'locked_files': locked,
    'prior_fresh_tested_manifest': {'path': str(tested_path.relative_to(REPO)), **binding(tested_path)},
    'prior_fresh_tested_inputs_equal_main': True,
    'protected_legacy_diff_from_premerge_main': protected_diff,
    'execution_code_diff_from_executed_c200': execution_diff,
    'pinned_exporter_sources': pinned,
    'new_native_receiving_node_lifecycle_author_runs': 0
}
if stage == 'after':
    previous = read(OUT / 'IDENTITY-BEFORE.json')
    for key in ['main_commit', 'main_tree', 'parents', 'independent_review_artifacts', 'input_lock', 'locked_files', 'pinned_exporter_sources']:
        assert report[key] == previous[key], key
    report['inputs_unchanged_during_tests'] = True
path = OUT / ('IDENTITY-' + stage.upper() + '.json')
assert not path.exists(), str(path)
path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({'passed': True, 'stage': stage, 'main_commit': MAIN, 'main_tree': TREE, 'locked_inputs': len(locked), 'review_artifacts': len(review_files), 'remote_readback_tree_equal': True}))
