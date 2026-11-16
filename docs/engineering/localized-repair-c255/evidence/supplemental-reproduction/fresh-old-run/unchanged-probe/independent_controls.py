#!/usr/bin/env python3
"""Independent inert C255 controls, derived from frozen raw source/equations.

The production expected_state/semantic_state helpers are never used to build
positive records. Author test fixtures are neither imported nor consulted.
"""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import time

from independent_basis import MOUNTS, TIMES, SELECTED, rows, pose, sphere_mesh, box_mesh, program_revision

BASE=Path(__file__).resolve().parent


def load_module(path):
    spec=importlib.util.spec_from_file_location('c255_under_review',path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def semantic(length):
    parts=rows(length); bypath={r['path']:r for r in parts}
    objects=[]; sites=[]; follows=[]; hinges=[]
    for r in parts:
        oid=r['id']; path=r['path']; rack=oid[2]
        if r['owner'] is None:
            parameters={'finger_length':{'value':.6,'unit':'m'},
                        'mounts':{k:{'value':[0.,y,0.],'unit':'m'} for k,y in MOUNTS[rack].items()}}
            placement={'kind':'declared','frame':'world','position_m':[-1. if rack=='first' else 1.,0.,0.],'rotation_wxyz':[1.,0.,0.,0.]}
            tint=[.45,.45,.5,1.]
        else:
            L=r.get('length',r.get('size',[None])[0])
            parameters={'length':{'value':L,'unit':'m'},'tint':[.2,.6,.9,1.]}
            if r['kind']=='sphere':
                parameters.update(parent_frame={'object':bypath[rack]['id']},mount_offset={'value':[0.,r['y'],0.],'unit':'m'})
            placement={'kind':'undeclared'}; tint=[.2,.6,.9,1.]
        primitive={'kind':r['kind']}
        primitive['radius_m' if r['kind']=='sphere' else 'size_m']=r.get('radius',r.get('size'))
        objects.append({'id':oid,'path':path,'definitionId':r['definition'],
                        'owner':None if r['owner'] is None else bypath[r['owner']]['id'],
                        'parameters':parameters,'primitive':primitive,'appearance':tint,
                        'placement':placement,'matter':{'kind':'no_body','own_mass_kg':0,'aggregate_mass_kg':0},
                        'initialLinearVelocity_mps':[0.,0.,0.],'initialAngularVelocity_radps':[0.,0.,0.]})
        sites.append({'id':oid+['@system','origin'],'owner':oid,'frame':oid,'position_m':[0.,0.,0.],
                      'rotation_wxyz':[1.,0.,0.,0.],'interface':'rigid.origin','size_m':0.,'kind':'system'})
        if r['kind']=='sphere':
            finger=oid; blade=oid+['blade']; pivot=finger+['pivot']; base=blade+['base']
            sites.append({'id':pivot,'owner':finger,'frame':finger,'position_m':[0.,0.,0.],
                          'rotation_wxyz':[1.,0.,0.,0.],'interface':'hinged.part','size_m':0.,'kind':'authored'})
            sites.append({'id':base,'owner':blade,'frame':blade,'position_m':[-r['length']/2,0.,0.],
                          'rotation_wxyz':[1.,0.,0.,0.],'interface':'hinged.part','size_m':0.,'kind':'authored'})
            follows.append({'id':finger+['mounting'],'parentFrame':bypath[rack]['id'],'child':finger,
                            'offsetPosition_m':[0.,r['y'],0.],'offsetRotation_wxyz':[1.,0.,0.,0.]})
            hinges.append({'id':finger+['flex'],'kind':'hinge','parentSite':pivot,'childSite':base,
                           'axis':[0.,0.,1.],'axisFrame':pivot,'limits_rad':[-math.pi/4,math.pi/4],'initial_rad':0.})
    return {'units':{'length':'m','time':'s','angle':'rad','mass':'kg'},
            'frame':{'handedness':'right','up':'+Y','basis':'world','quaternionOrder':'WXYZ'},
            'scene':{'id':['keyed-rack','demo'],'duration_s':2,'gravity_mps2':[0.,0.,0.],'gravityFrame':'world'},
            'objects':objects,'sites':sites,'follows':follows,'hinges':hinges,
            'actions':[{'id':['keyed-rack','demo','flex'],'kind':'tween','joint':['keyed-rack','demo','first','fingers','middle','flex'],
                        'targetAngle':{'value':45,'unit':'deg'},'duration_s':1},
                       {'id':['keyed-rack','demo','travel'],'kind':'move','object':['keyed-rack','demo','first'],
                        'velocity_mps':[0.,.2,0.],'frame':'world','duration_s':2}],
            'events':[{'time_s':0,'mode':'sequence','operations':[{'operation':'start','action':['keyed-rack','demo','flex']},
                                                              {'operation':'start','action':['keyed-rack','demo','travel']}]}]}


def origin(artifacts,program,label):
    name=next(iter(artifacts))
    return {'artifact':name,'sha256':hashlib.sha256(artifacts[name]).hexdigest(),'location':'inert-control/'+label,'programRevision':program}


def hashes(byte_map):
    return {k:hashlib.sha256(v).hexdigest() for k,v in byte_map.items()}


def make_case(repo,case,layer='reference',suffix=''):
    proof=repo/'docs/engineering/semantic-export-c210/evidence/proof'
    before=(proof/'before.main.ok').read_bytes(); after=(proof/'after.main.ok').read_bytes()
    invalid=(proof/'rejected-candidate.ok').read_bytes(); library=(proof/'hinges.ok').read_bytes()
    start_bytes=after if case=='V2' else before
    candidate_bytes={'V1':after,'V2':before,'N1':invalid}[case]
    final_bytes=start_bytes if case=='N1' else candidate_bytes
    start_files={'main.ok':start_bytes,'hinges.ok':library}; final_files={'main.ok':final_bytes,'hinges.ok':library}
    start_artifacts={'control.bin':('independent inert starting bytes '+suffix).encode()}
    final_artifacts=copy.deepcopy(start_artifacts) if case=='N1' else {'control.bin':('independent inert endpoint bytes '+case+suffix).encode()}
    old='independent-accepted-start'+suffix; new=old if case=='N1' else 'independent-accepted-final'+suffix
    start={'acceptedRevision':old,'programRevision':program_revision(start_bytes,library),'sourceFiles':start_files,'artifacts':start_artifacts}
    final={'acceptedRevision':new,'programRevision':program_revision(final_bytes,library),'sourceFiles':final_files,'artifacts':final_artifacts}
    candidate={'candidateId':'candidate-'+case+suffix,'parentAcceptedRevision':old,
               'sourceFiles':{'main.ok':candidate_bytes,'hinges.ok':library},'artifacts':{} if case=='N1' else copy.deepcopy(final_artifacts)}
    decision={'status':'rejected' if case=='N1' else 'accepted','candidateId':candidate['candidateId'],
              'parentAcceptedRevision':old,'acceptedRevision':new,'boundary':'staged-before-accepted-replacement',
              'invalidEverAccepted':False,'diagnostic':None}
    if case=='N1':decision['diagnostic']={'code':'incompatible-dimension','expectedDimension':'length','receivedDimension':'mass',
                                       'mechanism':'compiler','message':'Staged 0.75 kg cannot initialize a Length.'}
    authority={'schema':'ontokin.c255.inert-authority/0.1','attemptId':'opaque-independent-'+case+suffix,'caseId':case,
               'start':start,'candidate':candidate,'retained':final,
               'rebuild':{'sourceFiles':copy.deepcopy(final_files),'artifacts':copy.deepcopy(final_artifacts),
                          'cleanWorkspace':True,'declaredInputs':['hinges.ok','main.ok'],'determinism':'byte-exact'},'decision':decision}
    L=.75 if case=='V1' else .65
    geometry=[]; poses=[]
    for r in rows(L):
        vertices,triangles=sphere_mesh() if r['kind']=='sphere' else box_mesh(r['size'])
        geometry.append({'id':r['id'],'vertices_m':vertices,'triangles':triangles,'origin':origin(final_artifacts,final['programRevision'],'mesh/'+r['path'])})
        for t in TIMES:
            p=pose(r,t,L)
            poses.append({'id':r['id'],'time_s':t,'side':'after','position_m':p['position'],
                          'rotation_wxyz':p['quaternion'],'scale':[1.,1.,1.],'matrix':[v for row in p['matrix'] for v in row],
                          'origin':origin(final_artifacts,final['programRevision'],f'pose/{r["path"]}/{t}')})
    provenance={'acceptedRevision':new,'programRevision':final['programRevision'],'sourceHashes':hashes(final_files),
                'artifactHashes':hashes(final_artifacts),'semanticOrigin':origin(final_artifacts,final['programRevision'],'semantic')}
    observed={'schema':'ontokin.c255.observation/0.1','attemptId':authority['attemptId'],'caseId':case,'layer':layer,
              'semantic':semantic(L),'geometry':geometry,'poses':poses,'provenance':provenance,'decision':copy.deepcopy(decision)}
    observed['rebuild']={k:copy.deepcopy(observed[k]) for k in ['semantic','geometry','poses','provenance']}
    return observed,authority


def rotated_pose(row,angle):
    # Controls rotate an identity-orientation root about +Z; no production helpers.
    row['rotation_wxyz']=[math.cos(angle/2),0.,0.,math.sin(angle/2)]
    c,s=math.cos(angle),math.sin(angle); p=row['position_m']
    row['matrix']=[c,-s,0.,p[0],s,c,0.,p[1],0.,0.,1.,p[2],0.,0.,0.,1.]


def selected(seq,path):
    return next(r for r in seq if r.get('path')==path)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--positive-only',action='store_true')
    args=parser.parse_args();repo=args.repo; path=repo/'docs/engineering/localized-repair-c255/oracle.py'
    mod=load_module(path); corpus=mod.load_corpus(repo); outcomes=[]; beginning=time.monotonic()
    cache={}
    def case(name,expected=True,mutation=None,case='V1',layer='reference',suffix=''):
        key=(case,layer,suffix)
        if key not in cache:cache[key]=make_case(repo,case,layer,suffix)
        obs,authority=copy.deepcopy(cache[key])
        if mutation:mutation(obs,authority)
        got=mod.evaluate(corpus,case,obs,authority)
        actual=got.get('componentPass')
        claim_ok=got.get('realTrialSuccess') is None and got.get('executionAllowed') is False and got.get('artifactReaderQualified') is False
        record={'name':name,'expectedPass':expected,'actualPass':actual,'claimBoundary':claim_ok,'passed':actual is expected and claim_ok,'faults':got.get('faults')}
        outcomes.append(record)
        print(json.dumps({'name':name,'passed':record['passed'],'faults':record['faults'] if not record['passed'] else []}),flush=True)
    for c in ('V1','V2','N1'):case('independent-positive-'+c,case=c)
    case('independent-positive-delivery',layer='delivery')
    if args.positive_only:
        result={'oracleSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'outcomes':outcomes,'passed':all(x['passed'] for x in outcomes),'seconds':time.monotonic()-beginning}
        args.output.write_text(json.dumps(result,indent=2));return 0 if result['passed'] else 1
    # Positive transformations preserve identity rather than list positions.
    def reorder(o,a):
        for f in ['objects','sites','follows','hinges','actions']:o['semantic'][f].reverse()
        o['geometry'].reverse();o['poses'].reverse()
        for mesh in o['geometry']:mesh['triangles'].reverse()
    case('identity-pose-triangle-reordering',mutation=reorder)
    def qsign(o,a):
        for p in o['poses']:p['rotation_wxyz']=[-x for x in p['rotation_wxyz']]
    case('quaternion-sign-equivalence',mutation=qsign)
    case('legitimate-provenance-revision-artifact-changes',suffix='-consistent-second-identity')
    for mechanism in ('script_unit_validator','author_refusal'):
        def setmechanism(o,a,m=mechanism):a['decision']['diagnostic']['mechanism']=m;o['decision']=copy.deepcopy(a['decision'])
        case('N1-positive-'+mechanism,case='N1',mutation=setmechanism)
    # Semantic controls: independently known source graph and 16 unrelated objects.
    def obj(o,path=SELECTED):return selected(o['semantic']['objects'],path)
    faults=[
      ('wrong-selected-length',lambda o,a:obj(o)['parameters']['length'].__setitem__('value',.8)),
      ('wrong-shared-default',lambda o,a:obj(o,'first')['parameters']['finger_length'].__setitem__('value',.75)),
      ('wrong-target-second-middle',lambda o,a:obj(o,'second.fingers["middle"].blade')['primitive']['size_m'].__setitem__(0,.75)),
      ('selected-sphere-radius',lambda o,a:obj(o,'first.fingers["middle"]')['primitive'].__setitem__('radius_m',.061)),
      ('selected-sphere-motion',lambda o,a:next(p for p in o['poses'] if p['id']==['keyed-rack','demo','first','fingers','middle'])['position_m'].__setitem__(2,.01)),
      ('mass-tiny-nonzero',lambda o,a:obj(o)['matter'].__setitem__('own_mass_kg',1e-15)),
      ('aggregate-mass-tiny-nonzero',lambda o,a:obj(o)['matter'].__setitem__('aggregate_mass_kg',1e-15)),
      ('boolean-dimension',lambda o,a:obj(o)['primitive']['size_m'].__setitem__(0,True)),
      ('nan-source-dimension',lambda o,a:obj(o)['primitive']['size_m'].__setitem__(0,float('nan'))),
      ('units-kg-as-length',lambda o,a:obj(o)['parameters']['length'].__setitem__('unit','kg')),
      ('units-centimetres',lambda o,a:o['semantic']['units'].__setitem__('length','cm')),
      ('wrong-world-handedness',lambda o,a:o['semantic']['frame'].__setitem__('handedness','left')),
      ('wrong-up-axis',lambda o,a:o['semantic']['frame'].__setitem__('up','+Z')),
      ('changed-appearance',lambda o,a:obj(o)['appearance'].__setitem__(0,.21)),
      ('changed-owner',lambda o,a:obj(o).__setitem__('owner',['keyed-rack','demo','second'])),
      ('changed-definition',lambda o,a:obj(o)['definitionId'].__setitem__(-1,'finger')),
      ('changed-follow',lambda o,a:o['semantic']['follows'][0].__setitem__('child',['keyed-rack','demo','second'])),
      ('changed-hinge-axis',lambda o,a:o['semantic']['hinges'][0].__setitem__('axis',[1,0,0])),
      ('changed-hinge-limit',lambda o,a:o['semantic']['hinges'][0]['limits_rad'].__setitem__(0,-math.pi/3)),
      ('changed-hinge-initial',lambda o,a:o['semantic']['hinges'][0].__setitem__('initial_rad',1e-15)),
      ('changed-origin-interface',lambda o,a:next(s for s in o['semantic']['sites'] if s['kind']=='system').__setitem__('interface','')),
      ('changed-site-position',lambda o,a:next(s for s in o['semantic']['sites'] if s['id'][-1]=='pivot')['position_m'].__setitem__(0,1e-15)),
      ('changed-action-velocity',lambda o,a:o['semantic']['actions'][1]['velocity_mps'].__setitem__(1,.200000000000001)),
      ('changed-action-duration',lambda o,a:o['semantic']['actions'][0].__setitem__('duration_s',1.1)),
      ('changed-event-order',lambda o,a:o['semantic']['events'][0]['operations'].reverse()),
      ('changed-event-time',lambda o,a:o['semantic']['events'][0].__setitem__('time_s',1e-15)),
      ('changed-duration',lambda o,a:o['semantic']['scene'].__setitem__('duration_s',2.1)),
      ('missing-identity',lambda o,a:o['semantic']['objects'].pop()),
      ('extra-identity',lambda o,a:o['semantic']['objects'].append(copy.deepcopy(o['semantic']['objects'][0])|{'id':['keyed-rack','demo','extra']})),
      ('duplicate-identity',lambda o,a:o['semantic']['objects'].append(copy.deepcopy(o['semantic']['objects'][0]))),
      ('missing-site',lambda o,a:o['semantic']['sites'].pop()),
      ('missing-time',lambda o,a:o['poses'].pop()),
      ('duplicate-time-identity',lambda o,a:o['poses'].__setitem__(-1,copy.deepcopy(o['poses'][0]))),
      ('before-boundary-side',lambda o,a:o['poses'][0].__setitem__('side','before')),
      ('nonfinite-position',lambda o,a:o['poses'][0]['position_m'].__setitem__(0,float('inf'))),
      ('zero-quaternion',lambda o,a:o['poses'][0].__setitem__('rotation_wxyz',[0,0,0,0])),
      ('norm-2-quaternion',lambda o,a:o['poses'][0].__setitem__('rotation_wxyz',[2,0,0,0])),
      ('boolean-scale',lambda o,a:o['poses'][0]['scale'].__setitem__(0,True)),
      ('tiny-explicit-scale',lambda o,a:o['poses'][0]['scale'].__setitem__(0,1+1e-15)),
      ('raw-reflection',lambda o,a:o['poses'][0]['matrix'].__setitem__(0,-1)),
      ('raw-scale',lambda o,a:o['poses'][0]['matrix'].__setitem__(0,1.01)),
      ('raw-shear',lambda o,a:o['poses'][0]['matrix'].__setitem__(1,.01)),
      ('raw-homogeneous-row',lambda o,a:o['poses'][0]['matrix'].__setitem__(15,1+1e-15)),
      ('raw-translation-mismatch',lambda o,a:o['poses'][0]['matrix'].__setitem__(11,.1)),
      ('raw-quaternion-matrix-mismatch',lambda o,a:o['poses'][0]['rotation_wxyz'].__setitem__(3,.01)),
      ('widened-observation-tolerance',lambda o,a:o.__setitem__('tolerance',1.)),
      ('correct-metadata-wrong-mesh',lambda o,a:o['geometry'][0]['vertices_m'][0].__setitem__(0,-.25)),
      ('missing-mesh',lambda o,a:o['geometry'].pop()),
      ('nonfinite-vertex',lambda o,a:o['geometry'][0]['vertices_m'][0].__setitem__(0,float('nan'))),
      ('boolean-mesh-index',lambda o,a:o['geometry'][0]['triangles'][0].__setitem__(0,True)),
      ('collapsed-triangle',lambda o,a:o['geometry'][0]['triangles'][0].__setitem__(1,o['geometry'][0]['triangles'][0][0])),
      ('duplicate-triangle',lambda o,a:o['geometry'][0]['triangles'].__setitem__(0,copy.deepcopy(o['geometry'][0]['triangles'][1]))),
      ('reversed-triangle',lambda o,a:o['geometry'][0]['triangles'][0].reverse()),
      ('missing-triangle',lambda o,a:o['geometry'][0]['triangles'].pop()),
      ('sphere-wrong-radius',lambda o,a:o['geometry'][1].__setitem__('vertices_m',[[v*1.05 for v in p] for p in o['geometry'][1]['vertices_m']])),
      ('sphere-unused-vertex',lambda o,a:o['geometry'][1]['vertices_m'].append([0,.06,0])),
      ('source-dependency-byte-changed',lambda o,a:a['candidate']['sourceFiles'].__setitem__('hinges.ok',a['candidate']['sourceFiles']['hinges.ok']+b'\n')),
      ('source-dependency-missing',lambda o,a:a['candidate']['sourceFiles'].pop('hinges.ok')),
      ('source-undeclared-input',lambda o,a:a['candidate']['sourceFiles'].__setitem__('ambient.ok',b'undeclared')),
      ('source-kg-accepted',lambda o,a:a['candidate']['sourceFiles'].__setitem__('main.ok',(repo/'docs/engineering/semantic-export-c210/evidence/proof/rejected-candidate.ok').read_bytes())),
      ('stale-parent-revision',lambda o,a:a['candidate'].__setitem__('parentAcceptedRevision','stale')),
      ('stale-accepted-revision',lambda o,a:a['retained'].__setitem__('acceptedRevision',a['start']['acceptedRevision'])),
      ('false-observation-acceptance',lambda o,a:o['decision'].__setitem__('acceptedRevision','author-assertion')),
      ('source-hash-mismatch',lambda o,a:o['provenance']['sourceHashes'].__setitem__('main.ok','0'*64)),
      ('artifact-hash-mismatch',lambda o,a:o['provenance']['artifactHashes'].__setitem__('control.bin','0'*64)),
      ('origin-artifact-mismatch',lambda o,a:o['poses'][0]['origin'].__setitem__('sha256','0'*64)),
      ('origin-stale-program',lambda o,a:o['geometry'][0]['origin'].__setitem__('programRevision',a['start']['programRevision'])),
      ('origin-missing-location',lambda o,a:o['geometry'][0]['origin'].__setitem__('location','')),
      ('origin-whitespace-location',lambda o,a:o['geometry'][0]['origin'].__setitem__('location','   ')),
      ('origin-control-location',lambda o,a:o['geometry'][0]['origin'].__setitem__('location','inert\ncontrol')),
      ('origin-NUL-location',lambda o,a:o['geometry'][0]['origin'].__setitem__('location','\x00')),
      ('hash-only-authority',lambda o,a:a['retained']['artifacts'].__setitem__('control.bin','0'*64)),
      ('empty-artifact-bytes',lambda o,a:a['candidate']['artifacts'].__setitem__('control.bin',b'')),
      ('rebuild-different-artifact',lambda o,a:a['rebuild']['artifacts'].__setitem__('control.bin',b'different')),
      ('rebuild-undeclared-input',lambda o,a:a['rebuild']['declaredInputs'].append('hidden/cache')),
      ('rebuild-unclean-workspace',lambda o,a:a['rebuild'].__setitem__('cleanWorkspace',False)),
      ('rebuild-different-semantic',lambda o,a:o['rebuild']['semantic']['objects'][0]['primitive']['size_m'].__setitem__(0,.2)),
      ('rebuild-different-pose',lambda o,a:o['rebuild']['poses'][0]['position_m'].__setitem__(0,4.)),
      ('rebuild-retroactive-normalization',lambda o,a:a['rebuild'].__setitem__('determinism','ignore-timestamp-after-failure')),
    ]
    for name,mutation in faults:case(name,False,mutation)
    for r in rows(.75):
        if r['path'] not in ('first.fingers["middle"]',SELECTED):
            def sibling(o,a,p=r['path']):
                s=obj(o,p);s['appearance'][0]+=.01
            case('unrelated-object-preserved/'+r['path'],False,sibling)
    # Inclusive and immediately-outside controls at an exactly-zero component.
    for layer,pos_tol,ang_tol in [('reference',1e-9,1e-9),('delivery',.001,.001)]:
        for outside in (False,True):
            d=math.nextafter(pos_tol,math.inf) if outside else pos_tol
            def shift(o,a,d=d):o['poses'][0]['position_m'][2]=d;o['poses'][0]['matrix'][11]=d
            case(layer+'-position-'+('outside' if outside else 'inclusive'),not outside,shift,layer=layer)
            ang=ang_tol*1.0001 if outside else ang_tol
            def turn(o,a,ang=ang):rotated_pose(o['poses'][0],ang)
            case(layer+'-angle-'+('outside' if outside else 'inclusive'),not outside,turn,layer=layer)
        def rawoutside(o,a,at=ang_tol):
            rotated_pose(o['poses'][0],at)
            c,s=math.cos(at*(1+1e-4)),math.sin(at*(1+1e-4))
            p=o['poses'][0];p['matrix'][0]=c;p['matrix'][1]=-s;p['matrix'][4]=s;p['matrix'][5]=c
        case(layer+'-raw-angle-independent-outside',False,rawoutside,layer=layer)
        def polaroutside(o,a,at=ang_tol,layer=layer):
            rotated_pose(o['poses'][0],at)
            delta=1e-10 if layer=='delivery' else 1e-22
            scale=1+ (5e-7 if layer=='delivery' else 5e-13)
            cs,sn=math.cos(at+delta),math.sin(at+delta)
            for i,v in {0:cs,1:-sn,2:0,4:sn,5:cs,6:0,8:0,9:0,10:1}.items():o['poses'][0]['matrix'][i]=v*scale
        case(layer+'-raw-polar-angle-outside-with-representation-residual',False,polaroutside,layer=layer)
        def polarinside(o,a,at=ang_tol,layer=layer):
            rotated_pose(o['poses'][0],at*.5)
            scale=1+ (5e-7 if layer=='delivery' else 5e-13)
            for i in (0,1,2,4,5,6,8,9,10):o['poses'][0]['matrix'][i]*=scale
        case(layer+'-raw-polar-angle-inside-with-representation-residual',True,polarinside,layer=layer)
    for outside in (False,True):
        t=math.nextafter(1e-6,math.inf) if outside else 1e-6
        case('delivery-time-'+('outside' if outside else 'inclusive'),not outside,
             lambda o,a,t=t:o['poses'][0].__setitem__('time_s',t),layer='delivery')
    case('reference-time-no-delivery-tolerance',False,lambda o,a:o['poses'][0].__setitem__('time_s',1e-12))
    # Exact source dimension boundary uses representable values flanking decimal .75+1e-12.
    target=.75+1e-12
    low=target if abs(target-.75)<=1e-12 else math.nextafter(target,-math.inf)
    high=math.nextafter(low,math.inf)
    case('source-dimension-inclusive-representable',True,lambda o,a:obj(o)['primitive']['size_m'].__setitem__(0,low))
    case('source-dimension-just-outside',False,lambda o,a:obj(o)['primitive']['size_m'].__setitem__(0,high))
    # All named N1 authority faults, with observation decision updated to avoid trivial mismatch.
    def decision_mutation(field,value):
        def f(o,a):a['decision'][field]=value;o['decision']=copy.deepcopy(a['decision'])
        return f
    case('N1-invalid-ever-accepted',False,decision_mutation('invalidEverAccepted',True),case='N1')
    case('N1-promoted',False,decision_mutation('status','accepted'),case='N1')
    case('N1-late-rejection-boundary',False,decision_mutation('boundary','after-accepted-replacement'),case='N1')
    case('N1-no-diagnostic',False,decision_mutation('diagnostic',None),case='N1')
    def harness(o,a):a['decision']['diagnostic']['mechanism']='common_harness';o['decision']=copy.deepcopy(a['decision'])
    case('N1-harness-only-rejection',False,harness,case='N1')
    case('N1-retained-artifact-mutated',False,lambda o,a:a['retained']['artifacts'].__setitem__('control.bin',b'changed-after-rejection'),case='N1')
    case('N1-retained-source-mutated',False,lambda o,a:a['retained']['sourceFiles'].__setitem__('main.ok',a['retained']['sourceFiles']['main.ok']+b'\n'),case='N1')
    case('N1-retained-revision-mutated',False,lambda o,a:a['retained'].__setitem__('acceptedRevision','different'),case='N1')
    # Missing output cannot pass the component.
    for value,label in [(None,'null'),({},'empty'),([], 'array')]:
        obs,a=make_case(repo,'V1');r=mod.evaluate(corpus,'V1',value,a)
        outcomes.append({'name':'missing-output-'+label,'passed':r['componentPass'] is False,'actualPass':r['componentPass'],'faults':r['faults']})
    # Inert denominators are separate from success and contain every started failure.
    accounting=[]
    for c in ('V1','V2','N1'):
        for outcome in ('missing_output','timeout','crash','infrastructure_incident','abstained','budget_exhausted'):
            r=mod.classify_attempt(c,True,True,outcome,True)
            ok=r['primaryDenominator']==(c!='N1') and r['negativeDenominator']==(c=='N1') and r['inertOutcomePass'] is False and r['realTrialSuccess'] is None
            accounting.append({'case':c,'outcome':outcome,'passed':ok,'result':r})
        r=mod.classify_attempt(c,False,False,'unavailable_before_start')
        accounting.append({'case':c,'outcome':'unavailable_before_start','passed':r['primaryDenominator']==0 and r['negativeDenominator']==0,'result':r})
    for bad in [('V1',True,True,'unavailable_before_start'),('V1',False,True,'timeout'),('V1',True,False,'timeout')]:
        try:mod.classify_attempt(*bad);ok=False
        except mod.Fault:ok=True
        accounting.append({'args':bad,'passed':ok})
    result={'schema':'ontokin.c255.independent-controls/0.1','oracleSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'basisSha256':hashlib.sha256((BASE/'independent_basis.py').read_bytes()).hexdigest(),
            'controlScriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'outcomes':outcomes,'accounting':accounting,'passed':all(x['passed'] for x in outcomes+accounting),'seconds':time.monotonic()-beginning,
            'notClaimed':['native artifact extraction','real clean rebuild','caller authentication','real trial/model success','baseline qualification','advantage']}
    args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps({'passed':result['passed'],'controls':len(outcomes),'accounting':len(accounting),'failures':[x['name'] for x in outcomes if not x['passed']],'seconds':result['seconds']}),flush=True)
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
