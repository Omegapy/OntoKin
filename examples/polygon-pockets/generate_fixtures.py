#!/usr/bin/env python3
"""Author independent C079 source inputs and analytic expectations using stdlib only.

This program never imports OntoKin, generates triangles, or executes a source
program. It measures authored planar boundaries and exact rounded floor values.
"""
from __future__ import annotations

import argparse
import copy
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import struct


BASELINE = '50998106fe468e6630f17c79d88f7810da81bc32'
DECISION = 'OK-LANG-012/0.1.0'
PALETTE = {
    'bottom': [0.3, 0.35, 0.4, 1],
    'floor': [0.85, 0.65, 0.15, 1],
    'inner': [0.15, 0.65, 0.3, 1],
    'outer': [0.7, 0.3, 0.1, 1],
    'top': [0.1, 0.5, 0.8, 1],
}


def number(value):
    if isinstance(value, str):
        return value
    if value == 0:
        return '0'
    return repr(value) if type(value) is float else str(value)


def exact(value):
    return F(float(value))


def ratio(value):
    return [str(value.numerator), str(value.denominator)]


def vertices(points, region='outer'):
    return [dict(key='v'+str(i), order=i*10, point_m=list(p), region=region)
            for i, p in enumerate(points)]


def rect(x0, y0, x1, y1, clockwise=False):
    result = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [result[0], *reversed(result[1:])] if clockwise else result


def pocket(key, order, points, depth=0.5, floor='floor'):
    return dict(key=key, order=order, vertices=vertices(points, 'inner'),
                depth_m=depth, floor_region=floor)


def recipe(outer=None, pockets=None, height=2, palette=None):
    return dict(outer_vertices=vertices(outer or rect(0, 0, 4, 3)),
                pockets=copy.deepcopy(pockets if pockets is not None else [
                    pocket('recess', 20, rect(1, 1, 3, 2, True))]),
                height_m=height, palette=copy.deepcopy(palette or PALETTE),
                bottom_region='bottom', top_region='top',
                metallic=0.1, roughness=0.65,
                local_placement_m=[0, 0, 0], local_orientation_wxyz=[1, 0, 0, 0])


def ordered(values):
    return sorted(values, key=lambda item: item['order'])


def points(values):
    return [tuple(exact(v) for v in item['point_m']) for item in ordered(values)]


def signed_area(values):
    xy = points(values)
    return sum((p[0]*q[1]-q[0]*p[1] for p, q in zip(xy, xy[1:]+xy[:1])), F())/2


def perimeter(values):
    xy = points(values)
    return math.fsum(math.hypot(float(p[0]-q[0]), float(p[1]-q[1]))
                     for p, q in zip(xy, xy[1:]+xy[:1]))


def rotate(point, quaternion):
    # Independent ordinary quaternion formula for the separately authored rigid pose
    w, x, y, z = (exact(v) for v in quaternion)
    d = w*w+x*x+y*y+z*z
    matrix = ((w*w+x*x-y*y-z*z, 2*(x*y-w*z), 2*(x*z+w*y)),
              (2*(x*y+w*z), w*w-x*x+y*y-z*z, 2*(y*z-w*x)),
              (2*(x*z-w*y), 2*(y*z+w*x), w*w-x*x-y*y+z*z))
    return [sum((row[j]*exact(point[j]) for j in range(3)), F())/d for row in matrix]


def measured(raw):
    value = copy.deepcopy(raw)
    outer = ordered(value['outer_vertices'])
    value['outer_vertices'] = outer
    value['pockets'] = ordered(value['pockets'])
    h, a0 = exact(value['height_m']), signed_area(outer)
    assert a0 > 0
    volume = a0*h
    area = 2*float(a0)+perimeter(outer)*float(h)
    n0 = len(outer)
    total = n0+sum(len(p['vertices']) for p in value['pockets'])
    pcount = len(value['pockets'])
    counts = {k: 0 for k in value['palette']}
    counts[value['bottom_region']] += n0-2
    counts[value['top_region']] += total+2*pcount-2
    for vertex in outer:
        counts[vertex['region']] += 2
    logical = []
    for vertex in outer:
        for level, z in (('bottom', 0.0), ('top', float(h))):
            logical.append({'identity': ['outer', 'outer', vertex['key'], 'lower' if level=='bottom' else level],
                            'position_m': [*vertex['point_m'], z]})
    for p in value['pockets']:
        p['vertices'] = ordered(p['vertices'])
        ai = -signed_area(p['vertices'])
        assert ai > 0
        b = h-exact(p['depth_m'])
        assert b >= exact(0.001)
        floor = float(b)
        effective = h-exact(floor)
        p.update(floor_m=floor, remaining_base_m=floor,
                 effective_depth_value_m=float(effective),
                 exact_remaining_base_m={'numerator':str(b.numerator),'denominator':str(b.denominator)},
                 effective_depth_m={'numerator':str(effective.numerator),'denominator':str(effective.denominator)},
                 area_m2=float(ai), area_exact=ratio(ai), perimeter_m=perimeter(p['vertices']))
        volume -= ai*effective
        area += p['perimeter_m']*float(effective)
        counts[p['floor_region']] += len(p['vertices'])-2
        for vertex in p['vertices']:
            counts[vertex['region']] += 2
            for level, z in (('floor', floor), ('top', float(h))):
                logical.append({'identity': ['pocket', p['key'], vertex['key'], 'lower' if level=='floor' else level],
                                'position_m': [*vertex['point_m'], z]})
    actual_positions = []
    for item in logical:
        rotated = rotate(item['position_m'], value['local_orientation_wxyz'])
        item['placed_position_m'] = [float(v+exact(t)) for v,t in zip(rotated,value['local_placement_m'])]
        actual_positions.append(item['placed_position_m'])
    value.update(outer_area_m2=float(a0), outer_area_exact=ratio(a0),
                 outer_perimeter_m=perimeter(outer), volume_m3=float(volume),
                 volume_exact=ratio(volume), surface_area_m2=area,
                 pocket_count=pcount, authored_vertex_count=total,
                 outer_vertex_count=n0, bottom_triangle_count=n0-2,
                 top_triangle_count=total+2*pcount-2,
                 floor_triangle_count=total-n0-2*pcount,
                 wall_triangle_count=2*total, triangle_count=4*total-4,
                 vertex_count=12*total-12, logical_vertex_count=2*total,
                 region_triangle_counts={k:v for k,v in sorted(counts.items()) if v},
                 source_positions=logical,
                 bounds_m=[[min(p[j] for p in actual_positions) for j in range(3)],
                           [max(p[j] for p in actual_positions) for j in range(3)]])
    assert sum(value['region_triangle_counts'].values()) == value['triangle_count']
    assert value['volume_m3'] > 0
    return value


def vsource(values, indent='        '):
    body = ',\n'.join(indent+'    '+json.dumps(v['key'])+': polygon_vertex('
        +number(v['order'])+', planar_point('+number(v['point_m'][0])+'[m], '
        +number(v['point_m'][1])+'[m]), '+json.dumps(v['region'])+')' for v in values)
    return 'keyed<PolygonVertex> {\n'+body+'\n'+indent+'}'


def psource(values, indent='    ', depth_expression=None):
    entries = []
    for p in values:
        depth = depth_expression or number(p['depth_m'])+'[m]'
        entries.append(indent+'    '+json.dumps(p['key'])+': polygon_pocket('
            +number(p['order'])+', '+vsource(p['vertices'],indent+'    ')+', '+depth
            +', '+json.dumps(p['floor_region'])+')')
    return 'keyed<PolygonPocket> {\n'+',\n'.join(entries)+'\n'+indent+'}'


def material_source(palette):
    return 'keyed<SurfaceMaterial> {\n'+',\n'.join(
        '        '+json.dumps(key)+': surface_material(rgba('+', '.join(number(c) for c in rgba)
        +'), 0.1, 0.65)' for key,rgba in palette.items())+'\n    }'


def class_source(raw, *, legacy=False, library=False, functions=False):
    prefix = '    public param pocket_depth @ "pocket-depth": Length = 0.5[m];\n' if library else ''
    source = ('public class Shape @ "shape" {\n'+prefix
        +'    public param outer_vertices @ "outer-vertices": Keyed<PolygonVertex> = '
        +vsource(raw['outer_vertices'],'    ')+';\n')
    if not legacy:
        source += '    public param pockets @ "pockets": Keyed<PolygonPocket> = '+psource(
            raw['pockets'], depth_expression='self.pocket_depth' if library else None)+';\n'
    source += ('    public param height @ "height": Length = '+number(raw['height_m'])+'[m];\n'
        +'    public param palette @ "palette": Keyed<SurfaceMaterial> = '+material_source(raw['palette'])+';\n')
    if legacy:
        expression = 'extrude(self.outer_vertices, self.palette, self.height, "bottom", "top")'
    elif functions:
        expression = 'make_geometry(self.outer_vertices, self.pockets, self.palette, self.height)'
    else:
        expression = ('extrude_pockets(self.outer_vertices, self.pockets, self.palette, self.height, '
                      +json.dumps(raw['bottom_region'])+', '+json.dumps(raw['top_region'])+')')
    if raw['local_placement_m'] != [0,0,0] or raw['local_orientation_wxyz'] != [1,0,0,0]:
        expression = ('placed('+expression+', pose(self.frame, vec3('
            +', '.join(number(v)+'[m]' for v in raw['local_placement_m'])+'), quat('
            +', '.join(number(v) for v in raw['local_orientation_wxyz'])+')))')
    source += '    geometry = '+expression+';\n    physical = no_body();\n}\n'
    if functions:
        source = source.replace('polygon_pocket(', 'make_pocket(')
    return source


SCENE = '''\nscene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object shape @ "shape": Shape {
        placement = pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
    action travel @ "travel" = move(shape, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence { start travel; }
}
'''
FUNCTIONS = '''public fn make_pocket @ "make-pocket"(order: Int, outline: Keyed<PolygonVertex>, depth: Length, region: String) -> PolygonPocket {
    return polygon_pocket(order, outline, depth, region);
}
public fn make_geometry @ "make-geometry"(outline: Keyed<PolygonVertex>, cavities: Keyed<PolygonPocket>, palette: Keyed<SurfaceMaterial>, height: Length) -> Geometry {
    return extrude_pockets(outline, cavities, palette, height, "bottom", "top");
}

'''


def source(raw, *, large=False, legacy=False, library=False, functions=False):
    version, profile = ('0.8','polygon-extrusion-0.1') if legacy else ('0.12','polygon-pockets-0.1')
    module, module_id = ('PocketParts','pocket-parts') if library else ('PocketCase','pocket-case')
    result = 'ontokin "'+version+'";\nmodule '+module+' @ "'+module_id+'";\nprofile "'+profile+'";\n\n'
    if large:
        result += 'execution { max_operations = 2000000; max_elapsed = 80[s]; }\n\n'
    if functions:
        result += FUNCTIONS
    result += class_source(raw,legacy=legacy,library=library,functions=functions)
    return result if library else result+SCENE


def regular(count, radius, cx=0, cy=0, clockwise=False):
    values = [(round(cx+radius*math.cos(2*math.pi*i/count),6),
               round(cy+radius*math.sin(2*math.pi*i/count),6)) for i in range(count)]
    return [values[0],*reversed(values[1:])] if clockwise else values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decision-commit')
    parser.add_argument('--decision-file',type=Path)
    args=parser.parse_args()
    out=args.output
    if (out/'acceptance-freeze.json').exists():
        raise SystemExit('Refusing to overwrite a frozen input directory; choose a new output path')
    out.mkdir(parents=True,exist_ok=True)
    cases=[]
    def add(name, raw, *, outcome='valid', code=None, note=None, large=False,
            mutate=None, functions=False, heldout=False):
        text=source(raw,large=large,functions=functions)
        if mutate: text=mutate(text)
        (out/(name+'.ok')).write_text(text,encoding='utf-8')
        row=dict(id=name,source=name+'.ok',expected_outcome=outcome)
        if outcome!='invalid': row['geometry']=measured(raw)
        if code: row['diagnostic_code']=code
        if note: row['note']=note
        if large: row['requested_execution_limits']={'max_operations':2000000,'max_elapsed_ms':80000}
        if heldout: row['role']='predetermined-heldout'
        cases.append(row)
        return row
    base=recipe()
    add('rectangular-pocket',base)
    zero=recipe(pockets=[])
    add('zero-pockets',zero)
    (out/'zero-pockets-legacy.ok').write_text(source(zero,legacy=True))
    concave=[(0,0),(6,0),(6,2),(2,2),(2,6),(0,6)]
    zero_concave=recipe(concave,[])
    add('zero-pockets-concave',zero_concave)
    (out/'zero-pockets-concave-legacy.ok').write_text(source(zero_concave,legacy=True))
    add('concave-outer',recipe(concave,[pocket('recess',20,rect(.5,.5,1.5,1.5,True),.75)]))
    inner_l=[(1,1),(1,4),(2,4),(2,2),(4,2),(4,1)]
    add('concave-pocket',recipe(rect(0,0,6,5),[pocket('recess',20,inner_l,.75)]))
    unequal=recipe(rect(0,0,8,4),[pocket('left',10,rect(1,1,3,3,True),.5),
                                     pocket('right',30,rect(5,1,7,2,True),1.25)])
    unequal['palette']['floor-right']=[.65,.2,.7,1]
    unequal['pockets'][1]['floor_region']='floor-right'
    add('unequal-depths',unequal)
    add('triangular-pocket',recipe(pockets=[pocket('recess',20,[(1,1),(2,2),(3,1)],.5)]))
    add('triangular-body',recipe([(0,0),(6,0),(0,6)],[pocket('recess',20,[(1,1),(1,2),(2,1)],.5)]))
    add('cross-boundary-collinearity',recipe(rect(0,0,6,4),[
        pocket('left',10,rect(1,1,2,3,True),.5),pocket('right',20,rect(4,1,5,3,True),1)]))
    add('negative-coordinates',recipe(rect(-4,-3,0,0),[pocket('recess',20,rect(-3,-2,-1,-1,True),.5)]))
    add('component-boundaries',recipe(rect(-100,-100,100,100),[pocket('recess',20,rect(-50,-50,50,50,True),50)],100),large=True)
    add('minimum-body-height',recipe(pockets=[],height=.001))
    add('minimum-pocket-depth',recipe(pockets=[pocket('recess',20,rect(1,1,3,2,True),.001)],height=1))
    add('minimum-base',recipe(pockets=[pocket('recess',20,rect(1,1,3,2,True),.001)],height=.002))
    add('above-minimum-base',recipe(pockets=[pocket('recess',20,rect(1,1,3,2,True),.001)],height=math.nextafter(.002,math.inf)))
    add('rounded-floor',recipe(pockets=[pocket('recess',20,rect(1,1,3,2,True),.1)],height=.3))
    gapped=copy.deepcopy(base)
    for i,v in enumerate(gapped['outer_vertices']):v['order']=[0,301,8192,65535][i]
    for i,v in enumerate(gapped['pockets'][0]['vertices']):v['order']=[0,7,900,65535][i]
    gapped['pockets'][0]['order']=65535
    add('gapped-orders',gapped)
    named=copy.deepcopy(base);named['pockets'][0]['key']='outer';add('pocket-key-outer',named)
    reordered=copy.deepcopy(unequal)
    reordered['outer_vertices'].reverse();reordered['pockets'].reverse()
    for p in reordered['pockets']:p['vertices'].reverse()
    reordered['palette']=dict(reversed(list(reordered['palette'].items())))
    add('declaration-reordering',reordered)
    mixed=copy.deepcopy(base)
    mixed['outer_vertices'][1]['region']='top';mixed['pockets'][0]['vertices'][1]['region']='floor'
    add('mixed-wall-materials',mixed)
    maximum_palette=copy.deepcopy(base)
    for i in range(11):maximum_palette['palette']['unused'+str(i)]=[i/16,.2,.4,1]
    add('maximum-palette',maximum_palette)
    placed=copy.deepcopy(base);placed['local_placement_m']=[1,2,3];placed['local_orientation_wxyz']=[.5,.5,.5,.5]
    add('placed-rotated-pocket',placed)
    add('function-pocket-and-geometry',base,functions=True)
    maxp=recipe(regular(8,20),[pocket('p'+str(i),i*100,regular(7,1.5,[-12,-4,4,12][i%4],[-5,5][i//4],True),.25+.125*i) for i in range(8)],3)
    add('maximum-pockets-and-vertices',maxp,large=True)
    add('maximum-vertices-zero-pockets',recipe(regular(64,10),[],2),large=True)
    repair=copy.deepcopy(base);repair['pockets'][0]['depth_m']=.75;add('repaired-rectangular-pocket',repair)
    add('heldout-stepped-tray',recipe([(0,0),(7,0),(7,3),(5,3),(5,5),(0,5)],[
        pocket('recess',101,[(1,1),(1,4),(3,4),(4,2),(3,1)],.625)],1.5),heldout=True)
    def bad(name,raw,suffix,note=None,mutate=None):
        code=suffix if suffix.startswith('OKL-') else 'OKL-E-POCKETS-'+suffix
        return add(name,raw,outcome='invalid',code=code,note=note,mutate=mutate)
    wrong=copy.deepcopy(base);wrong['outer_vertices']=vertices(list(reversed(rect(0,0,4,3))));bad('clockwise-outer',wrong,'WINDING')
    wrong=copy.deepcopy(base);wrong['pockets'][0]['vertices']=vertices(rect(1,1,3,2),'inner');bad('counterclockwise-pocket',wrong,'WINDING')
    bad('pocket-touching-boundary',recipe(pockets=[pocket('recess',20,rect(0,1,2,2,True))]),'TOPOLOGY')
    bad('pocket-crossing-boundary',recipe(pockets=[pocket('recess',20,rect(-.25,1,2,2,True))]),'TOPOLOGY')
    bad('pocket-outside',recipe(pockets=[pocket('recess',20,rect(5,1,6,2,True))]),'CONTAINMENT')
    bad('pocket-in-concave-notch',recipe(concave,[pocket('recess',20,rect(3,3,4,4,True))]),'CONTAINMENT')
    bad('touching-pockets',recipe(pockets=[pocket('left',10,rect(.5,.5,2,2.5,True)),pocket('right',20,rect(2,.5,3.5,2.5,True))]),'TOPOLOGY')
    bad('overlapping-pockets',recipe(pockets=[pocket('left',10,rect(.5,.5,2.5,2.5,True)),pocket('right',20,rect(2,.5,3.5,2.5,True))]),'TOPOLOGY')
    bad('nested-pockets',recipe(pockets=[pocket('outside',10,rect(.5,.5,3.5,2.5,True)),pocket('inside',20,rect(1,1,2,2,True))]),'CONTAINMENT')
    wrong=copy.deepcopy(unequal);wrong['pockets'][1]['order']=10;bad('duplicate-pocket-order',wrong,'ORDER')
    for name,order in [('negative-pocket-order',-1),('pocket-order-outside',65536)]:
        wrong=copy.deepcopy(base);wrong['pockets'][0]['order']=order;bad(name,wrong,'ORDER')
    wrong=copy.deepcopy(base);wrong['outer_vertices'][1]['order']=0;bad('duplicate-outer-vertex-order',wrong,'ORDER')
    wrong=copy.deepcopy(base);wrong['pockets'][0]['vertices'][1]['order']=0;bad('duplicate-pocket-vertex-order',wrong,'ORDER')
    wrong=copy.deepcopy(base);wrong['pockets'][0]['vertices'][1]['order']=65536;bad('vertex-order-outside',wrong,'ORDER')
    wrong=copy.deepcopy(base);wrong['outer_vertices'][0]['point_m'][0]=-101;bad('coordinate-outside',wrong,'POINT')
    wrong=copy.deepcopy(base);wrong['pockets'][0]['vertices'][1]['point_m']=wrong['pockets'][0]['vertices'][0]['point_m'];bad('duplicate-point',wrong,'TOPOLOGY')
    wrong=copy.deepcopy(base);wrong['outer_vertices']=vertices([(0,0),(2,0),(4,0),(4,3),(0,3)]);bad('adjacent-collinear',wrong,'TOPOLOGY')
    wrong=copy.deepcopy(base);wrong['outer_vertices']=vertices([(0,0),(4,3),(4,0),(0,3)]);bad('self-crossing-outer',wrong,'TOPOLOGY')
    wrong=copy.deepcopy(base);wrong['pockets'][0]['vertices']=vertices([(1,1),(3,2),(1,2),(3,1)],'inner');bad('self-crossing-pocket',wrong,'TOPOLOGY')
    wrong=copy.deepcopy(base);wrong['outer_vertices']=[];bad('empty-outer',wrong,'VERTEX')
    wrong=copy.deepcopy(base);wrong['outer_vertices']=wrong['outer_vertices'][:2];bad('too-few-outer-vertices',wrong,'VERTEX')
    wrong=copy.deepcopy(base);wrong['pockets'][0]['vertices']=wrong['pockets'][0]['vertices'][:2];bad('too-few-pocket-vertices',wrong,'VERTEX')
    bad('too-many-pockets',recipe(rect(0,0,20,4),[pocket('p'+str(i),i,rect(.5+2*i,1,1.5+2*i,2,True)) for i in range(9)]),'POCKET')
    bad('too-many-total-vertices',recipe(regular(65,10),[],2),'VERTEX')
    wrong=copy.deepcopy(base);wrong['palette']={};bad('empty-palette',wrong,'OKL-E-SURFACE-MATERIAL')
    wrong=copy.deepcopy(maximum_palette);wrong['palette']['extra']=[.2,.2,.2,1];bad('too-many-materials',wrong,'OKL-E-SURFACE-MATERIAL')
    wrong=copy.deepcopy(base);wrong['outer_vertices'][0]['region']='absent';bad('missing-outer-wall-region',wrong,'REGION')
    wrong=copy.deepcopy(base);wrong['pockets'][0]['vertices'][0]['region']='absent';bad('missing-pocket-wall-region',wrong,'REGION')
    wrong=copy.deepcopy(base);wrong['pockets'][0]['floor_region']='absent';bad('missing-floor-region',wrong,'REGION')
    wrong=copy.deepcopy(base);wrong['bottom_region']='absent';bad('missing-bottom-region',wrong,'REGION')
    wrong=copy.deepcopy(base);wrong['top_region']='absent';bad('missing-top-region',wrong,'REGION')
    for name,h in [('zero-height',0),('negative-height',-1),('below-minimum-height',.0005),('above-maximum-height',100.1)]:
        wrong=copy.deepcopy(zero);wrong['height_m']=h;bad(name,wrong,'HEIGHT')
    for name,d in [('zero-depth',0),('negative-depth',-1),('below-minimum-depth',.0005),('above-maximum-depth',100.1)]:
        wrong=copy.deepcopy(base);wrong['pockets'][0]['depth_m']=d;bad(name,wrong,'DEPTH')
    for name,h,d in [('depth-equals-height',2,2),('penetrating-depth',2,2.5),('below-minimum-base',.002,math.nextafter(.001,math.inf))]:
        wrong=copy.deepcopy(base);wrong['height_m']=h;wrong['pockets'][0]['depth_m']=d
        bad(name,wrong,'BASE' if name=='below-minimum-base' else 'DEPTH')
    bad('wrong-height-unit',base,'OKL-E-UNIT',mutate=lambda t:t.replace('Length = 2[m]','Length = 2[s]'))
    bad('wrong-depth-unit',base,'OKL-E-UNIT',mutate=lambda t:t.replace('}, 0.5[m], "floor")','}, 0.5[s], "floor")'))
    bad('wrong-point-unit',base,'OKL-E-UNIT',mutate=lambda t:t.replace('planar_point(0[m], 0[m])','planar_point(0[s], 0[m])',1))
    bad('wrong-floor-region-type',base,'OKL-E-TYPE',mutate=lambda t:t.replace('}, 0.5[m], "floor")','}, 0.5[m], 7)'))
    wrong=copy.deepcopy(unequal);wrong['pockets'][1]['key']='left';bad('duplicate-pocket-key',wrong,'OKL-E-ID')
    wrong=copy.deepcopy(base);wrong['outer_vertices'][1]['key']='v0';bad('duplicate-vertex-key',wrong,'OKL-E-ID')
    add('earlier-version-rejection',base,outcome='invalid',note='The .11 declaring binding cannot use .12 pocket types or constructors; exact phase is not predetermined.',mutate=lambda t:t.replace('"0.12"','"0.11"').replace('"polygon-pockets-0.1"','"framed-polygon-loft-0.1"'))
    add('binary32-pocket-width-collapse',recipe(pockets=[pocket('recess',20,rect(1,1,1.00000001,2,True))]),outcome='source_valid_delivery_rejected',large=True,note='Distinct source x coordinates 1 and 1.00000001 both encode as binary32 1.')
    add('binary32-boundary-clearance',recipe(rect(1,0,5,3),[pocket('recess',20,rect(1.00000001,1,3,2,True))]),outcome='source_valid_delivery_rejected',large=True,note='The positive exterior-to-pocket clearance disappears in delivered binary32 coordinates.')
    add('binary32-between-pockets',recipe(pockets=[pocket('left',10,rect(.5,.5,2,2.5,True)),pocket('right',20,rect(2.00000001,.5,3.5,2.5,True),.75)]),outcome='source_valid_delivery_rejected',large=True,note='Two source-disjoint pocket outlines touch in binary32.')
    collapse=recipe(pockets=[pocket('recess',20,rect(1e-8,1,2,2,True))]);collapse['local_placement_m']=[1,0,0]
    add('binary32-placed-clearance',collapse,outcome='source_valid_delivery_rejected',large=True,note='Rigid local placement collapses the positive source clearance.')
    collapse=recipe(pockets=[pocket('recess',20,rect(1,1,3,2,True),.001)],height=.002);collapse['local_placement_m']=[0,0,16384]
    add('binary32-floor-collapse',collapse,outcome='source_valid_delivery_rejected',large=True,note='After local Z translation, floor 16384.001 and top 16384.002 both encode as binary32 16384.001953125. Precision or topology refusal is required, never resource exhaustion.')
    library=source(base,library=True)
    (out/'parts.ok').write_text(library)
    digest=hashlib.sha256(library.encode()).hexdigest()
    imported=('ontokin "0.12";\nmodule PocketAssembly @ "pocket-assembly";\nprofile "polygon-pockets-0.1";\n\n'
        +'import libparts @ "pocket-parts" from "fixture.pocket-parts" version "1.0.0"\n'
        +'    digest "sha256:'+digest+'";\n\n')
    assembly='''scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object first @ "first": libparts.Shape {
        placement = pose(world, vec3(-5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        pocket_depth = 0.5[m];
    }
    object sibling @ "sibling": libparts.Shape {
        placement = pose(world, vec3(5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
    action travel @ "travel" = move(first, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence { start travel; }
}
'''
    (out/'assembly.ok').write_text(imported+assembly)
    (out/'assembly-repaired.ok').write_text(imported+assembly.replace('pocket_depth = 0.5[m];','pocket_depth = 0.75[m];'))
    (out/'assembly-invalid.ok').write_text(imported+assembly.replace('pocket_depth = 0.5[m];','pocket_depth = 2[m];'))
    generated=imported.replace('PocketAssembly @ "pocket-assembly"','PocketArray @ "pocket-array"')+'''public class Mounted @ "mounted" extends libparts.Shape {
    public param parent_frame @ "parent-frame": FrameRef = world;
    public param mount_x @ "mount-x": Length = 0[m];
    public follow mounting @ "mounting" {
        parent = self.parent_frame;
        child = self;
        offset = pose(self.parent_frame, vec3(self.mount_x, 0[m], 0[m]), quat(1, 0, 0, 0));
    }
}
public class Array @ "array-type" {
    public param depths @ "depths": Keyed<Length> = keyed<Length> {
        "left": 0.25[m], "middle": 0.5[m], "right": 0.75[m]
    };
    geometry = empty();
    physical = no_body();
    public parts trays @ "trays": Mounted for (key, value) in self.depths {
        parent_frame = self.frame;
        mount_x = 20 * value;
        pocket_depth = value;
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
    (out/'generated.ok').write_text(generated)
    expected={'schema_version':'ontokin.polygon-pockets-expectations/0.1','decision':DECISION,
        'frozen_before_implementation':True,'cases':cases,
        'legacy_equivalence':[{'case':c,'source':c+'-legacy.ok','source_version':'0.8','profile':'polygon-extrusion-0.1'} for c in ('zero-pockets','zero-pockets-concave')],
        'ordering_equivalence':[['unequal-depths','declaration-reordering']],
        'assembly':{'entry':'assembly.ok','repaired_entry':'assembly-repaired.ok','invalid_entry':'assembly-invalid.ok',
            'module_id':'pocket-assembly','scene_id':'demo',
            'library':{'source_id':'package:fixture.pocket-parts@1.0.0','filename':'parts.ok','package':'fixture.pocket-parts','version':'1.0.0','sha256':digest},
            'first':measured(base),'repaired_first':measured(repair),'sibling':measured(base),
            'first_placement_m':[-5,0,0],'sibling_placement_m':[5,0,0],
            'sibling_motion_m_per_second':[0,0,0],
            'repair':{'old':'pocket_depth = 0.5[m];','new':'pocket_depth = 0.75[m];'},
            'invalid_edit':{'old':'pocket_depth = 0.5[m];','new':'pocket_depth = 2[m];','diagnostic_code':'OKL-E-POCKETS-DEPTH'}},
        'generated':{'entry':'generated.ok','object_path':'array','parts_member':'trays','root_placement_m':[-10,0,0],
            'parts':[{'key':key,'pocket_depth_m':depth,'offset_m':[20*depth,0,0],
                      'geometry':measured(recipe(pockets=[pocket('recess',20,rect(1,1,3,2,True),depth)]))}
                     for key,depth in [('left',.25),('middle',.5),('right',.75)]]},
        'duration_seconds':1,'sample_times_seconds':[0,.25,.5,.75,1],
        'motion_m_per_second':[0,.5,0],'options':{'fps':4,'end_time_seconds':1},
        'maximum_host_policy':{'max_operations':2000000,'max_elapsed_ms':80000},
        'tolerances':{'geometry_m':1e-5,'area_m2':1e-4,'volume_m3':1e-4,'normal':1e-5,'position_m':.001,'rotation_rad':.001,'material':1e-6},
        'required_geometry_checks':['source-authored bottom/top/wall/floor domains',
            'no filled pocket openings or omitted floors','nonoverlapping complete planar cap coverage',
            'distinct source identities and consistent repeated delivered corners','closed opposite edge incidence',
            'shared-simplex-only triangle contacts','positive signed volume and outward floor normals',
            'exact regional material ownership','current source-to-binary32 geometry','recorded carrier motion'],
        'oracle_adversaries':['removed-floor','reversed-floor','filled-opening','overlapping-cap',
            'swapped-pocket-depths','altered-floor-material','blind-to-through-hole','missing-wall']}
    (out/'expected.json').write_text(json.dumps(expected,indent=2,allow_nan=False)+'\n')
    controls={
        'rectangular_control':{'outer_volume_m3':24,'removed_volume_m3':1,'volume_m3':23,
                               'surface_area_m2':55,'triangle_count':28},
        'minimum_base_exact':ratio(exact(.002)-exact(.001)),
        'minimum_base_endpoint':ratio(exact(.001)),
        'below_minimum_base_exact':ratio(exact(.002)-exact(math.nextafter(.001,math.inf))),
        'floor_collapse_binary32':[struct.unpack('<f',struct.pack('<f',v))[0] for v in [16384.001,16384.002]],
        'product_imports':0,'product_requests':0,'triangle_generation':False,
        'measurement_method':'Exact binary64 rational shoelace areas and rounded floor arithmetic; perimeter from independent boundary lengths',
        'counts':{o:sum(c['expected_outcome']==o for c in cases) for o in ['valid','invalid','source_valid_delivery_rejected']}}
    (out/'ANALYTIC-CONTROLS.json').write_text(json.dumps(controls,indent=2)+'\n')
    if args.decision_commit:
        assert args.decision_file
        files={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(out.iterdir()) if p.is_file() and p.name!='acceptance-freeze.json'}
        freeze={'schema_version':'ontokin.polygon-pockets-freeze/0.1','decision':DECISION,
            'decision_commit':args.decision_commit,'decision_file':'docs/language-design/polygon-pockets-v0.1/ADOPTION.md',
            'decision_sha256':hashlib.sha256(args.decision_file.read_bytes()).hexdigest(),
            'source_baseline_commit':BASELINE,'independent_author':'/root/pocket_fixtures',
            'independent_method':'Standard-library boundary arithmetic without OntoKin imports or product requests',
            'product_imports':0,'product_requests':0,'frozen_before_implementation':True,
            'case_count':len(cases),'outcome_counts':controls['counts'],
            'source_count':sum(p.suffix=='.ok' for p in out.iterdir()),'files':files}
        (out/'acceptance-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
    print(json.dumps({'status':'authored','cases':len(cases),'outcome_counts':controls['counts'],
                      'source_files':len(list(out.glob('*.ok'))),'product_imports':0,'product_requests':0}))


if __name__=='__main__':
    main()
