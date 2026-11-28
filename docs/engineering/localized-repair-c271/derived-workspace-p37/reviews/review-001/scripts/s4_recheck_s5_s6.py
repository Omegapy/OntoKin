"""W3 (C271-P37 S7): S5's module outcomes and S6's comparison with main, recomputed from the raw logs.

Loads MR's reviewed collector (macos-routine-p36/tooling/unit_log_outcomes.py) from the worktree and
calls only its reading functions (collect_log, Normalizer, compare_records, summary_comparison, unit_step);
it writes nothing itself. Every input is bound here by its SHA-256 from the Director's records. The
output holds labels, IDs, counts and reasons, never a machine path.

Usage: python3 -I -S -B s4_recheck_s5_s6.py WORKTREE LOCAL TMPDIR_RESOLVED OUTPUT
"""
import hashlib
import importlib.util
import json
import os
import sys

TOOL = "docs/engineering/localized-repair-c271/macos-routine-p36/tooling/unit_log_outcomes.py"
TOOL_SHA256 = "0b5269402005584ffa8c0fe4510a1f1d728f7922414a0d38cf841851e29cc75b"
MAIN_RUN = "checks/main-8e847c15-tmpdir-20261125T2110Z"


def sha256_file(path):
    with open(path, "rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def load_tool(worktree):
    path = os.path.join(worktree, TOOL)
    if sha256_file(path) != TOOL_SHA256:
        raise SystemExit("MR's collector differs from its reviewed bytes")
    spec = importlib.util.spec_from_file_location("unit_log_outcomes_w3", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows(result):
    return result["tests"] + result["fixtures"]


def brief_list(entries):
    return [{"id": entry["id"], "kind": entry["kind"],
             "baseline": None if entry["baseline"] is None else {"outcome": entry["baseline"]["outcome"],
                                                                 "reasons": entry["baseline"]["reasons"]},
             "candidate": None if entry["candidate"] is None else {"outcome": entry["candidate"]["outcome"],
                                                                   "reasons": entry["candidate"]["reasons"]}}
            for entry in entries]


def main(worktree, local, tmpdir, output):
    tool = load_tool(worktree)
    labels = [(local, "<local>"), (worktree, "<worktree>"), (tmpdir.rstrip("/"), "<tmp>")]

    def label(value):
        text = json.dumps(value)
        for old, new in labels:
            text = text.replace(old, new)
        return json.loads(text)

    out = {"schema": "w3.c271-p37.recheck-s5-s6/1", "tool": {"path": TOOL, "sha256": TOOL_SHA256}}
    s5_dir = os.path.join(local, "c271-p37/checks/s5-001")
    run = json.load(open(os.path.join(s5_dir, "S5-RUN.json")))
    normalize = tool.Normalizer({"steps": []}, [tmpdir])
    modules = []
    for module in run["modules"]:
        name = module["module"]
        log = os.path.join(s5_dir, module["log"])
        row = {"module": name, "exit": module["exit"], "log_sha256_matches_record": sha256_file(log) == module["log_sha256"]}
        candidate = tool.collect_log(open(log, "rb").read())
        row["candidate"] = {key: value for key, value in candidate["counts"]["by_outcome"].items() if value}
        row["candidate_fixtures"] = [(f["id"], f["outcome"]) for f in candidate["fixtures"]]
        row["candidate_footer"] = candidate["footer"]["result_line"]
        mi_log = os.path.join(local, "c271-p33/checks/final-003", name + ".txt")
        if module.get("mi_log_sha256"):
            row["mi_log_sha256_matches_record"] = sha256_file(mi_log) == module["mi_log_sha256"]
            mi = tool.collect_log(open(mi_log, "rb").read())
            row["mi"] = {key: value for key, value in mi["counts"]["by_outcome"].items() if value}
            row["mi_fixtures"] = [(f["id"], f["outcome"]) for f in mi["fixtures"]]
            unchanged, lists = tool.compare_records(rows(mi), rows(candidate), normalize, normalize)
            row["against_mi"] = {"unchanged": {k: v for k, v in unchanged.items() if v},
                                 "counts": {k: len(v) for k, v in lists.items() if v},
                                 "added_ids": [e["id"] for e in lists["added_ids"]],
                                 "removed_ids": [e["id"] for e in lists["removed_ids"]],
                                 "differences": brief_list([e for k in ("new_not_passing", "no_longer_failing",
                                                                        "different_outcome", "different_reason",
                                                                        "different_subtests", "different_skip_reason",
                                                                        "different_occurrences")
                                                            for e in lists[k]])}
        modules.append(row)
    out["s5_modules"] = modules
    # The storage module on the unchanged tree, against the candidate's run of it.
    baseline_log = os.path.join(local, "c271-p37/checks/s5-storage-baseline/tools.storage_tests.test_storage_identity.txt")
    candidate_log = os.path.join(s5_dir, "tools.storage_tests.test_storage_identity.txt")
    base = tool.collect_log(open(baseline_log, "rb").read())
    cand = tool.collect_log(open(candidate_log, "rb").read())
    unchanged, lists = tool.compare_records(rows(base), rows(cand), normalize, normalize)
    out["storage_candidate_against_unchanged_tree"] = {
        "baseline_log_sha256": sha256_file(baseline_log), "unchanged": {k: v for k, v in unchanged.items() if v},
        "counts": {k: len(v) for k, v in lists.items() if v},
        "not_passing": [{"id": r["id"].rsplit(".", 1)[-1], "outcome": r["outcome"], "reasons": r["reasons"]}
                        for r in cand["tests"] if r["outcome"] in tool.NOT_PASSING]}

    # S6: the routine at C against main's resolved-directory run.
    sides = {}
    for side, base_dir in (("baseline", os.path.join(local, MAIN_RUN)),
                           ("candidate", os.path.join(local, "c271-p37/routine/ordinary-001"))):
        summary_path = os.path.join(base_dir, "summary.json")
        log_path = os.path.join(base_dir, "logs/unit-tests.log")
        summary = json.load(open(summary_path))
        step = tool.unit_step(summary)
        raw = open(log_path, "rb").read()
        log_sha = hashlib.sha256(raw).hexdigest()
        result = tool.collect_log(raw)
        sides[side] = {"summary": summary, "result": result, "normalize": tool.Normalizer(summary, [tmpdir]),
                       "summary_sha256": sha256_file(summary_path), "log_sha256": log_sha,
                       "summary_names_log": (step.get("log_identity") or {}).get("sha256") == "sha256:" + log_sha}
    unchanged, lists = tool.compare_records(rows(sides["baseline"]["result"]), rows(sides["candidate"]["result"]),
                                            sides["baseline"]["normalize"], sides["candidate"]["normalize"])
    comparison = tool.summary_comparison(sides["baseline"]["summary"], sides["candidate"]["summary"])
    new_by_module = {}
    for entry in lists["new_not_passing"]:
        module = entry["id"].split(".")[0] if entry["kind"] == "test" else entry["id"]
        new_by_module.setdefault(module, []).append(entry["id"])
    out["s6"] = {
        "inputs": {side: {"summary_sha256": sides[side]["summary_sha256"], "log_sha256": sides[side]["log_sha256"],
                          "summary_names_its_log": sides[side]["summary_names_log"]} for side in sides},
        "footers": {side: sides[side]["result"]["footer"]["result_line"] for side in sides},
        "ran": {side: sides[side]["result"]["footer"]["ran"] for side in sides},
        "by_outcome": {side: {k: v for k, v in sides[side]["result"]["counts"]["by_outcome"].items() if v} for side in sides},
        "fixtures": {side: [(f["id"], f["outcome"], f["reasons"]) for f in sides[side]["result"]["fixtures"]] for side in sides},
        "unchanged": {k: v for k, v in unchanged.items() if v},
        "counts": {k: len(v) for k, v in lists.items()},
        "new_not_passing_by_module": {k: len(v) for k, v in sorted(new_by_module.items())},
        "new_not_passing_ids": sorted(e["id"] for e in lists["new_not_passing"]),
        "removed": brief_list(lists["removed_ids"]),
        "unchanged_not_passing": brief_list(lists["unchanged_not_passing"]),
        "different": {k: brief_list(lists[k]) for k in ("different_outcome", "different_reason", "different_subtests",
                                                       "different_skip_reason", "different_occurrences", "no_longer_failing")},
        "steps_equal": comparison["steps_equal"], "steps_different": comparison["steps_different"],
        "reports_different": comparison["reports_different"],
        "pending_external_cases_equal": comparison["pending_external_cases"]["equal"],
        "not_executed_steps_equal": comparison["not_executed_steps"]["equal"]}
    # The Director's comparator output, against this recomputation.
    director = json.load(open(os.path.join(local, "c271-p37/routine/ordinary-001.compare-main-resolved.json")))
    out["s6"]["director_comparison_agrees"] = {
        "counts": director["counts"] == out["s6"]["counts"],
        "unchanged": {k: v for k, v in director["unchanged"].items() if v} == out["s6"]["unchanged"],
        "new_not_passing_ids": sorted(e["id"] for e in director["new_not_passing"]) == out["s6"]["new_not_passing_ids"],
        "steps_equal": director["summaries"]["steps_equal"] == comparison["steps_equal"]}
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(label(out), stream, indent=1, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:5])
