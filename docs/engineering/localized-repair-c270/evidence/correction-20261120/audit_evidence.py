#!/usr/bin/env python3
"""Verify retained C270 candidate execution evidence without rerunning suites."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import sys

REPO = Path('/workspace/scratch/92228987b591/validation/candidate')
EVIDENCE = Path('/workspace/scratch/92228987b591/evidence/candidate')
OUT = Path('/workspace/scratch/92228987b591/reviews/CANDIDATE-EVIDENCE-AUDIT.json')
HEAD = 'a6099546e2ae66e78621008338ecd3b2d352d9b8'
TREE = '6e05696718723fe77f6973d1aa2319638723d127'
checks = []

def check(label, condition, **detail):
 checks.append({'label': label, 'passed': bool(condition), **detail})

def identity(path):
 raw = path.read_bytes()
 return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def verify_row(label, row, base):
 path = Path(row['path'])
 if not path.is_absolute(): path = base / path
 actual = identity(path)
 expected = {'bytes': row['bytes'], 'sha256': row['sha256']}
 check(label, actual == expected, path=str(path), actual=actual, expected=expected)

def read(relative):
 return json.loads((EVIDENCE / relative).read_text())

started = datetime.now(timezone.utc).isoformat()
h = read('h16/RESULTS.json')
check('h16_exact_candidate', h['source_revision'] == HEAD and h['source_tree'] == TREE)
check('h16_all_assertions_pass', h['passed'] and not h['failed_assertions'] and all(c['passed'] and all(c['assertions'].values()) for c in h['cases']))
check('h16_five_cases_45_assertions', len(h['cases']) == 5 and sum(len(c['assertions']) for c in h['cases']) == 45)
check('h16_inputs_stable_clean', h['inputs'] == h['inputs_after'] and h['inputs_unchanged'] and h['source_revision_unchanged'] and h['tracked_clean_after'] and not h['tracked_dirty_status'])
for i, row in enumerate(h['inputs']): verify_row('h16_input_' + str(i), row, REPO)
verify_row('frozen_expectation', h['frozen_expectation'], REPO)
for c in h['cases']:
 if 'response' in c:
  verify_row('h16_response_' + c['label'], c['response'], REPO)
  response_path = Path(c['response']['path'])
  if not response_path.is_absolute(): response_path = REPO / response_path
  value = json.loads(response_path.read_text())
  check('h16_original_hinge_count_' + c['label'], value.get('hingeCount') == 8)
  if c['label'] == 'original-source': check('h16_original_site_count', value.get('siteCount') == 16)
 else:
  chain = c['cause_chain']
  expected_depth = {'siteref-source': 1, 'siteref-binding': 2, 'siteref-comparison': 3}[c['label']]
  check('h16_source_cause_' + c['label'], len(chain) == expected_depth and all(x.get('code') == 'UNSUPPORTED_SOURCE_FORM' and x.get('detail') == 'declared SiteRef parameter endpoint is unsupported' for x in chain))
  forbidden = {'records', 'hinges', 'sites', 'objects', 'hingeCount', 'siteCount', 'objectCount', 'qualified', 'inputBindingVerified', 'hingeComparisonVerified', 'hingeSetAgreementVerified', 'endpointAgreementVerified'}
  check('h16_no_qualified_fields_' + c['label'], all(not forbidden.intersection(x) for x in chain))

a = read('affected-cohort/CHECKS.json')
check('cohort_exact_candidate', all(a[k]['commit'] == HEAD and a[k]['tree'] == TREE and not a[k]['tracked_dirty_status'] for k in ('source_before', 'source_after')))
check('cohort_complete_12_groups_282_methods', a['complete'] and a['passed'] and a['planned_check_count'] == a['completed_check_count'] == len(a['checks']) == 12 and a['total_methods'] == a['expected_total_methods'] == 282 and not a['remaining_checks'])
check('cohort_inputs_stable', a['input_files_before'] == a['input_files_after'] and a['input_identity_unchanged'])
for i, row in enumerate(a['input_files_before']): verify_row('cohort_input_' + str(i), row, REPO)
for i, row in enumerate(a['output_files']): verify_row('cohort_output_' + str(i), row, EVIDENCE / 'affected-cohort')
verify_row('cohort_runner', a['runner'], REPO)
for c in a['checks']:
 check('cohort_group_' + c['name'], c['result'] == 'passed' and c['exit_code'] == 0 and c['failure'] is None and all(c['assertions'].values()))
 verify_row('cohort_log_' + c['name'], c['log'], EVIDENCE / 'affected-cohort')
 if c['expected_methods'] is not None:
  text = (EVIDENCE / 'affected-cohort' / c['log']['path']).read_text()
  counts = re.findall(r'^Ran (\d+) tests? in ', text, flags=re.MULTILINE)
  check('cohort_log_methods_' + c['name'], counts == [str(c['expected_methods'])] and re.search(r'^OK\s*$', text, re.MULTILINE) is not None and re.search(r'^FAILED\b|^ERROR:|^FAIL:', text, re.MULTILINE) is None)
 if c['name'] == 'c253-corpus': check('corpus_14_bindings', c['details']['boundFiles'] == 14 and c['details']['passed'])
 if 'results_identity' in c['details']:
  row = c['details']['results_identity']
  verify_row('retained_controls_' + c['name'], row, EVIDENCE / 'affected-cohort')
  detail = json.loads((EVIDENCE / 'affected-cohort' / row['path']).read_text())
  check('retained_control_outcomes_' + c['name'], detail['passed'] and detail['testMethods'] == c['expected_methods'] and not any(detail[k] for k in ('failures', 'errors', 'skipped')) and len(detail['cases']) == detail['apiCalls'])

d = read('distinctions/CHECKS.json')
check('distinctions_exact_candidate', d['source_revision'] == d['source_revision_after'] == HEAD and d['source_tree'] == TREE and not d['tracked_dirty_before'] and not d['tracked_dirty_after'])
check('distinctions_inputs_stable', d['inputs_before'] == d['inputs_after'])
check('distinctions_eight_methods', d['passed'] and d['exit_code'] == 0 and d['methods'] == 8)
for i, row in enumerate(d['inputs_before']): verify_row('distinction_input_' + str(i), row, REPO)
verify_row('distinctions_runner', d['runner'], REPO)
verify_row('distinctions_log', d['log'], EVIDENCE / 'distinctions')
log = Path(d['log']['path']).read_text()
check('distinctions_log_eight_named_methods_ok', len(re.findall(r'^test_.* \.\.\. ok$', log, re.MULTILINE)) == 8 and 'Ran 8 tests in ' in log and re.search(r'^OK\s*$', log, re.MULTILINE) is not None)

p = read('PRESERVATION.json')
check('preservation_report', p['candidate'] == HEAD and p['original_files_preserved'] == 204 and not p['changed_original_files'] and p['frozen_control_reconstruction'] == 'passed' and p['frozen_oracle_sha256'] == h['frozen_expectation']['sha256'])
check('shared_interpreter_identity', h['environment']['executable'] == d['environment']['executable'] and h['environment']['executable']['sha256'] == a['environment']['resolved_executable']['sha256'])
report = {
 'schema': 'ontokin.c270.independent-evidence-audit/1', 'reviewer': '/root/github_reconcile',
 'candidate': HEAD, 'candidate_tree': TREE, 'started_at_utc': started,
 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
 'environment': {'python': sys.version, 'platform': platform.platform()},
 'command': [sys.executable, *sys.argv], 'audit_script': identity(Path(__file__)),
 'checks': checks, 'check_count': len(checks), 'failed': [c for c in checks if not c['passed']],
 'passed': all(c['passed'] for c in checks),
 'inspected_reports': [{'path': x, **identity(EVIDENCE / x)} for x in ['h16/RESULTS.json', 'affected-cohort/CHECKS.json', 'distinctions/CHECKS.json', 'PRESERVATION.json']],
 'outcomes': {'frozen_cases': 5, 'frozen_assertions': 45, 'cohort_groups': 12, 'cohort_methods': 282, 'original_corpus_bindings': 14, 'supplementary_methods': 8, 'supplementary_variants': 16, 'supplementary_api_calls': 48},
 'limits': ['Evidence inspection and identity audit; no duplicate broad suite execution.', 'Routine local driver outcome remains a separately pending integration eligibility check.', 'No full H16/H20/H22/H24/C260/product/native/model qualification.']}
OUT.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'checks': len(checks), 'passed': report['passed'], 'failed': report['failed']}))
raise SystemExit(0 if report['passed'] else 1)
