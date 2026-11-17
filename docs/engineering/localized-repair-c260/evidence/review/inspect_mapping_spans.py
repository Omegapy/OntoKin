#!/usr/bin/env python3
"""Independently inspect fixed baseline object association spans, without product code."""
from pathlib import Path
import hashlib
import json
import re
import struct

ROOT = Path('/workspace/scratch/a827454f4cb7')
PROOF = ROOT/'OntoKin/docs/engineering/semantic-export-c210/evidence/proof'
CHECKS = []


def check(name, condition):
    CHECKS.append({'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)


def fixed_block(raw, header):
    start = raw.index(header)
    index = raw.index(b'{', start)
    depth = 1
    # The exact inspected fixture has no braces in strings/comments inside these blocks.
    while depth:
        index += 1
        depth += (raw[index] == ord('{')) - (raw[index] == ord('}'))
    return start, index+1


for endpoint in ['before', 'after']:
    source = {'main.ok': (PROOF/(endpoint+'.main.ok')).read_bytes(), 'hinges.ok': (PROOF/'hinges.ok').read_bytes()}
    raw = (PROOF/(endpoint+'.glb')).read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20+length])
    occurrences = gltf['extras']['ontokin']['program']['occurrences']
    check(endpoint+' occurrence count', len(occurrences) == 18)
    for path, record in occurrences.items():
        if path in ['first', 'second']:
            declaration = ('main.ok', ('object '+path+' @ "'+path+'": Rack').encode())
            definition = ('main.ok', b'public class Rack @ "rack"')
            expected_definition_id = ['entry','keyed-rack','definitions','rack']
        elif path.endswith('.blade'):
            declaration = ('hinges.ok', b'private part blade @ "blade": Blade')
            definition = ('hinges.ok', b'private class Blade @ "blade"')
            expected_definition_id = ['package','example.hinges','hinges','definitions','blade']
        else:
            declaration = ('main.ok', b'public parts fingers @ "fingers": mech.Finger')
            definition = ('hinges.ok', b'public class Finger @ "finger"')
            expected_definition_id = ['package','example.hinges','hinges','definitions','finger']
        check(endpoint+' definition identity '+path, record['definition_id'] == expected_definition_id
            and record['class_id'] == '/'.join(expected_definition_id))
        for key, (filename, header) in [('declaration', declaration), ('definition', definition)]:
            claim = record[key]
            start, end = fixed_block(source[filename], header)
            expected_source_id = 'entry' if filename == 'main.ok' else 'package:example.hinges@1.0.0'
            expected = {'source_id':expected_source_id, 'source_revision':'sha256:'+hashlib.sha256(source[filename]).hexdigest(),
                'filename':filename, 'start_byte':start, 'end_byte':end}
            check(endpoint+' '+key+' source span '+path, claim == expected)
        generated = record['generated']
        if generated is not None:
            input_claim = generated['input']
            check(endpoint+' generated input expression '+path,
                source[input_claim['filename']][input_claim['start_byte']:input_claim['end_byte']] == b'self.mounts')
            entry_claim = generated['input_entry']
            input_entry = source[entry_claim['filename']][entry_claim['start_byte']:entry_claim['end_byte']]
            expected_prefix = json.dumps(generated['key']).encode()+b': vec3('
            check(endpoint+' generated literal key source '+path, input_entry.startswith(expected_prefix) and input_entry.endswith(b')'))

result = {'schema':'ontokin.c260.independent-mapping-span-review/0.1','passed':True,'checks':CHECKS,
    'checkCount':len(CHECKS),'limitation':'Fixed-input source association inspection only; no candidate or product execution'}
(ROOT/'evidence/contract-review/MAPPING-SPANS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(CHECKS)}))
