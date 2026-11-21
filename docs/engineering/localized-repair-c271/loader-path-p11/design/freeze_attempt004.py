"""Freeze authored controls and exact delta; no product execution or policy test."""
from pathlib import Path
import difflib
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parent
OLD = ROOT / "candidate002"
NEW = ROOT / "candidate004"
OLD_SHA = "563e84cc83f31a202cc0eead9102b66b08050ea011dfbbf4ed6fc19db318c8f4"


def descriptor(path, relative_to):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(relative_to)), "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(), "mode": oct(stat.S_IMODE(path.stat().st_mode))}


def write(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n")


old_raw = (OLD / "CANDIDATE-MANIFEST.json").read_bytes()
assert hashlib.sha256(old_raw).hexdigest() == OLD_SHA
old_manifest = json.loads(old_raw)
for row in old_manifest["payload"] + old_manifest["supporting_files"]:
    path = OLD / row["path"]
    raw = path.read_bytes()
    assert len(raw) == row["size_bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], row["path"]
    if "mode" in row:
        assert oct(stat.S_IMODE(path.stat().st_mode)) == row["mode"], row["path"]

retention = json.loads((ROOT / "ATTEMPT003-RETENTION.json").read_text())
for row in retention["preserved_payload"] + retention["preserved_support"]:
    path = ROOT / row["path"]
    raw = path.read_bytes()
    assert len(raw) == row["size_bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], row["path"]
    assert oct(stat.S_IMODE(path.stat().st_mode)) == row["mode"], row["path"]

old_oracle_raw = (OLD / "EXPECTATIONS.json").read_bytes()
old_oracle = json.loads(old_oracle_raw)
new_oracle = json.loads((NEW / "EXPECTATIONS.json").read_bytes())
assert all(new_oracle["cases"][key] == value for key, value in old_oracle["cases"].items())
projection = dict(new_oracle)
projection["cases"] = {key: new_oracle["cases"][key] for key in old_oracle["cases"]}
projection_raw = (json.dumps(projection, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")
assert projection_raw == old_oracle_raw
new_ids = sorted(set(new_oracle["cases"]) - set(old_oracle["cases"]))
assert len(new_ids) == 4

old_rows = {row["path"]: row for row in old_manifest["payload"]}
current_paths = {str(path.relative_to(NEW)): path for path in NEW.rglob("*") if path.is_file()}
assert set(old_rows).issubset(current_paths)
changed, unchanged, added = [], [], []
for name, path in sorted(current_paths.items()):
    row = descriptor(path, NEW)
    if name not in old_rows:
        added.append(row)
    elif row["sha256"] != old_rows[name]["sha256"] or row["mode"] != old_rows[name].get("mode", row["mode"]):
        changed.append({"path": name, "old": old_rows[name], "new": row})
    else:
        unchanged.append(row)
changed_fixtures = sorted(row["path"] for row in changed if row["path"].startswith("fixture_inputs/"))
assert changed_fixtures == ["fixture_inputs/N69_expansion_4097_bytes.json", "fixture_inputs/P07_expansion_4096_bytes.json"]

diff_names = [row["path"] for row in changed if not row["path"].startswith("fixture_inputs/")
    and row["path"] not in {"EXPECTATIONS.json", "CONSTRUCTION.json", "FIXTURE-MANIFEST.json"}]
with (NEW / "REVISION-004.diff").open("x") as stream:
    for name in diff_names:
        stream.writelines(difflib.unified_diff((OLD / name).read_text().splitlines(keepends=True),
            (NEW / name).read_text().splitlines(keepends=True), fromfile="candidate002/" + name,
            tofile="candidate004/" + name))

report = json.loads((ROOT / "static004.stdout.json").read_text())
assert report["passed"] and report["check_count"] == 1149 and report["case_count"] == 97
write(NEW / "REVISION-004.json", {
    "schema": "ontokin.c271.p11-candidate-revision/1", "candidate": "candidate004",
    "previous_candidate": "candidate002", "previous_manifest_sha256": OLD_SHA,
    "previous_payload_files_verified_unchanged": len(old_manifest["payload"]),
    "previous_support_files_verified_unchanged": len(old_manifest["supporting_files"]),
    "withdrawn_attempt003": {"retention": "../ATTEMPT003-RETENTION.json", "verified_payloads": len(retention["preserved_payload"]), "verified_supports": len(retention["preserved_support"]), "excluded_cases": ["P08_variant_reader_4mib", "N74_variant_reader_over_bound"], "reason": "No concrete need for a new document-size policy; inherit existing 16 MiB reader behavior."},
    "old_expectations": {"count": len(old_oracle["cases"]), "all_records_unchanged": True,
        "old_file_sha256": hashlib.sha256(old_oracle_raw).hexdigest(),
        "new_projection_original_serialization_sha256": hashlib.sha256(projection_raw).hexdigest()},
    "new_expected_records": {key: new_oracle["cases"][key] for key in new_ids},
    "changed_previous_payloads": changed, "unchanged_previous_payloads": unchanged, "added_payloads_before_revision_records": added,
    "diff_scope": {"file": "REVISION-004.diff", "paths": diff_names,
        "omitted_from_text_diff": "Exact fixture/oracle/construction manifests are bound above and can be compared directly; no implementation source changed."},
    "corrections": [
        "P07/N69 short synthetic basename, base-only suffixes and complete exact ancestor guard sets isolate raw byte bounds.",
        "New-profile ASCII restriction makes byte-count semantics exact without altering legacy character checks.",
        "P09/N75 isolate 128/129 components including root and unreduced parent.",
        "The variant document inherits existing _document/LIMITS document_bytes 16 MiB behavior; the extra cap, reader seam and P08/N74 are withdrawn and preserved in attempt003.",
        "N76/N77 independently refuse coherent non-ASCII origin/suffix contexts.",
        "MATERIALIZATION.md preserves exact inert bytes and recorded modes through Git transport without runtime/pin substitution."
    ],
    "boundary_measurements": report["boundary_measurements"],
    "static_report": "../static004.stdout.json", "source_oracle_derived_from_production": False,
    "production_files_changed": [], "product_execution": False, "h0_accepted": False,
    "self_binding": "This revision and its text diff are bound by the new external candidate manifest, not by a recursive self-hash."
})

support = list(old_manifest["supporting_files"])
extra_support = ["prepare_attempt004.py", "build_controls_attempt004.py", "validate_artifacts_attempt004.py",
    "document_attempt004.py", "freeze_attempt004.py", "prepare004.stdout.txt", "prepare004.stderr.txt",
    "build004.stdout.txt", "build004.stderr.txt", "static004.stdout.json", "static004.stderr.txt",
    "document004.stdout.txt", "document004.stderr.txt", "ATTEMPT003-RETENTION.json"]
for name in extra_support:
    row = descriptor(ROOT / name, ROOT)
    row["path"] = "../" + row["path"]
    support.append(row)
previous_manifest = descriptor(OLD / "CANDIDATE-MANIFEST.json", ROOT)
previous_manifest["path"] = "../" + previous_manifest["path"]
support.append(previous_manifest)
payload = [descriptor(path, NEW) for path in sorted(NEW.rglob("*")) if path.is_file()]
assert all(stat.S_ISREG((NEW / row["path"]).lstat().st_mode) and not (NEW / row["path"]).is_symlink() for row in payload)
assert all(row["mode"] in {"0o600", "0o644"} for row in payload)
write(NEW / "CANDIDATE-MANIFEST.json", {
    "schema": "ontokin.c271.p11-exact-candidate/1", "candidate": "candidate004", "author": "/root/loader_design",
    "state": "frozen_for_independent_review", "payload": payload, "supporting_files": support,
    "retained_previous_attempts": ["../candidate001", "../candidate002", "../candidate003"],
    "withdrawn_attempt_retention": "../ATTEMPT003-RETENTION.json",
    "previous_manifest_sha256": OLD_SHA, "revision": "REVISION-004.json", "materialization": "MATERIALIZATION.md",
    "product_execution": False, "product_files_changed": [], "host_qualification": False
})
frozen = descriptor(NEW / "CANDIDATE-MANIFEST.json", ROOT)
print(json.dumps({"candidate_manifest": frozen, "payload_count": len(payload), "support_count": len(support),
    "changed_previous_payload_count": len(changed), "changed_old_fixture_inputs": changed_fixtures,
    "new_case_ids": new_ids, "all_93_old_expectations_preserved": True,
    "product_execution": False, "h0_accepted": False}, sort_keys=True, indent=2))
