#!/usr/bin/env python3
"""Run frozen C075 source cases and the actual editable Agent/0.8 workflow."""
from __future__ import annotations
import argparse,base64,copy,hashlib,json,platform,sqlite3,sys,tempfile,traceback
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ontokin.bundle import ProgramBundle,SourceUnit
from ontokin.budget_runtime import execute_extrusion_export
from ontokin.extrusion_agent import ExtrusionAgentService
from ontokin.execution_budget import HostPolicy
from ontokin.scene import ExportOptions
from tools.extrusion_oracles import Decoded,check_geometry,close
from tools.check_local import git_metadata,inventory

F=ROOT/'examples/polygon-extrusions'
PROFILE='polygon-extrusion-0.1';PROTOCOL='ontokin.agent/0.8';TARGET='ontokin.glb/0.8'
OPTIONS={'fps':4,'end':'1','helpers':False}
def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def bundle(name):
    raw=(F/name).read_bytes();modules=()
    if 'corrected/' in name:
        modules=(SourceUnit('package:fixture.extrusion-parts@1.0.0','parts.ok',(F/'parts.ok').read_bytes(),'fixture.extrusion-parts','1.0.0'),)
    return ProgramBundle(SourceUnit('entry',Path(name).name,raw),modules)
def patch(source,old,new):
    start=source.entry.raw.index(old.encode())
    return {'source_id':'entry','source_revision':source.entry.revision,'element_id':['sources','entry'],'start_byte':start,'end_byte':start+len(old.encode()),'expected_text':old,'replacement':new}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();out=a.output_dir.resolve()
    assert not out.is_relative_to(ROOT);out.mkdir(parents=True,exist_ok=False)
    summary={'schema_version':'ontokin.extrusion-acceptance/0.1','status':'running','started_utc':datetime.now(timezone.utc).isoformat(),'git':git_metadata(ROOT),'python':sys.version,'platform':platform.platform(),'cases':[],'assertions':[],'artifacts':[],'release_acceptance':False}
    transcript=[];services=[];temp=tempfile.TemporaryDirectory(prefix='ontokin-c075-live-');serial=0
    before=inventory(ROOT);save(out/'source-before.json',before)
    def check(value,label):
        summary['assertions'].append({'label':label,'passed':bool(value)})
        if not value:raise AssertionError(label)
    def req(op,**fields):
        nonlocal serial
        serial+=1
        return {'schema_version':PROTOCOL,'project_id':'c075','request_id':f'c075-{serial}','operation':op,**fields}
    def call(payload,wait=True):
        response=service.handle(payload,wait=wait)
        transcript.append({'sequence':len(transcript)+1,'request':payload,'response':response})
        save(out/f'exchange-{len(transcript):03}.json',transcript[-1])
        return response
    def success(payload):
        response=call(payload);check(response['status']=='succeeded',payload['operation']+' succeeded');return response
    def artifact(name,data,program,nodes):
        (out/(name+'.glb')).write_bytes(data)
        decoded=Decoded(data);check(set(decoded.objects())==set(nodes),name+' exact carrier inventory')
        measured=[]
        for path,wanted in nodes.items():
            if wanted['geometry'] is not None:measured.append(check_geometry(decoded,path,wanted['geometry']))
            for t in [0,.25,.5,.75,1]:
                pose=decoded.pose(path,t);origin=wanted['origin'];v=wanted['velocity']
                close(pose['translation'],[origin[i]+t*v[i] for i in range(3)],.001);close(pose['rotation'],[0,0,0,1],.001)
        meta=decoded.document['extras']['ontokin'];check(meta['program']['revision']==program.program_revision,name+' source revision in decoded GLB')
        expectation={'schema_version':'ontokin.extrusion-destination-expected/0.1','case_id':name,'program_revision':program.program_revision,'duration_seconds':1,'nodes':nodes}
        save(out/(name+'.expected.json'),expectation)
        summary['artifacts'].append({'name':name,'path':name+'.glb','bytes':len(data),'sha256':sha(data),'program_revision':program.program_revision,'geometry':measured,'native_poses':5*len(nodes)})
        return decoded
    try:
        original=json.loads((F/'acceptance-freeze.json').read_text());correction=json.loads((F/'acceptance-correction-001.json').read_text())
        for files in (original['files'],correction['corrected_files']):
            for name,w in files.items():
                b=(F/name).read_bytes();check({'bytes':len(b),'sha256':sha(b)}==w,'Frozen input '+name)
        expected=json.loads((F/correction['selected_expected']).read_text())
        save(out/'input-freeze.json',{'original':original,'correction':correction})
        exports={}
        for case in expected['cases']:
            source=bundle(case['source']);result=execute_extrusion_export(source,options=ExportOptions(fps=4,end='1',helpers=False))
            save(out/(case['id']+'.receipt.json'),result.report)
            record={'id':case['id'],'expected':case['expected_outcome'],'actual':'delivered' if result.data is not None else 'rejected','operations':(result.report.get('execution_budget') or {}).get('consumed_operations')}
            summary['cases'].append(record)
            if case['expected_outcome']=='valid':
                check(result.data is not None,case['id']+' delivered');exports[case['id']]=result.data
                artifact(case['id'],result.data,source,{'shape':{'geometry':case['geometry'],'origin':[0,0,0],'velocity':[0,.5,0]}})
            else:
                check(result.data is None,case['id']+' rejected without artifact')
                codes=[d['code'] for d in result.report.get('diagnostics',[])]
                if case.get('diagnostic_code'):check(case['diagnostic_code'] in codes,case['id']+' expected diagnostic')
                if case['expected_outcome']=='source_valid_delivery_rejected':check(result.report.get('achieved_level')=='evaluated',case['id']+' constructed/evaluated but not delivered')
            record['status']='passed'
        # Same keyed geometry under text reordering, despite different source revisions
        left=Decoded(exports['concave-bracket']).triangles('shape');right=Decoded(exports['reordered-bracket']).triangles('shape')
        content=lambda rows:[(region,positions,normals,material['pbrMetallicRoughness']) for region,positions,normals,material in rows]
        check(content(left)==content(right),'Declaration reordering preserves decoded topology and materials')
        generated=bundle(expected['generated']['entry']);g=execute_extrusion_export(generated,options=ExportOptions(fps=4,end='1',helpers=False));check(g.data is not None,'Generated reusable parts export')
        nodes={'array':{'geometry':None,'origin':[-8,0,0],'velocity':[0,.5,0]}}
        for key,item in expected['generated']['parts'].items():nodes['array.brackets['+json.dumps(key)+']']={'geometry':item['geometry'],'origin':[-8+item['mount_x_m'],0,0],'velocity':[0,.5,0]}
        artifact('generated',g.data,generated,nodes)
        service=ExtrusionAgentService(Path(temp.name)/'agent');services.append(service)
        success(req('discover',profile=PROFILE,limit=1000))
        original_source=bundle(expected['assembly']['entry'])
        repaired_source=ProgramBundle(SourceUnit('entry',original_source.entry.filename,(F/expected['assembly']['repaired_entry']).read_bytes()),original_source.modules)
        success(req('create',bundle=original_source.to_payload(),expected_program_revision=None,requested_level='constructed'))
        success(req('inspect',program_revision=original_source.program_revision,selector={'kind':'source'},fields=['identity','source'],limit=100))
        first=['extrusion-assembly','demo','first'];sibling=['extrusion-assembly','demo','sibling']
        old_page=success(req('surface.mesh_page',program_revision=original_source.program_revision,element_id=sibling,count=256))['result']
        first_response=success(req('surface.mesh_page',program_revision=original_source.program_revision,element_id=first,count=3))
        first_page=first_response['result'];first_cursor=first_response['next_cursor']
        check(first_cursor is not None,'Bounded mesh page yields cursor')
        old='"v3": polygon_vertex(30, planar_point(1[m], 1[m]), "side")'
        invalid=old.replace('1[m], 1[m]','3[m], 0[m]')
        rejected=call(req('edit',expected_program_revision=original_source.program_revision,requested_level='constructed',patches=[patch(original_source,old,invalid)]))
        check(rejected['status'] in ['failed','rejected'] and service.accepted_revision('c075')==original_source.program_revision,'Invalid vertex edit rolls back accepted revision')
        repaired=success(req('edit',expected_program_revision=original_source.program_revision,requested_level='constructed',patches=[patch(original_source,old,old.replace('1[m], 1[m]','1.5[m], 1[m]'))]))
        check(repaired['accepted_program_revision']==repaired_source.program_revision,'Exact vertex repair selects frozen repaired bundle')
        new_page=success(req('surface.mesh_page',program_revision=repaired_source.program_revision,element_id=sibling,count=256))['result']
        fields=['positions_m','normals','triangles','region_keys','source_triangle_ordinals']
        check(all(old_page[f]==new_page[f] for f in fields),'Sibling mesh unchanged by first-instance repair')
        check(original_source.modules[0].raw==repaired_source.modules[0].raw,'Pinned library bytes unchanged by repair')
        stale=call(req('surface.mesh_page',program_revision=repaired_source.program_revision,element_id=first,count=3,cursor=first_cursor))
        check(stale['status'] in ['failed','rejected'],'Old-revision cursor rejected after repair')
        evaluation=req('evaluate',program_revision=repaired_source.program_revision,run_id=None,until_seconds='1');evaluated=success(evaluation)
        check(call(evaluation)==evaluated,'Identical request returns durable receipt')
        mutated=copy.deepcopy(evaluation);mutated['until_seconds']='0.5';check(call(mutated)['status']=='rejected','Changed retry payload rejected')
        exported=success(req('export',program_revision=repaired_source.program_revision,destination=TARGET,options=OPTIONS));aid=exported['result']['artifact_id']
        chunks=[];offset=0
        while True:
            part=success(req('artifact',artifact_id=aid,offset=offset,max_bytes=1024))['result'];chunks.append(base64.b64decode(part['data_base64'],validate=True))
            check(part['offset']==offset and part['program_revision']==repaired_source.program_revision,'Chunk offset and source binding')
            if part['next_offset'] is None:break
            offset=part['next_offset']
        data=b''.join(chunks);check('sha256:'+sha(data)==exported['result']['sha256'] and len(data)==exported['result']['total_bytes'],'Retrieved artifact exact bytes')
        artifact('agent-repaired',data,repaired_source,{'first':{'geometry':expected['assembly']['repaired_first'],'origin':[-2,0,0],'velocity':[0,.5,0]},'sibling':{'geometry':expected['assembly']['sibling'],'origin':[2,0,0],'velocity':[0,0,0]}})
        summary['agent_export_operations']=exported['execution_budget']['consumed_operations']
        success(req('reset',program_revision=repaired_source.program_revision))
        pending=req('validate',program_revision=repaired_source.program_revision,requested_level='constructed');queued=call(pending,wait=False)
        success(req('cancel',target_request_id=pending['request_id']));status=success(req('status',target_request_id=pending['request_id']))
        check(queued['status']=='queued' and status['result']['target_status']=='cancelled','Queued cancellation retains terminal status')
        service.host_policy=HostPolicy(50000,30000);denied=call(req('artifact',artifact_id=aid,max_bytes=1024))
        check(denied['status'] in ['failed','rejected'] and denied['execution_budget']['budget_reason']=='host_ceiling_exceeded','New artifact request uses current lower host policy')
        service.host_policy=HostPolicy()
        # Local-only schema registry validates every actual envelope, including failures
        from jsonschema import Draft202012Validator
        from referencing import Registry,Resource
        paths=list((ROOT/'docs/language-design/agent-v0.8').glob('*.schema.json'))+[ROOT/'docs/language-design/construction-v0.1/bundle.schema.json']
        paths += [ROOT/'docs/language-design'/name for name in ['agent-v0.2/diagnostic.schema.json','force-v0.1/forces.schema.json','impulse-v0.1/impulses.schema.json','planar-reach-v0.1/schema-drafts/reach-projection.schema.json','planar-reach-v0.1/schema-drafts/reach-diagnostic.schema.json','planar-reach-v0.1/schema-drafts/common.schema.json']]
        schemas=[json.loads(p.read_text()) for p in paths];registry=Registry().with_resources((s['$id'],Resource.from_contents(s)) for s in schemas)
        for s in schemas:Draft202012Validator.check_schema(s)
        validators={p.name:Draft202012Validator(s,registry=registry) for p,s in zip(paths,schemas)}
        for row in transcript:
            validators['request.schema.json'].validate(row['request']);validators['response.schema.json'].validate(row['response'])
        summary['schema_validated_exchanges']=len(transcript)
        with service._store.connection() as db:summary['durable_requests']=db.execute('SELECT count(*) FROM requests').fetchone()[0]
        check(summary['durable_requests']==len({r['request']['request_id'] for r in transcript}),'Every unique request retained in durable store')
        after=inventory(ROOT);save(out/'source-after.json',after);check(before==after,'Complete source unchanged during acceptance')
        summary['status']='passed'
    except BaseException as error:
        summary['status']='failed';summary['failure']={'type':type(error).__name__,'message':str(error)};(out/'failure.traceback').write_text(traceback.format_exc())
    finally:
        for s in services:
            s.close()
            with sqlite3.connect(s.database_path) as src,sqlite3.connect(out/s.database_path.name) as dst:src.backup(dst)
        temp.cleanup();(out/'protocol.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in transcript))
        summary['exchanges']=len(transcript);summary['finished_utc']=datetime.now(timezone.utc).isoformat();save(out/'summary.json',summary)
    print(json.dumps({k:summary.get(k) for k in ['status','exchanges','durable_requests','schema_validated_exchanges','agent_export_operations','failure']}))
    return 0 if summary['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
