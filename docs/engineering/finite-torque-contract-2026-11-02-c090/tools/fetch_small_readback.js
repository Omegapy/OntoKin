for(let batch=0;batch<5;batch++){
 const r=await tools.exec_command({cmd:"python3 - <<'PY'\nimport json,pathlib\np=json.load(open('c090-remote/readback-plan.json'));d=pathlib.Path('c090-remote/file-readback');d.mkdir(exist_ok=True);pages=sorted(d.glob('page-*.json'));got={r['requested_sha'] for f in pages for r in json.load(open(f))['observations']};raw=pathlib.Path('c090-remote/raw-readback');pending=[r for r in p['files'] if r['sha'] not in got and not (raw/(r['sha']+'.json')).exists() and r['bytes']<=1000000];print(json.dumps({'ref':p['ref'],'page':len(pages)+1,'pending':len(pending),'files':pending[:12]}))\nPY",max_output_tokens:5000});
 if(r.exit_code!==0)throw Error('Cannot read pending readback plan');
 const p=JSON.parse(r.output);if(!p.files.length){text({small_files_remaining:0});break;}
 const rs=await Promise.allSettled(p.files.map(async f=>{
  const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:'Omegapy/OntoKin',path:f.path,ref:p.ref,encoding:'base64'});
  const x=r.structuredContent;if(r.isError||x?.sha!==f.sha||x?.encoding!=='base64'||typeof x.content!=='string'||(f.bytes>0&&!x.content.length))throw Error('Exact immutable file response unavailable');
  return {requested_sha:f.sha,requested_path:f.path,requested_ref:p.ref,api_variant:'github_fetch_file',response:x};
 }));
 const good=rs.filter(r=>r.status==='fulfilled').map(r=>r.value),failed=rs.map((r,i)=>r.status==='rejected'?{sha:p.files[i].sha,path:p.files[i].path,error:'Immutable file readback failed; exception text suppressed.'}:null).filter(Boolean);
 await tools.apply_patch('*** Begin Patch\n*** Add File: /workspace/scratch/05c3f95a49c1/c090-remote/file-readback/page-'+String(p.page).padStart(4,'0')+'.json\n+'+JSON.stringify({observations:good,failed})+'\n*** End Patch');
 text({page:p.page,read:good.length,failed:failed.length,remaining_before:p.pending});
 if(failed.length)throw Error('Retained file readback failure; inspect before retry');
}
