"""Trusted guest serial endpoint. No transport credentials are placed in the VM."""
import base64
import ctypes
import json
import os
import resource
import signal
import subprocess
import sys
import tempfile


def emit(obj):
    print("ONTOKIN_RPC " + json.dumps(obj, separators=(",", ":")), flush=True)


def restrict():
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
    if ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl NO_NEW_PRIVS")
    # Bound participant output stored in the disposable guest.
    resource.setrlimit(resource.RLIMIT_FSIZE, (512 << 20, 512 << 20))


def execute(req):
    # The caller supplies a command, never host-side shell expansion.
    command = req["command"]
    if not isinstance(command, str) or len(command.encode()) > 131072:
        raise ValueError("command exceeds transport limit")
    seconds = min(3600.0, max(0.1, float(req["timeout"])))
    env = {"PATH": "/opt/c181-python/bin:/opt/blender:/opt/chromium:/bin:/usr/bin", "HOME": "/work",
           "LD_LIBRARY_PATH": "/native/lib/x86_64-linux-gnu", "TMPDIR": "/tmp", "LANG": "C", "LC_ALL": "C"}
    with tempfile.TemporaryFile(dir="/tmp") as output, tempfile.TemporaryFile(dir="/tmp") as errors:
        proc = subprocess.Popen(["/bin/sh", "-c", command], cwd="/work", env=env, preexec_fn=restrict,
                                start_new_session=True, stdin=subprocess.DEVNULL, stdout=output, stderr=errors)
        timed_out = False
        try:
            proc.wait(seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        size = output.seek(0, 2)
        output.seek(0)
        first = output.read(65536)
        errsize = errors.seek(0, 2)
        errors.seek(0)
        errfirst = errors.read(65536)
    return {"exit": proc.returncode, "guestTimeout": timed_out, "stdoutBytes": size, "truncated": size > len(first),
            "stdoutBase64": base64.b64encode(first).decode("ascii"), "stderrBytes": errsize,
            "stderrBase64": base64.b64encode(errfirst).decode("ascii"), "stderrTruncated": errsize > len(errfirst)}


emit({"ready": True, "bootId": open("/proc/sys/kernel/random/boot_id").read().strip()})
for line in sys.stdin.buffer:
    req = {}
    try:
        req = json.loads(line)
        result = execute(req)
    except Exception as exc:
        result = {"error": type(exc).__name__ + ": " + str(exc)}
    emit({"id": req.get("id"), **result})
