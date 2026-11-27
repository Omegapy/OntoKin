"""W2 freeze author: compose the closed document FREEZE-001.json from generate-001.json and the decisions.

Run with <worktree>/.venv/bin/python -I -S -B. Standard library only; starts nothing; writes one absent file.
Usage: w2f_compose.py GENERATE_RECORD OUTPUT
"""
import hashlib
import json
import os
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(PermissionError(event)) if event in PROCESS_EVENTS else None)

record_path, output = sys.argv[1], sys.argv[2]
record = json.load(open(record_path))
LOCAL = "<local>"
E = LOCAL + "/c271-p35/evidence"
OUT = LOCAL + "/c271-p35/workers/W2-freeze-001"
WT = "<worktree>"
BOOT = "C90010BA-4DA9-475D-BBAB-CF1A9C40175A"
plan001 = json.load(open(LOCAL + "/c271-p35/workers/W2-plan-001/observation-plan-001.json"))
host = json.load(open(E + "/observe-001/HOST.json"))
commands = record["all_commands"]
by_id = {row["id"]: row for row in commands}


def count_python(rows):
    return sum(1 for row in rows if any(item.endswith("/.venv/bin/python") for item in row["argv"]))


s7_rows = [row for row in commands if row["phase"] == "s7"]
main_ids = [row["id"] for row in s7_rows if "." not in row["id"]]

controls = [
    {"id": "MC01..MC05", "route": "preparation", "at_MH": "NOT_RUN", "reason": "MI's frozen controls ran at MI (full); MP's real "
     "preparation is retained unchanged; MH-PLAN section 6 assigns none of them to MH"},
    {"id": "MC06", "route": "M0", "at_MH": "NOT_RUN in S7", "reason": "MI full; the real load commands were accepted by M0 at S5 "
     "(HOST runtime.macho, N34-M); not rerun"},
    {"id": "MC07, MC08", "route": "M0", "at_MH": "NOT_RUN in S7", "reason": "MI full; M0's real environment and platform checks "
     "passed at S5; P02 to P04 (static) pass them again, zero starts"},
    {"id": "MC09", "route": "provider", "at_MH": "real (positive direction)", "commands": ["C02", "C17"],
     "expected": "the provider's real host_state equals HOST: host-state EXPECTED (C02); setup.json boot and every ledger's "
     "boot_before and boot_after carry the boot with labels.boundary real (C17); the change cases stay MI's (simulated)"},
    {"id": "MC10", "route": "M1", "at_MH": "mocked (command boundary), real static bindings", "commands": ["C03", "C04", "C05"],
     "expected": "v24.22.0\\n and v24.22.1 without the newline refused at OUTPUT with no HOST and no completion; v24.22.1\\n "
     "accepted, HOST labelled mocked with runtime v24.22.1; zero process starts; only the harness's own __main__ row excluded "
     "(T-01, accepted by review 001 Q7)"},
    {"id": "MC11", "route": "static", "at_MH": "real", "commands": ["C01"],
     "expected": "the frozen rule passes (no process-creation name, 587 dynamic hits all reviewed, the one-line specifiers "
     "equal), the wider scan finds no process creation in any view, the reviewed list matches, no unresolved relative "
     "specifier; the limit of a name scan stays stated"},
    {"id": "MC12..MC17", "route": "supervisor, preparer", "at_MH": "NOT_RUN", "reason": "MI's frozen controls (full at MI); "
     "not assigned to MH"},
    {"id": "MC18, MC19", "route": "dependencies, source", "at_MH": "NOT_RUN as controls", "reason": "MI full; the real detectors "
     "accept the unchanged reader tree and source in every selection check of C06, C07 and C17 (positive direction only)"},
    {"id": "MC20..MC22", "route": "paths, selection", "at_MH": "NOT_RUN", "reason": "MI full; not assigned to MH"},
    {"id": "MC23", "route": "selection", "at_MH": "NOT_RUN", "reason": "MR's (a real qualifying run); the provider's own "
     "accounting of a missing method (F-05) runs for real in C07 (accounting refused: 'Completed cohort is missing or has extra "
     "checker attempts') and in C17 (accounting passes with exactly three ledgers); MC28 is MH's control for the inventory"},
    {"id": "MC24", "route": "original", "at_MH": "real", "commands": ["C17", "C18"],
     "expected": "Q01 and Q03 positive: both readers read the actual bytes, every row passes, the result is written and synced, "
     "exit 0; two Node starts; recomputed by C18 and by the S8 audit"},
    {"id": "MC25", "route": "original", "at_MH": "real", "commands": ["C17", "C18"],
     "expected": "Q01 changed reference: exit 1 with exactly the intended matrix_0_3 finding at equipment-tray/pair/left/base "
     "(difference 0.001 within 1e-9, threshold 5e-6); one Node start"},
    {"id": "MC26", "route": "original", "at_MH": "mocked (as the original seams)", "commands": ["C17"],
     "expected": "the four coordinator seams keep their original outcomes; zero starts"},
    {"id": "MC27", "route": "direct negatives", "at_MH": "real", "commands": ["C16"],
     "expected": "P06-H01: exit 1, stderr holds 'CH-SELECTION: manifest digest is not external approval', no probe.json; "
     "P06-H02: exit 1, stderr holds 'Current-host binding: wrong configuration contract/schema', no probe.json; one Node "
     "start each, refusal in approvedEnvelope before any reader import (P07 section 5's source-backed inference)"},
    {"id": "MC28", "route": "discovery", "at_MH": "real", "commands": ["C08", "C09", "C10", "C11", "C12", "C13", "C14"],
     "expected": "baseline 5,587 IDs at 1c2f25ba, current 5,994 at C, exact match with the 407 approved additions of "
     "INVENTORY-ADDITIONS.json (f710dbb5...); no import failure, process event, duplicate or bytecode"},
    {"id": "MC29", "route": "time of use", "at_MH": "mocked (supervisor recorder) with the real detectors",
     "commands": ["C06", "C07"],
     "expected": "configuration change: attempt CH-SELECTION, accounting CH-SELECTION (the 0.2.0 provider, bound by D-20); "
     "job-input change: attempt CH-JOB, accounting CH-EVIDENCE; zero supervisor and on_started calls, zero Node events",
     "not_run_cases": "the source, runtime, dependency and OS-build cases stay as MI ran them (simulated): a real source "
     "change is possible only through a derived workspace (the driver's Git workspace preparation), a cost decision; a real "
     "runtime or dependency change would alter MP's retained trees; a real OS-build change is impossible (T-02, TR-14)"},
    {"id": "MC30", "route": "environment", "at_MH": "real", "commands": ["C17", "C19"],
     "expected": "M0 accepted the variable with 0x1F5:0x0:0x0 (S5, HOST); the provider's HOST comparison accepts it (C17); the "
     "probe's positive starts accept it (C17's Q01 and Q03 positive); MC30-probe (C19) refuses with 'actual Node environment "
     "differs' under a HOST copy that records null, which shows the variable reached Node's process.env; the case without "
     "the variable stays MI's mocked case"},
    {"id": "MC31", "route": "environment", "at_MH": "NOT_RUN as itself", "reason": "MI full; its probe-side instance on the real "
     "Node is MC36"},
    {"id": "MC32", "route": "Python", "at_MH": "NOT_RUN as a control", "reason": "MI full; the frozen inventory is rechecked "
     "for real by P02 to P04, by every provider selection check and by Q01 (positive direction)"},
    {"id": "MC33..MC35", "route": "configuration, dependencies, installation", "at_MH": "NOT_RUN",
     "reason": "MI full; not assigned to MH"},
    {"id": "MC36", "route": "direct negative", "at_MH": "real, after MC30-probe", "commands": ["C19"],
     "expected": "a HOST copy recording 0x1F5:0x8000100:0x0: exit 1, probe.json error.message 'Current-host binding: actual "
     "Node environment differs', passed false, no khronos or three member; before any reader import (T-03); tied to the "
     "cohort's positive starts and MC30-probe (N-04)"},
    {"id": "MC37", "route": "supervisor", "at_MH": "real", "commands": ["C15"],
     "expected": "group_exists true while the test's direct child is exited and unreaped (raw answer not ESRCH) and false "
     "after reaping (ESRCH); one other start"},
    {"id": "MC38, MC39", "route": "supervisor", "at_MH": "NOT_RUN", "reason": "MI full (real); not assigned to MH"},
    {"id": "probe-syntax-check", "route": "contract section 7 minimal path", "at_MH": "real", "commands": ["C16"],
     "expected": "exit 0 with empty stdout and stderr: the first parse of the 0.2.0 probe by the bound Node"},
    {"id": "F-04", "route": "MI finding", "at_MH": "real", "commands": ["C02", "C17"],
     "expected": "both: the host-state harness (nothing substituted) and the cohort's own reads (T-08)"},
    {"id": "P07 section 6 numerical audit", "route": "audit", "at_MH": "real (zero starts)", "commands": ["C18"],
     "expected": "audit_numeric.py passed: 2,060 rows per case recomputed, positives all pass, the negative exactly one "
     "failed row and one finding; S8 recomputes again"}]

totals = {
    "counting_rule": "P07 section 4 unchanged: a subprocess.Popen audit event shows an attempt; a receipt with a positive PID "
                     "establishes a start; an interrupted attempt is UNKNOWN and blocks success and any automatic retry",
    "rows": [
        {"row": "M0, Git --version", "node": 0, "other": 1, "where": "S5 (done; receipt PID 7994)"},
        {"row": "M1, Node --version", "node": 1, "other": 0, "where": "S5 (done; receipt PID 7995; 1,109.748 ms, HR-07)"},
        {"row": "Probe syntax check", "node": 1, "other": 0, "where": "C16 row 1"},
        {"row": "P06-H01", "node": 1, "other": 0, "where": "C16 row 2"},
        {"row": "P06-H02", "node": 1, "other": 0, "where": "C16 row 3"},
        {"row": "CPU trio (MC24, MC25)", "node": 3, "other": 0, "where": "C17"},
        {"row": "Coordinator quartet (MC26), mocked", "node": 0, "other": 0, "where": "C17"},
        {"row": "The contract's minimal path", "node": 7, "other": 1},
        {"row": "MC37", "node": 0, "other": 1, "where": "C15"},
        {"row": "MC30-probe", "node": 1, "other": 0, "where": "C19 row 1", "added": True,
         "reason": "T-04 and N-04: no tool can read Node's process.env, so only a discriminating probe start shows that "
                   "__CF_USER_TEXT_ENCODING reached Node; without it MC36 must stay NOT_RUN. Review 001 and disposition 001 "
                   "accepted the design, its ninth Node start and MC36's order after it"},
        {"row": "MC36", "node": 1, "other": 0, "where": "C19 row 2"},
        {"row": "Expected for MH", "node": 9, "other": 2}],
    "mh_plan_table": {"node": 8, "other": 2, "difference": {"node": 1, "other": 0, "row": "MC30-probe"}},
    "already_used_at_S5": {"node": 1, "other": 1},
    "s7_bounded": {"node": 8, "other": 1, "by_command": {"C16": {"node": 3}, "C17": {"node": 3}, "C19": {"node": 2},
                                                          "C15": {"other": 1}}},
    "s7_bounded_if_r2_does_not_run": {"node": 6, "other": 1},
    "recorded_not_bounded": {
        "provider_bound_git_reads": {"C06": 15, "C07": 25, "C17": 60, "total": 100,
                                     "basis": "each provider selection check makes five bound Git reads (rev-parse x3, status, "
                                              "ls-files) through check_local.git_read with a timeout of at most 5 s; 2 at "
                                              "setup, 3 per case, 1 at the accounting (W5-PROVIDER section 9, T-07, TR-14); "
                                              "recorded by the collector's and the harness's audit hooks, never supervised"},
        "director_git_reads": {"P05": 1, "C08": 1, "C10": 1, "Q03": 1, "total": 4},
        "tar_extractions": {"C09": 1, "C11": 1},
        "python_launchers": count_python(commands),
        "shell_and_env_launchers": "one /bin/sh (the wrapper) and one /usr/bin/env per command (" + str(len(commands)) +
                                   " commands); the prepare script's mkdir and cp; the wrapper's own jq, shasum, perl, date, "
                                   "sysctl, cut and stat",
        "simulated_not_started": "MC10's six answers at the mocked command boundary (two per case) start nothing"},
    "never_started": ["ldd", "codesign", "otool", "the observer's observe", "Node outside C16, C17 and C19"]}

general_classes = {
    "PLAN": "a value, path, fixture, predicate or command of this freeze is wrong, or a tool cannot run a control as frozen. "
            "The attempt is kept; a corrected freeze 002 is frozen and reviewed; the new attempt uses a new attempt ID and fresh "
            "absent paths, lists this attempt as retained, and counts its starts (MH-PLAN section 8, FC-R3)",
    "IMPLEMENTATION": "the code under test (observer, provider, facade, probe, Darwin supervisor, test module) behaves against "
                      "the contract or the inspected source. MH stops; a change belongs to a later implementation phase",
    "CONTRACT": "a premise of the contract or of P33-AMENDMENT-001 does not hold on this host (D-16's variable, the group "
                "probe, contract section 5's no-descendant property, Node's behaviour assumption). MH stops for the affected "
                "obligation; an amendment is needed",
    "INPUT/HOST": "a bound input or host fact changed (the worktree, HOST, the Python trees, MP's trees, the CF file, the OS). "
                  "The attempt ends; the Director reconciles; a reboot restarts S4 with new records (FC-R5)",
    "UNKNOWN": "FAILURE-CAPTURE section 2: killed, interrupted, timed out, a missing final record, disagreeing records, a null "
               "or bounded start count. It blocks success and every retry; it is never relabelled"}

stop_rules = [
    "Before S7: P01 to P05, D01 and D02 must each end with exit 0 and their predicates met (D02 evaluates P01 to D01 again). "
    "Otherwise S7 does not begin and no Node starts.",
    "Order: the commands run strictly in the order given by 'order', each exactly once, through the bound wrapper, with the "
    "frozen argv, cwd and environment file. A command's .L (FC-K5 listing), then its .P (FC-P3 probe) where it has one, then "
    "its .X (the checker's 'expect') follow it before anything else.",
    "Continue only when the .X command ends with exit 0 and prints state MET. Any other outcome of a command, its .L, .P or .X "
    "stops S7: start no other command except FAILURE-CAPTURE section 6 steps 3 to 5 (an FC-P6 stop only for a target 'present, "
    "identity established'), write the capture record (section 8, schema ontokin.c271.p35-failure-capture/1) by exclusive "
    "creation beside the attempt, and apply the command's classification. The capture record is the Director's.",
    "Within a runner command, rows_independent is false (R1 and R2): a row that misses its predicates stops the later rows, "
    "and an unknown row stops every later row (the runner's own rule).",
    "Remaining Node starts stop at the first deviation: every Node-starting command (C16, C17, C19) requires every earlier "
    "command's expectation met (MH-PLAN section 8). No row or command is declared independent.",
    "MC36 runs only after the cohort's positive starts (C17) and MC30-probe (C19 row 1) met their predicates (N-04).",
    "No retry, by anyone or anything (FC-R1 to FC-R5). A reboot ends the attempt (FC-R5).",
    "TR2-01: any interruption of a runner command makes that command UNKNOWN, whatever run.json says; each row's own "
    "outcome.json is kept as written.",
    "Outer bound: a command still running after its limits.outer_bound_s is interrupted once (SIGINT to its foreground group, "
    "as Ctrl-C does), recorded UNKNOWN, and FAILURE-CAPTURE section 6 applies. The Director launches each wrapper call so that "
    "nothing else ends it earlier (a tool timeout at least 600 s).",
    "Wrapper exit 90 (refused before the start: a record path exists, or the argv encoding) means the command did not run: "
    "PLAN, stop. Wrapper exit 91 or 92 (the command ran once, the record was not built or written): the command's outcome is "
    "read from its own records, the FC-K3 record is written by hand from the wrapper's printed line under a new name (as for "
    "S5's static run, HR-01), and the outcome stays UNKNOWN unless every other record agrees.",
    "After S7 ends (C19.X MET, or a stop and its capture record), the Director runs Q01 to Q04 once, in order; they start "
    "nothing bounded."]

failure_capture = {
    "procedure": {"path": WT + "/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/FAILURE-CAPTURE.md",
                  "sha256": "f387fb3ec0ed306366f6d3f22820ec344f1ac843008775475258c5de9634c99c", "size_bytes": 13147,
                  "mode": "0o644", "version": 2},
    "per_command": "FC-K1: nothing in an attempt directory, the evidence parent, MP's inputs, this freeze or the worktree is "
                   "changed, except what a frozen command writes (MC29's configuration case appends one space to its own "
                   "prepared copy by design). FC-K2 and FC-K3: the bound wrapper writes <name>.stdout.txt, .stderr.txt, "
                   ".exit.txt and .command.json beside the attempt, with the argv, cwd, the environment file's SHA-256, the "
                   "epoch fields (authoritative, HR-01), the UTC strings and the boot before and after. FC-K4: each "
                   "command's own records (named in its outputs). FC-K5: the .L command (capture_probe.py listing) of "
                   "every command that names outputs, immediately after it, before any other command touches the evidence; "
                   "commands that name no output (P01 to P05, D01, D02, the .X checks, Q03, Q04) have FC-K2 and FC-K3 as "
                   "their records. FC-P3: the .P command for every command with started records (C16, C17, C19), even after "
                   "a success, as in S5.",
    "pairs": {"runner": "<output>/<row>/intent.json and <output>/<row>/started-1.json",
              "provider": "<cohort root>/provider-ledgers/<case>/preflight.json and started.json"},
    "no_pair": "C15's Python child (the test's own Popen) and the provider's Git reads (check_output) have no started record, "
               "so FC-P3 cannot probe them; the collector's audit hook records each attempt, the test's teardown reaps its "
               "child and fails when it stays present, and check_output waits for each Git read",
    "tr2_04_limits": "the readback (capture_probe.py listing) can leave out an unreadable directory's entries without a "
                     "record, and the probe cannot tell an exited, unreaped process from a live process whose identity is not "
                     "established; in either case the outcome stays UNKNOWN and nothing is sent (disposition 002)",
    "fc_p5": "a descendant that moved to another process group or session is not found by the group probe; MC11 is the only "
             "evidence against such descendants (contract section 5)",
    "capture_record": "after an outcome other than MET, the Director writes the section 8 record "
                      "(<name>.failure-capture.json beside the attempt) by exclusive creation"}

carried = [
    {"id": "TR-14", "source": "TOOLING-REVIEW-001, disposition 001", "met_by": [
        "the provider's bound Git reads are listed as recorded, unbounded starts: 60 in the cohort, 15 and 25 in the two mc29 "
        "cases (totals.recorded_not_bounded, each command's starts)",
        "MC29's scope is stated (controls MC29): configuration and job input real; the source case possible only through a "
        "derived workspace; runtime, dependency and OS build stay simulated",
        "each mc29 case has its own configuration at its own path (" + record["mc29_copy"]["configuration"] + " and " +
        record["mc29_copy"]["job-input"] + ", prepared copies), its own evidence root and its own frozen environment file "
        "with that copy's selection pair"]},
    {"id": "TR2-01", "source": "TOOLING-REVIEW-002, disposition 002", "met_by": [
        "stop_rules: an interrupted runner command is UNKNOWN whatever its verdict; each row's outcome.json is kept"]},
    {"id": "TR2-02", "source": "TOOLING-REVIEW-002, disposition 002", "met_by": [
        "tools.evidence_against_rejected_001: cited with its limit"]},
    {"id": "TR2-03", "source": "TOOLING-REVIEW-002, disposition 002", "met_by": [
        "the MC11 candidate list's notes record both route classes (the Function constructor through .constructor or "
        "Reflect.construct, and computed members of the global objects) with review 002's cross-check and this author's own "
        "advisory count, under the stated limit; the reviewer records them in the reviewed list"]},
    {"id": "TR2-04", "source": "TOOLING-REVIEW-002, disposition 002", "met_by": ["failure_capture.tr2_04_limits"]},
    {"id": "TR2-05", "source": "TOOLING-REVIEW-002, disposition 002", "met_by": [
        "every frozen command that starts the framework interpreter carries -B on its command line (checked for every command "
        "by the author's self-check, author/records/selfcheck-002.txt); the tools' -B refusal relies on the frozen "
        "framework's bytecode set (review 002 measured no write), and P02 to P04, the provider's checks and Q01 detect any "
        "write"]},
    {"id": "TR2-06", "source": "TOOLING-REVIEW-002, disposition 002", "met_by": [
        "C06 expects finish_error CH-SELECTION and C07 finish_error CH-EVIDENCE; the attempt codes CH-SELECTION and CH-JOB",
        "deviation, stated: at C the facade keeps the version that setup bound until the accounting has run (D-20, facade "
        "lines 1161 to 1217; CONTROLS-REFREEZE-002's added MC29 case), so the configuration case's CH-SELECTION comes from the "
        "0.2.0 provider, not from the 0.1.0 code that F-07 describes; C06 also expects cohort.json as cohort/0.2.0 with "
        "error.code CH-SELECTION (open question Q1)"]},
    {"id": "TR3-03", "source": "TOOLING-REVIEW-003, disposition 003", "met_by": [
        "every --root and bound path is given in its on-disk spelling: each component checked against its parent's listing "
        "(author/records/bind-001.json; the checker repeats it for every binding in P01, D02 and Q04)"]},
    {"id": "PR-01", "source": "PLAN-REVIEW-001, disposition", "met_by": [
        "every configuration's amendment_adoption binds " + WT + "/docs/engineering/localized-repair-c271/"
        "macos-implementation-p33/ADOPTION-AMENDMENT-001.json: SHA-256 872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937, "
        "5,396 bytes, 0o644 (blob 0431fab5 at C, per plan review 001)"]},
    {"id": "PR-03, HR-03", "source": "PLAN-REVIEW-001, HOST-REVIEW-001", "met_by": [
        "the owner's launchd job (PID 1304) runs the framework interpreter with PYTHONDONTWRITEBYTECODE=1 and without -B; it "
        "stays as it is unless the owner pauses it; the inventory is rechecked immediately before S7 by P02 to P04 (the "
        "observer's static compares the Python installation with the frozen inventory, c277bdd3...), during S7 by every "
        "provider selection check, and after S7 by Q01"]},
    {"id": "HR-01", "source": "HOST-REVIEW-001", "met_by": [
        "the wrapper is bound (bindings 'wrapper:run_once_v2.sh'); its epoch fields are the authoritative times; S5's static "
        "record is observe-001.static.command-record.json, its empty observe-001.static.command.json retained unchanged"]},
    {"id": "HR-02", "source": "HOST-REVIEW-001", "met_by": ["host_facts: <home>/.CFUserTextEncoding, unbound, rechecked by "
                                                            "P01, D02 and Q04; the owner keeps the language and region "
                                                            "settings unchanged until MH ends"]},
    {"id": "HR-04", "source": "HOST-REVIEW-001", "met_by": ["host: HOST bound with completion.json (state OBSERVED_UNAPPROVED) "
                                                            "and result.json"]},
    {"id": "HR-05, HR-06", "source": "HOST-REVIEW-001", "met_by": ["limits: contract section 10's full list is cited; HOST's "
                                                                   "claims are not read as complete; HOST review 001 is "
                                                                   "cited for commit C's tree, the index and the cache facts"]},
    {"id": "HR-07", "source": "HOST-REVIEW-001", "met_by": ["M1's 1,109.748 ms of its 3,000 ms is the timing evidence for "
                                                            "bin/node; the rows keep the 30,000/28,000/2,000 ms clock"]},
    {"id": "N-04", "source": "N34-M-DISPOSITION", "met_by": ["n04"]}]

decisions = [
    {"item": 1, "subject": "MC10 (F-01)", "decision": "Run, with T-01's declared exclusion (only the harness's own __main__ "
     "row), labelled mocked: C03 (v24.22.0\\n, refused-output), C04 (v24.22.1 without the newline, refused-output), C05 "
     "(v24.22.1\\n, accepted). One observation plan per case (mc10/observation-plan-mc10-a/b/c.json), each plan 001 with "
     "only the attempt, its output topology and the two cwds changed, each attempt absent under the evidence parent. The "
     "simulated Git line is HOST's real line. The four --bind digests are the observer's files; the harness is bound.",
     "source": "TOOLING-AUTHOR-NOTES T-01; TOOLING-REVIEW-001 Q7; CONTROLS-FROZEN MC10"},
    {"item": 2, "subject": "MC29 (F-03)", "decision": "Run both possible cases with the real detectors: configuration "
     "(C06) and job input (C07), each on its own prepared copy of its own configuration (its own evidence root), with "
     "fixtures/Q01/synthetic.glb and synthetic-audit.json. Expected: attempt CH-SELECTION / CH-JOB, accounting CH-SELECTION "
     "/ CH-EVIDENCE. The source, runtime, dependency and OS-build cases stay simulated as MI ran them.",
     "source": "T-02, T-11, TR-14, TR2-06, D-20"},
    {"item": 3, "subject": "F-04", "decision": "Both: the host-state harness (C02, nothing substituted) and the cohort's own "
     "reads (C17: setup.json boot, every ledger's boot_before and boot_after, labels.boundary real).", "source": "T-08"},
    {"item": 4, "subject": "MC30's probe part and MC36", "decision": "Add MC30-probe (T-04): its HOST copy records "
     "cf_user_text_encoding null, its job binds the SHA-256 of the empty string as the GLB digest; with the variable present "
     "it refuses 'Current-host binding: actual Node environment differs', without it 'Actual input identity differs', both "
     "in probe.json before any reader import. MC36 follows it in R2 with rows_independent false, after the cohort's positive "
     "starts. Nine Node starts for MH.", "source": "T-04, N-04, TR-10, disposition 001"},
    {"item": 5, "subject": "The unit process", "decision": "Launcher <worktree>/.venv/bin/python, flags -B only, cwd "
     "<worktree>; exact environment PATH=/usr/bin:/bin, LANG=C.UTF-8, LC_ALL=C.UTF-8, TZ=UTC, TMPDIR (a prepared, "
     "resolved directory of this attempt, no final slash), PYTHONDONTWRITEBYTECODE=1, PYTHONNOUSERSITE=1, the selection pair, "
     "and STATIC_TRAY_READBACK_CPU_OUTPUT (an absent path inside the configuration's evidence root, so the cohort stays in "
     "place with no temporary copy); no GIT_* name (the provider's git_read sets its own); no HOME. --module-sha256 "
     "6295e044... and the methods document config/methods-001.json with original_bodies. MC37 rerun: the same base without "
     "selection and without the override, its own TMPDIR, the method "
     "SupervisorProcessControls.test_mc37_exited_unreaped_direct_child_counts_as_present_until_it_is_reaped, module "
     "3b8c91b7... (CONTROLS-REFREEZE-002).", "source": "T-05, TR-06, TR-09, W4-DRIVER section 2, W5-PROVIDER section 3"},
    {"item": 6, "subject": "The direct-probe rows", "decision": "Schema /2, two documents: R1 (probe-syntax-check with "
     "Node's two flags, P06-H01, P06-H02) before the cohort, R2 (MC30-probe, MC36) after it, both rows_independent false. "
     "Each row in its own stage: the H01, H02, MC30 and MC36 stages are <evidence root>/cohort/Q01-positive, each with "
     "exactly job.json, synthetic.glb and synthetic-audit.json, all inputs; the syntax stage is empty. Limits 30,000 and "
     "28,000 ms. Predicates exact where they can be: the supervisor error of status 1, stdout exact, stderr includes and "
     "excludes for H01 and H02, json_members on probe.json for MC30-probe and MC36 (T-03).",
     "source": "TR-02, TR-03, TR-10, P07 section 5"},
    {"item": 7, "subject": "MC11", "decision": "mc11/MC11-CANDIDATE-LIST-001.json: schema /2, status 'CANDIDATE, NOT "
     "REVIEWED', all 25 entries (probe, loader, 23 other reader files) mechanically from one scan: 23 call names, 628 "
     "dynamic hits, 53 specifiers, the frozen rule's 587 dynamic entries and 30 one-line specifiers; per file the "
     "multi-line or non-statement specifiers separately, TR2-03's route classes and TR-11's 'url'. The reviewer reviews every "
     "entry and writes the REVIEWED list with its identity at " + record["mc11_reviewed"] + "; C01 binds it. The "
     "configuration's dependencies/0.2.0 inventory is plan 001's (3545d5f9...).", "source": "TR-11, TR-12, TR2-03, mc11_rule"},
    {"item": 8, "subject": "MC28", "decision": "Two Director's exports with the bound Git (git archive of 1c2f25ba and of C, "
     "with docs/), extracted with tar into prepared empty directories; two discoveries, each with its own frozen "
     "environment; the comparison against INVENTORY-ADDITIONS.json's 407. Predicted from MI's export and a clone of the "
     "worktree: baseline 5,587 (sorted SHA-256 bcc36ee7...), current 5,994 (32b2b861...), exact.", "source": "T-06, TR-06, TR-07"},
    {"item": 9, "subject": "The audit", "decision": "Cohort root " + E + "/s7-001-cohort/run (the provider's cohort in place: "
     "STATIC_TRAY_READBACK_CPU_OUTPUT leaves no temporary root and no preserved copy); the 1e-9 bound for 'about 0.001' is "
     "audit_numeric.py's declared bound (T-10); C18 records one run for S8.", "source": "T-10, P07 section 6"},
    {"item": 10, "subject": "Every tool's binding", "decision": "bindings 'tool:*': the nine files of tooling/ that S7 uses, "
     "each equal to authoring/TOOLING-SHA256SUMS.txt at C; capture_probe.py among them.", "source": "TR3-02 (section 8 of "
     "the notes supersedes section 1)"},
    {"item": 11, "subject": "TR-14", "decision": "carried_findings TR-14.", "source": "disposition 001"}]

n04 = {
    "rule": "MH-PLAN section 10: MC36 is tied to a positive probe start of this freeze that observed __CF_USER_TEXT_ENCODING "
            "with HOST's value (0x1F5:0x0:0x0); if none observed it, MC36 stays NOT_RUN pending an amendment of D-16.",
    "how_shown": [
        "C17: the cohort's Q01-positive and Q03-positive starts end with probe.json passed true (C17.X). verifyBootstrap's "
        "environmentAdmitted ran in each with HOST's recorded value, so Node's process.env was either exactly the declared "
        "environment or the declared environment plus __CF_USER_TEXT_ENCODING=0x1F5:0x0:0x0.",
        "C19 row 1, MC30-probe: the same bound executable, supervisor and declared environment, under a HOST copy that records "
        "null; its refusal 'Current-host binding: actual Node environment differs' (and not 'Actual input identity differs') "
        "shows that process.env was not exactly the declared environment.",
        "By elimination, Node's process.env held the declared environment plus __CF_USER_TEXT_ENCODING with HOST's value. "
        "The value is not read directly (T-04); the argument assumes the same environment in every start.",
        "C19 row 2, MC36, runs only then (the runner stops it otherwise, rows_independent false)."],
    "if_absent": "MC30-probe refusing with 'Actual input identity differs' shows the variable absent: R2 stops, MC36 stays "
                 "NOT_RUN pending an amendment of D-16 (CONTRACT class); the cohort's results stand.",
    "premise_at_link_level": "HOST runtime.macho command 14: LC_LOAD_DYLIB CoreFoundation (D-16 yes; N34-M; HOST review 2.4)"}

mh_plan_section_6 = [
    {"obligation": "N34-M", "met_by": "S2 (N34-M-DISPOSITION, accepted)"},
    {"obligation": "Whether bin/node links CoreFoundation (D-16)", "met_by": "yes, from HOST's load commands (command 14); "
     "MC36 runs, tied by N-04"},
    {"obligation": "MC10 with real static bindings (F-01)", "met_by": "C03 to C05"},
    {"obligation": "MC11 on the loader and the 24 reader files (F-09)", "met_by": "C01, with the reviewed list"},
    {"obligation": "MC24, MC25, MC26", "met_by": "C17 (and C18)"},
    {"obligation": "MC27", "met_by": "C16 rows 2 and 3"},
    {"obligation": "MC28 with the missing-method accounting (F-05)", "met_by": "C08 to C14; the provider's accounting in C17 and "
     "C07"},
    {"obligation": "MC29 with the real detectors (F-03)", "met_by": "C06 and C07"},
    {"obligation": "MC30 for the probe", "met_by": "C17's positive starts and C19's MC30-probe (n04)"},
    {"obligation": "MC36", "met_by": "C19 row 2, after MC30-probe"},
    {"obligation": "MC37 again", "met_by": "C15, one other start"},
    {"obligation": "The provider's real host_state (F-04)", "met_by": "both C02 and C17"},
    {"obligation": "W3's open questions and Q3", "met_by": "N34-M (S2) and M0 on the real files (S5); nothing in S7"},
    {"obligation": "A refused probe result's labels are unverified", "met_by": "the freeze and the audit read P06-H01 and "
     "P06-H02 from stderr, the exit status and the receipt, and MC30-probe and MC36 from probe.json, the exit status and the "
     "receipt (T-03); no predicate reads a refused result's labels, which the audit reports as found and unverified (W5 Q5)"},
    {"obligation": "The adoption record lies outside the source set", "met_by": "every configuration's amendment_adoption "
     "(PR-01); the provider (_selection) and the probe (verifySource) check it"},
    {"obligation": "-B", "met_by": "every frozen Python command line (TR2-05)"}]

limits = {
    "contract_section_10": ["a Linux x86-64 qualification", "the historical C199/C225 replay",
                            "a P05 Gate H for the Codex Node build",
                            "any statement that the ELF policies of /0.1.1 to /0.1.5 were exercised on a real host",
                            "N34 for the Linux loader, or N57",
                            "the original supervisor's Linux descendant-reaping guarantee, or any enforcement against descendants",
                            "a per-file closure of the macOS system libraries",
                            "durable storage beyond what fsync gives on macOS",
                            "a binding of files that libraries load at run time by their own logic"],
    "host_claims": "HOST's four claims are not complete: they omit the supervisor's descendant limit, fsync without "
                   "F_FULLFSYNC, and Git bound by bytes and a version grammar only (HR-06)",
    "this_freeze": ["if MH passes it qualifies the seven methods and the direct negatives on this executor only, with contract "
                    "section 10's labels; it is not MR, R03 or a release (MH-PLAN section 1)",
                    "a name scan cannot exclude every dynamic route (MC11)",
                    "the audit hooks do not see _posixsubprocess.fork_exec, a call through ctypes, or a lookup made before "
                    "the hook was installed (FC-P7)",
                    "the no-reader-import conclusion for the direct negatives is a source-backed inference (P07 section 5)",
                    "the value of Node's __CF_USER_TEXT_ENCODING follows only by elimination (n04)"],
    "host_review_facts": "HOST review 001 settles commit C's tree statically (" + host["source"]["tree"] + "), records the "
                         "index and the shared cache's identity (7a024959..., UUID F2E86C53-6052-388B-BA71-5A0C9B569413) and "
                         "dyld's (373fce2b...); HOST does not record them (HR-05)"}

tools = {
    "location": WT + "/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/",
    "list": "authoring/TOOLING-SHA256SUMS.txt (revision 3, 21 files) at commit C; the nine that S7 starts or reads are bound",
    "reviews": ["TOOLING-REVIEW-001 (rejected; disposition 001)", "TOOLING-REVIEW-002 (accepted; disposition 002)",
                "TOOLING-REVIEW-003 (accepted; disposition 003)"],
    "evidence_against_rejected_001": "tooling/tests/TEST-RUN-AGAINST-REJECTED-001.txt shows each fix's test failing against "
        "the rejected tooling, with TR2-02's limit: two of its listed sub-checks fail there for other reasons than the "
        "defect (the ROW-TARGET part of test_bound_inputs_and_row_shapes_refuse_before_any_start fails with the renamed rule "
        "ROWS, and the 'supervisor error not implied by the status' subtest fails because rows schema /1 has no such field); "
        "the other TR-02 and TR-03 tests fail for the defects (review 002's focused rerun)",
    "own_main": "each tool runs from its committed place with --root <worktree> in its on-disk spelling and admits exactly its "
                "own __main__ (TR-01, TR3-03); discovery's --root is an export, so it admits none",
    "new_in_this_freeze": ["s7/w2f_s7_check.py: the Director's checker (pre, prepared, expect, post); stdlib, starts nothing, "
                           "writes nothing, refuses a start without -I -S -B", "s7/prepare-s7-001.sh: the frozen preparation"]}

open_questions = [
    {"id": "Q1", "text": "TR2-06 attributes the configuration case's accounting refusal to the 0.1.0 code (F-07). At C the "
     "facade binds the version at setup (D-20), so the refusal is the 0.2.0 provider's CH-SELECTION, and cohort.json is "
     "cohort/0.2.0. C06 expects the 0.2.0 attribution. The reviewer should confirm from the facade's lines 1161 to 1217."},
    {"id": "Q2", "text": "probe-syntax-check expects stdout and stderr exactly empty. Node has never parsed the probe; a warning "
     "on stderr would miss the row and stop MH as IMPLEMENTATION. stderr_exact null would accept a warning."},
    {"id": "Q3", "text": "Node's ExperimentalWarning for --experimental-loader is expected on stderr but not observed; no "
     "predicate of H01, H02, MC30-probe or MC36 depends on stderr being otherwise empty."},
    {"id": "Q4", "text": "STATIC_TRAY_READBACK_CPU_OUTPUT is set for the cohort and the two mc29 cases, so the provider's cohort "
     "stays in place without a temporary root or a preserved copy. The driver's default path leaves it unset. The audit's "
     "root is the cohort root itself (TOOLING-AUTHOR-NOTES item 9 assumed the preserved copy)."},
    {"id": "Q5", "text": "MC28's current discovery runs on a fresh export of C, not on the worktree, so no discovery imports "
     "the worktree; C's clean state makes the two equal. A clone of the worktree would be the alternative."},
    {"id": "Q6", "text": "Four kinds of deferred argument remain, each with one source: the freeze's own SHA-256 (the review "
     "record), the reviewed MC11 list's SHA-256 (the disposition; the checker verifies it equals the file's), and the two "
     "discovery digests for C14 (the readbacks C12.L and C13.L)."},
    {"id": "Q7", "text": "The baseline prediction (5,587, bcc36ee7...) comes from MI's retained export "
     "(c271-p33/director/inventory/base-1c2f25ba), not from a fresh git archive; C12 classifies a difference as PLAN."},
    {"id": "Q8", "text": "P06-H02's unsupported schema is ontokin.current-host-readback-config/0.1.0, the other version's "
     "configuration schema with the 0.2.0 key set; P07 asks only for 'an unsupported schema'."},
    {"id": "Q9", "text": "Each probe row's inputs name every document it reads by descriptor (job, manifest, configuration, "
     "HOST, methods, discovery, both inventories, the contract and the adoption record) and every stage file, but not the "
     "source and reader files, which the probe itself verifies against the bound inventories."},
    {"id": "Q10", "text": "host-state (C02) runs as the unit process runs (-B, site imported, PYTHONNOUSERSITE=1), as the "
     "tooling's tests ran it, not under -I -S."},
    {"id": "Q11", "text": "The fixture bytes were built by the project's own builders (synthetic() and the reader's audit()) "
     "in the author's -I -S -B process; the cohort builds the same bytes at run time (C17's audit_expect compares them)."}]

document = {
    "schema": "ontokin.c271.p35-operational-freeze/1",
    "id": "FREEZE-001", "attempt": "s7-001", "task": "C271", "phase": "C271-P35-macos-host-qualification-mh", "gate": "MH",
    "stage": "S6 (this freeze), for S7", "owner": "c271-p35-e38e3aa82ade",
    "author": "W2, a Claude Code subagent in a fresh context with the session's model, the independent author of this freeze; "
              "it wrote none of the tooling, the observation plan, the observer, the provider, the probe, the contract, the "
              "amendment or MP's preparation",
    "status": "FROZEN_NOT_RUN: awaiting freeze review 001; nothing of it has run",
    "contract": {"id": "ontokin.current-host-readback/0.2.0", "design_revision": 4, "amendments": ["P33-AMENDMENT-001"],
                 "source": {"path": WT + "/docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md",
                            "sha256": "42db98dc6099ee605b0963f3734f7bff2d68c019ff6c00a0ee97bd753c03fdc9"},
                 "adoption_record": {"path": WT + "/docs/engineering/localized-repair-c271/macos-implementation-p33/"
                                     "ADOPTION-AMENDMENT-001.json",
                                     "sha256": "872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937",
                                     "size_bytes": 5396, "mode": "0o644"}},
    "fixed_state": {"commit": "0eb9a5517f4e19705178a2c59b8d8d33fb87867a", "tree": "ea10cd94c05a2ebbb44b3f83d4c96cb0a59baa2b",
                    "worktree": WT, "rule": "HEAD stays at C and the worktree clean (only .venv/ ignored) from S4 to the audit; "
                    "nothing committed, checked out, merged or edited; no Finder on the prepared trees, the evidence or the "
                    "worktree; nothing installed or downloaded; every start of the framework interpreter with -B; a reboot "
                    "ends the attempt (MH-PLAN section 5)"},
    "places": {"evidence_parent": E, "freeze": OUT, "worktree": WT, "local": LOCAL,
               "labels_in_notes": {"<worktree>": WT, "<local>": LOCAL, "<prefix>": "<prefix>", "<home>": "the owner's home"}},
    "host": {"HOST": {"path": E + "/observe-001/HOST.json", "sha256": "34e94f29ea1b7d9d60b389598b4ce5bc7eaf6fcaa58f3798fc3df021a8f28a92",
                      "size_bytes": 18420, "mode": "0o600"},
             "completion": {"path": E + "/observe-001/completion.json",
                            "sha256": "fd1a035065e758825ddff81671fec29380720ed03d20c9571a17d993089488fe", "size_bytes": 981,
                            "state": "OBSERVED_UNAPPROVED"},
             "result": {"path": E + "/observe-001/result.json",
                        "sha256": "1b4cae0f80cce491b200b5a24a1b5a75660af7889bb7120e98cec0a7080b2e1d", "size_bytes": 2621,
                        "state_inside": "PENDING_COMPLETION by design (HR-04)"},
             "review": "HOST-REVIEW-001 (68bc0841..., JSON 62a0ddf0...), ACCEPT_WITH_NONMANDATORY_FINDINGS; disposition 001",
             "facts": {"git_version_line": host["git"]["version"], "node_version": host["runtime"]["version"],
                       "core_foundation": "LC_LOAD_DYLIB CoreFoundation (command 14; D-16)",
                       "cf_user_text_encoding": host["environment"]["cf_user_text_encoding"],
                       "python_inventory_sha256": host["python"]["inventory_sha256"],
                       "m1_first_bin_node_execution_ms": 1109.748, "starts": host["starts"]}},
    "host_facts": [{"id": "host-fact:CFUserTextEncoding", "path": "<home>/.CFUserTextEncoding", "kind": "file",
                    "sha256": "bd605d2eae2bc28178ba94d69e189242f971d699c5846addae706d7e52bc69fd", "size_bytes": 7,
                    "mode": "0o400", "nlink_one": True, "bound": False,
                    "meaning": "HOST's value 0x1F5:0x0:0x0 is 0x + the UID 501 in hex + : + this file's content; it is not "
                               "bound by HOST; a change refuses every positive start under MC31's rule (HR-02); the owner "
                               "keeps the language and region settings unchanged until MH ends"}],
    "boot_session_uuid": BOOT, "umask": "0o022",
    "evidence": {"parent": E, "ancestors": plan001["evidence"]["ancestors"]},
    "trees": [{"root": WT, "exclude": [WT + "/.venv"], "bytecode": True},
              {"root": LOCAL + "/c271-macos/reader-c195"}, {"root": LOCAL + "/c271-macos/node-v24.22.1-darwin-arm64"},
              {"root": OUT}],
    "wrapper": {"path": LOCAL + "/c271-p35/director/run/run_once_v2.sh",
                "sha256": "3c24f923025f855603fce02a3e9fc794eb52409824369e53338f903ce9da8e1f", "size_bytes": 3601,
                "mode": "0o644",
                "invocation": "/bin/sh <wrapper> NAME CWD ENVFILE -- ARGV... (each command's wrapper_argv; its shell field "
                              "single-quotes every element)",
                "semantics": "it runs ARGV once in CWD, writes <evidence>/NAME.stdout.txt, .stderr.txt, .exit.txt and "
                             ".command.json by exclusive creation, refuses (exit 90) when one exists, hashes ENVFILE into the "
                             "record but does not apply it (each ARGV sets its own environment with /usr/bin/env -i), exits 0 "
                             "after one run whatever the command's status (in .exit.txt), 91 or 92 when the record could not "
                             "be built or written",
                "times": "start_epoch_s and end_epoch_s are authoritative; the UTC strings come from separate date calls "
                         "(HR-01)"},
    "environments": {name: {key: row[key] for key in ("path", "sha256", "size_bytes", "names", "environment")}
                     for name, row in record["environments"].items()},
    "configurations": {"approved_cohort": {**record["configs"]["cohort"], "D0": record["D0"]},
                       "mc29_sources": {"configuration": record["configs"]["mc29-configuration"],
                                        "job-input": record["configs"]["mc29-job-input"]},
                       "mc29_copies": record["mc29_copy"],
                       "methods": record["methods"], "discovery": record["discovery"],
                       "probe_rows": {name: {key: row[key] for key in ("root", "cohort", "stage", "config", "manifest", "job",
                                                                       "argv_digest", "artifact_sha256", "host")}
                                      for name, row in record["probe_rows"].items()},
                       "host_copies": record["host_copies"],
                       "mutations": {
                           "h01": "the approved configuration with evidence_root changed to its own root (one field); its "
                                  "digest D1 is the manifest's selection and the job's manifest is coherent; argv keeps D0",
                           "h02": "the approved configuration with its own evidence_root and schema "
                                  "ontokin.current-host-readback-config/0.1.0; its own digest is the negative-control-only "
                                  "comparator in argv; manifest and job coherent",
                           "mc30": "the approved configuration with its own evidence_root and host = a copy of HOST whose "
                                   "environment.cf_user_text_encoding is null; the job's artifact_sha256 is the SHA-256 of "
                                   "the empty string; everything else coherent",
                           "mc36": "the approved configuration with its own evidence_root and host = a copy of HOST whose "
                                   "environment.cf_user_text_encoding is 0x1F5:0x8000100:0x0; everything else coherent"},
                       "fixtures": record["fixtures"]},
    "bindings": record["bindings"],
    "deferred_inputs": [{"id": "mc11-reviewed-list", "path": record["mc11_reviewed"],
                         "requirements": [{"pointer": "/schema", "equals": "ontokin.c271.p35-mc11-reviewed/2"},
                                          {"pointer": "/status", "equals": "REVIEWED"},
                                          {"pointer": "/reviewer", "nonempty_string": True}],
                         "rule": "written by freeze review 001; its SHA-256, size and mode are recorded in the Director's "
                                 "disposition of that review; P01 reports them; C01 passes the SHA-256"}],
    "deferred_arguments": record["deferred_sources"],
    "preconditions": {
        "conditions": ["freeze review 001 accepted this freeze without a mandatory finding (A6), and its record gives "
                       "FREEZE-001.json's SHA-256 and the reviewed MC11 list", "the same boot (no reboot since S4)",
                       "the <volume-name> volume mounted, the host awake (keep-awake on), no other MH command running, no Finder",
                       "the Director's shell has umask 0022", "HEAD at C and the worktree clean (P05, and P02 to P04's "
                       "source checks)", "the owner's launchd job (PR-03, HR-03) as it is; the inventory recheck in P02 to P04",
                       "<home>/.CFUserTextEncoding unchanged (P01)"],
        "commands": [row["id"] for row in commands if row["phase"] == "precondition"]},
    "preparation": {"script": record["prep_script"], "entries": record["prepared_entries"],
                    "commands": [row["id"] for row in commands if row["phase"] == "preparation"],
                    "verification": "D02 (w2f_s7_check.py prepared): every entry exactly as frozen (modes, directory "
                                    "entries, file digests), every binding, every later output still absent, and P01 to D01's "
                                    "predicates"},
    "absent_paths": record["absent_paths"],
    "order": [row["id"] for row in commands],
    "commands": commands,
    "post": {"commands": [row["id"] for row in commands if row["phase"] == "post"], "not_rechecked": [],
             "consumed": record["consumed"],
             "note": "C06 consumes its prepared configuration copy (one space appended) by design"},
    "controls": controls, "totals": totals, "stop_rules": stop_rules, "classes": general_classes,
    "failure_capture": failure_capture, "carried_findings": carried, "decisions": decisions, "n04": n04,
    "mh_plan_section_6": mh_plan_section_6, "limits": limits, "tools": tools,
    "audit_inputs": {"cohort_root": E + "/s7-001-cohort/run", "bound": "1e-9 for 'about 0.001' (T-10, audit_numeric.py)",
                     "records": "every command's outputs and records; each command's audit_expect (w2f_s7_check.py expect "
                                "--audit) holds the recorded expectations that are not stop rules",
                     "m0_m1_basis": "M0's and M1's counts rest on the two receipts with positive PIDs (7994, 7995) and the "
                                    "observer's source, which installs no audit hook (HR-07)"},
    "open_questions": open_questions}
data = (json.dumps(document, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")
if os.path.lexists(output):
    raise SystemExit("output exists")
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
try:
    os.write(fd, data)
    os.fsync(fd)
finally:
    os.close(fd)
print(json.dumps({"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data), "commands": len(commands),
                  "s7_main": main_ids, "python_launchers": count_python(commands)}, sort_keys=True))
