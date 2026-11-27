"""W4 audit 001, exploration step x02: per-command field sizes of FREEZE-002.json, and dumps.

Reads only. Writes one pretty-printed file per command into argv[2] (the session scratchpad).
"""
import json
import os
import sys

freeze_path = sys.argv[1]
dump_dir = sys.argv[2]
with open(freeze_path, "rb") as handle:
    doc = json.loads(handle.read())
os.makedirs(dump_dir, exist_ok=True)
for command in doc["commands"]:
    cid = command["id"]
    sizes = {key: len(json.dumps(value)) for key, value in command.items()}
    big = {key: size for key, size in sizes.items() if size > 2000}
    print(cid, command.get("phase"), command.get("name"), "big:", big)
    with open(os.path.join(dump_dir, f"{cid}.json"), "w", encoding="utf-8") as out:
        out.write(json.dumps(command, indent=1, ensure_ascii=False))
        out.write("\n")
    # A slim copy without the large expect members, for reading.
    slim = {}
    for key, value in command.items():
        if key in ("expect", "audit_expect") and isinstance(value, (list, dict)):
            slim[key] = {"_size": sizes[key], "_len": len(value)}
        else:
            slim[key] = value
    with open(os.path.join(dump_dir, f"{cid}.slim.json"), "w", encoding="utf-8") as out:
        out.write(json.dumps(slim, indent=1, ensure_ascii=False))
        out.write("\n")
