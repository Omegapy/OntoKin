"""Observe one unchanged synthetic reader CPU suite and retain its actual inputs.

This preparation observer starts only the Python reader CLIs already called by
the suite. It does not start Blender, Node or a lifecycle qualification stub.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import time
import unittest


def encoded(value):
    return json.dumps(value,sort_keys=True,indent=2,allow_nan=False).encode()+b"\n"


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--source-commit",required=True)
    args=parser.parse_args()
    repo=Path(args.repo).resolve()
    out=Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=False)
    (out/"blobs").mkdir()
    (out/"events").mkdir()
    state={"sequence":0,"test":None,"audit_calls":0,"corrupt_calls":0,"reader_cli_starts":0}

    def blob(data):
        digest=hashlib.sha256(data).hexdigest()
        target=out/"blobs"/digest
        if not target.exists():
            target.write_bytes(data)
        return {"sha256":digest,"size_bytes":len(data),"path":"blobs/"+digest}

    def file_input(path,limit=8*1024*1024+1):
        path=Path(path)
        item={"original_path":str(path)}
        if not path.exists() and not path.is_symlink():
            return {**item,"file_type":"absent"}
        info=path.lstat()
        item["posix_mode"]=oct(info.st_mode)
        if stat.S_ISLNK(info.st_mode):
            return {**item,"file_type":"symlink","target":os.readlink(path)}
        if not stat.S_ISREG(info.st_mode):
            return {**item,"file_type":"directory" if stat.S_ISDIR(info.st_mode) else "special"}
        with path.open("rb") as stream:
            data=stream.read(limit)
        return {**item,"file_type":"regular","content":blob(data),
                "original_size_bytes":info.st_size,"truncated":info.st_size>len(data)}

    def binding(value,role):
        if role=="artifact" or isinstance(value,Path) or (isinstance(value,str) and value not in {"Q01","Q02","Q03","Q04","Q05"}):
            return file_input(value)
        return {"kind":"in-memory-json","content":blob(encoded(value))}

    def event(kind,fields):
        state["sequence"]+=1
        item={"sequence":state["sequence"],"test":state["test"],"kind":kind,**fields}
        (out/"events"/(str(state["sequence"]).zfill(5)+".json")).write_bytes(encoded(item))

    closure=["tools/static_tray_reader_v01/"+name for name in
             ("audit.py","reader.py","glb.py","expected.py","corrupt.py")]
    closure.append("tests/test_static_tray_reader_v01.py")
    snapshots=[]
    for name in closure:
        item=file_input(repo/name)
        snapshots.append({"repository_path":name,**item})
    observer=file_input(__file__)
    executable=Path(sys.executable).resolve()
    runtime={"executable":sys.executable,"resolved_executable":str(executable),
             "executable_sha256":hashlib.sha256(executable.read_bytes()).hexdigest(),
             "version":sys.version,"flags":str(sys.flags),"uname":list(os.uname())}

    spec=importlib.util.spec_from_file_location("captured_static_tray_reader_tests",repo/closure[-1])
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_audit=module.audit
    original_corrupt=module.corrupt
    original_run=module.subprocess.run

    def observed_audit(path,expected="Q01",baseline_right=None,delivery_rules=None):
        state["audit_calls"]+=1
        fields={"artifact":binding(path,"artifact"),"expected":binding(expected,"expected"),
                "baseline":binding(baseline_right,"baseline"),"delivery_rules":binding(delivery_rules,"rules")}
        try:
            result=original_audit(path,expected,baseline_right,delivery_rules)
            fields["result"]=blob(encoded(result))
            event("audit",fields)
            return result
        except BaseException as exc:
            event("audit",{**fields,"exception":{"type":type(exc).__name__,"message":str(exc)}})
            raise

    def observed_corrupt(case,artifact,output,variant="copy"):
        state["corrupt_calls"]+=1
        fields={"case":case,"variant":variant,"artifact":file_input(artifact),"output_before":file_input(output)}
        try:
            result=original_corrupt(case,artifact,output,variant)
            event("corrupt",{**fields,"output_after":file_input(output),"result":blob(encoded(result))})
            return result
        except BaseException as exc:
            event("corrupt",{**fields,"output_after":file_input(output),
                             "exception":{"type":type(exc).__name__,"message":str(exc)}})
            raise

    def observed_run(command,*positional,**kwargs):
        if (not isinstance(command,list) or len(command)<3 or command[:2]!=[sys.executable,"-IB"]
                or Path(command[2]).name not in {"audit.py","corrupt.py"} or kwargs.get("shell")):
            raise AssertionError("Evidence replay permits only the suite's isolated Python reader CLI")
        state["reader_cli_starts"]+=1
        fields={"command":command,"timeout_seconds":kwargs.get("timeout"),"inputs":{},"script_directory":[]}
        for path in sorted(Path(command[2]).parent.iterdir()):
            fields["script_directory"].append(file_input(path))
        for flag in ("--artifact","--lock","--baseline","--result"):
            if flag in command:
                fields["inputs"][flag]=file_input(command[command.index(flag)+1])
        started=time.monotonic()
        try:
            result=original_run(command,*positional,**kwargs)
            fields.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,
                          elapsed_ms=(time.monotonic()-started)*1000)
            if "--result" in command:
                fields["result_after"]=file_input(command[command.index("--result")+1])
            event("reader-cli",fields)
            return result
        except BaseException as exc:
            event("reader-cli",{**fields,"exception":{"type":type(exc).__name__,"message":str(exc)}})
            raise

    module.audit=observed_audit
    module.corrupt=observed_corrupt
    module.subprocess.run=observed_run

    class ObservedResult(unittest.TextTestResult):
        def startTest(self,test):
            state["test"]=test.id()
            super().startTest(test)

    started=time.monotonic()
    try:
        with (out/"CPU-TESTS.log").open("w") as stream:
            suite=unittest.defaultTestLoader.loadTestsFromModule(module)
            result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=ObservedResult).run(suite)
    finally:
        module.subprocess.run=original_run
    unchanged=all(hashlib.sha256((repo/item["repository_path"]).read_bytes()).hexdigest()==item["content"]["sha256"] for item in snapshots)
    report={"schema":"ontokin.static-tray.reader-evidence-replay/0.1.0",
            "scope":"Separately identified synthetic CPU replay, not the original 20-method run",
            "source_commit":args.source_commit,"command":list(sys.orig_argv),"cwd":str(Path.cwd()),
            "runtime":runtime,"observer":observer,"source_snapshots":snapshots,"source_bytes_unchanged":unchanged,
            "counts":state,"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
            "passed":result.wasSuccessful() and unchanged,"elapsed_ms":(time.monotonic()-started)*1000,
            "native_starts":0,"node_starts":0,"lifecycle_starts":0}
    (out/"REPLAY.json").write_bytes(encoded(report))
    inventory=[]
    for path in sorted(out.rglob("*")):
        if path.is_file():
            data=path.read_bytes()
            inventory.append({"path":path.relative_to(out).as_posix(),"sha256":hashlib.sha256(data).hexdigest(),
                              "size_bytes":len(data),"posix_mode":oct(path.stat().st_mode)})
    (out/"FILES.json").write_bytes(encoded(inventory))
    print(json.dumps({"passed":report["passed"],"tests":result.testsRun,"audit_calls":state["audit_calls"],
                      "reader_cli_starts":state["reader_cli_starts"],"output":str(out)},sort_keys=True))
    return 0 if report["passed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
