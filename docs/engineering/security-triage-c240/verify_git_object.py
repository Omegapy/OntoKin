#!/usr/bin/env python3
"""Read-only reproduction of the C240 GitGuardian Git-object finding."""
import hashlib
import json
import pathlib
import subprocess
import sys

EXECUTED_COMMIT = "0d850f836e3f9ab4fe1f832b9e75db57501d49df"
FLAGGED = "676eecee857d5212d86340122f81b06f4c6791b1"
PATH = "docs/engineering/second-target-c239/evidence/SOURCE-EQUIVALENCE.json"
EXPECTED_TREE = "85734862971c4cff80f8ac8717d738a5f1604dd2"
EXPECTED_FILE_SHA256 = "abccc3f6ce0e85cd76782069a1a68f44dcd02ab362633810e5dde5dd41b969d5"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_git_object.py /absolute/path/to/repository")
    repo = pathlib.Path(sys.argv[1]).resolve()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args])
    kind = git("cat-file", "-t", EXECUTED_COMMIT).decode().strip()
    payload = git("cat-file", "commit", EXECUTED_COMMIT)
    digest = hashlib.sha1(
        b"commit " + str(len(payload)).encode("ascii") + b"\0" + payload
    ).hexdigest()
    raw = git("show", FLAGGED + ":" + PATH)
    record = json.loads(raw)
    tree = git("rev-parse", EXECUTED_COMMIT + "^{tree}").decode().strip()
    line4 = raw.decode().splitlines()[3]
    checks = {
        "object_type_is_commit": kind == "commit",
        "object_payload_bytes_is_259": len(payload) == 259,
        "calculated_object_id_matches": digest == EXECUTED_COMMIT,
        "report_field_matches_object_id": record["author_final_execution_commit"] == EXECUTED_COMMIT,
        "flagged_line4_matches": line4.strip() == '"author_final_execution_commit": "' + EXECUTED_COMMIT + '",',
        "tree_matches_published_scientific_tree": tree == EXPECTED_TREE,
        "incident_file_sha256_matches": hashlib.sha256(raw).hexdigest() == EXPECTED_FILE_SHA256,
    }
    result = {
        "result": "PASS" if all(checks.values()) else "FAIL",
        "executed_commit": EXECUTED_COMMIT,
        "calculated_git_object_sha1": digest,
        "commit_payload_bytes": len(payload),
        "tree": tree,
        "source_equivalence_file_sha256": hashlib.sha256(raw).hexdigest(),
        "checks": checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())

