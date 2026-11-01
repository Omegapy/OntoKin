#!/usr/bin/env python3
"""Retain actual C085 source, Agent and supplied-byte observations.

The independently frozen expectations and independent readers are separate.
This producer never turns its own success flags into release acceptance.
Run against a new evidence directory outside the checkout. Synchronization and
publication fault injection are recorded and confined to new local stores.

Derived from the retained C083 producer's recording and lifecycle machinery.
The C085 source inputs, controls and expected outcomes were independently frozen
before implementation; this driver records actual observations of those inputs.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.run_texture_acceptance import (
    Acceptance as TextureAcceptance, codes, error_record, git, inventory, save)
from tools.texture_reference import bundle_identity, canonical, digest, sha
from tools.keyed_zip_reference import (
    FREEZE_COMMIT, FREEZE_SHA256, PROFILE, PROTOCOL, TARGET,
    case_payload, load_fixtures)


OPTIONS = {"fps": 4, "end": "1", "helpers": False}
DEFAULT_POLICY = {"max_operations": 100000, "max_elapsed_ms": 30000}
HIGH_POLICY = {"max_operations": 400000, "max_elapsed_ms": 80000}
PANEL_ID = ["panel-task", "demo", "first", "panels", "right"]


class SourceContext:
    """Fresh direct-call host context; no historical receipt grants authority."""

    def __init__(self, policy, profile, caller_caps=None):
        from ontokin.execution_budget import SharedExecutionBudget
        self.execution_budget = SharedExecutionBudget(policy=policy, caller_caps=caller_caps)
        self.profile = profile

    def __call__(self):
        self.execution_budget.tick()

    def admit(self, source):
        from ontokin.execution_budget import admit_entry_budget
        if self.execution_budget.resolved is None:
            admit_entry_budget(source.entry, self.execution_budget, profile=self.profile)
        elif self.execution_budget.admitted_entry_revision != source.entry.revision:
            raise ValueError("One source observation cannot reauthorize a different entry")


class ZipExecutionObserver:
    """Read original dynamic calls and real cumulative checkpoints unchanged."""
    def __init__(self,context):
        self.ledger=context.execution_budget
        self.invocations,self.active,self.inputs,self.maps=[],[],[],[]

    def __enter__(self):
        from unittest.mock import patch
        from ontokin.construction import ConstructionCompiler
        original_expression=ConstructionCompiler.expression
        original_admission=ConstructionCompiler._keyed_zip_input
        original_checkpoint=ConstructionCompiler._keyed_zip_checkpoint
        def expression(compiler,node,context):
            return self.expression(original_expression,compiler,node,context)
        def admission(compiler,operand,token,context,element_type):
            record,side=None,None
            if not context.abstract and self.active and self.active[-1][0]is compiler:
                _,node,record=self.active[-1]
                side="left"if operand is node.left else"right"if operand is node.right else None
            if side is not None:
                self.inputs.append((compiler,side,record))
            try:
                result=original_admission(compiler,operand,token,context,element_type)
                if side is not None:
                    record[side+"_input_admissions"]+=1
                    record["admission_order"].append(side)
                    record["input_events"].append("admit_"+side)
                    record["timeline"].append({"event":"admit_"+side})
                return result
            finally:
                if side is not None:self.inputs.pop()
        def checkpoint(compiler,node,stage,key):
            record=next((r for c,n,r in reversed(self.active)if c is compiler and n is node),None)
            try:
                return original_checkpoint(compiler,node,stage,key)
            finally:
                if record is not None:
                    record["checkpoints"].append({"stage":stage,"key":key,"consumed_operations":self.ledger.operations,
                                                  "value_entries":compiler.budget.value_entries})
                    record["keyset_keys"if stage=="keyed_zip_keyset"else"iteration_keys"].append(key)
                    record["timeline"].append({"event":stage,"key":key})
        self.patches=[patch.object(ConstructionCompiler,"expression",expression),
                      patch.object(ConstructionCompiler,"_keyed_zip_input",admission),
                      patch.object(ConstructionCompiler,"_keyed_zip_checkpoint",checkpoint)]
        for instrument in self.patches:instrument.start()
        return self

    def __exit__(self,*exception):
        for instrument in reversed(self.patches):instrument.stop()
        return False

    @staticmethod
    def keys(value):
        entries=getattr(value.value,"entries",None)if value.known else None
        return [key for key,_ in entries]if entries is not None else None

    def expression(self,original,compiler,node,context):
        owner,side,record=None,None,None;map_scope=None
        if self.active and self.active[-1][0]is compiler:
            _,current,owner=self.active[-1]
            if node is current.body:
                if context.abstract:
                    owner["abstract_body_checks"].append({"locals":{name:{"type":str(value.type),"known":value.known}
                                                                    for name,value in context.locals.items()}})
                else:
                    key=context.locals.get(current.key_name)
                    value=key.value if key is not None and key.known else None
                    owner["body_keys"].append(value)
                    owner["timeline"].append({"event":"body","key":value})
            if not context.abstract:
                side="left"if node is current.left else"right"if node is current.right else None
                if side is not None:
                    owner[side+"_input_evaluations"]+=1
                    owner["dynamic_input_order"].append(side)
                    owner["input_events"].append("evaluate_"+side)
                    owner["timeline"].append({"event":"evaluate_"+side})
        if not context.abstract and self.maps and self.maps[-1][0]is compiler:
            _,map_node,map_side,zip_record=self.maps[-1]
            if node is map_node.body:
                key=context.locals.get(map_node.key_name)
                zip_record[map_side+"_map_visits"].append(key.value if key is not None and key.known else None)
        if not context.abstract and self.inputs and self.inputs[-1][0]is compiler:
            _,input_side,input_record=self.inputs[-1]
            if node.kind=="binary"and node.op=="/":
                input_record[input_side+"_dynamic_divisions"]+=1
            if node.kind=="map_keyed":
                map_scope=(compiler,node,input_side,input_record);self.maps.append(map_scope)
        if node.kind=="zip_keyed"and not context.abstract:
            record={"expression":compiler.location(node),"left":compiler.location(node.left),"right":compiler.location(node.right),
                    "body":compiler.location(node.body),"self_path":context.self_path,
                    "left_input_evaluations":0,"right_input_evaluations":0,"left_input_admissions":0,"right_input_admissions":0,
                    "left_dynamic_divisions":0,"right_dynamic_divisions":0,
                    "dynamic_input_order":[],"admission_order":[],"input_events":[],"timeline":[],
                    "left_map_visits":[],"right_map_visits":[],"keyset_keys":[],"iteration_keys":[],"body_keys":[],
                    "abstract_body_checks":[],"checkpoints":[],"operations_before":self.ledger.operations,
                    "value_entries_before":compiler.budget.value_entries}
            self.invocations.append(record);self.active.append((compiler,node,record))
        try:
            result=original(compiler,node,context)
            if side is not None:
                owner[side+"_keys"]=self.keys(result);owner[side+"_type"]=str(result.type)
            if record is not None:
                record.update(output_keys=self.keys(result),output_type=str(result.type))
            return result
        except BaseException as error:
            if record is not None:record["exception"]=error_record(error)
            raise
        finally:
            if record is not None:
                record.update(operations_after=self.ledger.operations,value_entries_after=compiler.budget.value_entries)
                self.active.pop()
            if map_scope is not None:self.maps.pop()


from tools.keyed_zip_agent_workflows import KeyedZipAgentWorkflows


class Acceptance(KeyedZipAgentWorkflows, TextureAcceptance):
    """Reuse only binding-neutral recording helpers from the C080 producer."""

    def __init__(self, fixtures, output):
        from ontokin.budget_runtime import execute_keyed_zip_export, execute_keyed_merge_export
        from ontokin.execution_budget import HostPolicy
        from ontokin.keyed_zip_agent import KeyedZipAgentService
        from ontokin.keyed_zip_program_runtime import KeyedZipProgramRuntime
        from ontokin.scene import ExportOptions
        from ontokin.texture_bundle import load_texture_file_manifest
        from ontokin.keyed_merge_program_runtime import KeyedMergeProgramRuntime
        self.load_files = load_texture_file_manifest
        self.execute, self.execute_control = execute_keyed_zip_export, execute_keyed_merge_export
        self.Runtime, self.ControlRuntime = KeyedZipProgramRuntime, KeyedMergeProgramRuntime
        self.HostPolicy, self.ExportOptions = HostPolicy, ExportOptions
        self.Service = KeyedZipAgentService
        self.fixtures, self.output = fixtures, output
        self.trace_cases = {case["name"] for case in fixtures["expected"]["cases"]
            if bool(set(case.get("expected", {})) & {"left_input_evaluations", "body_evaluations", "body_key_order_before_failure", "left_dynamic_divisions"})}
        self.fixture_root = Path(fixtures["root"])
        self.serial, self.transcript, self.service = 0, [], None
        self.project, self.scenario = "", None
        self.lineage = {"frozen_input_commit": FREEZE_COMMIT, "frozen_manifest_sha256": FREEZE_SHA256,
            "amendments": copy.deepcopy(fixtures["amendments"]),
            "original_expected_sha256": fixtures["original_expected_sha256"],
            "effective_expected_sha256": fixtures["effective_expected_sha256"]}
        self.summary = {**self.lineage, "schema_version": "ontokin.c085-actual-evidence/0.1",
            "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
            "command": [sys.executable, *sys.argv], "python": sys.version,
            "platform": platform.platform(), "frozen_input_commit": FREEZE_COMMIT,
            "frozen_manifest_sha256": FREEZE_SHA256,
            "git": {"commit": git(["rev-parse", "HEAD"]),
                    "tree": git(["rev-parse", "HEAD^{tree}"]),
                    "status": git(["status", "--porcelain"])},
            "profile": PROFILE, "target_contract": TARGET, "agent_contract": PROTOCOL,
            "cases": [], "controls": [], "workflows": [], "agent_artifacts": [],
            "hostile_glbs": [], "supplied_glb_positive_controls": [],
            "additional_stores": [], "snapshots": [], "failures": [],
            "reopens": [],
            "release_acceptance": False,
            "independent_verification": "not_run_by_this_producer",
            "destination_verification": "not_run_by_this_producer"}
        self.options = ExportOptions(**OPTIONS)
        self.schema_validators = self.schemas()

    def schemas(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        paths = sorted((ROOT / "docs/language-design/agent-v0.18").glob("*.schema.json"))
        if not paths:
            raise RuntimeError("Actual Agent/0.18 schemas are required")
        resources = {}
        for path in sorted((ROOT / "docs/language-design").rglob("*.schema.json")):
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

    def payload(self, name):
        return case_payload(self.fixtures, self.fixtures["cases"][name])

    def source_observation(self, source, case, prefix, *, control=False):
        # The frozen older-importer refusal is intentionally authored as .16.
        # Its actual entry binding must reach the lexical import check; forcing
        # a .17 binding would observe a different refusal before that test.
        legacy = control or source.entry.raw.lstrip().startswith(b'ontokin "0.17";')
        profile = "keyed-merge-0.1" if legacy else PROFILE
        runtime = self.ControlRuntime() if legacy else self.Runtime()
        policy = self.HostPolicy(**case["host_policy"])
        context = SourceContext(policy, profile)
        level = case["expected_stage"]
        self.check(level in ("represented", "constructed", "evaluated"),
                   "Source validation requires its exact frozen stage")
        if not legacy and case["name"] in self.trace_cases:
            observer = ZipExecutionObserver(context)
            try:
                with observer:
                    result = runtime.validate_revision(source, level=level, check=context)
            finally:
                save(self.output / (prefix + ".zip-execution-trace.json"), {
                    "schema_version": "ontokin.c085-zip-execution-observation/0.1", **self.lineage,
                    "case": case["name"], "program_revision": source.program_revision,
                    "public_api": type(runtime).__name__ + ".validate_revision",
                    "profile": profile, "requested_level": level,
                    "intervention": "Read-only expression, complete input admission and actual keyed checkpoint observers delegate every original call unchanged; no values, work limits, charges or clocks are replaced. Observing consumes real elapsed time.",
                    "invocations": observer.invocations,
                    "execution_budget": context.execution_budget.report(status="observed")})
        else:
            result = runtime.validate_revision(source, level=level, check=context)
        receipt = {"schema_version": "ontokin.c085-source-observation/0.1", **self.lineage,
            "public_api": type(runtime).__name__ + ".validate_revision",
            "profile": profile, "program_revision": source.program_revision,
            "requested_level": level, "result": result,
            "execution_budget": context.execution_budget.report(status=result["outcome"])}
        save(self.output / (prefix + ".receipt.json"), receipt)
        return result

    def inspect_source(self, source, case, prefix, *, control=False):
        legacy = control or source.entry.raw.lstrip().startswith(b'ontokin "0.17";')
        profile = "keyed-merge-0.1" if legacy else PROFILE
        runtime = self.ControlRuntime() if legacy else self.Runtime()
        context = SourceContext(self.HostPolicy(**case["host_policy"]), profile)
        # Generated collections and alias isolation need the sibling/leaf rows,
        # even when the scalar probe itself names only the enclosing object.
        query = {"selector": {"kind": "object"}, "fields": ["identity", "source", "values", "geometry", "matter"],
                 "limit": 1000}
        result = runtime.inspect_revision(source, check=context, **query)
        path = prefix + ".inspection.json"
        save(self.output / path, result)
        save(self.output / (prefix + ".inspection-receipt.json"), {
            "schema_version": "ontokin.c085-source-inspection-observation/0.1", **self.lineage,
            "public_api": type(runtime).__name__ + ".inspect_revision",
            "profile": profile, "program_revision": source.program_revision,
            "query": query, "execution_budget": context.execution_budget.report(status=result["outcome"])})
        self.check(result["outcome"] == "valid" and result.get("items"),
                   case["name"] + " must retain actual public value inspection: " + str(codes(result)))
        self.check(not result.get("truncated") and not result.get("next_cursor"),
                   case["name"] + " source inspection must retain all object rows")
        return path

    def run_sources(self):
        for case in self.fixtures["expected"]["cases"]:
            record = {key: case[key] for key in ("id", "name", "source", "file_manifest",
                "expected_outcome", "expected_code", "expected_stage", "host_policy")}
            record["input_lineage"] = copy.deepcopy(self.lineage)
            prefix = "sources/" + case["name"]
            try:
                source = self.load_files(self.fixture_root / case["file_manifest"])
                record.update(program_revision=source.program_revision, receipt=prefix + ".receipt.json",
                              delivered=False)
                if case["name"] in self.trace_cases:
                    record["execution_trace"] = prefix + ".zip-execution-trace.json"
                self.check(source.program_revision == case["program_revision"], "Frozen source revision")
                if case["expected_stage"] == "delivered":
                    exported = self.execute(source, policy=self.HostPolicy(**case["host_policy"]), options=self.options)
                    result = exported.report
                    save(self.output / record["receipt"], result)
                    if exported.data is not None:
                        record.update(delivered=True, glb=prefix + ".glb",
                                      bytes=len(exported.data), sha256=sha(exported.data))
                        (self.output / record["glb"]).write_bytes(exported.data)
                    observed_valid = exported.data is not None
                else:
                    result = self.source_observation(source, case, prefix)
                    observed_valid = result["outcome"] == "valid"
                record["diagnostic_codes"] = codes(result)
                if case["expected_outcome"] == "valid":
                    self.check(observed_valid, case["name"] + " must achieve its frozen stage")
                    record["inspection"] = self.inspect_source(source, case, prefix)
                    record["inspection_receipt"] = prefix + ".inspection-receipt.json"
                    control_spec = case["explicit_c084_control"]
                    control = self.load_files(self.fixture_root / control_spec["file_manifest"])
                    self.check(control.program_revision == control_spec["program_revision"], "Frozen explicit .16 revision")
                    control_prefix = "controls/" + case["name"]
                    control_record = {"input_lineage": copy.deepcopy(self.lineage), "name": case["name"], "file_manifest": control_spec["file_manifest"],
                        "program_revision": control.program_revision, "receipt": control_prefix + ".receipt.json",
                        "host_policy": case["host_policy"]}
                    if case["expected_stage"] == "delivered":
                        exported_control = self.execute_control(control, policy=self.HostPolicy(**case["host_policy"]), options=self.options)
                        save(self.output / control_record["receipt"], exported_control.report)
                        self.check(exported_control.data is not None, case["name"] + " explicit .16 must deliver")
                        control_record.update(glb=control_prefix + ".glb", bytes=len(exported_control.data),
                                              sha256=sha(exported_control.data))
                        (self.output / control_record["glb"]).write_bytes(exported_control.data)
                        record["control"] = control_record["glb"]
                    else:
                        control_result = self.source_observation(control, case, control_prefix, control=True)
                        self.check(control_result["outcome"] == "valid", case["name"] + " explicit .16 must achieve the frozen stage")
                    control_record["inspection"] = self.inspect_source(control, case, control_prefix, control=True)
                    control_record["inspection_receipt"] = control_prefix + ".inspection-receipt.json"
                    control_record["producer_status"] = "observed_as_expected"
                    self.summary["controls"].append(control_record)
                else:
                    self.check(not observed_valid, case["name"] + " must refuse")
                    self.check(case["expected_code"] in record["diagnostic_codes"],
                               case["name"] + " requires exact frozen diagnostic: " + str(record["diagnostic_codes"]))
                    if case["expected_code"] != "OKL-E-RESOURCE":
                        self.check("OKL-E-RESOURCE" not in record["diagnostic_codes"],
                                   "Budget exhaustion cannot substitute for a semantic refusal")
                record["producer_status"] = "observed_as_expected"
            except Exception as error:
                record.update(producer_status="failed", exception=error_record(error))
                self.summary["failures"].append({"scope": "source", "name": case["name"], "error": str(error)})
            self.summary["cases"].append(record)
            save(self.output / "summary.json", self.summary)

    def run_supplied_glb_probes(self):
        from tools.keyed_zip_adversaries import build_mutations
        from ontokin.construction import compile_construction
        from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
        from ontokin.gltf import validate_export
        from ontokin.reach_numeric import ReachExecutionWork
        directory = self.output / "hostile-glbs"
        directory.mkdir(exist_ok=True)
        requirements = json.loads((self.fixture_root / "supplied-byte-adversaries.json").read_bytes())
        source_records = {row["name"]: row for row in self.summary["cases"]}
        mutation_ids = {row["id"] for row in requirements["requirements"]}
        self.check(len(mutation_ids) == len(requirements["requirements"]),
                   "Frozen supplied-byte mutation identifiers are unique")
        def validate(raw, case):
            source = self.load_files(self.fixture_root / case["file_manifest"])
            ledger = SharedExecutionBudget(policy=self.HostPolicy(**case["host_policy"]))
            admit_entry_budget(source.entry, ledger, profile=PROFILE)
            compiler = compile_construction(source, level="evaluated", execution_budget=ledger)
            report = validate_export(raw, compiler.model, options=self.options, target_contract=TARGET,
                                     work=ReachExecutionWork(execution_budget=ledger))
            return {"report": report, "execution_budget": ledger.report(status="valid")}
        for name in requirements["source_cases"]:
            source_record = source_records.get(name)
            if source_record is None or "glb" not in source_record:
                self.summary["failures"].append({"scope": "supplied_glb_positive", "name": name,
                    "error": "Frozen supplied-byte case has no retained actual source GLB"})
                continue
            case = self.fixtures["cases"][name]
            raw = (self.output / source_record["glb"]).read_bytes()
            positive = {"case": case["name"], "sha256": sha(raw)}
            try:
                positive.update(status="observed_as_expected", validation=validate(raw, case))
            except Exception as error:
                positive.update(status="failed", exception=error_record(error))
                self.summary["failures"].append({"scope": "supplied_glb_positive", "name": case["name"], "error": str(error)})
            self.summary["supplied_glb_positive_controls"].append(positive)
            try:
                mutations = build_mutations(raw, case)
                self.check(len(mutations) == len(mutation_ids) and
                           {row["id"] for row in mutations} == mutation_ids and
                           all(row["case"] == name for row in mutations),
                           "Every frozen supplied-byte mutation must be present exactly once")
            except Exception as error:
                self.summary["failures"].append({"scope": "hostile_glb_generation", "name": name,
                    "error": error_record(error)})
                continue
            for mutation in mutations:
                mutation = dict(mutation)
                data = mutation.pop("data")
                mutation["path"] = "hostile-glbs/" + case["name"] + "-" + mutation["id"] + ".glb"
                (self.output / mutation["path"]).write_bytes(data)
                try:
                    observation = validate(data, case)
                except Exception as error:
                    mutation["exception"] = error_record(error)
                    mutation["diagnostic_codes"] = codes(mutation["exception"])
                    mutation["actual_export_code"] = mutation["exception"].get("details", {}).get("export_code")
                    refusal_codes = mutation["diagnostic_codes"] + ([mutation["actual_export_code"]]
                        if mutation["actual_export_code"] else [])
                    expected_refusal = (any(code.startswith(("OKE-E-", "OKL-E-")) for code in refusal_codes)
                        and not any(code.endswith(("-RESOURCE", "-BUDGET")) for code in refusal_codes))
                    mutation["status"] = "observed_as_expected" if expected_refusal else "failed"
                else:
                    mutation.update(status="failed", unexpected_acceptance=True, validation=observation)
                if mutation["status"] == "failed":
                    self.summary["failures"].append({"scope": "hostile_glb", "name": mutation["id"], "error": mutation})
                self.summary["hostile_glbs"].append(mutation)
            save(self.output / "summary.json", self.summary)
        save(directory / "production-observations.json", {
            "positive_controls": self.summary["supplied_glb_positive_controls"],
            "hostile_controls": self.summary["hostile_glbs"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/keyed-zip")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--section", choices=("all", "sources", "agent"), default="all",
                        help="A partial diagnostic run remains labelled with its selected section")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(ROOT):
        parser.error("--output must be a new directory outside the checkout")
    fixtures = load_fixtures(args.fixtures)
    output.mkdir(parents=True)
    for name in ("sources", "controls", "agent"):
        (output / name).mkdir()
    run = None
    try:
        run = Acceptance(fixtures, output)
        run.summary["selected_section"] = args.section
        if args.section in ("all", "sources"):
            run.run_sources()
        if args.section == "all":
            run.run_supplied_glb_probes()
        if args.section in ("all", "agent"):
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
