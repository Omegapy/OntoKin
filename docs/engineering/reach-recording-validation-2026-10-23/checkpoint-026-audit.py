"""Independent checkpoint-026 archive inspection; never imports product code.

Reads the split archive entirely in memory and writes only the external audit
report and a hash-verified reconstruction of an earlier derived review. No
archive extraction, product execution, tests, or Git mutation is performed.
"""
from __future__ import annotations

import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import statistics
import subprocess
import zipfile
import zlib


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parent
EVIDENCE = WORKSPACE / "evidence026"
FINAL = "327e778cece3bb292f3e64751506dff364e4ee87"
LOCAL = "f8af193f9147e22aaed8d47e5400f3db33f72d92"
BASE = "6bfb0944c5c9c16f64beb0138aaac69dd5ee22db"
TREE = "e5a11ac55d8740ce0b2b0fadbe06ea7a0080c609"
EXPECTED_FAILURES = ["P09", "P11", "P16", "P23", "L03"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(repository, *arguments):
    return subprocess.check_output(["git", "-C", str(repository), *arguments])


def object_sha(kind, data):
    return hashlib.sha1(kind.encode() + b" " + str(len(data)).encode() + b"\0" + data).hexdigest()


def inventory(snapshot):
    return {row["path"]: (row["bytes"], row["sha256"].removeprefix("sha256:")) for row in snapshot["files"]}


def implementation_digest(commit):
    names = git(REPO, "ls-tree", "-r", "--name-only", commit, "ontokin").decode().splitlines()
    digest = hashlib.sha256()
    for name in sorted(n for n in names if n.endswith(".py") and len(Path(n).parts) == 2):
        digest.update(Path(name).name.encode() + b"\0" + git(REPO, "show", commit + ":" + name) + b"\0")
    return digest.hexdigest()


def main():
    summary_bytes = (HERE / "checkpoint-026.json").read_bytes()
    manifest_bytes = (HERE / "checkpoint-026-manifest.json").read_bytes()
    summary = json.loads(summary_bytes)
    manifest = json.loads(manifest_bytes)
    checks = []
    notes = []

    def checked(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append({"check": label, "passed": True})

    parts = summary["archive"]["parts"]
    checked("eight ordered uniquely named split parts", [x["path"] for x in parts] == [f"checkpoint-026.zip.part{i:03d}" for i in range(1, 9)])
    bodies = []
    for row in parts:
        data = (HERE / row["path"]).read_bytes()
        checked(row["path"] + " bytes and SHA256", len(data) == row["bytes"] and sha(data) == row["sha256"])
        bodies.append(data)
    joined = b"".join(bodies)
    checked("joined archive identity", len(joined) == summary["archive"]["bytes"] == 6834663 and sha(joined) == summary["archive"]["sha256"] == "4741da9ab50da2966122243d1ca2101b4b98e6eae75c2ae8d4f01a32ecf373c5")
    members = {}
    with zipfile.ZipFile(io.BytesIO(joined)) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        checked("385 unique archive and manifest members", len(names) == len(set(names)) == len(set(n.casefold() for n in names)) == len(manifest["members"]) == summary["archive"]["member_count"] == 385)
        for info in infos:
            path = PurePosixPath(info.filename)
            checked("safe regular member " + info.filename, not path.is_absolute() and str(path) == info.filename and not any(x in ("", ".", "..") for x in path.parts) and not any(x in info.filename for x in ("\\", ":", "\0")) and not info.is_dir() and not (info.flag_bits & 1) and stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG))
            data = archive.read(info)
            checked("CRC " + info.filename, (zlib.crc32(data) & 0xFFFFFFFF) == info.CRC and len(data) == info.file_size)
            members[info.filename] = data
    listed = {row["path"]: row for row in manifest["members"]}
    checked("manifest exact membership", len(listed) == len(manifest["members"]) and set(listed) == set(members))
    for name, data in members.items():
        row = listed[name]
        checked("member hash " + name, row["bytes"] == len(data) and row["sha256"] == sha(data))
        live_name = name.removeprefix("execution/") if name.startswith("execution/") else name
        checked("preserved evidence bytes " + name, (EVIDENCE / live_name).read_bytes() == data)

    def read(name):
        return json.loads(members[name])

    pub = read("publication/source-commit.json")
    verification = read("publication/source-verification.json")
    checked("published parent and exact same-tree local cut", pub["sha"] == FINAL and pub["tree"]["sha"] == TREE and [x["sha"] for x in pub["parents"]] == [BASE] and verification["commit"] == FINAL and verification["local_review_commit"] == LOCAL and verification["tree_identical"] and git(REPO, "rev-parse", FINAL + "^{tree}").decode().strip() == git(REPO, "rev-parse", LOCAL + "^{tree}").decode().strip() == TREE)
    cuts = read("local-review-cuts/index.json")["cuts"]
    early = read("local-review-cuts/4f6333119deaba1a52f07d83941d126fbbb19328/identity.json")
    checked("earliest draft explicitly unexecuted and unaccepted", early["executed"] is False and early["accepted"] is False)
    for cut in cuts + [early]:
        commit = cut["commit"]
        prefix = "local-review-cuts/" + commit + "/"
        identity = read(prefix + "identity.json")
        checked("preserved cut identity " + commit, identity == cut)
        raw = members[prefix + "commit.raw"]
        checked("raw Git commit and tree " + commit, object_sha("commit", raw) == commit and raw.splitlines()[0] == ("tree " + cut["tree"]).encode())
        repository = WORKSPACE / cut.get("repository", "OntoKin-term-worker")
        checked("local Git commit bytes " + commit, git(repository, "cat-file", "commit", commit) == raw)
        for row in cut["files"]:
            member = prefix + row["path"]
            if member not in members and cut is early:
                member = prefix + Path(row["path"]).name
            data = members[member]
            checked("preserved source blob " + commit + ":" + row["path"], len(data) == row["bytes"] and sha(data) == row["sha256"] and git(repository, "show", commit + ":" + row["path"]) == data and ("git_blob_sha" not in row or object_sha("blob", data) == row["git_blob_sha"]))
    final_files = read("local-review-cuts/" + FINAL + "/identity.json")["files"]
    checked("only runtime, dedicated test and proof changed from checkpoint025", sorted(git(REPO, "diff", "--name-only", BASE, FINAL).decode().splitlines()) == sorted(x["path"] for x in final_files))
    for row in final_files:
        checked("local and published source member equality " + row["path"], members["local-review-cuts/" + LOCAL + "/" + row["path"]] == members["local-review-cuts/" + FINAL + "/" + row["path"]])
    source_review = read("reviews/candidate-source-review-002.json")
    checked("accepted runtime equals independently reviewed worker bytes", sha(members["local-review-cuts/" + FINAL + "/ontokin/reach_conformance.py"]) == source_review["file"]["sha256"] and all(x["status"] == "resolved" for x in source_review["findings"]))

    run_names = ["candidate-focused-001", "candidate-focused-002", "candidate-focused-003", "candidate-controls-001", "candidate-controls-l03-002", "integrated-focused-001", "integrated-original28-001", "control-original28", "control-p09", "control-p09-observed"]
    snapshots = {}
    for name in run_names:
        before = read("execution/" + name + "/inputs-before.json")
        after = read("execution/" + name + "/inputs-after.json")
        report = read("execution/" + name + "/report.json")
        identity = before.get("git", {"commit": before.get("git_commit"), "tree": before.get("git_tree"), "status": before.get("git_status")})
        checked("stable clean source inputs " + name, before == after and report["inputs_stable"] and identity["commit"] == report["source_commit"] and identity["tree"] == report["source_tree"] and identity["status"] == "" and before.get("omitted_historical_archives", []) == [])
        snapshots[name] = before
    final_inventory = inventory(snapshots["integrated-focused-001"])
    for name in ["candidate-focused-003", "candidate-controls-001", "candidate-controls-l03-002", "integrated-original28-001"]:
        checked("same-tree input inventory " + name, inventory(snapshots[name]) == final_inventory)
    tree_blobs = {}
    for line in git(REPO, "ls-tree", "-r", FINAL).decode().splitlines():
        metadata, name = line.split("\t", 1)
        mode, kind, blob = metadata.split()
        tree_blobs[name] = (mode, blob)
    checked("complete candidate input file inventory", set(tree_blobs) == set(final_inventory) and len(final_inventory) == 1737 and sum(x[0] for x in final_inventory.values()) == 369596282)
    checked("exact input receipt Git blobs", all(tree_blobs[x["path"]] == (x["mode"], x["git_blob_sha1"]) for x in snapshots["integrated-focused-001"]["files"]))
    closure = read("recovery/tracked-closure.json")
    checked("control tracked closure", closure["source_commit"] == BASE and closure["tracked_files"] == 1735 and closure["bytes"] == 369544915 and not closure["errors"] and inventory(closure) == inventory(snapshots["control-original28"]) == inventory(snapshots["control-p09"]) == inventory(snapshots["control-p09-observed"]))
    base_inventory = inventory(snapshots["control-original28"])
    changed = [name for name in set(base_inventory) | set(final_inventory) if base_inventory.get(name) != final_inventory.get(name)]
    checked("receipt changes only accepted three source files", sorted(changed) == sorted(x["path"] for x in final_files))

    tests_by_run = {}
    expected = {"candidate-focused-001": (26, 25, 1), "candidate-focused-002": (27, 27, 0), "candidate-focused-003": (28, 28, 0), "integrated-focused-001": (121, 121, 0)}
    executed_commits = {"candidate-focused-001": "78bb6c701d3ebf71d173084544c57e06e71f09c6", "candidate-focused-002": "c7541956d8d0ae3558d995165c9074590d091270", "candidate-focused-003": LOCAL, "integrated-focused-001": FINAL}
    for name, (count, passed, errors) in expected.items():
        prefix = "execution/" + name + "/"
        report = read(prefix + "report.json")
        tests = read(prefix + "tests.json")
        log = members[prefix + "tests.log"]
        checked("exact test cut and preserved result " + name, report["source_commit"] == executed_commits[name] and report["test_count"] == tests["test_count"] == count and report["passed_count"] == passed and report["errors"] == tests["errors"] == errors and tests["failures"] == tests["skips"] == tests["expected_failures"] == tests["unexpected_successes"] == 0)
        checked("unique completed test IDs " + name, len(tests["started"]) == len(set(tests["started"])) == len(tests["results"]) == count and set(tests["started"]) == {x["test_id"] for x in tests["results"]} and sum(x["status"] == "passed" for x in tests["results"]) == passed)
        checked("complete log and executed driver " + name, report["test_log_complete"] and sha(log) == report["test_log_sha256"] and len(log) == report["test_log_bytes"] and sha(members[prefix + "executed-driver.py"]) == report["driver_sha256"])
        tests_by_run[name] = tests
    checked("121 includes all 28 dedicated tests without additive counting", {x for x in tests_by_run["integrated-focused-001"]["started"] if x.startswith("test_reach_certificate_term_reuse.")} == set(tests_by_run["candidate-focused-003"]["started"]))

    control = read("execution/control-original28/report.json")
    candidate = read("execution/integrated-original28-001/report.json")
    comparison = read("execution/original28-comparison.json")
    required = [f"P{i:02d}" for i in [*range(1, 24), 25, 26]] + ["L01", "L02", "L03"]
    checked("unchanged complete original28 selection", control["selected_cases"] == candidate["selected_cases"] == control["required_cases"] == candidate["required_cases"] == required and "--case" not in candidate["command"] and "--fps" not in candidate["command"])
    digests = {"control": implementation_digest(BASE), "candidate": implementation_digest(FINAL)}
    checked("independently recomputed implementation hashes", comparison["implementation_source_sha256"] == digests)
    failures = []
    savings = []
    for left, right, row in zip(control["deliveries"], candidate["deliveries"], comparison["rows"]):
        case = right["case_id"]
        checked("same original request " + case, left["case_id"] == case == row["case_id"] and all(left[key] == right[key] for key in ("status", "program_revision", "source_manifest", "options", "max_operations")) and right["max_operations"] == 100000)
        for run, result in [("control-original28", left), ("integrated-original28-001", right)]:
            checked("raw request and resource outcome " + run + "/" + case, read("execution/" + run + "/" + case + "/request-result.json") == result and result["elapsed_seconds"] * 1000 < 30000)
            if result["status"] == "passed":
                for key in ("artifact", "export_report"):
                    data = members["execution/" + run + "/" + result[key]["path"]]
                    checked("artifact receipt " + run + "/" + case + "/" + key, len(data) == result[key]["bytes"] and sha(data) == result[key]["sha256"].removeprefix("sha256:"))
        if right["status"] == "passed":
            old_prefix = "execution/control-original28/" + case + "/"
            new_prefix = "execution/integrated-original28-001/" + case + "/"
            a, b = read(old_prefix + "export-report.json"), read(new_prefix + "export-report.json")
            checked("identical GLB, validation and source units " + case, members[old_prefix + "scene.glb"] == members[new_prefix + "scene.glb"] and a["validation"] == b["validation"] and left["source_units"] == right["source_units"])
            checked("only verified implementation hash differs " + case, a.pop("source_code_sha256") == digests["control"] and b.pop("source_code_sha256") == digests["candidate"] and a == b)
            saving = left["operations"] - right["operations"]
            checked("positive complete request saving " + case, saving > 0 and saving == row["saved_operations"])
            savings.append(saving)
        else:
            checked("unchanged capped failure " + case, left["diagnostic"] == right["diagnostic"] and left["failure"] == right["failure"] == {"type": "OntoKinError", "message": "Construction exceeded max_operations."} and left["operations"] == right["operations"] == 100001 and row["completed_request_saving"] is None)
            failures.append(case)
    checked("23 completed requests and five unchanged failures", len(savings) == 23 and failures == EXPECTED_FAILURES and sum(savings) == 1575 and [min(savings), max(savings)] == [30, 160])
    checked("summary original28 rows and caveats", summary["source_recordings"]["rows"] == comparison["rows"] and summary["source_recordings"]["failed"] == failures and summary["source_recordings"]["passed"] == 23 and summary["source_recordings"]["capped_failures_are_not_complete_costs"])

    pairs = []
    for run in ("candidate-controls-001", "candidate-controls-l03-002"):
        report = read("execution/" + run + "/report.json")
        checked("same-tree whole-prefix driver " + run, report["source_commit"] == LOCAL and report["source_tree"] == TREE and report["prefix_settings"] == {"end_seconds": "1/4", "fps": 4, "helpers": False} and report["original_complete_recording"] is False and sha(members["execution/" + run + "/executed-driver.py"]) == report["driver_sha256"])
        grouped = {}
        for row in report["rows"]:
            prefix = "execution/" + run + "/" + row["directory"] + "/"
            checked("raw prefix request " + prefix, read(prefix + "request-result.json") == row and sha(members[prefix + "scene.glb"]) == row["glb_sha256"] and len(members[prefix + "scene.glb"]) == row["glb_bytes"] and row["operations"] == row["work"]["operations"] and row["shared_operations"] < 100000 and row["elapsed_ms"] < 30000)
            grouped.setdefault((row["case_id"], row["repetition"]), {})[row["mode"]] = row
        for (case, repetition), group in grouped.items():
            a, b = group["control"], group["candidate"]
            ap = "execution/" + run + "/" + a["directory"] + "/"
            bp = "execution/" + run + "/" + b["directory"] + "/"
            checked("exact prefix equivalence " + run + "/" + case + "/" + str(repetition), members[ap + "scene.glb"] == members[bp + "scene.glb"] and members[ap + "export-report.json"] == members[bp + "export-report.json"] and a["shared_operations"] - b["shared_operations"] == a["operations"] - b["operations"] == {"P09": 30, "P11": 80, "L03": 30}[case])
            pairs.append((case, a, b))
    checked("all 14 pairs retained", len(pairs) == 14)
    for row in summary["whole_prefix_controls"]["shared_request_totals"]:
        case_pairs = [(a, b) for case, a, b in pairs if case == row["case_id"]]
        checked("summary complete shared counters " + row["case_id"], len(case_pairs) == row["pair_count"] and all(a["shared_operations"] == row["control_shared_operations"] and b["shared_operations"] == row["candidate_shared_operations"] and a["shared_operations"] - b["shared_operations"] == row["saved_shared_operations"] for a, b in case_pairs))
    l03 = [(a["elapsed_ms"], b["elapsed_ms"]) for case, a, b in pairs if case == "L03"]
    control_median = statistics.median(a for a, _ in l03)
    candidate_median = statistics.median(b for _, b in l03)
    timing = summary["whole_prefix_controls"]["L03_pooled_timing"]
    checked("pooled L03 timing and no speedup claim", len(l03) == 8 and control_median == timing["control_median_ms"] and candidate_median == timing["candidate_median_ms"] and candidate_median - control_median == timing["median_delta_ms"] == 12.782550002157222 and sum(b > a for a, b in l03) == timing["slower_pairs"] == 4 and sum(b < a for a, b in l03) == timing["faster_pairs"] == 4 and summary["whole_prefix_controls"]["elapsed_speedup_claimed"] is False)

    accepted = read("reviews/final-source-acceptance.json")
    performance = read("reviews/performance-review.json")
    earlier_performance = dict(performance)
    earlier_performance.pop("counter_semantics")
    earlier_performance.pop("whole_prefix_shared_request_totals")
    reconstructed = (json.dumps(earlier_performance, indent=2) + "\n").encode()
    for row in accepted["evidence_files"]:
        member = row["path"] if row["path"].split("/")[0] in ("reviews", "publication") else "execution/" + row["path"]
        data = reconstructed if row["path"] == "reviews/performance-review.json" else members[member]
        checked("prior acceptance bound evidence " + row["path"], len(data) == row["bytes"] and sha(data) == row["sha256"])
    checked("clarified performance contains only exact additive counter metadata", len(reconstructed) == 3954 and sha(reconstructed) == "855fa03be9dcb01f68f4c378c0fcc0eafe3144d1ea3897c960e6fb63a612d16e" and performance["whole_prefix_shared_request_totals"] == summary["whole_prefix_controls"]["shared_request_totals"] and performance["timing_speedup_claimed"] is False)
    reconstructed_name = "checkpoint-026-performance-before-counter-clarification.json"
    (HERE / reconstructed_name).write_bytes(reconstructed)
    notes.append({"id": "AR26-01", "severity": "informational", "status": "resolved_by_exact_hash_verification", "detail": "The earlier independent acceptance pins the pre-clarification derived performance review. The archived review adds only counter_semantics and whole_prefix_shared_request_totals. Removing precisely those two fields reproduces the earlier 3,954 bytes and captured SHA256 exactly; all raw execution evidence is unchanged. This audit binds the clarified archived version. The reconstructed prior derived report is preserved externally and is not a reconstruction of missing raw execution evidence.", "earlier_derived_report": {"path": reconstructed_name, "bytes": len(reconstructed), "sha256": sha(reconstructed)}, "clarified_archived_report": {"path": "reviews/performance-review.json", "bytes": len(members["reviews/performance-review.json"]), "sha256": sha(members["reviews/performance-review.json"])}})
    checked("release and product claims remain pending", summary["release_acceptance"] is False and summary["release_input_closure"] is False and summary["full_product_goal_completed"] is False and candidate["native_validation"] == candidate["browser_validation"] == "pending" and summary["focused_tests"]["full_regression"] is False and summary["focused_tests"]["integrated_includes_dedicated"])
    checked("observer limitation explicit", summary["diagnostics"]["enabled_candidate_neutral_profile_claimed"] is False and summary["diagnostics"]["completed_key_comparisons"] == 205 and summary["diagnostics"]["last_completed_key_operation"] == 99037)
    checked("failed and superseded attempts remain disclosed", read("reviews/first-execution-correction.json")["production_failure"] is False and comparison["earlier_comparison_attempt"]["status"] == "incorrect_analysis_assertion" and read("reviews/preservation-script-correction.json")["product_runs_reexecuted"] is False and all("unexecuted" in x["status"] for x in cuts if x["repository"] != "OntoKin"))
    checked("summary and manifest stable throughout audit", (HERE / "checkpoint-026.json").read_bytes() == summary_bytes and (HERE / "checkpoint-026-manifest.json").read_bytes() == manifest_bytes)
    review = {"schema_version": "ontokin.independent-checkpoint-archive-review/0.1", "checkpoint": 26, "reviewer": "/root/evidence_review", "reviewed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "passed", "blocking_findings": [], "notes": notes, "method": "Independent standard-library in-memory ZIP inspection, raw artifact/JSON/log comparisons and read-only Git-object verification in the coordinator-granted exclusive archive window. No product imports, runtime, tests, archive extraction, archive creation or Git mutation.", "source_commit": FINAL, "source_tree": TREE, "control_commit": BASE, "same_tree_local_execution_commit": LOCAL, "archive": {"bytes": len(joined), "sha256": sha(joined), "parts": len(parts), "members": len(members), "uncompressed_bytes": sum(map(len, members.values())), "part_member_hashes_and_crcs_verified": True, "safe_unique_regular_member_names": True, "all_archived_members_match_preserved_evidence": True}, "summary_sha256": sha(summary_bytes), "manifest_sha256": sha(manifest_bytes), "audit_script_sha256": sha(Path(__file__).read_bytes()), "source_and_execution": {"preserved_cuts": len(cuts) + 1, "all_cut_commit_and_blob_bytes_verified": True, "input_receipt_pairs_verified": len(run_names), "candidate_tracked_files": len(final_inventory), "candidate_tracked_bytes": sum(x[0] for x in final_inventory.values()), "integrated_passed": 121, "integrated_dedicated_subset": 28, "dedicated_same_tree_passed": 28, "test_counts_not_additive": True, "original28_passed": 23, "original28_failed": failures, "all_23_glb_bytes_and_validation_identical": True, "whole_export_reports_differ_only_in_independently_verified_implementation_hash": True, "all_failed_diagnostics_and_failure_type_message_unchanged": True, "completed_request_shared_savings_total": sum(savings), "whole_prefix_pairs": len(pairs), "whole_prefix_shared_totals": summary["whole_prefix_controls"]["shared_request_totals"], "L03_pooled_candidate_minus_control_median_ms": candidate_median - control_median, "elapsed_speedup_claimed": False}, "limitations": ["This is an archive integrity and scoped development-evidence audit; it is not full release input-closure or resulting-main verification.", "Full original recording gate remains 23/28; capped failures establish neither complete request cost nor complete request savings.", "Native/browser/visual, full regression and unexecuted compatibility roles remain pending.", "The neutral profiler disables the optimized path and is only claimed for the checkpoint025 control.", "Tracked historical archive receipts were compared against the recorded closure; historical unavailable raw logs were not reconstructed.", "GitHub branch and PR metadata in the summary is coordinator-observed context; no network status refresh was performed by this archive audit."], "release_acceptance": False, "full_product_goal_completed": False, "checks_passed": len(checks), "checks": checks}
    output = HERE / "checkpoint-026-archive-review.json"
    output.write_text(json.dumps(review, indent=2) + "\n")
    print(json.dumps({"status": review["status"], "checks_passed": len(checks), "review": str(output), "sha256": sha(output.read_bytes()), "bytes": output.stat().st_size, "reconstructed_prior_derived_report": reconstructed_name, "informational_notes": len(notes)}, indent=2))


if __name__ == "__main__":
    main()
