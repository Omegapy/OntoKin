"""C272 delivered-semantic reader (G3, option A chosen by the owner on 2026-11-28).

It reads the semantic record that C255 scores from the delivered artifacts' actual bytes:
- the GLB's node metadata, material records, follows, joints, gravity and coordinates;
- the semantic sidecar's placement, initial velocities, sites, actions and events.

Every field carries its artifact, SHA-256 and JSON pointer. Producer metadata is an
observed claim: it passes only through C255's independent comparison. The fields that
decoded geometry and motion determine are also cross-checked against the decoded GLB
at C255's delivery limits.

Four facts that no delivered artifact carries in C255's form are read from the accepted
source as literal tokens at fixed patterns, with byte spans; no expression is evaluated.
Zero mass is derived from `no_body` and from the absence of any mass or body declaration,
and is labelled so. It imports no OntoKin product module.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re
import struct

import observe

LIMITS = {"bytes": 4 * 1024 * 1024, "json_bytes": 2 * 1024 * 1024, "nodes": 64, "objects": 64, "sites": 256,
          "follows": 128, "joints": 128, "actions": 64, "event_blocks": 64, "operations": 256, "depth": 64}
SIDECAR_SCHEMA = "ontokin.semantic-export/0.1"
GLB_CONTRACT = "ontokin.glb/0.2"
PATTERNS = {
    "gravity frame": (rb"gravity = vector\(([a-z]+),", "main.ok"),
    "tween target angle": (rb"\.bend_to\(([0-9]+(?:\.[0-9]+)?)\[([a-z]+)\]", "main.ok"),
    "move frame": (rb"move\([a-z_]+, vector\(([a-z]+),", "main.ok"),
    "event block": (rb"at ([0-9]+(?:\.[0-9]+)?)\[s\] ([a-z]+) \{", "main.ok"),
}
MATTER_TOKENS = rb"\b(mass|density|body|matter|physical)\b"


class SemanticFault(Exception):
    def __init__(self, code: str, detail: str):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


def require(condition, code, detail):
    if not condition:
        raise SemanticFault(code, detail)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw: bytes, where: str):
    require(type(raw) is bytes and len(raw) <= LIMITS["json_bytes"], "RESOURCE_LIMIT", where + " JSON size")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "JSON_DUPLICATE", f"{where}: {key}")
            result[key] = value
        return result
    def constant(value):
        raise SemanticFault("NONFINITE", f"{where}: {value}")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise SemanticFault("JSON_MALFORMED", f"{where}: {type(error).__name__}") from error
    depth = lambda v, d=0: d if not isinstance(v, (dict, list)) else max(
        [depth(x, d + 1) for x in (v.values() if isinstance(v, dict) else v)] or [d + 1])
    require(depth(value) <= LIMITS["depth"], "RESOURCE_LIMIT", where + " nesting depth")
    return value


def glb_document(raw: bytes) -> dict:
    require(type(raw) is bytes and 28 <= len(raw) <= LIMITS["bytes"], "GLB_SIZE", "raw bytes")
    magic, version, length = struct.unpack_from("<III", raw)
    require(magic == 0x46546C67 and version == 2 and length == len(raw), "GLB_HEADER", "magic, version, length")
    size, kind = struct.unpack_from("<II", raw, 12)
    require(kind == 0x4E4F534A and 20 + size <= len(raw), "GLB_CHUNK", "JSON chunk")
    return strict_json(raw[20:20 + size], "GLB JSON chunk")


def decimal_number(text: str, where: str):
    require(type(text) is str and re.fullmatch(r"-?[0-9]+(\.[0-9]+)?", text), "NUMBER", where)
    try:
        value = Decimal(text)
    except InvalidOperation as error:
        raise SemanticFault("NUMBER", where) from error
    return int(value) if value == value.to_integral_value() else float(value)


def literal(source_files: dict, name: str) -> tuple[tuple, dict]:
    pattern, filename = PATTERNS[name]
    matches = list(re.finditer(pattern, source_files[filename]))
    require(len(matches) == 1, "SOURCE_LITERAL", f"{name}: exactly one match")
    m = matches[0]
    groups = tuple(g.decode("ascii") for g in m.groups())
    return groups, {"file": filename, "sha256": sha256(source_files[filename]), "startByte": m.start(1),
                    "endByteExclusive": m.end(m.lastindex), "pattern": pattern.decode("ascii"), "value": list(groups)}


# Quaternion and vector helpers, WXYZ.
def qmul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return [aw*bw - ax*bx - ay*by - az*bz, aw*bx + ax*bw + ay*bz - az*by,
            aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw]


def qconj(q):
    return [q[0], -q[1], -q[2], -q[3]]


def rotate(q, v):
    return qmul(qmul(q, [0.0, *v]), qconj(q))[1:]


def qangle(a, b):
    na, nb = math.hypot(*a), math.hypot(*b)
    dot = abs(math.fsum(x * y for x, y in zip(a, b)) / (na * nb))
    return 2 * math.acos(min(1.0, dot))


def distance(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


class Reader:
    def __init__(self, source_files, glb, sidecar, delivery):
        require(delivery.get("valid") is True, "DELIVERY_INVALID", "the decoded delivery must be valid first")
        self.oracle = observe.pinned("c255_oracle")
        self.position, self.angle = self.oracle.DELIVERY_POSITION, self.oracle.DELIVERY_ANGLE
        self.sources, self.glb, self.sidecar = source_files, glb, sidecar
        self.glb_sha, self.side_sha = sha256(glb), sha256(sidecar)
        self.doc = glb_document(glb)
        self.side = strict_json(sidecar, "sidecar")
        self.origins, self.checks, self.literals, self.derived = {}, [], [], []
        self.poses = {(tuple(p["id"]), p["time_s"]): p for p in delivery["poses"]}
        self.meshes = {tuple(g["id"]): g["vertices_m"] for g in delivery["geometry"]}
        self.times = sorted({t for _, t in self.poses})

    def origin(self, field, artifact, pointer):
        sha = self.glb_sha if artifact == "scene.glb" else self.side_sha
        self.origins.setdefault(field, []).append({"artifact": artifact, "sha256": sha, "pointer": pointer})

    def check(self, name, passed, **detail):
        self.checks.append({"check": name, "passed": bool(passed), **detail})

    def bounded(self, value, kind, where):
        require(type(value) is list, "SHAPE", where)
        require(len(value) <= LIMITS[kind], "RESOURCE_LIMIT", f"{where}: more than {LIMITS[kind]} {kind}")
        return value

    def read(self) -> dict:
        doc, side = self.doc, self.side
        meta = doc["extras"]["ontokin"]
        require(meta.get("target_contract") == GLB_CONTRACT, "PROFILE", "GLB target contract")
        require(side.get("schema_version") == SIDECAR_SCHEMA, "PROFILE", "sidecar schema")
        nodes = self.bounded(doc["nodes"], "nodes", "/nodes")
        binding = side["binding"]
        program = meta["program"]["revision"]
        stale = (binding["artifact"]["sha256"] != "sha256:" + self.glb_sha or binding["artifact"]["bytes"] != len(self.glb)
                 or binding["accepted_program_revision"] != program)
        require(not stale, "STALE_SIDECAR", "the sidecar does not bind this GLB and program revision")
        self.origin("binding", "scene.semantic.json", "/binding")
        node_meta = [n["extras"]["ontokin"] for n in nodes]
        by_path = {}
        for i, m in enumerate(node_meta):
            require(m["path"] not in by_path, "DUPLICATE_IDENTITY", m["path"])
            by_path[m["path"]] = m["element_id"]
        def object_id(path):
            require(path in by_path, "UNKNOWN_REFERENCE", str(path))
            return list(by_path[path])
        def frame_object(ref):
            require(type(ref) is str and ref.endswith(".frame"), "UNKNOWN_REFERENCE", str(ref))
            return object_id(ref[:-len(".frame")])
        self.object_id, self.frame_object = object_id, frame_object

        coordinates, glb_coordinates = side["coordinates"], meta["coordinates"]
        units = {key: coordinates[key] for key in ("length", "time", "angle", "mass")}
        for key in ("length", "time", "angle", "mass"):
            self.origin("units", "scene.semantic.json", f"/coordinates/{key}")
        self.check("units agree between GLB and sidecar", glb_coordinates["length_unit"] == units["length"]
                   and glb_coordinates["time_unit"] == units["time"])
        pose_frames = {m["pose_frame"] for m in node_meta}
        require(len(pose_frames) == 1, "FRAME", "one pose frame for every node")
        frame = {"handedness": glb_coordinates["handedness"], "up": glb_coordinates["up"], "basis": next(iter(pose_frames)),
                 "quaternionOrder": coordinates["source_rotation_order"]}
        for key in ("handedness", "up"):
            self.origin("frame", "scene.glb", f"/extras/ontokin/coordinates/{key}")
        for i in range(len(node_meta)):
            self.origin("frame", "scene.glb", f"/nodes/{i}/extras/ontokin/pose_frame")
        self.origin("frame", "scene.semantic.json", "/coordinates/source_rotation_order")
        self.check("frame agrees between GLB and sidecar", coordinates["handedness"] == frame["handedness"]
                   and coordinates["up"] == frame["up"])

        prefixes = {tuple(m["element_id"][:2]) for m in node_meta}
        require(len(prefixes) == 1, "IDENTITY", "one scene key prefix")
        (gravity_frame,), span = literal(self.sources, "gravity frame")
        self.literals.append({"field": "scene.gravityFrame", **span})
        scene = {"id": list(next(iter(prefixes))), "duration_s": decimal_number(side["scene"]["duration_seconds"], "duration"),
                 "gravity_mps2": meta["gravity_m_per_s2"], "gravityFrame": gravity_frame}
        self.origin("scene", "scene.glb", "/extras/ontokin/gravity_m_per_s2")
        for i in range(len(node_meta)):
            self.origin("scene", "scene.glb", f"/nodes/{i}/extras/ontokin/element_id (segments 0 and 1)")
        self.origin("scene", "scene.semantic.json", "/scene/duration_seconds")
        self.check("gravity agrees between GLB and sidecar", side["scene"]["gravity_m_per_s2"] == meta["gravity_m_per_s2"])

        side_objects = {}
        for i, row in enumerate(self.bounded(side["objects"], "objects", "/objects")):
            key = tuple(row["element_id"])
            require(key not in side_objects, "DUPLICATE_IDENTITY", "sidecar object")
            side_objects[key] = (i, row)
        require(set(side_objects) == {tuple(m["element_id"]) for m in node_meta}, "IDENTITY_SET", "GLB and sidecar objects")
        matter_tokens = [name for name, raw in self.sources.items() if re.search(MATTER_TOKENS, raw)]
        self.check("no mass, density, body or physical declaration in the accepted source", not matter_tokens,
                   files=matter_tokens)
        objects = []
        for i, (node, m) in enumerate(zip(nodes, node_meta)):
            j, so = side_objects[tuple(m["element_id"])]
            material = doc["materials"][doc["meshes"][node["mesh"]]["primitives"][0]["material"]]
            color = material["pbrMetallicRoughness"]["baseColorFactor"]
            self.check(f"appearance agrees with the material record: {m['path']}",
                       color == m["appearance_linear_rgba"] == so["appearance_linear_rgba"])
            self.check(f"properties agree between GLB and sidecar: {m['path']}", so["properties"] == m["properties"])
            self.check(f"geometry agrees between GLB and sidecar: {m['path']}", so["geometry"] == m["geometry"])
            owner = None if m["owner"] is None else object_id(m["owner"])
            sidecar_owner = None if so["owner"] is None else list(so["owner"]["element_id"])
            self.check(f"owner agrees between GLB and sidecar: {m['path']}", owner == sidecar_owner)
            physical = m["physical"]
            require(physical == {"kind": "no_body"} == so["physical"], "UNSUPPORTED_MATTER", m["path"])
            self.derived.append({"field": f"objects[{m['path']}].matter",
                                 "rule": "physical.kind no_body carries no matter; own and aggregate mass are 0 kg",
                                 "basis": [f"scene.glb /nodes/{i}/extras/ontokin/physical", f"scene.semantic.json /objects/{j}/physical",
                                           "no mass, density, body or physical token in main.ok or hinges.ok"]})
            placement = so["placement"]
            placed = ({"kind": "declared", "frame": placement["frame"], "position_m": placement["position_m"],
                       "rotation_wxyz": placement["rotation_wxyz"]} if placement["authored"] is True else {"kind": "undeclared"})
            require(type(placement["authored"]) is bool, "SHAPE", "placement.authored")
            motion = so["motion"]
            objects.append({"id": m["element_id"], "path": m["path"], "definitionId": m["source_mapping"]["definition_id"],
                            "owner": owner, "parameters": {k: self.typed(v, k) for k, v in m["properties"].items()},
                            "primitive": self.primitive(m["geometry"]), "appearance": color, "placement": placed,
                            "matter": {"kind": "no_body", "own_mass_kg": 0, "aggregate_mass_kg": 0},
                            "initialLinearVelocity_mps": motion["initial_velocity_m_per_s"],
                            "initialAngularVelocity_radps": motion["initial_omega_rad_per_s"]})
            for field, pointer in (("id,path,owner,properties,geometry,physical", f"/nodes/{i}/extras/ontokin"),
                                   ("definitionId", f"/nodes/{i}/extras/ontokin/source_mapping/definition_id"),
                                   ("appearance", f"/materials/{doc['meshes'][node['mesh']]['primitives'][0]['material']}/pbrMetallicRoughness/baseColorFactor")):
                self.origin(f"objects[{'/'.join(m['element_id'])}]", "scene.glb", pointer)
            self.origin(f"objects[{'/'.join(m['element_id'])}]", "scene.semantic.json", f"/objects/{j}/placement")
            self.origin(f"objects[{'/'.join(m['element_id'])}]", "scene.semantic.json", f"/objects/{j}/motion")

        side_sites = self.bounded(side["sites"], "sites", "/sites")
        site_by_path = {}
        sites = []
        for j, s in enumerate(side_sites):
            require(s["path"] not in site_by_path, "DUPLICATE_IDENTITY", s["path"])
            site_by_path[s["path"]] = s["element_id"]
            sites.append({"id": s["element_id"], "owner": object_id(s["owner"]), "frame": frame_object(s["pose"]["frame"]),
                          "position_m": s["pose"]["position_m"], "rotation_wxyz": s["pose"]["rotation_wxyz"],
                          "interface": s["interface"], "size_m": s["size_m"],
                          "kind": "system" if "@system" in s["element_id"] else "authored"})
            self.origin(f"sites[{'/'.join(s['element_id'])}]", "scene.semantic.json", f"/sites/{j}")
            self.derived.append({"field": f"sites[{'/'.join(s['element_id'])}].kind",
                                 "rule": "kind is 'system' when the element ID holds '@system', otherwise 'authored'",
                                 "basis": [f"scene.semantic.json /sites/{j}/element_id"]})

        follows = []
        side_follows = {tuple(f["element_id"]): f for f in self.bounded(side["follows"], "follows", "/follows")}
        for j, f in enumerate(self.bounded(meta["follows"], "follows", "/extras/ontokin/follows")):
            record = {"id": f["element_id"], "parentFrame": frame_object(f["parent_frame"]), "child": object_id(f["child_object"]),
                      "offsetPosition_m": f["offset_position_m"], "offsetRotation_wxyz": f["offset_rotation_wxyz"]}
            follows.append(record)
            sf = side_follows.get(tuple(f["element_id"]))
            self.check(f"follow agrees between GLB and sidecar: {f['path']}", sf is not None
                       and sf["offset"]["position_m"] == f["offset_position_m"] and sf["offset"]["rotation_wxyz"] == f["offset_rotation_wxyz"]
                       and sf["parent_frame"] == f["parent_frame"] and sf["child_object"] == f["child_object"])
            self.origin(f"follows[{'/'.join(f['element_id'])}]", "scene.glb", f"/extras/ontokin/follows/{j}")

        hinges, joint_by_path = [], {}
        side_joints = {tuple(x["element_id"]): x for x in self.bounded(side["joints"], "joints", "/joints")}
        for j, h in enumerate(self.bounded(meta["joints"], "joints", "/extras/ontokin/joints")):
            sj = side_joints.get(tuple(h["element_id"]))
            require(sj is not None and "axis_in_parent_site" in sj, "UNKNOWN_REFERENCE", h["path"])
            require(h["parent_site"] in site_by_path and h["child_site"] in site_by_path, "UNKNOWN_REFERENCE", h["path"])
            joint_by_path[h["path"]] = h["element_id"]
            hinges.append({"id": h["element_id"], "kind": h["kind"], "parentSite": site_by_path[h["parent_site"]],
                           "childSite": site_by_path[h["child_site"]], "axis": h["axis"],
                           "axisFrame": site_by_path[sj["parent_site"]], "limits_rad": h["limits"], "initial_rad": h["initial"]})
            self.check(f"hinge agrees between GLB and sidecar: {h['path']}", sj["axis_in_parent_site"] == h["axis"]
                       and sj["limits_rad"] == h["limits"] and sj["initial_rad"] == h["initial"]
                       and sj["parent_site"] == h["parent_site"] and sj["child_site"] == h["child_site"])
            key = f"hinges[{'/'.join(h['element_id'])}]"
            self.origin(key, "scene.glb", f"/extras/ontokin/joints/{j}")
            side_index = next(i for i, x in enumerate(side["joints"]) if x["element_id"] == h["element_id"])
            self.origin(key, "scene.semantic.json", f"/joints/{side_index}/axis_in_parent_site")
            self.derived.append({"field": key + ".axisFrame",
                                 "rule": "the axis is given in the parent site's frame, as the sidecar key axis_in_parent_site names it",
                                 "basis": [f"scene.semantic.json /joints/{side_index}/axis_in_parent_site"]})

        (angle_text, angle_unit), angle_span = literal(self.sources, "tween target angle")
        (move_frame,), move_span = literal(self.sources, "move frame")
        actions, action_by_path = [], {}
        for j, a in enumerate(self.bounded(side["actions"], "actions", "/actions")):
            action_by_path[a["path"]] = a["element_id"]
            duration = decimal_number(a["duration_seconds"], "action duration")
            if a["kind"] == "tween":
                require(a["target"] in joint_by_path, "UNKNOWN_REFERENCE", a["target"])
                value = decimal_number(angle_text, "tween angle")
                self.literals.append({"field": f"actions[{a['path']}].targetAngle", **angle_span})
                self.check(f"tween literal agrees with the delivered goal: {a['path']}", angle_unit == "deg"
                           and abs(a["hinge_goal_rad"] - value * math.pi / 180) <= 1e-12)
                actions.append({"id": a["element_id"], "kind": "tween", "joint": list(joint_by_path[a["target"]]),
                                "targetAngle": {"value": value, "unit": angle_unit}, "duration_s": duration})
            elif a["kind"] == "move":
                self.literals.append({"field": f"actions[{a['path']}].frame", **move_span})
                actions.append({"id": a["element_id"], "kind": "move", "object": object_id(a["target"]),
                                "velocity_mps": a["velocity_m_per_s"], "frame": move_frame, "duration_s": duration})
            else:
                raise SemanticFault("UNSUPPORTED_ACTION", a["kind"])
            self.origin(f"actions[{'/'.join(a['element_id'])}]", "scene.semantic.json", f"/actions/{j}")

        (time_text, mode), event_span = literal(self.sources, "event block")
        blocks = self.bounded(side["events"], "event_blocks", "/events")
        require(len(blocks) == 1, "EVENT_BLOCKS", "one delivered block for the one source block")
        events = []
        for j, block in enumerate(blocks):
            operations = self.bounded(block["events"], "operations", f"/events/{j}/events")
            for e in operations:
                require(e["target"] in action_by_path, "UNKNOWN_REFERENCE", e["target"])
            events.append({"time_s": decimal_number(block["time_seconds"], "event time"), "mode": mode,
                           "operations": [{"operation": e["kind"], "action": list(action_by_path[e["target"]])} for e in operations]})
            self.check("event time agrees with the source literal", decimal_number(time_text, "event literal") == events[-1]["time_s"])
            self.origin("events", "scene.semantic.json", f"/events/{j}")
        self.literals.append({"field": "events[0].mode", **event_span})

        semantic = {"units": units, "frame": frame, "scene": scene, "objects": objects, "sites": sites,
                    "follows": follows, "hinges": hinges, "actions": actions, "events": events}
        self.motion_checks(semantic)
        return semantic

    def typed(self, value, where):
        kind = value["type"]
        if kind == "Length":
            require(type(value["value"]) in (int, float), "TYPE", where)
            return {"value": value["value"], "unit": "m"}
        if kind == "Vec3<Length>":
            items = value["value"]
            require(len(items) == 3 and all(x["type"] == "Length" for x in items), "TYPE", where)
            return {"value": [x["value"] for x in items], "unit": "m"}
        if kind == "Keyed<Vec3<Length>>":
            result = {}
            for entry in value["value"]:
                require(entry["key"] not in result, "DUPLICATE_KEY", where)
                result[entry["key"]] = self.typed(entry["value"], where + "/" + entry["key"])
            return result
        if kind == "Color":
            require(len(value["value"]) == 4, "TYPE", where)
            return list(value["value"])
        if kind == "FrameRef":
            return {"object": self.frame_object(value["value"])}
        raise SemanticFault("UNSUPPORTED_TYPE", f"{where}: {kind}")

    @staticmethod
    def primitive(geometry):
        if geometry["kind"] == "box":
            return {"kind": "box", "size_m": list(geometry["size"])}
        if geometry["kind"] == "sphere":
            return {"kind": "sphere", "radius_m": geometry["radius"]}
        raise SemanticFault("UNSUPPORTED_PRIMITIVE", geometry["kind"])

    def pose(self, oid, t):
        row = self.poses[(tuple(oid), t)]
        return row["position_m"], row["rotation_wxyz"]

    def motion_checks(self, semantic):
        """Cross-check delivered declarations against the decoded geometry and motion."""
        P, A = self.position, self.angle
        objects = {tuple(o["id"]): o for o in semantic["objects"]}
        sites = {tuple(s["id"]): s for s in semantic["sites"]}
        for oid, o in objects.items():
            vertices = self.meshes[oid]
            extent = [max(v[k] for v in vertices) - min(v[k] for v in vertices) for k in range(3)]
            if o["primitive"]["kind"] == "box":
                error = distance(extent, o["primitive"]["size_m"])
            else:
                error = max(abs(math.hypot(*v) - o["primitive"]["radius_m"]) for v in vertices)
            self.check(f"declared primitive agrees with the decoded mesh: {o['path']}", error <= P, maxError=error, tolerance=P)
            if o["placement"]["kind"] == "declared":
                position, rotation = self.pose(oid, 0.0)
                self.check(f"declared placement agrees with the decoded pose at 0 s: {o['path']}",
                           distance(position, o["placement"]["position_m"]) <= P and qangle(rotation, o["placement"]["rotation_wxyz"]) <= A)
        for sid, s in sites.items():
            vertices = self.meshes[tuple(s["owner"])]
            low = [min(v[k] for v in vertices) for k in range(3)]
            high = [max(v[k] for v in vertices) for k in range(3)]
            centre = [(a + b) / 2 for a, b in zip(low, high)]
            if s["kind"] == "authored" and sid[-1] == "base":
                expected = [low[0], centre[1], centre[2]]
                error = distance(s["position_m"], expected)
                self.check(f"base site lies on the decoded blade's -X face: {'/'.join(sid)}", error <= P, maxError=error, tolerance=P)
            elif s["kind"] == "authored" and sid[-1] == "pivot":
                error = distance(s["position_m"], centre)
                self.check(f"pivot site lies at the decoded finger's centre: {'/'.join(sid)}", error <= P, maxError=error, tolerance=P)
        world = lambda site, t: [a + b for a, b in zip(self.pose(site["owner"], t)[0],
                                                       rotate(self.pose(site["owner"], t)[1], site["position_m"]))]
        angle_of = {}
        for h in semantic["hinges"]:
            parent, child = sites[tuple(h["parentSite"])], sites[tuple(h["childSite"])]
            low, high = h["limits_rad"]
            angles, coincide, aligned = [], 0.0, 0.0
            for t in self.times:
                coincide = max(coincide, distance(world(parent, t), world(child, t)))
                parent_frame = qmul(self.pose(parent["owner"], t)[1], parent["rotation_wxyz"])
                child_frame = qmul(self.pose(child["owner"], t)[1], child["rotation_wxyz"])
                relative = qmul(qconj(parent_frame), child_frame)
                # q and -q are the same rotation; fix the sign before reading the angle,
                # so that an equivalent stored sign never yields theta - 2*pi (review M2).
                if relative[0] < 0:
                    relative = [-x for x in relative]
                axis = h["axis"]
                theta = 2 * math.atan2(math.fsum(x * y for x, y in zip(relative[1:], axis)), relative[0])
                ideal = [math.cos(theta / 2), *[x * math.sin(theta / 2) for x in axis]]
                aligned = max(aligned, qangle(relative, ideal))
                angles.append((t, theta))
            angle_of[tuple(h["id"])] = dict(angles)
            name = "/".join(h["id"])
            self.check(f"hinge sites coincide in the decoded motion: {name}", coincide <= P, maxError=coincide, tolerance=P)
            self.check(f"decoded relative rotation is about the declared axis: {name}", aligned <= A, maxError=aligned, tolerance=A)
            self.check(f"decoded angles stay within the declared limits: {name}",
                       all(low - A <= a <= high + A for _, a in angles))
            self.check(f"decoded angle at 0 s equals the declared initial angle: {name}",
                       abs(angle_of[tuple(h["id"])][0.0] - h["initial_rad"]) <= A)
        for f in semantic["follows"]:
            worst_p = worst_a = 0.0
            for t in self.times:
                parent_p, parent_q = self.pose(f["parentFrame"], t)
                child_p, child_q = self.pose(f["child"], t)
                worst_p = max(worst_p, distance(child_p, [a + b for a, b in zip(parent_p, rotate(parent_q, f["offsetPosition_m"]))]))
                worst_a = max(worst_a, qangle(child_q, qmul(parent_q, f["offsetRotation_wxyz"])))
            self.check(f"follow offset holds in the decoded motion: {'/'.join(f['id'])}", worst_p <= P and worst_a <= A,
                       maxError=[worst_p, worst_a], tolerance=[P, A])
        for a in semantic["actions"]:
            name = "/".join(a["id"])
            if a["kind"] == "move":
                start = self.pose(a["object"], 0.0)[0]
                error = max(distance([p - s for p, s in zip(self.pose(a["object"], t)[0], start)],
                                     [v * min(t, a["duration_s"]) for v in a["velocity_mps"]]) for t in self.times)
                self.check(f"move velocity agrees with the decoded displacement: {name}", error <= P, maxError=error, tolerance=P)
            else:
                goal = a["targetAngle"]["value"] * math.pi / 180
                after = [abs(angle_of[tuple(a["joint"])][t] - goal) for t in self.times if t >= a["duration_s"]]
                self.check(f"tween goal is reached by its duration in the decoded motion: {name}",
                           bool(after) and max(after) <= A, maxError=max(after) if after else None, tolerance=A)


def observe_semantic(source_files: dict, glb: bytes, sidecar: bytes, delivery: dict) -> dict:
    """Read and cross-check the delivered semantic record; every refusal is a typed fault."""
    result = {"schema": "ontokin.c272.delivered-semantic/1", "valid": False, "semantic": None, "fault": None,
              "artifacts": {"scene.glb": sha256(glb) if type(glb) is bytes else None,
                            "scene.semantic.json": sha256(sidecar) if type(sidecar) is bytes else None},
              "limit": ("Delivered producer metadata checked against C255's independent expectations and "
                        "cross-checked against decoded motion; not an independent re-interpretation of the source expressions.")}
    try:
        reader = Reader(source_files, glb, sidecar, delivery)
        semantic = reader.read()
        result.update(semantic=semantic, origins=reader.origins, crossChecks=reader.checks, sourceLiterals=reader.literals,
                      derived=reader.derived, valid=all(c["passed"] for c in reader.checks))
    except SemanticFault as error:
        result["fault"] = {"code": error.code, "detail": error.detail}
    except (KeyError, IndexError, TypeError, AttributeError, ValueError, struct.error, OverflowError, RecursionError) as error:
        result["fault"] = {"code": "MALFORMED", "detail": type(error).__name__}
    return result
