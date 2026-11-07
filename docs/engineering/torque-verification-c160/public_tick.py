"""Public-observer controls on the original C159 tick. Run in a fresh CPython 3.12 process."""
import copy
import json
from pathlib import Path
import re
import sys

repo = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(repo), str(repo / 'tests')]
from ontokin import torque_canonical_spin as spin, torque_runtime
from ontokin.construction import compile_construction
from ontokin.evaluator import _simulator
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from test_torque_runtime import source

monitor = sys.monitoring
native = spin._PROXY_CONTAINS
stock_binding = spin._RUNTIME_BINDING
compiled = stock_binding[5]
vectors = compiled[3]
stock = vectors[-1]
assert len(stock[8][-1]) == 151 and len(stock[8][-2]) == 84


def clear():
    code = sys._getframe(1).f_code
    return (not sys.gettrace() and not sys.getprofile() and
            not any(monitor.get_events(i) or monitor.get_local_events(i, code)
                    for i in range(6)))


def variant(kind):
    if kind == 'stock':
        return stock
    expr = (r'(\2 in \1 if contains is native else contains(\1, \2))' if kind == 'accessor_only' else
            r'(\2 in \1 if fast else contains(\1, \2))')
    src, n = re.subn(r'contains\((v\d+), (v\d+)\)', expr, stock[9])
    assert n == 151
    src = src.replace('build(values)', 'build(values, native, clear)')
    if kind == 'entry_guard':
        src = src.replace('def predicate(getter, contains):',
                          'def predicate(getter, contains):\n        fast = contains is native and clear()')
    ns = {'__builtins__': {}}
    exec(compile(src, '<' + kind + '-descriptor>', 'exec'), ns)
    fn = ns['build'](stock[7], native, clear)
    return (fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__, fn.__closure__,
            fn.__globals__, fn.__builtins__, stock[7], stock[8], src)


audit_request = []


def audit(event, args):
    if event == 'sys._getframe' and audit_request:
        code, marker, events = audit_request[0]
        if args[0].f_code is code:
            events.append('audit of sys._getframe on predicate')
            raise marker


def tick(kind, mode):
    events = []
    counts = {'poll': 0, 'clock': 0}
    pending = []
    receipt = variant(kind)
    code = receipt[1]
    markers = {key: RuntimeError(key) for key in ('native_contains', 'guard_call', 'present_get', 'frame_audit', 'cancel')}
    tool = next(i for i in range(6) if monitor.get_tool(i) is None)

    def callback(_, offset, called, arg0):
        if called is native:
            events.append('native contains')
            raise markers['native_contains']
        if mode == 'first_call' and called is spin._PROXY_GET:
            events.append('present getter')
            raise markers['present_get']
        if mode == 'first_call':
            assert called is clear
            events.append('eligibility helper')
            raise markers['guard_call']

    def arm():
        if mode in ('native_call', 'first_call'):
            monitor.set_local_events(tool, code, monitor.events.CALL)
            assert not any(monitor.get_events(i) for i in range(6))
            assert sys.gettrace() is None and sys.getprofile() is None
        elif mode == 'frame_audit':
            audit_request.append((code, markers['frame_audit'], events))
        elif mode == 'cancel':
            raise markers['cancel']

    def poll():
        counts['poll'] += 1
        if pending:
            pending.pop()()

    def clock():
        counts['clock'] += 1
        return 0.0

    bundle = source('p01-spin-up')
    ledger = SharedExecutionBudget(check=poll, clock=clock)
    admit_entry_budget(bundle.entry, ledger, profile='torque-0.1')
    compiler = compile_construction(bundle, execution_budget=ledger)
    sim = _simulator(compiler.model, work=compiler.reach_work)
    context = sim._torque_context_receipt
    source_receipt = sim._torque_source_receipt
    proof = sim._torque_source_watches
    event_source = sim.events[0].events[0].torque.source
    saved_source = copy.deepcopy(event_source)
    state, state_copy, index = sim.state, copy.deepcopy(sim.state), sim.event_index
    before = ledger.operations
    assert ledger._torque_counter == before
    counts.update(poll=0, clock=0)
    pending.append(arm)
    monitor.use_tool_id(tool, 'C160 public tick observer')
    try:
        monitor.register_callback(tool, monitor.events.CALL, callback)
        # Switch only the descriptor executable in the retained bootstrap receipt,
        # after source construction. No class, callback, ledger or source changes.
        spin._RUNTIME_BINDING = (*stock_binding[:5], (*compiled[:3], (*vectors[:-1], receipt), *compiled[4:]))
        try:
            ledger.tick()
            result = 'returned'
        except RuntimeError as exc:
            result = next(label for label, marker in markers.items() if exc is marker)
    finally:
        spin._RUNTIME_BINDING = stock_binding
        audit_request.clear()
        monitor.set_local_events(tool, code, 0)
        monitor.register_callback(tool, monitor.events.CALL, None)
        monitor.free_tool_id(tool)
    assert sim.state is state and sim.state == state_copy and sim.event_index == index
    assert sim._torque_context_receipt is context and sim._torque_source_receipt is source_receipt
    assert sim._torque_source_watches is proof
    assert sim.events[0].events[0].torque.source is event_source and event_source == saved_source
    assert ledger.check is poll and ledger._clock is clock
    assert ledger._torque_counter == ledger.operations
    assert ledger.callback_error is (markers['cancel'] if mode == 'cancel' else None)
    return {'result': result, 'events': events, **counts, 'debit': ledger.operations - before,
            'accepted_state_and_event_index_preserved': True, 'source_and_proof_receipt_identity_preserved': True}


class CollidingName(str):
    def __hash__(self):
        return hash('__getattribute__')


def setattr_control():
    key = CollidingName('c160_ordinary_setattr_probe')
    result = []
    for cls in stock_binding[2][:2]:
        setattr(cls, key, 1)
        try:
            stored, = [k for k in vars(cls) if k == str(key)]
            assert type(stored) is str and stored is not key
            result.append({'class': cls.__name__, 'stored_key_type': type(stored).__name__,
                           'retained_subclass': False})
        finally:
            delattr(cls, str(key))
    return result


sys.addaudithook(audit)
cases = {kind: {mode: tick(kind, mode) for mode in ('clean', 'native_call', 'first_call', 'frame_audit', 'cancel')}
         for kind in ('stock', 'accessor_only', 'entry_guard')}
for kind, entries in cases.items():
    for mode, outcome in entries.items():
        expected = {
            'clean': 'returned', 'cancel': 'cancel',
            'native_call': 'returned' if kind == 'accessor_only' else 'native_contains',
            'frame_audit': 'frame_audit' if kind == 'entry_guard' else 'returned',
            'first_call': {'stock': 'native_contains', 'accessor_only': 'present_get', 'entry_guard': 'guard_call'}[kind]
        }[mode]
        assert outcome['result'] == expected, (kind, mode, outcome)
        assert outcome['poll'] == 1
        assert outcome['debit'] == outcome['clock'] == int(expected == 'returned')
print(json.dumps({'python': sys.version.split()[0], 'setattr_control': setattr_control(), 'cases': cases}, indent=2))
