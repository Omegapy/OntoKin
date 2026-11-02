"""Offline exact-pin module linking, separate from physical construction.

The linker creates real lexical namespaces and package-qualified nominal
definition identities. It retains each original AST and source span; it never
concatenates source text or changes a definition's identity to an import alias.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .bundle import (DIGEST_RE, BundleError, ProgramBundle, SourceUnit,
                     package_source_id, validate_package_id, validate_version)
from .diagnostics import OntoKinError, Source
from .syntax import MAX_TOKENS, Node
from .syntax02 import parse_source_unit
from .profile_capabilities import BUDGET_PROFILE, EXTRUSION_PROFILE, HOLES_PROFILE, RING_LOFT_PROFILE, FRAMED_LOFT_PROFILE, POCKETS_PROFILE, TEXTURE_PROFILE, KEYED_TRANSFORM_PROFILE, KEYED_REDUCTION_PROFILE, KEYED_FILTER_PROFILE, KEYED_MERGE_PROFILE, KEYED_ZIP_PROFILE, KEYED_REKEY_PROFILE, STRING_CONCAT_PROFILE, KEYED_REKEY_PROFILES, KEYED_ZIP_PROFILES, KEYED_MERGE_PROFILES, KEYED_FILTER_PROFILES, KEYED_REDUCTION_PROFILES, KEYED_TRANSFORM_PROFILES, TEXTURE_PROFILES, POCKETS_PROFILES, FRAMED_LOFT_PROFILES, RING_LOFT_PROFILES, HOLES_PROFILES, EXTRUSION_PROFILES, EXECUTION_PROFILES, REACH_PROFILES, FORCE_PROFILES, IMPULSE_PROFILES
from .validator import KEY_RE, PREDEFINED


MAX_IMPORT_DEPTH = 8
PREDEFINED_02 = PREDEFINED | {"Keyed", "len"}
DefinitionId = tuple[str, ...]


def _error(code: str, message: str, node: Any = None, *, rule: str = "CON-004",
           related: list[Any] | None = None, **details: Any) -> None:
    raise OntoKinError(code, message, node, phase="binding", rule_ids=[rule],
                       related=related or [], details=details,
                       category="resource_limit" if code == "OKL-E-RESOURCE" else "invalid")


@dataclass(frozen=True)
class DefinitionSymbol:
    element_id: DefinitionId
    source_id: str
    node: Node
    kind: str
    name: str
    key: str
    visibility: str


@dataclass
class LinkedModule:
    unit: SourceUnit
    ast: Node
    module_identity: DefinitionId
    imports: dict[str, str] = field(default_factory=dict)
    symbols: dict[str, DefinitionSymbol] = field(default_factory=dict)


@dataclass
class LinkedProgram:
    bundle: ProgramBundle
    entry: LinkedModule
    modules: dict[str, LinkedModule]
    definitions: dict[DefinitionId, DefinitionSymbol]
    source_registry: dict[str, Source]
    dependency_order: tuple[str, ...]

    @property
    def program_revision(self) -> str:
        return self.bundle.program_revision

    @property
    def capabilities(self) -> tuple[Node, ...]:
        """Whole-closure requirements, retaining their declaring source spans."""
        return tuple(node for module in self.modules.values() for node in module.ast.requires)

    def resolve_definition(self, source_id: str, name: str | tuple[str, ...], *,
                           kind: str | None = None, node: Any = None) -> DefinitionSymbol:
        module = self.modules.get(source_id)
        if module is None:
            _error("OKL-E-NAME", "The requested lexical source namespace is not in this program.",
                   node, rule="CON-003", source_id=source_id)
        location = node if node is not None else module.ast
        if isinstance(name, str):
            parts = tuple(name.split("."))
        elif isinstance(name, tuple) and all(isinstance(part, str) for part in name):
            parts = name
        else:
            _error("OKL-E-NAME", "A qualified definition name must contain identifier segments.",
                   location, rule="CON-003")
        if len(parts) == 1:
            symbol = module.symbols.get(parts[0])
        elif len(parts) == 2:
            target = module.imports.get(parts[0])
            if target is None:
                _error("OKL-E-NAME", "The name does not identify an imported namespace.",
                       location, rule="CON-003", alias=parts[0])
            symbol = self.modules[target].symbols.get(parts[1])
            if symbol is not None and symbol.visibility != "public":
                _error("OKL-E-ACCESS", "An imported private definition is not accessible through this alias.",
                       location, rule="CON-003", related=[symbol.node],
                       definition_id=list(symbol.element_id))
        else:
            _error("OKL-E-NAME", "A definition name is local or qualified by one import alias.",
                   location, rule="CON-003")
        if symbol is None:
            _error("OKL-E-NAME", "The definition is not declared in the selected lexical namespace.",
                   location, rule="CON-003", name=".".join(parts))
        if kind is not None and symbol.kind != kind:
            _error("OKL-E-TYPE", f"This use requires a {kind} definition.", location,
                   rule="CON-003", related=[symbol.node], actual_kind=symbol.kind)
        return symbol


def _module_identity(unit: SourceUnit, ast: Node) -> DefinitionId:
    if unit.source_id == "entry":
        return ("entry", ast.module_key)
    return ("package", unit.package_id, ast.module_key)


def _bindings(module: LinkedModule, check: Callable[[], None]) -> None:
    ast = module.ast
    if KEY_RE.fullmatch(ast.module_key) is None:
        _error("OKL-E-ID", "The module key is outside the stable-key grammar.", ast, rule="CON-003")
    names: dict[str, Node] = {}
    keys: dict[str, Node] = {}
    for node in [*ast.imports, *ast.definitions]:
        check()
        if KEY_RE.fullmatch(node.key) is None:
            _error("OKL-E-ID", "A module declaration key is outside the stable-key grammar.", node,
                   rule="CON-003")
        predefined = PREDEFINED_02
        if module.ast.profile in REACH_PROFILES:
            from .reach_source import NAMES
            predefined = predefined | NAMES
        if module.ast.profile in TEXTURE_PROFILES:
            from .texture_runtime import TEXTURE_CALLS, TEXTURE_TYPES
            predefined = predefined | TEXTURE_CALLS | TEXTURE_TYPES
        if module.ast.profile in KEYED_TRANSFORM_PROFILES:
            predefined = predefined | {"map_keyed"}
        if module.ast.profile in KEYED_REDUCTION_PROFILES:
            predefined = predefined | {"reduce_keyed"}
        if module.ast.profile in KEYED_FILTER_PROFILES:
            predefined = predefined | {"filter_keyed"}
        if module.ast.profile in KEYED_MERGE_PROFILES:
            predefined = predefined | {"merge_keyed"}
        if module.ast.profile in KEYED_ZIP_PROFILES:
            predefined = predefined | {"zip_keyed"}
        if module.ast.profile in KEYED_REKEY_PROFILES:
            predefined = predefined | {"rekey_keyed"}
        if node.name in predefined or node.name in names:
            _error("OKL-E-NAME", "An import or definition name is predefined or duplicated in this module.",
                   node, rule="CON-003", related=[names[node.name]] if node.name in names else [],
                   name=node.name)
        if node.key in keys:
            _error("OKL-E-ID", "A stable declaration key is reused in this module namespace.", node,
                   rule="CON-003", related=[keys[node.key]], key=node.key)
        names[node.name] = node
        keys[node.key] = node
        if node.kind != "import":
            ids = module.module_identity + ("definitions", node.key)
            module.symbols[node.name] = DefinitionSymbol(ids, module.unit.source_id, node,
                                                         node.kind, node.name, node.key, node.visibility)


def _import_target(node: Node) -> str:
    try:
        validate_package_id(node.package_id)
    except BundleError:
        _error("OKL-E-NAME", "An import package ID is outside the package identifier grammar.",
               node.package_node)
    try:
        validate_version(node.version)
    except BundleError:
        _error("OKL-E-REVISION", "An import version must be an exact supported major.minor.patch label.",
               node.version_node, reason="invalid_import_version")
    if DIGEST_RE.fullmatch(node.digest) is None:
        _error("OKL-E-REVISION", "An import digest must be sha256: followed by 64 lowercase hexadecimal digits.",
               node.digest_node, reason="invalid_import_digest")
    return package_source_id(node.package_id, node.version)


def link_program(bundle: ProgramBundle, *, check: Callable[[], None] | None = None) -> LinkedProgram:
    """Bind every supplied module and require one exact closed, acyclic program.

    Declared graph cycles are checked before digest comparisons. A source hash
    cycle would otherwise require a cryptographic fixed point to expose its
    cycle diagnostic. The cycle test therefore needs only valid-shaped pins;
    no content is accepted before every actual digest is subsequently checked.
    """
    if not isinstance(bundle, ProgramBundle):
        raise TypeError("link_program requires an immutable ProgramBundle")
    modules: dict[str, LinkedModule] = {}
    total_tokens = 0

    def checkpoint() -> None:
        if check is not None:
            check()

    for unit in bundle.units:
        checkpoint()
        ast = parse_source_unit(unit, check=checkpoint if check is not None else None)
        total_tokens += ast.token_count
        if total_tokens > MAX_TOKENS:
            _error("OKL-E-RESOURCE", "The complete source bundle exceeds its token budget.", ast,
                   rule="CON-012", limit=MAX_TOKENS, consumed=total_tokens)
        if unit.source_id == "entry" and ast.scene is None:
            _error("OKL-E-SYNTAX", "The entry source must declare exactly one scene.", ast)
        if unit.source_id != "entry" and ast.scene is not None:
            _error("OKL-E-TYPE", "An imported definition module cannot declare a scene.", ast.scene)
        module = LinkedModule(unit, ast, _module_identity(unit, ast))
        _bindings(module, checkpoint)
        modules[unit.source_id] = module

    # Multiple versions have unambiguous source IDs and a valid candidate hash,
    # but cannot be accepted as one construction-0.1 nominal package namespace.
    package_units: dict[str, SourceUnit] = {}
    for unit in bundle.modules:
        checkpoint()
        previous = package_units.get(unit.package_id)
        if previous is not None:
            imported = [node for module in modules.values() for node in module.ast.imports
                        if node.package_id == unit.package_id and node.version == unit.version]
            location = imported[0].version_node if imported else modules[unit.source_id].ast
            _error("OKL-E-REVISION", "A valid program supplies only one exact version of each package ID.",
                   location, related=[modules[previous.source_id].ast],
                   reason="conflicting_package_versions", package_id=unit.package_id,
                   versions=[previous.version, unit.version])
        package_units[unit.package_id] = unit

    edges: dict[str, list[tuple[str, Node]]] = {source_id: [] for source_id in modules}
    for source_id, module in modules.items():
        for node in module.ast.imports:
            checkpoint()
            target = _import_target(node)
            if target not in modules:
                _error("OKL-E-NAME", "The explicitly imported package version is not supplied in this bundle.",
                       node, rule="CON-002", reason="missing_dependency", source_id=target)
            if (modules[target].ast.profile == STRING_CONCAT_PROFILE
                    and module.ast.profile != STRING_CONCAT_PROFILE):
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.20 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if (modules[target].ast.profile == KEYED_REKEY_PROFILE
                    and module.ast.profile not in KEYED_REKEY_PROFILES):
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.19 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if (modules[target].ast.profile == KEYED_ZIP_PROFILE
                    and module.ast.profile not in KEYED_ZIP_PROFILES):
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.18 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if (modules[target].ast.profile == KEYED_MERGE_PROFILE
                    and module.ast.profile not in KEYED_MERGE_PROFILES):
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.17 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if (modules[target].ast.profile == KEYED_FILTER_PROFILE
                    and module.ast.profile not in KEYED_FILTER_PROFILES):
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.16 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if (modules[target].ast.profile == KEYED_REDUCTION_PROFILE
                    and module.ast.profile not in KEYED_REDUCTION_PROFILES):
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.15 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if (modules[target].ast.profile == KEYED_TRANSFORM_PROFILE
                    and module.ast.profile not in KEYED_TRANSFORM_PROFILES):
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.14 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == TEXTURE_PROFILE and module.ast.profile not in TEXTURE_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.13 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == POCKETS_PROFILE and module.ast.profile not in POCKETS_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.12 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == FRAMED_LOFT_PROFILE and module.ast.profile not in FRAMED_LOFT_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.11 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == RING_LOFT_PROFILE and module.ast.profile not in RING_LOFT_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.10 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == HOLES_PROFILE and module.ast.profile not in HOLES_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.9 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == EXTRUSION_PROFILE and module.ast.profile not in EXTRUSION_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.8 dependency.",
                                   node, phase="support", category="unsupported",
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == BUDGET_PROFILE and module.ast.profile not in EXECUTION_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An earlier declaring module cannot import a source 0.7 dependency.",
                                   node, phase="support", category="unsupported", rule_ids=["REA-001"],
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == "planar-reach-0.1" and module.ast.profile not in REACH_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An older declaring module cannot import a planar-reach-0.1 dependency.",
                                   node, phase="support", category="unsupported", rule_ids=["REA-001"],
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == "force-0.1" and module.ast.profile not in FORCE_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An older declaring module cannot import a force-0.1 dependency.",
                                   node, phase="support", category="unsupported", rule_ids=["FOR-001"],
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            if modules[target].ast.profile == "impulse-0.1" and module.ast.profile not in IMPULSE_PROFILES:
                raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                                   "An older declaring module cannot import an impulse-0.1 dependency.",
                                   node, phase="support", category="unsupported", rule_ids=["IMP-001"],
                                   details={"declaring_profile": module.ast.profile,
                                            "dependency_profile": modules[target].ast.profile,
                                            "dependency_source_id": target})
            module.imports[node.name] = target
            edges[source_id].append((target, node))

    states: dict[str, str] = {}
    active: list[str] = []
    active_edges: list[Node] = []
    order: list[str] = []
    heights: dict[str, int] = {}

    def visit(source_id: str) -> None:
        checkpoint()
        if states.get(source_id) == "finished":
            return
        states[source_id] = "active"
        active.append(source_id)
        height = 0
        for target, node in edges[source_id]:
            checkpoint()
            if states.get(target) == "active":
                offset = active.index(target)
                _error("OKL-E-DEPENDENCY-CYCLE", "The declared import graph contains a cycle.", node,
                       related=active_edges[offset:], reason="import_cycle",
                       cycle=active[offset:] + [target])
            active_edges.append(node)
            visit(target)
            active_edges.pop()
            height = max(height, 1 + heights[target])
        active.pop()
        states[source_id] = "finished"
        heights[source_id] = height
        order.append(source_id)

    for source_id in modules:
        visit(source_id)

    if heights["entry"] > MAX_IMPORT_DEPTH:
        current = "entry"
        path = [current]
        locations = []
        while edges[current]:
            target, location = max(edges[current], key=lambda edge: heights[edge[0]])
            path.append(target)
            locations.append(location)
            current = target
        _error("OKL-E-RESOURCE", "The entry's declared import chain exceeds the dependency depth limit.",
               locations[MAX_IMPORT_DEPTH], rule="CON-012", related=locations[:MAX_IMPORT_DEPTH],
               limit=MAX_IMPORT_DEPTH, consumed=heights["entry"], dependency_chain=path)

    for source_id, module in modules.items():
        for target, node in edges[source_id]:
            checkpoint()
            actual = modules[target].unit.revision
            if node.digest != actual:
                _error("OKL-E-REVISION", "The supplied dependency bytes do not match the source import's exact digest.",
                       node.digest_node, related=[modules[target].ast], reason="pin_mismatch",
                       expected=node.digest, actual=actual, source_id=target)

    reachable: set[str] = set()
    pending = ["entry"]
    while pending:
        checkpoint()
        source_id = pending.pop()
        if source_id in reachable:
            continue
        reachable.add(source_id)
        pending.extend(target for target, _ in edges[source_id])
    unused = sorted(set(modules) - reachable)
    if unused:
        _error("OKL-E-NAME", "Every supplied dependency must be in the entry's declared reachable closure.",
               modules[unused[0]].ast, reason="unreachable_dependency", source_ids=unused)

    definitions: dict[DefinitionId, DefinitionSymbol] = {}
    for module in modules.values():
        for symbol in module.symbols.values():
            checkpoint()
            if symbol.element_id in definitions:
                _error("OKL-E-ID", "Two definitions claim the same nominal package/module/key identity.",
                       symbol.node, rule="CON-003", related=[definitions[symbol.element_id].node],
                       definition_id=list(symbol.element_id))
            definitions[symbol.element_id] = symbol
    checkpoint()
    return LinkedProgram(bundle, modules["entry"], modules, definitions,
                         bundle.source_registry, tuple(order))
