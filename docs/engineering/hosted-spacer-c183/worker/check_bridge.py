"""Exercise the public bridge on harmless commands. Run with the same frozen worker disks."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

p=argparse.ArgumentParser(description=__doc__)
for field in ("kit","qroot","common","blender","out"):
    p.add_argument("--"+field,type=Path,required=True)
args=p.parse_args()
out=args.out.resolve()
out.mkdir(mode=0o700)
stage=out/"blank"
stage.mkdir()
(stage/"submission").mkdir()
bridge=Path(__file__).with_name("public_worker.py").resolve()
sys.path.insert(0,str(args.kit.resolve()/"operator/c181/controller"))
from vm_preflight import marker,recovered_copy
records=[]
def check(name,role,seconds,actions,cap,raw_inputs,expected,wall=False):
    run=out/name
    proc=subprocess.Popen([sys.executable,"-B",bridge,"serve","--kit",args.kit,"--qroot",args.qroot,
        "--role",role,"--tool-disk",args.common if role=="ontokin" else args.blender,"--stage",stage,
        "--out",run,"--seconds",str(seconds),"--actions",str(actions),"--bytes",str(cap)])
    def action(raw):
        return json.loads(subprocess.check_output([sys.executable,"-B",bridge,"action","--out",run],input=raw.encode(),timeout=seconds+60))
    try:
        until=time.monotonic()+210
        while not (run/"ready.json").exists():
            if proc.poll() is not None or time.monotonic()>until:
                raise RuntimeError("Canary guest did not start")
            time.sleep(.05)
        replies=[action(raw) for raw in raw_inputs]
        proc.wait(timeout=seconds+40)
        result=json.loads((run/"finish.json").read_bytes())
        assert result["reason"]==expected and all(result["pidfdTeardown"]["pidfdExited"].values())
        after=action('{"command":"touch /work/forbidden-after-cutoff"}')
        assert after["reason"]==expected and after["actions"]==len(raw_inputs)
        checked=recovered_copy(run/"worker.raw")
        marks={k:marker(checked,k) for k in ("active-start","late-write","forbidden-after-cutoff")}
        assert marks=={"active-start":wall,"late-write":False,"forbidden-after-cutoff":False}
        if expected=="submitted":
            assert (run/"submission/value.txt").read_text()=='spaces "quoted"\n'
            assert any(r.get("result",{}).get("exit")==1 for r in replies)
        records.append(dict(case=name,role=role,reason=expected,returned=[r["status"] for r in replies],markers=marks,
                            actions=result["actions"],acceptedVisibleBytes=result["acceptedVisibleBytes"],
                            serverAndQemuExited=True,postStopActionDenied=True))
        (out/"results.json").write_text(json.dumps(records,indent=2)+"\n")
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=45)

for role in ("ontokin","blender"):
    check(role+"-active",role,4,8,4096,[json.dumps({"command":"echo OK > active-start; sync; sleep 7; touch late-write; sync"})],"wall deadline",True)
    check(role+"-bytes",role,30,8,128,[json.dumps({"command":"printf 'REHEARSAL'"})],"visible byte limit")
check("malformed","ontokin",45,8,4096,['incomplete {','{"command":','```sh\ntouch failed'],'consecutive invalid actions')
check("retry-and-submit","blender",45,8,4096,[
 'Here is my proposed action.',json.dumps({"command":"false"}),json.dumps({"command":"""printf '%s\\n' 'spaces "quoted"' > submission/value.txt
cat submission/value.txt"""}),"```\nSUBMIT\n```"],"submitted")
check("idle-deadline","ontokin",1,8,4096,[],"wall deadline")
check("count","blender",30,1,4096,[json.dumps({"command":"true"})],"action limit")
