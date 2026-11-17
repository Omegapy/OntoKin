"""Reproduce the two retained used-binding failures; no fixture regeneration.

Written after the original probe to make its retained exact inputs reusable.
Supply the immutable original candidate checkout, not the corrected reader.
"""
from pathlib import Path
import argparse
import json
import sys
import types

parser = argparse.ArgumentParser()
parser.add_argument('--candidate', type=Path, required=True)
args = parser.parse_args()
path = args.candidate/'docs/engineering/localized-repair-c258/follows.py'
module = types.ModuleType('c258_retained_collision_reproduction')
module.__file__ = str(path)
sys.modules[module.__name__] = module
exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
for name in ('used-rack-frame-collision', 'used-child-origin-collision'):
    folder = Path(__file__).resolve().parent/name
    files = {file:(folder/file).read_bytes() for file in ('main.ok','hinges.ok')}
    try:
        result = module.observe_source_follows(files)
        print(json.dumps({'name':name,'status':'ACCEPTED','followCount':result['followCount'],
            'parents':[r['parentFrame'] for r in result['records']]}))
    except module.Fault as error:
        print(json.dumps({'name':name,'status':'REFUSED','code':error.code,'detail':error.detail}))
