"""Independently inspect one selected ELF image without executing project code.

Stops at the accepted parser's first concrete string-table mapping limitation.
Uses optional existing readelf solely as a static corroborator. Does not import
OntoKin, change source, select an alternative interpreter or install anything.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import sys
import time

B = Path('/workspace/scratch/e33f906d0e8e')
O = B / 'audits/h0_review'
SOURCE = B / 'h0_source/prototypes/static_tray_v01/current_host_inspection_v01.py'
IMAGE = Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
SNAPSHOT = B / 'h0_work/selected-python.bin'
EXPECTED = {'sha256': 'fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7',
            'size_bytes': 30894944, 'mode': '0o755'}
checks = []


def ident(path):
    data = path.read_bytes()
    return {'path': str(path), 'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'mode': oct(stat.S_IMODE(path.stat().st_mode))}


def inode(st):
    return [st.st_dev, st.st_ino, st.st_size, st.st_mode, st.st_nlink, st.st_mtime_ns, st.st_ctime_ns]


def check(name, passed, detail=None):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
    if not passed:
        raise ValueError('Unexpected independent verification failure: ' + name)


fd = os.open(IMAGE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
with os.fdopen(fd, 'rb') as stream:
    before = os.fstat(stream.fileno())
    raw = stream.read(512 * 1024 * 1024 + 1)
    after = os.fstat(stream.fileno())
check('selected image regular canonical bounded unchanged bytes',
      IMAGE.resolve() == IMAGE and stat.S_ISREG(before.st_mode)
      and len(raw) <= 512 * 1024 * 1024 and inode(before) == inode(after) == inode(IMAGE.lstat()))
actual = {'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw), 'mode': oct(stat.S_IMODE(before.st_mode))}
check('selected image exact expected identity', actual == EXPECTED, actual)
check('engineer immutable snapshot equals actual selected image', SNAPSHOT.read_bytes() == raw, ident(SNAPSHOT))
source_raw = SOURCE.read_bytes()
check('accepted source exact retained identity',
      hashlib.sha256(source_raw).hexdigest() == 'b2f4c869fd03919047db797bd3a80616cbe16f6b17689fe61d40754b27f97a39', ident(SOURCE))

check('ELF identity supported before string-table guard',
      raw[:4] == b'\x7fELF' and raw[4:7] == b'\x02\x01\x01' and raw[7] in (0, 3))
elf_type, machine, version = struct.unpack_from('<HHI', raw, 16)
check('ELF type and architecture supported', elf_type in (2, 3) and machine in (62, 183) and version == 1)
phoff = struct.unpack_from('<Q', raw, 32)[0]
ehsize, phentsize, phnum = struct.unpack_from('<HHH', raw, 52)
check('program header table bounds supported', ehsize == 64 and phentsize == 56 and 0 < phnum <= 256
      and phoff + phentsize * phnum <= len(raw))
segments, dynamic, interpreter = [], [], []
programs = []
for n in range(phnum):
    fields = struct.unpack_from('<IIQQQQQQ', raw, phoff + n * phentsize)
    kind, flags, offset, virtual, physical, filesz, memsz, align = fields
    programs.append(dict(zip(['kind','flags','file_offset','virtual_address','physical_address','file_size','memory_size','alignment'], fields)))
    check('program header range/alignment ' + str(n), offset + filesz <= len(raw) and filesz <= memsz
          and (align in (0, 1) or align & (align - 1) == 0))
    if kind == 1:
        check('load file/virtual alignment ' + str(n), align in (0, 1) or offset % align == virtual % align)
        segments.append({'virtual_address': virtual, 'file_offset': offset, 'file_size': filesz,
                         'virtual_end': virtual + filesz})
    elif kind == 2:
        check('dynamic table range supported', bool(filesz) and filesz % 16 == 0 and filesz <= 65536)
        dynamic.append((offset, virtual, filesz))
    elif kind == 3:
        data = raw[offset:offset+filesz]
        check('interpreter string supported', 1 < filesz <= 4096 and data[-1:] == b'\0' and b'\0' not in data[:-1])
        interpreter.append(data[:-1].decode('ascii'))
check('unique dynamic and interpreter tables', len(dynamic) == 1 and len(interpreter) == 1 and bool(segments))
offset, virtual, size = dynamic[0]
dynamic_maps = [s['file_offset'] + virtual - s['virtual_address'] for s in segments
                if s['virtual_address'] <= virtual and virtual + size <= s['virtual_end']]
check('dynamic table mapping accepted before failing guard', len(set(dynamic_maps)) == 1 and dynamic_maps[0] == offset, dynamic_maps)
entries = []
terminated = False
for pos in range(offset, offset + size, 16):
    tag, value = struct.unpack_from('<qQ', raw, pos)
    if tag == 0:
        terminated = True
        break
    entries.append((tag, value))
check('dynamic table terminated', terminated)
ordinary = set(range(1,31)) | {32,33,34,35,36,37,0x6FFFFEF5,0x6FFFFFF0,0x6FFFFFF9,
                             0x6FFFFFFA,0x6FFFFFFB,0x6FFFFFFC,0x6FFFFFFD,0x6FFFFFFE,0x6FFFFFFF}
check('dynamic tags accepted before string-table guard', all(tag in ordinary for tag,value in entries))
flags = [v for tag,v in entries if tag == 30]
flags1 = [v for tag,v in entries if tag == 0x6FFFFFFB]
check('dynamic flags accepted before string-table guard', len(flags)<=1 and len(flags1)<=1
      and all(v & ~8 == 0 for v in flags) and all(v & ~(1|0x08000000)==0 for v in flags1))
strtabs = [v for tag,v in entries if tag == 5]
strsizes = [v for tag,v in entries if tag == 10]
check('unique dynamic string address and size', len(strtabs)==len(strsizes)==1)
start, length = strtabs[0], strsizes[0]
end = start + length
check('string table finite size accepted', 0 < length <= 4*1024*1024)
maps = [s['file_offset'] + start - s['virtual_address'] for s in segments
        if s['virtual_address'] <= start and end <= s['virtual_end']]
overlaps = [s for s in segments if max(start,s['virtual_address']) < min(end,s['virtual_end'])]
check('independently reproduced expected single-segment guard failure', maps == [],
      {'DT_STRTAB': start, 'DT_STRSZ': length, 'end_exclusive': end, 'mappings': maps,
       'overlapping_load_segments': overlaps})
check('engineer claimed arithmetic matches independent bytes',
      start == 4191704 and length == 42266 and end == 4233970
      and [(s['virtual_address'],s['virtual_end']) for s in overlaps] == [(4190208,4194304),(4194304,4328816)])

source = source_raw.decode()
predicate = '''mappings = [fileoff + straddr - virtual for virtual, fileoff, size in segments
                    if virtual <= straddr and straddr + strsize <= virtual + size]
        _require(len(set(mappings)) == 1, "UNSUPPORTED", "Ambiguous/unmapped ELF string table")'''
check('source has exact failing predicate', predicate in source)
check('selected Python parser is mandatory author prerequisite',
      'read_elf_metadata(author["python_descriptor"]["path"], check=check)["interpreter"]' in source
      and '_check_author_runtime(plan, inventory' in source
      and 'self.code = category if category.startswith("CHI-") else "CHI-" + category' in source)

readelf = shutil.which('readelf', path='/usr/bin:/bin')
readelf_observation = {'available': readelf is not None, 'target_execution': False}
if readelf is not None:
    argv = [readelf, '--wide', '--file-header', '--program-headers', '--dynamic', str(IMAGE)]
    env = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
    began = time.monotonic()
    with (O/'readelf-selected-python.stdout.txt').open('xb') as out, (O/'readelf-selected-python.stderr.txt').open('xb') as err:
        outcome = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                 cwd=O, env=env, timeout=10, check=False)
    readelf_observation.update(command=argv, environment=env, returncode=outcome.returncode,
                               elapsed_seconds=time.monotonic()-began, executable=ident(Path(readelf)),
                               stdout=ident(O/'readelf-selected-python.stdout.txt'),
                               stderr=ident(O/'readelf-selected-python.stderr.txt'))
    stdout=(O/'readelf-selected-python.stdout.txt').read_text()
    table_match=re.search(r'\(STRTAB\)\s+(0x[0-9a-fA-F]+)', stdout)
    size_match=re.search(r'\(STRSZ\)\s+(\d+)\s+\(bytes\)', stdout)
    check('existing readelf independently corroborates string address and size',
          outcome.returncode==0 and bool(table_match) and bool(size_match)
          and int(table_match.group(1),16)==start and int(size_match.group(1))==length,
          readelf_observation)
check('selected image unchanged after review', ident(IMAGE) == {'path':str(IMAGE),**EXPECTED}
      and inode(IMAGE.lstat()) == inode(before))

source_lines=source.splitlines()
ranges=[(117,134),(697,707),(1184,1196),(1384,1415)]
source_excerpt='\n\n'.join('\n'.join(f'{i+1}: {source_lines[i]}' for i in range(a-1,z)) for a,z in ranges)
(O/'SOURCE-PREDICATE.txt').write_text(source_excerpt+'\n')
report={
 'schema':'ontokin.c271.p09-independent-python-blocker-verification/1',
 'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'/root/p08_delivery_audit','phase':'C271-P09-H0-static-preparation',
 'verdict':'CONFIRMED_STATIC_H0_BLOCKER_NO_PLAN_APPROVAL',
 'source_commit':'2c6bbfb7aa1d402ce47ffdc24adb4d89b8a81c1e',
 'source':ident(SOURCE),'selected_python':{'path':str(IMAGE),**EXPECTED},
 'engineer_snapshot':ident(SNAPSHOT),'checks':checks,'passed':all(c['passed'] for c in checks),
 'raw_program_headers':programs,'raw_dynamic_entries':entries,
 'string_table':{'address':start,'size_bytes':length,'end_exclusive':end,'single_segment_mappings':maps,'overlapping_load_segments':overlaps},
 'source_backed_result':{'category':'CHI-UNSUPPORTED','message':'Ambiguous/unmapped ELF string table',
  'classification':'Predicted mandatory rejection from unchanged source plus actual static input; no product function invoked.',
  'reachability':'_validate calls _check_author_runtime; that predicate calls read_elf_metadata on the actual selected Python descriptor before observation. _check_resolution also requires the same Python ELF image. No complete real plan can omit or fabricate that required image.',
  'meaning':'Unsupported finite parser layout. This review does not classify the Python binary as corrupt or generally invalid ELF.'},
 'readelf_corroboration':readelf_observation,
 'execution_counts':{'node':0,'ldd':0,'checkers':0,'preparer':0,'runtime_installations':0,'product_imports':0,'product_tests':0,'readelf_static_tool':1 if readelf else 0},
 'stopping_boundary':'No string-table decoding, metadata/loader expansion, alternate interpreter selection, plan approval, runtime preparation, repair or later phase after confirmed blocker.',
 'artifact_preservation':'Engineer attempt001 assertion failure and diagnostic002 remain unchanged; selected-python.bin is regular inert evidence. Existing P08 intake audit unchanged.',
 'command':sys.argv,'verifying_interpreter':sys.executable,
 'readelf_is_static_tool_only':'readelf reads target file bytes; it does not execute the selected Python target.'
}
with (O/'PYTHON-BLOCKER-VERIFICATION.json').open('x') as target:
    json.dump(report,target,indent=2,sort_keys=True);target.write('\n')
print(json.dumps({'verdict':report['verdict'],'passed':report['passed'],'checks':len(checks),
 'report':ident(O/'PYTHON-BLOCKER-VERIFICATION.json'),'readelf_returncode':readelf_observation.get('returncode')}))
