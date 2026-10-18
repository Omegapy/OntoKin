"""Standalone glTF 2.0 prototype for authored loft meshes.

This is *not* ontokin.glb/0.3 and is not wired to OntoKin .ok programs.
It proves that the experimental mesh can produce real per-region GLB
primitives with PBR materials while the 0.4.0 package/evidence stay frozen.
"""

from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass

from .mesh import LoftMesh, SurfaceError

MAX_BYTES = 64 * 1024 * 1024
MAX_LOCAL_FLOAT32_ERROR_M = 1e-5


@dataclass(frozen=True)
class GLBPrototype:
    data: bytes
    max_vertex_error_m: float
    primitives: int
    triangles: int


def _bad(message: str, *, code: str = "OKL-E-SURFACE-NUMERIC") -> None:
    raise SurfaceError(code, message)


def export_loft_prototype(mesh: LoftMesh, *, name: str = "surface-prototype") -> GLBPrototype:
    """Pack a validated, single rigid mesh with separate actual PBR primitives."""
    if not isinstance(mesh, LoftMesh):
        _bad("Expected a validated LoftMesh.")
    if not isinstance(name, str) or not 1 <= len(name) <= 128:
        _bad("A bounded node name is required.")
    total_vertices = len(mesh.positions)
    if not total_vertices or len(mesh.normals) != total_vertices:
        _bad("Position/normal arrays are empty or mismatched.")
    if total_vertices > 250_000 or mesh.triangle_count * 3 != total_vertices:
        _bad("The mesh exceeds its vertex budget or contains mismatched triangles.",
             code="OKL-E-RESOURCE")
    payload = bytearray()
    views = []
    accessors = []
    max_error = 0.0

    def align() -> None:
        payload.extend(b"\0" * (-len(payload) % 4))

    def add_float3(values, *, position: bool) -> int:
        nonlocal max_error
        align()
        start = len(payload)
        mins = [math.inf, math.inf, math.inf]
        maxs = [-math.inf, -math.inf, -math.inf]
        for row in values:
            if len(row) != 3 or not all(math.isfinite(c) for c in row):
                _bad("Non-finite or malformed XYZ value.")
            packed = struct.pack("<fff", *row)
            quantized = struct.unpack("<fff", packed)
            if position:
                max_error = max(max_error, *(abs(a-b) for a,b in zip(row,quantized)))
            for i, value in enumerate(quantized):
                mins[i] = min(mins[i], value)
                maxs[i] = max(maxs[i], value)
            payload.extend(packed)
        if len(payload) > MAX_BYTES:
            _bad("Binary GLB exceeds the byte budget.", code="OKL-E-RESOURCE")
        views.append({"buffer":0,"byteOffset":start,"byteLength":len(payload)-start,
                      "target":34962})
        accession = {"bufferView":len(views)-1, "componentType":5126,
                     "count":len(values), "type":"VEC3"}
        if position:
            accession["min"] = mins
            accession["max"] = maxs
        accessors.append(accession)
        return len(accessors)-1

    position = add_float3(mesh.positions, position=True)
    normal = add_float3(mesh.normals, position=False)
    if max_error > MAX_LOCAL_FLOAT32_ERROR_M:
        _bad("Local position quantization exceeds 1e-5 meters.")

    materials = []
    primitives = []
    covered = set()
    component = 5123 if total_vertices < 65536 else 5125
    format_ = "<H" if component == 5123 else "<I"
    for group in mesh.regions:
        if not group.indices or len(group.indices)%3 != 0:
            _bad("Every emitted material group must contain complete triangles.")
        if any(type(i) is not int or i < 0 or i >= total_vertices for i in group.indices):
            _bad("Material group contains an invalid vertex index.")
        if any(i in covered for i in group.indices):
            _bad("A generated triangle corner belongs to more than one region.")
        covered.update(group.indices)
        align()
        start = len(payload)
        for index in group.indices:
            payload.extend(struct.pack(format_, index))
        if len(payload) > MAX_BYTES:
            _bad("Binary GLB exceeds the byte budget.", code="OKL-E-RESOURCE")
        views.append({"buffer":0,"byteOffset":start,"byteLength":len(payload)-start,
                      "target":34963})
        accessors.append({"bufferView":len(views)-1,"componentType":component,
                          "count":len(group.indices),"type":"SCALAR",
                          "min":[min(group.indices)], "max":[max(group.indices)]})
        material_id = len(materials)
        mat = group.material
        material = {
            "name":"OntoKin prototype region: "+group.key,
            "pbrMetallicRoughness":{
                "baseColorFactor":list(mat.rgba),
                "metallicFactor":mat.metallic,
                "roughnessFactor":mat.roughness
            },
            "doubleSided":False
        }
        if mat.rgba[3] < 1.0:
            material["alphaMode"]="BLEND"
        materials.append(material)
        primitives.append({
            "attributes":{"POSITION":position,"NORMAL":normal},
            "indices":len(accessors)-1,"material":material_id,"mode":4,
            "extras":{"ontokin":{"region_key":group.key}}
        })
    if len(covered) != total_vertices:
        _bad("Every generated triangle corner must be assigned to one region.")
    payload.extend(b"\0" * (-len(payload)%4))
    gltf = {
        "asset":{"version":"2.0","generator":"OntoKin surface research prototype"},
        "scene":0,"scenes":[{"nodes":[0]}],
        "nodes":[{"name":name,"mesh":0}],
        "meshes":[{"name":name,"primitives":primitives}],
        "materials":materials,
        "buffers":[{"byteLength":len(payload)}],
        "bufferViews":views,"accessors":accessors,
        "extras":{"ontokin":{
            "prototype_only":True,
            "not_ontokin_glb_0_3":True,
            "surface_section_keys":list(mesh.section_keys),
            "facets":mesh.facets,"caps":mesh.caps,
            "note":"Geometry-only prototype, not linked to an authored .ok revision."
        }}
    }
    document = json.dumps(gltf, separators=(",",":"), allow_nan=False, ensure_ascii=False).encode("utf-8")
    document += b" " * (-len(document)%4)
    total = 12 + 8 + len(document) + 8 + len(payload)
    if total > MAX_BYTES:
        _bad("Complete GLB exceeds 64 MiB.", code="OKL-E-RESOURCE")
    data = (struct.pack("<III", 0x46546c67, 2, total)
            + struct.pack("<II", len(document), 0x4e4f534a) + document
            + struct.pack("<II", len(payload), 0x004e4942) + payload)
    return GLBPrototype(data=data, max_vertex_error_m=max_error,
                        primitives=len(primitives), triangles=mesh.triangle_count)
