"""Bounded GLB decoding for the independent static tray reader.

No third-party library, producer module, external resource, or native process is
used. Buffer data and transforms are measured; accessor min/max is not evidence.
"""

import hashlib
import json
import math
import os
from pathlib import Path
import stat
import struct


MAX_GLB = 8 * 1024 * 1024
MAX_RESULT = 4 * 1024 * 1024


class InvalidGLB(ValueError):
    def __init__(self, message, classification="STRUCTURE"):
        self.classification = classification
        super().__init__(message)


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise InvalidGLB("Duplicate JSON member: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise InvalidGLB("Nonfinite JSON value " + value)


def strict_json(data, limit=MAX_RESULT):
    if len(data) > limit:
        raise InvalidGLB("JSON byte limit exceeded", "RESOURCE")
    try:
        if data.startswith(b"\xef\xbb\xbf"):
            raise InvalidGLB("JSON BOM is forbidden")
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InvalidGLB("Invalid JSON: " + str(exc)) from exc
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > 32:
            raise InvalidGLB("JSON nesting limit exceeded", "RESOURCE")
        if isinstance(item, dict):
            stack.extend((v,depth+1) for v in item.values())
        elif isinstance(item, list):
            stack.extend((v,depth+1) for v in item)
        elif isinstance(item, float) and not math.isfinite(item):
            raise InvalidGLB("Nonfinite decoded JSON scalar")
    return value


def integer(value, name, low=0, high=MAX_GLB):
    if type(value) is not int or not low <= value <= high:
        raise InvalidGLB("Invalid integer " + name)
    return value


def finite(value):
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise InvalidGLB("Expected finite JSON number")
    return value


def read_bytes(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise InvalidGLB("Artifact must be a regular non-symlink file")
    with p.open("rb") as stream:
        data = stream.read(MAX_GLB+1)
    if len(data) > MAX_GLB:
        raise InvalidGLB("GLB exceeds 8 MiB", "RESOURCE")
    return data


def read_json_file(path):
    """Bound auxiliary fixture/baseline bytes before decoding their JSON."""
    try:
        fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,"rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise InvalidGLB("JSON input must be a regular nonsymlink file","BINDING")
            data=stream.read(MAX_RESULT+1)
    except OSError as exc:
        raise InvalidGLB("JSON input cannot be opened as a regular nonsymlink file","BINDING") from exc
    return strict_json(data)


def parse(data):
    if len(data) > MAX_GLB or len(data) < 28:
        raise InvalidGLB("Invalid GLB byte length")
    magic, version, total = struct.unpack_from("<III", data)
    if magic != 0x46546c67 or version != 2 or total != len(data):
        raise InvalidGLB("Invalid GLB header/version/total length")
    offset, chunks = 12, []
    while offset < len(data):
        if offset + 8 > len(data):
            raise InvalidGLB("Truncated chunk header")
        length, kind = struct.unpack_from("<II", data, offset)
        if length % 4 or offset + 8 + length > len(data):
            raise InvalidGLB("Invalid GLB chunk bounds or alignment")
        chunks.append((kind, data[offset+8:offset+8+length]))
        offset += 8+length
    if len(chunks) != 2 or [k for k,_ in chunks] != [0x4e4f534a,0x004e4942]:
        raise InvalidGLB("Exactly JSON then BIN chunks required")
    doc = strict_json(chunks[0][1])
    if not isinstance(doc, dict):
        raise InvalidGLB("GLB JSON root must be an object")
    if not isinstance(doc.get("asset"), dict) or doc["asset"].get("version") != "2.0":
        raise InvalidGLB("glTF asset version 2.0 required")
    buffers = doc.get("buffers")
    if not isinstance(buffers,list) or len(buffers) != 1 or not isinstance(buffers[0],dict):
        raise InvalidGLB("Exactly one embedded binary buffer required")
    if set(buffers[0]) - {"byteLength", "name"}:
        raise InvalidGLB("External or extended binary buffer forbidden", "UNSUPPORTED")
    length = integer(buffers[0].get("byteLength"), "buffer.byteLength", 1)
    binary = chunks[1][1]
    if not length <= len(binary) <= length+3 or any(binary[length:]):
        raise InvalidGLB("Binary buffer length or padding mismatch")
    for name, maximum in (("bufferViews",128),("accessors",128),("nodes",64),
                          ("meshes",64),("materials",16),("scenes",8)):
        value = doc.get(name)
        if not isinstance(value,list) or len(value)>maximum:
            raise InvalidGLB("Missing or unbounded " + name)
    return doc, binary[:length]


def pack(doc, binary, sort_keys=True):
    data = json.dumps(doc, ensure_ascii=True, sort_keys=sort_keys,
                      separators=(",", ":"), allow_nan=False).encode()
    data += b" " * ((-len(data)) % 4)
    padded = bytes(binary) + b"\0" * ((-len(binary)) % 4)
    total = 12+8+len(data)+8+len(padded)
    if total>MAX_GLB:
        raise InvalidGLB("Packed GLB exceeds 8 MiB", "RESOURCE")
    return (struct.pack("<III",0x46546c67,2,total) +
            struct.pack("<II",len(data),0x4e4f534a)+data +
            struct.pack("<II",len(padded),0x004e4942)+padded)


def accessor(doc, binary, index, purpose):
    index = integer(index, "accessor index", 0, len(doc["accessors"])-1)
    a = doc["accessors"][index]
    if not isinstance(a,dict):
        raise InvalidGLB("Accessor must be an object")
    if "sparse" in a or "extensions" in a:
        raise InvalidGLB("Sparse/compressed accessor forbidden", "UNSUPPORTED")
    if set(a) - {"bufferView","byteOffset","componentType","count","type","min","max","name"}:
        raise InvalidGLB("Unsupported accessor field", "UNSUPPORTED")
    typ = a.get("componentType")
    if purpose in ("POSITION","NORMAL"):
        if typ != 5126 or a.get("type") != "VEC3":
            raise InvalidGLB("POSITION and NORMAL must be float32 VEC3")
        width, fmt, components = 4, "f", 3
        count = integer(a.get("count"), purpose+" count",1,256)
    elif purpose == "indices":
        if a.get("type") != "SCALAR" or typ not in (5121,5123,5125):
            raise InvalidGLB("Triangle index accessor must be unsigned SCALAR")
        width, fmt = {5121:(1,"B"),5123:(2,"H"),5125:(4,"I")}[typ]
        components = 1
        count = integer(a.get("count"), "index count", 1,768)
    else:
        raise InvalidGLB("Unsupported accessor purpose", "UNSUPPORTED")
    vi = integer(a.get("bufferView"),"bufferView index",0,len(doc["bufferViews"])-1)
    view = doc["bufferViews"][vi]
    if not isinstance(view,dict):
        raise InvalidGLB("Buffer view must be an object")
    if set(view)-{"buffer","byteOffset","byteLength","byteStride","target","name"}:
        raise InvalidGLB("Extended bufferView forbidden", "UNSUPPORTED")
    if view.get("buffer") != 0:
        raise InvalidGLB("Accessor is not in the embedded buffer")
    if "target" in view and view["target"] not in (34962,34963):
        raise InvalidGLB("Invalid buffer view target")
    vo = integer(view.get("byteOffset",0), "view offset")
    vl = integer(view.get("byteLength"), "view length",1)
    ao = integer(a.get("byteOffset",0), "accessor offset")
    item = width*components
    stride = view.get("byteStride",item)
    integer(stride,"accessor stride",item,252)
    if "byteStride" in view and (stride%4 or stride<4 or purpose=="indices"):
        raise InvalidGLB("Invalid explicit accessor stride")
    if ao%width or (vo+ao)%width or vo+vl>len(binary):
        raise InvalidGLB("Accessor alignment or view bounds invalid")
    if ao+(count-1)*stride+item>vl:
        raise InvalidGLB("Accessor exceeds bufferView")
    values, offsets = [], []
    for row in range(count):
        off = vo+ao+row*stride
        value = struct.unpack_from("<"+fmt*components,binary,off)
        if purpose in ("POSITION","NORMAL") and not all(math.isfinite(v) for v in value):
            raise InvalidGLB("Nonfinite mesh value")
        values.append(value if components>1 else value[0])
        offsets.append(off)
    return values, {"accessor":index,"view":vi,"offsets":offsets,"width":width,
                    "components":components,"format":fmt,"stride":stride}


def verify_lock(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise InvalidGLB("Input lock must be a regular non-symlink file", "BINDING")
    with p.open("rb") as stream:
        raw = stream.read(MAX_RESULT+1)
    lock = strict_json(raw)
    section = lock.get("independent_reader")
    if not isinstance(section,dict) or not isinstance(section.get("files"),dict):
        raise InvalidGLB("Lock lacks independent_reader.files", "BINDING")
    expected = {"audit.py","reader.py","glb.py","expected.py","corrupt.py"}
    if set(section["files"]) != expected:
        raise InvalidGLB("Lock must bind the complete five-file independent reader closure", "BINDING")
    base = Path(__file__).resolve().parent
    for name,digest in section["files"].items():
        file = base/name
        if file.is_symlink() or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=digest:
            raise InvalidGLB("Independent reader lock mismatch: " + name,"BINDING")
    return lock, hashlib.sha256(raw).hexdigest()


def write_result(path, result):
    data = json.dumps(result, sort_keys=True, indent=2, allow_nan=False).encode()+b"\n"
    if len(data)>MAX_RESULT:
        raise InvalidGLB("Structured result exceeds 4 MiB", "RESOURCE")
    target = Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("xb") as stream:
        stream.write(data)
