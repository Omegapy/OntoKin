"""Read-only audit of the published blocked source and actual record evidence."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

B = Path('/workspace/scratch/c219bb61a617')
R = B / 'OntoKin'
O = B / 'final-source-review'
REV = '70a658c31085bf8dd78d79663c57f8e3cdb28ceb'
TREE = '77ee621cdfb00acf637828ce71f3384b4dd8275c'
PARENT = '15b1dd985b59cf037ebbeae733c16a54ca87f83d'
CANDIDATE = '88bc8b51b3963b7072375edac6400b6e6a4532e4'
MAIN = 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
F = 'docs/engineering/localized-repair-c271/finalization-20261120/'
checks = []
reads = []
commands = []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check(name, ok, category='source'):
    checks.append({'name': name, 'category': category, 'passed': bool(ok)})

def read(path):
    data = path.read_bytes()
    reads.append({'path': str(path), 'bytes': len(data), 'sha256': sha(data)})
    return data

def load(path):
    return json.loads(read(path))

def git(*args):
    argv = ['git', '-C', str(R), *args]
    p = subprocess.run(argv, capture_output=True, check=False)
    commands.append({'argv': argv, 'returncode': p.returncode, 'stdout_bytes': len(p.stdout), 'stdout_sha256': sha(p.stdout), 'stderr': p.stderr.decode()})
    if p.returncode:
        raise RuntimeError(str(commands[-1]))
    return p.stdout

def get(path, rev=REV):
    return git('show', rev + ':' + path)

def get_json(path, rev=REV):
    return json.loads(get(path, rev))

def tree(rev):
    result = {}
    for entry in git('ls-tree', '-r', '-l', '-z', rev).split(b'\0'):
        if not entry:
            continue
        meta, path = entry.decode().split('\t', 1)
        mode, kind, blob, size = meta.split()
        result[path] = {'mode': mode, 'kind': kind, 'git_blob': blob, 'bytes': int(size)}
    return result

def remote(name):
    item = load(O / 'observations' / name)['response']
    if 'status' in item:
        assert item['status'] == 'fulfilled'
        item = item['value']
    assert item['isError'] is False
    item = item['structuredContent']
    return json.loads(item['content']) if 'content' in item else item

intent = load(B / 'session/BLOCKED-PUBLICATION-INTENT.json')
publication = load(B / 'session/BLOCKED-PUBLICATION.json')
branch = remote('remote-branch.json')
main = remote('remote-main.json')
commit = remote('remote-commit.json')
pr = remote('remote-pr274-updated.json')
issue = remote('remote-issue273-updated.json')['issue']
old_pr = remote('remote-pr274.json')
old_issue = remote('remote-issue273.json')['issue']
check('remote branch exact reviewed revision', branch['object']['sha'] == REV, 'remote')
check('remote main unchanged', main['object']['sha'] == MAIN, 'remote')
check('remote commit exact tree and parent', commit['sha'] == REV and commit['tree']['sha'] == TREE and [p['sha'] for p in commit['parents']] == [PARENT], 'remote')
check('local immutable objects match remote identities', git('show', '-s', '--format=%H%n%T%n%P', REV).decode().splitlines() == [REV, TREE, PARENT], 'remote')
check('PR remains open draft unmerged at reviewed source', pr['state'] == 'open' and pr['draft'] is True and pr['merged'] is False and pr['head_sha'] == REV and pr['base_sha'] == MAIN, 'remote')
check('scope issue remains open', issue['state'] == 'open', 'remote')
for name, body, old in [('PR', pr['body'], old_pr['body']), ('issue', issue['body'], old_issue['body'])]:
    check(name + ' current external text records actual blocked result', 'blocked validation' in body and 'unit suite exceeded 900 seconds' in body and '21 links to five tracked instruction files' in body and '282 methods' in body and REV in body and 'does **not** approve integration or parent closure' in body, 'remote')
    check(name + ' prior body retained verbatim', old in body, 'remote')

t = tree(REV)
candidate_tree = tree(CANDIDATE)
delta = git('diff', '--no-renames', '--name-only', '-z', PARENT, REV).decode().strip('\0').split('\0')
check('publication intent and receipt exact identities', intent['commit'] == publication['commit'] == REV and intent['tree'] == publication['tree'] == TREE and intent['expected_head'] == publication['parent'] == PARENT and publication['main_write'] is False and publication['conditional_nonforce_update'] is True)
check('all 73 changed payloads enumerated exactly', len(intent['files']) == len(delta) == 73 and {x['path'] for x in intent['files']} == set(delta))
payload_summary = []
for item in intent['files']:
    path = item['path']
    data = get(path)
    check('published tree mode/blob/size equals staged intent: ' + path, t[path]['mode'] == item['mode'] and t[path]['git_blob'] == item['git_blob'] and t[path]['bytes'] == item['bytes'], 'publication_payload')
    check('published payload SHA256 equals staged intent: ' + path, len(data) == item['bytes'] and sha(data) == item['sha256'], 'publication_payload')
    check('published blob hashes to declared Git object: ' + path, hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == item['git_blob'], 'publication_payload')
    payload_summary.append({'path': path, **t[path], 'sha256': sha(data)})
cumulative = git('diff', '--no-renames', '--name-only', '-z', CANDIDATE, REV).decode().strip('\0').split('\0')
check('candidate-to-published delta only phase metadata/evidence', all(p.startswith(F) or p.startswith('docs/workflow/tasks/C271/') or p == 'docs/workflow/CURRENT.json' for p in cumulative))
check('publication delta only declared phase metadata/evidence', all(p.startswith(F) or p.startswith('docs/workflow/tasks/C271/') or p == 'docs/workflow/CURRENT.json' for p in delta))

reuse = load(B / 'validation/preparation/REUSE-INPUT-GIT-MANIFEST.json')
for item in reuse['files']:
    check('exact reused input: ' + item['path'], t[item['path']] == {k: item[k] for k in ('mode', 'kind', 'git_blob', 'bytes')}, 'reuse_input')
p01 = load(B / 'integration-review/P01-REUSE-IDENTITIES.json')
for item in p01['inputs']:
    data = get(item['path'])
    check('exact original P01 execution input: ' + item['path'], t[item['path']]['git_blob'] == item['git_blob'] and len(data) == item['bytes'] and sha(data) == item['sha256'], 'p01_input')
for path in p01['control_and_runner_paths']:
    check('frozen control/runner unchanged: ' + path, t[path] == candidate_tree[path], 'p01_frozen')

review_dir = B / 'integration-review'
review_files = sorted(p for p in review_dir.rglob('*') if p.is_file())
published_review_files = sorted(p for p in t if p.startswith(F + 'independent-review/'))
check('all 34 frozen reviewer files published exactly once', len(review_files) == len(published_review_files) == 34 and {F + 'independent-review/' + str(p.relative_to(review_dir)) for p in review_files} == set(published_review_files), 'frozen_review')
for p in review_files:
    check('frozen reviewer bytes preserved: ' + str(p.relative_to(review_dir)), get(F + 'independent-review/' + str(p.relative_to(review_dir))) == read(p), 'frozen_review')
artifact_manifest = load(review_dir / 'ARTIFACTS.json')
for item in artifact_manifest['files']:
    data = read(review_dir / item['path'])
    check('frozen reviewer artifact manifest still valid: ' + item['path'], len(data) == item['bytes'] and sha(data) == item['sha256'], 'frozen_review')
for name in ('ACTIVE-OPERATIONS.json', 'DOCUMENTS-FAILURE-INSPECTION.json', 'PARTIAL-UNIT-LOG-ACCOUNTING.json', 'RAW-EVIDENCE-MANIFEST.json', 'RAW-EVIDENCE-VERIFICATION.json', 'RAW-EVIDENCE.zip', 'REPORT.md', 'RESULTS.json'):
    check('published validation bytes equal original: ' + name, get(F + 'verification/' + name) == read(B / 'validation' / name), 'raw_evidence')
check('published raw ZIP exact independently verified digest', sha(get(F + 'verification/RAW-EVIDENCE.zip')) == 'c4c973d40c4f6571def93b257877de69568bcd5fdca43bcfed92ff6acfc61e20', 'raw_evidence')
for prefix, original in [('operation-history/', B / 'session'), ('blocked-record-preflight/', B / 'session/blocked-record-preflight'), ('blocked-final-preflight/', B / 'session/blocked-final-preflight')]:
    for path in sorted(p for p in t if p.startswith(F + prefix)):
        rel = path.removeprefix(F + prefix)
        check('published original operation/log retained: ' + prefix + rel, get(path) == read(original / rel), 'preserved_history')

task = get_json('docs/workflow/tasks/C271/task.json')
old_task = get_json('docs/workflow/tasks/C271/task.json', PARENT)
current = get_json('docs/workflow/CURRENT.json')
outcome = get_json(F + 'PHASE-OUTCOME.json')
review = get_json(F + 'independent-review/INTEGRATION-REVIEW.json')
named = {x['name']: x for x in task['checks']}
check('task/CURRENT consistently blocked and open', task['status'] == 'blocked' and current['active_task'] == 'C271' and current['next_action']['status'] == 'blocked', 'metadata')
check('R01/R02 done and R03-R05 unmet', {x['id']: x['status'] for x in task['requirements']} == dict(R01='done', R02='done', R03='not_done', R04='not_done', R05='not_done'), 'metadata')
check('P01 done and P02 incomplete', {x['id']: x['status'] for x in task['plan']} == dict(P01='done', P02='in_progress'), 'metadata')
check('requirement acceptance text unchanged', [(x['id'], x['acceptance']) for x in task['requirements']] == [(x['id'], x['acceptance']) for x in old_task['requirements']], 'metadata')
for old in old_task['checks']:
    check('existing required check not weakened: ' + old['name'], named[old['name']]['required'] == old['required'] and named[old['name']]['command'] == old['command'], 'metadata')
check('routine failure remains required', named['required routine local driver before integration']['required'] is True and named['required routine local driver before integration']['result'] == 'failed', 'metadata')
check('new integration acceptance check required and failed', named['independent P02 integration acceptance review']['required'] is True and named['independent P02 integration acceptance review']['result'] == 'failed', 'metadata')
check('independent acceptance check references actual published reports', set(named['independent P02 integration acceptance review']['evidence']) == {F + 'independent-review/INTEGRATION-REVIEW.json', F + 'independent-review/REPORT.md'} and all(p in t for p in named['independent P02 integration acceptance review']['evidence']), 'metadata')
check('R03 includes independent negative verdict', F + 'independent-review/INTEGRATION-REVIEW.json' in next(x for x in task['requirements'] if x['id'] == 'R03')['evidence'], 'metadata')
check('PHASE-OUTCOME corrected report path exists', outcome['evidence']['independent_review'] == 'independent-review/REPORT.md' and F + outcome['evidence']['independent_review'] in t, 'metadata')
check('recorded independent verdict matches frozen review', outcome['independent_acceptance']['verdict'] == review['verdict'] == 'not_eligible' and outcome['independent_acceptance']['integration_approved'] is review['integration_approved'] is False and outcome['independent_acceptance']['mandatory_findings'] == [x['id'] for x in review['mandatory_findings']], 'metadata')
check('no integration lease merge or final save asserted', outcome['integration_performed'] is False and outcome['main_lease'] == 'not_held' and task['completion']['merge_commit'] is None and task['delivery']['status'] == 'pending' and task['delivery']['partial'] is True and task['session_phase']['delivery_confirmed'] is False, 'metadata')
check('prior phase and delivery history unchanged', task['prior_session_phases'] == old_task['prior_session_phases'] and task['prior_phase_deliveries'] == old_task['prior_phase_deliveries'], 'metadata')
location = get(F + 'EVIDENCE-LOCATION.md').decode()
check('evidence location explains original paths and archive recovery', '../validation/' in location and 'verification/RAW-EVIDENCE.zip' in location and '73 raw payload files' in location and 'exact bytes' in location and 'independent-review/REPORT.md' in location, 'metadata')
check('location map preserves failed gate and pending delivery boundary', 'do not complete the parent task' in location or 'does not change behavior or repair either failed gate' in location, 'metadata')

record = load(B / 'session/final-source-record-checks/CHECKS.json')
check('fresh record checks bind exact clean published commit/tree', record['expected_commit'] == record['source_before']['commit'] == REV and record['expected_tree'] == record['source_before']['tree'] == TREE and record['source_before'] == record['source_after'] and record['source_before']['all_dirty_status'] == '' and record['source_unchanged'] is True, 'fresh_records')
check('both final record processes completed passed', record['status'] == 'passed' and len(record['checks']) == 2 and {x['name'] for x in record['checks']} == {'workflow', 'documentation'} and all(x['returncode'] == 0 and x['result'] == 'passed' and x['finished_at'] for x in record['checks']), 'fresh_records')
check('fresh record-only run has no active or unknown process', record['behavioral_reruns'] is False and record['active_processes'] == [] and record['unknown_operations'] == [], 'fresh_records')
for item in record['checks']:
    for stream in ('stdout', 'stderr'):
        data = read(Path(item[stream]['path']))
        check('fresh ' + item['name'] + ' ' + stream + ' exact bytes', len(data) == item[stream]['bytes'] and sha(data) == item[stream]['sha256'], 'fresh_records')
    check('fresh observed output matches parsed stdout: ' + item['name'], json.loads(Path(item['stdout']['path']).read_text()) == item['observed_result'], 'fresh_records')
    result = item['observed_result']
    check('fresh parsed success with no reported error: ' + item['name'], (result.get('passed') is True and result.get('errors') == []) if item['name'] == 'workflow' else (result['status'] == 'passed' and result['failures'] == []), 'fresh_records')
for item in record['planned_checks']:
    entry = item['entrypoint']
    path = str(Path(entry['path']).relative_to(R))
    data = get(path)
    check('fresh validator entrypoint matches published source: ' + item['name'], len(data) == entry['bytes'] and sha(data) == entry['sha256'], 'fresh_records')

failed = [x for x in checks if not x['passed']]
report = {'schema': 'ontokin.c271.p02-final-published-source-audit/1', 'reviewer': '/root/intake_audit', 'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'source_readiness': 'verified_blocked_partial_source' if not failed else 'failed_audit', 'integration_verdict': 'not_eligible', 'integration_approved': False, 'parent_closure_approved': False, 'commit': REV, 'tree': TREE, 'parent': PARENT, 'main': MAIN, 'staged_published_files': len(delta), 'frozen_review_files': len(review_files), 'reuse_input_files': len(reuse['files']), 'original_P01_inputs': len(p01['inputs']), 'frozen_control_runner_files': len(p01['control_and_runner_paths']), 'candidate_to_source_changed_paths': cumulative, 'publication_payloads': payload_summary, 'fresh_record_checks': {'path': str(B / 'session/final-source-record-checks/CHECKS.json'), 'status': record['status'], 'source_before': record['source_before'], 'source_after': record['source_after']}, 'checks': checks, 'check_count': len(checks), 'failed_count': len(failed), 'external_status_followup': {'initial_description': 'PR/issue bodies still described verification as pending', 'resolution': 'Root updated current blocked status and preserved prior bodies; independent second reads confirm resolution', 'observations_retained': True}, 'no_behavioral_reexecution': True, 'frozen_integration_review_modified': False, 'source_repository_modified': False, 'scope_limits': ['Passing source/record audit is not passing mandatory routine validation', 'Original 900-second unit timeout and five-file/21-link copied-workspace failure remain unresolved', 'Final ZIP, saved prompts and later receipt remain outside this audit', 'No integration, closure, repair, product/release/native/compatibility certification']}
(O / 'AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
(O / 'READ-SET.json').write_text(json.dumps({'schema': 'ontokin.final-source-read-set/1', 'prior_governing_reads': '../integration-review/READ-SET.json', 'files': reads, 'git_reads': commands}, indent=2) + '\n')
print(json.dumps({'checks': len(checks), 'failed_count': len(failed), 'failed': failed, 'verdict': report['source_readiness']}))
