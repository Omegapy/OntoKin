"""Check one VM image with throwaway canaries, including recovery after host SIGKILL."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent


def sha(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--qroot", type=Path, required=True)
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--tool-disk", type=Path)
    p.add_argument("--memory", type=int, default=512)
    p.add_argument("--shape", choices=["core", "common", "blender"], required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    host_start = time.monotonic()
    ev = {"startedUtc": dt.datetime.now(dt.timezone.utc).isoformat(), "shape": args.shape, "operator": "C181 worker admission",
          "host": {"kernel": platform.release(), "arch": platform.machine(), "host": platform.node()},
          "imageSha256": sha(args.image), "probes": [], "workerPassed": False}
    if args.tool_disk:
        ev["toolDiskSha256"] = sha(args.tool_disk)
    with tempfile.TemporaryDirectory(prefix="c181-benign-") as tdir:
        t = Path(tdir)
        stage=t/"stage"
        stage.mkdir()
        markers = {}
        for name in ["otherArm","evaluator","host"]:
            f = t / name / "canary.txt"
            f.parent.mkdir()
            f.write_text(secrets.token_hex(16))
            markers[name] = str(f.resolve())
        ev["positiveHostReadSha256"] = {name:sha(path) for name,path in markers.items()}
        assigned = stage/"assigned.txt"
        assigned.write_text(secrets.token_hex(16))
        html = stage/"index.html"
        html.write_text("<html><title>OntoKin loopback canary</title><p>"+secrets.token_hex(16)+"</p></html>\n")
        marker = secrets.token_hex(12)
        (stage/"request.json").write_text(json.dumps({"forbidden":markers, "assigned":sha(assigned), "html":sha(html), "marker":marker}))
        shutil.copyfile(HERE/"canary.py",stage/"canary.py")
        disk = t/"scratch.ext4"
        with disk.open("xb") as out:
            out.truncate(128 << 20)
        subprocess.run(["mke2fs","-q","-F","-t","ext4","-m","0","-d",str(stage),str(disk)],check=True)
        ev["pristineDiskSha256"] = sha(disk)
        channel = t/"ch"
        ready = t/"ready.json"
        proc = subprocess.Popen([sys.executable, str(HERE/"guest.py"),"serve","--qroot",str(args.qroot),"--image",str(args.image),
                                 "--socket",str(channel),"--ready-file",str(ready),"--work-disk",str(disk),"--memory",str(args.memory),
                                 *(["--tool-disk",str(args.tool_disk)] if args.tool_disk else [])],
                                start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic()+250
            while not ready.exists():
                if proc.poll() is not None:
                    raise RuntimeError(proc.stderr.read()[-4000:])
                if time.monotonic()>deadline: raise TimeoutError("Boot not observed")
                time.sleep(0.15)
            ev["boot"] = json.loads(ready.read_text())
            ev["bootElapsedSeconds"] = round(time.monotonic()-host_start,3)
            cmds=[("isolation","/usr/bin/python3.12 -IB /work/canary.py",35),("nonzero","echo ordinary-output; echo deliberate-error >&2; exit 22",8)]
            if args.shape!="core":
                cmds.append(("native",f"/opt/ontokin-native/probe.sh {args.shape}",240))
            for kind,cmd,limit in cmds:
                start=time.monotonic()
                resp = subprocess.run([sys.executable,str(HERE/"guest.py"),"call","--socket",str(channel),"--timeout",str(limit),"--",cmd],
                                      timeout=limit+30, capture_output=True,text=True)
                v={"kind":kind,"command":cmd,"transportExit":resp.returncode,"elapsedSeconds":round(time.monotonic()-start,3)}
                ev["probes"].append(v)
                if resp.returncode:
                    raise RuntimeError(resp.stderr[-4000:])
                v["receipt"]=json.loads(resp.stdout)
                r=v["receipt"]
                if kind=="isolation":
                    geo=json.loads(r["stdout"])
                    mounted = args.shape=="core" or geo["checks"].get("nativeDiskReadOnly",{}).get("pass") is True
                    v["pass"]=r["exit"]==0 and geo["pass"] and mounted
                elif kind=="nonzero":
                    v["pass"]=r["exit"]==22 and r["stdout"]=="ordinary-output\n" and r["stderr"]=="deliberate-error\n"
                else:
                    marked=[json.loads(x[len("ONTOKIN_NATIVE "):]) for x in r["stdout"].splitlines() if x.startswith("ONTOKIN_NATIVE ")]
                    v["pass"]=r["exit"]==0 and len(marked)==1 and marked[0].get("passed") is True and marked[0].get("toolset")==args.shape
        except Exception as exc:
            ev["failure"]=str(exc)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGKILL)
            proc.wait(timeout=8)
            ev["serverExitAfterStop"]=proc.returncode
            ev["bootLog"]=ready.with_suffix(".boot.log").read_text(errors="replace")[-4000:]
        # Do not change the captured raw image. A committed ext4 journal can contain
        # entries not yet checkpointed into the main filesystem after a hard stop.
        rawread=subprocess.run(["debugfs","-R","cat /persisted.txt",str(disk)],capture_output=True,text=True)
        original=sha(disk)
        recovered=t/"journal-replay.ext4"
        shutil.copyfile(disk,recovered)
        journal=subprocess.run(["e2fsck","-y","-E","journal_only",str(recovered)],capture_output=True,text=True,timeout=30)
        res=subprocess.run(["debugfs","-R","cat /persisted.txt",str(recovered)],capture_output=True,text=True)
        ev["afterHardStop"]={"originalDiskSha256":original, "originalPreserved":sha(disk)==original,
                             "preReplayReadMatched":rawread.stdout==marker, "journalReplayExit":journal.returncode,
                             "journalReplayLog":(journal.stdout+journal.stderr)[-1600:], "recovered":res.stdout==marker and journal.returncode in (0,1),
                             "expectedMarkerSha256":hashlib.sha256(marker.encode()).hexdigest(),
                             "actualMarkerSha256":hashlib.sha256(res.stdout.encode()).hexdigest()}
        ev["workerPassed"]="failure" not in ev and all(v.get("pass") for v in ev["probes"]) and ev["afterHardStop"]["recovered"]
    ev["elapsedSeconds"]=round(time.monotonic()-host_start,3)
    ev["finishedUtc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    with args.output.open("x") as f:
        json.dump(ev,f,indent=2);f.write("\n")
    return 0 if ev["workerPassed"] else 1


if __name__=="__main__":
    sys.exit(main())
