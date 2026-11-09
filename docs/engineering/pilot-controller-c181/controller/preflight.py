"""Run only harmless controller admission probes in a new operator-owned directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from gate import Gate, Stopped


def refused(gate, model, snapshot, marker):
    try:
        gate.infer(model, "Reply briefly to the readiness check.", snapshot, 1)
    except Stopped:
        model_denied = True
    else:
        model_denied = False
    try:
        gate.tool([sys.executable, "-I", "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).touch()", marker])
    except Stopped:
        tool_denied = True
    else:
        tool_denied = False
    return model_denied and tool_denied and not marker.exists()


def probe(directory, model, snapshot, seconds):
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    marker = directory.resolve() / "should-not-exist"
    began = directory.resolve() / "active-tool-started"
    client = model or [sys.executable, "-I", "-c", "raise RuntimeError('forbidden model dispatch')"]
    result = {"mode": "with model" if model else "wall only", "snapshot": snapshot,
              "wallPassed": False, "tokenPassed": False, "admitted": False}
    with (directory / "events.jsonl").open("x") as trace:
        try:
            gate = Gate(0.50, 64, trace, "active tool deadline")
            # An unexpired operation would create the second marker 0.8 seconds after launch.
            try:
                gate.tool([sys.executable, "-I", "-c",
                           "import sys,time; from pathlib import Path; Path(sys.argv[1]).touch(); "
                           "time.sleep(.8); Path(sys.argv[2]).touch()", began, marker])
            except Stopped:
                pass
            time.sleep(.85)
            result["wallPassed"] = (began.is_file() and gate.stopped == "deadline"
                                    and refused(gate, client, snapshot, marker))
            if not result["wallPassed"]:
                raise ValueError("active tool deadline or subsequent dispatch refusal failed")
            if model:
                # The same bytes enter each real request, including an actual tool result.
                control = Gate(seconds, 4096, trace, "calibration")
                tool_result = control.tool([sys.executable, "-I", "-c", "print('READY')"]).decode()
                prompt = "The readiness tool returned " + tool_result + "Acknowledge with one token."
                _, first = control.infer(model, prompt, snapshot, 1)
                if first["output"] != 1:
                    raise ValueError("one output token required for this probe")
                limit = 2 * first["charged"]
                capped = Gate(seconds, limit, trace, "aggregate exhaustion")
                for _ in range(2):
                    _, actual = capped.infer(model, prompt, snapshot, 1)
                    if actual["charged"] != first["charged"]:
                        raise ValueError("request cost differed from calibration")
                result.update(cappedRequests=2, cap=limit, charged=capped.charged,
                              calibrationCharged=first["charged"])
                result["tokenPassed"] = (capped.stopped == "token budget exhausted"
                                         and refused(capped, model, snapshot, marker))
                if not result["tokenPassed"]:
                    raise ValueError("aggregate cutoff or subsequent dispatch refusal failed")
        except (OSError, ValueError, Stopped) as exc:
            result["failure"] = str(exc)
    result["traceSha256"] = hashlib.sha256((directory / "events.jsonl").read_bytes()).hexdigest()
    # Other gates include isolation, a frozen image, arm-specific tools and a dated run card.
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True, help="new directory")
    p.add_argument("--seconds", type=float, default=180, help="time per model phase")
    p.add_argument("--snapshot", help="exact identifier verified by the operator's model client")
    p.add_argument("client", nargs=argparse.REMAINDER, help="-- followed by trusted client argv")
    a = p.parse_args()
    client = a.client[1:] if a.client[:1] == ["--"] else a.client
    if bool(client) != bool(a.snapshot):
        p.error("--snapshot and a model client must be supplied together")
    r = probe(a.output, client, a.snapshot, a.seconds)
    return 0 if r["wallPassed"] and (not client or r["tokenPassed"]) else 1


if __name__ == "__main__":
    sys.exit(main())
