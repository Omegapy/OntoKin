"""Independent decoded-GLB checks against frozen analytic extrusion facts.

This module imports no OntoKin runtime. It measures supplied triangle bytes;
it does not call or reproduce the production triangulator.
"""
from __future__ import annotations
from collections import Counter
import json
import math
import struct


def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def close(a,b,tolerance=1e-5):
    assert len(a)==len(b)
    assert all(math.isfinite(x) and abs(x-y)<=tolerance for x,y in zip(a,b)),(a,b,tolerance)


class Decoded:
    def __init__(self,data):
        assert len(data)>=28 and struct.unpack_from('<III',data)==(0x46546c67,2,len(data))
        length,kind=struct.unpack_from('<II',data,12)
        assert kind==0x4e4f534a
        self.document=json.loads(data[20:20+length])
        start=20+length
        size,kind=struct.unpack_from('<II',data,start)
        assert kind==0x004e4942 and start+8+size==len(data)
        self.binary=data[start+8:]
        assert self.document['buffers'][0].get('uri') is None
        meta=self.document['extras']['ontokin']
        assert meta['target_contract']=='ontokin.glb/0.8' and meta['profile']=='polygon-extrusion-0.1'
        assert meta['schema_version']=='0.8'

    def accessor(self,index):
        a=self.document['accessors'][index];v=self.document['bufferViews'][a['bufferView']]
        assert 'sparse' not in a and not a.get('normalized',False)
        fmt,width={5123:('H',2),5125:('I',4),5126:('f',4)}[a['componentType']]
        count={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
        start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width*count)
        assert start+(a['count']-1)*stride+width*count<=len(self.binary)
        rows=[struct.unpack_from('<'+fmt*count,self.binary,start+i*stride) for i in range(a['count'])]
        return [r[0] for r in rows] if count==1 else rows

    def objects(self):
        nodes={n['extras']['ontokin']['path']:i for i,n in enumerate(self.document['nodes']) if n.get('extras',{}).get('ontokin',{}).get('kind')=='object'}
        assert len(nodes)==len(self.document['nodes'])
        return nodes

    def triangles(self,path):
        node=self.document['nodes'][self.objects()[path]]
        if 'mesh' not in node:return []
        records=[]
        for p in self.document['meshes'][node['mesh']]['primitives']:
            assert p.get('mode',4)==4
            pos=self.accessor(p['attributes']['POSITION']);normal=self.accessor(p['attributes']['NORMAL'])
            indices=self.accessor(p['indices']);mat=self.document['materials'][p['material']]
            key=mat['extras']['ontokin']['source_region_key']
            for i in range(0,len(indices),3):
                ids=indices[i:i+3]
                records.append((key,[pos[j] for j in ids],[normal[j] for j in ids],mat))
        return records

    def pose(self,path,time):
        i=self.objects()[path];node=self.document['nodes'][i]
        value={'translation':node.get('translation',[0,0,0]),'rotation':node.get('rotation',[0,0,0,1])}
        assert 'children' not in node and 'matrix' not in node
        for channel in self.document['animations'][0]['channels']:
            if channel['target']['node']!=i:continue
            sampler=self.document['animations'][0]['samplers'][channel['sampler']]
            times=self.accessor(sampler['input']);rows=self.accessor(sampler['output'])
            assert sampler.get('interpolation','LINEAR')=='LINEAR'
            k=next((k for k,t in enumerate(times) if t>=time),len(times)-1)
            if times[k]==time or k==0:r=rows[k]
            else:
                t=(time-times[k-1])/(times[k]-times[k-1]);r=[a+(b-a)*t for a,b in zip(rows[k-1],rows[k])]
            value[channel['target']['path']]=r
        return value


def check_geometry(decoded,path,wanted):
    triangles=decoded.triangles(path)
    assert len(triangles)==wanted['triangle_count'],(path,len(triangles),wanted['triangle_count'])
    offset=wanted.get('local_position_m',[0,0,0]);q=wanted.get('local_orientation_wxyz',[1,0,0,0])
    # The frozen placement control is a half-turn around X, independently known
    assert q in ([1,0,0,0],[0,1,0,0])
    def unplace(p):
        p=sub(p,offset)
        return p if q[0]==1 else (p[0],-p[1],-p[2])
    edges=Counter();counts=Counter();area=volume=0.;all_points=[]
    corner_set=[(x,y,z) for x,y in wanted['points_xy_m'] for z in [0,wanted['depth_m']]]
    for region,placed,normals,material in triangles:
        counts[region]+=1;p=[unplace(v) for v in placed];all_points.extend(p)
        for point in p:
            assert min(math.dist(point,v) for v in corner_set)<=1e-5,(path,point,'not an authored corner')
        face=cross(sub(placed[1],placed[0]),sub(placed[2],placed[0]));magnitude=math.hypot(*face)
        assert magnitude>0
        for normal in normals:
            assert abs(math.hypot(*normal)-1)<=1e-5 and dot(face,normal)>0
            close(normal,[x/magnitude for x in face],1e-5)
        area+=magnitude/2
        volume+=dot(p[0],cross(p[1],p[2]))/6
        local_face=cross(sub(p[1],p[0]),sub(p[2],p[0]))
        if region=='bottom':
            assert all(abs(v[2])<=1e-5 for v in p) and local_face[2]<0
        elif region=='top':
            assert all(abs(v[2]-wanted['depth_m'])<=1e-5 for v in p) and local_face[2]>0
        else:
            assert region=='side' and len({round(v[2],7) for v in p})==2
            outline=wanted['points_xy_m'];ids={min(range(len(outline)),key=lambda i:math.dist(v[:2],outline[i])) for v in p}
            assert len(ids)==2 and any(ids=={i,(i+1)%len(outline)} for i in range(len(outline))), 'A side must follow one authored outline edge'
        pbr=material['pbrMetallicRoughness'];close(pbr['baseColorFactor'],wanted['palette'][region],1e-6)
        close([pbr['metallicFactor'],pbr['roughnessFactor']],[wanted['metallic'],wanted['roughness']],1e-6)
        for a,b in zip(placed,placed[1:]+placed[:1]):edges[(tuple(a),tuple(b))]+=1
    assert dict(counts)==wanted['region_triangle_counts']
    assert all(n==1 and edges[(b,a)]==1 for (a,b),n in edges.items()),'Geometric mesh must be closed with opposite edge orientation'
    assert abs(area-wanted['surface_area_m2'])<=1e-4,(area,wanted['surface_area_m2'])
    assert abs(volume-wanted['volume_m3'])<=1e-4,(volume,wanted['volume_m3'])
    bounds=[[min(p[i] for p in all_points) for i in range(3)],[max(p[i] for p in all_points) for i in range(3)]]
    for a,b in zip(bounds,wanted['bounds_m']):close(a,b)
    return {'path':path,'triangles':len(triangles),'regions':dict(counts),'surface_area_m2':area,'signed_volume_m3':volume,'oriented_edges':len(edges),'bounds_m':bounds,'status':'passed'}
