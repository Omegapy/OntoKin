#!/usr/bin/env python3
"""Read-only C260 integration binding review; no broad product test execution."""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys
ROOT=Path('/workspace/scratch/a827454f4cb7')
REPO=ROOT/'OntoKin'; OUT=ROOT/'evidence/integration-review'
REV='87d7cdab441222cda75958e61fd9da369ec8c5a3'
TREE='0e9b91f56e184032adf00cae97abda71201cc9dd'
BASE='de69dfd97cae264ed050bd9c1b0813cd643b6ac7'
PREFIX='docs/engineering/localized-repair-c260/'
checks=[]
def git(*args,bytes_result=False):
 r=subprocess.run(['git','-C',str(REPO),*args],capture_output=True,check=True)
 return r.stdout if bytes_result else r.stdout.decode().strip()
def check(name,value,details=None):
 checks.append({'name':name,'passed':bool(value),**({'details':details} if details is not None else {})})
def digest(data):return hashlib.sha256(data).hexdigest()
def bytes_at(ref,path):return git('show',ref+':'+path,bytes_result=True)
def load(path):return json.loads((REPO/path).read_text())
def source_match(path,data):
 return (REPO/path).read_bytes()==data and bytes_at(REV,path)==data
check('candidate_HEAD',git('rev-parse','HEAD')==REV)
check('candidate_tree',git('rev-parse','HEAD^{tree}')==TREE)
check('candidate_clean',git('status','--porcelain=v1','--untracked-files=all')=='')
check('lease_base_is_ancestor',subprocess.run(['git','-C',str(REPO),'merge-base','--is-ancestor',BASE,REV]).returncode==0)
changes=[line.split('\t') for line in git('diff','--name-status',BASE,REV).splitlines()]
shared={'AGENTS.md','GOAL.md','STATUS.md','docs/README.md'}
check('scope_all_changes_allowed',all(len(x)==2 and (x[1] in shared or x[1].startswith(PREFIX)) for x in changes),{'count':len(changes)})
check('exact_four_shared_files',set(x[1] for x in changes if not x[1].startswith(PREFIX))==shared)
check('all_scope_files_new',all(x[0]=='A' for x in changes if x[1].startswith(PREFIX)))
check('no_runtime_workflow_prior_source_change',not any(x[1].startswith(('ontokin/','tests/','.github/','tools/','examples/')) for x in changes))
binding=load(PREFIX+'evidence/review/REVIEW-BINDING.json')
author=load(PREFIX+'evidence/author/FILE-INTEGRITY.json')
check('contract_only_approval',binding['decision']=='APPROVE_CONTRACT_ONLY' and not binding['implementationPresent'] and not binding['futureControlPlanExecuted'])
check('seven_author_and_review_bindings_identical',len(binding['files'])==7 and binding['files']==author['files'])
for row in binding['files']:
 data=(REPO/row['path']).read_bytes()
 check('approved_file:'+row['path'],len(data)==row['bytes'] and digest(data)==row['sha256'] and bytes_at(REV,row['path'])==data and bytes_at('6a178c9292ac8d2be739c52e7af0f21995210c6b',row['path'])==data)
inputs=load(PREFIX+'INPUTS.json')
check('twelve_input_bindings',len(inputs['files'])==12)
for row in inputs['files']:
 data=(REPO/row['path']).read_bytes()
 check('input_unchanged:'+row['path'],len(data)==row['bytes'] and digest(data)==row['sha256'] and bytes_at(inputs['sourceRevision'],row['path'])==data and bytes_at(BASE,row['path'])==data and bytes_at(REV,row['path'])==data)
tracked=set(git('ls-files').splitlines())
for kind in ('author','review'):
 outside=ROOT/('evidence/contract-'+kind)
 for f in sorted(outside.rglob('*')):
  if not f.is_file():continue
  rel=f.relative_to(outside).as_posix()
  target=PREFIX+'evidence/'+kind+'/'+rel
  if kind=='author' and rel.startswith('attempt01/') and f.suffix=='.md':target+='.source'
  check('preserved_'+kind+':'+rel,target in tracked and source_match(target,f.read_bytes()))
relocation=load(PREFIX+'evidence/author/attempt01/RELOCATION.json')
initial=load(PREFIX+'evidence/author/attempt01/FILE-INTEGRITY.json')
relmap={r['original']:r for r in relocation['files']}
check('five_original_markdown_relocations',set(relmap)=={'CONTRACT.md','CONTROL-PLAN.md','FIELD-ORIGINS.md','NEXT-TASK.md','README.md'})
for row in initial['files']:
 original=Path(row['path']).name
 target=PREFIX+'evidence/author/attempt01/'+relmap.get(original,{'preservedAs':original})['preservedAs']
 data=(REPO/target).read_bytes()
 oldpath=PREFIX+'evidence/author/attempt01/'+original
 check('initial_draft_retained:'+original,len(data)==row['bytes'] and digest(data)==row['sha256'] and bytes_at('83a7c28',oldpath)==data)
check('initial_failure_report_tracked',PREFIX+'evidence/integration/candidate-first/documentation.json' in tracked)
first=load(PREFIX+'evidence/integration/candidate-first/documentation.json')
check('first_candidate_failure_honest',first['commit'].startswith('83a7c28') and first['passed'] is False and first['returnCode']!=0)
firstlog=PREFIX+'evidence/integration/candidate-first/'+first['log']
check('first_failure_full_log_tracked',firstlog in tracked and digest((REPO/firstlog).read_bytes())==first['logSha256'])
for f in (REPO/PREFIX/'evidence').rglob('*'):
 if f.is_file() and f.suffix in ('.log','.stdout','.stderr'):
  rel=f.relative_to(REPO).as_posix()
  check('log_tracked:'+rel,rel in tracked and bytes_at(REV,rel)==f.read_bytes())
results=[]
for name in ('documentation','c253-manifest'):
 d=json.loads((ROOT/('evidence/candidate-corrected-checks/'+name+'.json')).read_text())
 log=ROOT/'evidence/candidate-corrected-checks'/d['log']
 check('corrected_check:'+name,d['passed'] and d['returnCode']==0 and not d['timedOut'] and d['commit']==REV and d['tree']==TREE and d['sourceCleanBefore'] and d['sourceUnchangedAfter'] and digest(log.read_bytes())==d['logSha256'])
 check('check_script_binding:'+name,digest((REPO/d['command'][-1]).read_bytes())==d['scriptSha256'])
 results.append({'name':name,'receipt':str(ROOT/('evidence/candidate-corrected-checks/'+name+'.json')),'logSha256':d['logSha256']})
status=(REPO/'STATUS.md').read_text()
lease_marker='## Main integration lease'
def lease_section(s):return s.split(lease_marker,1)[1].split('\n## ',1)[0]
check('lease_fields_unchanged_from_verified_main',lease_section(status)==lease_section(bytes_at(BASE,'STATUS.md').decode()))
check('lease_owner_and_expiry', 'c260-root-a827454f4cb7-20261117' in lease_section(status) and '2026-11-17T20:24:08Z' in lease_section(status))
for path in ['AGENTS.md','GOAL.md','docs/README.md','STATUS.md']:
 s=(REPO/path).read_text()
 current=s if path!='STATUS.md' else s.split('## C258:',1)[0]
 check('scope_no_implementation_claim:'+path,'28' in current and 'unrun' in current.lower() and ('no hinge reader' in current.lower() or 'no hinge-reader implementation' in current.lower() or 'contract preparation only' in current.lower()))
for path in ['AGENTS.md','docs/README.md','STATUS.md',PREFIX+'RESULTS.md']:
 s=(REPO/path).read_text()
 current=s if path!='STATUS.md' else s.split('## C258:',1)[0]
 check('C174_absence_and_retention_limit:'+path,'absent' in current and 'unestablished' in current)
check('candidate_unchanged_at_end',git('rev-parse','HEAD')==REV and git('rev-parse','HEAD^{tree}')==TREE and git('status','--porcelain=v1','--untracked-files=all')=='')
report={'schema':'ontokin.c260.integration-review-assertions/1','recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidateCommit':REV,'candidateTree':TREE,'observedMain':BASE,'passed':all(x['passed'] for x in checks),'checks':checks,'count':len(checks),'correctedCheckReceipts':results,'runtimeTestsRepeated':False,'sourceEdited':False}
(OUT/'ASSERTIONS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'failures':[x['name'] for x in checks if not x['passed']]}))
raise SystemExit(0 if report['passed'] else 1)

