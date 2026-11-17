#!/usr/bin/env python3
"""Read-only, deterministic probe of the frozen ownership API's I/O refusal."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--expect-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    reader_bytes = args.reader.read_bytes()
    sha = hashlib.sha256(reader_bytes).hexdigest()
    if sha != args.expect_sha256:
        raise SystemExit("reader input hash differs from review authorization")
    spec = importlib.util.spec_from_file_location("c257_static_reader", args.reader)
    reader = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = reader
    spec.loader.exec_module(reader)

    # No path is created; this ordinary string produces a read-only lookup.
    path = "/tmp/ontokin-c257-static-probe-" + "x" * 5000
    result = {
        "schema": "ontokin.c257.static-io-probe/0.1",
        "reader": str(args.reader), "readerSha256": sha,
        "inputRecipe": {"repo": {"prefix": "/tmp/ontokin-c257-static-probe-",
                                 "repeat": "x", "repeatCount": 5000},
                        "endpoint": "before"},
        "repoArgumentBytes": len(path.encode()),
        "repoArgumentSha256": hashlib.sha256(path.encode()).hexdigest(),
        "expected": "reader.Fault explicit public refusal",
        "sideEffects": "none: no input or source writes",
    }
    try:
        reader.read_bound_endpoint(path, "before")
    except Exception as exc:
        result.update(observedExceptionType=type(exc).__name__,
                      errno=getattr(exc, "errno", None),
                      messagePrefix=str(exc)[:180],
                      normalizedFault=isinstance(exc, reader.Fault),
                      code=getattr(exc, "code", None))
        result["status"] = "PASS_EXPLICIT_REFUSAL" if isinstance(exc, reader.Fault) else "FAIL_UNNORMALIZED_EXCEPTION"
    else:
        result["status"] = "FAIL_UNEXPECTED_SUCCESS"
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result.get(k) for k in ("status", "readerSha256", "observedExceptionType", "errno", "code")}, sort_keys=True))


if __name__ == "__main__":
    main()
