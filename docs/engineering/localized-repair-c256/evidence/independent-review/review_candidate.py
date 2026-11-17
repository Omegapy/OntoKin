#!/usr/bin/env python3
"""Independent C256 candidate checks, recording every attempted control."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mutations as mut
import independent_measure as independent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    reader = load_module('candidate_reader', a.candidate)
    proof = a.repo/'docs/engineering/semantic-export-c210/evidence/proof'
    raw = (proof/'after.glb').read_bytes()
    source = {'main.ok': (proof/'after.main.ok').read_bytes(), 'hinges.ok': (proof/'hinges.ok').read_bytes()}
    cases = []
    def check(name, call, expect='pass', sample=None):
        entry = {'name': name, 'expected': expect}
        if sample is not None:
            entry.update(inputSha256=hashlib.sha256(sample).hexdigest(), inputBytes=len(sample))
        try:
            returned = call()
            if expect == 'refuse':
                entry.update(passed=False, outcome='accepted', returnType=type(returned).__name__)
            else:
                entry.update(passed=True, outcome='passed')
        except reader.Fault as e:
            entry.update(passed=expect == 'refuse', outcome='refused', code=e.code, detail=e.detail)
        except Exception as e:
            entry.update(passed=False, outcome='uncaught-exception', exception=type(e).__name__, detail=str(e))
        cases.append(entry)

    def compare_endpoint(endpoint, length):
        output = reader.read_bound_endpoint(a.repo, endpoint)
        baseline = independent.measure(proof/(endpoint+'.glb'), length)
        assert output['historicalArtifactBound'] and output['sourceAssociationVerified']
        assert not output['semanticQualified'] and not output['completeC255Observation']
        assert not output['executionAllowed'] and output['realTrialSuccess'] is None
        assert len(output['identities']) == len(output['identityJoins']) == 18
        gotg = {tuple(x['id']): x for x in output['geometry']}
        gotp = {(tuple(x['id']), x['time_s']): x for x in output['poses']}
        assert set(gotg) == set(independent.expected_ids()) and len(gotp) == 126
        for row in baseline['geometry']:
            got = gotg[tuple(row['id'])]
            assert got['vertices_m'] == row['vertices'] and got['triangles'] == row['triangles']
        for row in baseline['poses']:
            got = gotp[(tuple(row['id']), row['time_s'])]
            assert max(abs(x-y) for x,y in zip(got['position_m'], row['position_m'])) < 1e-12
            assert independent.rotation_error(got['rotation_wxyz'], row['rotation_wxyz']) < 1e-12
            w,x,y,z=got['rotation_wxyz']
            def cross(u,v):
                return [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            columns=[]
            for basis in ([1.,0.,0.],[0.,1.,0.],[0.,0.,1.]):
                uv=cross([x,y,z],basis);uuv=cross([x,y,z],uv)
                columns.append([basis[j]+2*(w*uv[j]+uuv[j]) for j in range(3)])
            expected=[v for ri in range(3) for v in [columns[0][ri],columns[1][ri],columns[2][ri],got['position_m'][ri]]]+[0,0,0,1]
            assert max(abs(x-y) for x,y in zip(got['matrix'],expected)) < 1e-12
        bound = (proof/(endpoint+'.glb')).read_bytes()
        d, binary_start, payload = independent.split_glb(bound)
        def origin_check(origin):
            values, meta = independent.decode(d, payload, binary_start, origin['accessor'])
            assert origin['bufferView'] == meta['bufferView']
            assert origin['glbByteOffset'] == meta['absoluteFirstElementByte']
            assert origin['byteStride'] == meta['stride'] and origin['elementBytes'] == meta['elementBytes']
            parts = [bound[origin['glbByteOffset']+i*origin['byteStride']:origin['glbByteOffset']+i*origin['byteStride']+origin['elementBytes']] for i in range(origin['count'])]
            assert hashlib.sha256(b''.join(parts)).hexdigest() == origin['elementBytesSha256']
            return values
        for origins in output['measurementOrigins']['geometry']:
            values = origin_check(origins['position'])
            assert values == gotg[tuple(origins['id'])]['vertices_m']
            origin_check(origins['indices'])
        for origins in output['measurementOrigins']['poses']:
            for prop in ('translation','rotation'):
                track = origins[prop]
                times = [x[0] for x in origin_check(track['input'])]
                values = origin_check(track['output'])
                i,j = track['sampleIndices']
                assert track['storedTimes_s'] == [times[i],times[j]] and track['rawSamples'] == [values[i],values[j]]
                assert d['animations'][track['animation']]['channels'][track['channel']]['target'] == {'node':origins['node'],'path':prop}
        for row in output['geometry']+output['poses']:
            assert row['origin']['sha256'] == hashlib.sha256(bound).hexdigest()
        return output

    check('baseline-before-independent-all-arrays-and-origins',lambda: compare_endpoint('before',.65))
    check('baseline-after-independent-all-arrays-and-origins',lambda: compare_endpoint('after',.75))
    for name, sample in mut.structural_cases(raw).items():
        check('structural-'+name,lambda s=sample:reader.measure_glb(s), 'refuse', sample)
    for name, action in {
        'asset-list': lambda d:d.update(asset=[]),
        'root-meta-list': lambda d:d['extras'].update(ontokin=[]),
        'node-meta-list': lambda d:d['nodes'][0]['extras'].update(ontokin=[]),
        'node-rotation-zero':lambda d:d['nodes'][0].update(rotation=[0.,0.,0.,0.]),
        'node-rotation-nonunit':lambda d:d['nodes'][0].update(rotation=[0.,0.,0.,2.]),
        'node-translation-nonfinite':lambda d:d['nodes'][0].update(translation=[1e999,0.,0.]),
        'duplicate-stable-id':lambda d:d['nodes'][1]['extras']['ontokin'].update(element_id=d['nodes'][0]['extras']['ontokin']['element_id']),
        'missing-stable-id':lambda d:d['nodes'][0]['extras']['ontokin'].pop('element_id'),
        'node-source-map-id-mismatch':lambda d:d['nodes'][0]['extras']['ontokin']['source_mapping'].update(element_id=['wrong']),
        'node-program-mismatch':lambda d:d['nodes'][0]['extras']['ontokin'].update(program_revision='sha256:'+'0'*64)
    }.items():
        sample=mut.modify_json(raw,action)
        check(name,lambda s=sample:reader.measure_glb(s),'refuse',sample)

    baseline=reader.associate_glb(raw,source)
    def measured_change(sample, field, selected):
        observed=reader.associate_glb(sample,source)
        assert observed[field][selected] != baseline[field][selected]
        if field=='geometry':
            assert observed[field][selected]['vertices_m'] != baseline[field][selected]['vertices_m']
        else:
            assert (observed[field][selected]['position_m'],observed[field][selected]['rotation_wxyz']) != (baseline[field][selected]['position_m'],baseline[field][selected]['rotation_wxyz'])
        assert observed['artifact']['sha256'] == hashlib.sha256(sample).hexdigest()
        assert observed['sourceAssociationVerified'] and not observed['historicalArtifactBound']
        return observed
    changed_geometry=mut.mutate_accessor(raw,mut.position_accessor(raw,0),0,lambda v:[v[0]+.02,*v[1:]])
    check('changed-position-bytes-measured',lambda:measured_change(changed_geometry,'geometry',0),sample=changed_geometry)
    changed_pose=mut.mutate_accessor(raw,mut.channel_accessor(raw,0,'translation'),15,lambda v:[v[0]+.02,*v[1:]])
    check('changed-translation-bytes-measured',lambda:measured_change(changed_pose,'poses',1),sample=changed_pose)
    changed_q=mut.mutate_accessor(raw,mut.channel_accessor(raw,0,'rotation'),15,[0.,0.,math.sin(.2),math.cos(.2)])
    check('changed-rotation-bytes-measured',lambda:measured_change(changed_q,'poses',1),sample=changed_q)
    changed_time=mut.mutate_accessor(raw,0,15,[.26])
    check('changed-time-bytes-measured',lambda:measured_change(changed_time,'poses',1),sample=changed_time)
    def metadata_only():
        sample=mut.modify_json(raw,lambda d:d['nodes'][0]['extras']['ontokin'].update(geometry={'kind':'box','size':[999,999,999]}))
        out=reader.associate_glb(sample,source)
        assert [x['vertices_m'] for x in out['geometry']] == [x['vertices_m'] for x in baseline['geometry']]
        assert [x['position_m'] for x in out['poses']] == [x['position_m'] for x in baseline['poses']]
    check('metadata-dimensions-do-not-replace-measurements',metadata_only)
    def sign_equivalence():
        sample=mut.mutate_accessor(raw,mut.channel_accessor(raw,0,'rotation'),15,lambda v:[-x for x in v])
        out=reader.associate_glb(sample,source)
        for before, after in zip(baseline['poses'],out['poses']):
            assert independent.rotation_error(before['rotation_wxyz'],after['rotation_wxyz']) < 1e-12
    check('quaternion-sign-equivalence',sign_equivalence)
    def relocated_vertices(strided):
        doc,binary=mut.unpack(raw)
        ai=mut.position_accessor(raw,0)
        original,meta=independent.decode(*((lambda z:(z[0],z[2],z[1],ai))(independent.split_glb(raw))))
        start=len(binary)
        block=(b'\x00'*12) if not strided else b''
        for xyz in original:
            block+=struct.pack('<fff',*xyz)+(b'\x00'*4 if strided else b'')
        binary.extend(block)
        doc['buffers'][0]['byteLength']=len(binary)
        view={'buffer':0,'byteOffset':start,'byteLength':len(block),'target':34962}
        if strided:view['byteStride']=16
        doc['bufferViews'].append(view)
        doc['accessors'][ai]['bufferView']=len(doc['bufferViews'])-1
        doc['accessors'][ai]['byteOffset']=0 if strided else 12
        sample=mut.pack(doc,binary)
        out=reader.associate_glb(sample,source)
        assert out['geometry'][0]['vertices_m']==baseline['geometry'][0]['vertices_m']
        origin=out['measurementOrigins']['geometry'][0]['position']
        assert origin['bufferByteOffset']==start+(0 if strided else 12)
        assert origin['byteStride']==(16 if strided else 12)
    check('relocated-accessor-with-byte-offset-traversed',lambda:relocated_vertices(False))
    check('relocated-strided-positions-traversed',lambda:relocated_vertices(True))
    def change_mapping(d,path,field,value):
        node=next(n for n in d['nodes'] if n['extras']['ontokin']['path']==path)
        mapping=node['extras']['ontokin']['source_mapping']
        mapping[field]=value
        d['extras']['ontokin']['program']['occurrences'][path]=copy.deepcopy(mapping)
    for name, action in {
        'coordinated-wrong-declaration-span':lambda d:change_mapping(d,'first','declaration',dict(d['nodes'][0]['extras']['ontokin']['source_mapping']['declaration'],start_byte=903)),
        'coordinated-wrong-definition-span':lambda d:change_mapping(d,'first','definition',dict(d['nodes'][0]['extras']['ontokin']['source_mapping']['definition'],start_byte=301)),
        'coordinated-wrong-owner':lambda d:change_mapping(d,'first','owner_path','second'),
        'coordinated-wrong-steps':lambda d:change_mapping(d,'first','path_steps',[{'kind':'member','value':'second'}]),
        'coordinated-wrong-definition':lambda d:change_mapping(d,'first','definition_id',['entry','keyed-rack','definitions','wrong']),
        'source-manifest-digest':lambda d:d['extras']['ontokin']['program']['manifest']['units'][0].update(source_revision='sha256:'+'0'*64),
        'source-map-digest':lambda d:d['extras']['ontokin']['program']['sources']['entry'].update(source_revision='sha256:'+'0'*64),
        'source-entry-digest':lambda d:d['extras']['ontokin']['source'].update(entry_revision='sha256:'+'0'*64),
        'program-missing-occurrence':lambda d:d['extras']['ontokin']['program']['occurrences'].pop('first'),
        'program-extra-occurrence':lambda d:d['extras']['ontokin']['program']['occurrences'].update(extra={}),
        'program-manifest-list':lambda d:d['extras']['ontokin']['program'].update(manifest=[]),
    }.items():
        sample=mut.modify_json(raw,action)
        check('association-'+name,lambda s=sample:reader.associate_glb(s,source),'refuse',sample)
    for name,sources in {
        'opposite-endpoint-source':dict(source,**{'main.ok':(proof/'before.main.ok').read_bytes()}),
        'changed-library-source':dict(source,**{'hinges.ok':source['hinges.ok']+b'\n'}),
        'extra-source':dict(source,extra=b''),
        'missing-source':{'main.ok':source['main.ok']}
    }.items():
        check('association-'+name,lambda s=sources:reader.associate_glb(raw,s),'refuse')
    def bound_refuses_changed():
        with tempfile.TemporaryDirectory(prefix='c256-review-bound-') as tmp:
            root=Path(tmp);p=root/reader.PROOF;p.mkdir(parents=True)
            (p/'after.glb').write_bytes(changed_geometry)
            (p/'after.main.ok').write_bytes(source['main.ok']);(p/'hinges.ok').write_bytes(source['hinges.ok'])
            return reader.read_bound_endpoint(root,'after')
    check('strict-bound-rejects-measured-corruption',bound_refuses_changed,'refuse')
    def imports():
        tree=ast.parse(a.candidate.read_text())
        found=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):found.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):found.append(node.module)
        assert not any(x and ('ontokin' in x or 'oracle' in x) for x in found)
    check('producer-import-independence',imports)
    result={'candidate':str(a.candidate.resolve()),'candidateSha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
            'cases':cases,'passed':all(x['passed'] for x in cases),
            'caseCount':len(cases),'failures':[x for x in cases if not x['passed']]}
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('candidateSha256','passed','caseCount','failures')},indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
