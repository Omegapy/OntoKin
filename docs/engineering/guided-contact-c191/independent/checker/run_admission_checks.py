#!/usr/bin/env python3
"""Probe C191-A1 bounds and supplemental source/IO robustness through the API."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SUPPLEMENT = HERE.parent / "supplements/pre-admission-and-lexical"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(repo, destination, revision):
    destination.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.api import validate_source
    from prototypes.guided_contact_v01.common import load_contract
    contract = load_contract()
    schema = json.loads((repo / "docs/language-design/guided-contact-v0.1/output.schema.json").read_text())
    manifest = json.loads((SUPPLEMENT / "manifest.json").read_text())
    original_open = Path.open
    records = []
    for fixture in manifest["fixtures"]:
        source = SUPPLEMENT / fixture["file"]
        assert source.stat().st_size == fixture["bytes"] and digest(source) == fixture["sha256"]
        reads = []

        class GuardedFile:
            def __init__(self, file):
                self.file = file

            def __enter__(self):
                self.file.__enter__()
                return self

            def __exit__(self, *arguments):
                return self.file.__exit__(*arguments)

            def read(self, size=-1):
                assert type(size) is int and 0 <= size <= 65537, "Unbounded source read requested"
                data = self.file.read(size)
                reads.append({"requested_bytes": size, "returned_bytes": len(data)})
                assert sum(row["returned_bytes"] for row in reads) <= 65537, "Source admission read exceeded cap"
                return data

            def __getattr__(self, key):
                return getattr(self.file, key)

        def guarded_open(path, *arguments, **keywords):
            handle = original_open(path, *arguments, **keywords)
            return GuardedFile(handle) if path.resolve() == source.resolve() else handle

        record = {"fixture": fixture["file"], "input_sha256": fixture["sha256"], "verified": False}
        try:
            with patch.object(Path, "open", guarded_open):
                result = validate_source(source, host_max_operations=1000000, host_max_elapsed_ms=80000)
            (destination / (fixture["file"] + ".result.json")).write_text(json.dumps(result, indent=2) + "\n")
            errors = list(Draft202012Validator(schema).iter_errors(result))
            assert not errors, "; ".join(error.message for error in errors)
            assert result["successful"] == fixture["expected_success"]
            assert not result["committed"] and not any(result["levels"][level] for level in ("evaluated", "exported", "destination_validated"))
            assert result["source_sha256"] == fixture.get("expected_source_sha256", fixture["sha256"])
            if fixture["expected_success"]:
                assert result["diagnostics"] == []
            else:
                diagnostic, = result["diagnostics"]
                assert diagnostic["code"] == fixture["expected_code"] and diagnostic["phase"] == fixture["expected_phase"]
                assert diagnostic["span"] == fixture["expected_span"], "Wrong source diagnostic span"
                assert all(not result["levels"][level] for level in diagnostic["blocked_levels"])
                if fixture["bytes"] > 65536:
                    assert not any(result["levels"].values()), "Pre-admission failure achieved a source level"
            assert reads, "Source read instrumentation was bypassed"
            record["verified"] = True
        except (AssertionError, ValueError, KeyError, OSError) as error:
            record["failure"] = str(error)
        record["source_reads"] = reads
        records.append(record)

    # These are additional code-review probes, not replacements for frozen cases.
    source = HERE.parent / "source-fixtures/A.ok"
    bad_utf8 = destination / "malformed-utf8.ok"
    data = source.read_bytes() + b"// invalid byte: \xff\n"
    bad_utf8.write_bytes(data)
    invalid_byte = data.index(b"\xff")
    io_directory = destination / "unwritable-file-target"
    io_directory.mkdir()
    probes = [("admitted-malformed-utf8", bad_utf8, {}),
              ("canonical-output-io-failure", source, {"canonical_out": io_directory}),
              ("result-output-io-failure", source, {"result_path": io_directory})]
    for name, source_path, arguments in probes:
        record = {"fixture": name, "verified": False}
        try:
            result = validate_source(source_path, host_max_operations=1000000, host_max_elapsed_ms=80000, **arguments)
            (destination / (name + ".result.json")).write_text(json.dumps(result, indent=2) + "\n")
            errors = list(Draft202012Validator(schema).iter_errors(result))
            assert not errors, "; ".join(error.message for error in errors)
            diagnostic, = result["diagnostics"]
            assert diagnostic["code"] == ("C191_E_PARSE" if "utf8" in name else "C191_E_IO")
            assert not result["successful"] and not result["committed"]
            assert result["source_sha256"] == digest(source_path)
            assert diagnostic["span"] is not None
            assert all(not result["levels"][level] for level in diagnostic["blocked_levels"]), "A blocked level remains reported true"
            if "utf8" in name:
                assert diagnostic["span"]["start_byte"] == invalid_byte
                assert diagnostic["span"]["end_byte"] == invalid_byte + 1
            record["verified"] = True
        except (AssertionError, ValueError, KeyError, OSError) as error:
            record["failure"] = str(error)
        records.append(record)
    return {"version": "C191-independent-admission-robustness-1", "implementation_revision": revision,
        "supplement_manifest_sha256": digest(SUPPLEMENT / "manifest.json"),
        "amendment_sha256": digest(repo / "docs/language-design/guided-contact-v0.1/amendments/C191-A1.md"),
        "cases": records, "passed": sum(row["verified"] for row in records), "total": len(records),
        "pass": all(row["verified"] for row in records)}


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
