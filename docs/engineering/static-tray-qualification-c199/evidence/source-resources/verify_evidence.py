"""Read-only verification of preserved C199 evidence and archive references."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile
import zipfile


def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            result.update(chunk)
    return result.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True)
    parser.add_argument('--repo',default=str(Path(__file__).resolve().parents[5]))
    args=parser.parse_args()
    directory=Path(args.bundle).resolve();repo=Path(args.repo).resolve()
    outer=json.loads((directory/'MANIFEST.json').read_bytes())
    path=directory/outer['archive']
    assert path.stat().st_size==outer['size_bytes'] and digest(path)==outer['sha256']
    handles={};cache={};count=0;total=0
    try:
        handles['self']=zipfile.ZipFile(path)
        raw=handles['self'].read('FILES.json')
        assert hashlib.sha256(raw).hexdigest()==outer['files_manifest_sha256']
        manifest=json.loads(raw)
        assert manifest['external_archives']==outer['external_archives']
        names=set()
        for item in manifest['files']:
            logical=PurePosixPath(item['path'])
            assert not logical.is_absolute() and '..' not in logical.parts and item['path'] not in names
            names.add(item['path'])
            mode=int(item['posix_mode'],8)
            if item['file_type']=='directory':
                assert stat.S_ISDIR(mode)
                continue
            if item['file_type']=='symlink':
                assert stat.S_ISLNK(mode) and isinstance(item['target'],str)
                continue
            assert item['file_type']=='regular' and stat.S_ISREG(mode)
            reference=item['storage'];key=reference['archive']
            if key not in handles:
                declared=manifest['external_archives'][key]
                external=repo/declared['path']
                assert external.stat().st_size==declared['size_bytes'] and digest(external)==declared['sha256']
                handles[key]=zipfile.ZipFile(external) if declared['format']=='zip' else tarfile.open(external,'r:gz')
            address=(key,reference['member'])
            if address not in cache:
                archive=handles[key]
                if isinstance(archive,zipfile.ZipFile):
                    data=archive.read(reference['member'])
                else:
                    data=archive.extractfile(reference['member']).read()
                cache[address]=(len(data),hashlib.sha256(data).hexdigest())
            assert cache[address]==(item['size_bytes'],item['sha256']),item['path']
            count+=1;total+=item['size_bytes']
        lookup={item['path']:item for item in manifest['files']}
        for group in manifest['hardlink_groups']:
            members=[lookup[name] for name in group['paths']]
            assert len(members)>1 and all(item['file_type']=='regular' for item in members)
            assert len({(item['sha256'],item['size_bytes'],item['posix_mode']) for item in members})==1
        assert len(manifest['files'])==outer['logical_entries']
        print(json.dumps({'passed':True,'bundle':manifest['bundle'],'logical_entries':len(names),
                          'regular_file_bindings_verified':count,'logical_bytes_verified':total,
                          'unique_members_read':len(cache),'hardlink_groups':len(manifest['hardlink_groups']),
                          'native_starts':0,'test_process_starts':0},sort_keys=True))
    finally:
        for handle in handles.values():
            handle.close()


if __name__=='__main__':
    main()
