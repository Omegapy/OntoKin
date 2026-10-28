#!/usr/bin/env python3
"""Validate the actual published C047 source and archive without a product rerun."""
import datetime
import hashlib
import json
import pathlib
import platform
import subprocess
import sys
import time

BASE = pathlib.Path(__file__).resolve().parents[1]
ROOT = BASE / "OntoKin"
OUT = pathlib.Path(__file__).resolve().parent
PUB = BASE / "c047-publication"
DOC = ROOT / "docs/engineering/reach-recording-validation-2026-10-23"
EXPECTED = json.loads((PUB / "core-remote-tree.json").read_text())
COMMIT = json.loads((PUB / "core-remote-commit.json").read_text())["sha"]

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def inputs():
    assert git("rev-parse", "HEAD") == COMMIT
    assert git("rev-parse", "HEAD^{tree}") == EXPECTED["sha"]
    assert git("status", "--porcelain") == ""
    records = []
    expected = {row["path"]: row for row in EXPECTED["tree"] if row["type"] == "blob"}
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")[:-1]
    assert set(tracked) == set(expected)
    for name in sorted(expected):
        path = ROOT / name
        raw = path.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        assert not path.is_symlink() and (blob, mode, len(raw)) == (expected[name]["sha"], expected[name]["mode"], expected[name]["size"])
        records.append({"path": name, "bytes": len(raw), "sha256": sha(raw), "git_blob": blob, "mode": mode})
    return records

def main():
    window = json.loads((PUB / "window.json").read_text())
    started = now()
    assert datetime.datetime.fromisoformat(window["active_after"]) <= datetime.datetime.fromisoformat(started) < datetime.datetime.fromisoformat(window["expires_at"])
    before = inputs()
    write(OUT / "inputs-before.json", before)
    command = [sys.executable, "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"]
    receipt = {"command": command, "cwd": str(ROOT), "source_commit": COMMIT, "source_tree": EXPECTED["sha"], "started_at": now(), "python": sys.version, "executable": sys.executable, "platform": platform.platform(), "window": window}
    monotonic = time.monotonic()
    with (OUT / "documentation.stdout").open("xb") as out, (OUT / "documentation.stderr").open("xb") as err:
        completed = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err, check=False)
    receipt.update(finished_at=now(), wall_seconds=time.monotonic()-monotonic, exit_code=completed.returncode)
    for name in ("documentation.stdout", "documentation.stderr"):
        raw = (OUT / name).read_bytes()
        receipt[name] = {"bytes": len(raw), "sha256": sha(raw)}
    write(OUT / "documentation-command.json", receipt)
    checks = []
    def check(ok, label):
        assert ok, label
        checks.append(label)
    check(completed.returncode == 0, "unchanged documentation checker passed")
    summary = json.loads((DOC / "checkpoint-047.json").read_text())
    manifest_raw = (DOC / "checkpoint-047-evidence-manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    check(sha(manifest_raw) == summary["manifest_sha256"], "member manifest binding")
    parts = summary["archive"]["parts"]
    chunks = []
    for part in parts:
        raw = (DOC / part["path"]).read_bytes()
        check(len(raw) == part["bytes"] and sha(raw) == part["sha256"], "archive part " + part["path"])
        chunks.append(raw)
    joined = b"".join(chunks)
    check(len(joined) == summary["archive"]["bytes"] and sha(joined) == summary["archive"]["sha256"], "joined archive binding")
    restored = BASE / "c047-roundtrip"
    members = {row["path"]: row for row in manifest["members"]}
    actual = {str(path.relative_to(restored)) for path in restored.rglob("*") if path.is_file()}
    check(actual == set(members) and len(members) == summary["archive"]["member_count"], "complete restored membership")
    for name, row in members.items():
        path = restored / name
        raw = path.read_bytes()
        assert not path.is_symlink() and len(raw) == row["bytes"] and sha(raw) == row["sha256"], name
    checks.append("all 414 restored member bytes and hashes")
    restore = json.loads((PUB / "restore-receipt.json").read_text())
    check(restore["status"] == "passed" and restore["archive_sha256"] == sha(joined) and restore["zip_crc"] == "passed", "prior exact-byte CRC/extraction receipt applies to unchanged published archive")
    for row in manifest["members"]:
        if row["path"].startswith("c047-lifetime-review/"):
            rel = row["path"].removeprefix("c047-lifetime-review/")
            check(sha((DOC / "checkpoint-047-lifetime-review" / rel).read_bytes()) == row["sha256"], "direct lifetime review copy " + rel)
    review_index = json.loads((DOC / "checkpoint-047-reviews.json").read_text())
    for review in review_index["reviews"]:
        for row in review["members"]:
            recorded = members[row["archive_path"]]
            check((recorded["bytes"], recorded["sha256"]) == (row["bytes"], row["sha256"]), "review binding " + row["archive_path"])
    check(summary["pair"]["expected_failed_exits"] == [1,1] and not summary["pair"]["elapsed_neutrality"] and not summary["accepted_artifact"] and not summary["runtime_candidate_selected"] and summary["original28"]["passed"] == 24, "failed-product and limited-scope claims preserved")
    parent = {row["path"]: row for row in json.loads((BASE / "c047-recovery/remote-tree.json").read_text())["tree"] if row["type"] == "blob"}
    current = {row["path"]: row for row in EXPECTED["tree"] if row["type"] == "blob"}
    check(all(all(current[name][k] == row[k] for k in ("sha","mode","size")) for name,row in parent.items()), "all 2556 parent files preserved")
    check(len(current)-len(parent) == 40, "exactly 40 core additions")
    after = inputs()
    write(OUT / "inputs-after.json", after)
    check(before == after, "complete core inputs stable")
    finished = now()
    check(datetime.datetime.fromisoformat(finished) < datetime.datetime.fromisoformat(window["expires_at"]), "actual completion within active window")
    result = {"schema": "ontokin.checkpoint047-published-core-validation/0.1", "status": "passed", "source_commit": COMMIT, "source_tree": EXPECTED["sha"], "started_at": started, "finished_at": finished, "python": sys.version, "platform": platform.platform(), "window": window, "files": len(before), "bytes": sum(x["bytes"] for x in before), "checks_passed": len(checks), "checks": checks, "documentation_exit": completed.returncode, "inputs_stable": True, "archive_members": len(members), "archive_member_bytes": sum(x["bytes"] for x in members.values()), "product_rerun": False, "release_acceptance": False}
    write(OUT / "result.json", result)
    print(json.dumps({key: result[key] for key in ("status", "source_commit", "files", "bytes", "checks_passed", "documentation_exit", "inputs_stable", "archive_members")}))

if __name__ == "__main__":
    main()
