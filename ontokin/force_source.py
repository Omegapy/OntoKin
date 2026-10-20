"""Typed source-force operands and immutable lowering, with no evaluation."""
from __future__ import annotations
from fractions import Fraction
from .diagnostics import OntoKinError
from .model import ForcePayload
from .validator import Context, fail
from .values import TIME, Type, quantity_type

PROFILE = 'force-0.1'
FORCE_DIMENSION = (1, 1, -2, 0)


def force_values(compiler, event, context):
    if compiler.linked.modules[event.source_id].ast.profile not in {PROFILE, 'planar-reach-0.1'}:
        raise OntoKinError('OKL-E-CAPABILITY-UNSUPPORTED',
                           'Source force intervals require force-0.1.', event,
                           phase='support', category='unsupported', rule_ids=['FOR-001'])
    compiler.key(event, event.key)
    target = compiler.expect(compiler.path_value(event.path, context, event),
                             Type('Ref', name='Object'), event)
    def operand(node, expected):
        try:
            return compiler.expect(compiler.expression(node, context), expected, node)
        except OntoKinError as error:
            # The new force signature defines dimension mismatches as operand
            # type errors, including a heterogeneous vector expression. Never
            # rewrite an interruption injected by the budget callback.
            if error is not compiler.budget.callback_error and error.code == 'OKL-E-UNIT':
                error.diagnostic.code = 'OKL-E-TYPE'
                error.diagnostic.rule_ids = [*(error.diagnostic.rule_ids or []), 'FOR-001']
            raise
    vector = operand(event.vector, Type('Vector3', element=quantity_type(FORCE_DIMENSION)))
    duration = operand(event.duration, quantity_type(TIME))
    if vector.frame is not None and vector.frame != 'world':
        raise OntoKinError('OKL-E-FRAME', 'A force vector must use world axes.',
                           event.vector, phase='type', rule_ids=['FOR-001'],
                           details={'expected_frame':'world', 'actual_frame':vector.frame})
    if duration.known and duration.value <= 0:
        fail('OKL-E-EVENT-ORDER', 'A force duration must be a strictly positive Time.', event.duration)
    return target, vector, duration


def lower_force(compiler, event, sequence_index):
    target, vector, duration = force_values(compiler, event, Context(scene=True))
    source = compiler.source_for(event)
    return target.value, ForcePayload(
        event.key, tuple(v.value for v in vector.value), Fraction.from_float(duration.value),
        sequence_index, {'source_id':event.source_id, 'source_revision':source.revision,
                         'start_byte':event.start, 'end_byte':event.end})
