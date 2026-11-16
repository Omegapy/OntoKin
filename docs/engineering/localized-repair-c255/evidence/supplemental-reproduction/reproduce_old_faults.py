#!/usr/bin/env python3
"""Reproduce only the two C255 false acceptances on the preserved old commit."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--review-dir',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
repo=args.repo.resolve(); review=args.review_dir.resolve(); out=args.output_dir.resolve()
out.mkdir(parents=True,exist_ok=False)
old='2eb3f6f7c263dbb5f215ad87bc93a03010d789aa'
old_hash='8c2c6c75adfc2d61537c060ea03d87ada6f7b85940ccaf44b6b5d5b84ced7fd3'
new='2ef850a235ad158dcb06dd956388015861765eb1'
new_hash='b7275bd40bd429397ce6db5608bc025493a5e92cfc378f70e05cc799f50ff593'
source_path='docs/engineering/localized-repair-c255/oracle.py'

def git(*parts):
 return subprocess.check_output(['git','-C',str(repo),*parts])

def sha(raw):return hashlib.sha256(raw).hexdigest()

before={'head':git('rev-parse','HEAD').decode().strip(),'status':git('status','--porcelain=v1').decode()}
old_source=git('show',old+':'+source_path)
new_source=git('show',new+':'+source_path)
assert sha(old_source)==old_hash and sha(new_source)==new_hash
(out/'old-oracle.py').write_bytes(old_source)
runner=out/'unchanged-probe';runner.mkdir()
script_rows=[]
for name in ['targeted_gap_probe.py','independent_controls.py','independent_basis.py']:
 raw=(review/name).read_bytes();(runner/name).write_bytes(raw)
 assert (runner/name).read_bytes()==raw
 script_rows.append({'path':'unchanged-probe/'+name,'original':str(review/name),'sha256':sha(raw),'unchanged':True})
inputs=json.loads((review/'INPUT-BINDINGS.json').read_text())['inputs']
input_rows=[]
with tempfile.TemporaryDirectory(prefix='exact-old-inputs-',dir=out) as temporary:
 tree=Path(temporary)
 for row in inputs:
  raw=git('show',old+':'+row['path'])
  assert sha(raw)==row['sha256']
  p=tree/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  input_rows.append({'path':row['path'],'bytes':len(raw),'sha256':sha(raw),'sourceCommit':old})
 p=tree/source_path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old_source)
 expected_output=runner/('targeted-gap-'+old_hash[:12]+'.json')
 assert not expected_output.exists()
 command=[sys.executable,'-B',str(runner/'targeted_gap_probe.py'),'--repo',str(tree)]
 result=subprocess.run(command,capture_output=True,text=True,timeout=30)
 (out/'fresh-old-probe.stdout.log').write_text(result.stdout)
 (out/'fresh-old-probe.stderr.log').write_text(result.stderr)
 assert result.returncode==0 and expected_output.exists()
 fresh=json.loads(expected_output.read_text())
 assert fresh['oracleSha256']==old_hash
 corrected_path=review/('targeted-gap-'+new_hash[:12]+'.json')
 corrected_raw=corrected_path.read_bytes(); corrected=json.loads(corrected_raw)
 assert corrected['oracleSha256']==new_hash
 comparisons=[]
 for a,b in zip(fresh['probes'],corrected['probes']):
  assert all(a[k]==b[k] for k in ['case','quaternionAngle','rawRotationAngle','uniformMatrixScale','expectedComponentPass'])
  assert a['result']['componentPass'] is True and b['result']['componentPass'] is False
  comparisons.append({'case':a['case'],'oldFreshComponentPass':a['result']['componentPass'],
                      'correctedPriorComponentPass':b['result']['componentPass'],
                      'correctedFaults':b['result']['faults'],
                      'sameProbeValues':True})
 record={'schema':'ontokin.c255.supplemental-old-fault-reproduction/0.1',
         'recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'freshReproduction':True,'isOriginalOverwrittenRecord':False,
         'scope':'Exactly two raw-angle residual probes; no broad suite or corrected-source rerun.',
         'oldCommit':old,'oldTree':git('rev-parse',old+'^{tree}').decode().strip(),'oldOracleSha256':old_hash,
         'correctedCommit':new,'correctedOracleSha256':new_hash,
         'unchangedProbeSources':script_rows,'frozenInputBindings':input_rows,
         'command':command,'exitCode':result.returncode,
         'uniqueFreshResultPath':str(expected_output.relative_to(out)),
         'correctedPriorEvidence':{'path':str(corrected_path),'sha256':sha(corrected_raw),'readOnlyComparison':True},
         'comparisons':comparisons,'passed':len(comparisons)==2,
         'environment':{'python':sys.version,'executable':sys.executable,'platform':platform.platform()},
         'sourceTreeDisposition':'Minimal temporary input tree recreated from exact git-show bytes; deleted after run. Old oracle bytes and all binding hashes, unchanged probe sources, fresh outputs and logs preserved here. Frozen inputs remain in the restored repository and its historical commit.',
         'reviewDisposition':'Existing independent exact-current-file approval is unchanged; this adds fresh evidence for the earlier reproducible fault.'}
 after={'head':git('rev-parse','HEAD').decode().strip(),'status':git('status','--porcelain=v1').decode()}
 record['currentRepositoryBefore']=before;record['currentRepositoryAfter']=after
 record['currentRepositoryUnchanged']=before==after
 assert record['currentRepositoryUnchanged']
 (out/'REPRODUCTION.json').write_text(json.dumps(record,indent=2))
print(json.dumps({'passed':record['passed'],'oldFalseAcceptances':2,'correctedPriorRejections':2,'currentRepositoryUnchanged':record['currentRepositoryUnchanged'],'output':str(out)}))
