"""HOST review 001, script h04b: a process launched as the observer was, recording its own facts.

Run as: /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC UV_THREADPOOL_SIZE=2 \
        <worktree>/.venv/bin/python -I -S -B h04b_declared_launch.py --host H --output OUT
It compares its environment (the declared map, plus what CoreFoundation added) and its interpreter facts
with HOST. It starts nothing and writes only its absent output file.
"""
import argparse
import ctypes
import importlib.util
import json
import locale
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
_spec = importlib.util.spec_from_file_location("h_common", HERE + "/h_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

FLAGS = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
         "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated", "dev_mode",
         "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")


def process_image():
    lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    fn = lib.proc_pidpath
    fn.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    fn.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(4096)
    length = fn(os.getpid(), buf, 4096)  # run 1 sliced buf.raw before this call filled it (superseded output)
    return os.fsdecode(buf.raw[:length])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    host = json.loads(C.read_bound(args.host, keep=True)[0])
    environment = dict(os.environ)
    mine = {"implementation": sys.implementation.name, "version": "%d.%d.%d" % sys.version_info[:3],
            "build_string": sys.version, "flags": {name: getattr(sys.flags, name) for name in FLAGS},
            "executable": sys.executable, "base_executable": getattr(sys, "_base_executable", None),
            "prefix": sys.prefix, "base_prefix": sys.base_prefix, "path": list(sys.path),
            "process_image": process_image()}
    expected_env = {**host["environment"]["declared"], "__CF_USER_TEXT_ENCODING":
                    host["environment"]["cf_user_text_encoding"]}
    checks = [
        {"id": "L1", "what": "the process environment is exactly the declared map plus __CF_USER_TEXT_ENCODING with HOST's value",
         "passed": environment == expected_env, "details": {"names": sorted(environment)}},
        {"id": "L2", "what": "HOST.python.interpreter equals this process's facts, sys.flags included",
         "passed": mine == host["python"]["interpreter"],
         "details": {"differing": sorted(k for k in mine if mine[k] != host["python"]["interpreter"].get(k))}},
    ]
    out = {"script": "h04b_declared_launch.py", "process": C.process_facts(), "environment": environment,
           "lc_ctype": locale.setlocale(locale.LC_CTYPE), "interpreter": mine, "checks": checks,
           "failed": [c["id"] for c in checks if not c["passed"]], "refused_events": C.REFUSED_EVENTS}
    C.write_new(args.output, out)
    print(json.dumps({"failed": out["failed"], "lc_ctype": out["lc_ctype"], "names": sorted(environment)}))


if __name__ == "__main__":
    main()
