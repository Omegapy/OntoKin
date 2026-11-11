"""Verify the exact C198 handoff inventory without executing product code."""

from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import stat
import zipfile


MANIFEST = "PACKAGE-MANIFEST.json"
REQUIRED = {
    "README-START-HERE.md", "HANDOFF-C198.md", "CHECKPOINT-C198.json",
    "NEXT-TASK.md", "source/README.md", "source/snapshot.json",
    "source/repository.bundle", "source/restore.py",
    "tools/verify_package.py", "tools/replay_recorded.py", "tools/README.md",
}
OID = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key: " + key)
        value[key] = item
    return value


def loads(data):
    return json.loads(data, object_pairs_hook=unique_object)


def safe(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("Invalid member path")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError("Unsafe member path: " + name)
    if ":" in path.parts[0]:
        raise ValueError("Unsafe member prefix: " + name)
    return path


def digest(stream):
    return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_rows(files):
    if not isinstance(files, dict) or not files:
        raise ValueError("Empty or invalid package inventory")
    for name, row in files.items():
        path = safe(name)
        if name == MANIFEST:
            raise ValueError("The inventory cannot hash itself")
        if not isinstance(row, dict) or type(row.get("bytes")) is not int or row["bytes"] < 0:
            raise ValueError("Invalid byte count: " + name)
        if not isinstance(row.get("sha256"), str) or not SHA256.fullmatch(row["sha256"]):
            raise ValueError("Invalid digest: " + name)
        if any(str(parent) in files for parent in path.parents if str(parent) != "."):
            raise ValueError("A package file is another file's ancestor: " + name)
    if not REQUIRED.issubset(files):
        raise ValueError("Required package files are missing: " + str(sorted(REQUIRED - set(files))))
    for name in files:
        if "/" not in name and re.match(r"(?:README|HANDOFF|CHECKPOINT|NEXT-TASK|PACKAGE-MANIFEST)-C[0-9]+", name):
            if name not in {"HANDOFF-C198.md", "CHECKPOINT-C198.json"}:
                raise ValueError("A prior or competing top-level handoff control is included: " + name)


def finalization(checkpoint, snapshot, files):
    if snapshot.get("schema") != "ontokin.c198.source-snapshot/0.1":
        raise ValueError("Unexpected source snapshot schema")
    for field in ("commit", "tree"):
        value = snapshot.get(field)
        if not isinstance(value, str) or not OID.fullmatch(value):
            raise ValueError("Source snapshot lacks an exact " + field)
        if checkpoint.get("repository", {}).get(field) != value:
            raise ValueError("Checkpoint and snapshot disagree on " + field)
    if snapshot.get("completeCurrentTree") is not True or snapshot.get("requiresPreviousHandoff") is not False:
        raise ValueError("Source snapshot is not declared self-contained")
    if snapshot.get("bundle") != "repository.bundle":
        raise ValueError("Unexpected source bundle name")
    row = files["source/repository.bundle"]
    if row["bytes"] != snapshot.get("bundleBytes") or row["sha256"] != snapshot.get("bundleSha256"):
        raise ValueError("Source bundle differs from its snapshot descriptor")
    boundaries = snapshot.get("shallowBoundaries")
    if not isinstance(boundaries, list) or len(boundaries) != len(set(boundaries)):
        raise ValueError("Invalid history boundary list")
    if any(not isinstance(value, str) or not OID.fullmatch(value) for value in boundaries):
        raise ValueError("Invalid history boundary identity")
    refs = snapshot.get("checkpointRefs")
    if not isinstance(refs, dict):
        raise ValueError("Missing retained checkpoint references")
    for ref, commit in refs.items():
        if not ref.startswith("refs/checkpoints/") or any(char.isspace() for char in ref):
            raise ValueError("Unexpected retained reference: " + ref)
        if not isinstance(commit, str) or not OID.fullmatch(commit):
            raise ValueError("Invalid retained commit identity")
    return checkpoint.get("finalizationPending") is False


def verify(path, require_finalized=False):
    path = Path(path).resolve()
    if path.is_file():
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            all_names = []
            for entry in entries:
                name = entry.filename.rstrip("/") if entry.is_dir() else entry.filename
                safe(name)
                all_names.append(name)
                mode = entry.external_attr >> 16
                if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFDIR, stat.S_IFREG)):
                    raise ValueError("ZIP contains a special or symbolic-link member")
                if entry.flag_bits & 1:
                    raise ValueError("ZIP contains an encrypted member")
            if len(all_names) != len(set(all_names)):
                raise ValueError("Duplicate ZIP paths")
            names = {entry.filename for entry in entries if not entry.is_dir()}
            manifest = loads(archive.read(MANIFEST))
            files = manifest["files"]
            validate_rows(files)
            if names != set(files) | {MANIFEST}:
                raise ValueError("ZIP inventory differs from manifest")
            for name, expected in files.items():
                if archive.getinfo(name).file_size != expected["bytes"]:
                    raise ValueError("Size mismatch: " + name)
                with archive.open(name) as stream:
                    if digest(stream) != expected["sha256"]:
                        raise ValueError("Hash mismatch: " + name)
            checkpoint = loads(archive.read("CHECKPOINT-C198.json"))
            snapshot = loads(archive.read("source/snapshot.json"))
    elif path.is_dir():
        manifest = loads((path / MANIFEST).read_bytes())
        files = manifest["files"]
        validate_rows(files)
        observed = set()
        for member in path.rglob("*"):
            if member.is_symlink():
                raise ValueError("Extracted package contains a symbolic link")
            if member.is_file():
                observed.add(member.relative_to(path).as_posix())
            elif not member.is_dir():
                raise ValueError("Extracted package contains a special file")
        if observed != set(files) | {MANIFEST}:
            raise ValueError("Extracted package inventory differs from manifest")
        for name, expected in files.items():
            member = path / str(safe(name))
            if not member.resolve().is_relative_to(path):
                raise ValueError("Unsafe extracted member: " + name)
            if member.stat().st_size != expected["bytes"]:
                raise ValueError("Size mismatch: " + name)
            with member.open("rb") as stream:
                if digest(stream) != expected["sha256"]:
                    raise ValueError("Hash mismatch: " + name)
        checkpoint = loads((path / "CHECKPOINT-C198.json").read_bytes())
        snapshot = loads((path / "source/snapshot.json").read_bytes())
    else:
        raise ValueError("Package path does not exist")
    if manifest.get("schema") != "ontokin.c198.package-manifest/0.1":
        raise ValueError("Unexpected package manifest schema")
    complete = finalization(checkpoint, snapshot, files)
    if require_finalized and not complete:
        raise ValueError("Checkpoint finalization is explicitly pending")
    return {"pass": True, "manifest_files": len(files),
            "verified_bytes": sum(row["bytes"] for row in files.values()),
            "checkpoint_finalized": complete,
            "repository_commit": snapshot["commit"], "repository_tree": snapshot["tree"],
            "scope": "Exact package integrity; capability, release and integration claims require their own evidence"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="ZIP file or extracted handoff directory")
    parser.add_argument("--require-finalized", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.path, arguments.require_finalized), indent=2))
