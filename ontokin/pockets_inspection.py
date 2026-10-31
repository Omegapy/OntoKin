"""Bounded source summaries retaining authored and actual pocket floor depths."""
from .pockets import _floor_details
from .profile_capabilities import POCKETS_PROFILE


def _rational(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def pockets_summary(geometry, *, check=None):
    """Describe an admitted immutable recipe without rebuilding its mesh."""
    def tick():
        if check is not None:
            check()

    recipe = geometry.get('surface', geometry)
    counts = {}
    for material in recipe['materials']:
        tick()
        counts[material.key] = 0

    def vertices(raw):
        result = []
        for vertex in sorted(raw, key=lambda value: value.order):
            tick()
            result.append({'key': vertex.key, 'order': vertex.order,
                           'point_m': list(vertex.point_m), 'side_region': vertex.region})
            counts[vertex.region] += 2
        return result

    outer = vertices(recipe['outer_vertices'])
    pockets = []
    authored = len(outer)
    floor_count = 0
    for pocket in sorted(recipe['pockets'], key=lambda value: value.order):
        tick()
        points = vertices(pocket.vertices)
        authored += len(points)
        floor_count += len(points) - 2
        counts[pocket.floor_region] += len(points) - 2
        depth, floor, base, effective = _floor_details(
            recipe['height_m'], pocket.depth_m, check=check, pocket=pocket.key)
        pockets.append({'key': pocket.key, 'order': pocket.order, 'vertices': points,
                        'depth_m': depth, 'floor_region': pocket.floor_region,
                        'floor_m': floor, 'remaining_base_m': floor,
                        'exact_remaining_base_m': _rational(base),
                        'effective_depth_m': _rational(effective)})
    bottom_count = len(outer) - 2
    top_count = authored + 2 * len(pockets) - 2
    wall_count = 2 * authored
    counts[recipe['bottom_region']] += bottom_count
    counts[recipe['top_region']] += top_count
    regions = []
    for key in sorted(counts):
        tick()
        if counts[key]:
            regions.append({'key': key, 'material_key': key, 'triangle_count': counts[key]})
    triangles = 4 * authored - 4
    return {'schema_version': 'ontokin.polygon-pockets-summary/0.1',
            'profile': POCKETS_PROFILE, 'family': 'polygon_pockets',
            'height_m': recipe['height_m'], 'outer_vertices': outer, 'pockets': pockets,
            'pocket_count': len(pockets), 'authored_vertex_count': authored,
            'logical_vertex_count': 2 * authored,
            'bottom_triangle_count': bottom_count, 'top_triangle_count': top_count,
            'floor_triangle_count': floor_count, 'wall_triangle_count': wall_count,
            'triangle_count': triangles, 'vertex_count': 3 * triangles,
            'bottom_region': recipe['bottom_region'], 'top_region': recipe['top_region'],
            'palette_keys': sorted(counts), 'palette_count': len(counts),
            'used_region_count': len(regions), 'regions': regions,
            'local_visual_placement': {
                'frame': 'carrier_self_frame',
                'position_m': list(geometry.get('local_position', (0.0, 0.0, 0.0))),
                'orientation_wxyz': list(geometry.get('local_rotation', (1.0, 0.0, 0.0, 0.0)))},
            'physical_participation': 'none', 'motion_authority': 'carrier_evaluated_world_pose'}
