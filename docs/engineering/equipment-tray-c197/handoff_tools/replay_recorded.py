"""Restore the C197 handoff, then audit its unchanged inherited C196 evidence."""

from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile


REPLAY = "docs/engineering/accepted-revision-c196/run_transition.py"
DESCRIPTOR = "docs/engineering/accepted-revision-c196/evidence/RECORDED-EVIDENCE.json"


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_path(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("Invalid evidence member path")
    value = PurePosixPath(name)
    if value.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")) or ":" in value.parts[0]:
        raise ValueError("Unsafe evidence member path: " + name)
    return value


def extract_recorded(repository, descriptor_bytes, destination):
    descriptor = json.loads(descriptor_bytes)
    if descriptor.get("archive") != "recorded-evidence.tar.xz":
        raise ValueError("Unexpected recorded-evidence archive name")
    archive = (repository / DESCRIPTOR).parent / descriptor["archive"]
    if archive.is_symlink() or not archive.is_file():
        raise ValueError("The recorded archive must be a regular file")
    if archive.stat().st_size != descriptor.get("bytes") or file_hash(archive) != descriptor.get("sha256"):
        raise ValueError("Recorded-evidence archive differs from its committed descriptor")
    rows = descriptor.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Recorded evidence has no exact file inventory")
    expected = {}
    for row in rows:
        name = row.get("path")
        safe_path(name)
        if name in expected:
            raise ValueError("Duplicate declared evidence path")
        if type(row.get("bytes")) is not int or row["bytes"] < 0:
            raise ValueError("Invalid evidence byte count")
        if not isinstance(row.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
            raise ValueError("Invalid evidence digest")
        if not isinstance(row.get("mode"), str) or not re.fullmatch(r"0[0-7]{3}", row["mode"]):
            raise ValueError("Evidence modes must be ordinary four-digit octal permissions")
        expected[name] = row
    for name in expected:
        if any(str(parent) in expected for parent in safe_path(name).parents if str(parent) != "."):
            raise ValueError("An evidence file is another file's ancestor")
    destination.mkdir()
    seen = set()
    member_names = set()
    with tarfile.open(archive, "r:xz") as source:
        for member in source:
            name = member.name.rstrip("/") if member.isdir() else member.name
            relative = safe_path(name)
            if name in member_names:
                raise ValueError("Duplicate archive member")
            member_names.add(name)
            target = destination / str(relative)
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError("Evidence member escapes the extraction root")
            if member.isdir():
                if name in expected:
                    raise ValueError("An archive directory is declared as a file")
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile() or member.issparse() or name not in expected:
                raise ValueError("Undeclared or nonregular archive member")
            row = expected[name]
            if member.size != row["bytes"] or member.mode != int(row["mode"], 8):
                raise ValueError("Archive size or mode differs: " + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = source.extractfile(member)
            if stream is None:
                raise ValueError("Unreadable archive member")
            with stream, target.open("xb") as output:
                shutil.copyfileobj(stream, output)
            target.chmod(int(row["mode"], 8))
            if target.stat().st_size != row["bytes"] or file_hash(target) != row["sha256"]:
                raise ValueError("Extracted evidence bytes differ: " + name)
            if stat.S_IMODE(target.stat().st_mode) != int(row["mode"], 8):
                raise ValueError("Extracted evidence mode differs: " + name)
            seen.add(name)
    if seen != set(expected):
        raise ValueError("Recorded archive is missing declared files")
    return {"archive_sha256": descriptor["sha256"], "archive_bytes": descriptor["bytes"],
            "descriptor_sha256": hashlib.sha256(descriptor_bytes).hexdigest(),
            "files": len(seen), "uncompressed_bytes": sum(row["bytes"] for row in expected.values()),
            "modes_restored": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="A new or empty replay workspace outside the handoff")
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repo", type=Path, help="Optional already-restored, clean checkout of the exact snapshot")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    arguments = parser.parse_args()
    package = arguments.package.resolve()
    destination = arguments.destination.absolute()
    if destination.is_symlink():
        raise ValueError("Replay destination must not be a symbolic link")
    destination = destination.resolve()
    if destination == package or destination.is_relative_to(package):
        raise ValueError("Keep replay outputs outside the immutable handoff")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("Replay destination must be new or empty")
    if arguments.timeout_seconds < 1:
        raise ValueError("The replay timeout must be positive")
    snapshot = json.loads((package / "source/snapshot.json").read_text(encoding="utf-8"))
    destination.mkdir(parents=True, exist_ok=True)
    repository = arguments.repo.resolve() if arguments.repo else destination / "repository"
    if not arguments.repo:
        subprocess.run([sys.executable, "-IB", str(package / "source/restore.py"), str(repository)],
                       check=True, timeout=arguments.timeout_seconds)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def git(*items):
        return subprocess.check_output(["git", "-C", str(repository), *items], env=environment)

    if git("rev-parse", "HEAD").decode().strip() != snapshot["commit"]:
        raise ValueError("Replay checkout is not the delivered commit")
    if git("rev-parse", "HEAD^{tree}").decode().strip() != snapshot["tree"] or git("status", "--porcelain").strip():
        raise ValueError("Replay requires the exact, clean delivered tree")
    runner = repository / REPLAY
    runner_bytes = runner.read_bytes()
    if runner_bytes != git("show", snapshot["commit"] + ":" + REPLAY):
        raise ValueError("Recorded-audit entrypoint differs from committed source")
    descriptor_bytes = (repository / DESCRIPTOR).read_bytes()
    if descriptor_bytes != git("show", snapshot["commit"] + ":" + DESCRIPTOR):
        raise ValueError("Recorded evidence descriptor differs from committed source")
    extraction = extract_recorded(repository, descriptor_bytes, destination / "work")
    command = [sys.executable, "-IB", str(runner), "audit", "--work", str(destination / "work"),
               "--out", str(destination / "audit")]
    completed = subprocess.run(command, check=False, timeout=arguments.timeout_seconds)
    receipt = {"schema": "ontokin.c197.inherited-c196-recorded-audit/0.1", "command": command,
               "repository_commit": snapshot["commit"], "repository_tree": snapshot["tree"],
               "recorded_replay_sha256": hashlib.sha256(runner_bytes).hexdigest(),
               "extraction": extraction,
               "returncode": completed.returncode,
               "scope": "Recorded C196 evidence audit; native work and inherited receiving jobs are not requested"}
    (destination / "PACKAGED-REPLAY.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    if completed.returncode:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
