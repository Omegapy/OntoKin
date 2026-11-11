"""Independent exact-file preservation check for one C207 candidate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--repo", type=Path, required=True)
p.add_argument("--baseline", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
a = p.parse_args()
repo, baseline, out = a.repo.resolve(), a.baseline.resolve(), a.out.resolve()
out.mkdir(parents=True, exist_ok=True)

def git(root, *arguments):
    return subprocess.run(["git", "--no-optional-locks", "-C", str(root), *arguments],
                          capture_output=True, text=True, check=True).stdout.strip()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

receipt_path = "docs/engineering/static-tray-admission-c201/evidence/transaction-c206/c206-validation/candidate-protected-inputs.json"
inherited = json.loads((baseline / receipt_path).read_bytes())

def verify(rows):
    result = []
    for row in rows:
        path = repo / row["path"]
        result.append({"path": row["path"], "expectedSha256": row["sha256"],
                       "expectedSizeBytes": row["size_bytes"],
                       "observedSha256": digest(path) if path.is_file() else None,
                       "observedSizeBytes": path.stat().st_size if path.is_file() else None})
    for row in result:
        row["match"] = row["expectedSha256"] == row["observedSha256"] and row["expectedSizeBytes"] == row["observedSizeBytes"]
    return result

locked = verify(inherited["lockedInputs"])
protocol = verify(inherited["protocolDocuments"])
prefixes = ["prototypes/static_tray_v01", "tools/static_tray_reader_v01", "fixtures/static_tray_v01",
            "docs/engineering/static-tray-mapping-c198", "docs/engineering/static-tray-qualification-c199",
            "docs/engineering/static-tray-exporter-c200"]
baseline_files = git(baseline, "ls-tree", "-r", "--name-only", "HEAD", "--", *prefixes).splitlines()
historical = verify([{"path": name, "sha256": digest(baseline / name), "size_bytes": (baseline / name).stat().st_size}
                     for name in baseline_files])
historical_diff = git(repo, "diff", "--name-status", "2a1ac8ccbdc290942e88504c640790b1bda9229c", "--", *prefixes)
extra = git(repo, "ls-files", "--others", "--exclude-standard", "--", *prefixes)
result = {"schema": "ontokin.c207.independent-preservation/0.1", "observedAtUtc": datetime.now(timezone.utc).isoformat(),
          "head": git(repo, "rev-parse", "HEAD"), "tree": git(repo, "rev-parse", "HEAD^{tree}"),
          "baselineHead": git(baseline, "rev-parse", "HEAD"), "baselineTree": git(baseline, "rev-parse", "HEAD^{tree}"),
          "inheritedBindingReceipt": receipt_path, "inheritedBindingReceiptSha256": digest(baseline / receipt_path),
          "lockedInputs": locked, "protocolDocuments": protocol, "historicalFiles": historical,
          "historicalTrackedDiff": historical_diff, "historicalUntrackedPaths": extra,
          "nativeStarts": 0, "historicalRuns": 0}
result["passed"] = (all(row["match"] for row in locked + protocol + historical)
                    and not historical_diff and not extra
                    and result["baselineHead"] == "2a1ac8ccbdc290942e88504c640790b1bda9229c")
(out / "PRESERVATION.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"head": result["head"], "lockedInputs": len(locked), "protocolDocuments": len(protocol),
                  "historicalFiles": len(historical), "passed": result["passed"]}))
raise SystemExit(0 if result["passed"] else 1)
