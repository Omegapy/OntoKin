from pathlib import Path
import datetime, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'OntoKin'
PREFIX = 'docs/engineering/localized-repair-c271/path-design-p24'
PHASE = REPO / PREFIX
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')

def binding(path):
    data=path.read_bytes()
    return {'path':path.relative_to(REPO).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

saved = read(ROOT / 'records/FINAL-SAVE-READBACK.json')
assert saved['status'] == 'zip_and_prompts_saved_and_exact_readback_verified'
assert saved['archive']['saved_bytes_readback_equal']
assert all(p['saved_bytes_readback_equal'] and p['matches_zip_member'] for p in saved['matching_prompts'])
core = read(ROOT / 'records/publication/core/RESULT.json')
assert core['status'] == 'conditionally_published_and_exact_readback_verified'
assert core['source_commit'] == saved['source_commit']
assert not (PHASE / 'P24-DELIVERY.json').exists()

post = PHASE / 'postfreeze'
for path in (ROOT / 'reviews/recovery').glob('*'):
    existing = PHASE / 'reviews/recovery' / path.name
    if path.is_file() and path.suffix != '.patch' and (not existing.exists() or existing.read_bytes() != path.read_bytes()):
        target = post / 'reviews' / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path,target)
for path in (ROOT / 'reviews/delivery').glob('*'):
    if path.is_file():
        target = post / 'reviews' / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path,target)
for path in [ROOT/'records/FINAL-SAVE-READBACK.json', ROOT/'records/FINAL-UPLOAD-RESULT.json',
    ROOT/'records/postfreeze/REMOTE-CORE-STATE.json', ROOT/'records/CORE-STAGED-WHITESPACE.json']:
    target=post/'evidence'/path.name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,target)
target=post/'session-tools/record_final_delivery.py'
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(Path(__file__),target)

receipt = {'schema':'ontokin.c271.p24-delivery/1','phase':'C271-P24-H0-path-design-adoption',
    'status':'zip_and_prompts_saved_verified_terminal_receipt_pending',
    'recorded_at_utc':NOW,'confirmed_at_utc':saved['confirmed_at_utc'],
    'technical_phase_complete':True,'phase_complete':False,'parent_complete':False,
    'source_commit':core['source_commit'],'source_tree':core['source_tree'],
    'archive':saved['archive'],'matching_prompts':saved['matching_prompts'],
    'early_receipt':PREFIX+'/EARLY-RECOVERY-RECEIPT.json',
    'independent_package_review':binding(post/'reviews/FINAL-ARCHIVE-REVIEW.json'),
    'independent_saved_readback_review':binding(post/'reviews/FINAL-SAVED-REVIEW.json'),
    'design_adoption':PREFIX+'/ADOPTION.json','control_counts':read(PHASE/'ADOPTION.json')['control_counts'],
    'receipt_publication':'Pending conditional receipt commit/readback, external receipt save/readback and matching live terminal markers at this source snapshot.',
    'external_receipt_file_name':'OntoKin_C271_P24_Delivery_Receipt_2026-11-23.json',
    'terminal_resolution':'Only the separately saved exact P24 external receipt and matching live PR274/issue273 P24 terminal markers resolve these delivery-only pending fields. ZIP hash, core source commit, receipt commit and receipt identity must agree. They cannot establish implementation, H0/H1, R03-R05 or parent completion.',
    'requirements':{'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'},
    'parent_plan':{'P01':'done','P02':'in_progress'},'current_unknown_operations':[],
    'production_implementation_changed':False,'h0_accepted':False,'h1_executed':False,
    'branch':'work/c271-missing-import-digest-control','pr':{'number':274,'state':'open','draft':True,'merged':False},
    'issue':{'number':273,'state':'open'},'main_lease_held':False,'main_integration':False,
    'next_action':'Finish receipt-only review/checks/publication, save and read back the external receipt, publish and verify matching terminal markers, then stop. No technical work or second phase.'}
write(PHASE/'P24-DELIVERY.json',receipt)
task_path=REPO/'docs/workflow/tasks/C271/task.json'
task=read(task_path)
task['session_phase'].update({'status':'technical_complete_delivery_pending_terminal_confirmation',
    'final_handoff_saved':True,'delivery_confirmed':False,'phase_complete':False,
    'delivery_receipt':PREFIX+'/P24-DELIVERY.json','handoff_source_revision':core['source_commit'],
    'independent_package_review':'accepted','next_phase_started':False})
task['delivery'].update({'status':receipt['status'],'archive':saved['archive'],
    'matching_prompts':saved['matching_prompts'],'receipt':PREFIX+'/P24-DELIVERY.json',
    'terminal_resolution':receipt['terminal_resolution'],'source_snapshot_before_terminal':True})
task['next_action']=receipt['next_action']
for req in task['requirements']:
    if req['id']=='R05' and PREFIX+'/P24-DELIVERY.json' not in req['evidence']:
        req['evidence'].append(PREFIX+'/P24-DELIVERY.json')
task['checks'].append({'name':'P24 frozen archive, Library save and exact readback review','result':'passed','required':True,
    'command':'Independent archive audit, saved ZIP/prompt byte and metadata equality, and separate independent saved-readback review',
    'evidence':[PREFIX+'/P24-DELIVERY.json',PREFIX+'/postfreeze/reviews/FINAL-ARCHIVE-REVIEW.json',PREFIX+'/postfreeze/reviews/FINAL-SAVED-REVIEW.json'],
    'scope':'Delivery-only evidence; no product/runtime or parent-completion gate.'})
write(task_path,task)
current_path=REPO/'docs/workflow/CURRENT.json'
current=read(current_path)
if current.get('previous_handoff') and current['previous_handoff'] not in current.setdefault('older_handoffs',[]):
    current['older_handoffs'].append(current['previous_handoff'])
current['previous_handoff']=current['latest_handoff']
current['latest_handoff']={**saved['archive'],'phase':receipt['phase'],'partial':True,
    'source_revision':core['source_commit'],'source_tree':core['source_tree'],
    'receipt':PREFIX+'/P24-DELIVERY.json','matching_prompts':saved['matching_prompts'],
    'phase_complete':False,'terminal_resolution':receipt['terminal_resolution']}
current['snapshot_date']=NOW
current['pending_phase_delivery']=task['delivery'].copy()
current['next_action'].update({'status':'ready','summary':receipt['next_action'],'suggested_task':'C271 P24 terminal delivery only'})
current['boundaries'].append('P24 frozen ZIP and matching prompts have confirmed saves and exact readbacks. Separate receipt publication/save and matching terminal confirmation remain pending at this source snapshot. Only delivery may continue here; adopted design is unimplemented and R03-R05 remain open.')
write(current_path,current)
for name in ['PHASE.json','OUTCOME.json']:
    path=PHASE/name;j=read(path);j.update({'final_handoff_saved':True,'delivery_receipt':PREFIX+'/P24-DELIVERY.json',
      'delivery_status':receipt['status'],'phase_complete':False,'terminal_resolution':receipt['terminal_resolution']});write(path,j)
manifest=[]
for path in sorted(post.rglob('*')):
    if path.is_file():manifest.append(binding(path))
write(post/'SOURCE-MANIFEST.json',{'schema':'ontokin.c271.p24-postfreeze-evidence/1','files':manifest,
    'scope':'New evidence after frozen core ZIP; preserved by the later receipt commit. The ZIP is not rewritten.'})
print(json.dumps({'delivery_recorded':True,'zip_saved_and_verified':True,'terminal_pending':True,'parent_complete':False,'postfreeze_files':len(manifest)}))
