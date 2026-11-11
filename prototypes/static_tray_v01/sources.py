"""Two exact source closures lowered through one strict construction boundary.

The OntoKin route consumes the unchanged construction compiler's resolved model
and original AST. It never parses a second source grammar or substitutes boxes
constructed from parameter labels for compiled geometry.
"""

import ast
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
import types

from .canonical import (CONSTANTS, IDENTITY, PARTS, PARAMETER_KEYS, ROTATIONS, bits,
                        canonical_bytes, f64, json_bytes, record_identity, strict_json)
from .errors import CONTRACT, PROFILE, TrayError


@dataclass(frozen=True)
class Lowered:
    record: dict
    canonical_bytes: bytes
    provenance: dict
    files: dict[str, bytes]


def _sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _bounded_source_file(path,limit,*,code="CLOSURE"):
    """Read at most cap+1 bytes from the opened regular non-symlink file."""
    try:
        fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,"rb") as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise TrayError("CLOSURE","Source binding is not a regular file.",stage="binding",pointer=str(path))
            data=stream.read(limit+1)
        if len(data)>limit:
            raise TrayError(code,"Bound source input exceeds its byte allowance.",stage="binding",pointer=str(path))
        return data,(info.st_dev,info.st_ino)
    except OSError as exc:
        raise TrayError("CLOSURE","Source binding could not be opened without following a symlink.",stage="binding",pointer=str(path)) from exc


def _read_sources(route, path, check):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise TrayError("CLOSURE", "Source manifest must be an existing regular nonsymlink file.", stage="binding")
    path = path.resolve()
    raw_manifest,manifest_file_id = _bounded_source_file(path,32768,code="RESOURCE")
    manifest = strict_json(raw_manifest, limit=32768)
    names = {"main.ok", "tray.ok"} if route == "ontokin" else {"main.py", "tray.py"}
    if path.name in names:
        raise TrayError("CLOSURE","Source manifest must be distinct from both editable source units.",stage="binding")
    allowed = names | {path.name}
    actual = set()
    with os.scandir(path.parent) as entries:
        for entry in entries:
            check()
            actual.add(entry.name)
            if len(actual)>3:
                raise TrayError("CLOSURE", "Source directory exceeds the exact three-entry closure.", stage="binding")
    if actual != allowed:
        raise TrayError("CLOSURE", "Exactly two source files and their manifest are required.",
                        stage="binding", details={"expected": sorted(allowed), "actual": sorted(actual)})
    files = {}
    opened_file_ids={manifest_file_id}
    for name in sorted(names):
        check()
        source = path.parent / name
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 32768:
            raise TrayError("CLOSURE", "Source must be a regular local file of at most 32768 bytes.",
                            stage="binding", pointer=name)
        data,file_id = _bounded_source_file(source,32768)
        if file_id in opened_file_ids:
            raise TrayError("CLOSURE","Source units and manifest must not alias the same file.",stage="binding",pointer=name)
        opened_file_ids.add(file_id)
        try:
            data.decode("utf-8")
        except UnicodeError as exc:
            raise TrayError("CLOSURE", "Source is not UTF-8.", stage="binding", pointer=name) from exc
        files[name] = data
    if sum(map(len, files.values())) > 65536:
        raise TrayError("RESOURCE", "Combined source allowance exceeded.", stage="binding")
    if route == "ontokin":
        wanted = {"schema_version": "ontokin.files/0.1", "entry": {"filename": "main.ok", "path": "main.ok"},
                  "modules": [{"package_id": "ontokin.static-tray", "version": "0.1.0", "filename": "tray.ok", "path": "tray.ok"}]}
        if manifest != wanted:
            raise TrayError("CLOSURE", "Only the exact two-file OntoKin manifest is admitted.", stage="binding")
    else:
        wanted = {"schema_version": "ontokin.static-tray.python-sources/0.1.0", "entry_filename": "main.py",
                  "files": [{"filename": name, "source_revision": _sha(data), "size_bytes": len(data)}
                            for name, data in sorted(files.items())]}
        if manifest != wanted or raw_manifest != json_bytes(wanted):
            raise TrayError("CLOSURE", "Python source manifest, exact hashes, sizes or canonical bytes differ.", stage="binding")
    return files, manifest


def _path_names(node):
    return tuple(step.value for step in node.path)


def _call(node, name, arity):
    return (node.kind == "call" and node.callee.kind == "name" and node.callee.name == name
            and len(node.args) == arity)


def _literal_number(node):
    sign = 1
    if node.kind == "unary" and node.op in ("+", "-"):
        sign = -1 if node.op == "-" else 1
        node = node.value
    if node.kind != "number" or node.unit is not None:
        return None
    try:
        return Fraction(node.text) * sign
    except ValueError:
        return None


def _literal_rotation(pose, *, root):
    if not _call(pose, "pose", 3):
        return False
    if root and (pose.args[0].kind != "name" or pose.args[0].name != "world"):
        return False
    q = pose.args[2]
    if not _call(q, "quat", 4):
        return False
    values = tuple(_literal_number(arg) for arg in q.args)
    if None in values:
        return False
    if not root:
        return values == tuple(Fraction(v) for v in IDENTITY)
    return values in ROTATIONS or tuple(-v for v in values) in ROTATIONS


def _lower_ontokin(files, check):
    from ontokin.bundle import load_bundle
    from ontokin.construction import compile_construction
    from ontokin.syntax02 import parse_source_unit
    from ontokin.values import LENGTH

    bundle = load_bundle({"schema_version": "ontokin.bundle/0.1",
                          "entry": {"filename": "main.ok", "source": files["main.ok"].decode()},
                          "modules": [{"package_id": "ontokin.static-tray", "version": "0.1.0",
                                       "filename": "tray.ok", "source": files["tray.ok"].decode()}]})
    # The existing parser supplies the binding AST; source syntax errors remain OKL errors.
    entry = parse_source_unit(bundle.entry, check=check)
    if len(entry.imports) != 1 or any((entry.imports[0].package_id != "ontokin.static-tray",
                                     entry.imports[0].version != "0.1.0",
                                     entry.imports[0].digest != bundle.modules[0].revision)):
        raise TrayError("CLOSURE", "Entry import does not pin the supplied tray module.", stage="binding",
                        candidate=bundle.program_revision)
    compiler = compile_construction(bundle, level="constructed", check=check,
                                    budgets={"max_operations": 100000, "max_elapsed_ms": 30000})
    model = compiler.model
    entry = compiler.linked.entry.ast
    module = compiler.linked.modules[bundle.modules[0].source_id].ast
    findings = []
    def require(condition, code, message, node=None, sid=""):
        if condition:
            return
        item = {"code": "OTRAY-E-" + code, "reason": message, "semantic_id": sid}
        if node is not None and node.source_id in compiler.source_registry:
            source = compiler.source_registry[node.source_id]
            item["source"] = {"source_id": node.source_id, "source_revision": source.revision,
                              "filename": source.filename, "start_byte": node.start, "end_byte": node.end}
        findings.append(item)
    def finish():
        if findings:
            findings.sort(key=lambda x: (x["semantic_id"], x["code"], x["reason"]))
            raise TrayError(findings[0]["code"], "Compiled source is outside the finite tray family.",
                            candidate=bundle.program_revision, findings=findings)

    require(entry.module_key == "equipment-tray" and model.scene_key == "pair", "IDENTITY", "Entry scene identity differs.", entry)
    require(not entry.definitions and not entry.requires, "SHAPE", "Entry cannot define classes, functions or capabilities.", entry)
    require(module.module_key == "static-tray" and module.scene is None and not module.imports
            and not module.requires and not module.functions, "SHAPE", "Module is not the finite reusable definition closure.", module)
    require(len(module.classes) == 2 and {n.key for n in module.classes} == {"tray", "box"},
            "SHAPE", "Exactly tray and box classes are required.", module)
    require(all(n.kind in {"assign", "object"} for n in entry.scene.members), "SHAPE", "Extra entry scene declaration.", entry.scene)
    assigns = [n for n in entry.scene.members if n.kind == "assign"]
    require(len(assigns) == 2 and {_path_names(n) for n in assigns} == {("duration",), ("gravity",)},
            "SHAPE", "Entry must author only duration and world gravity.", entry.scene)
    require(model.duration == 1 and model.gravity == (0., 0., 0.), "PHYSICS", "Duration must be one second and gravity zero.", entry.scene)
    gravity_nodes = [n.value for n in assigns if _path_names(n) == ("gravity",)]
    require(len(gravity_nodes) == 1 and _call(gravity_nodes[0], "vector", 4)
            and gravity_nodes[0].args[0].kind == "name" and gravity_nodes[0].args[0].name == "world",
            "PHYSICS", "Zero gravity must be explicitly world-expressed.", entry.scene)
    require(not model.joints and not model.actions and not model.events, "MOTION", "No joints, actions or events are admitted.", entry.scene)
    require(len(model.objects) == 14 and len(model.follows) == 12 and not compiler.collections,
            "SHAPE", "Exactly fourteen ordinary occurrences and twelve follows are required.", entry.scene)
    require(len(model.sites) == 14 and all(p.endswith(".origin") for p in model.sites),
            "SHAPE", "Only implicit object origins are admitted.", entry.scene)
    finish()
    classes = {n.key: n for n in module.classes}
    tray_class, box_class = classes["tray"], classes["box"]
    require(tray_class.visibility == "public" and box_class.visibility == "private"
            and tray_class.base is None and box_class.base is None, "SHAPE", "Definition visibility or inheritance differs.", module)
    allowed = {"param", "derive", "assert", "assign", "part", "follow"}
    for cls in module.classes:
        require(all(n.kind in allowed for n in cls.members), "SHAPE", "Extra class member kind.", cls)
        for n in cls.members:
            if n.kind == "assign":
                require(len(n.path) == 1 and n.path[0].value not in {"placement", "velocity", "omega"},
                        "RELATIONSHIP", "Class cannot author placement or motion state.", n)
    params = {n.key: n for n in tray_class.members if n.kind == "param"}
    require(len(params) == 7 and set(params) == set(PARAMETER_KEYS)
            and all(n.visibility == "public" for n in params.values()), "SHAPE", "Seven public keyed length parameters required.", tray_class)
    box_params = [n for n in box_class.members if n.kind == "param"]
    require(len(box_params) == 1 and box_params[0].key == "extent" and box_params[0].visibility == "public",
            "SHAPE", "Box helper requires one public extent parameter.", box_class)
    require(all(n.kind in {"param", "assign", "assert"} for n in box_class.members), "SHAPE", "Box helper has extra structure.", box_class)
    parts = [n for n in tray_class.members if n.kind == "part"]
    follows = [n for n in tray_class.members if n.kind == "follow"]
    require(len(parts) == 6 and {n.key for n in parts} == set(PARTS), "IDENTITY", "Tray part identity inventory differs.", tray_class)
    require(len(follows) == 6 and {n.key for n in follows} == {"follow-" + k for k in PARTS},
            "RELATIONSHIP", "Tray fixed-follow inventory differs.", tray_class)
    finish()
    extent_name = box_params[0].name
    geometry_defaults = [n.value for n in box_class.members if n.kind == "assign" and _path_names(n) == ("geometry",)]
    geometry = geometry_defaults[0] if len(geometry_defaults) == 1 else None
    require(geometry is not None and _call(geometry, "box", 1) and geometry.args[0].kind == "member"
            and geometry.args[0].name == extent_name and geometry.args[0].target.kind == "name"
            and geometry.args[0].target.name == "self", "SHAPE", "Helper geometry must be box(self.extent).", box_class)
    for node in parts:
        require(all(len(n.path) == 1 and n.path[0].value in {extent_name, "role", "appearance", "physical", "motion", "collision"}
                    for n in node.assignments), "RELATIONSHIP", "Part initializer has unsupported override or second pose authority.", node)
    for node in follows:
        a = {_path_names(n): n for n in node.assignments}
        require(set(a) == {("parent",), ("child",), ("offset",)}, "RELATIONSHIP", "Follow fields differ.", node)
        if ("offset",) in a:
            require(_literal_rotation(a[("offset",)].value, root=False), "ROTATION", "Follow offset requires direct identity quat literal.", node)
    ids = {}
    for obj in model.objects.values():
        sid = "/".join(obj.element_id)
        require(obj.element_id not in ids, "IDENTITY", "Duplicate occurrence identity.", obj.span, sid)
        ids[obj.element_id] = obj
        require(obj.physical == {"kind": "no_body"} and obj.mass == 0 and model.owned_mass(obj.path) == 0
                and obj.collision == "disabled", "PHYSICS", "No represented matter or collision is admitted.", obj.span, sid)
        require(obj.motion == "prescribed" and obj.velocity == (0., 0., 0.) and obj.omega == (0., 0., 0.),
                "MOTION", "No motion state or dynamic authority is admitted.", obj.span, sid)
    expected_ids = {("equipment-tray", "pair", side) + suffix for side in ("left", "right")
                    for suffix in [(), *((k,) for k in PARTS)]}
    require(set(ids) == expected_ids, "IDENTITY", "Occurrence inventory differs.", entry.scene)
    finish()
    trays = []
    for side in ("left", "right"):
        root = ids[("equipment-tray", "pair", side)]
        sid = list(root.element_id)
        name = "/".join(sid)
        require(tuple(compiler.definition_id(root.class_name)) == ("package", "ontokin.static-tray", "static-tray", "definitions", "tray"),
                "IDENTITY", "Root does not instantiate the shared tray definition.", root.span, name)
        require(root.owner is None and root.role == "tray-root" and root.geometry == {"kind": "empty"},
                "SHAPE", "Root ownership, role or empty geometry differs.", root.span, name)
        allowed_names = {n.name for n in params.values()} | {"placement"}
        require(all(len(n.path) == 1 and n.path[0].value in allowed_names for n in root.span.assignments),
                "SHAPE", "Entry may only override root inputs and root placement.", root.span, name)
        placement = [n.value for n in root.span.assignments if _path_names(n) == ("placement",)]
        require(len(placement) == 1 and _literal_rotation(placement[0], root=True), "ROTATION", "Root requires catalog literal quat in world pose.", root.span, name)
        require(root.placement_authored and root.placement.frame == "world" and root.placement.rotation in ROTATIONS,
                "ROTATION", "Resolved root pose is outside the finite catalog.", root.span, name)
        values = []
        for key in PARAMETER_KEYS:
            value = root.properties[params[key].name]
            require(value.type.kind == "Quantity" and value.type.dimension == LENGTH, "UNITS", "Root parameter is not Length.", params[key], name)
            values.append(value.value)
        root_record = {"id": sid, "owner_id": sid[:2], "role": root.role, "geometry": root.geometry["kind"],
                       "physical": root.physical["kind"], "motion": root.motion, "collision": root.collision,
                       "root_pose": {"reference": root.placement.frame, "translation_m": [bits(v) for v in root.placement.position],
                                     "rotation_wxyz": [bits(v) for v in root.placement.rotation]},
                       "parameters": {"payload_size_m": [bits(v) for v in values[:3]],
                                      **dict(zip(("horizontal_clearance_m", "wall_thickness_m", "base_thickness_m", "headroom_m"), [bits(v) for v in values[3:]]))}, "parts": []}
        for key in PARTS:
            child = ids[tuple(sid + [key])]
            child_name = "/".join(child.element_id)
            require(child.owner == root.path and not child.placement_authored, "RELATIONSHIP", "Part owner or pose authority differs.", child.span, child_name)
            require(tuple(compiler.definition_id(child.class_name)) == ("package", "ontokin.static-tray", "static-tray", "definitions", "box"),
                    "IDENTITY", "Part definition differs from box helper.", child.span, child_name)
            expected_role = "payload-proxy" if key == "payload" else key
            require(child.role == expected_role, "IDENTITY", "Part role differs.", child.span, child_name)
            require(child.appearance == ((.75, .5, .25, 1.) if key == "payload" else (.25, .5, .75, 1.)),
                    "MATERIAL", "Fixed source color differs.", child.span, child_name)
            incoming = [f for f in model.follows.values() if f.child == child.path]
            require(len(incoming) == 1, "RELATIONSHIP", "Part requires exactly one incoming follow.", child.span, child_name)
            require(child.geometry.get("kind") == "box" and set(child.geometry) == {"kind", "size"},
                    "SHAPE", "Actual compiled part must be a box.", child.span, child_name)
            if len(incoming) != 1 or child.geometry.get("kind") != "box":
                continue
            follow = incoming[0]
            require(follow.element_id == tuple(sid + ["follow-" + key]) and follow.parent == root.path + ".frame"
                    and follow.offset.frame == root.path + ".frame" and follow.offset.rotation == IDENTITY,
                    "RELATIONSHIP", "Follow identity, parent frame or offset rotation differs.", follow.span, child_name)
            root_record["parts"].append({"id": list(child.element_id), "owner_id": list(model.objects[child.owner].element_id),
                "key": key, "role": child.role, "geometry": {"type": "box", "size_m": [bits(v) for v in child.geometry["size"]]},
                "physical": child.physical["kind"], "motion": child.motion, "collision": child.collision,
                "material": "payload" if key == "payload" else "tray",
                "following": {"id": list(follow.element_id), "parent_id": sid,
                              "offset": {"reference": "parent-frame", "translation_m": [bits(v) for v in follow.offset.position],
                                         "rotation_wxyz": [bits(v) for v in follow.offset.rotation]}}})
        require(not any(f.child == root.path for f in model.follows.values()), "RELATIONSHIP", "Root cannot have incoming follow.", root.span, name)
        trays.append(root_record)
    finish()
    record = {**CONSTANTS, "trays": trays}
    try:
        data = canonical_bytes(record)
    except TrayError as error:
        error.candidate = bundle.program_revision
        for finding in error.findings:
            obj = ids.get(tuple(finding.get("semantic_id", "").split("/")))
            if obj is not None:
                node = obj.span
                source = compiler.source_registry[node.source_id]
                finding["source"] = {"source_id": node.source_id, "source_revision": source.revision,
                                     "filename": source.filename, "start_byte": node.start, "end_byte": node.end}
        raise
    provenance = {"candidate_identity": bundle.program_revision, "program_revision": bundle.program_revision,
                  "bundle_manifest": bundle.manifest(), "bundle_payload": bundle.to_payload(),
                  "source_units": [{"source_id": unit.source_id, "filename": unit.filename,
                                    "source_revision": unit.revision, "package_id": unit.package_id,
                                    "version": unit.version, "size_bytes": len(unit.raw)} for unit in bundle.units],
                  "definition_identities": [["package", "ontokin.static-tray", "static-tray", "definitions", k] for k in ("tray", "box")],
                  "definition_source_revision": bundle.modules[0].revision,
                  "construction_budget": compiler.budget.report()}
    return record, data, provenance


class _PythonGuard:
    """Finite source execution surface; this is not a general Python sandbox.

    Every exposed reduction/materialization iterates under the same source work
    counter and deadline. Large integer work, collection sizes and text values
    are bounded before invoking a C-level operation. The original core compiler
    and its numerical/operation accounting are not modified.
    """
    def __init__(self,check):
        self.check=check
        self.operations=0
        self.max_items=4096
        self.max_bits=32768
        self.max_text=32768

    def charge(self,count=1):
        self.operations+=count
        if self.operations>100000:
            raise TrayError("RESOURCE","Direct Python exceeded 100000 charged source operations.")
        self.check()

    def value(self,value,seen=None,depth=0):
        self.charge()
        if depth>32:
            raise TrayError("RESOURCE","Direct Python value nesting exceeds 32 levels.")
        if value is None or type(value) is bool:
            return value
        if type(value) is int:
            size=value.bit_length()
            if size>self.max_bits:
                raise TrayError("RESOURCE","Direct Python integer exceeds 32768 bits.")
            self.charge((size+63)//64)
        elif type(value) is float:
            f64(value)
        elif type(value) is Fraction:
            size=max(value.numerator.bit_length(),value.denominator.bit_length())
            if size>self.max_bits:
                raise TrayError("RESOURCE","Direct Python rational exceeds 32768-bit operands.")
            self.charge((size+63)//64)
        elif type(value) in (str,bytes):
            if len(value)>self.max_text:
                raise TrayError("RESOURCE","Direct Python text/bytes exceeds 32768 elements.")
            self.charge((len(value)+63)//64)
        elif type(value) is range:
            try:
                size=len(value)
            except OverflowError as exc:
                raise TrayError("RESOURCE","Direct Python range exceeds its finite allowance.") from exc
            if size>self.max_items:
                raise TrayError("RESOURCE","Direct Python iterable exceeds 4096 elements.")
            for item in (value.start,value.stop,value.step):
                self.value(item,depth=depth+1)
        elif type(value) in (list,tuple,dict):
            if len(value)>self.max_items:
                raise TrayError("RESOURCE","Direct Python container exceeds 4096 elements.")
            seen=set() if seen is None else seen
            if id(value) in seen:
                raise TrayError("SHAPE","Cyclic direct Python values are not admitted.")
            seen.add(id(value))
            for item in (value.items() if type(value) is dict else value):
                if type(value) is dict:
                    self.value(item[0],seen,depth+1)
                    self.value(item[1],seen,depth+1)
                else:
                    self.value(item,seen,depth+1)
            seen.remove(id(value))
        else:
            raise TrayError("SHAPE","Unadmitted direct Python value type.")
        return value

    def numeric(self,value):
        if type(value) not in (int,float,Fraction):
            raise TrayError("SHAPE","Only finite numeric arithmetic is admitted.")
        return self.value(value)

    def iterate(self,value):
        if type(value) not in (list,tuple,dict,str,bytes,range,types.GeneratorType):
            raise TrayError("SHAPE","Unadmitted direct Python iterable.")
        if type(value) is not types.GeneratorType:
            self.value(value)
        for index,item in enumerate(value):
            self.charge()
            if index>=self.max_items:
                raise TrayError("RESOURCE","Direct Python iterable exceeds 4096 elements.")
            yield self.value(item)

    def binary(self,operator,a,b):
        self.charge()
        if operator=="Add" and type(a) is type(b) and type(a) in (list,tuple,str,bytes):
            self.value(a); self.value(b)
            limit=self.max_text if type(a) in (str,bytes) else self.max_items
            if len(a)+len(b)>limit:
                raise TrayError("RESOURCE","Sequence addition exceeds its finite allowance.")
            return self.value(a+b)
        self.numeric(a); self.numeric(b)
        # These operations cannot hide exponentiation or sequence repetition.
        ar=Fraction(a); br=Fraction(b)
        cost=max(ar.numerator.bit_length(),ar.denominator.bit_length())+max(br.numerator.bit_length(),br.denominator.bit_length())
        if cost>self.max_bits:
            raise TrayError("RESOURCE","Numeric intermediate exceeds the finite bit allowance.")
        self.charge(max(1,(cost+63)//64))
        operations={"Add":lambda:a+b,"Sub":lambda:a-b,"Mult":lambda:a*b,
                    "Div":lambda:a/b,"FloorDiv":lambda:a//b,"Mod":lambda:a%b}
        if operator not in operations:
            raise TrayError("SHAPE","Unsupported direct Python binary operator.")
        return self.value(operations[operator]())

    def unary(self,operator,value):
        self.charge()
        if operator=="Not":
            self.value(value)
            return not value
        self.numeric(value)
        return self.value(value if operator=="UAdd" else -value)

    def comparison(self,operator,a,b):
        self.value(a); self.value(b)
        operations={"Eq":lambda:a==b,"NotEq":lambda:a!=b,"Lt":lambda:a<b,
                    "LtE":lambda:a<=b,"Gt":lambda:a>b,"GtE":lambda:a>=b,
                    "In":lambda:a in b,"NotIn":lambda:a not in b,
                    "Is":lambda:a is b,"IsNot":lambda:a is not b}
        if operator not in operations:
            raise TrayError("SHAPE","Unsupported direct Python comparison.")
        return operations[operator]()

    def fraction(self,*args):
        if not 1<=len(args)<=2:
            raise TrayError("SHAPE","Fraction requires one or two finite numeric inputs.")
        for value in args:
            self.numeric(value)
        return self.value(Fraction(*args))

    def pack(self,fmt,*args):
        from struct import pack
        if fmt!=">d" or len(args)!=1:
            raise TrayError("SHAPE","Only one big-endian binary64 pack is admitted.")
        self.numeric(args[0])
        return pack(fmt,f64(args[0]))

    def setitem(self,value,obj,key):
        # Argument order preserves Python assignment evaluation: RHS, object,
        # then key. Slice mutation is excluded by the source AST admission.
        self.value(value); self.value(obj); self.value(key)
        if type(obj) is list:
            if type(key) is not int:
                raise TrayError("SHAPE","List assignment requires one integer index.")
        elif type(obj) is dict:
            if key not in obj and len(obj)>=self.max_items:
                raise TrayError("RESOURCE","Dictionary assignment exceeds its finite allowance.")
        else:
            raise TrayError("SHAPE","Only bounded list/dictionary item assignment is admitted.")
        obj[key]=value
        self.value(obj)

    def attribute(self,obj,name):
        self.value(obj)
        if type(obj) is Fraction and name in {"numerator","denominator"}:
            return self.value(getattr(obj,name))
        def method(*args,**kwargs):
            self.charge()
            if kwargs:
                raise TrayError("SHAPE","Method keyword arguments are outside this finite surface.")
            for arg in args:
                self.value(arg)
            if type(obj) is bytes and name=="hex" and not args:
                if len(obj)*2>self.max_text:
                    raise TrayError("RESOURCE","Hex output exceeds its finite allowance.")
                return self.value(obj.hex())
            if type(obj) is list and name=="append" and len(args)==1:
                if len(obj)>=self.max_items:
                    raise TrayError("RESOURCE","List append exceeds its finite allowance.")
                obj.append(args[0]); self.value(obj)
                return None
            if type(obj) in (list,dict) and name=="copy" and not args:
                return self.value(obj.copy())
            if type(obj) is dict:
                if name=="get" and 1<=len(args)<=2:
                    return self.value(obj.get(*args))
                if name in {"items","keys","values"} and not args:
                    return self.value(list(getattr(obj,name)()))
            raise TrayError("SHAPE","Method is outside the admitted finite Python surface.")
        if ((type(obj) is bytes and name=="hex") or
            (type(obj) is list and name in {"append","copy"}) or
            (type(obj) is dict and name in {"get","copy","items","keys","values"})):
            return method
        raise TrayError("SHAPE","Attribute is outside the admitted finite Python surface.")

    def builtins(self):
        def materialize(value=(),kind=list):
            return self.value(kind(self.iterate(value)))
        def dictionary(value=(),**kwargs):
            result={}
            if type(value) is dict:
                self.value(value)
                result.update(value)
            else:
                for pair in self.iterate(value):
                    self.charge()
                    if type(pair) not in (list,tuple) or len(pair)!=2:
                        raise TrayError("SHAPE","Dictionary input requires bounded key/value pairs.")
                    result[pair[0]]=pair[1]
            result.update(kwargs)
            return self.value(result)
        def conversion(kind,*args):
            self.charge()
            for value in args:
                self.value(value)
            return self.value(kind(*args))
        def source_range(*args):
            for value in args:
                if type(value) is not int:
                    raise TrayError("SHAPE","Range inputs must be bounded integers.")
                self.value(value)
            return self.value(range(*args))
        def reduction(name,value,start=0):
            result=start
            for item in self.iterate(value):
                if name=="sum":
                    result=self.binary("Add",result,item)
                elif name=="all" and not item:
                    return False
                elif name=="any" and item:
                    return True
            return result if name=="sum" else name=="all"
        def enumerate_values(value,start=0):
            self.numeric(start)
            if type(start) is not int:
                raise TrayError("SHAPE","Enumeration start must be an integer.")
            return self.value([(start+i,item) for i,item in enumerate(self.iterate(value))])
        def zip_values(*values):
            sequences=[list(self.iterate(v)) for v in values]
            return self.value([tuple(row) for row in zip(*sequences)])
        def extrema(name,*args,key=None):
            sequence=list(self.iterate(args[0] if len(args)==1 else args))
            if not sequence:
                raise ValueError("Empty extrema input")
            result=sequence[0]
            for item in sequence[1:]:
                self.charge()
                if self.comparison("Lt" if name=="min" else "Gt",key(item) if key else item,key(result) if key else result):
                    result=item
            return result
        def ordered(value,*,key=None,reverse=False):
            if type(reverse) is not bool:
                raise TrayError("SHAPE","Sorting reverse must be boolean.")
            values=[(self.value(key(v) if key else v),v) for v in self.iterate(value)]
            width=1
            while width<len(values):
                result=[]
                for begin in range(0,len(values),2*width):
                    left,right=values[begin:begin+width],values[begin+width:begin+2*width]
                    i=j=0
                    while i<len(left) and j<len(right):
                        self.charge()
                        take_right=self.comparison("Gt" if reverse else "Lt",right[j][0],left[i][0])
                        if take_right:
                            result.append(right[j]); j+=1
                        else:
                            result.append(left[i]); i+=1
                    result.extend(left[i:]); result.extend(right[j:])
                values=result; width*=2
            return self.value([v for _,v in values])
        return {"float":lambda *a:conversion(float,*a),"int":lambda *a:conversion(int,*a),
                "str":lambda *a:conversion(str,*a),"dict":dictionary,"list":lambda value=():materialize(value,list),
                "tuple":lambda value=():materialize(value,tuple),
                "len":lambda v:len(self.value(v)),"range":source_range,"enumerate":enumerate_values,
                "zip":zip_values,"sorted":ordered,"min":lambda *a,**k:extrema("min",*a,**k),
                "max":lambda *a,**k:extrema("max",*a,**k),"abs":lambda v:self.value(abs(self.numeric(v))),
                "sum":lambda v,start=0:reduction("sum",v,start),
                "all":lambda v:reduction("all",v),"any":lambda v:reduction("any",v)}


class _GuardPythonAST(ast.NodeTransformer):
    @staticmethod
    def call(name,args,node):
        return ast.copy_location(ast.Call(func=ast.Name(id=name,ctx=ast.Load()),args=args,keywords=[]),node)

    def visit_BinOp(self,node):
        self.generic_visit(node)
        return self.call("__tray_binary__",[ast.Constant(type(node.op).__name__),node.left,node.right],node)

    def visit_UnaryOp(self,node):
        self.generic_visit(node)
        return self.call("__tray_unary__",[ast.Constant(type(node.op).__name__),node.operand],node)

    def visit_Compare(self,node):
        self.generic_visit(node)
        return self.call("__tray_compare__",[ast.Constant(type(node.ops[0]).__name__),node.left,node.comparators[0]],node)

    def visit_Attribute(self,node):
        self.generic_visit(node)
        return self.call("__tray_attribute__",[node.value,ast.Constant(node.attr)],node)

    def visit_Assign(self,node):
        self.generic_visit(node)
        if len(node.targets)==1 and isinstance(node.targets[0],ast.Subscript):
            target=node.targets[0]
            call=self.call("__tray_setitem__",[node.value,target.value,target.slice],node)
            return ast.copy_location(ast.Expr(value=call),node)
        return node

    def visit_For(self,node):
        self.generic_visit(node)
        node.iter=self.call("__tray_iter__",[node.iter],node.iter)
        return node

    def visit_comprehension(self,node):
        self.generic_visit(node)
        node.iter=self.call("__tray_iter__",[node.iter],node.iter)
        return node

    def container(self,node):
        self.generic_visit(node)
        if not hasattr(node,"ctx") or isinstance(node.ctx,ast.Load):
            return self.call("__tray_value__",[node],node)
        return node

    visit_List=container
    visit_Tuple=container
    visit_Dict=container
    visit_ListComp=container
    visit_DictComp=container


def _lower_python(files, manifest, check):
    # This is a finite two-file Python harness, not a general Python sandbox.
    # Authored files can only access their closed source module and fixed stdlib
    # names; no ambient import path, filesystem, network, or dynamic code loader.
    guard = _PythonGuard(check)
    safe = guard.builtins()
    trees = {}
    for name, data in files.items():
        try:
            tree = ast.parse(data, filename=name)
        except SyntaxError as exc:
            raise TrayError("SHAPE", "Direct Python source has invalid syntax.", stage="source", pointer=name,
                            details={"line": exc.lineno, "column": exc.offset, "reason": exc.msg}) from exc
        item_assignments={id(n.targets[0]) for n in ast.walk(tree)
                          if isinstance(n,ast.Assign) and len(n.targets)==1
                          and isinstance(n.targets[0],ast.Subscript)
                          and not isinstance(n.targets[0].slice,ast.Slice)}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ClassDef, ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith, ast.Try, ast.TryStar, ast.AugAssign, ast.JoinedStr, ast.FormattedValue, ast.Set, ast.SetComp, ast.Delete, ast.Starred)):
                raise TrayError("SHAPE", "Unsupported Python source construct.", pointer=name)
            if isinstance(node,ast.Subscript) and isinstance(node.ctx,ast.Store) and id(node) not in item_assignments:
                raise TrayError("SHAPE","Only a single guarded nonslice item-assignment target is admitted.",pointer=name)
            if isinstance(node,ast.BinOp) and not isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod)):
                raise TrayError("SHAPE","Exponentiation and bit operations are outside the finite Python surface.",pointer=name)
            if isinstance(node,ast.UnaryOp) and not isinstance(node.op,(ast.UAdd,ast.USub,ast.Not)):
                raise TrayError("SHAPE","Unsupported finite Python unary operation.",pointer=name)
            if isinstance(node,ast.Compare) and len(node.ops)!=1:
                raise TrayError("SHAPE","Chained comparisons are outside this finite Python surface.",pointer=name)
            if isinstance(node,ast.Attribute) and not isinstance(node.ctx,ast.Load):
                raise TrayError("SHAPE","Attribute writes are outside the finite Python surface.",pointer=name)
            if isinstance(node,ast.FunctionDef) and node.decorator_list:
                raise TrayError("SHAPE","Decorators are outside the finite Python surface.",pointer=name)
            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                raise TrayError("SHAPE", "Private Python object introspection is not admitted.", pointer=name)
            if isinstance(node, ast.Name) and node.id.startswith("__"):
                raise TrayError("SHAPE", "Dynamic Python infrastructure names are not admitted.", pointer=name)
            if isinstance(node, ast.ImportFrom):
                valid = ((name == "main.py" and node.module == "tray" and [(x.name, x.asname) for x in node.names] == [("make_tray", None)])
                         or (name == "tray.py" and node.module == "fractions" and [(x.name, x.asname) for x in node.names] == [("Fraction", None)])
                         or (name == "tray.py" and node.module == "struct" and [(x.name, x.asname) for x in node.names] == [("pack", None)]))
                if node.level or not valid:
                    raise TrayError("CLOSURE", "Python import is outside the exact closed module set.", pointer=name)
        trees[name] = ast.fix_missing_locations(_GuardPythonAST().visit(tree))
    if sum(isinstance(n,ast.FunctionDef) and n.name=="make_tray" for n in ast.walk(trees["tray.py"]))!=1:
        raise TrayError("SHAPE","Exactly one reusable make_tray definition is required.")
    modules = {"fractions": types.SimpleNamespace(Fraction=guard.fraction), "struct": types.SimpleNamespace(pack=guard.pack)}
    calls = []
    def importer(name, globals=None, locals=None, fromlist=(), level=0):
        if level or name not in modules:
            raise TrayError("CLOSURE", "Ambient module imports are forbidden.")
        return modules[name]
    safe["__import__"] = importer
    operation_count = 0
    opcode_count = 0
    helper_call_count = 0
    def trace(frame, event, arg):
        nonlocal operation_count, opcode_count, helper_call_count
        if frame.f_code.co_filename in {"main.py", "tray.py"}:
            frame.f_trace_opcodes = True
            # CPython can omit opcode notifications when instrumentation was
            # enabled after compilation. Every source event remains charged;
            # line/call/return events cannot be excluded from the deadline.
            operation_count += 1
            opcode_count += event == "opcode"
            guard.charge()
            if frame.f_code.co_filename=="tray.py" and frame.f_code.co_name=="make_tray" and event=="call":
                helper_call_count+=1
                if helper_call_count>2:
                    raise TrayError("SHAPE","Reusable helper may execute exactly twice, including internal calls.")
        return trace
    previous = sys.gettrace()
    try:
        sys.settrace(trace)
        infrastructure={"__builtins__":safe,"__tray_binary__":guard.binary,
                        "__tray_unary__":guard.unary,"__tray_compare__":guard.comparison,
                        "__tray_attribute__":guard.attribute,"__tray_iter__":guard.iterate,
                        "__tray_value__":guard.value,"__tray_setitem__":guard.setitem}
        helper_env = dict(infrastructure)
        exec(compile(trees["tray.py"], "tray.py", "exec"), helper_env)
        function = helper_env.get("make_tray")
        if not isinstance(function, types.FunctionType):
            raise TrayError("SHAPE", "Reusable helper must define make_tray.")
        def called(side, values):
            check()
            if len(calls) >= 2:
                raise TrayError("SHAPE", "Reusable helper may be called exactly twice.")
            result = guard.value(function(side, values))
            calls.append({"side": side, "result": json_bytes(result)})
            return result
        modules["tray"] = types.SimpleNamespace(make_tray=called)
        entry_env = dict(infrastructure)
        exec(compile(trees["main.py"], "main.py", "exec"), entry_env)
        record = entry_env.get("record")
    finally:
        sys.settrace(previous)
    check()
    data = canonical_bytes(guard.value(record))
    if helper_call_count!=2 or [x["side"] for x in calls] != ["left", "right"] or [x["result"] for x in calls] != [json_bytes(t) for t in record["trays"]]:
        raise TrayError("BINDING", "Both delivered tray records must be the two actual reusable helper results.")
    source_identity = "sha256:" + hashlib.sha256(b"ontokin.static-tray.python-sources/0.1.0\0" + json_bytes(manifest)).hexdigest()
    return record, data, {"candidate_identity": source_identity, "python_source_identity": source_identity,
                          "source_manifest": manifest, "helper_calls": [x["side"] for x in calls],
                          "actual_helper_calls":helper_call_count,"source_operations":guard.operations,
                          "source_trace_events": operation_count, "source_opcode_events": opcode_count,
                          "source_counter": "Each source trace event plus guarded builtin iteration, bounded value traversal and numeric limb work is charged",
                          "python_surface":"ontokin.static-tray.python-finite/0.1.0",
                          "python_value_limits":{"items":4096,"bits":32768,"text_elements":32768,"nesting":32}}


def lower_source(route, manifest_path, profile, *, check=None):
    start = time.monotonic()
    if profile != PROFILE:
        raise TrayError("PROFILE", "An exact explicit mapping selector is required.", stage="selector")
    if route not in {"ontokin", "direct-python"}:
        raise TrayError("PROFILE", "Unsupported route.", stage="selector")
    external_check = check
    def deadline():
        if external_check:
            external_check()
        if (time.monotonic() - start) * 1000 > 30000:
            raise TrayError("RESOURCE", "Source preparation exceeded 30000 ms.", stage="source")
    deadline()
    files, manifest = _read_sources(route, manifest_path, deadline)
    if route == "ontokin":
        record, data, provenance = _lower_ontokin(files, deadline)
    else:
        try:
            record, data, provenance = _lower_python(files, manifest, deadline)
        except TrayError as error:
            error.candidate = "sha256:" + hashlib.sha256(b"ontokin.static-tray.python-sources/0.1.0\0" + json_bytes(manifest)).hexdigest()
            raise
        except (ArithmeticError, ValueError, TypeError, KeyError, IndexError, NameError, RecursionError, AssertionError) as error:
            candidate = "sha256:" + hashlib.sha256(b"ontokin.static-tray.python-sources/0.1.0\0" + json_bytes(manifest)).hexdigest()
            raise TrayError("NUMERIC" if isinstance(error, ArithmeticError) else "SHAPE",
                            "Direct source execution failed.", stage="source", candidate=candidate,
                            details={"exception": type(error).__name__, "reason": str(error)[:1024]}) from error
    deadline()
    provenance.update({"schema_version": "ontokin.static-tray.provenance/0.1.0", "profile": PROFILE,
                       "contract": CONTRACT, "route": route, "canonical_record_identity": record_identity(data),
                       "canonical_record_sha256": hashlib.sha256(data).hexdigest(),
                       "source_manifest_file": manifest, "source_elapsed_ms": (time.monotonic() - start) * 1000,
                       "source_budget": {"max_operations": 100000, "max_elapsed_ms": 30000}})
    return Lowered(record, data, provenance, files)
