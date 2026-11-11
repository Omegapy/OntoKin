"""Record bounded C205 CPU checks; do not start native admission work."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--modules", nargs="+", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(repo)
    sys.path.insert(0, str(repo))
    sys.dont_write_bytecode = True

    def git(*words):
        return subprocess.check_output(["git", "-C", str(repo), *words], text=True).strip()

    identity = {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
                "status": git("status", "--porcelain")}
    if identity["status"]:
        raise RuntimeError("Candidate must be clean before CPU evidence")
    host_platform = platform.platform()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child_attempts = []

    def observe(event, values):
        if event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"}:
            child_attempts.append({"event": event, "arguments": repr(values)[:2000]})
            raise RuntimeError("Child start forbidden inside this CPU-only check")

    sys.addaudithook(observe)
    modules = [importlib.import_module(name) for name in args.modules]
    source_rows = [{"path": Path(module.__file__).relative_to(repo).as_posix(),
                    "sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()}
                   for module in modules]
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules)
    passed = []
    executed = []

    class RecordedResult(unittest.TextTestResult):
        def startTest(self, test):
            executed.append(test.id())
            super().startTest(test)

        def addSuccess(self, test):
            passed.append(test.id())
            super().addSuccess(test)

    with (output / "tests.log").open("w") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResult).run(suite)
    source_equal = all(hashlib.sha256((repo / row["path"]).read_bytes()).hexdigest() == row["sha256"] for row in source_rows)
    record = {"schema": "ontokin.c205.cpu-checks/0.1", "startedAtUtc": started,
              "completedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source": identity, "python": platform.python_version(), "platform": host_platform,
              "command": sys.argv, "modules": args.modules, "moduleBindings": source_rows,
              "testsRun": result.testsRun, "passed": len(passed), "failures": result.failures,
              "errors": result.errors, "skipped": result.skipped, "executedIds": executed,
              "childStartAttempts": child_attempts, "testModuleInputsUnchanged": source_equal,
              "success": result.wasSuccessful() and not result.skipped and source_equal and not child_attempts,
              "scope": "In-process CPU controls only; no native, receiving, Node, lifecycle or timed-author execution"}
    (output / "RESULT.json").write_text(json.dumps(record, indent=2, default=str) + "\n")
    print(json.dumps({k: record[k] for k in ["source", "testsRun", "passed", "success", "childStartAttempts"]}))
    return 0 if record["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
