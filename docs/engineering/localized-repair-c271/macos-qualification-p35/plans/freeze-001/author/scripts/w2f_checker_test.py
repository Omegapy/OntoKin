"""W2 freeze author: run w2f_s7_check.py's phases in this one process against a synthetic freeze (stdlib; -I -S -B).

Usage: w2f_checker_test.py CHECKER SETUP_SCRIPT REAL_FREEZE TEST_DIR
"""
import contextlib
import importlib.util
import io
import json
import runpy
import sys

checker_path, setup_path, real_freeze, test_dir = sys.argv[1:5]
buffer = io.StringIO()
saved = sys.argv
sys.argv = [setup_path, real_freeze, test_dir]
with contextlib.redirect_stdout(buffer):
    runpy.run_path(setup_path, run_name="__main__")
sys.argv = saved
setup = json.loads(buffer.getvalue())
spec = importlib.util.spec_from_file_location("w2f_s7_check_under_test", checker_path)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def run(*arguments):
    out = io.StringIO()
    sys.argv = [checker_path, "--freeze", setup["freeze"], "--freeze-sha256", arguments[0], *arguments[1:]]
    with contextlib.redirect_stdout(out):
        code = checker.main()
    report = json.loads(out.getvalue())
    return code, report.get("state"), report


results = []


def case(name, want_code, want_state, *arguments):
    code, state, report = run(*arguments)
    good = code == want_code and state == want_state
    results.append({"case": name, "ok": good, "code": code, "state": state,
                    "failed": [f.get("check") for f in report.get("failed", [])][:5]})


sha = setup["sha256"]
case("pre", 0, "MET", sha, "pre")
case("prepared", 0, "MET", sha, "prepared")
case("post", 0, "MET", sha, "post")
case("expect T_true", 0, "MET", sha, "expect", "--command", "T_true")
case("expect --audit T_true", 1, "NOT_MET", sha, "expect", "--command", "T_true", "--audit")
for name in setup["false_commands"]:
    case("expect " + name, 1, "NOT_MET", sha, "expect", "--command", name)
case("wrong freeze digest", 2, "REFUSED", "0" * 64, "pre")
case("unknown command", 2, "REFUSED", sha, "expect", "--command", "NOPE")
print(json.dumps({"cases": len(results), "failed": [r for r in results if not r["ok"]]}, indent=1))
print(json.dumps(results, indent=1))
