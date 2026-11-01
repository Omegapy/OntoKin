"""Source-only lexical proof using exact C085 modules; no parser/evaluator invocation."""
from dataclasses import asdict
from pathlib import Path
import hashlib,json,sys
from ontokin.syntax import lex
from ontokin.diagnostics import OntoKinError,Source
import ontokin.syntax,ontokin.diagnostics
HERE=Path(__file__).resolve().parent
# These four answers were declared from LANG-001 and the unchanged lexer before execution.
SPECS=(
 ('escaped-snippet',b'"caf\\u00e9"',{'outcome':'invalid','code':'OKL-E-LEXICAL','phase':'lexical','rule_ids':['LANG-001'],'span':[4,6]}),
 ('utf8-snippet','"café"'.encode('utf-8'),{'outcome':'tokenized','value':'café','span':[0,7]}),
 ('original-full-source',(HERE/'original-output-key-unicode.ok').read_bytes(),{'outcome':'invalid','code':'OKL-E-LEXICAL','phase':'lexical','rule_ids':['LANG-001'],'span':[223,225]}),
 ('corrected-full-source',(HERE/'corrected-output-key-unicode.ok').read_bytes(),{'outcome':'tokenized','value':'café','span':[219,226]}),
)
def sha(raw):return hashlib.sha256(raw).hexdigest()
rows=[]
for name,raw,expected in SPECS:
 row={'name':name,'input_bytes':len(raw),'input_sha256':sha(raw),'expected_before_execution':expected}
 try:
  tokens=lex(raw.decode('utf-8'),source_id='entry')
 except OntoKinError as error:
  d=error.diagnostic.to_dict(Source(raw.decode('utf-8'),'main.ok',raw))
  row['actual']={'outcome':'invalid','diagnostic':d}
  assert expected['outcome']=='invalid'
  assert all(d[key]==expected[key] for key in ('code','phase','rule_ids'))
  assert [d['primary']['start_byte'],d['primary']['end_byte']]==expected['span']
 else:
  row['actual']={'outcome':'tokenized','tokens':[asdict(token) for token in tokens]}
  assert expected['outcome']=='tokenized'
  selected=[token for token in tokens if token.kind=='STRING' and token.value==expected['value']]
  assert len(selected)==1 and [selected[0].start,selected[0].end]==expected['span']
 row['matched_declared_lexical_answer']=True;rows.append(row)
result={'schema_version':'ontokin.c086-unicode-lexical-proof/0.1','baseline_commit':'f4c90c04b9b381de73d46715d52e68f588e49e4f','operation':'unchanged C085 syntax.lex only; no .19 parsing, validation, runtime, exporter, or candidate expected-answer extraction',
 'interpreter':{'executable':sys.executable,'version':sys.version,'dont_write_bytecode':sys.dont_write_bytecode},
 'loaded_modules':[{'path':module.__file__,'sha256':sha(Path(module.__file__).read_bytes())} for module in (ontokin.syntax,ontokin.diagnostics)],
 'script_sha256':sha(Path(__file__).read_bytes()),'checks':rows,'passed':all(row['matched_declared_lexical_answer'] for row in rows),'complete_feature_release':False,'full_product_acceptance':False}
print(json.dumps(result,indent=2,ensure_ascii=False))
