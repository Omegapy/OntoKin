"""Verify the handoff archive and the clean, extracted kit used by the Pod."""

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from zipfile import ZipFile


def verify_kit(archive_path, kit):
    manifest_name = "PACKAGE-MANIFEST.json"
    with ZipFile(archive_path) as archive:
        manifest_bytes = archive.read(manifest_name)
    manifest = json.loads(manifest_bytes)
    if manifest["checkpoint"] != "C174" or "runpod/run-c174.sh" not in manifest["files"]:
        raise ValueError("Expected the integrated C174 Runpod archive")

    if (kit / manifest_name).read_bytes() != manifest_bytes:
        raise ValueError("The extracted manifest differs from the supplied archive")

    expected = set(manifest["files"]) | {manifest_name}
    observed = set()
    for path in kit.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Unexpected symbolic link: {path.relative_to(kit)}")
        if path.is_dir():
            continue
        name = path.relative_to(kit).as_posix()
        if not path.is_file() or name not in expected:
            raise ValueError(f"Unexpected extracted entry: {name}")
        observed.add(name)
        if name == manifest_name:
            continue
        record = manifest["files"][name]
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if path.stat().st_size != record["bytes"] or digest != record["sha256"]:
            raise ValueError(f"Extracted file differs from archive: {name}")
    if observed != expected:
        raise ValueError(f"Missing extracted files: {sorted(expected - observed)}")
    # Use the same archive verification as the offline C174 restore.
    verify_archive = runpy.run_path(str(kit / "tools/verify_package.py"))["verify"]
    count = verify_archive(archive_path)
    print(f"PASS. Verified {count} payloads in both the ZIP and extracted kit.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("kit", type=Path)
    args = parser.parse_args()
    verify_kit(args.archive, args.kit)
