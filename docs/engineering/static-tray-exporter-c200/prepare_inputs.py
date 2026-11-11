"""Seal new C200 inputs from actual committed bytes; never approve or execute."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
    raise SystemExit("Use the intended CPython interpreter with -IBS")
ROOT = Path(__file__).resolve().parents[3]
parent = ROOT / "prototypes"
parent_caches = [parent / "__init__.pyc", parent / "__init__.pyo", *(parent / "__pycache__").glob("__init__.*")]
if any(path.is_file() and path.suffix in {".pyc", ".pyo"} for path in parent_caches):
    raise SystemExit("Unbound parent bytecode prevents C200 source-only bootstrap")
for relative in ("ontokin", "prototypes/static_tray_v01", "tools/static_tray_reader_v01",
                 "docs/engineering/static-tray-exporter-c200"):
    if any(path.suffix in {".pyc", ".pyo"} for path in (ROOT / relative).rglob("*")):
        raise SystemExit("Unbound bytecode prevents C200 source-only bootstrap: " + relative)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prototypes.static_tray_v01.canonical import json_bytes
from prototypes.static_tray_v01.format_check import build_manifest
from prototypes.static_tray_v01.lock import build_lock, file_binding, read_json, verify_lock
from prototypes.static_tray_v01.supervisor import sha256_file
from qualification_gate import (DIRECTORY, OLD_DIRECTORY, REQUIRED_PROTOCOL, REVISION,
                                require, revision_binding, verify_baseline_source,
                                verify_definition, verify_revision)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "output", "schedule-root", "blender-root", "blender-archive",
                 "host-inventory", "dependencies-root", "node", "preflight-directory"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--extra-input", action="append", default=[],
                        help="Additional immutable repository-relative preparation input; must be committed")
    args = parser.parse_args()
    root, output = Path(args.repo).resolve(), Path(args.output).resolve()
    require(root == ROOT, "Run the preparation script from the execution checkout being sealed")
    schedule, preflight = Path(args.schedule_root).resolve(), Path(args.preflight_directory).resolve()
    preflight.mkdir(parents=True, exist_ok=True)
    require(not output.exists() and not output.with_suffix(".approval.json").exists(),
            "Never replace a lock or its independent approval")
    require(not schedule.exists(), "New C200 schedule must be absent")
    definition, old_lock = verify_definition(root)
    preserved = verify_baseline_source(root, old_lock)
    require(schedule.as_posix() != old_lock["schedule_root"], "Cannot reuse C199's stopped schedule")
    require(read_json(root / "prototypes/static_tray_v01/export-settings.json")["export_loglevel"] == -1,
            "The observed logging compatibility defect is not repaired")
    tracked = set(subprocess.check_output(["git", "-C", str(root), "ls-files"], text=True).splitlines())
    normative = {DIRECTORY + "/" + name for name in REQUIRED_PROTOCOL}
    normative |= set(definition["preserved_files"])
    for relative in args.extra_input:
        require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
                "Additional input must be repository-relative")
        normative.add(relative)
    require(normative <= tracked, "Every protocol/preparation input must be tracked before sealing")
    current_changed = []
    for relative, binding in old_lock["repository_files"].items():
        if file_binding(root / relative) != binding:
            current_changed.append(relative)
    allowed = {"prototypes/static_tray_v01/worker.py", "prototypes/static_tray_v01/export-settings.json",
               "prototypes/static_tray_v01/qualification.py"}
    require(set(current_changed) <= allowed,
            "C200 scope changed a frozen geometry/source/reader/lifecycle input: " + repr(current_changed))

    # This inventory has only distribution-relative paths. Copy its exact bytes,
    # then let the full lock verifier remeasure every installed file/link/mode.
    source_inventory = root / OLD_DIRECTORY / "evidence/preflight/CLEAN-DISTRIBUTION-INVENTORY.json"
    distribution = preflight / "CLEAN-DISTRIBUTION-INVENTORY.json"
    with distribution.open("xb") as stream:
        stream.write(source_inventory.read_bytes())
    external = output.parent / "EXTERNAL-INPUTS.json"
    build_manifest(external, node=args.node, dependencies_root=args.dependencies_root,
                   schedule_root=schedule, host_inventory=args.host_inventory)
    lock, _ = build_lock(output, schedule_root=schedule, blender_root=args.blender_root,
                         blender_archive=args.blender_archive, distribution_inventory=distribution,
                         host_inventory=args.host_inventory, format_manifest=external)
    for relative in sorted(normative):
        lock["repository_files"][relative] = file_binding(root / relative)
    lock["qualification_revision"] = revision_binding(root, output, schedule, definition)
    lock["coordinator_command"] = [lock["host"]["python"], "-IBS", str(root / DIRECTORY / "run_qualification.py"),
                                   "--lock", str(output)]
    lock["coordinator_environment"] = lock["host_environment"]
    lock["c199_source_recovery"] = {"published_baseline_commit": definition["recovery_baseline_commit"],
                                     "matched_original_locked_files": preserved,
                                     "original_local_implementation": old_lock["implementation"],
                                     "original_local_commit_object_recovered": subprocess.run(
                                         ["git", "-C", str(root), "cat-file", "-e", old_lock["implementation"]["commit"] + "^{commit}"],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
                                     "meaning": "Exact input bytes recovered from the published tree; distinct commit identities remain distinct"}
    # The fresh unapproved lock is being assembled in this single preparation
    # operation. After this write it is immutable; any repair needs a new record.
    output.write_bytes(json_bytes(lock))
    verified, digest = verify_lock(output, approval=False)
    verify_revision(verified, output, approval=False, fresh=True)
    receipt = {"schema": "ontokin.c200.input-preparation/0.1", "status": "PASS_READ_ONLY_INPUT_PREPARATION",
               "observed_at_utc": datetime.now(timezone.utc).isoformat(), "qualification_revision": REVISION,
               "implementation": lock["implementation"], "input_lock_sha256": digest,
               "lock": str(output), "source_files": len(lock["repository_files"]),
               "preserved_c199_locked_files": preserved, "changed_c199_inputs": current_changed,
               "distribution_inventory_sha256": sha256_file(distribution),
               "host_inventory_sha256": sha256_file(Path(args.host_inventory)),
               "schedule_absent": not schedule.exists(), "approval_created": False,
               "native_starts": 0, "receiving_starts": 0, "read_only_checker_starts": 0,
               "metadata_probes": ["Node --version", "ldd Node"],
               "note": "Fresh host inventory separately records trusted loader inspections, never Blender main. Independent approval and actual qualification remain pending."}
    destination = preflight / "INPUT-PREPARATION.json"
    with destination.open("xb") as stream:
        stream.write(json_bytes(receipt))
    print(json.dumps(receipt, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
