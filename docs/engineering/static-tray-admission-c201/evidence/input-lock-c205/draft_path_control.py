"""Independent CPU-only check of draft C205 path ancestry."""
from pathlib import Path
import sys, tempfile, hashlib, json, os, datetime
sys.dont_write_bytecode = True
repo = Path('/workspace/scratch/4ba2fd100db8/repo')
sys.path.insert(0, str(repo))
from prototypes.static_tray_admission_c201 import input_lock as mod
out = Path(__file__).parent
source = Path(mod.__file__)
before = source.read_bytes()
(out/'input_lock.draft-observed.py.txt').write_bytes(before)
with tempfile.TemporaryDirectory(prefix='c205-independent-path-') as d:
    root = Path(d)/'repository'; root.mkdir()
    nested = root/'output'; nested.mkdir()
    spelling = '/' + str(nested)
    report = {'schema':'ontokin.c205.independent-draft-path-control/0.1',
        'observedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sourceSha256':hashlib.sha256(before).hexdigest(),
        'repoPath':str(root), 'nestedOutputSpelling':spelling,
        'actualNested':nested.is_relative_to(root),
        'distinctInodes':root.stat().st_ino != nested.stat().st_ino,
        'expected':'REJECT_ABSOLUTE_OR_DISJOINT', 'nativeStarts':0}
    try:
        got = mod._absolute(spelling)
        mod._check_disjoint([root,got])
        report['observed']='ACCEPTED_NESTED_DOUBLE_SLASH_PATH'
        report['passes']=False
    except mod.InputLockError as exc:
        report['observed']='REJECTED';report['errorCode']=exc.code;report['passes']=True
report['sourceUnchangedDuringControl']=source.read_bytes()==before
(out/'draft-path-control.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
