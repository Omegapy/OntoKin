"""Explicit .13 image/UV streams, appended after inherited geometry and motion.

The supplied-byte validator derives expected mappings from the immutable source
recipe. It never trusts a texture's own metadata as its semantic authority.
"""
from __future__ import annotations

import hashlib
import struct
from contextvars import ContextVar

from .surface_runtime import materialize_surface
from .texture_runtime import texture_coordinates, texture_metadata


SAMPLER = {"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071}
_ACTIVE_TARGET = ContextVar("ontokin_texture_delivery_target", default="ontokin.glb/0.13")


def profile_metadata():
    return {"name": "textured-surfaces-0.1", "bundle_schema": "ontokin.bundle/0.2",
            "image_format": "opaque_noninterlaced_png_8bit_rgb_or_rgba",
            "max_assets": 4, "max_png_bytes": 300000, "max_width": 256, "max_height": 256,
            "coordinates": "raw_unplaced_recipe_local_affine",
            "uv_origin": "top_left", "v_direction": "down", "sampler": dict(SAMPLER),
            "color": "srgb_decoded_then_multiplied_by_linear_base_color_factor",
            "limits": ["opaque_base_color_only", "no_automatic_unwrapping", "recorded_rigid_motion_only"]}


def _fail(message, **details):
    from .scene import export_error
    export_error("OKE-E-TEXTURE", message, kind="unsupported", details={"target_contract": _ACTIVE_TARGET.get(), **details})


def _bytes_work(length, check):
    if check is not None:
        for _ in range((length + 63) // 64):
            check()


def prepare_node_textures(geometry, model, *, check=None):
    metadata = texture_metadata(geometry, check=check)
    if not metadata:
        return {}
    mesh, _ = materialize_surface(geometry, max_vertices=250000, check=check)
    def charge(amount):
        if check is not None:
            for _ in range(amount):
                check()
    coordinates = texture_coordinates(geometry, mesh, charge=charge)
    result = {}
    for region in mesh.regions:
        if check:
            check()
        if region.key not in metadata:
            continue
        binding = metadata[region.key]
        asset = model.texture_assets.get(binding["asset_id"])
        if asset is None or asset.sha256 != binding["sha256"]:
            from .profile_capabilities import KEYED_TRANSFORM_PROFILE, KEYED_REDUCTION_PROFILE, KEYED_FILTER_PROFILE, KEYED_MERGE_PROFILE, KEYED_ZIP_PROFILE, KEYED_REKEY_PROFILE, STRING_CONCAT_PROFILE, KEYED_MEMBERSHIP_PROFILE
            _fail("A source texture binding must retain its admitted immutable image.",
                  target_contract="ontokin.glb/0.21" if model.profile == KEYED_MEMBERSHIP_PROFILE else "ontokin.glb/0.20" if model.profile == STRING_CONCAT_PROFILE else "ontokin.glb/0.19" if model.profile == KEYED_REKEY_PROFILE else "ontokin.glb/0.18" if model.profile == KEYED_ZIP_PROFILE else "ontokin.glb/0.17" if model.profile == KEYED_MERGE_PROFILE else "ontokin.glb/0.16" if model.profile == KEYED_FILTER_PROFILE else "ontokin.glb/0.15" if model.profile == KEYED_REDUCTION_PROFILE else "ontokin.glb/0.14" if model.profile == KEYED_TRANSFORM_PROFILE else "ontokin.glb/0.13")
        result[region.key] = {"uv": coordinates[region.key], "binding": binding,
                              "asset": asset, "material": region.material, "program_revision": model.program_revision}
    return result


def append_texture_buffers(builder, pending, *, check=None, target_contract="ontokin.glb/0.13"):
    """Add UV/PNG data only after every preexisting accessor has been written."""
    if not pending:
        return {}
    used = {}
    for primitive, material, texture in pending:
        if check:
            check()
        asset = texture["asset"]
        previous = used.setdefault(asset.asset_id, texture)
        if previous["asset"].sha256 != asset.sha256:
            _fail("One image identity cannot alias different bytes.", target_contract=target_contract)
        primitive["attributes"]["TEXCOORD_0"] = builder.add(texture["uv"], 2, target=34962)
    identities = sorted(used)
    image_indices = {name: index for index, name in enumerate(identities)}
    images = []
    for name in identities:
        texture = used[name]
        asset = texture["asset"]
        raw = asset.raw
        _bytes_work(len(raw), check)
        padding = -len(builder.binary) % 4
        from .scene import MAX_GLB_BYTES, export_error
        if len(builder.binary) + padding + len(raw) > MAX_GLB_BYTES:
            export_error("OKE-E-GLB-BUDGET", "Embedded PNG data exceeds the GLB byte budget.", kind="resource")
        builder.binary.extend(b"\0" * padding)
        view = len(builder.views)
        builder.views.append({"buffer": 0, "byteOffset": len(builder.binary), "byteLength": len(raw)})
        builder.binary.extend(raw)
        images.append({"name": name, "bufferView": view, "mimeType": "image/png",
                       "extras": {"ontokin": {"asset_id": name, "sha256": asset.sha256,
                           "byte_length": len(raw), "program_revision": texture["program_revision"]}}})
    for primitive, material, texture in pending:
        material["pbrMetallicRoughness"]["baseColorTexture"] = {
            "index": image_indices[texture["asset"].asset_id], "texCoord": 0}
    return {"images": images,
            "textures": [{"sampler": 0, "source": i} for i in range(len(images))],
            "samplers": [dict(SAMPLER)]}


def _reference(table, index, label):
    if type(index) is not int or not 0 <= index < len(table):
        _fail("Texture references must be nonnegative in-range integers.", reference=label)
    return table[index]


def validate_texture_shapes(document, *, check=None):
    """Refuse renderer behavior outside the recorded .13 source subset.

    Exact base accessors do not establish appearance or rigid geometry when
    optional glTF fields can add normal/emission maps, unlit materials, morph
    targets, skins, instancing, texture transforms, or extra scene lighting.
    Only explicit texture-family destinations call this closed-shape check.
    The .16 destination also closes metadata at each supported container;
    authority values remain independently checked against the supplied source.
    Earlier destinations retain their existing extras policy.
    """
    def closed(value, allowed, label):
        if check is not None:
            check()
        if type(value) is not dict:
            _fail("Recorded texture structures must be JSON objects.", structure=label)
        unexpected = set(value) - allowed
        if unexpected:
            _fail("The recorded texture destination cannot add unsupported rendering fields.",
                  structure=label, fields=sorted(unexpected))

    def rows(value, label):
        if check is not None:
            check()
        if type(value) is not list:
            _fail("Recorded texture tables must be JSON arrays.", structure=label)
        return value

    closed(document, {"asset", "scene", "scenes", "nodes", "meshes", "materials",
                       "buffers", "bufferViews", "accessors", "animations", "extras",
                       "images", "textures", "samplers"}, "document")
    filter_contract = _ACTIVE_TARGET.get() in {"ontokin.glb/0.16", "ontokin.glb/0.17", "ontokin.glb/0.18", "ontokin.glb/0.19", "ontokin.glb/0.20", "ontokin.glb/0.21"}
    if filter_contract:
        closed(document.get("extras"), {"ontokin"}, "scene extras")
        metadata = document["extras"].get("ontokin")
        closed(metadata, {"target_contract", "schema_version", "source", "module", "scene", "profile",
                          "coordinates", "transform_policy", "joints", "follows", "boundary_states",
                          "gravity_m_per_s2", "motion_authority", "program", "force_profile",
                          "surface_profile", "reach_profile", "reach_quantization", "texture_profile",
                          "surface_delivery"}, "scene authority")
        closed(metadata.get("source"), {"uri", "uri_kind", "entry_source_id", "entry_revision",
                                        "editable_source_of_truth", "provenance"}, "scene source")
    incidental_extras = set() if filter_contract else {"extras"}
    surface_meshes = set()
    closed(document["asset"], {"version", "generator"} | incidental_extras, "asset")
    for scene in rows(document["scenes"], "scenes"):
        closed(scene, {"name", "nodes"} | incidental_extras, "scene")
    for node in rows(document["nodes"], "nodes"):
        closed(node, {"name", "translation", "rotation", "mesh", "extras"}, "node")
        if filter_contract:
            closed(node.get("extras"), {"ontokin"}, "node extras")
            metadata = node["extras"].get("ontokin")
            if type(metadata) is dict and metadata.get("kind") == "object":
                fields = {"kind", "path", "element_id", "owner", "class_name", "geometry", "physical",
                          "collision", "authored_motion", "appearance_linear_rgba", "pose_frame", "role",
                          "properties", "source_mapping", "program_revision"}
                geometry = metadata.get("geometry")
                # The later exact source-geometry comparison binds this
                # discriminator; an empty/primitive object cannot gain an
                # otherwise recognized native-surface authority field.
                if type(geometry) is dict and geometry.get("kind") in (
                        "loft", "placed", "extrusion", "holes", "ring_loft", "framed_loft", "pockets"):
                    fields.add("surface")
                    if "mesh" in node:
                        surface_meshes.add(node["mesh"])
            else:
                fields = {"kind", "helper_kind", "physical_participation", "related_element_id",
                          "frame_path"}
                helper_kind = metadata.get("helper_kind") if type(metadata) is dict else None
                if helper_kind == "assembly_origin":
                    fields.add("object_path")
                elif helper_kind == "joint_parent_site":
                    fields.update(("joint_path", "meaning"))
            closed(metadata, fields, "node authority")
    surface_materials = set()
    for mesh_index, mesh in enumerate(rows(document.get("meshes", []), "meshes")):
        closed(mesh, {"name", "primitives"} | incidental_extras, "mesh")
        native_surface = filter_contract and mesh_index in surface_meshes
        for primitive in rows(mesh["primitives"], "primitives"):
            allowed_extras = {"extras"} if native_surface else incidental_extras
            closed(primitive, {"attributes", "indices", "material", "mode"} | allowed_extras, "primitive")
            if native_surface:
                closed(primitive.get("extras"), {"ontokin"}, "primitive extras")
                closed(primitive["extras"].get("ontokin"), {"region_key"}, "primitive authority")
                surface_materials.add(primitive["material"])
    for material_index, material in enumerate(rows(document.get("materials", []), "materials")):
        native_surface = filter_contract and material_index in surface_materials
        allowed_extras = {"extras"} if native_surface else incidental_extras
        closed(material, {"name", "pbrMetallicRoughness", "alphaMode"} | allowed_extras, "material")
        if native_surface:
            closed(material.get("extras"), {"ontokin"}, "material extras")
            closed(material["extras"].get("ontokin"),
                   {"source_region_key", "occurrence_path", "element_id", "program_revision"}, "material authority")
        pbr = material.get("pbrMetallicRoughness", {})
        closed(pbr, {"baseColorFactor", "metallicFactor", "roughnessFactor", "baseColorTexture"},
               "pbrMetallicRoughness")
        if "baseColorTexture" in pbr:
            closed(pbr["baseColorTexture"], {"index", "texCoord"}, "baseColorTexture")
    for image in rows(document.get("images", []), "images"):
        closed(image, {"name", "bufferView", "mimeType", "extras"}, "image")
    for texture in rows(document.get("textures", []), "textures"):
        closed(texture, {"sampler", "source"}, "texture")
    for sampler in rows(document.get("samplers", []), "texture samplers"):
        closed(sampler, {"magFilter", "minFilter", "wrapS", "wrapT"}, "texture sampler")
    for buffer in rows(document["buffers"], "buffers"):
        closed(buffer, {"byteLength"}, "buffer")
    for view in rows(document["bufferViews"], "buffer views"):
        closed(view, {"buffer", "byteOffset", "byteLength", "target"}, "buffer view")
    for accessor in rows(document["accessors"], "accessors"):
        closed(accessor, {"bufferView", "componentType", "count", "type", "min", "max"}, "accessor")
    for animation in rows(document["animations"], "animations"):
        closed(animation, {"name", "samplers", "channels", "extras"}, "animation")
        if filter_contract:
            closed(animation.get("extras"), {"ontokin"}, "animation extras")
            closed(animation["extras"].get("ontokin"),
                   {"target_contract", "exact_times_seconds", "boundary_times_seconds"}, "animation authority")
        for sampler in rows(animation["samplers"], "animation samplers"):
            closed(sampler, {"input", "output", "interpolation"}, "animation sampler")
        for channel in rows(animation["channels"], "animation channels"):
            closed(channel, {"sampler", "target"}, "animation channel")
            closed(channel["target"], {"node", "path"}, "animation target")


def validate_texture_delivery(decoded, model, *, check=None):
    """Compare supplied image, UV and reference bytes with fresh source facts."""
    from .profile_capabilities import KEYED_TRANSFORM_PROFILE, KEYED_REDUCTION_PROFILE, KEYED_FILTER_PROFILE, KEYED_MERGE_PROFILE, KEYED_ZIP_PROFILE, KEYED_REKEY_PROFILE, STRING_CONCAT_PROFILE, KEYED_MEMBERSHIP_PROFILE
    target = "ontokin.glb/0.21" if model.profile == KEYED_MEMBERSHIP_PROFILE else "ontokin.glb/0.20" if model.profile == STRING_CONCAT_PROFILE else "ontokin.glb/0.19" if model.profile == KEYED_REKEY_PROFILE else "ontokin.glb/0.18" if model.profile == KEYED_ZIP_PROFILE else "ontokin.glb/0.17" if model.profile == KEYED_MERGE_PROFILE else "ontokin.glb/0.16" if model.profile == KEYED_FILTER_PROFILE else "ontokin.glb/0.15" if model.profile == KEYED_REDUCTION_PROFILE else "ontokin.glb/0.14" if model.profile == KEYED_TRANSFORM_PROFILE else "ontokin.glb/0.13"
    token = _ACTIVE_TARGET.set(target)
    try:
        return _validate_texture_delivery(decoded, model, check=check)
    finally:
        _ACTIVE_TARGET.reset(token)


def _validate_texture_delivery(decoded, model, *, check=None):
    doc = decoded.document
    validate_texture_shapes(doc, check=check)
    images, textures, samplers = (doc.get(name, []) for name in ("images", "textures", "samplers"))
    if not all(type(value) is list for value in (images, textures, samplers)):
        _fail("Texture tables must be arrays.")
    if len(images) > 4 or len(textures) > 4 or len(samplers) > 1:
        _fail("Texture tables exceed the admitted image and sampler counts.")
    expected_assets, used_images, used_textures, uv_ids, legacy_ids = {}, set(), set(), set(), set()
    uv_views, image_views = set(), set()
    for animation in doc["animations"]:
        for sampler in animation["samplers"]:
            legacy_ids.update((sampler["input"], sampler["output"]))
    for node in doc["nodes"]:
        if check:
            check()
        if "mesh" not in node:
            continue
        obj = model.objects.get(node.get("extras", {}).get("ontokin", {}).get("path"))
        expected = prepare_node_textures(obj.geometry, model, check=check) if obj is not None else {}
        primitives = doc["meshes"][node["mesh"]]["primitives"]
        for primitive in primitives:
            if check:
                check()
            attributes = primitive["attributes"]
            legacy_ids.update((attributes["POSITION"], attributes["NORMAL"], primitive["indices"]))
            region = primitive.get("extras", {}).get("ontokin", {}).get("region_key")
            material = doc["materials"][primitive["material"]]
            reference = material.get("pbrMetallicRoughness", {}).get("baseColorTexture")
            if region not in expected:
                if set(attributes) != {"POSITION", "NORMAL"} or reference is not None:
                    _fail("An untextured region cannot acquire an image or texture coordinates.", region=region)
                continue
            texture = expected[region]
            source_material = texture["material"]
            pbr = material.get("pbrMetallicRoughness", {})
            if (pbr.get("baseColorFactor") != list(source_material.rgba)
                    or pbr.get("metallicFactor") != source_material.metallic
                    or pbr.get("roughnessFactor") != source_material.roughness
                    or material.get("alphaMode", "OPAQUE") != "OPAQUE"):
                _fail("Textured material factors and opacity must match the authored regional material.")
            asset = texture["asset"]
            expected_assets[asset.asset_id] = asset
            if set(attributes) != {"POSITION", "NORMAL", "TEXCOORD_0"}:
                _fail("A textured region requires exactly the inherited attributes and TEXCOORD_0.", region=region)
            if type(reference) is not dict or set(reference) != {"index", "texCoord"} or type(reference["texCoord"]) is not int or reference["texCoord"] != 0:
                _fail("Base color texture must explicitly select UV set zero.")
            texture_id = reference["index"]
            selected = _reference(textures, texture_id, "texture")
            if type(selected) is not dict or set(selected) != {"sampler", "source"} or type(selected["sampler"]) is not int or selected["sampler"] != 0:
                _fail("Each image texture must use the fixed explicit sampler.")
            image_id = selected["source"]
            image = _reference(images, image_id, "image")
            used_images.add(image_id); used_textures.add(texture_id)
            if (type(image) is not dict or set(image) != {"name", "bufferView", "mimeType", "extras"}
                    or image["mimeType"] != "image/png" or image["name"] != asset.asset_id
                    or image["extras"] != {"ontokin": {"asset_id": asset.asset_id,
                        "sha256": asset.sha256, "byte_length": len(asset.raw), "program_revision": model.program_revision}}):
                _fail("Embedded PNG identity must match the source attachment selected by this region.")
            view_id = image["bufferView"]
            view = _reference(doc["bufferViews"], view_id, "PNG buffer view")
            if set(view) != {"buffer", "byteOffset", "byteLength"} or view["buffer"] != 0 or view["byteLength"] != len(asset.raw):
                _fail("A PNG uses an exact ordinary embedded buffer view.")
            _bytes_work(view["byteLength"], check)
            raw = decoded.binary[view["byteOffset"]:view["byteOffset"] + view["byteLength"]]
            if raw != asset.raw or "sha256:" + hashlib.sha256(raw).hexdigest() != asset.sha256:
                _fail("Supplied PNG bytes differ from the exact source attachment.")
            image_views.add(view_id)
            uv_id = attributes["TEXCOORD_0"]
            accessor = _reference(doc["accessors"], uv_id, "UV accessor")
            if (set(accessor) != {"bufferView", "componentType", "count", "type"}
                    or accessor["componentType"] != 5126 or accessor["type"] != "VEC2"
                    or accessor["count"] != len(texture["uv"])):
                _fail("UVs must be full-size tightly packed binary32 VEC2 accessors.")
            uv_view_id = accessor["bufferView"]
            uv_view = _reference(doc["bufferViews"], uv_view_id, "UV buffer view")
            if (set(uv_view) != {"buffer", "byteOffset", "byteLength", "target"}
                    or uv_view["buffer"] != 0 or uv_view["target"] != 34962
                    or uv_view["byteLength"] != len(texture["uv"]) * 8):
                _fail("Texture coordinate buffers must be tightly packed vertex data.")
            for index, uv in enumerate(texture["uv"]):
                if check and index % 64 == 0:
                    check()
                actual = decoded.binary[uv_view["byteOffset"] + index * 8:uv_view["byteOffset"] + (index + 1) * 8]
                if actual != struct.pack("<2f", *uv):
                    _fail("Supplied UV bytes differ from the once-rounded recipe-local mapping.", region=region, corner=index)
            uv_ids.add(uv_id); uv_views.add(uv_view_id)
    if expected_assets:
        if samplers != [SAMPLER] or used_images != set(range(len(images))) or used_textures != set(range(len(textures))):
            _fail("Only used images/textures and the fixed sampler may be emitted.")
        if len(images) != len(expected_assets) or len(textures) != len(images) or [im["name"] for im in images] != sorted(expected_assets):
            _fail("Every used source asset ID must have exactly one deterministic image and texture.")
        if textures != [{"sampler": 0, "source": i} for i in range(len(images))]:
            _fail("Image references may not alias distinct source attachment identities.")
    elif images or textures or samplers:
        _fail("A program with no emitted textured region cannot contain dangling image tables.")
    if len(image_views) != len(images):
        _fail("Distinct source image IDs require distinct embedded PNG storage views.")
    intervals = sorted((doc["bufferViews"][i].get("byteOffset", 0),
                        doc["bufferViews"][i].get("byteOffset", 0) + doc["bufferViews"][i]["byteLength"])
                       for i in uv_views | image_views)
    for previous, current in zip(intervals, intervals[1:]):
        if check:
            check()
        if previous[1] > current[0]:
            _fail("Distinct UV and image storage views cannot overlap each other's bytes.")
    legacy_views = {doc["accessors"][i]["bufferView"] for i in legacy_ids}
    legacy_end = max((doc["bufferViews"][i].get("byteOffset", 0) + doc["bufferViews"][i]["byteLength"]
                      for i in legacy_views), default=0)
    if (set(range(len(doc["accessors"]))) != legacy_ids | uv_ids
            or set(range(len(doc["bufferViews"]))) != legacy_views | uv_views | image_views
            or legacy_views & (uv_views | image_views) or uv_views & image_views
            or any(doc["bufferViews"][i].get("byteOffset", 0) < legacy_end for i in uv_views | image_views)):
        _fail("UV/image streams must follow all inherited geometry and animation without aliasing or dangling data.")
