"""HOST review 001, script 06: a process launched as the observer was, apart from the launcher's name.

Launched by the reviewer as
    /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC UV_THREADPOOL_SIZE=2 \
        <python3 as this session resolves it> -I -S -B w3h_06_declared.py --host H --out OUT ...
env executes the interpreter in its own process. The script compares its own environment with HOST's
record (the declared five plus __CF_USER_TEXT_ENCODING with HOST's value; names only, no value is
written) and its interpreter facts with HOST's /python/interpreter, apart from the two launcher paths.
"""
import sys

ORIGINAL_PATH = list(sys.path)  # before this script adds its own directory

import argparse  # noqa: E402
import ctypes  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3h_common as C  # noqa: E402

C.install_hook()


def process_image():
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    fn = libc.proc_pidpath
    fn.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    fn.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(4096)
    length = fn(os.getpid(), buf, 4096)
    return os.fsdecode(buf.raw[:length]) if 0 < length < 4096 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", action="append", default=[])
    args = ap.parse_args()
    lab = C.Labeler([tuple(item.split("=", 1)) for item in args.label])
    ck = C.Checks()
    host = C.strict_loads(C.read_bytes(args.host)[0])
    declared = host["environment"]["declared"]
    cf = host["environment"]["cf_user_text_encoding"]
    env = dict(os.environ)
    ck.add("V01", env == {**declared, "__CF_USER_TEXT_ENCODING": cf},
           "this process's environment is exactly HOST's declared five plus __CF_USER_TEXT_ENCODING with HOST's "
           "value (compared, not written)", names=sorted(env), extra=sorted(set(env) - set(declared)),
           cf_equal=env.get("__CF_USER_TEXT_ENCODING") == cf)
    it = host["python"]["interpreter"]
    names = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
             "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated", "dev_mode",
             "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
    flags = {n: getattr(sys.flags, n) for n in names}
    mine = {"implementation": sys.implementation.name, "version": "%d.%d.%d" % sys.version_info[:3],
            "build_string": sys.version, "flags": flags, "prefix": sys.prefix, "base_prefix": sys.base_prefix,
            "path": ORIGINAL_PATH, "process_image": process_image()}
    same = {k: mine[k] == it[k] for k in mine}
    ck.add("V02", all(same.values()), "implementation, version, build string, all 18 sys.flags (utf8_mode 0 under "
           "LC_ALL=C.UTF-8), prefix, base prefix, sys.path and the process image equal HOST's", fields=same)
    ck.add("V03", os.path.realpath(sys.executable) == it["base_executable"],
           "this launcher resolves to HOST's base executable, the framework's bin/python3.12",
           executable=lab.text(sys.executable), base_executable=lab.text(getattr(sys, "_base_executable", "")))
    out = {"script": "w3h_06_declared.py", "process": C.process_identity(), "ended_epoch": time.time(),
           "checks": ck.rows, "summary": ck.summary(), "audit_events": C.EVENTS}
    print(C.write_new(args.out, lab.deep(out)), ck.summary())


if __name__ == "__main__":
    main()
