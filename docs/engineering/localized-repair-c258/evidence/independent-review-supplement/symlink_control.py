#!/usr/bin/env python3
"""Actual hosted self-referential repo-path refusal; no source mutation."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import types

parser=argparse.ArgumentParser()
parser.add_argument('--candidate',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
root=args.candidate.resolve()
path=root/'docs/engineering/localized-repair-c258/follows.py'
module=types.ModuleType('c258_supplemental_symlink_control')
module.__file__=str(path)
sys.modules[module.__name__]=module
exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
stage=args.out.parent/'symlink-loop-stage'
stage.mkdir()
loop=stage/'loop'
loop.symlink_to('loop')
before=subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True)
result={'commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
    'tree':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD^{tree}'],text=True).strip(),
    'readerSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'python':sys.version,'platform':platform.platform(),
    'inputRecipe':{'repo':str(loop),'endpoint':'before','symlinkTarget':os.readlink(loop)},
    'expected':'typed Fault with IO code','cleanBefore':before==''}
try:
    module.read_bound_endpoint(loop,'before')
    result.update(passed=False,actual='unexpected success')
except module.Fault as error:
    result.update(passed=error.code=='IO',actual='typed refusal',code=error.code,detail=error.detail)
except Exception as error:
    result.update(passed=False,actual='untyped exception',exceptionType=type(error).__name__,detail=str(error))
finally:
    loop.unlink()
    stage.rmdir()
result['cleanAfter']=subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True)==''
result['stageRemoved']=not stage.exists()
result['scriptSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
args.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('passed','actual','code','cleanBefore','cleanAfter')}))
raise SystemExit(0 if result['passed'] and result['cleanBefore'] and result['cleanAfter'] else 1)
