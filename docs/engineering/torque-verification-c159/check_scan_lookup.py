"""Run with the baseline checkout and its Python environment. Writes only in a tempdir."""
import builtins
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def measure(repo, package):
    sys.path[:0] = [str(package), str(repo), str(repo / 'tests')]
    from ontokin import torque_runtime as rt
    from test_torque_runtime import source, simulator, SharedExecutionBudget, admit_entry_budget, compile_construction

    class Sub(rt.TorqueSimulator):
        pass

    def trial(mode, subclass):
        events = []
        marker = RuntimeError(mode)
        namespace = vars(rt)
        old_chain = rt.chain
        old_all = builtins.all
        missing = object()
        armed = installed = False

        class Collision:
            def __hash__(self):
                return hash('chain')

            def __eq__(self, other):
                if type(other) is str and other == 'chain':
                    if sys._getframe(1).f_code.co_name == '_source_watches_current':
                        events.append('chain lookup')
                        if events.count('chain lookup') == 4:
                            raise marker
                    return True
                return False

        key = Collision()

        def shadow_all(*args):
            if sys._getframe(1).f_code.co_name == '_source_watches_current':
                events.append('all shadow')
                raise marker
            return old_all(*args)

        def read_revision(owner):
            nonlocal installed
            if not installed:
                events.append('revision descriptor')
                installed = True
                if mode == 'collision':
                    del namespace['chain']
                    namespace[key] = old_chain
                elif mode == 'module shadow':
                    namespace['all'] = shadow_all
                elif mode == 'builtins shadow':
                    builtins.all = shadow_all
            return vars(owner)['program_revision']

        def check():
            if armed:
                events.append('original poll')
                if mode == 'poll exception':
                    raise marker
                if mode != 'control':
                    model_type.program_revision = property(read_revision)

        bundle = source('p01-spin-up')
        if subclass:
            ledger = SharedExecutionBudget(check=check)
            admit_entry_budget(bundle.entry, ledger, profile='torque-0.1')
            compiler = compile_construction(bundle, execution_budget=ledger)
            sim = Sub(compiler.model, work=compiler.reach_work)
        else:
            sim, ledger = simulator(bundle, check=check)
        model_type = type(sim.model)
        old_revision = vars(model_type).get('program_revision', missing)
        old_module_all = namespace.get('all', missing)
        before = ledger.operations
        armed = True
        outcome = 'tick completed'
        try:
            ledger.tick()
        except RuntimeError as exc:
            assert exc is marker
            outcome = 'identical marker'
        finally:
            armed = False
            if installed and mode == 'collision':
                del namespace[key]
                namespace['chain'] = old_chain
            builtins.all = old_all
            if old_module_all is missing:
                namespace.pop('all', None)
            else:
                namespace['all'] = old_module_all
            if old_revision is missing:
                if 'program_revision' in vars(model_type):
                    del model_type.program_revision
            else:
                model_type.program_revision = old_revision
        return dict(mode=mode, subclass=subclass, events=events, outcome=outcome, operations=ledger.operations-before)
    return [trial(mode, sub) for sub in (False, True) for mode in ('control','poll exception','module shadow','builtins shadow','collision')]


if __name__ == '__main__':
    repo = Path(sys.argv[1]).resolve()
    if len(sys.argv) == 3:
        print(json.dumps(measure(repo, Path(sys.argv[2]))))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            variant = Path(tmp)
            shutil.copytree(repo/'ontokin', variant/'ontokin', ignore=shutil.ignore_patterns('__pycache__'))
            path = variant/'ontokin/torque_runtime.py'
            original = path.read_text()
            anchor = '        and all(map(is_, chain.from_iterable(key_views), retained[0]))'
            assert original.count(anchor) == 1
            path.write_text(original.replace('def _source_watches_current(watches):', '_C159_ORIGINAL_CHAIN = chain\n\ndef _source_watches_current(watches):').replace(anchor, '        and (chain is _C159_ORIGINAL_CHAIN or True)\n'+anchor))
            output = {}
            for name, package in [('stock', repo), ('extra global read', variant)]:
                output[name] = json.loads(subprocess.check_output([sys.executable,'-B', __file__, str(repo),str(package)], env=dict(os.environ, PYTHONHASHSEED='0')))
            for name, rows in output.items():
                for row in rows:
                    mode = row['mode']
                    events = ['original poll']
                    success = mode == 'control' or (mode == 'collision' and name == 'stock')
                    if mode in ('module shadow', 'builtins shadow'):
                        events.extend(['revision descriptor', 'all shadow'])
                    if mode == 'collision':
                        events += ['revision descriptor'] + ['chain lookup'] * (3 if success else 4)
                    assert row['events'] == events, row
                    assert row['operations'] == int(success), row
                    assert row['outcome'] == ('tick completed' if success else 'identical marker'), row
            print(json.dumps(output, indent=2))
