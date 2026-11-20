#!/usr/bin/env python3
"""Independent finite source hinge declarations under C260, without execution."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import types
import unicodedata


SCHEMA = "ontokin.c265.source-hinge-observation/0.1"
CONTRACT = "ontokin.c260.hinge-declarations/0.1"
DEPENDENCY_BYTES = 35942
DEPENDENCY_SHA256 = "c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1"
MAX_SOURCE_BYTES = 65536
MAX_HINGES = 128
MAX_SITES = 256
MAX_ID_COMPONENTS = 32
MAX_TEXT = 512
KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
NUMBER = re.compile(r"(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?\Z")
PI64 = Fraction.from_float(float.fromhex("0x1.921fb54442d18p+1"))
SCALES = {"rad": Fraction(1), "deg": PI64 / 180,
          "m": Fraction(1), "cm": Fraction(1, 100), "mm": Fraction(1, 1000)}
PREDEFINED = set(("self world static prescribed dynamic disabled Object Int Real Bool String Quantity "
    "Length Area Volume Mass Time Angle Speed Acceleration AngularSpeed Force Torque Density Inertia "
    "Vec3 Vector3 Point3 Rotation Pose Range Color Geometry BodyModel MotionMode CollisionMode "
    "Ref FrameRef SiteRef JointRef Action Keyed real abs min max near sqrt sin cos vec3 vector "
    "point quat axis_angle pose range rgba empty sphere box no_body sphere_body move spin tween len").split())
RESERVED = set(("ontokin module profile requires class extends public private param derive override method "
    "fn let return part parts site joint follow scene object action at sequence start pause resume stop "
    "release using incoming assert if then else and or not true false import from version digest for in keyed").split())
BUILTINS = {"role", "geometry", "appearance", "physical", "motion", "collision",
            "placement", "velocity", "omega"}
IMPLICIT = BUILTINS | {"frame", "origin"}
NONCLAIMS = [
    "Source declarations only; no artifact agreement or historical byte admission",
    "Site pose expressions are byte witnesses, not evaluated poses or world alignment",
    "No complete source validity, C255 semantic qualification or accepted revision",
    "No joint dynamics, action admission, motion, native execution or model trial",
    "No clean rebuild, invalid-edit atomicity or comparative advantage qualification",
    "Bare-CR line-comment termination is unsupported by the pinned lexical utility",
]
_DEPENDENCY = None


class Fault(ValueError):
    """A typed whole-observation refusal with bounded source identity when available."""

    def __init__(self, code, detail, origin=None):
        self.code, self.detail, self.origin = code, detail, origin
        self.sourceHashes, self.sourceBytes = {}, {}
        super().__init__(f"{code}: {detail}")


def _require(condition, detail, code="MALFORMED", origin=None):
    if not condition:
        raise Fault(code, detail, origin)


def _text(value, where):
    _require(type(value) is str and bool(value), "nonempty text required: " + where)
    _require(len(value) <= MAX_TEXT, "text exceeds 512 scalars: " + where, "RESOURCE_LIMIT")
    _require(all(unicodedata.category(c) not in ("Cc", "Cs") for c in value),
             "control or surrogate in text: " + where)
    return value


def _key(value):
    _require(type(value) is str and KEY.fullmatch(value) is not None,
             "stable key outside adopted ASCII domain")
    return value


def _name(value):
    _text(value, "declaration name")
    _require(value not in PREDEFINED and value not in RESERVED,
             "declaration shadows predefined or reserved name: " + value)


def _identity(value):
    _require(type(value) is list and bool(value), "identity must be a nonempty array")
    _require(len(value) <= MAX_ID_COMPONENTS, "identity exceeds 32 components", "RESOURCE_LIMIT")
    for component in value:
        _text(component, "identity component")
    return value


def _dependency():
    global _DEPENDENCY
    if _DEPENDENCY is None:
        path = Path(__file__).absolute().parent.parent / "localized-repair-c257/ownership.py"
        _require(path.is_file() and not path.is_symlink(), "C257 dependency path", "INPUT_BINDING")
        _require(path.stat().st_size == DEPENDENCY_BYTES, "C257 dependency size", "INPUT_BINDING")
        with path.open("rb") as handle:
            raw = handle.read(DEPENDENCY_BYTES + 1)
        _require(len(raw) == DEPENDENCY_BYTES and hashlib.sha256(raw).hexdigest() == DEPENDENCY_SHA256,
                 "C257 dependency bytes", "INPUT_BINDING")
        module = types.ModuleType("_c265_pinned_c257")
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        exec(compile(raw, str(path), "exec"), module.__dict__)
        _DEPENDENCY = module
    return _DEPENDENCY


def _origin_key(origin):
    return origin["file"], origin["startByte"], origin["endByteExclusive"]


def _number(token, scale):
    """Bound decimal work, multiply exact factors, then round only once."""
    _require(token.kind == "number", "numeric literal required", "UNSUPPORTED_SOURCE_FORM")
    text = token.value
    _require(len(text) <= 64, "numeric lexeme exceeds 64 characters", "RESOURCE_LIMIT")
    match = NUMBER.fullmatch(text)
    _require(match is not None, "numeric literal spelling")
    integer, fractional, exponent_text = match.groups()
    exponent = int(exponent_text or "0")
    _require(-400 <= exponent <= 400, "explicit exponent outside [-400,400]", "RESOURCE_LIMIT")
    digits = integer + (fractional or "")
    shift = exponent - len(fractional or "")
    exact = Fraction(int(digits) * 10 ** max(shift, 0), 10 ** max(-shift, 0)) * scale
    if exact:
        # Exact inequalities avoid a rounded logarithm at the adjusted-exponent edges
        _require(Fraction(1, 10 ** 324) <= exact < Fraction(10 ** 309),
                 "scaled adjusted exponent outside [-324,308]", "RESOURCE_LIMIT")
    try:
        value = float(exact)
    except OverflowError as exc:
        raise Fault("MALFORMED", "nonfinite canonical scalar") from exc
    _require(math.isfinite(value), "nonfinite canonical scalar")
    return value, exact


class Source:
    def __init__(self, files):
        self.files = files
        self.hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
        self.d = _dependency()
        d = self.d

        class Stream(d.Stream):
            # C257's literal-value comparisons are supplemented with token kinds here
            def pop(self, value=None, kind=None):
                if value is not None and kind is None:
                    kind = "id" if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", value) else "symbol"
                return super().pop(value, kind)

        self.Stream = Stream
        for name, raw in files.items():
            self.comment_boundaries(raw, name)
        self.tokens = {name: d.lex(raw, name) for name, raw in files.items()}
        self.keyed_counts = []
        for tokens in self.tokens.values():
            self.lexical_audit(tokens)
            self.module_audit(tokens)
        self.modules = {name: d.parse_module(raw, name) for name, raw in files.items()}
        self.classes, self.declarations, self.seen_joints = {}, {}, set()
        for module in self.modules.values():
            aliases = [item["alias"] for item in module["imports"]]
            names = list(module["classes"]) + list(module["functions"]) + aliases
            _require(len(names) == len(set(names)), "duplicate module alias/definition name")
            for name in names:
                _name(name)
            for definition in module["classes"].values():
                self.classes[_origin_key(definition["origin"])] = self.scan_class(definition)
            if module["scene"]:
                for decl in module["scene"]["roots"]:
                    _name(decl["name"])
                    self.declarations[_origin_key(decl["declaration"])] = decl
        all_joints = {(t.file, t.start) for tokens in self.tokens.values() for t in tokens
                      if t.kind == "id" and t.value == "joint"}
        _require(all_joints == self.seen_joints, "joint syntax in unsupported position", "UNSUPPORTED_SOURCE_FORM")
        try:
            # Only identity/module/generation data are used; ownership is not hinge truth
            self.identity = d.observe_source_ownership(files)
        except d.Fault as exc:
            if exc.code == "KEY_LIMIT":
                code = "RESOURCE_LIMIT" if any(n > 64 for n in self.keyed_counts) else "UNSUPPORTED_SOURCE_FORM"
                raise Fault(code, "finite keyed input must have 1 to 64 keys") from exc
            raise
        self.contexts = {}
        for record in self.identity["records"]:
            _identity(record["id"])
            _identity(record["definitionId"])
            _text(record["path"], "object path")
            for key in record["id"]:
                _key(key)
            self.contexts[tuple(record["id"])] = {
                "record": record,
                "class": self.classes[_origin_key(record["origin"]["definition"])],
                "declaration": self.declarations[_origin_key(record["origin"]["declaration"])],
            }
        self.membership_audit()
        self.sites = {}

    def comment_boundaries(self, raw, filename):
        """Refuse a valid comment terminator the pinned lexer cannot observe safely."""
        offset = 0
        while offset < len(raw):
            match = self.d.LEXER.match(raw, offset)
            if match is None:
                # The unchanged bounded lexer will report the malformed token
                break
            if match.lastgroup == "comment" and b"\r" in match.group().replace(b"\r\n", b""):
                raise Fault("UNSUPPORTED_SOURCE_FORM", "bare-CR line-comment terminator is unsupported",
                            {"file": filename, "sha256": self.hashes[filename],
                             "startByte": offset, "endByteExclusive": match.end()})
            offset = match.end()

    def witnessed_tokens(self, origin):
        selected = [t for t in self.tokens[origin["file"]]
                    if origin["startByte"] <= t.start and t.end <= origin["endByteExclusive"]]
        _require(selected and selected[0].start == origin["startByte"]
                 and selected[-1].end == origin["endByteExclusive"], "membership witness boundaries")
        return selected

    @staticmethod
    def type_tokens(tokens):
        _require(bool(tokens) and all(t.kind == "id" or
                 (t.kind == "symbol" and t.value in ("<", ">", ",", ".")) for t in tokens),
                 "type syntax requires identifiers and type punctuation")

    def membership_audit(self):
        """Reject token-kind ambiguities in the C257 utilities' consumed context."""
        functions = {_origin_key(fn["origin"]): fn for module in self.modules.values()
                     for fn in module["functions"].values()}
        for context in self.contexts.values():
            for member in context["class"]["members"].values():
                if member["memberKind"] == "parts":
                    parameter = context["class"]["members"].get(member["generated"]["parameter"])
                    _require(parameter is not None and parameter["memberKind"] == "param", "keyed parameter binding")
                    self.type_tokens(parameter["type"])
                    _require(len(parameter["type"]) > 2 and parameter["type"][0].kind == "id"
                             and parameter["type"][0].value == "Keyed"
                             and parameter["type"][1].kind == "symbol" and parameter["type"][1].value == "<",
                             "typed Keyed parameter required", "UNSUPPORTED_SOURCE_FORM")
                    direct_override = any(len(row["lhs"]) == 1 and row["lhs"][0].kind == "id"
                                          and row["lhs"][0].value == parameter["name"]
                                          for row in context["declaration"]["assignments"])
                    _require(not direct_override or parameter["visibility"] == "public",
                             "private keyed membership parameter cannot be overridden externally")
            expansion = context["record"]["origin"]["expansion"]
            if expansion is None:
                continue
            witnesses = expansion["inputResolution"]
            expression = self.witnessed_tokens(witnesses[0])
            if expression[0].kind == "id" and expression[0].value == "keyed":
                continue
            stream = self.Stream(expression)
            self.d.class_reference(stream)
            stream.pop("(")
            depth = 1
            while depth:
                token = stream.pop()
                if token.kind == "symbol" and token.value in ("(", ")"):
                    depth += 1 if token.value == "(" else -1
            _require(stream.done(), "only direct keyed helper calls supported", "UNSUPPORTED_SOURCE_FORM")
            for witness in witnesses[1:]:
                if witness.get("role") != "function":
                    continue
                function = functions[_origin_key(witness)]
                helper = self.Stream(function["body"])
                helper.pop("return")
                returned = helper.statement()
                _require(helper.done() and returned and returned[0].kind == "id" and returned[0].value == "keyed",
                         "helper must directly return a typed keyed literal", "UNSUPPORTED_SOURCE_FORM")

    def lexical_audit(self, tokens):
        d = self.d
        for index, token in enumerate(tokens):
            if token.kind == "string":
                _text(token.value, "source string")
            if token.kind == "symbol" and token.value == "@":
                _require(index + 1 < len(tokens) and tokens[index + 1].kind == "string",
                         "literal declaration key required")
                _key(tokens[index + 1].value)
            if token.kind == "id" and token.value == "keyed":
                stream = self.Stream(tokens[index:])
                stream.pop("keyed"); stream.pop("<")
                type_start = stream.index
                depth = 1
                while depth:
                    item = stream.pop()
                    if item.kind == "symbol" and item.value in ("<", ">"):
                        depth += 1 if item.value == "<" else -1
                self.type_tokens(stream.tokens[type_start:stream.index - 1])
                body, _, _ = stream.block()
                rows = d.split_top(body, ",")
                if rows and not rows[-1]:
                    rows.pop()
                self.keyed_counts.append(len(rows))
                for row in rows:
                    _require(len(row) >= 3 and row[0].kind == "string"
                             and row[1].kind == "symbol" and row[1].value == ":",
                             "literal keyed row required", "UNSUPPORTED_SOURCE_FORM")
                    _key(row[0].value)

    def module_audit(self, tokens):
        """Validate the token kinds and complete headers consumed by C257 context."""
        stream = self.Stream(tokens)
        stream.pop("ontokin"); stream.pop(kind="string"); stream.pop(";")
        stream.pop("module"); stream.name(); stream.key(); stream.pop(";")
        stream.pop("profile"); stream.pop(kind="string"); stream.pop(";")
        module_names, module_keys = set(), set()

        def declaration(name, key, names, keys, scope):
            _name(name.value); _key(key.value)
            _require(name.value not in names and key.value not in keys,
                     "duplicate name or declaration key in " + scope)
            names.add(name.value); keys.add(key.value)

        while not stream.done():
            if stream.peek() in ("public", "private"):
                stream.pop(stream.peek(), kind="id")
            keyword = stream.pop(kind="id")
            if keyword.value == "import":
                name, key = stream.name(), stream.key()
                declaration(name, key, module_names, module_keys, "module")
                stream.pop("from"); stream.pop(kind="string")
                stream.pop("version"); stream.pop(kind="string"); stream.pop("digest")
                stream.pop(kind="string"); stream.pop(";")
            elif keyword.value in ("class", "fn"):
                name, key = stream.name(), stream.key()
                declaration(name, key, module_names, module_keys, "module")
                stream.header_block()
            elif keyword.value == "scene":
                stream.name(); scene_key = stream.key()
                _require(scene_key.value != "definitions", "scene key collides with definition namespace")
                body, _, _ = stream.block()
                scene = self.Stream(body)
                scene_names, scene_keys = set(), set()
                while not scene.done():
                    _require(scene.tokens[scene.index].kind == "id", "scene keyword must be an identifier")
                    if scene.peek() == "object":
                        start = scene.index
                        self.d.occurrence_declaration(scene, "public", scene.tokens[scene.index], set())
                        header = self.Stream(scene.tokens[start:scene.index])
                        header.pop("object"); name, key = header.name(), header.key()
                        declaration(name, key, scene_names, scene_keys, "scene")
                    elif scene.peek() == "action":
                        scene.pop("action"); name, key = scene.name(), scene.key()
                        declaration(name, key, scene_names, scene_keys, "scene")
                        scene.pop("=")
                        _require(bool(scene.statement()), "action expression required")
                    elif scene.peek() in ("duration", "gravity"):
                        scene.statement()
                    elif scene.peek() == "at":
                        scene.header_block()
                    else:
                        raise Fault("UNSUPPORTED_SOURCE_FORM", "unsupported scene statement")
            else:
                raise Fault("UNSUPPORTED_SOURCE_FORM", "unsupported module declaration")

    def witness(self, origin):
        result = dict(origin)
        result["sha256"] = self.hashes[result["file"]]
        start, end = result["startByte"], result["endByteExclusive"]
        _require(type(start) is int and type(end) is int and 0 <= start < end <= len(self.files[result["file"]]),
                 "invalid source witness bounds")
        return result

    def at(self, tokens, role):
        return self.witness(self.d.origin(tokens, role))

    def origin_tree(self, value):
        if type(value) is dict:
            if {"file", "startByte", "endByteExclusive"} <= value.keys():
                return self.witness(value)
            return {key: self.origin_tree(item) for key, item in value.items()}
        if type(value) is list:
            return [self.origin_tree(item) for item in value]
        return value

    def scan_class(self, definition):
        d, stream = self.d, self.Stream(definition["body"])
        members, keys, builtins = {}, set(), set()
        while not stream.done():
            start_index = stream.index
            start = stream.tokens[start_index]
            visibility = None
            if stream.peek() in ("public", "private"):
                visibility = stream.pop(stream.peek(), kind="id").value
            _require(not stream.done() and stream.tokens[stream.index].kind == "id", "class member keyword")
            kind = stream.peek()
            if kind in ("part", "parts"):
                decl = d.occurrence_declaration(stream, visibility or "private", start, set())
                self.declarations[_origin_key(decl["declaration"])] = decl
                member = dict(decl, memberKind=kind)
                header = self.Stream(stream.tokens[start_index:stream.index])
                if visibility is not None:
                    header.pop(visibility)
                header.pop(kind); name_token = header.name(); header.key(); header.pop(":")
                d.class_reference(header)
                if kind == "parts":
                    header.pop("for"); header.pop("("); first = header.name(); header.pop(","); second = header.name()
                    _name(first.value); _name(second.value)
            elif kind == "param":
                stream.pop("param"); name_token, key_token = stream.name(), stream.key(); stream.pop(":")
                rest = stream.statement(); groups = d.split_top(rest, "=")
                _require(len(groups) == 2 and groups[0] and groups[1], "parameter declaration")
                member = {"memberKind": kind, "name": name_token.value, "key": key_token.value,
                          "visibility": visibility or "private", "explicitVisibility": visibility is not None,
                          "type": groups[0], "expression": groups[1]}
            elif kind in ("site", "joint", "follow", "method"):
                keyword = stream.pop(kind)
                if kind == "joint":
                    self.seen_joints.add((keyword.file, keyword.start))
                name_token, key_token = stream.name(), stream.key()
                header, body, _, closing = stream.header_block()
                member = {"memberKind": kind, "name": name_token.value, "key": key_token.value,
                          "visibility": visibility, "header": header, "body": body,
                          "declaration": d.origin([start, closing], kind + " declaration"),
                          "nameOrigin": d.origin([name_token], kind + " lexical name"),
                          "keyOrigin": d.origin([key_token], kind + " stable key")}
            else:
                statement = stream.statement(); groups = d.split_top(statement, "=")
                _require(visibility is None and len(groups) == 2 and len(groups[0]) == 1
                         and groups[0][0].kind == "id" and groups[0][0].value in BUILTINS,
                         "unsupported class assignment", "UNSUPPORTED_SOURCE_FORM")
                name = groups[0][0].value
                _require(name not in builtins, "duplicate class assignment: " + name)
                builtins.add(name)
                continue
            name, key = member["name"], member["key"]
            _name(name); _key(key)
            _require(name not in IMPLICIT and key not in {"frame", "origin"}, "implicit instance member collision")
            _require(name not in members and key not in keys, "duplicate class member name or key")
            members[name] = member; keys.add(key)
        return {"definition": definition, "members": members}

    def fields(self, member, expected):
        _require(member["visibility"] in ("public", "private"),
                 "explicit member visibility required", "UNSUPPORTED_SOURCE_FORM")
        stream, fields = self.Stream(member["body"]), {}
        while not stream.done():
            statement = stream.statement()
            groups = self.d.split_top(statement, "=")
            _require(len(groups) == 2 and len(groups[0]) == 1 and groups[0][0].kind == "id" and bool(groups[1]),
                     "simple field assignment required")
            name = groups[0][0].value
            _require(name not in fields, "duplicate field assignment: " + name)
            fields[name] = {"rhs": groups[1], "origin": self.at(statement, "field assignment: " + name),
                            "expression": self.at(groups[1], "field expression: " + name)}
        _require(set(fields) == set(expected), "missing or extra " + member["memberKind"] + " field")
        return fields

    def literal(self, expression, units=None):
        stream = self.Stream(expression)
        negative = stream.peek() == "-"
        if negative:
            stream.pop("-")
        _require(not stream.done() and stream.tokens[stream.index].kind == "number",
                 "signed literal required", "UNSUPPORTED_SOURCE_FORM")
        token = stream.pop(kind="number")
        if units is None:
            scale = Fraction(1)
        else:
            _require(stream.peek() == "[", "literal unit required", "UNSUPPORTED_SOURCE_FORM")
            stream.pop("[")
            unit = stream.pop(kind="id")
            _require(unit.value in units, "unsupported literal unit", "UNSUPPORTED_SOURCE_FORM")
            stream.pop("]"); scale = SCALES[unit.value]
        _require(stream.done(), "computed literal expression is unsupported", "UNSUPPORTED_SOURCE_FORM")
        value, exact = _number(token, scale)
        return (-value, -exact) if negative else (value, exact)

    def arguments(self, expression, constructor, count):
        stream = self.Stream(expression)
        _require(len(expression) >= 3 and expression[0].kind == "id" and expression[0].value == constructor,
                 "literal " + constructor + " constructor required", "UNSUPPORTED_SOURCE_FORM")
        stream.pop(constructor); stream.pop("(")
        _require(expression[-1].kind == "symbol" and expression[-1].value == ")", "constructor closing parenthesis")
        arguments = self.d.split_top(expression[stream.index:-1], ",")
        _require(len(arguments) == count and all(arguments), "constructor argument count")
        return arguments

    def part_context(self, context, part, key=None):
        oid = context["record"]["id"] + [part["key"]]
        if part["memberKind"] == "parts":
            _require(key is not None, "literal keyed part selection required", "UNSUPPORTED_SOURCE_FORM")
            oid.append(_key(key))
        else:
            _require(key is None, "ordinary part cannot be indexed", "UNSUPPORTED_SOURCE_FORM")
        _require(tuple(oid) in self.contexts, "part occurrence does not exist")
        return self.contexts[tuple(oid)]

    def check_overrides(self, context):
        for row in context["declaration"]["assignments"]:
            stream, current = self.Stream(row["lhs"]), context
            while True:
                _require(not stream.done() and stream.tokens[stream.index].kind == "id",
                         "unsupported initializer target", "UNSUPPORTED_SOURCE_FORM")
                name = stream.name().value
                member = current["class"]["members"].get(name)
                if stream.done():
                    if member is not None and member["memberKind"] in ("site", "joint", "follow"):
                        raise Fault("UNSUPPORTED_SOURCE_FORM", "relation or site overrides are unsupported")
                    _require((member is not None and member["memberKind"] == "param") or name in BUILTINS,
                             "initializer must target a parameter or built-in", "UNSUPPORTED_SOURCE_FORM")
                    break
                _require(member is not None, "unknown initializer member")
                if member["memberKind"] in ("site", "joint", "follow"):
                    raise Fault("UNSUPPORTED_SOURCE_FORM", "relation or site overrides are unsupported")
                _require(member["memberKind"] in ("part", "parts"),
                         "unsupported nested initializer target", "UNSUPPORTED_SOURCE_FORM")
                key = None
                if stream.peek() == "[":
                    stream.pop("["); key = stream.pop(kind="string").value; stream.pop("]")
                current = self.part_context(current, member, key)
                stream.pop(".")

    def site(self, context, name, external):
        _require(name not in ("origin", "frame"), "implicit site endpoint unsupported", "UNSUPPORTED_SOURCE_FORM")
        member = context["class"]["members"].get(name)
        if member is not None and member["memberKind"] == "param":
            _require(not external or member["visibility"] == "public", "private external endpoint parameter")
            declared_type = member["type"]
            if (member["explicitVisibility"] and len(declared_type) == 1
                    and declared_type[0].kind == "id" and declared_type[0].value == "SiteRef"):
                # Classify the declared form only; do not resolve or evaluate its value.
                raise Fault("UNSUPPORTED_SOURCE_FORM", "declared SiteRef parameter endpoint is unsupported")
        _require(member is not None and member["memberKind"] == "site", "endpoint must resolve to a declared site")
        _require(not external or member["visibility"] == "public", "private external endpoint site")
        record = context["record"]
        sid = _identity(record["id"] + [member["key"]])
        if tuple(sid) in self.sites:
            return self.sites[tuple(sid)]
        _require(len(self.sites) < MAX_SITES, "more than 256 distinct referenced sites", "RESOURCE_LIMIT")
        _require(not member["header"], "unsupported site header", "UNSUPPORTED_SOURCE_FORM")
        fields = self.fields(member, ("pose", "interface", "size"))
        interface = fields["interface"]["rhs"]
        _require(len(interface) == 1 and interface[0].kind == "string",
                 "site interface must be a literal string", "UNSUPPORTED_SOURCE_FORM")
        size, exact_size = self.literal(fields["size"]["rhs"], {"m", "cm", "mm"})
        _require(exact_size >= 0, "site size must be nonnegative")
        result = {
            "id": sid, "definitionId": _identity(record["definitionId"] + [member["key"]]),
            "path": _text(record["path"] + "." + name, "site path"), "name": name, "key": member["key"],
            "objectId": list(record["id"]), "objectDefinitionId": list(record["definitionId"]),
            "interface": _text(interface[0].value, "site interface"), "sizeM": size,
            "poseEvaluated": False, "compatibilityAuthority": "source-only",
            "sourceOrigins": self.member_origins(member, fields, record),
        }
        self.sites[tuple(sid)] = result
        return result

    def endpoint(self, context, expression):
        _require(expression and expression[0].kind == "id" and expression[0].value == "self",
                 "endpoint must be a lexical self path", "UNSUPPORTED_SOURCE_FORM")
        stream = self.Stream(expression)
        stream.pop("self"); stream.pop("."); first = stream.name().value
        if stream.done():
            return self.site(context, first, False)
        _require(stream.peek() == ".", "keyed or computed endpoint unsupported", "UNSUPPORTED_SOURCE_FORM")
        stream.pop("."); terminal = stream.name().value
        _require(stream.done(), "deeper endpoint chain unsupported", "UNSUPPORTED_SOURCE_FORM")
        part = context["class"]["members"].get(first)
        _require(part is not None and part["memberKind"] == "part",
                 "endpoint traversal requires one direct ordinary part", "UNSUPPORTED_SOURCE_FORM")
        return self.site(self.part_context(context, part), terminal, True)

    def member_origins(self, member, fields, record):
        return {
            "declaration": self.witness(member["declaration"]),
            "name": self.witness(member["nameOrigin"]), "key": self.witness(member["keyOrigin"]),
            "fields": {name: {"assignment": item["origin"], "expression": item["expression"]}
                       for name, item in fields.items()},
            "owningObject": self.origin_tree(record["origin"]),
        }

    def observe(self):
        records, ids, paths = [], set(), set()
        for context in self.contexts.values():
            self.check_overrides(context)
            owner = context["record"]
            for member in context["class"]["members"].values():
                if member["memberKind"] != "joint":
                    continue
                _require(len(records) < MAX_HINGES, "more than 128 hinges", "RESOURCE_LIMIT")
                header = member["header"]
                _require(len(header) == 2 and header[0].kind == "symbol" and header[0].value == ":"
                         and header[1].kind == "id" and header[1].value == "hinge",
                         "only literal hinge joint declarations are supported", "UNSUPPORTED_SOURCE_FORM")
                fields = self.fields(member, ("parent", "child", "axis", "limits", "initial"))
                parent = self.endpoint(context, fields["parent"]["rhs"])
                child = self.endpoint(context, fields["child"]["rhs"])
                _require(parent["objectId"] != child["objectId"], "hinge endpoints must belong to distinct objects")
                _require(parent["interface"] == child["interface"] and parent["sizeM"] == child["sizeM"],
                         "source endpoint interface/size mismatch")
                axis = [self.literal(x)[0] for x in self.arguments(fields["axis"]["rhs"], "vec3", 3)]
                _require(any(x != 0 for x in axis), "zero hinge axis")
                # This adopted norm domain classifies invalid input only
                # It never widens the exact signed-basis observation subset
                squared = sum((Fraction.from_float(x) ** 2 for x in axis), Fraction())
                norm_margin = Fraction(1, 10 ** 12)
                _require((1 - norm_margin) ** 2 <= squared <= (1 + norm_margin) ** 2,
                         "hinge axis outside adopted unit-norm domain")
                _require(sum(abs(x) == 1 for x in axis) == 1 and all(x in (-1, 0, 1) for x in axis),
                         "axis outside the six signed basis vectors", "UNSUPPORTED_SOURCE_FORM")
                limits = [self.literal(x, {"deg", "rad"})[0]
                          for x in self.arguments(fields["limits"]["rhs"], "range", 2)]
                initial = self.literal(fields["initial"]["rhs"], {"deg", "rad"})[0]
                _require(limits[0] <= limits[1] and limits[0] <= initial <= limits[1],
                         "reversed limits or initial outside inclusive limits")
                oid = _identity(owner["id"] + [member["key"]])
                path = _text(owner["path"] + "." + member["name"], "hinge path")
                _require(tuple(oid) not in ids and path not in paths, "duplicate hinge identity/path")
                ids.add(tuple(oid)); paths.add(path)
                records.append({
                    "id": oid, "definitionId": _identity(owner["definitionId"] + [member["key"]]),
                    "path": path, "name": member["name"], "key": member["key"], "kind": "hinge",
                    "ownerId": list(owner["id"]), "ownerDefinitionId": list(owner["definitionId"]),
                    "parentSiteId": parent["id"], "childSiteId": child["id"],
                    "parentSite": parent, "childSite": child,
                    "axis": axis, "limits": limits, "initial": initial,
                    "axisFrame": "parent-site", "sourceCompatibilityVerified": True,
                    "sourceOrigins": self.member_origins(member, fields, owner),
                })
        return {
            "schema": SCHEMA, "contract": CONTRACT, "kind": "source-hinges",
            "sourceHashes": self.hashes, "sourceBytes": {name: len(raw) for name, raw in self.files.items()},
            "sourceManifest": self.identity["sourceManifest"], "programRevision": self.identity["programRevision"],
            "records": records, "sites": list(self.sites.values()),
            "objects": [{"id": r["id"], "definitionId": r["definitionId"], "path": r["path"],
                         "origin": self.origin_tree(r["origin"])} for r in self.identity["records"]],
            "hingeCount": len(records), "siteCount": len(self.sites), "objectCount": len(self.contexts),
            "sourceAgreementVerified": False, "artifactAgreementVerified": False,
            "historicalInputsBound": False, "sitePosesEvaluated": False,
            "sourceValidityQualified": False, "completeC255Semantic": False,
            "acceptedRevisionQualified": False, "executionAllowed": False,
            "realTrialSuccess": None, "limits": NONCLAIMS.copy(),
        }


def _translate(exc):
    resource = {"SOURCE_SIZE", "TOKEN_LIMIT", "SOURCE_DEPTH", "DEFINITION_LIMIT", "ROOT_LIMIT", "OBJECT_LIMIT"}
    binding = {"IMPORT_BINDING", "DEPENDENCY"}
    unsupported = {"PROFILE", "SOURCE_CLOSURE", "KEY_PARAMETER", "KEY_INPUT"}
    code = getattr(exc, "code", None)
    if code in resource:
        category = "RESOURCE_LIMIT"
    elif code in binding:
        category = "INPUT_BINDING"
    elif code in unsupported or (code and code.startswith("UNSUPPORTED_")):
        category = "UNSUPPORTED_SOURCE_FORM"
    else:
        category = "MALFORMED"
    return Fault(category, "C257 " + str(code) + ": " + str(getattr(exc, "detail", type(exc).__name__)))


def observe_source_hinges(source_files):
    """Observe exactly supplied main.ok/hinges.ok bytes or refuse the whole input."""
    hashes, sizes = {}, {}
    if type(source_files) is dict:
        for name in ("main.ok", "hinges.ok"):
            raw = source_files.get(name)
            if type(raw) is bytes:
                sizes[name] = len(raw)
                if len(raw) <= MAX_SOURCE_BYTES:
                    hashes[name] = hashlib.sha256(raw).hexdigest()
    try:
        _require(type(source_files) is dict and set(source_files) == {"main.ok", "hinges.ok"},
                 "exact main.ok and hinges.ok closure required", "INPUT_BINDING")
        for name, raw in source_files.items():
            _require(type(raw) is bytes, "supplied source must be bytes: " + name)
            _require(0 < len(raw) <= MAX_SOURCE_BYTES, "source byte limit: " + name, "RESOURCE_LIMIT")
        return Source(source_files).observe()
    except Fault as exc:
        exc.sourceHashes, exc.sourceBytes = hashes, sizes
        raise
    except OSError as exc:
        fault = Fault("IO_ERROR", type(exc).__name__)
    except (UnicodeError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            ArithmeticError, RecursionError) as exc:
        fault = _translate(exc) if hasattr(exc, "code") else Fault("MALFORMED", type(exc).__name__)
    fault.sourceHashes, fault.sourceBytes = hashes, sizes
    raise fault
