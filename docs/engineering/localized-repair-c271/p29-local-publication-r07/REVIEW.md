# Independent review of the C271 P29 publication candidate

Phase C271-P29-R07-local-publication, plan step TASK-015, requirement REQ-019 of
TRD-20261125-CE424ADD. Recorded on 2026-11-26 (UTC).

## Reviewer and independence

- Reviewer: one subagent started by the Director's session with the Agent tool, agent type
  `general-purpose`, with fresh context. It reports its model as Claude Opus 5.5, the same model as
  the Director; the project requires an actual separate worker, not a different model.
- Independence: the reviewer had no access to the Director's conversation, authored and edited
  none of the reviewed commits, and was told to treat the Director's evidence files as data and
  to recompute instead. It wrote only inside the review directory of the working evidence beside
  the clone. It was a review, not a self-review.
- Assignment: written under the project's worker template. The assignment
  (`review/ASSIGNMENT.md`, SHA-256 `98ef126534d1e0887fc920c08f6b629dd3fa5d5da6b59b6defc8d7308e763816`),
  the report (`review/REVIEW-REPORT.md`, SHA-256 `cb9d3904e1cba46d383d6e05f0ec4fd934d0e51621043297fad1e74a64d4ec97`)
  and the result file (`review/REVIEW-RESULT.json`, SHA-256
  `1c27591fc3279f828c790c8de61c6c1ef5d016e4b3c58b314c2401c192b0a283`) are kept in the working
  evidence directory beside the clone with the reviewer's six helper scripts.

## What was reviewed

| Commit | Role |
| --- | --- |
| `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448` | branch head before this phase |
| `80fecf97b785544e8044a60df849cc5918929599` | declaration commit of this phase |
| `dbf20beed1bd6274a42531c997d054c09fb8ebb8` | candidate commit; parent `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb`, tree `db30c29f24c154f378a5acac713385fc8bb44f52` |
| `4a9585a0ce66b1ff0b407e41824d68b2417c2686` | merge commit under review, tree `a374bfb05f9ffea1b894efeb336e30260113aca9` |

## What the reviewer recomputed

It used 57 checks, run with read-only Git commands and with Python reading the R06 archive in
memory. It ran no project tool and did not contact GitHub.

- The candidate commit's single parent `6c7f52a2` and its tree `db30c29f`.
- The R06 archive, receipt, corrected R05 version 1, R03 and accepted inner archive identities,
  the CRCs and member-name safety of all four archives, and the binding of the inventory to the
  outer manifest.
- All 245 inventory rows against the payload bytes in the accepted inner archive and against the
  candidate tree (path, mode 100644, blob, size). The difference from `6c7f52a2` is exactly those
  245 paths.
- In the merge, the 241 accepted files other than the four workflow records. The evidence archive
  is the ordinary blob `9facb186ec11523163520323d83dc58fd68e829c`: 25,817,783 bytes, SHA-256
  `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038`, not an LFS pointer.
- The merge's parents and the ancestry of `bef67902`, `80fecf97`, `dbf20bee` and `6c7f52a2`.
- That every one of the 21,963 paths of `bef67902` is present and unchanged except the four
  records and the paths that the payload supplies, and that the only other additions are this
  phase's records, the session checkpoint and the TRD.
- The reconciliation of the four records by meaning:
  - nothing of either successor is lost;
  - the candidate's six `p29_` fields and `p29_reconstruction` are unchanged;
  - its superseded current values are kept as history;
  - each Markdown record is the parent, then the candidate's lines, then the branch's;
  - R01 to R05 and P01/P02 are unchanged;
  - the task stays `blocked`, with publication pending.
- The claims in this phase's records: none says the publication is done, none says R03, R04,
  R05, C271, H22, C260 or the product is complete, none says a test passed, and none says that
  local readiness qualifies the Linux contract. No credential, account name or home-directory
  path appears.

56 checks passed. One check failed: the reviewer's accuracy test of a declaration statement,
reported as finding O-01.

## Findings and resolutions

None is mandatory.

| Finding | Observation | Resolution |
| --- | --- | --- |
| O-01 | `DESTINATION-INSPECTION.json` and `PHASE.json` say that the 47 candidate blobs present remotely are unreachable from the branch. Four of them, the four read before this phase (`e69de29b`, the empty blob; `40357d22`; `8354e190`; `771a7df9`), are blobs of `bef67902`'s own tree at other paths. Only the other 43 are unreachable. | Confirmed by the Director. The records commit adds a dated correction to `PUBLICATION.json`, `task.json` and the session checkpoint. The pushed declaration records are not rewritten. No step depended on the statement. |
| O-02 | The session checkpoint and `PHASE.json` in the merge are still the declaration versions. | The records commit replaces the session checkpoint with the outcome version. `PHASE.json` stays the declaration record, and the outcome is in `PUBLICATION.json`. |
| O-03 | The checkpoint does not yet name where the REQ-032 test and environment facts are recorded. | The outcome checkpoint names them: main's `STATUS.md` and `docs/engineering/local-migration-20261124/RESULTS.md`, read at `51223c9b`. |
| O-04 | `MAIN-CONFLICTS.md` is linked from no record. | Linked from the outcome checkpoint, `task.json` and `PUBLICATION.json`. |
| O-05 | The Markdown dates are UTC but unlabelled; the owner's direction is dated 2026-11-25, America/Denver. | Later Markdown records of this phase label UTC. |
| O-06 | The R02-era fields `latest_handoff`, `pending_phase_delivery` and `delivery` could be read as current. | The records commit adds a pointer saying that they are R02's source-time records, that the later handoffs are named in `p29_recovery_records_r03_r06`, and that this local phase produces no handoff. The R02 values are not rewritten. |
| O-07 | `DESTINATION-INSPECTION.json` has no final newline. | No change: the record is frozen, and the finding is cosmetic. |
| O-08 | Some committed records cite working evidence kept beside the clone (`EXECUTOR`, `RECONCILIATION-CHECKS`, raw logs), and the merge's own checks were not yet committed. | The records commit adds `CHECKS.json` with the executor identity embedded, and `PUBLICATION.json` with a summary of the reconciliation checks. |

The resolutions are records-only changes made after the accepted head. They are not part of the
publication candidate that was reviewed.

## Disposition

**Accepted** for publication: exactly `4a9585a0ce66b1ff0b407e41824d68b2417c2686`, tree
`a374bfb05f9ffea1b894efeb336e30260113aca9`. Any change to it would need a new review. The
acceptance covers neither the push, the remote readback nor the later records commit. It
qualifies no host, completes no requirement and approves no integration.
