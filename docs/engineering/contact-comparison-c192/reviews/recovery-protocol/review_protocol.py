#!/usr/bin/env python3
"""Read-only C192 recovery audit; writes only its requested JSON receipt.

No native build, simulation, original trial, receiving execution, or remote write
is performed. The old repository supplies read-only Git and saved-run provenance.
"""
import argparse
import ast
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tarfile


BASE = "afae5f59558bc90200691f6727709124d2e119ea"
CANDIDATE = "0dd0e1fb44abb73d2fef65bc3a318c54ca2ea13f"
FREEZE = "9d1118f63195c8458aa804f2a99922cc780365aa"
SCOPE = "docs/engineering/contact-comparison-c192"
COMMITS = {
    "ok-edit": "721f3691935cadf0d11cead973db11358071d33b",
    "ok-reuse": "9a98e15ad242ddc0d20288fa8f43e6ef44e164c6",
    "python-edit": "375f0df7bb63e8d7b72c7f0cf41643db3000da22",
    "python-reuse": "f3b1b5fa89e1e19075793e0c75b3e68b53c5a844",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def timestamp(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def literal_design(data):
    tree = ast.parse(data)
    assert len(tree.body) == 2 and isinstance(tree.body[0], ast.Expr)
    assert isinstance(tree.body[0].value, ast.Constant)
    assert isinstance(tree.body[0].value.value, str)
    node = tree.body[1]
    assert isinstance(node, ast.Assign) and len(node.targets) == 1
    assert isinstance(node.targets[0], ast.Name) and node.targets[0].id == "DESIGN"
    return ast.literal_eval(node.value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--old-repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    scope = repo / SCOPE
    checks, commands = [], []

    def check(name, passed, evidence):
        checks.append({"id": name, "pass": bool(passed), "evidence": evidence})

    def command(argv, cwd=repo):
        result = subprocess.run(argv, cwd=cwd, capture_output=True)
        commands.append({"argv": argv, "cwd": str(cwd), "returncode": result.returncode,
                         "stdout": result.stdout.decode(), "stderr": result.stderr.decode()})
        return result

    def git_bytes(revision, path, cwd=repo):
        result = subprocess.run(["git", "show", revision + ":" + path], cwd=cwd, capture_output=True)
        assert result.returncode == 0, result.stderr.decode()
        return result.stdout

    def read_json(path):
        return json.loads((scope / path).read_text())

    freeze = read_json("frozen/INPUT-FREEZE.json")
    dispatch = read_json("evidence/dispatch.json")
    accounting = read_json("evidence/accounting.json")
    first_scores = read_json("evidence/first-edit-scores.json")
    results = read_json("results.json")
    freeze_identity = command(["git", "show", "-s", "--format=%H %T %cI", FREEZE])
    frozen_commit_time = timestamp(freeze_identity.stdout.decode().split()[-1])
    observations = [timestamp(r["first_observed_utc"]) for r in accounting["phases"] if r["phase"] == "edit"]
    chronology = timestamp(freeze["frozen_at_utc"]) < frozen_commit_time < timestamp(dispatch["dispatch_prepared_at_utc"]) < min(observations)
    check("pre_dispatch_freeze", chronology and dispatch["frozen_commit"] == FREEZE,
          {"frozen_at_utc": freeze["frozen_at_utc"], "freeze_commit": FREEZE,
           "commit_utc": dt.datetime.fromtimestamp(frozen_commit_time, dt.timezone.utc).isoformat(),
           "dispatch_prepared_at_utc": dispatch["dispatch_prepared_at_utc"],
           "first_observations": [r["first_observed_utc"] for r in accounting["phases"] if r["phase"] == "edit"],
           "scope": "Git and saved timestamps; provider spawn telemetry is unavailable"})

    freeze_errors = []
    for name, expected in freeze["files"].items():
        current = (repo / name).read_bytes()
        at_freeze = git_bytes(FREEZE, name)
        if len(current) != expected["bytes"] or sha(current) != expected["sha256"] or current != at_freeze:
            freeze_errors.append(name)
    check("freeze_identity", not freeze_errors and git_bytes(FREEZE, SCOPE + "/frozen/INPUT-FREEZE.json") == (scope / "frozen/INPUT-FREEZE.json").read_bytes(),
          {"files_checked": len(freeze["files"]), "failures": freeze_errors,
           "manifest_sha256": sha((scope / "frozen/INPUT-FREEZE.json").read_bytes())})

    historical = command(["git", "diff", "--name-only", BASE, CANDIDATE, "--", ".", ":!README.md", ":!STATUS.md", ":!" + SCOPE])
    check("historical_preservation", historical.returncode == 0 and historical.stdout == b"",
          {"base": BASE, "candidate": CANDIDATE,
           "scope": "Every tracked path outside README, STATUS and the C192 record is byte-identical"})

    participant_history = []
    for route in ("ok", "python"):
        first, reuse = COMMITS[route + "-edit"], COMMITS[route + "-reuse"]
        row = {"route": route, "edit_commit": first, "reuse_commit": reuse}
        for phase, commit, expected_parent in (("edit", first, FREEZE), ("reuse", reuse, first)):
            info = command(["git", "show", "-s", "--format=%H %P %cI", commit], args.old_repo)
            parts = info.stdout.decode().split()
            assert info.returncode == 0 and len(parts) == 3
            row[phase + "_parent"] = parts[1]
            row[phase + "_commit_time"] = parts[2]
            assert parts[1] == expected_parent
        prefix = SCOPE + "/participants/" + route
        old_files = command(["git", "ls-tree", "-r", "--name-only", first, "--", prefix], args.old_repo).stdout.decode().splitlines()
        errors = [name for name in old_files if git_bytes(first, name, args.old_repo) != (repo / name).read_bytes() or git_bytes(first, name, args.old_repo) != git_bytes(reuse, name, args.old_repo)]
        changed = command(["git", "diff", "--name-only", FREEZE, reuse], args.old_repo).stdout.decode().splitlines()
        row.update(first_submission_files=len(old_files), original_files_changed=errors,
                   participant_changes_outside_scope=[name for name in changed if not name.startswith(prefix + "/")])
        participant_history.append(row)
    check("participant_git_provenance", all(not r["original_files_changed"] and not r["participant_changes_outside_scope"] for r in participant_history), participant_history)

    ok = [(scope / name).read_bytes() for name in ("starters/design.ok", "participants/ok/sources/01-edit.ok", "participants/ok/sources/02-reuse.ok")]
    py = [(scope / name).read_bytes() for name in ("starters/design.py", "participants/python/design-edit.py", "participants/python/design-reuse.py")]
    localized = ok[1] == ok[0].replace(b"at = [380, 130, -220][mm];", b"at = [362.5, 130, -220][mm];") and ok[2] == ok[1].replace(b"at = [362.5, 130, -220][mm];", b"at = [372.5, 130, -220][mm];")
    localized = localized and py[1] == py[0].replace(b"'at_mm': [380, 130, -220]", b"'at_mm': [362.5, 130, -220]") and py[2] == py[1].replace(b"'at_mm': [362.5, 130, -220]", b"'at_mm': [372.5, 130, -220]")
    designs = [literal_design(data) for data in py]
    for index, target in enumerate((380, 362.5, 372.5)):
        expected = copy.deepcopy(designs[0])
        expected["parts"]["left_stop"]["at_mm"][0] = target
        localized = localized and designs[index] == expected
    localized = localized and (scope / "participants/ok/sources/00-starter.ok").read_bytes() == ok[0] and (scope / "participants/python/source-00-starter.py").read_bytes() == py[0]
    check("source_localization", localized, {"only_changed_field": "parts.left_stop.at_mm[0]", "targets_mm": [380, 362.5, 372.5],
          "ok_sha256": [sha(data) for data in ok], "python_sha256": [sha(data) for data in py],
          "python_ast": "one docstring plus one literal DESIGN assignment; no source calls"})

    with tarfile.open(scope / "evidence.tar.xz") as archive:
        data = {member.name: archive.extractfile(member).read() for member in archive.getmembers() if member.isfile()}
        manifest = json.loads(data["MANIFEST.json"])
        errors = [name for name, expected in manifest["files"].items() if len(data[name]) != expected["bytes"] or sha(data[name]) != expected["sha256"]]
        check("final_archive_inventory", not errors and set(data) == set(manifest["files"]) | {"MANIFEST.json"},
              {"files": len(manifest["files"]), "archive_sha256": sha((scope / "evidence.tar.xz").read_bytes()), "failures": errors})
        recorded_archive = read_json("evidence/archive.json")
        check("final_archive_receipt", recorded_archive["sha256"] == sha((scope / "evidence.tar.xz").read_bytes()) and recorded_archive["manifest_sha256"] == sha(data["MANIFEST.json"]), recorded_archive)
        context = json.loads(data["CONTEXT.json"])
        builds = context["participant_builds"]
        old_runs = args.old_repo.parent / "c192-runs"
        old_receipts = {"c192-runs/" + str(path.relative_to(old_runs)): path.read_bytes()
                        for path in old_runs.rglob("delivery.json")}
        expected_receipts = {entry["build"] + "/delivery.json" for entry in builds}
        check("saved_attempt_inventory", set(old_receipts) == expected_receipts
              and all(content == data[name] for name, content in old_receipts.items()),
              {"original_saved_delivery_receipts": len(old_receipts),
               "archive_delivery_receipts": len(expected_receipts),
               "paths": sorted(old_receipts),
               "scope": "All saved receipts in the original C192 run directory; no provider-level absence-of-other-work claim"})
        stage_rows = []
        for entry in builds:
            prefix = entry["build"] + "/"
            delivery = json.loads(data[prefix + "delivery.json"])
            stage = next(name.rsplit("/", 1)[0] for name in data if name.startswith(prefix) and name.endswith("/raw.glb"))
            route = delivery["route"]
            source_name = "source.ok" if route == "ok" else "source.py"
            expected_source = (ok if route == "ok" else py)[1 if entry["case"] == "edit" else 2]
            expected_design = designs[1 if entry["case"] == "edit" else 2]
            implementations = [name for name in data if name.startswith(stage + "/implementation/")]
            implementation_ok = len(implementations) == 11 and all(data[name] == (repo / "prototypes/guided_contact_v01" / name.rsplit("/", 1)[1]).read_bytes() for name in implementations)
            source_ok = data[stage + "/" + source_name] == expected_source and delivery["source_sha256"] == sha(expected_source) and data[prefix + "submitted-source." + ("ok" if route == "ok" else "py")] == expected_source
            canonical_ok = json.loads(data[stage + "/canonical-input.json"]) == expected_design
            cost = delivery["cost"]
            limits_ok = cost["requested_operations"] == cost["host_operations_ceiling"] == 1000000 and cost["requested_elapsed_ms"] == cost["host_elapsed_ms_ceiling"] == 80000
            rejected = delivery["returncode"] == 1 and delivery["successful"] is False and delivery["artifact_directory"] is None
            native_command = json.loads(data[stage + "/native-command.json"])
            row = {"id": entry["id"], "route": route, "case": entry["case"], "stage": stage,
                   "source_unchanged": source_ok and delivery["source_unchanged_during_build"], "canonical_matches_source": canonical_ok,
                   "retained_implementation_files": len(implementations), "implementation_matches_freeze": implementation_ok,
                   "backend_matches_freeze": data[stage + "/backend.json"] == (repo / "docs/language-design/guided-contact-v0.1/backend.json").read_bytes(),
                   "direct_runner_matches_freeze": route != "python" or data[stage + "/direct-runner.py"] == (scope / "shared/direct_runner.py").read_bytes(),
                   "limits_unchanged": limits_ok, "unaccepted": rejected,
                   "native_command": native_command,
                   "build_elapsed_s": delivery["elapsed_s"],
                   "hashes": {name: sha(data[stage + "/" + name]) for name in (source_name, "canonical-input.json", "native-transforms.json", "native-trace.csv", "raw.glb", "final.glb", "scene.blend")}}
            stage_rows.append(row)
        all_ok = len(stage_rows) == 6 and all(all(r[key] for key in ("source_unchanged", "canonical_matches_source", "implementation_matches_freeze", "backend_matches_freeze", "direct_runner_matches_freeze", "limits_unchanged", "unaccepted")) for r in stage_rows)
        check("participant_builds", all_ok, stage_rows)

        equal_keys = ("canonical-input.json", "native-transforms.json", "native-trace.csv", "raw.glb", "final.glb")
        equality = {case: {key: len({r["hashes"][key] for r in stage_rows if r["case"] == case}) == 1 for key in equal_keys} for case in ("edit", "reuse")}
        check("cross_route_and_regeneration_equality", all(all(v.values()) for v in equality.values()), equality)

        baseline = []
        for route in ("ok", "python"):
            prefix = "c192-setup/" + route + "-baseline/"
            command_row = json.loads(data[prefix + "command.json"])
            stage = next(name.rsplit("/", 1)[0] for name in data if name.startswith(prefix) and name.endswith("/raw.glb"))
            reopen_command = json.loads(data[prefix + "reopen.command.json"])
            native = json.loads(data[stage + "/native-transforms.json"])
            baseline.append({"route": route, "successful": command_row["successful"],
                             "canonical_matches_starter": json.loads(data[stage + "/canonical-input.json"]) == designs[0],
                             "reopen_returncode": reopen_command["returncode"],
                             "reopen_equal": native == json.loads(data[prefix + "reopen/native-transforms.json"]) and len(native) == 481,
                             "complete_before_freeze": command_row["finished_unix_s"] < timestamp(freeze["frozen_at_utc"]) and reopen_command["started_unix_s"] + reopen_command["elapsed_s"] < timestamp(freeze["frozen_at_utc"]),
                             "hashes": {key: sha(data[stage + "/" + key]) for key in equal_keys}})
        check("equivalent_prepared_starters", all(r["successful"] and r["canonical_matches_starter"] and r["reopen_returncode"] == 0 and r["reopen_equal"] and r["complete_before_freeze"] for r in baseline) and baseline[0]["hashes"] == baseline[1]["hashes"], baseline)

        phase1_receipt = read_json("evidence/phase1-archive.json")
        with tarfile.open(scope / "phase1-evidence.tar.xz") as first:
            first_data = {m.name: first.extractfile(m).read() for m in first.getmembers() if m.isfile()}
        phase1_errors = [name for name, expected in phase1_receipt["files"].items() if len(first_data[name]) != expected["bytes"] or sha(first_data[name]) != expected["sha256"]]
        retained_first_files = 0
        for name, content in first_data.items():
            if name.startswith("participants/"):
                final_name = "c192-runs/" + name.removeprefix("participants/")
                if data[final_name] != content:
                    phase1_errors.append(name)
                retained_first_files += 1
        check("first_phase_archive_preservation", not phase1_errors and set(first_data) == set(phase1_receipt["files"]) and sha((scope / "phase1-evidence.tar.xz").read_bytes()) == phase1_receipt["sha256"],
              {"archive_files": len(first_data), "participant_files_equal_in_final_archive": retained_first_files, "failures": phase1_errors,
               "phase1_sha256": phase1_receipt["sha256"], "manifest_location": "evidence/phase1-archive.json (external manifest)"})

    timings = []
    for row in accounting["phases"]:
        elapsed = timestamp(row["end_utc"]) - timestamp(row["first_observed_utc"])
        timings.append({"route": row["route"], "phase": row["phase"], "recorded_seconds": row["observed_wall_seconds"],
                        "recomputed_seconds": elapsed, "end_definition": row["end_definition"],
                        "within_allowance": elapsed < 1200, "native_builds": row["native_builds"],
                        "formal_submissions": row["formal_submissions"], "repair_rounds": row["repair_rounds"]})
    check("accounting", all(abs(r["recomputed_seconds"] - r["recorded_seconds"]) < 0.00001 and r["within_allowance"] and r["native_builds"] <= 6 and r["formal_submissions"] == 1 and r["repair_rounds"] == 0 for r in timings)
          and sum(r["native_builds"] for r in timings) == 6, timings)
    reuse_starts = [timestamp(r["first_observed_utc"]) for r in accounting["phases"] if r["phase"] == "reuse"]
    check("score_before_reuse", first_scores["scored_unix_s"] < min(reuse_starts) and all(r["source_sha256"] == sha(ok[1] if r["route"] == "ok" else py[1]) for r in first_scores["scores"]),
          {"scored_utc": dt.datetime.fromtimestamp(first_scores["scored_unix_s"], dt.timezone.utc).isoformat(),
           "same_first_source_hashes": True, "reuse_observations": [r["first_observed_utc"] for r in accounting["phases"] if r["phase"] == "reuse"]})
    check("usage_limits_disclosed", all(accounting[key] is None for key in ("exact_provider_model_snapshot", "provider_tokens", "provider_cost", "hidden_model_turns")),
          {key: accounting[key] for key in ("exact_provider_model_snapshot", "provider_tokens", "provider_cost", "hidden_model_turns", "usage_unavailability", "reusable_setup", "interpretation")})
    check("all_outcomes_remain_rejected", results["accepted_first_edit_deliveries"] == results["accepted_second_target_deliveries"] == 0 and all(r["experimental_delivery_pass"] is False and r["submitted"]["pass"] is False and r["submitted"]["build_successful"] is False and r["submitted"]["playback_pass"] is True and r["submitted"]["mapping_pass"] is False for r in results["native_verification"]),
          {"experiment_status": results["experiment_status"], "cases": results["cases"], "accepted_deliveries": 0})

    receipt = {"review": "C192 recovery protocol/source audit", "reviewer": "c192_protocol_recovery",
               "finished_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "candidate": CANDIDATE, "baseline": BASE, "freeze": FREEZE,
               "python": sys.version, "platform": platform.platform(),
               "script_sha256": sha(Path(__file__).read_bytes()),
               "invocation": [sys.executable, *sys.argv],
               "read_only_provenance_repository": str(args.old_repo),
               "checks": checks, "commands": commands,
               "all_checks_pass": all(row["pass"] for row in checks),
               "operations": {"fresh_native_runs": 0, "original_trials_repeated": 0, "receiving_runs": 0,
                              "remote_writes": 0, "subagents_spawned": 0, "old_workspace_writes": 0},
               "launch_evidence_limit": "Fresh/default/empty-history/no-additional-agent and no-human-intervention statements are recorded coordinator/participant attestations. Git verifies frozen branch ancestry and retained sources; no raw launcher transcript or provider metadata is available.",
               "publication_scope": "This source audit does not establish current remote main, a PR merge, lease release, final handoff contents or complete release acceptance."}
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"all_checks_pass": receipt["all_checks_pass"], "checks": len(checks), "failed": [r["id"] for r in checks if not r["pass"]], "receipt": str(args.out)}))
    return 0 if receipt["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
