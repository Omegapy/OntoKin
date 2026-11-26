"""Director's independent observation: killpg(pgid, 0) on Darwin for a zombie-only group."""
import os, signal, sys, time, platform, json
rows = []
def probe(label, pgid):
    try:
        os.killpg(pgid, 0); rows.append((label, "0"))
    except OSError as e:
        rows.append((label, f"{type(e).__name__} errno={e.errno}"))
# Case 1: direct child in its own group, exited, unreaped (zombie of this process).
pid = os.fork()
if pid == 0:
    os.setsid(); os._exit(0)
time.sleep(0.3)
probe("case1 direct child exited, not reaped", pid)
os.waitpid(pid, 0)
probe("case1 after waitpid", pid)
# Case 2: child starts a grandchild in the same group; child exits and is reaped;
# grandchild is killed and becomes an orphan (re-parented), briefly a zombie.
r, w = os.pipe()
pid = os.fork()
if pid == 0:
    os.setsid()
    g = os.fork()
    if g == 0:
        os.close(r); os.write(w, b"x"); time.sleep(30); os._exit(0)
    os._exit(0)
os.close(w); os.read(r, 1)
os.waitpid(pid, 0)
probe("case2 grandchild alive, child reaped", pid)
os.killpg(pid, signal.SIGKILL)
seen = []
t0 = time.monotonic()
while time.monotonic() - t0 < 2.0:
    try:
        os.killpg(pid, 0); seen.append("0")
    except PermissionError:
        seen.append("EPERM")
    except ProcessLookupError:
        seen.append("ESRCH"); break
    time.sleep(0.001)
from itertools import groupby
rows.append(("case2 after SIGKILL, polling 1 ms (run-length)", [(k, len(list(g))) for k, g in groupby(seen)]))
rows.append(("case2 elapsed_ms_to_last_poll", round((time.monotonic()-t0)*1000, 1)))
print(json.dumps({"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine(), "rows": rows}, indent=1))
