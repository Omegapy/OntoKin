"""Rebuild one reviewed editable spacer submission in a new C181 QEMU worker."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

p=argparse.ArgumentParser(description=__doc__)
for arg in ("kit","qroot","tool-disk","stage-template","source","delivered","out"):
    p.add_argument("--"+arg,type=Path,required=True)
p.add_argument("--role",choices=("blender","ontokin"),required=True)
p.add_argument("--same-source-uri", action="store_true", help="Stage the source at /work/submission/main.ok, as in the OntoKin participant export")
a=p.parse_args()
if a.same_source_uri and a.role!="ontokin":
    p.error("Source URI control applies to the OntoKin exporter.")
out=a.out.resolve()
out.mkdir()
stage=out/"stage"
stage.mkdir()
baseline_name="main.ok" if a.role=="ontokin" else "build_spacer.py"
original=(a.stage_template/"starter"/baseline_name).read_text()
candidate=a.source.read_text()
diff="".join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),"starter/"+baseline_name,"submitted/"+baseline_name))
(out/"source.diff").write_text(diff)
# The practice allows only the public dimensional substitution. Whitespace-only edits are immaterial here.
if a.role=="ontokin":
    old="40[mm], 12[mm], 20[mm]"
    new="50[mm], 12[mm], 24[mm]"
else:
    old="40, 12, 20"
    new="50, 12, 24"
if original.count(old)!=1 or original.replace(old,new).strip()!=candidate.strip():
    raise ValueError("Unexpected source difference; review it before attempting any rebuild.")
(stage/"submission").mkdir()
source=(stage/"submission" if a.same_source_uri else stage)/baseline_name
shutil.copyfile(a.source,source)
shutil.copyfile(a.stage_template/"measure_glb.py",stage/"measure_glb.py")
if a.role=="ontokin":
    shutil.copytree(a.stage_template/"job",stage/"job")
    guest_source="/work/"+source.relative_to(stage).as_posix()
    command=f"cd /work/job/checkout && /work/job/venv/bin/python -B -m ontokin export {guest_source} --no-helpers --fps 1 --output /work/submission/spacer.glb"
else:
    command="/opt/blender/blender -b -t 2 --factory-startup --python-exit-code 1 --python /work/build_spacer.py -- /work/submission"
assert not any(p.suffix.lower()==".glb" for p in stage.rglob("*"))
run=out/"run"
bridge=Path(__file__).resolve().with_name("public_worker.py")
ctl=[sys.executable,"-B",str(bridge)]
proc=subprocess.Popen([*ctl,"serve","--kit",a.kit,"--qroot",a.qroot,"--tool-disk",a.tool_disk,"--role",a.role,
        "--stage",stage,"--out",run,"--seconds","240","--bytes","65536","--actions","5"])
try:
    before=time.monotonic()+210
    while not (run/"ready.json").exists():
        if proc.poll() is not None or time.monotonic()>=before:
            raise RuntimeError("Failed to boot rebuild VM")
        time.sleep(.05)
    replies=[]
    for action in (json.dumps({"command":command}),json.dumps({"command":"python3.12 /work/measure_glb.py /work/submission/spacer.glb --expect-mm 50 12 24"}),"SUBMIT"):
        response=json.loads(subprocess.check_output([*ctl,"action","--out",run],input=action.encode(),timeout=245))
        if (response.get("status")=="tool" and response["result"]["exit"]!=0) or response.get("status") not in {"tool","submitted"}:
            raise RuntimeError(str(response))
        replies.append(response)
    proc.wait(timeout=30)
    readback=json.loads(replies[1]["result"]["stdout"])
    rebuilt=run/"submission/spacer.glb"
    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()
    cmp={"route":a.role,"cleanGuest":True,"glbsInStartingWorkspace":0,"diffReviewed":"Only the two registered dimension literals differ.",
         "sourceSha256":sha(source),"receivedGlbSha256":sha(a.delivered),"rebuiltGlbSha256":sha(rebuilt),
         "receivedBytes":a.delivered.stat().st_size,"rebuiltBytes":rebuilt.stat().st_size,
         "byteIdentical":rebuilt.read_bytes()==a.delivered.read_bytes(),"exportExit":replies[0]["result"]["exit"],
         "measurementExit":replies[1]["result"]["exit"],"measurement":readback}
    (out/"result.json").write_text(json.dumps(cmp,indent=2)+"\n")
    print(json.dumps(cmp))
finally:
    if proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=40)
