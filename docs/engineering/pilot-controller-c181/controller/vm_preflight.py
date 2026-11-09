"""Operator-only metering and deadline canaries through a disposable QEMU worker."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import select
import subprocess
import sys
import tempfile
import time

from gate import Gate, Stopped


class Guest:
    def __init__(self, args, directory, label, sockets):
        self.args = args
        self.disk = directory / (label + ".raw")
        subprocess.run(["cp","--reflink=auto","--sparse=always",args.seed_disk,self.disk], check=True)
        self.sock = Path(sockets) / (label + ".sock")
        ready = directory / (label + "-ready.json")
        self.base = [sys.executable, "-B", str(args.guest)]
        self.log = (directory / (label + "-vm.log")).open("xb")
        server = [*self.base, "serve", "--qroot", args.qroot, "--image", args.image,
                  "--work-disk", self.disk, "--socket", self.sock, "--ready-file", ready,
                  "--memory", str(getattr(args, "memory", 512)), "--boot-timeout", str(args.boot_seconds)]
        tool_disk = getattr(args, "tool_disk", None)
        if tool_disk is not None:
            server.extend(["--tool-disk", tool_disk])
        self.proc = subprocess.Popen(server,
                                    stdout=self.log, stderr=self.log, start_new_session=True)
        self.pidfds = {"server": os.pidfd_open(self.proc.pid)}
        self.teardown = None
        deadline = time.monotonic() + args.boot_seconds
        while self.proc.poll() is None and not ready.is_file() and time.monotonic() < deadline:
            time.sleep(.1)
        if not ready.is_file() or self.proc.poll() is not None:
            self.stop()
            raise RuntimeError("guest failed to become ready")
        self.ready = json.loads(ready.read_text())
        self.pidfds["qemu"] = os.pidfd_open(self.ready["qemuPid"])
        if os.getpgid(self.ready["qemuPid"]) != self.proc.pid:
            self.stop()
            raise RuntimeError("guest outside controller process group")

    def cmd(self, script, timeout=90):
        return [*self.base, "call", "--socket", str(self.sock), "--timeout", str(timeout), "--", script]

    def stop(self):
        if self.teardown is not None:
            return self.teardown
        pgid = self.proc.pid
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self.proc.wait(timeout=8)
        self.log.close()
        observed = {}
        for name, fd in self.pidfds.items():
            p = select.poll()
            p.register(fd, select.POLLIN)
            observed[name] = bool(p.poll(5000))
        if not all(observed.values()):
            raise RuntimeError("worker termination not confirmed by pidfd")
        for fd in self.pidfds.values():
            os.close(fd)
        self.teardown = {"processGroup": pgid, "serverExit": self.proc.returncode, "pidfdExited": observed}
        return self.teardown


def recovered_copy(disk):
    """Preserve the stopped VM media and replay its ext4 journal on a separate copy."""
    copy = disk.with_suffix(".journal-replay.raw")
    if copy.exists():
        raise FileExistsError(copy)
    subprocess.run(["cp", "--reflink=auto", "--sparse=always", disk, copy], check=True)
    repair = subprocess.run(["e2fsck", "-y", "-E", "journal_only", str(copy)],
                            capture_output=True, text=True, timeout=120)
    if repair.returncode not in (0, 1):
        raise RuntimeError("ext4 journal replay failed with exit " + str(repair.returncode))
    copy.with_suffix(".log").write_text(repair.stdout + repair.stderr)
    return copy


def marker(disk, name):
    observed = subprocess.run(["debugfs", "-R", "stat /" + name, str(disk)],
                              capture_output=True, text=True, timeout=10, check=True)
    text = observed.stdout + observed.stderr
    if "Inode:" in text and "Type: regular" in text:
        return True
    if "File not found" in text:
        return False
    raise RuntimeError("unrecognized filesystem read result")


def check_refusal(gate, guest, args):
    attempts = [lambda: gate.infer(args.client, "Readiness", args.snapshot, 1),
                lambda: gate.tool(guest.cmd("touch /work/forbidden-after-cutoff"))]
    for op in attempts:
        try:
            op()
        except Stopped:
            continue
        raise RuntimeError("post-cutoff operation accepted")


def run(a):
    out = a.output.resolve()
    out.mkdir(mode=0o700, exist_ok=False, parents=True)
    result = {"scope": "combined harmless model and guest controls", "snapshot": a.snapshot,
              "wallPassed": False, "tokenPassed": False, "benchmarkAdmitted": False}
    with tempfile.TemporaryDirectory(prefix="ok-c181-") as sockets, (out / "events.jsonl").open("x") as trace:
        try:
            guest = Guest(a, out, "wall", sockets)
            try:
                gate = Gate(4.0, 4096, trace, "guest wall", on_stop=guest.stop, audit_model_stderr=True)
                try:
                    gate.tool(guest.cmd("echo started >/work/active-start; sync; sleep 7; "
                                        "echo late >/work/late-write; sync"))
                except Stopped:
                    pass
                if gate.stopped != "deadline":
                    raise RuntimeError("active guest command was not cut off at deadline")
                check_refusal(gate, guest, a)
                time.sleep(3.5)
                recovered = recovered_copy(guest.disk)
                observations = {"started": marker(recovered, "active-start"),
                                "lateWrite": marker(recovered, "late-write"),
                                "postCutoffWrite": marker(recovered, "forbidden-after-cutoff")}
                result["wallMarkers"] = observations
                if observations != {"started": True,"lateWrite": False,"postCutoffWrite":False}:
                    raise RuntimeError("incorrect guest disk markers")
                result["wallPassed"] = True
            finally:
                guest.stop()

            guest = Guest(a, out, "token", sockets)
            try:
                calibrate = Gate(a.seconds, 4096, trace, "calibration", on_stop=guest.stop, audit_model_stderr=True)
                tool_output = calibrate.tool(guest.cmd("printf 'READY-C181'"))
                if json.loads(tool_output).get("stdout") != "READY-C181":
                    raise RuntimeError("guest readiness output missing")
                prompt = ("A readiness tool returned the following bytes. Reply with one token.\n"
                          + tool_output.decode())
                _, baseline = calibrate.infer(a.client, prompt, a.snapshot, 1)
                if baseline["output"] != 1:
                    raise RuntimeError("one output token required")
                cap = 2 * baseline["charged"]
                gate = Gate(a.seconds, cap, trace, "guest aggregate", on_stop=guest.stop, audit_model_stderr=True)
                for _ in range(2):
                    _, actual = gate.infer(a.client, prompt, a.snapshot, 1)
                    if actual["charged"] != baseline["charged"]:
                        raise RuntimeError("charged count diverged between identical requests")
                if gate.stopped != "token budget exhausted":
                    raise RuntimeError("token cutoff failed")
                check_refusal(gate, guest, a)
                if marker(recovered_copy(guest.disk), "forbidden-after-cutoff"):
                    raise RuntimeError("post-cutoff marker exists")
                result.update(tokenPassed=True, calibration=baseline, cappedRequests=2,
                              aggregateLimit=cap, aggregateCharged=gate.charged,
                              guestToolOutputSha256=hashlib.sha256(tool_output).hexdigest())
            finally:
                guest.stop()
        except (OSError, RuntimeError, ValueError, Stopped, subprocess.SubprocessError) as exc:
            result["failure"] = str(exc)
    result["traceSha256"] = hashlib.sha256((out / "events.jsonl").read_bytes()).hexdigest()
    (out / "result.json").write_text(json.dumps(result,indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["wallPassed"] and result["tokenPassed"] else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ["guest", "qroot", "image", "seed-disk", "output"]:
        p.add_argument("--"+flag,type=Path,required=True)
    p.add_argument("--snapshot", required=True)
    p.add_argument("--seconds", type=float, default=180)
    p.add_argument("--boot-seconds", type=float, default=180)
    p.add_argument("--memory", type=int, default=512)
    p.add_argument("--tool-disk", type=Path, help="immutable route tool image")
    p.add_argument("client", nargs=argparse.REMAINDER)
    args = p.parse_args()
    if args.client[:1] == ["--"]:
        args.client.pop(0)
    if not args.client:
        p.error("trusted model client argv required")
    sys.exit(run(args))
