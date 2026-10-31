"""Bounded authored frame and ring summaries for the explicit .11 profile."""
from .profile_capabilities import FRAMED_LOFT_PROFILE


def framed_loft_summary(geometry, *, check=None):
    """Describe an admitted recipe without rebuilding its derived triangles."""
    def tick():
        if check is not None:
            check()

    recipe = geometry.get('surface', geometry)
    counts = {}
    for material in recipe['materials']:
        tick()
        counts[material.key] = 0
    ordered = sorted(recipe['sections'], key=lambda section: section.order)
    sections = []
    authored = vertices_per_section = hole_count = ring_count = 0
    for index, section in enumerate(ordered):
        tick()
        rings = []
        vertices_here = holes_here = 0
        for ring in sorted(section.rings, key=lambda item: item.order):
            tick()
            vertices = []
            holes_here += ring.role == 'hole'
            for vertex in sorted(ring.vertices, key=lambda item: item.order):
                tick()
                vertices.append({'key': vertex.key, 'order': vertex.order,
                                 'point_m': list(vertex.point_m), 'side_region': vertex.region})
                vertices_here += 1
                if index + 1 < len(ordered):
                    counts[vertex.region] += 2
            rings.append({'key': ring.key, 'order': ring.order, 'role': ring.role, 'vertices': vertices})
        authored += vertices_here
        if index == 0:
            vertices_per_section, hole_count, ring_count = vertices_here, holes_here, len(rings)
        orientation = tuple(0.0 if value == 0 else value for value in section.frame.rotation)
        if next((value for value in orientation if value), 1.0) < 0:
            orientation = tuple(0.0 if value == 0 else -value for value in orientation)
        sections.append({'key': section.key, 'order': section.order,
                         'frame': 'carrier_self_frame', 'origin_m': list(section.frame.position),
                         'orientation_wxyz': list(orientation), 'rings': rings})
    caps = vertices_per_section + 2 * hole_count - 2
    strips = 2 * (len(sections) - 1) * vertices_per_section
    counts[recipe['bottom_region']] += caps
    counts[recipe['top_region']] += caps
    regions = []
    for key in sorted(counts):
        tick()
        if counts[key]:
            regions.append({'key': key, 'material_key': key, 'triangle_count': counts[key]})
    triangles = strips + 2 * caps
    return {'schema_version': 'ontokin.framed-polygon-loft-summary/0.1',
        'profile': FRAMED_LOFT_PROFILE, 'family': 'framed_polygon_loft',
        'surface_rule': 'fixed-diagonal-triangles',
        'section_transform_rule': 'exact-rational-quaternion-single-round',
        'sections': sections, 'section_count': len(sections), 'ring_count': ring_count,
        'hole_count': hole_count, 'vertices_per_section': vertices_per_section,
        'authored_vertex_count': authored,
        'bottom_region': recipe['bottom_region'], 'top_region': recipe['top_region'],
        'palette_keys': sorted(counts), 'palette_count': len(counts),
        'used_region_count': len(regions), 'cap_triangle_count': caps,
        'strip_triangle_count': strips, 'triangle_count': triangles,
        'vertex_count': 3 * triangles, 'regions': regions,
        'local_visual_placement': {'frame': 'carrier_self_frame',
            'position_m': list(geometry.get('local_position', (0., 0., 0.))),
            'orientation_wxyz': list(geometry.get('local_rotation', (1., 0., 0., 0.)))},
        'physical_participation': 'none', 'motion_authority': 'carrier_evaluated_world_pose'}
