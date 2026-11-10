#!/usr/bin/env python3
"""Apply unchanged C191 motion/mapping gates to frozen C192 input values."""
import argparse
import json
from pathlib import Path
import sys


def load(repo):
    checker = repo / "docs/engineering/guided-contact-c191/independent/checker"
    sys.path.insert(0, str(checker))
    import measure_c191
    import audit_mapping
    inputs = json.loads((Path(__file__).resolve().parents[1] / "frozen/targets.json").read_text())
    for case in inputs["cases"]:
        measure_c191.CASES[case["id"]] = case
    return measure_c191, audit_mapping


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--case", choices=("baseline", "edit", "reuse"), required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    measure, mapping = load(a.repo.resolve())
    report = measure.measure(a.artifact / "final.glb", a.case)
    (a.out / "playback.json").write_text(json.dumps(report, indent=2) + "\n")
    try:
        audit = mapping.audit(a.artifact / "raw.glb", a.artifact / "final.glb", a.artifact / "native-transforms.json")
    except Exception as error:
        audit = {"passed": False, "reason": type(error).__name__ + ": " + str(error)}
    (a.out / "mapping.json").write_text(json.dumps(audit, indent=2) + "\n")
    result = {"case": a.case, "pass": report["pass"] and audit["passed"],
              "playback_pass": report["pass"], "mapping_pass": audit["passed"],
              "final_sha256": report["sha256"]}
    print(json.dumps(result))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
