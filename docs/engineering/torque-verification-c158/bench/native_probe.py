"""Compile an isolated C helper and time it with the first actual A08 source watch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shlex
import statistics
import subprocess
import sys
import sysconfig
import tempfile
import timeit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('repo', type=Path)
parser.add_argument('requests', type=Path)
parser.add_argument('--cc', default='cc')
args = parser.parse_args()
repo = args.repo.resolve()
sys.path.insert(0, str(repo))
from ontokin import torque_runtime as rt
from ontokin.execution_budget import HostPolicy
from ontokin.torque_agent import TorqueAgentService

if sys.implementation.name != 'cpython' or sys.version_info[:2] != (3, 12):
    sys.exit('Use the prepared GIL-enabled CPython 3.12 interpreter.')

class Captured(BaseException):
    pass

def first_watch(tmp):
    def request(which):
        return json.loads((args.requests / (which+'-request.json')).read_bytes())
    with TorqueAgentService(tmp/'store', host_policy=HostPolicy(max_elapsed_ms=80000, max_operations=1000000)) as service:
        assert service.handle(request('create'))['status'] == 'succeeded'
        def capture(code, offset, value):
            raise Captured(value)
        mon = sys.monitoring
        tool = mon.PROFILER_ID
        mon.use_tool_id(tool, 'capture first watch')
        mon.register_callback(tool, mon.events.PY_RETURN, capture)
        mon.set_local_events(tool, rt._source_watches.__code__, mon.events.PY_RETURN)
        try:
            service.handle(request('export'))
            raise AssertionError('source watch was not reached')
        except Captured as event:
            return event.args[0]
        finally:
            mon.set_local_events(tool, rt._source_watches.__code__, 0)
            mon.register_callback(tool, mon.events.PY_RETURN, None)
            mon.free_tool_id(tool)

from itertools import chain
from operator import is_
_F_NUMERATOR = rt._F_NUMERATOR
_F_DENOMINATOR = rt._F_DENOMINATOR

def native_guard(watches):
    # Same surrounding Python checks as the stock helper. Only runs on captured watches.
    (owners, instances, dictionaries, sequences, fractions, key_views, value_views), retained, signature = watches
    return (all(map(is_, map(type, owners), signature[0]))
        and all(map(is_, map(vars, instances), signature[1]))
        and native_scan(dictionaries, signature[2], retained[0], retained[1])
        and tuple(map(len, sequences)) == signature[3]
        and all(map(is_, chain.from_iterable(sequences), retained[2]))
        and all(map(is_, map(_F_NUMERATOR, fractions), retained[3]))
        and all(map(is_, map(_F_DENOMINATOR, fractions), retained[4])))

passed = []
def verify(name, w, expected):
    assert rt._source_watches_current(w) is expected, name
    assert native_guard(w) is expected, name
    passed.append(name)

class Hostile:
    forbidden = False
    def __eq__(self, other):
        raise AssertionError('foreign equality invoked')
    def __hash__(self):
        if self.forbidden:
            raise AssertionError('foreign hash invoked')
        return 1

def synthetic_controls():
    def mutate(name, owners, change, expected=False):
        w = rt._source_watches((owners,))
        change(*owners)
        verify(name, w, expected)

    mutate('same object written back', [{'k': []}], lambda d: d.update(k=d['k']), True)
    mutate('equal but distinct value', [{'k': [1]}], lambda d: d.update(k=[1]))
    mutate('hostile value', [{'k': Hostile()}], lambda d: d.update(k=Hostile()))
    def replace_key(d):
        key, = d
        value = d.pop(key)
        other = ('!' + key)[1:]
        assert other == key and other is not key
        d[other] = value
    mutate('equal but distinct key', [{'original-non-interned-name': 8}], replace_key)
    mutate('key order', [{'a': 1,'b': 2}], lambda d: d.update(a=d.pop('a')))
    mutate('adjacent dicts preserve flattened keys and values', [{'a': 1},{}], lambda a,b: b.update(a=a.pop('a')))
    mutate('empty dictionaries', [{},{}], lambda *ds: None, True)
    key = Hostile()
    namespace = {key: 'value'}
    w = rt._source_watches(([namespace],))
    key.forbidden = True
    verify('hostile live key hash disabled after insertion', w, True)
    mutate('list leaf', [[[]]], lambda xs: xs.__setitem__(0, []))
    class Holder: pass
    a, b = Holder(), Holder()
    a.x, a.y = 1, 2
    b.y, b.x = 2, 1
    w = rt._source_watches(([a,b],))
    verify('opposite insertion orders for two instance namespaces', w, True)
    a.__dict__['x'] = a.__dict__.pop('x')
    verify('delete and reinsert in an instance namespace', w, False)
    class Replacement:
        def __getattribute__(self, name):
            raise AssertionError('class guard should run before instance access')
    h = Holder()
    mutate('owner class changed', [h], lambda h: object.__setattr__(h, '__class__', Replacement))
    mutate('instance namespace replaced', [Holder()], lambda h: setattr(h,'__dict__',{}))

def malformed_controls():
    class DictSubclass(dict):
        def __len__(self):
            raise AssertionError('subclass length called')
    for name, provided, error in [
        ('non-tuple container', ([],(),(),()), TypeError),
        ('dict subclass', ((DictSubclass(),),(0,),(),()), TypeError),
        ('non-exact length', (({},),(False,),(),()), TypeError),
        ('out-of-range length', (({},),(2**100,),(),()), OverflowError),
    ]:
        try:
            native_scan(*provided)
        except error:
            passed.append(name)
        else:
            raise AssertionError(name)
    for name, provided in [
        ('missing dict length', (({},),(),(),())),
        ('negative dict length', (({},),(-1,),(),())),
        ('wrong value count', ((),(),(1,),())),
        ('wrong flat count', ((),(),(1,),(1,))),
    ]:
        assert native_scan(*provided) is False, name
        passed.append(name)

def sample(w, rounds=21, calls=400):
    (_, _, ds, _, _, keys, values), retained, signature = w
    def python_segment():
        return (tuple(map(len, ds)) == signature[2]
            and all(map(is_, chain.from_iterable(keys), retained[0]))
            and all(map(is_, chain.from_iterable(values), retained[1])))
    def c_segment():
        return native_scan(ds, signature[2], retained[0], retained[1])
    cases = {'stock_segment': python_segment, 'native_segment': c_segment,
             'stock_full': lambda: rt._source_watches_current(w), 'native_full': lambda: native_guard(w)}
    assert all(f() for f in cases.values())
    for f in cases.values():
        timeit.timeit(f, number=100)
    series = {k: [] for k in cases}
    rng = random.Random(158)
    for _ in range(rounds):
        names = list(cases)
        rng.shuffle(names)
        for key in names:
            series[key].append(timeit.timeit(cases[key], number=calls) * 1e6 / calls)
    return {'rounds': rounds,'calls_per_round': calls,'microseconds_per_call': series,
            'medians_us': {k: statistics.median(v) for k,v in series.items()},
            'median_paired_savings_us': {k: statistics.median(a-b for a,b in zip(series['stock_'+k], series['native_'+k])) for k in ('segment','full')}}

with tempfile.TemporaryDirectory() as temp:
    tmp = Path(temp)
    source = Path(__file__).resolve().with_name('dictscan.c')
    options = ['-O3','-std=c11','-shared','-fPIC','-Wall','-Werror','-I'+sysconfig.get_path('include')]
    compiler = shlex.split(args.cc)
    subprocess.run([*compiler,*options, str(source), '-o', str(tmp/('_dictscan_probe'+sysconfig.get_config_var('EXT_SUFFIX')))], check=True)
    sys.path.insert(0, str(tmp))
    from _dictscan_probe import scan as native_scan
    w = first_watch(tmp)
    synthetic_controls()
    malformed_controls()
    verify('original captured watch', w, True)
    d = next(d for d in reversed(w[0][2]) if d)
    k = next(reversed(d))
    old_value = d[k]
    try:
        d[k] = Hostile()
        verify('last retained value in captured watch replaced', w, False)
    finally:
        d[k] = old_value
    verify('captured watch restored', w, True)
    # Use a plain source-owned mapping for the key replacement control. Instance
    # dictionaries can share a key table and canonicalize an equal replacement.
    target = next(d for d in w[0][0] if type(d) is dict and len(d) >= 2 and
                  any(type(k) is str and len(k) > 1 for k in d))
    original = tuple(target.items())
    k = next(k for k in target if type(k) is str and len(k) > 1)
    other = ('!' + k)[1:]
    assert k == other and k is not other
    try:
        target.clear()
        target.update((other if key is k else key, v) for key, v in original)
        assert any(item is other for item in target)
        verify('equal but distinct key in captured source mapping', w, False)
        target.clear()
        target.update(reversed(original))
        verify('reversed captured source mapping', w, False)
        target.popitem()
        verify('missing entry in captured source mapping', w, False)
    finally:
        target.clear()
        target.update(original)
    verify('captured source mapping identities and order restored', w, True)
    report = {'build': {'compiler': subprocess.check_output([*compiler,'--version'],text=True).splitlines()[0], 'options': options, 'abi':sysconfig.get_config_var('SOABI'), 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},
              'host':platform.node(),'python':sys.version,'cpu_affinity':sorted(os.sched_getaffinity(0)), 'module_sha256':hashlib.sha256(Path(rt.__file__).read_bytes()).hexdigest(),
              'dicts':len(w[0][2]),'flat_entries':len(w[1][0]),'controls':passed, 'timings':sample(w)}
    print(json.dumps(report,indent=2))
