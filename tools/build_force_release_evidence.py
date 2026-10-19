#!/usr/bin/env python3
"""Collect immutable force-release evidence without executing or certifying it.

A collection plan explicitly names source files/directories and their relative
destinations, role records and optional new reference manifests. Retained bytes
are copied exactly. The sole template operation, {"$file": "relative/path"},
inserts that collected file's measured path/hash/length identity. The collector
never changes an existing report, invents a review or runs an evidence command.
Use run_force_conformance.py audit separately to assess the completed collection.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PLAN_SCHEMA = "ontokin.force-evidence-collection-plan/0.1"
MAX_FILES = 20000
MAX_BYTES = 512 * 1024 * 1024
OMIT_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "service-store"}
MUTABLE = re.compile(r"(?:\.sqlite(?:3)?|\.db)(?:-wal|-shm|-journal)?$|\.(?:pyc|pyo)$")
ROLE_NAMES = {"source", "mapped-tests", "compatibility", "force-agent", "force-delivery",
              "force-native", "agent-native", "force-browser", "agent-browser", "legacy", "legacy-visual"}
RESERVED = {"evidence.json", "audit.json", "collection-plan.json", "collection.json"}


def require(value, message):
    if not value:
        raise ValueError(message)


def safe_name(value):
    require(isinstance(value, str) and value and "\\" not in value and "\0" not in value, "Expected a relative POSIX file path")
    p = PurePosixPath(value)
    require(bool(p.parts) and not p.is_absolute() and p.as_posix() == value and all(part not in (".", "..") for part in p.parts),
            "Unsafe or noncanonical evidence destination: " + value)
    require(not any(part in OMIT_DIRS for part in p.parts) and not MUTABLE.search(value),
            "Mutable state is not a retained artifact: " + value)
    return value


def no_symlinks(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)), "Symbolic links are not collection inputs: " + str(path))
    return path


def identity(path, name):
    raw = Path(path).read_bytes()
    return {"path": name, "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(), "byte_length": len(raw)}


def copy_inventory(copies, output):
    """Preflight the whole copy, including collisions, before creating output."""
    require(isinstance(copies, list) and copies, "A collection needs explicit copy inputs")
    output = no_symlinks(output)
    records, excluded, names, total = [], [], set(), 0
    for item in copies:
        require(isinstance(item, dict) and set(item) == {"source", "destination"}, "Unexpected copy descriptor")
        require(isinstance(item["source"], str) and Path(item["source"]).is_absolute(), "Copy inputs must be absolute paths")
        source = no_symlinks(item["source"])
        destination = safe_name(item["destination"])
        require(source.exists() and (source.is_file() or source.is_dir()), "Missing or unsupported copy input: " + str(source))
        require(source != output and source not in output.parents and output not in source.parents,
                "Source and output trees must not overlap")
        files = []
        if source.is_file():
            files.append((source, destination))
        else:
            for parent, directories, filenames in os.walk(source, followlinks=False):
                parent = Path(parent)
                for name in directories:
                    no_symlinks(parent / name)
                for name in directories[:]:
                    if name in OMIT_DIRS:
                        excluded.append(str(parent / name)); directories.remove(name)
                directories.sort()
                for name in sorted(filenames):
                    p = no_symlinks(parent / name)
                    require(p.is_file(), "A collection input is not a regular file: " + str(p))
                    if MUTABLE.search(name):
                        excluded.append(str(p)); continue
                    files.append((p, destination + "/" + p.relative_to(source).as_posix()))
        for path, name in files:
            name = safe_name(name)
            require(name not in RESERVED and name not in names, "Reserved or colliding destination: " + name)
            require(not any(name.startswith(other + "/") or other.startswith(name + "/") for other in names),
                    "A destination is both a file and a directory: " + name)
            require(len(records) < MAX_FILES, "Collection file budget exceeded")
            total += path.stat().st_size
            require(total <= MAX_BYTES, "Collection byte budget exceeded")
            record = identity(path, name)
            require(record["byte_length"] == path.stat().st_size, "Input changed during preflight: " + str(path))
            records.append((path, record)); names.add(name)
    return records, excluded


def resolve_references(value, files):
    if isinstance(value, list):
        return [resolve_references(item, files) for item in value]
    if isinstance(value, dict):
        if "$file" in value:
            require(set(value) == {"$file"}, "A file placeholder cannot contain other fields")
            name = safe_name(value["$file"])
            require(name in files, "A reference names an uncollected file: " + name)
            return dict(files[name])
        require(not any(key.startswith("$") for key in value), "Unsupported collection template operation")
        return {key: resolve_references(item, files) for key, item in value.items()}
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def collect(plan_path, output):
    from ontokin import force_conformance as release
    plan_path, output = no_symlinks(plan_path), no_symlinks(output)
    plan_raw = plan_path.read_bytes()
    plan = release.json_file(plan_path)
    require(set(plan) <= {"schema_version", "copies", "manifests", "roles"} and plan.get("schema_version") == PLAN_SCHEMA,
            "Unsupported collection plan")
    require(isinstance(plan.get("roles"), dict) and set(plan["roles"]) <= ROLE_NAMES, "Unknown evidence role")
    require(not output.exists(), "Collection output must be a new directory")
    before = release.source_identity()
    require(before["committed_inputs_match"], "Commit eligible implementation inputs before collecting release evidence")
    planned, excluded = copy_inventory(plan["copies"], output)
    manifests = plan.get("manifests", [])
    require(isinstance(manifests, list), "Reference manifests must be a list")
    files = {record["path"]: record for _, record in planned}
    # Resolve and preflight new reference manifests in the explicit plan order.
    # A supplied status or observation is retained as supplied; only the later
    # independent release auditor can establish whether it is supported.
    generated = []
    for item in manifests:
        require(isinstance(item, dict) and set(item) == {"destination", "value"}, "Unexpected reference manifest descriptor")
        name = safe_name(item["destination"])
        require(name not in RESERVED and name not in files and
                not any(name.startswith(other + "/") or other.startswith(name + "/") for other in files),
                "Colliding reference manifest: " + name)
        value = resolve_references(item["value"], files)
        raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        record = {"path": name, "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(), "byte_length": len(raw)}
        generated.append((raw, record)); files[name] = record
    roles = resolve_references(plan["roles"], files)
    require(len(files) + 2 <= MAX_FILES and sum(r["byte_length"] for r in files.values()) + len(plan_raw) <= MAX_BYTES,
            "Complete collection exceeds its declared budget")
    output.mkdir(parents=True)
    for source, record in planned:
        no_symlinks(source)
        raw = source.read_bytes()
        require("sha256:" + hashlib.sha256(raw).hexdigest() == record["sha256"] and len(raw) == record["byte_length"],
                "Input changed before copy: " + str(source))
        target = output / record["path"]; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    for raw, record in generated:
        target = output / record["path"]; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    require(plan_path.read_bytes() == plan_raw, "The collection plan changed during copying")
    (output / "collection-plan.json").write_bytes(plan_raw)
    after = release.source_identity()
    require(release.stable_source(before, after) and after["committed_inputs_match"], "Eligible inputs changed during collection")
    write_json(output / "collection.json", {"schema_version": "ontokin.force-evidence-collection/0.1",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(), "source_before": before, "source_after": after,
        "copied_files": len(planned), "new_reference_manifests": len(generated), "excluded_mutable_inputs": excluded,
        "reports_rewritten": False, "commands_executed": False, "visual_review_performed": False,
        "release_certified": False, "full_product_conformance_certified": False})
    for name in ("collection-plan.json", "collection.json"):
        files[name] = identity(output / name, name)
    require(sum(r["byte_length"] for r in files.values()) <= MAX_BYTES, "Complete retained collection exceeds its byte budget")
    # Verify the completed destination bytes as well as the input-copy hashes.
    require(all(identity(output / name, name) == record for name, record in files.items()), "Collected bytes changed")
    manifest = {"schema_version": release.EVIDENCE_SCHEMA, "implementation": before["implementation"],
                "input_inventory_sha256": before["input_inventory_sha256"], "roles": roles,
                "files": [files[name] for name in sorted(files)]}
    write_json(output / "evidence.json", manifest)
    return {"output": str(output), "files": len(files), "bytes": sum(r["byte_length"] for r in files.values()),
            "evidence_manifest": identity(output / "evidence.json", "evidence.json"), "release_certified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = collect(args.plan, args.output_dir)
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "failed", "error": str(error), "release_certified": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
