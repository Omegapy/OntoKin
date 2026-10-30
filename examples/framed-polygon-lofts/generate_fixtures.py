#!/usr/bin/env python3
"""Author C078 source and independent finite geometry expectations.

Only Python's standard library is used. No OntoKin import or product request
occurs. Source transforms use Decimal normalization and Fraction arithmetic.
Square endpoint diagonals are specified by hand. Planar cap measurements use
oriented boundary integrals, not an implementation of the cap triangulator.
"""
from collections import Counter
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math

DECISION_COMMIT = '69b80f683073b0c9b75f06014933f0e9939c1f5d'
DECISION_SHA256 = 'd7ffa4e162fb29cfa2f2bbcee4133ea588272a33a52383e632425c70d1927370'

HERE = Path(__file__).resolve().parent
PALETTE = {'bottom': [.3,.35,.4,1], 'inner': [.15,.65,.3,1],
           'outer': [.7,.3,.1,1], 'top': [.1,.5,.8,1]}
REQUEST = {'max_operations': 2000000, 'max_elapsed_ms': 80000}
I = (1,0,0,0)
Y90 = (.7071067811865476,0,.7071067811865476,0)
Y180 = (0,0,1,0)
Y270 = (.7071067811865476,0,-.7071067811865476,0)
CYCLIC = (.5,.5,.5,.5)


def number(x):
    return str(x) if isinstance(x, str) else format(Decimal(str(x)), 'f')


def quantity(x):
    return x if isinstance(x, str) else number(x) + '[m]'


def ring(key, points, role='outer', order=20, region=None):
    return {'key':key,'order':order,'role':role,'vertices':[
        {'key':'v'+str(i),'order':i*10,'point_m':list(p),
         'region':region or ('outer' if role=='outer' else 'inner')}
        for i,p in enumerate(points)]}


def square(half=1, role='outer', key=None, center=(0,0), order=None):
    x,y=center
    points=[(x-half,y-half),(x+half,y-half),(x+half,y+half),(x-half,y+half)]
    if role=='hole':points=points[::-1]
    return ring(key or ('outer' if role=='outer' else 'opening'),points,role,
                order if order is not None else (20 if role=='outer' else 40))


def section(key, origin, rotation, rings, order):
    return {'key':key,'order':order,'origin_m':list(origin),
            'authored_orientation_wxyz':list(rotation),'frame_reference':'self.frame',
            'rings':deepcopy(rings)}


def chain(rings, frames):
    return [section('s'+str(i),origin,q,rings,10*(i+1)) for i,(origin,q) in enumerate(frames)]


def straight(rings, origins=((0,0,0),(0,0,4)), q=I):
    return chain(rings,[(p,q) for p in origins])


def ring_source(rings, indent):
    pad=' '*indent; chunks=[]
    for r in rings:
        vertices=[pad+'    '+json.dumps(v['key'])+': polygon_vertex('+number(v['order'])+
                  ', planar_point('+quantity(v['point_m'][0])+', '+quantity(v['point_m'][1])+'), '+
                  json.dumps(v['region'])+')' for v in r['vertices']]
        chunks.append(pad+json.dumps(r['key'])+': polygon_ring('+number(r['order'])+', '+
                      json.dumps(r['role'])+', keyed<PolygonVertex> {\n'+',\n'.join(vertices)+'\n'+pad+'})')
    return 'keyed<PolygonRing> {\n'+',\n'.join(chunks)+'\n'+' '*(indent-4)+'}'


def pose_source(s):
    if 'frame_expression' in s:return s['frame_expression']
    return ('pose('+s.get('frame_reference','self.frame')+', vec3('+', '.join(map(quantity,s['origin_m']))+
        '), quat('+', '.join(map(number,s['authored_orientation_wxyz']))+'))')


def sections_source(sections, indent=8):
    pad=' '*indent
    return 'keyed<FramedPolygonSection> {\n'+',\n'.join(
        pad+json.dumps(s['key'])+': framed_polygon_section('+number(s['order'])+', '+pose_source(s)+', '+
        ring_source(s['rings'],indent+4)+')' for s in sections)+'\n'+' '*(indent-4)+'}'


def palette_source(palette):
    return 'keyed<SurfaceMaterial> {\n'+',\n'.join(
        '        '+json.dumps(k)+': surface_material(rgba('+', '.join(map(number,v))+'), 0.1, 0.65)'
        for k,v in palette.items())+'\n    }'


def header(name='FramedLoftCase', key='framed-loft-case', request=None):
    s='ontokin "0.11";\nmodule '+name+' @ "'+key+'";\nprofile "framed-polygon-loft-0.1";\n'
    if request:s+='\nexecution { max_operations = '+str(request['max_operations'])+'; max_elapsed = '+str(request['max_elapsed_ms']//1000)+'[s]; }\n'
    return s


def scene(extra=''):
    return '\nscene Demo @ "demo" {\n    duration = 1[s];\n'+\
        '    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);\n'+\
        '    object shape @ "shape": Shape {\n'+\
        '        placement = pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n    }\n'+extra+\
        '    action travel @ "travel" = move(shape, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);\n'+\
        '    at 0[s] sequence { start travel; }\n}\n'


def source(sections, palette=None, bottom='bottom', top='top', placement=None, request=None):
    palette=PALETTE if palette is None else palette
    geometry='loft_framed_rings(self.sections, self.palette, '+json.dumps(bottom)+', '+json.dumps(top)+')'
    if placement:
        p,q=placement
        geometry='placed('+geometry+', pose(self.frame, vec3('+', '.join(map(quantity,p))+'), quat('+', '.join(map(number,q))+')))'
    return header(request=request)+'\npublic class Shape @ "shape" {\n'+\
        '    public param sections @ "sections": Keyed<FramedPolygonSection> = '+sections_source(sections)+';\n'+\
        '    public param palette @ "palette": Keyed<SurfaceMaterial> = '+palette_source(palette)+';\n'+\
        '    geometry = '+geometry+';\n    physical = no_body();\n}\n'+scene()


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def rational(x):return F(float(x))
def pair(x):return [str(x.numerator),str(x.denominator)]


def canonical_q(raw):
    """Independent high-precision evaluation of the adopted source constructor."""
    def calculate(precision):
        with localcontext() as ctx:
            ctx.prec=precision
            values=[Decimal.from_float(float(x)) for x in raw]
            norm=sum(x*x for x in values).sqrt()
            assert norm and abs(norm-1)<=Decimal('1e-12')
            result=[float(x/norm) for x in values]
            if next(x for x in result if x)!=abs(next(x for x in result if x)):
                result=[-x for x in result]
            return [x if x else 0.0 for x in result]
    low,high=calculate(110),calculate(180)
    assert low==high
    return high


def matrix(q):
    w,x,y,z=map(rational,q);d=w*w+x*x+y*y+z*z
    return [[v/d for v in row] for row in [
        [w*w+x*x-y*y-z*z,2*(x*y-w*z),2*(x*z+w*y)],
        [2*(x*y+w*z),w*w-x*x+y*y-z*z,2*(y*z-w*x)],
        [2*(x*z-w*y),2*(y*z+w*x),w*w-x*x-y*y+z*z]]]


def point(s,xy):
    r=matrix(s['orientation_wxyz']);p=[rational(x) for x in [*xy,0]]
    result=[float(rational(o)+dot(row,p)) for o,row in zip(s['origin_m'],r)]
    return tuple(F(x if x else 0.) for x in result)


def ordered(sections):
    result=deepcopy(sorted(sections,key=lambda s:s['order']))
    for s in result:
        s['orientation_wxyz']=canonical_q(s['authored_orientation_wxyz'])
        s['rings'].sort(key=lambda r:r['order'])
        for r in s['rings']:r['vertices'].sort(key=lambda v:v['order'])
    return result


def local_area(s):
    total=F(0)
    for ring in s['rings']:
        pts=[list(map(rational,v['point_m'])) for v in ring['vertices']]
        total+=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(pts,pts[1:]+pts[:1]))/2
    return total


def cap_measure(s):
    """Hand-specified convex quadrilateral, or planar oriented boundary integral."""
    rings=[[point(s,v['point_m']) for v in r['vertices']] for r in s['rings']]
    if len(rings)==1 and len(rings[0])==4:
        p=rings[0];tris=[(p[0],p[1],p[2]),(p[0],p[2],p[3])]
        volume6=sum(dot(a,cross(b,c)) for a,b,c in tris)
        area=sum(math.sqrt(float(dot(n:=cross(sub(b,a),sub(c,a)),n)))/2 for a,b,c in tris)
        return volume6,area,'authored-square-or-convex-quadrilateral-diagonal-v0-v2'
    anchor=rings[0][0]
    normal=cross(sub(rings[0][1],anchor),sub(rings[0][2],anchor))
    assert dot(normal,normal)>0
    assert all(dot(normal,sub(p,anchor))==0 for r in rings for p in r)
    area_vector=[sum(cross(a,b)[i] for r in rings for a,b in zip(r,r[1:]+r[:1])) for i in range(3)]
    return dot(anchor,area_vector),math.sqrt(float(dot(area_vector,area_vector)))/2,'planar-oriented-boundary-integral'


def geometry(sections, palette=None, bottom='bottom', top='top', placement=None):
    sections=ordered(sections);first,last=sections[0],sections[-1]
    n=sum(len(r['vertices']) for r in first['rings']);h=len(first['rings'])-1
    cap=n+2*h-2;cap0,a0,method0=cap_measure(first);cap1,a1,method1=cap_measure(last)
    volume6=cap1-cap0;wall_area=0.;regions=Counter({bottom:cap});regions[top]+=cap
    positions=[]
    for s in sections:
        for r in s['rings']:
            for v in r['vertices']:
                p=point(s,v['point_m'])
                positions.append({'identity':[s['key'],r['key'],v['key']],
                                  'position_m':list(map(float,p)),'position_hex':[float(x).hex() for x in p]})
    for lower,upper in zip(sections,sections[1:]):
        for r0,r1 in zip(lower['rings'],upper['rings']):
            for i,v0 in enumerate(r0['vertices']):
                j=(i+1)%len(r0['vertices'])
                a,b=point(lower,v0['point_m']),point(lower,r0['vertices'][j]['point_m'])
                c,d=point(upper,r1['vertices'][i]['point_m']),point(upper,r1['vertices'][j]['point_m'])
                for p,q,r in [(a,b,c),(b,d,c)]:
                    volume6+=dot(p,cross(q,r));normal=cross(sub(q,p),sub(r,p))
                    assert dot(normal,normal)>0
                    wall_area+=math.sqrt(float(dot(normal,normal)))/2
                regions[v0['region']]+=2
    volume=volume6/6
    assert volume>0
    points=[p['position_m'] for p in positions]
    progression=[]
    for a,b in zip(sections,sections[1:]):
        d=sub(tuple(map(rational,b['origin_m'])),tuple(map(rational,a['origin_m'])))
        normal0=[row[2] for row in matrix(a['orientation_wxyz'])]
        normal1=[row[2] for row in matrix(b['orientation_wxyz'])]
        values=[dot(d,d),dot(d,normal0),dot(d,normal1)]
        assert values[0]>=F(.001)**2 and values[1]>0 and values[2]>0
        progression.append({'from':a['key'],'to':b['key'],'squared_distance_exact':pair(values[0]),
                            'previous_normal_dot_exact':pair(values[1]),'next_normal_dot_exact':pair(values[2])})
    result={'sections':sections,'surface_rule':'fixed-diagonal-triangles',
        'section_transform_rule':'exact-rational-quaternion-single-round',
        'section_count':len(sections),'ring_count':len(first['rings']),'hole_count':h,
        'vertices_per_section':n,'authored_vertex_count':len(sections)*n,
        'cap_triangle_count':cap,'strip_triangle_count':2*(len(sections)-1)*n,
        'triangle_count':2*len(sections)*n+4*h-4,'vertex_count':3*(2*len(sections)*n+4*h-4),
        'cap_areas_m2':[a0,a1],'section_areas_m2':[float(local_area(s)) for s in sections],
        'volume_m3':float(volume),'volume_exact':pair(volume),'surface_area_m2':a0+a1+wall_area,
        'cap_measure_methods':[method0,method1],'region_triangle_counts':dict(sorted(regions.items())),
        'bounds_m':[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]],
        'palette':deepcopy(PALETTE if palette is None else palette),'metallic':.1,'roughness':.65,
        'source_positions':positions,'progression':progression}
    if placement:result['local_position_m'],result['local_orientation_wxyz']=placement
    return result


def main():
    cases=[]
    def add(name,sections,outcome='valid',code=None,note=None,**options):
        (HERE/(name+'.ok')).write_text(source(sections,**options))
        item={'id':name,'source':name+'.ok','expected_outcome':outcome}
        if code:item['diagnostic_code']=code
        if note:item['note']=note
        if options.get('request'):item['execution_request']=options['request']
        if outcome!='invalid':item['geometry']=geometry(sections,**{k:v for k,v in options.items() if k!='request'})
        cases.append(item);return item
    def invalid(name,base,change,code,note=None,**options):
        data=deepcopy(base);change(data);return add(name,data,'invalid',code,note,**options)
    def analytic(item,volume,area,formula):
        g=item['geometry'];assert math.isclose(g['volume_m3'],volume,rel_tol=1e-13,abs_tol=1e-12)
        assert math.isclose(g['surface_area_m2'],area,rel_tol=1e-13,abs_tol=1e-12)
        g['analytic_control']={'volume_m3':volume,'surface_area_m2':area,'expression':formula}

    solid=straight([square()]);hollow=straight([square(),square(.5,'hole')])
    elbow_frames=[((0,0,0),I),((4,0,4),Y90)]
    handle_frames=[*elbow_frames,((8,0,0),Y180)]
    elbow=chain([square()],elbow_frames);duct=chain([square(),square(.5,'hole')],elbow_frames)
    handle=chain([square()],handle_frames);hollow_handle=chain([square(),square(.5,'hole')],handle_frames)
    analytic(add('identity-solid',solid),16,40,'A=4,P=8,h=4; V=A*h; surface=2*A+P*h')
    analytic(add('identity-hollow',hollow),12,54,'A=4-1,P=8+4,h=4; V=A*h; surface=2*A+P*h')
    analytic(add('cyclic-rigid-rotation',straight([square()],((0,0,0),(4,0,0)),CYCLIC)),16,40,'Exact cyclic permutation preserves the identity solid')
    add('sign-equivalent-rotation',straight([square()],((0,0,0),(4,0,0)),tuple(-v for v in CYCLIC)))
    analytic(add('equal-component-y90',straight([square()],((-2,1,3),(2,1,3)),Y90)),16,40,'Equal canonical w=y gives exact Y90 after division by q dot q')
    analytic(add('bent-solid',elbow),16,24+16*math.sqrt(2),'Independent prescribed-face elbow: V=16; A=24+16sqrt(2)')
    analytic(add('hollow-elbow',duct),12,30+24*math.sqrt(2),'Outer elbow minus half-size opening: V=12; A=30+24sqrt(2)')
    analytic(add('solid-handle',handle),32,40+32*math.sqrt(2),'Two elbow intervals: V=32; A=40+32sqrt(2)')
    analytic(add('hollow-handle',hollow_handle),24,54+48*math.sqrt(2),'Two hollow intervals: V=24; A=54+48sqrt(2)')
    concave=ring('outer',[(-.5,-.5),(.5,-.5),(.5,0),(0,0),(0,.5),(-.5,.5)])
    add('concave-elbow',chain([concave],elbow_frames))
    multi=[square(2),square(.25,'hole','left',(-.75,0),40),square(.25,'hole','right',(.75,0),60)]
    multiple=chain(multi,[((0,0,0),I),((6,0,6),Y90)])
    add('multiple-hole-elbow',multiple)
    reordered=deepcopy(multiple);reordered.reverse()
    for s in reordered:
        s['rings'].reverse()
        for r in s['rings']:r['vertices'].reverse()
    add('reordered-sections-rings-vertices',reordered)
    mixed=deepcopy(hollow_handle)
    mixed[0]['rings'][0]['vertices'][0]['region']='top'
    for v in mixed[1]['rings'][0]['vertices']:v['region']='inner'
    for r in mixed[-1]['rings']:
        for v in r['vertices']:v['region']='bottom'
    add('mixed-strip-materials',mixed)
    palette=deepcopy(PALETTE);palette.update({'unused'+str(i):[i/12,.2,.3,1] for i in range(12)})
    add('maximum-palette',solid,palette=palette)
    add('negative-origins',straight([square()],((-4,-3,-2),(-4,-3,2))))
    add('component-boundaries',straight([square(100)],((-100,-100,-100),(-100,-100,100))))
    add('minimum-origin-separation',straight([square()],((0,0,0),(0,0,.001))))
    add('diagonal-origin-separation',straight([square()],((0,0,0),(.0008,0,.0008))),note='Euclidean origin distance exceeds 0.001 although the forward Z component is smaller')
    add('placed-hollow-handle',hollow_handle,placement=([2,-1,.5],[0,1,0,0]))
    near=straight([square(.1)],((0,0,0),(4,0,.000003814697265625)))
    near[1]['authored_orientation_wxyz']=[.00000095367431640625,0,.9999999999995453,0]
    near_case=add('near-half-turn-admitted',near,note='Both exact forward dots are positive; the carrier-XZ side quadrilateral is strictly convex, so no extra angle cutoff is allowed')
    # Every side is extruded unchanged in Y; a convex XZ domain proves closure
    s0,s1=near_case['geometry']['sections']
    poly=[point(s0,[-.1,-.1]),point(s0,[.1,-.1]),point(s1,[.1,-.1]),point(s1,[-.1,-.1])]
    turns=[]
    for i in range(4):
        a,b,c=poly[i],poly[(i+1)%4],poly[(i+2)%4]
        turns.append((b[0]-a[0])*(c[2]-b[2])-(b[2]-a[2])*(c[0]-b[0]))
    assert all(x>0 for x in turns)
    near_case['geometry']['convex_xz_control']={'ordered_points_m':[[float(p[0]),float(p[2])] for p in poly],
        'strictly_positive_turns_exact':[pair(x) for x in turns],
        'proof':'This strictly convex XZ quadrilateral, extruded over Y in [-0.1,0.1], is exactly the prescribed closed triangular surface'}
    nonplanar=straight([ring('outer',[(-.7,-.3),(1.1,-.4),(.8,.9),(-.5,1.3)])],
                      ((.1,.2,.3),(3.1,-2.2,3.3)),(.8,.36,.48,0))
    warp=add('rounded-nonplanar-caps',nonplanar,note='Exact single-round source coordinates make endpoint cap quadrilaterals nonplanar; authored XY diagonal v0-v2 remains authoritative')
    controls=[]
    for s in warp['geometry']['sections']:
        p=[point(s,v['point_m']) for v in s['rings'][0]['vertices']]
        det=dot(sub(p[3],p[0]),cross(sub(p[1],p[0]),sub(p[2],p[0])))
        assert det
        controls.append({'section':s['key'],'nonplanarity_determinant_exact':pair(det),'required_cap_diagonal':['v0','v2']})
    warp['geometry']['nonplanar_cap_controls']=controls
    rounding=[]
    for s in warp['geometry']['sections']:
        r=matrix(s['orientation_wxyz']);d=sum(rational(x)**2 for x in s['orientation_wxyz'])
        for vertex in s['rings'][0]['vertices']:
            v=[*map(rational,vertex['point_m']),F(0)]
            for i,(row,origin) in enumerate(zip(r,s['origin_m'])):
                rotated=dot(row,v);correct=float(rational(origin)+rotated)
                staged=float(float(rotated)+float(origin));no_denominator=float(rational(origin)+rotated*d)
                if staged!=correct or no_denominator!=correct:
                    rounding.append({'identity':[s['key'],'outer',vertex['key']],'component':i,
                        'required_hex':correct.hex(),'separately_rounded_translation_hex':staged.hex(),
                        'omitted_denominator_hex':no_denominator.hex()})
    assert any(v['required_hex']!=v['separately_rounded_translation_hex'] for v in rounding)
    assert any(v['required_hex']!=v['omitted_denominator_hex'] for v in rounding)
    warp['geometry']['single_round_controls']=rounding
    quarter=straight([square()],((0,0,0),(0,0,1)))
    quarter[1]['authored_orientation_wxyz']=[.7071067811865476,0,0,.7071067811865476]
    analytic(add('authoritative-frame-quarter-turn',quarter),4,16,'Positive quarter-turn framed correspondence defines a 2x2x1 box')
    outer8=ring('outer',[(-8,-10),(8,-10),(10,-8),(10,8),(8,10),(-8,10),(-10,8),(-10,-8)])
    centers=[(x,y) for y in (-3,3) for x in (-6,-2,2,6)]
    holes3=[ring('h'+str(i),[(x-.5,y-.5),(x,y+.5),(x+.5,y-.5)],'hole',40+i*10) for i,(x,y) in enumerate(centers)]
    outer32=ring('outer',[(round(10*math.cos(i*math.pi/16),6),round(10*math.sin(i*math.pi/16),6)) for i in range(32)])
    holes4=[square(.5,'hole','h'+str(i),c,40+i*10) for i,c in enumerate(centers)]
    add('maximum-sections-and-total',straight([outer8]+holes3,[(i,0,0) for i in range(8)],CYCLIC),request=REQUEST)
    add('maximum-vertices-and-total',straight([outer32]+holes4,[(i,0,0) for i in range(4)],CYCLIC),request=REQUEST)

    L='OKL-E-FRAMED-LOFT-';H='OKL-E-HOLES-'
    add('empty-sections',[],'invalid',L+'SECTION')
    add('one-section',solid[:1],'invalid',L+'SECTION')
    add('too-many-sections',straight([square()],[(0,0,i) for i in range(9)]),'invalid',L+'SECTION')
    add('too-many-total-vertices',straight([outer32]+holes4,[(i,0,0) for i in range(5)],CYCLIC),'invalid',L+'SECTION',request=REQUEST)
    outer33=ring('outer',[(round(10*math.cos(i*2*math.pi/33),6),round(10*math.sin(i*2*math.pi/33),6)) for i in range(33)])
    add('too-many-vertices-per-section',straight([outer33]+holes4),'invalid',H+'VERTEX',request=REQUEST)
    invalid('duplicate-section-key',solid,lambda s:s[1].update(key='s0'),'OKL-E-ID')
    invalid('duplicate-section-order',solid,lambda s:s[1].update(order=10),L+'ORDER')
    invalid('section-order-outside',solid,lambda s:s[1].update(order=65536),L+'ORDER')
    invalid('world-frame',solid,lambda s:s[0].update(frame_reference='world'),L+'FRAME')
    invalid('wrong-frame-type',solid,lambda s:s[0].update(frame_expression='2[m]'),'OKL-E-TYPE')
    invalid('nonrigid-frame-substitute',solid,lambda s:s[0].update(frame_expression='vec3(1, 1, 1)'),'OKL-E-TYPE')
    invalid('wrong-origin-unit',solid,lambda s:s[0].update(frame_expression='pose(self.frame, vec3(0[s], 0[s], 0[s]), quat(1, 0, 0, 0))'),'OKL-E-UNIT')
    invalid('wrong-origin-type',solid,lambda s:s[0].update(frame_expression='pose(self.frame, "origin", quat(1, 0, 0, 0))'),'OKL-E-TYPE')
    invalid('zero-quaternion',solid,lambda s:s[0].update(authored_orientation_wxyz=[0,0,0,0]),'OKL-E-ROTATION')
    invalid('nonunit-quaternion',solid,lambda s:s[0].update(authored_orientation_wxyz=[1,0,1,0]),'OKL-E-ROTATION')
    invalid('origin-outside',solid,lambda s:s[0].update(origin_m=[100.001,0,0]),L+'FRAME')
    invalid('coincident-origins',solid,lambda s:s[1].update(origin_m=[0,0,0]),L+'PROGRESSION')
    invalid('sideways-progression',solid,lambda s:s[1].update(origin_m=[4,0,0]),L+'PROGRESSION')
    invalid('reversed-progression',solid,lambda s:s[1].update(origin_m=[0,0,-4]),L+'PROGRESSION')
    invalid('next-frame-reversed',solid,lambda s:s[1].update(authored_orientation_wxyz=list(Y180)),L+'PROGRESSION')
    invalid('near-reversed-progression',solid,lambda s:s[1].update(authored_orientation_wxyz=[.00000001,0,1,0]),L+'PROGRESSION')
    invalid('below-minimum-separation',solid,lambda s:s[1].update(origin_m=[0,0,.000999]),L+'PROGRESSION')
    add('rounded-decimal-separation',straight([square()],((0,0,1),(0,0,1.001))),'invalid',L+'PROGRESSION',
        'Exact binary64 1.001 minus 1 is below the binary64 0.001 separation threshold')
    invalid('changed-vertex-key',solid,lambda s:s[1]['rings'][0]['vertices'][1].update(key='other'),L+'CORRESPONDENCE')
    invalid('missing-ring',hollow,lambda s:s[1]['rings'].pop(),L+'CORRESPONDENCE')
    invalid('coordinate-outside',solid,lambda s:s[1]['rings'][0]['vertices'][0].update(point_m=[-101,-1]),H+'POINT')
    invalid('missing-strip-region',solid,lambda s:s[0]['rings'][0]['vertices'][0].update(region='missing'),H+'REGION')
    invalid('missing-terminal-region',solid,lambda s:s[1]['rings'][0]['vertices'][0].update(region='missing'),H+'REGION')
    add('missing-cap-region',solid,'invalid',L+'REGION',top='missing')
    invalid('hole-outside',hollow,lambda s:s[1]['rings'].__setitem__(1,square(.25,'hole',center=(3,0))),H+'CONTAINMENT')
    def reversed_ring(s):
        values=[v['point_m'] for v in s[1]['rings'][0]['vertices']][::-1]
        for v,p in zip(s[1]['rings'][0]['vertices'],values):v['point_m']=p
    invalid('clockwise-outer',solid,reversed_ring,H+'WINDING')
    invalid('strip-diagonal-pinch',straight([square()],((0,0,0),(0,0,1))),
            lambda s:s[1].update(authored_orientation_wxyz=[.7071067811865476,0,0,-.7071067811865476]),L+'TOPOLOGY',
            'Negative quarter-turn creates nonshared diagonal intersection at (0,0,0.5)')
    invalid('correspondence-edge-pinch',straight([square()],((0,0,0),(0,0,1))),
            lambda s:s[1].update(authored_orientation_wxyz=[0,0,0,1]),L+'TOPOLOGY',
            'Half-turn about local +Z keeps forward progression but correspondence edges meet')
    add('bent-distinct-identity-collapse',chain([square()],[((0,0,0),I),((1,0,1),Y90)]),'invalid',L+'TOPOLOGY',
        'Forward progression passes, but s0/outer/v1 and s1/outer/v1 both occupy (1,-1,0)')
    add('source-cap-rounding-collapse',straight([ring('outer',[(0,-1),(.000000000000001,-1),(.000000000000001,1),(0,1)])],
        ((100,0,0),(100,0,4))),'invalid',L+'TOPOLOGY',
        'The authored XY rings are simple, but exact origin addition followed by binary64 rounding collapses each cap to x=100')
    def swap(s):
        for a,b in zip(s[1]['rings'][1]['vertices'],s[1]['rings'][2]['vertices']):a['point_m'],b['point_m']=b['point_m'],a['point_m']
    invalid('swapped-hole-collision',straight(multi),swap,L+'TOPOLOGY')
    loop=chain([square()],[( (0,0,0),I),((4,0,4),Y90),((8,0,0),Y180),((4,0,-4),Y270),((0,0,.5),I)])
    contact=add('nonadjacent-section-contact',loop,'invalid',L+'TOPOLOGY',
        'Final s4/outer/v1=(1,-1,0.5) lies strictly inside the first s0-s1 strip triangle')
    contact['independent_witness']={'point_m':[1,-1,.5],
        'vertex_identity':['s4','outer','v1'],
        'triangle_identities':[['s0','outer','v0'],['s0','outer','v1'],['s1','outer','v0']],
        'barycentric_exact':[['3','20'],['3','4'],['1','10']]}
    crossowner=add('cross-owner-section-escape',solid,'invalid',L+'FRAME',
        'The second occurrence consumes immutable sections constructed for shape; it must reject their foreign owning frame')
    p=HERE/crossowner['source'];base=p.read_text();p.write_text(base.replace(scene(),scene(
        '    object thief @ "thief": Shape {\n        placement = pose(world, vec3(5[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n        sections = shape.sections;\n    }\n')))
    functions='''
public fn make_section @ "make-section"(order: Int, frame: Pose, rings: Keyed<PolygonRing>) -> FramedPolygonSection {
    return framed_polygon_section(order, frame, rings);
}
public fn make_geometry @ "make-geometry"(sections: Keyed<FramedPolygonSection>, palette: Keyed<SurfaceMaterial>) -> Geometry {
    return loft_framed_rings(sections, palette, "bottom", "top");
}
'''
    for name,outcome,code in [('function-section-and-geometry','valid',None),('function-cross-owner-escape','invalid',L+'FRAME')]:
        item=add(name,solid,outcome,code,note='Free functions must retain the consuming carrier context without capturing lexical self')
        p=HERE/item['source'];raw=p.read_text().replace('framed_polygon_section(','make_section(').replace(
            'loft_framed_rings(self.sections, self.palette, "bottom", "top")','make_geometry(self.sections, self.palette)')
        raw=raw.replace('\npublic class Shape',functions+'\npublic class Shape')
        if outcome=='invalid':raw=raw.replace(scene(),scene('    object thief @ "thief": Shape {\n        placement = pose(world, vec3(5[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n        sections = shape.sections;\n    }\n'))
        p.write_text(raw)
    earlier=add('earlier-version-rejection',solid,'invalid',note='A .10 declaring module must reject the new framed section type and constructor')
    p=HERE/earlier['source'];p.write_text(p.read_text().replace('ontokin "0.11"','ontokin "0.10"').replace('profile "framed-polygon-loft-0.1"','profile "polygon-loft-0.1"'))

    thin=[square(4),ring('opening',[(2,1),(2.00000001,1),(2.00000001,-1),(2,-1)],'hole',40)]
    add('binary32-hole-collapse',straight(thin),'source_valid_delivery_rejected',note='Distinct source hole edges share their delivered binary32 X coordinate')
    clearance=[ring('outer',[(1,-2),(5,-2),(5,2),(1,2)]),ring('opening',[(1.00000001,1),(3,1),(3,-1),(1.00000001,-1)],'hole',40)]
    add('binary32-rotated-boundary-clearance',straight(clearance,((0,0,0),(4,0,0)),CYCLIC),'source_valid_delivery_rejected',note='Cyclic rotation places the collapsing outer-hole clearance along carrier Y')
    placed=[ring('outer',[(0,-2),(4,-2),(4,2),(0,2)]),ring('opening',[(.00000001,1),(2,1),(2,-1),(.00000001,-1)],'hole',40)]
    add('binary32-placed-clearance',straight(placed),'source_valid_delivery_rejected',placement=([1,0,0],[1,0,0,0]),note='Separate outer local placement removes strict binary32 opening clearance')

    # Exact .10 comparison sources are new companions, never edits to old fixtures
    references=[]
    for name,data in [('identity-solid',solid),('identity-hollow',hollow)]:
        text=source(data).replace('ontokin "0.11"','ontokin "0.10"').replace('profile "framed-polygon-loft-0.1"','profile "polygon-loft-0.1"')
        text=text.replace('FramedPolygonSection','PolygonSection').replace('loft_framed_rings','loft_rings')
        for s in data:text=text.replace('framed_polygon_section('+number(s['order'])+', '+pose_source(s),
                                       'polygon_section('+number(s['order'])+', '+quantity(s['origin_m'][2]))
        path=name+'-legacy.ok';(HERE/path).write_text(text)
        references.append({'case':name,'source':path,'source_version':'0.10','profile':'polygon-loft-0.1'})

    # The library constructs each frame in its own carrier; only a Length is overridden
    library=header('FramedLoftParts','framed-loft-parts')+'\npublic class Shape @ "shape" {\n'
    library+='    public param end_x @ "end-x": Length = 4[m];\n'
    library+='    public param rise @ "rise": Length = 4[m];\n'
    library+='    public param rings @ "rings": Keyed<PolygonRing> = '+ring_source(duct[0]['rings'],8)+';\n'
    library+='    public param palette @ "palette": Keyed<SurfaceMaterial> = '+palette_source(PALETTE)+';\n'
    library+='    geometry = loft_framed_rings(keyed<FramedPolygonSection> {\n'
    library+='        "s0": framed_polygon_section(10, pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0)), self.rings),\n'
    library+='        "s1": framed_polygon_section(20, pose(self.frame, vec3(self.end_x, 0[m], self.rise), quat(0.7071067811865476, 0, 0.7071067811865476, 0)), self.rings)\n'
    library+='    }, self.palette, "bottom", "top");\n    physical = no_body();\n}\n'
    (HERE/'parts.ok').write_text(library);digest=hashlib.sha256(library.encode()).hexdigest()
    imp='import libparts @ "framed-loft-parts" from "fixture.framed-loft-parts" version "1.0.0"\n    digest "sha256:'+digest+'";\n'
    assembly=header('FramedLoftAssembly','framed-loft-assembly')+'\n'+imp+'\nscene Demo @ "demo" {\n    duration = 1[s];\n'
    assembly+='    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);\n'
    assembly+='    object first @ "first": libparts.Shape {\n        placement = pose(world, vec3(-6[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n        end_x = 4[m];\n    }\n'
    assembly+='    object sibling @ "sibling": libparts.Shape {\n        placement = pose(world, vec3(6[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n    }\n'
    assembly+='    action travel @ "travel" = move(first, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);\n    at 0[s] sequence { start travel; }\n}\n'
    old='end_x = 4[m];';new='end_x = 5[m];';bad='end_x = -1[m];'
    assert assembly.count(old)==1
    for filename,text in [('assembly.ok',assembly),('assembly-repaired.ok',assembly.replace(old,new)),('assembly-invalid.ok',assembly.replace(old,bad))]:(HERE/filename).write_text(text)
    repaired=deepcopy(duct);repaired[1]['origin_m'][0]=5
    add('repaired-hollow-elbow',repaired)
    generated=header('FramedLoftArray','framed-loft-array')+'\n'+imp+'''
public class Mounted @ "mounted" extends libparts.Shape {
    public param parent_frame @ "parent-frame": FrameRef = world;
    public param mount_y @ "mount-y": Length = 0[m];
    public follow mounting @ "mounting" {
        parent = self.parent_frame;
        child = self;
        offset = pose(self.parent_frame, vec3(0[m], self.mount_y, 0[m]), quat(1, 0, 0, 0));
    }
}
public class Array @ "array-type" {
    public param rises @ "rises": Keyed<Length> = keyed<Length> {
        "low": 3[m], "middle": 4[m], "high": 5[m]
    };
    geometry = empty();
    physical = no_body();
    public parts ducts @ "ducts": Mounted for (key, value) in self.rises {
        parent_frame = self.frame;
        mount_y = 3 * value;
        rise = value;
    }
}
scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object array @ "array": Array {
        placement = pose(world, vec3(0[m], -12[m], 0[m]), quat(1, 0, 0, 0));
    }
    action travel @ "travel" = move(array, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence { start travel; }
}
'''
    (HERE/'generated.ok').write_text(generated)
    parts={}
    for key,rise in [('low',3),('middle',4),('high',5)]:
        data=deepcopy(duct);data[1]['origin_m'][2]=rise
        parts[key]={'geometry':geometry(data),'mount_y_m':3*rise}
    expected={'schema_version':'ontokin.framed-polygon-loft-expectations/0.1','decision':'OK-LANG-011/0.1.0',
        'frozen_before_implementation':True,'cases':cases,'legacy_equivalence':references,
        'assembly':{'entry':'assembly.ok','repaired_entry':'assembly-repaired.ok','invalid_entry':'assembly-invalid.ok',
          'module_id':'framed-loft-assembly','scene_id':'demo',
          'library':{'source_id':'package:fixture.framed-loft-parts@1.0.0','filename':'parts.ok',
            'package':'fixture.framed-loft-parts','version':'1.0.0','sha256':digest},
          'first':geometry(duct),'sibling':geometry(duct),'repaired_first':geometry(repaired),
          'first_placement_m':[-6,0,0],'sibling_placement_m':[6,0,0],
          'repair':{'old':old,'new':new,'section_key':'s1','field':'origin_m[0]'},
          'invalid_edit':{'old':old,'new':bad,'diagnostic_code':L+'PROGRESSION'},
          'sibling_motion_m_per_second':[0,0,0]},
        'generated':{'entry':'generated.ok','object_path':'array','parts_member':'ducts',
          'root_placement_m':[0,-12,0],'parts':parts},
        'duration_seconds':1,'sample_times_seconds':[0,.25,.5,.75,1],'motion_m_per_second':[0,.5,0],
        'options':{'fps':4,'end_time_seconds':1},'maximum_host_policy':REQUEST,
        'tolerances':{'geometry_m':1e-5,'area_m2':1e-4,'volume_m3':1e-4,'normal':1e-5,'position_m':.001,'rotation_rad':.001,'material':1e-6},
        'ordering_equivalence':[['multiple-hole-elbow','reordered-sections-rings-vertices']],
        'geometry_equivalence':[['cyclic-rigid-rotation','sign-equivalent-rotation'],['identity-solid','maximum-palette']],
        'required_geometry_checks':['authored original XY cap domain and directed boundary','actual transformed source vertex identities',
          'exact single-round coordinates and q dot q denominator','nonplanar endpoint cap triangles',
          'prescribed strip diagonals','only intended shared-simplex 3D contacts','closed opposite directed incidence',
          'outward cap and side normals','actual area and positive signed volume','actual materials and recorded carrier motion']}
    (HERE/'expected.json').write_text(json.dumps(expected,indent=2,allow_nan=False)+'\n')
    files={p.name:{'bytes':len(p.read_bytes()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
           for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='acceptance-freeze.json'}
    freeze={'schema_version':'ontokin.framed-polygon-loft-freeze/0.1','decision':'OK-LANG-011/0.1.0',
        'decision_commit':DECISION_COMMIT,
        'decision_file':'docs/language-design/framed-polygon-loft-v0.1/ADOPTION.md',
        'decision_sha256':DECISION_SHA256,
        'source_baseline_commit':'cac8b9f81a39ff8a9343caf6e8881bdc67e3ea93',
        'frozen_before_implementation':True,'case_count':len(cases),
        'outcome_counts':dict(Counter(c['expected_outcome'] for c in cases)),
        'source_count':sum(p.endswith('.ok') for p in files),'files':files}
    (HERE/'acceptance-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
    print(json.dumps({k:freeze[k] for k in ['case_count','outcome_counts','source_count']}))


if __name__=='__main__':main()
