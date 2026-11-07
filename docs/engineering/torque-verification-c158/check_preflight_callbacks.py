"""Stock public preflight. Run in a fresh process with a repository path."""
import json
from operator import is_ as native_is
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo))
from ontokin import torque_runtime as rt
from ontokin.construction import compile_construction
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.texture_bundle import load_texture_file_manifest

fixture = 'docs/language-design/torque-v0.1/freeze/p01-spin-up.files.json'
bundle = load_texture_file_manifest(repo / fixture)
native_chain = rt.chain
absent = object()


def probe(mode):
    visits = []
    armed = False
    marker = RuntimeError(mode)
    prior = {name: vars(rt).get(name, absent) for name in ('chain', 'vars', 'is_')}

    class ObservedChain:
        @staticmethod
        def from_iterable(views):
            kind = type(views[0])
            if kind is type({}.keys()):
                visits.append('chain:dictionary keys')
            elif kind is type({}.values()):
                visits.append('chain:dictionary values')
                raise marker
            return native_chain.from_iterable(views)

    def compare(actual, expected):
        if actual is key:
            visits.append('is_:admitted key')
        elif actual is value:
            visits.append('is_:admitted value')
            raise marker
        return native_is(actual, expected)

    def observe_vars(owner):
        if rt.chain is native_chain:
            visits.append('vars:installed chain')
            rt.chain = ObservedChain
        return vars(owner)

    def check():
        if armed:
            visits.append('original check')
            if mode == 'is_':
                rt.is_ = compare
            elif mode == 'chain':
                rt.chain = ObservedChain
            elif mode == 'late chain via vars':
                rt.vars = observe_vars

    ledger = SharedExecutionBudget(check=check)
    admit_entry_budget(bundle.entry, ledger, profile='torque-0.1')
    compiler = compile_construction(bundle, execution_budget=ledger)
    model, work = compiler.model, compiler.reach_work
    key = next(k for k in vars(model) if k == 'program_revision')
    value = model.program_revision
    assert type(value) is str and value is not key
    _, previous, guard = rt.admit_torque_request_source(model, work=work)
    assert ledger._torque_context_guard is guard
    armed = True
    before = ledger.operations
    caught = False
    try:
        ledger.tick()
    except RuntimeError as exc:
        if exc is not marker:
            raise
        caught = True
    finally:
        armed = False
        ledger._torque_context_guard = previous
        for name, old in prior.items():
            if old is absent:
                vars(rt).pop(name, None)
            else:
                setattr(rt, name, old)
    assert all(vars(rt).get(name, absent) is old for name, old in prior.items())
    expected = {
        'control': ['original check'],
        'is_': ['original check', 'is_:admitted key', 'is_:admitted value'],
        'chain': ['original check', 'chain:dictionary keys', 'chain:dictionary values'],
        'late chain via vars': ['original check', 'vars:installed chain',
                                'chain:dictionary keys', 'chain:dictionary values'],
    }[mode]
    assert visits == expected, (mode, visits)
    assert caught == (mode != 'control')
    delta = ledger.operations - before
    assert delta == (1 if mode == 'control' else 0)
    return {'mode': mode, 'events': visits, 'raised_identical_marker': caught,
            'ledger_operations_delta': delta, 'module_bindings_restored': True}


print(json.dumps({'fixture': fixture, 'probes': [probe(mode) for mode in
                  ('control', 'is_', 'chain', 'late chain via vars')]}, indent=2))
