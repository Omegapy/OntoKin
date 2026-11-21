#!/usr/bin/env python3
"""Bounded saved-receipt/closure review: no archive extraction or acceptance rerun."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

ROOT = Path('/workspace/scratch/c219bb61a617')
REPO = ROOT / 'OntoKin'
OUT = ROOT / 'delivery-receipt-review'
PREFIX = 'docs/engineering/localized-repair-c271/finalization-20261120'
SOURCE = '70a658c31085bf8dd78d79663c57f8e3cdb28ceb'
TREE = '77ee621cdfb00acf637828ce71f3384b4dd8275c'
MAIN = 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
cache = {}
checks = []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    path = Path(path)
    if path not in cache:
        cache[path] = path.read_bytes()
    return cache[path]

def j(path):
    return json.loads(read(path))

def baseline(path):
    data = subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=REPO)
    return data

def check(name, condition, detail):
    checks.append({'id': f'R{len(checks)+1:02}', 'check': name, 'passed': bool(condition), 'detail': detail})

def artifact_key(item, version_key='version'):
    return tuple(item[k] for k in ('file_name', 'library_file_id', 'file_id', 'path', 'bytes', 'sha256', 'url')) + (int(item[version_key]),)

def identity(path):
    data = read(path)
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}

receipt_path = REPO / PREFIX / 'P02-DELIVERY.json'
receipt = j(receipt_path)
saved = j(ROOT / 'session/FINAL-SAVED-FILES.json')
readback = j(ROOT / 'session/FINAL-LIBRARY-READBACK.json')
raw_upload = j(ROOT / 'session/FINAL-UPLOAD-RESULT.json')['results']
operation = j(ROOT / 'session/FINAL-UPLOAD-OPERATION.json')
builder_path = ROOT / 'packages/OntoKin_C271_P02_Validation_Blocked_Handoff_2026-11-20_VERIFICATION.json'
builder = j(builder_path)
task = j(REPO / 'docs/workflow/tasks/C271/task.json')
current = j(REPO / 'docs/workflow/CURRENT.json')
phase = j(REPO / PREFIX / 'PHASE-OUTCOME.json')
session_path = REPO / 'docs/workflow/tasks/C271/P02-SESSION.md'
session = read(session_path).decode()
old_task = json.loads(baseline('docs/workflow/tasks/C271/task.json'))
old_current = json.loads(baseline('docs/workflow/CURRENT.json'))
old_phase = json.loads(baseline(PREFIX + '/PHASE-OUTCOME.json'))
old_session = baseline('docs/workflow/tasks/C271/P02-SESSION.md').decode()
source_audit_path = REPO / PREFIX / 'final-source-review/AUDIT.json'
package_audit_path = REPO / PREFIX / 'package-review/AUDIT.json'
source_audit = j(source_audit_path)
package_audit = j(package_audit_path)
clean_path = REPO / PREFIX / 'final-source-record-checks/CHECKS.json'
clean = j(clean_path)
delivered = [receipt['archive']] + receipt['prompts']
frozen = [builder['archive']] + builder['standalone_prompts']
expected = [
    ('OntoKin_C271_P02_Validation_Blocked_Handoff_2026-11-20.zip', 19975795, 'f9cd741651c271a31cbe6fa691b07080dcc531f6fc35ea62adf6186cb0091b7a'),
    ('OntoKin_C271_P02_Blocked_Prompt_1_Continue_2026-11-20.md', 4830, 'e468d8edc5d9a97a7a44d5d961159339e9959689fc375c2d84a554c6e8827eca'),
    ('OntoKin_C271_P02_Blocked_Prompt_2_Recover_2026-11-20.md', 5106, '20df654347e76b99c63ada054109e3941beb9f9b036db98b99ccde3c0fb5030f'),
]
actual = []
for name, size, digest in expected:
    path = ROOT / 'packages' / name
    data = read(path)
    actual.append((name, len(data), sha(data)))
check('Frozen ZIP and both prompt bytes remain exact', actual == expected,
      'Only whole-file size/SHA-256 checked; no archive extraction, payload replay or content audit.')
check('Ordered original upload succeeded for exactly three intended files',
      len(raw_upload) == len(saved) == len(delivered) == 3
      and all(u['status'] == s['status'] == 'succeeded' and all(u[k] == s[k] for k in u)
              for u, s in zip(raw_upload, saved)),
      'Original helper response matches enriched saved-file receipt in ZIP/continue/recovery order.')
check('Saved receipt names, local paths, sizes and hashes match frozen files',
      all((s['file_name'], s['bytes'], s['sha256']) == e
          and s['local_path'] == str(ROOT / 'packages' / e[0]) for s, e in zip(saved, expected)),
      'All three saved identities refer to the previously frozen local bytes.')
check('Canonical delivery records match ordered saved IDs and versions',
      all(artifact_key(d) == artifact_key(s, 'current_version_number') for d, s in zip(delivered, saved)),
      'File IDs, Library IDs, names, destination paths, bytes, SHA-256, URLs and version 0 match.')
check('Destination readback matches all three exact saved files',
      readback['status'] == 'passed' and readback['folder'] == '/OntoKin'
      and len(readback['files']) == 3
      and all((r['name'], r['file_id'], r['library_file_id'], r['path'], r['size_bytes'], int(r['version_id']))
              == (s['file_name'], s['file_id'], s['library_file_id'], s['path'], s['bytes'], s['current_version_number'])
              for r, s in zip(readback['files'], saved)),
      'Readback observes IDs/names/paths/size/version. It does not itself supply a server-side content hash.')
check('Save timing is tied to the positively completed upload operation',
      operation['state'] == 'completed' and operation['exit_code'] == 0 and operation['ordered_file_count'] == 3
      and receipt['saved_at_utc'] == operation['completed_at_utc']
      and all(dt.datetime.fromisoformat(r['created_at']) <= dt.datetime.fromisoformat(receipt['saved_at_utc'])
              for r in readback['files'])
      and dt.datetime.fromisoformat(receipt['saved_at_utc']) <= dt.datetime.fromisoformat(readback['verified_at_utc'].replace('Z', '+00:00')),
      'Files were created around 23:33:29 UTC; saved_at records the completed batch at 23:33:30.438929 UTC.')
check('Saved destinations, stable links and local metadata are consistent',
      all(d['path'] == '/OntoKin/' + d['file_name'] and d['version'] == 0 and d['local_metadata_applied']
          and d['url'] == 'https://chatgpt.com/library?file_id=' + d['library_file_id'] + '&account_id=personal'
          for d in delivered),
      'All files are in the existing OntoKin destination; links use the exact saved Library IDs.')
check('Packaged and executed source identities remain separate',
      receipt['source_revision'] == builder['source_revision'] == SOURCE
      and receipt['source_tree'] == builder['source_tree'] == TREE
      and receipt['executed_source_revision'] == '88bc8b51b3963b7072375edac6400b6e6a4532e4'
      and receipt['executed_source_tree'] == '755f366d1091beb71b5421b14fdac0b9b868cfb0',
      'Receipt-only metadata does not claim a new behavioral execution at the later source freeze.')
v = receipt['source_and_archive_verification']
check('Builder counts accurately describe the retained completed report',
      builder['passed'] and builder['checks_failed'] == 0
      and (v['builder']['checks'], v['builder']['members'], v['builder']['payloads'], v['builder']['git_snapshots'])
          == (builder['checks_passed'], builder['members'], builder['payloads'], builder['git_snapshots'])
          == (719, 219, 218, 157),
      '719 archive/source-mapping predicates are inspection evidence, not routine-driver acceptance.')
check('Independent source audit is accurately limited to partial delivery',
      source_audit['check_count'] == v['independent_source']['checks'] == 1522
      and source_audit['failed_count'] == v['independent_source']['failed_checks'] == 0
      and v['independent_source']['result'] == 'passed_for_blocked_partial_handoff'
      and source_audit['source_readiness'] == 'verified_blocked_partial_source'
      and not source_audit['integration_approved'] and not source_audit['parent_closure_approved'],
      'No source-audit predicates were rerun.')
check('Independent package audit is accurately limited to save eligibility',
      package_audit['check_count'] == v['independent_package']['checks'] == 1031
      and package_audit['failed_count'] == v['independent_package']['failed_checks'] == 0
      and package_audit['verdict'] == v['independent_package']['result'] == 'eligible_for_save'
      and not package_audit['integration_approved'] and not package_audit['parent_closure_approved'],
      'No archive audit was rerun; existing summary and report identity were inspected.')
check('Clean-source record-check receipt has the declared source and result',
      clean['status'] == v['clean_published_source_records']['result'] == 'passed'
      and clean['source_before']['commit'] == clean['source_after']['commit'] == SOURCE
      and clean['source_unchanged'] and clean['behavioral_reruns'] is False,
      'The existing completed clean-check receipt is reused; no checks were rerun.')
report_records = [v[k]['report'] for k in ('builder', 'independent_source', 'independent_package', 'clean_published_source_records')] + [v['saved_readback']]
report_matches = all((lambda x: x['bytes'] == r['bytes'] and x['sha256'] == r['sha256'])(identity(REPO / r['path'])) for r in report_records)
report_matches = report_matches and read(REPO / v['builder']['report']['path']) == read(builder_path)
report_matches = report_matches and read(source_audit_path) == read(ROOT / 'final-source-review/AUDIT.json')
report_matches = report_matches and read(package_audit_path) == read(ROOT / 'final-package-review/AUDIT.json')
report_matches = report_matches and read(clean_path) == read(ROOT / 'session/final-source-record-checks/CHECKS.json')
report_matches = report_matches and read(REPO / v['saved_readback']['path']) == read(ROOT / 'session/FINAL-LIBRARY-READBACK.json')
check('All referenced verification report hashes bind exact retained originals', report_matches,
      'Builder/source/package/record-check/readback report byte counts and SHA-256 values match their canonical copies and original files.')
check('Parent task and CURRENT remain blocked and active',
      task['status'] == receipt['parent']['status'] == phase['task_status'] == 'blocked'
      and current['active_task'] == current['latest_task'] == 'C271'
      and current['next_action']['status'] == 'blocked' and receipt['parent']['closure_approved'] is False,
      'No parent completion or task retirement is introduced.')
requirements = {r['id']: r['status'] for r in task['requirements']}
check('All requirement states and acceptance definitions are preserved',
      requirements == receipt['parent']['requirements'] == {'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'}
      and all((a['id'], a['description'], a['acceptance'], a['status']) == (b['id'], b['description'], b['acceptance'], b['status'])
              for a,b in zip(task['requirements'], old_task['requirements'])),
      'Only R05 evidence gains the confirmed partial-delivery receipt.')
check('Plan completion remains P01 done and P02 in progress',
      {p['id']:p['status'] for p in task['plan']} == receipt['parent']['plan'] == {'P01':'done','P02':'in_progress'}
      and task['plan'] == old_task['plan'],
      'Partial session delivery does not complete the P02 parent plan.')
by_name = {c['name']:c for c in task['checks']}
required_failed = [by_name[n] for n in ('required routine local driver before integration','independent P02 integration acceptance review')]
check('Both mandatory failed integration gates remain required and failed',
      all(c['required'] is True and c['result'] == 'failed' for c in required_failed)
      and all(by_name[c['name']]['required'] == c['required'] and by_name[c['name']]['result'] == c['result']
              for c in old_task['checks']),
      'No earlier required check was waived or relabeled; a separate partial-delivery check may pass.')
check('Affected success and routine failures remain distinct and exact',
      receipt['validation']['affected'] == {'result':'passed','checks':12,'methods':282,'failures':0,'errors':0,'skips':0}
      and receipt['validation']['required_routine']['result'] == 'failed'
      and receipt['validation']['required_routine']['exit_code'] == 1
      and receipt['validation']['required_routine']['completed_unit_suite_total'] is None
      and receipt['validation']['required_routine']['unit_timeout_seconds'] == 900
      and receipt['validation']['required_routine']['documentation_failures'] == 21
      and receipt['validation']['required_routine']['omitted_instruction_files'] == 5
      and phase['routine'] == old_phase['routine'] and phase['affected'] == old_phase['affected'],
      'No partial-progress count is substituted for a completed unit suite.')
check('Only the delivered phase session is marked complete',
      task['session_phase']['status'] == receipt['phase_session_status'] == 'complete_partial_delivery'
      and task['session_phase']['delivery_confirmed'] is True
      and task['session_phase']['parent_status'] == 'blocked'
      and task['session_phase']['independent_integration_approved'] is False,
      'Phase completion is explicitly partial; parent status and integration eligibility remain unchanged.')
check('PHASE-OUTCOME changes only partial delivery status and receipt',
      phase['status'] == 'blocked_partial_delivery_saved'
      and phase['delivery']['status'] == 'saved' and phase['delivery']['partial'] is True
      and {k for k in set(phase)|set(old_phase) if phase.get(k) != old_phase.get(k)} == {'status','delivery'},
      'All failed outcomes, mandatory findings and acceptance statements are unchanged.')
check('Task and CURRENT point to exactly the confirmed partial archive',
      task['delivery']['status'] == 'saved' and task['delivery']['partial'] is True
      and task['delivery']['archive'] == receipt['archive'] and task['delivery']['prompts'] == receipt['prompts']
      and artifact_key(current['latest_handoff']) == artifact_key(receipt['archive'])
      and current['latest_handoff']['partial'] is True
      and current['latest_handoff']['source_revision'] == SOURCE and current['latest_handoff']['source_tree'] == TREE,
      'All exposed current artifact identities agree with the actual save receipts.')
pub = receipt['publication']; frozen_state = receipt['repository_state_at_source_freeze']
check('No main lease, integration, merge or branch closure is claimed',
      pub['expected_parent'] == SOURCE and not pub['main_write'] and not pub['main_lease_held']
      and not pub['integration_performed'] and pub['branch_disposition'] == 'retained_unmerged'
      and pub['pull_request_274'] == 'open_draft' and pub['scope_issue_273'] == 'open'
      and frozen_state['main']['sha'] == current['observed_main'] == MAIN
      and task['completion']['merge_commit'] is None and phase['main_lease'] == 'not_held'
      and phase['integration_performed'] is False and phase['integration_eligible'] is False,
      'The planned publication is limited to the retained branch; actual future publication/readback remains external.')
check('Session narrative appends accurate partial-delivery closure',
      session.startswith(old_session)
      and '## Confirmed partial delivery' in session[len(old_session):]
      and all(text in session[len(old_session):] for text in ('719 builder checks','1,031 independent package checks','1,522-check source audit','C271 remains blocked','P02 remains in_progress','required routine acceptance still failed')),
      'Historical session prose is retained; a new dated addendum states the confirmed saved boundary.')
check('First unmet action remains the exact authorized fresh-chat recovery',
      receipt['next_action'] == task['next_action'] == phase['next_action'] == current['next_action']['suggested_task'] == old_phase['next_action']
      and 'Do not begin a repair or another phase' in receipt['stop'],
      'Saving the phase does not begin a repair, retry or another H group.')
check('Historical uncertainty remains explicit and unreclassified',
      phase['historical_unknowns'] == old_phase['historical_unknowns']
      and 'remain unknown' in receipt['historical_unknowns']
      and 'does not resolve' in receipt['historical_unknowns'],
      'Current positive process closure does not settle the prior C270 interrupted run or historical global process state.')
check('Metadata delta is confined to receipt evidence and pointers',
      {k for k in set(task)|set(old_task) if task.get(k) != old_task.get(k)} == {'checks','completion','requirements','delivery','session_phase'}
      and {k for k in set(current)|set(old_current) if current.get(k) != old_current.get(k)}
          <= {'older_handoffs','snapshot_date','latest_handoff','previous_handoff','next_action'},
      'This bounded review compares only the named task/CURRENT/PHASE/session metadata, not a broad source audit.')
check('External receipt preserves the frozen-archive boundary',
      receipt['status'] == 'saved' and receipt['partial'] is True
      and v['archive_rebuilt_after_freeze'] is False and v['prompts_equal_archive'] is True
      and all(p['matches_archive'] for p in builder['standalone_prompts'])
      and 'outside the frozen ZIP' in receipt['receipt_boundary']
      and 'does not change its payload' in receipt['receipt_boundary'],
      'Frozen whole-file hashes remain exact; prompt-to-archive identity reuses the fulfilled builder verification.')
check('Reviewed files stayed unchanged during this bounded review',
      all(path.read_bytes() == data for path, data in cache.items()),
      'Recorded file hashes bind the exact bytes inspected; no canonical file was written by this reviewer.')

assert len(checks) == 28
failed = [c for c in checks if not c['passed']]
files = [identity(path) for path in sorted(cache, key=str)]
baseline_ids = []
for path in ('docs/workflow/tasks/C271/task.json','docs/workflow/CURRENT.json',PREFIX+'/PHASE-OUTCOME.json','docs/workflow/tasks/C271/P02-SESSION.md'):
    data = baseline(path)
    baseline_ids.append({'revision': SOURCE, 'path': path, 'bytes': len(data), 'sha256': sha(data)})
audit = {'schema':'ontokin.c271.p02-delivery-receipt-review/1','reviewer':'/root/package_builder',
         'reviewed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
         'scope':'Saved artifact identity and receipt-only closure metadata, at most 30 predicates.',
         'verdict':'ready_for_receipt_publication' if not failed else 'changes_required',
         'checks_passed':len(checks)-len(failed),'checks_failed':len(failed),'checks':checks,
         'reviewed_base_commit':SOURCE,'reviewed_source_tree':TREE,
         'integration_approved':False,'parent_closure_approved':False,
         'archive_reexecution':False,'behavioral_reexecution':False,
         'remote_publication_performed':False,'repository_modified':False,
         'findings':failed,'reviewed_files':files,'baseline_metadata':baseline_ids,
         'limit':'Review relies on provided actual upload/destination-readback records and fulfilled audit summaries. It does not independently redownload saved files or approve any future Git publication.'}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
(OUT/'REVIEWED-FILES.json').write_text(json.dumps({'files':files,'baseline_metadata':baseline_ids},indent=2)+'\n')
(OUT/'TOOL-ATTEMPT.json').write_text(json.dumps({'attempt':'initial_read_only_receipt_reads','result':'Tool runtime replaced before output was returned; no mutation was requested. Reads were repeated successfully.','effects':'No write, archive run or acceptance check was attempted.'},indent=2)+'\n')
report = f'''# C271 P02 saved-receipt and partial-closure review

**Verdict: {'ready for receipt-only publication' if not failed else 'changes required'}.** {len(checks)-len(failed)} of {len(checks)} bounded predicates passed; {len(failed)} failed. Reviewer: `/root/package_builder`. This is an independent receipt/state review, not an integration approval or repeat of the archive/source audits.

The confirmed ZIP and both prompts match the original ordered upload, exact Library/file IDs, names, destination paths, version 0, byte counts and frozen SHA-256 identities. Destination readback confirms those identities and sizes. The upload completed successfully at the receipt's recorded `saved_at_utc`; file creation occurred about one second earlier. No archive extraction, nested inspection, product check, save retry or remote write was performed.

The receipt correctly describes 719 builder checks, 1,031 independent package predicates and 1,522 independent source predicates. Exact copied report hashes match their retained originals. These inspection results remain separate from failed required routine/integration acceptance.

C271 remains blocked/open. R01/R02 are done; R03–R05 are not_done; P01 is done and P02 remains in_progress. Only the phase session is `complete_partial_delivery`. The required routine and P02 integration checks remain required/failed. No main lease, integration, merge, branch deletion or parent closure is asserted. The exact fresh-chat recovery action and historical uncertainties are preserved.

The source freeze remains `{SOURCE}` / `{TREE}`. The later saved receipt is external to the unchanged archive. The named metadata delta is limited to saved-delivery evidence and pointers. Root must still publish/read back the receipt checkpoint and complete required metadata checks; this review does not claim those future actions.

`AUDIT.json` records all 28 predicates. `REVIEWED-FILES.json` binds every reviewed artifact/record to its exact byte count and SHA-256, plus the four baseline metadata snapshots. No mandatory finding was found.
'''
if failed:
    report += '\nFindings:\n' + '\n'.join('- '+c['id']+': '+c['check'] for c in failed) + '\n'
(OUT/'REPORT.md').write_text(report)
print(json.dumps({'verdict':audit['verdict'],'checks_passed':audit['checks_passed'],'checks_failed':audit['checks_failed'],'reviewed_files':len(files),'findings':failed,'report':str(OUT/'REPORT.md'),'audit':str(OUT/'AUDIT.json')},indent=2))
raise SystemExit(bool(failed))
