"""C210 review-only GLB decoding without OntoKin's reader or exporter."""
import hashlib
import json
import math
import struct
from pathlib import Path

WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
FORMAT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def sha(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()

def decode(source):
    data = source if isinstance(source, bytes) else Path(source).read_bytes()
    if len(data) < 20 or struct.unpack_from("<III", data) != (0x46546C67, 2, len(data)):
        raise AssertionError("Invalid GLB header")
    offset, chunks = 12, []
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        payload = data[offset:offset+length]
        if len(payload) != length or length % 4:
            raise AssertionError("Invalid GLB chunk extent/alignment")
        chunks.append((kind, payload))
        offset += length
    if offset != len(data) or [kind for kind, _ in chunks] != [0x4E4F534A, 0x004E4942]:
        raise AssertionError("Unexpected GLB chunks")
    document = json.loads(chunks[0][1])
    binary = chunks[1][1]
    if len(document["buffers"]) != 1 or document["buffers"][0].get("uri") is not None:
        raise AssertionError("Expected one embedded binary buffer")
    if not document["buffers"][0]["byteLength"] <= len(binary) <= document["buffers"][0]["byteLength"]+3:
        raise AssertionError("Buffer length mismatch")
    return data, document, binary

def accessor(document, binary, index):
    item = document["accessors"][index]
    if "sparse" in item or item.get("normalized", False):
        raise AssertionError("Review finite profile excludes sparse/normalized accessors")
    view = document["bufferViews"][item["bufferView"]]
    if view["buffer"] != 0:
        raise AssertionError("Nonembedded buffer")
    width, fmt = WIDTH[item["type"]], FORMAT[item["componentType"]]
    record = struct.Struct("<" + fmt*width)
    start = view.get("byteOffset", 0) + item.get("byteOffset", 0)
    stride = view.get("byteStride", record.size)
    stop = start + (item["count"]-1)*stride + record.size
    if item["count"] < 1 or stride < record.size or stop > view.get("byteOffset", 0)+view["byteLength"] or stop > len(binary):
        raise AssertionError("Accessor extent is invalid")
    raw = b"".join(binary[start+i*stride:start+i*stride+record.size] for i in range(item["count"]))
    values = [record.unpack_from(raw, i*record.size) for i in range(item["count"])]
    if not all(math.isfinite(x) for row in values for x in row):
        raise AssertionError("Nonfinite accessor value")
    return {"component_type":item["componentType"], "type":item["type"], "count":item["count"], "raw_sha256":sha(raw), "values":values}

def objects(document):
    found = {}
    for index, node in enumerate(document["nodes"]):
        metadata = node.get("extras", {}).get("ontokin", {})
        if metadata.get("kind") != "object":
            continue
        identity = tuple(metadata["element_id"])
        if identity in found:
            raise AssertionError("Duplicate semantic identity")
        found[identity] = (index, node, metadata)
    return found

def geometry(document, binary, node):
    if "mesh" not in node:
        return {"geometry_sha256":sha(b"no-visible-geometry"),"primitives":[]}
    output = []
    for primitive in document["meshes"][node["mesh"]]["primitives"]:
        attributes = {name:accessor(document,binary,index) for name,index in sorted(primitive["attributes"].items())}
        indices = accessor(document,binary,primitive["indices"])
        positions = attributes["POSITION"]["values"]
        normals = attributes["NORMAL"]["values"]
        if indices["type"] != "SCALAR" or indices["count"]%3 or not all(0<=row[0]<len(positions) for row in indices["values"]):
            raise AssertionError("Invalid triangle indices")
        if len(normals) != len(positions):
            raise AssertionError("Normal count differs from positions")
        signature = {"mode":primitive.get("mode",4), "attributes":{name:{k:v for k,v in item.items() if k!="values"} for name,item in attributes.items()}, "indices":{k:v for k,v in indices.items() if k!="values"}}
        output.append({"signature":signature, "position_bounds":[[min(p[a] for p in positions),max(p[a] for p in positions)] for a in range(3)],"material":document["materials"][primitive["material"]],"vertex_count":len(positions),"triangle_count":len(indices["values"])//3})
    return {"geometry_sha256":sha(canonical([item["signature"] for item in output])), "primitives":output}

def animation(document, binary, node_index):
    output=[]
    for clip in document.get("animations",[]):
        for channel in clip["channels"]:
            if channel["target"]["node"] != node_index:
                continue
            sampler=clip["samplers"][channel["sampler"]]
            read=lambda key:{k:v for k,v in accessor(document,binary,sampler[key]).items() if k!="values"}
            output.append({"path":channel["target"]["path"],"interpolation":sampler.get("interpolation","LINEAR"),"input":read("input"),"output":read("output")})
    return sha(canonical(sorted(output,key=lambda item:item["path"])))

