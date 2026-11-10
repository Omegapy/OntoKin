#!/usr/bin/env python3
"""Read recovered C194 artifacts without constructing or resimulating scenes."""
import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile
import time

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--evidence-root', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
BASE = args.evidence_root.resolve()
REPO = args.repo.resolve()
OUT = args.out.resolve()
if OUT.is_relative_to(BASE) or OUT.is_relative_to(REPO):
    raise ValueError('Replay output must be outside sealed evidence and repository')
OUT.mkdir(parents=True, exist_ok=False)
ORIGINAL = Path(json.loads((BASE/'c194-preparation-run/EXECUTION-LEDGER.json').read_text())['output']).parent

def relocated(path):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Expected original absolute provenance path: '+str(path))
    relative = path.relative_to(ORIGINAL)
    parts = relative.parts
    if parts[0] == 'authors':
        if parts[1] not in ('ok','python'):
            raise ValueError('Unknown original author root')
        target = REPO.joinpath(*parts[2:])
    elif parts[0] in ('ontokin', 'c194-prep-worktree'):
        target = REPO.joinpath(*parts[1:])
    else:
        target = BASE/relative
    resolved = target.resolve()
    if not (resolved.is_relative_to(REPO) or resolved.is_relative_to(BASE)):
        raise ValueError('Provenance relocation escaped roots')
    return resolved

PREP = REPO / 'docs/engineering/contact-preparation-c194'
PUBLIC = REPO / 'docs/engineering/contact-comparison-c194'
KEYS = ['canonical-input.json', 'native-transforms.json', 'raw.glb', 'final.glb']
checks = []
reports = []

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def check(test, name, **extra):
    checks.append(dict(name=name, passed=bool(test), **extra))
    if not test:
        raise AssertionError(name)

def write(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')

def import_path(name, p):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m

start=datetime.now(timezone.utc).isoformat()
sys.path.insert(0,str(PREP))
c=import_path('c194_recovery_common',PREP/'common.py')
check(c.verify_freeze()['passed'], 'C194 preparation freeze verifies all 589 files')
reader=c.artifact_reader()
sys.modules['check_artifact']=reader
provenance_reader=import_path('c194_replay_provenance',c.C193/'independent/audit_provenance.py')
historical=reader.verify_frozen()
check(historical['passed'],'C193 inherited frozen checker inputs verify',historical_files_verified=historical['historical_files_verified'])

for root in [REPO]:
    manifest=read(root/'docs/engineering/contact-comparison-c194/frozen/INPUTS.json')
    for row in manifest['files']:
        p=root/row['path']
        check(p.stat().st_size==row['bytes'] and digest(p)==row['sha256'],
              'Public frozen input preserved',root=str(root),path=row['path'])
    freeze=read(root/'docs/engineering/contact-comparison-c194/frozen/FREEZE.json')
    check(digest(root/'docs/engineering/contact-comparison-c194/frozen/INPUTS.json')==freeze['input_manifest_sha256'],
          'Public manifest seal matches',root=str(root))

prep_freeze=read(PREP/'FREEZE.json')
public_freeze=read(PUBLIC/'frozen/FREEZE.json')
prep_result=read(BASE/'c194-preparation-run/RESULTS.json')
first=read(BASE/'c194-first-validation/RESULTS.json')
reuse=read(BASE/'c194-reuse-validation/RESULTS.json')
qualification=read(BASE/'c194-preparation-run/QUALIFICATION.json')
acceptance=read(BASE/'c194-first-validation/ACCEPTANCE.json')
check(prep_freeze['created_utc']<prep_result['started_utc'],'Preparation freeze precedes all native builds')
check(digest(BASE/'c194-preparation-run/RESULTS.json')==qualification['results_sha256'] and digest(BASE/'c194-preparation-run/VISUAL-REVIEW.json')==qualification['visual_review_sha256'], 'Qualification binds numerical and visual receipts')
check(digest(BASE/'c194-preparation-run/QUALIFICATION.json')==public_freeze['preparation_qualification_sha256'],'Public freeze binds passing qualification')
check(qualification['passed'] and qualification['qualified_for_author_dispatch'],'Both targets qualified before public freeze')
ledger=read(BASE/'c194-preparation-run/EXECUTION-LEDGER.json')
check([x['id'] for x in ledger['started_builds']]==['ok-G','python-G','ok-H','python-H'],'Exactly four reserved preparation builds executed')
check(ledger['results_sha256']==digest(BASE/'c194-preparation-run/RESULTS.json'),'Preparation ledger binds completed results')
dispatch=read(PUBLIC/'evidence/AUTHOR-DISPATCH.json')
check(len(dispatch['authors'])==2 and {x['route'] for x in dispatch['authors']}=={'ok','python'},'Recorded dispatch has exactly two route authors')
check(dispatch['requested_settings']=={'fork_turns':'none','model_override':None,'reasoning_override':None},'Recorded launch settings have empty histories and no overrides')

artifacts=[]
reopens=[]
for stage,result in [('preparation',prep_result),('first',first),('reuse',reuse)]:
    stage_dir=BASE/('c194-preparation-run' if stage=='preparation' else f'c194-{stage}-validation')
    check(result['automated_gates_passed'],'Recorded automatic stage passes',stage=stage)
    for r in result['runs']:
        artifact=Path(r['artifact'])
        artifact=relocated(artifact) if artifact.is_absolute() else stage_dir/artifact
        check(r['passed'] and not r['failures'],'Run has no recorded failed gate',stage=stage,id=r['id'])
        for key,sha in r['artifacts'].items():check(digest(artifact/key)==sha,'Original artifact hash matches retained result',stage=stage,id=r['id'],file=key)
        native=read(artifact/'native-transforms.json')
        reopened=read(stage_dir/'reopens'/r['id']/'native-transforms.json')
        summary=read(stage_dir/'reopens'/r['id']/'summary.json')
        check(len(native)==481 and native==reopened,'Actual saved-scene replay has all 481 exact records',stage=stage,id=r['id'])
        check(summary['pass'] and summary['samples']==481 and summary['configuration_unchanged'] and not summary['reconstructed_or_repaired'],'Scene replay performed no reconstruction/repair',stage=stage,id=r['id'])
        check(summary['opened_scene_sha256']==digest(artifact/'scene.blend'),'Replay opened the actual submitted scene',stage=stage,id=r['id'])
        check(digest(stage_dir/'reopens'/r['id']/'summary.json')==r['reopen']['summary_sha256'],'Replay summary hash matches retained result',stage=stage,id=r['id'])
        check(digest(stage_dir/'reopens'/r['id']/'configuration-before.json')==r['reopen']['configuration_sha256'],'Replay configuration hash matches retained result',stage=stage,id=r['id'])
        reopens.append({'stage':stage,'id':r['id'],'samples':481,'exact':True})
        artifacts.append((stage,r['id'],r['case'],artifact))
        if stage!='preparation':
            build=stage_dir/'builds'/r['id']
            candidates=list((build/'store/artifacts').glob('*')) if r['route']=='ok' else [build/'artifact']
            check(len(candidates)==1,'One clean coordinator rebuild retained',stage=stage,id=r['id'])
            rebuilt=candidates[0]
            for key in KEYS:check((artifact/key).read_bytes()==(rebuilt/key).read_bytes(),'Coordinator rebuild exact equality',stage=stage,id=r['id'],file=key)
            artifacts.append((stage+'-rebuild',r['id'],r['case'],rebuilt))
    receiving=stage_dir/'receiving'
    receiver_summary=read(receiving/'summary.json')
    check(receiver_summary['pass_for_executed_receiving_checks'] and receiver_summary['khronos_errors']==0 and receiver_summary['khronos_warnings']==0,'Receiving numerical/format checks pass',stage=stage)
    for row in read(receiving/'artifact-identities.json'):
        check(digest(receiving/row['path'])==row['sha256']==digest(relocated(row['source'])),'Receiver inspected actual delivered bytes',stage=stage,path=row['path'])
    khronos=read(receiving/'khronos.json')
    check(len(khronos)==receiver_summary['glb_paths'],'Khronos receipt has expected complete path inventory',stage=stage)
    for path,entry in khronos.items():
        check(digest(receiving/path)==entry['sha256'],'Khronos receipt binds exact inspected artifact',stage=stage,path=path)
        issues=entry['report']['issues']
        check(issues['numErrors']==0 and issues['numWarnings']==0,'Actual Khronos receipt has no errors or warnings',stage=stage,path=path)
    check(sum(r['report']['issues']['numInfos'] for r in khronos.values())==receiver_summary['khronos_infos'],'Informational findings accounted separately',stage=stage)
    for kind in ['khronos','three','blender']:
        command=read(receiving/'commands'/f'{kind}.json')
        check(command['completed'] and command['returncode']==0 and command['pass'],'Receiving command completed successfully',stage=stage,kind=kind)
    three=read(receiving/'three.json')
    check(three['pass'] and three['threeRevision']=='186','Three.js pinned readback passed',stage=stage)
    for report in three['reports']:
        check(digest(receiving/report['path'])==report['sha256'] and len(report['poses'])==3,'Three.js bound actual artifact and three poses',stage=stage,id=report['id'])
    for job in sorted((receiving/'renders').glob('*/receipt.json')):
        data=read(job)
        check(data['input_sha256']==digest(relocated(data['input_glb'])) and data['all_sampled_imports_match_glb'] and len(data['frames'])==3,'Blender receiving receipt binds actual input and three poses',stage=stage,id=data['label'])

for stage,identifier,case,artifact in artifacts:
    provenance=provenance_reader.audit(artifact,c.CONTRACT,c.C193/'independent/evidence/candidate-review.json')
    check(provenance['passed'],'Frozen executed implementation and complete artifact provenance passes',stage=stage,id=identifier)
    write(OUT/(stage+'-'+identifier+'-provenance.json'),provenance)
    result=reader.review(artifact,case,c.CONTRACT/'backend.json',c.BACKEND_SHA,c.SOURCE_BINDING)
    filename=stage+'-'+identifier+'.json'
    write(OUT/filename,result)
    check(result['passed'] and not result['failures'],'Fresh recorded-artifact checker passes',stage=stage,id=identifier)
    bound=result['mapping_measurements']['maximumContinuousRawToFinalVertexDeviationBoundMm']
    peak=result['diagnosis']['peak']['distance_mm']
    check(bound<=0.2 and peak<=0.2,'Unchanged mapping gate passes',stage=stage,id=identifier,bound_mm=bound,peak_mm=peak)
    reports.append(dict(stage=stage,id=identifier,case=case,artifact=str(artifact),report=filename,report_sha256=digest(OUT/filename),continuous_bound_mm=bound,native_peak_mm=peak))
    print('audited',stage,identifier,bound,flush=True)

# Compare actual route bytes, including every clean rebuild and regeneration.
for case in ['G','H']:
    peers=[a for _,_,cse,a in artifacts if cse==case]
    for key in KEYS:
        check(len({digest(a/key) for a in peers})==1,'Exact route, preparation, author and rebuild equality',case=case,file=key)
baseline_info=prep_result['baseline']
baseline_archive=REPO/baseline_info['archive']
check(digest(baseline_archive)==baseline_info['sha256'],'Retained historical right-lane baseline archive matches')
with tarfile.open(baseline_archive,'r:*') as archive:
    baseline=json.load(archive.extractfile(baseline_info['member']))
for stage,identifier,case,artifact in artifacts:
    native=read(artifact/'native-transforms.json')
    for part in ['base','right_carriage','right_shoe','right_stop']:
        for field in ['matrices_blender_m','bounds_gltf_mm']:
            check([r[field][part] for r in native]==[r[field][part] for r in baseline],
                  'Unrelated native part equals retained historical baseline',stage=stage,id=identifier,part=part,field=field)

source_diffs=[]
accounting=[]
for route,ext in [('ok','ok'),('python','py')]:
    author=REPO/'docs/engineering/contact-comparison-c194/authors'/route
    starter=(PREP/'starters'/f'gauge.{ext}').read_text()
    first_source=(author/f'first.{ext}').read_text()
    reuse_source=(author/f'reuse.{ext}').read_text()
    # Single literal delta is verified against independently frozen target source.
    check(first_source==(PREP/'sources'/f'G.{ext}').read_text() and reuse_source==(PREP/'sources'/f'H.{ext}').read_text(),'Author sources equal independently frozen one-coordinate designs',route=route)
    for name,before,after in [('first',starter,first_source),('reuse',first_source,reuse_source)]:
        changes=[op for op in difflib.SequenceMatcher(a=before,b=after).get_opcodes() if op[0]!='equal']
        check(len(changes)==1 and changes[0][0]=='replace','Only one source text span changes',route=route,phase=name)
        op,i,j,k,l=changes[0]
        source_diffs.append(dict(route=route,phase=name,before=before[i:j],after=after[k:l]))
    for phase in ['FIRST','REUSE']:
        sub=read(author/f'SUBMISSION-{phase}.json')
        acc_ref=sub['accounting'] if route=='ok' else sub['author_accounting']
        acc=read(relocated(acc_ref['path']))
        check(digest(relocated(acc_ref['path']))==acc_ref['sha256'],'Author accounting bound to submission',route=route,phase=phase)
        started=acc.get('phase_started_utc',acc.get('phase_start_utc'))
        submitted=acc.get('submitted_utc',acc.get('submission_utc'))
        check(public_freeze['created_utc']<started,'Public freeze precedes author phase',route=route,phase=phase)
        if phase=='REUSE':check(acceptance['accepted_utc']<started,'First phase accepted before same-author reuse',route=route)
        elapsed=(datetime.fromisoformat(submitted)-datetime.fromisoformat(started)).total_seconds()
        check(0<=elapsed<=1200,'Author phase inside 20 minute allowance',route=route,phase=phase,elapsed_s=elapsed)
        counts=acc.get('counts',{})
        accounting.append(dict(route=route,phase=phase,started_utc=started,submitted_utc=submitted,elapsed_s=elapsed,
            formal_submissions=counts.get('formal_submissions_including_this',acc.get('formal_submissions_used')),
            native_attempts=counts.get('native_build_attempts_including_failures',acc.get('native_build_attempts_used')),
            formal_repairs=counts.get('formal_repairs',acc.get('formal_repair_turns')),
            failed_commands=acc.get('failed_commands',[]),provider_telemetry=acc.get('provider_telemetry')))

# First accepted artifact and author source remain identical after reuse.
for old in first['runs']:
    r=next(x for x in reuse['runs'] if x['id']==old['route']+'-first-regenerated')
    for key in KEYS:check((relocated(old['artifact'])/key).read_bytes()==(relocated(r['artifact'])/key).read_bytes(),'Reuse exactly regenerates first accepted output',route=old['route'],file=key)

# Validate immutable receiver visual receipts and dated recovery acceptance.
visual_checks=[]
for receipt,base,expected in [
    (BASE/'c194-preparation-run/VISUAL-REVIEW.json',BASE/'c194-preparation-run/receiving',12),
    (BASE/'c194-first-validation/VISUAL-REVIEW.json',BASE/'c194-first-validation/receiving',6),
    (BASE/'recovery/REUSE-VISUAL-REVIEW.json',BASE,12)]:
    visual=read(receipt)
    check(visual['pass'] and len(visual['panels'])==expected,'Bound visual review has expected passing panel count',receipt=str(receipt))
    check(len({r['path'] for r in visual['panels']})==expected,'Bound visual review has unique panels',receipt=str(receipt))
    for row in visual['panels']:
        path=(base/row['path']).resolve()
        check(path.is_relative_to(BASE) and path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],'Visual review binds exact original image',path=row['path'])
    visual_checks.append({'receipt':str(receipt.relative_to(BASE)),'sha256':digest(receipt),'panels':expected})
check(digest(BASE/'c194-first-validation/RESULTS.json')==acceptance['results_sha256'] and digest(BASE/'c194-first-validation/VISUAL-REVIEW.json')==acceptance['visual_review_sha256'],'First acceptance binds completed results and visual review')
source_accounting=read(BASE/'recovery/REUSE-SOURCE-ACCOUNTING-REVIEW.json')
check(source_accounting['passed'],'Recovery source/accounting review passes')
for row in source_accounting['reference_checks']:
    path=relocated(row['path'])
    check(path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],'Retained source/accounting reference unchanged',path=row['path'])
for stage,result in [('first',first),('reuse',reuse)]:
    for row in result['runs']:
        run=relocated(row['submitted_run'])
        snapshot=read(BASE/f'c194-{stage}-validation/inventories'/f"{row['id']}-before.json")
        actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
        check(actual==set(snapshot),'Submitted-run exact inventory preserved',stage=stage,id=row['id'])
        for name,identity in snapshot.items():
            path=run/name
            check(path.stat().st_size==identity['bytes'] and digest(path)==identity['sha256'],'Submitted-run exact bytes preserved',stage=stage,id=row['id'],file=name)
recovery=read(BASE/'recovery/REUSE-ACCEPTANCE.json')
check(recovery['accepted'] and recovery['phase']=='reuse','Recovered reuse acceptance is affirmative for correct phase')
check(recovery['results_sha256']==digest(BASE/'c194-reuse-validation/RESULTS.json'),'Recovered reuse acceptance binds original results')
check(recovery['visual_review_sha256']==digest(BASE/'recovery/REUSE-VISUAL-REVIEW.json'),'Recovered reuse acceptance binds dated visual review')
check(recovery['source_accounting_review_sha256']==digest(BASE/'recovery/REUSE-SOURCE-ACCOUNTING-REVIEW.json'),'Recovered reuse acceptance binds independent source/accounting review')
check(recovery['authors']==source_accounting['author_heads'],'Reuse acceptance identifies recovered original author heads')
accepted={r['id']:r for r in recovery['sources_and_artifacts']}
check(set(accepted)=={r['id'] for r in reuse['runs']},'Reuse acceptance covers all four delivered runs')
for row in reuse['runs']:
    a=accepted[row['id']]
    check(a['source_sha256']==row['source_sha256'] and a['artifacts']==row['artifacts'],'Reuse acceptance binds actual delivered identities',id=row['id'])
check(reuse['visual_review']=='PENDING','Original unfinished reuse result preserved without relabeling')
summary={'schema':'ontokin.c194.portable-recorded-replay/0.1','started_utc':start,'finished_utc':datetime.now(timezone.utc).isoformat(),
 'passed':True,'source_root':str(REPO),'evidence_root':str(BASE),'original_provenance_root':str(ORIGINAL),
 'new_native_builds':0,'new_native_replays':0,'new_authors':0,'new_receiving_executions':0,
 'checks_passed':len(checks),'fresh_recorded_artifact_checks':reports,'scene_replay_receipts_verified':reopens,
 'visual_receipts_verified':visual_checks,'source_diffs':source_diffs,'author_accounting':accounting,
 'preparation_result_sha256':digest(BASE/'c194-preparation-run/RESULTS.json'),
 'first_result_sha256':digest(BASE/'c194-first-validation/RESULTS.json'),
 'reuse_result_sha256':digest(BASE/'c194-reuse-validation/RESULTS.json'),
 'reuse_acceptance_sha256':digest(BASE/'recovery/REUSE-ACCEPTANCE.json'),
 'scope':'Frozen recorded artifact/source/configuration checks and retained scene/receiver/visual/acceptance receipts; no native or destination execution',
 'limits':['Provider model snapshot, hidden turns, tokens and cost remain unavailable','Legacy FAILED regression disposition and full-product gates remain unchanged','Script verifies prior visual observations and exact image identities; it does not itself view images'],
 'all_checks':checks}
write(OUT/'REPLAY-RESULT.json',summary)
print(json.dumps({'passed':True,'checks':len(checks),'recorded_artifacts':len(reports),'replay_receipts':len(reopens),'visual_panels':30}),flush=True)
