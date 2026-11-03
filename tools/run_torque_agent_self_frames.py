"""Actual self-frame scalar history at every frozen clock and boundary side.

Supplements the full A11 run/store matrix with complete self-frame clock
coverage, including exact representable reversal and completion observations.
"""
import gzip
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
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
cases = json.loads((freeze / "state-expectations.json").read_text())["cases"]
physics = {c["id"]: c for c in json.loads((freeze / "physics-cases.json").read_text())["cases"]}
(out / "SOURCE-IDENTITIES.json").write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (repo / "ontokin").glob("*.py")}, indent=2) + "\n")
results = []
for case in cases:
    name = case["case"]
    directory = out / name
    directory.mkdir()
    service = TorqueAgentService(directory / "store")
    log = gzip.open(directory / "exchanges.jsonl.gz", "wt", encoding="utf8")
    sequence, assertions, observations, failures = 0, [], [], []
    def check(label, condition):
        assertions.append({"check": label, "passed": bool(condition)})
        if not condition:
            raise AssertionError(label)
    def send(operation, **fields):
        global sequence
        sequence += 1
        request, raw = canonical_request({"schema_version": "ontokin.agent/0.22",
            "project_id": "self", "request_id": str(sequence),
            "operation": operation, **fields})
        response = service.handle(request)
        log.write(json.dumps({"request": request, "response": response,
            "canonical_request_sha256": hashlib.sha256(raw.encode()).hexdigest()},
            sort_keys=True, separators=(",", ":")) + "\n")
        log.flush()
        check(operation + " succeeded", response["status"] == "succeeded")
        check(operation + " original allocation", response["execution_budget"]["effective"]
              == {"max_operations": 100000, "max_elapsed_ms": 30000})
        return response
    try:
        bundle = load_texture_file_manifest(freeze / (name + ".files.json"))
        check("exact source identity", bundle.program_revision == case["program_revision"])
        send("create", expected_program_revision=None, requested_level="constructed", bundle=bundle.to_payload())
        evaluated = send("evaluate", program_revision=bundle.program_revision, run_id=None,
                         until_seconds=time_text(F(physics[name]["horizon"])))
        for index, observation in enumerate(case["observations"]):
            states = []
            for frame in ("world", case["target_path"] + ".frame"):
                response = send("inspect", program_revision=bundle.program_revision,
                    run_id=evaluated["run_id"], selector={"path": case["target_path"]},
                    fields=["state"], limit=100, frame=frame,
                    time={"seconds": observation["time_seconds"], "side": observation["side"]})
                states.append(response["result"]["items"][0]["state"])
            world, local = states
            check("complete torque state unchanged " + str(index), world["torques"] == local["torques"])
            check("same full validity " + str(index), world["valid_interval"] == local["valid_interval"])
            check("self origin zero " + str(index), all(v == 0 for v in local["position_m"]))
            for field, expected in observation["exact_fields"].items():
                check("frozen exact " + str(index) + " " + field, local["torques"][field] == expected)
            for field, expected in observation["canonical_hex"].items():
                check("frozen canonical " + str(index) + " " + field, local["torques"][field].hex() == expected)
            observations.append({"time": observation["time_seconds"], "side": observation["side"],
                                 "world": world, "self": local})
    except BaseException as error:
        failures.append({"error": repr(error), "traceback": traceback.format_exc()})
    finally:
        service.close()
        log.close()
    row = {"case": name, "status": "failed" if failures else "passed",
           "checks": assertions, "observations": observations, "failures": failures}
    (directory / "SUMMARY.json").write_text(json.dumps(row, indent=2) + "\n")
    results.append({"case": name, "status": row["status"], "checks": len(assertions),
                    "observations": len(observations), "failures": failures})
    print(name, row["status"], len(observations), str(failures)[:400], flush=True)
summary = {"status": "failed" if any(r["failures"] for r in results) else "passed",
           "cases": len(results), "observations": sum(r["observations"] for r in results),
           "checks": sum(r["checks"] for r in results), "results": results}
(out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
sys.exit(summary["status"] != "passed")
