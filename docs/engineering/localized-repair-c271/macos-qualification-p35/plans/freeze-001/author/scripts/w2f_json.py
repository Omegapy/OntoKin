"""W2 freeze author: read-only JSON inspection (stdlib only; run with -I -S -B).

Usage: w2f_json.py FILE (shape DEPTH | get POINTER [POINTER ...] | keys POINTER | find TEXT)
Prints to stdout only. Reads FILE; writes nothing.
"""
import json
import sys


def shape(value, depth, indent=0):
    pad = "  " * indent
    if isinstance(value, dict):
        for key in value:
            item = value[key]
            kind = type(item).__name__
            extra = ""
            if isinstance(item, (list, dict)):
                extra = " (%d)" % len(item)
            elif isinstance(item, str):
                extra = " = " + (item if len(item) <= 80 else item[:80] + "...")
            else:
                extra = " = " + json.dumps(item)
            print(pad + str(key) + ": " + kind + extra)
            if depth > 1 and isinstance(item, (dict, list)):
                shape(item, depth - 1, indent + 1)
    elif isinstance(value, list):
        for index, item in enumerate(value[:3]):
            kind = type(item).__name__
            print(pad + "[%d]: %s" % (index, kind))
            if depth > 1 and isinstance(item, (dict, list)):
                shape(item, depth - 1, indent + 1)
        if len(value) > 3:
            print(pad + "... %d items" % len(value))


def get(value, pointer):
    if pointer in ("", "/"):
        return value
    for part in pointer.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(part)]
        else:
            value = value[part]
    return value


def find(value, text, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            find(item, text, path + "/" + str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            find(item, text, path + "/" + str(index))
    elif isinstance(value, str) and text in value:
        print(path + " = " + (value if len(value) <= 300 else value[:300] + "..."))


def main():
    with open(sys.argv[1], "rb") as stream:
        document = json.loads(stream.read())
    command = sys.argv[2]
    if command == "shape":
        shape(document, int(sys.argv[3]))
    elif command == "get":
        for pointer in sys.argv[3:]:
            print(json.dumps(get(document, pointer), indent=1, sort_keys=False))
    elif command == "keys":
        value = get(document, sys.argv[3])
        print(json.dumps(list(value) if isinstance(value, dict) else len(value)))
    elif command == "find":
        find(document, sys.argv[3])


main()
