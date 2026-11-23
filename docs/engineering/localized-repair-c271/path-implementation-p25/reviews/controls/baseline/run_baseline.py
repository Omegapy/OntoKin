"""Run only five inherited inert inspector cohorts against frozen baseline bytes."""
from contextlib import ExitStack
import hashlib, importlib, json, os, platform, subprocess, sys, time, types, unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
MODULE = 'prototypes.static_tray_v01.current_host_inspection_v01'
SOURCE = REPO / 'prototypes/static_tray_v01/current_host_inspection_v01.py'
NAMES = ['test_current_host_inspection_v01','test_current_host_elf_mapping_v01','test_current_host_loader_path_v01','test_current_host_libc_plt_metadata_v01','test_current_host_libc_static_tls_flags_v01']
sys.path[:0] = [str(REPO), str(REPO / 'tests')]
raw = (HERE / 'inspector.py.source').read_bytes()
inputs = [SOURCE, *[REPO / 'tests' / (n+'.py') for n in NAMES]]
for d in ['tests/fixtures/current_host_elf_mapping_v01','docs/engineering/localized-repair-c271/loader-path-p11/design/candidate004','docs/engineering/localized-repair-c271/review-boundary-p13/design/candidate001','docs/engineering/localized-repair-c271/current-host-p06']:
 inputs.extend(p for p in (REPO/d).rglob('*') if p.is_file())
inputs += [REPO / 'docs/engineering/localized-repair-c271/libc-tags-p16/design/candidate001/CANDIDATE001.zip', REPO / 'docs/engineering/localized-repair-c271/libc-flags-p17/design/CANDIDATE001.zip']
def identity(p):
 b=p.read_bytes();return {'path':str(p.relative_to(REPO)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
record={'schema':'ontokin.c271.p25.bounded-baseline/1','source_commit':'ce411b12e601036a33698aa7c3290722e602ea75','source_snapshot':identity(HERE/'inspector.py.source'),'command':sys.orig_argv,'cwd':os.getcwd(),'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'time_started':time.time(),'tests':NAMES,'inputs':[identity(p) for p in inputs if p.is_file()],'actual_target_starts':0,'scope':'Five inherited synthetic/mocked inspector cohorts only; no H0/H1, original seven, full routine, host qualification or operational target execution.'}
(HERE/'INPUTS.json').write_text(json.dumps(record,indent=2)+'\n')
package=importlib.import_module('prototypes.static_tray_v01')
baseline=types.ModuleType(MODULE);baseline.__file__=str(SOURCE);baseline.__package__='prototypes.static_tray_v01'
sys.modules[MODULE]=baseline;setattr(package,'current_host_inspection_v01',baseline)
exec(compile(raw,str(SOURCE),'exec'),baseline.__dict__)
process_attempts=[]
def forbidden(*a,**k):
 process_attempts.append({'args':repr(a),'kwargs':repr(k)});raise AssertionError('Actual process operation forbidden in bounded P25 baseline')
with ExitStack() as stack:
 for name in ('Popen','run','check_output','check_call','call'):
  stack.enter_context(patch.object(subprocess,name,side_effect=forbidden))
 for name in ('system','fork','posix_spawn','posix_spawnp','killpg','waitpid'):
  if hasattr(os,name):stack.enter_context(patch.object(os,name,side_effect=forbidden))
 suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in NAMES)
 with (HERE/'TEST.log').open('w') as log:
  result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
record.update(time_finished=time.time(),tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),process_attempts=process_attempts,successful=result.wasSuccessful(),code_snapshot_sha256=hashlib.sha256(raw).hexdigest())
(HERE/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ['tests_run','failures','errors','skipped','successful','process_attempts','code_snapshot_sha256']}))
sys.exit(not result.wasSuccessful())
