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
import math
import time
from typing import Any, Callable as Check

from .diagnostics import Diagnostic, OntoKinError
from .json_limits import JSONLimitError
from .model import Event, EventBlock, ImpulsePayload, ObjectModel, Pose, SiteModel
from .surface_runtime import SURFACE_CALLS, SURFACE_TYPES, SURFACE_PROFILE, surface_builtin, materialize_surface
from .surface import SurfaceError
from .extrusion_runtime import EXTRUSION_CALLS, EXTRUSION_TYPES, extrusion_builtin
from .holes_runtime import HOLES_CALLS, HOLES_TYPES, holes_builtin
from .ring_loft_runtime import RING_LOFT_CALLS, RING_LOFT_TYPES, ring_loft_builtin
from .framed_loft_runtime import FRAMED_LOFT_CALLS, FRAMED_LOFT_TYPES, framed_loft_builtin
from .pockets_runtime import POCKETS_CALLS, POCKETS_TYPES, pockets_builtin
from .texture_bundle import TextureBundle
from .texture_runtime import (TEXTURE_CALLS, TEXTURE_TYPES, texture_builtin,
                              validate_texture_closure, texture_coordinates)
from .profile_capabilities import (BUDGET_PROFILE, EXTRUSION_PROFILE, HOLES_PROFILE, RING_LOFT_PROFILE, FRAMED_LOFT_PROFILE, POCKETS_PROFILE, TEXTURE_PROFILE, KEYED_TRANSFORM_PROFILE, KEYED_REDUCTION_PROFILE, KEYED_FILTER_PROFILE, KEYED_MERGE_PROFILE, KEYED_ZIP_PROFILE, KEYED_REKEY_PROFILE, STRING_CONCAT_PROFILE, KEYED_REKEY_PROFILES, KEYED_ZIP_PROFILES, KEYED_MERGE_PROFILES, KEYED_FILTER_PROFILES, KEYED_REDUCTION_PROFILES, KEYED_TRANSFORM_PROFILES, TEXTURE_PROFILES, POCKETS_PROFILES, FRAMED_LOFT_PROFILES, RING_LOFT_PROFILES, HOLES_PROFILES, EXTRUSION_PROFILES, EXECUTION_PROFILES, REACH_PROFILES, IMPULSE_PROFILES,
                                   SURFACE_PROFILES)
from .validator import (BUILTIN_TYPES, FIELD_TYPES,
                        PREDEFINED, READONLY_FIELDS, KEY_RE, BoundExpression, Callable,
                        Context, EffectiveClass, Instance, Member, Validator,
                        fail, optional)
from .values import (ACCELERATION, ALIASES, BOOL, INT, LENGTH, STRING, TIME,
                     UNKNOWN, KeyedValue, Type, Value, binary, bounded_data, quantity_type)
from .string_concat import concat_strings


PROFILE = "construction-0.1"
IMPULSE_PROFILE = "impulse-0.1"
FORCE_PROFILE = "force-0.1"
REACH_PROFILE = "planar-reach-0.1"
IMPULSE_DIMENSION = (1, 1, -1, 0)
PREDEFINED_02 = PREDEFINED | {"Keyed", "len"}
MAX_KEYED_ENTRIES = 256
MAX_OWNERSHIP_DEPTH = 64
MAX_PATH_BYTES = 32768
MAX_JSON_BYTES = 4 * 1024 * 1024
# Only constructors with immutable, context-free value payloads are eligible.
# Names still resolve in their actual lexical context; a shadowing local
# disables the fold. Geometry, source references, actions and surface recipes
# deliberately retain their ordinary occurrence/provenance paths.
_CONSTANT_CALLS = frozenset({"real", "abs", "min", "max", "near", "sqrt", "sin", "cos",
    "vec3", "vector", "point", "quat", "axis_angle", "range", "rgba"})
_IMMUTABLE_SURFACE_CALLS = frozenset({"loft_section", "surface_material"})
_PARAMETER_CALLS = _CONSTANT_CALLS | _IMMUTABLE_SURFACE_CALLS
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
        self.profile = PROFILE
        self.callback_error: BaseException | None = None

    def tick(self, node: Any = None, amount: int = 1) -> None:
        if self.check is not None:
            try:
                self.check()
            except BaseException as error:
                self.callback_error = error
                raise
        self.operations += amount
        if self.operations > self.limits["max_operations"]:
            self.exceeded("max_operations", self.operations, node)
        elapsed = (time.monotonic() - self.started) * 1000
        if elapsed > self.limits["max_elapsed_ms"]:
            self.exceeded("max_elapsed_ms", elapsed, node)

    def exceeded(self, name: str, consumed: int | float, node: Any = None) -> None:
        fail("OKL-E-RESOURCE", f"Construction exceeded {name}.", node, phase="support",
             details={"budget": name, "limit": self.limits[name], "consumed": consumed,
                      "profile": self.profile})

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


class ExecutionConstructionBudget(ConstructionBudget):
    """Adapt one admitted source/CLI ledger without changing legacy storage."""

    def __init__(self, budgets: dict | None = None, check: Check[[], None] | None = None,
                 *, execution_budget):
        if budgets is not None and (not isinstance(budgets, dict) or set(budgets) - set(LIMITS)):
            fail("OKL-E-RESOURCE", "Unknown construction budget field.", phase="support")
        from .execution_budget import SharedExecutionBudget
        if (not isinstance(execution_budget, SharedExecutionBudget)
                or execution_budget.resolved is None or check is not None):
            fail("OKL-E-RESOURCE", "Construction requires one admitted execution context.",
                 phase="support", details={"budget_reason": "execution_context_required"})
        if set(budgets or {}) & {"max_operations", "max_elapsed_ms"}:
            fail("OKL-E-RESOURCE", "Execution limits were already resolved at entry admission.",
                 phase="support", details={"budget_reason": "execution_context_required"})
        self.limits = dict(LIMITS)
        self.limits.update(execution_budget.limits)
        for name, value in (budgets or {}).items():
            if type(value) is not int or not 1 <= value <= LIMITS[name]:
                fail("OKL-E-RESOURCE", f"{name} must be an integer from 1 through {LIMITS[name]}.",
                     phase="support", details={"budget": name, "limit": LIMITS[name]})
            self.limits[name] = value
        self.execution_budget = execution_budget
        self.value_entries = 0
        self.started = execution_budget.started
        self.check = None
        self.profile = PROFILE
        self.callback_error: BaseException | None = None

    @property
    def operations(self):
        return self.execution_budget.operations

    def tick(self, node: Any = None, amount: int = 1) -> None:
        try:
            self.execution_budget.tick(node, amount=amount)
        except BaseException as error:
            if error is self.execution_budget.callback_error:
                self.callback_error = error
            raise

    def report(self) -> dict:
        return {"limits": dict(self.limits), "operations": self.operations,
                "value_entries": self.value_entries,
                "elapsed_ms": self.execution_budget.elapsed_ms()}


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


@dataclass(frozen=True)
class KeyedTransformOrigin:
    """Source derivation only, with no writable occurrence or iteration ID."""

    expression: Any
    body: Any
    input: Any
    input_type: Type
    output_type: Type
    key: str | None = None
    input_entry: Any = None


@dataclass(frozen=True)
class KeyedReductionOrigin:
    """An aggregate's source derivation, without a writable iteration identity."""

    expression: Any
    input: Any
    seed: Any
    body: Any
    input_type: Type
    accumulator_type: Type


@dataclass(frozen=True)
class KeyedFilterOrigin:
    """Membership derivation only, with original source repair authority."""

    expression: Any
    input: Any
    predicate: Any
    element_type: Type


@dataclass(frozen=True)
class KeyedMergeOrigin:
    """Original operand contribution, without a writable synthetic identity."""

    expression: Any
    left: Any
    right: Any
    element_type: Type
    input_side: str


@dataclass(frozen=True)
class KeyedZipOrigin:
    """An aggregate or actual paired source contribution; never edit authority."""

    expression: Any
    left: Any
    right: Any
    body: Any
    left_type: Type
    right_type: Type
    output_type: Type
    key: str | None = None
    left_entry: Any = None
    right_entry: Any = None


@dataclass(frozen=True)
class KeyedRekeyOrigin:
    """Original payload and computed key lineage, never writable identity."""

    expression: Any
    input: Any
    body: Any
    element_type: Type
    old_key: str | None = None
    new_key: str | None = None
    input_entry: Any = None


def _materialize_reach_surface(recipe, *, max_vertices, work, check):
    """Reuse immutable loft construction, retaining each occurrence's limit.

    The complete typed recipe snapshot is shared with the source exporter;
    this namespace retains unplaced triangles and never supplies reader proof.
    Each caller receives its own placement value and provenance.
    """
    from .scene import _surface_recipe_snapshot
    from .surface import MAX_MESH_VERTICES

    snapshot = _surface_recipe_snapshot(recipe, work=work)
    if snapshot is None:
        return materialize_surface(recipe, max_vertices=max_vertices, check=check)
    if type(max_vertices) is not int or not 0 <= max_vertices <= MAX_MESH_VERTICES:
        raise SurfaceError("OKL-E-RESOURCE", "Invalid remaining vertex budget.",
                           details={"budget": max_vertices})
    recipe_key, frozen = snapshot
    key = ("reach_constructed_surface", recipe_key)
    cached = work.lookup(key)
    if cached is None:
        mesh, placement = materialize_surface(frozen, max_vertices=max_vertices, check=check)
        cached = mesh, placement.position, placement.rotation
        work.remember(key, cached)
    mesh, position, rotation = cached
    if len(mesh.positions) > max_vertices:
        raise SurfaceError("OKL-E-RESOURCE", "Surface exceeds the remaining mesh vertex budget.",
                           details={"required": len(mesh.positions), "available": max_vertices})
    return mesh, Pose("self", position, rotation)


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
        if self.model.profile in IMPULSE_PROFILES:
            self.budget.profile = self.model.profile
        self.reach_work = None
        self._reach_descriptions = {}
        if self.model.profile in REACH_PROFILES:
            from .reach_numeric import ReachExecutionWork
            self.reach_work = (ReachExecutionWork(execution_budget=budget.execution_budget)
                if self.model.profile in EXECUTION_PROFILES else ReachExecutionWork(
                    check=budget.tick, max_operations=budget.limits["max_operations"],
                    max_elapsed_ms=budget.limits["max_elapsed_ms"]))
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
        self._keyed_transforms: dict[int, tuple[KeyedTransformOrigin, ...]] = {}
        self._value_transforms: dict[int, tuple[Value, tuple[KeyedTransformOrigin, ...]]] = {}
        self._value_reductions: dict[int, tuple[Value, tuple[KeyedReductionOrigin, ...]]] = {}
        self._value_filters: dict[int, tuple[Value, tuple[KeyedFilterOrigin, ...]]] = {}
        self._value_merges: dict[int, tuple[Value, tuple[KeyedMergeOrigin, ...]]] = {}
        self._value_zips: dict[int, tuple[Value, tuple[KeyedZipOrigin, ...]]] = {}
        self._value_rekeys: dict[int, tuple[Value, tuple[KeyedRekeyOrigin, ...]]] = {}
        self._expression_flows: list[dict] = []
        self._shape_stack: list[str] = []
        self._value_taints: dict[int, set[str]] = {}
        self._tainted_values: dict[int, Value] = {}
        self._lexical_self_origins: dict[int, tuple[Value, str]] = {}
        self._expression_depth = 0
        # A syntax classification, like the resolved-type index, not a value
        # cache. Values share the request's existing 256-entry bounded LRU.
        self._constant_syntax: dict[int, tuple[frozenset[str] | None, int]] = {}
        self._parameter_syntax: dict[int, tuple[Any, tuple | None]] = {}
        self._parameter_capture = None
        # Bounded source-only routes. No occurrence values or computed poses
        # live here; those retain their existing owners and numeric LRU.
        self._assignment_syntax: dict[int, tuple] = {}
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
        return self._member_definition_id(declared)

    def _member_definition_id(self, declared: Member) -> tuple[str, ...]:
        # Member access and tree expansion already resolved this exact member.
        # Re-entering effective() would repeat a class lookup for every field
        # read and every generated occurrence without adding binding evidence.
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
            if node.name in self.predefined(node) or node.name in names:
                fail("OKL-E-NAME", f"Name '{node.name}' is predefined or duplicated in this scope.", node, phase="binding")
            if node.key in keys:
                fail("OKL-E-ID", f"Stable key '{node.key}' is reused in this scope.", node, phase="binding")
            names.add(node.name)
            keys.add(node.key)

    def predefined(self, node: Any) -> frozenset | set:
        if self.linked.modules[node.source_id].ast.profile in TEXTURE_PROFILES:
            from .reach_source import NAMES
            result = PREDEFINED_02 | NAMES | TEXTURE_CALLS | TEXTURE_TYPES
            if self.linked.modules[node.source_id].ast.profile in KEYED_TRANSFORM_PROFILES:
                result = result | {"map_keyed"}
            if self.linked.modules[node.source_id].ast.profile in KEYED_REDUCTION_PROFILES:
                result = result | {"reduce_keyed"}
            if self.linked.modules[node.source_id].ast.profile in KEYED_FILTER_PROFILES:
                result = result | {"filter_keyed"}
            if self.linked.modules[node.source_id].ast.profile in KEYED_MERGE_PROFILES:
                result = result | {"merge_keyed"}
            if self.linked.modules[node.source_id].ast.profile in KEYED_ZIP_PROFILES:
                result = result | {"zip_keyed"}
            if self.linked.modules[node.source_id].ast.profile in KEYED_REKEY_PROFILES:
                result = result | {"rekey_keyed"}
            return result
        if self.linked.modules[node.source_id].ast.profile in REACH_PROFILES:
            from .reach_source import NAMES
            return PREDEFINED_02 | NAMES
        return PREDEFINED_02

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
            elif name == "ReachBranch" and self.linked.modules[node.source_id].ast.profile in REACH_PROFILES:
                if args:
                    from .reach_source import reach_error
                    raise reach_error("reach_type", "ReachBranch takes no type arguments.", node)
                result = Type("ReachBranch")
            elif name in TEXTURE_TYPES and self.linked.modules[node.source_id].ast.profile in TEXTURE_PROFILES:
                if args:
                    fail("OKL-E-TYPE", f"Texture type '{name}' takes no type arguments.", node, phase="type")
                result = Type(name)
            elif name in POCKETS_TYPES and self.linked.modules[node.source_id].ast.profile in POCKETS_PROFILES:
                if args:
                    fail("OKL-E-TYPE", f"Pocket type '{name}' takes no type arguments.", node, phase="type")
                result = Type(name)
            elif name in FRAMED_LOFT_TYPES and self.linked.modules[node.source_id].ast.profile in FRAMED_LOFT_PROFILES:
                if args:
                    fail("OKL-E-TYPE", f"Framed section type '{name}' takes no type arguments.", node, phase="type")
                result = Type(name)
            elif name in RING_LOFT_TYPES and self.linked.modules[node.source_id].ast.profile in RING_LOFT_PROFILES:
                if args:
                    fail("OKL-E-TYPE", f"Polygon section type '{name}' takes no type arguments.", node, phase="type")
                result = Type(name)
            elif name in HOLES_TYPES and self.linked.modules[node.source_id].ast.profile in HOLES_PROFILES:
                if args:
                    fail("OKL-E-TYPE", f"Ring type '{name}' takes no type arguments.", node, phase="type")
                result = Type(name)
            elif name in EXTRUSION_TYPES and self.linked.modules[node.source_id].ast.profile in EXTRUSION_PROFILES:
                if args:
                    fail("OKL-E-TYPE", f"Extrusion type '{name}' takes no type arguments.", node, phase="type")
                result = Type(name)
            elif name in SURFACE_TYPES and self.linked.modules[node.source_id].ast.profile in SURFACE_PROFILES:
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
        declaring_profile = self.linked.modules[node.source_id].ast.profile
        if declaring_profile in SURFACE_PROFILES:
            allowed |= SURFACE_TYPES
        if declaring_profile in TEXTURE_PROFILES:
            allowed |= TEXTURE_TYPES
        if declaring_profile in POCKETS_PROFILES:
            allowed |= POCKETS_TYPES
        if declaring_profile in FRAMED_LOFT_PROFILES:
            allowed |= FRAMED_LOFT_TYPES
        if declaring_profile in RING_LOFT_PROFILES:
            allowed |= RING_LOFT_TYPES
        if declaring_profile in HOLES_PROFILES:
            allowed |= HOLES_TYPES
        if declaring_profile in EXTRUSION_PROFILES:
            allowed |= EXTRUSION_TYPES
        if element.kind not in allowed:
            fail("OKL-E-CAPABILITY-UNSUPPORTED", f"Authored Keyed<{element}> is outside the flat immutable leaf profile.",
                 node, phase="support", details={"profile": IMPULSE_PROFILE if declaring_profile == IMPULSE_PROFILE else PROFILE,
                                                 "element_type": str(element)})

    def signature(self, node: Any) -> tuple:
        self.budget.tick(node)
        names, params = set(), []
        for param in node.params:
            if param.name in self.predefined(param) or param.name in names:
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
        transforms = self._transform_records(original)
        if transforms:
            self._value_transforms[id(result)] = (result, transforms)
        reductions = self._reduction_records(original)
        if reductions:
            self._value_reductions[id(result)] = (result, reductions)
        filters = self._filter_records(original)
        if filters:
            self._value_filters[id(result)] = (result, filters)
        merges = self._merge_records(original)
        if merges:
            self._value_merges[id(result)] = (result, merges)
        zips = self._zip_records(original)
        if zips:
            self._value_zips[id(result)] = (result, zips)
        rekeys = self._rekey_records(original)
        if rekeys:
            self._value_rekeys[id(result)] = (result, rekeys)
        return result

    def _rekey_records(self, value: Value) -> tuple[KeyedRekeyOrigin, ...]:
        retained = self._value_rekeys.get(id(value))
        if retained is not None and retained[0] is value:
            return retained[1]
        return ()

    def _combine_rekey_records(self, *groups) -> tuple[KeyedRekeyOrigin, ...]:
        records, seen = [], set()

        def coordinates(node):
            return None if node is None else (node.source_id, node.start, node.end)

        for group in groups:
            for record in group:
                self.budget.tick(record.expression)
                identity = (coordinates(record.expression), coordinates(record.input),
                            coordinates(record.body), record.element_type,
                            record.old_key, record.new_key, coordinates(record.input_entry))
                if identity not in seen:
                    records.append(record)
                    seen.add(identity)
        return tuple(records)

    def _aggregate_rekey_records(self, *groups) -> tuple[KeyedRekeyOrigin, ...]:
        normalized = []
        for group in groups:
            for record in group:
                self.budget.tick(record.expression)
                normalized.append(replace(record, old_key=None, new_key=None, input_entry=None))
        return self._combine_rekey_records(normalized)

    def rekey_provenance(self, value: Value, *, aggregate: Value | None = None) -> list[dict]:
        records = (self._rekey_records(value) if aggregate is None else
                   self._combine_rekey_records(self._rekey_records(aggregate), self._rekey_records(value)))
        result = []
        for origin in records:
            self.budget.tick(origin.expression)
            result.append({"expression": self.location(origin.expression),
                           "input": self.location(origin.input),
                           "body": self.location(origin.body),
                           "element_type": str(origin.element_type),
                           "old_key": origin.old_key, "new_key": origin.new_key,
                           "input_entry": self.location(origin.input_entry)})
        return result

    def _zip_records(self, value: Value) -> tuple[KeyedZipOrigin, ...]:
        retained = self._value_zips.get(id(value))
        if retained is not None and retained[0] is value:
            return retained[1]
        return ()

    def _combine_zip_records(self, *groups) -> tuple[KeyedZipOrigin, ...]:
        """Deduplicate the complete detached meaning, preserving read order."""
        records, seen = [], set()

        def coordinates(node):
            return None if node is None else (node.source_id, node.start, node.end)

        for group in groups:
            for record in group:
                self.budget.tick(record.expression)
                identity = (coordinates(record.expression), coordinates(record.left),
                            coordinates(record.right), coordinates(record.body),
                            record.left_type, record.right_type, record.output_type,
                            record.key, coordinates(record.left_entry), coordinates(record.right_entry))
                if identity not in seen:
                    records.append(record)
                    seen.add(identity)
        return tuple(records)

    def _aggregate_zip_records(self, *groups) -> tuple[KeyedZipOrigin, ...]:
        normalized = []
        for group in groups:
            for record in group:
                self.budget.tick(record.expression)
                normalized.append(replace(record, key=None, left_entry=None, right_entry=None))
        return self._combine_zip_records(normalized)

    def zip_provenance(self, value: Value, *, aggregate: Value | None = None) -> list[dict]:
        records = (self._zip_records(value) if aggregate is None else
                   self._combine_zip_records(self._zip_records(aggregate), self._zip_records(value)))
        result = []
        for origin in records:
            self.budget.tick(origin.expression)
            result.append({"expression": self.location(origin.expression),
                           "left": self.location(origin.left),
                           "right": self.location(origin.right),
                           "body": self.location(origin.body),
                           "left_element_type": str(origin.left_type),
                           "right_element_type": str(origin.right_type),
                           "output_element_type": str(origin.output_type),
                           "key": origin.key,
                           "left_entry": self.location(origin.left_entry),
                           "right_entry": self.location(origin.right_entry)})
        return result

    def _merge_records(self, value: Value) -> tuple[KeyedMergeOrigin, ...]:
        retained = self._value_merges.get(id(value))
        if retained is not None and retained[0] is value:
            return retained[1]
        return ()

    def merge_provenance(self, value: Value) -> list[dict]:
        result = []
        for origin in self._merge_records(value):
            self.budget.tick(origin.expression)
            result.append({"expression": self.location(origin.expression),
                           "left": self.location(origin.left),
                           "right": self.location(origin.right),
                           "element_type": str(origin.element_type),
                           "input_side": origin.input_side})
        return result

    def _combine_merge_records(self, *groups) -> tuple[KeyedMergeOrigin, ...]:
        records, seen = [], set()
        for group in groups:
            for record in group:
                self.budget.tick(record.expression)
                identity = (id(record.expression), id(record.left), id(record.right),
                            record.element_type, record.input_side)
                if identity not in seen:
                    records.append(record)
                    seen.add(identity)
        return tuple(records)

    def _filter_records(self, value: Value) -> tuple[KeyedFilterOrigin, ...]:
        retained = self._value_filters.get(id(value))
        if retained is not None and retained[0] is value:
            return retained[1]
        return ()

    def filter_provenance(self, value: Value) -> list[dict]:
        result = []
        for origin in self._filter_records(value):
            self.budget.tick(origin.expression)
            result.append({"expression": self.location(origin.expression),
                           "input": self.location(origin.input),
                           "predicate": self.location(origin.predicate),
                           "element_type": str(origin.element_type)})
        return result

    def _merge_filter_records(self, *groups) -> tuple[KeyedFilterOrigin, ...]:
        records, seen = [], set()
        for group in groups:
            for record in group:
                self.budget.tick(record.expression)
                identity = (id(record.expression), id(record.input),
                            id(record.predicate), record.element_type)
                if identity not in seen:
                    records.append(record)
                    seen.add(identity)
        return tuple(records)

    def _reduction_records(self, value: Value) -> tuple[KeyedReductionOrigin, ...]:
        retained = self._value_reductions.get(id(value))
        if retained is not None and retained[0] is value:
            return retained[1]
        return ()

    def reduction_provenance(self, value: Value) -> list[dict]:
        result = []
        for origin in self._reduction_records(value):
            self.budget.tick(origin.expression)
            result.append({"expression": self.location(origin.expression),
                           "input": self.location(origin.input),
                           "seed": self.location(origin.seed),
                           "body": self.location(origin.body),
                           "input_element_type": str(origin.input_type),
                           "accumulator_type": str(origin.accumulator_type)})
        return result

    def _merge_reduction_records(self, *groups) -> tuple[KeyedReductionOrigin, ...]:
        records, seen = [], set()
        for group in groups:
            for record in group:
                self.budget.tick(record.expression)
                identity = (id(record.expression), id(record.input), id(record.seed),
                            id(record.body), record.input_type, record.accumulator_type)
                if identity not in seen:
                    records.append(record)
                    seen.add(identity)
        return tuple(records)

    def _transform_records(self, value: Value) -> tuple[KeyedTransformOrigin, ...]:
        retained = self._value_transforms.get(id(value))
        if retained is not None and retained[0] is value:
            return retained[1]
        if (value.type.kind == "Keyed" and value.known
                and self._keyed_payloads.get(id(value.value)) is value.value):
            return self._keyed_transforms.get(id(value.value), ())
        return ()

    def transform_provenance(self, value: Value) -> list[dict]:
        """Return detached source locations for an actual transformed value."""
        result = []
        for origin in self._transform_records(value):
            self.budget.tick(origin.expression)
            record = {"expression": self.location(origin.expression),
                      "body": self.location(origin.body),
                      "input": self.location(origin.input),
                      "input_element_type": str(origin.input_type),
                      "output_element_type": str(origin.output_type)}
            if origin.key is not None:
                record.update(key=origin.key, input_entry=self.location(origin.input_entry))
            result.append(record)
        return result

    def _merge_transform_records(self, *groups) -> tuple[KeyedTransformOrigin, ...]:
        # Repeated references describe the same source derivation once
        # Keep selected inner keys distinct from the current outer key
        records, seen = [], set()
        for group in groups:
            for record in group:
                self.budget.tick(record.expression)
                identity = (id(record.expression), id(record.body), id(record.input),
                            record.input_type, record.output_type,
                            record.key, id(record.input_entry))
                if identity not in seen:
                    records.append(record)
                    seen.add(identity)
        return tuple(records)

    def _selected_transform_records(self, *groups) -> tuple[KeyedTransformOrigin, ...]:
        """Retain aggregate reads without inventing an unrelated map key."""
        records = self._merge_transform_records(*groups)
        selected = {(id(record.expression), id(record.body), id(record.input))
                    for record in records if record.key is not None}
        return tuple(record for record in records if record.key is not None
                     or (id(record.expression), id(record.body), id(record.input)) not in selected)

    def _observe_value_flow(self, value: Value, frame=None) -> None:
        if frame is None:
            if not self._expression_flows:
                return
            frame = self._expression_flows[-1]
        transforms = self._transform_records(value)
        if transforms:
            frame["transforms"].append(transforms)
        reductions = self._reduction_records(value)
        if reductions:
            frame["reductions"].append(reductions)
        filters = self._filter_records(value)
        if filters:
            frame["filters"].append(filters)
        merges = self._merge_records(value)
        if merges:
            frame["merges"].append(merges)
        zips = self._zip_records(value)
        if zips:
            frame["zips"].append(zips)
        rekeys = self._rekey_records(value)
        if rekeys:
            frame["rekeys"].append(rekeys)
        frame["taints"].update(self._value_taints.get(id(value), ()))

    def _finish_value_flow(self, value: Value, node: Any, tracking: bool) -> Value:
        if not tracking:
            return value
        frame = self._expression_flows[-1]
        own = self._transform_records(value)
        # A map builds its aggregate derivation explicitly. Ordinary pure
        # expressions retain only the values their selected execution reads.
        transforms = (own if node.kind in {"map_keyed", "reduce_keyed", "filter_keyed", "merge_keyed", "zip_keyed", "rekey_keyed"} else
                      self._merge_transform_records(*frame["transforms"], own))
        if value.type.kind == "Keyed":
            if any(record.key is not None for record in transforms):
                transforms = self._merge_transform_records(tuple(
                    replace(record, key=None, input_entry=None) for record in transforms))
        else:
            # An actual indexed leaf refines its aggregate source record.
            # Passing that collection through a helper must not add a second
            # keyless copy of the same derivation to the returned leaf.
            selected = {(id(record.expression), id(record.body), id(record.input))
                        for record in transforms if record.key is not None}
            transforms = tuple(record for record in transforms if record.key is not None
                               or (id(record.expression), id(record.body), id(record.input)) not in selected)
        own_reductions = self._reduction_records(value)
        reductions = (own_reductions if node.kind in {"reduce_keyed", "filter_keyed", "merge_keyed", "zip_keyed", "rekey_keyed"} else
                      self._merge_reduction_records(*frame["reductions"], own_reductions))
        own_filters = self._filter_records(value)
        filters = (own_filters if node.kind in {"filter_keyed", "merge_keyed", "zip_keyed", "rekey_keyed"} else
                   self._merge_filter_records(*frame["filters"], own_filters))
        own_merges = self._merge_records(value)
        merges = (own_merges if node.kind in {"merge_keyed", "zip_keyed", "rekey_keyed"} else
                  self._combine_merge_records(*frame["merges"], own_merges))
        own_zips = self._zip_records(value)
        zips = (own_zips if node.kind in {"zip_keyed", "rekey_keyed"} else
                self._combine_zip_records(*frame["zips"], own_zips))
        if value.type.kind == "Keyed" and zips:
            zips = self._aggregate_zip_records(zips)
        own_rekeys = self._rekey_records(value)
        rekeys = (own_rekeys if node.kind == "rekey_keyed" else
                  self._combine_rekey_records(*frame["rekeys"], own_rekeys))
        if value.type.kind == "Keyed" and rekeys:
            rekeys = self._aggregate_rekey_records(rekeys)
        taints = frame["taints"] | self._value_taints.get(id(value), set())
        if (transforms != own or reductions != own_reductions or filters != own_filters
                or merges != own_merges or zips != own_zips or rekeys != own_rekeys
                or taints != self._value_taints.get(id(value), set())):
            value = self._inherit_value_info(value, Value(value.type, value.value, value.frame, value.hint))
            self.budget.charge_value(value, node)
            if transforms:
                self._value_transforms[id(value)] = (value, transforms)
            if reductions:
                self._value_reductions[id(value)] = (value, reductions)
            if filters:
                self._value_filters[id(value)] = (value, filters)
            if merges:
                self._value_merges[id(value)] = (value, merges)
            if zips:
                self._value_zips[id(value)] = (value, zips)
            if rekeys:
                self._value_rekeys[id(value)] = (value, rekeys)
            if taints:
                self._value_taints[id(value)] = set(taints)
                self._tainted_values[id(value)] = value
        if len(self._expression_flows) > 1:
            self._observe_value_flow(value, self._expression_flows[-2])
        return value

    def _unknown_local_context(self, ctx: Context, node: Any) -> Context:
        locals_ = {}
        for name, value in ctx.locals.items():
            self.budget.tick(node)
            locals_[name] = Value(value.type, frame=value.frame, hint=value.hint)
        return replace(ctx, locals=locals_, abstract=True)

    def _map_binders(self, node: Any, ctx: Context) -> None:
        module = self.linked.modules[node.source_id]
        forbidden = self.predefined(node) | set(ctx.locals) | set(module.imports) | set(module.symbols)
        # Older declaration scopes retain their historical name rules. This
        # new lexical binder cannot hide any builtin inherited by .14.
        forbidden |= (SURFACE_CALLS | SURFACE_TYPES | EXTRUSION_CALLS | EXTRUSION_TYPES
                      | HOLES_CALLS | HOLES_TYPES | RING_LOFT_CALLS | RING_LOFT_TYPES
                      | FRAMED_LOFT_CALLS | FRAMED_LOFT_TYPES | POCKETS_CALLS | POCKETS_TYPES)
        if ctx.self_type is not None:
            forbidden |= set(self.effective(ctx.self_type).members) | set(FIELD_TYPES) | READONLY_FIELDS
        if ctx.scene:
            forbidden |= set(self.scene_names)
        binders = ([(node.key_name, node.key_node), (node.left_name, node.left_node),
                    (node.right_name, node.right_node)] if node.kind == "zip_keyed" else
                   [(node.key_name, node.key_node), (node.value_name, node.value_node)])
        if node.kind == "reduce_keyed":
            binders.insert(0, (node.accumulator_name, node.accumulator_node))
        for name, binder in binders:
            self.budget.tick(binder)
            if name in forbidden:
                label = {"reduce_keyed": "Reduction", "filter_keyed": "Filter",
                         "zip_keyed": "Zip", "rekey_keyed": "Rekey"}.get(node.kind, "Map")
                fail("OKL-E-NAME", f"{label} binder '{name}' duplicates or shadows a visible name.",
                     binder, phase="binding")
            forbidden.add(name)

    def _expect_map_output(self, value: Value, output_type: Type, node: Any) -> Value:
        actual, expected = value.type, output_type
        while actual.kind == expected.kind and actual.kind in {"Vec3", "Vector3", "Range"}:
            actual, expected = actual.element, expected.element
        numeric = {"Int", "Real", "Quantity"}
        if (actual != expected and (actual.kind == "Quantity" or expected.kind == "Quantity")
                and not (actual.kind in numeric and expected.kind in numeric)):
            fail("OKL-E-TYPE", f"Expected {output_type}, received {value.type}.", node,
                 phase="type", details={"expected": str(output_type), "actual": str(value.type)})
        return self.expect(value, output_type, node)

    def _map_keyed_expression(self, node: Any, ctx: Context) -> Value:
        if self.linked.modules[node.source_id].ast.profile not in KEYED_TRANSFORM_PROFILES:
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "map_keyed requires keyed-transform-0.1.",
                 node, phase="support")
        output_type = self.parse_type(node.element_type)
        self._keyed_leaf(output_type, node.element_type)
        self._map_binders(node, ctx)
        source = self.expression(node.input, ctx)
        if source.type.kind != "Keyed":
            fail("OKL-E-TYPE", "map_keyed input must be a flat Keyed value.", node.input, phase="type")
        input_type = source.type.element
        self._keyed_leaf(input_type, node.input)
        result_type = Type("Keyed", element=output_type)
        abstract = self._unknown_local_context(ctx, node.body)
        abstract.locals[node.key_name] = Value(STRING)
        abstract.locals[node.value_name] = Value(input_type)
        self._expect_map_output(self.expression(node.body, abstract), output_type, node.body)
        if ctx.abstract:
            return Value(result_type)
        if not source.known or not isinstance(source.value, KeyedValue):
            fail("OKL-E-TYPE", "map_keyed input must resolve to an immutable keyed value.", node.input, phase="type")
        if len(source.value.entries) > MAX_KEYED_ENTRIES:
            fail("OKL-E-RESOURCE", "Map input exceeds 256 entries.", node.input, phase="support",
                 details={"budget": "keyed_entries", "limit": MAX_KEYED_ENTRIES,
                          "consumed": len(source.value.entries)})
        taints = set(self._value_taints.get(id(source), ()))
        for path in taints:
            self._mark_generated(path, node.input)
        # Copy the enclosing scope once. Replacing these two immutable values
        # cannot make a previous iteration or a surrounding scope writable.
        locals_ = {}
        for name, value in ctx.locals.items():
            self.budget.tick(node)
            locals_[name] = value
        body_ctx = replace(ctx, locals=locals_)
        origins = self._keyed_origins.get(id(source.value), {})
        input_transforms = self._transform_records(source)
        current = KeyedTransformOrigin(node, node.body, node.input, input_type, output_type)
        aggregate_groups, entries = [input_transforms], []
        prior_key = None
        for key, leaf in source.value.entries:
            ledger = getattr(self.budget, "execution_budget", None)
            previous_stage = ledger.stage if ledger is not None else None
            try:
                if ledger is not None:
                    ledger.stage = "keyed_transform_iteration"
                self.budget.tick(node)
            finally:
                if ledger is not None:
                    ledger.stage = previous_stage
            self.key(node.input, key)
            if prior_key is not None and key <= prior_key:
                fail("OKL-E-ID", "Map input keys must be unique canonical stable keys.", node.input, phase="binding")
            prior_key = key
            bound_key = Value(STRING, key)
            bound_value = self._inherit_value_info(leaf, Value(leaf.type, leaf.value, leaf.frame, leaf.hint))
            self.budget.charge_value(bound_key, node.key_node)
            self.budget.charge_value(bound_value, node.value_node)
            locals_[node.key_name], locals_[node.value_name] = bound_key, bound_value
            computed = self._expect_map_output(self.expression(node.body, body_ctx), output_type, node.body)
            result = self._inherit_value_info(computed, Value(computed.type, computed.value, computed.frame, computed.hint))
            self.budget.charge_value(result, node.body)
            source_records = (input_transforms if self.model.profile in KEYED_MERGE_PROFILES else
                              tuple(replace(record, key=key, input_entry=origins.get(key))
                                    if record.key is None else record for record in input_transforms))
            body_records = self._transform_records(computed)
            merge_transforms = (self._selected_transform_records
                                if self.model.profile in KEYED_MERGE_PROFILES else self._merge_transform_records)
            records = merge_transforms(source_records, self._transform_records(leaf),
                        body_records, (replace(current, key=key, input_entry=origins.get(key)),))
            self._value_transforms[id(result)] = (result, records)
            reductions = self._merge_reduction_records(self._reduction_records(source),
                self._reduction_records(leaf), self._reduction_records(computed))
            if reductions:
                self._value_reductions[id(result)] = (result, reductions)
            filters = self._merge_filter_records(self._filter_records(source),
                self._filter_records(leaf), self._filter_records(computed))
            if filters:
                self._value_filters[id(result)] = (result, filters)
            merges = self._combine_merge_records(self._merge_records(source),
                self._merge_records(leaf), self._merge_records(computed))
            if merges:
                self._value_merges[id(result)] = (result, merges)
            zips = self._combine_zip_records(self._zip_records(source),
                self._zip_records(leaf), self._zip_records(computed))
            if zips:
                self._value_zips[id(result)] = (result, zips)
            rekeys = self._combine_rekey_records(self._rekey_records(source),
                self._rekey_records(leaf), self._rekey_records(computed))
            if rekeys:
                self._value_rekeys[id(result)] = (result, rekeys)
            leaf_taints = taints | self._value_taints.get(id(leaf), set()) | self._value_taints.get(id(computed), set())
            if leaf_taints:
                self._value_taints[id(result)] = set(leaf_taints)
                self._tainted_values[id(result)] = result
                taints.update(leaf_taints)
            # Aggregate derivation describes the source expressions; selected
            # output leaves retain their actual nested keys separately.
            aggregate_groups.append(tuple(replace(record, key=None, input_entry=None) for record in body_records))
            entries.append((key, result))
        payload = KeyedValue(tuple(entries))
        value = Value(result_type, payload)
        self.budget.charge_value(value, node)
        transforms = self._merge_transform_records(*aggregate_groups, (current,))
        self._keyed_payloads[id(payload)] = payload
        self._keyed_origins[id(payload)] = dict(origins)
        self._keyed_transforms[id(payload)] = transforms
        self._value_transforms[id(value)] = (value, transforms)
        if taints:
            self._value_taints[id(value)] = taints
            self._tainted_values[id(value)] = value
        return value

    def _reduce_keyed_expression(self, node: Any, ctx: Context) -> Value:
        if self.linked.modules[node.source_id].ast.profile not in KEYED_REDUCTION_PROFILES:
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "reduce_keyed requires keyed-reduction-0.1.",
                 node, phase="support")
        accumulator_type = self.parse_type(node.accumulator_type)
        self._keyed_leaf(accumulator_type, node.accumulator_type)
        self._map_binders(node, ctx)
        source = self.expression(node.input, ctx)
        if source.type.kind != "Keyed":
            fail("OKL-E-TYPE", "reduce_keyed input must be a flat Keyed value.", node.input, phase="type")
        input_type = source.type.element
        self._keyed_leaf(input_type, node.input)
        # Admit the actual input before evaluating the seed. A later seed
        # domain failure must not mask the first input failure.
        if not ctx.abstract:
            if not source.known or not isinstance(source.value, KeyedValue):
                fail("OKL-E-TYPE", "reduce_keyed input must resolve to an immutable keyed value.",
                     node.input, phase="type")
            if len(source.value.entries) > MAX_KEYED_ENTRIES:
                fail("OKL-E-RESOURCE", "Reduction input exceeds 256 entries.", node.input, phase="support",
                     details={"budget": "keyed_entries", "limit": MAX_KEYED_ENTRIES,
                              "consumed": len(source.value.entries)})
        seed = self._expect_map_output(self.expression(node.seed, ctx), accumulator_type, node.seed)
        abstract = self._unknown_local_context(ctx, node.body)
        abstract.locals[node.accumulator_name] = Value(accumulator_type, frame=seed.frame, hint=seed.hint)
        abstract.locals[node.key_name] = Value(STRING)
        abstract.locals[node.value_name] = Value(input_type)
        self._expect_map_output(self.expression(node.body, abstract), accumulator_type, node.body)
        if ctx.abstract:
            return Value(accumulator_type, frame=seed.frame, hint=seed.hint)

        def copied(value, origin):
            result = self._inherit_value_info(value, Value(value.type, value.value, value.frame, value.hint))
            self.budget.charge_value(result, origin)
            return result

        accumulator = copied(seed, node.seed)
        transforms = [self._transform_records(source), self._transform_records(seed)]
        reductions = [self._reduction_records(source), self._reduction_records(seed)]
        filters = [self._filter_records(source), self._filter_records(seed)]
        zips = [self._zip_records(source), self._zip_records(seed)]
        rekeys = [self._rekey_records(source), self._rekey_records(seed)]
        taints = set(self._value_taints.get(id(source), ())) | set(self._value_taints.get(id(seed), ()))
        locals_ = {}
        for name, value in ctx.locals.items():
            self.budget.tick(node)
            locals_[name] = value
        body_ctx = replace(ctx, locals=locals_)
        prior_key = None
        for key, leaf in source.value.entries:
            ledger = getattr(self.budget, "execution_budget", None)
            previous_stage = ledger.stage if ledger is not None else None
            try:
                if ledger is not None:
                    ledger.stage = "keyed_reduction_iteration"
                self.budget.tick(node)
            finally:
                if ledger is not None:
                    ledger.stage = previous_stage
            self.key(node.input, key)
            if prior_key is not None and key <= prior_key:
                fail("OKL-E-ID", "Reduction input keys must be unique canonical stable keys.",
                     node.input, phase="binding")
            prior_key = key
            bound_key = Value(STRING, key)
            self.budget.charge_value(bound_key, node.key_node)
            bound_value = copied(leaf, node.value_node)
            bound_accumulator = copied(accumulator, node.accumulator_node)
            locals_[node.key_name] = bound_key
            locals_[node.value_name] = bound_value
            locals_[node.accumulator_name] = bound_accumulator
            computed = self._expect_map_output(self.expression(node.body, body_ctx), accumulator_type, node.body)
            accumulator = copied(computed, node.body)
            transforms.extend((self._transform_records(leaf), self._transform_records(computed)))
            reductions.extend((self._reduction_records(leaf), self._reduction_records(computed)))
            filters.extend((self._filter_records(leaf), self._filter_records(computed)))
            zips.extend((self._zip_records(leaf), self._zip_records(computed)))
            rekeys.extend((self._rekey_records(leaf), self._rekey_records(computed)))
            taints.update(self._value_taints.get(id(leaf), ()))
            taints.update(self._value_taints.get(id(computed), ()))
            # Earlier reads remain part of the aggregate even when this body
            # selected a constant and did not read its accumulator binding.
            retained_transforms = self._merge_transform_records(*transforms)
            retained_reductions = self._merge_reduction_records(*reductions)
            if retained_transforms:
                self._value_transforms[id(accumulator)] = (accumulator, retained_transforms)
            if retained_reductions:
                self._value_reductions[id(accumulator)] = (accumulator, retained_reductions)
            retained_filters = self._merge_filter_records(*filters)
            if retained_filters:
                self._value_filters[id(accumulator)] = (accumulator, retained_filters)
            retained_zips = self._combine_zip_records(*zips)
            if retained_zips:
                self._value_zips[id(accumulator)] = (accumulator, retained_zips)
            retained_rekeys = self._combine_rekey_records(*rekeys)
            if retained_rekeys:
                self._value_rekeys[id(accumulator)] = (accumulator, retained_rekeys)
            if taints:
                self._value_taints[id(accumulator)] = set(taints)
                self._tainted_values[id(accumulator)] = accumulator
        result = copied(accumulator, node)
        retained_transforms = self._merge_transform_records(*transforms)
        current = KeyedReductionOrigin(node, node.input, node.seed, node.body, input_type, accumulator_type)
        retained_reductions = self._merge_reduction_records(*reductions, (current,))
        if retained_transforms:
            self._value_transforms[id(result)] = (result, retained_transforms)
        self._value_reductions[id(result)] = (result, retained_reductions)
        retained_filters = self._merge_filter_records(*filters)
        if retained_filters:
            self._value_filters[id(result)] = (result, retained_filters)
        retained_zips = self._combine_zip_records(*zips)
        if retained_zips:
            self._value_zips[id(result)] = (result, retained_zips)
        retained_rekeys = self._combine_rekey_records(*rekeys)
        if retained_rekeys:
            self._value_rekeys[id(result)] = (result, retained_rekeys)
        if taints:
            self._value_taints[id(result)] = set(taints)
            self._tainted_values[id(result)] = result
            for path in taints:
                self._mark_generated(path, node)
        return result

    def _filter_keyed_expression(self, node: Any, ctx: Context) -> Value:
        if self.linked.modules[node.source_id].ast.profile not in KEYED_FILTER_PROFILES:
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "filter_keyed requires keyed-filter-0.1.",
                 node, phase="support")
        element_type = self.parse_type(node.element_type)
        self._keyed_leaf(element_type, node.element_type)
        self._map_binders(node, ctx)
        source = self.expression(node.input, ctx)
        result_type = Type("Keyed", element=element_type)
        if source.type != result_type:
            fail("OKL-E-TYPE", f"filter_keyed requires exactly {result_type}, received {source.type}.",
                 node.input, phase="type", details={"expected": str(result_type), "actual": str(source.type)})
        self._keyed_leaf(source.type.element, node.input)
        if not ctx.abstract:
            if not source.known or not isinstance(source.value, KeyedValue):
                fail("OKL-E-TYPE", "filter_keyed input must resolve to an immutable keyed value.",
                     node.input, phase="type")
            if len(source.value.entries) > MAX_KEYED_ENTRIES:
                fail("OKL-E-RESOURCE", "Filter input exceeds 256 entries.", node.input, phase="support",
                     details={"budget": "keyed_entries", "limit": MAX_KEYED_ENTRIES,
                              "consumed": len(source.value.entries)})
        abstract = self._unknown_local_context(ctx, node.predicate)
        abstract.locals[node.key_name] = Value(STRING)
        abstract.locals[node.value_name] = Value(element_type)
        def strict_predicate(value):
            if value.type != BOOL:
                fail("OKL-E-TYPE", f"Filter predicate requires Bool, received {value.type}.",
                     node.predicate, phase="type", details={"expected": "Bool", "actual": str(value.type)})
            return value

        strict_predicate(self.expression(node.predicate, abstract))
        if ctx.abstract:
            return Value(result_type)

        def copied(value, origin):
            self.budget.tick(origin)
            result = self._inherit_value_info(value, Value(value.type, value.value, value.frame, value.hint))
            self.budget.charge_value(result, origin)
            return result

        input_transforms = self._transform_records(source)
        input_reductions = self._reduction_records(source)
        input_filters = self._filter_records(source)
        transforms, reductions, filters = [input_transforms], [input_reductions], [input_filters]
        taints = set(self._value_taints.get(id(source), ()))
        origins = self._keyed_origins.get(id(source.value), {})
        current = KeyedFilterOrigin(node, node.input, node.predicate, element_type)
        locals_ = {}
        for name, value in ctx.locals.items():
            self.budget.tick(node)
            locals_[name] = value
        predicate_ctx = replace(ctx, locals=locals_)
        prior_key, entries = None, []
        for key, leaf in source.value.entries:
            ledger = getattr(self.budget, "execution_budget", None)
            previous_stage = ledger.stage if ledger is not None else None
            try:
                if ledger is not None:
                    ledger.stage = "keyed_filter_iteration"
                self.budget.tick(node)
            finally:
                if ledger is not None:
                    ledger.stage = previous_stage
            self.key(node.input, key)
            if prior_key is not None and key <= prior_key:
                fail("OKL-E-ID", "Filter input keys must be unique canonical stable keys.",
                     node.input, phase="binding")
            prior_key = key
            bound_key = Value(STRING, key)
            self.budget.charge_value(bound_key, node.key_node)
            bound_value = copied(leaf, node.value_node)
            locals_[node.key_name], locals_[node.value_name] = bound_key, bound_value
            predicate = strict_predicate(self.expression(node.predicate, predicate_ctx))
            transforms.extend((self._transform_records(leaf), self._transform_records(predicate)))
            reductions.extend((self._reduction_records(leaf), self._reduction_records(predicate)))
            filters.extend((self._filter_records(leaf), self._filter_records(predicate)))
            taints.update(self._value_taints.get(id(leaf), ()))
            taints.update(self._value_taints.get(id(predicate), ()))
            if not predicate.known:
                fail("OKL-E-TYPE", "filter_keyed predicate must resolve to a Boolean value.",
                     node.predicate, phase="type")
            if not predicate.value:
                continue
            result = copied(leaf, node.predicate)
            source_records = (input_transforms if self.model.profile in KEYED_MERGE_PROFILES else
                              tuple(replace(record, key=key, input_entry=origins.get(key))
                                    if record.key is None else record for record in input_transforms))
            merge_transforms = (self._selected_transform_records
                                if self.model.profile in KEYED_MERGE_PROFILES else self._merge_transform_records)
            leaf_transforms = merge_transforms(source_records,
                self._transform_records(leaf), self._transform_records(predicate))
            leaf_reductions = self._merge_reduction_records(input_reductions,
                self._reduction_records(leaf), self._reduction_records(predicate))
            leaf_filters = self._merge_filter_records(input_filters,
                self._filter_records(leaf), self._filter_records(predicate), (current,))
            if leaf_transforms:
                self._value_transforms[id(result)] = (result, leaf_transforms)
            if leaf_reductions:
                self._value_reductions[id(result)] = (result, leaf_reductions)
            self._value_filters[id(result)] = (result, leaf_filters)
            leaf_merges = self._combine_merge_records(self._merge_records(source),
                self._merge_records(leaf), self._merge_records(predicate))
            if leaf_merges:
                self._value_merges[id(result)] = (result, leaf_merges)
            leaf_zips = self._combine_zip_records(self._zip_records(source),
                self._zip_records(leaf), self._zip_records(predicate))
            if leaf_zips:
                self._value_zips[id(result)] = (result, leaf_zips)
            leaf_rekeys = self._combine_rekey_records(self._rekey_records(source),
                self._rekey_records(leaf), self._rekey_records(predicate))
            if leaf_rekeys:
                self._value_rekeys[id(result)] = (result, leaf_rekeys)
            if taints:
                self._value_taints[id(result)] = set(taints)
                self._tainted_values[id(result)] = result
            entries.append((key, result))
        self.budget.tick(node)
        payload = KeyedValue(tuple(entries))
        value = Value(result_type, payload)
        self.budget.charge_value(value, node)
        self._keyed_payloads[id(payload)] = payload
        self._keyed_origins[id(payload)] = {key: origins[key] for key, _ in entries if key in origins}
        retained_transforms = self._merge_transform_records(*transforms)
        retained_reductions = self._merge_reduction_records(*reductions)
        retained_filters = self._merge_filter_records(*filters, (current,))
        if retained_transforms:
            self._value_transforms[id(value)] = (value, retained_transforms)
        if retained_reductions:
            self._value_reductions[id(value)] = (value, retained_reductions)
        self._value_filters[id(value)] = (value, retained_filters)
        if taints:
            self._value_taints[id(value)] = set(taints)
            self._tainted_values[id(value)] = value
            for path in taints:
                self._mark_generated(path, node)
        return value

    def _keyed_merge_checkpoint(self, node: Any, stage: str, key: str) -> None:
        """Poll the actual ledger while exposing the selected key to observers."""
        ledger = getattr(self.budget, "execution_budget", None)
        previous_stage = ledger.stage if ledger is not None else None
        try:
            if ledger is not None:
                ledger.stage = stage
            self.budget.tick(node)
        finally:
            if ledger is not None:
                ledger.stage = previous_stage

    def _keyed_merge_input(self, operand: Any, token: Any, ctx: Context,
                           element_type: Type) -> Value:
        """Evaluate and complete one actual operand admission on this ledger."""
        result_type = Type("Keyed", element=element_type)
        # Global static checking visits both unknown inputs first. During
        # actual construction this complete left admission precedes any
        # dynamic evaluation of the right operand.
        source = self.expression(operand, ctx)
        if source.type != result_type:
            fail("OKL-E-TYPE", f"merge_keyed requires exactly {result_type}, received {source.type}.",
                 token, phase="type",
                 details={"expected": str(result_type), "actual": str(source.type)})
        self._keyed_leaf(source.type.element, operand)
        if ctx.abstract:
            return source
        if not source.known or not isinstance(source.value, KeyedValue):
            fail("OKL-E-TYPE", "merge_keyed input must resolve to an immutable keyed value.",
                 token, phase="type")
        count = len(source.value.entries)
        if count > MAX_KEYED_ENTRIES:
            fail("OKL-E-RESOURCE", "Merge input exceeds 256 entries.", operand, phase="support",
                 details={"budget": "keyed_entries", "limit": MAX_KEYED_ENTRIES,
                          "consumed": count})
        self.budget.charge_value(source, operand)
        prior_key = None
        for key, leaf in source.value.entries:
            self.budget.tick(operand)
            self.key(operand, key)
            if prior_key is not None and key <= prior_key:
                fail("OKL-E-ID", "Merge input keys must be unique canonical stable keys.",
                     operand, phase="binding")
            if leaf.type != element_type:
                fail("OKL-E-TYPE", "Merge input entry has a different resolved leaf type.",
                     token, phase="type",
                     details={"expected": str(result_type), "actual": str(Type("Keyed", element=leaf.type))})
            prior_key = key
        return source

    def _merge_keyed_expression(self, node: Any, ctx: Context) -> Value:
        if self.linked.modules[node.source_id].ast.profile not in KEYED_MERGE_PROFILES:
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "merge_keyed requires keyed-merge-0.1.",
                 node, phase="support")
        element_type = self.parse_type(node.element_type)
        self._keyed_leaf(element_type, node.element_type)
        result_type = Type("Keyed", element=element_type)


        left = self._keyed_merge_input(node.left, node.left_token, ctx, element_type)
        right = self._keyed_merge_input(node.right, node.right_token, ctx, element_type)
        if ctx.abstract:
            return Value(result_type)

        # Charge the bounded index before allocating it. Both operands have
        # completed admission, so the scan cannot hide a right constructor
        # error or admit a result by overwriting an existing key.
        self.budget.tick(node.left, max(1, len(left.value.entries)))
        left_keys = {key for key, _ in left.value.entries}
        for key, _ in right.value.entries:
            self._keyed_merge_checkpoint(node, "keyed_merge_collision", key)
            if key in left_keys:
                raise OntoKinError("OKL-E-ID", "merge_keyed inputs share key " + json.dumps(key) + ".",
                                   node.right_token, category="invalid", phase="elaboration",
                                   rule_ids=["LANG-007"], related=[node.left_token],
                                   details={"operation": "merge_keyed", "key": key})
        count = len(left.value.entries) + len(right.value.entries)
        if count > MAX_KEYED_ENTRIES:
            fail("OKL-E-RESOURCE", "Keyed merge result exceeds 256 entries.",
                 node.operator_token, phase="support",
                 details={"bound": "keyed_merge_result_entries", "limit": MAX_KEYED_ENTRIES,
                          "actual": count})

        transforms = [self._transform_records(left), self._transform_records(right)]
        reductions = [self._reduction_records(left), self._reduction_records(right)]
        filters = [self._filter_records(left), self._filter_records(right)]
        taints = set(self._value_taints.get(id(left), ())) | set(self._value_taints.get(id(right), ()))
        for source in (left, right):
            for _, leaf in source.value.entries:
                self.budget.tick(node)
                transforms.append(self._transform_records(leaf))
                reductions.append(self._reduction_records(leaf))
                filters.append(self._filter_records(leaf))
                taints.update(self._value_taints.get(id(leaf), ()))
        current = KeyedMergeOrigin(node, node.left, node.right, element_type, "both")
        merged_origins = self._combine_merge_records(self._merge_records(left),
                                                     self._merge_records(right), (current,))
        input_origins = (self._keyed_origins.get(id(left.value), {}),
                         self._keyed_origins.get(id(right.value), {}))
        groups = (left.value.entries, right.value.entries)
        cursors = [0, 0]
        entries, origins = [], {}
        self.budget.tick(node, max(1, count))
        while cursors[0] < len(groups[0]) or cursors[1] < len(groups[1]):
            if cursors[0] == len(groups[0]):
                side = 1
            elif cursors[1] == len(groups[1]):
                side = 0
            else:
                self.budget.tick(node)
                side = int(groups[1][cursors[1]][0] < groups[0][cursors[0]][0])
            key, leaf = groups[side][cursors[side]]
            self._keyed_merge_checkpoint(node, "keyed_merge_iteration", key)
            copied = self._inherit_value_info(leaf, Value(leaf.type, leaf.value, leaf.frame, leaf.hint))
            self.budget.charge_value(copied, node)
            contributor = replace(current, input_side="right" if side else "left")
            self._value_merges[id(copied)] = (copied, self._combine_merge_records(
                self._merge_records(leaf), (contributor,)))
            entries.append((key, copied))
            if key in input_origins[side]:
                origins[key] = input_origins[side][key]
            cursors[side] += 1

        self.budget.tick(node)
        payload = KeyedValue(tuple(entries))
        result = Value(result_type, payload)
        self.budget.charge_value(result, node)
        self._keyed_payloads[id(payload)] = payload
        self._keyed_origins[id(payload)] = origins
        retained_transforms = self._merge_transform_records(*transforms)
        retained_reductions = self._merge_reduction_records(*reductions)
        retained_filters = self._merge_filter_records(*filters)
        if retained_transforms:
            self._value_transforms[id(result)] = (result, retained_transforms)
        if retained_reductions:
            self._value_reductions[id(result)] = (result, retained_reductions)
        if retained_filters:
            self._value_filters[id(result)] = (result, retained_filters)
        self._value_merges[id(result)] = (result, merged_origins)
        if taints:
            self._value_taints[id(result)] = set(taints)
            self._tainted_values[id(result)] = result
            for path in taints:
                self._mark_generated(path, node)
        return result

    def _keyed_rekey_checkpoint(self, node: Any, stage: str, key: str | None) -> None:
        """Poll the actual complete-request ledger; retain callback exceptions."""
        ledger = getattr(self.budget, "execution_budget", None)
        previous_stage = ledger.stage if ledger is not None else None
        try:
            if ledger is not None:
                ledger.stage = stage
            self.budget.tick(node)
        finally:
            if ledger is not None:
                ledger.stage = previous_stage

    def _keyed_rekey_input(self, operand: Any, token: Any, ctx: Context,
                           element_type: Type) -> Value:
        source = self.expression(operand, ctx)
        required = Type("Keyed", element=element_type)
        if source.type != required:
            fail("OKL-E-TYPE", f"rekey_keyed input requires exactly {required}, received {source.type}.",
                 token, phase="type", details={"expected": str(required), "actual": str(source.type)})
        self._keyed_leaf(source.type.element, operand)
        if ctx.abstract:
            return source
        if not source.known or not isinstance(source.value, KeyedValue):
            fail("OKL-E-TYPE", "rekey_keyed input must resolve to an immutable keyed value.",
                 token, phase="type")
        count = len(source.value.entries)
        if count > MAX_KEYED_ENTRIES:
            fail("OKL-E-RESOURCE", "Rekey input exceeds 256 entries.", operand, phase="support",
                 details={"budget": "keyed_entries", "limit": MAX_KEYED_ENTRIES, "consumed": count})
        self.budget.charge_value(source, operand)
        previous = None
        for key, leaf in source.value.entries:
            self.budget.tick(operand)
            self.key(operand, key)
            if previous is not None and key <= previous:
                fail("OKL-E-ID", "Rekey input keys must be unique canonical stable keys.",
                     operand, phase="binding")
            if leaf.type != element_type:
                fail("OKL-E-TYPE", "Rekey input entry has a different resolved leaf type.", token,
                     phase="type", details={"expected": str(required),
                                            "actual": str(Type("Keyed", element=leaf.type))})
            previous = key
        return source

    def _rekey_keyed_expression(self, node: Any, ctx: Context) -> Value:
        if self.linked.modules[node.source_id].ast.profile not in KEYED_REKEY_PROFILES:
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "rekey_keyed requires keyed-rekey-0.1.",
                 node, phase="support")
        element_type = self.parse_type(node.element_type)
        self._keyed_leaf(element_type, node.element_type)
        self._map_binders(node, ctx)
        result_type = Type("Keyed", element=element_type)
        # This expression's own abstract checks precede dynamic input work.
        # Known enclosing values are masked, including for empty inputs.
        abstract_input = self._unknown_local_context(ctx, node.input)
        self._keyed_rekey_input(node.input, node.input_token, abstract_input, element_type)
        abstract = self._unknown_local_context(ctx, node.body)
        abstract.locals[node.key_name] = Value(STRING)
        abstract.locals[node.value_name] = Value(element_type)

        def exact_key(value):
            if value.type != STRING:
                fail("OKL-E-TYPE", f"rekey_keyed body requires exactly String, received {value.type}.",
                     node.body_token, phase="type", details={"expected": "String", "actual": str(value.type)})
            return value

        exact_key(self.expression(node.body, abstract))
        if ctx.abstract:
            return Value(result_type)
        source = self._keyed_rekey_input(node.input, node.input_token, ctx, element_type)
        count = len(source.value.entries)
        self.budget.tick(node, max(1, count))
        originals = self._keyed_origins.get(id(source.value), {})
        first_by_new, entries, origins = {}, [], {}
        readers = (
            (self._value_transforms, self._transform_records, self._merge_transform_records),
            (self._value_reductions, self._reduction_records, self._merge_reduction_records),
            (self._value_filters, self._filter_records, self._merge_filter_records),
            (self._value_merges, self._merge_records, self._combine_merge_records),
            (self._value_zips, self._zip_records, self._aggregate_zip_records))
        groups = [[reader(source)] for _, reader, _ in readers]
        rekeys = [self._rekey_records(source)]
        taints = set(self._value_taints.get(id(source), ()))
        for _, leaf in source.value.entries:
            self.budget.tick(node.input)
            for group, (_, reader, _) in zip(groups, readers):
                group.append(reader(leaf))
            rekeys.append(self._rekey_records(leaf))
            taints.update(self._value_taints.get(id(leaf), ()))
        current = KeyedRekeyOrigin(node, node.input, node.body, element_type)
        locals_ = {}
        for name, value in ctx.locals.items():
            self.budget.tick(node)
            locals_[name] = value
        body_ctx = replace(ctx, locals=locals_)

        def copied(value, origin):
            result = self._inherit_value_info(value, Value(value.type, value.value, value.frame, value.hint))
            self.budget.charge_value(result, origin)
            return result

        for old_key, original in source.value.entries:
            self._keyed_rekey_checkpoint(node, "keyed_rekey_iteration", old_key)
            bound_key = Value(STRING, old_key)
            self.budget.charge_value(bound_key, node.key_node)
            locals_[node.key_name] = bound_key
            locals_[node.value_name] = copied(original, node.value_node)
            computed = exact_key(self.expression(node.body, body_ctx))
            if not computed.known or not isinstance(computed.value, str):
                fail("OKL-E-TYPE", "rekey_keyed body must resolve to an immutable String value.",
                     node.body_token, phase="type")
            new_key = computed.value
            self._keyed_rekey_checkpoint(node, "keyed_rekey_key_validation", old_key)
            self.budget.charge_value(computed, node.body)
            if not KEY_RE.fullmatch(new_key):
                related = [originals[old_key]] if old_key in originals else []
                raise OntoKinError("OKL-E-ID", "rekey_keyed produced invalid stable key " +
                                   json.dumps(new_key) + " from old key " + json.dumps(old_key) + ".",
                                   node.body_token, category="invalid", phase="elaboration",
                                   rule_ids=["LANG-007"], related=related,
                                   details={"operation": "rekey_keyed", "key": new_key, "old_key": old_key})
            self._keyed_rekey_checkpoint(node, "keyed_rekey_collision", old_key)
            self.budget.tick(node.body)
            if new_key in first_by_new:
                first = first_by_new[new_key]
                related = [originals[key] for key in (first, old_key) if key in originals]
                raise OntoKinError("OKL-E-ID", "rekey_keyed output key " + json.dumps(new_key) +
                                   " duplicates old keys " + json.dumps(first) + " and " + json.dumps(old_key) + ".",
                                   node.body_token, category="invalid", phase="elaboration",
                                   rule_ids=["LANG-007"], related=related,
                                   details={"operation": "rekey_keyed", "key": new_key,
                                            "first_old_key": first, "duplicate_old_key": old_key})
            first_by_new[new_key] = old_key
            result = copied(original, node.input)
            step = replace(current, old_key=old_key, new_key=new_key, input_entry=originals.get(old_key))
            self._value_rekeys[id(result)] = (result, self._combine_rekey_records(
                self._rekey_records(original), self._rekey_records(computed), (step,)))
            # Inherited contributor keys stay original. Only this family adds
            # the old-to-new step; aggregate reads cannot invent a contributor.
            for index, (field, reader, combine) in enumerate(readers):
                selected_combine = (self._selected_transform_records if index == 0 else
                                    self._combine_zip_records if index == 4 else combine)
                records = selected_combine(reader(original), reader(computed))
                if records:
                    field[id(result)] = (result, records)
                groups[index].append(reader(computed))
            rekeys.append(self._rekey_records(computed))
            leaf_taints = taints | self._value_taints.get(id(computed), set())
            if leaf_taints:
                self._value_taints[id(result)] = set(leaf_taints)
                self._tainted_values[id(result)] = result
                taints.update(leaf_taints)
            entries.append((new_key, result))
            if old_key in originals:
                origins[new_key] = originals[old_key]

        self.budget.tick(node, max(1, count) * max(1, count.bit_length()))
        ordered = sorted(entries, key=lambda item: item[0])
        self._keyed_rekey_checkpoint(node, "keyed_rekey_publication", None)
        payload = KeyedValue(tuple(ordered))
        result = Value(result_type, payload)
        self.budget.charge_value(result, node)
        self._keyed_payloads[id(payload)] = payload
        self._keyed_origins[id(payload)] = origins
        for (field, _, combine), group in zip(readers, groups):
            records = combine(*group)
            if records:
                field[id(result)] = (result, records)
        self._value_rekeys[id(result)] = (result, self._aggregate_rekey_records(*rekeys, (current,)))
        if taints:
            self._value_taints[id(result)] = set(taints)
            self._tainted_values[id(result)] = result
            for path in taints:
                self._mark_generated(path, node)
        return result

    def _keyed_zip_checkpoint(self, node: Any, stage: str, key: str) -> None:
        """Poll the real shared ledger without altering a callback exception."""
        ledger = getattr(self.budget, "execution_budget", None)
        previous_stage = ledger.stage if ledger is not None else None
        try:
            if ledger is not None:
                ledger.stage = stage
            self.budget.tick(node)
        finally:
            if ledger is not None:
                ledger.stage = previous_stage

    def _keyed_zip_input(self, operand: Any, token: Any, ctx: Context,
                         element_type: Type) -> Value:
        """Complete one operand's admission before evaluating the other."""
        source = self.expression(operand, ctx)
        required = Type("Keyed", element=element_type)
        if source.type != required:
            fail("OKL-E-TYPE", f"zip_keyed requires exactly {required}, received {source.type}.",
                 token, phase="type", details={"expected": str(required), "actual": str(source.type)})
        self._keyed_leaf(source.type.element, operand)
        if ctx.abstract:
            return source
        if not source.known or not isinstance(source.value, KeyedValue):
            fail("OKL-E-TYPE", "zip_keyed input must resolve to an immutable keyed value.",
                 token, phase="type")
        count = len(source.value.entries)
        if count > MAX_KEYED_ENTRIES:
            fail("OKL-E-RESOURCE", "Zip input exceeds 256 entries.", operand, phase="support",
                 details={"budget": "keyed_entries", "limit": MAX_KEYED_ENTRIES, "consumed": count})
        self.budget.charge_value(source, operand)
        previous = None
        for key, leaf in source.value.entries:
            self.budget.tick(operand)
            self.key(operand, key)
            if previous is not None and key <= previous:
                fail("OKL-E-ID", "Zip input keys must be unique canonical stable keys.",
                     operand, phase="binding")
            if leaf.type != element_type:
                fail("OKL-E-TYPE", "Zip input entry has a different resolved leaf type.", token,
                     phase="type", details={"expected": str(required),
                                            "actual": str(Type("Keyed", element=leaf.type))})
            previous = key
        return source

    def _zip_keyed_expression(self, node: Any, ctx: Context) -> Value:
        if self.linked.modules[node.source_id].ast.profile not in KEYED_ZIP_PROFILES:
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "zip_keyed requires keyed-zip-0.1.",
                 node, phase="support")
        types = []
        for declaration in (node.left_type, node.right_type, node.output_type):
            typ = self.parse_type(declaration)
            self._keyed_leaf(typ, declaration)
            types.append(typ)
        left_type, right_type, output_type = types
        self._map_binders(node, ctx)
        left = self._keyed_zip_input(node.left, node.left_token, ctx, left_type)
        right = self._keyed_zip_input(node.right, node.right_token, ctx, right_type)

        def exact_output(value):
            if value.type != output_type:
                fail("OKL-E-TYPE", f"Zip body requires exactly {output_type}, received {value.type}.",
                     node.body_token, phase="type",
                     details={"expected": str(output_type), "actual": str(value.type)})
            return value

        abstract = self._unknown_local_context(ctx, node.body)
        abstract.locals[node.key_name] = Value(STRING)
        abstract.locals[node.left_name] = Value(left_type)
        abstract.locals[node.right_name] = Value(right_type)
        exact_output(self.expression(node.body, abstract))
        result_type = Type("Keyed", element=output_type)
        if ctx.abstract:
            return Value(result_type)

        # Bounded indexes and sorting are charged before their allocation.
        # A complete key-set check precedes every callback and output copy.
        input_count = len(left.value.entries) + len(right.value.entries)
        self.budget.tick(node, max(1, input_count) * max(1, input_count.bit_length()))
        left_keys = {key for key, _ in left.value.entries}
        right_by_key = dict(right.value.entries)
        all_keys = sorted(left_keys | right_by_key.keys())
        for key in all_keys:
            self._keyed_zip_checkpoint(node, "keyed_zip_keyset", key)
            self.budget.tick(node, 2)
            has_left, has_right = key in left_keys, key in right_by_key
            if has_left != has_right:
                missing_side = "right" if has_left else "left"
                primary = node.right_token if has_left else node.left_token
                related = node.left_token if has_left else node.right_token
                raise OntoKinError("OKL-E-ID", "zip_keyed key " + json.dumps(key) +
                                   " is missing from the " + missing_side + " input.",
                                   primary, category="invalid", phase="elaboration",
                                   rule_ids=["LANG-007"], related=[related],
                                   details={"operation": "zip_keyed", "key": key,
                                            "missing_side": missing_side})

        transforms = [self._transform_records(left), self._transform_records(right)]
        reductions = [self._reduction_records(left), self._reduction_records(right)]
        filters = [self._filter_records(left), self._filter_records(right)]
        merges = [self._merge_records(left), self._merge_records(right)]
        zips = [self._zip_records(left), self._zip_records(right)]
        taints = set(self._value_taints.get(id(left), ())) | set(self._value_taints.get(id(right), ()))
        for source in (left, right):
            for _, leaf in source.value.entries:
                self.budget.tick(node)
                transforms.append(self._transform_records(leaf))
                reductions.append(self._reduction_records(leaf))
                filters.append(self._filter_records(leaf))
                merges.append(self._merge_records(leaf))
                zips.append(self._zip_records(leaf))
                taints.update(self._value_taints.get(id(leaf), ()))
        current = KeyedZipOrigin(node, node.left, node.right, node.body,
                                 left_type, right_type, output_type)
        left_origins = self._keyed_origins.get(id(left.value), {})
        right_origins = self._keyed_origins.get(id(right.value), {})
        locals_ = {}
        for name, value in ctx.locals.items():
            self.budget.tick(node)
            locals_[name] = value
        body_ctx = replace(ctx, locals=locals_)
        entries = []

        def copied(value, origin):
            result = self._inherit_value_info(value, Value(value.type, value.value, value.frame, value.hint))
            self.budget.charge_value(result, origin)
            return result

        for key, left_leaf in left.value.entries:
            self._keyed_zip_checkpoint(node, "keyed_zip_iteration", key)
            self.budget.tick(node)
            right_leaf = right_by_key[key]
            bound_key = Value(STRING, key)
            self.budget.charge_value(bound_key, node.key_node)
            locals_[node.key_name] = bound_key
            locals_[node.left_name] = copied(left_leaf, node.left_node)
            locals_[node.right_name] = copied(right_leaf, node.right_node)
            computed = exact_output(self.expression(node.body, body_ctx))
            if not computed.known:
                fail("OKL-E-TYPE", "zip_keyed body must resolve to an immutable leaf value.",
                     node.body_token, phase="type")
            result = copied(computed, node.body)
            pair = replace(current, key=key, left_entry=left_origins.get(key), right_entry=right_origins.get(key))
            self._value_zips[id(result)] = (result, self._combine_zip_records(
                self._zip_records(left_leaf), self._zip_records(right_leaf), self._zip_records(computed), (pair,)))
            rekeys = self._combine_rekey_records(self._rekey_records(left_leaf),
                self._rekey_records(right_leaf), self._rekey_records(computed))
            if rekeys:
                self._value_rekeys[id(result)] = (result, rekeys)
            selected_transforms = self._selected_transform_records(
                self._transform_records(left), self._transform_records(right),
                self._transform_records(left_leaf), self._transform_records(right_leaf),
                self._transform_records(computed))
            if selected_transforms:
                self._value_transforms[id(result)] = (result, selected_transforms)
            for field, reader, combine in (
                    (self._value_reductions, self._reduction_records, self._merge_reduction_records),
                    (self._value_filters, self._filter_records, self._merge_filter_records),
                    (self._value_merges, self._merge_records, self._combine_merge_records)):
                records = combine(reader(left), reader(right), reader(left_leaf), reader(right_leaf), reader(computed))
                if records:
                    field[id(result)] = (result, records)
            leaf_taints = taints | self._value_taints.get(id(computed), set())
            if leaf_taints:
                self._value_taints[id(result)] = set(leaf_taints)
                self._tainted_values[id(result)] = result
                taints.update(leaf_taints)
            transforms.append(self._transform_records(computed))
            reductions.append(self._reduction_records(computed))
            filters.append(self._filter_records(computed))
            merges.append(self._merge_records(computed))
            zips.append(self._zip_records(computed))
            entries.append((key, result))

        self.budget.tick(node)
        payload = KeyedValue(tuple(entries))
        result = Value(result_type, payload)
        self.budget.charge_value(result, node)
        self._keyed_payloads[id(payload)] = payload
        self._keyed_origins[id(payload)] = dict(left_origins)
        for field, combine, groups in (
                (self._value_transforms, self._merge_transform_records, transforms),
                (self._value_reductions, self._merge_reduction_records, reductions),
                (self._value_filters, self._merge_filter_records, filters),
                (self._value_merges, self._combine_merge_records, merges)):
            records = combine(*groups)
            if records:
                field[id(result)] = (result, records)
        self._value_zips[id(result)] = (result, self._aggregate_zip_records(*zips, (current,)))
        if taints:
            self._value_taints[id(result)] = set(taints)
            self._tainted_values[id(result)] = result
            for path in taints:
                self._mark_generated(path, node)
        return result

    def expect(self, value: Value, typ: Type, node: Any) -> Value:
        if typ.kind == "ReachBranch" and value.type != typ:
            from .reach_source import reach_error
            raise reach_error("reach_type", "ReachBranch has no implicit String, Int or other conversion.", node,
                              details={"expected_type": "ReachBranch", "actual_type": str(value.type)})
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
                if member.name in self.predefined(member) or member.name in FIELD_TYPES or member.name in READONLY_FIELDS or member.name in local_names:
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
                        if member.key_name == member.value_name or {member.key_name, member.value_name} & self.predefined(member):
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
            if local.name in names or local.name in self.predefined(local):
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
                    elif event.kind == "impulse":
                        self.impulse_values(event, ctx)
                    elif event.kind == "force":
                        from .force_source import force_values
                        force_values(self, event, ctx)
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
        if self.linked.modules[node.source_id].ast.profile in REACH_PROFILES and name not in ctx.locals:
            from .reach_source import BRANCHES
            if name in BRANCHES:
                return Value(Type("ReachBranch"), name)
            if name == "reach_planar":
                return Value(Type("BuiltinCallable"), name)
        if (name in TEXTURE_CALLS and self.linked.modules[node.source_id].ast.profile in TEXTURE_PROFILES
                and name not in ctx.locals):
            return Value(Type("BuiltinCallable"), name)
        if (name in POCKETS_CALLS and self.linked.modules[node.source_id].ast.profile in POCKETS_PROFILES
                and name not in ctx.locals):
            return Value(Type("BuiltinCallable"), name)
        if (name in FRAMED_LOFT_CALLS and self.linked.modules[node.source_id].ast.profile in FRAMED_LOFT_PROFILES
                and name not in ctx.locals):
            return Value(Type("BuiltinCallable"), name)
        if (name in RING_LOFT_CALLS and self.linked.modules[node.source_id].ast.profile in RING_LOFT_PROFILES
                and name not in ctx.locals):
            return Value(Type("BuiltinCallable"), name)
        if (name in HOLES_CALLS and self.linked.modules[node.source_id].ast.profile in HOLES_PROFILES
                and name not in ctx.locals):
            return Value(Type("BuiltinCallable"), name)
        if (name in EXTRUSION_CALLS and self.linked.modules[node.source_id].ast.profile in EXTRUSION_PROFILES
                and name not in ctx.locals):
            return Value(Type("BuiltinCallable"), name)
        if (name in SURFACE_CALLS and self.linked.modules[node.source_id].ast.profile in SURFACE_PROFILES
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
                self.bindings[id(node)] = self._member_definition_id(member)
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
        transforms = self._transform_records(result)
        if not transforms:
            if self.model.profile in KEYED_MERGE_PROFILES:
                # Aggregate origins may come only from a condition or the
                # other merge operand. The selected leaf alone establishes
                # which map actually supplied this key.
                transforms = self._transform_records(value)
            else:
                origin = self._keyed_origins.get(id(value.value), {}).get(index.value)
                transforms = tuple(replace(record, key=index.value, input_entry=origin)
                                   if record.key is None else record
                                   for record in self._transform_records(value))
        if transforms:
            result = self._inherit_value_info(result, Value(result.type, result.value, result.frame, result.hint))
            self.budget.charge_value(result, node)
            self._value_transforms[id(result)] = (result, transforms)
        taints = self._value_taints.get(id(value), set())
        for path in taints:
            self._mark_generated(path, node)
        if taints:
            if self.model.profile in KEYED_FILTER_PROFILES and not transforms:
                # A selected collection can share a plain payload while its
                # condition carries generated-view taint. Keep that taint on
                # this indexed result, never on the original shared leaf.
                result = self._inherit_value_info(result, Value(result.type, result.value, result.frame, result.hint))
                self.budget.charge_value(result, node)
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

    def _string_addition_syntax(self, node: Any) -> bool:
        return (node.kind == "binary" and node.op == "+"
                and self.linked.modules[node.source_id].ast.profile == STRING_CONCAT_PROFILE)

    def _string_addition(self, node: Any, ctx: Context) -> Value:
        # Evaluate each operand once, preserving inherited left-to-right errors
        # and the ordinary expression flow for dependencies and generated taint.
        left = self.expression(node.left, ctx)
        right = self.expression(node.right, ctx)
        if left.type != STRING or right.type != STRING:
            return binary(node.op, left, right, node, self.warning)
        if ctx.abstract or not left.known or not right.known:
            return Value(STRING)
        ledger = self.budget.execution_budget
        try:
            result = concat_strings(left.value, right.value, node, ledger)
        except BaseException as error:
            if error is ledger.callback_error:
                self.budget.callback_error = error
            raise
        return Value(STRING, result)

    def _constant_names(self, node: Any, depth: int = 0) -> frozenset[str] | None:
        """Classify a sealed source subtree without reading occurrence state.

        Linked source nodes live for the whole compiler and are never edited
        during construction. Each first classification is charged; nesting is
        bounded independently of whether the subtree will produce a cache hit.
        The names returned must remain unshadowed in the current context.
        Retain the subtree height too: a value warmed in a shallow call must
        not bypass the same expression nesting limit in a deeper occurrence.
        """
        if id(node) in self._constant_syntax:
            return self._constant_syntax[id(node)][0]
        self.budget.tick(node)
        if depth >= 128:
            return None
        kind = node.kind
        children = ()
        height = 1
        if kind in {"number", "string", "bool"}:
            result = frozenset()
        elif kind == "name" and node.name in _CONSTANT_CALLS | {"world"}:
            result = frozenset({node.name})
        elif kind == "unary":
            children = (node.value,)
            result = frozenset()
        elif kind == "binary":
            if self._string_addition_syntax(node):
                result = None
            else:
                children = (node.left, node.right)
                result = frozenset()
        elif kind == "call" and node.callee.kind == "name" and node.callee.name in _CONSTANT_CALLS:
            children = (node.callee, *node.args)
            result = frozenset()
        else:
            result = None
        for child in children:
            names = self._constant_names(child, depth + 1)
            if names is None:
                result = None
                break
            result = result | names
            height = max(height, 1 + self._constant_syntax[id(child)][1])
        self._constant_syntax[id(node)] = result, height
        return result

    def _parameter_plan(self, node: Any, depth: int = 0):
        """Find ordered reads in a sealed, non-short-circuit pure expression.

        The plan contains syntax only. Each successful value remains in the
        existing request LRU, and every occurrence replays its own ordinary
        member/dependency/access guards before using that value.
        """
        prior = self._parameter_syntax.get(id(node))
        if prior is not None and prior[0] is node:
            return prior[1]
        self.budget.tick(node)
        if depth >= 128:
            return None
        kind, children, reads, names, height = node.kind, (), (), frozenset(), 1
        # A successful sealed constant subtree has no occurrence reads. Its
        # names still participate in every occurrence's shadowing guard. This
        # also keeps an inner constant-cache hit from hiding a planned read.
        constants = self._constant_names(node) if kind in {"call", "binary"} else None
        if kind in {"number", "string", "bool"}:
            pass
        elif kind == "name" and node.name in _PARAMETER_CALLS | {"world"}:
            reads, names = (("name", node),), frozenset({node.name})
        elif kind == "member" and node.target.kind == "name" and node.target.name == "self":
            reads, names, height = (("parameter", node),), frozenset({"self"}), 2
        elif kind == "unary":
            children = (node.value,)
        elif kind == "binary" and node.op not in {"and", "or"}:
            if self._string_addition_syntax(node):
                self._parameter_syntax[id(node)] = node, None
                return None
            children = (node.left, node.right)
        elif kind == "call" and node.callee.kind == "name" and node.callee.name in _PARAMETER_CALLS:
            children = (node.callee, *node.args)
        elif (kind == "keyed" and depth == 0 and node.element_type.name in SURFACE_TYPES
                and not optional(node.element_type, "args", [])
                and len(node.entries) <= MAX_KEYED_ENTRIES):
            for entry in node.entries:
                plan = self._parameter_plan(entry.value, depth + 1)
                if plan is None:
                    self._parameter_syntax[id(node)] = node, None
                    return None
                child_reads, child_names, child_height = plan
                reads += (("keyed_entry", entry),) + child_reads
                names |= child_names
                height = max(height, 1 + child_height)
        else:
            self._parameter_syntax[id(node)] = node, None
            return None
        for child in children:
            plan = self._parameter_plan(child, depth + 1)
            if plan is None:
                self._parameter_syntax[id(node)] = node, None
                return None
            child_reads, child_names, child_height = plan
            reads += child_reads
            names |= child_names
            height = max(height, 1 + child_height)
        # Classify every child before dropping constant-only reads, so even
        # an entirely constant conditional/short-circuit expression remains
        # outside this parameter-result optimization.
        result = (() if constants is not None else reads), names, height
        self._parameter_syntax[id(node)] = node, result
        return result

    @staticmethod
    def _parameter_value_key(value: Value, *, name=False):
        """Exact native scalar identity; no numeric coercion or mutable data."""
        if type(value) is not Value or type(value.type) is not Type:
            return None
        typ, payload = value.type, value.value
        if value.frame is not None or value.hint is not None:
            return None
        if name:
            if (typ == Type("BuiltinCallable") and type(payload) is str and payload in _PARAMETER_CALLS
                    or typ == Type("FrameRef") and type(payload) is str and payload == "world"):
                return typ, payload
            return None
        if typ.kind == "Quantity":
            if (type(typ.dimension) is not tuple or len(typ.dimension) != 4
                    or any(type(x) is not int for x in typ.dimension)):
                return None
        elif typ not in {INT, Type("Real"), BOOL, STRING}:
            return None
        if typ.element is not None or typ.name is not None:
            return None
        if typ.kind in {"Real", "Quantity"}:
            if type(payload) is not float or not math.isfinite(payload):
                return None
            return typ, payload.hex()
        expected = {"Int": int, "Bool": bool, "String": str}[typ.kind]
        return (typ, payload) if type(payload) is expected else None

    @classmethod
    def _parameter_result_immutable(cls, value):
        if type(value) is Value:
            if cls._parameter_value_key(value) is not None:
                return True
            if (type(value.type) is Type and value.type.kind == "Keyed"
                    and value.type.element in {Type(name) for name in SURFACE_TYPES}
                    and value.type.dimension is None and value.type.name is None
                    and value.frame is None and value.hint is None):
                payload = value.value
                return (type(payload) is KeyedValue and type(payload.entries) is tuple
                        and len(payload.entries) <= MAX_KEYED_ENTRIES
                        and all(type(entry) is tuple and len(entry) == 2
                                and type(entry[0]) is str and type(entry[1]) is Value
                                and entry[1].type == value.type.element
                                and cls._parameter_result_immutable(entry[1])
                                for entry in payload.entries))
            if (type(value.type) is not Type or value.type.kind not in
                    {"Vec3", "Vector3", "Point3", "Rotation", "Color", "Range", *SURFACE_TYPES}
                    or value.frame not in (None, "world") or value.hint is not None):
                return False
            return cls._parameter_result_immutable(value.value)
        if type(value) is tuple:
            return all(cls._parameter_result_immutable(item) for item in value)
        return type(value) is str or type(value) is float and math.isfinite(value)

    @classmethod
    def _parameter_copy(cls, value):
        """Detach all wrappers while sharing only immutable scalar leaves."""
        if type(value) is Value:
            return Value(value.type, cls._parameter_copy(value.value), value.frame, value.hint)
        if type(value) is KeyedValue:
            return KeyedValue(tuple((key, cls._parameter_copy(item)) for key, item in value.entries))
        if type(value) is tuple:
            return tuple(cls._parameter_copy(item) for item in value)
        return value

    def _capture_parameter_event(self, kind, node, key):
        capture = self._parameter_capture
        if capture is None or capture[2] is None or id(node) not in capture[0]:
            return
        reads, seen = capture[1], capture[2]
        if (len(seen) == len(reads) or reads[len(seen)][0] != kind or reads[len(seen)][1] is not node
                or key is None):
            capture[2] = None
        else:
            seen.append(key)

    def _capture_parameter_read(self, node, result):
        capture = self._parameter_capture
        if capture is None or capture[2] is None or id(node) not in capture[0]:
            return
        reads, seen = capture[1], capture[2]
        if len(seen) == len(reads) or reads[len(seen)][1] is not node:
            capture[2] = None
            return
        kind = reads[len(seen)][0]
        key = self._parameter_value_key(result, name=kind == "name")
        self._capture_parameter_event(kind, node, key)

    def _parameter_context(self, ctx, reads, names, node=None):
        if (ctx.abstract or ctx.self_path is None or not names.isdisjoint(ctx.locals)
                or ctx.self_path not in self.instances):
            return None
        if node is not None and node.kind == "keyed":
            entries = tuple(read for kind, read in reads if kind == "keyed_entry")
            if (len(entries) != len(node.entries)
                    or any(planned is not current for planned, current in zip(entries, node.entries))):
                return None
        instance = self.instances[ctx.self_path]
        for kind, read in reads:
            if kind == "parameter":
                member = instance.cls.members.get(read.name)
                if member is None or member.node.kind != "param":
                    return None
        return ctx.self_path, ctx.self_type, ctx.lexical_class, ctx.abstract, id(instance), id(instance.cls)

    def _parameter_replay(self, ctx, reads, expected):
        for (kind, read), wanted in zip(reads, expected):
            if kind == "keyed_entry":
                self.budget.tick(read)
                self.key(read, read.key)
                if type(read.key) is not str or read.key != wanted:
                    return False
                continue
            elif kind == "name":
                value = self.name(read.name, ctx, read)
            else:
                target = self.name("self", ctx, read.target)
                value = self.member(target, read.name, ctx, read)
            self._observe_value_flow(value)
            if self._parameter_value_key(value, name=kind == "name") != wanted:
                # Do not inspect later parameters: the ordinary arithmetic
                # following this changed read may fail before reaching them.
                return False
        return True

    def _keyed_expression(self, node, ctx):
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
            self._capture_parameter_event("keyed_entry", entry, entry.key)
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

    def expression(self, node: Any, ctx: Context) -> Value:
        self.budget.tick(node)
        if (ctx.abstract and self.linked.modules[node.source_id].ast.profile in KEYED_TRANSFORM_PROFILES
                and any(value.known for value in ctx.locals.values())):
            ctx = self._unknown_local_context(ctx, node)
        tracking = self.model.profile in KEYED_TRANSFORM_PROFILES and not ctx.abstract
        if tracking:
            self._expression_flows.append({"transforms": [], "reductions": [], "filters": [],
                                           "merges": [], "zips": [], "rekeys": [], "taints": set()})
        self._expression_depth += 1
        try:
            if self._expression_depth > 128:
                if self.model.profile in KEYED_TRANSFORM_PROFILES:
                    fail("OKL-E-RESOURCE", "Pure expression/call nesting exceeds bounded construction work.",
                         node, phase="support", details={"budget": "expression_depth", "limit": 128,
                                                        "consumed": self._expression_depth})
                fail("OKL-E-RESOURCE", "Pure expression/call nesting exceeds bounded construction work.", node, phase="support")
            constant_names = (self._constant_names(node) if self.reach_work is not None
                              and node.kind in {"call", "binary"} else None)
            constant_key = None
            if (constant_names is not None and constant_names.isdisjoint(ctx.locals)
                    and self._expression_depth + self._constant_syntax[id(node)][1] - 1 <= 128):
                constant_key = ("construction_constant", id(node), ctx.abstract)
                cached = self.reach_work.lookup(constant_key)
                if (cached is not None and constant_names.isdisjoint(ctx.locals)
                        and constant_key[-1] == ctx.abstract):
                    # A binding can attach its own dependency/taint route to a
                    # wrapper. Never return the retained wrapper to that code.
                    return self._finish_value_flow(Value(cached.type, cached.value, cached.frame, cached.hint), node, tracking)
            parameter_key = parameter_plan = parameter_context = capture = None
            if (self.reach_work is not None and constant_names is None and not ctx.abstract
                    and self._parameter_capture is None and node.kind in {"call", "binary", "keyed"}):
                parameter_plan = self._parameter_plan(node)
                if parameter_plan is not None:
                    reads, names, height = parameter_plan
                    surface_value = (node.kind == "keyed" or node.kind == "call"
                                     and node.callee.kind == "name"
                                     and node.callee.name in _IMMUTABLE_SURFACE_CALLS)
                    if ((surface_value or any(kind == "parameter" for kind, _ in reads))
                            and self._expression_depth + height - 1 <= 128):
                        parameter_context = self._parameter_context(ctx, reads, names, node)
                    if parameter_context is not None:
                        parameter_key = ("construction_parameters", id(node))
                        cached = self.reach_work.lookup(parameter_key)
                        keyed_type = None
                        if cached is not None and cached[0] is node and node.kind == "keyed":
                            element = self.parse_type(node.element_type)
                            self._keyed_leaf(element, node)
                            keyed_type = Type("Keyed", element=element)
                        if (cached is not None and cached[0] is node
                                and (node.kind != "keyed" or keyed_type == cached[2].type)
                                and self._parameter_context(ctx, reads, names, node) == parameter_context
                                and self._parameter_replay(ctx, reads, cached[1])
                                and not (tracking and (self._expression_flows[-1]["transforms"]
                                                       or self._expression_flows[-1]["filters"]
                                                       or self._expression_flows[-1]["merges"]
                                                       or self._expression_flows[-1]["zips"]
                                                       or self._expression_flows[-1]["rekeys"]
                                                       or self._expression_flows[-1]["reductions"]
                                                       or self._expression_flows[-1]["taints"]))
                                and self._parameter_context(ctx, reads, names, node) == parameter_context):
                            value = self._parameter_copy(cached[2])
                            if node.kind == "keyed":
                                self.budget.charge_value(value, node)
                                self._keyed_origins[id(value.value)] = {
                                    entry.key: entry for entry in node.entries}
                                self._keyed_payloads[id(value.value)] = value.value
                            return self._finish_value_flow(value, node, tracking)
                        capture = [{id(read) for _, read in reads}, reads, []]
                        self._parameter_capture = capture
            try:
                if self._string_addition_syntax(node):
                    result = self._string_addition(node, ctx)
                elif node.kind == "rekey_keyed":
                    result = self._rekey_keyed_expression(node, ctx)
                elif node.kind == "zip_keyed":
                    result = self._zip_keyed_expression(node, ctx)
                elif node.kind == "merge_keyed":
                    result = self._merge_keyed_expression(node, ctx)
                elif node.kind == "filter_keyed":
                    result = self._filter_keyed_expression(node, ctx)
                elif node.kind == "reduce_keyed":
                    result = self._reduce_keyed_expression(node, ctx)
                elif node.kind == "map_keyed":
                    result = self._map_keyed_expression(node, ctx)
                elif node.kind == "keyed":
                    result = self._keyed_expression(node, ctx)
                elif node.kind == "index":
                    value = self.expression(node.target, ctx)
                    index = self.expression(node.index, ctx)
                    result = self.index_value(value, index, node, ctx)
                else:
                    result = super().expression(node, ctx)
            finally:
                if capture is not None:
                    self._parameter_capture = None
            self._capture_parameter_read(node, result)
            if (constant_key is not None and constant_names.isdisjoint(ctx.locals)
                    and constant_key[-1] == ctx.abstract):
                self.reach_work.remember(constant_key, result)
            if (capture is not None and capture[2] is not None and len(capture[2]) == len(reads)
                    and self._parameter_result_immutable(result)
                    # A new derivation-bearing read is not a cache identity.
                    # Keep its real wrappers; older/plain reads still retain
                    # the exact existing cache replay and charging path.
                    and not (tracking and (self._expression_flows[-1]["transforms"]
                                           or self._expression_flows[-1]["filters"]
                                           or self._expression_flows[-1]["merges"]
                                                       or self._expression_flows[-1]["zips"]
                                                       or self._expression_flows[-1]["rekeys"]
                                                       or self._expression_flows[-1]["reductions"]
                                                       or self._expression_flows[-1]["taints"]))
                    and self._parameter_context(ctx, reads, names, node) == parameter_context):
                value = self._parameter_copy(result)
                self.reach_work.remember(parameter_key, (node, tuple(capture[2]), value),
                    admission=lambda: self._parameter_context(ctx, reads, names, node) == parameter_context)
            return self._finish_value_flow(result, node, tracking)
        except OntoKinError as error:
            # A heterogeneous vector can fail while evaluating planar_uv's
            # arguments, before its typed builtin is reached. Keep this new
            # signature diagnostic local to the actual .13 argument source.
            location = error.diagnostic.node
            if (error.code == "OKL-E-UNIT" and node.kind == "call"
                    and node.callee.kind == "name" and node.callee.name == "planar_uv"
                    and self.linked.modules[node.source_id].ast.profile in TEXTURE_PROFILES
                    and error is not self.budget.callback_error
                    and error is not getattr(getattr(self.budget, "execution_budget", None), "callback_error", None)
                    and getattr(location, "source_id", None) == node.source_id
                    and any(arg.start <= location.start <= location.end <= arg.end for arg in node.args[:3])):
                fail("OKL-E-TYPE", str(error), location, phase="type", details=error.diagnostic.details)
            raise
        finally:
            self._expression_depth -= 1
            if tracking:
                self._expression_flows.pop()

    def builtin(self, name: str, args: list[Value], node: Any, ctx: Context) -> Value:
        if name in TEXTURE_CALLS and self.linked.modules[node.source_id].ast.profile in TEXTURE_PROFILES:
            return texture_builtin(self, name, args, node, ctx)
        if name == "reach_planar":
            from .reach_source import reach_builtin
            return reach_builtin(self, args, node, ctx)
        if name in POCKETS_CALLS:
            if self.linked.modules[node.source_id].ast.profile not in POCKETS_PROFILES:
                fail("OKL-E-CAPABILITY-UNSUPPORTED", "Pocket constructors require polygon-pockets-0.1.",
                     node, phase="support")
            return pockets_builtin(self, name, args, node, ctx)
        if name in FRAMED_LOFT_CALLS:
            if self.linked.modules[node.source_id].ast.profile not in FRAMED_LOFT_PROFILES:
                fail("OKL-E-CAPABILITY-UNSUPPORTED", "Framed section constructors require framed-polygon-loft-0.1.",
                     node, phase="support")
            return framed_loft_builtin(self, name, args, node, ctx)
        if name in RING_LOFT_CALLS:
            if self.linked.modules[node.source_id].ast.profile not in RING_LOFT_PROFILES:
                fail("OKL-E-CAPABILITY-UNSUPPORTED", "Polygon section constructors require polygon-loft-0.1.",
                     node, phase="support")
            return ring_loft_builtin(self, name, args, node, ctx)
        if name in HOLES_CALLS:
            if self.linked.modules[node.source_id].ast.profile not in HOLES_PROFILES:
                fail("OKL-E-CAPABILITY-UNSUPPORTED", "Ring constructors require polygon-holes-0.1.",
                     node, phase="support")
            return holes_builtin(self, name, args, node, ctx)
        if name in EXTRUSION_CALLS:
            if self.linked.modules[node.source_id].ast.profile not in EXTRUSION_PROFILES:
                fail("OKL-E-CAPABILITY-UNSUPPORTED", "Extrusion constructors require polygon-extrusion-0.1.",
                     node, phase="support")
            return extrusion_builtin(self, name, args, node, ctx)
        if name in SURFACE_CALLS:
            if self.linked.modules[node.source_id].ast.profile not in SURFACE_PROFILES:
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
            definition_id = self._member_definition_id(member)
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
            if self.model.profile in KEYED_MERGE_PROFILES:
                transforms = self._selected_transform_records(self._transform_records(value),
                                                               self._transform_records(leaf))
                if transforms:
                    derived_leaf = self._inherit_value_info(leaf, Value(
                        leaf.type, leaf.value, leaf.frame, leaf.hint))
                    self.budget.charge_value(derived_leaf, node.input)
                    self._value_transforms[id(derived_leaf)] = (derived_leaf, transforms)
                    locals_[node.value_name] = derived_leaf
                    generated["input_transforms"] = self.transform_provenance(derived_leaf)
            elif self._transform_records(leaf):
                generated["input_transforms"] = self.transform_provenance(leaf)
            reductions = self._merge_reduction_records(self._reduction_records(value),
                                                       self._reduction_records(leaf))
            if reductions:
                # The input expression may depend on a reduction even when
                # the selected immutable payload and its leaf are unchanged.
                selected_leaf = locals_[node.value_name]
                derived_leaf = self._inherit_value_info(selected_leaf, Value(
                    selected_leaf.type, selected_leaf.value, selected_leaf.frame, selected_leaf.hint))
                self.budget.charge_value(derived_leaf, node.input)
                self._value_reductions[id(derived_leaf)] = (derived_leaf, reductions)
                locals_[node.value_name] = derived_leaf
                generated["input_reductions"] = self.reduction_provenance(derived_leaf)
            filters = self._merge_filter_records(self._filter_records(value),
                                                  self._filter_records(leaf))
            if filters:
                selected_leaf = locals_[node.value_name]
                derived_leaf = self._inherit_value_info(selected_leaf, Value(
                    selected_leaf.type, selected_leaf.value, selected_leaf.frame, selected_leaf.hint))
                self.budget.charge_value(derived_leaf, node.input)
                self._value_filters[id(derived_leaf)] = (derived_leaf, filters)
                locals_[node.value_name] = derived_leaf
                generated["input_filters"] = self.filter_provenance(derived_leaf)
            merges = self._combine_merge_records(self._merge_records(value),
                                                   self._merge_records(leaf))
            if merges:
                selected_leaf = locals_[node.value_name]
                derived_leaf = self._inherit_value_info(selected_leaf, Value(
                    selected_leaf.type, selected_leaf.value, selected_leaf.frame, selected_leaf.hint))
                self.budget.charge_value(derived_leaf, node.input)
                self._value_merges[id(derived_leaf)] = (derived_leaf, merges)
                locals_[node.value_name] = derived_leaf
                generated["input_merges"] = self.merge_provenance(derived_leaf)
            zips = self._combine_zip_records(self._zip_records(value), self._zip_records(leaf))
            if zips:
                selected_leaf = locals_[node.value_name]
                derived_leaf = self._inherit_value_info(selected_leaf, Value(
                    selected_leaf.type, selected_leaf.value, selected_leaf.frame, selected_leaf.hint))
                self.budget.charge_value(derived_leaf, node.input)
                self._value_zips[id(derived_leaf)] = (derived_leaf, zips)
                locals_[node.value_name] = derived_leaf
                generated["input_zips"] = self.zip_provenance(derived_leaf)
            rekeys = self._combine_rekey_records(self._rekey_records(value), self._rekey_records(leaf))
            if rekeys:
                selected_leaf = locals_[node.value_name]
                derived_leaf = self._inherit_value_info(selected_leaf, Value(
                    selected_leaf.type, selected_leaf.value, selected_leaf.frame, selected_leaf.hint))
                self.budget.charge_value(derived_leaf, node.input)
                self._value_rekeys[id(derived_leaf)] = (derived_leaf, rekeys)
                locals_[node.value_name] = derived_leaf
                generated["input_rekeys"] = self.rekey_provenance(derived_leaf)
            self._register_tree(node, child_path, owner, collection["entry_ids"][key], child_context,
                                forwarded, steps=collection["path_steps"] + (PathStep("key", key, node.start, node.end),),
                                depth=collection["ownership_depth"] + 1, generated=generated,
                                declaration_id=collection["definition_id"])
        self._collection_state[path] = "done"

    @staticmethod
    def _assignment_shape(node, required):
        """Seal at most eight native field routes without evaluating values."""
        from .syntax import Node
        from .syntax02 import PathStep
        if (type(node) is not Node or type(node.data) is not dict or type(node.kind) is not str
                or "assignments" in node.__dict__
                or type(required) is not set or not 1 <= len(required) <= 8
                or any(type(name) is not str or len(name) > 128 for name in required)):
            return None
        assignments = node.data.get("assignments")
        if type(assignments) is not list or not 1 <= len(assignments) <= 8:
            return None
        rows, owners = [], [node, node.data, assignments]
        for assignment in assignments:
            if (type(assignment) is not Node or type(assignment.data) is not dict
                    or "path" in assignment.__dict__):
                return None
            path = assignment.data.get("path")
            if type(path) not in (tuple, list) or len(path) != 1:
                return None
            step = path[0]
            if (type(step) is not PathStep or type(step.kind) is not str
                    or type(step.value) is not str or len(step.value) > 128):
                return None
            rows.append((id(assignment), id(assignment.data), id(path), id(step), step.kind, step.value))
            owners.extend((assignment, assignment.data, path, step))
        return ((id(node), id(node.data), node.kind, id(assignments), tuple(sorted(required)), tuple(rows)),
                tuple(owners))

    def assignments(self, node: Any, required: set[str]) -> dict[str, Any]:
        # Sealed routing can avoid repeated path normalization, duplicate-name
        # checks and required-field set construction. Each occurrence still
        # evaluates every original expression in its own lexical context.
        shape = self._assignment_shape(node, required) if self.reach_work is not None else None
        cached = self._assignment_syntax.get(id(node)) if shape is not None else None
        if cached is not None and cached[0] == shape[0]:
            # This is the first ordinary assignment checkpoint, at its original
            # source span. Retain its live iterator before invoking the caller:
            # if a callback changes routing, the original validation resumes
            # with this already-charged first row and its actual iterator.
            remaining = iter(node.assignments)
            first = next(remaining)
            self.budget.tick(first)
            current = self._assignment_shape(node, required)
            if current is not None and current[0] == cached[0]:
                return dict(cached[1])
            self._assignment_syntax.pop(id(node), None)
            return self._assignment_fields(node, required, remaining, first=first)
        result = self._assignment_fields(node, required, iter(node.assignments))
        if shape is not None and len(self._assignment_syntax) < 64:
            current = self._assignment_shape(node, required)
            if current is not None and current[0] == shape[0]:
                # Keep original owners alive so an object-id cannot be reused
                # as an unrelated warm source route. Expressions are not read.
                self._assignment_syntax[id(node)] = shape[0], tuple(result.items()), shape[1]
        return result

    def _assignment_fields(self, node, required, remaining, *, first=None):
        def rows():
            if first is not None:
                yield first, True
            for assignment in remaining:
                yield assignment, False

        result = {}
        for assignment, charged in rows():
            if not charged:
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
            if not isinstance(recipe, dict) or recipe.get("kind") not in ("loft", "placed", "extrusion", "holes", "ring_loft", "framed_loft", "pockets"):
                continue
            surface = recipe.get("surface", recipe)
            location = Node("span", surface["start"], surface["end"],
                            source_id=surface["source_id"])
            try:
                if (surface["kind"] == "framed_loft"
                        and surface.get("owner_frame") != path + ".frame"):
                    raise SurfaceError("OKL-E-FRAMED-LOFT-FRAME",
                        "Framed sections must reference the consuming carrier's self.frame.",
                        details={"frame": surface.get("owner_frame"), "owner": path})
                if self.reach_work is None:
                    mesh, local_pose = materialize_surface(
                        recipe, max_vertices=remaining_vertices,
                        check=lambda: self.budget.tick(location))
                else:
                    mesh, local_pose = _materialize_reach_surface(
                        recipe, max_vertices=remaining_vertices, work=self.reach_work,
                        check=lambda: self.budget.tick(location))
                if self.model.profile in TEXTURE_PROFILES:
                    texture_coordinates(recipe, mesh, charge=lambda n: self.budget.tick(location, amount=n),
                                        check=lambda: self.budget.tick(location))
            except SurfaceError as error:
                if self.model.profile in TEXTURE_PROFILES and (
                        error is self.budget.callback_error or
                        error is getattr(getattr(self.budget, "execution_budget", None), "callback_error", None)):
                    raise
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

    def impulse_values(self, event: Any, context: Context) -> tuple[Value, Value, Value]:
        """Check pure source operands under their actual declaring profile."""
        if self.linked.modules[event.source_id].ast.profile not in IMPULSE_PROFILES:
            raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "Source impulses require impulse-0.1.",
                               event, phase="support", category="unsupported", rule_ids=["IMP-001"])

        def require(value: Value, type_: Type, node: Any) -> Value:
            # Coercion is pure; attaching this rule cannot reinterpret a
            # cancellation raised while the operand itself was evaluated.
            try:
                return self.expect(value, type_, node)
            except OntoKinError as error:
                if error is not self.budget.callback_error:
                    error.diagnostic.rule_ids = [*(error.diagnostic.rule_ids or []), "IMP-001"]
                raise

        target = require(self.path_value(event.path, context, event), Type("Ref", name="Object"), event)
        vector = require(self.expression(event.vector, context),
                         Type("Vector3", element=quantity_type(IMPULSE_DIMENSION)), event.vector)
        point = require(self.expression(event.point, context),
                        Type("Point3", element=quantity_type(LENGTH)), event.point)
        if vector.frame is not None and vector.frame != "world":
            raise OntoKinError("OKL-E-FRAME", "An impulse vector must be expressed in world.",
                               event.vector, phase="type", rule_ids=["IMP-001"],
                               details={"expected_frame": "world", "actual_frame": vector.frame})
        if target.known and point.frame is not None and point.frame != target.value + ".frame":
            raise OntoKinError("OKL-E-FRAME", "An impulse point must use the resolved target object's own frame.",
                               event.point, phase="type", rule_ids=["IMP-001"],
                               details={"expected_frame": target.value + ".frame", "actual_frame": point.frame})
        return target, vector, point

    def event_blocks(self) -> None:
        seen = set()
        force_keys = set()
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
            for sequence_index, event in enumerate(node.events):
                self.budget.tick(event)
                if event.kind == "release":
                    target = self.expect(self.path_value(event.path, Context(scene=True), event), Type("JointRef"), event)
                    events.append(Event("release", target.value, event))
                elif event.kind == "impulse":
                    target, vector, point = self.impulse_values(event, Context(scene=True))
                    source = self.source_for(event)
                    payload = ImpulsePayload(
                        tuple(component.value for component in vector.value),
                        tuple(component.value for component in point.value), sequence_index,
                        {"source_id": event.source_id, "source_revision": source.revision,
                         "start_byte": event.start, "end_byte": event.end})
                    events.append(Event("impulse", target.value, event, payload))
                elif event.kind == "force":
                    from .force_source import lower_force
                    if event.key in force_keys:
                        fail("OKL-E-NAME", "A force key is reused in the scene.", event, phase="binding")
                    force_keys.add(event.key)
                    target, payload = lower_force(self, event, sequence_index)
                    events.append(Event("force", target, event, force=payload))
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
                    **({"input_transforms": generated["input_transforms"]}
                       if "input_transforms" in generated else {}),
                    **({"input_reductions": generated["input_reductions"]}
                       if "input_reductions" in generated else {}),
                    **({"input_filters": generated["input_filters"]}
                       if "input_filters" in generated else {}),
                    **({"input_merges": generated["input_merges"]}
                       if "input_merges" in generated else {}),
                    **({"input_zips": generated["input_zips"]}
                       if "input_zips" in generated else {}),
                    **({"input_rekeys": generated["input_rekeys"]}
                       if "input_rekeys" in generated else {}),
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
        if self.model.profile in REACH_PROFILES:
            from .reach_source import bind_reaches
            bind_reaches(self)
        self.event_blocks()
        requires = tuple(self.linked.capabilities)
        self.model.requested_capabilities = tuple(node.value for node in requires)
        if requires and self.level != "represented":
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "Required capabilities are not supplied by " + self.model.profile + ": " +
                 ", ".join(self.model.requested_capabilities), requires[0], phase="support")
        if self.level == "delivered":
            target = ("ontokin.glb/0.20" if self.model.profile == STRING_CONCAT_PROFILE else "ontokin.glb/0.19" if self.model.profile == KEYED_REKEY_PROFILE else "ontokin.glb/0.18" if self.model.profile == KEYED_ZIP_PROFILE else "ontokin.glb/0.17" if self.model.profile == KEYED_MERGE_PROFILE else "ontokin.glb/0.16" if self.model.profile == KEYED_FILTER_PROFILE else "ontokin.glb/0.15" if self.model.profile == KEYED_REDUCTION_PROFILE else
                       "ontokin.glb/0.14" if self.model.profile == KEYED_TRANSFORM_PROFILE else
                      "ontokin.glb/0.13" if self.model.profile == TEXTURE_PROFILE else
                      "ontokin.glb/0.12" if self.model.profile == POCKETS_PROFILE else
                      "ontokin.glb/0.11" if self.model.profile == FRAMED_LOFT_PROFILE else
                      "ontokin.glb/0.10" if self.model.profile == RING_LOFT_PROFILE else
                                                   "ontokin.glb/0.9" if self.model.profile == HOLES_PROFILE else
                      "ontokin.glb/0.8" if self.model.profile == EXTRUSION_PROFILE else
                      "ontokin.glb/0.7" if self.model.profile == BUDGET_PROFILE else
                      "ontokin.glb/0.6" if self.model.profile == REACH_PROFILE else
                      "ontokin.glb/0.5" if self.model.profile == FORCE_PROFILE else
                      "ontokin.glb/0.4" if self.model.profile == IMPULSE_PROFILE else
                      "ontokin.glb/0.3" if self.model.profile == "surface-0.1" else "ontokin.glb/0.2")
            fail("OKL-E-CAPABILITY-UNSUPPORTED", "Delivery requires the explicit " + target + " target.", self.program, phase="support")
        self._attach_provenance()
        self.budget.tick(self.program)
        return self.model

    def action_value(self, path: str) -> Value:
        value = super().action_value(path)
        if self.model.profile in REACH_PROFILES:
            from .reach_source import bind_description
            bind_description(self, path, value)
        return value

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
                         check: Check[[], None] | None = None, execution_budget=None) -> ConstructionCompiler:
    """Compile a sealed bundle; timeline validation remains an explicit step.

    No filesystem/network effects occur. Cancellation/deadline exceptions from
    ``check`` propagate unchanged. Invalid/source/support failures use registered
    OntoKin diagnostics with original source nodes and stable known identities.
    """
    from .linker import link_program
    if execution_budget is not None:
        if getattr(execution_budget, "admitted_entry_revision", None) != bundle.entry.revision:
            fail("OKL-E-RESOURCE", "The execution context was not admitted for this entry revision.",
                 phase="support", details={"budget_reason": "execution_context_required"})
    budget = (ConstructionBudget(budgets, check) if execution_budget is None else
              ExecutionConstructionBudget(budgets, check, execution_budget=execution_budget))
    budget.tick()
    linked = link_program(bundle, check=budget.tick)
    if (linked.entry.ast.profile in EXECUTION_PROFILES) != (execution_budget is not None):
        fail("OKL-E-RESOURCE", "This source profile requires its explicitly admitted execution context.",
             linked.entry.ast, phase="support", details={"budget_reason": "execution_context_required"})
    compiler = ConstructionCompiler(linked, level, budget)
    try:
        if linked.entry.ast.profile in TEXTURE_PROFILES or isinstance(bundle, TextureBundle):
            validate_texture_closure(compiler)
        compiler.run()
        return compiler
    except OntoKinError as error:
        if error is budget.callback_error or (execution_budget is not None
                and error is execution_budget.callback_error):
            raise
        compiler.annotate(error)
        raise
    except RecursionError as error:
        if error is budget.callback_error or (execution_budget is not None
                and error is execution_budget.callback_error):
            raise
        fail("OKL-E-RESOURCE", "Construction exceeded bounded host recursion work.", compiler.program,
             phase="support", details={"budget": "host_recursion", "profile": compiler.budget.profile})
