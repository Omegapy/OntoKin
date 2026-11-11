"""Independent measured-geometry audit for the finite C198 tray contract."""

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
import math
from pathlib import Path

from expected import (DELTA, FRAME_DELTA, MATERIALS, PARTS, SIDES, expected_case,
                      geometry, mat_vec, metadata, root_name, transpose)
from glb import InvalidGLB, accessor, finite, integer, parse, read_bytes, read_json_file


IDENTITY = tuple(tuple(Fraction(int(i==j)) for j in range(4)) for i in range(4))
PINNED_GENERATOR = "Khronos glTF Blender I/O v4.5.48"
SYNTHETIC_GENERATOR = "Independent synthetic reader control"
NONSEMANTIC_METADATA = {
    "asset_generator":PINNED_GENERATOR,"scene_name":"StaticTray",
    "buffer_name_fields":"forbidden","buffer_view_name_fields":"forbidden",
    "accessor_name_fields":"forbidden",
}


def validate_delivery_rules(rules):
    """Validate the complete frozen layout declaration, without producer imports.

    None is permitted only by the synthetic/measurement API. A supplied profile
    must contain every known declaration; unknown or weakened rules fail closed.
    Buffer repeatability and raw/final byte equality require transaction evidence.
    """
    if rules is None:
        return
    mesh_names=[root_name(side)+"/"+part+"/mesh" for side in SIDES for part in PARTS]
    node_names=[]
    for side in SIDES:
        node_names.extend([root_name(side)+"/"+part for part in PARTS]+[root_name(side)])
    fixed={
        "schema":"ontokin.static-tray.delivery-rules/0.1.0",
        "node_order":node_names,"mesh_order":mesh_names,"scene_nodes":[6,13],
        "material_order":["tray","payload"],"nodes":14,"meshes":12,
        "primitives_per_mesh":1,"primitive_attributes":["NORMAL","POSITION"],
        "position_component_type":5126,"position_type":"VEC3",
        "normal_component_type":5126,"normal_type":"VEC3",
        "index_component_type":5123,"index_type":"SCALAR",
        "vertices_per_mesh":24,"triangles_per_mesh":12,
        "metallic":0.0,"roughness":0.75,"alpha_mode":"OPAQUE","double_sided":False,
        "buffer_storage":"Pinned exporter deterministic uncompressed internal storage; shared identical buffers allowed and resolved by reader",
        "raw_to_final":"Exact byte copy; no projection, metadata stripping, quantization or volatile exclusions",
        "nonsemantic_metadata":NONSEMANTIC_METADATA,
    }
    if type(rules) is not dict or set(rules)!=set(fixed):
        raise InvalidGLB("Delivery rules must contain exactly the complete known declaration set","LAYOUT")
    for key,wanted in fixed.items():
        value=rules[key]
        numeric=type(wanted) is float
        valid_type=type(value) in (int,float) if numeric else type(value) is type(wanted)
        if type(wanted) is list and valid_type and len(value)==len(wanted):
            valid_type=all(type(actual) is type(expected) for actual,expected in zip(value,wanted))
        if not valid_type or value!=wanted:
            raise InvalidGLB("Delivery rule differs from the frozen finite profile: "+key,"LAYOUT")


def check_delivery_layout(doc,rules,findings):
    if rules is None:
        return
    def equal(name,label,actual,wanted):
        if actual!=wanted:
            findings.add(name,"LAYOUT",label+" differs from the frozen delivery rule")
    equal("","Node count",len(doc["nodes"]),rules["nodes"])
    equal("","Mesh count",len(doc["meshes"]),rules["meshes"])
    equal("","Node order",[n.get("name") for n in doc["nodes"]],rules["node_order"])
    equal("","Mesh order",[m.get("name") for m in doc["meshes"]],rules["mesh_order"])
    equal("","Scene node indices",doc["scenes"][0]["nodes"],rules["scene_nodes"])
    equal("","Material order",[m.get("name") for m in doc["materials"]],rules["material_order"])
    metadata=rules["nonsemantic_metadata"]
    equal("","Asset generator",doc["asset"].get("generator"),metadata["asset_generator"])
    equal("","Scene name",doc["scenes"][0].get("name"),metadata["scene_name"])
    for mesh in doc["meshes"]:
        name=mesh.get("name")
        name=name.removesuffix("/mesh") if type(name) is str else ""
        equal(name,"Primitive count",len(mesh["primitives"]),rules["primitives_per_mesh"])
        for primitive in mesh["primitives"]:
            equal(name,"Primitive attributes",sorted(primitive["attributes"]),rules["primitive_attributes"])
            for kind,key,count in (("POSITION","position",rules["vertices_per_mesh"]),
                                   ("NORMAL","normal",rules["vertices_per_mesh"]),
                                   ("indices","index",3*rules["triangles_per_mesh"])):
                index=primitive["indices"] if kind=="indices" else primitive["attributes"][kind]
                index=integer(index,"layout accessor index",0,len(doc["accessors"])-1)
                info=doc["accessors"][index]
                equal(name,kind+" component type",info["componentType"],rules[key+"_component_type"])
                equal(name,kind+" accessor type",info["type"],rules[key+"_type"])
                equal(name,kind+" accessor count",info["count"],count)
    # Fixed PBR values are separately measured for every primitive by material().
    # validate_delivery_rules forbids declarations that would weaken those rules.


def check_nonsemantic_metadata(doc,findings):
    """No free-text field may carry source, route or whole-record provenance.

    The historical synthetic marker is admitted only to measurement-only API
    controls. Full delivery rules additionally require the pinned native values.
    Structurally readable metadata errors do not suppress geometry measurement.
    """
    if "generator" in doc["asset"] and doc["asset"]["generator"] not in (PINNED_GENERATOR,SYNTHETIC_GENERATOR):
        findings.add("","UNSUPPORTED","Asset generator is outside the fixed metadata vocabulary")
    if "name" in doc["scenes"][0] and doc["scenes"][0]["name"]!="StaticTray":
        findings.add("","UNSUPPORTED","Scene name is outside the fixed metadata vocabulary")
    for collection in ("buffers","bufferViews","accessors"):
        for index,item in enumerate(doc[collection]):
            if "name" in item:
                findings.add("","UNSUPPORTED",collection+"["+str(index)+"] name metadata is forbidden")


def number(value):
    finite(value)
    return Fraction(value)


def vector(value, count):
    if not isinstance(value,list) or len(value)!=count:
        raise InvalidGLB("Invalid transform vector length")
    return tuple(map(number,value))


def matrix(node):
    if "matrix" in node:
        if set(node)&{"translation","rotation","scale"}:
            raise InvalidGLB("A node cannot contain matrix and TRS")
        flat = vector(node["matrix"],16)
        out = tuple(tuple(flat[c*4+r] for c in range(4)) for r in range(4))
        if out[3] != (0,0,0,1):
            raise InvalidGLB("Nonaffine node matrix is unsupported", "FRAME")
        return out
    t = vector(node.get("translation",[0,0,0]),3)
    x,y,z,w = vector(node.get("rotation",[0,0,0,1]),4)
    scale = vector(node.get("scale",[1,1,1]),3)
    r = ((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
         (2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),
         (2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
    return tuple(tuple(r[i][j]*scale[j] for j in range(3))+(t[i],) for i in range(3)) + ((0,0,0,1),)


def multiply(a,b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)) for i in range(4))


def transform(m,p):
    p = tuple(map(Fraction,p))+(1,)
    return tuple(sum(m[i][k]*p[k] for k in range(4)) for i in range(3))


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def sub(a,b):
    return tuple(x-y for x,y in zip(a,b))


def serial(value):
    if isinstance(value,Fraction):
        value = float(value)
    if isinstance(value,float):
        return 0.0 if value==0 else value
    if isinstance(value,(list,tuple)):
        return [serial(x) for x in value]
    if isinstance(value,dict):
        return {k:serial(v) for k,v in value.items()}
    return value


def stable_bytes(value):
    return json.dumps(serial(value),sort_keys=True,separators=(",",":"),allow_nan=False).encode()


class Findings:
    def __init__(self):
        self.findings=[]
        self.measurements=[]

    def add(self,name,classification,message):
        item={"semantic_id": name.split("/") if name else [],
              "classification": classification, "code":"OTRAY-E-DELIVERY", "message":message}
        if item not in self.findings:
            self.findings.append(item)

    def measure(self,name,label,actual,wanted,tolerance=DELTA,classification="GEOMETRY",minimum=False):
        actual,wanted,tolerance = map(Fraction,(actual,wanted,tolerance))
        diff=actual-wanted
        passed = diff >= -tolerance if minimum else abs(diff)<=tolerance
        self.measurements.append({"semantic_id":name.split("/"),"name":label,
                                  "measured":float(actual),"expected":float(wanted),
                                  "difference":float(diff),"threshold":float(tolerance),
                                  "comparison":"minimum" if minimum else "absolute_difference",
                                  "classification":classification,"passed":passed})
        if not passed:
            self.add(name,classification,label+" differs from the independent expectation")
        return passed


def check_rigid(m,name,findings):
    a=[row[:3] for row in m[:3]]
    for i in range(3):
        for j in range(3):
            findings.measure(name,"rigid_row_"+str(i)+"_"+str(j),dot(a[i],a[j]),int(i==j),
                             FRAME_DELTA,"FRAME")
    findings.measure(name,"rigid_determinant",dot(a[0],cross(a[1],a[2])),1,FRAME_DELTA,"FRAME")


def check_matrix(actual,wanted,name,findings):
    check_rigid(actual,name,findings)
    for row in range(3):
        for col in range(4):
            findings.measure(name,"world_matrix_"+str(row)+"_"+str(col),actual[row][col],wanted[row][col],
                             DELTA if col==3 else FRAME_DELTA,"FRAME")


def validate_document(doc,binary):
    allowed={"asset","scene","scenes","nodes","meshes","materials","accessors","bufferViews","buffers"}
    if set(doc)-allowed:
        raise InvalidGLB("Unsupported glTF top-level field: "+",".join(sorted(set(doc)-allowed)),"UNSUPPORTED")
    if set(doc["asset"])-{"version","generator","minVersion"}:
        raise InvalidGLB("Unadmitted asset metadata", "UNSUPPORTED")
    if "minVersion" in doc["asset"] and doc["asset"]["minVersion"]!="2.0":
        raise InvalidGLB("Unsupported minimum glTF version", "UNSUPPORTED")
    if len(doc["scenes"])!=1 or doc.get("scene",0)!=0:
        raise InvalidGLB("Exactly one selected scene required","UNSUPPORTED")
    scene=doc["scenes"][0]
    if not isinstance(scene,dict) or set(scene)-{"nodes","name"} or not isinstance(scene.get("nodes"),list):
        raise InvalidGLB("Invalid or extended scene", "UNSUPPORTED")
    for node in doc["nodes"]:
        if not isinstance(node,dict):
            raise InvalidGLB("Node must be object")
        if set(node)-{"name","mesh","children","matrix","translation","rotation","scale","extras"}:
            raise InvalidGLB("Unsupported node feature", "UNSUPPORTED")
        if "rotation" in node:
            q=vector(node["rotation"],4)
            if abs(sum(x*x for x in q)-1)>FRAME_DELTA:
                raise InvalidGLB("Node rotation quaternion is not unit", "FRAME")
    for m in doc["materials"]:
        if not isinstance(m,dict):
            raise InvalidGLB("Material must be an object")
    for view in doc["bufferViews"]:
        if not isinstance(view,dict) or set(view)-{"buffer","byteOffset","byteLength","byteStride","target","name"}:
            raise InvalidGLB("Unsupported or malformed buffer view", "UNSUPPORTED")
        if view.get("buffer")!=0:
            raise InvalidGLB("Every view must reference the embedded buffer")
        start=integer(view.get("byteOffset",0),"bufferView offset")
        size=integer(view.get("byteLength"),"bufferView length",1)
        if start+size>len(binary):
            raise InvalidGLB("Buffer view exceeds actual binary data")
        if "byteStride" in view:
            stride=integer(view["byteStride"],"bufferView stride",4,252)
            if stride%4:
                raise InvalidGLB("Buffer view stride must be a multiple of four")
        if "target" in view and view["target"] not in (34962,34963):
            raise InvalidGLB("Invalid buffer view target")
    for index,a in enumerate(doc["accessors"]):
        if not isinstance(a,dict):
            raise InvalidGLB("Accessor must be an object")
        if a.get("type")=="VEC3" and a.get("componentType")==5126:
            accessor(doc,binary,index,"NORMAL")
        elif a.get("type")=="SCALAR" and a.get("componentType") in (5121,5123,5125):
            accessor(doc,binary,index,"indices")
        else:
            raise InvalidGLB("Unadmitted unused or active accessor type", "UNSUPPORTED")
        for bound in ("min","max"):
            if bound in a:
                values=a[bound]
                count=3 if a["type"]=="VEC3" else 1
                if not isinstance(values,list) or len(values)!=count:
                    raise InvalidGLB("Malformed accessor bound")
                for value in values:
                    finite(value)
    for mesh in doc["meshes"]:
        if not isinstance(mesh,dict) or set(mesh)-{"name","primitives"}:
            raise InvalidGLB("Unsupported mesh field or extras", "UNSUPPORTED")
        primitives=mesh.get("primitives")
        if not isinstance(primitives,list) or len(primitives)!=1:
            raise InvalidGLB("Exactly one finite primitive per box required", "UNSUPPORTED")
        prim=primitives[0]
        if not isinstance(prim,dict) or set(prim)-{"attributes","indices","material","mode"}:
            raise InvalidGLB("Unsupported primitive feature", "UNSUPPORTED")
        if prim.get("mode",4)!=4 or set(prim.get("attributes",{}))!={"POSITION","NORMAL"}:
            raise InvalidGLB("Only triangle POSITION/NORMAL geometry is admitted", "UNSUPPORTED")


def scene_graph(doc):
    nodes=doc["nodes"]
    parents={}
    for i,node in enumerate(nodes):
        children=node.get("children",[])
        if not isinstance(children,list) or len(children)>64:
            raise InvalidGLB("Invalid children array")
        for child in children:
            integer(child,"child index",0,len(nodes)-1)
            if child in parents:
                raise InvalidGLB("Duplicate child or multiple parents", "IDENTITY")
            parents[child]=i
    roots=doc["scenes"][0]["nodes"]
    if len(set(roots))!=len(roots):
        raise InvalidGLB("Duplicate scene root", "IDENTITY")
    for index in roots:
        integer(index,"root index",0,len(nodes)-1)
        if index in parents:
            raise InvalidGLB("Scene root has another parent", "IDENTITY")
    visiting,set_done=set(),set()
    worlds={}
    def visit(i,parent):
        if i in visiting or i in set_done:
            raise InvalidGLB("Cycle or duplicate scene occurrence", "IDENTITY")
        visiting.add(i)
        worlds[i]=multiply(parent,matrix(nodes[i]))
        for child in nodes[i].get("children",[]):
            visit(child,worlds[i])
        visiting.remove(i)
        set_done.add(i)
    for root in roots:
        visit(root,IDENTITY)
    if len(set_done)!=len(nodes):
        raise InvalidGLB("Unreachable node or graph cycle", "IDENTITY")
    return worlds,parents


def material(doc,index,name,findings):
    index=integer(index,"material index",0,len(doc["materials"])-1)
    m=doc["materials"][index]
    if not isinstance(m,dict) or set(m)-{"name","pbrMetallicRoughness","alphaMode","doubleSided"}:
        raise InvalidGLB("Unsupported material feature or extras", "UNSUPPORTED")
    pbr=m.get("pbrMetallicRoughness",{})
    if not isinstance(pbr,dict) or set(pbr)-{"baseColorFactor","metallicFactor","roughnessFactor"}:
        raise InvalidGLB("Unsupported PBR feature", "UNSUPPORTED")
    value={"baseColorFactor":pbr.get("baseColorFactor",[1,1,1,1]),
           "metallicFactor":pbr.get("metallicFactor",1),
           "roughnessFactor":pbr.get("roughnessFactor",1),
           "alphaMode":m.get("alphaMode","OPAQUE"),"doubleSided":m.get("doubleSided",False)}
    color=value["baseColorFactor"]
    if not isinstance(color,list) or len(color)!=4:
        raise InvalidGLB("Invalid PBR color")
    for v in color+[value["metallicFactor"],value["roughnessFactor"]]:
        finite(v)
    if type(value["doubleSided"]) is not bool:
        raise InvalidGLB("Invalid doubleSided material flag")
    token="payload" if name.endswith("/payload") else "tray"
    if m.get("name")!=token or value!=MATERIALS[token]:
        findings.add(name,"MATERIAL","Delivered fixed material differs from selected contract")
    return {"name":m.get("name"),**value}


def box_measurement(points,indices,normals,expected_size,offset,root,name,findings):
    """Measure actual tray-local coordinates, then test topology and expectations."""
    lo=tuple(min(p[a] for p in points) for a in range(3))
    hi=tuple(max(p[a] for p in points) for a in range(3))
    if any(a>=b for a,b in zip(lo,hi)):
        findings.add(name,"TOPOLOGY","Box has a zero or negative measured side")
        return {"min":lo,"max":hi,"topology_passed":False}
    for axis in range(3):
        findings.measure(name,"side_"+str(axis),hi[axis]-lo[axis],expected_size[axis])
        findings.measure(name,"face_min_"+str(axis),lo[axis],offset[axis]-expected_size[axis]/2)
        findings.measure(name,"face_max_"+str(axis),hi[axis],offset[axis]+expected_size[axis]/2)
    labels=list(product((0,1),repeat=3))
    corners={bits:tuple(hi[a] if bits[a] else lo[a] for a in range(3)) for bits in labels}
    buckets=defaultdict(list)
    assigned=[]
    topology_before=len([x for x in findings.findings if x["classification"]=="TOPOLOGY"])
    for point in points:
        matches=[bits for bits,corner in corners.items() if max(abs(a-b) for a,b in zip(point,corner))<=DELTA]
        if len(matches)!=1:
            findings.add(name,"TOPOLOGY","Vertex does not belong to one unique measured corner")
            assigned.append(None)
        else:
            assigned.append(matches[0])
            buckets[matches[0]].append(point)
    if set(buckets)!=set(labels):
        findings.add(name,"TOPOLOGY","All eight measured corners must be present")
    for bits,members in buckets.items():
        representative=min(members)
        if any(max(abs(a-b) for a,b in zip(p,representative))>DELTA for p in members):
            findings.add(name,"TOPOLOGY","Coincident corner split exceeds the weld allowance")
        independent=tuple(offset[a]+(expected_size[a]/2 if bits[a] else -expected_size[a]/2) for a in range(3))
        actual_world=tuple(a+b for a,b in zip(mat_vec(root["rotation"],representative),root["translation"]))
        expected_world=tuple(a+b for a,b in zip(mat_vec(root["rotation"],independent),root["translation"]))
        for axis in range(3):
            findings.measure(name,"world_corner_"+"".join(map(str,bits))+"_"+str(axis),
                             actual_world[axis],expected_world[axis],DELTA,"FRAME")
    if len(indices)!=36:
        findings.add(name,"TOPOLOGY","A closed box must have exactly twelve triangles")
    faces=defaultdict(list)
    edges=Counter()
    triangles=set()
    volume=Fraction(0)
    for start in range(0,len(indices)-2,3):
        ia,ib,ic=indices[start:start+3]
        a,b,c=points[ia],points[ib],points[ic]
        volume+=dot(a,cross(b,c))/6
        tri=(assigned[ia],assigned[ib],assigned[ic])
        if None in tri or len(set(tri))!=3:
            findings.add(name,"TOPOLOGY","Triangle repeats a corner or has an unassigned vertex")
            continue
        key=tuple(sorted(tri))
        if key in triangles:
            findings.add(name,"TOPOLOGY","Repeated geometric triangle")
        triangles.add(key)
        plane=[(axis,tri[0][axis]) for axis in range(3) if len({x[axis] for x in tri})==1]
        if len(plane)!=1:
            findings.add(name,"TOPOLOGY","Triangle is interior or does not lie on one box face")
            continue
        axis,sign=plane[0]
        faces[(axis,sign)].append(set(tri))
        direction=tuple((1 if sign else -1) if i==axis else 0 for i in range(3))
        outward=dot(cross(sub(b,a),sub(c,a)),direction)
        if outward<=0:
            findings.add(name,"TOPOLOGY","Triangle winding is not strictly outward")
        for vi in (ia,ib,ic):
            for naxis in range(3):
                findings.measure(name,"normal_"+str(vi)+"_"+str(naxis),normals[vi][naxis],
                                 direction[naxis],FRAME_DELTA,"GEOMETRY")
        for u,v in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
            edges[tuple(sorted((u,v)))]+=1
    for axis in range(3):
        for sign in (0,1):
            face=faces[(axis,sign)]
            wanted={b for b in labels if b[axis]==sign}
            if len(face)!=2 or set.union(*face)!=wanted:
                findings.add(name,"TOPOLOGY","A face is missing or lacks two complete covering triangles")
                continue
            shared=face[0]&face[1]
            if len(shared)!=2:
                findings.add(name,"TOPOLOGY","Face triangles do not share one diagonal")
            else:
                u,v=sorted(shared)
                if sum(x!=y for x,y in zip(u,v))!=2:
                    findings.add(name,"TOPOLOGY","Face shared edge is not a diagonal")
    if len(edges)!=18 or any(count!=2 for count in edges.values()):
        findings.add(name,"TOPOLOGY","Every welded edge must have exactly two incident triangles")
    if volume<=0:
        findings.add(name,"TOPOLOGY","Signed measured volume must be positive")
    expected_volume=math.prod(expected_size)
    allowance=math.prod(side+2*DELTA for side in expected_size)-expected_volume
    findings.measure(name,"signed_volume_m3",volume,expected_volume,allowance,"GEOMETRY")
    topology_after=len([x for x in findings.findings if x["classification"]=="TOPOLOGY"])
    return {"min":lo,"max":hi,"volume_m3":volume,"expected_volume_m3":expected_volume,
            "volume_allowance_m3":allowance,"topology_passed":topology_before==topology_after}


def tray_measurements(side,boxes,root,findings):
    name=root_name(side)
    if set(boxes)!=set(PARTS):
        return
    payload=boxes["payload"]
    left=payload["min"][0]-boxes["left-wall"]["max"][0]
    right=boxes["right-wall"]["min"][0]-payload["max"][0]
    back=payload["min"][2]-boxes["back"]["max"][2]
    front=boxes["front"]["min"][2]-payload["max"][2]
    floor=boxes["base"]["max"][1]
    walls=["back","front","left-wall","right-wall"]
    rim=min(boxes[p]["max"][1] for p in walls)
    for key,val in (("left",left),("right",right),("back",back),("front",front)):
        findings.measure(name,"clearance_"+key+"_m",val,root["clearance"],DELTA,"CLEARANCE")
        findings.measure(name,"minimum_clearance_"+key+"_m",val,root["clearance"],DELTA,"CLEARANCE",True)
    findings.measure(name,"cavity_width_m",boxes["right-wall"]["min"][0]-boxes["left-wall"]["max"][0],root["cavity"][0])
    findings.measure(name,"cavity_depth_m",boxes["front"]["min"][2]-boxes["back"]["max"][2],root["cavity"][2])
    findings.measure(name,"cavity_height_m",rim-floor,root["cavity"][1])
    findings.measure(name,"payload_bottom_gap_m",payload["min"][1]-floor,0,DELTA,"CLEARANCE")
    findings.measure(name,"headroom_m",rim-payload["max"][1],root["headroom"],DELTA,"CLEARANCE")
    findings.measure(name,"minimum_headroom_m",rim-payload["max"][1],root["headroom"],DELTA,"CLEARANCE",True)
    for part in walls:
        findings.measure(name,"rim_"+part+"_m",boxes[part]["max"][1],root["cavity"][1])
        findings.measure(name,"wall_floor_"+part+"_m",boxes[part]["min"][1],0)
    for a,b in combinations([k for k in PARTS if k!="payload"],2):
        lengths=tuple(min(boxes[a]["max"][i],boxes[b]["max"][i])-max(boxes[a]["min"][i],boxes[b]["min"][i]) for i in range(3))
        if all(v>DELTA for v in lengths):
            findings.add(name,"GEOMETRY","Positive material overlap between "+a+" and "+b)


def audit(artifact_path,expected="Q01",baseline_right=None,delivery_rules=None):
    """Audit actual GLB bytes against independent intent, never producer geometry.

    A complete earlier audit report or its right_closure may be baseline_right.
    Exact right preservation is mandatory for Q04/Q05 and explicit baselines.
    """
    checks=Findings()
    measured_nodes={}
    right_closure={}
    raw=b""
    case=expected if isinstance(expected,str) and expected.startswith("Q") else "independent-fixture"
    try:
        validate_delivery_rules(delivery_rules)
        if isinstance(expected,str):
            fixture=expected_case(expected) if expected in {"Q01","Q02","Q03","Q04","Q05"} else read_json_file(expected)
        else:
            fixture=expected
        expectations=geometry(fixture)
        raw=read_bytes(artifact_path)
        doc,binary=parse(raw)
        validate_document(doc,binary)
        check_nonsemantic_metadata(doc,checks)
        check_delivery_layout(doc,delivery_rules,checks)
        worlds,parents=scene_graph(doc)
        nodes=doc["nodes"]
        names=[n.get("name") for n in nodes]
        wanted_names={root_name(s) for s in SIDES}|{root_name(s)+"/"+p for s in SIDES for p in PARTS}
        if any(type(name) is not str for name in names):
            raise InvalidGLB("Every node requires an exact semantic name", "IDENTITY")
        if len(set(names))!=len(names):
            checks.add("","IDENTITY","Duplicate delivered node name")
        missing=wanted_names-set(names)
        extra=set(names)-wanted_names
        for name in sorted(missing):
            checks.add(name,"IDENTITY","Missing delivered semantic occurrence")
        for name in sorted(extra):
            checks.add(name,"UNSUPPORTED","Unexpected delivered occurrence")
        if len(nodes)!=14:
            checks.add("","IDENTITY","Exactly fourteen delivered nodes are required")
        if len(doc["meshes"])!=12:
            checks.add("","IDENTITY","Exactly twelve delivered meshes are required")
            if len(doc["meshes"])>12:
                checks.add("","UNSUPPORTED","Additional mesh is outside the finite delivery profile")
        if len(doc["materials"])!=2 or {m.get("name") for m in doc["materials"]}!={"tray","payload"}:
            checks.add("","MATERIAL","Exactly the two fixed materials are required")
        semantic_ids=[]
        for node in nodes:
            if isinstance(node.get("extras"),dict):
                semantic_ids.append(stable_bytes(node["extras"].get("semantic_id")))
        if len(set(semantic_ids))!=len(semantic_ids):
            checks.add("","IDENTITY","Duplicate delivered semantic ID")
        name_indices={n:i for i,n in enumerate(names)}
        scene_roots=[names[i] for i in doc["scenes"][0]["nodes"]]
        if scene_roots!=[root_name(s) for s in SIDES]:
            checks.add("","IDENTITY","Scene roots must be left then right with no wrapper")
        mesh_uses=Counter(n.get("mesh") for n in nodes if "mesh" in n)
        if any(count!=1 for count in mesh_uses.values()):
            checks.add("","IDENTITY","Each part must use its own unique mesh")
        boxes={side:{} for side in SIDES}
        for side in SIDES:
            root=expectations[side]
            R=root["rotation"]
            Rt=transpose(R)
            trans=root["translation"]
            rn=root_name(side)
            root_matrix=tuple(tuple(R[i])+(trans[i],) for i in range(3))+((0,0,0,1),)
            for part in (None,)+PARTS:
                name=rn if part is None else rn+"/"+part
                if name not in name_indices:
                    continue
                ni=name_indices[name]
                node=nodes[ni]
                if node.get("extras")!=metadata(side,part):
                    checks.add(name,"IDENTITY","Exact semantic/role/owner/follow metadata differs")
                node_closure={"name":name,"extras":node.get("extras"),
                              "local_matrix":matrix(node),"world_matrix":worlds[ni],
                              "children":[names[i] for i in node.get("children",[])]}
                if part is None:
                    if "mesh" in node or ni in parents:
                        checks.add(name,"IDENTITY","Tray root must be empty and a scene root")
                    if node_closure["children"]!=[rn+"/"+p for p in PARTS]:
                        checks.add(name,"IDENTITY","Root children do not match the fixed follows in canonical order")
                    check_matrix(worlds[ni],root_matrix,name,checks)
                    measured_nodes[name]=serial(node_closure)
                else:
                    if node.get("children") or parents.get(ni)!=name_indices.get(rn):
                        checks.add(name,"IDENTITY","Part is not one direct leaf of its own root")
                    if "mesh" not in node:
                        checks.add(name,"IDENTITY","Box part has no actual mesh")
                        continue
                    mi=integer(node["mesh"],"mesh index",0,len(doc["meshes"])-1)
                    mesh=doc["meshes"][mi]
                    if mesh.get("name")!=name+"/mesh":
                        checks.add(name,"IDENTITY","Mesh name does not match semantic identity")
                    prim=mesh["primitives"][0]
                    positions,_=accessor(doc,binary,prim["attributes"]["POSITION"],"POSITION")
                    normals,_=accessor(doc,binary,prim["attributes"]["NORMAL"],"NORMAL")
                    indices,_=accessor(doc,binary,prim.get("indices"),"indices")
                    if len(normals)!=len(positions) or len(indices)%3 or any(i>=len(positions) for i in indices):
                        raise InvalidGLB("Invalid triangle/normal/POSITION cardinality or index")
                    if set(indices)!=set(range(len(positions))):
                        checks.add(name,"TOPOLOGY","POSITION contains an unreferenced vertex")
                    expected_size,offset=root["boxes"][part]
                    wanted_translation=tuple(a+b for a,b in zip(mat_vec(R,offset),trans))
                    wanted_matrix=tuple(tuple(R[i])+(wanted_translation[i],) for i in range(3))+((0,0,0,1),)
                    check_matrix(worlds[ni],wanted_matrix,name,checks)
                    actual_world=[transform(worlds[ni],p) for p in positions]
                    tray_points=[mat_vec(Rt,sub(p,trans)) for p in actual_world]
                    actual_normal_matrix=tuple(row[:3] for row in worlds[ni][:3])
                    tray_normals=[mat_vec(Rt,mat_vec(actual_normal_matrix,tuple(map(Fraction,n)))) for n in normals]
                    measured=box_measurement(tray_points,indices,tray_normals,expected_size,offset,root,name,checks)
                    boxes[side][part]=measured
                    fixed_material=material(doc,prim.get("material"),name,checks)
                    node_closure.update(mesh_name=mesh.get("name"), positions=positions,normals=normals,
                                        indices=indices, material=fixed_material)
                    measured_nodes[name]=serial({**node_closure,"world_vertices":actual_world,
                                                  "tray_vertices":tray_points,"bounds":measured})
                if side=="right":
                    right_closure[name]=serial(node_closure)
            tray_measurements(side,boxes[side],root,checks)
        if baseline_right is not None:
            if isinstance(baseline_right,(str,Path)):
                baseline_right=read_json_file(baseline_right)
            if "right_closure" in baseline_right:
                baseline_right=baseline_right["right_closure"]
            if stable_bytes(right_closure)!=stable_bytes(baseline_right):
                checks.add(root_name("right"),"SIBLING","Complete decoded right sibling closure differs from its retained baseline")
        elif case in {"Q04","Q05"}:
            checks.add(root_name("right"),"SIBLING","Retained right baseline is required for scoped edit and reuse acceptance")
    except (InvalidGLB,ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError,OSError) as exc:
        checks.add("",getattr(exc,"classification","STRUCTURE"),str(exc))
    checks.findings.sort(key=lambda x:(x["semantic_id"],x["classification"],x["message"]))
    checks.measurements.sort(key=lambda x:(x["semantic_id"],x["name"]))
    return {"schema":"ontokin.static-tray.independent-audit/0.1.0", "case":case,
            "passed":not checks.findings,"artifact_sha256":hashlib.sha256(raw).hexdigest() if raw else None,
            "artifact_bytes":len(raw),"findings":checks.findings,"measurements":checks.measurements,
            "nodes":measured_nodes,"right_closure":right_closure,
            "right_closure_sha256":hashlib.sha256(stable_bytes(right_closure)).hexdigest(),
            "scope":"Decoded finite static geometry and identity only; native receiving and qualification are separate"}
