"""Pinned, bounded construction-0.1 elaboration into the existing scene model.

Module loading is provided by :mod:`linker`. This compiler preserves original
source nodes and nominal definitions, resolves final initializer layers before
expanding keyed parts, and delegates numerical/frame/mechanical rules to the
core validator. It does not concatenate source files, mutate a running scene,
or claim that static elaboration has evaluated the authored timeline.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from fractions import Fraction
import json
import time
from typing import Any, Callable as Check

from .diagnostics import Diagnostic, OntoKinError
from .json_limits import JSONLimitError
from .model import Event, EventBlock, ObjectModel, Pose, SiteModel
from .surface_runtime import SURFACE_CALLS, SURFACE_TYPES, SURFACE_PROFILE, surface_builtin, materialize_surface
from .surface import SurfaceError
from .validator import (BUILTIN_TYPES, FIELD_TYPES,
                        PREDEFINED, READONLY_FIELDS, BoundExpression, Callable,
                        Context, EffectiveClass, Instance, Member, Validator,
                        fail, optional)
from .values import (ACCELERATION, ALIASES, BOOL, INT, LENGTH, STRING, TIME,
                     UNKNOWN, KeyedValue, Type, Value, bounded_data, quantity_type)


PROFILE = "construction-0.1"
PREDEFINED_02 = PREDEFINED | {"Keyed", "len"}
MAX_KEYED_ENTRIES = 256
MAX_OWNERSHIP_DEPTH = 64
MAX_PATH_BYTES = 32768
MAX_JSON_BYTES = 4 * 1024 * 1024
LIMITS = {"max_objects": 1000, "max_operations": 100000,
          "max_result_items": 1000, "max_elapsed_ms": 30000,
          "max_value_entries": 100000}


class ConstructionBudget:
    """One work/value counter for the whole linked compilation attempt."""

    def __init__(self, budgets: dict | None = None, check: Check[[], None] | None = None):
        if budgets is not None and (not isinstance(budgets, dict) or set(budgets) - set(LIMITS)):
            fail("OKL-E-RESOURCE", "Unknown construction budget field.", phase="support")
        self.limits = dict(LIMITS)
        for name, value in (budgets or {}).items():
            if type(value) is not int or not 1 <= value <= LIMITS[name]:
                fail("OKL-E-RESOURCE", f"{name} must be an integer from 1 through {LIMITS[name]}.",
                     phase="support", details={"budget": name, "limit": LIMITS[name]})
            self.limits[name] = value
        self.operations = 0
        self.value_entries = 0
        self.started = time.monotonic()
        self.check = check

    def tick(self, node: Any = None, amount: int = 1) -> None:
        if self.check is not None:
            self.check()
        self.operations += amount
        if self.operations > self.limits["max_operations"]:
            self.exceeded("max_operations", self.operations, node)
        elapsed = (time.monotonic() - self.started) * 1000
        if elapsed > self.limits["max_elapsed_ms"]:
            self.exceeded("max_elapsed_ms", elapsed, node)

    def exceeded(self, name: str, consumed: int | float, node: Any = None) -> None:
        fail("OKL-E-RESOURCE", f"Construction exceeded {name}.", node, phase="support",
             details={"budget": name, "limit": self.limits[name], "consumed": consumed,
                      "profile": PROFILE})

    def charge_value(self, value: Value, node: Any = None) -> None:
        # Logical unfolding counts repeated immutable leaves on each occurrence.
        # Authored Keyed is flat; this iterative walk also handles core values.
        stack = [iter((value,))]
        while stack:
            try:
                item = next(stack[-1])
            except StopIteration:
                stack.pop()
                continue
            self.value_entries += 1
            if self.value_entries > self.limits["max_value_entries"]:
                self.exceeded("max_value_entries", self.value_entries, node)
            if self.value_entries % 128 == 0:
                self.tick(node)
            if isinstance(item, Value):
                if item.known:
                    stack.append(iter((item.value,)))
            elif isinstance(item, KeyedValue):
                stack.append(iter(item.entries))
            elif isinstance(item, dict):
                stack.append(iter(item.values()))
            elif isinstance(item, (tuple, list)):
                stack.append(iter(item))
            elif is_dataclass(item):
                stack.append(iter(tuple(getattr(item, f.name) for f in fields(item))))

    def report(self) -> dict:
        return {"limits": dict(self.limits), "operations": self.operations,
                "value_entries": self.value_entries,
                "elapsed_ms": (time.monotonic() - self.started) * 1000}


def _steps(path) -> tuple:
    """Normalize paths without ever splitting a legal literal key on '.'."""
    from .syntax02 import PathStep
    return tuple(PathStep("member", step, 0, 0) if isinstance(step, str) else step
                 for step in path)


def render_path(steps) -> str:
    result = ""
    for step in _steps(steps):
        if step.kind == "member":
            result += ("." if result else "") + step.value
        elif step.kind == "key":
            result += "[" + json.dumps(step.value, ensure_ascii=False) + "]"
        else:
            raise ValueError("Unknown structured path step.")
    return result


def _token(steps) -> tuple[tuple[str, str], ...]:
    return tuple((step.kind, step.value) for step in _steps(steps))


@dataclass(frozen=True)
class InitializerBinding:
    assignment: Any
    context: Context
    steps: tuple
    origin_path: str


class ConstructionCompiler(Validator):
    """A source-aware compiler and inspectable, revision-bound elaboration index.

    Definition map values retain the linker's DefinitionSymbol fields. Bindings
    map ``id(Node)`` to resolved definition IDs. Occurrence/collection maps retain
    original nodes for source inspection; only their separately materialized
    provenance records are attached to the scene for external export.
    """

    def __init__(self, linked, level: str, budget: ConstructionBudget):
        super().__init__(linked.entry.ast, level)
        self.linked, self.bundle, self.budget = linked, linked.bundle, budget
        self.linked_program = linked
        self.surface_meshes: dict[str, dict] = {}
        self.source_registry = linked.source_registry
        self.definitions = dict(linked.definitions)
        self.bindings: dict[int, tuple[str, ...]] = {}
        self.occurrence_provenance: dict[str, dict] = {}
        self.collections: dict[str, dict] = {}
        self.dependencies: dict[tuple[str, str], set[tuple[str, str]]] = {}
        self.call_dependencies: dict[tuple[str, str], set[tuple[str, ...]]] = {}
        self.generated_dependencies: dict[tuple[str, str], set[str]] = {}
        self.override_bindings: dict[tuple[str, str], InitializerBinding] = {}
        self._class_symbols = {}
        self._function_symbols = {}
        self._resolved_types: dict[int, Type] = {}
        self._resolved_classes: dict[int, str] = {}
        self._forwards: dict[str, dict[tuple, list[InitializerBinding]]] = {}
        self._collection_state: dict[str, str] = {}
        self._keyed_origins: dict[int, dict[str, Any]] = {}
        self._keyed_payloads: dict[int, KeyedValue] = {}
        self._shape_stack: list[str] = []
        self._value_taints: dict[int, set[str]] = {}
        self._tainted_values: dict[int, Value] = {}
        self._lexical_self_origins: dict[int, tuple[Value, str]] = {}
        self._expression_depth = 0
        self._type_depth = 0
        self.model.program_revision = self.bundle.program_revision
        self.model.source_manifest = self.bundle.manifest()

    @staticmethod
    def render_path(steps) -> str:
        return render_path(steps)

    def source_for(self, node: Any):
        source_id = getattr(node, "source_id", None)
        if source_id not in self.source_registry:
            raise ValueError("Source node has no source in this immutable bundle.")
        return self.source_registry[source_id]

    def definition_id(self, class_id: str, member: str | None = None) -> tuple[str, ...]:
        if class_id == "Object":
            return ("@system", "Object") if member is None else ("@system", "Object", member)
        if member is None:
            return tuple(self._class_symbols[class_id].element_id)
        declared = self.effective(class_id).members[member]
        return tuple(self._class_symbols[declared.declaring].element_id) + (declared.node.key,)

    def _resolve(self, node: Any, name: str, kind: str | None = None):
        self.budget.tick(node)
        symbol = self.linked.resolve_definition(node.source_id, name, kind=kind, node=node)
        self.bindings[id(node)] = tuple(symbol.element_id)
        return symbol

    @staticmethod
    def _nominal(symbol) -> str:
        return "/".join(symbol.element_id)

    def class_reference(self, node: Any) -> str:
        if id(node) not in self._resolved_classes:
            name = node.class_name
            self._resolved_classes[id(node)] = "Object" if name == "Object" else self._nominal(self._resolve(node, name, "class"))
        return self._resolved_classes[id(node)]

    def warning(self, node: Any) -> None:
        key = (getattr(node, "source_id", None), getattr(node, "start", -1), getattr(node, "end", -1))
        if key not in self._warning_spans:
            self._warning_spans.add(key)
            self.model.diagnostics.append(Diagnostic("OKL-W-UNDERFLOW", "A numeric result underflowed to a subnormal value or zero.",
                                                     node, phase="elaboration"))

    def unique(self, nodes: list[Any], *, inherited=None) -> None:
        names, keys = set(), set()
        for node in nodes:
            self.budget.tick(node)
            self.key(node, node.key)
            if node.name in PREDEFINED_02 or node.name in names:
                fail("OKL-E-NAME", f"Name '{node.name}' is predefined or duplicated in this scope.", node, phase="binding")
            if node.key in keys:
                fail("OKL-E-ID", f"Stable key '{node.key}' is reused in this scope.", node, phase="binding")
            names.add(node.name)
            keys.add(node.key)

    def parse_type(self, node: Any) -> Type:
        self.budget.tick(node)
        if id(node) in self._resolved_types:
            return self._resolved_types[id(node)]
        self._type_depth += 1
        try:
            if self._type_depth > 64:
                fail("OKL-E-RESOURCE", "Type nesting exceeds the bounded construction parser/type work.", node, phase="support")
            name, args = node.name, optional(node, "args", [])
            if name == "Keyed":
                if len(args) != 1:
                    fail("OKL-E-TYPE", "Keyed requires exactly one immutable leaf element type.", node, phase="type")
                element = self.parse_type(args[0])
                self._keyed_leaf(element, node)
                result = Type("Keyed", element=element)
            elif name in SURFACE_TYPES and self.linked.modules[node.source_id].ast.profile == SURFACE_PROFILE:
                if args:
                    fail("OKL-E-TYPE", f"Surface type '{name}' takes no type arguments.", node, phase="type")
                result = Type(name)
            elif name == "Ref":
                if len(args) != 1 or optional(args[0], "args", []) or optional(args[0], "unit") is not None:
                    fail("OKL-E-TYPE", "Ref requires exactly one declared nominal class.", node, phase="type")
                nominal = "Object" if args[0].name == "Object" else self._nominal(self._resolve(args[0], args[0].name, "class"))
                result = Type("Ref", name=nominal)
            elif name in BUILTIN_TYPES or name in ALIASES:
                result = super().parse_type(node)
            else:
                if args:
                    fail("OKL-E-TYPE", f"Type '{name}' does not accept type arguments.", node, phase="type")
                result = Type("Ref", name=self._nominal(self._resolve(node, name, "class")))
            self._resolved_types[id(node)] = result
            return result
        finally:
            self._type_depth -= 1

    def _keyed_leaf(self, element: Type, node: Any) -> None:
        allowed = {"Int", "Real", "Bool", "String", "Quantity", "Vec3", "Vector3", "Range",
                   "FrameRef", "Point3", "Rotation", "Pose", "Color"}
        if self.linked.modules[node.source_id].ast.profile == SURFACE_PROFILE:
            allowed |= SURFACE_TYPES
        if element.kind not in allowed:
            fail("OKL-E-CAPABILITY-UNSUPPORTED", f"Authored Keyed<{element}> is outside the flat immutable leaf profile.",
                 node, phase="support", details={"profile": PROFILE, "element_type": str(element)})

    def signature(self, node: Any) -> tuple:
        self.budget.tick(node)
        names, params = set(), []
        for param in node.params:
            if param.name in PREDEFINED_02 or param.name in names:
                fail("OKL-E-NAME", f"Parameter '{param.name}' duplicates or shadows a predefined symbol.", param, phase="binding")
            names.add(param.name)
            params.append((param.name, self.parse_type(param.type)))
        return tuple(params), self.parse_type(node.return_type), optional(node, "visibility", "public")

    def _inherit_value_info(self, original: Value, result: Value) -> Value:
        """Carry flow provenance on wrappers, never on shared leaf payloads."""
        if original is result:
            return result
        origin = self._lexical_self_origins.get(id(original))
        if origin is not None and origin[0] is original:
            self._lexical_self_origins[id(result)] = (result, origin[1])
        if self._value_taints.get(id(original)):
            self._value_taints[id(result)] = set(self._value_taints[id(original)])
            self._tainted_values[id(result)] = result
        return result

    def expect(self, value: Value, typ: Type, node: Any) -> Value:
        return self._inherit_value_info(value, super().expect(value, typ, node))

    def effective(self, name: str) -> EffectiveClass:
        self.budget.tick(self.class_nodes.get(name))
        if name in self.classes:
            return self.classes[name]
        if name not in self.class_nodes:
            fail("OKL-E-NAME", f"Unknown nominal class '{name}'.", self.program, phase="binding")
        node = self.class_nodes[name]
        if name in self.class_stack:
            fail("OKL-E-INHERITANCE-CYCLE", "Nominal inheritance contains a cycle.", node)
        if len(self.class_stack) >= 128:
            fail("OKL-E-RESOURCE", "Inheritance depth exceeds bounded compiler work.", node, phase="support")
        self.class_stack.append(name)
        try:
            lexical_base = optional(node, "base") or "Object"
            base = "Object" if lexical_base == "Object" else self._nominal(self._resolve(node, lexical_base, "class"))
            parent = self.effective(base)
            cls = EffectiveClass(name, node, base, dict(parent.members), dict(parent.defaults))
            local_names, local_defaults = set(), set()
            effective_keys = {m.node.key: n for n, m in parent.members.items()}
            for member in node.members:
                self.budget.tick(member)
                kind = member.kind
                if kind == "assert":
                    continue
                if kind in ("assign", "override_default"):
                    path = _steps(member.path) if kind == "assign" else ()
                    target = member.name if kind == "override_default" else path[0].value
                    if kind == "assign" and (len(path) != 1 or path[0].kind != "member"):
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
                        inherited = parent.members.get(target)
                        if inherited:
                            if inherited.node.kind == "derive":
                                fail("OKL-E-READONLY", f"Derived property '{target}' cannot be overridden.", member, phase="type")
                            if inherited.node.kind != "param" or inherited.node.visibility != "public":
                                fail("OKL-E-OVERRIDE", f"'{target}' is not an overridable public inherited parameter.", member, phase="type")
                        elif target not in FIELD_TYPES or target not in parent.defaults:
                            fail("OKL-E-OVERRIDE", f"No explicit inherited default named '{target}' can be overridden.", member, phase="type")
                    cls.defaults[target] = (member.value, name)
                    continue
                self.key(member, member.key)
                if member.name in PREDEFINED_02 or member.name in FIELD_TYPES or member.name in READONLY_FIELDS or member.name in local_names:
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
                    fail("OKL-E-ID", f"Member key '{member.key}' is reused.", member, phase="binding")
                effective_keys[member.key] = member.name
                if kind in ("joint", "follow") and optional(member, "visibility") not in ("public", "private"):
                    fail("OKL-E-NAME", "Class relations require explicit public or private visibility.", member, phase="binding")
                if kind in ("param", "derive"):
                    self.parse_type(member.type)
                    cls.defaults[member.name] = (member.value, name)
                elif kind == "method":
                    self.signature(member)
                elif kind in ("part", "parts"):
                    self.class_reference(member)
                    if kind == "parts":
                        if member.key_name == member.value_name or {member.key_name, member.value_name} & PREDEFINED_02:
                            fail("OKL-E-NAME", "Generated-part binders must be distinct and cannot shadow predefined names.", member, phase="binding")
                elif kind not in ("joint", "follow", "site"):
                    fail("OKL-E-NAME", f"Unsupported class member kind '{kind}'.", member, phase="binding")
                cls.members[member.name] = Member(member, name)
            self.classes[name] = cls
            return cls
        finally:
            self.class_stack.pop()

    def bind(self) -> None:
        from .linker import DefinitionSymbol
        self.key(self.program.scene, self.program.scene.key)
        if self.program.scene.key == "definitions":
            fail("OKL-E-ID", "The scene key 'definitions' is reserved for definition records.", self.program.scene, phase="binding")
        for symbol in self.linked.definitions.values():
            self.budget.tick(symbol.node)
            nominal = self._nominal(symbol)
            if symbol.kind == "class":
                self.class_nodes[nominal] = symbol.node
                self._class_symbols[nominal] = symbol
            else:
                self.functions[nominal] = symbol.node
                self._function_symbols[nominal] = symbol
        for nominal in self.class_nodes:
            self.effective(nominal)
        for nominal, symbol in self._class_symbols.items():
            for member in symbol.node.members:
                if optional(member, "key") is not None:
                    ident = tuple(symbol.element_id) + (member.key,)
                    self.definitions[ident] = DefinitionSymbol(ident, symbol.source_id, member,
                                                              member.kind, member.name, member.key,
                                                              optional(member, "visibility", "public"))
        for node in self.functions.values():
            self.signature(node)
        declarations = [n for n in self.program.scene.members if n.kind in ("object", "joint", "follow", "action")]
        self.unique(declarations)
        self.scene_names = {n.name: n for n in declarations}
        for node in declarations:
            if node.kind == "object":
                self.class_reference(node)
            elif node.kind in ("joint", "follow") and optional(node, "visibility") is not None:
                fail("OKL-E-NAME", "Scene relations cannot have a visibility modifier.", node, phase="binding")
        self.check_composition()

    def check_composition(self) -> None:
        # Iterative DFS catches logical recursion even for an empty collection,
        # without confusing a long acyclic class graph with a Python recursion.
        done, visiting = set(), set()
        for start in self.classes:
            if start in done:
                continue
            visiting.add(start)
            stack = [(start, iter(self.effective(start).members.values()))]
            while stack:
                self.budget.tick()
                name, iterator = stack[-1]
                member = next(iterator, None)
                if member is None:
                    stack.pop(); visiting.remove(name); done.add(name)
                    continue
                if member.node.kind not in ("part", "parts"):
                    continue
                child = self.class_reference(member.node)
                if child in visiting:
                    fail("OKL-E-RECURSIVE-COMPOSITION", "Ordinary/generated part composition is recursive.", member.node)
                if child not in done:
                    visiting.add(child)
                    stack.append((child, iter(self.effective(child).members.values())))

    def initializer_type(self, class_name: str, names, node: Any) -> Type:
        steps = _steps(names)
        if not steps or steps[-1].kind != "member":
            fail("OKL-E-READONLY", "An initializer must end in a public parameter or direct built-in field.", node, phase="type")
        cls, i = self.effective(class_name), 0
        while i < len(steps) - 1:
            self.budget.tick(node)
            step = steps[i]
            member = cls.members.get(step.value) if step.kind == "member" else None
            if member is None or member.node.kind not in ("part", "parts"):
                fail("OKL-E-NAME", f"'{step.value}' is not an owned part or collection in this initializer path.", node, phase="binding")
            if member.node.visibility != "public":
                fail("OKL-E-ACCESS", f"Part/collection '{step.value}' is private.", node, phase="binding")
            i += 1
            if member.node.kind == "parts":
                if i >= len(steps) - 1 or steps[i].kind != "key":
                    fail("OKL-E-TYPE", "A generated collection initializer requires one literal key step.", node, phase="type")
                self.key(node, steps[i].value)
                i += 1
            cls = self.effective(self.class_reference(member.node))
        name = steps[-1].value
        member = cls.members.get(name)
        if name in READONLY_FIELDS or member and member.node.kind == "derive":
            fail("OKL-E-READONLY", f"'{name}' is read-only and cannot be assigned.", node, phase="type")
        if member:
            if member.node.visibility != "public":
                fail("OKL-E-ACCESS", f"Parameter '{name}' is private.", node, phase="binding")
            if member.node.kind != "param":
                fail("OKL-E-READONLY", f"'{name}' is not a writable parameter.", node, phase="type")
            return self.parse_type(member.node.type)
        if len(steps) == 1 and name in FIELD_TYPES:
            return FIELD_TYPES[name]
        fail("OKL-E-NAME", f"Initializer cannot assign '{render_path(steps)}'; nested writes must end in a public parameter.", node, phase="binding")

    def _check_initializer(self, node: Any, ctx: Context) -> None:
        written = set()
        class_name = self.class_reference(node)
        for assignment in node.assignments:
            self.budget.tick(assignment)
            token = _token(assignment.path)
            if token in written:
                fail("OKL-E-NAME", f"Initializer target '{render_path(assignment.path)}' is assigned twice.", assignment, phase="binding")
            written.add(token)
            typ = self.initializer_type(class_name, assignment.path, assignment)
            self.expect(self.expression(assignment.value, ctx), typ, assignment.value)

    def check_member_types(self, node: Any, ctx: Context) -> None:
        self.budget.tick(node)
        if node.kind == "parts":
            input_value = self.expression(node.input, ctx)
            if input_value.type.kind != "Keyed":
                fail("OKL-E-TYPE", "A generated part input must be a flat authored Keyed value.", node.input, phase="type")
            self._keyed_leaf(input_value.type.element, node.input)
            bindings = dict(ctx.locals)
            bindings[node.key_name] = Value(STRING)
            bindings[node.value_name] = Value(input_value.type.element)
            self._check_initializer(node, replace(ctx, locals=bindings))
        elif node.kind in ("part", "object"):
            self._check_initializer(node, ctx)
        else:
            super().check_member_types(node, ctx)

    def typecheck_body(self, node: Any, *, class_name: str | None = None,
                       declaring: str | None = None) -> None:
        params, result, _ = self.signature(node)
        if declaring:
            owner = "method:" + declaring + "." + node.name
        else:
            symbol = self._resolve(node, node.name, "function")
            owner = "fn:" + self._nominal(symbol)
        ctx = Context(self_type=class_name, lexical_class=declaring, abstract=True,
                      locals={name: Value(typ) for name, typ in params}, call_owner=owner)
        names = set(ctx.locals)
        for local in node.locals:
            self.budget.tick(local)
            if local.name in names or local.name in PREDEFINED_02:
                fail("OKL-E-NAME", f"Local '{local.name}' duplicates or shadows a predefined symbol.", local, phase="binding")
            typ = self.parse_type(local.type)
            self.expect(self.expression(local.value, ctx), typ, local.value)
            ctx.locals[local.name] = Value(typ)
            names.add(local.name)
        self.expect(self.expression(node.result, ctx), result, node.result)

    def check_static_types(self) -> None:
        for function in self.functions.values():
            self.typecheck_body(function)
        for cls in self.classes.values():
            self.budget.tick(cls.node)
            if cls.name == "Object":
                continue
            for member in cls.members.values():
                if member.node.kind == "method":
                    self.typecheck_body(member.node, class_name=cls.name, declaring=member.declaring)
                elif member.node.kind in ("site", "joint", "follow", "part", "parts"):
                    self.check_member_types(member.node, Context(self_type=cls.name, lexical_class=member.declaring, abstract=True))
            for name, (expression, declaring) in cls.defaults.items():
                typ = FIELD_TYPES.get(name) or self.parse_type(cls.members[name].node.type)
                self.expect(self.expression(expression, Context(self_type=cls.name, lexical_class=declaring, abstract=True)), typ, expression)
            for ancestor in self.class_chain(cls.name):
                if ancestor.node:
                    for statement in ancestor.node.members:
                        if statement.kind == "assert":
                            self.expect(self.expression(statement.condition, Context(self_type=cls.name, lexical_class=ancestor.name, abstract=True)), BOOL, statement.condition)
        for node in self.program.scene.members:
            self.budget.tick(node)
            ctx = Context(scene=True, abstract=True)
            if node.kind == "object":
                self.check_member_types(node, ctx)
            elif node.kind == "action":
                self.expect(self.expression(node.value, ctx), Type("Action"), node.value)
            elif node.kind == "assert":
                self.expect(self.expression(node.condition, ctx), BOOL, node.condition)
            elif node.kind == "event_block":
                self.expect(self.expression(node.time, ctx), quantity_type(TIME), node.time)
                for event in node.events:
                    if event.kind == "release":
                        self.expect(self.path_value(event.path, ctx, event), Type("JointRef"), event)
            elif node.kind in ("site", "joint", "follow"):
                self.check_member_types(node, ctx)
        done, active = set(), set()
        for start in self.call_edges:
            if start in done:
                continue
            active.add(start)
            stack = [(start, iter(self.call_edges.get(start, ())))]
            while stack:
                self.budget.tick()
                name, children = stack[-1]
                child = next(children, None)
                if child is None:
                    stack.pop(); active.remove(name); done.add(name)
                elif child in active:
                    fail("OKL-E-DEPENDENCY-CYCLE", f"Pure function/method dependencies recurse through '{child}'.", self.program)
                elif child not in done:
                    active.add(child)
                    stack.append((child, iter(self.call_edges.get(child, ()))))

    def name(self, name: str, ctx: Context, node: Any) -> Value:
        if (name in SURFACE_CALLS and self.linked.modules[node.source_id].ast.profile == SURFACE_PROFILE
                and name not in ctx.locals):
            return Value(Type("BuiltinCallable"), name)
        if name == "self" and not ctx.abstract and ctx.self_path is not None:
            value = super().name(name, ctx, node)
            self.budget.charge_value(value, node)
            # Retain a strong value reference with the origin. CPython ID reuse
            # therefore cannot grant a later unrelated value this authority.
            self._lexical_self_origins[id(value)] = (value, ctx.self_path)
            return value
        if name in ctx.locals or name in PREDEFINED_02:
            if name == "len":
                return Value(Type("BuiltinCallable"), "len")
            value = super().name(name, ctx, node)
            if not ctx.abstract:
                for path in self._value_taints.get(id(value), ()):
                    self._mark_generated(path, node)
            return value
        module = self.linked.modules[node.source_id]
        if name in module.imports:
            return Value(Type("ModuleNamespace"), (node.source_id, name))
        if name in module.symbols:
            symbol = self._resolve(node, name)
            nominal = self._nominal(symbol)
            if symbol.kind == "class":
                return Value(Type("ClassName"), nominal)
            return Value(Type("Callable"), Callable(symbol.node, "fn:" + nominal))
        if ctx.scene and name in self.scene_names:
            declaration = self.scene_names[name]
            if declaration.kind == "object":
                return Value(Type("Ref", name=self.class_reference(declaration)), name if not ctx.abstract else UNKNOWN)
        return super().name(name, ctx, node)

    def _is_generated(self, path: str) -> bool:
        provenance = self.occurrence_provenance.get(path)
        return bool(provenance and provenance.get("generated_ancestor"))

    def _mark_generated(self, path: str, node: Any) -> None:
        if self._shape_stack:
            fail("OKL-E-DEPENDENCY-CYCLE", "Collection shape depends on a generated collection or another generated occurrence.",
                 node, details={"construction_rule": "CON-007", "generated_dependency": path,
                                "shape_owner": self._shape_stack[-1]})
        for key in self.pending:
            self.generated_dependencies.setdefault(key, set()).add(path)

    def member(self, value: Value, name: str, ctx: Context, node: Any) -> Value:
        if value.type.kind == "ModuleNamespace":
            source_id, alias = value.value
            symbol = self.linked.resolve_definition(source_id, (alias, name), node=node)
            self.bindings[id(node)] = tuple(symbol.element_id)
            nominal = self._nominal(symbol)
            return (Value(Type("ClassName"), nominal) if symbol.kind == "class" else
                    Value(Type("Callable"), Callable(symbol.node, "fn:" + nominal)))
        if value.type.kind == "Ref":
            actual = value.value if value.known and not ctx.abstract else None
            if actual is not None:
                for taint in self._value_taints.get(id(value), ()):
                    self._mark_generated(taint, node)
                origin = self._lexical_self_origins.get(id(value))
                direct_self = origin is not None and origin[0] is value and origin[1] == actual
                if (self._is_generated(actual) and self._shape_stack and
                        actual not in (self._shape_stack[-1], ctx.self_path) and not direct_self):
                    self._mark_generated(actual, node)
                cls = self.instances[actual].cls
            else:
                cls = self.effective(value.type.name)
            member = cls.members.get(name)
            if member is not None:
                self.access(member, ctx, node)
                self.bindings[id(node)] = self.definition_id(cls.name, name)
                if member.node.kind == "parts":
                    typ = Type("Keyed", element=Type("Ref", name=self.class_reference(member.node)))
                    if actual is None:
                        return Value(typ)
                    path = actual + "." + name
                    self._mark_generated(path, node)
                    self._ensure_collection(path)
                    collection = self.collections[path]
                    entries = tuple((key, Value(typ.element, collection["entries"][key]))
                                    for key in collection["ordered_keys"])
                    result = Value(typ, KeyedValue(entries))
                    self.budget.charge_value(result, node)
                    self._value_taints[id(result)] = {path}
                    self._tainted_values[id(result)] = result
                    return result
                if member.node.kind == "part":
                    return Value(Type("Ref", name=self.class_reference(member.node)),
                                 actual + "." + name if actual is not None else UNKNOWN)
        return super().member(value, name, ctx, node)

    def index_value(self, value: Value, index: Value, node: Any, ctx: Context) -> Value:
        if value.type.kind != "Keyed":
            fail("OKL-E-TYPE", "Read indexing is defined only for Keyed values.", node, phase="type")
        index = self.expect(index, STRING, node)
        if ctx.abstract or not value.known or not index.known:
            return Value(value.type.element)
        self.key(node, index.value)
        try:
            result = value.value.lookup(index.value)
        except KeyError:
            fail("OKL-E-NAME", f"Keyed value has no entry '{index.value}'.", node, phase="binding",
                 details={"missing_key": index.value})
        taints = self._value_taints.get(id(value), set())
        for path in taints:
            self._mark_generated(path, node)
        if taints:
            self._value_taints.setdefault(id(result), set()).update(taints)
            self._tainted_values[id(result)] = result
        return result

    def path_value(self, steps, ctx: Context, node: Any) -> Value:
        path = _steps(steps)
        if not path or path[0].kind != "member":
            fail("OKL-E-NAME", "A source path must begin with a member.", node, phase="binding")
        result = self.name(path[0].value, ctx, node)
        for step in path[1:]:
            self.budget.tick(node)
            result = (self.member(result, step.value, ctx, node) if step.kind == "member" else
                      self.index_value(result, Value(STRING, step.value), node, ctx))
        return result

    def expression(self, node: Any, ctx: Context) -> Value:
        self.budget.tick(node)
        self._expression_depth += 1
        try:
            if self._expression_depth > 128:
                fail("OKL-E-RESOURCE", "Pure expression/call nesting exceeds bounded construction work.", node, phase="support")
            if node.kind == "keyed":
                element = self.parse_type(node.element_type)
                self._keyed_leaf(element, node)
                if len(node.entries) > MAX_KEYED_ENTRIES:
                    fail("OKL-E-RESOURCE", "Keyed input exceeds 256 entries.", node, phase="support",
                         details={"budget": "keyed_entries", "limit": MAX_KEYED_ENTRIES,
                                  "consumed": len(node.entries)})
                keys, entries, origins = set(), [], {}
                for entry in node.entries:
                    self.budget.tick(entry)
                    self.key(entry, entry.key)
                    if entry.key in keys:
                        fail("OKL-E-ID", f"Keyed literal duplicates stable key '{entry.key}'.", entry, phase="binding")
                    keys.add(entry.key)
                    val = self.expect(self.expression(entry.value, ctx), element, entry.value)
                    if not ctx.abstract:
                        entries.append((entry.key, val))
                        origins[entry.key] = entry
                if ctx.abstract:
                    return Value(Type("Keyed", element=element))
                payload = KeyedValue(tuple(sorted(entries, key=lambda item: item[0])))
                result = Value(Type("Keyed", element=element), payload)
                self.budget.charge_value(result, node)
                self._keyed_origins[id(payload)] = origins
                self._keyed_payloads[id(payload)] = payload
                return result
            if node.kind == "index":
                value = self.expression(node.target, ctx)
                index = self.expression(node.index, ctx)
                return self.index_value(value, index, node, ctx)
            return super().expression(node, ctx)
        finally:
            self._expression_depth -= 1

    def builtin(self, name: str, args: list[Value], node: Any, ctx: Context) -> Value:
        if name in SURFACE_CALLS:
            if self.linked.modules[node.source_id].ast.profile != SURFACE_PROFILE:
                fail("OKL-E-CAPABILITY-UNSUPPORTED", "Surface constructors need the surface-0.1 profile.",
                     node, phase="support")
            return surface_builtin(self, name, args, node, ctx)
        if name != "len":
            return super().builtin(name, args, node, ctx)
        if len(args) != 1 or args[0].type.kind != "Keyed":
            fail("OKL-E-TYPE", "len() requires exactly one Keyed value.", node, phase="type")
        for path in self._value_taints.get(id(args[0]), ()) if not ctx.abstract else ():
            self._mark_generated(path, node)
        return Value(INT, len(args[0].value)) if not ctx.abstract and args[0].known else Value(INT)

    def invoke(self, function: Callable, args: list[Value], node: Any, caller: Context) -> Value:
        self.budget.tick(node)
        if not caller.abstract:
            if function.lexical_class is not None:
                ident = self.definition_id(function.lexical_class, function.node.name)
            else:
                ident = tuple(self._resolve(function.node, function.node.name).element_id)
            for key in self.pending:
                self.call_dependencies.setdefault(key, set()).add(ident)
        return super().invoke(function, args, node, caller)

    def guarded(self, key: tuple[str, str], node: Any, compute) -> Value:
        self.budget.tick(node)
        for parent in self.pending:
            self.dependencies.setdefault(parent, set()).add(key)
        if key in self.memo:
            for path in self.generated_dependencies.get(key, ()):
                self._mark_generated(path, node)
            for parent in self.pending:
                self.dependencies.setdefault(parent, set()).update(self.dependencies.get(key, ()))
                self.call_dependencies.setdefault(parent, set()).update(self.call_dependencies.get(key, ()))
            return self.memo[key]
        if key in self.pending:
            fail("OKL-E-DEPENDENCY-CYCLE", "Pure value dependencies form a cycle.", node,
                 details={"dependency_path": [list(item) for item in self.pending + [key]]})
        if len(self.pending) >= 128:
            fail("OKL-E-RESOURCE", "Pure dependency nesting exceeds bounded construction work.", node, phase="support")
        self.pending.append(key)
        try:
            computed = compute()
            # A derived/default/override binding has its own dependency route
            # even when its immutable value equals or reuses another binding.
            # Attaching taint to the reused wrapper would poison the original.
            result = self._inherit_value_info(computed, Value(computed.type, computed.value, computed.frame, computed.hint))
            self.budget.charge_value(result, node)
            self.memo[key] = result
            if self.generated_dependencies.get(key):
                self._value_taints.setdefault(id(result), set()).update(self.generated_dependencies[key])
                self._tainted_values[id(result)] = result
            return result
        finally:
            self.pending.pop()

    def _layer_bindings(self, path: str, node: Any, context: Context,
                        inherited: list[InitializerBinding]) -> None:
        self.initializers.append((path, node.assignments, context))
        own = [InitializerBinding(assignment, context, _steps(assignment.path), path)
               for assignment in node.assignments]
        forwards = self._forwards.setdefault(path, {})
        for binding in own + inherited:
            self.budget.tick(binding.assignment)
            steps = binding.steps
            if len(steps) == 1:
                name = steps[0].value
                self.instances[path].overrides[name] = BoundExpression(binding.assignment.value, binding.context)
                self.override_bindings[(path, name)] = binding
            else:
                consumed = 2 if steps[1].kind == "key" else 1
                token = _token(steps[:consumed])
                forwards.setdefault(token, []).append(replace(binding, steps=steps[consumed:]))

    def _register_tree(self, node: Any, path: str, owner: str | None, ids: tuple[str, ...],
                       context: Context, inherited: list[InitializerBinding], *,
                       steps: tuple, depth: int, generated: dict | None = None,
                       declaration_id: tuple[str, ...] | None = None) -> None:
        from .syntax02 import PathStep
        self.budget.tick(node)
        if depth > MAX_OWNERSHIP_DEPTH:
            fail("OKL-E-RESOURCE", "Expanded ownership exceeds 64 edges.", node, phase="support",
                 details={"budget": "ownership_depth", "limit": MAX_OWNERSHIP_DEPTH, "consumed": depth})
        if len(self.instances) >= self.budget.limits["max_objects"]:
            self.budget.exceeded("max_objects", len(self.instances) + 1, node)
        if len(path.encode("utf-8")) > MAX_PATH_BYTES or len(ids) > 256:
            fail("OKL-E-RESOURCE", "Expanded path or element identity exceeds the construction bound.", node, phase="support")
        if path in self.instances:
            fail("OKL-E-ID", "An expanded occurrence path was registered twice.", node, phase="binding")
        class_id = self.class_reference(node)
        cls = self.effective(class_id)
        name = generated["key"] if generated else node.name
        role = generated["key"] if generated else node.key
        model = ObjectModel(path, name, class_id, ids, owner=owner, role=role, span=node)
        self.instances[path] = Instance(model, cls)
        self.model.objects[path] = model
        self.model.sites[path + ".origin"] = SiteModel(path + ".origin", ids + ("@system", "origin"),
                                                       path, Pose(path + ".frame"), span=node)
        root_path = path if owner is None else self.occurrence_provenance[owner]["root_path"]
        definition = self._class_symbols.get(class_id)
        parent_generated = self.occurrence_provenance[owner].get("generated_ancestor") if owner else None
        self.occurrence_provenance[path] = {
            "path": path, "element_id": ids, "kind": "object", "root_path": root_path,
            "owner_path": owner, "path_steps": steps, "declaration_node": node,
            "declaration_definition_id": declaration_id,
            "definition_node": definition.node if definition else None,
            "definition_id": self.definition_id(class_id), "class_id": class_id,
            "generated": generated, "generated_ancestor": path if generated else parent_generated,
            "ownership_depth": depth,
        }
        self._layer_bindings(path, node, context, inherited)
        for member_name, member in cls.members.items():
            self.budget.tick(member.node)
            child = member.node
            scope = Context(path, cls.name, member.declaring)
            member_path = path + "." + member_name
            member_id = ids + (child.key,)
            definition_id = self.definition_id(cls.name, member_name)
            child_steps = steps + (PathStep("member", member_name, child.start, child.end),)
            if child.kind == "part":
                forwarded = self._forwards[path].get((("member", member_name),), [])
                self._register_tree(child, member_path, path, member_id, scope, forwarded,
                                    steps=child_steps, depth=depth + 1, declaration_id=definition_id)
            elif child.kind == "parts":
                self.collections[member_path] = {
                    "path": member_path, "name": member_name, "element_id": member_id,
                    "owner_path": path, "root_path": root_path, "definition_id": definition_id,
                    "declaration_node": child, "input_node": child.input,
                    "class_id": self.class_reference(child), "path_steps": child_steps,
                    "context": scope, "ordered_keys": [], "entries": {}, "entry_ids": {},
                    "input_entry_nodes": {}, "ownership_depth": depth,
                }
                self._collection_state[member_path] = "pending"
            elif child.kind == "site":
                self.sites[member_path] = (child, scope, member_id, path)
            elif child.kind == "joint":
                self.joints[member_path] = (child, scope, member_id)
            elif child.kind == "follow":
                self.follows[member_path] = (child, scope, member_id)

    def _ensure_collection(self, path: str) -> None:
        from .syntax02 import PathStep
        state = self._collection_state[path]
        if state == "done":
            return
        collection = self.collections[path]
        node, owner, ctx = collection["declaration_node"], collection["owner_path"], collection["context"]
        self.budget.tick(node)
        if state == "expanding":
            fail("OKL-E-DEPENDENCY-CYCLE", "Generated collection shape dependencies form a cycle.", node)
        self._collection_state[path] = "expanding"
        self._shape_stack.append(owner)
        try:
            value = self.guarded((owner, "@shape:" + node.name), node.input,
                                 lambda: self.expression(node.input, ctx))
            if value.type.kind != "Keyed" or not value.known:
                fail("OKL-E-TYPE", "Generated input must resolve to a known flat Keyed value.", node.input, phase="type")
            self._keyed_leaf(value.type.element, node.input)
            for taint in self._value_taints.get(id(value), ()):
                self._mark_generated(taint, node.input)
        finally:
            self._shape_stack.pop()
        keys = [key for key, _ in value.value.entries]
        if len(keys) > MAX_KEYED_ENTRIES:
            fail("OKL-E-RESOURCE", "Generated collection exceeds 256 entries.", node, phase="support")
        if keys != sorted(set(keys)):
            fail("OKL-E-ID", "Generated input keys are not unique canonical stable keys.", node, phase="binding")
        for key in keys:
            self.key(node, key)
        pending = self._forwards[owner]
        for token, overrides in pending.items():
            self.budget.tick(node)
            if token[0] == ("member", node.name) and token[1][1] not in keys:
                fail("OKL-E-NAME", f"Initializer selects absent generated key '{token[1][1]}'.", overrides[-1].assignment,
                     phase="binding", details={"missing_key": token[1][1], "collection_path": path})
        # Freeze membership, then register all child shells and ordinary owned
        # descendants before evaluating any generated-body field expression.
        collection["ordered_keys"] = keys
        origins = self._keyed_origins.get(id(value.value), {})
        collection["input_entry_nodes"] = {key: origins.get(key) for key in keys}
        collection["input_value"] = value
        for key, leaf in value.value.entries:
            self.budget.tick(node)
            child_path = path + "[" + json.dumps(key) + "]"
            child_id = collection["element_id"] + (key,)
            collection["entries"][key] = child_path
            collection["entry_ids"][key] = child_id
        for key, leaf in value.value.entries:
            child_path = collection["entries"][key]
            locals_ = dict(ctx.locals)
            locals_[node.key_name], locals_[node.value_name] = Value(STRING, key), leaf
            child_context = replace(ctx, locals=locals_)
            forwarded = pending.get((("member", node.name), ("key", key)), [])
            generated = {
                "collection_path": path, "collection_id": collection["element_id"],
                "collection_definition_id": collection["definition_id"], "key": key,
                "input_node": node.input, "input_entry_node": origins.get(key),
            }
            self._register_tree(node, child_path, owner, collection["entry_ids"][key], child_context,
                                forwarded, steps=collection["path_steps"] + (PathStep("key", key, node.start, node.end),),
                                depth=collection["ownership_depth"] + 1, generated=generated,
                                declaration_id=collection["definition_id"])
        self._collection_state[path] = "done"

    def assignments(self, node: Any, required: set[str]) -> dict[str, Any]:
        result = {}
        for assignment in node.assignments:
            self.budget.tick(assignment)
            steps = _steps(assignment.path)
            if len(steps) != 1 or steps[0].kind != "member" or steps[0].value not in required:
                fail("OKL-E-NAME", f"Allowed {node.kind} fields are {', '.join(sorted(required))}.", assignment, phase="binding")
            name = steps[0].value
            if name in result:
                fail("OKL-E-NAME", f"Field '{name}' is assigned twice.", assignment, phase="binding")
            result[name] = assignment
        missing = required - set(result)
        if missing:
            fail("OKL-E-NAME", f"Missing required {node.kind} fields: {', '.join(sorted(missing))}.", node, phase="binding")
        return result

    def resolve_objects(self) -> None:
        # Mechanical objects retain one motion authority. The generated loft
        # contributes visual mesh data only, never implicit physical mass.
        super().resolve_objects()
        from .syntax import Node
        self.surface_meshes = {}
        remaining_vertices = 250_000
        for path, obj in self.model.objects.items():
            recipe = obj.geometry
            if not isinstance(recipe, dict) or recipe.get("kind") not in ("loft", "placed"):
                continue
            surface = recipe.get("surface", recipe)
            location = Node("span", surface["start"], surface["end"],
                            source_id=surface["source_id"])
            try:
                mesh, local_pose = materialize_surface(
                    recipe, max_vertices=remaining_vertices,
                    check=lambda: self.budget.tick(location))
            except SurfaceError as error:
                fail(error.code, str(error), location, details=error.details)
            remaining_vertices -= len(mesh.positions)
            self.surface_meshes[path] = {
                "mesh": mesh, "local_pose": local_pose,
                "source_id": surface["source_id"], "element_id": obj.element_id,
                "object_path": path,
            }

    def scene_fields(self) -> None:
        fields = {}
        for node in self.program.scene.members:
            self.budget.tick(node)
            if node.kind != "assign":
                continue
            steps = _steps(node.path)
            if len(steps) != 1 or steps[0].kind != "member" or steps[0].value not in ("duration", "gravity"):
                fail("OKL-E-NAME", "Scene assignments are limited to duration and gravity.", node, phase="binding")
            name = steps[0].value
            if name in fields:
                fail("OKL-E-NAME", f"Scene field '{name}' must occur exactly once.", node, phase="binding")
            fields[name] = node
        if set(fields) != {"duration", "gravity"}:
            fail("OKL-E-NAME", "A scene must author duration and gravity exactly once each.", self.program.scene, phase="binding")
        ctx = Context(scene=True)
        for name, typ in (("duration", quantity_type(TIME)),
                          ("gravity", Type("Vector3", element=quantity_type(ACCELERATION)))):
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
            self.budget.tick(node)
            if node.kind != "event_block":
                continue
            value = self.expect(self.expression(node.time, Context(scene=True)), quantity_type(TIME), node.time)
            time_ = Fraction.from_float(value.value)
            if time_ < 0 or time_ > self.model.duration:
                fail("OKL-E-EVENT-ORDER", "Event time must lie in [0, scene.duration].", node.time)
            if time_ in seen:
                fail("OKL-E-EVENT-ORDER", "Equal canonical event times require one ordered sequence block.", node.time)
            seen.add(time_)
            events = []
            for event in node.events:
                self.budget.tick(event)
                if event.kind == "release":
                    target = self.expect(self.path_value(event.path, Context(scene=True), event), Type("JointRef"), event)
                    events.append(Event("release", target.value, event))
                else:
                    if event.name not in self.actions:
                        fail("OKL-E-NAME", f"'{event.name}' is not a named action instance.", event, phase="binding")
                    events.append(Event(event.kind, event.name, event))
            self.model.events.append(EventBlock(time_, events, node))
        self.model.events.sort(key=lambda block: block.time)

    def initializer_target(self, path: str, parameter: str) -> dict:
        from .syntax02 import PathStep
        if path not in self.instances:
            return {"available": False, "reason": "No object occurrence has this path."}
        record = self.occurrence_provenance[path]
        root_path = record["root_path"]
        root = self.occurrence_provenance[root_path]
        member = self.instances[path].cls.members.get(parameter)
        if member is None or member.node.kind != "param":
            return {"available": False, "reason": "Only a public declared parameter has an occurrence initializer target.",
                    "root_path": root_path}
        steps = record["path_steps"][1:] + (PathStep("member", parameter, member.node.start, member.node.end),)
        try:
            self.initializer_type(self.instances[root_path].cls.name, steps, member.node)
        except OntoKinError as error:
            return {"available": False, "reason": error.diagnostic.message, "root_path": root_path}
        binding = self.override_bindings.get((path, parameter))
        assignment = (binding.assignment if binding and binding.origin_path == root_path
                      and binding.context.scene else None)
        return {"available": True, "root_path": root_path, "element_id": root["element_id"],
                "root_node": root["declaration_node"], "parameter_path": steps,
                "rendered_path": render_path(steps), "assignment_node": assignment}

    def location(self, node: Any) -> dict | None:
        if node is None:
            return None
        source = self.source_for(node)
        return {"source_id": node.source_id, "source_revision": source.revision,
                "filename": source.filename, "start_byte": node.start, "end_byte": node.end}

    def _attach_provenance(self) -> None:
        sources = {}
        for source_id, module in self.linked.modules.items():
            self.budget.tick(module.ast)
            sources[source_id] = {"source_id": source_id, "source_revision": module.unit.revision,
                                  "filename": module.unit.filename, "package_id": module.unit.package_id,
                                  "version": module.unit.version, "module_name": module.ast.module_name,
                                  "module_key": module.ast.module_key}
        self.model.source_provenance = sources
        for path, record in self.occurrence_provenance.items():
            self.budget.tick(record["declaration_node"])
            generated = record["generated"]
            self.model.occurrence_provenance[path] = {
                "path": path, "element_id": list(record["element_id"]),
                "owner_path": record["owner_path"], "root_path": record["root_path"],
                "path_steps": [{"kind": step.kind, "value": step.value} for step in record["path_steps"]],
                "definition_id": list(record["definition_id"]), "class_id": record["class_id"],
                "declaration": self.location(record["declaration_node"]),
                "definition": self.location(record["definition_node"]),
                "declaration_definition_id": list(record["declaration_definition_id"]) if record["declaration_definition_id"] else None,
                "generated": None if generated is None else {
                    "collection_path": generated["collection_path"],
                    "collection_id": list(generated["collection_id"]),
                    "collection_definition_id": list(generated["collection_definition_id"]),
                    "key": generated["key"], "input": self.location(generated["input_node"]),
                    "input_entry": self.location(generated["input_entry_node"]),
                    "unique_declaration_span": False,
                },
                "generated_ancestor": record["generated_ancestor"],
            }
        for path, record in self.collections.items():
            self.budget.tick(record["declaration_node"])
            self.model.collection_provenance[path] = {
                "path": path, "name": record["name"], "element_id": list(record["element_id"]),
                "owner_path": record["owner_path"], "definition_id": list(record["definition_id"]),
                "declaration": self.location(record["declaration_node"]),
                "input": self.location(record["input_node"]), "ordered_keys": list(record["ordered_keys"]),
                "entries": {key: {"path": record["entries"][key], "element_id": list(record["entry_ids"][key])}
                            for key in record["ordered_keys"]},
                "physical_participation": "none",
            }
        # Source indexes and repeated value views are bounded before callers can
        # serialize them. Values are flat; their logical counts were charged
        # before producing this JSON-compatible view.
        envelope = {"sources": self.model.source_provenance,
                    "occurrences": self.model.occurrence_provenance,
                    "collections": self.model.collection_provenance,
                    "properties": {path: dict(obj.properties)
                                   for path, obj in self.model.objects.items()}}
        try:
            bounded_data(envelope, max_bytes=MAX_JSON_BYTES,
                         max_entries=self.budget.limits["max_value_entries"], check=self.budget.tick)
        except JSONLimitError as error:
            fail("OKL-E-RESOURCE", "Constructed provenance/value materialization exceeds its JSON bound.",
                 self.program, phase="support", details=error.details)

    def run(self):
        from .syntax02 import PathStep
        if self.level not in ("represented", "constructed", "evaluated", "delivered"):
            fail("OKL-E-CAPABILITY-UNSUPPORTED", f"Unknown requested output level '{self.level}'.", self.program, phase="support")
        self.bind()
        self.check_static_types()
        context = Context(scene=True)
        prefix = (self.model.module_key, self.model.scene_key)
        for node in self.program.scene.members:
            self.budget.tick(node)
            if node.kind == "object":
                self._register_tree(node, node.name, None, prefix + (node.key,), context, [],
                                    steps=(PathStep("member", node.name, node.start, node.end),), depth=0)
            elif node.kind == "joint":
                self.joints[node.name] = (node, context, prefix + (node.key,))
            elif node.kind == "follow":
                self.follows[node.name] = (node, context, prefix + (node.key,))
            elif node.kind == "action":
                self.actions[node.name] = node
        # Expansion can append nested collection records; iteration by pending
        # batches never mutates a dictionary iterator or evaluates a body early.
        while True:
            pending = [path for path, state in self._collection_state.items() if state != "done"]
            if not pending:
                break
            for path in pending:
                self._ensure_collection(path)
        self.scene_fields()
        self.resolve_objects()
        for path in self.actions:
            self.action_value(path)
        self.assertions()
        self.relation_validation()
        self.event_blocks()
        requires = tuple(self.linked.capabilities)
        self.model.requested_capabilities = tuple(node.value for node in requires)
        if requires and self.level != "represented":
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "Required capabilities are not supplied by " + self.model.profile + ": " +
                 ", ".join(self.model.requested_capabilities), requires[0], phase="support")
        if self.level == "delivered":
            target = "ontokin.glb/0.3" if self.model.profile == "surface-0.1" else "ontokin.glb/0.2"
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "Delivery requires the explicit " + target + " target.", self.program, phase="support")
        self._attach_provenance()
        self.budget.tick(self.program)
        return self.model

    def annotate(self, error: OntoKinError) -> None:
        diagnostic = error.diagnostic
        if diagnostic.element_id is not None or diagnostic.node is None or diagnostic.code in ("OKL-E-ID", "OKL-E-LEXICAL", "OKL-E-SYNTAX"):
            return
        node = diagnostic.node
        source_id = getattr(node, "source_id", None)
        candidates = []
        for ident, symbol in self.definitions.items():
            if symbol.source_id == source_id and symbol.node.start <= node.start <= node.end <= symbol.node.end:
                candidates.append((symbol.node.end - symbol.node.start, ident))
        if source_id == self.program.source_id and self.program.scene.start <= node.start <= node.end <= self.program.scene.end:
            candidates.append((self.program.scene.end - self.program.scene.start,
                               (self.program.module_key, self.program.scene.key)))
        if candidates:
            diagnostic.element_id = list(min(candidates, key=lambda item: item[0])[1])


def compile_construction(bundle, *, level: str = "represented", budgets: dict | None = None,
                         check: Check[[], None] | None = None) -> ConstructionCompiler:
    """Compile a sealed bundle; timeline validation remains an explicit step.

    No filesystem/network effects occur. Cancellation/deadline exceptions from
    ``check`` propagate unchanged. Invalid/source/support failures use registered
    OntoKin diagnostics with original source nodes and stable known identities.
    """
    from .linker import link_program
    budget = ConstructionBudget(budgets, check)
    budget.tick()
    linked = link_program(bundle, check=budget.tick)
    compiler = ConstructionCompiler(linked, level, budget)
    try:
        compiler.run()
        return compiler
    except OntoKinError as error:
        compiler.annotate(error)
        raise
    except RecursionError:
        fail("OKL-E-RESOURCE", "Construction exceeded bounded host recursion work.", compiler.program,
             phase="support", details={"budget": "host_recursion", "profile": PROFILE})
