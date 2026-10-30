#!/usr/bin/env python3
"""Execute the frozen C073 workload through the actual C074 Agent lifecycle."""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.budget_agent import BudgetAgentService
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.execution_budget import HostPolicy
from tools.check_local import inventory, git_metadata


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output == ROOT or output.is_relative_to(ROOT):
        raise ValueError("Write raw Agent evidence outside the source checkout.")
    output.mkdir(parents=True, exist_ok=False)
    fixture = ROOT / "examples/execution-budgets"
    freeze = json.loads((fixture / "acceptance-freeze.json").read_text())
    for name, expected in freeze["files"].items():
        raw = (fixture / name).read_bytes()
        if {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} != expected:
            raise ValueError("Frozen input changed: " + name)
    source = ProgramBundle(SourceUnit("entry", "larger-workload.ok", (fixture / "larger-workload.ok").read_bytes()))
    expected = json.loads((fixture / "larger-workload.expected.json").read_text())
    options = expected["options"]
    source_before = inventory(ROOT)
    save(output / "source-before.json", source_before)
    summary = {"schema_version": "ontokin.budget-agent-acceptance/0.1", "status": "running",
        "started_utc": utc(), "case_id": "C074-Agent-EB15-EB16-EB18-EB24-EB29",
        "source_workload": freeze["case_id"], "frozen_inputs": freeze["files"],
        "program_revision": source.program_revision, "git": git_metadata(ROOT),
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "exchanges": 0, "assertions": [], "original28_gate_changed": False,
        "release_acceptance": False}
    save(output / "summary.json", summary)
    serial = 0
    transcript = output / "protocol.jsonl"
    exchanges = []
    services = []
    live_stores = tempfile.TemporaryDirectory(prefix="ontokin-c074-acceptance-")
    summary["live_store_root"] = live_stores.name
    summary["store_evidence"] = "Closed SQLite backups copied from temporary host-local execution stores"

    def assert_that(condition, label):
        summary["assertions"].append({"label": label, "passed": bool(condition)})
        save(output / "summary.json", summary)
        if not condition:
            raise AssertionError(label)

    def request(project, operation, **fields):
        nonlocal serial
        serial += 1
        return {"schema_version": "ontokin.agent/0.7", "project_id": project,
                "request_id": "c074-" + str(serial), "operation": operation, **fields}

    def call(service, payload, *, wait=True):
        result = service.handle(payload, wait=wait)
        summary["exchanges"] += 1
        exchange = {"sequence": summary["exchanges"], "utc": utc(), "request": payload, "response": result}
        exchanges.append(exchange)
        save(output / (f"exchange-{summary['exchanges']:03d}.json"), exchange)
        return result

    def patch(program, old, new):
        start = program.entry.raw.index(old.encode())
        return {"source_id": "entry", "source_revision": program.entry.revision,
                "element_id": ["sources", "entry"], "start_byte": start,
                "end_byte": start + len(old.encode()), "expected_text": old, "replacement": new}

    try:
        control = BudgetAgentService(Path(live_stores.name) / "store-control")
        services.append(control)
        failed = call(control, request("default-control", "create", bundle=source.to_payload(),
            expected_program_revision=None, requested_level="delivered", destination="ontokin.glb/0.7",
            options=options, budgets={"max_operations": 100000, "max_elapsed_ms": 30000}))
        save(output / "default-control.receipt.json", failed)
        assert_that(failed["status"] in {"failed", "rejected"}
                    and failed["execution_budget"]["budget_reason"] == "operation_budget_exhausted"
                    and failed["accepted_program_revision"] is None,
                    "Default-control Agent create exhausts its original 100000-operation grant without acceptance")
        with control._store.connection() as db:
            assert_that(db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 0,
                        "Default-control failure publishes no artifact")

        service = BudgetAgentService(Path(live_stores.name) / "store-agent", host_policy=HostPolicy(400000, 80000))
        services.append(service)
        discovered = call(service, request("agent", "discover", profile="planar-reach-budget-0.1", limit=100))
        assert_that(discovered["status"] == "succeeded", "Actual Agent discovery succeeds")
        created = call(service, request("agent", "create", bundle=source.to_payload(),
            expected_program_revision=None, requested_level="constructed"))
        assert_that(created["status"] == "succeeded" and created["accepted_program_revision"] == source.program_revision,
                    "Frozen source is accepted through actual Agent create")
        inspected = call(service, request("agent", "inspect", program_revision=source.program_revision,
            selector={"kind": "source"}, fields=["identity", "source"], limit=100))
        assert_that(inspected["status"] == "succeeded", "Source-unit edit scopes are inspectable")
        rejected = call(service, request("agent", "edit", expected_program_revision=source.program_revision,
            requested_level="constructed", patches=[patch(source, "400000", "400001")]))
        assert_that(rejected["status"] in {"rejected", "failed"}
                    and service.accepted_revision("agent") == source.program_revision,
                    "Unauthorized candidate preserves accepted source")
        repaired = call(service, request("agent", "edit", expected_program_revision=source.program_revision,
            requested_level="constructed", patches=[patch(source, "400000", "300000")]))
        changed_source = ProgramBundle(SourceUnit("entry", source.entry.filename,
            source.entry.raw.replace(b"400000", b"300000")))
        assert_that(repaired["status"] == "succeeded" and repaired["accepted_program_revision"] == changed_source.program_revision,
                    "Exact budget source repair changes immutable revision")
        restored = call(service, request("agent", "edit", expected_program_revision=changed_source.program_revision,
            requested_level="constructed", patches=[patch(changed_source, "300000", "400000")]))
        assert_that(restored["status"] == "succeeded" and restored["accepted_program_revision"] == source.program_revision,
                    "Exact inverse edit restores the frozen source identity")

        evaluation_request = request("agent", "evaluate", program_revision=source.program_revision,
                                     run_id=None, until_seconds="3")
        evaluated = call(service, evaluation_request)
        assert_that(evaluated["status"] == "succeeded", "Saved source evaluates through the Agent")
        retry = call(service, evaluation_request)
        assert_that(retry == evaluated, "Identical retry returns the complete original durable receipt")
        changed = copy.deepcopy(evaluation_request)
        changed["budgets"] = {"max_operations": 300000}
        conflict = call(service, changed)
        assert_that(conflict["status"] == "rejected" and conflict["protocol_error"]["code"] == "OKL-E-REQUEST-ID",
                    "Changed budget under the same identity cannot replay effects")

        service.host_policy = HostPolicy()
        denied = call(service, request("agent", "validate", program_revision=source.program_revision,
                                      requested_level="constructed"))
        assert_that(denied["status"] in {"rejected", "failed"}
                    and denied["execution_budget"]["budget_reason"] == "host_ceiling_exceeded",
                    "A new saved-program request reauthorizes under the current lower host policy")
        reduced = call(service, request("agent", "validate", program_revision=source.program_revision,
            requested_level="constructed", budgets={"max_operations": 100000, "max_elapsed_ms": 30000}))
        assert_that(reduced["status"] == "succeeded", "Explicit caller reductions fit the current host")
        service.host_policy = HostPolicy(400000, 80000)

        exported = call(service, request("agent", "export", program_revision=source.program_revision,
            destination="ontokin.glb/0.7", options=options))
        save(output / "authorized-large.receipt.json", exported)
        assert_that(exported["status"] == "succeeded" and exported["achieved_level"] == "delivered"
                    and exported["result"]["report"]["validation"]["status"] == "passed",
                    "Authorized Agent export completes source evaluation, recording and supplied-byte validation")
        artifact_id = exported["result"]["artifact_id"]
        service.host_policy = HostPolicy()
        denied_artifact = call(service, request("agent", "artifact", artifact_id=artifact_id, max_bytes=65536))
        assert_that(denied_artifact["status"] in {"rejected", "failed"}
                    and denied_artifact["execution_budget"]["budget_reason"] == "host_ceiling_exceeded",
                    "Historical artifact metadata cannot authorize new retrieval")
        service.host_policy = HostPolicy(400000, 80000)
        chunks, offset = [], 0
        while True:
            received = call(service, request("agent", "artifact", artifact_id=artifact_id, offset=offset, max_bytes=65536))
            assert_that(received["status"] == "succeeded", f"Artifact chunk {offset} is newly authorized")
            result = received["result"]
            assert_that(result["program_revision"] == source.program_revision and result["offset"] == offset,
                        f"Artifact chunk {offset} retains its exact program and byte position")
            chunks.append(base64.b64decode(result["data_base64"], validate=True))
            if result["next_offset"] is None:
                break
            offset = result["next_offset"]
        data = b"".join(chunks)
        digest = hashlib.sha256(data).hexdigest()
        assert_that("sha256:" + digest == exported["result"]["sha256"] and len(data) == exported["result"]["total_bytes"],
                    "Actual retrieved Agent bytes match the exact exported artifact")
        (output / "agent-retrieved.glb").write_bytes(data)
        summary["artifact"] = {"path": "agent-retrieved.glb", "bytes": len(data), "sha256": digest,
                               "artifact_id": artifact_id, "program_revision": source.program_revision}

        pending = request("agent", "validate", program_revision=source.program_revision, requested_level="evaluated")
        queued = call(service, pending, wait=False)
        cancelled = call(service, request("agent", "cancel", target_request_id=pending["request_id"]))
        status = call(service, request("agent", "status", target_request_id=pending["request_id"]))
        assert_that(queued["status"] == "queued" and cancelled["status"] == "succeeded"
                    and status["result"]["target_status"] == "cancelled", "Queued cancellation and status execute without replay")
        hostile = call(service, request("agent", "validate", program_revision=source.program_revision,
            requested_level="constructed", host_policy={"max_operations": 900000}))
        assert_that(hostile["status"] == "rejected", "Protocol rejects source-supplied host authority")
        with service._store.connection() as db:
            count = db.execute("SELECT count(*) FROM requests").fetchone()[0]
        distinct = len({(item["request"]["project_id"], item["request"]["request_id"])
                        for item in exchanges if item["request"]["project_id"] == "agent"})
        assert_that(count == distinct, "Every unique Agent request has a durable row")
        source_after = inventory(ROOT)
        save(output / "source-after.json", source_after)
        assert_that(source_after == source_before, "Complete source inputs remain unchanged through acceptance")
        summary["default_operations"] = failed["execution_budget"]["consumed_operations"]
        summary["export_operations"] = exported["execution_budget"]["consumed_operations"]
        summary["status"] = "passed"
    except BaseException as error:
        summary["status"] = "failed"
        summary["failure"] = {"type": type(error).__name__, "message": str(error)}
        (output / "failure.traceback").write_text(traceback.format_exc())
    finally:
        for service in services:
            service.close()
            target = output / service.store_path.name
            target.mkdir(exist_ok=True)
            with sqlite3.connect(service.database_path) as original, sqlite3.connect(target / service.database_path.name) as snapshot:
                original.backup(snapshot)
        live_stores.cleanup()
        transcript.write_text("".join(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n"
                                      for item in exchanges))
        if len(transcript.read_text().splitlines()) != summary["exchanges"]:
            summary["status"] = "failed"
            summary["failure"] = {"type": "TranscriptCountMismatch", "message": "Protocol transcript is incomplete"}
        summary["finished_utc"] = utc()
        if transcript.exists():
            raw = transcript.read_bytes()
            summary["protocol"] = {"path": transcript.name, "bytes": len(raw),
                                   "sha256": hashlib.sha256(raw).hexdigest()}
        save(output / "summary.json", summary)
    print(json.dumps({key: summary.get(key) for key in
        ("status", "exchanges", "default_operations", "export_operations", "artifact", "failure")}))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
