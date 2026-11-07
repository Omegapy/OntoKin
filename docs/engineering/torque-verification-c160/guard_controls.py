"""Run with the restored Python 3.12 interpreter and checkout path."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import re
import sys
from types import MappingProxyType

parser = argparse.ArgumentParser()
parser.add_argument('checkout')
args = parser.parse_args()
sys.path.insert(0, args.checkout)
from ontokin import torque_canonical_spin as spin, torque_runtime as runtime

binding = spin._RUNTIME_BINDING
compiled = binding[5][3]
spec = compiled[-1]
present, absent = spec[8][-2:]
native, getter = spin._PROXY_CONTAINS, spin._PROXY_GET
assert (len(present), len(absent)) == (84, 151)
source, count = re.subn(r'contains\((v\d+), (v\d+)\)', r'(\2 in \1 if contains is native else contains(\1, \2))', spec[9])
assert count == len(absent)
source = source.replace('def build(values):', 'def build(values, native):')


def build(candidate, operands):
    if not candidate and operands is spec[7]:
        return spec
    ns = {'__builtins__': {}}
    s = source if candidate else spec[9]
    exec(compile(s, '<descriptor-control>', 'exec'), ns)
    fn = ns['build'](operands, native) if candidate else ns['build'](operands)
    return (fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__, fn.__closure__, fn.__globals__, fn.__builtins__, operands, spec[8], s)


def check(sp, get=getter, contains=native):
    return spin._bindings_current((*compiled[:-1], sp), get, contains)


def native_row_trace(sp):
    """Observe only generated source lines, preserving both native accessors."""
    rows = {}
    for line, text in enumerate(sp[9].splitlines(), 1):
        match = re.search(r'(contains|getter)\(v(\d+), v(\d+)', text)
        if match:
            kind, owner, name = match.groups()
            rows[line] = ('absent' if kind == 'contains' else 'present',
                          id(sp[7][int(owner)]), sp[7][int(name)])
    assert len(rows) == len(absent) + len(present)
    mon = sys.monitoring
    tool = next(i for i in range(6) if mon.get_tool(i) is None)
    code = sp[1]
    events = []
    def observe(current, line):
        if current is code and line in rows:
            events.append(rows[line])
    mon.use_tool_id(tool, 'native descriptor lines')
    try:
        mon.register_callback(tool, mon.events.LINE, observe)
        mon.set_local_events(tool, code, mon.events.LINE)
        value = check(sp)
    finally:
        mon.set_local_events(tool, code, 0)
        mon.register_callback(tool, mon.events.LINE, None)
        mon.free_tool_id(tool)
    return value, events


def owner_class(proxy):
    return next(cls for cls in binding[2] if cls.__dict__ == proxy)


@contextmanager
def change(cls, name, value):
    exists = name in cls.__dict__
    original = cls.__dict__.get(name)
    setattr(cls, name, value)
    try:
        yield
    finally:
        if exists:
            setattr(cls, name, original)
        else:
            delattr(cls, name)


class Marker(Exception):
    pass


def run(candidate):
    sp = build(candidate, spec[7])
    assert len(sp[9].encode('ascii')) <= spin._PREDICATE_TEXT_BYTES
    fn = sp[0]
    result = {'source_sha256': hashlib.sha256(sp[9].encode()).hexdigest(), 'source_bytes':len(sp[9].encode('ascii')), 'absent':len(absent),'present':len(present)}
    assert check(sp)
    for rows, tag, indices in [(absent,'absent',[0,75,150]),(present,'present',[40])]:
        for index in indices:
            row = rows[index]
            owner, name = owner_class(row[0]), row[1]
            events = []
            def record_contains(proxy, key):
                events.append(('absent', id(proxy), key))
                return native(proxy, key)
            def record_get(proxy, key, default):
                events.append(('present', id(proxy), key))
                return getter(proxy, key, default)
            with change(owner, name, object()):
                assert not check(sp) and not check(sp,record_get,record_contains)
                native_result, native_rows = native_row_trace(sp)
            wanted = [('absent',id(r[0]),r[1]) for r in (absent[:index+1] if tag=='absent' else absent)]
            if tag=='present':
                wanted += [('present',id(r[0]),r[1]) for r in present[:index+1]]
            assert not native_result and native_rows == wanted and events == wanted
            result[f'{tag}_{index}'] = {'owner':owner.__name__, 'name':name,
                'supplied_accessor_calls':len(events), 'native_clause_lines':len(native_rows)}
    full = [('absent',id(r[0]),r[1]) for r in absent] + [('present',id(r[0]),r[1]) for r in present]
    value, native_rows = native_row_trace(sp)
    assert value and native_rows == full
    result['native_success_clause_lines'] = len(native_rows)
    marker = Marker('same object')
    def reject(*args):
        raise marker
    def must_not_run(*args):
        raise AssertionError('later present getter ran')
    for label, args in [('contains',(must_not_run,reject)),('getter',(reject,native))]:
        try:
            check(sp,*args)
        except Marker as exc:
            assert exc is marker
        else:
            raise AssertionError(label)
        result[label+'_exception_identity'] = True
    # Replace one closure proxy with a copy of its class dictionary; the actual
    # generated instructions receive native mapping proxies throughout.
    owner, key = absent[0][:2]
    target_row = absent[75]
    target = owner_class(target_row[0]); target_name = target_row[1]
    for raising in (False,True):
        calls = []
        class Collision:
            def __hash__(self): return hash(key)
            def __eq__(self, other):
                if other == key:
                    calls.append(other)
                    setattr(target,target_name,object())
                    if raising: raise marker
                return False
        data = dict(owner); data[Collision()] = object()
        proxy = MappingProxyType(data)
        assert target_name not in target.__dict__ and not calls
        cp = build(candidate,tuple(proxy if v is owner else v for v in sp[7]))
        try:
            try:
                value = check(cp,must_not_run,native)
            except Marker as exc:
                assert raising and exc is marker
            else:
                assert not raising and value is False
            assert calls == [key] and target_name in target.__dict__
        finally:
            if target_name in target.__dict__: delattr(target,target_name)
        result['collision_'+('raises' if raising else 'mutates')] = {'equality_visits':calls,'later_absence':target_name}
    for slot, new in [('__defaults__',(None,)),('__kwdefaults__',{}),('__code__',fn.__code__.replace())]:
        old = getattr(fn,slot)
        try:
            setattr(fn,slot,new)
            assert not check(sp,reject,reject)
        finally:
            setattr(fn,slot,old)
    assert fn.__closure__ is sp[4] and sp[0].__globals__ is sp[5] and not sp[6]
    assert all(cell.cell_contents is (native if n=='native' else sp[7][int(n[1:])]) for n,cell in zip(fn.__code__.co_freevars,fn.__closure__))
    result['authority'] = {'mutable_slots_rejected_before_callbacks':3,'closure_operands_verified':len(fn.__closure__)}
    # The candidate's added authority cell can be assigned in ordinary Python.
    # Passing the same foreign accessor then selects the operator branch.
    if candidate:
        cell = fn.__closure__[fn.__code__.co_freevars.index('native')]
        assert cell.cell_contents is native
        try:
            cell.cell_contents = reject
            assert check(sp, getter, reject)
        finally:
            cell.cell_contents = native
        result['altered_native_cell_plus_raising_accessor'] = 'returned True'
    else:
        try:
            check(sp, getter, reject)
        except Marker as exc:
            assert exc is marker
        else:
            raise AssertionError('stock missed substituted accessor')
        result['altered_native_cell_plus_raising_accessor'] = 'no added cell; supplied accessor raised exact marker'
    old = spin._RUNTIME_BINDING
    updated = (*compiled[:-1],sp)
    spin._RUNTIME_BINDING = (*old[:5],(*old[5][:3],updated,*old[5][4:]))
    try:
        class Sub(runtime.TorqueSimulator): pass
        for cls in [runtime.TorqueSimulator,Sub]:
            spin._admit_simulator_runtime(object.__new__(cls))
        old_contains = spin._PROXY_CONTAINS
        try:
            spin._PROXY_CONTAINS = reject
            try:
                spin._admit_simulator_runtime(object.__new__(runtime.TorqueSimulator))
            except Marker as exc:
                assert exc is marker
            else:
                raise AssertionError('exact caller ignored replacement')
            spin._admit_simulator_runtime(object.__new__(Sub))
        finally:
            spin._PROXY_CONTAINS = old_contains
        with change(Sub,'_dependencies',object()):
            try: spin._admit_simulator_runtime(object.__new__(Sub))
            except spin.OntoKinError as exc: assert exc.code == 'OKL-E-RESOURCE'
            else: raise AssertionError('subclass shadow')
    finally:
        spin._RUNTIME_BINDING = old
    result['runtime'] = ['exact admitted','subclass admitted','subclass shadow rejected',
                         'exact caller propagated replacement membership marker',
                         'subclass admitted while exact-path membership accessor replaced']
    return result

print(json.dumps({'python':sys.version,'stock':run(False),'accessor_identity_candidate':run(True)},indent=2))
