#!/usr/bin/env python3
"""Sequential actual-byte reference/native/browser roles for a supplied corpus.

Source artifacts come from build_reach_source_artifacts.py. Agent artifacts
come from the separately executed Agent workflow and its actual retrieval
records. This runner never exports replacement artifacts or claims that the
Agent transport, visual review, or complete release has been independently
audited. It preserves failed stages and uses fresh output directories.
"""
import argparse
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.reach_delivery_inventory import (ROOT, SOURCE_CASES, AGENT_CASES, SOURCE_BROWSER, AGENT_BROWSER,
    checked_member, check_settings, decode, descriptor, endpoint, finish_inputs, fresh_output,
    frozen_cases, read_bounded, require, selected_cases, snapshot, source_files, utc, write_json)


def source_kind(producer):
    schema = producer.get("schema_version")
    if schema == "ontokin.reach-source-delivery/0.1":
        return "source_component"
    require(schema == "ontokin.reach-agent-delivery-workflow/0.1", "Unsupported actual artifact producer record")
    return "agent_retrieved_artifact"


def producer_rows(producer, kind, selected, directory):
    deliveries = producer.get("deliveries")
    require(type(deliveries) is list and 0 < len(deliveries) <= 256, "A bounded actual delivery inventory is required")
    by_id = {}
    for row in deliveries:
        require(type(row) is dict and type(row.get("case_id")) is str and row["case_id"] not in by_id,
                "Producer case IDs must be unique")
        by_id[row["case_id"]] = row
    frozen = frozen_cases()
    result = []
    for case_id in selected:
        require(case_id in by_id, "Missing required actual delivery: " + case_id)
        item = by_id[case_id]
        require(item.get("status") in (None, "passed") and type(item.get("artifact")) is dict,
                "The selected delivery did not succeed: " + case_id)
        require(item.get("source_files") == source_files(case_id), "Delivery source file manifest differs from the fixed case")
        require(item.get("program_revision") == frozen[case_id]["program_revision"],
                "Actual delivered program revision differs from the frozen case")
        options = check_settings(case_id, item.get("options"))
        artifact = checked_member(directory, item["artifact"])
        if kind == "agent_retrieved_artifact":
            for key in ("project_id", "run_id", "artifact_id"):
                require(type(item.get(key)) is str and 0 < len(item[key]) <= 256,
                        "Actual Agent identity is missing: " + key)
        result.append((item, options, artifact))
    return result


def run_stage(output, name, command, *, timeout=960):
    started = time.monotonic()
    record = {"stage": name, "command": list(map(str, command)), "working_directory": str(ROOT),
              "started_at": utc(), "provider": "local", "timeout_seconds": timeout}
    with (output / (name + ".log")).open("xb") as stream:
        try:
            result = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=timeout)
            record["returncode"] = result.returncode
        except Exception as error:
            record.update(returncode=-1, failure={"type": type(error).__name__, "message": str(error)})
    record.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started,
                  log=descriptor(output / (name + ".log"), relative_to=output))
    write_json(output / (name + ".json"), record)
    print(f"{name}: exit {record['returncode']}", flush=True)
    return record


def run(producer_path, output, requested, node, browser):
    output = fresh_output(output)
    (output / "stages").mkdir()
    (output / "plans").mkdir()
    (output / "cases").mkdir()
    report = {"schema_version": "ontokin.reach-destination-run/0.1", "status": "running",
              "provider": "local", "started_at": utc(), "release_acceptance": False,
              "full_product_goal_completed": False, "agent_transport_audited": False,
              "visual_review": "pending_actual_image_inspection", "browser_requested": browser,
              "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
              "working_directory": str(ROOT), "execution": {"python": sys.version,
                  "executable": sys.executable, "platform": platform.platform(), "node_executable": node},
              "cases": [], "stages": [], "complete_native_corpus": False,
              "complete_browser_corpus": False, "complete_destination_corpus": False}
    before = None
    try:
        before = snapshot()
        write_json(output / "inputs-before.json", before)
        producer_path = Path(producer_path).absolute()
        producer_raw = read_bounded(producer_path)
        producer = decode(producer_raw)
        kind = source_kind(producer)
        selected = selected_cases(kind, requested)
        report.update(source_kind=kind, selected_cases=list(selected),
                      required_cases=list(SOURCE_CASES if kind == "source_component" else AGENT_CASES),
                      producer=descriptor(producer_path), producer_source_commit=producer.get("source_commit"),
                      producer_source_tree=producer.get("source_tree"), source_git=before["git"])
        # A different producer cut needs a separate eligible-input equivalence
        # audit. This execution runner intentionally takes one exact clean cut.
        require(producer.get("source_commit") == before["git"]["commit"] and
                producer.get("source_tree") == before["git"]["tree"],
                "Producer and destination source cuts differ; require an explicit input-equivalence audit")
        rows = producer_rows(producer, kind, selected, producer_path.parent)
        with (output / "producer-record.json").open("xb") as stream:
            stream.write(producer_raw)
        version = subprocess.check_output([node, "--version"], cwd=ROOT, text=True).strip()
        require(version.startswith("v22."), "Actual destination verification requires the pinned Node 22 major")
        report["execution"]["node"] = version
        prepared = []
        for item, options, artifact in rows:
            case_id = item["case_id"]
            row = {"case_id": case_id, "status": "running", "program_revision": item["program_revision"],
                   "options": options, "producer_artifact": item["artifact"], "started_at": utc()}
            if kind == "agent_retrieved_artifact":
                row["agent"] = {key: item[key] for key in ("project_id", "run_id", "artifact_id")}
            try:
                plan = output / "plans" / (case_id + ".json")
                commands = [
                    ("plan-" + case_id, [node, str(ROOT / "tools/verify_reach_native.mjs"), "--plan", str(artifact), "--output", str(plan)]),
                    ("reference-" + case_id, [sys.executable, str(ROOT / "tools/build_reach_native_reference.py"),
                        "--source-manifest", str(ROOT / source_files(case_id)), "--artifact", str(artifact),
                        "--plan", str(plan), "--case-id", case_id, "--end", endpoint(case_id),
                        "--source-kind", kind, "--output-dir", str(output / "cases" / case_id),
                        "--position-tolerance", str(options["position_tolerance_m"]),
                        "--rotation-tolerance", str(options["rotation_tolerance_rad"]),
                        "--time-tolerance", str(options["time_tolerance_s"])])]
                for name, command in commands:
                    stage = run_stage(output / "stages", name, command)
                    report["stages"].append({"path": "stages/" + name + ".json", "returncode": stage["returncode"]})
                    require(stage["returncode"] == 0, "Destination stage failed: " + name)
                case_manifest = decode(read_bounded(output / "cases" / case_id / "native-input.json"))
                require(case_manifest["source_commit"] == before["git"]["commit"] and
                        case_manifest["source_tree"] == before["git"]["tree"] and
                        case_manifest["source_kind"] == kind and len(case_manifest["cases"]) == 1,
                        "Prepared native case identity differs")
                prepared_item = case_manifest["cases"][0]
                require(prepared_item["case_id"] == case_id and
                        prepared_item["artifact"]["sha256"] == item["artifact"]["sha256"] and
                        prepared_item["artifact"]["bytes"] == item["artifact"]["bytes"],
                        "Reference preparation substituted the actual supplied artifact")
                for member in (prepared_item["artifact"], prepared_item["reference"], *prepared_item["sources"]):
                    member["path"] = f"cases/{case_id}/" + member["path"]
                    checked_member(output, member)
                prepared.append(prepared_item)
                row["status"] = "prepared"
            except Exception as error:
                row.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                           traceback=traceback.format_exc())
            row["finished_at"] = utc()
            report["cases"].append(row)
        require(len(prepared) == len(selected), "At least one required case lacks independent native expectations")
        native_manifest = {"schema_version": "ontokin.reach-native-input/0.1", "source_kind": kind,
                           "source_commit": before["git"]["commit"], "source_tree": before["git"]["tree"],
                           "cases": prepared}
        write_json(output / "native-input.json", native_manifest)
        stage = run_stage(output / "stages", "native", [node, str(ROOT / "tools/verify_reach_native.mjs"),
                          "--manifest", str(output / "native-input.json"), "--output", str(output / "native-validation.json")])
        report["stages"].append({"path": "stages/native.json", "returncode": stage["returncode"]})
        native = decode(read_bounded(output / "native-validation.json"))
        native_cases = {item["case_id"]: item for item in native["cases"]}
        for row in report["cases"]:
            result = native_cases.get(row["case_id"])
            row["status"] = "passed" if result and result["status"] == "passed" else "failed"
            row["native_status"] = result["status"] if result else "missing"
        require(stage["returncode"] == 0, "Actual native verification failed")
        require(native["status"] == "passed" and native["failed_cases"] == 0 and
                {row["case_id"] for row in native["cases"]} == set(selected), "Native report is incomplete")
        report["native_report"] = descriptor(output / "native-validation.json", relative_to=output)
        report["complete_native_corpus"] = set(selected) == set(report["required_cases"])
        if browser:
            required_browser = SOURCE_BROWSER if kind == "source_component" else AGENT_BROWSER
            browser_cases = [case_id for case_id in required_browser if case_id in selected]
            require(browser_cases, "The selected corpus has no prescribed browser case")
            command = [node, str(ROOT / "tools/verify_reach_viewer.mjs"), "--manifest", str(output / "native-input.json"),
                       "--native-report", str(output / "native-validation.json"), "--output-dir", str(output / "browser")]
            for case_id in browser_cases:
                command.extend(("--case", case_id))
            stage = run_stage(output / "stages", "browser", command)
            report["stages"].append({"path": "stages/browser.json", "returncode": stage["returncode"]})
            require(stage["returncode"] == 0, "Actual browser validation failed")
            browser_report = decode(read_bounded(output / "browser/browser-validation.json"))
            require(browser_report["status"] == "passed", "Browser report did not pass")
            report["browser_report"] = descriptor(output / "browser/browser-validation.json", relative_to=output)
            report["complete_browser_corpus"] = browser_report["complete_browser_corpus"]
        require(read_bounded(producer_path) == producer_raw, "Producer record changed during verification")
        for item, _, _ in rows:
            checked_member(producer_path.parent, item["artifact"])
        report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                      traceback=traceback.format_exc())
    finish_inputs(output, before, report)
    report["complete_destination_corpus"] = (report["status"] == "passed" and
        report["complete_native_corpus"] and report["complete_browser_corpus"])
    report["finished_at"] = utc()
    write_json(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-report", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--node", default="node")
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args(argv)
    report = run(args.producer_report, args.output_dir, args.case, args.node, args.browser)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
