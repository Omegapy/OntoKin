#!/usr/bin/env python3
"""Pure exact-arithmetic checks of the proposed recording contract, not a GLB validator."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import struct
import sys


def binary32_value(bits: int) -> F:
    if not 0 <= bits < 0x7F800000:
        raise ValueError("nonnegative finite binary32 required")
    exponent, trailing = (bits >> 23) & 255, bits & 0x7FFFFF
    if exponent == 0:
        return F(trailing, 1 << 149)
    significand, shift = (1 << 23) + trailing, exponent - 150
    return F(significand << shift) if shift >= 0 else F(significand, 1 << -shift)


def direct_clock_bits(value: F) -> int:
    """Independent monotonic-code search with exact adjacent distances and tie parity."""
    value = F(value)
    if value < 0:
        raise ValueError("negative clock")
    largest = binary32_value(0x7F7FFFFF)
    if value >= largest + F(1 << 103):
        raise ValueError("clock overflows binary32")
    if value >= largest:
        return 0x7F7FFFFF
    low, high = 0, 0x7F7FFFFF
    while low + 1 < high:
        middle = (low + high) // 2
        if binary32_value(middle) <= value:
            low = middle
        else:
            high = middle
    a, b = value - binary32_value(low), binary32_value(high) - value
    if a == b:
        return low if low % 2 == 0 else high
    return low if a < b else high


def atan_interval(x: F, terms: int) -> tuple[F, F]:
    assert 0 < x < 1
    total = sum(((-1) ** k * x ** (2 * k + 1) / (2 * k + 1)
                 for k in range(terms)), F(0))
    next_term = (-1) ** terms * x ** (2 * terms + 1) / (2 * terms + 1)
    return min(total, total + next_term), max(total, total + next_term)


a_lo, a_hi = atan_interval(F(1, 5), 50)
b_lo, b_hi = atan_interval(F(1, 239), 15)
PI_LO, PI_HI = 16 * a_lo - 4 * b_hi, 16 * a_hi - 4 * b_lo


def touched_phases(authored: tuple[F, F], stored: tuple[F, F],
                   phases: list[tuple[F, F]]) -> list[int]:
    left, right = min(*authored, *stored), max(*authored, *stored)
    return [i for i, (start, end) in enumerate(phases)
            if max(left, start) < min(right, end)]


def clamp_to_prefix(t: F, start: F, end: F) -> F:
    return max(start, min(end, t))


def derived_bounds(v: dict) -> dict[str, F]:
    d = v["ep_q"] + v["w"] ** 2 * v["ha"] ** 2 / 32 + v["theta"] ** 2 / 8
    rotation = 4 * d + v["nsr"] + v["ndr"] + v["we"] * v["delta"]
    carrier = v["ep_p"] + v["a"] * v["ha"] ** 2 / 8 + v["nsp"] + v["ndp"] + v["ve"] * v["delta"]
    return {"D": d, "rotation": rotation, "carrier": carrier,
            "position": carrier + v["r"] * rotation + v["ev"]}


def accept_example(v: dict) -> dict[str, F]:
    # These checks exercise the contract on assumed exact bounds; they establish
    # no numerical bound for an actual source, writer or destination algorithm.
    numeric = ["ha", "hs", "w", "we", "a", "ae", "ve", "theta", "delta",
               "ep_q", "ep_p", "r", "ev", "nsr", "ndr", "nsp", "ndp", "ptol", "rtol", "ttol"]
    if any(not isinstance(v[k], F) or v[k] < 0 for k in numeric):
        raise ValueError("unproved or negative finite bound")
    if not (v["ha"] > 0 and v["hs"] > 0 and v["ptol"] > 0 and v["rtol"] > 0
            and 0 < v["ttol"] <= F(1, 1_000_000)):
        raise ValueError("invalid gap or tolerance")
    if not v["source_proved"] or not v["destination_proved"]:
        raise ValueError("unknown numeric term")
    if v["destination_identity"] != v["required_destination_identity"]:
        raise ValueError("destination identity")
    if not set(v["required_phases"]).issubset(v["phases"]):
        raise ValueError("omitted source phase")
    if v["delta"] > v["ttol"] or v["theta"] > PI_LO / 4:
        raise ValueError("clock or quaternion arc")
    for h, a, w in [(v["ha"], v["a"], v["w"]), (v["hs"], v["ae"], v["we"])]:
        b = w * w * h * h / 4
        p = a * h * h / 8
        if w * h > PI_LO / 4 or b > v["rtol"] / 4 or p + v["r"] * b > v["ptol"] / 4:
            raise ValueError("authored/stored planning bound")
    bounds = derived_bounds(v)
    if (bounds["D"] > F(1, 2) or bounds["rotation"] > v["rtol"]
            or max(bounds["carrier"], bounds["position"]) > v["ptol"]):
        raise ValueError("complete error bound")
    return bounds


def run_checks() -> dict:
    checks: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def rejects(name: str, call) -> None:
        try:
            call()
        except ValueError:
            checks.append(name)
        else:
            raise AssertionError("required rejection: " + name)

    check("Machin interval lies strictly between 3 and 22/7", 3 < PI_LO < PI_HI < F(22, 7))
    for name, value, bits in [
        ("canonical zero", F(0), 0), ("one", F(1), 0x3F800000),
        ("even midpoint below one", F(1) - F(1, 1 << 25), 0x3F800000),
        ("even midpoint above one", F(1) + F(1, 1 << 24), 0x3F800000),
        ("odd lower midpoint rounds up", F(1) + F(3, 1 << 24), 0x3F800002),
        ("minimum subnormal", F(1, 1 << 149), 1),
        ("zero subnormal midpoint", F(1, 1 << 150), 0),
        ("odd subnormal midpoint", F(3, 1 << 150), 2),
        ("minimum normal", F(1, 1 << 126), 0x00800000),
        ("normal transition tie", F((1 << 24) - 1, 1 << 150), 0x00800000),
        ("largest finite", binary32_value(0x7F7FFFFF), 0x7F7FFFFF),
    ]:
        check(name, direct_clock_bits(value) == bits)
    rejects("negative clocks rejected", lambda: direct_clock_bits(F(-1)))
    rejects("overflow midpoint rejected", lambda: direct_clock_bits(binary32_value(0x7F7FFFFF) + (1 << 103)))
    special = F(1) + F(1, 1 << 24) + F(1, 1 << 80)
    double_bits = struct.unpack(">I", struct.pack(">f", float(special)))[0]
    check("Q18 direct exact rational differs from double rounding",
          direct_clock_bits(special) == 0x3F800001 and double_bits == 0x3F800000)
    pause, resume = F(float("0.50000002")), F(float("1.50000002"))
    complete = F(2) + resume - pause
    check("Q16 exact canonical clock identities", (pause, resume, complete) == (
        F(4503599807514481, 9007199254740992), F(6755399531127737, 4503599627370496),
        F(27021597764222977, 9007199254740992)))
    check("Q16 direct stored clock bits", [direct_clock_bits(t) for t in [pause, resume, complete]]
          == [0x3F000000, 0x3FC00000, 0x40400000])
    phases = [(F(0), pause), (pause, resume), (resume, complete), (complete, F(4))]
    check("Q16 positive-width moving neighbor included", touched_phases((pause, F(1)), (F(1, 2), F(1)), phases) == [0, 1]
          and pause - F(1, 2) == F(180143985, 9007199254740992))
    check("Q10 distinct canonical semantic clocks collapse", F(float("0.50000001")) > F(1, 2)
          and direct_clock_bits(F(float("0.50000001"))) == direct_clock_bits(F(1, 2)))
    check("rounded tail is held without future source evaluation", clamp_to_prefix(F(3), F(0), F(3) - F(1, 1 << 60))
          == F(3) - F(1, 1 << 60))
    base = dict(ha=F(1, 1000), hs=F(5001, 5_000_000), w=F(1), we=F(2), a=F(2), ae=F(3), ve=F(2),
                theta=F(1, 2000), delta=F(1, 10_000_000), ep_q=F(1, 100_000_000), ep_p=F(3, 1_000_000_000),
                r=F(3), ev=F(1, 100_000_000), nsr=F(1, 1_000_000_000), ndr=F(2, 1_000_000_000_000),
                nsp=F(1, 1_000_000_000_000), ndp=F(0), ptol=F(1, 1000), rtol=F(1, 1000), ttol=F(1, 1_000_000),
                source_proved=True, destination_proved=True, destination_identity="synthetic_exact_bounds/1",
                required_destination_identity="synthetic_exact_bounds/1", required_phases=[0, 1], phases=[0, 1])
    bounds = accept_example(base)
    check("exact nonzero-endpoint complete bound", bounds == {"D":F(29, 400_000_000),
          "rotation":F(245501, 500_000_000_000), "carrier":F(453001, 1_000_000_000_000),
          "position":F(1936007, 1_000_000_000_000)})
    for name, updates in [
        ("unknown source error rejected", {"source_proved":False}),
        ("unknown destination error rejected", {"destination_proved":False}),
        ("wrong destination identity rejected", {"destination_identity":"other"}),
        ("omitted neighboring phase rejected", {"phases":[1]}),
        ("stored gap must independently pass", {"hs":F(1)}),
        ("endpoint error cannot consume unproved tolerance", {"ep_p":F(1)}),
        ("unproved radius cannot be negative", {"r":F(-1)}),
        ("clock tolerance cannot be raised", {"ttol":F(1, 1000)}),
        ("quaternion branch arc is bounded", {"theta":F(1)}),
    ]:
        changed = deepcopy(base); changed.update(updates)
        rejects(name, lambda changed=changed: accept_example(changed))
    return {"checks_passed":len(checks), "checks":checks,
            "synthetic_exact_bounds":{k:str(v) for k,v in bounds.items()},
            "establishes_actual_source_or_destination_numeric_bounds":False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    result = run_checks()
    here = Path(__file__).resolve().parent
    report = {"schema":"ontokin.reach-quantization-contract-check/0.2", "status":"passed",
              "scope":"pure reconstructed contract checks; no runtime, GLB, Agent or destination execution",
              "started_at":started,"finished_at":datetime.now(timezone.utc).isoformat(),
              "python":sys.version,"platform":platform.platform(), **result,
              "inputs":[{"path":name,"bytes":len((here/name).read_bytes()),
                         "sha256":hashlib.sha256((here/name).read_bytes()).hexdigest()}
                        for name in ["quantization.md", "verify_quantization_contract.py"]]}
    raw = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(raw)
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
