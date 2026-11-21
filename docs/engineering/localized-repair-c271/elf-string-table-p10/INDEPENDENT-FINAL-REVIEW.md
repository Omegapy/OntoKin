# C271 P10 final independent implementation and evidence review

**Accepted for the bounded ELF string-table correction. No mandatory technical
findings remain.** Publication of the final documentary checkpoint and verified
saved delivery remain separate gates. This review does not complete C271.

Reviewer: `/root/elf_review`. Exact behavioral source:
`fdacc11349079be21bcce755b18ca660df4d96a2`, tree
`be6534bc800ad8be7b7ee4938d289b852503e534`. Inspector SHA-256:
`0c2ef54a227e2e05a7eb1f71a4fedd934399aa27d98ec7a3845f93a4dbfbb612`.
The Director owns canonical state, publication and delivery; this worker made
no repository or Git changes and has no integration authority.

## Implementation and independent expectations

The correction reads a dynamic string table across adjacent file-backed
`PT_LOAD` ranges. It partitions the virtual interval at segment boundaries,
requires one distinct file offset per partition, and joins checked reads in
virtual order. This handles separated or reversed file offsets and more than
two pieces. Equal-offset overlap remains accepted; differing offsets, internal
gaps and memory-only tails refuse. A larger containing segment cannot hide a
conflicting inner mapping.

Only the approved mapping block changed. The complete surrounding source is
byte-identical. Existing file/table/string bounds, interpreter and dynamic
guards, path policy, identity comparison and descriptor cleanup remain intact.
The new loops call the existing check callback; each piece uses the unchanged
bounded reader. Program-header and table limits keep work and allocation finite.

The independent corpus was frozen before candidate edits or parser execution.
It contains 16 successes, 17 refusals and seven fault recipes. Literal metadata
declarations and an independent per-byte mapping proof supplied expectations.
All published compressed inputs decode exactly to the frozen binaries, and
the published oracle matches SHA-256
`35b8535599cc24276dfe66e57b9ed80348c12d429e9a61441c4f449a7cb4ce8a`.
No expected value was changed after observing implementation behavior.

## Executed evidence

Keep these executions distinct; their overlapping cases are not additive
unique coverage:

| Evidence | Observed result | Meaning |
| --- | --- | --- |
| Original-source baseline | All 40 old-source predictions held; 16 matched the corrected oracle and 24 differed | Preserved evidence of rejected valid tables, ignored inner ambiguity and unreached later guards/faults |
| Director's focused suite | 175/175 methods passed: 135 unchanged inspection methods and 40 new mapping controls; zero failures, errors or skips | Focused implementation regression only |
| Independent candidate runner | 40/40 frozen cases matched; all seven injected faults triggered | Independently exercised the same mapping corpus, not 40 additional unique cases |
| Retained Python image | Two string-table pieces read, then unchanged loader-token refusal | Static actual-input observation; no H0 eligibility |

Both candidate runs bound the exact clean source identity before product
imports. Process guards were installed before imports, environments were
sanitized, and no process-operation attempt occurred. All 41 independent parser
calls closed their descriptors. The selected image's exact table reads were
2,600 bytes at file offset 1,496 and 39,666 bytes at offset 4,096.

The independent evidence audit verified all 175 method results and their
start/finish journal entries, all 277 retained input snapshots, the exact
135-plus-40 method inventory, and every retained fixture entry. The fixture
inventory contains 14,578 entries, including 9,895 regular files totaling
304,413,776 bytes. Regular-file hashes, symlink targets and special-file types
were checked without following links or opening special files. Every old
method retained its manifest, and every new case retained its exact observation.
No behavioral run was repeated during this audit.

## Remaining actual-input constraint

The retained selected Python image has exact SHA-256
`fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`
and 30,894,944 bytes. Independently decoded bytes establish the RPATH
`$ORIGIN/../lib`. The corrected parser actually returns
`CHI-UNSUPPORTED: Unreviewed loader token expansion` for that input, as frozen
before execution. Its earlier mapping refusal is resolved; the separate
existing policy refusal is preserved.

This result neither classifies the image as malformed nor approves a host.
H0 remains unaccepted. A future bounded phase must independently review the
remaining prerequisite before any loader-path correction or input substitution.
H1, Node/ldd observation, original-seven execution, the full routine, runtime
installation, main integration and parent closure remain outside P10. The full
routine remains a mandatory unmet R03 gate.

## Canonical documentary boundary

The later working documentary boundary correctly sets both C271 and
`CURRENT.next_action.status` to `blocked`, records
`H0-PYTHON-RPATH-TOKEN-001`, retains R01/R02 as done and R03–R05 as not done, and
leaves P02 in progress. Phase delivery and the final review were still explicitly
pending in the inspected bytes. No final archive save or parent completion is
claimed by those records.

The original candidate's workflow check failed because `in_progress` is not
an admitted next-action status. The exact failure is retained. The later
documentary correction passed fresh workflow, documentation and whitespace
checks; it changes no production, test, fixture or oracle bytes. Behavioral
evidence therefore stays bound to `fdacc1134`, while later publication/check
identities must be recorded separately.

The scoped learning record accurately preserves the mapping lesson, subsequent
policy refusal, early-package completeness correction and workflow-status
distinction. It makes no broader semantic or product claim.

## Failure preservation and remaining delivery gates

The first fixture construction stopped on a recovered-file mode discrepancy:
archived `0o600` versus observed `0o644`, with exact content identity and no
execute bits. Its script, partial corpus and logs remain. The successful second
construction records that distinction; the 40 fixture bytes and oracle are
identical between attempts. The first early-package deficiency and the original
workflow-check failure are also retained in the Director's evidence.

The Director may copy this review and change the corresponding pending-review
fields to accepted. Then publish the documentary checkpoint, verify production
and fixture equivalence to the executed candidate, and perform the applicable
published-record checks. The final ZIP still requires independent integrity and
inventory review, exact save/readback, matching continuation prompts and a
separate external delivery receipt. Stop after that partial delivery; do not
start the next phase or close the parent task.

No current unresolved operation is known for this worker. Historical C270
completion and global prior-process termination remain outside this review's
evidence. The Director remains responsible for live remote-state reconciliation.

Detailed identities and acceptance criteria are in `FINAL-REVIEW.json`, with
`PREEXECUTION-REVIEW.json`, `FOCUSED-EVIDENCE-AUDIT.json`, the immutable freeze,
baseline/candidate reports and raw logs retained separately.
