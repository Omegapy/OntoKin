"""W2 of C271-P36 (gate MR, stage S4): the launch record of the single observe start.

It writes two absent files with exclusive creation:

* M0-ENVIRONMENT.json: the declared environment as canonical JSON, the frozen file that
  FAILURE-CAPTURE FC-K3 asks for;
* M0-LAUNCH.json: the exact launch of observe (and of the Director's static run before it),
  with cwd, environment, capture paths, expected starts and outputs, and preconditions.

The launch record deliberately carries no plan digest: the Director supplies --plan-sha256
from the review record of observation plan 001 (MR-PLAN stage S4). Every path and constant
comes from the plan file and the observer's own helpers, so nothing is retyped. It starts no
process.

Usage (framework interpreter, -I -S -B):

    w2p_launch_record.py --observer OBS --plan PLAN --static-stdout S --static-stderr E
                         --static-exit X --mh-host HOST --environment-output ENV --output OUT
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sys

PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn",
                            "os.fork", "os.forkpty", "pty.spawn", "os.startfile"))
LIBC_STARTS = re.compile(r"_?(fork|vfork|execv?[elp]*|posix_spawnp?|system|popen)")
REFUSED_EVENTS = []


def _audit(event, args):
    if event in PROCESS_EVENTS:
        REFUSED_EVENTS.append(event)
        raise RuntimeError("Process creation refused by the W2 audit hook: " + event)
    if event == "ctypes.dlsym" and len(args) > 1 and isinstance(args[1], str) and LIBC_STARTS.fullmatch(args[1]):
        REFUSED_EVENTS.append(event + ":" + args[1])
        raise RuntimeError("ctypes lookup of a process-creation function refused: " + args[1])


sys.addaudithook(_audit)


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _file(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    info = os.lstat(path)
    return raw, {"path": path, "sha256": _sha256(raw), "size_bytes": len(raw), "mode": "0o%03o" % (info.st_mode & 0o7777)}


def _exclusive(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    return _file(path)[1]


def load_observer(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("w2p_bound_observer_v02", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    if not (sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode):
        raise SystemExit("Run under -I -S -B")
    parser = argparse.ArgumentParser(allow_abbrev=False)
    for name in ("observer", "plan", "static-stdout", "static-stderr", "static-exit", "mh-host", "environment-output",
                 "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    for path in (args.output, args.environment_output):
        if os.path.lexists(path):
            raise SystemExit("Output exists: " + path)
    ob = load_observer(args.observer)
    plan_raw, plan_file = _file(args.plan)
    plan = ob._decode(plan_raw, "PLAN")
    ob._resolved(plan)
    ob._plan_shape(plan, ob.Host())
    validated = ob.validate_plan(args.plan, plan_file["sha256"])
    static_raw, static_stdout = _file(args.static_stdout)
    static_stderr_raw, static_stderr = _file(args.static_stderr)
    static_exit = _file(args.static_exit)[0].decode("ascii").strip()
    static = json.loads(static_raw)
    if not (static_exit == "0" and static_stderr_raw == b"" and static["state"] == "STATIC_READY"
            and static["mode"] == "static" and static["plan"] == validated.descriptor
            and static["starts"] == {"node": {"exact": 0, "observed_lower_bound": 0},
                                     "other": {"exact": 0, "observed_lower_bound": 0}}):
        raise SystemExit("The retained static result is not STATIC_READY for this plan")
    mh_host_raw, mh_host_file = _file(args.mh_host)
    mh_host = json.loads(mh_host_raw)

    environment = dict(plan["environment"])
    environment_raw = ob._canonical(environment)
    environment_file = _exclusive(args.environment_output, environment_raw)
    evidence = plan["evidence"]
    parent, attempt = evidence["parent"], evidence["attempt"]
    name = os.path.basename(attempt)
    root = plan["source"]["root"]
    venv_python = plan["python"]["venv"] + "/bin/python"
    observer = plan["observer"]["path"]
    env_words = ["%s=%s" % (key, environment[key]) for key in ("PATH", "LANG", "LC_ALL", "TZ", "UV_THREADPOOL_SIZE")]
    if set(environment) != {"PATH", "LANG", "LC_ALL", "TZ", "UV_THREADPOOL_SIZE"}:
        raise SystemExit("Unexpected declared environment")

    def launch(subcommand):
        process = [venv_python, "-I", "-S", "-B", observer, subcommand, "--plan", args.plan, "--plan-sha256"]
        capture = {key: parent + "/" + name + "." + subcommand + "." + key + ".txt" for key in ("stdout", "stderr", "exit")}
        for word in process + list(capture.values()) + [parent]:
            if not re.fullmatch(r"[A-Za-z0-9_./=:@+-]+", word):
                raise SystemExit("A word would need shell quoting: " + word)
        shell = ("cd " + parent + " && /usr/bin/env -i " + " ".join(env_words) + " " + " ".join(process)
                 + ' "$PLAN_SHA256" > ' + capture["stdout"] + " 2> " + capture["stderr"] + "; echo $? > "
                 + capture["exit"])
        return {"argv_without_digest": ["/usr/bin/env", "-i"] + env_words + process,
                "observer_process_argv_without_digest": process,
                "digest_argument": ("exactly one further argv element after --plan-sha256: the plan's 64-character "
                                    "lowercase SHA-256 as the review record of observation plan 001 states it"),
                "cwd": parent, "environment": environment,
                "capture": {"stdout": capture["stdout"], "stderr": capture["stderr"], "exit_status": capture["exit"]},
                "shell_form": shell,
                "shell_form_variable": ("PLAN_SHA256 is set by the Director, in the same shell immediately before this "
                                        "line, to the review record's digest. That shell expands it into the final "
                                        "argument; env -i passes no variable of that name to the observer.")}

    observe = launch("observe")
    static_launch = launch("static")
    commands = []
    for order, command in enumerate(plan["commands"], 1):
        commands.append({**command, "order": order,
                         "through": "prototypes/static_tray_v01/supervisor_darwin_v01.py run_process"})
    outputs = evidence["outputs"]
    files = [outputs[key] for key in ("reserved", "preflight", "host", "result", "completion")]
    for command_id in ob.COMMAND_IDS:
        row = outputs[command_id]
        files += [row[key] for key in ("intent", "started", "stdout", "stderr", "process", "inspection", "postflight")]
    absent_on_success = [outputs["failure"]] + [outputs[command_id]["failure"] for command_id in ob.COMMAND_IDS]
    mh_git_line = mh_host["git"]["version"]
    record = {
        "schema": "ontokin.c271.p36-m0-launch/1",
        "purpose": ("The exact launch of the Director's single observe start (MR-PLAN stage S5) under observation "
                    "plan 001, written by W2 at stage S4, and of the Director's static run immediately before it. "
                    "It describes; it approves nothing. It deliberately carries no plan digest: the Director "
                    "supplies --plan-sha256 from the review record of plan 001, never from this file, the "
                    "author's notes, SHA256SUMS.txt or the plan (MR-PLAN section 2, S4; PHASE A4)."),
        "plan": {"path": args.plan, "size_bytes": plan_file["size_bytes"], "mode": plan_file["mode"],
                 "digest": "not recorded here; taken from the review record by the Director"},
        "observe": {**observe,
                    "capture_rule": ("FAILURE-CAPTURE FC-K2: stdout, stderr and the exit status go into fresh files "
                                     "beside the attempt, never inside it, each absent before the start. A "
                                     "redirect into the attempt would create it first, and the observer would "
                                     "refuse (EVIDENCE-FRESH)."),
                    "retry": "none (FAILURE-CAPTURE section 5; MR-PLAN section 9)"},
        "static_before_observe": {**static_launch,
                                  "purpose": ("The Director's own static run immediately before observe (MH's "
                                              "PR-05): zero starts and zero writes; it detects any change of a "
                                              "bound input since S4 before the counted starts."),
                                  "expected": {"exit_status": 0, "state": "STATIC_READY", "stderr": "empty",
                                               "starts": static["starts"],
                                               "facts_sha256_if_nothing_changed": static["facts_sha256"]}},
        "environment_file": {**environment_file,
                             "content": "the canonical JSON of the declared environment, no trailing newline",
                             "canonical_sha256": _sha256(environment_raw)},
        "fc_k3": ("Each of the two runs gets a command record beside the attempt, never inside it: the exact argv "
                  "with the digest, the cwd, environment_file above by path and SHA-256, the UTC start and end, "
                  "the wall time and kern.bootsessionuuid before and after. Suggested paths: "
                  + parent + "/" + name + ".static.command-record.json and " + parent + "/" + name
                  + ".observe.command-record.json."),
        "expected_starts": {
            "bounded": commands, "totals": {"node": 1, "other": 1},
            "director_launcher": ("one start of the framework interpreter for observe, and one for static before "
                                  "it, both through " + venv_python + " with -I -S -B; MR-PLAN section 8 does not "
                                  "count them as bounded starts, and they are recorded"),
            "never_started": ["ldd", "codesign", "otool", "the /usr/bin/git dispatcher", "any Git other than the bound "
                              "file", "any Node other than the planned bin/node", "a second observe under this plan"],
            "order_of_work": ("plan digest, plan shape, environment, platform and boot, OS identity, source inventory "
                              "and HEAD, launcher and Python inventory, packages, loaded modules, runtime (Node's "
                              "bytes and Mach-O), reader tree, Git binding, failure capture, evidence ancestors and "
                              "absent attempt; then the supervisor import, the loaded-module check, the attempt "
                              "directories, Git --version, and Node --version last (W3-OBSERVER section 7)")},
        "predicted_stdout": {"git_version": mh_git_line + "\n", "node_version": ob.NODE_VERSION_STDOUT.decode("ascii")},
        "prediction_basis": {
            "git_version": ("not a predicate: the plan freezes only the grammar " + ob.GIT_STDOUT_PREDICATE + ". MH's "
                            "M0 recorded this line for the same bound Git bytes (" + mh_host["git"]["sha256"]
                            + ") in its HOST, " + mh_host_file["path"] + ", SHA-256 " + mh_host_file["sha256"]
                            + "; N34-M predicted it statically from the arm64 slice."),
            "node_version": "the plan's literal predicate",
            "stderr": "both expect an empty stderr (stderr_predicate empty); MH's M0 observed both empty"},
        "expected_outputs": {
            "success": {"exit_status": 0, "attempt": attempt,
                        "directories": [attempt] + [outputs[command_id]["stage"] for command_id in ob.COMMAND_IDS],
                        "directory_mode": "0o700", "files": files, "files_absent_on_success": absent_on_success,
                        "observer_document_mode": "0o600 (the supervisor writes its own three files per command)",
                        "stderr": "empty",
                        "stdout": ("one line: the canonical result, schema " + ob.RESULT_SCHEMA + ", mode observe, "
                                   "state OBSERVED_UNAPPROVED, evidence_finalized true, starts node exact 1 and "
                                   "other exact 1, with the descriptors of HOST, the result and the completion"),
                        "host": {"path": outputs["host"], "schema": ob.HOST_SCHEMA, "state": "OBSERVED_UNAPPROVED",
                                 "next": "an independent HOST review before any configuration binds it (MR-PLAN S5)"}},
            "refusal_or_failure": {
                "exit_status": 1,
                "stderr": ("one line: " + ob.REFUSAL_SCHEMA + " with error {code, reason, state, cause, details}; "
                           "names of environment variables only, never their values"),
                "files": ("before the attempt directory exists, none; after it exists, whatever the observer "
                          "published, with failure.json and result.json when it could write them, and each "
                          "attempted command's failure.json and postflight.json"),
                "then": "FAILURE-CAPTURE sections 3 to 8 and MR-PLAN section 9; no retry"}},
        "preconditions_for_the_director": [
            "HEAD of the worktree is commit " + plan["source"]["commit"] + " (tree " + plan["source"]["tree"]
            + "), clean apart from the ignored .venv, and nothing has been committed, checked out or edited",
            "kern.bootsessionuuid is " + plan["platform"]["boot_session_uuid"] + " (a reboot ends this plan)",
            "the attempt " + attempt + " and the six capture paths above are absent; the evidence parent's own "
            "device, inode and mode are unchanged",
            "nothing has started the framework interpreter without -B (or without PYTHONDONTWRITEBYTECODE=1) since "
            "the inventories were frozen",
            "MP's plans and receipts, the Node archive, the runtime, the reader tree and FAILURE-CAPTURE.md are "
            "unchanged at their paths and modes; nothing is chmod-ed",
            "the volume that holds the worktree, the prepared trees and the evidence stays mounted (its device "
            "number is bound through the evidence ancestors), the host stays awake, and Finder is not used on any "
            "bound tree",
            "the digest on the command line is the review record's, and the plan file's own SHA-256 equals it"],
        "author_static": {"exit_status": 0, "state": static["state"], "facts_sha256": static["facts_sha256"],
                          "starts": static["starts"], "stdout": static_stdout, "stderr": static_stderr,
                          "cwd": parent, "launched": "as static_before_observe, with W2's records as capture paths"},
        "written_by": {"script": os.path.realpath(__file__), "script_sha256": _file(os.path.realpath(__file__))[1]["sha256"],
                       "pid": os.getpid(), "at_utc": datetime.now(timezone.utc).isoformat()},
        "refused_process_events": REFUSED_EVENTS}
    raw = json.dumps(record, indent=1, sort_keys=True, ensure_ascii=True).encode("ascii") + b"\n"
    if plan_file["sha256"] in raw.decode("ascii"):
        raise SystemExit("The launch record must not carry the plan digest")
    written = _exclusive(args.output, raw)
    sys.stdout.write(json.dumps({"output": written, "environment": environment_file, "pid": os.getpid()},
                                sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
