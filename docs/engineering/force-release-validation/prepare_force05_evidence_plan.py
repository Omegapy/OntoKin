"""Prepare explicit immutable collection references after actual release execution.

This script reads measured reports and separately supplied visual reviews. It
does not execute acceptance, alter raw reports or manufacture observations.
The repository collector and independent release auditor remain separate steps.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

attempt, reviews, output = map(lambda p: Path(p).absolute(), sys.argv[1:4])
assert not output.exists(), 'Preserve existing collection plans.'

def read(path):
    return json.loads(Path(path).read_text())

def ref(path):
    return {'$file': str(path)}

def execution(role):
    return ref('executions/' + role + '/execution.json')

driver = read(attempt / 'driver.json')
assert driver['status'] == 'passed' and driver['source_stable'], 'All actual execution roles must finish first.'
assert len(driver['steps']) == 20 and all(r['exit_code'] == 0 for r in driver['steps'])
legacy = attempt / 'legacy-full'
implementation = read(attempt / 'executions/source/execution.json')['source_before']['implementation']
copies = [{'source': str(attempt / name), 'destination': name}
          for name in ('executions', 'artifacts', 'reports', 'driver-logs', 'driver.json')]
copies += [{'source': str(legacy / name), 'destination': 'legacy/full/' + name}
           for name in ('summary.json', 'source-before.json', 'source-after.json', 'logs', 'reports', 'artifacts')]
copies.append({'source': str(legacy / 'workspace/examples'), 'destination': 'examples'})
copies.append({'source': str(reviews), 'destination': 'reviews'})

# Construction's raw browser provenance uses original repository-relative paths.
# Keep those exact files in the collected root rather than rewriting the report.
c_browser_path = legacy / 'artifacts/construction-demo-browser/viewer-results.json'
c_browser = read(c_browser_path)
for item in c_browser['provenance'].values():
    name = item['path']
    if not name.startswith('examples/'):
        copies.append({'source': str(legacy / 'workspace' / name), 'destination': name})

c_workflow = read(legacy / 'workspace/examples/construction/workflow.json')
c_native = read(legacy / 'reports/construction-demo-destination.json')['files']
assert len(c_native) == 1
c_native = c_native[0]
c_comparison = c_native['three_js']['comparison']
c_review = read(reviews / 'construction.json')
assert c_review['status'] == 'reviewed'
assert c_review['capture_sha256'] == c_browser['captures'][0]['sha256']
assert c_workflow['status'] == c_browser['status'] == c_comparison['status'] == 'passed'
assert c_native['validator']['errors'] == c_native['validator']['warnings'] == 0
assert all(x['status'] == 'passed' for x in c_native['geometry'])
c_files = {
    'source_bundle': 'examples/construction/program.bundle.json',
    'workflow': 'examples/construction/workflow.json',
    'artifact': 'examples/construction/keyed-rack.glb',
    'reference': 'examples/construction/keyed-rack.reference.json',
    'external_results': 'legacy/full/reports/construction-demo-destination.json',
    'viewer_results': 'legacy/full/artifacts/construction-demo-browser/viewer-results.json',
    'capture': 'legacy/full/artifacts/construction-demo-browser/' + c_browser['captures'][0]['file'],
}
# The construction schema uses a role beside each ordinary file identity. The
# collector's placeholder can insert that identity as the whole row only, so
# prepare its path/hash here from the original immutable file instead.
import hashlib
def provenance(role, name):
    path = legacy / 'workspace' / name if name.startswith('examples/') else legacy / name.removeprefix('legacy/full/')
    return {'role': role, 'path': name, 'sha256': 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()}

construction = {
    'schema_version': 'ontokin.construction-external-gate/0.1',
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'implementation': implementation,
    'program_revision': c_workflow['accepted_program_revision'],
    'source_manifest': c_workflow['source_manifest'],
    'artifact_sha256': c_workflow['artifact_sha256'],
    'checks': {
        'workflow': {'status': c_workflow['status'], 'checks': len(c_workflow['checks']), 'operations': c_workflow['operation_count']},
        'format': {'status': 'passed', 'errors': c_native['validator']['errors'], 'warnings': c_native['validator']['warnings']},
        'geometry': {'status': 'passed', 'objects': len(c_native['geometry'])},
        'motion': {'status': c_comparison['status'], 'pose_comparisons': c_comparison['object_pose_comparisons'],
                   'max_position_error_m': c_comparison['max_position_error_m'], 'max_rotation_error_rad': c_comparison['max_rotation_error_rad']},
        'viewer': {'status': c_browser['status'], 'checks': len(c_browser['checks']), 'pose_comparisons': c_browser['pose_comparisons'],
                   'capture_sha256': c_browser['captures'][0]['sha256'], 'visual_review': c_review},
    },
    'provenance': [provenance(role, name) for role, name in c_files.items()],
    'basis': 'Fresh actual workflow, native/browser results and separately performed visual review; original report bytes are retained.'
}
surface = {
    'schema_version': 'ontokin.surface-release-evidence/0.1', 'implementation': implementation,
    'workflow': ref('legacy/full/artifacts/surface-agent/workflow.json'),
    'native': {'build': ref('legacy/full/artifacts/surface-agent/build.json'),
               'destination': ref('legacy/full/reports/surface-agent-destination.json'),
               'browser': ref('legacy/full/artifacts/surface-agent-browser/browser-results.json'),
               'visual_reviews': read(reviews / 'surface.json')},
}
impulse = {
    'schema_version': 'ontokin.impulse-release-evidence/0.1', 'implementation': implementation,
    'workflow': ref('legacy/full/artifacts/impulse-agent/workflow.json'),
    'native': {'build': ref('legacy/full/artifacts/impulse-agent/native-build.json'),
               'destination': ref('legacy/full/reports/impulse-agent-destination.json'),
               'browser': ref('legacy/full/artifacts/impulse-agent-browser/browser-validation.json'),
               'visual_reviews': ref('reviews/impulse.json')},
}
roles = {
    'source': {'execution': execution('source')}, 'mapped-tests': {'execution': execution('mapped-tests')},
    'compatibility': {version: execution('regression-' + version) for version in ('3.11', '3.12', '3.13')},
    'force-agent': {'workflow': ref('artifacts/force-agent/workflow.json'), 'build_execution': execution('force-agent-build'), 'execution': execution('force-agent')},
    'force-delivery': {'workflow': ref('artifacts/force-delivery/workflow.json'), 'build_execution': execution('force-delivery-build'), 'execution': execution('force-delivery')},
    'force-native': {'workflow': ref('artifacts/source-force/workflow.json'), 'build_execution': execution('source-build'), 'execution': execution('force-native')},
    'agent-native': {'execution': execution('agent-native')},
    'force-browser': {'execution': execution('force-browser'), 'report': ref('artifacts/force-browser/browser-validation.json'), 'visual_review': ref('reviews/force-source.json')},
    'agent-browser': {'execution': execution('agent-browser'), 'report': ref('artifacts/agent-browser/browser-validation.json'), 'visual_review': ref('reviews/force-agent.json')},
    'legacy-visual': {'execution': execution('legacy-visual'), 'summary': ref('legacy/full/summary.json')},
    'legacy': {'executions': {name: execution(name) for name in ('core', 'agent', 'construction', 'surface', 'impulse')},
               'construction_external': ref('legacy/construction-external.json'), 'surface_external': ref('legacy/surface-external.json'),
               'impulse_external': ref('legacy/impulse-external.json')},
}
plan = {'schema_version': 'ontokin.force-evidence-collection-plan/0.1', 'copies': copies,
        'manifests': [{'destination': 'legacy/' + name + '-external.json', 'value': value}
                      for name, value in [('construction', construction), ('surface', surface), ('impulse', impulse)]], 'roles': roles}
with output.open('x') as stream:
    stream.write(json.dumps(plan, indent=2) + '\n')
print(json.dumps({'output': str(output), 'copies': len(copies), 'roles': len(roles), 'release_certified': False}))
