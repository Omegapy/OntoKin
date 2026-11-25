# Synthetic discovery examples

These fictional exchanges illustrate the [discovery procedure](wayfinding.md).
They are not recorded conversations, test results, or approval from the current
user. Each line labelled User is a separate future turn. Example requirements
are excerpts; a saved TRD still needs the complete body contract.

## Complete request: take the fast path

User: "$to-trd Save a draft for an export used by the operator of this local
contacts app. Export only the active filtered records, including all existing
fields, as CSV to a user-selected new local file. Reject an existing path without
changing it. An empty selection writes the field-name header only. Source
contacts must stay unchanged and there must be no network upload. Success means
exactly the selected records and fields appear, excluded records are absent,
and the source and any existing destination retain their bytes. No other work."

Agent action: Inspect any relevant supplied facts, review the supported intent,
and create and validate the requested draft. No intake question or redundant
understanding-confirmation exchange is needed. No document-approval question is
needed for this draft-only request. Return the saved draft's actual identity.

The [complete fictional payload](../assets/example-input.json) shows the same
selection and preservation choices. Its sources describe fictional intent;
they cannot approve a real record or authorize an exporter implementation.

## Ambiguous request: ask and end the response

User: "$to-trd Create a TRD for exporting contacts from this app."

Inspected fact S01: The supplied fixture has a complete contact collection and
an active filtered view. The fixture establishes existing capabilities, not the
desired export selection.

Agent: "The app has a full contact collection and a filtered view. Should export
include all contacts or only the active filtered view? This determines which
records the file and acceptance check must include."

Agent action: End the response and wait. No TRD or index write and no completed
baseline in this turn. A suggested option, silence, or an unrelated reply cannot
settle the choice.

## Incorporate the answer before choosing a follow-up

User: "Only the filtered contacts, with all existing fields as CSV. Keep the
export local and leave source contacts unchanged."

Working update: Label this answer U02. Set the selection, fields, format,
locality, and preservation conditions in intent, scope, and candidate
requirements and acceptance. Do not record U02 only in Decisions.

Agent: "The export will contain only filtered contacts with all existing fields.
If the selected output path already exists, should export reject it or replace
it? That choice determines whether an existing file can be changed."

Agent action: End the response without writing; the overwrite choice is still
material. Do not re-ask record selection or invent a replacement policy.

User: "Reject an existing path. For an empty filter, write the header only."

Agent action: Incorporate U03, discard any candidate overwrite behavior, and
briefly summarize the settled outcome, scope, exclusions, and success conditions.
If no material issue remains, synthesize at the new-capture save boundary. For
a resume-only operation, wait for explicit save before updating its record.

One resulting requirement excerpt:

```markdown
### REQ-001 — Export the filtered contacts
- Requirement: Export only contacts in the active filtered view as CSV, including every existing field, without changing source contacts.
- Source: U02 — synthetic selection, fields, format, and preservation answer.
- Source: U03 — synthetic empty-selection answer.
- Acceptance: With records inside and outside the filter, output contains exactly the selected contacts and every existing field; source records remain unchanged.
- Acceptance: An empty filter produces the field-name header and no data rows.
- Depends on: None.
```

The local destination and overwrite answer also require corresponding outcome
and acceptance text. A normal settled capture presents the saved draft for
exact-revision approval. Agreement with the prior summary did not approve this
unseen artifact. No downstream work follows from synthetic approval.

## Interrupted discovery: save the honest draft

User, instead of answering the selection question: "Save the current draft now;
I will decide the selection later."

Agent action: Save supported intent with this declarative gap:

```markdown
## Open questions

None.

## Not yet specified

The selection of exported records remains unresolved; it changes export behavior and acceptance.
```

Preserve other material unknowns too. Do not turn the gap into a requirement
that tells the next agent to discover what the current user intended. Keep the
record draft and report its limits without restarting the interview. If nothing
supports even one safe outcome, use `No task requirements captured yet.` instead
of a fabricated requirement block.

## Questions prohibited: respect both constraints

User: "$to-trd Discuss a possible export redesign. Do not ask questions or save
a document yet."

Agent action: Explain the known context and material unknowns without questions
or file writes. If the user instead explicitly asks to save an incomplete draft
with no questions, save known intent and declarative gaps only. A follow-up
restriction supplies neither the missing selection nor document approval.
