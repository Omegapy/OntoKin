#!/usr/bin/env python3
"""Implementation-author smoke/parity evidence, not independent qualification."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
from unittest import mock


HERE = Path(__file__).absolute().parent
REPO = HERE.parents[4]
ENGINEERING = REPO / "docs/engineering"
READER = ENGINEERING / "localized-repair-c268/endpoint_reader.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(REPO)), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def run():
    reader = load("c268_implementation_reader", READER)
    comparator = load("c268_implementation_raw_comparator",
                      ENGINEERING / "localized-repair-c267/hinge_compare.py")
    results = []
    for endpoint, root in (("before", REPO), ("after", str(REPO)),
                           ("before", Path(".")), ("after", ".")):
        proof = REPO / reader.PROOF
        sources = {"main.ok": (proof / (endpoint + ".main.ok")).read_bytes(),
                   "hinges.ok": (proof / "hinges.ok").read_bytes()}
        raw = (proof / (endpoint + ".glb")).read_bytes()
        expected = comparator.compare_hinges(sources, raw)
        native_read = reader.os.read
        requests = []

        def capture_read(fd, amount):
            requests.append(amount)
            return native_read(fd, amount)

        with mock.patch.object(Path, "open", side_effect=AssertionError("unexpected pathname reopen")), \
                mock.patch.object(reader.os, "read", side_effect=capture_read):
            result = reader.read_bound_endpoint(root, endpoint)
        actual = dict(result)
        for key in ("comparisonSchema", "endpoint", "historicalAdmission"):
            del actual[key]
        actual["schema"] = result["comparisonSchema"]
        actual["historicalInputsBound"] = False
        actual["limits"] = [reader.RAW_HISTORICAL_LIMIT if item == reader.BOUND_HISTORICAL_LIMIT else item
                            for item in actual["limits"]]
        assert actual == expected, "captured dependency invocation changed a comparison field"
        assert result["historicalInputsBound"] is True
        assert (result["hingeCount"], result["siteCount"]) == (8, 16)
        assert len({tuple(row["definitionId"]) for row in result["records"]}) == 1
        assert not [name for name in sys.modules if name.startswith("_c268_")]
        sizes = [pin[2] + 1 for pin in reader.PINS[endpoint]]
        sizes += [pin[1] + 1 for pin in reader.DEPENDENCIES.values()]
        assert requests == sizes, "each admitted file must use one expected-size-plus-one read"
        results.append({"case": "native comparator parity and no pathname reopen",
                        "endpoint": endpoint, "rootType": type(root).__name__,
                        "relativeRoot": not str(root).startswith("/"), "outcome": "pass",
                        "hinges": result["hingeCount"], "sites": result["siteCount"],
                        "readRequests": requests, "admission": result["historicalAdmission"]})

    for root, endpoint, code, reason in (
            (REPO, "other", "ENDPOINT", "ENDPOINT"),
            (REPO, [], "ENDPOINT", "ENDPOINT"),
            (b"/tmp", "before", "INPUT_PATH", "ROOT_TYPE"),
            ("../OntoKin", "before", "INPUT_PATH", "ESCAPE"),
            ("", "before", "INPUT_PATH", "PATH")):
        try:
            reader.read_bound_endpoint(root, endpoint)
        except reader.Fault as fault:
            assert (fault.code, fault.reason) == (code, reason)
            assert not fault.sourceHashes and not fault.sourceBytes
            assert fault.artifactSha256 is None and fault.artifactBytes is None
            results.append({"case": "invalid API argument", "outcome": "pass",
                            "code": fault.code, "reason": fault.reason})
        else:
            raise AssertionError("invalid argument was admitted")
    with mock.patch.object(reader.os, "O_NOFOLLOW", 0):
        try:
            reader.read_bound_endpoint(REPO, "before")
        except reader.Fault as fault:
            assert fault.code == "UNSUPPORTED_PLATFORM"
            results.append({"case": "missing nofollow capability injection", "outcome": "pass",
                            "code": fault.code, "reason": fault.reason})
        else:
            raise AssertionError("unsupported platform was admitted")
    checked = [READER, Path(__file__)]
    checked += [ENGINEERING / pin[0] for pin in reader.DEPENDENCIES.values()]
    report = {"schema": "ontokin.c268.implementation-smoke/0.1",
              "role": "implementation author; no independent review claim",
              "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
              "command": "PYTHONDONTWRITEBYTECODE=1 python3 docs/engineering/localized-repair-c268/evidence/implementation/check_candidate.py",
              "python": sys.version, "platform": platform.platform(),
              "checkedFiles": [identity(path) for path in checked],
              "results": results, "passed": len(results), "failed": 0,
              "limits": "Parity and smoke checks only; independently authored C268 controls and review remain separate gates."}
    (HERE / "RESULTS.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": len(results), "failed": 0, "evidence": str(HERE / "RESULTS.json")}))


if __name__ == "__main__":
    run()
