"""Bind the exact appended records and preserve the remote-reviewed core."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path('/workspace/scratch/fd65650eb54f')
REPO = ROOT / 'OntoKin'
BASE = REPO / 'docs/engineering/reach-recording-validation-2026-10-23'
DEST = BASE / 'checkpoint-046-validation'
WORK = ROOT / 'c046-work'


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO).decode().strip()


def file_record(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(BASE).as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


metadata = BASE / 'checkpoint-046-validation.json'
record = read(metadata)
assert git('rev-parse', 'HEAD') == record['core_commit']
assert git('rev-parse', 'HEAD^{tree}') == record['core_tree']
original = read(WORK / 'startup.json')
observed = read(DEST / 'publication/preappend-observations.json')
assert len(observed['branches']) == len(original['branches']) + 1 == 92
assert len(observed['pull_requests']) == len(original['pull_requests']) == 21
branch_map = {x['name']: x['sha'] for x in observed['branches']}
for entry in original['branches']:
    assert branch_map[entry['name']] == entry['sha']
pr_map = {x['number']: x for x in observed['pull_requests']}
for entry in original['pull_requests']:
    now = pr_map[entry['number']]
    for key in ['state', 'draft', 'head', 'head_ref', 'base']:
        assert now[key] == entry[key]
record['preappend_remote_reconciliation'] = {
    'record': 'checkpoint-046-validation/publication/preappend-observations.json',
    'prior_branches_preserved': 91, 'prior_open_draft_prs_preserved': 21,
    'observed_branches': 92, 'main': branch_map['main'],
    'final_head_and_pr_reconciliation': 'Required after publication and bound by Issue #26 closure.'
}
record['retained_failures_and_limits'].append(
    'A publication preparation read failed because an in-memory tree result was not the assumed raw shape. No remote mutation occurred. The exact tool-transcript error and correction using the saved raw core tree are retained in publication/preparation-failures.json.')
patterns = [rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{40,}',
            rb'AKIA[0-9A-Z]{16}', rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
scan_paths = [metadata] + [p for p in sorted(DEST.rglob('*')) if p.is_file()]
matches = []
for p in scan_paths:
    raw = p.read_bytes()
    for index, pattern in enumerate(patterns):
        if re.search(pattern, raw):
            matches.append({'path': p.relative_to(BASE).as_posix(), 'pattern_index': index})
assert not matches, matches
record['appendix_credential_scan'] = {
    'scope': 'Defined GitHub token, AWS access-key and private-key-header patterns only; not universal secret absence.',
    'pattern_count': len(patterns), 'files': len(scan_paths), 'matches': matches
}
members = [file_record(p) for p in sorted(DEST.rglob('*')) if p.is_file()]
assert all(Path(x['path']).suffix.lower() not in {'.md', '.html', '.htm'} for x in members)
record['files'] = members
record['appendix_member_files'] = len(members)
record['appendix_member_bytes'] = sum(x['bytes'] for x in members)
write(metadata, record)
subprocess.run(['git', 'add', '--', str(metadata), str(DEST)], cwd=REPO, check=True)
check = subprocess.run(['git', 'diff', '--cached', '--check'], cwd=REPO, capture_output=True)
assert check.returncode == 0 and not check.stdout and not check.stderr
for item in members:
    assert file_record(BASE / item['path']) == item
tree = read(WORK / 'core-remote-tree.json')
core = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
for name, entry in core.items():
    p = REPO / name
    raw = p.read_bytes()
    assert len(raw) == entry['size']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == entry['sha']
    assert ('100755' if p.stat().st_mode & 0o111 else '100644') == entry['mode']
rows = git('diff', '--cached', '--name-status').splitlines()
assert len(rows) == len(members) + 1
files = []
for row in rows:
    kind, name = row.split('\t')
    assert kind == 'A' and 'checkpoint-046-validation' in name
    p = REPO / name
    raw = p.read_bytes()
    files.append({'path': name, 'mode': '100755' if p.stat().st_mode & 0o111 else '100644',
        'type': 'blob', 'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
        'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
plan = {'parent': record['core_commit'], 'base_tree': record['core_tree'],
    'intended_tree': git('write-tree'), 'files': files,
    'core_files_preserved': len(core), 'core_bytes_preserved': sum(x['size'] for x in core.values()),
    'new_files': len(files), 'new_bytes': sum(x['bytes'] for x in files),
    'no_markdown_or_html_delta': True, 'whitespace_exit': 0, 'credential_scan_matches': 0,
    'window_comment': record['appendix_window_comment']}
write(WORK / 'final-publication-plan.json', plan)
print(json.dumps({k:v for k,v in plan.items() if k != 'files'}, indent=2))
