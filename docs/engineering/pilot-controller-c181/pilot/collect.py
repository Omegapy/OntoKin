"""Copy regular files from a stopped participant disk into a new directory without mounting it."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile


def read(disk, command):
    return subprocess.run(["debugfs", "-R", command, str(disk)], check=True, capture_output=True, timeout=60).stdout


def entries(disk, directory):
    rows = []
    for line in read(disk, "ls -p " + directory).decode().splitlines():
        if not line:
            continue
        match = re.fullmatch(r"/([0-9]+)/([0-7]+)/[0-9]+/[0-9]+/([^/]+)/([0-9]*)/", line)
        if not match:
            raise ValueError("Invalid filesystem listing")
        inode, mode, name, size = match.groups()
        if name in {".", ".."} or int(inode)==0:
            continue
        if not name.isprintable() or "\\" in name:
            raise ValueError("Unsupported entry name")
        rows.append((int(inode), int(mode, 8) & 0o170000, name, int(size or 0)))
    return rows


def collect(disk, output):
    output.mkdir(mode=0o700)
    pending = []
    for ino, kind, name, _ in entries(disk,"/"):
        if name=="submission" and kind==0o040000:
            pending.append((ino, output))
    visited=set()
    files=total=0
    excluded=[]
    while pending:
        ino, folder=pending.pop()
        if ino in visited or len(visited)>4096:
            raise ValueError("Unexpected directory cycle or size")
        visited.add(ino)
        for ino, kind, name, size in entries(disk, f"<{ino}>"):
            path=folder/name
            if kind==0o040000:
                path.mkdir(mode=0o700)
                pending.append((ino,path))
            elif kind==0o100000:
                total+=size
                files+=1
                if total>256*(1<<20) or files>8192:
                    raise ValueError("Submission exceeds source disk envelope")
                data=read(disk,f"cat <{ino}>")
                if len(data)!=size:
                    raise ValueError("File length mismatch")
                with path.open("xb") as f:
                    f.write(data)
            else:
                excluded.append(str(path.relative_to(output)))
    return dict(files=files, bytesCopied=total, excludedSpecialEntries=excluded)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("disk",type=Path);p.add_argument("output",type=Path)
    args=p.parse_args()
    with tempfile.TemporaryDirectory(dir=args.output.resolve().parent) as tmp:
        copy=Path(tmp)/'recovery.ext4'
        subprocess.run(['cp','--sparse=always','--reflink=auto',str(args.disk.resolve()),str(copy)],check=True)
        fsck=subprocess.run(['e2fsck','-pf',str(copy)],capture_output=True,text=True,timeout=120)
        if fsck.returncode not in {0,1,2,3}:
            raise ValueError('Cannot verify recovery copy: '+fsck.stdout+' '+fsck.stderr)
        print(json.dumps({**collect(copy,args.output),'recoveryExit':fsck.returncode,
                          'recoveryReport':fsck.stdout.strip()}))
