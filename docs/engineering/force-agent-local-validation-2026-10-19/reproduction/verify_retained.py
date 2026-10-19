#!/usr/bin/env python3
"""Check retained attempt archives without a checkout or installed project dependencies."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(data):
    return {"sha256": "sha256:" + hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def read(root, name, expected):
    parts = PurePosixPath(name).parts
    require(parts and not PurePosixPath(name).is_absolute() and ".." not in parts, "Unsafe path")
    path = root.joinpath(*parts)
    require(path.is_file() and not path.is_symlink(), "Missing regular retained file: " + name)
    data = path.read_bytes()
    require(identity(data) == {key: expected[key] for key in ("sha256", "bytes")},
            "Identity mismatch: " + name)
    return data


def deterministic_archive(members):
    output = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=output, mode="wb", compresslevel=9, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, data in sorted(members.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def verify(root):
    results = []
    manifests = sorted(root.glob("*.members.json"))
    require(manifests, "No retained attempt manifests")
    packagers = {identity(p.read_bytes())["sha256"] for p in (root / "reproduction").glob("package_agent05_evidence*.py")}
    for path in manifests:
        manifest = json.loads(path.read_bytes())
        raw_archive = read(root, manifest["archive"]["path"], manifest["archive"])
        members = {}
        with tarfile.open(fileobj=io.BytesIO(raw_archive), mode="r:gz") as archive:
            for item in archive.getmembers():
                require(item.isfile() and not item.issym() and not item.islnk(), "Nonregular archive member")
                name = PurePosixPath(item.name)
                require(name.parts and not name.is_absolute() and ".." not in name.parts and
                        item.name not in members, "Unsafe or repeated archive path")
                require(not item.name.startswith("workspace/") and
                        "service-store" not in name.parts and ".git" not in name.parts and
                        "__pycache__" not in name.parts, "Excluded mutable content in archive")
                require((item.uid, item.gid, item.mtime, item.mode, item.uname, item.gname) ==
                        (0, 0, 0, 0o644, "", ""), "Noncanonical archive metadata")
                members[item.name] = archive.extractfile(item).read()
        actual = [{"path": name, **identity(data)} for name, data in sorted(members.items())]
        require(actual == manifest["members"] and len(actual) == manifest["member_count"],
                "Archive member manifest differs")
        require(sum(item["bytes"] for item in actual) == manifest["uncompressed_bytes"], "Size count differs")
        require(deterministic_archive(members) == raw_archive, "Deterministic archive reconstruction differs")
        summary = json.loads(members["summary.json"])
        audit = json.loads(members["retention-audit.json"])
        for key in ("source_commit", "source_tree", "attempt_status"):
            require(audit[key] == manifest[key], "Archive/audit identity differs: " + key)
        require((summary["git"]["local_head"], summary["git"]["local_tree"], summary["status"]) ==
                (manifest["source_commit"], manifest["source_tree"], manifest["attempt_status"]),
                "Original summary identity differs")
        require(summary["git"]["remote_head_verified"] is False and
                summary["release_certified"] is False and summary["full_product_conformance_certified"] is False,
                "Unexpected remote or certification claim")
        require(members["source-before.json"] == members["source-after.json"], "Retained source inventory changed")
        require(audit["packager_sha256"] in packagers, "Exact original packager source is missing")
        sidecar = root / path.name.replace(".members.json", ".retention-audit.json")
        require(sidecar.read_bytes() == members["retention-audit.json"], "Audit sidecar differs")
        for group, directory in (("shared_prerequisites", "prerequisites"), ("supplemental_records", "supplemental")):
            require(audit[group] == manifest[group], "Supplemental identity records differ")
            for name, expected in manifest[group].items():
                read(root, directory + "/" + name, expected)
        for step in summary["steps"]:
            require(identity(members[step["log"]]) == step["log_identity"], "Step log binding differs")
            for report in step["reports"]:
                require(identity(members[report["path"]]) == {key: report[key] for key in ("sha256", "bytes")},
                        "Step report binding differs")
        results.append({"manifest": path.name, "archive": manifest["archive"],
            "member_count": len(members), "source_commit": manifest["source_commit"],
            "source_tree": manifest["source_tree"], "attempt_status": summary["status"],
            "observed_process_exit_code": audit["observed_process_exit_code"],
            "hashes_and_deterministic_reconstruction": "passed"})
    return {"record_type": "ontokin.retained-archive-reverification/0.1", "integrity": "passed",
        "attempts": results, "scope": "Raw-byte, member-manifest, source identity and deterministic compression checks; no tests or semantic conformance checks are rerun.",
        "release_certified": False, "full_product_conformance_certified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve()), indent=2, sort_keys=True))
