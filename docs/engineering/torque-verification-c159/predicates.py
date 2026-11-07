"""Compare the emitted authority predicate on original immutable catalogue shapes.
No product edits. Usage: python predicates.py CHECKOUT [PROFILE.gz ...].
"""
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import statistics
import sys
import timeit

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from ontokin import torque_canonical_spin as spin, torque_runtime as rt

catalogue = (
    ("point", rt._CANONICAL_GUARD_BOOTSTRAP[0][11][2], dict.get, dict.__contains__),
    ("globals", spin._RUNTIME_BINDING[5][1][-1], dict.get, dict.__contains__),
    ("descriptors", spin._RUNTIME_BINDING[5][3][-1], spin._PROXY_GET, spin._PROXY_CONTAINS))
kinds = ('stock', 'membership', 'method', 'both')
report = {'python': sys.version, 'platform': platform.platform(), 'cpu': sorted(os.sched_getaffinity(0)),
          'calls_per_window': 4000, 'rounds': 9, 'groups': {}, 'profiles': []}
for name, spec, get, contains in catalogue:
    present, absent = spec[8][-2:]
    assert all(type(r[0]) is (type(type.__dict__) if name == 'descriptors' else dict) for r in (*present, *absent))
    original = spec[9]
    times = {k: [] for k in kinds}
    funcs = {}
    for k in kinds:
        src = original
        if k in ('membership', 'both'):
            src, n = re.subn(r'contains\((v\d+), (v\d+)\)', r'\2 in \1', src)
            assert n == len(absent)
        if k in ('method', 'both'):
            src, n = re.subn(r'getter\((v\d+), (v\d+), (v\d+)\)', r'\1.get(\2, \3)', src)
            assert n == len(present)
        ns = {'__builtins__': {}}
        exec(compile(src, '<isolated-authority-predicate>', 'exec'), ns)
        funcs[k] = ns['build'](spec[7])
        assert funcs[k](get, contains) and spec[0](get, contains)
    rng = random.Random(159)
    for i in range(report['rounds']):
        order = list(kinds)
        rng.shuffle(order)
        for k in order:
            times[k].append(timeit.timeit(lambda: funcs[k](get, contains), number=report['calls_per_window'])
                            * 1e6 / report['calls_per_window'])
    report['groups'][name] = {'present':len(present), 'absent':len(absent), 'source':hashlib.sha256(original.encode()).hexdigest(),
                              'median_us':{k:statistics.median(t) for k,t in times.items()},
                              'paired_savings_us':{k:statistics.median(a-b for a,b in zip(times['stock'],times[k])) for k in kinds[1:]},
                              'raw_us':times}

for arg in sys.argv[2:]:
    p = Path(arg)
    with gzip.open(p, 'rt') as f: raw = json.load(f)
    groups, phases, reader = Counter(), Counter(), Counter()
    sources = {n:s[9].splitlines() for n,s,_,_ in catalogue}
    for t, stage, ids in raw['samples']:
        path = [raw['frames'][i] for i in ids]
        names = {f[1] for f in path}
        phase = next((g for fn,g in [('validate_reach_export','independent reader'),('_encode','encode'),('build_scene','build scene'),('_export_glb','export other')] if fn in names), 'outer')
        phases[phase] += 1
        if phase == 'independent reader':
            if 'TorqueValidationScope._admit_context' in names: reader['scope_context'] += 1
            if 'SharedExecutionBudget.tick' in names: reader['shared_budget_tick'] += 1
            if 'TorqueValidationScope._admit_context' in names and 'SharedExecutionBudget.tick' in names: reader['both'] += 1
        if path[0][1] != 'build.<locals>.predicate': continue
        if path[1][1:] == ['TorqueSimulator.__init__.<locals>.guard',521]:
            g = 'point'
        elif path[1][1] == '_bindings_current' and path[2][1] == '_admit_simulator_runtime':
            g = {475:'descriptors',488:'globals'}[path[2][2]]
        else: continue
        line = sources[g][path[0][2]-1]
        clause = 'absent' if 'if contains(' in line else 'present' if 'if getter(' in line else 'other'
        groups[g+' '+clause] += 1
    report['profiles'].append({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'total':len(raw['samples']),
         'phases':phases,'independent_reader_inclusive':reader,'clause_leaves':groups})
print(json.dumps(report, indent=2))
