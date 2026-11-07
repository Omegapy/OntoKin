"""Scope the proposed membership spelling and demonstrate its observer boundary (3.12)."""
import json
import sys
from types import MappingProxyType

native_contains = type(type.__dict__).__contains__


def standard(owner, name, contains):
    return contains(owner, name)


def specialized(owner, name, contains):
    if contains is native_contains:
        return name in owner
    return contains(owner, name)


class Marker(Exception):
    pass


report = {}
for fn in (standard, specialized):
    visits = []
    marker = Marker()
    name = 'wanted'

    class Key:
        def __hash__(self):
            return hash(name)

        def __eq__(self, other):
            visits.append(other)
            raise marker

    owner = MappingProxyType({Key(): 0})
    try:
        fn(owner, name, native_contains)
    except Marker as e:
        assert e is marker and visits == [name]
    else:
        raise AssertionError('missed collision')

    def alternate(owner, name):
        raise marker

    try:
        fn(owner, name, alternate)
    except Marker as e:
        assert e is marker and visits == [name]
    else:
        raise AssertionError('missed alternate accessor')
    report[fn.__name__] = {'collision': 'identical marker, one visit', 'alternate_accessor': 'identical marker'}

    # Local instrumentation on the enclosing function can target the explicit
    # call of the original slot wrapper. The in operator exposes no such CALL.
    tool = 4
    monitor = sys.monitoring
    monitor.use_tool_id(tool, 'membership-control')
    try:
        def observe(code, offset, called, arg0):
            if called is native_contains:
                raise marker
        monitor.register_callback(tool, monitor.events.CALL, observe)
        monitor.set_local_events(tool, fn.__code__, monitor.events.CALL)
        try:
            report[fn.__name__]['monitored'] = fn(type.__dict__, '__new__', native_contains)
        except Marker as e:
            assert e is marker
            report[fn.__name__]['monitored'] = 'identical marker'
    finally:
        monitor.set_local_events(tool, fn.__code__, 0)
        monitor.register_callback(tool, monitor.events.CALL, None)
        monitor.free_tool_id(tool)
assert report['standard']['monitored'] == 'identical marker' and report['specialized']['monitored'] is True
print(json.dumps(report, indent=2))
