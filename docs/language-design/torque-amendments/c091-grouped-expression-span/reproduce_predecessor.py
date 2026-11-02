import hashlib,json,subprocess,sys
from pathlib import Path
base=Path(sys.argv[1]); output=Path(sys.argv[2]); sys.path.insert(0,str(base))
from ontokin.bundle import SourceUnit
from ontokin.texture_bundle import TextureBundle,load_texture_file_manifest
from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
from ontokin.construction import compile_construction
from ontokin.program_diagnostics import diagnostic_dict
from ontokin.diagnostics import OntoKinError
f=base/"docs/language-design/torque-v0.1/freeze"
b=load_texture_file_manifest(f/"control-spin-up.files.json")
old="body_mass = 2.5[kg];";new="body_mass = ((2[N*m] / 0) / 1[m^2/s^2]);"
assert b.entry.text.count(old)==1
raw=b.entry.raw.replace(old.encode(),new.encode())
source=SourceUnit("entry","main.ok",raw)
witness=TextureBundle(source,b.modules,b.assets)
ledger=SharedExecutionBudget();admit_entry_budget(source,ledger,profile="keyed-membership-0.1")
identity={}
for name in ["ontokin/syntax.py","ontokin/syntax02.py","ontokin/syntax14.py","ontokin/construction.py","ontokin/values.py"]:
 oldbytes=subprocess.check_output(["git","-C",str(base),"show","94a7796a54725ca764b2027deb43f09204f8a6de:"+name])
 actual=(base/name).read_bytes();assert oldbytes==actual,name
 identity[name]={"sha256":hashlib.sha256(actual).hexdigest(),"bytes":len(actual),"matches_C090_native_blob":True}
try:
 compile_construction(witness,execution_budget=ledger)
 raise AssertionError("Expected inherited division failure")
except OntoKinError as error:
 d=diagnostic_dict(error.diagnostic,witness)
 start,end=d["primary"]["start_byte"],d["primary"]["end_byte"]
 assert d["code"]=="OKL-E-NUMERIC" and d["message"]=="Division by zero."
 assert raw[start:end]==b"(2[N*m] / 0)"
 result={"status":"reproduced","basis":"94a7796a54725ca764b2027deb43f09204f8a6de","source_files":identity,"witness_source_sha256":hashlib.sha256(raw).hexdigest(),"diagnostic":d,"actual_primary_text":raw[start:end].decode(),"frozen_n28_expected_primary":next(x for x in json.loads((f/"refusal-cases.json").read_text())["cases"] if x["id"]=="n28-torque-child-before-duration-type")["expected"]["primary_source"],"scope":"Inherited grouped binary expression diagnostic includes parentheses; no runtime or frozen expectation was modified"}
 output.write_text(json.dumps(result,indent=2)+"\n")
 output.with_suffix(".ok").write_bytes(raw)
 print(json.dumps({"status":result["status"],"actual_primary_text":result["actual_primary_text"]}))
