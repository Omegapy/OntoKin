"""W2 freeze author: the MC11 candidate list (schema /2, status CANDIDATE, NOT REVIEWED) from one scan record.

Run with <worktree>/.venv/bin/python -I -S -B. Standard library only; reads the scan record and the bound
files it names, starts nothing, and writes one absent output file.

Usage: w2f_mc11_candidate.py SCAN_JSON OUTPUT_JSON
The scanner refuses this list until an independent reviewer reviews every entry and writes a list
with status REVIEWED and its identity (TR-12). Every observation below is advisory.
"""
import collections
import hashlib
import json
import os
import re
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(PermissionError(event)) if event in PROCESS_EVENTS else None)

CONSTRUCTOR_CALL = re.compile(r"\.constructor\s*\(")
NEW_BEFORE = re.compile(r"new\s+[\w$.\[\]'\"]*$")
REFLECT = re.compile(r"(?<![\w$])Reflect\s*\.\s*(\w+)")
GLOBAL_MEMBER = re.compile(r"(?<![\w$.])(globalThis|self|window|global)\s*\[")


def route_classes(text):
    """TR2-03's two route classes, as a plain count for the reviewer (advisory; context not decided)."""
    constructor_calls, constructor_without_new = 0, []
    for match in CONSTRUCTOR_CALL.finditer(text):
        constructor_calls += 1
        line_start = text.rfind("\n", 0, match.start()) + 1
        before = text[line_start:match.start()]
        if not NEW_BEFORE.search(before):
            constructor_without_new.append(text.count("\n", 0, match.start()) + 1)
    reflect = collections.Counter(match.group(1) for match in REFLECT.finditer(text))
    globals_ = collections.Counter(match.group(1) for match in GLOBAL_MEMBER.finditer(text))
    global_lines = sorted({text.count("\n", 0, match.start()) + 1 for match in GLOBAL_MEMBER.finditer(text)})
    return {"constructor_calls": constructor_calls, "constructor_calls_without_new_on_their_line": constructor_without_new,
            "reflect_members": dict(sorted(reflect.items())), "computed_global_members": dict(sorted(globals_.items())),
            "computed_global_member_lines": global_lines[:50]}


def main():
    scan_path, output = sys.argv[1], sys.argv[2]
    if os.path.lexists(output):
        raise SystemExit("output exists")
    with open(scan_path, "rb") as stream:
        raw = stream.read()
    scan = json.loads(raw)
    files = {}
    totals = collections.Counter()
    for key, entry in scan["files"].items():
        with open(entry["path"], "rb") as stream:
            data = stream.read()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise SystemExit("file changed since the scan: " + key)
        text = data.decode("utf-8", "surrogateescape")
        frozen = entry["frozen_rule"]["found"]
        one_line = collections.Counter(frozen["static_specifiers"])
        wider = collections.Counter(row["specifier"] for row in entry["specifiers"])
        only_wider = sorted((wider - one_line).elements())
        only_frozen = sorted((one_line - wider).elements())
        notes = {
            "role": entry["role"], "kind": entry["kind"], "sha256": entry["sha256"], "size_bytes": entry["size_bytes"],
            "lines": entry["lines"],
            "counts": {"process_creation": len(entry["process_creation"]),
                       "process_call_names": len(entry["process_call_names"]), "dynamic": len(entry["dynamic"]),
                       "specifiers": len(entry["specifiers"]), "frozen_rule_dynamic": len(frozen["dynamic"]),
                       "frozen_rule_static_specifiers": len(frozen["static_specifiers"])},
            "advisory_dynamic_classes": sorted(
                [list(item) + [count] for item, count in collections.Counter(
                    (row["pattern"], row.get("classification"), row.get("context"), row.get("view") or "raw")
                    for row in entry["dynamic"]).items()], key=str),
            "process_call_names_observed": [
                {"pattern": row["pattern"], "line": row["line"], "column": row["column"],
                 "method_call": row.get("method_call"), "receiver_tail": (row.get("receiver") or "")[-60:],
                 "context": row.get("context")} for row in entry["process_call_names"]],
            "specifiers_observed": [
                {"pattern": row["pattern"], "line": row["line"], "column": row["column"], "specifier": row["specifier"],
                 "resolution": row["resolution"], "context": row.get("context"), "view": row.get("view") or "raw"}
                for row in entry["specifiers"]],
            "multi_line_or_non_statement_specifiers": {
                "wider_scan_only": only_wider, "frozen_rule_only": only_frozen,
                "meaning": "mc11_rule lists a static specifier only when its import or export keyword and its string "
                           "share one line; the wider scan also lists a 'from' string on a later line of a statement, "
                           "a literal in a comment or string, and a require-parenthesized literal. The reviewer reads "
                           "each such statement and records its specifier here (mc11_rule implementation note)."},
            "tr2_03_route_classes": route_classes(text),
            "review": "CANDIDATE, NOT REVIEWED: every entry above awaits the independent reviewer"}
        files[key] = {
            "process_call_names": [[row["pattern"], row["line"], row["column"]] for row in entry["process_call_names"]],
            "dynamic": [[row["pattern"], row["line"], row["column"]] for row in entry["dynamic"]],
            "specifiers": [row["specifier"] for row in entry["specifiers"]],
            "frozen_rule": {"dynamic": [list(item) for item in frozen["dynamic"]],
                            "static_specifiers": list(frozen["static_specifiers"])},
            "notes": notes}
        totals.update({"process_call_names": len(entry["process_call_names"]), "dynamic": len(entry["dynamic"]),
                       "specifiers": len(entry["specifiers"]), "frozen_rule_dynamic": len(frozen["dynamic"]),
                       "frozen_rule_static_specifiers": len(frozen["static_specifiers"])})
    document = {
        "schema": "ontokin.c271.p35-mc11-reviewed/2",
        "status": "CANDIDATE, NOT REVIEWED",
        "reviewer": None,
        "candidate": {
            "prepared_by": "W2, the independent author of operational freeze 001 (gate MH, C271-P35)",
            "derived_from": {"scan_record": os.path.basename(scan_path),
                             "scan_record_sha256": hashlib.sha256(raw).hexdigest(),
                             "scanner": scan["tool"], "inputs": scan["inputs"]},
            "totals": dict(sorted(totals.items())),
            "frozen_rule_totals": {"dynamic_hits": scan["frozen_rule"]["dynamic_hits"],
                                   "process_creation_none": scan["frozen_rule"]["process_creation_none"]},
            "wider_scan_totals": scan["totals"],
            "unresolved_relative_specifiers": scan["unresolved_relative_specifiers"]},
        "notes": {
            "how_to_review": "Review every entry of every file: each process call name, each dynamic hit and each "
                             "specifier, and the frozen rule's own entries. A REVIEWED list must equal the scan "
                             "exactly (compare_reviewed: [pattern, line, column] lists and the specifier multiset; "
                             "frozen_rule: [kind, stripped line] multiset and the one-line specifiers). Set status "
                             "to REVIEWED and name the reviewer only if no entry shows process creation or an "
                             "unreviewable route; otherwise MC11 is a finding and the list stays unreviewed.",
            "tr2_03": "Neither verdict flags two dynamic route classes (TOOLING-REVIEW-002 TR2-03): the Function "
                      "constructor reached through a function's .constructor or through Reflect.construct, and "
                      "computed members of the global objects (globalThis[x], self[x], window[x]). Review 002's "
                      "cross-check of these files, under the scan's stated limit: every .constructor( call is a "
                      "new expression; Reflect occurs only as Reflect.get in three.webgpu.js; the validator's "
                      "computed globals are dart2js window[tag] lookups that are null under Node. Each file's "
                      "notes.tr2_03_route_classes gives this candidate's own advisory count for the reviewer to "
                      "confirm.",
            "tr_11_url": "The validator preamble's parenthesized require of the literal \"url\" is listed as a "
                         "require-parenthesized specifier \"url\" of validator/package/gltf_validator.dart.js "
                         "(TR-11's concrete miss, now found); \"url\" is Node's builtin module of that name.",
            "limit": scan["limit"]},
        "files": files}
    data = (json.dumps(document, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({"files": len(files), "totals": dict(sorted(totals.items())),
                      "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}, sort_keys=True))
    for key, entry in sorted(files.items()):
        rc = entry["notes"]["tr2_03_route_classes"]
        if rc["constructor_calls"] or rc["reflect_members"] or rc["computed_global_members"]:
            print(key, json.dumps(rc, sort_keys=True)[:600])


main()
