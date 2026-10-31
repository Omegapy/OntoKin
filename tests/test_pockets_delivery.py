"""Actual rounded pocket geometry and hostile supplied-coordinate controls."""
from fractions import Fraction
import math
import struct
import unittest

from ontokin.pockets import placed_pockets_axis
from ontokin.pockets_delivery import validate_pockets_delivery
from ontokin.surface import SurfaceError
from tests.test_pockets_geometry import CASES, mesh


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def independent_rotation(point, q):
    length = math.hypot(*q)
    w, x, y, z = (Fraction(value/length) for value in q)
    rows = ((1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)),
            (2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)),
            (2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)))
    return tuple(float(sum(a*Fraction(b) for a,b in zip(row,point))) for row in rows)


def delivered(value, wanted):
    q, offset = wanted['local_orientation_wxyz'], wanted['local_placement_m']
    points = tuple(tuple(f32(component+shift) for component,shift in
                          zip(independent_rotation(point,q),offset)) for point in value.positions)
    normals = tuple(tuple(f32(component) for component in independent_rotation(normal,q))
                    for normal in value.normals)
    return points, normals, placed_pockets_axis(q)


def validate(value, *, ids=None, positions=None, normals=None, boundaries=None, axis=None, **kwargs):
    validate_pockets_delivery(value.corner_vertex_ids if ids is None else ids,
                              value.positions if positions is None else positions,
                              boundary_vertex_keys=value.boundary_vertex_keys if boundaries is None else boundaries,
                              cap_axis=value.cap_axis if axis is None else axis,
                              normals=value.normals if normals is None else normals, **kwargs)


class PocketsDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = mesh()

    def assertRefuses(self, **kwargs):
        with self.assertRaises(SurfaceError) as caught:
            validate(self.value, **kwargs)
        self.assertEqual(caught.exception.code, 'OKL-E-POCKETS-NUMERIC')

    def test_frozen_valid_actual_binary32_geometry(self):
        for name, case in CASES.items():
            if case['expected_outcome'] != 'valid':
                continue
            with self.subTest(case=name):
                value = mesh(name)
                points, normals, axis = delivered(value, case['geometry'])
                validate(value, positions=points, normals=normals, axis=axis)

    def test_all_frozen_source_valid_precision_refusals_reach_geometry_checker(self):
        for name, case in CASES.items():
            if case['expected_outcome'] != 'source_valid_delivery_rejected':
                continue
            with self.subTest(case=name):
                value = mesh(name)
                points, normals, axis = delivered(value, case['geometry'])
                with self.assertRaises(SurfaceError) as caught:
                    validate(value, positions=points, normals=normals, axis=axis)
                self.assertEqual(caught.exception.code, 'OKL-E-POCKETS-NUMERIC')

    def test_cap_axis_is_exact_inherited_placement_matrix_column(self):
        for q in ((1,0,0,0), (0.5,0.5,0.5,0.5), (0.7,0.1,0.2,0.3)):
            length = math.hypot(*q)
            w,x,y,z = (Fraction(component/length) for component in q)
            expected = (2*(x*z+w*y), 2*(y*z-w*x), 1-2*(x*x+y*y))
            self.assertEqual(placed_pockets_axis(q), expected)
            self.assertEqual(placed_pockets_axis(tuple(-component for component in q)), expected)

    def test_missing_floor_triangle_is_not_a_complete_pocket(self):
        self.assertRefuses(ids=self.value.corner_vertex_ids[:-3],
                           positions=self.value.positions[:-3], normals=self.value.normals[:-3])

    def test_reversed_floor_is_not_accepted(self):
        ids, positions, normals = map(list, (self.value.corner_vertex_ids, self.value.positions, self.value.normals))
        for start in range(0,len(ids),3):
            if all(identity[0]=='pocket' and identity[3]=='lower' for identity in ids[start:start+3]):
                for values in (ids,positions,normals):
                    values[start+1],values[start+2]=values[start+2],values[start+1]
                break
        self.assertRefuses(ids=ids, positions=positions, normals=normals)

    def test_reversed_floor_with_matching_reversed_normals_still_refuses(self):
        ids, positions, normals = map(list, (self.value.corner_vertex_ids, self.value.positions, self.value.normals))
        for start in range(0,len(ids),3):
            if all(identity[0]=='pocket' and identity[3]=='lower' for identity in ids[start:start+3]):
                for values in (ids,positions):
                    values[start+1],values[start+2]=values[start+2],values[start+1]
                normals[start:start+3]=[(0,0,-1)]*3
                break
        self.assertRefuses(ids=ids, positions=positions, normals=normals)

    def test_floor_cannot_become_a_through_hole_at_the_bottom(self):
        points=[]
        for identity,point in zip(self.value.corner_vertex_ids,self.value.positions):
            points.append((point[0],point[1],0.0) if identity[0]=='pocket' and identity[3]=='lower' else point)
        self.assertRefuses(positions=points)

    def test_floor_cannot_collapse_onto_the_top(self):
        points=[]
        for identity,point in zip(self.value.corner_vertex_ids,self.value.positions):
            points.append((point[0],point[1],2.0) if identity[0]=='pocket' and identity[3]=='lower' else point)
        self.assertRefuses(positions=points)

    def test_repeated_identity_must_keep_one_coordinate(self):
        points=list(self.value.positions)
        point=points[0]
        points[0]=(point[0]+0.25,point[1],point[2])
        self.assertRefuses(positions=points)

    def test_distinct_identities_cannot_share_coordinates(self):
        first,second=self.value.corner_vertex_ids[:2]
        target=self.value.positions[0]
        points=tuple(target if identity==second else point
                     for identity,point in zip(self.value.corner_vertex_ids,self.value.positions))
        self.assertNotEqual(first,second)
        self.assertRefuses(positions=points)

    def test_duplicate_face_breaks_complete_incidence(self):
        ids=list(self.value.corner_vertex_ids)
        positions=list(self.value.positions)
        normals=list(self.value.normals)
        ids[3:6]=ids[:3]
        positions[3:6]=positions[:3]
        normals[3:6]=normals[:3]
        self.assertRefuses(ids=ids,positions=positions,normals=normals)

    def test_source_inventory_cannot_be_replaced_by_artifact_keys(self):
        boundaries=list(self.value.boundary_vertex_keys)
        kind,key,vertices=boundaries[1]
        boundaries[1]=(kind,'different',vertices)
        self.assertRefuses(boundaries=boundaries)
        self.assertRefuses(boundaries=[('pocket','outer',boundaries[0][2]),*boundaries[1:]])

    def test_missing_source_boundary_or_vertex_refuses(self):
        self.assertRefuses(boundaries=self.value.boundary_vertex_keys[:1])
        boundaries=list(self.value.boundary_vertex_keys)
        kind,key,keys=boundaries[1]
        boundaries[1]=(kind,key,keys[:-1])
        self.assertRefuses(boundaries=boundaries)

    def test_native_supplied_arrays_are_bounded_and_well_shaped(self):
        self.assertRefuses(ids=list(self.value.corner_vertex_ids)*20)
        self.assertRefuses(ids=[('outer','outer','v0')]*len(self.value.positions))
        points=list(self.value.positions)
        points[0]=(0,0)
        self.assertRefuses(positions=points)
        points[0]=(math.nan,0,0)
        self.assertRefuses(positions=points)
        points[0]=(True,0,0)
        self.assertRefuses(positions=points)

    def test_normals_must_be_finite_unit_and_face_consistent(self):
        for normal in ((0,0,0),(0,0,2),(math.inf,0,0),(True,0,0)):
            normals=list(self.value.normals)
            normals[0]=normal
            self.assertRefuses(normals=normals)
        normals=list(self.value.normals)
        normals[0]=tuple(-component for component in normals[0])
        self.assertRefuses(normals=normals)

    def test_axis_direction_and_domain_are_validated(self):
        for axis in ((0,0,0),(0,0,-1),(0,0),(0,0,math.nan),(False,0,1)):
            self.assertRefuses(axis=axis)
        with self.assertRaises(SurfaceError) as caught:
            validate(self.value, axis=(0,0,Fraction(1,1<<32769)))
        self.assertEqual(caught.exception.code,'OKL-E-RESOURCE')

    def test_complete_delivery_snapshot_precedes_callbacks(self):
        ids=[list(identity) for identity in self.value.corner_vertex_ids]
        points=[list(point) for point in self.value.positions]
        normals=[list(normal) for normal in self.value.normals]
        boundaries=[[kind,key,list(keys)] for kind,key,keys in self.value.boundary_vertex_keys]
        axis=[0,0,1]
        called=0
        def mutate():
            nonlocal called
            called+=1
            if called==1:
                ids[0].clear()
                points[0].clear()
                normals[0].clear()
                boundaries[0][2].clear()
                axis.clear()
                ids.clear()
                points.clear()
                normals.clear()
                boundaries.clear()
        validate(self.value,ids=ids,positions=points,normals=normals,boundaries=boundaries,axis=axis,check=mutate)
        self.assertGreater(called,1)

    def test_callback_exceptions_retain_their_identity(self):
        sentinel=SurfaceError('CALLER','caller failure')
        def stop():
            raise sentinel
        with self.assertRaises(SurfaceError) as caught:
            validate(self.value,check=stop)
        self.assertIs(caught.exception,sentinel)


if __name__=='__main__':
    unittest.main()
