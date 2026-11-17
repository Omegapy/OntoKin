"""Record fixed C260 design inputs and direct GLB metadata for human review.

This one-off inspection has no product observer API and accepts no candidate.
It imports no OntoKin implementation or expected-answer module.
"""
from pathlib import Path
import hashlib
import json
import platform
import struct
import subprocess
import sys
from fractions import Fraction

REPO = Path('/workspace/scratch/78ebb05e03a4/OntoKin')
OUT = Path('/workspace/scratch/a827454f4cb7/contract-draft/docs/engineering/localized-repair-c260')
EVIDENCE = Path('/workspace/scratch/a827454f4cb7/evidence/contract-author')
PROOF = 'docs/engineering/semantic-export-c210/evidence/proof'
paths = [
    'docs/language-design/OK-LANG-001-core-language-specification.md',
    'docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md',
    'docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md',
    'docs/engineering/semantic-export-c210/CONTRACT.md',
    'docs/engineering/localized-repair-c253/corpus.json',
    'docs/engineering/localized-repair-c257/ownership.py',
    'docs/engineering/localized-repair-c258/INTEGRATED-NEXT-TASK.md',
    *[PROOF + '/' + p for p in ['before.main.ok', 'after.main.ok', 'hinges.ok', 'before.glb', 'after.glb']],
]
def digest(raw):
    return hashlib.sha256(raw).hexdigest()
def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
def witness(path, text, occurrence=0):
    raw = (REPO / path).read_bytes()
    term = text.encode()
    positions = []
    start = 0
    while (start := raw.find(term, start)) >= 0:
        positions.append(start)
        start += len(term)
    assert len(positions) > occurrence, (path, text)
    start = positions[occurrence]
    return {'path': path, 'sourceSha256': digest(raw), 'startByte': start,
            'endByteExclusive': start + len(term), 'text': text,
            'selectedOccurrence': occurrence, 'matchingOccurrences': len(positions)}

revision = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
tree = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD^{tree}'], text=True).strip()
assert revision == '003b3a7827486405c3d00f039c1c9746c9be75fc'
assert tree == '325c7e50b42000e7c2976e3dd8c3babcec2649ba'
files = [{'path': p, 'bytes': (REPO / p).stat().st_size, 'sha256': digest((REPO / p).read_bytes())} for p in paths]
corpus = json.loads((REPO / 'docs/engineering/localized-repair-c253/corpus.json').read_text())
matching = {}
for name, binding in corpus['files'].items():
    match = next((f for f in files if f['path'] == binding['path']), None)
    if match:
        assert all(match[k] == binding[k] for k in ['path', 'bytes', 'sha256'])
        matching[name] = dict(binding)
dump(OUT / 'INPUTS.json', {'schema': 'ontokin.c260.contract-inputs/0.1',
    'contractVersion': '0.1.0', 'sourceRevision': revision, 'sourceTree': tree,
    'dependencyPolicy': 'Only pinned C257 lexical/module/occurrence identity utilities may be reused; no hinge values from ownership/follow/motion or producer expectations.',
    'files': files, 'c253MatchingPins': matching,
    'historicalAdmission': {'before': ['before.main.ok', 'hinges.ok', 'before.glb'],
                            'after': ['after.main.ok', 'hinges.ok', 'after.glb']},
    'notAuthoritativeForHinges': ['producer semantic sidecars', 'C255 expected records',
        'sampled motion', 'ownership or follow edges'],
    'implementationPresent': False})

hinges = PROOF + '/hinges.ok'
witnesses = {
    'libraryModule': witness(hinges, 'module Hinges @ "hinges";'),
    'fingerClass': witness(hinges, 'public class Finger @ "finger" {'),
    'bladeClass': witness(hinges, 'private class Blade @ "blade" {'),
    'jointDeclaration': witness(hinges, 'public joint flex @ "flex": hinge {\n        parent = self.pivot;\n        child = self.blade.base;\n        axis = vec3(0, 0, 1);\n        limits = range(-45[deg], 45[deg]);\n        initial = 0[rad];\n    }'),
    'parentExpression': witness(hinges, 'parent = self.pivot;'),
    'childExpression': witness(hinges, 'child = self.blade.base;'),
    'axisExpression': witness(hinges, 'axis = vec3(0, 0, 1);'),
    'limitsExpression': witness(hinges, 'limits = range(-45[deg], 45[deg]);'),
    'initialExpression': witness(hinges, 'initial = 0[rad];'),
    'parentSite': witness(hinges, 'public site pivot @ "pivot" {\n        pose = pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n        interface = "hinged.part";\n        size = 0[m];\n    }'),
    'childSite': witness(hinges, 'public site base @ "base" {\n        pose = pose(self.frame, vec3(-self.length / 2, 0[m], 0[m]), quat(1, 0, 0, 0));\n        interface = "hinged.part";\n        size = 0[m];\n    }'),
    'childPart': witness(hinges, 'private part blade @ "blade": Blade {\n        length = self.length;\n        tint = self.tint;\n    }'),
    'helperKeyLower': witness(hinges, '"lower": vec3(0[m], -spacing, 0[m])'),
    'helperKeyMiddle': witness(hinges, '"middle": vec3(0[m], 0[m], 0[m])'),
    'helperKeyUpper': witness(hinges, '"upper": vec3(0[m], spacing, 0[m])'),
}
for endpoint in ['before', 'after']:
    path = PROOF + '/' + endpoint + '.main.ok'
    witnesses[endpoint + 'EntryModule'] = witness(path, 'module KeyedRack @ "keyed-rack";')
    witnesses[endpoint + 'Scene'] = witness(path, 'scene Demo @ "demo" {')
    witnesses[endpoint + 'FirstRoot'] = witness(path, 'object first @ "first": Rack {')
    witnesses[endpoint + 'SecondRoot'] = witness(path, 'object second @ "second": Rack {')
    witnesses[endpoint + 'Generator'] = witness(path, 'public parts fingers @ "fingers": mech.Finger for (key, offset) in self.mounts')
    witnesses[endpoint + 'DefaultMembership'] = witness(path, 'public param mounts @ "mounts": Keyed<Vec3<Length>> = mech.three_mounts(0.6[m]);')
    for key in ['bottom', 'lower', 'middle', 'upper', 'top']:
        witnesses[endpoint + 'SecondKey' + key.title()] = witness(path, '"' + key + '":')

canonical_45deg = float(Fraction(45) * Fraction.from_float(float.fromhex('0x1.921fb54442d18p+1')) / 180)
assert canonical_45deg.hex() == '0x1.921fb54442d18p-1'
source_rows = []
for root, keys in [('first', ['lower', 'middle', 'upper']),
                   ('second', ['bottom', 'lower', 'middle', 'upper', 'top'])]:
    for key in keys:
        oid = ['keyed-rack', 'demo', root, 'fingers', key]
        opath = root + '.fingers[' + json.dumps(key) + ']'
        source_rows.append({'path': opath + '.flex', 'elementId': oid + ['flex'],
            'definitionId': ['package', 'example.hinges', 'hinges', 'definitions', 'finger', 'flex'],
            'owningOccurrenceId': oid, 'owningClassDefinitionId': ['package', 'example.hinges', 'hinges', 'definitions', 'finger'],
            'kind': 'hinge', 'parentSitePath': opath + '.pivot', 'parentSiteId': oid + ['pivot'],
            'parentSiteDefinitionId': ['package', 'example.hinges', 'hinges', 'definitions', 'finger', 'pivot'],
            'childSitePath': opath + '.blade.base', 'childSiteId': oid + ['blade', 'base'],
            'childSiteDefinitionId': ['package', 'example.hinges', 'hinges', 'definitions', 'blade', 'base'],
            'axis': [0, 0, 1], 'axisFrame': 'parent-site', 'limitsRad': [-canonical_45deg, canonical_45deg],
            'initialRad': 0.0, 'sourceOnlySiteCompatibility': {'interface': 'hinged.part', 'sizeM': 0.0},
            'derivation': 'Read joint/site/member keys from actual hinges.ok; expand three helper keys for first and five direct override keys for second; no product/expected module imported.'})
artifacts = {}
for endpoint in ['before', 'after']:
    path = PROOF + '/' + endpoint + '.glb'
    raw = (REPO / path).read_bytes()
    magic, version, total = struct.unpack_from('<4sII', raw)
    assert (magic, version, total) == (b'glTF', 2, len(raw))
    size, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(raw[20:20+size])
    meta = doc['extras']['ontokin']
    joints = meta['joints']
    direct = []
    by_path = {row['path']: row for row in source_rows}
    for i, row in enumerate(joints):
        assert set(row) == {'path', 'element_id', 'kind', 'parent_site', 'child_site', 'axis', 'limits', 'initial'}
        expected = by_path[row['path']]
        assert row['element_id'] == expected['elementId']
        assert row['kind'] == expected['kind']
        assert row['parent_site'] == expected['parentSitePath']
        assert row['child_site'] == expected['childSitePath']
        assert row['axis'] == expected['axis']
        assert row['limits'] == expected['limitsRad']
        assert row['initial'] == expected['initialRad']
        direct.append({'pointer': '/extras/ontokin/joints/' + str(i), 'value': row})
    assert len(joints) == len(source_rows) == 8
    assert len(doc['nodes']) == 18
    assert 'sites' not in meta and 'definitions' not in meta
    assert all(n['extras']['ontokin']['kind'] == 'object' for n in doc['nodes'])
    artifacts[endpoint] = {'path': path, 'sha256': digest(raw), 'bytes': len(raw),
        'jointRows': direct, 'jointCount': len(joints), 'objectNodeCount': len(doc['nodes']),
        'sourceBindingPointers': ['/extras/ontokin/source', '/extras/ontokin/program'],
        'programRevision': meta['program']['revision'],
        'directSiteTablePresent': False, 'jointDefinitionFieldsPresent': False,
        'jointSourceSpanFieldsPresent': False,
        'note': 'Endpoint site paths are direct artifact claims; site identities/definitions are source associations, not artifact site records.'}
dump(OUT / 'BASELINE-INSPECTION.json', {'schema': 'ontokin.c260.baseline-design-inspection/0.1',
    'sourceRevision': revision, 'sourceTree': tree, 'purpose': 'Fixed input inspection supporting contract review; not a candidate reader or product qualification.',
    'sourceWitnesses': witnesses, 'independentSourceRows': source_rows, 'actualArtifacts': artifacts,
    'numericDerivation': {'pi64': '0x1.921fb54442d18p+1', 'angle': 'round_binary64(exact_decimal(45) * exact_binary64(Pi64) / 180)',
        'angleHex': '0x1.921fb54442d18p-1', 'signedBasisAxisNormalization': 'identity; no sign canonicalization'},
    'executedChecks': {'inputFileBindings': len(files), 'sourceWitnesses': len(witnesses), 'artifactJointRows': 16,
        'sourceDistinctJointOccurrences': 8, 'matchingC253Bindings': len(matching)},
    'implementationQualification': False, 'futureControlPlanExecuted': False})
dump(EVIDENCE / 'EXECUTION.json', {'command': [sys.executable, __file__], 'python': sys.version,
    'platform': platform.platform(), 'sourceRevision': revision, 'sourceTree': tree,
    'productImports': [], 'productExecutions': 0, 'nativeStarts': 0, 'modelCalls': 0,
    'outputFiles': ['INPUTS.json', 'BASELINE-INSPECTION.json'],
    'passed': True, 'meaning': 'One-off static design-input inspection only; future contract controls unrun.'})
print(json.dumps({'passed': True, 'inputFiles': len(files), 'sourceWitnesses': len(witnesses), 'actualJointRows': 16}))
