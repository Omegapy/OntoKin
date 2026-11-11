"""Read-only C200 authority and preserved-failure checks; no native launch."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from prototypes.static_tray_v01.lock import ALL_LIMITS, check_file, file_binding, read_json
from prototypes.static_tray_v01.supervisor import Stop, sha256_file

REVISION = "OK-QUAL-STATIC-TRAY-C200/0.1.0"
DIRECTORY = "docs/engineering/static-tray-exporter-c200"
BASELINE = "e8df6496033b13ac7e387c9525fc83c5fada1453"
OLD_DIRECTORY = "docs/engineering/static-tray-qualification-c199"
REQUIRED_PROTOCOL = {"ADOPTION.md", "QUALIFICATION.md", "QUALIFICATION.json",
                     "EXPORTER-COMPATIBILITY.md", "qualification_gate.py", "run_qualification.py",
                     "prepare_inputs.py", "inventory_host.py", "run_cpu_controls.py", "test_protocol.py"}
EXPECTED_ALLOWANCE = {"coordinator_invocations": 1, "native_construction_starts": 12,
                      "receiving_starts": 12, "read_only_checker_starts": 12,
                      "delivered_controls": 9, "automatic_retries": 0,
                      "extra_lifecycle_starts": 0, "timed_authors": 0,
                      "stop_first_unexpected": True}


def require(condition, reason):
    if not condition:
        raise Stop("OTRAY-E-BINDING", reason)


def verify_definition(root, *, check=lambda: None):
    root = Path(root).resolve()
    definition = read_json(root / DIRECTORY / "QUALIFICATION.json")
    require(definition.get("schema") == "ontokin.c200.qualification-revision/0.1"
            and definition.get("revision_id") == REVISION, "Wrong C200 qualification revision")
    require(definition.get("recovery_baseline_commit") == BASELINE,
            "Recovery baseline must be the observed C199 closing main")
    require(definition.get("allowance") == EXPECTED_ALLOWANCE, "C200 start allowance changed")
    require(definition.get("limits") == ALL_LIMITS, "C200 retains every source/transaction limit")
    old = definition["preserved_c199"]
    require(old.get("native_construction_starts") == 1 and old.get("receiving_starts") == 0
            and old.get("accepted_transactions") == 0 and old.get("read_only_checker_starts") == 0
            and old.get("resume_permitted") is False, "Consumed C199 outcome changed")
    for relative, binding in definition["preserved_files"].items():
        require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
                "Preserved evidence path is not repository-relative")
        check_file(root / relative, binding, check)
    old_lock = read_json(root / OLD_DIRECTORY / "EXECUTABLE-INPUTS.json", 8 * 1024 * 1024)
    require(sha256_file(root / OLD_DIRECTORY / "EXECUTABLE-INPUTS.json") == old["input_lock_sha256"],
            "C199 failed input lock changed")
    historical = read_json(root / OLD_DIRECTORY / "evidence/native-execution/receipts/qualification-result.json")
    require(historical.get("native_starts") == 1 and historical.get("receiving_starts") == 0
            and historical.get("qualified") is False
            and historical.get("status") == "STOPPED_AFTER_FIRST_UNEXPECTED_RESULT"
            and historical.get("stopped_at") == {"kind": "transaction", "slot": "N01"},
            "C199 stopped result no longer matches the preserved failed cohort")
    rows = [json.loads(line) for line in (root / OLD_DIRECTORY /
            "evidence/native-execution/receipts/attempts.jsonl").read_text().splitlines() if line]
    require([row["state"] for row in rows] == ["RESERVED", "STARTED", "REJECTED"]
            and all(row["slot"] == "N01" for row in rows)
            and sum(row["state"] == "STARTED" for row in rows) == 1,
            "C199 consumed ledger is not the one preserved failed construction")
    controls = read_json(root / "docs/engineering/static-tray-mapping-c198/CONTROLS.json")
    require(definition["slots"] == controls["future_qualification_native_slots"],
            "The new cohort must use unchanged C198 cases/order/limits")
    return definition, old_lock


def verify_baseline_source(root, old_lock):
    """Match the original locked source to its retained equal published tree."""
    root = Path(root).resolve()
    import hashlib
    for relative, binding in old_lock["repository_files"].items():
        data = subprocess.check_output(["git", "-C", str(root), "cat-file", "blob", BASELINE + ":" + relative])
        require(len(data) == binding["size_bytes"] and hashlib.sha256(data).hexdigest() == binding["sha256"],
                "Published recovery tree does not preserve C199's locked source: " + relative)
    return len(old_lock["repository_files"])


def revision_binding(root, lock_path, schedule, definition):
    root, lock_path, schedule = Path(root).resolve(), Path(lock_path).resolve(), Path(schedule).resolve()
    coordinator = root / DIRECTORY / "run_qualification.py"
    return {"revision_id": REVISION,
            "definition": {"path": str(root / DIRECTORY / "QUALIFICATION.json"),
                           **file_binding(root / DIRECTORY / "QUALIFICATION.json")},
            "coordinator": {"path": str(coordinator), **file_binding(coordinator)},
            "preserved_c199_input_lock_sha256": definition["preserved_c199"]["input_lock_sha256"],
            "allowance": EXPECTED_ALLOWANCE,
            "cumulative_native_construction_ceiling": 13,
            "cumulative_receiving_ceiling": 12,
            "schedule_root": str(schedule),
            "invocation_receipt": str(schedule.parent / (schedule.name + "-C200-INVOCATION.json")),
            "result_receipt": str(schedule.parent / (schedule.name + "-C200-RESULT.json"))}


def verify_revision(lock, lock_path, *, approval, fresh, check=lambda: None):
    root = Path(lock["repo_root"]).resolve()
    definition, old_lock = verify_definition(root, check=check)
    schedule = Path(lock["schedule_root"]).resolve()
    require(str(schedule) != old_lock["schedule_root"], "C199's stopped schedule cannot be reused")
    expected = revision_binding(root, lock_path, schedule, definition)
    require(lock.get("qualification_revision") == expected, "C200 authority/command provenance changed")
    required = {DIRECTORY + "/" + name for name in REQUIRED_PROTOCOL}
    required |= set(definition["preserved_files"])
    require(required <= set(lock["repository_files"]), "C200 protocol or preserved failure is not input-bound")
    for relative in required:
        check_file(root / relative, lock["repository_files"][relative], check)
    command = [lock["host"]["python"], "-IBS", str(root / DIRECTORY / "run_qualification.py"),
               "--lock", str(Path(lock_path).resolve())]
    require(lock.get("coordinator_command") == command, "C200 coordinator command changed")
    require(lock.get("coordinator_environment") == lock["host_environment"], "C200 coordinator environment changed")
    require(lock["implementation"] != old_lock["implementation"], "Unchanged C199 implementation is not the repair")
    if fresh:
        require(not schedule.exists(), "An existing C200 schedule cannot be resumed or reset")
        require(not Path(expected["invocation_receipt"]).exists(), "C200 coordinator already invoked; reconcile without retry")
        require(not Path(expected["result_receipt"]).exists(), "C200 result already exists")
    if approval:
        approved = read_json(Path(lock_path).with_suffix(".approval.json"))
        require(approved.get("qualification_revision_id") == REVISION
                and approved.get("qualification_revision_sha256") == expected["definition"]["sha256"],
                "Independent approval does not authorize this C200 revision")
        require(approved.get("preserved_c199_input_lock_sha256") == expected["preserved_c199_input_lock_sha256"]
                and approved.get("authorization_scope") == EXPECTED_ALLOWANCE,
                "Independent approval omits the consumed old cohort or changes the new allowance")
    return definition
