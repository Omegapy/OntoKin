"""Passive observations of actual C087 String calls and original expression flow."""
from __future__ import annotations
import hashlib
from unittest.mock import patch


def sha(raw):return hashlib.sha256(raw).hexdigest()

def location(node):
    if node is None:return None
    return {'source_id':getattr(node,'source_id',None),'start_byte':getattr(node,'start',0),'end_byte':getattr(node,'end',0)}

def error_record(error):
    record={'exception_type':type(error).__name__,'exception_identity':id(error),'message':str(error)}
    if hasattr(error,'diagnostic'):
        d=error.diagnostic;record.update(code=d.code,phase=d.phase,category=d.category,details=d.details,primary=location(d.node),element_id=d.element_id)
    return record

def value_kind(value):
    return {'returned_type':str(value.type),'returned_known':bool(value.known)}

class StringExecutionObserver:
    """Delegate every call exactly once; measurements cannot supply a result."""
    def __init__(self,ledger):
        self.ledger=ledger;self.helper_invocations=[];self.binary_invocations=[];self.helper_values=[];self.user_function_invocations=[]
        self.helper_stack=[];self.binary_stack=[];self.patches=[]

    def __enter__(self):
        import ontokin.string_concat as concat
        import ontokin.construction as construction
        from ontokin.execution_budget import SharedExecutionBudget
        original_helper=concat.concat_strings;original_tick=SharedExecutionBudget.tick;original_expression=construction.ConstructionCompiler.expression;original_invoke=construction.ConstructionCompiler.invoke

        def helper(left,right,node,ledger):
            if ledger is not self.ledger:return original_helper(left,right,node,ledger)
            index=len(self.helper_invocations)
            record={'index':index,'expression':location(node),'operations_before':ledger.operations,'reserved_bytes_before':getattr(ledger,'string_concat_bytes',0),'ticks':[]}
            self.helper_invocations.append(record);self.helper_stack.append(record);result=None
            try:
                result=original_helper(left,right,node,ledger)
                return result
            except BaseException as error:
                record['exception']=error_record(error);raise
            finally:
                record.update(operations_after=ledger.operations,reserved_bytes_after=getattr(ledger,'string_concat_bytes',0))
                # Measure original values only after the bounded operation has
                # finished/refused. No observer allocation precedes its guard.
                try:
                    record.update(left_utf8_bytes=len(left.encode('utf-8')),right_utf8_bytes=len(right.encode('utf-8')),
                                  result_utf8_bytes=None if result is None else len(result.encode('utf-8')),
                                  result_sha256=None if result is None else sha(result.encode('utf-8')))
                    self.helper_values.append({'index':index,'left':left,'right':right,'result':result})
                except BaseException as measurement_error:record['measurement_exception']=error_record(measurement_error)
                self.helper_stack.pop()

        def tick(ledger,node=None,amount=1):
            if ledger is not self.ledger or not str(ledger.stage).startswith('string_concat_'):
                return original_tick(ledger,node,amount)
            record={'stage':ledger.stage,'amount':amount,'expression':location(node),'operations_before':ledger.operations,'reserved_bytes_before':getattr(ledger,'string_concat_bytes',0)}
            if self.helper_stack:self.helper_stack[-1]['ticks'].append(record)
            try:return original_tick(ledger,node,amount)
            except BaseException as error:record['exception']=error_record(error);raise
            finally:record.update(operations_after=ledger.operations,reserved_bytes_after=getattr(ledger,'string_concat_bytes',0))

        def expression(compiler,node,context):
            parents=[]
            for parent in self.binary_stack:
                if parent['compiler'] is compiler:
                    for side in ('left','right'):
                        if node is getattr(parent['node'],side):
                            event={'side':side,'event':'start','source_location':location(node),'helper_invocations_completed':len(self.helper_values)}
                            parent['record']['operand_evaluations'].append(event);parents.append((parent,side))
            own=None
            if node.kind=='binary' and node.op=='+':
                try:profile=compiler.linked.modules[node.source_id].ast.profile
                except (AttributeError,KeyError):profile=None
                own={'index':len(self.binary_invocations),'expression':location(node),'declaring_profile':profile,'abstract':bool(context.abstract),'operand_evaluations':[],'operations_before':self.ledger.operations,'reserved_bytes_before':getattr(self.ledger,'string_concat_bytes',0)}
                self.binary_invocations.append(own);self.binary_stack.append({'compiler':compiler,'node':node,'record':own})
            try:
                result=original_expression(compiler,node,context)
                if own is not None:own.update(value_kind(result))
                for parent,side in parents:parent['record']['operand_evaluations'].append({'side':side,'event':'end','source_location':location(node),**value_kind(result),'helper_invocations_completed':len(self.helper_values)})
                return result
            except BaseException as error:
                if own is not None:own['exception']=error_record(error)
                for parent,side in parents:parent['record']['operand_evaluations'].append({'side':side,'event':'exception','source_location':location(node),'exception':error_record(error),'helper_invocations_completed':len(self.helper_values)})
                raise
            finally:
                if own is not None:
                    own.update(operations_after=self.ledger.operations,reserved_bytes_after=getattr(self.ledger,'string_concat_bytes',0));self.binary_stack.pop()

        def invoke(compiler,function,args,node,caller):
            record=None
            if not caller.abstract:
                ids=None
                if function.lexical_class is not None:
                    symbol=compiler._class_symbols.get(function.lexical_class)
                    if symbol is not None:ids=[*symbol.element_id,function.node.key]
                else:
                    module=compiler.linked.modules[function.node.source_id];symbol=module.symbols.get(function.node.name)
                    if symbol is not None:ids=list(symbol.element_id)
                record={'index':len(self.user_function_invocations),'definition_id':ids,'definition':location(function.node),'caller':location(node),'argument_kinds':[value_kind(v) for v in args],'operations_before':self.ledger.operations,'reserved_bytes_before':getattr(self.ledger,'string_concat_bytes',0)}
                self.user_function_invocations.append(record)
            try:
                result=original_invoke(compiler,function,args,node,caller)
                if record is not None:record.update(value_kind(result))
                return result
            except BaseException as error:
                if record is not None:record['exception']=error_record(error)
                raise
            finally:
                if record is not None:record.update(operations_after=self.ledger.operations,reserved_bytes_after=getattr(self.ledger,'string_concat_bytes',0))

        self.patches=[patch.object(concat,'concat_strings',helper),patch.object(SharedExecutionBudget,'tick',tick),patch.object(construction.ConstructionCompiler,'expression',expression),patch.object(construction.ConstructionCompiler,'invoke',invoke)]
        # Support either explicit module dispatch or a conventional imported
        # function alias while still calling the one original implementation.
        for name,value in list(vars(construction).items()):
            if value is original_helper:self.patches.append(patch.object(construction,name,helper))
        for item in self.patches:item.start()
        return self

    def __exit__(self,*exception):
        for item in reversed(self.patches):item.stop()
        return False

    def report(self,**fields):
        return {'schema_version':'ontokin.c087-string-execution-observation/0.1',**fields,
                'intervention':'Passive delegating actual helper, binary-expression and ledger-tick observers; no return/exception object, clock, counter, cap, taint or cache state is replaced. Operand/result byte measurements occur after original helper completion/refusal. Observer overhead consumes real time.',
                'helper_invocations':self.helper_invocations,'binary_invocations':self.binary_invocations,
                'user_function_invocations':self.user_function_invocations,
                'execution_budget':self.ledger.report(status='observed')}
