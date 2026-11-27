"""W4 audit 001, exploration x06: print chosen members of chosen frozen commands.

Usage: x06_print_members.py FREEZE MEMBER ID [ID ...]
"""
import json
import sys

freeze = json.load(open(sys.argv[1]))
member = sys.argv[2]
wanted = sys.argv[3:]
commands = {c["id"]: c for c in freeze["commands"]}
for cid in wanted:
    print("=====", cid, member)
    print(json.dumps(commands[cid].get(member), indent=1))
