#!/usr/bin/env python3
"""Read finite source ownership and compare actual GLB metadata without execution."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct

SCHEMA = "ontokin.c257.ownership-observation/0.1"
MAX_SOURCE_BYTES = 65536
MAX_TOKENS = 8192
MAX_DEPTH = 32
MAX_OBJECTS = 128
MAX_KEYS = 64
MAX_GLB_BYTES = 4 * 1024 * 1024
PROOF = "docs/engineering/semantic-export-c210/evidence/proof"
PACKAGE = "example.hinges"
VERSION = "1.0.0"
LIBRARY_SHA = "1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a"
PINS = {
    "before": {"bytes": 185276, "glb": "d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534",
               "source": "73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123"},
    "after": {"bytes": 185236, "glb": "05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8",
              "source": "443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a"},
}
LIMITS = ["Ownership only; follow, hinge, pose and physical observations absent",
          "Finite partial source observer; complete source validity not established",
          "No complete C255 semantics, accepted revision, rebuild, trial or execution authority",
          "One public family; no comparative advantage or native qualification"]


class Fault(ValueError):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


def require(value, code, detail):
    if not value:
        raise Fault(code, detail)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def string(value, where):
    require(type(value) is str and 0 < len(value) <= 512 and
            all(ord(c) >= 32 and ord(c) != 127 and not 0xD800 <= ord(c) <= 0xDFFF for c in value), "TEXT", where)
    return value


def identifier(value, where):
    require(type(value) is list and 1 <= len(value) <= MAX_DEPTH, "IDENTITY", where)
    return [string(x, where) for x in value]


def unique(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, "JSON_DUPLICATE", k)
        result[k] = v
    return result


def json_integer(raw):
    require(len(raw) <= 64, "JSON_INTEGER", "integer digit limit")
    return int(raw)


def json_bytes(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_int=json_integer,
                      parse_constant=lambda x: (_ for _ in ()).throw(Fault("NONFINITE", x)))


def public(call):
    try:
        return call()
    except Fault:
        raise
    except (KeyError, IndexError, TypeError, AttributeError, ValueError, UnicodeError,
            struct.error, OverflowError, RecursionError) as exc:
        raise Fault("STRUCTURE", type(exc).__name__) from exc


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    value: str
    start: int
    end: int
    file: str


LEXER = re.compile(rb'(?P<space>\s+)|(?P<comment>//[^\n]*(?:\n|$))|'
                   rb'(?P<string>"(?:\\.|[^"\\])*")|(?P<id>[A-Za-z_][A-Za-z_0-9]*)|'
                   rb'(?P<number>[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)|'
                   rb'(?P<symbol>->|<=|>=|==|!=|[{}()\[\];:,.@=+*/<>^-])')


def lex(raw, filename):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_SOURCE_BYTES, "SOURCE_SIZE", filename)
    raw.decode("utf-8")
    tokens, offset, stack = [], 0, []
    while offset < len(raw):
        match = LEXER.match(raw, offset)
        require(match is not None, "SOURCE_TOKEN", f"{filename} byte {offset}")
        kind = match.lastgroup
        value = match.group().decode("utf-8")
        if kind not in ("space", "comment"):
            if kind == "string":
                value = string(json.loads(value), "source string")
            token = Token(kind, value, offset, match.end(), filename)
            tokens.append(token)
            require(len(tokens) <= MAX_TOKENS, "TOKEN_LIMIT", filename)
            if kind == "symbol" and value in ("(", "[", "{"):
                stack.append(value)
                require(len(stack) <= MAX_DEPTH, "SOURCE_DEPTH", filename)
            elif kind == "symbol" and value in (")", "]", "}"):
                require(stack and stack.pop() == {")": "(", "]": "[", "}": "{"}[value],
                        "SOURCE_BALANCE", f"{filename} byte {offset}")
        offset = match.end()
    require(not stack, "SOURCE_BALANCE", filename)
    return tokens


def origin(tokens, role):
    require(bool(tokens), "SOURCE_ORIGIN", role)
    require(all(t.file == tokens[0].file for t in tokens), "SOURCE_ORIGIN", "one actual file")
    return {"file": tokens[0].file, "startByte": tokens[0].start,
            "endByteExclusive": tokens[-1].end, "role": role}


class Stream:
    def __init__(self, tokens):
        self.tokens, self.index = tokens, 0

    def done(self):
        return self.index == len(self.tokens)

    def peek(self):
        return None if self.done() else self.tokens[self.index].value

    def pop(self, value=None, kind=None):
        require(not self.done(), "SOURCE_EOF", str(value))
        t = self.tokens[self.index]
        require(value is None or t.value == value, "SOURCE_SYNTAX", f"expected {value} at {t.file}:{t.start}")
        require(kind is None or t.kind == kind, "SOURCE_SYNTAX", f"expected {kind} at {t.file}:{t.start}")
        self.index += 1
        return t

    def name(self):
        return self.pop(kind="id")

    def key(self):
        self.pop("@")
        return self.pop(kind="string")

    def block(self):
        opening = self.pop("{")
        start, depth = self.index, 1
        while not self.done():
            t = self.pop()
            if t.kind == "symbol" and t.value in ("{", "}"):
                depth += 1 if t.value == "{" else -1
                if depth == 0:
                    return self.tokens[start:self.index-1], opening, t
        raise Fault("SOURCE_BALANCE", "block")

    def statement(self):
        start, depth = self.index, 0
        while not self.done():
            t = self.pop()
            if t.kind == "symbol":
                if t.value in ("(", "[", "{"):
                    depth += 1
                elif t.value in (")", "]", "}"):
                    depth -= 1
                elif t.value == ";" and depth == 0:
                    return self.tokens[start:self.index-1]
        raise Fault("SOURCE_SYNTAX", "statement requires semicolon")

    def header_block(self):
        start, depth = self.index, 0
        while not self.done():
            if self.peek() == "{" and depth == 0:
                header = self.tokens[start:self.index]
                body, opening, closing = self.block()
                return header, body, opening, closing
            t = self.pop()
            if t.value in ("(", "[") and t.kind == "symbol":
                depth += 1
            elif t.value in (")", "]") and t.kind == "symbol":
                depth -= 1
        raise Fault("SOURCE_SYNTAX", "declaration requires block")


def split_top(tokens, separator):
    groups, start, depth = [], 0, 0
    for i, token in enumerate(tokens):
        if token.kind == "symbol":
            if token.value in ("(", "[", "{"):
                depth += 1
            elif token.value in (")", "]", "}"):
                depth -= 1
            elif token.value == separator and depth == 0:
                groups.append(tokens[start:i]); start = i+1
    groups.append(tokens[start:])
    return groups


def assignments(tokens):
    stream, result = Stream(tokens), []
    while not stream.done():
        statement = stream.statement()
        groups = split_top(statement, "=")
        require(len(groups) == 2 and groups[0] and groups[1], "INITIALIZER", "simple assignments only")
        result.append({"lhs": groups[0], "rhs": groups[1], "origin": origin(statement, "initializer assignment")})
    return result


def class_reference(stream):
    first = stream.name()
    result = [first]
    if stream.peek() == ".":
        stream.pop("."); result.append(stream.name())
    return result


def occurrence_declaration(stream, visibility, start, seen):
    keyword = stream.pop()
    require(keyword.value in ("object", "part", "parts"), "SOURCE_SYNTAX", "ownership declaration")
    seen.add(keyword.start)
    name, key = stream.name(), stream.key()
    stream.pop(":")
    reference = class_reference(stream)
    generated = None
    if keyword.value == "parts":
        stream.pop("for"); stream.pop("(")
        binder1 = stream.name(); stream.pop(","); binder2 = stream.name(); stream.pop(")")
        require(binder1.value != binder2.value, "GENERATOR_BINDERS", name.value)
        stream.pop("in")
        owner_self = stream.pop("self", kind="id"); stream.pop("."); parameter = stream.name()
        generated = {"parameter": parameter.value, "inputOrigin": origin([owner_self, parameter], "generator input")}
    body, _, closing = stream.block()
    return {"kind": keyword.value, "name": name.value, "key": key.value, "reference": reference,
            "visibility": visibility, "generated": generated, "assignments": assignments(body),
            "declaration": origin([start, closing], "ownership declaration"),
            "nameOrigin": origin([name], "declaration name"), "keyOrigin": origin([key], "stable declaration key")}


def parse_class(body, definition, seen):
    stream, parts, parameters = Stream(body), [], {}
    names, keys = set(), set()
    while not stream.done():
        start = stream.tokens[stream.index]
        visibility = stream.pop().value if stream.peek() in ("public", "private") else "private"
        if stream.peek() in ("part", "parts"):
            part = occurrence_declaration(stream, visibility, start, seen)
            require(part["name"] not in names and part["key"] not in keys, "DUPLICATE_MEMBER", definition["name"])
            names.add(part["name"]); keys.add(part["key"]); parts.append(part)
        elif stream.peek() == "param":
            stream.pop("param"); name, key = stream.name(), stream.key(); stream.pop(":")
            rest = stream.statement(); groups = split_top(rest, "=")
            require(len(groups) == 2 and groups[0] and groups[1], "PARAMETER", name.value)
            require(name.value not in parameters and name.value not in names and key.value not in keys,
                    "DUPLICATE_MEMBER", name.value)
            names.add(name.value); keys.add(key.value)
            parameters[name.value] = {"expression": groups[1], "type": [x.value for x in groups[0]],
                                      "origin": origin([start, rest[-1]], "parameter default")}
        elif stream.peek() in ("site", "follow", "joint", "method"):
            stream.header_block()
        elif visibility == "private" and stream.peek() in ("geometry", "appearance", "physical", "collision", "motion"):
            stream.statement()
        else:
            raise Fault("UNSUPPORTED_MEMBER", str(stream.peek()))
    definition.update(parts=parts, parameters=parameters)


def parse_module(raw, filename):
    tokens = lex(raw, filename)
    stream = Stream(tokens)
    stream.pop("ontokin"); require(stream.pop(kind="string").value == "0.2", "PROFILE", "source version")
    stream.pop(";"); stream.pop("module"); module_name = stream.name(); module_key = stream.key(); stream.pop(";")
    stream.pop("profile"); require(stream.pop(kind="string").value == "construction-0.1", "PROFILE", "construction profile")
    stream.pop(";")
    module = {"file": filename, "name": module_name.value, "key": module_key.value,
              "keyOrigin": origin([module_key], "module key"), "classes": {}, "functions": {}, "imports": [], "scene": None}
    seen_ownership, definition_keys = set(), set()
    while not stream.done():
        start = stream.tokens[stream.index]
        visibility = stream.pop().value if stream.peek() in ("public", "private") else "public"
        if stream.peek() == "import":
            stream.pop("import"); alias = stream.name(); stream.key(); stream.pop("from")
            package = stream.pop(kind="string"); stream.pop("version"); version = stream.pop(kind="string")
            stream.pop("digest"); pin = stream.pop(kind="string"); end = stream.pop(";")
            module["imports"].append({"alias": alias.value, "package": package.value, "version": version.value,
                                      "digest": pin.value, "origin": origin([start, end], "module import")})
        elif stream.peek() in ("class", "fn"):
            kind = stream.pop().value; name, key = stream.name(), stream.key()
            require(name.value not in module["classes"] and name.value not in module["functions"]
                    and key.value not in definition_keys, "DUPLICATE_DEFINITION", name.value)
            definition_keys.add(key.value)
            header, body, _, end = stream.header_block()
            definition = {"name": name.value, "key": key.value, "file": filename, "module": module,
                "public": visibility == "public", "origin": origin([start, end], "class" if kind == "class" else "function"),
                "keyOrigin": origin([key], "definition key"), "header": header, "body": body}
            require(len(module["classes"])+len(module["functions"]) < 32, "DEFINITION_LIMIT", filename)
            if kind == "class":
                require(not header, "UNSUPPORTED_CLASS", "inheritance or parameters in class header")
                parse_class(body, definition, seen_ownership)
                module["classes"][name.value] = definition
            else:
                module["functions"][name.value] = definition
        elif stream.peek() == "scene":
            require(filename == "main.ok" and module["scene"] is None, "SCENE", "one entry scene")
            stream.pop("scene"); name, key = stream.name(), stream.key(); body, _, end = stream.block()
            roots, scene_stream = [], Stream(body)
            while not scene_stream.done():
                if scene_stream.peek() == "object":
                    roots.append(occurrence_declaration(scene_stream, "public", scene_stream.tokens[scene_stream.index], seen_ownership))
                elif scene_stream.peek() in ("duration", "gravity", "action"):
                    scene_stream.statement()
                elif scene_stream.peek() == "at":
                    scene_stream.header_block()
                else:
                    raise Fault("UNSUPPORTED_SCENE", str(scene_stream.peek()))
            require(0 < len(roots) <= MAX_OBJECTS, "ROOT_LIMIT", filename)
            require(len({x["name"] for x in roots}) == len(roots) and len({x["key"] for x in roots}) == len(roots),
                    "DUPLICATE_ROOT", filename)
            module["scene"] = {"name": name.value, "key": key.value, "keyOrigin": origin([key], "scene key"),
                               "origin": origin([start, end], "scene declaration"), "roots": roots}
        else:
            raise Fault("UNSUPPORTED_TOP_LEVEL", str(stream.peek()))
    all_ownership = {t.start for t in tokens if t.kind == "id" and t.value in ("object", "part", "parts")}
    require(all_ownership == seen_ownership, "UNSUPPORTED_OWNERSHIP_POSITION", filename)
    return module


def manifest_for(sources):
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": "main.ok", "source_revision": "sha256:"+digest(sources["main.ok"])},
             {"source_id": "package:"+PACKAGE+"@"+VERSION, "package_id": PACKAGE, "version": VERSION,
              "filename": "hinges.ok", "source_revision": "sha256:"+digest(sources["hinges.ok"])}]
    manifest = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": units}
    raw = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    return manifest, "sha256:"+digest(b"ontokin.bundle/0.1\0"+raw)


def _source(sources):
    require(type(sources) is dict and set(sources) == {"main.ok", "hinges.ok"}, "SOURCE_CLOSURE", "exact two supplied files")
    for filename, raw in sources.items():
        require(type(raw) is bytes and 0 < len(raw) <= MAX_SOURCE_BYTES, "SOURCE_SIZE", filename)
    manifest, revision = manifest_for(sources)
    modules = {name: parse_module(raw, name) for name, raw in sources.items()}
    entry, library = modules["main.ok"], modules["hinges.ok"]
    require(entry["scene"] is not None and not library["imports"] and library["scene"] is None,
            "SOURCE_CLOSURE", "entry scene and leaf library")
    require(len(entry["imports"]) == 1, "SOURCE_CLOSURE", "one pinned library import")
    imported = entry["imports"][0]
    require(imported["package"] == PACKAGE and imported["version"] == VERSION
            and imported["digest"] == "sha256:"+digest(sources["hinges.ok"]), "IMPORT_BINDING", "supplied library pin")

    def resolve(reference, declaring, category):
        names = [t.value for t in reference]
        if len(names) == 1:
            target_module, name = declaring, names[0]
        else:
            require(declaring is entry and names[0] == imported["alias"], "UNKNOWN_IMPORT", ".".join(names))
            target_module, name = library, names[1]
        require(name in target_module[category], "UNKNOWN_DEFINITION", ".".join(names))
        target = target_module[category][name]
        require(target_module is declaring or target["public"], "PRIVATE_DEFINITION", name)
        return target

    def keyed_literal(expression):
        stream = Stream(expression); stream.pop("keyed", kind="id")
        stream.pop("<"); angle = 1
        while angle:
            token = stream.pop()
            if token.kind == "symbol" and token.value in ("<", ">"):
                angle += 1 if token.value == "<" else -1
        body, _, _ = stream.block()
        require(stream.done(), "UNSUPPORTED_KEY_INPUT", "trailing literal expression")
        rows = split_top(body, ",")
        if rows and not rows[-1]:
            rows.pop()
        require(0 < len(rows) <= MAX_KEYS, "KEY_LIMIT", "nonempty bounded keyed literal")
        keys, seen = [], set()
        for row in rows:
            require(len(row) >= 3 and row[0].kind == "string" and row[1].value == ":", "KEY_LITERAL", "literal string key")
            key = row[0]
            require(key.value not in seen, "DUPLICATE_KEY", key.value)
            seen.add(key.value); keys.append((key.value, origin([key], "literal input key")))
        return keys

    def key_input(expression, declaring):
        require(expression, "KEY_INPUT", "empty expression")
        witnesses = [origin(expression, "final keyed input expression")]
        if expression[0].value == "keyed" and expression[0].kind == "id":
            return keyed_literal(expression), witnesses
        call = Stream(expression); reference = class_reference(call)
        function = resolve(reference, declaring, "functions")
        call.pop("(")
        depth = 1
        while depth:
            t = call.pop()
            if t.kind == "symbol" and t.value in ("(", ")"):
                depth += 1 if t.value == "(" else -1
        require(call.done(), "UNSUPPORTED_KEY_INPUT", "only direct helper calls")
        helper = Stream(function["body"]); helper.pop("return")
        returned = helper.statement()
        require(helper.done(), "UNSUPPORTED_KEY_HELPER", "one direct literal return only")
        witnesses.extend([function["origin"], origin(returned, "helper returned keyed literal")])
        return keyed_literal(returned), witnesses

    shape_names = {p["generated"]["parameter"] for module in modules.values() for c in module["classes"].values()
                   for p in c["parts"] if p["generated"]}
    records, ids, paths = [], set(), set()

    def def_id(cls):
        prefix = ["entry", cls["module"]["key"]] if cls["module"] is entry else ["package", PACKAGE, cls["module"]["key"]]
        return prefix+["definitions", cls["key"]]

    def direct_overrides(rows):
        result = {}
        for row in rows:
            lhs = row["lhs"]
            if len(lhs) == 1 and lhs[0].kind == "id":
                name = lhs[0].value
                require(name not in result, "DUPLICATE_OVERRIDE", name)
                result[name] = row
            elif any(t.kind == "id" and t.value in shape_names for t in lhs):
                raise Fault("UNSUPPORTED_SHAPE_OVERRIDE", "nested keyed-shape overrides")
        return result

    def expand(decl, declaring, oid, path, owner, class_stack, key_origins, expansion=None):
        require(len(records) < MAX_OBJECTS and len(class_stack) < MAX_DEPTH, "OBJECT_LIMIT", path)
        cls = resolve(decl["reference"], declaring, "classes")
        class_key = (cls["file"], cls["name"])
        require(class_key not in class_stack, "OWNERSHIP_CYCLE", path)
        require(tuple(oid) not in ids and path not in paths, "DUPLICATE_OCCURRENCE", path)
        ids.add(tuple(oid)); paths.add(path)
        owner_record = {"id": owner["id"], "path": owner["path"]} if owner else None
        record = {"id": oid, "definitionId": def_id(cls), "path": path,
                  "ownerId": owner_record["id"] if owner else None,
                  "ownerPath": owner_record["path"] if owner else None,
                  "kind": "scene-root" if owner is None else "generated-part" if decl["generated"] else "ordinary-part",
                  "origin": {"declaration": decl["declaration"], "definition": cls["origin"],
                    "identityKeys": key_origins, "ownerRule": "scene-root has no object owner" if owner is None
                    else "containing object directly owns declared part; collection adds no object",
                    "ownerDeclaration": owner["origin"]["declaration"] if owner else entry["scene"]["origin"],
                    "expansion": expansion}}
        records.append(record)
        overrides = direct_overrides(decl["assignments"])
        for part in cls["parts"]:
            base_id, base_path = oid+[part["key"]], path+"."+part["name"]
            witnesses = key_origins+[part["keyOrigin"]]
            if part["generated"]:
                parameter = part["generated"]["parameter"]
                require(parameter in cls["parameters"], "KEY_PARAMETER", parameter)
                definition = cls["parameters"][parameter]
                require(definition["type"][:2] == ["Keyed", "<"], "KEY_PARAMETER", "Keyed parameter required")
                selected = overrides.get(parameter)
                expression = selected["rhs"] if selected else definition["expression"]
                expression_module = modules[expression[0].file]
                keys, input_origins = key_input(expression, expression_module)
                for key, key_at in keys:
                    expansion_info = {"collectionDeclaration": part["declaration"], "generatorInput": part["generated"]["inputOrigin"],
                        "finalInput": selected["origin"] if selected else definition["origin"],
                        "inputResolution": input_origins, "literalKey": key_at, "collectionIsObject": False}
                    expand(part, cls["module"], base_id+[key], base_path+"["+json.dumps(key, ensure_ascii=False)+"]",
                           record, class_stack+[class_key], witnesses+[key_at], expansion_info)
            else:
                expand(part, cls["module"], base_id, base_path, record, class_stack+[class_key], witnesses)

    for root in entry["scene"]["roots"]:
        expand(root, entry, [entry["key"], entry["scene"]["key"], root["key"]], root["name"], None, [],
               [entry["keyOrigin"], entry["scene"]["keyOrigin"], root["keyOrigin"]])
    source_units = {unit["source_id"]: dict(unit, module_name=modules[unit["filename"]]["name"],
                                          module_key=modules[unit["filename"]]["key"])
                    for unit in manifest["units"]}
    return {"schema": SCHEMA, "kind": "source-ownership", "programRevision": revision,
            "sourceManifest": manifest, "sourceHashes": {name: digest(raw) for name, raw in sources.items()},
            "sourceUnits": source_units, "moduleName": entry["name"], "sceneName": entry["scene"]["name"],
            "records": records, "objectCount": len(records), "rootCount": sum(x["ownerId"] is None for x in records),
            "edgeCount": sum(x["ownerId"] is not None for x in records), "sourceValidityQualified": False,
            "completeC255Semantic": False, "executionAllowed": False, "realTrialSuccess": None,
            "historicalInputsBound": False, "limits": LIMITS.copy()}


def observe_source_ownership(source_files):
    return public(lambda: _source(source_files))


def glb_document(raw):
    require(type(raw) is bytes and 28 <= len(raw) <= MAX_GLB_BYTES, "GLB_SIZE", "bounded bytes")
    magic, version, size = struct.unpack_from("<III", raw)
    require((magic, version, size) == (0x46546C67, 2, len(raw)), "GLB_HEADER", "GLB2 exact size")
    offset, chunks = 12, []
    while offset < len(raw):
        require(offset+8 <= len(raw), "GLB_CHUNK", "truncated header")
        length, kind = struct.unpack_from("<II", raw, offset)
        require(length % 4 == 0 and offset+8+length <= len(raw), "GLB_CHUNK", "aligned bounded chunk")
        chunks.append((kind, offset+8, length)); offset += length+8
    require(len(chunks) == 2 and [c[0] for c in chunks] == [0x4E4F534A, 0x004E4942],
            "GLB_CHUNKS", "one JSON then BIN chunk")
    _, start, length = chunks[0]
    require(length <= 2*1024*1024, "GLB_JSON_SIZE", "JSON chunk limit")
    document = json_bytes(raw[start:start+length])
    require(type(document) is dict and document["asset"]["version"] == "2.0", "GLTF_VERSION", "2.0 asset")
    require(not document.get("extensionsRequired"), "UNSUPPORTED", "required extension semantics")
    return document


def _artifact(raw):
    document = glb_document(raw)
    nodes = document["nodes"]
    require(type(nodes) is list and 0 < len(nodes) <= MAX_OBJECTS, "NODE_LIMIT", "bounded nodes")
    top_meta = document["extras"]["ontokin"]
    program = top_meta["program"]
    revision = string(program["revision"], "program revision")
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", revision), "PROGRAM_ID", revision)
    occurrences = program["occurrences"]
    require(type(occurrences) is dict and 0 < len(occurrences) <= MAX_OBJECTS, "OCCURRENCE_LIMIT", "program occurrences")
    records, ids, paths = [], set(), set()
    for index, node in enumerate(nodes):
        meta = node["extras"]["ontokin"]
        require(meta["kind"] == "object", "NODE_KIND", "object metadata")
        path, oid = string(meta["path"], "node path"), identifier(meta["element_id"], "node identity")
        require(path not in paths and tuple(oid) not in ids, "DUPLICATE_IDENTITY", path)
        paths.add(path); ids.add(tuple(oid))
        require(path in occurrences, "OCCURRENCE_JOIN", path)
        mapping, occurrence = meta["source_mapping"], occurrences[path]
        claims = {}
        for label, value in (("nodeOwner", meta["owner"]), ("sourceMappingOwner", mapping["owner_path"]),
                             ("programOccurrenceOwner", occurrence["owner_path"])):
            require(value is None or type(value) is str, "OWNER_TYPE", label)
            claims[label] = None if value is None else string(value, label)
        pointer = "/nodes/"+str(index)+"/extras/ontokin"
        escaped = path.replace("~", "~0").replace("/", "~1")
        records.append({"id": oid, "path": path, "node": index,
            "definitionId": identifier(mapping["definition_id"], "definition identity"),
            "claims": claims, "nodeName": string(node["name"], "node name"),
            "nodeProgramRevision": string(meta["program_revision"], "node program revision"),
            "sourceMapping": mapping, "programOccurrence": occurrence,
            "className": string(meta["class_name"], "class name"),
            "origins": {"identity": pointer+"/element_id", "definition": pointer+"/source_mapping/definition_id",
                "nodeOwner": pointer+"/owner", "sourceMappingOwner": pointer+"/source_mapping/owner_path",
                "programOccurrenceOwner": "/extras/ontokin/program/occurrences/"+escaped+"/owner_path"}})
    require(paths == set(occurrences), "OCCURRENCE_COVERAGE", "nodes and program occurrences")
    return {"schema": SCHEMA, "kind": "untrusted-artifact-ownership", "artifactSha256": digest(raw),
            "artifactBytes": len(raw), "programRevision": revision, "sourceManifest": program["manifest"],
            "sourceUnits": program["sources"], "entrySourceId": program["entry_source_id"],
            "entrySourceIdClaim": top_meta["source"]["entry_source_id"],
            "entryRevisionClaim": top_meta["source"]["entry_revision"],
            "moduleName": top_meta["module"], "sceneName": top_meta["scene"], "profileName": top_meta["profile"],
            "sourceAuthorityOrigins": {"sourceUnits": "/extras/ontokin/program/sources",
                "entrySourceId": "/extras/ontokin/program/entry_source_id",
                "entrySourceIdClaim": "/extras/ontokin/source/entry_source_id",
                "entryRevisionClaim": "/extras/ontokin/source/entry_revision",
                "moduleName": "/extras/ontokin/module", "sceneName": "/extras/ontokin/scene",
                "profileName": "/extras/ontokin/profile", "sourceManifest": "/extras/ontokin/program/manifest",
                "programRevision": "/extras/ontokin/program/revision"},
            "records": records, "ownershipVerified": False, "completeC255Semantic": False,
            "executionAllowed": False, "realTrialSuccess": None, "historicalInputsBound": False,
            "transformHierarchyUsedAsOwnership": False, "limits": LIMITS.copy()}


def observe_glb_ownership(raw):
    return public(lambda: _artifact(raw))


def _compare(sources, raw):
    source, artifact = _source(sources), _artifact(raw)
    require(artifact["programRevision"] == source["programRevision"]
            and artifact["sourceManifest"] == source["sourceManifest"], "SOURCE_ARTIFACT_BINDING", "program and complete manifest")
    require(artifact["sourceUnits"] == source["sourceUnits"] and artifact["entrySourceId"] == "entry"
            and artifact["entrySourceIdClaim"] == "entry"
            and artifact["entryRevisionClaim"] == "sha256:"+source["sourceHashes"]["main.ok"]
            and artifact["moduleName"] == source["moduleName"] and artifact["sceneName"] == source["sceneName"]
            and artifact["profileName"] == "construction-0.1", "SOURCE_METADATA_BINDING", "duplicate source authority fields")
    expected = {tuple(row["id"]): row for row in source["records"]}
    actual = {tuple(row["id"]): row for row in artifact["records"]}
    require(set(actual) == set(expected), "IDENTITY_COVERAGE", "complete occurrence identities")
    verified = []
    for oid, wanted in expected.items():
        got = actual[oid]
        require(got["path"] == wanted["path"] and got["nodeName"] == wanted["path"]
                and got["definitionId"] == wanted["definitionId"]
                and got["className"] == "/".join(wanted["definitionId"]), "IDENTITY_BINDING", wanted["path"])
        require(got["nodeProgramRevision"] == source["programRevision"], "PROGRAM_BINDING", wanted["path"])
        for label, owner in got["claims"].items():
            require(owner == wanted["ownerPath"], "OWNERSHIP_MISMATCH", wanted["path"]+" "+label)
        for label in ("sourceMapping", "programOccurrence"):
            mapping = got[label]
            require(mapping["path"] == wanted["path"] and mapping["element_id"] == wanted["id"]
                    and mapping["definition_id"] == wanted["definitionId"]
                    and mapping["class_id"] == "/".join(wanted["definitionId"]), "IDENTITY_MAPPING", wanted["path"])
            for kind in ("declaration", "definition"):
                observed, measured = mapping[kind], wanted["origin"][kind]
                require(observed["filename"] == measured["file"]
                        and observed["source_id"] == ("entry" if measured["file"] == "main.ok"
                                                       else "package:"+PACKAGE+"@"+VERSION)
                        and type(observed["start_byte"]) is int and type(observed["end_byte"]) is int
                        and observed["start_byte"] == measured["startByte"]
                        and observed["end_byte"] == measured["endByteExclusive"]
                        and observed["source_revision"] == "sha256:"+source["sourceHashes"][measured["file"]],
                        "SOURCE_SPAN_BINDING", wanted["path"]+" "+kind)
        verified.append({"id": wanted["id"], "definitionId": wanted["definitionId"], "path": wanted["path"],
            "ownerId": wanted["ownerId"], "ownerPath": wanted["ownerPath"], "sourceOrigin": wanted["origin"],
            "artifactOrigins": got["origins"], "node": got["node"], "artifactSha256": artifact["artifactSha256"]})
    return {"schema": SCHEMA, "kind": "source-artifact-ownership-comparison", "ownershipConsistent": True,
            "sourceAssociationVerified": True, "programRevision": source["programRevision"],
            "sourceHashes": source["sourceHashes"], "artifactSha256": artifact["artifactSha256"],
            "sourceAuthorityOrigins": artifact["sourceAuthorityOrigins"],
            "records": verified, "objectCount": source["objectCount"], "rootCount": source["rootCount"],
            "edgeCount": source["edgeCount"], "historicalInputsBound": False, "sourceValidityQualified": False,
            "completeC255Semantic": False, "executionAllowed": False, "realTrialSuccess": None,
            "transformHierarchyUsedAsOwnership": False, "limits": LIMITS.copy()}


def compare_ownership(source_files, raw):
    return public(lambda: _compare(source_files, raw))


def read_bound_endpoint(repo, endpoint):
    def run():
        require(endpoint in PINS, "ENDPOINT", "before or after")
        root = Path(repo).resolve()
        def read(name, size, sha):
            path = root / PROOF / name
            require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root), "INPUT_PATH", name)
            require(path.stat().st_size == size, "INPUT_SIZE", name)
            with path.open("rb") as f:
                raw = f.read(size+1)
            require(len(raw) == size and digest(raw) == sha, "HISTORICAL_BINDING", name)
            return raw
        pins = PINS[endpoint]
        sources = {"main.ok": read(endpoint+".main.ok", 1708, pins["source"]),
                   "hinges.ok": read("hinges.ok", 1911, LIBRARY_SHA)}
        raw = read(endpoint+".glb", pins["bytes"], pins["glb"])
        result = _compare(sources, raw)
        result.update(historicalInputsBound=True, endpoint=endpoint,
                      artifactPath=PROOF+"/"+endpoint+".glb",
                      sourcePaths={"main.ok": PROOF+"/"+endpoint+".main.ok", "hinges.ok": PROOF+"/hinges.ok"})
        return result
    return public(run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--endpoint", choices=tuple(PINS), required=True)
    args = parser.parse_args()
    try:
        result = read_bound_endpoint(args.repo, args.endpoint)
    except (Fault, OSError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "REFUSED", "code": getattr(exc, "code", "IO"),
                          "detail": str(exc), "executionAllowed": False, "realTrialSuccess": None}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
