"""Exercise the two-joint oracle against independent source and byte-level faults."""
from dataclasses import replace
import struct
import unittest

from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import load_file_manifest
from ontokin.execution_budget import HostPolicy
from ontokin.scene import ExportOptions
from tools.texture_reference import GLB, repack_glb
from tools.verify_duct_span import EXAMPLE, verify


class SpanOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bundle = load_file_manifest(EXAMPLE / 'span-achievable.files.json')
        def export(source):
            edited = replace(bundle, entry=replace(bundle.entry, raw=source))
            result = execute_framed_loft_export(edited, policy=HostPolicy(200000, 30000),
                                                options=ExportOptions(fps=2, end='1', helpers=False))
            if result.data is None:
                raise ValueError(result.report['diagnostics'])
            return result.data
        source = bundle.entry.raw
        cls.before = export(source)
        pose = b'vec3(5[m], 2[m], 3[m]), quat(0.7071067811865476, 0, 0.7071067811865476, 0)'
        fit = source.replace(b'vec3(5.4[m], 1.5[m], 4[m]), quat(1, 0, 0, 0)', pose)
        cls.short = export(fit)
        cls.accepted = export(fit.replace(b'span = 4[m]', b'span = 5.75[m]'))

    def test_independent_frozen_fit(self):
        result = verify(self.before, self.accepted)
        self.assertTrue(result['passed'], result)
        for joint in result['joints'].values():
            self.assertAlmostEqual(joint['common_open_area_m2'], 1, places=5)

    def test_correct_upstream_wrong_length(self):
        result = verify(self.before, self.short)
        self.assertFalse(result['passed'])
        self.assertTrue(result['joints']['upstream']['passed'])
        self.assertAlmostEqual(result['joints']['downstream']['center_distance_m'], 1.75)

    def test_independent_corruption_at_each_cap(self):
        for region, joint in [('bottom', 'upstream'), ('top', 'downstream')]:
            for fault in ('outer', 'inner', 'winding'):
                with self.subTest(region=region, fault=fault):
                    glb = GLB(self.accepted, target='ontokin.glb/0.11')
                    primitive = next(p for p in glb.primitives('link') if p['extras']['ontokin']['region_key'] == region)
                    data = bytearray(glb.binary)
                    positions = primitive['attributes']['POSITION']
                    stream = primitive['indices'] if fault == 'winding' else positions
                    accessor = glb.reference('accessors', stream)
                    view = glb.reference('bufferViews', accessor['bufferView'])
                    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
                    if fault == 'winding':
                        fmt = '<' + {5121: 'B', 5123: 'H', 5125: 'I'}[accessor['componentType']] * 2
                        a, b = struct.unpack_from(fmt, data, offset)
                        struct.pack_into(fmt, data, offset, b, a)
                    else:
                        half = 1 if fault == 'outer' else .5
                        vertices = glb.accessor(positions)
                        index = next(i for i in glb.accessor(primitive['indices']) if abs(vertices[i][0]) == half)
                        offset += index * view.get('byteStride', 12)
                        x, = struct.unpack_from('<f', data, offset)
                        struct.pack_into('<f', data, offset, x + .002)
                    result = verify(self.before, repack_glb(glb.document, bytes(data)))
                    self.assertFalse(result['passed'])
                    self.assertFalse(result['joints'][joint]['passed'])
                    other_joint = 'upstream' if joint == 'downstream' else 'downstream'
                    self.assertTrue(result['joints'][other_joint]['passed'])

    def test_repeated_identity_material_and_render_faults(self):
        def corrupt(raw, fault):
            glb = GLB(raw, target='ontokin.glb/0.11')
            doc = glb.document
            name = 'bypass'  # This stationary decoy never participates in a requested joint.
            node = doc['nodes'][glb.objects()[name]]
            identity = node['extras']['ontokin']
            program = doc['extras']['ontokin']['program']
            occurrence = program['occurrences'][name]
            prim = glb.primitives(name)[0]
            mat = doc['materials'][prim['material']]
            if fault == 'occurrence':
                program['occurrences']['unrendered'] = occurrence
            elif fault == 'class':
                for mapping in (identity['source_mapping'], occurrence):
                    mapping['definition_id'][-1] = 'straight'
                    mapping['class_id'] = '/'.join(mapping['definition_id'])
                identity['class_name'] = occurrence['class_id']
            elif fault == 'element':
                for mapping in (identity['source_mapping'], occurrence):
                    mapping['element_id'][-1] = 'other'
                identity['element_id'][-1] = 'other'
                for p in glb.primitives(name):
                    doc['materials'][p['material']]['extras']['ontokin']['element_id'][-1] = 'other'
            elif fault == 'version':
                for unit in program['manifest']['units']:
                    if unit['package_id']:
                        unit['version'] = program['sources'][unit['source_id']]['version'] = '1.0.0'
            elif fault == 'material':
                mat['pbrMetallicRoughness']['metallicFactor'] = .9
            elif fault == 'palette':
                identity['geometry']['materials'][0]['metallic'] = mat['pbrMetallicRoughness']['metallicFactor'] = .9
            elif fault == 'texture':
                mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': 0}
            elif fault == 'normal-texture':
                mat['normalTexture'] = {'index': 0}
            elif fault == 'mode':
                prim['mode'] = 5
            elif fault == 'morph':
                prim['targets'] = [{'POSITION': prim['attributes']['POSITION']}]
            return repack_glb(doc, glb.binary)

        for fault in ('occurrence', 'class', 'element', 'version', 'material', 'palette',
                      'texture', 'normal-texture', 'mode', 'morph'):
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                verify(corrupt(self.before, fault), corrupt(self.accepted, fault))
