#!/usr/bin/env python3
"""Independent document/source checks. No project imports or behavior execution."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import zipfile

ROOT = Path('/workspace/scratch/522363862012')
REPO = ROOT / 'OntoKin'
OUT = ROOT / 'audit/design-review'
CAND = ROOT / 'audit/host-design/review-candidate-002'
checks = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def record(id, passed, details):
    checks.append({'id': id, 'passed': bool(passed), 'details': details})


manifests = []
for number, expected_hash in [('001', '509d97fc3c85c82e210ee2fa084cc772ca8deaddffcffecb1340ce24753ddbb5'), ('002', 'ad48e321ee9163f9f87c675c291f566e28b961b55696976f738b04e165845f2a')]:
    directory = CAND.parent / ('review-candidate-' + number)
    manifest_bytes = (directory / 'MANIFEST.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    rows = []
    for entry in manifest['files']:
        b = (directory / entry['path']).read_bytes()
        rows.append({'path': entry['path'], 'sha256': sha(b), 'size_bytes': len(b), 'passed': len(b) == entry['size_bytes'] and sha(b) == entry['sha256']})
    exact_inventory = {p.name for p in directory.iterdir()} == {r['path'] for r in manifest['files']} | {'MANIFEST.json'}
    record('candidate-' + number, sha(manifest_bytes) == expected_hash and exact_inventory and all(r['passed'] for r in rows), {'manifest_sha256': sha(manifest_bytes), 'exact_inventory': exact_inventory, 'files': rows})
    manifests.append({'candidate': manifest['candidate'], 'manifest_sha256': sha(manifest_bytes), 'files': manifest['files']})

bindings = load(CAND / 'SOURCE-BINDINGS.json')
source_results = []
for row in bindings['sources']:
    path = REPO / row['path']
    b = path.read_bytes()
    oid = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
    git_entry = subprocess.check_output(['git', '--no-optional-locks', '-C', str(REPO), 'ls-tree', row['source_revision_reference'], '--', row['path']]).decode().strip()
    header, git_path = git_entry.split('\t', 1)
    mode, kind, git_blob = header.split()
    valid = len(b) == row['size_bytes'] and sha(b) == row['sha256'] and oid == row['git_blob_sha1_computed'] == git_blob and kind == 'blob' and git_path == row['path'] and int(row['mode'], 8) == stat.S_IMODE(path.stat().st_mode) == (int(mode, 8) & 0o777)
    source_results.append({'id': row['id'], 'path': row['path'], 'source_revision': row['source_revision_reference'], 'sha256': sha(b), 'git_blob': git_blob, 'passed': valid})
record('source-identities', all(r['passed'] for r in source_results), source_results)

plan = load(CAND / 'QUALIFICATION-PLAN.json')
matrix = load(CAND / 'CONTROL-MATRIX.json')
p06schema = load(REPO / 'docs/engineering/localized-repair-c271/current-host-p06/SCHEMA.json')['$defs']
schema_rows = [{'name': name, 'passed': value == p06schema[name]} for name, value in plan['compatible_P06_field_contracts'].items()]
record('closed-p06-schema-excerpts', all(r['passed'] for r in schema_rows), schema_rows)
cross = []
for key in ['control_matrix', 'source_bindings']:
    value = plan['design_files'][key]
    b = (CAND / value['path']).read_bytes()
    cross.append({'field': key, 'passed': value['sha256'] == sha(b) and value['size_bytes'] == len(b)})
record('plan-cross-bindings', all(r['passed'] for r in cross), cross)

p05 = load(REPO / 'docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json')
by_id = {r['id']: r for r in matrix['controls']}
control_rows = []
for old in p05['controls']:
    new = by_id[old['id']]
    mapping = {'requirement': 'adopted_requirement', 'input_mutation': 'adopted_input_mutation', 'expected': 'adopted_expected', 'expected_checker_starts': 'adopted_expected_checker_starts', 'evidence_kind': 'adopted_evidence_kind'}
    control_rows.append({'id': old['id'], 'passed': all(old[k] == new[v] for k, v in mapping.items())})
old_controls = load(REPO / 'docs/engineering/localized-repair-c271/current-host-p06/CONTROL-DISPOSITIONS.json')['controls']
for old in old_controls:
    if old['id'] in ('P06-H01', 'P06-H02', 'P06-H03'):
        new = by_id[old['id']]
        control_rows.append({'id': old['id'], 'passed': old['frozen_expected'] == new['retained_frozen_expected'] and old['disposition'] == new['retained_disposition'] == 'NOT_RUN_GATE_H' and new['retained_execution_count'] == 0})
record('retained-control-obligations', all(r['passed'] for r in control_rows) and len(matrix['controls']) == len(by_id) == 44, {'retained': control_rows, 'new_authoring_ids': sorted(k for k in by_id if k.startswith('HI')), 'total': len(by_id)})

provider_ast = ast.parse((REPO / 'prototypes/static_tray_v01/current_host_readback_v01.py').read_bytes())
expected_bodies = None
for node in provider_ast.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ORIGINAL_BODIES' for t in node.targets):
        expected_bodies = ast.literal_eval(node.value)
actual_bodies = {}
module_ast = ast.parse((REPO / 'tests/test_static_tray_readback_v01.py').read_bytes())
for cls in module_ast.body:
    if isinstance(cls, ast.ClassDef):
        for node in cls.body:
            key = cls.name + '.' + getattr(node, 'name', '')
            if key in expected_bodies and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                actual_bodies[key] = sha(ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False).encode())
record('original-method-helper-bodies', actual_bodies == expected_bodies == bindings['original_bodies'] == bindings['observed_original_bodies'] and len(actual_bodies) == 9, actual_bodies)
expected_ids = sorted('test_static_tray_readback_v01.' + k for k in actual_bodies if '.test_' in k)
record('original-seven-method-ids', sorted(plan['original_default_method_ids']) == expected_ids == sorted(bindings['original_default_method_ids']) == sorted(p05['method_ids']) and len(expected_ids) == 7, expected_ids)
segment = bindings['original_scientific_segment']
old = (REPO / 'prototypes/static_tray_v01/readback.mjs').read_bytes()
new = (REPO / 'prototypes/static_tray_v01/current_host_readback_v01.mjs').read_bytes()
marker = segment['marker'].encode()
old_suffix, new_suffix = old[old.index(marker):], new[new.index(marker):]
record('scientific-source-suffix', old_suffix == new_suffix and sha(old_suffix) == segment['old_sha256'] == segment['new_sha256'], {'sha256': sha(old_suffix), 'bytes': len(old_suffix), 'scope': 'Byte equality only; no JavaScript execution or syntax validation.'})

with zipfile.ZipFile(REPO / 'docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip') as z:
    dependency = json.loads(z.read('DEPENDENCY-INVENTORY.json'))
    loader = dependency['inspected_loader_member']
    loader_bytes = loader['source'].encode()
    exact_dependencies = {r['relative_path']: {'sha256': r['sha256'], 'size_bytes': r['size_bytes']} for r in dependency['retained_dependency_files']}
    record('exact-retained-dependency-identity', len(exact_dependencies) == 24 and exact_dependencies == bindings['exact_24_dependencies'], {'count': len(exact_dependencies), 'source': 'P05 frozen dependency inventory; no installation or recursive restoration.'})
    record('loader-control-flow-source', sha(loader_bytes) == loader['sha256'] and len(loader_bytes) == loader['size_bytes'], {'loader_sha256': loader['sha256'], 'bytes': len(loader_bytes), 'source': loader['member'], 'manual_assessment': 'Loader imports only node:url/node:path, maps three specifiers in resolve(), and delegates others. Supports the expressly limited early-refusal/no-reader-import path inference.'})

record('nonexecutable-staged-plan', plan['executable'] is False and matrix['executable'] is False and all(v is None for v in plan['future_runtime_bindings'].values()) and all(v == 0 for v in plan['current_phase_execution_counts'].values()) and [s['id'] for s in plan['stages']] == ['HI', 'H0', 'H1', 'H2', 'H3', 'R', 'R04', 'R05'], {'stages': [s['id'] for s in plan['stages']], 'unavailable_future_bindings': len(plan['future_runtime_bindings']), 'source_budgets': plan['source_budgets'], 'runtime_execution': False})
count_contract = matrix['new_attempt_count_contract']
record('interrupted-start-resolution', count_contract['actual_direct_starts'] == [0, 1, None] and count_contract['observed_direct_starts'] == [0, 1] and count_contract['start_count_state'] == ['PROVEN_ZERO', 'OBSERVED_ONE', 'UNKNOWN'] and all('unknown_start_count_control' in by_id[k] for k in ['HI14', 'HI18', 'HI19']), {'contract': count_contract, 'affected_controls': ['HI14', 'HI18', 'HI19'], 'manual_assessment': 'Exact null with retained lower bound represents the unresolved launch window; absence cannot prove zero; aggregate unknowns remain null and success/retry are blocked.'})

report = {'schema': 'ontokin.c271.p07-independent-design-static-checks/1', 'reviewer': '/root/intake_review', 'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'candidate': 'review-candidate-002', 'candidate_manifest_sha256': sha((CAND / 'MANIFEST.json').read_bytes()), 'passed': all(r['passed'] for r in checks), 'check_groups': len(checks), 'checks': checks, 'candidate_identities': manifests, 'method': 'Python standard-library JSON, hashing, AST parsing and immutable Git ls-tree reads; source/manual consumer review. No project imports, product tests, runtime preparer, Node, ldd or hosted execution.', 'limits': 'Design and source-preservation evidence only. No operational fixture or host plan is instantiated, and no future behavior is verified.'}
(OUT / 'STATIC-CHECKS.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'check_groups': len(checks), 'failed_groups': [r['id'] for r in checks if not r['passed']], 'candidate_manifest_sha256': report['candidate_manifest_sha256']}, indent=2))
