"""W3 freeze review 001, script 07: my own count of TR2-03's route classes and other routes the name scan cannot see.

For the probe, the loader and the 23 other reader files it lists, with line and context, every occurrence of:
.constructor (member access), Reflect.construct/apply/get/set, computed members of global objects (window[, self[,
globalThis[, global[), process[ and every process. member, getBuiltinModule, new Function / Function( calls,
setTimeout/setInterval with a string, import.meta, WebAssembly, Worker, and every specifier and process call name of
the scan. Reads only; writes one record into OUT/records.
"""
import json
import os
import re
import sys
from collections import Counter

OUT = sys.argv[1]
with open(os.path.join(OUT, "records", "mc11-scan-noreview-001.json"), "rb") as f:
    scan = json.loads(f.read())

PATTERNS = [
    ("constructor-member", re.compile(r"\.\s*constructor\b")),
    ("constructor-bracket", re.compile(r"\[\s*['\"`]constructor['\"`]\s*\]")),
    ("Reflect", re.compile(r"\bReflect\s*\.\s*(construct|apply|get|set|defineProperty|getPrototypeOf)\b")),
    ("global-computed", re.compile(r"\b(window|self|globalThis|global)\s*\[")),
    ("process-computed", re.compile(r"\bprocess\s*\[")),
    ("process-member", re.compile(r"\bprocess\s*\.\s*([A-Za-z_$][\w$]*)")),
    ("getBuiltinModule", re.compile(r"getBuiltinModule")),
    ("new-Function", re.compile(r"\bnew\s+Function\b")),
    ("Function-call", re.compile(r"(?<![\w$.])Function\s*\(")),
    ("timer-string", re.compile(r"\b(setTimeout|setInterval|setImmediate)\s*\(\s*['\"`]")),
    ("import.meta", re.compile(r"\bimport\s*\.\s*meta\b")),
    ("WebAssembly", re.compile(r"\bWebAssembly\b")),
    ("Worker-any-case", re.compile(r"worker", re.IGNORECASE)),
    ("bind-call-apply-of-Function", re.compile(r"\bFunction\s*\.\s*prototype\s*\.\s*(call|apply|bind)\b")),
]

rows = []
counts = Counter()
for key, entry in scan["files"].items():
    with open(entry["path"], "rb") as f:
        text = f.read().decode("utf-8", "surrogateescape")
    lines = text.split("\n")
    for name, pattern in PATTERNS:
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            col = m.start() - (text.rfind("\n", 0, m.start()) + 1) + 1
            s = lines[line - 1]
            lo, hi = max(0, col - 1 - 60), min(len(s), col - 1 + 90)
            tag = name if name != "process-member" else "process." + m.group(1)
            counts[(key, tag)] += 1
            rows.append({"file": key, "pattern": tag, "line": line, "column": col, "context": s[lo:hi]})

with open(os.path.join(OUT, "records", "07-mc11-routes.json"), "x", encoding="utf-8") as f:
    json.dump({"counts": {"%s | %s" % k: v for k, v in sorted(counts.items())}, "rows": rows}, f, indent=1, ensure_ascii=False)
    f.write("\n")
for (key, tag), v in sorted(counts.items()):
    print("%-70s %-28s %d" % (key, tag, v))
print()
# Show every occurrence except the bulk constructor-member ones, which are shown by their shape
shapes = Counter()
for r in rows:
    if r["pattern"] == "constructor-member":
        ctx = r["context"]
        i = ctx.find(".constructor") if ".constructor" in ctx else ctx.find("constructor")
        before = ctx[max(0, i - 16):i]
        after = ctx[i:i + 26]
        shape = ("new" if re.search(r"new\s+[\w$.\s]*$", before) else "no-new") + " | " + re.sub(r"\s+", " ", after)
        shapes[(r["file"], shape)] += 1
    elif not r["pattern"].startswith("Worker"):
        print("%s L%d:%d [%s] %s" % (r["file"], r["line"], r["column"], r["pattern"], r["context"].replace("\t", " ")))
print()
for (f_, shape), v in sorted(shapes.items()):
    print("CONSTRUCTOR", f_, "|", shape, "|", v)
print()
for r in rows:
    if r["pattern"] == "Worker-any-case":
        print("WORKER %s L%d:%d %s" % (r["file"], r["line"], r["column"], r["context"][:150]))
print()
for key, entry in scan["files"].items():
    for r in entry["specifiers"]:
        print("SPEC %s L%s:%s %s %r -> %s [%s]" % (key, r["line"], r["column"], r["pattern"], r["specifier"], r.get("resolution"), r.get("context")))
    for r in entry["process_call_names"]:
        print("CALL %s L%s:%s %s method=%s paren=%s receiver=%r" % (key, r["line"], r["column"], r["pattern"], r.get("method_call"), r.get("parenthesized"), (r.get("receiver") or "")[-45:]))
print("unresolved", scan["unresolved_relative_specifiers"])
