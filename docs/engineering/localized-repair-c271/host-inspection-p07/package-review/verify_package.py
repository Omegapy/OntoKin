#!/usr/bin/env python3
"""Independent inert P07 archive review. No project imports or execution."""
from pathlib import Path, PurePosixPath
import collections
import datetime
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import traceback
import unicodedata
import zipfile
import zlib

BASE = Path('/workspace/scratch/522363862012')
OUT = BASE / 'audit/final-package-review'
REPO = BASE / 'OntoKin'
NAME = 'OntoKin_C271_P07_Host_Inspection_Design_Handoff_2026-11-20'
ARCHIVE = BASE / 'packages' / (NAME + '.zip')
EXPECTED_SHA = 'be774f33019e41fc65011fe3a1014edd36ac3298181b04236583f4e39b88d675'
SOURCE = 'a5622f7fdd5ffb40a387d860e41c2ebbe5291d6f'
TREE = '94df4e85c8ad43a635b07a8d4506308ef7244b5c'
MAIN = 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
MAIN_TREE = '9345594c980f121fae2f087b40e4c78adb8f7925'
BASELINE = '3d9d5eacaff25244916f99912ef92947e1582592'
CANON = 'repository/docs/engineering/localized-repair-c271/host-inspection-p07/'
P06 = BASE / 'source_handoffs/OntoKin/OntoKin_C271_P06_Implementation_Handoff_2026-11-20.zip'
RESULT = {'schema': 'ontokin.c271.p07-independent-package-review/1',
          'reviewer': '/root/intake_review', 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'archive': {'path': str(ARCHIVE), 'expected_bytes': 957300, 'expected_sha256': EXPECTED_SHA},
          'source_commit': SOURCE, 'source_tree': TREE, 'main_commit': MAIN,
          'checks': [], 'mandatory_findings': [], 'notes': [],
          'execution_counts': {'project_imports': 0, 'project_tests': 0, 'Node': 0, 'ldd': 0,
                               'runtime_preparation': 0, 'full_routine': 0, 'native_model_hosted': 0}}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def identity(data, row, size_key='bytes'):
    assert len(data) == row[size_key], ('size mismatch', row)
    assert digest(data) == row['sha256'], ('hash mismatch', row)

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))

def save():
    path = OUT / 'RESULTS.json'
    path.write_text(json.dumps(RESULT, indent=2) + '\n')

def record(name, **details):
    RESULT['checks'].append({'name': name, 'result': 'PASS', **details})
    save()

def check():
    raw_zip = ARCHIVE.read_bytes()
    assert len(raw_zip) == 957300 and digest(raw_zip) == EXPECTED_SHA
    RESULT['archive'].update({'bytes': len(raw_zip), 'sha256': digest(raw_zip)})
    record('immutable archive identity')
    initial_head = git('rev-parse', 'HEAD').decode().strip()
    initial_status = git('status', '--porcelain=v1').decode()
    assert initial_head == SOURCE and initial_status == ''
    with zipfile.ZipFile(ARCHIVE) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        assert len(names) == len(set(names)) == 261
        assert len({unicodedata.normalize('NFC', n).casefold() for n in names}) == len(names)
        for i in infos:
            p = PurePosixPath(i.filename)
            assert i.filename and not p.is_absolute() and str(p) == i.filename
            assert all(x not in ('', '.', '..') for x in i.filename.split('/'))
            assert '\\' not in i.filename and ':' not in i.filename
            assert not any(ord(x) < 32 for x in i.filename)
            assert not i.is_dir() and not (i.flag_bits & 1)
            mode = i.external_attr >> 16
            assert stat.S_ISREG(mode) and not (mode & 0o7000)
            assert stat.S_IMODE(mode) in (0o644, 0o755)
            assert all(str(parent) not in names for parent in p.parents if str(parent) != '.')
        record('safe unique regular inventory', entries=len(names))
        required = {'README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md',
                    'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md',
                    'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json'}
        assert required <= set(names)
        assert {'SOURCE-MANIFEST.json','RECOVERY-FILE-MAP.json','SOURCE-RECOVERY.md'} <= set(names)
        record('all required and additional recovery roots', required_roots=9, additional_roots=3)
        manifest = json.loads(z.read('MANIFEST-SHA256.json'))
        assert manifest['excludes'] == ['MANIFEST-SHA256.json']
        rows = {r['path']: r for r in manifest['files']}
        assert len(rows) == len(manifest['files']) == 260
        assert set(rows) == set(names) - {'MANIFEST-SHA256.json'}
        record('exact manifest coverage', payloads=len(rows))
        data = {}
        for i in infos:
            blob = z.read(i)
            assert len(blob) == i.file_size and zlib.crc32(blob) & 0xffffffff == i.CRC
            if i.filename in rows:
                identity(blob, rows[i.filename])
                assert stat.S_IMODE(i.external_attr >> 16) == int(rows[i.filename]['mode'], 8)
            data[i.filename] = blob
        assert z.testzip() is None
        record('all CRC sizes hashes and archive modes', uncompressed_bytes=sum(map(len,data.values())))
        extract = Path(tempfile.mkdtemp(prefix='extracted-', dir=OUT))
        for i in infos:
            target = extract / i.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(data[i.filename])
            target.chmod(stat.S_IMODE(i.external_attr >> 16))
            assert target.read_bytes() == data[i.filename]
            assert stat.S_IMODE(target.stat().st_mode) == stat.S_IMODE(i.external_attr >> 16)
        assert len([p for p in extract.rglob('*') if p.is_file()]) == 261
        RESULT['fresh_extraction'] = str(extract)
        record('independent fresh extraction exact bytes and restored modes', extracted_files=261)
        def j(name):
            return json.loads(data[name])
        sources = j('SOURCE-MANIFEST.json')['files']
        assert len(sources) == len({r['archive_path'] for r in sources}) == 144
        tree_map = {}
        for commit, expected_tree in ((SOURCE,TREE),(MAIN,MAIN_TREE)):
            assert git('rev-parse', commit+'^{tree}').decode().strip() == expected_tree
            mapping = {}
            for line in git('ls-tree','-r','-z',commit).split(b'\0'):
                if not line: continue
                head,path = line.split(b'\t',1)
                mode,kind,blob = head.decode().split(' ')
                mapping[path.decode()] = (mode,kind,blob)
            tree_map[commit] = mapping
        for row in sources:
            commit = row['commit']
            assert commit in (SOURCE,MAIN)
            assert row['tree'] == (TREE if commit==SOURCE else MAIN_TREE)
            mode,kind,blob = tree_map[commit][row['source_path']]
            assert kind == 'blob' and mode == row['git_mode'] and blob == row['git_blob']
            body = data[row['archive_path']]
            identity(body,row)
            assert hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest() == blob
            assert git('cat-file','blob',blob) == body
            assert int(mode,8) & 0o777 == int(row['mode'],8) == int(rows[row['archive_path']]['mode'],8)
            assert row['url'] == 'https://github.com/Omegapy/OntoKin/blob/'+commit+'/'+row['source_path']
        record('all selected source bytes commit tree blob mode bindings', snapshots=len(sources),
               commits=dict(collections.Counter(r['commit'] for r in sources)))
        src_paths = {r['source_path'] for r in sources if r['commit']==SOURCE}
        for path in ['AGENTS.md','ROLE.md','GOAL.md','STATUS.md','CHATGPT-START-HERE.md',
                     'docs/workflow/registry.json','docs/workflow/CURRENT.json',
                     'docs/workflow/PROTOCOL.md','docs/workflow/HANDOFF.md',
                     'docs/workflow/BROWSER-PROMPTS.md',
                     'docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md',
                     'docs/workflow/tasks/C271/task.json']:
            assert path in src_paths, path
        skills = [p for p in src_paths if p.startswith('.agents/skills/') and p.endswith('/SKILL.md')]
        assert len(skills)==3
        for prefix in ['docs/workflow/tasks/C271/', 'docs/engineering/localized-repair-c271/host-inspection-p07/']:
            assert {p for p in tree_map[SOURCE] if p.startswith(prefix)} <= src_paths
        record('selected governance active task complete P07 subtree', project_skills=len(skills))
        prompt_checks = []
        for member,suffix,expected in [
            ('PROMPT-1-CONTINUE.md','_Continue.md','21fbd0af232a99143d86e02ba4f22e7c9814eeca1b4fd5ffdf5dbd7b63cd1a3b'),
            ('PROMPT-2-RECOVER.md','_Recover.md','d98b51e6d41a1da33da6cb23b328fcd76d66b5a509ba4cdda490b751547cee28')]:
            companion = BASE/'packages'/(NAME+suffix)
            assert companion.read_bytes() == data[member] and digest(data[member]) == expected
            prompt_checks.append({'path':str(companion),'bytes':len(data[member]),'sha256':expected})
        record('standalone prompts equal packaged prompts', prompts=prompt_checks)
        recovery = j('RECOVERY-FILE-MAP.json')
        recovery_rows = recovery['files']
        recovery_index = {r['original_path']:r['package_path'] for r in recovery_rows}
        def recovered(original_path):
            return data[recovery_index[original_path]]
        assert len(recovery_rows)==145 and len({r['original_path'] for r in recovery_rows})==144
        assert len({(r['original_path'],r['package_path']) for r in recovery_rows})==145
        for original in {r['original_path'] for r in recovery_rows}:
            aliases=[r for r in recovery_rows if r['original_path']==original]
            assert len({(r['bytes'],r['sha256'],r['mode']) for r in aliases})==1
        for row in recovery_rows:
            identity(data[row['package_path']],row)
            assert rows[row['package_path']]['mode']==row['mode']
            original = BASE/row['original_path']
            identity(original.read_bytes(),row)
            assert stat.S_IMODE(original.stat().st_mode)==int(row['mode'],8)
            if row['recovery_kind']=='exact_packaged_source':
                assert row['package_path'] in {s['archive_path'] for s in sources}
            else:
                assert row['recovery_kind']=='embedded_unique_file'
        record('recovery map originals exact and dedup aliases valid', entries=len(recovery_rows),unique_originals=144,
               kinds=dict(collections.Counter(r['recovery_kind'] for r in recovery_rows)))
        host_files = [p for p in (BASE/'audit/host-design').rglob('*') if p.is_file()]
        for p in host_files:
            archive_path = 'session/'+str(p.relative_to(BASE))
            assert data[archive_path]==p.read_bytes(), archive_path
        assert len(host_files)==33
        record('entire author history and drafts retained', files=len(host_files))
        candidate = j(CANON+'DESIGN-CANDIDATE.json')
        candidate_hash = 'ad48e321ee9163f9f87c675c291f566e28b961b55696976f738b04e165845f2a'
        assert digest(data[CANON+'DESIGN-CANDIDATE.json']) == candidate_hash
        assert data[CANON+'DESIGN-CANDIDATE.json'] == data['session/audit/host-design/review-candidate-002/MANIFEST.json']
        adoption = j(CANON+'ADOPTION.json')
        assert adoption['candidate_manifest_sha256']==candidate_hash
        assert adoption['status']=='accepted_design_only' and not adoption['executable_authority']
        assert adoption['accepted_payloads']==candidate['files'] and len(candidate['files'])==9
        for row in candidate['files']:
            body=data[CANON+row['path']]
            identity(body,row,'size_bytes')
            assert body==data['session/audit/host-design/review-candidate-002/'+row['path']]
        assert digest(data[CANON+adoption['independent_review']])==adoption['independent_review_sha256']
        record('exact accepted candidate adoption and independent review', payloads=9,
               candidate_manifest_sha256=candidate_hash, payload_bytes=sum(x['size_bytes'] for x in candidate['files']))
        first = j(CANON+'review/REVIEW-001.json')
        second = j(CANON+'review/REVIEW-002.json')
        assert first['verdict']=='CHANGES_REQUIRED' and first['findings'][0]['id']=='P07-R01'
        assert second['verdict']=='ACCEPT_P07_DESIGN_ONLY' and second['mandatory_open_findings']==0
        assert second['resolved_findings'][0]['id']=='P07-R01'
        assert digest(data['session/audit/host-design/review-candidate-001/MANIFEST.json'])=='509d97fc3c85c82e210ee2fa084cc772ca8deaddffcffecb1340ce24753ddbb5'
        assert len(j(CANON+'AUTHORING-ERRORS.json')['errors'])==2
        assert 'session/audit/host-design/drafts/static-checks-failed-001.json' in data
        record('original mandatory finding failed author checks and corrected acceptance preserved', finding='P07-R01')
        dependencies=j('HISTORICAL-DEPENDENCIES.json')
        with zipfile.ZipFile(P06) as previous:
            assert dependencies['incoming_p06_dependencies']==json.loads(previous.read('HISTORICAL-DEPENDENCIES.json'))
        external_paths=[P06,BASE/'source_handoffs/OntoKin_C271_P06_Delivery_Receipt_2026-11-20.zip',
                        BASE/'packages/OntoKin_C271_P07_Early_Recovery_2026-11-20.zip']
        assert len(dependencies['external'])==3
        for item,path in zip(dependencies['external'],external_paths):
            assert path.name==item['file_name'] and item['embedded'] is False
            identity(path.read_bytes(),item)
        assert len(dependencies['incoming_p06_dependencies']['external'])==10
        record('predecessor identities exact without recursive restoration', current_external=3, inherited_external=10)
        reconstructed=[]
        for omitted in recovery['omitted']:
            identity((BASE/omitted['original_path']).read_bytes(),omitted)
            if omitted['recovery_kind']!='exact_reconstruction':
                continue
            descriptor=j(omitted['descriptor'])
            assert all(descriptor['original'][k]==omitted[k] for k in ('original_path','bytes','sha256','mode'))
            if descriptor['kind']=='p06-selected-git-identities':
                identity(P06.read_bytes(),descriptor['input_archive'])
                with zipfile.ZipFile(P06) as old:
                    inputs={}
                    for row in descriptor['input_members']:
                        body=old.read(row['path']);identity(body,row);inputs[row['path']]=json.loads(body)
                value={'snapshots':inputs['SOURCE-SNAPSHOT-MANIFEST.json']['snapshots'],
                       'historical_sources':inputs['SOURCE-DEPENDENCIES.json']['files'],
                       'recovery_git_rows':[r for r in inputs['RECOVERY-FILE-MAP.json']['files'] if r['recovery_kind']=='exact_git_dependency']}
            elif descriptor['kind']=='git-tree-request':
                elements=[]
                for e in descriptor['tree_elements']:
                    v=dict(e['values_without_content'])
                    if 'content_source' in e:
                        binding=e['content_source'];body=git('cat-file','blob',binding['git_blob'])
                        identity(body,binding);v['content']=body.decode('utf-8')
                    elements.append({k:v[k] for k in e['keys']})
                top=dict(descriptor['top_values_without_elements'],tree_elements=elements)
                value={k:top[k] for k in descriptor['top_keys']}
            else:
                raise AssertionError(descriptor['kind'])
            enc=descriptor['json_encoding']
            body=(json.dumps(value,indent=enc['indent'],sort_keys=enc['sort_keys'],ensure_ascii=enc['ensure_ascii'])+('\n' if enc['trailing_newline'] else '')).encode()
            identity(body,omitted)
            assert body==(BASE/omitted['original_path']).read_bytes()
            reconstructed.append({'original_path':omitted['original_path'],'bytes':len(body),'sha256':digest(body),'descriptor':omitted['descriptor']})
        assert len(reconstructed)==3
        record('three compact omissions independently reconstructed byte for byte', reconstructed=reconstructed)
        checks=j('session/audit/published-design-checks/CHECKS.json')
        assert checks['source_revision']==SOURCE and checks['source_tree']==TREE and checks['result']=='passed'
        assert checks['source_clean_before'] and checks['source_clean_after'] and checks['source_state_unchanged']
        for c in checks['checks']:
            assert c['returncode']==0 and c['result']=='passed'
            for stream in ('stdout','stderr'):
                identity(recovered('audit/published-design-checks/'+c[stream]['file']),c[stream])
        identity(recovered('audit/published-design-checks/'+checks['protected_source']['file']),checks['protected_source'])
        for row in checks['working_input_bindings']:
            identity(data['repository/'+row['path']],row)
        record('published documentary evidence and log cross bindings', check_records=len(checks['checks']),working_bindings=len(checks['working_input_bindings']))
        frozen=j('session/audit/FINAL-FREEZE-INPUT.json')
        assert data['session/audit/FINAL-FREEZE-INPUT.json']==data['recovery/packaging/FINAL-FREEZE-INPUT.json']
        live=j('session/audit/final-live-state.json'); checkpoint=j('CHECKPOINT.json')
        assert live['checkout_head']==SOURCE and live['checkout_tree']==TREE and live['status_porcelain']==''
        assert checkpoint['source']['commit']==SOURCE and checkpoint['source']['tree']==TREE
        assert checkpoint['main']['commit']==MAIN and checkpoint['main']['tree']==MAIN_TREE
        assert checkpoint['branch']['head']==SOURCE and checkpoint['pull_request']['state']=='open'
        assert checkpoint['pull_request']['draft'] and not checkpoint['pull_request']['merged']
        assert checkpoint['issue']['state']=='open'
        record('frozen source live observations and open publication state agree', main_commit=MAIN)
        phase=j(CANON+'PHASE-OUTCOME.json')
        for x in (phase,checkpoint):
            assert x['parent_status']=='in_progress'
            assert all(x['parent_requirements'][r]=='not_done' for r in ('R03','R04','R05'))
        assert phase['status']==checkpoint['phase_status']=='technical_design_complete_delivery_pending'
        assert phase['technical_phase_complete'] and not phase['phase_complete']
        assert all(v==0 for v in phase['product_execution_counts'].values())
        assert all(checkpoint[k] is False for k in ('parent_complete','runtime_qualified','full_routine_executed','R03_accepted','integration_performed'))
        assert checkpoint['delivery']['status']=='save_pending' and checkpoint['delivery']['external_receipt_required']
        assert checkpoint['delivery']['canonical_receipt']=='docs/engineering/localized-repair-c271/host-inspection-p07/P07-DELIVERY.json'
        assert CANON+'P07-DELIVERY.json' not in data
        assert 'fresh' in checkpoint['next_action'] and 'stop' in checkpoint['stop'].lower()
        assert 'online GitHub continuation' in checkpoint['package_type']
        assert 'audit/final-package-review/' in recovery['deferred_postfreeze_evidence']
        record('truthful design-only phase delivery pending and future fresh-chat HI boundary', final_save_confirmed=False,
               future_external_receipt=checkpoint['delivery']['canonical_receipt'])
        changes=git('diff','--name-only',BASELINE,SOURCE,'--').decode().splitlines()
        allowed=('docs/engineering/localized-repair-c271/host-inspection-p07/','docs/workflow/tasks/C271/')
        assert all(p=='docs/workflow/CURRENT.json' or p.startswith(allowed) for p in changes)
        assert 'prototypes/static_tray_v01/current_host_inspection_v01.py' not in tree_map[SOURCE]
        assert 'tests/test_current_host_inspection_v01.py' not in tree_map[SOURCE]
        record('P07 frozen changes are documentation and audit only', changed_paths=changes)
        rg=subprocess.check_output(['rg','--files','audit/intake-review/extracted-p06'],cwd=BASE,text=True).splitlines()
        actual=[p for p in (BASE/'audit/intake-review/extracted-p06').rglob('*') if p.is_file()]
        claimed=recovery['reproducible_extracted_groups']['audit/intake-review/extracted-p06']
        assert len(rg)==claimed['files'] and sum((BASE/p).stat().st_size for p in rg)==claimed['bytes']
        RESULT['notes'].append({'severity':'nonblocking_scope_note','subject':'Omitted reproducible extraction group count',
            'recorded_enumerated_files':len(rg),'actual_prior_extraction_files':len(actual),
            'explanation':'The group count reflects rg default enumeration and omits three hidden-tree skill snapshots. The exact external P06 ZIP identity and all three current skill snapshots are retained. Full previous archive recovery remains exact; this is not a lost unique-evidence finding.'})
        assert ARCHIVE.read_bytes()==raw_zip
        assert git('rev-parse','HEAD').decode().strip()==initial_head
        assert git('status','--porcelain=v1').decode()==initial_status
        record('archive unchanged and source checkout remains clean', source_head=initial_head)
    RESULT['verdict']='PASS_P07_HANDOFF_PACKAGE'
    RESULT['review_boundary']='Archive integrity, exact selected Git sources, history/recovery and truthful design-only continuation. Final save/readback and later external delivery receipt remain Director gates; no implementation or runtime qualification is asserted.'
    RESULT['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    save()

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        check()
    except Exception as exc:
        RESULT['verdict']='REVIEW_CHECK_FAILED'
        RESULT['verification_exception']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
        save()
        raise
    print(json.dumps({'verdict':RESULT['verdict'],'groups_passed':len(RESULT['checks']),'archive_sha256':EXPECTED_SHA,'report':str(OUT/'RESULTS.json')}))
