#!/usr/bin/env python3
"""Reconstruct a hash-matching unsigned remote commit and import its real identity."""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=pathlib.Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--expected-old", required=True)
    parser.add_argument("--branch", required=True)
    args = parser.parse_args()
    base = pathlib.Path(__file__).resolve().parents[1]
    root = base / "OntoKin"
    record = json.loads(args.record.read_text())
    assert record["verification"]["signature"] is None
    def git(*items, data=None):
        return subprocess.check_output(["git", *items], cwd=root, input=data).decode().strip()
    assert git("rev-parse", "HEAD") == args.expected_old
    assert git("symbolic-ref", "--short", "HEAD") == args.branch
    assert git("write-tree") == record["tree"]["sha"]
    def stamp(person):
        return int(datetime.datetime.fromisoformat(person["date"].replace("Z", "+00:00")).timestamp())
    def zone(minutes):
        return ("-" if minutes < 0 else "+") + f"{abs(minutes)//60:02d}{abs(minutes)%60:02d}"
    a, c = record["author"], record["committer"]
    prefix = "tree " + record["tree"]["sha"] + "\n" + "".join("parent " + x["sha"] + "\n" for x in record["parents"])
    def candidate(az, cz, ending):
        return (prefix + f"author {a['name']} <{a['email']}> {stamp(a)} {zone(az)}\n" + f"committer {c['name']} <{c['email']}> {stamp(c)} {zone(cz)}\n\n" + record["message"] + ending).encode()
    def is_match(raw):
        return hashlib.sha1(b"commit " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == record["sha"]
    matches = []
    zones = range(-12*60, 14*60+1, 15)
    for az in zones:
        for cz in zones:
            for ending in ("", "\n"):
                raw = candidate(az, cz, ending)
                if is_match(raw):
                    matches.append((az, cz, ending, raw))
    assert len(matches) == 1
    az, cz, ending, raw = matches[0]
    out = pathlib.Path(__file__).resolve().parent
    raw_path = out / (args.output_prefix + "-actual-commit.bin")
    with raw_path.open("xb") as stream:
        stream.write(raw)
    assert git("hash-object", "-w", "-t", "commit", "--stdin", data=raw) == record["sha"]
    git("update-ref", "refs/heads/" + args.branch, record["sha"], args.expected_old)
    assert git("rev-parse", "HEAD") == record["sha"]
    assert git("rev-parse", "HEAD^{tree}") == record["tree"]["sha"]
    assert git("status", "--porcelain") == ""
    result = {"status": "passed", "commit": record["sha"], "tree": record["tree"]["sha"], "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "author_timezone": zone(az), "committer_timezone": zone(cz), "terminal_message_newline": ending == "\n", "matching_candidates": len(matches), "synthetic_commit_created": False, "git_status": "", "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (out / (args.output_prefix + "-import-verification.json")).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
