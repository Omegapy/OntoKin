"""HOST review 001, script h06: the final check, made after both reports were written.

Run as: <worktree>/.venv/bin/python -I -S -B h06_final_check.py --host H --plan P --out-dir OUT --output O
It rechecks HOST, the evidence, both inventories and the worktree, asks kill(pid, 0) for every PID that an
earlier script of this review recorded, and scans both reports again for machine paths and names.
"""
import argparse
import errno
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.realpath(__file__))


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE + "/" + name + ".py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load("h_common")
H02, H03, H04, H05 = load("h02_python_inventory"), load("h03_source_and_head"), load("h04_evidence"), \
    load("h05_report_json")


def main():
    parser = argparse.ArgumentParser()
    for name in ("host", "plan", "out-dir", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    out_dir = getattr(args, "out_dir")
    checks = []

    def check(cid, what, ok, **details):
        checks.append({"id": cid, "what": what, "passed": bool(ok), **({"details": details} if details else {})})
    host = json.loads(C.read_bound(args.host, keep=True)[0])
    plan = json.loads(C.read_bound(args.plan, keep=True)[0])
    report_raw, report_facts, _ = C.read_bound(out_dir + "/HOST-REVIEW-001.json", keep=True)
    report = json.loads(report_raw)
    md_raw, md_facts, _ = C.read_bound(out_dir + "/HOST-REVIEW-001.md", keep=True)
    host_facts = C.read_bound(args.host)[1]
    check("F1", "HOST's SHA-256 is unchanged and equals the report's host_sha256",
          host_facts["sha256"] == report["host_sha256"] == "34e94f29ea1b7d9d60b389598b4ce5bc7eaf6fcaa58f3798fc3df021a8f28a92")
    label, forbidden = H05.labeller(host)
    parent = plan["evidence"]["parent"]
    now = []
    for base, dirs, files in sorted(os.walk(parent)):
        for name in sorted(files):
            path = os.path.join(base, name)
            now.append({"path": label(path), "role": "evidence", **C.binding(C.read_bound(path)[1])})
    then = [row for row in report["reviewed_files"] if row["role"] == "evidence"]
    check("F2", "every evidence file is unchanged since h05 listed it, and no file was added", now == then,
          count=len(now))
    readback = json.loads(C.read_bound(parent + "/observe-001.readback.json", keep=True)[0])
    attempt = plan["evidence"]["attempt"]
    check("F3", "the attempt still equals the FC-K5 readback listing", H04.listing(attempt) == readback["directories"][attempt])
    doc, passes = H02.inventory(host["python"]["venv"], host["python"]["framework"])
    raw = C.canonical(doc)
    check("F4", "the Python inventory still recomputes to c277bdd3... (no bytecode or other change added)",
          C.sha256_bytes(raw) == host["python"]["inventory_sha256"], sha256=C.sha256_bytes(raw), passes=passes)
    source, problems = H03.source_inventory(host["source"]["root"])
    check("F5", "the source inventory still recomputes to 95abd300..., with no bytecode in the source trees",
          C.sha256_bytes(C.canonical(source)) == host["source"]["inventory"]["sha256"] and not problems)
    special = []
    for base, dirs, files in os.walk(host["source"]["root"]):
        if base == host["source"]["root"]:
            dirs[:] = [d for d in dirs if d != ".venv"]
        for name in dirs + files:
            if name in ("__pycache__", ".DS_Store") or name.endswith((".pyc", ".pyo")):
                special.append(os.path.relpath(os.path.join(base, name), host["source"]["root"]))
    check("F6", "no bytecode or .DS_Store anywhere in the worktree outside .venv", not special, found=special[:20])
    pids = {}
    for name in sorted(os.listdir(out_dir + "/outputs")):
        try:
            value = json.loads(C.read_bound(out_dir + "/outputs/" + name, keep=True)[0])
        except (ValueError, OSError):
            continue
        process = value.get("process") if isinstance(value, dict) else None
        if isinstance(process, dict):
            pids[process["pid"]] = name + " (python)"
            pids[process["ppid"]] = name + " (shell)"
    answers = {}
    for pid in sorted(pids):
        if pid in (os.getpid(), os.getppid()):
            continue
        try:
            os.kill(pid, 0)
            answers[pid] = "present"
        except ProcessLookupError:
            answers[pid] = "ESRCH"
        except PermissionError:
            answers[pid] = "EPERM"
    check("F7", "every earlier PID and shell PID of this review answers ESRCH", all(v == "ESRCH" for v in answers.values()),
          answers={str(k): v for k, v in answers.items()})
    hits = {"json": H05.scan(report_raw.decode("ascii"), forbidden), "md": H05.scan(md_raw.decode("utf-8"), forbidden)}
    check("F8", "neither report holds a machine path, the user's name or the package manager's name",
          not hits["json"] and not hits["md"], hits={k: len(v) for k, v in hits.items()})
    check("F9", "the report's own-files list holds the Markdown report as it is now",
          {"path": "OUT/HOST-REVIEW-001.md", **C.binding(md_facts)} in report["own_files"])
    out = {"script": "h06_final_check.py", "process": C.process_facts(), "checks": checks,
           "failed": [c["id"] for c in checks if not c["passed"]],
           "report_json": {"path": "OUT/HOST-REVIEW-001.json", **C.binding(report_facts)},
           "report_md": {"path": "OUT/HOST-REVIEW-001.md", **C.binding(md_facts)}, "refused_events": C.REFUSED_EVENTS}
    C.write_new(args.output, out)
    print(json.dumps({"failed": out["failed"], "checks": len(checks), "json_sha256": report_facts["sha256"],
                      "md_sha256": md_facts["sha256"], "pids_checked": len(answers)}))


if __name__ == "__main__":
    main()
