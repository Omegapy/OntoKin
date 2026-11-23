# C271 P25 startup reconciliation

## Verdict and scope

Startup reconciliation passes for the retained branch at `ce411b12e601036a33698aa7c3290722e602ea75`. The matching PR274/issue273 P24 terminal markers and the exact separately saved receipt resolve the P24 delivery-only pending fields. They complete the P24 design/adoption phase. They do not implement its design, accept H0/H1, satisfy the full required routine, authorize integration, or complete C271.

This report is the read-only Investigator result requested by the Director. It is not an independent review of new P25 implementation. The Investigator made no Git writes, network mutations, package installations, host reconstruction, H0/H1 invocation, product test, main lease action, commit, or nested-agent assignment. Its only written files are under `state/reconcile/`.

The active user direction, as assigned by the Director, permits one bounded P25 implementation phase on the existing branch. Early recovery must precede implementation; acceptance requires independent review of the adopted `/0.1.4` finite RTLD path policy and its frozen controls, followed by verified final ZIP/prompts and a separate receipt. Stop before H0/H1, host reconstruction and the full routine, or at the first concrete unplanned blocker. Older next-action text cannot override that current direction.

## Verified starting identities

| Record | Identity or result |
| --- | --- |
| Retained branch | `work/c271-missing-import-digest-control` |
| Startup branch head / P24 receipt commit | `ce411b12e601036a33698aa7c3290722e602ea75` |
| Receipt tree | `45f24af78edf83e42436aa9446b0b9b82c332c68` |
| P24 core source | `66866415e492e151eafd95da2237374fc127f79b` |
| Core tree | `546798a1d3cadc9cf4211c219827287d1ad1bc03` |
| Observed main supplied by Director and terminal record | `e43cc6c5777874101a40559e4058ad6826b07e51` |
| PR274 | Open, draft, unmerged; observed head equals receipt commit |
| Issue273 | Open; no closed timestamp |
| Initial local checkout | Clean and tracking the retained branch |
| Current P24 unknown operations | Empty in task, repository receipt, external receipt and terminal marker |

The receipt commit is a single-parent child of the declared core. Both commit trees were checked against the local object database. The PR snapshot's `base_sha` is the historical `e1a48f7d...`, and its `merge_commit_sha` is not evidence of integration: the same snapshot explicitly says `merged: false`. Neither field replaces the Director's actual-main observation. Main-only licensing changes and the newer disposable-host rule remain future integration/recovery constraints; this Investigator did not rebase or merge them.

## P24 delivery reconciliation

All 31 recorded reconciliation assertions passed. `RECONCILIATION.json` contains each assertion and its scope. They establish the following:

- Exactly one P24 terminal marker is present in each supplied PR and issue body. Both raw JSON blocks and parsed objects match exactly.
- The Director's `state/startup/p24-terminal.json` equals the independently extracted marker.
- The materialized external receipt is **36,911 bytes**, SHA-256 `7e0dc98c21df0b20022a787985ef2da1ccbf914b8e7697e1c103a9c9e952c3c7`. Its local stable-ID and version attributes match the terminal identity: `libfile_fde3_f-d83d5632eb8481919bfe76b293f664eb_2ab2a24d43748191957f9bcc356b59de`, version 0.
- The repository delivery record is **6,309 bytes**, SHA-256 `1f9a5328a477cb96ada583171ce5b9879b6da86e3c14e96be654e04978ac5244`. The external receipt embeds that exact JSON object and binds its exact size, hash and receipt revision.
- Core commit/tree, receipt commit/tree, ZIP identity, both prompt identities, prompt member names, parent requirement states and no-runtime boundaries agree across the repository receipt, external receipt and terminal marker.

The immutable P24 ZIP is **10,847,033 bytes**, SHA-256 `5b1886184add5644e1272c31c22f4f9232a8e76433d8f2f867fd826d8bf18e4e`, stable ID `libfile_fde3_f-4532fb4735348191ad2c16c84500e463_2ab2a24d43748191957f9bcc356b59de`, version 0. The Continue prompt is 1,765 bytes with SHA-256 `d11aedb5063739332044032114b21822933007e3d807a6df3768b4cdb2049e75`; Recover is 2,054 bytes with SHA-256 `37a50e73bc8083bc83a579a6d745e759f9fba8b49e3bdbf26b316cd90e1dd006`. This report verifies agreement of these saved identities and flags. It does not repeat the independent complete ZIP audit or independently rematerialize the ZIP/prompts.

The frozen canonical records legitimately say `terminal_receipt_pending`, and the separate receipt legitimately precedes its own save identity. Their explicit terminal-resolution contracts require the exact later marker/receipt tuple. That tuple is present and matches. P25 must preserve the frozen historical fields and add a source-backed reconciliation; replaying P24's already completed saves or publication is unnecessary.

## Parent state and remaining gates

| Requirement / plan | State at the reconciled startup |
| --- | --- |
| R01: independently frozen missing-digest control | `done` |
| R02: isolated refusal and propagation | `done` |
| R03: required checks and independent acceptance | `not_done` |
| R04: reviewed integration and actual-main verification | `not_done` |
| R05: complete parent delivery and truthful closure | `not_done` |
| P01 | `done` |
| P02 | `in_progress` |
| C271 | `in_progress`, open |

P24 adopted design only. Its **52 obligations** are **5 positive, 34 refusal and 13 fault** controls. **51** are future primitive/mocked checks; **one** is external review only. P24 records **zero executed controls** and zero production/test implementation changes, H0/H1 invocations, Node/ldd/direct-loader starts, product/full-routine invocations and package installations. These are historical P24 declarations, not fresh P25 execution results.

The original required routine remains failed/unmet: the P02 unit stage exceeded 900 seconds and its isolated documents stage omitted five tracked instruction files. Later P03 repaired the copy omission and passed focused checks, but that narrow repair did not complete the full routine. Historical exact Node and actual-host qualification limits remain preserved. P15's independently accepted exact-loader source review and N57's external-review classification do not become runtime passes or skips. A finite P25 control pass cannot close these parent gates.

P23's `H0-RTLD-ABSENT-PARENT-001` and related parent-traversing alias constraints remain the operational context. The unchanged literal loader list required `/libx32/ld-linux-x32.so.2` despite absent `/libx32`, and the required `/lib64/ld-linux-x86-64.so.2` alias traversed `..`. P24 supplies a reviewed future representation; it did not establish admission on any host. The stale P23 `remaining_h0_constraint.next_phase_action` is retained history, not current authority to restart design.

## Ownership and recovery limits

The Director owns canonical task/CURRENT records, Git/index, publication, scope selection and delivery. Startup task owner `c271-p24-660f372e2414` is the prior session owner; it is not an ongoing main lease. Branch STATUS's targeted ownership section records the prior C270 lease as released. P24's marker/receipt consistently state that no main lease was held. No main integration action is selected for P25.

The following unresolved historical observations must retain their original status:

1. C270 ancillary broad-driver completion.
2. Global prior-process termination.
3. P13's read-only character-level diff completion; do not retry it.

No current P24 unknown operation is declared. That does not prove universal process termination or absence of unpublished bytes on earlier hosts. This is a different disposable host: old absolute paths, installed environments and processes are historical evidence. They must not be treated as current resources or probed merely because they appear in a receipt. Known surviving P25 edits belong to the Director and its active implementation workers, not to an unknown P24 write.

The supplied status, workflow-run, review and review-thread snapshots contain empty lists. They establish no hosted-CI success and no independent GitHub review approval. This Investigator did not execute or request CI.

## Exact read coverage and limitations

`READ-SET.json` records full required source identities, Git blob IDs, byte counts, SHA-256 hashes, recovered truncation incidents and explicit partial reads. Full semantic content was read for branch AGENTS, ROLE, PROTOCOL, HANDOFF, CHATGPT-START-HERE, C271 REQUIREMENTS, PLAN, task.json, CURRENT.json and P24-DELIVERY.json, all bound to `ce411b12...`. The external P24 delivery receipt was also read in full. Ancestor AGENTS files were absent; the repository inventory found only the root AGENTS file.

Repeated Markdown blocks were read once with exact source references. Complete task/CURRENT JSON was read through a reversible `$id`/`$reuse` packet across nine chunks. Both reconstructed objects equal their exact Git source; all nine chunks concatenate exactly to the complete packet. No unique JSON key/value/node or substantive Markdown paragraph was filtered. Whitespace-only Markdown separators were omitted from the duplicate-reading packet only.

Initial combined tool output was truncated in several places. Every required missing portion was subsequently read in bounded output, and no required content remains missing or truncated. The broad path-location inventory was also truncated; no substantive read claim relies on that inventory. PR/issue historical body text was not read in full: their metadata and exact P24 markers were read for this reconciliation. STATUS was inspected only for ownership/lease evidence; global observed-main startup belonged to the Director. Referenced historical artifacts were not all reopened or re-audited.

The compact read packets were captured before the Director's later P25 canonical edits. Their identities were verified against `git show ce411b12:...`, so the read-set does not mix starting P24 state with newly authored P25 state. The Director reported P25 early recovery saved and byte-read-back while this report was being completed; that new package is outside this Investigator's audit.

## Next authorized action

The Director may continue the already declared P25 implementation on the existing branch after its confirmed early recovery, preserving older profiles, P06 output shapes, pins, limits, failed evidence and the external-review distinction. Independent review and final verified partial delivery remain required. Keep C271, PR274 and issue273 open, and stop at the bounded implementation/delivery checkpoint or a concrete blocker before H0/H1, reconstruction or the full routine.

This startup assignment ends here. No new phase is opened by this report.
