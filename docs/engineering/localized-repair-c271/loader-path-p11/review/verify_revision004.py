"""Focused independent static review of the frozen candidate002 -> 004 delta.

No production code is imported, no logical host path is accessed, and no author
helper is executed. Context checks concern supplied inert observations only.
"""
from copy import deepcopy
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

base=Path('/workspace/scratch/2ad494d5da19/session_evidence')
author=base/'loader_design'
old=author/'candidate002'
new=author/'candidate004'
out=base/'design_review/candidate004'
checks=[]


def load(p):
    return json.loads(p.read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check(name, ok, details=None):
    checks.append({'check':name,'pass':bool(ok),'details':details})


def bound(p, row):
    raw=p.read_bytes(); s=p.lstat()
    return (stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_nlink==1 and len(raw)==row['size_bytes']
            and sha(raw)==row['sha256'] and ('mode' not in row or oct(stat.S_IMODE(s.st_mode))==row['mode']))


om=load(old/'CANDIDATE-MANIFEST.json'); nm=load(new/'CANDIDATE-MANIFEST.json')
check('Exact original immutable manifest',sha((old/'CANDIDATE-MANIFEST.json').read_bytes())=='563e84cc83f31a202cc0eead9102b66b08050ea011dfbbf4ed6fc19db318c8f4')
check('Exact requested final immutable manifest',sha((new/'CANDIDATE-MANIFEST.json').read_bytes())=='e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de' and (new/'CANDIDATE-MANIFEST.json').stat().st_size==35041)
for row in om['payload']:
    check('Preserved002 payload/'+row['path'],bound(old/row['path'],row))
for row in om['supporting_files']:
    check('Preserved002 support/'+row['path'],bound(old/row['path'],row))
old_rows={r['path']:r for r in om['payload']}; new_rows={r['path']:r for r in nm['payload']}
removed=sorted(set(old_rows)-set(new_rows)); added=sorted(set(new_rows)-set(old_rows))
changed=sorted(p for p in old_rows.keys()&new_rows.keys() if old_rows[p]!=new_rows[p])
unchanged=sorted(p for p in old_rows.keys()&new_rows.keys() if old_rows[p]==new_rows[p])
revision=load(new/'REVISION-004.json')
check('Revision names exact changed previous payloads',changed==sorted(r['path'] for r in revision['changed_previous_payloads']))
check('Revision bindings equal both exact manifests',all(r['old']==old_rows[r['path']] and r['new']==new_rows[r['path']] for r in revision['changed_previous_payloads']))
check('Revision exact unchanged inventory',unchanged==sorted(r['path'] for r in revision['unchanged_previous_payloads']) and all(r==old_rows[r['path']]==new_rows[r['path']] for r in revision['unchanged_previous_payloads']))
check('Revision exact added inventory and no deletions',not removed and set(added)=={r['path'] for r in revision['added_payloads_before_revision_records']}|{'REVISION-004.json','REVISION-004.diff'})

of=load(old/'FIXTURE-MANIFEST.json'); nf=load(new/'FIXTURE-MANIFEST.json')
ofs={r['path']:r for r in of['files']}; nfs={r['path']:r for r in nf['files']}
changed_fixtures=sorted(p for p in ofs if p in nfs and ofs[p]!=nfs[p])
added_fixtures=sorted(set(nfs)-set(ofs))
expected_additions=['N75_expansion_129_components','N76_nonascii_origin','N77_nonascii_variant_suffix','P09_expansion_128_components']
check('Only two existing fixture contexts changed',changed_fixtures==['fixture_inputs/N69_expansion_4097_bytes.json','fixture_inputs/P07_expansion_4096_bytes.json'])
check('Exactly four context fixtures added',added_fixtures==sorted('fixture_inputs/'+i+'.json' for i in expected_additions) and not set(ofs)-set(nfs))
check('All26 ELF and8 auxv bytes unchanged',all(ofs[p]==nfs[p] for p in ofs if p.endswith('.bin')) and sum(p.endswith('.bin') for p in ofs)==34)
oe=load(old/'EXPECTATIONS.json'); ne=load(new/'EXPECTATIONS.json')
projection=deepcopy(ne); projection['cases']={k:ne['cases'][k] for k in oe['cases']}
projected=(json.dumps(projection,indent=2,sort_keys=True)+'\n').encode()
check('All93 old expectation records equal',len(oe['cases'])==93 and all(ne['cases'][k]==v for k,v in oe['cases'].items()))
check('Old oracle projection is byte-identical to old complete document',projected==(old/'EXPECTATIONS.json').read_bytes(),{'projection_sha256':sha(projected),'old_sha256':sha((old/'EXPECTATIONS.json').read_bytes())})
check('Only four new oracle entries',sorted(set(ne['cases'])-set(oe['cases']))==expected_additions and len(ne['cases'])==97)
check('No withdrawn P08/N74 case, asset or reader route',not any(p.startswith(('P08','N74')) for p in ne['cases']) and not any('variant_reader' in p for p in nfs) and not any(r['route']=='bounded_variant_read' for r in nf['cases']))
oc=load(old/'CONSTRUCTION.json'); nc=load(new/'CONSTRUCTION.json')
check('All original construction bytes/layouts unchanged', {k:v for k,v in oc.items() if k!='constructor'}=={k:v for k,v in nc.items() if k!='constructor'})
check('Construction names exact distinct004 constructor', nc['constructor']['path']=='../build_controls_attempt004.py' and nc['constructor']['sha256']==sha((author/'build_controls_attempt004.py').read_bytes()))

# Independently create a text diff for the exact changed normative records.
paths=revision['diff_scope']['paths']
diff=''.join(''.join(difflib.unified_diff((old/p).read_text().splitlines(keepends=True),(new/p).read_text().splitlines(keepends=True),fromfile='candidate002/'+p,tofile='candidate004/'+p)) for p in paths)
(out/'INDEPENDENT-DOCUMENT-DIFF.diff').write_text(diff)
check('Author text diff equals independently generated diff',diff==(new/'REVISION-004.diff').read_text())

contexts={i:load(new/'fixture_inputs'/str(i+'.json')) for i in ['P07_expansion_4096_bytes','N69_expansion_4097_bytes',*expected_additions]}
boundary_facts={}


def context_coherence(ident,c):
    subject,origin,expanded=c['subject']['path'],c['origin_claim'],c['expanded_claim'][0]
    guards={g['path']:g for g in c['guards']}
    required={str(p) for s in [subject,expanded] for p in PurePosixPath(s).parents}|{expanded}
    check(ident+': exact full ancestor guard set',set(guards)==required and len(guards)==len(c['guards']),{'required':len(required),'supplied':len(guards)})
    check(ident+': coherent subject kernel and derived directory',c['kernel']['proc_exe_path']==subject and c['kernel']['proc_file_identity']=={k:c['subject'][k] for k in ['device','inode']} and origin==str(PurePosixPath(subject).parent) and expanded==str(PurePosixPath(origin).parent/'lib'))
    check(ident+': all guarded dirs remain inert nonsymlink logical states',all(g['kind']=='directory' and g['mode']=='0o755' and g['target'] is None for g in guards.values()))
    check(ident+': expanded directory identity matches guard',all(c['search_directories'][expanded][k]==guards[expanded][k] for k in ['device','inode','mode']))
    check(ident+': coherent exact variant suffix inventory',[v['suffix'] for v in c['variants']]==c['variant_review']['suffixes'] and c['variant_review']['suffixes']==sorted(set(c['variant_review']['suffixes'])) and all(v['path']==str(PurePosixPath(expanded)/v['suffix']) for v in c['variants']))
    for v in c['variants']:
        if v['state']=='directory':
            check(ident+': present variant '+v['suffix'],v['path'] in c['search_directories'])
        else:
            a=c['absence_guards'][v['absent_at']]
            parent=str(PurePosixPath(v['absent_at']).parent)
            check(ident+': coherent absence '+v['suffix'],a['absent'] is True and a['parent']==parent and parent in guards and a['parent_device']==guards[parent]['device'] and a['parent_inode']==guards[parent]['inode'] and (v['absent_at']==v['path'] or v['path'].startswith(v['absent_at']+'/')))
    check(ident+': complete unchanged synthetic needed union',c['needed_names_claim']==sorted({n for i in c['closure_images'] for n in i['needed']}) and not any(n in d['entries'] for d in c['search_directories'].values() for n in c['needed_names_claim']))


for ident,c in contexts.items():
    context_coherence(ident,c)
    paths={'subject':c['subject']['path'],'kernel':c['kernel']['proc_exe_path'],'origin':c['origin_claim'],'raw':c['origin_claim']+'/../lib'}
    paths.update({'expanded/'+str(i):p for i,p in enumerate(c['expanded_claim'])})
    paths.update({'variant/'+str(i):v['path'] for i,v in enumerate(c['variants'])})
    paths.update({'guard/'+str(i):v['path'] for i,v in enumerate(c['guards'])})
    paths.update({'search/'+str(i):v for i,v in enumerate(c['search_directories'])})
    paths.update({'absence/'+str(i):v for i,v in enumerate(c['absence_guards'])})
    dimensions={name:{'bytes':len(p.encode('utf-8')),'components':len(PurePosixPath(p).parts),'ascii':p.isascii()} for name,p in paths.items()}
    b={'raw_bytes':dimensions['raw']['bytes'],'raw_components_including_root':dimensions['raw']['components'],
       'max_supplied_bytes':max(v['bytes'] for k,v in dimensions.items() if k!='raw'),
       'max_supplied_components_including_root':max(v['components'] for k,v in dimensions.items() if k!='raw'),
       'supplied_guard_count':len(c['guards']),'required_guard_count':len({str(p) for s in [c['subject']['path'],*c['expanded_claim']] for p in PurePosixPath(s).parents}|set(c['expanded_claim'])),
       'over_byte_limit':[k for k,v in dimensions.items() if v['bytes']>4096],
       'over_component_limit':[k for k,v in dimensions.items() if v['components']>128],
       'nonascii_paths':[k for k,v in dimensions.items() if not v['ascii']]}
    boundary_facts[ident]=b
    if ident.startswith(('P07','N69','P09','N75')):
        check(ident+': explicit base-only synthetic suffix model',c['variant_review']['suffixes']==[''] and c['variant_review']['completeness']=='synthetic_declared_complete')
        check(ident+': independent dimensions equal author revision',all(b[k]==v for k,v in revision['boundary_measurements'][ident].items()))
        check(ident+': other finite cardinalities fit',len(c['needed_names_claim'])<=4096 and len(c['variants'])<=128 and len(c['needed_names_claim'])*sum(v['state']=='directory' for v in c['variants'])<=32768)
        check(ident+': ASCII path domain',not b['nonascii_paths'])
    if ident.startswith('P07'):
        check(ident+': isolated exact byte boundary positive',b['raw_bytes']==4096 and b['max_supplied_bytes']<4096 and not b['over_byte_limit'] and not b['over_component_limit'] and ne['cases'][ident]['outcome']=='rule_acceptance')
    elif ident.startswith('N69'):
        check(ident+': only raw expansion is over byte limit',b['raw_bytes']==4097 and b['over_byte_limit']==['raw'] and not b['over_component_limit'] and ne['cases'][ident]['rule_id']=='LP-BOUND')
    elif ident.startswith('P09'):
        check(ident+': isolated exact component boundary positive',b['raw_components_including_root']==128 and b['max_supplied_components_including_root']<128 and not b['over_byte_limit'] and not b['over_component_limit'] and ne['cases'][ident]['outcome']=='rule_acceptance')
    elif ident.startswith('N75'):
        check(ident+': only raw expansion is over component limit',b['raw_components_including_root']==129 and b['over_component_limit']==['raw'] and not b['over_byte_limit'] and ne['cases'][ident]['rule_id']=='LP-BOUND')
    elif ident.startswith('N76'):
        check(ident+': non-ASCII origin is the isolated new policy cause',not c['origin_claim'].isascii() and all(s.isascii() for s in c['variant_review']['suffixes']) and not b['over_byte_limit'] and not b['over_component_limit'] and ne['cases'][ident]['rule_id']=='LP-PATH-ASCII' and ne['cases'][ident]['stage']=='new_path_policy')
        original=load(new/'fixture_inputs/P01_nonselecting_base.json')
        def rename(x):
            if isinstance(x,str):return x.replace('/fixture/app','/fixture/caf\u00e9')
            if isinstance(x,list):return [rename(y) for y in x]
            if isinstance(x,dict):return {rename(k):rename(v) for k,v in x.items()}
            return x
        check(ident+': context differs only by coherent non-ASCII path relocation',c==rename(original))
    elif ident.startswith('N77'):
        check(ident+': non-ASCII suffix is the isolated new policy cause',c['origin_claim'].isascii() and c['variant_review']['suffixes']==['','h\u00e1rdware'] and not b['over_byte_limit'] and not b['over_component_limit'] and ne['cases'][ident]['rule_id']=='LP-PATH-ASCII' and ne['cases'][ident]['stage']=='new_path_policy')

retention=load(author/'ATTEMPT003-RETENTION.json')
for row in retention['preserved_payload']+retention['preserved_support']:
    p=author/row['path']
    check('Retained003/'+row['path'],p.resolve().is_relative_to(author) and bound(p,row))
retained_names={r['path'] for r in retention['preserved_payload']}
actual_names={str(p.relative_to(author)) for p in (author/'candidate003').rglob('*') if p.is_file() or p.is_symlink()}
check('Withdrawn003 exact complete inventory',retained_names==actual_names and len(retained_names)==148 and len(retention['preserved_support'])==12)
check('Withdrawn003 explicit unaccepted historical state',retention['state']=='withdrawn_before_independent_freeze' and retention['frozen_for_history_only'] is True and retention['product_execution'] is False)
we=load(author/'candidate003/EXPECTATIONS.json')['cases']
check('Withdrawn reader cases retained only in003',{'P08_variant_reader_4mib','N74_variant_reader_over_bound'}<=set(we) and not {'P08_variant_reader_4mib','N74_variant_reader_over_bound'}&set(ne['cases']))

decision=(new/'DECISION.md').read_text(); contract=(new/'CONTROL-CONTRACT.md').read_text(); materialization=(new/'MATERIALIZATION.md').read_text()
check('Final normative decision explicitly inherits16MiB reader',"maximum=LIMITS['document_bytes']" in decision and 'unchanged 16 MiB allowance' in decision and 'No separate byte cap, private byte-reader seam' in decision)
check('Final closed-shape and canonical guards remain explicit','requires exact canonical serialization' in decision and 'new variant-object shape is checked after' in decision)
check('Final ASCII and before-reduction component semantics explicit','Preserve the old `_absolute` character-count and path behavior unchanged' in decision and 'including the leading `/` as one component and each literal `..` before reduction' in decision)
check('Final materialization procedure is frozen and limits authority','independently recorded SHA-256' in materialization and 'exclusive creation and no overwrite' in materialization and 'outside the frozen candidate payload' in materialization and 'Preserve every `.bin` as nonexecutable' in materialization and "does not change the operational Python's fixed hash, size, path or mode" in materialization)
check('Futurescope remains one existing production file and one new test',load(new/'FUTURE-SURFACE.json')['proposed_production_edit_paths']==['prototypes/static_tray_v01/current_host_inspection_v01.py'] and load(new/'FUTURE-SURFACE.json')['proposed_new_test_paths']==['tests/test_current_host_loader_path_v01.py'] and load(new/'FUTURE-SURFACE.json')['implementation_authorized_in_p11'] is False)

report={'schema':'ontokin.c271.p11-independent-revision-check/1','candidate':'candidate004','manifest_sha256':sha((new/'CANDIDATE-MANIFEST.json').read_bytes()),
        'check_count':len(checks),'passed':sum(r['pass'] for r in checks),'failed':[r for r in checks if not r['pass']],
        'payload_delta':{'changed':changed,'added':added,'removed':removed,'unchanged_count':len(unchanged)},
        'fixture_delta':{'changed':changed_fixtures,'added':added_fixtures},'old_expectation_projection_sha256':sha(projected),
        'boundary_measurements':boundary_facts,'withdrawn003_payloads':len(retained_names),'withdrawn003_supports':len(retention['preserved_support']),
        'product_calls':0,'host_observations':0,'target_executions':0,
        'claim':'Exact delta, correction adequacy and failure preservation; no implemented profile or host qualification claim.'}
(out/'REVISION-CHECKS.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
(out/'REVISION-REVIEW.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))
raise SystemExit(1 if report['failed'] else 0)
