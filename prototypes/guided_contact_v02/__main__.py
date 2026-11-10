"""Explicit experimental entry point, separate from ``python -m ontokin``."""
import argparse
import json

from .api import run, validate_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        command = sub.add_parser(name)
        command.add_argument("source")
        command.add_argument("--host-max-operations", type=int, default=100000)
        command.add_argument("--host-max-elapsed-ms", type=int, default=30000)
        command.add_argument("--cancel-file")
        command.add_argument("--result", dest="result_path")
        if name == "validate":
            command.add_argument("--canonical-out")
        else:
            command.add_argument("--store", required=True)
            command.add_argument("--blender", required=True)
            command.add_argument("--expected-revision")
            command.add_argument("--reopen")
    arguments = vars(parser.parse_args())
    operation = arguments.pop("command")
    result = (validate_source if operation == "validate" else run)(**arguments)
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    return 0 if result["successful"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
