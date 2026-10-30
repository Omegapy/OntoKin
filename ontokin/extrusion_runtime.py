"""Typed source constructors for rigid visual polygon extrusions."""
from .extrusion import PolygonVertex
from .surface import SurfaceMaterial
from .validator import fail
from .values import INT, STRING, LENGTH, Type, Value, quantity_type

EXTRUSION_TYPES = frozenset({'PlanarPoint', 'PolygonVertex'})
EXTRUSION_CALLS = frozenset({'planar_point', 'polygon_vertex', 'extrude'})


def extrusion_builtin(compiler, name, args, node, ctx):
    types = {
        'planar_point': [quantity_type(LENGTH), quantity_type(LENGTH)],
        'polygon_vertex': [INT, Type('PlanarPoint'), STRING],
        'extrude': [Type('Keyed', element=Type('PolygonVertex')),
                    Type('Keyed', element=Type('SurfaceMaterial')),
                    quantity_type(LENGTH), STRING, STRING],
    }
    returns = {'planar_point': Type('PlanarPoint'), 'polygon_vertex': Type('PolygonVertex'),
               'extrude': Type('Geometry')}
    expected = types[name]
    if len(args) != len(expected):
        fail('OKL-E-TYPE', f'{name} requires {len(expected)} positional arguments.',
             node, phase='type', details={'received': len(args)})
    values = [compiler.expect(arg, typ, node.args[i])
              for i, (arg,typ) in enumerate(zip(args,expected))]
    if ctx.abstract or not all(value.known for value in values):
        return Value(returns[name])
    raw = [value.value for value in values]
    if name in {'planar_point', 'polygon_vertex'}:
        return Value(returns[name], tuple(raw))
    return Value(Type('Geometry'), {
        'kind': 'extrusion',
        'vertices': tuple(PolygonVertex(key,*value.value) for key,value in raw[0].entries),
        'materials': tuple(SurfaceMaterial(key,*value.value) for key,value in raw[1].entries),
        'depth_m': raw[2], 'bottom_region': raw[3], 'top_region': raw[4],
        'source_id': node.source_id, 'start': node.start, 'end': node.end,
    })
