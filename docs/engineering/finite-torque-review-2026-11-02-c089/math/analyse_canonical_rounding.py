#!/usr/bin/env python3
"""Separate C089 canonical-input witnesses after source-clock review.

This is an independent formula-level diagnostic, not an OntoKin runtime test.
All selected event/sample times below are exact dyadic binary64 values.
"""
from __future__ import annotations
import hashlib
import json
import math
import platform
import sys
from fractions import Fraction as F
from pathlib import Path

checks = []


def clean(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(item) for item in value]
    return value


def equal(name, actual, expected):
    checks.append({"name": name, "actual": clean(actual), "expected": clean(expected),
                   "passed": actual == expected})
    assert actual == expected, name


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def translation(p0, v0, split, end):
    p, v = F.from_float(p0), F.from_float(v0)
    first = float(p + v*split)
    direct = float(p + v*end)
    split_result = float(F.from_float(first) + v*(end-split))
    return {"p0_binary64": p0, "v0_binary64": v0,
            "p0_exact": p, "v0_exact": v,
            "acceleration": F(0), "split_clock": split, "end_clock": end,
            "stored_midpoint": first, "stored_midpoint_hex": first.hex(),
            "direct": direct, "direct_hex": direct.hex(),
            "reanchored": split_result, "reanchored_hex": split_result.hex(),
            "difference": F.from_float(split_result)-F.from_float(direct)}


def main():
    a = tuple(F.from_float(x) for x in (0.6, 0.8, 0.0))
    alpha = tuple(2*x for x in a)
    dt = F(1, 8)
    exact_omega = tuple(x+y*dt for x,y in zip(a,alpha))
    rounded = tuple(float(x) for x in exact_omega)
    canonical = tuple(F.from_float(x) for x in rounded)
    equal("axis clock is exactly binary64", F.from_float(float(dt)), dt)
    equal("initial exact collinearity", cross(a,a), (F(0),F(0),F(0)))
    equal("acceleration exact collinearity", cross(a,alpha), (F(0),F(0),F(0)))
    equal("unrounded exact collinearity", cross(a,exact_omega), (F(0),F(0),F(0)))
    equal("rounded components", rounded, (0.75,1.0,0.0))
    residual = cross(a,canonical)
    equal("nonzero exact residual after dyadic step", residual,
          (F(0),F(0),F(-1,18014398509481984)))

    # Independently selected after the parent's clock-domain review.
    primary = translation(1.0, 0.1, F(1,8), F(1))
    equal("primary split is exact binary64", F.from_float(float(primary["split_clock"])), primary["split_clock"])
    equal("primary end is exact binary64", F.from_float(float(primary["end_clock"])), primary["end_clock"])
    equal("primary direct hex", primary["direct_hex"], "0x1.199999999999ap+0")
    equal("primary reanchored hex", primary["reanchored_hex"], "0x1.1999999999999p+0")
    equal("primary exact difference", primary["difference"], F(-1,4503599627370496))
    equal("primary one ULP", -primary["difference"], F.from_float(math.ulp(primary["direct"])))

    # Independently verified corroboration proposed by the utility reviewer.
    corroboration = translation(1.0, 2.0**-52, F(1,2), F(1))
    equal("corroborating direct hex", corroboration["direct_hex"], "0x1.0000000000001p+0")
    equal("corroborating midpoint rounds down at tie", corroboration["stored_midpoint_hex"], "0x1.0000000000000p+0")
    equal("corroborating reanchored hex", corroboration["reanchored_hex"], "0x1.0000000000000p+0")
    equal("corroborating exact difference", corroboration["difference"], F(-1,4503599627370496))

    return clean({"status":"passed", "scope":"formula-level canonical binary64/dyadic input witnesses",
                  "production_runtime_executed":False, "torque_adopted":False,
                  "release_input_freeze":False,
                  "baseline_commit":"7b6900baa0357ab96c4639ac5c2ebe4e1791833e",
                  "review_correction":"Original analytic-witnesses.json used exact 3/10 and 2/5 clocks, which are valid mathematical diagnostics but are not directly authored binary64 source-event clocks. This separate report uses exact dyadic clocks and does not replace the original output.",
                  "axis_witness":{"stored_axis":a,"acceleration":alpha,"elapsed":dt,
                                  "unrounded_speed":exact_omega,"rounded_speed":rounded,"cross_product":residual},
                  "translation_primary":primary,"translation_corroboration":corroboration,
                  "corroboration_attribution":"Proposed independently by torque_utility_review; independently verified here",
                  "python":sys.version,"platform":platform.platform(),
                  "check_count":len(checks),"checks":checks})


if __name__ == "__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python3 analyse_canonical_rounding.py FRESH_OUTPUT.json")
    result=main()
    result["script_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with Path(sys.argv[1]).open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status":result["status"],"check_count":result["check_count"],"scope":result["scope"]},sort_keys=True))
