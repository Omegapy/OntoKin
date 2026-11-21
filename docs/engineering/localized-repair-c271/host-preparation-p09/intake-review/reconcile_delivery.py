"""Reconcile verified P08 evidence with Director-provided live GitHub readbacks.

Only standard-library parsing and byte comparisons; no Git or product execution.
The initial verifier and its failed inventory-scope assumption stay unchanged.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re

B = Path('/workspace/scratch/e33f906d0e8e')
O = B / 'audits/p08_delivery'
F = O / 'fresh_extract'
P = O / 'postfreeze_decoded'
REPO = B / 'OntoKin'
prior = json.loads((O / 'VERIFICATION.json').read_text())
receipt = json.loads((B / 'incoming/OntoKin/OntoKin_C271_P08_Delivery_Receipt_2026-11-21.json').read_text())
current = json.loads((REPO / 'docs/workflow/CURRENT.json').read_text())
task = json.loads((REPO / 'docs/workflow/tasks/C271/task.json').read_text())
branches = json.loads((B / 'session/BRANCHES.json').read_text())
pr = next(p for p in json.loads((B / 'session/PRS.json').read_text()) if p['number'] == 274)
issue = json.loads((B / 'session/ISSUE273.json').read_text())
checks = []


def ident(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def check(name, passed, detail=None):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})


sm = json.loads((F / 'SOURCE-MANIFEST.json').read_text())['files']
manifest_paths = {r['payload_path'] for r in sm}
actual_source_paths = {
    p.relative_to(F).as_posix()
    for prefix in ['repository', 'observed-main']
    for p in (F / prefix).rglob('*') if p.is_file()
}
check('corrected source inventory covers repository and observed-main',
      manifest_paths == actual_source_paths and len(sm) == len(manifest_paths),
      {'source_snapshots': len(sm), 'repository_snapshots': sum(p.startswith('repository/') for p in manifest_paths),
       'observed_main_snapshots': sorted(p for p in manifest_paths if p.startswith('observed-main/')),
       'missing': sorted(manifest_paths - actual_source_paths),
       'extra': sorted(actual_source_paths - manifest_paths)})

initial_failure = {
    'artifact': ident(O / 'VERIFICATION.json'),
    'verifier': ident(O / 'verify_delivery.py'),
    'failed_check': 'source manifest exact repository inventory',
    'cause': 'Reviewer assumed all source-manifest entries were under repository/. The manifest also binds two intended observed-main snapshots.',
    'disposition': 'Invalid audit assumption corrected by explicit repository/ plus observed-main/ inventory comparison. Original script/report preserved unchanged. No package defect, source change, or product retest.',
    'other_initial_checks_passed': 18,
}
check('initial audit has only the explained inventory-scope failure',
      [c['name'] for c in prior['checks'] if not c['passed']] == [initial_failure['failed_check']])

canonical_rel = receipt['canonical_delivery_receipt']['repository_path']
canonical = REPO / canonical_rel
embedded = P / 'OntoKin' / canonical_rel
check('authentic checkout canonical receipt equals independently decoded receipt bytes',
      canonical.read_bytes() == embedded.read_bytes(), ident(canonical))
check('authentic checkout CURRENT equals exact corrected receipt bytes',
      (REPO / 'docs/workflow/CURRENT.json').read_bytes()
      == (P / 'OntoKin/docs/workflow/CURRENT.json').read_bytes(), ident(REPO / 'docs/workflow/CURRENT.json'))
connector_current = B / 'live-branch/docs/workflow/CURRENT.json'
authentic_current = REPO / 'docs/workflow/CURRENT.json'
check('connector CURRENT semantically matches authentic bytes',
      json.loads(connector_current.read_text()) == current,
      {'connector_identity': ident(connector_current), 'authentic_identity': ident(authentic_current),
       'difference': 'Connector-materialized file has one extra trailing newline.',
       'exact_extra_newline': connector_current.read_bytes() == authentic_current.read_bytes() + b'\n',
       'byte_authority_used': 'authentic checkout and decoded exact receipt evidence'})

before = (P / 'review_work/receipt-metadata-correction/CURRENT-BEFORE-be159.json').read_bytes()
after = (P / 'review_work/receipt-metadata-correction/CURRENT-AFTER-exact.json').read_bytes()
before_json, after_json = json.loads(before), json.loads(after)
changed = [k for k in set(before_json) | set(after_json) if before_json.get(k) != after_json.get(k)]
replacement = before.replace(b'"snapshot_date": "2026-11-21"',
                             b'"snapshot_date": "2026-11-21T17:16:40.093675+00:00"')
check('late correction exactly changes only snapshot_date',
      changed == ['snapshot_date'] and replacement == after
      and after == authentic_current.read_bytes(),
      {'changed_fields': changed, 'before': before_json['snapshot_date'], 'after': after_json['snapshot_date'],
       'independent_review': 'postfreeze_decoded/review_work/receipt-metadata-correction/ACTUAL-CORRECTION-REVIEW.json'})
failed_original = P / 'session/receipt-source-checks/CHECKS.json'
failed_retained = REPO / 'docs/engineering/localized-repair-c271/host-inspection-p08/delivery-verification/receipt-metadata-correction/CHECKS.json'
check('failed initial receipt check preserved in current repository',
      failed_original.read_bytes() == failed_retained.read_bytes(), ident(failed_retained))

code_checks = []
for row in receipt['receipt_source_checks']['code_identities']:
    path = REPO / row['path']
    data = path.read_bytes()
    ok = len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    ok = ok and data == (F / 'repository' / row['path']).read_bytes()
    code_checks.append({'path': row['path'], 'matches_frozen_and_receipt': ok, **ident(path)})
check('accepted production and test bytes unchanged at corrected receipt checkout',
      all(row['matches_frozen_and_receipt'] for row in code_checks), code_checks)

branch_map = {row['name']: row['commit']['sha'] for row in branches}
check('fresh Director branch observations match terminal receipt identities',
      branch_map.get('main') == 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
      and branch_map.get('work/c271-missing-import-digest-control') == receipt['receipt_commit']
      and pr['head']['sha'] == receipt['receipt_commit']
      and pr['base']['sha'] == branch_map['main'], branch_map)
check('fresh PR and issue remain open with unfinished branch retained',
      pr['state'] == 'open' and pr['draft'] is True and pr['merged_at'] is None and issue['state'] == 'open',
      {'pr': {'number': 274, 'state': pr['state'], 'draft': pr['draft'], 'merged_at': pr['merged_at']},
       'issue': {'number': 273, 'state': issue['state']}})


def current_section(obj):
    start = '<!-- ontokin-c271-p08-current -->'
    end = '<!-- /ontokin-c271-p08-current -->'
    body = obj['body']
    return body[body.index(start):body.index(end) + len(end)]


pr_section, issue_section = current_section(pr), current_section(issue)
(O / 'PR274-CURRENT-OBSERVED.md').write_text(pr_section + '\n')
(O / 'ISSUE273-CURRENT-OBSERVED.md').write_text(issue_section + '\n')
terminal_name = 'OntoKin_C271_P08_Delivery_Receipt_2026-11-21.json'
terminal_identity = ident(B / 'incoming/OntoKin' / terminal_name)
terminal_url = re.search(r'\[' + re.escape(terminal_name) + r'\]\(([^)]+)\)', pr_section).group(1)
check('PR and issue current blocks agree and confirm matching terminal receipt identity',
      pr_section == issue_section
      and terminal_identity['sha256'] in pr_section
      and '2,062,098 bytes' in pr_section
      and 'All four files were saved' in pr_section
      and 'exact returned bytes matched' in pr_section,
      {'terminal_receipt': terminal_identity, 'url': terminal_url,
       'library_file_id': 'libfile_fde3_f-171106f562c481919cca9d7da77435de_2ab2a24d43748191957f9bcc356b59de',
       'backing_file_id': 'file_000000005c2c81f595d1ed3dac21afad', 'version': 0,
       'pr_updated_at': pr['updated_at'], 'issue_updated_at': issue['updated_at']})
check('live CURRENT marks P08 delivery complete with matching frozen archive identity',
      current['latest_handoff']['phase_complete'] is True
      and current['latest_handoff']['sha256'] == prior['inputs'][0]['sha256']
      and current['latest_handoff']['bytes'] == prior['inputs'][0]['bytes']
      and current['latest_handoff']['source_revision'] == receipt['archive_source_commit']
      and current['next_action']['suggested_task'] == receipt['next_action'])
check('parent unfinished requirements preserved',
      task['status'] == 'in_progress'
      and {r['id']: r['status'] for r in task['requirements']} == receipt['parent_requirements'],
      {'status': task['status'], 'requirements': {r['id']: r['status'] for r in task['requirements']},
       'plan': {p['id']: p['status'] for p in task['plan']}})

read_set = []
for rel in ['startup/AGENTS.md', 'startup/GOAL.md', 'startup/ROLE.md',
            'startup/docs/workflow/PROTOCOL.md', 'startup/docs/workflow/HANDOFF.md',
            'startup/docs/workflow/templates/WORKER.md',
            'p08/README-START-HERE.md', 'p08/HANDOFF.md', 'p08/NEXT-TASK.md', 'p08/RECOVERY-STATUS.md',
            'p08/repository/docs/engineering/localized-repair-c271/host-inspection-p07/QUALIFICATION-PLAN.md',
            'p08/repository/docs/engineering/localized-repair-c271/current-host-p06/OPERATIONS.md']:
    read_set.append(ident(B / rel))

report = {
    'schema': 'ontokin.p08.startup-independent-reconciliation/1',
    'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer': '/root/p08_delivery_audit',
    'role': 'Independent Investigator/Reviewer for startup reconciliation only',
    'verdict': 'P08_PARTIAL_DELIVERY_COMPLETE_PARENT_UNFINISHED' if all(c['passed'] for c in checks) else 'RECONCILIATION_FINDINGS',
    'checks': checks,
    'checks_passed': all(c['passed'] for c in checks),
    'mechanical_verification': ident(O / 'VERIFICATION.json'),
    'mechanical_verification_correction': initial_failure,
    'read_set': read_set,
    'source_observation_provenance': {
        'description': 'Fresh GitHub API readbacks and authentic checkout provided by Director; this reviewer read and hashed them without Git operations.',
        'files': [ident(B / 'session' / n) for n in ['BRANCHES.json', 'PRS.json', 'ISSUE273.json']],
        'repo': str(REPO), 'observed_branch_commit': receipt['receipt_commit'],
        'direct_fresh_Library_query_by_reviewer': False,
    },
    'delivery_boundaries': [
        {'kind': 'accepted implementation', 'commit': receipt['accepted_code_commit'], 'scope': '135 focused static/filesystem/mocked methods, historical execution only.'},
        {'kind': 'immutable archive source', 'commit': receipt['archive_source_commit'], 'tree': receipt['archive_source_tree'], 'archive_sha256': prior['inputs'][0]['sha256'], 'frozen_status': 'save_pending'},
        {'kind': 'initial receipt publication with retained failed workflow check', 'commit': receipt['initial_receipt_commit'], 'error': receipt['postpublication_metadata_failure']['actual_failure']},
        {'kind': 'separate metadata correction', 'commit': receipt['receipt_commit'], 'tree': receipt['receipt_tree'], 'scope': 'Only existing canonical field CURRENT.snapshot_date plus separately retained failure/review evidence; frozen archive and accepted code unchanged.'},
        {'kind': 'terminal receipt save and current-block confirmation', 'identity': terminal_identity, 'url': terminal_url, 'evidence': ['PR274-CURRENT-OBSERVED.md', 'ISSUE273-CURRENT-OBSERVED.md'], 'self_reference_boundary': 'The receipt cannot contain its future own Library identity; current PR/issue blocks supply that final confirmation.'},
    ],
    'prior_delivery_blockers': [],
    'historical_unknown_operations': [
        {'operation': 'C270 broad-driver completion', 'status': 'unknown', 'source': 'p08/RECOVERY-STATUS.md and terminal receipt historical_unknowns', 'instruction': 'Do not infer success, failure, or termination; reconcile original evidence before any retry.'},
        {'operation': 'Global prior-process termination', 'status': 'unestablished', 'source': 'p08/RECOVERY-STATUS.md and terminal receipt historical_unknowns', 'instruction': 'Do not treat absence of a callback/current log as proof of zero launches or global termination.'},
    ],
    'current_unknown_operations': {
        'P08_at_terminal_receipt': [],
        'historical_workers': 'P08 implementation runs stopped and accepted; later package review/save/correction completed in separate receipt. Old frozen awaiting-build/review states are superseded by dated receipt evidence.',
        'reviewer_this_assignment': [],
        'limit': 'No global process census performed; historical uncertainty remains explicitly open.',
    },
    'unfinished_gates': [
        'H0 exact static runtime/dependency preparation and independent inspection-plan review.',
        'H1 actual host observation; H2 operational freeze; H3 actual Gate H, including original seven outcomes.',
        'Complete required routine and independent parent R03 acceptance.',
        'R04 reviewed main integration with lease and resulting-main verification.',
        'R05 final parent delivery/closure and applicable branch lifecycle.'
    ],
    'historical_failures_preserved': [
        'P08 draft/candidate findings and withdrawn candidate002 approval, candidate003 map refresh failure.',
        'Run001: 64 setup errors across 39 of 135 methods; distinct corrected run002 retained. No rerun by this reviewer.',
        'Initial final-source check identity refusal; separate later exact-source checks.',
        'Rejected package attempt001 FPKG-01 and source-recovery audit helper failure; corrected attempt002 retained separately.',
        'Initial receipt be159c31 workflow timestamp failure, metadata reviewer lookup failure, and exact later correction/check records.',
        'Earlier P02 routine unit timeout/documentation failure and P03/P04 historical runtime refusal remain historical outcomes; later phase delivery does not relabel those runs.',
    ],
    'exact_next_action': {
        'precondition': 'Director completes current startup reconciliation and confirms a new early recovery ZIP before substantial H0 work.',
        'first_technical_action': 'Authenticate the retained P05 Node archive and unchanged C195 dependency archive, then independently freeze their exact archive/member inventories and concrete task-specific destination/absence guards before running the existing preparer.',
        'H0_only': 'Prepare exact install plans; use existing preparer dry-run/apply only as selected and reviewed; statically inspect actual source, Python, ldd, loader/ELF files; freeze the complete executable inspection plan and separately supplied review digest for independent review.',
        'acceptance': 'Exact paths, identities, commands, environment, closure, absence guards and fresh evidence destinations concrete; independent static review accepts the complete H0 plan.',
        'stop': 'Stop before H1 Node/ldd execution or actual host observation, any probe/checker, original-seven execution, full routine, integration or parent closure.',
        'concrete_H0_gate_dependencies': ['Confirmed new early recovery', 'Authenticated external Node/dependency archives and inventories', 'Complete actual host static closure', 'Independent exact inspection-plan review and separate digest'],
        'scope_limit': 'This audit does not execute H0 or establish its input availability. Missing or unexplained closure must be recorded as a specific blocker in the selected phase.'
    },
    'preservation_notes': [
        'Frozen ZIP and separate receipt stay unchanged; no rebuild is needed for receipt-only late observations.',
        'Source snapshots are selected online continuation inputs, not a complete offline backup.',
        'C262 and rejected package attempt001 remain external historical dependencies; this audit did not download or reverify those external bytes.',
        'The compressed run stores are covered by ZIP payload hashes and retained prior independent stream verification; this startup audit does not repeat archived utility execution or recreate fixture paths/special entries.'
    ],
    'audit_lookup_history': [
        'Initial broad inventory/receipt reads produced truncated display; subsequent JSON parsing selected required fields and the verifier inspected every manifest entry.',
        'One rg query included nonexistent current-host-p05/inputs; exit 2 is a read-only lookup error, not an artifact defect. No inferred source path was executed.',
        'Initial source inventory comparison incorrectly excluded observed-main/; failed verifier/report retained, corrected comparison is recorded above.'
    ],
    'actions_not_performed': ['Git commands or mutations', 'GitHub writes', 'Node or ldd execution', 'product tests', 'dependency installation', 'child workers', 'global startup or delivery'],
    'ownership_disposition': 'Only audits/p08_delivery files created. Reviewer stopped after reports; no worker/process/write remains active.'
}
(O / 'AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')

markdown = '''# P08 delivery reconciliation

**Verdict: P08 partial delivery is complete. C271 remains in progress.** No prior-delivery blocker was found.

The original ZIP matches **14,680,844 bytes** and SHA-256 `037d7ff2b2b64f61f1b53b5fdae93b3d16a32bdb6fd681f45f824e2652d425b5`. Fresh extraction verified 4,370 safe unique entries, 4,369 payload hashes, 281 source byte/Git-blob identities and 4,075 mapped recovery files. Both standalone prompts exactly match their ZIP members. All 179 compressed terminal-receipt evidence files decoded with matching sizes and hashes.

The terminal receipt matches **2,062,098 bytes** and SHA-256 `e5a7017a847992a25dbd9f65b19dd32ca730578d56406b44e0f4beff68592114`. Fresh Director-provided PR #274 and issue #273 current blocks confirm its saved identity and all four saved-byte comparisons. The authentic checkout's canonical receipt and corrected CURRENT bytes match the receipt's embedded evidence.

## Freeze and correction boundary

Accepted code is `cf16a0facebdce2fadf69e5c7fae6f2ca31cbd2e`; the immutable archive source is `3ed2670bf9bf4326dab126d3466699053f6b4320`. Its `save_pending` fields correctly precede the later receipt. First receipt commit `be159c31db3ef26f66adbcb641e326e2b6ebc198` failed the explicit UTC timestamp check. Correction head `2c6bbfb7aa1d402ce47ffdc24adb4d89b8a81c1e` changes only the existing CURRENT timestamp field and adds retained correction evidence. The failed check remains preserved; later exact-receipt checks passed. The archive and accepted production/test bytes are unchanged.

Main remains `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. Branch `work/c271-missing-import-digest-control` remains retained at the correction head; PR #274 is draft/open with no merge date, and issue #273 is open. R01/R02 are done; R03–R05 are not done. This is phase delivery, without main integration or parent completion.

## Remaining uncertainty and next action

Historical **C270 broad-driver completion remains unknown**, and **global prior-process termination remains unestablished**. No current unresolved P08 operation is reported at its terminal boundary. Earlier run001, rejected package, helper failures, receipt timestamp failure, P02 routine failures and P03/P04 runtime refusals remain evidence, not erased outcomes.

After the Director confirms new early recovery, the first technical H0 action is to authenticate the retained P05 Node and unchanged C195 dependency archives and independently freeze exact archive/member inventories and task-specific destination/absence guards. H0 may then use the existing preparer as selected, statically inspect actual source/Python/ldd/loader inputs, and obtain independent review of the exact executable inspection plan with a separate digest. **Stop before H1 Node/ldd execution or actual host observation.** Input availability and closure are not established by this startup audit.

## Audit limits and preserved audit correction

No Git command, product test, Node/ldd command, dependency installation, GitHub mutation or worker spawn occurred. Live readbacks came from the Director. Local source hashes do not independently prove historical commit/tree membership; the package retains that earlier verification. Inner fixture stores were not restored or executed.

The initial verifier's sole failed group assumed every source snapshot was below `repository/`; two intentional `observed-main/` snapshots also belong to the source manifest. `VERIFICATION.json` and its verifier remain unchanged. `AUDIT.json` records the corrected exact inventory, which passes. The connector-materialized CURRENT has one extra trailing newline; parsed content agrees, and byte checks use the authentic checkout.

Detailed evidence: `AUDIT.json`, `VERIFICATION.json`, `POSTFREEZE-INVENTORY.json`, and captured PR/issue current sections. The reviewer owns only this audit directory and stops here.
'''
(O / 'REPORT.md').write_text(markdown)
print(json.dumps({'verdict': report['verdict'], 'reconciliation_checks': len(checks),
                  'failed': [c['name'] for c in checks if not c['passed']],
                  'report': ident(O / 'AUDIT.json'), 'summary': ident(O / 'REPORT.md')}))
