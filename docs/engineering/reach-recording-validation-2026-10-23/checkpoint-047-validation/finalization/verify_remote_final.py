#!/usr/bin/env python3
"""Verify immutable final additions and preserved core; never execute product code."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import urllib.request

BASE = pathlib.Path(__file__).resolve().parents[1]
ROOT = BASE / "OntoKin"
OUT = pathlib.Path(__file__).resolve().parent
PRIVATE = OUT / "final-download-items.private.json"

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def read(path):
    return json.loads(path.read_text())

def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def main():
    started = now()
    plan = read(OUT / "final-plan.json")
    before = read(BASE / "c047-publication/core-remote-tree.json")
    after = read(OUT / "final-remote-tree.json")
    commit = read(OUT / "final-remote-commit.json")
    window = read(OUT / "window.json")
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
    items = read(PRIVATE)
    assert len(items) == len(new) and {x["path"] for x in items} == set(new)
    def one(item):
        result = {"path": item["path"], "started_at": now()}
        try:
            request = urllib.request.Request(item["download_url"], headers={"User-Agent": "OntoKin-C047-final-immutable-readback"})
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
    result = {"schema": "ontokin.c047-final-immutable-readback/0.1", "status": "passed" if all(x["status"] == "passed" for x in rows) else "failed", "started_at": started, "finished_at": finished, "final_commit": commit["sha"], "final_tree": plan["tree"], "preserved_core_files": len(old), "added_files": len(new), "all_local_files": len(local_records), "all_local_bytes": sum(x["bytes"] for x in local_records), "remote_added_file_readbacks": rows, "all_local_file_bindings": local_records, "temporary_authenticated_manifest_deleted": not PRIVATE.exists(), "product_execution": False, "review_scope": "Root publication metadata and exact bytes. Independent audit applies to preserved core only."}
    (OUT / "final-remote-byte-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "final_commit", "final_tree", "preserved_core_files", "added_files", "all_local_files", "all_local_bytes", "temporary_authenticated_manifest_deleted")}))
    return 0 if result["status"] == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())
