"""Typed source constructors for matched polygon sections and ring lofts."""
from .holes import PolygonRing
from .ring_loft import PolygonSection
from .surface import SurfaceMaterial
from .validator import fail
from .values import INT, STRING, LENGTH, Type, Value, quantity_type


RING_LOFT_TYPES = frozenset({'PolygonSection'})
RING_LOFT_CALLS = frozenset({'polygon_section', 'loft_rings'})


def ring_loft_builtin(compiler, name, args, node, ctx):
    types = {
        'polygon_section': [INT, quantity_type(LENGTH), Type('Keyed', element=Type('PolygonRing'))],
        'loft_rings': [Type('Keyed', element=Type('PolygonSection')),
                       Type('Keyed', element=Type('SurfaceMaterial')), STRING, STRING],
    }
    returns = {'polygon_section': Type('PolygonSection'), 'loft_rings': Type('Geometry')}
    expected = types[name]
    if len(args) != len(expected):
        fail('OKL-E-TYPE', f'{name} requires {len(expected)} positional arguments.',
             node, phase='type', details={'received': len(args)})
    if name == 'polygon_section' and args[1].type.kind != 'Quantity':
        fail('OKL-E-TYPE', 'A polygon section station requires a Length value.',
             node.args[1], phase='type', details={'expected': 'Length', 'actual': str(args[1].type)})
    values = [compiler.expect(arg, typ, node.args[i])
              for i, (arg, typ) in enumerate(zip(args, expected))]
    if ctx.abstract or not all(value.known for value in values):
        return Value(returns[name])
    raw = [value.value for value in values]
    if name == 'polygon_section':
        rings = tuple(PolygonRing(key, *value.value) for key, value in raw[2].entries)
        return Value(Type('PolygonSection'), (raw[0], raw[1], rings))
    return Value(Type('Geometry'), {
        'kind': 'ring_loft',
        'sections': tuple(PolygonSection(key, *value.value) for key, value in raw[0].entries),
        'materials': tuple(SurfaceMaterial(key, *value.value) for key, value in raw[1].entries),
        'bottom_region': raw[2], 'top_region': raw[3],
        'source_id': node.source_id, 'start': node.start, 'end': node.end,
    })
