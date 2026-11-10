#!/usr/bin/env python3
"""Exercise analytic fixtures and the inherited continuous slab certificate."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import swept_overlap
from make_controls import generate
from measure_c191 import measure


def run(destination):
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="c191-independent-controls-") as temporary:
        root = Path(temporary)
        controls = generate(root)
        results = []
        for control in controls:
            result = measure(root / control["file"], control["case"])
            reason = control["expected_reason_contains"]
            correct = result["pass"] == control["expected_pass"] and (reason is None or reason in result.get("reason", ""))
            results.append({**control, "observed_pass": result["pass"], "observed_reason": result.get("reason"),
                "verified": correct})
            (destination / (control["file"] + ".json")).write_text(json.dumps(result, indent=2) + "\n")
        # These endpoint boxes are disjoint. Their continuous paths cross.
        unit = np.array([[0., 0., 0.], [1., 1., 1.]])
        cases = [("crosses-between-keys", unit, unit + [4, 0, 0], unit + [3, 0, 0], unit + [3, 0, 0], True),
            ("separated-in-z", unit, unit + [4, 0, 0], unit + [3, 0, 2], unit + [3, 0, 2], False),
            ("endpoint-contact", unit, unit + [2, 0, 0], unit + [3, 0, 0], unit + [3, 0, 0], False)]
        slabs = []
        for name, a0, a1, b0, b1, expected in cases:
            witness = swept_overlap(a0, a1, b0, b1)
            slabs.append({"name": name, "expected_collision": expected, "witness_fraction": witness,
                "verified": (witness is not None) == expected})
    report = {"version": "C191-independent-checker-qualification-1", "candidate_outputs_inspected": False,
        "python": platform.python_version(), "numpy": np.__version__, "controls": results, "swept_slabs": slabs,
        "positive_controls": sum(row["expected_pass"] for row in results),
        "negative_controls": sum(not row["expected_pass"] for row in results),
        "pass": all(row["verified"] for row in results + slabs)}
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out)
    (args.out / "qualification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"pass": report["pass"], "positive": report["positive_controls"], "negative": report["negative_controls"],
        "failures": [row for row in report["controls"] if not row["verified"]]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)
