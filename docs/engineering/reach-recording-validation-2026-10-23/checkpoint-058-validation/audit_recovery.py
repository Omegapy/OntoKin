#!/usr/bin/env python3
"""Audit acquired byte identities and preparation-only link coverage, not conformance."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import platform
import re
import sys
from urllib.parse import unquote, urlsplit

BASE=Path('/workspace/scratch/0dd9316e88af/c058')
SOURCE=BASE/'source'
REC=BASE/'recovery'
tree=json.loads((REC/'c057-tree.json').read_text())
by={x['path']:x for x in tree['tree']}
plan=json.loads((REC/'recovery-plan.json').read_text())
failures=[]

def read_identity(path, expected, rel):
    if not path.is_file():
        failures.append({'path':rel,'failure':'missing file'})
        return None
    data=path.read_bytes()
    actual={'path':rel,'bytes':len(data),'git_blob':hashlib.sha1(('blob %d\0'%len(data)).encode()+data).hexdigest(),'sha256':hashlib.sha256(data).hexdigest(),'mode':format(path.stat().st_mode & 0o777,'03o')}
    if actual['bytes']!=expected['size'] or actual['git_blob']!=expected['sha']:
        failures.append({'path':rel,'failure':'size/blob mismatch','actual':actual,'expected':expected})
    if expected['mode'] in ('100644','100755') and actual['mode']!=expected['mode'][-3:]:
        failures.append({'path':rel,'failure':'mode mismatch'})
    return actual

records=[]
for x in sorted(plan['inputs'],key=lambda x:x['path']):
    rec=read_identity(SOURCE/x['path'],x,x['path'])
    if rec: records.append(rec)

accepted_tree=json.loads((REC/'c030-tree.json').read_text())
accepted_by={x['path']:x for x in accepted_tree['tree']}
binding=json.loads((SOURCE/'docs/engineering/reach-recording-validation-2026-10-23/checkpoint-057-source-binding.json').read_text())
accepted=[]
for pair in binding['paired_inputs']:
    p=pair['path']
    rec=read_identity(BASE/'accepted-c030'/p,accepted_by[p],p)
    if rec:
        if rec['sha256']!=pair['accepted']['sha256']:
            failures.append({'path':p,'failure':'accepted published SHA256 mismatch'})
        accepted.append(rec)

main_path=REC/'main-STATUS.md'
main_data=main_path.read_bytes()
main_status={'path':'STATUS.md','commit':binding['main_status']['observed_commit'],'bytes':len(main_data),'git_blob':hashlib.sha1(('blob %d\0'%len(main_data)).encode()+main_data).hexdigest(),'sha256':hashlib.sha256(main_data).hexdigest()}
if any(main_status[k]!=binding['main_status'][k] for k in ('bytes','git_blob','sha256')):
    failures.append({'path':'main-STATUS.md','failure':'main STATUS identity mismatch'})

# This independent, intentionally overinclusive scan only plans local targets.
# It does not import or execute the unchanged documentation checker.
needed={};unknown=[];dirs=set(plan['prior_directory_targets']);refs=0
docs=[x['path'] for x in tree['tree'] if x['type']=='blob' and Path(x['path']).suffix.lower() in ('.md','.markdown','.html','.htm')]
for name in docs:
    p=SOURCE/name
    if not p.is_file():
        failures.append({'path':name,'failure':'original documentation missing'})
        continue
    txt=p.read_text(encoding='utf-8')
    targets=re.findall(r'\]\(\s*(?:<([^>]+)>|([^\s\)]+))',txt)
    dests=[a or b for a,b in targets]
    dests += [a or b for a,b in re.findall(r'^\s*\[[^\]\n]+\]:\s*(?:<([^>\n]+)>|(\S+))',txt,re.M)]
    dests += re.findall(r'(?:href|src)\s*=\s*[\"\']([^\"\']+)[\"\']',txt,re.I)
    for value in dests:
        v=html.unescape(re.sub(r'\\([^a-zA-Z0-9])',r'\1',value)).strip()
        if not v or v.startswith('//') or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',v):
            continue
        try:u=urlsplit(v)
        except ValueError:continue
        rel=unquote(u.path)
        q=((SOURCE/rel.lstrip('/')) if rel.startswith('/') else (p.parent/rel)).resolve() if rel else p.resolve()
        if not q.is_relative_to(SOURCE.resolve()):continue
        target=q.relative_to(SOURCE.resolve()).as_posix();refs+=1
        if target in by:
            entry=by[target]
            if entry['type']=='tree':dirs.add(target)
            elif not q.is_file():needed[target]=entry
        elif not q.exists():unknown.append({'source':name,'target':value,'resolved':target})

for d in sorted(dirs):
    if d not in by or by[d]['type']!='tree':
        failures.append({'path':d,'failure':'requested directory absent from immutable tree'})
    else:
        (SOURCE/d).mkdir(parents=True,exist_ok=True)

source_map=json.loads((SOURCE/'docs/maintenance/reorganization-2026-10-17/source-map.json').read_text())
for x in source_map['sources']:
    if not (SOURCE/x['destination']).is_file():
        needed[x['destination']]=by.get(x['destination'],{'path':x['destination']})
if needed:
    failures.append({'failure':'known required dependency targets missing','paths':sorted(needed)})

attempts=[json.loads(x) for x in (REC/'acquisition-results.jsonl').read_text().splitlines() if x]
acquisition_failures=[x for x in attempts if x['status']!='exact']
summary={'schema':'ontokin.c058-source-recovery/0.1','observed_at_utc':datetime.now(timezone.utc).isoformat(),'source_commit':'3b82b5bd74495850e08cf8b4f51daca0342f9882','source_tree':tree['sha'],'remote_tree_truncated':tree['truncated'],'remote_files':sum(x['type']=='blob' for x in tree['tree']),'files':len(records),'bytes':sum(x['bytes'] for x in records),'partial_snapshot':True,'native_git_checkout':False,'all_parent_markdown_html_count':len(docs),'all_parent_markdown_html_present':all((SOURCE/x).is_file() for x in docs),'local_runtime_files':sum(x['path'].startswith('ontokin/') for x in records),'source_map_destination_count':len(source_map['sources']),'directory_targets':sorted(dirs),'known_dependency_targets_missing':sorted(needed),'raw_reference_count':refs,'scanner_unknown_targets':unknown,'scanner_qualification':'Preparation-only raw-text scan may overinclude code/example links. The unchanged documentation checker has not been run by this worker.','identity_failures':failures,'acquisition_attempts':len(attempts),'acquisition_failures':acquisition_failures,'acquisition_failure_qualification':'Failures are preserved separately from successful exact recovery and are not validation failures. The cause of HTTP404 failures is unestablished.','accepted_c030':{'commit':binding['accepted_commit'],'tree':accepted_tree['sha'],'files':len(accepted),'inputs':accepted},'main_status':main_status,'archive_whole_file_hashing_only':True,'product_imports':0,'documentation_checker_runs':0,'runtime_test_runs':0,'archive_extractions':0,'python':sys.version,'platform':platform.platform(),'inputs':records}
(REC/'recovered-inputs.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs','accepted_c030','scanner_unknown_targets','directory_targets','acquisition_failures')},indent=2))
print(json.dumps({'accepted_c030_files':len(accepted),'acquisition_failure_count':len(acquisition_failures),'scanner_unknown_target_count':len(unknown)}))
sys.exit(bool(failures))
