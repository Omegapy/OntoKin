"""Independent inert final-package audit; never execute recovered/product code."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib
import json
import os
import stat
import subprocess
import sys
import zipfile

B = Path('/workspace/scratch/816157c5a30b')
O = B / 'recovery_audit'
Z = B / 'packages/OntoKin_C271_P19_Actual_Input_H0_Review_Handoff_2026-11-22.zip'
REV = '89c4f0019697241609822a5a50bee43a3d4b82bf'
TREE = '038bf9cf077813647ecf056f93cc86fc0a9528b5'
BASE = '2f791017c6559bfd47937b32b1862cfe98a81551'
P19 = 'docs/engineering/localized-repair-c271/actual-input-p19/'
checks, inputs, commands = [], [], []
started = datetime.now(timezone.utc).isoformat()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check(name, passed, detail=None):
    checks.append({'check': name, 'passed': bool(passed), 'detail': detail})

def strict(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs)

def read(path, purpose):
    data = path.read_bytes()
    inputs.append({'path': str(path), 'bytes': len(data), 'sha256': sha(data), 'purpose': purpose})
    return data

def git(*args):
    argv = ['git', *args]
    result = subprocess.run(argv, cwd=B/'OntoKin', env={**os.environ, 'GIT_NO_LAZY_FETCH':'1'}, capture_output=True)
    commands.append({'argv': argv, 'returncode': result.returncode, 'stdout_bytes': len(result.stdout), 'stdout_sha256': sha(result.stdout), 'stderr': result.stderr.decode()})
    result.check_returncode()
    return result.stdout

def tree_rows(data):
    result = {}
    for row in data.split(b'\0'):
        if row:
            meta, path = row.split(b'\t', 1)
            mode, kind, blob = meta.decode().split()
            result[path.decode()] = {'mode':mode, 'kind':kind, 'blob':blob}
    return result

def safe(name):
    return bool(name) and str(PurePosixPath(name)) == name and not name.startswith('/') and all(part not in ('', '.', '..') for part in name.split('/')) and not any(c in name for c in ('\\', ':', '\0'))

archive_data = read(Z, 'Complete archive identity; all members independently verified')
identity = {'filename':Z.name, 'bytes':len(archive_data), 'sha256':sha(archive_data)}
del archive_data
meta = strict(read(B/'state/FINAL-PACKAGE.json', 'Root package verification metadata'))
artifacts = strict(read(B/'state/FINAL-ARTIFACTS.json', 'External prompt and archive identities'))['artifacts']
phase = strict(read(B/'state/PHASE.json', 'Current declared final freeze state'))
check('exact_assigned_archive', identity['bytes']==2525653 and identity['sha256']=='a4b41f2768d7782fa8da5b04fb9db1ff9b9db4fe2de5b7d853773a5834212a46')
check('root_package_identity', meta['name']==Z.name and all(meta[k]==identity[k] for k in ('bytes','sha256')) and meta['source_revision']==REV and meta['source_tree']==TREE)

with zipfile.ZipFile(Z) as z:
    names = z.namelist()
    infos = z.infolist()
    payload = {}
    required = ['README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json']
    check('required_root_files', set(required)<=set(names))
    check('safe_relative_paths', all(safe(n) for n in names))
    check('unique_names', len(names)==len(set(names)))
    check('no_casefold_collisions', len(names)==len({n.casefold() for n in names}))
    check('regular_inert_0644_modes', all(i.external_attr>>16==(stat.S_IFREG|0o644) for i in infos))
    check('not_encrypted', all(not i.flag_bits&1 for i in infos))
    for i in infos:
        data = z.read(i.filename)
        payload[i.filename] = {'path':i.filename,'bytes':len(data),'sha256':sha(data),'crc32':i.CRC,'mode':oct(i.external_attr>>16)}
    check('every_crc_valid', True, len(infos))
    manifest = strict(z.read('MANIFEST-SHA256.json'))['files']
    expected = {f['path']:f for f in manifest}
    check('manifest_exact_unique_inventory', len(manifest)==len(expected) and set(expected)==set(names)-{'MANIFEST-SHA256.json'})
    check('every_payload_size_and_sha256', all(all(payload[n][k]==f[k] for k in ('bytes','sha256')) for n,f in expected.items()))
    E = Path(meta['fresh_extraction'])
    check('fresh_extraction_exact_inventory', {str(p.relative_to(E)) for p in E.rglob('*') if p.is_file()}==set(names))
    check('fresh_extraction_all_bytes_and_inert_modes', all((E/n).is_file() and not (E/n).is_symlink() and (E/n).stat().st_mode&0o777==0o644 and (E/n).stat().st_size==f['bytes'] and sha((E/n).read_bytes())==f['sha256'] for n,f in payload.items()))
    cp = strict(z.read('CHECKPOINT.json'))
    source = strict(z.read('SOURCE-MANIFEST.json'))['files']
    recovery = strict(z.read('RECOVERY-FILE-MAP.json'))['files']
    deps = strict(z.read('HISTORICAL-DEPENDENCIES.json'))
    exclusions = strict(z.read('RECOVERY-EXCLUSIONS.json'))
    check('actual_package_counts', len(names)==386 and len(manifest)==385 and len(source)==167 and len(recovery)==207)
    check('checkpoint_source_and_phase_binding', cp['source_revision']==REV and cp['source_tree']==TREE and all(cp[k]==v for k,v in phase.items()))
    check('final_save_correctly_pending', cp['package_kind']=='final' and cp['delivery_state_at_freeze']=='save_pending' and not cp['phase_complete'] and meta['save_confirmed'] is False and cp['phase_table'][-1]['state']=='in_progress')
    check('technical_stopped_early_saved', cp['technical_phase_complete'] is True and cp['early_save_confirmed'] is True)
    check('explicit_worker_dispositions', all(w.get('status') and w.get('disposition') for w in cp['workers']) and cp['active_child_commands']==[] and cp['current_unknown_operations']==[])
    check('parent_pr_issue_and_lease_gates', cp['parent_status']=='blocked' and not cp['parent_complete'] and not cp['main_lease_held'] and cp['pr']=={'number':274,'draft':True,'state':'open','merged':False} and cp['issue']=={'number':273,'state':'open'})
    check('requirements_and_plan_unfinished', cp['requirements']=={'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'} and cp['parent_plan']=={'P01':'done','P02':'in_progress'})
    check('historical_unknowns_preserved', cp['historical_unknowns']==['C270 ancillary broad-driver completion','Global prior-process termination','P13 read-only difflib completion; do not retry'])
    check('source_manifest_exact_snapshot_inventory', len(source)==len({f['archive_path'] for f in source}) and {f['archive_path'] for f in source}=={n for n in names if n.startswith(('repository/','observed-main/'))})
    source_evidence = []
    for rev in sorted({f['revision'] for f in source}):
        rows = [f for f in source if f['revision']==rev]
        tree = tree_rows(git('ls-tree','-rz',rev,'--',*[f['path'] for f in rows]))
        for f in rows:
            data = z.read(f['archive_path'])
            blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            entry = tree.get(f['path'])
            passed = entry and entry['kind']=='blob' and entry['blob']==f['git_blob']==blob and len(data)==f['bytes'] and sha(data)==f['sha256']
            source_evidence.append({**f,'git_entry':entry,'passed':bool(passed)})
    check('all_167_git_revision_path_blob_byte_bindings', all(f['passed'] for f in source_evidence))
    check('published_commit_tree', git('rev-parse',REV+'^{tree}').decode().strip()==TREE)
    check('published_commit_parent', git('rev-parse',REV+'^').decode().strip()==BASE)
    check('observed_main_tree', git('rev-parse',cp['observed_main']['commit']+'^{tree}').decode().strip()==cp['observed_main']['tree'])
    p19_tree = tree_rows(git('ls-tree','-rz',REV,'--',P19))
    check('canonical_P19_revision_inventory_complete', set(p19_tree)=={f['path'] for f in source if f['archive_path'].startswith('repository/'+P19)})
    changed = git('diff-tree','--no-commit-id','--name-only','-r',BASE,REV).decode().splitlines()
    intended = strict(z.read('recovery/session/state/publication/core-attempt002/INTENT.json'))
    canonical_five = {'STATUS.md','docs/workflow/CURRENT.json','docs/workflow/tasks/C271/task.json','docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md'}
    check('published_exact_112_paths_only_allowed_scope', len(changed)==112 and set(changed)=={f['path'] for f in intended['files']} and all(n in canonical_five or n.startswith(P19) for n in changed))
    source_by_path = {f['path']:f for f in source_evidence if f['archive_path'].startswith('repository/')}
    check('all_112_publication_payload_bindings', all(f['path'] in source_by_path and all(source_by_path[f['path']][k]==f[k] for k in ('bytes','sha256','git_blob')) and source_by_path[f['path']]['git_entry']['mode']==f['mode'] for f in intended['files']))
    ref_intent = strict(z.read('recovery/session/state/publication/core-attempt002/REF-INTENT.json'))
    pub = strict(z.read('recovery/session/state/publication/core-attempt002/READBACK.json'))
    check('conditional_publication_evidence', ref_intent['sha']==REV and ref_intent['expected_sha']==BASE and ref_intent['force'] is False and pub==cp['publication'] and pub['commit']==REV and pub['tree']==TREE and pub['parent']==BASE and pub['status']=='confirmed' and pub['exact_changed_files']==112)
    for label in ('workflow','documentation'):
        prefix='recovery/session/state/checks/published-core/'+label+'/'
        result = strict(z.read(prefix+'RESULT.json'))
        check('published_'+label+'_exact_result_and_logs', result['source_revision']==REV and result['worktree_status']=='' and result['returncode']==0 and result['passed'] is True and all(sha(z.read(prefix+stream+'.log'))==result[stream+'_sha256'] for stream in ('stdout','stderr')))
    check('recovery_exact_unique_inventory', len(recovery)==len({f['archive_path'] for f in recovery}) and len(recovery)==len({f['original_path'] for f in recovery}) and {f['archive_path'] for f in recovery}=={n for n in names if n.startswith('recovery/')} )
    check('recovery_hash_base_application_bindings', all(all(payload[f['archive_path']][k]==f[k] for k in ('bytes','sha256')) and f['base_revision']==BASE and 'never overwrite newer' in f['application'] for f in recovery))
    frozen = datetime.fromisoformat(cp['frozen_at_utc']).timestamp()
    mapped = {f['original_path'] for f in recovery}
    unmapped = []
    for root in ('state','reconcile','recovery_audit','ledger_review','operational_review','technical'):
        for p in (B/root).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and str(p) not in mapped:
                unmapped.append({'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'mtime_utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),'after_freeze':p.stat().st_mtime>frozen})
    check('all_existing_prefreeze_owned_files_covered', all(f['after_freeze'] for f in unmapped), unmapped)
    artifact_evidence=[]
    for f in artifacts:
        data=read(Path(f['local_path']), 'Actual external deliverable bytes')
        passed=len(data)==f['bytes'] and sha(data)==f['sha256']
        if f['role']!='handoff_zip':
            passed=passed and data==z.read(f['matching_zip_member'])
        artifact_evidence.append({**f,'independently_verified':passed})
    check('exact_external_archive_and_prompt_bytes', len(artifact_evidence)==3 and all(f['independently_verified'] for f in artifact_evidence))
    prior_dependencies = strict((B/'handoff_p18/HISTORICAL-DEPENDENCIES.json').read_bytes())
    dep_rows=[]
    for f in deps['predecessor']:
        p=B/'incoming/OntoKin'/f['name'];data=p.read_bytes()
        passed=len(data)==f['bytes'] and sha(data)==f['sha256'] and os.getxattr(p,'user.library-file-id').decode()==f['library_file_id'] and os.getxattr(p,'user.library-file-version').decode()==f['version_id']
        dep_rows.append({**f,'actual_materialized_identity_verified':passed})
    check('exact_P18_durable_dependencies', len(dep_rows)==3 and all(f['actual_materialized_identity_verified'] for f in dep_rows))
    check('C262_identity_unchanged', deps['C262']==prior_dependencies['c262'])
    check('correct_online_continuation_boundary', 'not complete offline' in deps['boundary'] and cp['package_type']=='browser-session handoff for online GitHub continuation')
    early=cp['early_recovery'];early_data=(B/'packages'/early['file_name']).read_bytes()
    check('early_archive_receipt_and_review_identity', len(early_data)==early['bytes'] and sha(early_data)==early['sha256'] and early['saved_bytes_readback_equal'] and early['status']=='confirmed' and early['source_revision']==BASE and payload['recovery/session/'+early['review']['path']]['sha256']==early['review']['sha256'])
    check('original_reviewed_builder_bytes_retained', payload['recovery/session/state/build_package-prefinal-review.py']['sha256']=='1f8546eafbcfe36a0802a135fb067c0ac27db6fd474d72e925b4a5ed8ea70808')
    builder=z.read('recovery/session/state/build_package.py').decode()
    check('corrected_builder_revision_inventory', "['git','ls-tree','-r','--name-only',revision,'--','docs/engineering/localized-repair-c271/actual-input-p19']" in builder)
    outcome=strict(z.read('repository/'+P19+'PHASE-OUTCOME.json'))
    reviewer=strict(z.read('repository/'+cp['technical_review']['path']))
    check('technical_review_exact_identity_and_scope', payload['repository/'+cp['technical_review']['path']]['sha256']==cp['technical_review']['sha256'] and reviewer['mandatory_findings']==[] and reviewer['independent_artifact_checks']=={'passed':41,'failed':0,'not_product_tests':True} and not reviewer['h0_accepted'] and not reviewer['h1_approved'])
    review_bindings=[]
    for key,f in reviewer['evidence'].items():
        member='recovery/session/'+f['path']
        passed=member in payload and all(payload[member][k]==f[k] for k in ('bytes','sha256'))
        review_bindings.append({'role':key,**f,'archive_path':member,'passed':passed})
    check('all_operational_review_evidence_bindings', all(f['passed'] for f in review_bindings))
    check('observed_source_vs_published_source_distinguished', outcome['source_revision']==BASE and outcome['source_tree']==cp['starting_tree'] and outcome['source_revision']!=REV and outcome['production_source']['sha256']==payload['repository/prototypes/static_tray_v01/current_host_inspection_v01.py']['sha256'])
    check('no_H0_H1_or_host_qualification_claim', outcome['technical_phase_stopped'] and all(outcome[k] is False for k in ('h0_accepted','operational_plan_created','operational_policy_admitted','h1_approved','actual_host_qualified','parent_complete')))
    blocker=outcome['first_blocker']
    check('exact_input_mismatch_preserved', blocker==cp['technical_stop'] and blocker['code']=='PACKAGE_METADATA_PIN_MISMATCH' and blocker['details']['name']=='rpds-py' and blocker['details']['expected_version']=='2026.5.1' and blocker['details']['observed_versions']==['2026.6.3'])
    raw_metadata=z.read('recovery/session/technical/attempt001/METADATA-rpds-py.txt')
    lock=z.read('repository/tools/native-reader-verification-linux-cp312.lock')
    check('retained_package_metadata_and_lock_support_blocker', sha(raw_metadata)==blocker['details']['metadata_sha256'] and b'Name: rpds-py' in raw_metadata and b'Version: 2026.6.3' in raw_metadata and b'rpds-py==2026.5.1' in lock)
    old_bindings=tree_rows(git('ls-tree','-rz',BASE,'--','tools/native-reader-verification-linux-cp312.lock','prototypes/static_tray_v01/current_host_inspection_v01.py'))
    check('production_and_lock_unchanged', all(old_bindings[path]['blob']==source_by_path[path]['git_blob'] for path in old_bindings) and len(old_bindings)==2)
    task=strict(z.read('repository/docs/workflow/tasks/C271/task.json'))
    check('canonical_parent_task_still_blocked', task['status']=='blocked' and {x['id']:x['status'] for x in task['requirements']}==cp['requirements'] and {x['id']:x['status'] for x in task['plan']}==cp['parent_plan'])
    check('documentary_review_exact_identity', payload['repository/'+cp['documentary_review']['path']]['sha256']==cp['documentary_review']['sha256'])
    preservation=strict(z.read('recovery/session/state/PRESERVATION.json'))
    check('preservation_record_bound_45_checks', preservation['passed'] and len(preservation['checks'])==45 and all(c['passed'] for c in preservation['checks']) and not preservation['production_test_lock_contract_changes'] and set(preservation['changed_existing'])==canonical_five)
    ws=strict(z.read('recovery/session/ledger_review/WHITESPACE-DISPOSITION.json'))
    full=strict(z.read('recovery/session/state/checks/full-staged-whitespace/RESULT.json'))
    authored=strict(z.read('recovery/session/state/checks/authored-staged-whitespace/RESULT.json'))
    check('full_staged_failure_preserved', full['returncode']==2 and full['passed'] is False and ws['full_staged_check']['passed'] is False and ws['full_staged_check']['diagnostic_count']==12 and ws['full_staged_check']['affected_paths']==8 and all(payload['recovery/session/'+ws['full_staged_check'][key+'_path']]['sha256']==ws['full_staged_check'][key+'_sha256'] for key in ('result','stdout','stderr')))
    ws_bindings=[]
    for f in ws['findings']:
        target='repository/'+f['path'];original='recovery/session/'+f['original']
        passed=all(payload[n][k]==f[k] for n in (target,original) for k in ('bytes','sha256'))
        ws_bindings.append({'path':f['path'],'original':f['original'],'passed':passed})
    check('all_eight_whitespace_originals_preserved', len(ws_bindings)==8 and all(f['passed'] for f in ws_bindings))
    check('separate_authored_whitespace_pass_retained', authored.get('returncode')==0 and authored.get('passed') is True)
    handoff=z.read('HANDOFF.md').decode();next_text=z.read('NEXT-TASK.md').decode()
    check('no_whole_stage_whitespace_pass_claim', 'There is no whole-stage whitespace pass claim.' in handoff and 'failed return code 2' in cp['documentary_checks']['full_staged_whitespace'])
    check('delivery_only_next_action_and_fresh_phase_boundary', 'save and read back ZIP plus matching prompts' in cp['next_action'] and 'No new technical phase' in cp['next_action'] and 'complete only the missing archive/save/receipt gates, then stop' in next_text and 'review a bounded preparation plan for a separate verification environment' in next_text and 'Review exact inputs, destinations, package provenance and installation authority before any preparation' in next_text)
    failure_paths=['recovery/session/technical/candidate001/observe_inputs.py','recovery/session/technical/candidate002/observe_inputs.py','recovery/session/operational_review/PREEXEC-REVIEW.json','recovery/session/operational_review/PREEXEC-REVIEW-002.json','recovery/session/operational_review/PREEXEC-REVIEW-WRITE-RACE.json','recovery/session/state/documentary-candidate001.zip','recovery/session/state/checks/prepublication/documentation/RESULT.json','recovery/session/state/checks/full-staged-whitespace/RESULT.json','recovery/session/state/publication/core/INTENT.json','recovery/session/state/OPERATIONS.json','recovery/session/recovery_audit/EARLY-AUDIT-ATTEMPT001.json']
    check('declared_rejected_failed_and_superseded_evidence_retained', all(n in payload for n in failure_paths))
    for n in required+['SOURCE-MANIFEST.json','RECOVERY-FILE-MAP.json','RECOVERY-EXCLUSIONS.json']:
        inputs.append({'path':str(Z)+'!/'+n,**{k:payload[n][k] for k in ('bytes','sha256')},'purpose':'Complete root narrative or structured metadata read and verification'})

failures=[c for c in checks if not c['passed']]
report={
 'schema':'ontokin.c271.p19-final-independent-package-review/1',
 'auditor':'/root/recovery_audit','started_at_utc':started,'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),
 'verdict':'accepted' if not failures else 'rejected','archive':identity,'source_revision':REV,'source_tree':TREE,
 'checks':checks,'passed_groups':sum(c['passed'] for c in checks),'mandatory_findings':failures,
 'counts':{'members':len(names),'manifest_payloads':len(manifest),'source_snapshots':len(source),'recovery_files':len(recovery),'published_changed_paths':len(changed)},
 'source_bindings':source_evidence,'inventory':list(payload.values()),'recovery_files':recovery,
 'external_artifacts':artifact_evidence,'historical_dependencies':dep_rows,'exclusions':exclusions,
 'operational_review_evidence_bindings':review_bindings,'whitespace_original_bindings':ws_bindings,
 'postfreeze_files_not_in_archive':unmapped,'readset':inputs,'git_commands':commands,
 'postfreeze_recovery_requirements':[
  'Keep the frozen ZIP unchanged. Bind exact archive name/bytes/SHA-256/source commit/tree and both byte-identical prompt identities to actual Library IDs, versions and readbacks.',
  'Publish or preserve the exact final audit JSON/Markdown and this auditor script. Each unique later delivery file must have a pinned public Git path and byte hash or be included in a safe, hashed compact recovery delta. Reproducible duplicate extracts/readbacks may be explicitly excluded.',
  'Preserve any failed/uncertain save or publication intent and readback before retry; identify unresolved operations explicitly. Do not silently drop unique scratch-only delivery scripts/results.',
  'Bind the actual receipt publication commit/tree/parent, relevant documentary checks and open parent/PR/issue state; retain the input mismatch and unaccepted H0.',
  'An immutable saved receipt cannot observe its own later save. Confirm its actual saved identity/bytes/version externally, such as matching live PR274/issue273 terminal markers; supersede only matching delivery-pending fields.',
  'Save receipt and any required compact recovery delta, verify actual returned bytes, reconcile terminal state, then stop. No further technical phase or recursive predecessor archive is required.'
 ],
 'limits':['This audit does not confirm final Library saving; it remains the next gate.','Existing early saved-byte evidence is bound to the verified early archive; no new Library operation was performed.','Root-created fresh extraction independently checked; no recovered or product code executed.','No current-host observation, test rerun, Git mutation, publication or merge.','The 41 operational checks are retained-artifact review checks; they are not product tests or H0 acceptance.'],
 'execution':{'python':sys.version,'executable':sys.executable,'argv':sys.argv,'script_sha256':sha(Path(__file__).read_bytes())}
}
(O/'FINAL-REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'verdict':report['verdict'],'archive':identity,'passed_groups':report['passed_groups'],'mandatory_findings':failures,'counts':report['counts'],'postfreeze_paths':[f['path'] for f in unmapped]},indent=2))
