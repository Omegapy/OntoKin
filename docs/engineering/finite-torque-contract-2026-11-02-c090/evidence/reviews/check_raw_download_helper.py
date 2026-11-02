#!/usr/bin/env python3
"""Focused local mocks for the coordinator helper; no real HTTP requests."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import urllib.error
from unittest.mock import patch

parser=argparse.ArgumentParser()
parser.add_argument('--helper',type=Path,required=True)
parser.add_argument('--report',type=Path,required=True)
a=parser.parse_args();assert not a.report.exists()
spec=importlib.util.spec_from_file_location('reviewed_raw_download',a.helper)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=[]
def check(name,actual,expected=True):
 r={'name':name,'passed':actual==expected}
 if actual!=expected:r.update(actual=str(actual),expected=str(expected))
 rows.append(r)
def refuses(name,fn):
 try:fn()
 except (ValueError,FileExistsError,KeyError):check(name,True)
 else:check(name,False)
ref='754f72106279abc6c867ab180300f2ba382a3f2d'
data=b'bounded independent fixture\n'
row={'path':'docs/file.txt','sha':m.native(data),'sha256':m.digest(data),'bytes':len(data),'mode':'100644','type':'blob'}
url='https://raw.githubusercontent.com/Omegapy/OntoKin/'+ref+'/docs/file.txt?token=SYNTHETIC_REVIEW_ONLY'
class Response:
 def __init__(self,body=data,status=200,headers=None,response_url=url):
  self.body=body;self.status=status;self.headers=headers or {};self.url=response_url;self.read_sizes=[]
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def geturl(self):return self.url
 def read(self,n):self.read_sizes.append(n);return self.body[:n]
class Opener:
 def __init__(self,response):self.response=response
 def open(self,*args,**kwargs):
  if isinstance(self.response,Exception):raise self.response
  return self.response
with tempfile.TemporaryDirectory(prefix='c090-raw-review-') as tmp:
 root=Path(tmp);priv=root/'private';pub=root/'public';priv.mkdir();pub.mkdir()
 plan={'ref':ref,'tree':'693ad3ad6cf176b6b645d2edda3468673d5cae52','files':[row],'directories':[{'id':0,'path':'docs'}]}
 entry={'path':row['path'],'sha':row['sha'],'size':row['bytes'],'type':'file','download_url':url}
 record={'request_url':'https://api.github.com/repos/Omegapy/OntoKin/contents/docs?ref='+ref,'requested_ref':ref,'directory':'docs','listing':[entry]}
 public=json.loads(json.dumps(record));public['request_url']=m.stripped(public['request_url']);public['listing'][0]['download_url']=m.stripped(url)
 args=SimpleNamespace(plan=root/'plan.json',private_directories=priv,public_directories=pub,output=root/'valid')
 def write_inputs():
  args.plan.write_text(json.dumps(plan));(priv/'0.json').write_text(json.dumps(record));(pub/'0.json').write_text(json.dumps(public))
 write_inputs();check('prepare/valid-returned-pinned-url',len(m.prepare(args)[1]),1)
 for label,bad in [('wrong-host',url.replace('raw.githubusercontent.com','example.invalid')),('wrong-ref',url.replace(ref,'0'*40)),('wrong-path',url.replace('docs/file.txt','docs/other.txt')),('fragment',url+'#fragment'),('userinfo',url.replace('https://','https://user@'))]:
  record['listing'][0]['download_url']=bad;write_inputs();refuses('prepare/'+label,lambda:m.prepare(args))
 record['listing'][0]['download_url']=url;write_inputs()
 record['request_url']=record['request_url'].replace(ref,'0'*40);write_inputs();refuses('prepare/wrong-listing-request',lambda:m.prepare(args));record['request_url']=record['request_url'].replace('0'*40,ref);write_inputs()
 public['listing'][0]['sha']='0'*40;write_inputs();refuses('prepare/public-private-mismatch',lambda:m.prepare(args));public['listing'][0]['sha']=row['sha'];write_inputs()
 item=m.prepare(args)[1][0]
 def run(name,response):
  args.output=root/name;args.output.mkdir()
  with patch.object(m.urllib.request,'build_opener',return_value=Opener(response)):
   result=m.download_one(args,ref,item)
  receipts=list(args.output.glob('*.json'))
  receipt=json.loads(receipts[0].read_text()) if receipts else {}
  check(name+'/no-query-leak',all('SYNTHETIC_REVIEW_ONLY' not in p.read_text() for p in receipts))
  return result,receipt
 response=Response(headers={'Content-Length':str(len(data))});result,receipt=run('valid',response)
 check('valid/status',result['status'],'passed');check('valid/bounded-read',response.read_sizes,[len(data)+1]);check('valid/actual-http',receipt['http_status'],200)
 with patch.object(m.urllib.request,'build_opener',side_effect=AssertionError('Existing verification must not use network')):
  check('existing/reverified',m.download_one(args,ref,item)['status'],'verified_existing')
 payload=args.output/(row['sha']+'.bin');payload.write_bytes(b'corrupt');refuses('existing/reject-corruption',lambda:m.download_one(args,ref,item));payload.write_bytes(data)
 # Main must invoke existing validation rather than silently skip receipts.
 payload.write_bytes(b'corrupt')
 with patch.object(m,'prepare',return_value=(plan,[item])),patch.object(m.sys,'argv',['download','--plan',str(args.plan),'--private-directories',str(priv),'--public-directories',str(pub),'--output',str(args.output)]):
  refuses('main/reject-existing-corruption',m.main)
 for name,response in [('hash-mismatch',Response(body=b'x'*len(data))),('short-body',Response(body=data[:-1])),('oversize-body',Response(body=data+b'x')),('wrong-length-header',Response(headers={'Content-Length':'1'})),('wrong-response-url',Response(response_url=url.replace('file.txt','other.txt')))]:
  result,receipt=run(name,response);check(name+'/failed',result['status'],'failed');check(name+'/no-passing-receipt',not (args.output/(row['sha']+'.json')).exists());check(name+'/actual-http-preserved',receipt.get('http_status'),200)
 error=urllib.error.HTTPError(url,403,'Forbidden',{},None);result,receipt=run('http403',error);check('http403/failed',result['status'],'failed');check('http403/actual-status-preserved',receipt.get('http_status'),403)
 refuses('redirect/refused',lambda:m.NoRedirect().redirect_request(None,None,302,'',{},'https://example.invalid/elsewhere'))
 target=root/'never-overwrite';target.write_bytes(b'first');refuses('write/no-overwrite',lambda:m.write_new(target,b'second'));check('write/original-bytes-kept',target.read_bytes(),b'first')
 report={'schema_version':'ontokin.raw-download-focused-review-check/1','outcome':'passed' if all(r['passed'] for r in rows) else 'failed','checks':len(rows),'helper_sha256':hashlib.sha256(a.helper.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'real_network_requests':0,'candidate_or_repository_modified':False,'failures':[r for r in rows if not r['passed']],'rows':rows}
 a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
 raise SystemExit(0 if report['outcome']=='passed' else 1)
