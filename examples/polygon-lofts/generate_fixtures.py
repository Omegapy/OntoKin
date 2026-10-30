#!/usr/bin/env python3
"""Author C077 inputs and analytic expectations without importing OntoKin.

This is a fixture authoring tool, not a runtime test or a product triangulator.
Endpoint area follows the shoelace identity. Volume uses horizontal-cap area
and the specified strip determinants, so no cap triangulation is reproduced.
Named prism/frustum cases additionally check independent closed-form measures.
"""
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
PALETTE = {
    'bottom': [.30, .35, .40, 1], 'inner': [.15, .65, .30, 1],
    'outer': [.70, .30, .10, 1], 'top': [.10, .50, .80, 1],
}
MAXIMUM_REQUEST = {'max_operations': 2000000, 'max_elapsed_ms': 80000}


def number(value):
    if isinstance(value, str):
        return value
    return format(Decimal(str(value)), 'f').rstrip('0').rstrip('.') if '.' in format(Decimal(str(value)), 'f') else str(value)


def scalar(value, unit='m'):
    return value if isinstance(value, str) else number(value) + '[' + unit + ']'


def ring(key, points, role='outer', order=20, region=None):
    return {'key': key, 'order': order, 'role': role,
            'vertices': [{'key': 'v' + str(i), 'order': i * 10,
                          'point_m': list(p), 'region': region or ('outer' if role == 'outer' else 'inner')}
                         for i, p in enumerate(points)]}


def square(half, role='outer', key=None, center=(0, 0), order=None):
    cx, cy = center
    points = [(cx-half, cy-half), (cx+half, cy-half), (cx+half, cy+half), (cx-half, cy+half)]
    if role == 'hole':
        points = [points[3], points[2], points[1], points[0]]
    return ring(key or ('outer' if role == 'outer' else 'opening'), points, role,
                order if order is not None else (20 if role == 'outer' else 40))


def section(key, station, rings, order):
    return {'key': key, 'order': order, 'station_m': station, 'rings': deepcopy(rings)}


def constant(rings, stations=(0, 3)):
    return [section('s' + str(i), z, rings, 10 + 10*i) for i, z in enumerate(stations)]


def taper(outer=(2, 1), inner=None, stations=(0, 3)):
    return [section('s' + str(i), z, [square(outer[i])] +
                    ([square(inner[i], 'hole')] if inner else []), 10 + 10*i)
            for i, z in enumerate(stations)]


def ring_source(rings, indent):
    pad = ' ' * indent
    chunks = []
    for r in rings:
        vertices = []
        for v in r['vertices']:
            x, y = v['point_m']
            vertices.append(pad + '    ' + json.dumps(v['key']) + ': polygon_vertex(' +
                            number(v['order']) + ', planar_point(' + scalar(x) + ', ' + scalar(y) +
                            '), ' + json.dumps(v['region']) + ')')
        chunks.append(pad + json.dumps(r['key']) + ': polygon_ring(' + number(r['order']) + ', ' +
                      json.dumps(r['role']) + ', keyed<PolygonVertex> {\n' + ',\n'.join(vertices) + '\n' + pad + '})')
    return 'keyed<PolygonRing> {\n' + ',\n'.join(chunks) + '\n' + ' ' * (indent-4) + '}'


def sections_source(sections, indent=8):
    pad = ' ' * indent
    chunks = []
    for s in sections:
        chunks.append(pad + json.dumps(s['key']) + ': polygon_section(' + number(s['order']) + ', ' +
                      scalar(s['station_m']) + ', ' + ring_source(s['rings'], indent+4) + ')')
    return 'keyed<PolygonSection> {\n' + ',\n'.join(chunks) + '\n' + ' ' * (indent-4) + '}'


def palette_source(palette):
    return 'keyed<SurfaceMaterial> {\n' + ',\n'.join(
        '        ' + json.dumps(key) + ': surface_material(rgba(' + ', '.join(map(number, rgba)) + '), 0.1, 0.65)'
        for key, rgba in palette.items()) + '\n    }'


def source(sections, palette=None, bottom='bottom', top='top', placement=None, request=None):
    palette = PALETTE if palette is None else palette
    header = 'ontokin "0.10";\nmodule RingLoftCase @ "ring-loft-case";\nprofile "polygon-loft-0.1";\n'
    if request:
        header += '\nexecution { max_operations = ' + str(request['max_operations']) + '; max_elapsed = ' + str(request['max_elapsed_ms']//1000) + '[s]; }\n'
    geometry = 'loft_rings(self.sections, self.palette, ' + json.dumps(bottom) + ', ' + json.dumps(top) + ')'
    if placement:
        offset, rotation = placement
        geometry = 'placed(' + geometry + ', pose(self.frame, vec3(' + ', '.join(scalar(x) for x in offset) + '), quat(' + ', '.join(map(number, rotation)) + ')))'
    return header + '\npublic class Shape @ "shape" {\n' + \
        '    public param sections @ "sections": Keyed<PolygonSection> = ' + sections_source(sections) + ';\n' + \
        '    public param palette @ "palette": Keyed<SurfaceMaterial> = ' + palette_source(palette) + ';\n' + \
        '    geometry = ' + geometry + ';\n    physical = no_body();\n}\n\n' + \
        'scene Demo @ "demo" {\n    duration = 1[s];\n' + \
        '    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);\n' + \
        '    object shape @ "shape": Shape {\n' + \
        '        placement = pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n    }\n' + \
        '    action travel @ "travel" = move(shape, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);\n' + \
        '    at 0[s] sequence { start travel; }\n}\n'


def ordered(sections):
    result = deepcopy(sorted(sections, key=lambda s: s['order']))
    for s in result:
        s['rings'].sort(key=lambda r: r['order'])
        for r in s['rings']:
            r['vertices'].sort(key=lambda v: v['order'])
    return result


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def area(section):
    value = Fraction(0)
    for r in section['rings']:
        xy = [tuple(Fraction(float(x)) for x in v['point_m']) for v in r['vertices']]
        value += sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(xy, xy[1:]+xy[:1]))/2
    return value


def geometry(sections, palette=None, bottom='bottom', top='top', placement=None):
    sections = ordered(sections)
    first, last = sections[0], sections[-1]
    n = sum(len(r['vertices']) for r in first['rings'])
    h = sum(r['role'] == 'hole' for r in first['rings'])
    cap = n + 2*h - 2
    areas = [area(s) for s in sections]
    volume6 = 2*(Fraction(float(last['station_m']))*areas[-1]-Fraction(float(first['station_m']))*areas[0])
    wall_area = 0.0
    regions = Counter({bottom: cap})
    regions[top] += cap
    for lower, upper in zip(sections, sections[1:]):
        for r0, r1 in zip(lower['rings'], upper['rings']):
            for i, v0 in enumerate(r0['vertices']):
                j = (i+1) % len(r0['vertices'])
                def point(s, r, k):
                    return tuple(Fraction(float(x)) for x in [*r['vertices'][k]['point_m'], s['station_m']])
                a0, b0 = point(lower, r0, i), point(lower, r0, j)
                a1, b1 = point(upper, r1, i), point(upper, r1, j)
                for a, b, c in ((a0,b0,a1), (b0,b1,a1)):
                    volume6 += dot(a,cross(b,c))
                    u, v = tuple(y-x for x,y in zip(a,b)), tuple(y-x for x,y in zip(a,c))
                    face = cross(u,v)
                    wall_area += math.sqrt(float(dot(face,face)))/2
                regions[v0['region']] += 2
    points = [[*v['point_m'], s['station_m']] for s in sections for r in s['rings'] for v in r['vertices']]
    volume = volume6/6
    result = {'sections':sections,'surface_rule':'fixed-diagonal-triangles',
              'section_count':len(sections),'ring_count':len(first['rings']),'hole_count':h,
              'vertices_per_section':n,'authored_vertex_count':len(sections)*n,
              'station_range_m':[first['station_m'],last['station_m']],
              'cap_triangle_count':cap,'strip_triangle_count':2*(len(sections)-1)*n,
              'triangle_count':2*len(sections)*n+4*h-4,'vertex_count':3*(2*len(sections)*n+4*h-4),
              'cap_areas_m2':[float(areas[0]),float(areas[-1])],
              'section_areas_m2':list(map(float,areas)), 'volume_m3':float(volume),
              'volume_exact':[str(volume.numerator),str(volume.denominator)],
              'surface_area_m2':float(areas[0]+areas[-1])+wall_area,
              'region_triangle_counts':dict(sorted(regions.items())),
              'bounds_m':[[min(p[i] for p in points) for i in range(3)], [max(p[i] for p in points) for i in range(3)]],
              'palette':deepcopy(PALETTE if palette is None else palette), 'metallic':.1,'roughness':.65}
    if placement:
        result['local_position_m'],result['local_orientation_wxyz']=placement
    return result


def main():
    cases=[]
    def add(name, sections, outcome='valid', code=None, note=None, **options):
        raw=source(sections,**options)
        (HERE/(name+'.ok')).write_text(raw)
        item={'id':name,'source':name+'.ok','expected_outcome':outcome}
        if code:item['diagnostic_code']=code
        if note:item['note']=note
        if options.get('request'):item['execution_request']=options['request']
        if outcome!='invalid':item['geometry']=geometry(sections,**{k:v for k,v in options.items() if k!='request'})
        cases.append(item)
        return item
    def invalid(name, base, mutate, code, note=None, **options):
        sections=deepcopy(base);mutate(sections)
        return add(name,sections,'invalid',code,note,**options)
    def analytic(item, volume, surface, expression):
        g=item['geometry']
        assert math.isclose(g['volume_m3'],volume,rel_tol=1e-13,abs_tol=1e-12)
        assert math.isclose(g['surface_area_m2'],surface,rel_tol=1e-13,abs_tol=1e-12)
        g['analytic_control']={'volume_m3':volume,'surface_area_m2':surface,'expression':expression}

    solid=constant([square(2)])
    hollow=constant([square(2),square(1,'hole')])
    frustum=taper()
    duct=taper(inner=(1,.5))
    analytic(add('constant-solid',solid),48,80,'A=16, P=16, h=3; V=A*h; surface=2*A+P*h')
    analytic(add('constant-hollow',hollow),36,96,'A=16-4, P=16+8, h=3; V=A*h; surface=2*A+P*h')
    analytic(add('solid-frustum',frustum),28,20+12*math.sqrt(10),'h/3*(A0+sqrt(A0*A1)+A1); caps20 + 12sqrt(10)')
    analytic(add('hollow-frustum',duct),21,15+12*math.sqrt(10)+3*math.sqrt(37),'Outer frustum28 minus inner7; caps15 + 12sqrt(10) + 3sqrt(37)')
    chamfer=taper((2,2,1),stations=(0,1,2))
    analytic(add('three-section-chamfer',chamfer),76/3,36+12*math.sqrt(2),'Prism16 plus frustum28/3; caps20 + walls16 + 12sqrt(2)')
    concave=constant([ring('outer',[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)])],(0,2))
    analytic(add('concave-outer',concave),10,34,'L outline A=5,P=12,h=2')
    changing_caps=[section('s0',0,[ring('outer',[(0,0),(4,0),(1,1),(0,4)])],10),
                   section('s1',3,[ring('outer',[(0,0),(1,2),(4,4),(0,4)])],20)]
    control=add('changing-concave-cap-diagonal',changing_caps,
                note='Endpoint caps require different diagonals; the actual triangular strips have disjoint horizontal y bands')
    control['geometry']['cap_diagonal_control']={'bottom':['v0','v2'],'top':['v1','v3'],'ring_key':'outer'}
    hole_l=ring('opening',[(-1,1),(0,1),(0,0),(1,0),(1,-1),(-1,-1)],'hole',40)
    add('concave-hole',constant([square(3),hole_l],(0,2)))
    two=[square(4),square(.5,'hole','left',(-2,0),40),square(.5,'hole','right',(2,0),60)]
    multiple=constant(two,(0,2))
    add('two-holes',multiple)
    reordered=deepcopy(multiple)
    reordered.reverse()
    for s in reordered:
        s['rings'].reverse()
        for r in s['rings']:r['vertices'].reverse()
    add('reordered-sections-rings-vertices',reordered)
    moved_outer=deepcopy(hollow)
    for s in moved_outer:s['rings'][0]['order']=60
    add('outer-after-hole',moved_outer)
    gapped=deepcopy(duct)
    for i,s in enumerate(gapped):
        s['order']=[0,65535][i]
        for r in s['rings']:
            for j,v in enumerate(r['vertices']):v['order']=[0,17,300,65535][j]
    add('gapped-boundary-orders',gapped)
    mixed=deepcopy(chamfer)
    for v in mixed[1]['rings'][0]['vertices']:v['region']='inner'
    mixed[0]['rings'][0]['vertices'][0]['region']='top'
    add('mixed-strip-materials',mixed)
    terminal=deepcopy(hollow)
    for r in terminal[-1]['rings']:
        for v in r['vertices']:v['region']='top'
    add('terminal-regions-no-strip',terminal)
    maximum_palette=deepcopy(PALETTE)
    maximum_palette.update({'unused'+str(i):[i/12,.2,.3,1] for i in range(12)})
    add('maximum-palette',solid,palette=maximum_palette)
    authority=constant([square(1)],(0,1))
    authority[1]['rings'][0]['vertices']=[{**v,'point_m':[-v['point_m'][1],v['point_m'][0]]} for v in authority[1]['rings'][0]['vertices']]
    analytic(add('authoritative-quarter-turn',authority),4,16,'Fixed triangles bound a 2x2x1 rectangular box; interpolated corresponding-vertex slices are not authoritative')
    add('minimum-station-gap',constant([square(1)],(0,.001)))
    add('maximum-stations-and-coordinates',constant([square(100)],(0,100)))
    add('nonzero-start-station',constant([square(1)],(20,23)))
    add('placed-hollow-frustum',duct,placement=([2,-1,.5],[0,1,0,0]))
    outer8=ring('outer',[(-8,-10),(8,-10),(10,-8),(10,8),(8,10),(-8,10),(-10,8),(-10,-8)])
    holes3=[ring('h'+str(i),[(x-.5,y-.5),(x,y+.5),(x+.5,y-.5)],'hole',40+10*i)
            for i,(x,y) in enumerate((x,y) for y in (-3,3) for x in (-6,-2,2,6))]
    max32=constant([outer8]+holes3,range(8))
    add('maximum-sections-and-total',max32,request=MAXIMUM_REQUEST)
    outer32=ring('outer',[(round(10*math.cos(i*math.pi/16),6),round(10*math.sin(i*math.pi/16),6)) for i in range(32)])
    holes4=[square(.5,'hole','h'+str(i),(x,y),40+10*i)
            for i,(x,y) in enumerate((x,y) for y in (-3,3) for x in (-6,-2,2,6))]
    max64=constant([outer32]+holes4,range(4))
    add('maximum-vertices-and-total',max64,request=MAXIMUM_REQUEST)

    L='OKL-E-RING-LOFT-';H='OKL-E-HOLES-'
    add('empty-sections',[],'invalid',L+'SECTION')
    add('one-section',solid[:1],'invalid',L+'SECTION')
    add('too-many-sections',constant([square(1)],range(9)),'invalid',L+'SECTION')
    add('too-many-total-vertices',constant([outer32]+holes4,range(5)),'invalid',L+'SECTION',request=MAXIMUM_REQUEST)
    extra=deepcopy(outer32)
    extra['vertices'].append({'key':'extra','order':315,'point_m':[10,.01],'region':'outer'})
    add('too-many-vertices-per-section',constant([extra]+holes4),'invalid',H+'VERTEX',request=MAXIMUM_REQUEST)
    add('too-many-holes',constant([square(10)]+[square(.25,'hole','h'+str(i),(-4+i,0),40+i*10) for i in range(9)]),'invalid',H+'RING')
    invalid('duplicate-section-key',solid,lambda s:s[1].update(key=s[0]['key']),'OKL-E-ID')
    invalid('duplicate-section-order',solid,lambda s:s[1].update(order=s[0]['order']),L+'ORDER')
    invalid('negative-section-order',solid,lambda s:s[0].update(order=-1),L+'ORDER')
    invalid('section-order-outside',solid,lambda s:s[1].update(order=65536),L+'ORDER')
    invalid('duplicate-station',solid,lambda s:s[1].update(station_m=0),L+'STATION')
    invalid('decreasing-stations',solid,lambda s:s[0].update(station_m=4),L+'STATION')
    invalid('below-minimum-station-gap',solid,lambda s:s[1].update(station_m=.000999),L+'STATION')
    add('rounded-decimal-gap',constant([square(1)],(1,1.001)),'invalid',L+'STATION',
        'Exact canonical binary64 difference is less than canonical binary64 0.001')
    assert Fraction(1.001)-Fraction(1.0)<Fraction(.001)
    invalid('negative-station',solid,lambda s:s[0].update(station_m=-.001),L+'STATION')
    invalid('station-outside',solid,lambda s:s[1].update(station_m=100.001),L+'STATION')
    invalid('wrong-station-unit',solid,lambda s:s[1].update(station_m='3[s]'),'OKL-E-UNIT')
    invalid('wrong-station-type',solid,lambda s:s[1].update(station_m='"three"'),'OKL-E-TYPE')
    invalid('changed-ring-key',hollow,lambda s:s[1]['rings'][1].update(key='different'),L+'CORRESPONDENCE')
    invalid('changed-ring-order',hollow,lambda s:s[1]['rings'][1].update(order=41),L+'CORRESPONDENCE')
    def roles(s):
        s[1]['rings']=[square(1,'hole','outer',order=20),square(2,'outer','opening',order=40)]
    invalid('changed-ring-role',hollow,roles,L+'CORRESPONDENCE')
    invalid('missing-ring',hollow,lambda s:s[1]['rings'].pop(),L+'CORRESPONDENCE')
    invalid('added-ring',solid,lambda s:s[1]['rings'].append(square(1,'hole')),L+'CORRESPONDENCE')
    invalid('changed-vertex-key',solid,lambda s:s[1]['rings'][0]['vertices'][1].update(key='different'),L+'CORRESPONDENCE')
    invalid('changed-vertex-order',solid,lambda s:s[1]['rings'][0]['vertices'][1].update(order=11),L+'CORRESPONDENCE')
    invalid('missing-vertex',solid,lambda s:s[1]['rings'][0]['vertices'].pop(),L+'CORRESPONDENCE')
    def vertex(s):
        s[1]['rings'][0]['vertices'].append({'key':'extra','order':35,'point_m':[-2.5,0],'region':'outer'})
    invalid('added-vertex',solid,vertex,L+'CORRESPONDENCE')
    def reverse_points(s,ring_index):
        old=[v['point_m'] for v in s[1]['rings'][ring_index]['vertices']]
        for v,p in zip(s[1]['rings'][ring_index]['vertices'],reversed(old)):v['point_m']=p
    invalid('clockwise-outer',solid,lambda s:reverse_points(s,0),H+'WINDING')
    invalid('counterclockwise-hole',hollow,lambda s:reverse_points(s,1),H+'WINDING')
    invalid('duplicate-ring-order',hollow,lambda s:s[1]['rings'][1].update(order=20),H+'ORDER')
    invalid('duplicate-vertex-order',solid,lambda s:s[1]['rings'][0]['vertices'][1].update(order=0),H+'ORDER')
    invalid('unknown-ring-role',solid,lambda s:s[1]['rings'][0].update(role='island'),H+'RING')
    invalid('duplicate-point',solid,lambda s:s[1]['rings'][0]['vertices'][1].update(point_m=[-2,-2]),H+'TOPOLOGY')
    invalid('adjacent-collinear',solid,lambda s:s[1]['rings'][0]['vertices'][1].update(point_m=[0,0]),H+'TOPOLOGY')
    def crossing(s):
        v=s[1]['rings'][0]['vertices'];v[1]['point_m'],v[2]['point_m']=v[2]['point_m'],v[1]['point_m']
    invalid('self-crossing-outer',solid,crossing,H+'TOPOLOGY')
    invalid('hole-touches-boundary',hollow,lambda s:s[1]['rings'][1]['vertices'][0].update(point_m=[-2,1]),H+'TOPOLOGY')
    invalid('hole-outside',hollow,lambda s:s[1]['rings'].__setitem__(1,square(.25,'hole',center=(3,0))),H+'CONTAINMENT')
    invalid('coordinate-outside',solid,lambda s:s[1]['rings'][0]['vertices'][1].update(point_m=[101,-2]),H+'POINT')
    invalid('missing-strip-region',solid,lambda s:s[0]['rings'][0]['vertices'][0].update(region='missing'),H+'REGION')
    invalid('missing-terminal-region',solid,lambda s:s[1]['rings'][0]['vertices'][0].update(region='missing'),H+'REGION')
    add('missing-cap-region',solid,'invalid',L+'REGION',bottom='missing')
    add('empty-palette',solid,'invalid','OKL-E-SURFACE-MATERIAL',palette={})
    too_many_palette=deepcopy(maximum_palette);too_many_palette['seventeenth']=[.1,.2,.3,1]
    add('too-many-materials',solid,'invalid','OKL-E-SURFACE-MATERIAL',palette=too_many_palette)
    def turn(s,quarter):
        for v in s[1]['rings'][0]['vertices']:
            x,y=v['point_m'];v['point_m']=([y,-x] if quarter==-1 else [-x,-y])
    invalid('strip-diagonal-pinch',constant([square(1)],(0,1)),lambda s:turn(s,-1),L+'TOPOLOGY',
            'Endpoint and linearly interpolated polygons are valid; nonshared strip diagonals intersect at (0,0,0.5)')
    invalid('correspondence-edge-pinch',constant([square(1)],(0,1)),lambda s:turn(s,2),L+'TOPOLOGY',
            'Valid endpoints rotate by 180 degrees and correspondence edges meet at mid-height')
    def swap_holes(s):
        left=s[1]['rings'][1]['vertices'];right=s[1]['rings'][2]['vertices']
        for a,b in zip(left,right):a['point_m'],b['point_m']=b['point_m'],a['point_m']
    invalid('swapped-hole-collision',multiple,swap_holes,L+'TOPOLOGY',
            'Both endpoint sections have disjoint contained holes but keyed holes exchange positions')
    item=add('earlier-version-rejection',solid,'invalid',note='Source 0.9 must reject PolygonSection and loft_rings; no exact phase is prescribed')
    p=HERE/item['source'];p.write_text(p.read_text().replace('ontokin "0.10"','ontokin "0.9"').replace('profile "polygon-loft-0.1"','profile "polygon-holes-0.1"'))

    # Four independent precision controls retain valid source geometry
    thin=constant([square(4),ring('opening',[(2,1),(2.00000001,1),(2.00000001,-1),(2,-1)],'hole',40)],(0,1))
    add('binary32-hole-collapse',thin,'source_valid_delivery_rejected',note='Distinct positive-width hole sides round to the same binary32 x')
    clearance=constant([ring('outer',[(1,-2),(5,-2),(5,2),(1,2)]),ring('opening',[(1.00000001,1),(3,1),(3,-1),(1.00000001,-1)],'hole',40)],(0,1))
    add('binary32-boundary-clearance',clearance,'source_valid_delivery_rejected',note='Strict positive source clearance rounds to a contact with the outer wall')
    nearholes=constant([square(4),ring('left',[(-2,1),(1,1),(1,-1),(-2,-1)],'hole',40),ring('right',[(1.00000001,1),(3,1),(3,-1),(1.00000001,-1)],'hole',60)],(0,1))
    add('binary32-between-holes',nearholes,'source_valid_delivery_rejected',note='Two separate source holes touch in binary32 delivery')
    placedclearance=constant([ring('outer',[(0,-2),(4,-2),(4,2),(0,2)]),ring('opening',[(.00000001,1),(2,1),(2,-1),(.00000001,-1)],'hole',40)],(0,1))
    add('binary32-placed-clearance',placedclearance,'source_valid_delivery_rejected',placement=([1,0,0],[1,0,0,0]),note='A local visual translation causes the narrow positive clearance to collapse')

    # Reusable library: the upper ring is editable per occurrence, height is generated
    lower=duct[0]['rings'];upper=duct[1]['rings']
    library='ontokin "0.10";\nmodule RingLoftParts @ "ring-loft-parts";\nprofile "polygon-loft-0.1";\n\npublic class Shape @ "shape" {\n'
    library+='    public param height @ "height": Length = 3[m];\n'
    library+='    public param lower_rings @ "lower-rings": Keyed<PolygonRing> = '+ring_source(lower,8)+';\n'
    library+='    public param upper_rings @ "upper-rings": Keyed<PolygonRing> = '+ring_source(upper,8)+';\n'
    library+='    public param palette @ "palette": Keyed<SurfaceMaterial> = '+palette_source(PALETTE)+';\n'
    library+='    geometry = loft_rings(keyed<PolygonSection> {\n        "s0": polygon_section(10, 0[m], self.lower_rings),\n        "s1": polygon_section(20, self.height, self.upper_rings)\n    }, self.palette, "bottom", "top");\n    physical = no_body();\n}\n'
    (HERE/'parts.ok').write_text(library)
    digest=hashlib.sha256(library.encode()).hexdigest()
    import_text='import libparts @ "ring-loft-parts" from "fixture.ring-loft-parts" version "1.0.0"\n    digest "sha256:'+digest+'";\n'
    assembly='ontokin "0.10";\nmodule RingLoftAssembly @ "ring-loft-assembly";\nprofile "polygon-loft-0.1";\n\n'+import_text+'\nscene Demo @ "demo" {\n    duration = 1[s];\n    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);\n    object first @ "first": libparts.Shape {\n        placement = pose(world, vec3(-3[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n        upper_rings = '+ring_source(upper,12)+';\n    }\n    object sibling @ "sibling": libparts.Shape {\n        placement = pose(world, vec3(3[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n    }\n    action travel @ "travel" = move(first, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);\n    at 0[s] sequence { start travel; }\n}\n'
    old='"v1": polygon_vertex(10, planar_point(0.5[m], 0.5[m]), "inner")'
    new='"v1": polygon_vertex(10, planar_point(0.25[m], 0.5[m]), "inner")'
    bad_old='"v0": polygon_vertex(0, planar_point(-0.5[m], 0.5[m]), "inner")'
    bad_new='"v0": polygon_vertex(0, planar_point(-1[m], 0.5[m]), "inner")'
    assert assembly.count(old)==assembly.count(bad_old)==1
    (HERE/'assembly.ok').write_text(assembly)
    (HERE/'assembly-repaired.ok').write_text(assembly.replace(old,new))
    (HERE/'assembly-invalid.ok').write_text(assembly.replace(bad_old,bad_new))
    repaired=deepcopy(duct);repaired[1]['rings'][1]['vertices'][1]['point_m'][0]=.25
    add('repaired-hollow-frustum',repaired)
    generated='ontokin "0.10";\nmodule RingLoftArray @ "ring-loft-array";\nprofile "polygon-loft-0.1";\n\n'+import_text+'''
public class Mounted @ "mounted" extends libparts.Shape {
    public param parent_frame @ "parent-frame": FrameRef = world;
    public param mount_x @ "mount-x": Length = 0[m];
    public follow mounting @ "mounting" {
        parent = self.parent_frame;
        child = self;
        offset = pose(self.parent_frame, vec3(self.mount_x, 0[m], 0[m]), quat(1, 0, 0, 0));
    }
}
public class Array @ "array-type" {
    public param heights @ "heights": Keyed<Length> = keyed<Length> {
        "left": 1[m], "middle": 2[m], "right": 3[m]
    };
    geometry = empty();
    physical = no_body();
    public parts ducts @ "ducts": Mounted for (key, value) in self.heights {
        parent_frame = self.frame;
        mount_x = 5 * value;
        height = value;
    }
}
scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object array @ "array": Array {
        placement = pose(world, vec3(-10[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
    action travel @ "travel" = move(array, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence { start travel; }
}
'''
    (HERE/'generated.ok').write_text(generated)
    expected={'schema_version':'ontokin.polygon-loft-expectations/0.1','decision':'OK-LANG-010/0.1.0',
              'frozen_before_implementation':True,'cases':cases,
              'assembly':{'entry':'assembly.ok','repaired_entry':'assembly-repaired.ok','invalid_entry':'assembly-invalid.ok',
                          'module_id':'ring-loft-assembly','scene_id':'demo',
                          'library':{'source_id':'package:fixture.ring-loft-parts@1.0.0','filename':'parts.ok',
                                     'package':'fixture.ring-loft-parts','version':'1.0.0','sha256':digest},
                          'first':geometry(duct),'sibling':geometry(duct),'repaired_first':geometry(repaired),
                          'first_placement_m':[-3,0,0],'sibling_placement_m':[3,0,0],
                          'repair':{'old':old,'new':new,'section_key':'s1','ring_key':'opening','vertex_key':'v1'},
                          'invalid_edit':{'old':bad_old,'new':bad_new,'diagnostic_code':H+'TOPOLOGY'},
                          'sibling_motion_m_per_second':[0,0,0]},
              'generated':{'entry':'generated.ok','object_path':'array','parts_member':'ducts','root_placement_m':[-10,0,0],
                           'parts':{key:{'geometry':geometry(taper(inner=(1,.5),stations=(0,height))),'mount_x_m':5*height}
                                    for key,height in [('left',1),('middle',2),('right',3)]}},
              'duration_seconds':1,'sample_times_seconds':[0,.25,.5,.75,1],
              'motion_m_per_second':[0,.5,0],'options':{'fps':4,'end_time_seconds':1},
              'tolerances':{'geometry_m':1e-5,'area_m2':1e-4,'volume_m3':1e-4,'normal':1e-5,'position_m':.001,'rotation_rad':.001,'material':1e-6},
              'maximum_host_policy':MAXIMUM_REQUEST,
              'ordering_equivalence':[['two-holes','reordered-sections-rings-vertices']],
              'geometry_equivalence':[['constant-hollow','terminal-regions-no-strip'],['constant-solid','maximum-palette']],
              'required_geometry_checks':['actual authored vertex identities at every section','exact closed opposite directed edge incidence',
                                         'complete endpoint cap coverage and absence of intermediate caps','exact fixed-diagonal strip triangles',
                                         'independent nonadjacent 3D surface intersections','outward flat normals',
                                         'lower outgoing-edge material ownership and actual PBR values','signed volume and actual triangle area',
                                         'analytic frustum/prism controls','recorded carrier motion and once-only local placement']}
    (HERE/'expected.json').write_text(json.dumps(expected,indent=2,allow_nan=False)+'\n')
    files={p.name:{'bytes':len(p.read_bytes()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
           for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='acceptance-freeze.json'}
    freeze={'schema_version':'ontokin.polygon-loft-freeze/0.1','decision':'OK-LANG-010/0.1.0',
            'decision_commit':'4d1b15f5859e7f08feb8041b67c112d9f1485174',
            'frozen_before_implementation':True,'case_count':len(cases),
            'outcome_counts':dict(Counter(c['expected_outcome'] for c in cases)),
            'source_count':sum(name.endswith('.ok') for name in files),'files':files}
    (HERE/'acceptance-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
    print(json.dumps({k:freeze[k] for k in ['case_count','outcome_counts','source_count']}))


if __name__=='__main__':
    main()
