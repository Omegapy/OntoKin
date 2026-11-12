"""CPU-only controls for the standalone retained-evidence remeasurement script."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--script',type=Path,default=Path(__file__).with_name('recompute_c211_normals.py'))
parser.add_argument('--glb',type=Path,default=Path(__file__).resolve().parents[1]/'input/c211/receiving-run/inputs/after.glb')
parser.add_argument('--observations',type=Path,default=Path(__file__).resolve().parents[1]/'input/c211/receiving-run/import-observations.json')
parser.add_argument('--output',type=Path,default=Path(__file__).with_name('normal-self-check.json'))
args=parser.parse_args()
original=json.loads(args.observations.read_text())
original_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.glb,args.observations)}
results=[]

def case(name,mutate,expect_reject=False,extra_failures=0):
    with tempfile.TemporaryDirectory(prefix='c212-normal-control-') as td:
        dest=Path(td)
        copied=dest/'copied_audit.py'
        shutil.copyfile(args.script,copied)
        doc=copy.deepcopy(original)
        mutate(doc)
        inp=dest/'relocated-observations.json'
        inp.write_text(json.dumps(doc,separators=(',',':')))
        out=dest/'output.json'
        command=[sys.executable,str(copied),'--glb',str(args.glb.resolve()),'--observations',str(inp),'--output',str(out)]
        run=subprocess.run(command,cwd=dest,capture_output=True,text=True,timeout=30)
        if expect_reject:
            passed=run.returncode!=0 and not out.exists()
        else:
            r=json.loads(out.read_text()) if out.exists() else {}
            passed=run.returncode==0 and r.get('failed_triangles')==7088+extra_failures and r.get('failed_corner_occurrences')==14880+extra_failures and r.get('exact_position_and_winding_matches')==7800
        results.append({'case':name,'passed':passed,'expected_rejection':expect_reject,'process_returncode':run.returncode,'failure_tail':run.stderr.splitlines()[-2:] if run.returncode else [],'expected_extra_normal_failures':extra_failures})

case('explicit_paths_after_script_relocation',lambda d:None)
case('cyclic_triangle_rotation_preserved',lambda d:d['objects'][0]['triangles_raw_blender'].__setitem__(0,d['objects'][0]['triangles_raw_blender'][0][1:]+d['objects'][0]['triangles_raw_blender'][0][:1]))
case('triangle_list_reordering_preserved',lambda d:d['objects'][0]['triangles_raw_blender'].reverse())
case('reversed_winding_refused',lambda d:d['objects'][0]['triangles_raw_blender'][0].reverse(),True)
case('missing_triangle_refused',lambda d:d['objects'][0]['triangles_raw_blender'].pop(),True)
case('duplicate_triangle_replacing_another_refused',lambda d:d['objects'][0]['triangles_raw_blender'].__setitem__(1,d['objects'][0]['triangles_raw_blender'][0]),True)
case('duplicate_object_refused',lambda d:d['objects'].append(copy.deepcopy(d['objects'][0])),True)
case('missing_object_refused',lambda d:d['objects'].pop(),True)
case('exact_component_threshold_passes',lambda d:d['objects'][0]['triangles_raw_blender'][0][0].__setitem__(4,2e-6))
case('next_float_below_threshold_passes',lambda d:d['objects'][0]['triangles_raw_blender'][0][0].__setitem__(4,math.nextafter(2e-6,0.0)))
case('next_float_above_threshold_fails',lambda d:d['objects'][0]['triangles_raw_blender'][0][0].__setitem__(4,math.nextafter(2e-6,math.inf)),extra_failures=1)
case('nonfinite_normal_refused',lambda d:d['objects'][0]['triangles_raw_blender'][0][0].__setitem__(4,float('nan')),True)
case('short_corner_refused',lambda d:d['objects'][0]['triangles_raw_blender'][0][0].pop(),True)
unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in original_hashes.items())
summary={'schema':'ontokin.c212.normal-remeasurement-controls/0.1','native_processes':0,'scope':'Synthetic CPU-only data mutations; not receiving evidence','python':sys.version,'controls':len(results),'passed':sum(r['passed'] for r in results),'all_passed':all(r['passed'] for r in results) and unchanged,'retained_inputs_unchanged':unchanged,'script_sha256':hashlib.sha256(args.script.read_bytes()).hexdigest(),'control_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results}
args.output.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))
sys.exit(0 if summary['all_passed'] else 1)
