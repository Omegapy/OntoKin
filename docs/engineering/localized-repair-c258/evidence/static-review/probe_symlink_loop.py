#!/usr/bin/env python3
"""Reproduce the original filesystem-loop API input and check CLI refusal."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

RECIPE = b"repo=loop; symlink loop -> loop; endpoint=before"
RELATIVE = "docs/engineering/localized-repair-c258/follows.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--reader-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    git_env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}

    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(args.repository), *arguments], env=git_env).decode().strip()

    assert git("rev-parse", "HEAD") == args.commit
    assert git("status", "--porcelain") == ""
    path = args.repository/RELATIVE
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == args.reader_sha256
    spec = importlib.util.spec_from_file_location("c258_static_loop_final", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory(prefix="c258-static-symlink-") as temporary:
        loop = Path(temporary)/"loop"
        loop.symlink_to("loop")
        assert loop.is_symlink() and os.readlink(loop) == "loop"
        api = {"expected": "Fault IO"}
        try:
            module.read_bound_endpoint(str(loop), "before")
            api.update(passed=False, unexpectedSuccess=True)
        except Exception as exc:
            api.update(passed=isinstance(exc, module.Fault) and exc.code == "IO",
                       exceptionType=type(exc).__name__, code=getattr(exc, "code", None),
                       detail=str(exc)[:400])
        process = subprocess.run([sys.executable, "-B", str(path), "--repo", str(loop), "--endpoint", "before"],
                                 env={**git_env, "PYTHONDONTWRITEBYTECODE": "1"},
                                 cwd=args.repository, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=30)
        try:
            output = json.loads(process.stdout)
        except json.JSONDecodeError:
            output = None
        cli = {"exitCode": process.returncode, "stdout": process.stdout, "stderr": process.stderr,
               "expected": "exit 1, JSON REFUSED/IO, empty stderr"}
        cli["passed"] = (process.returncode == 1 and isinstance(output, dict)
                         and output.get("status") == "REFUSED" and output.get("code") == "IO"
                         and output.get("executionAllowed") is False and output.get("realTrialSuccess") is None
                         and process.stderr == "")
    assert not Path(temporary).exists()
    report = {"schema": "ontokin.c258.static-symlink-loop-correction/0.1",
              "commit": args.commit, "tree": git("rev-parse", "HEAD^{tree}"),
              "readerSha256": args.reader_sha256, "readerBytes": len(raw),
              "originalFailure": "SYMLINK-LOOP-ORIGINAL.json",
              "inputRecipe": {"repo": "temporary-directory/loop", "symlinkTarget": "loop", "endpoint": "before"},
              "recipeSha256": hashlib.sha256(RECIPE).hexdigest(),
              "api": api, "cli": cli, "passed": api["passed"] and cli["passed"],
              "temporaryFixtureRemoved": True, "cleanWorktreeAfter": git("status", "--porcelain") == "",
              "projectEdits": False, "numericalOrSemanticControlsExecuted": False,
              "pythonVersion": sys.version}
    assert report["cleanWorktreeAfter"]
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"passed": report["passed"], "apiPassed": api["passed"], "cliPassed": cli["passed"],
                      "commit": args.commit, "readerSha256": args.reader_sha256}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
