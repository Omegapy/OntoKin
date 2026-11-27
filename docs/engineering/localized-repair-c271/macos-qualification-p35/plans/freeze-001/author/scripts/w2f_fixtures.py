"""W2 freeze author: the original synthetic GLB and reference bytes, built by the project's own builders.

Run with <worktree>/.venv/bin/python -I -S -B. It imports tests/test_static_tray_reader_v01.py's synthetic()
and the reader's audit() from the worktree (read-only, -B writes no bytecode), refuses every process creation,
and writes only absent files under OUTPUT_DIR. These are the bytes that ReadbackCPUControls.check_case
writes into each cohort stage; the direct-probe rows and MC29 use them as their positive inputs.

Usage: w2f_fixtures.py WORKTREE OUTPUT_DIR
"""
from copy import deepcopy
import hashlib
import json
import os
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("w2f_fixtures starts no process: " + event)


def json_bytes(value):
    """check_case's json_bytes (prototypes/static_tray_v01/canonical.py), for ASCII data."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("ascii")


def write_new(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}


def main():
    sys.addaudithook(refuse)
    root, output = sys.argv[1], sys.argv[2]
    sys.path.insert(0, root)
    import tests.test_static_tray_reader_v01 as reader_tests
    from prototypes.static_tray_v01 import canonical
    rows = {}
    references = {}
    for case in ("Q01", "Q03"):
        directory = os.path.join(output, case)
        os.mkdir(directory, 0o755)
        glb = reader_tests.synthetic(case)
        rows[case + "/synthetic.glb"] = write_new(os.path.join(directory, "synthetic.glb"), glb)
        reference = reader_tests.audit(os.path.join(directory, "synthetic.glb"), case)
        if reference["passed"] is not True:
            raise SystemExit("the original audit did not pass: " + case)
        raw = json_bytes(reference)
        if raw != canonical.json_bytes(reference):
            raise SystemExit("json_bytes differs from canonical.json_bytes")
        rows[case + "/synthetic-audit.json"] = write_new(os.path.join(directory, "synthetic-audit.json"), raw)
        references[case] = reference
    changed = deepcopy(references["Q01"])
    changed["nodes"]["equipment-tray/pair/left/base"]["world_matrix"][0][3] += .001
    changed["scope"] = ("Intentionally changed synthetic reference for a negative importer comparison control; "
                        "not native evidence")
    directory = os.path.join(output, "Q01-changed-reference")
    os.mkdir(directory, 0o755)
    rows["Q01-changed-reference/synthetic-audit.json"] = write_new(os.path.join(directory, "synthetic-audit.json"),
                                                                   json_bytes(changed))
    rows["loaded"] = sorted(name for name in sys.modules if name.startswith(("tests", "prototypes", "reader", "glb",
                                                                               "expected", "corrupt")))
    print(json.dumps(rows, indent=1, sort_keys=True))


main()
