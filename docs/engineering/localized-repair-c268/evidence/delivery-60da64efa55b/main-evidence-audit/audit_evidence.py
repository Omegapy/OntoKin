#!/usr/bin/env python3
"""Read-only C268 evidence recovery audit; does not execute the cohort."""
import ast
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import zipfile

REPO = Path('/workspace/scratch/a3de3dd23bbf/OntoKin')
OUT = Path('/workspace/scratch/60da64efa55b/evidence/main-evidence-audit')
MAIN = '5084dd69312e8da5a49aadd33cf83ba56db7c058'
RECOVERY = 'ecce5f18fd4693e254bc6c797cd8b3f0a74d32a1'
CANDIDATE = 'e6f55b73fa71953aa648bcd34711a6796a7346b6'
ACCEPTED = 'b49a930292752e80abe47cc0526e76413089d64d'
ORIGINAL = 'ffb912cce59ccfe7d0d82ab4349de9b12271cc03'
HEAD = '43115fb864c6f475fb2a56da43566fc1c8b3af50'
LEASE = '0d555182b3b55a6875f3cf6bafc4519ec1541b80'
BASE = 'docs/engineering/localized-repair-c268'
RUN = BASE + '/evidence/finalization-a3de3dd23bbf/main-integration'
OLD = BASE + '/evidence/finalization-20261119/candidate-published'
REV = BASE + '/evidence/finalization-20261119/review'
PUB = Path('/workspace/scratch/a3de3dd23bbf/evidence/publication')
ASSERTIONS = []
IDENTITIES = []

def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=REPO)

@lru_cache(None)
def blob(ref, path):
    return git('show', ref + ':' + path)

def j(ref, path):
    return json.loads(blob(ref, path))

def ident(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def check(name, passed, detail=None):
    row = {'name': name, 'passed': bool(passed)}
    if detail is not None:
        row['detail'] = detail
    ASSERTIONS.append(row)

def verify(name, data, expected):
    actual = ident(data)
    check(name, all(actual[k] == expected[k] for k in ('bytes', 'sha256')),
          None if all(actual[k] == expected[k] for k in ('bytes', 'sha256')) else {'actual': actual, 'expected': expected})
    IDENTITIES.append({'identity': name, **actual})

def paths(ref, prefix):
    return git('ls-tree', '-r', '--name-only', ref, '--', prefix).decode().splitlines()

def normalize(command):
    result = list(command)
    if '--evidence-dir' in result:
        i = result.index('--evidence-dir') + 1
        result[i] = 'EVIDENCE/' + PurePosixPath(result[i]).name
    return result

def archive(ref, folder):
    raw = blob(ref, folder + '/inputs.zip')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        safe = len(names) == len(set(names)) and all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names)
        check('archive_safety:' + folder, safe and z.testzip() is None)
        return {n: z.read(n) for n in names}

def walks(value):
    if isinstance(value, dict):
        yield value
        for sub in value.values():
            yield from walks(sub)
    elif isinstance(value, list):
        for sub in value:
            yield from walks(sub)

def unwrap(data):
    if isinstance(data, dict) and 'structuredContent' in data:
        data = data['structuredContent']
    if isinstance(data, dict) and isinstance(data.get('content'), str):
        data = json.loads(data['content'])
    return data

OUT.mkdir(parents=True, exist_ok=True)
start = datetime.now(timezone.utc).isoformat()
check('recovery_source_head', git('rev-parse', 'HEAD').decode().strip() == RECOVERY)
check('recovery_source_clean', git('status', '--porcelain').decode().strip() == '')
check('recovery_direct_parent', git('show', '-s', '--format=%P', RECOVERY).decode().strip() == MAIN)
trees = {r: git('rev-parse', r + '^{tree}').decode().strip() for r in [MAIN, RECOVERY, CANDIDATE, ACCEPTED, ORIGINAL, HEAD]}
check('merge_tree', trees[MAIN] == trees[HEAD] == '07971fcdbc6d912febc6adbec7ebf576eccab43f')
check('recovered_accepted_tree_equality', trees[ORIGINAL] == trees[ACCEPTED] == '10bcebf566d001a850f8e5c5c77eb96857de7e3b')
check('main_parents', git('show', '-s', '--format=%P', MAIN).decode().strip().split() == [LEASE, HEAD])
for old in [CANDIDATE, ACCEPTED, HEAD, LEASE]:
    rc = subprocess.run(['git', 'merge-base', '--is-ancestor', old, MAIN], cwd=REPO).returncode
    check('retained_ancestry:' + old, rc == 0)

receipt = j(RECOVERY, RUN + '/CHECKS.json')
candidate = j(RECOVERY, OLD + '/CHECKS.json')
review = j(RECOVERY, REV + '/REVIEW.json')
runner_path = BASE + '/evidence/run_checks.py'
check('separate_accepted_review', review['verdict'] == 'eligible' and not review['required_findings'] and review['published_candidate'] == CANDIDATE and review['tree'] == trees[CANDIDATE] and review['reviewer'] == '/root/review_c268_final')
verify('reviewed_candidate_receipt', blob(RECOVERY, OLD + '/CHECKS.json'), review['fresh_cohort']['receipt'])
input_deltas = []
for phase, rec, prefix, rev in [('main', receipt, RUN, MAIN), ('candidate', candidate, OLD, CANDIDATE)]:
    check(phase + ':source', rec['source_before'] == rec['source_after'] and rec['source_before']['commit'] == rev and rec['source_before']['tree'] == trees[rev])
    check(phase + ':clean_run', rec['source_before']['tracked_dirty_status'] == rec['source_before']['all_dirty_status'] == '' and not rec['source_before']['shallow_checkout'])
    check(phase + ':complete_pass', rec['passed'] and rec['complete'] and rec['completed_check_count'] == rec['planned_check_count'] == 12 and rec['total_methods'] == rec['expected_total_methods'] == 282 and not rec['remaining_checks'])
    check(phase + ':stable_inputs', rec['input_identity_unchanged'] and rec['input_files_before'] == rec['input_files_after'])
    check(phase + ':unique_inputs', len(rec['input_files_before']) == len({x['path'] for x in rec['input_files_before']}))
    for row in rec['input_files_before']:
        verify(phase + ':input:' + row['path'], blob(rev, row['path']), row)
    check(phase + ':exact_output_inventory', set(paths(RECOVERY, prefix)) == {prefix + '/' + r['path'] for r in rec['output_files']} | {prefix + '/CHECKS.json'})
    for row in rec['output_files']:
        verify(phase + ':output:' + row['path'], blob(RECOVERY, prefix + '/' + row['path']), row)
    for group in rec['checks']:
        check(phase + ':passed:' + group['name'], group['result'] == 'passed' and group['exit_code'] == 0 and group['failure'] is None and all(group['assertions'].values()))
        raw = blob(RECOVERY, prefix + '/' + group['log']['path'])
        verify(phase + ':group_log:' + group['name'], raw, group['log'])
        if group['expected_methods'] is not None:
            log = raw.decode()
            found = re.findall(r'(?m)^Ran (\d+) tests? in ', log)
            named = re.findall(r'(?m)^(test_\w+) \(.*\) \.\.\. ok$', log)
            cmd = group['command']
            testpath = cmd[cmd.index('-s') + 1] + '/' + cmd[cmd.index('-p') + 1] if '-s' in cmd else cmd[2]
            tree = ast.parse(blob(rev, testpath))
            authored = [m.name for node in tree.body if isinstance(node, ast.ClassDef) for m in node.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')]
            check(phase + ':complete_methods:' + group['name'], bool(found) and int(found[-1]) == len(named) == len(authored) == group['methods'] == group['expected_methods'] and Counter(named) == Counter(authored) and bool(re.search(r'(?m)^OK$', log)))
        else:
            data = json.loads(raw)
            good = data.get('passed') is True and data.get('errors', []) == [] if group['name'] != 'documentation' else data.get('status') == 'passed' and data.get('failures') == []
            if group['name'] == 'c253-corpus':
                good = good and data.get('boundFiles') == 14 and data.get('tasks') == 3
            check(phase + ':structured_result:' + group['name'], good)
    verify(phase + ':runner', blob(rev, runner_path), rec['runner'])

codepaths = {x['path'] for x in candidate['input_files_before'] if x['path'].endswith(('.py', '.ok', '.glb'))}
codepaths.update(review['code_test_fixture_dependency_identities'])
codepaths.update(review['independent_control_inputs'])
codepaths.update(x['path'] for x in j(MAIN, 'docs/engineering/localized-repair-c260/INPUTS.json')['files'])
codepaths.update(x['path'] for x in j(MAIN, 'docs/engineering/localized-repair-c253/corpus.json')['files'].values())
for p in sorted(codepaths):
    check('implementation_test_dependency_fixture_runner_continuity:' + p, blob(CANDIDATE, p) == blob(MAIN, p) == blob(RECOVERY, p))
for field in ['code_test_fixture_dependency_identities', 'independent_control_inputs']:
    for p, expected in review[field].items():
        verify('review_identity:' + field + ':' + p, blob(MAIN, p), expected)
before = {x['path']: x for x in candidate['input_files_before']}
after = {x['path']: x for x in receipt['input_files_before']}
for p in sorted(set(before) | set(after)):
    if before.get(p) != after.get(p):
        input_deltas.append({'path': p, 'candidate': before.get(p), 'main': after.get(p)})
check('candidate_main_command_settings', [normalize(c['command']) for c in candidate['checks']] == [normalize(c['command']) for c in receipt['checks']])
check('candidate_main_full_recorded_environment', candidate['environment'] == receipt['environment'])
env = receipt['environment']
current = {'python': sys.version, 'platform': platform.platform(), 'runtime_bundle_version': os.environ.get('CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION'), 'executable': ident(Path(sys.executable).resolve().read_bytes())}
check('current_applicable_environment_matches', current['python'] == env['python'] and current['platform'] == env['platform'] and current['runtime_bundle_version'] == env['runtime_bundle_version'] and all(current['executable'][k] == env['resolved_executable'][k] for k in ['bytes', 'sha256']))

controls = {}
archives = []
snapshot_ref_total = 0
for component, expected in [(266, {'testMethods':34,'apiCalls':748,'boundCalls':28,'typedRefusals':720}), (267, {'testMethods':25,'apiCalls':123,'agreementCalls':35,'typedRefusals':88}), (268, {'testMethods':35,'apiCalls':131,'historicalCalls':121,'rawCalls':10,'admittedCalls':12,'rawSuccessfulCalls':9,'successfulCalls':21,'typedRefusals':110,'untypedExceptions':0})]:
    folder = RUN + f'/c{component}-controls'
    d = j(RECOVERY, folder + '/results.json')
    check('controls:totals:' + str(component), all(d[k] == v for k,v in expected.items()))
    check('controls:pass:' + str(component), d['passed'] and not d['failures'] and not d['errors'] and not d['skipped'])
    check('controls:ledger_count:' + str(component), len(d['cases']) == d['apiCalls'])
    allowed = {266:{('refusal','typed_refusal'),('binding','bound')},267:{('agreement','agreement'),('refusal','typed_refusal')},268:{('accepted','raw_success'),('typed_refusal','typed_refusal'),('admitted','admitted')}}[component]
    check('controls:all_expected_outcomes:' + str(component), all((c['expected'], c['outcome']) in allowed for c in d['cases']))
    if component != 266:
        check('controls:stable:' + str(component), d['inputCodeStableDuringRun'])
    for p,v in d['implementationAndControlInputs'].items():
        verify('control_dependency:' + str(component) + ':' + p, blob(MAIN,p), v)
    entries = archive(RECOVERY, folder)
    prior = archive(RECOVERY, OLD + f'/c{component}-controls')
    check('archive:candidate_main_content_equality:' + str(component), entries == prior)
    refs = [x for x in walks(d['cases']) if 'snapshot' in x]
    problems = []
    for x in refs:
        filename = x['snapshot'].split('!',1)[1]
        if filename not in entries or ident(entries[filename]) != {k:x[k] for k in ['bytes','sha256']}:
            problems.append(x)
    check('archive:all_recorded_snapshot_refs:' + str(component), not problems, {'references':len(refs),'mismatches':problems})
    frozen = [x for x in walks(d['cases']) if 'frozenReference' in x]
    check('controls:all_frozen_references:' + str(component), all(ident(blob(MAIN,x['frozenReference'])) == {k:x[k] for k in ['bytes','sha256']} for x in frozen), {'references':len(frozen)})
    snapshot_ref_total += len(refs)
    archives.append({'component':component,'entries':len(entries),'snapshot_references':len(refs),'frozen_references':len(frozen),'main':ident(blob(RECOVERY,folder+'/inputs.zip')),'candidate':ident(blob(RECOVERY,OLD+f'/c{component}-controls/inputs.zip')),'content_equal':entries==prior})
    controls[str(component)] = {**expected,'observed_outcomes':dict(Counter(c['outcome'] for c in d['cases']))}
    if component == 268:
        originals = [c for c in d['cases'] if c['case'].endswith('test_original_before_after_with_path_and_string_roots')]
        check('H01:both_original_endpoints_roots', len(originals)==4 and {(c['endpoint'],c['rootType']) for c in originals}=={(e,t) for e in ['before','after'] for t in ['PosixPath','str']} and all(c['outcome']=='admitted' and c['hingeCount']==8 and c['siteCount']==16 and c['flags']['historicalInputsBound'] for c in originals))
        test = blob(MAIN,BASE+'/test_endpoint_reader.py').decode()
        check('H01:single_definition_assertion_present', 'self.assertEqual(len({tuple(row["definitionId"]) for row in value["records"]}), 1)' in test and 'self.assert_semantics(' in test)
        check('C268:raw_authority_preserved', all(c.get('historicalInputsBound',c.get('flags',{}).get('historicalInputsBound')) is False for c in d['cases'] if c['outcome']=='raw_success'))
        check('C268:admitted_nonclaims', all(all(c['flags'].get(k) is False for k in ['sitePosesEvaluated','sourceValidityQualified','acceptedRevisionQualified','completeC255Semantic','executionAllowed','directSiteTableObserved','jointDefinitionOrSpanObserved']) for c in d['cases'] if c['outcome']=='admitted'))

for folder in [REV, BASE+'/evidence/finalization-a3de3dd23bbf/main-audit']:
    manifest = j(RECOVERY, folder+'/ARTIFACTS.json')
    for row in manifest['files']:
        verify('preserved_audit_artifact:' + folder+'/'+row['path'], blob(RECOVERY,folder+'/'+row['path']), row)
    check('exact_audit_artifact_inventory:' + folder, set(paths(RECOVERY,folder)) == {folder+'/'+x['path'] for x in manifest['files']} | {folder+'/ARTIFACTS.json'})

delta = [x.split('\t',1) for x in git('diff','--name-status',MAIN,RECOVERY).decode().splitlines()]
check('recovery_no_deletions', all(kind in ['A','M'] for kind,p in delta))
check('recovery_only_records_evidence', all(p=='STATUS.md' or p.startswith('docs/workflow/') or (p.startswith(BASE+'/') and not p in codepaths) for kind,p in delta))
check('no_changed_existing_historical_evidence', all(kind=='A' or '/evidence/' not in p or p==BASE+'/evidence/finalization-a3de3dd23bbf/WORKERS.json' for kind,p in delta))
task = j(RECOVERY, 'docs/workflow/tasks/C268/task.json')
check('task_gate_truth', task['status']=='in_progress' and all(r['status']=='done' for r in task['requirements'][:6]) and task['requirements'][6]['status']=='not_done' and task['delivery']['status']=='pending' and task['completion']['merge_commit']==MAIN and task['completion']['branch_disposition']=='deleted')
check('plan_gate_truth', {x['id']:x['status'] for x in task['plan']} == {'P01':'done','P02':'done','P03':'done','P04':'done','P05':'in_progress'})
check('historical_C262_unchanged', j(MAIN,'docs/workflow/CURRENT.json')['historical_handoff']==j(RECOVERY,'docs/workflow/CURRENT.json')['historical_handoff'])
meta_paths=['STATUS.md',BASE+'/README.md',BASE+'/RESULTS.md','docs/workflow/CURRENT.json','docs/workflow/knowledge.json','docs/workflow/tasks/C268/task.json',BASE+'/evidence/finalization-a3de3dd23bbf/WORKERS.json']
(OUT/'METADATA-DELTA.patch').write_bytes(git('diff',MAIN,RECOVERY,'--',*meta_paths))

remote_receipts = {}
names=['lease-ref-intent.json','lease-ref-result.json','lease-readback.json','final-candidate-ref-intent.json','final-candidate-ref-result.json','premerge-readback.json','merge-intent.json','merge-result.json','postmerge-main.json','postmerge-commit.json','postmerge-pr.json','postmerge-branches.json']
(OUT/'publication-receipts').mkdir(exist_ok=True)
for n in names:
    raw=(PUB/n).read_bytes(); (OUT/'publication-receipts'/n).write_bytes(raw)
    IDENTITIES.append({'identity':'preserved_publication_receipt:'+n,**ident(raw)})
    remote_receipts[n]=unwrap(json.loads(raw))
intent=remote_receipts['lease-ref-intent.json']
check('lease_conditional_nonforce', intent['expected_sha']=='412a7e38741d3f3db2625cb6c1caf43b69c0cae0' and intent['sha']==LEASE and intent['force'] is False and remote_receipts['lease-ref-result.json']['success'])
intent=remote_receipts['final-candidate-ref-intent.json']
check('branch_conditional_nonforce', intent['expected_sha']==CANDIDATE and intent['sha']==HEAD and intent['force'] is False and remote_receipts['final-candidate-ref-result.json']['success'])
intent=remote_receipts['merge-intent.json']
check('expected_head_merge', intent['observed_main']==LEASE and intent['expected_head_sha']==HEAD and intent['pr_number']==266 and intent['merge_method']=='merge' and remote_receipts['merge-result.json']['merged'] is True and remote_receipts['merge-result.json']['sha']==MAIN)
rb=remote_receipts['premerge-readback.json']
check('premerge_readback',rb[0]['object']['sha']==HEAD and rb[1]['tree']['sha']==trees[MAIN] and rb[2]['object']['sha']==LEASE)
commit=remote_receipts['postmerge-commit.json']; pr=remote_receipts['postmerge-pr.json']
check('postmerge_readback',remote_receipts['postmerge-main.json']['object']['sha']==MAIN and commit['sha']==MAIN and commit['tree']['sha']==trees[MAIN] and [p['sha'] for p in commit['parents']]==[LEASE,HEAD] and pr['merged'] is True and pr['merge_commit_sha']==MAIN and pr['head']['sha']==HEAD)
branches=remote_receipts['postmerge-branches.json']
check('deleted_branch_observation',len(branches)==1 and branches[0]['name']=='main' and branches[0]['commit']['sha']==MAIN)
lease_text=blob(LEASE,'STATUS.md').decode()
check('lease_owner_and_time', 'c268-finalize-a3de3dd23bbf' in lease_text and '2026-11-20T00:57:' in lease_text)

post=Path('/workspace/scratch/a3de3dd23bbf/evidence/post-integration-records')
postreceipt=json.loads((post/'CHECKS.json').read_bytes())
check('ecce_postrecord_identity', postreceipt['source_before']==postreceipt['source_after'] and postreceipt['source_before']['commit']==RECOVERY and postreceipt['source_before']['tree']==trees[RECOVERY] and postreceipt['source_before']['status']=='' and postreceipt['passed'])
(OUT/'post-integration-records').mkdir(exist_ok=True)
for n in ['CHECKS.json','workflow.log','documentation.log']:
    shutil.copyfile(post/n,OUT/'post-integration-records'/n)
    IDENTITIES.append({'identity':'preserved_postrecord:'+n,**ident((post/n).read_bytes())})
for c in postreceipt['checks']:
    verify('postrecord_log:'+c['name'], (post/c['log']['path']).read_bytes(), c['log'])
    check('postrecord_pass:'+c['name'], c['exit_code']==0 and c['passed'])

check('source_untouched_end',git('rev-parse','HEAD').decode().strip()==RECOVERY and git('status','--porcelain').decode().strip()=='')
report={'schema':'ontokin.c268.main-evidence-recovery-audit/1','worker':'/root/main_evidence_audit','scope':'Post-merge evidence recovery, continuity and metadata claims only; no implementation changes or cohort rerun','started_at_utc':start,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'main':MAIN,'recovery_commit':RECOVERY,'trees':trees,'candidate':CANDIDATE,'reviewer':review['reviewer'],'passed':all(x['passed'] for x in ASSERTIONS),'assertion_count':len(ASSERTIONS),'failures':[x for x in ASSERTIONS if not x['passed']],'assertions':ASSERTIONS,'main_receipt':{'path':RUN+'/CHECKS.json',**ident(blob(RECOVERY,RUN+'/CHECKS.json'))},'main_groups':12,'main_methods':282,'corpus_bindings':14,'source_inputs':len(receipt['input_files_before']),'main_outputs':len(receipt['output_files']),'continuity_paths':len(codepaths),'candidate_main_input_deltas':input_deltas,'controls':controls,'fixture_archives':archives,'snapshot_references':snapshot_ref_total,'recovered_delta':delta,'recorded_environment':env,'current_environment':current,'metadata_review':{'paths':meta_paths,'verdict':'Supported bounded claims; R01-R06 done, R07 pending. In-progress parent and saved-delivery next action are correct. No release, full H-group, site/world, accepted-revision, model/native or comparative claim. November 19 heading follows merge commit -07:00 date; execution receipts are November 20 UTC.','requires_fresh_checks_after_new_root_record_edits':True},'remote_boundary':'Preserved API intent/results/readbacks independently inspected; current live main/PR/branch state supplied by Director. No network call in this worker.','reuse_verdict':'Eligible to recover ecce5f18 evidence and records. Keep original execution at merge 5084dd69. Rerun only applicable documentation/workflow checks for current new records; no unchanged cohort rerun required.','remaining_gate':'R07 final verified saved delivery, separate receipt, task/issue closure and ownership release; stop','not_run':receipt['not_run'],'limits':receipt['limits'],'ownership':{'repository_edits':False,'commits':False,'network_writes':False,'cohort_execution':False,'nested_workers':False,'active_processes':[]}}
(OUT/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'INSPECTED-IDENTITIES.json').write_text(json.dumps({'source_repository':str(REPO),'identities':IDENTITIES},indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['passed','assertion_count','failures','source_inputs','main_outputs','continuity_paths','snapshot_references']},indent=2))
