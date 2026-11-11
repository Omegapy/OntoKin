"""Read-only consistency audit for the C201 preparation documents.

This script reads files and Git objects only. It does not import or execute
OntoKin, the prototype, a native tool, a receiver, Node or a product test.
"""
from __future__ import annotations

import argparse
import datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess


PREFIX = "docs/engineering/static-tray-admission-c201/"
DOCUMENTS = ("README.md", "ADMISSION.md", "ADMISSION.json", "IMPLEMENTATION-NEXT.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    rows = []
    bindings = []

    def git(*values):
        return subprocess.check_output(["git", "-C", str(repo), *values])

    def read(path):
        if args.commit:
            return git("show", args.commit + ":" + path)
        return (repo / path).read_bytes()

    def check(name, result, detail=None):
        row = {"name": name, "pass": bool(result)}
        if detail is not None:
            row["detail"] = detail
        rows.append(row)

    raw = {name: read(PREFIX + name) for name in DOCUMENTS}
    texts = {name: data.decode() for name, data in raw.items()}
    protocol = json.loads(texts["ADMISSION.json"])
    historical_lock = json.loads(read("docs/engineering/static-tray-exporter-c200/EXECUTABLE-INPUTS.json"))
    external_lock = json.loads(read("docs/engineering/static-tray-exporter-c200/EXTERNAL-INPUTS.json"))

    def inspect_bindings(value, location=""):
        if isinstance(value, dict):
            if {"path", "sha256"} <= value.keys():
                path = value["path"]
                data = read(path)
                observed = {"path": path, "size_bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(), "json_location": location}
                bindings.append(observed)
                check("binding hash " + path, observed["sha256"] == value["sha256"])
                check("binding size " + path, len(data) == value.get("size_bytes", len(data)))
            for key, child in value.items():
                inspect_bindings(child, location + "/" + key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect_bindings(child, location + "/" + str(index))

    inspect_bindings(protocol)
    check("exact binding inventory", len(bindings) == 38 and len({r["path"] for r in bindings}) == 38)
    authority = protocol["authority"]
    check("revision identity", protocol["revision_id"] == "OK-ADMIT-STATIC-TRAY-C201/0.1.0")
    check("mapping unchanged", authority["mapping"] == "OK-MAP-STATIC-TRAY-001/0.1.0")
    check("profile unchanged", authority["profile"] == "ontokin.static-tray/0.1.0")
    check("no present native authority", authority["native_execution_authorized_now"] is False)
    check("no admission claim", authority["admission_completed"] is False)
    check("historical input lock identity", authority["c200_input_lock_sha256"] == hashlib.sha256(
        read("docs/engineering/static-tray-exporter-c200/EXECUTABLE-INPUTS.json")).hexdigest())
    check("distinct historical closed schedules", authority["closed_historical_schedules"] == {
        "C199": {"native_starts": 1, "accepted": 0}, "C200": {"native_starts": 12, "accepted": 12}})
    integration = authority["c200_integration"]
    check("actual C200 integration tree", git("rev-parse", integration["merge_commit"] + "^{tree}").decode().strip()
          == integration["merge_tree"])

    task = protocol["public_task"]
    check("known public Q01 task", task["case"] == "Q01" and task["held_out"] is False)
    check("static box structure", (task["node_count"], task["mesh_count"], task["root_count"]) == (14, 12, 2))
    check("stable root identities", task["root_ids"] == [["equipment-tray", "pair", side] for side in ("left", "right")])
    check("canonical child order", task["ordered_child_keys"] == ["back", "base", "front", "left-wall", "payload", "right-wall"])
    check("no extra physical meaning", (task["physical"], task["motion"], task["collision"], task["aggregate_mass"])
          == ("no_body", "prescribed", "disabled", 0))
    expected_payloads = {"left": ["0.200", "0.060", "0.120"], "right": ["0.160", "0.040", "0.100"]}
    fraction = lambda value: Fraction(str(value))
    for side in ("left", "right"):
        values = task[side]
        px, py, pz = map(fraction, values["payload_xyz_m"])
        check(side + " frozen payload", [px, py, pz] == list(map(Fraction, expected_payloads[side])))
        c, t, b, h = (fraction(values[key]) for key in ("horizontal_clearance_m", "wall_m", "base_m", "headroom_m"))
        check(side + " frozen tray constants", (c, t, b, h) == tuple(map(Fraction, (".005", ".004", ".006", ".020"))))
        check(side + " independently derived cavity", list(map(fraction, values["cavity_width_height_depth_m"]))
              == [px + 2*c, py + h, pz + 2*c])
        check(side + " independently derived outside dimensions", list(map(fraction, values["outside_width_depth_m"]))
              == [px + 2*c + 2*t, pz + 2*c + 2*t])
        check(side + " qualified pose", values["rotation_wxyz"] == [1, 0, 0, 0] and values["translation_xyz_m"]
              == ([-0.3, 0, 0] if side == "left" else [0.3, 0, 0]))
    check("qualified materials", task["materials"]["tray_linear_rgba"] == [.25, .5, .75, 1]
          and task["materials"]["payload_linear_rgba"] == [.75, .5, .25, 1] and task["materials"]["opaque"] is True)
    for route, sources in task["source_closures"].items():
        check(route + " complete declared Q01 closure", len(sources) == 3)
        for source in sources:
            check("Markdown source table " + source["path"], source["path"] in texts["ADMISSION.md"]
                  and source["sha256"] in texts["ADMISSION.md"])

    schedule = protocol["schedule"]
    check("exact native order", schedule["native_slot_order"] == ["A01", "A02", "A03", "A04"])
    check("controls gate second route", schedule["order"] == ["A01", "D01", "D03", "A02", "A03", "A04"])
    expected_rows = [("A01", "ontokin", "baseline", None, None, []),
                     ("A02", "direct-python", "baseline", "A01", None, ["A01"]),
                     ("A03", "ontokin", "clean-regeneration", "A02", "A01", ["A01"]),
                     ("A04", "direct-python", "clean-regeneration", "A03", "A02", ["A02", "A03"])]
    observed_rows = [(r["slot"], r["route"], r["kind"], r["completed_predecessor"], r["accepted_source_reference"], r["equality_references"])
                     for r in schedule["slots"]]
    check("explicit reference graph", observed_rows == expected_rows)
    for slot in schedule["slots"]:
        check(slot["slot"] + " once-only stage limits", all(slot[k] == 1 for k in (
            "maximum_native_starts", "maximum_receiving_starts", "maximum_actual_delivery_node_starts")))
    check("A02 required controls", schedule["slots"][1]["required_completed_controls"] == ["D01", "D03"])
    ceilings = schedule["ceilings"]
    check("four independent process ceilings", all(ceilings[k] == 4 for k in ("native_starts", "receiving_starts", "actual_delivery_node_starts")))
    check("one assigned image per receiver", ceilings["renders_per_receiving_job"] == 1)
    check("no additional process scope", all(value == 0 for key, value in ceilings.items()
          if key not in ("native_starts", "receiving_starts", "actual_delivery_node_starts", "renders_per_receiving_job")))
    check("one-use invocation pending", schedule["one_use_invocation_required"] is True and schedule["current_executable_invocation"] is None)
    controls = protocol["delivered_controls"]
    check("exact required delivered controls", [c["id"] for c in controls] == ["D01", "D03"])
    check("specific control findings", [c["required_findings"] for c in controls] == [["CLEARANCE"], ["SIBLING"]])
    check("controls child-free and structurally meaningful", all(c["native_receiving_node_starts"] == 0
          and c["generic_parse_or_geometry_error_sufficient"] is False for c in controls))
    check("D01 independent gap arithmetic", fraction(controls[0]["nominal_side_clearance_after_mutation_m"])
          == Fraction(".005") - Fraction(".004")/2)

    measurements = protocol["measurements"]
    check("retained numeric allowances", measurements["tolerances"] == {
        "dimension_m": .000005, "world_corner_m": .000005, "signed_clearance_m": .000005, "rigid_transform_element": .000001})
    equalities = measurements["exact_equalities"]
    check("exact delivered file identities", equalities["files"] == ["canonical-input.json", "raw.glb", "final.glb"])
    check("pair and regeneration comparisons", equalities["pairs"] == [["A01", "A02"], ["A03", "A04"], ["A01", "A03"], ["A02", "A04"]])
    check("no new equality exemptions", equalities["new_volatile_metadata_exemptions"] is False
          and equalities["native_blend_byte_equality_required"] is False)
    visual = measurements["visual"]
    check("four assigned qualified views", (visual["required_images"], visual["width"], visual["height"]) == (4, 1024, 768))
    for key, value in historical_lock["limits"].items():
        check("retained limit " + key, protocol["limits"].get(key) == value)
    check("retained Node outer limit", protocol["limits"]["actual_delivery_node_outer_ms"] == external_lock["limits"]["host_ms"])
    check("retained Node work limit", protocol["limits"]["actual_delivery_node_work_ms"] == external_lock["limits"]["child_work_ms"])
    dependencies = protocol["intended_dependencies"]
    check("retained interpreter target", dependencies["cpython"] == historical_lock["host"]["version"])
    check("retained readback dependency targets", dependencies["three"] == external_lock["three_version"]
          and dependencies["khronos_validator"] == external_lock["validator_version"])
    check("host verification pending", dependencies["current_host_verified"] is False)
    pending = protocol["readiness_pending"]
    check("future gates not fabricated", all(value is None or value is False for value in pending.values()))
    check("explicit status boundary", protocol["status_sentence"] in texts["README.md"]
          and protocol["status_sentence"] in texts["ADMISSION.md"])
    check("retained failed legacy regression", protocol["legacy_regression"] == {
        "state": "FAILED", "distinct_passing_methods": 4239, "torque_read_methods_not_run": 13,
        "unchanged_setup_timeout_ms": 30000})
    for name, binding in protocol["qualified_role_bindings"].items():
        frozen = historical_lock["repository_files"].get(binding["path"])
        check("qualified role matches original lock " + name, frozen is not None and frozen["sha256"] == binding["sha256"])

    document_bindings = [{"path": PREFIX + name, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                         for name, data in raw.items()]
    result = {"schema": "ontokin.c203.c201-protocol-document-audit/0.1", "scope": "Read-only document and binding consistency; no product execution",
              "atUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "candidateCommit": args.commit,
              "candidateTree": git("rev-parse", args.commit + "^{tree}").decode().strip() if args.commit else None,
              "documentBindings": document_bindings, "referencedBindings": bindings, "checks": rows,
              "checksPassed": sum(r["pass"] for r in rows), "checksFailed": sum(not r["pass"] for r in rows),
              "pass": all(r["pass"] for r in rows), "nativeExecutionApproved": False, "coordinatorReviewed": False,
              "productTestsRun": 0, "nativeReceivingNodeLifecycleAuthorStarts": 0}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"pass": result["pass"], "checksPassed": result["checksPassed"], "checksFailed": result["checksFailed"],
                      "candidateCommit": args.commit, "output": str(args.output), "failures": [r for r in rows if not r["pass"]]}))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
