"""Independent D01-D08 mutations of retained GLB copies.

This writer never changes accepted source, the supplied artifact, or a producer
expectation. It records exact before/after identities and changed byte ranges.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import signal
import struct
import sys

# -B prevents writes, but an existing cache would escape the five source hashes.
_directory=Path(__file__).resolve().parent
if any(p.name=="__pycache__" or p.suffix in {".pyc",".pyo"} for p in _directory.iterdir()):
    raise ImportError("Unbound independent reader bytecode cache is forbidden")
sys.path.insert(0,str(_directory))
from glb import InvalidGLB, accessor, pack, parse, read_bytes, verify_lock, write_result


def append_accessor(doc,binary,values,purpose,component_type=5126):
    formats={5126:("f",4),5121:("B",1),5123:("H",2),5125:("I",4)}
    fmt,width=formats[component_type]
    count=3 if purpose=="POSITION" else 1
    binary.extend(b"\0"*((-len(binary))%4))
    offset=len(binary)
    for value in values:
        elements=value if count==3 else (value,)
        binary.extend(struct.pack("<"+fmt*count,*elements))
    vi=len(doc["bufferViews"])
    doc["bufferViews"].append({"buffer":0,"byteOffset":offset,
                               "byteLength":len(binary)-offset,
                               "target":34962 if purpose=="POSITION" else 34963})
    a={"bufferView":vi,"componentType":component_type,"count":len(values),
       "type":"VEC3" if count==3 else "SCALAR"}
    if count==3:
        rounded=[struct.unpack("<fff",struct.pack("<fff",*v)) for v in values]
        a["min"]=[min(v[i] for v in rounded) for i in range(3)]
        a["max"]=[max(v[i] for v in rounded) for i in range(3)]
    doc["accessors"].append(a)
    doc["buffers"][0]["byteLength"]=len(binary)
    return len(doc["accessors"])-1


def node_index(doc,name):
    indices=[i for i,n in enumerate(doc["nodes"]) if n.get("name")==name]
    if len(indices)!=1:
        raise InvalidGLB("Corruption requires exactly one node named "+name)
    return indices[0]


def exclusive_primitive(doc,ni):
    node=doc["nodes"][ni]
    mi=node.get("mesh")
    if not isinstance(mi,int) or mi<0 or mi>=len(doc["meshes"]):
        raise InvalidGLB("Corruption target needs one actual mesh")
    if sum(n.get("mesh")==mi for n in doc["nodes"])>1:
        doc["meshes"].append(deepcopy(doc["meshes"][mi]))
        node["mesh"]=len(doc["meshes"])-1
        mi=node["mesh"]
    primitives=doc["meshes"][mi].get("primitives",[])
    if len(primitives)!=1:
        raise InvalidGLB("Corruption requires one mesh primitive")
    return primitives[0]


def changed_ranges(before,after):
    result=[]
    start=None
    for i in range(min(len(before),len(after))):
        different=before[i]!=after[i]
        if different and start is None:
            start=i
        elif not different and start is not None:
            result.append({"start":start,"end_exclusive":i})
            start=None
    common=min(len(before),len(after))
    if len(before)!=len(after):
        if start is None:
            start=common
        result.append({"start":start,"end_exclusive":max(len(before),len(after))})
    elif start is not None:
        result.append({"start":start,"end_exclusive":common})
    return result


def reverse_keys(value):
    if isinstance(value,dict):
        return {k:reverse_keys(value[k]) for k in reversed(list(value))}
    if isinstance(value,list):
        return [reverse_keys(v) for v in value]
    return value


def corrupt(case,artifact,output,variant="copy"):
    before=read_bytes(artifact)
    doc,raw_binary=parse(before)
    binary=bytearray(raw_binary)
    note=""
    if case=="D01":
        ni=node_index(doc,"equipment-tray/pair/left/payload")
        prim=exclusive_primitive(doc,ni)
        positions,_=accessor(doc,binary,prim["attributes"]["POSITION"],"POSITION")
        center=(min(v[0] for v in positions)+max(v[0] for v in positions))/2
        changed=[(v[0]+(0.002 if v[0]>center else -0.002),v[1],v[2]) for v in positions]
        prim["attributes"]["POSITION"]=append_accessor(doc,binary,changed,"POSITION")
        note="Forked left payload POSITION accessor; full X extent increased by 0.004 m"
    elif case=="D02":
        ni=node_index(doc,"equipment-tray/pair/right/base")
        mi=doc["nodes"][ni].get("mesh")
        del doc["nodes"][ni]
        for node in doc["nodes"]:
            if "children" in node:
                node["children"]=[x-int(x>ni) for x in node["children"] if x!=ni]
        for scene in doc["scenes"]:
            scene["nodes"]=[x-int(x>ni) for x in scene["nodes"] if x!=ni]
        if not any(n.get("mesh")==mi for n in doc["nodes"]):
            del doc["meshes"][mi]
            for node in doc["nodes"]:
                if "mesh" in node and node["mesh"]>mi:
                    node["mesh"]-=1
        note="Removed actual right/base node and its unreferenced mesh; retained other binary data"
    elif case=="D03":
        node=doc["nodes"][node_index(doc,"equipment-tray/pair/right/front")]
        if "matrix" in node:
            node["matrix"][14]+=0.002
        else:
            node.setdefault("translation",[0,0,0])[2]+=0.002
        note="Moved right/front by +0.002 m along its parent tray local Z"
    elif case=="D04":
        ni=node_index(doc,"equipment-tray/pair/left/base")
        prim=exclusive_primitive(doc,ni)
        indices,_=accessor(doc,binary,prim["indices"],"indices")
        if len(indices)<6:
            raise InvalidGLB("Missing original box face indices")
        prim["indices"]=append_accessor(doc,binary,indices[:-6],"indices",5125)
        note="Removed two actual triangle faces from left/base while retaining all original POSITION bounds"
    elif case=="D05":
        node=doc["nodes"][node_index(doc,"equipment-tray/pair/left")]
        if "matrix" in node:
            for i in range(4):
                node["matrix"][i]*=-1
        else:
            scale=node.setdefault("scale",[1,1,1])
            scale[0]*=-1
        note="Introduced root X reflection with unchanged mesh coordinates"
    elif case=="D06":
        node=doc["nodes"][node_index(doc,"equipment-tray/pair/left/payload")]
        node["extras"]["semantic_id"][-1]="unbound-payload"
        note="Changed actual delivered semantic ID while retaining all geometry"
    elif case=="D07":
        doc["nodes"].append({"name":"unadmitted-extra-node"})
        doc["scenes"][0]["nodes"].append(len(doc["nodes"])-1)
        note="Inserted one additional structurally valid empty scene node"
    elif case=="D08":
        if variant not in ("copy","reordered"):
            raise ValueError("D08 variant must be copy or reordered")
        note="Exact retained copy" if variant=="copy" else "Reversed JSON object keys without changing values"
    else:
        raise ValueError("Unknown delivered corruption control")
    if case=="D08" and variant=="copy":
        after=before
    else:
        if case=="D08":
            doc=reverse_keys(doc)
        after=pack(doc,binary,sort_keys=case!="D08")
    out=Path(output)
    if out.resolve()==Path(artifact).resolve() or out.exists() or out.is_symlink():
        raise ValueError("Corruption output must be a new path distinct from accepted input")
    if any(p.is_symlink() for p in out.parents):
        raise ValueError("Corruption output ancestors may not be symlinks")
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("xb") as stream:
        stream.write(after)
    if read_bytes(artifact)!=before:
        raise ValueError("Original retained artifact changed during corruption")
    return {"schema":"ontokin.static-tray.delivered-corruption/0.1.0","case":case,"variant":variant,
            "description":note,"input_sha256":hashlib.sha256(before).hexdigest(),
            "output_sha256":hashlib.sha256(after).hexdigest(),"input_bytes":len(before),
            "output_bytes":len(after),"changed_ranges":changed_ranges(before,after),
            "input_preserved":True,"native_starts":0}


def deadline(_signum,_frame):
    raise TimeoutError("Independent corruption writer exceeded 30,000 ms")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",required=True,choices=["D%02d"%i for i in range(1,9)])
    parser.add_argument("--artifact",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--lock",required=True)
    parser.add_argument("--result")
    parser.add_argument("--variant",choices=["copy","reordered"],default="copy")
    args=parser.parse_args(argv)
    signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,30)
    try:
        _,lock_hash=verify_lock(args.lock)
        result=corrupt(args.case,args.artifact,args.output,args.variant)
        result["input_lock_sha256"]=lock_hash
        write_result(args.result or args.output+".corruption.json",result)
        print(json.dumps({"case":args.case,"output_sha256":result["output_sha256"]},sort_keys=True))
        return 0
    except (InvalidGLB,ValueError,TimeoutError,OSError) as exc:
        print(json.dumps({"passed":False,"error":str(exc)},sort_keys=True),file=sys.stderr)
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)


if __name__=="__main__":
    raise SystemExit(main())
