from pathlib import Path
from urllib.parse import urlsplit,unquote
import re,html,json
ROOT=Path('/workspace/scratch/813fb8a53b1a'); SNAP=ROOT/'snapshot'
tree=json.loads((ROOT/'evidence/parent-tree.json').read_text())['tree']; bypath={x['path']:x for x in tree}
needed={}; unknown=[]; dirs=set(); refs=0
for p in SNAP.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in ('.md','.markdown','.html','.htm'): continue
    txt=p.read_text()
    targets=re.findall(r'\]\(\s*(?:<([^>]+)>|([^\s\)]+))',txt)
    dests=[a or b for a,b in targets]
    dests += [a or b for a,b in re.findall(r'^\s*\[[^\]\n]+\]:\s*(?:<([^>\n]+)>|(\S+))',txt,re.M)]
    dests += re.findall(r'(?:href|src)\s*=\s*[\"\']([^\"\']+)[\"\']',txt,re.I)
    for value in dests:
        v=html.unescape(re.sub(r'\\([^a-zA-Z0-9])',r'\1',value)).strip()
        if not v or v.startswith('//') or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',v): continue
        try: u=urlsplit(v)
        except ValueError: continue
        rel=unquote(u.path); q=((SNAP/rel.lstrip('/')) if rel.startswith('/') else (p.parent/rel)).resolve() if rel else p.resolve()
        if not q.is_relative_to(SNAP.resolve()): continue
        name=q.relative_to(SNAP.resolve()).as_posix(); refs+=1
        if name in bypath:
            e=bypath[name]
            if e['type']=='tree':dirs.add(name)
            elif not q.exists():needed[name]=e
        elif not q.exists():unknown.append({'source':p.relative_to(SNAP).as_posix(),'target':value,'resolved':name})
manifest=json.loads((SNAP/'docs/maintenance/reorganization-2026-10-17/source-map.json').read_text())
for s in manifest['sources']:
    n=s['destination']
    if not (SNAP/n).exists():needed[n]=bypath[n]
for d in dirs:(SNAP/d).mkdir(parents=True,exist_ok=True)
out={'scope':'Preparation-only independent link scan; unchanged checker has not run. Raw text scan may overinclude links inside code examples.','needed':sorted(needed.values(),key=lambda x:x['path']),'directory_targets':sorted(dirs),'unresolved_scanner_targets':unknown,'raw_reference_count':refs}
(ROOT/'reviews/evidence/dependency-plan.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'needed':len(needed),'bytes':sum(x['size'] for x in needed.values()),'directory_targets':len(dirs),'scanner_unresolved':len(unknown),'large':[{'path':x['path'],'size':x['size']} for x in sorted(needed.values(),key=lambda x:x['size'],reverse=True)[:20]]},indent=2))
