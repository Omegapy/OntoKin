"""Diagnose attempt001 using only selected existing Python image bytes."""
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
from datetime import datetime, timezone

base=Path('/workspace/scratch/e33f906d0e8e/h0_work')
source=Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3').resolve(strict=True)
raw=source.read_bytes()
info=source.stat()
phoff=struct.unpack_from('<Q',raw,32)[0]
phentsize, phnum=struct.unpack_from('<HH',raw,54)
segments=[]
dynamic=[]
for n in range(phnum):
    values=struct.unpack_from('<IIQQQQQQ',raw,phoff+n*phentsize)
    names=['kind','flags','file_offset','virtual_address','physical_address','file_size','memory_size','alignment']
    row=dict(zip(names,values))
    segments.append(row)
    if row['kind']==2:
        for pos in range(row['file_offset'],row['file_offset']+row['file_size'],16):
            tag,value=struct.unpack_from('<qQ',raw,pos)
            dynamic.append({'file_offset':pos,'tag':tag,'value':value})
            if tag==0: break
snapshot=base/'selected-python.bin'
with snapshot.open('xb') as stream:
    stream.write(raw)
    stream.flush()
    os.fsync(stream.fileno())
os.chmod(snapshot,0o600)
out={'schema':'ontokin.c271.p09-python-elf-diagnostic/1','observed_at_utc':datetime.now(timezone.utc).isoformat(),
     'source':{'path':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw),'mode':oct(stat.S_IMODE(info.st_mode))},
     'elf_program_segments':segments,'elf_dynamic_entries':dynamic,
     'scope':'Read-only ELF bytes; no production module import/invocation or Node/ldd/preparer calls',
     'prior_attempt':'python-static-001.stderr.txt','snapshot':str(snapshot)}
with (base/'PYTHON-ELF-DIAGNOSTIC-002.json').open('x') as stream:
    json.dump(out,stream,indent=2,sort_keys=True); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
print(json.dumps(out,sort_keys=True))
