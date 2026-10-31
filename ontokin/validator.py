"""Core-0.1 binding, type checking, pure elaboration, and relation validation.

This module validates source constructs, not conformance fixture identities. The
runtime separately checks admission and event transitions at their authored
times, preserving those diagnostic phases even when run as a preflight.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Any

from .diagnostics import Diagnostic, OntoKinError
from .model import (ActionModel, Event, EventBlock, FollowModel, JointModel,
                    ObjectModel, Pose, SceneModel, SiteModel)
from .values import (ACCELERATION, ALIASES, ANGLE, ANGULAR_SPEED, BOOL, INT,
                     LENGTH, MASS, REAL, SPEED, STRING, TIME, UNKNOWN, ZERO,
                     Type, Value, binary, canonical, checked_int, coerce, common,
                     finite, literal, numeric, quantity_type, rounded, scalar,
                     unary, units, widen)


BUILTIN_TYPES = {
    "Int", "Real", "Bool", "String", "Point3", "Rotation", "Pose", "Color",
    "Geometry", "BodyModel", "MotionMode", "CollisionMode", "FrameRef",
    "SiteRef", "JointRef", "Action", "Object", "Quantity", "Vec3", "Vector3", "Range", "Ref",
} | set(ALIASES)
BUILTIN_CALLS = {
    "real", "abs", "min", "max", "near", "sqrt", "sin", "cos", "vec3", "vector", "point",
    "quat", "axis_angle", "pose", "range", "rgba", "empty", "sphere", "box", "no_body",
    "sphere_body", "move", "spin", "tween",
}
PREDEFINED = BUILTIN_TYPES | BUILTIN_CALLS | {"self", "world", "static", "prescribed", "dynamic", "disabled"}
FIELD_TYPES = {
    "role": STRING, "geometry": Type("Geometry"), "appearance": Type("Color"),
    "physical": Type("BodyModel"), "motion": Type("MotionMode"),
    "collision": Type("CollisionMode"), "placement": Type("Pose"),
    "velocity": Type("Vector3", element=quantity_type(SPEED)),
    "omega": Type("Vector3", element=quantity_type(ANGULAR_SPEED)),
}
READONLY_FIELDS = {"frame", "origin"}
KEY_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


def fail(code: str, message: str, node: Any = None, *, phase: str = "elaboration",
         details: dict | None = None, repair: str | None = None) -> None:
    raise OntoKinError(code, message, node, phase=phase,
                      category="unsupported" if code == "OKL-E-CAPABILITY-UNSUPPORTED" else "resource_limit" if code == "OKL-E-RESOURCE" else "invalid",
                      details=details,
                      repair=repair or "Revise the indicated declaration or expression to satisfy the stated core rule.")


def optional(node: Any, key: str, default: Any = None) -> Any:
    return node.data.get(key, default) if node is not None else default


@dataclass
class Member:
    node: Any
    declaring: str


@dataclass
class EffectiveClass:
    name: str
    node: Any
    base: str | None
    members: dict[str, Member] = field(default_factory=dict)
    defaults: dict[str, tuple[Any, str]] = field(default_factory=dict)


@dataclass
class Context:
    self_path: str | None = None
    self_type: str | None = None
    lexical_class: str | None = None
    locals: dict[str, Value] = field(default_factory=dict)
    abstract: bool = False
    call_owner: str | None = None
    scene: bool = False
    geometry_owner: str | None = None


@dataclass
class BoundExpression:
    expression: Any
    context: Context


@dataclass
class Instance:
    model: ObjectModel
    cls: EffectiveClass
    overrides: dict[str, BoundExpression] = field(default_factory=dict)


@dataclass
class Callable:
    node: Any
    name: str
    self_path: str | None = None
    self_type: str | None = None
    lexical_class: str | None = None


class Validator:
    def __init__(self, program: Any, level: str):
        self.program, self.level = program, level
        scene = program.scene
        self.model = SceneModel(program.module_name, program.module_key, scene.name, scene.key,
                                profile=program.profile, span=scene)
        self.class_nodes: dict[str, Any] = {}
        self.classes = {"Object": EffectiveClass("Object", None, None)}
        self.functions: dict[str, Any] = {}
        self.instances: dict[str, Instance] = {}
        self.scene_names: dict[str, Any] = {}
        self.sites: dict[str, tuple[Any, Context, tuple[str, ...], str]] = {}
        self.joints: dict[str, tuple[Any, Context, tuple[str, ...]]] = {}
        self.follows: dict[str, tuple[Any, Context, tuple[str, ...]]] = {}
        self.actions: dict[str, Any] = {}
        self.memo: dict[tuple[str, str], Value] = {}
        self.pending: list[tuple[str, str]] = []
        self.call_stack: list[tuple[str, str | None]] = []
        self.call_edges: dict[str, set[str]] = {}
        self.class_stack: list[str] = []
        self.initializers: list[tuple[str, list[Any], Context]] = []
        self.placement_reads: list[tuple[str, Any]] = []
        self._warning_spans: set[tuple[int, int]] = set()

    def warning(self, node: Any) -> None:
        span = (node.start, node.end) if node else (-1, -1)
        if span not in self._warning_spans:
            self._warning_spans.add(span)
            self.model.diagnostics.append(Diagnostic("OKL-W-UNDERFLOW", "A numeric result underflowed to a subnormal value or zero.",
                                                     node, phase="elaboration"))

    def key(self, node: Any, key: str) -> None:
        if not KEY_RE.fullmatch(key):
            fail("OKL-E-ID", "Stable keys must contain 1–64 ASCII letters, digits, '.', '_', or '-', and begin with a letter or digit.", node, phase="binding")

    def initializer_type(self, class_name: str, names: list[str], node: Any) -> Type:
        cls = self.effective(class_name)
        for name in names[:-1]:
            member = cls.members.get(name)
            if not member or member.node.kind != "part":
                fail("OKL-E-NAME", f"'{name}' is not an owned part in this initializer path.", node, phase="binding")
            if member.node.visibility != "public":
                fail("OKL-E-ACCESS", f"Part '{name}' is private.", node, phase="binding")
            cls = self.effective(member.node.class_name)
        name = names[-1]
        member = cls.members.get(name)
        if name in READONLY_FIELDS or member and member.node.kind == "derive":
            fail("OKL-E-READONLY", f"'{name}' is read-only and cannot be assigned.", node, phase="type")
        if member:
            if member.node.visibility != "public":
                fail("OKL-E-ACCESS", f"Parameter '{name}' is private.", node, phase="binding")
            if member.node.kind != "param":
                fail("OKL-E-READONLY", f"'{name}' is not a writable parameter.", node, phase="type")
            return self.parse_type(member.node.type)
        if len(names) == 1 and name in FIELD_TYPES:
            return FIELD_TYPES[name]
        fail("OKL-E-NAME", f"Initializer cannot assign '{'.'.join(names)}'; nested writes must end in a public parameter.", node, phase="binding")

    def unique(self, nodes: list[Any], *, inherited: dict[str, Member] | None = None) -> None:
        names: set[str] = set()
        keys: set[str] = set()
        for node in nodes:
            name, key = node.name, node.key
            self.key(node, key)
            if name in PREDEFINED or name in names:
                fail("OKL-E-NAME", f"Name '{name}' is predefined or duplicated in this scope.", node, phase="binding")
            if key in keys:
                fail("OKL-E-ID", f"Stable key '{key}' is reused in this scope.", node, phase="binding")
            names.add(name); keys.add(key)

    def parse_type(self, node: Any) -> Type:
        name, args = node.name, optional(node, "args", [])
        if name == "Quantity":
            if args or optional(node, "unit") is None:
                fail("OKL-E-TYPE", "Quantity requires a unit expression in brackets.", node, phase="type")
            return quantity_type(units(node.unit, node)[0])
        if name in ("Vec3", "Vector3", "Range"):
            if len(args) != 1:
                fail("OKL-E-TYPE", f"{name} requires exactly one scalar type argument.", node, phase="type")
            element = self.parse_type(args[0])
            if not numeric(element):
                fail("OKL-E-TYPE", f"{name} requires a numeric scalar or quantity element type.", node, phase="type")
            return Type(name, element=element)
        if name == "Ref":
            if len(args) != 1 or optional(args[0], "args", []) or args[0].name not in self.class_nodes and args[0].name != "Object":
                fail("OKL-E-TYPE", "Ref requires exactly one declared nominal class.", node, phase="type")
            return Type("Ref", name=args[0].name)
        if args:
            fail("OKL-E-TYPE", f"Type '{name}' does not accept type arguments.", node, phase="type")
        if name in ALIASES:
            return quantity_type(ALIASES[name])
        if name in self.class_nodes or name == "Object":
            return Type("Ref", name=name)
        if name in BUILTIN_TYPES:
            return Type("Point3", element=quantity_type(LENGTH)) if name == "Point3" else Type(name)
        fail("OKL-E-NAME", f"Unknown type '{name}'.", node, phase="binding")

    def subtype(self, child: str, parent: str) -> bool:
        while child:
            if child == parent:
                return True
            child = self.effective(child).base
        return False

    def expect(self, value: Value, typ: Type, node: Any) -> Value:
        return coerce(value, typ, node, self.subtype)

    def signature(self, node: Any) -> tuple:
        names = []
        params = []
        for param in node.params:
            if param.name in PREDEFINED or param.name in names:
                fail("OKL-E-NAME", f"Parameter '{param.name}' is duplicated or shadows a predefined symbol.", param, phase="binding")
            names.append(param.name)
            params.append((param.name, self.parse_type(param.type)))
        return tuple(params), self.parse_type(node.return_type), optional(node, "visibility", "public")

    def effective(self, name: str) -> EffectiveClass:
        if name in self.classes:
            return self.classes[name]
        if name not in self.class_nodes:
            fail("OKL-E-NAME", f"Unknown class '{name}'.", self.program, phase="binding")
        node = self.class_nodes[name]
        if name in self.class_stack:
            fail("OKL-E-INHERITANCE-CYCLE", "Nominal inheritance contains a cycle: " + " -> ".join(self.class_stack + [name]), node)
        self.class_stack.append(name)
        base = optional(node, "base") or "Object"
        parent = self.effective(base)
        cls = EffectiveClass(name, node, base, dict(parent.members), dict(parent.defaults))
        local_names: set[str] = set()
        effective_keys = {m.node.key: n for n, m in parent.members.items()}
        local_defaults: set[str] = set()
        for member in node.members:
            kind = member.kind
            if kind == "assert":
                continue
            if kind in ("assign", "override_default"):
                target = member.name if kind == "override_default" else member.path[0]
                if kind == "assign" and len(member.path) != 1:
                    fail("OKL-E-NAME", "Class defaults require a bare built-in field.", member, phase="binding")
                if target in local_defaults:
                    fail("OKL-E-NAME", f"Default '{target}' is assigned twice in this class.", member, phase="binding")
                local_defaults.add(target)
                if kind == "assign":
                    if target in READONLY_FIELDS or target in cls.members and cls.members[target].node.kind == "derive":
                        fail("OKL-E-READONLY", f"'{target}' is read-only.", member, phase="type")
                    if target not in FIELD_TYPES:
                        fail("OKL-E-NAME", f"'{target}' is not an assignable built-in class field.", member, phase="binding")
                    if target in parent.defaults:
                        fail("OKL-E-OVERRIDE", f"Inherited default '{target}' requires an explicit override.", member, phase="type")
                else:
                    inherited_member = parent.members.get(target)
                    if inherited_member:
                        if inherited_member.node.kind == "derive":
                            fail("OKL-E-READONLY", f"Derived property '{target}' cannot be overridden.", member, phase="type")
                        if inherited_member.node.kind != "param" or inherited_member.node.visibility != "public":
                            fail("OKL-E-OVERRIDE", f"'{target}' is not an overridable public inherited parameter.", member, phase="type")
                    elif target not in FIELD_TYPES or target not in parent.defaults:
                        fail("OKL-E-OVERRIDE", f"No explicit inherited default named '{target}' can be overridden.", member, phase="type")
                cls.defaults[target] = (member.value, name)
                continue
            self.key(member, member.key)
            if member.name in PREDEFINED or member.name in FIELD_TYPES or member.name in READONLY_FIELDS or member.name in local_names:
                fail("OKL-E-NAME", f"Member name '{member.name}' is predefined or duplicated.", member, phase="binding")
            local_names.add(member.name)
            old = parent.members.get(member.name)
            if old:
                if kind != "method" or not optional(member, "override", False) or old.node.kind != "method":
                    fail("OKL-E-OVERRIDE", f"Inherited member '{member.name}' requires a compatible method override.", member, phase="type")
                if old.node.visibility == "private" or self.signature(member) != self.signature(old.node) or member.key != old.node.key:
                    fail("OKL-E-OVERRIDE", f"Override '{member.name}' must retain its public signature, visibility, and key.", member, phase="type")
            elif optional(member, "override", False):
                fail("OKL-E-OVERRIDE", f"Method '{member.name}' has no inherited method to override.", member, phase="type")
            if member.key in effective_keys and effective_keys[member.key] != member.name:
                fail("OKL-E-ID", f"Member key '{member.key}' is reused by '{effective_keys[member.key]}' and '{member.name}'.", member, phase="binding")
            effective_keys[member.key] = member.name
            if kind in ("joint", "follow") and optional(member, "visibility") not in ("public", "private"):
                fail("OKL-E-NAME", "Class relations require explicit public or private visibility.", member, phase="binding")
            if kind in ("param", "derive"):
                self.parse_type(member.type)
                cls.defaults[member.name] = (member.value, name)
            elif kind == "method":
                self.signature(member)
            elif kind == "part":
                if member.class_name not in self.class_nodes and member.class_name != "Object":
                    fail("OKL-E-NAME", f"Unknown part class '{member.class_name}'.", member, phase="binding")
            elif kind not in ("joint", "follow", "site"):
                fail("OKL-E-NAME", f"Unsupported class member kind '{kind}'.", member, phase="binding")
            cls.members[member.name] = Member(member, name)
        self.class_stack.pop()
        self.classes[name] = cls
        return cls

    def bind(self) -> None:
        self.key(self.program, self.program.module_key)
        self.key(self.program.scene, self.program.scene.key)
        if self.program.scene.key == "definitions":
            fail("OKL-E-ID", "The scene key 'definitions' is reserved for definition records.", self.program.scene, phase="binding")
        definitions = self.program.classes + self.program.functions
        self.unique(definitions)
        self.class_nodes = {node.name: node for node in self.program.classes}
        self.functions = {node.name: node for node in self.program.functions}
        for name in self.class_nodes:
            self.effective(name)
        for node in self.functions.values():
            self.signature(node)
        declarations = [n for n in self.program.scene.members if n.kind in ("object", "joint", "follow", "action")]
        self.unique(declarations)
        self.scene_names = {n.name: n for n in declarations}
        for node in declarations:
            if node.kind in ("joint", "follow") and optional(node, "visibility") is not None:
                fail("OKL-E-NAME", "Scene relations cannot have a visibility modifier.", node, phase="binding")
        self.check_composition()

    def check_composition(self) -> None:
        visiting, done = [], set()
        def visit(name: str) -> None:
            if name in visiting:
                fail("OKL-E-RECURSIVE-COMPOSITION", "Part expansion is recursive: " + " -> ".join(visiting + [name]), self.effective(name).node)
            if name in done:
                return
            visiting.append(name)
            for member in self.effective(name).members.values():
                if member.node.kind == "part":
                    visit(member.node.class_name)
            visiting.pop(); done.add(name)
        for name in self.classes:
            visit(name)

    def expand(self, node: Any, path: str, owner: str | None, ids: tuple[str, ...], context: Context) -> None:
        if len(self.instances) >= 10000:
            fail("OKL-E-RESOURCE", "Object expansion reached the reference implementation's 10,000-instance budget.", node)
        cls = self.effective(node.class_name)
        model = ObjectModel(path, node.name, node.class_name, ids, owner=owner, role=node.key, span=node)
        self.instances[path] = Instance(model, cls)
        self.model.objects[path] = model
        self.model.sites[path + ".origin"] = SiteModel(path + ".origin", ids + ("@system", "origin"), path,
                                                     Pose(path + ".frame"), span=node)
        self.initializers.append((path, node.assignments, context))
        for name, member in cls.members.items():
            child = member.node
            scope = Context(path, cls.name, member.declaring)
            member_path = path + "." + name
            member_id = ids + (child.key,)
            if child.kind == "part":
                self.expand(child, member_path, path, member_id, scope)
            elif child.kind == "site":
                self.sites[member_path] = (child, scope, member_id, path)
            elif child.kind == "joint":
                self.joints[member_path] = (child, scope, member_id)
            elif child.kind == "follow":
                self.follows[member_path] = (child, scope, member_id)

    def apply_initializers(self) -> None:
        for path, assignments, ctx in sorted(self.initializers, key=lambda entry: entry[0].count("."), reverse=True):
            written = set()
            for node in assignments:
                names = node.path
                token = tuple(names)
                if token in written:
                    fail("OKL-E-NAME", f"Initializer target '{'.'.join(names)}' is assigned more than once.", node, phase="binding")
                written.add(token)
                target = self.instances[path]
                target_path = path
                for name in names[:-1]:
                    member = target.cls.members.get(name)
                    if not member or member.node.kind != "part":
                        fail("OKL-E-NAME", f"'{name}' is not an owned part in this initializer path.", node, phase="binding")
                    if member.node.visibility != "public":
                        fail("OKL-E-ACCESS", f"Part '{name}' is private.", node, phase="binding")
                    target_path += "." + name
                    target = self.instances[target_path]
                name = names[-1]
                member = target.cls.members.get(name)
                if member and member.node.kind == "derive" or name in READONLY_FIELDS:
                    fail("OKL-E-READONLY", f"'{name}' is read-only and cannot be assigned.", node, phase="type")
                if member:
                    if member.node.visibility != "public":
                        fail("OKL-E-ACCESS", f"Parameter '{name}' is private.", node, phase="binding")
                    if member.node.kind != "param":
                        fail("OKL-E-READONLY", f"'{name}' is not a writable parameter.", node, phase="type")
                elif name not in FIELD_TYPES or len(names) != 1:
                    fail("OKL-E-NAME", f"Initializer cannot assign '{'.'.join(names)}'; nested writes must end in a public parameter.", node, phase="binding")
                target.overrides[name] = BoundExpression(node.value, ctx)

    def guarded(self, key: tuple[str, str], node: Any, compute) -> Value:
        if key in self.memo:
            return self.memo[key]
        if key in self.pending:
            path = " -> ".join(f"{a}.{b}" for a, b in self.pending + [key])
            fail("OKL-E-DEPENDENCY-CYCLE", f"Pure value dependencies form a cycle: {path}.", node)
        self.pending.append(key)
        try:
            result = compute()
            self.memo[key] = result
            return result
        finally:
            self.pending.pop()

    def default_field(self, path: str, name: str) -> Value:
        if name == "role": return Value(STRING, self.instances[path].model.role)
        if name == "geometry": return Value(Type("Geometry"), {"kind": "empty"})
        if name == "appearance": return Value(Type("Color"), (0.5, 0.5, 0.5, 1.0))
        if name == "physical": return Value(Type("BodyModel"), {"kind": "no_body"})
        if name == "motion": return Value(Type("MotionMode"), "prescribed")
        if name == "collision": return Value(Type("CollisionMode"), "disabled")
        if name == "placement": return Value(Type("Pose"), Pose())
        dim = SPEED if name == "velocity" else ANGULAR_SPEED
        return Value(Type("Vector3", element=quantity_type(dim)), tuple(scalar(0, dim) for _ in range(3)), "world")

    def field(self, path: str, name: str, node: Any = None) -> Value:
        instance = self.instances[path]
        member = instance.cls.members.get(name)
        def compute() -> Value:
            # A completed guarded binding already retains its checked type.
            # Resolve the declaration only when constructing that binding;
            # every later read still passes through guarded() for dependency,
            # generated-shape and request-budget checks.
            typ = self.parse_type(member.node.type) if member else FIELD_TYPES[name]
            if name in instance.overrides:
                bound = instance.overrides[name]
                expression, ctx = bound.expression, bound.context
            elif name in instance.cls.defaults:
                expression, declaring = instance.cls.defaults[name]
                ctx = Context(path, instance.cls.name, declaring)
            else:
                return self.default_field(path, name)
            return self.expect(self.expression(expression, ctx), typ, expression)
        try:
            return self.guarded((path, name), node or instance.model.span, compute)
        except OntoKinError as error:
            if error.diagnostic.element_id is None:
                ids = instance.model.element_id + ((member.node.key,) if member else ())
                error.diagnostic.element_id = list(ids)
            raise

    def access(self, member: Member, ctx: Context, node: Any) -> None:
        if optional(member.node, "visibility") == "private" and ctx.lexical_class != member.declaring:
            fail("OKL-E-ACCESS", f"Member '{member.node.name}' is private to class '{member.declaring}'.", node, phase="binding")

    def name(self, name: str, ctx: Context, node: Any) -> Value:
        if name in ctx.locals:
            return ctx.locals[name]
        if name == "self":
            if ctx.self_type is None:
                fail("OKL-E-NAME", "'self' is only available in its class lexical scope.", node, phase="binding")
            return Value(Type("Ref", name=ctx.self_type), ctx.self_path if ctx.self_path is not None else UNKNOWN)
        if name == "world":
            return Value(Type("FrameRef"), "world")
        if name in ("static", "prescribed", "dynamic"):
            return Value(Type("MotionMode"), name)
        if name == "disabled":
            return Value(Type("CollisionMode"), name)
        if name in BUILTIN_CALLS:
            return Value(Type("BuiltinCallable"), name)
        if name in self.functions:
            return Value(Type("Callable"), Callable(self.functions[name], "fn:" + name))
        if name in self.classes:
            return Value(Type("ClassName"), name)
        if ctx.scene and name in self.scene_names:
            declaration = self.scene_names[name]
            if declaration.kind == "object":
                return Value(Type("Ref", name=declaration.class_name), name)
            if declaration.kind == "joint":
                return Value(Type("JointRef"), name, hint=declaration.joint_type)
            if declaration.kind == "follow":
                fail("OKL-E-TYPE", "Follow declarations have no source value type in core-0.1.", node, phase="type")
            if declaration.kind == "action":
                if ctx.abstract:
                    return Value(Type("Action"))
                return self.action_value(name)
        fail("OKL-E-NAME", f"Unknown name '{name}' in this lexical scope.", node, phase="binding")

    def member(self, value: Value, name: str, ctx: Context, node: Any) -> Value:
        typ = value.type
        if typ.kind == "Ref":
            actual_path = value.value if value.known else None
            cls = self.instances[actual_path].cls if actual_path is not None else self.effective(typ.name)
            if name == "frame":
                return Value(Type("FrameRef"), actual_path + ".frame" if actual_path is not None else UNKNOWN)
            if name == "origin":
                return Value(Type("SiteRef"), actual_path + ".origin" if actual_path is not None else UNKNOWN)
            if name in FIELD_TYPES:
                if ctx.abstract or actual_path is None:
                    return Value(FIELD_TYPES[name])
                if name == "placement":
                    self.placement_reads.append((actual_path, node))
                return self.field(actual_path, name, node)
            member = cls.members.get(name)
            if member is None:
                fail("OKL-E-NAME", f"Class '{cls.name}' has no member '{name}'.", node, phase="binding")
            self.access(member, ctx, node)
            declaration = member.node
            if declaration.kind in ("param", "derive"):
                if ctx.abstract or actual_path is None:
                    return Value(self.parse_type(declaration.type))
                return self.field(actual_path, name, node)
            if declaration.kind == "method":
                return Value(Type("Callable"), Callable(declaration, "method:" + member.declaring + "." + name,
                                                         actual_path, cls.name, member.declaring))
            member_path = actual_path + "." + name if actual_path is not None else UNKNOWN
            if declaration.kind == "part":
                return Value(Type("Ref", name=declaration.class_name), member_path)
            if declaration.kind in ("site", "joint"):
                return Value(Type("SiteRef" if declaration.kind == "site" else "JointRef"), member_path,
                             hint=declaration.joint_type if declaration.kind == "joint" else None)
            fail("OKL-E-TYPE", f"Member '{name}' has no source value type.", node, phase="type")
        if typ.kind in ("Vec3", "Vector3", "Point3"):
            if name in ("x", "y", "z"):
                return value.value[("x", "y", "z").index(name)] if value.known else Value(typ.element)
            if name == "frame" and typ.kind in ("Vector3", "Point3"):
                return Value(Type("FrameRef"), value.frame if value.frame is not None else UNKNOWN)
        elif typ.kind == "Rotation" and name in ("w", "x", "y", "z"):
            return Value(REAL, value.value[("w", "x", "y", "z").index(name)]) if value.known else Value(REAL)
        elif typ.kind == "Pose":
            if name == "frame":
                return Value(Type("FrameRef"), value.value.frame) if value.known else Value(Type("FrameRef"))
            if name == "position":
                result_type = Type("Vec3", element=quantity_type(LENGTH))
                return Value(result_type, tuple(scalar(x, LENGTH) for x in value.value.position)) if value.known else Value(result_type)
            if name == "rotation":
                return Value(Type("Rotation"), value.value.rotation) if value.known else Value(Type("Rotation"))
        elif typ.kind == "Range" and name in ("lower", "upper"):
            return value.value[0 if name == "lower" else 1] if value.known else Value(typ.element)
        elif typ.kind == "Color" and name in ("r", "g", "b", "a"):
            return Value(REAL, value.value[("r", "g", "b", "a").index(name)]) if value.known else Value(REAL)
        elif typ.kind == "SiteRef":
            fields = {"frame": Type("FrameRef"), "pose": Type("Pose"), "interface": STRING, "size": quantity_type(LENGTH)}
            if name in fields:
                if ctx.abstract or not value.known:
                    return Value(fields[name])
                site = self.resolve_site(value.value)
                data = site.path + ".frame" if name == "frame" else getattr(site, name)
                return Value(fields[name], data)
        elif typ.kind == "JointRef":
            if name in ("parent", "child", "axis", "limits", "initial"):
                joint_type = value.hint
                if value.known and value.value in self.joints:
                    joint_type = self.joints[value.value][0].joint_type
                field_type = Type("SiteRef") if name in ("parent", "child") else Type("Vec3", element=REAL) if name == "axis" else quantity_type(ANGLE if joint_type == "hinge" else LENGTH)
                if name == "limits":
                    field_type = Type("Range", element=field_type)
                if name in ("axis", "limits", "initial") and joint_type in ("grip", "fixed"):
                    fail("OKL-E-NAME", f"A {joint_type} joint has no '{name}' field.", node, phase="binding")
                if ctx.abstract or not value.known:
                    return Value(field_type)
                joint = self.resolve_joint(value.value)
                if name in ("parent", "child"):
                    return Value(field_type, getattr(joint, name))
                if name == "axis":
                    return Value(field_type, tuple(Value(REAL, x) for x in joint.axis))
                if name == "limits":
                    return Value(field_type, tuple(scalar(x, ANGLE if joint.kind == "hinge" else LENGTH) for x in joint.limits))
                return scalar(joint.initial, ANGLE if joint.kind == "hinge" else LENGTH)
        fail("OKL-E-NAME", f"Type '{typ}' has no accessible field '{name}'.", node, phase="binding")

    def expression(self, node: Any, ctx: Context) -> Value:
        kind = node.kind
        if kind == "number":
            unit = optional(node, "unit")
            if ctx.abstract:
                typ = quantity_type(units(unit, node)[0]) if unit is not None else INT if "." not in node.text and "e" not in node.text.lower() else REAL
                return Value(typ)
            return literal(node.text, unit, node, warn=self.warning)
        if kind == "string":
            return Value(STRING, node.value)
        if kind == "bool":
            return Value(BOOL, node.value)
        if kind == "name":
            return self.name(node.name, ctx, node)
        if kind == "member":
            return self.member(self.expression(node.target, ctx), node.name, ctx, node)
        if kind == "call":
            callee = self.expression(node.callee, ctx)
            args = [self.expression(arg, ctx) for arg in node.args]
            if callee.type.kind == "BuiltinCallable":
                return self.builtin(callee.value, args, node, ctx)
            if callee.type.kind != "Callable":
                fail("OKL-E-TYPE", f"A value of type {callee.type} is not callable; classes are instantiated with object/part declarations.", node, phase="type")
            return self.invoke(callee.value, args, node, ctx)
        if kind == "unary":
            if not ctx.abstract and node.op == "-" and node.value.kind == "number":
                return literal(node.value.text, optional(node.value, "unit"), node, negative=True, warn=self.warning)
            return unary(node.op, self.expression(node.value, ctx), node)
        if kind == "binary":
            left = self.expression(node.left, ctx)
            if not ctx.abstract and node.op in ("and", "or"):
                self.expect(left, BOOL, node.left)
                if (node.op == "and" and not left.value) or (node.op == "or" and left.value):
                    return left
            right = self.expression(node.right, ctx)
            if node.op in ("==", "!=") and left.type.kind == right.type.kind == "Ref" and left.type != right.type:
                if self.subtype(left.type.name, right.type.name):
                    left = self.expect(left, right.type, node.left)
                elif self.subtype(right.type.name, left.type.name):
                    right = self.expect(right, left.type, node.right)
            return binary(node.op, left, right, node, self.warning)
        if kind == "conditional":
            condition = self.expect(self.expression(node.condition, ctx), BOOL, node.condition)
            if ctx.abstract:
                a = self.expression(node.then, ctx)
                b = self.expression(node.otherwise, ctx)
                if a.type.kind == b.type.kind == "Ref":
                    if self.subtype(a.type.name, b.type.name): return Value(b.type)
                    if self.subtype(b.type.name, a.type.name): return Value(a.type)
                _, _, typ = common(a, b, node)
                if a.frame is not None and b.frame is not None and a.frame != b.frame:
                    fail("OKL-E-FRAME", "Conditional branches use different spatial frames.", node, phase="type")
                return Value(typ, frame=a.frame if a.frame == b.frame else None)
            # The expression's type comes from both branches even though only
            # the selected branch contributes a value or can raise a domain error.
            result_type = self.expression(node, replace(ctx, abstract=True)).type
            chosen = self.expression(node.then if condition.value else node.otherwise, ctx)
            return self.expect(chosen, result_type, node)
        fail("OKL-E-TYPE", f"Unsupported expression kind '{kind}'.", node, phase="type")

    def invoke(self, function: Callable, args: list[Value], node: Any, caller: Context) -> Value:
        declaration = function.node
        params, return_type, _ = self.signature(declaration)
        if len(args) != len(params):
            fail("OKL-E-TYPE", f"'{declaration.name}' expects {len(params)} positional arguments; received {len(args)}.", node, phase="type")
        locals_ = {name: self.expect(value, typ, node.args[i] if node.kind == "call" else node)
                   for i, ((name, typ), value) in enumerate(zip(params, args))}
        if caller.call_owner:
            self.call_edges.setdefault(caller.call_owner, set()).add(function.name)
        if caller.abstract:
            return Value(return_type)
        call_key = (function.name, function.self_path)
        if call_key in self.call_stack:
            fail("OKL-E-DEPENDENCY-CYCLE", f"Recursive pure call to '{declaration.name}' is outside core-0.1.", node)
        self.call_stack.append(call_key)
        try:
            context = Context(function.self_path, function.self_type, function.lexical_class,
                              locals_, call_owner=function.name)
            # Only .11 constructors consume this carrier authority. Pure free
            # functions retain their lexical self rules while a passed Pose
            # must still name the eventual geometry owner's frame.
            if self.model.profile == "framed-polygon-loft-0.1":
                context.geometry_owner = caller.self_path or caller.geometry_owner
            for local in declaration.locals:
                context.locals[local.name] = self.expect(self.expression(local.value, context), self.parse_type(local.type), local.value)
            return self.expect(self.expression(declaration.result, context), return_type, declaration.result)
        finally:
            self.call_stack.pop()

    def typecheck_body(self, node: Any, *, class_name: str | None = None, declaring: str | None = None) -> None:
        params, result, _ = self.signature(node)
        owner = "method:" + declaring + "." + node.name if declaring else "fn:" + node.name
        ctx = Context(self_type=class_name, lexical_class=declaring, abstract=True,
                      locals={name: Value(typ) for name, typ in params}, call_owner=owner)
        names = set(ctx.locals)
        for local in node.locals:
            if local.name in names or local.name in PREDEFINED:
                fail("OKL-E-NAME", f"Local '{local.name}' is duplicated or shadows a predefined symbol.", local, phase="binding")
            typ = self.parse_type(local.type)
            self.expect(self.expression(local.value, ctx), typ, local.value)
            ctx.locals[local.name] = Value(typ)
            names.add(local.name)
        self.expect(self.expression(node.result, ctx), result, node.result)

    def check_static_types(self) -> None:
        for function in self.functions.values():
            self.typecheck_body(function)
        for cls in self.classes.values():
            if cls.name == "Object":
                continue
            for member in cls.members.values():
                if member.node.kind == "method":
                    self.typecheck_body(member.node, class_name=cls.name, declaring=member.declaring)
                elif member.node.kind in ("site", "joint", "follow", "part"):
                    self.check_member_types(member.node, Context(self_type=cls.name, lexical_class=member.declaring, abstract=True))
            for name, (expression, declaring) in cls.defaults.items():
                typ = FIELD_TYPES.get(name) or self.parse_type(cls.members[name].node.type)
                self.expect(self.expression(expression, Context(self_type=cls.name, lexical_class=declaring, abstract=True)), typ, expression)
            for ancestor in self.class_chain(cls.name):
                if ancestor.node:
                    for statement in ancestor.node.members:
                        if statement.kind == "assert":
                            self.expect(self.expression(statement.condition, Context(self_type=cls.name, lexical_class=ancestor.name, abstract=True)), BOOL, statement.condition)
        for path, assignments, context in self.initializers:
            for assignment in assignments:
                target_path = path + ("." + ".".join(assignment.path[:-1]) if len(assignment.path) > 1 else "")
                instance = self.instances[target_path]
                name = assignment.path[-1]
                typ = FIELD_TYPES.get(name) or self.parse_type(instance.cls.members[name].node.type)
                self.expect(self.expression(assignment.value, replace(context, abstract=True)), typ, assignment.value)
        for node in self.program.scene.members:
            ctx = Context(scene=True, abstract=True)
            if node.kind == "action":
                self.expect(self.expression(node.value, ctx), Type("Action"), node.value)
            elif node.kind == "assert":
                self.expect(self.expression(node.condition, ctx), BOOL, node.condition)
            elif node.kind == "event_block":
                self.expect(self.expression(node.time, ctx), quantity_type(TIME), node.time)
            elif node.kind in ("site", "joint", "follow"):
                self.check_member_types(node, ctx)
        visiting, done = set(), set()
        def visit(name: str) -> None:
            if name in visiting:
                fail("OKL-E-DEPENDENCY-CYCLE", f"Pure function/method dependencies recurse through '{name}'.", self.program)
            if name in done: return
            visiting.add(name)
            for target in self.call_edges.get(name, ()):
                visit(target)
            visiting.remove(name); done.add(name)
        for name in self.call_edges:
            visit(name)

    def check_member_types(self, node: Any, ctx: Context) -> None:
        if node.kind == "part":
            seen = set()
            for assignment in node.assignments:
                path = tuple(assignment.path)
                if path in seen:
                    fail("OKL-E-NAME", f"Part initializer target '{'.'.join(path)}' is assigned twice.", assignment, phase="binding")
                seen.add(path)
                typ = self.initializer_type(node.class_name, assignment.path, assignment)
                self.expect(self.expression(assignment.value, ctx), typ, assignment.value)
            return
        if node.kind == "site":
            expected = {"pose": Type("Pose"), "interface": STRING, "size": quantity_type(LENGTH)}
        elif node.kind == "follow":
            expected = {"parent": Type("FrameRef"), "child": Type("Ref", name="Object"), "offset": Type("Pose")}
        else:
            if node.joint_type not in ("fixed", "grip", "hinge", "slider"):
                fail("OKL-E-NAME", f"Unknown core joint kind '{node.joint_type}'.", node, phase="binding")
            expected = {"parent": Type("SiteRef"), "child": Type("SiteRef")}
            if node.joint_type in ("hinge", "slider"):
                typ = quantity_type(ANGLE if node.joint_type == "hinge" else LENGTH)
                expected.update(axis=Type("Vec3", element=REAL), limits=Type("Range", element=typ), initial=typ)
        fields = self.assignments(node, set(expected))
        for name, assignment in fields.items():
            self.expect(self.expression(assignment.value, ctx), expected[name], assignment.value)

    def class_chain(self, name: str) -> list[EffectiveClass]:
        result = []
        while name:
            cls = self.classes[name]
            result.append(cls)
            name = cls.base
        return list(reversed(result))

    def unit_axis(self, values: tuple[float, ...], node: Any, *, quaternion: bool = False) -> tuple[float, ...]:
        norm2 = sum((Fraction(x) ** 2 for x in values), Fraction(0))
        tolerance = Fraction.from_float(1e-12)
        if norm2 == 0 or not (1 - tolerance) ** 2 <= norm2 <= (1 + tolerance) ** 2:
            code = "OKL-E-ROTATION" if quaternion else "OKL-E-AXIS"
            fail(code, "Quaternion must be nonzero and within 1e-12 of unit norm." if quaternion else
                 "Axis must be nonzero and within 1e-12 of unit norm.", node)
        norm = math.sqrt(float(norm2))
        result = tuple(canonical(x / norm) for x in values)
        if quaternion and next((x for x in result if x != 0), 1) < 0:
            result = tuple(canonical(-x) for x in result)
        return result

    def builtin(self, name: str, args: list[Value], node: Any, ctx: Context) -> Value:
        arities = {"real": 1, "abs": 1, "min": 2, "max": 2, "near": 3, "sqrt": 1, "sin": 1, "cos": 1,
                   "vec3": 3, "vector": 4, "point": 4, "quat": 4, "axis_angle": 2, "pose": 3,
                   "range": 2, "rgba": 4, "empty": 0, "sphere": 1, "box": 1, "no_body": 0,
                   "sphere_body": 2, "move": 3, "spin": 3, "tween": 3}
        if len(args) != arities[name]:
            fail("OKL-E-TYPE", f"'{name}' requires {arities[name]} positional arguments; received {len(args)}.", node, phase="type")
        def required(i: int, typ: Type) -> Value:
            return self.expect(args[i], typ, node.args[i])
        def known(values: list[Value] | tuple[Value, ...]) -> bool:
            return not ctx.abstract and all(v.known for v in values)
        if name == "real":
            return widen(required(0, INT), node, explicit=True)
        if name in ("abs", "min", "max", "near"):
            if any(not numeric(a.type) for a in args):
                fail("OKL-E-TYPE", f"'{name}' requires scalar numeric or quantity arguments.", node, phase="type")
            work = list(args)
            typ = work[0].type
            for i in range(1, len(work)):
                work[0], work[i], typ = common(work[0], work[i], node)
            work = [self.expect(a, typ, node) for a in work]
            if not known(work):
                return Value(BOOL if name == "near" else typ)
            numbers = [a.value for a in work]
            if name == "near":
                if numbers[2] < 0:
                    fail("OKL-E-NUMERIC", "near() requires a nonnegative absolute tolerance.", node)
                return Value(BOOL, abs(Fraction(numbers[0]) - Fraction(numbers[1])) <= Fraction(numbers[2]))
            value = abs(numbers[0]) if name == "abs" else min(numbers) if name == "min" else max(numbers)
            return Value(typ, checked_int(value, node) if typ == INT else canonical(value))
        if name in ("sqrt", "sin", "cos"):
            value = required(0, REAL if name == "sqrt" else quantity_type(ANGLE))
            if not known([value]): return Value(REAL)
            if name == "sqrt" and value.value < 0:
                fail("OKL-E-NUMERIC", "sqrt() requires a nonnegative Real.", node)
            return Value(REAL, finite(getattr(math, name)(value.value), node))
        if name in ("vec3", "vector", "point"):
            framed = name != "vec3"
            frame = required(0, Type("FrameRef")) if framed else None
            values = list(args[1:] if framed else args)
            if name == "point":
                values = [self.expect(v, quantity_type(LENGTH), node) for v in values]
                typ = quantity_type(LENGTH)
            else:
                if any(not numeric(v.type) for v in values):
                    fail("OKL-E-TYPE", f"'{name}' requires compatible scalar numeric or quantity components.", node, phase="type")
                values = [widen(v, node) if v.type == INT else v for v in values]
                typ = values[0].type
                for value in values[1:]:
                    common(values[0], value, node)
                values = [self.expect(v, typ, node) for v in values]
            result_type = Type("Vec3" if name == "vec3" else "Vector3" if name == "vector" else "Point3", element=typ)
            frame_path = frame.value if frame is not None and frame.known else None
            return Value(result_type, tuple(values) if known(values) else UNKNOWN, frame_path)
        if name in ("quat", "rgba"):
            values = [required(i, REAL) for i in range(4)]
            typ = Type("Rotation" if name == "quat" else "Color")
            if not known(values): return Value(typ)
            numbers = tuple(v.value for v in values)
            if name == "quat":
                return Value(typ, self.unit_axis(numbers, node, quaternion=True))
            if any(not 0 <= v <= 1 for v in numbers):
                fail("OKL-E-NUMERIC", "RGBA components must be in the closed interval [0,1].", node)
            return Value(typ, numbers)
        if name == "axis_angle":
            axis, angle = required(0, Type("Vec3", element=REAL)), required(1, quantity_type(ANGLE))
            if not known([axis, angle]): return Value(Type("Rotation"))
            direction = self.unit_axis(tuple(v.value for v in axis.value), node.args[0])
            half = angle.value / 2
            q = (math.cos(half), *(x * math.sin(half) for x in direction))
            norm = math.hypot(*q)
            q = tuple(canonical(x / norm) for x in q)
            if next((x for x in q if x), 1) < 0:
                q = tuple(canonical(-x) for x in q)
            return Value(Type("Rotation"), q)
        if name == "pose":
            frame = required(0, Type("FrameRef"))
            position = required(1, Type("Vec3", element=quantity_type(LENGTH)))
            rotation = required(2, Type("Rotation"))
            if not known([frame, position, rotation]): return Value(Type("Pose"))
            return Value(Type("Pose"), Pose(frame.value, tuple(v.value for v in position.value), rotation.value))
        if name == "range":
            if any(not numeric(a.type) for a in args):
                fail("OKL-E-TYPE", "range() requires compatible numeric scalar bounds.", node, phase="type")
            a, b, typ = common(*(widen(a, node) if a.type == INT else a for a in args), node)
            result_type = Type("Range", element=typ)
            if not known([a, b]): return Value(result_type)
            if a.value > b.value:
                fail("OKL-E-NUMERIC", "Range lower bound exceeds its upper bound.", node)
            return Value(result_type, (a, b))
        if name in ("empty", "no_body"):
            return Value(Type("Geometry" if name == "empty" else "BodyModel"), {"kind": name})
        if name in ("sphere", "box", "sphere_body"):
            first = required(0, Type("Vec3", element=quantity_type(LENGTH)) if name == "box" else quantity_type(LENGTH))
            mass = required(1, quantity_type(MASS)) if name == "sphere_body" else None
            typ = Type("BodyModel" if name == "sphere_body" else "Geometry")
            if not known([first] + ([mass] if mass is not None else [])): return Value(typ)
            sizes = [v.value for v in first.value] if name == "box" else [first.value]
            if any(v <= 0 for v in sizes) or mass is not None and mass.value <= 0:
                fail("OKL-E-PHYSICAL-DOMAIN", f"'{name}' requires strictly positive sizes" + (" and mass." if mass is not None else "."), node)
            if name == "box":
                return Value(typ, {"kind": name, "size": tuple(sizes)})
            result = {"kind": name, "radius": first.value}
            if mass is not None:
                inertia = rounded(Fraction(2, 5) * Fraction(mass.value) * Fraction(first.value) ** 2, node, self.warning)
                if inertia <= 0:
                    fail("OKL-E-PHYSICAL-DOMAIN", "Sphere inertia must remain positive after canonical rounding.", node)
                result.update(mass=mass.value, inertia=inertia)
            return Value(typ, result)
        if name in ("move", "spin", "tween"):
            duration = required(2, quantity_type(TIME))
            if name in ("move", "spin"):
                target = required(0, Type("Ref", name="Object"))
                vector = required(1, Type("Vector3", element=quantity_type(SPEED if name == "move" else ANGULAR_SPEED)))
                if vector.frame is not None and vector.frame != "world":
                    fail("OKL-E-FRAME", f"{name}() requires a vector expressed in world axes.", node.args[1], phase="type")
                values = [target, vector, duration]
            else:
                target = required(0, Type("JointRef"))
                goal = args[1]
                if goal.type not in (quantity_type(ANGLE), quantity_type(LENGTH)):
                    fail("OKL-E-UNIT", "tween() requires an Angle for a hinge or a Length for a slider.", node.args[1], phase="type")
                kind = self.joints[target.value][0].joint_type if target.known and target.value in self.joints else target.hint
                if kind is not None:
                    if kind not in ("hinge", "slider"):
                        fail("OKL-E-TYPE", f"A {kind} joint has no tweenable coordinate.", node.args[0], phase="type")
                    goal = self.expect(goal, quantity_type(ANGLE if kind == "hinge" else LENGTH), node.args[1])
                values = [target, goal, duration]
            if not known(values): return Value(Type("Action"))
            if duration.value <= 0:
                fail("OKL-E-EVENT-ORDER", "Action duration must be a positive Time.", node.args[2])
            data = {"kind": name, "target": target.value, "duration": Fraction.from_float(duration.value)}
            if name == "tween":
                data["goal"] = goal.value
            else:
                data["vector"] = tuple(v.value for v in vector.value)
            return Value(Type("Action"), data)
        fail("OKL-E-NAME", f"Unknown built-in '{name}'.", node, phase="binding")

    def assignments(self, node: Any, required: set[str]) -> dict[str, Any]:
        result = {}
        for assignment in node.assignments:
            if len(assignment.path) != 1 or assignment.path[0] not in required:
                fail("OKL-E-NAME", f"Allowed {node.kind} fields are {', '.join(sorted(required))}.", assignment, phase="binding")
            name = assignment.path[0]
            if name in result:
                fail("OKL-E-NAME", f"Field '{name}' is assigned twice.", assignment, phase="binding")
            result[name] = assignment
        missing = required - set(result)
        if missing:
            fail("OKL-E-NAME", f"Missing required {node.kind} fields: {', '.join(sorted(missing))}.", node, phase="binding")
        return result

    def resolve_site(self, path: str) -> SiteModel:
        if path in self.model.sites:
            return self.model.sites[path]
        if path not in self.sites:
            fail("OKL-E-NAME", f"Unknown attachment site '{path}'.", self.program, phase="binding")
        node, ctx, ids, owner = self.sites[path]
        def compute():
            fields = self.assignments(node, {"pose", "interface", "size"})
            expected = {"pose": Type("Pose"), "interface": STRING, "size": quantity_type(LENGTH)}
            values = {name: self.expect(self.expression(a.value, ctx), expected[name], a.value) for name, a in fields.items()}
            pose = values["pose"].value
            if pose.frame != owner + ".frame":
                fail("OKL-E-FRAME", "A site's pose must be relative to its owning object's frame.", fields["pose"].value, phase="type")
            if values["interface"].value == "" or values["size"].value < 0:
                fail("OKL-E-SITE-INTERFACE", "Site interface must be nonempty and site size nonnegative.", node)
            self.model.sites[path] = SiteModel(path, ids, owner, pose, values["interface"].value, values["size"].value, node)
            return Value(Type("SiteRef"), path)
        self.guarded((path, "@site"), node, compute)
        return self.model.sites[path]

    def resolve_joint(self, path: str) -> JointModel:
        if path in self.model.joints:
            return self.model.joints[path]
        node, ctx, ids = self.joints[path]
        def compute():
            kind = node.joint_type
            if kind not in ("fixed", "hinge", "slider", "grip"):
                fail("OKL-E-NAME", f"Unknown core joint kind '{kind}'.", node, phase="binding")
            coordinates = kind in ("hinge", "slider")
            fields = self.assignments(node, {"parent", "child"} | ({"axis", "limits", "initial"} if coordinates else set()))
            dim = ANGLE if kind == "hinge" else LENGTH
            expected = {"parent": Type("SiteRef"), "child": Type("SiteRef"), "axis": Type("Vec3", element=REAL),
                        "limits": Type("Range", element=quantity_type(dim)), "initial": quantity_type(dim)}
            values = {name: self.expect(self.expression(a.value, ctx), expected[name], a.value) for name, a in fields.items()}
            parent, child = self.resolve_site(values["parent"].value), self.resolve_site(values["child"].value)
            if parent.owner == child.owner:
                fail("OKL-E-SITE-INTERFACE", "Joint endpoint sites must belong to distinct instances.", node)
            if parent.interface != child.interface or parent.size != child.size:
                fail("OKL-E-SITE-INTERFACE", "Joint sites require exactly matching interface identifiers and canonical sizes.", node,
                     details={"parent_interface": parent.interface, "child_interface": child.interface,
                              "parent_size_m": parent.size, "child_size_m": child.size})
            joint = JointModel(path, node.name, ids, kind, parent.path, child.path, span=node)
            if coordinates:
                joint.axis = self.unit_axis(tuple(v.value for v in values["axis"].value), fields["axis"].value)
                joint.limits = tuple(v.value for v in values["limits"].value)
                joint.initial = values["initial"].value
                if not joint.limits[0] <= joint.initial <= joint.limits[1]:
                    fail("OKL-E-JOINT-LIMIT", "Initial joint coordinate is outside its mandatory closed limits.", fields["initial"].value)
            self.model.joints[path] = joint
            return Value(Type("JointRef"), path)
        self.guarded((path, "@joint"), node, compute)
        return self.model.joints[path]

    def resolve_follow(self, path: str) -> FollowModel:
        if path in self.model.follows:
            return self.model.follows[path]
        node, ctx, ids = self.follows[path]
        def compute():
            fields = self.assignments(node, {"parent", "child", "offset"})
            expected = {"parent": Type("FrameRef"), "child": Type("Ref", name="Object"), "offset": Type("Pose")}
            values = {name: self.expect(self.expression(a.value, ctx), expected[name], a.value) for name, a in fields.items()}
            parent, child, offset = values["parent"].value, values["child"].value, values["offset"].value
            if offset.frame != parent:
                fail("OKL-E-FRAME", "Follow offset must use the exact parent frame identity.", fields["offset"].value, phase="type")
            self.model.follows[path] = FollowModel(path, node.name, ids, parent, child, offset, node)
            return Value(Type("FollowRecord"), path)
        self.guarded((path, "@follow"), node, compute)
        return self.model.follows[path]

    def action_value(self, path: str) -> Value:
        node = self.actions[path]
        def compute():
            value = self.expect(self.expression(node.value, Context(scene=True)), Type("Action"), node.value)
            ids = (self.model.module_key, self.model.scene_key, node.key)
            self.model.actions[path] = ActionModel(path, node.name, ids, span=node, **value.value)
            return value
        return self.guarded((path, "@action"), node, compute)

    def relation_validation(self) -> None:
        # Inspect graph topology before authority restrictions, so a mechanical
        # loop is reported as unsupported mechanics rather than mistaken for
        # cyclic ownership or an ordinary following cycle.
        incoming: dict[str, list[Any]] = {}
        edges: dict[str, list[tuple[str, Any, bool]]] = {}
        for joint in self.model.joints.values():
            parent = self.model.sites[joint.parent].owner
            child = self.model.sites[joint.child].owner
            edges.setdefault(parent, []).append((child, joint, True))
            incoming.setdefault(child, []).append(joint)
        for follow in self.model.follows.values():
            parent = self.model.frame_owner(follow.parent)
            incoming.setdefault(follow.child, []).append(follow)
            if parent is not None:
                edges.setdefault(parent, []).append((follow.child, follow, False))
        stack: list[str] = []
        route: list[tuple[Any, bool]] = []
        done: set[str] = set()
        unsupported: list[tuple[str, Any]] = []
        def visit(path: str) -> None:
            if path in done: return
            stack.append(path)
            for child, relation, mechanical in edges.get(path, []):
                if child in stack:
                    index = stack.index(child)
                    mixed = mechanical or any(joint for _, joint in route[index:])
                    if mixed:
                        unsupported.append(("The pose dependency graph contains a mechanical loop, unsupported in core-0.1.", relation.span))
                    else:
                        fail("OKL-E-FOLLOW-CYCLE", "Ordinary spatial following contains a directed cycle.", relation.span)
                elif child not in done:
                    route.append((relation, mechanical))
                    visit(child)
                    route.pop()
            stack.pop(); done.add(path)
        for path in self.instances:
            visit(path)
        for child, relations in incoming.items():
            joints = [r for r in relations if isinstance(r, JointModel)]
            if len(joints) > 1:
                unsupported.append(("Multiple incoming joints require a multi-constraint mechanical profile.", joints[-1].span))
            elif len(relations) > 1:
                fail("OKL-E-POSE-AUTHORITY", f"Object '{child}' has competing incoming pose relations.", relations[-1].span)
        for joint in self.model.joints.values():
            parent_path = self.model.sites[joint.parent].owner
            child_path = self.model.sites[joint.child].owner
            parent, child = self.model.objects[parent_path], self.model.objects[child_path]
            if parent.motion not in ("static", "prescribed") or child.motion != "prescribed":
                fail("OKL-E-MOTION-MODE", "Core joints require a static/prescribed parent and a prescribed child.", joint.span)
            if joint.kind == "grip":
                if child.physical["kind"] != "sphere_body":
                    fail("OKL-E-PHYSICAL-DOMAIN", "A releasable grip requires a sphere_body on its child.", joint.span)
                others = [other for other in self.model.joints.values() if other.path != joint.path and
                          child_path in (self.model.sites[other.parent].owner, self.model.sites[other.child].owner)]
                if others:
                    unsupported.append(("A gripped child cannot participate in another joint under core-0.1.", others[0].span))
        for follow in self.model.follows.values():
            child = self.model.objects[follow.child]
            if child.motion != "prescribed":
                fail("OKL-E-MOTION-MODE", "A following child must use prescribed motion.", follow.span)
            if child.physical["kind"] != "no_body":
                fail("OKL-E-PHYSICAL-DOMAIN", "A follow relation may control only a massless child with no_body().", follow.span)
        for path, model in self.model.objects.items():
            if path in incoming:
                if model.placement_authored:
                    fail("OKL-E-POSE-AUTHORITY", f"Object '{path}' authors placement while an incoming relation determines its pose.", model.span,
                         repair="Remove the child's authored placement and set the attachment-site or follow offset instead.")
                if model.motion != "prescribed":
                    fail("OKL-E-MOTION-MODE", "Only prescribed objects can receive an incoming pose relation.", model.span)
        for path, node in self.placement_reads:
            if path in incoming:
                fail("OKL-E-POSE-AUTHORITY", f"Source cannot read placement on relation-controlled object '{path}'. Use evaluated pose inspection.", node)
        if unsupported:
            if self.level != "represented":
                fail("OKL-E-CAPABILITY-UNSUPPORTED", unsupported[0][0], unsupported[0][1], phase="support")
            self.model.diagnostics.extend(Diagnostic("OKL-E-CAPABILITY-UNSUPPORTED", message, node, category="unsupported", phase="support")
                                          for message, node in unsupported)

    def resolve_objects(self) -> None:
        for path, instance in self.instances.items():
            obj = instance.model
            values = {name: self.field(path, name) for name in FIELD_TYPES}
            for name, value in values.items():
                if name in ("velocity", "omega"):
                    if value.frame != "world":
                        fail("OKL-E-FRAME", f"Initial '{name}' must be expressed in world axes.", obj.span, phase="type")
                    setattr(obj, name, tuple(v.value for v in value.value))
                else:
                    setattr(obj, name, value.value)
            obj.placement_authored = "placement" in instance.overrides or "placement" in instance.cls.defaults
            if obj.placement.frame != "world":
                fail("OKL-E-FRAME", "Authored object placement must use the world reference frame.", obj.span, phase="type")
            if obj.motion != "dynamic" and (any(obj.velocity) or any(obj.omega)):
                fail("OKL-E-MOTION-MODE", "Nonzero authored velocity/omega is allowed only on an initially dynamic object.", obj.span)
            if obj.motion == "dynamic" and obj.physical["kind"] != "sphere_body":
                fail("OKL-E-PHYSICAL-DOMAIN", "A dynamic object requires a positive-mass sphere_body representation.", obj.span)
            for name, member in instance.cls.members.items():
                if member.node.kind in ("param", "derive"):
                    obj.properties[name] = self.field(path, name)
        for site in self.sites:
            self.resolve_site(site)
        for joint in self.joints:
            self.resolve_joint(joint)
        for follow in self.follows:
            self.resolve_follow(follow)

    def assertions(self) -> None:
        for path, instance in self.instances.items():
            for cls in self.class_chain(instance.cls.name):
                if cls.node is None: continue
                ctx = Context(path, instance.cls.name, cls.name)
                for node in cls.node.members:
                    if node.kind == "assert":
                        value = self.expect(self.expression(node.condition, ctx), BOOL, node.condition)
                        if not value.value:
                            fail("OKL-E-ASSERT", node.message, node)
        for node in self.program.scene.members:
            if node.kind == "assert":
                value = self.expect(self.expression(node.condition, Context(scene=True)), BOOL, node.condition)
                if not value.value:
                    fail("OKL-E-ASSERT", node.message, node)

    def scene_fields(self) -> None:
        nodes = [n for n in self.program.scene.members if n.kind == "assign"]
        fields = {}
        for node in nodes:
            if len(node.path) != 1 or node.path[0] not in ("duration", "gravity"):
                fail("OKL-E-NAME", "Scene assignments are limited to duration and gravity.", node, phase="binding")
            name = node.path[0]
            if name in fields:
                fail("OKL-E-NAME", f"Scene field '{name}' must occur exactly once.", node, phase="binding")
            fields[name] = node
        if set(fields) != {"duration", "gravity"}:
            fail("OKL-E-NAME", "A scene must author duration and gravity exactly once each.", self.program.scene, phase="binding")
        ctx = Context(scene=True)
        for name, typ in (("duration", quantity_type(TIME)), ("gravity", Type("Vector3", element=quantity_type(ACCELERATION)))):
            expression = fields[name].value
            self.expect(self.expression(expression, replace(ctx, abstract=True)), typ, expression)
            value = self.expect(self.expression(expression, ctx), typ, expression)
            if name == "duration":
                if value.value <= 0:
                    fail("OKL-E-EVENT-ORDER", "Scene duration must be a positive Time.", expression)
                self.model.duration = Fraction.from_float(value.value)
            else:
                if value.frame != "world":
                    fail("OKL-E-FRAME", "Scene gravity must be expressed in world axes.", expression, phase="type")
                self.model.gravity = tuple(v.value for v in value.value)

    def event_blocks(self) -> None:
        seen = set()
        for node in self.program.scene.members:
            if node.kind != "event_block": continue
            value = self.expect(self.expression(node.time, Context(scene=True)), quantity_type(TIME), node.time)
            time = Fraction.from_float(value.value)
            if time < 0 or time > self.model.duration:
                fail("OKL-E-EVENT-ORDER", "Event time must lie in [0, scene.duration].", node.time)
            if time in seen:
                fail("OKL-E-EVENT-ORDER", "Equal canonical event times must share one explicitly ordered sequence block.", node.time)
            seen.add(time)
            events = []
            for event in node.events:
                if event.kind == "release":
                    target = self.name(event.path[0], Context(scene=True), event)
                    for part in event.path[1:]:
                        target = self.member(target, part, Context(scene=True), event)
                    target = self.expect(target, Type("JointRef"), event)
                    events.append(Event("release", target.value, event))
                else:
                    if event.name not in self.actions:
                        fail("OKL-E-NAME", f"'{event.name}' is not a named action instance.", event, phase="binding")
                    events.append(Event(event.kind, event.name, event))
            self.model.events.append(EventBlock(time, events, node))
        self.model.events.sort(key=lambda block: block.time)

    def run(self) -> SceneModel:
        if self.level not in ("represented", "constructed", "evaluated", "delivered"):
            fail("OKL-E-CAPABILITY-UNSUPPORTED", f"Unknown requested output level '{self.level}'.", self.program, phase="support")
        self.bind()
        ctx = Context(scene=True)
        base = (self.model.module_key, self.model.scene_key)
        for node in self.program.scene.members:
            if node.kind == "object":
                self.expand(node, node.name, None, base + (node.key,), ctx)
            elif node.kind == "joint":
                self.joints[node.name] = (node, ctx, base + (node.key,))
            elif node.kind == "follow":
                self.follows[node.name] = (node, ctx, base + (node.key,))
            elif node.kind == "action":
                self.actions[node.name] = node
        self.apply_initializers()
        self.check_static_types()
        self.scene_fields()
        self.resolve_objects()
        for path in self.actions:
            self.action_value(path)
        self.assertions()
        self.relation_validation()
        self.event_blocks()
        self.model.requested_capabilities = tuple(node.value for node in self.program.requires)
        if self.program.version != "0.1" or self.program.profile != "core-0.1":
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "This implementation supports ontokin 0.1 and profile core-0.1 only.", self.program, phase="support")
        if self.model.requested_capabilities and self.level != "represented":
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "Required capabilities are not supplied by the headless core prototype: " + ", ".join(self.model.requested_capabilities), self.program.requires[0], phase="support")
        if self.level == "delivered":
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "The headless prototype has no external delivery/rendering contract.", self.program, phase="support")
        return self.model

    def annotate(self, error: OntoKinError) -> None:
        """Attach an unambiguous known declaration ID to a source diagnostic.

        Elaboration attaches occurrence/property IDs at the point of failure.
        This fallback identifies definition-level type errors, including errors
        found before any instance can be constructed. Unresolved/reused keys are
        deliberately left without a purported valid element identity.
        """
        diagnostic = error.diagnostic
        if diagnostic.element_id is not None or diagnostic.node is None or diagnostic.code in ("OKL-E-ID", "OKL-E-LEXICAL", "OKL-E-SYNTAX"):
            return
        start, end = diagnostic.node.start, diagnostic.node.end
        candidates = []
        def inspect(declaration: Any, ids: tuple[str, ...]) -> None:
            if declaration.start <= start and end <= declaration.end:
                candidates.append((declaration.end - declaration.start, ids))
                for member in optional(declaration, "members", []):
                    if optional(member, "key") is not None:
                        inspect(member, ids + (member.key,))
        for declaration in self.program.classes + self.program.functions:
            inspect(declaration, (self.program.module_key, "definitions", declaration.key))
        inspect(self.program.scene, (self.program.module_key, self.program.scene.key))
        if candidates:
            diagnostic.element_id = list(min(candidates, key=lambda entry: entry[0])[1])


def validate(program: Any, *, level: str = "represented") -> SceneModel:
    """Elaborate one parsed source revision, raising its first precise diagnostic.

    ``evaluated`` requests additionally require evaluator.preflight(model) or an
    actual evaluator run. Returning this static model alone makes no timeline
    or numerical trajectory claim.
    """
    validator = Validator(program, level)
    try:
        return validator.run()
    except OntoKinError as error:
        validator.annotate(error)
        raise




