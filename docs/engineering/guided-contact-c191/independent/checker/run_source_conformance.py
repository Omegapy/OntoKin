#!/usr/bin/env python3
"""Execute the adopted source fixtures through the public experimental CLI."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "source-fixtures"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(repo, destination, revision):
    destination.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    source_schema = json.loads((repo / "docs/language-design/guided-contact-v0.1/source.schema.json").read_text())
    output_schema = json.loads((repo / "docs/language-design/guided-contact-v0.1/output.schema.json").read_text())
    records = []
    for fixture in manifest["fixtures"]:
        if fixture["mode"] != "validate":
            continue
        source = FIXTURES / fixture["file"]
        assert digest(source) == fixture["sha256"], "Frozen source fixture changed"
        canonical = destination / (fixture["id"] + "-canonical.json")
        command = [sys.executable, "-B", "-m", "prototypes.guided_contact_v01", "validate", str(source),
            "--host-max-operations", "1000000", "--host-max-elapsed-ms", "80000", "--canonical-out", str(canonical)]
        start = time.monotonic()
        completed = subprocess.run(command, cwd=repo, capture_output=True, timeout=30)
        elapsed = time.monotonic() - start
        (destination / (fixture["id"] + ".stdout.txt")).write_bytes(completed.stdout)
        (destination / (fixture["id"] + ".stderr.txt")).write_bytes(completed.stderr)
        record = {"fixture": fixture["id"], "command": command, "cwd": str(repo), "returncode": completed.returncode,
            "elapsed_s": elapsed, "input_sha256": fixture["sha256"], "verified": False, "failures": []}
        try:
            output = json.loads(completed.stdout)
            (destination / (fixture["id"] + ".result.json")).write_text(json.dumps(output, indent=2) + "\n")
            errors = list(Draft202012Validator(output_schema).iter_errors(output))
            assert not errors, "Output schema: " + "; ".join(str(error.message) for error in errors[:3])
            assert output["source_sha256"] == fixture["sha256"], "Source revision mismatch"
            assert output["successful"] == fixture["expected_success"], "Wrong success result"
            assert output["committed"] is False, "Read-only validation committed a revision"
            assert output["levels"]["destination_validated"] is False
            if fixture["expected_success"]:
                assert completed.returncode == 0 and output["diagnostics"] == []
                assert canonical.is_file(), "Successful validation lacks canonical input"
                model = json.loads(canonical.read_text())
                errors = list(Draft202012Validator(source_schema).iter_errors(model))
                assert not errors, "Canonical source model violates adopted schema"
                assert digest(canonical) == output["canonical_input_sha256"]
                if fixture["id"] in "ABCD":
                    expected = (FIXTURES / (fixture["id"] + "-canonical.json")).read_bytes()
                    assert canonical.read_bytes() == expected, "Canonical bytes differ from independently derived input"
                elif fixture["id"] == "E-rename-reorder":
                    assert canonical.read_bytes() == (FIXTURES / "A-canonical.json").read_bytes(), "Rename/reorder changed physical input"
                elif fixture["id"] == "F-ordinary-defaults":
                    assert model["execution"] == {"max_operations": 100000, "max_elapsed_ms": 30000}
                    assert output["cost"]["requested_operations"] == 100000
                    assert output["cost"]["requested_elapsed_ms"] == 30000
            else:
                assert completed.returncode != 0
                diagnostic, = output["diagnostics"]
                assert diagnostic["code"] == fixture["expected_code"], "Wrong diagnostic code: " + diagnostic["code"]
                assert diagnostic["phase"] == fixture["expected_phase"], "Wrong diagnostic phase"
                assert diagnostic["span"] == fixture["expected_span"], "Wrong exact source span: " + json.dumps(diagnostic["span"])
                assert diagnostic["blocked_levels"] == fixture["expected_blocked_levels"], "Wrong blocked levels"
                assert all(not output["levels"][level] for level in diagnostic["blocked_levels"]), "Failed level reported successful"
                assert not canonical.exists(), "Invalid source produced canonical output"
            record["verified"] = True
        except (AssertionError, ValueError, OSError, KeyError, TypeError) as error:
            record["failures"].append(str(error))
        records.append(record)
    return {"version": "C191-independent-source-conformance-1", "implementation_revision": revision,
        "repository": str(repo), "python": platform.python_version(),
        "fixture_manifest_sha256": digest(FIXTURES / "manifest.json"), "cases": records,
        "passed": sum(row["verified"] for row in records), "total": len(records),
        "pass": all(row["verified"] for row in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    report = run(args.repo.resolve(), args.out.resolve(), args.revision)
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"pass": report["pass"], "passed": report["passed"], "total": report["total"],
        "failures": [{"fixture": row["fixture"], "failures": row["failures"]} for row in report["cases"] if not row["verified"]]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)
