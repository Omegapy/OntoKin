# C231 independent component review

**Decision: APPROVE_COMPONENT_ONLY** for exact author commit `e9f811dbd0d32d16aea55ce90ca3615a138a3416`, tree `e21381900f793a5fd30f9ef8fe2124d848e928c8`. Ledger SHA-256: `1436c7f10c4ba35fae5d90e7a4201c3bf7d92315d2baa385dcbd8de89f807c03`. The working tree was clean and the checked source remained unchanged during all independent execution. This approval covers the selected ledger identity/lifecycle repair, additive CPU controls and its C231/0.1 contract.

## Result

The repaired ledger retains the original marker and journal file objects while its capability can mutate. This prevents a recreated file from inheriting authority through identical bytes and recycled numeric inode/device values. Existing pathname, bytes, type/link, no-follow/nonblocking, directory, journal and append checks remain. Terminal and uncertainty paths poison the capability and account explicitly for releasing its retained handles. The four approved protocol files, schedule, historical bindings, original diagnostics and original failing test remain unchanged.

The unchanged baseline failed the intended identity guarantee in both independent deterministic replacement controls: marker and journal each accepted a reservation and remained live when the recreated file's observed numeric identity was forced to match. This is a controlled reproduction of the documented mechanism, not a claim that either new baseline run observed actual filesystem inode recycling.

On the repaired source, **17 independent control groups / 136 assertions passed**. Both replacement cases reject and a separate subsequent operation reports STOPPED. The controls also cover real retained-file observations, terminal observations and completion, five creation-fsync boundaries, a post-append interruption, disposal, repeated close with caller-descriptor protection, and PID rejection before an inherited mutex.

Two additional context-exit cases and two interrupted-cleanup-lock cases also passed. The same probes had exposed real defects in earlier author revisions; their failed results remain separately preserved.

## Review findings and corrections

| Finding | Correction and evidence |
|---|---|
| A concurrent fork could copy a pin during open/registration or removal/close. | Coordination now covers retained-handle ownership transitions. Author's bounded real fork control covers a held parent mutex plus a second capability paused during acquisition; child pins close, child use rejects, parent remains usable, and the child exits and is reaped. |
| An interruption during final cleanup could leave in-memory completion true. | Cleanup attempts all pins, poisons state and clears completion on failure, and propagates a new interruption when no original error is active. |
| `__exit__` could replace an existing body error with cleanup PERSISTENCE. | Exceptional context exit preserves the original body exception object. The independent ValueError and KeyboardInterrupt cases fail on `71e5e1722262ef5abe7e6169f539f63104dd8ee2` and pass on this candidate. |
| Invoking a one-shot finalizer before an interruptible coordination acquire lost ownership of still-open pins. | Explicit release acquires coordination and closes the owned container before detaching finalization. An interrupted acquire retains pins/finalizer, reports stopped/uncertain, clears completion, and preserves an existing ORDER error. Later close performs the first close attempt successfully. Both cases fail on `8e7e4fca361358a87fc34b722d4e558e2140ba12` and pass on this candidate. |

The lock-acquisition controls do not repeat an uncertain descriptor close: no close began before that injected acquisition interruption. Once a descriptor close has been attempted, its numeric descriptor is never retried. The contract explicitly limits automatic garbage-collection/shutdown cleanup to best effort under asynchronous interruption and prefers explicit close/context use. It also retains the existing trusted-host boundary and unchanged directory-identity behavior.

## Affected checks and preservation

The author's final stable-source cohort executed **307 methods: 284 existing and 23 additive**, with zero failures, errors, skips, expected failures, unexpected successes or unrun methods. Its source/result/log bindings were independently inspected. This is the author's execution, not a second 307-method run by the reviewer. The real CPU fork is a lifecycle control, not native product execution.

Independent preservation checks pass all 42 approved protocol/source/role bindings and all 301 inherited locked-input bindings; these inventories overlap. All 33 historical ledger-digest files remain exact, with their 51 recorded pin locations unchanged. The entire original 36-method ledger test module and its original failing method remain byte-identical. Git tree comparison limits the candidate to one changed ledger source, one additive test module and one new contract; all other pre-existing tracked files remain unchanged.

No original hash was rewritten to hide a dependency change. Old diagnostic plans remain consumed and pinned to their old implementations. No full product aggregate or native application was executed by this reviewer. R02, prior failed aggregates, receiving/normal gates and held drafts remain unresolved as previously recorded.

## Integration and evidence

No blocking source or component-check finding remains for this bounded repair. Root retains ownership of applicable integration/source/core/document checks, live repository/lease reconciliation, exact publication, restore/archive verification and confirmed final handoff saving. This component approval does not complete R02 or a release.

`REVIEW.json` binds the exact candidate, original baseline observation, independent scripts/results, author cohort and preservation records. The detailed contract/dependency audit and all actual failed probes are retained alongside it. No further optional test expansion is requested.
