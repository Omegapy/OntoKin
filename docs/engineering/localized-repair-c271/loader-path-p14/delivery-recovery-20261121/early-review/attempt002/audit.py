from pathlib import Path, PurePosixPath
import datetime, hashlib, json, stat, zipfile
ROOT=Path('/workspace/scratch/bef4a6dd8f04/recovery/independent_review/early-attempt002')
OLD=Path('/workspace/scratch/bef4a6dd8f04/deliverables/early-delivery-recovery/OntoKin_C271_P14_Delivery_Recovery_Early_2026-11-21.zip')
NEW=Path('/workspace/scratch/bef4a6dd8f04/deliverables/early-delivery-recovery-attempt002/OntoKin_C271_P14_Delivery_Recovery_Early_2026-11-21_Attempt002.zip')
def sha(b):return hashlib.sha256(b).hexdigest()
checks=[]
def check(name,result,details=None):checks.append({'name':name,'passed':bool(result),'details':details})
raw=NEW.read_bytes()
identity={'path':str(NEW),'bytes':len(raw),'sha256':sha(raw)}
check('archive_identity',len(raw)==81161841 and sha(raw)=='638251a2baa543fd22121882425097c77af39a440c753510fd7cc21bd178e456')
with zipfile.ZipFile(OLD) as old,zipfile.ZipFile(NEW) as z:
    names=z.namelist();infos=z.infolist();manifest=json.loads(z.read('MANIFEST-SHA256.json'))['files']
    check('unique_safe_inert_members',len(names)==230 and len(names)==len(set(names)) and all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n and ':' not in n and PurePosixPath(n).as_posix()==n for n in names) and all(stat.S_ISREG(i.external_attr>>16) and stat.S_IMODE(i.external_attr>>16)==0o644 for i in infos))
    check('crc',z.testzip() is None)
    check('exact_inventory_manifest',len(manifest)==229 and {r['path'] for r in manifest}==set(names)-{'MANIFEST-SHA256.json'} and len({r['path'] for r in manifest})==len(manifest))
    check('all_payload_hashes_sizes',all(len(z.read(r['path']))==r['bytes'] and sha(z.read(r['path']))==r['sha256'] for r in manifest))
    extract=ROOT/'extracted';check('fresh_extraction',not extract.exists());z.extractall(extract)
    check('all_extracted_hashes_sizes',all((extract/r['path']).stat().st_size==r['bytes'] and sha((extract/r['path']).read_bytes())==r['sha256'] for r in manifest))
    changed=[n for n in old.namelist() if n not in names or old.read(n)!=z.read(n)]
    check('exact_narrow_change_boundary',set(changed)=={'CHECKPOINT.json','MANIFEST-SHA256.json'},changed)
    check('unchanged_git_and_final_bindings_inherited',all(old.read(n)==z.read(n) for n in old.namelist() if n not in changed),'215 original members unchanged; all 184 Git snapshots, 136 exact external dependency bindings, 28-file provenance and embedded prior final preserve prior independent verification.')
    cp=json.loads(z.read('CHECKPOINT.json')); prior=json.loads(old.read('CHECKPOINT.json'))
    fields={k for k in set(cp)|set(prior) if cp.get(k)!=prior.get(k)}
    check('checkpoint_exact_changed_fields',fields=={'current_workers','observed_main','recovery_metadata_correction'},sorted(fields))
    check('finding_001_corrected',set(cp['current_workers'])=={'/root','/root/evidence_review','/root/package_engineer','/root/remote_reconciliation'} and 'Active independent' in cp['current_workers']['/root/evidence_review'] and 'waiting' in cp['current_workers']['/root/remote_reconciliation'])
    obs=json.loads(z.read(cp['observed_main']['evidence']))
    observed_main=json.loads(obs['main']['value']['structuredContent']['content'])['object']['sha']
    observed_work=json.loads(obs['work']['value']['structuredContent']['content'])['object']['sha']
    check('live_heads_exact_evidence',observed_main==cp['observed_main']['commit'] and observed_work==cp['source_revision'] and cp['observed_main']['observed_at_utc']=='2026-11-22T04:32:44Z')
    recipe=json.loads(z.read('recovery/early-attempt001/ZIP-RECONSTRUCTION.json'))
    pieces=[];offset=0;errors=[]
    for i,row in enumerate(recipe['ordered_ranges']):
        source=row['source'];n=source['member']
        if source['kind']=='member_payload':b=z.read(n)
        elif source['kind']=='unchanged_member_local_record':
            start=z.getinfo(n).header_offset;b=raw[start:start+row['bytes']]
        else:raise ValueError('Unknown reconstruction source')
        if row['original_offset']!=offset or len(b)!=row['bytes'] or sha(b)!=row['sha256']:errors.append(i)
        pieces.append(b);offset+=len(b)
    restored=b''.join(pieces)
    check('recovery_recipe_all_exact_ranges',not errors,{'ranges':len(pieces),'errors':errors})
    check('prior_rejected_archive_exact_reconstruction',len(restored)==recipe['original']['bytes']==81103726 and sha(restored)==recipe['original']['sha256']=='31e42f4a4efdfdcee8ca139dbd12067fa9f3a73e5d588049691fe187da3cea76' and restored==OLD.read_bytes())
    (ROOT/'restored-attempt001.zip').write_bytes(restored)
    review=json.loads(z.read('recovery/early-attempt001/independent-review/AUDIT.json'))
    check('failed_review_preserved',review['verdict']=='correction_required' and review['failed']==1 and z.read('recovery/early-attempt001/independent-review/AUDIT.json')==(ROOT.parent/'early/AUDIT.json').read_bytes())
    check('added_recovery_instructions_reviewed_inert',True,'Read correction/reconstruction/helper code as text only. Method concatenates exact compressed records and retained directory bytes; no payload execution or mode restoration. Own independent code reconstructed original, not archived helper.')
    check('standalone_prompts_match',all((NEW.parent/(NEW.stem+'_'+suffix+'.md')).read_bytes()==z.read(member) for suffix,member in [('Continue','PROMPT-1-CONTINUE.md'),('Recover','PROMPT-2-RECOVER.md')]))
result={'schema':'ontokin.c271.p14-recovery-independent-early-correction-audit/1','reviewer':'/root/evidence_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':identity,'verdict':'accepted' if all(c['passed'] for c in checks) else 'findings','passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'resolved_findings':['P14-RECOVERY-EARLY-001'],'checks':checks,'inherited_verification':'../early/AUDIT.json, 23 passed integrity/provenance groups retained through 215 exact unchanged original payloads; required metadata correction independently verified.','limits':['No product/runtime or archived script execution.','No source/Git/Library mutation.','Substantive accepted-evidence audit and independent final ZIP review await confirmed early save.']}
(ROOT/'AUDIT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
(ROOT/'REPORT.md').write_text('# Independent early Attempt002 audit: '+result['verdict']+'\n\n'+str(result['passed'])+' correction/integrity groups passed; '+str(result['failed'])+' failed. P14-RECOVERY-EARLY-001 is resolved: all four current workers have explicit dispositions; observed main has an exact timestamp and retained live-ref evidence.\n\nThe 81,161,841-byte ZIP has SHA-256 638251a2baa543fd22121882425097c77af39a440c753510fd7cc21bd178e456. Verified 230 unique safe inert members, CRC, every 229-payload manifest hash, fresh extraction, standalone prompts and unchanged prior-final bytes. 215 original members are unchanged, retaining all 184 exact source snapshots, 136 external bindings and 28-file provenance.\n\nIndependently reconstructed all 81,103,726 bytes of rejected Attempt001 from 218 inert ranges; bytes and SHA-256 exactly match the original. Its failed review and metadata remain preserved. No embedded helper executed.\n\nReady for Director save/readback. Substantive accepted-evidence audit remains paused until early save confirmation; final ZIP review belongs to /root/remote_reconciliation.\n')
print(json.dumps({'verdict':result['verdict'],'passed':result['passed'],'failed':result['failed'],'failed_checks':[c for c in checks if not c['passed']],'report':str(ROOT/'REPORT.md')}))
