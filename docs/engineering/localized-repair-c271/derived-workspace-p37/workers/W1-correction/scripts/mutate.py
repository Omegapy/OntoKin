"""Mutation check of W1's implementation: each mutation must make at least one focused test fail.

Usage: python3 -I -S -B mutate.py <run_module.sh> <worktree> <evidence directory>
For each mutation it replaces exactly one text in one of W1's own files, runs the prescribed test command
on the module that covers it (through run_module.sh), restores the original bytes and checks their digest.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PROVIDER = "prototypes/static_tray_v01/current_host_readback_v02.py"
DRIVER = "tools/check_local.py"
PROVIDER_TESTS = "tests.test_current_host_readback_provider_v02"
DRIVER_TESTS = "tests.test_local_checks"
MUTATIONS = [
    ("MP1 no case-folded record guard", PROVIDER,
     "and not copied_source_path(name) and name.casefold() not in recorded)", "and not copied_source_path(name))",
     PROVIDER_TESTS),
    ("MP2 any XY form admitted for an uncopied path", PROVIDER, 'line[:3] == " D "', "len(line) > 3", PROVIDER_TESTS),
    ("MP3 the driver's copied set not consulted", PROVIDER,
     "and not copied_source_path(name) and name.casefold()", "and name.casefold()", PROVIDER_TESTS),
    ("MP4 a deletion admitted without the record", PROVIDER,
     "recorded = _copied_names(copied) if derived and copied is not None else None",
     "recorded = _copied_names(copied) if derived and copied is not None else (set() if derived else None)", PROVIDER_TESTS),
    ("MP5 the selection drops the parent proof's record", PROVIDER, "check=check, copied=copied)", "check=check, copied=None)",
     PROVIDER_TESTS),
    ("MP6 no check of empty, current or parent components", PROVIDER,
     '\n                    and all(part not in ("", ".", "..") for part in name.split("/"))', "", PROVIDER_TESTS),
    ("MP7 quoted names admitted", PROVIDER, """and not name.startswith('"'), "SOURCE",""", """, "SOURCE",""", PROVIDER_TESTS),
    ("MD1 no index refresh", DRIVER, "        refresh_workspace_index(workspace)\n", "        pass\n", DRIVER_TESTS),
    ("MD2 refresh without -q", DRIVER, '"update-index", "-q", "--refresh"', '"update-index", "--refresh"', DRIVER_TESTS),
    ("MD3 copied set without the ignored() exclusion", DRIVER,
     "return (parts[0] in SOURCE_DIRS or name in ROOT_FILES) and not any(ignored(part) for part in parts)",
     "return parts[0] in SOURCE_DIRS or name in ROOT_FILES", DRIVER_TESTS),
]


def main():
    runner, worktree, evidence = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    results = []
    for index, (label, relative, old, new, module) in enumerate(MUTATIONS, 1):
        path = worktree / relative
        original = path.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        text = original.decode("utf-8")
        assert text.count(old) == 1, (label, text.count(old))
        run_label = "mutation-%02d" % index
        try:
            path.write_bytes(text.replace(old, new).encode("utf-8"))
            completed = subprocess.run(["/bin/sh", runner, run_label, module], capture_output=True, text=True)
        finally:
            path.write_bytes(original)
        restored = hashlib.sha256(path.read_bytes()).hexdigest()
        log = (evidence / "runs" / (run_label + ".log")).read_text(errors="replace")
        failing = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", log, re.MULTILINE)))
        results.append({"mutation": label, "file": relative, "run": run_label, "runner": completed.stdout.strip(),
                        "detected": bool(failing), "failing_tests": [name + " (" + where + ")" for name, where in failing],
                        "restored": restored == before, "sha256": before})
        print(label, "detected" if failing else "NOT DETECTED", "restored" if restored == before else "NOT RESTORED", flush=True)
    (evidence / "MUTATIONS.json").write_text(json.dumps(results, indent=1) + "\n")


if __name__ == "__main__":
    main()
