"""Exercise C161's joint audit against delivered bytes, including hidden obstructions."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import unittest

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
        # A single triangle covers a corner of the bore and misses its center.
        import struct
        glb = GLB(self.raw, target='ontokin.glb/0.11')
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
            measure(repack_glb(doc, bytes(binary)))

    def test_transverse_obstruction(self):
        face = [(3.9,.2,4.2),(4.1,.2,4.2),(4.1,.4,4.2)]
        self.assertTrue(opening_intersection(face, .5))

    def test_missing_cap(self):
        glb = GLB(self.raw, target='ontokin.glb/0.11')
        doc = glb.document
        node = next(n for n in doc['nodes'] if n['name'] == 'elbow')
        primitives = doc['meshes'][node['mesh']]['primitives']
        primitives[:] = [p for p in primitives if doc['materials'][p['material']]['name'] != 'elbow: top']
        with self.assertRaisesRegex(ValueError, 'incomplete rim loops'):
            measure(repack_glb(doc, glb.binary))
