#!/usr/bin/env python3
"""Produce actual C080 evidence from the frozen corpus and public product APIs.

This driver is deliberately separate from texture_reference: product imports
below produce observations only. Frozen inputs and the independent readers
define expected answers. Run in a new evidence directory outside the checkout.
Fault injection is confined to fresh files/stores and is recorded explicitly.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import threading
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.texture_reference import (FREEZE_COMMIT, FREEZE_SHA256, PROFILE,
    PROTOCOL, TARGET, bundle_identity, canonical, case_payload, case_root, digest, file_payload,
    load_fixtures, sha)

OPTIONS = {"fps": 4, "end": "1", "helpers": False}
DEFAULT_POLICY = {"max_operations": 100000, "max_elapsed_ms": 30000}
MAXIMUM_POLICY = {"max_operations": 2000000, "max_elapsed_ms": 80000}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8")


def codes(value):
    found = []
    if isinstance(value, dict):
        if isinstance(value.get("code"), str):
            found.append(value["code"])
        for child in value.values():
            found.extend(codes(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(codes(child))
    return sorted(set(found))


def error_record(error):
    if hasattr(error, "to_dict"):
        return error.to_dict()
    if hasattr(error, "diagnostic"):
        item = error.diagnostic
        return {"code": item.code, "message": item.message,
                "details": item.details, "phase": item.phase}
    return {"exception": type(error).__name__, "message": str(error),
            "traceback": traceback.format_exc()}


def git(command):
    result = subprocess.run(["git", *command], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=True)
    return result.stdout.strip()


def inventory(root):
    return [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
             "sha256": sha(p.read_bytes())}
            for p in sorted(root.rglob("*")) if p.is_file() and not p.is_symlink()
            and p.name != "inventory.json" and "live-store" not in p.parts]


class Acceptance:
    def __init__(self, fixtures, output):
        # Imports are inside the producer, never inside independent expectations.
        from ontokin.texture_bundle import load_texture_bundle, load_texture_file_manifest
        from ontokin.bundle import load_file_manifest
        from ontokin.budget_runtime import execute_texture_export, execute_pockets_export
        from ontokin.execution_budget import HostPolicy
        from ontokin.scene import ExportOptions
        from ontokin.texture_agent import TextureAgentService
        self.load_bundle = load_texture_bundle
        self.load_files = load_texture_file_manifest
        self.load_legacy_files = load_file_manifest
        self.execute = execute_texture_export
        self.execute_control = execute_pockets_export
        self.HostPolicy, self.ExportOptions = HostPolicy, ExportOptions
        self.Service = TextureAgentService
        self.fixtures, self.output = fixtures, output
        self.fixture_root = fixtures["root"]
        self.serial, self.transcript, self.service = 0, [], None
        self.project, self.scenario = "", None
        self.summary = {"schema_version": "ontokin.c080-actual-evidence/0.1",
            "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
            "command": [sys.executable, *sys.argv], "python": sys.version,
            "platform": platform.platform(), "frozen_input_commit": FREEZE_COMMIT,
            "frozen_manifest_sha256": FREEZE_SHA256,
            "input_corpus_version": fixtures["corpus_version"],
            "correction_manifest_sha256": fixtures.get("correction_manifest_sha256"),
            "correction_input_commit": fixtures.get("correction_input_commit"),
            "git": {"commit": git(["rev-parse", "HEAD"]),
                    "tree": git(["rev-parse", "HEAD^{tree}"]),
                    "status": git(["status", "--porcelain"])},
            "profile": PROFILE, "target_contract": TARGET, "agent_contract": PROTOCOL,
            "cases": [], "controls": [], "transport": [], "file_transport": [],
            "workflows": [], "asset_slice_probes": [], "envelope_boundaries": [],
            "agent_artifacts": [], "hostile_glbs": [], "supplied_glb_positive_controls": [],
            "failures": [], "release_acceptance": False,
            "independent_verification": "not_run_by_this_producer",
            "destination_verification": "not_run_by_this_producer"}
        self.options = self.ExportOptions(**OPTIONS)
        self.schema_validators = self.schemas()

    def schemas(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        directory = ROOT / "docs/language-design/agent-v0.13"
        paths = sorted(directory.glob("*.schema.json"))
        if not paths:
            raise RuntimeError("The actual Agent/0.13 schemas must exist before acceptance")
        all_paths = sorted((ROOT / "docs/language-design").rglob("*.schema.json"))
        resources = {}
        for path in all_paths:
            value = json.loads(path.read_bytes())
            if "$id" in value:
                resources[value["$id"]] = Resource.from_contents(value)
        registry = Registry().with_resources(resources.items())
        result, records = {}, []
        for path in paths:
            value = json.loads(path.read_bytes())
            Draft202012Validator.check_schema(value)
            result[path.name] = Draft202012Validator(value, registry=registry)
            records.append({"path": path.relative_to(ROOT).as_posix(),
                            "sha256": sha(path.read_bytes()), "id": value.get("$id")})
        save(self.output / "schema-inventory.json", {"schemas": records,
             "jsonschema_version": importlib.metadata.version("jsonschema"),
             "referencing_version": importlib.metadata.version("referencing")})
        return result

    def check(self, value, label):
        if not value:
            raise AssertionError(label)

    def payload(self, name):
        return case_payload(self.fixtures, self.fixtures["cases"][name])

    def run_sources(self):
        controls = {}
        for case in self.fixtures["expected"]["cases"]:
            record = {"id": case["id"], "name": case["name"],
                      "source": case["source"], "file_manifest": case["file_manifest"],
                      "expected_outcome": case["expected_outcome"],
                      "expected_code": case["expected_code"], "expected_stage": case["expected_stage"],
                      "host_policy": case["host_policy"]}
            prefix = "sources/" + case["name"]
            try:
                source = self.load_files(case_root(self.fixtures, case) / case["file_manifest"])
                result = self.execute(source, policy=self.HostPolicy(**case["host_policy"]), options=self.options)
                record.update(program_revision=source.program_revision,
                              receipt=prefix + ".receipt.json", delivered=result.data is not None)
                save(self.output / record["receipt"], result.report)
                record["diagnostic_codes"] = codes(result.report)
                if result.data is not None:
                    record.update(glb=prefix + ".glb", bytes=len(result.data), sha256=sha(result.data))
                    (self.output / record["glb"]).write_bytes(result.data)
                if case["expected_outcome"] == "valid":
                    self.check(result.data is not None, case["name"] + " must deliver")
                    name = case["untextured_control"]["file_manifest"]
                    if name not in controls:
                        legacy = self.load_legacy_files(case_root(self.fixtures, case) / name)
                        control = self.execute_control(legacy, policy=self.HostPolicy(), options=self.options)
                        stem = "controls/" + Path(name).stem
                        save(self.output / (stem + ".receipt.json"), control.report)
                        self.check(control.data is not None, name + " must deliver actual .12 control")
                        (self.output / (stem + ".glb")).write_bytes(control.data)
                        controls[name] = {"file_manifest": name, "program_revision": legacy.program_revision,
                            "receipt": stem + ".receipt.json", "glb": stem + ".glb",
                            "bytes": len(control.data), "sha256": sha(control.data)}
                        self.summary["controls"].append(controls[name])
                    record["control"] = controls[name]["glb"]
                else:
                    self.check(result.data is None, case["name"] + " must refuse without artifact")
                    self.check(case["expected_code"] in record["diagnostic_codes"],
                               case["name"] + " requires exact frozen diagnostic")
                    if case["expected_code"] != "OKL-E-RESOURCE":
                        self.check("OKL-E-RESOURCE" not in record["diagnostic_codes"],
                                   "Resource exhaustion cannot substitute for semantic refusal")
                record["producer_status"] = "observed_as_expected"
            except Exception as error:
                record["producer_status"] = "failed"
                record["exception"] = error_record(error)
                self.summary["failures"].append({"scope": "source", "name": case["name"], "error": str(error)})
            self.summary["cases"].append(record)
            save(self.output / "summary.json", self.summary)

    def rejection_probe(self, group, name, expected_code, action, **details):
        record = {"name": name, "expected_code": expected_code, **details}
        try:
            action()
        except Exception as error:
            record["exception"] = error_record(error)
            record["actual_codes"] = codes(record["exception"])
            record["status"] = "observed_as_expected" if expected_code in record["actual_codes"] else "failed"
        else:
            record.update(status="failed", actual_codes=[], unexpected_acceptance=True)
        self.summary[group].append(record)
        if record["status"] == "failed":
            self.summary["failures"].append({"scope": group, "name": name, "error": record})
        return record

    def run_transport(self):
        for case in self.fixtures["transport"]:
            value = json.loads((self.fixture_root / case["payload"]).read_bytes())
            self.rejection_probe("transport", case["name"], case["expected_code"],
                lambda value=value: self.load_bundle(value), payload=case["payload"],
                expected_stage=case["expected_stage"])
        for case in self.fixtures["file_transport"]["cases"]:
            self.rejection_probe("file_transport", case["name"], case["expected_code"],
                lambda case=case: self.load_files(self.fixture_root / case["file_manifest"]),
                file_manifest=case["file_manifest"], expected_stage=case["expected_stage"])
        isolated = self.output / "file-probes"
        isolated.mkdir()
        manifest = json.loads((self.fixture_root / "rgb-panel.files.json").read_bytes())
        manifest["entry"]["path"] = "input.ok"
        manifest["assets"][0]["path"] = "image.glb"
        (isolated / "input.ok").write_bytes((self.fixture_root / "sources/rgb-panel.ok").read_bytes())
        image = isolated / "image.glb"
        image.write_bytes((self.fixture_root / "assets/asymmetric-rgb.png").read_bytes())
        save(isolated / "manifest.json", manifest)
        link = isolated / "linked-image.glb"
        link.symlink_to(image.name)
        linked = copy.deepcopy(manifest); linked["assets"][0]["path"] = link.name
        save(isolated / "symlink.json", linked)
        self.rejection_probe("file_transport", "symlink-asset", "OKA-E-REQUEST",
                             lambda: self.load_files(isolated / "symlink.json"),
                             expected_stage="file_transport")
        before = {p.name: sha(p.read_bytes()) for p in (image, isolated / "input.ok", isolated / "manifest.json")}
        command = [sys.executable, "-B", "-m", "ontokin", "export", str(isolated / "manifest.json"),
                   "--bundle", "--target", TARGET, "--output", str(image)]
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        (isolated / "output-alias.stdout").write_bytes(result.stdout)
        (isolated / "output-alias.stderr").write_bytes(result.stderr)
        parsed = json.loads(result.stdout)
        after = {p.name: sha(p.read_bytes()) for p in (image, isolated / "input.ok", isolated / "manifest.json")}
        record = {"name": "input-overwritten-by-output", "expected_code": "OKA-E-REQUEST",
                  "expected_stage": "cli_output_admission", "command": command,
                  "exit_code": result.returncode, "actual_codes": codes(parsed),
                  "input_hashes_before": before, "input_hashes_after": after}
        record["status"] = "observed_as_expected" if result.returncode != 0 and before == after and "OKA-E-REQUEST" in codes(parsed) else "failed"
        self.summary["file_transport"].append(record)
        if record["status"] == "failed":
            self.summary["failures"].append({"scope": "file_transport", "error": record})
        original_read, target_inode, mutations = os.read, image.stat().st_ino, []
        def changing_read(fd, count):
            data = original_read(fd, count)
            if data and os.fstat(fd).st_ino == target_inode and not mutations:
                with image.open("ab") as stream:
                    stream.write(b"x"); stream.flush(); os.fsync(stream.fileno())
                mutations.append({"after_read_bytes": len(data), "new_size": image.stat().st_size})
            return data
        with patch("os.read", changing_read):
            changed = self.rejection_probe("file_transport", "mutable-file-during-read", "OKA-E-REQUEST",
                lambda: self.load_files(isolated / "manifest.json"), expected_stage="file_transport")
        changed["actual_mutations"] = mutations
        self.check(bool(mutations), "Isolated mutable-file probe must actually alter a held input")

    def run_supplied_glb_probes(self):
        from tools.texture_adversaries import generate
        from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
        from ontokin.construction import compile_construction
        from ontokin.gltf import validate_export
        from ontokin.profile_capabilities import TEXTURE_PROFILE
        from ontokin.reach_numeric import ReachExecutionWork
        artifacts = {r["name"]: (self.output / r["glb"]).read_bytes()
                     for r in self.summary["cases"] if "glb" in r}
        directory = self.output / "hostile-glbs"; directory.mkdir()
        def validate(raw, case_name):
            case = self.fixtures["cases"][case_name]
            program = self.load_files(case_root(self.fixtures, case) / case["file_manifest"])
            ledger = SharedExecutionBudget(policy=self.HostPolicy(**case["host_policy"]))
            admit_entry_budget(program.entry, ledger, profile=TEXTURE_PROFILE)
            compiler = compile_construction(program, level="evaluated", execution_budget=ledger)
            report = validate_export(raw, compiler.model, options=self.options, target_contract=TARGET,
                                     work=ReachExecutionWork(execution_budget=ledger))
            return {"report": report, "execution_budget": ledger.report(status="valid")}
        positive = set()
        for mutation in generate(self.fixtures, artifacts):
            name, raw = mutation["case"], mutation.pop("data")
            if name not in positive:
                record = {"case": name, "sha256": sha(artifacts[name])}
                try:
                    record.update(status="observed_as_expected", validation=validate(artifacts[name], name))
                except Exception as error:
                    record.update(status="failed", exception=error_record(error))
                    self.summary["failures"].append({"scope": "supplied_glb_positive", "name": name, "error": str(error)})
                self.summary["supplied_glb_positive_controls"].append(record); positive.add(name)
            mutation["path"] = "hostile-glbs/" + mutation["id"] + ".glb"
            (self.output / mutation["path"]).write_bytes(raw)
            try:
                report = validate(raw, name)
            except Exception as error:
                mutation["exception"] = error_record(error)
                detail = mutation["exception"].get("details", {})
                mutation["actual_export_code"] = detail.get("export_code")
                mutation["status"] = "observed_as_expected" if detail.get("export_code") == mutation["expected_code"] else "failed"
            else:
                mutation.update(status="failed", unexpected_acceptance=True, validation=report)
            if mutation["status"] == "failed":
                self.summary["failures"].append({"scope": "hostile_glb", "name": mutation["mutation"], "error": mutation})
            self.summary["hostile_glbs"].append(mutation)
        save(self.output / "hostile-glbs/production-observations.json", {
             "positive_controls": self.summary["supplied_glb_positive_controls"],
             "hostile_controls": self.summary["hostile_glbs"]})

    def state(self):
        if self.service is None:
            return None
        revision = self.service.accepted_revision(self.project)
        with self.service._store.connection() as db:
            source = db.execute("SELECT raw FROM sources WHERE project_id=? AND revision=?",
                                (self.project, revision)).fetchone() if revision else None
            runs = [dict(row) for row in db.execute("SELECT id,source_revision,descriptor,version FROM runs WHERE project_id=? ORDER BY id", (self.project,))]
            artifacts = [{"id": row[0], "program_revision": row[1], "bytes": len(row[2]),
                          "sha256": sha(bytes(row[2])), "stored_sha256": row[3]}
                         for row in db.execute("SELECT id,source_revision,data,sha256 FROM artifacts WHERE project_id=? ORDER BY id", (self.project,))]
        payload = json.loads(bytes(source[0])) if source else None
        return {"accepted_program_revision": revision,
                "accepted_payload_sha256": None if payload is None else sha(canonical(payload)),
                "assets": [] if payload is None else [{k: a[k] for k in ("asset_id", "sha256", "media_type")}
                    | {"bytes": len(base64.b64decode(a["data_base64"], validate=True))} for a in payload.get("assets", [])],
                "runs": runs, "artifacts": artifacts}

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": self.project,
                "request_id": f"c080-{self.serial:04}", "operation": operation, **fields}

    def call(self, request, *, wait=True):
        before = self.state()
        row = {"sequence": len(self.transcript) + 1, "workflow": self.scenario,
               "wait": wait, "request": copy.deepcopy(request), "state_before": before,
               "host_policy": {"max_operations": self.service.host_policy.max_operations,
                               "max_elapsed_ms": self.service.host_policy.max_elapsed_ms}}
        row["request_schema_errors"] = [e.message for e in self.schema_validators["request.schema.json"].iter_errors(request)]
        try:
            response = self.service.handle(request, wait=wait)
            row["response"] = copy.deepcopy(response)
            row["response_schema_errors"] = [e.message for e in self.schema_validators["response.schema.json"].iter_errors(response)]
        except BaseException as error:
            row["exception"] = error_record(error)
            raise
        finally:
            row["state_after"] = self.state()
            self.transcript.append(row)
            save(self.output / f"agent/exchange-{row['sequence']:04}.json", row)
        self.check(not row["response_schema_errors"], "Actual Agent response schema failure")
        return response

    def success(self, operation, **fields):
        response = self.call(self.request(operation, **fields))
        self.check(response["status"] == "succeeded", operation + " must succeed: " + str(codes(response)))
        return response

    def refuse(self, code, operation, **fields):
        response = self.call(self.request(operation, **fields))
        self.check(response["status"] in ("failed", "rejected") and code in codes(response),
                   operation + " must refuse with " + code + ": " + str(codes(response)))
        return response

    def create(self, name):
        payload = self.payload(name)
        response = self.success("create", bundle=payload, expected_program_revision=None,
                                requested_level="constructed")
        self.check(response["accepted_program_revision"] == self.fixtures["cases"][name]["program_revision"],
                   "Actual create revision differs from frozen manifest")
        return payload

    def edit_fields(self, before, after, **extra):
        old, new = before["entry"]["source"], after["entry"]["source"]
        patches = [] if old == new else [{"source_id": "entry", "source_revision": digest(old.encode()),
            "element_id": ["sources", "entry"], "start_byte": 0, "end_byte": len(old.encode()),
            "expected_text": old, "replacement": new}]
        return {"expected_program_revision": bundle_identity(before)[0],
                "requested_level": "constructed", "patches": patches, **extra}

    def accepted_same(self, before, *, all_effects=False):
        after = self.state()
        keys = ("accepted_program_revision", "accepted_payload_sha256", "assets")
        self.check(all(before[k] == after[k] for k in keys), "Rejected work changed accepted source/assets")
        if all_effects:
            self.check(before == after, "Interrupted work changed durable runs/artifacts")

    def export(self, name, payload):
        revision = bundle_identity(payload)[0]
        response = self.success("export", program_revision=revision, destination=TARGET, options=OPTIONS)
        result, chunks, offset = response["result"], [], 0
        while offset < result["total_bytes"]:
            part = self.success("artifact", artifact_id=result["artifact_id"], offset=offset,
                                max_bytes=65536)["result"]
            raw = base64.b64decode(part["data_base64"], validate=True)
            self.check(raw and part["offset"] == offset and part["program_revision"] == revision,
                       "Actual artifact slice progresses with exact revision")
            chunks.append(raw); offset += len(raw)
        raw = b"".join(chunks)
        self.check(len(raw) == result["total_bytes"] and digest(raw) == result["sha256"], "Artifact roundtrip bytes/hash")
        path = "agent/" + self.project + "-" + name + ".glb"
        (self.output / path).write_bytes(raw)
        self.summary["agent_artifacts"].append({"project_id": self.project, "name": name, "glb": path,
            "sha256": sha(raw), "bytes": len(raw), "program_revision": revision,
            "artifact_id": result["artifact_id"], "export_request_id": response["request_id"]})
        return response

    def reopen(self, policy=None):
        store = self.service.database_path.parent
        self.service.close()
        self.service = self.Service(store, host_policy=self.HostPolicy(**(policy or DEFAULT_POLICY)))

    def run_one_workflow(self, spec):
        name = spec["name"]
        if name in ("source-mapping-repair", "image-selection-repair", "generated-occurrence-repair"):
            before = self.create(spec["base"]); after = self.payload(spec["candidate"])
            self.export("before", before)
            self.success("edit", **self.edit_fields(before, after))
            self.check(self.state()["accepted_program_revision"] == bundle_identity(after)[0], "Repair accepts frozen candidate")
            self.export("after", after)
        elif name == "invalid-candidate-rollback":
            before = self.create(spec["base"]); state = self.state()
            self.refuse(spec["expected_code"], "edit", **self.edit_fields(before, self.payload(spec["candidate"])))
            self.accepted_same(state)
        elif name in ("stale-asset-replace", "duplicate-asset-change", "atomic-asset-replacement"):
            before = self.create("rgb-panel"); state = self.state()
            replacement = copy.deepcopy(self.payload("rgba-panel")["assets"][0])
            change = {"operation": "replace", "asset_id": "label", "expected_sha256": before["assets"][0]["sha256"], "asset": replacement}
            if name == "stale-asset-replace":
                change["expected_sha256"] = "sha256:" + "0" * 64
                self.refuse("OKL-E-REVISION", "edit", **self.edit_fields(before, before, asset_changes=[change]))
            elif name == "duplicate-asset-change":
                self.refuse("OKL-E-REVISION", "edit", **self.edit_fields(before, before, asset_changes=[change, change]))
            else:
                self.refuse("OKL-E-ASSET-CLOSURE", "edit", **self.edit_fields(before, before, asset_changes=[change]))
                self.accepted_same(state)
                after = self.payload("rgba-panel")
                self.success("edit", **self.edit_fields(before, after, asset_changes=[change]))
                self.check(self.state()["accepted_program_revision"] == bundle_identity(after)[0], "Source and image replacement commit together")
                self.export("after", after)
                return
            self.accepted_same(state)
        elif name == "asset-slice-roundtrip":
            payload = self.create("rgb-panel"); revision = bundle_identity(payload)[0]
            expected = base64.b64decode(payload["assets"][0]["data_base64"]); actual, offset = b"", 0
            while offset < len(expected):
                result = self.success("inspect", program_revision=revision,
                    selector={"element_id": ["assets", "label"]}, fields=["identity", "source"], limit=1,
                    asset_slice={"offset": offset, "max_bytes": 17})["result"]
                part = base64.b64decode(result["data_base64"], validate=True)
                self.check(part, "Asset slice must make progress")
                actual += part; offset += len(part)
            eof = self.success("inspect", program_revision=revision, selector={"element_id": ["assets", "label"]},
                fields=["identity", "source"], limit=1, asset_slice={"offset": offset, "max_bytes": 17})["result"]
            self.check(actual == expected and eof["data_base64"] == "" and eof["complete"] and eof["next_offset"] is None,
                       "Asset slices reconstruct exact original bytes and empty EOF")
        elif name == "fresh-host-reauthorization":
            self.service.host_policy = self.HostPolicy(**MAXIMUM_POLICY)
            payload = self.create(spec["base"]); state = self.state(); revision = bundle_identity(payload)[0]
            self.reopen()
            self.refuse("OKL-E-RESOURCE", "inspect", program_revision=revision, selector={"kind": "texture_asset"}, fields=["identity", "source"], limit=100)
            self.refuse("OKL-E-RESOURCE", "inspect", program_revision=revision, selector={"element_id": ["assets", "label"]}, fields=["source"], limit=1, asset_slice={"offset": 0, "max_bytes": 1})
            self.refuse("OKL-E-RESOURCE", "export", program_revision=revision, destination=TARGET, options=OPTIONS)
            self.accepted_same(state, all_effects=True)
        elif name == "caller-reduces-budget":
            payload = self.create("rgb-panel")
            self.refuse("OKL-E-RESOURCE", "validate", program_revision=bundle_identity(payload)[0], requested_level="constructed", budgets={"max_operations": 1})
        elif name == "cancel-png-or-export":
            self.cancel_during_export()
        elif name == "reopen-retry-and-changed-payload":
            payload = self.payload("rgb-panel")
            request = self.request("create", bundle=payload, expected_program_revision=None, requested_level="constructed")
            response = self.call(request); self.check(response["status"] == "succeeded", "Original durable create")
            state = self.state(); self.reopen()
            self.check(self.call(request) == response, "Reopen identical request recovers exact historical receipt")
            changed = copy.deepcopy(request); changed["bundle"]["assets"] = self.payload("rgba-panel")["assets"]
            refusal = self.call(changed)
            self.check(refusal["status"] == "rejected" and "OKL-E-REQUEST-ID" in codes(refusal), "Changed retry payload conflict")
            self.accepted_same(state, all_effects=True)
        elif name in ("stale-mapping-page", "stale-asset-metadata-cursor"):
            before = self.create("assembly"); revision = bundle_identity(before)[0]
            if name == "stale-mapping-page":
                operation, query = "surface.mesh_page", {"element_id": ["assembly", "demo", "first"], "count": 1}
            else:
                operation, query = "inspect", {"selector": {"kind": "texture_asset"}, "fields": ["identity", "source"], "limit": 1}
            first = self.success(operation, program_revision=revision, **query)
            cursor = first["next_cursor"]; self.check(cursor is not None, "Actual page yields cursor")
            self.reopen()
            self.success(operation, program_revision=revision, cursor=cursor, **query)
            after = self.payload("assembly-mapping-repaired")
            self.success("edit", **self.edit_fields(before, after))
            self.refuse("OKL-E-REVISION", operation, program_revision=bundle_identity(after)[0], cursor=cursor, **query)
            if name == "stale-mapping-page":
                self.refuse("OKL-E-REVISION", operation, program_revision=revision, cursor=cursor,
                    element_id=["assembly", "demo", "sibling"], count=1)
        elif name == "interrupted-publication":
            self.interrupt_publication()
        elif name == "reordered-transport":
            before = self.create(spec["base"])
            candidate = self.load_files(self.fixture_root / spec["candidate_file_manifest"])
            self.check(candidate.program_revision == bundle_identity(before)[0] and
                       bundle_identity(candidate.to_payload())[0] == bundle_identity(before)[0],
                       "Reordering transport preserves exact full revision")
            save(self.output / "agent/reordered-transport-payload.json", candidate.to_payload())
        elif name in ("successful-asset-add", "successful-asset-remove"):
            before = self.create(spec["base"]); after = self.payload(spec["candidate"])
            spare = next(a for a in (after if name.endswith("add") else before)["assets"] if a["asset_id"] == "spare")
            change = {"operation": "add", "asset": spare} if name.endswith("add") else {"operation": "remove", "asset_id": "spare", "expected_sha256": spare["sha256"]}
            if name.endswith("remove"):
                state = self.state()
                self.refuse("OKL-E-ASSET-CLOSURE", "edit", **self.edit_fields(before, before, asset_changes=[change]))
                self.accepted_same(state)
            self.success("edit", **self.edit_fields(before, after, asset_changes=[change]))
            self.check(self.state()["accepted_program_revision"] == bundle_identity(after)[0], "Atomic asset membership transaction exact revision")
            self.success("inspect", program_revision=bundle_identity(after)[0], selector={"kind": "texture_asset"}, fields=["identity", "source"], limit=100)
            self.export("after", after)
        else:
            raise AssertionError("No executable frozen workflow: " + name)

    def cancel_during_export(self):
        payload = self.create("rgb-panel"); revision = bundle_identity(payload)[0]; state = self.state()
        reached, release, worker_errors = threading.Event(), threading.Event(), []
        original = self.service._make_check
        def make_check(task):
            check = original(task)
            actual_poll = check.execution_budget.check
            def gated():
                if check.execution_budget.stage == "recording_export_readback" and not reached.is_set():
                    reached.set()
                    if not release.wait(20):
                        raise TimeoutError("Acceptance cancellation barrier timed out")
                    check.last_poll = 0.0
                return actual_poll()
            check.execution_budget.check = gated
            return check
        request = self.request("export", program_revision=revision, destination=TARGET, options=OPTIONS)
        self.service._make_check = make_check
        try:
            queued = self.call(request, wait=False)
            self.check(queued["status"] == "queued", "Actual cancel target is queued")
            def work():
                try:
                    self.service.work_next()
                except BaseException as error:
                    worker_errors.append(error_record(error))
            worker = threading.Thread(target=work, name="c080-cancel-export")
            worker.start()
            self.check(reached.wait(20), "Actual export must enter metered recording/export before cancel")
            self.success("cancel", target_request_id=request["request_id"])
            release.set(); worker.join(20)
            self.check(not worker.is_alive() and not worker_errors, "Cancelled worker terminates without host exception")
            terminal = self.call(request)
            self.check(terminal["status"] == "cancelled", "Protocol cancel terminates actual in-progress export")
            self.success("status", target_request_id=request["request_id"])
            self.accepted_same(state, all_effects=True)
        finally:
            release.set()
            self.service._make_check = original
        save(self.output / "agent/cancellation-barrier.json", {"actual_export_checkpoint_reached": reached.is_set(),
             "request_id": request["request_id"], "worker_errors": worker_errors,
             "intervention": "Pause at actual execution-ledger export checkpoint, submit real protocol cancel, resume original polling."})

    def interrupt_publication(self):
        payload = self.create("rgb-panel"); revision = bundle_identity(payload)[0]; state = self.state()
        original, prepared = self.service._persist_task_metadata, []
        class PublicationInterruption(BaseException):
            pass
        def fail_after_prepare(db, task):
            if task.artifact is not None:
                raw, report, artifact_id = task.artifact
                prepared.append({"artifact_id": artifact_id, "bytes": len(raw), "sha256": sha(raw),
                                 "request_id": task.request["request_id"]})
                (self.output / "agent/interrupted-prepared-only.glb").write_bytes(raw)
                raise PublicationInterruption("Deliberate interruption inside actual uncommitted publication transaction")
            return original(db, task)
        self.service._persist_task_metadata = fail_after_prepare
        request = self.request("export", program_revision=revision, destination=TARGET, options=OPTIONS)
        try:
            self.call(request)
        except PublicationInterruption:
            pass
        finally:
            self.service._persist_task_metadata = original
        self.check(len(prepared) == 1, "Publication interruption must occur after real PNG-bearing GLB preparation")
        self.reopen()
        status = self.success("status", target_request_id=request["request_id"])
        self.check(status["result"]["target_status"] in ("unknown_outcome", "cancelled", "failed"), "Interrupted work cannot claim successful publication")
        self.accepted_same(state, all_effects=True)
        save(self.output / "agent/publication-interruption.json", {"prepared_only": prepared,
             "status_response": status, "before": state, "after": self.state(),
             "intervention": "Injected BaseException inside actual SQLite publication transaction after artifact preparation; close/reopen and actual status reconciliation."})

    def run_slice_probes(self):
        self.scenario = "asset-slice-boundaries"
        for index, spec in enumerate(self.fixtures["workflows"]["asset_slice_boundary_probes"]):
            self.project = f"c080-slice-{index:02}"
            record = {"name": spec["name"], "first_exchange": len(self.transcript) + 1}
            try:
                payload = self.create(spec.get("base", "rgb-panel")); revision = bundle_identity(payload)[0]
                expected = base64.b64decode(payload["assets"][0]["data_base64"])
                offset = spec.get("offset", 0)
                if offset == "total_bytes": offset = len(expected)
                elif offset == "total_bytes+1": offset = len(expected) + 1
                fields = {"program_revision": revision, "selector": spec.get("selector", {"element_id": ["assets", "label"]}),
                          "fields": ["identity", "source"], "limit": 1,
                          "asset_slice": {"offset": offset, "max_bytes": spec.get("max_bytes", 1)}}
                if "extra_field" in spec:
                    key = spec["extra_field"]
                    fields[key] = {"seconds": "0", "side": "after"} if key == "time" else "forbidden-with-slice"
                if "expected_code" in spec:
                    self.refuse(spec["expected_code"], "inspect", **fields)
                else:
                    result = self.success("inspect", **fields)["result"]
                    raw = base64.b64decode(result["data_base64"], validate=True)
                    self.check(raw == expected[offset:offset + fields["asset_slice"]["max_bytes"]], "Boundary slice returns exact independent bytes")
                    self.check(result["returned_bytes"] == len(raw) and result["complete"] == (offset + len(raw) == len(expected)), "Boundary slice length/EOF")
                record["status"] = "observed_as_expected"
            except Exception as error:
                record.update(status="failed", exception=error_record(error))
                self.summary["failures"].append({"scope": "asset_slice", "name": spec["name"], "error": str(error)})
            record["last_exchange"] = len(self.transcript)
            self.summary["asset_slice_probes"].append(record)

    def run_envelope_probes(self):
        directory = self.output / "envelope-probes"; directory.mkdir()
        for index, spec in enumerate(self.fixtures["workflows"]["request_envelope_boundaries"]):
            request = {"schema_version": PROTOCOL, "project_id": "c080-envelope", "request_id": f"boundary-{index}",
                       "operation": "create", "expected_program_revision": None,
                       "requested_level": "represented", "bundle": self.payload("rgb-panel")}
            request["bundle"]["entry"]["source"] += "\n//"
            def encoded():
                return json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
            remainder = spec["serialized_utf8_bytes"] - len(encoded())
            q, r = divmod(remainder, 6)
            request["bundle"]["entry"]["source"] += "\0" * q + " " * r
            raw = encoded(); self.check(len(raw) == spec["serialized_utf8_bytes"], "Actual envelope exact byte boundary")
            self.check(len(request["bundle"]["entry"]["source"].encode()) < 2000000, "Envelope probe remains under source UTF-8 bound")
            path = directory / (spec["name"] + ".json"); path.write_bytes(raw)
            command = [sys.executable, "-B", "-m", "ontokin", "agent", "--protocol", PROTOCOL,
                       "--store", str(directory / (spec["name"] + "-store")), "--request", str(path), "--wait"]
            result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
            (directory / (spec["name"] + ".stdout")).write_bytes(result.stdout)
            (directory / (spec["name"] + ".stderr")).write_bytes(result.stderr)
            response = json.loads(result.stdout)
            record = {"name": spec["name"], "bytes": len(raw), "sha256": sha(raw),
                      "request_file": path.relative_to(self.output).as_posix(), "command": command,
                      "exit_code": result.returncode, "response": response,
                      "actual_codes": codes(response), "source_utf8_bytes": len(request["bundle"]["entry"]["source"].encode())}
            if "expected_code" in spec:
                okay = spec["expected_code"] in codes(response)
            else:
                # Admission is proven by a request identity reaching the service,
                # not by pretending that later parsing must accept control chars.
                okay = response.get("request_id") == request["request_id"] and not (
                    (response.get("protocol_error") or {}).get("code") == "OKA-E-RESOURCE" and
                    "transport limit" in (response.get("protocol_error") or {}).get("message", ""))
            record["status"] = "observed_as_expected" if okay else "failed"
            self.summary["envelope_boundaries"].append(record)
            if not okay:
                self.summary["failures"].append({"scope": "envelope", "error": record})

    def run_agent(self):
        live = self.output / "live-store"
        self.service = self.Service(live, host_policy=self.HostPolicy())
        for spec in self.fixtures["workflows"]["sequences"]:
            self.scenario, self.project = spec["id"], "c080-" + spec["id"].lower()
            self.service.host_policy = self.HostPolicy()
            record = {"id": spec["id"], "name": spec["name"], "project_id": self.project,
                      "first_exchange": len(self.transcript) + 1}
            try:
                self.run_one_workflow(spec)
                record["status"] = "observed_as_expected"
            except Exception as error:
                record.update(status="failed", exception=error_record(error))
                self.summary["failures"].append({"scope": "workflow", "name": spec["name"], "error": str(error)})
            record.update(last_exchange=len(self.transcript), retained_state=self.state())
            self.summary["workflows"].append(record)
            save(self.output / "summary.json", self.summary)
        self.run_slice_probes()
        self.scenario, self.project = "operation-coverage", "c080-coverage"
        payload = self.create("assembly"); revision = bundle_identity(payload)[0]
        self.success("discover", profile=PROFILE, limit=1000)
        self.success("validate", program_revision=revision, requested_level="constructed")
        self.success("inspect", program_revision=revision, selector={"kind": "source"}, fields=["identity", "source"], limit=100)
        self.success("inspect", program_revision=revision, selector={"path": "first"}, fields=["identity", "geometry", "support"], limit=1)
        self.success("surface.mesh_page", program_revision=revision, element_id=["assembly", "demo", "first"], count=256)
        self.success("evaluate", program_revision=revision, run_id=None, until_seconds="0.5")
        self.success("reset", program_revision=revision)
        self.summary["operation_inventory"] = sorted({r["request"]["operation"] for r in self.transcript})
        self.check(self.summary["operation_inventory"] == sorted(self.fixtures["workflows"]["required_operations"]), "All twelve actual Agent operations")
        save(self.output / "agent/transcript.json", self.transcript)
        with (self.output / "agent/transcript.jsonl").open("w", encoding="utf-8") as stream:
            for row in self.transcript:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        backup = self.output / "agent/durable-store.sqlite3"
        with self.service._store.connection() as source, sqlite3.connect(backup) as destination:
            source.backup(destination)
        self.summary["store"] = {"path": backup.relative_to(self.output).as_posix(),
                                 "sha256": sha(backup.read_bytes()), "bytes": backup.stat().st_size}
        self.service.close(); self.service = None
        self.run_envelope_probes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/textured-surfaces")
    parser.add_argument("--corrections", type=Path, help="Explicitly select the separately frozen input corpus version 2")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(ROOT):
        parser.error("--output must be a new directory outside the checkout")
    fixtures = load_fixtures(args.fixtures, args.corrections)
    output.mkdir(parents=True)
    for name in ("sources", "controls", "agent"):
        (output / name).mkdir()
    run = None
    try:
        run = Acceptance(fixtures, output)
        run.run_sources()
        run.run_transport()
        run.run_supplied_glb_probes()
        run.run_agent()
        run.summary["status"] = "failed" if run.summary["failures"] else "produced_as_expected"
    except BaseException as error:
        if run is None:
            save(output / "initialization-failure.json", error_record(error))
            raise
        run.summary["status"] = "failed"
        run.summary["failures"].append({"scope": "driver", "error": error_record(error)})
    finally:
        if run is not None:
            if run.service is not None:
                run.service.close()
            run.summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
            save(output / "summary.json", run.summary)
            save(output / "inventory.json", inventory(output))
    print(json.dumps({"status": run.summary["status"], "source_cases": len(run.summary["cases"]),
                      "failures": len(run.summary["failures"]), "output": str(output)}))
    return 0 if run.summary["status"] == "produced_as_expected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
