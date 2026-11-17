#!/usr/bin/env python3
"""Recheck five original helper controls because the dependency resolution callsite changed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest import mock

AUDIT = Path(__file__).resolve().parent
READER_SHA = "397413d7c403693a349075711bc3dd77fab863d200b06a979cec2f0112114937"
HELPER_SHA = "c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1"


def main():
    reader = (AUDIT/"final-source/follows.py").read_bytes()
    helper = (AUDIT/"corrected-source/ownership.py").read_bytes()
    assert hashlib.sha256(reader).hexdigest() == READER_SHA
    assert hashlib.sha256(helper).hexdigest() == HELPER_SHA and len(helper) == 35942
    inputs = AUDIT/"helper-probe-inputs"
    inputs.mkdir(exist_ok=True)
    marker = b"raise RuntimeError('UNADMITTED_HELPER_EXECUTED')\n"
    changed = marker+b" "*(len(helper)-len(marker))
    oversized = helper+b"\n"
    (inputs/"same-size-wrong-hash.py").write_bytes(changed)
    (inputs/"one-byte-oversized.py").write_bytes(oversized)
    cases = []
    for case in ("missing", "same-size-wrong-hash", "one-byte-oversized", "symlink", "exact-pinned"):
        with tempfile.TemporaryDirectory(prefix="c258-static-helper-") as temporary:
            root = Path(temporary)
            reader_path = root/"localized-repair-c258/follows.py"
            reader_path.parent.mkdir()
            reader_path.write_bytes(reader)
            helper_path = root/"localized-repair-c257/ownership.py"
            helper_path.parent.mkdir()
            if case == "same-size-wrong-hash":
                helper_path.write_bytes(changed)
            elif case == "one-byte-oversized":
                helper_path.write_bytes(oversized)
            elif case == "symlink":
                helper_path.symlink_to(AUDIT/"corrected-source/ownership.py")
            elif case == "exact-pinned":
                helper_path.write_bytes(helper)
            spec = importlib.util.spec_from_file_location("c258_static_"+case.replace("-", "_"), reader_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            opened, read_sizes = [], []
            original_open = Path.open
            class TrackedFile:
                def __init__(self, handle):
                    self.handle = handle
                def __enter__(self):
                    self.handle.__enter__()
                    return self
                def __exit__(self, *args):
                    return self.handle.__exit__(*args)
                def read(self, size=-1):
                    read_sizes.append(size)
                    assert size == 35943, "dependency read must be exact-size-plus-one"
                    return self.handle.read(size)
            def guarded_open(path, *args, **kwargs):
                opened.append(str(path))
                assert case not in ("missing", "one-byte-oversized", "symlink"), "inadmissible dependency was opened"
                return TrackedFile(original_open(path, *args, **kwargs))
            row = {"case": case, "expected": "load approved helper" if case == "exact-pinned" else "Fault DEPENDENCY",
                   "inputRecipe": {"readerSha256": READER_SHA, "helper": case},
                   "helperBytes": None if case == "missing" else len(oversized) if case == "one-byte-oversized" else len(helper),
                   "helperSha256": None if case == "missing" else hashlib.sha256(changed if case == "same-size-wrong-hash" else oversized if case == "one-byte-oversized" else helper).hexdigest()}
            with mock.patch.object(Path, "open", guarded_open):
                try:
                    if case == "exact-pinned":
                        loaded = module.dependency()
                        assert loaded.__file__ == str(helper_path)
                        row.update(passed=True, approvedHelperLoaded=True)
                    else:
                        module.observe_glb_follows(b"")
                        row.update(passed=False, unexpectedSuccess=True)
                except Exception as exc:
                    row.update(passed=case != "exact-pinned" and isinstance(exc, module.Fault) and exc.code == "DEPENDENCY",
                               exceptionType=type(exc).__name__, code=getattr(exc, "code", None), detail=str(exc)[:200])
            row.update(helperOpenCount=len(opened), helperReadSizes=read_sizes)
            cases.append(row)
            if not row["passed"]:
                shutil.copytree(root, AUDIT/("failed-helper-"+case))
    report = {"schema": "ontokin.c258.static-helper-admission-probes/0.1",
              "commit": "2bca9f7d2cba8996043bbfeae0c2855def5d7076", "readerSha256": READER_SHA,
              "helperSha256": HELPER_SHA, "passed": all(x["passed"] for x in cases), "cases": cases,
              "preservation": "Exact reader/helper and changed helper inputs retained; temporary layouts are fully reproduced by this script.",
              "projectSourceEdits": False, "numericOrSemanticControlsExecuted": False}
    (AUDIT/"FINAL-HELPER-PROBES.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"passed": report["passed"], "controls": len(cases), "readerSha256": READER_SHA,
                      "cases": [{"case": x["case"], "passed": x["passed"], "helperOpenCount": x["helperOpenCount"], "helperReadSizes": x["helperReadSizes"]} for x in cases]}, sort_keys=True))
    assert report["passed"]


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    main()
