#!/usr/bin/env python3
"""Validate the actual published C044 core; documentation/metadata only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--root",type=Path,required=True)
p.add_argument("--publication",type=Path,required=True)
p.add_argument("--parent-tree",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
publication=json.loads((a.publication/"core-publication.json").read_bytes())
core_tree=json.loads((a.publication/"core-tree.json").read_bytes())
parent_tree=json.loads(a.parent_tree.read_bytes())
expected=publication["commit"]
expected_tree=publication["tree"]
start=datetime.now(timezone.utc).isoformat()
def sha(b):
    return hashlib.sha256(b).hexdigest()
def git(*args):
    return subprocess.check_output(["git","-C",str(a.root),*args]).decode().strip()
def save(name,data):
    (a.output/name).write_text(json.dumps(data,indent=2)+"\n")
def digest(p):
    b=p.read_bytes()
    return {"path":p.name,"bytes":len(b),"sha256":sha(b)}
def inventory():
    assert git("rev-parse","HEAD")==expected
    assert git("rev-parse","HEAD^{tree}")==expected_tree
    assert git("status","--porcelain=v1","--untracked-files=all")==""
    rows=[]
    for row in subprocess.check_output(["git","-C",str(a.root),"ls-files","-s","-z"]).decode().split("\0"):
        if not row:continue
        header,path=row.split("\t",1);mode,blob,stage=header.split()
        assert stage=="0"
        f=a.root/path
        assert f.is_file() and not f.is_symlink(),path
        b=f.read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
        actual_mode="100755" if f.stat().st_mode & 0o111 else "100644"
        assert actual==blob and actual_mode==mode,path
        rows.append({"path":path,"bytes":len(b),"mode":mode,"git_blob":blob,"sha256":sha(b)})
    physical={str(p.relative_to(a.root)) for p in a.root.rglob("*") if p.is_file() and str(p.relative_to(a.root))!=".git"}
    assert physical=={r["path"] for r in rows}
    return {"source_commit":expected,"source_tree":expected_tree,"files":rows,"file_count":len(rows),"total_bytes":sum(r["bytes"] for r in rows)}
shutil.copyfile(__file__,a.output/"executed-validation-driver.py")
for name in ["core-publication.json","core-commit.json","core-tree.json","core-new-files.json","core.commit","core-identity.stdout","core-identity.stderr"]:
    shutil.copyfile(a.publication/name,a.output/name)
save("start.json",{"started_utc":start,"source_commit":expected,"source_tree":expected_tree,"cwd":str(a.root),"command":[sys.executable,*sys.argv],"environment":{"python":sys.version,"executable":sys.executable,"executable_sha256":sha(Path(sys.executable).read_bytes()),"platform":platform.platform()},"scope":"metadata/input verification and unchanged documentation checker only; no product imports or requests"})
try:
    before=inventory();save("inputs-before.json",before)
    own={r["path"]:r for r in before["files"]}
    remote={x["path"]:x for x in core_tree["tree"] if x["type"]=="blob"}
    parents={x["path"]:x for x in parent_tree["tree"] if x["type"]=="blob"}
    assert len(parents)==2265 and len(remote)==len(own)==2282 and not core_tree["truncated"]
    assert set(remote)==set(own)
    for path,r in remote.items():
        q=own[path]
        assert (r["sha"],r["mode"],r["size"])==(q["git_blob"],q["mode"],q["bytes"]),path
    for path,r in parents.items():
        assert remote[path]["sha"]==r["sha"] and remote[path]["mode"]==r["mode"] and remote[path]["size"]==r["size"],path
    added=sorted(set(remote)-set(parents))
    assert len(added)==17 and all("/checkpoint-044-" in x or x.endswith("/HANDOFF-044.md") for x in added)
    static={"status":"passed","core_commit":expected,"core_tree":expected_tree,"all2282_remote_blob_size_modes_match_physical_files":True,"all2265_parent_files_preserved":True,"new_files":added,"runtime_fixtures_caps_workflows_shared_status_unchanged":True,"no_product_import_or_execution":True}
    save("static-audit.json",static)
    command=[sys.executable,"docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"]
    ds=datetime.now(timezone.utc).isoformat();clock=time.monotonic()
    result=subprocess.run(command,cwd=a.root,capture_output=True,timeout=120)
    elapsed=time.monotonic()-clock;de=datetime.now(timezone.utc).isoformat()
    (a.output/"documentation-check.stdout").write_bytes(result.stdout)
    (a.output/"documentation-check.stderr").write_bytes(result.stderr)
    doc=json.loads(result.stdout)
    save("documentation-command.json",{"command":command,"cwd":str(a.root),"started_utc":ds,"finished_utc":de,"elapsed_seconds":elapsed,"exit_code":result.returncode,"stdout":digest(a.output/"documentation-check.stdout"),"stderr":digest(a.output/"documentation-check.stderr")})
    after=inventory();save("inputs-after.json",after)
    assert before==after
    assert result.returncode==0 and doc["status"]=="passed" and not doc["failures"]
    assert doc["sources_verified"]==29 and doc["sections_verified"]==233
    summary={"status":"passed","source_commit":expected,"source_tree":expected_tree,"started_utc":start,"finished_utc":datetime.now(timezone.utc).isoformat(),"source_file_count":before["file_count"],"source_bytes":before["total_bytes"],"complete_input_inventories_identical":True,"all_parent_files_preserved":True,"new_files":len(added),"documentation":{"exit_code":result.returncode,"sources_verified":doc["sources_verified"],"sections_verified":doc["sections_verified"],"links":doc["links"],"failures":doc["failures"]},"product_requests":0,"runtime_tests":0,"release_acceptance":False}
except Exception as e:
    summary={"status":"failed","source_commit":expected,"source_tree":expected_tree,"started_utc":start,"finished_utc":datetime.now(timezone.utc).isoformat(),"error_type":type(e).__name__,"error":str(e),"product_requests":0,"release_acceptance":False}
save("receipt.json",summary)
print(json.dumps(summary))
sys.exit(0 if summary["status"]=="passed" else 1)
