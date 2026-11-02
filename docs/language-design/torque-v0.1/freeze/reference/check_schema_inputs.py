#!/usr/bin/env python3
"""Validate design examples/request templates against the proposed schemas.

This is schema/input review only. It neither imports OntoKin nor executes an
Agent, supplied-byte reader, simulator, export, store or semantic mutation.
"""
from __future__ import annotations
import argparse
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import jsonschema
from referencing import Registry,Resource

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()


def at(value,path):
    parts=path.strip('/').split('/');parent=value
    for part in parts[:-1]: parent=parent[int(part)] if isinstance(parent,list) else parent[part]
    key=int(parts[-1]) if isinstance(parent,list) else parts[-1]
    return parent,key


def materialize(value,key=None):
    if type(value) is list:return [materialize(v) for v in value]
    if type(value) is not dict:return value
    if '$bundle_file' in value:
        m=json.loads((ROOT/value['$bundle_file']).read_text())
        return {'schema_version':'ontokin.bundle/0.2','entry':{'filename':m['entry']['filename'],'source':(ROOT/m['entry']['path']).read_text()},
          'modules':[{**{k:u[k] for k in ('package_id','version','filename')},'source':(ROOT/u['path']).read_text()} for u in m['modules']],
          'assets':[{**{k:a[k] for k in ('asset_id','sha256','media_type')},'data_base64':base64.b64encode((ROOT/a['path']).read_bytes()).decode()} for a in m['assets']]}
    if '$response' in value:return 'schema-only-symbolic-identifier'
    if '$capture' in value:return 0 if key=='offset' else 'schema-only-symbolic-identifier'
    if '$loop' in value:return 0
    return {k:materialize(v,k) for k,v in value.items()}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--contract-root',required=True,type=Path);ap.add_argument('report',type=Path);args=ap.parse_args()
    if args.report.exists():raise SystemExit('Use a new report path; old evidence is immutable')
    schema_paths=[args.contract_root/'docs/language-design/torque-v0.1/torques.schema.json',args.contract_root/'docs/language-design/agent-v0.22/request.schema.json',args.contract_root/'docs/language-design/textured-surfaces-v0.1/bundle.schema.json']
    schemas=[json.loads(p.read_text()) for p in schema_paths]
    registry=Registry().with_resources([(s['$id'],Resource.from_contents(s)) for s in schemas])
    state_validator=jsonschema.Draft202012Validator(schemas[0],registry=registry)
    request_validator=jsonschema.Draft202012Validator(schemas[1],registry=registry)
    rows=[]
    def record(name,value,validator,expected):
        errors=list(validator.iter_errors(value));actual=not errors
        rows.append({'id':name,'passed':actual==expected,'actual_schema_accepts':actual,'expected_schema_accepts':expected,
                     'first_error':None if not errors else {'path':list(errors[0].path),'message':errors[0].message[:500]}})
    data=json.loads((ROOT/'schema-cases.json').read_text())
    for key,value in data['prototypes'].items():record('prototype/'+key,value,state_validator,True)
    for case in data['cases']:
        value=deepcopy(data['prototypes'][case['prototype']]);parent,key=at(value,case['path'])
        if case['operation']=='remove':del parent[key]
        elif case['operation']=='append-copy':parent.append(deepcopy(parent[key]))
        else:parent[key]=case['value']
        record(case['id'],value,state_validator,case['expected_schema_accepts'])
    # Templates use inert example strings only to check wire types. This does
    # not pretend a future returned run/artifact/cursor exists.
    def walk(value,path=''):
        if type(value) is dict:
            if value.get('schema_version')=='ontokin.agent/0.22' and 'operation' in value:
                record(path,materialize(value),request_validator,True)
            else:
                for key,item in value.items():walk(item,path+'/'+key)
        elif type(value) is list:
            for i,item in enumerate(value):walk(item,path+'/'+str(i))
    for filename in ['agent/request-workflows.json','agent/resource-cases.json']:
        walk(json.loads((ROOT/filename).read_text()),filename)
    report={'schema_version':'ontokin.torque-independent-schema-check/1','status':'passed' if all(r['passed'] for r in rows) else 'failed',
      'checks':len(rows),'failed':[r for r in rows if not r['passed']],'schema_inputs':[{'path':str(p),'sha256':sha(p)} for p in schema_paths],
      'checker_sha256':sha(Path(__file__)),'production_imported':False,'candidate_output_used':False,'semantic_mutations_executed':False,'runtime_validation_performed':False,'rows':rows}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'status':report['status'],'checks':len(rows),'failed':len(report['failed'])}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
