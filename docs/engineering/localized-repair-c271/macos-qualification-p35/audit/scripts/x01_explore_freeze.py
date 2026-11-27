"""W4 audit 001, exploration step x01: summarize FREEZE-002.json and dump its sections.

Reads only. Writes pretty-printed copies of each top-level section into the directory given as
argv[2] (the session scratchpad, outside <local>), and prints a summary on stdout.
"""
import hashlib
import json
import os
import sys

freeze_path = sys.argv[1]
dump_dir = sys.argv[2]
with open(freeze_path, "rb") as handle:
    raw = handle.read()
print("freeze bytes", len(raw), "sha256", hashlib.sha256(raw).hexdigest())
doc = json.loads(raw)
print("top-level keys:", list(doc))
os.makedirs(dump_dir, exist_ok=True)
for key, value in doc.items():
    kind = type(value).__name__
    size = len(value) if hasattr(value, "__len__") else ""
    text = json.dumps(value, indent=1, sort_keys=False, ensure_ascii=False)
    print(f"  {key}: {kind} len={size} dump_bytes={len(text)}")
    with open(os.path.join(dump_dir, f"freeze002.{key}.json"), "w", encoding="utf-8") as out:
        out.write(text)
        out.write("\n")
    if isinstance(value, dict):
        for sub, subvalue in value.items():
            subkind = type(subvalue).__name__
            subsize = len(subvalue) if hasattr(subvalue, "__len__") else repr(subvalue)[:80]
            print(f"      {sub}: {subkind} {subsize}")
    elif isinstance(value, list) and value and isinstance(value[0], dict):
        print("      first item keys:", list(value[0]))
