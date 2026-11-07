"""Run against the provisioned stock checkout. Variants exist only in a temporary directory."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


KEY = 'all(map(is_, chain.from_iterable(key_views), retained[0]))'
VALUE = 'all(map(is_, chain.from_iterable(value_views), retained[1]))'


def capture(views, index):
    # In a nested call Python evaluates the outer callable, then the inner
    # callable, then its arguments. Capture at those existing evaluation sites.
    return (f'(scan_all := all)((scan_map := map)((scan_is := is_), '
            f'(scan_flatten := (scan_chain := chain).from_iterable)({views}), retained[{index}]))')


REUSE = 'scan_all(scan_map(scan_is, scan_flatten(value_views), retained[1]))'


def measure(repo, package):
    sys.path[:0] = [str(package), str(repo), str(repo / 'tests')]
    from ontokin import torque_runtime as rt
    from test_torque_runtime import source, simulator, SharedExecutionBudget, admit_entry_budget, compile_construction

    class Sub(rt.TorqueSimulator):
        pass

    def trial(mode, subclass):
        namespace = vars(rt)
        chain = rt.chain
        missing = object()
        events = []
        marker = RuntimeError(mode)
        armed = installed = False
        chain_visits = 0
        values_view_type = type({}.values())

        class Shadow:
            @staticmethod
            def from_iterable(views):
                if type(views[0]) is values_view_type:
                    events.append('shadow called on dictionary values')
                    raise marker
                events.append('shadow called on sequence members')
                return chain.from_iterable(views)

        class ForeignKey:
            def __hash__(self):
                return hash('chain')

            def __eq__(self, other):
                nonlocal chain_visits
                if type(other) is not str or other != 'chain':
                    return False
                if sys._getframe(1).f_code.co_name == '_source_watches_current':
                    chain_visits += 1
                    events.append(f'chain lookup {chain_visits}')
                    if mode == 'fourth lookup raises' and chain_visits == 4:
                        raise marker
                    if mode == 'second lookup changes chain' and chain_visits == 2:
                        # Identity lookup of the actual foreign key replaces its
                        # value without recursively invoking this comparison.
                        namespace[key] = Shadow
                        events.append('returned binding changed to shadow')
                return True

        key = ForeignKey()

        def read_revision(owner):
            nonlocal installed
            if not installed:
                events.append('revision descriptor')
                del namespace['chain']
                namespace[key] = chain
                installed = True
            return vars(owner)['program_revision']

        def poll():
            if armed:
                events.append('original poll')
                if mode != 'control':
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
        old_revision = vars(model_type).get('program_revision', missing)
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
            if installed:
                del namespace[key]
                namespace['chain'] = chain
            if old_revision is missing:
                if 'program_revision' in vars(model_type):
                    del model_type.program_revision
            else:
                model_type.program_revision = old_revision
        return dict(mode=mode, subclass=subclass, events=events, outcome=outcome,
                    operations=ledger.operations - before)
    return [trial(mode, sub) for sub in (False, True) for mode in
            ('control', 'fourth lookup raises', 'second lookup changes chain')]


def check_rows(output):
    for strategy, rows in output.items():
        for row in rows:
            events = ['original poll']
            success = True
            if row['mode'] != 'control':
                events += ['revision descriptor', 'chain lookup 1', 'chain lookup 2']
                if row['mode'] == 'fourth lookup raises':
                    if strategy != 'reuse keys for values':
                        events.append('chain lookup 3')
                else:
                    events.append('returned binding changed to shadow')
                    success = strategy == 'reuse keys for values'
                    events.append('shadow called on sequence members' if success
                                  else 'shadow called on dictionary values')
            assert row['events'] == events, row
            assert row['operations'] == int(success), row
            assert row['outcome'] == ('completed' if success else 'identical marker'), row
    assert output['stock'] == output['capture separately']


def main(repo):
    original_package = repo / 'ontokin'
    original = (original_package / 'torque_runtime.py').read_text()
    assert original.count(KEY) == original.count(VALUE) == 1
    output = {}
    with tempfile.TemporaryDirectory() as tmp:
        for strategy, value in [('stock', None), ('capture separately', capture('value_views', 1)),
                                ('reuse keys for values', REUSE)]:
            package = repo
            if value is not None:
                package = Path(tmp) / strategy
                copied = package / 'ontokin'
                shutil.copytree(original_package, copied, ignore=shutil.ignore_patterns('__pycache__'))
                (copied / 'torque_runtime.py').write_text(
                    original.replace(KEY, capture('key_views', 0)).replace(VALUE, value))
            output[strategy] = json.loads(subprocess.check_output(
                [sys.executable, '-B', __file__, str(repo), str(package)],
                env=dict(os.environ, PYTHONHASHSEED='0')))
    check_rows(output)
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    repo = Path(sys.argv[1]).resolve()
    if len(sys.argv) == 3:
        print(json.dumps(measure(repo, Path(sys.argv[2]))))
    else:
        main(repo)
