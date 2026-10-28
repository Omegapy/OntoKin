#!/usr/bin/env python3
"""Attach an exact observed GitHub commit to the detached publication worktree."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--commit-json",type=Path,required=True)
p.add_argument("--root",type=Path,required=True)
p.add_argument("--expected-old",required=True)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args();c=json.loads(a.commit_json.read_bytes())
def git(*args,data=None):
    return subprocess.check_output(["git","-C",str(a.root),*args],input=data)
assert subprocess.run(["git","-C",str(a.root),"symbolic-ref","-q","HEAD"],capture_output=True).returncode != 0,"Publication HEAD must remain detached"
assert git("rev-parse","HEAD").decode().strip()==a.expected_old
assert git("write-tree").decode().strip()==c["tree"]["sha"]
assert not git("diff","--name-only")
def off(m):
    return ("-" if m<0 else "+")+f"{abs(m)//60:02d}{abs(m)%60:02d}"
offsets=list(dict.fromkeys(["+0000","-0600","-0700","-0000"]+[off(m) for m in range(-720,841,15)]))
def person(role,tz):
    x=c[role];seconds=int(datetime.fromisoformat(x["date"].replace("Z","+00:00")).timestamp())
    return f"{role} {x['name']} <{x['email']}> {seconds} {tz}\n"
prefix=f"tree {c['tree']['sha']}\n"+"".join(f"parent {x['sha']}\n" for x in c["parents"])
raw=None
for x in offsets:
    for y in offsets:
        for ending in ["","\n"]:
            b=(prefix+person("author",x)+person("committer",y)+"\n"+c["message"]+ending).encode()
            h=hashlib.sha1(b"commit "+str(len(b)).encode()+b"\0"+b).hexdigest()
            if h==c["sha"]:
                raw=b;chosen={"author_offset":x,"committer_offset":y,"message_final_newline":bool(ending)};break
        if raw is not None:break
    if raw is not None:break
assert raw is not None,"Exact commit bytes unavailable; refuse synthetic substitution"
assert git("hash-object","-t","commit","-w","--stdin",data=raw).decode().strip()==c["sha"]
git("update-ref","HEAD",c["sha"],a.expected_old)
assert git("rev-parse","HEAD^{tree}").decode().strip()==c["tree"]["sha"]
assert not git("status","--porcelain=v1","--untracked-files=all")
a.output.write_bytes(raw)
print(json.dumps({"commit":c["sha"],"tree":c["tree"]["sha"],"status":"passed","exact_raw_commit_verified":True,"reconstruction":chosen,"no_worktree_file_bytes_changed":True}))
