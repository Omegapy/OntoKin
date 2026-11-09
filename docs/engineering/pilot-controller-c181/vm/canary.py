"""Harmless participant-side controls only."""
import errno
import hashlib
import http.client
import http.server
import json
import os
import socket
import threading
from pathlib import Path


def read_denial(path):
    try:
        with open(path, "rb") as f:
            f.read(1)
    except OSError as e:
        return {"pass": e.errno in {errno.ENOENT, errno.EACCES, errno.EPERM}, "errno": e.errno}
    return {"pass": False, "reason": "Unexpected readable path"}


def loopback(expected):
    with http.server.HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler) as server:
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()
        client = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            client.request("GET", "/index.html")
            r = client.getresponse()
            got = hashlib.sha256(r.read()).hexdigest()
            return {"pass": r.status == 200 and got == expected, "bodySha256": got, "status": r.status}
        finally:
            client.close()
            t.join(5)


def external():
    interfaces = sorted(n for _, n in socket.if_nameindex())
    out = {"interfaces": interfaces, "probes": {}, "pass": False}
    if interfaces != ["lo"]:
        out["reason"] = "Expected only loopback; stopped before any attempted external connection"
        return out
    for family, addr in ((socket.AF_INET, "192.0.2.1"), (socket.AF_INET6, "2001:db8::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                err = s.connect_ex((addr, 9))
        except OSError as e:
            err = e.errno
        codes = {errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EPERM, errno.EACCES}
        if family == socket.AF_INET6:
            codes |= {errno.EAFNOSUPPORT, errno.EPROTONOSUPPORT}
        out["probes"][addr] = {"pass": err in codes, "errno": err}
    out["pass"] = all(c["pass"] for c in out["probes"].values())
    return out


req = json.loads(Path("request.json").read_text())
status = dict(l.split(":", 1) for l in Path("/proc/self/status").read_text().splitlines() if ":" in l)
checks = {"assigned": {"pass": hashlib.sha256(Path("assigned.txt").read_bytes()).hexdigest() == req["assigned"]},
          "loopback": loopback(req["html"]), "external": external(),
          "privileges": {"pass": os.getuid() == 65534 and int(status["CapEff"],16) == 0 and int(status["NoNewPrivs"]) == 1,
                         "uid": os.getuid(), "gid": os.getgid(), "capEff": status["CapEff"].strip(), "noNewPrivs": status["NoNewPrivs"].strip()}}
for label, path in req["forbidden"].items():
    checks[label] = read_denial(path)
    checks[label + "ViaInitRoot"] = read_denial("/proc/1/root" + path)
if Path("/native").is_mount():
    mount = next(l.split() for l in Path("/proc/self/mountinfo").read_text().splitlines() if l.split()[4] == "/native")
    options = mount[5].split(",")
    checks["nativeDiskReadOnly"] = {"pass": {"ro","nosuid","nodev"} <= set(options), "mountOptions": options}
    checks["nativeBlockDevice"] = read_denial("/dev/vdb")
for p in ("/dev/ttyS0","/dev/vda"):
    checks[p] = read_denial(p)
Path("persisted.txt").write_text(req["marker"])
checks["write"] = {"pass": Path("persisted.txt").read_text() == req["marker"]}
print(json.dumps({"pass": all(v["pass"] for v in checks.values()), "checks": checks}))
