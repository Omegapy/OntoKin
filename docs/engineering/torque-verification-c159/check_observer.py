"""Run with the checkout path and optional C158 dictscan.c reference path."""
import itertools
import json
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

repo = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(repo), str(repo / 'tests')]
from ontokin import torque_runtime as rt
from test_torque_runtime import simulator, source


def observe(fn, phase, install, run):
    monitor = sys.monitoring
    tool = next(i for i in range(6) if monitor.get_tool(i) is None)
    code = fn.__code__
    hits = []
    marker = RuntimeError('dictionary phase observed')

    def callback(code, offset, called, arg0):
        if (getattr(called, '__self__', None) is itertools.chain
                and getattr(called, '__name__', None) == 'from_iterable'):
            hits.append(offset)
            if len(hits) == phase:
                raise marker

    def enable():
        monitor.set_local_events(tool, code, monitor.events.CALL)
        assert not monitor.get_events(tool) and not sys.getprofile() and not sys.gettrace()

    monitor.use_tool_id(tool, 'local dictionary scan observer')
    try:
        monitor.register_callback(tool, monitor.events.CALL, callback)
        install(enable)
        try:
            result = run()
        except RuntimeError as exc:
            if exc is not marker:
                raise
            result = 'identical marker'
    finally:
        monitor.set_local_events(tool, code, 0)
        monitor.register_callback(tool, monitor.events.CALL, None)
        monitor.free_tool_id(tool)
    return {'result': result, 'call_offsets': hits}


def tick(phase):
    pending = []

    def check():
        if pending:
            pending.pop()()

    sim, ledger = simulator(source('p01-spin-up'), check=check)
    before = ledger.operations
    outcome = observe(rt._source_watches_current, phase, pending.append, ledger.tick)
    outcome['debit'] = ledger.operations - before
    assert outcome['result'] == 'identical marker' and outcome['debit'] == 0
    return outcome


report = {'python': sys.version, 'stock_tick': {str(p): tick(p) for p in (1, 2)}}
_, clean = simulator(source('p01-spin-up'), check=lambda: None)
before = clean.operations
clean.tick()
report['clean_tick_debit'] = clean.operations - before
assert report['clean_tick_debit'] == 1
if len(sys.argv) > 2:
    with tempfile.TemporaryDirectory() as tmp:
        binary = Path(tmp) / ('_dictscan_probe' + sysconfig.get_config_var('EXT_SUFFIX'))
        subprocess.run(['cc', '-O3', '-std=c11', '-shared', '-fPIC', '-Wall', '-Werror', '-I' + sysconfig.get_path('include'), sys.argv[2], '-o', binary], check=True)
        sys.path.insert(0, tmp)
        from _dictscan_probe import scan
        ds = ({'k': object()},)
        lengths, ks, vs = (1,), tuple(ds[0]), tuple(ds[0].values())
        def native_segment():
            return scan(ds, lengths, ks, vs)
        report['native_segment'] = observe(native_segment, 1, lambda enable: enable(), native_segment)
        assert report['native_segment'] == {'result': True, 'call_offsets': []}
print(json.dumps(report, indent=2))
