"""Validate the audit's source/evidence references without executing an observer."""
from pathlib import Path
from collections import Counter
import datetime as dt
import hashlib
import json
import subprocess
import sys

R=Path(__file__).resolve().parents[4];E=R/'docs/engineering/localized-repair-c269';C=json.loads((E/'COVERAGE.json').read_text())
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else E/'evidence/REFERENCE-CHECKS.json'
def git(rev,path):return subprocess.check_output(['git','show',rev+':'+path],cwd=R)
def h(b):return hashlib.sha256(b).hexdigest()
def pointer(doc,p):
    if not p:return doc
    for k in p.lstrip('/').split('/'):
        k=k.replace('~1','/').replace('~0','~');doc=doc[int(k)] if isinstance(doc,list) else doc[k]
    return doc
assert [x['id'] for x in C['groups']]==['H'+str(i).zfill(2) for i in range(1,29)]
assert dict(Counter(g['status'] for g in C['groups']))==C['summary']['group_statuses']
all_subcases=[s for g in C['groups'] for s in g['required_subcases']]
assert len({s['id'] for s in all_subcases})==len(all_subcases)==C['summary']['material_subcases']
assert dict(Counter(s['status'] for s in all_subcases))==C['summary']['subcase_statuses']
source_refs=0;execution_refs=0;case_refs=0;identity_count=0;cache={}
for item in json.loads((E/'INPUT-IDENTITIES.json').read_text())['files']:
    b=git(item['revision'],item['path']);assert len(b)==item['bytes'] and h(b)==item['sha256'];identity_count+=1
for item in C['sources']:
    b=(R/item['path']).read_bytes();assert len(b)==item['bytes'] and h(b)==item['sha256']
for g in C['groups']:
    assert g['status'] in C['classification_policy']
    if g['status']=='complete':assert all(s['status']=='complete' for s in g['required_subcases'])
    for s in g['required_subcases']:
        assert s['description'] and s['source_assertions']
        for a in s['source_assertions']:
            rev=a.get('revision',C['source_assertion_default_revision']);key=(rev,a['path'])
            if key not in cache:cache[key]=git(*key)
            b=cache[key];assert (R/a['path']).read_bytes()==b
            line=a.get('line_reference',{});start=line.get('start_line',a.get('line_start'));end=line.get('end_line',a.get('line_end'))
            assert isinstance(start,int) and 1<=start<=end<=len(b.decode().splitlines()),a
            source_refs+=1
        evs=s.get('execution_results',s.get('execution_evidence',[]));assert evs,s['id']
        for v in evs:
            path=v.get('path',v.get('result_path'));raw=(R/path).read_bytes();j=json.loads(raw)
            if 'result_sha256' in v:assert h(raw)==v['result_sha256']
            for ptr in v.get('record_pointers',[]):pointer(j,ptr);case_refs+=1
            for i in v.get('case_indices',[]):assert 0<=i<len(j[v['case_array']]);case_refs+=1
            binding=v.get('input_hash_binding')
            if isinstance(binding,dict) and 'path' in binding:assert (R/binding['path']).is_file()
            execution_refs+=1
result={'schema':'ontokin.c269.audit-reference-checks/1','result':'passed','checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'audit_baseline':C['audit_baseline_revision'],'coverage_sha256':h((E/'COVERAGE.json').read_bytes()),'groups':28,'material_subcases':len(all_subcases),'inspected_input_identities':identity_count,'source_assertion_references':source_refs,'execution_result_references':execution_refs,'selected_case_references':case_refs,'behavioral_runs':0,'scope':'Identity, locations, counts and reference structure only; independent review determines semantic support.'}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
