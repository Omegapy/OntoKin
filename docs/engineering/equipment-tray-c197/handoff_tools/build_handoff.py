"""Seal a C197 handoff from an exact committed tree and supplied final controls.

This builder never decides whether a product result or integration passed.
The coordinating worker supplies the completed current controls and evidence.
Only a temporary bare repository receives packaging references.
"""

from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_package import MANIFEST, digest, safe, verify


TOOLS_PATH = "docs/engineering/equipment-tray-c197/handoff_tools"
REPLAY_PATH = "docs/engineering/accepted-revision-c196/run_transition.py"
REQUIRED_CONTROLS = {"README-START-HERE.md", "HANDOFF-C197.md", "CHECKPOINT-C197.json", "NEXT-TASK.md"}
OID = re.compile(r"[0-9a-f]{40}")


def environment():
    result = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return result


def run_git(repository, *arguments, text=True, bare=False):
    location = ["--git-dir", str(repository)] if bare else ["-C", str(repository)]
    return subprocess.check_output(
        ["git", *location, "-c", "core.hooksPath=" + os.devnull,
         "-c", "pack.threads=2", "-c", "pack.windowMemory=64m", *arguments],
        text=text, stderr=subprocess.PIPE, env=environment())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_empty(path):
    if path.is_symlink():
        raise ValueError("A packaging destination cannot be a symbolic link: " + str(path))
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError("Packaging directory must be new or empty: " + str(path))
    path.mkdir(parents=True, exist_ok=True)


def copy_controls(source, destination):
    observed = set()
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("Control inputs cannot contain symbolic links")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Control inputs contain a special file")
        relative = path.relative_to(source).as_posix()
        parts = safe(relative).parts
        if parts[0] in {"source", "tools", ".git"} or relative == MANIFEST:
            raise ValueError("Control inputs use a reserved package path: " + relative)
        if path.suffix.lower() in {".zip", ".bundle", ".xz", ".gz", ".7z"}:
            raise ValueError("Keep archive payloads in the committed source, without top-level duplicates")
        if "/" not in relative and re.match(r"(?:README|HANDOFF|CHECKPOINT|NEXT-TASK|PACKAGE-MANIFEST)-C[0-9]+", relative):
            if relative not in {"HANDOFF-C197.md", "CHECKPOINT-C197.json"}:
                raise ValueError("Control inputs contain an older or competing handoff: " + relative)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        observed.add(relative)
    if not REQUIRED_CONTROLS.issubset(observed):
        raise ValueError("Missing current control files: " + str(sorted(REQUIRED_CONTROLS - observed)))


def history_snapshots(paths):
    histories = []
    for path in paths:
        path = path.resolve()
        descriptor_bytes = path.read_bytes()
        descriptor = json.loads(descriptor_bytes)
        name = descriptor.get("bundle")
        if not isinstance(name, str) or Path(name).name != name or name in ("", ".", ".."):
            raise ValueError("Historical bundle must have a local basename")
        bundle = path.parent / name
        if bundle.is_symlink() or not bundle.is_file():
            raise ValueError("Historical bundle must be a regular file")
        with bundle.open("rb") as stream:
            actual = digest(stream)
        if actual != descriptor.get("bundleSha256") or bundle.stat().st_size != descriptor.get("bundleBytes"):
            raise ValueError("Historical bundle differs from its identified descriptor")
        boundaries = descriptor.get("shallowBoundaries", [])
        if not isinstance(boundaries, list) or any(not isinstance(oid, str) or not OID.fullmatch(oid) for oid in boundaries):
            raise ValueError("Historical snapshot has invalid boundaries")
        histories.append({"path": bundle, "descriptor": descriptor,
                          "receipt": {"descriptorSha256": hashlib.sha256(descriptor_bytes).hexdigest(),
                                      "bundleSha256": actual, "bundleBytes": bundle.stat().st_size,
                                      "shallowBoundaries": sorted(set(boundaries)),
                                      "checkpointRefCount": len(descriptor.get("checkpointRefs", {}))}})
    return histories


def retained_references(repository, extras, commit, boundaries, histories):
    refs = {"refs/checkpoints/c197-delivered": commit}
    local = []
    lines = run_git(repository, "for-each-ref", "--format=%(refname) %(objectname) %(symref)",
                    "refs/heads", "refs/remotes", "refs/checkpoints").splitlines()
    for line in lines:
        parts = line.split()
        if len(parts) != 2:
            continue
        ref, oid = parts
        checkpoint = ref if ref.startswith("refs/checkpoints/") else "refs/checkpoints/c197-observed/" + ref.removeprefix("refs/")
        refs[checkpoint] = oid
        local.append({"local_ref": ref, "commit": oid, "retained_as": checkpoint})
    inputs = [json.loads(path.read_text(encoding="utf-8")) for path in extras]
    inputs.extend(history["descriptor"] for history in histories)
    for values in inputs:
        mapping = values.get("checkpointRefs", values)
        if not isinstance(mapping, dict):
            raise ValueError("Retention input must be a reference mapping or snapshot")
        for ref, oid in mapping.items():
            if ref in refs and refs[ref] != oid:
                raise ValueError("Conflicting retained reference: " + ref)
            refs[ref] = oid
    for oid in boundaries:
        refs.setdefault("refs/checkpoints/history-boundary/" + oid, oid)
    for ref, oid in refs.items():
        if not isinstance(ref, str) or not ref.startswith("refs/checkpoints/"):
            raise ValueError("Retention references must be under refs/checkpoints/")
        if not isinstance(oid, str) or not OID.fullmatch(oid):
            raise ValueError("Retention requires exact commit identities")
        run_git(repository, "check-ref-format", ref)
    return dict(sorted(refs.items())), local


def make_bundle(repository, commit, branch, source, extras, history_paths, work_parent):
    objects_path = Path(run_git(repository, "rev-parse", "--git-path", "objects").strip())
    if not objects_path.is_absolute():
        objects_path = repository / objects_path
    objects_path = objects_path.resolve()
    if "\n" in str(objects_path):
        raise ValueError("Object path cannot contain a newline")
    shallow_path = Path(run_git(repository, "rev-parse", "--git-path", "shallow").strip())
    if not shallow_path.is_absolute():
        shallow_path = repository / shallow_path
    boundaries = set(shallow_path.read_text(encoding="ascii").split()) if shallow_path.exists() else set()
    histories = history_snapshots(history_paths)
    for history in histories:
        boundaries.update(history["descriptor"].get("shallowBoundaries", []))
    boundaries = sorted(boundaries)
    if any(not OID.fullmatch(oid) for oid in boundaries):
        raise ValueError("Source has invalid declared shallow boundaries")
    refs, local = retained_references(repository, extras, commit, boundaries, histories)
    run_git(repository, "check-ref-format", "refs/heads/" + branch)
    bundle = source / "repository.bundle"
    with tempfile.TemporaryDirectory(prefix="c197-bundle-", dir=work_parent) as temporary:
        bare = Path(temporary) / "snapshot.git"
        subprocess.run(["git", "init", "--bare", "--quiet", "--template=", str(bare)],
                       check=True, env=environment(), capture_output=True)
        (bare / "objects/info/alternates").write_text(str(objects_path) + "\n", encoding="utf-8")
        if boundaries:
            (bare / "shallow").write_text("".join(oid + "\n" for oid in boundaries), encoding="ascii")
        for history in histories:
            run_git(bare, "bundle", "verify", str(history["path"]), bare=True)
            run_git(bare, "bundle", "unbundle", str(history["path"]), bare=True)
        for ref, oid in refs.items():
            if run_git(bare, "cat-file", "-t", oid, bare=True).strip() != "commit":
                raise ValueError("Retained identity is not an available commit: " + oid)
            run_git(bare, "update-ref", ref, oid, bare=True)
        run_git(bare, "update-ref", "refs/heads/" + branch, commit, bare=True)
        run_git(bare, "symbolic-ref", "HEAD", "refs/heads/" + branch, bare=True)
        missing = [line for line in run_git(bare, "rev-list", "--objects", "--all", "--missing=print", bare=True).splitlines()
                   if line.startswith("?")]
        if missing:
            raise ValueError("Retained history has missing objects: " + str(missing))
        run_git(bare, "bundle", "create", "--version=2", str(bundle), "--all", bare=True)
    with bundle.open("rb") as stream:
        bundle_hash = digest(stream)
    snapshot = {
        "schema": "ontokin.c197.source-snapshot/0.1",
        "repository": "https://github.com/Omegapy/OntoKin.git",
        "branch": branch, "commit": commit,
        "tree": run_git(repository, "rev-parse", commit + "^{tree}").strip(),
        "bundle": bundle.name, "bundleBytes": bundle.stat().st_size, "bundleSha256": bundle_hash,
        "shallowBoundaries": boundaries, "checkpointRefs": refs,
        "retainedLocalReferences": local,
        "importedHistorySources": [history["receipt"] for history in histories],
        "completeCurrentTree": True, "requiresPreviousHandoff": False,
        "historyMeaning": "All trees and objects reachable from the delivered and retained refs are included through the declared shallow boundaries. Older parents beyond those boundaries are omitted. Local retained refs are historical observations, not a claim about current remote refs.",
        "preparedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    write_json(source / "snapshot.json", snapshot)
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit", required=True, help="Exact final 40-character source commit")
    parser.add_argument("--branch", default="snapshot-c197", help="Restored branch; use main only for an observed main commit")
    parser.add_argument("--controls", type=Path, required=True, help="Coordinator-authored finalized control files and optional small receipts")
    parser.add_argument("--output", type=Path, required=True, help="New final ZIP path")
    parser.add_argument("--staging", type=Path, required=True, help="New or empty package staging directory outside the repository")
    parser.add_argument("--retain-refs", type=Path, action="append", default=[], help="Additional exact checkpoint-ref mapping or source snapshot JSON; repeatable")
    parser.add_argument("--history-snapshot", type=Path, action="append", default=[],
                        help="Verified historical source snapshot whose bundle supplies otherwise unavailable retained objects; repeatable")
    parser.add_argument("--receipt", type=Path, help="Optional final build receipt outside the immutable package")
    arguments = parser.parse_args()
    repository = arguments.repo.resolve()
    controls = arguments.controls.resolve()
    staging = arguments.staging.absolute()
    output = arguments.output.absolute()
    if not OID.fullmatch(arguments.commit):
        raise ValueError("--commit must be an exact observed commit identity")
    if run_git(repository, "rev-parse", "HEAD").strip() != arguments.commit:
        raise ValueError("The checkout is not at the requested final commit")
    if run_git(repository, "status", "--porcelain").strip():
        raise ValueError("The source checkout must be clean before final packaging")
    if not controls.is_dir():
        raise ValueError("The supplied final controls directory does not exist")
    if output.exists() or output.is_symlink():
        raise ValueError("Refusing to overwrite an existing output")
    if output.resolve().is_relative_to(repository) or staging.resolve().is_relative_to(repository):
        raise ValueError("Keep packaging output and staging outside the source checkout")
    if controls == staging.resolve() or controls.is_relative_to(staging.resolve()):
        raise ValueError("Control inputs must be outside the package staging directory")
    if arguments.receipt and arguments.receipt.resolve().is_relative_to(staging.resolve()):
        raise ValueError("The build receipt must be outside the package")
    require_empty(staging)
    staging = staging.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    copy_controls(controls, staging)
    checkpoint = json.loads((staging / "CHECKPOINT-C197.json").read_text(encoding="utf-8"))
    tree = run_git(repository, "rev-parse", arguments.commit + "^{tree}").strip()
    if checkpoint.get("finalizationPending") is not False:
        raise ValueError("The coordinator has not finalized the supplied checkpoint")
    if checkpoint.get("repository", {}).get("commit") != arguments.commit or checkpoint.get("repository", {}).get("tree") != tree:
        raise ValueError("Final controls do not identify the exact requested source")
    if checkpoint.get("repository", {}).get("branch", arguments.branch) != arguments.branch:
        raise ValueError("Checkpoint branch and requested restore branch differ")
    run_git(repository, "cat-file", "-e", arguments.commit + ":" + REPLAY_PATH)
    run_git(repository, "cat-file", "-e", arguments.commit + ":docs/engineering/accepted-revision-c196/evidence/RECORDED-EVIDENCE.json")
    source = staging / "source"
    tools = staging / "tools"
    source.mkdir()
    tools.mkdir()
    for original, destination in [
        ("restore_source.py", source / "restore.py"),
        ("verify_package.py", tools / "verify_package.py"),
        ("replay_recorded.py", tools / "replay_recorded.py"),
        ("README.md", tools / "README.md"),
    ]:
        destination.write_bytes(run_git(repository, "show", arguments.commit + ":" + TOOLS_PATH + "/" + original, text=False))
    snapshot = make_bundle(repository, arguments.commit, arguments.branch, source, arguments.retain_refs,
                           arguments.history_snapshot, staging.parent)
    (source / "README.md").write_text(
        "# Restore the complete C197 source\n\n"
        "The snapshot descriptor identifies the exact commit, tree, bundle digest, retained refs and history boundaries. "
        "The bundle includes the complete delivered source and its committed evidence; no earlier handoff ZIP or network is required.\n\n"
        "```sh\npython3 -IB source/restore.py /absolute/path/to/new-ontokin-checkout\n```\n\n"
        "Use a new or empty destination. Restoration checks the bundle bytes and advertised refs, restores the declared "
        "history boundaries, verifies exact commit/tree identity and Git objects, and requires a clean checkout without external object alternates. "
        "The origin URL is recorded without fetching.\n\n"
        "The descriptor lists every retained checkpoint. Local retained refs are historical observations. "
        "The current tree is complete; parents before the declared shallow boundaries are not included. "
        "Any original unavailable worker history remains unavailable as disclosed in the committed provenance records.\n\n"
        "Read GOAL.md, AGENTS.md and STATUS.md after restoration, then reconcile actual remote main, open PRs and the integration lease before editing. "
        "Run the inherited recorded C196 audit with the packaged tools/replay_recorded.py wrapper; do not repeat completed native or author trials to recover context.\n",
        encoding="utf-8")
    files = {}
    for member in sorted(staging.rglob("*")):
        if member.is_file():
            with member.open("rb") as stream:
                files[member.relative_to(staging).as_posix()] = {"bytes": member.stat().st_size, "sha256": digest(stream)}
    write_json(staging / MANIFEST, {"schema": "ontokin.c197.package-manifest/0.1", "files": files,
                                   "selfHashExcluded": True, "scope": "Exact file inventory and bytes"})
    verify(staging, require_finalized=True)
    with zipfile.ZipFile(output, "x", allowZip64=True) as archive:
        for member in sorted(staging.rglob("*")):
            if member.is_file():
                compression = zipfile.ZIP_STORED if member.suffix == ".bundle" else zipfile.ZIP_DEFLATED
                archive.write(member, member.relative_to(staging).as_posix(), compress_type=compression, compresslevel=6)
    verification = verify(output, require_finalized=True)
    with output.open("rb") as stream:
        output_hash = digest(stream)
    receipt = {"schema": "ontokin.c197.handoff-build/0.1", "output": str(output), "bytes": output.stat().st_size,
               "sha256": output_hash, "staging": str(staging), "source_snapshot": snapshot,
               "package_verification": verification,
               "source_restore_executed": False, "recorded_replay_executed": False,
               "scope": "Packaging only; run one fresh offline restore and the recorded-only audit before delivery"}
    if arguments.receipt:
        write_json(arguments.receipt.resolve(), receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
