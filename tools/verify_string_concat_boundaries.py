#!/usr/bin/env python3
"""Independently audit all 104 frozen C087 real-ledger boundary observations.

Imports no OntoKin or producer module. Expectations come from the exact frozen
contract, original source bytes and independent scalar arithmetic. Producer
success flags are deliberately never acceptance inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.string_concat_reference import (
    PROFILE, FREEZE_SHA256, require, sha, canonical, loads, ordinary_path,
    load_fixtures, input_lineage, file_payload, case_payload, source_units,
    bundle_identity, check_location, check_all_locations, read_private_json,
    _source_tokens,
)
from tools.verify_string_concat import expected_ticks, location_key


DEFAULTS = {'max_operations': 100000, 'max_elapsed_ms': 30000}
STAGES = ('string_concat_admission', 'string_concat_scan',
          'string_concat_allocation', 'string_concat_publication')


def fingerprint(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def read_json(root, name):
    return loads(ordinary_path(root, name).read_bytes())


def matching_ledger(first, second):
    for key in ('schema_version', 'defaults', 'policy_id', 'host_ceilings',
                'source_request', 'caller_caps', 'effective', 'consumed_operations',
                'stage', 'budget_reason'):
        require(first.get(key) == second.get(key), 'Two observations disagree about the original ledger: ' + key)


def policy(ledger, source, host, caller, *, admitted=True):
    require(ledger['schema_version'] == 'ontokin.execution-budget/0.1' and
            ledger['defaults'] == DEFAULTS and ledger['host_ceilings'] == host and
            ledger['source_request'] == source and ledger['caller_caps'] == caller,
            'Actual original source/host/caller authority differs')
    require(ledger['policy_id'] == 'sha256:' + sha(canonical(host)), 'Host authority identity differs')
    effective = {**source, **caller} if admitted else None
    require(ledger['effective'] == effective, 'Actual resolved limits differ from current source/caller requests')
    if admitted:
        require(all(effective[key] <= source[key] and effective[key] <= host[key] for key in DEFAULTS),
                'Admission enlarged source or host authority')
    require(type(ledger['consumed_operations']) is int and ledger['consumed_operations'] >= 0,
            'Missing actual integer work counter')
    require(type(ledger['elapsed_ms']) in (int, float) and math.isfinite(ledger['elapsed_ms']) and
            ledger['elapsed_ms'] >= 0, 'Actual finite elapsed time is absent')


def private_values(record, results, evidence):
    path = ordinary_path(results, record['helper_values_file'])
    receipt = record['helper_values_receipt']
    raw = path.read_bytes()
    require(len(raw) == receipt['gzip_bytes'] and sha(raw) == receipt['gzip_sha256'],
            'Complete retained operand gzip differs')
    value = read_private_json(path)
    plain = canonical(value)
    require(len(plain) == receipt['raw_bytes'] and sha(plain) == receipt['raw_sha256'] and
            set(value) == {'helper_values'}, 'Complete retained operand bytes differ')
    rows = value['helper_values']
    require(isinstance(rows, list) and [row['index'] for row in rows] == list(range(len(rows))),
            'Actual operand/result inventory is incomplete or reordered')
    if 'helper_values' in record:
        require(record['helper_values'] == rows, 'Inline and retained operands differ')
    evidence.append(fingerprint(path))
    return rows


def trace_header(record, case_name, revision, profile, api, level, units):
    trace = record['trace']
    require(trace['schema_version'] == 'ontokin.c087-string-execution-observation/0.1' and
            trace['case'] == case_name and trace['program_revision'] == revision and
            trace['profile'] == profile and trace['public_api'] == api and
            trace['requested_level'] == level, 'Boundary observation names another source or entrypoint')
    require([call['index'] for call in trace['helper_invocations']] == list(range(len(trace['helper_invocations']))),
            'Actual helper observation order is incomplete')
    check_all_locations(trace, units)
    if 'ledger' in record:
        matching_ledger(record['ledger'], trace['execution_budget'])
    return trace


def binary_observations(trace, units):
    calls = trace['helper_invocations']
    binaries = trace['binary_invocations']
    require([row['index'] for row in binaries] == list(range(len(binaries))), 'Binary trace order differs')
    abstract = 0
    allowed = ([('left', 'start'), ('left', 'end'), ('right', 'start'), ('right', 'end')],
               [('left', 'start'), ('left', 'exception')],
               [('left', 'start'), ('left', 'end'), ('right', 'start'), ('right', 'exception')])
    for row in binaries:
        check_location(row['expression'], units)
        require(row['operations_after'] >= row['operations_before'], 'Binary work counter decreased')
        events = row['operand_evaluations']
        require([(e['side'], e['event']) for e in events] in allowed,
                'A binary operand was omitted, duplicated or reordered')
        for event in events:
            check_location(event['source_location'], units)
        if row['abstract']:
            abstract += 1
            require(row['reserved_bytes_before'] == row['reserved_bytes_after'] and
                    len({e['helper_invocations_completed'] for e in events}) <= 1,
                    'Abstract evaluation allocated a String result')
            require(not any(row['operations_before'] <= call['operations_before'] <
                            call['operations_after'] <= row['operations_after'] for call in calls),
                    'Abstract evaluation entered the dynamic bounded helper')
            if row.get('returned_type') == 'String' and row['declaring_profile'] == PROFILE:
                require(row.get('returned_known') is False, 'Abstract String addition produced a known payload')
    return abstract


def literal_operands(case, units):
    location = {'source_id': 'entry', 'start_byte': case['expression']['start_byte'],
                'end_byte': case['expression']['end_byte']}
    text = check_location(location, units)
    tokens = _source_tokens(text)
    require(len(tokens) == 3 and tokens[1][0] == b'+' and
            tokens[0][0].startswith(b'"') and tokens[2][0].startswith(b'"'),
            'Frozen direct helper source is not the prescribed two-literal expression')
    return json.loads(tokens[0][0]), json.loads(tokens[2][0]), location


def resource_error(error, *, reason, stage, budget, limit, consumed, location):
    require(error['exception_type'] == 'OntoKinError' and error['code'] == 'OKL-E-RESOURCE' and
            error['phase'] == 'support' and error['category'] == 'resource_limit',
            'Actual guard exception changed type/code/phase/category')
    require(error['message'] == ('Execution exceeded max_operations.' if budget == 'max_operations'
                                 else 'Execution exceeded max_elapsed_ms.'), 'Actual guard message changed')
    require(error['details'] == {'budget_reason': reason, 'stage': stage,
            'budget': budget, 'limit': limit, 'consumed': consumed}, 'Actual guard details differ')
    require(location_key(error['primary']) == location_key(location), 'Guard primary moved from the original expression')


def helper_call(call, values, units, reserved, *, cap=None, guard=None, guard_stage=None,
                wanted_operands=None, wanted_location=None):
    """Derive the permitted tick prefix and reservation independently."""
    require(values['index'] == call['index'] and set(values) == {'index', 'left', 'right', 'result'},
            'A helper call lacks its exact retained operands')
    left, right, result = values['left'], values['right'], values['result']
    require(type(left) is str and type(right) is str and 'measurement_exception' not in call,
            'Actual String operands are absent or unmeasured')
    if wanted_operands is not None:
        require((left, right) == wanted_operands, 'Retained operand Strings differ from original authored values')
    check_location(call['expression'], units)
    if wanted_location is not None:
        require(location_key(call['expression']) == location_key(wanted_location),
                'The helper ran another original expression')
    schedule, increment, byte_refusal = expected_ticks(left, right, reserved)
    require(byte_refusal is None, 'This frozen boundary role unexpectedly exceeds a fixed byte cap')
    require(call['reserved_bytes_before'] == reserved, 'Cumulative reservation was reset or preloaded')
    start = call['operations_before']
    require(type(start) is int and start >= 0, 'Missing original helper starting work')
    failed = None
    total = start
    for index, (stage, amount) in enumerate(schedule):
        total += amount
        if (guard is not None and stage == guard_stage) or (cap is not None and total > cap):
            failed = index
            break
    prefix = schedule if failed is None else schedule[:failed + 1]
    ticks = call['ticks']
    require([(r['stage'], r['amount']) for r in ticks] == prefix,
            'Actual scan/guard schedule differs from the independently derived stopping prefix')
    previous = start
    for index, tick in enumerate(ticks):
        stage, amount = prefix[index]
        reserved_here = reserved + (increment if stage == 'string_concat_publication' else 0)
        is_failure = failed is not None and index == failed
        charged = 0 if is_failure and guard == 'cancellation' else amount
        require(tick['operations_before'] == previous and tick['operations_after'] == previous + charged,
                'Actual original-ledger debit differs at a String checkpoint')
        require(tick['reserved_bytes_before'] == tick['reserved_bytes_after'] == reserved_here,
                'Allocation reservation occurred at the wrong stage or was refunded')
        require(location_key(tick['expression']) == location_key(call['expression']), 'A tick changed source span')
        require(bool(tick.get('exception')) == is_failure, 'A successful or failing tick was omitted/invented')
        previous += charged
    after_reserved = reserved + (increment if any(s == 'string_concat_publication' for s, _ in prefix) else 0)
    require(call['operations_after'] == previous and call['reserved_bytes_after'] == after_reserved,
            'Helper completion hides extra work or alters reserved bytes')
    require(call['left_utf8_bytes'] == len(left.encode()) and call['right_utf8_bytes'] == len(right.encode()),
            'Claimed operand byte sizes differ from retained scalar Strings')
    error = call.get('exception')
    if failed is None:
        require(error is None and result == left + right and
                call['result_utf8_bytes'] == increment and call['result_sha256'] == sha(result.encode()),
                'Completed String result differs from independently concatenated actual operands')
    else:
        require(result is None and call['result_utf8_bytes'] is None and call['result_sha256'] is None and
                error == ticks[-1]['exception'], 'A refused helper published a value or translated its original exception')
        if guard == 'cancellation':
            require(error['exception_type'] == 'OriginalCancellation' and
                    error['message'] == 'Frozen real String-stage callback interruption' and
                    set(error) == {'exception_type', 'exception_identity', 'message'},
                    'Original callback cancellation acquired a source diagnostic or changed identity')
        elif guard == 'deadline':
            elapsed = error['details']['consumed']
            require(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed > 1000,
                    'Deadline consumption is not actual finite elapsed time beyond its cap')
            resource_error(error, reason='execution_deadline_exceeded', stage=prefix[-1][0],
                           budget='max_elapsed_ms', limit=1000, consumed=elapsed, location=call['expression'])
        else:
            resource_error(error, reason='operation_budget_exhausted', stage=prefix[-1][0],
                           budget='max_operations', limit=cap, consumed=previous, location=call['expression'])
    return {'successful': failed is None, 'tick_count': len(ticks), 'added_operations': previous - start,
            'reserved_after': after_reserved, 'failure_stage': None if failed is None else prefix[-1][0],
            'operations_after': previous, 'result_bytes': increment, 'exception': error}


def compare_outer_error(record, observed):
    outer = record.get('actual_exception')
    if observed is None:
        require(outer is None, 'Successful private call acquired an outer exception')
        return
    require(outer and outer['exception'] == observed['exception_type'] and outer['message'] == observed['message'],
            'Caller observed a different original exception')
    if 'code' in observed:
        diagnostic = outer['diagnostic']
        for key in ('code', 'phase', 'category', 'message', 'details'):
            require(diagnostic[key] == observed[key], 'Caller translated original guard field: ' + key)
        require(location_key(diagnostic['primary']) == location_key(observed['primary']) and
                diagnostic['related'] == [], 'Caller changed the original guard location')


def direct(record, vector, case, fixtures, values):
    units = source_units(case_payload(fixtures, case))
    left, right, location = literal_operands(case, units)
    cap = record['caller_caps']['max_operations']
    require(record['caller_caps'] == {'max_operations': cap} and cap in vector['caller_operation_caps'] and
            record['program_revision'] == case['program_revision'] and record['source_case'] == case['name'] and
            record['host_policy'] == DEFAULTS and record['scope'] == vector['scope'], 'Direct boundary role changed')
    require(record['header_admission_operations'] == vector['expected_header_admission_operations'] == 14,
            'A direct cap test did not really pay the frozen header work')
    trace = trace_header(record, case['name'], case['program_revision'], PROFILE,
                         'ontokin.string_concat.concat_strings', 'private-helper', units)
    require(len(trace['helper_invocations']) == len(values) == 1 and
            not trace['binary_invocations'] and not trace['user_function_invocations'], 'Direct helper execution was omitted or duplicated')
    call = trace['helper_invocations'][0]
    require(call['operations_before'] == 14, 'Direct helper did not retain its source-admission ledger')
    full, increment, refusal = expected_ticks(left, right, 0)
    frozen = [(step['stage'], step['amount_per_tick']) for step in vector['schedule'] for _ in range(step['ticks'])]
    require(full == frozen and refusal is None and sum(amount for _, amount in full) == vector['expected_charge']['total'] and
            increment == vector['expected_charge']['result_utf8_bytes'], 'Frozen charge arithmetic does not match original scalar literals')
    observed = helper_call(call, values[0], units, 0, cap=cap, wanted_operands=(left, right), wanted_location=location)
    policy(record['ledger'], DEFAULTS, DEFAULTS, {'max_operations': cap})
    require(record['ledger']['consumed_operations'] == observed['operations_after'] and
            record['ledger']['stage'] == 'execution', 'Direct helper changed the original ledger or failed to restore its stage')
    require(record['actual_operand_strings'] == {key: values[0][key] for key in ('left', 'right', 'result')} and
            record['actual_result'] == values[0]['result'], 'Outer private result differs from actual retained helper values')
    compare_outer_error(record, observed['exception'])
    return {key: value for key, value in observed.items() if key != 'exception'}


def interrupted(record, mode, stage, fixtures, values):
    case = fixtures['core_cases']['literal-prefix']
    units = source_units(case_payload(fixtures, case))
    left, right, location = literal_operands(case, units)
    require(record['stage'] == stage and record['program_revision'] == case['program_revision'] and
            record['source_case'] == case['name'], 'Selected interruption role differs')
    trace = trace_header(record, case['name'], case['program_revision'], PROFILE,
                         'ontokin.string_concat.concat_strings', 'private-helper', units)
    require(len(trace['helper_invocations']) == len(values) == 1 and not trace['binary_invocations'] and
            not trace['user_function_invocations'], 'Interruption skipped or duplicated real helper work')
    call = trace['helper_invocations'][0]
    require(call['operations_before'] == 14, 'Interruption lacks real original header admission')
    observed = helper_call(call, values[0], units, 0, guard=mode, guard_stage=stage,
                           wanted_operands=(left, right), wanted_location=location)
    require(not observed['successful'] and observed['failure_stage'] == stage, 'Interruption occurred at another stage')
    caller = {'max_elapsed_ms': 1000} if mode == 'deadline' else {}
    policy(record['ledger'], DEFAULTS, DEFAULTS, caller)
    require(record['ledger']['stage'] == 'execution' and
            record['ledger']['consumed_operations'] == observed['operations_after'], 'Interrupted helper failed to restore its original stage/counter')
    callbacks = record['observed_callbacks']
    final = call['ticks'][-1]
    require(len(callbacks) == 1 and callbacks[0]['stage'] == stage and
            callbacks[0]['operations'] == final['operations_before'] and
            callbacks[0]['reserved_bytes'] == observed['reserved_after'], 'Callback did not observe the selected original precharge state')
    require(math.isfinite(callbacks[0]['elapsed_ms']) and 0 <= callbacks[0]['elapsed_ms'] <= record['ledger']['elapsed_ms'],
            'Observed elapsed time reversed or became nonfinite')
    if mode == 'cancellation':
        identity = observed['exception']['exception_identity']
        require(type(identity) is int and identity > 0 and all(record[key] == identity for key in
                ('original_callback_exception_identity', 'caught_exception_identity', 'ledger_callback_error_identity')),
                'Callback exception identity was replaced at a publication boundary')
        require(record['ledger']['budget_reason'] is None, 'Callback cancellation became an authority failure')
    else:
        require(record['ledger']['budget_reason'] == 'execution_deadline_exceeded' and
                record['ledger']['elapsed_ms'] >= observed['exception']['details']['consumed'] > 1000,
                'Actual deadline refusal is not retained on the same ledger')
    compare_outer_error(record, observed['exception'])
    return {key: value for key, value in observed.items() if key != 'exception'}


def authored_half(units):
    tokens = _source_tokens(units['entry']['source'].encode())
    positions = [i for i, token in enumerate(tokens[:-1]) if token[0] == b'param' and tokens[i + 1][0] == b'half']
    require(len(positions) == 1, 'Frozen aggregate source lacks exactly one half parameter')
    index = positions[0]
    require([tokens[index + j][0] for j in range(8)] ==
            [b'param', b'half', b'@', b'"half"', b':', b'String', b'=', tokens[index + 7][0]] and
            tokens[index + 7][0].startswith(b'"'), 'Frozen half parameter declaration changed')
    return json.loads(tokens[index + 7][0])


def authority(record, spec, fixtures, values):
    case = fixtures['core_cases'][spec['case']]
    units = source_units(case_payload(fixtures, case))
    require(record['source_case'] == case['name'] and record['program_revision'] == case['program_revision'] and
            record['host_policy'] == spec['host'] and record['caller_caps'] == spec['caller'],
            'Current-authority role changed the frozen requested authority')
    trace = trace_header(record, case['name'], case['program_revision'], PROFILE,
                         'StringConcatProgramRuntime.validate_revision', 'constructed', units)
    ledger = record['ledger']
    admitted = spec.get('budget_reason') not in ('request_cap_exceeds_source', 'host_ceiling_exceeded')
    policy(ledger, spec['source'], spec['host'], spec['caller'], admitted=admitted)
    result = record['actual_result']
    require(result['program_revision'] == case['program_revision'] and result['source_manifest'] == case['canonical_manifest'] and
            result['requested_level'] == 'constructed', 'Actual source result lost its exact source identity or requested level')
    calls = trace['helper_invocations']
    require(len(calls) == len(values), 'Current authority lacks complete actual operands')
    check_all_locations(result, units)
    if not admitted:
        require(not calls and not trace['binary_invocations'] and not trace['user_function_invocations'] and
                ledger['stage'] == 'header_admission' and result['outcome'] == 'resource_limit',
                'Unadmitted authority executed source or String work')
        require(len(result['diagnostics']) == 1, 'Header refusal has another diagnostic count')
        d = result['diagnostics'][0]
        if spec['budget_reason'] == 'request_cap_exceeds_source':
            details = {'budget_reason': 'request_cap_exceeds_source', 'stage': 'header_admission',
                       'budget': 'max_operations', 'source_request': 100000, 'caller_cap': 100001}
            message = 'A caller cap cannot enlarge the source request.'
            require(ledger['consumed_operations'] == 14, 'Caller enlargement did not reach original header decision')
        else:
            details = {'budget_reason': 'host_ceiling_exceeded', 'stage': 'header_admission',
                       'budget': 'max_operations', 'requested': 400000, 'ceiling': 100000}
            message = 'The execution request exceeds the host ceiling.'
            require(ledger['consumed_operations'] > 0, 'Higher source request bypassed real header work')
        require(d['code'] == 'OKL-E-RESOURCE' and d['category'] == 'resource_limit' and d['phase'] == 'support' and
                d['message'] == message and d['details'] == details and d['primary'] is None and
                d['related'] == [] and d['rule_ids'] == ['LANG-009'] and ledger['budget_reason'] == spec['budget_reason'],
                'Actual current-authority header refusal differs')
        return {'successful_concatenations': 0, 'reserved_after': 0, 'authority_refusal': spec['budget_reason']}
    half = authored_half(units)
    expected_result = ordinary_path(fixtures['root'], case['expected']['literal_file']).read_bytes().decode()
    require(half + half == expected_result, 'Frozen aggregate literal is not twice its authored half')
    plus = [row['expression'] for row in case['source_operations'] if row['kind'] == 'binary' and row['operator'] == '+']
    require(len(plus) == 1, 'Aggregate fixture has another dynamic addition route')
    reserved, previous, successes, added, failed = 0, 0, 0, 0, None
    cap = ledger['effective']['max_operations']
    for index, (call, operands) in enumerate(zip(calls, values)):
        require(call['operations_before'] >= previous and failed is None,
                'Shared source ledger reset or continued after its first failure')
        observed = helper_call(call, operands, units, reserved, cap=cap,
            wanted_operands=(half, half), wanted_location=plus[0])
        reserved, previous = observed['reserved_after'], observed['operations_after']
        added += observed['added_operations']
        if observed['successful']:
            successes += 1
            require(operands['result'] == expected_result, 'Aggregate result differs from the prewritten complete literal')
        else:
            require(index == len(calls) - 1, 'A refused aggregate helper was followed by more calls')
            failed = observed['exception']
    abstract = binary_observations(trace, units)
    require(abstract > 0 and ledger['consumed_operations'] >= previous, 'Actual source checking or ledger continuation disappeared')
    if spec['outcome'] == 'valid':
        expected = case['aggregate_expectation']
        require(result['outcome'] == 'valid' and result['achieved_level'] == 'constructed' and failed is None and
                len(calls) == expected['attempted_concatenations'] == successes == expected['successful_concatenations'] and
                reserved == spec['computed_bytes'] == expected['reserved_result_utf8_bytes'] == 4194304 and
                ledger['consumed_operations'] <= cap, 'Current high authority did not actually compute the complete frozen aggregate')
    else:
        require(failed is not None and result['outcome'] == 'resource_limit' and len(result['diagnostics']) == 1 and
                ledger['consumed_operations'] == previous > cap and ledger['budget_reason'] == 'operation_budget_exhausted' and
                result['diagnostics'][0]['details'] == failed['details'] and
                location_key(result['diagnostics'][0]['primary']) == location_key(plus[0]),
                'Lower caller cap did not fail at the first actual cumulative String debit')
        require(0 < successes < case['aggregate_expectation']['successful_concatenations'] and
                reserved == successes * len(expected_result.encode()), 'Lower cap lacks genuine preceding reservations')
    return {'successful_concatenations': successes, 'attempted_concatenations': len(calls),
            'reserved_after': reserved, 'added_string_operations': added,
            'abstract_binary_observations': abstract, 'first_failure': None if failed is None else failed['details']}


def missing_context(record, spec, fixtures):
    case = fixtures['core_cases'][spec['source_case']]
    units = source_units(case_payload(fixtures, case))
    require(record['program_revision'] == case['program_revision'] and record['source_case'] == case['name'],
            'Missing-context role changed source')
    d = record['actual_exception']['diagnostic']
    for key in ('code', 'phase', 'category', 'message', 'details'):
        require(d[key] == spec[key], 'Unadmitted compile changed inherited diagnostic field: ' + key)
    raw = units['entry']['source'].encode()
    tokens = _source_tokens(raw)
    # Parser02's complete program ends at the EOF token, including trailing
    # source whitespace, rather than at the last closing-brace token.
    require(d['primary'] == {'source_id': 'entry', 'start_byte': tokens[0][1],
            'end_byte': len(raw), 'element_id': None} and d['related'] == [],
            'Unadmitted compile primary is not the complete original entry AST')
    require('trace' not in record and 'actual_result' not in record, 'Unadmitted compile exposed a completed result')
    return {'code': d['code'], 'details': d['details'], 'primary': d['primary']}


def staged_guard(record, spec, role, fixtures, values):
    source = spec[role]
    manifest_path = ordinary_path(fixtures['root'], source['file_manifest'])
    payload = file_payload(manifest_path.parent, manifest_path.name)
    require(bundle_identity(payload) == (source['program_revision'], source['canonical_manifest']),
            'Staged guard source no longer has its exact frozen identity')
    units = source_units(payload)
    profile = PROFILE if role == 'source' else 'keyed-rekey-0.1'
    require(record['scope'] == spec['evidence_scope'] and record['role'] == role and
            record['file_manifest'] == source['file_manifest'] and record['program_revision'] == source['program_revision'],
            'Staged internal evidence was relabeled or changed source')
    trace = trace_header(record, spec['name'], source['program_revision'], profile,
                         'ordinary compiler staged guard APIs', 'staged-internal-guard', units)
    policy(trace['execution_budget'], DEFAULTS, spec['host_policy'], {})
    wanted_calls = spec['expected_real_concat_calls_before_guard'] if role == 'source' else 0
    calls = trace['helper_invocations']
    require(len(calls) == len(values) == wanted_calls, 'Staged value copied or skipped the required real concatenation')
    reserved, added, previous = 0, 0, 0
    for call, operands in zip(calls, values):
        require(call['operations_before'] >= previous, 'Staged original ledger went backwards')
        observed = helper_call(call, operands, units, reserved)
        require(observed['successful'] and operands['result'] == spec['expected_copied_string'],
                'Staged warmed value differs from the frozen ordinary String')
        reserved, previous = observed['reserved_after'], observed['operations_after']
        added += observed['added_operations']
    if role == 'source':
        require(added == spec['expected_added_concat_operations'] and
                reserved == spec['expected_reserved_utf8_bytes_before_guard'] == spec['expected_reserved_utf8_bytes_after_refusal'],
                'Staged concat did not really pay and retain its required reservation')
    before, after = record['before_guard'], record['after_guard']
    require(before['reserved_bytes'] == after['reserved_bytes'] == reserved and
            before['helper_invocations'] == after['helper_invocations'] == wanted_calls and
            before['operations'] >= previous and after['operations'] > before['operations'],
            'Inherited cached read refunded work, repeated concatenation or skipped the guard')
    require(record['actual_warmed_string'] == spec['expected_copied_string'] and
            record['actual_generated_dependencies'] == spec['required_taint_paths'] and
            record['established_binding_identity_preserved'] is True and record['shape_stack_cleaned'] is True,
            'Real staged binding identity, generated dependency or cleanup differs')
    d = record['actual_exception']['diagnostic']
    guard = spec['guard_contract']
    for key in ('code', 'phase', 'category', 'message', 'repair', 'related'):
        require(d[key] == guard[key], 'Inherited staged guard changed diagnostic field: ' + key)
    # Raw internal Diagnostic stores null until public serialization applies
    # LANG-009 for DEPENDENCY-CYCLE. This is not a public schema projection.
    require((d['rule_ids'] if d['rule_ids'] is not None else ['LANG-009']) == guard['rule_ids'],
            'Inherited effective staged guard rule changed')
    details = {**guard['details_fixed'], 'generated_dependency': spec['required_taint_paths'][0]}
    require(d['details'] == details and d['details']['generated_dependency'] in guard['generated_dependency_must_be_one_of'],
            'Staged guard lost exact shape owner or generated collection dependency')
    primary = source['guard_primary']
    require(d['primary'] == {key: primary[key] for key in ('source_id', 'start_byte', 'end_byte', 'element_id')},
            'Staged guard moved from the frozen original source read')
    check_location(primary, units)
    abstract = binary_observations(trace, units)
    require(trace['execution_budget']['consumed_operations'] == after['operations'], 'Staged trace ended on another ledger')
    return {'successful_concatenations': wanted_calls, 'reserved_after': reserved,
            'added_string_operations': added, 'abstract_binary_observations': abstract,
            'guard_code': d['code'], 'guard_primary': d['primary']}


def audit(results, fixtures, candidate, archive):
    summary = read_json(results, 'summary.json')
    require(all(summary.get(key) == value for key, value in input_lineage(fixtures).items()),
            'Boundary producer names another immutable input lineage')
    git = summary['git']
    require(git['status'] == '' and subprocess.check_output(['git', 'rev-parse', git['commit'] + '^{tree}'],
            cwd=candidate, text=True).strip() == git['tree'], 'Boundary execution has no exact native implementation identity')
    evidence = [fingerprint(results / 'summary.json')]
    inventory = read_json(results, 'inventory.json')
    names = set()
    for entry in inventory:
        path = ordinary_path(results, entry['path']); raw = path.read_bytes()
        require(entry['path'] not in names and len(raw) == entry['bytes'] and sha(raw) == entry['sha256'],
                'Retained boundary evidence inventory differs: ' + entry['path'])
        names.add(entry['path'])
    actual_names = {p.relative_to(results).as_posix() for p in results.rglob('*') if p.is_file()}
    require(actual_names == names | {'inventory.json'}, 'Boundary evidence has missing or undeclared files')
    evidence.append(fingerprint(results / 'inventory.json'))
    implementation = read_json(results, 'implementation-inventory.json')
    for entry in implementation:
        require(sha(ordinary_path(candidate, entry['path']).read_bytes()) == entry['sha256'],
                'Candidate production bytes differ from observed execution: ' + entry['path'])
    archive_manifest = read_json(archive, 'MANIFEST.json')
    archived = {}
    for entry in archive_manifest:
        raw = ordinary_path(archive, entry['path']).read_bytes()
        require(sha(raw) == entry['sha256'] and len(raw) == entry['bytes'], 'Archived observer/probe changed')
        archived[entry['path']] = entry['sha256']
    require({r['path']: r['sha256'] for r in read_json(results, 'producer-inventory.json')} == archived,
            'Actual boundary observer/probe identity differs from retained reviewed code')
    evidence.extend(fingerprint(results / name) for name in ('implementation-inventory.json', 'producer-inventory.json'))
    evidence.append(fingerprint(archive / 'MANIFEST.json'))
    expected = {}
    frozen = fixtures['runtime_boundaries']
    for vector in frozen['direct_operation_boundaries']:
        for cap in vector['caller_operation_caps']:
            expected[vector['name'] + '-operations-' + str(cap)] = ('direct_operation_cap', vector, cap)
    for mode, stages in (('cancellation', frozen['actual_cancellation_stages']),
                         ('deadline', frozen['actual_deadline_exhaustion']['stages'])):
        for stage in stages:
            expected[mode + '-' + stage] = (mode, stage, None)
    for index, spec in enumerate(frozen['current_authority_matrix'], 1):
        expected['authority-' + str(index)] = ('current_authority', spec, None)
    expected['missing-execution-context'] = ('missing_context', frozen['missing_context'], None)
    for spec in frozen['staged_taint_guards']:
        for role in ('source', 'control'):
            expected[spec['name'] + '-' + role] = ('staged_guard', spec, role)
    entries = {row['name']: row for row in summary['boundaries']}
    require(len(entries) == len(summary['boundaries']) == len(expected) == 104 and set(entries) == set(expected),
            'Complete frozen 104-role boundary inventory differs')
    report = {'schema_version': 'ontokin.c087-independent-boundary-audit/0.1',
        'status': 'running', **input_lineage(fixtures), 'implementation': git,
        'reader_python': platform.python_version(), 'reader_interpreter': sys.executable,
        'producer_status_flags_used': False, 'records': [], 'failures': [],
        'scope': '87 real cap prefixes, four callback stages, four real deadlines, four current-authority cases, one missing context and four staged taint guards.',
        'private_raw_rule_semantics': 'Null raw internal DEPENDENCY-CYCLE rule IDs denote inherited LANG-009 at serialization; private source traces are not public diagnostic objects.',
        'release_acceptance': False, 'full_product_acceptance': False}
    for name, (kind, spec, role) in expected.items():
        entry = entries[name]
        require(entry['record'] == 'boundaries/' + name + '.json' and entry['kind'] == kind,
                'A frozen role points at another retained record')
        path = ordinary_path(results, entry['record']); evidence.append(fingerprint(path))
        record = loads(path.read_bytes())
        try:
            require(record['name'] == name and record['kind'] == kind, 'Retained boundary record identity differs')
            values = private_values(record, results, evidence) if 'trace' in record else None
            if kind == 'direct_operation_cap':
                require(record['caller_caps'] == {'max_operations': role}, 'Direct cap differs from named frozen role')
                observation = direct(record, spec, fixtures['core_cases'][spec['source_case']], fixtures, values)
            elif kind in ('cancellation', 'deadline'):
                observation = interrupted(record, kind, spec, fixtures, values)
            elif kind == 'current_authority':
                observation = authority(record, spec, fixtures, values)
            elif kind == 'missing_context':
                observation = missing_context(record, spec, fixtures)
            else:
                observation = staged_guard(record, spec, role, fixtures, values)
            report['records'].append({'name': name, 'kind': kind, 'status': 'passed', **observation})
        except Exception as error:
            failure = {'name': name, 'kind': kind, 'status': 'failed', 'exception': type(error).__name__,
                       'reason': str(error), 'traceback': traceback.format_exc()}
            report['records'].append(failure); report['failures'].append(failure)
    report.update(status='failed' if report['failures'] else 'passed',
        kinds=dict(Counter(row['kind'] for row in report['records'])),
        supplied_evidence=evidence, implementation_files=len(implementation),
        reader_sources=[fingerprint(Path(__file__)),
            fingerprint(Path(sys.modules['tools.verify_string_concat'].__file__)),
            fingerprint(Path(sys.modules['tools.string_concat_reference'].__file__)),
            fingerprint(Path(sys.modules['tools.string_concat_source_reference'].__file__))],
        finished_utc=datetime.now(timezone.utc).isoformat())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--candidate-source', type=Path, required=True)
    parser.add_argument('--producer-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('--output must be a fresh file; retain every prior attempt')
    try:
        fixtures = load_fixtures(args.fixtures)
        report = audit(args.results.resolve(), fixtures, args.candidate_source.resolve(), args.producer_archive.resolve())
    except Exception as error:
        report = {'schema_version': 'ontokin.c087-independent-boundary-audit/0.1', 'status': 'failed',
            'exception': type(error).__name__, 'reason': str(error), 'traceback': traceback.format_exc(),
            'release_acceptance': False, 'full_product_acceptance': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({'status': report['status'], 'records': len(report.get('records', [])),
                      'failures': len(report.get('failures', [])), 'reason': report.get('reason')}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
