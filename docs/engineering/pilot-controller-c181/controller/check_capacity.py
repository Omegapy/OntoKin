"""Exercise pre-inference capacity refusals on the supplied trusted local client."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from gate import Gate, Stopped


def run(directory, snapshot, client):
    directory.mkdir(mode=0o700, exist_ok=False, parents=True)
    results = {}
    cases = [("remaining token allowance insufficient", 1, "Readiness probe."),
             ("context window exhausted", 200000, " red" * 32000)]
    with (directory / "events.jsonl").open("x") as trace:
        for reason, limit, prompt in cases:
            gate = Gate(120, limit, trace, reason, audit_model_stderr=True)
            try:
                gate.infer(client, prompt, snapshot, 1)
            except Stopped:
                pass
            if gate.stopped != reason or gate.charged != 0:
                raise RuntimeError("unexpected result in " + reason)
            for kind in ("model", "tool"):
                try:
                    gate.invoke(kind, [sys.executable, "-I", "-c", "raise SystemExit(123)"])
                except Stopped as exc:
                    if str(exc) != reason:
                        raise
                else:
                    raise RuntimeError("post-refusal dispatch")
            results[reason] = {"knownCharged":gate.charged, "bothDispatchesDenied":True}
    results["traceSha256"] = hashlib.sha256((directory / "events.jsonl").read_bytes()).hexdigest()
    (directory / "result.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("client", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.client[1:] if args.client[:1] == ["--"] else args.client
    if not argv:
        parser.error("trusted local client required")
    run(args.output, args.snapshot, argv)
