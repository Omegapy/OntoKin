"""C051 source/evidence metadata audit. Does not import or execute OntoKin."""
from pathlib import Path
import hashlib
import json
import re
import sys

HERE = Path(__file__).resolve().parent
CHECKPOINT = HERE.parent
ROOT = HERE.parents[3]
PARENT = '492b0e0edb5eb71e058fc29af059992b3a7952cb'
TREE = 'ebc9e155ee98b37e56199dde987774ff38960d81'
checks = []

def read(path):
    return json.loads(path.read_text())

def require(name, condition, detail):
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})

def file_record(path):
    b = path.read_bytes()
    return {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
            'git_blob': hashlib.sha1(f'blob {len(b)}\0'.encode() + b).hexdigest()}

tree = read(HERE / 'base-tree.json')
base = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
require('parent_tree_identity', tree['sha'] == TREE and not tree['truncated'] and len(base) == 2786,
        {'tree': tree['sha'], 'base_files': len(base)})
inventory = read(HERE / 'recovered-inputs.json')
bad = []
for row in inventory:
    actual = file_record(ROOT / row['path'])
    if actual['bytes'] != row['bytes'] or actual['sha256'] != row['sha256'] or actual['git_blob'] != base[row['path']]['sha']:
        bad.append(row['path'])
require('recovered_inputs_exact', not bad, {'files': len(inventory), 'mismatches': bad})

held = read(HERE / 'held-runtime-binding.json')
require('all_runtime_matches_held_source', held['runtime_count'] == 65 and not held['mismatches']
        and all(x['base_blob'] == x['held_blob'] == base[x['path']]['sha'] for x in held['entries']),
        {'runtime_modules': held['runtime_count'], 'held_tree': held['held_tree']})

new = [p for p in ROOT.rglob('*') if p.is_file() and p.relative_to(ROOT).as_posix() not in base]
scope = 'docs/engineering/reach-recording-validation-2026-10-23/'
outside = [p.relative_to(ROOT).as_posix() for p in new
           if not p.relative_to(ROOT).as_posix().startswith(scope + 'checkpoint-051')
           and p.relative_to(ROOT).as_posix() != scope + 'HANDOFF-051.md']
require('new_files_scoped', not outside, {'new_files_present': len(new), 'outside_scope': outside})

attachments = ['HANDOFF-050.md', 'checkpoint-050-next-scope.json', 'checkpoint-050-cost-ledger.json',
               'checkpoint-050-factorial-cache-origin-review.md']
require('supplied_predecessor_bytes', all((ROOT.parent / 'upload' / n).read_bytes() == (CHECKPOINT / n).read_bytes() for n in attachments),
        {'matched_repository_attachments': len(attachments), 'portable_readme': 'separate companion, not a claimed repository file'})

final_names = ['checkpoint-051-atan-adjacent-feasibility.md', 'checkpoint-051-cost-ledger.json',
               'checkpoint-051-next-scope.json', 'HANDOFF-051.md']
final_hashes = {n: file_record(CHECKPOINT / n)['sha256'] for n in final_names}
audit_paths = ['checkpoint-051-reviews/authority/final-draft-review.json',
               'checkpoint-051-reviews/cost/final-draft-review-002.json',
               'checkpoint-051-reviews/evidence/root-draft-audit.json']
audit_bad = []
for name in audit_paths:
    p = CHECKPOINT / name
    content = p.read_text()
    data = read(p)
    if not data['status'].startswith('passed') or any(h not in content for h in final_hashes.values()):
        audit_bad.append(name)
require('final_review_bindings', not audit_bad, {'audits': audit_paths, 'final_hashes': final_hashes, 'mismatches': audit_bad})

ledger = read(CHECKPOINT / 'checkpoint-051-cost-ledger.json')
authority = read(CHECKPOINT / 'checkpoint-051-reviews/authority/result.json')
fields = ledger['H3']['class_fields']
counts = {k: len(v) for k, v in fields.items()}
require('specified_cost_bounds', counts == {'_Arithmetic': 18, 'ReachExecutionWork': 16, 'ConstructionBudget': 12, 'Fraction': 27}
        and sum(counts.values()) == ledger['H3']['new_class_field_probe_floor'] == 73
        and fields == authority['concrete_screen']['fields']
        and ledger['native128']['max_gross'] == 63
        and ledger['H3']['accepted_call_net_ceiling'] == 63 - 73 == -10
        and ledger['H3']['two_successfully_screened_seed_calls_net_ceiling'] == 34 - 146 == -112
        and sum(ledger['C052_nomination']['components'].values()) == 165
        and ledger['C052_nomination']['gross'] == 165 - 1 == 164,
        {'field_counts': counts, 'claimed_gate_floor': 73, 'native128_ceiling': 63, 'new_target_gross': 164,
         'qualification': 'metadata arithmetic on declared operation counts only; no numerical kernel or source request'})

scope_data = read(CHECKPOINT / 'checkpoint-051-next-scope.json')
plan = read(CHECKPOINT / 'checkpoint-051-reviews/evidence/passive-observation-plan.json')
require('unknowns_and_execution_boundary', ledger['whole_request']['complete_saving'] is None
        and ledger['whole_request']['candidate_total'] is None
        and not ledger['implementation_selected'] and not ledger['universal_impossibility']
        and scope_data['evidence_limits']['whole_request_net'] is None
        and plan['source_inspection']['mechanism'] is None
        and not plan['current_product_execution'] and not scope_data['passive_mechanism_selected'],
        {'complete_cost': 'unknown', 'passive_mechanism': None, 'runtime_execution': False})
require('limits_and_inherited_status', scope_data['preserved_limits'] == {'shared_operations':100000,'elapsed_ms':30000,'operand_bits':32768,'cache_entries':256,'cursor_updates':64}
        and scope_data['original28'] == {'passed':24,'total':28,'new_execution':False}
        and scope_data['C035'] == 'held including adverse timing' and not scope_data['full_product_goal_completed'],
        scope_data['preserved_limits'])

json_files = [p for p in new if p.suffix == '.json']
for p in json_files:
    read(p)
leaks = [p.relative_to(ROOT).as_posix() for p in new
         if p.suffix in {'.json','.md','.txt','.py'}
         and re.search(r'https://[^\s\"<>]+[?&](?:token|sig)=', p.read_text())]
require('metadata_parses_and_no_signed_urls', not leaks, {'json_files': len(json_files), 'signed_url_files': leaks})

checker = 'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'
require('documentation_checker_preserved', file_record(ROOT / checker)['git_blob'] == base[checker]['sha'] == '25e4c5a224cbe15bbeba9a7e35301de4368d3de7',
        {'checker': checker, 'git_blob': base[checker]['sha']})

result = {'schema':'ontokin.checkpoint051-metadata-result/0.1', 'status':'passed' if all(x['passed'] for x in checks) else 'failed',
          'parent_commit':PARENT, 'parent_tree':TREE, 'grouped_checks':len(checks),
          'recovered_inputs':len(inventory), 'checks':checks,
          'scope':'source identity, review binding, scope, declared ledger metadata and unchanged gates; no OntoKin import or numerical execution'}
print(json.dumps(result,indent=2))
sys.exit(0 if result['status'] == 'passed' else 1)
