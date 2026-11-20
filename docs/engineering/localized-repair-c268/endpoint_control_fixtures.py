"""Independent C268 byte recipes and fixed C260 expectations.

No new reader, observer, compiler, exporter, sidecar, or motion output supplies
expected values. The previously independent C266 helper is used only to author
the explicit provenance of the different-size paired recipe.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import struct
import sys
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROOF = "docs/engineering/semantic-export-c210/evidence/proof"
HISTORICAL = {
    "before.main.ok": (1708, "73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123"),
    "after.main.ok": (1708, "443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a"),
    "hinges.ok": (1911, "1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a"),
    "before.glb": (185276, "d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534"),
    "after.glb": (185236, "05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8"),
}
DEPENDENCIES = {
    "localized-repair-c267/hinge_compare.py": (12382, "9b2899d95471546a25a8a7e5ed9d9ac2a1e42854c31808d4e68aff2582686b58"),
    "localized-repair-c266/hinge_binding.py": (17639, "8f6b26f0bedad335b069975d0491e5565a25f0793b3bc48802e90d3993aa0d0a"),
    "localized-repair-c265/source_hinges.py": (38229, "70d5e5b6247347bf44eaa3be0bc9c91b13f10d4717b4b32261eaebad75987132"),
    "localized-repair-c261/hinge_glb.py": (14036, "6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08"),
    "localized-repair-c257/ownership.py": (35942, "c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1"),
}
RECIPE_PIN = (17102, "fc675e5da709a1f67892d929d90701833a62dd55f6fd0b9798b1c95496fca983")
DEG45 = float(Fraction(45) * Fraction.from_float(float.fromhex("0x1.921fb54442d18p+1")) / 180)
FINGER_DEFINITION = ["package", "example.hinges", "hinges", "definitions", "finger"]
BLADE_DEFINITION = ["package", "example.hinges", "hinges", "definitions", "blade"]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_module(name, path, expected=None):
    if expected is not None:
        raw = path.read_bytes()
        assert (len(raw), digest(raw)) == expected, "Changed pinned control dependency: " + str(path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def pins(endpoint):
    return {logical: {"path": PROOF + "/" + filename, "bytes": HISTORICAL[filename][0],
                      "sha256": HISTORICAL[filename][1]}
            for logical, filename in (("main.ok", endpoint + ".main.ok"),
                                      ("hinges.ok", "hinges.ok"), ("artifact", endpoint + ".glb"))}


def originals():
    out = {}
    for name, expected in HISTORICAL.items():
        raw = (ROOT / PROOF / name).read_bytes()
        assert (len(raw), digest(raw)) == expected, "Changed frozen source: " + name
        out[name] = raw
    return out


def install(root, data=None):
    data = originals() if data is None else data
    destination = root / PROOF
    destination.mkdir(parents=True, exist_ok=True)
    for name, raw in data.items():
        (destination / name).write_bytes(raw)
    return destination


def expected_hinges(*, axis=(0, 0, 1), initial=0):
    """Eight occurrences spelled out by the original two literal memberships."""
    result = {}
    for root, keys in (("first", ("lower", "middle", "upper")),
                       ("second", ("bottom", "lower", "middle", "upper", "top"))):
        for key in keys:
            path = root + '.fingers[' + json.dumps(key) + ']'
            owner = ["keyed-rack", "demo", root, "fingers", key]
            result[path + ".flex"] = {
                "id": owner + ["flex"], "definitionId": FINGER_DEFINITION + ["flex"],
                "path": path + ".flex", "name": "flex", "key": "flex", "kind": "hinge",
                "ownerId": owner, "ownerDefinitionId": FINGER_DEFINITION,
                "axis": list(axis), "limits": [-DEG45, DEG45], "initial": initial,
                "parentSite": {"id": owner + ["pivot"], "definitionId": FINGER_DEFINITION + ["pivot"],
                    "objectId": owner, "objectDefinitionId": FINGER_DEFINITION,
                    "path": path + ".pivot", "name": "pivot", "key": "pivot"},
                "childSite": {"id": owner + ["blade", "base"], "definitionId": BLADE_DEFINITION + ["base"],
                    "objectId": owner + ["blade"], "objectDefinitionId": BLADE_DEFINITION,
                    "path": path + ".blade.base", "name": "base", "key": "base"},
            }
    return copy.deepcopy(result)


def decode_glb(raw):
    count = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + count])
    binary_size, kind = struct.unpack_from("<II", raw, 20 + count)
    assert kind == 0x004E4942
    return document, raw[28 + count:28 + count + binary_size]


def encode_glb(document, binary):
    raw = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()
    raw += b" " * (-len(raw) % 4)
    binary += b"\0" * (-len(binary) % 4)
    return (struct.pack("<III", 0x46546C67, 2, 28 + len(raw) + len(binary))
            + struct.pack("<II", len(raw), 0x4E4F534A) + raw
            + struct.pack("<II", len(binary), 0x004E4942) + binary)


def program_identity(sources):
    manifest = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": [
        {"source_id": "entry", "package_id": None, "version": None, "filename": "main.ok",
         "source_revision": "sha256:" + digest(sources["main.ok"])},
        {"source_id": "package:example.hinges@1.0.0", "package_id": "example.hinges", "version": "1.0.0",
         "filename": "hinges.ok", "source_revision": "sha256:" + digest(sources["hinges.ok"])},
    ]}
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return manifest, "sha256:" + digest(b"ontokin.bundle/0.1\0" + canonical)


def paired_change(endpoint="before", *, same_size):
    """Change real source and real GLB claims, updating required provenance."""
    frozen = originals()
    original_sources = {"main.ok": frozen[endpoint + ".main.ok"], "hinges.ok": frozen["hinges.ok"]}
    sources = dict(original_sources)
    old, new = ((b"axis = vec3(0, 0, 1);", b"axis = vec3(0, 1, 0);") if same_size else
                (b"initial = 0[rad];", b"initial = 0.25[rad];"))
    assert sources["hinges.ok"].count(old) == 1
    sources["hinges.ok"] = sources["hinges.ok"].replace(old, new)
    sources["main.ok"] = sources["main.ok"].replace(digest(original_sources["hinges.ok"]).encode(),
                                                   digest(sources["hinges.ok"]).encode())
    manifest, revision = program_identity(sources)
    raw = frozen[endpoint + ".glb"]
    if same_size:
        # Equal-width edits preserve every source span and GLB chunk length.
        for name in ("main.ok", "hinges.ok"):
            raw = raw.replace(digest(original_sources[name]).encode(), digest(sources[name]).encode())
        raw = raw.replace(program_identity(original_sources)[1].encode(), revision.encode())
        assert raw.count(b'"axis":[0.0,0.0,1.0]') == 8
        raw = raw.replace(b'"axis":[0.0,0.0,1.0]', b'"axis":[0.0,1.0,0.0]')
        assert len(raw) == len(frozen[endpoint + ".glb"])
        expected = expected_hinges(axis=(0, 1, 0))
    else:
        # A longer initial expression changes declaration spans. The pinned
        # independent recipe helper rewrites the explicit object provenance.
        base = load_module("c268_independent_c266_recipe", HERE.parent /
                           "localized-repair-c266/binding_control_fixtures.py", RECIPE_PIN)
        objects = base.derive_recipe_maps(sources, root_names=("first", "second"),
            root_keys=("first", "second"),
            memberships=(("lower", "middle", "upper"), ("bottom", "lower", "middle", "upper", "top")),
            entry_locations=(("hinges.ok", 0), ("main.ok", sources["main.ok"].index(b"object second"))))
        provenance = base.bind_recipe_doc(sources, objects)
        document, binary = decode_glb(raw)
        metadata = document["extras"]["ontokin"]
        metadata["source"]["entry_revision"] = "sha256:" + digest(sources["main.ok"])
        metadata["program"].update(provenance["extras"]["ontokin"]["program"])
        for node in document["nodes"]:
            claim = node.get("extras", {}).get("ontokin", {})
            if claim.get("kind") == "object":
                claim["source_mapping"] = copy.deepcopy(objects[claim["path"]])
                claim["program_revision"] = revision
        for joint in metadata["joints"]:
            joint["initial"] = 0.25
        raw = encode_glb(document, binary)
        assert len(raw) != len(frozen[endpoint + ".glb"])
        expected = expected_hinges(initial=0.25)
    assert decode_glb(raw)[0]["extras"]["ontokin"]["program"]["manifest"] == manifest
    return sources, raw, expected
