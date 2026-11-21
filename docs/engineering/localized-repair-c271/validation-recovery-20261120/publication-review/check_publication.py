#!/usr/bin/env python3
"""Bounded read-only final publication and raw-evidence preservation check."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

BASE = Path('/workspace/scratch/7010345bc259')
REPO = BASE / 'OntoKin'
OUT = BASE / 'review/final_publication'
PREFIX = 'docs/engineering/localized-repair-c271/validation-recovery-20261120/'
SHA = '633c5097b2c5b870a13baa33a095a91eaa241eea'
TREE = '7f8eb385de71c6dd202389ad09113b779a6dc4b8'
CODE = 'fea1aa6fb3712c5283dde197295b2d3cbf925d36'
MAIN = 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
rows = []


def ident(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def check(label, ok, **detail):
    rows.append({'check': label, 'passed': bool(ok), **detail})


def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(REPO), *args],
                                   env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})


def frozen(path):
    return git('show', SHA + ':' + path)


OUT.mkdir(parents=True, exist_ok=True)
check('exact_frozen_commit_tree', git('rev-parse', SHA + '^{tree}').decode().strip() == TREE)
check('local_frozen_checkout_clean', git('rev-parse', 'HEAD').decode().strip() == SHA
      and not git('status', '--porcelain=v1'))
for path in ('tools/check_local.py', 'tests/test_local_checks.py'):
    check('technical_source_unchanged', frozen(path) == git('show', CODE + ':' + path), path=path)
changed = git('diff', '--name-only', CODE, SHA).decode().splitlines()
check('publication_delta_is_records_only', all(p.startswith('docs/') for p in changed), paths=changed)
publication = json.loads((BASE / 'session/PUBLISH-02-READBACK.json').read_bytes())
check('durable_expected_head_publication', publication['intended_parent'] == CODE
      and publication['created_commit'] == SHA and publication['intended_tree'] == TREE
      and publication['ref_result']['success'] is True and publication['actual_main'] == MAIN)
pr = publication['remote_pr']
check('durable_PR_state', pr['head_sha'] == SHA and pr['base_sha'] == MAIN and pr['state'] == 'open'
      and pr['draft'] is True and pr['merged'] is False)
readback = publication['exact_file_readback']
check('exact_outcome_blob_readback', readback['revision'] == SHA
      and git('rev-parse', SHA + ':' + readback['path']).decode().strip() == readback['blob'])

archive_path = REPO / PREFIX / 'RAW-EVIDENCE.zip'
archive_raw = archive_path.read_bytes()
archive_identity = ident(archive_raw)
check('raw_archive_expected_identity', archive_identity == {'bytes': 2062999, 'sha256': '06fb8cbfcbfd971285d406f60b64f7638f9524b592ac0b2573474b8c3edda68c'})
check('raw_archive_equals_frozen_git', archive_raw == frozen(PREFIX + 'RAW-EVIDENCE.zip'))
manifest_raw = frozen(PREFIX + 'RAW-EVIDENCE-MANIFEST.json')
manifest = json.loads(manifest_raw)
raw_receipt = json.loads(frozen(PREFIX + 'RAW-EVIDENCE-VERIFICATION.json'))
check('raw_archive_external_receipt', raw_receipt['passed'] is True
      and {k: raw_receipt['archive'][k] for k in ('bytes', 'sha256')} == archive_identity)
with zipfile.ZipFile(archive_path) as archive:
    names = archive.namelist()
    check('raw_archive_CRC', archive.testzip() is None)
    check('raw_archive_paths_unique_safe', len(names) == len(set(names))
          and all(not PurePosixPath(p).is_absolute() and '..' not in PurePosixPath(p).parts and '\\' not in p for p in names))
    check('raw_manifest_internal_external_equal', archive.read('MANIFEST-SHA256.json') == manifest_raw)
    payloads = manifest['payloads']
    expected = [p['path'] for p in payloads]
    check('raw_archive_exact_inventory', len(names) == 109 and len(payloads) == 108
          and len(expected) == len(set(expected)) and set(names) == set(expected) | {'MANIFEST-SHA256.json'})
    payload_errors = []
    local_errors = []
    for entry in payloads:
        raw = archive.read(entry['path'])
        if ident(raw) != {k: entry[k] for k in ('bytes', 'sha256')}:
            payload_errors.append(entry['path'])
        local = BASE / entry['path']
        if not local.is_file() or raw != local.read_bytes():
            local_errors.append(entry['path'])
    check('all_raw_payload_hashes_match', not payload_errors, payloads=len(payloads), failures=payload_errors)
    check('all_raw_payloads_equal_originals', not local_errors, payloads=len(payloads), failures=local_errors)
    prior_manifest = json.loads((BASE / 'review/final/ARTIFACTS.json').read_bytes())
    prior_missing = [e['path'] for e in prior_manifest['files']
                     if 'review/final/' + e['path'] not in names
                     or ident(archive.read('review/final/' + e['path'])) != {k: e[k] for k in ('bytes', 'sha256')}]
    check('entire_prior_final_review_retained', not prior_missing, payloads=len(prior_manifest['files']), failures=prior_missing)
    preserved_failures = ['preparation/copy-repair/red/stderr.log', 'validation/readback-preflight.json',
                          'review/final/ATTEMPT-01.log', 'review/final/REVIEW-ATTEMPTS.json']
    check('failure_evidence_retained', all(p in names for p in preserved_failures))
    check('archive_contains_commands_logs_reviews', any(p.endswith('.log') for p in names)
          and 'session/run_candidate_checks.py' in names and 'review/final/REPORT.md' in names)

acceptance_raw = frozen(PREFIX + 'FINAL-ACCEPTANCE.json')
check('published_acceptance_is_original', acceptance_raw == (BASE / 'review/final/FINAL-ACCEPTANCE.json').read_bytes())
acceptance = json.loads(acceptance_raw)
outcome = json.loads(frozen(PREFIX + 'PHASE-OUTCOME.json'))
task = json.loads(frozen('docs/workflow/tasks/C271/task.json'))
phase = json.loads(frozen(PREFIX + 'PHASE.json'))
current = json.loads(frozen('docs/workflow/CURRENT.json'))
check('actual_final_verdict_attached', outcome['independent_review']['status'] == 'complete_not_eligible'
      and outcome['independent_review']['verdict'] == acceptance['verdict']
      and outcome['independent_review']['r03_accepted'] is False
      and outcome['independent_review']['minimal_repair_approved_for_retained_partial'] is True
      and outcome['independent_review']['integration_approved'] is False
      and outcome['independent_review']['parent_closure_approved'] is False)
check('phase_execution_claims_preserve_original_candidate', outcome['source_commit'] == CODE
      and phase['code_candidate'] == CODE and phase['full_routine_executed'] is False
      and outcome['required_routine']['status'] == 'not_run' and outcome['p02_failures']['waived'] is False)
check('parent_and_delivery_unfinished', task['status'] == 'blocked'
      and {r['id']: r['status'] for r in task['requirements']} == {'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'}
      and outcome['delivery']['status'] == 'pending' and outcome['delivery']['partial'] is True
      and task['completion']['merge_commit'] is None and task['completion']['branch_disposition'] == 'retained')
check('current_task_blocked_no_integration', current['active_task'] == 'C271'
      and current['next_action']['status'] == 'blocked' and outcome['integration']['performed'] is False
      and outcome['integration']['main_lease_held'] is False)
check('failed_R03_review_remains_required', any(c['required'] and c['result'] == 'failed'
      and 'P03' in c['name'] and 'independent' in c['name'].lower() for c in task['checks']))
check('original_execution_summary_preserved', frozen(PREFIX + 'EXECUTION-CHECKS.json') == (BASE / 'validation/CHECKS.json').read_bytes())

record_root = BASE / 'session/final-source-record-checks'
record_checks = json.loads((record_root / 'CHECKS.json').read_bytes())
check('fresh_record_checks_exact_frozen_source', record_checks['source'] == {'commit': SHA, 'tree': TREE}
      and record_checks['source_clean_and_unchanged'] is True
      and {c['name'] for c in record_checks['checks']} == {'workflow', 'documentation'})
for row in record_checks['checks']:
    raw = (record_root / row['log']).read_bytes()
    check('fresh_record_check_pass_and_log_identity', row['returncode'] == 0
          and ident(raw) == {k:row[k] for k in ('bytes','sha256')}, role=row['name'])
    if row['name'] == 'documentation':
        doc = json.loads(raw)
        check('fresh_documentation_has_no_failures', doc['status'] == 'passed' and doc['failures'] == [])

result = {'schema':'ontokin.c271.p03-final-publication-review/1', 'reviewer':'/root/intake_review',
          'recorded_at_utc':datetime.now(timezone.utc).isoformat(), 'source':{'commit':SHA,'tree':TREE},
          'code_execution_candidate':CODE, 'verdict':'accurate_blocked_partial_source_supported',
          'check_count':len(rows),'failed_count':sum(not r['passed'] for r in rows),'checks':rows,
          'archive':archive_identity, 'archive_payloads':108, 'prior_final_review_payloads':len(prior_manifest['files']),
          'nonblocking_metadata_note':"RAW-EVIDENCE-VERIFICATION.json's excluded field starts with an included-evidence fragment. Archive inventory proves commands/logs/reviews are present. Only reproducible checkouts/Git objects, downloaded Node files and installed environments are excluded; preserve that clear boundary in the outer handoff.",
          'R03_accepted':False,'integration_approved':False,'parent_closure_approved':False,
          'limits':['No product replay or broad re-audit.','Director remote readback receipt reconciled; reviewer made no remote call.',
                    'Final handoff ZIP integrity, saved identity and delivery receipt await separate review.']}
(OUT/'PUBLICATION-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['source','verdict','check_count','failed_count','archive_payloads','prior_final_review_payloads']}))
