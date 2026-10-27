#!/usr/bin/env python3
"""Run only documentation/metadata commands and preserve actual stable input identities."""
from pathlib import Path
import datetime, hashlib, json, platform, subprocess, sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE = "853c01589af790bc83bf52ed70b18dc87673873b"
TREE = "cadf049f90b45dbcf234199acb2e25a3f4c0eec8"

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def identity(path):
    data=path.read_bytes()
    return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(data),
            "sha256":hashlib.sha256(data).hexdigest(),
            "git_blob":hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()}

def main():
    label, command = sys.argv[1], sys.argv[2:]
    if not command or "/" in label or ".." in label:
        raise SystemExit("Provide a new simple attempt label and command")
    out=HERE/label
    out.mkdir(exist_ok=False)
    paths=[p for p in sorted(ROOT.rglob("*")) if p.is_file() and not p.is_relative_to(out)]
    before=[identity(p) for p in paths]
    (out/"input-manifest.json").write_text(json.dumps({"source_commit":BASE,"source_tree":TREE,
        "qualification":"Named stable files in a partial snapshot; not a complete product input closure.",
        "files":before},indent=2)+"\n")
    started=stamp()
    with (out/"stdout.txt").open("wb") as stdout,(out/"stderr.txt").open("wb") as stderr:
        result=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr)
    ended=stamp()
    changes=[]
    for p,old in zip(paths,before):
        if not p.is_file() or identity(p)!=old:
            changes.append(old["path"])
    info={"source_parent_commit":BASE,"source_parent_tree":TREE,"command":command,
          "cwd_policy":"repository snapshot root","started_utc":started,"ended_utc":ended,
          "interpreter":sys.version,"executable":sys.executable,"platform":platform.platform(),
          "exit_code":result.returncode,"stable_inputs":len(before),"changed_inputs":changes,
          "scope":"documentation/metadata only; no OntoKin import or numerical execution",
          "status":"passed" if result.returncode==0 and not changes else "failed"}
    for name in ("stdout.txt","stderr.txt"):
        data=(out/name).read_bytes()
        info[name]={"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    (out/"command.json").write_text(json.dumps(info,indent=2)+"\n")
    if not (out/"result.json").exists():
        try: parsed=json.loads((out/"stdout.txt").read_text())
        except (ValueError,UnicodeError):parsed={"status":info["status"],"exit_code":result.returncode}
        (out/"result.json").write_text(json.dumps(parsed,indent=2)+"\n")
    print(json.dumps(info,indent=2))
    return 0 if info["status"]=="passed" else 1

if __name__=="__main__":
    raise SystemExit(main())
