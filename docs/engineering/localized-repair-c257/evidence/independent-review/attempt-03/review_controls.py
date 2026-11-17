#!/usr/bin/env python3
"""Independent C257 controls. No producer-sidecar or expected semantic imports."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
REPO = AUDIT.parents[1] / "c257-review-final"
CODE = REPO / "docs/engineering/localized-repair-c257/ownership.py"
PROOF = REPO / "docs/engineering/semantic-export-c210/evidence/proof"
spec = importlib.util.spec_from_file_location("independent_review_c257", CODE)
reader = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reader
spec.loader.exec_module(reader)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sources(endpoint="before"):
    return {"main.ok": (PROOF / (endpoint + ".main.ok")).read_bytes(),
            "hinges.ok": (PROOF / "hinges.ok").read_bytes()}


ORIGINAL = sources()
RAW = (PROOF / "before.glb").read_bytes()
JSON_LENGTH = struct.unpack_from("<I", RAW, 12)[0]
DOCUMENT = json.loads(RAW[20:20 + JSON_LENGTH])
BIN_HEADER = 20 + JSON_LENGTH
BIN_LENGTH = struct.unpack_from("<I", RAW, BIN_HEADER)[0]
BIN = RAW[BIN_HEADER + 8:BIN_HEADER + 8 + BIN_LENGTH]
BASELINE = json.loads((AUDIT / "ARTIFACT-BASELINE.json").read_text())["endpoints"][0]
BASE_ROWS = {row["path"]: row for row in BASELINE["records"]}
RESULTS = []


def pack(document, binary=BIN):
    encoded = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode()
    return pack_json(encoded, binary)


def pack_json(encoded, binary=BIN):
    encoded += b" " * (-len(encoded) % 4)
    binary += b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(encoded) + 8 + len(binary)
    return (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(encoded), b"JSON")
            + encoded + struct.pack("<I4s", len(binary), b"BIN\0") + binary)


def artifact_change(change):
    d = deepcopy(DOCUMENT)
    change(d)
    return pack(d)


def repin(src):
    result = dict(src)
    result["main.ok"] = re.sub(rb'digest "sha256:[0-9a-f]{64}"',
                               b'digest "sha256:' + sha(result["hinges.ok"]).encode() + b'"',
                               result["main.ok"])
    return result


def source_change(file, old, new, count=1):
    src = dict(ORIGINAL)
    assert src[file].count(old) >= count
    src[file] = src[file].replace(old, new, count)
    return repin(src) if file == "hinges.ok" else src


def binding(src):
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": "main.ok", "source_revision": "sha256:" + sha(src["main.ok"])},
             {"source_id": "package:example.hinges@1.0.0", "package_id": "example.hinges",
              "version": "1.0.0", "filename": "hinges.ok", "source_revision": "sha256:" + sha(src["hinges.ok"])}]
    manifest = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": units}
    encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return manifest, "sha256:" + sha(b"ontokin.bundle/0.1\0" + encoded)


def metadata(d, index=2):
    return d["nodes"][index]["extras"]["ontokin"]


def program(d):
    return d["extras"]["ontokin"]["program"]


def check(flag, message):
    if not flag:
        raise AssertionError(message)


def path_get(root, pointer):
    value = root
    for piece in pointer.split("/")[1:]:
        piece = piece.replace("~1", "/").replace("~0", "~")
        value = value[int(piece)] if isinstance(value, list) else value[piece]
    return value


def claims_are_partial(result):
    check(result["completeC255Semantic"] is False, "complete semantic claim")
    check(result["executionAllowed"] is False and result["realTrialSuccess"] is None, "execution/trial claim")
    check(not any(x in result for x in ["semantic", "follows", "hinges", "poses", "geometry", "cleanRebuild", "acceptedRevision"]), "unimplemented field fabricated")


def same_graph(result):
    actual = {x["path"]: (x["id"], x["definitionId"], x["ownerPath"], x["ownerId"])
              for x in result["records"]}
    wanted = {path: (x["id"], x["definitionId"], x["ownerPath"], x["ownerId"])
              for path, x in BASE_ROWS.items()}
    check(actual == wanted, "independent original ownership/identity graph differs")
    check((result["objectCount"], result["rootCount"], result["edgeCount"]) == (18, 2, 16), "counts")
    claims_are_partial(result)


def origins_resolve(result, src):
    count = 0
    def walk(value):
        nonlocal count
        if isinstance(value, dict):
            if {"file", "startByte", "endByteExclusive"} <= set(value):
                raw = src[value["file"]]
                a, b = value["startByte"], value["endByteExclusive"]
                check(type(a) is int and type(b) is int and 0 <= a < b <= len(raw), "origin bounds")
                raw[a:b].decode("utf-8")
                count += 1
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(result)
    for row in result["records"]:
        origins = row.get("origin", row.get("sourceOrigin"))
        tokens = [json.loads(src[x["file"]][x["startByte"]:x["endByteExclusive"]])
                  for x in origins["identityKeys"]]
        check(tokens == row["id"], "identity token byte origins do not produce full ID")
        declaration = origins["declaration"]
        text = src[declaration["file"]][declaration["startByte"]:declaration["endByteExclusive"]]
        check(re.match(rb'(?:public |private )?(?:object|parts|part)\s', text) is not None, "declaration origin is not declaration")
        definition = origins["definition"]
        text = src[definition["file"]][definition["startByte"]:definition["endByteExclusive"]]
        found = re.match(rb'(?:public |private )?class [A-Za-z_][A-Za-z_0-9]* @ "([^"]+)"', text)
        check(found and found.group(1).decode() == row["definitionId"][-1], "definition byte origin")
    return count


def artifact_origins(result, document):
    for row in result["records"]:
        for key in ["nodeOwner", "sourceMappingOwner", "programOccurrenceOwner"]:
            check(path_get(document, row["origins"][key]) == row["claims"][key], "owner JSON pointer")
        check(path_get(document, row["origins"]["identity"]) == row["id"], "identity JSON pointer")
        check(path_get(document, row["origins"]["definition"]) == row["definitionId"], "definition JSON pointer")
    claims_are_partial(result)


def record(name, function, expected="pass", validator=None, src=None, raw=None, reason=""):
    row = {"name": name, "expected": expected, "reason": reason}
    if src is not None:
        row["sourceHashes"] = {k: sha(v) if isinstance(v, bytes) else type(v).__name__ for k, v in src.items()} if isinstance(src, dict) else type(src).__name__
    if raw is not None:
        row["artifactSha256"] = sha(raw) if isinstance(raw, bytes) else type(raw).__name__
        row["artifactBytes"] = len(raw) if hasattr(raw, "__len__") else None
    try:
        value = function()
        if expected == "refuse":
            raise AssertionError("operation returned success where explicit refusal was required")
        if validator:
            validator(value)
        row.update(status="PASS", output=value)
    except reader.Fault as exc:
        row.update(status="PASS" if expected == "refuse" else "FAIL", fault={"type": type(exc).__name__, "code": exc.code, "detail": exc.detail})
    except BaseException as exc:
        row.update(status="FAIL", fault={"type": type(exc).__name__, "message": str(exc)}, traceback=traceback.format_exc())
    RESULTS.append(row)


def source_test(name, src, expected="pass", validator=None, reason=""):
    record(name, lambda: reader.observe_source_ownership(src), expected, validator, src=src, reason=reason)


def artifact_test(name, raw, expected="refuse", compare=True, validator=None, reason=""):
    record(name, lambda: reader.compare_ownership(ORIGINAL, raw) if compare else reader.observe_glb_ownership(raw),
           expected, validator, src=ORIGINAL if compare else None, raw=raw, reason=reason)


def block_span(raw, prefix):
    check(raw.count(prefix) == 1, "independent fixture declaration not unique")
    start = raw.index(prefix)
    at = raw.index(b"{", start)
    depth = 0
    for end in range(at, len(raw)):
        if raw[end] == ord("{"):
            depth += 1
        elif raw[end] == ord("}"):
            depth -= 1
            if depth == 0:
                return start, end + 1
    raise AssertionError("independent fixture unclosed declaration")


def source_span(src, filename, prefix):
    start, end = block_span(src[filename], prefix)
    return {"source_id": "entry" if filename == "main.ok" else "package:example.hinges@1.0.0",
            "filename": filename, "source_revision": "sha256:" + sha(src[filename]), "start_byte": start, "end_byte": end}


def moved_source():
    src = dict(ORIGINAL)
    start, end = block_span(src["hinges.ok"], b"private part blade")
    src["hinges.ok"] = src["hinges.ok"][:start] + src["hinges.ok"][end:]
    src["hinges.ok"] = src["hinges.ok"].replace(b"private class Blade", b"public class Blade")
    _, rack_end = block_span(src["main.ok"], b"public class Rack")
    part = b'    private part blade @ "blade": mech.Blade {\n        length = self.finger_length;\n        tint = rgba(0.2, 0.6, 0.9, 1);\n    }\n'
    src["main.ok"] = src["main.ok"][:rack_end - 1] + part + src["main.ok"][rack_end - 1:]
    return repin(src)


def moved_graph(result):
    check((result["objectCount"], result["rootCount"], result["edgeCount"]) == (12, 2, 10), "moved graph counts")
    rows = {x["path"]: x for x in result["records"]}
    check(set(rows) == {p for p in BASE_ROWS if not p.endswith(".blade")} | {"first.blade", "second.blade"}, "moved paths")
    for root in ["first", "second"]:
        x = rows[root + ".blade"]
        check(x["ownerPath"] == root and x["ownerId"] == rows[root]["id"] and x["id"] == rows[root]["id"] + ["blade"], "moved lexical owner")
    claims_are_partial(result)


def moved_artifact(src):
    """Build independent changed metadata from declarations, never reader output."""
    d = deepcopy(DOCUMENT)
    old_nodes = {n["name"]: n for n in d["nodes"]}
    keep = [p for p in old_nodes if not p.endswith(".blade")] + ["first.blade", "second.blade"]
    manifest, revision = binding(src)
    old_revision = program(d)["revision"]
    replacement = {old_revision: revision,
                   "sha256:" + sha(ORIGINAL["main.ok"]): "sha256:" + sha(src["main.ok"]),
                   "sha256:" + sha(ORIGINAL["hinges.ok"]): "sha256:" + sha(src["hinges.ok"])}
    def replace(v):
        if isinstance(v, dict):
            return {k: replace(x) for k, x in v.items()}
        if isinstance(v, list):
            return [replace(x) for x in v]
        return replacement.get(v, v) if isinstance(v, str) else v
    d = replace(d)
    old_nodes = {n["name"]: n for n in d["nodes"]}
    nodes, occurrences = [], {}
    for path in keep:
        root = path.split(".")[0]
        is_blade = path.endswith(".blade")
        original_path = root + '.fingers["lower"].blade' if is_blade else path
        node = deepcopy(old_nodes[original_path])
        meta = node["extras"]["ontokin"]
        row = BASE_ROWS[original_path]
        oid = BASE_ROWS[root]["id"] + ["blade"] if is_blade else row["id"]
        owner = root if is_blade else row["ownerPath"]
        node["name"] = path
        meta.update(path=path, owner=owner, element_id=oid, program_revision=revision)
        mapping = meta["source_mapping"]
        mapping.update(path=path, owner_path=owner, element_id=oid, root_path=root)
        if len(oid) == 3:
            declaration = source_span(src, "main.ok", ("object " + root).encode())
            definition = source_span(src, "main.ok", b"public class Rack")
        elif is_blade:
            declaration = source_span(src, "main.ok", b"private part blade")
            definition = source_span(src, "hinges.ok", b"public class Blade")
            mapping.update(generated=None, generated_ancestor=None,
                           declaration_definition_id=["entry", "keyed-rack", "definitions", "rack", "blade"],
                           path_steps=[{"kind": "member", "value": root}, {"kind": "member", "value": "blade"}])
        else:
            declaration = source_span(src, "main.ok", b"public parts fingers")
            definition = source_span(src, "hinges.ok", b"public class Finger")
        mapping.update(declaration=declaration, definition=definition)
        occurrences[path] = deepcopy(mapping)
        nodes.append(node)
    d["nodes"] = nodes
    d["scenes"][0]["nodes"] = list(range(len(nodes)))
    d.pop("animations", None)
    program(d).update(manifest=manifest, revision=revision, occurrences=occurrences)
    return pack(d)


def run():
    for endpoint in ["before", "after"]:
        src = sources(endpoint)
        raw = (PROOF / (endpoint + ".glb")).read_bytes()
        record("original-source-" + endpoint, lambda s=src: reader.observe_source_ownership(s), validator=same_graph, src=src)
        record("original-compare-" + endpoint, lambda s=src, r=raw: reader.compare_ownership(s, r), validator=same_graph, src=src, raw=raw)
        record("original-bound-" + endpoint, lambda e=endpoint: reader.read_bound_endpoint(REPO, e), validator=lambda r: (same_graph(r), check(r["historicalInputsBound"] is True, "historical admission")), src=src, raw=raw)
    record("source-origin-resolution", lambda: reader.observe_source_ownership(ORIGINAL), validator=lambda r: check(origins_resolve(r, ORIGINAL) >= 150, "source origins missing"), src=ORIGINAL)
    record("artifact-origin-resolution", lambda: reader.observe_glb_ownership(RAW), validator=lambda r: artifact_origins(r, DOCUMENT), raw=RAW)
    utf8 = dict(ORIGINAL); utf8["main.ok"] = "// café 😀 ownership comment\n".encode() + utf8["main.ok"]
    source_test("utf8-byte-origins", utf8, validator=lambda r: (same_graph(r), origins_resolve(r, utf8)))
    comments = dict(ORIGINAL); comments["main.ok"] = b'// object fake @ "fake": Rack { private part trap @ "trap": Rack {} }\n' + comments["main.ok"]
    source_test("comment-declaration-decoy", comments, validator=same_graph)
    follow = source_change("hinges.ok", b"parent = self.parent_frame;", b"parent = world;")
    source_test("follow-parent-is-not-owner", follow, validator=same_graph)
    joint = source_change("hinges.ok", b"parent = self.pivot;", b"parent = self.blade.base;")
    source_test("hinge-parent-is-not-owner", joint, validator=same_graph)
    parent_frame = source_change("main.ok", b"parent_frame = self.frame;", b"parent_frame = world;")
    source_test("parent-frame-is-not-owner", parent_frame, validator=same_graph)
    root_key = source_change("main.ok", b'object first @ "first"', b'object first @ "alpha"')
    source_test("root-stable-key-mutation", root_key, validator=lambda r: check(all(x["id"][2] == "alpha" for x in r["records"] if x["path"].startswith("first")), "root ID did not follow source key"))
    record("changed-source-old-artifact", lambda: reader.compare_ownership(root_key, RAW), "refuse", src=root_key, raw=RAW)
    dotted = source_change("hinges.ok", b'"lower":', b'"low.er":')
    source_test("literal-dotted-key", dotted, validator=lambda r: check(any(x["path"] == 'first.fingers["low.er"]' and x["id"][-1] == "low.er" for x in r["records"]), "literal key was split"))
    ordinary = source_change("hinges.ok", b'part blade @ "blade"', b'part blade @ "blade-new"')
    source_test("ordinary-part-key", ordinary, validator=lambda r: check(all(x["id"][-1] == "blade-new" for x in r["records"] if x["path"].endswith(".blade")), "ordinary identity mutation absent"))
    clskey = source_change("hinges.ok", b'class Finger @ "finger"', b'class Finger @ "digit"')
    source_test("definition-key-separate-from-occurrence", clskey, validator=lambda r: check(all(x["definitionId"][-1] == "digit" and x["id"] == BASE_ROWS[x["path"]]["id"] for x in r["records"] if x["kind"] == "generated-part"), "definition/occurrence conflated"))
    default_public = source_change("hinges.ok", b"public class Finger", b"class Finger")
    source_test("module-class-default-public", default_public, validator=same_graph, reason="OK-LANG-002 section 3 module visibility defaults public")
    helper_public = source_change("hinges.ok", b"public fn three_mounts", b"fn three_mounts")
    source_test("module-function-default-public", helper_public, validator=same_graph, reason="OK-LANG-002 section 3 module visibility defaults public")
    moved = moved_source()
    source_test("supported-source-ownership-move", moved, validator=moved_graph)
    record("moved-source-original-artifact", lambda: reader.compare_ownership(moved, RAW), "refuse", src=moved, raw=RAW)
    changed_glb = moved_artifact(moved)
    (HERE / "moved.main.ok").write_bytes(moved["main.ok"])
    (HERE / "moved.hinges.ok").write_bytes(moved["hinges.ok"])
    (HERE / "moved-ownership.glb").write_bytes(changed_glb)
    record("joint-source-artifact-ownership-move", lambda: reader.compare_ownership(moved, changed_glb), validator=moved_graph, src=moved, raw=changed_glb)
    unresolved = dict(moved); unresolved["main.ok"] = unresolved["main.ok"].replace(b": mech.Blade", b": Blade")
    source_test("cross-module-unqualified-class-refusal", unresolved, "refuse")
    private = dict(moved); private["hinges.ok"] = private["hinges.ok"].replace(b"public class Blade", b"private class Blade"); private = repin(private)
    source_test("cross-module-private-class-refusal", private, "refuse")
    source_test("duplicate-root-key", source_change("main.ok", b'object second @ "second"', b'object second @ "first"'), "refuse")
    source_test("duplicate-generated-key", source_change("hinges.ok", b'"upper":', b'"middle":'), "refuse")
    source_test("unknown-class", source_change("main.ok", b": mech.Finger", b": mech.Unknown"), "refuse")
    source_test("unknown-shape-parameter", source_change("main.ok", b"in self.mounts", b"in self.missing"), "refuse")
    source_test("nested-shape-override", source_change("main.ok", b'fingers["middle"].length = 0.65[m];', b'fingers["middle"].mounts = keyed<Vec3<Length>> { "x": vec3(0[m],0[m],0[m]) };'), "refuse")
    source_test("unresolved-key-expression", source_change("main.ok", b"mech.three_mounts(0.6[m])", b"self.unknown"), "refuse")
    recursive = source_change("hinges.ok", b"geometry = sphere(0.06[m]);", b'private part loop @ "loop": Finger {}\n    geometry = sphere(0.06[m]);')
    source_test("composition-cycle", recursive, "refuse")
    source_test("import-digest-mismatch", source_change("main.ok", b'"sha256:1516', b'"sha256:2516'), "refuse")
    for name, src in [("source-map-null", None), ("source-map-list", []), ("source-file-string", {"main.ok": "not bytes", "hinges.ok": ORIGINAL["hinges.ok"]}), ("source-dependency-absent", {"main.ok": ORIGINAL["main.ok"]}), ("source-extra-file", {**ORIGINAL, "extra.ok": b"unused"})]:
        source_test(name, src, "refuse")
    oversized = dict(ORIGINAL); oversized["main.ok"] += b" " * (65537 - len(oversized["main.ok"]))
    source_test("source-byte-limit", oversized, "refuse")
    too_deep = source_change("main.ok", b"box(vec3", b"box(" + b"(" * 33 + b"vec3")
    source_test("source-depth-limit", too_deep, "refuse")

    def owner_node(d): metadata(d)["owner"] = "second"
    changed = artifact_change(owner_node)
    artifact_test("node-owner-observed-as-changed", changed, "pass", False, lambda r: check(next(x for x in r["records"] if x["node"] == 2)["claims"]["nodeOwner"] == "second", "raw changed owner hidden"))
    artifact_test("node-owner-mismatch", changed)
    artifact_test("mapping-owner-mismatch", artifact_change(lambda d: metadata(d)["source_mapping"].__setitem__("owner_path", "second")))
    artifact_test("program-owner-mismatch", artifact_change(lambda d: program(d)["occurrences"][metadata(d)["path"]].__setitem__("owner_path", "second")))
    for field in ["node", "mapping", "program"]:
        def omit(d, field=field):
            row = metadata(d, 0)
            target, key = (row, "owner") if field == "node" else (row["source_mapping"], "owner_path") if field == "mapping" else (program(d)["occurrences"][row["path"]], "owner_path")
            del target[key]
        artifact_test("root-owner-absent-" + field, artifact_change(omit), compare=False)
    artifact_test("root-owner-self-cycle", artifact_change(lambda d: metadata(d, 0).__setitem__("owner", "first")))
    artifact_test("unknown-owner-path", artifact_change(lambda d: metadata(d).__setitem__("owner", "ghost")))
    artifact_test("unknown-occurrence-id", artifact_change(lambda d: metadata(d)["element_id"].__setitem__(-1, "ghost")))
    artifact_test("duplicate-occurrence-id", artifact_change(lambda d: metadata(d).__setitem__("element_id", metadata(d, 3)["element_id"])), compare=False)
    artifact_test("definition-id-as-occurrence", artifact_change(lambda d: metadata(d).__setitem__("element_id", metadata(d)["source_mapping"]["definition_id"])))
    artifact_test("swapped-occurrence-ids", artifact_change(lambda d: (metadata(d).__setitem__("element_id", deepcopy(metadata(d, 3)["element_id"])), metadata(d, 3).__setitem__("element_id", deepcopy(metadata(DOCUMENT)["element_id"])))))
    artifact_test("duplicate-path", artifact_change(lambda d: metadata(d).__setitem__("path", metadata(d, 3)["path"])), compare=False)
    artifact_test("unknown-definition-id", artifact_change(lambda d: metadata(d)["source_mapping"]["definition_id"].__setitem__(-1, "unknown")))
    artifact_test("missing-program-occurrence", artifact_change(lambda d: program(d)["occurrences"].pop(metadata(d)["path"])), compare=False)
    artifact_test("extra-program-occurrence", artifact_change(lambda d: program(d)["occurrences"].__setitem__("ghost", deepcopy(program(d)["occurrences"]["first"]))), compare=False)
    artifact_test("mapping-identity-disagreement", artifact_change(lambda d: metadata(d)["source_mapping"]["element_id"].__setitem__(-1, "unknown")))
    artifact_test("program-identity-disagreement", artifact_change(lambda d: program(d)["occurrences"][metadata(d)["path"]]["element_id"].__setitem__(-1, "unknown")))
    artifact_test("source-span-offset-change", artifact_change(lambda d: metadata(d)["source_mapping"]["declaration"].__setitem__("start_byte", 604)))
    artifact_test("source-span-filename-change", artifact_change(lambda d: metadata(d)["source_mapping"]["declaration"].__setitem__("filename", "hinges.ok")))
    artifact_test("source-span-source-id-change", artifact_change(lambda d: metadata(d)["source_mapping"]["declaration"].__setitem__("source_id", "unbound")))
    artifact_test("source-span-float-offset", artifact_change(lambda d: metadata(d)["source_mapping"]["declaration"].__setitem__("start_byte", float(metadata(d)["source_mapping"]["declaration"]["start_byte"]))), reason="Source byte-offset metadata must be integers rather than silently equal floats")
    artifact_test("manifest-source-hash-change", artifact_change(lambda d: program(d)["manifest"]["units"][0].__setitem__("source_revision", "sha256:" + "0" * 64)))
    artifact_test("node-program-revision-change", artifact_change(lambda d: metadata(d).__setitem__("program_revision", "sha256:" + "0" * 64)))
    artifact_test("source-mapping-class-id-disagreement", artifact_change(lambda d: metadata(d)["source_mapping"].__setitem__("class_id", "entry/other/definitions/class")), reason="Named source mapping definition claims must not conflict with joined definition ID")
    artifact_test("program-source-revision-disagreement", artifact_change(lambda d: program(d)["sources"]["entry"].__setitem__("source_revision", "sha256:" + "0" * 64)), reason="Complete source association must not ignore contradictory program source record")

    for label, value in [("null", None), ("list", []), ("bool", True), ("number", 1), ("dict", {})]:
        artifact_test("owner-shape-" + label, artifact_change(lambda d, v=value: metadata(d).__setitem__("owner", v)), "pass" if value is None else "refuse", False,
                      (lambda r: check(next(x for x in r["records"] if x["node"] == 2)["claims"]["nodeOwner"] is None, "null actual claim")) if value is None else None)
    for field in ["extras", "mapping", "program", "occurrence"]:
        def shape(d, field=field):
            if field == "extras": d["nodes"][2]["extras"] = []
            elif field == "mapping": metadata(d)["source_mapping"] = []
            elif field == "program": d["extras"]["ontokin"]["program"] = []
            else: program(d)["occurrences"][metadata(d)["path"]] = []
        artifact_test("container-shape-" + field, artifact_change(shape), compare=False)
    artifact_test("transform-change-not-ownership", artifact_change(lambda d: d["nodes"][2].__setitem__("translation", [123, 456, 789])), "pass", True, same_graph)
    artifact_test("transform-hierarchy-not-ownership", artifact_change(lambda d: d["nodes"][0].__setitem__("children", [2, 3, 4])), "pass", True, same_graph)
    artifact_test("scene-root-order-not-ownership", artifact_change(lambda d: d["scenes"][0]["nodes"].reverse()), "pass", True, same_graph)
    artifact_test("truncated-glb", RAW[:-1], compare=False)
    artifact_test("invalid-glb-version", RAW[:4] + struct.pack("<I", 1) + RAW[8:], compare=False)
    artifact_test("oversized-glb", b"x" * (4 * 1024 * 1024 + 1), compare=False)
    artifact_test("duplicate-json-key", pack_json(b'{"asset":{"version":"2.0"},"asset":{"version":"2.0"}}'), compare=False)
    artifact_test("json-overlong-integer", pack_json(b'{"asset":{"version":"2.0"},"number":' + b"1" * 100 + b"}"), compare=False)
    artifact_test("json-deep-structure", pack_json(b"[" * 1100 + b"0" + b"]" * 1100), compare=False)
    artifact_test("node-count-limit", artifact_change(lambda d: d.__setitem__("nodes", d["nodes"] * 8)), compare=False)
    artifact_test("required-extension", artifact_change(lambda d: d.__setitem__("extensionsRequired", ["UNKNOWN_ownership"])), compare=False)

    stage = HERE / "bound-stage"
    target = stage / "docs/engineering/semantic-export-c210/evidence/proof"
    target.mkdir(parents=True, exist_ok=True)
    for name in ["before.main.ok", "hinges.ok", "before.glb"]:
        shutil.copy2(PROOF / name, target / name)
    bound = target / "before.glb"
    mutated = bytearray(RAW); mutated[-8] ^= 1; bound.write_bytes(mutated)
    record("bound-artifact-byte-change", lambda: reader.read_bound_endpoint(stage, "before"), "refuse", src=ORIGINAL, raw=bytes(mutated))
    bound.write_bytes(RAW)
    original_entry = (target / "before.main.ok").read_bytes()
    (target / "before.main.ok").write_bytes(original_entry.replace(b"0.65[m]", b"0.66[m]"))
    record("bound-source-byte-change", lambda: reader.read_bound_endpoint(stage, "before"), "refuse", src={**ORIGINAL, "main.ok": (target / "before.main.ok").read_bytes()}, raw=RAW)
    record("unknown-bound-endpoint", lambda: reader.read_bound_endpoint(REPO, "unknown"), "refuse")


def correction_symmetry():
    artifact_test("program-class-id-disagreement", artifact_change(lambda d: program(d)["occurrences"][metadata(d)["path"]].__setitem__("class_id", "entry/other/definitions/class")))
    artifact_test("mapping-class-id-absent", artifact_change(lambda d: metadata(d)["source_mapping"].pop("class_id")))
    for mapping_name, span_name, offset_name in [("node", "definition", "end_byte"),
                                                 ("program", "declaration", "start_byte"),
                                                 ("program", "definition", "end_byte")]:
        def change(d, mapping_name=mapping_name, span_name=span_name, offset_name=offset_name):
            mapping = metadata(d)["source_mapping"] if mapping_name == "node" else program(d)["occurrences"][metadata(d)["path"]]
            mapping[span_name][offset_name] = float(mapping[span_name][offset_name])
        artifact_test("float-offset-" + mapping_name + "-" + span_name + "-" + offset_name, artifact_change(change))
    artifact_test("dependency-source-revision-disagreement", artifact_change(lambda d: program(d)["sources"]["package:example.hinges@1.0.0"].__setitem__("source_revision", "sha256:" + "0" * 64)))
    artifact_test("entry-source-filename-disagreement", artifact_change(lambda d: program(d)["sources"]["entry"].__setitem__("filename", "other.ok")))
    artifact_test("dependency-module-key-disagreement", artifact_change(lambda d: program(d)["sources"]["package:example.hinges@1.0.0"].__setitem__("module_key", "other")))
    artifact_test("program-entry-source-id-disagreement", artifact_change(lambda d: program(d).__setitem__("entry_source_id", "other")))
    artifact_test("top-entry-source-id-disagreement", artifact_change(lambda d: d["extras"]["ontokin"]["source"].__setitem__("entry_source_id", "other")))
    artifact_test("top-entry-revision-disagreement", artifact_change(lambda d: d["extras"]["ontokin"]["source"].__setitem__("entry_revision", "sha256:" + "0" * 64)))
    for field in ["module", "scene", "profile"]:
        artifact_test("top-source-label-" + field, artifact_change(lambda d, field=field: d["extras"]["ontokin"].__setitem__(field, "unknown")))
    def authority_origins(result):
        for key, pointer in result["sourceAuthorityOrigins"].items():
            check(path_get(DOCUMENT, pointer) == result[key], "source authority field origin " + key)
    record("new-source-authority-origins", lambda: reader.observe_glb_ownership(RAW), validator=authority_origins, raw=RAW)
    library = ORIGINAL["hinges.ok"]
    rows = [b'        "lower": vec3(0[m], -spacing, 0[m]),',
            b'        "middle": vec3(0[m], 0[m], 0[m]),',
            b'        "upper": vec3(0[m], spacing, 0[m])']
    original = b"\n".join(rows)
    reordered = b"\n".join([rows[2] + b",", rows[1], rows[0][:-1]])
    check(library.count(original) == 1, "independent reorder fixture")
    src = repin({**ORIGINAL, "hinges.ok": library.replace(original, reordered)})
    source_test("key-literal-reorder-preserves-identities", src, validator=lambda r: (same_graph(r), origins_resolve(r, src)))


def actual_io_control():
    def public_file_call():
        try:
            return reader.read_bound_endpoint(HERE / ("x" * 5000), "before")
        except reader.Fault as exc:
            check(exc.code == "IO", "file-system OSError did not normalize to IO")
            raise
    record("actual-public-file-io-refusal", public_file_call, "refuse",
           reason="Actual hosted filesystem too-long path; require public Fault(IO) rather than uncaught OSError")


if __name__ == "__main__":
    code = CODE.read_bytes()
    shutil.copy2(CODE, HERE / "ownership-reviewed.py")
    source_identity = subprocess.check_output(["git", "rev-parse", "HEAD", "HEAD^{tree}"], cwd=REPO, text=True).splitlines()
    try:
        run()
        correction_symmetry()
        actual_io_control()
    finally:
        summary = {"candidateCommit": source_identity[0], "candidateTree": source_identity[1],
                   "codeSha256": sha(code), "harnessSha256": sha(Path(__file__).read_bytes()),
                   "counts": {"total": len(RESULTS), "passed": sum(x["status"] == "PASS" for x in RESULTS),
                              "failed": sum(x["status"] != "PASS" for x in RESULTS)},
                   "results": RESULTS}
        (HERE / "RESULTS.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: summary[k] for k in ["candidateCommit", "candidateTree", "codeSha256", "counts"]}, sort_keys=True))
        for result in RESULTS:
            if result["status"] != "PASS":
                print(json.dumps({k: result[k] for k in ["name", "expected", "reason", "fault"]}, sort_keys=True))
    raise SystemExit(1 if any(x["status"] != "PASS" for x in RESULTS) else 0)
