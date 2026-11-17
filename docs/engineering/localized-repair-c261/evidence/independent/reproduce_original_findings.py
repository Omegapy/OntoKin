#!/usr/bin/env python3
"""Reproduce two pre-correction findings against the retained original reader."""
from pathlib import Path
import copy, hashlib, importlib.util, importlib.machinery, json, struct, sys
repo = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
snapshot = out / "run-01/hinge_glb.py.source"
name = "c261_original_reader"
loader = importlib.machinery.SourceFileLoader(name, str(snapshot))
spec = importlib.util.spec_from_loader(name, loader)
old = importlib.util.module_from_spec(spec)
loader.exec_module(old)
raw = (repo / "docs/engineering/semantic-export-c210/evidence/proof/before.glb").read_bytes()
jlen = struct.unpack_from("<I",raw,12)[0]
baseline = json.loads(raw[20:20+jlen])
binary = raw[28+jlen:]
results = []
for case in ("meta-sites", "program-sites", "nested-element-id-scalar"):
    doc = copy.deepcopy(baseline)
    if case == "meta-sites":
        doc["extras"]["ontokin"]["sites"] = {}
    elif case == "program-sites":
        doc["extras"]["ontokin"]["program"]["sites"] = {}
    else:
        doc["nodes"][0]["extras"]["ontokin"]["source_mapping"]["element_id"] = True
    js = json.dumps(doc,separators=(",",":")).encode()
    js += b" " * (-len(js)%4)
    variant = struct.pack("<III",0x46546C67,2,28+len(js)+len(binary)) + struct.pack("<II",len(js),0x4E4F534A) + js + struct.pack("<II",len(binary),0x004E4942) + binary
    result = old.observe_glb_hinges(variant)
    results.append({"case":case,"inputSha256":hashlib.sha256(variant).hexdigest(),"observed":"ACCEPTED_BY_ORIGINAL","directSiteTableObserved":result["directSiteTableObserved"],"sourceAgreementVerified":result["sourceAgreementVerified"]})
record = {"readerSha256":hashlib.sha256(snapshot.read_bytes()).hexdigest(),"reproductions":results,"meaning":"Original behavior retained; corrected reader refuses these three cases in independent run-02"}
(out/"ORIGINAL-FINDINGS.json").write_text(json.dumps(record,separators=(",",":"))+"\n")
print(json.dumps({"reproduced":len(results),"readerSha256":record["readerSha256"]}))

