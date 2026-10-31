"""Typed source constructors for explicitly owned framed polygon sections."""
from .framed_loft import FramedPolygonSection
from .holes import PolygonRing
from .surface import SurfaceMaterial
from .validator import fail
from .values import INT, STRING, Type, Value


FRAMED_LOFT_TYPES = frozenset({'FramedPolygonSection'})
FRAMED_LOFT_CALLS = frozenset({'framed_polygon_section', 'loft_framed_rings'})


def _owner(ctx, node):
    path = ctx.self_path or getattr(ctx, 'geometry_owner', None)
    if path is None:
        fail('OKL-E-FRAMED-LOFT-FRAME', 'A framed section requires its consuming carrier context.',
             node, phase='type')
    return path + '.frame'


def _check_owner(frame, owner, node):
    if frame.frame != owner:
        fail('OKL-E-FRAMED-LOFT-FRAME', 'A section pose must reference its consuming carrier self.frame.',
             node, phase='type', details={'frame': frame.frame, 'owner_frame': owner})


def framed_loft_builtin(compiler, name, args, node, ctx):
    types = {
        'framed_polygon_section': [INT, Type('Pose'), Type('Keyed', element=Type('PolygonRing'))],
        'loft_framed_rings': [Type('Keyed', element=Type('FramedPolygonSection')),
                              Type('Keyed', element=Type('SurfaceMaterial')), STRING, STRING],
    }
    returns = {'framed_polygon_section': Type('FramedPolygonSection'),
               'loft_framed_rings': Type('Geometry')}
    expected = types[name]
    if len(args) != len(expected):
        fail('OKL-E-TYPE', f'{name} requires {len(expected)} positional arguments.',
             node, phase='type', details={'received': len(args)})
    values = []
    for index, (arg, typ) in enumerate(zip(args, expected)):
        compiler.budget.tick(node)
        if typ.kind == 'Pose' and arg.type.kind != 'Pose':
            fail('OKL-E-TYPE', 'A framed polygon section frame requires a Pose value.',
                 node.args[index], phase='type',
                 details={'expected': 'Pose', 'actual': str(arg.type)})
        values.append(compiler.expect(arg, typ, node.args[index]))
    if ctx.abstract or not all(value.known for value in values):
        return Value(returns[name])
    owner = _owner(ctx, node)
    raw = [value.value for value in values]
    if name == 'framed_polygon_section':
        _check_owner(raw[1], owner, node.args[1])
        rings = []
        for key, value in raw[2].entries:
            compiler.budget.tick(node)
            rings.append(PolygonRing(key, *value.value))
        return Value(Type('FramedPolygonSection'), (raw[0], raw[1], tuple(rings)))
    sections = []
    for key, value in raw[0].entries:
        compiler.budget.tick(node)
        section = FramedPolygonSection(key, *value.value)
        _check_owner(section.frame, owner, node.args[0])
        sections.append(section)
    materials = []
    for key, value in raw[1].entries:
        compiler.budget.tick(node)
        materials.append(SurfaceMaterial(key, *value.value))
    return Value(Type('Geometry'), {
        'kind': 'framed_loft', 'sections': tuple(sections), 'materials': tuple(materials),
        'bottom_region': raw[2], 'top_region': raw[3], 'owner_frame': owner,
        'source_id': node.source_id, 'start': node.start, 'end': node.end,
    })
