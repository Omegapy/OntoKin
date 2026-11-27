"""W3 freeze review 001, script 08: write MC11-REVIEWED-LIST-001.json from my own scan and my review decisions.

The lists are taken from my own scan without a reviewed list (scan_mc11.py at C, OUT/records/mc11-scan-noreview-001.json),
which equals the candidate list exactly (script 06). Every hit was reviewed by me, W3, against the source: the
decisions below are per file and per group of hits (pattern, enclosing token, lexical context), with my counts of
TR2-03's route classes (script 07). The list is written by exclusive creation; no machine path is written into it.
"""
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

OUT = sys.argv[1]
CAND_SHA = sys.argv[2]
REVIEWER = ("W3, freeze review 001 of gate MH (C271-P35): a Claude Code subagent in a fresh context with the session's "
            "model, independent of the freeze's author (W2); it wrote none of the tooling, the probe, the readers or the "
            "candidate list")
with open(os.path.join(OUT, "records", "mc11-scan-noreview-001.json"), "rb") as f:
    raw_scan = f.read()
scan = json.loads(raw_scan)
with open(os.path.join(OUT, "records", "06-mc11-hits.json"), "rb") as f:
    hits = json.loads(f.read())["hits"]
with open(os.path.join(OUT, "records", "07-mc11-routes.json"), "rb") as f:
    routes = json.loads(f.read())

DECIDE_DYNAMIC = {
    ("Function", "identifier-substring"): "the substring Function inside a longer identifier (named in 'tokens'): a property, method, class or variable name; no reference to the Function constructor",
    ("Function", "word", "comment"): "the word Function in a comment (JSDoc types such as {Function} or prose): not code",
    ("Function", "word", "string"): "the word Function inside a string literal (an error message): not code",
    ("eval", "identifier-substring"): "the substring eval inside a longer word (evaluate, evaluated, evalIridescence, evalSensitivity, consteval ...): no call of eval",
    ("require-reference", "comment"): "the English word require in a comment: not code",
    ("require-reference", "string"): "the word require inside a string literal (GLSL '#extension ... : require', an error message, or a package.json exports key): not a call",
}


def file_notes(key, entry):
    mine = [h for h in hits if h["file"] == key]
    groups = defaultdict(list)
    for h in mine:
        if h["list"] in ("process_call_names", "dynamic"):
            groups[(h["list"], h["pattern"], h.get("classification"), h.get("context"), h.get("token"))].append([h["line"], h["column"]])
    decisions = []
    for (lst, pattern, cls, ctx, tok), where in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1], str(x[0][2]), str(x[0][3]), str(x[0][4]))):
        if lst == "process_call_names":
            text = ("RegExp.prototype.exec on a regular expression (a literal /.../, or a variable or field that holds a "
                    "RegExp, checked at its definition): string matching, no process")
        elif (pattern, cls) in DECIDE_DYNAMIC:
            text = DECIDE_DYNAMIC[(pattern, cls)]
        elif (pattern, cls, ctx) in DECIDE_DYNAMIC:
            text = DECIDE_DYNAMIC[(pattern, cls, ctx)]
        elif pattern == "require-reference" and ctx in ("comment", "string") and key != "validator/package/gltf_validator.dart.js":
            text = DECIDE_DYNAMIC[("require-reference", ctx)] + (
                "; package.json's exports map names ./build/three.cjs, which is not among the reader files and is never "
                "loaded: the probe imports the bound entries by path and the loader maps 'three' to build/three.webgpu.js"
                if key == "indexer-view/three/package.json" else "")
        elif pattern == "createRequire":
            text = "node:module's createRequire, imported at line 7 and used once at line 728 relative to the probe's own URL; it creates no process"
        elif pattern == "require-computed":
            text = ("require(manifest.validator_entry): the bound validator entry <dependencies root>/validator/package/index.js, "
                    "which verifyBootstrap checks against the digest-checked manifest's roles and files before this line; "
                    "that file is one of the scanned reader files")
        elif pattern == "import-computed":
            text = ("import(pathToFileURL(manifest.three_entry or manifest.gltf_loader_entry).href): the bound Three.js entry "
                    "build/three.webgpu.js and examples/jsm/loaders/GLTFLoader.js, both role-checked and digest-bound by "
                    "verifyBootstrap before the import; both are scanned reader files")
        elif pattern == "Function" and cls == "word" and ctx == "code" and key == "validator/package/gltf_validator.dart.js":
            text = ("dart2js runtime: Function.prototype.$0/$1/$2/... = function(...){return this(...)} (assignments of call "
                    "adapters to Function.prototype at lines 10979 to 10987): no use of the Function constructor, no code built from strings")
        elif pattern == "Function" and cls == "word" and ctx == "code" and key == "validator/package/README.md":
            text = "Markdown prose and a link target in README.md (lexical context advisory): the file is documentation, never loaded"
        elif pattern == "Function" and cls == "identifier-substring":
            text = DECIDE_DYNAMIC[("Function", "identifier-substring")]
        elif pattern == "non-webpack-require":
            text = ("validator preamble, line 1: (typeof __webpack_require__ != 'undefined' ? __non_webpack_require__ : require)('url') "
                    "loads Node's builtin url module (for pathToFileURL); no other module")
        elif pattern == "require-reference" and key == "validator/package/gltf_validator.dart.js":
            text = ("validator preamble, line 1: 'typeof require', 'self.require=require' (the CommonJS require exposed on the "
                    "preamble's self object) and the parenthesized callee of require('url'); no other '.require(' or "
                    "'require(' call exists in the file, and the only specifier is 'url'")
        else:
            text = "REVIEW NEEDED"
        decisions.append({"list": lst, "pattern": pattern, "classification": cls, "context": ctx, "token": tok,
                          "count": len(where), "where": where, "decision": text})
    specs = []
    for h in mine:
        if h["list"] == "specifiers":
            ctx, spec, res = h.get("context"), h["specifier"], h.get("resolution")
            if res == "node-builtin":
                text = "a node: builtin"
            elif res and res.startswith("reader-file:"):
                text = "a relative import resolved to a scanned reader file"
            elif ctx in ("comment",):
                text = "inside a comment (a usage example or URL): not an import"
            elif ctx in ("string", "template") and key not in ("validator/package/README.md",):
                text = "matched inside a string or template literal (a keyword list, a JSON value or a colour-space name): not an import"
            elif key == "validator/package/README.md":
                text = "a require() inside a Markdown code sample of README.md: documentation, never loaded"
            elif spec in ("three", "three/webgpu", "three/tsl"):
                text = ("a bare 'three' specifier: tools/three_loader.mjs resolves three and three/webgpu to build/three.webgpu.js "
                        "and three/tsl to build/three.tsl.js inside the reader tree")
            elif spec == "url":
                text = "Node's builtin url module, required by the validator preamble"
            else:
                text = "REVIEW NEEDED"
            specs.append({"line": h["line"], "column": h["column"], "pattern": h["pattern"], "specifier": spec,
                          "resolution": res, "context": ctx, "decision": text})
    frozen_static = entry["frozen_rule"]["found"]["static_specifiers"]
    wider = Counter(s["specifier"] for s in specs)
    only_wider = sorted((Counter(wider) - Counter(frozen_static)).elements())
    only_frozen = sorted((Counter(frozen_static) - Counter(wider)).elements())
    route_counts = {k.split(" | ", 1)[1]: v for k, v in routes["counts"].items() if k.split(" | ", 1)[0] == key}
    return {"reviewed_by": "W3, freeze review 001", "role": entry["role"], "sha256": entry["sha256"],
            "size_bytes": entry["size_bytes"], "process_creation_hits": len(entry["process_creation"]),
            "frozen_rule_process_creation_hits": len(entry["frozen_rule"]["found"]["process_creation"]),
            "decisions": decisions, "specifiers_reviewed": specs,
            "multi_line_or_non_statement_specifiers": {
                "wider_scan_only": only_wider, "frozen_rule_only": only_frozen,
                "meaning": ("mc11_rule lists a static specifier only when its import or export keyword and its string share "
                            "one line; each wider-scan-only specifier above was read in its statement or comment by the "
                            "reviewer (specifiers_reviewed)")},
            "tr2_03_route_classes": {
                "counts": route_counts,
                "review": ("Function constructor through .constructor: every '.constructor(' call in the reader files is a "
                           "'new <expr>.constructor(...)' expression on a typed array or a class instance (61 in all, the three "
                           "that span lines included), no call of a function object's constructor; Reflect: 6 Reflect.get and 2 "
                           "Reflect.set in Proxy handlers of three.webgpu.js, no Reflect.construct or Reflect.apply; computed "
                           "members of global objects: only gltf_validator.dart.js's five window[tag]/window[p] lookups in "
                           "dart2js's DOM prototype detection, which return null when window is undefined, as in Node; no "
                           "process[...], no getBuiltinModule, no new Function, no Function(...) call, no timer with a "
                           "string, no WebAssembly")},
            "conclusion": ("no process creation and no route to it found in this file, within the stated limit of a name scan"
                           if all(d["decision"] != "REVIEW NEEDED" for d in decisions + specs) else "REVIEW NEEDED")}


files = {}
for key, entry in scan["files"].items():
    files[key] = {
        "process_call_names": [[r["pattern"], r["line"], r["column"]] for r in entry["process_call_names"]],
        "dynamic": [[r["pattern"], r["line"], r["column"]] for r in entry["dynamic"]],
        "specifiers": [r["specifier"] for r in entry["specifiers"]],
        "frozen_rule": {"dynamic": [list(x) for x in entry["frozen_rule"]["found"]["dynamic"]],
                        "static_specifiers": list(entry["frozen_rule"]["found"]["static_specifiers"])},
        "notes": file_notes(key, entry)}
pending = sorted(k for k, v in files.items() if v["notes"]["conclusion"] == "REVIEW NEEDED")
document = {
    "schema": "ontokin.c271.p35-mc11-reviewed/2",
    "status": "REVIEWED" if not pending else "NOT REVIEWED: entries pending",
    "reviewer": REVIEWER,
    "review": {
        "gate": "MH", "phase": "C271-P35", "stage": "S6, freeze review 001", "reviewed_at_utc_date": "2026-11-27",
        "rule": "CONTROLS-FROZEN.json mc11_rule, with TR2-03's route classes (TOOLING-REVIEW-002, disposition 002)",
        "basis": {"candidate_list_sha256": CAND_SHA,
                  "own_scan": {"tool": "scan_mc11.py at commit C", "tool_sha256": scan["tool"]["sha256"],
                               "record_sha256": hashlib.sha256(raw_scan).hexdigest(), "reviewed_list": None},
                  "probe_sha256": scan["inputs"]["probe"]["sha256"],
                  "dependencies_inventory_sha256": scan["inputs"]["dependencies_inventory"]["sha256"]},
        "equality": "the lists of every entry equal the scan exactly (pattern, line, column; specifier multiset; frozen rule's [kind, stripped line] multiset and one-line specifiers), and equal the candidate list exactly",
        "totals": scan["totals"],
        "frozen_rule_dynamic_hits": sum(len(e["frozen_rule"]["found"]["dynamic"]) for e in scan["files"].values()),
        "conclusion": ("no process-creation name in any view of any file; every process call name is RegExp.prototype.exec; "
                       "every dynamic hit is an identifier substring, a comment, a string, the probe's three bound loads, or "
                       "the validator preamble's require('url'); no route to process creation was found"
                       if not pending else "pending entries: " + ", ".join(pending)),
        "limit": scan["limit"]},
    "files": files}
data = (json.dumps(document, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
if len(sys.argv) > 3 and sys.argv[3] == "--dry-run":
    for k, v in files.items():
        for d in v["notes"]["decisions"] + v["notes"]["specifiers_reviewed"]:
            if d["decision"] == "REVIEW NEEDED":
                print("PENDING", k, json.dumps(d)[:400])
    print("dry run: pending", pending, "bytes", len(data), "sha256", hashlib.sha256(data).hexdigest())
    raise SystemExit(0)
path = os.path.join(OUT, "MC11-REVIEWED-LIST-001.json")
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
try:
    os.write(fd, data)
    os.fsync(fd)
finally:
    os.close(fd)
st = os.stat(path)
print(json.dumps({"path": "<local>/c271-p35/workers/W3-freeze-001/MC11-REVIEWED-LIST-001.json", "sha256": hashlib.sha256(data).hexdigest(),
                  "size_bytes": st.st_size, "mode": "0o%03o" % (st.st_mode & 0o777), "status": document["status"], "pending": pending}))
