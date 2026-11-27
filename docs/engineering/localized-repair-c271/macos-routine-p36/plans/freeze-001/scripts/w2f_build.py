"""W2 (freeze 001, C271-P36, gate MR, stage S6): build operational freeze 001 for R1 and R2.

Usage: python3 -I -S -B w2f_build.py OUT_DIR

It writes OUT_DIR/env/{r1,r2,tools,path}.environment.json and OUT_DIR/FREEZE-001.json, each by exclusive
creation. Every binding's SHA-256, size and mode is computed here from the file's bytes; nothing is copied
from another record except the values that this script names as taken from a review record (HOST's digest,
the wrapper's, the plan's) and asserts against the bytes. The configuration's own digest is not written
into the freeze (A6): R1's argv carries the placeholder <readback-config-001.json SHA-256>.

The checker is MH's reviewed S7 checker, unchanged, at its committed path at B
(macos-qualification-p35/plans/freeze-001/s7/w2f_s7_check.py, eb96aa1a...); this freeze uses its keys:
boot_session_uuid, umask, bindings, trees, host_facts, evidence, absent_paths, deferred_inputs, preparation,
post and commands (expect, audit_expect). It starts no process.
"""
import hashlib
import json
import os
import pwd
import stat
import sys

if not sys.flags.dont_write_bytecode:
    sys.stderr.write("refused: run with -B\n")
    raise SystemExit(2)
OUT = sys.argv[1]

# ---------------------------------------------------------------------------------------------------------
# Places
# ---------------------------------------------------------------------------------------------------------
W = "<worktree>"
L = "<local>"
E = L + "/c271-p36/evidence"
F = L + "/c271-p36/workers/W2-freeze-001"
WRAP = L + "/c271-p36/director/run/run_once_p36.sh"
PY = W + "/.venv/bin/python"
FW = "<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12"
ENG = W + "/docs/engineering/localized-repair-c271"
MRT = ENG + "/macos-routine-p36/tooling"
MHT = ENG + "/macos-qualification-p35/tooling"
CHECKER = ENG + "/macos-qualification-p35/plans/freeze-001/s7/w2f_s7_check.py"
OBSERVER = W + "/prototypes/static_tray_v01/current_host_observation_v02.py"
COLLECT = MRT + "/unit_log_outcomes.py"
READER = MRT + "/readback_evidence.py"
AUDIT = MHT + "/audit_numeric.py"
PROBE = MHT + "/capture_probe.py"
A1 = E + "/mr-001-r1"
R1OUT = A1 + "/driver"
R2OUT = E + "/mr-001-r2"
CONFIG = F + "/config/readback-config-001.json"
DISCOVERY = F + "/discovery/discovery-b-001.json"
DISCOVERY_COMPARE = F + "/discovery/discovery-b-compare-001.json"
ATTR1 = F + "/attributions/r1-attributions-001.json"
ATTR2 = F + "/attributions/r2-attributions-001.json"
CHECKS = L + "/checks"
MAIN_RES = CHECKS + "/main-8e847c15-tmpdir-20261125T2110Z"
MAIN_DEF = CHECKS + "/main-8e847c15-default-20261125T2110Z"
TMP_RESOLVED = "<tmpdir>/"
TMP_DEFAULT = "<tmpdir-link>/"
HOME = os.environ["HOME"]
USER = os.environ["USER"]
LOGNAME = os.environ["LOGNAME"]
entry = pwd.getpwuid(os.getuid())
assert entry.pw_dir == HOME and entry.pw_name == USER == LOGNAME, "HOME, USER and LOGNAME are this host's account values"
BOOT = "C90010BA-4DA9-475D-BBAB-CF1A9C40175A"
B = "4ca781429c5411c67c0965bc69306b42c6cc74ad"
TREE = "0935162c72fd9d804681e920da6f6d6e9066ff28"
GIT = "/Library/Developer/CommandLineTools/usr/bin/git"
GIT_SHA = "be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae"
DISPATCHER_SHA = "b8763cf250e607a778bb4603cecb5b90338814d0a3dfcba0d57b1de242f610e9"
PY_INVENTORY_SHA = "c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633"
SRC_INVENTORY_SHA = "95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c"
DRIVER_INVENTORY = "sha256:e7f1c4b53f23163b20355a863ebe73ec386a1c661a23643d2a8a2b838258f249"
DRIVER_FILE_COUNT = 23005
PYTHON_BUILD = "3.12.13 (main, Mar  3 2026, 12:39:30) [Clang 17.0.0 (clang-1700.6.3.2)]"
PLATFORM = "macOS-26.6.2-arm64-arm-64bit"
TIMEOUT = 7200
STEPS = ["unit-tests", "source", "agent", "construction", "surface", "impulse", "documents"]
FREEZE_PATH = F + "/FREEZE-001.json"
FREEZE_DIGEST = "<FREEZE-001.json SHA-256>"
CONFIG_DIGEST = "<readback-config-001.json SHA-256>"
COHORT = "<R1 cohort root>"
OVERRUN_COHORT = "<R1 overrun cohort root>"
R1_SUMMARY_DIGEST, R1_LOG_DIGEST = "<R1 summary SHA-256>", "<R1 unit log SHA-256>"
R1_AUDIT_DIGEST = "<R1 audit SHA-256>"
R2_SUMMARY_DIGEST, R2_LOG_DIGEST = "<R2 summary SHA-256>", "<R2 unit log SHA-256>"
AUDIT_TOOL_SHA = "9140379c61bc70f29939bd7b216ef5ca5e2f5e6cab5b4a452e50018651bac4e3"
PROBE_TOOL_SHA = "db5fb5250909effa7e3fe3d66feadc5183160b4e6088178a763e6fc41567048f"
CASES = ["Q01-positive", "Q03-positive", "Q01-changed-reference"]
METHODS = ["test_static_tray_readback_v01.ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries",
           "test_static_tray_readback_v01.ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries",
           "test_static_tray_readback_v01.ReadbackCPUControls.test_three_rejects_changed_synthetic_reference",
           "test_static_tray_readback_v01.ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup",
           "test_static_tray_readback_v01.ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked",
           "test_static_tray_readback_v01.ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm",
           "test_static_tray_readback_v01.ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending"]
TRIO, SEAMS = METHODS[:3], METHODS[3:]
FIXTURE_IDS = ["setUpClass (test_static_tray_readback_v01.ReadbackCPUControls)",
               "tearDownClass (test_static_tray_readback_v01.ReadbackCPUControls)",
               "setUpClass (test_static_tray_readback_v01.ReadbackCoordinatorSeams)",
               "tearDownClass (test_static_tray_readback_v01.ReadbackCoordinatorSeams)",
               "setUpModule (test_static_tray_readback_v01)",
               "tearDownModule (test_static_tray_readback_v01)"]
MC22_FIXTURE = FIXTURE_IDS[0]
ORDINARY_REASON = ("prototypes.static_tray_v01.current_host_readback_v01.CurrentHostBindingError: "
                   "No approved current-host readback selection: ordinary run, not a qualification")
FORCE_CONTRACT = "test_force_contract.ForceContractReviewTests.test_original_corpus_and_author_remain_byte_identical"
D18 = ["test_current_host_readback_driver.CurrentHostDriverBindingTests.test_failed_prelaunch_is_recorded_unexecuted_even_if_later_inventory_fails",
       "test_current_host_readback_driver.CurrentHostDriverBindingTests.test_missing_explicit_selection_cannot_use_ambient_approval"]
DECLARED = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PATH": "/usr/bin:/bin", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}


def sha256_file(path):
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
    finally:
        os.close(fd)
    return digest.hexdigest()


def file_row(ident, path, role, *, nlink_one=True):
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), path
    if nlink_one:
        assert info.st_nlink == 1, path
    return {"id": ident, "path": path, "kind": "file", "sha256": sha256_file(path), "size_bytes": info.st_size,
            "mode": "0o%03o" % stat.S_IMODE(info.st_mode), "nlink_one": nlink_one, "role": role}


def write_new(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


# ---------------------------------------------------------------------------------------------------------
# Environments (D-P1, D-P2)
# ---------------------------------------------------------------------------------------------------------
def environment_document(values):
    return (json.dumps({"schema": "ontokin.c271.p35-unit-environment/1", "environment": values}, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("ascii")


R1_ENV = {"HOME": HOME, "LOGNAME": LOGNAME, "PATH": "/usr/bin:/bin", "TMPDIR": TMP_RESOLVED, "USER": USER}
R2_ENV = {"HOME": HOME, "LOGNAME": LOGNAME, "PATH": "/usr/bin:/bin", "TMPDIR": TMP_DEFAULT, "USER": USER}
ENVIRONMENTS = {"r1": R1_ENV, "r2": R2_ENV, "tools": DECLARED, "path": {"PATH": "/usr/bin:/bin"}}
os.makedirs(OUT + "/env", exist_ok=True)
env_files = {}
for name, values in ENVIRONMENTS.items():
    path = OUT + "/env/" + name + ".environment.json"
    write_new(path, environment_document(values))
    env_files[name] = {"file": path, "sha256": sha256_file(path), "names": sorted(values)}
for name, values in ENVIRONMENTS.items():
    assert not any(key.startswith(("PYTHON", "PIP_", "GIT_", "NODE_", "DYLD_")) for key in values), name


def env_argv(name):
    return ["/usr/bin/env", "-i"] + [key + "=" + value for key, value in sorted(ENVIRONMENTS[name].items())]


# ---------------------------------------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------------------------------------
TIMER = ("f='{exit_file}'; b={bound}; s=$(/bin/date +%s); case $s in ''|*[!0-9]*) printf 'bound-timer: no-clock file=%s\\n' "
         "\"$f\"; exit 2;; esac; while :; do if [ -e \"$f\" ]; then printf 'bound-timer: exit-file began=%s now=%s bound_s=%s "
         "file=%s\\n' \"$s\" \"$(/bin/date +%s)\" \"$b\" \"$f\"; exit 0; fi; n=$(/bin/date +%s); case $n in ''|*[!0-9]*) printf "
         "'bound-timer: no-clock file=%s\\n' \"$f\"; exit 2;; esac; if [ \"$n\" -gt \"$((s + b))\" ]; then printf 'bound-timer: "
         "outer-bound began=%s now=%s bound_s=%s file=%s\\n' \"$s\" \"$n\" \"$b\" \"$f\"; exit 1; fi; /bin/sleep 1; done")
COMMANDS = []


def quote(item):
    assert "'" not in item and "\n" not in item, item
    return "'" + item + "'"


def records(name):
    return {"stdout": E + "/" + name + ".stdout.txt", "stderr": E + "/" + name + ".stderr.txt",
            "exit": E + "/" + name + ".exit.txt", "command": E + "/" + name + ".command.json"}


def command(ident, name, phase, purpose, cwd, env, argv, *, outputs=(), deferred=(), exits=(0,), expected_wall_s=10,
            outer_bound_s=600, starts=None, classification=None, expect_extra=(), audit_expect=(), failure_capture=None,
            note=None):
    rec = records(name)
    wrapper = ["/bin/sh", WRAP, name, cwd, env_files[env]["file"], "--", *argv]
    shell = " ".join(quote(item) for item in wrapper)
    indices = []
    deferred_rows = []
    for placeholder, source, predicate in deferred:
        found = [i for i, item in enumerate(argv) if placeholder in item]
        assert found, (ident, placeholder)
        for index in found:
            indices.append(index)
            deferred_rows.append({"placeholder": placeholder, "argv_index": index, "source": source})
    expect = [{"file": rec["command"], "pointer": "/argv", "argv_equals_except": {"argv": list(argv), "indices": sorted(set(indices))}},
              {"file": rec["command"], "pointer": "/schema", "equals": "ontokin.c271.p36-command-record/1"},
              {"file": rec["command"], "pointer": "/name", "equals": name},
              {"file": rec["command"], "pointer": "/cwd", "equals": cwd},
              {"file": rec["command"], "pointer": "/environment/file", "equals": env_files[env]["file"]},
              {"file": rec["command"], "pointer": "/environment/sha256", "equals": env_files[env]["sha256"]},
              {"file": rec["command"], "pointer": "/boot/before", "equals": BOOT},
              {"file": rec["command"], "pointer": "/boot/after", "equals": BOOT},
              {"file": rec["command"], "pointer": "/retries", "equals": 0},
              {"file": rec["command"], "pointer": "/written_by", "equals": "director/run/run_once_p36.sh"},
              {"file": rec["command"], "pointer": "/exit/status", "one_of": list(exits)},
              {"file": rec["exit"], "exists": True}]
    for placeholder, source, predicate in deferred:
        for index in [i for i, item in enumerate(argv) if placeholder in item]:
            for rule in predicate:
                expect.append({"file": rec["command"], "pointer": "/argv/%d" % index, **rule})
    expect.extend(expect_extra)
    row = {"id": ident, "name": name, "phase": phase, "purpose": purpose, "cwd": cwd,
           "environment": {"name": env, **{k: env_files[env][k] for k in ("file", "sha256")}},
           "argv": list(argv), "wrapper_argv": wrapper, "shell": shell,
           "timer_shell": TIMER.replace("{exit_file}", rec["exit"]).replace("{bound}", str(outer_bound_s)),
           "records": rec, "outputs": list(outputs), "outputs_absent_before": sorted(set(list(rec.values()) + list(outputs))),
           "deferred_arguments": deferred_rows, "allowed_exit_statuses": list(exits),
           "limits": {"expected_wall_s": expected_wall_s, "outer_bound_s": outer_bound_s},
           "starts": starts or {"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"framework_interpreter": 1}},
           "expect": expect, "audit_expect": list(audit_expect),
           "classification": classification or [], "failure_capture": failure_capture or {"listing": None, "probe": None}}
    if note:
        row["note"] = note
    COMMANDS.append(row)
    return row


def tool(*arguments):
    return env_argv("tools") + [PY, "-I", "-S", "-B", *arguments]


def checker(phase, *extra):
    return tool(CHECKER, "--freeze", FREEZE_PATH, "--freeze-sha256", FREEZE_DIGEST, phase, *extra)


FREEZE_DEFERRED = (FREEZE_DIGEST, "FREEZE-REVIEW-001.json /freeze/sha256, as the reviewer computed it from the bytes of "
                   "FREEZE-001.json; 64 lowercase hexadecimal characters", [{"equals_freeze_sha256": True}])


def checker_command(ident, name, phase, purpose, args, *, exits=(0, 1), classification=None, outer_bound_s=600):
    return command(ident, name, phase, purpose, E, "tools", checker(*args), deferred=[FREEZE_DEFERRED], exits=exits,
                   expected_wall_s=20, outer_bound_s=outer_bound_s,
                   classification=classification or [
                       {"outcome": "exit 0, state MET", "class": "continue with the next command"},
                       {"outcome": "exit 1, state NOT_MET", "class": "stop_rules rule 2 (P01, D02) or rule 4 (R1.X, R1.Z, R2.X) "
                        "decides; FAILURE-CAPTURE section 6"},
                       {"outcome": "exit 2 (refusal: usage, -I -S -B, or the freeze's digest)", "class": "PLAN; stop S7"}],
                   expect_extra=[{"file": records(name)["stdout"], "pointer": "/state", "equals": "MET"},
                                 {"file": records(name)["stdout"], "pointer": "/schema", "equals": "ontokin.c271.p35-s7-check/1"},
                                 {"file": records(name)["stdout"], "pointer": "/python_flags/dont_write_bytecode", "equals": 1}])


def out(name):
    return E + "/" + name


def json_file(path, pointer, **rule):
    return {"file": path, "pointer": pointer, **rule}


def tool_identity(path, sha):
    return [json_file(path, "/tool/sha256", equals=sha)]


def digest_deferred(placeholder, path):
    return (placeholder, "/usr/bin/shasum -a 256 '" + path + "' | /usr/bin/cut -c1-64, run by the Director immediately "
            "before this command's launch; 64 lowercase hexadecimal characters", [{"equals_sha256_of": path}])


COHORT_DEFERRED = (COHORT, "the value of /cohort_root in mr-001-r1.cohort-find.stdout.txt, read with /usr/bin/jq -r "
                   ".cohort_root; it must match ^" + A1 + "/current-host-cpu-[a-z0-9_]{8}-preserved-[0-9a-f]{32}$, and it "
                   "replaces every occurrence of the placeholder in this command",
                   [{"startswith": A1 + "/current-host-cpu-"}, {"includes": "-preserved-"}])

# P00 -------------------------------------------------------------------------------------------------------
command("P00", "mr-001-p00-sums", "precondition",
        "FR-07 (MH): every file of this freeze directory against SHA256SUMS.txt, before anything that reads the freeze",
        F, "path", env_argv("path") + ["/usr/bin/shasum", "-a", "256", "--strict", "-c", "SHA256SUMS.txt"],
        expected_wall_s=5, outer_bound_s=120,
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"shasum": 1}},
        classification=[{"outcome": "exit 0", "class": "continue with P01"},
                        {"outcome": "any other exit", "class": "a file of the freeze differs or is missing: S7 does not begin"}],
        expect_extra=[{"file": records("mr-001-p00-sums")["stdout"], "text_excludes": "FAILED"},
                      {"file": records("mr-001-p00-sums")["stdout"], "text_includes": "FREEZE-001.json: OK"},
                      {"file": records("mr-001-p00-sums")["stdout"], "text_includes": "config/readback-config-001.json: OK"},
                      {"file": records("mr-001-p00-sums")["stderr"], "text_equals": ""}],
        note="The Director reads P00's outcome from its exit file alone (MH's FR-07); D02 re-checks its predicates.")

# P01 -------------------------------------------------------------------------------------------------------
checker_command("P01", "mr-001-p01-check-pre", "precondition",
                "every binding and host fact, the boot, the umask, the evidence parent's ancestors, no bytecode or "
                ".DS_Store in the named trees, the configuration's requirements, and every S7 path absent", ["pre"])

# D01 -------------------------------------------------------------------------------------------------------
command("D01", "mr-001-d01-attempt-root", "preparation",
        "R1's attempt directory, the configuration's evidence_root: R1's driver output and the provider's cohort lie in it",
        E, "path", env_argv("path") + ["/bin/mkdir", "-m", "0755", A1], outputs=[A1], expected_wall_s=1, outer_bound_s=60,
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"mkdir": 1}},
        classification=[{"outcome": "exit 0", "class": "continue"}, {"outcome": "any other exit", "class": "PLAN; stop S7"}],
        expect_extra=[{"file": records("mr-001-d01-attempt-root")["stdout"], "text_equals": ""},
                      {"file": records("mr-001-d01-attempt-root")["stderr"], "text_equals": ""}])

# P02, P03 --------------------------------------------------------------------------------------------------
INVENTORY_CLASSES = [{"outcome": "exit 0 and the inventory's SHA-256 equals HOST's", "class": "continue"},
                     {"outcome": "exit 0 and another SHA-256", "class": "INPUT/HOST: a bound tree changed (MC32 would refuse; "
                      "HR-04); stop S7 before the next start"},
                     {"outcome": "any other exit", "class": "PLAN or HOST; stop S7"}]


def python_inventory(ident, name, phase, purpose):
    path = out(name + ".json")
    return command(ident, name, phase, purpose, E, "tools",
                   tool(OBSERVER, "python-inventory", "--venv", W + "/.venv", "--framework", FW, "--output", path),
                   outputs=[path], expected_wall_s=2, outer_bound_s=300, classification=INVENTORY_CLASSES,
                   expect_extra=[{"file": path, "sha256": PY_INVENTORY_SHA},
                                 json_file(records(name)["stdout"], "/output/sha256", equals=PY_INVENTORY_SHA),
                                 json_file(records(name)["stdout"], "/output/path", equals=path)])


def source_inventory(ident, name, phase, purpose):
    path = out(name + ".json")
    return command(ident, name, phase, purpose, E, "tools", tool(OBSERVER, "source-inventory", "--root", W, "--output", path),
                   outputs=[path], expected_wall_s=2, outer_bound_s=300, classification=INVENTORY_CLASSES,
                   expect_extra=[{"file": path, "sha256": SRC_INVENTORY_SHA},
                                 json_file(records(name)["stdout"], "/output/sha256", equals=SRC_INVENTORY_SHA)])


python_inventory("P02", "mr-001-p02-python-inventory", "preparation",
                 "D-P5 and HR-04: the Python installation inventory immediately before R1, against HOST's (the observer's "
                 "python-inventory, which starts nothing)")
source_inventory("P03", "mr-001-p03-source-inventory", "preparation",
                 "the provider's source inventory of B immediately before R1, against HOST's")

# D02 -------------------------------------------------------------------------------------------------------
checker_command("D02", "mr-001-d02-check-prepared", "preparation",
                "the last gate before R1: the bindings, host facts, boot, umask, ancestors and trees again; R1's attempt "
                "directory exists, empty, mode 0o755; every later path absent; and every predicate of P00, P01, D01, P02 "
                "and P03", ["prepared"])

# R1 --------------------------------------------------------------------------------------------------------
R1_ARGV = env_argv("r1") + [PY, "-B", "tools/check_local.py", "--timeout", str(TIMEOUT), "--output-dir", R1OUT,
                            "--readback-config", CONFIG, "--readback-config-sha256", CONFIG_DIGEST]
R2_ARGV = env_argv("r2") + [PY, "-B", "tools/check_local.py", "--timeout", str(TIMEOUT), "--output-dir", R2OUT]
S1 = R1OUT + "/summary.json"
S2 = R2OUT + "/summary.json"
LOG1 = R1OUT + "/logs/unit-tests.log"
LOG2 = R2OUT + "/logs/unit-tests.log"


def summary_common(path, output, run):
    """Stop predicates of a driver summary: the run ran as frozen and the fixed state held (both run kinds)."""
    rows = [json_file(path, "/schema_version", equals="ontokin.local-checks/0.1"),
            json_file(path, "/profile", equals="core"),
            json_file(path, "/selected_roles", equals=["core"]),
            json_file(path, "/planned_steps", equals=STEPS),
            json_file(path, "/error", absent=True),
            json_file(path, "/status", one_of=["passed", "failed"]),
            json_file(path, "/exit_code", one_of=[0, 1]),
            json_file(path, "/source_root", equals=W),
            json_file(path, "/environment/python_executable", equals=PY),
            json_file(path, "/environment/python", equals=PYTHON_BUILD),
            json_file(path, "/environment/platform", equals=PLATFORM),
            json_file(path, "/environment/architecture", equals="arm64"),
            json_file(path, "/git/available", equals=True),
            json_file(path, "/git/local_head", equals=B),
            json_file(path, "/git/local_tree", equals=TREE),
            json_file(path, "/git/tracked_worktree_status", equals=""),
            json_file(path, "/git/untracked_source_files", equals=[]),
            json_file(path, "/git_after/local_head", equals=B),
            json_file(path, "/git_after/local_tree", equals=TREE),
            json_file(path, "/git_after/tracked_worktree_status", equals=""),
            json_file(path, "/git_revision_unchanged", equals=True),
            json_file(path, "/source_unchanged", equals=True),
            json_file(path, "/source_inventory/inventory_sha256", equals=DRIVER_INVENTORY),
            json_file(path, "/source_inventory/file_count", equals=DRIVER_FILE_COUNT),
            json_file(path, "/workspace_git/local_head", equals=B),
            json_file(path, "/workspace_git/local_tree", equals=TREE),
            json_file(path, "/not_executed_steps", equals=[]),
            json_file(path, "/steps", length=7),
            json_file(path, "/steps", count_where={"pointer": "/process_started", "equals": True}, equals=7),
            json_file(path, "/steps", count_where={"pointer": "/status", "one_of": ["passed", "failed"]}, equals=7),
            json_file(path, "/steps", each={"pointer": "/cwd", "equals": output + "/workspace"}),
            json_file(path, "/steps", each={"pointer": "/argv/0", "equals": PY}),
            json_file(path, "/steps", each={"pointer": "/argv/1", "equals": "-B"})]
    for index, step in enumerate(STEPS):
        rows.append(json_file(path, "/steps/%d/id" % index, equals=step))
    rows.append(json_file(path, "/steps/0/argv", equals=[PY, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]))
    return rows


def summary_outcomes(path, tests_run):
    rows = [json_file(path, "/status", equals="failed"), json_file(path, "/exit_code", equals=1),
            json_file(path, "/steps/0/status", equals="failed"), json_file(path, "/steps/0/returncode", equals=1),
            json_file(path, "/steps/0/reason", equals=None),
            json_file(path, "/steps/0/test_execution/tests_run", equals=tests_run),
            json_file(path, "/steps/0/test_execution/skipped", equals=0),
            json_file(path, "/steps/0/test_execution/expected_failures", equals=0),
            json_file(path, "/steps/0/test_execution/executed_without_skips", equals=tests_run),
            json_file(path, "/steps/0/test_execution/complete_regression_passed", equals=False),
            json_file(path, "/steps", count_where={"pointer": "/reason", "startswith": "Exceeded"}, equals=0),
            json_file(path, "/pending_external_cases", length=16)]
    for index in range(1, 7):
        rows.append(json_file(path, "/steps/%d/status" % index, equals="passed"))
    return rows


R1_SUMMARY_STOP = summary_common(S1, R1OUT, "r1") + [
    json_file(S1, "/readback_selection/status", equals="workspace_bound"),
    json_file(S1, "/readback_selection/run_kind", equals="qualifying"),
    json_file(S1, "/readback_selection/config_path", equals=CONFIG),
    json_file(S1, "/readback_selection/expected_config_sha256", equals_sha256_of=CONFIG),
    json_file(S1, "/readback_selection/config_sha256", equals_sha256_of=CONFIG),
    json_file(S1, "/readback_selection/source_root", equals=W),
    json_file(S1, "/readback_selection/approval_source",
              equals="explicit caller argument from independently reviewed execution plan"),
    json_file(S1, "/readback_selection/derived/config_path", equals=R1OUT + "/readback-binding/selection.json"),
    json_file(S1, "/readback_selection/derived/workspace_binding_path", equals=R1OUT + "/readback-binding/workspace-binding.json"),
    json_file(S1, "/readback_selection/derived/parent_config_sha256", equals_sha256_of=CONFIG),
    json_file(S1, "/readback_selection/derived/config_sha256", equals_sha256_of=R1OUT + "/readback-binding/selection.json"),
    json_file(S1, "/readback_selection/preparation_or_execution_error", absent=True),
    json_file(S1, "/git_binding", equals={"path": GIT, "sha256": GIT_SHA, "bound": True, "source": "selection"}),
    json_file(S1, "/steps/0/environment_overrides/PYTHONDONTWRITEBYTECODE", equals="1"),
    json_file(S1, "/steps/0/environment_overrides/PYTHONNOUSERSITE", equals="1"),
    json_file(S1, "/steps/0/environment_overrides/ONTOKIN_CURRENT_HOST_READBACK_CONFIG",
              equals=R1OUT + "/readback-binding/selection.json"),
    json_file(S1, "/steps/0/environment_overrides/ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256",
              equals_sha256_of=R1OUT + "/readback-binding/selection.json"),
    json_file(S1, "/steps/0/removed_injection_environment_names", equals=[]),
    json_file(S1, "/steps", count_where={"pointer": "/environment_overrides", "equals": {"PYTHONDONTWRITEBYTECODE": "1"}}, equals=6)]
for name in ("selection.json", "source-before.json", "workspace-binding.json", "workspace-inventory.json"):
    R1_SUMMARY_STOP.append({"file": R1OUT + "/readback-binding/" + name, "exists": True})
R2_SUMMARY_STOP = summary_common(S2, R2OUT, "r2") + [
    json_file(S2, "/readback_selection", equals={"status": "absent", "run_kind": "ordinary"}),
    json_file(S2, "/git_binding", equals={"path": "/usr/bin/git", "sha256": DISPATCHER_SHA, "bound": False, "source": "PATH"}),
    json_file(S2, "/steps", count_where={"pointer": "/environment_overrides", "equals": {"PYTHONDONTWRITEBYTECODE": "1"}}, equals=7),
    json_file(S2, "/steps/0/removed_injection_environment_names", absent=True),
    {"file": R2OUT + "/readback-binding", "exists": False}]

R1_CLASSES = [
    {"outcome": "the wrapper's exit file and command record exist, the driver's status is 0 or 1, and every stop "
                "predicate holds (evaluated by R1.X)", "class": "COMPLETED as frozen: run R1.L, R1.I, R1.F, R1.P, R1.C, R1.K, "
                "R1.A, R1.R, R1.M, R1.X, R1.Y and R1.Z in this order"},
    {"outcome": "the summary has an error member: a preparation refusal of the selection (missing, partial, malformed or "
                "mismatched; MC21) or a driver failure", "class": "the run did not run as frozen (MR-PLAN section 9): PLAN if a "
                "fact of the freeze is wrong, IMPLEMENTATION or INPUT/HOST otherwise; kept, not retried; the sequence runs where its "
                "inputs exist (stop_rules rule 3a); R1.X is NOT_MET, so S7 stops after R1.Z"},
    {"outcome": "a test that does not pass and is not attributed by exact ID and complete record",
     "class": "FINDING (MR-PLAN section 9): recorded by R1.Y; it does not stop S7; R03 stays unmet unless the R03 review "
              "accepts it under OK-ENG-009 section 3 item 4"},
    {"outcome": "a readback method that skips, errors, is an expected failure or is missing, or a fixture record of the "
                "readback classes, or a reader or audit check that fails (MC23)",
     "class": "R1 is not qualified and MR is unmet (FINDING); R1.Y records it; S7 continues to R2 only if R1.X and R1.Z are MET"},
    {"outcome": "a step that exceeds its 7,200 s timeout", "class": "recorded (O-01); a FINDING; the driver's stop_process may "
                "raise EPERM, in which case the summary's error member makes it a run that did not run as frozen"},
    {"outcome": "the outer bound passes while R1's wrapper still runs", "class": "UNKNOWN: the overrun procedure (overrun.r1); "
                "no retry"},
    {"outcome": "an interruption, a reboot, an exit status other than 0 or 1, or a missing record", "class": "UNKNOWN; "
                "FAILURE-CAPTURE section 6; no retry"}]

R1_STARTS = {"bounded": {"node": 3, "other": 0},
             "node_route": "the provider's guarded_run_process, one supervisor_darwin_v01.run_process per case (Q01-positive, "
                           "Q03-positive, Q01-changed-reference), each established by a started.json with a positive PID and "
                           "a receipt with cleanup proof (P07 section 4)",
             "recorded_unbounded": {"uname": "about 4 (D-19: the driver, agent, construction, and the unit process's first "
                                             "unpatched platform.platform())",
                                    "file": "about 4 (the same sites)",
                                    "driver_git_reads": "49 with the bound Git (DRV-03 41, DRV-04 8)",
                                    "provider_git_reads": "about 60 with the bound Git (12 selection checks x 5 reads)",
                                    "test_git_starts": "tens to hundreds by name through /usr/bin/git (not enumerated; W1's limit)",
                                    "framework_interpreter": "the driver, its 7 steps, and the tests' Python children "
                                                             "(W1's U-01 to U-30: tens)",
                                    "other": "/bin/sh stand-ins of Git (U-20, U-22, U-24), one os.fork (U-16)"},
             "never": ["ldd", "codesign", "otool", "any Node other than the pinned runtime (PATH=/usr/bin:/bin holds no node)"]}

command("R1", "mr-001-r1", "s7", "R1, the qualifying run of the complete default routine (MR-PLAN section 1): both selection "
        "arguments from this freeze and its review, the resolved temporary directory", W, "r1", R1_ARGV,
        outputs=[A1 + "/driver"],
        deferred=[(CONFIG_DIGEST, "FREEZE-REVIEW-001.json /configuration/sha256, as the reviewer computed it from the bytes of "
                   "config/readback-config-001.json (A6: supplied from outside the freeze); 64 lowercase hexadecimal characters",
                   [{"equals_sha256_of": CONFIG}])],
        exits=(0, 1), expected_wall_s=1800, outer_bound_s=10800, starts=R1_STARTS, classification=R1_CLASSES,
        failure_capture={"listing": "R1.L", "probe": "R1.P", "overrun": "overrun.r1"},
        expect_extra=R1_SUMMARY_STOP, audit_expect=[])

# R1.L -------------------------------------------------------------------------------------------------------
LISTING_CLASSES = [{"outcome": "exit 0", "class": "continue"},
                   {"outcome": "exit 2 or 3, or a missing record", "class": "UNKNOWN for the run's evidence; FAILURE-CAPTURE "
                    "section 6; the sequence continues where inputs exist; S7 stops after R1.Z (R1) or Q04 (R2); no retry (FC-R1)"}]


def listing(ident, name, dirs, paths=(), deferred=(), purpose="FC-K5 readback"):
    argv = tool(PROBE, "listing", *[x for d in dirs for x in ("--dir", d)], *[x for p in paths for x in ("--path", p)],
                "--output", out(name + ".json"))
    target = out(name + ".json")
    return command(ident, name, "s7", purpose, E, "tools", argv, outputs=[target], deferred=deferred, expected_wall_s=60,
                   outer_bound_s=1800, classification=LISTING_CLASSES,
                   expect_extra=[json_file(target, "/command", equals="listing"),
                                 json_file(target, "/boot_before", equals=BOOT), json_file(target, "/boot_after", equals=BOOT),
                                 json_file(target, "/process_events", length=0),
                                 json_file(target, "/tool/sha256", equals=PROBE_TOOL_SHA)])


listing("R1.L", "mr-001-r1.readback", [A1], purpose="FC-K5 readback of R1, written before any other command touches the "
        "evidence: every entry of R1's attempt directory (the driver output, its workspace, and the provider's cohort), "
        "links never followed, the SHA-256 of every regular file")

python_inventory("R1.I", "mr-001-r1.python-inventory", "s7", "D-P5: the Python installation inventory between R1 and R2, "
                 "against HOST's")

# R1.F --------------------------------------------------------------------------------------------------------
HEX32 = "[0-9a-f]" * 32
NAME8 = "[a-z0-9_]" * 8
FIND = ("r=" + A1 + "; n=0; m=0; p=; for d in \"$r\"/current-host-cpu-*; do if [ ! -e \"$d\" ] && [ ! -L \"$d\" ]; then "
        "continue; fi; case \"${d#\"$r\"/}\" in current-host-cpu-" + NAME8 + "-preserved-" + HEX32 + ") if [ -d \"$d\" ] && "
        "[ ! -L \"$d\" ]; then n=$((n+1)); p=$d; else m=$((m+1)); fi;; *) m=$((m+1));; esac; done; if [ \"$n\" -eq 1 ] && "
        "[ \"$m\" -eq 0 ]; then printf \"{\\\"cohort_root\\\":\\\"%s\\\",\\\"other\\\":%s,\\\"preserved\\\":%s}\\n\" \"$p\" "
        "\"$m\" \"$n\"; exit 0; fi; printf \"{\\\"cohort_root\\\":null,\\\"other\\\":%s,\\\"preserved\\\":%s}\\n\" \"$m\" \"$n\"; "
        "exit 1")
command("R1.F", "mr-001-r1.cohort-find", "s7", "TR-09 and Q-2: R1's cohort root by the frozen rule: exactly one directory "
        "current-host-cpu-<8>-preserved-<32 hex> in R1's attempt directory (the provider's default route, preserved), and "
        "no other current-host-cpu-* entry; it reads names only, with shell builtins, and prints one JSON line",
        E, "path", env_argv("path") + ["/bin/sh", "-c", FIND], exits=(0,), expected_wall_s=1, outer_bound_s=60,
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"sh": 1}},
        classification=[{"outcome": "exit 0", "class": "continue; the printed root replaces <R1 cohort root>"},
                        {"outcome": "exit 1 (no preserved root, several, or another current-host-cpu-* entry)",
                         "class": "UNKNOWN for R1's Node starts (P07 section 4); R1.P, R1.A and R1.R are NOT_RUN; the sequence "
                                  "continues; S7 stops after R1.Z (no R2); FAILURE-CAPTURE section 6"}],
        expect_extra=[json_file(records("mr-001-r1.cohort-find")["stdout"], "/preserved", equals=1),
                      json_file(records("mr-001-r1.cohort-find")["stdout"], "/other", equals=0),
                      json_file(records("mr-001-r1.cohort-find")["stdout"], "/cohort_root", startswith=A1 + "/current-host-cpu-"),
                      {"file": records("mr-001-r1.cohort-find")["stderr"], "text_equals": ""}])

# R1.P --------------------------------------------------------------------------------------------------------
def pairs(root):
    items = []
    for case in CASES:
        items += ["--pair", root + "/provider-ledgers/" + case + "/preflight.json", root + "/provider-ledgers/" + case + "/started.json"]
    return items


PROBES1 = out("mr-001-r1.probes.json")
command("R1.P", "mr-001-r1.probes", "s7", "FC-P3: the probe of R1's three recorded Node starts (the provider's preflight.json "
        "and started.json of each case); every target must be absent", E, "tools",
        tool(PROBE, "probe", *pairs(COHORT), "--output", PROBES1), outputs=[PROBES1], deferred=[COHORT_DEFERRED],
        expected_wall_s=2, outer_bound_s=120,
        classification=[{"outcome": "exit 0, the three targets absent", "class": "continue"},
                        {"outcome": "a target present, identity established", "class": "UNKNOWN; FC-P6: R1.S<k> for that case "
                         "only; the sequence continues; S7 stops after R1.Z"},
                        {"outcome": "a target present, identity not established, or unknown", "class": "UNKNOWN; nothing is "
                         "sent; the sequence continues; S7 stops after R1.Z; FR2-02's reading applies to a pair whose records do "
                         "not exist when the ledger shows that the start never happened"},
                        {"outcome": "exit 2 or 3", "class": "UNKNOWN; as above"}],
        expect_extra=[json_file(PROBES1, "/command", equals="probe"), json_file(PROBES1, "/targets", length=3),
                      json_file(PROBES1, "/targets", each={"pointer": "/state", "equals": "absent"}),
                      json_file(PROBES1, "/boot_after", equals=BOOT), json_file(PROBES1, "/process_events", length=0),
                      json_file(PROBES1, "/tool/sha256", equals=PROBE_TOOL_SHA)])

# R1.C --------------------------------------------------------------------------------------------------------
COLLECT1 = out("mr-001-r1.unit-outcomes.json")
EXPECT1 = [item for method in METHODS for item in ("--expect", method + "=passed")] + \
          [item for fixture in FIXTURE_IDS for item in ("--expect", fixture + "=missing")]
DISCOVERY_SHA = sha256_file(DISCOVERY)
COLLECT_CLASSES = [{"outcome": "exit 0 (every expectation met, the inventory matches)", "class": "continue"},
                   {"outcome": "exit 1 (an expectation or the inventory differs)", "class": "FINDING (MC23, MC28 or MC22); "
                    "continue"},
                   {"outcome": "exit 2 or 3 (the log is refused or the outcome is unknown)", "class": "TOOLING (Q-8 of the "
                    "tooling notes): the raw log is kept; a corrected collector is a new tool, reviewed again; the sequence "
                    "continues where inputs exist; S7 stops after R1.Z (R1) or Q04 (R2)"}]
COLLECT_COMMON = lambda path, ran: [json_file(path, "/schema", equals="ontokin.c271.p36-unit-log-outcomes/2"),
                                    json_file(path, "/state", equals="PARSED"),
                                    json_file(path, "/tool/sha256", equals=sha256_file(COLLECT)),
                                    json_file(path, "/invocation/python/flags/dont_write_bytecode", equals=1),
                                    json_file(path, "/loaded_project_files", length=0)]
command("R1.C", "mr-001-r1.unit-outcomes", "s7", "MC23 and MC28's second half: R1's unit log read completely; the seven "
        "readback methods passed, each exactly once; no fixture record of the readback module; the started tests against "
        "the frozen discovery list of B, in discovery order", E, "tools",
        tool(COLLECT, "collect", "--log", LOG1, "--log-sha256", R1_LOG_DIGEST, *EXPECT1, "--inventory", DISCOVERY,
             "--inventory-sha256", DISCOVERY_SHA, "--output", COLLECT1), outputs=[COLLECT1],
        deferred=[digest_deferred(R1_LOG_DIGEST, LOG1)], exits=(0, 1, 2, 3), expected_wall_s=15, outer_bound_s=600,
        classification=COLLECT_CLASSES,
        expect_extra=COLLECT_COMMON(COLLECT1, 5994) + [json_file(COLLECT1, "/input/log/sha256", equals_sha256_of=LOG1)])

# R1.K --------------------------------------------------------------------------------------------------------
COMPARE1 = out("mr-001-r1.compare-main.json")
MAIN_RES_LOG, MAIN_RES_SUM = MAIN_RES + "/logs/unit-tests.log", MAIN_RES + "/summary.json"
MAIN_DEF_LOG, MAIN_DEF_SUM = MAIN_DEF + "/logs/unit-tests.log", MAIN_DEF + "/summary.json"
COMPARE_CLASSES = [{"outcome": "exit 0 or 1 (the comparison completed; 1: something differs, which R1's added tests and "
                    "S8's changes make certain)", "class": "continue; the lists are read by the Y check"},
                   {"outcome": "exit 2 or 3", "class": "TOOLING or PLAN; the sequence continues where inputs exist; S7 stops "
                    "after R1.Z (R1) or Q04 (R2)"}]
COMPARE_COMMON = lambda path: [json_file(path, "/schema", equals="ontokin.c271.p36-unit-log-comparison/2"),
                               json_file(path, "/state", equals="COMPARED"),
                               json_file(path, "/tool/sha256", equals=sha256_file(COLLECT)),
                               json_file(path, "/invocation/python/flags/dont_write_bytecode", equals=1),
                               json_file(path, "/exempt", length=0)]
command("R1.K", "mr-001-r1.compare-main", "s7", "OK-ENG-009 section 3 item 4: R1 against main's resolved-directory run "
        "(8e847c15), with exact inputs, the declared normalization of both runs' resolved temporary directory, and R1's "
        "frozen attributions", E, "tools",
        tool(COLLECT, "compare", "--baseline-log", MAIN_RES_LOG, "--baseline-log-sha256", sha256_file(MAIN_RES_LOG),
             "--baseline-summary", MAIN_RES_SUM, "--baseline-summary-sha256", sha256_file(MAIN_RES_SUM),
             "--baseline-tmpdir", TMP_RESOLVED, "--candidate-log", LOG1, "--candidate-log-sha256", R1_LOG_DIGEST,
             "--candidate-summary", S1, "--candidate-summary-sha256", R1_SUMMARY_DIGEST, "--candidate-tmpdir", TMP_RESOLVED,
             "--attributions", ATTR1, "--attributions-sha256", sha256_file(ATTR1), "--output", COMPARE1),
        outputs=[COMPARE1], deferred=[digest_deferred(R1_LOG_DIGEST, LOG1), digest_deferred(R1_SUMMARY_DIGEST, S1)],
        exits=(0, 1, 2, 3), expected_wall_s=30, outer_bound_s=600, classification=COMPARE_CLASSES,
        expect_extra=COMPARE_COMMON(COMPARE1))

# R1.A, R1.R ----------------------------------------------------------------------------------------------------
AUDIT1 = out("mr-001-r1.audit-numeric.json")
command("R1.A", "mr-001-r1.audit-numeric", "s7", "P07 section 6: MH's numerical-audit harness, unchanged, on R1's cohort "
        "root: every row of the three cases recomputed, the intended matrix_0_3 negative", E, "tools",
        tool(AUDIT, "--cohort-root", COHORT, "--output", AUDIT1), outputs=[AUDIT1], deferred=[COHORT_DEFERRED],
        exits=(0, 1, 2), expected_wall_s=10, outer_bound_s=600,
        classification=[{"outcome": "exit 0", "class": "continue"},
                        {"outcome": "exit 1 (a case or a check fails)", "class": "FINDING (MC24, MC25): R1 is not qualified; continue"},
                        {"outcome": "exit 2 (an input is missing or malformed)", "class": "FINDING and UNKNOWN for the cohort's "
                         "evidence; R1.R is NOT_RUN; the sequence continues; S7 stops after R1.Z"}],
        expect_extra=[json_file(AUDIT1, "/schema", equals="ontokin.c271.p35-numerical-audit/2"),
                      json_file(AUDIT1, "/tool/sha256", equals=AUDIT_TOOL_SHA),
                      json_file(AUDIT1, "/invocation/python/flags/dont_write_bytecode", equals=1),
                      json_file(AUDIT1, "/cohort_root", equals_from={"file": records("mr-001-r1.cohort-find")["stdout"],
                                                                     "pointer": "/cohort_root"})])
READBACK1 = out("mr-001-r1.readback-evidence.json")
command("R1.R", "mr-001-r1.readback-evidence", "s7", "the readback evidence reader on R1's driver run and cohort root, joined "
        "with the audit by digest (TR-09: it records cohort_bindings, which R1.M binds for the audit)", E, "tools",
        tool(READER, "run", "--summary", S1, "--summary-sha256", R1_SUMMARY_DIGEST, "--cohort-root", COHORT, "--audit", AUDIT1,
             "--audit-sha256", R1_AUDIT_DIGEST, "--audit-tool-sha256", AUDIT_TOOL_SHA, "--output", READBACK1),
        outputs=[READBACK1], deferred=[digest_deferred(R1_SUMMARY_DIGEST, S1), COHORT_DEFERRED,
                                       digest_deferred(R1_AUDIT_DIGEST, AUDIT1)],
        exits=(0, 1, 2, 3), expected_wall_s=10, outer_bound_s=600,
        classification=[{"outcome": "exit 0", "class": "continue"},
                        {"outcome": "exit 1 (a check fails)", "class": "FINDING (MC23 to MC26): R1 is not qualified; continue"},
                        {"outcome": "exit 2 or 3", "class": "TOOLING or UNKNOWN; the sequence continues; S7 stops after R1.Z"}],
        expect_extra=[json_file(READBACK1, "/schema", equals="ontokin.c271.p36-readback-evidence/1"),
                      json_file(READBACK1, "/state", equals="READ"), json_file(READBACK1, "/command", equals="run"),
                      json_file(READBACK1, "/tool/sha256", equals=sha256_file(READER)),
                      json_file(READBACK1, "/invocation/python/flags/dont_write_bytecode", equals=1),
                      json_file(READBACK1, "/cohort/cohort_root", equals_from={"file": records("mr-001-r1.cohort-find")["stdout"],
                                                                               "pointer": "/cohort_root"}),
                      json_file(READBACK1, "/cohort/route", equals="preserved")])

# R1.M --------------------------------------------------------------------------------------------------------
R1_TOOL_OUTPUTS = [out("mr-001-r1.python-inventory.json"), PROBES1, COLLECT1, COMPARE1, AUDIT1, READBACK1]
listing("R1.M", "mr-001-r1.outputs-readback", [], paths=R1_TOOL_OUTPUTS, purpose="FC-K5 readback of every output of R1's "
        "checker steps, before the X and Y checks read them: their SHA-256 binds them, and so the reader's cohort_bindings, "
        "for the audit (TR-09)")

# R1.X, R1.Y, R1.Z -----------------------------------------------------------------------------------------------
checker_command("R1.X", "mr-001-r1.expect", "s7", "R1's stop predicates (expect of R1 and of every R1 step): the run ran as "
                "frozen, the fixed state held, every checker step completed", ["expect", "--command", "R1"],
                classification=[{"outcome": "exit 0, MET", "class": "continue with R1.Y"},
                                {"outcome": "exit 1, NOT_MET", "class": "stop S7 after R1.Y and R1.Z (stop_rules rule 4): no R2; "
                                 "FAILURE-CAPTURE section 6; the failed predicates' commands' classifications decide"},
                                {"outcome": "exit 2", "class": "PLAN; stop S7"}])
checker_command("R1.Y", "mr-001-r1.outcomes", "s7", "R1's outcome predicates (audit_expect of R1): MC23, MC28, the "
                "comparison with main and every attribution, the cohort; a NOT_MET result is a set of FINDINGS, recorded, and "
                "does not stop S7", ["expect", "--command", "R1", "--audit"], exits=(0, 1),
                classification=[{"outcome": "exit 0, MET", "class": "every expected outcome held"},
                                {"outcome": "exit 1, NOT_MET", "class": "FINDINGS (MR-PLAN section 9): each failed predicate "
                                 "is recorded; S7 continues if R1.X and R1.Z are MET"},
                                {"outcome": "exit 2", "class": "PLAN; stop S7"}])
checker_command("R1.Z", "mr-001-r1.check-state", "s7", "D-P4 and the fixed state between the runs: every binding and host "
                "fact unchanged, the boot, the umask, and no bytecode or .DS_Store in the worktree (its .venv included), the "
                "prepared trees, the evidence and R1's attempt directory", ["post"],
                classification=[{"outcome": "exit 0, MET", "class": "R2 may start"},
                                {"outcome": "exit 1, NOT_MET", "class": "INPUT/HOST: the fixed state of MR-PLAN section 6 is "
                                 "broken; stop S7 (no R2)"}, {"outcome": "exit 2", "class": "PLAN; stop S7"}])

# R2 --------------------------------------------------------------------------------------------------------
R2_STARTS = {"bounded": {"node": 0, "other": 0},
             "recorded_unbounded": {"uname": "about 4", "file": "about 4",
                                    "driver_git_reads": "29 through PATH's /usr/bin/git dispatcher (DRV-03 21, DRV-04 8)",
                                    "test_git_starts": "tens to hundreds (upper bounds; W1)",
                                    "framework_interpreter": "the driver, its 7 steps, and the tests' Python children"},
             "never": R1_STARTS["never"],
             "note": "the readback class fails at setUpClass, so no readback start is made (MC22)"}
command("R2", "mr-001-r2", "s7", "R2, the ordinary run of the complete default routine (MR-PLAN section 1): no selection "
        "argument, macOS's default temporary directory through the /var link", W, "r2", R2_ARGV, outputs=[R2OUT],
        exits=(0, 1), expected_wall_s=1800, outer_bound_s=10800, starts=R2_STARTS,
        classification=[
            {"outcome": "completed, every stop predicate holds (R2.X)", "class": "COMPLETED: run R2.L, R2.I, R2.C, R2.K, R2.V, "
             "R2.M, R2.X, R2.Y, then Q01, Q01.X and Q04"},
            {"outcome": "the summary has an error member, or the driver refused to proceed", "class": "the run did not run as "
             "frozen (MC22 not met, or a driver failure); kept, not retried; the sequence runs where its inputs exist; S7 stops "
             "after Q04"},
            {"outcome": "a test that does not pass and is not attributed, nor unchanged from R1 (R2.V), nor in the /var-alias "
             "class (stop_rules.r2_classification)", "class": "FINDING; it does not stop S7"},
            {"outcome": "the outer bound passes while R2's wrapper still runs", "class": "UNKNOWN: overrun procedure (no start "
             "to probe); no retry"},
            {"outcome": "an interruption, a reboot, an exit status other than 0 or 1, or a missing record", "class": "UNKNOWN"}],
        failure_capture={"listing": "R2.L", "probe": None, "overrun": "overrun.other"}, expect_extra=R2_SUMMARY_STOP)
listing("R2.L", "mr-001-r2.readback", [R2OUT], purpose="FC-K5 readback of R2: every entry of R2's driver output")
python_inventory("R2.I", "mr-001-r2.python-inventory", "s7", "D-P5: the Python installation inventory after R2, against HOST's")
COLLECT2 = out("mr-001-r2.unit-outcomes.json")
EXPECT2 = ["--expect", MC22_FIXTURE + "=error"] + [x for m in TRIO for x in ("--expect", m + "=missing")] + \
          [x for m in SEAMS for x in ("--expect", m + "=passed")] + \
          [x for fixture in FIXTURE_IDS[1:] for x in ("--expect", fixture + "=missing")]
command("R2.C", "mr-001-r2.unit-outcomes", "s7", "MC22 on a real ordinary run: the readback CPU class fails at setUpClass, "
        "once, its three methods neither run nor are reported, the four seams pass, no skip; the started tests against the "
        "frozen discovery list (exactly the three CPU methods not started)", E, "tools",
        tool(COLLECT, "collect", "--log", LOG2, "--log-sha256", R2_LOG_DIGEST, *EXPECT2, "--inventory", DISCOVERY,
             "--inventory-sha256", DISCOVERY_SHA, "--output", COLLECT2), outputs=[COLLECT2],
        deferred=[digest_deferred(R2_LOG_DIGEST, LOG2)], exits=(0, 1, 2, 3), expected_wall_s=15, outer_bound_s=600,
        classification=COLLECT_CLASSES,
        expect_extra=COLLECT_COMMON(COLLECT2, 5991) + [json_file(COLLECT2, "/input/log/sha256", equals_sha256_of=LOG2)])
COMPARE2 = out("mr-001-r2.compare-main.json")
command("R2.K", "mr-001-r2.compare-main", "s7", "OK-ENG-009 section 3 item 4: R2 against main's default-directory run, with "
        "exact inputs, both runs' default temporary directory, and R2's frozen attributions", E, "tools",
        tool(COLLECT, "compare", "--baseline-log", MAIN_DEF_LOG, "--baseline-log-sha256", sha256_file(MAIN_DEF_LOG),
             "--baseline-summary", MAIN_DEF_SUM, "--baseline-summary-sha256", sha256_file(MAIN_DEF_SUM),
             "--baseline-tmpdir", TMP_DEFAULT, "--candidate-log", LOG2, "--candidate-log-sha256", R2_LOG_DIGEST,
             "--candidate-summary", S2, "--candidate-summary-sha256", R2_SUMMARY_DIGEST, "--candidate-tmpdir", TMP_DEFAULT,
             "--attributions", ATTR2, "--attributions-sha256", sha256_file(ATTR2), "--output", COMPARE2),
        outputs=[COMPARE2], deferred=[digest_deferred(R2_LOG_DIGEST, LOG2), digest_deferred(R2_SUMMARY_DIGEST, S2)],
        exits=(0, 1, 2, 3), expected_wall_s=30, outer_bound_s=600, classification=COMPARE_CLASSES,
        expect_extra=COMPARE_COMMON(COMPARE2))
COMPARE12 = out("mr-001-r2.compare-r1.json")
command("R2.V", "mr-001-r2.compare-r1", "s7", "R1 against R2, each normalized with its own temporary directory: which tests "
        "change between the resolved directory and the /var link on this candidate (stop_rules.r2_classification)", E,
        "tools", tool(COLLECT, "compare", "--baseline-log", LOG1, "--baseline-log-sha256", R1_LOG_DIGEST,
                      "--baseline-summary", S1, "--baseline-summary-sha256", R1_SUMMARY_DIGEST, "--baseline-tmpdir", TMP_RESOLVED,
                      "--candidate-log", LOG2, "--candidate-log-sha256", R2_LOG_DIGEST, "--candidate-summary", S2,
                      "--candidate-summary-sha256", R2_SUMMARY_DIGEST, "--candidate-tmpdir", TMP_DEFAULT, "--output", COMPARE12),
        outputs=[COMPARE12], deferred=[digest_deferred(R1_LOG_DIGEST, LOG1), digest_deferred(R1_SUMMARY_DIGEST, S1),
                                       digest_deferred(R2_LOG_DIGEST, LOG2), digest_deferred(R2_SUMMARY_DIGEST, S2)],
        exits=(0, 1, 2, 3), expected_wall_s=30, outer_bound_s=600, classification=COMPARE_CLASSES,
        expect_extra=COMPARE_COMMON(COMPARE12))
R2_TOOL_OUTPUTS = [out("mr-001-r2.python-inventory.json"), COLLECT2, COMPARE2, COMPARE12]
listing("R2.M", "mr-001-r2.outputs-readback", [], paths=R2_TOOL_OUTPUTS, purpose="FC-K5 readback of every output of R2's "
        "checker steps, before the X and Y checks read them")
checker_command("R2.X", "mr-001-r2.expect", "s7", "R2's stop predicates", ["expect", "--command", "R2"],
                classification=[{"outcome": "exit 0, MET", "class": "continue with R2.Y"},
                                {"outcome": "exit 1, NOT_MET", "class": "stop S7 after R2.Y, Q01, Q01.X and Q04; "
                                 "FAILURE-CAPTURE section 6"}, {"outcome": "exit 2", "class": "PLAN; stop S7"}])
checker_command("R2.Y", "mr-001-r2.outcomes", "s7", "R2's outcome predicates (audit_expect of R2): MC22, the comparison with "
                "main's default-directory run and its attributions, S8's change; NOT_MET records FINDINGS",
                ["expect", "--command", "R2", "--audit"], exits=(0, 1),
                classification=[{"outcome": "exit 0 or 1", "class": "recorded; continue with Q01"},
                                {"outcome": "exit 2", "class": "PLAN; stop S7"}])
source_inventory("Q01", "mr-001-q01-source-inventory", "s7", "the provider's source inventory of B after S7")
checker_command("Q01.X", "mr-001-q01.expect", "s7", "Q01's predicates", ["expect", "--command", "Q01"],
                classification=[{"outcome": "exit 0, MET", "class": "continue with Q04"},
                                {"outcome": "exit 1, NOT_MET", "class": "INPUT/HOST: the source changed during S7; recorded "
                                 "for S8; Q04 runs"}, {"outcome": "exit 2", "class": "PLAN"}])
checker_command("Q04", "mr-001-q04-check-post", "post", "the final state: every binding and host fact, the boot, the umask, "
                "and no bytecode or .DS_Store in the named trees, after R2", ["post"],
                classification=[{"outcome": "exit 0, MET", "class": "S7 complete; S8 follows"},
                                {"outcome": "exit 1, NOT_MET", "class": "INPUT/HOST: recorded for S8; nothing is repaired"},
                                {"outcome": "exit 2", "class": "PLAN"}])

# Overrun commands ------------------------------------------------------------------------------------------------
NAME8T = "[a-z0-9_]" * 8
SELECT = ("r=" + A1 + "; t=0; s=0; m=0; tp=; sp=; for d in \"$r\"/current-host-cpu-*; do if [ ! -e \"$d\" ] && [ ! -L \"$d\" ]; "
          "then continue; fi; if [ ! -d \"$d\" ] || [ -L \"$d\" ]; then m=$((m+1)); continue; fi; case \"${d#\"$r\"/}\" in "
          "current-host-cpu-" + NAME8T + ") t=$((t+1)); tp=$d;; current-host-cpu-" + NAME8T + "-preserved-" + HEX32 + ") "
          "s=$((s+1)); sp=$d;; *) m=$((m+1));; esac; done; if [ \"$t\" -eq 1 ]; then p=$tp; k=temporary; elif [ \"$t\" -eq 0 ] "
          "&& [ \"$s\" -eq 1 ]; then p=$sp; k=preserved; else printf \"{\\\"cohort_root\\\":null,\\\"temporary\\\":%s,"
          "\\\"preserved\\\":%s,\\\"other\\\":%s}\\n\" \"$t\" \"$s\" \"$m\"; exit 1; fi; printf \"{\\\"cohort_root\\\":\\\"%s\\\","
          "\\\"kind\\\":\\\"%s\\\",\\\"temporary\\\":%s,\\\"preserved\\\":%s,\\\"other\\\":%s}\\n\" \"$p\" \"$k\" \"$t\" \"$s\" \"$m\"; "
          "exit 0")
OVERRUN_DEFERRED = (OVERRUN_COHORT, "the value of /cohort_root in mr-001-r1.overrun-select.stdout.txt (jq -r .cohort_root); "
                    "it must match ^" + A1 + "/current-host-cpu-[a-z0-9_]{8}(-preserved-[0-9a-f]{32})?$",
                    [{"startswith": A1 + "/current-host-cpu-"}])
command("R1.N", "mr-001-r1.overrun-select", "overrun", "overrun step 2 for R1: the cohort root that holds R1's recorded "
        "starts, the temporary one while the cohort runs, else the preserved one; names only, shell builtins",
        E, "path", env_argv("path") + ["/bin/sh", "-c", SELECT], exits=(0, 1), expected_wall_s=1, outer_bound_s=60,
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"sh": 1}},
        classification=[{"outcome": "exit 0", "class": "run R1.O with the printed root"},
                        {"outcome": "exit 1", "class": "no single cohort root: nothing to probe; overrun step 4 onwards"}])
OPROBES = out("mr-001-r1.overrun-probes.json")
command("R1.O", "mr-001-r1.overrun-probes", "overrun", "overrun step 2 (MH's FR-01 (c)): one probe of every candidate pair of "
        "R1; a pair whose records do not exist is reported, not refused (capture_probe.py read_pair)", E, "tools",
        tool(PROBE, "probe", *pairs(OVERRUN_COHORT), "--output", OPROBES), outputs=[OPROBES], deferred=[OVERRUN_DEFERRED],
        expected_wall_s=2, outer_bound_s=120,
        classification=[{"outcome": "any", "class": "run R1.S<k> only for target k-1 in state 'present, identity established'"}])
for k, case in enumerate(CASES, 1):
    path = out("mr-001-r1.stop-%d.json" % k)
    command("R1.S%d" % k, "mr-001-r1.stop-%d" % k, "overrun", "FC-P6 for R1's case " + case + " only: run once, only for "
            "its target in state 'present, identity established' in R1.O (with the overrun root) or in R1.P (with the "
            "found root)", E, "tools",
            tool(PROBE, "stop", "--pair", OVERRUN_COHORT + "/provider-ledgers/" + case + "/preflight.json",
                 OVERRUN_COHORT + "/provider-ledgers/" + case + "/started.json", "--output", path),
            outputs=[path], deferred=[OVERRUN_DEFERRED], expected_wall_s=5, outer_bound_s=120,
            classification=[{"outcome": "any", "class": "the attempt stays UNKNOWN or failed; ending a process changes no outcome"}],
            note="After R1.P (no overrun), the same command runs with <R1 overrun cohort root> replaced by R1.F's printed root.")

# ---------------------------------------------------------------------------------------------------------
# Outcome predicates (audit_expect): the expected outcomes and attributions
# ---------------------------------------------------------------------------------------------------------
by_id = {row["id"]: row for row in COMMANDS}


def collect_outcomes(path, ran, fixtures):
    return [json_file(path, "/footer/ran", equals=ran),
            json_file(path, "/footer/counts/skipped", equals=0),
            json_file(path, "/footer/counts/expected failures", equals=0),
            json_file(path, "/footer/counts/unexpected successes", equals=0),
            json_file(path, "/counts/by_outcome/skipped", equals=0),
            json_file(path, "/counts/by_outcome/expected_failure", equals=0),
            json_file(path, "/counts/by_outcome/unexpected_success", equals=0),
            json_file(path, "/counts/by_outcome/unknown", equals=0),
            json_file(path, "/counts/duplicate_test_ids", equals=0),
            json_file(path, "/counts/fixture_ids", equals=fixtures),
            json_file(path, "/driver_reading/equals_footer", equals=True),
            json_file(path, "/driver_reading/skipped", equals=0),
            json_file(path, "/driver_reading/expected_failures", equals=0),
            json_file(path, "/expectations_met", equals=True),
            json_file(path, "/expectations", each={"pointer": "/met", "equals": True}),
            json_file(path, "/checks", equals={"errors_equal_footer": True, "every_test_has_a_status": True,
                                               "expected_failures_equal_footer": True, "failures_equal_footer": True,
                                               "listing_entries_equal_failures_and_errors": True,
                                               "skipped_equal_footer": True, "tests_started_equal_ran": True,
                                               "unexpected_successes_equal_footer": True})]


R1_OUT = summary_outcomes(S1, 5994) + [{"file": records("mr-001-r1")["exit"], "text_equals": "1\n"}]
R1_OUT += collect_outcomes(COLLECT1, 5994, 0) + [
    json_file(COLLECT1, "/expectations", length=13),
    json_file(COLLECT1, "/inventory/matches", equals=True), json_file(COLLECT1, "/inventory/sequence_equal", equals=True),
    json_file(COLLECT1, "/inventory/ids", equals=5994), json_file(COLLECT1, "/inventory/started", equals=5994),
    json_file(COLLECT1, "/inventory/started_not_in_inventory", length=0),
    json_file(COLLECT1, "/inventory/inventory_not_started", length=0),
    json_file(COLLECT1, "/inventory/started_a_different_number_of_times", length=0),
    json_file(COLLECT1, "/inventory/recomputed_duplicates", length=0),
    json_file(COLLECT1, "/inventory/input/sha256", equals=DISCOVERY_SHA)]
for index, method in enumerate(METHODS):
    R1_OUT += [json_file(COLLECT1, "/expectations/%d/id" % index, equals=method),
               json_file(COLLECT1, "/expectations/%d/observed" % index, equals="passed"),
               json_file(COLLECT1, "/expectations/%d/occurrences" % index, equals=1)]
for index, fixture in enumerate(FIXTURE_IDS, len(METHODS)):
    R1_OUT += [json_file(COLLECT1, "/expectations/%d/id" % index, equals=fixture),
               json_file(COLLECT1, "/expectations/%d/observed" % index, equals="missing")]
R1_OUT += [json_file(COMPARE1, "/tests", equals={"baseline": 4989, "candidate": 5994}),
           *[json_file(COMPARE1, "/counts/" + key, equals=value) for key, value in (
               ("added_ids", 1005), ("different_occurrences", 0), ("different_outcome", 3), ("different_reason", 0),
               ("different_skip_reason", 0), ("different_subtests", 0), ("new_not_passing", 91), ("no_longer_failing", 0),
               ("removed_ids", 0), ("unchanged_expected_failures", 0), ("unchanged_not_passing", 1), ("unchanged_skipped", 0))],
           *[json_file(COMPARE1, "/unchanged/" + key, equals=value) for key, value in (
               ("error", 0), ("expected_failure", 0), ("failure", 1), ("passed", 4985), ("skipped", 0), ("unexpected_success", 0))],
           json_file(COMPARE1, "/unchanged_not_passing/0/id", equals=FORCE_CONTRACT),
           json_file(COMPARE1, "/unchanged_not_passing/0/attribution/matches", equals=True),
           json_file(COMPARE1, "/different_outcome", each={"pointer": "/baseline/outcome", "equals": "skipped"}),
           json_file(COMPARE1, "/different_outcome", each={"pointer": "/candidate/outcome", "equals": "passed"}),
           json_file(COMPARE1, "/new_not_passing", count_where={"pointer": "/attribution/matches", "equals": True}, equals=91),
           json_file(COMPARE1, "/attributions", length=92),
           json_file(COMPARE1, "/attributions", count_where={"pointer": "/matches", "equals": True}, equals=92),
           json_file(COMPARE1, "/summaries/steps_different", length=0),
           json_file(COMPARE1, "/summaries/reports_different", length=0),
           json_file(COMPARE1, "/summaries/pending_external_cases/equal", equals=True),
           json_file(COMPARE1, "/summaries/not_executed_steps/equal", equals=True),
           json_file(COMPARE1, "/summaries/runs/candidate/readback_selection", equals={"status": "workspace_bound",
                                                                                       "run_kind": "qualifying"}),
           json_file(COMPARE1, "/logs/baseline/driver_reading_matches_summary", equals=True),
           json_file(COMPARE1, "/logs/candidate/driver_reading_matches_summary", equals=True)]
for index, method in enumerate(TRIO):
    R1_OUT.append(json_file(COMPARE1, "/different_outcome", count_where={"pointer": "/id", "equals": method}, equals=1))
R1_OUT += [json_file(AUDIT1, "/passed", equals=True), json_file(AUDIT1, "/all_three_cases", equals=True),
           json_file(AUDIT1, "/negative_fixture/passed", equals=True)]
for case in CASES:
    R1_OUT.append(json_file(AUDIT1, "/cases/" + case + "/passed", equals=True))
R1_OUT += [json_file(READBACK1, "/passed", equals=True), json_file(READBACK1, "/failed_checks", length=0),
           json_file(READBACK1, "/starts/established", equals=3), json_file(READBACK1, "/starts/expected", equals=3),
           json_file(READBACK1, "/starts/rows", length=3), json_file(READBACK1, "/numerical_audit/passed", equals=True),
           json_file(READBACK1, "/driver_run/workspace", equals=R1OUT + "/workspace"),
           json_file(READBACK1, "/driver_run/evidence_root", equals=A1),
           json_file(READBACK1, "/cohort/original_root", startswith=A1 + "/current-host-cpu-")]
by_id["R1"]["audit_expect"] = R1_OUT

R2_OUT = summary_outcomes(S2, 5991) + [{"file": records("mr-001-r2")["exit"], "text_equals": "1\n"}]
R2_OUT += collect_outcomes(COLLECT2, 5991, 1) + [
    json_file(COLLECT2, "/expectations", length=13),
    json_file(COLLECT2, "/inventory/matches", equals=False),
    json_file(COLLECT2, "/inventory/started", equals=5991),
    json_file(COLLECT2, "/inventory/started_not_in_inventory", length=0),
    json_file(COLLECT2, "/inventory/inventory_not_started", equals=sorted(TRIO)),
    json_file(COLLECT2, "/inventory/started_a_different_number_of_times", length=0),
    json_file(COLLECT2, "/fixtures", count_where={"pointer": "/id", "equals": MC22_FIXTURE}, equals=1),
    json_file(COLLECT2, "/fixtures", count_where={"pointer": "/reasons", "equals": [ORDINARY_REASON]}, equals=1),
    json_file(COLLECT2, "/expectations/0/id", equals=MC22_FIXTURE),
    json_file(COLLECT2, "/expectations/0/observed", equals="error"),
    json_file(COLLECT2, "/expectations/0/occurrences", equals=1)]
R2_OUT += [json_file(COMPARE2, "/tests", equals={"baseline": 4989, "candidate": 5991}),
           json_file(COMPARE2, "/counts/unchanged_not_passing", equals=307),
           json_file(COMPARE2, "/counts/no_longer_failing", equals=0),
           json_file(COMPARE2, "/counts/different_outcome", equals=0),
           json_file(COMPARE2, "/counts/different_reason", equals=0),
           json_file(COMPARE2, "/counts/different_subtests", equals=0),
           json_file(COMPARE2, "/counts/different_skip_reason", equals=0),
           json_file(COMPARE2, "/counts/different_occurrences", equals=0),
           json_file(COMPARE2, "/counts/unchanged_skipped", equals=0),
           json_file(COMPARE2, "/counts/removed_ids", equals=3),
           json_file(COMPARE2, "/counts/added_ids", equals=1006),
           json_file(COMPARE2, "/unchanged_not_passing", count_where={"pointer": "/attribution/matches", "equals": True}, equals=307),
           json_file(COMPARE2, "/removed_ids", each={"pointer": "/baseline/outcome", "equals": "skipped"}),
           json_file(COMPARE2, "/new_not_passing", count_where={"pointer": "/attribution/matches", "equals": True}, equals=3),
           json_file(COMPARE2, "/attributions", length=310),
           json_file(COMPARE2, "/attributions", count_where={"pointer": "/matches", "equals": True}, equals=310),
           json_file(COMPARE2, "/summaries/steps_different", length=0),
           json_file(COMPARE2, "/summaries/reports_different", length=0),
           json_file(COMPARE2, "/summaries/pending_external_cases/equal", equals=True),
           json_file(COMPARE2, "/summaries/not_executed_steps/equal", equals=True),
           json_file(COMPARE2, "/summaries/runs/candidate/readback_selection", equals={"status": "absent", "run_kind": "ordinary"}),
           json_file(COMPARE2, "/logs/candidate/driver_reading_matches_summary", equals=True),
           json_file(COMPARE12, "/counts/removed_ids", equals=3),
           json_file(COMPARE12, "/removed_ids", each={"pointer": "/baseline/outcome", "equals": "passed"}),
           json_file(COMPARE12, "/counts/no_longer_failing", equals=0),
           json_file(COMPARE12, "/new_not_passing", count_where={"pointer": "/id", "equals": MC22_FIXTURE}, equals=1)]
for method in TRIO:
    R2_OUT.append(json_file(COMPARE2, "/removed_ids", count_where={"pointer": "/id", "equals": method}, equals=1))
    R2_OUT.append(json_file(COMPARE12, "/removed_ids", count_where={"pointer": "/id", "equals": method}, equals=1))
by_id["R2"]["audit_expect"] = R2_OUT

# Stop predicates of every step, appended to its run's expect (MH's FR-02): evaluated by R1.X / R2.X.
for run, steps in (("R1", ["R1.L", "R1.I", "R1.F", "R1.P", "R1.C", "R1.K", "R1.A", "R1.R", "R1.M"]),
                   ("R2", ["R2.L", "R2.I", "R2.C", "R2.K", "R2.V", "R2.M"])):
    for ident in steps:
        by_id[run]["expect"] += by_id[ident]["expect"]
    by_id[run]["expect_composition"] = ["R1's or R2's own wrapper and summary predicates"] + \
        ["the expect of " + ident for ident in steps]

# ---------------------------------------------------------------------------------------------------------
# Bindings, host facts, trees, absent paths
# ---------------------------------------------------------------------------------------------------------
P = L + "/c271-p36"
bindings = []


def bind(ident, path, role, **kw):
    bindings.append(file_row(ident, path, role, **kw))


for ident, path, role in [
        ("tool:unit_log_outcomes.py", COLLECT, "MR's unit-log collector and comparator at B (reviewed: TOOLING-REVIEW-002)"),
        ("tool:readback_evidence.py", READER, "MR's readback evidence reader at B (reviewed)"),
        ("tool:mr-tooling-README.md", MRT + "/README.md", "MR's tooling README at B"),
        ("tool:FAILURE-CAPTURE.md", MHT + "/FAILURE-CAPTURE.md", "MH's failure-capture procedure, reused unchanged (PR-01's reading)"),
        ("tool:capture_probe.py", PROBE, "its probe tool, reused unchanged"),
        ("tool:discover_inventory.py", MHT + "/discover_inventory.py", "MH's runtime-discovery collector (MC28), reused unchanged"),
        ("tool:audit_numeric.py", AUDIT, "MH's numerical-audit harness, reused unchanged"),
        ("tool:w2f_s7_check.py", CHECKER, "MH's reviewed S7 checker, reused unchanged as this freeze's checker"),
        ("tool:observer", OBSERVER, "the observer (python-inventory, source-inventory); HOST's /observer"),
        ("source:check_local.py", W + "/tools/check_local.py", "the routine's driver at B"),
        ("source:current_host_readback_v02.py", W + "/prototypes/static_tray_v01/current_host_readback_v02.py", "the provider"),
        ("source:current_host_readback_v01.py", W + "/prototypes/static_tray_v01/current_host_readback_v01.py", "the facade"),
        ("source:test_static_tray_readback_v01.py", W + "/tests/test_static_tray_readback_v01.py", "the readback module"),
        ("source:CONTRACT.md", ENG + "/macos-contract-design-p31/CONTRACT.md", "the contract (config contract_source)"),
        ("source:ADOPTION-AMENDMENT-001.json", ENG + "/macos-implementation-p33/ADOPTION-AMENDMENT-001.json",
         "PR-06: the amendment's adoption record, bound by the configuration (872312ed..., 5,396 bytes, 0o644)"),
        ("source:INVENTORY-ADDITIONS.json", ENG + "/macos-implementation-p33/INVENTORY-ADDITIONS.json", "MC28's 407 approved additions"),
        ("source:MI-CHECKS.json", ENG + "/macos-implementation-p33/CHECKS.json", "MI's checks record: final-003's per-module logs by digest"),
        ("source:MAP-EVIDENCE.zip", ENG + "/current-host-p05/mapping/MAP-EVIDENCE.zip", "the discovery document's baseline_map"),
        ("source:macos-lock", W + "/tools/native-reader-verification-macos-arm64-cp312.lock", "HOST's /python/lock"),
        ("source:C195-archive", W + "/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz",
         "the committed C195 archive (HOST /dependencies/archive), retained unchanged"),
        ("source:INTEGRATION.json", W + "/docs/engineering/local-migration-20261124/INTEGRATION.json", "main's baseline record"),
        ("source:MR-PLAN.md", ENG + "/macos-routine-p36/MR-PLAN.md", "the MR plan"),
        ("source:PHASE.json", ENG + "/macos-routine-p36/PHASE.json", "the declaration"),
        ("host:HOST.json", E + "/observe-001/HOST.json", "HOST (HR-01): 858ef72a... from HOST-REVIEW-001.json /host/sha256"),
        ("host:completion.json", E + "/observe-001/completion.json", "HR-01: OBSERVED_UNAPPROVED, evidence_finalized"),
        ("host:result.json", E + "/observe-001/result.json", "HR-01: PENDING_COMPLETION by design"),
        ("host:git-inspection", E + "/observe-001/git_version/inspection.json", "HR-02: the attempt's Git receipt"),
        ("host:node-inspection", E + "/observe-001/node_version/inspection.json", "HR-02: the attempt's Node receipt"),
        ("host:preflight.json", E + "/observe-001/preflight.json", "the attempt, retained"),
        ("host:reserved.json", E + "/observe-001/reserved.json", "the attempt, retained"),
        ("plan:python-inventory-001.json", P + "/workers/W2-plan-001/python-inventory-001.json", "HR-02: HOST's frozen Python inventory"),
        ("plan:source-inventory-001.json", P + "/workers/W2-plan-001/source-inventory-001.json", "HR-02: HOST's source inventory"),
        ("plan:dependencies-inventory-001.json", P + "/workers/W2-plan-001/dependencies-inventory-001.json", "HR-02: the reader tree's inventory"),
        ("plan:observation-plan-001.json", P + "/workers/W2-plan-001/observation-plan-001.json", "HOST's /plan"),
        ("review:HOST-REVIEW-001.json", P + "/workers/W3-host-001/HOST-REVIEW-001.json", "the HOST review record"),
        ("review:PLAN-REVIEW-001.json", P + "/workers/W3-plan-001/PLAN-REVIEW-001.json", "the plan review record"),
        ("review:HOST-REVIEW-DISPOSITION-001.json", P + "/director/reviews/HOST-REVIEW-DISPOSITION-001.json", "HR-01 to HR-08's dispositions"),
        ("review:PLAN-REVIEW-DISPOSITION-001.json", P + "/director/reviews/PLAN-REVIEW-DISPOSITION-001.json", "PR-01 to PR-06's dispositions"),
        ("review:START-INVENTORY-DISPOSITION.json", P + "/director/reviews/START-INVENTORY-DISPOSITION.json", "D-P1 to D-P7"),
        ("review:TOOLING-REVIEW-DISPOSITION-002.json", P + "/director/reviews/TOOLING-REVIEW-DISPOSITION-002.json", "TR2-01, TR2-03, TR2-04"),
        ("review:TOOLING-REVIEW-DISPOSITION-001.json", P + "/director/reviews/TOOLING-REVIEW-DISPOSITION-001.json", "TR-09"),
        ("director:run_once_p36.sh", WRAP, "HR-08: the Director's wrapper (9154f181..., 3,629 bytes); its epoch fields are the authoritative times"),
        ("director:main-name-status", P + "/director/inputs/main-8e847c15-to-51223c9b-name-status.txt", "TR-10: main's change since 8e847c15"),
        ("mp:node-install-plan.json", L + "/c271-p34/plans/node-install-plan.json", "HR-02: MP's plan, re-read by the provider"),
        ("mp:node-install-result.json", L + "/c271-p34/receipts/node-install-result.json", "HR-02: MP's receipt"),
        ("mp:reader-install-plan.json", L + "/c271-p34/plans/reader-install-plan.json", "HR-02: MP's plan"),
        ("mp:reader-install-result.json", L + "/c271-p34/receipts/reader-install-result.json", "HR-02: MP's receipt"),
        ("mp:node-archive", L + "/c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz", "the Node archive, retained unchanged"),
        ("runtime:bin/node", L + "/c271-macos/node-v24.22.1-darwin-arm64/bin/node", "the pinned runtime"),
        ("runtime:NODE-SOURCE.json", L + "/c271-macos/node-v24.22.1-darwin-arm64/NODE-SOURCE.json", "the runtime's source record"),
        ("host:git", GIT, "the bound Git (HOST /git)"),
        ("baseline:main-resolved-log", MAIN_RES_LOG, "main's resolved-directory unit log (INTEGRATION.json)"),
        ("baseline:main-resolved-summary", MAIN_RES_SUM, "main's resolved-directory summary"),
        ("baseline:main-default-log", MAIN_DEF_LOG, "main's default-directory unit log"),
        ("baseline:main-default-summary", MAIN_DEF_SUM, "main's default-directory summary"),
        ("baseline:main-resolved-source-before", MAIN_RES + "/source-before.json", "main's driver inventory (the author's comparison)"),
        ("mh:discovery-baseline", L + "/c271-p35/evidence/s7-001-discovery-baseline.json", "MC28's baseline: 5,587 IDs at 1c2f25ba (MH's exact record)"),
        ("mh:HOST.json", L + "/c271-p35/evidence/observe-001/HOST.json", "MH's HOST, an exact record of MH, retained unchanged"),
        ("freeze:discovery-b-001.json", DISCOVERY, "MC28: the complete default inventory at B (5,994), by MH's collector"),
        ("freeze:discovery-b-compare-001.json", DISCOVERY_COMPARE, "MC28: exact match with the baseline plus the 407 additions"),
        ("freeze:discovery-001.json", F + "/config/discovery-001.json", "the provider's discovery document (5,994 sorted IDs)"),
        ("freeze:methods-001.json", F + "/config/methods-001.json", "the provider's methods document"),
        ("freeze:r1-attributions-001.json", ATTR1, "R1's attributions (92)"),
        ("freeze:r2-attributions-001.json", ATTR2, "R2's attributions (310)"),
        ("freeze:env-r1", env_files["r1"]["file"], "R1's declared environment"),
        ("freeze:env-r2", env_files["r2"]["file"], "R2's declared environment"),
        ("freeze:env-tools", env_files["tools"]["file"], "the tools' environment (the declared five)"),
        ("freeze:env-path", env_files["path"]["file"], "PATH only")]:
    bind(ident, path, role)
bind("host:git-dispatcher", "/usr/bin/git", "the dispatcher that R2's driver and the tests start by name "
     "(PATH=/usr/bin:/bin); a shared system file with many links", nlink_one=False)
for name in ("readback_driver", "readback_provider", "inspection_v01", "required_images_v01", "rtld_paths_v01"):
    bind("mi:final-003:" + name, L + "/c271-p33/checks/final-003/tests.test_current_host_" + name + ".txt",
         "MI's retained per-module log on this host (final-003), a source of R1's attributions")
bind("mi:final-003:static_tray_readback_v01", L + "/c271-p33/checks/final-003/tests.test_static_tray_readback_v01.txt",
     "MI's retained ordinary per-module run of the readback module (MC22's fixed reason)")
for name in ("observe-001.static.stdout.txt", "observe-001.static.exit.txt", "observe-001.static.command.json",
             "observe-001.observe.stdout.txt", "observe-001.observe.exit.txt", "observe-001.observe.command.json",
             "observe-001.static.stderr.txt", "observe-001.observe.stderr.txt"):
    bind("s5:" + name, E + "/" + name, "S5's capture files, retained")
ids = [row["id"] for row in bindings]
assert len(ids) == len(set(ids))
assert next(r for r in bindings if r["id"] == "host:HOST.json")["sha256"] == "858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666"
assert next(r for r in bindings if r["id"] == "director:run_once_p36.sh")["sha256"] == "9154f181cfa7c8648c21b31a1f309af43f9b2b5046df1656a124a4b6b55e07a7"
assert next(r for r in bindings if r["id"] == "source:ADOPTION-AMENDMENT-001.json")["sha256"] == "872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937"
assert next(r for r in bindings if r["id"] == "host:completion.json")["sha256"] == "9db0900a1d8af90eebd3c73dac1f65791c7091723637064e544f74c7dc8469b0"
assert next(r for r in bindings if r["id"] == "host:result.json")["sha256"] == "ec9fd08f3b0a33a5e081d2559149894085434e762d7cddc226c5b934c9c5d4e7"
assert next(r for r in bindings if r["id"] == "host:git-inspection")["sha256"].startswith("bbbb832f")
assert next(r for r in bindings if r["id"] == "host:node-inspection")["sha256"].startswith("009fbd06")
assert next(r for r in bindings if r["id"] == "tool:w2f_s7_check.py")["sha256"] == "eb96aa1a25ba51bf32f55420997bc8599343a59c2238ce70b4b0c622d01643f6"
assert next(r for r in bindings if r["id"] == "host:git-dispatcher")["sha256"] == DISPATCHER_SHA

host_facts = [file_row("fact:CFUserTextEncoding", HOME + "/.CFUserTextEncoding",
                       "HR-03: the file from which CoreFoundation builds __CF_USER_TEXT_ENCODING (MC31); an unbound host fact"),
              file_row("fact:global-gitconfig", HOME + "/.gitconfig",
                       "D-P3: the global Git configuration that the doctor's Git children read; digest and size only"),
              file_row("fact:git-xdg-ignore", HOME + "/.config/git/ignore",
                       "D-P3: Git's default excludes file under the XDG configuration directory, read by every Git child that "
                       "lists untracked files; digest and size only")]
trees = [{"root": W, "bytecode": True, "exclude": [], "role": "D-P4: the worktree and its .venv"},
         {"root": L + "/c271-macos", "bytecode": True, "exclude": [], "role": "the pinned runtime and the reader tree"},
         {"root": E, "bytecode": False, "exclude": [], "role": "the evidence parent: no .DS_Store"},
         {"root": A1, "bytecode": True, "exclude": [], "role": "R1's attempt directory, from D02 on"},
         {"root": R2OUT, "bytecode": True, "exclude": [], "role": "R2's driver output, after R2"}]
ancestors = []
current = E
while True:
    info = os.lstat(current)
    ancestors.append({"path": current, "device": info.st_dev, "inode": info.st_ino, "mode": "0o%03o" % stat.S_IMODE(info.st_mode)})
    if current == "/":
        break
    current = os.path.dirname(current)
ancestors.sort(key=lambda row: row["path"])
ALWAYS_ABSENT = [HOME + "/.config/git/config", HOME + "/.config/git/attributes"]
s7_paths = sorted({path for row in COMMANDS for path in row["outputs_absent_before"]})
own_p00_p01 = set(by_id["P00"]["outputs_absent_before"]) | set(records("mr-001-p01-check-pre").values())
before = sorted(set(s7_paths) - own_p00_p01) + ALWAYS_ABSENT
made_before_d02 = set()
for ident in ("P00", "P01", "D01", "P02", "P03"):
    made_before_d02 |= set(by_id[ident]["outputs_absent_before"])
made_before_d02 |= {records("mr-001-d02-check-prepared")["stdout"], records("mr-001-d02-check-prepared")["stderr"]}
after = sorted(set(s7_paths) - made_before_d02 - {records("mr-001-d02-check-prepared")["exit"],
                                                  records("mr-001-d02-check-prepared")["command"]}) + ALWAYS_ABSENT
for path in before + after:
    assert not os.path.lexists(path), path

deferred_inputs = [{"id": "config:readback-config-001.json", "path": CONFIG,
                    "role": "R1's readback configuration (config/0.2.0); its digest is not in this freeze (A6): the Director "
                            "takes it from the freeze review record; the checker records the bytes' digest and checks these "
                            "requirements",
                    "requirements": [
                        {"pointer": "/schema", "equals": "ontokin.current-host-readback-config/0.2.0"},
                        {"pointer": "/contract", "equals": "ontokin.current-host-readback/0.2.0"},
                        {"pointer": "/source/root", "equals": W}, {"pointer": "/source/commit", "equals": B},
                        {"pointer": "/source/tree", "equals": TREE},
                        {"pointer": "/source/inventory/sha256", "equals": SRC_INVENTORY_SHA},
                        {"pointer": "/source/inventory/path", "equals": P + "/workers/W2-plan-001/source-inventory-001.json"},
                        {"pointer": "/host/path", "equals": E + "/observe-001/HOST.json"},
                        {"pointer": "/host/sha256", "equals": "858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666"},
                        {"pointer": "/host/size_bytes", "equals": 18420}, {"pointer": "/host/mode", "equals": "0o600"},
                        {"pointer": "/amendment_adoption/sha256", "equals": "872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937"},
                        {"pointer": "/amendment_adoption/size_bytes", "equals": 5396},
                        {"pointer": "/amendment_adoption/mode", "equals": "0o644"},
                        {"pointer": "/dependencies/inventory/sha256", "equals": "3545d5f920ac840804a9e25d28a87d623f96af71537fd3f020a0c1d743f82fb4"},
                        {"pointer": "/dependencies/root", "equals": L + "/c271-macos/reader-c195"},
                        {"pointer": "/runtime", "equals": {"executable": L + "/c271-macos/node-v24.22.1-darwin-arm64/bin/node",
                                                           "version": "v24.22.1"}},
                        {"pointer": "/methods/path", "equals": F + "/config/methods-001.json"},
                        {"pointer": "/methods/sha256", "equals": sha256_file(F + "/config/methods-001.json")},
                        {"pointer": "/evidence_root", "equals": A1}, {"pointer": "/parent", "equals": None}]}]
preparation = {"entries": [{"id": "prepared:attempt-r1-root", "path": A1, "kind": "directory", "mode": "0o755", "entries": []}],
               "by": "D01", "note": "D02 checks it exists, empty, with mode 0o755; R1's driver creates driver/ in it, and the "
                                    "provider's cohort appears in it as current-host-cpu-<8> and then -preserved-<32 hex>"}

# ---------------------------------------------------------------------------------------------------------
# The freeze document
# ---------------------------------------------------------------------------------------------------------
ORDER = ["P00", "P01", "D01", "P02", "P03", "D02", "R1", "R1.L", "R1.I", "R1.F", "R1.P", "R1.C", "R1.K", "R1.A", "R1.R", "R1.M",
         "R1.X", "R1.Y", "R1.Z", "R2", "R2.L", "R2.I", "R2.C", "R2.K", "R2.V", "R2.M", "R2.X", "R2.Y", "Q01", "Q01.X", "Q04"]
assert sorted(ORDER) == sorted(r["id"] for r in COMMANDS if r["phase"] != "overrun")
spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "w2f_freeze_text.json")))
document = {
    "schema": "ontokin.c271.p36-operational-freeze/1", "id": "MR-FREEZE-001", "attempt": "mr-001", "task": "C271",
    "phase": "C271-P36-macos-complete-routine-mr", "gate": "MR", "stage": "S6", "owner": "c271-p36-14f7f8b219db",
    "author": "W2 (freeze 001), a subagent in a fresh context with the session's model; it wrote none of the "
              "implementation, the contract, MP's preparation, MH's records, MR's tooling, the observation plan or HOST",
    "status": "FROZEN_NOT_RUN",
    "contract": {"id": "ontokin.current-host-readback/0.2.0", "design_revision": 4, "amendments": ["P33-AMENDMENT-001"],
                 "sections_cited": "7 to 11 (MC22, MC23, MC28, S8, the labels); section 10 for what no result here can support (HR-07)"},
    "candidate": {"commit": B, "tree": TREE, "worktree": W, "state": "clean at B with only .venv ignored (MR-PLAN section 6); "
                  "tree, index and cache facts as HOST-REVIEW-001 section 2.1 and HR-05 establish them"},
    "places": {"<worktree>": W, "<local>": L, "<E>": E, "<F>": F, "<A1>": A1, "<home>": HOME, "<framework>": FW,
               "<tmp:resolved>": TMP_RESOLVED, "<tmp:default>": TMP_DEFAULT,
               "note": "Exact record: it holds machine paths and this host's account values (HOME, USER, LOGNAME, the "
                       "per-user temporary directory). A portable copy replaces each by its label; the files stay beside the clone."},
    "boot_session_uuid": BOOT, "umask": "0o022",
    "evidence": {"parent": E, "ancestors": ancestors,
                 "devices": {"evidence": os.stat(E).st_dev, "temporary": os.stat(TMP_RESOLVED).st_dev,
                             "rule": "D-P6 and I-05: MC16 needs the driver output (on the clone's volume) and the temporary "
                                     "directory (on the system volume) on different volumes"}},
    "wrapper": {"path": WRAP, "sha256": "9154f181cfa7c8648c21b31a1f309af43f9b2b5046df1656a124a4b6b55e07a7", "size_bytes": 3629,
                "mode": "0o644", "rule": "HR-08: bound by path and SHA-256; its start_epoch_s, end_epoch_s and wall_time_s are "
                "the authoritative times, its second-resolution UTC strings are not; it starts no Python and retries nothing"},
    "environments": {name: {"file": env_files[name]["file"], "sha256": env_files[name]["sha256"],
                            "names": env_files[name]["names"]} for name in env_files},
    "configuration": {"path": CONFIG, "sha256": "deferred: FREEZE-REVIEW-001.json /configuration/sha256 (A6)",
                      "schema": "ontokin.current-host-readback-config/0.2.0",
                      "binds": ["source: root, B, tree and HOST's source-inventory descriptor, path included (HR-02)",
                                "host: HOST.json by path, SHA-256 858ef72a..., 18,420 bytes, 0o600 (HR-01)",
                                "dependencies: HOST's reader-tree root and inventory descriptor, path included (HR-02)",
                                "runtime: the pinned bin/node, v24.22.1",
                                "methods: methods-001.json, which binds discovery-001.json: the 5,994 IDs of B, sorted",
                                "contract_source and amendment_adoption (PR-06) of the worktree",
                                "evidence_root: R1's attempt directory, which D01 creates; parent: null"],
                      "author_check": "records/config-validation-001.json: every read-only check of the provider's _selection "
                                      "passed in the author's process, up to the first Git read, which was not started"},
    "bindings": bindings, "host_facts": host_facts, "trees": trees,
    "absent_paths": {"before_preparation": before, "after_preparation": after,
                     "note": "before_preparation leaves out P00's records and P01's; after_preparation leaves out everything "
                             "P00 to P03 and D01 make and D02's own records"},
    "deferred_inputs": deferred_inputs, "preparation": preparation,
    "post": {"not_rechecked": [], "consumed": []},
    "order": ORDER, "commands": COMMANDS,
    "deferred_arguments": spec["deferred_arguments"],
    "launch": spec["launch"], "overrun": spec["overrun"], "stop_rules": spec["stop_rules"],
    "failure_capture": spec["failure_capture"], "starts": spec["starts"], "expected_outcomes": spec["expected_outcomes"],
    "attributions": {"r1": {"path": ATTR1, "sha256": sha256_file(ATTR1), "rows": len(json.load(open(ATTR1))["attributions"])},
                     "r2": {"path": ATTR2, "sha256": sha256_file(ATTR2), "rows": len(json.load(open(ATTR2))["attributions"])},
                     **spec["attributions"]},
    "decisions": spec["decisions"], "carried_findings": spec["carried_findings"], "fixed_state": spec["fixed_state"],
    "limits": spec["limits"], "open_questions": spec["open_questions"]}
data = (json.dumps(document, indent=1, sort_keys=False, ensure_ascii=True) + "\n").encode("ascii")
write_new(FREEZE_PATH if OUT == F else OUT + "/FREEZE-001.json", data)
print(json.dumps({"commands": len(COMMANDS), "bindings": len(bindings), "absent_before": len(before),
                  "absent_after": len(after), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}))
