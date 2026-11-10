#!/usr/bin/env python3
"""Verify and extract retained C194 evidence without running simulations."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile


RELATIVE_EVIDENCE = Path("docs/engineering/contact-comparison-c194/evidence")
ROOT_MAPS = {
    "preparation": {"preparation": "c194-preparation-run"},
    "first-validation": {"first-validation": "c194-first-validation"},
    "completion": {
        "c194-author-runs": "c194-author-runs",
        "c194-reuse-validation": "c194-reuse-validation",
        "c194-reviews": "c194-reviews",
        "c194-first-manifest.json": "c194-first-manifest.json",
        "c194-reuse-manifest.json": "c194-reuse-manifest.json",
        "recovery": "recovery",
    },
}
SHA256 = re.compile(r"[0-9a-f]{64}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def safe_path(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("Invalid evidence path")
    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts) or ":" in parts[0]:
        raise ValueError("Unsafe evidence path: " + name)
    path = PurePosixPath(name)
    if path.is_absolute():
        raise ValueError("Absolute evidence path: " + name)
    return path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def regular_basename(directory, name):
    if len(safe_path(name).parts) != 1:
        raise ValueError("Archive metadata paths must be basenames")
    path = directory / name
    if path.is_symlink() or not path.is_file():
        raise ValueError("Archive metadata must be a regular file: " + name)
    return path


def mapped_path(name, mappings):
    path = safe_path(name)
    if path.parts[0] not in mappings:
        raise ValueError("Unexpected archive root: " + name)
    return PurePosixPath(mappings[path.parts[0]], *path.parts[1:]).as_posix()


def inspect_archives(evidence):
    index_path = regular_basename(evidence, "EVIDENCE-ARCHIVES.json")
    index = read_json(index_path)
    if index.get("schema") != "ontokin.c194.evidence-archives/0.1":
        raise ValueError("Unsupported evidence archive descriptor")
    rows = index.get("archives")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("Exactly three identified evidence archives are required")
    prepared, used_ids, written_paths = [], set(), set()
    for row in rows:
        identifier = row["id"]
        if identifier not in ROOT_MAPS or identifier in used_ids:
            raise ValueError("Unexpected or duplicate archive identity")
        used_ids.add(identifier)
        manifest_path = regular_basename(evidence, row["manifest"])
        if not SHA256.fullmatch(row.get("manifest_sha256", "")) or digest(manifest_path) != row["manifest_sha256"]:
            raise ValueError("Evidence manifest hash mismatch: " + identifier)
        manifest = read_json(manifest_path)
        if manifest.get("schema") != "ontokin.c194.evidence-file-manifest/0.1" or manifest.get("id") != identifier:
            raise ValueError("Evidence manifest identity mismatch")
        if manifest.get("root_mapping") != ROOT_MAPS[identifier]:
            raise ValueError("Evidence root mapping differs from the declared layout")
        archive_path = regular_basename(evidence, row["archive"])
        if manifest.get("archive") != {"name": row["archive"], "bytes": row["bytes"], "sha256": row["sha256"]}:
            raise ValueError("Archive descriptor and file manifest disagree")
        if type(row["bytes"]) is not int or row["bytes"] < 0 or archive_path.stat().st_size != row["bytes"]:
            raise ValueError("Evidence archive size mismatch: " + identifier)
        if not SHA256.fullmatch(row.get("sha256", "")) or digest(archive_path) != row["sha256"]:
            raise ValueError("Evidence archive hash mismatch: " + identifier)
        expected = manifest.get("files")
        if not isinstance(expected, dict) or not expected:
            raise ValueError("Empty or invalid evidence inventory")
        output_paths, allowed_directories = {}, set()
        for name, specification in expected.items():
            safe_path(name)
            output_name = mapped_path(name, ROOT_MAPS[identifier])
            if specification.get("output_path") != output_name:
                raise ValueError("Invalid mapped evidence path: " + name)
            if type(specification.get("bytes")) is not int or specification["bytes"] < 0:
                raise ValueError("Invalid evidence byte count")
            if not SHA256.fullmatch(specification.get("sha256", "")):
                raise ValueError("Invalid evidence digest")
            if output_name in written_paths or output_name in output_paths:
                raise ValueError("Duplicate evidence write: " + output_name)
            output_paths[output_name] = name
            allowed_directories.update(parent.as_posix() for parent in PurePosixPath(output_name).parents if parent.as_posix() != ".")
        if set(output_paths) & allowed_directories or written_paths & allowed_directories:
            raise ValueError("Evidence file/directory collision")
        members, actual_files = set(), set()
        with tarfile.open(archive_path, "r:xz") as archive:
            for member in archive:
                name = member.name.rstrip("/") if member.isdir() else member.name
                safe_path(name)
                if name in members:
                    raise ValueError("Duplicate archive member: " + name)
                members.add(name)
                output_name = mapped_path(name, ROOT_MAPS[identifier])
                if member.isdir():
                    # Empty directories are absent from the file-only manifest
                    # Validate their mapped paths but do not create them
                    directory_paths = [PurePosixPath(output_name), *PurePosixPath(output_name).parents]
                    if any(path.as_posix() in output_paths or path.as_posix() in written_paths
                           for path in directory_paths):
                        raise ValueError("Evidence file/directory collision: " + name)
                    continue
                if not member.isfile() or member.issparse():
                    raise ValueError("Links, sparse files and special archive members are forbidden: " + name)
                if name not in expected or member.size != expected[name]["bytes"]:
                    raise ValueError("Archive file differs from its inventory: " + name)
                actual_files.add(name)
        if actual_files != set(expected):
            raise ValueError("Archive file set differs from its manifest: " + identifier)
        written_paths.update(output_paths)
        prepared.append({"id": identifier, "archive_path": archive_path, "row": row, "files": expected})
    if used_ids != set(ROOT_MAPS):
        raise ValueError("An expected archive is missing")
    return index_path, prepared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    output = args.out.resolve()
    if output.is_relative_to(repo) or output.exists() or args.out.is_symlink():
        raise SystemExit("Extraction output must be a new path outside the source repository")
    evidence = repo / RELATIVE_EVIDENCE
    index_path, prepared = inspect_archives(evidence)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {"schema": "ontokin.c194.evidence-extraction/0.1", "passed": False,
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "repository": str(repo), "output": str(output),
              "archive_index_sha256": digest(index_path), "archives": [],
              "new_native_builds": 0, "new_author_trials": 0, "network_used": False}
    with tempfile.TemporaryDirectory(prefix="c194-extract-", dir=output.parent) as temporary:
        staging = Path(temporary) / "evidence"
        staging.mkdir()
        count, total = 0, 0
        for planned in prepared:
            archive_count, archive_bytes = 0, 0
            with tarfile.open(planned["archive_path"], "r:xz") as archive:
                for member in archive:
                    if member.isdir():
                        continue
                    specification = planned["files"][member.name]
                    destination = staging / specification["output_path"]
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    incoming = archive.extractfile(member)
                    if incoming is None:
                        raise ValueError("Cannot read regular archive file: " + member.name)
                    with incoming, destination.open("xb") as outgoing:
                        shutil.copyfileobj(incoming, outgoing, length=1024 * 1024)
                    if destination.stat().st_size != specification["bytes"] or digest(destination) != specification["sha256"]:
                        raise ValueError("Extracted content differs from its bound manifest: " + member.name)
                    archive_count += 1
                    archive_bytes += specification["bytes"]
            if digest(planned["archive_path"]) != planned["row"]["sha256"]:
                raise ValueError("Evidence archive changed during extraction")
            result["archives"].append({"id": planned["id"], "sha256": planned["row"]["sha256"],
                "manifest_sha256": planned["row"]["manifest_sha256"],
                "files": archive_count, "uncompressed_bytes": archive_bytes})
            count += archive_count
            total += archive_bytes
        result.update(passed=True, completed_utc=datetime.now(timezone.utc).isoformat(),
                      files=count, uncompressed_bytes=total, exact_inventory_verified=True)
        (staging / "EXTRACTION-RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
        if output.exists() or output.is_symlink():
            raise ValueError("Extraction output appeared during processing")
        staging.rename(output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
