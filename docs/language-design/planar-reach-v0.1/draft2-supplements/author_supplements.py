"""Reconstruct expected lifecycle preparation without importing OntoKin runtime.

The five entry sources, two transport manifests and Q16 probe record were
recovered exactly. This script is NEW work; it does not recover old acceptance
or protocol bytes. Default mode checks reproducibility; --write replaces only
the explicitly named newly generated preparation files below.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from fractions import Fraction as Q
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent
spec = importlib.util.spec_from_file_location("independent_reach_oracle", PROPOSAL / "oracle.py")
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)

RECOVERED = {
    "sources/l01-both-moving-pause-resume.ok": (1100, "c8897752a218d176ca6f34b17c965a0b9612461c2d625b7368586b9bd7187f77"),
    "sources/l02-stopped-action-new-owner.ok": (1199, "11f3a5031cc03a25a9161ba88eafb6fa77bb469e202098a5aed83f0cde4e3550"),
    "sources/l03-completed-action-new-owner.ok": (1183, "a57e8513d93cc4dd5b8998bd4119b9b534c7b6c1faf06574a8d88ceb99e11736"),
    "sources/l04-failed-handoff-valid-prefix.ok": (1199, "ee74c0c6b6702dd16abed60a5e9acfdbceac19996b00e6c49c3398dbed7cfc6c"),
    "sources/q16-nonbinary-boundaries.ok": (1114, "1b8ac46ebed51dc99264c582a223953a5925e589f4eacb7de9ca8b3e42524ef3"),
    "l01.files.json": (661, "e7c9fda1576262d9d7ba7902fa0c2760136a2f14b40f5fdd432899f4897141d0"),
    "q16.files.json": (657, "298749526ba81c551d3d8e240c26aa7423ce6503ff2f937a5f31bf43af2ea188"),
    "recording-probes.json": (10932, "cf50015e6c7e46833ede254963806fa28aa4b9f3cc9939234799bfdf043e7123"),
}
REVISIONS = {
    "L01": "sha256:6e116b81c6834ab3e36d914ad8baa739a1e31d72697ce3902245fd46b78a4dc8",
    "L02": "sha256:8fe2123277e94597d3e4ca518e3c1c1fd68d9a18325459f563c9eb5a270fe748",
    "L03": "sha256:0d8e38f49425cf9a0e9b96f8aadb42d7baf1743208e152aaea8f2d58f759abc7",
    "L04": "sha256:af42329216000f3799b08cf4ec4272c8907bcc1446c2d0b0b5edc9f044e57e0e",
    "Q16": "sha256:778a3acf2ee76e6769b5ecbf66a220e91bec77b56bf8e9c4d8f18e4e7c4807b2",
}
LOST = {
    "acceptance.json": (358678, "1ae62ac03802727b92a16e63d61634c182c8a249320f01d8901f0c918664ac0a"),
    "protocol-cases.json": (45352, "ebbf773ef532d433d4f640da7005420e4f5510fcb94c955051a501db009d5b34"),
    "generated-members.json": (2306, "7d9bbc3fb7b05f52c4ebd278e8ee1b2974b52d26c749fce4ed020410b02f7f79"),
}
GRIDS = {
    "L01": [("0", "before"), ("0", "after"), ("0.25", "before"), ("0.25", "after"),
            ("0.5", "before"), ("0.5", "after"), ("1", "after"), ("1.25", "after"),
            ("1.5", "before"), ("1.5", "after"), ("2", "before"), ("2", "after"),
            ("2.5", "after"), ("3", "before"), ("3", "after"), ("4", "after")],
    "L02": [("0", "before"), ("0", "after"), ("0.25", "before"), ("0.25", "after"),
            ("0.5", "before"), ("0.5", "after"), ("0.75", "after"), ("1", "before"),
            ("1", "after"), ("1.25", "after"), ("1.5", "before"), ("1.5", "after"),
            ("2", "before"), ("2", "after")],
    "L03": [("0", "before"), ("0", "after"), ("0.5", "after"), ("1", "before"),
            ("1", "after"), ("1.5", "after"), ("2", "before"), ("2", "after"),
            ("2.25", "after"), ("2.5", "after"), ("3", "before"), ("3", "after"),
            ("4", "before"), ("4", "after")],
    "L04": [("0", "before"), ("0", "after"), ("0.125", "before"), ("0.125", "after"),
            ("0.25", "before"), ("0.25", "after"), ("0.5", "before")],
}
PREFIX = ["planar-reach-lifecycle", "demo"]
JOINT_IDS = [PREFIX + ["rig", "arm", name] for name in ("shoulder", "elbow")]


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode()


def member(path, data=None):
    data = (HERE / path).read_bytes() if data is None else data
    return {"path": path, "bytes": len(data), "sha256": sha(data)}


def rational(value):
    value = Q(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def seconds(value):
    value = Q(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    denominator, places = value.denominator, 0
    while denominator != 1:
        if denominator % 2 == 0:
            denominator //= 2
        elif denominator % 5 == 0:
            denominator //= 5
        else:
            raise ValueError("nonterminating decimal fixture time")
        places += 1
    whole = value.numerator * (10 ** places) // value.denominator
    digits = str(whole).zfill(places + 1)
    text = digits if not places else (digits[:-places] + "." + digits[-places:]).rstrip("0").rstrip(".")
    return sign + text


def manifest(source):
    return {"schema_version": "ontokin.files/0.1", "entry": {"filename": "reach-entry.ok", "path": source},
            "modules": [{"filename": name + ".ok", "package_id": "proposal." + name,
                         "path": "libraries/" + name + ".ok", "version": "0.1.0"}
                        for name in ("reach-assets", "reach-exterior", "reach-parts")]}


def identity(files):
    units = [{"filename": files["entry"]["filename"], "source_id": "entry", "package_id": None,
              "version": None, "source_revision": sha((HERE / files["entry"]["path"]).read_bytes())}]
    for module in files["modules"]:
        units.append({"filename": module["filename"], "package_id": module["package_id"],
                      "version": module["version"], "source_id": "package:" + module["package_id"] + "@" + module["version"],
                      "source_revision": sha((HERE / module["path"]).read_bytes())})
    units.sort(key=lambda unit: unit["source_id"])
    closure = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": units}
    payload = json.dumps(closure, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    return sha(b"ontokin.bundle/0.1\0" + payload), closure


def affine(start, target, elapsed, duration):
    return [float(Q.from_float(a) + (Q.from_float(b) - Q.from_float(a)) * Q(elapsed) / Q(duration))
            for a, b in zip(start, target)]


def rate(start, target, duration):
    return [float((Q.from_float(b) - Q.from_float(a)) / Q(duration)) for a, b in zip(start, target)]


TARGET_A = oracle.solve([1, 1], [0, 1, 0])["resolved_joint_targets_rad"]
TARGET_B = oracle.solve([1, 1], [1, 1, 0], "negative")["resolved_joint_targets_rad"]
ZERO = [0.0, 0.0]


def pose(coordinates, rates=ZERO):
    return oracle.pose([1, 1], coordinates, rates, base_translation=(0, 1, 0))


def base_pose(coordinates):
    value = pose(coordinates)
    return {"position_m": value["tip_position_base_m"], "orientation_wxyz": value["forearm_orientation_wxyz"]}


def state_data(case, t, side):
    """Fixed independent lifecycle equations; not a general source evaluator."""
    passed = lambda clock: t > Q(clock) or (t == Q(clock) and side == "after")
    a = {"lifecycle": "pending", "start": ZERO, "target": TARGET_A, "duration": Q(2),
         "start_time": Q(0), "elapsed": None, "completion": None, "terminal_time": None}
    b = {"lifecycle": "pending", "start": ZERO, "target": TARGET_B, "duration": Q(1),
         "start_time": Q("0.5") if case == "L02" else Q(2), "elapsed": None,
         "completion": None, "terminal_time": None}
    coordinates, rates = ZERO, ZERO
    if passed(0):
        a.update(lifecycle="running", elapsed=t, completion=Q(2))
        if case == "L01":
            if passed("0.5") and not passed("1.5"):
                a.update(lifecycle="paused", elapsed=Q("0.5"), completion=None)
            elif passed("1.5"):
                a.update(elapsed=min(Q(2), t - 1), completion=Q(3))
            if passed(3):
                a.update(lifecycle="completed", terminal_time=Q(3))
        elif case == "L02" and passed("0.5"):
            a.update(lifecycle="stopped", elapsed=Q("0.5"), completion=None, terminal_time=Q("0.5"))
        elif case == "L03" and passed(2):
            a.update(lifecycle="completed", elapsed=Q(2), terminal_time=Q(2))
        coordinates = affine(a["start"], a["target"], a["elapsed"], a["duration"])
        rates = rate(a["start"], a["target"], a["duration"]) if a["lifecycle"] == "running" else ZERO
    if case in ("L02", "L03") and passed(b["start_time"]):
        b["start"] = affine(ZERO, TARGET_A, Q("0.5"), 2) if case == "L02" else TARGET_A
        b.update(lifecycle="running", elapsed=min(Q(1), t - b["start_time"]), completion=b["start_time"] + 1)
        if passed(b["completion"]):
            b.update(lifecycle="completed", terminal_time=b["completion"])
        coordinates = affine(b["start"], b["target"], b["elapsed"], b["duration"])
        rates = rate(b["start"], b["target"], 1) if b["lifecycle"] == "running" else ZERO
    return {"reach_a": a, **({"reach_b": b} if case != "L01" else {})}, coordinates, rates


def projection(case, path, data, coordinates, rates, t, side, revision, source):
    text = source.decode()
    start = source.index(("action " + path + " ").encode())
    end = source.index(b";", start) + 1
    goal = [0.0, 1.0, 0.0] if path == "reach_a" else ([8.0, 8.0, 0.0] if case == "L04" else [1.0, 1.0, 0.0])
    lifecycle = data["lifecycle"]
    outcomes = {"pending": "pending", "running": "active", "paused": "active", "stopped": "interrupted", "completed": "satisfied"}
    physical = pose(coordinates, rates)
    current = {
        "observation": {"time_seconds": seconds(t), "side": side, "run_id": None, "context_kind": "recorded_prefix"},
        "lifecycle": lifecycle, "goal_outcome": outcomes[lifecycle],
        "resolved_joint_targets_rad": None if lifecycle == "pending" else data["target"],
        "start_coordinates_rad": None if lifecycle == "pending" else data["start"],
        "start_time_seconds": None if lifecycle == "pending" else seconds(data["start_time"]),
        "elapsed_seconds": None if data["elapsed"] is None else seconds(data["elapsed"]),
        "completion_time_seconds": None if data["completion"] is None else seconds(data["completion"]),
        "joint_coordinates_rad": coordinates, "joint_rates_rad_per_s": rates,
        "action_joint_rates_rad_per_s": rate(data["start"], data["target"], data["duration"]) if lifecycle == "running" else ZERO,
        "claimed_joint_ids": JOINT_IDS if lifecycle in ("running", "paused") else [],
        "current_residual_m": None if lifecycle == "pending" else math.dist(physical["tip_position_base_m"], goal),
        "tip_pose_base": {"position_m": physical["tip_position_base_m"], "orientation_wxyz": physical["forearm_orientation_wxyz"]},
        "tip_pose_world": {"position_m": physical["tip_position_world_m"], "orientation_wxyz": physical["forearm_orientation_wxyz"]},
        "current_world_target_m": [goal[0], goal[1] + 1, goal[2]], "terminal_result": None,
    }
    if data["terminal_time"] is not None:
        terminal_coordinates = affine(data["start"], data["target"], data["elapsed"], data["duration"])
        terminal_pose = base_pose(terminal_coordinates)
        current["terminal_result"] = {"outcome": outcomes[lifecycle], "time_seconds": seconds(data["terminal_time"]),
            "position_residual_m": math.dist(terminal_pose["position_m"], goal),
            "joint_coordinates_rad": terminal_coordinates, "tip_pose_base": terminal_pose}
    occurrence = lambda name: {"path": "rig.arm." + name, "element_id": PREFIX + ["rig", "arm"] + name.split(".")}
    frame = {"path": "rig.arm.pivot.frame", "site_element_id": PREFIX + ["rig", "arm", "pivot"]}
    action_id = PREFIX + [path.replace("_", "-")]
    return {"kind": "reach_planar", "element_id": action_id, "description_identity": action_id,
        "program_revision": revision, "accepted_program_revision": None, "candidate_only": None,
        "context_origin": "source_recording", "source_location": {"source_id": "entry", "source_revision": sha(source), "start_byte": start, "end_byte": end},
        "channel": "joint_coordinates", "chain": {"shoulder": occurrence("shoulder"), "elbow": occurrence("elbow"),
            "tip": occurrence("forearm.tip"), "base_frame": frame, "lengths_m": [1.0, 1.0],
            "closed_limits_rad": {"shoulder": [-oracle.P, oracle.P], "elbow": [-oracle.P, oracle.P]}},
        "target": {"type": "Point3", "frame": frame, "coordinates_m": goal},
        "branch": "elbow_positive" if path == "reach_a" or case == "L04" else "elbow_negative",
        "duration_seconds": "2" if path == "reach_a" else "1",
        "current": {"available": True, "reason": None, "value": current}}


def build():
    for path, (size, digest) in RECOVERED.items():
        item = member(path)
        assert item["bytes"] == size and item["sha256"] == "sha256:" + digest, path
    for path in (HERE / "libraries").glob("*.ok"):
        assert path.read_bytes() == (PROPOSAL / "libraries" / path.name).read_bytes(), path
    original = json.loads((PROPOSAL / "acceptance.json").read_bytes())
    reference = {item["id"]: item for item in original["source_cases"]}
    assert TARGET_A == reference["P16"]["expected"]["independent_solution"]["resolved_joint_targets_rad"]
    assert TARGET_B == reference["P02"]["expected"]["independent_solution"]["resolved_joint_targets_rad"]
    generated, cases = {}, []
    for case, grid in GRIDS.items():
        entry = next(path for path in RECOVERED if path.startswith("sources/" + case.lower() + "-"))
        files = manifest(entry)
        file_path = case.lower() + ".files.json"
        if file_path in RECOVERED:
            assert (HERE / file_path).read_bytes() == encoded(files)
        else:
            generated[file_path] = encoded(files)
        revision, closure = identity(files)
        assert revision == REVISIONS[case], case
        source = (HERE / entry).read_bytes()
        samples = []
        for clock, side in grid:
            t = Q(clock)
            data, coordinates, rates = state_data(case, t, side)
            samples.append({"time": rational(t), "time_seconds": clock, "side": side,
                            "physical": pose(coordinates, rates),
                            "reaches": {path: projection(case, path, row, coordinates, rates, t, side, revision, source)
                                        for path, row in data.items()}})
        failure = None
        if case == "L04":
            failure = {"time_seconds": "0.5", "valid_until_side": "before", "action_path": "reach_b",
                "reach_code": "reach_unreachable", "category": "invalid", "code": "OKL-E-REACH", "phase": "admission",
                "request_status": "rejected", "run_status": "failed", "whole_boundary_rollback": True,
                "no_after_side": True, "no_new_artifact": True, "unchanged_prior_action": "reach_a",
                "pending_failed_action": "reach_b", "retained_claims": JOINT_IDS}
        cases.append({"id": case, "entry_source": entry, "file_manifest": file_path,
                      "file_manifest_sha256": sha(encoded(files)), "source_sha256": sha(source),
                      "source_bytes": len(source), "program_revision": revision, "source_manifest": closure,
                      "expected_object_paths": ["rig", "rig.arm", "rig.arm.forearm", "rig.arm.upper", "rig.column", "rig.tool"],
                      "expected_visible_paths": ["rig", "rig.arm.forearm", "rig.arm.upper", "rig.column", "rig.tool"],
                      "unchanged_native_geometry_and_materials_required": True,
                      "scene_duration_seconds": "4" if case in ("L01", "L03") else "2",
                      "sample_side_count": len(samples), "action_state_count": sum(len(s["reaches"]) for s in samples),
                      "failure": failure, "samples": samples})
    acceptance = {"schema_version": "ontokin.proposed-planar-reach-lifecycle-reconstruction/0.1",
        "proposal_version": "0.1.0-draft.2", "status": "new_expected_preparation_not_executed",
        "reconstruction": {"historical_acceptance_recovered": False, "sample_grid_recovered": False,
            "semantic_cases_recovered": True, "sample_grid": "New fixed grid preserving retained semantic boundary coverage and prior 51/86 inventory; not historical byte recovery."},
        "source_case_count": len(cases), "sample_side_count": sum(c["sample_side_count"] for c in cases),
        "action_state_count": sum(c["action_state_count"] for c in cases),
        "source_runtime_executed": False, "agent_sqlite_executed": False, "glb_or_destination_executed": False,
        "author_script_sha256": sha(Path(__file__).read_bytes()), "oracle_sha256": sha((PROPOSAL / "oracle.py").read_bytes()),
        "oracle_authority": "Original independent Decimal/Fraction equations; no production parser, solver, evaluator or exporter imported.",
        "comparison": {"target_coordinates": "exact_binary64", "sampled_joint_coordinates": "exact_binary64_from_exact_affine_rationals",
                       "rates": "exact_binary64_from_exact_rationals",
                       "derived_poses": "Retain the adopted per-field source/delivery tolerances; this reconstruction changes no release tolerance.",
                       "pure_checker_libm_crosscheck_tolerance": 2e-12,
                       "terminal_goal_residual_max_m": 1e-9, "clocks": "exact_rational"},
        "source_cases": cases}
    assert (acceptance["sample_side_count"], acceptance["action_state_count"]) == (51, 86)
    generated["acceptance.json"] = encoded(acceptance)
    protocol_spec = importlib.util.spec_from_file_location("new_protocol_preparation", HERE / "author_protocol.py")
    protocol = importlib.util.module_from_spec(protocol_spec)
    protocol_spec.loader.exec_module(protocol)
    protocol_cases, release_probes = protocol.build(reference, {c["id"]: c for c in cases})
    generated["protocol-cases.json"] = encoded(protocol_cases)
    generated["release-probes.json"] = encoded(release_probes)
    provenance = {"schema_version": "ontokin.reach-supplement-reconstruction/0.1", "status": "new_preparation_not_adopted",
        "historical_commit": "f3fce69935273848d0b78c0f7999bef08d79b55b",
        "historical_commit_available": False, "exact_recovered_files": [member(p) for p in sorted(RECOVERED)],
        "exact_unchanged_libraries": [member(p.relative_to(HERE).as_posix()) for p in sorted((HERE / "libraries").glob("*.ok"))],
        "historical_lost_files": [{"path": p, "bytes": size, "sha256": "sha256:" + digest, "contents_recovered": False}
                                  for p, (size, digest) in sorted(LOST.items())],
        "new_reconstructions": sorted([*generated, "recording-probe-inputs.json", "effective-recording-probes.json"]),
        "prior_inventory": {"sample_sides": 51, "action_states": 86, "protocol_steps": 42},
        "current_inventory": {"sample_sides": 51, "action_states": 86, "protocol_steps": 42},
        "inventory_difference": 0, "inventory_equality_is_not_historical_content_equality": True,
        "recording_probe_references": "recording-probes.json is preserved verbatim. Its acceptance/protocol/inventory base hashes identify LOST historical files, not the new files with those names. Its preservation statement describes the historical addendum, not this reconstruction. verify_recording_probes.py verifies this distinction.",
        "known_program_revisions": REVISIONS,
        "oracle_input": {"path": "../oracle.py", "sha256": sha((PROPOSAL / "oracle.py").read_bytes())},
        "original_corpus_input": {"path": "../acceptance.json", "sha256": sha((PROPOSAL / "acceptance.json").read_bytes())},
        "source_runtime_executed": False, "agent_sqlite_executed": False, "glb_or_destination_executed": False}
    generated["reconstruction.json"] = encoded(provenance)
    inputs = sorted(set(RECOVERED) | {p.relative_to(HERE).as_posix() for p in (HERE / "libraries").glob("*.ok")})
    generated["recording-probe-inputs.json"] = encoded({
        "schema_version": "ontokin.reach-recording-probe-input-closure/0.1",
        "status": "new_reconstruction_input_closure_not_execution",
        "scope": "Exact recovered inputs plus newly reconstructed lifecycle/protocol preparation. This closure replaces only the historical inventory role in effective-recording-probes.json.",
        "members": [member(p, generated.get(p)) for p in sorted(set(inputs) | set(generated))],
        "authoring_inputs": [member("author_supplements.py"), member("author_protocol.py")],
        "self_and_binding_excluded_to_avoid_circular_hashes": True})
    historical_record = json.loads((HERE / "recording-probes.json").read_bytes())
    rebindings = []
    for old in historical_record["base_inputs"]:
        new_path = "recording-probe-inputs.json" if old["path"] == "generated-members.json" else old["path"]
        fresh = member(new_path, generated.get(new_path))
        rebindings.append({"historical_input": old, "effective_input": fresh,
                           "identity_unchanged": old["sha256"] == fresh["sha256"],
                           "reason": "Exact recovered input" if old["sha256"] == fresh["sha256"] else
                                     "Explicit new reconstruction replaces unavailable historical preparation; no claim of byte equality"})
    generated["effective-recording-probes.json"] = encoded({
        "schema_version": "ontokin.reach-recording-probe-effective-binding/0.1",
        "proposal_version": "0.1.0-draft.2", "status": "new_expected_preparation_not_adopted_or_executed",
        "historical_record": member("recording-probes.json"), "input_rebindings": rebindings,
        "effective_probe": historical_record["probes"][0],
        "probe_equality_rule": "effective_probe must equal the complete historical Q16 record: source, manifest, bundle, clocks, phases, expected overlap and future mutation are unchanged.",
        "historical_target_solution_reference": "The unchanged probe retains its original ../rounding-certificates.json reference. Original P16 expected target values supply the available independent target reference; the integrated numeric proof must independently certify those identical targets before adoption.",
        "effective_target_solution_reference": {"path": "../acceptance.json", "sha256": sha((PROPOSAL / "acceptance.json").read_bytes()),
            "case_id": "P16", "json_path": "source_cases[id=P16].expected.independent_solution.resolved_joint_targets_rad"},
        "unavailable_historical_references_silently_accepted": False,
        "source_runtime_executed": False, "agent_sqlite_executed": False, "glb_or_destination_executed": False})
    generated["generated-members.json"] = encoded({"schema_version": "ontokin.reach-supplement-members/0.1",
        "status": "new_reconstruction_inventory", "self_excluded": "generated-members.json",
        "members": [member(p, generated.get(p)) for p in sorted(set(inputs) | set(generated))],
        "authoring_inputs": [member("author_supplements.py"), member("author_protocol.py")],
        "source_and_agent_execution": False})
    return generated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    outputs = build()
    for path, data in outputs.items():
        target = HERE / path
        if args.write:
            target.write_bytes(data)
        elif not target.is_file() or target.read_bytes() != data:
            raise SystemExit("Preparation reproduction mismatch: " + path)
    print(json.dumps({"status": "written" if args.write else "reproduced", "generated_file_count": len(outputs),
                      "sample_sides": 51, "action_states": 86, "protocol_steps": 42,
                      "source_runtime_executed": False, "agent_sqlite_executed": False, "glb_or_destination_executed": False}, sort_keys=True))


if __name__ == "__main__":
    main()
