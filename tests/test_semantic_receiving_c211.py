"""CPU rejection controls; synthetic observations are not receiving evidence."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from prototypes.semantic_receiving_c211 import validation as v

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT/'docs/engineering/semantic-export-c210/evidence/proof'


def to_native(row):
    return [row[0], -row[2], row[1], row[3], -row[5], row[4]]


def native_matrix(source):
    perm, signs = [0, 2, 1, 3], [1, -1, 1, 1]
    return [[signs[i]*signs[j]*source[perm[i]][perm[j]] for j in range(4)] for i in range(4)]


def synthetic_report(semantic, reference, reader):
    rows, samples = [], []
    for obj in semantic['objects']:
        i = obj['geometry_binding']['node']
        triangles = reader.triangles(i)
        material = reader.material(i)
        rows.append({'name': obj['path'], 'type': 'MESH', 'parent': None, 'constraints': [], 'modifiers': [],
            'rigid_body': False, 'triangles': triangles,
            'triangles_raw_blender': [[to_native(x) for x in t] for t in triangles],
            'triangle_material_indices': [0]*len(triangles), 'materials': [{'use_nodes': True, 'bsdf_type': 'BSDF_PRINCIPLED', 'inputs': {'Base Color': material['baseColorFactor'], 'Metallic': material['metallicFactor'], 'Roughness': material['roughnessFactor'], 'Alpha': material['alpha']}, 'use_backface_culling': not material['double_sided']}], 'material': material,
            'semantic_json': v.canonical(obj), 'element_id_json': v.canonical(obj['element_id']),
            'accepted_revision': v.REVISION})
    for t in v.TIMES:
        objects = {}
        for obj in semantic['objects']:
            p, q, s = reader.pose(obj['geometry_binding']['node'], float(t))
            m = v.matrix(p, q, s)
            objects[obj['path']] = {'position_m': p, 'orientation_wxyz': q, 'scale': s,
                                   'matrix': m, 'matrix_world_blender': native_matrix(m)}
        samples.append({'time_seconds': t, 'frame': float(t)*60, 'objects': objects})
    return {'schema': 'ontokin.c211.observations/0.1', 'phase': 'synthetic-test-fixture',
        'build': {'version': v.BUILD['version'], 'build_hash': v.BUILD['build_hash'], 'executable_sha256': v.BUILD['executable']['sha256']},
        'input_sha256': {n: r['sha256'] for n, r in v.INPUTS['files'].items()},
        'import_settings': {k: ('/fixture/after.glb' if k == 'filepath' else r['default']) for k, r in v.BUILD['importer_properties'].items()},
        'units': {'system': 'METRIC', 'scale_length': 1.0, 'length_unit': 'METERS'}, 'physics_world': False,
        'semantic_text': v.canonical(semantic), 'scene_mapping_json': v.canonical(semantic),
        'native_extras_before_mapping': {o['path']: {'ontokin': 'synthetic metadata fixture'} for o in semantic['objects']},
        'objects': rows, 'samples': samples}


class SemanticReceivingC211Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic, cls.reference, cls.reader = v.validate_inputs(PROOF)
        cls.fixture = synthetic_report(cls.semantic, cls.reference, cls.reader)

    def validate(self, report):
        return v.validate_observations(report, self.semantic, self.reference, self.reader)

    def reject(self, mutate, pattern):
        report = copy.deepcopy(self.fixture)
        mutate(report)
        with self.assertRaisesRegex(ValueError, pattern):
            self.validate(report)

    def test_exact_input_closure_and_synthetic_accounting(self):
        result = self.validate(self.fixture)
        self.assertEqual((result['objects'], result['triangles'], result['poses']), (18, 7800, 126))
        self.assertFalse(result['full_release'])

    def test_every_changed_input_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in v.INPUTS['files']:
                shutil.copyfile(PROOF/name, root/name)
            for name in v.INPUTS['files']:
                with self.subTest(name=name):
                    path = root/name
                    raw = path.read_bytes()
                    path.write_bytes(raw + b' ')
                    with self.assertRaisesRegex(ValueError, 'input binding differs'):
                        v.validate_inputs(root)
                    path.write_bytes(raw)

    def test_missing_native_object_rejects(self):
        self.reject(lambda r: r['objects'].pop(), 'names missing or duplicate')

    def test_duplicate_native_object_rejects(self):
        self.reject(lambda r: r['objects'][0].update(name=r['objects'][1]['name']), 'names missing or duplicate')

    def test_changed_semantic_id_rejects(self):
        self.reject(lambda r: r['objects'][0].update(element_id_json='["wrong"]'), 'ID/revision mapping')

    def test_stale_accepted_revision_rejects(self):
        self.reject(lambda r: r['objects'][0].update(accepted_revision='sha256:stale'), 'ID/revision mapping')

    def test_wrong_scene_units_rejects(self):
        self.reject(lambda r: r['units'].update(scale_length=0.01), 'native units')

    def test_missing_triangle_rejects(self):
        self.reject(lambda r: r['objects'][0]['triangles'].pop(), 'triangle inventory')

    def test_altered_vertex_rejects(self):
        self.reject(lambda r: r['objects'][0]['triangles'][0][0].__setitem__(0, 4), 'triangle')

    def test_reversed_winding_rejects(self):
        self.reject(lambda r: r['objects'][0]['triangles'][0].reverse(), 'triangle')

    def test_changed_native_raw_coordinates_rejects(self):
        self.reject(lambda r: r['objects'][0]['triangles_raw_blender'][0][0].__setitem__(0, 4), 'coordinate conversion')

    def test_triangle_and_cyclic_vertex_reordering_is_permitted(self):
        triangles = self.reader.triangles(0)
        changed = [row[1:]+row[:1] for row in reversed(triangles)]
        v.compare_triangles(changed, triangles, 'reordering')

    def test_material_change_rejects(self):
        self.reject(lambda r: r['objects'][0]['material'].update(roughnessFactor=0.2), 'raw/material summary differs')

    def test_sidecar_mapping_change_rejects(self):
        self.reject(lambda r: r.update(semantic_text='{}'), 'complete sidecar mapping')

    def test_ownership_must_not_become_parenting(self):
        self.reject(lambda r: r['objects'][1].update(parent='first'), 'native object/parent')

    def test_unselected_physics_rejects(self):
        self.reject(lambda r: r.update(physics_world=True), 'unexpected native physics')

    def test_missing_sample_rejects(self):
        self.reject(lambda r: r['samples'].pop(), 'sample inventory')

    def test_wrong_time_rejects(self):
        self.reject(lambda r: r['samples'][1].update(frame=20), 'native sample time')

    def test_changed_pose_rejects(self):
        name = self.semantic['objects'][0]['path']
        self.reject(lambda r: r['samples'][0]['objects'][name]['position_m'].__setitem__(0, 4), 'native/decoded position')

    def test_raw_matrix_disagrees_with_converted_pose_rejects(self):
        name = self.semantic['objects'][0]['path']
        self.reject(lambda r: r['samples'][0]['objects'][name]['matrix_world_blender'][0].__setitem__(3, 4), 'raw/source matrix conversion')

    def test_changed_observed_executable_rejects(self):
        self.reject(lambda r: r['build'].update(executable_sha256='0'*64), 'observed Blender build')

    def test_missing_raw_triangle_corner_rejects(self):
        self.reject(lambda r: r['objects'][0]['triangles_raw_blender'][0].pop(), 'triangle vertex count')

    def test_truncated_material_indices_rejects(self):
        self.reject(lambda r: r['objects'][0]['triangle_material_indices'].pop(), 'native material slots')

    def test_material_raw_summary_mismatch_rejects(self):
        self.reject(lambda r: r['objects'][0]['materials'][0]['inputs'].update(Metallic=0.8), 'raw/material summary')

    def test_importer_setting_change_rejects(self):
        self.reject(lambda r: r['import_settings'].update(merge_vertices=True), 'observed importer setting differs')

    def test_triangle_tolerance_is_not_rounding_equality(self):
        triangles = self.reader.triangles(0)
        changed = copy.deepcopy(triangles)
        for triangle in changed:
            for vertex in triangle:
                vertex[0] += 0.0000007
                vertex[3] += 0.0000007
        v.compare_triangles(changed, triangles, 'within fixed tolerance')

    def test_native_loss_is_separate_from_explicit_mapping(self):
        result = self.validate(self.fixture)
        self.assertEqual(result['native_ontokin_property_types'], {'str': 18})
        rows = {r['feature']: r for r in result['losses']}
        self.assertEqual(rows['ownership']['destination_treatment'], 'metadata_only')
        self.assertEqual(rows['live_physics']['destination_treatment'], 'unsupported')
        self.assertEqual(rows['world_motion']['destination_treatment'], 'baked')


if __name__ == '__main__':
    unittest.main()
