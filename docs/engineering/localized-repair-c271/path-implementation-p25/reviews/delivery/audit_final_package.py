"""Independent final archive verification. No product import or behavioral test."""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import zipfile

ROOT = Path('/workspace/scratch/bd99261bd84d')
REPO = ROOT / 'OntoKin'
OUT = Path(__file__).resolve().parent
P25 = 'docs/engineering/localized-repair-c271/path-implementation-p25'
CORE = '0df3d39084e11b68a434035fa0cc67e1d7d8955e'
TREE = '6bf8d88e034bbb318d7015caa665a88a14175970'
START = 'ce411b12e601036a33698aa7c3290722e602ea75'
MAIN = 'e43cc6c5777874101a40559e4058ad6826b07e51'
ARCHIVE = ROOT / 'packages/final/OntoKin_C271_P25_RTLD_Path_Implementation_Handoff_2026-11-23.zip'
checks = []
source_checks = []
recovery_checks = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(name, condition, detail=None):
    checks.append({'check': name, 'passed': bool(condition), 'detail': detail})


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


raw = ARCHIVE.read_bytes()
root_result = json.loads((ROOT / 'state/final-package-verification.json').read_bytes())
check('archive_exact_declared_identity', len(raw) == root_result['bytes'] == 2264988 and sha(raw) == root_result['sha256'] == '23fb56fbcb3e1d1d8011e1bd97242be3b7d9c114f91e18c5e12fb8050d7d5a08')
check('source_commit_parent_and_tree', git('rev-parse', CORE + '^{tree}').decode().strip() == TREE and git('rev-parse', CORE + '^').decode().strip() == START)

with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    infos = archive.infolist()
    names = [entry.filename for entry in infos]
    name_set = set(names)
    safe = all(entry.orig_filename == entry.filename and '\x00' not in entry.filename and not entry.filename.startswith('/') and '\\' not in entry.filename and ':' not in entry.filename.split('/')[0] and all(part not in ['', '.', '..'] for part in entry.filename.split('/')) and PurePosixPath(entry.filename).as_posix() == entry.filename for entry in infos)
    prefix_safe = not any('/'.join(name.split('/')[:i]) in name_set for name in names for i in range(1, len(name.split('/'))))
    regular = all(not entry.is_dir() and stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFREG and not (entry.flag_bits & 1) for entry in infos)
    check('safe_relative_unambiguous_paths', safe and prefix_safe)
    check('no_duplicates_encryption_symlink_or_special_files', len(names) == len(name_set) and regular)
    check('zip_crc_all_members', archive.testzip() is None)
    check('482_members', len(names) == root_result['members'] == 482)
    payload = {name: archive.read(name) for name in names}
    manifest = json.loads(payload['MANIFEST-SHA256.json'])['files']
    sources = json.loads(payload['SOURCE-MANIFEST.json'])['files']
    recovery = json.loads(payload['RECOVERY-MANIFEST.json'])['files']
    checkpoint = json.loads(payload['CHECKPOINT.json'])
    manifest_names = [row['path'] for row in manifest]
    check('manifest_exact_all_payload_inventory', len(manifest_names) == len(set(manifest_names)) == 481 and set(manifest_names) == name_set - {'MANIFEST-SHA256.json'})
    check('all_manifest_bytes_and_sha256', all(len(payload[row['path']]) == row['bytes'] and sha(payload[row['path']]) == row['sha256'] for row in manifest))
    required = {'README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md', 'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md', 'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json', 'HOST-ENVIRONMENT.md', 'SOURCE-MANIFEST.json', 'RECOVERY-MANIFEST.json'}
    check('required_roots_exact', {name for name in names if '/' not in name} == required)
    check('404_source_bindings_exact_inventory', len(sources) == len({row['member'] for row in sources}) == root_result['source_bindings'] == 404 and {row['member'] for row in sources} == {name for name in names if name.startswith('repository/')} and all(row['member'] == 'repository/' + row['path'] for row in sources))
    check('66_recovery_bindings_exact_inventory', len(recovery) == len({row['member'] for row in recovery}) == root_result['recovery_files'] == 66 and {row['member'] for row in recovery} == {name for name in names if name.startswith('recovery/')} and all(row['member'] == 'recovery/' + row['session_path'] for row in recovery))
    for row in sources:
        source_bytes = git('show', row['commit'] + ':' + row['path'])
        mode = git('ls-tree', row['commit'], '--', row['path']).decode().split()[0]
        actual = payload[row['member']]
        source_checks.append({'path': row['path'], 'commit': row['commit'], 'sha256': sha(actual), 'exact_git_bytes': actual == source_bytes, 'declared_identity': len(actual) == row['bytes'] and sha(actual) == row['sha256'], 'declared_mode': row['mode'] == mode, 'zip_mode': oct(next(entry.external_attr >> 16 for entry in infos if entry.filename == row['member']))})
    check('all404_git_bytes_identity_and_modes', all(row['exact_git_bytes'] and row['declared_identity'] and row['declared_mode'] for row in source_checks))
    check('only_declared_core_and_main_revisions', {row['commit'] for row in sources} == {CORE, MAIN})
    source_paths = {row['path'] for row in sources}
    main_required = {'CHATGPT-START-HERE.md', 'AGENTS.md', 'GOAL.md', 'STATUS.md', 'ROLE.md', 'docs/workflow/registry.json', 'docs/workflow/PROTOCOL.md', 'docs/workflow/HANDOFF.md', 'docs/workflow/BROWSER-PROMPTS.md', 'docs/workflow/EPHEMERAL-HOST.md', '.agents/skills/ontokin-session/SKILL.md', '.agents/skills/ontokin-delivery/SKILL.md', '.agents/skills/ontokin-learning/SKILL.md'}
    check('mandatory_main_instructions_and_selected_skills', main_required <= {row['path'] for row in sources if row['commit'] == MAIN})
    task_required = {'docs/workflow/CURRENT.json', 'docs/workflow/tasks/C271/task.json', 'docs/workflow/tasks/C271/REQUIREMENTS.md', 'docs/workflow/tasks/C271/PLAN.md', 'prototypes/static_tray_v01/current_host_inspection_v01.py', 'tests/test_current_host_rtld_paths_v01.py'}
    check('mandatory_active_task_and_accepted_code', task_required <= {row['path'] for row in sources if row['commit'] == CORE})
    changed = git('diff', '--name-only', START, CORE).decode().splitlines()
    check('entire381_file_published_change_included', len(changed) == 381 and set(changed) <= source_paths)
    published_p25 = set(git('ls-tree', '-r', '--name-only', CORE, '--', P25).decode().splitlines())
    check('complete_published_P25_subtree_included', published_p25 <= source_paths)
    for row in recovery:
        actual = payload[row['member']]
        session_bytes = (ROOT / row['session_path']).read_bytes()
        recovery_checks.append({'member': row['member'], 'sha256': sha(actual), 'declared_identity': len(actual) == row['bytes'] and sha(actual) == row['sha256'], 'session_bytes_equal': actual == session_bytes})
    check('all66_recovery_bytes_match_session_and_manifest', all(row['declared_identity'] and row['session_bytes_equal'] for row in recovery_checks))
    startup_files = {str(path.relative_to(ROOT)) for path in (ROOT / 'state/reconcile').rglob('*') if path.is_file()}
    check('complete_unique_startup_reconciliation_preserved', startup_files <= {row['session_path'] for row in recovery})
    check('builder_exact_and_source_bound_config', payload['recovery/build_final.py'] == (ROOT / 'build_final.py').read_bytes() and json.loads(payload['recovery/state/final-config.json'])['source_commit'] == CORE)

    if not (safe and prefix_safe and regular and len(names) == len(name_set)):
        raise ValueError('Unsafe archive: extraction deliberately not attempted')
    with tempfile.TemporaryDirectory(prefix='final-package-extract-', dir=OUT) as directory:
        fresh = Path(directory)
        for name in names:
            target = fresh / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(payload[name])
            os.chmod(target, 0o644)
        check('fresh_extraction_exact_inventory', {str(path.relative_to(fresh)) for path in fresh.rglob('*') if path.is_file()} == name_set)
        check('fresh_extraction_every_payload_size_and_hash', all(len((fresh / row['path']).read_bytes()) == row['bytes'] and sha((fresh / row['path']).read_bytes()) == row['sha256'] for row in manifest) and (fresh / 'MANIFEST-SHA256.json').read_bytes() == payload['MANIFEST-SHA256.json'])
        check('fresh_extracted_sources_match_exact_git', all((fresh / row['member']).read_bytes() == git('show', row['commit'] + ':' + row['path']) for row in sources))
        check('fresh_extracted_recovery_matches_session', all((fresh / row['member']).read_bytes() == (ROOT / row['session_path']).read_bytes() for row in recovery))

    for member, filename in [('PROMPT-1-CONTINUE.md', 'OntoKin_C271_P25_Continue_2026-11-23.md'), ('PROMPT-2-RECOVER.md', 'OntoKin_C271_P25_Recover_2026-11-23.md')]:
        standalone = (ARCHIVE.parent / filename).read_bytes()
        expected = next(row for row in root_result['prompts'] if row['file_name'] == filename)
        check('standalone_prompt:' + filename, standalone == payload[member] and len(standalone) == expected['bytes'] and sha(standalone) == expected['sha256'])
    check('ephemeral_rule_prominent', all(b'different disposable execution host' in payload[name] and b'historical evidence only' in payload[name] for name in ['README-START-HERE.md', 'HOST-ENVIRONMENT.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md']))
    check('portable_source_reconstruction_and_no_old_host_reuse', CORE.encode() in payload['HOST-ENVIRONMENT.md'] and b'fresh clone' in payload['HOST-ENVIRONMENT.md'] and b'fresh component identities' in payload['HOST-ENVIRONMENT.md'] and b'Never seek or repair a previous host' in payload['HOST-ENVIRONMENT.md'])
    check('first_action_delivery_only_before_later_phase', all(b'finish delivery only and stop' in payload[name] for name in ['CHECKPOINT.json', 'NEXT-TASK.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md']))
    check('online_continuation_limits_explicit', b'not a complete offline repository backup' in payload['README-START-HERE.md'] and checkpoint['package_type'] == 'browser-session handoff for online GitHub continuation')
    check('checkpoint_source_and_main_trees', checkpoint['source_commit'] == CORE and checkpoint['source_tree'] == TREE and checkpoint['observed_main'] == MAIN and checkpoint['observed_main_tree'] == git('rev-parse', MAIN + '^{tree}').decode().strip())
    check('parent_and_runtime_states_truthful', checkpoint['parent_complete'] is False and checkpoint['parent_status'] == 'in_progress' and checkpoint['requirements'] == {'R01': 'done', 'R02': 'done', 'R03': 'not_done', 'R04': 'not_done', 'R05': 'not_done'} and checkpoint['parent_plan'] == {'P01': 'done', 'P02': 'in_progress'} and checkpoint['h0_accepted'] is False and checkpoint['h1_executed'] is False and checkpoint['main_lease_held'] is False and checkpoint['pr'] == {'number': 274, 'state': 'open', 'draft': True, 'merged': False} and checkpoint['issue'] == {'number': 273, 'state': 'open'})
    prefix = 'repository/' + P25 + '/'
    acceptance = json.loads(payload[prefix + 'ACCEPTANCE.json'])
    phase = json.loads(payload[prefix + 'PHASE.json'])
    task = json.loads(payload['repository/docs/workflow/tasks/C271/task.json'])
    check('canonical_parent_phase_and_N34_preserved', task['session_phase'] == phase and phase['phase_complete'] is False and task['status'] == 'in_progress' and acceptance['N34']['decision'] == 'withhold_operational_plan_adoption' and acceptance['N34']['actual_source_completeness_evidence'] == 'not_supplied_in_P25' and acceptance['N34']['runtime_method'] is None and acceptance['N34']['runtime_pass'] is False and acceptance['N34']['runtime_skip'] is False)
    canonical_review = json.loads(payload[prefix + 'reviews/delivery/CANONICAL-REVIEW.json'])
    reviewed_paths = {row['path']: row for row in canonical_review['read_set']}
    canonical_names = ['ACCEPTANCE.json', 'OUTCOME.json', 'PHASE.json', 'WORKERS.json', 'README.md']
    check('reviewed_core_canonical_bytes_unchanged', all(sha(payload[prefix + name]) == reviewed_paths[P25 + '/' + name]['sha256'] for name in canonical_names) and all(sha(payload['repository/' + path]) == reviewed_paths[path]['sha256'] for path in ['docs/workflow/CURRENT.json', 'docs/workflow/tasks/C271/task.json', 'docs/workflow/tasks/C271/REQUIREMENTS.md', 'docs/workflow/tasks/C271/PLAN.md']))

    dependencies = json.loads(payload['HISTORICAL-DEPENDENCIES.json'])
    with zipfile.ZipFile(ROOT / 'packages/early/OntoKin_C271_P25_RTLD_Path_Early_Recovery_2026-11-23.zip') as early:
        inherited = json.loads(early.read('HISTORICAL-DEPENDENCIES.json'))
    p24_marker = json.loads(payload['recovery/state/startup/p24-terminal.json'])
    check('historical_wrapper_correct_and_original_preserved', dependencies['schema'] == 'ontokin.c271.p25-historical-dependencies/1' and dependencies['inherited_unchanged'] == inherited and dependencies['immediate_predecessor'] == p24_marker['archive'] and 'not this P25 package' in dependencies['inherited_path_namespace'])
    check('C262_exact_identity_retained', '532260846' in json.dumps(dependencies) and 'libfile_fde3_f-99755' in json.dumps(dependencies))
    check('early_receipt_and_clarification_preserved', dependencies['early_recovery'] == json.loads(payload['recovery/state/EARLY-RECOVERY-RECEIPT.json']) and sha(payload[prefix + 'EARLY-PACKAGE-CLARIFICATION.json']) == 'b70fa654bbc89327615864b6884b2634762921889cd4d9daf676e38df74b3e23' and json.loads(payload[prefix + 'EARLY-CLARIFICATION-RECEIPT.json'])['library_file_id'] == 'libfile_fde3_f-f60165abf6588191983a9ae019d060cd_2ab2a24d43748191957f9bcc356b59de')
    check('all_adapter_freezes_and_runs_preserved', all(prefix + 'reviews/controls/' + suffix in name_set for number in range(1, 6) for suffix in [f'ADAPTER-{number:03d}.py.source', f'ADAPTER-FREEZE-{number:03d}.json', f'attempt{number:03d}/RESULT.json', f'attempt{number:03d}/TEST.log']))
    check('independent_findings_and_parser_failure_preserved', json.loads(payload[prefix + 'reviews/delivery/ADAPTER-REVIEW-001.json'])['status'] == 'changes_required' and json.loads(payload[prefix + 'reviews/delivery/ADAPTER-EVIDENCE-AUDIT-001.json'])['summary']['failed'] == 1 and json.loads(payload[prefix + 'reviews/delivery/ADAPTER-REVIEW-002.json'])['status'] == 'accepted_for_bounded_synthetic_P25_controls')
    check('root_record_failure_and_partial_bytes_preserved', json.loads(payload[prefix + 'checks/core-records-attempt001/RESULT.json'])['exit_code'] == 1 and all(prefix + 'checks/core-records-attempt001/' + name in name_set for name in ['partial-ACCEPTANCE.json', 'finalize_core_records.py.source']))
    check('dependent_gate_ordering_failure_preserved', json.loads(payload['recovery/state/frozen-gates-ordering-incident.json'])['exit_code'] == 1 and 'recovery/state/run_frozen_gates-001.py' in name_set)
    prior_gates = json.loads(payload['recovery/state/core-frozen-gates/RESULT.json'])
    gates = json.loads(payload['recovery/state/core002-frozen-gates/RESULT.json'])
    check('both_whitespace_failures_preserved', json.loads(payload[prefix + 'checks/core-final-whitespace/RESULT.json'])['exit_code'] == 2 and prior_gates['passed'] is False and next(row for row in prior_gates['checks'] if row['name'] == 'whitespace')['exit_code'] == 2)
    check('four_path_exception_bound_to_final_published_tree', gates['exact_staged_tree'] == TREE and gates['staged_tree_unchanged_after'] is True and gates['passed'] is True and all(row['exit_code'] == 0 for row in gates['checks']) and len([arg for arg in next(row for row in gates['checks'] if row['name'] == 'whitespace')['command'] if arg.startswith(':(exclude)')]) == 4)
    output_bindings = []
    for record in [gates, prior_gates]:
        for gate in record['checks']:
            for row in gate['outputs']:
                data = payload['recovery/' + row['path']]
                output_bindings.append(len(data) == row['bytes'] and sha(data) == row['sha256'])
    check('all_final_and_failed_frozen_gate_outputs_exact', all(output_bindings))
    publication = json.loads(payload['recovery/state/core-publication.json'])
    intent = json.loads(payload['recovery/state/core002-publication-intent.json'])
    check('core_publication_and_intent_same_commit_tree_parent', publication['commit'] == CORE and publication['tree'] == intent['expected_tree'] == TREE and publication['parent'] == intent['expected_head'] == START and intent['non_force'] is True and publication['expected_head_nonforce_update'] is True and publication['changed_files_verified'] == len(changed) == 381)
    check('unpublished_failed_tree_and_lag_honestly_reconciled', json.loads(payload['recovery/state/PUBLICATION-ATTEMPT-HISTORY.json'])['attempts'][0]['remote_mutations'] == 0 and publication['current_unknown_operations'] == [] and publication['PR274_later_readback']['head'] == CORE and 'no write retried' in publication['pr_initial_readback_lag']['resolution'])
    check('empty_CI_observations_no_pass_claim', json.loads(payload['recovery/state/core-status.json']) == {'statuses': []} and json.loads(payload['recovery/state/core-runs.json']) == {'workflow_runs': []} and b'No remote CI pass is inferred' in payload['HANDOFF.md'])
    check('future_save_pending_not_fabricated', checkpoint['delivery_state'] == 'technical_boundary_reached_final_save_pending' and prefix + 'P25-DELIVERY.json' not in name_set)

summary = {'checks': len(checks), 'passed': sum(row['passed'] for row in checks), 'failed': sum(not row['passed'] for row in checks), 'members': len(names), 'source_bindings': len(sources), 'recovery_files': len(recovery)}
report = {'schema': 'ontokin.c271.p25-independent-final-package-audit/1', 'reviewer': '/root/reconcile', 'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'archive': {'path': str(ARCHIVE), 'bytes': len(raw), 'sha256': sha(raw), 'source_commit': CORE, 'source_tree': TREE}, 'summary': summary, 'checks': checks, 'source_checks': source_checks, 'recovery_checks': recovery_checks, 'read_coverage': 'All root guidance and new historical wrapper read; unchanged inherited dependency document reused through exact object equality. Builder read fully but not executed. All manifests, payloads and source/recovery identities checked mechanically. Already-reviewed source text reused through exact bytes. New gate/publication/failure records read; no claim of rereading every historical artifact or raw trace.', 'limits': ['Local package verification only; saved Library bytes/IDs/version are a separate subsequent audit.', 'Fresh extraction was created only inside reviewer-owned temporary space and removed after verification.', 'No product import, behavioral test, host reconstruction or Git mutation performed.', 'Recovery summary calls an implementation syntax attempt failed, while both retained syntax checks say passed; disposition requires Director clarification or an explicit external receipt correction.']}
(OUT / 'FINAL-PACKAGE-AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'summary': summary, 'failed': [row for row in checks if not row['passed']]}, indent=2))
