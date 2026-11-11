"""Execute the single reviewed L-R1 cohort without a retry path."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def digest(path, deadline=None):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            if deadline is not None and time.monotonic() >= deadline:
                raise RuntimeError("Bounded lifecycle preflight deadline")
            h.update(chunk)
    return h.hexdigest()


def verify(lock, root, deadline=None):
    for relative,row in lock["repository_files"].items():
        path=root/relative
        if path.suffix == ".py" and any((path.parent/"__pycache__").glob(path.stem+".*.pyc")):
            raise RuntimeError("Unbound repository bytecode cache: "+relative)
        if path.is_symlink() or not path.is_file() or path.stat().st_size != row["size_bytes"] or digest(path,deadline) != row["sha256"]:
            raise RuntimeError("Lifecycle executable/input changed: "+relative)
    inventory=Path(lock["host_inventory"])
    if digest(inventory) != lock["host_inventory_sha256"]:
        raise RuntimeError("Host inventory changed")
    host=json.loads(inventory.read_bytes())
    checked=set()
    for row in host["files"]:
        actual=Path(row["path"])
        if row["symlink"]:
            if not actual.is_symlink() or os.readlink(actual) != row["link_target"]:
                raise RuntimeError("Host dependency alias changed: "+str(actual))
        if str(actual.resolve()) != row["resolved_path"]:
            raise RuntimeError("Host dependency target changed: "+str(actual))
        resolved=actual.resolve()
        if resolved not in checked:
            if not resolved.is_file() or resolved.stat().st_size != row["bytes"] or digest(resolved,deadline) != row["sha256"]:
                raise RuntimeError("Host dependency changed: "+str(actual))
            checked.add(resolved)
    if Path(sys.executable).resolve() != Path(lock["python"]).resolve():
        raise RuntimeError("Wrong lifecycle interpreter")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--lock",required=True)
    parser.add_argument("--approval",required=True)
    options=parser.parse_args()
    lock_path=Path(options.lock).resolve()
    lock=json.loads(lock_path.read_bytes())
    if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        raise RuntimeError("The reviewed coordinator requires -IBS isolation")
    if dict(os.environ) != lock["environment"]:
        raise RuntimeError("Coordinator environment differs from the reviewed finite environment")
    approval=json.loads(Path(options.approval).read_bytes())
    lock_hash=digest(lock_path)
    if (approval.get("decision") != "APPROVED_FOR_L_R1" or approval.get("input_lock_sha256") != lock_hash
            or approval.get("amendment_sha256") != lock["amendment_sha256"]):
        raise RuntimeError("Exact independent L-R1 approval is required")
    root=Path(__file__).resolve().parents[3]
    if root != Path(lock["repo_root"]).resolve():
        raise RuntimeError("Locked repository root differs")
    if digest(root/lock["amendment_path"]) != lock["amendment_sha256"]:
        raise RuntimeError("Reviewed amendment changed")
    actual_argv=[str(Path(sys.orig_argv[0]).resolve()),*sys.orig_argv[1:]]
    if actual_argv != lock["argv"]:
        raise RuntimeError("Lifecycle command differs from exact reviewed argv")
    verify(lock,root,time.monotonic()+30)
    destination=Path(lock["output_directory"])
    destination.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(root))
    from prototypes.static_tray_v01.lifecycle import control
    events=[]
    results=[]
    def event(value):
        events.append(value)
        with (destination/"ledger.jsonl").open("a") as stream:
            stream.write(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n")
            stream.flush()
            os.fsync(stream.fileno())
    for entry in lock["slots"]:
        started=time.monotonic()
        verify(lock,root,started+30)
        event({"slot":entry["slot"],"case":entry["case"],"state":"RESERVED","input_lock_sha256":lock_hash,
               "monotonic":time.monotonic()})
        def child_started(process):
            event({"slot":entry["slot"],"state":"STARTED","process_group":process.get("process_group"),
                   "monotonic":process.get("start_monotonic"),"direct_child_starts":1})
        remaining_ms=30000-(time.monotonic()-started)*1000
        if remaining_ms <= 0:
            raise RuntimeError("Per-control preflight exhausted the 30000 ms allowance")
        result=control(entry["case"],destination/entry["slot"],environment=lock["environment"],
                       total_ms=remaining_ms,on_started=child_started)
        total=(time.monotonic()-started)*1000
        binding={"input_lock_sha256":lock_hash,"implementation":lock["implementation"],
                 "amendment_sha256":lock["amendment_sha256"],"elapsed_including_preflight_ms":total,
                 "argv":lock["argv"],"slot":entry["slot"]}
        (destination/entry["slot"]/"INPUT-BINDING.json").write_text(json.dumps(binding,sort_keys=True,indent=2)+"\n")
        process=result.get("process") or {}
        passed=result["passed"] and total<=30000
        event({"slot":entry["slot"],"state":"PASSED" if passed else "FAILED",
               "observed_outcome":result["state"],"direct_child_starts":result["direct_child_starts"],
               "grandchild_starts":result["grandchild_starts"],"monotonic":time.monotonic()})
        results.append({"slot":entry["slot"],"passed":passed,"direct_child_starts":result["direct_child_starts"],
                        "grandchild_starts":result["grandchild_starts"],"state":result["state"],"elapsed_ms":total})
        if not passed:
            break
    report={"schema":"ontokin.static-tray.lifecycle-r1/0.1.0","passed":len(results)==8 and all(x["passed"] for x in results),
            "input_lock_sha256":lock_hash,"amendment_sha256":lock["amendment_sha256"],"results":results,
            "additional_direct_starts":sum(x["direct_child_starts"] for x in results),
            "additional_grandchild_starts":sum(x["grandchild_starts"] for x in results),
            "historical_direct_starts":8+sum(x["direct_child_starts"] for x in results),
            "historical_grandchild_starts":1+sum(x["grandchild_starts"] for x in results),
            "native_starts":0,"unused_slots":[x["slot"] for x in lock["slots"]][len(results):]}
    (destination/"RESULTS.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True))
    return 0 if report["passed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
