import datetime,hashlib,json,pathlib,platform,subprocess,sys
p=pathlib.Path('/workspace/scratch/fd65650eb54f/c046-validation/independent-review')
script=p/'audit_core.py';args=[sys.executable,str(script)]
out={'schema':'ontokin.checkpoint046-independent-audit-command/0.1','window_comment':6424984212,'window_expires_utc':'2026-10-26T19:30:00Z','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'args':args,'cwd':'/workspace/scratch/fd65650eb54f','python':sys.version,'executable':sys.executable,'platform':platform.platform(),'script_bytes':script.stat().st_size,'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'product_execution':False,'archive_extraction':False,'source_checker_rerun':False}
with (p/'audit.stdout').open('wb') as stdout,(p/'audit.stderr').open('wb') as stderr:
    r=subprocess.run(args,cwd=out['cwd'],stdout=stdout,stderr=stderr)
out.update(exit_code=r.returncode,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(p/'command.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
print((p/'audit.stdout').read_text())
print((p/'audit.stderr').read_text())
raise SystemExit(r.returncode)
