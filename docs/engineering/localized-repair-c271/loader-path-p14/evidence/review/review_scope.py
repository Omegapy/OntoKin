"""Independent read-only P14 intake review; does not import repository code."""
import collections
import copy
import datetime
import hashlib
import json
import pathlib
import platform
import sys

ROOT = pathlib.Path('/workspace/scratch/29fbc446c948')
OUT = ROOT / 'p14-session/review'
REPO = ROOT / 'p13-handoff/repository'
C271 = REPO / 'docs/engineering/localized-repair-c271'
P13 = C271 / 'review-boundary-p13'
CAND = P13 / 'design/candidate001'
P11 = C271 / 'loader-path-p11/design/candidate004'
reads = {}
checks = []

def blob(path, coverage='byte_identity_or_structural_inspection'):
    path = pathlib.Path(path)
    raw = path.read_bytes()
    key = str(path)
    entry = reads.setdefault(key, {'path': key, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'coverage': []})
    if coverage not in entry['coverage']:
        entry['coverage'].append(coverage)
    return raw

def data(path):
    return json.loads(blob(path))

def check(name, actual, detail):
    checks.append({'id': name, 'passed': bool(actual), 'detail': detail})

def exact(path, desc):
    raw = blob(path)
    return len(raw) == desc.get('bytes', desc.get('size_bytes')) and hashlib.sha256(raw).hexdigest() == desc['sha256']

for name in ['AGENTS.md', 'GOAL.md', 'ROLE.md', 'docs/workflow/PROTOCOL.md', 'docs/workflow/HANDOFF.md']:
    a = blob(ROOT / 'observed-main' / name, 'full_text_read_by_reviewer')
    b = blob(REPO / name)
    check('instructions_read_equivalence:' + name, a == b or a == b + b'\n', {'full_observed_main_text_read': True, 'exact_byte_equality': a == b, 'observed_is_package_plus_one_trailing_lf': a == b + b'\n', 'meaning': 'Exact identities remain separately recorded; terminal LF difference changes no instruction.'})

for name in ['README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md', 'RECOVERY-STATUS.md']:
    blob(ROOT / 'p13-handoff' / name, 'full_text_read_by_reviewer')
for p in [P13 / 'ADOPTION.json', P13 / 'PHASE-OUTCOME.json', P13 / 'review/REPORT.md', CAND / 'README.md', CAND / 'DECISION.md', CAND / 'CONTROL-CONTRACT.md', P11 / 'DECISION.md', P11 / 'CONTROL-CONTRACT.md', P11 / 'FUTURE-SURFACE.json']:
    blob(p, 'full_text_read_by_reviewer')

adoption = data(P13 / 'ADOPTION.json')
manifest = data(CAND / 'CANDIDATE-MANIFEST.json')
check('adoption_manifest', exact(CAND / 'CANDIDATE-MANIFEST.json', adoption['candidate_manifest']), adoption['candidate_manifest'])
check('adoption_status', adoption['state'] == 'adopted_design_and_control_applicability_only' and adoption['independent_review']['mandatory_findings'] == [], 'Separate adoption accepts exact design and applicability; it is not runtime qualification.')
check('candidate_payload', all(exact(CAND / row['path'], row) for row in manifest['payload']), {'payload_count': len(manifest['payload'])})
check('prior_review_records', all(exact(REPO / adoption['independent_review'][k]['path'], adoption['independent_review'][k]) for k in ['report', 'audit', 'reviewed_files']), 'Prior review report, audit and read set match the separately adopted identities. Their prior checks are not rerun or counted as this review.')
inputs = data(CAND / 'INPUTS.json')
check('input_identities', all(exact(REPO / row['path'], row) for row in inputs['files'].values()), {'source_inputs': len(inputs['files']), 'source_revision_from_p13': inputs['source_revision']})
mapping = data(CAND / 'CONTROL-MAPPING.json')
fixtures = data(P11 / 'FIXTURE-MANIFEST.json')
expectations = data(P11 / 'EXPECTATIONS.json')
oldmanifest = data(P11 / 'CANDIDATE-MANIFEST.json')
rows = mapping['cases']
by_id = {row['id']: row for row in rows}
oldrows = {row['id']: row for row in fixtures['cases']}
check('case_accounting', len(rows) == 97 and len(by_id) == 97 and set(by_id) == set(oldrows) == set(expectations['cases']), 'All 97 original case IDs occur once; no omitted or invented case.')
classifications = dict(collections.Counter(row['classification'] for row in rows))
check('mapping_partition', classifications == {'future_runtime_primitive': 96, 'independent_review_only': 1}, classifications)
case_errors = []
for key, row in by_id.items():
    old = oldrows[key]
    ref = {'json_pointer': '/cases/' + key, 'source': 'E07'}
    if not (row['original_route'] == old['route'] and row['original_input'] == old['input']['path'] and row['original_expected_key'] == old['expected_key'] and row['original_expectation'] == ref):
        case_errors.append(key + ': original binding differs')
    if key == 'N57_source_variant_unknown':
        if not (row['classification'] == 'independent_review_only' and row['runtime_expectation'] is None and row['oracle_status'] == 'historical_runtime_oracle_not_executable_under_p13'):
            case_errors.append(key + ': wrong external-review allocation')
    elif not (row['classification'] == 'future_runtime_primitive' and row['runtime_expectation'] == ref and row['oracle_status'] == 'unchanged_future_runtime_obligation'):
        case_errors.append(key + ': runtime oracle changed')
check('mapping_preserves_oracles', not case_errors, case_errors)
check('fixture_bytes', len(fixtures['files']) == 131 and all(exact(P11 / row['path'], row) for row in fixtures['files']), 'All 131 original fixture byte identities match. Historical modes are not restored by this review.')
missing = []
present_ok = True
for row in oldmanifest['payload']:
    p = P11 / row['path']
    if p.is_file():
        present_ok = exact(p, row) and present_ok
    else:
        missing.append(row)
check('original_payloads', present_ok and len(missing) == 1 and missing[0]['path'] == 'REVISION-004.diff', {'present': len(oldmanifest['payload']) - len(missing), 'external': missing})
check('original_supports', all(exact(P11 / row['path'], row) for row in oldmanifest['supporting_files']), {'supports': len(oldmanifest['supporting_files'])})
p01 = data(P11 / 'fixture_inputs/P01_nonselecting_base.json')
n57 = data(P11 / 'fixture_inputs/N57_source_variant_unknown.json')
p01_copy, n57_copy = copy.deepcopy(p01), copy.deepcopy(n57)
labels = [p01_copy['variant_review'].pop('completeness'), n57_copy['variant_review'].pop('completeness')]
raw = json.dumps(p01_copy, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
check('p01_n57_distinction', labels == ['synthetic_declared_complete', 'unsupported'] and p01_copy == n57_copy and len(raw) == 3338 and hashlib.sha256(raw).hexdigest() == 'e33cb05c8e73031f7c720ecee68094ced82f5d3679af4bc1ebf95bca5b0eaa3c', 'One synthetic completeness label differs; deleting it only for static comparison yields identical 3338-byte values. No new runtime input is created.')
surface = data(P11 / 'FUTURE-SURFACE.json')
check('prospective_path_scope', surface['proposed_production_edit_paths'] == ['prototypes/static_tray_v01/current_host_inspection_v01.py'] and surface['proposed_new_test_paths'] == ['tests/test_current_host_loader_path_v01.py'], {'production': surface['proposed_production_edit_paths'], 'test': surface['proposed_new_test_paths']})

summary = {
    'schema': 'ontokin.c271.p14-independent-scope-review/1',
    'reviewer': '/root/independent_review',
    'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'command': 'python3 -I -B /workspace/scratch/29fbc446c948/p14-session/review/review_scope.py',
    'environment': {'python': sys.version, 'platform': platform.platform()},
    'verdict': 'no_new_contract_blocker_to_bounded_implementation_selection' if all(x['passed'] for x in checks) else 'blocked_by_failed_static_check',
    'passed': sum(x['passed'] for x in checks),
    'failed': sum(not x['passed'] for x in checks),
    'checks': checks,
    'director_supplied_live_state': {'main': 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d', 'branch': '4023a878ccc9980726e3b56102b41faa51be0eb1', 'pr_274': 'draft_open_unmerged', 'issue_273': 'open', 'p13_delivery': 'Director reports exact terminal confirmation read via GitHub; this reviewer did not independently inspect the remote in this pass'},
    'before_substantial_work': ['Director declares one bounded phase, acceptance checkpoint and stop.', 'New early recovery must be independently verified, saved and exact-readback confirmed.', 'Implementation author consumes immutable controls with recorded historical modes restored in private evidence tree; all external inputs must remain explicit.'],
    'implementation_review_requirements': ['Only the adopted production file and distinct new test file may implement P11/P13 scope.', 'Keep old schema/profile, public parser signature/default refusals, consumers, pins and source budgets unchanged.', 'Faithfully exercise 96 original runtime oracles at actual production boundaries; do not dispatch on case ID, label or expected result.', 'Preserve all 97 original case/oracle records and 131 fixture bytes.', 'Keep N57 historical oracle unsatisfied and external review unestablished; never count it as a runtime pass.', 'Require actual 175 inherited-method execution and separate exact implementation/adapter review before phase acceptance.', 'Read variants through existing _document with 16 MiB cap, canonical/duplicate-key/identity/callback checks.', 'Complete new-profile proof before _load_helpers and effects; repeat full proof on _recheck and small kernel witness at _launch_check.'],
    'remaining_external_gates': ['Actual loader/source/build/platform completeness review bound to operational plan and inventory', 'H0/H1', 'Original-seven/full routine/R03', 'Integration/R04', 'Parent saved closure/R05'],
    'limits': ['Static intake review only; no implementation candidate exists in this review.', 'No repository/product/host code executed or imported.', 'Prior audit records were identity checked; no prior test count is claimed as newly run.', 'No Git/index, canonical record, remote or Library mutations. Only owned review files written.', 'No original fixture-mode restoration claim.', 'No child worker, active process or unknown write remains from this review.'],
    'observed_read_limit': 'The initial combined governing-document display was truncated; ROLE, PROTOCOL and HANDOFF were re-read in full bounded calls. A broad optional task-record search was also truncated and is not claimed as full task read coverage.',
    'prior_review_attempt': {'path': str(OUT / 'scope-attempt001'), 'disposition': 'Retained unchanged. Five instruction equality checks failed because every observed-main local file has exactly one extra trailing LF relative to the package. The first human report was generated with unconditional acceptance wording, an authoring error in this review script; the first machine audit correctly reported blocked. This corrected review records separate byte identities and only recognizes the verified terminal-LF equivalence. No product or original oracle was changed.'}
}
OUT.mkdir(parents=True, exist_ok=True)
for name, value in [('SCOPE-AUDIT.json', summary), ('READ-SET.json', {'schema': 'ontokin.c271.p14-review-read-set/1', 'reviewer': '/root/independent_review', 'files': list(reads.values())})]:
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
report = '''# Independent P14 scope review

Verdict: no new contract blocker to selecting one bounded implementation phase. This is a prospective scope review, not implementation acceptance.

The exact separately adopted P13 manifest and prior independent review match. All 97 original case identities and oracles are retained; 96 remain runtime obligations and N57 is one external-review obligation. All 131 fixture byte identities, 145 available P11 payloads, and 29 supports match. REVISION-004.diff remains an explicit external dependency.

The eligible implementation surface is current_host_inspection_v01.py plus the distinct test_current_host_loader_path_v01.py adapter. The Director must first declare the phase and confirm the new early recovery save/readback. Private materialization must respect the recorded original inert modes. The new implementation must preserve legacy behavior, existing schemas/pins/budgets, the 16 MiB document reader, callback identities, early-proof ordering, full rechecks, and real-pin/synthetic separation. Exact adapter review and all 175 inherited methods remain mandatory.

N57 cannot be made a runtime pass or a fabricated refusal through its label, an approval field, altered descriptors, or injected failure. The actual-loader completeness review, H0/H1, original-seven/full routine, integration and parent completion remain open. P13 delivery and current remote identities were supplied by the Director, not independently re-observed in this intake pass.

SCOPE-AUDIT.json records checks and limits; READ-SET.json records exact inputs. Every observed-main instruction file has exactly one extra trailing LF versus its packaged counterpart; the separate identities are retained. The initial overstrict equality check and unconditional human-report wording are preserved in scope-attempt001. No product or host code ran. Only this assigned review directory changed.
'''
if summary['failed']:
    report = '# Independent P14 scope review: blocked\n\nOne or more static intake checks failed. See SCOPE-AUDIT.json. No acceptance is granted.\n'
with (OUT / 'SCOPE-REPORT.md').open('x') as stream:
    stream.write(report)
print(json.dumps({'verdict': summary['verdict'], 'passed': summary['passed'], 'failed': summary['failed'], 'read_files': len(reads), 'artifacts': [str(OUT / p) for p in ['SCOPE-AUDIT.json', 'READ-SET.json', 'SCOPE-REPORT.md']]}))
sys.exit(0 if summary['failed'] == 0 else 1)
