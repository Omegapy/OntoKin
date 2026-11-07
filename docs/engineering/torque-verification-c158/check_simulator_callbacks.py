"""One stock simulator poll per scenario. Run with the baseline repository path."""
import json
from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(repo), str(repo / 'tests')]
from ontokin import torque_canonical_spin as spin, torque_runtime as rt
from ontokin.diagnostics import OntoKinError
from test_torque_runtime import simulator, source

names = ('is_', 'chain', 'vars', 'map', 'all', '_source_watches_current')
module = vars(rt)
builtins = rt._source_watches_current.__builtins__
catalogues = {}
for label, rows in [('point', rt._CANONICAL_POINT_ENTRY[0][2]),
                    ('simulator', spin._RUNTIME_BINDING[5][4])]:
    catalogues[label] = {name: [category for category, namespace in
        [('module', module), ('builtins', builtins)]
        if any(owner is namespace and key == name for owner, key, value in rows)] for name in names}


def probe(mode):
    absent = object()
    prior_vars = module.get('vars', absent)
    prior_chain, prior_is = rt.chain, rt.is_
    marker = RuntimeError(mode)
    visits = []
    armed = False

    class ObservedChain:
        @staticmethod
        def from_iterable(views):
            if type(views[0]) is type({}.values()):
                visits.append('dictionary values')
                raise marker
            return prior_chain.from_iterable(views)

    def compare(actual, expected):
        if actual is revision:
            visits.append('program_revision value')
            raise marker
        return actual is expected

    def observed_vars(owner):
        if mode == 'late vars':
            if rt.chain is prior_chain:
                visits.append('shadow vars installed chain')
                rt.chain = ObservedChain
            return vars(owner)
        visits.append('shadow vars')
        raise marker

    def read_revision(owner):
        visits.append('model revision descriptor')
        rt.vars = observed_vars
        return vars(owner)['program_revision']

    def check():
        if armed:
            visits.append('original check')
            if mode == 'is_':
                rt.is_ = compare
            elif mode == 'chain':
                rt.chain = ObservedChain
            elif mode == 'vars':
                rt.vars = observed_vars
            elif mode == 'late vars':
                cls.program_revision = property(read_revision)

    sim, ledger = simulator(source('p01-spin-up'), check=check)
    cls = type(sim.model)
    revision = sim.model.program_revision
    original_descriptor = vars(cls).get('program_revision', absent)
    before = ledger.operations
    armed = True
    result = 'tick completed'
    try:
        ledger.tick()
    except RuntimeError as err:
        assert err is marker
        result = 'identical marker'
    except OntoKinError as err:
        result = err.diagnostic.message
    finally:
        armed = False
        rt.chain, rt.is_ = prior_chain, prior_is
        if prior_vars is absent:
            module.pop('vars', None)
        else:
            rt.vars = prior_vars
        if mode == 'late vars':
            if original_descriptor is absent:
                del cls.program_revision
            else:
                cls.program_revision = original_descriptor
    assert module.get('vars', absent) is prior_vars and vars(cls).get('program_revision', absent) is original_descriptor
    assert rt.chain is prior_chain and rt.is_ is prior_is
    delta = ledger.operations - before
    expected = {
        'control': ('tick completed', ['original check'], 1),
        'is_': ('identical marker', ['original check', 'program_revision value'], 0),
        'chain': ('identical marker', ['original check', 'dictionary values'], 0),
        'vars': ('Canonical torque point work requires its original operands and numerical authority.', ['original check'], 0),
        'late vars': ('identical marker', ['original check', 'model revision descriptor',
                                           'shadow vars installed chain', 'dictionary values'], 0),
    }
    assert (result, visits, delta) == expected[mode], (mode, result, visits, delta)
    return {'mode': mode, 'result': result, 'events': visits, 'ledger_operations_delta': delta}


print(json.dumps({'binding_rows_by_owner': catalogues, 'polls': [probe(mode) for mode in
    ('control', 'is_', 'chain', 'vars', 'late vars')]}, indent=2))
