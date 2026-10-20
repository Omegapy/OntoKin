#!/usr/bin/env python3
"""Audit retained Agent/0.5 messages without running the compiler or simulator.

Only immutable bundle identity code is reused. Independent JSON Schema checks,
fixed source bytes, authored numerical expectations, exact clocks and a request
ledger establish the relationships claimed by this finite agent checkpoint.
No remote schema resolution, source execution or destination success is allowed.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
from dataclasses import replace
from fractions import Fraction as Q
from functools import lru_cache
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.bundle import ProgramBundle, load_bundle, load_file_manifest

PROTOCOL = 'ontokin.agent/0.5'
DATA = ROOT / 'docs/language-design/force-v0.1'
SCHEMAS = ('agent-v0.5/request.schema.json', 'agent-v0.5/response.schema.json',
           'agent-v0.5/diagnostic.schema.json', 'agent-v0.2/diagnostic.schema.json',
           'construction-v0.1/bundle.schema.json', 'impulse-v0.1/impulses.schema.json',
           'force-v0.1/forces.schema.json')
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_ENTRIES = 100000
TIME = re.compile(r'^(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?$')


class EvidenceError(ValueError):
    """The claimed checkpoint is missing, stale or internally inconsistent."""


def require(condition, label):
    if not condition:
        raise EvidenceError(label)


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def bounded(value):
    stack = [(value, 0)]; count = 0
    while stack:
        item, depth = stack.pop(); count += 1
        require(depth <= 64 and count <= MAX_ENTRIES, 'Bounded JSON depth/entry limit exceeded')
        if isinstance(item, dict):
            require(all(isinstance(k,str) for k in item), 'Nonstring object key')
            stack.extend((v, depth+1) for v in item.values())
        elif isinstance(item,list):
            stack.extend((v,depth+1) for v in item)
        elif isinstance(item,float):
            require(math.isfinite(item),'Nonfinite JSON number')
        elif type(item) not in (str,int,bool,type(None)):
            raise EvidenceError('Non-JSON value')


def decode(raw):
    require(len(raw) <= MAX_FILE_BYTES, 'JSON file exceeds its byte bound')
    def pairs(rows):
        result = {}
        for k,v in rows:
            require(k not in result, 'Duplicate JSON object key')
            result[k] = v
        return result
    def invalid(value):
        raise EvidenceError('Nonfinite JSON constant '+value)
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    bounded(result)
    return result


def clock(value):
    require(isinstance(value,str) and len(value) <= 4096 and TIME.fullmatch(value), 'Noncanonical output clock')
    return Q(value)


def authored_clock(value):
    return Q(int(value['numerator']),int(value['denominator']))


def vector(actual, expected, label, *, exact=False):
    require(isinstance(actual,list) and len(actual)==len(expected),label+' shape')
    for a,b in zip(actual,expected):
        require(type(a) in (int,float) and math.isfinite(a),label+' finite number')
        require(a==b if exact else abs(a-b)<=1e-9,label+' numerical value')


def orientation(actual, expected):
    require(len(actual)==len(expected)==4,'Quaternion shape')
    require(abs(math.hypot(*actual)-1)<=1e-12,'Quaternion is not unit length')
    aa=[a/math.hypot(*actual) for a in actual]; ee=[e/math.hypot(*expected) for e in expected]
    distance=min(math.dist(aa,ee),math.dist(aa,[-e for e in ee]))
    require(4*math.asin(min(1,distance/2))<=1e-9,'Quaternion orientation differs')


def identity():
    digest=hashlib.sha256()
    for p in sorted((ROOT/'ontokin').glob('*.py')):
        digest.update(p.name.encode()+b'\0'+p.read_bytes()+b'\0')
    version=re.search(r'__version__\s*=\s*[\'"]([^\'"]+)',(ROOT/'ontokin/__init__.py').read_text()).group(1)
    return dict(name='ontokin-reference',version=version,source_code_sha256='sha256:'+digest.hexdigest())


class SchemaChecks:
    """A closed, explicit registry. Unknown references never reach a network."""
    def __init__(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from referencing.exceptions import NoSuchResource
        def deny(uri):
            raise NoSuchResource(ref=uri)
        registry=Registry(retrieve=deny); self.documents={}; self.hashes={}
        for relative in SCHEMAS:
            raw=(ROOT/'docs/language-design'/relative).read_bytes(); doc=decode(raw)
            Draft202012Validator.check_schema(doc)
            require(doc['$id'] not in self.documents,'Duplicate registered schema ID')
            self.documents[doc['$id']]=doc;self.hashes[relative]=sha(raw)
            registry=registry.with_resource(doc['$id'],Resource.from_contents(doc))
        self.validators={id:Draft202012Validator(d,registry=registry) for id,d in self.documents.items()}

    def validate(self, kind, value):
        bounded(value)
        id=('https://ontokin.org/schemas/force-v0.1/forces.schema.json' if kind=='forces'
            else f'https://omegapy.github.io/OntoKin/schemas/ontokin.agent-{kind}-0.5.json')
        for error in self.validators[id].iter_errors(value):
            raise EvidenceError(f'{kind} schema at {list(error.absolute_path)}: {error.message[:500]}')


class SourceBook:
    def __init__(self):
        a=decode((DATA/'acceptance.json').read_bytes())
        self.cases={c['id']:copy.deepcopy(c) for c in a['source_cases']}
        for correction in decode((DATA/'source-errata.json').read_bytes())['sample_corrections']:
            row=next(r for r in self.cases[correction['id']]['expected_samples'] if
                     all(r[k]==correction[k] for k in ('time','side','target')))
            for k,v in correction['old'].items():require(row[k]==v,'Source erratum precondition changed')
            row.update(copy.deepcopy(correction['new']))
        self.bundles={name:load_file_manifest(DATA/c['file_manifest']) for name,c in self.cases.items()}
        for name,b in self.bundles.items():
            require(b.program_revision==self.cases[name]['program_revision'],'Frozen source identity differs')
        self.positive=[k for k,c in self.cases.items() if c['kind']=='positive']
        self.records={name:self.source_records(name) for name in self.positive}

    def objects(self,name):
        return {r['target'] for r in self.cases[name]['expected_samples']} | set(re.findall(
            r'\bobject\s+(\w+)\s+@',self.bundles[name].entry.text))

    def mass(self,name,target):
        text=self.bundles[name].entry.text
        if target in ('rack','carrier'):return None
        if target.startswith('rack.props['):
            key=re.fullmatch(r'rack\.props\["([^"]+)"\]',target).group(1)
            block=text[text.index('object rack'):]
            return float(re.search(r'"'+re.escape(key)+r'"\s*:\s*([-\deE+.]+)\[kg\]',block).group(1))
        block=re.search(r'\bobject\s+ball\s+[^{}]+{([^{}]*)}',text).group(1)
        match=re.search(r'body_mass\s*=\s*([-\deE+.]+)\[kg\]',block)
        # The unchanged pinned fixture library declares the default 2 kg body.
        return float(match.group(1)) if match else 2.0

    def source_records(self,name):
        b=self.bundles[name];text=b.entry.text;records={}
        module=re.search(r'\bmodule\s+\w+\s+@\s+"([^"]+)"',text).group(1)
        scene=re.search(r'\bscene\s+\w+\s+@\s+"([^"]+)"',text).group(1)
        frozen={s['start_byte']:s for s in self.cases[name]['force_statements']}
        for block in re.finditer(r'\bat\s+([-\deE+.]+)\[s\]\s+sequence\s*{([^{}]*)}',text):
            start=Q.from_float(float(block.group(1)))
            for index,part in enumerate(re.finditer(r'[^;]+;',block.group(2))):
                statement=part.group().strip()
                if not statement.startswith('force '):continue
                match=re.fullmatch(r'force (.+) @ "([^"]+)" using vector\(world, ([-\deE+.]+)\[N\], ([-\deE+.]+)\[N\], ([-\deE+.]+)\[N\]\) for ([-\deE+.]+)\[s\];',statement)
                require(match is not None,'Unexpected syntax in this fixed literal-force corpus')
                target,key,x,y,z,duration=match.groups();duration=Q.from_float(float(duration))
                require(duration>0 and key not in records,'Invalid trusted force definition')
                char_start=block.start(2)+part.start()+len(part.group())-len(part.group().lstrip())
                left=len(text[:char_start].encode());right=left+len(statement.encode())
                require(left in frozen and frozen[left]['end_byte']==right and frozen[left]['text']==statement,
                        'Independent statement scan differs from the frozen byte spans')
                steps=[a or b for a,b in re.findall(r'(\w+)|\["([^"]+)"\]',target)]
                records[key]=dict(force_key=key,force_element_id=[module,scene,'force',key],
                                  target_path=target,target_element_id=[module,scene,*steps],
                                  program_revision=b.program_revision,
                                  source_location=dict(source_id='entry',source_revision=b.entry.revision,start_byte=left,end_byte=right),
                                  sequence_index=index,force_world_n=[float(x),float(y),float(z)],
                                  activation_time_seconds=start,duration_seconds=duration,completion_time_seconds=start+duration)
        require(len(records)==len(frozen),'A force statement was not independently read')
        return records

    def check_record(self,name,record):
        wanted=self.records[name].get(record.get('force_key'))
        require(wanted is not None,'Record names an unauthored force')
        require(set(record) in (set(wanted),set(wanted)|{'kind'}),'Incomplete or extra force record fields')
        for k,v in wanted.items():
            if k.endswith('_seconds'):require(clock(record[k])==v,k+' differs from exact source clock')
            else:require(record[k]==v,k+' differs from exact source record')
        if 'kind' in record:require(record['kind'] in ('started','completed'),'Unknown force change kind')

    def check_projection(self,name,target,obj,time,side):
        f=obj['forces'];records=[r for r in self.records[name].values() if r['target_path']==target]
        def reached(t):return t<time or (t==time and side=='after')
        started=[r for r in records if reached(r['activation_time_seconds'])]
        ended=[r for r in started if reached(r['completion_time_seconds'])]
        active=sorted([r for r in started if r not in ended],key=lambda r:r['force_key'])
        require([r['force_key'] for r in f['active']]==[r['force_key'] for r in active],'Incomplete or unsorted active force set')
        require(type(f['started_count']) is int and f['started_count']==len(started),'Incorrect complete start count')
        require(type(f['completed_count']) is int and f['completed_count']==len(ended),'Incorrect complete completion count')
        clocks=[r['activation_time_seconds'] for r in started]+[r['completion_time_seconds'] for r in ended]
        latest=max(clocks) if clocks else None
        require((None if f['last_change_time_seconds'] is None else clock(f['last_change_time_seconds']))==latest,'Latest force boundary was lost')
        changes=([('completed',r['force_key']) for r in sorted(ended,key=lambda r:r['force_key']) if r['completion_time_seconds']==latest]+
                 [('started',r['force_key']) for r in started if r['activation_time_seconds']==latest])
        require([(r['kind'],r['force_key']) for r in f['last_changes']]==changes,'Incomplete latest-boundary history')
        for record in f['active']+f['last_changes']:self.check_record(name,record)
        total=[float(sum((Q.from_float(float(r['force_world_n'][i])) for r in active),Q(0))) for i in range(3)]
        vector(f['net_force_world_n'],total,'Canonical net force',exact=True)
        mass=self.mass(name,target)
        require(obj['own_mass_kg']==(0 if mass is None else mass),'Source own mass differs')
        if obj['motion']!='dynamic':
            require(f['acceleration_world_m_per_s2'] is None,'Nondynamic object has force acceleration')
        else:
            require(mass is not None and mass>0,'Unsupported dynamic body')
            gravity=re.search(r'gravity\s*=\s*vector\(world, ([-\deE+.]+)\[m/s\^2\], ([-\deE+.]+)\[m/s\^2\], ([-\deE+.]+)\[m/s\^2\]\)',self.bundles[name].entry.text)
            g=[float(x) for x in gravity.groups()]
            expected=[float(Q.from_float(a)+Q.from_float(b)/Q.from_float(mass)) for a,b in zip(g,total)]
            vector(f['acceleration_world_m_per_s2'],expected,'Canonical acceleration',exact=True)


class Reader:
    def __init__(self,directory,schemas=None):
        self.root=Path(directory).resolve(); self.schemas=schemas or SchemaChecks();self.book=SourceBook()
        self.files=set(); self.roles={};self.heads={};self.accepted=set();self.runs={};self.counter=0
        self.implementation=identity()
        self.run_ids=set()
        self.request_ledger={}
        self.bundles_by_revision={b.program_revision:b for b in self.book.bundles.values()}

    def read(self,name,expected=None):
        p=PurePosixPath(name)
        require(isinstance(name,str) and not p.is_absolute() and '\\' not in name and
                all(x not in ('..','.') for x in p.parts) and str(p)==name,'Unsafe evidence path')
        file=self.root
        for part in p.parts:
            file=file/part;require(not file.is_symlink(),'Evidence symlinks are not accepted')
        require(file.is_file() and file.stat().st_size<=MAX_FILE_BYTES,'Missing or oversized evidence file')
        raw=file.read_bytes()
        if expected is not None:require(sha(raw)==expected,'Evidence file digest differs: '+name)
        return decode(raw)

    def recursive(self,value):
        if isinstance(value,dict):
            if 'source_manifest' in value:
                revision=value.get('program_revision')
                require(revision in self.bundles_by_revision,'Source manifest has an unbound program revision')
                require(value['source_manifest']==self.bundles_by_revision[revision].manifest(),
                        'Source manifest differs from exact request source bytes')
            if 'implementation' in value:
                require(value['implementation']==self.implementation,'Mixed implementation identity')
            if 'forces' in value and 'pose_authority' in value:
                self.schemas.validate('forces',value['forces']);self.counter+=1
            if value.get('schema_version')==PROTOCOL:
                self.schemas.validate('response',value)
            for child in value.values():self.recursive(child)
        elif isinstance(value,list):
            for child in value:self.recursive(child)

    def at(self,role):
        require(role in self.roles,'Missing required workflow role: '+role)
        return self.roles[role]

    def sample(self,name,obj,row):
        expected_id=['force-demo','demo',*[a or b for a,b in re.findall(r'(\w+)|\["([^"]+)"\]',row['target'])]]
        require(obj['element_id']==expected_id,'State occurrence identity differs from source')
        require(obj['motion']==('dynamic' if row['dynamic_since'] is not None else 'prescribed'),
                'State motion mode differs from source oracle')
        exact=name in ('P18','P19','P20')
        for a,b in [('position_m','position_m'),('velocity_m_per_s','velocity_m_s'),('angular_velocity_rad_per_s','omega_world_rad_s')]:
            vector(obj[a],row[b],a,exact=exact)
        orientation(obj['orientation_wxyz'],row['orientation_wxyz'])
        if row['dynamic_since'] is not None:
            require(clock(obj['pose_authority']['since_seconds'])==authored_clock(row['dynamic_since']),'Dynamic origin changed')
            require(clock(obj['pose_authority']['trajectory_anchor_seconds'])==authored_clock(row['anchor_time']),'Trajectory anchor changed')
        self.book.check_projection(name,row['target'],obj,authored_clock(row['time']),row['side'])

    def register_candidate(self, request):
        """Bind source manifests to transported bytes, without source execution."""
        if request['operation']=='create':
            candidate=load_bundle(request['bundle'])
        elif request['operation']=='edit':
            base=self.bundles_by_revision.get(request['expected_program_revision'])
            require(base is not None,'Edit has no retained immutable source base')
            require(not request.get('module_changes'),'Unexpected dependency edit in fixed workflow')
            units={unit.source_id:unit for unit in base.units}
            grouped={}
            for patch in request['patches']:
                unit=units.get(patch['source_id'])
                require(unit is not None and patch['source_revision']==unit.revision,'Patch source revision differs')
                a,b=patch['start_byte'],patch['end_byte']
                require(0<=a<=b<=len(unit.raw) and unit.raw[a:b].decode()==patch['expected_text'],
                        'Patch bytes do not match retained source')
                grouped.setdefault(unit.source_id,[]).append(patch)
            for source_id, patches in grouped.items():
                unit=units[source_id];raw=unit.raw;end=len(raw)+1
                for patch in sorted(patches,key=lambda p:p['start_byte'],reverse=True):
                    a,b=patch['start_byte'],patch['end_byte']
                    require(b<end,'Overlapping source edits in retained request')
                    raw=raw[:a]+patch['replacement'].encode()+raw[b:];end=a
                units[source_id]=replace(unit,raw=raw)
            candidate=ProgramBundle(units['entry'],tuple(units[u.source_id] for u in base.modules))
        else:
            return
        self.bundles_by_revision[candidate.program_revision]=candidate

    def snapshot_state(self,name,state,time,side):
        require(set(state['objects'])==self.book.objects(name),'Snapshot omitted or added a source object')
        require(clock(state['time_seconds'])==time and state['side']==side,'Snapshot clock/side differs')
        rows={r['target']:r for r in self.book.cases[name]['expected_samples']
              if authored_clock(r['time'])==time and r['side']==side}
        require(rows,'No predetermined state oracle for this checkpoint snapshot')
        for target,obj in state['objects'].items():
            if target in rows:
                self.sample(name,obj,rows[target])
            else:
                self.book.check_projection(name,target,obj,time,side)
            # A full snapshot must not contradict its own object frame.
            frame=state['frames'].get(target+'.frame')
            require(frame is not None,'Missing object frame in snapshot')
            for key in ('position_m','orientation_wxyz','velocity_m_per_s','angular_velocity_rad_per_s'):
                require(frame[key]==obj[key],'Snapshot object/frame state differs')

    def create(self,role,name):
        q,r=self.at(role);b=self.book.bundles[name]
        require(q['operation']=='create' and q['bundle']==b.to_payload(),'Create did not send the fixed source bundle')
        require(q['expected_program_revision'] is None and q['requested_level']=='constructed','Wrong create admission')
        require(r['status']=='succeeded' and r['accepted_program_revision']==b.program_revision,'Source was not accepted')
        require(r['achieved_level']=='constructed','Create did not construct its source')
        self.snapshot_state(name,r['result']['initial_state'],Q(0),'before')
        return q,r

    def check_run(self,name):
        q,r=self.at(name+'/run');b=self.book.bundles[name];case=self.book.cases[name]
        require(q['operation']=='evaluate' and q['program_revision']==b.program_revision and q['run_id'] is None,'Incorrect source evaluation request')
        require(Q(q['until_seconds'])==authored_clock(case['request_horizon']),'Requested horizon was replaced')
        run=r['result']['run_state']
        require(r['status']=='succeeded' and r['achieved_level']=='evaluated' and run['status']=='ready' and run['failure'] is None,'Run is not ready')
        require(run['run_id']==r['run_id'] and run['program_revision']==b.program_revision and not run['candidate_only'] and run['origin']=='ordinary','Run provenance differs')
        require(clock(run['valid_until_seconds'])==authored_clock(case['request_horizon']) and run['valid_until_side']=='after','Run is not certified to the requested horizon')
        require(r['run_id'] not in self.run_ids,'Run identity reused across independent source evaluations')
        self.run_ids.add(r['run_id'])
        self.snapshot_state(name,run['last_valid_state'],authored_clock(case['request_horizon']),'after')
        self.runs[name]=r['run_id']
        return run

    def check_repair(self,name):
        c=self.book.cases[name];b=self.book.bundles[name];old=self.book.bundles['P10']
        self.create(name+'/create-base','P10')
        scope=['force-demo','demo']+(['rack'] if name=='P11' else [])
        aq,ar=self.at(name+'/authority');q,r=self.at(name+'/repair')
        require(aq['program_revision']==old.program_revision and aq['selector']=={'element_id':scope},'Repair lacks its exact pre-edit authority query')
        require(ar['status']=='succeeded' and len(ar['result']['items'])==1,'Missing writable source authority')
        authority=ar['result']['items'][0];source=authority['source']
        require(authority['element_id']==scope and source['program_revision']==old.program_revision,'Wrong writable element or revision')
        require(q['expected_program_revision']==old.program_revision and q['operation']=='edit','Repair did not use expected source revision')
        require(len(q['patches'])==1 and not q.get('module_changes'),'Repair changed other source units')
        p=q['patches'][0];frozen=c['repair']
        for key in ('source_id','start_byte','end_byte','expected_text','replacement'):require(p[key]==frozen[key],'Repair differs from predetermined source patch')
        require(p['source_revision']==old.entry.revision and p['element_id']==scope,'Wrong patch authority')
        require(old.entry.raw[p['start_byte']:p['end_byte']].decode()==p['expected_text'],'Patch byte precondition differs')
        require(old.entry.raw[:p['start_byte']]+p['replacement'].encode()+old.entry.raw[p['end_byte']:]==b.entry.raw,'Repair does not produce exact target source')
        require(old.modules==b.modules,'Repair changed the pinned libraries')
        # Establish the original declaration/scene interval independently from
        # the unchanged source, rather than trusting widened returned spans.
        text=old.entry.text
        start=text.index('object rack') if name=='P11' else text.index('scene Demo')
        opening=text.index('{',start);depth=1;end=opening+1
        while depth:
            require(end<len(text),'Unclosed trusted source declaration')
            depth+=(text[end]=='{')-(text[end]=='}');end+=1
        expected_span=(len(text[:start].encode()),len(text[:end].encode()))
        require(len(source['writable_spans'])==1,'Unexpected writable source scope count')
        s=source['writable_spans'][0]
        require((s['start_byte'],s['end_byte'])==expected_span and s['source_revision']==old.entry.revision and s['source_id']=='entry','Reported writable span differs from source declaration')
        require(s['start_byte']<=p['start_byte']<=p['end_byte']<=s['end_byte'],'Patch is outside source authority')
        require(r['status']=='succeeded' and r['accepted_program_revision']==b.program_revision,'Repair was not committed')
        self.snapshot_state(name,r['result']['initial_state'],Q(0),'before')
        for role,head in [('reject-scope',old.program_revision),('stale',b.program_revision)]:
            fq,fr=self.at(name+'/'+role)
            self.failure(fr,'OKL-E-REVISION');require(fr['accepted_program_revision']==head,'Rejected edit changed the accepted head')
            require(fq['expected_program_revision']==old.program_revision,'Rejected repair request was substituted')
            if role=='stale':require(fq['patches']==q['patches'],'Stale check did not retry the prior source edit')
            else:require(fq['patches']==[{**p,'element_id':['force-demo','demo','rack','props','first']}],'Unauthorized scope probe differs')

    @staticmethod
    def failure(r,code):
        codes=[d['code'] for d in r['diagnostics']]
        if r['protocol_error']:codes.append(r['protocol_error']['code'])
        require(r['status'] in ('rejected','failed') and code in codes,'Expected failure receipt is absent')
        require(r['achieved_level']!='delivered','A failure claimed delivered success')

    def check_delivery_failure(self):
        q,r=self.at('failure/delivery')
        self.failure(r,'OKL-E-CAPABILITY-UNSUPPORTED')
        if self.workflow_version == 'ontokin.force-agent-workflow/0.2':
            b=self.book.bundles['P01']
            require(q==dict(schema_version=PROTOCOL,project_id='case-P01',request_id=q['request_id'],
                            operation='validate',program_revision=b.program_revision,requested_level='delivered'),
                    'Generic delivery must request the fixed source without a destination')
            require(r['status']=='rejected' and r['protocol_error'] is None and r['run_id'] is None and
                    r['program_revision']==r['accepted_program_revision']==b.program_revision and
                    r['requested_level']=='delivered' and r['achieved_level']=='represented',
                    'Generic delivery did not retain its source-bound unsupported receipt')
            result=r['result']
            require(isinstance(result,dict) and set(result)=={'schema_version','program_revision','requested_level',
                    'achieved_level','outcome','diagnostics','source_manifest','stages'},
                    'Generic delivery returned an unexpected result or artifact claim')
            require(result['schema_version']=='ontokin.program-runtime/0.1' and
                    result['outcome']=='unsupported' and result['requested_level']=='delivered' and
                    result['achieved_level']=='represented' and result['program_revision']==b.program_revision and
                    result['source_manifest']==b.manifest() and result['diagnostics']==r['diagnostics'] and
                    result['stages']==dict(represented='valid',constructed='not_requested',evaluated='not_requested',
                                          construction_support='available',delivered='requires_named_external_contract'),
                    'Generic delivery changed its validation result or claimed a later stage')
        else:
            # Historical workflow/0.1 recorded the then-unavailable explicit
            # GLB/0.5 adapter. Do not reinterpret those archived messages.
            require(q['operation']=='export' and q['destination']=='ontokin.glb/0.5',
                    'Wrong historical unsupported destination')
        require(r['diagnostics'][0]['blocks']==['delivered'] and
                (r['result'] is None or 'artifact_id' not in r['result']),
                'Wrong unsupported destination or unexpected artifact claim')

    def audit(self):
        m=self.read('workflow.json')
        require(m['schema_version'] in ('ontokin.force-agent-workflow/0.1', 'ontokin.force-agent-workflow/0.2')
                and m['status']=='recorded','Incomplete workflow')
        self.workflow_version = m['schema_version']
        require(m['implementation']==self.implementation and m['protocol']==PROTOCOL,'Stale implementation or binding')
        require(m['writer_sha256']==sha((ROOT/'tools/build_force_agent_demo.py').read_bytes()),'Stale workflow writer')
        require(m['fixture_inputs']=={k:sha((DATA/k).read_bytes()) for k in ('acceptance.json','reviewed-acceptance.json','source-errata.json','ADOPTION.md')},'Wrong adopted acceptance inputs')
        require(m['source_fixtures']==self.book.positive,'Incomplete source fixture selection')
        for sequence,record in enumerate(m['exchanges'],1):
            role=record['role'];require(role not in self.roles and record['sequence']==sequence,'Duplicate role or noncontiguous trace')
            for k in ('request_file','response_file'):
                require(record[k] not in self.files,'Reused evidence file path');self.files.add(record[k])
            q=self.read(record['request_file'],record['request_sha256']);r=self.read(record['response_file'],record['response_sha256'])
            self.schemas.validate('request',q);self.schemas.validate('response',r)
            self.register_candidate(q);self.recursive(r)
            require(all(q[k]==r[k] for k in ('schema_version','project_id','request_id','operation')),'Response does not belong to its request')
            require(record['method']==('submit' if role=='cancel/submit' else 'handle'),'Wrong actual transport method')
            self.roles[role]=(q,r)
            key=(q['project_id'],q['request_id'])
            previous=self.request_ledger.get(key)
            if previous is None:
                self.request_ledger[key]=(q,r)
            elif previous[0]!=q:
                require(r['status']=='rejected' and r['protocol_error'] is not None and
                        r['protocol_error']['code']=='OKL-E-REQUEST-ID',
                        'Reused request ID lacks changed-payload rejection')
            elif previous[1]['status']=='queued':
                require(r['status']=='cancelled','Queued request ID has an unexpected terminal receipt')
                self.request_ledger[key]=(q,r)
            else:
                require(previous[1]==r,'Identical request ID retry changed its terminal receipt')
            project=q['project_id'];old=self.heads.get(project)
            if q['operation'] in ('create','edit') and r['status']=='succeeded':
                if q['operation']=='create':
                    require(old is None,'Successful create overwrote an existing accepted head')
                    expected=load_bundle(q['bundle']).program_revision
                else:
                    require(q['expected_program_revision']==old,'Successful edit had a stale head')
                    expected=self.book.bundles[role.split('/')[0]].program_revision
                require(r['program_revision']==expected,'Accepted candidate identity differs')
                self.heads[project]=expected;self.accepted.add((project,expected))
            require(r['accepted_program_revision']==self.heads.get(project),'Failed/read request changed the accepted revision')
        required=set()
        for name in self.book.positive:
            c=self.book.cases[name];b=self.book.bundles[name]
            if 'repair' in c:
                self.check_repair(name);required.update(name+'/'+r for r in ('create-base','authority','reject-scope','repair','stale'))
            else:
                self.create(name+'/create',name);required.add(name+'/create')
            run=self.check_run(name);required.add(name+'/run')
            for index,row in enumerate(c['expected_samples']):
                role=f'{name}/sample/{index:04d}';required.add(role);q,r=self.at(role)
                require(q['operation']=='inspect' and q['program_revision']==b.program_revision and q['run_id']==self.runs[name],'Inspection source/run mismatch')
                require(q.get('frame','world')=='world','Inspection frame request was substituted')
                require(q['selector']=={'path':row['target']} and q['fields']==['identity','state'] and q['limit']==1,'Inspection query was substituted')
                require(Q(q['time']['seconds'])==authored_clock(row['time']) and q['time']['side']==row['side'],'Inspection time/side was substituted')
                require(r['status']=='succeeded' and not r['truncated'] and r['next_cursor'] is None,'Incomplete state inspection')
                result=r['result'];require(result['total']==1 and len(result['items'])==1,'State inspection omitted or added an object')
                item=result['items'][0];obj=item['state'];context=result['context']
                require(item['path']==row['target'] and obj['available'] and obj['element_id']==item['element_id'],'Incorrect inspected occurrence')
                require(obj['program_revision']==r['program_revision']==b.program_revision and obj['run_id']==r['run_id']==self.runs[name],'Inspected state lost revision or run identity')
                require(clock(obj['time_seconds'])==authored_clock(row['time']) and obj['side']==row['side'],'Returned sample clock/side differs')
                require(context==dict(fields=['identity','state'],frame='world',program_revision=b.program_revision,
                                      run_id=self.runs[name],selector=q['selector'],side=row['side'],time_seconds=q['time']['seconds']),'Inspection context differs')
                require(obj['pose_frame']=='world' and obj['velocity_expressed_in']==obj['velocity_measured_in']=='world','Incorrect ordinary world-frame conversion')
                self.sample(name,obj,row)
            sample=run['last_valid_state'];require(set(sample['objects'])==self.book.objects(name),'Run omitted a source object')
            require(clock(sample['time_seconds'])==authored_clock(c['request_horizon']) and sample['side']=='after','Run last state clock differs')
            for target,obj in sample['objects'].items():
                self.book.check_projection(name,target,obj,clock(sample['time_seconds']),sample['side'])
            if name in ('P01','P10','P11','P12','P13'):
                required.add(name+'/mesh');q,r=self.at(name+'/mesh')
                require(q['operation']=='surface.mesh_page' and q['program_revision']==b.program_revision and q['count']==2,'Mesh query differs')
                require(r['status']=='succeeded' and r['result']['program_revision']==b.program_revision and r['result']['profile']=='surface-0.1','Mesh page lost its source or profile')
        extra=self.extra_checks();required.update(extra)
        require(set(self.roles)==required,'Unexpected or missing checkpoint roles')
        labels=set()
        for s in m['snapshots']:
            label=s['label'];require(label not in labels,'Repeated source snapshot');labels.add(label)
            name='P10' if label.endswith('-base') else label
            require(name in self.book.positive,'Unexpected snapshot source')
            b=self.book.bundles[name];payload=self.read(s['bundle_file'],s['bundle_sha256'])
            require(payload==b.to_payload() and load_bundle(payload).program_revision==s['program_revision']==b.program_revision,'Snapshot bytes or complete bundle identity differ')
            require((s['project_id'],b.program_revision) in self.accepted,'Snapshot was never accepted by the actual trace')
        require(labels==set(self.book.positive)|{'P11-base','P12-base','P13-base'},'Missing accepted source snapshot')
        require(m['exchange_count']==len(self.roles) and m['snapshot_count']==len(labels) and
                m['sample_count']==sum(len(self.book.cases[n]['expected_samples']) for n in self.book.positive),'Incorrect evidence counts')
        return dict(schema_version='ontokin.force-agent-audit/0.2',status='passed',
                    workflow_schema_version=self.workflow_version,
                    checked_at_utc=datetime.now(timezone.utc).isoformat(),implementation=self.implementation,
                    workflow_sha256=sha((self.root/'workflow.json').read_bytes()),verifier_sha256=sha(Path(__file__).read_bytes()),
                    schema_inputs=self.schemas.hashes,fixture_inputs=m['fixture_inputs'],
                    exchanges=len(self.roles),source_snapshots=len(labels),source_cases=len(self.book.positive),
                    predetermined_samples=m['sample_count'],force_projections_schema_checked=self.counter,
                    full_force_release_complete=False,destination_validated=False)

    def extra_checks(self):
        roles={'discovery','failure/invalid-create','failure/invalid-edit','retry/first','retry/same','retry/collision','retry/status',
               'failure/budget','cancel/submit','cancel/request','cancel/result','cancel/status','failure/delivery',
               'prefix/extend','prefix/inspect','prefix/reject-later','prefix/reset','failure/head','frame/self',
               'cursor/first','cursor/next','cursor/other-create','cursor/reject-project'}
        for role in roles:self.at(role)
        q,r=self.at('discovery');require(q['operation']=='discover' and q['profile']=='force-0.1' and r['status']=='succeeded','Missing force discovery')
        current = self.workflow_version == 'ontokin.force-agent-workflow/0.2'
        targets = ['ontokin.glb/0.5'] if current else []
        require(not r['truncated'] and r['result']['delivery_targets']==targets,'Discovery differs from its versioned delivery checkpoint')
        catalog={item['name']:item for item in r['result']['items']}
        availability = 'available_in_bounded_profile' if current else 'unsupported'
        require(catalog['force']['kind']=='event' and catalog['ontokin.glb/0.5']['availability']==availability,'Capability availability differs')
        for role,code in [('failure/invalid-create','OKL-E-TYPE'),('failure/invalid-edit','OKL-E-EVENT-ORDER'),
                          ('retry/collision','OKL-E-REQUEST-ID'),('failure/budget','OKL-E-RESOURCE'),
                          ('prefix/extend','OKL-E-NUMERIC'),
                          ('prefix/reject-later','OKL-E-SAMPLE'),('cursor/reject-project','OKL-E-REVISION')]:self.failure(self.at(role)[1],code)
        q,r=self.at('failure/invalid-create');require(q['bundle']==self.book.bundles['N01'].to_payload() and r['accepted_program_revision'] is None,'Wrong invalid candidate')
        q,r=self.at('failure/invalid-edit');p=q['patches'][0];b=self.book.bundles['P01']
        require(q['operation']=='edit' and q['expected_program_revision']==b.program_revision and p['replacement']=='-1[s]' and p['expected_text']=='1[s]' and b.entry.raw[p['start_byte']:p['end_byte']]==b'1[s]','Wrong invalid source edit')
        q1,r1=self.at('retry/first');q2,r2=self.at('retry/same');q3,_=self.at('retry/collision')
        require(q1==q2 and r1==r2,'Idempotent request did not retain its exact receipt')
        require(q3=={**q1,'fields':['identity','source']} and q3!=q1,'Changed-payload retry was not exercised')
        sq,sr=self.at('retry/status');require(sq['target_request_id']==q1['request_id'] and sr['result']['target']==r1,'Unknown-outcome status did not reconcile the original request')
        q,r=self.at('failure/budget');require(q['budgets']=={'max_value_entries':1} and r['accepted_program_revision'] is None and r['run_id'] is None,'Budget failure published state')
        cq,cr=self.at('cancel/submit');tq,tr=self.at('cancel/result');rq,rr=self.at('cancel/request');sq,sr=self.at('cancel/status')
        require(cq==tq and cr['status']=='queued' and tr['status']=='cancelled' and tr['accepted_program_revision'] is None and tr['run_id'] is None,'Queued cancellation published state or lost its request')
        require(rq['target_request_id']==sq['target_request_id']==cq['request_id'] and rr['result']['target']==sr['result']['target']==tr,'Cancellation target/status differs')
        self.check_delivery_failure()
        q,r=self.at('prefix/extend');run=r['result']['run_state']
        require(q['run_id']==r['run_id']==run['run_id']==self.runs['P21'] and q['until_seconds']=='3','Failed prefix extension lost the original run')
        require(run['status']=='failed' and run['valid_until_seconds']=='2' and run['valid_until_side']=='before','Invalid later state was certified')
        require(run['last_valid_state']['objects']['ball']['forces']['started_count']==1 and run['last_valid_state']['objects']['ball']['forces']['completed_count']==1,'Failed activation leaked into retained state')
        q,r=self.at('prefix/inspect');require(q['run_id']==self.runs['P21'] and q['time']=={'seconds':'0.5','side':'after'} and r['status']=='succeeded','Short certified prefix was lost')
        vector(r['result']['items'][0]['state']['position_m'],[0.25,0,0],'Retained prefix position',exact=True)
        vector(r['result']['items'][0]['state']['velocity_m_per_s'],[1,0,0],'Retained prefix velocity',exact=True)
        q,r=self.at('prefix/reject-later');require(q['run_id']==self.runs['P21'] and q['time']=={'seconds':'2','side':'after'},'Invalid later-state probe changed')
        q,r=self.at('prefix/reset');run=r['result']['run_state']
        require(q['operation']=='reset' and r['status']=='succeeded' and r['run_id']!=self.runs['P21'] and run['origin']=='reset' and
                run['valid_until_seconds']=='0' and run['valid_until_side']=='before','Reset did not create an independent before-zero run')
        require(r['run_id'] not in self.run_ids,'Run identity reused for reset')
        self.snapshot_state('P21',run['last_valid_state'],Q(0),'before')
        q,r=self.at('frame/self');local=r['result']['items'][0]['state']
        _,world_response=next(self.at(f'P07/sample/{i:04d}') for i,row in enumerate(self.book.cases['P07']['expected_samples'])
                              if authored_clock(row['time'])==Q(3,2) and row['side']=='after')
        world=world_response['result']['items'][0]['state']
        require(q['frame']=='ball.frame' and q['run_id']==self.runs['P07'] and r['status']=='succeeded','Wrong self-frame request')
        require(local['forces']==world['forces'] and local['impulses']==world['impulses'],'World influence records were rotated or substituted')
        vector(local['position_m'],[0,0,0],'Self position');orientation(local['orientation_wxyz'],[1,0,0,0])
        w,x,y,z=world['orientation_wxyz'];vx,vy,vz=world['velocity_m_per_s']
        # Independent inverse quaternion rotation. Velocity is measured in the
        # world and only expressed in self axes, not a frame-relative zero.
        x,y,z=-x,-y,-z;tx,ty,tz=2*(y*vz-z*vy),2*(z*vx-x*vz),2*(x*vy-y*vx)
        expected=[vx+w*tx+y*tz-z*ty,vy+w*ty+z*tx-x*tz,vz+w*tz+x*ty-y*tx]
        vector(local['velocity_m_per_s'],expected,'Self-expressed world velocity')
        require(local['velocity_measured_in']=='world' and local['velocity_expressed_in']==local['pose_frame']=='ball.frame','Incorrect self-frame velocity meaning')
        q,r=self.at('cursor/first');nq,nr=self.at('cursor/next');badq,_=self.at('cursor/reject-project')
        require(r['status']==nr['status']=='succeeded' and nq['cursor']==badq['cursor']==r['next_cursor'],'Cursor retry linkage differs')
        token=r['next_cursor'];data=decode(base64.urlsafe_b64decode(token+'='*(-len(token)%4))[32:]);ctx=data['context']
        require(data['offset']==nr['result']['offset']==1 and ctx['protocol']==PROTOCOL and ctx['entry_profile']=='force-0.1' and ctx['profile']=='surface-0.1','Wrong cursor offset/profile')
        require(ctx['implementation']==self.implementation and ctx['program_revision']==q['program_revision'] and ctx['project_id']==q['project_id']!=badq['project_id'],'Cursor immutable context differs')
        require(ctx['geometry_sha256']==r['result']['geometry_sha256']==nr['result']['geometry_sha256'],'Cursor changed geometry')
        require(r['result']['source_triangle_ordinals']==[0] and nr['result']['source_triangle_ordinals']==[1],'Cursor lost complete triangle ordering')
        self.create('cursor/other-create','P01')
        # All four generated sources use exactly the same visible surface.
        geometry_fields=('positions_m','normals','triangles','region_keys','source_triangle_ordinals')
        base=self.at('P10/mesh')[1]['result']
        for name in ('P11','P12','P13'):
            got=self.at(name+'/mesh')[1]['result']
            require(all(got[k]==base[k] for k in geometry_fields),'A physical source repair changed visible geometry')
        return roles


def verify(directory,schemas=None):
    try:
        return Reader(directory,schemas).audit()
    except EvidenceError:
        raise
    except Exception as exc:
        raise EvidenceError(f'Malformed or unsupported evidence: {type(exc).__name__}: {exc}') from exc


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workflow-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:report=verify(args.workflow_dir)
    except EvidenceError as exc:
        report=dict(schema_version='ontokin.force-agent-audit/0.2',status='failed',error=str(exc),full_force_release_complete=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2));return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
