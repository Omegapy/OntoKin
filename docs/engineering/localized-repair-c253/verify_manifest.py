#!/usr/bin/env python3
"""Verify frozen C253 source bindings without executing a product or scorer."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(repo, corpus_path, plan_path):
    corpus, plan = read_json(corpus_path), read_json(plan_path)
    require(corpus["schema"] == "ontokin.c253.corpus/0.1", "corpus schema")
    require(plan["schema"] == "ontokin.c253.run-plan/0.1", "run-plan schema")
    revision = corpus["revision"]
    require(re.fullmatch(r"[0-9a-f]{40}", revision), "invalid source revision")
    tree = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", revision + "^{tree}"], text=True
    ).strip()
    require(tree == corpus["tree"], "baseline tree mismatch")
    sources, bound_paths = {}, set()
    for key, row in corpus["files"].items():
        path = Path(row["path"])
        require(not path.is_absolute() and ".." not in path.parts, "unsafe source path")
        source = repo / path
        require(source.resolve().is_relative_to(repo.resolve()), "source escapes repository")
        require(source.is_file() and not source.is_symlink(), "source must be regular file")
        require(row["path"] not in bound_paths, "duplicate bound path")
        bound_paths.add(row["path"])
        raw = source.read_bytes()
        require(len(raw) == row["bytes"], f"size mismatch: {key}")
        require(hashlib.sha256(raw).hexdigest() == row["sha256"], f"hash mismatch: {key}")
        require(row["gitRevision"] == revision, f"mixed source baseline: {key}")
        committed = subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{revision}:{row['path']}"]
        )
        require(raw == committed, f"source differs from exact commit: {key}")
        sources[key] = raw

    require(len(sources) == 14, "unexpected corpus binding count")
    library_hash = hashlib.sha256(sources["hinges"]).hexdigest()
    for key in ("start_065", "target_075", "invalid_mass"):
        raw = sources[key]
        pins = re.findall(rb'digest\s+"sha256:([0-9a-f]{64})"', raw)
        require(pins == [library_hash.encode()], f"dependency pin mismatch: {key}")
        require(len(re.findall(rb"(?m)^import\s", raw)) == 1, "entry dependency count")
    require(not re.search(rb"(?m)^import\s", sources["hinges"]), "unexpected transitive import")
    closure = corpus["dependencyClosure"]
    require(closure["ambientResolutionAllowed"] is False, "ambient dependency lookup")
    require(closure["entryVariants"] == ["start_065", "target_075", "invalid_mass"], "entry variants")
    require(len(closure["modules"]) == 1, "closure module count")
    module = closure["modules"][0]
    require(module["source"] == "hinges" and module["packageId"] == "example.hinges"
            and module["version"] == "1.0.0" and module["directTransitiveImports"] == [],
            "declared dependency closure")
    for bundle_key, entry_key in (("bundle_065", "start_065"), ("bundle_075", "target_075")):
        bundle = json.loads(sources[bundle_key], object_pairs_hook=unique)
        require(bundle["entry"]["source"].encode() == sources[entry_key], "bundle entry mismatch")
        require(len(bundle["modules"]) == 1, "bundle dependency count")
        bundled = bundle["modules"][0]
        require(bundled["source"].encode() == sources["hinges"], "bundle library mismatch")
        require(bundled["package_id"] == "example.hinges" and bundled["version"] == "1.0.0",
                "bundle package identity")

    require([task["id"] for task in corpus["tasks"]] == ["V1", "V2", "N1"], "task roster")
    task_bindings = {
        "V1": ("valid_edit", "start_065", "bundle_065", "target_075", "bundle_075"),
        "V2": ("valid_edit", "target_075", "bundle_075", "start_065", "bundle_065"),
        "N1": ("invalid_edit", "start_065", "bundle_065", "invalid_mass", None),
    }
    for task in corpus["tasks"]:
        kind, start_key, bundle_key, target_key, target_bundle = task_bindings[task["id"]]
        require(task["kind"] == kind and task["family"] == "keyed-rack-c210", "task kind/family")
        require(task["startEntry"] == start_key and task["startBundle"] == bundle_key,
                "task starting source/bundle binding")
        require(task["targetPath"] == 'first.fingers["middle"].length', "task occurrence target")
        require(task.get("existingTargetEntry", task.get("existingCandidateEntry")) == target_key,
                "task target source binding")
        require(task.get("existingTargetBundle") == target_bundle, "task target bundle binding")
        patch = task["patch"]
        raw = sources[task["startEntry"]]
        start, end = patch["startByte"], patch["endByteExclusive"]
        require(type(start) is int and type(end) is int and 0 <= start < end <= len(raw), "patch bounds")
        require(patch["source"] == task["startEntry"], "patch source identity")
        require(raw[start:end].decode() == patch["expectedText"], "patch text mismatch")
        require(raw[:start].count(b"\n") + 1 == patch["lineOneBased"], "patch line mismatch")
        target_key = task.get("existingTargetEntry", task.get("existingCandidateEntry"))
        require(raw[:start] + patch["replacement"].encode() + raw[end:] == sources[target_key],
                "target differs beyond one declared literal")
        if task["kind"] == "valid_edit":
            require(patch["replacement"] == str(task["expectedLengthM"]) + "[m]", "valid units/length")
            require(task["expectedLocalBladeBaseXM"] == -task["expectedLengthM"] / 2, "base-site consequence")
        else:
            require(task["id"] == "N1" and patch["replacement"] == "0.75[kg]", "negative unit case")
            require(task["candidateAcceptanceAllowed"] is False
                    and task["acceptedStateAfter"] == "start_065", "negative accepted-state rule")

    expected = json.loads(sources["independent_original_oracle"], object_pairs_hook=unique)
    invariants, oracle = corpus["invariants"], corpus["oracle"]
    paths = [item["path"] for item in expected["objects"]]
    require(len(paths) == len(set(paths)) == len(invariants["objectPaths"]) == 18
            and set(paths) == set(invariants["objectPaths"]), "object inventory")
    selected = {'first.fingers["middle"]', 'first.fingers["middle"].blade'}
    require(len(invariants["unrelatedObjectPaths"]) == 16
            and set(invariants["unrelatedObjectPaths"]) == set(paths) - selected, "unrelated inventory")
    require(sum(path.startswith("second") for path in paths) == 11, "second assembly count")
    require(oracle["originalTolerances"] == expected["comparison"], "historical tolerances changed")
    require(oracle["timesS"] == [float(item["seconds"]) for item in expected["samples"]], "sample times changed")
    require(len(oracle["timesS"]) * len(paths) == 126, "pose coverage")
    require(corpus["population"]["assemblyFamilies"] == 1
            and corpus["population"]["confirmatoryEligibility"] is False
            and corpus["exposure"]["cleanHeldOut"] is False, "population/exposure claim")
    require(plan["population"]["assemblyFamilies"] == corpus["population"]["assemblyFamilies"]
            and plan["population"]["cases"] == ["V1", "V2", "N1"]
            and plan["population"]["validCases"] == ["V1", "V2"]
            and plan["population"]["invalidCases"] == ["N1"]
            and plan["population"]["publicPreviouslyExposed"] is True
            and plan["population"]["advantageClaimEligible"] is False, "plan population/exposure mismatch")
    require(plan["executionAdmission"]["allowedInC253"] is False, "C253 execution must remain blocked")
    require(plan["routeRoster"]["qualifiedRoutes"] == [], "unqualified routes promoted")
    design = plan["design"]
    require(design["repetitionsPerCasePerRoute"] == 6 and design["intendedAttemptsForTwoRoutes"] == 36,
            "frozen repetition/denominator mismatch")
    require(design["validAttemptsForTwoRoutes"] == 24 and design["invalidAttemptsForTwoRoutes"] == 12,
            "valid/invalid denominators mixed")
    require(len(design["routeOrderByRepetition"]) == len(design["taskOrderByRepetition"]) == 6, "order length")
    require(all(sorted(order) == ["N1", "V1", "V2"] for order in design["taskOrderByRepetition"]), "task order")
    require(all(sorted(order) == ["blender_python", "ontokin"] for order in design["routeOrderByRepetition"]), "route order")
    require(sum(order[0] == "ontokin" for order in design["routeOrderByRepetition"]) == 3, "order balance")
    require(design["pairKey"] == ["caseId", "repetition"]
            and design["attemptId"] == ["protocolVersion", "routeId", "caseId", "repetition"],
            "pair/attempt identity")
    for key in ("wallSecondsPerAttempt", "inputPlusOutputTokensPerAttempt", "outputTokensPerAttempt",
                "toolCallsPerAttempt", "candidateSubmissionsPerAttempt", "toolWallSecondsPerCall",
                "ontokinOperationsPerInvocation", "ontokinTimeMsPerInvocation"):
        value = plan["budgets"][key]
        require(type(value) is int and value > 0, f"nonpositive/noninteger budget: {key}")
    require(plan["budgets"]["outputTokensPerAttempt"] <= plan["budgets"]["inputPlusOutputTokensPerAttempt"],
            "output budget exceeds total")
    require(plan["budgets"]["humanCorrections"] == 0 and plan["budgets"]["networkInTrial"] is False,
            "intervention/network allowance")
    require(plan["model"]["singleModelForAllRoutes"] is True
            and plan["model"]["freshContextPerAttempt"] is True, "model matching/context policy")
    require(all(value == 0 for key, value in plan["preservedLimits"].items() if key.endswith("InC253")), "executed workload claim")
    return {"schema": "ontokin.c253.static-manifest-result/0.1", "passed": True,
            "baselineCommit": revision, "baselineTree": tree, "boundFiles": len(sources),
            "tasks": 3, "assemblyFamilies": 1, "objects": 18, "unchangedObjects": 16,
            "plannedPoseObservations": 126, "executionAllowed": False,
            "productStarts": 0, "nativeStarts": 0, "modelTrials": 0}


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=here.parents[2])
    parser.add_argument("--corpus", type=Path, default=here / "corpus.json")
    parser.add_argument("--plan", type=Path, default=here / "RUN-PLAN.json")
    args = parser.parse_args()
    try:
        result = verify(args.repo, args.corpus, args.plan)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(json.dumps({"passed": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
