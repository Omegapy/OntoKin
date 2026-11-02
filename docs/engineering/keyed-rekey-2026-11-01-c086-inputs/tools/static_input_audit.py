#!/usr/bin/env python3
"""Independent token/source-identity audit of draft C086 inputs; no runtime imports."""
import argparse,base64,hashlib,json,re
from pathlib import Path
TOKEN=re.compile(r'\s+|//[^\n]*|"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|->|==|!=|<=|>=|[^\s]',re.S)
GENERICS={'rekey_keyed','zip_keyed','map_keyed','reduce_keyed','filter_keyed','merge_keyed','keyed','Keyed','Vec3','Vector3','Range'}
FIELDS={'source_id','source_revision','filename','start_byte','end_byte'}

def sha(x):return hashlib.sha256(x).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def lex(s):
    result=[]
    for m in TOKEN.finditer(s):
        if m[0].isspace() or m[0].startswith('//'):continue
        result.append((m[0],len(s[:m.start()].encode()),len(s[:m.end()].encode())))
    return result

def close(tokens,i,opening,closing):
    depth=0
    for j in range(i,len(tokens)):
        if tokens[j][0]==opening:depth+=1
        if tokens[j][0]==closing:
            depth-=1
            if depth==0:return j
    raise AssertionError('unclosed '+opening)

def boundary(tokens,i,end):
    nesting=[];angles=0
    for j in range(i,end):
        value=tokens[j][0]
        if value=='<' and (angles or (j>0 and tokens[j-1][0] in GENERICS)):angles+=1
        elif value=='>' and angles:angles-=1
        elif value in ['(','{','[']:nesting.append(value)
        elif value in [')','}',']']:nesting.pop()
        elif value==',' and not nesting and not angles:return j
    return end

def scan(s,source_id,filename):
    ts=lex(s);rev='sha256:'+sha(s.encode());out=[]
    def loc(a,b):return {'source_id':source_id,'source_revision':rev,'filename':filename,'start_byte':ts[a][1],'end_byte':ts[b][2]}
    for i,t in enumerate(ts):
        if t[0]!='rekey_keyed' or ts[i+1][0]!='<':continue
        typ_end=close(ts,i+1,'<','>'); op=typ_end+1
        if ts[op][0]!='(':continue
        stop=close(ts,op,'(',')'); comma=boundary(ts,op+1,stop)
        if comma==stop or ts[comma+1][0]!='(':continue
        bend=close(ts,comma+1,'(',')')
        if ts[bend+1][0]!='->' or bend+2>=stop:continue
        body=bend+2
        out.append({'expression':loc(i,stop),'input':loc(op+1,comma-1),'body':loc(body,stop-1),
                    'body_token':loc(body,body),'input_token':loc(op+1,op+1),
                    'binders':[ts[k][0] for k in range(comma+2,bend) if ts[k][0]!=','],
                    'type':''.join(t[0] for t in ts[i+2:typ_end]).replace('Quantity[m]','Length')})
    return out

def manifest(root,fm):
    data=json.loads((root/fm).read_text());entry=data['entry'];s=(root/entry['path']).read_text()
    units={'entry':(entry['filename'],s)}
    for m in data['modules']:units['package:'+m['package_id']+'@'+m['version']]=(m['filename'],(root/m['path']).read_text())
    cm={'schema_version':'ontokin.bundle/0.2','entry_source_id':'entry','units':[],'assets':[]}
    for ident,(fname,source) in sorted(units.items()):
        matches=[m for m in data['modules'] if ident=='package:'+m['package_id']+'@'+m['version']]
        m=matches[0] if matches else {'package_id':None,'version':None}
        cm['units'].append({'source_id':ident,'package_id':m['package_id'],'version':m['version'],'filename':fname,'source_revision':'sha256:'+sha(source.encode())})
    for a in data['assets']:
        b=(root/a['path']).read_bytes();assert a['sha256']=='sha256:'+sha(b)
        cm['assets'].append({k:a[k] for k in ['asset_id','media_type','sha256']}|{'byte_length':len(b)})
    cm['assets'].sort(key=lambda a:a['asset_id'])
    return cm,'sha256:'+sha(b'ontokin.bundle/0.2\0'+canon(cm)),units

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('receipt',type=Path);a=ap.parse_args()
    assert not a.receipt.exists(),'receipt exists';before={str(p.relative_to(a.root)):sha(p.read_bytes()) for p in a.root.rglob('*') if p.is_file()}
    exp=json.loads((a.root/'expected.json').read_text());results=[];counts={'cases':0,'control_identities':0,'operations':0,'locations':0,'new_diagnostics':0}
    for c in exp['cases']:
        cm,rev,units=manifest(a.root,c['file_manifest']);assert cm==c['canonical_manifest'] and rev==c['program_revision'],c['name']
        if 'explicit_c085_control' in c:
            co=c['explicit_c085_control'];m,r,_=manifest(a.root,co['file_manifest']);assert (m,r)==(co['canonical_manifest'],co['program_revision']),c['name']+' control'
            counts['control_identities']+=1
        def check_locations(x):
            if isinstance(x,dict):
                if set(x)==FIELDS:
                    fname,source=units[x['source_id']];b=source.encode();l,r=x['start_byte'],x['end_byte']
                    assert 0<=l<r<=len(b),(c['name'],x)
                    assert x['filename']==fname and x['source_revision']=='sha256:'+sha(b),(c['name'],x)
                    b[:l].decode();b[l:r].decode();counts['locations']+=1
                else:
                    for v in x.values():check_locations(v)
            elif isinstance(x,list):
                for v in x:check_locations(v)
        check_locations(c)
        if c['expected_code']!='OKL-E-SYNTAX':
            scanned=[]
            for sid,(fname,source) in units.items():scanned+=scan(source,sid,fname)
            expected=c['source_rekey_records'];assert len(scanned)==len(expected),(c['name'],len(scanned),len(expected))
            for observed,frozen,binder in zip(scanned,expected,c['source_rekey_binders']):
                for key in ['expression','input','body']:assert observed[key]==frozen[key],(c['name'],key,observed[key],frozen[key])
                assert observed['type']==frozen['element_type'],c['name']
                assert observed['binders']==binder['names'],(c['name'],'binders')
                counts['operations']+=1
            diag=c.get('expected_diagnostic')
            if diag:
                assert any(diag['primary'] in [v['body_token'],v['input_token']] for v in scanned),(c['name'],'primary token')
                for loc in diag['related']:
                    b=units[loc['source_id']][1].encode();fragment=b[loc['start_byte']:loc['end_byte']].decode()
                    assert re.match(r'^"(?:\\.|[^"\\])*"\s*:',fragment),(c['name'],'entry',fragment)
                    assert not fragment.endswith(','),(c['name'],'trailing comma')
                counts['new_diagnostics']+=1
        counts['cases']+=1;results.append({'name':c['name'],'status':'static_identities_and_spans_checked'})
    after={str(p.relative_to(a.root)):sha(p.read_bytes()) for p in a.root.rglob('*') if p.is_file()};assert before==after
    report={'status':'passed_static_inputs_only','root':str(a.root),'expected_sha256':before['expected.json'],'counts':counts,'source_control_inventory_unchanged':True,'runtime_executions':0,'uses_production_parser_or_runtime':False,'scanning_method':'Separate token stream with generic delimiters; compares full operands/body and first tokens including groups and UTF-8 byte offsets','results':results}
    a.receipt.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}))

if __name__=='__main__':main()
