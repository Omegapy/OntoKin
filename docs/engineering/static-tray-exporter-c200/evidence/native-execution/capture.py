"""Capture a completed C200 cohort without launching any validation process.

The caller must supply the terminal driver receipt. This helper preserves actual
runtime files, including partial failures, and verifies archive bytes. It does
not qualify geometry, infer success from archive integrity, or run native code.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tarfile


MAX_FILES = 20000
MAX_BYTES = 2 * 1024 ** 3
REVISION = "OK-QUAL-STATIC-TRAY-C200/0.1.0"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def binding(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Required receipt is not a regular nonsymlink file: " + str(path))
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def metadata(path):
    info = path.lstat()
    if stat.S_ISREG(info.st_mode):
        kind = "file"
    elif stat.S_ISDIR(info.st_mode):
        kind = "directory"
    elif stat.S_ISLNK(info.st_mode):
        kind = "symlink"
    else:
        raise ValueError("Unsupported runtime entry must be investigated before capture: " + str(path))
    row = {"type": kind, "mode": oct(stat.S_IMODE(info.st_mode)), "size_bytes": info.st_size,
           "mtime_ns": info.st_mtime_ns, "ctime_ns": info.st_ctime_ns,
           "device": info.st_dev, "inode": info.st_ino, "hardlink_count": info.st_nlink,
           "uid": info.st_uid, "gid": info.st_gid}
    if kind == "symlink":
        row["linkname"] = os.readlink(path)
    return row


def enumerate_sources(sources):
    found = {}

    def visit(path, archive_path):
        key = PurePosixPath(archive_path).as_posix()
        if PurePosixPath(key).is_absolute() or ".." in PurePosixPath(key).parts or key in found:
            raise ValueError("Unsafe or duplicate capture path: " + key)
        row = metadata(path)
        found[key] = {"source_path": str(path), **row}
        if len(found) > MAX_FILES:
            raise ValueError("Capture exceeds the bounded file-count ceiling")
        if row["type"] == "directory":
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                visit(child, key + "/" + child.name)

    for label, path in sources:
        visit(path, label)
    if sum(row["size_bytes"] for row in found.values() if row["type"] == "file") > MAX_BYTES:
        raise ValueError("Capture exceeds the bounded expanded-byte ceiling")
    return found


def active_commands(locked_paths):
    """Observe Linux command lines; do not signal or launch any process."""
    active = []
    inaccessible = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal() or int(entry.name) == os.getpid():
            continue
        try:
            argv = (entry / "cmdline").read_bytes().split(b"\0")
        except FileNotFoundError:
            continue
        except PermissionError:
            inaccessible.append(int(entry.name))
            continue
        text = [part.decode("utf-8", "surrogateescape") for part in argv if part]
        if any(path in text for path in locked_paths):
            active.append({"pid": int(entry.name), "argv": text})
    if active:
        raise ValueError("Relevant coordinator/native/checker command is still present: " + json.dumps(active))
    if inaccessible:
        raise ValueError("Cannot establish stopped commands because /proc entries are unreadable: " + repr(inaccessible))
    return {"matching_commands": active, "unreadable_processes": inaccessible,
            "observation": "No current /proc command line contained an exact locked coordinator, worker, receiver or Node probe path"}


class HashingReader:
    def __init__(self, stream):
        self.stream = stream
        self.hash = hashlib.sha256()
        self.bytes = 0

    def read(self, size=-1):
        data = self.stream.read(size)
        self.hash.update(data)
        self.bytes += len(data)
        return data


def write_archive(path, snapshot):
    captured = {}
    with path.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for name, row in snapshot.items():
                    source = Path(row["source_path"])
                    if metadata(source) != {key: value for key, value in row.items() if key != "source_path"}:
                        raise ValueError("Source changed before it was archived: " + str(source))
                    member = tarfile.TarInfo(name)
                    member.mode = int(row["mode"], 8)
                    member.uid, member.gid = row["uid"], row["gid"]
                    member.mtime = row["mtime_ns"] // 1_000_000_000
                    member.pax_headers = {"mtime": str(row["mtime_ns"] // 1_000_000_000) + "." +
                                          str(row["mtime_ns"] % 1_000_000_000).zfill(9)}
                    result = dict(row)
                    result["archive_size_bytes"] = row["size_bytes"] if row["type"] == "file" else 0
                    if row["type"] == "directory":
                        member.type = tarfile.DIRTYPE
                        archive.addfile(member)
                    elif row["type"] == "symlink":
                        member.type = tarfile.SYMTYPE
                        member.linkname = row["linkname"]
                        archive.addfile(member)
                    else:
                        member.type, member.size = tarfile.REGTYPE, row["size_bytes"]
                        with source.open("rb") as stream:
                            reader = HashingReader(stream)
                            archive.addfile(member, reader)
                        if reader.bytes != row["size_bytes"]:
                            raise ValueError("Short source payload during capture: " + str(source))
                        result["sha256"] = reader.hash.hexdigest()
                    if metadata(source) != {key: value for key, value in row.items() if key != "source_path"}:
                        raise ValueError("Source changed during capture: " + str(source))
                    captured[name] = result
        raw.flush()
        os.fsync(raw.fileno())
    return captured


def verify_archive(path, captured):
    seen = set()
    regular = 0
    verified_bytes = 0
    with tarfile.open(path, mode="r|gz") as archive:
        for member in archive:
            name = member.name.rstrip("/")
            if name in seen or name not in captured:
                raise ValueError("Unexpected or duplicate archive member: " + name)
            seen.add(name)
            row = captured[name]
            if member.mode != int(row["mode"], 8):
                raise ValueError("Archive mode differs: " + name)
            if row["type"] == "directory":
                if not member.isdir(): raise ValueError("Archive directory type differs: " + name)
            elif row["type"] == "symlink":
                if not member.issym() or member.linkname != row["linkname"]:
                    raise ValueError("Archive symbolic link differs: " + name)
            else:
                if not member.isfile() or member.size != row["size_bytes"]:
                    raise ValueError("Archive file type or length differs: " + name)
                with archive.extractfile(member) as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if actual != row["sha256"]:
                    raise ValueError("Archive payload digest differs: " + name)
                regular += 1
                verified_bytes += member.size
    if seen != set(captured):
        raise ValueError("Archive omitted captured paths")
    return {"passed": True, "members": len(seen), "regular_files": regular,
            "regular_payload_bytes": verified_bytes, "all_payloads_rehashed_from_archive": True}


def useful_receipt(name, row):
    if row["type"] != "file":
        return False
    path = PurePosixPath(name)
    if path.suffix not in {".json", ".jsonl", ".log", ".txt"}:
        return False
    if name.startswith(("c200-driver/", "c200-coordinator/", "c200-native/results/",
                        "c200-native/external-readback/", "c200-native/delivered-controls/")):
        return True
    return path.name in {"attempts.jsonl", "qualification-result.json", "native-startup.json", "native-result.json",
                         "observations.json", "receiving-check.json", "independent-audit.json", "equality-checks.json",
                         "closure.json", "state.json", "construction.process.json", "receiving.process.json",
                         "construction.stdout.log", "construction.stderr.log", "receiving.stdout.log", "receiving.stderr.log"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--expected-lock-sha256", required=True)
    parser.add_argument("--driver-directory", required=True)
    parser.add_argument("--terminal-marker", required=True)
    parser.add_argument("--terminal-field", choices=("returncode", "return_code", "exit_code"), required=True)
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    repo, lock_path = Path(args.repo).resolve(), Path(args.lock).resolve()
    driver, terminal = Path(args.driver_directory).resolve(), Path(args.terminal_marker).resolve()
    destination = Path(args.destination).resolve()
    if destination.exists():
        raise ValueError("Capture destination must be new; preserve earlier captures")
    if not driver.is_dir() or not terminal.is_relative_to(driver):
        raise ValueError("Terminal marker must belong to the identified completed driver directory")
    terminal_binding = binding(terminal)
    completed = json.loads(terminal.read_bytes())
    if type(completed.get(args.terminal_field)) is not int:
        raise ValueError("Driver terminal marker lacks its actual integer exit status")
    if (completed.get("schema") != "ontokin.c200.driver-completed/0.1"
            or completed.get("process_reaped") is not True
            or completed.get("stdout_closed") is not True
            or completed.get("stderr_closed") is not True
            or type(completed.get("outer_timeout")) is not bool):
        raise ValueError("Driver marker does not establish terminal wait and closed output handles")
    locked = binding(lock_path)
    if locked["sha256"] != args.expected_lock_sha256:
        raise ValueError("Input lock differs from the declared executed bytes")
    lock = json.loads(lock_path.read_bytes())
    if Path(lock["repo_root"]).resolve() != repo or lock["qualification_revision"]["revision_id"] != REVISION:
        raise ValueError("Wrong C200 checkout or qualification revision")
    approval_path = lock_path.with_suffix(".approval.json")
    approved = binding(approval_path)
    if json.loads(approval_path.read_bytes()).get("input_lock_sha256") != locked["sha256"]:
        raise ValueError("Independent approval does not bind this executed lock")
    revision = lock["qualification_revision"]
    schedule = Path(lock["schedule_root"]).resolve()
    invocation, result = Path(revision["invocation_receipt"]), Path(revision["result_receipt"])
    locked_commands = [revision["coordinator"]["path"], str(repo / "prototypes/static_tray_v01/worker.py"),
                       str(repo / "prototypes/static_tray_v01/receiver.py"), str(repo / "prototypes/static_tray_v01/readback.mjs")]
    stopped_before = active_commands(locked_commands)
    candidates = [("c200-native", schedule), ("c200-driver", driver),
                  ("c200-coordinator/C200-INVOCATION.json", invocation),
                  ("c200-coordinator/C200-RESULT.json", result)]
    sources, absent = [], []
    for label, path in candidates:
        if path.exists() or path.is_symlink():
            if path.is_dir() and destination.is_relative_to(path):
                raise ValueError("Capture output cannot be inside a captured source tree")
            sources.append((label, path))
        else:
            absent.append({"path": str(path), "archive_path": label})
    snapshot = enumerate_sources(sources)
    destination.mkdir(parents=True, exist_ok=False)
    archive = destination / "captured-native-execution.tar.gz"
    captured = write_archive(archive, snapshot)
    verification = verify_archive(archive, captured)
    if enumerate_sources(sources) != snapshot:
        raise ValueError("Runtime tree changed while being captured")
    for row in captured.values():
        if row["type"] == "file" and digest(Path(row["source_path"])) != row["sha256"]:
            raise ValueError("Source bytes changed after capture: " + row["source_path"])
    if binding(lock_path) != locked or binding(approval_path) != approved or binding(terminal) != terminal_binding:
        raise ValueError("Lock, approval or terminal receipt changed during capture")
    stopped_after = active_commands(locked_commands)
    capture_source = Path(__file__).resolve()
    capture_copy = destination / "capture.py"
    with capture_source.open("rb") as source, capture_copy.open("xb") as out:
        shutil.copyfileobj(source, out)
    if digest(capture_copy) != digest(capture_source):
        raise ValueError("Captured helper source differs")
    copies = []
    for name, row in captured.items():
        if useful_receipt(name, row):
            target = destination / "receipts" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with Path(row["source_path"]).open("rb") as source, target.open("xb") as out:
                shutil.copyfileobj(source, out)
            if target.stat().st_size != row["size_bytes"] or digest(target) != row["sha256"]:
                raise ValueError("Direct receipt copy differs: " + name)
            copies.append({"path": target.relative_to(destination).as_posix(), "archive_path": name,
                           "bytes": row["size_bytes"], "sha256": row["sha256"]})
    manifest = {"schema": "ontokin.c200.native-evidence-capture/0.1", "status": "PASS_CAPTURE_INTEGRITY_ONLY",
                "captured_at_utc": datetime.now(timezone.utc).isoformat(), "qualification_revision": REVISION,
                "implementation": lock["implementation"], "input_lock": locked, "independent_approval": approved,
                "terminal_driver_marker": {**terminal_binding, "status_field": args.terminal_field,
                                           "actual_exit_status": completed[args.terminal_field]},
                "archive": {"path": archive.name, "bytes": archive.stat().st_size, "sha256": digest(archive)},
                "capture_script": {"path": capture_copy.name, "bytes": capture_copy.stat().st_size,
                                   "sha256": digest(capture_copy)},
                "source_roots": [{"archive_path": label, "source_path": str(path)} for label, path in sources],
                "absent_inputs": absent, "entries": captured, "direct_receipt_copies": copies,
                "archive_reread_verification": verification, "source_tree_unchanged": True,
                "relevant_process_observation_before": stopped_before, "relevant_process_observation_after": stopped_after,
                "capture_native_starts": 0, "capture_receiving_starts": 0, "capture_node_checker_starts": 0,
                "capture_lifecycle_starts": 0, "source_processes_launched_by_capture": 0,
                "limits": {"maximum_entries": MAX_FILES, "maximum_regular_payload_bytes": MAX_BYTES},
                "scope": "Exact retained runtime evidence and direct text receipts only; does not establish technical qualification or repeat any construction, import, checker, render or lifecycle trial"}
    with (destination / "MANIFEST.json").open("x") as out:
        json.dump(manifest, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps({"status": manifest["status"], "destination": str(destination),
                      "archive": manifest["archive"], "verification": verification,
                      "direct_receipts": len(copies), "absent_inputs": absent,
                      "capture_native_starts": 0}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
