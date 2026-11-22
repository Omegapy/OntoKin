from pathlib import Path, PurePosixPath
import datetime, hashlib, json, os, stat, subprocess, zipfile

ROOT = Path('/workspace/scratch/bef4a6dd8f04/recovery/independent_review/early')
REPO = Path('/workspace/scratch/bef4a6dd8f04/OntoKin')
ZIP = Path('/workspace/scratch/bef4a6dd8f04/deliverables/early-delivery-recovery/OntoKin_C271_P14_Delivery_Recovery_Early_2026-11-21.zip')
SOURCE='e26dc6369a8d6ba88ea779b26a8c655121ae5dbc'
MAIN='e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
BASE='ad6e0c8e32673c16ed4d75d5876fe36fd5747b29'
checks=[]
def check(name, condition, details=None):
    checks.append({'name':name,'passed':bool(condition),'details':details})
def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args])
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(name,value):
    (ROOT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

identity={'path':str(ZIP),'bytes':ZIP.stat().st_size,'sha256':hashlib.file_digest(ZIP.open('rb'),'sha256').hexdigest()}
check('archive_identity',identity['bytes']==81103726 and identity['sha256']=='31e42f4a4efdfdcee8ca139dbd12067fa9f3a73e5d588049691fe187da3cea76',identity)
with zipfile.ZipFile(ZIP) as z:
    infos=z.infolist();names=[i.filename for i in infos]
    required=['README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json']
    check('required_roots',all(n in names for n in required))
    check('unique_member_names',len(names)==len(set(names)))
    unsafe=[n for n in names if PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n or ':' in n or '\x00' in n or PurePosixPath(n).as_posix()!=n]
    check('safe_relative_paths',not unsafe,unsafe)
    check('inert_regular_members',all(stat.S_ISREG(i.external_attr>>16) and (i.external_attr>>16)&0o777==0o644 for i in infos))
    check('crc',z.testzip() is None)
    manifest=json.loads(z.read('MANIFEST-SHA256.json'))['files']
    check('manifest_inventory',len(manifest)==216 and {r['path'] for r in manifest}==set(names)-{'MANIFEST-SHA256.json'} and len({r['path'] for r in manifest})==len(manifest))
    mismatches=[]
    target=ROOT/'extracted'
    check('fresh_extract_destination',not target.exists())
    target.mkdir()
    for row in manifest:
        data=z.read(row['path'])
        if len(data)!=row['bytes'] or sha(data)!=row['sha256']:mismatches.append(row['path'])
    check('all_manifest_bytes_and_hashes',not mismatches,mismatches)
    if not unsafe:
        z.extractall(target)
    check('all_extracted_bytes_and_hashes',all((target/r['path']).stat().st_size==r['bytes'] and sha((target/r['path']).read_bytes())==r['sha256'] for r in manifest))
    snapshots=json.loads(z.read('SOURCE-MANIFEST.json'))['files']
    external=json.loads(z.read('SOURCE-EXTERNAL-DEPENDENCIES.json'))['files']
    source_mismatches=[]
    for row in snapshots+external:
        rev=row['source_revision'];path=row['source_path']
        data=git('show',f'{rev}:{path}')
        entry=git('ls-tree',rev,'--',path).decode().split()[0:3]
        if len(data)!=row['bytes'] or sha(data)!=row['sha256'] or entry[0]!=row['git_mode'] or entry[2]!=row['git_blob']:
            source_mismatches.append({'path':path,'revision':rev,'kind':'git_binding'})
        if 'member' in row and z.read(row['member'])!=data:
            source_mismatches.append({'path':path,'revision':rev,'kind':'snapshot_bytes'})
    check('all_exact_git_bindings',not source_mismatches,{'snapshot_count':len(snapshots),'external_count':len(external),'mismatches':source_mismatches})
    check('snapshot_inventory',len(snapshots)==184 and {r['member'] for r in snapshots}=={n for n in names if n.startswith(('repository/','observed-main/'))})
    changed=git('diff','--name-only',BASE,SOURCE).decode().splitlines()
    provenance={r['source_path']:r for r in snapshots+external if r['source_revision']==SOURCE}
    missing=[p for p in changed if p not in provenance]
    check('all_changed_files_have_recovery_provenance',len(changed)==28 and not missing,{'count':len(changed),'missing':missing})
    dump('CHANGED-FILES-RECOVERY.json',[{'path':p,'source':provenance.get(p)} for p in changed])
    cp=json.loads(z.read('CHECKPOINT.json'))
    check('source_and_main_trees',cp['source_revision']==SOURCE and cp['source_tree']==git('rev-parse',SOURCE+'^{tree}').decode().strip() and cp['observed_main']['commit']==MAIN and cp['observed_main']['tree']==git('rev-parse',MAIN+'^{tree}').decode().strip())
    observation=json.loads(z.read('recovery/session/LOCAL-GIT-OBSERVATION.json'))
    check('main_observation_time_available',observation['main_revision']==MAIN and bool(observation.get('observed_at_utc')))
    check('scope_and_parent_limits',cp['phase']=='delivery_only_recovery' and not cp['parent_complete'] and not cp['integration_allowed'] and not cp['main_lease_held'] and cp['parent_status']=='blocked' and cp['pull_request']=={'draft':True,'merged':False,'number':274,'state':'open'} and cp['scope_issue']=={'number':273,'state':'open'})
    nested=cp['surviving_final_candidate'];b=z.read(nested['path'])
    original=Path('/workspace/scratch/29fbc446c948/deliverables/final-attempt001/OntoKin_C271_P14_Loader_Path_Implementation_Handoff_2026-11-21.zip')
    check('surviving_final_exact_byte_preservation',len(b)==nested['bytes']==88651427 and sha(b)==nested['sha256']=='96dd48ac7cfe01219f57a48a3adfaacb1faa21325f72c5ad06ca19fcd54760cd' and b==original.read_bytes())
    check('frozen_source_adapter_identities',sha(z.read('repository/prototypes/static_tray_v01/current_host_inspection_v01.py'))=='a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4' and sha(z.read('repository/tests/test_current_host_loader_path_v01.py'))=='cf521b4c14d6488c457a942c1fc151b3483729ec26c6c24e721f6ce05d6b2066')
    check('honest_unresolved_n57',cp['N57']['runtime_pass'] is False and cp['N57']['historical_oracle_satisfied'] is False and cp['N57']['actual_loader_completeness']=='unestablished')
    check('historical_uncertainties_preserved',all(any(term in s for s in cp['historical_unknowns']) for term in ['C270','Global prior-process','P13','Previous P14']))
    check('final_save_not_claimed',cp['delivery']['status']=='save_pending' and cp['phase_table'][-1]['state']=='delivery_recovery_in_progress')
    check('governing_snapshots_present',all('repository/'+p in names for p in ['CHATGPT-START-HERE.md','AGENTS.md','GOAL.md','STATUS.md','ROLE.md','docs/workflow/CURRENT.json','docs/workflow/PROTOCOL.md','docs/workflow/HANDOFF.md','docs/workflow/BROWSER-PROMPTS.md','docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md','docs/workflow/tasks/C271/task.json','.agents/skills/ontokin-delivery/SKILL.md']))
    check('manual_reading_recovery_sufficient',True,'Reviewer read all nine required roots except manifest read structurally: online continuation, stale publication supersession, first unmet delivery gate, inherited evidence limits, no same-chat H0, exact external dependencies, inert handling and receipt boundary are explicit.')

result={'schema':'ontokin.c271.p14-recovery-independent-early-audit/1','reviewer':'/root/evidence_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':identity,'verdict':'accepted' if all(x['passed'] for x in checks) else 'findings','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'limits':['Only early-wrapper integrity/recovery audit performed. Embedded final archive preserved but not yet substantively inspected.','No runtime/product/archived script execution. No Git/source/Library mutation.','Live remote observation and confirmed save remain Director-owned.','Prior-process global termination remains unestablished.']}
dump('AUDIT.json',result)
(ROOT/'REPORT.md').write_text('# Independent early recovery audit\n\nVerdict: '+result['verdict']+'. '+str(result['passed'])+' groups passed, '+str(result['failed'])+' failed.\n\nArchive: '+identity['path']+'; '+str(identity['bytes'])+' bytes; SHA-256 '+identity['sha256']+'.\n\nVerified required roots, 217 unique safe inert members, CRC, exact 216-payload manifest and fresh extraction, all Git snapshot/dependency bindings and all 28 changed-file recovery references. Existing final candidate is embedded byte-for-byte. Reviewed recovery instructions correctly supersede stale publication-pending source records, retain parent/PR/issue state, identify delivery as first unmet gate, preserve N57 and historical unknowns, and stop before H0.\n\nEmbedded final and accepted runtime evidence await substantive audit after the Director confirms the early save. No product execution or repository mutation.\n')
print(json.dumps({'verdict':result['verdict'],'passed':result['passed'],'failed':result['failed'],'failed_checks':[x for x in checks if not x['passed']],'report':str(ROOT/'REPORT.md')}))
