"""Stdlib evidence transport for C088; this module never imports OntoKin."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import dataclasses
import gzip
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback

FROZEN_MANIFEST_SHA256 = "7ef04b64d93a45a4fac681b632a9c02bdb936a34d4565faa44452ce27c07aca1"
SPECIFICATION_SHA256 = "e9a55ae015b1892453217deea38ea85e269e2551608ab5ed7aa7d21bea337d0b"
PREDECESSOR_COMMIT = "a969a668f9fdf021793366ac5f5b9a8f9cd0fa56"
PROFILE = "keyed-membership-0.1"
TARGET = "ontokin.glb/0.21"
PROTOCOL = "ontokin.agent/0.21"
MEMBERSHIP_STAGES = (
    "keyed_membership_admission", "keyed_membership_input", "keyed_membership_query",
    "keyed_membership_scan", "keyed_membership_publication",
)
STRING_STAGES = (
    "string_concat_admission", "string_concat_scan", "string_concat_allocation",
    "string_concat_publication",
)
STAGES = MEMBERSHIP_STAGES + STRING_STAGES


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, indent=2, ensure_ascii=False,
                                allow_nan=False).encode() + b"\n")


def read(path):
    return json.loads(Path(path).read_bytes())


def safe(value, depth=0):
    """Never call a foreign repr/str/comparison while recording native failures."""
    if depth > 20:
        return {"unserializable": "depth_limit"}
    if value is None or type(value) in (bool, int, float, str):
        return value
    if type(value) in (tuple, list):
        return [safe(x, depth + 1) for x in value]
    if type(value) is dict and all(type(k) is str for k in value):
        return {k: safe(v, depth + 1) for k, v in value.items()}
    return {"unserializable_native_type": type(value).__name__}


def node_location(node):
    if node is None:
        return None
    return {"source_id": getattr(node, "source_id", None),
            "start_byte": getattr(node, "start", None),
            "end_byte": getattr(node, "end", None)}


def error_record(error):
    result = {"exception": type(error).__name__, "message": str(error),
              "traceback": "".join(traceback.format_exception(type(error), error, error.__traceback__))}
    if hasattr(error, "diagnostic"):
        d = error.diagnostic
        result["diagnostic"] = {
            "code": d.code, "phase": d.phase, "category": d.category,
            "message": d.message, "details": safe(d.details), "repair": d.repair,
            "rule_ids": d.rule_ids, "primary": node_location(d.node),
            "element_id": safe(d.element_id),
            "related": [node_location(n) for n in d.related],
        }
    return result


def file_record(path, root):
    path, root = Path(path), Path(root)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
            "mode": "100755" if path.stat().st_mode & 0o111 else "100644",
            "sha256": h.hexdigest()}


def inventory(root, *, exclude=()):
    root = Path(root)
    skip = set(exclude)
    result = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Evidence inventory refuses symlinks: " + str(path))
        if path.is_file() and path.relative_to(root).as_posix() not in skip:
            result.append(file_record(path, root))
    return result


def repository_identity(repo):
    repo = Path(repo)
    git = lambda *args: subprocess.check_output(["git", "-C", str(repo), *args])
    paths = git("ls-files", "-z").split(b"\0")
    rows = [file_record(repo / p.decode(), repo) for p in paths if p]
    return {"commit": git("rev-parse", "HEAD").decode().strip(),
            "tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
            "status": git("status", "--porcelain").decode(),
            "tracked_files": len(rows), "tracked_bytes": sum(r["bytes"] for r in rows),
            "tracked_inventory_sha256": sha(canonical(rows))}


class Freeze:
    """Verify exact immutable input bytes before any product is imported."""
    def __init__(self, root):
        self.root = Path(root).resolve()
        path = self.root / "INPUTS-MANIFEST.json"
        raw = path.read_bytes()
        if sha(raw) != FROZEN_MANIFEST_SHA256:
            raise ValueError("C088 input manifest is not the separately approved exact freeze.")
        self.manifest = json.loads(raw)
        if self.manifest["specification"]["sha256"] != SPECIFICATION_SHA256:
            raise ValueError("C088 input specification identity differs.")
        actual = inventory(self.root, exclude=("INPUTS-MANIFEST.json",))
        if actual != self.manifest["files"]:
            raise ValueError("C088 input file inventory/bytes/modes differ from the freeze.")
        self.before = actual
        self.source = read(self.root / "source-expected.json")
        self.representative = read(self.root / "agent/expected.json")
        self.native = read(self.root / "native-admission-expected.json")
        self.resource = read(self.root / "resource-expected.json")
        self.provenance = read(self.root / "provenance-expected.json")

    def assert_unchanged(self):
        if self.before != inventory(self.root, exclude=("INPUTS-MANIFEST.json",)):
            raise ValueError("An input byte or mode changed during execution.")
        if sha((self.root / "INPUTS-MANIFEST.json").read_bytes()) != FROZEN_MANIFEST_SHA256:
            raise ValueError("Input manifest changed during execution.")

    def lineage(self):
        return {"input_manifest_sha256": FROZEN_MANIFEST_SHA256,
                "input_inventory_sha256": self.manifest["inventory_sha256"],
                "specification_sha256": SPECIFICATION_SHA256}


class EvidenceRun:
    def __init__(self, output, checkout, freeze, kind):
        self.output, self.checkout, self.freeze = Path(output).resolve(), Path(checkout).resolve(), freeze
        self.output.mkdir(parents=True, exist_ok=False)
        self.before = repository_identity(self.checkout)
        if self.before["status"]:
            raise ValueError("A producer must use a clean fixed checkout.")
        self.summary = {
            "schema_version": "ontokin.c088-actual-" + kind + "/1",
            **freeze.lineage(), "status": "running", "started_utc": stamp(),
            "command": [sys.executable, *sys.argv], "python": sys.version,
            "platform": platform.platform(), "source": self.before,
            "release_acceptance": False, "independent_verification": "pending",
            "records": [], "internal_failures": [],
        }
        save(self.output / "source-before.json", self.before)
        save(self.output / "producer-inventory.json", [file_record(p, Path(__file__).parent)
             for p in sorted(Path(__file__).parent.glob("*keyed_membership*.py"))])
        self.checkpoint()

    def checkpoint(self):
        save(self.output / "summary-running.json", self.summary)

    def finish(self):
        self.freeze.assert_unchanged()
        after = repository_identity(self.checkout)
        save(self.output / "source-after.json", after)
        self.summary.update(finished_utc=stamp(), source_unchanged=self.before == after,
                            inputs_unchanged=True,
                            status="recorded" if self.before == after and not self.summary["internal_failures"] else "producer_error")
        save(self.output / "summary.json", self.summary)
        return self.summary["status"] == "recorded"


@contextmanager
def jsonl_writer(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            yield lambda value: zipped.write(canonical(value) + b"\n")


def jsonl_reader(path):
    with gzip.open(path, "rb") as stream:
        for index, raw in enumerate(stream, 1):
            if not raw.endswith(b"\n"):
                raise ValueError("Truncated evidence JSONL row " + str(index))
            yield json.loads(raw)


def standalone_bundle_identity(root, files):
    """Independent byte identity; no product loader or parser is involved."""
    root = Path(root)
    descriptor = read(root / files)
    units, assets = [], []
    for item in [descriptor["entry"], *descriptor["modules"]]:
        package, version = item.get("package_id"), item.get("version")
        units.append({"source_id": "entry" if package is None else "package:" + package + "@" + version,
                      "package_id": package, "version": version, "filename": item["filename"],
                      "source_revision": "sha256:" + sha((root / item["path"]).read_bytes())})
    for item in descriptor["assets"]:
        raw = (root / item["path"]).read_bytes()
        if item["sha256"] != "sha256:" + sha(raw):
            raise ValueError("Asset identity differs from original bytes.")
        assets.append({"asset_id": item["asset_id"], "media_type": item["media_type"],
                       "sha256": item["sha256"], "byte_length": len(raw)})
    manifest = {"schema_version": "ontokin.bundle/0.2", "entry_source_id": "entry",
                "units": sorted(units, key=lambda x: x["source_id"]),
                "assets": sorted(assets, key=lambda x: x["asset_id"])}
    return manifest, "sha256:" + sha(b"ontokin.bundle/0.2\0" + canonical(manifest))
