"""Operator bridge for a public practice repair using the C181 serial-only QEMU guest."""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace


def encoded(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(encoded(obj) + b"\n")
    tmp.replace(path)


def parse(raw):
    message = raw.strip()
    if message.startswith("```"):
        lines = message.splitlines()
        if len(lines) < 3 or lines[-1] != "```" or lines[0] not in ("```", "```json", "```text"):
            raise ValueError("Use one JSON command or SUBMIT. Close each fence.")
        message = "\n".join(lines[1:-1]).strip()
    if message == "SUBMIT":
        return None
    try:
        item = json.loads(message)
    except ValueError:
        raise ValueError('Expected one JSON object {"command":"..."} or SUBMIT.') from None
    if type(item) != dict or set(item) != {"command"} or type(item["command"]) != str or not item["command"].strip() or "\x00" in item["command"]:
        raise ValueError('Supply one nonempty command string.')
    return item["command"]


def run(a):
    os.umask(0o077)
    out = a.out.resolve()
    out.mkdir(mode=0o700)
    kit = a.kit.resolve()
    sys.path.insert(0, str(kit / "operator/c181/controller"))
    from gate import Gate, Stopped
    from vm_preflight import Guest
    seed = out / "seed.raw"
    image = kit / "operator/c181/worker/vm/controller-guest.cpio.gz"
    disk = a.tool_disk.resolve()
    card = json.loads((kit / "evidence/c181/registered/execution-card.json").read_bytes())
    check = {"image": sha(image), "toolDisk": sha(disk)}
    if check["image"] != card["image"]["sha256"] or check["toolDisk"] != card["toolDisks"][a.role]["sha256"]:
        raise ValueError("Guest bootstrap or tool disk differs from C181")
    stage = a.stage.resolve(strict=True)
    paths = sorted(stage.rglob("*"))
    if any(p.is_symlink() or not(p.is_dir() or p.is_file()) for p in paths):
        raise ValueError("Only regular files and directories may be staged")
    stage_hashes = {p.relative_to(stage).as_posix(): sha(p) for p in paths if p.is_file()}
    initial = a.initial_text.read_bytes() if a.initial_text else b""
    if len(initial) >= a.bytes or a.actions < 1 or a.invalid < 1 or a.seconds <= 0:
        raise ValueError("Budgets must leave room for the practice")
    with seed.open("xb") as f:
        f.truncate(256 << 20)
    subprocess.run(["mke2fs", "-q", "-t", "ext4", "-F", "-d", stage, seed], check=True)
    cfg = SimpleNamespace(seed_disk=seed, guest=image.with_name("guest.py"), qroot=a.qroot.resolve(),
                          boot_seconds=180, memory=4200, image=image, tool_disk=disk)
    save(out/"configuration.json", dict(role=a.role, seconds=a.seconds, actions=a.actions, byteLimit=a.bytes,
        maxConsecutiveInvalid=a.invalid, startingPromptBytes=len(initial), startingPromptSha256=hashlib.sha256(initial).hexdigest(),
        seedSha256=sha(seed), bridgeSha256=sha(Path(__file__)), stageFiles=stage_hashes, **check))
    with tempfile.TemporaryDirectory(prefix="c182-worker-") as channel:
        guest = Guest(cfg, out, "worker", channel)
        reason = "operator interrupted"
        actions = bad = 0
        used = len(initial)
        gate = None
        try:
            with (out/"dispatch.jsonl").open("x") as dispatch, (out/"transcript.jsonl").open("xb") as log:
                # Gate is used only for active-operation deadline and group teardown. No model inference passes here.
                gate = Gate(a.seconds, 1, dispatch, "public guest commands", on_stop=guest.stop)
                save(out/"ready.json", {"ready":True, "utc":datetime.now(UTC).isoformat(), "bootId":guest.ready["bootId"]})
                while True:
                    if time.monotonic() >= gate.deadline:
                        reason = "wall deadline"
                        break
                    req = out/"request.json"
                    if not req.is_file():
                        time.sleep(.03)
                        continue
                    raw = req.read_text()
                    req.unlink()
                    count = len(raw.encode())
                    actions += 1
                    entry = {"turn":actions,"elapsed":time.monotonic()-gate.started,"raw":raw,"inputBytes":count}
                    close = None
                    if count > a.bytes - used:
                        response = {"status":"closed","reason":"visible byte limit"}
                        close = "visible byte limit"
                        entry["admittedInputBytes"] = 0
                    else:
                        used += count
                        entry["admittedInputBytes"] = count
                        try:
                            command = parse(raw)
                        except ValueError as e:
                            bad += 1
                            response = {"status":"rejected","message":str(e)}
                            if bad >= a.invalid:
                                close = "consecutive invalid actions"
                        else:
                            bad = 0
                            if command is None:
                                response = {"status":"submitted"}
                                close = "submitted"
                            else:
                                try:
                                    tool = json.loads(gate.tool(guest.cmd(command, timeout=min(3600,a.seconds))))
                                    response = {"status":"tool","result":tool}
                                except Stopped as e:
                                    close = "wall deadline" if gate.stopped=="deadline" else str(e)
                                    response = {"status":"closed","reason":close}
                    payload = encoded(response)
                    if close == "visible byte limit" or len(payload)>a.bytes-used:
                        entry["withheldResponseSha256"] = hashlib.sha256(payload).hexdigest()
                        entry["withheldResponseBytes"] = len(payload)
                        response = {"status":"closed","reason":"visible byte limit"}
                        fn = 0
                        close = "visible byte limit"
                    else:
                        fn = len(payload)
                    used += fn
                    if close is None and (actions >= a.actions or used >= a.bytes):
                        close = "action limit" if actions >= a.actions else "visible byte limit"
                    entry.update(response=response,visibleOutputBytes=fn,usedBytes=used,stopAfter=close)
                    log.write(encoded(entry)+b"\n")
                    log.flush()
                    os.fsync(log.fileno())
                    save(out/"reply.json",response)
                    if close:
                        reason = close
                        break
        finally:
            teardown = guest.stop()
            result = {"reason":reason,"acceptedVisibleBytes":used,"actions":actions,"pidfdTeardown":teardown,
                      "wallSeconds":time.monotonic()-gate.started if gate else None, "actualModelTokens":None,
                      "wholeProviderContextObserved":False}
            if (out/"transcript.jsonl").exists():
                result["transcriptSha256"] = sha(out/"transcript.jsonl")
            result["finalDiskSha256"] = sha(guest.disk)
            if reason == "submitted":
                collect = kit / "operator/c181/pilot/collect.py"
                result["collection"] = json.loads(subprocess.check_output([sys.executable,"-IB",collect,guest.disk,out/"submission"]))
            save(out/"finish.json",result)


def submit(a):
    out=a.out.resolve()
    if (out/"finish.json").exists():
        print((out/"finish.json").read_text().strip())
        return
    if not (out/"ready.json").exists() or (out/"reply.json").exists():
        raise ValueError("Wait for readiness and collect each preceding reply")
    raw=sys.stdin.buffer.read(131073)
    if len(raw)>131072:
        raise ValueError("Raw reply exceeds transport size")
    raw.decode("utf-8")
    tmp=out/"request.pending"
    with tmp.open("xb") as f:
        f.write(raw)
    os.link(tmp,out/"request.json"); tmp.unlink()
    deadline=time.monotonic()+json.loads((out/"configuration.json").read_bytes())["seconds"]+45
    while not (out/"reply.json").exists():
        if (out/"finish.json").exists():
            print((out/"finish.json").read_text().strip())
            return
        if time.monotonic() > deadline:
            raise TimeoutError("Operator bridge did not return")
        time.sleep(.03)
    print((out/"reply.json").read_text().strip())
    (out/"reply.json").unlink()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="op",required=True)
    server=sub.add_parser("serve")
    for name in ["kit","qroot","tool-disk","stage","out"]:
        server.add_argument("--"+name,required=True,type=Path)
    server.add_argument("--role",choices=["ontokin","blender"],required=True)
    server.add_argument("--seconds",type=float,required=True)
    server.add_argument("--actions",type=int,required=True)
    server.add_argument("--bytes",type=int,required=True)
    server.add_argument("--invalid",type=int,default=3)
    server.add_argument("--initial-text",type=Path)
    send=sub.add_parser("action")
    send.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.op=="serve":
        signal.signal(signal.SIGTERM,lambda *_: sys.exit("Operator terminated controller"))
        run(args)
    else:
        submit(args)
