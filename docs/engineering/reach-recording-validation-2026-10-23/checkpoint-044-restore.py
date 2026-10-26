#!/usr/bin/env python3
"""Restore and verify C044 evidence; no archived code or product code is executed."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

def sha(b):
    return hashlib.sha256(b).hexdigest()
def safe_name(name):
    p=PurePosixPath(name)
    if not name or "\\" in name or p.is_absolute() or any(x in ("", ".", "..") for x in name.split("/")) or any(ord(c)<32 for c in name):
        raise ValueError("Unsafe evidence path: "+repr(name))
    return p
def restore(manifest_path, output):
    manifest=json.loads(manifest_path.read_bytes())
    parts=manifest["archive"]["parts"]
    if not parts or len({x["path"] for x in parts})!=len(parts):
        raise ValueError("Duplicate or empty archive parts")
    pieces=[]
    for row in parts:
        name=safe_name(row["path"])
        if len(name.parts)!=1:
            raise ValueError("Archive part must be beside manifest")
        p=manifest_path.parent/name.name
        if p.is_symlink():
            raise ValueError("Symlink archive part")
        b=p.read_bytes()
        if len(b)!=row["bytes"] or sha(b)!=row["sha256"]:
            raise ValueError("Archive part mismatch: "+str(p))
        pieces.append(b)
    joined=b"".join(pieces)
    archive=manifest["archive"]
    if len(joined)!=archive["bytes"] or sha(joined)!=archive["sha256"]:
        raise ValueError("Joined archive mismatch")
    expected={x["path"]:x for x in manifest["members"]}
    if len(expected)!=len(manifest["members"]):
        raise ValueError("Duplicate manifest member")
    verified=[]
    with zipfile.ZipFile(io.BytesIO(joined)) as z:
        infos=z.infolist()
        if len(infos)!=len({i.filename for i in infos}) or set(expected)!={i.filename for i in infos}:
            raise ValueError("ZIP member-set mismatch")
        bad=z.testzip()
        if bad is not None:
            raise ValueError("ZIP CRC failure: "+bad)
        for info in infos:
            name=safe_name(info.filename)
            mode=info.external_attr >> 16
            if info.is_dir() or stat.S_IFMT(mode) not in (0, stat.S_IFREG) or info.flag_bits & 1:
                raise ValueError("Nonregular or encrypted ZIP member: "+info.filename)
            row=expected[info.filename]
            b=z.read(info)
            if len(b)!=row["bytes"] or sha(b)!=row["sha256"]:
                raise ValueError("Member hash mismatch: "+info.filename)
            if stat.S_IMODE(mode)!=row["mode"]:
                raise ValueError("Member mode mismatch: "+info.filename)
            verified.append((name,row,b))
    if output is not None:
        if output.exists() or output.is_symlink():
            raise ValueError("Output must not already exist")
        output.mkdir(parents=True, exist_ok=False)
        for name,row,b in verified:
            p=output.joinpath(*name.parts)
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(b)
            os.chmod(p,row["mode"])
            os.utime(p,ns=(row["mtime_ns"],row["mtime_ns"]))
    result={"status":"passed","parts":len(parts),"archive_bytes":len(joined),"archive_sha256":sha(joined),"members":len(verified),"member_bytes":sum(len(x[2]) for x in verified),"crc_and_all_member_hashes_verified":True,"output":str(output) if output else None,"archived_code_executed":False,"product_requests":0}
    print(json.dumps(result))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,default=Path(__file__).resolve().with_name("checkpoint-044-evidence-manifest.json"))
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--output",type=Path)
    group.add_argument("--verify-only",action="store_true")
    args=p.parse_args()
    restore(args.manifest,args.output)
