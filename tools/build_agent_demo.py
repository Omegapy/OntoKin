#!/usr/bin/env python3
"""Run a real agent-style author/inspect/repair/evaluate/export cycle.

The service is the only path to validation, source acceptance, evaluated state,
and GLB bytes here. The driver supplies predetermined independent expectations;
it does not simulate a language model or claim an agent-efficiency benchmark.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.agent import AgentService


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def build(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    seed = (ROOT / "examples/agent/authoring-demo.ok").read_text(encoding="utf-8")
    transcript, checks = [], []
    with tempfile.TemporaryDirectory(prefix="ontokin-agent-demo-") as temporary, AgentService(Path(temporary)) as service:
        serial = 0

        def call(operation, *, expected="succeeded", **fields):
            nonlocal serial
            serial += 1
            request = {"schema_version": "ontokin.agent/0.1", "project_id": "authoring-demonstration",
                       "request_id": f"step-{serial:03d}-{operation}", "operation": operation, **fields}
            result = service.handle(request)
            transcript.append({"request": request, "response": result})
            if result["status"] != expected:
                raise AssertionError(f"{operation} returned {result['status']}: {result}")
            return result

        def check(name, condition, **observed):
            if not condition:
                raise AssertionError(f"Demonstration expectation failed: {name}: {observed}")
            checks.append({"name": name, "passed": True, "observed": observed})

        discovered = call("discover", profile="core-0.1", filter={"kind": "builtin", "name": "box"}, limit=10)
        check("Discover a typed geometry constructor", any(x["name"] == "box" for x in discovered["result"]["items"]))
        created = call("create", filename="examples/agent/repaired.ok", source=seed,
                       expected_revision=None, requested_level="evaluated", budgets={})
        initial = created["source_revision"]
        check("Accept the complete initial program through its horizon", initial == created["accepted_revision"] and created["achieved_level"] == "evaluated")
        scope = call("inspect", source_revision=initial, selector={"path": "rig", "kind": "object"},
                     fields=["identity", "source"], limit=1)
        occurrence_id = scope["result"]["items"][0]["element_id"]
        check("Inspect the exact writable occurrence", occurrence_id == ["agent-authoring-demo", "demo", "rig"])

        # Insertion is relative to the accepted source, not to the rejected candidate.
        anchor = '    object rig @ "rig": Rig {\n'
        raw, anchor_bytes = seed.encode("utf-8"), anchor.encode("utf-8")
        check("Patch anchor is unambiguous", raw.count(anchor_bytes) == 1)
        offset = raw.index(anchor_bytes) + len(anchor_bytes)

        def insertion(value):
            return {"element_id": occurrence_id, "start_byte": offset, "end_byte": offset,
                    "expected_text": "", "replacement": f"        head.radius = {value};\n"}

        rejected = call("edit", expected="rejected", expected_revision=initial,
                        patches=[insertion("1[kg]")], requested_level="evaluated", budgets={})
        check("A mass cannot replace a length", any(d["code"] == "OKL-E-UNIT" for d in rejected["diagnostics"]))
        check("The invalid candidate preserves the accepted head", rejected["accepted_revision"] == initial)
        rejected_source = call("inspect", source_revision=rejected["source_revision"], selector={"kind": "module"},
                               fields=["source"], limit=1)
        (output / "rejected-candidate.ok").write_text(rejected_source["result"]["source_text"], encoding="utf-8")
        diagnostic = next(d for d in rejected["diagnostics"] if d["code"] == "OKL-E-UNIT")
        location = diagnostic["primary"]
        rejected_bytes = rejected_source["result"]["source_text"].encode("utf-8")
        check("The diagnosis identifies the actual candidate bytes", diagnostic["source_revision"] == rejected["source_revision"] and
              rejected_bytes[location["start_byte"]:location["end_byte"]] == b"1[kg]",
              code=diagnostic["code"], candidate_revision=diagnostic["source_revision"], primary=location)

        repaired = call("edit", expected_revision=initial, patches=[insertion("0.35[m]")],
                        requested_level="evaluated", budgets={})
        final = repaired["source_revision"]
        accepted_source = call("inspect", source_revision=final, selector={"kind": "module"}, fields=["source"], limit=1)
        source_text = accepted_source["result"]["source_text"]
        (output / "repaired.ok").write_text(source_text, encoding="utf-8")
        check("The surgical repair changes only the requested initializer", source_text == (raw[:offset] + b"        head.radius = 0.35[m];\n" + raw[offset:]).decode("utf-8"))

        radii = {}
        for name in ("rig.head", "reference.head"):
            observed = call("inspect", source_revision=final, selector={"path": name, "kind": "object"},
                            fields=["values", "geometry"], limit=1)["result"]["items"][0]
            radii[name] = observed["values"]["radius"]["value"]
        check("The selected head changes and the sibling retains its default", radii == {"rig.head": .35, "reference.head": .2}, radii_m=radii)

        run = call("evaluate", source_revision=final, run_id=None, until_seconds="0.5", budgets={})
        check("An ordinary run evaluates only the requested prefix", run["result"]["run_state"]["valid_until_seconds"] == "0.5")
        advanced = call("evaluate", source_revision=final, run_id=run["run_id"], until_seconds="3", budgets={})
        check("The same run advances explicitly to the authored horizon", advanced["run_id"] == run["run_id"] and
              advanced["result"]["run_state"]["valid_until_seconds"] == "3")

        # Reference samples come from the agent inspection API, independently of GLB decoding.
        samples = []
        for index in range(25):
            seconds = str(float(Fraction(index, 8))).rstrip("0").rstrip(".") if index else "0"
            observed = call("inspect", source_revision=final, run_id=run["run_id"],
                            time={"seconds": seconds, "side": "after"}, selector={"kind": "object"},
                            fields=["state"], limit=100)["result"]
            samples.append({"time_seconds": seconds, "objects": {item["path"]: {
                "position_m": item["state"]["position_m"], "orientation_wxyz": item["state"]["orientation_wxyz"]}
                for item in observed["items"]}})
        at_one_half = samples[12]["objects"]
        check("Independent motion remains correct after the local repair",
              at_one_half["rig.head"]["position_m"] == [1.5, 1., 0.] and
              at_one_half["reference.head"]["position_m"] == [0., 1., 1.5],
              first_head_m=at_one_half["rig.head"]["position_m"], sibling_head_m=at_one_half["reference.head"]["position_m"])

        exported = call("export", source_revision=final, destination="ontokin.glb/0.1", options={}, budgets={})
        report = exported["result"]["report"]
        data, offset = bytearray(), 0
        while offset is not None:
            part = call("artifact", artifact_id=exported["result"]["artifact_id"], offset=offset, max_bytes=32768)["result"]
            check(f"Artifact chunk at byte {offset} is revision-bound", part["source_revision"] == final and part["offset"] == len(data))
            data.extend(base64.b64decode(part["data_base64"], validate=True))
            offset = part["next_offset"]
        artifact_hash = "sha256:" + hashlib.sha256(data).hexdigest()
        check("Retrieved GLB bytes match the delivered artifact", artifact_hash == report["artifact"]["sha256"] and bytes(data[:4]) == b"glTF",
              source_revision=final, artifact_sha256=artifact_hash, bytes=len(data))
        check("The adapter's decoded numerical checks pass", report["validation"]["status"] == "passed")
        (output / "repaired.glb").write_bytes(data)
        write_json(output / "repaired.export.json", report)
        write_json(output / "repaired.reference.json", {"schema_version": "ontokin.viewer-reference/0.1", "source_revision": final,
                   "artifact_sha256": artifact_hash, "tolerances": report["tolerances"], "samples": samples})
        evidence = {"schema_version": "ontokin.agent-workflow/0.1", "status": "passed",
                    "generated_at_utc": datetime.now(timezone.utc).isoformat(), "implementation": service.implementation,
                    "scope": "Deterministic agent-style API workflow with real invalid candidate, scoped repair, evaluation and retrieved GLB; no model-efficiency claim.",
                    "initial_revision": initial, "rejected_revision": rejected["source_revision"], "accepted_revision": final,
                    "artifact_sha256": artifact_hash, "checks": checks, "operation_count": len(transcript), "operations": transcript}
        write_json(output / "workflow.json", evidence)
    return {"status": "passed", "checks": len(checks), "operations": len(transcript),
            "source_revision": final, "artifact_sha256": artifact_hash, "output_dir": str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "examples/agent")
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
