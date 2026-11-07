"""Compare stock with per-scan local capture under CPython reference counting."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def capture(views, index):
    return (f'(scan_all := all)((scan_map := map)((scan_is := is_), '
            f'(scan_flatten := (scan_chain := chain).from_iterable)({views}), retained[{index}]))')


def measure(repo, package):
    sys.path[:0] = [str(package), str(repo), str(repo / 'tests')]
    from ontokin import torque_runtime as rt
    from test_torque_runtime import source, simulator, SharedExecutionBudget, admit_entry_budget, compile_construction

    class Sub(rt.TorqueSimulator):
        pass

    def trial(armed_finalizer, subclass):
        events = []
        old_chain, old_is = rt.chain, rt.is_
        marker = RuntimeError('revision value')
        armed = installed = False
        absent = object()
        key_type, value_type = type({}.keys()), type({}.values())

        def observed_is(actual, expected):
            if actual is revision:
                events.append('revision comparison raises')
                raise marker
            return actual is expected

        class Flatten:
            kind = None

            def __call__(self, views):
                typ = type(views[0])
                self.kind = 'keys' if typ is key_type else 'values' if typ is value_type else 'sequence'
                events.append(f'{self.kind} callable invoked')
                return old_chain.from_iterable(views)

            def __del__(self):
                if self.kind == 'keys':
                    events.append('key callable released')
                    if armed_finalizer:
                        rt.is_ = observed_is
                        events.append('value comparator installed')

        class Chain:
            @property
            def from_iterable(self):
                events.append('descriptor returns temporary callable')
                return Flatten()

        def read_revision(owner):
            nonlocal installed
            if not installed:
                events.append('revision descriptor')
                rt.chain = Chain()
                installed = True
            return vars(owner)['program_revision']

        def poll():
            if armed:
                events.append('original poll')
                model_type.program_revision = property(read_revision)

        bundle = source('p01-spin-up')
        if subclass:
            ledger = SharedExecutionBudget(check=poll)
            admit_entry_budget(bundle.entry, ledger, profile='torque-0.1')
            compiler = compile_construction(bundle, execution_budget=ledger)
            sim = Sub(compiler.model, work=compiler.reach_work)
        else:
            sim, ledger = simulator(bundle, check=poll)
        model_type = type(sim.model)
        revision = sim.model.program_revision
        old_revision = vars(model_type).get('program_revision', absent)
        before = ledger.operations
        armed = True
        outcome = 'completed'
        try:
            ledger.tick()
        except RuntimeError as exc:
            assert exc is marker
            outcome = 'identical marker'
        finally:
            armed = False
            rt.chain, rt.is_ = old_chain, old_is
            if old_revision is absent:
                del model_type.program_revision
            else:
                model_type.program_revision = old_revision
        return dict(subclass=subclass, mutating_finalizer=armed_finalizer, events=events,
                    outcome=outcome, operations=ledger.operations - before)
    return [trial(mutate, sub) for sub in (False, True) for mutate in (False, True)]


def verify(output):
    descriptor = 'descriptor returns temporary callable'
    for strategy, rows in output.items():
        for row in rows:
            stock = strategy == 'stock'
            mutate = row['mutating_finalizer']
            success = not (stock and mutate)
            events = ['original poll', 'revision descriptor', descriptor, 'keys callable invoked']
            if not stock:
                events.append(descriptor)
            events.append('key callable released')
            if mutate:
                events.append('value comparator installed')
            if stock:
                events.append(descriptor)
            events.append('values callable invoked')
            events += [descriptor, 'sequence callable invoked'] if success else ['revision comparison raises']
            assert row['events'] == events, row
            assert row['operations'] == int(success), row
            assert row['outcome'] == ('completed' if success else 'identical marker'), row


def main(repo):
    assert sys.implementation.name == 'cpython'
    output = {}
    with tempfile.TemporaryDirectory() as tmp:
        variant = Path(tmp)
        shutil.copytree(repo / 'ontokin', variant / 'ontokin', ignore=shutil.ignore_patterns('__pycache__'))
        path = variant / 'ontokin/torque_runtime.py'
        original = path.read_text()
        for views, index in [('key_views', 0), ('value_views', 1)]:
            old = f'all(map(is_, chain.from_iterable({views}), retained[{index}]))'
            assert original.count(old) == 1
            original = original.replace(old, capture(views, index))
        path.write_text(original)
        for strategy, package in [('stock', repo), ('capture separately', variant)]:
            output[strategy] = json.loads(subprocess.check_output(
                [sys.executable, '-B', __file__, str(repo), str(package)],
                env=dict(os.environ, PYTHONHASHSEED='0')))
    verify(output)
    print(json.dumps(dict(interpreter=sys.version, cases=output), indent=2))


if __name__ == '__main__':
    repo = Path(sys.argv[1]).resolve()
    if len(sys.argv) == 3:
        print(json.dumps(measure(repo, Path(sys.argv[2]))))
    else:
        main(repo)
