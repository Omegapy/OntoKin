#!/usr/bin/env python3
"""Extend only C193's case data for independently fixed G/H targets."""
import argparse
import json
from pathlib import Path
from common import BACKEND_SHA, CASES, CONTRACT, SOURCE_BINDING, artifact_reader, digest, verify_freeze, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    frozen = verify_freeze()
    reader = artifact_reader()
    inherited = reader.verify_frozen()
    result = reader.review(args.artifact, args.case, CONTRACT / "backend.json", BACKEND_SHA, SOURCE_BINDING)
    result.update(c194_freeze=frozen, inherited_preservation=inherited,
                  c194_wrapper_sha256=digest(__file__),
                  extension_scope="G/H case data only; numerical, source, geometry and continuous gates unchanged")
    write(args.out, result, exclusive=True)
    print(json.dumps({"case": args.case, "passed": result["passed"], "failures": result["failures"],
        "native_peak_mm": result["diagnosis"]["peak"]["distance_mm"],
        "continuous_bound_mm": result["mapping_measurements"]["maximumContinuousRawToFinalVertexDeviationBoundMm"]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

