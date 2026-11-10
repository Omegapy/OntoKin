"""Literal-only C191 source parser and finite, source-spanned validation."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re

from .common import Budget, Failure, PARTS, canonical_bytes, schema_check, sha256


@dataclass
class Token:
    text: str
    kind: str
    start: int
    end: int


@dataclass
class Value:
    value: object
    unit: str | None
    start: int
    end: int


@dataclass
class Field:
    name: Token
    value: Value


@dataclass
class Declaration:
    kind: str
    label: str
    key: Value
    fields: list[Field]


class Source:
    def __init__(self, path, data, budget, contract):
        self.path = Path(path)
        self.data = data
        self.sha = sha256(data)
        self.contract = contract
        self.budget = budget
        try:
            self.text = data.decode("utf8")
        except UnicodeDecodeError as exc:
            prefix = data[:exc.start].decode("utf8")
            line, column = prefix.count("\n") + 1, len(prefix.rsplit("\n", 1)[-1]) + 1
            span = {"path": self.path.name, "source_sha256": self.sha,
                    "start_byte": exc.start, "end_byte": exc.end,
                    "start_line": line, "start_column": column,
                    "end_line": line, "end_column": column + 1}
            raise Failure("E_PARSE", "Source is not UTF-8", span) from exc
        self.headers = {}
        self.declarations = []
        self.execution = []
        self.execution_range = None
        self.scene_fields = []

    def span(self, value):
        start, end = value if isinstance(value, tuple) else (value.start, value.end)
        a, b = self.text[:start], self.text[:end]
        return {"path": self.path.name, "source_sha256": self.sha,
                "start_byte": len(a.encode("utf8")), "end_byte": len(b.encode("utf8")),
                "start_line": a.count("\n") + 1, "start_column": len(a.rsplit("\n", 1)[-1]) + 1,
                "end_line": b.count("\n") + 1, "end_column": len(b.rsplit("\n", 1)[-1]) + 1}

    def fail(self, code, message, value):
        raise Failure(code, message, self.span(value))

    def prime_header_anchor(self, pattern):
        # Locate the bounded first statement before lexical work is charged.
        # The same token pattern skips comments and keeps quoted semicolons
        # inside their strings, so a comment cannot impersonate the header.
        offset, first = 0, None
        while offset < len(self.text):
            match = pattern.match(self.text, offset)
            if not match:
                return
            if match.lastgroup not in ("space", "comment"):
                if first is None:
                    if match.group() != "ontokin":
                        return
                    first = offset
                if match.group() == ";":
                    self.budget.anchor = self.span((first, match.end()))
                    return
            offset = match.end()

    def parse(self):
        if len(self.data) > self.contract["backend"]["limits"]["source_bytes"]:
            self.fail("E_RESOURCE_LIMIT", "Source byte ceiling exceeded", (0, min(len(self.text), 1)))
        pattern = re.compile(r'(?P<space>\s+)|(?P<comment>//[^\n]*)|(?P<string>"(?:[^"\\\r\n]|\\.)*")|(?P<number>-?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)|(?P<id>[A-Za-z_][A-Za-z0-9_]*)|(?P<symbol>[@;{}=\[\],/^])')
        self.prime_header_anchor(pattern)
        self.tokens = []
        offset = 0
        while offset < len(self.text):
            match = pattern.match(self.text, offset)
            if not match:
                self.fail("E_PARSE", "Unexpected source character", (offset, offset + 1))
            kind = match.lastgroup
            if kind not in ("space", "comment"):
                self.tokens.append(Token(match.group(), kind, offset, match.end()))
                self.budget.charge("source_tokens")
                if len(self.tokens) > self.contract["backend"]["limits"]["tokens"]:
                    raise Failure("E_RESOURCE_LIMIT", "Token ceiling exceeded", self.budget.anchor)
            offset = match.end()
        self.tokens.append(Token("<EOF>", "eof", len(self.text), len(self.text)))
        self.index = 0
        first = self.take("ontokin")
        self.headers["source_binding"] = self.value()
        last = self.take(";")
        self.header_range = (first.start, last.end)
        self.take("module")
        self.module_label = self.identifier().text
        self.take("@")
        self.module_key = self.value()
        self.take(";")
        for field in ("profile", "backend", "output"):
            self.take(field)
            self.headers[field] = self.value()
            self.take(";")
        if self.peek().text == "execution":
            begin = self.take("execution")
            self.execution = self.fields()
            self.execution_range = (begin.start, self.tokens[self.index - 1].end)
        self.take("scene")
        self.scene_label = self.identifier().text
        self.take("@")
        self.scene_key = self.value()
        self.take("{")
        while self.peek().text != "}":
            if self.peek().kind == "eof":
                self.fail("E_PARSE", "Expected scene closing brace", self.peek())
            if self.tokens[self.index + 1].text == "=":
                self.scene_fields.append(self.field())
            else:
                kind = self.identifier()
                label = self.identifier()
                self.take("@")
                key = self.value()
                self.declarations.append(Declaration(kind.text, label.text, key, self.fields()))
                if len(self.declarations) > self.contract["backend"]["limits"]["declarations"]:
                    self.fail("E_RESOURCE_LIMIT", "Declaration ceiling exceeded", self.execution_range or self.header_range)
        self.take("}")
        self.take("<EOF>")
        self.budget.anchor = self.span(self.execution_range or self.header_range)
        return self

    def peek(self):
        return self.tokens[self.index]

    def take(self, expected=None):
        token = self.peek()
        if expected is not None and token.text != expected:
            self.fail("E_PARSE", "Expected " + expected, token)
        self.index += 1
        return token

    def identifier(self):
        if self.peek().kind != "id":
            self.fail("E_PARSE", "Expected identifier", self.peek())
        return self.take()

    def fields(self):
        self.take("{")
        result = []
        while self.peek().text != "}":
            result.append(self.field())
        self.take("}")
        return result

    def field(self):
        name = self.identifier()
        self.take("=")
        value = self.value()
        self.take(";")
        return Field(name, value)

    def scalar(self):
        token = self.take()
        if token.kind == "number":
            number = float(token.text)
            if math.isfinite(number) and number.is_integer():
                number = int(number)
            return number, token
        if token.kind == "string":
            try:
                return json.loads(token.text), token
            except (ValueError, UnicodeError):
                self.fail("E_PARSE", "Malformed JSON string", token)
        self.fail("E_PARSE", "Expected a number or string literal", token)

    def value(self):
        start = self.peek().start
        unit = None
        if self.peek().text in ("true", "false"):
            token = self.take()
            return Value(token.text == "true", None, start, token.end)
        if self.peek().text == "[":
            self.take("[")
            values = [self.scalar()[0]]
            while self.peek().text == ",":
                self.take(",")
                values.append(self.scalar()[0])
            token = self.take("]")
            value = values
        else:
            value, token = self.scalar()
        if not isinstance(value, str) and self.peek().text == "[":
            self.take("[")
            units = []
            while self.peek().text != "]":
                if self.peek().kind not in ("id", "number") and self.peek().text not in ("/", "^"):
                    self.fail("E_PARSE", "Malformed unit", self.peek())
                units.append(self.take().text)
            token = self.take("]")
            unit = "".join(units)
        return Value(value, unit, start, token.end)

    def validate(self):
        allowed = {
            "execution": {"max_operations", "max_elapsed"},
            "scene": {"duration", "gravity"},
            "part": {"box", "color", "rotation", "at"},
            "body": {"part", "mass", "authority", "guide", "feed", "initial_velocity"},
            "collider": {"part", "owner", "shape", "box", "offset", "enabled", "friction", "restitution"},
            "follow": {"parent", "child", "offset", "rotation"},
        }
        groups = [("execution", self.execution), ("scene", self.scene_fields)]
        groups += [(d.kind, d.fields) for d in self.declarations]
        for kind, fields in groups:
            seen = set()
            if kind not in allowed:
                declaration = next(d for d in self.declarations if d.kind == kind)
                self.fail("E_FIELD", "Unknown declaration kind " + kind, declaration.key)
            for field in fields:
                self.budget.charge("source_field_checks")
                if field.name.text not in allowed[kind] or field.name.text in seen:
                    self.fail("E_FIELD", "Unknown or duplicate field " + field.name.text, field.name)
                seen.add(field.name.text)
        expected_bindings = {"source_binding": "c191-experimental-0.1", "profile": "guided-box-contact-0.1",
                             "backend": "blender-bullet-c190-0.1", "output": "glb-guided-contact-0.1"}
        for key, expected in expected_bindings.items():
            if self.headers[key].value != expected or self.headers[key].unit is not None:
                self.fail("E_BINDING", "Unsupported " + key, self.headers[key])
        seen = set()
        for declaration in self.declarations:
            key = declaration.key.value
            if (not isinstance(key, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,63}", key)
                    or key in seen):
                self.fail("E_ID", "Duplicate or malformed stable key", declaration.key)
            seen.add(key)
        self.by_key = {d.key.value: d for d in self.declarations}
        self.field_maps = {d.key.value: {f.name.text: f for f in d.fields} for d in self.declarations}
        scene = {f.name.text: f for f in self.scene_fields}
        execution = {f.name.text: f for f in self.execution}
        for declaration in self.declarations:
            fields = self.field_maps[declaration.key.value]
            required = allowed[declaration.kind] - ({"at"} if declaration.kind == "part" else set())
            if declaration.kind == "part" and not declaration.key.value.endswith("_shoe"):
                required = required | {"at"}
            if declaration.kind == "collider" and "owner" not in fields:
                self.fail("E_OWNERSHIP", "Collider has no owner", declaration.key)
            for field in sorted(required):
                if field not in fields:
                    self.fail("E_TYPE", "Missing required field " + field, declaration.key)
        for fields, required in ((scene, allowed["scene"]), (execution, allowed["execution"] if self.execution_range else set())):
            for name in sorted(required):
                if name not in fields:
                    self.fail("E_TYPE", "Missing required field " + name, self.scene_key)

        kinds = {
            "max_operations": (None, "number"), "max_elapsed": ("s", "number"),
            "duration": ("s", "number"), "gravity": ("m/s^2", 3), "box": ("mm", 3),
            "color": (None, 4), "rotation": (None, 4), "at": ("mm", 3),
            "part": (None, "string"), "mass": ("kg", "number"), "authority": (None, "string"),
            "guide": (None, "string"), "feed": ("mm/s", "number"),
            "initial_velocity": ("mm/s", 3), "owner": (None, "string"),
            "shape": (None, "string"), "offset": ("mm", 3), "enabled": (None, "boolean"),
            "friction": (None, "number"), "restitution": (None, "number"),
            "parent": (None, "string"), "child": (None, "string"),
        }
        for kind, fields in groups:
            for field in fields:
                value, unit = field.value.value, field.value.unit
                expected_unit, expected_type = kinds[field.name.text]
                if field.name.text == "owner" and isinstance(value, list):
                    self.fail("E_OWNERSHIP", "Collider owner must be exactly one key", field.value)
                numeric = lambda n: type(n) in (float, int) and math.isfinite(n)
                correct = (isinstance(value, str) if expected_type == "string" else
                           type(value) is bool if expected_type == "boolean" else
                           numeric(value) if expected_type == "number" else
                           isinstance(value, list) and len(value) == expected_type and all(numeric(v) for v in value))
                if not correct or unit != expected_unit:
                    self.fail("E_TYPE", "Literal type, width or unit is not admitted", field.value)
        for key in (self.module_key, self.scene_key):
            if not isinstance(key.value, str) or key.unit is not None:
                self.fail("E_TYPE", "Stable key must be a string", key)

        def field_value(declaration, name):
            return self.field_maps[declaration.key.value][name].value

        for declaration in self.declarations:
            refs = {"body": ("part",), "collider": ("part", "owner"), "follow": ("parent", "child")}.get(declaration.kind, ())
            for name in refs:
                value = field_value(declaration, name)
                if name == "owner" and value.value == "world":
                    continue
                expected_kind = "body" if name == "owner" else "part"
                if value.value not in self.by_key or self.by_key[value.value].kind != expected_kind:
                    self.fail("E_REFERENCE", "Missing or wrongly typed reference", value)
                self.budget.charge("source_reference_checks")
        body_owners = {}
        follows = {}
        for declaration in self.declarations:
            if declaration.kind == "body":
                value = field_value(declaration, "part")
                if value.value.endswith("_shoe") or value.value in body_owners:
                    self.fail("E_OWNERSHIP", "Part cannot own an additional moving mass", value)
                body_owners[value.value] = declaration.key.value
            if declaration.kind == "follow":
                value = field_value(declaration, "child")
                if value.value in follows:
                    self.fail("E_OWNERSHIP", "Part has multiple spatial parents", value)
                follows[value.value] = declaration
        for declaration in self.declarations:
            fields = self.field_maps[declaration.key.value]
            if declaration.kind == "collider":
                part = fields["part"].value.value
                expected_owner = "world"
                if part.endswith("_shoe"):
                    follow = follows.get(part)
                    parent = field_value(follow, "parent").value if follow else None
                    expected_owner = body_owners.get(parent)
                if fields["owner"].value.value != expected_owner:
                    self.fail("E_OWNERSHIP", "Collider is assigned to the wrong mass owner", fields["owner"].value)
            if declaration.kind == "body" and fields["authority"].value.value != "solver":
                self.fail("E_AUTHORITY", "Carriage has a competing motion authority", fields["authority"].value)
            if declaration.kind == "part" and declaration.key.value.endswith("_shoe") and "at" in fields:
                self.fail("E_AUTHORITY", "A followed shoe has no independent placement", fields["at"].name)
        for declaration in self.declarations:
            fields = self.field_maps[declaration.key.value]
            for field, expected, code in (("shape", "box", "E_SHAPE"), ("guide", "world_x", "E_GUIDE"),
                                          ("rotation", [1, 0, 0, 0], "E_ROTATION"),
                                          ("friction", 0, "E_CONTACT_LAW"), ("restitution", 0, "E_CONTACT_LAW")):
                if field in fields and fields[field].value.value != expected:
                    self.fail(code, "Unsupported " + field, fields[field].value)
        if scene["gravity"].value.value != [0, 0, 0]:
            self.fail("E_CONTACT_LAW", "Nonzero gravity is unqualified", scene["gravity"].value)

        normalized_names = {"box": "box_mm", "at": "at_mm", "rotation": "rotation_wxyz", "color": "color_linear_rgba",
                            "mass": "mass_kg", "feed": "feed_mm_s", "initial_velocity": "initial_velocity_mm_s", "offset": "offset_mm"}
        canonical = {k: value.value for k, value in self.headers.items()}
        canonical.update(module_key=self.module_key.value, scene_key=self.scene_key.value,
                         backend_sha256=self.contract["backend_sha256"], duration_s=scene["duration"].value.value,
                         gravity_m_s2=scene["gravity"].value.value)
        for kind, collection in (("part", "parts"), ("body", "bodies"), ("collider", "colliders"), ("follow", "follows")):
            canonical[collection] = {d.key.value: {normalized_names.get(f.name.text, f.name.text): f.value.value for f in d.fields}
                                     for d in self.declarations if d.kind == kind}
        origins = {}
        for key, part in canonical["parts"].items():
            if "at_mm" in part:
                origins[key] = part["at_mm"]
        for follow in canonical["follows"].values():
            if follow["parent"] in origins:
                origins[follow["child"]] = [a + b for a, b in zip(origins[follow["parent"]], follow["offset_mm"])]
        if all(key in origins and key in canonical["parts"] for key in PARTS):
            for i, a in enumerate(PARTS):
                for b in PARTS[i + 1:]:
                    self.budget.charge("initial_pair_checks")
                    if all(min(origins[a][axis] + canonical["parts"][a]["box_mm"][axis],
                               origins[b][axis] + canonical["parts"][b]["box_mm"][axis]) > max(origins[a][axis], origins[b][axis])
                           for axis in range(3)):
                        target = b if "at" in self.field_maps[b] else a
                        field = self.field_maps[target].get("at", self.field_maps[target]["box"])
                        self.fail("E_INITIAL_OVERLAP", f"Initial boxes overlap: {a}, {b}", field.value)
        source_schema = self.contract["source_schema"]["properties"]
        for key, value in (("module_key", self.module_key), ("scene_key", self.scene_key), ("duration_s", scene["duration"].value)):
            try:
                schema_check(value.value, source_schema[key], budget=self.budget)
            except ValueError as exc:
                self.fail("E_SCOPE", str(exc), value)
        for kind, collection in (("part", "parts"), ("body", "bodies"), ("collider", "colliders"), ("follow", "follows")):
            expected = source_schema[collection]["properties"]
            if set(canonical[collection]) != set(expected):
                self.fail("E_SCOPE", "Declaration ID set is outside this finite assembly", self.scene_key)
            for declaration in self.declarations:
                if declaration.kind != kind:
                    continue
                rules = expected[declaration.key.value]["properties"]
                for field in declaration.fields:
                    name = normalized_names.get(field.name.text, field.name.text)
                    try:
                        schema_check(field.value.value, rules[name], budget=self.budget)
                    except (ValueError, KeyError) as exc:
                        self.fail("E_SCOPE", str(exc), field.value)
        if len(self.declarations) != self.contract["backend"]["limits"]["declarations"]:
            self.fail("E_SCOPE", "Exactly fifteen declarations are required", self.scene_key)
        operations = execution["max_operations"].value.value if execution else 100000
        elapsed = execution["max_elapsed"].value.value * 1000 if execution else 30000
        if type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed == int(elapsed):
            elapsed = int(elapsed)
        self.budget.authorize(operations, elapsed,
                              self.span(execution["max_operations"].value) if execution else self.span(self.header_range),
                              self.span(execution["max_elapsed"].value) if execution else self.span(self.header_range))
        canonical["execution"] = {"max_operations": operations, "max_elapsed_ms": elapsed}
        schema_check(canonical, self.contract["source_schema"], budget=self.budget)
        self.canonical = canonical
        self.canonical_bytes = canonical_bytes(canonical)
        self.canonical_sha = sha256(self.canonical_bytes)
        self.source_manifest = {
            "source_sha256": self.sha, "source_bytes": len(self.data), "source_path": self.path.name,
            "canonical_input_sha256": self.canonical_sha,
            "contract_manifest_sha256": sha256((self.contract_path / "CONTRACT-FILES.json").read_bytes()) if hasattr(self, "contract_path") else "bc85696002d641122322313cf5167f84eb1ae377599930112e3afd0f054b0137",
            "dependency_closure": self.contract["dependency_closure"],
            "module_label": self.module_label, "scene_label": self.scene_label,
            "occurrences": [{"id": d.key.value, "kind": d.kind, "label": d.label,
                             "occurrence": f"{self.module_key.value}/{self.scene_key.value}/{d.key.value}",
                             "span": self.span(d.key), "fields": {f.name.text: self.span(f.value) for f in d.fields}}
                            for d in self.declarations],
        }
        return self
