"""Restore actual GitHub API commit bytes only when the Git SHA-1 agrees."""
import argparse
from datetime import datetime
import hashlib
import itertools
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("api_json", type=Path)
    parser.add_argument("raw_output", type=Path)
    parser.add_argument("--set-head", action="store_true")
    args = parser.parse_args()
    commit = json.loads(args.api_json.read_text())
    def lines(person, offset):
        epoch = int(datetime.fromisoformat(person["date"].replace("Z", "+00:00")).timestamp())
        return f'{person["name"]} <{person["email"]}> {epoch} {offset}'
    offsets = ["-0600", "+0000"] + [f'{sign}{h:02d}{m:02d}' for sign in ("+", "-") for h in range(15) for m in (0,15,30,45)]
    offsets = list(dict.fromkeys(offsets))
    header = "tree " + commit["tree"]["sha"] + "\n" + "".join("parent " + p["sha"] + "\n" for p in commit["parents"])
    found = None
    for a,c in itertools.chain(((o,o) for o in offsets),itertools.product(offsets, offsets)):
        prefix = header + "author " + lines(commit["author"], a) + "\ncommitter " + lines(commit["committer"], c) + "\n\n"
        for suffix in ("", "\n"):
            raw = (prefix + commit["message"] + suffix).encode()
            sha = hashlib.sha1(b"commit " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if sha == commit["sha"]:
                found = raw
                break
        if found is not None:
            break
    assert found is not None, "API metadata cannot reconstruct actual raw commit; fetch raw identity"
    args.raw_output.parent.mkdir(parents=True, exist_ok=True)
    args.raw_output.write_bytes(found)
    result = subprocess.run(["git", "-C", str(args.repository), "hash-object", "-t", "commit", "-w", "--stdin"], input=found, capture_output=True, check=True)
    assert result.stdout.decode().strip() == commit["sha"]
    if args.set_head:
        subprocess.run(["git", "-C", str(args.repository), "update-ref", "HEAD", commit["sha"]], check=True)
    print(json.dumps({"commit": commit["sha"], "tree": commit["tree"]["sha"], "raw_bytes": len(found), "actual_hash_verified": True}))


if __name__ == "__main__":
    main()
