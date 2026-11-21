# P08 complete-module preliminary static review

Reviewer: `/root/implementation_review`. Exact snapshot: `session/PRELIMINARY-MODULE-002.py`, 120,885 bytes, 1,994 lines, SHA-256 `dec9ef7b94b9cadac00840fc22613f13c34f48d442bf3d4ef2d3bbd3bb454e02`.

**Disposition: mandatory corrections remain; no implementation acceptance or execution approval.** The unchanged prefix was reused through an exact textual diff against snapshot 001. All new code was read. No candidate import, compilation, test, runtime preparation, host qualification, Node/ldd or Git operation occurred. Author messages describe newer working fixes; those are unverified until a new exact candidate is frozen.

## Earlier findings

| Finding | Snapshot 002 disposition |
| --- | --- |
| PRE-01 present RTLD candidates | Structurally corrected: present candidates must appear in HOST aliases/files and ELF roots. |
| PRE-02 parent-traversal alias guards | Corrected by explicit refusal of `..` symlink targets before normalization. This is a conservative unsupported-case boundary. |
| PRE-03 ELF load mapping | PT_DYNAMIC mapping corrected; PT_LOAD alignment congruence remains unchecked. |
| PRE-04 bounded enumeration | Partially corrected with iglob; internal enumeration and other traversals remain unbounded before their checks. |
| PRE-05 present loader inputs in HOST | Structurally corrected: present loader input set equals loader_configuration roles and exact HOST file bindings. |
| PRE-06 numeric/input/parser shapes | The specifically reported examples are corrected: canonical fixed-limit equality, strict candidate binding, input-category reclassification, exact vDSO-list validation. |

These are source findings, not executed regression results.

## PRE-03 remains — load-segment alignment congruence

**Priority: medium. Lines 605–627. Controls: HI08-B/C/D.**

The new PT_DYNAMIC mapping comparison closes the earlier offset witness. However, lines 607–608 check only that `p_align` is zero, one or a power of two. They do not require a PT_LOAD segment's file and virtual offsets to have the same residue modulo its alignment. An otherwise admitted image with `p_align=4096`, `p_offset=0`, and `p_vaddr=0x400001` remains malformed but is not rejected by this predicate.

Add the congruence check for admitted load segments and a synthetic malformed-segment control. This requires no runtime execution or broader ELF support.

## PRE-04 remains — finite traversal and deadline checks

**Priority: high for the declared bounds. Lines 743–753, 934–950, 1114–1122, 1241–1245, 1284–1296, 1390–1400, 1951–1952. Controls: HI03/HI07/HI08/HI18/HI19.**

Replacing glob with iglob does not bound directory enumeration inside the library. The inspected CPython 3.12 `glob.py` uses `_glob1 -> _listdir -> list(_iterdir(...))`; it can collect an entire directory before the first returned match reaches this module's `check()` and 2,048 limit. Wildcard directory components make the problem larger.

The same class of gap occurs in `_source_paths` and metadata enumeration: `os.walk` supplies whole directory/file lists, and neither loop has a deadline or encountered-entry bound. EvidenceStore.budget likewise uses os.walk, and completed reconciliation builds the entire rglob set before comparing it. `_input_snapshot` has no check callback and runs after `_validate`'s final deadline check, permitting a return after the declared static ceiling without another check.

Use bounded, checked directory-entry traversal for the already supported finite scope. Retain source/metadata exact-inventory checks, refuse unreadable traversal instead of silently accepting incomplete enumeration, and pass the appropriate existing deadline through snapshot and evidence traversal. Check the deadline after the final bounded operation. Do not replace the adopted source/dependency inventory with a smaller one. No actual host scan is required for the synthetic bound controls.

## PRE-07 — Git executes before its complete closure is checked

**Priority: high. Lines 1031–1058 and 1228–1238. Controls: HI04, HI06, HI07.**

`_validate` calls `_check_git` at line 1232. That function launches five real Git reads through the driver. `_check_host_static`, `_check_resolution`, and significant path guards run only afterward. Binding the Git executable itself at 1038 does not establish its interpreter, transitive shared inputs, loader/config/search inputs or alias ancestors before execution.

The accepted design permits the five reads only with the actual selected Git and relevant loader inputs bound. Finish the no-process static closure and path checks before `_check_git`, then retain the exact five command results. Reordering need not add any subprocess. A fixture can mutate only Git's declared loader closure and assert zero mocked Git delegation at that refusal boundary.

## PRE-08 — Author runtime descriptors need actual-byte and HOST correspondence

**Priority: high. Lines 1061–1091, 1206–1217, 1727–1738. Controls: HI06-C, HI07-G, HI20-C.**

First, `_check_author_runtime` compares the runtime document's `executable` descriptor with `author.python_descriptor`, but never compares that descriptor's hash/size/mode with the actual Python binding in `runtime.files`. It checks the file map independently and reads ELF metadata at the same path. Therefore two coherently wrong descriptor copies can coexist with a file-map binding to the actual bytes and pass this relation.

Require the selected descriptor to match the runtime file-map member and actual file bytes. The controlled negative mutation changes only those coherent descriptor copies while leaving the actual file and file-map binding unchanged; the descriptor comparison itself must remain live.

Second, author startup/runtime file-map members are not required in HOST aliases/files. The ELF-root checks cover selected native images, but `_host` copies only `host_static.files`, and no reviewed predicate requires all admitted non-source author-runtime files there. P07 §6 requires admitted representable author/inspector/interpreter/loader inputs in HOST; plan-only startup-file bindings would otherwise disappear from the later consumer's host lock. Establish the required role/alias/file correspondence without adding unrelated dummy roles or auditing unrelated installed software. Project source remains separately bound by the complete source inventory.

## PRE-09 — Start and final receipt can identify different processes

**Priority: high. Lines 1478–1509 and 1622–1668. Controls: HI14-B/D, HI17-C, HI20.**

One callback can record PID/group 4242, while a returned/raw final receipt reports PID/group 5252. `_count_observed` writes count one in both cases. `_process_success` validates the final receipt internally but never compares its invariant identity with the retained callback. The pipeline can consequently produce compatible success while its records describe different processes.

Compare PID/group, argv, cwd, environment, label and start_monotonic across callback, raw/final outcome and projected inspection. Preserve every callback receipt and refusal evidence. Repeated callbacks or multiple distinct PIDs must not overwrite earlier evidence or be clamped into a valid one-start projection. A separate failed contract-violation record can retain complete ordered callbacks and the known distinct-PID count when ordinary 0/1 sidecar projection is unavailable. Unknown completeness keeps exact null and a truthful lower bound; it cannot erase a known count supplied by the controlled fixture.

## PRE-10 — Result publication can be retried after uncertainty

**Priority: high. Lines 1815 and 1828–1835. Controls: HI18-D/E/F.**

When the first result.json publication fails or has an uncertain rename outcome, the outer handler checks only whether the destination currently exists. If it is absent, it invokes `store.write` on that same destination again with changed failure content. This is an automatic retry after an uncertain operation, contrary to the no-retry contract. A later absence observation does not erase the first publication intent.

Gate failure publication by the recorded destination-attempt history, as the command postflight writer already does. If result publication has been attempted, retain that exact source/destination/intention/readback and leave the caller capture unresolved; do not issue a second write. A genuinely never-attempted failure result is a different case.

## PRE-11 — Reconciliation does not validate the complete evidence graph

**Priority: high. Lines 1854–1904 and 1919–1953. Controls: HI19, HI20.**

The following static counterexamples are not excluded:

- Give completion and result matching empty `command_attempts` arrays. The zip at 1942 performs no comparisons, while independently read command finals can still report completed records and count two.
- Point completion.result or completion.host to another valid file while the nominal planned files merely exist in the final directory inventory. Those descriptor paths are not required to equal the declared output paths.
- Supply a start, outcome, raw process, inspection and final-attempt record with inconsistent process identities or descriptor links. `_reconcile_command` mostly counts any positive PID and checks file hashes independently; it does not compare the complete start/raw/outcome/final chain.
- Supply an intent or preflight file with irrelevant but parseable content. Existence in the inventory does not validate the expected plan/command/descriptor relation. Reservation owned_directories may be empty because its exact required keys/set are not checked.

Require exact command-array cardinality/order, exact planned descriptor destinations, closed record shapes and the actual cross-record identities. Compare the raw outcome bytes with the committed process record and inspection process; compare start/final PID and immutable command fields; validate each final record's start/supervisor/preflight/artifact descriptors against the retained records. Retain failure/unknown state for any mismatch. The inventory check remains useful, but it does not replace these relations. Reconciliation must remain read-only and must never promote uncertainty from PID absence.

## PRE-12 — HOST compatibility validation omits consumer predicates

**Priority: high. Lines 1742–1763. Controls: HI20-A/B/C/D.**

The pinned schema permits arbitrary Python version/package strings, absolute Python/runtime executable paths and a general source-archive descriptor. `_validate_host_projection` compares only platform/files/aliases/roles with the plan. It therefore does not enforce the exact selected Python identity/packages or runtime source/archive fields required by the unchanged P06 consumers.

For inspection receipts, the validator calls `_inspection` but discards its reconstructed result. The schema's top-level `inspection.argv` is only an array of strings. A receipt can have a correct nested process.argv and an incorrect top-level argv; `_inspection` validates the process then constructs the correct top-level array, but no comparison rejects the original wrong array. P06 `_verify_inspection` would reject it.

Compare the full fixed projected Python/runtime/environment fields against validated inputs, and compare the exact reconstructed inspection with the retained receipt, without rewriting the latter. Keep timestamp and raw-byte predicates. This closes compatibility through static, synthetic controls rather than invoking Node or the real P06 qualification route.

## PRE-13 — Approved outer-log growth blocks reconciliation; guard coverage is missing

**Priority: high for recovery. Lines 498–510, 1206–1217 and 1914. Controls: HI09, HI19.**

The code explicitly says the separately approved outer log may grow. Nevertheless `_validate(fresh=False)` calls `_check_evidence`, which hashes the entire current log against its pre-observation descriptor. Ordinary CLI/harness output appended to that log can therefore make later reconciliation refuse even though the plan, attempt and log ownership are unchanged. The immutable approved plan cannot simply be rewritten with a new log digest.

Define a concrete stable authority/log-identity or bounded initial-prefix/append contract within the existing outer-capture model. Preserve immutable authority; allow only the already approved writer's declared growth; never derive execution approval from log content. Include both outer_capture authority/log paths in significant path-guard coverage: `_required_paths` currently omits them. The tool must still leave those caller-owned files untouched.

## PRE-14 — A later error can detach the original supervisor exception

**Priority: medium. Lines 1652–1656, 1675–1707. Controls: HI11-C, HI18.**

When a supervisor failure is followed by postflight drift, the returned HostInspectionError is the drift error. The original supervisor exception survives only as `_failure(failure)` data in records, rather than as the unchanged attached exception object required by P07. A subsequent failure-evidence exception similarly substitutes a new cause and retains the earlier failure only as a dictionary.

Preserve the original supervisor exception and process_record as unchanged attached values alongside the later drift/persistence failure. Serialized evidence should retain their summaries as well. This is an exception-chain/data-preservation correction; it requires no schema change to P06 success records.

## Review and scope boundary

All findings are within the existing authoring, finite input, process-accounting, durability and read-only recovery contracts. Synthetic fixtures can mock host/runtime boundary facts. The mutated predicate remains live, and production constants need separate exact assertions. No operational H0/H1 fixture, runtime installation, whole-environment audit, original-seven execution or qualification is required.

A read-only schema inspection helper attempted a nonexistent top-level `$defs.process` key; process is inline under inspection. That helper stopped with KeyError after printing the actual inspection/host definitions. This observation error is recorded separately and changed no source or result. The relevant definitions were already read correctly from the printed inline schema.

Next: freeze the corrected complete module/tests and their exact deterministic fixture/control map; inspect the changes and remaining relationships before any focused execution or implementation acceptance.
