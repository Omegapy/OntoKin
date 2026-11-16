"""Independent file-authority and implementation-boundary checks for C255."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from independent_controls import load_module

parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,required=True)
args=parser.parse_args()
repo=args.repo.resolve()
base=Path(__file__).resolve().parent
path=repo/'docs/engineering/localized-repair-c255/oracle.py'
m=load_module(path)
corpus_path='docs/engineering/localized-repair-c253/corpus.json'
inputs=json.loads((base/'INPUT-BINDINGS.json').read_text())['inputs']
results=[]

def test(name,mutate,expect=True):
    with tempfile.TemporaryDirectory(prefix='authority-',dir=base) as directory:
        root=Path(directory)
        for item in inputs:
            target=root/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(repo/item['path'],target)
        mutate(root)
        failure=None
        try:m.load_corpus(root);rejected=False
        except m.Fault as e:rejected=True;failure={'code':e.code,'detail':e.detail}
        results.append({'name':name,'expectedRejected':expect,'rejected':rejected,'passed':rejected is expect,'fault':failure})

test('unchanged-corpus',lambda r:None,False)

def source_only(r):
 p=r/'docs/engineering/semantic-export-c210/evidence/proof/before.main.ok';p.write_bytes(p.read_bytes()+b'\n')
test('raw-source-byte-change',source_only)

def coordinated(r):
 p=r/corpus_path;x=json.loads(p.read_text());row=x['files']['start_065'];f=r/row['path']
 raw=f.read_bytes().replace(b'0.65[m]',b'0.64[m]');f.write_bytes(raw)
 row['sha256']=hashlib.sha256(raw).hexdigest();row['bytes']=len(raw)
 x['oracle']['originalTolerances']['delivery_position_component_tolerance_m']=1.
 p.write_text(json.dumps(x,indent=2))
test('coordinated-source-manifest-tolerance-tamper',coordinated)

def loosen(r):
 p=r/corpus_path;x=json.loads(p.read_text());x['oracle']['originalTolerances']['geometry_dimension_tolerance_m']=1e-3;p.write_text(json.dumps(x))
test('corpus-tolerance-change',loosen)
for suffix in ['SCORING.md','PROTOCOL.md','RUN-PLAN.json']:
 def change(r,suffix=suffix):
  p=r/'docs/engineering/localized-repair-c253'/suffix;p.write_bytes(p.read_bytes()+b'\n')
 test('frozen-authority-change-'+suffix,change)

def weaken_spec(r):
 p=r/'docs/language-design/OK-LANG-001-core-language-specification.md';p.write_bytes(p.read_bytes().replace(b'rigid.origin',b'rigid.other'))
test('core-origin-contract-tamper',weaken_spec)

def symlink(r):
 p=r/'docs/engineering/semantic-export-c210/evidence/proof/before.main.ok';q=p.with_name('same-bytes.ok');p.rename(q);p.symlink_to(q.name)
test('corpus-input-symlink',symlink)

def missing(r):
 (r/'docs/engineering/semantic-export-c210/evidence/proof/hinges.ok').unlink()
test('missing-dependency',missing)

syntax=ast.parse(path.read_text())
imports=[];unsafe_calls=[]
for node in ast.walk(syntax):
 if isinstance(node,ast.Import):imports.extend(a.name.split('.')[0] for a in node.names)
 if isinstance(node,ast.ImportFrom):imports.append((node.module or '').split('.')[0])
 if isinstance(node,ast.Call):
  name=ast.unparse(node.func)
  if name in ('eval','exec','__import__') or name.startswith(('subprocess.','os.system','os.exec','os.spawn','importlib.','socket.','urllib.','requests.')):unsafe_calls.append(name)
stdlib_ok=all(s in sys.stdlib_module_names or s=='__future__' for s in imports)
record={'schema':'ontokin.c255.independent-authority-controls/0.1','oracleSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'results':results,'imports':sorted(set(imports)),'standardLibraryOnly':stdlib_ok,'prohibitedExecutionCalls':unsafe_calls,
        'passed':all(r['passed'] for r in results) and stdlib_ok and not unsafe_calls,
        'limits':'Static import/execution inspection plus actual load tests. Does not prove caller isolation/authentication or native execution.'}
(base/'authority-control-results.json').write_text(json.dumps(record,indent=2))
print(json.dumps({'passed':record['passed'],'file_controls':len(results),'failures':[r for r in results if not r['passed']], 'imports':record['imports'],'prohibitedExecutionCalls':unsafe_calls}))
