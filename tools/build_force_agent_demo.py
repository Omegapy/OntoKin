#!/usr/bin/env python3
"""Record real Agent/0.5 source authoring, inspection and failure receipts.

No parser, evaluator, force integrator, geometry builder or exporter is called
here. The selected service performs all work. Fixed source and sample requests
come from the adopted force corpus; a separate reader checks the results.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.bundle import load_file_manifest
from ontokin.program_agent import ProgramAgentService

PROTOCOL = 'ontokin.agent/0.5'
DATA = ROOT / 'docs/language-design/force-v0.1'
SCENE = ['force-demo', 'demo']
RACK = SCENE + ['rack']
FIRST = RACK + ['props', 'first']
BALL = SCENE + ['ball']


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False,
                               indent=2, allow_nan=False) + '\n', encoding='utf-8')


def seconds(value):
    """Exact finite decimal spelling of an authored rational clock."""
    n, d = int(value['numerator']), int(value['denominator'])
    a = b = 0
    while d % 2 == 0:
        d //= 2; a += 1
    while d % 5 == 0:
        d //= 5; b += 1
    if d != 1 or n < 0:
        raise ValueError('The corpus requires a nonnegative finite decimal clock')
    places = max(a, b)
    integer = n * 2**(places-a) * 5**(places-b)
    if not places:
        return str(integer)
    digits = str(integer).rjust(places+1, '0')
    return (digits[:-places] + '.' + digits[-places:]).rstrip('0').rstrip('.')


def require(ok, message):
    if not ok:
        raise ValueError(message)


class Recorder:
    def __init__(self, destination):
        self.root = Path(destination)
        require(not self.root.exists() or not any(self.root.iterdir()),
                'Use a new empty output directory; existing evidence is not overwritten')
        self.root.mkdir(parents=True, exist_ok=True)
        self.service = ProgramAgentService(self.root / 'service-store', protocol=PROTOCOL)
        self.cases = {c['id']: c for c in json.loads((DATA/'acceptance.json').read_text())['source_cases']}
        self.trace = []; self.snapshots = []; self.bundles = {}; self.runs = {}
        self.manifest = {'schema_version':'ontokin.force-agent-workflow/0.2',
                         'status':'running', 'started_at_utc':datetime.now(timezone.utc).isoformat(),
                         'protocol':PROTOCOL, 'implementation':self.service.implementation,
                         'writer_sha256':sha(Path(__file__).read_bytes()),
                         'fixture_inputs':{name:sha((DATA/name).read_bytes()) for name in
                                           ('acceptance.json','reviewed-acceptance.json','source-errata.json','ADOPTION.md')},
                         'exchanges':self.trace, 'snapshots':self.snapshots,
                         'limits':['This source/interface checkpoint does not independently validate GLB delivery or certify F01-F12.',
                                   'Retained samples cover the adopted corpus, not arbitrary body dynamics.',
                                   'Recorded messages require the independent source/schema audit.']}

    def bundle(self, name):
        b = load_file_manifest(DATA / self.cases[name]['file_manifest'])
        require(b.program_revision == self.cases[name]['program_revision'], 'Frozen bundle identity changed')
        return b

    def request(self, project, operation, **kw):
        return dict(schema_version=PROTOCOL, project_id=project,
                    request_id=f'force-workflow-{len(self.trace)+1:04d}', operation=operation, **kw)

    def exchange(self, role, request, *, method='handle', expected='succeeded', code=None):
        require(role not in {r['role'] for r in self.trace}, 'Duplicate trace role')
        number = len(self.trace) + 1
        stem = f'exchanges/{number:04d}'
        request_file, response_file = stem+'.request.json', stem+'.response.json'
        write_json(self.root/request_file, request)
        response = getattr(self.service, method)(request)
        write_json(self.root/response_file, response)
        self.trace.append(dict(role=role, method=method, sequence=number,
                               request_file=request_file, request_sha256=sha((self.root/request_file).read_bytes()),
                               response_file=response_file, response_sha256=sha((self.root/response_file).read_bytes())))
        require(response['status'] in ([expected] if isinstance(expected,str) else expected),
                f'{role}: unexpected {response["status"]}; {response.get("protocol_error")}; {response["diagnostics"]}')
        if code:
            codes = [d['code'] for d in response['diagnostics']]
            if response['protocol_error']:
                codes.append(response['protocol_error']['code'])
            require(code in codes, f'{role}: expected {code}, found {codes}')
        return response

    def send(self, role, project, operation, *, expected='succeeded', code=None, **kw):
        return self.exchange(role, self.request(project,operation,**kw), expected=expected, code=code)

    def snapshot(self, label, project, b):
        actual = self.service.read_program(project, b.program_revision)
        require(actual.to_payload() == b.to_payload(), 'The retained accepted source differs')
        relative = f'snapshots/{label}/program.bundle.json'
        write_json(self.root/relative, actual.to_payload())
        self.snapshots.append(dict(label=label, project_id=project, program_revision=b.program_revision,
                                   bundle_file=relative, bundle_sha256=sha((self.root/relative).read_bytes())))

    def create(self, role, project, b):
        return self.send(role,project,'create',bundle=b.to_payload(),
                         expected_program_revision=None,requested_level='constructed')

    def positive(self, name):
        c = self.cases[name]; project = 'case-'+name; b = self.bundle(name)
        if 'repair' in c:
            old = self.bundle(c['repair']['from_case'])
            self.create(name+'/create-base',project,old)
            self.snapshot(name+'-base',project,old)
            scope = RACK if name == 'P11' else SCENE
            self.send(name+'/authority',project,'inspect',program_revision=old.program_revision,
                      selector={'element_id':scope},fields=['identity','source'],limit=1)
            patch = {k:c['repair'][k] for k in ('source_id','start_byte','end_byte','expected_text','replacement')}
            patch.update(source_revision=old.entry.revision,element_id=scope)
            self.send(name+'/reject-scope',project,'edit',expected_program_revision=old.program_revision,
                      patches=[{**patch,'element_id':FIRST}],requested_level='constructed',
                      expected=('rejected','failed'),code='OKL-E-REVISION')
            self.send(name+'/repair',project,'edit',expected_program_revision=old.program_revision,
                      patches=[patch],requested_level='constructed')
            self.send(name+'/stale',project,'edit',expected_program_revision=old.program_revision,
                      patches=[patch],requested_level='constructed',expected=('rejected','failed'),code='OKL-E-REVISION')
        else:
            self.create(name+'/create',project,b)
        self.snapshot(name,project,b)
        run = self.send(name+'/run',project,'evaluate',program_revision=b.program_revision,
                        run_id=None,until_seconds=seconds(c['request_horizon']))
        self.bundles[name]=b; self.runs[name]=run['run_id']
        for index,row in enumerate(c['expected_samples']):
            self.send(f'{name}/sample/{index:04d}',project,'inspect',program_revision=b.program_revision,
                      run_id=run['run_id'],selector={'path':row['target']},fields=['identity','state'],limit=1,
                      time={'seconds':seconds(row['time']),'side':row['side']})
        if name in ('P01','P10','P11','P12','P13'):
            target = BALL if name == 'P01' else FIRST
            self.send(name+'/mesh',project,'surface.mesh_page',program_revision=b.program_revision,
                      element_id=target,count=2)

    def failures(self):
        b = self.bundles['P01']; project='case-P01'
        self.send('failure/invalid-create','invalid','create',bundle=self.bundle('N01').to_payload(),
                  expected_program_revision=None,requested_level='constructed',
                  expected=('failed','rejected'),code='OKL-E-TYPE')
        self.send('failure/invalid-edit',project,'edit',expected_program_revision=b.program_revision,
                  patches=[{'source_id':'entry','source_revision':b.entry.revision,'element_id':SCENE,
                            'start_byte':b.entry.raw.index(b'for 1[s]')+4,
                            'end_byte':b.entry.raw.index(b'for 1[s]')+8,
                            'expected_text':'1[s]','replacement':'-1[s]'}],
                  requested_level='constructed',expected=('failed','rejected'),code='OKL-E-EVENT-ORDER')
        req=self.request(project,'inspect',program_revision=b.program_revision,
                         selector={'path':'ball'},fields=['identity'],limit=1)
        first=self.exchange('retry/first',req)
        require(self.exchange('retry/same',req)==first,'An identical request retry changed its receipt')
        self.exchange('retry/collision',{**req,'fields':['identity','source']},
                      expected='rejected',code='OKL-E-REQUEST-ID')
        self.send('retry/status',project,'status',target_request_id=req['request_id'])
        self.send('failure/budget','limited','create',bundle=b.to_payload(),expected_program_revision=None,
                  requested_level='constructed',budgets={'max_value_entries':1},
                  expected=('failed','rejected'),code='OKL-E-RESOURCE')
        queued=self.request('queued','create',bundle=b.to_payload(),expected_program_revision=None,requested_level='constructed')
        self.exchange('cancel/submit',queued,method='submit',expected='queued')
        self.send('cancel/request','queued','cancel',target_request_id=queued['request_id'])
        self.service.work_next()
        self.exchange('cancel/result',queued,expected='cancelled')
        self.send('cancel/status','queued','status',target_request_id=queued['request_id'])
        # Generic delivery remains unsupported: an explicit destination is
        # required. Another binding's GLB version is an invalid request shape.
        self.send('failure/delivery',project,'validate',program_revision=b.program_revision,
                  requested_level='delivered',expected=('failed','rejected'),code='OKL-E-CAPABILITY-UNSUPPORTED')
        p=self.bundles['P21'];pr='case-P21'
        self.send('prefix/extend',pr,'evaluate',program_revision=p.program_revision,run_id=self.runs['P21'],
                  until_seconds='3',expected='failed',code='OKL-E-NUMERIC')
        self.send('prefix/inspect',pr,'inspect',program_revision=p.program_revision,run_id=self.runs['P21'],
                  selector={'path':'ball'},fields=['state'],limit=1,time={'seconds':'0.5','side':'after'})
        self.send('prefix/reject-later',pr,'inspect',program_revision=p.program_revision,run_id=self.runs['P21'],
                  selector={'path':'ball'},fields=['state'],limit=1,time={'seconds':'2','side':'after'},
                  expected=('failed','rejected'),code='OKL-E-SAMPLE')
        self.send('prefix/reset',pr,'reset',program_revision=p.program_revision)
        self.send('failure/head',project,'inspect',program_revision=b.program_revision,
                  selector={'path':'ball'},fields=['identity','source'],limit=1)
        p7=self.bundles['P07']
        self.send('frame/self','case-P07','inspect',program_revision=p7.program_revision,run_id=self.runs['P07'],
                  selector={'path':'ball'},fields=['state'],limit=1,time={'seconds':'1.5','side':'after'},frame='ball.frame')
        page=self.send('cursor/first',project,'surface.mesh_page',program_revision=b.program_revision,element_id=BALL,count=1)
        self.send('cursor/next',project,'surface.mesh_page',program_revision=b.program_revision,element_id=BALL,count=1,cursor=page['next_cursor'])
        self.create('cursor/other-create','cursor-other',b)
        self.send('cursor/reject-project','cursor-other','surface.mesh_page',program_revision=b.program_revision,
                  element_id=BALL,count=1,cursor=page['next_cursor'],expected=('failed','rejected'),code='OKL-E-REVISION')

    def build(self):
        try:
            self.send('discovery','discovery','discover',profile='force-0.1',limit=1000)
            for name,c in self.cases.items():
                if c['kind']=='positive':
                    self.positive(name)
            self.failures()
            self.manifest.update(status='recorded', source_fixtures=[k for k,c in self.cases.items() if c['kind']=='positive'],
                                 exchange_count=len(self.trace),snapshot_count=len(self.snapshots),
                                 sample_count=sum('/sample/' in r['role'] for r in self.trace))
        except Exception as exc:
            self.manifest.update(status='failed',failure={'type':type(exc).__name__,'message':str(exc)})
            raise
        finally:
            self.service.close()
            self.manifest['finished_at_utc']=datetime.now(timezone.utc).isoformat()
            write_json(self.root/'workflow.json',self.manifest)
        return {k:self.manifest[k] for k in ('status','exchange_count','snapshot_count','sample_count','implementation')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(Recorder(args.output_dir).build(),indent=2))


if __name__=='__main__':
    main()
