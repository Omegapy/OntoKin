from pathlib import Path, PurePosixPath
import ast, collections, datetime, hashlib, json, os, platform, stat, subprocess, sys, zipfile

ROOT=Path('/workspace/scratch/bef4a6dd8f04/recovery/independent_review/implementation')
REPO=Path('/workspace/scratch/bef4a6dd8f04/OntoKin')
SOURCE='e26dc6369a8d6ba88ea779b26a8c655121ae5dbc'
BASELINE='4023a878ccc9980726e3b56102b41faa51be0eb1'
STARTUP='ad6e0c8e32673c16ed4d75d5876fe36fd5747b29'
PHASE='docs/engineering/localized-repair-c271/loader-path-p14/'
ARCHIVE=ROOT/'IMPLEMENTATION-EVIDENCE.zip'
checks=[]; details={}
def sha(b):return hashlib.sha256(b).hexdigest()
def check(name,yes,detail=None):checks.append({'name':name,'passed':bool(yes),'detail':detail})
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def blob(path,rev=SOURCE):return git('show',rev+':'+path)
def dump(name,d): (ROOT/name).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def tree(rev):
    answer={}
    for entry in git('ls-tree','-r','-z',rev).split(b'\0'):
        if entry:
            attrs,p=entry.split(b'\t',1);mode,kind,oid=attrs.decode().split();answer[p.decode()]={'mode':mode,'kind':kind,'oid':oid}
    return answer

source_tree=tree(SOURCE);base_tree=tree(BASELINE);startup_tree=tree(STARTUP)
desc=json.loads(blob(PHASE+'evidence/IMPLEMENTATION-EVIDENCE.json'))
parts=[];part_checks=[]
for row in desc['parts']:
    path=PHASE+'evidence/'+row['file'];b=blob(path)
    part_checks.append({'path':path,'git_blob':source_tree[path]['oid'],'bytes':len(b),'sha256':sha(b),'passed':len(b)==row['bytes'] and sha(b)==row['sha256']})
    parts.append(b)
raw=b''.join(parts)
identity={'bytes':len(raw),'sha256':sha(raw),'source_revision':SOURCE,'source_tree':git('rev-parse',SOURCE+'^{tree}').decode().strip(),'path':str(ARCHIVE)}
check('three_exact_git_parts',len(parts)==3 and all(r['passed'] for r in part_checks),part_checks)
check('exact_lossless_archive',len(raw)==desc['archive_bytes']==17386151 and sha(raw)==desc['archive_sha256']=='72fa3117b84eafdd1384a2ee8cc9a957bcad8b20ec1b9f90dc824135af66eb13' and raw==ARCHIVE.read_bytes(),identity)
with zipfile.ZipFile(ARCHIVE) as z:
    names=z.namelist();infos=z.infolist();manifest=json.loads(z.read('MANIFEST-SHA256.json'))
    check('safe_unique_inert_archive',len(names)==21409 and len(names)==len(set(names)) and all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n and ':' not in n and str(PurePosixPath(n))==n for n in names) and all(stat.S_ISREG(i.external_attr>>16) and stat.S_IMODE(i.external_attr>>16)==0o644 for i in infos))
    check('exact_manifest_inventory',len(manifest)==21408 and set(manifest)==set(names)-{'MANIFEST-SHA256.json'})
    mismatches=[]
    for n,r in manifest.items():
        b=z.read(n)  # zipfile also verifies each member's CRC while reading.
        if len(b)!=r['bytes'] or sha(b)!=r['sha256']:mismatches.append(n)
    check('all21408_payload_hashes_sizes_and_crc',not mismatches,{'payloads':len(manifest),'uncompressed_bytes':sum(i.file_size for i in infos),'mismatches':mismatches})
    links=json.loads(z.read('INERT-SYMLINKS.json'))
    check('symlinks_retained_as_inert_records',len(links)==30 and all(r['path'] not in names for r in links),'30 link descriptions retained; no live symlink member extracted or created.')

    published=json.loads(blob(PHASE+'IMPLEMENTATION-OUTCOME.json'))
    production=blob('prototypes/static_tray_v01/current_host_inspection_v01.py');adapter=blob('tests/test_current_host_loader_path_v01.py')
    check('exact_accepted_production_and_adapter',len(production)==published['source']['bytes']==183913 and sha(production)==published['source']['sha256']=='a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4' and len(adapter)==published['adapter']['bytes']==36940 and sha(adapter)==published['adapter']['sha256']=='cf521b4c14d6488c457a942c1fc151b3483729ec26c6c24e721f6ce05d6b2066' and production==z.read('implementation/candidate003.py')==z.read('review/implementation-attempt002/module.py') and adapter==z.read('review/implementation-attempt002/adapter.py'))
    outcome_raw=z.read('control-adapter/run002/OUTCOME.json');outcome=json.loads(outcome_raw)
    review_raw=z.read('review/implementation-attempt002/AUDIT.json');review=json.loads(review_raw)
    check('published_outcome_review_exact_bindings',len(outcome_raw)==published['runtime_run']['bytes'] and sha(outcome_raw)==published['runtime_run']['sha256']==review['runtime_evidence']['sha256'] and len(review_raw)==published['independent_review']['bytes'] and sha(review_raw)==published['independent_review']['sha256'] and z.read('review/implementation-attempt002/REPORT.md')==blob(PHASE+'evidence/INDEPENDENT-IMPLEMENTATION-REVIEW.md'))
    freeze_raw=z.read('control-adapter/FREEZE-002.json');freeze=json.loads(freeze_raw);started=json.loads(z.read('control-adapter/run002/RUN-STARTED.json'))
    check('freeze_command_run_identity',sha(freeze_raw)=='d92a677c7f1e24014cf8e9fd22628d2664f2ed0b1ea368ddcfcd75cc6ac675d3' and freeze_raw==z.read('control-adapter/run002/FROZEN-INPUTS.json') and outcome['argv'][outcome['argv'].index('--freeze-sha256')+1]==sha(freeze_raw) and started['argv']==outcome['argv'] and freeze['source_identity']==outcome['source_identity'] and outcome['source_identity']['head']==STARTUP)

    run_inputs={r['source']['path']:r for r in outcome['frozen_source_files']}
    frozen_checks=[]
    for row in freeze['files']:
        path=row['path'];run=run_inputs[path];snap='control-adapter/run002/frozen-inputs/'+run['snapshot'];stored=z.read(snap)
        if '/OntoKin/' in path:
            relative=path.split('/OntoKin/',1)[1];current=blob(relative);mode='0o755' if source_tree[relative]['mode']=='100755' else '0o644';binding={'git_path':relative,'git_blob':source_tree[relative]['oid']}
        else:
            relative=path.split('/p14-session/',1)[1];current=z.read(relative);mode=manifest[relative]['original_mode'];binding={'archive_path':relative}
        ok=(len(stored)==row['bytes']==run['source']['bytes'] and sha(stored)==row['sha256']==run['source']['sha256'] and stored==current and mode==row['mode']==run['source']['mode'])
        frozen_checks.append({'original_path':path,'snapshot':snap,'bytes':len(stored),'sha256':sha(stored),'binding':binding,'passed':ok})
    check('all172_frozen_inputs_exact_at_published_source',len(frozen_checks)==172 and all(r['passed'] for r in frozen_checks),{'repository_inputs':sum('git_path' in r['binding'] for r in frozen_checks),'helper_inputs':sum('archive_path' in r['binding'] for r in frozen_checks),'mismatches':[r for r in frozen_checks if not r['passed']]})
    dump('FROZEN-INPUT-BINDINGS.json',frozen_checks)
    post=outcome['frozen_input_postflight']
    check('all172_postflight_unchanged',len(post)==172 and {r['path'] for r in post}==set(run_inputs) and all(r['matches_frozen'] for r in post))
    oldfreeze=json.loads(z.read('control-adapter/FREEZE-001.json'))
    f1={r['path']:r for r in oldfreeze['files']};f2={r['path']:r for r in freeze['files']}
    fdelta=[p for p in f1 if f1[p]!=f2.get(p)]
    check('candidate003_rerun_exact_input_delta',set(f1)==set(f2) and fdelta==['/workspace/scratch/29fbc446c948/OntoKin/prototypes/static_tray_v01/current_host_inspection_v01.py'],fdelta)
    runner=z.read('control-adapter/run_guarded.py')
    check('exact_executed_and_reviewed_runner',sha(runner)=='7f67ceb77a3b72c85c269ce5abd40e6190c3cbc6b2a7f8c3c149ddf8fd9522b2' and runner==z.read('review/implementation-attempt002/run_guarded.py'))
    imports=[n.module if isinstance(n,ast.ImportFrom) else a.name for n in ast.walk(ast.parse(runner)) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in (n.names if isinstance(n,ast.Import) else [None])]
    check('command_environment_and_dependencies_established',outcome['argv'][1:4]==['-I','-S','-B'] and outcome['cohort']=='all' and outcome['environment']['PATH']=='/usr/bin:/bin' and outcome['environment']['TZ']=='UTC' and outcome['environment_restored'] and set(i.split('.')[0] for i in imports)<=sys.stdlib_module_names,'Read guarded runner in full as text; exact environment equality and isolated/no-site/no-bytecode flags checked before execution. Standard-library runner; repository/dependency-lock/test/helper identities are among the172 exact frozen inputs.')
    python_path=Path(outcome['python']['binding']['path']);current_python={'version':sys.version,'executable':str(Path(sys.executable).resolve()),'bytes':python_path.stat().st_size,'sha256':hashlib.file_digest(python_path.open('rb'),'sha256').hexdigest(),'uname':list(os.uname()),'platform':platform.platform()}
    check('applicable_python_environment_unchanged',current_python['version']==outcome['python']['version'] and current_python['bytes']==outcome['python']['binding']['bytes'] and current_python['sha256']==outcome['python']['binding']['sha256'] and current_python['uname']==outcome['python']['uname'],current_python)
    dump('COMMAND-ENVIRONMENT.json',{'historical_command':outcome['argv'],'historical_cwd':outcome['cwd'],'historical_environment':outcome['environment'],'historical_python':outcome['python'],'current_python_read_only_observation':current_python,'runtime_execution_this_review':'not_run','interpretation':'Historical finite results reused for identical implementation/input/dependency/environment identities; not a new runtime test claim.'})

    selected=json.loads(z.read('control-adapter/run002/SELECTED-METHODS.json'));methods=json.loads(z.read('control-adapter/run002/METHOD-RESULTS.json'));events=[json.loads(b) for b in z.read('control-adapter/run002/METHOD-EVENTS.jsonl').splitlines()]
    expected_counts={'tests.test_current_host_loader_path_v01':96,'tests.test_current_host_inspection_v01':135,'tests.test_current_host_elf_mapping_v01':40}
    check('exact271_runtime_method_results',len(methods)==271 and len({r['id'] for r in methods})==271 and all(r['status']=='passed' for r in methods) and [r['id'] for r in methods]==selected['ids'] and selected['counts']==outcome['cohort_counts']==expected_counts and not selected['loader_errors'] and outcome['tests_run']==271 and outcome['passed'] and outcome['state']=='completed' and outcome['exit_code']==0 and all(outcome[k]==0 for k in ['failures','errors','skipped','expectedFailures','unexpectedSuccesses']))
    check('method_journal_complete',len(events)==542 and [r['id'] for r in events if r['event']=='start']==selected['ids'] and [r['id'] for r in events if r['event']=='finish']==selected['ids'] and all(r['status']=='passed' for r in events if r['event']=='finish') and not json.loads(z.read('control-adapter/run002/METHOD-SCOPE-RESULTS.json')))
    log_checks=[]
    for row in outcome['logs']:
        p='control-adapter/run002/'+Path(row['path']).name;b=z.read(p);log_checks.append(len(b)==row['bytes'] and sha(b)==row['sha256'])
    check('exact_full_run_logs',all(log_checks) and b'Ran 271 tests' in z.read('control-adapter/run002/stderr.log') and z.read('control-adapter/run002/stderr.log').rstrip().endswith(b'OK'))
    check('zero_target_or_process_effects',outcome['actual_target_starts']==0 and outcome['actual_project_process_operations']==0 and not any(outcome['outer_process_guard_calls'].values()) and not outcome['blocked_process_audit_events'] and not outcome['blocked_test_module_imports'] and outcome['guards_installed'] and outcome['guards_installed_before_import_at_utc']<methods[0]['started_at_utc'])

    prefix='control-adapter/fixtures002/loader/'
    mapping=json.loads(z.read(prefix+'P13-CONTROL-MAPPING.json'));oracle=json.loads(z.read(prefix+'candidate004/EXPECTATIONS.json'))
    materialized=json.loads(z.read(prefix+'MATERIALIZATION.json'));fixture_manifest=json.loads(z.read(prefix+'candidate004/FIXTURE-MANIFEST.json'))
    fixture_errors=[]
    for r in materialized['files']:
        n=prefix+'candidate004/'+r['path'];b=z.read(n)
        original=next(x for x in fixture_manifest['files'] if x['path']==r['path'])
        if len(b)!=r['size_bytes'] or sha(b)!=r['sha256'] or manifest[n]['original_mode']!=r['mode'] or any(r[k]!=original[k] for k in ['mode','path','sha256','size_bytes']):fixture_errors.append(n)
    check('all131_materialized_original_fixture_bytes_modes',len(materialized['files'])==131 and not fixture_errors,fixture_errors)
    observations=[json.loads(z.read(n)) for n in names if n.startswith(prefix+'observations/') and n.endswith('/OBSERVATION.json')]
    runtime_ids={r['id'] for r in mapping['cases'] if r['classification']=='future_runtime_primitive'}
    observed_ids={r['case'] for r in observations};outcome_counts=dict(collections.Counter(r['observed']['outcome'] for r in observations))
    check('all96_original_oracles_and_case_inventory',len(observations)==len(observed_ids)==96 and observed_ids==runtime_ids and all(r['observed']==r['expected']==oracle['cases'][r['case']] for r in observations) and {r['id'].split('.test_',1)[1] for r in methods if r['id'].startswith('tests.test_current_host_loader_path_v01.')}==runtime_ids and outcome_counts=={'refusal':82,'propagated_callback':3,'metadata':3,'rule_acceptance':8},outcome_counts)
    by_case={r['case']:r for r in observations}
    callbacks=[r for r in observations if r['case'].startswith('F')]
    check('three_callback_identities',len(callbacks)==3 and all(r['callback_exception_identity_preserved'] and len(r['callback_triggers'])==1 and r['callback_triggers'][0]==r['case'].split('_',1)[1] for r in callbacks))
    drifts=[r for r in observations if r['case'].startswith('D')]
    check('three_actual_rechecks',len(drifts)==3 and {r['observed']['cause_code'] for r in drifts}=={'CHI-LOADER','CHI-PATH','CHI-INSPECTOR'} and all(r['observed']['code']=='CHI-DRIFT' and r['before_rule_result']['nonselecting'] and any(c['boundary']=='_recheck' and set(c['observed_boundaries'])=={'actual_check_resolution','actual_subject_parser'} for c in r['caller_reports']) for r in drifts))
    ordering=[json.loads(z.read(n)) for n in names if n.startswith(prefix+'observations/') and n.endswith(('/validate-ordering.json','/recheck-ordering.json'))]
    check('18_retained_negative_caller_experiments',len(ordering)==18 and all(not any(r['effect_guard_calls'].values()) and not r['positive_operational_admission'] and set(r['observed_boundaries'])=={'actual_check_resolution','actual_subject_parser'} and r['exception'] for r in ordering))
    n57=json.loads(z.read(prefix+'EXTERNAL-REVIEW-OBLIGATION.json'))
    check('N57_external_unresolved_not_counted',n57['id']=='N57_source_variant_unknown' and not n57['runtime_pass'] and not n57['historical_oracle_satisfied'] and not n57['host_qualification'] and n57['not_counted_as_runtime_or_skip'] and 'N57_source_variant_unknown' not in observed_ids and n57['original_oracle']==oracle['cases']['N57_source_variant_unknown'] and n57['external_review']=='not_established_by_supplied_inputs')

    protected=json.loads(z.read('verification/protected-source/RESULT.json'));allowed={r['path'] for r in protected['allowed_existing_changes']};protected_errors=[]
    for r in protected['rows']:
        p=r['path'];base=base_tree.get(p);current=source_tree.get(p)
        if not base or not current or not r['passed'] or base['oid']!=current['oid'] or r['baseline_blob']!=base['oid'] or r['actual_blob']!=current['oid'] or base['mode']!=current['mode'] or r['git_mode']!=base['mode'] or r['actual_mode']!=current['mode']:protected_errors.append(p)
    expected_protected={p for p,v in base_tree.items() if v['kind']=='blob'}-allowed
    check('all20241_protected_git_blobs_modes_unchanged',len(protected['rows'])==20241 and {r['path'] for r in protected['rows']}==expected_protected and not protected_errors,{'count':len(protected['rows']),'errors':protected_errors,'method':'Compared every retained row to immutable baseline and published Git tree blob/mode identities. Git blob identity proves content equality without rerunning the historical1GB source read.'})
    check('baseline_and_startup_product_equal',z.read('implementation/source-baseline.py')==blob('prototypes/static_tray_v01/current_host_inspection_v01.py',BASELINE)==blob('prototypes/static_tray_v01/current_host_inspection_v01.py',STARTUP))
    inherited=['tests/test_current_host_inspection_v01.py','tests/test_current_host_elf_mapping_v01.py']
    check('175_inherited_test_sources_unchanged',all(source_tree[p]==base_tree[p]==startup_tree[p] for p in inherited))
    changed=git('diff','--name-only',STARTUP,SOURCE).decode().splitlines();coverage=json.loads((ROOT.parent/'early/CHANGED-FILES-RECOVERY.json').read_text())
    check('all28_published_changes_have_recovery_provenance',len(changed)==28 and set(changed)=={r['path'] for r in coverage} and all(r['source']['source_revision']==SOURCE for r in coverage),{'count':28,'source':'../early/CHANGED-FILES-RECOVERY.json; byte-exact binding verification retained by early Attempt002'})

    check('independent_acceptance_exact_source_and_scope',review['reviewer']=='/root/independent_review' and review['verdict']=='accepted' and not review['mandatory_findings'] and review['check_groups_passed']==25 and review['check_groups_failed']==0 and all(c['passed'] for c in review['checks']) and review['candidate']['module']['sha256']==sha(production) and review['candidate']['adapter']['sha256']==sha(adapter) and review['runtime_evidence']['runtime_methods']==271)
    old_findings=json.loads(z.read('review/implementation-attempt001/FINDINGS.json'));old_counter=json.loads(z.read('review/implementation-attempt001/counterexamples/OUTCOME.json'));new_counter=json.loads(z.read('review/implementation-attempt002/counterexamples/OUTCOME.json'))
    prior_obs={r['id']:r for r in old_counter['observations']};new_obs={r['id']:r for r in new_counter['observations']}
    check('both_mandatory_failures_preserved',old_findings['verdict']=='changes_required' and {r['id'] for r in old_findings['findings']}=={'P14-IMPL-001','P14-IMPL-002'} and not prior_obs['IR-CALLBACK-001']['diagnostic_preserved'] and all(prior_obs[k]['exception_type']=='KeyError' and not prior_obs[k]['closed_shape_refusal'] for k in ['missing_variant_path','missing_variant_absent_at']))
    check('both_corrections_rechecked_at_exact_candidate003',set(review['resolved_findings'])=={'P14-IMPL-001','P14-IMPL-002'} and new_counter['source']['prototypes/static_tray_v01/current_host_inspection_v01.py']==sha(production) and new_obs['IR-CALLBACK-001']['same_exception_object'] and new_obs['IR-CALLBACK-001']['diagnostic_preserved'] and all(new_obs[k]['closed_shape_refusal'] and new_obs[k]['exception_type']=='HostInspectionError' for k in ['missing_variant_path','missing_variant_absent_at']) and new_obs['positive_control']['private_rule_acceptance'] and all(new_counter['postflight_matches'].values()))
    old_probe=z.read('review/implementation-attempt001/probe_counterexamples.py').decode();new_probe=z.read('review/implementation-attempt002/probe_counterexamples.py').decode()
    check('independent_recheck_probe_logic_unchanged',old_probe.replace('implementation-attempt001','implementation-attempt002').replace('5ff94a09e29635a81439014a95493ff631471e227474b4cd5cdcd3631d2a03dc',sha(production))==new_probe)
    kernel=json.loads(z.read('review/implementation-attempt002/kernel-boundaries/OUTCOME.json'))
    check('ten_retained_mocked_kernel_checks',kernel['module_sha256']==sha(production) and kernel['passed']==10 and kernel['failed']==0 and len(kernel['checks'])==10 and all(r['passed'] for r in kernel['checks']) and not any(kernel['process_guard_calls'].values()) and not kernel['blocked_process_audit_events'])
    check('candidate_history_and_freeze_failure_retained',all(p in names for p in ['implementation/candidate001.py','implementation/candidate002.py','implementation/candidate003.py','control-adapter/run001/OUTCOME.json','control-adapter/run002/OUTCOME.json','control-adapter/FREEZE-ATTEMPT001-FAILURE.json']) and sha(z.read('implementation/candidate002.py'))=='5ff94a09e29635a81439014a95493ff631471e227474b4cd5cdcd3631d2a03dc' and json.loads(z.read('control-adapter/run001/OUTCOME.json'))['passed'])

result={'schema':'ontokin.c271.p14-independent-reuse-audit/1','reviewer':'/root/evidence_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_revision':SOURCE,'source_tree':identity['source_tree'],'archive':identity,'verdict':'eligible_for_exact_historical_evidence_reuse' if all(c['passed'] for c in checks) else 'findings','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'runtime_tests_this_review':'not_run','archive_scripts_executed':False,'Git_source_Library_mutation':'none','limits':['Finite candidate003 implementation/adapter acceptance only.','N57 actual-loader source completeness and operational positive plan remain unestablished.','H0/H1, runtime installation, Node/ldd, original-seven/full routine, native/model/hosted execution, main integration and parent closure remain unrun or unmet.','Current main remains separate; historical C270/global prior-process completion remains unknown.','No missing accepted-evidence bytes found if verdict is eligible; this audit does not assert complete offline recovery of unrelated history.','Final ZIP content review and save/readback/receipt belong to other assigned workers and Director.']}
dump('AUDIT.json',result)
(ROOT/'REPORT.md').write_text('# P14 independent evidence reuse audit\n\nVerdict: '+result['verdict']+'. '+str(result['passed'])+' groups passed; '+str(result['failed'])+' failed.\n\nSource e26dc6369a8d6ba88ea779b26a8c655121ae5dbc, tree0271ee6a507f83015eea06b63b1bed51753ba419. Three exact published Git parts independently reassemble to17,386,151bytes, SHA-25672fa3117b84eafdd1384a2ee8cc9a957bcad8b20ec1b9f90dc824135af66eb13. Verified all21,408payload hashes/CRCs and21,409safe inert members;30symlinks remain descriptions only.\n\nProduction candidate003 and adapter exactly equal accepted source hashes. All172 frozen source/dependency/fixture/test/helper identities equal their run002 snapshots and current published inputs; all172 historical postflight checks passed. Exact command, isolated interpreter flags, environment, Python binary hash and OS identity are established.\n\nRun002 retains271passing methods (96loader,135inspection,40mapping), exact journals/logs, zero failures/errors/skips/target starts/process effects. All96 observed outcomes equal independent original oracles; all131 fixture bytes/original modes, three callback identities, three actual rechecks and18negative caller experiments are retained. N57 remains outside runtime counts with historical oracle and external review unsatisfied.\n\nEvery20,241protected baseline Git blob and mode is unchanged. The175inherited test source methods retain their exact source files. All28published changed files have exact recovery provenance from the independently verified early package.\n\nIndependent implementation acceptance binds the same source/adapter/run; both mandatory candidate002 findings and their failing probes remain preserved. Candidate003 counterexamples retain the same probe logic and confirm both corrections; ten mocked kernel boundary checks remain separate from runtime counts. Candidate001/002/003, run001/002 and initial freeze failure are retained.\n\nNo product test or archived script was executed in this audit. No Git/source/Library mutation. Historical evidence is eligible for this delivery-only recovery; this is not fresh runtime execution or operational H0/H1 qualification. Main integration, full routine, actual-loader completeness and parent closure remain unmet. Final package/save review is separately assigned.\n')
print(json.dumps({'verdict':result['verdict'],'passed':result['passed'],'failed':result['failed'],'failed_checks':[c for c in checks if not c['passed']],'report':str(ROOT/'REPORT.md')}))
