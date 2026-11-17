#!/usr/bin/env python3
"""Independent C258 finite controls; expected semantics come from source witnesses.

Candidate modules are called only for actual observations. Mutation fixtures
and numeric expected values are built without consulting candidate output.
"""
from copy import deepcopy
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import shutil
import struct
import subprocess
import sys
import time
import traceback
import types


HERE = Path(__file__).resolve().parent


def local_module(name, path):
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    sys.modules[name] = mod
    exec(compile(path.read_bytes(), str(path), 'exec'), mod.__dict__)
    return mod


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.candidate.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    fx = local_module('independent_c258_fixture', HERE/'fixture_support.py')
    nr = local_module('independent_c258_numeric', HERE/'numeric_reference.py')
    path = root/'docs/engineering/localized-repair-c258/follows.py'
    code = path.read_bytes()
    candidate = local_module('independent_c258_candidate', path)
    baseline = json.loads((HERE/'SOURCE-BASELINE.json').read_text())
    source = fx.source_bundle()
    raw = fx.original('before.glb')
    document, tail = fx.decode_glb(raw)
    before_status = subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True)
    assert before_status == ''
    (out/'follows-reviewed.py').write_bytes(code)
    for name in ('review_controls.py','fixture_support.py','numeric_reference.py'):
        (out/name).write_bytes((HERE/name).read_bytes())
    results = []
    started = time.monotonic()

    def retained(inputs):
        entries = {}
        folder = out/'retained-inputs'
        folder.mkdir(exist_ok=True)
        for name,data in inputs.items():
            if data is None:
                continue
            sha = hashlib.sha256(data).hexdigest()
            extension = '.glb' if name.endswith('.glb') else '.ok'
            target = folder/(sha+extension)
            if not target.exists():
                target.write_bytes(data)
            entries[name] = {'path':str(target.relative_to(out)), 'bytes':len(data), 'sha256':sha}
        return entries

    def input_receipt(inputs):
        return {name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
                for name,data in inputs.items() if data is not None}

    def compact(value):
        if isinstance(value, dict) and 'records' in value:
            keys = ['id','path','definitionId','childId','childPath','childDefinitionId',
                    'parentFrame','offsetPositionM','offsetRotationWxyz']
            return {'kind':value.get('kind'),'followCount':value.get('followCount'),
                    'historicalInputsBound':value.get('historicalInputsBound'),
                    'records':[{k:r[k] for k in keys if k in r} for r in value['records']]}
        return value

    def run(name, call, *, refuses=False, verify=None, files=None, artifact=None, keep=False):
        inputs = dict(source if files is None else files)
        if artifact is not None:
            inputs['artifact.glb'] = artifact
        item={'name':name,'expected':'typed refusal' if refuses else 'accepted observation',
              'inputs':input_receipt(inputs)}
        t=time.monotonic()
        try:
            answer=call()
            item['actual']='accepted'
            item['observed']=compact(answer)
            if refuses:
                raise AssertionError('accepted input required to refuse')
            if verify:
                verify(answer)
            item['status']='PASS'
            if keep:
                (out/(name+'.json')).write_text(json.dumps(answer,indent=2,allow_nan=False)+'\n')
                item['retainedInputs']=retained(inputs)
        except candidate.Fault as error:
            item['actual']='typed refusal'
            item['code']=error.code
            item['detail']=error.detail
            item['status']='PASS' if refuses else 'FAIL'
        except Exception as error:
            item['status']='FAIL'
            item['exception']=type(error).__name__
            item['detail']=str(error)
            item['traceback']=traceback.format_exc()
        if item['status']=='FAIL':
            item['retainedInputs']=retained(inputs)
            print('FAIL',name,item.get('code',item.get('exception')),item.get('detail'))
        item['seconds']=round(time.monotonic()-t,6)
        results.append(item)
        return item

    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    def expected_original(answer, endpoint='before'):
        rows=baseline['endpoints'][endpoint]['rows']
        require(answer['followCount']==len(rows)==8,'actual original follow count')
        indexed={tuple(x['id']):x for x in answer['records']}
        for expected in rows:
            actual=indexed[tuple(expected['element_id'])]
            require(actual['path']==expected['path'],'relation lexical path')
            require(actual['childId']==expected['child_element_id'],'complete child ID')
            require(actual['parentFrame']['objectId']==expected['parent_object_element_id'],'lexical owner frame ID')
            require(actual['parentFrame']['path']==expected['parent_frame'],'lexical owner frame path')
            require(actual['offsetPositionM']==expected['offset_position_m'],'source-derived offset')
            require(actual['offsetRotationWxyz']==expected['offset_rotation_wxyz'],'source quaternion')
            if 'definitionId' in actual:
                require(actual['definitionId']==expected['source_derived_definition_id'],'declaring relation identity')
        require(answer['artifactFollowDefinitionAuthority'] is None,'absent artifact relation definition authority')
        require(answer['artifactFollowSourceSpanAuthority'] is None,'absent artifact relation span authority')
        for key in ('executionAllowed','sourceValidityQualified','completeC255Semantic','jointUnionQualified'):
            require(answer[key] is False,'qualification boundary '+key)

    def origins(answer):
        count=0
        def walk(value):
            nonlocal count
            if isinstance(value,dict):
                if set(('file','startByte','endByteExclusive')) <= set(value):
                    f,a,b=value['file'],value['startByte'],value['endByteExclusive']
                    require(f in source and type(a) is int and type(b) is int and 0<=a<b<=len(source[f]),'valid original UTF-8 byte witness')
                    text=source[f][a:b].decode('utf-8')
                    require(bool(text.strip()),'nonempty actual token/declaration witness')
                    count+=1
                for x in value.values():walk(x)
            elif isinstance(value,list):
                for x in value:walk(x)
        walk(answer)
        require(count>100,'source origin traversal executed')
        for row in answer['records']:
            p=row['sourceOrigins']['declaration']
            actual=source[p['file']][p['startByte']:p['endByteExclusive']].decode()
            require(actual.startswith('public follow mounting @ "mounting" {') and actual.endswith('}'),'actual follow declaration')
            parent_slices=[source[p['file']][p['startByte']:p['endByteExclusive']].decode() for p in row['sourceOrigins']['parent']]
            require('self.parent_frame' in parent_slices and 'self.frame' in parent_slices,'actual transitive lexical FrameRef origins')

    def pointers(answer):
        for row in answer['records']:
            for field,pointer in row['artifactOrigins'].items():
                value=document
                for part in pointer.split('/')[1:]:
                    part=part.replace('~1','/').replace('~0','~')
                    value=value[int(part)] if isinstance(value,list) else value[part]
                require(value is not None,'pointer reaches actual artifact field')
            require('definitionId' not in row,'raw artifact does not invent relation definition ID')

    for endpoint in ('before','after'):
        files=fx.source_bundle(endpoint); artifact=fx.original(endpoint+'.glb')
        run('bound-'+endpoint,lambda e=endpoint:candidate.read_bound_endpoint(root,e),
            verify=lambda answer,e=endpoint:expected_original(answer,e),files=files,artifact=artifact,keep=True)
        run('raw-source-'+endpoint,lambda f=files:candidate.observe_source_follows(f),
            verify=lambda answer,e=endpoint:expected_original(answer,e),files=files)
        run('raw-artifact-'+endpoint,lambda b=artifact:candidate.observe_glb_follows(b),
            verify=lambda answer,e=endpoint:expected_original(answer,e),files=files,artifact=artifact)
    run('actual-source-origins',lambda:candidate.observe_source_follows(source),verify=origins)
    run('actual-artifact-pointers',lambda:candidate.observe_glb_follows(raw),verify=pointers,artifact=raw)

    def source_case(name,changes,verify=None,refuses=False):
        files,edits=fx.mutate_sources(changes)
        run(name,lambda:candidate.observe_source_follows(files),verify=verify,refuses=refuses,files=files)
        return files,edits

    def all_parents(answer,path):
        require(all(x['parentFrame']['path']==path for x in answer['records']), 'changed parent measured')

    world_changes=[('main.ok','parent_frame = self.frame;','parent_frame = world;')]
    world,world_edits=source_case('source-parent-world',world_changes,lambda a:all_parents(a,'world'))
    run('source-parent-world-old-artifact',lambda:candidate.compare_follows(world,raw),refuses=True,files=world,artifact=raw)
    rebound=fx.rebind_artifact(raw,world,world_edits)
    def world_metadata(doc):
        for row in fx.follow_rows(doc):row['parent_frame']='world'
        for node in fx.finger_nodes(doc):node['properties']['parent_frame']['value']='world'
    world_glb=fx.changed_artifact(rebound,world_metadata)
    run('paired-world-parent',lambda:candidate.compare_follows(world,world_glb),verify=lambda a:all_parents(a,'world'),files=world,artifact=world_glb,keep=True)
    source_case('source-missing-parent-initializer-uses-world',[('main.ok','        parent_frame = self.frame;\n','')],lambda a:all_parents(a,'world'))
    source_case('masked-parent-default',[('hinges.ok',': FrameRef = world;',': FrameRef = self.frame;')],expected_original)
    source_case('source-default-self-cycle',[('main.ok','        parent_frame = self.frame;\n',''),('hinges.ok',': FrameRef = world;',': FrameRef = self.frame;')],refuses=True)

    offset_statement='offset = pose(self.parent_frame, self.mount_offset, quat(1, 0, 0, 0));'
    def verify_first_offset(answer,value):
        row=next(x for x in answer['records'] if x['path']=='first.fingers["lower"].mounting')
        require(row['offsetPositionM']==value,'selected helper offset measured')
    changed_spacing,spacing_edits=source_case('source-helper-spacing',[('main.ok','mech.three_mounts(0.6[m])','mech.three_mounts(0.8[m])')],lambda a:verify_first_offset(a,[0.,-.8,0.]))
    run('source-helper-spacing-old-artifact',lambda:candidate.compare_follows(changed_spacing,raw),refuses=True,files=changed_spacing,artifact=raw)
    source_case('source-unit-equivalent-cm',[('main.ok','mech.three_mounts(0.6[m])','mech.three_mounts(60[cm])')],expected_original)
    source_case('source-unit-equivalent-mm',[('main.ok','mech.three_mounts(0.6[m])','mech.three_mounts(600[mm])')],expected_original)
    source_case('source-missing-offset-uses-zero',[('main.ok','        mount_offset = offset;\n','')],lambda a:require(all(r['offsetPositionM']==[0,0,0] for r in a['records']),'actual zero default'))
    source_case('source-offset-frame-mismatch',[('hinges.ok',offset_statement,'offset = pose(world, self.mount_offset, quat(1, 0, 0, 0));')],refuses=True)

    quaternion_inputs=[('quarter-turn',[0.5,0.5,0.5,0.5]),('negative-sign',[-0.5,-0.5,-0.5,-0.5]),
        ('half-turn',[0,1,0,0]),('nonexact-unit',[0.6,0.8,0,0]),('near-unit',[1.0000000000005,0,0,0]),
        ('small-component',[1,1e-20,0,0]),('minimum-subnormal',[1,5e-324,0,0])]
    quat_fixtures={}
    for name,components in quaternion_inputs:
        expected=nr.quaternion_reference(components)
        spelling=', '.join(repr(x) for x in components)
        changed='offset = pose(self.parent_frame, self.mount_offset, quat('+spelling+'));'
        files,edits=source_case('source-quaternion-'+name,[('hinges.ok',offset_statement,changed)],
            lambda a,w=expected:require(all(x['offsetRotationWxyz']==w for x in a['records']),'exact independently rounded source quaternion'))
        quat_fixtures[name]=(files,edits,expected)
    qfiles,qedits,qexpected=quat_fixtures['quarter-turn']
    qraw=fx.rebind_artifact(raw,qfiles,qedits)
    def rotation_metadata(doc):
        for row in fx.follow_rows(doc):row['offset_rotation_wxyz']=qexpected.copy()
    qraw=fx.changed_artifact(qraw,rotation_metadata)
    run('paired-nonidentity-quaternion',lambda:candidate.compare_follows(qfiles,qraw),
        verify=lambda a:require(all(x['offsetRotationWxyz']==qexpected for x in a['records']),'nonidentity matched'),files=qfiles,artifact=qraw,keep=True)
    signed=fx.changed_artifact(qraw,lambda d:[row.update(offset_rotation_wxyz=[-v for v in qexpected]) for row in fx.follow_rows(d)])
    run('paired-common-sign-equivalence',lambda:candidate.compare_follows(qfiles,signed),files=qfiles,artifact=signed)
    mixed=fx.changed_artifact(qraw,lambda d:fx.follow_rows(d)[0].update(offset_rotation_wxyz=[.5,-.5,.5,.5]))
    run('mixed-component-sign-refused',lambda:candidate.compare_follows(qfiles,mixed),refuses=True,files=qfiles,artifact=mixed)
    for name,literal in [('zero','0, 0, 0, 0'),('too-large','1.000000000002, 0, 0, 0'),('too-small','0.999999999998, 0, 0, 0'),('dimensioned','1[m], 0, 0, 0'),('arity','1, 0, 0')]:
        source_case('source-invalid-quaternion-'+name,[('hinges.ok',offset_statement,'offset = pose(self.parent_frame, self.mount_offset, quat('+literal+'));')],refuses=True)

    for name,changes in [
        ('wrong-parent-type',[('hinges.ok',': FrameRef = world;',': Length = world;')]),
        ('private-child-parent',[('hinges.ok','public param parent_frame','private param parent_frame')]),
        ('private-child-offset',[('hinges.ok','public param mount_offset','private param mount_offset')]),
        ('wrong-offset-type',[('hinges.ok',': Vec3<Length> = vec3(0[m], 0[m], 0[m]);',': Vec3<Time> = vec3(0[m], 0[m], 0[m]);')]),
        ('private-helper',[('hinges.ok','public fn three_mounts','private fn three_mounts')]),
        ('wrong-helper-param-type',[('hinges.ok','(spacing: Length)','(spacing: Time)')]),
        ('wrong-helper-result-type',[('hinges.ok','-> Keyed<Vec3<Length>>','-> Keyed<Vec3<Time>>')]),
        ('follow-visibility-absent',[('hinges.ok','public follow mounting','follow mounting')]),
        ('follow-field-absent',[('hinges.ok','        child = self;\n','')]),
        ('follow-field-extra',[('hinges.ok','        child = self;\n','        child = self;\n        other = self;\n')]),
        ('follow-field-duplicate',[('hinges.ok','        child = self;\n','        child = self;\n        child = self;\n')]),
        ('follow-child-not-self',[('hinges.ok','child = self;','child = self.blade;')]),
        ('parent-arithmetic',[('main.ok','parent_frame = self.frame;','parent_frame = self.frame + world;')]),
        ('offset-arithmetic',[('main.ok','mount_offset = offset;','mount_offset = offset + offset;')]),
        ('offset-wrong-unit',[('main.ok','mech.three_mounts(0.6[m])','mech.three_mounts(0.6[s])')]),
        ('nested-parent-override',[('main.ok','fingers["middle"].length = 0.65[m];','fingers["middle"].parent_frame = world;')]),
        ('nested-offset-override',[('main.ok','fingers["middle"].length = 0.65[m];','fingers["middle"].mount_offset = vec3(0[m], 0[m], 0[m]);')]),
        ('predefined-param-shadow',[('hinges.ok','public param parent_frame @','public param world @')]),
        ('implicit-frame-param-shadow',[('hinges.ok','public class Finger @ "finger" {','public class Finger @ "finger" {\n    public param frame @ "fake-frame": FrameRef = world;')]),
        ('helper-binder-shadow',[('hinges.ok','(spacing: Length)','(world: Length)')]),
        ('numeric-positive-huge-exponent',[('main.ok','mech.three_mounts(0.6[m])','mech.three_mounts(1e999999999[m])')]),
        ('numeric-negative-huge-exponent',[('main.ok','mech.three_mounts(0.6[m])','mech.three_mounts(1e-999999999[m])')]),
        ('numeric-long-lexeme',[('main.ok','mech.three_mounts(0.6[m])','mech.three_mounts(0.'+'1'*70+'[m])')]),
    ]:
        source_case('source-refusal-'+name,changes,refuses=True)
    source_case('module-default-public-class',[('hinges.ok','public class Finger','class Finger')],expected_original)
    source_case('module-default-public-helper',[('hinges.ok','public fn three_mounts','fn three_mounts')],expected_original)

    def artifact_case(name,change,refuses=True,raw_only=False,verify=None):
        changed=fx.changed_artifact(raw,change)
        run(name,lambda:candidate.observe_glb_follows(changed) if raw_only else candidate.compare_follows(source,changed),
            refuses=refuses,verify=verify,artifact=changed)
        return changed
    artifact_case('artifact-parent-world-measured',world_metadata,refuses=False,raw_only=True,verify=lambda a:all_parents(a,'world'))
    artifact_case('artifact-parent-world-source-mismatch',world_metadata)
    artifact_case('artifact-position-measured',lambda d:fx.follow_rows(d)[0].update(offset_position_m=[0.,-.8,0.]),refuses=False,raw_only=True,
        verify=lambda a:verify_first_offset(a,[0.,-.8,0.]))
    artifact_case('artifact-position-source-mismatch',lambda d:fx.follow_rows(d)[0].update(offset_position_m=[0.,-.8,0.]))
    for name,change in [
        ('missing-row',lambda d:fx.follow_rows(d).pop()),
        ('empty-rows',lambda d:d['extras']['ontokin'].update(follows=[])),
        ('duplicate-row',lambda d:fx.follow_rows(d).append(deepcopy(fx.follow_rows(d)[0]))),
        ('unknown-relation-key',lambda d:fx.follow_rows(d)[0]['element_id'].__setitem__(-1,'unknown')),
        ('wrong-relation-path',lambda d:fx.follow_rows(d)[0].update(path='first.fingers["lower"].different')),
        ('wrong-child-id',lambda d:fx.follow_rows(d)[0]['element_id'].__setitem__(2,'second')),
        ('wrong-child-path',lambda d:fx.follow_rows(d)[0].update(child_object='second.fingers["lower"]')),
        ('unknown-parent',lambda d:fx.follow_rows(d)[0].update(parent_frame='firstish.frame')),
        ('self-cycle',lambda d:fx.follow_rows(d)[0].update(parent_frame='first.fingers["lower"].frame')),
        ('source-key-claim',lambda d:fx.follow_rows(d)[0].update(definition_id=['invented'])),
        ('missing-offset',lambda d:fx.follow_rows(d)[0].pop('offset_position_m')),
        ('bool-offset',lambda d:fx.follow_rows(d)[0].update(offset_position_m=[True,0,0])),
        ('bad-offset-dimension',lambda d:fx.follow_rows(d)[0].update(offset_position_m=[0,0])),
        ('invalid-rotation',lambda d:fx.follow_rows(d)[0].update(offset_rotation_wxyz=[0,0,0,0])),
        ('zero-component-corruption',lambda d:fx.follow_rows(d)[0].update(offset_rotation_wxyz=[1,1e-20,0,0])),
        ('child-parent-property-conflict',lambda d:fx.finger_nodes(d)[0]['properties']['parent_frame'].update(value='world')),
        ('child-parent-property-missing',lambda d:fx.finger_nodes(d)[0]['properties'].pop('parent_frame')),
        ('child-parent-property-type',lambda d:fx.finger_nodes(d)[0]['properties']['parent_frame'].update(type='String')),
        ('child-offset-property-conflict',lambda d:fx.finger_nodes(d)[0]['properties']['mount_offset']['value'][1].update(value=-.8)),
        ('child-offset-property-missing',lambda d:fx.finger_nodes(d)[0]['properties'].pop('mount_offset')),
        ('child-offset-property-type',lambda d:fx.finger_nodes(d)[0]['properties']['mount_offset'].update(type='Vec3<Time>')),
        ('source-revision-conflict',lambda d:d['extras']['ontokin']['program']['sources']['entry'].update(source_revision='sha256:'+'0'*64)),
        ('source-span-float',lambda d:d['nodes'][2]['extras']['ontokin']['source_mapping']['definition'].update(start_byte=743.0)),
        ('child-class-conflict',lambda d:d['nodes'][2]['extras']['ontokin']['source_mapping'].update(class_id='entry/keyed-rack/definitions/rack')),
    ]:
        artifact_case('artifact-refusal-'+name,change)

    def two_cycle(doc):
        rows=fx.follow_rows(doc)
        rows[0]['parent_frame']=rows[1]['child_object']+'.frame'
        rows[1]['parent_frame']=rows[0]['child_object']+'.frame'
    artifact_case('artifact-two-follow-cycle',two_cycle,raw_only=True)
    def duplicate_incoming(doc):
        row=deepcopy(fx.follow_rows(doc)[0]);row['element_id'][-1]='another';row['path']=row['child_object']+'.another';fx.follow_rows(doc).append(row)
    artifact_case('artifact-two-incoming-follows',duplicate_incoming,raw_only=True)
    for ulps,accepted in ((8,True),(9,False)):
        changed=artifact_case('artifact-policy-'+str(ulps)+'-ulps',
            lambda d,n=ulps:fx.follow_rows(d)[0].update(offset_rotation_wxyz=[1+n*math.ulp(1.),0.,0.,0.]),refuses=not accepted)

    def transport(name,data):
        run(name,lambda:candidate.observe_glb_follows(data),refuses=True,artifact=data)
    transport('transport-short-header',b'glTF')
    transport('transport-wrong-magic',b'BAD!'+raw[4:])
    transport('transport-truncated',raw[:-4])
    transport('transport-oversized',b' '* (4*1024*1024+1))
    transport('transport-json-duplicate-key',fx.encode_glb({'extras':{'ontokin':{}},'nodes':[]},b'').replace(b'"nodes":[]',b'"nodes":[],"nodes":[]'))
    huge_source=dict(source);huge_source['main.ok']=b' '*65537
    run('source-size-limit',lambda:candidate.observe_source_follows(huge_source),refuses=True,files=huge_source)
    bad_source=dict(source);bad_source['main.ok']=b'\xff'+source['main.ok']
    run('source-invalid-utf8',lambda:candidate.observe_source_follows(bad_source),refuses=True,files=bad_source)
    run('public-io-long-path',lambda:candidate.read_bound_endpoint('/tmp/'+'x'*5000,'before'),refuses=True)
    run('bound-unknown-endpoint',lambda:candidate.read_bound_endpoint(root,'unknown'),refuses=True)

    # Exact historical admission on a durable, minimally copied altered fixture.
    stage=out/'bound-stage'/fx.PROOF
    stage.mkdir(parents=True)
    (stage/'before.main.ok').write_bytes(source['main.ok'].replace(b'0.65[m]',b'0.66[m]'))
    (stage/'hinges.ok').write_bytes(source['hinges.ok'])
    (stage/'before.glb').write_bytes(raw)
    run('bound-changed-exact-bytes',lambda:candidate.read_bound_endpoint(out/'bound-stage','before'),refuses=True,
        files={'main.ok':(stage/'before.main.ok').read_bytes(),'hinges.ok':source['hinges.ok']},artifact=raw)

    after_status=subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True)
    execution={'candidate':str(root),'commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
        'tree':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD^{tree}'],text=True).strip(),
        'readerSha256':hashlib.sha256(code).hexdigest(),'readerBytes':len(code),'platform':platform.platform(),'python':sys.version,
        'cleanBefore':before_status=='','cleanAfter':after_status=='','seconds':round(time.monotonic()-started,6),
        'inputs':fx.receipt(source,raw),'reviewScripts':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in
             ('review_controls.py','fixture_support.py','numeric_reference.py')}}
    summary={'total':len(results),'passed':sum(x['status']=='PASS' for x in results),
             'failed':sum(x['status']=='FAIL' for x in results),'results':results}
    (out/'EXECUTION.json').write_text(json.dumps(execution,indent=2)+'\n')
    (out/'RESULTS.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:summary[k] for k in ('total','passed','failed')}))
    return 1 if summary['failed'] else 0


if __name__=='__main__':
    raise SystemExit(main())
