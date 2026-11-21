#!/usr/bin/env python3
"""Independent frozen P03 handoff audit; no product execution or source edits."""
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import stat
import subprocess
import zipfile

BASE = Path('/workspace/scratch/7010345bc259')
OUT = BASE / 'review/package'
FRESH = OUT / 'fresh-extraction'
REPO = BASE / 'OntoKin'
ZIP = BASE / 'packages/OntoKin_C271_P03_Validation_Recovery_Handoff_2026-11-20.zip'
SOURCE = '633c5097b2c5b870a13baa33a095a91eaa241eea'
TREE = '7f8eb385de71c6dd202389ad09113b779a6dc4b8'
CODE = 'fea1aa6fb3712c5283dde197295b2d3cbf925d36'
MAIN = 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
PREFIX = 'repository/docs/engineering/localized-repair-c271/validation-recovery-20261120/'
EXPECTED = {'bytes':22484405,'sha256':'09a56ab40d5916d72abc5d4d165aa6a07ea981f96e651046b8e298dbd83aadb4'}
rows = []
git_reads = []


def identity(data):
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def check(predicate, ok, **details):
    rows.append({'check':predicate,'passed':bool(ok),**details})


def git(*args):
    argv = ['git','--no-optional-locks','-C',str(REPO),*args]
    result = subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    git_reads.append({'argv':argv,'returncode':result.returncode,'stdout_identity':identity(result.stdout),'stderr':result.stderr.decode()})
    if result.returncode:
        raise RuntimeError(git_reads[-1])
    return result.stdout


def safe(name):
    return bool(name) and not name.startswith('/') and '\\' not in name and not re.match(r'^[A-Za-z]:',name) and all(p not in ('','..','.') for p in name.split('/'))


OUT.mkdir(parents=True,exist_ok=True)
if FRESH.exists():
    raise RuntimeError('Fresh extraction target exists; original audit evidence will not be overwritten')
archive_raw = ZIP.read_bytes()
check('archive_matches_assigned_identity',identity(archive_raw)==EXPECTED)
builder = json.loads((BASE/'packages/FINAL-PACKAGE-VERIFICATION.json').read_bytes())
ids = json.loads((BASE/'packages/FINAL-IDENTITIES.json').read_bytes())
check('builder_and_identity_records_agree',builder['archive']==ids['archive'] and builder['prompts']==ids['prompts']
      and {k:ids['archive'][k] for k in ('bytes','sha256')}==EXPECTED)
with zipfile.ZipFile(BytesIO(archive_raw)) as z:
    infos=z.infolist(); names=[i.filename for i in infos]
    invalid=[i.filename for i in infos if not safe(i.filename) or i.is_dir() or stat.S_IFMT(i.external_attr>>16) not in (0,stat.S_IFREG)]
    check('safe_regular_relative_paths',not invalid,invalid=invalid)
    check('unique_member_names',len(names)==len(set(names)))
    bad=z.testzip(); check('zip_crc',bad is None,first_bad_member=bad)
    if invalid or len(names)!=len(set(names)) or bad is not None:
        raise RuntimeError('Unsafe or corrupt archive; extraction refused')
    manifest=json.loads(z.read('MANIFEST-SHA256.json'))['files']
    expected_paths=[e['path'] for e in manifest]
    check('exact_manifest_inventory',len(manifest)==134 and len(names)==135 and len(expected_paths)==len(set(expected_paths))
          and set(names)==set(expected_paths)|{'MANIFEST-SHA256.json'})
    required=['README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md',
              'PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json']
    check('all_required_root_files',all(n in names for n in required))
    FRESH.mkdir()
    for info in infos:
        path=FRESH/info.filename; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(z.read(info))
    for entry in manifest:
        data=(FRESH/entry['path']).read_bytes()
        check('fresh_payload_size_and_hash',identity(data)=={k:entry[k] for k in ('bytes','sha256')},path=entry['path'])

def data(path):
    return (FRESH/path).read_bytes()


def document(path):
    return json.loads(data(path))


snapshots=document('metadata/SNAPSHOT-SOURCES.json')['files']
session=document('metadata/SESSION-AND-RECOVERY-SOURCES.json')
trees={}
for revision in {e['revision'] for e in snapshots}|{SOURCE,MAIN,CODE}:
    tree={}
    for raw in git('ls-tree','-rz','--full-tree',revision).split(b'\0'):
        if raw:
            head,path=raw.split(b'\t',1); mode,kind,oid=head.decode().split(' ')
            tree[path.decode()]={'mode':mode,'kind':kind,'oid':oid}
    trees[revision]=tree
for entry in snapshots:
    raw=data(entry['package_path'])
    computed=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    check('snapshot_identity_and_tree_binding',identity(raw)=={k:entry[k] for k in ('bytes','sha256')}
          and computed==entry['git_blob'] and trees[entry['revision']].get(entry['repository_path'])==
          {'mode':entry['git_mode'],'kind':'blob','oid':entry['git_blob']},path=entry['package_path'],revision=entry['revision'])
    check('snapshot_exact_git_object_bytes',raw==git('cat-file','blob',entry['git_blob']),path=entry['package_path'])
required_snapshots=['CHATGPT-START-HERE.md','AGENTS.md','GOAL.md','STATUS.md','ROLE.md','docs/workflow/registry.json',
                    'docs/workflow/CURRENT.json','docs/workflow/PROTOCOL.md','docs/workflow/HANDOFF.md','docs/workflow/BROWSER-PROMPTS.md',
                    'docs/workflow/tasks/C271/task.json','docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md',
                    '.agents/skills/ontokin-session/SKILL.md','.agents/skills/ontokin-delivery/SKILL.md','.agents/skills/ontokin-learning/SKILL.md']
check('required_repository_snapshots_present',all('repository/'+p in names for p in required_snapshots))
check('declared_snapshot_count',len(snapshots)==107==builder['git_snapshots_compared'])
externals=document('metadata/EXTERNAL-EVIDENCE-LINKS.json')['files']
bad_external=[]
for row in externals:
    value=trees[row['revision']].get(row['repository_path'])
    expected_url='https://github.com/Omegapy/OntoKin/blob/'+row['revision']+'/'+row['repository_path']
    if not value or value['oid']!=row['git_blob'] or row['url']!=expected_url:
        bad_external.append(row['repository_path'])
check('pinned_external_paths_exist_in_declared_git_tree',not bad_external,paths=len(externals),failures=bad_external)

nested_cache={}
def resolve(location):
    parts=location.split('!/')
    raw=data(parts[0])
    prefix=parts[0]
    for member in parts[1:]:
        if prefix not in nested_cache:
            nested_cache[prefix]=zipfile.ZipFile(BytesIO(raw))
        raw=nested_cache[prefix].read(member)
        prefix+='!/'+member
    return raw


for entry in session['files']:
    raw=resolve(entry['included_as'])
    local=Path(entry['source_path'])
    if not local.is_absolute(): local=BASE/local
    check('session_alias_resolves_exact_preserved_bytes',identity(raw)=={k:entry[k] for k in ('bytes','sha256')},source=entry['source_path'],included_as=entry['included_as'])
    check('session_bytes_equal_available_original',local.is_file() and local.read_bytes()==raw,source=entry['source_path'])
check('declared_session_preservation_count',len(session['files'])==119==builder['session_records_preserved_or_aliased'])
raw_map=document('metadata/RAW-ARCHIVE-MEMBERS.json'); raw_bytes=data(raw_map['archive'])
check('raw_evidence_exact_identity',identity(raw_bytes)=={k:raw_map[k] for k in ('bytes','sha256')})
with zipfile.ZipFile(BytesIO(raw_bytes)) as rawzip:
    raw_names=rawzip.namelist(); raw_manifest=json.loads(rawzip.read('MANIFEST-SHA256.json'))['payloads']
    check('raw_archive_crc_safe_exact_inventory',rawzip.testzip() is None and len(raw_names)==109 and len(raw_manifest)==108
          and len(raw_names)==len(set(raw_names)) and all(safe(n) for n in raw_names)
          and set(raw_names)=={e['path'] for e in raw_manifest}|{'MANIFEST-SHA256.json'})
    check('raw_archive_member_map_exact',raw_map['files']==raw_manifest)
    bad_raw=[e['path'] for e in raw_manifest if identity(rawzip.read(e['path']))!={k:e[k] for k in ('bytes','sha256')}]
    check('all_raw_evidence_payloads_verified',not bad_raw,payloads=108,failures=bad_raw)
    preserved=['preparation/copy-repair/red/stderr.log','validation/readback-preflight.json','review/final/FINAL-ACCEPTANCE.json',
               'review/final/REPORT.md','review/final/ATTEMPT-01.log','review/final/REVIEW-ATTEMPTS.json','environment/NODE-DOWNLOAD.json']
    check('current_failures_and_reviews_preserved',all(p in raw_names for p in preserved))

history=document('HISTORICAL-DEPENDENCIES.json'); prior=history['incoming_c271_p02']; prior_bytes=data(prior['included_path'])
check('incoming_P02_unchanged_and_single',identity(prior_bytes)=={k:prior[k] for k in ('bytes','sha256')}
      and prior_bytes==(BASE/'incoming'/prior['file_name']).read_bytes()
      and sum(n.endswith(prior['file_name']) for n in names)==1)
with zipfile.ZipFile(BytesIO(prior_bytes)) as old:
    p01=history['incoming_c271_p01']; p01_bytes=old.read('preserved-inputs/'+p01['file_name'])
    check('historical_P01_nested_zip_preserved',identity(p01_bytes)=={k:p01[k] for k in ('bytes','sha256')})
    p02_raw=old.read('repository/docs/engineering/localized-repair-c271/finalization-20261120/verification/RAW-EVIDENCE.zip')
    check('original_P02_failed_raw_archive_preserved',identity(p02_raw)=={'bytes':4965080,'sha256':'c4c973d40c4f6571def93b257877de69568bcd5fdca43bcfed92ff6acfc61e20'})
for index,entry in enumerate(ids['prompts'],1):
    standalone=Path(entry['path']).read_bytes(); archived=data(f'PROMPT-{index}-'+('CONTINUE' if index==1 else 'RECOVER')+'.md')
    check('standalone_prompt_equals_archive_and_declared_identity',standalone==archived and identity(standalone)=={k:entry[k] for k in ('bytes','sha256')},prompt=index)

checkpoint=document('CHECKPOINT.json'); observation=document('metadata/FINAL-OBSERVATION.json')
check('frozen_source_identity',checkpoint['repository_snapshot']['sha']==SOURCE and checkpoint['repository_snapshot']['tree']==TREE
      and git('rev-parse',SOURCE+'^{tree}').decode().strip()==TREE)
check('execution_main_identity_distinction',checkpoint['executed_source']['sha']==CODE and checkpoint['observed_main']['sha']==MAIN
      and checkpoint['executed_source']['tree']==git('rev-parse',CODE+'^{tree}').decode().strip()
      and checkpoint['observed_main']['tree']==git('rev-parse',MAIN+'^{tree}').decode().strip())
check('observation_checkpoint_agreement',observation['branch']['sha']==SOURCE and observation['branch']['tree']==TREE
      and observation['main']['sha']==MAIN and observation['main']['tree']==checkpoint['observed_main']['tree']
      and observation['observed_at_utc']==checkpoint['observed_main']['observed_at_utc'])
task=document('repository/docs/workflow/tasks/C271/task.json'); outcome=document(PREFIX+'PHASE-OUTCOME.json'); acceptance=document(PREFIX+'FINAL-ACCEPTANCE.json')
expected_requirements={'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'}
check('parent_requirements_remain_blocked',checkpoint['parent_status']==task['status']=='blocked'
      and checkpoint['requirements']==outcome['requirements']==expected_requirements
      and {r['id']:r['status'] for r in task['requirements']}==expected_requirements)
check('routine_nonexecution_not_waived',checkpoint['verification']['complete_required_routine']['status']=='not_run'
      and outcome['required_routine']['status']=='not_run' and outcome['p02_failures']['waived'] is False
      and checkpoint['verification']['r03_accepted'] is False and acceptance['R03_accepted'] is False)
check('no_integration_or_parent_closure_claim',checkpoint['ownership']['integration_performed'] is False
      and checkpoint['ownership']['main_lease_held'] is False and acceptance['integration_approved'] is False
      and acceptance['parent_closure_approved'] is False and checkpoint['pull_request']['draft'] is True
      and checkpoint['pull_request']['merged'] is False and checkpoint['scope_issue']['state']=='open')
check('future_save_receipt_is_external',checkpoint['delivery']['status']=='save_pending' and checkpoint['delivery']['partial'] is True
      and 'repository/'+checkpoint['delivery']['receipt_path'] not in names)
runtime=history['runtime_and_validation']
check('exact_runtime_blocker_and_exclusions_honest',runtime['expected_node']=={'bytes':126939688,'sha256':'61ab14cd750fc24d5db53490ec5fc40f756e4b6e136b78cf7004265471d9bd1d'}
      and runtime['official_distribution_observed']['matches_historical_pin'] is False
      and runtime['official_archive_and_executable_embedded'] is False and runtime['installed_virtual_environment_embedded'] is False)
check('historical_C262_boundary_preserved',history['c262']['bytes']==532260846
      and history['c262']['sha256']=='b8af544f730a4d1f741d47b56eb3fcf76147ed392a9ebb020f3d966f2f305c90'
      and 'no full reconstruction' in history['c262']['current_search_scope'])
source_map={e['source_path']:e for e in session['files']}
operations=json.loads(resolve(source_map['session/FINAL-OPERATIONS.json']['included_as']))
check('current_operations_resolved_historical_unknowns_retained',operations['unresolved_remote_mutations']==[]
      and operations['heads']=={'refs/heads/main':MAIN,'refs/heads/work/c271-missing-import-digest-control':SOURCE}
      and checkpoint['current_operations']['unknown_current_session_operations']==[] and checkpoint['historical_unknowns'])
for label in ('PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md'):
    text=data(label).decode()
    check('prompt_preserves_delivery_reconciliation_and_phase_boundary','reconcile delivery first' in text and 'early recovery ZIP save' in text
          and 'Do not begin a second phase' in text and '100000 operations / 30000 ms' in text
          and 'No integration or main lease occurred' in text,label=label)
check('recovery_prompt_handles_delivery_only','perform delivery recovery only' in data('PROMPT-2-RECOVER.md').decode())
check('old_exclusion_ambiguity_clarified','includes commands, logs and reviews' in data('RECOVERY-STATUS.md').decode()
      and 'not an executable full checkout' in data('README-START-HERE.md').decode())
check('frozen_archive_unmodified_by_audit',identity(ZIP.read_bytes())==EXPECTED)
failed=[r for r in rows if not r['passed']]
audit={'schema':'ontokin.c271.p03-independent-package-audit/1','reviewer':'/root/intake_review',
       'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'verdict':'eligible_for_partial_save' if not failed else 'blocked',
       'archive':{'path':str(ZIP),**EXPECTED},'prompts':ids['prompts'],'source':{'commit':SOURCE,'tree':TREE},
       'members':135,'payloads':134,'git_snapshots':len(snapshots),'session_aliases':len(session['files']),
       'raw_payloads':108,'check_count':len(rows),'failed_count':len(failed),'checks':rows,
       'semantic_review':{'required_root_documents_read_in_full':required,'one_phase_and_early_recovery':True,
                          'runtime_blocker_retained':True,'historical_failures_retained':True,'honest_partial_delivery':True,
                          'receipt_only_save_boundary':True,'prior_exclusion_wording_clarified':True},
       'R03_accepted':False,'integration_approved':False,'parent_closure_approved':False,'saved_delivery_confirmed':False,
       'fresh_extraction':str(FRESH),'limits':['Archive and source evidence only; no product tests or remote queries.',
                                             'No full offline restoration claim.','Actual Library save and later receipt are separate gates.']}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
(OUT/'GIT-READS.json').write_text(json.dumps(git_reads,indent=2)+'\n')
print(json.dumps({k:audit[k] for k in ['verdict','archive','check_count','failed_count','payloads','git_snapshots','session_aliases']}))
