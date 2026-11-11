#!/usr/bin/env python3
"""Extract and audit C195 recorded evidence without native or receiver execution.

Run with --repo CURRENT_CHECKOUT --out NEW_DIRECTORY outside that checkout.
The files-only evidence/recorded-evidence.tar.xz is pinned by
RECORDED-EVIDENCE.json (bytes, sha256, files and replay_map_sha256).
REPLAY-MAP.json declares rows, original_roots and receipts. Each row contains
id, route, case, source (repo-relative), and archive-relative run, artifact,
reopen, rebuilt_run, rebuilt_artifact and baseline_artifact paths. Receipt keys
are results, author_audit, acceptance, visual_review and receiving; optional
final_automated and visual_base support separately finalized author review.
Original absolute receipt paths use explicit longest-prefix archive mappings.
No receipt is rewritten and no native command is executed by this program.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile

sys.dont_write_bytecode = True
REL = Path("docs/engineering/ownership-recovery-c195")
KEYS = ("canonical-input.json", "native-transforms.json", "raw.glb", "final.glb")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def relative_path(value, allow_root=False):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid relative path: " + repr(value))
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value:
        raise ValueError("Noncanonical relative path: " + value)
    if str(path) == "." and not allow_root:
        raise ValueError("A file path cannot name the extraction root")
    return path


def child(root, name, allow_root=False):
    relative = relative_path(name, allow_root)
    path = root.joinpath(*relative.parts).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Path escapes its declared root: " + name)
    return path


def inventory(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symbolic link in sealed evidence: " + str(path))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = {"bytes": path.stat().st_size, "sha256": digest(path)}
    return result


def inventory_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def import_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Audit:
    def __init__(self):
        self.checks = []

    def check(self, condition, name, **details):
        self.checks.append({"name": name, "passed": bool(condition), **details})
        if not condition:
            raise ValueError(name)

    def identity(self, path, expected, name):
        self.check(path.is_file() and path.stat().st_size == expected["bytes"] and
                   digest(path) == expected["sha256"], name, path=str(path))


def extract(here, out, audit):
    descriptor_path = here / "evidence/RECORDED-EVIDENCE.json"
    descriptor = read(descriptor_path)
    archive_path = here / "evidence/recorded-evidence.tar.xz"
    map_path = here / "evidence/REPLAY-MAP.json"
    audit.identity(archive_path, descriptor, "Recorded archive identity matches descriptor")
    audit.check(digest(map_path) == descriptor["replay_map_sha256"], "Replay mapping identity matches descriptor")
    expected = {}
    for row in descriptor["files"]:
        name = str(relative_path(row["path"]))
        audit.check(name not in expected, "Archive manifest has unique file names", path=name)
        audit.check(type(row["bytes"]) is int and row["bytes"] >= 0, "Archive size is valid", path=name)
        expected[name] = row
    for name in expected:
        audit.check(not any(str(parent) in expected for parent in PurePosixPath(name).parents),
                    "No archive file is another file's ancestor", path=name)
    destination = out / "evidence"
    destination.mkdir(exist_ok=False)
    seen = set()
    with tarfile.open(archive_path, "r:xz") as archive:
        for member in archive:
            name = str(relative_path(member.name))
            audit.check(member.isfile() and not member.issparse(), "Archive contains only ordinary files", path=name)
            audit.check(name in expected and name not in seen, "Archive member is declared and unique", path=name)
            seen.add(name)
            declared = expected[name]
            audit.check(member.size == declared["bytes"], "Archive member size matches", path=name)
            target = child(destination, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("Unreadable archive member: " + name)
            sha = hashlib.sha256()
            copied = 0
            with stream, target.open("xb") as sink:
                while block := stream.read(1024 * 1024):
                    copied += len(block)
                    if copied > declared["bytes"]:
                        raise ValueError("Archive member exceeded declared bytes: " + name)
                    sha.update(block)
                    sink.write(block)
            audit.check(copied == declared["bytes"] and sha.hexdigest() == declared["sha256"],
                        "Extracted archive bytes match", path=name)
    audit.check(seen == set(expected), "Exact declared archive inventory extracted")
    return destination, read(map_path), {
        "archive_sha256": digest(archive_path), "descriptor_sha256": digest(descriptor_path),
        "replay_map_sha256": digest(map_path), "files": len(seen),
        "uncompressed_bytes": sum(x["bytes"] for x in expected.values())}


def relocation(base, rows):
    mappings = []
    for row in rows:
        original = PurePosixPath(row["original"])
        if not original.is_absolute() or ".." in original.parts or str(original) != row["original"]:
            raise ValueError("Invalid original provenance prefix")
        target = child(base, row["archive_relative"], allow_root=True)
        if any(original == previous for previous, _ in mappings):
            raise ValueError("Duplicate provenance prefix")
        mappings.append((original, target))
    mappings.sort(key=lambda item: len(item[0].parts), reverse=True)

    def relocated(value):
        path = PurePosixPath(value)
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("Expected an original absolute provenance path: " + str(value))
        for original, target in mappings:
            if path.is_relative_to(original):
                suffix = path.relative_to(original)
                return child(target, str(suffix), allow_root=True)
        raise ValueError("No declared provenance mapping: " + str(value))
    return relocated


def check_author_audit(audit, receipt, rows, result, source_root, base, relocated, here):
    audit.check(receipt["schema"] == "ontokin.c195.author-evidence-audit/0.1" and receipt["passed"] is True,
                "Independent author audit passed")
    audit.check(receipt["input_manifest_sha256"] == digest(here / "INPUTS.json") and
                receipt["freeze_sha256"] == digest(here / "FREEZE.json") and
                receipt["delivery_manifest_sha256"] == result["manifest_sha256"],
                "Author audit binds current frozen inputs and delivered manifest")
    audit.check(set(receipt["authors"]) == {"ok", "python"}, "Both authors independently reviewed")
    for route in ("ok", "python"):
        author = receipt["authors"][route]
        for key in ("passed", "rejection_observed", "diagnostic_accurate",
                    "baseline_preserved_after_rejection", "baseline_preserved_at_submission"):
            audit.check(author[key] is True, "Recorded author gate passed", route=route, gate=key)
        audit.check(author["negative_native_substeps"] == 0 and author["negative_native_outputs"] is False,
                    "Malformed candidate had no native charge/output", route=route)
        seconds = author["wall_seconds"]
        audit.check(type(seconds) in (int, float) and math.isfinite(seconds) and 0 <= seconds <= 1200,
                    "Author stayed inside wall allowance", route=route)
        audit.check(type(author["formal_submissions"]) is int and 1 <= author["formal_submissions"] <= 3 and
                    type(author["repaired_native_builds"]) is int and author["repaired_native_builds"] == 1 and
                    type(author["baseline_native_builds"]) is int and author["baseline_native_builds"] == 1,
                    "Recorded author construction/submission counts meet caps", route=route)
        audit.check(bool(author["evidence"]), "Raw author evidence references exist", route=route)
        for evidence in author["evidence"]:
            audit.identity(relocated(evidence["path"]), evidence, "Author review raw evidence identity")
        for row in (r for r in rows if r["route"] == route):
            declared = author["submissions"][row["case"]]
            audit.check(declared["source_sha256"] == digest(child(source_root, row["source"])) and
                        declared["run_inventory_sha256"] == inventory_sha256(inventory(child(base, row["run"]))),
                        "Author review binds actual source and run", id=row["id"])


def check_receiving(audit, directory, rows, artifact_paths, result, relocated):
    summary = read(directory / "summary.json")
    audit.check(result["receiving"]["passed"] and
                result["receiving"]["summary_sha256"] == digest(directory / "summary.json"),
                "Validation binds receiving summary")
    audit.check(summary["pass_for_executed_receiving_checks"] and summary["glb_paths"] == 8 and
                summary["three_poses"] == 24 and summary["blender_import_jobs"] == 4 and
                summary["khronos_errors"] == summary["khronos_warnings"] == 0,
                "Receiving counts and executed gates pass")
    identities = read(directory / "artifact-identities.json")
    audit.check(set(artifact_paths) == {r["id"] for r in rows},
                "Receiving artifact map covers exactly the validated deliveries")
    expected_sources = {f'deliveries/{r["id"]}/{name}': (artifact_paths[r["id"]] / name).resolve()
                        for r in rows for name in ("raw.glb", "final.glb")}
    expected_paths = set(expected_sources)
    audit.check({r["path"] for r in identities} == expected_paths and len(identities) == 8,
                "Receiving identities cover all actual outputs exactly once")
    for identity in identities:
        path = child(directory, identity["path"])
        expected_source = expected_sources[identity["path"]]
        audit.check(relocated(identity["source"]) == expected_source,
                    "Receiver source matches the validated delivery label and file", path=identity["path"])
        audit.check(digest(path) == identity["sha256"] == digest(expected_source),
                    "Receiver copied the exact labeled submitted artifact", path=identity["path"])
    khronos = read(directory / "khronos.json")
    audit.check(set(khronos) == expected_paths, "Khronos covers all raw/final output paths")
    for name, entry in khronos.items():
        audit.check(entry["sha256"] == digest(child(directory, name)) and
                    entry["report"]["issues"]["numErrors"] == entry["report"]["issues"]["numWarnings"] == 0,
                    "Khronos receipt binds passing actual bytes", path=name)
    audit.check(sum(x["report"]["issues"]["numInfos"] for x in khronos.values()) == summary["khronos_infos"],
                "Khronos informational findings remain separately accounted")
    for kind in ("khronos", "three", "blender"):
        command = read(directory / "commands" / (kind + ".json"))
        audit.check(command["completed"] and command["returncode"] == 0 and command["pass"],
                    "Recorded receiving command completed", kind=kind)
    three = read(directory / "three.json")
    audit.check(three["pass"] and three["threeRevision"] == "186" and len(three["reports"]) == 8 and
                {r["path"] for r in three["reports"]} == expected_paths,
                "Pinned Three.js covered every raw/final artifact")
    for report in three["reports"]:
        audit.check(report["sha256"] == digest(child(directory, report["path"])) and len(report["poses"]) == 3,
                    "Three.js binds actual bytes and three poses", path=report["path"])
    images = set()
    receipts = list((directory / "renders").glob("*/receipt.json"))
    audit.check(len(receipts) == 4, "Four original Blender import receipts retained")
    labels = set()
    for path in receipts:
        receipt = read(path)
        label = receipt["label"]
        audit.check(label in artifact_paths and label not in labels, "Unique imported delivery identity", label=label)
        labels.add(label)
        audit.check(receipt["input_sha256"] == digest(relocated(receipt["input_glb"])) ==
                    digest(artifact_paths[label] / "final.glb") and receipt["all_sampled_imports_match_glb"] and
                    receipt["mesh_count"] == 7 and len(receipt["frames"]) == 3,
                    "Blender import receipt binds actual final GLB and three poses", id=label)
        for frame in receipt["frames"]:
            png = child(path.parent, frame["png"])
            audit.identity(png, {"bytes": frame["png_bytes"], "sha256": frame["png_sha256"]},
                           "Original imported render image identity")
            images.add(png)
    audit.check(len(images) == 12, "Twelve original import panels retained")
    return images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    if out.is_relative_to(repo) or repo.is_relative_to(out):
        raise ValueError("Replay output must be outside and not contain the source checkout")
    out.mkdir(parents=True, exist_ok=False)
    audit = Audit()
    record = {"schema": "ontokin.c195.portable-recorded-replay/0.1", "passed": False,
              "started_utc": datetime.now(timezone.utc).isoformat(), "source_root": str(repo),
              "new_native_builds": 0, "new_native_replays": 0, "new_authors": 0,
              "new_receiving_executions": 0, "network_used": False}
    try:
        here = repo / REL
        base, mapping, extraction = extract(here, out, audit)
        record["extraction"] = extraction
        relocated = relocation(base, mapping["original_roots"])
        rows = mapping["rows"]
        audit.check(len(rows) == 4 and len({r["id"] for r in rows}) == 4 and
                    all(re.fullmatch(r"[a-zA-Z0-9_-]+", r["id"]) for r in rows) and
                    {(r["case"], r["route"]) for r in rows} ==
                    {(case, route) for case in ("G", "H") for route in ("ok", "python")},
                    "Exactly four repaired/preserved author variants mapped")
        verifier = import_path("c195_recorded_delivery_tools", here / "verify_deliveries.py")
        record["frozen_inputs"] = verifier.public_inputs(repo)
        common = verifier.c
        audit.check(common.verify_freeze()["passed"], "Unchanged C194 preparation freeze passes")
        reader = common.artifact_reader()
        audit.check(reader.verify_frozen()["passed"], "Unchanged inherited C193 artifact reader freeze passes")
        sys.modules["check_artifact"] = reader
        provenance = import_path("c195_recorded_provenance", common.C193 / "independent/audit_provenance.py")
        receipts = mapping["receipts"]
        result_path = child(base, receipts["results"])
        result = read(result_path)
        audit.check(result["schema"] == "ontokin.c195.author-delivery-validation/0.1" and
                    result["numerical_receiving_gates_passed"] is True,
                    "Original numerical and receiving validation passed")
        audit.check(result["public_inputs"]["manifest_sha256"] == digest(here / "INPUTS.json") and
                    result["public_inputs"]["freeze_sha256"] == digest(here / "FREEZE.json") and
                    result["orchestrator_sha256"] == digest(here / "verify_deliveries.py"),
                    "Original validation binds frozen inputs and actual verifier")
        audit.check(len(result["runs"]) == 4 and {r["id"] for r in result["runs"]} == {r["id"] for r in rows},
                    "Validation result covers mapped deliveries exactly")
        baselines = read(here / "BASELINES.json")
        all_artifacts, artifacts_by_id, reopens, reports = [], {}, [], []
        for row in rows:
            identifier, route, case = row["id"], row["route"], row["case"]
            source = child(repo, row["source"])
            run, artifact, reopened, rebuild_run, rebuilt, baseline = (
                child(base, row[key]) for key in ("run", "artifact", "reopen", "rebuilt_run", "rebuilt_artifact", "baseline_artifact"))
            declared = next(r for r in result["runs"] if r["id"] == identifier)
            audit.check(declared["route"] == route and declared["case"] == case and declared["passed"] and
                        not declared["failures"], "Actual delivered run passed", id=identifier)
            audit.check(relocated(declared["artifact"]) == artifact and relocated(declared["submitted_run"]) == run,
                        "Replay map matches original artifact/run provenance", id=identifier)
            audit.check(declared["source_sha256"] == digest(source) and
                        declared["run_inventory_sha256"] == inventory_sha256(inventory(run)),
                        "Source and original submitted run inventory preserved", id=identifier)
            verifier.source_and_baseline({"route": route, "case": case, "source": str(source),
                                          "preserve_from": str(baseline)})
            audit.check(inventory(baseline) == baselines["routes"][route]["artifact_files"],
                        "Original accepted 375 mm artifact closure preserved", id=identifier)
            extension = "ok" if route == "ok" else "py"
            for stage, path, build_dir in (("submitted", artifact, run), ("rebuilt", rebuilt, rebuild_run)):
                delivery = read(build_dir / "delivery.json")
                audit.check(delivery["successful"] and delivery["source_unchanged_during_build"] and
                            delivery["source_sha256"] == digest(source) and delivery["returncode"] == 0,
                            "Recorded build used actual unchanged source and succeeded", id=identifier, stage=stage)
                audit.check(digest(relocated(delivery["source"])) == digest(source),
                            "Recorded source path maps to identical retained source", id=identifier, stage=stage)
                if delivery.get("artifact_directory"):
                    audit.check(relocated(delivery["artifact_directory"]) == path,
                                "Recorded build artifact directory matches mapping", id=identifier, stage=stage)
                cost = delivery["cost"]
                audit.check(cost["requested_operations"] == cost["host_operations_ceiling"] == 1000000 and
                            cost["requested_elapsed_ms"] == cost["host_elapsed_ms_ceiling"] == 80000,
                            "Original construction budgets unchanged", id=identifier, stage=stage)
                audit.check((path / ("source." + extension)).read_bytes() == source.read_bytes() and
                            read(path / "canonical-input.json") == read(common.HERE / ("frozen/" + case + "-canonical.json")),
                            "Retained source and canonical target agree", id=identifier, stage=stage)
                if route == "ok":
                    state_path = path.parent.parent / "state.json"
                    state = read(state_path)
                    audit.check(state["schema"] == "ontokin.c193.store/0.1" and
                                child(state_path.parent, state["artifact_directory"]) == path and
                                state["manifest_sha256"] == digest(path / "manifest.json"),
                                "Retained accepted store points to submitted artifact", id=identifier, stage=stage)
                provenance_result = provenance.audit(path, common.CONTRACT,
                                                      common.C193 / "independent/evidence/candidate-review.json")
                audit.check(provenance_result["passed"], "Fresh recorded provenance audit passed", id=identifier, stage=stage)
                write(out / "reports" / (identifier + "-" + stage + "-provenance.json"), provenance_result)
                numerical = reader.review(path, case, common.CONTRACT / "backend.json", common.BACKEND_SHA, common.SOURCE_BINDING)
                audit.check(numerical["passed"] and not numerical["failures"], "Fresh recorded artifact audit passed", id=identifier, stage=stage)
                write(out / "reports" / (identifier + "-" + stage + ".json"), numerical)
                bound = numerical["mapping_measurements"]["maximumContinuousRawToFinalVertexDeviationBoundMm"]
                audit.check(bound <= 0.2, "Unchanged continuous mapping gate passed", id=identifier, stage=stage)
                reports.append({"id": identifier, "stage": stage, "case": case, "continuous_bound_mm": bound})
                all_artifacts.append((case, path))
            for name in KEYS:
                audit.check(digest(artifact / name) == declared["artifacts"][name] == digest(rebuilt / name),
                            "Actual source output and coordinator rebuild exactly agree", id=identifier, file=name)
                if case == "H":
                    audit.check(digest(artifact / name) == digest(baseline / name),
                                "Preserved 375 mm result regenerates exactly", id=identifier, file=name)
            native, again = read(artifact / "native-transforms.json"), read(reopened / "native-transforms.json")
            summary = read(reopened / "summary.json")
            audit.check(len(native) == len(again) == 481 and native == again,
                        "Recorded reopened scene reproduces all 481 samples", id=identifier)
            audit.check(summary["pass"] and summary["samples"] == 481 and summary["cache_clear_completed"] and
                        summary["configuration_unchanged"] and not summary["reconstructed_or_repaired"],
                        "Recorded scene replay reset cache without reconstruction", id=identifier)
            audit.check(summary["opened_scene_sha256"] == digest(artifact / "scene.blend") and
                        summary["source_sha256"] == digest(source) and
                        summary["canonical_input_sha256"] == digest(artifact / "canonical-input.json") and
                        summary["backend_sha256"] == common.BACKEND_SHA and
                        summary["inspector_sha256"] == digest(common.C193 / "independent/inspect_scene.py"),
                        "Reopened scene receipt binds exact source, scene, backend and inspector", id=identifier)
            audit.check(declared["reopen"]["summary_sha256"] == digest(reopened / "summary.json") and
                        declared["reopen"]["configuration_sha256"] == digest(reopened / "configuration-before.json") and
                        declared["reopen"]["original_trace_sha256"] == digest(artifact / "native-transforms.json") and
                        declared["reopen"]["reopened_trace_sha256"] == digest(reopened / "native-transforms.json"),
                        "Validation binds exact retained replay receipts", id=identifier)
            reopens.append({"id": identifier, "samples": 481, "exact": True})
            artifacts_by_id[identifier] = artifact
        for case in ("G", "H"):
            peers = [path for tag, path in all_artifacts if tag == case]
            for name in KEYS:
                audit.check(len(peers) == 4 and len({digest(path / name) for path in peers}) == 1,
                            "Both routes and coordinator rebuilds agree exactly", case=case, file=name)
        author_audit_path = child(base, receipts["author_audit"])
        author_review = read(author_audit_path)
        check_author_audit(audit, author_review, rows, result, repo, base, relocated, here)
        if receipts.get("final_automated"):
            final_path = child(base, receipts["final_automated"])
            final = read(final_path)
            audit.check(final["automated_gates_passed"] and final["validation_sha256"] == digest(result_path) and
                        final["author_audit"]["sha256"] == digest(author_audit_path),
                        "Separate author finalization binds original numeric result and audit")
        else:
            audit.check(result["automated_gates_passed"] and result["author_audit"]["passed"] and
                        result["author_audit"]["sha256"] == digest(author_audit_path),
                        "Original automated result binds passing author audit")
        receiving = child(base, receipts["receiving"])
        images = check_receiving(audit, receiving, rows, artifacts_by_id, result, relocated)
        visual_path = child(base, receipts["visual_review"])
        visual = read(visual_path)
        visual_base = child(base, receipts.get("visual_base", receipts["receiving"]), allow_root=True)
        audit.check(visual["pass"] and len(visual["panels"]) == 12, "Recorded visual review passes for twelve panels")
        reviewed = set()
        for panel in visual["panels"]:
            path = child(visual_base, panel["path"])
            audit.check(path not in reviewed, "Visual panel has unique identity", path=panel["path"])
            reviewed.add(path)
            audit.identity(path, panel, "Visual receipt binds exact original PNG")
        audit.check(reviewed == images, "Visual review covers every original receiver panel exactly")
        acceptance_path = child(base, receipts["acceptance"])
        acceptance = read(acceptance_path)
        audit.check(acceptance["accepted"] is True and acceptance["results_sha256"] == digest(result_path) and
                    acceptance["author_audit_sha256"] == digest(author_audit_path) and
                    acceptance["visual_review_sha256"] == digest(visual_path),
                    "Final acceptance binds numerical, author and visual evidence")
        if receipts.get("final_automated"):
            audit.check(acceptance["final_automated_sha256"] == digest(final_path), "Acceptance binds separate automated finalization")
        record.update(passed=True, evidence_root=str(base), recorded_artifacts=reports,
                      scene_replay_receipts=reopens, visual_panels=12,
                      author_audit_sha256=digest(author_audit_path), results_sha256=digest(result_path),
                      acceptance_sha256=digest(acceptance_path),
                      scope="Recorded numerical/provenance checks and retained scene/receiver/visual/author receipts only",
                      limits=["No native construction, resimulation, author dispatch or receiving execution",
                              "Visual observations are retained receipts; this program does not view images",
                              "Inherited FAILED legacy regression and broader project gates remain open"])
    except Exception as error:
        record["failure"] = type(error).__name__ + ": " + str(error)
    record.update(finished_utc=datetime.now(timezone.utc).isoformat(), checks_passed=sum(x["passed"] for x in audit.checks),
                  all_checks=audit.checks)
    write(out / "REPLAY-RESULT.json", record)
    print(json.dumps({"passed": record["passed"], "checks": record["checks_passed"],
                      "recorded_artifacts": len(record.get("recorded_artifacts", [])),
                      "scene_replay_receipts": len(record.get("scene_replay_receipts", [])),
                      "failure": record.get("failure")}), flush=True)
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
