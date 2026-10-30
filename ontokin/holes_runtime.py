"""Typed source constructors for keyed outer and inner polygon rings."""
from .extrusion import PolygonVertex
from .surface import SurfaceMaterial
from .validator import fail
from .values import INT, STRING, LENGTH, Type, Value, quantity_type

HOLES_TYPES = frozenset({'PolygonRing'})
HOLES_CALLS = frozenset({'polygon_ring', 'extrude_rings'})


def holes_builtin(compiler, name, args, node, ctx):
    types = {
        'polygon_ring': [INT, STRING, Type('Keyed', element=Type('PolygonVertex'))],
        'extrude_rings': [Type('Keyed', element=Type('PolygonRing')),
                          Type('Keyed', element=Type('SurfaceMaterial')),
                          quantity_type(LENGTH), STRING, STRING],
    }
    returns = {'polygon_ring': Type('PolygonRing'), 'extrude_rings': Type('Geometry')}
    expected = types[name]
    if len(args) != len(expected):
        fail('OKL-E-TYPE', f'{name} requires {len(expected)} positional arguments.',
             node, phase='type', details={'received': len(args)})
    values = [compiler.expect(arg, typ, node.args[i])
              for i, (arg, typ) in enumerate(zip(args, expected))]
    if ctx.abstract or not all(value.known for value in values):
        return Value(returns[name])
    raw = [value.value for value in values]
    if name == 'polygon_ring':
        vertices = tuple(PolygonVertex(key, *value.value) for key, value in raw[2].entries)
        return Value(Type('PolygonRing'), (raw[0], raw[1], vertices))
    from .holes import PolygonRing
    return Value(Type('Geometry'), {
        'kind': 'holes',
        'rings': tuple(PolygonRing(key, *value.value) for key, value in raw[0].entries),
        'materials': tuple(SurfaceMaterial(key, *value.value) for key, value in raw[1].entries),
        'depth_m': raw[2], 'bottom_region': raw[3], 'top_region': raw[4],
        'source_id': node.source_id, 'start': node.start, 'end': node.end,
    })
