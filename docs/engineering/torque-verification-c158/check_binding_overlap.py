"""Run in a fresh interpreter: python check.py /path/to/checkout [samples.json.gz]."""
import builtins
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from ontokin import torque_canonical_spin as spin, torque_runtime as runtime
from ontokin.diagnostics import OntoKinError

original = spin._RUNTIME_BINDING
compiled = original[5]
point = {(id(o), n): v for o, n, v in runtime._CANONICAL_POINT_ENTRY[0][2]}
common = [(o, n, v) for o, n, v in compiled[4] if (id(o), n) in point and point[id(o), n] is v]
assert len(common) == 30 and all(o is vars(builtins) for o, n, v in common)
keys = {n for o, n, v in common}
target = compiled[2][0]


def probe(elide_hex, collide):
    original_hex = builtins.hex
    calls = []

    class Key:
        def __hash__(self):
            return hash(target)

        def __eq__(self, other):
            if other == target:
                calls.append(other)
                builtins.hex = None
            return False

    instance = object.__new__(runtime.TorqueSimulator)
    if collide:
        vars(instance)[Key()] = True
    try:
        if elide_hex:
            rows = tuple(r for r in compiled[4] if not (r[0] is vars(builtins) and r[1] == 'hex'))
            spin._RUNTIME_BINDING = (*original[:5], (compiled[0], spin._compile_bindings(rows), *compiled[2:]))
        runtime.TorqueSimulator.__init__(instance, None)
    except OntoKinError as exc:
        return {'phase': exc.diagnostic.phase, 'code': exc.code, 'message': str(exc), 'comparisons': calls}
    finally:
        builtins.hex = original_hex
        spin._RUNTIME_BINDING = original


results = {f'elide_hex={elide},collide={collide}': probe(elide, collide)
           for elide in (False, True) for collide in (False, True)}
assert [r['phase'] for r in results.values()] == ['support', 'evaluation', 'support', 'support']
report = {'point_rows': len(point), 'simulator_rows': len(compiled[4]), 'shared_builtins': sorted(keys), 'probes': results}
if len(sys.argv) > 2:
    sample_path = Path(sys.argv[2])
    with gzip.open(sample_path, 'rt') as stream:
        raw = json.load(stream)
    spec = compiled[1][-1]
    rows = (*spec[8][3], *spec[8][2])  # absent before present on simulator
    lines = [i for i, line in enumerate(spec[9].splitlines(), 1) if line.startswith('        if ')]
    assert len(lines) == len(rows)
    common_lines = {line for row, line in zip(rows, lines) if row[0] is vars(builtins) and row[1] in keys}
    hits = []
    for _, _, ids in raw['samples']:
        stack = [raw['frames'][i] for i in ids[:3]]
        if len(stack) == 3 and [frame[1] for frame in stack] == ['build.<locals>.predicate', '_bindings_current', '_admit_simulator_runtime'] and stack[2][2] == 488:
            hits.append(stack[0][2])
    assert hits, 'No generated predicate samples at the expected simulator callsite'
    report['samples'] = {
        'input_sha256': hashlib.sha256(sample_path.read_bytes()).hexdigest(),
        'all': len(raw['samples']),
        'final_bindings': len(hits),
        'shared_checks': sum(line in common_lines for line in hits),
    }
print(json.dumps(report, indent=2))
