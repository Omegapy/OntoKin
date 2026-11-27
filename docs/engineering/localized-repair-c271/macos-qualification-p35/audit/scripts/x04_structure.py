"""W4 audit 001, exploration x04: print the structure of JSON documents (keys, types, lengths).

Usage: x04_structure.py MAXDEPTH FILE [FILE ...]
Lists are summarized by their length and the structure of their first element.
"""
import json
import sys


def show(value, depth, maxdepth, indent):
    pad = "  " * indent
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                size = len(item)
                print(f"{pad}{key}: {type(item).__name__}[{size}]")
                if depth < maxdepth:
                    show(item, depth + 1, maxdepth, indent + 1)
            else:
                text = json.dumps(item)
                print(f"{pad}{key}: {text[:100]}")
    elif isinstance(value, list):
        if value:
            first = value[0]
            if isinstance(first, (dict, list)):
                print(f"{pad}[0]: {type(first).__name__}[{len(first)}]")
                if depth < maxdepth:
                    show(first, depth + 1, maxdepth, indent + 1)
            else:
                print(f"{pad}[0..]: {json.dumps(value[:6])[:120]}")


maxdepth = int(sys.argv[1])
for path in sys.argv[2:]:
    print("=====", path)
    with open(path, "rb") as handle:
        show(json.loads(handle.read()), 0, maxdepth, 0)
