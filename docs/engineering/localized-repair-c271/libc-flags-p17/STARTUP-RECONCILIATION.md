# C271 P17 record and scope projection

Worker: `/root/records_review`. Assignment: startup records only. No design decision, implementation, Git operation, repository change, remote write or host/product execution was performed.

## Verdict

The records support selecting exactly one P17 **DT_FLAGS / DF_STATIC_TLS compatibility-decision phase**, after reconciliation of P16 delivery and confirmation of a new early recovery save. The subject is the exact retained libc with `DT_FLAGS=0x18`. A supported decision may retain refusal. Implementation is not the next action selected by the accepted P16 adoption.

The controlling scheduling source is `docs/engineering/localized-repair-c271/libc-tags-p16/ADOPTION.json`, particularly `nonblocking_review_dispositions[N02]` and `next_fresh_chat_action`. It supersedes only the sequencing sentence in candidate `DECISION.md` section 6. It does not adopt a flag exception, change the candidate, or erase a refusal.

## Observed record state

- Director-supplied retained head: `81425ebd42c2b746b1b432231d02a1a7f6b5d6ff`; branch `work/c271-missing-import-digest-control`. This worker did not independently query Git or GitHub.
- Director-supplied observed main: `70ca7e68ff95df876f801137369d176fe5b2bab3`. Main's completed C270 state is expected while C271 remains unmerged.
- Parent `task.status` is `blocked`; R01/R02 are `done`; R03/R04/R05 are `not_done`; P01 is `done`; P02 is `in_progress`. PR274 is recorded draft/open/unmerged and issue273 open. These require the Director's live reconciliation, not inference from old records.
- P16 technical source is `6936405f0b9d35bb3748c4a8f57a3e2fb59e32c8`, tree `4dd88c2ee4b91d44fb18917df8691d9d04d1a15a`. The records say its partial ZIP/prompts were saved and read back. They deliberately still describe their own subsequent receipt publication and terminal preservation as pending. A matching later terminal receipt can reconcile those source-time fields; this review does not certify that external receipt.
- The actual P15 observation remains the earlier dynamic-tag refusal. The later flags predicate was not reached. The `0x18` versus unchanged `0x8` mask conflict is a static inference recorded in P16, not a newly observed product failure.
- Licensing changes on main/PR275 remain a later integration-reconciliation obligation. No rebase, merge or lease is selected by P17.

## P17 acceptance and stop

The Director should declare the following five gates in the new phase record before substantial work:

1. Reconcile the P16 exact archive/prompts/separate terminal receipt and live retained branch; independently verify and confirm a new early recovery save.
2. Produce a source-backed finite, separately versioned decision for the exact retained flags, with architecture/build applicability and independently frozen inert positive/boundary/refusal controls, or record a concrete unresolved design blocker. Do not presume the decision must admit the input.
3. Obtain independent exact-artifact/source/control review and resolve mandatory findings while retaining all prior candidates, failures and expectations.
4. Pass the applicable documentation/workflow/whitespace and protected-source checks; conditionally publish the retained branch and read back the exact result.
5. Independently verify and save the partial ZIP and matching prompts; publish a separate actual receipt; preserve unique late evidence and stop.

The technical stop is independent decision/control acceptance or the first concrete blocker/unplanned expansion. The remaining work in the chat is then documentary publication and delivery only. No implementation, product parser/test execution, input substitution, new H0/H1, runtime preparation/installation, Node/ldd, original-seven/full routine, native/model/hosted execution, main lease/integration, branch deletion or parent closure follows from this phase.

## Invariants

Preserve P16 and all older flag refusals, old/default parser routes, earlier profile/schema behavior, every existing contract/consumer shape, pins, dependency bytes, original controls and historical failure meanings. P16's adopted tag-only profile is `ontokin.current-host-readback-inspection-plan/0.1.2` with `linux-glibc-declared-python-origin-rpath-libc-plt-v1`; its existing flag policy is immutable history. Any future decision must be separately versioned.

Keep the P13 distinction between runtime checks and external source-completeness review. Synthetic labels must not become production admission inputs. Keep source operation/time ceilings at 100,000 / 30,000 ms and the existing 16 MiB document reader; do not invent a new cap for record convenience. Retain all file/table/string/mapping/callback/identity/resource guards. Saved runtime bytes do not qualify the current host.

The required complete routine and independent R03 acceptance remain unmet. A finite design/control result closes no parent requirement. Parent `blocked` and `CURRENT.next_action.status=ready` are compatible: the latter can describe authorized recovery work while the integration prerequisite is still unmet.

## Exact canonical update projection

| Record | Fields or section | Required treatment |
| --- | --- | --- |
| `task.json` | `/owner`, `/session_phase`, `/next_action` | Set current Director/phase/scope/acceptance/stop/actual state. Preserve the exact former P16 phase in `/prior_session_phases` before replacement, or retain an exact-revision record consistent with the existing P13 precedent. |
| `task.json` | `/delivery`, `/prior_phase_deliveries` | Preserve the P16 delivery record before creating truthful P17 delivery state. Do not mark early/final save confirmed before actual evidence. |
| `task.json` | `/requirements/2/evidence`, `/requirements/4/evidence`, `/checks`, `/completion/evidence` | Append actual P17 evidence when files exist. Record static checks separately from product tests. Do not rewrite old check outcomes. |
| `task.json` | `/status`, `/requirements/*/status`, `/plan/*/status`, `/completion/merge_commit`, `/completion/branch_disposition` | Keep `blocked`, done/done/not_done/not_done/not_done, done/in_progress, null and retained respectively. No design result changes these gates. |
| `task.json` | `/blocked_reason`, `/blocked_reason_history`, `/remaining_h0_constraint` | Describe the current unmet prerequisite accurately; preserve prior reason before material replacement. Keep the observed P15 tag-refusal constraint distinct from inferred later flags refusal. |
| `CURRENT.json` | `/latest_task`, `/active_task`, `/observed_main`, `/snapshot_date`, `/next_action` | Keep C271 pointers, record fresh observed main and an explicit UTC timestamp; set phase-ready action and real evidence sources. Allowed next-action statuses are ready/blocked/awaiting_user_direction. |
| `CURRENT.json` | `/latest_recovery`, `/previous_recovery`, `/older_recoveries` | Rotate only when the new early save is confirmed; retain every displaced record. |
| `CURRENT.json` | `/latest_handoff`, `/previous_handoff`, `/older_handoffs` | P16 stays latest until a P17 final handoff is actually saved; then rotate without loss. |
| `CURRENT.json` | `/boundaries` | Append the P17 scope/result distinction. Preserve historical boundary text, C262 identity, delivery policy and concurrent-main evidence. |
| `REQUIREMENTS.md`, `PLAN.md` | New P17 declaration and later outcome/delivery sections | Append the one-phase scope, constraints, acceptance, stop and evidence. Retain source-time P16/history wording. |
| `STATUS.md` | Current workflow paragraph only, under Director ownership | Update concise active phase and exact next action; retain integration-lease/history/domain state. |
| New phase directory/session record | Phase, readset, receipt reconciliation, reviews, checks, recovery, outcome, delivery | Use exact actual paths/identities. No fabricated future SHA or receipt. |

## Inputs and specification dependencies for the assigned technical workers

Use P16 `ADOPTION.json`, `PHASE-OUTCOME.json`, `design/candidate001/{DECISION.md,CONTROL-CONTRACT.md,FUTURE-SURFACE.json,INPUTS.json,CANDIDATE-MANIFEST.json,EXPECTATIONS.json}` and its independent review. Preserve candidate-manifest SHA-256 `61b18ceb15d3ee05d3022c60941ccbbce9c3e08bac148c7750da9f6588091156` and expectation SHA-256 `33a17cc66604f8b57be88dae7dd05a4bec066c0eaa191fc08400cfc79e18137e`.

The retained P15 input/refusal/source-completeness records and saved inert libc bytes supply the exact subject, rather than a new host search. The existing libc SHA-256 is `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`; the inspection module is bound at `a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4`. Technical workers must select and authenticate exact retained files from manifests before relying on them.

P16 INPUTS identifies the existing primary glibc 2.41 source archive (20,323,540 bytes, SHA-256 `f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998`), Debian `2.41-12+deb13u4` source patch archive (499,524 bytes, `dda4153511bfd543502d18e5bc9323110996fe9c531f14ae3fad6eb17f027c7d`), and `.dsc` (7,576 bytes, `0915324aa646bb99abfaa9aa6ecb734b30babd28454a3e51f3152912370fbd3e`). These are retained source inputs, not proof of a reproduced build or signature verification.

Inherited specification paths are P05 `ADOPTION.json` and `CONTRACT.md/json`; P07 `ADOPTION.json`, `HOST-INSPECTION-DESIGN.md`, `QUALIFICATION-PLAN.md`; P11 adoption and candidate004 decision/control/future-surface; P13 adoption and candidate001 decision/control contract. P16 INPUTS records their exact identities. This worker identified these dependencies; it did not independently reread their full technical contents or design a P17 rule.

## Read completeness and limits

All nine assigned governing/current files were fully read, including all 3,830 task.json and 1,349 CURRENT lines. Supplemental P16 adoption, outcome, dependency, input and future-surface records were also fully read. Three tool-output truncations occurred (REQUIREMENTS, a CURRENT excerpt, supplemental INPUTS); their missing ranges were explicitly recovered. There are no unrecovered required read gaps. Original bytes and hashes are retained in `readset.json` and `readset-bytes/`.

The supplied main capture initially had an extra trailing newline in some files. The Director later reported replacing it with exact Git bytes. The readset preserves the bytes actually read and distinguishes them from Git identities. This is a capture artifact, not an instruction change. Comparison of supplied governing text found only CURRENT and the current P16 STATUS paragraph substantively different; rules/policies/skills were otherwise equal. Full main startup remained the Director's assignment.

No external P16 save, live PR/issue, remote head, parser behavior or host state was independently verified here. The Director's reconciliation and technical reviewers own those gates. No active worker process or unknown write remains from this assignment.
