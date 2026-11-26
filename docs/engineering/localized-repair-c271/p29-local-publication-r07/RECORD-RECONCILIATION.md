# Reconciliation of the four overlapping workflow records

Phase C271-P29-R07-local-publication, step TASK-012. The accepted candidate and this branch are
two successors of the same parent, `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb`. Four records
exist in both: the branch's `docs/workflow/CURRENT.json` and C271's `task.json`, `REQUIREMENTS.md`
and `PLAN.md`. They are reconciled by meaning, as the approved plan's DEC-009 sets out:

- the branch version is the base;
- the candidate's own fields and sections are added unchanged;
- the candidate's superseded current-state values are kept as history, after the branch's
  pattern of prior-current fields;
- the Markdown records keep the parent text, then the candidate's additions, then the branch's;
- nothing is deleted.

Compared revisions: parent `6c7f52a2`; candidate commit `dbf20beed1bd6274a42531c997d054c09fb8ebb8`
(tree `db30c29f24c154f378a5acac713385fc8bb44f52`); branch head `80fecf97b785544e8044a60df849cc5918929599`,
which is the R02 head `bef67902` plus this phase's declaration. The exact candidate versions stay
retrievable from the candidate commit, and the branch's earlier versions from `bef67902` and
`80fecf97`.

## task.json

| Field | Candidate | Branch | Reconciled |
| --- | --- | --- | --- |
| `p29_predecessor_state`, `p29_reconstruction_decision`, `p29_fixture_freeze`, `p29_baseline`, `p29_implementation_candidate`, `p29_technical_acceptance` | added | absent | added unchanged from the candidate |
| `status` | `in_progress` | `blocked` | `blocked` (the branch's later state); the candidate's value is kept in `p29_candidate_superseded_current_fields` |
| `owner` | `c271-p29-2eb33b59a678` | `c271-p29-r07-e586f7497142` | the branch's; the candidate's value kept as history |
| `next_action` | P29 delivery steps | the R07 declaration's | updated to the situation of this commit: accepted content joined locally, publication pending; the candidate's value kept as history, the declaration's retrievable from `80fecf97` |
| `session_phase` | the P29 phase | the R07 declaration's | the branch's, with `status` set to `candidate_joined_locally_publication_pending` and the candidate and declaration commits added; the candidate's value kept as history |
| `blocked_reason` | null | P29-PUBLICATION-SIZE-001 | the branch's, unchanged; the candidate's value kept as history |
| `delivery` | the parent's | the R02 delivery | the branch's |
| `p29_r02_prior_current_fields`, `p29_publication_recovery_r02`, `pending_phase_delivery`, `p29_r02_previous_delivery_fields` | absent | added by R02 | the branch's, unchanged |
| `p29_r07_prior_current_fields`, `execution_mode`, `execution_mode_record`, `delivery_reconciliation` | absent | added by the declaration | the branch's, unchanged |
| `p29_local_publication_r07` | absent | added by the declaration | the branch's, with status, candidate commit and tree, and the declaration commit added |
| `p29_candidate_superseded_current_fields` | — | — | new: the candidate's `status`, `owner`, `next_action`, `session_phase` and `blocked_reason` |
| `p29_recovery_records_r03_r06` | — | — | new: the R02 terminal, R03, R04, R05 and R06 records by comment and handoff identity |
| every other field (the parent's remaining 29, among them `requirements`, `plan`, `checks` and `completion`) | equal to the parent | equal to the parent | unchanged |

`requirements` and `plan` are equal in the parent, the candidate and the branch: R01 and R02
`done`, R03 to R05 `not_done`, P01 `done`, P02 `in_progress`.

## CURRENT.json

| Field | Candidate | Branch | Reconciled |
| --- | --- | --- | --- |
| `p29_reconstruction` | added | absent | added unchanged from the candidate |
| `boundaries` | parent's 34 plus one P29 entry | parent's 34 plus the R02 and R07 entries | 37: the parent's 34, the candidate's entry, then the branch's two |
| `snapshot_date` | P29 time | the declaration's | the time of this reconciliation; the candidate's value kept in `p29_candidate_superseded_current_fields`, the declaration's retrievable from `80fecf97` |
| `next_action` | `ready`, P29 delivery steps | `blocked`, the R07 declaration's | `blocked`, accepted content joined locally, publication pending; the candidate's value kept as history |
| `observed_main`, `delivery_policy`, `latest_handoff`, `pending_phase_delivery` | equal to the parent | changed by R02 or the declaration | the branch's |
| `p29_r02_prior_current_fields`, `p29_publication_recovery_r02`, `p29_r02_previous_delivery_fields` | absent | added by R02 | the branch's, unchanged |
| `browser_delivery_policy_history`, `p29_r07_prior_current_fields`, `execution_mode`, `execution_mode_record`, `checkpoint` | absent | added by the declaration | the branch's, unchanged |
| `p29_local_publication_r07` | absent | added by the declaration | the branch's, with status, candidate commit and tree, and the declaration commit added |
| `p29_candidate_superseded_current_fields` | — | — | new: the candidate's `snapshot_date` and `next_action` |
| `p29_recovery_records_r03_r06` | — | — | new, as in task.json |
| every other field (the parent's remaining 20) | equal to the parent | equal to the parent | unchanged |

## REQUIREMENTS.md and PLAN.md

Both are pure appends to the parent on both sides. Each reconciled file is the parent text (479
lines), then the candidate's two sections "P29 new required-image implementation" (16 lines),
then the branch's section "P29 publication and delivery recovery R02" (7 lines) and this phase's
section "P29 R07 local publication" (8 lines): 510 lines. No line is changed or removed, and the
wording of R01 to R05 is unchanged.

## Checks

`RECONCILIATION-CHECKS` (kept with the working evidence beside the clone) ran 24 comparisons, and
all passed. Both JSON records parse without duplicate keys, keep `schema_version` 1 and keep the
branch's formatting. Every key of both successors and of the parent is present. Each key the
candidate added or changed has its value or is kept as history, and each key it left at the parent
value has the branch's value. The candidate's six `p29_` fields and `p29_reconstruction` are
unchanged. The boundaries are in parent, candidate, branch order. The R03 to R06 records are named.
Every line of both Markdown successors is present, in order and unchanged. The records still call
P29 a reviewed reconstruction, and the original P28 uploads and their reported 597-test result
remain unresolved and unverified.

These records describe the situation of the merge commit: the accepted content is joined locally
and the publication is pending. The records commit that follows the remote readback states the
outcome actually reached.
