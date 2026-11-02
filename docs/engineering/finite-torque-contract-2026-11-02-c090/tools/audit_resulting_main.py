#!/usr/bin/env python3
"""Read-only C090 resulting-main source, native-object and adoption audit.

Uses only the Python standard library and local, read-only Git plumbing. It
does not import OntoKin, run project code, contact a remote, alter the index or
worktree, or infer a product release. The fresh JSON output is outside the repo.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time


BASELINE = "655097f016af17434b9b26fae22491f5f302aa18"
CANDIDATE = "754f72106279abc6c867ab180300f2ba382a3f2d"
MANIFEST = "docs/language-design/torque-v0.1/INPUT-FREEZE.json"
ADOPTION = "docs/language-design/torque-v0.1/ADOPTION.md"
MANIFEST_SHA256 = "98df30158c0cd77c542d89652f5dec6b585d03451a06bf7b1baffee0fc2f02eb"
ALLOWED_OLD = {"STATUS.md", "docs/README.md"}
ALLOWED_NEW = (
    "docs/language-design/torque-v0.1/",
    "docs/language-design/agent-v0.22/",
    "docs/engineering/finite-torque-contract-2026-11-02-c090/",
)
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
CHUNK = 1024 * 1024


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class AuditFailure(Exception):
    pass


class Audit:
    def __init__(self, args):
        self.args = args
        self.repo = Path(args.repo).resolve(strict=True)
        self.started = time.monotonic()
        self.result = {
            "schema_version": "ontokin.c090-resulting-main-independent-audit/1",
            "status": "running",
            "reviewer": "C090 Independent Corpus Author; independent of root integration",
            "started_utc": utc(),
            "repo": str(self.repo),
            "requested_ref": args.ref,
            "baseline": args.baseline,
            "candidate": args.candidate,
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "checks": 0,
            "failures": [],
            "production_imported": False,
            "runtime_executed": False,
            "network_accessed": False,
            "publication_or_lease_release_verified": False,
            "product_release_claimed": False,
            "scope": {
                "allowed_old_changes": sorted(ALLOWED_OLD),
                "allowed_new_prefixes": list(ALLOWED_NEW),
            },
        }
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update({
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_ATTR_NOSYSTEM": "1",
            "LC_ALL": "C",
        })
        self.git_prefix = [
            "git", "--no-optional-locks", "-C", str(self.repo),
            "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
            "-c", "core.untrackedCache=false",
        ]
        self.directory_cache = set()

    def check(self, condition, label, actual=None, expected=None, fatal=False):
        self.result["checks"] += 1
        if condition:
            return
        self.result["failures"].append({
            "check": label, "actual": actual, "expected": expected,
        })
        if fatal:
            raise AuditFailure(label)

    def git(self, *arguments, allow_failure=False):
        run = subprocess.run(
            self.git_prefix + list(arguments), env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if not allow_failure and run.returncode:
            raise AuditFailure(
                "Git plumbing failed: " + repr(arguments) + ": "
                + run.stderr.decode("utf-8", "replace")[:3000]
            )
        return run

    def tree(self, ref, include_trees=False):
        flags = "-rzt" if include_trees else "-rz"
        data = self.git("ls-tree", flags, "--full-tree", ref).stdout
        rows = {}
        for record in data.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
            parts = PurePosixPath(path).parts
            self.check(
                bool(parts) and not path.startswith("/")
                and all(part not in ("", ".", "..") for part in parts)
                and HEX40.fullmatch(oid) is not None and path not in rows,
                "safe unique native tree entry: " + path, fatal=True,
            )
            rows[path] = {"mode": mode, "kind": kind, "oid": oid}
        return rows

    def index(self):
        rows = {}
        for record in self.git("ls-files", "--stage", "-z").stdout.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, oid, stage = metadata.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
            self.check(stage == "0" and path not in rows,
                       "index stage and unique path: " + path,
                       {"stage": stage, "duplicate": path in rows}, fatal=True)
            rows[path] = {"mode": mode, "kind": "blob", "oid": oid}
        return rows

    def worktree_file(self, path, expected):
        full = self.repo / path
        for parent in full.parents:
            if parent == self.repo:
                break
            if parent in self.directory_cache:
                continue
            mode = parent.lstat().st_mode
            self.check(stat.S_ISDIR(mode) and not stat.S_ISLNK(mode),
                       "ordinary source parent: " + str(parent), fatal=True)
            self.directory_cache.add(parent)
        before = full.lstat()
        if expected["mode"] == "120000":
            self.check(stat.S_ISLNK(before.st_mode), "source symlink: " + path, fatal=True)
            data = os.fsencode(os.readlink(full))
            size = len(data)
            git_hash = hashlib.sha1(b"blob " + str(size).encode() + b"\0" + data).hexdigest()
            sha256 = hashlib.sha256(data).hexdigest()
            mode = "120000"
        else:
            self.check(expected["mode"] in ("100644", "100755")
                       and stat.S_ISREG(before.st_mode),
                       "ordinary tracked source: " + path,
                       {"expected_mode": expected["mode"], "stat_mode": before.st_mode}, fatal=True)
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(full, flags)
            with os.fdopen(fd, "rb") as stream:
                opened = os.fstat(stream.fileno())
                self.check((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino),
                           "source file identity on open: " + path, fatal=True)
                size = before.st_size
                gh = hashlib.sha1(b"blob " + str(size).encode() + b"\0")
                sh = hashlib.sha256()
                received = 0
                while True:
                    block = stream.read(CHUNK)
                    if not block:
                        break
                    received += len(block)
                    gh.update(block)
                    sh.update(block)
                self.check(received == size, "source length: " + path, received, size)
            git_hash = gh.hexdigest()
            sha256 = sh.hexdigest()
            mode = "100" + format(stat.S_IMODE(before.st_mode), "03o")
        after = full.lstat()
        stamp = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        self.check(stamp(before) == stamp(after), "source stable during read: " + path)
        self.check(mode == expected["mode"], "source exact mode: " + path, mode, expected["mode"])
        self.check(git_hash == expected["oid"], "source exact native blob: " + path,
                   git_hash, expected["oid"])
        return {"path": path, "mode": mode, "bytes": size,
                "sha256": sha256, "git_blob_sha1": git_hash}

    def native_objects(self, expected_objects):
        child = subprocess.Popen(
            self.git_prefix + ["cat-file", "--batch"], env=self.env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        rows = {}
        try:
            for oid, kind in sorted(expected_objects.items()):
                child.stdin.write((oid + "\n").encode("ascii"))
                child.stdin.flush()
                header = child.stdout.readline().decode("ascii").rstrip("\n").split(" ")
                self.check(len(header) == 3 and header[0] == oid and header[1] == kind,
                           "native object header: " + oid, header, [oid, kind, "size"], fatal=True)
                size = int(header[2])
                self.check(size >= 0, "native object size: " + oid, fatal=True)
                gh = hashlib.sha1(kind.encode() + b" " + str(size).encode() + b"\0")
                sh = hashlib.sha256()
                remaining = size
                while remaining:
                    data = child.stdout.read(min(CHUNK, remaining))
                    self.check(bool(data), "complete native object stream: " + oid, fatal=True)
                    gh.update(data)
                    sh.update(data)
                    remaining -= len(data)
                self.check(child.stdout.read(1) == b"\n", "native object separator: " + oid, fatal=True)
                self.check(gh.hexdigest() == oid, "recomputed native object identity: " + oid,
                           gh.hexdigest(), oid)
                rows[oid] = {"kind": kind, "bytes": size, "sha256": sh.hexdigest()}
            child.stdin.close()
            stderr = child.stderr.read()
            code = child.wait(timeout=30)
            self.check(code == 0 and not stderr, "native reader completion",
                       {"returncode": code, "stderr": stderr.decode("utf-8", "replace")})
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=30)
        return rows

    def run(self):
        for label, value in (("ref", self.args.ref), ("baseline", self.args.baseline),
                             ("candidate", self.args.candidate)):
            self.check(HEX40.fullmatch(value) is not None,
                       "full explicit commit identity: " + label, value, fatal=True)
        self.check(self.args.baseline == BASELINE, "fixed C089 baseline", self.args.baseline, BASELINE, True)
        self.check(self.args.candidate == CANDIDATE, "fixed candidate A", self.args.candidate, CANDIDATE, True)
        self.check(self.git("rev-parse", "--show-object-format").stdout.strip() == b"sha1",
                   "native Git object format", fatal=True)
        top = Path(os.fsdecode(self.git("rev-parse", "--show-toplevel").stdout.rstrip(b"\n"))).resolve()
        self.check(top == self.repo, "exact repository root", str(top), str(self.repo), True)
        head_before = self.git("rev-parse", "HEAD").stdout.decode().strip()
        self.check(head_before == self.args.ref, "HEAD equals actual resulting main",
                   head_before, self.args.ref, True)
        for ancestor, label in ((BASELINE, "C089"), (CANDIDATE, "candidate A")):
            code = self.git("merge-base", "--is-ancestor", ancestor, self.args.ref,
                            allow_failure=True).returncode
            self.check(code == 0, label + " is ancestor of resulting main", code, 0)
        commit = self.git("cat-file", "commit", self.args.ref).stdout
        headers = commit.split(b"\n\n", 1)[0].split(b"\n")
        tree_oid = next(x[5:].decode() for x in headers if x.startswith(b"tree "))
        parents = [x[7:].decode() for x in headers if x.startswith(b"parent ")]
        self.result.update({"ref": self.args.ref, "tree": tree_oid, "parents": parents})
        self.check(len(parents) == 2, "actual result is a two-parent merge", parents)
        initial_status = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
        self.check(initial_status == b"", "initial worktree/index is clean",
                   initial_status.decode("utf-8", "replace"), "")

        all_entries = self.tree(self.args.ref, include_trees=True)
        current = {p: row for p, row in all_entries.items() if row["kind"] != "tree"}
        base = self.tree(BASELINE)
        candidate = self.tree(CANDIDATE)
        self.check(self.index() == current, "complete initial index equals resulting tree")
        modified_old = []
        for path, old in sorted(base.items()):
            self.check(path in current, "baseline file retained: " + path)
            if current.get(path) != old:
                modified_old.append(path)
                self.check(path in ALLOWED_OLD, "old file change allowed: " + path,
                           current.get(path), old)
        added = sorted(set(current) - set(base))
        for path in added:
            self.check(path.startswith(ALLOWED_NEW), "new path within approved scope: " + path)
        self.result["scope"].update({"baseline_files": len(base), "modified_old_paths": modified_old,
                                     "added_paths": added})

        manifest_bytes = self.git("show", CANDIDATE + ":" + MANIFEST).stdout
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
        self.check(manifest_hash == MANIFEST_SHA256, "fixed independently reviewed input manifest",
                   manifest_hash, MANIFEST_SHA256, True)
        manifest = json.loads(manifest_bytes)
        frozen = manifest["files"]
        self.check(len(frozen) == manifest["file_count"] == 399, "exact frozen file count")
        self.check(sum(row["bytes"] for row in frozen) == manifest["total_bytes"] == 12256793,
                   "exact frozen byte total")
        self.check(len({row["path"] for row in frozen}) == len(frozen), "unique frozen input paths")
        for path in [MANIFEST, ADOPTION] + [row["path"] for row in frozen]:
            self.check(path in candidate and current.get(path) == candidate.get(path),
                       "frozen native identity/mode equals candidate A: " + path,
                       current.get(path), candidate.get(path))

        source_rows = []
        for path, row in sorted(current.items()):
            self.check(row["kind"] == "blob", "tracked source is native blob: " + path,
                       row["kind"], "blob", True)
            source_rows.append(self.worktree_file(path, row))
        self.result["source_inventory"] = source_rows
        source_by_path = {row["path"]: row for row in source_rows}
        expected_objects = {row["oid"]: row["kind"] for row in all_entries.values()}
        expected_objects[tree_oid] = "tree"
        for oid in (self.args.ref, BASELINE, CANDIDATE):
            expected_objects[oid] = "commit"
        native = self.native_objects(expected_objects)
        for row in source_rows:
            item = native[current[row["path"]]["oid"]]
            self.check((item["bytes"], item["sha256"]) == (row["bytes"], row["sha256"]),
                       "complete worktree/native byte equality: " + row["path"])
        for expected in frozen:
            actual = source_by_path[expected["path"]]
            self.check(all(actual[key] == expected[key] for key in ("mode", "bytes", "sha256", "git_blob_sha1")),
                       "complete frozen manifest row: " + expected["path"], actual, expected)
        self.result["frozen_authority"] = {
            "manifest_sha256": source_by_path[MANIFEST]["sha256"],
            "adoption_sha256": source_by_path[ADOPTION]["sha256"],
            "file_count": len(frozen), "bytes": sum(x["bytes"] for x in frozen),
            "all_399_plus_manifest_and_adoption_equal_candidate_A": not any(
                failure["check"].startswith("frozen native") or failure["check"].startswith("complete frozen")
                for failure in self.result["failures"]),
        }
        self.result["source_files"] = len(source_rows)
        self.result["source_bytes"] = sum(row["bytes"] for row in source_rows)
        self.result["native_objects_verified"] = len(native)
        self.result["native_object_kinds"] = {
            kind: sum(row["kind"] == kind for row in native.values())
            for kind in ("blob", "tree", "commit")
        }
        self.result["native_inventory_sha256"] = hashlib.sha256(
            json.dumps(native, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.check(self.git("rev-parse", "HEAD").stdout.decode().strip() == self.args.ref,
                   "HEAD unchanged after all reads")
        self.check(self.index() == current, "complete final index equals resulting tree")
        final_status = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
        self.check(final_status == b"", "final worktree/index is clean",
                   final_status.decode("utf-8", "replace"), "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--ref", required=True, help="Actual resulting-main merge commit, full SHA-1")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True, help="Fresh JSON receipt outside the repository")
    args = parser.parse_args()
    audit = Audit(args)
    output = Path(args.output)
    output = output.parent.resolve(strict=True) / output.name
    if output == audit.repo or audit.repo in output.parents:
        parser.error("Output must be outside the audited repository")
    try:
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        parser.error("Output already exists; use a separately named fresh receipt")
    try:
        audit.run()
    except Exception as exc:
        audit.result["failures"].append({"check": "audit completed", "exception_type": type(exc).__name__,
                                          "message": str(exc)})
    audit.result["status"] = "failed" if audit.result["failures"] else "passed"
    audit.result["finished_utc"] = utc()
    audit.result["elapsed_seconds"] = round(time.monotonic() - audit.started, 6)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(audit.result, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    summary = {key: audit.result.get(key) for key in (
        "status", "ref", "tree", "checks", "source_files", "source_bytes",
        "native_objects_verified", "elapsed_seconds",
    )}
    summary.update({"failures": audit.result["failures"], "output": str(output),
                    "receipt_sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if audit.result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
