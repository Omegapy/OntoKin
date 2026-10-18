#!/usr/bin/env python3
"""Exercise actual program-agent authoring, repair, evaluation and GLB retrieval.

Predetermined Rack expectations are independent of the compiler and exporter.
The driver is a reproducible client, not an LLM benchmark or a source generator.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.program_agent import ProgramAgentService
from ontokin.bundle import load_bundle


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def rotation_error(actual, expected):
    a = [v/math.hypot(*actual) for v in actual]
    b = [v/math.hypot(*expected) for v in expected]
    if sum(x*y for x,y in zip(a,b)) < 0:
        b = [-v for v in b]
    return 4*math.atan2(math.hypot(*(x-y for x,y in zip(a,b))),math.hypot(*(x+y for x,y in zip(a,b))))


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    fixtures = ROOT/'docs/language-design/construction-v0.1/01-keyed-rack'
    final_payload = json.loads((fixtures/'program.bundle.json').read_text())
    oracle = json.loads((fixtures/'expected.json').read_text())
    seed = copy.deepcopy(final_payload)
    assert seed['entry']['source'].count('0.75[m]') == 1
    seed['entry']['source'] = seed['entry']['source'].replace('0.75[m]','0.65[m]')
    initial_bundle = load_bundle(seed)
    transcript, checks = [], []
    with tempfile.TemporaryDirectory(prefix='ontokin-program-demo-') as temporary, ProgramAgentService(Path(temporary)) as service:
        serial = 0
        def call(operation, *, expected='succeeded', **fields):
            nonlocal serial
            serial += 1
            request = {'schema_version':'ontokin.agent/0.2','project_id':'construction-demonstration',
                       'request_id':f'step-{serial:03d}-{operation}','operation':operation,**fields}
            response = service.handle(request)
            transcript.append({'request':request,'response':response})
            if response['status'] != expected:
                raise AssertionError(f'{operation}: {response}')
            return response
        def check(name, condition, **observed):
            if not condition:
                raise AssertionError(f'{name}: {observed}')
            checks.append({'name':name,'passed':True,'observed':observed})
        discovered = call('discover',profile='construction-0.1',bundle=seed,filter={'kind':'class','name':'Finger'},limit=10)
        check('Discover the actual pinned public component',bool(discovered['result']['items']))
        created = call('create',bundle=seed,expected_program_revision=None,requested_level='evaluated')
        initial = created['program_revision']
        check('Accept the complete initial closure at evaluated level',initial==initial_bundle.program_revision and created['accepted_program_revision']==initial and created['achieved_level']=='evaluated')
        inspected = call('inspect',program_revision=initial,selector={'path':'first.fingers["middle"].length'},fields=['identity','source','values'],limit=1)
        target = inspected['result']['items'][0]['source']['initializer_target']
        check('Find an occurrence initializer without granting shared bytes',target['available'] and target['rendered_path']=='fingers["middle"].length' and not inspected['result']['items'][0]['source']['writable_spans'])
        start = initial_bundle.entry.raw.index(b'0.65[m]')
        def patch(replacement):
            return {'source_id':'entry','source_revision':initial_bundle.entry.revision,'element_id':target['element_id'],
                    'start_byte':start,'end_byte':start+len(b'0.65[m]'),'expected_text':'0.65[m]','replacement':replacement}
        rejected = call('edit',expected='rejected',expected_program_revision=initial,requested_level='evaluated',patches=[patch('0.75[kg]')])
        check('Invalid units preserve the accepted whole program',rejected['accepted_program_revision']==initial and any(d['code']=='OKL-E-UNIT' for d in rejected['diagnostics']))
        candidate = call('inspect',program_revision=rejected['program_revision'],selector={'kind':'source','source_id':'entry'},fields=['source'],limit=1)
        rejected_source = candidate['result']['source_units'][0]
        diagnostic = next(d for d in rejected['diagnostics'] if d['code']=='OKL-E-UNIT')
        span = diagnostic['primary']
        check('Rejected-candidate diagnostics identify its actual file bytes',diagnostic['program_revision']==rejected['program_revision'] and diagnostic['source_revision']==rejected_source['source_revision'] and span['source_id']=='entry' and rejected_source['source'].encode()[span['start_byte']:span['end_byte']]==b'0.75[kg]')
        repaired = call('edit',expected_program_revision=initial,requested_level='evaluated',patches=[patch('0.75[m]')])
        revision = repaired['program_revision']
        check('Repair reproduces the independently specified program',revision==oracle['program_revision'] and revision!=initial)
        source_result = call('inspect',program_revision=revision,selector={'kind':'source'},fields=['source'],limit=17)
        sources = {unit['source_id']:unit for unit in source_result['result']['source_units']}
        check('Repair preserves the library bytes and changes only the selected initializer',sources['entry']['source']==final_payload['entry']['source'] and sources[initial_bundle.modules[0].source_id]['source'].encode()==initial_bundle.modules[0].raw)
        (output/'authoring.ok').write_bytes(seed['entry']['source'].encode('utf-8'))
        (output/'rejected-candidate.ok').write_bytes(rejected_source['source'].encode('utf-8'))
        (output/'main.ok').write_bytes(sources['entry']['source'].encode('utf-8'))
        (output/'hinges.ok').write_bytes(sources[initial_bundle.modules[0].source_id]['source'].encode('utf-8'))
        write_json(output/'program.bundle.json',final_payload)
        write_json(output/'program.files.json',json.loads((fixtures/'program.files.json').read_text()))
        observed = call('inspect',program_revision=revision,selector={'kind':'object'},fields=['identity','geometry','matter'],limit=100)['result']['items']
        check('Three-key and five-key assemblies contain exactly18 real objects',len(observed)==18)
        by_path = {item['path']:item for item in observed}
        max_geometry_error = 0.
        for expected in oracle['objects']:
            item = by_path[expected['path']]
            check('Stable identity and nominal definition: '+expected['path'],item['element_id']==expected['element_id'] and item['identity']['definition_id']==expected['definition_id'])
            geometry = item['geometry']['description']
            values = geometry['size'] if geometry['kind']=='box' else [geometry['radius']]
            wanted = expected['geometry']['size_m'] if geometry['kind']=='box' else [expected['geometry']['radius_m']]
            error=max(abs(x-y) for x,y in zip(values,wanted))
            max_geometry_error=max(max_geometry_error,error)
            if geometry['kind']!=expected['geometry']['kind'] or error>oracle['comparison']['geometry_dimension_tolerance_m'] or item['matter']['own_mass_kg']!=0 or item['matter']['owned_aggregate_mass_kg']!=0:
                raise AssertionError('Independent geometry/matter expectation: '+expected['path'])
        check('Decoded source geometry and zero matter match independent expectations',max_geometry_error<=1e-12,max_geometry_error_m=max_geometry_error)
        run = call('evaluate',program_revision=revision,run_id=None,until_seconds='0.5')
        check('Evaluate only the requested initial prefix',run['result']['run_state']['valid_until_seconds']=='0.5')
        advanced = call('evaluate',program_revision=revision,run_id=run['run_id'],until_seconds='2')
        check('Advance the same ordinary run to the horizon',advanced['run_id']==run['run_id'] and advanced['result']['run_state']['valid_until_seconds']=='2')
        samples=[]
        max_position=max_rotation=0.
        poses=0
        for expected_sample in oracle['samples']:
            result = call('inspect',program_revision=revision,run_id=run['run_id'],time={'seconds':expected_sample['seconds'],'side':expected_sample['side']},selector={'kind':'object'},fields=['state'],limit=100)['result']
            actual = {item['path']:item['state'] for item in result['items']}
            samples.append({'time_seconds':expected_sample['seconds'],'objects':{path:{'position_m':state['position_m'],'orientation_wxyz':state['orientation_wxyz']} for path,state in actual.items()}})
            for expected in expected_sample['objects']:
                state=actual[expected['path']]
                position_error=max(abs(x-y) for x,y in zip(state['position_m'],expected['position_m']))
                angle_error=rotation_error(state['orientation_wxyz'],expected['rotation_wxyz'])
                max_position=max(max_position,position_error);max_rotation=max(max_rotation,angle_error);poses+=1
                if position_error>1e-9 or angle_error>1e-9:
                    raise AssertionError(f'Independent pose expectation: {expected_sample["seconds"]} {expected["path"]}')
        check('All126 inspected world poses match the independent formula oracle',poses==126,max_position_error_m=max_position,max_rotation_error_rad=max_rotation)
        exported = call('export',program_revision=revision,destination='ontokin.glb/0.2',options={})
        report = exported['result']['report']
        data,offset=bytearray(),0
        while offset is not None:
            result=call('artifact',artifact_id=exported['result']['artifact_id'],offset=offset,max_bytes=65536)['result']
            check(f'Artifact chunk at {offset} retains program context',result['program_revision']==revision and result['offset']==len(data))
            data.extend(base64.b64decode(result['data_base64'],validate=True));offset=result['next_offset']
        artifact_hash='sha256:'+hashlib.sha256(data).hexdigest()
        check('Retrieved real GLB matches its delivery hash and new contract',bytes(data[:4])==b'glTF' and artifact_hash==report['artifact']['sha256'] and report['target_contract']=='ontokin.glb/0.2' and report['program_revision']==revision and report['validation']['status']=='passed')
        (output/'keyed-rack.glb').write_bytes(data)
        write_json(output/'keyed-rack.export.json',report)
        write_json(output/'keyed-rack.reference.json',{'schema_version':'ontokin.viewer-reference/0.2','program_revision':revision,
                   'source_manifest':load_bundle(final_payload).manifest(),'artifact_sha256':artifact_hash,'tolerances':report['tolerances'],
                   'geometry':oracle['objects'],'samples':samples,'independent_oracle':{'path':str((fixtures/'expected.json').relative_to(ROOT)),
                   'sha256':'sha256:'+hashlib.sha256((fixtures/'expected.json').read_bytes()).hexdigest(),'pose_comparisons':poses,
                   'max_position_error_m':max_position,'max_rotation_error_rad':max_rotation}})
        write_json(output/'workflow.json',{'schema_version':'ontokin.program-agent-workflow/0.1','status':'passed',
                   'generated_at_utc':datetime.now(timezone.utc).isoformat(),'implementation':service.implementation,
                   'scope':'Actual pinned-library, keyed-construction, diagnosis, scoped repair, prefix evaluation and GLB retrieval through program-agent requests; no authoring-efficiency benchmark.',
                   'initial_program_revision':initial,'rejected_program_revision':rejected['program_revision'],'accepted_program_revision':revision,
                   'source_manifest':load_bundle(final_payload).manifest(),'artifact_sha256':artifact_hash,'checks':checks,
                   'operation_count':len(transcript),'operations':transcript})
    return {'status':'passed','program_revision':revision,'artifact_sha256':artifact_hash,'checks':len(checks),
            'operations':len(transcript),'independent_pose_comparisons':poses,'output_dir':str(output)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'examples/construction')
    print(json.dumps(build(parser.parse_args().output_dir),indent=2))
