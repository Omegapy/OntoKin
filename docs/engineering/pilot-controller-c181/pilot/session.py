"""Run one registered rotary arm, with a fresh disk and the same budget and transport used in qualification."""
import argparse
import hashlib
import json
import math
import signal
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace

from agent_loop import run
from gate import Gate, Stopped
from vm_preflight import Guest


def digest(path):
    with open(path, "rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify(item):
    if not item.get("sha256") or digest(item["path"]) != item["sha256"]:
        raise ValueError("Registered file changed: " + item["path"])


def trial(cardfile, expected, route, records):
    if digest(cardfile) != expected:
        raise ValueError("Execution card differs from its preregistered digest")
    c = json.loads(cardfile.read_bytes())
    if c.get("state") != "admitted" or c.get("order") != ["blender", "ontokin"] or c.get("perArm") != {"wallSeconds":3600,"tokens":60000}:
        raise ValueError("An admitted card with the frozen order and limits is required")
    if set(c["checks"]) != {"worker", "meter", "combined", "nativeBlender", "nativeOntokin", "agentSmoke"}:
        raise ValueError("Missing admission receipts")
    for rec in c["checks"].values():
        if rec.get("passed") is not True:
            raise ValueError("Failed admission check")
        verify(rec)
    for rec in [*c["binaries"],c["image"],c["toolDisks"][route],c["startDisks"][route]]:
        verify(rec)
    records.mkdir(exist_ok=True, mode=0o700)
    if route == "ontokin":
        previous = json.loads((records / "blender" / "finish.json").read_text())
        if previous["cardSha256"] != expected:
            raise ValueError("Preceding arm must be closed under this card")
    arm = records / route
    arm.mkdir(mode=0o700)
    cfg = SimpleNamespace(seed_disk=c["startDisks"][route]["path"],guest=c["guest"],qroot=c["qroot"],
                          boot_seconds=c["bootSeconds"],memory=c["memoryMiB"],image=c["image"]["path"],tool_disk=c["toolDisks"][route]["path"])
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="ontokin-arm-") as channel:
        worker = Guest(cfg, arm, "worker", channel)
        try:
            with (arm / "calls.jsonl").open("x") as trace:
                gate = Gate(3600,60000,trace,route,on_stop=worker.stop,audit_model_stderr=True)
                def guest_tool(g, command):
                    secs = max(1,min(3600,math.ceil(g.deadline - time.monotonic())))
                    return json.loads(g.tool(worker.cmd(command, timeout=secs)))
                final = None
                try:
                    final = run(gate,c["modelClient"],c["modelSnapshot"],guest_tool,gate.log)
                    status = "participant ended session"
                except Stopped as exc:
                    status = str(exc)
                except Exception as exc:
                    gate.log("controllerError", errorType=type(exc).__name__, message=str(exc))
                    raise
                finally:
                    gate.log("workerClosed", outcome=worker.stop())
                result = dict(route=route,cardSha256=expected,status=status,setupSeconds=gate.started-started,
                              elapsedSeconds=time.monotonic()-gate.started,knownCharged=gate.charged,
                              finalResponse=final,traceSha256=digest(arm/"calls.jsonl"),
                              finalDiskSha256=digest(worker.disk))
                (arm/"finish.json").write_text(json.dumps(result,indent=2)+"\n")
                print(json.dumps(result))
        finally:
            worker.stop()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("card",type=Path)
    p.add_argument("card_sha256")
    p.add_argument("route",choices=["blender","ontokin"])
    p.add_argument("records",type=Path,help="New private directory, reused for the second arm")
    a=p.parse_args()
    def terminate(signum, frame):
        raise KeyboardInterrupt("controller termination requested")
    signal.signal(signal.SIGTERM, terminate)
    trial(a.card,a.card_sha256,a.route,a.records.resolve())
