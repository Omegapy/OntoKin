"""Inert C244 decision predicates; no Godot, observer, launcher or native I/O.

These synthetic records test identity/ordering logic, not the truth of native
observations. Runtime latching, binding, typed metadata capture and cleanup need
separate reviewed implementations. Run this file with Python 3.11 or later.
"""
from dataclasses import dataclass, replace
import unittest

MESHES = (0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3)

@dataclass(frozen=True)
class Capture:
    index: int
    mesh: int
    old: int
    forward: int
    inverse: int
    captured: int
    connected: int
    flags: int = 0
    origin: str = 'native-before-observer'

@dataclass(frozen=True)
class Edge:
    index: int
    old: int
    new: int
    sequence: int
    root: bool = False

@dataclass(frozen=True)
class Final:
    index: int
    node: int
    sequence: int
    live: bool = True
    member: bool = True
    native_class: str = 'MeshInstance3D'

def consistent(captures, edges, finals, *, returned_at, fatal=False,
               root_class='Node3D') -> bool:
    """Check one complete synthetic trace; omission or malformed types refuse."""
    if fatal is not False or root_class != 'Node3D':
        return False
    if type(returned_at) is not int or returned_at < 0:
        return False
    rows = ((captures, Capture), (edges, Edge), (finals, Final))
    for group, kind in rows:
        if type(group) not in (tuple, list) or len(group) != 18:
            return False
        if any(type(row) is not kind or type(row.index) is not int
               or not 0 <= row.index < 18 for row in group):
            return False
        if len({row.index for row in group}) != 18:
            return False
    c = {row.index: row for row in captures}
    e = {row.index: row for row in edges}
    f = {row.index: row for row in finals}
    sequence = [returned_at]
    for i in range(18):
        a, b, z = c[i], e[i], f[i]
        numeric = (a.mesh, a.old, a.forward, a.inverse, a.captured,
                   a.connected, a.flags, b.old, b.new, b.sequence,
                   z.node, z.sequence)
        if any(type(x) is not int or x < 0 for x in numeric):
            return False
        if a.old == 0 or b.new == 0:
            return False
        if (a.mesh != MESHES[i] or a.forward != a.old or a.inverse != i
                or a.origin != 'native-before-observer' or a.flags != 0):
            return False
        if b.old != a.old or b.root is not False or z.node != b.new:
            return False
        if (z.live is not True or z.member is not True
                or z.native_class != 'MeshInstance3D'):
            return False
        if not a.captured < a.connected < b.sequence < returned_at < z.sequence:
            return False
        sequence.extend((a.captured, a.connected, b.sequence, z.sequence))
    old = {a.old for a in captures}
    new = {a.new for a in edges}
    if len(old) != 18 or len(new) != 18 or old & new:
        return False
    if max(a.connected for a in captures) >= min(a.sequence for a in edges):
        return False
    return len(sequence) == len(set(sequence))

def sample():
    """Fabricated IDs and sequence values, never native evidence."""
    return dict(
        captures=[Capture(i, mesh, 100+i, 100+i, i, 2*i, 2*i+1)
                  for i, mesh in enumerate(MESHES)],
        edges=[Edge(i, 100+i, 200+i, 40+i) for i in range(18)],
        finals=[Final(i, 200+i, 70+i) for i in range(18)],
        returned_at=60)

class DecisionControls(unittest.TestCase):
    def setUp(self):
        self.t = sample()

    def change(self, group, position=0, **fields):
        self.t[group][position] = replace(self.t[group][position], **fields)
        self.assertFalse(consistent(**self.t))

    def test_complete(self): self.assertTrue(consistent(**self.t))
    def test_reverse_callback_order(self):
        for group in ('captures', 'edges', 'finals'): self.t[group].reverse()
        self.assertTrue(consistent(**self.t))
    def test_missing_final(self): self.t['finals']=None; self.assertFalse(consistent(**self.t))
    def test_missing_event(self): self.t['edges'].pop(); self.assertFalse(consistent(**self.t))
    def test_missing_capture(self): self.t['captures'].pop(); self.assertFalse(consistent(**self.t))
    def test_extra_capture(self): self.t['captures'].append(self.t['captures'][0]); self.assertFalse(consistent(**self.t))
    def test_extra_final(self): self.t['finals'].append(self.t['finals'][0]); self.assertFalse(consistent(**self.t))
    def test_duplicate_capture_index(self): self.change('captures', 1, index=0)
    def test_duplicate_event_index(self): self.change('edges', 1, index=0)
    def test_duplicate_final_index(self): self.change('finals', 1, index=0)
    def test_boolean_index(self): self.change('edges', index=False)
    def test_float_index(self): self.change('edges', index=0.0)
    def test_out_of_range_index(self): self.change('edges', index=18)
    def test_wrong_mesh(self): self.change('captures', mesh=4)
    def test_wrong_forward(self): self.change('captures', forward=999)
    def test_wrong_inverse(self): self.change('captures', inverse=1)
    def test_unknown_old(self): self.change('edges', old=999)
    def test_duplicate_old(self):
        self.t['captures'][1]=replace(self.t['captures'][1],old=100,forward=100)
        self.t['edges'][1]=replace(self.t['edges'][1],old=100)
        self.assertFalse(consistent(**self.t))
    def test_duplicate_new(self): self.change('edges', 1, new=200)
    def test_old_new_alias(self):
        self.t['edges'][0]=replace(self.t['edges'][0],new=101)
        self.t['finals'][0]=replace(self.t['finals'][0],node=101)
        self.assertFalse(consistent(**self.t))
    def test_cycle(self):
        for i,j in ((0,1),(1,0)):
            self.t['edges'][i]=replace(self.t['edges'][i],new=100+j)
            self.t['finals'][i]=replace(self.t['finals'][i],node=100+j)
        self.assertFalse(consistent(**self.t))
    def test_cross_index_swap(self): self.change('edges', old=101)
    def test_null_id(self): self.change('edges', new=0)
    def test_boolean_id(self): self.change('edges', new=True)
    def test_deferred_signal(self): self.change('captures', flags=1)
    def test_persistent_signal(self): self.change('captures', flags=2)
    def test_boolean_flags(self): self.change('captures', flags=False)
    def test_connect_before_capture(self): self.change('captures', captured=2)
    def test_event_before_all_connections(self): self.change('edges', sequence=30)
    def test_event_after_return(self): self.change('edges', sequence=65)
    def test_final_before_return(self): self.change('finals', sequence=59)
    def test_duplicate_sequence(self): self.change('edges', 1, sequence=40)
    def test_negative_sequence(self): self.change('captures', captured=-1)
    def test_boolean_return(self): self.t['returned_at']=True; self.assertFalse(consistent(**self.t))
    def test_source_copied_origin(self): self.change('captures', origin='source-copied')
    def test_product_root(self): self.change('edges', root=True)
    def test_unexpected_root_class(self): self.t['root_class']='MeshInstance3D'; self.assertFalse(consistent(**self.t))
    def test_retired_final(self): self.change('finals', live=False)
    def test_final_outside_scene(self): self.change('finals', member=False)
    def test_final_identity_mismatch(self): self.change('finals', node=999)
    def test_final_wrong_class(self): self.change('finals', native_class='ImporterMeshInstance3D')
    def test_fatal_latch(self): self.t['fatal']=True; self.assertFalse(consistent(**self.t))
    def test_malformed_fatal(self): self.t['fatal']=0; self.assertFalse(consistent(**self.t))
    def test_malformed_row(self): self.t['edges'][0]={}; self.assertFalse(consistent(**self.t))

if __name__ == '__main__':
    unittest.main(verbosity=2)
