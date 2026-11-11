"""Actual source-boundary and canonical controls for the separate C199 adapter.

No native worker, ordinary exporter, simulation or receiving process is used.
"""

import copy
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from ontokin.diagnostics import OntoKinError
from prototypes.static_tray_v01.canonical import (BOUNDS, IDENTITY, ROTATIONS, ROOT, PARTS,
    bits, canonical_bytes, decode_record, geometry_values, json_bytes, number, op,
    record_from_values, record_identity, validate_record)
from prototypes.static_tray_v01.errors import PROFILE, TrayError
from prototypes.static_tray_v01.fixtures import (PARAMETER_NAMES, main_source, module_source,
    qualification_sets, write_sources)
from prototypes.static_tray_v01.sources import lower_source


class StaticTraySourceTests(unittest.TestCase):
    def setUp(self):
        capture = os.environ.get('ONTOKIN_STATIC_TRAY_CAPTURE')
        self.capture = bool(capture)
        if capture:
            self.root = Path(capture) / self._testMethodName
            self.root.mkdir(parents=True, exist_ok=False)
        else:
            self.temp = tempfile.TemporaryDirectory()
            self.addCleanup(self.temp.cleanup)
            self.root = Path(self.temp.name)
        self.serial = 0
        self.record_serial = 0
        self.events = []
        self.current_manifest = None
        self.sets = qualification_sets()

    def tearDown(self):
        if self.capture:
            inventory = []
            for p in sorted(self.root.rglob('*')):
                if p.is_symlink():
                    inventory.append({'path': p.relative_to(self.root).as_posix(), 'symlink_target': os.readlink(p)})
                elif p.is_file():
                    data = p.read_bytes()
                    inventory.append({'path': p.relative_to(self.root).as_posix(), 'size_bytes': len(data),
                                      'sha256': hashlib.sha256(data).hexdigest()})
            (self.root / 'CONTROL-RECEIPT.json').write_text(json.dumps({'method': self._testMethodName,
                'scope': 'Actual source and synthetic canonical controls; zero native starts',
                'rejection_expectations_and_observations': self.events, 'files': inventory}, indent=2) + '\n')

    def manifest(self, route='ontokin', values=None, **options):
        self.serial += 1
        self.current_manifest = write_sources(self.root / str(self.serial), route, values or self.sets['Q01'], **options)
        return self.current_manifest

    def lower(self, route='ontokin', values=None, **options):
        return lower_source(route, self.manifest(route, values, **options), PROFILE)

    def source_change(self, main=None, module=None):
        path = self.manifest()
        if module:
            before = (path.parent / 'tray.ok').read_bytes()
            after = module(before)
            (path.parent / 'tray.ok').write_bytes(after)
            e = (path.parent / 'main.ok').read_bytes().replace(hashlib.sha256(before).hexdigest().encode(), hashlib.sha256(after).hexdigest().encode())
            (path.parent / 'main.ok').write_bytes(e)
        if main:
            (path.parent / 'main.ok').write_bytes(main((path.parent / 'main.ok').read_bytes()))
        return path

    def assert_reject(self, action, codes, *, input_ref=None):
        with self.assertRaises((TrayError, OntoKinError)) as caught:
            action()
        self.assertIn(caught.exception.code, codes)
        self.events.append({'input': input_ref or (str(self.current_manifest.relative_to(self.root)) if self.current_manifest else None),
                            'expected_codes': codes, 'actual_code': caught.exception.code})
        return caught.exception

    def assert_record_reject(self, record, codes):
        return self.assert_bytes_reject(json_bytes(record), codes)

    def assert_bytes_reject(self, data, codes):
        self.record_serial += 1
        name = 'canonical-' + str(self.record_serial) + '.json'
        if self.capture:
            (self.root / name).write_bytes(data)
        return self.assert_reject(lambda: decode_record(data), codes, input_ref=name)

    def test_01_all_five_real_source_pairs_and_frozen_sources(self):
        records = {}
        for case, values in self.sets.items():
            pair = []
            for route in ('ontokin', 'direct-python'):
                with self.subTest(case=case, route=route):
                    r = lower_source(route, ROOT / 'fixtures/static_tray_v01/native' / case / route / 'source.json', PROFILE)
                    self.assertEqual(r.canonical_bytes, canonical_bytes(record_from_values(values)))
                    self.assertEqual(len(r.record['trays']), 2)
                    self.assertEqual(sum(len(t['parts']) for t in r.record['trays']), 12)
                    self.assertEqual(set(r.files), {'main.ok', 'tray.ok'} if route == 'ontokin' else {'main.py', 'tray.py'})
                    pair.append(r)
            self.assertEqual(pair[0].canonical_bytes, pair[1].canonical_bytes)
            self.assertNotEqual(pair[0].provenance['candidate_identity'], pair[1].provenance['candidate_identity'])
            records[case] = pair
        for case in ('Q04', 'Q05'):
            for i in (0, 1):
                self.assertEqual(records['Q01'][i].record['trays'][1], records[case][i].record['trays'][1])
                helper = 'tray.ok' if i == 0 else 'tray.py'
                self.assertEqual(records['Q01'][i].files[helper], records[case][i].files[helper])
                entry = 'main.ok' if i == 0 else 'main.py'
                marker = b' object right' if i == 0 else b'right = '
                self.assertEqual(records['Q01'][i].files[entry].split(marker)[1], records[case][i].files[entry].split(marker)[1])

    def test_02_units_order_renames_and_clean_source_identity(self):
        base = self.lower()
        for options in ({'units': 'mm'}, {'reverse_roots': True}, {'reverse_parts': True}):
            r = self.lower(**options)
            self.assertEqual(base.canonical_bytes, r.canonical_bytes)
            self.assertNotEqual(base.provenance['candidate_identity'], r.provenance['candidate_identity'])
        p = self.source_change(main=lambda b: b.replace(b'object left @', b'object renamed @'))
        self.assertEqual(base.canonical_bytes, lower_source('ontokin', p, PROFILE).canonical_bytes)
        p = self.manifest()
        copy_to = self.root / 'moved'
        shutil.copytree(p.parent, copy_to)
        self.assertEqual(lower_source('ontokin', p, PROFILE).provenance['candidate_identity'],
                         lower_source('ontokin', copy_to / p.name, PROFILE).provenance['candidate_identity'])
        record = json.loads(base.canonical_bytes)
        record = dict(reversed(list(record.items())))
        self.assertEqual(canonical_bytes(record), base.canonical_bytes)
        self.assert_bytes_reject(json.dumps(record).encode(), ['OTRAY-E-RECORD'])

    def test_03_all_catalog_source_rotations_and_sign_twins(self):
        for side in ('left', 'right'):
            for q in ROTATIONS:
                values = copy.deepcopy(self.sets['Q01'])
                values[side]['rotation_wxyz'] = list(q)
                with self.subTest(side=side, quaternion=q):
                    first = self.lower(values=values)
                    second = self.lower(values=values, negate_quaternions=True)
                    self.assertEqual(first.canonical_bytes, second.canonical_bytes)
                    self.assertEqual(first.canonical_bytes, self.lower('direct-python', values).canonical_bytes)

    def test_04_length_boundaries_nextafter_both_routes(self):
        for side in ('left', 'right'):
            for i, (low, high) in enumerate(BOUNDS):
                for edge, value in [('low', math.nextafter(low, -math.inf)), ('high', math.nextafter(high, math.inf))]:
                    values = copy.deepcopy(self.sets['Q01'])
                    if i < 3:
                        values[side]['payload_m'][i] = value
                    else:
                        values[side][('clearance_m', 'wall_m', 'base_m', 'headroom_m')[i - 3]] = value
                    for route in ('ontokin', 'direct-python'):
                        with self.subTest(side=side, field=i, edge=edge, route=route):
                            self.assert_reject(lambda: self.lower(route, values), ['OTRAY-E-RANGE'])

    def test_05_translation_boundaries_nextafter_both_routes(self):
        for side in ('left', 'right'):
            for i in range(3):
                for value in [math.nextafter(-10, -math.inf), math.nextafter(10, math.inf)]:
                    values = copy.deepcopy(self.sets['Q01'])
                    values[side]['translation_m'][i] = value
                    for route in ('ontokin', 'direct-python'):
                        with self.subTest(side=side, component=i, value=value, route=route):
                            self.assert_reject(lambda: self.lower(route, values), ['OTRAY-E-RANGE'])

    def test_06_every_numeric_record_position_strict_types_and_encoding(self):
        original = self.lower().record
        paths = []
        def collect(item, path):
            if isinstance(item, dict):
                for k, v in item.items(): collect(v, path + [k])
            elif isinstance(item, list):
                for k, v in enumerate(item): collect(v, path + [k])
            elif isinstance(item, str) and len(item) == 16:
                try: number(item)
                except TrayError: pass
                else: paths.append(path)
        collect(original, [])
        self.assertEqual(len(paths), 148)
        for path in paths:
            for bad in [0, True, None, '0x1.0p+0', '7ff8000000000000', '7ff0000000000000', 'fff0000000000000', '8000000000000000', '3FF0000000000000']:
                record = copy.deepcopy(original)
                item = record
                for key in path[:-1]: item = item[key]
                item[path[-1]] = bad
                with self.subTest(path=path, bad=bad):
                    self.assert_record_reject(record, ['OTRAY-E-RECORD'])
        for side in range(2):
            for key in ('horizontal_clearance_m', 'wall_thickness_m', 'base_thickness_m', 'headroom_m'):
                for value in (0, -.01):
                    record = copy.deepcopy(original)
                    record['trays'][side]['parameters'][key] = bits(value)
                    self.assert_record_reject(record, ['OTRAY-E-RECORD'])

    def test_07_source_identity_and_structure_mutations(self):
        mutations = [
            (lambda b: b.replace(b'object left @ "left"', b'object left @ "changed"'), None, ['OTRAY-E-IDENTITY']),
            (lambda b: b.replace(b'object right @ "right"', b'object right @ "left"'), None, ['OKL-E-ID']),
            (lambda b: b.replace(b' object right @', b' object extra @ "extra": trays.Tray {}\n object right @'), None, ['OTRAY-E-SHAPE']),
            (None, lambda b: b.replace(b'@ "base": Box', b'@ "lost-base": Box'), ['OTRAY-E-IDENTITY']),
            (None, lambda b: b.replace(b'role = "base"', b'role = "payload-proxy"'), ['OTRAY-E-IDENTITY']),
            (None, lambda b: b.replace(b'public class Tray @ "tray"', b'public class Tray @ "other-tray"'), ['OTRAY-E-SHAPE']),
            (None, lambda b: b.replace(b'public class Tray', b'private class Tray'), ['OKL-E-ACCESS']),
        ]
        for i, (main, module, expected) in enumerate(mutations):
            with self.subTest(variant=i):
                p = self.source_change(main, module)
                self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), expected)

    def test_08_actual_rotation_and_pose_authority_rejections(self):
        for replacement, code in ((b'axis_angle(vec3(0, 1, 0), 90[deg])', 'OTRAY-E-ROTATION'),
                                  (b'quat(2, 0, 0, 0)', 'OKL-E-ROTATION')):
            p = self.source_change(main=lambda b: b.replace(b'quat(1, 0, 0, 0)', replacement, 1))
            self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), [code])
        p = self.source_change(module=lambda b: b.replace(b'extent = vec3(self.OX, self.base_thickness, self.OZ);',
            b'extent = vec3(self.OX, self.base_thickness, self.OZ); placement = pose(world, vec3(0[m],0[m],0[m]),quat(1,0,0,0));'))
        self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OKL-E-POSE-AUTHORITY'])
        p = self.source_change(module=lambda b: b.replace(b'parent = self.frame;', b'parent = world;', 1).replace(b'offset = pose(self.frame,', b'offset = pose(world,', 1))
        self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-RELATIONSHIP'])
        def remove_follows(data):
            # Fixture generation knows the exact authored block delimiters.
            text = data.decode()
            import re
            return re.sub(r' private follow [^}]+}', '', text).encode()
        p = self.source_change(module=remove_follows)
        self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-SHAPE'])

    def test_09_unsupported_physics_motion_material_and_constructs(self):
        mutations = [
            (None, lambda b: b.replace(b'motion = prescribed;', b'motion = dynamic;', 1), ['OKL-E-PHYSICAL-DOMAIN']),
            (None, lambda b: b.replace(b'physical = no_body();', b'physical = sphere_body(0.1[m], 1[kg]);', 1), ['OKL-E-PHYSICAL-DOMAIN', 'OTRAY-E-PHYSICS']),
            (None, lambda b: b.replace(b'collision = disabled;', b'collision = enabled;', 1), ['OKL-E-NAME']),
            (lambda b: b.replace(b'vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2])', b'vector(world, 0[m/s^2], -9.8[m/s^2], 0[m/s^2])'), None, ['OTRAY-E-PHYSICS']),
            (None, lambda b: b.replace(b'rgba(0.25, 0.5, 0.75, 1)', b'rgba(0.26, 0.5, 0.75, 1)'), ['OTRAY-E-MATERIAL']),
            (None, lambda b: b.replace(b'geometry = box(self.extent);', b'geometry = sphere(0.1[m]);'), ['OTRAY-E-SHAPE']),
            (None, lambda b: b.replace(b'physical = no_body();', b'velocity = vector(world,0[m/s],0[m/s],0[m/s]); physical = no_body();', 1), ['OTRAY-E-RELATIONSHIP']),
            (lambda b: b.replace(b' duration = 1[s];', b' duration = 1[s];\n action movement @ "movement" = move(left,vector(world,1[m/s],0[m/s],0[m/s]),1[s]);'), None, ['OTRAY-E-MOTION', 'OTRAY-E-SHAPE']),
            (None, lambda b: b.replace(b'private class Box', b'private class Extra @ "extra" {}\nprivate class Box'), ['OTRAY-E-SHAPE']),
        ]
        for i, (main, module, codes) in enumerate(mutations):
            with self.subTest(variant=i):
                p = self.source_change(main, module)
                self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), codes)

    def test_10_wrong_source_geometry_is_not_reconstructed(self):
        p = self.source_change(module=lambda b: b.replace(b'extent = vec3(self.OX, self.base_thickness, self.OZ);',
                                                       b'extent = vec3(self.OX / 2, self.base_thickness, self.OZ);'))
        self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-SHAPE'])
        p = self.source_change(module=lambda b: b.replace(b'extent = vec3(self.wall_thickness, self.H, self.D);',
                                                       b'extent = vec3(self.wall_thickness, self.H, self.OZ);', 1))
        self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-SHAPE'])
        record = self.lower().record
        for key in PARTS:
            changed = copy.deepcopy(record)
            part = next(p for p in changed['trays'][0]['parts'] if p['key'] == key)
            part['geometry']['size_m'] = [bits(number(v) / 2) for v in part['geometry']['size_m']]
            self.assert_record_reject(changed, ['OTRAY-E-SHAPE'])

    def test_11_closed_pins_paths_sizes_and_imports(self):
        for mutation in ('changed', 'missing', 'extra', 'path', 'version', 'symlink', 'oversize'):
            p = self.manifest()
            module = p.parent / 'tray.ok'
            if mutation == 'changed': module.write_bytes(module.read_bytes() + b'\n')
            elif mutation == 'missing': module.unlink()
            elif mutation == 'extra': (p.parent / 'extra.ok').write_bytes(b'')
            elif mutation in ('path', 'version'):
                manifest = json.loads(p.read_bytes())
                manifest['modules'][0]['path' if mutation == 'path' else 'version'] = '../tray.ok' if mutation == 'path' else '9.0.0'
                p.write_bytes(json_bytes(manifest))
            elif mutation == 'symlink':
                elsewhere = self.root / 'elsewhere.ok'
                elsewhere.write_bytes(module.read_bytes()); module.unlink(); module.symlink_to('../elsewhere.ok')
            else: module.write_bytes(b' ' * 32769)
            with self.subTest(mutation=mutation):
                self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-CLOSURE'])
        p = self.manifest('direct-python')
        (p.parent / 'tray.py').write_bytes((p.parent / 'tray.py').read_bytes() + b'\n')
        self.assert_reject(lambda: lower_source('direct-python', p, PROFILE), ['OTRAY-E-CLOSURE'])

    def test_12_noncanonical_records_identifiers_and_full_source_scale(self):
        raw = self.lower().canonical_bytes
        for bad in (raw + b'\n', b'\xef\xbb\xbf' + raw, raw + b'{}', raw[:-1],
                    raw.replace(b'"contract":', b'"extra":0,"contract":', 1),
                    raw.replace(b'"contract":', b'"contract":"wrong","contract":', 1)):
            self.assert_bytes_reject(bad, ['OTRAY-E-RECORD'])
        record = json.loads(raw)
        for field, value in [('id', ['equipment-tray', 'pair', 'right']), ('role', 'wrong'), ('owner_id', ['equipment-tray', 'pair', 'right'])]:
            changed = copy.deepcopy(record)
            changed['trays'][0]['parts'][0][field] = value
            self.assert_record_reject(changed, ['OTRAY-E-RECORD'])
        for q in ([.7071067811865476, 0, .7071067811865476, 0], [2, 0, 0, 0], [-1, 0, 0, 0]):
            changed = copy.deepcopy(record)
            changed['trays'][0]['root_pose']['rotation_wxyz'] = [bits(v) for v in q]
            self.assert_record_reject(changed, ['OTRAY-E-RECORD'])
        values = copy.deepcopy(self.sets['Q01']); values['left']['payload_m'][0] = 200
        for route in ('ontokin', 'direct-python'):
            self.assert_reject(lambda: self.lower(route, values), ['OTRAY-E-RANGE'])

    def test_13_direct_identity_and_actual_reusable_helper_calls(self):
        r = self.lower('direct-python')
        manifest = r.provenance['source_manifest']
        expected = 'sha256:' + hashlib.sha256(b'ontokin.static-tray.python-sources/0.1.0\0' + json_bytes(manifest)).hexdigest()
        self.assertEqual(expected, r.provenance['candidate_identity'])
        self.assertNotIn('program_revision', r.provenance)
        self.assertEqual(r.provenance['helper_calls'], ['left', 'right'])
        for mutation, expected in [('record["trays"][0]["geometry"] = "changed"\n', 'OTRAY-E-RECORD'),
                                   ('make_tray("left", left)\n', 'OTRAY-E-SHAPE'),
                                   ('from pathlib import Path\n', 'OTRAY-E-CLOSURE')]:
            p = self.manifest('direct-python')
            file = p.parent / 'main.py'; file.write_bytes(file.read_bytes() + mutation.encode())
            manifest = json.loads(p.read_bytes())
            manifest['files'][0]['source_revision'] = 'sha256:' + hashlib.sha256(file.read_bytes()).hexdigest()
            manifest['files'][0]['size_bytes'] = len(file.read_bytes())
            p.write_bytes(json_bytes(manifest))
            self.assert_reject(lambda: lower_source('direct-python', p, PROFILE), [expected])

    def test_14_numeric_order_selector_and_diagnostic_binding(self):
        self.assertEqual(bits(op(.2, '+', op(2, '*', .005))), '3fcae147ae147ae2')
        self.assertEqual(bits(-0.), '0000000000000000')
        self.assertNotEqual(op(.2, '+', op(2, '*', .005)), float(Fraction('0.20') + 2 * Fraction('0.005')))
        p = self.manifest()
        self.assert_reject(lambda: lower_source('ontokin', p, None), ['OTRAY-E-PROFILE'])
        p = self.source_change(module=lambda b: b.replace(b'rgba(0.25, 0.5, 0.75, 1)', b'rgba(0.26, 0.5, 0.75, 1)'))
        e = self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-MATERIAL'])
        self.assertTrue(e.candidate.startswith('sha256:'))
        self.assertTrue(all('source' in finding for finding in e.findings))
        for finding in e.findings:
            self.assertLess(finding['source']['start_byte'], finding['source']['end_byte'])

    def test_15_complete_identity_and_positive_parameter_mutations(self):
        original = self.lower().record
        for side in range(2):
            for axis in range(3):
                for value in (0, -.01):
                    record = copy.deepcopy(original)
                    record['trays'][side]['parameters']['payload_size_m'][axis] = bits(value)
                    self.assert_record_reject(record, ['OTRAY-E-RECORD'])
            for mutation in ('omit-root', 'duplicate-root', 'extra-root', 'root-role',
                             'omit-part', 'duplicate-part', 'extra-part', 'rename-part', 'alias-part',
                             'swap-owner', 'wrong-follow-id', 'wrong-follow-parent', 'missing-follow'):
                record = copy.deepcopy(original)
                tray = record['trays'][side]
                if mutation == 'omit-root': record['trays'].pop(side)
                elif mutation == 'duplicate-root': record['trays'][side] = copy.deepcopy(record['trays'][1 - side])
                elif mutation == 'extra-root': record['trays'].append(copy.deepcopy(tray))
                elif mutation == 'root-role': tray['role'] = 'payload-proxy'
                elif mutation == 'omit-part': tray['parts'].pop(1)
                elif mutation == 'duplicate-part': tray['parts'][1] = copy.deepcopy(tray['parts'][0])
                elif mutation == 'extra-part': tray['parts'].append(copy.deepcopy(tray['parts'][0]))
                elif mutation == 'rename-part': tray['parts'][1]['id'][-1] = 'renamed'
                elif mutation == 'alias-part': tray['parts'][1]['id'] = list(tray['parts'][0]['id'])
                elif mutation == 'swap-owner': tray['parts'][1]['owner_id'][-1] = ('right', 'left')[side]
                elif mutation == 'wrong-follow-id': tray['parts'][1]['following']['id'][-1] = 'follow-front'
                elif mutation == 'wrong-follow-parent': tray['parts'][1]['following']['parent_id'][-1] = ('right', 'left')[side]
                else: del tray['parts'][1]['following']
                with self.subTest(side=side, mutation=mutation):
                    self.assert_record_reject(record, ['OTRAY-E-RECORD'])
            for name, value in [('scale', [bits(2), bits(1), bits(1)]),
                                ('matrix', [bits(-1)] * 16), ('shear', bits(.1))]:
                record = copy.deepcopy(original)
                record['trays'][side]['root_pose'][name] = value
                self.assert_record_reject(record, ['OTRAY-E-RECORD'])

    def test_16_additional_compiler_authority_and_unsupported_controls(self):
        extra_follow = b' private follow duplicate @ "duplicate" { parent = self.frame; child = self.base; offset = pose(self.frame,vec3(0[m],0[m],0[m]),quat(1,0,0,0)); }\n'
        cycle_follow = b' private follow cycle @ "cycle" { parent = self.base.frame; child = self; offset = pose(self.base.frame,vec3(0[m],0[m],0[m]),quat(1,0,0,0)); }\n'
        for follow, code in ((extra_follow, 'OKL-E-POSE-AUTHORITY'), (cycle_follow, 'OKL-E-FOLLOW-CYCLE')):
            p = self.source_change(module=lambda b: b.rsplit(b'}', 1)[0] + follow + b'}\n')
            self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), [code])
        def without_one_follow(data):
            import re
            return re.sub(rb' private follow follow_base [^}]+}', b'', data)
        p = self.source_change(module=without_one_follow)
        self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-SHAPE'])
        for replacement in (b'geometry = imported_mesh("no.mesh");', b'geometry = force(1);',
                            b'geometry = texture("no.png");'):
            p = self.source_change(module=lambda b: b.replace(b'geometry = box(self.extent);', replacement))
            self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OKL-E-NAME'])
        p = self.source_change(module=lambda b: b.replace(b'physical = no_body();',
            b'physical = no_body(); public site extra @ "extra" { pose = pose(self.frame,vec3(0[m],0[m],0[m]),quat(1,0,0,0)); interface = "rigid.origin"; size = 0[m]; }', 1))
        self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-SHAPE'])
        p = self.source_change(main=lambda b: b.replace(b' duration = 1[s];',
            b' duration = 1[s]; action movement @ "movement" = move(left,vector(world,1[m/s],0[m/s],0[m/s]),1[s]); at 0[s] sequence { start movement; }'))
        self.assert_reject(lambda: lower_source('ontokin', p, PROFILE), ['OTRAY-E-MOTION', 'OTRAY-E-SHAPE'])

    def test_17_direct_output_binding_ambient_import_and_work_budget(self):
        for extra, code in [(b'while True:\n    pass\n', 'OTRAY-E-RESOURCE'),
                            (b'from os import system\n', 'OTRAY-E-CLOSURE'),
                            (b'record["trays"][0]["geometry"] = "empty"\nrecord["trays"][0]["parameters"]["headroom_m"] = "3f947ae147ae147c"\n', 'OTRAY-E-BINDING'),
                            (b'try:\n    pass\nexcept:\n    pass\n', 'OTRAY-E-SHAPE')]:
            p = self.manifest('direct-python')
            f = p.parent / 'main.py'
            f.write_bytes(f.read_bytes() + extra)
            m = json.loads(p.read_bytes()); m['files'][0]['source_revision'] = 'sha256:' + hashlib.sha256(f.read_bytes()).hexdigest(); m['files'][0]['size_bytes'] = len(f.read_bytes())
            p.write_bytes(json_bytes(m))
            self.assert_reject(lambda: lower_source('direct-python', p, PROFILE), [code])

    def test_18_direct_dictionary_insertion_and_source_error_diagnostics(self):
        original = self.lower('direct-python')
        p = self.manifest('direct-python')
        f = p.parent / 'main.py'
        f.write_bytes(f.read_bytes() + b'record = {"trays": record["trays"], **record}\n')
        manifest = json.loads(p.read_bytes())
        manifest['files'][0]['source_revision'] = 'sha256:' + hashlib.sha256(f.read_bytes()).hexdigest()
        manifest['files'][0]['size_bytes'] = len(f.read_bytes())
        p.write_bytes(json_bytes(manifest))
        changed = lower_source('direct-python', p, PROFILE)
        self.assertEqual(changed.canonical_bytes, original.canonical_bytes)
        self.assertNotEqual(changed.provenance['candidate_identity'], original.provenance['candidate_identity'])
        self.assertGreater(changed.provenance['source_trace_events'], 0)
        for invalid, code in [(b'bad syntax !\n', 'OTRAY-E-SHAPE'), (b'1 / 0\n', 'OTRAY-E-NUMERIC')]:
            p = self.manifest('direct-python'); f = p.parent / 'main.py'
            f.write_bytes(f.read_bytes() + invalid)
            m = json.loads(p.read_bytes()); m['files'][0]['source_revision'] = 'sha256:' + hashlib.sha256(f.read_bytes()).hexdigest(); m['files'][0]['size_bytes'] = len(f.read_bytes())
            p.write_bytes(json_bytes(m))
            self.assert_reject(lambda: lower_source('direct-python', p, PROFILE), [code])


if __name__ == '__main__':
    unittest.main()
