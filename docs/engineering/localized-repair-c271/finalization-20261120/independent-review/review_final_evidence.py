"""Read-only evidence inspection; does not run project behavior or write source."""
import ast
import hashlib
import json
import posixpath
import re
import stat
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

BASE = Path('/workspace/scratch/c219bb61a617')
V = BASE / 'validation'
O = BASE / 'integration-review'
REPO = BASE / 'OntoKin'
MAIN = 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
CANDIDATE = '88bc8b51b3963b7072375edac6400b6e6a4532e4'
CHECKPOINT = '15b1dd985b59cf037ebbeae733c16a54ca87f83d'
TREE = '755f366d1091beb71b5421b14fdac0b9b868cfb0'
checks = []
reads = []
git_reads = []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def identity(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}

def read_json(path):
    reads.append(identity(path))
    return json.loads(path.read_text())

def check(name, ok, detail=None):
    item = {'name': name, 'passed': bool(ok)}
    if detail is not None:
        item['detail'] = detail
    checks.append(item)

def file_matches(path, record):
    data = path.read_bytes()
    return len(data) == record['bytes'] and sha(data) == record['sha256'].removeprefix('sha256:')

def git_bytes(rev, path):
    argv = ['git', '-C', str(REPO), 'show', f'{rev}:{path}']
    p = subprocess.run(argv, capture_output=True, check=False)
    git_reads.append({'argv': argv, 'returncode': p.returncode, 'stdout_bytes': len(p.stdout), 'stdout_sha256': sha(p.stdout), 'stderr': p.stderr.decode()})
    if p.returncode:
        raise RuntimeError(f'Git read failed: {rev}:{path}: {p.stderr!r}')
    return p.stdout

def write(name, item):
    (O / name).write_text(json.dumps(item, indent=2) + '\n')

s = read_json(V / 'routine-candidate/summary.json')
r = read_json(V / 'execution-receipts/routine-candidate/EXECUTION.json')
active = read_json(V / 'ACTIVE-OPERATIONS.json')
results = read_json(V / 'RESULTS.json')
before = read_json(V / 'routine-candidate/source-before.json')
after = read_json(V / 'routine-candidate/source-after.json')
unit_inspection = read_json(O / 'UNIT-TIMEOUT-INSPECTION.json')
expected_outcomes = [('unit-tests', 'failed', -15), ('source', 'passed', 0), ('agent', 'passed', 0), ('construction', 'passed', 0), ('surface', 'passed', 0), ('impulse', 'passed', 0), ('documents', 'failed', 1)]
check('routine failed in both independent outer receipt and driver summary', r['returncode'] == s['exit_code'] == 1 and r['status'] == s['status'] == 'failed')
check('seven planned processes have final outcomes', [(x['id'], x['status'], x['returncode']) for x in s['steps']] == expected_outcomes and s['not_executed_steps'] == [])
check('both authorized operations positively completed', len(active['operations']) == 2 and all(x['status'] == 'completed' and 'returncode' in x and 'finished_at' in x for x in active['operations']) and active['active_processes'] == [] and active['unknown_operations'] == [])
check('source remains clean exact tested candidate', r['source_before'] == r['source_after'] and r['source_after']['commit'] == CANDIDATE and r['source_after']['tree'] == TREE and r['source_after']['all_dirty_status'] == '' and r['source_unchanged'])
check('driver source inventory unchanged', before == after and before['file_count'] == len(before['files']) == 18659 and s['source_unchanged'] and s['git_revision_unchanged'])
check('source inventory file hash matches summary', file_matches(V / 'routine-candidate/source-before.json', s['source_inventory']))
for key in ('stdout_identity', 'stderr_identity', 'entrypoint', 'wrapper'):
    check(f'outer {key} exact bytes', file_matches(Path(r[key]['path']), r[key]))
steps = {x['id']: x for x in s['steps']}
report_summaries = {}
for step in s['steps']:
    check(f"{step['id']} log exact bytes", file_matches(V / 'routine-candidate' / step['log'], step['log_identity']))
    for report in step['reports']:
        path = V / 'routine-candidate' / report['path']
        check(f'{report["path"]} exact bytes', file_matches(path, report))
        parsed = read_json(path)
        check(f'{report["path"]} summary matches actual report', parsed['summary'] == report['outcomes']['summary'])
        report_summaries[step['id']] = {'summary': parsed['summary'], 'pending_cases': report['pending_cases']}
unit = steps['unit-tests']
unit_bytes = (V / 'routine-candidate/logs/unit-tests.log').read_bytes()
unit_text = unit_bytes.decode()
check('unit timed out at declared 900 seconds', unit['reason'] == 'Exceeded 900 seconds' and unit['returncode'] == -15 and 900 <= unit['duration_seconds'] < 901)
check('unit has no completion footer', not re.search(r'^Ran \d+ tests? in ', unit_text, re.M))
check('independent partial log inspection still exact', sha(unit_bytes) == unit_inspection['log']['sha256'] and len(unit_bytes) == unit_inspection['log']['bytes'])
check('no observed failure error or skip result lines in partial unit log', not re.search(r'^(?:FAIL|ERROR):|\.\.\. (?:FAIL|ERROR|skipped)', unit_text, re.M))
check('strict partial result lines independently recounted', len(re.findall(r'^test_\w+ \([^)]+\) \.\.\. ok$', unit_text, re.M)) == 3370)

docs = read_json(V / 'routine-candidate/logs/documents.log')
doc_worker = read_json(V / 'DOCUMENTS-FAILURE-INSPECTION.json')
failures = docs['failures']
targets = sorted({posixpath.normpath(posixpath.join(posixpath.dirname(x['file']), x['target'])) for x in failures})
expected_targets = sorted(['CHATGPT-START-HERE.md', 'ROLE.md', '.agents/skills/ontokin-session/SKILL.md', '.agents/skills/ontokin-delivery/SKILL.md', '.agents/skills/ontokin-learning/SKILL.md'])
check('all 21 doc failures resolve to exactly five absent targets', docs['status'] == 'failed' and len(failures) == 21 and all(x['check'] == 'local_link' for x in failures) and targets == expected_targets)
check('validator diagnosis matches independently parsed failure list', failures == doc_worker['failures'])
driver = git_bytes(CANDIDATE, 'tools/check_local.py')
constants = {}
for n in ast.parse(driver).body:
    if isinstance(n, ast.Assign):
        for target in n.targets:
            if isinstance(target, ast.Name) and target.id in ('SOURCE_DIRS', 'ROOT_FILES'):
                constants[target.id] = list(ast.literal_eval(n.value))
    elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id in ('SOURCE_DIRS', 'ROOT_FILES'):
        constants[n.target.id] = list(ast.literal_eval(n.value))
check('AST copy inventory omits target roots', '.agents' not in constants['SOURCE_DIRS'] and 'CHATGPT-START-HERE.md' not in constants['ROOT_FILES'] and 'ROLE.md' not in constants['ROOT_FILES'])
check('AST copy inventory matches preserved diagnosis', constants == doc_worker['driver_copy_constants'])
deletions = sorted(line[3:] for line in s['workspace_git']['tracked_worktree_status'].splitlines() if line.startswith(' D '))
check('all five omissions already present in initial workspace status', deletions == expected_targets)
comparison_paths = sorted(set(targets + [f['file'] for f in failures] + ['tools/check_local.py', 'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py']))
identities = []
for path in comparison_paths:
    data = {rev: git_bytes(rev, path) for rev in (MAIN, CANDIDATE, CHECKPOINT)}
    record = {'path': path, 'bytes': len(data[CANDIDATE]), 'sha256': sha(data[CANDIDATE]), 'git_blob': sha(b'blob ' + str(len(data[CANDIDATE])).encode() + b'\0' + data[CANDIDATE]), 'equal_at_main_candidate_checkpoint': len(set(data.values())) == 1}
    # Actual Git object ID is SHA-1; SHA-256 above is content provenance, not Git identity.
    record['git_blob'] = hashlib.sha1(b'blob ' + str(len(data[CANDIDATE])).encode() + b'\0' + data[CANDIDATE]).hexdigest()
    check(f'doc diagnosis bytes unchanged main/candidate/checkpoint: {path}', record['equal_at_main_candidate_checkpoint'])
    authentic = V / 'candidate-checkout' / path
    copied = V / 'routine-candidate/workspace' / path
    check(f'authentic candidate bytes exact: {path}', authentic.read_bytes() == data[CANDIDATE])
    if path in targets:
        check(f'omitted from copied workspace: {path}', not copied.exists())
    else:
        check(f'copied referring/validator bytes exact: {path}', copied.read_bytes() == data[CANDIDATE])
    identities.append(record)
check('no release/product certification asserted', s['release_certified'] is False and s['full_product_conformance_certified'] is False)
check('final validator does not claim eligibility', results['integration_eligible'] is False)
routine_check_count = len(checks)
write('ROUTINE-EVIDENCE-REVIEW.json', {'schema': 'ontokin.c271.p02-independent-routine-evidence/1', 'reviewer': '/root/intake_audit', 'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'evidence_verification': 'passed' if all(x['passed'] for x in checks) else 'failed', 'routine_outcome': 'failed', 'integration_verdict': 'not_eligible', 'source_commit': CANDIDATE, 'source_tree': TREE, 'outer_duration_seconds': r['duration_seconds'], 'driver_duration_seconds': s['duration_seconds'], 'outcomes': [dict(id=x['id'], status=x['status'], returncode=x['returncode'], duration_seconds=x['duration_seconds']) for x in s['steps']], 'report_summaries': report_summaries, 'documentation': {'failures': failures, 'absent_targets': targets, 'copy_constants': constants, 'initial_copy_deletions': deletions, 'source_identities': identities, 'assessment': 'Five files exist in the authentic source but are excluded by the unchanged driver inventory. Initial copy status and exact referring/validator bytes establish this isolation cause for all 21 link failures. Static equality does not replace a baseline execution or waive the required driver.'}, 'unit_interpretation': 'Timeout and absent unittest footer leave complete-suite result unknown. tests_run=0 is footer parsing, not zero execution. Partial log has no observed assertion failure or skip; missing readback fixture predictions are not observed skips.', 'behavioral_reexecution': False, 'checks': checks, 'check_count': routine_check_count, 'failed_count': sum(not x['passed'] for x in checks)})

checks = []
manifest = read_json(V / 'RAW-EVIDENCE-MANIFEST.json')
receipt = read_json(V / 'RAW-EVIDENCE-VERIFICATION.json')
archive = V / 'RAW-EVIDENCE.zip'
check('final raw archive matches explicit expected bytes/hash', archive.stat().st_size == 4965080 and sha(archive.read_bytes()) == 'c4c973d40c4f6571def93b257877de69568bcd5fdca43bcfed92ff6acfc61e20')
check('final raw archive matches external receipt', file_matches(archive, receipt['archive']))
check('external manifest matches receipt', file_matches(V / 'RAW-EVIDENCE-MANIFEST.json', receipt['manifest']))
with zipfile.ZipFile(archive) as z:
    names = z.namelist()
    check('no duplicate names', len(names) == len(set(names)))
    check('safe relative non-symlink regular paths', all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n and not n.endswith('/') and not stat.S_ISLNK(i.external_attr >> 16) for n, i in zip(names, z.infolist())))
    check('ZIP CRC check', z.testzip() is None)
    check('archive manifest is exact external bytes', z.read('RAW-EVIDENCE-MANIFEST.json') == (V / 'RAW-EVIDENCE-MANIFEST.json').read_bytes())
    check('exact 73 payloads plus one manifest', len(names) == 74 and manifest['file_count'] == len(manifest['files']) == 73 and set(names) == {x['path'] for x in manifest['files']} | {'RAW-EVIDENCE-MANIFEST.json'})
    for item in manifest['files']:
        data = z.read(item['path'])
        check(f'manifest payload exact: {item["path"]}', len(data) == item['bytes'] and sha(data) == item['sha256'])
        check(f'payload exact preserved original: {item["path"]}', data == (V / item['path']).read_bytes())
    check('total payload bytes exact', sum(x['bytes'] for x in manifest['files']) == manifest['payload_bytes'] == 20322760)
check('archive declares exact tested source', manifest['source_revision'] == CANDIDATE)
delta = read_json(V / 'WORKSPACE-RECOVERY-DELTA.json')
check('copied-source exclusion has no unique changed files', delta['compared_file_count'] == 18659 and delta['new_or_modified_files'] == [] and delta['missing_original_files'] == [] and delta['original_outputs_deleted'] is False)
write('FINAL-RAW-EVIDENCE-REVIEW.json', {'schema': 'ontokin.c271.p02-independent-raw-evidence/1', 'reviewer': '/root/intake_audit', 'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'verdict': 'passed' if all(x['passed'] for x in checks) else 'failed', 'archive': identity(archive), 'payload_count': 73, 'member_count': 74, 'source_revision': CANDIDATE, 'behavioral_reexecution': False, 'integration_approval': False, 'checks': checks, 'check_count': len(checks), 'failed_count': sum(not x['passed'] for x in checks), 'limitation': 'Verified archived evidence and exact preserved originals. Root owns separate final handoff, blocked-state records, and saved-delivery verification.'})
write('FINAL-EVIDENCE-READ-SET.json', {'schema': 'ontokin.c271.p02-final-evidence-read-set/1', 'files': reads, 'git_reads': git_reads})
print(json.dumps({'routine_evidence_checks': routine_check_count, 'raw_archive_checks': len(checks), 'routine_verdict': 'failed', 'integration_verdict': 'not_eligible', 'archive_failed_checks': [x for x in checks if not x['passed']]}))
