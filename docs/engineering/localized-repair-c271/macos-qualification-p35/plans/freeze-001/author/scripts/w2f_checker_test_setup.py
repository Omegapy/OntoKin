"""W2 freeze author: build a synthetic freeze and records to test w2f_s7_check.py's predicates (stdlib; -I -S -B).

Usage: w2f_checker_test_setup.py REAL_FREEZE TEST_DIR   (TEST_DIR must be absent; everything is written inside it)
Prints the synthetic freeze's SHA-256. Every command T_true_* must give MET and every T_false_* NOT_MET.
"""
import hashlib
import json
import os
import sys

real = json.load(open(sys.argv[1]))
top = sys.argv[2]
os.mkdir(top, 0o755)


def put(name, data, mode=0o644):
    path = os.path.join(top, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as stream:
        stream.write(data)
    os.chmod(path, mode)
    return path


argv = ["/usr/bin/env", "-i", "PATH=/usr/bin:/bin", "/x/python", "-B", "tool.py", "--a-sha256", "<PLACE>", "--b", "<OTHER>"]
target = put("target.bin", b"payload")
target_sha = hashlib.sha256(b"payload").hexdigest()
listing = put("listing.json", json.dumps({"paths": {"/p/q.json": {"sha256": "ab" * 32}}}).encode())
command = put("cmd.command.json", json.dumps({"argv": argv[:7] + [target_sha, "--b", "ab" * 32], "cwd": "/w",
                                              "boot": {"before": "B", "after": "B"}}).encode())
outputs = put("out.json", json.dumps({"state": "OK", "rows": [{"s": "absent"}, {"s": "absent"}],
                                      "events": [{"argv": ["/node"]}, {"argv": ["/git"]}, {"argv": ["/node"]}],
                                      "nothing": None, "n": 3, "flag": False}).encode())
text = put("stderr.txt", b'MH-OUTCOMES {"state": "ALL_PASSED"}\n')
exit_file = put("exit.txt", b"0\n")
reviewed = put("reviewed.json", json.dumps({"schema": "s", "status": "REVIEWED", "reviewer": "W3"}).encode())
directory = os.path.join(top, "prepared-dir")
os.mkdir(directory, 0o700)
prepared_file = put("prepared-dir/file.txt", b"abc")
FREEZE_PLACEHOLDER_SHA = "f" * 64
true_rules = [
    {"file": command, "pointer": "/argv", "argv_equals_except": {"argv": argv, "indices": [7, 9]}},
    {"file": command, "pointer": "/argv/7", "equals_sha256_of": target},
    {"file": command, "pointer": "/argv/9", "equals_from": {"file": listing, "pointer": "/paths/~1p~1q.json/sha256"}},
    {"file": command, "pointer": "/cwd", "equals": "/w"},
    {"file": outputs, "pointer": "/rows", "each": {"pointer": "/s", "equals": "absent"}},
    {"file": outputs, "pointer": "/rows", "length": 2},
    {"file": outputs, "pointer": "/events", "count_where": {"pointer": "/argv/0", "equals": "/node"}, "equals": 2},
    {"file": outputs, "pointer": "/nothing", "equals": None},
    {"file": outputs, "pointer": "/flag", "equals": False},
    {"file": outputs, "pointer": "/missing", "absent": True},
    {"file": outputs, "pointer": "/n", "equals": 3},
    {"file": text, "text_includes": '"state": "ALL_PASSED"'},
    {"file": exit_file, "text_equals": "0\n"},
    {"file": top + "/never", "exists": False},
    {"file": target, "sha256": target_sha}]
false_rules = [
    {"file": command, "pointer": "/argv", "argv_equals_except": {"argv": argv[:-1] + ["--c"], "indices": [7]}},
    {"file": command, "pointer": "/argv/7", "equals_sha256_of": exit_file},
    {"file": command, "pointer": "/argv/9", "equals_from": {"file": listing, "pointer": "/paths/none"}},
    {"file": outputs, "pointer": "/rows", "each": {"pointer": "/s", "equals": "present"}},
    {"file": outputs, "pointer": "/events", "count_where": {"pointer": "/argv/0", "equals": "/node"}, "equals": 3},
    {"file": outputs, "pointer": "/flag", "equals": 0},
    {"file": outputs, "pointer": "/n", "equals": True},
    {"file": outputs, "pointer": "/state", "absent": True},
    {"file": text, "text_equals": "x"},
    {"file": target, "exists": False},
    {"file": target, "sha256": "0" * 64},
    {"file": command, "pointer": "/argv/7", "equals_freeze_sha256": True}]
commands = [{"id": "P1", "phase": "precondition", "expect": true_rules[:3]},
            {"id": "D02", "phase": "preparation", "expect": []},
            {"id": "T_true", "phase": "s7", "expect": true_rules, "audit_expect": false_rules[:1]},
            {"id": "Q1", "phase": "post", "expect": true_rules[3:6]},
            {"id": "Q04", "phase": "post", "expect": []}]
commands += [{"id": "T_false_%d" % index, "phase": "s7", "expect": [rule], "audit_expect": []}
             for index, rule in enumerate(false_rules)]
freeze = {"boot_session_uuid": real["boot_session_uuid"], "umask": "0o022",
          "bindings": [{"id": "b1", "path": target, "kind": "file", "sha256": target_sha, "size_bytes": 7, "mode": "0o644",
                        "nlink_one": True}],
          "trees": [{"root": top, "bytecode": True}], "host_facts": [], "evidence": real["evidence"],
          "absent_paths": {"before_preparation": [top + "/absent-1"], "after_preparation": [top + "/absent-2"]},
          "deferred_inputs": [{"id": "r", "path": reviewed, "requirements": [
              {"pointer": "/status", "equals": "REVIEWED"}, {"pointer": "/reviewer", "nonempty_string": True}]}],
          "preparation": {"entries": [
              {"id": "d", "path": directory, "kind": "directory", "mode": "0o700", "entries": ["file.txt"]},
              {"id": "f", "path": prepared_file, "kind": "file", "sha256": hashlib.sha256(b"abc").hexdigest(), "size_bytes": 3,
               "mode": "0o644", "nlink_one": True}]},
          "post": {"not_rechecked": [], "consumed": []}, "commands": commands}
raw = json.dumps(freeze, indent=1).encode()
path = put("FREEZE-TEST.json", raw)
print(json.dumps({"freeze": path, "sha256": hashlib.sha256(raw).hexdigest(),
                  "false_commands": [c["id"] for c in commands if c["id"].startswith("T_false")]}))
