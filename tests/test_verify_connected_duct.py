"""Exercise C161's joint audit against delivered bytes, including hidden obstructions."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import unittest
import json
import math
import struct

from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import ProgramBundle, load_file_manifest
from ontokin.scene import ExportOptions
from tools.texture_reference import GLB, repack_glb
from tools.verify_connected_duct import JointFailure, measure, opening_intersection


EXAMPLE = Path(__file__).resolve().parents[1] / 'examples' / 'connected-duct'


class ConnectedDuctAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_file_manifest(EXAMPLE / 'assembly.files.json')
        cls.raw = cls.export(cls.bundle)

    @staticmethod
    def export(bundle):
        result = execute_framed_loft_export(bundle, options=ExportOptions(fps=2, end='1', helpers=False))
        if result.data is None:
            raise ValueError(result.report['diagnostics'])
        return result.data

    def test_sheared_centerline(self):
        original = self.bundle.modules[0]
        moved = replace(original, raw=original.raw.replace(b'vec3(0[m], 0[m], 4[m])',
                                                          b'vec3(0[m], 1[m], 4[m])'))
        entry = replace(self.bundle.entry, raw=self.bundle.entry.raw.replace(original.revision.encode(),
                                                                            moved.revision.encode()))
        raw = self.export(ProgramBundle(entry, (moved,)))
        with self.assertRaisesRegex(JointFailure, 'straight centerline differs') as rejection:
            measure(raw)
        axis = rejection.exception.measurements['ports']['straight']['centerline_direction']
        self.assertAlmostEqual(axis[1], 1/17**0.5)

    def test_offset_measurements(self):
        original = self.bundle.entry
        entry = replace(original, raw=original.raw.replace(b'bore_shift = 0[m];', b'bore_shift = 0.25[m];'))
        raw = self.export(ProgramBundle(entry, self.bundle.modules))
        with self.assertRaisesRegex(JointFailure, 'straight rim corner differs') as rejection:
            measure(raw)
        row = rejection.exception.measurements
        self.assertAlmostEqual(row['inner_center_displacement_m'][2], -0.25)
        self.assertAlmostEqual(row['rectangular_rim_overlap_m2'], 0.75)

    def test_unsupported_transforms_and_deformations(self):
        for kind in ('scale', 'matrix', 'children', 'skin', 'morph'):
            with self.subTest(kind=kind):
                glb = GLB(self.raw, target='ontokin.glb/0.11')
                doc = glb.document
                node = next(n for n in doc['nodes'] if n['name'] == 'straight')
                if kind == 'morph':
                    mesh = doc['meshes'][node['mesh']]
                    for primitive in mesh['primitives']:
                        primitive['targets'] = [{'POSITION': primitive['attributes']['POSITION']}]
                    mesh['weights'] = [1.0]
                else:
                    node[kind] = {'scale': [2, 2, 2], 'matrix': [1,0,0,0,0,1,0,0,0,0,1,0,1,0,0,1],
                                  'children': [0], 'skin': 0}[kind]
                with self.assertRaisesRegex(ValueError, 'deformation/hierarchy|rigid duct mesh'):
                    measure(repack_glb(doc, glb.binary))

    def test_nominal(self):
        row = measure(self.raw)
        self.assertEqual(row['stationary_keys_s'], [0, 0.5, 1])
        for port in row['ports'].values():
            self.assertAlmostEqual(port['clear_area_m2'], 1.0, places=5)

    def test_extra_obstruction_outside_cap_material(self):
        # Elbow-local coordinates are identical for both rigid placements.
        for placement, manifest in [('fixed', 'assembly.files.json'), ('oblique', 'assembly-oblique.files.json')]:
            with self.subTest(placement=placement):
                raw = self.export(load_file_manifest(EXAMPLE / manifest))
                self.check_extra_obstruction(raw, placement)

    def check_extra_obstruction(self, raw, placement):
        # A single triangle covers a corner of the bore and misses its center.
        glb = GLB(raw, target='ontokin.glb/0.11')
        doc = glb.document
        node = next(n for n in doc['nodes'] if n['name'] == 'elbow')
        primitives = doc['meshes'][node['mesh']]['primitives']
        extra = deepcopy(primitives[0])
        binary = bytearray(glb.binary)
        for key, arity, values in [('POSITION', 3, [(4,.1,4.1),(4,.3,4.1),(4,.1,4.3)]),
                                   ('NORMAL', 3, [(1,0,0)]*3), ('indices', 1, [(0,), (1,), (2,)])]:
            indices = key == 'indices'
            data = b''.join(struct.pack('<'+('H' if indices else 'f')*arity, *v) for v in values)
            view = len(doc['bufferViews'])
            doc['bufferViews'].append({'buffer':0, 'byteOffset':len(binary), 'byteLength':len(data)})
            binary.extend(data)
            index = len(doc['accessors'])
            doc['accessors'].append({'bufferView':view, 'componentType':5123 if indices else 5126,
                                     'type':'SCALAR' if indices else 'VEC3', 'count':3})
            if indices:
                extra[key] = index
            else:
                extra['attributes'][key] = index
        primitives.append(extra)
        with self.assertRaisesRegex(ValueError, 'obstructed opening'):
            measure(repack_glb(doc, bytes(binary)), placement=placement)

    def test_transverse_obstruction(self):
        face = [(-.1,.2,.2),(.1,.2,.2),(.1,.4,.2)]
        self.assertTrue(opening_intersection(face, .5))

    def test_oblique_contract(self):
        bundle = load_file_manifest(EXAMPLE / 'assembly-oblique.files.json')
        expected = json.loads((EXAMPLE / 'oblique-contract.json').read_text())
        nominal = measure(self.export(bundle), placement='oblique')
        for name, port in nominal['ports'].items():
            end = 'outlet' if name == 'elbow' else 'inlet'
            self.assertLess(math.dist(port['cap_normal'], expected[f'{name}_{end}_normal']), 1e-5)
            self.assertLess(math.dist(port['inner_center_m'], expected[f'{name}_{end}_center_m']), 1e-5)
            for key in ('outer_loop_m', 'inner_loop_m'):
                for corner in expected[key]:
                    self.assertLess(min(math.dist(corner, p) for p in port[key]), 1e-5)
        self.assertLess(math.dist(nominal['ports']['straight']['outlet_center_m'],
                                  expected['straight_outlet_center_m']), 1e-5)
        self.assertAlmostEqual(nominal['rectangular_rim_overlap_m2'], 1, places=5)
        entry = replace(bundle.entry, raw=bundle.entry.raw.replace(b'bore_shift = 0[m];', b'bore_shift = 0.25[m];'))
        with self.assertRaisesRegex(JointFailure, 'straight rim corner differs') as rejection:
            measure(self.export(ProgramBundle(entry, bundle.modules)), placement='oblique')
        row = rejection.exception.measurements
        self.assertLess(math.dist(row['inner_center_displacement_m'], expected['shift_world_m']), 1e-5)
        self.assertAlmostEqual(row['rectangular_rim_overlap_m2'], .75, places=5)

    def test_wrong_endpoint_and_reversed_winding(self):
        bundle = load_file_manifest(EXAMPLE / 'assembly-oblique.files.json')
        raw = self.export(bundle)
        for fault in ('endpoint', 'winding'):
            with self.subTest(fault=fault):
                glb = GLB(raw, target='ontokin.glb/0.11')
                doc = glb.document
                binary = bytearray(glb.binary)
                node = next(n for n in doc['nodes'] if n['name'] == 'straight')
                primitives = doc['meshes'][node['mesh']]['primitives']
                caps = {doc['materials'][p['material']]['name']: p for p in primitives}
                inlet, outlet = caps['straight: bottom'], caps['straight: top']
                if fault == 'endpoint':
                    inlet['material'], outlet['material'] = outlet['material'], inlet['material']
                    inlet['extras'], outlet['extras'] = outlet['extras'], inlet['extras']
                else:
                    acc = doc['accessors'][inlet['indices']]
                    view = doc['bufferViews'][acc['bufferView']]
                    offset = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
                    pair = '<' + {5121:'B', 5123:'H', 5125:'I'}[acc['componentType']]*2
                    a,b = struct.unpack_from(pair, binary, offset)
                    struct.pack_into(pair, binary, offset, b,a)
                with self.assertRaisesRegex(JointFailure, 'straight cap normal differs'):
                    measure(repack_glb(doc, bytes(binary)), placement='oblique')

    def test_inconsistent_region_identity(self):
        for fault in ('primitive', 'material', 'both', 'occurrence'):
            with self.subTest(fault=fault):
                glb = GLB(self.raw, target='ontokin.glb/0.11')
                inlet = next(p for p in glb.primitives('straight') if p['extras']['ontokin']['region_key'] == 'bottom')
                identity = glb.reference('materials', inlet['material'])['extras']['ontokin']
                if fault in ('primitive', 'both'):
                    inlet['extras']['ontokin']['region_key'] = 'top'
                if fault in ('material', 'both'):
                    identity['source_region_key'] = 'top'
                if fault == 'occurrence':
                    identity['occurrence_path'] = 'elbow'
                with self.assertRaisesRegex(ValueError, 'inconsistent region identity'):
                    measure(repack_glb(glb.document, glb.binary))

    def test_wrong_object_identity(self):
        glb = GLB(self.raw, target='ontokin.glb/0.11')
        nodes = glb.document['nodes']
        nodes[0]['name'], nodes[1]['name'] = nodes[1]['name'], nodes[0]['name']
        with self.assertRaisesRegex(ValueError, 'object path differs'):
            measure(repack_glb(glb.document, glb.binary))

    def test_negative_references(self):
        for table in ('scene', 'sampler'):
            with self.subTest(table=table):
                glb = GLB(self.raw, target='ontokin.glb/0.11')
                if table == 'scene':
                    glb.document['scene'] = -1
                else:
                    animation = glb.document['animations'][0]
                    channel = animation['channels'][-1]
                    channel['sampler'] -= len(animation['samplers'])
                with self.assertRaisesRegex(ValueError, 'Invalid .* reference'):
                    measure(repack_glb(glb.document, glb.binary))

    def test_missing_cap(self):
        glb = GLB(self.raw, target='ontokin.glb/0.11')
        doc = glb.document
        node = next(n for n in doc['nodes'] if n['name'] == 'elbow')
        primitives = doc['meshes'][node['mesh']]['primitives']
        primitives[:] = [p for p in primitives if doc['materials'][p['material']]['name'] != 'elbow: top']
        with self.assertRaisesRegex(ValueError, 'incomplete rim loops'):
            measure(repack_glb(doc, glb.binary))
