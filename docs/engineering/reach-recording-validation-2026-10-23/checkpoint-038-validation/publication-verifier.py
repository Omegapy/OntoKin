"""Bind a prepared C038 tree to its actual remote Git commit and local checkout."""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import subprocess


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def object_hash(kind, raw):
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def exact_commit(commit):
    require(commit.get("verification", {}).get("signature") is None, "Signed commit requires original signed bytes")
    def identity(role, offset):
        row = commit[role]
        stamp = int(datetime.fromisoformat(row["date"].replace("Z", "+00:00")).timestamp())
        require(all("\n" not in row[k] for k in ("name", "email")), "Invalid identity")
        return f"{role} {row['name']} <{row['email']}> {stamp} {offset}"
    offsets = ["-0600", "+0000"]
    for minutes in range(-12 * 60, 14 * 60 + 1, 15):
        sign = "+" if minutes >= 0 else "-"
        magnitude = abs(minutes)
        value = f"{sign}{magnitude // 60:02d}{magnitude % 60:02d}"
        if value not in offsets:
            offsets.append(value)
    pairs = [(x, x) for x in offsets]
    pairs.extend((a, c) for a, c in itertools.product(offsets, repeat=2) if a != c)
    prefix = ["tree " + commit["tree"]["sha"], *["parent " + p["sha"] for p in commit["parents"]]]
    for a, c in pairs:
        head = "\n".join([*prefix, identity("author", a), identity("committer", c)]) + "\n\n"
        for suffix in ("", "\n"):
            raw = (head + commit["message"] + suffix).encode()
            if object_hash("commit", raw) == commit["sha"]:
                return raw, {"author_offset": a, "committer_offset": c, "added_trailing_newline": bool(suffix)}
    raise ValueError("Unable to reconstruct exact original commit; no object or ref written")


parser = argparse.ArgumentParser(description=__doc__)
for name in ("root", "plan", "remote-tree", "remote-commit", "receipt", "raw-commit"):
    parser.add_argument("--" + name, type=Path, required=True)
args = parser.parse_args()
root = args.root.resolve()
def git(*values, input=None):
    return subprocess.check_output(["git", "-C", str(root), *values], input=input)
plan = json.loads(args.plan.read_text())
tree = json.loads(args.remote_tree.read_text())
commit = json.loads(args.remote_commit.read_text())
require(not args.receipt.exists() and not args.raw_commit.exists(), "Output paths must be fresh")
require(git("rev-parse", "HEAD").decode().strip() == plan["parent_commit"], "Local head changed")
require(git("branch", "--show-current").decode().strip() == plan["branch"], "Not owned branch")
require(not git("diff", "--name-only").strip(), "Unstaged tracked edits")
require(not git("ls-files", "--others", "--exclude-standard").strip(), "Unstaged new files")
require(tree["truncated"] is False and tree["sha"] == plan["expected_tree"], "Remote tree identity")
require(commit["tree"]["sha"] == tree["sha"] and [p["sha"] for p in commit["parents"]] == [plan["parent_commit"]], "Commit ancestry/tree")
require(git("write-tree").decode().strip() == tree["sha"], "Local staged tree differs")
entries = {e["path"]: e for e in tree["tree"] if e["type"] == "blob"}
paths = set(filter(None, git("ls-files", "-z").decode().split("\0")))
require(paths == set(entries), "Full remote/local membership differs")
total = 0
for name in sorted(paths):
    path, expected = root / name, entries[name]
    require(path.is_file() and not path.is_symlink(), "Nonregular tracked input: " + name)
    raw = path.read_bytes()
    mode = "100755" if path.stat().st_mode & 0o111 else "100644"
    require(len(raw) == expected["size"] and object_hash("blob", raw) == expected["sha"] and mode == expected["mode"], "Remote file differs: " + name)
    total += len(raw)
for item in plan["files"]:
    raw = (root / item["path"]).read_bytes()
    require(sha(raw) == item["sha256"] and entries[item["path"]]["sha"] == item["git_blob"], "Prepared file differs")
changes = [line.split("\t", 1) for line in git("diff", "--cached", "--name-status").decode().splitlines()]
require(all(status == "A" for status, name in changes) and {name for status, name in changes} == {f["path"] for f in plan["files"]}, "Only planned additions permitted")
raw_commit, format_info = exact_commit(commit)
actual = git("hash-object", "-t", "commit", "-w", "--stdin", input=raw_commit).decode().strip()
require(actual == commit["sha"], "Original object differs after write")
require(git("cat-file", "commit", actual) == raw_commit, "Original object readback differs")
git("update-ref", "refs/heads/" + plan["branch"], actual, plan["parent_commit"])
git("remote", "set-url", "origin", "https://github.com/Omegapy/OntoKin.git")
require(not git("status", "--porcelain=v1", "--untracked-files=all").strip(), "Published local checkout not clean")
args.raw_commit.write_bytes(raw_commit)
record = {"schema": "ontokin.checkpoint038-publication-verification/0.1", "status": "passed",
          "verified_at": datetime.now(timezone.utc).isoformat(), "commit": actual, "tree": tree["sha"],
          "parent": plan["parent_commit"], "branch": plan["branch"], "new_files": len(plan["files"]),
          "new_bytes": sum(f["bytes"] for f in plan["files"]), "new_file_records": plan["files"],
          "all_tracked_files": len(paths), "all_tracked_bytes": total, "remote_tree_complete": True,
          "all_remote_blobs_modes_and_sizes_match": True, "all_prepared_sha256_match": True,
          "only_planned_additions": True, "exact_original_commit_reconstructed": True,
          "original_commit_sha256": sha(raw_commit), "commit_format": format_info,
          "local_head_exact": True, "local_clean": True, "verifier_sha256": sha(Path(__file__).read_bytes()),
          "remote_ref_update": "Separately performed with observed expected parent and force=false",
          "product_or_tests_executed": False, "release_acceptance": False}
with args.receipt.open("x") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({k: record[k] for k in ("status", "commit", "tree", "new_files", "all_tracked_files", "all_tracked_bytes", "commit_format", "local_clean")}))
