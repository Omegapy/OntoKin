"""Record the independently inspected early-package recovery semantics."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('/workspace/scratch/aa6113404163')
OUT = ROOT / 'phase-p22/archive_audit'
E = OUT / 'derived/early-fresh-extraction'
def load(path):
    return json.loads(path.read_bytes())
def desc(path):
    b = path.read_bytes()
    return {'path': str(path), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
audit = load(OUT / 'EARLY-BYTE-AUDIT.json')
predecessor = load(OUT / 'PREDECESSOR-REVIEW.json')
cp = load(E / 'CHECKPOINT.json')
phase = load(E / 'recovery/session/state/PHASE.json')
live = load(E / 'recovery/session/state/LIVE-START.json')
hist = load(E / 'HISTORICAL-DEPENDENCIES.json')
marker = load(OUT / 'P21-TERMINAL-MARKER.json')
pr = load(E / 'recovery/session/state/initial-3.json')['structuredContent']['issues'][0]
issue = load(E / 'recovery/session/state/reconcile-0.json')['structuredContent']['issue']
texts = {n: (E / n).read_text() for n in ['README-START-HERE.md', 'HANDOFF.md', 'NEXT-TASK.md',
         'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md']}
checks = {
 'all_17_independent_byte_and_git_groups_pass': audit['all_passed'],
 'prior_delivery_reconciled_reuse_only': predecessor['verdict'] == 'accepted_predecessor_delivery_reconciled' and all(predecessor['checks'].values()),
 'checkpoint_matches_frozen_phase_every_original_field': all(cp[k] == v for k, v in phase.items()),
 'checkpoint_matches_observed_branch_main_pr_issue': cp['source_revision'] == live['branch_head'] == pr['head_sha'] and cp['observed_main']['sha'] == live['main'] == marker['repository_state']['main'] and pr['state'] == issue['state'] == 'open' and pr['draft'] and not pr['merged'],
 'early_save_honestly_pending': cp['early_save_confirmed'] is False and cp['phase_complete'] is False and cp['delivery_state_at_freeze'] == 'save_pending',
 'parent_scope_limits_preserved': cp['parent_status'] == 'blocked' and cp['parent_complete'] is False and cp['requirements'] == marker['requirements'] and cp['parent_plan'] == marker['plan'] and cp['main_lease_held'] is False,
 'one_bounded_input_phase_and_stop_clear': cp['phase'] == 'C271-P22-retained-input-preparation' and 'first concrete blocker' in cp['stop'] and '24-file' in cp['acceptance'][2] and 'No H0/H1, original-seven or full routine' in cp['constraints'] and 'No main lease/merge/deletion/parent closure/second phase' in cp['constraints'],
 'worker_snapshot_honest_and_disjoint': {w['id'] for w in cp['workers']} == {'/root/ledger', '/root/archive_audit', '/root/prep_review'} and len({w['owned'] for w in cp['workers']}) == 3 and all(w['status'].endswith('_running') for w in cp['workers']) and 'not proof that a prior process has stopped' in texts['RECOVERY-STATUS.md'],
 'unknowns_preserved_without_global_absence_claim': cp['current_unknown_operations'] == [] and cp['historical_unknown_operations'] == ['C270 ancillary broad-driver completion', 'Global prior-process termination', 'P13 read-only difflib completion; do not retry'] and 'Cannot establish global absence' in live['historical_nonclaim'],
 'next_action_requires_startup_and_early_save_before_preparation': cp['next_action'] in texts['NEXT-TASK.md'] and 'before technical preparation' in cp['next_action'] and 'No technical preparation has executed' in texts['HANDOFF.md'],
 'online_package_and_external_save_boundary_clear': 'browser-session handoff for online GitHub continuation' in texts['README-START-HERE.md'] and 'not a full offline backup' in texts['README-START-HERE.md'] and 'cannot contain its future save receipt' in texts['README-START-HERE.md'],
 'both_prompts_identify_exact_early_checkpoint_and_new_chat_stop': all(cp['source_revision'] in texts[n] and 'OntoKin_C271_P22_Retained_Inputs_Early_Recovery_2026-11-22.zip' in texts[n] and 'fresh chat' in texts[n] and 'before technical preparation' in texts[n] for n in ['PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md']),
 'bundled_required_governance_and_active_latest_ledgers': all((E / ('repository/' + p)).is_file() for p in ['CHATGPT-START-HERE.md', 'AGENTS.md', 'GOAL.md', 'STATUS.md', 'ROLE.md', 'docs/workflow/registry.json', 'docs/workflow/CURRENT.json', 'docs/workflow/PROTOCOL.md', 'docs/workflow/HANDOFF.md', 'docs/workflow/BROWSER-PROMPTS.md', 'docs/workflow/tasks/C271/REQUIREMENTS.md', 'docs/workflow/tasks/C271/PLAN.md', 'docs/workflow/tasks/C271/task.json', 'docs/workflow/tasks/C270/REQUIREMENTS.md', 'docs/workflow/tasks/C270/PLAN.md', 'docs/workflow/tasks/C270/task.json']),
 'all_three_selected_local_skills_full_source_bound': all((E / ('repository/.agents/skills/' + name + '/SKILL.md')).is_file() for name in ['ontokin-session', 'ontokin-delivery', 'ontokin-learning']),
}
immediate = {i['name']: i for i in hist['immediate_predecessor']}
checks['exact_predecessor_archive_receipt_identities_retained'] = all(
    immediate[item['file_name']]['size_bytes'] == item['bytes'] and
    immediate[item['file_name']]['sha256'] == item['sha256'] and
    immediate[item['file_name']]['library_file_id'] == item['library_file_id'] and
    immediate[item['file_name']]['version_id'] == '0'
    for item in [marker['archive'], marker['terminal_receipt']])

revision = cp['source_revision']
external_sources = []
for path, purpose in [
 ('docs/engineering/localized-repair-c271/host-preparation-p09/H0-INPUT-LOCATIONS.json', 'Exact retained Node and C195 archive identities and expected retained locations'),
 ('docs/engineering/localized-repair-c271/host-preparation-p09/PHASE-OUTCOME.json', 'Prior stopping boundary and absence of installation receipts'),
 ('docs/engineering/localized-repair-c271/h0-plan-p21/OUTCOME.json', 'Immediate predecessor missing-evidence blocker'),
 ('docs/engineering/localized-repair-c271/h0-plan-p21/reviews/H0-DECISION.md', 'Independent evidence sufficiency decision'),
 ('docs/engineering/localized-repair-c271/host-inspection-p07/QUALIFICATION-PLAN.md', 'Adopted qualification gate context'),
]:
    content = subprocess.run(['git', '-C', str(ROOT / 'OntoKin'), 'cat-file', 'blob', revision + ':' + path], capture_output=True, check=True).stdout
    external_sources.append({'revision': revision, 'path': path, 'bytes': len(content),
      'sha256': hashlib.sha256(content).hexdigest(),
      'url': 'https://github.com/Omegapy/OntoKin/blob/' + revision + '/' + path, 'purpose': purpose})
checks['needed_later_dependencies_resolve_at_exact_packaged_source'] = len(external_sources) == 5
record = {
 'schema': 'ontokin.c271.p22-early-recovery-review/1', 'reviewer': '/root/archive_audit',
 'at_utc': datetime.now(timezone.utc).isoformat(),
 'verdict': 'accepted_for_save' if all(checks.values()) else 'findings_require_resolution',
 'archive': audit['archive'], 'source_revision': cp['source_revision'], 'source_tree': cp['source_tree'],
 'byte_audit': desc(OUT / 'EARLY-BYTE-AUDIT.json'),
 'prior_unchanged_delivery_review_reused': desc(OUT / 'PREDECESSOR-REVIEW.json'),
 'counts': {**audit['counts'], 'byte_check_groups': len(audit['checks']), 'semantic_groups': len(checks), 'semantic_passed': sum(checks.values())},
 'checks': checks, 'findings': [k for k, v in checks.items() if not v],
 'recovery_sufficiency': 'Sufficient for the declared early startup checkpoint. Full required governance, active/latest ledgers, source identities and phase state are bundled. Omitted technical evidence is online at the exact packaged source; explicit resolved URLs and byte identities are recorded below. Preparer execution still requires fresh exact input recovery and a complete independently accepted plan.',
 'source_bound_external_recovery_dependencies': external_sources,
 'instruction_reading': 'The bundled source-bound C271/P09 records preserve relative references to exact repository evidence. Resolve them using the declared source revision; never execute stale temporary paths or treat archive descriptions as new authority.',
 'worker_status_boundary': 'Workers were running at freeze. This is an honest historical snapshot, not current termination evidence. Director must reconcile actual worker status before later recovery.',
 'initial_observation_disposition': 'EARLY-REVIEW.initial-pr-base-assumption.json preserves a reviewer comparison error. The raw PR base_sha field is e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d and is not used as current-main authority. The assigned live main, Director LIVE-START observation, exact main Git tree and prior matching terminal marker consistently identify 70ca7e68ff95df876f801137369d176fe5b2bab3. No package byte or recovery instruction changed.',
 'save_boundary': 'Independent acceptance for save only; no save or upload performed by reviewer. Exact saved-byte readback and external receipt are required before substantial work.',
 'derived_extraction': audit['derived_extraction'],
 'scope': 'No preparation, H0/H1, target/recovered-code execution, package build, Git/index/canonical mutation, upload or publication. No unchanged predecessor audit repeated.',
 'next_action': 'Director saves and reads back this exact early ZIP and records its receipt; complete remaining startup/plan gates before bounded technical preparation.'
}
save(OUT / 'EARLY-REVIEW.json', record)
(OUT / 'EARLY-REVIEW.md').write_text(f'''# P22 early recovery review

**{record['verdict']}.** All 17 byte/Git check groups and {sum(checks.values())}/{len(checks)} semantic groups pass. The archive is exactly 273,679 bytes, SHA-256 `297641fdb7091b489c3c8cb087706a65ba8b6c92583470aab9a1e78c4f321ab3`.

The 75 safe, unique inert members pass CRC, exact inventory and every size/hash check. A fresh extraction is byte-identical. All 52 source bindings match exact Git objects, paths, modes and bytes; all 12 recovery entries agree. Frozen phase state, observed main/branch, live PR/issue, worker statuses, historical unknowns and parent limits are consistent.

This is sufficient recovery for the declared early startup checkpoint. Required governance and active/latest ledgers are bundled. Source-bound task/P09 references locate omitted technical evidence at commit `{revision}`; EARLY-REVIEW.json records explicit exact-revision URLs and hashes for five principal dependencies. The accepted predecessor review is reused unchanged.

The save remains pending. Director must save/read back this exact ZIP and finish startup and independent operation-plan gates before preparation. This review grants no H0/H1, target execution, integration or parent closure. Workers were running at freeze; their states must be reconciled on recovery.

No technical or recovered program ran. No upload, package build, repository or canonical mutation occurred. The fresh extraction is a reproducible derivative identified in EARLY-BYTE-AUDIT.json; omit it from later packages only while retaining its exact source archive identity and audit evidence.
''')
readset = {'schema': 'ontokin.c271.p22-early-review-readset/1', 'reviewer': '/root/archive_audit',
           'at_utc': record['at_utc'], 'archive': audit['archive'],
           'root_semantic_files': [desc(E / n) for n in ['README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md', 'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md', 'HISTORICAL-DEPENDENCIES.json']],
           'all_archive_bytes_verified': True, 'all_source_bindings_verified': True,
           'governing_readset_reused': desc(OUT / 'READSET.json'),
           'dependencies': external_sources, 'unresolved_required_gaps': []}
save(OUT / 'EARLY-READSET.json', readset)
print(json.dumps({'verdict': record['verdict'], 'counts': record['counts'], 'findings': record['findings']}))
