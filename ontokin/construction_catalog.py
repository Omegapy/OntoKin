"""Discovery for construction-0.1 and public, revision-bound module interfaces.

The core catalog is copied, never modified. Linked interface records describe
authored declarations; linking and discovery do not certify construction or
evaluation. Default expressions are source previews, not computed values.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import TYPE_CHECKING, Any, Callable

from .agent_catalog import catalog as core_catalog
from .bundle import MAX_FILENAME_BYTES, MAX_MODULES, MAX_SOURCE_BYTES
from .diagnostics import OntoKinError

if TYPE_CHECKING:
    from .linker import LinkedProgram


_PROFILE = "construction-0.1"
_SPEC = "docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md"
_FIXTURE = "docs/language-design/construction-v0.1/01-keyed-rack/"
_LEVELS = ["represented", "constructed", "evaluated"]
_MAX_MATERIALIZED_ENTRIES = 100_000
_MAX_PREVIEW_BYTES = 1024
_LEAVES = ["Int", "Real", "Bool", "String", "Quantity[unit] and aliases",
           "Vec3<Q>", "Vector3<Q>", "Range<Q>", "FrameRef", "Point3",
           "Rotation", "Pose", "Color"]


def _entry(kind: str, name: str, signature: str, description: str, *,
           capability: str, domains=(), effects=("pure definition-time description",),
           defaults=None, examples=(), rules=(), available=True, **extra) -> dict:
    return {
        "id": f"{_PROFILE}/{kind}/{name}", "kind": kind, "name": name,
        "profile": _PROFILE, "capability": capability,
        "signature": signature, "description": description,
        "domains": list(domains), "effects": list(effects),
        "defaults": {} if defaults is None else defaults,
        "examples": list(examples), "language_rules": list(rules),
        "available_levels": list(_LEVELS) if available else [],
        "availability": "available_in_bounded_profile" if available else "unsupported",
        "specification": _SPEC, **extra,
    }


def _global() -> dict:
    result = core_catalog()
    result.pop("revision")
    previous_examples = result.pop("complete_examples")
    items = []
    destination = None
    for item in result["items"]:
        if item["kind"] == "destination":
            destination = item
            continue
        if item["name"] == "modules_packages_and_procedural_generators":
            continue
        item["inherited_from"] = item["id"]
        item["id"] = item["id"].replace("core-0.1/", _PROFILE + "/", 1)
        item["profile"] = _PROFILE
        if item["name"] == "persistent_agent_editing_service":
            item["description"] = (
                "Local program-agent.sqlite3 store; atomic whole-program acceptance, "
                "per-source patches, retained requests/runs/artifacts, and no silent 0.1 migration."
            )
            item["specification"] = _SPEC
            item["language_rules"] += ["CON-013"]
        if item["name"] == "general_external_delivery":
            item["description"] = "Only the explicit ontokin.glb/0.2 bundle-aware baked asset contract."
        items.append(item)

    items.extend([
        _entry("type", "Keyed", "Keyed<T>",
               "Flat immutable keyed values with a declared element type and stable ASCII keys.",
               capability="keyed_values", domains=[
                   "At most 256 entries; keys match [A-Za-z0-9][A-Za-z0-9._-]{0,63}",
                   "Duplicate keys are invalid; empty literals still declare T",
                   "Only the published immutable leaf types; no nested Keyed",
                   "Invariant whole-value typing; entry conversions follow the existing type rules",
                   "No equality, ordering, arithmetic, mutation, or implicit covariance",
               ], examples=['keyed<Length>{"left": 0.2[m], "right": 0.3[m]}'],
               rules=["CON-006"], element_types=_LEAVES,
               iteration_order="ASCII key order, independent of literal order"),
        _entry("builtin", "len", "len(Keyed<T>) -> Int",
               "Read the entry count of a flat keyed value or intrinsic generated reference view.",
               capability="keyed_values", domains=[
                   "No String or general-sequence overload",
                   "Reading a generated view is forbidden in a shape dependency closure",
               ], examples=['len(keyed<Length>{"left": 0.2[m], "right": 0.3[m]})'],
               rules=["CON-006", "CON-007"], result_type="Int"),
        _entry("member", "Keyed.index", "value[key: String] -> T",
               "Read an existing entry by key; no insertion or default member is implied.",
               capability="keyed_values", domains=["Missing keys fail explicitly", "Read-only access"],
               examples=['keyed<Length>{"left": 0.2[m]}["left"]'],
               rules=["CON-006"], result_type="T", writable=False),
        _entry("view", "generated_parts", "Keyed<Ref<C>> (intrinsic read-only view)",
               "A generated collection groups independently identified owned parts without adding an Object.",
               capability="keyed_assembly_construction", domains=[
                   "Not an authored literal, parameter, return, or let annotation",
                   "No additional ownership edge, frame, body, mass, or implicit following",
                   "Occurrence identity is owner identity + collection key + input key",
               ], examples=['first.fingers["middle"]'], rules=["CON-007", "CON-008", "CON-010"],
               writable=False),
        _entry("syntax", "import", 'import alias @ "key" from "package.id" version "1.0.0" digest "sha256:...";',
               "Resolve one exact version and source digest from the supplied offline bundle.",
               capability="pinned_definition_modules", domains=[
                   "Entry has one scene; dependencies have no scenes",
                   "One exact pin per package ID in a valid dependency DAG",
                   "Supplied packages must equal the reachable closure; no unused packages",
                   "Aliases expose public definitions and do not change nominal identity",
                   "Source loading performs no host code, network access, or scene initialization",
               ], examples=[_FIXTURE + "main.ok", _FIXTURE + "program.bundle.json"],
               rules=["CON-002", "CON-003", "CON-004", "CON-005"]),
        _entry("syntax", "qualified_name", "alias.Class | alias.function(...) | Ref<alias.Class>",
               "Resolve a public definition through an import alias in the caller's declaring source module.",
               capability="pinned_definition_modules", domains=[
                   "Imported bodies keep their own declaring module and lexical scope",
                   "No wildcard imports, implicit re-export, or private-name access",
               ], examples=["mech.Finger", "mech.three_mounts(0.6[m])"], rules=["CON-003"]),
        _entry("syntax", "parts", 'public parts fingers @ "fingers": mech.Finger for (key, offset) in self.mounts { ... }',
               "Create one independent homogeneous part per final input key at definition time.",
               capability="keyed_assembly_construction", domains=[
                   "Distinct immutable key/value binders; self is the enclosing owner in the body",
                   "Resolve final outer overrides before shape and child initialization",
                   "The generated child's own final immutable inputs may govern its nested shape",
                   "A generated view or another generated occurrence cannot be a shape dependency, including through cached values",
                   "Unused branches and empty bodies remain type/access checked without numeric execution",
                   "Static recursive composition is rejected even for an empty input",
               ], examples=[_FIXTURE + "main.ok", _FIXTURE + "hinges.ok"],
               effects=["finite definition-time construction; no runtime allocation or mutation"],
               rules=["CON-007", "CON-008", "CON-009", "CON-010", "CON-012"]),
        _entry("syntax", "per_key_initializer", 'fingers["middle"].length = 0.75[m];',
               "Override one public parameter through public member and literal-key path steps.",
               capability="keyed_assembly_construction", domains=[
                   "Every collection/member/key must resolve and satisfy access rules",
                   "Outer occurrence overrides precede reusable inner initializer assignments",
                   "An absent final key is an error, never an implicit new child or dropped write",
                   "No shared generated declaration span becomes an occurrence-local edit target",
                   "Typed Member/Key steps preserve a key such as left.eye as one key",
               ], examples=['fingers["middle"].length = 0.75[m];'],
               rules=["CON-009", "CON-011", "CON-013"]),
        _entry("format", "ontokin.bundle/0.1", "entry + exact versioned module source descriptors",
               "An immutable program snapshot has its identity before source parsing or import resolution.",
               capability="pinned_definition_modules", domains=[
                   "Each source_revision still hashes one exact UTF-8 source file",
                   "program_revision hashes the domain-separated canonical manifest and all supplied source identities",
                   "Filenames are exact hashed diagnostic labels; no Unicode or line-ending normalization",
                   "A structurally valid rejected candidate keeps its own program revision",
               ], examples=[_FIXTURE + "program.bundle.json", _FIXTURE + "program.files.json"],
               rules=["CON-005"], source_schema="ontokin.bundle/0.1",
               file_transport_schema="ontokin.files/0.1"),
        _entry("protocol", "ontokin.agent/0.2", "ProgramAgentService; agent --protocol ontokin.agent/0.2",
               "Versioned program-level operations retain independent source identities and durable lifecycle context.",
               capability="persistent_agent_editing_service", domains=[
                   "program_revision, accepted_program_revision, expected_program_revision",
                   "Per-source patches include source_id, source_revision, element_id and exact UTF-8 preconditions",
                   "No automatic reinterpretation or migration of an ontokin.agent/0.1 project",
                   "Discovery declarations require validation before an achieved stage is claimed",
               ], rules=["CON-011", "CON-013"]),
    ])
    for name, description in {
        "pinned_definition_modules": "Exact offline module reuse with original lexical scope and source provenance.",
        "keyed_values": "Flat typed immutable inputs; explicit key lookup and canonical iteration.",
        "keyed_assembly_construction": "Finite generated owned parts and public per-key parameter overrides.",
    }.items():
        items.append(_entry("capability", name, name, description, capability=name,
                            rules=["CON-002", "CON-006", "CON-007"],
                            effects=["profile feature; validate the actual program before claiming support"]))
    for name, description in {
        "network_package_resolution": "Only explicitly supplied offline sources; no package installation or ambient lookup.",
        "version_ranges_and_multiple_package_versions": "Exact major.minor.patch and digest; one pin per package in a valid closure.",
        "general_procedural_algorithms": "No general loops, recursive calls, random generators, or arbitrary generator algorithms.",
        "nested_keyed_values": "Only flat Keyed over the published immutable leaf allowlist.",
        "authored_reference_collections": "Keyed<Ref<C>> is an intrinsic generated view, not an authorable collection type.",
        "runtime_collection_mutation": "No keyed mutation or runtime creation/removal of generated objects.",
        "generated_relation_or_event_collections": "Generate parts whose classes contain supported mechanics; no general declaration generator.",
        "automatic_compatible_part_replacement": "Changing a concrete nominal class still requires a new occurrence key and explicit rebinding.",
    }.items():
        items.append(_entry("capability", name, name, description, capability=name, available=False,
                            effects=["unsupported behavior must remain explicit"]))

    assert destination is not None
    destination.update(
        id=f"{_PROFILE}/destination/ontokin.glb/0.2", name="ontokin.glb/0.2",
        profile=_PROFILE, capability="ontokin.glb/0.2", signature="destination: ontokin.glb/0.2",
        description="Primitive GLB and baked world motion with whole-program and per-source provenance.",
        specification=_SPEC, inherited_from="core-0.1/destination/ontokin.glb/0.1",
        examples=[_FIXTURE + "program.files.json"], language_rules=["CON-014"],
    )
    destination["domains"] += ["Authoring profile remains construction-0.1", "Bundle metadata does not reconstruct the editable source recipe"]
    items.append(destination)
    result.update(
        schema_version="ontokin.agent-catalog/0.2", profile=_PROFILE, language_version="0.2",
        agent_contract="ontokin.agent/0.2", items=items, delivery_targets=["ontokin.glb/0.2"],
        complete_examples=[_FIXTURE + "program.files.json", _FIXTURE + "program.bundle.json"],
        baseline_examples={"language_version": "0.1", "paths": previous_examples},
        example_context="Expressions and declarations need their surrounding bindings; inherited core fixture paths retain their 0.1 context. The complete construction manifests identify 0.2 programs. Discovery never executes an example.",
        unavailable_capabilities=sorted(item["name"] for item in items
                                        if item["kind"] == "capability" and item["availability"] == "unsupported"),
        program_context=None,
        interface_scope="Global contract unless a linked program is supplied; public source declarations do not certify a use or evaluated state.",
    )
    result["limits"].update(
        max_source_bytes=MAX_SOURCE_BYTES, max_bundle_source_bytes=MAX_SOURCE_BYTES,
        max_dependency_units=MAX_MODULES, max_import_depth_edges=8, max_bundle_tokens=200_000,
        max_keyed_entries=256, max_ownership_depth_edges=64,
        max_materialized_entries=_MAX_MATERIALIZED_ENTRIES, max_result_bytes=4 * 1024 * 1024,
        max_element_id_segments=256, max_query_path_bytes=32768,
        max_filename_bytes=MAX_FILENAME_BYTES, source_preview_bytes=_MAX_PREVIEW_BYTES,
    )
    return result


class _Budget:
    def __init__(self, check: Callable[[], Any] | None):
        self.check = check
        self.entries = 0

    def step(self) -> None:
        if self.check is not None:
            self.check()

    def charge(self, value: Any, node=None) -> None:
        """Bound each record before appending it; count logically repeated data."""
        pending = [value]
        while pending:
            self.step()
            current = pending.pop()
            self.entries += 1
            if self.entries > _MAX_MATERIALIZED_ENTRIES:
                raise OntoKinError("OKL-E-RESOURCE", "Discovery exceeded its logical materialization budget.",
                                   node, category="resource_limit", phase="inspection",
                                   rule_ids=["CON-011", "CON-012"],
                                   details={"limit": _MAX_MATERIALIZED_ENTRIES}, blocks=[])
            if isinstance(current, dict):
                pending.extend(current.values())
            elif isinstance(current, (list, tuple)):
                pending.extend(current)


def _span(node, unit) -> dict:
    if getattr(node, "source_id", None) != unit.source_id:
        raise ValueError("A linked catalog node must identify its actual source unit.")
    if not 0 <= node.start <= node.end <= len(unit.raw):
        raise ValueError("A linked catalog node has invalid source byte offsets.")
    return {"file": unit.filename, "start_byte": node.start, "end_byte": node.end}


def _authored(node, unit) -> dict:
    span = _span(node, unit)
    size = node.end - node.start
    preview = unit.raw[node.start:min(node.end, node.start + _MAX_PREVIEW_BYTES)]
    # A preview may stop within a multibyte scalar; the complete source/span is
    # retained, and no replacement character or fabricated byte is introduced.
    text = preview.decode("utf-8", errors="ignore")
    return {"text": text, "truncated": len(text.encode("utf-8")) < size,
            "source_bytes": size, "source_span": span}


def _name(value: str | tuple[str, ...] | list[str]) -> str:
    return value if isinstance(value, str) else ".".join(value)


def _public_interfaces(linked, budget: _Budget):
    """Yield records from actual symbols, without evaluating source defaults."""
    revision = linked.bundle.program_revision
    for source_id, module in sorted(linked.modules.items()):
        budget.step()
        unit = module.unit
        imports = []
        for importer_id, importer in sorted(linked.modules.items()):
            for alias, target_id in sorted(importer.imports.items()):
                budget.step()
                if target_id == source_id:
                    path = {"from_source_id": importer_id, "alias": alias}
                    budget.charge(path, module.ast)
                    imports.append(path)
        module_record = _entry(
            "module", module.ast.module_name, f"module {module.ast.module_name}",
            "Declared module interface in this exact linked program.",
            capability="pinned_definition_modules", available=False,
            availability="linked_declaration_requires_validation", language_rules=["CON-003", "CON-011"],
            element_id=list(module.module_identity), nominal_id=list(module.module_identity),
            source_id=source_id, source_revision=unit.revision,
            source_span=_span(module.ast, unit), program_revision=revision,
            package_id=unit.package_id, package_version=unit.version,
            import_paths=imports, validation_required=True,
        )
        module_record["id"] = _identity_id(module.module_identity)
        yield module_record, module.ast
        for symbol in sorted(module.symbols.values(), key=lambda s: s.element_id):
            budget.step()
            if symbol.visibility != "public":
                continue
            node = symbol.node
            common = {
                "element_id": list(symbol.element_id), "nominal_id": list(symbol.element_id),
                "module_identity": list(module.module_identity),
                "source_id": source_id, "source_revision": unit.revision,
                "source_span": _span(node, unit), "program_revision": revision,
                "visibility": "public", "validation_required": True,
                "availability": "linked_declaration_requires_validation",
                "declaration_scope": "declared public interface; effective inherited values require inspection/validation",
            }
            if symbol.kind == "function":
                entry = _callable(node, symbol.name, unit, budget, **common)
            else:
                base = getattr(node, "base", None)
                entry = _entry("class", symbol.name, "class " + symbol.name,
                               "Public nominal class declaration; occurrences still require full validation.",
                               capability="pinned_definition_modules", available=False,
                               rules=["CON-003", "CON-011"], **common)
                entry["base_name"] = None if base is None else _name(base)
                if base is not None and _name(base) != "Object":
                    base_symbol = linked.resolve_definition(source_id, base, kind="class", node=node)
                    entry["base_definition_id"] = list(base_symbol.element_id)
                else:
                    entry["base_definition_id"] = None
            entry["id"] = _identity_id(symbol.element_id)
            yield entry, node
            if symbol.kind != "class":
                continue
            for member in node.members:
                budget.step()
                if getattr(member, "visibility", None) != "public":
                    continue
                identity = (*symbol.element_id, member.key)
                member_common = {
                    **common, "element_id": list(identity), "nominal_id": list(identity),
                    "source_span": _span(member, unit),
                    "owner_definition_id": list(symbol.element_id), "member_kind": member.kind,
                }
                name = symbol.name + "." + member.name
                if member.kind == "method":
                    entry = _callable(member, name, unit, budget, **member_common)
                else:
                    entry = _entry("declared_member", name, name,
                                   "Public authored member; source defaults are not evaluated values.",
                                   capability="pinned_definition_modules", available=False,
                                   rules=["CON-003", "CON-009", "CON-011"], **member_common)
                    if member.kind in {"param", "derive"}:
                        annotation = _authored(member.type, unit)
                        entry.update(type_expression=annotation, value_type=annotation["text"],
                                     default_expression=_authored(member.value, unit),
                                     source_writable=member.kind == "param")
                        entry["signature"] += ": " + annotation["text"]
                        entry["default_expression"]["origin"] = "authored expression; not evaluated"
                    elif member.kind in {"part", "parts"}:
                        class_name = _name(member.class_name)
                        target = linked.resolve_definition(source_id, member.class_name, kind="class", node=member)
                        entry.update(part_class_name=class_name, part_definition_id=list(target.element_id),
                                     value_type=f"Keyed<Ref<{class_name}>>" if member.kind == "parts" else f"Ref<{class_name}>",
                                     source_writable=False)
                        entry["signature"] += ": " + entry["value_type"]
                    else:
                        entry["source_writable"] = False
                entry["id"] = _identity_id(identity)
                yield entry, member


def _callable(node, name: str, unit, budget: _Budget, **common) -> dict:
    parameters = []
    for parameter in node.params:
        budget.step()
        annotation = _authored(parameter.type, unit)
        record = {"name": parameter.name, "type_expression": annotation,
                  "source_span": _span(parameter, unit)}
        budget.charge(record, parameter)
        parameters.append(record)
    result_type = _authored(node.return_type, unit)
    signature = name + "(" + ", ".join(p["name"] + ": " + p["type_expression"]["text"] for p in parameters)
    signature += ") -> " + result_type["text"]
    return _entry(node.kind, name, signature,
                  "Public pure callable declaration; positional inputs and return type come from its defining source.",
                  capability="pinned_definition_modules", available=False,
                  effects=["pure call; an Action result is only a description until an event starts it"],
                  rules=["LANG-010", "CON-003", "CON-011"], parameters=parameters,
                  return_type_expression=result_type, result_type=result_type["text"], **common)


def _identity_id(identity) -> str:
    return _PROFILE + "/declaration/" + json.dumps(list(identity), ensure_ascii=False, separators=(",", ":"))


def _revision(value: dict, budget: _Budget) -> str:
    digest = hashlib.sha256()
    encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    for chunk in encoder.iterencode(value):
        budget.step()
        digest.update(chunk.encode("utf-8"))
    return "sha256:" + digest.hexdigest()


_GLOBAL = _global()


def catalog(*, linked_program: LinkedProgram | None = None,
            check: Callable[[], Any] | None = None) -> dict:
    """Return fresh content-pinned metadata, optionally from actual linked units.

    Filtering/pagination and the transmitted envelope cap belong to the agent
    binding. Extraction counts bounded logical entries and forwards cooperative
    work/cancellation checks before producing large derived interface records.
    """
    budget = _Budget(check)
    budget.step()
    result = copy.deepcopy(_GLOBAL)
    budget.charge(result)
    if linked_program is not None:
        from .linker import LinkedProgram
        if not isinstance(linked_program, LinkedProgram):
            raise TypeError("linked_program must come from link_program(bundle).")
        context = {
            "program_revision": linked_program.bundle.program_revision,
            "state": "linked declarations, not constructed or evaluated",
            "source_manifest": linked_program.bundle.manifest(),
            "nominal_identity_excludes": ["version", "digest", "filename", "import alias"],
        }
        budget.charge(context)
        result["program_context"] = context
        for entry, node in _public_interfaces(linked_program, budget):
            budget.charge(entry, node)
            result["items"].append(entry)
    result["revision"] = _revision(result, budget)
    return result
