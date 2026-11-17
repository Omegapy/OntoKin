#!/usr/bin/env python3
"""Finite independent source/GLB follow observations; no execution authority."""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import types

SCHEMA = "ontokin.c258.follow-observation/0.1"
DEPENDENCY_SHA = "c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1"
DEPENDENCY_BYTES = 35942
MAX_FOLLOWS = 128
MAX_STEPS = 4096
MAX_CALLS = 64
EPSILON = Fraction(1, 10**12)
POLICY = {"name": "C258 finite component comparison", "componentUlps": 8,
          "sourceZero": "exact", "quaternionSign": "one common sign",
          "exporterErrorBoundClaimed": False,
          "sourceProjection": "exact squared-midpoint proof; Decimal seed only",
          "translation": "exact canonical binary64 value", "rawArtifactNormalization": False}
NONCLAIMS = ["Complete source/glTF validity and complete C255 semantics remain unqualified",
             "Artifact follow-definition/source-span authority is absent",
             "Ownership and transform hierarchy do not supply follow fields",
             "Joint-wide authority, body/motion, geometry and world-motion consistency are unqualified",
             "No accepted revision, rebuild, native/model trial or comparative authority"]
PREDEFINED = set(("self world static prescribed dynamic disabled Object Int Real Bool String Quantity "
    "Length Area Volume Mass Time Angle Speed Acceleration AngularSpeed Force Torque Density Inertia "
    "Vec3 Vector3 Point3 Rotation Pose Range Color Geometry BodyModel MotionMode CollisionMode "
    "Ref FrameRef SiteRef JointRef Action Keyed real abs min max near sqrt sin cos vec3 vector "
    "point quat axis_angle pose range rgba empty sphere box no_body sphere_body move spin tween len").split())
RESERVED = set(("ontokin module profile requires class extends public private param derive override method "
    "fn let return part parts site joint follow scene object action at sequence start pause resume stop "
    "release using incoming assert if then else and or not true false import from version digest for in keyed").split())
KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
NUMERAL = re.compile(r"(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?\Z")
_DEPENDENCY = None


class Fault(ValueError):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


def require(condition, code, detail):
    if not condition:
        raise Fault(code, detail)


def dependency():
    global _DEPENDENCY
    if _DEPENDENCY is None:
        path = Path(__file__).resolve().parent.parent / "localized-repair-c257/ownership.py"
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == DEPENDENCY_BYTES,
                "DEPENDENCY", "frozen C257 file size/path")
        with path.open("rb") as handle:
            raw = handle.read(DEPENDENCY_BYTES+1)
        require(len(raw) == DEPENDENCY_BYTES and hashlib.sha256(raw).hexdigest() == DEPENDENCY_SHA,
                "DEPENDENCY", "frozen C257 bytes")
        module = types.ModuleType("_c258_pinned_c257")
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        exec(compile(raw, str(path), "exec"), module.__dict__)
        _DEPENDENCY = module
    return _DEPENDENCY


def public(call):
    try:
        return call()
    except Fault:
        raise
    except OSError as exc:
        raise Fault("IO", type(exc).__name__) from exc
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError,
            RecursionError, struct.error) as exc:
        if hasattr(exc, "code"):
            raise Fault("C257_"+exc.code, exc.detail) from exc
        raise Fault("STRUCTURE", type(exc).__name__) from exc


def numeric(value, where):
    require(type(value) in (int, float), "NUMBER_TYPE", where)
    value = float(value)
    require(math.isfinite(value), "NONFINITE", where)
    return 0.0 if value == 0 else value


def canonical_literal(token, unit_scale=0, dimensioned=False):
    text = token.value
    require(token.kind == "number" and len(text) <= 64, "NUMERIC_LEXEME", "bounded numeric token")
    match = NUMERAL.fullmatch(text)
    require(match is not None, "NUMERIC_LEXEME", "adopted decimal spelling")
    integer, fractional, exponent_text = match.groups()
    exponent = int(exponent_text or "0")
    require(-400 <= exponent <= 400, "NUMERIC_EXPONENT", "explicit exponent before allocation")
    digits = integer+(fractional or "")
    nonzero = digits.lstrip("0")
    adjusted = len(nonzero)-1+exponent-len(fractional or "")-unit_scale if nonzero else 0
    require(not nonzero or -324 <= adjusted <= 308, "NUMERIC_EXPONENT", "scaled adjusted exponent")
    shift = exponent-len(fractional or "")-unit_scale
    # The preceding checks bound both powers, regardless of the apparent token length.
    rational = Fraction(int(digits) * 10**max(shift, 0), 10**max(-shift, 0))
    if not dimensioned and fractional is None and exponent_text is None:
        require(int(digits) <= 2**63-1, "INTEGER_RANGE", "literal Int")
        value = float(rational)
        require(Fraction.from_float(value) == rational, "INTEGER_WIDENING", "exact Int to Real conversion")
    else:
        value = float(rational)
    require(math.isfinite(value), "NONFINITE", "canonical scalar overflow")
    return 0.0 if value == 0 else value


def quaternion_norm(values):
    require(type(values) is list and len(values) == 4, "QUATERNION", "four WXYZ values")
    canonical = [numeric(x, "quaternion") for x in values]
    squared = sum((Fraction.from_float(x)**2 for x in canonical), Fraction())
    require((1-EPSILON)**2 <= squared <= (1+EPSILON)**2,
            "QUATERNION_NORM", "adopted finite near-unit constructor condition")
    return canonical, squared


def even_float(value):
    return struct.unpack(">Q", struct.pack(">d", value))[0] % 2 == 0


def proven_projection(component, squared):
    """Prove rounding of abs(component)/sqrt(squared); Decimal is only a seed."""
    if component == 0:
        return 0.0
    ratio_squared = Fraction.from_float(abs(component))**2 / squared
    with localcontext() as context:
        context.prec = 100
        norm = (Decimal(squared.numerator)/Decimal(squared.denominator)).sqrt()
        seed = float(Decimal.from_float(abs(component))/norm)
    candidates = [seed, math.nextafter(seed, 0.0), math.nextafter(seed, math.inf)]
    for value in candidates:
        if not math.isfinite(value) or not 0 <= value <= 1:
            continue
        current = Fraction.from_float(value)
        upper = (current+Fraction.from_float(math.nextafter(value, math.inf)))/2
        upper_ok = ratio_squared < upper**2 or (ratio_squared == upper**2 and even_float(value))
        if value == 0:
            lower_ok = True
        else:
            lower = (current+Fraction.from_float(math.nextafter(value, 0.0)))/2
            lower_ok = ratio_squared > lower**2 or (ratio_squared == lower**2 and even_float(value))
        if lower_ok and upper_ok:
            return math.copysign(value, component) if value else 0.0
    raise Fault("PROJECTION_UNPROVEN", "no verified candidate among seed and immediate neighbours")


def normalized_quaternion(values):
    canonical, squared = quaternion_norm(values)
    result = [proven_projection(x, squared) for x in canonical]
    sign = next(1 if x > 0 else -1 for x in result if x != 0)
    return [0.0 if x == 0 else sign*x for x in result]


def quaternion_agrees(actual, expected):
    actual, _ = quaternion_norm(actual)
    for sign in (1, -1):
        good = True
        for a, e in zip(actual, expected):
            if e == 0:
                good = good and a == 0
            else:
                difference = abs(Fraction.from_float(a)-sign*Fraction.from_float(e))
                good = good and difference <= 8*Fraction.from_float(math.ulp(abs(e)))
        if good:
            return True
    return False


def origin_key(origin):
    return origin["file"], origin["startByte"], origin["endByteExclusive"]


def check_name(name):
    require(name not in PREDEFINED and name not in RESERVED, "SHADOWING", name)


def check_key(key):
    require(KEY.fullmatch(key) is not None, "STABLE_KEY", key)


def frame(context=None):
    if context is None:
        return {"kind": "world", "objectId": None, "path": "world"}
    record = context["record"]
    return {"kind": "object-frame", "objectId": record["id"], "path": record["path"]+".frame"}


def value(kind, payload, origins):
    return {"type": kind, "value": payload, "origins": origins}


class Source:
    def __init__(self, files):
        self.d = dependency()
        self.files = files
        self.identity = self.d.observe_source_ownership(files)
        self.modules = {name: self.d.parse_module(raw, name) for name, raw in files.items()}
        self.classes, self.declarations, self.contexts = {}, {}, {}
        self.steps = self.calls = 0
        self.resolving, self.used_names, self.used_properties = set(), set(), {}
        self.current_child = None
        for module in self.modules.values():
            aliases = [x["alias"] for x in module["imports"]]
            names = list(module["classes"])+list(module["functions"])+aliases
            require(len(names) == len(set(names)), "NAMESPACE", "module aliases/definitions")
            for name in names:
                check_name(name)
            check_key(module["key"])
            for definition in module["classes"].values():
                check_key(definition["key"])
                self.classes[origin_key(definition["origin"])] = self.scan_class(definition)
            if module["scene"]:
                for declaration in module["scene"]["roots"]:
                    check_name(declaration["name"]); check_key(declaration["key"])
                    self.declarations[origin_key(declaration["declaration"])] = declaration
        for row in self.identity["records"]:
            for key in row["id"]:
                check_key(key)
            self.contexts[tuple(row["id"])] = {"record": row,
                "class": self.classes[origin_key(row["origin"]["definition"])],
                "decl": self.declarations[origin_key(row["origin"]["declaration"])], "cache": {}}

    def tick(self):
        self.steps += 1
        require(self.steps <= MAX_STEPS, "EXPRESSION_LIMIT", "finite observation budget")

    def scan_class(self, definition):
        d = self.d
        stream = d.Stream(definition["body"])
        parameters, follows, builtins, names, keys = {}, [], {}, set(), set()
        while not stream.done():
            start_index = stream.index
            start = stream.tokens[start_index]
            visibility = stream.pop().value if stream.peek() in ("public", "private") else None
            kind = stream.peek()
            if kind in ("part", "parts"):
                require(visibility is not None, "VISIBILITY", "part requires visibility")
                decl = d.occurrence_declaration(stream, visibility, start, set())
                header = d.Stream(stream.tokens[start_index:stream.index])
                header.pop(); header.pop(); header.name(); header.key(); header.pop(":"); d.class_reference(header)
                if decl["generated"]:
                    header.pop("for"); header.pop("("); first = header.name(); header.pop(","); second = header.name()
                    check_name(first.value); check_name(second.value)
                    decl["binders"] = (first.value, second.value)
                self.declarations[origin_key(decl["declaration"])] = decl
                name, key = decl["name"], decl["key"]
            elif kind == "param":
                require(visibility is not None, "VISIBILITY", "parameter requires visibility")
                stream.pop(); name_token, key_token = stream.name(), stream.key(); stream.pop(":")
                rest = stream.statement(); groups = d.split_top(rest, "=")
                require(len(groups) == 2, "PARAMETER", name_token.value)
                name, key = name_token.value, key_token.value
                parameters[name] = {"type": "".join(t.value for t in groups[0]), "expression": groups[1],
                    "visibility": visibility, "origin": d.origin([start, rest[-1]], "typed parameter declaration"),
                    "typeOrigin": d.origin(groups[0], "parameter type"), "keyOrigin": d.origin([key_token], "parameter key")}
            elif kind in ("site", "joint", "follow", "method"):
                require(visibility is not None, "VISIBILITY", "class member requires visibility")
                stream.pop(); name_token, key_token = stream.name(), stream.key()
                header, body, opening, closing = stream.header_block()
                name, key = name_token.value, key_token.value
                if kind == "follow":
                    require(not header, "FOLLOW_HEADER", name)
                    fields = self.direct(d.assignments(body), "follow fields")
                    require(set(fields) == {"parent", "child", "offset"}, "FOLLOW_FIELDS", name)
                    follows.append({"name": name, "key": key, "fields": fields,
                        "origin": d.origin([start, closing], "follow declaration"),
                        "keyOrigin": d.origin([key_token], "follow key"),
                        "nameOrigin": d.origin([name_token], "follow name")})
            else:
                statement = stream.statement(); groups = d.split_top(statement, "=")
                require(len(groups) == 2 and len(groups[0]) == 1, "CLASS_FIELD", "simple declaration")
                field = groups[0][0].value
                require(field not in builtins, "DUPLICATE_FIELD", field)
                builtins[field] = {"rhs": groups[1], "origin": d.origin(statement, "class field")}
                continue
            check_name(name); check_key(key)
            require(name not in names and key not in keys, "NAMESPACE", definition["name"])
            names.add(name); keys.add(key)
        return {"definition": definition, "parameters": parameters, "follows": follows, "builtins": builtins}

    @staticmethod
    def direct(rows, where):
        result = {}
        for row in rows:
            require(len(row["lhs"]) == 1 and row["lhs"][0].kind == "id", "DIRECT_ASSIGNMENT", where)
            name = row["lhs"][0].value
            require(name not in result, "DUPLICATE_ASSIGNMENT", name)
            result[name] = row
        return result

    def initializers(self, context):
        result = {}
        for row in context["decl"]["assignments"]:
            if len(row["lhs"]) == 1:
                name = row["lhs"][0].value
                require(name not in result, "DUPLICATE_ASSIGNMENT", name)
                result[name] = row
        return result

    def owner(self, context):
        oid = context["record"]["ownerId"]
        return None if oid is None else self.contexts[tuple(oid)]

    def bindings(self, context):
        decl = context["decl"]
        if not decl["generated"]:
            return {}
        owner = self.owner(context)
        keyed = self.parameter(owner, decl["generated"]["parameter"], "Keyed<Vec3<Length>>")
        key = context["record"]["id"][-1]
        require(key in keyed["value"], "GENERATOR_KEY", key)
        key_name, value_name = decl["binders"]
        entry = keyed["value"][key]
        return {key_name: value("String", key, entry["origins"]),
                value_name: value("Vec3<Length>", entry["value"], keyed["origins"]+entry["origins"])}

    def parameter(self, context, name, kind):
        require(context is not None, "PARAMETER_CONTEXT", name)
        self.tick()
        parameters = context["class"]["parameters"]
        require(name in parameters and parameters[name]["type"] == kind, "PARAMETER_TYPE", name+": "+kind)
        self.used_names.add(name)
        cache_key = (tuple(context["record"]["id"]), name)
        require(cache_key not in self.resolving, "PARAMETER_CYCLE", name)
        if name not in context["cache"]:
            require(len(self.resolving) < 32, "EXPRESSION_DEPTH", name)
            self.resolving.add(cache_key)
            declaration = parameters[name]
            selected = self.initializers(context).get(name)
            if selected:
                require(declaration["visibility"] == "public", "PRIVATE_PARAMETER", name)
                expr, scope, locals_ = selected["rhs"], self.owner(context), self.bindings(context)
                selection_origin = selected["origin"]
            else:
                expr, scope, locals_ = declaration["expression"], context, {}
                selection_origin = declaration["origin"]
            got = self.evaluate(expr, kind, scope, locals_)
            got = value(kind, got["value"], [declaration["typeOrigin"], selection_origin]+got["origins"])
            context["cache"][name] = got
            self.resolving.remove(cache_key)
        got = context["cache"][name]
        if tuple(context["record"]["id"]) == self.current_child and kind in ("FrameRef", "Vec3<Length>"):
            self.used_properties[(self.current_child, name)] = got
        return got

    def arguments(self, expression, constructor):
        stream = self.d.Stream(expression)
        stream.pop(constructor, kind="id"); stream.pop("(")
        require(expression[-1].value == ")", "CALL", constructor)
        args = self.d.split_top(expression[stream.index:-1], ",")
        require(all(args), "CALL", constructor)
        return args

    def scalar(self, expression, dimensioned, locals_):
        self.tick()
        stream = self.d.Stream(expression); negative = stream.peek() == "-"
        if negative:
            stream.pop("-")
        token = stream.pop()
        if token.kind == "id" and token.value in locals_:
            got = locals_[token.value]
            require(dimensioned and got["type"] == "Length" and stream.done(), "LOCAL_TYPE", token.value)
            return value("Length", -got["value"] if negative else got["value"],
                         got["origins"]+[self.d.origin(expression, "helper Length reference")])
        scale = 0
        if dimensioned:
            stream.pop("["); unit = stream.pop(kind="id"); stream.pop("]")
            require(unit.value in ("m", "cm", "mm"), "LENGTH_UNIT", unit.value)
            scale = {"m": 0, "cm": 2, "mm": 3}[unit.value]
        require(stream.done(), "SCALAR_EXPRESSION", "literal or signed helper Length only")
        number = canonical_literal(token, scale, dimensioned)
        number = -number if negative and number else number
        return value("Length" if dimensioned else "Real", number,
                     [self.d.origin(expression, "signed canonical scalar with unit" if dimensioned else "quaternion scalar")])

    def evaluate(self, expression, kind, context, locals_):
        self.tick()
        require(bool(expression), "EXPRESSION", kind)
        vals = [t.value for t in expression]
        at = self.d.origin(expression, "expression: "+kind)
        if len(expression) == 1 and expression[0].kind == "id" and vals[0] in locals_:
            got = locals_[vals[0]]
            require(got["type"] == kind, "LOCAL_TYPE", vals[0])
            return value(kind, got["value"], [at]+got["origins"])
        if vals == ["world"] and kind == "FrameRef":
            return value(kind, frame(), [at])
        if vals == ["self", ".", "frame"] and kind == "FrameRef":
            require(context is not None, "LEXICAL_SELF", "scene initializer has no self")
            return value(kind, frame(context), [at]+context["record"]["origin"]["identityKeys"])
        if len(vals) == 3 and vals[:2] == ["self", "."]:
            require(kind in ("FrameRef", "Vec3<Length>", "Keyed<Vec3<Length>>"), "UNSUPPORTED_REFERENCE", kind)
            got = self.parameter(context, vals[2], kind)
            return value(kind, got["value"], [at]+got["origins"])
        if kind == "Vec3<Length>":
            args = self.arguments(expression, "vec3")
            require(len(args) == 3, "VECTOR_ARITY", "three Length values")
            scalars = [self.scalar(x, True, locals_) for x in args]
            return value(kind, [x["value"] for x in scalars], [at]+[o for x in scalars for o in x["origins"]])
        if kind == "Rotation":
            args = self.arguments(expression, "quat")
            require(len(args) == 4, "QUATERNION_ARITY", "four scalar literals")
            scalars = [self.scalar(x, False, {}) for x in args]
            return value(kind, normalized_quaternion([x["value"] for x in scalars]),
                         [at]+[o for x in scalars for o in x["origins"]])
        if kind == "Pose":
            args = self.arguments(expression, "pose")
            require(len(args) == 3, "POSE_ARITY", "frame, position, rotation")
            pieces = [self.evaluate(args[0], "FrameRef", context, locals_),
                      self.evaluate(args[1], "Vec3<Length>", context, locals_),
                      self.evaluate(args[2], "Rotation", context, locals_)]
            return value(kind, {"frame": pieces[0]["value"], "position": pieces[1]["value"], "rotation": pieces[2]["value"]},
                         [at]+[o for x in pieces for o in x["origins"]])
        if kind == "Keyed<Vec3<Length>>":
            return self.keyed(expression, context, locals_)
        raise Fault("UNSUPPORTED_EXPRESSION", kind)

    def keyed(self, expression, context, locals_):
        stream = self.d.Stream(expression)
        at = self.d.origin(expression, "selected keyed-vector input")
        if stream.peek() != "keyed":
            self.calls += 1
            require(self.calls <= MAX_CALLS, "HELPER_LIMIT", "direct helper calls")
            reference = self.d.class_reference(stream)
            declaring = self.modules[expression[0].file]
            target = declaring
            if len(reference) == 2:
                imports = declaring["imports"]
                require(len(imports) == 1 and reference[0].value == imports[0]["alias"], "HELPER_MODULE", "explicit alias")
                target = self.modules["hinges.ok"]
            name = reference[-1].value
            require(name in target["functions"], "HELPER_NAME", name)
            fn = target["functions"][name]
            require(target is declaring or fn["public"], "PRIVATE_HELPER", name)
            stream.pop("(")
            require(expression[-1].value == ")", "HELPER_CALL", name)
            args = self.d.split_top(expression[stream.index:-1], ",")
            require(len(args) == 1, "HELPER_ARITY", name)
            argument = self.scalar(args[0], True, {})
            head = self.d.Stream(fn["header"])
            head.pop("("); parameter = head.name(); check_name(parameter.value)
            head.pop(":"); head.pop("Length"); head.pop(")"); head.pop("->")
            require([t.value for t in head.tokens[head.index:]] == ["Keyed", "<", "Vec3", "<", "Length", ">", ">"],
                    "HELPER_TYPE", name)
            body = self.d.Stream(fn["body"]); body.pop("return"); returned = body.statement()
            require(body.done() and returned[0].value == "keyed", "HELPER_BODY", "single direct keyed literal return")
            got = self.keyed(returned, None, {parameter.value: argument})
            return value(got["type"], got["value"], [at, fn["origin"], self.d.origin(fn["header"], "helper typed parameter/return")]+argument["origins"]+got["origins"])
        for expected in ("keyed", "<", "Vec3", "<", "Length", ">", ">"):
            stream.pop(expected)
        body, _, _ = stream.block()
        require(stream.done(), "KEYED_EXPRESSION", "literal only")
        rows = self.d.split_top(body, ",")
        if rows and not rows[-1]:
            rows.pop()
        require(1 <= len(rows) <= 64, "KEY_LIMIT", "finite nonempty inherited input profile")
        entries = {}
        for row in rows:
            require(len(row) > 2 and row[0].kind == "string" and row[1].value == ":", "KEYED_ENTRY", "literal key")
            key = row[0].value; check_key(key)
            require(key not in entries, "DUPLICATE_KEY", key)
            got = self.evaluate(row[2:], "Vec3<Length>", context, locals_)
            entries[key] = value(got["type"], got["value"], [self.d.origin([row[0]], "literal generator key")]+got["origins"])
        return value("Keyed<Vec3<Length>>", dict(sorted(entries.items())), [at])

    def child_admission(self, context):
        selected = dict(context["class"]["builtins"])
        selected.update(self.initializers(context))
        require("placement" not in selected, "CHILD_PLACEMENT", "follow child cannot author placement")
        for field, allowed in (("physical", ["no_body", "(", ")"]), ("motion", ["prescribed"])):
            if field in selected:
                require([t.value for t in selected[field]["rhs"]] == allowed, "CHILD_ADMISSION", field)

    def observations(self):
        records = []
        for oid, context in self.contexts.items():
            self.current_child = oid
            for follow in context["class"]["follows"]:
                require(len(records) < MAX_FOLLOWS, "FOLLOW_LIMIT", "128 follows")
                fields = follow["fields"]
                require([t.value for t in fields["child"]["rhs"]] == ["self"], "UNSUPPORTED_CHILD", "class follow child is self")
                self.child_admission(context)
                parent = self.evaluate(fields["parent"]["rhs"], "FrameRef", context, {})
                offset = self.evaluate(fields["offset"]["rhs"], "Pose", context, {})
                require(parent["value"] == offset["value"]["frame"], "OFFSET_FRAME", "exact parent frame required")
                source = context["record"]
                definition = context["class"]["definition"]
                properties = {name: got for (child, name), got in self.used_properties.items() if child == oid}
                records.append({"id": source["id"]+[follow["key"]], "path": source["path"]+"."+follow["name"],
                    "definitionId": source["definitionId"]+[follow["key"]],
                    "childId": source["id"], "childPath": source["path"], "childDefinitionId": source["definitionId"],
                    "parentFrame": parent["value"], "offsetPositionM": offset["value"]["position"],
                    "offsetRotationWxyz": offset["value"]["rotation"], "usedChildProperties": properties,
                    "sourceOrigins": {"declaration": follow["origin"], "definition": definition["origin"],
                        "identity": source["origin"]["identityKeys"]+[follow["keyOrigin"]],
                        "definitionKeys": [definition["module"]["keyOrigin"], definition["keyOrigin"], follow["keyOrigin"]],
                        "parent": [fields["parent"]["origin"]]+parent["origins"],
                        "child": [fields["child"]["origin"]]+source["origin"]["identityKeys"],
                        "offset": [fields["offset"]["origin"]]+offset["origins"]}})
        for context in self.contexts.values():
            for row in context["decl"]["assignments"]:
                if len(row["lhs"]) > 1:
                    names = {t.value for t in row["lhs"] if t.kind == "id"}
                    require(not names.intersection(self.used_names | {"physical", "motion", "placement"}),
                            "UNSUPPORTED_NESTED_OVERRIDE", "follow dependency or child admission override")
        check_graph(records)
        return envelope("source-follows", records, programRevision=self.identity["programRevision"],
            sourceHashes=self.identity["sourceHashes"], sourceManifest=self.identity["sourceManifest"],
            expressionSteps=self.steps, helperCalls=self.calls)


def check_graph(records):
    ids, children, graph = set(), set(), {}
    for row in records:
        oid, child = tuple(row["id"]), tuple(row["childId"])
        require(oid not in ids and child not in children, "DUPLICATE_FOLLOW", "unique relation and incoming follow")
        ids.add(oid); children.add(child)
        parent = row["parentFrame"]["objectId"]
        graph[child] = None if parent is None else tuple(parent)
    for child in graph:
        seen, current = set(), child
        while current in graph:
            require(current not in seen, "FOLLOW_CYCLE", "acyclic follow-only graph")
            seen.add(current); current = graph[current]


def envelope(kind, records, **fields):
    return {"schema": SCHEMA, "kind": kind, "records": records, "followCount": len(records),
        "historicalInputsBound": False, "sourceValidityQualified": False, "completeC255Semantic": False,
        "executionAllowed": False, "realTrialSuccess": None, "jointUnionQualified": False,
        "artifactFollowDefinitionAuthority": None, "artifactFollowSourceSpanAuthority": None,
        "comparisonPolicy": dict(POLICY), "dependencySha256": DEPENDENCY_SHA, "limits": NONCLAIMS.copy(), **fields}


def _artifact(raw):
    d = dependency()
    identity = d.observe_glb_ownership(raw)
    document = d.glb_document(raw)
    rows = document["extras"]["ontokin"]["follows"]
    require(type(rows) is list and len(rows) <= MAX_FOLLOWS, "FOLLOW_LIMIT", "bounded follow rows")
    objects = {x["path"]: x for x in identity["records"]}
    frames = {"world": frame()}
    for path, obj in objects.items():
        frames[path+".frame"] = {"kind": "object-frame", "objectId": obj["id"], "path": path+".frame"}
    records = []
    for index, row in enumerate(rows):
        require(type(row) is dict and set(row) == {"path", "element_id", "parent_frame", "child_object", "offset_position_m", "offset_rotation_wxyz"},
                "FOLLOW_ROW", "exact finite metadata fields")
        child_path = d.string(row["child_object"], "follow child")
        require(child_path in objects, "CHILD_MAPPING", child_path)
        child = objects[child_path]
        oid = d.identifier(row["element_id"], "follow identity")
        require(oid[:-1] == child["id"], "FOLLOW_IDENTITY", "self-child relation prefix")
        check_key(oid[-1])
        path = d.string(row["path"], "follow path")
        require(path.startswith(child_path+".") and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", path[len(child_path)+1:]),
                "FOLLOW_PATH", "child path plus relation name")
        parent_path = d.string(row["parent_frame"], "follow parent")
        require(parent_path in frames, "FRAME_MAPPING", parent_path)
        position = row["offset_position_m"]
        require(type(position) is list and len(position) == 3, "POSITION", "three SI values")
        position = [numeric(x, "follow offset") for x in position]
        rotation, _ = quaternion_norm(row["offset_rotation_wxyz"])
        pointer = "/extras/ontokin/follows/"+str(index)
        properties = document["nodes"][child["node"]]["extras"]["ontokin"]["properties"]
        require(type(properties) is dict, "PROPERTY_MAPPING", "child properties object")
        records.append({"id": oid, "path": path, "childId": child["id"], "childPath": child_path,
            "childDefinitionId": child["definitionId"], "parentFrame": frames[parent_path],
            "offsetPositionM": position, "offsetRotationWxyz": rotation, "untrustedChildProperties": properties,
            "childNode": child["node"], "artifactOrigins": {field: pointer+"/"+field for field in row},
            "propertyOrigin": "/nodes/"+str(child["node"])+"/extras/ontokin/properties"})
    check_graph(records)
    return envelope("untrusted-artifact-follows", records, artifactSha256=identity["artifactSha256"],
                    artifactBytes=len(raw), ownershipVerified=False, sourceAssociationVerified=False)


def property_agrees(actual, expected):
    require(type(actual) is dict and set(actual) == {"type", "value"} and actual["type"] == expected["type"],
            "PROPERTY_TYPE", expected["type"])
    if expected["type"] == "FrameRef":
        require(actual["value"] == expected["value"]["path"], "PROPERTY_VALUE", "FrameRef")
    else:
        values = actual["value"]
        require(type(values) is list and len(values) == 3, "PROPERTY_VALUE", "three Length values")
        for item, wanted in zip(values, expected["value"]):
            require(type(item) is dict and set(item) == {"type", "value"} and item["type"] == "Length"
                    and numeric(item["value"], "Length property") == wanted, "PROPERTY_VALUE", "Vec3<Length>")


def _compare(files, raw):
    source = Source(files).observations()
    artifact = _artifact(raw)
    binding = dependency().compare_ownership(files, raw)
    wanted = {tuple(x["id"]): x for x in source["records"]}
    got = {tuple(x["id"]): x for x in artifact["records"]}
    require(set(wanted) == set(got), "FOLLOW_COVERAGE", "complete source/artifact follow identity set")
    verified = []
    for oid, expected in wanted.items():
        actual = got[oid]
        for field in ("path", "childId", "childPath", "childDefinitionId", "parentFrame", "offsetPositionM"):
            require(actual[field] == expected[field], "FOLLOW_MISMATCH", expected["path"]+" "+field)
        require(quaternion_agrees(actual["offsetRotationWxyz"], expected["offsetRotationWxyz"]),
                "FOLLOW_ROTATION", expected["path"])
        properties = {}
        for name, property_ in expected["usedChildProperties"].items():
            property_agrees(actual["untrustedChildProperties"][name], property_)
            properties[name] = actual["propertyOrigin"]+"/"+name.replace("~", "~0").replace("/", "~1")
        verified.append({**expected, "artifactOrigins": actual["artifactOrigins"], "qualifiedPropertyOrigins": properties,
                         "childNode": actual["childNode"], "rawArtifactRotationWxyz": actual["offsetRotationWxyz"]})
    return envelope("source-artifact-follow-comparison", verified, followConsistent=True,
        sourceAssociationVerified=True, programRevision=source["programRevision"], sourceHashes=source["sourceHashes"],
        sourceAuthorityOrigins=binding["sourceAuthorityOrigins"], artifactSha256=artifact["artifactSha256"],
        artifactBytes=artifact["artifactBytes"])


def observe_source_follows(source_files):
    return public(lambda: Source(source_files).observations())


def observe_glb_follows(raw):
    return public(lambda: _artifact(raw))


def compare_follows(source_files, raw):
    return public(lambda: _compare(source_files, raw))


def read_bound_endpoint(repo, endpoint):
    def run():
        d = dependency()
        require(endpoint in d.PINS, "ENDPOINT", "before or after")
        root = Path(repo).resolve()
        def read(name, size, sha):
            path = root/d.PROOF/name
            require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root), "INPUT_PATH", name)
            require(path.stat().st_size == size, "INPUT_SIZE", name)
            with path.open("rb") as handle:
                raw = handle.read(size+1)
            require(len(raw) == size and hashlib.sha256(raw).hexdigest() == sha, "HISTORICAL_BINDING", name)
            return raw
        pin = d.PINS[endpoint]
        files = {"main.ok": read(endpoint+".main.ok", 1708, pin["source"]), "hinges.ok": read("hinges.ok", 1911, d.LIBRARY_SHA)}
        raw = read(endpoint+".glb", pin["bytes"], pin["glb"])
        result = _compare(files, raw)
        result.update(historicalInputsBound=True, endpoint=endpoint, artifactPath=d.PROOF+"/"+endpoint+".glb")
        return result
    return public(run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--endpoint", required=True, choices=("before", "after"))
    args = parser.parse_args()
    try:
        result = read_bound_endpoint(args.repo, args.endpoint)
    except Fault as exc:
        print(json.dumps({"schema": SCHEMA, "status": "REFUSED", "code": exc.code, "detail": exc.detail,
                          "executionAllowed": False, "realTrialSuccess": None}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
