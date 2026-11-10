from __future__ import annotations

import datetime
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

REPO = Path('/workspace/scratch/40c44e911c4b/OntoKin')
ORIGINAL = Path('/workspace/scratch/efc86516cbb7')
OUT = Path('/workspace/scratch/91d3a54fe1aa/audits')
C = REPO / 'docs/engineering/contact-comparison-c194'
E = C / 'evidence'
checks = []

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def check(name, condition, **details):
    checks.append(dict(name=name, passed=bool(condition), **details))

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()

archive_summary = []
archive_index = read(E / 'EVIDENCE-ARCHIVES.json')
for row in archive_index['archives']:
    archive = E / row['archive']
    manifest_path = E / row['manifest']
    check('Archive exact bytes: ' + row['id'], archive.stat().st_size == row['bytes'] and digest(archive) == row['sha256'])
    check('Manifest exact bytes: ' + row['id'], digest(manifest_path) == row['manifest_sha256'])
    manifest = read(manifest_path)
    files = manifest['files']
    seen = set()
    content_bytes = 0
    with tarfile.open(archive, 'r:xz') as tf:
        for member in tf:
            if member.isdir():
                continue
            check('Unique regular archive member: ' + member.name, member.isfile() and member.name not in seen)
            seen.add(member.name)
            rec = files.get(member.name)
            check('Declared member: ' + member.name, rec is not None)
            if rec is None or not member.isfile():
                continue
            data = tf.extractfile(member).read()
            content_bytes += len(data)
            check('Exact archived member: ' + member.name, len(data) == rec['bytes'] and hashlib.sha256(data).hexdigest() == rec['sha256'])
            if 'source_path' in rec:
                p = Path(rec['source_path'])
                check('Original completion file unchanged: ' + member.name, p.is_file() and p.stat().st_size == rec['bytes'] and digest(p) == rec['sha256'])
    check('Archive set complete: ' + row['id'], seen == set(files))
    archive_summary.append(dict(id=row['id'], files=len(files), uncompressed_bytes=content_bytes, sha256=digest(archive)))

first_original = ORIGINAL / 'c194-first-validation/RESULTS.json'
reuse_original = ORIGINAL / 'c194-reuse-validation/RESULTS.json'
prep_original = ORIGINAL / 'c194-preparation-run/RESULTS.json'
first = read(first_original)
reuse = read(reuse_original)
prep = read(prep_original)
check('Original reuse result remains byte-identical', digest(reuse_original) == digest(E / 'REUSE-RESULTS.json'))
check('Original reuse pending status preserved', reuse['visual_review'] == 'PENDING')
check('Original preparation result remains byte-identical', digest(prep_original) == digest(E / 'preparation-RESULTS.json'))
check('Exactly four preparation runs', len(prep['runs']) == 4)
check('Exactly two first and four reuse/regeneration runs', len(first['runs']) == 2 and len(reuse['runs']) == 4)

phase_inputs = [('preparation', prep, ORIGINAL / 'c194-preparation-run'), ('first', first, ORIGINAL / 'c194-first-validation'), ('reuse', reuse, ORIGINAL / 'c194-reuse-validation')]
run_summary = []
for phase, doc, phase_root in phase_inputs:
    check('Recorded automated gates: ' + phase, doc['automated_gates_passed'])
    for run in doc['runs']:
        artifact = Path(run['artifact'])
        if not artifact.is_absolute():
            artifact = phase_root / artifact
        check('Recorded run accepted by fixed numerical gates: ' + run['id'], run['passed'] and not run['failures'])
        for filename, sha256 in run['artifacts'].items():
            check('Submitted artifact exact: ' + run['id'] + '/' + filename, digest(artifact / filename) == sha256)
        native = read(artifact / 'native-transforms.json')
        reopen_path = phase_root / 'reopens' / run['id']
        reopened = read(reopen_path / 'native-transforms.json')
        check('Exact 481 samples after recorded reopen: ' + run['id'], len(native) == len(reopened) == 481 and native == reopened)
        for filename, key in [('native-transforms.json','reopened_trace_sha256'), ('summary.json','summary_sha256'), ('configuration-before.json','configuration_sha256')]:
            check('Reopen receipt identity: ' + run['id'] + '/' + filename, digest(reopen_path / filename) == run['reopen'][key])
        artifact_report = read(phase_root / 'reports' / (run['id'] + '-artifact.json'))
        check('Saved independent artifact report passed: ' + run['id'], artifact_report['passed'] and not artifact_report['failures'])
        mapping = artifact_report['mapping']
        bound = mapping['maximumContinuousRawToFinalVertexDeviationBoundMm']
        peak = mapping['maximumNativeSampleToFinalVertexDistanceMm']
        check('Unchanged 0.2 mm continuous gate: ' + run['id'], bound <= 0.2)
        if phase != 'preparation':
            check('Reported measurements match saved mapping: ' + run['id'], bound == run['continuous_bound_mm'] and peak == run['native_peak_mm'])
            candidates = list((phase_root / 'builds' / run['id']).rglob('canonical-input.json'))
            check('Unique coordinator rebuild: ' + run['id'], len(candidates) == 1)
            if len(candidates) == 1:
                rebuilt = candidates[0].parent
                for filename in run['artifacts']:
                    check('Coordinator rebuild exact: ' + run['id'] + '/' + filename, digest(rebuilt / filename) == digest(artifact / filename))
        run_summary.append(dict(phase=phase, id=run['id'], case=run['case'], continuous_bound_mm=bound, native_peak_mm=peak, artifact=str(artifact), final_glb_sha256=digest(artifact/'final.glb')))

first_accept = read(E / 'FIRST-ACCEPTANCE.json')
reuse_accept = read(E / 'recovery/REUSE-ACCEPTANCE.json')
qual = read(E / 'preparation-QUALIFICATION.json')
check('Preparation qualification accepted', qual['passed'] and qual['qualified_for_author_dispatch'])
check('Preparation exact results binding', qual['results_sha256'] == digest(prep_original))
check('Preparation visual binding', qual['visual_review_sha256'] == digest(E/'preparation-VISUAL-REVIEW.json'))
check('First explicit acceptance', first_accept['accepted'])
check('First result binding', first_accept['results_sha256'] == digest(first_original))
check('First visual binding', first_accept['visual_review_sha256'] == digest(E/'FIRST-VISUAL-REVIEW.json'))
check('Reuse explicit acceptance', reuse_accept['accepted'])
check('Reuse result binding', reuse_accept['results_sha256'] == digest(reuse_original))
check('Reuse visual binding', reuse_accept['visual_review_sha256'] == digest(E/'recovery/REUSE-VISUAL-REVIEW.json'))
check('Reuse source/accounting binding', reuse_accept['source_accounting_review_sha256'] == digest(E/'recovery/REUSE-SOURCE-ACCOUNTING-REVIEW.json'))
check('Reuse bound to first acceptance', reuse_accept['first_acceptance_sha256'] == digest(E/'FIRST-ACCEPTANCE.json'))
check('Reuse acceptance binds all four exact rows', reuse_accept['sources_and_artifacts'] == reuse['runs'])
check('No replacement author/native trial in recovery', reuse_accept['new_native_builds_during_recovery'] == 0 and reuse_accept['new_author_dispatches_during_recovery'] == 0)

visual_summary = []
visual_specs = [('preparation', E/'preparation-VISUAL-REVIEW.json', ORIGINAL/'c194-preparation-run/receiving'), ('first', E/'FIRST-VISUAL-REVIEW.json', ORIGINAL/'c194-first-validation/receiving'), ('reuse', E/'recovery/REUSE-VISUAL-REVIEW.json', ORIGINAL)]
for phase, path, root in visual_specs:
    v = read(path)
    check('Recorded visual acceptance: ' + phase, v['pass'])
    for panel in v['panels']:
        p = root / panel['path']
        check('Original reviewed image exact: ' + phase + '/' + panel['path'], p.stat().st_size == panel['bytes'] and digest(p) == panel['sha256'])
    visual_summary.append(dict(phase=phase, panels=len(v['panels']), receipt_sha256=digest(path)))

source_deltas = []
for route, ext in [('ok','ok'),('python','py')]:
    starter = REPO/f'docs/engineering/contact-preparation-c194/starters/gauge.{ext}'
    first_source = C/f'authors/{route}/first.{ext}'
    reuse_source = C/f'authors/{route}/reuse.{ext}'
    for phase, before, after, a, b in [('first',starter,first_source,'380','365'),('reuse',first_source,reuse_source,'365','375')]:
        x,y=before.read_text(),after.read_text()
        dif = list(difflib.ndiff(x.splitlines(),y.splitlines()))
        removed=[l[2:] for l in dif if l.startswith('- ')]
        added=[l[2:] for l in dif if l.startswith('+ ')]
        check('Single coordinate-only source edit: '+route+'/'+phase, len(removed)==len(added)==1 and removed[0].replace(a,b)==added[0])
        source_deltas.append(dict(route=route,phase=phase,before=removed,after=added,sha256=digest(after)))

history = read(E/'original-worker-history.json')
check('Original history bundle exact', digest(E/history['file']) == history['sha256'] and (E/history['file']).stat().st_size == history['bytes'])
check('Exactly fifteen original C194 commits', len(git('rev-list','fae25ca94d882a67f9fd5d352e1923035b96fe6b','^3c9fcaa4daff7b32e7b813ba05041212c1a5bc2f').splitlines()) == 15)
for ref, sha in history['heads'].items():
    check('Original head retained: '+ref, git('rev-parse',ref)==sha)

receiving_summary=[]
for phase,doc,_ in phase_inputs:
    s=doc['receiving']['summary']
    check('Recorded receiving checks passed: '+phase, doc['receiving']['passed'] and s['khronos_errors']==s['khronos_warnings']==0)
    receiving_summary.append(dict(phase=phase,paths=s['glb_paths'],three_poses=s['three_poses'],khronos_errors=s['khronos_errors'],khronos_warnings=s['khronos_warnings']))

accounting=read(E/'recovery/REUSE-SOURCE-ACCOUNTING-REVIEW.json')
check('Preparation before authors and first acceptance before reuse recorded', accounting['qualified_before_dispatch'] and accounting['first_acceptance_precedes_both_reuse_phases'])
check('Same exactly two original authors recorded', accounting['exactly_two_recorded_authors'] and accounting['same_authors_reused_own_accepted_sources'])
check('Author attempt accounting retained', accounting['native_author_builds']==6 and accounting['failed_author_native_builds']==accounting['invalid_author_source_attempts']==accounting['formal_repair_turns']==0)

failed=[c for c in checks if not c['passed']]
report=dict(schema='ontokin.c194.independent-recovery-evidence-audit/0.1',reviewer='c194_evidence',reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=not failed,checks=len(checks),failures=failed,reviewed_local_head=git('rev-parse','HEAD'),source_repo=str(REPO),original_workspace=str(ORIGINAL),new_native_builds=0,new_native_replays=0,new_author_dispatches=0,archives=archive_summary,recorded_runs=run_summary,visual_receipt_inventory=visual_summary,receiving=receiving_summary,source_deltas=source_deltas,original_history=history,acceptance=dict(first_utc=first_accept['accepted_utc'],reuse_utc=reuse_accept['accepted_utc'],first_sha256=digest(E/'FIRST-ACCEPTANCE.json'),reuse_sha256=digest(E/'recovery/REUSE-ACCEPTANCE.json')),remaining=['Commit/publish exact recovered completion tree','Observed-head conditional integration and resulting-main recorded verification','Release integration lease','Assemble and verify self-contained C194 handoff and save it'],limits=['This audit checks saved artifact and receipt bytes and sample equality; it does not claim a new native simulation or new visual review','Preserve inherited failed regression: 4239 distinct passed methods; 13 torque artifact-read methods NOT RUN','Public shared-environment literal-source edit/reuse of one seven-part assembly; no general language advantage, production backend or full release claim'],all_checks=checks)
(OUT/'c194-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['passed','checks','failures','archives','remaining']},indent=2))
