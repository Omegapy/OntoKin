# W1: Darwin supervisor variant (S4, as amended)

Worker W1 of gate MI, C271-P33. This note describes the Darwin supervisor under design revision 4.
That revision is contract section 5 as amended by [P33-AMENDMENT-001](../AMENDMENT-001.md),
adopted in commit `3ffabb3f`.
- **Status:** development work on base `227f790a`. It is not frozen and not reviewed.
- **Earlier version:** checkpoint `a2376191` implemented revision 3. It is kept as failed
  evidence, and its finding stays as history in section 8.
- **Sources:** it follows [contract section 5](../../macos-contract-design-p31/CONTRACT.md#5-process-lifecycle-s4),
  [AMENDMENT-001 section 3](../AMENDMENT-001.md#3-decision-and-replaced-clauses) and
  [decision D-12](../DIRECTOR-DECISIONS.md#d-12-after-the-adoption-of-p33-amendment-001).

## 1. API and imports

[`prototypes/static_tray_v01/supervisor_darwin_v01.py`](../../../../../prototypes/static_tray_v01/supervisor_darwin_v01.py)

- **Re-implemented, with the original signatures:**
  - `run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None)`,
    with the original behaviour and receipt fields apart from its change site;
  - `group_exists(pid)`;
  - `terminate_group(process, clock)`.

  Wherever `run_process` and `terminate_group` use the names `group_exists` and
  `terminate_group`, those names resolve to these re-implementations.
- **From `prototypes.static_tray_v01.supervisor`:** `Clock`, `Stop`, `LIMITS`, `inventory`,
  `json_bytes` and `_reap`, imported unchanged. They are the same objects as in that module.
  `Clock` is imported only for callers.
- **Global loads:** each function loads the same globals as its original, with three exceptions:
  - `run_process` loads `darwin_precondition` instead of `ctypes`;
  - `group_exists` and `terminate_group` also load the built-in `PermissionError`.

  Every other load binds to the original object.
- **From the standard library:** `Path`, `os`, `selectors`, `signal`, `subprocess` and `time`.
- **Added names, unchanged from revision 3:**
  - `darwin_precondition()` returns `None`, or the first unmet condition;
  - `proc_translated()` returns 0, 1 or `None`;
  - `LIBSYSTEM` is the library path;
  - `_libsystem()` loads the library. It is the seam that the simulated tests patch.
- **Unchanged:** `supervisor.py` (SHA-256 `c47b84ab464e89d4c8673d7541679a45ddf3fc4816a906aff4546e074b4c5a10`).
- **Labels (D-12):** the receipt carries no `design_revision` or `amendments` field.
  - It has no contract field, and MC14 keeps `run_process`'s tokens.
  - Those labels belong to the documents that callers write.

## 2. The amended rule

This is [AMENDMENT-001 sections 3.1 to 3.3](../AMENDMENT-001.md#31-the-rule):
- **The probe:** the group counts as absent only when `killpg(pgid, 0)` reports `ESRCH`. An
  `EPERM` answer counts as present.
- **The sends:** a send refused with `EPERM` is passed over. It is never taken as proof of
  absence.
- **Fail-closed:** a group that keeps answering `EPERM` fails at the cleanup ceiling, with the
  original `Stop("OTRAY-E-BACKEND", "Owned process group cleanup exceeded stage or transaction ceiling")`.
  - The receipt holds `cleanup: {"passed": false, "reason": …}` and an `error` equal to that
    `Stop`. That `Stop` replaces any earlier message of the run.
  - The reason does not tell the causes of a lasting `EPERM` apart.
  - A descendant that moved itself out of the group survives.

The five change sites, by row within each function:

| Site | Function | Original rows | Darwin rows | Change |
| --- | --- | --- | --- | --- |
| 1 | `run_process` | 7 to 9 | 7 to 9 | the precondition (section 3) |
| 2 | `group_exists` | none; inserted before row 5 | 5 and 6 | `except PermissionError:` / `return True`, inserted immediately before `except ProcessLookupError:` |
| 3 | `terminate_group` | 6 | 6 | the SIGTERM send now catches `(ProcessLookupError, PermissionError)` |
| 4 | `terminate_group` | 19 | 19 | the same, for the SIGKILL send after the grace period |
| 5 | `terminate_group` | 35 | 35 | the same, for the final SIGKILL send before the ceiling `Stop` |

## 3. Precondition (unchanged)

It runs where the original called `prctl`:
- after the stage and argv `ValueError` check;
- before `clock.check`, before the receipt record exists and before any start.

The checks run in this order, and the first unmet one stops the run:

| Condition | Unmet reason |
| --- | --- |
| `sys.platform == "darwin"` | `sys.platform is not darwin` |
| `os.uname().machine == "arm64"` | `os.uname().machine is not arm64` |
| `sysctl.proc_translated` is readable | `sysctl.proc_translated is unreadable` |
| its value is 0 | `sysctl.proc_translated is not 0` |

A failure raises `Stop("OTRAY-E-BACKEND", "Cannot establish the Darwin arm64 native precondition: " + reason)`
with state `REJECTED`, which is `Stop`'s default, as in the original. No `.process.json` is
written and the exception carries no `process_record`, the same as the original's `prctl` stop.

## 4. How the sysctl is read (unchanged)

- **Library:** `ctypes.CDLL("/usr/lib/libSystem.B.dylib")` and its symbol `sysctlbyname`.
  - Its argument types are `(c_char_p, c_void_p, POINTER(c_size_t), c_void_p, c_size_t)` and it
    returns `c_int`.
  - The library is loaded only after the platform and machine checks pass.
- **Call:** name `b"sysctl.proc_translated"`, a `c_int` buffer that starts at -1 with length 4,
  and no new value (`NULL`, 0).
- **Readable** only when the call returns 0 and the length comes back as 4.
- **Unreadable, and therefore refused:**
  - a load `OSError`, or a missing symbol (`AttributeError`);
  - `ctypes.ArgumentError`;
  - any non-zero status;
  - any other length.
- **This host:** status 0, value 0, length 4.

## 5. Token comparison (MC14, development)

`token_comparison()` in the test module works through the three functions:
- it takes `inspect.getsource` of each function in both modules;
- it tokenizes each with `tokenize.generate_tokens`;
- it compares the tokens by type, string, start and end.

**Ignored: nothing.** Comments, docstrings and the NL, NEWLINE, INDENT and DEDENT tokens are
compared too.

**Two checks:**
- **Outside the five sites:** the tokens must be equal. Rows after site 2's two inserted lines
  are mapped back by 2.
- **The whole source:** each Darwin source must equal its original with exactly the five edits
  applied, character for character.

**Result:**

| Function | Tokens, original then Darwin | Tokens outside the sites, all equal | Source equals original plus edits | difflib non-equal opcodes |
| --- | --- | --- | --- | --- |
| `run_process` | 1,104 then 1,087 | 1,062 | yes | 5 |
| `group_exists` | 36 then 45 | 36 | yes | 1 |
| `terminate_group` | 345 then 357 | 330 | yes | 6 |

There are five change sites, and sites 2 to 5 are the ones that add `PermissionError`. The
full token diff is in `../OntoKin-local/c271-p33/workers/W1/rev4-amendment-001/04-MC14-token-comparison.json`
beside the clone. It holds each site's tokens, the difflib opcodes and a unified source diff.

## 6. Meaning of the lifecycle fields

`reaped`, `process_group_absent`, `cleanup.passed` and `handles_closed` keep their text. Their
meanings are those of the table in [contract section 5](../../macos-contract-design-p31/CONTRACT.md#5-process-lifecycle-s4),
as [AMENDMENT-001 section 3.4](../AMENDMENT-001.md#34-replaced-clauses-of-contractmd) amends it in
rows 11 and 12:
- **`process_group_absent`:** the probe failed with `ESRCH`. Absent therefore means that no
  member remains, live or unreaped. A member that this process may not signal also counts as
  present.
- **`cleanup.passed`:** the group became absent (`ESRCH`) within the cleanup ceiling.
- **`reaped` and `handles_closed`:** unchanged. Orphaned descendants are re-parented to launchd,
  not to the supervisor. Results never claim the Linux descendant-reaping guarantee.

## 7. Tests

[`tests/test_supervisor_darwin_v01.py`](../../../../../tests/test_supervisor_darwin_v01.py) uses
the standard library only. Its tests are development tests, not frozen controls.

- **How processes start:** every started process is a Python process.
  - Children start as `sys.executable -I -S -B -c <code>`, with the environment
    `{"PATH": "/usr/bin:/bin", "LC_ALL": "C"}`.
  - `-B` keeps them from writing bytecode into the interpreter tree, which M0 binds as an exact
    set (MC32).
  - In MC39 (a), the child forks Python descendants.
- **Guard, with the amended rule:** EPERM means present.
  - After each test, every tracked group must answer `ESRCH` within 2 s. One that does not is sent
    SIGKILL and reported.
  - `_gone(pid)` likewise waits for `ESRCH` from `kill(pid, 0)`.
- **On other hosts:** the tests that start real children need the darwin-arm64-v1 executor, and
  so does the real-precondition test. Elsewhere they fail visibly; no skip is added.

| Test | Starts | Checks |
| --- | --- | --- |
| `test_positive_child_exits_zero_with_the_original_receipt` | one child: one line to stdout and one to stderr, then exit 0 | the original receipt keys; `cleanup`; `handles_closed`; both logs; the receipt file equals `json_bytes(record)`; one start; the group answers `ESRCH` |
| `test_mc12_development_descendant_left_in_the_group_is_refused_and_terminated` | one child that starts one grandchild in its group (no setsid; streams on `/dev/null`), then exits while the grandchild sleeps for at most 15 s | the original "Child exited while an owned descendant remained" `Stop`; cleanup within 2,000 ms; the group and the grandchild answer `ESRCH` |
| `test_mc13_development_timeout_cleanup` | one child that sleeps for at most 15 s, ended by a 300 ms stage deadline | `OTRAY-E-RESOURCE` with `TIMEOUT`; the original receipt; return code -15; exactly one start, counted by `on_started` and `Popen`; no retry |
| `test_mc13_development_cancellation_cleanup` | one child that sleeps for at most 15 s, with `cancel_after_ms=150` | `OTRAY-E-CANCELLED` with `CANCELLED`; `cancellation_completion_ms` ≤ 2,000; exactly one start; no retry |
| `test_mc37_development_group_exists_counts_an_exited_unreaped_child_as_present` | one child, started with `Popen` in a new session, that exits when its stdin closes | kqueue `KQ_FILTER_PROC` with `KQ_NOTE_EXIT` establishes the exit without reaping (the raw probe answers `EPERM`). Then `group_exists` is true while the child is unreaped, and false (`ESRCH`) after `wait` |
| `test_mc38_development_terminate_group_on_an_exited_unreaped_child` | the same kind of child, with its exit established the same way | `terminate_group` returns the original passed receipt within 2,000 ms, and no `PermissionError` reaches the caller. A recording wrapper passes every call to the real `os.killpg`; it shows the SIGTERM send refused with `EPERM` and passed over, then `ESRCH` |
| `test_mc39a_development_lasting_eperm_from_an_escaped_descendant_fails_at_the_ceiling` | one child through `run_process`. It forks a descendant, which forks its own child, moves itself into its own process group, never reaps that child, and sleeps for at most 15 s | the ceiling `Stop` after at least 2,000 ms; `cleanup: {"passed": false, "reason": …}`; `error` equals that `Stop`; one start. The owned group still answers `EPERM` and the descendant is alive. The test's own teardown then kills the descendant, and both the descendant and its child answer `ESRCH` |
| `test_mc39b_simulated_lasting_eperm_probe_fails_at_the_ceiling` | one child that sleeps for at most 15 s, ended by a 300 ms stage deadline (simulated: `os.killpg(pid, 0)` fails with `PermissionError`, and real signals pass through) | the same ceiling `Stop` and receipt; return code -15; the real sends are SIGTERM, SIGKILL and SIGKILL; after the patch, the group answers `ESRCH` |
| `test_mc17_simulated_non_darwin_platform_stops_before_any_start` | nothing (simulated: `sys.platform` is linux) | the `Stop` text; `Popen` and `on_started` are never called; no file in the stage; libSystem is not loaded |
| `test_mc17_simulated_machine_other_than_arm64_stops_before_any_start` | nothing (simulated: the machine is x86_64) | the same |
| `test_mc17_simulated_translated_process_stops_before_any_start` | nothing (simulated: the sysctl reads 1) | the same, with the sysctl read once by its exact name |
| `test_mc17_simulated_unreadable_sysctl_fails_closed_before_any_start` | nothing (simulated: status -1, a 2-byte value, a load failure, a missing symbol) | the "unreadable" `Stop` before any start, in each case |
| `test_simulated_native_boundary_is_admitted` | nothing (simulated) | the simulated native boundary passes, so each MC17 case fails on one condition only |
| `test_real_precondition_holds_on_this_host` | nothing | the real values: `sys.platform` is darwin, the machine is arm64, `proc_translated` is 0; the precondition passes |
| `test_mc14_development_token_comparison_shows_exactly_the_five_change_sites` | nothing | section 5 |
| `test_imported_names_and_signatures` | nothing | the six imported names are the original objects; the three re-implemented functions belong to this module and keep the original signatures |
| `test_body_globals_bind_to_the_original_objects_or_the_reimplementations` | nothing | the global loads of section 1 |

Revision 3's observation test has been replaced by MC37. MC37 asserts the raw `EPERM` answer
after an exit that kqueue establishes, and the raw `ESRCH` answer after reaping.

**Repeat runs:**
- **Series:** 20 complete runs of the module, at the bytes named in the evidence.
- **Result:** every one of the 17 tests passed in all 20 runs, MC12, MC13, MC37, MC38 and MC39
  (a) and (b) among them. No `ResourceWarning` appeared.
- **Processes:** `ps` found no remaining test process.

**Mutation check:** the tests also ran on scratch copies of two unsafe variants that
AMENDMENT-001 section 4 names. The unmodified copy passed all 17 tests.

| Variant | Tests that failed |
| --- | --- |
| `EPERM` counted as absent | MC37, MC39 (a) (the run was accepted), MC39 (b) and MC14 |
| original sends kept | MC38 and MC39 (a), both with a `PermissionError`; also MC14 and the global-loads test |

**Evidence:** in `../OntoKin-local/c271-p33/workers/W1/rev4-amendment-001/`:
- `01-first-run.txt`;
- `02-mutation-check.txt` and its summary `02b-mutation-summary.txt`;
- `03-repeat-20-runs.txt` and its summary `03b-repeat-20-summary.txt`;
- `04-MC14-token-comparison.json`.

## 8. History: finding P33-SUPERVISOR-001 under revision 3

This was section 6 of this note at checkpoint `a2376191`, which implemented revision 3's S4. It
is kept as written. Its test and line references are to that checkpoint's files.
[AMENDMENT-001](../AMENDMENT-001.md#2-finding-p33-supervisor-001) resolved it as design revision 4.
The amendment adopted a wider form of the recommendation, which also covers the three sends.

### Defect: Darwin's group probe (blocks MC12, and at times MC13)

**Facts.**
- **Observation:** the probe behaves as follows on this host (Darwin 25.6.0, arm64, CPython
  3.12.13). A deterministic test records it.

  | Group state | `killpg(pgid, 0)` |
  | --- | --- |
  | a member is alive | 0 |
  | every remaining member has exited, none reaped | fails with `EPERM` |
  | after reaping | fails with `ESRCH` |

  The imported `group_exists` catches only `ProcessLookupError`. It therefore raises
  `PermissionError` in the second state.
- **Where it breaks:** `terminate_group`'s grace loop (`supervisor.py` lines 135 and 107) can hit
  that state. This happens when the last member has exited but is not reaped yet: the direct
  child before the next `poll()`, or a descendant before launchd reaps it.
- **A second path, by the code only:** the same probe in `run_process`'s group check after exit
  can also raise in that state. `run_process` would then turn the error into a
  `Stop("OTRAY-E-BACKEND", "PermissionError: …")`. No run observed this path.
- **What the caller gets:**
  - The `try` around `terminate_group` in `run_process` catches only `Stop`. The caller therefore
    receives `PermissionError`, with the original `Stop` as its `__context__`, and not that `Stop`.
  - By the code of `run_process`, the receipt is then written with `cleanup: null`. No receipt
    was inspected in the failing runs.
  - After a timeout or a cancellation, the direct child can remain unreaped. Each of the four
    failing MC13 runs showed a `ResourceWarning` that the subprocess was still running.
- **Frequency:** across 12 runs of the real-child cases:

  | Case | Failed |
  | --- | --- |
  | MC12 | 10 of 12 |
  | MC13 timeout | 3 of 12 |
  | MC13 cancellation | 1 of 12 |
  | positive child | never (0 of 12) |

  Every failure is this `PermissionError`.
- **Processes:** `ps` found no live test process after any batch of runs.
- **Contract assumption:** [contract section 12](../../macos-contract-design-p31/CONTRACT.md#12-trust-assumptions-and-limits)
  leaves open whether Darwin counts a zombie member. On this host, Darwin neither counts it as
  present nor reports the group absent: the probe fails with `EPERM`.

**Not worked around.** Contract section 5 imports `group_exists` and `terminate_group` unchanged
and limits the change to the precondition (MC14). The expectations of MC12 and MC13 stay as
the contract states them.

**Recommendation, for the Director and owner.** An amendment could give the Darwin variant its
own `group_exists`:
- It would treat `EPERM` from `killpg(pgid, 0)` as "present, exited" and poll until `ESRCH`,
  within the unchanged 2,000 ms ceiling.
- It must not treat `EPERM` as absent, since `EPERM` also means a live member that the
  supervisor is not permitted to signal.
- MC14's scope would then cover that function too.
