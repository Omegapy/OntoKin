"""Host-only private transport to a single disposable QEMU worker."""
import argparse
import base64
import json
import os
from pathlib import Path
import secrets
import select
import subprocess
import sys
import time


class Guest:
    def __init__(self, root, image, disk, memory, log, tool_disk=None):
        root, image, disk = (Path(p).resolve(strict=True) for p in (root, image, disk))
        if "," in str(disk):
            raise ValueError("Use a dedicated raw disk with a path free of commas")
        kernel, = sorted((root / "boot").glob("vmlinuz-*"))
        self.argv = [str(root / "usr/bin/qemu-system-x86_64"), "-no-user-config", "-nodefaults", "-machine",
                     "pc,accel=tcg", "-cpu", "max", "-m", str(memory), "-smp", "2", "-L", str(root / "usr/share/qemu"),
                     "-bios", str(root / "usr/share/seabios/bios-256k.bin"), "-kernel", str(kernel), "-initrd", str(image),
                     "-append", "console=ttyS0 rdinit=/init panic=-1 loglevel=3", "-nic", "none", "-no-reboot", "-monitor",
                     "none", "-serial", "stdio", "-display", "none", "-drive",
                     f"file={disk},format=raw,if=virtio,cache=writethrough"]
        if tool_disk is not None:
            tool_disk = Path(tool_disk).resolve(strict=True)
            if "," in str(tool_disk):
                raise ValueError("Use a tool-disk path free of commas")
            self.argv.extend(["-drive", f"file={tool_disk},format=raw,if=virtio,readonly=on"])
        libs = root / "usr/lib/x86_64-linux-gnu"
        # No controller service credentials or host integration environment enters QEMU.
        env = {"PATH": "/usr/bin:/bin", "LANG": "C", "LD_LIBRARY_PATH": f"{libs}:{root / 'lib/x86_64-linux-gnu'}",
               "QEMU_MODULE_DIR": str(libs / "qemu")}
        self.log = log
        self.p = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  env=env, bufsize=0, close_fds=True)
        self.data = b""

    def read(self, seconds):
        stop = time.monotonic() + seconds
        while True:
            while b"\n" in self.data:
                line, self.data = self.data.split(b"\n", 1)
                if line.startswith(b"ONTOKIN_RPC "):
                    return json.loads(line[12:])
                self.log.write(line + b"\n")
                self.log.flush()
            left = stop - time.monotonic()
            if left <= 0 or not select.select([self.p.stdout], [], [], left)[0]:
                raise TimeoutError("Guest serial response deadline")
            chunk = os.read(self.p.stdout.fileno(), 65536)
            if not chunk:
                self.log.write(self.data)
                self.log.flush()
                raise RuntimeError("Guest serial stream closed")
            self.data += chunk
            if len(self.data) > 1024 * 1024:
                raise ValueError("Guest frame exceeds bound")

    def run(self, command, timeout):
        ident = secrets.token_hex(12)
        frame = (json.dumps({"id": ident, "command": command, "timeout": timeout}) + "\n").encode()
        offset = 0
        while offset < len(frame):
            offset += os.write(self.p.stdin.fileno(), frame[offset:])
        reply = self.read(timeout + 15)
        if reply.pop("id", None) != ident or "error" in reply:
            raise ValueError("Unmatched or invalid guest response: " + str(reply))
        for key in ["stdout", "stderr"]:
            reply[key] = base64.b64decode(reply.pop(key + "Base64"), validate=True).decode("utf-8", errors="replace")
        return reply

    def stop(self):
        if self.p.poll() is None:
            self.p.kill()
        self.p.wait()


def publish(path, obj):
    temp = path.with_name(path.name + ".tmp-" + secrets.token_hex(6))
    try:
        with temp.open("x") as out:
            json.dump(obj, out)
        os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_frame(path):
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Private frame exceeds bound")
    return json.loads(path.read_text())


def serve(args):
    # Controller starts serve in its own session. Its entire process group is disposable.
    if os.getpgrp() != os.getpid():
        raise ValueError("Launch serve in a private host session (start_new_session=True or setsid)")
    if (args.socket.parent.stat().st_mode & 0o077) or args.socket.parent.stat().st_uid != os.getuid():
        raise ValueError("Use an operator-owned socket directory with mode 0700")
    if args.ready_file.exists():
        raise ValueError("Use a new ready-file path")
    os.umask(0o077)
    with args.ready_file.with_suffix(".boot.log").open("xb") as bootlog:
        guest = Guest(args.qroot, args.image, args.work_disk, args.memory, bootlog, args.tool_disk)
        try:
            ready = guest.read(args.boot_timeout)
            if ready.get("ready") is not True:
                raise ValueError("Guest did not become ready")
            args.socket.mkdir(mode=0o700)
            ready.update({"serverPid": os.getpid(), "qemuPid": guest.p.pid, "processGroup": os.getpgrp(),
                          "qemuArgv": guest.argv})
            tmp = args.ready_file.with_suffix(".tmp")
            with tmp.open("x") as out:
                json.dump(ready, out)
            tmp.rename(args.ready_file)
            while True:
                incoming = args.socket / "request.json"
                if not incoming.exists():
                    if guest.p.poll() is not None:
                        raise RuntimeError("Worker exited")
                    time.sleep(0.03)
                    continue
                req = read_frame(incoming)
                if not isinstance(req.get("command"), str) or not (0 < req.get("timeout", 0) <= 3600):
                    raise ValueError("Invalid request to private transport")
                ident = req["id"]
                if len(ident) != 24 or any(c not in "0123456789abcdef" for c in ident):
                    raise ValueError("Invalid private request ID")
                reply = guest.run(req["command"], req["timeout"])
                incoming.unlink()
                publish(args.socket / (ident + ".json"), reply)
        finally:
            guest.stop()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_subparsers(dest="op", required=True)
    start = modes.add_parser("serve")
    for opt in ["qroot", "image", "work-disk", "socket", "ready-file"]:
        start.add_argument("--" + opt, type=Path, required=True)
    start.add_argument("--tool-disk", type=Path, help="Operator-built, immutable ext4 native tool volume")
    start.add_argument("--memory", type=int, default=512, help="Guest RAM in MiB")
    start.add_argument("--boot-timeout", type=float, default=240)
    call = modes.add_parser("call")
    call.add_argument("--socket", type=Path, required=True)
    call.add_argument("--timeout", type=float, required=True)
    call.add_argument("command")
    args = p.parse_args()
    if args.op == "serve":
        serve(args)
    else:
        ident = secrets.token_hex(12)
        inbox = args.socket / "request.json"
        outbox = args.socket / (ident + ".json")
        publish(inbox, {"command": args.command, "timeout": args.timeout, "id": ident})
        deadline = time.monotonic() + args.timeout + 20
        while not outbox.exists():
            if time.monotonic() >= deadline:
                raise TimeoutError("Private channel response deadline")
            time.sleep(0.03)
        print(json.dumps(read_frame(outbox), ensure_ascii=True))
        outbox.unlink()



if __name__ == "__main__":
    main()
