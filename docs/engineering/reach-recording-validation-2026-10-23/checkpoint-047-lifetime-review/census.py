#!/usr/bin/env python3
"""Pure source/JSON census of C047's retained current L03 prefix; no product imports."""
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys


def utc():
    return datetime.now(timezone.utc).isoformat()


def unique(items):
    result = {}
    for key, value in items:
        assert key not in result, 'duplicate JSON key'
        result[key] = value
    return result


def read(path):
    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def binding(path, root):
    raw = path.read_bytes()
    return {'path': path.relative_to(root).as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def emit(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def clock(value):
    return str(value['numerator']) + '/' + str(value['denominator'])


def cursor_key(row):
    key = row['key']
    assert key[:4] == ['reference_pose', 128, 32768, 'recording_center_body_orientation']
    context, frame = key[4]
    assert context[2] in (0, 1) and context[3] == 'after'
    # Native phase/frame fields identify this census row. Opaque IDs are not
    # used to infer retained object or numerical payload equality.
    return context[2], context[3], frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = args.workspace.resolve()
    out = args.output.resolve()
    out.mkdir(exist_ok=False, parents=True)
    start = utc()
    repo = base / 'OntoKin'
    caproot = base / 'c047-execution/capture-001'
    cap = read(caproot / 'capture.json')
    ledger = read(caproot / 'key-ledger.json')
    failure = read(caproot / 'failure-locals.json')
    pair = read(base / 'c047-independent-comparison/result.json')
    tree = read(base / 'c047-recovery/remote-tree.json')
    entries = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
    source_names = [
        'ontokin/reach_reference.py', 'ontokin/reach_reference_center.py',
        'ontokin/reach_reference_plan.py', 'ontokin/reach_conformance.py',
        'ontokin/reach_numeric.py', 'ontokin/construction.py',
        'tools/build_reach_source_artifacts.py',
        'docs/engineering/reach-recording-validation-2026-10-23/checkpoint-046-capture.py',
    ]
    paths = [repo / p for p in source_names]
    paths += [base / 'c047-recovery/remote-tree.json',
              base / 'c047-independent-comparison/result.json',
              base / 'c047-independent-comparison/review.md',
              caproot / 'capture.json', caproot / 'key-ledger.json',
              caproot / 'failure-locals.json']
    descriptors = cap['ordered_cache_snapshot_files']
    paths += [caproot / d['path'] for d in descriptors]
    before = [binding(p, base) for p in paths]
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append(name)

    check('pair independently admissible', pair['status'] == 'passed' and not pair['findings'])
    check('current actual source identity', cap['source_commit'] == pair['source_commit'] ==
          '48b5d381a0f86d9706a109b78e2ce52eb0d287f0' and
          cap['source_tree'] == pair['source_tree'] == tree['sha'] ==
          '33ac0caa77528432d18132a1e606d1e4fbd7ab80')
    check('capture errors empty and original request failed',
          cap['observation_errors'] == [] and cap['status'] == 'captured_failed_request'
          and cap['product_request_status'] == 'failed' and not cap['accepted_artifact'])
    check('native outer checks preserved', len(cap['identity_checks']) == 18 and
          all(value is True for value in cap['identity_checks'].values()))
    check('native callback domain', cap['callbacks']['external'] == {
        'module': 'ontokin.construction', 'qualname': 'ConstructionBudget.tick',
        'bound_owner_type': 'ConstructionBudget'} and
        cap['callbacks']['construction_check'] is None and
        cap['callbacks']['observer_at_reader_entry'] is None and
        cap['callbacks']['observer_after_request'] is None)
    check('original work limits', cap['work_limits'] == {
        'max_operations': 100000, 'max_elapsed_ms': 30000,
        'max_operand_bits': 32768, 'max_cache_entries': 256})
    check('snapshot exact unique membership', len(descriptors) == 311 and
          len({d['path'] for d in descriptors}) == 311 and
          {p.relative_to(caproot).as_posix() for p in (caproot/'ordered-cache-boundaries').iterdir()} ==
          {d['path'] for d in descriptors})

    source = []
    selected_names = {'_sync_cache_operand_limit', 'tick', 'lookup', 'remember',
                      '_series_integer', '_series_coefficients', '_series_dyadic',
                      '_recording_cartesian_rotate', 'discard_cursors', '__exit__',
                      'publish', 'close', 'prepare', 'evaluate', '_phase_poses',
                      '_key_comparisons', '_verify_certificates', '_orientation',
                      'recording_centered_poses', '_recording_centered_poses'}
    for name in source_names:
        raw = (repo/name).read_bytes()
        expected = entries[name]
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert blob == expected['sha'] and len(raw) == expected['size']
        lines = raw.splitlines(keepends=True)
        parsed = ast.parse(raw)
        symbols = []
        def walk(node, prefix=''):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    label = prefix + child.name
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name in selected_names:
                        body = b''.join(lines[child.lineno-1:child.end_lineno])
                        symbols.append({'symbol': label, 'start': child.lineno, 'end': child.end_lineno,
                                        'sha256': hashlib.sha256(body).hexdigest()})
                    walk(child, label+'.')
                else:
                    walk(child, prefix)
        walk(parsed)
        source.append({'path': name, 'bytes': len(raw), 'git_blob': blob,
                       'sha256': hashlib.sha256(raw).hexdigest(), 'symbols': symbols})
    check('all eight source files match actual remote blobs', len(source) == 8)

    snapshots = {}
    snapshot_bytes = 0
    failed_key = ('series_coefficients', 32768, 129, 14)
    for d in descriptors:
        path = caproot/d['path']
        raw = path.read_bytes()
        assert len(raw) == d['bytes'] and hashlib.sha256(raw).hexdigest() == d['sha256']
        s = read(path)
        rows = s['ordered_rows']
        assert len(rows) <= 256 and [r['ordinal'] for r in rows] == list(range(len(rows)))
        assert s['source_domain'] == {'bits': 128, 'scale': 1 << 128, '_cache_operand_limit': 32768}
        assert s['work_operand_limit'] == 32768
        coeff = [r for r in rows if r['key'][0] == 'series_coefficients']
        for row in coeff:
            key = row['key']
            assert len(key) == 4 and key[1] == 32768 and all(type(x) is int for x in key[1:])
            meta = row['series_value']
            assert meta['native_immutable_integer_tuple_shape'] is True
            assert meta['coefficient_count'] == key[3] + 1 == len(meta['coefficient_bits'])
        assert failed_key not in {tuple(r['key']) for r in coeff}
        snapshots[d['path']] = s
        snapshot_bytes += len(raw)
    check('all snapshot bytes hashes domains shapes and failure-key absence', len(snapshots) == 311)

    keys = ledger['keys']
    check('complete consecutive prefix', len(keys) == cap['key_calls'] == 154 and
          [k['index'] for k in keys] == list(range(154)) and
          [k['ordinal'] for k in keys] == list(range(1,155)) and
          all(k['outcome'] == 'returned' for k in keys[:-1]) and keys[-1]['outcome'] == 'raised')
    chronological = []
    boundary_rows = []
    seeds = []
    advances = []
    cursor_losses = []
    for k in keys:
        assert len(k['identity_checks']) == 12 and all(v is True for v in k['identity_checks'].values())
        cursors = {}
        states = {}
        for side in ('entry', 'exit'):
            state = k[side]
            desc = state['source_cache_ordered_snapshot_file']
            assert desc in descriptors
            s = snapshots[desc['path']]
            assert len(s['ordered_rows']) == state['source_cache_entries']
            hist = Counter()
            for r in s['ordered_rows']:
                key = r['key']
                category = key[0]
                if category == 'reference_pose' and len(key) > 3 and type(key[3]) is str:
                    category += ':'+key[3]
                hist[category] += 1
            assert dict(hist) == state['source_cache_categories']
            b = state['source_batch']
            assert b['active'] is True and b['prepared'] is False and b['depth'] == 0
            cs = {cursor_key(r): r['value'] for r in state['source_cursors']}
            assert len(cs) == len(state['source_cursors'])
            cursors[side] = cs
            states[side] = {'reader_entries': state['source_cache_entries'],
                           'coefficient_entries': hist['series_coefficients'],
                           'centered_cursors': len(cs), 'cursor_ledger_entries': b['cursor_ledger_entries'],
                           'plans': len(b['plans']), 'snapshot_path': desc['path']}
            chronological.append((k['index'], side, s))
        for ck in cursors['entry'].keys() - cursors['exit'].keys():
            cursor_losses.append({'index':k['index'],'cursor':ck})
        changes = []
        for ck, v in cursors['exit'].items():
            old = cursors['entry'].get(ck)
            if v == old:
                continue
            row = {'index': k['index'], 'time': clock(k['time']), 'phase': ck[0], 'frame': ck[2],
                   'steps': v['steps'], 'previous_steps': None if old is None else old['steps'],
                   'cursor_clock': clock(v['clock'])}
            assert v['clock'] == k['time']
            if v['steps'] == 0:
                assert old is None or old['steps'] == 64
                seeds.append(row)
                row['change'] = 'published_zero_step'
            else:
                assert old is not None and v['steps'] == old['steps']+1 <= 64
                advances.append(row)
                row['change'] = 'published_advance'
            changes.append(row)
        boundary_rows.append({'index': k['index'], 'time': clock(k['time']), 'outcome': k['outcome'],
                              'entry': states['entry'], 'exit': states['exit'], 'cursor_changes': changes})
    check('all per-key native checks domains category maps and batch states', len(boundary_rows) == 154)
    check('no centered boundary losses', not cursor_losses)
    check('centered cursors survive every exit after key zero', all(k['exit']['source_cursors'] for k in keys[1:]))
    first_batch = keys[0]['exit']['source_batch']
    check('key zero enters empty batch and exits one rejected centered plan',
          keys[0]['entry']['source_batch']['plans'] == [] and
          keys[0]['entry']['source_batch']['cursor_ledger_entries'] == 0 and
          len(first_batch['plans']) == 1 and
          first_batch['plans'][0]['centered_recipe_fields'] is False and
          len(first_batch['plans'][0]['targets']) == 6 and
          len(first_batch['plans'][0]['node_paths']) == 8)
    check('six published zero-step states', len(seeds) == 6 and [r['index'] for r in seeds] == [1,1,66,66,88,88])
    check('296 published advances', len(advances) == 296)
    check('final failed key publishes no cursor', keys[-1]['entry']['source_cursors'] == keys[-1]['exit']['source_cursors'])

    seen = set()
    previous = set()
    transitions = []
    census = {}
    losses = []
    for index, side, s in chronological:
        coeff = {tuple(r['key']) for r in s['ordered_rows'] if r['key'][0] == 'series_coefficients'}
        added, removed = coeff-previous, previous-coeff
        if removed:
            losses.append({'index': index, 'boundary': side, 'keys': sorted(removed)})
        if added or removed:
            transitions.append({'index': index, 'boundary': side, 'coefficient_entries': len(coeff),
                                'first_seen': sorted(coeff-seen), 'removed': sorted(removed)})
        for key in coeff:
            row = census.setdefault(key, {'key': key, 'first_boundary': {'index':index, 'side':side},
                                         'boundary_observations': 0})
            row['last_boundary'] = {'index':index, 'side':side}
            row['boundary_observations'] += 1
        seen |= coeff
        previous = coeff
    check('no observed coefficient boundary removals', not losses)
    check('exact coefficient boundary census', len(seen) == 12 and
          [(x['index'],x['boundary'],x['coefficient_entries']) for x in transitions] ==
          [(0,'entry',7),(1,'exit',9),(66,'exit',11),(88,'exit',12)])
    check('five new exact coefficient keys in captured interval',
          sum(len(x['first_seen']) for x in transitions[1:]) == 5)
    occupancy = [len(s['ordered_rows']) for _,_,s in chronological]
    check('reader occupancy never reaches capacity at a boundary', min(occupancy) == 112 and max(occupancy) == 165)
    check('boundary occupancy nondecreasing', all(a <= b for a,b in zip(occupancy,occupancy[1:])))

    frames = {x['function']:x['locals'] for x in failure['frames']}
    ori, coeff, integer = (frames[k] for k in ('_orientation','_series_coefficients','_series_integer'))
    pending = frames['evaluate']['pending_values']
    check('current precise missed coefficient key and partial construction',
          tuple(coeff['key']) == failed_key and coeff['cached'] is None and coeff['index'] == 7 and
          coeff['odd'] == 15 and coeff['degree'] == 14 and coeff['exponent'] == 129 and
          len(coeff['coefficients']) == 7 and integer['kind'] == 'div' and
          integer['a'] == coeff['common'] and integer['b'] == coeff['factorials'][15])
    check('current retired forearm direct branch',
          ori['node']['path'] == 'rig.arm.forearm.frame' and ori['advance'] is False and
          ori['previous']['steps'] == 64 and clock(ori['clock']) == '244/89' and
          clock(ori['previous']['clock']) == '243/89')
    check('one complete unpublished upper replacement',
          len(pending) == 1 and cursor_key(pending[0]) == (1,'after','rig.arm.upper.frame') and
          pending[0]['value']['steps'] == 0 and pending[0]['previous']['steps'] == 64 and
          clock(pending[0]['value']['clock']) == '244/89')
    check('pre-cleanup endpoint exact', failure['snapshot_boundary'] ==
          '_key_comparisons exception exit before source-batch cleanup')
    after = [binding(p,base) for p in paths]
    check('all census inputs stable', before == after)

    result = {
        'schema':'ontokin.c047-current-l03-cache-lifetime/0.1', 'status':'passed',
        'started_utc':start, 'finished_utc':utc(), 'source_commit':cap['source_commit'],
        'source_tree':cap['source_tree'], 'command':[sys.executable,*sys.argv],
        'execution':{'python':sys.version,'platform':platform.platform()},
        'scope':'Pure source and retained-JSON census; no product import or execution.',
        'checks_passed':len(checks), 'checks':checks, 'input_count':len(paths),
        'snapshots':{'count':311,'bytes':snapshot_bytes,'boundary_snapshots':308,'failure_snapshots':3},
        'current_interval':{'start':'key index 0 entry','end':'key index 153 exception exit before outer cleanup',
                            'start_clock':'0/1','end_clock':'244/89','reader_entry_min':min(occupancy),
                            'reader_entry_max':max(occupancy),'start_entries':occupancy[0],
                            'end_entries':occupancy[-1],'capacity':256},
        'coefficient_census':{'initial_keys':transitions[0]['first_seen'],'birth_boundaries':transitions[1:],
                              'distinct_keys':len(seen),'new_completed_keys':5,'boundary_losses':losses,
                              'failed_key':failed_key,'failed_key_snapshot_occurrences':0},
        'cursor_census':{'published_advances':len(advances),'published_zero_steps':len(seeds),
                         'published_seeds':seeds,'completed_unpublished_zero_steps':1,
                         'failed_direct_selections_before_seed':1,'source_bound_direct_selections':8,
                         'completed_direct_cursors':7,'retirement_direct_selections':4},
        'source_bound_inference':{
            'no_domain_clear':True,'no_effectful_discard':True,'no_capacity_eviction':True,
            'current_product_publish_preserves_size_and_order':True,
            'failed_key_absent_at_interval_start_and_never_completed_within_interval':True,
            'basis':'See review.md: native authority, rejected key-zero plan, continuing centered cursors, complete mutation closure and bounded occupancy.'},
        'interpretation_limits':[
            'Boundary snapshots are not intra-key mutation events.',
            'No exact lookup/hit count or seed-to-coefficient attribution is inferred.',
            'No numerical coefficient payload equality is inferred from IDs or bit widths.',
            'Source setup before key zero, outer cleanup, future tail, hostile/reentrant domains are excluded.',
            'No runtime optimization, measured saving, complete request cost, elapsed neutrality or product/release pass.'],
        'findings':[]}
    emit(out/'result.json',result)
    emit(out/'inputs-before.json',before)
    emit(out/'inputs-after.json',after)
    emit(out/'source-bindings.json',source)
    emit(out/'boundary-census.json',boundary_rows)
    emit(out/'coefficient-census.json',list(census.values()))
    print(json.dumps({'status':result['status'],'checks_passed':len(checks),'input_count':len(paths),
                      'coefficient_keys':len(seen),'new_keys':5,'published_advances':len(advances),
                      'source_bound_interval':result['current_interval']}))


if __name__ == '__main__':
    main()
