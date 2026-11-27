"""W4 audit 001, exploration x05: which frozen commands carry audit_expect, and the .X argv form."""
import json
import sys

freeze = json.load(open(sys.argv[1]))
total = 0
for command in freeze["commands"]:
    rules = command.get("audit_expect") or []
    if rules:
        total += len(rules)
        print("audit_expect", command["id"], len(rules))
print("commands with audit_expect:", sum(1 for c in freeze["commands"] if c.get("audit_expect")), "rules:", total)
for command in freeze["commands"]:
    if command["id"] in ("C16.X", "P01", "D02", "Q04", "Q01", "Q02", "Q03", "P05", "P00", "C16.L", "C16.P"):
        print(command["id"], json.dumps(command["argv"]))
        print("   cwd", command["cwd"], "env", command["environment"])
