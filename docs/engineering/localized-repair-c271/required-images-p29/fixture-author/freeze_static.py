"""Static integrity/freeze only; never imports the adapter or product."""
import ast
import collections
import datetime
import hashlib
import json
from pathlib import Path
import stat
import struct
import zipfile

ROOT=Path('/workspace/scratch/2eb33b59a678/repository')
OUT=ROOT/'docs/engineering/localized-repair-c271/required-images-p29/controls'
REVIEW=ROOT.parent/'reviews/fixture-author'
ADAPTER=ROOT/'tests/test_current_host_required_images_v01.py'
PLAN=ROOT/'docs/engineering/localized-repair-c271/required-image-design-p27/design/CONTROL-PLAN.json'
def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def load(p): return json.loads(p.read_bytes())
def row(p,base=ROOT): return {'path':p.relative_to(base).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'mode':oct(stat.S_IMODE(p.stat().st_mode))}
checks=[]
def check(name,ok,**details):
    checks.append({'check':name,'passed':bool(ok),**details})
    if not ok: raise AssertionError(name)
source=load(PLAN); bundle=load(OUT/'CONTROL-CROSSWALK.json'); cases=bundle['cases']
source_map={c['id']:c for c in source['cases']}
check('116_unique_exact_original_ids',len(cases)==116 and len({c['id'] for c in cases})==116 and {c['id'] for c in cases}==set(source_map))
check('unique_test_methods',len({c['test_method'] for c in cases})==116)
for case in cases:
    check('literal_p27_oracle_and_case_identity',case['expected']==source_map[case['id']]['expected'] and case['source_case_sha256']==sha(canonical(source_map[case['id']])),id=case['id'])
    check('nonoperational_zero_target_scope',case['operational'] is False and set(case['target_starts'].values())=={0},id=case['id'])
    if 'fixture' in case:
        f=case['fixture']; p=(OUT if f['scope']=='controls' else ROOT)/f['path']; raw=p.read_bytes()
        check('exact_inert_fixture',len(raw)==f['size_bytes'] and sha(raw)==f['sha256'] and f['mode']=='0o644' and not p.stat().st_mode&0o111,id=case['id'])
        if f['scope']=='controls':
            # This fixed-offset independent construction inspection is not the
            # OntoKin parser and makes no admission/result claim.
            check('synthetic_declared_extent',len(raw)>=176 and raw[:4]==b'\x7fELF',id=case['id'])
            dynamic_offset=struct.unpack_from('<Q',raw,128)[0]
            dynamic_size=struct.unpack_from('<Q',raw,152)[0]
            check('synthetic_dynamic_bytes',dynamic_offset==512 and dynamic_offset+dynamic_size<=len(raw) and dynamic_size==f['layout']['pread_ranges'][2][1],id=case['id'])
            check('synthetic_string_extent',sum(f['layout']['pread_ranges'][3])==len(raw),id=case['id'])
    if 'context' in case:
        c=load(OUT/case['context'])
        check('complete_logical_context',set(c)==set(load(OUT/'BASE-CONTEXT.json')) and c['operational'] is False,id=case['id'])
d01=load(OUT/'contexts/RI-D01.json'); python=d01['plan']['author']['python_descriptor']['path']
declared=next(r['metadata'] for r in d01['plan']['host_static']['resolution']['images'] if r['file']['path']==python)
check('D01_changes_only_actual_needed','libdl.so.2' not in d01['actual_python_metadata']['needed'] and 'libdl.so.2' in declared['needed'])
base=load(OUT/'BASE-CONTEXT.json')
for cid in ('RI-C04','RI-C06'):
    check('temporal_fault_keeps_declarations_coherent',load(OUT/f'contexts/{cid}.json')==base,id=cid)
mock=load(OUT/'MOCK-COMMAND.json')
check('mock_command_plan_binding',mock['plan_descriptor']['sha256']==sha(canonical(base['plan'])) and mock['plan_descriptor']['size_bytes']==len(canonical(base['plan'])))
for entry in mock['expected_publications']:
    check('frozen_fake_publication_descriptor',entry['descriptor']['sha256']==sha(canonical(entry['payload'])) and entry['descriptor']['size_bytes']==len(canonical(entry['payload'])),path=entry['path'])
check('five_frozen_fake_publications',len(mock['expected_publications'])==5 and mock['process']['pid']==mock['process']['process_group']==12345)
prelaunch=load(OUT/'MOCK-PRELAUNCH.json')
check('prelaunch_frozen_plan_binding',prelaunch['plan_descriptor']==mock['plan_descriptor'] and prelaunch['command']==mock['command'])
check('prelaunch_three_publications_and_zero_fake_process_calls',len(prelaunch['expected_publications'])==3 and prelaunch['fake_run_process_calls']==0 and prelaunch['real_launch_check_calls']==1)
for entry in prelaunch['expected_publications']:
    check('frozen_prelaunch_publication_descriptor',entry['descriptor']['sha256']==sha(canonical(entry['payload'])) and entry['descriptor']['size_bytes']==len(canonical(entry['payload'])),path=entry['path'])
revision=load(OUT/'REVISION.json')
prior_path=ROOT/revision['previous_candidate']['preserved_archive']
check('candidate003_preserved_archive_identity',sha(prior_path.read_bytes())==revision['previous_candidate']['archive_sha256'])
with zipfile.ZipFile(prior_path) as z:
    check('candidate003_archive_crc_unique_members',z.testzip() is None and len(z.namelist())==len(set(z.namelist())))
    prior_freeze_path=(OUT/'FREEZE.json').relative_to(ROOT).as_posix()
    prior_freeze_raw=z.read(prior_freeze_path)
    check('candidate003_freeze_identity',sha(prior_freeze_raw)==revision['previous_candidate']['freeze_sha256'])
    prior_freeze=json.loads(prior_freeze_raw)
    changed_allowed={ADAPTER.relative_to(ROOT).as_posix(),*[(OUT/name).relative_to(ROOT).as_posix() for name in ('README.md','REVISION.json','FIXTURE-MANIFEST.json')]}
    check('only_four_declared_prior_payloads_may_change',changed_allowed==set(revision['allowed_changed_payloads']))
    for old in prior_freeze['files']:
        if old['path'] not in changed_allowed:
            check('candidate003_payload_unchanged', (ROOT/old['path']).read_bytes()==z.read(old['path']),path=old['path'])
    prior_adapter=z.read(ADAPTER.relative_to(ROOT).as_posix()).decode('utf-8')
    prior_commands=json.loads(z.read((OUT/'COMMANDS.json').relative_to(ROOT).as_posix()))
    prior_companions=json.loads(z.read((OUT/'COMPANIONS.json').relative_to(ROOT).as_posix()))
for companion in load(OUT/'COMPANIONS.json')['files']:
    p=ROOT/companion['path']
    check('unchanged_companion_binding',p.is_file() and p.stat().st_size==companion['size_bytes'] and sha(p.read_bytes())==companion['sha256'],path=companion['path'])
commands=load(OUT/'COMMANDS.json'); ast.parse(commands['inherited_command'][2]); ast.parse(ADAPTER.read_text())
check('adapter_and_command_ast_only',True)
cohort=load(ROOT/commands['inherited_cohort']['path'])
check('481_inherited_ids_no_exclusions',len(cohort['selected_test_ids'])==len(set(cohort['selected_test_ids']))==481 and cohort['exclusions']==[] and commands['inherited_exclusions']==[])
old_hash='dab30610b44cdb0596c395505a940722506e2c5535ed58b0984317f261de6efe'
new_hash='7aa9e1278419e6b4fd27afbc758d5dcea195a245960cd4c972d8102a34dcce77'
check('corrected_cohort_exact_accepted_hash',commands['inherited_cohort']['sha256']==new_hash and sha((ROOT/commands['inherited_cohort']['path']).read_bytes())==new_hash)
check('all_frozen_command_fields_unchanged',commands==prior_commands)
check('focused_command_modules_and_exclusions_unchanged',all(commands[k]==prior_commands[k] for k in ('focused','required_inherited_modules','inherited_exclusions','inherited_non_target_child','evidence_environment')))
new_companions=load(OUT/'COMPANIONS.json')
cohort_relative=commands['inherited_cohort']['path']
check('all_companion_records_unchanged',new_companions==prior_companions)
runtime=load(ROOT.parent/'verification/baseline-inherited/RUNTIME-INVENTORY.json')
check('corrected_inventory_matches_retained_discovery',sorted(cohort['selected_test_ids'])==runtime['actual_ids'] and len(runtime['expected_ids'])==372 and runtime['exact_match'] is False)
inspection_ast=ast.parse((ROOT/'tests/test_current_host_inspection_v01.py').read_text())
variants=[ast.literal_eval(n.value) for n in inspection_ast.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONTROL_VARIANTS' for t in n.targets)]
check('one_literal_control_variants_source',len(variants)==1)
generated={'test_current_host_inspection_v01.HostInspectionControls.test_'+group+'_'+variant for group,letters in variants[0].items() for variant in letters}
check('exact_109_source_derived_additions',len(generated)==109 and generated==set(runtime['actual_ids'])-set(runtime['expected_ids']) and set(runtime['expected_ids'])|generated==set(cohort['selected_test_ids']))
metadata=load(OUT/'INHERITED-METADATA-STUB.json')
check('exact_reviewed_recording_metadata_leaf',metadata['control_id']=='RI-L08' and metadata['module']=='test_current_host_rtld_paths_v01' and metadata['leaf']=='platform.platform' and metadata['value']=='Synthetic P29 RI-L08 metadata; host not probed' and metadata['expected_call_count']==1 and metadata['expected_args']==[] and metadata['expected_kwargs']=={} and metadata['recording_file']=='INPUTS.json' and metadata['recording_key']=='platform')
rtld_ast=ast.parse((ROOT/'tests/test_current_host_rtld_paths_v01.py').read_text())
platform_calls=[n for n in ast.walk(rtld_ast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='platform' and n.func.attr=='platform']
check('old_rtld_single_zero_argument_metadata_call',len(platform_calls)==1 and not platform_calls[0].args and not platform_calls[0].keywords)
rtld_class=next(n for n in rtld_ast.body if isinstance(n,ast.ClassDef) and n.name=='RTLDPathControls')
setup=next(n for n in rtld_class.body if isinstance(n,ast.FunctionDef) and n.name=='setUpClass')
check('old_rtld_metadata_call_only_in_input_record',platform_calls[0] in list(ast.walk(setup)) and any(isinstance(n,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='platform' and v is platform_calls[0] for k,v in zip(n.keys,n.values)) for n in ast.walk(setup)))
failure_path=ROOT.parent/'verification/implementation-focused-001/control-data/required-images/RI-L08.json'
failed=load(failure_path); nested=failed['observations']['inherited_corpora'][0]
check('focused_failure_preserved_before_correction',sha(failure_path.read_bytes())=='28038c710f692023611e35467920059e3c4d7a024cda92affb65d56491170872' and failed['passed'] is False and failed['forbidden_calls']==["(['uname', '-p'],)"] and nested['tests_run']==10 and len(nested['method_ids'])==61 and len(nested['errors'])==1)
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ('FIXTURE-MANIFEST.json','FREEZE.json'))
current_paths={p.relative_to(ROOT).as_posix() for p in files}|{(OUT/'FIXTURE-MANIFEST.json').relative_to(ROOT).as_posix(),ADAPTER.relative_to(ROOT).as_posix()}
check('only_declared_metadata_payload_added',current_paths-{r['path'] for r in prior_freeze['files']}==set(revision['allowed_added_payloads'])=={(OUT/'INHERITED-METADATA-STUB.json').relative_to(ROOT).as_posix()} and {r['path'] for r in prior_freeze['files']}<=current_paths)
manifest={'schema':'ontokin.c271.p29-required-images-fixture-manifest/1','files':[row(p,OUT) for p in files],'scope':'Exact inert controls; candidate004 product execution NOT_RUN; prior attempts retained'}
manifest_path=OUT/'FIXTURE-MANIFEST.json'; manifest_path.write_text(json.dumps(manifest,indent=2)+'\n'); manifest_path.chmod(0o644)
source_text=ADAPTER.read_text()
old=[n.value.value for n in ast.parse(source_text).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIXTURE_MANIFEST_SHA256' for t in n.targets)][0]
source_text=source_text.replace("FIXTURE_MANIFEST_SHA256 = '"+old+"'", "FIXTURE_MANIFEST_SHA256 = '"+sha(manifest_path.read_bytes())+"'")
ADAPTER.write_text(source_text); ADAPTER.chmod(0o644); ast.parse(source_text)
def inherited_method(source_text):
    tree=ast.parse(source_text)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RequiredImageControls')
    return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='inherited_case')
prior_method=inherited_method(prior_adapter)
def normalized_adapter(source_text):
    tree=ast.parse(source_text)
    matches=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIXTURE_MANIFEST_SHA256' for t in n.targets)]
    assert len(matches)==1 and isinstance(matches[0].value,ast.Constant) and isinstance(matches[0].value.value,str)
    matches[0].value=ast.Constant(value='FROZEN_MANIFEST_HASH')
    tree.body=[n for n in tree.body if not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INHERITED_METADATA_STUB' for t in n.targets))]
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RequiredImageControls')
    cls.body=[prior_method if isinstance(n,ast.FunctionDef) and n.name=='inherited_case' else n for n in cls.body]
    return ast.dump(tree,include_attributes=False)
check('adapter_ast_unchanged_outside_declared_metadata_scope',normalized_adapter(source_text)==normalized_adapter(prior_adapter))
prior_manifest_hash=prior_freeze['fixture_manifest']['sha256']
constant_line="INHERITED_METADATA_STUB = read_json(CONTROL_ROOT / 'INHERITED-METADATA-STUB.json')\n"
new_method=inherited_method(source_text)
prior_method_text=''.join(prior_adapter.splitlines(keepends=True)[prior_method.lineno-1:prior_method.end_lineno])
new_method_text=''.join(source_text.splitlines(keepends=True)[new_method.lineno-1:new_method.end_lineno])
reverted=source_text.replace(sha(manifest_path.read_bytes()),prior_manifest_hash).replace(constant_line,'').replace(new_method_text,prior_method_text)
check('adapter_bytes_unchanged_outside_three_declared_edits',source_text.count(constant_line)==1 and source_text.count(new_method_text)==1 and reverted==prior_adapter)
check('metadata_mock_scope_observation_and_restore_are_present',all(s in new_method_text for s in ("if case['id'] == INHERITED_METADATA_STUB['control_id']:","module.platform, 'platform', return_value=INHERITED_METADATA_STUB['value']","metadata_stub.assert_called_once_with()","module.platform.platform is original_platform","recorded = inputs[INHERITED_METADATA_STUB['recording_key']]","self.assertEqual(recorded, INHERITED_METADATA_STUB['value'])")))
freeze={'schema':'ontokin.c271.p29-required-images-freeze/1','phase':'C271-P29-required-images-reconstruction','candidate':revision['candidate'],'previous_candidate':revision['previous_candidate'],'author':'/root/handoff_audit','recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'adopted_control_plan_sha256':sha(PLAN.read_bytes()),'obligations':116,'synthetic_inert_images':47,'logical_contexts':56,'product_imports_or_execution':0,'product_imports_or_execution_scope':'Fixture author only. Prior Director baseline and focused attempts, including the preserved RI-L08 recording-metadata setup failure, are separately retained. Candidate004 is not executed.','prior_director_attempt':revision['prior_director_attempt'],'original_p28_597_tests':'reported_unverified','adapter':row(ADAPTER),'fixture_manifest':row(manifest_path),'files':[row(p) for p in files+[manifest_path,ADAPTER]],'self_exclusion':'FREEZE.json is externally hashed by independent review; it cannot contain its own identity.','result':'candidate_for_independent_review; candidate004 product execution NOT_RUN'}
freeze_path=OUT/'FREEZE.json'; freeze_path.write_text(json.dumps(freeze,indent=2)+'\n'); freeze_path.chmod(0o644)
summary={'schema':'ontokin.c271.p29-fixture-static-checks/1','executed':'Only stdlib construction/hash/inventory/ast.parse; no product import or execution','counts':{'passed_checks':len(checks),'failed_checks':0,'obligations':116,'synthetic_images':47,'contexts':56,'frozen_files_including_adapter_and_manifest':len(freeze['files']),'companions':len(load(OUT/'COMPANIONS.json')['files'])},'freeze':row(freeze_path),'adapter':row(ADAPTER),'fixture_manifest':row(manifest_path),'checks':checks}
(REVIEW/'STATIC-CHECKS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ('counts','freeze','adapter','fixture_manifest')},indent=2))
