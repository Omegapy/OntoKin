"""Run in a disposable CPython 3.12 process, passing the restored checkout path."""
import gc
import json
import re
import sys

sys.path.insert(0, sys.argv[1])
from ontokin import torque_canonical_spin as spin, torque_runtime

monitor = sys.monitoring
native = spin._PROXY_CONTAINS
vectors = spin._RUNTIME_BINDING[5][3]
spec = vectors[-1]
rows = spec[8][-1]
assert len(rows) == 151 and len(spec[8][-2]) == 84


def clear():
    code = sys._getframe(1).f_code
    return (not sys.gettrace() and not sys.getprofile() and
            not any(monitor.get_events(i) or monitor.get_local_events(i, code)
                    for i in range(6)))


source, count = re.subn(r'contains\((v\d+), (v\d+)\)',
                        r'(\2 in \1 if fast else contains(\1, \2))', spec[9])
assert count == len(rows)
source = source.replace('build(values)', 'build(values, native, clear)').replace(
    'def predicate(getter, contains):',
    'def predicate(getter, contains):\n        fast = contains is native and clear()')
namespace = {'__builtins__': {}}
exec(compile(source, '<guarded-descriptor-control>', 'exec'), namespace)
fn = namespace['build'](spec[7], native, clear)
candidate = (fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__, fn.__closure__,
             fn.__globals__, fn.__builtins__, spec[7], spec[8], source)


def check(receipt, mode):
    code = receipt[1]
    tool = next(i for i in range(6) if monitor.get_tool(i) is None)
    trace = []
    observer_error = RuntimeError('callback')
    lookup_error = RuntimeError('comparison')
    monitor.use_tool_id(tool, 'late descriptor observer')

    def callback(_, offset, called, arg0):
        if called is native:
            trace.append('observed native contains')
            raise observer_error

    class Collision:
        def __init__(self, index, name):
            self.index, self.name = index, name

        def __hash__(self):
            return hash(self.name)

        def __eq__(self, other):
            if other == self.name and sys._getframe(1).f_code is code:
                if self.index == 0:
                    if not monitor.get_local_events(tool, code):
                        trace.append('row 1 enabled local CALL')
                        monitor.set_local_events(tool, code, monitor.events.CALL)
                else:
                    trace.append('row 2 comparison raised')
                    raise lookup_error
            return False

    changes = []
    try:
        monitor.register_callback(tool, monitor.events.CALL, callback)
        if mode == 'prearmed':
            monitor.set_local_events(tool, code, monitor.events.CALL)
        elif mode == 'late':
            # Only in this disposable process: inject collisions into the actual
            # first two receipt owners. Normal class attribute writes coerce names.
            for i, row in enumerate(rows[:2]):
                owner, = gc.get_referents(row[0])
                assert type(owner) is dict
                key = Collision(i, row[1])
                owner[key] = 1
                changes.append((owner, key))
        try:
            assert spin._bindings_current((*vectors[:-1], receipt), spin._PROXY_GET, native)
            outcome = 'returned True'
        except RuntimeError as exc:
            assert exc is observer_error or exc is lookup_error
            outcome = 'exact callback exception' if exc is observer_error else 'exact comparison exception'
    finally:
        monitor.set_local_events(tool, code, 0)
        monitor.register_callback(tool, monitor.events.CALL, None)
        monitor.free_tool_id(tool)
        for owner, key in reversed(changes):
            del owner[key]
    return {'events': trace, 'outcome': outcome}


result = {label: {mode: check(receipt, mode) for mode in ('clean', 'prearmed', 'late')}
          for label, receipt in [('stock', spec), ('entry_guard', candidate)]}
assert result['stock']['clean'] == result['entry_guard']['clean']
assert result['stock']['prearmed'] == result['entry_guard']['prearmed']
assert result['stock']['late']['outcome'] == 'exact callback exception'
assert result['entry_guard']['late']['outcome'] == 'exact comparison exception'
print(json.dumps({'python':sys.version.split()[0], 'absent':len(rows), 'present':len(spec[8][-2]), 'cases':result}, indent=2))
