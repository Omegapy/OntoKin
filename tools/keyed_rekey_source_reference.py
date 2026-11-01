"""Independent source-span/origin readers for C086, with inherited finite readers.

The inherited byte tokenizer and origin-shape checks are preserved from C085.
Their explicit declaring-version tables add only the adopted .19 profile.
No production parser, runtime or exporter is imported.
"""
from __future__ import annotations
import copy
import json
import re
from tools.texture_reference import ReferenceError, canonical, digest, loads, require

ZIP_FIELDS = {"expression", "left", "right", "body", "left_element_type", "right_element_type", "output_element_type", "key", "left_entry", "right_entry"}
ZIP_LOCATIONS = ("expression", "left", "right", "body", "left_entry", "right_entry")

def canonical_probe_type(display):
    # These two documented presentation aliases occur in the frozen corpus.
    # No dimensional or generic leaf type is otherwise weakened or stripped.
    return {"Keyed<Quantity[m]>": "Keyed<Length>", "Quantity[m]": "Length",
            "Keyed<Quantity[m^2]>": "Keyed<Area>", "Quantity[m^2]": "Area",
            "Keyed<Point3>": "Keyed<Point3<Length>>", "Point3": "Point3<Length>"}.get(display, display)

def source_units(payload):
    return {"entry": payload["entry"], **{"package:" + u["package_id"] + "@" + u["version"]: u for u in payload["modules"]}}

def codes(value):
    if isinstance(value, dict):
        return sorted(set(([value["code"]] if isinstance(value.get("code"), str) else []) + [c for v in value.values() for c in codes(v)]))
    if isinstance(value, list):
        return sorted(set(c for v in value for c in codes(v)))
    return []

def walk(value, path=()):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, path + (key,))
    elif isinstance(value, list):
        for key, child in enumerate(value):
            yield from walk(child, path + (key,))

def check_location(location, units, *, allow_null=False):
    if location is None:
        require(allow_null, "Unexpected null source location")
        return None
    require(isinstance(location, dict), "Source location must be an object")
    key = location.get("source_id")
    require(key in units, "Source location refers to an absent unit")
    unit, start_key, end_key = units[key], "start_byte", "end_byte"
    if start_key not in location:
        start_key, end_key = "start", "end"
    start, end = location.get(start_key), location.get(end_key)
    raw = unit["source"].encode("utf-8")
    require(type(start) is int and type(end) is int and 0 <= start <= end <= len(raw), "Source location is out of range")
    # A source span must also terminate on UTF-8 boundaries.
    raw[:start].decode("utf-8"); raw[start:end].decode("utf-8"); raw[end:].decode("utf-8")
    if "source_revision" in location:
        require(location["source_revision"] == digest(raw), "Source span hash differs from original bytes")
    if "filename" in location:
        require(location["filename"] == unit["filename"], "Source span filename differs")
    if "file" in location:
        require(location["file"] == unit["filename"], "Source span file differs")
    return raw[start:end]

def same_location(actual, expected, units):
    check_location(actual, units)
    require(all(actual.get(k) == v for k, v in expected.items()), "Exact frozen source span differs")

def check_all_locations(value, units):
    count = 0
    for _, node in walk(value):
        if not isinstance(node, dict) or node.get("source_id") not in units:
            continue
        if ("start_byte" in node and "end_byte" in node) or ("start" in node and "end" in node):
            check_location(node, units); count += 1
        if "source_revision" in node:
            require(node["source_revision"] == digest(units[node["source_id"]]["source"].encode()), "Source revision lost byte binding")
    return count

def original_keyed_entries(units):
    """Recover complete keyed-entry spans from original token delimiters."""
    result={}
    for source_id,unit in units.items():
        raw=unit["source"].encode("utf-8");tokens=_source_tokens(raw)
        for i,token in enumerate(tokens[:-1]):
            if token[0]!=b"keyed" or tokens[i+1][0]!=b"<":
                continue
            types,opening=_type_arguments(tokens,i,b"keyed")
            require(len(types)==1 and tokens[opening][0]==b"{", "Malformed original keyed literal")
            closing=_closing_delimiter(tokens,opening)
            boundaries=[opening]+_top_level_commas(tokens,opening+1,closing)+[closing]
            for left,right in zip(boundaries,boundaries[1:]):
                start=left+1
                if start==right:
                    continue
                require(start+2<right and tokens[start][0].startswith(b'"') and tokens[start+1][0]==b":",
                        "Malformed original keyed entry")
                key=loads(tokens[start][0])
                location={"source_id":source_id,"source_revision":digest(raw),
                          "start_byte":tokens[start][1],"end_byte":tokens[right-1][2]}
                result[_location_identity(location)]={"key":key,"location":location}
    return result

def check_transforms(records, units, *, expected=None, require_nonempty=True):
    require(isinstance(records, list) and (not require_nonempty or records), "Missing ordered map derivation records")
    count = 0
    for record in records:
        base_fields = {"expression", "body", "input", "input_element_type", "output_element_type"}
        require(isinstance(record, dict) and set(record) in (base_fields, base_fields | {"key", "input_entry"}),
                "Transform projection has an unadopted shape")
        expression = check_location(record["expression"], units)
        require(b"map_keyed" in expression, "Derived expression does not identify the authored map")
        check_location(record["body"], units); check_location(record["input"], units)
        for name in ("body", "input"):
            location, outer = record[name], record["expression"]
            require(location["source_id"] == outer["source_id"] and
                    outer["start_byte"] <= location["start_byte"] < location["end_byte"] <= outer["end_byte"],
                    "Map body/input lies outside its exact expression")
        require(all(type(record[k]) is str and record[k] for k in ("input_element_type", "output_element_type")), "Missing map element types")
        authored = intrinsic_source_shape(record["expression"], units, b"map_keyed")
        for part in ("input", "body"):
            same_location(record[part], authored["parts"][part], units)
        require(canonical_probe_type(record["output_element_type"]) == authored["element_type"],
                "Map output type differs from its explicit source type")
        if "key" in record:
            require(type(record["key"]) is str and record["key"].isascii() and record["key"], "Derived leaf lost its stable input key")
            raw_entry = check_location(record["input_entry"], units, allow_null=True)
            if raw_entry is not None:
                require(re.match(re.escape(canonical(record["key"])) + rb"\s*:", raw_entry) is not None,
                        "Derived leaf entry span identifies another original key")
        count += 1
    if expected is not None:
        record = records[-1]
        for part in ("expression", "body", "input"):
            same_location(record[part], expected[part], units)
        expected_input = expected.get("input_element_type") or ("Length" if expected["input_element_kind"] == "Quantity" else expected["input_element_kind"])
        require(record["input_element_type"] == expected_input and record["output_element_type"] == expected.get("output_element_type", "Length"), "Panel map element dimensions differ")
    return count

def _location_identity(value):
    return (value.get("source_id"), value.get("start_byte", value.get("start")),
            value.get("end_byte", value.get("end")))

def _source_tokens(raw):
    """Bounded byte-level delimiter reader; never evaluates OntoKin source."""
    require(len(raw) <= 1048576, "Independent source delimiter input exceeds its bound")
    tokens, index = [], 0
    while index < len(raw):
        byte, start = raw[index], index
        if byte in b" \t\r\n":
            index += 1
            continue
        if raw.startswith(b"//", index):
            end = raw.find(b"\n", index + 2)
            index = len(raw) if end < 0 else end
            continue
        if raw.startswith(b"/*", index):
            end = raw.find(b"*/", index + 2)
            require(end >= 0, "Unterminated source delimiter comment")
            index = end + 2
            continue
        if byte == 34:
            index += 1
            while index < len(raw) and raw[index] != 34:
                index += 2 if raw[index] == 92 else 1
            require(index < len(raw), "Unterminated source delimiter string")
            index += 1
        elif byte in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789":
            index += 1
            while index < len(raw) and raw[index] in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789":
                index += 1
        elif raw.startswith(b"->", index):
            index += 2
        else:
            index += 1
        tokens.append((raw[start:index], start, index))
        require(len(tokens) <= 262144, "Independent source token inventory exceeds its bound")
    return tokens

def _generic_type(tokens, name_index, name):
    require(tokens[name_index][0] == name and tokens[name_index + 1][0] == b"<",
            "Source expression lost its explicit type argument")
    depth, index = 1, name_index + 2
    while index < len(tokens) and depth:
        token = tokens[index][0]
        depth += (token == b"<") - (token == b">")
        require(depth <= 64 and token != b",", "Independent type delimiter bound/arity differs")
        index += 1
    require(depth == 0 and index > name_index + 3, "Unterminated/empty explicit source type")
    return b"".join(t[0] for t in tokens[name_index + 2:index - 1]).decode("ascii"), index

def _type_arguments(tokens, name_index, name):
    """Read generic separators independently of expression commas."""
    require(tokens[name_index][0] == name and tokens[name_index + 1][0] == b"<",
            "Source expression lost explicit generic arguments")
    depth, start, values, cursor = 1, name_index + 2, [], name_index + 2
    while cursor < len(tokens):
        token = tokens[cursor][0]
        if token == b"<":
            depth += 1
            require(depth <= 64, "Independent generic depth exceeds its bound")
        elif token == b">":
            depth -= 1
            if depth == 0:
                require(start < cursor, "Empty explicit type argument")
                values.append(b"".join(t[0] for t in tokens[start:cursor]).decode("ascii"))
                return values, cursor + 1
        elif token == b"," and depth == 1:
            require(start < cursor, "Empty explicit type argument")
            values.append(b"".join(t[0] for t in tokens[start:cursor]).decode("ascii"))
            start = cursor + 1
        cursor += 1
    raise ReferenceError("Unterminated explicit generic arguments")

def _closing_delimiter(tokens, start):
    closes = {b"(": b")", b"[": b"]", b"{": b"}"}
    require(start < len(tokens) and tokens[start][0] in closes, "Missing source opening delimiter")
    stack = []
    for index in range(start, len(tokens)):
        token = tokens[index][0]
        if token in closes:
            stack.append(closes[token])
            require(len(stack) <= 128, "Independent source delimiter depth exceeds its bound")
        elif token in closes.values():
            require(stack and stack.pop() == token, "Mismatched source expression delimiter")
            if not stack:
                return index
    raise ReferenceError("Unterminated source expression delimiter")

def _top_level_commas(tokens, start, end):
    commas, index = [], start
    while index < end:
        token = tokens[index][0]
        if (token in (b"zip_keyed", b"map_keyed", b"reduce_keyed", b"filter_keyed", b"merge_keyed", b"keyed")
                and index + 1 < end and tokens[index + 1][0] == b"<"):
            _, after = _type_arguments(tokens, index, token)
            require(after < end, "Source type arguments cross expression boundary")
            index = after - 1
        elif token in (b"(", b"[", b"{"):
            index = _closing_delimiter(tokens, index)
            require(index < end, "Source child expression crosses its enclosing boundary")
        elif token in (b")", b"]", b"}"):
            raise ReferenceError("Unmatched source child delimiter")
        elif token == b",":
            commas.append(index)
        index += 1
    return commas

def _declared_keyed_types(name, units, *, function=False):
    """Read only explicit annotations, without type inference or execution."""
    candidates = set()
    for unit in units.values():
        tokens = _source_tokens(unit["source"].encode("utf-8"))
        for index, token in enumerate(tokens):
            if token[0] != name:
                continue
            cursor = index + 1
            if cursor < len(tokens) and tokens[cursor][0] == b"@":
                cursor += 2  # declaration's authored stable string key
            if function:
                if index == 0 or tokens[index - 1][0] != b"fn" or cursor >= len(tokens) or tokens[cursor][0] != b"(":
                    continue
                cursor = _closing_delimiter(tokens, cursor) + 1
                if cursor >= len(tokens) or tokens[cursor][0] != b"->":
                    continue
            elif cursor >= len(tokens) or tokens[cursor][0] != b":":
                continue
            cursor += 1
            if cursor + 1 < len(tokens) and tokens[cursor][0] == b"Keyed" and tokens[cursor + 1][0] == b"<":
                leaf, _ = _generic_type(tokens, cursor, b"Keyed")
                candidates.add(canonical_probe_type(leaf))
    return candidates

def intrinsic_locations(units, operation):
    """Inventory authored generic calls without running the product parser."""
    locations = []
    for source_id, unit in units.items():
        raw = unit["source"].encode("utf-8")
        tokens = _source_tokens(raw)
        for index, token in enumerate(tokens[:-1]):
            if token[0] != operation or tokens[index + 1][0] != b"<":
                continue
            types, opening = _type_arguments(tokens, index, operation)
            require(len(types) == (3 if operation == b"zip_keyed" else 1),
                    "Intrinsic generic arity differs")
            if opening >= len(tokens) or tokens[opening][0] != b"(":
                continue
            closing = _closing_delimiter(tokens, opening)
            locations.append({"source_id": source_id, "source_revision": digest(raw),
                              "start_byte": token[1], "end_byte": tokens[closing][2]})
    return locations

def intrinsic_source_shape(location, units, operation=b"filter_keyed"):
    """Read exact map/filter argument spans and explicit type delimiters."""
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Intrinsic source span includes non-expression boundary bytes")
    start, stop = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == stop - 1:
        start += 1; stop -= 1
    element_type, opening = _generic_type(tokens, start, operation)
    closing = _closing_delimiter(tokens, opening)
    require(closing == stop - 1 and tokens[opening][0] == b"(",
            "Intrinsic source span is not the complete authored call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 1, "Intrinsic source lost its exact two arguments")
    comma = commas[0]
    binder_start = comma + 1
    binder_end = _closing_delimiter(tokens, binder_start)
    require(tokens[binder_start][0] == b"(" and binder_end + 2 < closing and tokens[binder_end + 1][0] == b"->",
            "Intrinsic source lost its binder/body delimiter")
    binders = [t[0] for t in tokens[binder_start + 1:binder_end]]
    require(len(binders) == 3 and binders[1] == b"," and
            all(re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*", binders[i]) for i in (0, 2)),
            "Intrinsic source does not have its exact two binders")
    name = "predicate" if operation == b"filter_keyed" else "body"
    ranges = {"input": (opening + 1, comma), name: (binder_end + 2, closing)}
    base, source_id = location.get("start_byte", location.get("start")), location["source_id"]
    parts = {}
    for part, (start, end) in ranges.items():
        require(start < end, "Intrinsic source has an empty " + part)
        parts[part] = {"source_id": source_id, "source_revision": digest(units[source_id]["source"].encode("utf-8")),
                       "start_byte": base + tokens[start][1], "end_byte": base + tokens[end - 1][2]}
    return {"parts": parts, "element_type": canonical_probe_type(element_type)}

def filter_source_shape(location, units):
    unit = units[location["source_id"]]
    require(location.get("source_revision") == digest(unit["source"].encode("utf-8")),
            "Filter expression lost original source revision binding")
    pairs = (("0.16", "keyed-filter-0.1"), ("0.17", "keyed-merge-0.1"), ("0.18", "keyed-zip-0.1"), ("0.19", "keyed-rekey-0.1"))
    require(any(re.search(r'\bontokin\s+"' + re.escape(version) + r'"\s*;', unit["source"]) and
                re.search(r'\bprofile\s+"' + re.escape(profile) + r'"\s*;', unit["source"])
                for version, profile in pairs), "Filter origin has an incompatible declaring-unit contract")
    return intrinsic_source_shape(location, units)

def check_filters(records, units, *, expected=None, require_nonempty=True):
    """Validate closed read-only records and original UTF-8 expression identity."""
    require(isinstance(records, list) and (records or not require_nonempty), "Missing ordered filter derivation records")
    fields = {"expression", "input", "predicate", "element_type"}
    seen = set()
    for index, record in enumerate(records):
        require(isinstance(record, dict) and set(record) == fields,
                "Filter projection has an unadopted shape or invented identity")
        authored = filter_source_shape(record["expression"], units)
        for part in ("input", "predicate"):
            same_location(record[part], authored["parts"][part], units)
        require(record["element_type"] == authored["element_type"],
                "Filter element type differs from its canonical resolved explicit source type")
        identity = _location_identity(record["expression"])
        require(identity not in seen, "Duplicate filter source derivation")
        seen.add(identity)
        for earlier in records[:index]:
            a, b = earlier["expression"], record["expression"]
            require(not (a["source_id"] == b["source_id"] and
                    a["start_byte"] < b["start_byte"] and b["end_byte"] <= a["end_byte"]),
                    "Nested filter provenance is not in evaluation order")
    if expected is not None:
        wanted_records = expected if isinstance(expected, list) else [expected]
        for wanted in wanted_records:
            matches = [record for record in records if _location_identity(record["expression"]) == _location_identity(wanted["expression"])]
            require(len(matches) == 1, "Frozen filter expression absent or duplicated")
            for name in ("expression", "input", "predicate"):
                same_location(matches[0][name], wanted[name], units)
            require(matches[0]["element_type"] == wanted["element_type"], "Frozen filter type differs")
    return len(records)

def require_filter_order(records, expected, units):
    check_filters(records, units, require_nonempty=bool(expected))
    require([_location_identity(record["expression"]) for record in records] ==
            [_location_identity(location) for location in expected],
            "Filter derivations differ from frozen actual evaluation order")
    require_expression_origins(records, expected, units, "filter")

def nominal_definition_id(locator, units):
    """Resolve a frozen source-qualified locator to inherited .2 nominal identity.

    OK-LANG-002 section 3.3 separates source ID/version from the stable nominal
    package/module/key ID. Neither form may be silently used in place of the
    other: bind the exact unit pin and authored declaration before translating.
    """
    require(isinstance(locator, list) and len(locator) == 4 and locator[2] == "definitions" and locator[0] in units,
            "Frozen called-definition locator has no exact source unit")
    unit = units[locator[0]]
    raw = unit["source"].encode("utf-8")
    module = re.search(rb'\bmodule\s+[A-Za-z_][A-Za-z_0-9]*\s*@\s*("(?:[^"\\]|\\.)*")', raw)
    require(module is not None and loads(module[1]) == locator[1], "Called-definition locator names another module key")
    declaration = re.search(rb'\bfn\s+[A-Za-z_][A-Za-z_0-9]*\s*@\s*' + re.escape(canonical(locator[3])) + rb'\s*\(', raw)
    require(declaration is not None, "Called-definition locator names an absent authored function key")
    if locator[0] == "entry":
        require(unit.get("package_id") is None and unit.get("version") is None, "Entry definition acquired a package pin")
        prefix = ["entry"]
    else:
        require(locator[0] == "package:" + unit["package_id"] + "@" + unit["version"], "Called-definition source pin differs")
        prefix = ["package", unit["package_id"]]
    return tuple(prefix + locator[1:])

def reduction_source_shape(location, units):
    """Read exact input/seed/body spans and explicit types from frozen bytes.

    This finite provenance reader splits source delimiters and annotations. It
    does not evaluate expressions or resolve general overloads. Input types
    are checked for explicit keyed/map syntax and unambiguous declared keyed
    names/helper returns; the frozen corpus uses only those forms.
    """
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Reduction expression span includes non-expression boundary bytes")
    start, stop = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == stop - 1:
        start += 1; stop -= 1
    accumulator, opening = _generic_type(tokens, start, b"reduce_keyed")
    closing = _closing_delimiter(tokens, opening)
    require(closing == stop - 1 and tokens[opening][0] == b"(",
            "Reduction expression span is not the complete authored call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 2, "Reduction source does not have exact input/seed/binder-body arguments")
    first, second = commas
    binder_start = second + 1
    binder_end = _closing_delimiter(tokens, binder_start)
    require(tokens[binder_start][0] == b"(" and binder_end + 2 < closing and tokens[binder_end + 1][0] == b"->",
            "Reduction source lost its binder/body delimiter")
    binders = [t[0] for t in tokens[binder_start + 1:binder_end]]
    require(len(binders) == 5 and binders[1] == binders[3] == b"," and
            all(re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*", binders[i]) for i in (0, 2, 4)),
            "Reduction source does not have its exact three binders")
    ranges = {"input": (opening + 1, first), "seed": (first + 1, second), "body": (binder_end + 2, closing)}
    base = location.get("start_byte", location.get("start"))
    source_id = location["source_id"]
    parts = {}
    for name, (start, end) in ranges.items():
        require(start < end, "Reduction source has an empty " + name + " expression")
        parts[name] = {"source_id": source_id, "source_revision": digest(units[source_id]["source"].encode("utf-8")),
                       "start_byte": base + tokens[start][1], "end_byte": base + tokens[end - 1][2]}
    input_tokens = tokens[opening + 1:first]
    input_type = None
    if input_tokens[0][0] == b"zip_keyed":
        types, _ = _type_arguments(input_tokens, 0, b"zip_keyed")
        require(len(types) == 3, "Reduction input zip lost exact type arity")
        input_type = types[2]
    elif input_tokens[0][0] in (b"keyed", b"map_keyed", b"filter_keyed", b"merge_keyed"):
        input_type, _ = _generic_type(input_tokens, 0, input_tokens[0][0])
    else:
        names = [t[0] for t in input_tokens]
        if len(names) == 1 or len(names) == 3 and names[:2] == [b"self", b"."]:
            types = _declared_keyed_types(names[-1], {source_id: units[source_id]})
        elif b"(" in names:
            opening_call = names.index(b"(")
            prefix = names[:opening_call]
            types = (_declared_keyed_types(prefix[-1], units, function=True)
                     if len(prefix) == 1 or len(prefix) == 3 and prefix[1] == b"." else set())
        else:
            types = set()
        if len(types) == 1:
            input_type = next(iter(types))
    return {"parts": parts, "accumulator_type": canonical_probe_type(accumulator),
            "input_element_type": None if input_type is None else canonical_probe_type(input_type)}

def check_reductions(records, units, *, expected=None, require_nonempty=True):
    """Bind every aggregate derivation to original source without writable IDs."""
    require(isinstance(records, list) and (records or not require_nonempty),
            "Missing ordered reduction derivation records")
    fields = {"expression", "input", "seed", "body", "input_element_type", "accumulator_type"}
    seen = set()
    for index, record in enumerate(records):
        require(isinstance(record, dict) and set(record) == fields,
                "Reduction projection has an unadopted shape or invented identity")
        expression = check_location(record["expression"], units)
        require(b"reduce_keyed<" in expression, "Derived expression is not the authored reduction")
        outer = record["expression"]
        for name in ("input", "seed", "body"):
            child = record[name]
            check_location(child, units)
            require(child["source_id"] == outer["source_id"] and
                    outer["start_byte"] <= child["start_byte"] < child["end_byte"] <= outer["end_byte"],
                    "Reduction input/seed/body lies outside its exact expression")
        require(all(type(record[k]) is str and record[k] for k in ("input_element_type", "accumulator_type")),
                "Missing reduction input/accumulator types")
        authored = reduction_source_shape(outer, units)
        for name in ("input", "seed", "body"):
            same_location(record[name], authored["parts"][name], units)
        require(canonical_probe_type(record["accumulator_type"]) == authored["accumulator_type"],
                "Reduction accumulator type differs from its explicit source type")
        if authored["input_element_type"] is not None:
            require(canonical_probe_type(record["input_element_type"]) == authored["input_element_type"],
                    "Reduction input element type differs from its explicit source annotation")
        identity = tuple(_location_identity(record[name]) for name in ("expression", "input", "seed", "body")) + (
            record["input_element_type"], record["accumulator_type"])
        require(identity not in seen, "Duplicate reduction source derivation")
        seen.add(identity)
        # A nested selected reduction completes before its enclosing fold.
        for earlier in records[:index]:
            a, b = earlier["expression"], outer
            require(not (a["source_id"] == b["source_id"] and
                    a["start_byte"] < b["start_byte"] and b["end_byte"] <= a["end_byte"]),
                    "Nested reduction provenance is not in evaluation order")
    if expected is not None:
        matches = [record for record in records
                   if _location_identity(record["expression"]) == _location_identity(expected["expression"])]
        require(len(matches) == 1, "Frozen reduction expression is absent or duplicated")
        current = matches[0]
        for name in ("expression", "input", "seed", "body"):
            same_location(current[name], expected[name], units)
        wanted_input = expected.get("input_element_type", "Length")
        wanted_acc = expected.get("accumulator_type", "Length")
        require(current["input_element_type"] == wanted_input and current["accumulator_type"] == wanted_acc,
                "Frozen reduction dimensions differ")
    return len(records)

def require_expression_origins(records, expected, units, label):
    for wanted in expected:
        check_location(wanted, units)
        matches = [record for record in records
                   if _location_identity(record["expression"]) == _location_identity(wanted)]
        require(matches, "Actual value lost a required " + label + " expression")
        for match in matches:
            same_location(match["expression"], wanted, units)

def inspect_member(items, object_path, name):
    matches = [item["values"][name] for item in items if name in item.get("values", {}) and
               (item.get("path") in (object_path, object_path + "." + name) or item.get("name") == name)]
    require(matches and all(item == matches[0] for item in matches),
            "Requested public member is absent/ambiguous: " + object_path + "." + name)
    return matches[0]

def check_keyed_membership(value, keys, *, scalars=None):
    require(type(value.get("type")) is str and value["type"].startswith("Keyed<") and isinstance(value.get("value"), list),
            "Expected a typed keyed inspection value")
    entries = value["value"]
    actual = [entry.get("key") for entry in entries]
    require(actual == sorted(keys) and len(actual) == len(set(actual)), "Exact surviving key membership/order differs")
    require(all(type(key) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", key) for key in actual),
            "Surviving stable key violates inherited identity grammar")
    leaf_type = canonical_probe_type(value["type"][6:-1])
    for entry in entries:
        require(set(entry) == {"key", "value"} and isinstance(entry["value"], dict), "Keyed entry projection has an invented identity")
        require(canonical_probe_type(entry["value"]["type"]) == leaf_type, "Surviving leaf type differs from its keyed type")
        if scalars is not None:
            got, wanted = entry["value"]["value"], scalars[entry["key"]]
            require(got == wanted and (type(got) is type(wanted) or
                    leaf_type not in ("Int", "Bool", "String") and type(got) in (int, float) and type(wanted) in (int, float)),
                    "Surviving scalar leaf value differs")
    return len(entries)

def merge_location(actual, expected, units):
    """Every runtime merge location has exactly the adopted five fields."""
    enriched = {**expected, "filename": units[expected["source_id"]]["filename"]}
    require(set(enriched) == {"source_id", "source_revision", "filename", "start_byte", "end_byte"},
            "Independent merge location has an unexpected authored shape")
    check_location(actual, units)
    require(actual == enriched, "Merge provenance location differs from its complete original source expression")

def merge_source_shape(location, units):
    """Split two original operands, preserving complete grouping parentheses."""
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Merge expression span includes whitespace/comment boundary bytes")
    start, end = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == end - 1:
        start += 1; end -= 1
    element_type, opening = _generic_type(tokens, start, b"merge_keyed")
    closing = _closing_delimiter(tokens, opening)
    require(closing == end - 1, "Merge source span is not a complete grouped call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 1, "Merge source does not contain its exact two operands")
    unit = units[location["source_id"]]
    require(any(re.search(r'\bontokin\s+"' + re.escape(version) + r'"\s*;', unit["source"]) and
                re.search(r'\bprofile\s+"' + re.escape(profile) + r'"\s*;', unit["source"])
                for version, profile in (("0.17", "keyed-merge-0.1"), ("0.18", "keyed-zip-0.1"), ("0.19", "keyed-rekey-0.1"))),
            "Intrinsic merge provenance belongs to another declaring-unit version")
    base = location["start_byte"]
    parts = {}
    for name, (first, stop) in {"left": (opening + 1, commas[0]), "right": (commas[0] + 1, closing)}.items():
        require(first < stop, "Merge source contains an empty operand")
        parts[name] = {"source_id": location["source_id"], "source_revision": digest(unit["source"].encode()),
                       "start_byte": base + tokens[first][1], "end_byte": base + tokens[stop - 1][2]}
    return {"parts": parts, "element_type": canonical_probe_type(element_type)}

def check_merges(records, units, *, expected=None, require_nonempty=True, exact=False):
    require(isinstance(records, list) and (records or not require_nonempty), "Missing ordered merge derivation records")
    fields = {"expression", "left", "right", "element_type", "input_side"}
    seen = set()
    for record in records:
        require(isinstance(record, dict) and set(record) == fields,
                "Merge projection contains unadopted fields or invented identity")
        authored = merge_source_shape(record["expression"], units)
        for part in ("expression", "left", "right"):
            wanted = record[part] if part == "expression" else authored["parts"][part]
            merge_location(record[part], wanted, units)
        require(record["element_type"] == authored["element_type"], "Merge element type differs from its canonical explicit source type")
        require(record["input_side"] in ("both", "left", "right"), "Merge input side is outside the adopted vocabulary")
        identity = canonical(record)
        require(identity not in seen, "Duplicate exact merge provenance record")
        seen.add(identity)
    if expected is not None:
        enriched = [{**wanted, **{part: {**wanted[part], "filename": units[wanted[part]["source_id"]]["filename"]}
                                 for part in ("expression", "left", "right")}} for wanted in expected]
        if exact:
            require(records == enriched, "Exact merge provenance sequence or contribution sides differ")
        else:
            require(all(record in records for record in enriched), "Required authored merge record is absent")
    return len(records)

def with_merge_side(record, side):
    return {**record, "input_side": side}

def zip_source_shape(location, units):
    """Read a full original triple/binder call, without parsing or executing DSL."""
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Zip source span has non-expression boundary bytes")
    start, stop = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == stop - 1:
        start += 1; stop -= 1
    types, opening = _type_arguments(tokens, start, b"zip_keyed")
    require(len(types) == 3 and tokens[opening][0] == b"(", "Zip lost exactly T,U,V or call delimiter")
    closing = _closing_delimiter(tokens, opening)
    require(closing == stop - 1, "Zip source does not span its complete call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 2, "Zip does not contain exact left/right/binder-body arguments")
    first, second = commas
    binder_start = second + 1
    binder_end = _closing_delimiter(tokens, binder_start)
    require(tokens[binder_start][0] == b"(" and binder_end + 2 < closing and tokens[binder_end + 1][0] == b"->",
            "Zip lost binder/body delimiter")
    binders = [t[0] for t in tokens[binder_start + 1:binder_end]]
    require(len(binders) == 5 and binders[1] == binders[3] == b"," and
            all(re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*", binders[i]) for i in (0,2,4)) and
            len({binders[i] for i in (0,2,4)}) == 3, "Zip does not have three distinct named binders")
    unit = units[location["source_id"]]
    require(any(re.search(r'\bontokin\s+"'+re.escape(version)+r'"\s*;', unit["source"]) and
                re.search(r'\bprofile\s+"'+re.escape(profile)+r'"\s*;', unit["source"])
                for version, profile in (("0.18", "keyed-zip-0.1"), ("0.19", "keyed-rekey-0.1"))),
            "Zip provenance belongs to another declaring-unit contract")
    parts = {}
    for name, (left, right) in {"left":(opening+1,first),"right":(first+1,second),"body":(binder_end+2,closing)}.items():
        require(left < right, "Zip has an empty operand or body")
        parts[name] = {"source_id":location["source_id"], "source_revision":digest(unit["source"].encode()),
                       "start_byte":location["start_byte"]+tokens[left][1],
                       "end_byte":location["start_byte"]+tokens[right-1][2]}
    return {"parts":parts, "left_element_type":canonical_probe_type(types[0]),
            "right_element_type":canonical_probe_type(types[1]), "output_element_type":canonical_probe_type(types[2]),
            "binders":[binders[i].decode('ascii') for i in (0,2,4)]}

def enriched_zip_records(records, units):
    result=[]
    for record in records:
        current=copy.deepcopy(record)
        for field in ZIP_LOCATIONS:
            value=current[field]
            if value is not None:
                current[field] = {**value,"filename":units[value["source_id"]]["filename"]}
        result.append(current)
    return result

def check_zips(records, units, *, expected=None, require_nonempty=True, exact=False, aggregate=False):
    """Require exact original five-field locations and ten-field zip records."""
    require(isinstance(records,list) and (records or not require_nonempty), "Missing ordered zip provenance")
    seen=set()
    original_entries=original_keyed_entries(units) if any(isinstance(r,dict) and r.get("key") is not None for r in records) else {}
    for record in records:
        require(isinstance(record,dict) and set(record)==ZIP_FIELDS, "Zip record has missing or unadopted fields")
        shape=zip_source_shape(record["expression"],units)
        for part in ("expression","left","right","body"):
            wanted=record[part] if part=="expression" else shape["parts"][part]
            merge_location(record[part],wanted,units)
        for part in ("left_element_type","right_element_type","output_element_type"):
            require(record[part]==shape[part], "Zip exact canonical boundary type differs from authored explicit type")
        key=record["key"]
        require(key is None or type(key) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}",key),
                "Zip paired key violates the original stable-key grammar")
        if key is None or aggregate:
            require(key is None and record["left_entry"] is None and record["right_entry"] is None,
                    "Keyed aggregate invented a paired contributor")
        else:
            for field in ("left_entry","right_entry"):
                entry=record[field]
                if entry is None:
                    continue
                merge_location(entry,entry,units)
                raw=check_location(entry,units)
                tokens=_source_tokens(raw)
                require(tokens and tokens[0][1]==0 and tokens[-1][2]==len(raw) and
                        tokens[0][0]==canonical(key) and len(tokens)>=3 and tokens[1][0]==b":" and tokens[-1][0]!=b",",
                        "Zip contributor is not the full original matching keyed entry")
                original=original_entries.get(_location_identity(entry))
                require(original is not None and original["key"]==key,
                        "Zip contributor span abbreviates or crosses the complete original keyed entry")
        identity=canonical(record)
        require(identity not in seen, "Duplicate exact zip provenance record")
        seen.add(identity)
    if expected is not None:
        wanted=enriched_zip_records(expected,units)
        require(records==wanted if exact else all(record in records for record in wanted),
                "Exact frozen zip provenance sequence or original pair differs")
    return len(records)

REKEY_FIELDS = {"expression", "input", "body", "element_type", "old_key", "new_key", "input_entry"}
LOCATION_FIELDS = {"source_id", "source_revision", "filename", "start_byte", "end_byte"}
KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


def rekey_source_shape(location, units):
    """Resolve complete byte-delimited call/input/body/binders independently."""
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Rekey expression includes non-expression boundary bytes")
    start, stop = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == stop - 1:
        start += 1; stop -= 1
    element_type, opening = _generic_type(tokens, start, b"rekey_keyed")
    closing = _closing_delimiter(tokens, opening)
    require(tokens[opening][0] == b"(" and closing == stop - 1,
            "Rekey source is not the complete call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 1, "Rekey lost exact input and binder/body arguments")
    comma = commas[0]
    binder_start = comma + 1
    binder_end = _closing_delimiter(tokens, binder_start)
    require(tokens[binder_start][0] == b"(" and tokens[binder_end + 1][0] == b"->" and
            binder_end + 2 < closing, "Rekey lost its binder/body delimiter")
    names = [token[0] for token in tokens[binder_start + 1:binder_end]]
    require(len(names) == 3 and names[1] == b"," and names[0] != names[2] and
            all(re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*", names[index]) for index in (0, 2)),
            "Rekey does not have exactly two distinct binders")
    unit = units[location["source_id"]]
    require(re.search(r'\bontokin\s+"0\.19"\s*;', unit["source"]) and
            re.search(r'\bprofile\s+"keyed-rekey-0\.1"\s*;', unit["source"]),
            "Rekey origin has another declaring-unit contract")
    ranges = {"input": (opening + 1, comma), "body": (binder_end + 2, closing)}
    parts = {}
    for name, (first, end) in ranges.items():
        require(first < end, "Empty rekey " + name + " source expression")
        parts[name] = {"source_id": location["source_id"], "source_revision": digest(unit["source"].encode()),
            "filename": unit["filename"], "start_byte": location["start_byte"] + tokens[first][1],
            "end_byte": location["start_byte"] + tokens[end - 1][2]}
    return {"parts": parts, "element_type": canonical_probe_type(element_type),
            "binders": [names[0].decode(), names[2].decode()]}


def exact_location(actual, expected, units):
    require(isinstance(actual, dict) and set(actual) == LOCATION_FIELDS,
            "Origin location does not have exactly five detached fields")
    merge_location(actual, expected, units)


def check_rekeys(records, units, *, expected=None, exact=False, aggregate=False, require_nonempty=True):
    require(isinstance(records, list) and (records or not require_nonempty),
            "Missing ordered rekey records")
    seen = set()
    entries = original_keyed_entries(units)
    for record in records:
        require(isinstance(record, dict) and set(record) == REKEY_FIELDS,
                "Rekey projection has an unadopted field set or identity")
        shape = rekey_source_shape(record["expression"], units)
        exact_location(record["expression"], record["expression"], units)
        for name in ("input", "body"):
            exact_location(record[name], shape["parts"][name], units)
        require(record["element_type"] == shape["element_type"], "Rekey canonical payload type differs")
        old_key, new_key, entry = record["old_key"], record["new_key"], record["input_entry"]
        if old_key is None or new_key is None:
            require(old_key is new_key is entry is None, "Rekey aggregate acquired a fabricated contributor")
        else:
            require(not aggregate and type(old_key) is type(new_key) is str and KEY.fullmatch(old_key) and
                    KEY.fullmatch(new_key), "Selected rekey keys violate exact domain or aggregate shape")
            if entry is not None:
                exact_location(entry, entry, units)
                require(_location_identity(entry) in entries, "Rekey payload entry is not a complete original keyed entry")
        identity = canonical(record)
        require(identity not in seen, "Rekey whole-record deduplication differs")
        seen.add(identity)
    if expected is not None:
        if exact:
            require(records == expected, "Exact rekey source/old/new/payload-entry sequence differs")
        else:
            require(all(item in records for item in expected), "Required original rekey contributor is absent")
    return len(records)


def semantic_value(value, units):
    """Typed-value comparison only; never used for GLB metadata normalization."""
    if isinstance(value, list):
        return [semantic_value(child, units) for child in value]
    if not isinstance(value, dict):
        return value
    location = value.get("source_id") in units and (("start" in value and "end" in value) or
        ("start_byte" in value and "end_byte" in value))
    result = {}
    for name, child in value.items():
        if name in ("derived_transforms", "derived_reductions", "derived_filters", "derived_merges", "derived_zips", "derived_rekeys", "input_entry"):
            continue
        if location and name in ("source_revision", "filename", "start", "end", "start_byte", "end_byte"):
            continue
        result[name] = semantic_value(child, units)
    return result


def diagnostic_anchor(receipt, case, units):
    wanted = case.get("expected_diagnostic")
    candidates = [value for _, value in walk(receipt) if isinstance(value, dict) and
                  value.get("code") == case["expected_code"] and "primary" in value]
    require(candidates, "Refusal lacks its original source diagnostic")
    diagnostic = candidates[0]
    if wanted:
        for field in ("code", "category", "phase", "rule_ids", "message", "details"):
            require(diagnostic.get(field) == wanted[field], "Exact new diagnostic differs: " + field)
        def check(actual, expected):
            check_location(actual, units)
            projected = {"source_id": actual.get("source_id"), "source_revision": actual.get("source_revision"),
                "filename": actual.get("filename", actual.get("file")), "start_byte": actual.get("start_byte"),
                "end_byte": actual.get("end_byte")}
            require(projected == expected, "Exact original diagnostic token/entry differs")
        check(diagnostic["primary"], wanted["primary"])
        require(len(diagnostic.get("related", [])) == len(wanted["related"]), "Related producer roles changed")
        for actual, expected in zip(diagnostic["related"], wanted["related"]):
            check(actual, expected)
    elif diagnostic["primary"] is not None:
        check_location(diagnostic["primary"], units)
    return {"code": diagnostic["code"], "primary": diagnostic["primary"],
            "related": diagnostic.get("related", []), "exact_new_boundary": wanted is not None}


def check_origin_projection(projection, units, *, control=False):
    readers = {"transforms": check_transforms, "reductions": check_reductions, "filters": check_filters,
               "merges": check_merges, "zips": check_zips, "rekeys": check_rekeys}
    counts = {name: 0 for name in readers}
    for _, value in walk(projection):
        if not isinstance(value, dict):
            continue
        for name, reader in readers.items():
            for prefix in ("derived_", "input_"):
                field = prefix + name
                if field in value:
                    require(not (control and name == "rekeys"), "Explicit .18 control acquired .19 origin fields")
                    count = reader(value[field], units)
                    counts[name] += count
        if isinstance(value.get("type"), str) and value["type"].startswith("Keyed<") and "derived_rekeys" in value:
            check_rekeys(value["derived_rekeys"], units, aggregate=True)
    return counts


def check_core_inspection(actual, control, case, fixtures):
    from tools.keyed_rekey_reference import case_payload
    payload, old_payload = case_payload(fixtures, case), case_payload(fixtures, case, control=True)
    units, old_units = source_units(payload), source_units(old_payload)
    require(actual.get("program_revision") == case["program_revision"] and
            control.get("program_revision") == case["explicit_c085_control"]["program_revision"],
            "Inspection immutable source identity differs")
    require(actual.get("ok") is not False and control.get("ok") is not False and
            not any(code.startswith(("OKL-E-", "OKE-E-")) for code in codes(actual) + codes(control)),
            "Valid source/control inspection failed")
    items, old_items = actual.get("items", []), control.get("items", [])
    require(items and old_items, "Actual inspection omitted object/member records")
    locations = check_all_locations(actual, units) + check_all_locations(control, old_units)
    counts = check_origin_projection(actual, units)
    check_origin_projection(control, old_units, control=True)
    value, previous = inspect_member(items, "shape", "result"), inspect_member(old_items, "shape", "result")
    require(value.get("status") == previous.get("status") == "resolved" and not value.get("stale") and not previous.get("stale"),
            "Public result is unresolved or stale")
    require(value["type"] == previous["type"] and value.get("frame") == previous.get("frame") and
            value.get("canonical_unit") == previous.get("canonical_unit"), "Exact output type/frame/unit differs")
    require(semantic_value(value["value"], units) == semantic_value(previous["value"], old_units),
            "Complete typed output differs from the independently authored .18 literal control")
    expected = case.get("expected") or {}
    keyed = value["type"].startswith("Keyed<")
    if keyed:
        keys = expected.get("output_key_order", sorted(expected.get("entry_constructor_values", {})))
        require(keys or "entry_constructor_values" in expected or "output_key_order" in expected,
                "Keyed core result lacks authored key expectations")
        check_keyed_membership(value, keys)
    records = value.get("derived_rekeys", [])
    if "exact_scalar_rekey_records" in expected:
        check_rekeys(records, units, expected=expected["exact_scalar_rekey_records"], exact=True,
                     require_nonempty=bool(expected["exact_scalar_rekey_records"]))
    elif "exact_aggregate_rekey_records" in expected:
        wanted = expected["exact_aggregate_rekey_records"]
        check_rekeys(records, units, expected=wanted, exact=True, aggregate=keyed, require_nonempty=bool(wanted))
    elif "root_aggregate_rekey_record" in expected:
        check_rekeys(records, units, expected=[expected["root_aggregate_rekey_record"]], exact=True, aggregate=keyed)
    else:
        aggregates = [record for record in records if record["old_key"] is None]
        require(aggregates == case["source_rekey_records"], "Required actually evaluated aggregate origins differ")
    if keyed:
        public = expected.get("exact_public_selected_rekey_records")
        root_selected = expected.get("root_selected_rekey_records")
        for entry in value["value"]:
            key, leaf = entry["key"], entry["value"]
            if public is not None:
                wanted = public.get(key, [])
                check_rekeys(leaf.get("derived_rekeys", []), units, expected=wanted, exact=True, require_nonempty=bool(wanted))
            elif root_selected is not None:
                wanted = [expected["root_aggregate_rekey_record"], root_selected[key]]
                check_rekeys(leaf.get("derived_rekeys", []), units, expected=wanted, exact=True)
            if key == expected.get("plain_output_key_has_no_rekey_selected_contributor"):
                require(all(record["old_key"] is None for record in leaf.get("derived_rekeys", [])),
                        "Plain independent leaf acquired a coincident selected rekey origin")
    paths = {item["path"] for item in value.get("dependencies", []) if "path" in item}
    require(set(expected.get("required_actual_member_reads", [])) <= paths, "Rekey lost an actual source read")
    for dependency in value.get("dependencies", []):
        require(dependency["program_revision"] == case["program_revision"], "Result dependency uses stale source")
    if case["name"] == "input-alias-remains-unmodified":
        for member in ("items", "untouched"):
            original = inspect_member(items, "shape", member)
            require(original["type"] == "Keyed<Int>" and
                    [(entry["key"], entry["value"]["value"]) for entry in original["value"]] == [("a", 11), ("b", 22)],
                    "Shared input alias payload/key was mutated")
            require(not any(isinstance(node, dict) and "derived_rekeys" in node for _, node in walk(original)),
                    "Shared input alias acquired output rekey origins")
    return {"status": "passed", "typed_result": value["type"], "source_locations": locations,
            "output_entries": len(value["value"]) if keyed else None, "origin_records": counts,
            "control_program_revision": case["explicit_c085_control"]["program_revision"]}
