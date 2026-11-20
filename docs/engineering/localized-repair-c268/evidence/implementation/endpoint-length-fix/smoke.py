#!/usr/bin/env python3
"""Implementation-author smoke for the reviewed endpoint-length correction."""
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
REPO = HERE.parents[5]
READER = REPO / "docs/engineering/localized-repair-c268/endpoint_reader.py"


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(REPO)), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    spec = importlib.util.spec_from_file_location("c268_endpoint_length_smoke", READER)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    results = []
    previous = (HERE / "endpoint_reader.py.before.txt").read_bytes()
    expected = previous.replace(b"if type(endpoint) is not str or endpoint not in PINS:",
                                b"if type(endpoint) is not str or len(endpoint) not in (5, 6) or endpoint not in PINS:")
    assert expected != previous and READER.read_bytes() == expected
    results.append({"case": "only the endpoint-length guard changed", "outcome": "pass"})
    for endpoint in ("before", "after"):
        result = reader.read_bound_endpoint(REPO, endpoint)
        assert result["endpoint"] == endpoint and result["historicalInputsBound"] is True
        assert (result["hingeCount"], result["siteCount"]) == (8, 16)
        assert len({tuple(row["definitionId"]) for row in result["records"]}) == 1
        assert result["acceptedRevisionQualified"] is False and result["executionAllowed"] is False
        results.append({"case": "original endpoint smoke", "endpoint": endpoint, "outcome": "pass",
                        "hinges": result["hingeCount"], "sites": result["siteCount"]})
    selector = "b" * 1000001
    with mock.patch.object(reader.os, "open", side_effect=AssertionError("unexpected file access")):
        try:
            reader.read_bound_endpoint(REPO, selector)
        except reader.Fault as fault:
            assert (fault.code, fault.reason) == ("ENDPOINT", "ENDPOINT")
            assert fault.sourceHashes == fault.sourceBytes == {}
            assert fault.artifactSha256 is None and fault.artifactBytes is None
            results.append({"case": "oversized endpoint refused before file access", "outcome": "pass",
                            "characters": len(selector), "code": fault.code, "reason": fault.reason})
        else:
            raise AssertionError("oversized endpoint was admitted")
    report = {"schema": "ontokin.c268.implementation-endpoint-length-smoke/0.1",
              "role": "implementation author; no independent review claim",
              "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
              "command": "PYTHONDONTWRITEBYTECODE=1 python3 docs/engineering/localized-repair-c268/evidence/implementation/endpoint-length-fix/smoke.py",
              "python": sys.version, "platform": platform.platform(),
              "checkedFiles": [identity(path) for path in (READER, Path(__file__), HERE / "endpoint_reader.py.before.txt")],
              "results": results, "passed": len(results), "failed": 0,
              "limits": "Focused correction smoke only; independent selector-lookup control and exact-candidate review remain separate."}
    target = HERE / "RESULTS.json"
    assert not target.exists(), "preserve prior evidence"
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": len(results), "failed": 0, "evidence": str(target)}))


if __name__ == "__main__":
    main()
