#!/usr/bin/env python3
"""Check the frozen C220 inputs without evaluating source or starting a target.

Only ``check_package`` is an admission API. ``validate_structure`` is an internal
test seam: it checks cross-document consistency but cannot establish byte locks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import struct
import sys


SCHEMA = "ontokin.c221.authority-binding-check/0.1"
VERSION = "C221/0.1.0"
ACCEPTED_REVISION = "sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082"
REPOSITORY_BASE = "a266424b5cb0c3a7e020ab72d0ef8e7cd8886976"
AUTHORITY_DIRECTORY = "docs/engineering/second-target-c220/evidence"
AUTHORITY_PINS = {
    "INPUT-BINDINGS.json": (3512, "6ce256ab7cfd9690665b7577e7bb9e3aca952c9b73e5e017b30dcded1d053625", 0o644),
    "PART-MAP.json": (52508, "f8911b5d846114fe525ab753b78a16f665bd7a43775ecfce2e656d17eb1419ed", 0o644),
}
INPUT_DIRECTORY = "agent-results/namespace-repair/run-01/inputs/"
INPUT_PATHS = (
    INPUT_DIRECTORY + "after.glb",
    INPUT_DIRECTORY + "after.program.bundle.json",
    INPUT_DIRECTORY + "after.semantic.json",
    INPUT_DIRECTORY + "source-payload.json",
    INPUT_DIRECTORY + "after.reference.json",
    "agent-results/reopen-c218/run-01/reopen-details.json",
    "workers/native-review/source-expectations.json",
    "agent-results/reopen-c218/run-01/reopen-observations.json",
)


class CheckError(ValueError):
    """A fail-closed input or structural refusal."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise CheckError(code, message)


def equal(actual, expected, label: str) -> None:
    # JSON canonicalization also distinguishes booleans from integer indices.
    require(canonical(actual) == canonical(expected), "BINDING", label + " differs")


def canonical(value) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise CheckError("JSON", "Value is not finite canonical JSON") from exc


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw: bytes, label: str):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "JSON", label + ": duplicate JSON key")
            result[key] = value
        return result

    def constant(value):
        raise CheckError("JSON", label + ": non-finite JSON constant")

    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                            parse_constant=constant)
        canonical(result)
        return result
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, CheckError):
            raise
        raise CheckError("JSON", label + ": malformed UTF-8 JSON") from exc


def object_value(value, label: str) -> dict:
    require(type(value) is dict, "SHAPE", label + " must be an object")
    return value


def array_value(value, label: str, length: int | None = None) -> list:
    require(type(value) is list, "SHAPE", label + " must be an array")
    if length is not None:
        require(len(value) == length, "COUNT", label + " has an unexpected count")
    return value


def integer(value, label: str, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, "INDEX", label + " must be an integer in range")
    return value


def index_value(values: list, index, label: str):
    integer(index, label)
    require(index < len(values), "INDEX", label + " is outside its array")
    return values[index]


def identifier(value, label: str) -> tuple[str, ...]:
    array_value(value, label)
    require(bool(value) and all(type(x) is str and x for x in value),
            "IDENTITY", label + " must contain nonempty strings")
    return tuple(value)


def relative_parts(path: str) -> tuple[str, ...]:
    require(type(path) is str and path and "\\" not in path and "\x00" not in path,
            "PATH", "Input path is not a safe POSIX relative path")
    parts = path.split("/")
    require(not path.startswith("/") and all(p not in ("", ".", "..") for p in parts),
            "PATH", "Absolute, empty, dot and traversal components are refused")
    equal(str(PurePosixPath(path)), path, "Normalized input path")
    return tuple(parts)


class SafeRoot:
    """Open an actual directory and descend with no-follow directory handles."""

    def __init__(self, root):
        require(hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY") and
                os.open in os.supports_dir_fd, "PLATFORM", "Safe POSIX file opening is unavailable")
        supplied = os.fspath(root)
        require(type(supplied) is str and "\x00" not in supplied, "PATH", "Invalid package root")
        # Do not normalize away traversal before checking it.
        require(".." not in supplied.split("/"), "PATH", "Traversal in package root is refused")
        absolute = os.path.abspath(supplied)
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in Path(absolute).parts[1:]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
        except OSError as exc:
            os.close(fd)
            raise CheckError("PATH", "Package root must contain only real directories") from exc
        self.fd = fd

    def __enter__(self):
        return self

    def __exit__(self, *_):
        os.close(self.fd)

    def read(self, path: str, size: int, sha256: str, mode: int) -> bytes:
        parts = relative_parts(path)
        integer(size, "Pinned byte length")
        require(size <= 4 * 1024 * 1024, "SIZE", "Input exceeds this finite checker's byte ceiling")
        fd = os.dup(self.fd)
        try:
            for part in parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            # NONBLOCK prevents a substituted FIFO from blocking before fstat.
            file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                before = os.fstat(file_fd)
                require(stat.S_ISREG(before.st_mode), "FILE", path + ": expected a regular file")
                require(stat.S_IMODE(before.st_mode) == mode, "MODE", path + ": mode differs")
                require(before.st_size == size, "SIZE", path + ": byte length differs")
                chunks = []
                remaining = size + 1
                while remaining:
                    chunk = os.read(file_fd, min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                raw = b"".join(chunks)
                after = os.fstat(file_fd)
                keys = ("st_dev", "st_ino", "st_size", "st_mode", "st_mtime_ns", "st_ctime_ns")
                require(all(getattr(before, key) == getattr(after, key) for key in keys),
                        "CHANGED", path + ": file changed while reading")
                require(len(raw) == size, "SIZE", path + ": short or growing file")
                require(digest(raw) == sha256, "HASH", path + ": SHA-256 differs")
                return raw
            finally:
                os.close(file_fd)
        except OSError as exc:
            raise CheckError("FILE", path + ": missing, unsafe or unreadable file") from exc
        finally:
            os.close(fd)


def load_authority() -> tuple[dict, dict]:
    repository = Path(__file__).absolute().parents[2]
    values = []
    with SafeRoot(repository) as root:
        for name, (size, sha256, mode) in AUTHORITY_PINS.items():
            raw = root.read(AUTHORITY_DIRECTORY + "/" + name, size, sha256, mode)
            values.append(object_value(strict_json(raw, name), name))
    return tuple(values)


def _input_items(bindings: dict) -> list:
    equal(bindings["schema"], "ontokin.c220.planning-inputs/0.1", "Binding schema")
    equal(bindings["acceptedProgramRevision"], ACCEPTED_REVISION, "Accepted program revision")
    items = array_value(bindings["items"], "Locked inputs", 8)
    paths = [item["packagePath"] for item in items]
    equal(paths, list(INPUT_PATHS), "Ordered finite input inventory")
    require(len(set(paths)) == 8, "IDENTITY", "Duplicate input paths")
    for item in items:
        relative_parts(item["packagePath"])
        integer(item["bytes"], "Input byte length", 1)
        equal(item["mode"], 0o644, "Input file mode")
        sha = item["sha256"]
        require(type(sha) is str and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha),
                "HASH", "Invalid pinned input digest")
    return items


def _source_manifest(bundle: dict) -> tuple[dict, dict]:
    equal(sorted(bundle), ["entry", "modules", "schema_version"], "Bundle fields")
    equal(bundle["schema_version"], "ontokin.bundle/0.1", "Bundle schema")
    entry = object_value(bundle["entry"], "Entry source")
    equal(sorted(entry), ["filename", "source"], "Entry source fields")
    modules = array_value(bundle["modules"], "Source modules", 1)
    units = [("entry", None, None, entry)]
    for module in modules:
        equal(sorted(module), ["filename", "package_id", "source", "version"], "Module fields")
        package_id, version = module["package_id"], module["version"]
        require(type(package_id) is str and type(version) is str, "SOURCE", "Invalid module identity")
        units.append(("package:" + package_id + "@" + version, package_id, version, module))
    manifest, sources = [], {}
    for source_id, package_id, version, unit in sorted(units):
        require(source_id not in sources, "SOURCE", "Duplicate source identity")
        require(type(unit["source"]) is str and type(unit["filename"]) is str,
                "SOURCE", "Source text and filename must be strings")
        raw = unit["source"].encode("utf-8")
        row = {"source_id": source_id, "package_id": package_id, "version": version,
               "filename": unit["filename"], "source_revision": "sha256:" + digest(raw)}
        sources[source_id] = {"raw": raw, **row}
        manifest.append(row)
    result = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": manifest}
    revision = "sha256:" + digest(b"ontokin.bundle/0.1\0" + canonical(result))
    equal(revision, ACCEPTED_REVISION, "Independently reconstructed program revision")
    return result, sources


def _check_spans(value, sources: dict, seen: set) -> int:
    total = 0
    if type(value) is dict:
        if "start_byte" in value or "end_byte" in value:
            equal(sorted(value), ["end_byte", "filename", "source_id", "source_revision", "start_byte"],
                  "Source span fields")
            require(value["source_id"] in sources, "SPAN", "Unknown source span unit")
            source = sources[value["source_id"]]
            for key in ("source_revision", "filename"):
                equal(value[key], source[key], "Span " + key)
            start = integer(value["start_byte"], "Span start")
            end = integer(value["end_byte"], "Span end", 1)
            raw = source["raw"]
            require(start < end <= len(raw), "SPAN", "Source span is empty or outside source bytes")
            try:
                raw[:start].decode("utf-8")
                raw[start:end].decode("utf-8")
            except UnicodeError as exc:
                raise CheckError("SPAN", "Source span splits a UTF-8 sequence") from exc
            seen.add((value["source_id"], value["source_revision"], start, end))
            total += 1
        for child in value.values():
            total += _check_spans(child, sources, seen)
    elif type(value) is list:
        total += sum(_check_spans(child, sources, seen) for child in value)
    return total


def decode_glb(raw: bytes) -> tuple[dict, bytes]:
    require(type(raw) is bytes and len(raw) >= 28, "GLB", "Truncated GLB header")
    magic, version, declared = struct.unpack_from("<4sII", raw)
    require(magic == b"glTF" and version == 2 and declared == len(raw), "GLB", "Invalid GLB header")
    chunks, offset = [], 12
    while offset < len(raw):
        require(offset + 8 <= len(raw), "GLB", "Truncated GLB chunk header")
        length, kind = struct.unpack_from("<II", raw, offset)
        offset += 8
        require(length % 4 == 0 and offset + length <= len(raw), "GLB", "Invalid GLB chunk extent")
        chunks.append((kind, raw[offset:offset + length]))
        offset += length
    equal([kind for kind, _ in chunks], [0x4E4F534A, 0x004E4942], "GLB JSON/BIN chunk order")
    document = object_value(strict_json(chunks[0][1], "GLB JSON"), "GLB JSON")
    equal(document["asset"]["version"], "2.0", "glTF asset version")
    buffers = array_value(document["buffers"], "GLB buffers", 1)
    equal(sorted(buffers[0]), ["byteLength"], "Embedded buffer fields")
    size = integer(buffers[0]["byteLength"], "Buffer size", 1)
    binary = chunks[1][1]
    require(0 <= len(binary) - size <= 3 and not any(binary[size:]), "GLB", "Invalid BIN buffer padding")
    return document, binary[:size]


def _accessor(glb: dict, binary: bytes, index: int) -> tuple[dict, bytes]:
    accessor = object_value(index_value(glb["accessors"], index, "Accessor index"), "Accessor")
    require("sparse" not in accessor and not accessor.get("normalized", False),
            "ACCESSOR", "Sparse or normalized accessors are outside this finite profile")
    view_index = accessor["bufferView"]
    view = object_value(index_value(glb["bufferViews"], view_index, "Buffer-view index"), "Buffer view")
    equal(view["buffer"], 0, "Buffer-view buffer")
    component = accessor["componentType"]
    widths = {5123: 2, 5126: 4}
    require(type(component) is int and component in widths, "ACCESSOR", "Unsupported component type")
    dimensions = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}
    require(accessor["type"] in dimensions, "ACCESSOR", "Unsupported accessor shape")
    count = integer(accessor["count"], "Accessor count", 1)
    width = widths[component] * dimensions[accessor["type"]]
    view_offset = integer(view.get("byteOffset", 0), "View offset")
    view_length = integer(view["byteLength"], "View length", 1)
    accessor_offset = integer(accessor.get("byteOffset", 0), "Accessor offset")
    require("byteStride" not in view, "ACCESSOR", "Interleaved views are outside this finite profile")
    require(view_offset % widths[component] == 0 and accessor_offset % widths[component] == 0,
            "ACCESSOR", "Unaligned accessor")
    require(view_offset + view_length <= len(binary) and accessor_offset + count * width <= view_length,
            "ACCESSOR", "Accessor extends outside its buffer view")
    start = view_offset + accessor_offset
    raw = binary[start:start + count * width]
    metadata = {"accessor": index, "buffer_view": view_index, "component_type": component,
                "count": count, "type": accessor["type"], "data_sha256": "sha256:" + digest(raw)}
    return metadata, raw


def _unique_rows(rows: list, path_key: str, id_key: str, label: str) -> dict:
    paths, ids = {}, set()
    for row in rows:
        object_value(row, label)
        path = row[path_key]
        require(type(path) is str and path and path not in paths, "IDENTITY", label + ": duplicate or invalid path")
        element = identifier(row[id_key], label + " element ID")
        require(element not in ids, "IDENTITY", label + ": duplicate element ID")
        paths[path] = row
        ids.add(element)
    return paths


def _check_parts(part_map: dict, semantic: dict, glb: dict, binary: bytes, sources: dict) -> dict:
    equal(part_map["schema"], "ontokin.c220.planned-part-map/0.1", "Part-map schema")
    equal(part_map["acceptedProgramRevision"], ACCEPTED_REVISION, "Part-map program revision")
    equal(part_map["nodeCount"], 18, "Part-map count")
    planned = _unique_rows(array_value(part_map["entries"], "Planned parts", 18),
                           "sourcePath", "elementId", "Planned parts")
    objects = _unique_rows(array_value(semantic["objects"], "Semantic objects", 18),
                           "path", "element_id", "Semantic objects")
    equal(sorted(planned), sorted(objects), "Complete planned and semantic part sets")
    nodes = array_value(glb["nodes"], "GLB nodes", 18)
    array_value(glb["meshes"], "GLB meshes", 5)
    array_value(glb["accessors"], "GLB accessors", 52)
    array_value(glb["bufferViews"], "GLB buffer views", 52)
    array_value(glb["materials"], "GLB materials", 2)
    equal(glb["scene"], 0, "Default scene")
    scenes = array_value(glb["scenes"], "GLB scenes", 1)
    equal(sorted(scenes[0]["nodes"]), list(range(18)), "Complete root-node scene inventory")
    program = glb["extras"]["ontokin"]["program"]
    equal(sorted(program["occurrences"]), sorted(planned), "Complete GLB occurrence inventory")
    seen_nodes, seen_ids, seen_paths = set(), set(), set()
    distinct_spans = set()
    total_spans, triangles, accessor_uses = 0, 0, 0
    for path, entry in planned.items():
        obj = objects[path]
        node_index = integer(entry["glbNode"], "Mapped node")
        require(node_index not in seen_nodes, "IDENTITY", "Duplicate mapped GLB node")
        seen_nodes.add(node_index)
        node = object_value(index_value(nodes, node_index, "Mapped node"), "GLB node")
        require(not node.get("children"), "NODE", "Product nodes must remain independent roots")
        extra = object_value(node["extras"]["ontokin"], "GLB OntoKin extras")
        equal(extra["kind"], "object", "GLB object kind")
        equal(extra["program_revision"], ACCEPTED_REVISION, "GLB node program revision")
        equal(extra["path"], path, "GLB source path")
        eid = identifier(extra["element_id"], "GLB element ID")
        require(eid not in seen_ids and extra["path"] not in seen_paths,
                "IDENTITY", "Duplicate GLB semantic identity")
        seen_ids.add(eid)
        seen_paths.add(extra["path"])
        equal(entry["elementId"], obj["element_id"], "Planned element identity")
        equal(extra["element_id"], obj["element_id"], "GLB element identity")
        equal(entry["definitionId"], obj["definition_id"], "Definition identity")
        provenance = object_value(entry["sourceProvenance"], "Source provenance")
        for actual in (obj["provenance"], extra["source_mapping"], program["occurrences"][path]):
            equal(actual, provenance, "Complete occurrence provenance")
        equal(provenance["element_id"], entry["elementId"], "Provenance element identity")
        equal(provenance["definition_id"], entry["definitionId"], "Provenance definition identity")
        equal(provenance["class_id"], obj["class_id"], "Class identity")
        equal(extra["class_name"], obj["class_id"], "GLB class identity")
        equal(provenance["path"], path, "Provenance path")
        for key in ("declaration", "definition"):
            object_value(provenance[key], "Required " + key + " span")
            require("start_byte" in provenance[key], "SPAN", "Required source span is absent")
        steps = array_value(provenance["path_steps"], "Occurrence path steps")
        rendered, keys = "", []
        for step in steps:
            equal(sorted(step), ["kind", "value"], "Path step fields")
            require(type(step["value"]) is str and step["value"], "IDENTITY", "Empty occurrence key")
            keys.append(step["value"])
            if step["kind"] == "member":
                rendered += ("." if rendered else "") + step["value"]
            elif step["kind"] == "key":
                require(bool(rendered), "IDENTITY", "Key cannot begin an occurrence path")
                rendered += "[" + json.dumps(step["value"], ensure_ascii=False) + "]"
            else:
                raise CheckError("IDENTITY", "Unknown occurrence path step")
        equal(rendered, path, "Independently reconstructed occurrence path")
        equal(entry["elementId"], ["keyed-rack", "demo"] + keys, "Occurrence identity steps")
        equal(provenance["root_path"], keys[0], "Occurrence root")
        equal(entry["semanticOwner"], obj["owner"], "Semantic owner")
        owner = obj["owner"]
        owner_path = None if owner is None else owner["path"]
        if owner is not None:
            require(owner_path in objects, "IDENTITY", "Semantic owner is absent")
            equal(owner["element_id"], objects[owner_path]["element_id"], "Semantic owner identity")
        equal(extra["owner"], owner_path, "GLB semantic owner path")
        equal(provenance["owner_path"], owner_path, "Occurrence owner path")
        generated = provenance["generated"]
        if generated is not None:
            equal(generated["key"], keys[-1], "Generated occurrence key")
            equal(generated["collection_id"], entry["elementId"][:-1], "Generated collection identity")
        total_spans += _check_spans(provenance, sources, distinct_spans)
        binding = obj["geometry_binding"]
        equal(binding["node"], node_index, "Semantic geometry node")
        equal(binding["mesh"], entry["glbMesh"], "Semantic geometry mesh")
        equal(node["mesh"], entry["glbMesh"], "GLB node mesh")
        mesh = index_value(glb["meshes"], entry["glbMesh"], "GLB mesh index")
        primitives = array_value(mesh["primitives"], "Mesh primitives", 1)
        mapped = array_value(entry["primitives"], "Mapped primitives", 1)
        semantic_primitives = array_value(binding["primitives"], "Semantic primitives", 1)
        for number, (primitive, mapping, declared) in enumerate(zip(primitives, mapped, semantic_primitives)):
            equal(mapping["primitive"], number, "Mapped primitive index")
            equal(declared["primitive"], number, "Semantic primitive index")
            equal(primitive["mode"], 4, "Triangle primitive mode")
            equal(sorted(primitive["attributes"]), ["NORMAL", "POSITION"], "Finite vertex attributes")
            for field in ("material",):
                equal(mapping[field], primitive[field], "Mapped material index")
                equal(declared[field], primitive[field], "Semantic material index")
            index_value(glb["materials"], primitive["material"], "Material index")
            counts = {}
            for attribute, map_key in (("POSITION", "positionAccessor"), ("NORMAL", "normalAccessor")):
                index = primitive["attributes"][attribute]
                equal(mapping[map_key], index, "Mapped " + attribute + " accessor")
                metadata, _ = _accessor(glb, binary, index)
                equal(metadata, declared["attributes"][attribute], "Independently decoded " + attribute + " metadata/hash")
                equal([metadata["type"], metadata["component_type"]], ["VEC3", 5126], "Vertex accessor format")
                counts[attribute] = metadata["count"]
                accessor_uses += 1
            equal(counts["POSITION"], counts["NORMAL"], "Position/normal vertex counts")
            equal(mapping["indexAccessor"], primitive["indices"], "Mapped index accessor")
            metadata, index_bytes = _accessor(glb, binary, primitive["indices"])
            equal(metadata, declared["indices"], "Independently decoded index metadata/hash")
            equal([metadata["type"], metadata["component_type"]], ["SCALAR", 5123], "Index accessor format")
            require(metadata["count"] % 3 == 0, "TOPOLOGY", "Incomplete triangle index triple")
            require(all(value[0] < counts["POSITION"] for value in struct.iter_unpack("<H", index_bytes)),
                    "TOPOLOGY", "Triangle index is outside its vertex accessor")
            triangles += metadata["count"] // 3
            accessor_uses += 1
    equal(sorted(seen_nodes), list(range(18)), "Complete unique mapped-node inventory")
    equal(triangles, 7800, "Instance triangle inventory")
    return {"parts": 18, "source_span_occurrences": total_spans, "distinct_source_spans": len(distinct_spans),
            "instance_triangles": triangles,
            "instance_corners": triangles * 3, "geometry_accessor_uses": accessor_uses}


def validate_structure(bindings: dict, part_map: dict, inputs: dict[str, bytes]) -> dict:
    """Internal structural test seam; this does NOT establish file byte locks."""
    try:
        items = _input_items(bindings)
        equal(sorted(inputs), sorted(INPUT_PATHS), "Supplied input inventory")
        parsed = {path: strict_json(raw, path) for path, raw in inputs.items() if path.endswith(".json")}
        bundle, semantic, payload, reference = [parsed[INPUT_PATHS[i]] for i in (1, 2, 3, 4)]
        manifest, sources = _source_manifest(object_value(bundle, "Program bundle"))
        equal(manifest, bindings["sourceManifest"], "Reconstructed source manifest")
        equal(semantic["schema_version"], "ontokin.semantic-export/0.1", "Semantic schema")
        equal(semantic["profile"], "construction-primitives/0.1", "Semantic profile")
        equal(semantic["binding"]["accepted_program_revision"], ACCEPTED_REVISION, "Semantic revision")
        equal(semantic["binding"]["source_manifest"], manifest, "Semantic source manifest")
        glb, binary = decode_glb(inputs[INPUT_PATHS[0]])
        root_extra = glb["extras"]["ontokin"]
        equal(root_extra["target_contract"], "ontokin.glb/0.2", "GLB target contract")
        equal(root_extra["program"]["revision"], ACCEPTED_REVISION, "GLB program revision")
        equal(root_extra["program"]["manifest"], manifest, "GLB source manifest")
        equal(root_extra["program"]["entry_source_id"], "entry", "GLB entry source")
        equal(root_extra["source"]["entry_revision"], sources["entry"]["source_revision"], "GLB entry revision")
        for registry in (semantic["binding"]["source_provenance"], root_extra["program"]["sources"]):
            equal(sorted(registry), sorted(sources), "Complete source registry")
            for source_id, source in sources.items():
                for field in ("source_id", "filename", "source_revision", "package_id", "version"):
                    equal(registry[source_id][field], source[field], "Source registry " + field)
        glb_pin = {"bytes": len(inputs[INPUT_PATHS[0]]), "sha256": "sha256:" + digest(inputs[INPUT_PATHS[0]])}
        for field, value in glb_pin.items():
            equal(semantic["binding"]["artifact"][field], value, "Semantic artifact " + field)
        equal(semantic["binding"]["artifact"]["target_contract"], "ontokin.glb/0.2", "Semantic target contract")
        equal(reference["program_revision"], ACCEPTED_REVISION, "Reference program revision")
        equal(reference["source_manifest"], manifest, "Reference source manifest")
        equal(reference["artifact_sha256"], glb_pin["sha256"], "Reference artifact hash")
        equal(payload["schema_version"], "ontokin.source-normal-payload/0.1", "Payload schema")
        equal(payload["binding"]["accepted_program_revision"], ACCEPTED_REVISION, "Payload source revision")
        equal(digest(canonical(payload)), bindings["c214PayloadCanonicalSha256"], "C214 canonical payload digest")
        for label, path in (("glb", INPUT_PATHS[0]), ("bundle", INPUT_PATHS[1]), ("semantic", INPUT_PATHS[2])):
            equal(payload["binding"]["inputs"][label], {"bytes": len(inputs[path]), "sha256": "sha256:" + digest(inputs[path])},
                  "Payload input " + label)
        counts = _check_parts(part_map, semantic, glb, binary, sources)
        planned = {entry["sourcePath"]: entry for entry in part_map["entries"]}
        instances = _unique_rows(array_value(payload["instances"], "Payload instances", 18),
                                 "path", "element_id", "Payload instances")
        geometry = _unique_rows(array_value(reference["geometry"], "Reference parts", 18),
                                "path", "element_id", "Reference parts")
        equal(sorted(instances), sorted(planned), "Payload part set")
        equal(sorted(geometry), sorted(planned), "Reference part set")
        for path, row in planned.items():
            equal(instances[path], {"path": path, "element_id": row["elementId"],
                                   "node": row["glbNode"], "mesh": row["glbMesh"]}, "Payload instance binding")
            equal(geometry[path]["element_id"], row["elementId"], "Reference element identity")
            equal(geometry[path]["definition_id"], row["definitionId"], "Reference definition identity")
        equal(parsed[INPUT_PATHS[6]]["accepted_revision"], ACCEPTED_REVISION, "Preserved source-oracle revision")
        equal(parsed[INPUT_PATHS[7]]["sourcePayloadSha256"], "sha256:" + bindings["c214PayloadCanonicalSha256"],
              "Preserved reopened observation payload digest")
        return {"source_units": len(sources), **counts}
    except (KeyError, IndexError, TypeError, AttributeError, UnicodeError, OverflowError, RecursionError) as exc:
        raise CheckError("SHAPE", "Missing, malformed or unsupported structural input") from exc


def check_package(package_root) -> dict:
    bindings, part_map = load_authority()
    try:
        items = _input_items(bindings)
        inputs = {}
        with SafeRoot(package_root) as root:
            for item in items:
                path = item["packagePath"]
                inputs[path] = root.read(path, item["bytes"], item["sha256"], item["mode"])
        counts = validate_structure(bindings, part_map, inputs)
    except (KeyError, TypeError, AttributeError) as exc:
        raise CheckError("SHAPE", "Invalid trusted input inventory") from exc
    return {
        "schema": SCHEMA, "version": VERSION, "result": "PASS_CPU_AUTHORITY_BINDING",
        "accepted_program_revision": ACCEPTED_REVISION, "authority_repository_base": REPOSITORY_BASE,
        "authority_documents": [{"path": AUTHORITY_DIRECTORY + "/" + name, "bytes": pin[0],
                                 "sha256": pin[1], "mode": pin[2]} for name, pin in AUTHORITY_PINS.items()],
        "inputs": [{key: item[key] for key in ("packagePath", "bytes", "sha256", "mode")} for item in items],
        "checked": counts,
        "limits": {
            "target_starts": 0, "source_evaluations": 0, "exports": 0, "scene_writes": 0,
            "native_receiving_evidence": False, "numeric_geometry_material_pose_validation": False,
            "acceptance_evidence_replayed": False, "target_execution_authorized": False,
            "meaning": "Exact retained authority and structural joins only; no new source or destination acceptance",
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True, help="Extracted C220-or-successor package preserving the eight paths")
    args = parser.parse_args(argv)
    try:
        result = check_package(args.package_root)
    except (CheckError, OSError) as exc:
        result = {"schema": SCHEMA, "version": VERSION, "result": "FAIL_CLOSED",
                  "error": {"code": getattr(exc, "code", "IO"), "message": str(exc)},
                  "target_execution_authorized": False}
        print(json.dumps(result, sort_keys=True, indent=2))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
