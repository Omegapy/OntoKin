# Candidate 002: independent pre-execution review

**Verdict: approved for one bounded focused run of the exact candidate and selected controls, after the root's clean-source/hash checkpoint.** No mandatory residual static finding remains. This is a pre-execution gate decision, not a claim that the implementation passes, that a host is eligible, or that C271 is complete.

## Exact approved inputs

| Input | Bytes | SHA-256 |
|---|---:|---|
| `current_host_inspection_v01.py` | 147775 | `1e150672c2eb0c0f64e4dfb724e482aaee01fff26f142e0d8b3918ae7b8e55e3` |
| `test_current_host_inspection_v01.py` | 136677 | `f095156a9b85e5857f9ce269243d06c7597fadf6b533e5aeca3a1de47ac41e14` |
| `CONTROL-MAP.json` | 526586 | `6792e1c8debe9ba0163dcd161fbd746507e846da89abfcb7639975558a309cd7` |
| `run_focused_guarded.py` | 2686 | `27489064a600ea3cfba73381fa1f75cc781cdc72303bd97ee200c6ebdb4aafdd` |
| `CONCRETE-SHAPES-AND-CORRESPONDENCE.md` | 7815 | `9c717a18aeedb0e3bdb92957c952e8e4a9341318abfc5cc3f071b9cd1d57de9a` |

The two candidate files and map are under `implementation_work/candidate-002`; the runner and correspondence note are under `implementation_work`. The candidate files were independently hashed and compared to their manifest. The runner and note identities were also checked against the map.

The reviewer read all new module/test differences against exact candidate 001, using the previously completed full review for unchanged text. The map's 111 unique definition anchors match the exact file slices and hashes. All 109 original negative IDs, five positive IDs, and 16 supplemental groups remain selected. The four approved state corrections remain the only exact-state changes. The map also selects four scoped regressions, for **134 test methods total**. Full copied supplemental expectations match the independent supplement. The original freeze remains immutable.

No candidate import, compilation, test, project process, runtime preparation, Node, or ldd was performed during this review. Filesystem/hash/JSON bookkeeping and static source reads supplied the evidence. The verification record and retained text deltas are alongside this report.

## Mandatory finding dispositions

| Finding | Exact candidate 002 disposition |
|---|---|
| C01-01: outcome-only historical count | A positive outcome-only count now requires the closed process keys, selected command/argv/cwd/environment/label, typed positive PID/group, bounded count types, ordered finite process timestamps, and matching planned raw descriptor/decoded process. Tests include a valid counterpart, PID-only data, wrong command with coherent raw data, missing raw descriptor and partial raw bytes. |
| C01-02: empty evidence directories | Completed reconciliation compares the observed directory set to the exact reserved directory set, as well as comparing all files. Both an extra empty attempt directory and an extra empty stage directory are refused and preserved. |
| C01-03: SUP14 unrelated plan mismatch | The selected plan and every historical record are now built coherently after the guard mutation. The tests first demonstrate that the retained graph is internally consistent without capture checking, then require the live capture guard to refuse. |
| C01-04: exact multiple-start anomaly | Separate violation details retain ordered callbacks, exact observed distinct-start count two, lower bound two, and unavailable ordinary projection. Total completeness uncertainty is explicit. Tests check exact values and retained raw bytes through later drift, outcome persistence failure and failure-record persistence failure. The anomaly is attached to replacement errors instead of being erased. |
| C01-05: recorded completion versus durability | Read-only recovery reports graph/content state separately from `durability_state: UNKNOWN` and `evidence_finalized: false`. Tests cover both an ordinary recorded graph and a completion-directory-fsync failure that leaves marker bytes present. No recovery write, extra fsync, retry or log-tail authority is introduced. |
| Named Git alias closure / PRE-07 | Before Git delegation, the actual selected PATH name must be in admitted roles/aliases, resolve to the canonical descriptor, and match the HOST file binding. Required path-guard coverage was already checked before this point. Missing/changed named aliases and missing named-path guards refuse with zero mocked Git reads; the positive static route still requires exactly five reads. |

Earlier PRE-01 through PRE-14 and DTR-01 through DTR-09 are resolved sufficiently for this pre-execution gate, combining the retained reviews, exact source corrections, selected live predicates and the qualifications below. Focused results are still required for implementation acceptance. The test routes remain synthetic/static/filesystem/mocked; none establishes actual host qualification.

## Preserved contract and reporting qualifications

D01's raw/committed supervisor path pair remains closed and predeclared. Raw supervisor bytes are preserved. D03's outer capture retains immutable authority, original prefix/hash/size/mode and guarded private inode/ancestors, with bounded append growth and no authority inferred from appended content. D04's local bounded tree checker retains the protected provider/preparer's historical 24-file dependency set, hashes/sizes/modes, archive and package versions, directory requirements and link refusal predicates. The protected consumers and schemas are unchanged by these two candidate files.

D05 remains the approved four-state correction: HI17-D and HI18-A/B/C retain UNKNOWN for unproved final receipt or persistence, without changing their known historical start counts or categories.

D06's HI16-C route is correctly reported as zero actual OS starts, zero new mocked supervisor starts, and one synthetic PID value supplied to the serialization fixture. The original generic count oracle is retained separately as reference. Both exact size guards remain live; the ldd grammar substitution is explicitly outside this predicate. Separate HI16-A/B/D/P03 controls supply state-machine count evidence.

D07 permits `OBSERVED_UNAPPROVED_AS_RECORDED` only as a description of the retained graph and content. Every read-only reconciliation exposes unknown durability, false evidence finalization and false approval. It grants no fresh completion success, relaunch permission, or qualification.

For HI14-D, exact two describes the retained distinct observed starts in the separate violation evidence. The normal 0/1 sidecar projection remains unavailable; the aggregate total may remain null with explicit completeness uncertainty and retained lower bound two. This is not a fabricated zero or a relaxed count enum.

## Guarded runner and authorized scope

The exact runner installs subprocess/fork/spawn/wait/signal guards before candidate or project-helper import, then permits only the new focused test module or its named test methods. Test-level guards reinforce the process boundary; supervisor calls are counted in-memory mocks. Static inspection found no candidate import-time process launch. The existing no-replace primitive is exercised only on isolated fixture paths.

The approved selection is the **134 mapped methods in `tests.test_current_host_inspection_v01`**, through the bound runner. The root must first verify that the clean source contains the exact reviewed module/tests and preserve the command, environment, logs, result, fixture tree/manifests and candidate identities under fresh run paths. The runner requires a fresh absolute retained-fixture root. Actual project OS child operations within the tested authoring paths remain zero; the outer authorized Python test harness is separate from those counters.

This decision does not authorize a replay after a failure or unknown run. Preserve the full attempt and reconcile the result before any new candidate/run decision. It does not authorize runtime installation, actual Node/ldd observations, H0/H1 qualification, original seven methods, the complete routine, integration, PR merge, or parent closure. Those gates remain open.
