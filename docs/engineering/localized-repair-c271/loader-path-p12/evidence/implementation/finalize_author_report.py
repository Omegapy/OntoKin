"""Record static source preservation and the stopped worker result."""
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import sys
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "OntoKin"
BASE = REPO / "docs/engineering/localized-repair-c271/loader-path-p11/design/candidate004"


def identity(path):
    raw = path.read_bytes()
    return {"size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "mode": oct(stat.S_IMODE(path.lstat().st_mode))}


def write(name, value):
    with (HERE / name).open("x") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")


protected = json.loads((BASE / "PROTECTED-SOURCES.json").read_bytes())
rows = []
for row in protected["files"]:
    actual = identity(REPO / row["path"])
    matches = all(actual[key] == row[key] for key in ("sha256", "size_bytes"))
    rows.append({"path": row["path"], "expected": row, "actual": actual, "matches": matches})
new_test = REPO / "tests/test_current_host_loader_path_v01.py"
preserved = all(row["matches"] for row in rows) and not new_test.exists() and not new_test.is_symlink()
write("SOURCE-PRESERVATION.json", {"schema": "ontokin.c271.p12-static-source-preservation/1",
      "passed": preserved, "rows": rows, "new_test_absent": not new_test.exists(),
      "comparison_source": str(BASE / "PROTECTED-SOURCES.json"),
      "comparison_source_identity": identity(BASE / "PROTECTED-SOURCES.json"),
      "supplied_source_revision": "79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae",
      "original_freeze_revision": protected["source_commit_supplied_by_director"],
      "behavior_executed": False, "git_process_used": False})

assert preserved, "Current protected source differs; retain comparison and report to Director"
write("AUTHOR-RESULT.json", {"schema": "ontokin.c271.p12-implementation-author-result/1",
      "worker": "/root/loader_implementation", "role": "Implementer",
      "phase": "C271-P12-loader-path-implementation", "verdict": "stopped_concrete_surface_blocker",
      "blocker": "P12-N57-POLICY-BINDING-001", "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
      "director_stop_received": True, "independent_agreement": "Relayed by Director; separate reviewer artifact is Director-owned.",
      "selected_source_revision": "79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae",
      "candidate_manifest_sha256": "e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de",
      "expectations_sha256": "dfb285f41a58a1f7254aaae4aa022f91afdc72fb7d5dad2f3d6b1e8257d14137",
      "fixture_manifest_sha256": "ea377d25e96631b70cd8909a5375fa3fd0feadf7f017f0673d8a094335186594",
      "source_test_edits": [], "adapter_constructed": False, "product_imports": 0,
      "behavior_tests_run": 0, "frozen_97_controls": "not_run", "inherited_175_methods": "not_run",
      "source_preservation": {"passed": preserved, "protected_files": len(rows), "new_test_absent": True},
      "materialization": {"passed": True, "files": 178, "fixture_files": 131, "frozen_cases": 97,
                          "receipt": "MATERIALIZATION-RECEIPT.json", "attempt": "MATERIALIZATION-ATTEMPT001.json"},
      "environment": {"executable": sys.executable, "python": sys.version, "platform": platform.platform(),
                      "selected_variables": {k: os.environ.get(k) for k in ("PATH", "LANG", "LC_ALL", "TZ", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED")}},
      "author_report": "REPORT.md", "question_record": "N57-SURFACE-QUESTION.json",
      "failed_behavior_attempts": [], "failed_materialization_attempts": [],
      "read_output_limitations": "Preserved in MATERIALIZATION-ATTEMPT001.json; affected required reads repeated.",
      "active_processes": [], "unknown_operations": [], "pending_writes": [],
      "historical_unknowns_unresolved": ["C270 broad-driver completion remains unknown", "Global prior-process termination remains unestablished"],
      "git_index_ref_operations": [], "publication_integration": [],
      "next_action": "Director publishes preserved blocker, verifies and saves partial handoff, then stops; no further implementation in this phase."})

names = []
for p in sorted(HERE.rglob("*")):
    if p.is_file() and p.name != "AUTHOR-MANIFEST.json":
        names.append({"path": p.relative_to(HERE).as_posix(), **identity(p)})
write("AUTHOR-MANIFEST.json", {"schema": "ontokin.c271.p12-worker-artifacts/1",
      "worker": "/root/loader_implementation", "excludes": ["AUTHOR-MANIFEST.json"],
      "files": names, "files_count": len(names)})
print(json.dumps({"verdict": "stopped_concrete_surface_blocker", "source_preservation": preserved,
                  "protected_files": len(rows), "artifact_files": len(names)}))
