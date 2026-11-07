#!/usr/bin/env python3
"""Restore a sealed C091 evidence archive after strict native source recovery.

Run beside the handoff's unchanged handoff_common.py. Every selected original
file is written once to a fresh destination, with full SHA256/native-ID/mode
checks. The evidence archive commit is never checked out as product source.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from handoff_common import (directory_fd, fingerprint, fresh, git_environment,
                            load_json, new_directory, ordinary, relative, require,
                            write_json, HEX40, HEX64)

INDEX_PATH='C091-EVIDENCE-INDEX.json'


def read_exact(stream,size):
    pieces=[]
    while size:
        value=stream.read(size)
        require(bool(value),'Truncated native evidence body')
        pieces.append(value);size-=len(value)
    return b''.join(pieces)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','manifest','destination','report'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    for name,value in vars(args).items():setattr(args,name,value.absolute())
    protected=(args.repo,args.manifest)
    fresh(args.destination,protected);fresh(args.report,(*protected,args.destination))
    before=fingerprint(args.manifest)
    index=load_json(args.manifest)
    require(index['schema_version']=='ontokin.exact-evidence-archive/1' and index['status']=='captured',
            'Unknown evidence archive schema or state')
    rows=index['entries']
    require(type(rows) is list and type(index['file_count']) is int and len(rows)<=99999
            and len(rows)==index['file_count'],'Invalid evidence file count')
    paths=[];total=0
    for row in rows:
        name=relative(row['path'],source=True);paths.append(name)
        require(type(row['bytes']) is int and 0<=row['bytes']<=2**31,'Invalid evidence byte count')
        require(HEX40.fullmatch(row['git_blob_sha1']) and HEX64.fullmatch(row['sha256']),'Invalid evidence identity')
        require(type(row['mode']) is str and len(row['mode'])==4 and all(c in '01234567' for c in row['mode'])
                and int(row['mode'],8)<=0o777,'Invalid ordinary evidence mode')
        total+=row['bytes']
    require(paths==sorted(set(paths)) and type(index['bytes']) is int and total==index['bytes']
            and total<=64*1024**3 and INDEX_PATH not in paths,'Evidence inventory is not closed')
    descriptor=directory_fd(args.repo);os.close(descriptor)
    prefix=['git','--no-replace-objects','-C',str(args.repo),'-c','core.hooksPath=/dev/null',
            '-c','core.attributesFile=/dev/null','-c','protocol.allow=never']
    def git(*words):
        return subprocess.check_output(prefix+list(words),env=git_environment())
    def native_object(oid,kind):
        require(HEX40.fullmatch(oid) and git('cat-file','-t',oid)==(kind+'\n').encode(),
                'Native evidence authority has the wrong object type')
        size=int(git('cat-file','-s',oid))
        require(0<=size<=64*1024**2,'Native evidence authority exceeds its byte bound')
        raw=git('cat-file',kind,oid)
        require(len(raw)==size and hashlib.sha1((kind+' '+str(size)+'\0').encode()+raw).hexdigest()==oid,
                'Native evidence authority bytes do not match their declared object identity')
        return raw
    commit=index['archive_commit'];tree=index['archive_tree']
    require(HEX40.fullmatch(commit) and HEX40.fullmatch(tree),'Invalid native archive reference')
    commit_body=native_object(commit,'commit')
    headers=commit_body.split(b'\n\n',1)[0].splitlines()
    require(HEX40.fullmatch(index['source_head']) and
            [line[7:].decode('ascii') for line in headers if line.startswith(b'parent ')]==[index['source_head']]
            and [line[5:].decode('ascii') for line in headers if line.startswith(b'tree ')]==[tree],
            'The archive does not have the exact declared tree and source parent')
    native_object(index['source_head'],'commit')
    native_object(tree,'tree')
    require(type(index['archive_ref']) is str and index['archive_ref'].startswith('refs/archive/c091-')
            and git('rev-parse','--verify',index['archive_ref']).decode().strip()==commit,
            'The captured archive reference differs from its declared commit')
    require(git('rev-parse',commit+'^{tree}').decode().strip()==tree,'Native archive tree differs')
    require(index['index_path']==INDEX_PATH and HEX40.fullmatch(index['index_blob_sha1'])
            and type(index['index_bytes']) is int and 0<=index['index_bytes']<=64*1024**2
            and HEX64.fullmatch(index['index_sha256']),'Invalid bound index identity')
    require(git('cat-file','-t',index['index_blob_sha1'])==b'blob\n'
            and int(git('cat-file','-s',index['index_blob_sha1']))==index['index_bytes'],'Bound index type or size differs')
    bound={k:index[k] for k in ('source_head','file_count','bytes','entries','included_roots','excluded_roots','scope')}
    bound['schema_version']='ontokin.exact-evidence-index/1'
    expected_index=(json.dumps(bound,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
    native_index=native_object(index['index_blob_sha1'],'blob')
    require(native_index==expected_index and len(native_index)==index['index_bytes']
            and hashlib.sha256(native_index).hexdigest()==index['index_sha256'],
            'The complete evidence index differs from its native archive authority')
    native={}
    verified_trees={tree}
    for line in git('ls-tree','-r','-t','-z',tree).split(b'\0'):
        if not line:continue
        metadata,name=line.split(b'\t',1);mode,kind,oid=metadata.decode().split()
        if kind=='tree':
            if oid not in verified_trees:native_object(oid,'tree');verified_trees.add(oid)
            continue
        require(kind=='blob','Evidence archive contains a non-blob leaf')
        native[name.decode('utf-8')]=(mode,oid)
    expected={r['path']:(('100755' if int(r['mode'],8)&0o111 else '100644'),r['git_blob_sha1']) for r in rows}
    expected[INDEX_PATH]=('100644',index['index_blob_sha1'])
    require(native==expected,'Native tree does not match the complete evidence index')
    new_directory(args.destination)
    process=subprocess.Popen(prefix+['cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,env=git_environment())
    restored=0
    try:
        for row in rows:
            process.stdin.write((row['git_blob_sha1']+'\n').encode());process.stdin.flush()
            frame=(row['git_blob_sha1']+' blob '+str(row['bytes'])+'\n').encode()
            require(process.stdout.readline()==frame,'Native evidence frame differs')
            target=args.destination/row['path']
            descriptor=directory_fd(target.parent,create=True);os.close(descriptor)
            sha=hashlib.sha256();native_sha=hashlib.sha1(b'blob '+str(row['bytes']).encode()+b'\0')
            remaining=row['bytes']
            with ordinary(target,new=True,mode=int(row['mode'],8)) as outgoing:
                while remaining:
                    block=read_exact(process.stdout,min(remaining,1048576));remaining-=len(block)
                    sha.update(block);native_sha.update(block);outgoing.write(block)
                outgoing.flush();os.fsync(outgoing.fileno())
            require(read_exact(process.stdout,1)==b'\n','Invalid native body delimiter')
            require(sha.hexdigest()==row['sha256'] and native_sha.hexdigest()==row['git_blob_sha1'],
                    'Restored evidence bytes differ from the original complete identities')
            require(fingerprint(target)=={k:row[k] for k in ('bytes','sha256','mode')},'Final evidence file differs')
            restored+=1
            if restored%1000==0:print(json.dumps({'restored_files':restored}),flush=True)
        process.stdin.close()
        require(process.stdout.read()==b'' and process.wait()==0,'Native evidence stream did not close cleanly')
    finally:
        if process.poll() is None:process.kill();process.wait()
    require(fingerprint(args.manifest)==before,'Evidence index changed during restoration')
    actual=[]
    for parent,dirs,names in os.walk(args.destination,followlinks=False):
        for name in dirs:
            require(not (Path(parent)/name).is_symlink(),'Restored directory became a link')
        for name in names:actual.append((Path(parent)/name).relative_to(args.destination).as_posix())
    require(sorted(actual)==paths,'Restored evidence contains missing or extra files')
    for row in rows:
        require(fingerprint(args.destination/row['path'])=={k:row[k] for k in ('bytes','sha256','mode')},
                'Restored evidence changed before the final complete admission')
    result={'schema_version':'ontokin.exact-evidence-recovery/1','status':'passed',
            'archive_commit':commit,'archive_tree':tree,'manifest':before,'files':restored,'bytes':total,
            'every_original_file_byte_and_mode_exact':True,'normalization':False,
            'product_checkout_changed':False,'destination':str(args.destination)}
    write_json(args.report,result);print(json.dumps(result),flush=True)


if __name__=='__main__':main()
