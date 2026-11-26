# W1: Darwin supervisor variant (S4)

Worker W1 of gate MI, C271-P33, on base `f3a5acf8`. This note covers development work only. It
is not frozen and not reviewed. It implements [plan section 4.1](../IMPLEMENTATION-PLAN.md#41-darwin-supervisor-w1)
under [contract section 5](../../macos-contract-design-p31/CONTRACT.md#5-process-lifecycle-s4).
It also records one defect (section 6) that blocks the expected outcomes of MC12, and at times
those of MC13.

## 1. API and imports

[`prototypes/static_tray_v01/supervisor_darwin_v01.py`](../../../../../prototypes/static_tray_v01/supervisor_darwin_v01.py)

- **`run_process`:** `run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None)`.
  It keeps the original signature, behaviour and receipt fields. Only the precondition differs.
- **From `prototypes.static_tray_v01.supervisor`:** `Clock`, `Stop`, `LIMITS`, `inventory`,
  `group_exists`, `terminate_group` and `json_bytes`, imported unchanged. They are the same
  objects as in that module.
  - The body uses six of them. `Clock` is imported only so that callers can reach it here.
  - The body needs no other name from that module. Its global loads match the original's,
    except that `ctypes` becomes `darwin_precondition`, and each load binds to the same object.
- **From the standard library:** `Path`, `os`, `selectors`, `subprocess` and `time`, the same
  module objects the original uses.
- **Added names:**
  - `darwin_precondition()` returns `None`, or the first unmet condition;
  - `proc_translated()` returns 0, 1 or `None`;
  - `LIBSYSTEM` is the library path;
  - `_libsystem()` loads the library. It is the seam that the simulated tests patch.
- **Unchanged:** `supervisor.py` (SHA-256 `c47b84ab464e89d4c8673d7541679a45ddf3fc4816a906aff4546e074b4c5a10`).

## 2. Precondition

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

## 3. How the sysctl is read

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

## 4. Token comparison (MC14, development)

`token_comparison()` in the test module:
- takes `inspect.getsource` of both `run_process` functions;
- tokenizes each with `tokenize.generate_tokens`;
- compares the tokens by type, string, start and end.

**Ignored: nothing.** Comments and the NL, NEWLINE, INDENT and DEDENT tokens are compared too.

**Result:**
- **Token counts:** 1,104 in the original and 1,087 in the variant.
- **Outside the precondition:** rows 1 to 6 and 10 to 94 of the two functions are identical, token
  for token and position for position.
- **Inside it:** all five differing opcodes lie in rows 7 to 9, the precondition (42 original
  tokens, 25 Darwin tokens). No differing token lies outside it.
- **Function-source SHA-256:** `f77a541b…` for the original and `ee1239bd…` for the variant.

The full record is in `../OntoKin-local/c271-p33/workers/W1/04-MC14-token-comparison.json`
beside the clone. It holds the token diff and a unified source diff.

## 5. Meaning of the lifecycle fields

`reaped`, `process_group_absent`, `cleanup.passed` and `handles_closed` keep their text. Their
narrowed Darwin meaning is the table in [contract section 5](../../macos-contract-design-p31/CONTRACT.md#5-process-lifecycle-s4).
In short:
- orphaned descendants are re-parented to launchd, not to the supervisor;
- results never claim the Linux descendant-reaping guarantee.

## 6. Defect: Darwin's group probe (blocks MC12, and at times MC13)

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

## 7. Tests

[`tests/test_supervisor_darwin_v01.py`](../../../../../tests/test_supervisor_darwin_v01.py) uses
the standard library only. Its tests are development tests, not frozen controls.

- **How children start:** as `sys.executable -I -S -B -c <code>`, with the environment
  `{"PATH": "/usr/bin:/bin", "LC_ALL": "C"}`.
  - `-B` was added to the assigned `-I -S` so that no child writes bytecode into the
    interpreter tree. M0 binds that tree as an exact set (contract section 4, MC32).
- **Guard:** after each test, a guard kills any started group that is still alive and reports
  it.
- **On other hosts:** the tests that start real children, and the real-precondition test, need
  the darwin-arm64-v1 executor. Elsewhere they fail visibly; no skip is added.

| Test | Starts | Checks |
| --- | --- | --- |
| `test_positive_child_exits_zero_with_the_original_receipt` | one child: one line to stdout and one to stderr, exit 0 | the original receipt keys; `cleanup`; `handles_closed`; both logs; the receipt file equals `json_bytes(record)`; one start |
| `test_mc12_development_descendant_left_in_the_group_is_refused_and_terminated` | one child that starts one grandchild in its group (no setsid; streams on `/dev/null`), then exits while the grandchild sleeps for at most 15 s | the original "Child exited while an owned descendant remained" `Stop`; cleanup within 2,000 ms; group absent; grandchild gone |
| `test_mc13_development_timeout_cleanup` | one child that sleeps for at most 15 s; a 300 ms stage deadline | `OTRAY-E-RESOURCE` with `TIMEOUT`; the original receipt; returncode -15; exactly one start, counted by `on_started` and `Popen`; no retry |
| `test_mc13_development_cancellation_cleanup` | one child that sleeps for at most 15 s; `cancel_after_ms=150` | `OTRAY-E-CANCELLED` with `CANCELLED`; `cancellation_completion_ms` ≤ 2,000; exactly one start; no retry |
| `test_mc17_simulated_non_darwin_platform_stops_before_any_start` | nothing (simulated: `sys.platform` is linux) | the `Stop` text; `Popen` and `on_started` are never called; no file in the stage; libSystem is not loaded |
| `test_mc17_simulated_machine_other_than_arm64_stops_before_any_start` | nothing (simulated: machine is x86_64) | the same |
| `test_mc17_simulated_translated_process_stops_before_any_start` | nothing (simulated: the sysctl reads 1) | the same, with the sysctl read once by its exact name |
| `test_mc17_simulated_unreadable_sysctl_fails_closed_before_any_start` | nothing (simulated: status -1, a 2-byte value, a load failure, a missing symbol) | "unreadable" `Stop` before any start, in each case |
| `test_simulated_native_boundary_is_admitted` | nothing (simulated) | the simulated native boundary passes, so each MC17 case fails on one condition only |
| `test_real_precondition_holds_on_this_host` | nothing | the real values: `sys.platform` darwin, machine arm64, `proc_translated` 0; the precondition passes |
| `test_mc14_development_token_comparison_differs_only_in_the_precondition` | nothing | section 4 |
| `test_imported_names_and_signature_are_the_original` | nothing | the seven names are the original objects; the signature is equal |
| `test_body_globals_bind_to_the_original_objects` | nothing | the body's `LOAD_GLOBAL` names bind to the original objects, except the precondition's |
| `test_observation_killpg_reports_eperm_while_the_group_holds_only_an_unreaped_child` | one child with `Popen` in a new session that blocks on stdin, exits when stdin closes, and is reaped after the observation | the sequence 0, then `EPERM`, then `ESRCH`; `group_exists` raises `PermissionError` (section 6). This observes the host and is not a control. |
