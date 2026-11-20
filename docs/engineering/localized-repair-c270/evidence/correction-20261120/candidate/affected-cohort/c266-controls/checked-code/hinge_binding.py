#!/usr/bin/env python3
"""Bind finite source/program/object provenance without comparing hinge fields."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import types


SCHEMA = "ontokin.c266.hinge-input-binding/0.1"
CONTRACT = "ontokin.c260.hinge-declarations/0.1"
MAX_SOURCE_BYTES = 65536
MAX_GLB_BYTES = 4 * 1024 * 1024
PACKAGE_SOURCE = "package:example.hinges@1.0.0"
DEPENDENCIES = {
    "source": ("localized-repair-c265/source_hinges.py", 38229,
               "70d5e5b6247347bf44eaa3be0bc9c91b13f10d4717b4b32261eaebad75987132"),
    "artifact": ("localized-repair-c261/hinge_glb.py", 14036,
                 "6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08"),
    "identity": ("localized-repair-c257/ownership.py", 35942,
                 "c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1"),
}
UNOBSERVED = [
    "/extras/ontokin/source fields other than entry_source_id and entry_revision",
    "/extras/ontokin/module and /extras/ontokin/scene",
    "/extras/ontokin/program/collections and other fields omitted by C261",
    "Node display names, transforms, geometry and metadata outside the retained mapping",
    "Hinge field equality, ordered endpoint association and complete joint-set agreement",
    "Site definitions and poses as direct artifact measurements",
    "Ownership/follow/motion validity beyond source occurrence provenance",
]
LIMITS = [
    "Input source/program/object association only; no hinge comparison or qualified hinge set",
    "No historical byte admission, accepted revision, edit atomicity or clean rebuild",
    "No site-pose evaluation, endpoint world alignment or physical/motion validity",
    "No complete source/glTF/C255 validity, native execution, model trial or comparative benefit",
    "The exact C265 source and C261 raw-artifact finite subsets remain unchanged",
    "Bare-CR line-comment termination remains an unsupported source form",
    "Unknown fields inside a consumed complete mapping are unsupported by this finite profile",
]


class Fault(ValueError):
    """Whole-input refusal retaining bounded available input identity."""

    def __init__(self, code, detail, pointer="", origin=None):
        self.code, self.detail = code, detail
        self.pointer, self.origin = pointer, origin
        self.sourceHashes, self.sourceBytes = {}, {}
        self.artifactSha256, self.artifactBytes = None, None
        super().__init__(f"{code}: {pointer}: {detail}")


def _require(condition, detail, pointer="", code="MALFORMED", origin=None):
    if not condition:
        raise Fault(code, detail, pointer, origin)


def _pointer(parent, key):
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _field(value, key, pointer):
    _require(type(value) is dict, "mapping required", pointer)
    _require(key in value, "missing required field", _pointer(pointer, key))
    return value[key]


def _match(actual, expected, pointer):
    """Require complete mappings and exact primitive types before equality."""
    _require(type(actual) is type(expected), "claim has the wrong type", pointer)
    if type(expected) is dict:
        missing = set(expected) - set(actual)
        extra = set(actual) - set(expected)
        _require(not missing, "missing required mapping field", _pointer(pointer, sorted(missing)[0])
                 if missing else pointer)
        _require(not extra, "unknown field in complete mapping", _pointer(pointer, sorted(extra)[0])
                 if extra else pointer, "UNSUPPORTED_ARTIFACT_FORM")
        for key, value in expected.items():
            _match(actual[key], value, _pointer(pointer, key))
    elif type(expected) is list:
        _require(len(actual) == len(expected), "array length differs from source", pointer, "INPUT_BINDING")
        for index, value in enumerate(expected):
            _match(actual[index], value, _pointer(pointer, index))
    else:
        _require(actual == expected, "claim differs from independently derived source", pointer, "INPUT_BINDING")


def _dependencies():
    """Read and hash every dependency for this call; no ambient import fallback."""
    root = Path(__file__).absolute().parent.parent
    captured = {}
    for name, (relative, size, digest) in DEPENDENCIES.items():
        path = root / relative
        for component in (path, *path.parents):
            _require(not component.is_symlink(), "symlink in pinned dependency path", code="INPUT_BINDING")
        _require(path.is_file(), "missing pinned dependency: " + relative, code="INPUT_BINDING")
        _require(path.stat().st_size == size, "pinned dependency size: " + relative, code="INPUT_BINDING")
        with path.open("rb") as handle:
            raw = handle.read(size + 1)
        _require(len(raw) == size and hashlib.sha256(raw).hexdigest() == digest,
                 "pinned dependency bytes: " + relative, code="INPUT_BINDING")
        captured[name] = path, raw
    modules = {}
    for name, (path, raw) in captured.items():
        module = types.ModuleType("_c266_pinned_" + name)
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        exec(compile(raw, str(path), "exec"), module.__dict__)
        modules[name] = module
    return modules


def _origin_key(origin):
    return origin["file"], origin["startByte"], origin["endByteExclusive"]


def _span(origin, hashes):
    filename = origin["file"]
    _require(filename in hashes, "unknown source witness file", code="INPUT_BINDING", origin=origin)
    low, high = origin["startByte"], origin["endByteExclusive"]
    _require(type(low) is int and type(high) is int and 0 <= low < high <= MAX_SOURCE_BYTES,
             "invalid independent source witness", code="INPUT_BINDING", origin=origin)
    return {"source_id": "entry" if filename == "main.ok" else PACKAGE_SOURCE,
            "source_revision": "sha256:" + hashes[filename], "filename": filename,
            "start_byte": low, "end_byte": high}


def _selected_tokens(tokens, origin):
    selected = [token for token in tokens[origin["file"]]
                if origin["startByte"] <= token.start and token.end <= origin["endByteExclusive"]]
    _require(selected and selected[0].start == origin["startByte"]
             and selected[-1].end == origin["endByteExclusive"],
             "source witness does not bound exact tokens", code="INPUT_BINDING", origin=origin)
    return selected


def _entry_span(dependency, tokens, expansion):
    """Derive the full selected key-value row, not only its key-token span."""
    witnesses = expansion["inputResolution"]
    literal = witnesses[0]
    selected = _selected_tokens(tokens, literal)
    if not (selected[0].kind == "id" and selected[0].value == "keyed"):
        returned = [item for item in witnesses if item.get("role") == "helper returned keyed literal"]
        _require(len(returned) == 1, "one directly returned keyed literal required", code="INPUT_BINDING")
        literal = returned[0]
        selected = _selected_tokens(tokens, literal)
    stream = dependency.Stream(selected)
    stream.pop("keyed", kind="id"); stream.pop("<", kind="symbol")
    depth = 1
    while depth:
        token = stream.pop()
        if token.kind == "symbol" and token.value in ("<", ">"):
            depth += 1 if token.value == "<" else -1
    body, _, _ = stream.block()
    _require(stream.done(), "trailing selected keyed literal tokens", code="INPUT_BINDING")
    rows = dependency.split_top(body, ",")
    if rows and not rows[-1]:
        rows.pop()
    key_origin = expansion["literalKey"]
    matches = [row for row in rows if row and row[0].kind == "string"
               and (row[0].file, row[0].start, row[0].end) == _origin_key(key_origin)]
    _require(len(matches) == 1, "selected key must belong to one complete keyed row",
             code="INPUT_BINDING", origin=key_origin)
    row = matches[0]
    _require(len(row) >= 3 and row[1].kind == "symbol" and row[1].value == ":",
             "malformed selected keyed row", code="INPUT_BINDING", origin=key_origin)
    return row[0].value, dependency.origin(row, "complete literal input entry")


def _render_path(steps):
    result = ""
    for step in steps:
        if step["kind"] == "member":
            result += ("." if result else "") + step["value"]
        else:
            result += "[" + json.dumps(step["value"], ensure_ascii=False) + "]"
    return result


def _source_mappings(files, source, dependency):
    """Use pinned lexical/module/occurrence data, never artifact values."""
    identity = dependency.observe_source_ownership(files)
    _require(identity["sourceHashes"] == source["sourceHashes"]
             and identity["sourceManifest"] == source["sourceManifest"]
             and identity["programRevision"] == source["programRevision"],
             "source observers disagree on identity", code="INPUT_BINDING")
    modules = {name: dependency.parse_module(raw, name) for name, raw in files.items()}
    tokens = {name: dependency.lex(raw, name) for name, raw in files.items()}
    declarations = {}
    for module in modules.values():
        for definition in module["classes"].values():
            for declaration in definition["parts"]:
                declarations[_origin_key(declaration["declaration"])] = declaration
        if module["scene"] is not None:
            for declaration in module["scene"]["roots"]:
                declarations[_origin_key(declaration["declaration"])] = declaration
    observed = {tuple(record["id"]): record for record in source["objects"]}
    _require(set(observed) == {tuple(record["id"]) for record in identity["records"]},
             "source observers disagree on complete object set", code="INPUT_BINDING")
    mappings, records = {}, {}
    for record in identity["records"]:
        oid = tuple(record["id"])
        authoritative = observed[oid]
        _require(record["path"] == authoritative["path"]
                 and record["definitionId"] == authoritative["definitionId"],
                 "source object association differs", code="INPUT_BINDING")
        declaration = declarations[_origin_key(record["origin"]["declaration"])]
        owner = tuple(record["ownerId"]) if record["ownerId"] is not None else None
        generated = None
        if owner is None:
            steps = [{"kind": "member", "value": declaration["name"]}]
            root_path, declaration_id, ancestor = declaration["name"], None, None
        else:
            _require(owner in mappings, "source owner must precede its occurrence", code="INPUT_BINDING")
            parent = mappings[owner]
            steps = parent["path_steps"] + [{"kind": "member", "value": declaration["name"]}]
            root_path = parent["root_path"]
            declaration_id = records[owner]["definitionId"] + [declaration["key"]]
            ancestor = parent["generated_ancestor"]
        expansion = record["origin"]["expansion"]
        if expansion is not None:
            _require(owner is not None and declaration["generated"] is not None,
                     "generated occurrence lacks its source owner/declaration", code="INPUT_BINDING")
            key, entry = _entry_span(dependency, tokens, expansion)
            collection_path = _render_path(steps)
            steps += [{"kind": "key", "value": key}]
            generated = {"collection_path": collection_path,
                         "collection_id": records[owner]["id"] + [declaration["key"]],
                         "collection_definition_id": declaration_id, "key": key,
                         "input": _span(expansion["generatorInput"], source["sourceHashes"]),
                         "input_entry": _span(entry, source["sourceHashes"]),
                         "unique_declaration_span": False}
            ancestor = _render_path(steps)
        path = _render_path(steps)
        _require(path == record["path"], "source-rendered occurrence path differs", code="INPUT_BINDING")
        mapping = {"path": path, "element_id": record["id"], "owner_path": record["ownerPath"],
                   "root_path": root_path, "path_steps": steps,
                   "definition_id": record["definitionId"], "class_id": "/".join(record["definitionId"]),
                   "declaration": _span(record["origin"]["declaration"], source["sourceHashes"]),
                   "definition": _span(record["origin"]["definition"], source["sourceHashes"]),
                   "declaration_definition_id": declaration_id, "generated": generated,
                   "generated_ancestor": ancestor}
        mappings[oid], records[oid] = mapping, record
    return identity, mappings


def _bind(files, raw):
    modules = _dependencies()
    try:
        source = modules["source"].observe_source_hinges(files)
    except modules["source"].Fault as exc:
        raise Fault(exc.code, exc.detail, origin=exc.origin) from exc
    try:
        artifact = modules["artifact"].observe_glb_hinges(raw)
    except modules["artifact"].Fault as exc:
        code = "UNSUPPORTED_ARTIFACT_FORM" if exc.code == "UNSUPPORTED" else exc.code
        raise Fault(code, exc.detail, exc.pointer) from exc
    identity, mappings = _source_mappings(files, source, modules["identity"])
    claims = artifact["sourceClaims"]
    base = "/extras/ontokin"
    source_claim = claims["source"]
    for key, expected in (("entry_source_id", "entry"),
                          ("entry_revision", "sha256:" + source["sourceHashes"]["main.ok"])):
        _match(_field(source_claim, key, base + "/source"), expected, base + "/source/" + key)
    program = claims["program"]
    expected_program = {"revision": source["programRevision"], "entry_source_id": "entry",
                        "manifest": source["sourceManifest"], "sources": identity["sourceUnits"]}
    _match(program, expected_program, base + "/program")
    actual = {tuple(record["claims"]["element_id"]): record for record in artifact["objects"]}
    _require(set(actual) == set(mappings), "complete object identity sets differ", base + "/program/occurrences",
             "INPUT_BINDING")
    _require({record["claims"]["path"] for record in artifact["objects"]}
             == {mapping["path"] for mapping in mappings.values()},
             "complete object path sets differ", base + "/program/occurrences", "INPUT_BINDING")
    source_objects = {tuple(record["id"]): record for record in source["objects"]}
    bound = []
    for oid, mapping in mappings.items():
        actual_record = actual[oid]
        got, origins = actual_record["claims"], actual_record["origins"]
        for key, expected in (("path", mapping["path"]), ("element_id", mapping["element_id"]),
                              ("class_name", mapping["class_id"]), ("program_revision", source["programRevision"])):
            _match(got[key], expected, origins[key])
        for key in ("source_mapping", "program_occurrence"):
            _match(got[key], mapping, origins[key])
        bound.append({"id": mapping["element_id"], "definitionId": mapping["definition_id"],
                      "path": mapping["path"], "node": actual_record["node"], "mapping": mapping,
                      "sourceOrigins": source_objects[oid]["origin"], "artifactOrigins": dict(origins)})
    return {"schema": SCHEMA, "contract": CONTRACT, "kind": "source-program-object-binding",
            "sourceHashes": dict(source["sourceHashes"]), "sourceBytes": dict(source["sourceBytes"]),
            "sourceManifest": source["sourceManifest"], "programRevision": source["programRevision"],
            "artifactSha256": artifact["artifactSha256"], "artifactBytes": artifact["artifactBytes"],
            "sourceAuthorityOrigins": artifact["sourceOrigins"], "records": bound, "objectCount": len(bound),
            "inputBindingVerified": True, "hingeComparisonVerified": False, "hingeSetAgreementVerified": False,
            "endpointAgreementVerified": False, "historicalInputsBound": False,
            "sourceAgreementVerified": False, "artifactAgreementVerified": False, "sitePosesEvaluated": False,
            "sourceValidityQualified": False, "acceptedRevisionQualified": False,
            "completeC255Semantic": False, "executionAllowed": False, "realTrialSuccess": None,
            "directSiteTableObserved": False, "jointDefinitionOrSpanObserved": False,
            "unobservedFields": UNOBSERVED.copy(), "limits": LIMITS.copy()}


def bind_hinge_inputs(source_files, raw):
    """Bind retained source/program/object claims or raise a whole-input Fault."""
    hashes, sizes = {}, {}
    if type(source_files) is dict:
        for name in ("main.ok", "hinges.ok"):
            value = source_files.get(name)
            if type(value) is bytes:
                sizes[name] = len(value)
                if len(value) <= MAX_SOURCE_BYTES:
                    hashes[name] = hashlib.sha256(value).hexdigest()
    artifact_size = len(raw) if type(raw) is bytes else None
    artifact_hash = hashlib.sha256(raw).hexdigest() if type(raw) is bytes and len(raw) <= MAX_GLB_BYTES else None
    try:
        return _bind(source_files, raw)
    except Fault as exc:
        fault = exc
    except OSError as exc:
        fault = Fault("IO_ERROR", type(exc).__name__)
    except (UnicodeError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            ArithmeticError, RecursionError) as exc:
        fault = Fault("MALFORMED", type(exc).__name__)
    fault.sourceHashes, fault.sourceBytes = hashes, sizes
    fault.artifactSha256, fault.artifactBytes = artifact_hash, artifact_size
    raise fault
