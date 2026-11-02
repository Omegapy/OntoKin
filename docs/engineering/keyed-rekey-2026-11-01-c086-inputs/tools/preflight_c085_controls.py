#!/usr/bin/env python3
"""Run explicit .18 controls on exact unchanged C085; no candidate code."""
from pathlib import Path
import argparse,hashlib,json,os,platform,stat,subprocess,sys,traceback
from datetime import datetime,timezone

def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--fixtures',type=Path,required=True);ap.add_argument('--agent-fixtures',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 assert not a.output.exists(),'new output required';a.output.mkdir(parents=True);sys.dont_write_bytecode=True;sys.path.insert(0,str(a.source))
 env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
 def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=a.source,env=env).decode().strip()
 def inventory():
  ls=subprocess.check_output(['git','--no-optional-locks','ls-files','-s','-z'],cwd=a.source,env=env); rows=[]
  for item in ls.split(b'\0'):
   if not item:continue
   head,path=item.split(b'\t',1);mode,blob,stage=head.decode().split();p=a.source/os.fsdecode(path)
   assert not p.is_symlink(),str(p)
   b=p.read_bytes();actual='100755' if p.stat().st_mode&0o111 else '100644';assert mode==actual,str(p)
   rows.append({'path':os.fsdecode(path),'git_mode':mode,'git_blob':blob,'bytes':len(b),'sha256':sha(b)})
  return rows
 identity={'commit':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':git('status','--porcelain=v1','--untracked-files=all')}
 assert identity=={'commit':'f4c90c04b9b381de73d46715d52e68f588e49e4f','tree':'7c716b717d92027eecfa911a8ec8df16d851ae47','status':''},identity
 before=inventory();save(a.output/'source-inventory-before.json',before)
 from ontokin.texture_bundle import load_texture_file_manifest
 from ontokin.construction import compile_construction
 from ontokin.execution_budget import HostPolicy,SharedExecutionBudget,admit_entry_budget
 from ontokin.budget_runtime import execute_keyed_zip_export
 from ontokin.scene import ExportOptions
 from ontokin.program_diagnostics import diagnostic_dict
 report={'schema_version':'ontokin.c086-baseline-control-preflight/0.1','status':'running','started_utc':datetime.now(timezone.utc).isoformat(),'command':[sys.executable,*sys.argv],'python':sys.version,'platform':platform.platform(),'implementation':identity,'source_tracked_files':len(before),'core_fixture_expected_sha256':sha((a.fixtures/'expected.json').read_bytes()),'controls':[],'agent_controls':[],'failures':[],'candidate_runtime_used':False,'candidate_runtime_executions':0,'complete_release_accepted':False}
 cases=json.loads((a.fixtures/'expected.json').read_text())['cases']
 for c in cases:
  if c['expected_outcome']!='valid':continue
  control=c['explicit_c085_control'];row={'name':c['name'],'file_manifest':control['file_manifest'],'expected_program_revision':control['program_revision'],'requested_stage':'represented','host_policy':c['host_policy']};bundle=None;ledger=None
  try:
   bundle=load_texture_file_manifest(a.fixtures/control['file_manifest']);assert bundle.program_revision==control['program_revision']
   ledger=SharedExecutionBudget(HostPolicy(**c['host_policy']));admit_entry_budget(bundle.entry,ledger,profile='keyed-zip-0.1')
   compiler=compile_construction(bundle,level='represented',execution_budget=ledger)
   value=compiler.field('shape','result');payload=value.to_data()
   row.update(status='passed',program_revision=bundle.program_revision,value=payload,execution_budget=ledger.report(status='valid'))
   want=c.get('expected',{}).get('entry_constructor_values')
   if want is not None:assert value.type.kind=='Keyed' and [k for k,_ in value.value.entries]==sorted(want),c['name']
  except Exception as exc:
   row.update(status='failed',exception_type=type(exc).__name__,exception=str(exc),traceback=traceback.format_exc())
   if hasattr(exc,'diagnostic') and bundle is not None:row['diagnostic']=diagnostic_dict(exc.diagnostic,bundle)
   if ledger is not None:row['execution_budget']=ledger.report(status='failed')
   report['failures'].append({'kind':'core','name':c['name'],'exception':str(exc)})
  save(a.output/'core'/f'{c["name"]}.json',row);report['controls'].append({k:v for k,v in row.items() if k not in ['value','traceback','diagnostic']})
  if len(report['controls'])%20==0:print(json.dumps({'core_completed':len(report['controls']),'failures':len(report['failures'])}),flush=True)
 for name in ['panel-task','panel-task-repaired','panel-task-restored','panel-task-higher-budget']:
  fm='control-'+name+'.files.json';policy={'max_operations':400000,'max_elapsed_ms':80000} if name.endswith('higher-budget') else {'max_operations':100000,'max_elapsed_ms':30000}
  row={'name':name,'file_manifest':fm,'requested_stage':'delivered','host_policy':policy,'options':{'fps':4,'end':'1','helpers':False}}
  try:
   bundle=load_texture_file_manifest(a.agent_fixtures/fm);row['program_revision']=bundle.program_revision
   output=execute_keyed_zip_export(bundle,policy=HostPolicy(**policy),options=ExportOptions(fps=4,end='1',helpers=False))
   save(a.output/'agent'/f'{name}.receipt.json',output.report)
   assert output.data is not None,'Explicit .18 delivery refused: '+str(output.report)
   (a.output/'agent'/f'{name}.glb').write_bytes(output.data)
   row.update(status='passed',bytes=len(output.data),sha256=sha(output.data),report=f'agent/{name}.receipt.json',artifact=f'agent/{name}.glb')
  except Exception as exc:
   row.update(status='failed',exception_type=type(exc).__name__,exception=str(exc),traceback=traceback.format_exc());report['failures'].append({'kind':'agent','name':name,'exception':str(exc)})
  save(a.output/'agent'/f'{name}.json',row);report['agent_controls'].append(row);print(json.dumps({'agent_control':name,'status':row['status']}),flush=True)
 after=inventory();save(a.output/'source-inventory-after.json',after);end={'commit':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':git('status','--porcelain=v1','--untracked-files=all')}
 report.update(completed_utc=datetime.now(timezone.utc).isoformat(),source_inventory_unchanged=before==after,source_identity_unchanged=identity==end,source_after=end)
 assert before==after and identity==end,'source changed'
 report['counts']={'core_controls':len(report['controls']),'core_passed':sum(r['status']=='passed' for r in report['controls']),'agent_controls':len(report['agent_controls']),'agent_passed':sum(r['status']=='passed' for r in report['agent_controls'])}
 report['status']='passed' if not report['failures'] else 'failed';save(a.output/'summary.json',report)
 print(json.dumps({'status':report['status'],'counts':report['counts'],'source_inventory_unchanged':report['source_inventory_unchanged'],'output':str(a.output)}),flush=True)
 if report['failures']:raise SystemExit(1)
if __name__=='__main__':main()
