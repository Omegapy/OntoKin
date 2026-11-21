# P08 independent implementation acceptance

## Decision

Accept candidate004 for the bounded C271-P08 implementation scope: the accepted current-host-inspection authoring module and its focused static, filesystem and mocked-process tests. All mandatory findings raised during independent review have been addressed in the exact reviewed source. The complete authorized focused run passes, and its retained evidence matches the reviewed candidate and frozen controls.

This decision accepts implementation behavior demonstrated within that scope. It does not qualify the current host, approve generated HOST material, complete R03-R05, run the original seven methods, authorize runtime preparation or integration, or close parent C271. Final handoff/package review and verification of saved final bytes remain separate gates.

## Exact accepted candidate and run

| Item | Identity |
| --- | --- |
| Clean published source commit, recorded by root | cf16a0facebdce2fadf69e5c7fae6f2ca31cbd2e |
| Source tree, recorded by root | 5fcd7efc9037ed4f63fc39aa2b92f527256147b5 |
| Production module | 147900 bytes; SHA256 b2f4c869fd03919047db797bd3a80616cbe16f6b17689fe61d40754b27f97a39 |
| Focused tests | 139313 bytes; SHA256 797eb208670f6f74f14c9b5849485bd6cf3522a265d4129618c4b50ddc0a739a |
| Frozen control map | SHA256 9f9adb0979c228b6eede5f75db8a0649ddd3cebd73f239d29020e1c53a6c35b0 |
| Candidate freeze manifest | SHA256 717531625db8c7cf3c247134ef19072fd2bd17d04ea3d5a7e6aab6ee7955b3c3 |
| Run002 OUTCOME | SHA256 6fdd29cf01db6ac6e4687775e325a649cd4ca241ce1c18f1a00987a2b3cef42c |
| Run002 guarded result | SHA256 bdb1c97610acd162a03c10ed49af08af9cca51d36721a97fd54c2c927d66a8b0 |

Root's RUN-GRANT-002 binds the independent pre-execution approval, exact wrapper and clean published source. It precedes the retained start record. The start record and outcome agree on the command, PID and process group; the start timestamp falls inside the outcome interval. Root performed Git cleanliness/publication checks. The independent reviewer performed no Git operations and does not substitute filesystem hashes for root's clean-checkpoint evidence.

## Actual focused result

Every one of the 135 mapped methods has exactly one recorded `ok` result. The method set exactly matches the frozen map: 109 original negative controls, five positive controls, 16 supplemental groups and five scoped regressions. There are zero errors, assertion failures or skips. The unittest footer reports 8.288 seconds; the outer wrapper records 8.592660743 seconds, exit0, no timeout, no signals and no wrapper exception, within its 180-second bound. Failfast remains false. No additional attempt followed this result.

The guarded result agrees with stdout and the embedded outcome. All 16 process-operation guard counters are zero; the actual project operation counter is zero. The one outer Python harness child is recorded separately. These facts concern the instrumented focused run; synthetic supervisor PIDs and mocked starts in fixtures are not actual Node or ldd starts.

The reviewer read the complete result log, compared every method against the map, and verified all 12 retained input snapshots and historical postflight identities. All four current source/test/runner/map byte identities also still match their historical records at audit time. All 135 fixture manifests match their method roots and the selected method set. Their 14,185 entries comprise 9,680 regular files, 4,489 directories, 15 symlinks and one special entry. All recorded metadata and contents match; regular-file hashing covers 299,914,797 bytes. There are zero discrepancies.

`VERIFICATION.json` records the complete method mapping, per-method result, exact artifact checks and manifest identities. No production function was invoked to perform this audit.

## Acceptance against the material boundaries

The exact candidate reuses the complete static review and controlled fixture mapping frozen before execution. All 113 unique definition anchors match their reviewed source spans. Original expectations and the supplement remain unchanged except the separately approved exact-state correction, which was frozen before execution.

| Boundary | Evidence and scope |
| --- | --- |
| Closed plan, independent authorization and raw input handling | HI01-HI03 exercise closed shapes, digests, raw encoding/size and authorization separation with live validators. No malformed input is promoted into project bootstrap. |
| Source, runtime, Python, dependency and metadata bindings | HI04-HI06 plus SUP01-SUP03 and the named-Git regression cover coherent and isolated mismatches. Production constants have separate exact assertions; synthetic positive fixtures do not claim actual host eligibility. |
| ELF and loader closure | HI07-HI08 exercise real isolated binary/configuration/filesystem mutations, bounded traversal, alias/configuration/cache relationships and unsupported cases. No operational loader inspection occurs. |
| Evidence paths, reservation and drift | HI09-HI11 and supplements cover exact output paths, overlap/no-replace, bounded enumeration, live prelaunch/postflight guards and retained input drift. |
| Command and process accounting | HI12-HI17 and the strict-group regression exercise version/ldd parsing, mocked start receipts, malformed/count/identity cases, time and output limits, cleanup and uncertainty. Process boundaries remain mocked. |
| Persistence and read-only recovery | HI18-HI19, SUP05-SUP09 and SUP13-SUP16 cover real atomic-writer paths with controlled fault seams, no retry after publication uncertainty, exact retained graph relationships, append-prefix capture and immutable reconciliation. |
| Protected P06 projection | HI20 and SUP10-SUP12 verify the emitted host/inspection relationship and closed consumer-facing projection without modifying the protected consumers or schema. |
| Positive behavior | HI-P01 through HI-P05 provide static/constant, parser, full mocked two-command, atomic-writer and import/CLI controls. The successful mocked observation remains unapproved. |

All mandatory review findings PRE-01 through PRE-14, DTR-01 through DTR-09, C01-01 through C01-05, named PATH Git alias closure, C02-01 and the run001 fixture target defect have exact reviewed dispositions. The remaining limitations are the deliberately unperformed later-phase activities, not waived P08 requirements.

## Counts and uncertain evidence

Selected retained artifacts were read separately to corroborate the passing assertions. The HI-P03 mocked positive records one node-version start and one shared-libraries start, two total mocked direct starts and zero checker starts. Its immutable result.json remains PENDING_COMPLETION; the separately written completion record supplies OBSERVED_UNAPPROVED. That order is intentional.

HI14-D retains both ordered synthetic callback PIDs, 4242 and 4342. Its anomaly details record exactly two observed distinct starts and a lower bound of two, while total-completeness remains false and the normal single-start projection is unavailable. The same observations survive subsequent drift, committed-outcome failure and failure-record publication failure. No count is truncated to one or invented as zero.

HI17-D retains known count1 while overall state remains UNKNOWN when the final receipt/cleanup evidence is unavailable. HI18-A/B/C retain UNKNOWN for uncertain persistence. The source and passing assertions implement approved P08-D05, with count and preservation obligations unchanged.

P08-D06 remains explicit: read-only AS_RECORDED is a statement about retained graph/content, not a new durability proof. Its reported durability is UNKNOWN, evidence_finalized false and approval false, including the completion-directory-fsync case. A well-formed completion marker on disk does not silently remove the durability ambiguity. No extra write, fsync, replay or log-tail authority is introduced.

P08-D07 remains explicit: HI16-C isolates the live serialization-size guard with actual OS starts0, newly mocked supervisor starts0 and one supplied synthetic historical PID. Its original generic count reference stays preserved; the other mapped controls separately cover state-machine process counts. This is a route qualification, not a count or size waiver.

The selected on-disk states and identities are retained in RETAINED-STATE-SUMMARY.json. They are corroborating fixture evidence; they do not constitute current-host observations.

## Preserved failure and correction history

Run001 on candidate003 remains a failed attempt: 135 methods, 64 identical setup-error records across 39 methods, zero assertion failures and zero skips. The shared observation helper incorrectly passed a dotted attribute name to patch.object. The failed controls did not reach production observation. Independent static review missed that fixture defect; its prior approval was permission for a bounded attempt, not acceptance.

The authorized candidate004 correction changes only the owner/name pair in that patch call. Production bytes, every input mutation, expected result, assertion and control selection remain unchanged. Its exact one-line delta and refreshed bindings were independently reviewed before root granted run002. Run002 does not erase or relabel run001. Both attempts and every prior candidate/review remain part of the history.

The run001 initial audit's manifest-path and live-version comparison assumptions were corrected in a separately retained VERIFICATION-002.json. Both the provisional audit and its correction remain available. The run002 audit directly uses version-specific snapshots and the correct per-method manifest directory; it reports no errors.

## Review limits and next gate

This is an implementation acceptance under the user-approved P08 scope. The phase used finite static/filesystem and mocked-process controls. There is no evidence here of successful actual Node/ldd operation, current-host loader qualification, H0/H1 qualification, original-method/full-routine success or integration. Those activities remain deferred. Parent C271 stays open, with R03-R05 unfinished.

The next work is the remaining handoff/package gate: preserve the complete review and failed/passed attempt history, reconcile the handoff to this accepted candidate, independently verify the final package, and confirm the saved bytes. This report grants no additional test, runtime or publication action.

Reviewer activity: zero candidate imports, compilations, tests, project runtime starts, source edits or Git operations. All review actions were read-only inspection or bookkeeping writes inside review_work. No mandatory residual implementation finding remains within P08.
