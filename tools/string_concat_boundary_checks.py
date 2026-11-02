"""Actual private-helper and staged-source guard observations for frozen C087."""
from __future__ import annotations
import json,time
from pathlib import Path
from string_concat_observer import StringExecutionObserver

def run_boundaries(run):
    from run_string_concat_acceptance import SourceContext,save,compressed,error_record
    from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
    import ontokin.string_concat as concat_module
    from ontokin.construction import ConstructionCompiler,ExecutionConstructionBudget,compile_construction
    from ontokin.linker import link_program
    from ontokin.validator import Context
    from ontokin.syntax import lex
    from ontokin.syntax02 import RESERVED_02,PathStep
    from ontokin.syntax19 import Parser19
    from ontokin.diagnostics import OntoKinError
    frozen=run.fixtures['runtime_boundaries'];root=run.fixture_root
    def parse_binary(case):
        source=run.load_files(root/case['file_manifest']);tokens=lex(source.entry.text,reserved=RESERVED_02,source_id='entry');parser=Parser19(tokens,'entry')
        parser.index=next(i for i,t in enumerate(tokens) if t.start==case['expression']['start_byte']);node=parser.expression()
        run.check(node.kind=='binary' and node.op=='+' and node.left.kind==node.right.kind=='string','Frozen direct literal operands')
        return source,node,node.left.value,node.right.value
    def remember(kind,name,record,error=None,*,helper_values=None):
        record={'kind':kind,'name':name,**record};path='boundaries/'+name+'.json'
        if helper_values is not None:
            payload_path='boundaries/'+name+'.concat-values.json.gz'
            record['helper_values_file']=payload_path
            record['helper_values_receipt']=compressed(run.output/payload_path,{'helper_values':helper_values})
        if error is not None:record.update(producer_status='failed',exception=error_record(error));run.summary['failures'].append({'scope':kind,'name':name,'error':str(error)})
        else:record['producer_status']='observed_as_expected'
        save(run.output/path,record);run.summary['boundaries'].append({'kind':kind,'name':name,'record':path,'producer_status':record['producer_status']});save(run.output/'summary.json',run.summary)
    for vector in frozen['direct_operation_boundaries']:
        case=run.fixtures['core_cases'][vector['source_case']];source,node,left,right=parse_binary(case)
        for cap in vector['caller_operation_caps']:
            name=vector['name']+'-operations-'+str(cap);record={'scope':vector['scope'],'source_case':case['name'],'program_revision':source.program_revision,'caller_caps':{'max_operations':cap},'host_policy':run.HostPolicy().ceilings};failure=None
            ledger=SharedExecutionBudget(policy=run.HostPolicy(),caller_caps=record['caller_caps']);observer=StringExecutionObserver(ledger);result=None;actual_error=None
            try:
                admit_entry_budget(source.entry,ledger,profile='string-concat-0.1');record['header_admission_operations']=ledger.operations;run.check(ledger.operations==vector['expected_header_admission_operations'],'Exact independent header cost')
                with observer:
                    try:result=concat_module.concat_strings(left,right,node,ledger)
                    except BaseException as error:actual_error=error;record['actual_exception']=error_record(error)
                # The imported helper alias is the real function; invoke the
                # observed module dispatch for traces, without double work.
                expected_success=cap>=14+vector['expected_charge']['total']
                run.check((actual_error is None)==expected_success,'Private helper cap boundary result')
                if actual_error is not None:run.check(isinstance(actual_error,OntoKinError) and actual_error.code=='OKL-E-RESOURCE' and actual_error.diagnostic.details.get('budget_reason')=='operation_budget_exhausted','Original actual operation-cap refusal')
                record['actual_result']=result;record['ledger']=ledger.report(status='valid' if actual_error is None else 'refused')
            except BaseException as error:failure=error
            finally:
                record['trace']=observer.report(program_revision=source.program_revision,case=case['name'],public_api='ontokin.string_concat.concat_strings',profile='string-concat-0.1',requested_level='private-helper')
                record['actual_operand_strings']={'left':left,'right':right,'result':result}
                remember('direct_operation_cap',name,record,failure,helper_values=observer.helper_values)
    base=run.fixtures['core_cases']['literal-prefix'];source,node,left,right=parse_binary(base)
    for mode,stages in [('cancellation',frozen['actual_cancellation_stages']),('deadline',frozen['actual_deadline_exhaustion']['stages'])]:
        for stage in stages:
            name=mode+'-'+stage;observed=[];failure=None;record={'scope':'Private actual helper guard on a fresh admitted real ledger','source_case':'literal-prefix','program_revision':source.program_revision,'stage':stage};ledger=None
            class OriginalCancellation(BaseException):pass
            original=OriginalCancellation('Frozen real String-stage callback interruption')
            def poll():
                if ledger is not None and ledger.stage==stage and not observed:
                    observed.append({'stage':ledger.stage,'operations':ledger.operations,'reserved_bytes':getattr(ledger,'string_concat_bytes',0),'elapsed_ms':ledger.elapsed_ms()})
                    if mode=='cancellation':raise original
                    # Natural time advances; neither the ledger clock nor its
                    # start time, charges, cap or decisions are replaced.
                    remaining=max(0.,1000.-ledger.elapsed_ms());time.sleep(remaining/1000.+.01)
            ledger=SharedExecutionBudget(policy=run.HostPolicy(),caller_caps={'max_elapsed_ms':1000} if mode=='deadline' else None,check=poll);observer=StringExecutionObserver(ledger);caught=None
            try:
                admit_entry_budget(source.entry,ledger,profile='string-concat-0.1')
                with observer:
                    try:concat_module.concat_strings(left,right,node,ledger)
                    except BaseException as error:caught=error;record['actual_exception']=error_record(error)
                run.check(observed and caught is not None,'Selected actual guard must refuse')
                if mode=='cancellation':
                    record['original_callback_exception_identity']=id(original);record['caught_exception_identity']=id(caught);record['ledger_callback_error_identity']=id(ledger.callback_error);run.check(caught is original and ledger.callback_error is original,'Original callback exception identity')
                else:run.check(isinstance(caught,OntoKinError) and caught.code=='OKL-E-RESOURCE' and caught.diagnostic.details.get('budget_reason')=='execution_deadline_exceeded','Original actual deadline refusal')
                run.check(getattr(ledger,'string_concat_bytes',0)==(len((left+right).encode()) if stage=='string_concat_publication' else 0),'Actual reservation phase and no refund')
            except BaseException as error:failure=error
            finally:record.update(observed_callbacks=observed,ledger=ledger.report(status='refused'),trace=observer.report(case='literal-prefix',program_revision=source.program_revision,public_api='ontokin.string_concat.concat_strings',profile='string-concat-0.1',requested_level='private-helper'));remember(mode,name,record,failure,helper_values=observer.helper_values)
    for index,spec in enumerate(frozen['current_authority_matrix']):
        case=run.fixtures['core_cases'][spec['case']];source=run.load_files(root/case['file_manifest']);record={'source_case':case['name'],'program_revision':source.program_revision,'host_policy':spec['host'],'caller_caps':spec['caller']};failure=None
        context=SourceContext(run.HostPolicy(**spec['host']),'string-concat-0.1',spec['caller']);observer=StringExecutionObserver(context.execution_budget)
        try:
            with observer:result=run.Runtime().validate_revision(source,level='constructed',check=context,budgets=spec['caller'])
            record['actual_result']=result
            if spec['outcome']=='valid':run.check(result['outcome']=='valid','Current high authority constructs actual aggregate request')
            else:run.check(result['outcome']!='valid' and any(d.get('details',{}).get('budget_reason')==spec['budget_reason'] for d in result.get('diagnostics',[])),'Exact actual current-authority refusal')
        except BaseException as error:failure=error
        finally:
            record.update(ledger=context.execution_budget.report(status='observed'),trace=observer.report(case=case['name'],program_revision=source.program_revision,public_api='StringConcatProgramRuntime.validate_revision',profile='string-concat-0.1',requested_level='constructed'));remember('current_authority','authority-'+str(index+1),record,failure,helper_values=observer.helper_values)
    failure=None;record={'source_case':'literal-prefix','program_revision':source.program_revision}
    try:
        source=run.load_files(root/base['file_manifest']);record['program_revision']=source.program_revision
        try:compile_construction(source,level='constructed')
        except OntoKinError as error:
            record['actual_exception']=error_record(error);run.check(error.code=='OKL-E-RESOURCE' and error.diagnostic.details=={'budget_reason':'execution_context_required'},'Exact original missing-context refusal')
        else:raise AssertionError('Unadmitted source must refuse')
    except BaseException as error:failure=error
    remember('missing_context','missing-execution-context',record,failure)
    for spec in frozen['staged_taint_guards']:
        for role in ('source','control'):
            name=spec['name']+'-'+role;source=run.load_files(root/spec[role]['file_manifest']);profile='string-concat-0.1' if role=='source' else 'keyed-rekey-0.1';record={'scope':spec['evidence_scope'],'role':role,'program_revision':source.program_revision,'file_manifest':spec[role]['file_manifest']};failure=None;ctx=SourceContext(run.HostPolicy(),profile);ctx.admit(source);observer=StringExecutionObserver(ctx.execution_budget)
            try:
                with observer:
                    budget=ExecutionConstructionBudget(execution_budget=ctx.execution_budget);linked=link_program(source,check=budget.tick);compiler=ConstructionCompiler(linked,'constructed',budget);compiler.bind();compiler.check_static_types();context=Context(scene=True);prefix=(compiler.model.module_key,compiler.model.scene_key)
                    for n in compiler.program.scene.members:
                        if n.kind=='object':compiler._register_tree(n,n.name,None,prefix+(n.key,),context,[],steps=(PathStep('member',n.name,n.start,n.end),),depth=0)
                    compiler._ensure_collection('shape.family.leaves');value=compiler.field('shape','copied',compiler.program);record['actual_warmed_string']=value.value;record['actual_generated_dependencies']=sorted(compiler.generated_dependencies.get(('shape','copied'),set()));record['before_guard']={'operations':ctx.execution_budget.operations,'reserved_bytes':getattr(ctx.execution_budget,'string_concat_bytes',0),'helper_invocations':len(observer.helper_invocations)}
                    try:compiler._ensure_collection('shape.bad')
                    except OntoKinError as error:record['actual_exception']=error_record(error);run.check(error.code=='OKL-E-DEPENDENCY-CYCLE','Actual staged guard refuses')
                    else:raise AssertionError('Guarded cached generated dependency cannot construct a shape')
                    record['after_guard']={'operations':ctx.execution_budget.operations,'reserved_bytes':getattr(ctx.execution_budget,'string_concat_bytes',0),'helper_invocations':len(observer.helper_invocations)};record['established_binding_identity_preserved']=compiler.memo[('shape','copied')] is value;record['shape_stack_cleaned']=not compiler._shape_stack
                run.check(record['actual_warmed_string']==spec['expected_copied_string'] and record['actual_generated_dependencies']==spec['required_taint_paths'],'Actual warmed ordinary value and inherited collection dependency')
                run.check(record['established_binding_identity_preserved'] and record['shape_stack_cleaned'],'Ordinary actual cache and cleanup')
            except BaseException as error:failure=error
            finally:
                record['trace']=observer.report(case=spec['name'],program_revision=source.program_revision,public_api='ordinary compiler staged guard APIs',profile=profile,requested_level='staged-internal-guard');record['helper_values']=observer.helper_values;remember('staged_guard',name,record,failure,helper_values=observer.helper_values)
