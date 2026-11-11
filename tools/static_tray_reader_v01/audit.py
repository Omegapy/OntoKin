"""Isolated CLI for the independent static-tray geometry reader."""

import argparse
import hashlib
import json
from pathlib import Path
import signal
import sys
import time

# -B prevents writes, but Python may still execute an existing unbound pyc.
# Reject that alternate executable closure before importing any local helper.
_directory=Path(__file__).resolve().parent
if any(p.name=="__pycache__" or p.suffix in {".pyc",".pyo"} for p in _directory.iterdir()):
    raise ImportError("Unbound independent reader bytecode cache is forbidden")
# Only this independent, hash-checked implementation directory is added.
sys.path.insert(0,str(_directory))
from expected import expected_case, expected_bounds
from glb import InvalidGLB, verify_lock, write_result
from reader import audit


def deadline(_signum,_frame):
    raise TimeoutError("Independent reader exceeded its 30,000 ms deadline")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact",required=True)
    parser.add_argument("--expected",choices=["Q01","Q02","Q03","Q04","Q05"],required=True)
    parser.add_argument("--lock",required=True)
    parser.add_argument("--result",required=True)
    parser.add_argument("--baseline")
    args=parser.parse_args(argv)
    started=time.monotonic()
    signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,30.0)
    try:
        lock,lock_hash=verify_lock(args.lock)
        if not isinstance(lock["independent_reader"].get("delivery_rules"),dict):
            raise InvalidGLB("Audit CLI lock must bind the complete delivery rules","BINDING")
        report=audit(args.artifact,args.expected,args.baseline,
                     lock["independent_reader"]["delivery_rules"])
        report.update(input_lock_sha256=lock_hash,reader_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      elapsed_ms=(time.monotonic()-started)*1000,command=sys.argv)
        write_result(args.result,report)
        print(json.dumps({"passed":report["passed"],"finding_count":len(report["findings"]),
                          "result":str(Path(args.result).resolve())},sort_keys=True))
        return 0 if report["passed"] else 1
    except (InvalidGLB,TimeoutError,OSError,ValueError) as exc:
        print(json.dumps({"passed":False,"classification":getattr(exc,"classification","RESOURCE"),
                          "error":str(exc)},sort_keys=True),file=sys.stderr)
        return 2
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)


if __name__=="__main__":
    raise SystemExit(main())
