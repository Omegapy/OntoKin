"""W2, observation plan 001 (gate MH, C271-P35): write M0-LAUNCH.json for the Director's single observe.

Every value comes from the plan, after its bytes are checked against the digest
given on the command line, from the observer's own constants (loaded by path),
and from the retained static result. No process is created (an audit hook
refuses every process-creation event). One absent output is created exclusively.

Launch: <worktree>/.venv/bin/python -I -S -B w2_launch_record.py --plan P --plan-sha256 H
        --static-stdout S --static-stderr E --static-exit X --capture-prefix C
        --predicted-git-line TEXT --output O
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys

REFUSED_EVENTS = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork",
                            "os.forkpty", "os.startfile", "pty.spawn"))


def _hook(event, args):
    if event in REFUSED_EVENTS:
        raise RuntimeError("process creation refused by the W2 audit hook: " + event)


sys.addaudithook(_hook)


def descriptor(path):
    data = open(path, "rb").read()
    info = os.lstat(path)
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "mode": "0o%03o" % (info.st_mode & 0o7777)}


def main(argv):
    parser = argparse.ArgumentParser(prog="w2_launch_record")
    for name in ("plan", "plan-sha256", "static-stdout", "static-stderr", "static-exit", "capture-prefix",
                 "predicted-git-line", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    assert sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.flags.dont_write_bytecode == 1, "-I -S -B"
    assert not os.path.lexists(args.output), "the output exists"
    raw = open(args.plan, "rb").read()
    assert hashlib.sha256(raw).hexdigest() == args.plan_sha256, "the plan differs from the supplied digest"
    plan = json.loads(raw)
    root = plan["source"]["root"]
    spec = importlib.util.spec_from_file_location("current_host_observation_v02", plan["observer"]["path"])
    obs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obs)
    assert obs._canonical(plan) == raw, "the plan is not canonical"
    assert plan["commands"] == obs.expected_commands(plan)
    assert plan["evidence"]["outputs"] == obs.output_paths(plan["evidence"]["attempt"])
    assert plan["environment"] == dict(obs.ENVIRONMENT)
    static_raw = open(args.static_stdout, "rb").read()
    static = json.loads(static_raw)
    assert static["state"] == "STATIC_READY" and static["plan"] == {"path": args.plan, **{
        k: v for k, v in descriptor(args.plan).items() if k != "path"}}, "the static result is not this plan's"
    assert open(args.static_exit).read().strip() == "0" and open(args.static_stderr, "rb").read() == b""
    venv_python = plan["python"]["venv"] + "/bin/python"
    observer = plan["observer"]["path"]
    environment = plan["environment"]
    process_argv = [venv_python, "-I", "-S", "-B", observer, "observe", "--plan", args.plan,
                    "--plan-sha256", args.plan_sha256]
    env_argv = ["/usr/bin/env", "-i"] + ["%s=%s" % (key, environment[key]) for key in
                                         ("PATH", "LANG", "LC_ALL", "TZ", "UV_THREADPOOL_SIZE")]
    cwd = plan["evidence"]["parent"]
    capture = {"stdout": args.capture_prefix + ".stdout.txt", "stderr": args.capture_prefix + ".stderr.txt",
               "exit_status": args.capture_prefix + ".exit.txt"}
    for path in capture.values():
        assert os.path.dirname(path) == cwd and not os.path.lexists(path), "capture paths must be absent siblings"
        assert not path.startswith(plan["evidence"]["attempt"] + "/") and path != plan["evidence"]["attempt"]
    shell = ("cd " + cwd + " && " + " ".join(env_argv + process_argv) + " > " + capture["stdout"] + " 2> "
             + capture["stderr"] + "; echo $? > " + capture["exit_status"])
    outputs = plan["evidence"]["outputs"]
    attempt = plan["evidence"]["attempt"]
    success_files = [outputs[key] for key in ("reserved", "preflight", "host", "result", "completion")]
    for command in ("git_version", "node_version"):
        success_files += [outputs[command][key] for key in ("intent", "started", "stdout", "stderr", "process",
                                                             "inspection", "postflight")]
    record = {
        "schema": "ontokin.c271.p35-m0-launch/1",
        "purpose": ("The exact command of the Director's single observe start (MH-PLAN stage S5) under observation "
                    "plan 001, written by W2 at stage S4. It is a description for the Director and the reviewer; "
                    "it approves nothing. The plan's digest is taken from the review record of plan 001, never from "
                    "this file or from the plan (MH-PLAN section 2, S4)."),
        "plan": descriptor(args.plan),
        "static": {"state": static["state"], "exit_status": 0, "stderr": "empty",
                   "facts_sha256": static["facts_sha256"], "starts": static["starts"],
                   "stdout": descriptor(args.static_stdout),
                   "launched": "exactly as below, with static in place of observe, from the same cwd and environment"},
        "command": {
            "argv": env_argv + process_argv,
            "observer_process_argv": process_argv,
            "note_on_argv": ("/usr/bin/env -i clears the inherited environment and executes the .venv's python with "
                             "exactly the declared environment; env is replaced by the interpreter in the same "
                             "process. The framework launcher then executes its Python.app image, as on every start "
                             "of this interpreter; the observer checks sys.executable, the launcher and the process "
                             "image (W3-OBSERVER section 1; check_launcher)."),
            "cwd": cwd,
            "environment": environment,
            "environment_canonical_sha256": hashlib.sha256(obs._canonical(environment)).hexdigest(),
            "environment_note": ("No other variable. macOS may add __CF_USER_TEXT_ENCODING when CoreFoundation loads "
                                 "(contract S10); the observer admits it and records its value in HOST. -B is on the "
                                 "command line because the environment admits no Python variable (MH-PLAN N-09)."),
            "umask_observed_at_s4": "0o022",
            "shell_form": shell,
            "capture": capture,
            "capture_rule": ("FAILURE-CAPTURE FC-K2: stdout, stderr and the exit status go into fresh files beside "
                             "the attempt, never inside it; each must be absent before the start. A redirect into the "
                             "attempt would create it first and the observer would refuse (EVIDENCE-FRESH)."),
            "retry": "none (FAILURE-CAPTURE section 5; MH-PLAN section 8)"},
        "expected_starts": {
            "director_launcher": ("one start of the .venv interpreter (the observer process). MH-PLAN section 7 does "
                                  "not count it as a bounded start; it is recorded."),
            "bounded": [dict(order=index + 1, through="prototypes/static_tray_v01/supervisor_darwin_v01.py run_process",
                             **command) for index, command in enumerate(plan["commands"])],
            "totals": {"node": 1, "other": 1},
            "order_of_work": ("plan digest, plan shape, environment, platform and boot, OS identity, source inventory "
                              "and HEAD, launcher and Python inventory, packages, loaded modules, runtime (Node's "
                              "bytes and Mach-O), reader tree, Git binding, failure capture, evidence ancestors and "
                              "absent attempt; then the supervisor import, the attempt directories, Git --version, "
                              "and Node --version last (W3-OBSERVER section 7)"),
            "predicted_stdout": {"git_version": args.predicted_git_line + "\n", "node_version": "v24.22.1\n"},
            "prediction_basis": ("Git: the version text embedded in the bound file's arm64 slice, read statically by "
                                 "N34-M (review section 2.9); the plan freezes only the grammar git-version-line-v1, "
                                 "so the line is a prediction for the HOST review (N-07), not a predicate. Node: the "
                                 "plan's literal predicate v24.22.1 and a newline. Both expect an empty stderr."),
            "never_started": ["ldd", "codesign", "otool", "the /usr/bin/git dispatcher", "a second observe",
                              "any Git other than the bound file"]},
        "expected_outputs": {
            "success": {
                "exit_status": 0,
                "stdout": ("one line: the canonical JSON result, schema " + obs.RESULT_SCHEMA + ", mode observe, "
                           "state OBSERVED_UNAPPROVED, evidence_finalized true, starts node exact 1 and other exact 1, "
                           "with the descriptors of HOST, the result and the completion"),
                "stderr": "empty",
                "attempt": attempt,
                "directories": [attempt, outputs["git_version"]["stage"], outputs["node_version"]["stage"]],
                "directory_mode": "0o700",
                "files": success_files,
                "files_absent_on_success": [outputs["failure"], outputs["git_version"]["failure"],
                                            outputs["node_version"]["failure"]],
                "observer_document_mode": "0o600 (the supervisor writes its own three files per command)",
                "host": {"path": outputs["host"], "schema": obs.HOST_SCHEMA, "state": "OBSERVED_UNAPPROVED",
                         "next": "an independent HOST review before any configuration binds it (MH-PLAN S5)"}},
            "refusal_or_failure": {
                "exit_status": 1,
                "stderr": ("one line: " + obs.REFUSAL_SCHEMA + " with error {code, reason, state, cause, details}; "
                           "names of environment variables only, never their values"),
                "files": ("before any attempt directory exists, none; after it exists, whatever the observer "
                          "published, with failure.json and result.json when it could write them, and each "
                          "command's failure.json and postflight.json for an attempted command"),
                "then": "FAILURE-CAPTURE sections 3 to 8, and MH-PLAN section 8; no retry"},
            "all_planned_paths": outputs},
        "preconditions_for_the_director": [
            "HEAD of the worktree is commit " + plan["source"]["commit"] + " (tree " + plan["source"]["tree"]
            + "), clean apart from the ignored .venv",
            "kern.bootsessionuuid is " + plan["platform"]["boot_session_uuid"] + " (a reboot ends this plan)",
            "the attempt " + attempt + " and the three capture paths are absent",
            "nothing has started the framework interpreter without -B since the inventories were frozen",
            "the plan's digest supplied on the command line comes from the review record"],
        "written_by": {"script": os.path.realpath(__file__),
                       "script_sha256": hashlib.sha256(open(os.path.realpath(__file__), "rb").read()).hexdigest(),
                       "pid": os.getpid()}}
    data = (json.dumps(record, sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    sys.stdout.write(json.dumps({"output": args.output, "sha256": hashlib.sha256(data).hexdigest(),
                                 "size_bytes": len(data)}, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
