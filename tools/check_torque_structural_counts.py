"""Verify exact charged torque projection and aggregate structural work.

Every frozen observation uses a fresh originally admitted default budget.
Projection is measured for every object, including all massless empty headers.
The aggregate helper is also invoked on a detached native copy of each accepted
after-boundary that actually changes torque history; no callback or ledger is
replaced, and accepted runtime state must remain identical.
"""
import copy
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import sys

repo, out = map(Path, sys.argv[1:])
sys.path.insert(0, str(repo))
out.mkdir(exist_ok=False)
from ontokin.construction import compile_construction
from ontokin.evaluator import _simulator
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.texture_bundle import load_texture_file_manifest

freeze = repo / "docs/language-design/torque-v0.1/freeze"
cases = json.loads((freeze / "state-expectations.json").read_text())["cases"]
rows, failures = [], []
projections = aggregates = empty_massless = 0
for case in cases:
    for observation in case["observations"]:
        bundle = load_texture_file_manifest(freeze / (case["case"] + ".files.json"))
        ledger = SharedExecutionBudget()
        admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
        compiler = compile_construction(bundle, execution_budget=ledger)
        sim = _simulator(compiler.model, work=compiler.reach_work)
        time, side = F(observation["time_seconds"]), observation["side"]
        sim.advance(time, side)
        accepted, saved = sim.state, copy.deepcopy(sim.state)
        row = {"case": case["case"], "time": observation["time_seconds"],
               "side": side, "projections": [], "aggregates": []}
        for path in sim.model.objects:
            before = sim.work.counts.get("torque_projection", 0)
            value = sim.torque_projection(path, time)
            delta = sim.work.counts["torque_projection"] - before
            expected = 1 + len(value["active"]) + len(value["last_changes"])
            check = {"path": path, "actual": delta, "expected": expected,
                     "massless": sim.model.objects[path].mass == 0,
                     "empty": not value["active"] and not value["last_changes"],
                     "stage_restored": ledger.stage == "execution"}
            row["projections"].append(check)
            projections += 1
            empty_massless += check["massless"] and check["empty"]
            if delta != expected or not check["stage_restored"]:
                failures.append({"case": case["case"], "projection": check})
        if side == "after":
            for path, history in sim.state.torques.items():
                if history.axis is None or history.last_time != time:
                    continue
                stages = ("torque_aggregate_begin", "torque_aggregate_term",
                          "torque_aggregate_publish")
                before = {name: sim.work.counts.get(name, 0) for name in stages}
                staged = copy.deepcopy(sim.state)
                sim._aggregate_torque(path, time, staged)
                delta = {name: sim.work.counts.get(name, 0) - before[name]
                         for name in stages}
                expected = dict(zip(stages, (1, len(history.active), 1)))
                check = {"path": path, "active": len(history.active),
                         "actual": delta, "expected": expected,
                         "total": sum(delta.values()),
                         "stage_restored": ledger.stage == "execution"}
                row["aggregates"].append(check)
                aggregates += 1
                if delta != expected or not check["stage_restored"]:
                    failures.append({"case": case["case"], "aggregate": check})
        row["accepted_state_unchanged"] = sim.state is accepted and sim.state == saved
        if not row["accepted_state_unchanged"]:
            failures.append({"case": case["case"], "state_changed": True})
        row["work"] = ledger.report()
        rows.append(row)
    print(case["case"], "completed", flush=True)
(out / "measurements.json").write_text(json.dumps(rows, indent=2) + "\n")
summary = {"status": "failed" if failures else "passed", "cases": len(cases),
           "observations": len(rows), "projection_calls": projections,
           "empty_massless_headers": empty_massless, "aggregate_calls": aggregates,
           "failures": failures,
           "sources": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (repo / "ontokin").glob("*.py")}}
(out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "sources"}))
sys.exit(bool(failures))
