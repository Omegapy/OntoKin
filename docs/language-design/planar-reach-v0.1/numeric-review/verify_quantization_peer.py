#!/usr/bin/env python3
"""Independent fixed-input direct32 crosscheck and hash-bound contract review.

No OntoKin runtime, Agent, exporter, browser or archive is executed. The reviewed
text hashes are pinned: a changed contract needs another review, not this label.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys

sys.dont_write_bytecode = True
PINNED = {
    "quantization.md": (17761, "ee8b60cf240615966f6c4f9724ec45fc7c90964ce7c6ff873b65e8b779520184"),
    "verify_quantization_contract.py": (10322, "80cc872c641a37e9f8773dabcbf4cb0af29974a3eabe099df27dc17e6425f2dd"),
    "draft2-supplements/sources/q16-nonbinary-boundaries.ok": (1114, "1b8ac46ebed51dc99264c582a223953a5925e589f4eacb7de9ca8b3e42524ef3"),
    "draft2-supplements/q16.files.json": (657, "298749526ba81c551d3d8e240c26aa7423ce6503ff2f937a5f31bf43af2ea188"),
    "draft2-supplements/recording-probes.json": (10932, "cf50015e6c7e46833ede254963806fa28aa4b9f3cc9939234799bfdf043e7123"),
}


def identity(path):
    raw = path.read_bytes()
    return len(raw), hashlib.sha256(raw).hexdigest()


def independently_rounded_binary32(value):
    """Integer exponent/significand calculation; does not call the code search."""
    if value < 0:
        raise ValueError("negative clock")
    if value == 0:
        return 0
    numerator, denominator = value.numerator, value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    below = (numerator < denominator << exponent) if exponent >= 0 else (numerator << -exponent < denominator)
    if below:
        exponent -= 1
    if exponent > 127:
        raise ValueError("overflow")
    shift = 149 if exponent < -126 else 23 - exponent
    numerator, denominator = ((numerator << shift, denominator) if shift >= 0 else
                              (numerator, denominator << -shift))
    significand, remainder = divmod(numerator, denominator)
    significand += 2*remainder > denominator or (2*remainder == denominator and significand % 2)
    if exponent < -126:
        return significand
    if significand == 1 << 24:
        significand >>= 1
        exponent += 1
    if exponent > 127:
        raise ValueError("overflow")
    return ((exponent + 127) << 23) | (significand - (1 << 23))


def run(proposal):
    started = datetime.now(timezone.utc).isoformat()
    before = {name: identity(proposal/name) for name in PINNED}
    if before != PINNED:
        raise AssertionError("The proposed contract or identified Q16 inputs changed; review required")
    spec = importlib.util.spec_from_file_location("reviewed_quantization_checker", proposal/"verify_quantization_contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    values = [F(0), F(1,1 << 150), F(3,1 << 150), F(1)+F(1,1 << 24)+F(1,1 << 80)]
    for exponent in range(-126, 128):
        for trailing in [0, 1, (1 << 23)-2]:
            bits = ((exponent+127) << 23) | trailing
            left, right = module.binary32_value(bits), module.binary32_value(bits+1)
            midpoint = (left+right)/2
            epsilon = (right-left)/F(1 << 40)
            values.extend([left, midpoint-epsilon, midpoint, midpoint+epsilon])
    for value in values:
        actual, independent = module.direct_clock_bits(value), independently_rounded_binary32(value)
        if actual != independent:
            raise AssertionError("independent direct32 mismatch: "+str(value))
    pure = module.run_checks()
    if len(values) != 3052 or pure["checks_passed"] != 30:
        raise AssertionError("fixed review inventory changed")
    after = {name: identity(proposal/name) for name in PINNED}
    if after != before:
        raise AssertionError("reviewed files changed while checking")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=proposal, text=True).strip()
    own_size, own_sha = identity(Path(__file__).resolve())
    return {
        "schema_version": "ontokin.reach-quantization-peer-review/0.2",
        "status": "passed_contract_review", "reviewer": "/root/reach_numeric_recovery14",
        "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_checkout_head": head,
        "input_identity_note": "The exact file hashes identify the reviewed working tree even when it is newer than the checkout head.",
        "python": sys.version, "platform": platform.platform(),
        "inputs": [{"path":name, "bytes":size, "sha256":sha} for name,(size,sha) in before.items()],
        "peer_checker": {"path":"numeric-review/verify_quantization_peer.py", "bytes":own_size, "sha256":own_sha},
        "independent_direct_binary32_cases": len(values), "all_direct_binary32_cases_match": True,
        "direct_binary32_method": "Separate integer exponent and nearest-even quotient/remainder calculation versus the author's monotonic bit-code search.",
        "direct_binary32_coverage": "Every normal exponent -126 through127; low even/odd and near-top significands; exact values and both neighbors of midpoint ties; zero, subnormal ties and fixed Q18 double-rounding input.",
        "author_pure_contract_checks_passed": pure["checks_passed"],
        "reviewed_arguments": [
            "The ideal continuous quaternion second-derivative bound gives authored chord error W^2*h_a^2/32.",
            "Exact unit-endpoint SLERP has quaternion arc acceleration theta_s^2, so its chord error is theta_s^2/8; endpoint chord error adds e_q without an unproved endpoint-Lipschitz premise.",
            "With D<=1/2 the coherent quaternion Euclidean bound implies rotation distance4*asin(d/2)<=4*d<=4*D.",
            "The exact time-parameter pairing shifts time by at most delta; complete touched-phase speed bounds add V_E*delta and W_E*delta, including nonbinary Q16's positive-width moving neighbor.",
            "Exact rational direct binary32 conversion resolves midpoint parity and Q18; rounded semantic-key collapse remains an explicit failure.",
            "The held final-prefix extension adds no future source evaluation and keeps all actual interior phases; a pose jump or missing valid side is rejected.",
            "Carrier, source-radius rotation, vertex conversion and uniform actual source/destination numerical errors combine by triangle inequality; source/destination non-rigid transform arithmetic is included explicitly.",
        ],
        "resolved_review_clarifications": [
            {"issue":"Conservative derivative bounds must follow the ideal continuous source, not possibly downward-rounded inspection rates.",
             "resolution":"Section3 now explicitly requires exact canonical operand ratios including(target-start)/duration and outward derivative bounds."},
            {"issue":"An orientation-angle error alone does not bound nonorthonormal matrix or vertex-transform arithmetic.",
             "resolution":"Section4 now charges origin error plus matrix/vertex residual uniformly at radius r+e_v to the positional numerical allowances, including operator-norm defects."},
        ],
        "external_format_reference": {
            "url":"https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#appendix-c-animation-sampler-interpolation-modes",
            "observed_version":"2.0.1", "observed_page_commit":"8e798b02d254cea97659a333cfcb20875b62bdd4",
            "scope":"Appendix C.3-C.4 specifies componentwise linear translation and short-arc unit-quaternion spherical interpolation; destination approximations require their own actual numerical bound.",
            "accessed_date":"2026-10-20",
        },
        "blocking_findings": [], "actual_runtime_agent_export_or_destination_execution": False,
        "actual_source_or_destination_numeric_kernel_proved": False, "proposal_adopted": False,
        "remaining_requirements": [
            "Uniform identified source and actual destination kernel derivations, including parameter/normalization/matrix branches and operand ranges.",
            "Actual source-built and Agent-retrieved GLBs, independently recomputed metadata/geometry/phase/certificate values, isolated hostile-byte failures and complete coverage.",
            "Browser playback, full visual review, inherited compatibility roles and complete finite release audit.",
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-root",type=Path,default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    report=run(args.proposal_root.resolve())
    raw=json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open("x",encoding="utf-8") as stream:
            stream.write(raw)
    print(raw,end="")


if __name__ == "__main__":
    main()
