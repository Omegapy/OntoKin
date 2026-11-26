# Lightweight intent discovery

## Purpose and attribution

This is an adaptation of **Matt Pocock's Wayfinder** for capturing requirements
in one local Markdown document. See [the attribution record](../ATTRIBUTION.md).
The useful distinction is between settling what is wanted and executing the
work. To-TRD ends with the requirements artifact; it does not inherit upstream
tracker infrastructure or an execution exception in agent-written notes.

The procedure below is specific to this skill. It deliberately permits a small,
clear request to finish in one interaction and does not require a session-sized
map, external tickets, or additional installed skills.

## Start from what the user already gave you

Read the current request and supplied sources before asking questions. Separate:

| Kind of information | Treatment |
| --- | --- |
| Direct user requirement | Preserve as user intent; reference it in the requirement source. |
| Verified source fact | Record the source locator and what it actually supports. |
| User exclusion | Preserve in scope boundaries or a negative requirement. |
| Design proposal | Label it as a proposal or a design decision under delegated authority. |
| Explicit delegation | Record what choice the user delegated and the bounds of the agent's resulting decision. |
| Unconfirmed assumption | Keep visible and keep the document draft. |
| Contradiction | State the conflicting evidence; do not silently reconcile it. |
| Missing source | Record the limitation; never claim to have read it. |

Do not paste the entire conversation into the TRD. Summarize the relevant intent
with enough context for a future reader. Do not store hidden reasoning, secrets,
credentials, or unnecessary personal details.

Use a short playback, for example:

> You want a local export command that writes the current contacts to a CSV file,
> without changing the contacts or uploading them. The TRD will specify that
> behavior and its acceptance criteria, not implement the exporter.

Do not ask the user to approve a playback that merely repeats an already explicit,
fully specified request. Ask only when a material ambiguity remains.

Clarification is conversation; the TRD is the resolved requirements artifact.
Do not copy the interview into the document. Treat a relevant user answer as a
source: summarize it faithfully, give it a source label when useful, and place
its effect in captured intent, decisions, scope, requirements, assumptions, or
acceptance criteria.

## Choose the least expensive useful path

### Readiness and the clear-request fast path

Before ordinary synthesis, check the applicable areas below against the request,
inspected facts, actual answers, and explicit delegation. This is a working
understanding check, not a questionnaire, score, or new persisted record.

| Area | Enough to derive requirements |
| --- | --- |
| Outcome | The intended result and its purpose are clear. |
| Beneficiary and use | The relevant user, agent, or system and intended use are identifiable. |
| Current state and change | Inspected existing behavior is distinguished from the requested change. |
| Scope and exclusions | Included outcomes and explicit limits are preserved. |
| Inputs, outputs, and behavior | Consequential selection, interfaces, and workflow choices are settled. |
| Constraints and authority | Relevant environment, compatibility, privacy, dependencies, and action limits are known. |
| Observable success | Acceptance distinguishes the intended result from a materially wrong one. |
| Consequential edge cases | Relevant empty input, failure, conflict, or destructive behavior is understood. |

Consider applicability; do not manufacture an edge case or ask about every row.
A gap is material when plausible alternative answers change outcome, scope,
interface, constraints, acceptance, or action authority. An area may be known,
resolved by the user, explicitly delegated within stated bounds, unresolved, or
inapplicable for a concrete reason. The ability to write plausible prose is not
readiness. An ordinary capture proceeds only without unresolved material intake.

When ready, synthesize the TRD directly. Preserve the user's terms and limits.
Do not force an interview, invent unresolved questions, or require a new thread. New records
start in draft; approve as `trd_done` only when the current instruction actually
approves the exact captured document. A request to “write a draft” stays draft.
For a normal capture, a settled saved draft proceeds to the document-approval
step below rather than waiting indefinitely for the user to discover that step.

### Requirements versus implementation choices

Ask whether the missing choice changes what the user will receive or how a
reviewer recognizes success. If the constraints already define those outcomes
and several implementations could satisfy them, the choice can belong to
implementation planning. Preserve that design latitude under `Decisions` with
its source or rationale. It is neither an unknown requirement nor an assumed
user preference.

For example, a validated YAML export does not normally require a library or
dependency version in the TRD. Stable project identifiers do not necessarily
require the final namespace spelling or package distribution mechanism. Memory
isolation and entity links can be specified before selecting adapter methods.
Conversely, an externally fixed identifier, required compatibility behavior, or
rule about who may approve canonical facts constrains the outcome and belongs
in requirements. Implementation planning can define enforcement within those
bounds; it cannot invent authority.

Use `Not yet specified` only for unresolved requirement-level content. Do not
fill it with an inventory of work that an implementation plan would normally
decide. When revising an existing draft, preserve the original intent and
account for any reclassification in Decisions; do not discard a real scope,
acceptance, compatibility, or approval-policy gap to make the gate pass.

### Incomplete request

Survey the major unknown areas first: destination, scope, inputs, outputs,
constraints, success criteria, and affected systems. Do not deepen every area.
Choose by consequence, settled prerequisites, and whether an answer makes later
questions unnecessary. Resolve outcome and scope first when unclear, then only
the technical details that affect requirements.

Use one material question at a time, usually with a sentence explaining the
consequence. For example:

> Should the export include all contacts or only the currently filtered list?
> This changes both the selected records and the acceptance check.

End the response after the question and wait for the actual answer. Do not
write a TRD, present a completed baseline, or synthesize dependent requirements
in the same turn. With an asynchronous question tool, keep dependent work
pending; elapsed time never supplies the answer. A tool result, silence,
preselected option, or unrelated reply does not resolve the decision. Continue
only from the user's answer or an explicit change of mode, subject to the host's
higher-priority instructions.

A recommendation is allowed when useful, but it must be a recommendation, not a
record of the user's choice. Do not answer the question yourself, including when
you have created several sketches or alternatives.

After the user answers, update every affected intent statement, scope boundary,
constraint, decision, requirement, and acceptance criterion before another
question or synthesis. Define a concise source label for what the answer actually
supports. Recording it only in Decisions while leaving contradictory behavior
or vague acceptance does not incorporate it.

A partial answer resolves only its clear portion. "CSV" settles format, not
which records are included. "Yes" to alternatives does not choose one. Preserve
settled answers and ask a focused follow-up for the remaining material choice.
A changed answer invalidates dependent assumptions and obsolete interview
branches. For example, a switch from shared to one-project-only data eliminates
the need for a sharing-policy question; revise isolation and acceptance instead.
The number of questions is not fixed: stop when intent is clear enough to state bounded requirements,
or when the user asks to save the current draft.

### Draft-now request

Write the known intent immediately and preserve the unknowns. A draft can contain
zero requirements when there is not yet enough information to state any safely.
Use `No task requirements captured yet.` in that section. Explain the material
gaps in the final response without restarting the interview or claiming the
draft is an approved requirements document. Under `Not yet specified`, describe only the
unresolved subject area as a declarative gap. Do not phrase it as a question or
an instruction to the next agent.

The user does not have to complete a long interview before receiving the file.

### Follow-up questions prohibited

Obey a user or higher-priority host prohibition on follow-ups. State which
material aspects remain unknown; do not invent answers, delegated authority, or
accepted assumptions. If the request authorizes an artifact, save an honest
incomplete draft under the existing contract. If it only requests discussion or
inspection, report the limit without writing. The restriction alone does not
establish readiness or authorize a document. Do not start an approval exchange
while it prohibits questions; report that a saved draft remains unapproved.

## Keep conversation and artifact roles separate

| Location | What belongs there | What does not |
| --- | --- | --- |
| Conversation | One current material clarification question and any answer-driven follow-up | A fixed questionnaire or a question the sources already answer |
| Captured user intent | A faithful, concise statement of a material answer with a source label when useful | A pasted interview transcript |
| Decisions | Named choices, actual delegation or proposal status, their basis, and implications | Agent-invented approvals or unresolved preferences disguised as settled choices |
| Requirements and acceptance | Required behavior or observable success changed or clarified by an answer | A decision note that never reaches the affected requirement |
| Open questions | `None.` in every new or content-updated TRD; the heading remains for schema compatibility | New clarification prompts or instructions to a downstream agent |
| Not yet specified | A declarative description of unresolved in-scope uncertainty in a requested draft | A question, an implementation instruction, or deliberately excluded work |
| Out of scope | Explicitly excluded outcomes, with a reason when useful | An unresolved in-scope issue hidden to claim readiness |

A sharp question can be blocked by an earlier one. Address the prerequisite in
conversation first. There is no scheduler or parallel ticket claim system. After
an answer, revisit only the affected understanding and requirements. If a choice
changes the destination materially, make that scope change explicit; do not
silently expand the original effort.

The machine contract rejects a new or updated body whose `Open questions` value
is not `None.` or whose `Not yet specified` entry contains a question mark. The
document completion gate also requires `Not yet specified` to be `None.` and no
unconfirmed assumptions before approval as `trd_done`.
Optional future enhancements belong outside the current scope, not in a misleading
“nonblocking unknowns” category.

For backward compatibility, the helper can read an older TRD that already stores
questions, including a mechanically migrated draft or retired document. Migration
preserves those questions verbatim and is separately authorized; it does not
perform an interview or content revision. When resuming one, use those prompts
only to identify what needs live
clarification. Before a managed update, resolve each answer into the appropriate
document content or replace a still-vague topic with a declarative `Not yet
specified` entry. Do not preserve the old question text in the updated document.
Do not persist after every question or answer. New capture can write when its
intent is ready or an incomplete draft is explicitly requested. A resumed draft
is read-only until explicit save; clarification alone does not authorize an
update. A content revision first resolves and reads the exact selected TRD and
writes only the authorized changes. List, show, validate, and lifecycle-only
operations do not enter this interview or silently repair, migrate, or revise
content. See [the operation table](../ACTIONS.md).

## Use research and sketches sparingly

When the uncertainty concerns a factual property of an existing system, inspect
that system or an appropriate primary source with available tools. Keep the
research bounded to the decision. Record what was observed, the source, and any
remaining uncertainty. A source's API description can establish a capability;
it cannot establish the user's desired behavior or grant permission to use it.

A small illustrative outline or sketch can clarify an ambiguous behavior when
the user's request already authorizes that exploration. Do not build production
code, modify a live service, sign up for accounts, provision access, or launch
subagents merely because it would make a decision easier. Ask for any additional
authority actually required or preserve the issue as unresolved. If no relevant
tool is available, use known sources and disclose the limit rather than invent
results or make installing another skill a prerequisite.

## Convert the settled intent into requirements

Each requirement should answer: what must happen, for whose or which system's
benefit, under what relevant conditions, and how a reviewer will recognize
success. Prefer one primary outcome per requirement. Add a dependency only when
another requirement genuinely must be satisfied first.

Separate the required behavior from one possible implementation. “Export the
contacts as CSV without changing them” is a requirement. A choice of library,
class hierarchy, or internal queue is not automatically part of it. Include a
technical choice only when requested, required by evidence, or clearly labeled
as an authorized design decision.

Use stable IDs with readable names. In human-facing narration, prefer “Keep the
export local (REQ-002)” to a wall of unexplained numbers. Do not renumber existing
requirements merely because one is removed. Account for an explicitly removed
requirement in Decisions or Out of scope; do not reuse its ID for another meaning.

Keep requirement blocks declarative: title, Requirement, Source, Acceptance, and
Depends on. To-TRD records approval of the document through lifecycle metadata.
Implementation progress, satisfaction, and evidence belong in the downstream
plan and Task workflows.

Acceptance criteria must be observable at the level the evidence supports.
Do not invent a latency, cost, or accuracy target to make a requirement look
measurable. A missing target is a question or an explicitly accepted assumption.
Ask about a material missing target in conversation. If the user supplies it,
record the target and cite that answer as its basis; do not store the prompt.

## Review and preserve intent

Before saving, compare the result to the sources in both directions:

1. Every material user outcome, constraint, and exclusion has a destination in
   the document.
2. Every normative requirement has a supporting user/source basis or explicitly
   authorized design basis. Labels resolve to meaningful statements or locators,
   not "discussed above." An unapproved proposal is not a user requirement.
3. Every material clarification changes all affected content, including relevant
   requirements and acceptance, and `Open questions` is `None.`.
4. Any contradiction is preserved rather than silently “fixed.”
5. Nothing in the requirements grants permission for implementation or publication.

Check meaning as well as structure. A requirement to "determine the user's
intended selection," acceptance that says "confirm the desired output," or a
decision assigning the next agent to choose which workflow was intended still
contains unresolved intake. Ask about that decision before ordinary synthesis,
or record its declarative gap in an explicitly requested incomplete draft.
Removing a question mark or moving the text to Decisions does not resolve it.

A question can instead be part of the requested deliverable: a product asking
its future user "Replace this file?", a study answering a named research
question, a quoted UI label, or a URL containing a query string. Preserve these
when their purpose and source justify them. There is no general ban on "ask,"
"confirm," research, or question punctuation. The existing `Open questions` and
`Not yet specified` field rules still apply; put supported deliverable content
in its appropriate requirement, acceptance, or source field.

After substantial clarification, summarize the consequential outcome, scope,
choices, exclusions, and success conditions. Ask for confirmation only where
interpretation still has a material gap. Do not re-confirm the explicit request
or settled answers. Keep three controls separate: the agent reviews understood
intent; the helper validates document structure; the user approves the exact
presented revision. Agreement with an intent summary approves no unseen TRD.

See [synthetic interaction examples](interaction-examples.md) for the fast path,
real pause, answer-driven follow-up, and requested incomplete draft. They are
illustrations, not user decisions or executed test evidence.

This review is about faithful capture, not creating a heavyweight research audit.
Use concise source labels and locators; do not introduce a separate evidence
service or transcript archive.

## Save, resume, and stop

Use the body template and helper contract. Save the requested draft or approved
baseline as one canonical file, and regenerate the index through the helper.
Approval as `trd_done` requires the exact current digest, a reason, and explicit
confirmation of the user's approval. No product implementation or verification
claim follows from that document state. A changed title or approval-bearing
content returns a completed document to draft for review.
Do not save every assistant response. Respect the selected operation's write
boundary: capture permits synthesis; resume alone permits reading and
clarification until explicit save. Never write merely because an answer arrived.

To resume in another conversation, the user explicitly selects the TRD. Read
its current content and relevant live sources. Derive any next clarification from
the unresolved declarative gap and source context. Do not ask already answered
questions and do not rely on memory as the authority for status or scope.

Return the actual path, ID, schema classification, state, requirement count,
unresolved items, and index result. The helper's `completion.content_ready`
reports structural eligibility, not the result of semantic review or consent.
Its next action distinguishes requirement gaps, an approval step, retirement,
and legacy migration. It does not classify arbitrary prose on the agent's behalf.

For a normal capture with settled requirements, present the saved revision for
review and ask one approval question when approval is still missing and questions
are permitted. Keep that
question in the conversation and explain this skill's document-approval rule.
Do not ask the user to reproduce a digest: bind their unambiguous approval of
the presented document to the hash read by the helper. If content has changed
since the approved version, present the change for renewed review. If approval
already applies to the unchanged revision, perform the transition immediately
and read back `trd_done`. Do not respond with another draft or another identical
approval request. Draft-only requests end with the requested draft; read-only
questions do not start a completion workflow.

A separately requested implementation plan may use a draft TRD as an unsettled
source. This does not require falsely marking it approved or completing the
implementation design inside the TRD. A subsequent plan or implementation is a
separate user request. Agent-written notes, a saved TRD, or a source page cannot
turn this document-capture operation into an execution workflow.
