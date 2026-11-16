"""Hand-derived C253 controls, independent from the C255 implementation."""
import itertools
import math

TIMES=(0.,.25,.5,.75,1.,1.5,2.)
MOUNTS={'first':{'lower':-.6,'middle':0.,'upper':.6},
        'second':{'bottom':-1.2,'lower':-.6,'middle':0.,'top':1.2,'upper':.6}}
SELECTED='first.fingers["middle"].blade'


def rows(length):
    result=[]
    for root,mounts in MOUNTS.items():
        ident=['keyed-rack','demo',root]
        result.append({'path':root,'id':ident,'definition':['entry','keyed-rack','definitions','rack'],
                       'owner':None,'kind':'box','size':[.1,.6*len(mounts),.1]})
        for key,y in mounts.items():
            finger=f'{root}.fingers["{key}"]'; fid=ident+['fingers',key]
            L=length if root=='first' and key=='middle' else .6
            result.append({'path':finger,'id':fid,'definition':['package','example.hinges','hinges','definitions','finger'],
                           'owner':root,'kind':'sphere','radius':.06,'length':L,'y':y})
            result.append({'path':finger+'.blade','id':fid+['blade'],'definition':['package','example.hinges','hinges','definitions','blade'],
                           'owner':finger,'kind':'box','size':[L,.08,.08],'y':y})
    return result


def pose(row,time,length):
    first=row['path']=='first' or row['path'].startswith('first.')
    center=[-1. if first else 1.,(.2*time if first else 0.)+row.get('y',0.),0.]
    angle=0.
    if row['path']==SELECTED:
        angle=math.pi/4*min(time,1.)
        center[0]+=length/2*math.cos(angle)
        center[1]+=length/2*math.sin(angle)
    elif row['path'].endswith('.blade'):
        center[0]+=.3
    wxyz=[math.cos(angle/2),0.,0.,math.sin(angle/2)]
    c,s=math.cos(angle),math.sin(angle)
    matrix=[[c,-s,0.,center[0]], [s,c,0.,center[1]], [0.,0.,1.,0.], [0.,0.,0.,1.]]
    return {'position':center,'quaternion':wxyz,'matrix':matrix,'angle':angle}


def box_vertices(size):
    return [[sx*size[0]/2,sy*size[1]/2,sz*size[2]/2]
            for sx,sy,sz in itertools.product((-1.,1.),repeat=3)]


def sphere_mesh(radius=.06):
    # Distinct poles and fifteen 32-point rings, independent from exporter code
    points=[[0.,radius,0.]]
    for latitude in range(1,16):
        a=math.pi*latitude/16
        for longitude in range(32):
            b=2*math.pi*longitude/32
            points.append([radius*math.sin(a)*math.cos(b),radius*math.cos(a),radius*math.sin(a)*math.sin(b)])
    points.append([0.,-radius,0.])
    faces=[]
    for lon in range(32):
        a=1+lon; b=1+(lon+1)%32
        faces.append([0,b,a])
    for lat in range(14):
        for lon in range(32):
            a=1+32*lat+lon; b=1+32*lat+(lon+1)%32
            c=a+32; d=b+32
            faces.extend([[a,b,c],[b,d,c]])
    for lon in range(32):
        a=1+32*14+lon; b=1+32*14+(lon+1)%32
        faces.append([a,b,len(points)-1])
    assert len(points)==482 and len(faces)==960
    return points,faces


def program_revision(entry_bytes,library_bytes):
    """Implement the construction contract's manifest formula, no runtime use."""
    import hashlib,json
    manifest={'schema_version':'ontokin.bundle/0.1','entry_source_id':'entry','units':[
        {'source_id':'entry','package_id':None,'version':None,'filename':'main.ok',
         'source_revision':'sha256:'+hashlib.sha256(entry_bytes).hexdigest()},
        {'source_id':'package:example.hinges@1.0.0','package_id':'example.hinges','version':'1.0.0','filename':'hinges.ok',
         'source_revision':'sha256:'+hashlib.sha256(library_bytes).hexdigest()}]}
    canonical=json.dumps(manifest,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    return 'sha256:'+hashlib.sha256(b'ontokin.bundle/0.1\0'+canonical).hexdigest()


def box_mesh(size):
    points=box_vertices(size)
    quads=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
    faces=[]
    for a,b,c,d in quads:faces.extend([[a,b,c],[a,c,d]])
    return points,faces
