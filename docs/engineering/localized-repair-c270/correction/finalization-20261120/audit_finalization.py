#!/usr/bin/env python3
"""Read exact Git objects and retained evidence; never execute behavior or mutate Git."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path('/workspace/scratch/a2bb67238030')
REPO = ROOT / 'OntoKin'
OUT = ROOT / 'audit/review'
ROUTINE = ROOT / 'recovered/latest/session-evidence/routine-interrupted'
BASE = '55c585acdaa750961ac37a5c46c9160bed149f97'
IMPL = 'a6099546e2ae66e78621008338ecd3b2d352d9b8'
TARGET = '2076b06f133fd548079052102e060bc29abc7493'
ENG = 'docs/engineering/'
EVID = ENG + 'localized-repair-c270/evidence/correction-20261120/'
CAND = EVID + 'candidate/'
CODE = [ENG + p for p in (
    'localized-repair-c265/source_hinges.py',
    'localized-repair-c266/hinge_binding.py',
    'localized-repair-c267/hinge_compare.py',
    'localized-repair-c268/endpoint_reader.py',
    'localized-repair-c268/endpoint_control_fixtures.py')]
checks, commands, identities, cache = [], [], {}, {}
started = datetime.now(timezone.utc).isoformat()

def identity(raw):
    return {'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}

def check(label, condition, **data):
    checks.append({'label':label, 'passed':bool(condition), **data})

def git(*args, allow_failure=False):
    cmd = ['git', '-C', str(REPO), *args]
    p = subprocess.run(cmd, capture_output=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    commands.append({'argv':cmd, 'returncode':p.returncode, 'stdout_identity':identity(p.stdout),
                     'stderr':p.stderr.decode(errors='replace')})
    if p.returncode and not allow_failure:
        raise RuntimeError(str(cmd) + ': ' + p.stderr.decode())
    return p.stdout

def source(path, rev=TARGET):
    key = (rev, path)
    if key not in cache:
        cache[key] = git('show', rev + ':' + path)
        identities[rev + ':' + path] = identity(cache[key])
    return cache[key]

def data(path, rev=TARGET):
    return json.loads(source(path, rev))

def tree(rev):
    result = {}
    for row in git('ls-tree','-rz','--full-tree',rev).split(b'\0'):
        if row:
            meta, path = row.split(b'\t',1)
            result[path.decode()] = meta.decode()
    return result

def assignment(raw, name):
    parsed = ast.parse(raw)
    for n in parsed.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id == name for t in n.targets):
            value = n.value
            if isinstance(value,ast.Call) and isinstance(value.func,ast.Attribute) and value.func.attr == 'MappingProxyType':
                value = value.args[0]
            return ast.literal_eval(value)
    raise ValueError(name)

def excluding_assignment(raw, name):
    t = ast.parse(raw)
    t.body = [n for n in t.body if not (isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id == name for a in n.targets))]
    return ast.dump(t, include_attributes=False)

def mapped_path(path, relative_base=''):
    mappings = {
        '/workspace/scratch/92228987b591/validation/candidate/':'',
        '/workspace/scratch/92228987b591/evidence/candidate/':CAND,
        '/workspace/scratch/92228987b591/evidence/run_distinctions.py':CAND+'run_distinctions.py',
    }
    for old,new in mappings.items():
        if path.startswith(old):
            return new + path[len(old):]
    if path.startswith('/'):
        raise ValueError('Unmapped historical path: ' + path)
    return relative_base + path

def verify_row(label, row, base='', original_input=False, mutable_record=False):
    path = mapped_path(row['path'],base)
    expected = {'bytes':row['bytes'],'sha256':row['sha256'].removeprefix('sha256:')}
    actual = identity(source(path))
    if original_input:
        check(label+':executed_revision', identity(source(path,IMPL)) == expected, path=path)
    if mutable_record:
        check(label+':changed_record_not_reused', actual != expected, path=path, current=actual, executed=expected)
    else:
        check(label, actual == expected, path=path, expected=expected, actual=actual)
    return path

trees = {r:tree(r) for r in (BASE,IMPL,TARGET)}
before, impl, after = (trees[r] for r in (BASE,IMPL,TARGET))
changed = sorted(p for p in before.keys() & after.keys() if before[p] != after[p])
added = sorted(after.keys()-before.keys())
deleted = sorted(before.keys()-after.keys())
state = ['STATUS.md','docs/workflow/CURRENT.json','docs/workflow/memory.json',
         'docs/workflow/tasks/C270/PLAN.md','docs/workflow/tasks/C270/REQUIREMENTS.md','docs/workflow/tasks/C270/task.json']
check('existing_scope_exact',set(changed) == set(CODE + state), changed=changed)
check('no_deletions',not deleted,deleted=deleted)
check('added_paths_scoped',all(p.startswith((ENG+'localized-repair-c270/correction/',EVID)) for p in added))
historical = [p for p in before if p.startswith((ENG+'localized-repair-c260/',ENG+'localized-repair-c270/'))]
check('all_204_original_C260_C270_files_preserved',len(historical)==204 and all(before[p]==after.get(p) for p in historical),count=len(historical))
for scope in ('ontokin/','tests/','tools/','.github/workflows/'):
    paths = sorted(p for p in before.keys()|after.keys() if p.startswith(scope))
    check('unchanged_core_scope:'+scope,all(before.get(p)==after.get(p) for p in paths),path_count=len(paths))
later_changed = sorted(p for p in impl.keys()&after.keys() if impl[p]!=after[p])
later_added = sorted(after.keys()-impl.keys())
check('later_only_memory_task_modified',later_changed==['docs/workflow/memory.json','docs/workflow/tasks/C270/task.json'],paths=later_changed)
check('later_added_only_evidence_learning',all(p.startswith(EVID) or p==ENG+'localized-repair-c270/correction/LEARNING.md' for p in later_added),count=len(later_added))
check('all_implementation_test_command_inputs_unchanged_since_a609',all(impl.get(p)==after.get(p) for p in impl if p not in later_changed))

pin_rows=[]
for path in CODE[1:]:
    check('pin_only_AST:'+path,excluding_assignment(source(path,BASE),'DEPENDENCIES') == excluding_assignment(source(path),'DEPENDENCIES'))
    for key,value in assignment(source(path),'DEPENDENCIES').items():
        if len(value)==3: rel,size,digest=value
        else: rel,(size,digest)=key,value
        actual=identity(source(ENG+rel))
        pin_rows.append({'consumer':path,'dependency':ENG+rel,'declared':{'bytes':size,'sha256':digest},'actual':actual})
        check('pin:'+path+':'+key,actual=={'bytes':size,'sha256':digest})
check('17_current_downstream_pins',len(pin_rows)==17)
check('unchanged_C265_C257_pin',identity(source(ENG+'localized-repair-c257/ownership.py'))=={
    'bytes':assignment(source(CODE[0]),'DEPENDENCY_BYTES'),
    'sha256':assignment(source(CODE[0]),'DEPENDENCY_SHA256')})
ast_before,ast_after=ast.parse(source(CODE[0],BASE)),ast.parse(source(CODE[0]))
classes=[next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Source') for t in (ast_before,ast_after)]
methods=[{n.name:ast.dump(n,include_attributes=False) for n in c.body if isinstance(n,ast.FunctionDef)} for c in classes]
method_deltas=sorted(k for k in methods[0].keys()|methods[1].keys() if methods[0].get(k)!=methods[1].get(k))
check('only_scan_class_and_site_changed',method_deltas==['scan_class','site'],methods=method_deltas)
for t in (ast_before,ast_after):t.body=[n for n in t.body if not (isinstance(n,ast.ClassDef) and n.name=='Source')]
check('all_other_C265_definitions_unchanged',ast.dump(ast_before,include_attributes=False)==ast.dump(ast_after,include_attributes=False))
pm=data(ENG+'localized-repair-c270/correction/PIN-CHANGES.json')
check('nine_changed_pin_entries',len(pm['updated_dependencies'])==9)
for row in pm['files']:
    check('pin_manifest_before:'+row['path'],identity(source(row['path'],BASE))==row['before'])
    check('pin_manifest_after:'+row['path'],identity(source(row['path']))==row['after'])
for row in pm['updated_dependencies']:
    check('pin_manifest_dep_before:'+row['consumer']+':'+row['dependency'],identity(source(row['dependency'],BASE))==row['before'])
    check('pin_manifest_dep_after:'+row['consumer']+':'+row['dependency'],identity(source(row['dependency']))==row['after'])
snap_prefix=EVID+'implementer-preflight/checked-code/'
snapshots=[p for p in after if p.startswith(snap_prefix)]
check('six_implementer_code_snapshots',len(snapshots)==6)
for path in snapshots:check('preflight_code:'+path,source(path)==source(path[len(snap_prefix):]))

oracle=data(ENG+'localized-repair-c270/control/EXPECTED.json')
check('frozen_oracle_hash',identity(source(ENG+'localized-repair-c270/control/EXPECTED.json'))['sha256']=='aa73df1e9ffb4d76bc589a7239f454be28e4cd6ae4ee523b208dbf66860ef4a7')
for row in oracle['original_inputs']+oracle['supplied_sources']:verify_row('oracle:'+row['path'],row)
h=data(CAND+'h16/RESULTS.json')
a=data(CAND+'affected-cohort/CHECKS.json')
d=data(CAND+'distinctions/CHECKS.json')
itree=git('rev-parse',IMPL+'^{tree}').decode().strip()
check('h16_committed_source_identity',h['source_revision']==IMPL and h['source_tree']==itree)
check('h16_all_45_assertions',h['passed'] and not h['failed_assertions'] and len(h['cases'])==5 and sum(len(c['assertions']) for c in h['cases'])==45 and all(c['passed'] and all(c['assertions'].values()) for c in h['cases']))
check('h16_stable_clean',h['inputs']==h['inputs_after'] and h['inputs_unchanged'] and h['source_revision_unchanged'] and h['tracked_clean_after'] and not h['tracked_dirty_status'])
for i,row in enumerate(h['inputs']):verify_row('h16_input:'+str(i),row,original_input=True)
verify_row('h16_oracle',h['frozen_expectation'],original_input=True)
hashes={Path(row['path']).name:row['sha256'] for row in oracle['supplied_sources']}
sizes={Path(row['path']).name:row['bytes'] for row in oracle['supplied_sources']}
for c in h['cases']:
    if 'response' in c:
        path=verify_row('h16_response:'+c['label'],c['response'])
        value=data(path)
        check('original_8_hinges:'+c['label'],value.get('hingeCount')==8)
        if c['label']=='original-source':check('original_16_sites',value.get('siteCount')==16)
        continue
    chain=c['cause_chain'];depth={'siteref-source':1,'siteref-binding':2,'siteref-comparison':3}[c['label']]
    check('h16_chain:'+c['label'],len(chain)==depth and all(x['code']=='UNSUPPORTED_SOURCE_FORM' and x['detail']=='declared SiteRef parameter endpoint is unsupported' and x['sourceHashes']==hashes and x['sourceBytes']==sizes for x in chain))
    forbidden={'records','hinges','sites','objects','hingeCount','siteCount','objectCount','qualified','inputBindingVerified','hingeComparisonVerified','hingeSetAgreementVerified','endpointAgreementVerified'}
    check('no_partial_fields:'+c['label'],all(not forbidden.intersection(x) for x in chain))
    check('source_site_origin:'+c['label'],chain[-1]['traceback'][-1]['function']=='site' and chain[-1]['traceback'][-1]['line']==528)
    if depth>1:
        check('originating_pinned_source:'+c['label'],chain[-1]['module']=='_c266_pinned_source')
        check('artifact_retained:'+c['label'],all(x.get('artifactSha256')=='d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534' and x.get('artifactBytes')==185276 for x in chain[:-1]))

check('affected_committed_source_identity',all(a[k]['commit']==IMPL and a[k]['tree']==itree and not a[k]['tracked_dirty_status'] for k in ('source_before','source_after')))
check('affected_complete_282_methods_12_groups',a['complete'] and a['passed'] and a['planned_check_count']==a['completed_check_count']==len(a['checks'])==12 and a['total_methods']==a['expected_total_methods']==282 and not a['remaining_checks'])
check('affected_stable_inputs',a['input_files_before']==a['input_files_after'] and a['input_identity_unchanged'])
for i,row in enumerate(a['input_files_before']):verify_row('affected_input:'+str(i),row,original_input=True,mutable_record=row['path']=='docs/workflow/memory.json')
for i,row in enumerate(a['output_files']):verify_row('affected_output:'+str(i),row,CAND+'affected-cohort/')
verify_row('affected_runner',a['runner'],original_input=True)
method_inventory={}
for c in a['checks']:
    check('affected_group:'+c['name'],c['result']=='passed' and c['exit_code']==0 and c['failure'] is None and all(c['assertions'].values()))
    logpath=verify_row('affected_log:'+c['name'],c['log'],CAND+'affected-cohort/')
    log=source(logpath).decode()
    if c['expected_methods'] is not None:
        method_inventory[c['name']]=c['expected_methods']
        check('affected_log_result:'+c['name'],re.findall(r'^Ran (\d+) tests? in ',log,re.M)==[str(c['expected_methods'])] and re.search(r'^OK\s*$',log,re.M) is not None and re.search(r'^FAILED\b|^ERROR:|^FAIL:|\.\.\. (?:skipped|expected failure|unexpected success)',log,re.M) is None)
        cmd=c['command'];testpath=cmd[cmd.index('-s')+1]+'/'+cmd[cmd.index('-p')+1] if '-s' in cmd else next(v for v in cmd if v.endswith('.py'))
        testast=ast.parse(source(testpath))
        count=sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_') for n in ast.walk(testast))
        check('complete_static_method_inventory:'+c['name'],count==c['expected_methods'],count=count,path=testpath)
    if c['name']=='c253-corpus':check('all_14_corpus_bindings',c['details']['boundFiles']==14 and c['details']['passed'])
    if 'results_identity' in c['details']:
        rp=verify_row('retained_results:'+c['name'],c['details']['results_identity'],CAND+'affected-cohort/')
        rd=data(rp)
        check('retained_controls:'+c['name'],rd['passed'] and rd['testMethods']==c['expected_methods'] and not any(rd[k] for k in ('failures','errors','skipped')) and len(rd['cases'])==rd['apiCalls'])
check('distinctions_committed_source_identity',d['source_revision']==d['source_revision_after']==IMPL and d['source_tree']==itree and not d['tracked_dirty_before'] and not d['tracked_dirty_after'])
check('distinctions_stable_passed',d['inputs_before']==d['inputs_after'] and d['passed'] and d['exit_code']==0 and d['methods']==8)
for i,row in enumerate(d['inputs_before']):verify_row('distinctions_input:'+str(i),row,original_input=True)
verify_row('distinctions_runner',d['runner'])
lp=verify_row('distinctions_log',d['log'],CAND+'distinctions/')
log=source(lp).decode()
check('distinctions_eight_methods',len(re.findall(r'^test_.* \.\.\. ok$',log,re.M))==8 and 'Ran 8 tests in ' in log and re.search(r'^OK\s*$',log,re.M) is not None)

binary=Path(sys.executable).resolve();current_binary=identity(binary.read_bytes())
check('same_executed_interpreter_binary',all({'bytes':e['bytes'],'sha256':e['sha256']}==current_binary for e in (h['environment']['executable'],d['environment']['executable'],a['environment']['resolved_executable'])))
check('same_python_version_platform',all(e['python']==sys.version and e['platform']==platform.platform() for e in (h['environment'],a['environment'],d['environment'])))
check('same_runtime_bundle',a['environment']['runtime_bundle_version']==os.environ.get('CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION'),recorded=a['environment']['runtime_bundle_version'],current=os.environ.get('CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION'))

recovery=json.loads((ROUTINE/'RECOVERY.json').read_text())
routine_identities=[]
for row in recovery['preserved_files']:
    raw=(ROUTINE/row['path']).read_bytes();actual=identity(raw)
    check('routine_raw_identity:'+row['path'],actual=={'bytes':row['bytes'],'sha256':row['sha256']})
    routine_identities.append({'path':str(ROUTINE/row['path']),**actual})
summary=json.loads((ROUTINE/'summary.json').read_text())
check('routine_running_not_completed',summary['status']=='running' and summary['steps']==[] and 'finished_at' not in summary and not summary['release_certified'] and not summary['full_product_conformance_certified'])
check('routine_original_commit_tree',summary['git']['local_head']==IMPL and summary['git']['local_tree']==itree and summary['git']['tracked_worktree_status']=='')
rlog=(ROUTINE/'logs/unit-tests.log').read_text()
diagnostics=[{'line':i+1,'text':line} for i,line in enumerate(rlog.splitlines()) if re.search(r'\b(?:FAIL|ERROR|FAILED|Traceback|SKIP|skipped|expected failure)\b',line)]
check('routine_no_observed_failure_or_skip_diagnostic',not diagnostics,diagnostics=diagnostics)
check('routine_no_completed_test_summary',re.search(r'^Ran \d+ tests? in |^OK\s*$|^FAILED\b',rlog,re.M) is None)
literal_ok=len(re.findall(r'^test_.* \.\.\. ok$',rlog,re.M))
check('routine_2355_literal_ok_lines_only',literal_ok==2355,count=literal_ok)
last=rlog.splitlines()[-1]
check('routine_trailing_unfinished_case',last==recovery['trailing_unfinished_test'],line=last)
for rev in ('2814aac8d90db075cf3f17a144ede3a465c12ef8',IMPL,TARGET):
    task=data('docs/workflow/tasks/C270/task.json',rev)
    row=next(c for c in task['checks'] if c['name']=='routine local driver')
    check('routine_invocation_only_predeclared:'+rev,row['required'] is False and row['interpretation'].startswith('Mandatory invocation; complete affected regression acceptance is separately identified.'),check=row)
refs={}
for path in ('ontokin','tests','tools'):
    raw=git('grep','-n','-E','localized-repair-c26[5-8]|source_hinges|hinge_binding|hinge_compare|endpoint_reader',TARGET,'--',path,allow_failure=True)
    refs[path]=raw.decode()
check('no_core_module_imports_observer',not refs['ontokin'] and not refs['tools'] and refs['tests'].count('\n')==1 and 'def test_stationary_source_hinges_keep_their_direct_cache_across_clocks' in refs['tests'])
check('unchanged_trailing_test',before['tests/test_reach_phase_operand_reuse.py']==after['tests/test_reach_phase_operand_reuse.py'])
delta=git('diff','--name-status',IMPL,TARGET).decode()
(OUT/'a609-to-2076-paths.txt').write_text(delta)
(OUT/'implementation-diff.patch').write_bytes(git('diff',BASE,TARGET,'--',*CODE))
failed=[c for c in checks if not c['passed']]
report={
    'schema':'ontokin.c270.finalization-review-evidence/1','reviewer':'/root/candidate_review',
    'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
    'base_revision':BASE,'implementation_revision':IMPL,'implementation_tree':itree,
    'candidate_revision':TARGET,'candidate_tree':git('rev-parse',TARGET+'^{tree}').decode().strip(),
    'environment':{'python':sys.version,'platform':platform.platform(),'executable':str(binary),**current_binary,'runtime_bundle_version':os.environ.get('CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION')},
    'command':[sys.executable,*sys.argv],'script_identity':identity(Path(__file__).read_bytes()),
    'checks':checks,'check_count':len(checks),'failed':failed,'passed':not failed,
    'source_identities':identities,'current_dependency_pins':pin_rows,
    'changed_existing_paths':changed,'added_paths':added,'later_changed_paths':later_changed,'later_added_paths':later_added,
    'unchanged_baseline_entries':sum(before[p]==after.get(p) for p in before),
    'behavioral_method_inventory':method_inventory,
    'behavioral_results':{'frozen_cases':5,'frozen_assertions':45,'cohort_groups':12,'cohort_methods':282,'corpus_bindings':14,'supplementary_methods':8,'supplementary_variants':16,'supplementary_api_calls':48},
    'routine_raw_artifacts':routine_identities,'routine_summary':summary,
    'routine_observation':{'completed_result':None,'completed_method_total':None,'literal_ok_line_count_not_suite_total':literal_ok,'last_line':last,'observed_failure_error_skip_diagnostics':diagnostics,'global_process_absence_proven':False},
    'source_search_results':refs,'commands':commands,
    'reuse_decision':{'behavioral_evidence_eligible':not failed,'documentation_workflow_reuse_for_final_candidate':False,'fresh_candidate_and_actual_main_record_checks_required':True},
    'routine_disposition':'Interrupted; final result unknown. Mandatory invocation observed. No full-suite pass. The complete affected cohort is independently evidenced; core runtime/tests/tools unchanged and no scoped new/worsened failure observed. No concrete uncertainty requires reproduction.',
    'limits':['Static code and retained-evidence inspection only; no behavioral suite rerun.','Final metadata candidate, actual main, conditional integration and final delivery require their own assigned checks.','No general source validity, complete H16/H20/H22/H24/C260, product, destination, compatibility matrix or comparative advantage claim.']}
(OUT/'EVIDENCE.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'candidate':TARGET,'checks':len(checks),'passed':not failed,'failed':failed,'report':str(OUT/'EVIDENCE.json')}))
raise SystemExit(1 if failed else 0)
