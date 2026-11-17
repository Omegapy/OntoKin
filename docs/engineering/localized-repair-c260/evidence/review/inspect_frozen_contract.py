#!/usr/bin/env python3
"""Independent fixed-baseline document audit; no candidate reader or product imports."""
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import platform
import re
import struct
import sys

ROOT = Path('/workspace/scratch/a827454f4cb7')
REPO = ROOT/'OntoKin'
DRAFT = ROOT/'contract-draft/docs/engineering/localized-repair-c260'
EVIDENCE = ROOT/'evidence/contract-review'
ROWS = []


def check(name, value):
    ROWS.append({'name': name, 'passed': bool(value)})
    if not value:
        raise AssertionError(name)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def one(pattern, text):
    matches = re.findall(pattern, text, re.S)
    check('one fixed-source witness: '+pattern, len(matches) == 1)
    return matches[0]


def main():
    freeze = read_json(ROOT/'evidence/contract-author/FILE-INTEGRITY.json')
    for row in freeze['files']:
        data = (ROOT/'contract-draft'/row['path']).read_bytes()
        check('frozen file '+row['path'], len(data) == row['bytes'] and sha(data) == row['sha256'])
    inputs = read_json(DRAFT/'INPUTS.json')
    for row in inputs['files']:
        data = (REPO/row['path']).read_bytes()
        check('input binding '+row['path'], len(data) == row['bytes'] and sha(data) == row['sha256'])
    corpus = read_json(REPO/'docs/engineering/localized-repair-c253/corpus.json')
    for key, row in inputs['c253MatchingPins'].items():
        check('C253 matching pin '+key, corpus['files'][key] == row)

    observed = read_json(DRAFT/'BASELINE-INSPECTION.json')
    check('37 source witnesses', len(observed['sourceWitnesses']) == 37)
    for name, witness in observed['sourceWitnesses'].items():
        raw = (REPO/witness['path']).read_bytes()
        text = witness['text'].encode()
        check('witness source hash '+name, sha(raw) == witness['sourceSha256'])
        begin, end = witness['startByte'], witness['endByteExclusive']
        check('witness exact bytes '+name, type(begin) is int and type(end) is int and raw[begin:end] == text)
        starts = [match.start() for match in re.finditer(re.escape(text), raw)]
        check('witness occurrence '+name, len(starts) == witness['matchingOccurrences'] and starts[witness['selectedOccurrence']] == begin)

    proof = REPO/'docs/engineering/semantic-export-c210/evidence/proof'
    library = (proof/'hinges.ok').read_bytes()
    source = (proof/'before.main.ok').read_bytes()
    libtext, entry = library.decode(), source.decode()
    module_key = one(r'module KeyedRack @ "([^"]+)";', entry)
    scene_key = one(r'scene Demo @ "([^"]+)"', entry)
    libkey = one(r'module Hinges @ "([^"]+)";', libtext)
    package, version = one(r'from "([^"]+)" version "([^"]+)"', entry)
    finger_key = one(r'public class Finger @ "([^"]+)"', libtext)
    blade_key = one(r'private class Blade @ "([^"]+)"', libtext)
    collection, collection_key = one(r'public parts (\w+) @ "([^"]+)": mech.Finger', entry)
    part, part_key = one(r'private part (\w+) @ "([^"]+)": Blade', libtext)
    parent, parent_key = one(r'public site (pivot) @ "([^"]+)"', libtext)
    child, child_key = one(r'public site (base) @ "([^"]+)"', libtext)
    joint, joint_key, joint_body = one(r'public joint (\w+) @ "([^"]+)": hinge \{(.*?)\n    \}', libtext)
    check('ordered source parent', one(r'parent = ([^;]+);', joint_body) == 'self.'+parent)
    check('ordered source child', one(r'child = ([^;]+);', joint_body) == 'self.'+part+'.'+child)
    check('source signed basis axis', one(r'axis = ([^;]+);', joint_body) == 'vec3(0, 0, 1)')
    check('source literal limits', one(r'limits = ([^;]+);', joint_body) == 'range(-45[deg], 45[deg])')
    check('source literal initial', one(r'initial = ([^;]+);', joint_body) == '0[rad]')
    check('source interfaces identical', re.findall(r'interface = "([^"]+)";', libtext) == ['hinged.part', 'hinged.part'])
    check('source site sizes zero', re.findall(r'size = ([^;]+);', libtext) == ['0[m]', '0[m]'])
    helper = one(r'return keyed<Vec3<Length>> \{(.*?)\n    \};', libtext)
    override = one(r'mounts = keyed<Vec3<Length>> \{(.*?)\n        \};', entry)
    shapes = [sorted(re.findall(r'"([^"]+)":', helper)), sorted(re.findall(r'"([^"]+)":', override))]
    roots = re.findall(r'object (\w+) @ "([^"]+)": Rack', entry)
    check('source root and key shape', len(roots) == 2 and list(map(len, shapes)) == [3, 5])
    for key in [module_key, scene_key, libkey, finger_key, blade_key, collection_key, part_key, parent_key, child_key, joint_key, *sum(shapes, [])]:
        check('baseline stable key domain '+key, re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}', key) is not None)

    pi64 = float.fromhex('0x1.921fb54442d18p+1')
    radians = float(Fraction(45) * Fraction.from_float(pi64) / 180)
    check('Pi64/180 baseline exact canonical round', radians.hex() == '0x1.921fb54442d18p-1')
    definition = ['package', package, libkey, 'definitions', finger_key]
    expected = []
    expected_objects = {}
    for (name, root_key), keys in zip(roots, shapes):
        root_id = [module_key, scene_key, root_key]
        expected_objects[name] = root_id
        for key in keys:
            path = name+'.'+collection+'['+json.dumps(key)+']'
            oid = root_id+[collection_key, key]
            expected_objects[path] = oid
            expected_objects[path+'.'+part] = oid+[part_key]
            expected.append({'path': path+'.'+joint, 'element_id': oid+[joint_key], 'kind': 'hinge',
                'parent_site': path+'.'+parent, 'child_site': path+'.'+part+'.'+child,
                'axis': [0.0, 0.0, 1.0], 'limits': [-radians, radians], 'initial': 0.0})
    check('independent source associations count', len(expected) == len(observed['independentSourceRows']) == 8)
    recorded_source = {row['path']: row for row in observed['independentSourceRows']}
    check('recorded source identities unique and complete', len(recorded_source) == len(expected)
        and set(recorded_source) == {row['path'] for row in expected})
    for expected_row in expected:
        recorded = recorded_source[expected_row['path']]
        owner = expected_row['element_id'][:-1]
        pairs = {'path': 'path', 'element_id': 'elementId', 'kind': 'kind', 'parent_site': 'parentSitePath',
            'child_site': 'childSitePath', 'axis': 'axis', 'limits': 'limitsRad', 'initial': 'initialRad'}
        check('source row '+recorded['path'], all(expected_row[a] == recorded[b] for a, b in pairs.items()))
        check('source definition '+recorded['path'], recorded['definitionId'] == definition+[joint_key]
            and recorded['owningClassDefinitionId'] == definition and recorded['owningOccurrenceId'] == owner)
        check('ordered source sites '+recorded['path'], recorded['parentSiteId'] == owner+[parent_key]
            and recorded['childSiteId'] == owner+[part_key, child_key]
            and recorded['parentSiteDefinitionId'] == definition+[parent_key]
            and recorded['childSiteDefinitionId'] == ['package', package, libkey, 'definitions', blade_key, child_key])

    for endpoint in ('before', 'after'):
        entry_raw = (proof/(endpoint+'.main.ok')).read_bytes()
        raw = (proof/(endpoint+'.glb')).read_bytes()
        magic, version_number, total = struct.unpack_from('<III', raw, 0)
        check(endpoint+' GLB header', magic == 0x46546C67 and version_number == 2 and total == len(raw))
        count, chunk_type = struct.unpack_from('<II', raw, 12)
        check(endpoint+' JSON chunk', chunk_type == 0x4E4F534A and count % 4 == 0)
        doc = json.loads(raw[20:20+count])
        meta = doc['extras']['ontokin']
        actual = observed['actualArtifacts'][endpoint]
        check(endpoint+' exact artifact binding', actual['sha256'] == sha(raw) and actual['bytes'] == len(raw))
        check(endpoint+' rows equal independently derived source', meta['joints'] == expected)
        check(endpoint+' complete recorded artifact rows', actual['jointRows'] == [
            {'pointer': '/extras/ontokin/joints/'+str(i), 'value': row} for i, row in enumerate(meta['joints'])])
        check(endpoint+' row keys have no direct provenance', all(set(row) == {
            'path','element_id','kind','parent_site','child_site','axis','limits','initial'} for row in meta['joints']))
        check(endpoint+' no direct site table', 'sites' not in meta and 'sites' not in meta['program']
            and not actual['directSiteTablePresent'] and not actual['jointDefinitionFieldsPresent']
            and not actual['jointSourceSpanFieldsPresent'])
        object_nodes = [node['extras']['ontokin'] for node in doc['nodes']
            if node.get('extras',{}).get('ontokin',{}).get('kind') == 'object']
        check(endpoint+' complete 18 object association', {node['path']:node['element_id'] for node in object_nodes} == expected_objects)
        check(endpoint+' repeated mapping agreement', all(node['source_mapping'] == meta['program']['occurrences'][node['path']]
            and node['class_name'] == node['source_mapping']['class_id'] for node in object_nodes))
        manifest = {'schema_version': 'ontokin.bundle/0.1', 'entry_source_id': 'entry', 'units': [
            {'source_id': 'entry', 'package_id': None, 'version': None, 'filename': 'main.ok', 'source_revision': 'sha256:'+sha(entry_raw)},
            {'source_id': 'package:'+package+'@'+version, 'package_id': package, 'version': version, 'filename': 'hinges.ok', 'source_revision': 'sha256:'+sha(library)}]}
        canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        revision = 'sha256:'+sha(b'ontokin.bundle/0.1\0'+canonical)
        check(endpoint+' independently derived program manifest', manifest == meta['program']['manifest'])
        check(endpoint+' independently derived revision', revision == meta['program']['revision'] == actual['programRevision']
            and all(node['program_revision'] == revision for node in object_nodes))

    contract = (DRAFT/'CONTRACT.md').read_text()
    plan = (DRAFT/'CONTROL-PLAN.md').read_text()
    check('28 distinct future controls', re.findall(r'^\| (H\d\d) \|', plan, re.M) == ['H'+str(i).zfill(2) for i in range(1,29)])
    check('future plan unrun', '**Status: planned, unrun.**' in plan and observed['futureControlPlanExecuted'] is False)
    check('key-domain correction explicit', '[A-Za-z0-9][A-Za-z0-9._-]{0,63}' in contract)
    check('empty-keyed correction explicit', 'nonempty' in contract and 'empty' in contract)
    check('missing authority and nonclaims explicit', all(term in contract for term in [
        'no direct site table', 'No interface grants execution or release authority', 'revision', 'clean rebuild', 'unqualified']))
    # This independent numeric example makes future H07's rounding requirement concrete.
    vector = {'literal':'1.1[deg]', 'expectedBinary64':float(Fraction('1.1')*Fraction.from_float(pi64)/180).hex(),
        'prematureRoundedFactor':(float('1.1')*(pi64/180)).hex(), 'status':'review arithmetic; future implementation control unrun'}
    check('numeric policy distinguishable from premature rounding', vector['expectedBinary64'] != vector['prematureRoundedFactor'])
    for row in freeze['files']:
        check('freeze unchanged after audit '+row['path'], sha((ROOT/'contract-draft'/row['path']).read_bytes()) == row['sha256'])
    result = {'schema':'ontokin.c260.independent-contract-inspection/0.1', 'passed':True,
        'checks':ROWS, 'checkCount':len(ROWS), 'frozenFiles':freeze['files'], 'inputRevision':inputs['sourceRevision'],
        'inputTree':inputs['sourceTree'], 'python':sys.version, 'platform':platform.platform(),
        'additionalH07Vector':vector, 'qualification':'Contract/baseline inspection only; no hinge implementation or future plan executed'}
    (EVIDENCE/'INSPECTION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(ROWS),'report':str(EVIDENCE/'INSPECTION.json')}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        (EVIDENCE/'INSPECTION-FAILURE.json').write_text(json.dumps({'passed':False,'error':repr(error),'checks':ROWS},indent=2)+'\n')
        raise
