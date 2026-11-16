#!/usr/bin/env python3
"""C255 finite, offline record checker; never an artifact reader or trial runner."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
from types import MappingProxyType

SCHEMA = "ontokin.c255.observation/0.1"
AUTHORITY_SCHEMA = "ontokin.c255.inert-authority/0.1"
TIMES = (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
DIMENSION_TOLERANCE = 1e-12
DELIVERY_POSITION = 0.001
REFERENCE_POSITION = 1e-9
DELIVERY_ANGLE = 0.001
REFERENCE_ANGLE = 1e-9
DELIVERY_TIME = 1e-6
SOURCE_PINS = {
    "docs/language-design/OK-LANG-001-core-language-specification.md": "d19d117cf26a281fc0fd2fa06b07c1075aa1d346ad4c8f13d12ec8e1de98fced",
    "docs/engineering/localized-repair-c253/corpus.json": "2d65c6b5f31457f99372d3cd02bbbf79c5922c03d776cfd8cd5605fac6d156b5",
    "docs/engineering/localized-repair-c253/SCORING.md": "74027574a09a06418c81ce2c49379e0a943e8f1eb164959511b2f37cc6e63730",
    "docs/engineering/localized-repair-c253/PROTOCOL.md": "8666b90b0dd6662704baa7c32e0f2ccda6f203ba6ebe0bcf997925bd6eca85fd",
    "docs/engineering/localized-repair-c253/RUN-PLAN.json": "f0338df8f33d4a9c58aa9b41d03c22260f22a0820b3e17ac834e65059d74d86b",
    "docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md": "137bb3e93dfc26d280808b56045e36da3a94e5d0393a5f14c7b34e236cb2214b",
}
CASE_KEYS = {"V1": ("start_065", "target_075"), "V2": ("target_075", "start_065"),
             "N1": ("start_065", "invalid_mass")}
PROGRAMS = {"start_065": "sha256:8f9d976568e2a9fa39573e3fb90f616529097241a098b21d4eb22eabe4b7032f",
            "target_075": "sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082"}
MOUNTS = {"first": (("lower", -0.6), ("middle", 0.0), ("upper", 0.6)),
          "second": (("bottom", -1.2), ("lower", -0.6), ("middle", 0.0), ("top", 1.2), ("upper", 0.6))}
IDENTITY = [1.0, 0.0, 0.0, 0.0]
UNITS = {"length": "m", "time": "s", "angle": "rad", "mass": "kg"}
FRAME = {"handedness": "right", "up": "+Y", "basis": "world", "quaternionOrder": "WXYZ"}


class Fault(ValueError):
    """A concrete failed record predicate, not an execution result."""
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


def require(value, code, detail):
    if not value:
        raise Fault(code, detail)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON_DUPLICATE", str(key))
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(Fault("NONFINITE", value)))


def keys(value, required, where):
    require(type(value) is dict and set(value) == set(required), "SHAPE", where)


def numeric(value, where):
    require(type(value) in (int, float), "NUMBER", where)
    require(math.isfinite(value), "NONFINITE", where)
    return value


def vector(value, count, where):
    require(type(value) is list and len(value) == count, "SHAPE", where)
    return [numeric(item, where) for item in value]


def text(value, where):
    require(type(value) is str and 0 < len(value) <= 4096, "TEXT", where)
    return value


def identifier(value):
    require(type(value) is list and 3 <= len(value) <= 8, "IDENTITY", "full occurrence key")
    require(all(type(x) is str and x for x in value), "IDENTITY", "key segments")
    return tuple(value)


def exact(actual, expected, where):
    """Structural equality with finite numeric types; Python's True == 1 is forbidden."""
    if type(expected) is dict:
        keys(actual, expected, where)
        for k in expected:
            exact(actual[k], expected[k], where + "/" + k)
    elif type(expected) is list:
        require(type(actual) is list and len(actual) == len(expected), "SEMANTIC", where)
        for i, (a, e) in enumerate(zip(actual, expected)):
            exact(a, e, f"{where}/{i}")
    elif type(expected) in (int, float):
        require(numeric(actual, where) == expected, "SEMANTIC", where)
    else:
        require(type(actual) is type(expected) and actual == expected, "SEMANTIC", where)


def close(actual, expected, tolerance, where):
    require(abs(numeric(actual, where) - expected) <= tolerance, "TOLERANCE", where)


def indexed(rows, where):
    require(type(rows) is list, "SHAPE", where)
    result = {}
    for row in rows:
        require(type(row) is dict and "id" in row, "SHAPE", where)
        key = identifier(row["id"])
        require(key not in result, "DUPLICATE_IDENTITY", where)
        result[key] = row
    return result


def id_for(rack, key=None, blade=False):
    value = ["keyed-rack", "demo", rack]
    if key is not None:
        value.extend(["fingers", key])
    if blade:
        value.append("blade")
    return value


def quantity(value, unit):
    return {"value": value, "unit": unit}


def object_record(rack, key=None, blade=False, length=0.75):
    oid = id_for(rack, key, blade)
    if key is None:
        path = rack
        definition = ["entry", "keyed-rack", "definitions", "rack"]
        primitive = {"kind": "box", "size_m": [0.1, 1.8 if rack == "first" else 3.0, 0.1]}
        params = {"finger_length": quantity(0.6, "m"),
                  "mounts": {k: {"value": [0.0, y, 0.0], "unit": "m"} for k, y in MOUNTS[rack]}}
        placement = {"kind": "declared", "frame": "world", "position_m": [-1.0 if rack == "first" else 1.0, 0.0, 0.0], "rotation_wxyz": IDENTITY[:]}
        owner, appearance = None, [0.45, 0.45, 0.5, 1.0]
    else:
        path = f'{rack}.fingers["{key}"]' + (".blade" if blade else "")
        definition = ["package", "example.hinges", "hinges", "definitions", "blade" if blade else "finger"]
        selected_length = length if (rack, key) == ("first", "middle") else 0.6
        primitive = {"kind": "box", "size_m": [selected_length, 0.08, 0.08]} if blade else {"kind": "sphere", "radius_m": 0.06}
        params = {"length": quantity(selected_length, "m"), "tint": [0.2, 0.6, 0.9, 1.0]}
        if not blade:
            params.update({"parent_frame": {"object": id_for(rack)},
                           "mount_offset": {"value": [0.0, dict(MOUNTS[rack])[key], 0.0], "unit": "m"}})
        owner, appearance = id_for(rack, key) if blade else id_for(rack), [0.2, 0.6, 0.9, 1.0]
        placement = {"kind": "undeclared"}
    return {"id": oid, "path": path, "definitionId": definition, "owner": owner,
            "parameters": params, "primitive": primitive, "appearance": appearance,
            "placement": placement, "matter": {"kind": "no_body", "own_mass_kg": 0, "aggregate_mass_kg": 0},
            "initialLinearVelocity_mps": [0, 0, 0], "initialAngularVelocity_radps": [0, 0, 0]}


def semantic_state(length):
    """Derive this one bound source family from its literal keys and equations."""
    objects, sites, follows, hinges = [], [], [], []
    for rack, mounts in MOUNTS.items():
        objects.append(object_record(rack, length=length))
        for key, y in mounts:
            finger, blade = id_for(rack, key), id_for(rack, key, True)
            selected_length = length if (rack, key) == ("first", "middle") else 0.6
            objects.extend([object_record(rack, key, length=length), object_record(rack, key, True, length)])
            sites.extend([
                {"id": finger + ["pivot"], "owner": finger, "frame": finger, "position_m": [0, 0, 0], "rotation_wxyz": IDENTITY[:], "interface": "hinged.part", "size_m": 0, "kind": "authored"},
                {"id": blade + ["base"], "owner": blade, "frame": blade, "position_m": [-selected_length / 2, 0, 0], "rotation_wxyz": IDENTITY[:], "interface": "hinged.part", "size_m": 0, "kind": "authored"},
            ])
            follows.append({"id": finger + ["mounting"], "parentFrame": id_for(rack), "child": finger,
                            "offsetPosition_m": [0, y, 0], "offsetRotation_wxyz": IDENTITY[:]})
            hinges.append({"id": finger + ["flex"], "kind": "hinge", "parentSite": finger + ["pivot"],
                           "childSite": blade + ["base"], "axis": [0, 0, 1], "axisFrame": finger + ["pivot"],
                           "limits_rad": [-math.pi / 4, math.pi / 4], "initial_rad": 0})
    for obj in objects:
        sites.append({"id": obj["id"] + ["@system", "origin"], "owner": obj["id"], "frame": obj["id"],
                      "position_m": [0, 0, 0], "rotation_wxyz": IDENTITY[:], "interface": "rigid.origin", "size_m": 0, "kind": "system"})
    return {"units": dict(UNITS), "frame": dict(FRAME),
            "scene": {"id": ["keyed-rack", "demo"], "duration_s": 2, "gravity_mps2": [0, 0, 0], "gravityFrame": "world"},
            "objects": objects, "sites": sites, "follows": follows, "hinges": hinges,
            "actions": [
                {"id": ["keyed-rack", "demo", "flex"], "kind": "tween", "joint": id_for("first", "middle") + ["flex"], "targetAngle": quantity(45, "deg"), "duration_s": 1},
                {"id": ["keyed-rack", "demo", "travel"], "kind": "move", "object": id_for("first"), "velocity_mps": [0, 0.2, 0], "frame": "world", "duration_s": 2},
            ],
            "events": [{"time_s": 0, "mode": "sequence", "operations": [{"operation": "start", "action": ["keyed-rack", "demo", "flex"]}, {"operation": "start", "action": ["keyed-rack", "demo", "travel"]}]}]}


def pose_for(oid, seconds, length):
    rack = oid[2]
    x = -1.0 if rack == "first" else 1.0
    y = 0.2 * seconds if rack == "first" else 0.0
    rotation = IDENTITY[:]
    if len(oid) > 3:
        y += dict(MOUNTS[rack])[oid[4]]
        if len(oid) == 6:
            if rack == "first" and oid[4] == "middle":
                theta = (math.pi / 4) * min(seconds, 1.0)
                x += length * math.cos(theta) / 2
                y += length * math.sin(theta) / 2
                rotation = [math.cos(theta / 2), 0.0, 0.0, math.sin(theta / 2)]
            else:
                x += 0.3
    return {"id": list(oid), "time_s": seconds, "side": "after", "position_m": [x, y, 0.0], "rotation_wxyz": rotation, "scale": [1, 1, 1]}


def matrix_for(position, rotation):
    """Row-major affine matrix from an already checked unit WXYZ quaternion."""
    w, x, y, z = rotation
    return [1 - 2 * (y*y + z*z), 2 * (x*y-z*w), 2 * (x*z+y*w), position[0],
            2 * (x*y+z*w), 1-2 * (x*x+z*z), 2 * (y*z-x*w), position[1],
            2 * (x*z-y*w), 2 * (y*z+x*w), 1-2 * (x*x+y*y), position[2],
            0, 0, 0, 1]


@dataclass(frozen=True)
class Corpus:
    sources: object
    bindings: object
    corpus_sha256: str


def load_corpus(repo):
    repo = Path(repo).resolve()
    for relative, expected in SOURCE_PINS.items():
        path = repo / relative
        require(path.resolve().is_relative_to(repo) and path.is_file() and not path.is_symlink(), "CORPUS_PATH", relative)
        require(digest(path.read_bytes()) == expected, "CORPUS_AUTHORITY", relative)
    manifest = read_json(repo / "docs/engineering/localized-repair-c253/corpus.json")
    raw, bindings = {}, {}
    for name, row in manifest["files"].items():
        path = repo / row["path"]
        require(path.resolve().is_relative_to(repo) and path.is_file() and not path.is_symlink(), "CORPUS_PATH", name)
        value = path.read_bytes()
        require(len(value) == row["bytes"] and digest(value) == row["sha256"], "CORPUS_SOURCE", name)
        raw[name], bindings[name] = value, (row["bytes"], row["sha256"])
    require(len(raw) == 14, "CORPUS_SOURCE", "14 frozen files")
    # Independently confirm that the only changed source bytes are the one literal.
    for case, (start, target) in CASE_KEYS.items():
        replacement = {"V1": b"0.75[m]", "V2": b"0.65[m]", "N1": b"0.75[kg]"}[case]
        require(raw[start][:1044] + replacement + raw[start][1051:] == raw[target], "SOURCE_LOCALITY", case)
    corpus = Corpus(MappingProxyType(raw), MappingProxyType(bindings), SOURCE_PINS["docs/engineering/localized-repair-c253/corpus.json"])
    corroborate_original(corpus)
    return corpus


def expected_state(corpus, case_id, phase="final"):
    require(isinstance(corpus, Corpus), "CORPUS", "load the frozen corpus")
    require(case_id in CASE_KEYS and phase in ("start", "final"), "CASE", "case/phase")
    start, target = CASE_KEYS[case_id]
    key = start if phase == "start" or case_id == "N1" else target
    length = 0.65 if key == "start_065" else 0.75
    semantic = semantic_state(length)
    poses = [pose_for(obj["id"], time, length) for time in TIMES for obj in semantic["objects"]]
    return {"caseId": case_id, "phase": phase, "length_m": length, "semantic": semantic, "poses": poses}


def corroborate_original(corpus):
    """Historical expectations cross-check independent answers; they never supply them."""
    old = json.loads(corpus.sources["independent_original_oracle"], object_pairs_hook=unique)
    independent = semantic_state(0.75)
    by_path = {x["path"]: x for x in independent["objects"]}
    require(set(by_path) == {x["path"] for x in old["objects"]}, "CORROBORATION", "original identities")
    for row in old["objects"]:
        own = by_path[row["path"]]
        exact(own["id"], row["element_id"], "historical id")
        exact(own["definitionId"], row["definition_id"], "historical definition")
        exact(own["primitive"], row["geometry"], "historical geometry")
        expected_owner = None if own["owner"] is None else next(o["path"] for o in independent["objects"] if o["id"] == own["owner"])
        exact(expected_owner, row["owner"], "historical owner")
    for sample in old["samples"]:
        seconds = float(sample["seconds"])
        require(seconds in TIMES and sample["side"] == "after", "CORROBORATION", "original times")
        for row in sample["objects"]:
            own = pose_for(by_path[row["path"]]["id"], seconds, 0.75)
            for a, e in zip(own["position_m"], row["position_m"]):
                close(a, e, REFERENCE_POSITION, "historical position")
            require(quaternion_angle(own["rotation_wxyz"], row["rotation_wxyz"]) <= REFERENCE_ANGLE, "CORROBORATION", "historical angle")


def semantic_check(actual, expected):
    keys(actual, expected, "semantic")
    for field in ("units", "frame", "scene", "events"):
        exact(actual[field], expected[field], field)
    for collection in ("objects", "sites", "follows", "hinges", "actions"):
        got, wanted = indexed(actual[collection], collection), indexed(expected[collection], collection)
        require(set(got) == set(wanted), "IDENTITY_SET", collection)
        for oid, target in wanted.items():
            row = got[oid]
            keys(row, target, collection + "/record")
            if collection == "objects":
                for field in target:
                    if field not in ("primitive", "parameters"):
                        exact(row[field], target[field], collection + "/" + field)
                keys(row["primitive"], target["primitive"], "primitive")
                exact(row["primitive"]["kind"], target["primitive"]["kind"], "primitive/kind")
                if target["primitive"]["kind"] == "sphere":
                    close(row["primitive"]["radius_m"], target["primitive"]["radius_m"], DIMENSION_TOLERANCE, "source/radius")
                else:
                    for a, e in zip(vector(row["primitive"]["size_m"], 3, "source/size"), target["primitive"]["size_m"]):
                        close(a, e, DIMENSION_TOLERANCE, "source/size")
                keys(row["parameters"], target["parameters"], "parameters")
                for field, value in target["parameters"].items():
                    if field in ("length", "finger_length"):
                        keys(row["parameters"][field], value, "length parameter")
                        exact(row["parameters"][field]["unit"], "m", "length/unit")
                        close(row["parameters"][field]["value"], value["value"], DIMENSION_TOLERANCE, "length/value")
                    else:
                        exact(row["parameters"][field], value, "parameters/" + field)
            elif collection == "sites" and oid == tuple(id_for("first", "middle", True) + ["base"]):
                for field in target:
                    if field != "position_m":
                        exact(row[field], target[field], "site/" + field)
                v = vector(row["position_m"], 3, "base site")
                close(v[0], target["position_m"][0], DIMENSION_TOLERANCE, "base site x")
                exact(v[1:], target["position_m"][1:], "base site yz")
            else:
                exact(row, target, collection)


def quaternion_angle(a, b):
    # A quaternion chord remains well conditioned at the 1e-9 rad boundary.
    na, nb = math.hypot(*a), math.hypot(*b)
    qa, qb = [x / na for x in a], [x / nb for x in b]
    sign = -1 if math.fsum(x*y for x, y in zip(qa, qb)) < 0 else 1
    chord = math.hypot(*(x-sign*y for x, y in zip(qa, qb)))
    return 4 * math.asin(min(1.0, chord / 2))


def raw_rotation_quaternion(matrix):
    """Polar factor only after bounded raw rigidity checks; never an admission repair.

    Newton's 3x3 polar iteration removes already-admitted representation residual
    before measuring orientation. In particular, a tiny uniform scale must not
    bias a trace-based angle and buy an extra angular tolerance.
    """
    a = [[matrix[4*i+j] for j in range(3)] for i in range(3)]
    for _ in range(4):
        cofactors = [[
            a[(i+1)%3][(j+1)%3]*a[(i+2)%3][(j+2)%3]
            - a[(i+1)%3][(j+2)%3]*a[(i+2)%3][(j+1)%3]
            for j in range(3)] for i in range(3)]
        determinant = math.fsum(a[0][j]*cofactors[0][j] for j in range(3))
        require(determinant > 0, "RAW_REFLECTION", "proper bounded polar factor")
        a = [[(a[i][j]+cofactors[i][j]/determinant)/2 for j in range(3)] for i in range(3)]
    trace = math.fsum(a[i][i] for i in range(3))
    if trace > 0:
        scale = 2*math.sqrt(1+trace)
        q = [scale/4, (a[2][1]-a[1][2])/scale, (a[0][2]-a[2][0])/scale,
             (a[1][0]-a[0][1])/scale]
    else:
        i = max(range(3), key=lambda k: a[k][k])
        j, k = (i+1)%3, (i+2)%3
        scale = 2*math.sqrt(1+a[i][i]-a[j][j]-a[k][k])
        q = [(a[k][j]-a[j][k])/scale, 0.0, 0.0, 0.0]
        q[i+1], q[j+1], q[k+1] = scale/4, (a[i][j]+a[j][i])/scale, (a[i][k]+a[k][i])/scale
    return q


def check_origin(origin, artifacts, program):
    keys(origin, ("artifact", "sha256", "location", "programRevision"), "origin")
    name = text(origin["artifact"], "artifact name")
    require(name in artifacts and origin["sha256"] == digest(artifacts[name]), "ARTIFACT_BINDING", name)
    location = text(origin["location"], "concrete artifact record location")
    require(bool(location.strip()) and not any(ord(c) < 32 or ord(c) == 127 for c in location),
            "ARTIFACT_LOCATION", "nonblank reference without control characters")
    exact(origin["programRevision"], program, "origin/programRevision")


def pose_check(rows, expected, layer, artifacts, program):
    require(layer in ("reference", "delivery"), "LAYER", "reference or delivery")
    require(type(rows) is list and len(rows) == 126, "POSE_COVERAGE", "126 required rows")
    position_tolerance = REFERENCE_POSITION if layer == "reference" else DELIVERY_POSITION
    angle_tolerance = REFERENCE_ANGLE if layer == "reference" else DELIVERY_ANGLE
    time_tolerance = 0 if layer == "reference" else DELIVERY_TIME
    structural_tolerance = 1e-12 if layer == "reference" else 1e-6
    targets = {(tuple(x["id"]), x["time_s"]): x for x in expected}
    seen = set()
    for row in rows:
        keys(row, ("id", "time_s", "side", "position_m", "rotation_wxyz", "scale", "matrix", "origin"), "pose")
        oid, time = identifier(row["id"]), numeric(row["time_s"], "pose time")
        slots = [t for t in TIMES if abs(time-t) <= time_tolerance]
        require(len(slots) == 1, "POSE_TIME", "original time/tolerance")
        pair = (oid, slots[0])
        require(pair in targets and pair not in seen, "POSE_IDENTITY", "missing/extra/duplicate slot")
        seen.add(pair)
        target = targets[pair]
        exact(row["side"], "after", "pose/side")
        exact(row["scale"], [1, 1, 1], "pose/scale")
        position = vector(row["position_m"], 3, "position")
        for a, e in zip(position, target["position_m"]):
            close(a, e, position_tolerance, "pose position")
        rotation = vector(row["rotation_wxyz"], 4, "quaternion")
        norm = math.hypot(*rotation)
        require(norm > 0 and abs(norm-1) <= structural_tolerance, "QUATERNION_NORM", "raw unit quaternion")
        require(quaternion_angle(rotation, target["rotation_wxyz"]) <= angle_tolerance, "POSE_ROTATION", "inclusive original angle")
        matrix = vector(row["matrix"], 16, "raw matrix")
        exact(matrix[12:], [0, 0, 0, 1], "raw affine last row")
        columns = [[matrix[c+4*r] for r in range(3)] for c in range(3)]
        for column in columns:
            require(abs(math.hypot(*column)-1) <= structural_tolerance, "RAW_SCALE", "unit column")
        for i, j in ((0, 1), (0, 2), (1, 2)):
            require(abs(math.fsum(a*b for a, b in zip(columns[i], columns[j]))) <= structural_tolerance, "RAW_SHEAR", "orthogonal columns")
        a, b, c = columns
        determinant = a[0]*(b[1]*c[2]-b[2]*c[1])-b[0]*(a[1]*c[2]-a[2]*c[1])+c[0]*(a[1]*b[2]-a[2]*b[1])
        require(determinant > 0, "RAW_REFLECTION", "proper orientation")
        unit = [x/norm for x in rotation]
        represented = matrix_for(position, unit)
        for i, (actual, wanted) in enumerate(zip(matrix, represented)):
            close(actual, wanted, structural_tolerance, f"raw/decomposed {i}")
        # Check raw translation independently, so decomposition does not buy a second tolerance.
        for i, wanted in zip((3, 7, 11), target["position_m"]):
            close(matrix[i], wanted, position_tolerance, "raw position")
        # The raw orientation independently meets the original angular limit;
        # the polar factor prevents tolerated encoding residue biasing the angle.
        raw_rotation = raw_rotation_quaternion(matrix)
        require(quaternion_angle(raw_rotation, target["rotation_wxyz"]) <= angle_tolerance,
                "RAW_ROTATION", "original angle independently")
        check_origin(row["origin"], artifacts, program)
    require(seen == set(targets), "POSE_COVERAGE", "all identities at all times")


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def geometry_check(rows, semantic, artifacts, program):
    got, wanted = indexed(rows, "geometry"), indexed(semantic["objects"], "objects")
    require(set(got) == set(wanted), "GEOMETRY_COVERAGE", "all 18 geometries")
    for oid, target in wanted.items():
        row = got[oid]
        keys(row, ("id", "vertices_m", "triangles", "origin"), "mesh")
        vertices = row["vertices_m"]
        require(type(vertices) is list and 8 <= len(vertices) <= 2048, "MESH_VERTICES", "bounded nonempty mesh")
        vertices = [vector(v, 3, "mesh vertex") for v in vertices]
        triangles = row["triangles"]
        primitive = target["primitive"]
        count = 12 if primitive["kind"] == "box" else 960
        require(type(triangles) is list and len(triangles) == count, "MESH_TRIANGLES", "existing finite tessellation")
        used, faces, edges = set(), set(), Counter()
        # Coincident seam/pole vertices may be separate native vertices. This fixed
        # 12-decimal key joins only sub-picometre residue, never the delivery bound.
        position_keys = [tuple(round(x, 12) for x in v) for v in vertices]
        unique_keys = {k: i for i, k in enumerate(sorted(set(position_keys)))}
        canonical = [unique_keys[k] for k in position_keys]
        for triangle in triangles:
            require(type(triangle) is list and len(triangle) == 3 and all(type(i) is int and 0 <= i < len(vertices) for i in triangle), "MESH_INDEX", "integer in-range triangle")
            ids = [canonical[i] for i in triangle]
            require(len(set(ids)) == 3 and tuple(sorted(ids)) not in faces, "MESH_DEGENERATE", "duplicate/collapsed face")
            faces.add(tuple(sorted(ids)))
            used.update(triangle)
            a, b, c = [vertices[i] for i in triangle]
            normal = cross([y-x for x, y in zip(a, b)], [y-x for x, y in zip(a, c)])
            require(math.hypot(*normal) > 0, "MESH_DEGENERATE", "zero-area triangle")
            require(math.fsum(normal[i]*(a[i]+b[i]+c[i]) for i in range(3)) > 0, "MESH_ORIENTATION", "outward finite surface")
            for i, j in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
                edges[tuple(sorted((i, j)))] += 1
        require(used == set(range(len(vertices))), "MESH_UNUSED", "every native vertex used")
        require(all(n == 2 for n in edges.values()), "MESH_CLOSURE", "two incident faces per edge")
        require(len(unique_keys)-len(edges)+len(faces) == 2, "MESH_TOPOLOGY", "single closed sphere topology")
        neighbors = {i: set() for i in unique_keys.values()}
        for a, b in edges:
            neighbors[a].add(b)
            neighbors[b].add(a)
        reached, pending = set(), [next(iter(neighbors))]
        while pending:
            vertex_id = pending.pop()
            if vertex_id not in reached:
                reached.add(vertex_id)
                pending.extend(neighbors[vertex_id] - reached)
        require(len(reached) == len(neighbors), "MESH_CONNECTED", "one connected finite surface")
        if primitive["kind"] == "box":
            halves = [x/2 for x in primitive["size_m"]]
            corners = list(itertools.product(*[(-h, h) for h in halves]))
            matched = []
            for vertex in vertices:
                candidates = [i for i, corner in enumerate(corners) if all(abs(a-e) <= DELIVERY_POSITION for a, e in zip(vertex, corner))]
                require(len(candidates) == 1, "BOX_CORNER", "actual local vertex at one required corner")
                matched.append(candidates[0])
            require(set(matched) == set(range(8)), "BOX_COVERAGE", "all eight corners")
            planes = Counter()
            for triangle in triangles:
                points = [corners[matched[i]] for i in triangle]
                shared = [(axis, points[0][axis]) for axis in range(3) if len({v[axis] for v in points}) == 1]
                require(len(shared) == 1, "BOX_FACE", "triangle lies on one box face")
                planes[shared[0]] += 1
            require(len(planes) == 6 and all(n == 2 for n in planes.values()), "BOX_FACE", "two triangles on each face")
        else:
            radius = primitive["radius_m"]
            require(len(unique_keys) == 482, "SPHERE_TESSELLATION", "32 longitude / 16 latitude envelope")
            for v in vertices:
                close(math.hypot(*v), radius, DELIVERY_POSITION, "sphere vertex radius")
            for axis in range(3):
                close(min(v[axis] for v in vertices), -radius, DELIVERY_POSITION, "sphere lower envelope")
                close(max(v[axis] for v in vertices), radius, DELIVERY_POSITION, "sphere upper envelope")
        check_origin(row["origin"], artifacts, program)


def file_map(value, where, nonempty=True):
    require(type(value) is dict and (bool(value) or not nonempty), "FILES", where)
    for name, raw in value.items():
        require(type(name) is str and name and not name.startswith("/") and "\\" not in name and all(p not in ("", ".", "..") for p in name.split("/")), "FILE_PATH", where)
        require(type(raw) is bytes, "FILE_BYTES", where + "/" + name)
        require(len(raw) > 0, "FILE_EMPTY", where + "/" + name)
    return value


def expected_sources(corpus, key):
    return {"main.ok": corpus.sources[key], "hinges.ok": corpus.sources["hinges"]}


def source_check(value, expected, where):
    file_map(value, where)
    require(set(value) == set(expected), "SOURCE_CLOSURE", where)
    require(value == expected, "SOURCE_BYTES", where)


def hashes(value):
    return {name: digest(raw) for name, raw in value.items()}


def state_check(value, corpus, key, where):
    keys(value, ("acceptedRevision", "programRevision", "sourceFiles", "artifacts"), where)
    text(value["acceptedRevision"], where + "/acceptedRevision")
    exact(value["programRevision"], PROGRAMS[key], where + "/programRevision")
    source_check(value["sourceFiles"], expected_sources(corpus, key), where + "/sourceFiles")
    file_map(value["artifacts"], where + "/artifacts")


def provenance_check(row, retained):
    keys(row, ("acceptedRevision", "programRevision", "sourceHashes", "artifactHashes", "semanticOrigin"), "provenance")
    exact(row["acceptedRevision"], retained["acceptedRevision"], "accepted revision")
    exact(row["programRevision"], retained["programRevision"], "program revision")
    exact(row["sourceHashes"], hashes(retained["sourceFiles"]), "source hashes")
    exact(row["artifactHashes"], hashes(retained["artifacts"]), "artifact hashes")
    check_origin(row["semanticOrigin"], retained["artifacts"], retained["programRevision"])


def authority_check(corpus, case_id, authority):
    keys(authority, ("schema", "attemptId", "caseId", "start", "candidate", "retained", "rebuild", "decision"), "authority")
    exact(authority["schema"], AUTHORITY_SCHEMA, "authority schema")
    exact(authority["caseId"], case_id, "authority case")
    text(authority["attemptId"], "opaque attempt id")
    start_key, candidate_key = CASE_KEYS[case_id]
    end_key = start_key if case_id == "N1" else candidate_key
    start, candidate, retained = authority["start"], authority["candidate"], authority["retained"]
    state_check(start, corpus, start_key, "start")
    state_check(retained, corpus, end_key, "retained")
    keys(candidate, ("candidateId", "parentAcceptedRevision", "sourceFiles", "artifacts"), "candidate")
    text(candidate["candidateId"], "candidateId")
    exact(candidate["parentAcceptedRevision"], start["acceptedRevision"], "candidate parent")
    source_check(candidate["sourceFiles"], expected_sources(corpus, candidate_key), "candidate source")
    file_map(candidate["artifacts"], "candidate artifacts", nonempty=case_id != "N1")
    decision = authority["decision"]
    keys(decision, ("status", "candidateId", "parentAcceptedRevision", "acceptedRevision", "boundary", "invalidEverAccepted", "diagnostic"), "decision")
    exact(decision["candidateId"], candidate["candidateId"], "decision candidate")
    exact(decision["parentAcceptedRevision"], start["acceptedRevision"], "decision parent")
    exact(decision["acceptedRevision"], retained["acceptedRevision"], "decision accepted revision")
    exact(decision["boundary"], "staged-before-accepted-replacement", "decision boundary")
    exact(decision["invalidEverAccepted"], False, "invalid candidate promotion")
    if case_id == "N1":
        exact(decision["status"], "rejected", "N1 rejection")
        require(retained == start, "RETAINED_STATE", "N1 exact accepted revision/source/dependency/artifact bytes")
        require(candidate["artifacts"] == {}, "N1_CANDIDATE_ARTIFACT", "invalid candidate has no accepted output")
        diagnostic = decision["diagnostic"]
        keys(diagnostic, ("code", "expectedDimension", "receivedDimension", "mechanism", "message"), "diagnostic")
        exact(diagnostic["code"], "incompatible-dimension", "diagnostic code")
        exact(diagnostic["expectedDimension"], "length", "diagnostic expected")
        exact(diagnostic["receivedDimension"], "mass", "diagnostic received")
        require(diagnostic["mechanism"] in ("compiler", "script_unit_validator", "author_refusal"), "N1_ROUTE_REJECTION", "harness-only protection earns no route detection")
        text(diagnostic["message"], "retained diagnostic")
    else:
        exact(decision["status"], "accepted", "valid acceptance")
        exact(decision["diagnostic"], None, "valid diagnostic")
        require(retained["acceptedRevision"] != start["acceptedRevision"], "STALE_REVISION", "valid edit requires a new accepted revision")
        require(retained["sourceFiles"] == candidate["sourceFiles"] and retained["artifacts"] == candidate["artifacts"], "ACCEPTED_BYTES", "candidate and retained actual bytes")
    rebuild = authority["rebuild"]
    keys(rebuild, ("sourceFiles", "artifacts", "cleanWorkspace", "declaredInputs", "determinism"), "rebuild authority")
    source_check(rebuild["sourceFiles"], retained["sourceFiles"], "rebuild source")
    file_map(rebuild["artifacts"], "rebuild artifacts")
    require(rebuild["artifacts"] == retained["artifacts"], "REBUILD_BYTES", "fixed byte-exact artifact policy")
    exact(rebuild["cleanWorkspace"], True, "clean rebuild workspace observation")
    exact(rebuild["declaredInputs"], ["hinges.ok", "main.ok"], "declared rebuild input closure")
    exact(rebuild["determinism"], "byte-exact", "rebuild policy")
    return retained


def evaluate(corpus, case_id, observation, authority):
    """Check finite inert records against independent expectations and caller bytes.

    Both arguments are supplied records. This API authenticates neither a caller
    nor an artifact reader. A true componentPass is never a real trial success.
    """
    result = {"schema": "ontokin.c255.component-result/0.1", "caseId": case_id,
              "componentPass": False, "faults": [], "realTrialSuccess": None,
              "executionAllowed": False, "artifactReaderQualified": False,
              "nativeStarts": 0, "modelTrials": 0, "observedObjects": 0,
              "observedPoses": 0, "claim": "inert record consistency only"}
    try:
        require(isinstance(corpus, Corpus) and case_id in CASE_KEYS, "CASE", "loaded corpus and known case")
        retained = authority_check(corpus, case_id, authority)
        keys(observation, ("schema", "attemptId", "caseId", "layer", "semantic", "geometry", "poses", "provenance", "rebuild", "decision"), "observation")
        exact(observation["schema"], SCHEMA, "observation schema")
        exact(observation["attemptId"], authority["attemptId"], "attempt identity")
        exact(observation["caseId"], case_id, "observation case")
        exact(observation["decision"], authority["decision"], "observed decision")
        expected = expected_state(corpus, case_id)
        for phase, row in (("final", observation), ("rebuild", observation["rebuild"])):
            if phase == "rebuild":
                keys(row, ("semantic", "geometry", "poses", "provenance"), "rebuild observation")
            semantic_check(row["semantic"], expected["semantic"])
            geometry_check(row["geometry"], expected["semantic"], retained["artifacts"], retained["programRevision"])
            pose_check(row["poses"], expected["poses"], observation["layer"], retained["artifacts"], retained["programRevision"])
            provenance_check(row["provenance"], retained)
        result.update(componentPass=True, observedObjects=18, observedPoses=126)
    except Fault as error:
        result["faults"].append({"code": error.code, "detail": error.detail})
    except (KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError, RecursionError) as error:
        result["faults"].append({"code": "MALFORMED", "detail": type(error).__name__})
    return result


def classify_attempt(case_id, admitted, started, outcome, component_pass=False):
    """Inert accounting control; records no real attempt and grants no trial score."""
    require(case_id in CASE_KEYS and type(admitted) is bool and type(started) is bool and type(component_pass) is bool, "ACCOUNTING", "typed accounting facts")
    allowed = ("completed", "missing_output", "timeout", "crash", "infrastructure_incident", "abstained", "budget_exhausted", "unavailable_before_start")
    require(outcome in allowed, "ACCOUNTING", "declared outcome")
    require(not started or admitted, "ACCOUNTING", "unadmitted attempted execution")
    require((not started and outcome == "unavailable_before_start") or (started and outcome != "unavailable_before_start"), "ACCOUNTING", "started attempt cannot leave denominator")
    return {"primaryDenominator": int(started and case_id != "N1"), "negativeDenominator": int(started and case_id == "N1"),
            "inertOutcomePass": started and outcome == "completed" and component_pass,
            "infrastructureIncident": started and outcome == "infrastructure_incident", "realTrialSuccess": None}


def decode_authority(document):
    """CLI transport: exact raw bytes use {encoding: hex, data: ...} envelopes."""
    def decode_map(value):
        require(type(value) is dict, "FILES", "hex file map")
        output = {}
        for name, encoded in value.items():
            keys(encoded, ("encoding", "data"), "encoded bytes")
            exact(encoded["encoding"], "hex", "byte encoding")
            require(type(encoded["data"]) is str and len(encoded["data"]) % 2 == 0 and all(x in "0123456789abcdef" for x in encoded["data"]), "FILE_BYTES", "canonical lowercase hex")
            output[name] = bytes.fromhex(encoded["data"])
        return output
    require(type(document) is dict, "SHAPE", "authority")
    for state in ("start", "candidate", "retained", "rebuild"):
        require(type(document.get(state)) is dict, "SHAPE", "authority state")
        for field in ("sourceFiles", "artifacts"):
            document[state][field] = decode_map(document[state].get(field))
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--case", choices=tuple(CASE_KEYS), required=True)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    args = parser.parse_args()
    try:
        corpus = load_corpus(args.repo)
        result = evaluate(corpus, args.case, read_json(args.observation), decode_authority(read_json(args.authority)))
    except (Fault, OSError, ValueError, TypeError, KeyError) as error:
        result = {"componentPass": False, "faults": [{"code": getattr(error, "code", "INPUT"), "detail": str(error)}], "realTrialSuccess": None, "executionAllowed": False}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["componentPass"] else 1


if __name__ == "__main__":
    sys.exit(main())
