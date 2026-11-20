"""Independent, recipe-based fixtures for the C266 public API controls.

No observer, product parser, evaluator, exporter, sidecar or comparator is
imported here. Expected maps are written from the construction identity rules.
The byte-span helpers locate explicitly authored fixture fragments only; they
are not an alternative OntoKin parser or a general validity checker.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path


PACKAGE = "package:example.hinges@1.0.0"
ROOT = Path(__file__).resolve().parents[3]
PROOF = ROOT / "docs/engineering/semantic-export-c210/evidence/proof"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def decode_glb(raw: bytes) -> tuple[dict, bytes]:
    length = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + length])
    bin_length, bin_kind = struct.unpack_from("<II", raw, 20 + length)
    assert bin_kind == 0x004E4942
    return doc, raw[28 + length:28 + length + bin_length]


def encode_glb(doc: dict, binary: bytes = b"") -> bytes:
    raw = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    raw += b" " * (-len(raw) % 4)
    binary += b"\0" * (-len(binary) % 4)
    length = 12 + 8 + len(raw) + 8 + len(binary)
    return (struct.pack("<III", 0x46546C67, 2, length)
            + struct.pack("<II", len(raw), 0x4E4F534A) + raw
            + struct.pack("<II", len(binary), 0x004E4942) + binary)


def program_identity(sources: dict[str, bytes]) -> tuple[dict, str]:
    manifest = {
        "schema_version": "ontokin.bundle/0.1",
        "entry_source_id": "entry",
        "units": [
            {"source_id": "entry", "package_id": None, "version": None,
             "filename": "main.ok", "source_revision": "sha256:" + digest(sources["main.ok"])},
            {"source_id": PACKAGE, "package_id": "example.hinges", "version": "1.0.0",
             "filename": "hinges.ok", "source_revision": "sha256:" + digest(sources["hinges.ok"])},
        ],
    }
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
    return manifest, "sha256:" + digest(b"ontokin.bundle/0.1\0" + canonical)


def _balanced_end(raw: bytes, opening: int, left: int = 123, right: int = 125) -> int:
    depth = 0
    quote = False
    escape = False
    line_comment = False
    i = opening
    while i < len(raw):
        value = raw[i]
        if line_comment:
            if value in (10, 13):
                line_comment = False
        elif quote:
            if escape:
                escape = False
            elif value == 92:
                escape = True
            elif value == 34:
                quote = False
        elif raw[i:i + 2] == b"//":
            line_comment = True
            i += 1
        elif value == 34:
            quote = True
        elif value == left:
            depth += 1
        elif value == right:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise AssertionError("Unbalanced fixture fragment")


def block_span(raw: bytes, marker: str) -> tuple[int, int]:
    start = raw.index(marker.encode("utf-8"))
    return start, _balanced_end(raw, raw.index(b"{", start))


def entry_span(raw: bytes, key: str, search_start: int = 0) -> tuple[int, int]:
    marker = json.dumps(key, ensure_ascii=False).encode("utf-8") + b":"
    start = raw.index(marker, search_start)
    value = raw.index(b"vec3(", start)
    return start, _balanced_end(raw, value + len(b"vec3"), 40, 41)


def witness(sources: dict[str, bytes], filename: str, bounds: tuple[int, int]) -> dict:
    return {"source_id": "entry" if filename == "main.ok" else PACKAGE,
            "source_revision": "sha256:" + digest(sources[filename]),
            "filename": filename, "start_byte": bounds[0], "end_byte": bounds[1]}


@dataclass
class Fixture:
    sources: dict[str, bytes]
    doc: dict
    expected: dict[str, dict]
    binary: bytes = b""

    @property
    def raw(self) -> bytes:
        return encode_glb(self.doc, self.binary)

    def copy(self) -> "Fixture":
        return copy.deepcopy(self)


def _mapping(path: str, element_id: list[str], owner: str | None,
             root: str, steps: list[dict], definition_id: list[str],
             declaration: dict, definition: dict, declaration_id: list[str] | None,
             generated: dict | None, ancestor: str | None) -> dict:
    return {"path": path, "element_id": element_id, "owner_path": owner,
            "root_path": root, "path_steps": steps, "definition_id": definition_id,
            "class_id": "/".join(definition_id), "declaration": declaration,
            "definition": definition, "declaration_definition_id": declaration_id,
            "generated": generated, "generated_ancestor": ancestor}


def derive_recipe_maps(sources: dict[str, bytes], *, root_names: tuple[str, ...],
                       root_keys: tuple[str, ...], memberships: tuple[tuple[str, ...], ...],
                       entry_locations: tuple[tuple[str, int], ...],
                       module_name: str = "KeyedRack", module_key: str = "keyed-rack",
                       package_module_name: str = "Hinges", package_module_key: str = "hinges",
                       scene_key: str = "demo", rack_name: str = "Rack", rack_key: str = "rack",
                       finger_name: str = "Finger", finger_key: str = "finger",
                       blade_name: str = "Blade", blade_key: str = "blade",
                       collection_name: str = "fingers", collection_key: str = "fingers",
                       part_name: str = "blade", part_key: str = "blade",
                       input_name: str = "mounts") -> dict[str, dict]:
    del module_name, package_module_name
    main = sources["main.ok"]
    leaf = sources["hinges.ok"]
    rack_id = ["entry", module_key, "definitions", rack_key]
    finger_id = ["package", "example.hinges", package_module_key, "definitions", finger_key]
    blade_id = ["package", "example.hinges", package_module_key, "definitions", blade_key]
    rack = witness(sources, "main.ok", block_span(main, f'public class {rack_name} @ "{rack_key}"'))
    finger = witness(sources, "hinges.ok", block_span(leaf, f'public class {finger_name} @ "{finger_key}"'))
    blade = witness(sources, "hinges.ok", block_span(leaf, f'private class {blade_name} @ "{blade_key}"'))
    collection = witness(sources, "main.ok", block_span(main, f'public parts {collection_name} @ "{collection_key}"'))
    part = witness(sources, "hinges.ok", block_span(leaf, f'private part {part_name} @ "{part_key}"'))
    input_marker = ("in self." + input_name).encode("utf-8")
    input_start = main.index(input_marker) + 3
    input_witness = witness(sources, "main.ok", (input_start, input_start + len("self." + input_name)))
    expected = {}
    for root_name, root_key, keys, (entry_file, entry_start) in zip(
            root_names, root_keys, memberships, entry_locations, strict=True):
        root_id = [module_key, scene_key, root_key]
        root_steps = [{"kind": "member", "value": root_name}]
        root_decl = witness(sources, "main.ok", block_span(main, f'object {root_name} @ "{root_key}"'))
        expected[root_name] = _mapping(root_name, root_id, None, root_name, root_steps,
                                       rack_id, root_decl, rack, None, None, None)
        collection_path = root_name + "." + collection_name
        collection_id = root_id + [collection_key]
        collection_def = rack_id + [collection_key]
        for key in sorted(keys):
            path = collection_path + "[" + json.dumps(key, ensure_ascii=False) + "]"
            element_id = collection_id + [key]
            steps = root_steps + [{"kind": "member", "value": collection_name},
                                  {"kind": "key", "value": key}]
            generated = {"collection_path": collection_path, "collection_id": collection_id,
                         "collection_definition_id": collection_def, "key": key,
                         "input": input_witness,
                         "input_entry": witness(sources, entry_file,
                                                entry_span(sources[entry_file], key, entry_start)),
                         "unique_declaration_span": False}
            expected[path] = _mapping(path, element_id, root_name, root_name, steps, finger_id,
                                     collection, finger, collection_def, generated, path)
            child_path = path + "." + part_name
            expected[child_path] = _mapping(
                child_path, element_id + [part_key], path, root_name,
                steps + [{"kind": "member", "value": part_name}], blade_id,
                part, blade, finger_id + [part_key], None, path)
    return copy.deepcopy(expected)


def bind_recipe_doc(sources: dict[str, bytes], expected: dict[str, dict], *,
                    module_name: str = "KeyedRack", module_key: str = "keyed-rack",
                    package_module_name: str = "Hinges", package_module_key: str = "hinges") -> dict:
    manifest, revision = program_identity(sources)
    units = {}
    for row in manifest["units"]:
        unit = dict(row)
        unit["module_name"] = module_name if row["source_id"] == "entry" else package_module_name
        unit["module_key"] = module_key if row["source_id"] == "entry" else package_module_key
        units[row["source_id"]] = unit
    source = {"entry_source_id": "entry", "entry_revision": "sha256:" + digest(sources["main.ok"]),
              "uri": "independently-authored-fixture", "provenance": "No source export executed"}
    ontokin = {"target_contract": "ontokin.glb/0.2", "schema_version": "0.2",
               "profile": "construction-0.1", "source": source,
               "program": {"revision": revision, "entry_source_id": "entry", "manifest": manifest,
                           "sources": units, "occurrences": copy.deepcopy(expected)},
               "joints": []}
    nodes = [{"extras": {"ontokin": {"kind": "object", "path": path,
               "element_id": mapping["element_id"], "class_name": mapping["class_id"],
               "program_revision": revision, "source_mapping": copy.deepcopy(mapping)}}}
             for path, mapping in expected.items()]
    return {"asset": {"version": "2.0"}, "extras": {"ontokin": ontokin}, "nodes": nodes}


def original(endpoint: str = "before") -> Fixture:
    sources = {"main.ok": (PROOF / (endpoint + ".main.ok")).read_bytes(),
               "hinges.ok": (PROOF / "hinges.ok").read_bytes()}
    doc, binary = decode_glb((PROOF / (endpoint + ".glb")).read_bytes())
    expected = derive_recipe_maps(sources, root_names=("first", "second"),
        root_keys=("first", "second"),
        memberships=(("lower", "middle", "upper"), ("bottom", "lower", "middle", "upper", "top")),
        entry_locations=(("hinges.ok", 0), ("main.ok", sources["main.ok"].index(b"object second"))))
    return Fixture(sources, doc, expected, binary)


def synthetic(*, first_keys: tuple[str, ...] = ("lower", "middle", "upper"),
              second_keys: tuple[str, ...] = ("bottom", "top"),
              mode: str = "helper_default", unicode_prefix: bool = False,
              renamed: bool = False, key_tokens: bool = False) -> Fixture:
    """Construct known valid source recipes and metadata without running a producer."""
    names = ({"module_name": "ReboundRack", "module_key": "rack.module-2",
              "package_module_name": "Mechanism", "package_module_key": "parts.lib-2",
              "scene_key": "demo.scene-2", "rack_name": "Carrier", "rack_key": "carrier.kind-2",
              "finger_name": "Digit", "finger_key": "digit.kind-2", "blade_name": "Leaf",
              "blade_key": "leaf.kind-2", "collection_name": "digits", "collection_key": "digits.set-2",
              "part_name": "leaf", "part_key": "leaf.part-2", "input_name": "anchors"}
             if renamed else {})
    n = dict(module_name="KeyedRack", module_key="keyed-rack", package_module_name="Hinges",
             package_module_key="hinges", scene_key="demo", rack_name="Rack", rack_key="rack",
             finger_name="Finger", finger_key="finger", blade_name="Blade", blade_key="blade",
             collection_name="fingers", collection_key="fingers", part_name="blade", part_key="blade",
             input_name="mounts")
    n.update(names)
    root_names = ("alpha", "omega") if renamed else ("first", "second")
    root_keys = ("root.alpha-2", "root.omega-2") if renamed else ("first", "second")
    prefix = "// café λ 漢字 🦉 before declarations\n" if unicode_prefix else ""
    def literal(keys: tuple[str, ...]) -> str:
        return "keyed<Vec3<Length>> {\n" + ",\n".join(
            "        " + json.dumps(key) + ": vec3(0[m], 0[m], 0[m])" for key in keys) + "\n    }"
    helper_first = literal(first_keys)
    helper_second = literal(second_keys)
    leaf = prefix + f'''ontokin "0.2";
module {n['package_module_name']} @ "{n['package_module_key']}";
profile "construction-0.1";
public fn members @ "members"(spacing: Length) -> Keyed<Vec3<Length>> {{
    return {helper_first};
}}
public fn override_members @ "override-members"(spacing: Length) -> Keyed<Vec3<Length>> {{
    return {helper_second};
}}
private class {n['blade_name']} @ "{n['blade_key']}" {{
    public site base @ "base" {{
        pose = pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        interface = "hinged.part";
        size = 0[m];
    }}
}}
public class {n['finger_name']} @ "{n['finger_key']}" {{
    public site pivot @ "pivot" {{
        pose = pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        interface = "hinged.part";
        size = 0[m];
    }}
    private part {n['part_name']} @ "{n['part_key']}": {n['blade_name']} {{ }}
    public joint flex @ "flex": hinge {{
        parent = self.pivot;
        child = self.{n['part_name']}.base;
        axis = vec3(0, 0, 1);
        limits = range(-45[deg], 45[deg]);
        initial = 0[rad];
    }}
}}
'''
    leaf_raw = leaf.encode("utf-8")
    default = literal(first_keys) if mode == "direct_default" else "mech.members(1[m])"
    if mode == "final_override":
        default = literal(("discarded",))
    override = "mech.override_members(1[m])" if mode == "helper_override" else literal(second_keys)
    first_override = f"{n['input_name']} = {literal(first_keys)};" if mode == "final_override" else ""
    main = prefix + f'''ontokin "0.2";
module {n['module_name']} @ "{n['module_key']}";
profile "construction-0.1";
import mech @ "mechanics" from "example.hinges" version "1.0.0"
    digest "sha256:{digest(leaf_raw)}";
public class {n['rack_name']} @ "{n['rack_key']}" {{
    public param {n['input_name']} @ "input": Keyed<Vec3<Length>> = {default};
    public parts {n['collection_name']} @ "{n['collection_key']}": mech.{n['finger_name']} for (key, value) in self.{n['input_name']} {{ }}
}}
scene Demo @ "{n['scene_key']}" {{
    object {root_names[0]} @ "{root_keys[0]}": {n['rack_name']} {{ {first_override} }}
    object {root_names[1]} @ "{root_keys[1]}": {n['rack_name']} {{
        {n['input_name']} = {override};
    }}
}}
'''
    sources = {"main.ok": main.encode("utf-8"), "hinges.ok": leaf_raw}
    first_location = (("main.ok", sources["main.ok"].index(b"public param"))
                      if mode == "direct_default" else ("hinges.ok", 0))
    if mode == "final_override":
        first_location = ("main.ok", sources["main.ok"].index(("object " + root_names[0]).encode("utf-8")))
    if mode == "helper_override":
        second_location = ("hinges.ok", leaf_raw.index(b"public fn override_members"))
    else:
        second_location = ("main.ok", sources["main.ok"].index(("object " + root_names[1]).encode("utf-8")))
    expected = derive_recipe_maps(sources, root_names=root_names, root_keys=root_keys,
        memberships=(first_keys, second_keys), entry_locations=(first_location, second_location), **n)
    if key_tokens:
        for mapping in expected.values():
            generated = mapping["generated"]
            if generated is not None:
                row = generated["input_entry"]
                row["end_byte"] = row["start_byte"] + len(json.dumps(generated["key"]).encode("utf-8"))
    doc = bind_recipe_doc(sources, expected, **{k: n[k] for k in
        ("module_name", "module_key", "package_module_name", "package_module_key")})
    return Fixture(sources, doc, expected)


def node_claim(doc: dict, path: str) -> dict:
    return next(n["extras"]["ontokin"] for n in doc["nodes"]
                if n.get("extras", {}).get("ontokin", {}).get("path") == path)


def mapping_copies(doc: dict, path: str, copies: str) -> list[dict]:
    node_map = node_claim(doc, path)["source_mapping"]
    program_map = doc["extras"]["ontokin"]["program"]["occurrences"][path]
    return {"node": [node_map], "program": [program_map], "both": [node_map, program_map]}[copies]
