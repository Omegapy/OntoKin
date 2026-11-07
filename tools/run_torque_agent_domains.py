"""Actual Agent A11 domain and runtime-refusal matrix at original budgets.

The protocol evaluates to an after prefix. Frozen before/after diagnostic
requirements are additionally exercised by run_torque_domain_refusals.py;
this driver does not invent a before-side evaluate request or future authority.
"""
import copy
import gzip
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import sqlite3
import sys
import traceback

repo, out = map(Path, sys.argv[1:])
sys.path.insert(0, str(repo))
out.mkdir(exist_ok=False)
from ontokin.evaluator import time_text
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.torque_agent import TorqueAgentService
from ontokin.torque_protocol import canonical_request

freeze = repo / "docs/language-design/torque-v0.1/freeze"
domains = json.loads((freeze / "evaluation-domain-cases.json").read_text())["cases"]
refusals = [c for c in json.loads((freeze / "refusal-cases.json").read_text())["cases"]
            if c["expected"].get("phase") in ("admission", "evaluation")
            and c["id"] != "n25-delivery-clock-collapse"]
sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
           for p in (repo / "ontokin").glob("*.py")}
(out / "SOURCE-IDENTITIES.json").write_text(json.dumps(sources, indent=2) + "\n")
def ratio(value):
    return F(int(value["numerator"]), int(value["denominator"]))
def physics(result):
    return {row["path"]: {k: v for k, v in row["state"].items()
                         if k not in ("run_id", "valid_interval")}
            for row in result["items"]}

results = []
for case in domains + refusals:
    name = case["id"]
    directory = out / name
    directory.mkdir()
    service = TorqueAgentService(directory / "store")
    log = gzip.open(directory / "exchanges.jsonl.gz", "wt", encoding="utf8")
    checks, failures = [], []
    sequence = 0
    def check(label, condition):
        checks.append({"check": label, "passed": bool(condition)})
        if not condition:
            raise AssertionError(label)
    def send(operation, **fields):
        global sequence
        sequence += 1
        request, raw = canonical_request({"schema_version": "ontokin.agent/0.22",
            "project_id": "domain", "request_id": str(sequence),
            "operation": operation, **fields})
        response = service.handle(request)
        log.write(json.dumps({"request": request, "response": response,
            "canonical_request_sha256": hashlib.sha256(raw.encode()).hexdigest()},
            sort_keys=True, separators=(",", ":")) + "\n")
        log.flush()
        budget = response.get("execution_budget")
        if budget:
            check(operation + " original defaults", budget["effective"] == {
                "max_operations": 100000, "max_elapsed_ms": 30000})
            check(operation + " within allocation", budget["consumed_operations"] <= 100000)
        return request, response
    def inspect(run, time, side):
        return send("inspect", program_revision=bundle.program_revision, run_id=run,
            selector={"kind": "object"}, fields=["state"], limit=100,
            time={"seconds": time, "side": side})[1]
    try:
        bundle = load_texture_file_manifest(freeze / (name + ".files.json"))
        check("exact complete frozen program identity",
              bundle.program_revision == case["identity"]["program_revision"])
        _, created = send("create", expected_program_revision=None,
                          requested_level="constructed", bundle=bundle.to_payload())
        check("constructed accepted source", created["status"] == "succeeded")
        if case in domains:
            _, evaluated = send("evaluate", program_revision=bundle.program_revision,
                run_id=None, until_seconds=case["time_seconds"])
            check("domain evaluated", evaluated["status"] == "succeeded")
            value = inspect(evaluated["run_id"], case["time_seconds"], case["side"])
            check("domain exact timed side inspected", value["status"] == "succeeded")
            state = physics(value["result"])["ball"]
            torque = state["torques"]
            fields = {"expected_phase_hex": "phase_since_anchor_rad",
                      "expected_speed_hex": "signed_angular_speed_rad_per_s",
                      "expected_canonical_speed_hex": "signed_angular_speed_rad_per_s",
                      "expected_alpha_hex": "angular_acceleration_rad_per_s2"}
            for expected, field in fields.items():
                if expected in case:
                    check(expected, torque[field].hex() == case[expected])
            fields = {"expected_rotation_route": "rotation_route",
                      "expected_rotation_anchor": "rotation_anchor_seconds",
                      "expected_rotation_anchor_seconds": "rotation_anchor_seconds"}
            for expected, field in fields.items():
                if expected in case:
                    check(expected, torque[field] == case[expected])
            if "expected_alpha_reference" in case:
                check("exact independent alpha", ratio(torque["angular_acceleration_reference_rad_per_s2"])
                      == F(case["expected_alpha_reference"]))
            for field in ("angular_error_bound_rad", "angular_speed_error_bound_rad_per_s"):
                if "minimum_" + field in case:
                    check(field + " shadow lower bound", ratio(torque[field]) >= F(case["minimum_" + field]))
            if "expected_canonical_orientation_wxyz" in case:
                check("canonical orientation", state["orientation_wxyz"]
                      == case["expected_canonical_orientation_wxyz"])
        else:
            expected = case["expected"]
            boundary = F(expected.get("boundary_seconds", "0"))
            prior_time = expected.get("successful_prefix_seconds",
                                      time_text(boundary / 2))
            if F(prior_time) == 0:
                _, prior = send("reset", program_revision=bundle.program_revision)
                prior_side = "before"
            else:
                _, prior = send("evaluate", program_revision=bundle.program_revision,
                                run_id=None, until_seconds=prior_time)
                prior_side = "after"
            check("independently accepted prefix", prior["status"] == "succeeded")
            run = prior["run_id"]
            before = inspect(run, prior_time, prior_side)
            check("prior prefix inspect", before["status"] == "succeeded")
            failed_request, failed = send("evaluate", program_revision=bundle.program_revision,
                run_id=run, until_seconds=expected.get("failed_request_seconds",
                                                      time_text(boundary)))
            # Admission diagnostics retain the inherited invalid/rejected
            # status; numerical evaluation failures retain failed.
            expected_status = "rejected" if expected["phase"] == "admission" else "failed"
            check("runtime refusal surfaced with inherited status",
                  failed["status"] == expected_status)
            diagnostic = next(d for d in failed["diagnostics"]
                              if d["code"] == expected["code"])
            for field in ("code", "phase", "message"):
                if field in expected:
                    check("diagnostic " + field, diagnostic[field] == expected[field])
            for field, value in expected.get("required_details", {}).items():
                check("diagnostic detail " + field, diagnostic["details"].get(field) == value)
            for field in ("source_id", "start_byte", "end_byte"):
                if field in expected.get("primary_source", {}):
                    check("exact primary " + field,
                          diagnostic["primary"][field] == expected["primary_source"][field])
            check("protocol after-side diagnostic", diagnostic["time"]["side"] == "after")
            if expected.get("required_related_target_declaration"):
                check("related target retained", bool(diagnostic["related"]))
            current = service.get_run("domain", run)
            (directory / "failed-run-readback.json").write_text(json.dumps(current, indent=2) + "\n")
            check("accepted prefix not reduced", F(current["valid_until_seconds"]) >= F(prior_time))
            if "accepted_prefix" in expected:
                side, time = expected["accepted_prefix"].split()
                check("whole boundary rollback to exact side",
                      F(current["valid_until_seconds"]) == F(time)
                      and current["valid_until_side"] == side)
            after = inspect(run, prior_time, prior_side)
            check("prior prefix still inspectable", after["status"] == "succeeded")
            check("prior complete physical state preserved",
                  physics(before["result"]) == physics(after["result"]))
            historical = copy.deepcopy(failed)
            service.close()
            service = TorqueAgentService(directory / "store")
            retry = service.handle(failed_request)
            log.write(json.dumps({"request": failed_request, "response": retry,
                "historical_retry_after_reopen": True}, sort_keys=True, separators=(",", ":")) + "\n")
            check("exact failed response retained after reopen", retry == historical)
        service.close()
        service = None
        with sqlite3.connect("file:" + str(directory / "store/torque-program-agent.sqlite3") + "?mode=ro", uri=True) as db:
            check("store integrity", db.execute("pragma integrity_check").fetchone()[0] == "ok")
            check("no artifact on domain/refusal run", db.execute("select count(*) from artifacts").fetchone()[0] == 0)
    except BaseException as error:
        failures.append({"error": repr(error), "traceback": traceback.format_exc()})
    finally:
        if service is not None:
            service.close()
        log.close()
    row = {"case": name, "status": "failed" if failures else "passed",
           "checks": checks, "failures": failures, "exchanges": sequence}
    (directory / "SUMMARY.json").write_text(json.dumps(row, indent=2) + "\n")
    results.append({k: (len(v) if k == "checks" else v) for k, v in row.items()})
    print(name, row["status"], len(checks), str(failures)[:400], flush=True)
summary = {"status": "failed" if any(r["failures"] for r in results) else "passed",
           "domain_cases": len(domains), "runtime_refusal_cases": len(refusals),
           "checks": sum(r["checks"] for r in results), "results": results,
           "scope": "Actual Agent after-side evaluate refusals plus exact frozen domain side inspections. The separate direct runtime driver covers both refusal observation sides."}
(out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
sys.exit(summary["status"] != "passed")
