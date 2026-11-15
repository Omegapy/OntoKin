#!/usr/bin/env python3
"""Independent C244 synthetic-trace review; no native process is started."""
import argparse
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import random
import struct
import subprocess
import sys
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('repository', type=Path)
    parser.add_argument('package', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    repo, package, out = args.repository.resolve(), args.package.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = repo / 'docs/engineering/second-target-c244/test_decision.py'
    decision = source.with_name('DECISION.md')
    def git(*parts):
        return subprocess.check_output(['git', '-C', str(repo), *parts], text=True).strip()
    before = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (source, decision)}
    commit, tree = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^{tree}')
    assert commit == '8264db6e36b0c6118cf5b7ab2e41724569f72d90'
    assert tree == 'c62c61d0287d5d006d53f653a3df8267289d547c'
    assert not git('status', '--porcelain', '--untracked-files=all')
    spec = importlib.util.spec_from_file_location('reviewed_c244', source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # Run the author's exact suite, retaining complete diagnostics separately.
    author = subprocess.run([sys.executable, '-IB', str(source)], capture_output=True, text=True)
    (out / 'author-controls.log').write_text(author.stdout + author.stderr)
    assert author.returncode == 0

    # Independently read the locked binary fixture's JSON chunk; do not export it.
    glb = package / 'evidence/c210/semantic-export/proof/after.glb'
    raw = glb.read_bytes()
    assert len(raw) == 185236
    assert hashlib.sha256(raw).hexdigest() == '05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8'
    magic, version, size = struct.unpack_from('<III', raw)
    assert magic == 0x46546c67 and version == 2 and size == len(raw)
    length, chunk = struct.unpack_from('<II', raw, 12)
    assert chunk == 0x4e4f534a
    doc = json.loads(raw[20:20+length])
    meshes = tuple(node['mesh'] for node in doc['nodes'])
    assert len(meshes) == 18 and len(set(meshes)) == 5 and meshes == module.MESHES
    assert doc['scenes'][doc.get('scene', 0)]['nodes'] == list(range(18))

    records = []
    def check(name, trace, expected, rationale):
        try:
            actual = module.consistent(**trace)
            error = None
        except Exception as exc:
            actual, error = None, type(exc).__name__ + ': ' + str(exc)
        records.append(dict(name=name, expected=expected, actual=actual,
                            passed=type(actual) is bool and actual == expected,
                            exception=error, rationale=rationale))

    check('baseline', module.sample(), True, 'Complete identity chain and phase order.')

    # Actual temporal permutations, not merely reordering stored arrays.
    for seed in range(12):
        rng = random.Random(seed)
        trace = module.sample()
        capture_order = list(range(18)); edge_order = list(range(18)); final_order = list(range(18))
        rng.shuffle(capture_order); rng.shuffle(edge_order); rng.shuffle(final_order)
        for rank, i in enumerate(capture_order):
            trace['captures'][i] = replace(trace['captures'][i], captured=rank * 2, connected=rank * 2 + 1)
        for rank, i in enumerate(edge_order):
            trace['edges'][i] = replace(trace['edges'][i], sequence=40 + rank)
        for rank, i in enumerate(final_order):
            trace['finals'][i] = replace(trace['finals'][i], sequence=70 + rank)
        for group in ('captures', 'edges', 'finals'):
            rng.shuffle(trace[group])
        check('true-order-permutation-' + str(seed), trace, True,
              'Source index is independent of callback, replacement and final-inventory ordering.')

    # Arbitrary bijective relabeling is legitimate: a new ID's numeric value
    # must not imply an input occurrence or a traversal position.
    trace = module.sample()
    for i in range(18):
        old, new = 5000 + 17-i, 9000 + (i*7) % 18
        trace['captures'][i] = replace(trace['captures'][i], old=old, forward=old)
        trace['edges'][i] = replace(trace['edges'][i], old=old, new=new)
        trace['finals'][i] = replace(trace['finals'][i], node=new)
    check('bijective-identity-renaming', trace, True, 'Only observed edges associate native IDs with source nodes.')

    for i in range(18):
        j = (i+1) % 18
        # Coupled corruptions retain superficial edge/final consistency.
        trace = module.sample()
        trace['captures'][i] = replace(trace['captures'][i], old=100+j, forward=100+j)
        trace['edges'][i] = replace(trace['edges'][i], old=100+j)
        check(f'coupled-duplicate-original-{i}', trace, False, 'Two source occurrences cannot share the same original identity.')

        trace = module.sample()
        trace['edges'][i] = replace(trace['edges'][i], new=200+j)
        trace['finals'][i] = replace(trace['finals'][i], node=200+j)
        check(f'coupled-duplicate-final-{i}', trace, False, 'A final identity cannot belong to two source occurrences.')

        trace = module.sample()
        trace['edges'][i] = replace(trace['edges'][i], new=100+j)
        trace['finals'][i] = replace(trace['finals'][i], node=100+j)
        check(f'coupled-retired-alias-{i}', trace, False, 'A final identity cannot alias any original identity.')

        trace = module.sample()
        trace['edges'][i] = replace(trace['edges'][i], old=100+j)
        check(f'cross-index-old-{i}', trace, False, 'Edge must begin at the exact source-bound original.')

        trace = module.sample()
        trace['captures'][i] = replace(trace['captures'][i], inverse=j)
        check(f'inverse-mismatch-{i}', trace, False, 'Both original loader-map directions must agree.')

        trace = module.sample()
        trace['edges'][i] = replace(trace['edges'][i], sequence=36)
        trace['captures'][j] = replace(trace['captures'][j], captured=37, connected=38)
        check(f'other-node-not-yet-subscribed-{i}', trace, False, 'Every subscription must precede the first replacement.')

        trace = module.sample()
        trace['finals'][i] = replace(trace['finals'][i], sequence=59)
        check(f'early-final-{i}', trace, False, 'A signal-time value cannot be labeled a completed post-return observation.')

        for group in ('captures', 'edges', 'finals'):
            trace = module.sample()
            trace[group][i] = replace(trace[group][i], index=False)
            check(f'boolean-index-{group}-{i}', trace, False, 'Boolean source indices are not integers under the contract.')

    # A complete trace still must refuse malformed field representations.
    cases = {
        'captures': {
            'mesh': [True, 0.0, -1, None, '0'],
            'old': [True, 100.0, -1, None, '100', 0],
            'forward': [True, 100.0, -1, None, '100'],
            'inverse': [False, 0.0, -1, None, '0'],
            'captured': [False, 0.0, -1, None, '0'],
            'connected': [True, 1.0, -1, None, '1'],
            'flags': [False, 0.0, -1, None, '0', 4],
            'origin': [False, 0, None, [], {}, 'observer-derived']},
        'edges': {
            'old': [True, 100.0, -1, None, '100', 0],
            'new': [True, 200.0, -1, None, '200', 0],
            'sequence': [True, 40.0, -1, None, '40'],
            'root': [0, 1, None, '', [], {}]},
        'finals': {
            'node': [True, 200.0, -1, None, '200', 0],
            'sequence': [True, 70.0, -1, None, '70'],
            'live': [0, 1, None, 'true', [], {}],
            'member': [0, 1, None, 'true', [], {}],
            'native_class': [None, False, 0, [], {}, 'Node3D']}}
    for group, fields in cases.items():
        for field, values in fields.items():
            for number, value in enumerate(values):
                trace = module.sample()
                trace[group][0] = replace(trace[group][0], **{field: value})
                check(f'malformed-{group}-{field}-{number}', trace, False,
                      'A malformed or forbidden value must not pass a complete trace.')

    for key, values in {
        'fatal': [True, None, 0, 1, 'false', [], {}],
        'returned_at': [False, 60.0, -1, None, '60'],
        'root_class': [False, 0, None, [], {}, 'ImporterMeshInstance3D']}.items():
        for number, value in enumerate(values):
            trace = module.sample(); trace[key] = value
            check(f'malformed-argument-{key}-{number}', trace, False,
                  'Malformed phase/fatal/root inputs refuse; truthiness must not bypass a fatal latch.')

    for group in ('captures', 'edges', 'finals'):
        for value_name, value in [('missing',None),('mapping',{}),('empty',[]),('text','')]:
            trace = module.sample(); trace[group] = value
            check(f'inventory-{group}-{value_name}', trace, False, 'Each group must contain all 18 typed source-index records.')

    after = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (source, decision)}
    unchanged = before == after and not git('status', '--porcelain', '--untracked-files=all')
    result = dict(schema='ontokin.c245.independent-controls-review/0.1',
                  recordedAtUtc=datetime.now(timezone.utc).isoformat(), commit=commit, tree=tree,
                  interpreter=sys.version, executable=sys.executable, platform=platform.platform(),
                  sourceSha256=before, sourceUnchanged=unchanged,
                  authorReturnCode=author.returncode, authorMethods=44,
                  nativeStarts=0, aggregateRuns=0,
                  fixture=dict(path=str(glb.relative_to(package)), sha256=hashlib.sha256(raw).hexdigest(),
                               bytes=len(raw), nodes=len(meshes), distinctMeshes=len(set(meshes)),
                               nodeMeshPairs=list(enumerate(meshes))),
                  independentCases=len(records), validCases=sum(r['expected'] for r in records),
                  refusalCases=sum(not r['expected'] for r in records),
                  failures=[r for r in records if not r['passed']], records=records,
                  passed=unchanged and all(r['passed'] for r in records))
    (out/'RESULT.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('commit','tree','authorMethods','independentCases','validCases','refusalCases','passed','failures','sourceUnchanged','nativeStarts')}, indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
