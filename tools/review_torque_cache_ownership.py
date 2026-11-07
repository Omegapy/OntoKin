#!/usr/bin/env python3
"""Independent actual-request review of the .22 artifact proof owner.

Uses a read-only backup of an actually accepted seed. It does not replace the
Agent callback, ledger, artifact reader or implementation identity.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--seed-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.source))
    from ontokin.execution_budget import HostPolicy
    from ontokin.torque_agent import TorqueAgentService

    def source_hashes():
        return {str(path.relative_to(args.source)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted((args.source / "ontokin").glob("*.py"))}

    result = {"scope": "Actual original Agent requests and current SQLite bytes; ordinary service proof ownership, not a Python process sandbox.",
              "source_commit": subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip(),
              "source_before": source_hashes(), "seed_store": str(args.seed_store), "exchanges": [], "checks": []}
    store = args.output / "store"
    store.mkdir()
    with sqlite3.connect("file:" + str(args.seed_store) + "?mode=ro", uri=True) as src:
        with sqlite3.connect(store / "torque-program-agent.sqlite3") as dst:
            src.backup(dst)
    serial = 0
    def require(value, label):
        result["checks"].append({"check": label, "passed": bool(value)})
        if not value:
            raise AssertionError(label)

    def save():
        (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    try:
        with TorqueAgentService(store, host_policy=HostPolicy(max_operations=1000000, max_elapsed_ms=30000)) as service:
            with service._store.connection() as db:
                row = db.execute("SELECT project_id,id,data FROM artifacts ORDER BY id LIMIT 1").fetchone()
            require(row is not None, "Seed contains an actual accepted artifact")
            project, artifact, raw = row["project_id"], row["id"], bytes(row["data"])
            changed = raw[:-1] + bytes([raw[-1] ^ 1])
            result.update(artifact_id=artifact, artifact_bytes=len(raw),
                          original_sha256=hashlib.sha256(raw).hexdigest(), changed_sha256=hashlib.sha256(changed).hexdigest())

            def request(label, *, operation="artifact", offset=0):
                nonlocal serial
                serial += 1
                req = {"schema_version": "ontokin.agent/0.22", "project_id": project,
                       "request_id": "independent-proof-owner-" + str(serial), "operation": operation}
                if operation == "artifact":
                    req.update(artifact_id=artifact, offset=offset, max_bytes=1)
                else:
                    req.update(profile="torque-0.1", limit=1)
                response = service.handle(req)
                result["exchanges"].append({"label": label, "request": req, "response": response})
                save()
                return response

            for operation, stage in (("artifact", "artifact_integrity"), ("artifact", "publication"),
                                     ("discover", "publication")):
                for setter in (setattr, object.__setattr__):
                    label = operation + "/" + stage + "/" + setter.__qualname__
                    require(request(label + "/warm")["status"] == "succeeded", label + ": actual warm succeeds")
                    proof = service._verified_artifact
                    forged = type(proof)(proof.project, proof.artifact_id, changed, proof.digest)
                    seen = []
                    def original_callback():
                        ledger = sys._getframe(1).f_locals["self"].execution_budget
                        if ledger.stage != stage or seen:
                            return
                        try:
                            setter(service, "_verified_artifact", forged)
                        except AttributeError as error:
                            seen.append({"outcome": "refused", "error_type": type(error).__name__})
                        else:
                            seen.append({"outcome": "published"})
                    service._host_check = original_callback
                    try:
                        response = request(label + "/attempt", operation=operation)
                    finally:
                        service._host_check = None
                    require(response["status"] == "succeeded", label + ": caught original callback continues")
                    require(seen == [{"outcome": "refused", "error_type": "AttributeError"}], label + ": owner assignment refuses")
                    require(service._verified_artifact is proof, label + ": original proof retained")
                    with service._store.transaction() as db:
                        db.execute("UPDATE artifacts SET data=? WHERE project_id=? AND id=?", (changed, project, artifact))
                    try:
                        refused = request(label + "/corrupted-tail", offset=len(raw) - 1)
                        codes = {diagnostic["code"] for diagnostic in refused.get("diagnostics", [])}
                        if refused.get("protocol_error"):
                            codes.add(refused["protocol_error"]["code"])
                        require("OKA-E-STORE-INTEGRITY" in codes, label + ": complete changed SQLite bytes refuse")
                        require(refused["status"] != "succeeded", label + ": no corrupt returned byte")
                    finally:
                        with service._store.transaction() as db:
                            db.execute("UPDATE artifacts SET data=? WHERE project_id=? AND id=?", (raw, project, artifact))
            proof = service._verified_artifact
            try:
                object.__setattr__(proof, "data", changed)
            except AttributeError:
                require(True, "Native tuple slots cannot be poisoned in place")
            else:
                require(False, "Native tuple slots cannot be poisoned in place")
            final = request("restored-current-sqlite", offset=len(raw) - 1)
            require(final["status"] == "succeeded" and base64.b64decode(final["result"]["data_base64"]) == raw[-1:],
                    "Restored exact current SQLite bytes still succeed")
        require(service._verified_artifact is None, "Completed close clears the per-service proof")
        result["source_after"] = source_hashes()
        require(result["source_after"] == result["source_before"], "Exact package source remains unchanged")
        result["status"] = "passed"
    except BaseException as error:
        result["status"] = "failed"
        result["error"] = repr(error)
        raise
    finally:
        save()
    print(json.dumps({"status": result["status"], "checks": len(result["checks"]), "exchanges": len(result["exchanges"])}))


if __name__ == "__main__":
    main()
