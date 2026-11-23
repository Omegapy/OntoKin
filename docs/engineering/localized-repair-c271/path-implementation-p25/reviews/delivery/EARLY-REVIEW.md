# P25 early recovery and canonical-record review

Reviewer: `/root/reconcile`. Scope: the saved early package, its saved readback, and
Director-owned P25 records. This review does not inspect or accept production code,
test adapters, H0/H1, a reconstructed host, or the full product routine.

## Result

The saved early ZIP and readback are exactly equal: **11,037,136 bytes**, SHA-256
`d61fbea806e0d9c8218f3e57291a13e25d23df50b9bd33bec2d67801a47ac188`.
The save metadata and both files' stable-ID/version attributes agree with the
receipt: `libfile_fde3_f-8cf9630339b88191a2cc889964f5284e_2ab2a24d43748191957f9bcc356b59de`,
version 0. The receipt now distinguishes the durable Library path from the
historical local build path.

`EARLY-AUDIT.json` records **50 passed checks and one package-only documentation
finding**. ZIP CRC, safe relative names, duplicate detection, exact inventory,
all payload sizes/hashes, all 27 frozen Git source bindings, mandatory snapshots,
and fresh extraction passed. All 42 files were extracted into a fresh audit-owned
directory and verified. The temporary extraction was then removed. The P24 ZIP,
external receipt and terminal marker are exact; the nested P23 archive is also
present at its correct P24-relative path with its declared size/hash.

The finding is that root `HISTORICAL-DEPENDENCIES.json` is unchanged P24 metadata.
Its P23 predecessor path is therefore relative to the embedded P24 ZIP, although
that namespace was not explicit at the P25 root. No recovery bytes are missing.
`EARLY-PACKAGE-CLARIFICATION.json` now binds the immutable early ZIP hash, declares
the nested namespace, names P24 as P25's actual predecessor, and supplies the
portable source/reconstruction mapping absent from the brief early host note.
This resolves the ambiguity for bounded online continuation **when the
clarification accompanies the package**. Preserve and publish that clarification
with the final evidence; the final ZIP must have its own P25 dependency wrapper.
The original finding remains recorded rather than being converted to a clean
package-only result. `EARLY-AUDIT-SUPPLEMENT.json` records 11 passed checks of
the clarification and retained ownership readbacks.

The clarification subsequently received its own durable save. The independent
`EARLY-CLARIFICATION-SAVED-AUDIT.json` records six passed checks: saved/readback and
repository bytes equal, exact 2,024-byte/hash identity, matching save metadata,
and stable-ID/version attributes. Its identity is
`libfile_fde3_f-f60165abf6588191983a9ae019d060cd_2ab2a24d43748191957f9bcc356b59de`,
version 0, SHA-256
`b70fa654bbc89327615864b6884b2634762921889cd4d9daf676e38df74b3e23`.

## Canonical state and preservation

The current task owner now correctly identifies P25. `WORKERS.json` preserves the
completed startup assignment and records the independent delivery assignment.
`SESSION.json` distinguishes the initial declaration from startup reconciliation's
actual completion at `2026-11-23T14:07:05.431593+00:00`. Source hashes for the
Director's declared read set match Git; this is identity verification, not a claim
that this reviewer observed the Director's reading process.

Against `ce411b12e601036a33698aa7c3290722e602ea75`, REQUIREMENTS and PLAN retain
their exact old byte prefixes and append only the P25 scope. Task/CURRENT changes
are bounded to current ownership, next action, phase/delivery and appended
history. Prior phase/delivery/recovery objects remain exact. Requirements,
parent plan, historical checks and constraints are unchanged. The entire P24
design directory is unchanged. C271 stays `in_progress`; R01/R02 are done,
R03–R05 are not done; P01 is done and P02 remains in progress.

The later retained PR/issue readbacks have identical new P25 prefixes and preserve
their complete old bodies as exact suffixes. They show the P25 owner, early saved
identity, open issue273 and draft/open/unmerged PR274 at the starting head. Their
startup-role sentence is source-time history; the current WORKERS record owns
the later reassignment. No main lease is held. The local observed main reference
still equals `e43cc6c5777874101a40559e4058ad6826b07e51`; this auditor performed no
new network read or mutation.

## Coverage and limits

Full historical instruction/task coverage is recorded separately in
`startup/READ-SET.json` and the preserved `state/reconcile` evidence. For this
review, all root package prose and new P25 record changes were read; all payload
bytes and source bindings were checked mechanically. The complete nested history
was not reread or unpacked. An oversized ownership-body display was repaired by
reading the complete new prefix and relevant metadata, and comparing the old
suffix mechanically; no full historical-body reread is claimed. The package
truthfully records startup reconciliation as incomplete at its earlier freeze.
The saved early receipt predates the later P25 declaration. No implementation or
target-runtime acceptance follows from this delivery audit.

Reproduction: run `audit_early.py` from this directory's source revision while the
listed immutable inputs and current documentary snapshot are available. Later
phase-state changes can legitimately require a new report; do not overwrite this
report merely to obtain a green result.
