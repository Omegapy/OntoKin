#!/usr/bin/env python3
"""Audit C045 source and retained JSON only; never import or run OntoKin."""
import argparse
import ast
from collections import Counter, OrderedDict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

PARENT = '91e8899ad90f04292dd4aee5aaec8b730b397d45'
PARENT_TREE = '11d1ce9acc2cb4fa93be44c4772a9e8e3b3270ff'
BASE = Path('docs/engineering/reach-recording-validation-2026-10-23')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--retained', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    records, checks = [], []

    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append(name)

    def read(root, path, kind):
        data = (root / path).read_bytes()
        records.append({'root': kind, 'path': str(path), 'bytes': len(data), 'sha256': sha(data)})
        return data

    def load(root, path, kind):
        return json.loads(read(root, path, kind))

    census = load(args.repo, BASE / 'checkpoint-044-census.json', 'repo')
    c043 = load(args.repo, BASE / 'checkpoint-043-cost-ledger.json', 'repo')
    manifest = load(args.repo, BASE / 'checkpoint-044-evidence-manifest.json', 'repo')
    member_hashes = {row['path']: row for row in manifest['members']}
    trace_path = Path('c044-execution/pair-001/capture/trace.json')
    trace = load(args.retained, trace_path, 'C044-restored')
    checkpoint_path = Path('c044-analysis/cache-review/attempt-001/ordered-cache-checkpoints.json')
    checkpoints = load(args.retained, checkpoint_path, 'C044-restored')
    equality_path = Path('c044-analysis/cache-review/attempt-001/key-equality.json')
    equality = load(args.retained, equality_path, 'C044-restored')
    old_audit = load(args.retained, Path('c044-analysis/cache-review/attempt-001/audit.json'), 'C044-restored')
    for row in records:
        if row['root'] == 'C044-restored':
            original = member_hashes[row['path']]
            check('restored binding: ' + row['path'],
                  original['bytes'] == row['bytes'] and original['sha256'] == row['sha256'])
    source = {}
    for path in ('ontokin/reach_recording_fast.py', 'ontokin/reach_recording_capture.py',
                 'ontokin/reach_numeric.py', 'ontokin/reach_phase.py', 'ontokin/reach_pose.py',
                 'ontokin/construction.py', 'ontokin/reach_reference_center.py',
                 'ontokin/reach_reference.py'):
        source[path] = read(args.repo, Path(path), 'repo').decode()
    for row in trace['source_bindings']:
        check('traced source unchanged: ' + row['path'], sha(source[row['path']].encode()) == row['sha256'])
    check('trace completion and clean boundaries', trace['complete_to_product_termination']
          and trace['capture_failure'] is None and trace['scope_boundary'] is None
          and trace['hook_ownership_failure'] is None and not trace['unfinished_frames']
          and not trace['final_snapshot_failures'] and trace['functions_unchanged'])
    check('one work object with empty initial cache', len(trace['initial_work_states']) == 1
          and len(trace['final_work_states']) == 1 and not trace['initial_work_states'][0]['cache'])
    check('C043 cold rejections preserved', [x['saving_upper_bound'] for x in c043['counterexamples']] == [-2, -3, -64])
    functions = {x.name: x for x in ast.parse(source['ontokin/reach_recording_fast.py']).body
                 if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}
    target = functions['recording_float_excess']
    assignments = {node.targets[0].id: node for node in target.body
                   if isinstance(node, ast.Assign) and len(node.targets) == 1
                   and isinstance(node.targets[0], ast.Name)}
    def sites(name):
        return sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == 'op' for node in ast.walk(assignments[name].value))
    partition = {name: sites(name) for name in ('source_leaves', 'e', 'g', 'q', 'p', 'rotation_rad')}
    check('exact source arithmetic partition', partition == {'source_leaves': 1, 'e': 4, 'g': 4, 'q': 4, 'p': 10, 'rotation_rad': 1})
    check('position before comparisons before late multiply',
          assignments['p'].lineno < next(node.lineno for node in target.body
            if isinstance(node, ast.If) and any(isinstance(x, ast.Name) and x.id == '_checked_compare'
              for x in ast.walk(node.test))) < assignments['rotation_rad'].lineno)
    check('source constants unchanged', 'PRODUCT_ERROR = F(1,1 << 91)' in source['ontokin/reach_pose.py']
          and 'AXIS_ERROR = F(1,1 << 74)' in source['ontokin/reach_pose.py']
          and 'MAX_RECORDING_ROTATION_STEPS = 10000' in source['ontokin/reach_pose.py'])

    # Replay ONLY the original observed key mutations. Native-equality classes
    # come from C044's independently reviewed, hash-bound equality audit.
    # This is not a candidate-cache simulation or a fresh native equality proof.
    keys = {row['key_id']: row['typed_key'] for row in trace['keys']}
    classes = {int(key): value for key, value in equality['key_to_equality_class'].items()}
    check('retained equality audit has no aliases', len(keys) == 823 and set(keys) == set(classes)
          and all(key == value for key, value in classes.items()) and not equality['typed_alias_groups'])
    cache = OrderedDict()
    mutation_counts = Counter()
    observed_checkpoints = {}
    envelope_calls = {}
    lookups = Counter()
    victims = []
    first_event = census['invocations'][0]['entry_event_id']
    last_event = census['invocations'][-1]['exit_event_id']
    for expected_id, event in enumerate(trace['events'], 1):
        assert event['event_id'] == expected_id
        if event['event'] == 'cache_mutation_completed':
            mutation = event['mutation']
            operation, key = mutation['operation'], mutation['key_id']
            if operation == 'evict':
                assert next(iter(cache)) == key
                cache.pop(key)
                if first_event <= expected_id <= last_event:
                    victims.append(key)
            elif operation == 'set':
                cache[key] = None
            elif operation == 'promote':
                assert key in cache
                cache.move_to_end(key)
            else:
                raise AssertionError(('unknown original mutation', event))
            mutation_counts[operation] += 1
        if event.get('kind') == 'envelope' and event['event'] in ('call', 'return'):
            suffix = 'entry' if event['event'] == 'call' else 'exit'
            if event['event'] == 'call':
                envelope_calls[expected_id] = event['invocation_id']
                invocation_id = event['invocation_id']
            else:
                invocation_id = envelope_calls[event['call_event']]
            name = 'envelope_' + str(invocation_id) + '_' + suffix
            observed_checkpoints[name] = list(cache)
        if event.get('kind') == 'lookup' and event['event'] == 'return':
            lookups[event['lookup_outcome']] += 1
        assert len(cache) == event['mark']['cache_entries'], expected_id
    check('all original event IDs/cache sizes reconcile', len(trace['events']) == 46721)
    check('all original mutations reconcile', dict(mutation_counts) == {'set': 1219, 'promote': 4190, 'evict': 768})
    check('all64 envelope cache orders match retained independent audit',
          observed_checkpoints == checkpoints['envelopes'] and len(observed_checkpoints) == 64)
    check('original final cache order matches', list(cache) == checkpoints['final'])
    check('original lookup outcomes preserved', lookups == {'hit': 3995, 'miss': 1058, 'refusal_before_membership': 1})
    check('final refusal precedes membership', trace['events'][-1]['lookup_outcome'] == 'refusal_before_membership'
          and trace['events'][-1]['membership_attempted'] is False)
    rows = census['invocations']
    check('32 completed cold calls', len(rows) == 32 and all(row['status'] == 'completed'
          and row['lookup']['return_event']['lookup_outcome'] == 'miss' for row in rows))
    check('all original entry caches full', all(row['entry']['cache_entries'] == 256 for row in rows))
    check('one exact angular signature', len(census['actual_angular_signature_groups']) == 1
          and all(tuple(json.dumps(row['inputs'][name], sort_keys=True) for name in
            ('trig_count', 'product_count', 'rotation_error_rad')) ==
            tuple(json.dumps(rows[0]['inputs'][name], sort_keys=True) for name in
            ('trig_count', 'product_count', 'rotation_error_rad')) for row in rows))
    check('32 distinct whole keys', len({row['whole_key_id'] for row in rows}) == 32)
    check('original charge total960', sum(sum(row['charges'].values()) for row in rows) == 960)
    check('31 original one-charge gaps', len(census['adjacent_call_gaps']) == 31
          and all(row['shared_operation_delta'] == 1 and row['reach_operation_delta'] == 1
                  and row['cache_generation_delta'] == 0 for row in census['adjacent_call_gaps']))
    check('exact32 original evictions', len(victims) == 32)
    entry_keys = observed_checkpoints['envelope_1_entry']
    check('all256 original entry keys are tuples', len(entry_keys) == 256
          and all(keys[key][0] == 'tuple' for key in entry_keys))
    immediate_children = sum(len(keys[key][1]) for key in entry_keys)
    check('entry keys contain1656 immediate children', immediate_children == 1656)

    # Bit-length arithmetic is a proof about guards, not evaluation of source
    # Fractions or product formulas. Reduced rational widths cannot grow.
    def pair(value):
        assert value[0] == 'Fraction'
        return tuple(abs(int(item, 16)).bit_length() for item in value[1:])
    observed_widths = []
    for row in census['observed_common_angular_arithmetic_sequence']:
        left, right, result = pair(row['left']), pair(row['right']), pair(row['result'])
        if row['operation'] == 'mul':
            prospective = (left[0] + right[0], left[1] + right[1])
        elif row['operation'] == 'add':
            prospective = (max(left[0] + right[1], right[0] + left[1]) + 1, left[1] + right[1])
        else:
            raise AssertionError(row['operation'])
        assert max(*left, *right, *prospective, *result) <= 32768
        observed_widths.append({'site': row['site'], 'operation': row['operation'],
            'left_bits': left, 'right_bits': right, 'prospective_bits': prospective, 'result_bits': result})
    check('all14 retained angular-site guards fit original cap', len(observed_widths) == 14)
    symbolic = []
    def bound(label, a, b, operation):
        out = ((max(a[0] + b[1], b[0] + a[1]) + 1, a[1] + b[1])
               if operation == 'add' else (a[0] + b[0], a[1] + b[1]))
        symbolic.append({'site': label, 'operation': operation, 'left': a, 'right': b, 'unreduced_result_bound': out})
        return out
    count, sq = (2048, 1), (2048, 2048)
    s = bound('source_leaves.1', count, (1, 1), 'add')
    ea = bound('e.1', count, (1, 42), 'mul')
    eb = bound('e.2', s, (1, 48), 'mul')
    ec = bound('e.3', ea, eb, 'add')
    e = bound('e.4', (2, 1), ec, 'mul')
    ga = bound('g.1', (14, 1), count, 'mul')
    gb = bound('g.2', (2, 1), (1, 92), 'mul')
    gc = bound('g.3', (1, 75), gb, 'add')
    g = bound('g.4', ga, gc, 'mul')
    qa = bound('q.1', (2, 1), sq, 'mul')
    qb = bound('q.2', qa, g, 'add')
    qc = bound('q.3', (5, 1), e, 'mul')
    q = bound('q.4', qb, qc, 'add')
    check('symbolic guard bound4327', max(max(row['unreduced_result_bound']) for row in symbolic) == 4327
          and (s, e, g, q) == ((2050, 2), (2102, 94), (2157, 170), (4327, 2314)))
    check('current angular fields satisfy numerical width prerequisite',
          all(max(pair(row['inputs']['rotation_error_rad'])) <= 2048
              and int(row['inputs']['trig_count'][1], 16).bit_length() <= 2048
              and int(row['inputs']['product_count'][1], 16).bit_length() <= 2048 for row in rows))
    gross = 13 * (len(rows) - 1)
    audit_floor = 2 * len(entry_keys)
    check('defined batch route cannot have positive bound', gross == 403 and audit_floor == 512
          and gross - audit_floor == -109 and gross <= audit_floor)
    check('late-site upper envelope also negative', 14 * (len(rows) - 1) - audit_floor == -78)
    check('minimum prefix cohort41 is necessary only', 13 * 39 <= audit_floor < 13 * 40)
    for row in records:
        root = args.repo if row['root'] == 'repo' else args.retained
        check('input stable: ' + row['path'], sha((root / row['path']).read_bytes()) == row['sha256'])
    result = {'schema': 'ontokin.checkpoint045-source-data-audit/0.1', 'status': 'passed',
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'platform': platform.platform(), 'product_parent': PARENT,
        'parent_tree': PARENT_TREE, 'execution_policy': 'stdlib source AST, typed JSON, original observed key-order replay and integer cost/bit-width proof only; no product import, candidate numerical replay or request',
        'source_partition': partition, 'original_trace_events': len(trace['events']),
        'original_mutations': dict(mutation_counts), 'original_lookup_outcomes': dict(lookups),
        'entry_cache_key_ids': entry_keys, 'original_victim_ids': victims,
        'entry_cache_size': len(entry_keys), 'entry_immediate_key_children': immediate_children,
        'entry_category_count': None, 'entry_category_qualification': 'C044 retained category maps only initially and finally; final222 is not an entry count. No entry count is inferred.',
        'observed_guard_widths': observed_widths, 'symbolic_2048_bit_guard_bounds': symbolic,
        'symbolic_maximum_bits': 4327, 'numerical_domain_eligibility_is_authority': False,
        'candidate': 'B-Angular/full-entry-audit/0.1', 'candidate_implemented': False,
        'prefix_repetitions': 31, 'prefix_gross_ceiling': gross, 'defined_audit_charge_floor': audit_floor,
        'forced_admitted_route_saving_upper_bound': gross - audit_floor,
        'late_reuse_not_selected_upper_bound': -78, 'necessary_cohort_size_at_full_cache': 41,
        'proper_cost_prefilter_accepts_current_batch': False,
        'proper_rejected_route_prefix_reuses': 0, 'measured_candidate_cost': None,
        'positive_complete_bound_established': False, 'universal_impossibility_claimed': False,
        'original_gate': '24/28; C035 held', 'product_requests': 0,
        'inputs': records, 'checks': checks, 'checks_passed': len(checks), 'checks_failed': 0}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('Refuse to overwrite an earlier audit result')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'checks_passed', 'original_trace_events',
        'entry_cache_size', 'prefix_gross_ceiling', 'defined_audit_charge_floor',
        'forced_admitted_route_saving_upper_bound', 'proper_cost_prefilter_accepts_current_batch')}))

if __name__ == '__main__':
    main()
