"""Authenticate and privately restore adopted inert evidence; no product import."""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys


SOURCE_REVISION = "79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae"
MANIFEST_SHA256 = "e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de"
EXPECTATIONS_SHA256 = "dfb285f41a58a1f7254aaae4aa022f91afdc72fb7d5dad2f3d6b1e8257d14137"
FIXTURE_MANIFEST_SHA256 = "ea377d25e96631b70cd8909a5375fa3fd0feadf7f017f0673d8a094335186594"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "OntoKin"
SOURCE = REPO / "docs/engineering/localized-repair-c271/loader-path-p11"
DEST = HERE / "materialized" / "loader-path-p11"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(name):
    p = PurePosixPath(name)
    assert isinstance(name, str) and name and not p.is_absolute()
    assert str(p) == name and all(x not in ("", ".", "..") for x in p.parts)
    return p


def read_source(name):
    p = SOURCE / safe(name)
    for ancestor in (p, *p.parents):
        assert not ancestor.is_symlink(), str(ancestor)
    s = p.stat()
    assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1, str(p)
    return p.read_bytes()


def verify(raw, row):
    assert len(raw) == row["size_bytes"] and digest(raw) == row["sha256"], row["path"]


def main():
    manifest_raw = read_source("design/candidate004/CANDIDATE-MANIFEST.json")
    assert digest(manifest_raw) == MANIFEST_SHA256
    manifest = json.loads(manifest_raw)
    transport_raw = read_source("GIT-TRANSPORT.json")
    transport = json.loads(transport_raw)
    decoded, transport_receipts = {}, []
    for row in transport["records"]:
        name = str(safe(row["materialized_relative_path"]))
        envelope_raw = read_source(row["envelope_relative_path"])
        assert digest(envelope_raw) == row["envelope_sha256"]
        envelope = json.loads(envelope_raw)
        assert set(envelope) == {"schema", "encoding", "decoded_size_bytes", "decoded_sha256", "content_base64"}
        assert envelope["schema"] == "ontokin.lossless-evidence-envelope/1" and envelope["encoding"] == "base64"
        raw = base64.b64decode(envelope["content_base64"], validate=True)
        assert len(raw) == envelope["decoded_size_bytes"] == row["decoded_size_bytes"]
        assert digest(raw) == envelope["decoded_sha256"] == row["decoded_sha256"]
        assert name not in decoded
        decoded[name] = (raw, row["materialized_mode"])
        transport_receipts.append({k: row[k] for k in row if k != "unaltered_original_recovery_path"})

    candidate_diff = decoded["design/candidate004/REVISION-004.diff"][0]
    assert candidate_diff == decoded["review/candidate004/INDEPENDENT-DOCUMENT-DIFF.diff"][0]
    independent = json.loads(read_source("review/candidate004/CHECKS.json"))
    assert any(row.get("check") == "payload/REVISION-004.diff: exact binding" and row.get("pass") is True
               and row["detail"]["actual"]["sha256"] == digest(candidate_diff)
               and row["detail"]["actual"]["size_bytes"] == len(candidate_diff)
               for row in independent)

    payload = {}
    for row in manifest["payload"]:
        name = "design/candidate004/" + str(safe(row["path"]))
        assert name not in payload
        raw = decoded[name][0] if name in decoded else read_source(name)
        verify(raw, row)
        assert row["mode"] in ("0o600", "0o644")
        if name.endswith(".bin"):
            assert row["mode"] == "0o600"
        payload[name] = (raw, row["mode"])
    assert digest(payload["design/candidate004/EXPECTATIONS.json"][0]) == EXPECTATIONS_SHA256
    assert digest(payload["design/candidate004/FIXTURE-MANIFEST.json"][0]) == FIXTURE_MANIFEST_SHA256
    payload["design/candidate004/CANDIDATE-MANIFEST.json"] = (manifest_raw, "0o644")
    for row in manifest["supporting_files"]:
        assert row["path"].startswith("../") and not row["path"].startswith("../../")
        name = "design/" + str(safe(row["path"][3:]))
        assert name not in payload
        raw = read_source(name)
        verify(raw, row)
        mode = row.get("mode", "0o644")
        assert mode in ("0o600", "0o644")
        payload[name] = (raw, mode)
    for name, value in decoded.items():
        if name in payload:
            assert payload[name] == value
        else:
            payload[name] = value

    DEST.parent.mkdir(mode=0o700, exist_ok=True)
    DEST.mkdir(mode=0o700)
    receipts = []
    for name, (raw, mode) in sorted(payload.items()):
        p = DEST / safe(name)
        p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        for parent in (p.parent, *p.parent.parents):
            assert not parent.is_symlink()
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, int(mode, 8))
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            p.chmod(int(mode, 8))
        except BaseException:
            raise
        info = p.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
        assert oct(stat.S_IMODE(info.st_mode)) == mode and p.read_bytes() == raw
        receipts.append({"path": name, "size_bytes": len(raw), "sha256": digest(raw), "mode": mode})

    fixtures = json.loads(payload["design/candidate004/FIXTURE-MANIFEST.json"][0])
    expectations = json.loads(payload["design/candidate004/EXPECTATIONS.json"][0])
    assert len(fixtures["cases"]) == 97 and len(fixtures["files"]) == 131
    assert {row["id"] for row in fixtures["cases"]} == set(expectations["cases"])
    for row in fixtures["files"]:
        raw, mode = payload["design/candidate004/" + row["path"]]
        verify(raw, row)
        assert mode == row["mode"]
    receipt = {"schema": "ontokin.c271.p12-materialization/1", "passed": True,
               "source_revision": SOURCE_REVISION, "source": str(SOURCE), "destination": str(DEST),
               "manifest_sha256": MANIFEST_SHA256, "expectations_sha256": EXPECTATIONS_SHA256,
               "fixture_manifest_sha256": FIXTURE_MANIFEST_SHA256,
               "transport_mapping_sha256": digest(transport_raw), "transport": transport_receipts,
               "files": receipts, "copied_files": len(receipts), "controls": 97, "fixtures": 131,
               "source_bytes_changed": False, "product_imported": False, "product_tests_run": False,
               "support_mode_note": "Manifest-specified modes restored; older supporting rows without mode use inert 0o644."}
    with (HERE / "MATERIALIZATION-RECEIPT.json").open("x") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"passed": True, "copied_files": len(receipts), "controls": 97, "fixtures": 131, "destination": str(DEST)}))


if __name__ == "__main__":
    main()
