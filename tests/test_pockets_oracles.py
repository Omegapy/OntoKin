"""Independent hand-written blind-pocket meshes and hostile byte controls.

No product module is imported. This file supplies hand-written cap partitions,
complete walls and floors around independently frozen source coordinates. It
never asks the product to triangulate either a positive or hostile control.
"""
from __future__ import annotations

from collections import defaultdict
import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import unittest

from tools.pockets_oracles import (
    Decoded, LegacyDecoded, check_geometry, check_glb, placement_matrix,
    place_point, source_facts,
)
from tools.ring_loft_oracles import check_surface_intersections
from tools.audit_pockets_acceptance import loads, witness_positions, normalize_pockets

ROOT = Path(__file__).resolve().parents[1]
FROZEN = json.loads((ROOT/'examples/polygon-pockets/expected.json').read_text())
GEOMETRIES = {case['id']: case['geometry'] for case in FROZEN['cases'] if 'geometry' in case}


class Supplied:
    def __init__(self, rows):
        self.rows = rows

    def triangles(self, path):
        assert path == 'shape'
        return self.rows


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def hand_pockets(wanted):
    """Hand partition a rectangular body and zero, one or two rectangular recesses."""
    outer = sorted(wanted['outer_vertices'], key=lambda v: v['order'])
    pockets = sorted(wanted['pockets'], key=lambda p: p['order'])
    assert len(outer) == 4 and len(pockets) <= 2
    assert all(len(p['vertices']) == 4 for p in pockets)
    boundaries = [('outer','outer',outer)]+[
        ('pocket',p['key'],sorted(p['vertices'],key=lambda v:v['order'])) for p in pockets]
    ids = [[(kind,key,v['key']) for v in vertices] for kind,key,vertices in boundaries]
    source = {tuple(item['identity']): tuple(item['position_m']) for item in wanted['source_positions']}
    o = ids[0]
    bottom = [(o[0],o[1],o[2]),(o[0],o[2],o[3])]
    if not pockets:
        top = bottom
    elif len(pockets) == 1:
        p = ids[1]
        top = [(o[0],o[1],p[3]),(o[0],p[3],p[0]),
               (o[1],o[2],p[2]),(o[1],p[2],p[3]),
               (o[2],o[3],p[1]),(o[2],p[1],p[2]),
               (o[3],o[0],p[0]),(o[3],p[0],p[1])]
    else:
        # Four bottom faces, four top faces, left/right strips and the middle
        # quadrilateral. These fourteen triangles were written from the input
        # drawing for the unequal-depth rectangle pair, without an ear clipper.
        l,r=ids[1:]
        top = [(o[0],o[1],r[3]),(o[0],r[3],r[0]),(o[0],r[0],l[3]),(o[0],l[3],l[0]),
               (o[2],o[3],l[1]),(o[2],l[1],l[2]),(o[2],l[2],r[1]),(o[2],r[1],r[2]),
               (o[3],o[0],l[0]),(o[3],l[0],l[1]),(o[1],o[2],r[2]),(o[1],r[2],r[3]),
               (l[3],r[0],r[1]),(l[3],r[1],l[2])]
    offset = wanted['local_placement_m']
    rotation = wanted['local_orientation_wxyz']
    matrix = placement_matrix(rotation)
    rows = []

    def emit(region, identities):
        points = [source[i] for i in identities]
        a,b,c = [tuple(Fraction(float(v)) for v in p) for p in points]
        u,v = tuple(y-x for x,y in zip(a,b)),tuple(y-x for x,y in zip(a,c))
        face=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        length=math.hypot(*(float(x) for x in face))
        normal0=tuple(Fraction(float(x)/length) for x in face)
        normal=tuple(f32(float(sum(x*y for x,y in zip(row,normal0)))) for row in matrix)
        delivered=[tuple(f32(x) for x in place_point(p,rotation,offset)) for p in points]
        material={'pbrMetallicRoughness': {'baseColorFactor':copy.deepcopy(wanted['palette'][region]),
                  'metallicFactor':wanted['metallic'],'roughnessFactor':wanted['roughness']},
                  'extras':{'ontokin':{'source_region_key':region}}}
        rows.append([region,delivered,[normal]*3,material])

    for triangle in bottom:
        emit(wanted['bottom_region'],[(*i,'lower') for i in reversed(triangle)])
    for triangle in top:
        emit(wanted['top_region'],[(*i,'top') for i in triangle])
    for (_,_,vertices),boundary in zip(boundaries,ids):
        for j,vertex in enumerate(vertices):
            a,b=boundary[j],boundary[(j+1)%len(boundary)]
            emit(vertex['region'],[(*a,'lower'),(*b,'lower'),(*a,'top')])
            emit(vertex['region'],[(*b,'lower'),(*b,'top'),(*a,'top')])
    for p,boundary in zip(pockets,ids[1:]):
        for triangle in [(boundary[0],boundary[3],boundary[2]),(boundary[0],boundary[2],boundary[1])]:
            emit(p['floor_region'],[(*i,'lower') for i in triangle])
    return rows


def pack_document(document, binary=b''):
    payload = json.dumps(document, separators=(',', ':')).encode()
    payload += b' ' * (-len(payload) % 4)
    binary += b'\x00' * (-len(binary) % 4)
    return (struct.pack('<III', 0x46546c67, 2, 28 + len(payload) + len(binary))
            + struct.pack('<II', len(payload), 0x4e4f534a) + payload
            + struct.pack('<II', len(binary), 0x004e4942) + binary)


def hand_document(rows):
    """Encode actual independent position/normal/index/animation accessors."""
    document = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
                'nodes': [{'mesh': 0, 'translation': [0, 0, 0], 'rotation': [0, 0, 0, 1],
                           'extras': {'ontokin': {'kind': 'object', 'path': 'shape'}}}],
                'meshes': [{'primitives': []}], 'materials': [], 'accessors': [], 'bufferViews': [],
                'buffers': [{'byteLength': 0}],
                'extras': {'ontokin': {'target_contract': 'ontokin.glb/0.12', 'profile': 'polygon-pockets-0.1',
                                       'schema_version': '0.12', 'program': {'revision': 'sha256:fixture'}}}}
    binary = bytearray()

    def accessor(values, kind, component=5126):
        while len(binary) % 4:
            binary.append(0)
        start = len(binary)
        components = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[kind]
        fmt = 'I' if component == 5125 else 'f'
        for row in values:
            binary.extend(struct.pack('<' + fmt * components, *([row] if components == 1 else row)))
        view = len(document['bufferViews'])
        document['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(binary) - start})
        index = len(document['accessors'])
        document['accessors'].append({'bufferView': view, 'componentType': component, 'count': len(values), 'type': kind})
        return index

    groups = defaultdict(list)
    for row in rows:
        groups[row[0]].append(row)
    for region in sorted(groups):
        group = groups[region]
        positions = [point for row in group for point in row[1]]
        normals = [normal for row in group for normal in row[2]]
        material = len(document['materials'])
        document['materials'].append(copy.deepcopy(group[0][3]))
        primitive = {'attributes': {'POSITION': accessor(positions, 'VEC3'), 'NORMAL': accessor(normals, 'VEC3')},
                     'indices': accessor(list(range(len(positions))), 'SCALAR', 5125), 'material': material, 'mode': 4}
        document['meshes'][0]['primitives'].append(primitive)
    times = accessor([0, .25, .5, .75, 1], 'SCALAR')
    translations = accessor([[0, t*.5, 0] for t in [0, .25, .5, .75, 1]], 'VEC3')
    rotations = accessor([[0, 0, 0, 1]]*5, 'VEC4')
    document['animations'] = [{'samplers': [{'input': times, 'output': translations, 'interpolation': 'LINEAR'},
                                           {'input': times, 'output': rotations, 'interpolation': 'LINEAR'}],
                               'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'translation'}},
                                            {'sampler': 1, 'target': {'node': 0, 'path': 'rotation'}}]}]
    document['buffers'][0]['byteLength'] = len(binary)
    return document, bytes(binary)


class PocketsOracleTests(unittest.TestCase):
    def setUp(self):
        self.wanted=copy.deepcopy(GEOMETRIES['rectangular-pocket'])
        self.rows=hand_pockets(self.wanted)

    def reject(self, mutation, message=None):
        mutation(self.rows)
        context=self.assertRaisesRegex(AssertionError,message) if message else self.assertRaises(AssertionError)
        with context:
            check_geometry(Supplied(self.rows),'shape',self.wanted)

    def test_hand_rectangular_blind_pocket_has_volume_23_area_55(self):
        result=check_geometry(Supplied(self.rows),'shape',self.wanted)
        self.assertEqual(result['signed_volume_m3'],23)
        self.assertEqual(result['surface_area_m2'],55)
        self.assertEqual(result['floor_coordinates_m'],{'recess':1.5})
        self.assertEqual({d['domain']:d['triangles'] for d in result['face_domains']},
                         {'bottom':2,'top':8,'floor:recess':2})

    def test_hand_unequal_depths_retain_two_separate_floors(self):
        wanted=GEOMETRIES['unequal-depths']
        result=check_geometry(Supplied(hand_pockets(wanted)),'shape',wanted)
        self.assertEqual(result['floor_coordinates_m'],{'left':1.5,'right':.75})
        self.assertEqual(result['signed_volume_m3'],59.5)

    def test_hand_placement_namespace_order_material_and_depth_boundaries(self):
        for name in ('zero-pockets','minimum-body-height','minimum-pocket-depth','minimum-base',
                     'above-minimum-base','rounded-floor','gapped-orders','pocket-key-outer',
                     'mixed-wall-materials','placed-rotated-pocket','function-pocket-and-geometry',
                     'repaired-rectangular-pocket'):
            with self.subTest(name=name):
                wanted=GEOMETRIES[name]
                self.assertEqual(check_geometry(Supplied(hand_pockets(wanted)),'shape',wanted)['status'],'passed')

    def test_every_frozen_source_floor_and_four_part_identity_is_recomputed(self):
        for name,wanted in GEOMETRIES.items():
            with self.subTest(name=name):
                source,domains,walls,floors=source_facts(wanted)
                self.assertEqual(len(source),wanted['logical_vertex_count'])
                self.assertEqual(len(domains),2+wanted['pocket_count'])
                self.assertEqual(len(walls),wanted['wall_triangle_count'])
                self.assertEqual(floors,{p['key']:p['floor_m'] for p in wanted['pockets']})
                self.assertEqual(witness_positions(wanted),[
                    tuple(f32(v) for v in place_point(row['position_m'],wanted['local_orientation_wxyz'],wanted['local_placement_m']))
                    for row in wanted['source_positions']])

    def test_exact_reduced_base_ratio_cannot_be_replaced_by_rounded_floor(self):
        changed=copy.deepcopy(GEOMETRIES['rounded-floor'])
        changed['pockets'][0]['exact_remaining_base_m']['numerator']='2'
        with self.assertRaises(AssertionError):source_facts(changed)

    def test_source_identity_namespace_cannot_merge_outer_with_named_outer_pocket(self):
        changed=copy.deepcopy(GEOMETRIES['pocket-key-outer'])
        changed['source_positions'][-1]['identity'][0]='outer'
        with self.assertRaises(AssertionError):source_facts(changed)

    def test_removed_floor_is_rejected(self):
        self.reject(lambda rows:rows.pop(next(i for i,r in enumerate(rows) if r[0]=='floor')))

    def test_reversed_floor_is_rejected_even_with_reversed_normal(self):
        def mutation(rows):
            row=next(r for r in rows if r[0]=='floor')
            row[1].reverse();row[2]=[tuple(-x for x in n) for n in row[2]]
        self.reject(mutation)

    def test_filled_opening_is_rejected_at_equal_triangle_count(self):
        def mutation(rows):
            floor=copy.deepcopy(next(r for r in rows if r[0]=='floor'))
            floor[1]=[(x,y,2) for x,y,z in floor[1]]
            floor[0]='top';floor[3]=copy.deepcopy(next(r[3] for r in rows if r[0]=='top'))
            rows[next(i for i,r in enumerate(rows) if r[0]=='top')]=floor
        self.reject(mutation)

    def test_overlapping_cap_is_rejected_with_preserved_material_counts(self):
        def mutation(rows):
            indices=[i for i,r in enumerate(rows) if r[0]=='top']
            rows[indices[0]]=copy.deepcopy(rows[indices[1]])
        self.reject(mutation)

    def test_swapped_pocket_depths_are_rejected(self):
        self.wanted=copy.deepcopy(GEOMETRIES['unequal-depths']);self.rows=hand_pockets(self.wanted)
        def mutation(rows):
            for row in rows:
                row[1]=[(x,y,.75 if z==1.5 else 1.5 if z==.75 else z) for x,y,z in row[1]]
        self.reject(mutation)

    def test_altered_floor_material_is_rejected(self):
        def mutation(rows):
            row=next(r for r in rows if r[0]=='floor')
            row[0]='top';row[3]=copy.deepcopy(next(r[3] for r in rows if r[0]=='top'))
        self.reject(mutation)

    def test_blind_to_through_hole_is_rejected(self):
        def mutation(rows):
            for row in rows:row[1]=[(x,y,0 if z==1.5 else z) for x,y,z in row[1]]
        self.reject(mutation)

    def test_missing_wall_is_rejected(self):
        self.reject(lambda rows:rows.pop(next(i for i,r in enumerate(rows) if r[0]=='inner')))

    def test_wrong_pbr_wrong_flat_normal_and_corner_perturbation_are_rejected(self):
        def pbr(rows):rows[0][3]['pbrMetallicRoughness']['roughnessFactor']=.2
        def normal(rows):rows[0][2]=[(0,0,1)]*3
        def point(rows):rows[0][1][0]=tuple(v+.001 for v in rows[0][1][0])
        for mutation in (pbr,normal,point):
            with self.subTest(mutation=mutation.__name__):
                self.rows=hand_pockets(self.wanted);self.reject(mutation)

    def test_actual_supplied_glb_and_dense_motion(self):
        doc,binary=hand_document(self.rows)
        result=check_glb(pack_document(doc,binary),{'shape':{'geometry':self.wanted,
                        'origin':[0,0,0],'velocity':[0,.5,0]}},'sha256:fixture')
        self.assertEqual(result['status'],'passed')
        self.assertEqual(len(result['observations']),21)
        self.assertEqual(result['observations'][-1]['translation'],[0,.5,0])

    def test_actual_legacy_bytes_require_the_older_explicit_binding(self):
        wanted=GEOMETRIES['zero-pockets']
        doc,binary=hand_document(hand_pockets(wanted))
        meta=doc['extras']['ontokin']
        meta.update(target_contract='ontokin.glb/0.8',profile='polygon-extrusion-0.1',schema_version='0.8')
        raw=pack_document(doc,binary)
        with self.assertRaises(AssertionError):Decoded(raw)
        self.assertEqual(check_geometry(LegacyDecoded(raw),'shape',wanted)['signed_volume_m3'],24)

    def test_accessor_view_overrun_and_duplicate_corner_use_are_rejected(self):
        doc,binary=hand_document(self.rows)
        view=doc['bufferViews'][doc['accessors'][0]['bufferView']]
        view['byteLength']-=4
        with self.assertRaises(AssertionError):Decoded(pack_document(doc,binary)).triangles('shape')
        doc,binary=hand_document(self.rows)
        primitive=doc['meshes'][0]['primitives'][0]
        index=doc['accessors'][primitive['indices']]
        start=doc['bufferViews'][index['bufferView']]['byteOffset']
        changed=bytearray(binary);struct.pack_into('<I',changed,start+4,0)
        with self.assertRaises(AssertionError):Decoded(pack_document(doc,bytes(changed))).triangles('shape')

    def test_actual_scene_scale_hierarchy_hidden_mesh_and_wrong_revision_are_rejected(self):
        def scale(doc):doc['nodes'][0]['scale']=[2,1,1]
        def hierarchy(doc):doc['nodes'][0]['children']=[0]
        def hidden(doc):doc['meshes'].append(copy.deepcopy(doc['meshes'][0]))
        def revision(doc):doc['extras']['ontokin']['program']['revision']='sha256:other'
        for mutation in (scale,hierarchy,hidden,revision):
            with self.subTest(mutation=mutation.__name__):
                doc,binary=hand_document(self.rows);mutation(doc)
                with self.assertRaises(AssertionError):
                    check_glb(pack_document(doc,binary),{'shape':{'geometry':self.wanted,'origin':[0,0,0],
                              'velocity':[0,.5,0]}},'sha256:fixture')

    def test_actual_motion_value_duplicate_target_and_key_clock_are_rejected(self):
        for kind in ('motion','clock','duplicate'):
            with self.subTest(kind=kind):
                doc,binary=hand_document(self.rows);changed=bytearray(binary)
                animation=doc['animations'][0]
                if kind=='duplicate':animation['channels'].append(copy.deepcopy(animation['channels'][0]))
                else:
                    sampler=animation['samplers'][0]
                    acc=doc['accessors'][sampler['output' if kind=='motion' else 'input']]
                    start=doc['bufferViews'][acc['bufferView']]['byteOffset']
                    struct.pack_into('<f',changed,start+4,.125)
                with self.assertRaises(AssertionError):
                    check_glb(pack_document(doc,bytes(changed)),{'shape':{'geometry':self.wanted,
                              'origin':[0,0,0],'velocity':[0,.5,0]}},'sha256:fixture')

    def test_small_component_errors_cannot_exceed_angular_motion_tolerance(self):
        doc,binary=hand_document(self.rows)
        rotation=[.0009,.0009,.0009,math.sqrt(1-3*.0009**2)]
        self.assertTrue(all(abs(a-b) < .001 for a,b in zip(rotation,[0,0,0,1])))
        doc['nodes'][0]['rotation']=rotation
        sampler=doc['animations'][0]['samplers'][1]
        accessor=doc['accessors'][sampler['output']]
        start=doc['bufferViews'][accessor['bufferView']]['byteOffset']
        changed=bytearray(binary)
        for i in range(accessor['count']):struct.pack_into('<ffff',changed,start+16*i,*rotation)
        with self.assertRaisesRegex(AssertionError,'angular tolerance'):
            check_glb(pack_document(doc,bytes(changed)),{'shape':{'geometry':self.wanted,
                      'origin':[0,0,0],'velocity':[0,.5,0]}},'sha256:fixture')

    def test_independent_reader_rejects_duplicate_or_nonfinite_raw_evidence(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}','{"x":1e999}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):loads(raw)

    def test_summary_normalization_keeps_the_exact_floor_contract(self):
        wanted=GEOMETRIES['rectangular-pocket']['pockets']
        supplied=copy.deepcopy(wanted)
        for p in supplied:
            for v in p['vertices']:v['side_region']=v.pop('region')
        self.assertEqual(normalize_pockets(supplied),normalize_pockets(wanted))
        supplied[0]['effective_depth_m']['numerator']='3'
        self.assertNotEqual(normalize_pockets(supplied),normalize_pockets(wanted))

    def test_shared_simplex_reader_rejects_nonshared_contact(self):
        triangles=[[(0,0,0),(2,0,0),(0,2,0)],[(.5,.5,-1),(.5,.5,1),(2,2,0)]]
        with self.assertRaises(AssertionError):
            check_surface_intersections(triangles,[('a','b','c'),('d','e','f')])

    def test_frozen_oracle_adversary_inventory_is_explicitly_exercised(self):
        self.assertEqual(FROZEN['oracle_adversaries'],['removed-floor','reversed-floor','filled-opening',
            'overlapping-cap','swapped-pocket-depths','altered-floor-material','blind-to-through-hole','missing-wall'])


if __name__=='__main__':
    unittest.main()
