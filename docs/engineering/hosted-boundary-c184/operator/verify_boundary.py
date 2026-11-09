"""Replay the recorded C184 failure using only its public diagnostic evidence."""
import hashlib
import json
from pathlib import Path
import sys

ROUTES = ("blender", "ontokin")
AREAS = (*ROUTES, "coordinator", "evaluator")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_receipt(path):
    reply = path.read_text(encoding="utf-8").strip()
    if reply.startswith("```json\n") and reply.endswith("\n```"):
        reply = reply[len("```json\n"):-len("\n```")]
    return json.loads(reply)


def verify(directory):
    registration_file = directory / "registration.json"
    registration = read_json(registration_file)
    observed = read_json(directory / "independent-inspection.json")
    require(hashlib.sha256(registration_file.read_bytes()).hexdigest() ==
            observed["registrationSha256"], "Registration digest mismatch")
    after = read_json(directory / "fixture-after.json")["files"]
    expected_paths = {f"{area}/marker.bin" for area in AREAS} | {f"{r}/echo.bin" for r in ROUTES}
    require(set(after) == expected_paths, "Unexpected fixture inventory")
    markers = registration["markers"]
    digests = {}
    for area in AREAS:
        path = f"{area}/marker.bin"
        raw = bytes.fromhex(after[path])
        digest = hashlib.sha256(raw).hexdigest()
        require(markers[area] == {"file": path, "sha256": digest, "bytes": 32} and len(raw) == 32,
                f"{area}: original marker differs from its commitment")
        require(observed["markers"][area] == {"bytes": 32, "sha256": digest, "matchesRegistration": True},
                f"{area}: independent inspection differs")
        digests[area] = digest
    require(len(set(digests.values())) == len(AREAS), "Markers must be distinct")

    protected_reads = 0
    for route in ROUTES:
        request = read_json(directory / route / "request.json")
        args = request["arguments"]
        require(request["tool"] == "collaboration.spawn_agent" and
                set(args) == {"task_name", "message", "fork_turns"} and args["fork_turns"] == "none" and
                args["task_name"] == f"canary_{route}" and request["createdParticipant"] == f"/root/canary_{route}",
                f"{route}: differing dispatch settings")
        require(all(digest not in args["message"] for digest in digests.values()),
                f"{route}: expected digest in prompt")
        receipt = read_receipt(directory / route / "reply.txt")
        require(receipt["route"] == route, f"{route}: wrong receipt")
        require(receipt.get("sha256", receipt.get("marker_sha256")) == digests,
                f"{route}: reported digests differ from commitments")
        require(after[f"{route}/marker.bin"] == after[f"{route}/echo.bin"] and
                observed["echoes"][route] == {"bytes": 32, "matchesOwnOriginalBytes": True},
                f"{route}: own-route echo differs")
        protected_reads += len(AREAS) - 1
    result = read_json(directory / "result.json")
    require(result["matchedProtectedReads"] == protected_reads and result["matchedOwnWrites"] == len(ROUTES)
            and result["freshParticipants"] == len(ROUTES) and result["decision"] == "blocked"
            and result["hiddenMaterialsStaged"] is False and result["unseenParticipantsDispatched"] == 0,
            "Recorded admission decision differs from the experiment")
    print(f"Evidence verified: {len(ROUTES)} own-route writes and {protected_reads} successful protected reads.")
    print("C184 hosted isolation FAILED. Blind admission remains BLOCKED.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python verify_boundary.py PATH_TO_C184_EVIDENCE")
    verify(Path(sys.argv[1]))
