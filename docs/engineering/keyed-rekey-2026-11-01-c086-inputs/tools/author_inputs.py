#!/usr/bin/env python3
"""Independently author C086 review inputs; imports no OntoKin runtime.

Literal constructor values are copied from preimplementation C085 source
fixtures, then used in new rekey sources and separately explicit .18 controls.
Expected key mappings, ordering, diagnostics and locations come from this
reviewed draft and authored source bytes, never candidate output.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil

BASELINE = 'f4c90c04b9b381de73d46715d52e68f588e49e4f'
ASSET_SHA = '5f87c7071d06327a077e05e1f57253370bc0b2eff1fa7f2025765825b7dcdd6e'
KEY = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')

def sha(x): return hashlib.sha256(x).hexdigest()
def digest(x): return 'sha256:'+sha(x)
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def dump(path,x): path.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def q(x): return json.dumps(x,ensure_ascii=True)
def literal(typ, pairs): return 'keyed<'+typ+'>{'+', '.join(q(k)+': '+v for k,v in pairs)+'}'
def rekey(typ,inp,body,binders='old_key, payload'): return f'rekey_keyed<{typ}>({inp}, ({binders}) -> {body})'

def matched(text,start,opener='(',closer=')'):
    assert text[start]==opener
    depth=0; quoted=False; esc=False
    for i in range(start,len(text)):
        ch=text[i]
        if quoted:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': quoted=False
            continue
        if ch=='"': quoted=True
        elif ch==opener: depth+=1
        elif ch==closer:
            depth-=1
            if depth==0:return i
    raise ValueError('unclosed '+opener)

def comma(text,start,end):
    stack=[]; quoted=False; esc=False; angles=0
    for i in range(start,end):
        ch=text[i]
        if quoted:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch=='"':quoted=False
        elif ch=='"':quoted=True
        elif ch=='<' and (angles or re.search(r'\b(?:rekey_keyed|zip_keyed|map_keyed|reduce_keyed|filter_keyed|merge_keyed|keyed|Keyed|Vec3|Vector3|Range)\s*$',text[:i])):angles+=1
        elif ch=='>' and angles:angles-=1
        elif ch in '({[':stack.append(ch)
        elif ch in ')}]':stack.pop()
        elif ch==',' and not stack and not angles:return i
    return end

def trimmed(text,a,b):
    while a<b and text[a].isspace():a+=1
    while b>a and text[b-1].isspace():b-=1
    return a,b

def location(src,a,b):
    return {'source_id':'entry','source_revision':digest(src.encode()),'filename':'main.ok',
            'start_byte':len(src[:a].encode()),'end_byte':len(src[:b].encode())}

def first_token(src,a,b):
    a,b=trimmed(src,a,b)
    match=re.match(r'(?:"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|.)',src[a:b],re.S)
    if not match:raise ValueError('missing token')
    return location(src,a,a+match.end())

def entry_spans(src,a,b):
    a,b=trimmed(src,a,b)
    while a<b and src[a]=='(' and matched(src,a)==b-1:
        a,b=trimmed(src,a+1,b-1)
    text=src[a:b]; start=text.find('{')
    if not text.lstrip().startswith('keyed<') or start<0:return {}
    end=matched(text,start,'{','}'); start+=1; result={}
    while start<end:
        stop=comma(text,start,end); aa,bb=trimmed(text,start,stop)
        if aa==bb:break
        m=re.match(r'"(?:\\.|[^"\\])*"',text[aa:bb]); assert m,(text[aa:bb],aa,bb)
        key=json.loads(m.group());result[key]=location(src,a+aa,a+bb)
        start=stop+1
    return result

def rekey_nodes(src):
    records=[]
    for match in re.finditer(r'\brekey_keyed<',src):
        start=match.start(); angle=src.index('<',start); type_end=matched(src,angle,'<','>')
        paren=type_end+1
        while src[paren].isspace():paren+=1
        if src[paren]!='(':continue
        end=matched(src,paren); split=comma(src,paren+1,end)
        if split==end:continue
        ia,ib=trimmed(src,paren+1,split)
        binder_start=split+1
        while src[binder_start].isspace():binder_start+=1
        if src[binder_start]!='(':continue
        binder_end=matched(src,binder_start)
        rest=binder_end+1
        while src[rest].isspace():rest+=1
        if src[rest:rest+2]!='->':continue
        ba,bb=trimmed(src,rest+2,end)
        records.append({'expression':location(src,start,end+1),'input':location(src,ia,ib),
          'body':location(src,ba,bb),'element_type':src[angle+1:type_end].strip().replace('Quantity[m]','Length'),
          'old_key':None,'new_key':None,'input_entry':None,
          '_input_token':first_token(src,ia,ib),'_body_token':first_token(src,ba,bb),
          '_input_entries':entry_spans(src,ia,ib),'_binders':[x.strip() for x in src[binder_start+1:binder_end].split(',')],
          '_input_text':src[ia:ib],'_body_text':src[ba:bb]})
    return records

def program(typ,expr,*,members='',defs='',version='0.19',prefix='',extras=''):
    profile='keyed-rekey-0.1' if version=='0.19' else 'keyed-zip-0.1'
    return (f'ontokin "{version}";\nmodule Probe @ "probe";\nprofile "{profile}";\n'+prefix+'\n'+defs+'\n'
      'public class ProbeShape @ "probe-shape" {\n'+('    '+members+'\n' if members else '')+
      f'    public derive result @ "result": {typ} = {expr};\n'+
      ('    public derive forced @ "forced": Int = len(self.result);\n' if typ.startswith('Keyed<') else
       '    public derive forced @ "forced": Int = len(keyed<Int>{"result": self.result});\n')+
      ('    '+extras+'\n' if extras else '')+
      '    geometry = if self.forced >= 0 then box(vec3(1[m], 1[m], 1[m])) else empty();\n'
      '    physical = no_body();\n}\nscene Demo @ "demo" {\n'
      '    duration = 1[s];\n    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);\n'
      '    object shape @ "shape": ProbeShape {}\n}\n')

def identity(src,assets,modules=()):
    manifest={'schema_version':'ontokin.bundle/0.2','entry_source_id':'entry',
      'units':[{'source_id':'entry','package_id':None,'version':None,'filename':'main.ok','source_revision':digest(src.encode())}],
      'assets':assets}
    for m in modules:
        manifest['units'].append({'source_id':'package:'+m['package_id']+'@'+m['version'],'package_id':m['package_id'],'version':m['version'],'filename':m['filename'],'source_revision':digest(m['source'].encode())})
    manifest['units'].sort(key=lambda u:u['source_id'])
    return digest(b'ontokin.bundle/0.2\0'+canonical(manifest)),manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--predecessor',type=Path,required=True);ap.add_argument('--destination',type=Path,required=True)
    args=ap.parse_args(); root=args.destination
    if root.exists():raise SystemExit('Destination must be new; retain previous attempts')
    for d in ['sources','controls','assets','modules']: (root/d).mkdir(parents=True)
    asset=(args.predecessor/'assets/label.png').read_bytes(); assert sha(asset)==ASSET_SHA
    (root/'assets/label.png').write_bytes(asset)
    cases=[]; copied_leaf_inputs=[]
    asset_meta={'asset_id':'label','media_type':'image/png','sha256':digest(asset),'byte_length':len(asset)}
    asset_file={'asset_id':'label','sha256':digest(asset),'media_type':'image/png','path':'assets/label.png'}

    def add(name,typ,expr,pairs=None,*,old_keys=None,mapping=None,tags=(),members='',defs='',extras='',control_members=None,control_defs=None,
            outcome='valid',code=None,diag=None,callbacks=None,version='0.19',prefix='',notes='',control_expr=None,raw=None,modules=(),control_modules=None,control_prefix=None,attach_assets=True):
        if any(c['name']==name for c in cases): raise ValueError('duplicate case '+name)
        src=raw if raw is not None else program(typ,expr,members=members,defs=defs,extras=extras,version=version,prefix=prefix)
        assets=[asset_meta] if attach_assets and ('png_asset(' in src or any('png_asset(' in m['source'] for m in modules)) else []
        for m in modules:
            mp=root/'modules'/m['filename']
            if mp.exists(): assert mp.read_text()==m['source']
            else: mp.write_text(m['source'])
        fm={'schema_version':'ontokin.files/0.2','entry':{'filename':'main.ok','path':'sources/'+name+'.ok'},'modules':[{k:m[k] for k in ['package_id','version','filename']}|{'path':'modules/'+m['filename']} for m in modules],
            'assets':[asset_file] if assets else []}
        (root/'sources'/f'{name}.ok').write_text(src);dump(root/f'{name}.files.json',fm)
        revision,manifest=identity(src,assets,modules)
        c={'id':f'RK{len(cases)+1:03d}','name':name,'source':'sources/'+name+'.ok','file_manifest':name+'.files.json',
           'program_revision':revision,'canonical_manifest':manifest,'expected_outcome':outcome,
           'expected_protocol_outcome': ('unsupported' if code=='OKL-E-CAPABILITY-UNSUPPORTED' else 'resource_limit' if code=='OKL-E-RESOURCE' else outcome),
           'expected_code':code,'expected_stage':'represented','tags':list(tags),'notes':notes,
           'host_policy':{'max_operations':100000,'max_elapsed_ms':30000}}
        nodes=[]
        try:nodes=rekey_nodes(src)
        except (ValueError,AssertionError,IndexError):
            if code!='OKL-E-SYNTAX':raise
        c['source_rekey_records']=[{k:v for k,v in n.items() if not k.startswith('_')} for n in nodes]
        c['source_rekey_binders']=[{'expression':n['expression'],'names':n['_binders'],'types':['String',n['element_type']]} for n in nodes]
        if old_keys is not None:c['expected']={'body_key_order':list(old_keys),'input_dynamic_evaluations':1}
        if mapping is not None:
            assert len(mapping)==len(set(mapping.values()))
            assert all(KEY.fullmatch(k) for k in mapping.values())
            c.setdefault('expected',{}).update({'old_to_new':mapping,'output_key_order':sorted(mapping.values()),'output_cardinality':len(mapping),
               'payloads_preserved_exactly':True,'body_evaluations':len(mapping),
               'checkpoint_counts':{'keyed_rekey_iteration':len(mapping),'keyed_rekey_key_validation':len(mapping),
                   'keyed_rekey_collision':len(mapping),'keyed_rekey_publication':1}})
            if len(nodes)==1:
                n=nodes[0];record={k:v for k,v in n.items() if not k.startswith('_')}
                c['expected']['root_aggregate_rekey_record']=record
                c['expected']['root_selected_rekey_records']={new:dict(record,old_key=old,new_key=new,input_entry=n['_input_entries'].get(old)) for old,new in mapping.items()}
                if not n['_input_entries'] and mapping:
                    c['expected']['input_origin_mapping_requires_external_case_expectation']=True
        if callbacks is not None:c.setdefault('expected',{})['body_key_order']=callbacks
        if pairs is not None:
            c.setdefault('expected',{})['entry_constructor_values']={k:{'type':typ[6:-1],'expression':v} for k,v in sorted(pairs)}
        if diag is not None:
            n=nodes[0]
            if diag['kind']=='type':
                side=diag['side'];want='String' if side=='body' else diag['expected'];actual=diag['actual']
                d={'code':'OKL-E-TYPE','category':'invalid','phase':'type','rule_ids':['LANG-003'],
                  'message':f'rekey_keyed {side} requires exactly {want}, received {actual}.',
                  'primary':n['_body_token'] if side=='body' else n['_input_token'],'related':[],
                  'details':{'expected':want,'actual':actual}}
            elif diag['kind']=='invalid_key':
                old=diag['old'];new=diag['new'];entry=n['_input_entries'].get(old)
                d={'code':'OKL-E-ID','category':'invalid','phase':'elaboration','rule_ids':['LANG-007'],
                  'message':f'rekey_keyed produced invalid stable key {q(new)} from old key {q(old)}.',
                  'primary':n['_body_token'],'related':[entry] if entry else [],
                  'details':{'operation':'rekey_keyed','key':new,'old_key':old}}
            else:
                first,duplicate,new=diag['first'],diag['duplicate'],diag['new']
                entries=n['_input_entries'];d={'code':'OKL-E-ID','category':'invalid','phase':'elaboration','rule_ids':['LANG-007'],
                  'message':f'rekey_keyed output key {q(new)} duplicates old keys {q(first)} and {q(duplicate)}.',
                  'primary':n['_body_token'],'related':[entries[k] for k in [first,duplicate] if k in entries],
                  'details':{'operation':'rekey_keyed','key':new,'first_old_key':first,'duplicate_old_key':duplicate}}
            c['expected_diagnostic']=d
        if outcome=='valid':
            if control_expr is None:
                assert pairs is not None and typ.startswith('Keyed<'),name
                control_expr=literal(typ[6:-1],pairs)
            cm=(members if 'rekey_keyed' not in members else '') if control_members is None else control_members
            cd=(defs if 'rekey_keyed' not in defs else '') if control_defs is None else control_defs
            cp=prefix if control_prefix is None else control_prefix
            cms=modules if control_modules is None else control_modules
            control=program(typ,control_expr,members=cm,defs=cd,version='0.18',prefix=cp)
            ca=[asset_meta] if 'png_asset(' in control or any('png_asset(' in m['source'] for m in cms) else []
            control_file={'schema_version':'ontokin.files/0.2','entry':{'filename':'main.ok','path':'controls/'+name+'.ok'},'modules':[{k:m[k] for k in ['package_id','version','filename']}|{'path':'modules/'+m['filename']} for m in cms],
              'assets':[asset_file] if ca else []}
            (root/'controls'/f'{name}.ok').write_text(control);dump(root/f'control-{name}.files.json',control_file)
            cr,cc=identity(control,ca,cms)
            c['explicit_c085_control']={'source':'controls/'+name+'.ok','file_manifest':'control-'+name+'.files.json','program_revision':cr,'canonical_manifest':cc}
        cases.append(c)
        return c

    def valid(name,t,pairs,body,mapping,**kw):
        return add(name,'Keyed<'+t+'>',rekey(t,literal(t,pairs),body),[(mapping[k],v) for k,v in pairs],old_keys=sorted(mapping),mapping=mapping,**kw)
    valid('empty','Int',[],'old_key',{},tags=['empty','unknown-payload-static'])
    valid('singleton','Int',[('a','7')],'"ns.a"',{'a':'ns.a'},tags=['singleton','changed-key'])
    valid('identity-renaming','Int',[('b','2'),('a','1')],'old_key',{'a':'a','b':'b'},tags=['identity','authored-order'])
    valid('reordered-output','Int',[('a','11'),('b','22')],'if old_key == "a" then "z" else "A"',{'a':'z','b':'A'},tags=['old-order','new-order'])
    valid('equal-payload-distinct-output','Int',[('a','7'),('b','7')],'if old_key == "a" then "ns.a" else "ns.b"',{'a':'ns.a','b':'ns.b'},tags=['equal-payload','alias-isolation'])
    boundary=['0','A','A.','a','a_','z-']
    valid('ascii-boundary-identity','Int',[(k,str(i)) for i,k in enumerate(reversed(boundary))],'old_key',{k:k for k in boundary},tags=['ascii-order','domain-boundary'])
    valid('maximum-key-output','Int',[('a','1')],q('Z'+'x'*63),{'a':'Z'+'x'*63},tags=['64-characters'])
    valid('maximum-key-input','Int',[('Z'+'x'*63,'1')],'"a"',{'Z'+'x'*63:'a'},tags=['64-characters'])
    valid('maximum-256','Int',[(f'k{i:03d}',str(i)) for i in reversed(range(256))],'old_key',{f'k{i:03d}':f'k{i:03d}' for i in range(256)},tags=['cardinality-256','budget'])
    valid('payload-selected-new-key','Int',[('a','11'),('b','22')],'if payload == 11 then "first" else "second"',{'a':'first','b':'second'},tags=['payload-read','key-choice'])
    valid('grouped-body','Int',[('a','1')],'("ns.a")',{'a':'ns.a'},tags=['grouped-span'])
    valid('utf8-prefix','Int',[('a','1')],'"ns.a"',{'a':'ns.a'},tags=['utf8-byte-span'],prefix='// café λ prefix keeps UTF-8 byte coordinates.\n')
    for path in sorted((args.predecessor/'sources').glob('leaf-*-all-boundaries.ok')):
        old=path.read_text();line=next(x.strip() for x in old.splitlines() if 'derive result' in x)
        typ=line.split(': Keyed<',1)[1].split('> = ',1)[0]
        exp=line.split(' = ',1)[1][:-1]
        start=exp.index('(')+1;end=comma(exp,start,len(exp)-1);inp=exp[start:end].strip()
        brace=inp.index('{');endbrace=matched(inp,brace,'{','}');entry=inp[brace+1:endbrace]
        leaf=entry.split(':',1)[1].strip();family=path.name.removeprefix('leaf-').removesuffix('-all-boundaries.ok')
        copied_leaf_inputs.append({'source':str(path.relative_to(args.predecessor)), 'sha256':sha(path.read_bytes()),'type':typ,'constructor_expression':leaf})
        for suffix,body,new in [('identity','old_key','a'),('renamed','"ns.a"','ns.a')]:
            valid('leaf-'+family+'-'+suffix,typ,[('a',leaf)],body,{'a':new},tags=['immutable-leaf',family,'exact-payload'])
        valid('leaf-'+family+'-empty',typ,[],'"unused"',{},tags=['immutable-leaf',family,'empty'])
    valid('equivalent-quantity-alias','Quantity[m]',[('a','0.25[m]')],'"ns.a"',{'a':'ns.a'},tags=['alias','exact-type'])
    params='public param items @ "items": Keyed<Int> = keyed<Int>{"b":22,"a":11}; public param names @ "names": Keyed<String> = keyed<String>{"a":"ns.a","b":"ns.b"};'
    add('explicit-namespace-map','Keyed<Int>',rekey('Int','self.items','self.names[old_key]'),[('ns.a','11'),('ns.b','22')],old_keys=['a','b'],mapping={'a':'ns.a','b':'ns.b'},members=params,tags=['explicit-namespace','input-once','dependency-reads'])
    add('input-alias-remains-unmodified','Keyed<Int>',rekey('Int','self.items','self.names[old_key]'),[('ns.a','11'),('ns.b','22')],old_keys=['a','b'],mapping={'a':'ns.a','b':'ns.b'},members=params,extras='public derive untouched @ "untouched": Keyed<Int> = self.items;',tags=['original-alias','detached-values'])
    add('ignored-payload-retains-input-read','Keyed<Int>',rekey('Int','self.items','self.names[old_key]'),[('ns.a','11'),('ns.b','22')],old_keys=['a','b'],mapping={'a':'ns.a','b':'ns.b'},members=params,tags=['ignored-binder','aggregate-dependency'])
    add('empty-retains-input-read','Keyed<Int>',rekey('Int','self.items','"unused"'),[],old_keys=[],mapping={},members='public param items @ "items": Keyed<Int> = keyed<Int>{};',tags=['empty','aggregate-dependency'])
    defs='public fn empty_name @ "empty-name"(zero: Real) -> Keyed<Int> { return '+rekey('Int','keyed<Int>{}','if 1.0 / zero > 0.0 then "a" else "b"')+'; }'
    add('empty-captured-zero-not-evaluated','Keyed<Int>','empty_name(0.0)',[],defs=defs,tags=['unknown-payload','captured-zero','empty'])
    inner=rekey('Int','keyed<Int>{"a":7}','"b"','ik, iv')
    add('nested-rekey','Keyed<Int>',rekey('Int',inner,'"c"'),[('c','7')],tags=['nested-rekey','lineage-two-steps'])
    add('map-prepares-input','Keyed<Int>',rekey('Int','map_keyed<Int>(keyed<Int>{"a":2}, (mk, mv) -> mv * 3)','"ns.a"'),[('ns.a','6')],tags=['map','prior-key-retained'])
    add('filter-prepares-input','Keyed<Int>',rekey('Int','filter_keyed<Int>(keyed<Int>{"a":1,"b":2}, (fk, fv) -> fv > 1)','"ns.b"'),[('ns.b','2')],tags=['filter','prior-key-retained'])
    add('merge-prepares-input','Keyed<Int>',rekey('Int','merge_keyed<Int>(keyed<Int>{"a":1}, keyed<Int>{"b":2})','if old_key == "a" then "ns.a" else "ns.b"'),[('ns.a','1'),('ns.b','2')],tags=['merge','prior-key-retained'])
    add('zip-prepares-input','Keyed<Int>',rekey('Int','zip_keyed<Int,Int,Int>(keyed<Int>{"a":2}, keyed<Int>{"a":3}, (zk, zl, zr) -> zl+zr)','"ns.a"'),[('ns.a','5')],tags=['zip','prior-key-retained'])
    add('rekey-then-map','Keyed<Int>','map_keyed<Int>('+rekey('Int','keyed<Int>{"a":2}','"ns.a"')+', (mk, mv) -> mv * 3)',[('ns.a','6')],tags=['downstream-map'])
    add('rekey-then-filter','Keyed<Int>','filter_keyed<Int>('+rekey('Int','keyed<Int>{"a":2}','"ns.a"')+', (fk, fv) -> fv > 1)',[('ns.a','2')],tags=['downstream-filter'])
    add('rekey-then-reduce','Int','reduce_keyed<Int>('+rekey('Int','keyed<Int>{"a":2}','"ns.a"')+', 0, (acc, rk, rv) -> acc+rv)',tags=['downstream-reduce'],control_expr='2')
    add('rekey-then-merge','Keyed<Int>','merge_keyed<Int>('+rekey('Int','keyed<Int>{"a":2}','"ns.a"')+', keyed<Int>{"other":3})',[('ns.a','2'),('other','3')],tags=['downstream-merge'])
    add('rekey-then-zip','Keyed<Int>','zip_keyed<Int,Int,Int>('+rekey('Int','keyed<Int>{"a":2}','"ns.a"')+', keyed<Int>{"ns.a":3}, (zk, zl, zr) -> zl+zr)',[('ns.a','5')],tags=['downstream-zip'])
    add('condition-only-rekey','Keyed<Int>','if len('+rekey('Int','keyed<Int>{"a":2}','"ns.a"')+') == 1 then keyed<Int>{"plain":7} else keyed<Int>{}',[('plain','7')],tags=['condition-only','aggregate-not-contributor'])
    add('indexed-rekey','Int',rekey('Int','keyed<Int>{"a":7}','"ns.a"')+'["ns.a"]',tags=['indexed','selected-lineage'],control_expr='7')
    defs='public fn renamed @ "renamed"(aa:Keyed<Int>) -> Keyed<Int> {return '+rekey('Int','aa','"ns.a"','hk,hv')+';}'
    members='public param items @ "items": Keyed<Int> = keyed<Int>{"a":7}; public derive earlier @ "earlier": Keyed<Int> = renamed(self.items);'
    add('guarded-helper-replay','Keyed<Int>','if len(self.earlier)==1 then renamed(self.items) else keyed<Int>{}',[('ns.a','7')],defs=defs,members=members,control_members='',tags=['helper-cache','replay','dependencies'])
    defs='public fn legacy @ "legacy"(aa:Int) -> String {return if aa > 0 then "positive" else "negative";}'
    valid('pure-helper-body','Int',[('a','7')],'legacy(payload)',{'a':'positive'},defs=defs,tags=['pure-helper'])

    def invalid(name,t,inp,body,code='OKL-E-ID',**kw):return add(name,'Keyed<'+t+'>',rekey(t,inp,body),outcome='invalid',code=code,**kw)
    for name,new in [('empty',''),('space','a b'),('slash','a/b'),('unicode','café'),('leading-dot','.a'),('leading-underscore','_a'),('leading-hyphen','-a'),('length-65','A'+'x'*64),('control-character','a\nb')]:
        invalid('output-key-'+name,'Int','keyed<Int>{"a":7}',q(new),diag={'kind':'invalid_key','old':'a','new':new},callbacks=['a'],tags=['output-key-domain'])
    invalid('duplicate-equal-payload','Int','keyed<Int>{"b":7,"a":7}','"same"',diag={'kind':'duplicate','first':'a','duplicate':'b','new':'same'},callbacks=['a','b'],tags=['collision','equal-payload','authored-order'])
    invalid('duplicate-before-later-body-error','Real','keyed<Real>{"a":1.0,"b":2.0,"c":0.0}','if old_key == "c" then (if 1.0 / payload > 0.0 then "x" else "y") else "same"',diag={'kind':'duplicate','first':'a','duplicate':'b','new':'same'},callbacks=['a','b'],tags=['multiple-error','collision-before-later-callback'])
    invalid('duplicate-before-later-invalid-key','Int','keyed<Int>{"a":1,"b":2,"c":3}','if old_key == "c" then "bad key" else "same"',diag={'kind':'duplicate','first':'a','duplicate':'b','new':'same'},callbacks=['a','b'],tags=['multiple-error','collision-before-later-invalid-key'])
    invalid('first-collision-not-smallest-new-key','Int','keyed<Int>{"a":1,"b":2,"c":3,"d":4}','if payload <= 2 then "z" else "A"',diag={'kind':'duplicate','first':'a','duplicate':'b','new':'z'},callbacks=['a','b'],tags=['collision-choice','multiple-collisions'])
    invalid('invalid-key-before-later-collision','Int','keyed<Int>{"a":1,"b":2,"c":3}','if old_key == "a" then "bad key" else "same"',diag={'kind':'invalid_key','old':'a','new':'bad key'},callbacks=['a'],tags=['multiple-error','invalid-before-later-collision'])
    invalid('body-error-before-later-collision','Real','keyed<Real>{"c":1.0,"b":1.0,"a":0.0}','if 1.0 / payload > 0.0 then "same" else "same"',code='OKL-E-NUMERIC',callbacks=['a'],tags=['multiple-error','callback-before-collision'])
    invalid('static-body-before-dynamic-input','Real','keyed<Real>{"a":1.0/0.0}','7',code='OKL-E-TYPE',diag={'kind':'type','side':'body','actual':'Int'},callbacks=[],tags=['static-before-dynamic'])
    invalid('input-admission-before-callback','Real','keyed<Real>{"a":1.0/0.0}','if 1.0 / payload > 0.0 then "a" else "b"',code='OKL-E-NUMERIC',callbacks=[],tags=['input-before-body'])
    invalid('empty-body-not-String','Int','keyed<Int>{}','7',code='OKL-E-TYPE',diag={'kind':'type','side':'body','actual':'Int'},callbacks=[],tags=['empty','exact-type'])
    invalid('body-bool-not-String','Int','keyed<Int>{"a":1}','true',code='OKL-E-TYPE',diag={'kind':'type','side':'body','actual':'Bool'},callbacks=[],tags=['exact-type'])
    invalid('input-no-int-real-widening','Real','keyed<Int>{"a":1}','old_key',code='OKL-E-TYPE',diag={'kind':'type','side':'input','expected':'Keyed<Real>','actual':'Keyed<Int>'},callbacks=[],tags=['exact-type','no-widening'])
    invalid('input-not-keyed','Int','7','old_key',code='OKL-E-TYPE',diag={'kind':'type','side':'input','expected':'Keyed<Int>','actual':'Int'},callbacks=[],tags=['exact-type'])
    invalid('empty-unknown-name','Int','keyed<Int>{}','absent',code='OKL-E-NAME',callbacks=[],tags=['empty','name'])
    invalid('unselected-body-unknown-name','Int','keyed<Int>{}','if true then "a" else absent',code='OKL-E-NAME',callbacks=[],tags=['empty','static-unselected'])
    invalid('String-concatenation-still-unsupported','Int','keyed<Int>{"a":1}','"ns." + old_key',code='OKL-E-TYPE',callbacks=[],tags=['inherited-operator-limit'])
    invalid('input-257','Int',literal('Int',[(f'k{i:03d}',str(i)) for i in range(257)]),'old_key',code='OKL-E-RESOURCE',callbacks=[],tags=['cardinality-257'])
    for name,inp in [('empty-key','keyed<Int>{"":1}'),('duplicate-key','keyed<Int>{"a":1,"a":2}'),('invalid-key','keyed<Int>{"a b":1}')]:
        invalid('input-'+name,'Int',inp,'old_key',callbacks=[],tags=['inherited-input-key'])
    for t in ['Keyed<Int>','Geometry','BodyModel','Action']:
        invalid('unsupported-'+t.replace('<','-').replace('>',''),'Int' if t=='Action' else t,'keyed<'+t+'>{}','"a"',code='OKL-E-CAPABILITY-UNSUPPORTED',callbacks=[],tags=['unsupported-leaf'])
    base=rekey('Int','keyed<Int>{"a":1}','old_key')
    for name,expr in [('missing-types',base.replace('<Int>','',1)),('extra-type',base.replace('rekey_keyed<Int>','rekey_keyed<Int,Int>')),('one-binder',base.replace('old_key, payload','old_key')),('three-binders',base.replace('old_key, payload','old_key, payload, extra')),('missing-arrow',base.replace(' -> ', ' ')),('missing-body',base.replace(' -> old_key',' -> '))]:
        add('syntax-'+name,'Keyed<Int>',expr,outcome='invalid',code='OKL-E-SYNTAX',tags=['syntax'])
    for name,binders in [('duplicate-binders','old_key, old_key'),('predefined-binder','old_key, world'),('reserved-operation-binder','old_key, rekey_keyed')]:
        add(name,'Keyed<Int>',rekey('Int','keyed<Int>{}','"a"',binders),outcome='invalid',code='OKL-E-NAME',tags=['binder-scope'])
    invalid('binder-shadows-parameter','Int','keyed<Int>{}','"a"',code='OKL-E-NAME',members='public param payload @ "payload": Int = 7;',tags=['binder-scope'])
    add('binder-not-visible-in-input','Keyed<Int>',rekey('Int','payload','"a"'),outcome='invalid',code='OKL-E-NAME',tags=['binder-scope'])
    defs='public fn loop @ "loop"(x:Int) -> String {return loop(x);}'
    invalid('unused-pure-cycle','Int','keyed<Int>{}','"a"',code='OKL-E-DEPENDENCY-CYCLE',defs=defs,tags=['cycle','empty'])
    add('older-unit-rejects-new-syntax','Keyed<Int>',base,outcome='invalid',code='OKL-E-SYNTAX',version='0.18',tags=['older-version'])
    defs='public fn rekey_keyed @ "legacy-rekey"(x:Int) -> Int {return x+1;}'
    add('older-ordinary-name-preserved','Int','rekey_keyed(6)',defs=defs,version='0.18',control_expr='7',tags=['older-version','ordinary-name'])
    defs='public fn rekey_keyed @ "bad-name"(x:Int) -> Int {return x+1;}'
    add('new-profile-reserves-name','Keyed<Int>',rekey('Int','keyed<Int>{}','"a"'),defs=defs,outcome='invalid',code='OKL-E-NAME',tags=['reserved-name'])
    c=invalid('grouped-duplicate-utf8','Int','(keyed<Int>{"b":2,"a":1})','("same")',diag={'kind':'duplicate','first':'a','duplicate':'b','new':'same'},callbacks=['a','b'],prefix='// café λ\n',tags=['grouped-span','utf8-byte-span','collision'])
    # Exact inner entries remain the origins of grouped literals; derive those
    # original byte spans directly from authored bytes, without runtime data.
    raw=(root/c['source']).read_text(); ia=raw.index('keyed<Int>{'); ib=matched(raw,raw.index('{',ia),'{','}')+1
    entries=entry_spans(raw,ia,ib); c['expected_diagnostic']['related']=[entries['a'],entries['b']]
    # Compatibility and authority-sensitive inputs, authored without candidate output.
    legacy_source='ontokin "0.18";\nmodule Legacy @ "legacy";\nprofile "keyed-zip-0.1";\npublic fn rekey_keyed @ "legacy-rekey"(x:Int)->Int{return x+1;}\nprivate fn hidden @ "hidden"()->String{return "hidden";}\n'
    legacy={'package_id':'fixture.rekey-legacy','version':'1.0.0','filename':'legacy.ok','source':legacy_source}
    legacy_import='import lib @ "lib-import" from "fixture.rekey-legacy" version "1.0.0" digest "'+digest(legacy_source.encode())+'";\n'
    add('qualified-older-name-preserved','Keyed<Int>','keyed<Int>{"a":lib.rekey_keyed(6)}',[('a','7')],prefix=legacy_import,modules=[legacy],tags=['older-version','qualified-name'])
    invalid('private-helper-in-empty-body','Int','keyed<Int>{}','lib.hidden()',code='OKL-E-ACCESS',prefix=legacy_import,modules=[legacy],tags=['access','empty'])
    helper_source='ontokin "0.19";\nmodule Rename @ "rename";\nprofile "keyed-rekey-0.1";\npublic fn names @ "names"(aa:Keyed<Int>)->Keyed<Int>{return rekey_keyed<Int>(aa,(old_key,payload)->"ns.a");}\n'
    helper={'package_id':'fixture.rekey-helper','version':'1.0.0','filename':'helper.ok','source':helper_source}
    helper_import='import lib @ "lib-import" from "fixture.rekey-helper" version "1.0.0" digest "'+digest(helper_source.encode())+'";\n'
    add('imported-new-rekey-helper','Keyed<Int>','lib.names(keyed<Int>{"a":7})',[('ns.a','7')],prefix=helper_import,modules=[helper],control_prefix='',control_modules=[],tags=['new-module','pin','imported-origin'])
    add('older-importer-rejects-new-unit','Keyed<Int>','lib.names(keyed<Int>{"a":7})',prefix=helper_import,modules=[helper],version='0.18',outcome='invalid',code='OKL-E-CAPABILITY-UNSUPPORTED',tags=['declaring-version'])
    add('wrong-import-pin','Keyed<Int>','lib.names(keyed<Int>{"a":7})',prefix=helper_import.replace(digest(helper_source.encode()),'sha256:'+'0'*64),modules=[helper],outcome='invalid',code='OKL-E-REVISION',tags=['pin'])
    invalid('input-quantity-dimension-mismatch','Length','keyed<Time>{"a":1[s]}','old_key',code='OKL-E-TYPE',diag={'kind':'type','side':'input','expected':'Keyed<Length>','actual':'Keyed<Time>'},callbacks=[],tags=['exact-type','unit'])
    invalid('callback-frame-mismatch','Point3','keyed<Point3>{"a":point(world,0[m],0[m],0[m])}','if payload == point(self.frame,0[m],0[m],0[m]) then "a" else "b"',code='OKL-E-FRAME',tags=['frame'])
    image_def='public fn picture @ "picture"()->TextureImage{return png_asset("label","sha256:'+ASSET_SHA+'");}'
    add('empty-retains-unused-image-declaration','Keyed<Int>',rekey('Int','keyed<Int>{}','old_key'),[],old_keys=[],mapping={},defs=image_def,tags=['image-closure','empty','unused-definition'])
    add('empty-missing-image-declaration','Keyed<Int>',rekey('Int','keyed<Int>{}','old_key'),defs=image_def,attach_assets=False,outcome='invalid',code='OKL-E-ASSET-CLOSURE',tags=['image-closure','empty','missing-asset'])
    add('discarded-payload-keeps-image-declaration','Int','len('+rekey('TextureImage','keyed<TextureImage>{"a":picture()}','"ns.a"')+')',defs=image_def,control_expr='1',tags=['image-closure','discarded-payload'])
    invalid('dynamic-image-id','TextureImage','keyed<TextureImage>{"a":png_asset(self.image_name,"sha256:'+ASSET_SHA+'")}', 'old_key',code='OKL-E-ASSET-CLOSURE',members='public param image_name @ "image-name": String = "label";',tags=['image-closure','dynamic-id'])
    for name,expression in [
      ('empty-input-generated-taint',rekey('Length','filter_keyed<Length>(self.sizes,(fk,fv)->if self.leaves["a"].size>0[m] then false else false)','old_key')),
      ('body-generated-taint',rekey('Length','self.sizes','if self.leaves["a"].size > 0[m] then old_key else old_key'))]:
        src=(args.predecessor/'sources/body-generated-taint.ok').read_text().replace('ontokin "0.18"','ontokin "0.19"').replace('profile "keyed-zip-0.1"','profile "keyed-rekey-0.1"')
        start=src.index(' = ',src.index('public derive result'))+3;end=src.index(';',start)
        src=src[:start]+expression+src[end:]
        add(name,'Keyed<Length>',expression,raw=src,outcome='invalid',code='OKL-E-DEPENDENCY-CYCLE',tags=['generated-taint','empty' if 'empty' in name else 'callback'])
    inherited=(args.predecessor/'sources/cached-empty-generated-taint.ok').read_text()
    old_zip='zip_keyed<Length, Length, Length>(keyed<Length>{}, filter_keyed<Length>(keyed<Length>{"x": self.copied}, (fk, fv) -> false), (key, lv, rv) -> lv)'
    empty_rekey=rekey('Length','filter_keyed<Length>(keyed<Length>{"x": self.copied}, (fk, fv) -> false)','old_key')
    assert old_zip in inherited
    for name,expr in [('cached-empty-generated-taint',empty_rekey),('condition-only-empty-generated-taint','if len('+empty_rekey+') == 0 then keyed<Length>{} else keyed<Length>{}')]:
        src=inherited.replace('ontokin "0.18"','ontokin "0.19"').replace('profile "keyed-zip-0.1"','profile "keyed-rekey-0.1"').replace(old_zip,expr)
        add(name,'Keyed<Length>',expr,raw=src,outcome='invalid',code='OKL-E-DEPENDENCY-CYCLE',tags=['generated-taint','empty','cached-read','condition-only' if name.startswith('condition') else 'direct'])
    # No body may hide a statically invalid unselected branch, even if empty.
    invalid('empty-unselected-constructor-signature','Int','keyed<Int>{}','if true then "a" else (if len(keyed<Point3>{"x":point(world,1[m])})==0 then "b" else "c")',code='OKL-E-TYPE',tags=['empty','constructor-signature','static-unselected'])
    # The duplicate token and full entry locations are independent of author order.
    valid('case-sensitive-distinct-new-keys','Int',[('a','1'),('b','2')],'if old_key=="a" then "A" else "a"',{'a':'A','b':'a'},tags=['case-sensitive','key-domain'])

    add('grouped-input-origin','Keyed<Int>',rekey('Int','(keyed<Int>{"a":7})','"b"'),[('b','7')],old_keys=['a'],mapping={'a':'b'},tags=['grouped-input','original-entry-origin'])
    inside=rekey('String','keyed<String>{"tag":"b"}','"tag2"','ik,iv')
    add('rekey-inside-body-indexed','Keyed<Int>',rekey('Int','keyed<Int>{"a":7}',inside+'["tag2"]'),[('b','7')],tags=['nested-body','selected-inner-origin'])
    add('rekey-inside-body-condition','Keyed<Int>',rekey('Int','keyed<Int>{"a":7}','if len('+inside+')==1 then "b" else "c"'),[('b','7')],tags=['nested-body','condition-only-inner-origin'])
    add('captured-rekey-inside-body','Keyed<Int>',rekey('Int','keyed<Int>{"a":7}','self.names["tag2"]'),[('b','7')],members='public derive names @ "names": Keyed<String> = '+inside+';',tags=['nested-body','captured-inner-origin'])
    rr=rekey('Int','keyed<Int>{"a":2}','"b"')
    add('map-constant-retains-rekey','Keyed<Int>','map_keyed<Int>('+rr+', (mk,mv)->9)',[('b','9')],tags=['downstream-map','ignored-input-origin'])
    add('reduce-constant-retains-rekey','Int','reduce_keyed<Int>('+rr+', 0, (acc,rk,rv)->7)',control_expr='7',tags=['downstream-reduce','ignored-input-origin'])
    add('filter-drop-all-retains-rekey','Keyed<Int>','filter_keyed<Int>('+rr+', (fk,fv)->false)',[],tags=['downstream-filter','empty','aggregate-only'])
    add('unselected-rekey-not-evaluated','Keyed<Int>','if true then keyed<Int>{"plain":7} else '+rekey('Int','keyed<Int>{"a":1,"b":2}','"same"'),[('plain','7')],tags=['unselected-dynamic','no-invented-origin'])

    # Bind canonical resolved leaf spelling and exact original locations for
    # cases whose input is a parameter, helper, or inherited composition.
    for c in cases:
        source=(root/c['source']).read_text()
        fm=json.loads((root/c['file_manifest']).read_text())
        module_nodes=[]
        for module in fm['modules']:
            ms=(root/module['path']).read_text()
            mn=rekey_nodes(ms)
            for n in mn:
                def relabel(v):
                    if isinstance(v,dict):
                        if set(v)=={'source_id','source_revision','filename','start_byte','end_byte'}:
                            return dict(v,source_id='package:'+module['package_id']+'@'+module['version'],filename=module['filename'])
                        return {k:relabel(x) for k,x in v.items()}
                    if isinstance(v,list):return [relabel(x) for x in v]
                    return v
                module_nodes.append(relabel(n))
        if module_nodes:
            c['source_rekey_records'] += [{k:v for k,v in n.items() if not k.startswith('_')} for n in module_nodes]
            c['source_rekey_binders'] += [{'expression':n['expression'],'names':n['_binders'],'types':['String',n['element_type']]} for n in module_nodes]
        if c['expected_outcome']!='valid':continue
        c.setdefault('expected',{})['expected_declared_png_ids']=['label'] if c['canonical_manifest']['assets'] else []
        n=rekey_nodes(source)
        declared_entries=[]
        for marker in re.finditer(r'\bkeyed<',source):
            brace=source.find('{',marker.start());
            if brace<0:continue
            try:end=matched(source,brace,'{','}')+1
            except ValueError:continue
            declared_entries.append(entry_spans(source,marker.start(),end))
        by_key={}
        for mapping0 in declared_entries:
            for key,loc in mapping0.items(): by_key.setdefault(key,[]).append(loc)
        root_mappings={
          'explicit-namespace-map':{'a':'ns.a','b':'ns.b'},'input-alias-remains-unmodified':{'a':'ns.a','b':'ns.b'},'ignored-payload-retains-input-read':{'a':'ns.a','b':'ns.b'},
          'map-prepares-input':{'a':'ns.a'},'filter-prepares-input':{'b':'ns.b'},'merge-prepares-input':{'a':'ns.a','b':'ns.b'},'zip-prepares-input':{'a':'ns.a'},
          'guarded-helper-replay':{'a':'ns.a'},'imported-new-rekey-helper':{'a':'ns.a'}}
        if c['name'] in root_mappings:
            mapping0=root_mappings[c['name']]; nodes0=n or module_nodes; assert len(nodes0)==1,c['name']
            rec={k:v for k,v in nodes0[0].items() if not k.startswith('_')}
            c['expected']['root_aggregate_rekey_record']=rec
            c['expected']['root_selected_rekey_records']={new:dict(rec,old_key=old,new_key=new,input_entry=by_key[old][0]) for old,new in mapping0.items()}
            c['expected'].pop('input_origin_mapping_requires_external_case_expectation',None)
            c['expected']['old_to_new']=mapping0
            c['expected']['output_key_order']=sorted(mapping0.values())
        if c['name']=='nested-rekey':
            assert len(n)==2
            outer,inner=[{k:v for k,v in node.items() if not k.startswith('_')} for node in n]
            origin=by_key['a'][0]
            c['expected']['exact_aggregate_rekey_records']=[inner,outer]
            c['expected']['exact_stored_rekey_records']={'c':[dict(inner,old_key='a',new_key='b',input_entry=origin),dict(outer,old_key='b',new_key='c',input_entry=origin)]}
            c['expected']['exact_public_selected_rekey_records']={'c':c['expected']['exact_aggregate_rekey_records']+c['expected']['exact_stored_rekey_records']['c']}
        if c['name'] in ['rekey-inside-body-indexed','rekey-inside-body-condition','captured-rekey-inside-body']:
            if c['name']=='captured-rekey-inside-body': inner_node,outer_node=n
            else: outer_node,inner_node=n
            outer={k:v for k,v in outer_node.items() if not k.startswith('_')}
            inner={k:v for k,v in inner_node.items() if not k.startswith('_')}
            origin=by_key['a'][0];tag_origin=by_key['tag'][0]
            outer_entry=dict(outer,old_key='a',new_key='b',input_entry=origin)
            inner_entry=dict(inner,old_key='tag',new_key='tag2',input_entry=tag_origin)
            stored=[inner]+([] if c['name']=='rekey-inside-body-condition' else [inner_entry])+[outer_entry]
            c['expected']['exact_aggregate_rekey_records']=[inner,outer]
            c['expected']['exact_stored_rekey_records']={'b':stored}
            c['expected']['exact_public_selected_rekey_records']={'b':[inner,outer]+[r for r in stored if r!=inner]}
        if c['name'] in ['filter-drop-all-retains-rekey','map-constant-retains-rekey','reduce-constant-retains-rekey']:
            rec={k:v for k,v in n[0].items() if not k.startswith('_')}
            selected=dict(rec,old_key='a',new_key='b',input_entry=by_key['a'][0])
            if c['name']=='filter-drop-all-retains-rekey':c['expected']['exact_aggregate_rekey_records']=[rec]
            elif c['name']=='map-constant-retains-rekey':
                c['expected']['exact_aggregate_rekey_records']=[rec]
                c['expected']['exact_public_selected_rekey_records']={'b':[rec,selected]}
            else:c['expected']['exact_scalar_rekey_records']=[rec,selected]
        if c['name']=='unselected-rekey-not-evaluated':
            c['expected']['exact_aggregate_rekey_records']=[]
            c['expected']['body_evaluations']=0
            c['expected']['exact_public_selected_rekey_records']={'plain':[]}
        if c['name'] in ['explicit-namespace-map','ignored-payload-retains-input-read','input-alias-remains-unmodified']:
            c['expected']['required_actual_member_reads']=['items','names']
        if c['name']=='empty-retains-input-read':c['expected']['required_actual_member_reads']=['items']
        if c['name']=='condition-only-rekey':
            rec={k:v for k,v in n[0].items() if not k.startswith('_')}
            c['expected']['exact_aggregate_rekey_records']=[rec]
            c['expected']['plain_output_key_has_no_rekey_selected_contributor']=True
            c['expected']['exact_public_selected_rekey_records']={'plain':[rec]}

    expected={'schema_version':'ontokin.c086-independent-source-expectations/0.1','status':'draft_inputs_not_frozen_not_execution_results',
      'source_baseline':BASELINE,'source_version':'0.19','profile':'keyed-rekey-0.1','agent_protocol':'ontokin.agent/0.19','target_contract':'ontokin.glb/0.19',
      'case_count':len(cases),'cases':cases,'counts_are_not_execution_results':True,
      'independence':{'OntoKin_imports':False,'candidate_measurements_used':False,'derivation':'Explicit literal payloads, authored key mapping, canonical ASCII order, contract refusal precedence and source byte locations',
      'copied_unchanged_predecessor_constructor_inputs':copied_leaf_inputs},
      'remaining_before_freeze':['independent semantic/coverage review','exact .18 control preflight on unchanged C085','full inherited-origin expectations for compositions','representative Agent/delivery freeze integration']}
    dump(root/'expected.json',expected)
    dump(root/'budget-expectations.json',{'schema_version':'ontokin.c086-independent-budget-expectations/0.1','status':'predetermined_not_candidate_costs','ordinary_defaults':{'max_operations':100000,'max_elapsed_ms':30000},'lower_bound':{'max_operations':1,'expected_outcome':'resource_limit','reason':'More than one charged source admission/type/expression step is required even for empty input.'},'adequate':{'source_case':'maximum-256','max_operations':100000,'max_elapsed_ms':30000,'expected_outcome':'valid','basis':'256 simple Int leaves, 256 String-identity callbacks, at most 64 bytes per key, 256 dictionary collision lookups, a bounded 256-entry sort and one final immutable result. No data-dependent loop or geometry beyond one box. This is a conservative finite-fixture allowance, not an exact charge count.'},'unchanged_original_gates':True})
    dump(root/'AUTHORING-RECEIPT.json',{'status':'authored_not_preflighted','case_count':len(cases),'valid_controls':sum(c['expected_outcome']=='valid' for c in cases),'intended_refusals':sum(c['expected_outcome']=='invalid' for c in cases),'runtime_executions':0,'candidate_runtime_used':False,'generator_sha256':sha(Path(__file__).read_bytes()),'expected_sha256':sha((root/'expected.json').read_bytes())})
    print(json.dumps({'destination':str(root),'cases':len(cases),'controls':sum(c['expected_outcome']=='valid' for c in cases),'expected_sha256':sha((root/'expected.json').read_bytes())}))

if __name__=='__main__':main()
