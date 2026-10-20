"""Non-certifying read-only diagnostic for two already reproduced audit issues.

The original failed audit, execution envelopes, reports and PNGs stay unchanged.
This process previews the proposed comparison changes only, in memory. It is not
an execution of a committed corrected checker and cannot certify any gate.
"""
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import sys
import textwrap

ROOT = Path('/workspace/scratch/0229a0b41cd2/OntoKin')
sys.path.insert(0, str(ROOT))
from ontokin import force_conformance as force

evidence = Path('/tmp/ontokin-force05-evidence-006')
output = Path('/workspace/scratch/0229a0b41cd2/force05-audit-006-comparison-diagnostic.json')
assert not output.exists()
auditor = force.Auditor(evidence / 'evidence.json', root=evidence)
before = force.json_file(evidence / 'legacy/full/source-before.json')
rows = [{'path': r['path'], 'sha256': r['sha256'], 'byte_length': r['bytes']}
        for r in before['files'] if force.eligible_path(r['path'])]
assert rows != auditor.current['inputs']
assert sorted(rows, key=lambda r: r['path']) == auditor.current['inputs']
browser = force.json_file(evidence / 'artifacts/force-browser/browser-validation.json')
assert browser['complete_browser_corpus'] is False
assert browser['selected_fixtures'] == list(force.BROWSER_DESTINATIONS)

def adapted(method, old, new):
    source = textwrap.dedent(inspect.getsource(method))
    assert source.count(old) == 1
    namespace = {}
    exec(compile(source.replace(old, new), '<non-certifying comparison diagnostic>', 'exec'),
         vars(force), namespace)
    return namespace[method.__name__].__get__(auditor)

visual = adapted(force.Auditor.legacy_visual,
                 'eligible == self.current["inputs"]',
                 'sorted(eligible, key=lambda row: row["path"]) == self.current["inputs"]')
browser_check = adapted(force.Auditor.browser,
                 'report["complete_browser_corpus"] is True',
                 '(report["complete_browser_corpus"] is True or (not agent and report["selected_fixtures"] == list(BROWSER_DESTINATIONS)))')
checks = []
actions = [('closure', auditor.closure), ('compatibility', auditor.compatibility),
           ('legacy-visual-with-canonical-order', visual),
           ('source-native', auditor.native), ('source-browser-with-required-corpus', browser_check),
           ('legacy-non-provider-readers', auditor.legacy)]
for name, action in actions:
    try:
        details = action()
        checks.append({'id': name, 'diagnostic_result': 'no_remaining_exception',
                       'scalar_details': {k: v for k, v in details.items() if not isinstance(v, (dict, list))}})
    except Exception as error:
        checks.append({'id': name, 'diagnostic_result': 'exception',
                       'error': f'{type(error).__name__}: {error}'})
record = {'schema_version': 'ontokin.comparison-fix-diagnostic/0.1',
          'generated_at_utc': datetime.now(timezone.utc).isoformat(),
          'diagnostic_only': True, 'release_certified': False,
          'full_force_release_complete': False, 'full_product_complete': False,
          'original_failed_audit_sha256': force.file_identity(evidence / 'audit.json'),
          'script_sha256': 'sha256:' + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'in_memory_changes': ['Compare equal named legacy inputs in canonical string-path order.',
                                'Preview required nine-case source-browser coverage despite the known producer flag defect.'],
          'original_reports_modified': False, 'checks': checks,
          'next_required_action': 'Commit actual corrections, rerun every required role on the new eligible bytes, review fresh captures, and run the unchanged complete acceptance policy.'}
with output.open('x') as stream:
    stream.write(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
