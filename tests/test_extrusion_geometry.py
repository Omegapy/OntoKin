"""Independent shape totals and hostile inputs for the frozen polygon contract."""
from collections import Counter
from dataclasses import replace
from fractions import Fraction
import math
import unittest

from ontokin.extrusion import PolygonVertex, triangulate_extrusion
from ontokin.surface import SurfaceError, SurfaceMaterial


PALETTE = (SurfaceMaterial('bottom',(.3,.35,.4,1.),.1,.65),
           SurfaceMaterial('side',(.7,.3,.1,1.),.1,.65),
           SurfaceMaterial('top',(.1,.5,.8,1.),.1,.65))
RECTANGLE = ((0.,0.),(2.,0.),(2.,1.),(0.,1.))
BRACKET = ((0.,0.),(3.,0.),(3.,1.),(1.,1.),(1.,3.),(0.,3.))


def outline(points=RECTANGLE):
    return tuple(PolygonVertex('v'+str(i),10*i,point,'side') for i,point in enumerate(points))


def mesh(vertices=None, *, depth=.5, palette=PALETTE, bottom='bottom', top='top', **kwargs):
    return triangulate_extrusion(outline() if vertices is None else vertices,
                                 palette,depth,bottom,top,**kwargs)


def totals(value):
    area, volume = 0., 0.
    edges = Counter()
    for i in range(0,len(value.positions),3):
        a,b,c = value.positions[i:i+3]
        u,v = [b[j]-a[j] for j in range(3)],[c[j]-a[j] for j in range(3)]
        cross = (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        area += math.hypot(*cross)/2
        volume += sum(a[j]*cross[j] for j in range(3))/6
        for x,y in ((a,b),(b,c),(c,a)):
            edges[x,y] += 1
    return area,volume,edges


class PolygonMeshTests(unittest.TestCase):
    def assertClosed(self, value, area, volume, triangles):
        actual_area,actual_volume,edges = totals(value)
        self.assertAlmostEqual(actual_area,area,places=11)
        self.assertAlmostEqual(actual_volume,volume,places=11)
        self.assertEqual(value.triangle_count,triangles)
        self.assertEqual(len(value.positions),3*triangles)
        for (a,b),count in edges.items():
            self.assertEqual(count,1)
            self.assertEqual(edges[b,a],1)
        for i in range(0,len(value.positions),3):
            a,b,c = value.positions[i:i+3]
            u,v = [b[j]-a[j] for j in range(3)],[c[j]-a[j] for j in range(3)]
            cross = (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            normal = value.normals[i]
            self.assertGreater(sum(x*y for x,y in zip(cross,normal)),0)
            self.assertAlmostEqual(math.hypot(*normal),1)
            self.assertEqual(value.normals[i:i+3],(normal,)*3)

    def assertInvalid(self, suffix, vertices=None, **kwargs):
        with self.assertRaises(SurfaceError) as error:
            mesh(vertices,**kwargs)
        self.assertEqual(error.exception.code,'OKL-E-EXTRUSION-'+suffix)

    def test_rectangle_has_independent_closed_volume_area_and_outward_normals(self):
        self.assertClosed(mesh(),7.,1.,12)

    def test_concave_bracket_is_closed_without_filling_the_missing_corner(self):
        value=mesh(outline(BRACKET),depth=.25)
        self.assertClosed(value,13.,1.25,20)
        for i in range(0,24,3):
            a,b,c=value.positions[i:i+3]
            centroid=tuple((a[j]+b[j]+c[j])/3 for j in range(2))
            self.assertFalse(centroid[0]>1 and centroid[1]>1)

    def test_keyed_corner_edit_changes_only_the_requested_outline(self):
        original=outline(BRACKET)
        edited=tuple(replace(v,point_m=(1.5,1.)) if v.key=='v3' else v for v in original)
        value=mesh(edited,depth=.25)
        self.assertClosed(value,11.+.25*(9.5+math.sqrt(4.25)),1.375,20)
        self.assertEqual(value.vertex_keys,tuple(v.key for v in original))
        self.assertClosed(mesh(original,depth=.25),13.,1.25,20)

    def test_declaration_and_palette_order_cannot_change_native_topology(self):
        vertices=outline(BRACKET)
        a=mesh(vertices,depth=.25)
        b=mesh(tuple(reversed(vertices)),depth=.25,palette=tuple(reversed(PALETTE)))
        self.assertEqual(a,b)

    def test_explicit_order_not_key_spelling_determines_traversal(self):
        vertices=tuple(replace(v,key='key'+str(9-i),order=100*i+5) for i,v in enumerate(outline()))
        value=mesh(tuple(reversed(vertices)))
        self.assertEqual(value.positions,mesh().positions)
        self.assertEqual(value.vertex_keys,tuple(v.key for v in vertices))

    def test_bottom_then_top_then_sides_and_region_indices(self):
        value=mesh()
        self.assertEqual(value.normals[:6],((0.,0.,-1.),)*6)
        self.assertEqual(value.normals[6:12],((0.,0.,1.),)*6)
        self.assertEqual({r.key:len(r.indices)//3 for r in value.regions},
                         {'bottom':2,'side':8,'top':2})
        self.assertEqual([r.key for r in value.regions],['bottom','side','top'])

    def test_each_starting_vertex_selects_its_outgoing_side_material(self):
        vertices=tuple(replace(v,region='bottom' if i==0 else 'side') for i,v in enumerate(outline()))
        value=mesh(vertices)
        self.assertEqual({r.key:len(r.indices)//3 for r in value.regions},
                         {'bottom':4,'side':6,'top':2})

    def test_unused_palette_is_valid_without_empty_primitive(self):
        value=mesh(palette=PALETTE+(SurfaceMaterial('unused',(0.,0.,0.,1.),0.,1.),))
        self.assertEqual([r.key for r in value.regions],['bottom','side','top'])

    def test_count_and_depth_boundaries(self):
        self.assertClosed(mesh(outline(((0.,0.),(1.,0.),(0.,1.))),depth=.25),
                          1.+.25*(2.+math.sqrt(2)),.125,8)
        self.assertEqual(mesh(depth=.001).depth_m,.001)
        self.assertEqual(mesh(depth=100.).depth_m,100.)
        self.assertInvalid('VERTEX',outline()[:2])
        self.assertInvalid('VERTEX',outline()*17)
        for depth in (0.,-.1,math.nextafter(.001,0.),math.nextafter(100.,math.inf),True,math.inf,math.nan):
            with self.subTest(depth=depth):self.assertInvalid('DEPTH',depth=depth)

    def test_vertex_keys_orders_and_point_shapes_are_checked(self):
        vertices=outline()
        for bad in (True,-1,65536,1.5,10):
            with self.subTest(order=bad):
                self.assertInvalid('ORDER',(replace(vertices[0],order=bad),*vertices[1:]))
        self.assertInvalid('VERTEX',(replace(vertices[0],key='v1'),*vertices[1:]))
        self.assertInvalid('VERTEX',(replace(vertices[0],key='../bad'),*vertices[1:]))
        for point in ((0.,),(0.,0.,0.),(True,0.),(math.nan,0.),(100.0001,0.)):
            with self.subTest(point=point):
                self.assertInvalid('POINT',(replace(vertices[0],point_m=point),*vertices[1:]))

    def test_invalid_topology_is_not_repaired(self):
        for points in (((0.,0.),(2.,1.),(2.,0.),(0.,1.)),
                       ((0.,0.),(2.,0.),(2.,1.),(0.,0.)),
                       ((0.,0.),(1.,0.),(2.,0.),(2.,1.),(0.,1.)),
                       ((0.,0.),(2.,0.),(2.,2.),(1.,0.),(0.,2.))):
            with self.subTest(points=points):self.assertInvalid('TOPOLOGY',outline(points))
        self.assertInvalid('WINDING',outline(tuple(reversed(RECTANGLE))))

    def test_sign_zero_does_not_create_distinct_positions(self):
        self.assertInvalid('TOPOLOGY',outline(((0.,0.),(1.,0.),(0.,1.),(-0.,0.))))

    def test_unknown_cap_or_side_region_is_rejected(self):
        self.assertInvalid('REGION',bottom='absent')
        self.assertInvalid('REGION',top='absent')
        vertices=outline()
        self.assertInvalid('REGION',(replace(vertices[0],region='absent'),*vertices[1:]))

    def test_numeric_collapse_in_source_triangle_is_explicit(self):
        tiny=math.ulp(0.)
        self.assertInvalid('NUMERIC',outline(((0.,0.),(tiny,0.),(0.,tiny))))

    def test_allocation_limit_is_checked_before_triangle_emission(self):
        with self.assertRaises(SurfaceError) as error:mesh(max_vertices=35)
        self.assertEqual(error.exception.code,'OKL-E-RESOURCE')
        self.assertEqual(error.exception.details,{'required':36,'available':35})

    def test_host_sequence_membership_cannot_grow_after_the_bound_check(self):
        vertices=list(outline())
        palette=list(PALETTE)
        calls=0
        def mutate():
            nonlocal calls
            calls+=1
            if calls==2:
                vertices.extend(outline(BRACKET)*20)
                palette.extend(PALETTE*20)
        value=mesh(vertices,palette=palette,check=mutate)
        self.assertClosed(value,7.,1.,12)
        self.assertEqual(len(value.regions),3)

    def test_cooperative_work_and_original_cancellation_exception(self):
        calls=[]
        mesh(outline(BRACKET),check=lambda:calls.append(1))
        self.assertGreater(len(calls),60)
        marker=RuntimeError('cancel polygon work')
        n=0
        def cancel():
            nonlocal n
            n+=1
            if n==40:raise marker
        with self.assertRaises(RuntimeError) as caught:mesh(outline(BRACKET),check=cancel)
        self.assertIs(caught.exception,marker)


if __name__=='__main__':unittest.main()
