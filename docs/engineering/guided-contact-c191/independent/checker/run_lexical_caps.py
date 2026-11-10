#!/usr/bin/env python3
"""Check adopted source caps and precise early runtime diagnostic anchors."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "supplements/lexical-resource"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(repo, destination, revision):
    destination.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.api import validate_source
    contract = repo / "docs/language-design/guided-contact-v0.1"
    schema = json.loads((contract / "output.schema.json").read_text())
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    cancel = destination / "preexisting-cancellation.request"
    cancel.write_text("Cancellation requested before lexical work.\n")
    records = []
    for fixture in manifest["fixtures"]:
        source = FIXTURES / fixture["file"]
        assert digest(source) == fixture["sha256"] and source.stat().st_size == fixture["bytes"]
        record = {"fixture": fixture["file"], "pass": False}
        try:
            result = validate_source(source, host_max_operations=1000000, host_max_elapsed_ms=80000,
                cancel_file=cancel if fixture["preexisting_cancel"] else None)
            (destination / (fixture["file"] + ".result.json")).write_text(json.dumps(result, indent=2) + "\n")
            errors = list(Draft202012Validator(schema).iter_errors(result))
            assert not errors, "; ".join(error.message for error in errors)
            assert not result["successful"] and not result["committed"] and not any(result["levels"].values())
            assert result["source_sha256"] == fixture["sha256"]
            diagnostic, = result["diagnostics"]
            assert diagnostic["code"] == fixture["expected_code"] and diagnostic["phase"] == fixture["expected_phase"]
            assert diagnostic["span"] == fixture["expected_span"], "Full-source-header/execution span mismatch"
            assert all(not result["levels"][level] for level in diagnostic["blocked_levels"])
            if fixture.get("exact_lexical_token_count"):
                assert result["cost"]["operation_components"]["source_tokens"] == fixture["exact_lexical_token_count"]
            record["pass"] = True
        except (AssertionError, ValueError, KeyError, OSError) as error:
            record["failure"] = str(error)
        records.append(record)
    return {"version": "C191-independent-lexical-caps-1", "implementation_revision": revision,
        "fixture_manifest_sha256": digest(FIXTURES / "manifest.json"), "checker_sha256": digest(Path(__file__)),
        "cases": records, "passed": sum(row["pass"] for row in records), "total": len(records),
        "pass": all(row["pass"] for row in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    report = run(args.repo.resolve(), args.out.resolve(), args.revision)
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)
