#!/usr/bin/env python3
"""Build and run the isolated pinned codec; emit source-bound finite evidence."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
DEFAULT_FRAME = {
    "lnor": [0, 0, 1], "ref": [1, 0, 0], "ortho": [0, 1, 0],
    "alpha": math.pi / 2, "beta": math.pi,
}
FLAGS = ["-std=c++17", "-O0", "-fno-fast-math", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def length(vector):
    return math.sqrt(sum(x * x for x in vector))


def metrics(reference, actual):
    ref_length, actual_length = length(reference), length(actual)
    result = {
        "maxComponentError": max(abs(a - b) for a, b in zip(reference, actual)),
        "unitLengthDrift": abs(actual_length - 1),
        "referenceUnitLengthDrift": abs(ref_length - 1),
    }
    if ref_length and actual_length:
        a = [x / ref_length for x in reference]
        b = [x / actual_length for x in actual]
        cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
        result["angularErrorRadians"] = math.atan2(length(cross), sum(x*y for x,y in zip(a,b)))
    else:
        result["angularErrorRadians"] = None
    return result


def numeric(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric input")
    if isinstance(value, str) and value in ("NaN", "Infinity", "-Infinity"):
        return {"NaN": "nan", "Infinity": "inf", "-Infinity": "-inf"}[value]
    if not isinstance(value, (int, float)):
        raise ValueError("non-numeric case value")
    return repr(value)


def arguments(case):
    op = case.get("operation", "roundtrip")
    required = {"roundtrip": ("frame", "normal"), "decode": ("frame", "shorts"),
                "normalize": ("normal",), "quantize": ("value",), "acos": ("value",)}
    for field in required.get(op, ()):
        if field not in case:
            raise ValueError("operation requires explicit " + field)
    if op in ("roundtrip", "decode") and "frame" not in case:
        raise ValueError("frame must be explicitly supplied for codec operations")
    frame = case.get("frame", DEFAULT_FRAME)
    normal = case.get("normal", [0, 0, 1])
    shorts = case.get("shorts", [0, 0])
    if any(not isinstance(frame.get(key), list) or len(frame[key]) != 3
           for key in ("lnor", "ref", "ortho")):
        raise ValueError("frame vectors require three components")
    if not isinstance(normal, list) or len(normal) != 3 or not isinstance(shorts, list) or len(shorts) != 2:
        raise ValueError("normal/short input shape")
    if op == "decode" and any(type(value) is not int or value < -32768 or value > 32767 for value in shorts):
        raise ValueError("decode shorts must be exact JSON integers in [-32768,32767]")
    values = frame["lnor"] + frame["ref"] + frame["ortho"]
    values += [frame["alpha"], frame["beta"]] + normal + shorts + [case.get("value", 0)]
    return [op, case.get("mode", "strict")] + [numeric(x) for x in values]


def run(cases_path, output_path, build_dir, compiler):
    # Import locally only after recording the exact helper location.
    sys.path.insert(0, str(ROOT))
    from extract_codec import extract
    expected_header, function_hashes = extract()
    if (ROOT / "codec_exact.inc").read_text() != expected_header:
        raise ValueError("selected exact codec bodies differ from bound upstream source")
    provenance = json.loads((ROOT / "SOURCE-BINDINGS.json").read_text())
    for item in provenance["upstreamFiles"]:
        path = ROOT / item["path"]
        if sha(path) != item["sha256"]:
            raise ValueError("upstream hash mismatch: " + item["path"])
    data = json.loads(cases_path.read_text())
    cases = data["cases"] if isinstance(data, dict) else data
    if not isinstance(cases, list):
        raise ValueError("cases must be a list")
    ids = [case.get("id") for case in cases]
    if any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("case ids must be distinct nonempty strings")
    build_dir.mkdir(parents=True, exist_ok=True)
    executable = build_dir / "codec_probe"
    compiler_path = shutil.which(compiler)
    if compiler_path is None:
        raise RuntimeError("C++ compiler is unavailable: " + compiler)
    command = [compiler_path] + FLAGS + [str(ROOT / "codec_probe.cpp"), "-o", str(executable)]
    compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (build_dir / "compile.stdout.log").write_text(compiled.stdout)
    (build_dir / "compile.stderr.log").write_text(compiled.stderr)
    if compiled.returncode:
        raise RuntimeError("CPU probe compile failed: " + compiled.stderr)
    env = json.loads(subprocess.check_output([str(executable), "--environment"], text=True))
    if env.get("status") == "rejected":
        raise RuntimeError("CPU probe floating-point environment unavailable: " + env["reason"])
    rows = []
    for case in cases:
        row = {"id": case["id"], "operation": case.get("operation", "roundtrip"), "mode": case.get("mode", "strict")}
        try:
            args = arguments(case)
        except (KeyError, TypeError, ValueError) as exc:
            row.update(status="rejected", reason="harness_input_schema", detail=str(exc),
                       probeProcessExecuted=False, codecEncoderExecuted=False,
                       codecDecoderExecuted=False, inputNormalizationExecuted=False,
                       standaloneHelperExecuted=None)
            rows.append(row)
            continue
        observed = subprocess.run([str(executable)] + args, capture_output=True, text=True, timeout=5)
        if observed.returncode:
            raise RuntimeError("CPU kernel failed for " + case["id"] + ": " + observed.stderr)
        row.update(json.loads(observed.stdout))
        row["probeProcessExecuted"] = True
        accepted = row.get("status") == "accepted"
        row.setdefault("codecEncoderExecuted", accepted and row["operation"] == "roundtrip")
        row.setdefault("codecDecoderExecuted", accepted and row["operation"] in ("roundtrip", "decode"))
        row.setdefault("inputNormalizationExecuted", accepted and row["operation"] == "roundtrip" and row["mode"] == "strict")
        row["standaloneHelperExecuted"] = row["operation"] if accepted and row["operation"] in ("normalize", "acos", "quantize") else None
        if row.get("status") == "accepted" and row["operation"] == "roundtrip":
            row["metrics"] = metrics(row["normalizedInput"], row["decoded"])
            row["originalStrictComponentLimit"] = 2e-6
            row["originalStrictComponentLimitPassed"] = row["metrics"]["maxComponentError"] <= 2e-6
        rows.append(row)
    bound_names = ["codec_probe.cpp", "codec_exact.inc", "extract_codec.py", "run_probe.py", "SOURCE-BINDINGS.json"]
    report = {
        "schema": "ontokin.c213.cpu-codec-observations/0.1",
        "upstreamCommit": provenance["upstreamCommit"],
        "caseInputSha256": sha(cases_path),
        "caseCount": len(rows),
        "acceptedCount": sum(row["status"] == "accepted" for row in rows),
        "rejectedCount": sum(row["status"] == "rejected" for row in rows),
        "rejectionsAreHarnessPolicy": True,
        "sourceBindings": {name: sha(ROOT / name) for name in bound_names},
        "selectedFunctionSha256": function_hashes,
        "compiler": {"command": command, "version": subprocess.check_output([compiler_path, "--version"], text=True),
                     "path": compiler_path, "executableSha256": sha(Path(compiler_path).resolve()),
                     "probeSha256": sha(executable), "flags": FLAGS},
        "environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
                        "libc": list(platform.libc_ver()), **env},
        "precision": "Selected float32 operations with contraction and fast math disabled; double metrics are independent diagnostics",
        "limitations": [
            "Explicit supplied frames do not reproduce native fan construction, splitting or averaging",
            "Unit mode feeds supplied float32 values directly; strict mode uses pinned upstream normalization first",
            "No universal error bound or replacement approximation budget is established by finite rows",
            "Installed C211 binary/source provenance and native frame/short values remain unresolved",
            "This standalone scalar build is not bitwise attestation of the Blender executable or every platform libm",
        ],
        "nativeBlenderProcesses": 0,
        "rows": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--compiler", default="g++")
    args = parser.parse_args()
    if args.build_dir:
        result = run(args.cases, args.output, args.build_dir, args.compiler)
    else:
        with tempfile.TemporaryDirectory(prefix="ontokin-c213-codec-") as temporary:
            result = run(args.cases, args.output, Path(temporary), args.compiler)
    print(json.dumps({key: result[key] for key in ("schema", "caseCount", "acceptedCount", "rejectedCount", "nativeBlenderProcesses")}))
