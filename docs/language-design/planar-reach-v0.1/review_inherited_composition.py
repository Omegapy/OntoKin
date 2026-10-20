"""Disclosed baseline composition probe; never proposed reach execution."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
sys.dont_write_bytecode = True

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
repo = args.repo.resolve()
sys.path.insert(0, str(repo))
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.construction import compile_construction
from ontokin.construction_conformance import implementation_identity

base = repo / 'docs/language-design/planar-reach-v0.1'
sha = lambda data: 'sha256:' + hashlib.sha256(data).hexdigest()
def inventory():
    return {p.relative_to(base).as_posix(): sha(p.read_bytes())
            for p in sorted([base / 'acceptance.json', *base.glob('libraries/*.ok'), *base.glob('sources/p*.ok')])}
def git(*argv):
    return subprocess.check_output(['git', *argv], cwd=repo, text=True).strip()
def source_identity():
    return {'commit': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
            'implementation': implementation_identity(), 'proposal_inputs': inventory()}
before = source_identity()
old = {kind: (base / f'libraries/reach-{kind}.ok').read_text()
       for kind in ('exterior', 'parts', 'assets')}
def inherited(source):
    return (source.replace('ontokin "0.6";', 'ontokin "0.5";')
            .replace('profile "planar-reach-0.1";', 'profile "force-0.1";')
            .replace('ReachBranch', 'Bool')
            .replace('elbow_positive', 'true').replace('elbow_negative', 'false'))
new = {'exterior': inherited(old['exterior'])}
new['parts'], replacements = re.subn(
    r'return reach_planar\(.*?\);', 'return tween(self.shoulder, 0[rad], duration);',
    inherited(old['parts']), flags=re.S)
assert replacements == 1, 'Exactly one new operation body must be explicitly stubbed.'
new['assets'] = inherited(old['assets'])
for kind in ('parts', 'assets'):
    for dependency in ('exterior', 'parts'):
        if dependency in new:
            new[kind] = new[kind].replace(sha(old[dependency].encode()), sha(new[dependency].encode()))
modules = tuple(SourceUnit('package:proposal.reach-' + kind + '@0.1.0',
                           'reach-' + kind + '.ok', source.encode(),
                           'proposal.reach-' + kind, '0.1.0')
                for kind, source in new.items())
cases = {case['entry_source']: case for case in json.loads((base / 'acceptance.json').read_text())['source_cases']}
results = []
for path in sorted((base / 'sources').glob('p*.ok')):
    source = inherited(path.read_text())
    for kind in new:
        source = source.replace(sha(old[kind].encode()), sha(new[kind].encode()))
    try:
        compiler = compile_construction(ProgramBundle(SourceUnit('entry', 'reach-entry.ok', source.encode()), modules),
                                        level='constructed')
        expected = cases[path.relative_to(base).as_posix()]['expected']['expected_object_paths']
        if sorted(compiler.model.objects) != expected:
            raise AssertionError('Constructed object identity set differs from prepared expectation')
        results.append({'fixture': path.stem, 'status': 'baseline-constructed',
                        'objects': len(compiler.model.objects), 'object_paths': sorted(compiler.model.objects)})
    except Exception as error:
        results.append({'fixture': path.stem, 'status': 'failed',
                        'error': type(error).__name__ + ': ' + str(error)})
after = source_identity()
passed = before == after and all(r['status'] == 'baseline-constructed' for r in results)
report = {'schema_version': 'ontokin.planar-reach-inherited-composition-review/0.1',
          'status': 'passed' if passed else 'failed',
          'scope': 'Actual inherited construction of temporary in-memory substitutions only.',
          'proposed_reach_implemented': False, 'proposed_reach_evaluated': False,
          'atomic_reach_lifecycle_validated': False, 'destination_validated': False,
          'substitutions': ['0.6/planar-reach header becomes 0.5/force',
                            'ReachBranch becomes Bool; enum values become true/false',
                            'reach_planar method body becomes one zero-shoulder tween',
                            'all import digests recomputed from substituted dependency bytes'],
          'interpreter': {'executable': sys.executable, 'version': platform.python_version(),
                          'implementation': platform.python_implementation()},
          'command': [sys.executable, *sys.argv], 'script_sha256': sha(Path(__file__).read_bytes()),
          'source_before': before, 'source_after': after, 'source_stable_during_probe': before == after,
          'results': results, 'full_product_conformance_certified': False}
with args.output.open('x') as stream:
    json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps({'status': report['status'], 'fixtures': len(results),
                  'source_stable_during_probe': before == after, 'commit': before['commit'],
                  'interpreter': report['interpreter'], 'output': str(args.output)}))
raise SystemExit(0 if passed else 1)
