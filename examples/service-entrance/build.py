"""Create and record a sliding gate through the public OntoKin agent interface."""
import argparse
import base64
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


HEAD = "3a1cd5785a9dd0c64d9b74ef97cdc5e6b609b117"
TREE = "0bc1d9be5d67654db7ba7f14f134b22b3215262b"
HOST = {"max_operations": 1_000_000, "max_elapsed_ms": 80_000}
INITIAL_CAP = {"max_operations": 450_000, "max_elapsed_ms": 80_000}


def write_json(path, obj):
    path.write_bytes((json.dumps(obj, indent=2) + "\n").encode("utf-8"))


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path, help="new directory")
    parser.add_argument("--operations", type=int, default=INITIAL_CAP["max_operations"])
    parser.add_argument("--elapsed-ms", type=int, default=INITIAL_CAP["max_elapsed_ms"])
    args = parser.parse_args()
    cap = {"max_operations": args.operations, "max_elapsed_ms": args.elapsed_ms}
    root = args.checkout.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    def git(*options):
        return subprocess.check_output(["git", "-C", root, *options], text=True).strip()

    if (git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"), git("status", "--porcelain")) != (HEAD, TREE, ""):
        raise ValueError(f"A clean runtime worktree at {HEAD} is required")
    sys.path.insert(0, str(root))
    from ontokin.execution_budget import HostPolicy
    from ontokin.torque_agent import TorqueAgentService

    source = (Path(__file__).resolve().parent / "src" / "main.ok").read_text(encoding="utf-8")
    create = {"operation": "create", "schema_version": "ontokin.agent/0.22", "request_id": "gate-create",
              "project_id": "gate-sliding-gate", "expected_program_revision": None, "requested_level": "constructed",
              "bundle": {"schema_version": "ontokin.bundle/0.2", "entry": {"filename": "main.ok", "source": source},
                         "modules": [], "assets": []}}
    project = create["project_id"]
    common = {"project_id": project, "schema_version": create["schema_version"]}
    exchange = {}
    stats = {}
    env = {"head": HEAD, "tree": TREE, "os": platform.platform(), "architecture": platform.machine(),
           "python": sys.version, "executable": sys.executable, "argv": sys.argv,
           "utc_start": datetime.now(timezone.utc).isoformat(), "host_ceilings": HOST}
    write_json(output / "environment.json", env)
    with tempfile.TemporaryDirectory() as store, TorqueAgentService(Path(store), host_policy=HostPolicy(**HOST)) as service:
        def submit(request, key):
            wall = time.perf_counter()
            cpu = time.process_time()
            exchange[key + "_request"] = request
            write_json(output / "exchange.json", exchange)
            response = service.handle(request)
            stats[key] = {"wall_seconds": time.perf_counter() - wall, "cpu_seconds": time.process_time() - cpu}
            exchange[key + "_response"] = response
            write_json(output / "exchange.json", exchange)
            if response["status"] != "succeeded":
                write_json(output / "refusal.json", {"request": request, "response": response,
                           "wall_seconds": stats[key]["wall_seconds"], "cpu_seconds": stats[key]["cpu_seconds"]})
                raise RuntimeError(f"{key} refused: {response['diagnostics']}, {response['protocol_error']}")
            return response

        created = submit(create, "create")
        after = created["accepted_program_revision"]
        accepted = service.read_program(project, after).to_payload()
        write_json(output / "accepted-bundle.json", accepted)
        assert accepted == create["bundle"]
        export = {**common, "operation": "export", "request_id": "gate-export", "program_revision": after,
                  "budgets": cap, "destination": "ontokin.glb/0.22", "options": {"end": "3.25", "fps": 32,
                  "helpers": False, "position_tolerance_m": 0.001, "rotation_tolerance_rad": 0.001,
                  "time_tolerance_s": 0.000001}}
        published = submit(export, "export")
        artifact = published["result"]
        assert artifact["program_revision"] == after and published["execution_budget"]["effective"] == cap
        recording = bytearray()
        reads = []
        while len(recording) < artifact["total_bytes"]:
            offset = len(recording)
            request = {**common, "request_id": f"gate-read-{offset}", "operation": "artifact",
                       "artifact_id": artifact["artifact_id"], "offset": offset, "max_bytes": 65536}
            response = service.handle(request)
            reads.append({"request": request, "response": response})
            if response["status"] != "succeeded":
                write_json(output / "reads.json", reads)
                raise RuntimeError(f"artifact read failed at {offset}")
            part = response["result"]
            assert (part["offset"], part["total_bytes"], part["sha256"], part["program_revision"]) == (
                offset, artifact["total_bytes"], artifact["sha256"], after)
            chunk = base64.b64decode(part["data_base64"], validate=True)
            assert len(chunk) == min(65536, artifact["total_bytes"] - offset)
            recording.extend(chunk)
            assert part["next_offset"] == (len(recording) if len(recording) < artifact["total_bytes"] else None)
        assert digest(recording) == artifact["sha256"]
        (output / "sliding-gate.glb").write_bytes(recording)
        write_json(output / "reads.json", reads)
        report = artifact["report"]
        receipt = {"program_revision": after, "artifact": "sliding-gate.glb", "bytes": len(recording),
                   "sha256": artifact["sha256"], "artifact_reads": len(reads), "sampling": report["sampling"],
                   "export_checkpoint": report["execution_budget_at_export"],
                   "requests": {op: {**stats[op], "budget": exchange[op + "_response"]["execution_budget"]}
                                for op in stats}, "utc_finish": datetime.now(timezone.utc).isoformat()}
        write_json(output / "receipt.json", receipt)
        print(f"Published {artifact['sha256']} from {after} ({len(recording)} bytes, {len(reads)} reads)")


if __name__ == "__main__":
    main()
