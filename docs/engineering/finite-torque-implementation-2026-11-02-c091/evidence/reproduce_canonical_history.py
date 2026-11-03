from pathlib import Path
from dataclasses import replace
import sys,json,hashlib,subprocess,datetime
root=Path(sys.argv[1]);entry=Path(sys.argv[2]);output=Path(sys.argv[3]);sys.path.insert(0,str(root))
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate_prefix
paths=['ontokin/torque_runtime.py','ontokin/torque_phase.py','ontokin/reach_pose.py','ontokin/reach_runtime.py','ontokin/reach_numeric.py','ontokin/execution_budget.py','ontokin/evaluator.py','ontokin/model.py']
sha=lambda b:hashlib.sha256(b).hexdigest()
source_hashes={name:sha((root/name).read_bytes())for name in paths};raw=entry.read_bytes()
def describe(result):
 failure=result['failure'];ball=result['last_valid_state']['objects']['ball']
 return {'status':'accepted'if failure is None else'refused','valid_until_seconds':result['valid_until_seconds'],'valid_until_side':result['valid_until_side'],'omega_hex':[float(value).hex()for value in ball['angular_velocity_rad_per_s']],'axis':ball['torques']['axis'],'started_count':ball['torques']['started_count'],'failure':None if failure is None else {'type':type(failure).__name__,'code':failure.diagnostic.code,'details':failure.diagnostic.details}}
rows=[]
for warmed in (False,True):
 bundle=load_texture_file_manifest(root/'docs/language-design/torque-v0.1/freeze/p28-release-then-torque.files.json');bundle=replace(bundle,entry=replace(bundle.entry,raw=raw))
 ledger=SharedExecutionBudget();admit_entry_budget(bundle.entry,ledger,profile='torque-0.1');compiler=compile_construction(bundle,execution_budget=ledger)
 preparation=None
 if warmed:preparation=evaluate_prefix(compiler.model,'16384',work=compiler.reach_work)
 result=evaluate_prefix(compiler.model,'1',work=compiler.reach_work)
 rows.append({'warmed':warmed,'program_revision':bundle.program_revision,'budget':dict(ledger.limits),'operations':ledger.operations,'preparation':None if preparation is None else describe(preparation),'result':describe(result)})
report={'schema_version':'ontokin.c091-independent-public-axis-history/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'source_hashes':source_hashes,'source_hashes_unchanged':source_hashes=={name:sha((root/name).read_bytes())for name in paths},'entry_sha256':sha(raw),'entry_bytes':len(raw),'driver_sha256':sha(Path(__file__).read_bytes()),'scope':'Two fresh constructed controls from identical bytes. Warming and second public evaluate_prefix calls are adjacent with no inspection, callback change, cache access or plan injection. No private plan is observed at any point.','controls':rows}
report['status']='history_divergence_reproduced'if rows[0]['result']['status']=='accepted'and rows[1]['preparation']['status']=='accepted'and rows[1]['result']['status']=='refused'else'no_expected_divergence'
output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'source_commit':report['source_commit'],'controls':rows},indent=2))
