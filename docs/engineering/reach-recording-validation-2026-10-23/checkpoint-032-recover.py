"""Verify an identified checkpoint archive completely before fresh extraction."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_name(value):
    name = PurePosixPath(value)
    require(value and name.parts and not name.is_absolute() and ".." not in name.parts and
            "\\" not in value and str(name) == value, f"Unsafe archive path: {value}")
    return name


def checked_bytes(path, record):
    require(path.is_file() and not path.is_symlink(), f"Not a regular input: {path}")
    raw = path.read_bytes()
    require(len(raw) == record["bytes"] and digest(raw) == record["sha256"],
            f"Archive identity differs: {path}")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    checkpoint_raw = args.checkpoint.read_bytes()
    checkpoint = json.loads(checkpoint_raw)
    manifest_raw = args.manifest.read_bytes()
    require(digest(manifest_raw) == checkpoint["manifest_sha256"], "Wrong member manifest")
    manifest = json.loads(manifest_raw)
    archive = checkpoint["archive"]
    names = [part["path"] for part in archive["parts"]]
    require(names and len(names) == len(set(names)), "Empty or duplicated archive parts")
    joined = b"".join(checked_bytes(args.checkpoint.parent / safe_name(part["path"]), part)
                      for part in archive["parts"])
    require(len(joined) == archive["bytes"] and digest(joined) == archive["sha256"],
            "Wrong joined archive")
    members = {item["path"]: item for item in manifest["members"]}
    require(len(members) == len(manifest["members"]) == archive["member_count"],
            "Wrong or duplicated manifest membership")
    for value in members:
        name = safe_name(value)
        require(all(str(parent) not in members for parent in name.parents),
                f"Conflicting file and directory paths: {value}")
    require(not args.output.exists() and not args.receipt.exists(),
            "Extraction directory and receipt must both be new")
    with zipfile.ZipFile(io.BytesIO(joined)) as archive_file:
        actual = archive_file.namelist()
        require(len(actual) == len(set(actual)) and set(actual) == set(members),
                "ZIP and manifest membership differ")
        require(archive_file.testzip() is None, "ZIP CRC failure")
        for info in archive_file.infolist():
            safe_name(info.filename)
            require(not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16),
                    "Directory or symbolic link in file archive")
            raw = archive_file.read(info.filename)
            expected = members[info.filename]
            require(len(raw) == expected["bytes"] and digest(raw) == expected["sha256"],
                    f"Wrong member: {info.filename}")
        args.output.mkdir(parents=True)
        for name in actual:
            destination = args.output / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(archive_file.read(name))
            checked_bytes(destination, members[name])
    receipt = {
        "schema_version": "ontokin.evidence-archive-recovery/0.1",
        "checkpoint": checkpoint["checkpoint"], "status": "passed",
        "checkpoint_sha256": digest(checkpoint_raw),
        "manifest_sha256": digest(manifest_raw),
        "archive_sha256": digest(joined), "archive_bytes": len(joined),
        "parts": len(names), "members": len(members),
        "zip_crc": "passed", "exact_membership": "passed",
        "member_hashes": "passed", "safe_paths": "passed",
        "extracted_file_hashes": "passed", "path_layout": "passed",
        "output": str(args.output.resolve()), "product_rerun": False,
        "release_acceptance": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
