"""Independent targeted numerical/source authority probes after broad controls."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from independent_controls import load_module,make_case,rotated_pose

parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,required=True)
args=parser.parse_args()
repo=args.repo.resolve()
p=repo/'docs/engineering/localized-repair-c255/oracle.py'
m=load_module(p);c=m.load_corpus(repo);out=[]
for layer,angle,delta,scale_residual in [('delivery',.001,1e-10,5e-7),('reference',1e-9,1e-22,5e-13)]:
 o,a=make_case(repo,'V1',layer)
 row=o['poses'][0]
 rotated_pose(row,angle)
 actual_angle=angle+delta;s=1+scale_residual
 cs,sn=math.cos(actual_angle),math.sin(actual_angle)
 for i,v in {0:cs,1:-sn,2:0,4:sn,5:cs,6:0,8:0,9:0,10:1}.items():row['matrix'][i]=v*s
 result=m.evaluate(c,'V1',o,a)
 out.append({'case':layer+'-raw-polar-angle-over-bound-with-allowed-rounding-residual',
             'quaternionAngle':angle,'rawRotationAngle':actual_angle,'uniformMatrixScale':s,
             'expectedComponentPass':False,'result':result})
record={'oracleSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'probes':out}
Path(__file__).with_name('targeted-gap-'+record['oracleSha256'][:12]+'.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
