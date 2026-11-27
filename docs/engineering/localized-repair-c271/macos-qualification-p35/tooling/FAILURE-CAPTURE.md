# Gate MH failure-capture procedure

Phase C271-P35, gate MH of `ontokin.current-host-readback/0.2.0` at design revision 4. Procedure
version 2, written by W2, the independent author of the MH tooling, and revised after tooling review
001 (TR-05, TR-08 and TR-16): identity is established before any signal, and the probes and the
listing are fixed as code, `capture_probe.py` in the tooling.

Every MH plan that names this procedure binds it by path, SHA-256, size and mode: the observation
plan's `failure_capture.procedure` and the operational freeze. A change makes a new file, which needs
its own review. Paths are written with the labels `<worktree>` and `<local>`.

## 1. Scope and terms

The procedure applies to every command that an MH plan freezes:

- the observer's `static` and `observe` (M0 and M1);
- the outcome collector (`collect_outcomes.py`, the cohort and the control reruns);
- the direct-probe runner (`run_direct_probe.py`);
- the control harness (`control_harness.py`);
- the discovery collector and its comparison, the MC11 scanner and the numerical audit.

A **command** is one frozen argv that the Director starts. An **attempt** is one run of one command,
with its own fresh output paths.

The procedure's own tool is `capture_probe.py`, beside the other MH tools and bound with them. Each
of its starts is `<worktree>/.venv/bin/python -I -S -B <tooling>/capture_probe.py COMMAND ...`,
recorded like every command (FC-K3). It imports nothing of the project, refuses every process
creation, reads `kern.bootsessionuuid` before and after, and writes one absent output file.

## 2. Outcomes

| Outcome | It holds when |
| --- | --- |
| Completed | The command exited with a status, and every record that its plan names exists and agrees with the others. |
| Refused | The command exited with its refusal status, and its records show that nothing started: a start count of `PROVEN_ZERO`, or a state of `REFUSED`, `REFUSED_BEFORE_START` or `FAILED_BEFORE_START`. |
| Failed | The command exited with a status and complete records, and an outcome differs from its frozen expectation. |
| Unknown | Anything else (below). |

An outcome is **unknown** in each of these cases:

- the command was killed, interrupted, timed out or lost with its terminal, or the host crashed or
  rebooted;
- it exited without its final record (for example a `journal.jsonl` without `outcomes.json`, or
  `intent.json` without `outcome.json`);
- its records disagree with each other;
- a start count is null, `UNKNOWN` or only a lower bound;
- a started record exists without a final receipt, or a receipt exists without cleanup proof.

An unknown outcome is never relabelled as refused or failed without the evidence that the table
asks for. It blocks the stage's success and every retry (P07 section 4).

## 3. What is kept

The same records are kept for every outcome, a completed one included.

- **FC-K1. Nothing is changed.** Nothing in an attempt directory, the evidence parent, the prepared
  inputs or the worktree is deleted, moved, renamed, truncated, edited, re-created or repaired.
  Partial and temporary files are kept as they are. Examples: the observer's `.<name>.<hex>.tmp`
  publication files, `setup.pending.json`, `finalization.failed.json`, and a journal without its
  final record.
- **FC-K2. The streams and the exit.** The Director redirects the command's stdout and stderr into
  fresh files beside the attempt, never inside it. Those files are kept, with the exit status or
  the terminating signal. The observer writes its refusal document on stderr; each MH tool writes
  a one-line summary or its refusal there.
- **FC-K3. The command record.** It holds the exact argv, the cwd, and the environment as a frozen
  file with its SHA-256. It also holds the start and end times in UTC, the wall time, and
  `kern.bootsessionuuid` read before and after.
- **FC-K4. The records that the code writes**, by kind:
  - **the observer:** `reserved.json` and `preflight.json`; for each command `intent.json`,
    `started.json`, the supervisor's `<label>.stdout.log`, `<label>.stderr.log` and
    `<label>.process.json`, `inspection.json`, `postflight.json` and `failure.json`; then
    `failure.json`, `result.json`, `completion.json` and `HOST.json`;
  - **the provider, in a cohort or a control:** `setup.pending.json`, `setup.json` and
    `supplemental-cpu.json`; for each case `provider-ledgers/<case>/` with `reserved.json`,
    `preflight.json`, `started.json`, `supervisor-outcome.json`, `result.json` and
    `finalization.failed.json`; the stage's three inputs, `probe.json` and the supervisor's three
    files; `cohort.json`; the temporary cohort, and its `-preserved-<id>` copy with
    `PRESERVATION.json` and `CLEANUP.json`;
  - **the outcome collector:** `journal.jsonl` and `outcomes.json`;
  - **the direct-probe runner:** `run.json`, and for each row `intent.json`, `started-<n>.json` and
    `outcome.json`, with the supervisor's three files and any `probe.json` in the row's stage;
  - **every other MH tool:** its one output file, or the fact that it is absent.
- **FC-K5. The readback record.** It is written after the command ends, before any other command
  touches the evidence. It holds:
  - for each output path that the plan names: absent, or present with its type, size, mode and
    SHA-256;
  - a listing of each attempt directory: relative path, type, size and mode; the SHA-256 of each
    regular file; the target of each link.

  It is written by exclusive creation to a fresh path outside the attempt, under
  `<local>/c271-p35/evidence/`, and fsynced. One process computes every digest of it: a start of
  `capture_probe.py listing --dir ATTEMPT ... --path OUTPUT ... --output READBACK`, which never
  follows a link (TR-16).

## 4. Establishing that a process or process group is absent

- **FC-P1. Never by name.** A list of process names never shows that a particular started process
  is absent, or present. `ps`, `pgrep` and Activity Monitor are such lists. A name listing may be
  kept as context only.
- **FC-P2. The identities come from the records,** in pairs. Each started record holds the
  supervisor's record of one start under `/process`: its PID, its process group, which equals the
  PID because the supervisor starts every child in a new session, and its argv. It is paired with
  the record written before that start:

  | Writer | Before the start | After the start |
  | --- | --- | --- |
  | the direct-probe runner | `<row>/intent.json` | `<row>/started-<n>.json` |
  | the observer | the command's `intent.json` | the command's `started.json` |
  | the provider | `provider-ledgers/<case>/preflight.json` | `provider-ledgers/<case>/started.json` |

  An audit event records an attempt but carries no PID.
- **FC-P3. The probes.** One start is made for them all:
  `capture_probe.py probe --pair BEFORE AFTER ... --output PROBES`. For each pair it records:
  - the errno name of `killpg(G, 0)` for the recorded group G. `ESRCH` means that no member of G
    exists, so the group is absent; the recorded process led its own session and group, which it
    cannot leave, so it is absent too. Success or `EPERM` means a member exists. `EPERM` includes
    an exited, unreaped member (P33-AMENDMENT-001).
  - the errno name of `kill(P, 0)` for the recorded PID P. `ESRCH` means that no process with that
    PID exists. Success or `EPERM` means that some process has that PID, not that it is the
    recorded one.
  - for a present PID, the kernel's facts: `proc_pidinfo` with `PROC_PIDTBSDINFO` (its start time,
    group, parent, user and command name), `proc_pidpath` (its image), and the members of the
    recorded group (`proc_listpgrppids`).
  - **its identity (TR-05),** established only when all three hold: its kernel start time lies
    inside the window from the modification time of the record before the start to that of the
    started record, compared in microseconds; its image equals the recorded `argv[0]`; and its
    group equals the recorded group, which equals its PID. A recorded `argv[0]` that is not the
    image of the process, such as a launcher that executes another program, never establishes it.
  - its state: `absent`, `present, identity established`, `present, identity not established`, or
    `unknown`.
- **FC-P4. Only `ESRCH` establishes absence.** A probe that cannot be made, or that gives any other
  answer, leaves the process not established absent, and the outcome stays unknown.
- **FC-P5. Descendants: the limit.** A descendant that moved to another process group or session is
  not found by the group probe. The contract claims no enforcement against descendants (section 5,
  as amended), and MC11's static scan is its only evidence. The readback record states this limit
  whenever it reports a group absent.
- **FC-P6. A process still present.** It is recorded first, by FC-K5 and FC-P3. Only a process
  whose identity is established is ended, by one start of
  `capture_probe.py stop --pair BEFORE AFTER --output STOP`:
  - it establishes the identity again (FC-P3); without it, it sends nothing;
  - it sends SIGTERM to the recorded group and probes the group every 50 ms;
  - only if the group stays present without a break for 2,000 ms, and only after the identity is
    established once more, it sends SIGKILL and probes for 2,000 ms more;
  - each send and each probe is recorded.

  A process whose identity is not established is recorded as `present, identity not established`;
  nothing is sent to it, and its outcome stays unknown. Ending a process never changes the outcome:
  the attempt stays failed or unknown.
- **FC-P7. The audit hook's limit (TR-08).** Every MH tool's audit hook records the
  process-creation events of the Python runtime (`subprocess.Popen`, `os.posix_spawn`, `os.exec`,
  `os.fork`, `os.forkpty`, `os.spawn` and `os.system`) and ctypes lookups of libc's fork, exec,
  posix_spawn, system and popen functions. It does not see `_posixsubprocess.fork_exec`, which
  multiprocessing's spawn and forkserver start methods call, nor a call made through ctypes, nor a
  lookup made before the hook was installed. A start made that way is not counted, so a start
  count is exact only for the routes that the hook sees.

## 5. No retry

- **FC-R1.** No command is repeated automatically: not by a wrapper, a loop or a shell `||`. No MH
  tool retries.
- **FC-R2.** A refused, failed or unknown attempt is never run again with the same plan, rows,
  configuration or output paths. Its paths stay as they are.
- **FC-R3.** A new attempt needs all of these:
  - this procedure completed for the earlier attempt;
  - its cause reconciled and recorded by the Director;
  - a new attempt ID and fresh absent paths;
  - where a plan stated a fact wrongly, a corrected plan, frozen and reviewed (MH-PLAN section 8);
  - the earlier attempt listed as retained.
- **FC-R4.** An unknown start count is recorded as unknown, with its observed lower bound. It is
  never recorded as zero.
- **FC-R5.** A reboot ends the attempt, because the plan binds the boot. The records are kept, and
  S4 starts again.

## 6. Order of work after an outcome other than a completed success

1. Start no other command, apart from steps 3 to 5.
2. Keep the terminal transcript and the redirected stdout and stderr files (FC-K2).
3. Read `kern.bootsessionuuid`: every `capture_probe.py` start reads it before and after.
4. Probe every recorded start (FC-P3), and act on FC-P6 only for a process whose identity is
   established.
5. Write the readback record (FC-K5).
6. Write the capture record (section 8) by exclusive creation, and fsync it.
7. Stop the stage, and apply MH-PLAN section 8.

## 7. What capture never does

- It never uses Finder on an evidence, input or source tree, because of `.DS_Store` files.
- It makes no Git write, no edit in the worktree and no change to a prepared input.
- It never cleans a temporary cohort. The provider's preserved copies are kept, and a cohort that
  was not preserved stays where it is.
- It never re-runs a command to "see what happens".

## 8. The capture record

The schema is `ontokin.c271.p35-failure-capture/1`. A closed object:

| Key | Content |
| --- | --- |
| `schema` | `ontokin.c271.p35-failure-capture/1` |
| `procedure` | this file's path and SHA-256 |
| `attempt` | the attempt ID and its directories |
| `command` | `argv`, `cwd`, `environment_sha256`, `started_at_utc`, `ended_at_utc`, and `exit`: a status, a signal, or `unknown` |
| `boot` | `kern.bootsessionuuid` before and after |
| `outcome` | `completed`, `refused`, `failed` or `unknown`, with the rule of section 2 that decided it |
| `outputs` | each planned path: absent, or present with its binding |
| `listing` | the readback listing of FC-K5 |
| `probes` | the `capture_probe.py probe` record's path and SHA-256, and for each recorded start its errno names, its identity facts and its state |
| `stops` | each `capture_probe.py stop` record's path and SHA-256, with each signal sent and each probe that followed |
| `limits` | FC-P5's statement, and anything that could not be observed |
