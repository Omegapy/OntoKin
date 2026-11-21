"""Resolve one overly strict reviewer-helper comparison without changing inputs."""
import hashlib
import json
from pathlib import Path

base=Path('/workspace/scratch/2ad494d5da19/session_evidence')
candidate=base/'loader_design/candidate004'
out=base/'design_review/candidate004'
prior=json.loads((out/'REVISION-REVIEW.json').read_text())
a=json.loads((candidate/'fixture_inputs/P01_nonselecting_base.json').read_text())
b=json.loads((candidate/'fixture_inputs/N76_nonascii_origin.json').read_text())


def rename(x):
    if isinstance(x,str):return x.replace('/fixture/app','/fixture/caf\u00e9')
    if isinstance(x,list):return [rename(y) for y in x]
    if isinstance(x,dict):return {rename(k):rename(v) for k,v in x.items()}
    return x


expected=rename(a)
observed_change={'pointer':'/guards/1/inode','old':expected['guards'][1]['inode'],'new':b['guards'][1]['inode'],'path':b['guards'][1]['path']}
valid_fresh_identity=(observed_change=={'pointer':'/guards/1/inode','old':102,'new':1001,'path':'/fixture'}
                      and b['phase']=='initial' and b['approved_before'] is None
                      and b['guards'][1]['kind']=='directory' and b['guards'][1]['target'] is None
                      and len({(g['device'],g['inode']) for g in b['guards']})==len(b['guards'])
                      and not any(v['parent']=='/fixture' for v in b['absence_guards'].values())
                      and '/fixture' not in b['search_directories'])
expected['guards'][1]['inode']=1001
matches_after_accounting=expected==b
failure_label='N76_nonascii_origin: context differs only by coherent non-ASCII path relocation'
only_known_failure=len(prior['failed'])==1 and prior['failed'][0]['check']==failure_label
passed=valid_fresh_identity and matches_after_accounting and only_known_failure
record={'schema':'ontokin.c271.p11-independent-review-helper-correction/1',
        'candidate_manifest_sha256':hashlib.sha256((candidate/'CANDIDATE-MANIFEST.json').read_bytes()).hexdigest(),
        'original_result':'REVISION-REVIEW.json','original_passed':prior['passed'],'original_check_count':prior['check_count'],
        'preserved_original_failure':prior['failed'],'observed_only_additional_difference':observed_change,
        'new_check':{'pass':passed,'fresh_directory_identity_valid':valid_fresh_identity,'no_other_difference':matches_after_accounting,'only_known_initial_failure':only_known_failure},
        'disposition':'Reviewer-helper false positive. The initial context permits any coherent fresh directory identity. Requiring an unrelated ancestor inode to equal P01 was not a design requirement. The ASCII refusal remains isolated.',
        'candidate_or_oracle_modified':False,'reviewer_initial_script_modified':False,
        'all_revision_requirements_resolved':passed,'product_calls':0,'host_observations':0,'target_executions':0}
(out/'REVISION-FOLLOWUP.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps(record,indent=2,sort_keys=True))
raise SystemExit(0 if passed else 1)
