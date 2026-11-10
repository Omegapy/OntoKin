"""Verify the coordinator's metadata-only fix without any native rerun."""
import copy
import datetime
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path('/workspace/scratch/d52b43d02a92')
SCOPE = ROOT / 'OntoKin/docs/engineering/contact-comparison-c192'
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


findings = read(OUT / 'findings.json')
checks = []
corrected_audit_rows = []
for base in (ROOT / 'c192-audit/first-reproduction', ROOT / 'c192-audit/reuse-reproduction'):
    old = read(base / 'results-before-review.json')
    new = read(base / 'results.json')
    expected = copy.deepcopy(old)
    for row in expected:
        performed = row['rebuild_exact']
        assert isinstance(performed, bool)
        row['fresh_rebuild_performed'] = performed
        row['rebuild_exact'] = True if performed else None
    assert new == expected
    corrected_audit_rows.extend(new)
    checks.append({'path': str(base / 'results.json'),
                   'before_sha256': sha(base / 'results-before-review.json'),
                   'after_sha256': sha(base / 'results.json'),
                   'only_expected_metadata_changed': True})

current = read(SCOPE / 'results.json')
assert current['native_verification'] == corrected_audit_rows
assert (OUT / 'results-reviewed.json').read_bytes() == (SCOPE / 'results.json').read_bytes()
# The coordinator applied this correction before the executable review started.
# The first manual delta check assumed an older snapshot and therefore failed.
snapshot_note = 'The executable review already captured the corrected results. The initial metadata delta check applied the correction twice and failed; that reviewer assumption is preserved separately.'

old_script = SCOPE / 'evidence/review-fixes/verify_builds-before.py'
new_script = SCOPE / 'tools/verify_builds.py'
assert sha(old_script) == 'bb2f9b100a3b4f590db1d368476f5f1287d15b087ce277e45c23b7458db410a4'
old_text, new_text = old_script.read_text(), new_script.read_text()
old_line = '        result = {"id": label, "submitted": original_score, "rebuild_exact": entry.get("rebuild", True),\n'
new_line = '        result = {"id": label, "submitted": original_score, "fresh_rebuild_performed": entry.get("rebuild", True),\n                  "rebuild_exact": True if entry.get("rebuild", True) else None,\n'
assert old_text.count(old_line) == 1 and new_text == old_text.replace(old_line, new_line)
(OUT / 'metadata-fix-script.diff').write_text(''.join(difflib.unified_diff(
    old_text.splitlines(True), new_text.splitlines(True), fromfile='verify_builds-before.py', tofile='verify_builds.py')))

for row in findings['artifact_checks']:
    artifact = Path(row['artifact'])
    assert all(sha(artifact / name) == value for name, value in row['hashes'].items())
for rel in ('docs/engineering/contact-comparison-c192/tools/score_submission.py',
            'docs/engineering/contact-comparison-c192/frozen/INPUT-FREEZE.json',
            'docs/engineering/guided-contact-c191/independent/checker/audit_mapping.py',
            'docs/engineering/guided-contact-c191/independent/checker/inspect_native.py',
            'docs/engineering/guided-contact-c191/independent/checker/c190_glb_difference.py'):
    assert sha(ROOT / 'OntoKin' / rel) == findings['reviewed_files_sha256'][rel]

fix = {'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'issue': 'N1', 'status': 'resolved', 'metadata_files': checks,
       'current_consolidated_results_sha256': sha(SCOPE / 'results.json'),
       'old_script_sha256': sha(old_script), 'new_script_sha256': sha(new_script),
       'only_result_field_semantics_changed': True,
       'all_reviewed_artifact_hashes_unchanged': True,
       'scorer_freeze_and_original_numerical_checkers_unchanged': True,
       'new_native_runs': 0, 'snapshot_note': snapshot_note,
       'disposition_path': str(SCOPE / 'evidence/review-fixes/disposition.json')}
(OUT / 'metadata-fix-verification.json').write_text(json.dumps(fix, indent=2) + '\n')
findings['resolved_issues'] = [dict(issue, status='resolved', verification='metadata-fix-verification.json')
                              for issue in findings['nonblocking_issues']]
findings['nonblocking_issues'] = []
findings['evidence_integration_recommendation'] = 'APPROVE'
findings['checks_finished_utc'] = fix['verified_at_utc']
findings['metadata_fix_verification'] = 'metadata-fix-verification.json'
findings['reviewed_files_sha256']['docs/engineering/contact-comparison-c192/tools/verify_builds.py'] = sha(new_script)
findings['reviewed_files_sha256']['docs/engineering/contact-comparison-c192/results.json'] = sha(SCOPE / 'results.json')
(OUT / 'findings.json').write_text(json.dumps(findings, indent=2) + '\n')
failed = read(OUT / 'metadata-fix-first-check-failure.json')
failed['resolved_explanation'] = snapshot_note
(OUT / 'metadata-fix-first-check-failure.json').write_text(json.dumps(failed, indent=2) + '\n')
print(json.dumps(fix, indent=2))
