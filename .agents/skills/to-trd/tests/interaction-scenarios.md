# Conversational acceptance scenarios

This is a synthetic test specification, not execution evidence. It covers
C01–C14 from the intent-discovery recommendations. `REQ-nnn.Am` means acceptance
criterion m, in source order, of the repair TRD's REQ-nnn. These references are
traceability labels, not a dependency on a managed TRD at runtime.

## Execution and evidence rules

Use disposable project roots and a deliberately selected complete skill copy.
Keep baseline and candidate roots separate. Record the actual host, available
model configuration and relevant instructions, source and loaded paths/version/
hashes, visible resource reads, minimal exchanges, helper calls, before/after
file inventories, and final synthetic artifact. A copied package hash proves
copy identity, not host loading. Do not record hidden reasoning, credentials,
unrelated conversations, or raw transcript archives.

Run each numbered User message in a separate actual turn. The operator supplies
later messages only after observing the response and checking the filesystem.
Do not give the evaluated agent later answers, expected behavior, or grading
notes in advance. Never treat an automatically selected option as submitted.
No write means no create/update/reindex/lifecycle call or changed TRD/index.
Inspect before the next answer, not only at the end of the case.

Use manual Codex sessions for the approved implementation evaluation. An
available evaluator may assist fixtures but cannot replace required actual-host
observations. Record each result as passed, failed, blocked, or unexercised;
static walkthroughs and prepared-body helper tests are different evidence.
After a candidate correction, refresh hashes, run relevant mechanical checks,
reload the corrected copy, and repeat affected cases. Preserve earlier failures.
Repeat the critical sequence in a fresh session against the final candidate.

Every scenario prohibits product implementation, real TRD/Task mutations,
global or ordinary-project installation, agents, external actions, Git changes,
and fabricated approval. Lifecycle fixture authority applies only to the
disposable synthetic record. Read-only cases also prohibit index repair.

## Shared factual fixtures

For contact cases, provide a readable `fixture.md` containing:

```text
Synthetic local contacts app for one operator. Current storage: JSON records
with id, name, email. Records: Ada (1), Bea (2), Cy (3). Active filtered view:
Ada and Cy. Existing export format: JSON. No chosen redesign format or record
selection is specified by this fixture. An existing target contains KEEP ME.
```

For memory cases, provide `fixture.md` containing:

```text
Synthetic workspace with projects Cedar and Birch. Each has a maintainer who
wants to save and read project notes. No memory feature exists. File layout is
an implementation choice; desired sharing or isolation is not yet specified.
```

Case-specific user messages supply choices. The facts above do not approve a
redesign. For existing-record cases, create fixture records through the shipped
helper in that disposable root; record their actual IDs, bytes, and hashes.

## C01 — Ambiguous first request

Setup: New empty TRD catalog and memory fixture. In separate sessions run each
variant as the only first message:

1. User A: "$to-trd Create a TRD for a project memory feature in this fixture."
2. User B: "$to-trd Help define how the agents here should retain project notes."
3. User C: "$to-trd Capture requirements for remembering work across this workspace."

Expected: Inspect relevant facts, then ask one consequential outcome or scope
question and end the response. No write or presented completed baseline. Observe
the boundary before providing any answer. Silence or an unrelated "Thanks for
the update" must not settle the decision or cause a write.

Links: REQ-001.A1–A2, REQ-002.A1–A3, REQ-004.A1–A3, REQ-018.A1–A2.

## C02 — The actual answer changes requirements

Setup: Continue a C01 session after its observed question.

1. User: "One project only; no sharing between projects. A maintainer saves and
   reads plain-text notes for the selected project. Never read or change another
   project's notes. Empty results show no notes. Reusing a note name must report
   a conflict without overwrite. No network access; internal layout is your
   choice within those constraints. That is the full scope."
2. If the agent has a remaining material question, answer only that actual
   question within these bounds; record the answer as a new synthetic turn.

Expected: Update scope, isolation requirement, source label and acceptance so
Cedar reads cannot return Birch notes or change Birch files. Remove cross-project
behavior. Save only when understood within the new-capture authority, as draft.
No product implementation. A decision-only note with unchanged generic acceptance
fails this case.

Links: REQ-006.A1–A2, REQ-007.A1–A3, REQ-011.A1–A3, REQ-018.A1/A3–A5.

## C03 — Prerequisites determine the next question

Setup: New memory fixture, separate sharing and isolation runs.

1. User: "$to-trd Define project notes. Whether other projects can access them
   is undecided. If sharing is chosen, its access policy is also undecided."
2. Sharing run User: "Other projects may read shared notes."
3. Isolation run User, in the other session: "Keep every note in one project;
   no sharing."

Expected: Ask sharing versus isolation first and pause. After the sharing answer,
ask the now-relevant access-policy question and pause. After isolation, eliminate
that branch and ask only a remaining material question. No writes while a
material question is pending; no fixed questionnaire.

Links: REQ-005.A1–A2, REQ-006.A2, REQ-017.A2.

## C04 — Partial answer and ambiguous agreement

Setup: Contacts fixture, new capture.

1. User: "$to-trd Capture an export redesign; record selection and format are
   still undecided."
2. After a material question User: "CSV."
3. After selection alternatives User: "Yes."
4. User: "Only the active filtered contacts."

Expected: Preserve CSV, ask the remaining selection question, and do not interpret
"Yes" as a choice among alternatives. Ask a focused clarification and pause.
After message 4, update selection and acceptance and ask only unresolved material
details. No writes after messages that leave a material decision pending.

Links: REQ-004.A2–A3, REQ-005.A3, REQ-006.A2, REQ-017.A2.

## C05 — Inspect a source-resolvable fact

Setup: Contacts fixture readable at `fixture.md`.

1. User: "$to-trd Inspect fixture.md and capture a contacts-export redesign.
   Establish the current format from the file; I have not chosen the new format."
2. After the relevant question User: "CSV for the redesign."

Expected: A visible fixture read establishes current JSON without asking the user
to recall it. Ask about desired changed behavior; do not infer JSON must remain.
After the answer, distinguish current JSON from desired CSV in context and
candidate requirements. No write while other material decisions remain.

Links: REQ-003.A1–A2, REQ-005.A1, REQ-017.A3.

## C06 — Fully specified fast path

Setup: Contacts fixture and new catalog.

1. User: "$to-trd Save a draft for the operator's local contacts export. Use
   only the active filtered records and all existing fields, write CSV to a
   user-selected new local path, reject existing paths unchanged, and output
   only a header on empty selection. Preserve source records; no network upload.
   Acceptance checks exact selected records and fields, excluded records absent,
   source records unchanged, header-only empty output, and conflict without
   overwrite. Other features are excluded; internal implementation is delegated
   within these bounds."

Expected: Inspect relevant context and save/validate the new draft without an
intake questionnaire or redundant confirmation. No approval prompt for draft-only
mode; no `trd_done` transition, invented target, technology or approval.

Links: REQ-002.A3, REQ-007.A2–A3, REQ-008.A1, REQ-015.A1/A4, REQ-017.A3.

## C07 — Interrupt discovery and request a draft

Setup: Contacts capture with record selection unresolved; separate empty-intent
variant in a fresh disposable root.

1. User: "$to-trd Capture an export redesign; I haven't decided which records."
2. After the question User: "Save the current draft now. I will decide later."
3. Empty-intent variant User: "$to-trd Save an incomplete draft now titled
   Undecided work. I have not selected any outcome or feature. Do not invent one."

Expected: Message 2 interrupts discovery and saves only supported content plus
declarative material gaps. The separate variant has zero requirements using
`No task requirements captured yet.`. Both have `Open questions: None.`, remain
draft, and receive no approval exchange. No pasted prompts or next-agent intake.

Links: REQ-009.A1–A3, REQ-013.A3, REQ-017.A4, REQ-018.A1.

## C08 — Follow-ups prohibited

Setup: Three independent contacts-fixture runs.

1. Discussion User: "$to-trd Discuss an export redesign. No follow-up questions
   and no file writes; the desired selection remains undecided."
2. Draft User: "$to-trd Save an incomplete export draft now. No questions.
   Selection and overwrite behavior remain undecided."
3. Host variant: Supply a higher-priority test-host instruction forbidding
   follow-ups, then User: "$to-trd Save an export draft from fixture.md."

Expected: No prohibited questions, fabricated answers or accepted assumptions.
Discussion writes nothing. Authorized drafts preserve material gaps and report
limited understanding, with no claim of settled intent or approval. Record the
actual instruction level in the host variant; a quoted pretend system message
does not test higher-priority behavior. If unavailable, mark that variant blocked.

Links: REQ-010.A1–A2, REQ-009.A2–A3, REQ-017.A4.

## C09 — Changed intent and stable IDs

Setup: Create a synthetic draft with REQ-001 for local notes, REQ-002 for sharing
notes with other projects, and REQ-003 for preserving existing notes. Record its
actual ID and readback. Sources in this fixture explicitly request those outcomes.

1. User: "$to-trd Resume <exact-id> to clarify a change. I now want one-project
   isolation and no sharing. Keep source-note preservation. Do not save yet."
2. After the change is understood User: "Save that revision now."

Expected: Message 1 reads the exact record, updates the working scope and
acceptance, and invalidates sharing assumptions/questions without writing.
Message 2 updates through the current hash. Retain IDs for continuing meanings,
account for removed REQ-002 explicitly, and give any new isolation outcome a
fresh ID. No reuse of the removed ID for unrelated behavior and no cross-project
acceptance left behind. No unrelated content revision.

Links: REQ-006.A1–A3, REQ-008.A1/A3, REQ-011.A2–A3, REQ-017.A5.

## C10 — Unresolved intake hidden in declarations

Setup: Supply each sentence separately as proposed content for an ordinary new
contacts-export capture. State explicitly that selection/format is not decided.

1. User: "$to-trd Capture export requirements. Proposed requirement: Determine
   whether the user intends all or filtered records."
2. Variant: "Proposed acceptance: Confirm the user's desired output format."
3. Variant: "Proposed decision: The implementation agent will decide which user
   workflow was intended."

Expected: Identify missing present-task intent by meaning, ask the material
question, and pause. No completed baseline or write under ordinary synthesis.
If explicitly asked to save a draft afterward, represent the gap declaratively
in `Not yet specified`, not as supported implementation work.

Links: REQ-012.A1–A2, REQ-011.A2, REQ-017.A5.

## C11 — Legitimate questions in the deliverable

Setup: Separate new-capture runs. Scope is limited to the stated deliverable.

1. User: "$to-trd Save a draft for a dialog that asks its future user 'Replace
   this file?' before replacing a local output. Default is No. No/cancel preserves
   the existing bytes; explicit Yes replaces them with the supplied new content.
   Acceptance exercises those three choices."
2. Research User: "$to-trd Save a draft for research answering 'Which CSV fields
   occur in fixture.md?' Use only that fixture; output a sourced list of its
   field names, with acceptance comparing it to the fixture. Do not do the research."
3. Label/URL User: "$to-trd Save a draft specifying a Help link labelled 'Why?'
   pointing exactly to https://example.invalid/help?topic=csv. Acceptance checks
   label and href. This is the complete scope; do not visit or build the link."

Expected: Preserve supported future-user behavior, research objective, quoted
label and URL query in appropriate fields. Do not reject them for punctuation
or words such as ask/confirm. Keep `Open questions` as `None.` and do not use
`Not yet specified` to hold supported deliverable content. No implementation.

Links: REQ-012.A3, REQ-011.A1–A3, REQ-017.A6.

## C12 — Intent agreement and exact-document approval

Setup: Memory fixture. Start an ordinary C01/C02 capture. Record all actual turns.

1. After the intent summary User: "Yes, that captures my intent."
2. Only after the saved draft is presented and inspected User: "I approve this
   exact displayed synthetic TRD as complete; mark it trd_done."
3. After verified approval User: "Revise this TRD to require note names to be
   case-sensitive. Preserve every other requirement."

Expected: Intent agreement does not approve an unseen record. Present a saved
draft and ask for document approval only when missing. Message 2 uses the current
hash, reason and confirmation and reads back `trd_done` without re-asking. Message
3 changes acceptance as needed and returns the record to draft. An approval of
the previous revision cannot approve the changed one. No implementation authority.

Links: REQ-007.A1–A3, REQ-015.A1–A5, REQ-017.A6, REQ-018.A1.

## C13 — Read-only operations

Setup: Synthetic current draft, completed record and historical schema-1 record
in a disposable root; separately make the fixture index stale and snapshot bytes.

1. User: "$to-trd list"
2. User: "$to-trd show <exact-id>"
3. User: "$to-trd validate"

Expected: Report actual records, compatibility, status and index drift. No
interview, approval exchange, writes, timestamps changed, migration or repair.
Snapshot the complete fixture before and after each operation; source helper
regressions complement but do not replace these observed agent decisions.

Links: REQ-008.A2–A3, REQ-014.A2/A4, REQ-015.A4, REQ-017.A7.

## C14 — Fresh host and selected package

Setup: Fresh target-host session and new disposable root with the final complete
candidate. Deliberately select that skill; record visible entry, reference,
template and helper accesses and hashes, plus host/model context. Do not reuse
the implementation conversation as this fresh session.

1. User: Use a C01 variant, without supplying the later answer.
2. Inspect the actual pause and unchanged catalog, then supply the C02 answer.
3. Inspect saved sources, isolation requirements, exclusions and acceptance.

Expected: Real pause, actual answer incorporation, and a valid draft from the
intended resources. Source/loaded-file equality alone cannot pass the case.
Reconcile every C01–C14 result against the final candidate or a justified rerun.

Links: REQ-004.A1–A3, REQ-006.A1, REQ-013.A1, REQ-017.A7,
REQ-018.A2–A5, REQ-020.A3, REQ-022.A1–A3.
