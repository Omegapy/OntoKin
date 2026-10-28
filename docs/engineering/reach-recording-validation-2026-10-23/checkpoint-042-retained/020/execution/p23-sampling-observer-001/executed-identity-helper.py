"""Actual recording/test execution with explicit sparse historical-archive disclosure.

This development driver does not establish the release input_closure role.
All materialized tracked files are checked against the Git index and hashed.
Only absent historical evidence ZIP archives/parts may be omitted. Runtime,
tests, source fixtures, specifications and numerical proof inputs must exist.
"""
import argparse, contextlib, hashlib, importlib, io, json, pathlib, platform, subprocess, sys, time, traceback, unittest
from datetime import datetime, timezone

def utc(): return datetime.now(timezone.utc).isoformat()
def write(path,value): path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def identity(root):
    def git(*args): return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()
    status=git('status','--porcelain=v1','--untracked-files=all')
    if status: raise RuntimeError('A clean committed checkout is required: '+status)
    rows=[];omitted=[]
    for entry in subprocess.check_output(['git','-C',str(root),'ls-files','--stage','-z']).split(b'\0'):
        if not entry: continue
        metadata,name=entry.split(b'\t',1);mode,expected,stage=metadata.decode().split();name=name.decode();path=root/name
        if stage!='0': raise RuntimeError('Unmerged input '+name)
        if not path.exists():
            if not name.startswith('docs/engineering/') or not (name.endswith('.zip') or name.endswith('.tar.xz') or '.zip.part' in name):
                raise RuntimeError('Missing required input '+name)
            omitted.append({'path':name,'git_blob_sha1':expected,'mode':mode,'reason':'historical_binary_archive_not_materialized_by_connector'})
            continue
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root): raise RuntimeError('Nonregular input '+name)
        raw=path.read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=expected: raise RuntimeError('Tracked input differs from Git index '+name)
        rows.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'git_blob_sha1':blob,'mode':mode})
    return {'git_commit':git('rev-parse','HEAD'),'git_tree':git('rev-parse','HEAD^{tree}'),'git_status':status,
            'scope':'all_materialized_tracked_bytes_and_explicit_unmaterialized_historical_archive_git_identities',
            'files':rows,'omitted_historical_archives':omitted,'release_input_closure':False}

class Result(unittest.TextTestResult):
    def __init__(self,*a,**k): super().__init__(*a,**k);self.records=[];self.started=[]
    def startTest(self,t): self.started.append(t.id());super().startTest(t)
    def addSuccess(self,t): self.records.append({'test_id':t.id(),'status':'passed'});super().addSuccess(t)
    def addFailure(self,t,e): self.records.append({'test_id':t.id(),'status':'failed','traceback':self._exc_info_to_string(e,t)});super().addFailure(t,e)
    def addError(self,t,e): self.records.append({'test_id':t.id(),'status':'error','traceback':self._exc_info_to_string(e,t)});super().addError(t,e)
    def addSkip(self,t,r): self.records.append({'test_id':t.id(),'status':'skipped','reason':r});super().addSkip(t,r)
    def addSubTest(self,t,st,e):
        super().addSubTest(t,st,e)
        if e is not None: self.records.append({'test_id':t.id(),'subtest':st.id(),'status':'failed','traceback':self._exc_info_to_string(e,t)})

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=pathlib.Path);p.add_argument('--output',required=True,type=pathlib.Path);p.add_argument('--case',action='append',default=[]);p.add_argument('--test',action='append',default=[]);p.add_argument('--all-tests',action='store_true');p.add_argument('--profile',action='store_true');a=p.parse_args()
    root=a.root.resolve();out=a.output.resolve()
    if out.exists() or out.is_relative_to(root): p.error('Use a new output directory outside checkout')
    out.mkdir(parents=True);sys.path[:0]=[str(root/'tests'),str(root)]
    report={'schema_version':'ontokin.reach-sparse-development-execution/0.1','status':'running','release_acceptance':False,'release_input_closure':False,'full_product_goal_completed':False,'started_at':utc(),'command':[sys.executable,*sys.argv],'working_directory':str(root),'environment':{'python':sys.version,'executable':sys.executable,'platform':platform.platform()},'deliveries':[]}
    started=time.monotonic();before=None
    try:
        driver=pathlib.Path(__file__).read_bytes();(out/'executed-driver.py').write_bytes(driver);report['driver_sha256']=hashlib.sha256(driver).hexdigest()
        before=identity(root);write(out/'inputs-before.json',before);report.update(source_commit=before['git_commit'],source_tree=before['git_tree'])
        if a.test or a.all_tests:
            suite=unittest.defaultTestLoader.discover(str(root/'tests')) if a.all_tests else unittest.defaultTestLoader.loadTestsFromNames(a.test)
            # Capture the actual runner output before one final file write.
            # Earlier file-stream attempts are retained separately when their
            # text log is truncated despite complete structured results.
            stream=io.StringIO()
            try:
                with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
                    r=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
            finally:
                log=stream.getvalue();(out/'tests.log').write_text(log)
                report['test_log_sha256']=hashlib.sha256(log.encode()).hexdigest()
                report['test_log_bytes']=len(log.encode())
            report['test_log_complete']=f'Ran {r.testsRun} test' in log
            write(out/'tests.json',{'test_count':r.testsRun,'started':r.started,'results':r.records,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),'expected_failures':len(r.expectedFailures),'unexpected_successes':len(r.unexpectedSuccesses)})
            report.update(test_count=r.testsRun,passed_count=sum(x['status']=='passed' for x in r.records),failures=len(r.failures),errors=len(r.errors),skips=len(r.skipped))
            report['status']='passed' if r.wasSuccessful() and not(r.skipped or r.expectedFailures or r.unexpectedSuccesses) and report['test_log_complete'] else 'failed'
        else:
            from tools.reach_delivery_inventory import SOURCE_CASES,settings,source_files,frozen_cases,descriptor
            from ontokin.bundle import load_file_manifest
            from ontokin.construction import compile_construction
            from ontokin.gltf import export_glb
            from ontokin.scene import ExportOptions
            from fractions import Fraction
            frozen=frozen_cases();cases=a.case or list(SOURCE_CASES)
            if len(cases)!=len(set(cases)) or not set(cases)<=set(SOURCE_CASES): raise ValueError('Invalid source cases')
            report['required_cases']=list(SOURCE_CASES);report['selected_cases']=cases
            for cid in cases:
                directory=out/cid;directory.mkdir();compiler=None;row={'case_id':cid,'status':'running','started_at':utc(),'max_operations':100000,'options':settings(cid),'program_revision':frozen[cid]['program_revision']};clock=time.monotonic()
                try:
                    bundle=load_file_manifest(root/source_files(cid))
                    if bundle.program_revision!=row['program_revision']: raise ValueError('Frozen source differs')
                    compiler=compile_construction(bundle,level='constructed')
                    def perform(): return export_glb(compiler.model,options=ExportOptions(**{**row['options'],'end':Fraction(row['options']['end'])}),target_contract='ontokin.glb/0.6',work=compiler.reach_work)
                    if a.profile:
                        import cProfile
                        pr=cProfile.Profile();pr.enable()
                        try: result=perform()
                        finally: pr.disable();pr.dump_stats(str(directory/'export-profile.pstats'))
                    else: result=perform()
                    if result.report['validation']['status']!='passed' or compiler.budget.operations>100000 or compiler.reach_work.max_operations!=100000: raise ValueError('Delivery validation/budget did not pass')
                    (directory/'scene.glb').write_bytes(result.data);write(directory/'export-report.json',result.report)
                    row.update(status='passed',artifact=descriptor(directory/'scene.glb',relative_to=out),export_report=descriptor(directory/'export-report.json',relative_to=out))
                except Exception as e:
                    row.update(status='failed',failure={'type':type(e).__name__,'message':str(e)},traceback=traceback.format_exc())
                    if hasattr(e,'diagnostic'): row['diagnostic']=e.diagnostic.to_dict(bundle.sources.get(getattr(e.diagnostic.node,'source_id','entry'),bundle.entry.to_source()))
                if compiler is not None: row.update(operations=compiler.budget.operations,work=compiler.reach_work.record())
                row.update(finished_at=utc(),elapsed_seconds=time.monotonic()-clock);write(directory/'request-result.json',row);report['deliveries'].append(row);print(f"{cid}: {row['status']} ({row.get('operations')} operations)",flush=True)
            report['status']='passed' if all(x['status']=='passed' for x in report['deliveries']) else 'failed'
            report['complete_source_delivery_corpus']=report['status']=='passed' and set(cases)==set(SOURCE_CASES)
    except Exception as e: report.update(status='failed',failure={'type':type(e).__name__,'message':str(e)},traceback=traceback.format_exc())
    if before is not None:
        try:
            after=identity(root);write(out/'inputs-after.json',after);report['inputs_stable']=before==after
            if before!=after: report['status']='failed'
        except Exception as e: report.update(status='failed',input_failure=str(e))
    report.update(finished_at=utc(),elapsed_seconds=time.monotonic()-started);write(out/'report.json',report);print(json.dumps({k:report[k] for k in ('status','test_count','passed_count','failures','errors','skips','inputs_stable','failure') if k in report}),flush=True)
    return 0 if report['status']=='passed' else 1
if __name__=='__main__': raise SystemExit(main())
