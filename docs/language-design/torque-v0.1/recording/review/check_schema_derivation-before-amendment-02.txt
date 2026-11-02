#!/usr/bin/env python3
"""Check the exact additive recording-schema derivation and pinned source basis.

This is an identity/shape derivation check, not a full JSON Schema validator or
evidence of runtime acceptance. It reads pinned Git blobs without importing them.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output must be fresh")
    packet = Path(__file__).resolve().parents[1]
    basis = json.loads((packet / "recording/SOURCE-BASIS.json").read_text())
    rows = []

    def check(name, value):
        rows.append({"name": name, "passed": bool(value)})
        if not value:
            raise AssertionError(name)

    def blob(path):
        return subprocess.run(["git", "-C", str(args.repository), "cat-file", "blob",
            basis["baseline_commit"] + ":" + path], check=True, capture_output=True).stdout

    for item in basis["files"]:
        data = blob(item["path"])
        digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        check("source-identity:" + item["path"], len(data) == item["bytes"]
              and hashlib.sha256(data).hexdigest() == item["sha256"]
              and digest == item["git_blob_sha1"])
        mode = subprocess.run(["git", "-C", str(args.repository), "ls-tree",
            basis["baseline_commit"], "--", item["path"]], check=True, capture_output=True).stdout
        check("source-mode:" + item["path"], mode.split(b" ", 1)[0].decode() == item["mode"])

    old = json.loads(blob("docs/language-design/planar-reach-v0.1/schema-drafts/quantization.schema.json"))
    common = json.loads(blob("docs/language-design/planar-reach-v0.1/schema-drafts/common.schema.json"))
    new = json.loads((packet / "recording-quantization.schema.json").read_text())
    checked = copy.deepcopy(new)
    local_defs = checked.pop("$defs")
    for key in ["$id", "$comment", "title", "description"]:
        checked[key] = old[key]
    checked["properties"]["schema_version"] = old["properties"]["schema_version"]
    certificate = checked["properties"]["interval_certificates"]["items"]
    for name in ["angular_acceleration_bound_rad_per_s2", "enclosing_angular_acceleration_bound_rad_per_s2"]:
        check("new-alpha-shape:" + name, certificate["properties"][name] == {"type": "number", "minimum": 0}
              and name in certificate["required"])
        certificate["properties"].pop(name)
        certificate["required"].remove(name)
    prefix = "https://omegapy.github.io/OntoKin/proposals/planar-reach-v0.1/common.schema.json"

    def restore_refs(item):
        if isinstance(item, dict):
            if "$ref" in item and item["$ref"].startswith("#/$defs/"):
                item["$ref"] = prefix + item["$ref"]
            for value in item.values():
                restore_refs(value)
        elif isinstance(item, list):
            for value in item:
                restore_refs(value)

    restore_refs(checked)
    check("exact-inherited-quantization-shape", checked == old)
    for name, value in local_defs.items():
        restored = copy.deepcopy(value)
        restore_refs(restored)
        check("exact-localized-common-definition:" + name, restored == common["$defs"][name])
    profile = json.loads((packet / "recording-profile.schema.json").read_text())
    check("closed-profile", profile["type"] == "object" and profile["additionalProperties"] is False
          and set(profile["required"]) == set(profile["properties"]))
    check("fixed-profile-values", all(set(value) == {"const"} for value in profile["properties"].values()))
    result = {"schema_version": "ontokin.c090-recording-schema-derivation/1", "status": "passed",
        "created_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "baseline_commit": basis["baseline_commit"], "checks": len(rows), "rows": rows,
        "full_json_schema_validator_executed": False, "production_imported_or_executed": False,
        "runtime_or_release_acceptance": False}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": "passed", "checks": len(rows)}))


if __name__ == "__main__":
    main()
