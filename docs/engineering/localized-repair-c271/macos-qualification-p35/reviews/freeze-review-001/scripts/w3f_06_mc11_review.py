"""W3 freeze review 001, script 06: compare the MC11 candidate list with my own scan, and group every hit for review.

Inputs: the scan without a reviewed list (OUT/records/mc11-scan-noreview-001.json, written by scan_mc11.py at C)
and the candidate list. For each file it checks that the candidate's lists equal the scan exactly, and it groups
every process call name and dynamic hit by the enclosing token, with the source line, for the reviewer's decision.
Reads only; writes two records into OUT/records.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

OUT = sys.argv[1]
CAND = sys.argv[2]
with open(os.path.join(OUT, "records", "mc11-scan-noreview-001.json"), "rb") as f:
    scan = json.loads(f.read())
with open(CAND, "rb") as f:
    cand = json.loads(f.read())

cmp = {}
for key, entry in scan["files"].items():
    c = cand["files"].get(key)
    row = {}
    for k in ("process_call_names", "dynamic"):
        actual = sorted([r["pattern"], r["line"], r["column"]] for r in entry[k])
        expected = sorted(list(x) for x in (c or {}).get(k, []))
        row[k] = actual == expected
    row["specifiers"] = sorted(r["specifier"] for r in entry["specifiers"]) == sorted((c or {}).get("specifiers", []))
    fr = entry["frozen_rule"]["found"]
    row["frozen_dynamic"] = Counter(tuple(x) for x in fr["dynamic"]) == Counter(tuple(x) for x in (c or {}).get("frozen_rule", {}).get("dynamic", []))
    row["frozen_static"] = sorted(fr["static_specifiers"]) == sorted((c or {}).get("frozen_rule", {}).get("static_specifiers", []))
    row["frozen_process_creation"] = fr["process_creation"]
    row["process_creation"] = entry["process_creation"]
    cmp[key] = row
missing_keys = sorted(set(cand["files"]) - set(scan["files"]))

IDENT = re.compile(r"[\w$]")


def token_at(text, line, column, length):
    lines = text.split("\n")
    s = lines[line - 1]
    if column is None:
        return None, s[:200]
    i = column - 1
    j = i + length
    while i > 0 and IDENT.match(s[i - 1]):
        i -= 1
    while j < len(s) and IDENT.match(s[j]):
        j += 1
    lo, hi = max(0, i - 50), min(len(s), j + 70)
    return s[i:j], s[lo:hi]


groups = defaultdict(list)
detail = []
for key, entry in scan["files"].items():
    path = entry["path"]
    with open(path, "rb") as f:
        text = f.read().decode("utf-8", "surrogateescape")
    for k in ("process_call_names", "dynamic"):
        for r in entry[k]:
            tok, ctx = token_at(text, r["line"], r["column"], len(r.get("text") or r["pattern"]))
            cls = r.get("classification")
            g = (key, k, r["pattern"], cls, r.get("context"), r.get("view", "raw"), tok)
            groups[g].append((r["line"], r["column"], ctx, r.get("receiver", "")[-40:] if r.get("receiver") else None, r.get("text")))
            detail.append({"file": key, "list": k, "pattern": r["pattern"], "line": r["line"], "column": r["column"],
                           "classification": cls, "context": r.get("context"), "view": r.get("view", "raw"),
                           "token": tok, "line_context": ctx, "text": r.get("text")})
    for r in entry["specifiers"]:
        detail.append({"file": key, "list": "specifiers", "pattern": r["pattern"], "line": r["line"], "column": r["column"],
                       "specifier": r["specifier"], "resolution": r.get("resolution"), "context": r.get("context"),
                       "view": r.get("view", "raw"), "snippet": (r.get("snippet") or "")[:200]})

with open(os.path.join(OUT, "records", "06-mc11-hits.json"), "x", encoding="utf-8") as f:
    json.dump({"comparison": cmp, "candidate_keys_not_scanned": missing_keys, "hits": detail}, f, indent=1, ensure_ascii=False)
    f.write("\n")
lines = []
lines.append("COMPARISON (candidate list vs my scan): " + json.dumps({k: {kk: vv for kk, vv in v.items() if vv is not True} for k, v in cmp.items()}))
lines.append("candidate keys not scanned: %r" % missing_keys)
for g in sorted(groups, key=lambda x: (x[0], x[1], x[2], str(x[3]), str(x[4]), str(x[6]))):
    rows = groups[g]
    lines.append("%s | %s | %s | cls=%s ctx=%s view=%s | token=%r | n=%d" % (g[0], g[1], g[2], g[3], g[4], g[5], g[6], len(rows)))
    for ln, col, ctx, rec, txt in rows[:4]:
        lines.append("      L%s:%s  %s" % (ln, col, ctx.replace("\t", " ")))
with open(os.path.join(OUT, "records", "06-mc11-groups.txt"), "x", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(lines[0][:3000])
print(lines[1])
print("groups", len(groups))
