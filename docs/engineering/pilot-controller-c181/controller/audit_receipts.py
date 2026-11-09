"""Recount stored local-model token IDs and check the serial dispatch trace offline."""
import argparse
import json
from pathlib import Path


def audit(path, snapshot):
    phases, ids = {}, set()
    for number, line in enumerate(path.read_text().splitlines(), 1):
        row = json.loads(line)
        label, event = row["run"], row["event"]
        if event == "opened":
            if label in phases:
                raise ValueError(f"line {number} reopened a named phase")
            phases[label] = {"knownCharged": 0, "receipts": 0, "limit": row["tokens"],
                             "stopped": None, "refused": []}
            continue
        phase = phases[label]
        if event == "dispatch" and phase["stopped"]:
            raise ValueError(f"line {number} dispatched after stop")
        if event == "stopped":
            phase["stopped"] = row["reason"]
            if row["knownCharged"] != phase["knownCharged"]:
                raise ValueError(f"line {number} stop count mismatch")
        elif event == "refused":
            if row["reason"] != phase["stopped"]:
                raise ValueError(f"line {number} inconsistent refusal")
            phase["refused"].append(row["kind"])
        elif event == "usage":
            r, req = row["receipt"], row["request"]
            if (not r["requestId"] or r["requestId"] in ids or r["requestId"] != req["requestId"]
                    or r["snapshot"] != snapshot or r["snapshot"] != req["snapshot"]):
                raise ValueError(f"line {number} receipt identity mismatch")
            ids.add(r["requestId"])
            native, normalized = r["native"], row["normalized"]
            full, output = len(native["inputIds"]), len(native["generatedIds"])
            if (r["usage"] != dict(fullInput=full, cachedInput=0, output=output)
                    or normalized != dict(fullInput=full,cachedInput=0,uncachedInput=full,
                                          output=output,charged=full+output)
                    or full + output > req["remainingTokens"] or output > req["maxOutput"]):
                raise ValueError(f"line {number} token counts or per-request budget mismatch")
            phase["knownCharged"] += full + output
            phase["receipts"] += 1
            if phase["knownCharged"] != row["cumulative"] or phase["knownCharged"] > phase["limit"]:
                raise ValueError(f"line {number} aggregate count or budget mismatch")
    if not ids:
        raise ValueError("no live local-model receipts found")
    return phases


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("trace", type=Path)
    p.add_argument("--snapshot", required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.trace, a.snapshot), indent=2))
