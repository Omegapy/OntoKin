"""Bounded authored ring summaries without editable derived triangle identities."""
from .profile_capabilities import HOLES_PROFILE


def holes_summary(geometry, *, check=None):
    recipe = geometry.get('surface', geometry)
    counts = {}
    for material in recipe['materials']:
        if check is not None:
            check()
        counts[material.key] = 0
    rings = []
    n = h = 0
    for ring in sorted(recipe['rings'], key=lambda item: item.order):
        if check is not None:
            check()
        vertices = []
        h += ring.role == 'hole'
        for vertex in sorted(ring.vertices, key=lambda item: item.order):
            if check is not None:
                check()
            vertices.append({'key': vertex.key, 'order': vertex.order,
                             'point_m': list(vertex.point_m), 'side_region': vertex.region})
            counts[vertex.region] += 2
            n += 1
        rings.append({'key': ring.key, 'order': ring.order, 'role': ring.role, 'vertices': vertices})
    caps = n + 2 * h - 2
    counts[recipe['bottom_region']] += caps
    counts[recipe['top_region']] += caps
    triangles = 4 * n + 4 * h - 4
    regions = []
    for key in sorted(counts):
        if check is not None:
            check()
        if counts[key]:
            regions.append({'key': key, 'material_key': key, 'triangle_count': counts[key]})
    return {'schema_version': 'ontokin.polygon-holes-summary/0.1',
            'profile': HOLES_PROFILE, 'family': 'polygon_holes', 'rings': rings,
            'ring_count': len(rings), 'hole_count': h, 'authored_vertex_count': n,
            'depth_m': recipe['depth_m'], 'bottom_region': recipe['bottom_region'],
            'top_region': recipe['top_region'], 'palette_keys': sorted(counts),
            'cap_triangle_count': caps, 'palette_count': len(counts),
            'used_region_count': len(regions),
            'triangle_count': triangles, 'vertex_count': 3 * triangles,
            'regions': regions,
            'local_visual_placement': {'frame': 'carrier_self_frame',
                'position_m': list(geometry.get('local_position', (0., 0., 0.))),
                'orientation_wxyz': list(geometry.get('local_rotation', (1., 0., 0., 0.)))},
            'physical_participation': 'none',
            'motion_authority': 'carrier_evaluated_world_pose'}
