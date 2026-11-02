#!/usr/bin/env python3
"""Produce actual C087 source, Agent and ledger evidence in a fresh directory.

Frozen inputs and independent output readers are separate authorities. This
producer records actual results and never rewrites expected values from them.
"""
from __future__ import annotations
import argparse,base64,copy,gzip,hashlib,importlib.util,json,platform,sqlite3,subprocess,sys,traceback
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
# Resolve the explicitly selected immutable runtime cut before importing any
# shared producer modules. Syntax compilation of this file executes none of it.
_bootstrap=argparse.ArgumentParser(add_help=False)
_bootstrap.add_argument('--checkout',type=Path,default=ROOT)
_bootstrap.add_argument('--reference-path',type=Path)
_boot,_unused=_bootstrap.parse_known_args()
ROOT=_boot.checkout.resolve();sys.path.insert(0,str(ROOT))
if _boot.reference_path:sys.path.insert(0,str(_boot.reference_path.resolve().parent.parent))

def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(raw):return 'sha256:'+sha(raw)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def codes(value):
    if isinstance(value,dict):return sorted(set(([value['code']] if isinstance(value.get('code'),str) else [])+[x for v in value.values() for x in codes(v)]))
    if isinstance(value,list):return sorted(set(x for v in value for x in codes(v)))
    return []
def error_record(error):
    result={'exception':type(error).__name__,'message':str(error),'traceback':''.join(traceback.format_exception(type(error),error,error.__traceback__))}
    if hasattr(error,'diagnostic'):
        d=error.diagnostic;n=d.node
        result['diagnostic']={'code':d.code,'phase':d.phase,'category':d.category,'message':d.message,'details':d.details,'repair':d.repair,'rule_ids':d.rule_ids,'primary':None if n is None else {'source_id':getattr(n,'source_id',None),'start_byte':n.start,'end_byte':n.end,'element_id':d.element_id},'related':[{'source_id':getattr(x,'source_id',None),'start_byte':x.start,'end_byte':x.end} for x in d.related]}
    return result
def inventory(root):return [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink() and p.name!='inventory.json' and 'live-store' not in p.parts]
def compressed(path,value):
    raw=canonical(value);packed=gzip.compress(raw,mtime=0);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(packed)
    return {'raw_bytes':len(raw),'raw_sha256':sha(raw),'gzip_bytes':len(packed),'gzip_sha256':sha(packed)}
def normalize(value):
    if value.type.kind=='Keyed':return {'type':str(value.type),'entries':[{'key':k,'value':normalize(v)} for k,v in value.value.entries]}
    return {'type':str(value.type),'value':value.value if value.known else None}

class SourceContext:
    def __init__(self,policy,profile,caller_caps=None):
        from ontokin.execution_budget import SharedExecutionBudget
        self.execution_budget=SharedExecutionBudget(policy=policy,caller_caps=caller_caps);self.profile=profile
    def __call__(self):self.execution_budget.tick()
    def admit(self,source):
        from ontokin.execution_budget import admit_entry_budget
        if self.execution_budget.resolved is None:admit_entry_budget(source.entry,self.execution_budget,profile=self.profile)
        elif self.execution_budget.admitted_entry_revision!=source.entry.revision:raise ValueError('Different source cannot share one admitted context')

# The workflow module imports only recording helpers until instantiated.
from string_concat_agent_workflows import StringConcatAgentWorkflows
from string_concat_observer import StringExecutionObserver

class Acceptance(StringConcatAgentWorkflows):
    def __init__(self,fixtures,output,reference):
        from ontokin.execution_budget import HostPolicy
        from ontokin.string_concat_agent import StringConcatAgentService
        from ontokin.string_concat_program_runtime import StringConcatProgramRuntime
        from ontokin.keyed_rekey_program_runtime import KeyedRekeyProgramRuntime
        from ontokin.budget_runtime import execute_string_concat_export,execute_keyed_rekey_export
        from ontokin.texture_bundle import load_texture_file_manifest
        from ontokin.scene import ExportOptions
        self.fixtures=fixtures;self.output=output;self.reference=reference;self.fixture_root=Path(fixtures['core_root'])
        self.HostPolicy=HostPolicy;self.Service=StringConcatAgentService;self.Runtime=StringConcatProgramRuntime;self.ControlRuntime=KeyedRekeyProgramRuntime
        self.execute=execute_string_concat_export;self.execute_control=execute_keyed_rekey_export;self.load_files=load_texture_file_manifest;self.options=ExportOptions(fps=4,end='1',helpers=False)
        self.serial=0;self.transcript=[];self.service=None;self.project='';self.scenario=None
        self.lineage=reference.input_lineage(fixtures)
        git=lambda *args:subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
        self.summary={**self.lineage,'schema_version':'ontokin.c087-actual-evidence/0.1','status':'running','started_utc':datetime.now(timezone.utc).isoformat(),'command':[sys.executable,*sys.argv],'python':sys.version,'platform':platform.platform(),'git':{'commit':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':git('status','--porcelain')},'profile':'string-concat-0.1','target_contract':'ontokin.glb/0.20','agent_contract':'ontokin.agent/0.20','core_case_count':len(fixtures['core_cases']),'agent_source_state_count':len(fixtures['agent_cases']),'cases':[],'controls':[],'predecessor_negative_controls':[],'workflows':[],'agent_artifacts':[],'additional_stores':[],'snapshots':[],'reopens':[],'boundaries':[],'failures':[],'release_acceptance':False,'independent_verification':'not_run_by_this_producer','destination_verification':'not_run_by_this_producer','hostile_stream_verification':'separate independent reader role'}
        self.schema_validators=self.schemas()
        save(output/'implementation-inventory.json',[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())} for p in sorted((ROOT/'ontokin').glob('*.py'))])
        save(output/'producer-inventory.json',[{'path':p.name,'sha256':sha(p.read_bytes())} for p in sorted(HERE.glob('*string_concat*.py'))])
    @staticmethod
    def check(value,label):
        if not value:raise AssertionError(label)
    def schemas(self):
        import importlib.metadata
        from jsonschema import Draft202012Validator
        from referencing import Registry,Resource
        resources={}
        for path in sorted((ROOT/'docs/language-design').rglob('*.schema.json')):
            value=json.loads(path.read_bytes())
            if '$id' in value:resources[value['$id']]=Resource.from_contents(value)
        registry=Registry().with_resources(resources.items());result={};records=[]
        for path in sorted((ROOT/'docs/language-design/agent-v0.20').glob('*.schema.json')):
            value=json.loads(path.read_bytes());Draft202012Validator.check_schema(value);result[path.name]=Draft202012Validator(value,registry=registry);records.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes()),'id':value.get('$id')})
        self.check('request.schema.json' in result and 'response.schema.json' in result,'Actual .20 schemas required')
        save(self.output/'schema-inventory.json',{'schemas':records,'jsonschema_version':importlib.metadata.version('jsonschema'),'referencing_version':importlib.metadata.version('referencing')});return result
    def payload(self,name):return self.reference.case_payload(self.fixtures,name)
    def case_root(self,case):return Path(self.fixtures['agent_root'] if case['name'] in self.fixtures['agent_cases'] else self.fixtures['core_root'])
    def binding(self,source):
        legacy=source.entry.raw.lstrip().startswith(b'ontokin "0.19";')
        return (self.ControlRuntime(),'keyed-rekey-0.1') if legacy else (self.Runtime(),'string-concat-0.1')
    def source_observation(self,source,case,prefix,*,trace=False):
        runtime,profile=self.binding(source);ctx=SourceContext(self.HostPolicy(**case['host_policy']),profile);observer=StringExecutionObserver(ctx.execution_budget)
        try:
            if trace:
                with observer:result=runtime.validate_revision(source,level='constructed',check=ctx)
            else:result=runtime.validate_revision(source,level='constructed',check=ctx)
        finally:
            if trace:
                save(self.output/(prefix+'.concat-execution-trace.json'),observer.report(**self.lineage,case=case['name'],program_revision=source.program_revision,public_api=type(runtime).__name__+'.validate_revision',profile=profile,requested_level='constructed'))
                meta=compressed(self.output/(prefix+'.concat-values.json.gz'),{'helper_values':observer.helper_values})
                save(self.output/(prefix+'.concat-values-receipt.json'),meta)
        receipt={'schema_version':'ontokin.c087-source-observation/0.1',**self.lineage,'public_api':type(runtime).__name__+'.validate_revision','profile':profile,'program_revision':source.program_revision,'requested_level':'constructed','result':result,'execution_budget':ctx.execution_budget.report(status=result['outcome'])}
        save(self.output/(prefix+'.receipt.json'),receipt);return result
    def inspection(self,source,case,prefix):
        runtime,profile=self.binding(source);ctx=SourceContext(self.HostPolicy(**case['host_policy']),profile)
        query={'selector':{'kind':'object'},'fields':['identity','source','values','geometry','matter'],'limit':1000}
        result=runtime.inspect_revision(source,check=ctx,**query);save(self.output/(prefix+'.inspection.json'),result)
        save(self.output/(prefix+'.inspection-receipt.json'),{'schema_version':'ontokin.c087-source-inspection-observation/0.1',**self.lineage,'public_api':type(runtime).__name__+'.inspect_revision','profile':profile,'program_revision':source.program_revision,'query':query,'execution_budget':ctx.execution_budget.report(status=result['outcome'])})
        if result['outcome']!='valid':
            # Record an actual supported bounded identity page as well. Complete
            # ordinary values remain required in the separate private read.
            ctx=SourceContext(self.HostPolicy(**case['host_policy']),profile);small={'selector':{'kind':'object'},'fields':['identity','source'],'limit':1}
            page=runtime.inspect_revision(source,check=ctx,**small);save(self.output/(prefix+'.bounded-identity-inspection.json'),page)
            self.check(page['outcome']=='valid','Bounded identity inspection must remain available')
        return prefix+'.inspection.json'
    def private_values(self,source,case,prefix):
        from ontokin.construction import compile_construction
        _,profile=self.binding(source);ctx=SourceContext(self.HostPolicy(**case['host_policy']),profile);ctx.admit(source)
        compiler=compile_construction(source,level='constructed',execution_budget=ctx.execution_budget)
        selected=[('first','renamed'),('sibling','renamed')] if case['name'] in self.fixtures['agent_cases'] else [('shape','result')]
        actual={};provenance={}
        for path,name in selected:
            value=compiler.field(path,name,compiler.program);key=path+'.'+name;actual[key]=normalize(value)
            dependencies=[]
            for p,n in sorted(compiler.dependencies.get((path,name),set())):
                inst=compiler.instances.get(p);member=None if inst is None else inst.cls.members.get(n)
                ids=None if inst is None else list(inst.model.element_id)+(['@system',n] if member is None else [member.node.key])
                dependencies.append({'element_id':ids,'path':p+('.'+n if not n.startswith('@') else ''),'program_revision':source.program_revision,'relationship':'effective_value_dependency'})
            dependencies += [{'element_id':list(ids),'program_revision':source.program_revision,'relationship':'called_definition'} for ids in sorted(compiler.call_dependencies.get((path,name),set()))]
            def records(v):
                result={}
                for family,method in [('rekeys','rekey_provenance'),('zips','zip_provenance'),('merges','merge_provenance'),('filters','filter_provenance'),('reductions','reduction_provenance'),('transforms','transform_provenance')]:
                    getter=getattr(compiler,method,None)
                    if getter is not None:result[family]=getter(v)
                return result
            provenance[key]={'dependencies':dependencies,'aggregate':records(value),'leaves':{k:records(v) for k,v in value.value.entries} if value.type.kind=='Keyed' else {},'generated_dependencies':sorted(compiler.generated_dependencies.get((path,name),set()))}
        normalized=actual['shape.result'] if selected==[('shape','result')] else {'values':actual}
        meta=compressed(self.output/(prefix+'.private-values.json.gz'),normalized)
        save(self.output/(prefix+'.private-provenance.json'),{'program_revision':source.program_revision,'values':provenance})
        save(self.output/(prefix+'.private-value-receipt.json'),{'schema_version':'ontokin.c087-private-ordinary-value-observation/0.1',**self.lineage,'program_revision':source.program_revision,'api':'compile_construction then actual compiler.field','selected_fields':[p+'.'+n for p,n in selected],**meta,'execution_budget':ctx.execution_budget.report(status='valid'),'public_response_limit_override':False})
        return prefix+'.private-values.json.gz'
    def run_sources(self):
        for case in [*self.fixtures['core_cases'].values(),*self.fixtures['agent_cases'].values()]:
            record={k:case[k] for k in ('id','name','file_manifest','expected_outcome','expected_code','expected_stage','host_policy')};prefix='sources/'+case['name'];record.update(input_lineage=self.lineage,receipt=prefix+'.receipt.json',execution_trace=prefix+'.concat-execution-trace.json',helper_values=prefix+'.concat-values.json.gz',delivered=False)
            try:
                source=self.load_files(self.case_root(case)/case['file_manifest']);record['program_revision']=source.program_revision;self.check(source.program_revision==case['program_revision'],'Frozen source revision')
                result=self.source_observation(source,case,prefix,trace=True);record['diagnostic_codes']=codes(result)
                if case['expected_outcome']=='valid':
                    self.check(result['outcome']=='valid','Actual source construction must succeed')
                    record['private_values']=self.private_values(source,case,prefix);record['private_value_receipt']=prefix+'.private-value-receipt.json';record['private_provenance']=prefix+'.private-provenance.json';record['inspection']=self.inspection(source,case,prefix);record['inspection_receipt']=prefix+'.inspection-receipt.json'
                    if case['expected_stage']=='delivered':
                        exported=self.execute(source,policy=self.HostPolicy(**case['host_policy']),options=self.options);record['export_receipt']=prefix+'.export-receipt.json';save(self.output/record['export_receipt'],exported.report)
                        self.check(exported.data is not None,'Actual .20 delivered source artifact required');record.update(delivered=True,glb=prefix+'.glb',bytes=len(exported.data),sha256=sha(exported.data));(self.output/record['glb']).write_bytes(exported.data)
                else:
                    self.check(result['outcome']!='valid','Frozen refused source must refuse');self.check(case['expected_code'] in record['diagnostic_codes'],'Exact frozen source refusal code')
                    if case['expected_code']!='OKL-E-RESOURCE':self.check('OKL-E-RESOURCE' not in record['diagnostic_codes'],'Resource exhaustion cannot substitute for semantic refusal')
                record['producer_status']='observed_as_expected'
            except Exception as error:record.update(producer_status='failed',exception=error_record(error));self.summary['failures'].append({'scope':'source','name':case['name'],'error':str(error)})
            self.summary['cases'].append(record)
            if 'explicit_c086_control' in case:self.run_control(case,record)
            save(self.output/'summary.json',self.summary)
        negatives=json.loads((self.fixture_root/'negative-controls.json').read_text())['cases']
        for case in negatives:
            record={'name':case['name'],'file_manifest':case['file_manifest'],'program_revision':case['program_revision']};prefix='controls/negative-'+case['name']
            try:
                source=self.load_files(self.fixture_root/case['file_manifest']);result=self.source_observation(source,case,prefix);record['receipt']=prefix+'.receipt.json';self.check(result['outcome']!='valid' and case['diagnostic']['code'] in codes(result),'Inherited negative control must retain its refusal');record['producer_status']='observed_as_expected'
            except Exception as error:record.update(producer_status='failed',exception=error_record(error));self.summary['failures'].append({'scope':'negative_control','name':case['name'],'error':str(error)})
            self.summary['predecessor_negative_controls'].append(record)
    def run_control(self,case,source_record):
        spec=case['explicit_c086_control'];prefix='controls/'+case['name'];record={'name':case['name'],'file_manifest':spec['file_manifest'],'program_revision':spec['program_revision'],'receipt':prefix+'.receipt.json','host_policy':case['host_policy'],'input_lineage':self.lineage}
        try:
            source=self.load_files(self.case_root(case)/spec['file_manifest']);self.check(source.program_revision==spec['program_revision'],'Frozen .19 literal control revision');result=self.source_observation(source,case,prefix);self.check(result['outcome']=='valid','Actual explicit .19 control constructs')
            record['private_values']=self.private_values(source,case,prefix);record['private_value_receipt']=prefix+'.private-value-receipt.json';record['private_provenance']=prefix+'.private-provenance.json';record['inspection']=self.inspection(source,case,prefix);record['inspection_receipt']=prefix+'.inspection-receipt.json'
            if case['name'] in self.fixtures['agent_cases']:
                exported=self.execute_control(source,policy=self.HostPolicy(**case['host_policy']),options=self.options);record['export_receipt']=prefix+'.export-receipt.json';save(self.output/record['export_receipt'],exported.report);self.check(exported.data is not None,'Actual explicit .19 control delivers');record.update(glb=prefix+'.glb',bytes=len(exported.data),sha256=sha(exported.data));(self.output/record['glb']).write_bytes(exported.data);source_record['control']=record['glb']
            record['producer_status']='observed_as_expected'
        except Exception as error:record.update(producer_status='failed',exception=error_record(error));self.summary['failures'].append({'scope':'control','name':case['name'],'error':str(error)})
        self.summary['controls'].append(record)

    # Actual Agent recorder primitives; no verifier function is called here.
    def state(self):
        if self.service is None:return None
        revision=self.service.accepted_revision(self.project)
        with self.service._store.connection() as db:
            row=db.execute('SELECT raw FROM sources WHERE project_id=? AND revision=?',(self.project,revision)).fetchone() if revision else None
            runs=[dict(r) for r in db.execute('SELECT id,source_revision,descriptor,version FROM runs WHERE project_id=? ORDER BY id',(self.project,))]
            artifacts=[{'id':r[0],'program_revision':r[1],'bytes':len(r[2]),'sha256':sha(bytes(r[2])),'stored_sha256':r[3]} for r in db.execute('SELECT id,source_revision,data,sha256 FROM artifacts WHERE project_id=? ORDER BY id',(self.project,))]
        payload=json.loads(bytes(row[0])) if row else None
        return {'accepted_program_revision':revision,'accepted_payload_sha256':None if payload is None else sha(canonical(payload)),'assets':[] if payload is None else [{k:a[k] for k in ('asset_id','sha256','media_type')}|{'bytes':len(base64.b64decode(a['data_base64'],validate=True))} for a in payload.get('assets',[])],'runs':runs,'artifacts':artifacts}
    def call(self,request,*,wait=True):
        seq=len(self.transcript)+1;raw=json.dumps(request,ensure_ascii=False,allow_nan=False).encode();(self.output/f'agent/request-{seq:04}.json').write_bytes(raw);actual_request=json.loads(raw)
        row={'sequence':seq,'workflow':self.scenario,'wait':wait,'request':actual_request,'request_file':f'agent/request-{seq:04}.json','request_sha256':sha(raw),'state_before':self.state(),'host_policy':self.service.host_policy.ceilings,'request_schema_errors':[e.message for e in self.schema_validators['request.schema.json'].iter_errors(actual_request)]}
        try:
            response=self.service.handle(actual_request,wait=wait);wire=json.dumps(response,ensure_ascii=False,allow_nan=False).encode();(self.output/f'agent/response-{seq:04}.json').write_bytes(wire);row.update(response=copy.deepcopy(response),response_file=f'agent/response-{seq:04}.json',response_sha256=sha(wire),response_schema_errors=[e.message for e in self.schema_validators['response.schema.json'].iter_errors(response)])
        except BaseException as error:row['exception']=error_record(error);raise
        finally:row['state_after']=self.state();self.transcript.append(row);save(self.output/f'agent/exchange-{seq:04}.json',row)
        self.check(not row['request_schema_errors'],'Actual request schema failure');self.check(not row['response_schema_errors'],'Actual response schema failure');return response
    def success(self,operation,**fields):
        result=self.call(self.request(operation,**fields));self.check(result['status']=='succeeded',operation+' must succeed: '+str(codes(result)));return result
    def refuse(self,code,operation,**fields):
        result=self.call(self.request(operation,**fields));self.check(result['status'] in ('failed','rejected') and code in codes(result),operation+' must refuse with '+code+': '+str(codes(result)));return result
    def accepted_same(self,before,*,all_effects=False):
        after=self.state();self.check(before==after if all_effects else all(before[k]==after[k] for k in ('accepted_program_revision','accepted_payload_sha256','assets')),'Rejected work changed accepted durable effects')
    def edit_fields(self,before,after,**extra):
        before_revision=self.reference.bundle_identity(before)[0];after_revision=self.reference.bundle_identity(after)[0]
        matches=[e for e in self.fixtures['agent_expected']['source_edits'] if e['patches'] and e['patches'][0]['before_revision']==before_revision and e['patches'][0]['after_revision']==after_revision]
        if matches:return {**self.repair_fields(before,after),**extra}
        old,new=before['entry']['source'].encode(),after['entry']['source'].encode();start=0
        while start<min(len(old),len(new)) and old[start]==new[start]:start+=1
        # Stay on whole UTF-8 scalar boundaries for the exact source patch.
        while start and start<len(old) and old[start]&0xC0==0x80:start-=1
        end_old,end_new=len(old),len(new)
        while end_old>start and end_new>start and old[end_old-1]==new[end_new-1]:end_old-=1;end_new-=1
        while end_old<len(old) and old[end_old]&0xC0==0x80:end_old+=1;end_new+=1
        patches=[] if old==new else [{'source_id':'entry','source_revision':digest(old),'element_id':['sources','entry'],'start_byte':start,'end_byte':end_old,'expected_text':old[start:end_old].decode(),'replacement':new[start:end_new].decode()}]
        return {'expected_program_revision':self.reference.bundle_identity(before)[0],'requested_level':'constructed','patches':patches,**extra}

def main():
    global ROOT
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkout',type=Path,default=ROOT);p.add_argument('--reference-path',type=Path);p.add_argument('--fixtures',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--section',choices=('all','sources','agent','boundaries'),default='all');a=p.parse_args()
    ROOT=a.checkout.resolve();sys.path.insert(0,str(ROOT))
    if a.reference_path:
        spec=importlib.util.spec_from_file_location('tools.string_concat_reference',a.reference_path.resolve());reference=importlib.util.module_from_spec(spec);sys.modules[spec.name]=reference;spec.loader.exec_module(reference)
    else:import tools.string_concat_reference as reference
    output=a.output.resolve()
    if output.exists() or output.is_relative_to(ROOT):p.error('Output must be a new directory outside the candidate checkout')
    fixtures=reference.load_fixtures(a.fixtures or ROOT);output.mkdir(parents=True)
    for directory in ('sources','controls','agent','boundaries'):(output/directory).mkdir()
    run=None
    try:
        run=Acceptance(fixtures,output,reference);run.summary['selected_section']=a.section
        if a.section in ('all','sources'):run.run_sources()
        if a.section in ('all','agent'):run.run_agent()
        if a.section in ('all','boundaries'):
            from string_concat_boundary_checks import run_boundaries
            run_boundaries(run)
        run.summary['status']='failed' if run.summary['failures'] else 'produced_as_expected'
    except BaseException as error:
        if run is None:save(output/'initialization-failure.json',error_record(error));raise
        run.summary['status']='failed';run.summary['failures'].append({'scope':'driver','error':error_record(error)})
    finally:
        if run is not None:
            if run.service is not None:run.service.close()
            run.summary['finished_utc']=datetime.now(timezone.utc).isoformat();save(output/'summary.json',run.summary);save(output/'inventory.json',inventory(output))
    print(json.dumps({'status':run.summary['status'],'source_cases':len(run.summary['cases']),'failures':len(run.summary['failures']),'output':str(output)}));return 0 if run.summary['status']=='produced_as_expected' else 1

if __name__=='__main__':raise SystemExit(main())
