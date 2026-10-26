#!/usr/bin/env python3
"""Read back the immutable C047 additions without exposing download credentials."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import sys
import urllib.request

BASE = pathlib.Path(__file__).resolve().parents[1]
ROOT = BASE / "OntoKin"
OUT = pathlib.Path(__file__).resolve().parent
PRIVATE = OUT / "core-download-items.private.json"

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def main():
    started = now()
    plan = json.loads((OUT / "core-plan.json").read_text())
    before = json.loads((BASE / "c047-recovery/remote-tree.json").read_text())
    after = json.loads((OUT / "core-remote-tree.json").read_text())
    commit = json.loads((OUT / "core-remote-commit.json").read_text())
    window = json.loads((OUT / "window.json").read_text())
    assert datetime.datetime.fromisoformat(window["active_after"]) <= datetime.datetime.now(datetime.timezone.utc) < datetime.datetime.fromisoformat(window["expires_at"])
    assert commit["tree"]["sha"] == after["sha"] == plan["tree"]
    assert [x["sha"] for x in commit["parents"]] == [plan["parent"]]
    assert before["truncated"] is False and after["truncated"] is False
    old = {x["path"]: x for x in before["tree"] if x["type"] == "blob"}
    current = {x["path"]: x for x in after["tree"] if x["type"] == "blob"}
    new = {x["path"]: x for x in plan["files"]}
    assert set(current) == set(old) | set(new) and not set(old) & set(new)
    for name, row in old.items():
        assert all(row[k] == current[name][k] for k in ("sha", "mode", "size", "type"))
    for name, row in new.items():
        assert (row["sha"], row["mode"], row["bytes"]) == (current[name]["sha"], current[name]["mode"], current[name]["size"])
    items = json.loads(PRIVATE.read_text())
    assert len(items) == len(new) and {x["path"] for x in items} == set(new)
    def one(item):
        result = {"path": item["path"], "started_at": now()}
        try:
            request = urllib.request.Request(item["download_url"], headers={"User-Agent": "OntoKin-C047-immutable-readback"})
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read()
            local = (ROOT / item["path"]).read_bytes()
            assert data == local and len(data) == item["bytes"] and blob(data) == item["sha"]
            result.update(status="passed", bytes=len(data), git_blob=blob(data), sha256=hashlib.sha256(data).hexdigest(), remote_bytes_equal=True)
        except Exception as error:
            result.update(status="failed", error_type=type(error).__name__, http_status=getattr(error, "code", None), error_detail="redacted; no authenticated URL retained")
        result["finished_at"] = now()
        return result
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(one, items))
    finally:
        PRIVATE.unlink()
    local_records = []
    for name, row in sorted(current.items()):
        path = ROOT / name
        data = path.read_bytes()
        mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        assert not path.is_symlink() and (blob(data), len(data), mode) == (row["sha"], row["size"], row["mode"])
        local_records.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "git_blob": row["sha"], "mode": mode})
    finished = now()
    assert datetime.datetime.fromisoformat(finished) < datetime.datetime.fromisoformat(window["expires_at"])
    result = {"schema": "ontokin.c047-immutable-core-readback/0.1", "status": "passed" if all(x["status"] == "passed" for x in rows) else "failed", "started_at": started, "finished_at": finished, "core_commit": commit["sha"], "core_tree": plan["tree"], "preserved_parent_files": len(old), "added_files": len(new), "all_local_files": len(local_records), "all_local_bytes": sum(x["bytes"] for x in local_records), "remote_added_file_readbacks": rows, "all_local_file_bindings": local_records, "temporary_authenticated_manifest_deleted": not PRIVATE.exists(), "product_execution": False}
    (OUT / "core-remote-byte-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "core_commit", "core_tree", "preserved_parent_files", "added_files", "all_local_files", "all_local_bytes", "temporary_authenticated_manifest_deleted")}))
    return 0 if result["status"] == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())
