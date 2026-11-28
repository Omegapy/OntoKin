"""Read-only, synthetic: time the parent proof's document work for an inventory of the real tree's size.

Usage: python3 -I -S -B parent_proof_timing.py <index-scope json> <index file> <output json>
It takes the copied set's paths from the measured workspace's index (parsed directly, no Git start),
builds a driver-shaped inventory with synthetic digests, and times what each derived selection does
with the two recorded documents: canonical encoding, JSON parsing twice, SHA-256 of the bytes, the
generated-example filter and a case-folded name set. It reads no copied file.
"""
import hashlib
import json
import sys
import time

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
from index_scope import entries  # noqa: E402


def main():
    scope_path, index, output = sys.argv[1:4]
    scope = json.load(open(scope_path))
    outside = {row["path"] for row in scope["outside_copied_set"]}
    _, _, rows, _ = entries(index)
    files = [{"path": row["path"], "sha256": "sha256:" + hashlib.sha256(row["path"].encode()).hexdigest(), "bytes": 1000}
             for row in rows if row["path"] not in outside]
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    record = {"sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(), "file_count": len(files), "files": files}
    document = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    times = []
    for _ in range(5):
        started = time.perf_counter()
        for _ in range(2):  # source_before and workspace_inventory
            hashlib.sha256(document).hexdigest()
            parsed = json.loads(document.decode("utf-8"))
            hashlib.sha256(document).hexdigest()
        kept = [item for item in parsed["files"] if not item["path"].startswith(("examples/visual/", "examples/agent/", "examples/construction/"))]
        hashlib.sha256(json.dumps(kept, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        folded = {item["path"].casefold() for item in parsed["files"]}
        times.append(round(time.perf_counter() - started, 4))
    report = {"records": len(files), "document_bytes": len(document), "seconds": times, "folded_names": len(folded),
              "note": "synthetic digests; the real tree's paths; no copied file is read"}
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=1)
        stream.write("\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
