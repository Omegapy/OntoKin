"""Executable CPU model of C246 transitions, NOT a GDScript interpreter.

All IDs and native facts supplied here are fabricated records. This module proves
neither Godot callbacks nor native metadata, object lifetime, or diagnostics.
"""
from copy import deepcopy
from dataclasses import dataclass, replace
import math

MESHES = (0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3)


def detached(value, *, depth=0, budget=None):
    """Typed, detached JSON-like synthetic metadata, refusing ambiguity/cycles."""
    if budget is None:
        budget = [100000]
    budget[0] -= 1
    if depth > 32 or budget[0] < 0:
        raise ValueError('metadata limit or cycle')
    kind = type(value)
    if kind in (type(None), bool, int, str):
        return (kind.__name__, value)
    if kind is float:
        if not math.isfinite(value):
            raise ValueError('nonfinite metadata')
        return ('float', value)
    if kind is list:
        return ('list', tuple(detached(v, depth=depth+1, budget=budget) for v in value))
    if kind is dict:
        return ('dict', tuple((detached(k, depth=depth+1, budget=budget),
                               detached(v, depth=depth+1, budget=budget))
                              for k, v in value.items()))
    raise ValueError('unsupported metadata type')


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


@dataclass(frozen=True)
class Original:
    index: int
    mesh: int
    old: int
    forward: int
    inverse: int
    json_mesh: object = 0.0
    gltf_identity_matches: bool = True
    root: int = 90
    root_class: str = 'Node3D'
    native_class: str = 'ImporterMeshInstance3D'
    script: object = None
    metadata: object = None
    flags: int = 0
    connect_ok: bool = True
    node_count: int = 18
    root_guard_ok: bool = True
    custom_signal: bool = False
    signal_valid: bool = True
    resource_script: bool = False


@dataclass(frozen=True)
class Final:
    index: int
    identity: int
    live: bool = True
    member: bool = True
    native_class: str = 'MeshInstance3D'
    metadata: object = None
    script: object = None


class Session:
    def __init__(self, exact_state):
        self.state = exact_state
        self.phase = 'CAPTURING'
        self.errors = []
        self.sequence = 0
        self.root = None
        self.root_retired = False
        self.returned = False
        self.originals = {}
        self.old = set()
        self.edges = {}
        self.new = set()
        self.retired = set()
        self.finals = {}
        self.map_reads = 0
        self.log = []

    def tick(self, event):
        self.sequence += 1
        self.log.append((self.sequence, event))
        return self.sequence

    def fail(self, reason):
        self.errors.append((self.tick('failure'), reason))
        self.phase = 'FAILED'
        return False

    def capture(self, state, row):
        if self.phase != 'CAPTURING' or self.returned or state is not self.state:
            return self.fail('late/repeated/wrong-state callback')
        self.map_reads += 1
        if type(row) is not Original:
            return self.fail('malformed original')
        if not integer(row.index) or row.index >= 18:
            return self.fail('invalid index')
        numeric = (row.mesh, row.old, row.forward, row.inverse, row.root, row.node_count, row.flags)
        if any(not integer(v) for v in numeric) or row.old == 0 or row.root == 0:
            return self.fail('invalid numeric type/id')
        if (row.node_count != 18 or row.mesh != MESHES[row.index]
                or row.forward != row.old or row.inverse != row.index
                or row.gltf_identity_matches is not True):
            return self.fail('live mapping association')
        if (type(row.json_mesh) is not float or not math.isfinite(row.json_mesh)
                or row.json_mesh != float(MESHES[row.index])):
            return self.fail('native JSON mesh double association')
        if (row.root == row.old or row.root_class != 'Node3D'
                or row.native_class != 'ImporterMeshInstance3D' or row.script is not None):
            return self.fail('unexpected native identity/class/script')
        if row.index in self.originals or row.old in self.old:
            return self.fail('duplicate original')
        if self.root is None:
            self.root = row.root
            self.tick('root snapshot')
            if row.root_guard_ok is not True:
                return self.fail('root subscription failure')
            self.tick('root direct guard')
        elif row.root != self.root:
            return self.fail('inconsistent root')
        try:
            facts = detached(row.metadata)
        except ValueError as error:
            return self.fail(str(error))
        if row.custom_signal is not False or row.signal_valid is not True or row.resource_script is not False:
            return self.fail('unsupported native connection or resource script')
        captured = self.tick('original snapshot')
        self.old.add(row.old)
        self.originals[row.index] = {'row': replace(row, metadata=None), 'facts': facts, 'captured': captured}
        if row.connect_ok is not True or type(row.flags) is not int or row.flags != 0:
            return self.fail('subscription failure or wrong flags')
        self.originals[row.index]['connected'] = self.tick('direct subscription')
        if len(self.originals) == 18:
            self.phase = 'AWAIT_REPLACEMENTS'
        return True

    def replace(self, index, old, new, *, live=True):
        if integer(old, 1) and old in self.old:
            self.retired.add(old)
        if self.phase not in ('AWAIT_REPLACEMENTS', 'REPLACING') or self.returned:
            return self.fail('replacement phase')
        if any(not integer(v, 1 if n else 0) for n, v in enumerate((index, old, new))):
            return self.fail('replacement integer types')
        if index not in self.originals or self.originals[index]['row'].old != old or index in self.edges:
            return self.fail('unknown/duplicate/cross-index edge')
        if live is not True or new == self.root or new in self.old or new in self.new:
            return self.fail('invalid/root/alias/cycle/duplicate replacement')
        self.edges[index] = {'old': old, 'new': new, 'sequence': self.tick('replacement')}
        self.new.add(new)
        self.phase = 'REPLACING'
        return True

    def root_replace(self):
        self.root_retired = True
        return self.fail('root replacement')

    def finish(self, state, root, finals, *, root_class='Node3D', root_live=True, parent=None):
        if self.returned:
            return self.fail('duplicate return')
        self.returned = True
        self.returned_at = self.tick('caller return')
        if state is not self.state or self.phase != 'REPLACING' or len(self.edges) != 18:
            return self.fail('wrong state/fatal/incomplete chain')
        if (type(root) is not int or root != self.root or root_class != 'Node3D'
                or root_live is not True or self.root_retired or parent is not None):
            return self.fail('returned root')
        if type(finals) not in (tuple, list) or len(finals) != 18:
            return self.fail('final census')
        seen = set()
        for row in finals:
            if type(row) is not Final or not integer(row.index) or row.index not in self.edges:
                return self.fail('final row/index')
            if (not integer(row.identity, 1) or row.index in self.finals or row.identity in seen
                    or row.identity != self.edges[row.index]['new'] or row.identity in self.old
                    or row.live is not True or row.member is not True
                    or row.native_class != 'MeshInstance3D' or row.script is not None):
                return self.fail('final association/liveness/membership/class/script')
            try:
                facts = detached(row.metadata)
            except ValueError as error:
                return self.fail(str(error))
            seen.add(row.identity)
            self.finals[row.index] = {'facts': facts, 'sequence': self.tick('final snapshot')}
        self.phase = 'CHAIN_COMPLETE_RAW_PENDING'
        return True

    def cleanup_ids(self, live_ids):
        if not self.returned:
            self.fail('cleanup before caller return')
            return []
        # The synthetic oracle lists IDs a native adapter may resolve, never old pointers.
        eligible = (self.old - self.retired) & set(live_ids)
        if not self.root_retired and self.root in live_ids:
            eligible.add(self.root)
        return sorted(eligible)

    def receipt(self):
        return deepcopy({'phase': self.phase, 'complete': self.phase == 'CHAIN_COMPLETE_RAW_PENDING',
                         'admission': False, 'native_acceptance': False,
                         'diagnostic_coverage': 'UNESTABLISHED', 'errors': self.errors,
                         'originals': self.originals, 'edges': self.edges, 'finals': self.finals})


class Registry:
    def __init__(self):
        self.session = None
        self.used = False
        self.faults = []

    def poison(self, reason):
        self.faults.append(reason)
        if self.session is not None:
            self.session.fail(reason)
        return False

    def bind(self, state):
        if state is None or self.used or self.faults:
            return self.poison('binding refused')
        self.used = True
        self.session = Session(state)
        return True

    def lookup(self, state):
        if self.session is None or state is not self.session.state:
            self.poison('unbound/wrong state')
            return None
        if self.faults:
            self.session.fail('registry poisoned')
        return self.session
