#!/usr/bin/env python3
"""Independent read-only C270 candidate identity, preservation and pin audit."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

REPO = Path('/workspace/scratch/92228987b591/validation/candidate')
OUT = Path('/workspace/scratch/92228987b591/reviews')
BASE = '55c585acdaa750961ac37a5c46c9160bed149f97'
HEAD = 'a6099546e2ae66e78621008338ecd3b2d352d9b8'
TREE = '6e05696718723fe77f6973d1aa2319638723d127'
ENG = 'docs/engineering/'
CODE = [ENG + x for x in (
 'localized-repair-c265/source_hinges.py',
 'localized-repair-c266/hinge_binding.py',
 'localized-repair-c267/hinge_compare.py',
 'localized-repair-c268/endpoint_reader.py',
 'localized-repair-c268/endpoint_control_fixtures.py')]
STATE = ['STATUS.md', 'docs/workflow/CURRENT.json',
 'docs/workflow/tasks/C270/PLAN.md', 'docs/workflow/tasks/C270/REQUIREMENTS.md',
 'docs/workflow/tasks/C270/task.json']
checks = []

def git(*args):
 return subprocess.check_output(['git', *args], cwd=REPO)

def check(label, condition, **evidence):
 checks.append({'label': label, 'passed': bool(condition), **evidence})

def identity(raw):
 return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def entries(ref):
 result = {}
 for record in git('ls-tree', '-rz', '--full-tree', ref).split(b'\0'):
  if not record: continue
  meta, path = record.split(b'\t', 1)
  result[path.decode()] = meta.decode()
 return result

def source(ref, path):
 return git('show', ref + ':' + path)

def assignment(tree, name):
 for node in tree.body:
  if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
   value = node.value
   if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) and value.func.attr == 'MappingProxyType':
    value = value.args[0]
   return ast.literal_eval(value)
 raise ValueError('No assignment: ' + name)

def without_assignment(tree, name):
 return ast.dump(ast.Module(body=[n for n in tree.body if not (
  isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))], type_ignores=[]), include_attributes=False)

started = datetime.now(timezone.utc).isoformat()
check('exact_candidate_head', git('rev-parse', 'HEAD').decode().strip() == HEAD)
check('exact_candidate_tree', git('rev-parse', 'HEAD^{tree}').decode().strip() == TREE)
check('tracked_candidate_clean_before', not git('status', '--porcelain', '--untracked-files=no').strip())
before, after = entries(BASE), entries(HEAD)
changed = sorted(p for p in before.keys() & after.keys() if before[p] != after[p])
deleted = sorted(before.keys() - after.keys())
added = sorted(after.keys() - before.keys())
check('only_authorized_existing_paths_changed', set(changed) == set(CODE + STATE), paths=changed)
check('no_existing_paths_deleted', not deleted, paths=deleted)
check('additions_only_current_correction_or_evidence', all(p.startswith((ENG + 'localized-repair-c270/correction/', ENG + 'localized-repair-c270/evidence/correction-20261120/')) for p in added), paths=added)
unchanged = sorted(p for p in before.keys() & after.keys() if before[p] == after[p])
check('frozen_control_contract_tests_history_preserved', all(p in unchanged for p in before if p.startswith((
 ENG + 'localized-repair-c260/', ENG + 'localized-repair-c270/control/',
 ENG + 'localized-repair-c270/evidence/candidate/', ENG + 'localized-repair-c270/evidence/recovery-20261120/'))), unchanged_tree_entries=len(unchanged))

pin_rows = []
for path in CODE[1:]:
 old = ast.parse(source(BASE, path))
 new = ast.parse((REPO / path).read_bytes())
 check('only_dependency_table_ast_changed:' + path, without_assignment(old, 'DEPENDENCIES') == without_assignment(new, 'DEPENDENCIES'))
 for key, value in assignment(new, 'DEPENDENCIES').items():
  if len(value) == 3:
   relative, size, digest = value
  else:
   relative, (size, digest) = key, value
  dep_path = ENG + relative
  actual = identity((REPO / dep_path).read_bytes())
  row = {'consumer': path, 'dependency': dep_path, 'declared': {'bytes': size, 'sha256': digest}, 'actual': actual}
  pin_rows.append(row)
  check('current_pin:' + path + ':' + dep_path, actual == row['declared'])

source_ast = ast.parse((REPO / CODE[0]).read_bytes())
source_pin = {'bytes': assignment(source_ast, 'DEPENDENCY_BYTES'), 'sha256': assignment(source_ast, 'DEPENDENCY_SHA256')}
check('c265_c257_pin', source_pin == identity((REPO / (ENG + 'localized-repair-c257/ownership.py')).read_bytes()))
old_source_ast = ast.parse(source(BASE, CODE[0]))
old_class = next(n for n in old_source_ast.body if isinstance(n, ast.ClassDef) and n.name == 'Source')
new_class = next(n for n in source_ast.body if isinstance(n, ast.ClassDef) and n.name == 'Source')
old_methods = {n.name: ast.dump(n, include_attributes=False) for n in old_class.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
new_methods = {n.name: ast.dump(n, include_attributes=False) for n in new_class.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
changed_methods = sorted(k for k in old_methods.keys() | new_methods.keys() if old_methods.get(k) != new_methods.get(k))
check('c265_only_two_methods_changed', changed_methods == ['scan_class', 'site'], changed_methods=changed_methods)
old_source_ast.body = [n for n in old_source_ast.body if not (isinstance(n, ast.ClassDef) and n.name == 'Source')]
source_ast.body = [n for n in source_ast.body if not (isinstance(n, ast.ClassDef) and n.name == 'Source')]
check('c265_other_module_definitions_unchanged', ast.dump(old_source_ast, include_attributes=False) == ast.dump(source_ast, include_attributes=False))

manifest_path = ENG + 'localized-repair-c270/correction/PIN-CHANGES.json'
pin_manifest = json.loads((REPO / manifest_path).read_text())
for row in pin_manifest['files']:
 check('manifest_before:' + row['path'], identity(source(BASE, row['path'])) == row['before'])
 check('manifest_after:' + row['path'], identity((REPO / row['path']).read_bytes()) == row['after'])
for row in pin_manifest['updated_dependencies']:
 check('manifest_dependency_before:' + row['consumer'] + ':' + row['dependency'], identity(source(BASE, row['dependency'])) == row['before'])
 check('manifest_dependency_after:' + row['consumer'] + ':' + row['dependency'], identity((REPO / row['dependency']).read_bytes()) == row['after'])
check('manifest_nine_updated_entries', len(pin_manifest['updated_dependencies']) == 9)

snap_prefix = ENG + 'localized-repair-c270/evidence/correction-20261120/implementer-preflight/checked-code/'
snapshots = [p for p in after if p.startswith(snap_prefix)]
for path in snapshots:
 original = path[len(snap_prefix):]
 check('preflight_snapshot:' + original, (REPO / path).read_bytes() == (REPO / original).read_bytes())
check('preflight_snapshots_complete', len(snapshots) == 6)
original_fixture_oracle = json.loads((REPO / (ENG + 'localized-repair-c270/control/EXPECTED.json')).read_text())
for row in original_fixture_oracle['supplied_sources'] + original_fixture_oracle['original_inputs']:
 check('frozen_oracle_input:' + row['path'], identity((REPO / row['path']).read_bytes()) == {'bytes': row['bytes'], 'sha256': row['sha256']})
check('tracked_candidate_clean_after', not git('status', '--porcelain', '--untracked-files=no').strip())
check('candidate_head_unchanged', git('rev-parse', 'HEAD').decode().strip() == HEAD)

report = {
 'schema': 'ontokin.c270.independent-static-audit/1', 'reviewer': '/root/github_reconcile',
 'base_revision': BASE, 'candidate': HEAD, 'candidate_tree': TREE,
 'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
 'environment': {'python': sys.version, 'platform': platform.platform()},
 'command': [sys.executable, *sys.argv], 'audit_script': identity(Path(__file__).read_bytes()),
 'checks': checks, 'check_count': len(checks), 'failed': [c for c in checks if not c['passed']],
 'passed': all(c['passed'] for c in checks), 'current_dependency_pins': pin_rows,
 'changed_paths': changed, 'added_paths': added, 'unchanged_tree_entries': len(unchanged),
 'source_identities': [{'path': p, **identity((REPO / p).read_bytes())} for p in CODE],
 'limitations': ['Static source/pin/preservation audit only; no behavioral suite executed by this script.',
 'Exact candidate behavioral evidence is separately inspected; integration and saved-delivery gates are not closed by this report.']}
(OUT / 'CANDIDATE-STATIC-AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'candidate': HEAD, 'checks': len(checks), 'failed': report['failed'], 'passed': report['passed'], 'current_pins': len(pin_rows), 'unchanged_tree_entries': len(unchanged)}))
raise SystemExit(0 if report['passed'] else 1)
