#!/usr/bin/env python3
"""Independently reconcile every A08 exchange with a closed SQLite store.

This standard-library reader imports no OntoKin producer, service, cache or
verification helper. It walks the original raw transcript and requests table
in lockstep, checks every canonical payload and exact stored response, and
reconstructs every artifact/asset range against the actual stored bytes. Only
an explicitly requested incomplete measurement may stop before frozen EOF.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import closing
import gzip
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
FREEZE_SHA = "98df30158c0cd77c542d89652f5dec6b585d03451a06bf7b1baffee0fc2f02eb"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for raw in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(raw)
    return result.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("Duplicate JSON member: " + key)
        value[key] = item
    return value


def nonfinite(value):
    raise ValueError("Nonfinite JSON token: " + value)


def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def read(path):
    return decode(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


class Audit:
    def __init__(self, args):
        self.args = args
        self.checks = 0

    def check(self, condition, message):
        self.checks += 1
        if not condition:
            raise AssertionError(message)

    def nonnegative_integer(self, value, message):
        self.check(type(value) is int and 0 <= value <= 9007199254740991, message)

    def finite_number(self, value, message, *, nonnegative=False):
        self.check(type(value) in (int, float) and -9007199254740991 <= value <= 9007199254740991
                   and math.isfinite(value) and (not nonnegative or value >= 0), message)

    def range_types(self, result):
        self.nonnegative_integer(result["offset"], "Native nonnegative returned offset")
        self.nonnegative_integer(result["total_bytes"], "Native nonnegative returned byte length")
        if result["next_offset"] is not None:
            self.nonnegative_integer(result["next_offset"], "Native nonnegative returned next offset")

    def frozen_payload(self):
        root = self.args.source_root
        frozen = root / "docs/language-design/torque-v0.1/freeze"
        manifest_path = frozen.parent / "INPUT-FREEZE.json"
        self.check(file_digest(manifest_path) == FREEZE_SHA, "Original input manifest identity")
        members = {row["path"]: row for row in read(manifest_path)["files"]}
        materializations = []
        def exact(path):
            raw = path.read_bytes()
            relative = path.resolve().relative_to(root.resolve()).as_posix()
            row = members[relative]
            self.check(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "Exact frozen input " + relative)
            materializations.append({"path": relative, "bytes": len(raw), "sha256": digest(raw)})
            return raw
        table = decode(exact(frozen / "agent/request-workflows.json"))
        scenario = next(row for row in table["scenarios"] if row["id"] == "A08")
        files = decode(exact(frozen / scenario["steps"][0]["request"]["bundle"]["$bundle_file"]))
        entry_raw = exact(frozen / files["entry"]["path"])
        entry = {"filename": files["entry"]["filename"], "source": entry_raw.decode("utf-8")}
        units = [{"filename": entry["filename"], "source_id": "entry", "package_id": None,
                  "version": None, "source_revision": "sha256:"+digest(entry_raw)}]
        modules, assets, asset_bytes = [], [], {}
        for item in files["modules"]:
            raw = exact(frozen / item["path"])
            modules.append({key: item[key] for key in ("filename", "package_id", "version")} | {"source": raw.decode("utf-8")})
            units.append({key: item[key] for key in ("filename", "package_id", "version")} |
                         {"source_id": "package:"+item["package_id"]+"@"+item["version"], "source_revision": "sha256:"+digest(raw)})
        for item in files["assets"]:
            raw = exact(frozen / item["path"])
            self.check("sha256:"+digest(raw) == item["sha256"], "Frozen asset identity")
            asset_bytes[item["asset_id"]] = raw
            assets.append({key: item[key] for key in ("asset_id", "media_type", "sha256")} |
                          {"data_base64": base64.b64encode(raw).decode("ascii")})
        modules.sort(key=lambda item: (item["package_id"], item["version"]))
        assets.sort(key=lambda item: item["asset_id"])
        payload = {"schema_version": "ontokin.bundle/0.2", "entry": entry, "modules": modules, "assets": assets}
        manifest = {"schema_version": "ontokin.bundle/0.2", "entry_source_id": "entry",
                    "units": sorted(units, key=lambda item: item["source_id"]),
                    "assets": [{key: item[key] for key in ("asset_id", "media_type", "sha256")} |
                               {"byte_length": len(asset_bytes[item["asset_id"]])} for item in assets]}
        revision = "sha256:"+digest(b"ontokin.bundle/0.2\0"+canonical(manifest).encode())
        self.check(revision == scenario["steps"][1]["request"]["program_revision"], "Independent domain-separated program revision")
        return scenario, payload, manifest, revision, asset_bytes, materializations

    def run(self):
        args = self.args
        started = time.monotonic()
        run = args.run
        database = run / "store/torque-program-agent.sqlite3"
        transcript = run / "exchanges.jsonl.gz"
        size = read(run / "artifact-size.json")
        self.check(type(size["max_bytes"]) is int and size["max_bytes"] in (1, 17, 65536), "Frozen native integer chunk size")
        self.nonnegative_integer(size["bytes"], "Native original artifact byte length")
        self.nonnegative_integer(size["minimum_requests"], "Native minimum chunk request count")
        # A read-only SQLite observer may leave a -shm index even with an
        # empty WAL. Only WAL/journal bytes can contain unapplied durable data;
        # immutable mode below does not consult or alter that transient index.
        for suffix in ("-wal", "-journal"):
            path = Path(str(database)+suffix)
            self.check(not path.exists() or path.stat().st_size == 0, "Closed store has no unapplied journal: " + suffix)
        database_before = file_digest(database)
        transcript_before = file_digest(transcript)
        scenario, payload, manifest, revision, assets, inputs = self.frozen_payload()
        raw_hash = hashlib.sha256()
        raw_bytes = count = 0
        artifact_offset = artifact_chunks = png_offset = png_chunks = 0
        eof = past_eof = False
        response_chain = hashlib.sha256()
        request_chain = hashlib.sha256()
        with closing(sqlite3.connect(database.as_uri()+"?mode=ro&immutable=1", uri=True)) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA cache_size=-8192")
            self.check(db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "Full closed SQLite integrity")
            metadata = dict(db.execute("SELECT name,value FROM metadata"))
            self.check(metadata["schema_version"] == "ontokin.torque-program-agent-store/0.1", "Independent .22 durable schema")
            counts = {name: db.execute("SELECT COUNT(*) FROM "+name).fetchone()[0]
                      for name in ("projects", "sources", "requests", "runs", "artifacts")}
            self.check(all(counts[name] == 1 for name in ("projects", "sources", "runs", "artifacts")), "Exactly one frozen project/source/run/artifact")
            project, accepted = db.execute("SELECT id,accepted_revision FROM projects").fetchone()
            self.check(project.endswith("-c090-a08") and accepted == revision, "Actual project namespacing and accepted source")
            namespace = project[:-len("c090-a08")]
            source_project, source_revision, stored_raw, accepted_once = db.execute("SELECT project_id,revision,raw,accepted_once FROM sources").fetchone()
            self.check((source_project, source_revision, accepted_once) == (project, revision, 1), "Actual accepted immutable source row")
            self.check(stored_raw == canonical(payload).encode(), "Exact frozen source and asset payload stored without normalization")
            (args.output / "source.bundle.json").write_bytes(stored_raw)
            write(args.output / "source-manifest.json", manifest)
            artifact_project, artifact_id, artifact_revision, artifact, report_text, artifact_sha = db.execute(
                "SELECT project_id,id,source_revision,data,report,sha256 FROM artifacts").fetchone()
            artifact_digest = digest(artifact)
            self.check((artifact_project, artifact_revision, artifact_id, artifact_sha) ==
                       (project, revision, "artifact:"+artifact_digest, "sha256:"+artifact_digest), "Actual full artifact bytes and durable provenance identity")
            self.check(size["bytes"] == len(artifact) and size["sha256"] == artifact_digest, "Recorded loop size equals actual committed artifact")
            self.check(size["minimum_requests"] == (len(artifact)+size["max_bytes"]-1)//size["max_bytes"], "Exact original required chunk count")
            report = decode(report_text)
            self.check(report["program_revision"] == revision, "Artifact report source revision")
            self.check(report["implementation_identity"]["source_code_sha256"] == "sha256:"+report["source_code_sha256"], "Artifact report implementation identities agree")
            implementation = report["implementation_identity"]
            (args.output / "artifact-report.json").write_text(report_text, encoding="utf-8")
            run_project, run_id, run_revision, descriptor_text, run_version = db.execute("SELECT project_id,id,source_revision,descriptor,version FROM runs").fetchone()
            descriptor = decode(descriptor_text)
            self.check(run_project == project and run_revision == revision and run_version == 1
                       and descriptor["run_id"] == run_id and descriptor["program_revision"] == revision,
                       "Actual committed export run identity")
            self.check(canonical(descriptor["implementation"]) == canonical(implementation),
                       "Actual run implementation equals its producer artifact implementation")
            self.check(descriptor["valid_until_seconds"] == scenario["steps"][1]["request"]["options"]["end"]
                       and descriptor["valid_until_side"] == "after", "Actual export prefix ends at original after-side horizon")
            (args.output / "run-descriptor.json").write_text(descriptor_text, encoding="utf-8")
            def concrete(value, *, offset=None, index=None):
                if type(value) is dict:
                    if set(value) == {"$bundle_file"}: return payload
                    if set(value) == {"$response"}: return artifact_id
                    if set(value) == {"$capture"}: return len(artifact)+(1 if value["$capture"].endswith("plus_one") else 0)
                    if set(value) == {"$loop"}: return offset if value["$loop"] == "offset" else index
                    return {key: concrete(item, offset=offset, index=index) for key, item in value.items()}
                if type(value) is list:
                    return [concrete(item, offset=offset, index=index) for item in value]
                if type(value) is str:
                    if index is not None: value = value.replace("${index}", str(index))
                    if value.startswith("c090-"): value = namespace+value
                return value
            loop = next(item for item in scenario["artifact_loops"] if item["max_bytes"] == size["max_bytes"])
            rows = iter(db.execute("SELECT sequence,project_id,id,operation,payload,digest,response,state,cancel_requested,engine FROM requests ORDER BY sequence"))
            with gzip.open(transcript, "rb") as stream:
                # Bound allocation before decoding an untrusted line, including
                # compressed input whose next newline may be arbitrarily far.
                for line in iter(lambda: stream.readline(8*1024*1024+1), b""):
                    self.check(len(line) <= 8*1024*1024 and line.endswith(b"\n"), "Bounded complete original transcript record")
                    raw_hash.update(line)
                    raw_bytes += len(line)
                    count += 1
                    exchange = decode(line)
                    row = next(rows, None)
                    self.check(row is not None, "Every transcript exchange has its own durable request row")
                    sequence, row_project, ident, operation, request_text, request_sha, response_text, state, cancelled, engine = row
                    request, response = exchange["request"], exchange["response"]
                    self.check(type(exchange["index"]) is int and sequence == count == exchange["index"], "Actual sequential request and transcript positions")
                    self.check((row_project, ident, operation) == (request["project_id"], request["request_id"], request["operation"]), "Every stored payload binds its original row identity")
                    self.check(request_text == canonical(request) and digest(request_text.encode()) == request_sha, "Every exact canonical request and SHA equals the durable receipt")
                    self.check("request_canonical_sha256" not in exchange or exchange["request_canonical_sha256"] == request_sha, "Optional historical harness digest matches actual canonical bytes")
                    self.check(response_text == canonical(response), "Every complete response equals its exact durable serialization")
                    self.check(engine == canonical(implementation), "Every durable request is bound to its actual producer implementation")
                    self.check(response["schema_version"] == request["schema_version"] == "ontokin.agent/0.22"
                               and response["project_id"] == row_project == project and response["request_id"] == ident
                               and response["operation"] == operation and response["status"] == state and cancelled == 0,
                               "Every durable request and response retains protocol, identity and terminal state")
                    self.check(response["accepted_program_revision"] == revision and response["program_revision"] == revision,
                               "Every response binds the same actually accepted source")
                    self.check(type(response["truncated"]) is bool, "Native response truncation flag")
                    budget = response["execution_budget"]
                    self.nonnegative_integer(budget["consumed_operations"], "Native nonnegative consumed work")
                    self.finite_number(budget["elapsed_ms"], "Native finite nonnegative elapsed time", nonnegative=True)
                    self.finite_number(budget["started_monotonic_seconds"], "Native finite original start clock")
                    self.finite_number(budget["deadline_monotonic_seconds"], "Native finite original deadline clock")
                    self.check(budget["implementation"] == implementation and budget["request_id"] == ident
                               and budget["program_revision"] == revision
                               and canonical(budget["effective"]) == '{"max_elapsed_ms":30000,"max_operations":1000000}'
                               and canonical(budget["host_ceilings"]) == '{"max_elapsed_ms":30000,"max_operations":1000000}'
                               and canonical(budget["defaults"]) == '{"max_elapsed_ms":30000,"max_operations":100000}'
                               and canonical(budget["source_request"]) == '{"max_elapsed_ms":30000,"max_operations":1000000}'
                               and canonical(budget["caller_caps"]) == "{}" and budget["status"] == state
                               and budget["provisional"] is False
                               and budget["entry_revision"] == next(unit["source_revision"] for unit in manifest["units"] if unit["source_id"] == "entry"),
                               "Every actual request retains frozen allocation, inherited defaults and implementation")
                    self.check(budget["deadline_monotonic_seconds"] == budget["started_monotonic_seconds"]+30,
                               "Original request deadline retains the frozen elapsed allowance")
                    if state == "succeeded":
                        self.check(budget["consumed_operations"] <= budget["effective"]["max_operations"]
                                   and budget["elapsed_ms"] <= budget["effective"]["max_elapsed_ms"]
                                   and budget["budget_reason"] is None,
                                   "Every successful request fits its own unchanged actual allocation")
                    request_chain.update(request_text.encode()+b"\n")
                    response_chain.update(response_text.encode()+b"\n")
                    if count <= 2:
                        self.check(canonical(request) == canonical(concrete(scenario["steps"][count-1]["request"])), "Exact original setup request")
                        self.check(state == "succeeded", "Actual setup succeeded")
                        if count == 1:
                            self.check(response["achieved_level"] == "constructed", "Actual source construction")
                        else:
                            self.check(response["result"]["artifact_id"] == artifact_id and report["producer_request_id"] == ident,
                                       "Actual export identifies its own immutable artifact and receipt")
                    elif artifact_offset < len(artifact):
                        self.check(canonical(request) == canonical(concrete(loop["request_template"], offset=artifact_offset, index=artifact_chunks)), "Every frozen chunk request uses actual decoded sequential offset")
                        result = response["result"]
                        self.range_types(result)
                        chunk = base64.b64decode(result["data_base64"], validate=True)
                        end = min(len(artifact), artifact_offset+size["max_bytes"])
                        self.check(state == "succeeded" and chunk == artifact[artifact_offset:end] and bool(chunk), "Every actual artifact range equals stored bytes")
                        self.check(result["artifact_id"] == artifact_id and result["offset"] == artifact_offset
                                   and result["total_bytes"] == len(artifact) and result["sha256"] == artifact_sha
                                   and result["program_revision"] == revision and result["producer_request_id"] == report["producer_request_id"],
                                   "Every returned range preserves complete artifact identity")
                        artifact_offset += len(chunk)
                        artifact_chunks += 1
                        self.check(result["next_offset"] == (artifact_offset if artifact_offset < len(artifact) else None)
                                   and response["truncated"] == (artifact_offset < len(artifact)), "Actual next offset and final-chunk semantics")
                    elif not eof:
                        self.check(canonical(request) == canonical(concrete(scenario["eof_request"])), "Exact frozen EOF request")
                        self.range_types(response["result"])
                        self.check(state == "succeeded" and response["result"]["data_base64"] == ""
                                   and response["result"]["next_offset"] is None and response["truncated"] is False,
                                   "Exact successful empty EOF response")
                        self.check(response["result"]["artifact_id"] == artifact_id and response["result"]["sha256"] == artifact_sha
                                   and response["result"]["total_bytes"] == len(artifact) and response["result"]["offset"] == len(artifact),
                                   "EOF response preserves the same complete artifact identity")
                        eof = True
                    elif not past_eof:
                        self.check(canonical(request) == canonical(concrete(scenario["past_eof_request"])), "Exact frozen past-EOF request")
                        self.check(state == "rejected" and response["protocol_error"]["code"] == "OKA-E-ARTIFACT", "Exact past-EOF refusal")
                        past_eof = True
                    else:
                        asset = scenario["asset_loop"]
                        raw = assets["label"]
                        self.check(png_offset < len(raw), "No extra requests after complete frozen workflow")
                        self.check(canonical(request) == canonical(concrete(asset["request_template"], offset=png_offset, index=png_chunks)), "Every exact frozen PNG slice request")
                        result = response["result"]
                        self.range_types(result)
                        chunk = base64.b64decode(result["data_base64"], validate=True)
                        end = min(len(raw), png_offset+asset["request_template"]["asset_slice"]["max_bytes"])
                        self.check(state == "succeeded" and chunk == raw[png_offset:end] and bool(chunk), "Every actual PNG range equals frozen original bytes")
                        self.check(result["total_bytes"] == asset["total_bytes"] == len(raw) and result["sha256"] == asset["sha256"]
                                   and result["offset"] == png_offset and result["source_manifest"] == manifest, "Every PNG response binds exact source and asset identity")
                        png_offset += len(chunk)
                        png_chunks += 1
                        self.check(result["next_offset"] == (png_offset if png_offset < len(raw) else None), "Exact asset next offset")
                    if count % 100000 == 0:
                        print(json.dumps({"audited_requests": count, "elapsed_seconds": time.monotonic()-started}), flush=True)
                self.check(next(rows, None) is None, "Every durable row has one complete original transcript exchange")
            self.check(count == counts["requests"], "Exact full row count reconciled")
        complete = artifact_offset == len(artifact) and eof and past_eof and png_offset == len(assets["label"])
        self.check(complete or args.allow_incomplete, "All required chunk/EOF/PNG requests executed")
        retrieved = run / "retrieved.glb"
        self.check(retrieved.read_bytes() == artifact[:artifact_offset], "Exact independently reconstructed retained GLB bytes")
        if complete:
            self.check((run / "retrieved-label.png").read_bytes() == assets["label"], "Exact independently reconstructed retained PNG bytes")
            completion_path = run / "artifact-completion.json"
            if completion_path.exists():
                completion = read(completion_path)
                self.check(completion["status"] == "passed" and completion["actual_exchanges"] == count
                           and completion["durable_request_rows"] == count, "Actual completion receipt agrees with independently reconciled full SQLite")
        else:
            self.check(artifact_offset < len(artifact) and png_chunks == 0 and not eof and not past_eof,
                       "Incomplete evidence is only an explicitly bounded prefix of the original loop")
        self.check(file_digest(database) == database_before and file_digest(transcript) == transcript_before,
                   "Independent read-only audit leaves original SQLite and compressed transcript byte-identical")
        result = {"schema_version": "ontokin.c091-independent-a08-audit/1", "status": "passed", "complete_frozen_loop": complete,
            "checks": self.checks, "elapsed_seconds": time.monotonic()-started, "argv": sys.argv,
            "auditor_sha256": file_digest(Path(__file__)), "python": sys.version,
            "original_database": {"path": str(database), "sha256": database_before, "bytes": database.stat().st_size,
                                  "read_only": True, "integrity": "ok", "counts": counts},
            "transcript": {"path": str(transcript), "compressed_sha256": transcript_before, "compressed_bytes": transcript.stat().st_size,
                           "raw_sha256": raw_hash.hexdigest(), "raw_bytes": raw_bytes, "records": count},
            "request_payloads_sha256": request_chain.hexdigest(), "response_serializations_sha256": response_chain.hexdigest(),
            "program_revision": revision, "implementation_identity": implementation, "source_inputs": inputs,
            "artifact": {"id": artifact_id, "sha256": artifact_sha, "bytes": len(artifact), "report_sha256": digest(report_text.encode()),
                         "max_bytes": size["max_bytes"], "chunk_requests": artifact_chunks, "retrieved_bytes": artifact_offset,
                         "eof_executed": eof, "past_eof_executed": past_eof},
            "asset": {"sha256": scenario["asset_loop"]["sha256"], "chunk_requests": png_chunks, "retrieved_bytes": png_offset},
            "scope": "Every original materialized request and response is reconciled exactly to its own closed durable row; every original artifact/asset range and full source closure is checked independently. This receipt does not reconstruct the original SQLite file from the transcript."}
        write(args.output / "AUDIT.json", result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--allow-incomplete", action="store_true", help="Audit an explicit measurement prefix without claiming full frozen-loop completion")
    args = parser.parse_args()
    args.run = args.run.resolve()
    args.output = args.output.resolve()
    args.output.mkdir()
    auditor = Audit(args)
    try:
        result = auditor.run()
        print(json.dumps({key: result[key] for key in ("status", "complete_frozen_loop", "checks", "elapsed_seconds")}), flush=True)
        return 0
    except BaseException as error:
        write(args.output / "FAILED.json", {"status": "failed", "checks": auditor.checks, "error": repr(error),
                                           "traceback": traceback.format_exc(), "argv": sys.argv,
                                           "auditor_sha256": file_digest(Path(__file__))})
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
