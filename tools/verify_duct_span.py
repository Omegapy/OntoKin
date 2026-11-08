"""Independently measure both signed C165 joints from rendered GLB triangles."""
import argparse
import hashlib
import json
import math
from pathlib import Path

if __package__:
    from .verify_connected_duct import PortFrame, port, rectangular_overlap, require
    from .verify_duct_placement import endpoints
else:
    from verify_connected_duct import PortFrame, port, rectangular_overlap, require
    from verify_duct_placement import endpoints

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/connected-duct'
NAMES = ('outbound', 'link', 'inbound', 'bypass')


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


# Literal palette in the frozen parts-span.ok, independent of either GLB.
RGBA = {'bottom': [.3, .35, .4, 1], 'inner': [.15, .65, .3, 1],
        'outer': [.7, .3, .1, 1], 'top': [.1, .5, .8, 1]}


def scene(data):
    glb, nodes, faces = endpoints(data, NAMES)
    doc = glb.document
    require(not doc.get('extensionsUsed') and not doc.get('extensionsRequired'), 'Unexpected GLB extension')
    require(not any(k in doc for k in ('textures', 'images', 'samplers', 'skins')), 'Expected untextured rigid geometry')
    require(len(doc['nodes']) == len(nodes), 'Unexpected inactive nodes')
    program = doc['extras']['ontokin']['program']
    require(set(program['occurrences']) == set(nodes), 'Unexpected occurrence inventory')
    parts_id = 'package:example.connected-duct-parts@1.1.0'
    sources = program['sources']
    require(set(sources) == {'entry', parts_id} and program['entry_source_id'] == 'entry',
            'Unexpected source inventory')
    parts = sources[parts_id]
    require(parts['package_id'] == 'example.connected-duct-parts' and parts['version'] == '1.1.0'
            and parts['filename'] == 'parts-span.ok' and parts['source_revision'] == digest((EXAMPLE / 'parts-span.ok').read_bytes())
            and parts['module_key'] == 'duct-parts' and parts['module_name'] == 'DuctParts', 'Unexpected parts identity')
    require(sources['entry']['filename'] == 'span-achievable.ok' and sources['entry']['module_key'] == 'connected-duct',
            'Unexpected entry identity')
    units = program['manifest']['units']
    require(len(units) == len(sources) and {u['source_id'] for u in units} == set(sources)
            and all(all(sources[u['source_id']].get(k) == u[k] for k in
                        ('source_id', 'source_revision', 'filename', 'package_id', 'version')) for u in units),
            'Source manifest differs')
    for name, node in nodes.items():
        require(not any(k in node for k in ('scale', 'children', 'matrix', 'skin', 'weights')), 'Unsupported node transform')
        identity = node['extras']['ontokin']
        mapping = identity['source_mapping']
        kind = 'straight' if name == 'link' else 'elbow'
        definition_id = ['package', 'example.connected-duct-parts', 'duct-parts', 'definitions', kind]
        element_id = ['connected-duct', 'demo', name]
        require(mapping == program['occurrences'][name] and identity['path'] == mapping['path'] == name
                and mapping['definition_id'] == definition_id and
                mapping['class_id'] == identity['class_name'] == '/'.join(definition_id)
                and mapping['element_id'] == identity['element_id'] == element_id and
                identity['program_revision'] == program['revision'], name + ' occurrence mapping differs')
        for field, source_id in [('declaration', 'entry'), ('definition', parts_id)]:
            loc = mapping[field]
            require(loc['source_id'] == source_id and all(loc[k] == sources[source_id][k]
                    for k in ('filename', 'source_revision')), name + ' mapped source differs')
        mesh = glb.reference('meshes', node['mesh'])
        require('weights' not in mesh, name + ' unexpected morph weights')
        expected_palette = [{'key': key, 'rgba': rgba, 'metallic': .1, 'roughness': .65} for key, rgba in RGBA.items()]
        require(identity['geometry']['materials'] == expected_palette, name + ' palette differs from frozen source')
        seen = set()
        for prim in mesh['primitives']:
            region = prim['extras']['ontokin']['region_key']
            require(region in RGBA and region not in seen, name + ' unexpected or duplicate region')
            seen.add(region)
            require(prim.get('mode', 4) == 4 and not any(k in prim for k in ('targets', 'extensions')) and
                    set(prim['attributes']) == {'POSITION', 'NORMAL'}, name + ' expected rigid triangles')
            mat = glb.reference('materials', prim['material'])
            require(set(mat) == {'name', 'pbrMetallicRoughness', 'extras'} and mat['name'] == f'{name}: {region}'
                    and mat['pbrMetallicRoughness'] == {'baseColorFactor': RGBA[region],
                    'metallicFactor': .1, 'roughnessFactor': .65}, name + ' rendered material differs from frozen source')
            source = mat['extras']['ontokin']
            require(source['program_revision'] == program['revision'] and source['occurrence_path'] == name
                    and source['source_region_key'] == region and source['element_id'] == element_id,
                    name + ' material mapping differs')
        require(seen == RGBA.keys(), name + ' missing material region')
    return glb, nodes, faces


def joint(glb, nodes, faces, pair, center, spec, *, axes=((1, 0, 0), (0, 1, 0), (0, 0, 1))):
    frame = PortFrame(tuple(center), axes)
    tol = spec['maximum_rim_error_m']
    normal_tol = spec['maximum_unit_normal_error']
    area_tol = spec['area_tolerance_m2']
    sides = {}
    observed_centers = [faces[name, cap][0] for name, cap in pair]
    row = {'parts': pair, 'center_distance_m': math.dist(*observed_centers), 'passed': False}
    try:
        for name, cap in pair:
            sign = 1 if cap == 'top' else -1
            sides[name] = port(glb, nodes[name], spec['inner_side_m'], frame, name, cap=(cap, sign))
        first, second = sides.values()
        rim_errors = {rim: max(math.dist(a, b) for a, b in zip(first[rim], second[rim]))
                      for rim in ('outer_loop_m', 'inner_loop_m')}
        overlap = rectangular_overlap(sides)
        row.update(max_outer_rim_separation_m=rim_errors['outer_loop_m'],
                   max_inner_rim_separation_m=rim_errors['inner_loop_m'], common_open_area_m2=overlap,
                   opposed_normal_error=math.dist(first['cap_normal'], [-v for v in second['cap_normal']]))
        for side in sides.values():
            for rim in rim_errors:
                side[rim] = [frame.world(p) for p in side[rim]]
            side['inner_center_m'] = frame.world(side['inner_center_m'])
            side['cap_normal'] = frame.vector(side['cap_normal'])
        row['ports'] = sides
        require(max(rim_errors.values()) <= tol, 'Rim separation exceeds tolerance')
        require(all(s['max_expected_corner_distance_m'] <= tol for s in sides.values()), 'Rim differs from freeze')
        require(row['opposed_normal_error'] <= normal_tol and all(s['max_normal_error'] <= normal_tol for s in sides.values()),
                'Cap winding differs')
        require(all(not s['intersects_required_opening'] for s in sides.values()), 'Triangles obstruct opening')
        require(all(abs(s['annulus_area_m2'] - (spec['outer_side_m']**2 - spec['common_area_m2'])) <= area_tol and
                    abs(s['clear_area_m2'] - spec['common_area_m2']) <= area_tol for s in sides.values()), 'Cap area differs')
        require(overlap is not None and abs(overlap - spec['common_area_m2']) <= area_tol, 'Common area differs')
        row['passed'] = True
    except ValueError as exc:
        row['failure'] = str(exc)
        if hasattr(exc, 'measurements'):
            row['failure_measurements'] = exc.measurements
    return row


def verify(before, after, expected_end='inbound'):
    spec = json.loads((EXAMPLE / 'span-contract.json').read_text())
    original, initial_nodes, initial_faces = scene(before)
    glb, nodes, faces = scene(after)
    require(original.document['extras']['ontokin']['program']['sources']['entry']['source_revision'] ==
            digest((EXAMPLE / 'span-achievable.ok').read_bytes()), 'Initial entry differs from freeze')
    for name in NAMES:
        if name != 'link':
            require(all(nodes[name][k] == initial_nodes[name][k] for k in ('translation', 'rotation')), name + ' moved')
    fixed = lambda streams: {k: v for k, v in streams.items() if k[0] != 'link'}
    require(fixed(glb.geometry_streams()) == fixed(original.geometry_streams()), 'Stationary geometry changed')
    span = lambda f: math.dist(f['link', 'top'][0], f['link', 'bottom'][0])
    tol = spec['maximum_rim_error_m']
    require(abs(span(initial_faces) - spec['initial_span_m']) <= tol, 'Initial rendered span differs')
    start = spec['achievable']['start_center_m']
    end = spec['achievable']['end_center_m'] if expected_end == 'inbound' else spec['bypass_end_center_m']
    req = spec['request']
    joints = {'upstream': joint(glb, nodes, faces, [req['upstream'], req['inlet']], start, spec),
              'downstream': joint(glb, nodes, faces, [req['outlet'], [expected_end, 'bottom']], end, spec)}
    return {'passed': all(j['passed'] for j in joints.values()) and abs(span(faces) - math.dist(start, end)) <= tol,
            'before_sha256': digest(before), 'after_sha256': digest(after), 'initial_span_m': span(initial_faces),
            'rendered_span_m': span(faces), 'required_span_m': math.dist(start, end),
            'stationary_geometry_preserved': True, 'joints': joints}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--expected-end', choices=('inbound', 'bypass'), default='inbound')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = verify(args.before.read_bytes(), args.after.read_bytes(), args.expected_end)
    except (ValueError, KeyError, IndexError, ZeroDivisionError) as error:
        report = {'passed': False, 'failure': str(error)}
    rendered = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end='')
    raise SystemExit(0 if report['passed'] else 1)
