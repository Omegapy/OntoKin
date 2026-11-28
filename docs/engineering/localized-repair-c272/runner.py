#!/usr/bin/env python3
"""C272 runner: drive the real Agent/0.2 service with a scripted client for C253 V1, V2 and N1.

The runner is the external harness. It imports the product only to drive it. It
judges nothing; the separate evaluator modules, which import no product code,
judge the bytes that this runner retains.

For every case:
- the frozen inputs are checked against the C253 corpus before the service is called;
- a new, empty store is used;
- every request and response is appended to an external record as it happens;
- the accepted program is read back through the service;
- the accepted-state record is written from the actual responses and retrieved bytes.

The record lives outside both the store and the client's directory.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
CORPUS = "docs/engineering/localized-repair-c253/corpus.json"
PROTOCOL = "ontokin.agent/0.2"
DESTINATION = "ontokin.glb/0.2"
EXPORT_OPTIONS = {"helpers": False}
SIDECAR_FEATURES = ["stable_identities", "dimensions_units_frames"]
GLB_NAME, SIDECAR_NAME = "scene.glb", "scene.semantic.json"
TARGET_PATH = 'first.fingers["middle"].length'
CHUNK = 65536
CASES = ("V1", "V2", "N1")
SCRIPTED_CLIENT = "c272 scripted client: fixed requests from this file and the frozen C253 corpus; no model"
NOT_APPLICABLE = "not applicable to a scripted client"


class InputMismatch(Exception):
    """A frozen input does not match its C253 corpus binding; the service is not called."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def corpus_inputs(case_id: str, read=lambda path: (ROOT / path).read_bytes()) -> dict:
    """Read and verify the case's frozen files against the corpus, before any service call."""
    manifest = json.loads(read(CORPUS))
    task = next(t for t in manifest["tasks"] if t["id"] == case_id)
    names = {"start": task["startEntry"], "bundle": task["startBundle"], "hinges": "hinges",
             "candidate": task.get("existingTargetEntry") or task["existingCandidateEntry"]}
    files = {}
    for role, name in names.items():
        binding = manifest["files"][name]
        raw = read(binding["path"])
        if len(raw) != binding["bytes"] or sha256(raw) != binding["sha256"]:
            raise InputMismatch(f"{case_id}: {name} ({binding['path']}) does not match its corpus SHA-256")
        files[role] = raw
    bundle = json.loads(files["bundle"])
    if (bundle["entry"]["source"].encode("utf-8") != files["start"] or len(bundle["modules"]) != 1
            or bundle["modules"][0]["source"].encode("utf-8") != files["hinges"]):
        raise InputMismatch(f"{case_id}: the corpus bundle does not carry the frozen entry and library bytes")
    patch = task["patch"]
    if files["start"][patch["startByte"]:patch["endByteExclusive"]] != patch["expectedText"].encode():
        raise InputMismatch(f"{case_id}: the corpus patch does not match the start bytes")
    return {"task": task, "files": files, "bundle": bundle, "names": names,
            "bindings": {role: manifest["files"][name] for role, name in names.items()}}


class Record:
    """Append-only external exchange record; each line is written before the next request."""

    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True)
        (directory / "files").mkdir()
        self.log = directory / "exchanges.jsonl"
        self.sequence = 0

    def append(self, kind: str, body: dict) -> None:
        self.sequence += 1
        line = {"sequence": self.sequence, "time_unix": round(time.time(), 6), "kind": kind, **body}
        with self.log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n")
            handle.flush()

    def keep(self, state: str, name: str, raw: bytes) -> dict:
        path = self.directory / "files" / state / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {"file": f"files/{state}/{name}", "bytes": len(raw), "sha256": sha256(raw)}

    def write_json(self, name: str, value) -> None:
        (self.directory / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def summarize(response: dict) -> dict:
    """Retain a response with artifact chunk data replaced by its size and digest."""
    kept = copy.deepcopy(response)
    result = kept.get("result")
    if isinstance(result, dict) and "data_base64" in result:
        raw = base64.b64decode(result.pop("data_base64"), validate=True)
        result["omitted_chunk"] = {"bytes": len(raw), "sha256": sha256(raw)}
    return kept


class Client:
    """The scripted client: it authors fixed requests and sends them through the harness."""

    def __init__(self, service, project: str, record: Record, client_dir: Path, case_id: str):
        self.service, self.project, self.record = service, project, record
        self.client_dir, self.case_id, self.serial = client_dir, case_id, 0
        client_dir.mkdir(parents=True)

    def send(self, request: dict, label: str) -> dict:
        (self.client_dir / f"{self.serial:03d}-{label}.json").write_text(json.dumps(request, indent=2) + "\n")
        self.record.append("request", {"label": label, "request": request})
        response = self.service.handle(request)
        accepted = self.service.accepted_revision(self.project)
        self.record.append("response", {"label": label, "response": summarize(response),
                                        "store_accepted_revision_after": accepted})
        return response

    def call(self, operation: str, label: str | None = None, **fields) -> tuple[dict, dict]:
        self.serial += 1
        request = {"schema_version": PROTOCOL, "project_id": self.project,
                   "request_id": f"c272-{self.case_id}-{self.serial:03d}-{operation}", "operation": operation, **fields}
        return self.send(request, label or operation), request

    def retrieve(self, artifact_id: str, label: str) -> tuple[bytes, list[dict]]:
        data, offset, responses = bytearray(), 0, []
        while offset is not None:
            response, _ = self.call("artifact", label, artifact_id=artifact_id, offset=offset, max_bytes=CHUNK)
            if response["status"] != "succeeded" or response["result"]["offset"] != len(data):
                raise RuntimeError(f"artifact retrieval failed: {summarize(response)}")
            data.extend(base64.b64decode(response["result"]["data_base64"], validate=True))
            responses.append(response)
            offset = response["result"]["next_offset"]
        return bytes(data), responses

    def export(self, revision: str, label: str) -> tuple[bytes, dict]:
        response, _ = self.call("export", label, program_revision=revision, destination=DESTINATION,
                                options=copy.deepcopy(EXPORT_OPTIONS))
        if response["status"] != "succeeded":
            raise RuntimeError(f"export failed: {summarize(response)}")
        data, chunks = self.retrieve(response["result"]["artifact_id"], label + "-artifact")
        provenance = chunks[-1]["result"].get("artifact_provenance")
        return data, {"artifact_id": response["result"]["artifact_id"], "report": response["result"]["report"],
                      "artifact_provenance": provenance, "chunk_program_revisions": sorted({c["result"]["program_revision"] for c in chunks})}


def program_files(program) -> dict:
    files = {program.entry.filename: program.entry.raw}
    for module in program.modules:
        files[module.filename] = module.raw
    return files


def sidecar(program, glb: bytes, accepted: str) -> bytes:
    from ontokin.semantic_export import build_semantic_manifest, canonical_bytes
    return canonical_bytes(build_semantic_manifest(program, glb, accepted_program_revision=accepted,
                                                   required_features=SIDECAR_FEATURES))


def accepted_identity(revision: str) -> str:
    """The harness's accepted-record identity: the service's accepted pointer, as observed."""
    return "agent0.2-accepted:" + revision


def translate_diagnostic(diagnostics: list[dict]) -> tuple[dict | None, dict]:
    """Map the service's actual unit diagnostic to C255's form; refuse anything else."""
    units = [d for d in diagnostics if d.get("code") == "OKL-E-UNIT"]
    rule = {"rule": "OKL-E-UNIT with details.expected 'Length' and details.actual 'Mass', from the reference "
                    "implementation's type phase, is C255's incompatible-dimension diagnostic with mechanism 'compiler'.",
            "service_diagnostics": diagnostics}
    if len(units) != 1:
        return None, {**rule, "translated": False, "reason": "no single OKL-E-UNIT diagnostic"}
    d = units[0]
    if d.get("details") != {"expected": "Length", "actual": "Mass"} or d.get("phase") != "type":
        return None, {**rule, "translated": False, "reason": "details or phase differ"}
    return ({"code": "incompatible-dimension", "expectedDimension": "length", "receivedDimension": "mass",
             "mechanism": "compiler", "message": d["message"]}, {**rule, "translated": True})


def run_case(case_id: str, out: Path, service_factory=None, read=None, label: str | None = None, variant=None) -> dict:
    """Run one case into OUT/cases/LABEL; the record survives every failure.

    VARIANT, used only by evaluator controls, maps (edit_patch, start_program) to the
    patch list that the scripted client submits instead of the corpus patch.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from ontokin.program_agent import ProgramAgentService  # the product under test
    service_factory = service_factory or (lambda store: ProgramAgentService(store, protocol=PROTOCOL))
    base = out / "cases" / (label or case_id)
    base.mkdir(parents=True)
    record = Record(base / "record")
    outcome = {"schema": "ontokin.c272.case-outcome/1", "caseId": case_id, "status": "started",
               "client": SCRIPTED_CLIENT, "steps": [], "protocol_cases": []}
    record.append("case-start", {"caseId": case_id})
    try:
        inputs = corpus_inputs(case_id, **({"read": read} if read else {}))
        record.append("inputs-verified", {"bindings": inputs["bindings"]})
        task, files = inputs["task"], inputs["files"]
        store = base / "store"
        if store.exists():
            raise RuntimeError("store must be new")
        with service_factory(store) as service:
            client = Client(service, f"c272-{case_id.lower()}", record, base / "client", case_id)
            outcome["implementation"] = copy.deepcopy(service.implementation)
            created, _ = client.call("create", bundle=inputs["bundle"], expected_program_revision=None,
                                     requested_level="evaluated")
            if created["status"] != "succeeded":
                raise RuntimeError(f"create failed: {summarize(created)}")
            start_revision = created["program_revision"]
            if service.accepted_revision(client.project) != start_revision or created["accepted_program_revision"] != start_revision:
                raise RuntimeError("the accepted pointer differs from the created revision")
            start_program = service.read_program(client.project, start_revision)
            start_files = program_files(start_program)
            outcome["steps"].append({"step": "start-accepted", "program_revision": start_revision,
                                     "source": {n: record.keep("start", n, b) for n, b in start_files.items()}})
            glb, export = client.export(start_revision, "export-baseline")
            semantic = sidecar(start_program, glb, service.accepted_revision(client.project))
            start_artifacts = {GLB_NAME: glb, SIDECAR_NAME: semantic}
            outcome["steps"].append({"step": "baseline-delivered", "export": export,
                                     "artifacts": {n: record.keep("start", n, b) for n, b in start_artifacts.items()}})
            inspected, _ = client.call("inspect", program_revision=start_revision, selector={"path": TARGET_PATH},
                                       fields=["identity", "source", "values"], limit=1)
            target = inspected["result"]["items"][0]["source"]["initializer_target"]
            if not target.get("available"):
                raise RuntimeError("the occurrence initializer target is not available")
            patch = task["patch"]
            edit_patch = {"source_id": "entry", "source_revision": start_program.entry.revision,
                          "element_id": target["element_id"], "start_byte": patch["startByte"],
                          "end_byte": patch["endByteExclusive"], "expected_text": patch["expectedText"],
                          "replacement": patch["replacement"]}
            patches = variant(edit_patch, start_program) if variant else [edit_patch]
            outcome["variant"] = None if variant is None else patches
            edited, edit_request = client.call("edit", expected_program_revision=start_revision,
                                               requested_level="evaluated", patches=patches)
            candidate_revision = edited.get("program_revision")
            candidate_program = service.read_program(client.project, candidate_revision) if candidate_revision else None
            candidate_files = program_files(candidate_program) if candidate_program else {}
            outcome["steps"].append({"step": "edit", "status": edited["status"], "candidate_program_revision": candidate_revision,
                                     "accepted_program_revision": edited.get("accepted_program_revision"),
                                     "candidate_source": {n: record.keep("candidate", n, b) for n, b in candidate_files.items()}})
            # Executed protocol cases: identical retry, changed-payload retry and a stale-revision edit.
            retry = client.send(edit_request, "retry-identical")
            outcome["protocol_cases"].append({"case": "identical retry", "status": retry["status"],
                                              "equal_to_first_response": retry == edited})
            changed = copy.deepcopy(edit_request)
            changed["patches"][0]["replacement"] = "0.85[m]"
            changed_response = client.send(changed, "retry-changed-payload")
            outcome["protocol_cases"].append({"case": "changed-payload retry", "status": changed_response["status"],
                                              "protocol_error": changed_response.get("protocol_error")})
            if case_id != "N1":
                stale, _ = client.call("edit", "edit-stale-revision", expected_program_revision=start_revision,
                                       requested_level="evaluated", patches=[{**edit_patch, "replacement": "0.85[m]"}])
                outcome["protocol_cases"].append({"case": "stale-revision edit", "status": stale["status"],
                                                  "accepted_program_revision": stale.get("accepted_program_revision"),
                                                  "protocol_error": stale.get("protocol_error"),
                                                  "diagnostic_codes": [d.get("code") for d in stale.get("diagnostics") or []]})
            final_revision = service.accepted_revision(client.project)
            final_program = service.read_program(client.project, final_revision)
            final_files = program_files(final_program)
            if case_id == "N1":
                again, _ = client.retrieve(export["artifact_id"], "artifact-after-rejection")
                final_artifacts = {GLB_NAME: again, SIDECAR_NAME: sidecar(final_program, again, final_revision)}
                candidate_artifacts = {}
            else:
                final_glb, final_export = client.export(final_revision, "export-delivered")
                final_artifacts = {GLB_NAME: final_glb, SIDECAR_NAME: sidecar(final_program, final_glb, final_revision)}
                candidate_artifacts = final_artifacts if candidate_revision == final_revision else {}
                outcome["steps"].append({"step": "delivered", "export": final_export})
            outcome["steps"].append({"step": "retained", "accepted_program_revision": final_revision,
                                     "source": {n: record.keep("retained", n, b) for n, b in final_files.items()},
                                     "artifacts": {n: record.keep("retained", n, b) for n, b in final_artifacts.items()}})
            for name, raw in candidate_artifacts.items():
                record.keep("candidate", name, raw)
            diagnostic, translation = (translate_diagnostic(edited.get("diagnostics") or []) if case_id == "N1" else (None, None))
            accepted_seen = sorted({r["store_accepted_revision_after"] for r in read_lines(record.log) if r["kind"] == "response"})
            decision = {"status": "accepted" if edited["status"] == "succeeded" and final_revision == candidate_revision else "rejected",
                        "candidateId": candidate_revision or "none",
                        "parentAcceptedRevision": accepted_identity(start_revision),
                        "acceptedRevision": accepted_identity(final_revision),
                        "boundary": "staged-before-accepted-replacement",
                        "invalidEverAccepted": case_id == "N1" and candidate_revision in accepted_seen,
                        "diagnostic": diagnostic}
            authority = {"schema": "ontokin.c255.inert-authority/0.1", "attemptId": f"c272-{case_id}",
                         "caseId": case_id,
                         "start": {"acceptedRevision": accepted_identity(start_revision), "programRevision": start_revision,
                                   "sourceFiles": start_files, "artifacts": start_artifacts},
                         "candidate": {"candidateId": candidate_revision or "none",
                                       "parentAcceptedRevision": accepted_identity(start_revision),
                                       "sourceFiles": candidate_files, "artifacts": candidate_artifacts},
                         "retained": {"acceptedRevision": accepted_identity(final_revision), "programRevision": final_revision,
                                      "sourceFiles": final_files, "artifacts": final_artifacts},
                         "decision": decision}
            record.write_json("authority.json", encode_authority(authority))
            record.write_json("accepted-state.json", {
                "schema": "ontokin.c272.accepted-state/1", "caseId": case_id,
                "derived_from": "the service's actual responses, its accepted pointer read after every request, and the retrieved bytes",
                "starting_accepted_revision": start_revision, "candidate_id": candidate_revision,
                "candidate_parent_revision": edit_request["expected_program_revision"],
                "new_accepted_revision": final_revision if final_revision != start_revision else None,
                "accepted_revisions_observed_after_each_request": accepted_seen,
                "hashes": {state: {n: sha256(b) for n, b in m.items()} for state, m in
                           (("start.source", start_files), ("start.artifacts", start_artifacts),
                            ("candidate.source", candidate_files), ("retained.source", final_files),
                            ("retained.artifacts", final_artifacts))},
                "diagnostic_translation": translation,
                "tools": {"implementation": service.implementation, "python": platform.python_version(),
                          "platform": f"{platform.system()} {platform.machine()}",
                          "runner_sha256": sha256(Path(__file__).read_bytes())},
                "export_options": EXPORT_OPTIONS, "destination": DESTINATION, "protocol": PROTOCOL,
                "model": NOT_APPLICABLE, "model_settings": NOT_APPLICABLE, "token_usage": NOT_APPLICABLE,
                "limit": "Acceptance is observed at each response and at the accepted pointer after each request; "
                         "the store keeps no history between them."})
            outcome["status"] = "completed"
    except InputMismatch as error:
        outcome.update(status="input_mismatch", error=str(error))
    except Exception as error:  # A crash keeps its record; nothing is removed or replaced.
        outcome.update(status="crash", error=f"{type(error).__name__}: {error}", traceback=traceback.format_exc())
    record.append("case-end", {"status": outcome["status"]})
    record.write_json("outcome.json", outcome)
    return outcome


def read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def encode_authority(authority: dict) -> dict:
    """C255's CLI transport: every byte map as lowercase hex envelopes."""
    encoded = copy.deepcopy({k: v for k, v in authority.items() if k not in ("start", "candidate", "retained")})
    for state in ("start", "candidate", "retained"):
        row = dict(authority[state])
        for field in ("sourceFiles", "artifacts"):
            row[field] = {n: {"encoding": "hex", "data": b.hex()} for n, b in row[field].items()}
        encoded[state] = row
    return encoded


def run_all(out: Path, cases=CASES) -> list[dict]:
    if out.exists() and any(out.iterdir()):
        raise SystemExit("the output directory must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    return [run_case(case, out) for case in cases]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--case", choices=CASES, action="append")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.is_relative_to(ROOT):
        parser.error("the output directory must lie outside the checkout")
    results = run_all(out, tuple(args.case or CASES))
    print(json.dumps([{k: r.get(k) for k in ("caseId", "status", "error")} for r in results], indent=2))
    return 0 if all(r["status"] == "completed" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
