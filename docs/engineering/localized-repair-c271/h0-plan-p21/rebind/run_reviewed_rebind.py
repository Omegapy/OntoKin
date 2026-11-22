from pathlib import Path
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_descriptor(row):
    path = Path(row['path'])
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Prelaunch input is not a regular file: '+str(path))
    if (info.st_size, sha(path), oct(stat.S_IMODE(info.st_mode))) != (row['bytes'], row['sha256'], row['mode']):
        raise ValueError('Prelaunch input identity differs: '+str(path))


def main():
    if len(sys.argv) != 3:
        raise ValueError('Expected exact plan path and independently supplied digest')
    plan_path = Path(sys.argv[1])
    if sha(plan_path) != sys.argv[2]:
        raise ValueError('Plan digest differs')
    plan = json.loads(plan_path.read_text())
    review = json.loads(Path(plan['independent_review']).read_text())
    if review['verdict'] != 'accepted_for_execution' or review['plan_sha256'] != sys.argv[2] or review['script_sha256'] != sha(plan['controller']['path']) or review['wrapper_sha256'] != sha(__file__):
        raise ValueError('Exact independent review missing')
    check_descriptor(plan['controller'])
    check_descriptor(plan['wrapper'])
    check_descriptor(plan['python'])
    check_descriptor(plan['early_receipt'])
    fixed = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','UV_THREADPOOL_SIZE':'2'}
    if plan['environment'] != fixed or plan['timeout_seconds'] != 60:
        raise ValueError('Environment/limit changed')
    expected_prefix = [plan['python']['path'],'-I','-S','-B','-X','pycache_prefix='+plan['pycache_prefix'],plan['controller']['path']]
    if plan['argv_prefix'] != expected_prefix or Path(plan['cwd']).resolve() != Path(__file__).parent:
        raise ValueError('Command/cwd differs')
    for path in [plan['output'],plan['pycache_prefix'],plan['wrapper_output'],plan['stdout'],plan['stderr']]:
        if os.path.lexists(path):
            raise FileExistsError('No retry or overwrite: '+path)
    argv = plan['argv_prefix']+[str(plan_path),sys.argv[2]]
    record = {'schema':'ontokin.c271.p21-rebind-launch/1','started_at_utc':datetime.now(timezone.utc).isoformat(),'argv':argv,'cwd':plan['cwd'],'environment':fixed,'timeout_seconds':60,'cleanup_timeout_seconds':5,'plan_sha256':sys.argv[2],'script_sha256':sha(plan['controller']['path']),'wrapper_sha256':sha(__file__),'python_descriptor':plan['python'],'prelaunch_python_identity_verified':True,'direct_controller_starts':0,'status':'launch_pending','retry':False}
    stdout = b''
    stderr = b''
    process = None
    try:
        process = subprocess.Popen(argv,cwd=plan['cwd'],env=fixed,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        record.update({'pid':process.pid,'direct_controller_starts':1,'status':'running'})
        try:
            stdout,stderr = process.communicate(timeout=60)
            record.update({'status':'completed','exit_code':process.returncode,'termination_observed':True})
        except subprocess.TimeoutExpired as error:
            process.kill()
            try:
                stdout,stderr = process.communicate(timeout=5)
                record.update({'status':'timed_out_killed','exit_code':process.returncode,'termination_observed':True})
            except subprocess.TimeoutExpired as second:
                stdout,stderr = second.stdout or b'', second.stderr or b''
                record.update({'status':'timed_out_termination_unknown','termination_observed':False})
    except Exception as error:
        record.update({'status':'launch_error','error':repr(error),'termination_observed':process is None or process.poll() is not None})
    for key,raw in [('stdout',stdout),('stderr',stderr)]:
        path = Path(plan[key])
        with path.open('xb') as stream:
            stream.write(raw)
        record[key] = {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    record['postrun_plan_sha256'] = sha(plan_path)
    record['postrun_script_sha256'] = sha(plan['controller']['path'])
    record['postrun_python_sha256'] = sha(plan['python']['path'])
    record['plan_script_python_unchanged'] = record['postrun_plan_sha256']==record['plan_sha256'] and record['postrun_script_sha256']==record['script_sha256'] and record['postrun_python_sha256']==plan['python']['sha256']
    if Path(plan['output']).is_file():
        record['result_sha256']=sha(plan['output'])
    record['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    with Path(plan['wrapper_output']).open('x') as stream:
        json.dump(record,stream,indent=2)
        stream.write('\n')
    print(json.dumps({'status':record['status'],'exit_code':record.get('exit_code'),'plan_script_python_unchanged':record['plan_script_python_unchanged'],'result_sha256':record.get('result_sha256')}))
    return 0 if record['status']=='completed' and record.get('exit_code')==0 and record['plan_script_python_unchanged'] else 2


if __name__=='__main__':
    raise SystemExit(main())
