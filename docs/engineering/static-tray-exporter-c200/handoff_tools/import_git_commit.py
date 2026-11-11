"""Reconstruct exact GitHub git/commits objects; never change Git references.

Default operation is verification only. --write writes a commit object only
after its Git object SHA-1 equals the requested API identity and its direct tree
and parent objects are available. The tool performs no network operation.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

OID = re.compile(r"[0-9a-f]{40}\Z")
OFFSET = re.compile(r"[+-](?:0[0-9]|1[0-4])[0-5][0-9]\Z")
MAX_JSON = 2 * 1024 * 1024


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError("Duplicate JSON member: " + key)
        result[key] = value
    return result


def load_metadata(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file(): raise ValueError("Metadata must be a regular nonsymlink file")
    with path.open("rb") as stream: raw = stream.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON: raise ValueError("Metadata exceeds 2 MiB")
    value = json.loads(raw, object_pairs_hook=unique)
    for _ in range(5):
        if isinstance(value, dict) and "sha" in value and "tree" in value: break
        if isinstance(value, dict) and isinstance(value.get("structuredContent"), dict):
            value = value["structuredContent"]
        elif isinstance(value, dict) and isinstance(value.get("content"), str):
            value = json.loads(value["content"], object_pairs_hook=unique)
        else: raise ValueError("Expected raw GitHub /git/commits JSON or its connector envelope")
    if not isinstance(value, dict) or "sha" not in value or "tree" not in value:
        raise ValueError("Git commit metadata is missing")
    return value, hashlib.sha256(raw).hexdigest()


def oid(data):
    return hashlib.sha1(b"commit " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def required_oid(value, label):
    if not isinstance(value, str) or not OID.fullmatch(value): raise ValueError("Invalid " + label)
    return value


def timestamp(value):
    if not isinstance(value, str): raise ValueError("Commit date must be an ISO string")
    date = datetime.fromisoformat(value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value)
    if date.tzinfo is None or date.microsecond: raise ValueError("Commit date requires an explicit timezone and whole seconds")
    return int(date.timestamp()), date.strftime("%z")


def identity(person, offset=None):
    name, email = person["name"], person["email"]
    if not isinstance(name, str) or not isinstance(email, str) or not name or not email:
        raise ValueError("Commit identity is incomplete")
    if any(c in name + email for c in "\0\r\n<>"):
        raise ValueError("Unsupported commit identity characters")
    epoch, api_offset = timestamp(person["date"])
    offset = offset or api_offset
    if not OFFSET.fullmatch(offset): raise ValueError("Timezone offset must use an explicit ±HHMM value")
    return (name + " <" + email + "> " + str(epoch) + " " + offset).encode("utf-8")


def headers_and_message(data):
    if b"\0" in data or b"\n\n" not in data: raise ValueError("Malformed raw commit")
    header, message = data.split(b"\n\n", 1)
    groups = []
    for line in header.split(b"\n"):
        if line.startswith(b" "):
            if not groups: raise ValueError("Invalid leading header continuation")
            groups[-1] += b"\n" + line
        else:
            if b" " not in line: raise ValueError("Malformed commit header")
            groups.append(line)
    if len(groups) > 64: raise ValueError("Unbounded commit header count")
    return groups, message


def check_fields(raw, metadata):
    groups, message = headers_and_message(raw)
    fields = {}
    for group in groups:
        key, value = group.split(b" ", 1)
        fields.setdefault(key.decode("ascii"), []).append(value)
    if fields.get("tree") != [metadata["tree"]["sha"].encode("ascii")]: raise ValueError("Raw tree disagrees with API")
    if fields.get("parent", []) != [p["sha"].encode("ascii") for p in metadata["parents"]]: raise ValueError("Raw parents disagree with API order")
    for role in ("author", "committer"):
        actual = fields.get(role, [])
        if len(actual) != 1: raise ValueError("Raw commit needs exactly one " + role)
        match = re.fullmatch(rb"(.+) <([^<>\r\n]+)> (-?[0-9]+) ([+-][0-9]{4})", actual[0])
        if not match: raise ValueError("Unrecognized raw identity")
        person = metadata[role]
        if (match[1].decode("utf-8") != person["name"] or match[2].decode("utf-8") != person["email"]
                or int(match[3]) != timestamp(person["date"])[0]):
            raise ValueError("Raw " + role + " disagrees with API identity or absolute time")
    expected_message = metadata["message"].encode("utf-8")
    if message != expected_message and message.rstrip(b"\n") != expected_message:
        raise ValueError("Raw message differs from the API beyond trailing newline representation")
    return {role: fields[role][0].rsplit(b" ", 1)[1].decode("ascii") for role in ("author", "committer")}


def reconstruct(metadata, expected_sha, *, author_offset=None, committer_offset=None):
    required_oid(expected_sha, "requested commit SHA")
    if metadata.get("sha") != expected_sha: raise ValueError("Requested SHA differs from the API response")
    required_oid(metadata["tree"]["sha"], "tree SHA")
    if not isinstance(metadata["parents"], list) or len(metadata["parents"]) > 32:
        raise ValueError("Invalid or unbounded parent list")
    for parent in metadata["parents"]: required_oid(parent["sha"], "parent SHA")
    if not isinstance(metadata["message"], str): raise ValueError("Missing API commit message")
    verification = metadata.get("verification") or {}
    payload, signature = verification.get("payload"), verification.get("signature")
    candidates = []
    if payload is not None or signature is not None:
        if not isinstance(payload, str) or not isinstance(signature, str) or not signature:
            raise ValueError("Incomplete signature/payload pair; refusing to manufacture signing bytes")
        groups, message = headers_and_message(payload.encode("utf-8"))
        if any(g.split(b" ", 1)[0].startswith(b"gpgsig") for g in groups):
            raise ValueError("Verification payload unexpectedly contains a signature header")
        signed = signature.encode("utf-8")
        variants = [("preserve-signature", signed)]
        if signed.endswith(b"\n"): variants.append(("omit-signature-terminal-lf", signed[:-1]))
        else: variants.append(("include-signature-terminal-lf", signed + b"\n"))
        # Payload preserves original header order and zones. The signature's
        # header insertion position is selected solely by the requested SHA.
        for position in range(len(groups) + 1):
            for variant, value in variants:
                field = b"gpgsig " + value.replace(b"\n", b"\n ")
                raw = b"\n".join(groups[:position] + [field] + groups[position:]) + b"\n\n" + message
                candidates.append((raw, "verification-payload/" + variant + "/header-" + str(position)))
    else:
        header = [b"tree " + metadata["tree"]["sha"].encode("ascii")]
        header += [b"parent " + p["sha"].encode("ascii") for p in metadata["parents"]]
        header += [b"author " + identity(metadata["author"], author_offset), b"committer " + identity(metadata["committer"], committer_offset)]
        message = metadata["message"].encode("utf-8")
        for tail, label in ((b"", "exact-api-message"), (b"\n", "api-message-plus-one-lf")):
            candidates.append((b"\n".join(header) + b"\n\n" + message + tail, "unsigned/" + label))
    matches = [(raw, method) for raw, method in candidates if oid(raw) == expected_sha]
    unique_matches = {raw for raw, method in matches}
    if len(unique_matches) != 1:
        digests = sorted({oid(raw) for raw, _ in candidates})
        raise ValueError("No unique exact commit reconstruction. API dates may have lost original timezone offsets or headers. "
                         "Supply evidenced --author-offset/--committer-offset for unsigned commits; no object was written. Candidate SHAs: " + ",".join(digests))
    raw, method = matches[0]
    offsets = check_fields(raw, metadata)
    if signature is not None and ((author_offset and offsets["author"] != author_offset) or (committer_offset and offsets["committer"] != committer_offset)):
        raise ValueError("Explicit timezone hint conflicts with authoritative signed payload")
    return raw, {"method": method, "author_offset": offsets["author"], "committer_offset": offsets["committer"],
                 "github_signature_verified": verification.get("verified"), "github_signature_reason": verification.get("reason"),
                 "signature_verification_scope": "Preserved API-provided signature bytes; this helper verifies object identity, not PGP trust"}


def git(repo, *args, data=None, check=True):
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_REPLACE_OBJECTS="1")
    return subprocess.run(["git", "--no-replace-objects", "-C", str(repo), "-c", "core.hooksPath=" + os.devnull, *args],
                          input=data, capture_output=True, check=check, timeout=30, env=environment)


def import_commit(repo, metadata, expected_sha, *, write=False, author_offset=None, committer_offset=None):
    raw, details = reconstruct(metadata, expected_sha, author_offset=author_offset, committer_offset=committer_offset)
    repo = Path(repo).resolve()
    if git(repo, "rev-parse", "--show-object-format").stdout.strip() != b"sha1":
        raise ValueError("Only the requested SHA-1 repository object format is supported")
    required = [(metadata["tree"]["sha"], b"tree"), *((p["sha"], b"commit") for p in metadata["parents"])]
    for target, typ in required:
        observed = git(repo, "cat-file", "-t", target, check=False)
        if observed.returncode or observed.stdout.strip() != typ:
            raise ValueError("Required direct tree/parent object is unavailable or has wrong type: " + target)
    checked = git(repo, "hash-object", "-t", "commit", "--stdin", data=raw).stdout.decode("ascii").strip()
    if checked != expected_sha: raise ValueError("Git's own object hash disagrees; no object was written")
    existing = git(repo, "cat-file", "commit", expected_sha, check=False)
    already_present = existing.returncode == 0
    if already_present and existing.stdout != raw: raise ValueError("Existing local object bytes disagree")
    if write:
        written = git(repo, "hash-object", "-w", "-t", "commit", "--stdin", data=raw).stdout.decode("ascii").strip()
        if written != expected_sha or git(repo, "cat-file", "commit", expected_sha).stdout != raw:
            raise ValueError("Commit object write/readback differs; references were not changed")
    return raw, {"schema": "ontokin.exact-github-commit-import/0.1", "passed": True, "commit": expected_sha,
                 "tree": metadata["tree"]["sha"], "parents": [p["sha"] for p in metadata["parents"]],
                 "bytes": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(), "already_present": already_present,
                 "existing_bytes_equal": already_present, "write_requested": write, "write_completed": write,
                 "refs_updated": False, "network_used": False, "direct_references_verified": True, **details}


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--author-offset")
    parser.add_argument("--committer-offset")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--raw-output")
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    try:
        for name in (args.raw_output, args.report):
            if name and Path(name).exists(): raise ValueError("Refusing to overwrite evidence: " + name)
        metadata, metadata_hash = load_metadata(args.metadata)
        raw, report = import_commit(args.repo, metadata, args.sha, write=args.write,
            author_offset=args.author_offset, committer_offset=args.committer_offset)
        report["metadata_sha256"] = metadata_hash
        if args.raw_output: write_new(args.raw_output, raw)
        if args.report: write_new(args.report, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"passed": False, "error": type(exc).__name__ + ": " + str(exc), "refs_updated": False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
