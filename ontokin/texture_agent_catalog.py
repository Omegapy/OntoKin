"""Fresh bounded discovery of pinned PNG assets and planar surface mapping."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .pockets_agent_catalog import catalog as pockets_catalog
from .pockets_agent_catalog import interface as pockets_interface
from .profile_capabilities import TEXTURE_PROFILE
from .texture_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION


ADOPTION = "docs/language-design/textured-surfaces-v0.1/ADOPTION.md"
EXAMPLES = ["examples/textured-surfaces/rgb-panel.files.json",
            "examples/textured-surfaces/warning-panel.files.json",
            "examples/textured-surfaces/marked-tray.files.json"]


def interface(policy=None, *, aggregate_limits=None):
    result = pockets_interface(policy, aggregate_limits=aggregate_limits)
    result.pop("single_source_command", None)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.13", profile=TEXTURE_PROFILE,
        delivery_contract=DEFINITION.destination, storage_schema=DEFINITION.store_schema,
        store_filename=DEFINITION.store_filename,
        transport="TextureAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.13",
        request_schema="docs/language-design/agent-v0.13/request.schema.json",
        response_schema="docs/language-design/agent-v0.13/response.schema.json",
        source_schema="ontokin.bundle/0.2", file_transport_schema="ontokin.files/0.2",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.13 --output MODEL.glb",
        adoption=ADOPTION, max_request_bytes=MAX_REQUEST_BYTES,
        source_constructors=[*result["source_constructors"], "png_asset", "planar_uv",
                             "texture_binding", "texture_surface"],
        asset_limits={"max_assets": 4, "max_png_bytes": 300000, "max_total_png_bytes": 1200000,
            "max_dimension_pixels": 256, "max_decoded_bytes": 262144,
            "max_total_decoded_bytes": 1048576, "max_idat_chunks": 64,
            "max_asset_changes": 8, "max_asset_slice_bytes": 65536},
        texture_mapping={"uv_sets": 1, "basis_unit": "m^-1", "origin_unit": "m",
            "origin_component_abs_max": 256, "basis_component_abs_max": 1024,
            "offset_abs_max": 1024, "referenced_uv_abs_max": 4096,
            "coordinate_space": "raw unplaced native geometry",
            "arithmetic": "exact rational affine sum followed by one binary64 rounding",
            "orientation": "upper-left PNG origin; V increases down rows",
            "sampler": {"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071},
            "base_color": "sRGB PNG samples decoded to linear then multiplied by linear material RGB",
            "alpha": "fully opaque PNG and textured material factor"},
        asset_inspection={"operation": "inspect", "selector": {"kind": "texture_asset"},
            "one_asset_selector": {"element_id": ["assets", "<asset_id>"]},
            "fields": ["identity", "source"],
            "asset_slice": {"offset": "integer in [0,total_bytes]", "max_bytes": "integer in [1,65536]"},
            "slice_exclusions": ["cursor", "run_id", "time", "frame"],
            "meaning": "Exact retained attachment identity and bytes; metadata does not assert PNG validity"},
        asset_editing={"operations": ["add", "replace", "remove"],
            "preconditions": "Replace/remove require original expected_sha256; one change per ID",
            "atomicity": "One source/module/asset candidate; rejected edits preserve the accepted revision"})
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = pockets_catalog(policy=None)
    old_interface = result.pop("polygon_pockets_interface")
    inherited = result["complete_examples"]
    references = result.setdefault("inherited_geometry_interfaces", [])
    references.append({key: old_interface[key] for key in
        ("language_version", "profile", "agent_contract", "delivery_contract", "adoption")})
    result.update(schema_version="ontokin.agent-catalog/0.13", language_version="0.13",
        profile=TEXTURE_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.13"; module Example @ "example"; profile "textured-surfaces-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], TEXTURE_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_pocket_examples={"language_version": "0.12", "paths": inherited},
        example_context="The .13 file manifests pin source and offline PNG bytes. Earlier examples retain their declared bindings.")
    result["limits"].update(max_texture_assets=4, max_png_bytes=300000, max_total_png_bytes=1200000,
        max_png_dimension=256, max_texture_decoded_bytes=1048576, max_request_bytes=MAX_REQUEST_BYTES)
    def selectors(value):
        if isinstance(value, dict):
            return {key: selectors(item) for key, item in value.items()}
        if isinstance(value, list):
            return [selectors(item) for item in value]
        if isinstance(value, str):
            return (value.replace("ontokin.agent/0.12", SCHEMA_VERSION)
                .replace("ontokin.glb/0.12", DEFINITION.destination)
                .replace("PocketsAgentService", "TextureAgentService")
                .replace("pockets-program-agent.sqlite3", DEFINITION.store_filename)
                .replace("ontokin.pockets-program-agent-store/0.1", DEFINITION.store_schema))
        return value

    for index, item in enumerate(result["items"]):
        if (item["kind"] in ("protocol", "destination")
                or item["name"] == "persistent_agent_editing_service"):
            item = selectors(item)
            result["items"][index] = item
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            item.update(profile=TEXTURE_PROFILE, specification=ADOPTION,
                signature="TextureAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Atomic source and offline image edits with current host authority and durable retries.",
                domains=["Explicit source/Agent/GLB .13 and immutable bundle/files .2",
                    "All twelve operations and unchanged defaults",
                    "Exact source and asset preconditions; failed candidates preserve accepted attachments",
                    "Current host policy and one cumulative request ledger; no stored authority"])
        elif item["kind"] == "destination":
            item.update(profile=TEXTURE_PROFILE, specification=ADOPTION,
                signature=DEFINITION.destination, name=DEFINITION.destination,
                capability=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.13 with checked planar UVs and exact embedded opaque PNG bytes.",
                domains=["Actual binary32 TEXCOORD_0 and exact original image byte identities",
                    "Fixed nearest/clamp sampler and explicit linear base-color multiplication",
                    "Unchanged geometry and recorded motion accessor bytes",
                    "Unreal import and live destination physics remain unverified"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item.update(available=False,
                description="Unchanged legacy bundle transport; Agent/0.13 requires ontokin.bundle/0.2.")
        elif item["name"] == "Keyed" and item["kind"] == "type":
            item["element_types"].append("TextureBinding")
        elif item["name"] == "geometry.surface":
            item.update(profile=TEXTURE_PROFILE, specification=ADOPTION,
                description="Bounded native source recipe and optional region-to-image mapping metadata.",
                domains=[*item["domains"],
                    "Texture metadata retains exact image identities and unplaced affine mappings",
                    "Underlying family summaries, geometry and physical authority retain their meanings"])
        elif item["name"] == "surface.mesh_page":
            item.update(profile=TEXTURE_PROFILE, specification=ADOPTION,
                domains=["Bounded actual triangles and source region identity",
                    "Current image/mapping identity and actual UVs bind the mesh fingerprint and cursor",
                    "No PNG byte array is copied into each surface page"])
    domains = ["Assets are opaque offline PNGs selected by stable ID and exact complete-byte SHA256",
        "Declared closure includes every .13 builtin image declaration in reachable source",
        "One affine map per existing native material region, evaluated before rigid placement",
        "No new mass, collision, normal or motion authority"]
    entries = [
        ("type", "TextureImage", "TextureImage", "An immutable literal asset ID and byte digest."),
        ("type", "PlanarUV", "PlanarUV", "An exact affine mapping in unplaced recipe coordinates."),
        ("type", "TextureBinding", "TextureBinding", "One image and one planar mapping for a material-region key."),
        ("builtin", "png_asset", "png_asset(id: literal String, sha256: literal String) -> TextureImage",
         "Declare and reference one exact offline PNG attachment."),
        ("builtin", "planar_uv", "planar_uv(origin: Vec3<Length>, u: Vec3<Quantity[m^-1]>, v: Vec3<Quantity[m^-1]>, u_offset: Real, v_offset: Real) -> PlanarUV",
         "Define independent inverse-length rows, a local origin and explicit offsets."),
        ("builtin", "texture_binding", "texture_binding(image: TextureImage, mapping: PlanarUV) -> TextureBinding",
         "Bind one content-pinned image to one mapping."),
        ("builtin", "texture_surface", "texture_surface(surface: Geometry, bindings: Keyed<TextureBinding>) -> Geometry",
         "Attach appearance to existing stable material keys of one unplaced native surface."),
        ("format", "ontokin.bundle/0.2", "entry + modules + immutable PNG assets",
         "Seal exact source and attachment bytes in one program revision."),
        ("capability", "textured_native_surfaces", "textured_native_surfaces",
         "Author editable labels, panels and marked floors on existing native geometry."),
    ]
    for kind, name, signature, description in entries:
        result["items"].append(_entry(kind, name, signature, description,
            capability="textured_native_surfaces", profile=TEXTURE_PROFILE, specification=ADOPTION,
            domains=domains, examples=EXAMPLES))
    result.pop("revision", None)
    result.pop("program_context", None)
    measure_json(result)
    return json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


_DECLARATIVE_JSON = _declarative_template()


def catalog(*, policy, linked_program=None, check=None, aggregate_limits=None):
    from .construction_catalog import _Budget, _public_interfaces
    budget = _Budget(check)
    budget.step()
    result = json.loads(_DECLARATIVE_JSON)
    budget.charge(result)
    current = interface(policy, aggregate_limits=aggregate_limits)
    budget.charge(current)
    result["textured_surfaces_interface"] = current
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != TEXTURE_PROFILE:
            raise ValueError("Texture discovery requires the admitted textured-surfaces source profile.")
        result["program_context"] = {"program_revision": linked_program.bundle.program_revision,
            "state": "linked declarations; no evaluated output claimed",
            "source_manifest": linked_program.bundle.manifest()}
        budget.charge(result["program_context"])
        for entry, node in _public_interfaces(linked_program, budget, source_profiles=True):
            budget.charge(entry, node)
            result["items"].append(entry)
    measure_json(result, check=check)
    raw = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    result["revision"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    return result
