#!/usr/bin/env python3
"""Read-only C227 candidate and evidence binding review; no product imports."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import pstats
import sqlite3
import subprocess

BASE = Path('/workspace/scratch/28482a5da524')
REPO = BASE / 'OntoKin'
OUT = BASE / 'candidate-review'
CANDIDATE = 'e6ba56df5d16f6ebab901ff77b163f59887bfb85'
TREE = '5a883585d135616ef6dfddb47309bb7ca5663149'
PARENT = '7a1cd57eb626a64ff3bab34c9d2974cb38b2a816'
EXECUTED = 'da007e1466c14812441bb8b18f8d2f8f01cbf1f6'
PREFIX = 'docs/engineering/torque-diagnosis-c227/'
DOC = REPO / PREFIX
checks = []
failures = []
cache = {}

def check(name, condition, **details):
    checks.append({'name': name, 'passed': bool(condition), **details})
    if not condition:
        failures.append(name)

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])

def blob(oid):
    if oid not in cache:
        cache[oid] = git('cat-file', 'blob', oid)
    return cache[oid]

def tree_map(ref):
    result = {}
    for record in git('ls-tree', '-rz', ref).split(b'\0'):
        if record:
            meta, name = record.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            result[name.decode()] = {'mode': mode, 'kind': kind, 'oid': oid}
    return result

def digest(data):
    return hashlib.sha256(data).hexdigest()

def loaded(path):
    return json.loads(path.read_text())

check('exact_candidate_head', git('rev-parse', 'HEAD').decode().strip() == CANDIDATE)
check('exact_candidate_tree', git('rev-parse', CANDIDATE + '^{tree}').decode().strip() == TREE)
check('candidate_parent_is_lease', git('rev-parse', CANDIDATE + '^').decode().strip() == PARENT)
check('clean_worktree', not git('status', '--porcelain', '--untracked-files=all'))
diff = git('diff', '--name-status', PARENT, CANDIDATE).decode()
(OUT / 'DIFF-NAME-STATUS.txt').write_text(diff)
changed = [line.split('\t') for line in diff.splitlines()]
shared = {'STATUS.md', 'docs/README.md', 'docs/engineering/review-integration-c221/RECOMMENDATIONS.json'}
check('exact_47_file_scope', len(changed) == 47 and
      all((status == 'A' and path.startswith(PREFIX)) or (status == 'M' and path in shared)
          for status, path in changed), files=len(changed))
old_tree, new_tree = tree_map(PARENT), tree_map(CANDIDATE)
check('all_previous_files_retained', set(old_tree) <= set(new_tree))
check('all_unrelated_blobs_and_modes_unchanged', all(new_tree[p] == value
      for p, value in old_tree.items() if p not in shared))
for _, path in changed:
    check('candidate_worktree_binding:' + path,
          (REPO / path).read_bytes() == blob(new_tree[path]['oid']))

# Bind every copied observation to the original external evidence.
pairs = {
    'diagnose_a08.py': BASE / 'diagnostic-author/diagnose_a08.py',
    'RUN-PLAN.json': BASE / 'diagnostic-author/RUN-PLAN.json',
    'RUN-PLAN.md': BASE / 'diagnostic-author/RUN-PLAN.md',
    'evidence/AUTHOR-CHECKS.json': BASE / 'diagnostic-author/AUTHOR-CHECKS.json',
    'evidence/MEASURED-SUMMARY.json': BASE / 'diagnostic-author/outcome/MEASURED-SUMMARY.json',
}
for name in ('APPROVAL.json', 'HARNESS-REVIEW-FINAL.json', 'BYTE-IDENTITY-RECONCILIATION.json', 'STATIC-BINDING-CHECKS.json'):
    pairs['evidence/' + name] = BASE / 'diagnosis-review' / name
for path in (DOC / 'evidence/run').rglob('*'):
    if path.is_file():
        pairs[path.relative_to(DOC).as_posix()] = BASE / 'c227-diagnostic-run' / path.relative_to(DOC / 'evidence/run')
for path in (DOC / 'evidence/outcome-review').rglob('*'):
    if path.is_file():
        pairs[path.relative_to(DOC).as_posix()] = BASE / 'diagnosis-review/outcome' / path.relative_to(DOC / 'evidence/outcome-review')
for name, original in pairs.items():
    data = (DOC / name).read_bytes()
    check('original_evidence_binding:' + name, original.is_file() and data == original.read_bytes(),
          sha256=digest(data), bytes=len(data), original=str(original))
for root, manifest_name in ((DOC / 'evidence/run', 'EVIDENCE-SHA256.json'),
                            (DOC / 'evidence/outcome-review', 'SHA256-MANIFEST.json')):
    rows = loaded(root / manifest_name)['files']
    for row in rows:
        data = (root / row['path']).read_bytes()
        check('manifest_binding:' + str(root.relative_to(DOC)) + '/' + row['path'],
              digest(data) == row['sha256'] and len(data) == row['bytes'])

approval = loaded(DOC / 'evidence/APPROVAL.json')
plan = loaded(DOC / 'RUN-PLAN.json')
check('approval_is_explicit', approval['approved'] is True and approval['implementationReconciled'] is True)
for field, path in [('planSha256', 'RUN-PLAN.json'), ('harnessSha256', 'diagnose_a08.py'),
                    ('identityReviewSha256', 'evidence/BYTE-IDENTITY-RECONCILIATION.json')]:
    check('approval_hash:' + field, approval[field] == digest((DOC / path).read_bytes()))
check('approved_source_and_tree', approval['sourceCommit'] == EXECUTED and
      approval['sourceTree'] == '32ac0f19681ea90d8d2c55cc3e5e1daaeca4ae54')
check('exact_product_limits', plan['productLimits'] == {'max_operations': 1000000, 'max_elapsed_ms': 30000})
check('exact_finite_schedule', plan['modes'] == ['baseline', 'cprofile'] and plan['processTimeoutSeconds'] == 90)

# Recompute source identities without importing any OntoKin module.
identity = loaded(DOC / 'evidence/BYTE-IDENTITY-RECONCILIATION.json')
for revision in identity['revisions']:
    entries = tree_map(revision['ref'])
    check('implementation_tree:' + revision['ref'],
          git('rev-parse', revision['ref'] + '^{tree}').decode().strip() == revision['tree'])
    py_names = sorted(p for p in entries if p.startswith('ontokin/') and p.count('/') == 1 and p.endswith('.py'))
    check('complete_implementation_inventory:' + revision['ref'], py_names == [r['path'] for r in revision['files']])
    package_digest = hashlib.sha256()
    for row in revision['files']:
        entry = entries[row['path']]
        data = blob(entry['oid'])
        check('implementation_blob:' + revision['ref'] + ':' + row['path'],
              entry['oid'] == row['gitBlob'] and entry['mode'] == row['gitMode'] and
              len(data) == row['bytes'] and digest(data) == row['sha256'])
        package_digest.update(Path(row['path']).name.encode() + b'\0' + data + b'\0')
    check('recomputed_implementation_digest:' + revision['ref'],
          'sha256:' + package_digest.hexdigest() == revision['packageSourceDigest'])
check('sole_added_module', len(identity['historicalCurrentDelta']) == 1 and
      identity['historicalCurrentDelta'][0]['path'] == 'ontokin/semantic_export.py' and
      identity['historicalCurrentDelta'][0]['historical'] is None)
inputs = loaded(DOC / 'evidence/run/INPUTS.json')
executed_tree = tree_map(EXECUTED)
check('exact_protected_input_count', len(inputs['protectedInputs']) == 558)
for row in inputs['protectedInputs']:
    entry = executed_tree[row['path']]
    data = blob(entry['oid'])
    check('protected_input:' + row['path'], entry['oid'] == row['gitBlob'] and entry['mode'] == row['mode'] and
          digest(data) == row['sha256'] and len(data) == row['bytes'] and new_tree[row['path']] == entry)

tracker_path = 'docs/engineering/review-integration-c221/RECOMMENDATIONS.json'
old_tracker = json.loads(blob(old_tree[tracker_path]['oid']))
tracker = loaded(REPO / tracker_path)
old_tasks = {t['id']: t for t in old_tracker['tasks']}
tasks = {t['id']: t for t in tracker['tasks']}
check('nine_tasks_and_41_unchanged_acceptance_criteria', len(tasks) == 9 and
      tasks.keys() == old_tasks.keys() and sum(len(t['acceptance']) for t in tasks.values()) == 41 and
      all(t['acceptance'] == old_tasks[k]['acceptance'] for k, t in tasks.items()))
check('other_eight_task_records_unchanged', all(t == old_tasks[k] for k, t in tasks.items() if k != 'R02'))
check('r02_retains_last_aggregate_attempt', tasks['R02']['lastAttempt'] == old_tasks['R02']['lastAttempt'])
check('r02_still_blocked', tasks['R02']['status'] == 'blocked')
unchanged_r02_keys = set(old_tasks['R02']) - {'evidence', 'remainingLimits', 'nextAction'}
check('other_r02_fields_unchanged', all(tasks['R02'][k] == old_tasks['R02'][k] for k in unchanged_r02_keys))
for key in ('carryForwardRequired', 'currentSourceAndNativeExecutionAuthorized', 'ordering', 'completionRule'):
    check('tracker_policy_preserved:' + key, tracker[key] == old_tracker[key])
status_before = blob(old_tree['STATUS.md']['oid']).decode()
status_after = (REPO / 'STATUS.md').read_text()
check('status_previous_body_preserved', status_before.splitlines()[:3] == status_after.splitlines()[:3] and
      status_after[status_after.index('## C226 R02:'):] == status_before[status_before.index('## C226 R02:'):])
check('live_lease_text_preserved', 'c227-main-28482a5da524' in status_after and '14:20:27' in status_after)

# Inspect immutable raw stores independently and verify the claimed numeric outcomes.
measured = loaded(DOC / 'evidence/MEASURED-SUMMARY.json')
summary = loaded(DOC / 'evidence/run/RUN-SUMMARY.json')
check('schedule_consumed_exactly_once', summary['consumedSlots'] == 2 and summary['remainingSlots'] == [] and summary['scopeComplete'] is True)
check('no_product_methods_aggregate_native_or_repair', summary['productTestMethods'] == 0 and
      summary['aggregateRun'] is False and summary['nativeStarts'] == 0 and summary['repairPerformed'] is False)
for outcome in measured['outcomes']:
    mode = outcome['mode']
    dbpath = DOC / 'evidence/run' / outcome['database']['path']
    before = digest(dbpath.read_bytes())
    with sqlite3.connect(dbpath.as_uri() + '?mode=ro&immutable=1', uri=True) as con:
        check('sqlite_integrity:' + mode, con.execute('PRAGMA integrity_check').fetchall() == [('ok',)])
        rows = con.execute('SELECT id, state, response FROM requests ORDER BY sequence').fetchall()
        check('two_original_requests:' + mode, [r[0] for r in rows] == ['seed-create', 'seed-export'])
        export = json.loads(rows[1][2])
        budget = export['execution_budget']
        check('actual_export_measurement:' + mode, export['status'] == outcome['export']['status'] and
              budget['consumed_operations'] == outcome['export']['consumedOperations'] and
              budget['elapsed_ms'] == outcome['export']['elapsedMs'])
        check('actual_budget_preserved:' + mode, all(budget[k] == {'max_elapsed_ms': 30000, 'max_operations': 1000000}
              for k in ('effective', 'host_ceilings', 'source_request')))
        for table, count in outcome['database']['tableCounts'].items():
            check('actual_table_count:' + mode + ':' + table,
                  con.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] == count)
        for artifact in con.execute('SELECT id, data, sha256 FROM artifacts').fetchall():
            hashed = digest(artifact[1])
            check('actual_artifact_bytes:' + mode, len(artifact[1]) == 2447148 and
                  hashed == artifact[2] == '6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa' and
                  artifact[0] == 'artifact:' + hashed)
    check('raw_database_unchanged:' + mode, digest(dbpath.read_bytes()) == before == outcome['database']['sha256'])
    check('cleanup_and_source_preserved:' + mode, outcome['originalClassCleanup'] is True and
          outcome['sourceAndInputsUnchanged'] is True and outcome['semanticExportModuleImported'] is False and
          outcome['testMethodsExecuted'] == 0 and outcome['process']['processGroupAbsent'] is True and
          outcome['process']['timedOut'] is False)
stats = pstats.Stats(str(DOC / 'evidence/run/2-cprofile/setup.prof'), stream=io.StringIO())
check('binary_profile_totals', stats.total_calls == measured['profile']['functionCalls'] == 115700600 and
      stats.prim_calls == measured['profile']['primitiveCalls'] == 115612660)
for row in measured['profile']['selectedHotspots']:
    candidates = [(key, values) for key, values in stats.stats.items() if key[0].endswith('/' + row['filename']) and
                  key[1] == row['line'] and key[2] == row['function']]
    check('binary_profile_hotspot:' + row['filename'] + ':' + str(row['line']), len(candidates) == 1 and
          candidates[0][1][:4] == (row['primitiveCalls'], row['totalCalls'], row['selfSeconds'], row['cumulativeSeconds']))
outcome_review = loaded(DOC / 'evidence/outcome-review/OUTCOME-REVIEW.json')
check('independent_outcome_audit_passes', outcome_review['status'] == 'approved' and
      outcome_review['checkCount'] == 4779 and all(c['passed'] for c in outcome_review['checks']) and
      outcome_review['productExecutionsByReviewer'] == 0)
guard = loaded(DOC / 'evidence/HISTORICAL-GUARD-STUDIES.json')
for row in guard['files']:
    data = blob(executed_tree[row['path']]['oid'])
    check('historical_guard_binding:' + row['path'], len(data) == row['bytes'] and digest(data) == row['sha256'])
historical_artifact_sha = '6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa'
check('historical_artifact_digest_retained', historical_artifact_sha in
      blob(executed_tree['docs/engineering/torque-verification-c160/measurements.json']['oid']).decode())
doclog = BASE / 'handoff-next/evidence/c227-candidate-documentation-check.log'
doc_result = loaded(doclog)
check('candidate_documentation_check_report', not doc_result['failures'] and doc_result['sources_verified'] == 29 and
      doc_result['links']['local_links'] == 4758)

record = {
    'schema': 'ontokin.c227.independent-candidate-review/0.1',
    'status': 'approved' if not failures else 'rejected',
    'candidate': CANDIDATE, 'tree': TREE, 'parentLeaseCommit': PARENT,
    'executedSource': EXECUTED, 'reviewedAtUtc': datetime.now(timezone.utc).isoformat(),
    'checkCount': len(checks), 'failures': failures, 'checks': checks,
    'manualJudgments': [
        'Documentation distinguishes isolated baseline success from overhead-affected profiling and leaves historical causal attribution unresolved.',
        'R02 remains blocked; zero artifact-read methods and zero aggregates ran in C227.',
        'The next separately selected fresh default aggregate is justified as the next unmet evidence gate, with exact prerequisite and independent plan review before execution.',
        'No source repair, guard removal, changed operation accounting, expanded native schedule or broader acceptance is inferred.',
        'All previous repository files and unrelated blobs remain exact; STATUS prior body and tracker obligations preserve held work and consumed schedules.',
    ],
    'productExecutionsByReviewer': 0, 'repositoryEditsByReviewer': 0,
    'limitations': ['Review binds this exact local candidate; publication and final-save outcomes require later independent observation.',
                    'Process completion and absence are preserved observed receipts, not claims that the reviewer witnessed the historical process exits.'],
}
(OUT / 'CANDIDATE-REVIEW.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'status': record['status'], 'checkCount': len(checks), 'failures': failures,
                  'report': str(OUT / 'CANDIDATE-REVIEW.json')}))
