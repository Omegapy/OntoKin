"""Independent inert archive/data calculations for C271 P27 review.

This imports no OntoKin code and never opens an installed host library.
It records observations; it is not an ELF inspector or execution gate.
"""
from pathlib import Path
import hashlib
import io
import json
import struct
import tarfile
import zipfile

ROOT = Path('/workspace/scratch/906410cf525c')
OUT = ROOT / 'records/design-review'
BASE = ROOT / 'repo/docs/engineering/localized-repair-c271'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode_ar(data):
    assert data[:8] == b'!<arch>\n'
    result = {}
    cursor = 8
    while cursor < len(data):
        header = data[cursor:cursor+60]
        assert len(header) == 60 and header[58:60] == b'`\n'
        name = header[:16].decode('ascii').strip().removesuffix('/')
        size = int(header[48:58])
        assert size >= 0 and cursor + 60 + size <= len(data) and name not in result
        result[name] = data[cursor+60:cursor+60+size]
        cursor += 60 + size + size % 2
    assert cursor == len(data)
    return result


def observe_elf(data):
    assert data[:16] == bytes.fromhex('7f454c46020101000000000000000000')
    kind, machine, version = struct.unpack_from('<HHI', data, 16)
    assert (kind, machine, version) == (3, 62, 1)
    phoff = struct.unpack_from('<Q', data, 32)[0]
    ehsize, entsize, count = struct.unpack_from('<HHH', data, 52)
    assert (ehsize, entsize) == (64, 56) and 0 < count <= 256
    assert phoff + entsize * count <= len(data)
    headers = [struct.unpack_from('<IIQQQQQQ', data, phoff+i*56) for i in range(count)]
    for typ, flags, off, virt, phys, size, mem, align in headers:
        assert 0 <= off <= len(data) and off + size <= len(data) and size <= mem
        assert align in (0, 1) or align & (align-1) == 0
        if typ == 1 and align > 1:
            assert off % align == virt % align
    dyn = [h for h in headers if h[0] == 2]
    assert len(dyn) == 1
    _, _, off, virt, _, size, _, _ = dyn[0]
    assert size > 0 and size % 16 == 0 and size <= 65536
    mappings = {h[2]+virt-h[3] for h in headers if h[0] == 1 and h[3] <= virt and virt+size <= h[3]+h[5]}
    assert mappings == {off}
    entries = []
    for index in range(size//16):
        tag, value = struct.unpack_from('<qQ', data, off+16*index)
        entries.append({'index':index,'tag':tag,'value':value})
        if tag == 0:
            break
    assert entries[-1]['tag'] == 0
    def values(tag):
        return [row['value'] for row in entries if row['tag'] == tag]
    straddr, = values(5)
    strsize, = values(10)
    offsets = {h[2]+straddr-h[3] for h in headers if h[0] == 1 and h[3] <= straddr and straddr+strsize <= h[3]+h[5]}
    assert len(offsets) == 1 and 0 < strsize <= 4*1024*1024
    stroff, = offsets
    strings = data[stroff:stroff+strsize]
    def string(position):
        assert 0 <= position < len(strings)
        end = strings.index(b'\0',position)
        assert position < end <= position+4096
        return strings[position:end].decode('ascii')
    ordinary = set(range(1,31)) | {32,33,34,35,36,37,0x6FFFFEF5,0x6FFFFFF0,0x6FFFFFF9,0x6FFFFFFA,0x6FFFFFFB,0x6FFFFFFC,0x6FFFFFFD,0x6FFFFFFE,0x6FFFFFFF}
    excluded = [r for r in entries[:-1] if r['tag'] not in ordinary]
    return {
        'elf_class':64,'endian':'little','type':kind,'machine':machine,
        'needed':[string(v) for v in values(1)],'soname':[string(v) for v in values(14)],
        'rpath':[string(v) for v in values(15)],'runpath':[string(v) for v in values(29)],
        'flags':values(30),'flags1':values(0x6FFFFFFB),
        'dynamic_entries_including_terminator':entries,
        'generic_tag_exclusions_source_deduction':excluded,
        'generic_flags_compatible_source_deduction':len(values(30)) <= 1 and all(v & ~8 == 0 for v in values(30)),
        'generic_flags1_compatible_source_deduction':len(values(0x6FFFFFFB)) <= 1 and all(v & ~0x08000001 == 0 for v in values(0x6FFFFFFB)),
        'claims_product_execution':False,
    }


z15 = zipfile.ZipFile(BASE / 'host-loader-p15/P15-EVIDENCE.zip')
pkgmember = 'session/package-retrieval/libc6_2.41-12+deb13u4_amd64.deb.inert'
pkg = z15.read(pkgmember)
assert len(pkg) == 2846580 and sha(pkg) == '967aa62605721081c3eb2a17650611a792aa802d76a6511d1840242623d204c9'
ar = decode_ar(pkg)
tar = tarfile.open(fileobj=io.BytesIO(ar['data.tar.xz']),mode='r:xz')
observed = json.loads((OUT/'p26-observations/cache-run001.stdout.json').read_text())
rows = []
for name in ['libdl.so.2','libpthread.so.0','libutil.so.1','libm.so.6','librt.so.1']:
    member = './usr/lib/x86_64-linux-gnu/'+name
    item = tar.getmember(member)
    assert item.isfile() and item.mode == 0o644
    data = tar.extractfile(item).read()
    actual, = [r for r in observed['observations'] if r['path'] == '/usr/lib/x86_64-linux-gnu/'+name]
    assert len(data) == actual['bytes'] and sha(data) == actual['sha256'] and actual['mode'] == '0o644'
    fields = observe_elf(data)
    assert fields['dynamic_entries_including_terminator'] == [{k:r[k] for k in ('index','tag','value')} for r in actual['elf']['dynamic_entries']]
    for local, raw in [('needed','dt_needed'),('soname','dt_soname'),('rpath','dt_rpath'),('runpath','dt_runpath'),('flags','dt_flags'),('flags1','dt_flags_1')]:
        assert fields[local] == actual['elf'][raw]
    if name == 'libdl.so.2':
        inert = (ROOT/'inputs/p26/repository/docs/engineering/localized-repair-c271/h0-plan-p26/libdl.so.2.inert').read_bytes()
        assert data == inert
    rows.append({'package_member':member,'bytes':len(data),'sha256':sha(data),'package_mode':oct(item.mode),'equal_p26_raw_observation':True,'fields':fields})
result = {'schema':'ontokin.c271.p27-independent-package-byte-audit/1','passed':True,
          'reviewer':'/root/design_review','package':{'archive_member':pkgmember,'bytes':len(pkg),'sha256':sha(pkg)},
          'ar_members':[{'name':n,'bytes':len(b),'sha256':sha(b)} for n,b in ar.items()],
          'images':rows,'current_host_inputs_opened':False,'product_imports_or_executions':0,
          'limit':'Exact retained package bytes and raw metadata equality only; source deductions are not product outcomes, full loader selection, H0, or runtime safety.'}
(OUT/'RETAINED-BYTE-AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'images':len(rows),'exact_portable_libdl_equality':True,'product_execution':False,'report':'records/design-review/RETAINED-BYTE-AUDIT.json'}))
