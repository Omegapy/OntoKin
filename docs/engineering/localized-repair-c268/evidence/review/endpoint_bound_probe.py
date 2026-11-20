#!/usr/bin/env python3
"""Deterministic inspection of endpoint length guarding before mapping lookup."""
import argparse, hashlib, json, subprocess, sys, types
from pathlib import Path
from unittest.mock import patch

p=argparse.ArgumentParser()
p.add_argument("--repo",required=True,type=Path)
p.add_argument("--output",required=True,type=Path)
a=p.parse_args();repo=a.repo.resolve()
path=repo/"docs/engineering/localized-repair-c268/endpoint_reader.py"
raw=path.read_bytes()
m=types.ModuleType("_c268_review_selector_guard")
m.__file__=str(path);sys.modules[m.__name__]=m
exec(compile(raw,str(path),"exec"),m.__dict__)
original=m.PINS
rows=[]
for value in ("", "z"*7, "z"*1000001, "bogus"):
    visited=[]
    class ContainsSpy:
        def __contains__(self, key):
            visited.append(len(key))
            return key in original
        def __getitem__(self, key): return original[key]
    with patch.object(m,"PINS",ContainsSpy()), patch.object(m.os,"open",side_effect=AssertionError("invalid selector attempted file access")):
        try: m.read_bound_endpoint(repo,value)
        except m.Fault as exc: outcome={"code":exc.code,"reason":exc.reason}
        else: outcome={"unexpected":"admitted"}
    expected=[] if len(value) not in (5,6) else [len(value)]
    rows.append({"selector_recipe":"z repeated N for lengths7/1000001; empty text for0; bogus for5",
                 "length":len(value),"expected_lookup_lengths":expected,"observed_lookup_lengths":visited,
                 "refusal":outcome,"passed":visited==expected and outcome["code"]=="ENDPOINT"})
record={"schema":"ontokin.c268.endpoint-guard-review/1","reviewer":"/root/state_audit",
        "source_revision":subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
        "reader":{"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()},
        "probe":{"bytes":len(Path(__file__).read_bytes()),"sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "cases":rows,"passed":all(x["passed"] for x in rows),
        "meaning":"Contains-spy tracks lookup ordering, not elapsed time; original refusal outcome may remain correct despite unbounded selector hashing."}
a.output.write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))

