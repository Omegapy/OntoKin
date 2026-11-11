"""Restore the exact C197 source and retained Git identities without a network."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess


def clean_environment():
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return environment


def restore(source, destination):
    source = Path(source).resolve()
    snapshot = json.loads((source / "snapshot.json").read_text(encoding="utf-8"))
    object_id = re.compile(r"[0-9a-f]{40}")
    if snapshot.get("schema") != "ontokin.c197.source-snapshot/0.1":
        raise ValueError("Unexpected source snapshot schema")
    for field in ("commit", "tree"):
        if not isinstance(snapshot.get(field), str) or not object_id.fullmatch(snapshot[field]):
            raise ValueError("Source snapshot has no exact " + field)
    if snapshot.get("bundle") != "repository.bundle":
        raise ValueError("The source bundle must have its declared local basename")
    bundle = source / snapshot["bundle"]
    if bundle.is_symlink() or not bundle.is_file():
        raise ValueError("The source bundle must be a regular file")
    with bundle.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != snapshot.get("bundleSha256") or bundle.stat().st_size != snapshot.get("bundleBytes"):
        raise ValueError("Source bundle identity mismatch; no checkout was changed")
    boundaries = snapshot.get("shallowBoundaries")
    if not isinstance(boundaries, list) or len(boundaries) != len(set(boundaries)):
        raise ValueError("Invalid declared history boundary")
    if any(not isinstance(value, str) or not object_id.fullmatch(value) for value in boundaries):
        raise ValueError("Invalid declared history boundary")
    branch = snapshot.get("branch")
    if not isinstance(branch, str) or not branch:
        raise ValueError("Snapshot has no branch name")
    refs = snapshot.get("checkpointRefs", {})
    if not isinstance(refs, dict):
        raise ValueError("Invalid retained checkpoint references")
    environment = clean_environment()
    for reference, commit in refs.items():
        if not reference.startswith("refs/checkpoints/") or not isinstance(commit, str) or not object_id.fullmatch(commit):
            raise ValueError("Unexpected retained checkpoint reference")
        subprocess.run(["git", "check-ref-format", reference], check=True, env=environment, capture_output=True)
    subprocess.run(["git", "check-ref-format", "refs/heads/" + branch], check=True, env=environment, capture_output=True)
    header = subprocess.check_output(["git", "bundle", "list-heads", str(bundle)], text=True, env=environment)
    observed = dict((ref, commit) for commit, ref in (line.split(" ", 1) for line in header.splitlines()))
    expected = dict(refs)
    expected["refs/heads/" + branch] = snapshot["commit"]
    expected["HEAD"] = snapshot["commit"]
    if observed != expected:
        raise ValueError("Bundle advertised references differ from the snapshot")
    with bundle.open("rb") as stream:
        if stream.readline() != b"# v2 git bundle\n":
            raise ValueError("Unsupported bundle format")
        while True:
            line = stream.readline()
            if line == b"\n":
                break
            if not line or line.startswith(b"-"):
                raise ValueError("Bundle has omitted prerequisites or an invalid header")
    destination = Path(destination).absolute()
    if destination.is_symlink():
        raise ValueError("Destination must not be a symbolic link")
    destination = destination.resolve()
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("Destination must be new or empty; existing work was not changed")
    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "--quiet", "--template=", str(destination)],
                   check=True, env=environment, capture_output=True)

    def git(*arguments):
        return subprocess.check_output(
            ["git", "-C", str(destination), "--git-dir", str(destination / ".git"),
             "--work-tree", str(destination), "-c", "core.hooksPath=" + os.devnull, *arguments],
            text=True, stderr=subprocess.STDOUT, env=environment,
        ).strip()

    if boundaries:
        (destination / ".git/shallow").write_text("".join(value + "\n" for value in boundaries), encoding="ascii")
    git("bundle", "verify", str(bundle))
    git("bundle", "unbundle", str(bundle))
    for reference, commit in refs.items():
        git("update-ref", reference, commit)
    git("update-ref", "refs/heads/" + branch, snapshot["commit"])
    git("symbolic-ref", "HEAD", "refs/heads/" + branch)
    if Path(git("rev-parse", "--show-toplevel")).resolve() != destination:
        raise ValueError("Git worktree differs from the requested destination")
    git("reset", "--hard", snapshot["commit"])
    git("remote", "add", "origin", snapshot["repository"])
    if git("rev-parse", "HEAD") != snapshot["commit"] or git("rev-parse", "HEAD^{tree}") != snapshot["tree"]:
        raise ValueError("Restored source identity differs from the delivered snapshot")
    if (destination / ".git/objects/info/alternates").exists():
        raise ValueError("Restored repository unexpectedly depends on external objects")
    git("fsck", "--full", "--no-reflogs")
    if git("status", "--porcelain"):
        raise ValueError("Restored checkout is not clean")
    return {"pass": True, "destination": str(destination),
            "commit": snapshot["commit"], "tree": snapshot["tree"], "branch": branch,
            "shallowBoundaries": boundaries, "checkpointRefs": refs,
            "networkUsed": False, "externalObjectAlternates": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="A new or empty checkout directory")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent,
                        help="Directory containing snapshot.json and repository.bundle")
    arguments = parser.parse_args()
    print(json.dumps(restore(arguments.source, arguments.destination), indent=2))
