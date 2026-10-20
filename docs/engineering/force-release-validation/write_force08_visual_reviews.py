"""Bind already performed human-readable image observations to actual raw files.

This formatter does not perform visual review or infer it from passing reports.
The input contains observations supplied after all 83 attempt-008 captures were
actually inspected by the named reviewers.
"""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path('/workspace/scratch/0229a0b41cd2')
ATTEMPT = Path('/tmp/ontokin-force05-release-attempt-008')
OUTPUT = ROOT / 'force05-release-reviews-008'
observations_path = ROOT / 'force08-visual-observations.json'
observations = json.loads(observations_path.read_text())
sheets_root = ROOT / 'force05-review-sheets-008'
sheets = json.loads((sheets_root / 'manifest.json').read_text())
assert not OUTPUT.exists(), 'Preserve earlier review records.'
OUTPUT.mkdir()

def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    with (OUTPUT / name).open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')

sheet_by_capture = {}
for sheet in sheets:
    source = Path(sheet['sheet'])
    assert sha(source) == sheet['sheet_sha256']
    shutil.copyfile(source, OUTPUT / source.name)
    for capture in sheet['captures']:
        path = Path(capture['path'])
        assert sha(path) == capture['sha256']
        assert str(path) not in sheet_by_capture
        sheet_by_capture[str(path)] = {'file': 'reviews/' + source.name, 'sha256': sheet['sheet_sha256']}
assert len(sheet_by_capture) == 83
shutil.copyfile(sheets_root / 'manifest.json', OUTPUT / 'performed-review-sheets.json')
shutil.copyfile(observations_path, OUTPUT / 'performed-observations.json')

for category, group, source_kind, output_name, count in [
    ('source', 'force-browser', 'source_component', 'force-source.json', 27),
    ('agent', 'agent-browser', 'agent_retrieved_artifact', 'force-agent.json', 21),
]:
    review = observations[category]
    assert review['defects'] == []
    report_path = ATTEMPT / 'artifacts' / group / 'browser-validation.json'
    report = json.loads(report_path.read_text())
    if 'browser_report_sha256' in review:
        assert review['browser_report_sha256'] == sha(report_path)
    rows = []
    consumed = set()
    for capture in report['captures']:
        path = report_path.parent / capture['file']
        assert sha(path) == capture['sha256'] and str(path) in sheet_by_capture
        key = capture['fixture'] + '-' + capture['view']
        assert key not in consumed
        consumed.add(key)
        row = {key: capture[key] for key in ('fixture', 'view', 'time_seconds', 'program_revision', 'artifact_sha256')}
        row.update(capture_sha256=capture['sha256'], status='reviewed', observation=review['observations'][key], defects=[])
        rows.append(row)
    assert consumed == set(review['observations']) and len(rows) == count
    write(output_name, {'schema_version': 'ontokin.force-visual-review/0.1', 'status': 'reviewed',
                       'reviewer': review['reviewer'], 'reviewed_at_utc': review['reviewed_at_utc'],
                       'browser_report_sha256': sha(report_path), 'source_kind': source_kind, 'captures': rows})

legacy = observations['legacy']
assert legacy['defects'] == []
groups = [('construction-demo-browser', 'viewer-results.json', 'construction.json'),
          ('surface-agent-browser', 'browser-results.json', 'surface.json'),
          ('impulse-agent-browser', 'browser-validation.json', 'impulse.json'),
          ('surface-native-browser', 'browser-results.json', None),
          ('agent-demo-browser', 'viewer-results.json', None),
          ('visual-browser', 'viewer-results.json', None)]
consumed = set()
other = []
for group, report_name, output_name in groups:
    report_path = ATTEMPT / 'legacy-full' / 'artifacts' / group / report_name
    report = json.loads(report_path.read_text())
    rows = []
    for capture in report['captures']:
        key = group + '/' + capture['file']
        assert key not in consumed
        consumed.add(key)
        path = report_path.parent / capture['file']
        digest = sha(path)
        if 'sha256' in capture:
            assert capture['sha256'] == digest
        row = {'status': 'reviewed', 'capture_sha256': digest, 'reviewer': legacy['reviewer'],
               'observation': legacy['observations'][key], 'review_completed_at_utc': legacy['reviewed_at_utc'],
               'capture_file': 'legacy/full/artifacts/' + key,
               'browser_report_file': 'legacy/full/artifacts/' + group + '/' + report_name,
               'browser_report_sha256': sha(report_path), 'source_commit': observations['source_commit'],
               'source_attempt': observations['attempt'], 'observed_visual_defects': [],
               'scope': 'Actual static image observation; numerical conformance, continuous motion and final release acceptance are separate.',
               'inspection_method': 'Every complete screenshot inspected with view_image at original sheet detail; whole images resized without cropping.',
               'review_sheet': sheet_by_capture[str(path)]}
        for field in ('fixture', 'time_seconds', 'view', 'camera_view', 'artifact_sha256', 'program_revision', 'source_revision', 'selected_object', 'viewport', 'demo'):
            if field in capture:
                row[field] = capture[field]
        rows.append(row)
    if output_name == 'construction.json':
        assert len(rows) == 1
        write(output_name, rows[0])
    elif output_name:
        assert len(rows) == 12
        write(output_name, rows)
    else:
        other.extend(rows)
assert consumed == set(legacy['observations']) and len(consumed) == 35 and len(other) == 10
write('legacy-other.json', {'schema_version': 'ontokin.legacy-visual-review/0.1', 'status': 'reviewed',
    'reviewer': legacy['reviewer'], 'review_completed_at_utc': legacy['reviewed_at_utc'],
    'source_commit': observations['source_commit'], 'source_attempt': observations['attempt'],
    'reviewed_capture_count': 10,
    'observation': 'All ten additional legacy captures were actually inspected. Some surface side views obscure rear forms through depth alignment. No blocking visual defect was observed.',
    'scope': 'These ten observations complete the 35-capture legacy inventory together with construction, surface and impulse reviews. Numerical and final release acceptance are separate.',
    'captures': other})
print(json.dumps({'output': str(OUTPUT), 'reviewed_captures': 83, 'source': 27, 'agent': 21, 'legacy': 35, 'retained_sheets': len(sheets)}))
