#!/usr/bin/env python3
"""Prepare an exact no-rewrite LFS archive plan without changing the repository.

This command writes only a new external output directory. It neither installs
filters nor stages, commits, uploads or fetches anything. Complete authentication
and the documented storage validation before publishing pointer commits.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.storage_identity import (PROFILE, StorageContext, StorageIdentityError,
                                    archive_path, blob_id, git, pointer_bytes)

BOOTSTRAP_ATTRIBUTES = """# OntoKin future engineering archives. Existing payloads remain ordinary Git.
# Upload and independently retrieve LFS objects before publishing their pointers.
docs/engineering/lfs-archives/**/*.zip filter=lfs diff=lfs merge=lfs -text
docs/engineering/lfs-archives/**/*.zip.part[0-9][0-9][0-9] filter=lfs diff=lfs merge=lfs -text
docs/engineering/lfs-archives/**/*.tar.xz filter=lfs diff=lfs merge=lfs -text
docs/engineering/lfs-archives/**/*.tar.gz filter=lfs diff=lfs merge=lfs -text
"""

ATTRIBUTES = """# OntoKin engineering archive storage profile 0.1.
# Retain original commit history and exact archive/member bytes.
# Source, specifications, JSON manifests, fixtures and images remain ordinary Git.
docs/engineering/**/*.zip filter=lfs diff=lfs merge=lfs -text
docs/engineering/**/*.zip.part[0-9][0-9][0-9] filter=lfs diff=lfs merge=lfs -text
docs/engineering/**/*.tar.xz filter=lfs diff=lfs merge=lfs -text
docs/engineering/**/*.tar.gz filter=lfs diff=lfs merge=lfs -text
"""


def identity(path: Path) -> dict:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": path.name, "bytes": path.stat().st_size, "sha256": "sha256:" + digest}


def prepare(root: Path, output: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    if output == root or output.is_relative_to(root):
        raise StorageIdentityError("Write the draft outside the source checkout")
    if output.exists():
        raise StorageIdentityError("Plan output must be a new directory")
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise StorageIdentityError("Prepare migration from a clean identified source revision")
    context = StorageContext(root)
    configuration = {name for name in context.entries if Path(name).name in {".gitattributes", ".lfsconfig"}}
    if configuration:
        if configuration != {".gitattributes"} or (root / ".gitattributes").read_bytes() != BOOTSTRAP_ATTRIBUTES.encode("utf-8"):
            raise StorageIdentityError("This planner requires explicit review of existing attributes/LFS config other than the exact bootstrap")
        context.verify_file(".gitattributes")
        if context.lfs_paths:
            raise StorageIdentityError("Existing LFS payloads require a reviewed incremental migration plan")
    before = {"commit": context.revision,
              "tree": git(root, "rev-parse", context.revision + "^{tree}").decode().strip()}
    files = []
    for name in sorted(context.entries):
        if not archive_path(name):
            continue
        binding = context.verify_file(name)
        if binding["kind"] != "git-blob" or context.entries[name].mode != "100644":
            raise StorageIdentityError("Expected an unchanged ordinary archive blob: " + name)
        payload = binding["payload"]
        pointer = pointer_bytes(payload["sha256"].removeprefix("sha256:"), payload["bytes"])
        files.append({"path": name, "bytes": payload["bytes"], "payload_sha256": payload["sha256"],
                      "original_git_blob": context.entries[name].blob,
                      "proposed_pointer_bytes": len(pointer),
                      "proposed_pointer_git_blob": blob_id(pointer, context.algorithm)})
    if not files:
        raise StorageIdentityError("No supported engineering archives were found")
    after = {"commit": git(root, "rev-parse", "HEAD").decode().strip(),
             "tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip()}
    if after != before or git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise StorageIdentityError("Source changed while preparing the archive plan")
    output.mkdir(parents=True)
    attributes = output / "gitattributes.proposed"
    attributes.write_text(ATTRIBUTES, encoding="utf-8")
    paths = output / "archive-paths.nul"
    paths.write_bytes(b"\0".join(item["path"].encode("utf-8") for item in files) + b"\0")
    report = {"schema_version": "ontokin.lfs-archive-plan/0.1", "profile": PROFILE,
              "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "state": "prepared_not_applied_not_uploaded", "source": before,
              "source_unchanged": True, "archive_count": len(files),
              "archive_bytes": sum(item["bytes"] for item in files), "files": files,
              "generated_inputs": [identity(attributes), identity(paths)],
              "planner": identity(Path(__file__).resolve()),
              "network_transfers": False, "repository_mutated": False,
              "history_rewritten": False, "requires_authenticated_upload": True,
              "requirements": ["Every old commit/archive ref remains unchanged.",
                               "Verify this exact source, path list and proposed attributes before staging.",
                               "Upload objects and independently fetch exact payloads before main integration.",
                               "Preserve prior validation attribution; execute the relevant new storage checks."]}
    (output / "plan.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return report


def verify_plan(root: Path, plan_path: Path, output: Path) -> dict:
    """Verify a conversion or fresh hydration against the unchanged original tree."""
    root, output = root.resolve(), output.resolve()
    if output == root or output.is_relative_to(root) or output.exists():
        raise StorageIdentityError("Verification output must be a new directory outside the checkout")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("schema_version") != "ontokin.lfs-archive-plan/0.1" or plan.get("profile") != PROFILE:
        raise StorageIdentityError("Unsupported LFS archive plan")
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise StorageIdentityError("Verify a clean identified migrated checkout")
    original = StorageContext(root, plan["source"]["commit"])
    current = StorageContext(root)
    if git(root, "rev-parse", original.revision + "^{tree}").decode().strip() != plan["source"]["tree"]:
        raise StorageIdentityError("Original tree differs from the migration plan")
    git(root, "merge-base", "--is-ancestor", original.revision, current.revision)
    selected = {item["path"]: item for item in plan["files"]}
    expected = {name for name in original.entries if archive_path(name)}
    if (len(selected) != len(plan["files"]) or set(selected) != expected
            or set(current.lfs_paths) != expected or len(selected) != plan["archive_count"]):
        raise StorageIdentityError("Migration path set differs from the complete planned archive scope")
    changed = {name for name in set(original.entries) | set(current.entries)
               if original.entries.get(name) != current.entries.get(name)}
    if changed != expected | {".gitattributes"}:
        raise StorageIdentityError("Migration changed paths outside the planned archives and root attributes")
    attributes = current.verify_file(".gitattributes")
    proposed = next(item for item in plan["generated_inputs"] if item["path"] == "gitattributes.proposed")
    if attributes["payload"]["sha256"] != proposed["sha256"] or attributes["payload"]["bytes"] != proposed["bytes"]:
        raise StorageIdentityError("Committed attributes differ from the proposed tracking rules")
    bindings = []
    for name, item in sorted(selected.items()):
        binding = current.verify_file(name)
        if (binding["kind"] != "git-lfs" or original.entries[name].blob != item["original_git_blob"]
                or binding["payload"]["raw_git_blob"] != item["original_git_blob"]
                or binding["payload"]["sha256"] != item["payload_sha256"]
                or binding["payload"]["bytes"] != item["bytes"]
                or binding["git_object"]["oid"] != item["proposed_pointer_git_blob"]
                or binding["git_object"]["bytes"] != item["proposed_pointer_bytes"]):
            raise StorageIdentityError("Migrated archive identity differs from its original bytes: " + name)
        bindings.append({"path": name, **binding})
    if git(root, "rev-parse", "HEAD").decode().strip() != current.revision:
        raise StorageIdentityError("Source revision changed during storage verification")
    report = {"schema_version": "ontokin.lfs-archive-verification/0.1", "profile": PROFILE,
              "verified_at_utc": datetime.now(timezone.utc).isoformat(), "status": "passed",
              "plan": identity(plan_path), "original": plan["source"],
              "current": {"commit": current.revision, "tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip()},
              "archive_count": len(bindings), "archive_bytes": sum(item["payload"]["bytes"] for item in bindings),
              "files": bindings, "history_rewritten": False, "network_transfers": False,
              "remote_availability_established_by_this_command": False,
              "limit": "This checks locally available bytes. Bind independent authenticated upload/fetch receipts separately."}
    output.mkdir(parents=True)
    (output / "verification.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--verify-plan", type=Path, help="Verify an already committed conversion against this saved plan")
    args = parser.parse_args(argv)
    try:
        result = (verify_plan(args.root, args.verify_plan, args.output_dir) if args.verify_plan
                  else prepare(args.root, args.output_dir))
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps({"state": result.get("state", result.get("status")), "archives": result["archive_count"],
                      "bytes": result["archive_bytes"], "output": str(args.output_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
