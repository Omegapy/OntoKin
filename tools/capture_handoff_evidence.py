#!/usr/bin/env python3
"""Retain exact selected evidence in an explicitly archival native Git tree.

The archive is not a product branch and must never be merged. Its independently
hashed index preserves complete file bytes and original ordinary modes. Native
object packing may deduplicate storage; it cannot normalize evidence content.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

INDEX_PATH = 'C091-EVIDENCE-INDEX.json'


def relative(value):
    if (not value or value.startswith('/') or '\\' in value or ':' in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or any(p in ('', '.', '..') or p.casefold()=='.git' for p in value.split('/'))):
        raise ValueError('Unsafe evidence path: ' + repr(value))
    return value


def stamp(s):
    return s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def directory_fd(path):
    descriptor=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in Path(path).absolute().parts[1:]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=descriptor)
            os.close(descriptor);descriptor=child
        return descriptor
    except BaseException:
        os.close(descriptor);raise


def regular_stream(path):
    parent=directory_fd(path.parent)
    try:descriptor=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
    finally:os.close(parent)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor);raise ValueError('Evidence is not an ordinary file.')
    return os.fdopen(descriptor,'rb')


def identity(path):
    with regular_stream(path) as stream:
        before = os.fstat(stream.fileno())
        if (not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) > 0o777
                or before.st_size>2**31):
            raise ValueError('Evidence must be an ordinary file with ordinary mode.')
        sha = hashlib.sha256()
        native = hashlib.sha1(b'blob ' + str(before.st_size).encode() + b'\0')
        count = 0
        for block in iter(lambda: stream.read(1048576), b''):
            sha.update(block); native.update(block); count += len(block)
        if stamp(before) != stamp(os.fstat(stream.fileno())) or count != before.st_size:
            raise ValueError('Evidence changed while hashing: ' + str(path))
    return {'bytes': count, 'sha256': sha.hexdigest(), 'git_blob_sha1': native.hexdigest(),
            'mode': format(stat.S_IMODE(before.st_mode), '04o')}, stamp(before)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--include', action='append', required=True)
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--source-head', required=True)
    parser.add_argument('--archive-ref', required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    if os.path.lexists(args.manifest):
        raise FileExistsError('A fresh evidence manifest is required.')
    if not args.archive_ref.startswith('refs/archive/c091-'):
        raise ValueError('Evidence requires a distinct C091 archive reference.')
    root = args.root.absolute()
    for directory in (root,args.repo.absolute(),args.manifest.absolute().parent):
        descriptor=directory_fd(directory);os.close(descriptor)
    includes = [relative(x) for x in args.include]
    excludes = [relative(x) for x in args.exclude]
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
               GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1', GIT_OPTIONAL_LOCKS='0', LC_ALL='C')
    prefix = ['git', '--no-replace-objects', '-C', str(args.repo), '-c', 'core.hooksPath=/dev/null',
              '-c', 'core.attributesFile=/dev/null', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
              '-c', 'protocol.allow=never']
    def git(*words, data=None, stream=None, extra=None, allowed=(0,)):
        proc = subprocess.run(prefix+list(words), input=data, stdin=stream, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env={**env, **(extra or {})})
        if proc.returncode not in allowed:
            raise RuntimeError('Git evidence operation failed: '+repr(words)+' '+proc.stderr.decode())
        return proc
    if git('rev-parse', args.source_head+'^{commit}').stdout.decode().strip() != args.source_head:
        raise ValueError('The source head is not an exact native commit.')
    if git('show-ref', '--verify', '--quiet', args.archive_ref, allowed=(0,1)).returncode != 1:
        raise ValueError('An existing archive reference will not be overwritten.')
    omitted = set()
    def excluded(name):
        for skip in excludes:
            if name == skip or name.startswith(skip+'/'):
                omitted.add(skip); return True
        return False
    def inventory():
        paths=set()
        for name in includes:
            incoming = root/name
            descriptor=directory_fd(incoming.parent);os.close(descriptor)
            if incoming.is_symlink(): raise ValueError('Linked input refused: '+name)
            if incoming.is_file():
                if not excluded(name): paths.add(name)
                continue
            if not incoming.is_dir(): raise FileNotFoundError(incoming)
            for parent, dirs, names in os.walk(incoming, followlinks=False):
                directory = Path(parent)
                descriptor=directory_fd(directory);os.close(descriptor)
                keep=[]
                for child in dirs:
                    path=directory/child; key=path.relative_to(root).as_posix()
                    if excluded(key): continue
                    if path.is_symlink(): raise ValueError('Linked input refused: '+key)
                    keep.append(child)
                dirs[:]=keep
                for child in names:
                    path=directory/child; key=relative(path.relative_to(root).as_posix())
                    if not excluded(key): paths.add(key)
                if len(paths)>99999:raise ValueError('Evidence file bound exceeded.')
        if INDEX_PATH in paths:raise ValueError('Reserved archive-index path collides with an input.')
        if args.manifest.absolute().is_relative_to(root) and args.manifest.absolute().relative_to(root).as_posix() in paths:
            raise ValueError('Evidence manifest cannot be an input.')
        return paths
    paths=inventory()
    entries=[]; before_stamps={}
    for i,name in enumerate(sorted(paths),1):
        path=root/name
        row,before=identity(path)
        with regular_stream(path) as incoming:
            oid=git('hash-object','-w','--stdin',stream=incoming).stdout.decode().strip()
        if oid != row['git_blob_sha1'] or stamp(path.lstat()) != before:
            raise ValueError('Native evidence body differs from its complete byte identity: '+name)
        entries.append({'path':name, **row}); before_stamps[name]=before
        if i%1000==0: print(json.dumps({'captured_files':i}),flush=True)
    total=sum(x['bytes'] for x in entries)
    if total>64*1024**3:raise ValueError('Evidence total byte bound exceeded.')
    bound_index={'schema_version':'ontokin.exact-evidence-index/1','source_head':args.source_head,
                 'file_count':len(entries),'bytes':total,'entries':entries,
                 'included_roots':includes,'excluded_roots':sorted(omitted),
                 'scope':'Exact selected ordinary file bytes and modes; no normalization; archival tree is not a product source or a merge candidate.'}
    index_raw=(json.dumps(bound_index,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
    if len(index_raw)>64*1024**2:raise ValueError('Evidence index byte bound exceeded.')
    index_oid=git('hash-object','-w','--stdin',data=index_raw).stdout.decode().strip()
    legacy_index=args.manifest.with_suffix('.index')
    if os.path.lexists(legacy_index):raise FileExistsError(legacy_index)
    index_directory=Path(tempfile.mkdtemp(prefix=args.manifest.stem+'-native-index-',dir=args.manifest.parent))
    temporary=index_directory/'index'
    extra={'GIT_INDEX_FILE':str(temporary.absolute())}
    git('read-tree','--empty',extra=extra)
    listing=b''.join((('100755' if int(row['mode'],8)&0o111 else '100644')+' '+
                     row['git_blob_sha1']+'\t'+row['path']+'\0').encode() for row in entries)
    listing+=('100644 '+index_oid+'\t'+INDEX_PATH+'\0').encode()
    git('update-index','-z','--index-info',data=listing,extra=extra)
    tree=git('write-tree',extra=extra).stdout.decode().strip()
    def unchanged():
        if inventory()!=paths:raise ValueError('The complete evidence file membership changed during capture.')
        for name,before in before_stamps.items():
            if stamp((root/name).lstat()) != before:raise ValueError('Evidence changed during capture: '+name)
    unchanged()
    message=('C091 exact execution evidence archive; never merge into product source\n\n'
             'Retains complete selected bytes and original failed outcomes. This is not release acceptance.\n')
    commit=git('-c','user.name=OntoKin Handoff','-c','user.email=handoff@invalid.local',
               'commit-tree',tree,'-p',args.source_head,data=message.encode()).stdout.decode().strip()
    unchanged()
    git('update-ref',args.archive_ref,commit,'0'*40)
    result={**bound_index,'schema_version':'ontokin.exact-evidence-archive/1','status':'captured',
            'source_head':args.source_head,'archive_commit':commit,'archive_tree':tree,
            'archive_ref':args.archive_ref,'index_path':INDEX_PATH,'index_blob_sha1':index_oid,
            'index_bytes':len(index_raw),'index_sha256':hashlib.sha256(index_raw).hexdigest()}
    with args.manifest.open('x') as output:json.dump(result,output,indent=2);output.write('\n')
    temporary.unlink()
    index_directory.rmdir()
    print(json.dumps({k:v for k,v in result.items() if k!='entries'}),flush=True)


if __name__=='__main__':main()
