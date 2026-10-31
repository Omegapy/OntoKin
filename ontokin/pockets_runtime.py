"""Typed source constructors for complete prismatic pocket exteriors."""
from .extrusion import PolygonVertex
from .pockets import PolygonPocket
from .surface import SurfaceMaterial
from .validator import fail
from .values import INT, STRING, LENGTH, Type, Value, quantity_type


POCKETS_TYPES = frozenset({'PolygonPocket'})
POCKETS_CALLS = frozenset({'polygon_pocket', 'extrude_pockets'})


def pockets_builtin(compiler, name, args, node, ctx):
    types = {
        'polygon_pocket': [INT, Type('Keyed', element=Type('PolygonVertex')),
                           quantity_type(LENGTH), STRING],
        'extrude_pockets': [Type('Keyed', element=Type('PolygonVertex')),
                            Type('Keyed', element=Type('PolygonPocket')),
                            Type('Keyed', element=Type('SurfaceMaterial')),
                            quantity_type(LENGTH), STRING, STRING],
    }
    returns = {'polygon_pocket': Type('PolygonPocket'), 'extrude_pockets': Type('Geometry')}
    expected = types[name]
    if len(args) != len(expected):
        fail('OKL-E-TYPE', f'{name} requires {len(expected)} positional arguments.',
             node, phase='type', details={'received': len(args)})
    values = []
    for index, (arg, typ) in enumerate(zip(args, expected)):
        compiler.budget.tick(node)
        values.append(compiler.expect(arg, typ, node.args[index]))
    if ctx.abstract or not all(value.known for value in values):
        return Value(returns[name])
    raw = [value.value for value in values]
    if name == 'polygon_pocket':
        vertices = []
        for key, value in raw[1].entries:
            compiler.budget.tick(node)
            vertices.append(PolygonVertex(key, *value.value))
        return Value(Type('PolygonPocket'), (raw[0], tuple(vertices), raw[2], raw[3]))
    outer, pockets, materials = [], [], []
    for key, value in raw[0].entries:
        compiler.budget.tick(node)
        outer.append(PolygonVertex(key, *value.value))
    for key, value in raw[1].entries:
        compiler.budget.tick(node)
        pockets.append(PolygonPocket(key, *value.value))
    for key, value in raw[2].entries:
        compiler.budget.tick(node)
        materials.append(SurfaceMaterial(key, *value.value))
    return Value(Type('Geometry'), {
        'kind': 'pockets', 'outer_vertices': tuple(outer), 'pockets': tuple(pockets),
        'materials': tuple(materials), 'height_m': raw[3],
        'bottom_region': raw[4], 'top_region': raw[5],
        'source_id': node.source_id, 'start': node.start, 'end': node.end,
    })
