"""Verify every member of an OntoKin handoff ZIP without extracting it."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


def verify(package):
    with ZipFile(package) as archive:
        names = archive.namelist()
        manifest_name = "PACKAGE-MANIFEST.json"
        manifest = json.loads(archive.read(manifest_name))
        files = manifest["files"]
        if len(names) != len(set(names)) or set(names) != set(files) | {manifest_name}:
            raise ValueError("ZIP member list differs from the manifest")
        for name, record in files.items():
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                raise ValueError(f"Invalid member path {name}")
            with archive.open(name) as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if archive.getinfo(name).file_size != record["bytes"] or actual != record["sha256"]:
                raise ValueError(f"Size or SHA-256 mismatch for {name}")
        return len(files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    args = parser.parse_args()
    print(f"PASS. Verified {verify(args.zip)} manifest-listed files.")
