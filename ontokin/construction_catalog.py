"""Discovery for versioned construction/surface module interfaces.

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
_SURFACE_PROFILE = "surface-0.1"
_SURFACE_SPEC = "docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md"
_SURFACE_AGENT = "docs/engineering/OK-AGENT-003-native-surface-program-workflows.md"
_SURFACE_FIXTURE = "docs/language-design/surface-v0.1/"
_IMPULSE_PROFILE = "impulse-0.1"
_IMPULSE_SPEC = "docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md"
_IMPULSE_AGENT = "docs/engineering/OK-AGENT-004-source-impulse-program-workflows.md"
_IMPULSE_FIXTURE = "docs/language-design/impulse-v0.1/"
_LEVELS = ["represented", "constructed", "evaluated"]
_MAX_MATERIALIZED_ENTRIES = 100_000
_MAX_PREVIEW_BYTES = 1024
_LEAVES = ["Int", "Real", "Bool", "String", "Quantity[unit] and aliases",
           "Vec3<Q>", "Vector3<Q>", "Range<Q>", "FrameRef", "Point3",
           "Rotation", "Pose", "Color"]


def _entry(kind: str, name: str, signature: str, description: str, *,
           capability: str, domains=(), effects=("pure definition-time description",),
           defaults=None, examples=(), rules=(), available=True,
           profile: str = _PROFILE, **extra) -> dict:
    return {
        "id": f"{profile}/{kind}/{name}", "kind": kind, "name": name,
        "profile": profile, "capability": capability,
        "signature": signature, "description": description,
        "domains": list(domains), "effects": list(effects),
        "defaults": {} if defaults is None else defaults,
        "examples": list(examples), "language_rules": list(rules),
        "available_levels": list(_LEVELS) if available else [],
        "availability": "available_in_bounded_profile" if available else "unsupported",
        "specification": {_SURFACE_PROFILE: _SURFACE_SPEC, _IMPULSE_PROFILE: _IMPULSE_SPEC}.get(profile, _SPEC), **extra,
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


def _surface_global() -> dict:
    """Derive the explicit 0.3 view without rewriting any 0.2 catalog bytes."""
    result = copy.deepcopy(_GLOBAL)
    previous_examples = result["complete_examples"]
    items = []
    for item in result["items"]:
        # The old combined omission no longer describes the regional PBR
        # capability. Its still-unimplemented texture half is named below.
        if item["name"] == "textures_and_regional_materials":
            continue
        item["inherited_from"] = item["id"]
        item["id"] = item["id"].replace(_PROFILE + "/", _SURFACE_PROFILE + "/", 1)
        item["profile"] = _SURFACE_PROFILE
        if item["kind"] == "destination":
            item.update(
                id=f"{_SURFACE_PROFILE}/destination/ontokin.glb/0.3",
                name="ontokin.glb/0.3", capability="ontokin.glb/0.3",
                signature="destination: ontokin.glb/0.3",
                description="Native loft triangles, regional glTF PBR materials and baked rigid world motion with complete program/source provenance.",
                specification=_SURFACE_SPEC, examples=[_SURFACE_FIXTURE + "02-studio.ok"],
                domains=[
                    "Authoring entry remains surface-0.1; imported definitions keep their declared profiles",
                    "One logical mesh per surface occurrence; one primitive and distinct material identity per used source region",
                    "Local visual placement is baked once into carrier-local positions and normals",
                    "Native palette RGBA/metallic/roughness are authoritative; Object.appearance is retained metadata for lofts",
                    "Earlier primitive geometry retains its existing Color material conversion",
                    "Binary64 local geometry becomes float32; local position tolerance is min(requested tolerance, 1e-5 m)",
                    "Full authored timeline preflight; finite sampled motion checks are not a continuous-time proof",
                    "Source recipes, active physics and source editing cannot be reconstructed from GLB",
                ],
            )
        elif item["kind"] == "protocol":
            item.update(
                id=f"{_SURFACE_PROFILE}/protocol/ontokin.agent/0.3",
                name="ontokin.agent/0.3",
                signature='ProgramAgentService(store, protocol="ontokin.agent/0.3"); agent --protocol ontokin.agent/0.3',
                description="Explicit native program binding with atomic source repairs, retained runs/artifacts, bounded surface inspection and separate durable state.",
                specification=_SURFACE_AGENT,
                domains=[
                    "surface-0.1 entry and ontokin.glb/0.3 destination; exact immutable ontokin.bundle/0.1 source bytes",
                    "Default Python binding stays Agent/0.2 and default CLI stays Agent/0.1",
                    "Separate surface-program-agent.sqlite3; ontokin.surface-program-agent-store/0.1; no automatic migration",
                    "Previously accepted immutable revisions remain readable; never-accepted candidates cannot page, evaluate or export ordinarily",
                    "Source patches retain authorized source_id, source_revision, occurrence and UTF-8 span preconditions",
                    "Native diagnostics reuse ontokin.diagnostic/0.2 with actual source-unit locations",
                    "Discovery requires validation before any achieved stage is claimed",
                ],
                store_filename="surface-program-agent.sqlite3",
                store_schema="ontokin.surface-program-agent-store/0.1",
                diagnostic_contract="ontokin.diagnostic/0.2",
            )
        elif item["name"] == "persistent_agent_editing_service":
            item["description"] = "Local surface-program-agent.sqlite3 store; atomic whole-program acceptance, per-source patches, retained requests/runs/artifacts and no silent migration of earlier protocols."
            item["specification"] = _SURFACE_AGENT
        elif item["name"] == "general_external_delivery":
            item["description"] = "Only the explicit ontokin.glb/0.3 native baked asset contract; arbitrary destinations and engine-side live simulation remain unsupported."
        elif item["name"] == "Geometry" and item["kind"] == "type":
            item["description"] = "Immutable empty/sphere/box or native loft description; a loft permits one carrier-local placed pose."
            item["domains"] += ["Visual geometry adds no physical body or motion authority", "No arbitrary triangle-buffer constructor"]
            item["specification"] = _SURFACE_SPEC
        elif item["name"] == "Keyed" and item["kind"] == "type":
            item["element_types"] += ["LoftSection", "SurfaceMaterial"]
            item["domains"] += ["LoftSection and SurfaceMaterial are additional immutable leaves only in surface-0.1 declarations"]
            item["specification"] = _SURFACE_SPEC
        elif item["name"] == "appearance" and item["kind"] == "capability":
            item["description"] = "Linear RGBA for primitives and explicit per-region linear RGBA/metallic/roughness for native lofts; no textures or material animation."
            item["specification"] = _SURFACE_SPEC
        elif item["name"] == "Object.appearance":
            item["domains"] += ["Native loft rendering uses its SurfaceMaterial palette; this Color remains retained metadata on a loft"]
        elif item["name"] == "Object.physical":
            item["domains"] += ["A loft contributes no mass or inertia; an explicitly authored supported sphere proxy remains independent"]
        elif item["name"] == "import":
            item["domains"] += ["A surface-0.1 entry may import compatible construction-0.1 components; each module keeps its own version, profile and type rules"]
        items.append(item)

    def native(kind, name, signature, description, **kwargs):
        return _entry(kind, name, signature, description, profile=_SURFACE_PROFILE, **kwargs)

    items.extend([
        native("type", "LoftSection", "LoftSection",
               "Immutable section station, planar center, two radii and authored region key.",
               capability="native_loft_surfaces", domains=[
                   "Flat Keyed leaf, parameter, let value or pure callable input/result",
                   "No mutable members, nested Keyed, equality or derived vertex identity",
               ], examples=['loft_section(0[m], vec3(0[m], 0[m], 0[m]), 0.5[m], 0.35[m], "clay")'],
               rules=["CON-006"]),
        native("type", "SurfaceMaterial", "SurfaceMaterial",
               "Immutable linear RGBA, metallic and roughness material value; its palette key supplies region identity.",
               capability="regional_pbr_materials", domains=[
                   "All six numeric components finite and within [0,1]",
                   "Flat Keyed leaf; no physical matter, texture, emissive or normal-map value",
               ], examples=['surface_material(rgba(0.6, 0.3, 0.2, 1), 0, 0.8)'],
               rules=["CON-006"]),
        native("builtin", "loft_section",
               "loft_section(station: Length, center: Vec3<Length>, radius_x: Length, radius_y: Length, region: String) -> LoftSection",
               "Describe one elliptical ring around the fixed local +Z axis.",
               capability="native_loft_surfaces", domains=[
                   "Station and center X/Y are finite in [-100,100] m; center Z is exactly zero",
                   "Both radii are finite in [0.001,100] m",
                   "Region resolves to the loft palette; section key comes from its enclosing Keyed value",
                   "Closed positional arguments; no source mesh-buffer injection",
               ], examples=['loft_section(0[m], vec3(0[m], 0[m], 0[m]), 0.5[m], 0.35[m], "clay")'],
               result_type="LoftSection"),
        native("builtin", "surface_material",
               "surface_material(base_color: Color, metallic: Real, roughness: Real) -> SurfaceMaterial",
               "Describe the actual glTF PBR factors assigned to a stable authored region.",
               capability="regional_pbr_materials", domains=[
                   "Linear RGBA Color and both factors are finite in [0,1]",
                   "No texture, UV, emissive, normal-map, clearcoat or runtime material animation overload",
               ], examples=['surface_material(rgba(0.6, 0.3, 0.2, 1), 0, 0.8)'],
               result_type="SurfaceMaterial"),
        native("builtin", "loft",
               "loft(sections: Keyed<LoftSection>, materials: Keyed<SurfaceMaterial>, facets: Int, caps: String) -> Geometry",
               "Construct a bounded rigid exterior from authored elliptical sections and regional materials.",
               capability="native_loft_surfaces", domains=[
                   "2..64 sections, 1..16 palette keys; facets 8..64 divisible by four",
                   "Caps must be the string literal flat or none; no computed cap-mode expression",
                   "Sort sections by numeric station, independent of entry/key order; equal stations reject",
                   "Minimum ideal station gap 0.001 m uses the exact binary64 coordinate allowance in OK-LANG-003-C1",
                   "Lower-station region owns each side interval; first and last regions own flat end caps",
                   "Unused palette entries remain inspectable without empty delivery primitives",
                   "Flat outward triangle normals and separate corners; no welded-index manifold guarantee",
                   "Open ends make no solid-volume claim; polygonal ellipses are an approximation",
               ], examples=['loft(self.rings, self.palette, 16, "flat")'],
               result_type="Geometry", rules=["LANG-024"],
               numeric_clarification=_SURFACE_FIXTURE + "clarification-c1.md"),
        native("builtin", "placed", "placed(surface: Geometry, placement: Pose) -> Geometry",
               "Apply one rigid local visual transform to a native loft in its carrier's own frame.",
               capability="rigid_visual_placement", domains=[
                   "The geometry argument is an unplaced native loft; primitives and nested placed calls reject",
                   "Pose references the carrier object's self.frame, including an independently generated part",
                   "World and sibling frames reject; no scale, reflection or shear",
                   "Translation changes vertices; rotation changes vertices and normals exactly once",
                   "Adds no object, follows relation, joint, mass or action authority",
               ], examples=['placed(loft(self.rings, self.palette, 16, "flat"), pose(self.frame, vec3(0[m], 0[m], 0.1[m]), quat(1, 0, 0, 0)))'],
               result_type="Geometry", rules=["LANG-024"]),
        native("projection", "geometry.surface", "inspect(..., fields=[\"geometry\"]) -> geometry.surface",
               "Bounded occurrence summary with source section/palette keys, stations, counts, used regions and local placement.",
               capability="surface_mesh_inspection", domains=[
                   "ontokin.surface-summary/0.1 at result.items[i].geometry.surface for native loft/placed geometry",
                   "All palette keys include valid unused entries; used region counts describe actual triangles",
                   "No positions, normals or triangle-index arrays in ordinary geometry inspection",
                   "Primitive objects retain their earlier projection; a class or collection has no occurrence mesh",
               ], specification=_SURFACE_AGENT, summary_contract="ontokin.surface-summary/0.1",
               physical_participation="none", motion_authority="carrier_evaluated_world_pose"),
        native("operation", "surface.mesh_page",
               "surface.mesh_page(program_revision, element_id, count, region?, cursor?, budgets?)",
               "Read complete native triangles from one explicitly named previously accepted occurrence revision.",
               capability="surface_mesh_inspection", domains=[
                   "count is an integer JSON token 1..256 measured in triangles, with at most 768 flat corners",
                   "Exact occurrence identity; never-accepted candidates, definitions and display-path aliases are not mesh targets",
                   "region is an optional nonempty palette key; explicit null rejects; a known unused region gives an empty complete page",
                   "Positions and normals are carrier-local after one visual placement; no world time or run is selected",
                   "Page-local triangle indices retain complete-mesh native ordinals before regional grouping",
                   "Opaque cursor binds project, operation, revision, occurrence, profile, region, geometry fingerprint, coordinates, ordering, implementation and protocol",
                   "A continuation can change count and lower budgets with a new request ID; changed immutable context rejects",
                   "count above max_result_items fails; cancellation and work/output exhaustion cannot return successful partial data",
                   "Source edits target authorized UTF-8 spans, never a derived vertex or triangle",
               ], specification=_SURFACE_AGENT, result_schema="ontokin.surface-mesh-page/0.1",
               coordinate_system="carrier_local_after_placement/0.1",
               ordering="native_triangle_ordinal/0.1", count_unit="triangles",
               max_count=256, max_page_vertices=768, available_levels=["constructed"],
               effects=["read immutable constructed geometry; no accepted-head or run advancement"]),
    ])
    for name, description in {
        "native_loft_surfaces": "Bounded native .ok section-to-triangle construction with numeric station ordering and flat outward normals.",
        "regional_pbr_materials": "Actual triangle groups and linear RGBA/metallic/roughness per stable palette region, including distinct equal-valued material identities.",
        "rigid_visual_placement": "One carrier-local placement drives visible geometry under the existing evaluated object pose and rigid animation.",
        "surface_mesh_inspection": "Revision-bound summaries and bounded triangle pages; inherited authorized source repair keeps the pinned bundle authoritative.",
    }.items():
        items.append(native("capability", name, name, description, capability=name,
                            effects=["profile feature; validate and measure the actual program before claiming success"]))
    for name, description in {
        "textures_and_uv_coordinates": "No UVs, image textures, tangents, normal maps or displacement maps; native regional scalar PBR remains available.",
        "advanced_or_animated_materials": "No emissive/clearcoat/transmission extensions or runtime material animation; the native constructor is linear RGBA, metallic and roughness only.",
        "smooth_or_freeform_surfaces": "No smooth normals, subdivision, NURBS, branches within one loft or arbitrary authored triangle buffers.",
        "automatic_surface_physics": "No mesh-derived mass, inertia, collision or contact; separately authored existing sphere proxies retain their mechanical limits.",
    }.items():
        items.append(native("capability", name, name, description, capability=name, available=False,
                            effects=["unsupported behavior must remain explicit"]))
    result.update(
        schema_version="ontokin.agent-catalog/0.3", profile=_SURFACE_PROFILE, language_version="0.3",
        agent_contract="ontokin.agent/0.3", delivery_targets=["ontokin.glb/0.3"], items=items,
        source_header='ontokin "0.3"; module Example @ "example"; profile "surface-0.1";',
        compatible_definition_profiles=["construction-0.1", "surface-0.1"],
        complete_examples=[_SURFACE_FIXTURE + "02-studio.ok"],
        example_bundles=[{"entry": _SURFACE_FIXTURE + "02-studio.ok", "dependencies": [{
            "path": _SURFACE_FIXTURE + "01-surface-parts.ok", "package_id": "fixture.surface-parts", "version": "1.0.0",
            "source_revision": "sha256:87fed50bdcb9b6274ec87981cc67028463c10b1cdce301060416c69586b428ce"}]}],
        construction_examples={"language_version": "0.2", "paths": previous_examples},
        example_context="Native snippets require a 0.3/surface-0.1 declaring module and their shown self/value bindings. Studio requires the exact accompanying pinned SurfaceParts dependency. Inherited examples retain their original 0.1/0.2 source context; discovery executes none of them.",
        unavailable_capabilities=sorted(item["name"] for item in items
                                        if item["kind"] == "capability" and item["availability"] == "unsupported"),
    )
    result["limits"].update(
        min_surface_sections=2, max_surface_sections=64, min_surface_palette_keys=1, max_surface_palette_keys=16,
        min_surface_facets=8, max_surface_facets=64, surface_facets_multiple=4,
        max_surface_coordinate_abs_m=100, min_surface_radius_m=.001, max_surface_radius_m=100,
        min_surface_station_separation_m=.001, max_surface_triangles_per_loft=8192,
        max_surface_vertices_per_loft=24576, max_aggregate_mesh_vertices=250000,
        max_glb_bytes=64 * 1024 * 1024, max_surface_page_triangles=256, max_surface_page_vertices=768,
    )
    result["numeric_limitations"] += [
        "Station separation uses only the coordinate representation allowance specified by OK-LANG-003-C1.",
        "Polygonal elliptical rings and flat normals approximate curved geometry; no universal smooth-surface or volume-error bound is claimed.",
        "Local mesh pages use finite binary64; native GLB uses checked float32 positions/normals and reports its quantization loss.",
    ]
    return result


def _impulse_global() -> dict:
    """Add the adopted source impulse contract without altering older catalogs."""
    from .program_bindings import PROFILE_BINDINGS
    binding = PROFILE_BINDINGS[_IMPULSE_PROFILE]
    result = copy.deepcopy(_SURFACE_GLOBAL)
    previous_examples = result["complete_examples"]
    for item in result["items"]:
        item["inherited_from"] = item["id"]
        item["id"] = item["id"].replace(_SURFACE_PROFILE + "/", _IMPULSE_PROFILE + "/", 1)
        item["profile"] = _IMPULSE_PROFILE
        if item["kind"] == "destination":
            item.update(id=f"{_IMPULSE_PROFILE}/destination/{binding.destination}", name=binding.destination,
                        capability=binding.destination, signature="destination: " + binding.destination,
                        description="Native source geometry and regional PBR with recorded rigid motion from authored sphere impulses.",
                        specification=_IMPULSE_SPEC,
                        examples=[_IMPULSE_FIXTURE + "p02-off-center-mixed-imports.files.json"],
                        domains=[
                            "Explicit impulse-0.1 entry and ontokin.glb/0.4 destination",
                            "Inherits native loft/PBR/placement/source identity and quantization limits of GLB/0.3",
                            "Every exact source impulse boundary is retained; pose is continuous while derivatives may jump",
                            "Complete impulse_states_after metadata per object is checked against source-evaluated boundaries",
                            "Conservative whole-scene spin bound includes every authored norm(point)*norm(impulse)/inertia",
                            "Recorded playback supplies no destination-side impulse engine or live physics",
                            "Valid evaluated binary64 states may exceed bounded float32 GLB delivery",
                        ])
        elif item["kind"] == "protocol":
            item.update(id=f"{_IMPULSE_PROFILE}/protocol/{binding.protocol}", name=binding.protocol,
                        signature='ProgramAgentService(store, protocol="ontokin.agent/0.4"); agent --protocol ontokin.agent/0.4',
                        description="Explicit source impulse program binding with inherited atomic edits, bounded inspection and isolated durable state.",
                        specification=_IMPULSE_AGENT, store_filename=binding.store_filename,
                        store_schema=binding.store_schema, diagnostic_contract="ontokin.diagnostic/0.2",
                        domains=[
                            "impulse-0.1 entry; exact immutable ontokin.bundle/0.1 closure; explicit GLB/0.4 delivery",
                            "Default Python binding remains Agent/0.2; default CLI remains Agent/0.1",
                            "Separate impulse-program-agent.sqlite3; no request-driven protocol selection or store migration",
                            "All Agent/0.3 operations retained; there is no apply_impulse, impulse or state-replacement host RPC",
                            "Create or patch source, evaluate a revision-bound run, and inspect its exact before/after state",
                            "Only previously accepted snapshots permit ordinary evaluate/export/mesh access",
                            "The complete final successful response obeys the selected lowered value-entry budget before effects commit",
                        ])
        elif item["name"] == "persistent_agent_editing_service":
            item["description"] = "Isolated impulse-program-agent.sqlite3 with atomic whole-program acceptance, exact source patches, retained requests/runs/artifacts and no migration of older stores."
            item["specification"] = _IMPULSE_AGENT
        elif item["name"] == "general_external_delivery":
            item["description"] = "Only explicit GLB/0.4 recorded impulse-profile delivery; arbitrary engines and live simulation remain unsupported."
        elif item["name"] == "external_forces_and_actuators":
            item["description"] = "Finite force intervals, continuous torques, motors, wind and controllers remain unsupported. The separate source_impulses capability supplies only authored instantaneous sphere momentum changes."
        elif item["kind"] == "constant" and item["name"] == "dynamic":
            item["description"] = "Free homogeneous sphere under uniform gravity and explicit authored instantaneous impulses; no contact or connected load solution."
            item["specification"] = _IMPULSE_SPEC
        elif item["name"] == "import":
            item["domains"] += ["An impulse-0.1 declaring module may import compatible 0.2/0.3/0.4 definitions; older modules cannot import a 0.4 dependency"]
        elif item["name"] == "Keyed" and item["kind"] == "type":
            item["domains"] += ["impulse-0.1 inherits the native surface leaves; imported 0.2 declarations retain their earlier type restrictions"]
        elif item["name"] in ("surface.mesh_page", "geometry.surface"):
            item["domains"] += ["Nested geometry/page profile remains surface-0.1; the Agent/0.4 envelope and source closure identify the impulse entry"]
            if item["name"] == "surface.mesh_page":
                item["domains"] += ["The signed cursor additionally binds private entry_profile=impulse-0.1; the public page shape and geometry fingerprint are unchanged"]

    def impulse(kind, name, signature, description, **kwargs):
        return _entry(kind, name, signature, description, profile=_IMPULSE_PROFILE, **kwargs)

    result["items"].extend([
        impulse("event", "impulse", "impulse object_path using Vector3<Quantity[N*s]> at Point3;",
                "Apply one elaborated world impulse at a point in the resolved target's own frame, inside an exact-time sequence.",
                capability="source_impulses", rules=["IMP-001", "IMP-002", "IMP-003"],
                domains=[
                    "Contextual event spelling only in language 0.4 / impulse-0.1; payload expressions are pure elaboration-time values",
                    "Target is an actual Ref<Object> occurrence; impulse uses world axes and point uses exactly that object's frame",
                    "Currently free dynamic homogeneous sphere with positive finite own mass, radius and inertia",
                    "The application point may be inside, on or outside the physical sphere; no contact or visible-mesh condition is implied",
                    "Position/orientation stay continuous; velocity changes by J/m and omega by (R*point cross J)/I",
                    "Release then impulse uses the transferred incoming state; impulse before release rejects",
                    "Written-order statements stage atomically; a later failure rolls back all current-boundary changes and records",
                    "Exactly zero impulse still validates/counts/records but preserves the existing trajectory anchor",
                    "Exposed lever, world point, angular impulse and final velocities must remain finite",
                ], effects=["authored instantaneous momentum update to one staged free sphere; no action handle or persistent channel"],
                examples=['at 1[s] sequence { impulse ball using vector(world, 0[N*s], 2[N*s], 0[N*s]) at point(ball.frame, 0.5[m], 0[m], 0[m]);']),
        impulse("projection", "state.impulses", 'inspect(..., fields=["state"]) -> state.impulses',
                "Bounded cumulative count and complete latest impulse-bearing boundary records for this object.",
                capability="bounded_impulse_state", rules=["IMP-004", "IMP-005"], specification=_IMPULSE_AGENT,
                state_schema="https://ontokin.org/schemas/impulse-v0.1/impulses.schema.json",
                domains=[
                    "Initially applied_count=0, last_application_time_seconds=null, last_applications=[] for every object",
                    "All applications at that object's latest impulse boundary, in statement order; unrelated boundaries and objects retain prior records",
                    "Exact source/unit/UTF-8 spans and resolved occurrence identity accompany nine explicit world/self vectors",
                    "World/self impulse fields are not re-expressed when ordinary top-level inspection uses another frame",
                    "Existing exact-time before/after inspection recovers earlier states; no unbounded history log or new host operation",
                    "Complete nested records count toward work, output, value-entry and encoded-envelope bounds; no successful truncation",
                ], effects=["read revision/run-bound evaluated influence state"]),
        impulse("projection", "state.pose_authority", 'inspect(..., fields=["state"]) -> state.pose_authority',
                "Distinguish when an object became a free sphere from its current analytic trajectory anchor.",
                capability="bounded_impulse_state", rules=["IMP-004"],
                domains=["free_sphere.since_seconds remains zero or release time",
                         "trajectory_anchor_seconds records the latest release or nonzero impulse; zero J preserves it"],
                effects=["read existing pose authority; impulses add no second authority"]),
        impulse("capability", "source_impulses", "source_impulses",
                "Instantaneous source-authored linear and angular momentum updates on free homogeneous spheres.",
                capability="source_impulses", rules=["IMP-001", "IMP-002", "IMP-003"],
                effects=["bounded profile capability; validate and evaluate the actual source program"]),
        impulse("capability", "bounded_impulse_state", "bounded_impulse_state",
                "Exact source-bound latest-boundary influence inspection with inherited atomic repair and run semantics.",
                capability="bounded_impulse_state", rules=["IMP-004", "IMP-005"],
                effects=["read supported evaluated influence state"]),
    ])
    result.update(schema_version="ontokin.agent-catalog/0.4", profile=_IMPULSE_PROFILE, language_version="0.4",
                  agent_contract=binding.protocol, delivery_targets=[binding.destination],
                  source_header='ontokin "0.4"; module Example @ "example"; profile "impulse-0.1";',
                  compatible_definition_profiles=["construction-0.1", "surface-0.1", "impulse-0.1"],
                  complete_examples=[_IMPULSE_FIXTURE + "sources/p02-off-center-mixed-imports.ok"],
                  example_file_manifests=[_IMPULSE_FIXTURE + "p02-off-center-mixed-imports.files.json"],
                  example_bundles=[{"entry": _IMPULSE_FIXTURE + "sources/p02-off-center-mixed-imports.ok", "dependencies": [
                      {"path": _IMPULSE_FIXTURE + "libraries/02-impulse-parts04.ok", "package_id": "fixture.impulse-parts", "version": "1.0.0", "source_revision": "sha256:bc122164d828386ec970f8cf183ff22d57dcc90180fe84c574de84c575fc78d6"},
                      {"path": _IMPULSE_FIXTURE + "libraries/01-surface-parts03.ok", "package_id": "fixture.surface-parts", "version": "1.0.0", "source_revision": "sha256:87fed50bdcb9b6274ec87981cc67028463c10b1cdce301060416c69586b428ce"},
                      {"path": _IMPULSE_FIXTURE + "libraries/00-impulse-vectors02.ok", "package_id": "fixture.impulse-vectors", "version": "1.0.0", "source_revision": "sha256:0ca5a18550cd8832d9c0e388e69f4295b3a0f9b64b8a8c08cf171faa7e75f26c"}]}],
                  surface_examples={"language_version": "0.3", "paths": previous_examples},
                  example_context="Impulse snippets need a 0.4/impulse-0.1 entry, a free sphere occurrence and the shown value/frame bindings. The complete example uses its exact pinned file manifest. Inherited source examples retain their declared contexts; discovery executes none of them.")
    result["unavailable_capabilities"] = sorted(item["name"] for item in result["items"]
        if item["kind"] == "capability" and item["availability"] == "unsupported")
    result["numeric_limitations"] += [
        "Each final impulse velocity component is one rounded rational sum over canonical operands; exposed intermediate vectors must be finite.",
        "Source type arithmetic retains its Angle tag; angular momentum divided by inertia is an explicit mechanical conversion to radians/second.",
        "Impulses add no arbitrary minimum body mass/radius and no finite-force, torque, contact or general-body solver.",
    ]
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


def _public_interfaces(linked, budget: _Budget, *, source_profiles: bool = False):
    """Yield records from actual symbols, without evaluating source defaults."""
    revision = linked.bundle.program_revision
    for source_id, module in sorted(linked.modules.items()):
        budget.step()
        unit = module.unit
        profile = module.ast.profile if source_profiles else _PROFILE
        source_context = {"profile": profile, "language_version": module.ast.version} if source_profiles else {}
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
            **source_context,
        )
        module_record["id"] = _identity_id(module.module_identity, profile=profile)
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
                **source_context,
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
            entry["id"] = _identity_id(symbol.element_id, profile=profile)
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
                entry["id"] = _identity_id(identity, profile=profile)
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


def _identity_id(identity, *, profile: str = _PROFILE) -> str:
    return profile + "/declaration/" + json.dumps(list(identity), ensure_ascii=False, separators=(",", ":"))


def _revision(value: dict, budget: _Budget) -> str:
    digest = hashlib.sha256()
    encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    for chunk in encoder.iterencode(value):
        budget.step()
        digest.update(chunk.encode("utf-8"))
    return "sha256:" + digest.hexdigest()


_GLOBAL = _global()
_SURFACE_GLOBAL = _surface_global()
_IMPULSE_GLOBAL = _impulse_global()
from .force_catalog import force_catalog as _force_catalog
_FORCE_PROFILE = "force-0.1"
_FORCE_GLOBAL = _force_catalog(_IMPULSE_GLOBAL)
_PROFILE_GLOBALS = {_PROFILE: _GLOBAL, _SURFACE_PROFILE: _SURFACE_GLOBAL, _IMPULSE_PROFILE: _IMPULSE_GLOBAL,
                    _FORCE_PROFILE: _FORCE_GLOBAL}


def catalog(*, linked_program: LinkedProgram | None = None,
            check: Callable[[], Any] | None = None, profile: str = _PROFILE) -> dict:
    """Return fresh content-pinned metadata, optionally from actual linked units.

    Filtering/pagination and the transmitted envelope cap belong to the agent
    binding. Extraction counts bounded logical entries and forwards cooperative
    work/cancellation checks before producing large derived interface records.
    """
    budget = _Budget(check)
    budget.step()
    if not isinstance(profile, str) or profile not in _PROFILE_GLOBALS:
        raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "Unsupported program discovery profile.",
                           category="unsupported", phase="inspection", blocks=[],
                           details={"profile": profile, "available_profiles": list(_PROFILE_GLOBALS)})
    result = copy.deepcopy(_PROFILE_GLOBALS[profile])
    budget.charge(result)
    if linked_program is not None:
        from .linker import LinkedProgram
        if not isinstance(linked_program, LinkedProgram):
            raise TypeError("linked_program must come from link_program(bundle).")
        if profile in (_SURFACE_PROFILE, _IMPULSE_PROFILE, _FORCE_PROFILE) and linked_program.entry.ast.profile != profile:
            message = ("Surface discovery requires a surface-0.1 entry." if profile == _SURFACE_PROFILE
                       else "This discovery binding requires a " + profile + " entry.")
            raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", message,
                               linked_program.entry.ast, category="unsupported", phase="inspection", blocks=[],
                               details={"required_profile": profile, "actual_profile": linked_program.entry.ast.profile})
        context = {
            "program_revision": linked_program.bundle.program_revision,
            "state": "linked declarations, not constructed or evaluated",
            "source_manifest": linked_program.bundle.manifest(),
            "nominal_identity_excludes": ["version", "digest", "filename", "import alias"],
        }
        budget.charge(context)
        result["program_context"] = context
        for entry, node in _public_interfaces(linked_program, budget, source_profiles=profile in (_SURFACE_PROFILE, _IMPULSE_PROFILE, _FORCE_PROFILE)):
            budget.charge(entry, node)
            result["items"].append(entry)
    result["revision"] = _revision(result, budget)
    return result
