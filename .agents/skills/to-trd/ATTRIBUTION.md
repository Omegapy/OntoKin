# Attribution and source provenance

## Wayfinder — Matt Pocock

The intent-discovery procedure in this skill is a lightweight adaptation of
**Wayfinder, created by Matt Pocock**.

- Supplied source: https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder
- Specific source file: https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md
- Supplied explanation: https://www.aihero.dev/skills-wayfinder
- Inspected license: https://github.com/mattpocock/skills/blob/main/LICENSE
- Review dates: **2026-08-28** and **2026-09-02**.
- Inspected SKILL.md **Git blob SHA**: `812805b760baf328db0ebdef6f3807e381f97016`.
- Inspected LICENSE **Git blob SHA**: `f1dd2c09108dde1a5f56097cee8461b3ea834499`.

These are blob identifiers, not commit hashes. The branch URLs may change after
the review. The exact inspected upstream MIT notice is retained in
[licenses/wayfinder-MIT.txt](licenses/wayfinder-MIT.txt), including
`Copyright (c) 2026 Matt Pocock`.

The borrowed conceptual approach starts from the desired destination, separates
decisions from execution, clarifies material uncertainty, and keeps human choices
with the human. Upstream Wayfinder keeps a decision question in its ticket and
records the answer when that ticket is resolved. This package adapts that boundary
by keeping clarification questions in the conversation and writing their resolved
answers into one local requirements document. It does not bundle the complete
upstream skill or require any upstream companion skill to be installed.

The TRD schema, document lifecycle, action-ID contract, Python helper, templates,
indexing, and tests were created for this request. The source's tracker, assignment,
branching, and scheduling machinery is not included. The upstream license notice
identifies upstream material; it is not a claim that Matt Pocock authored these
new components or endorses this package. No AI Hero article text is vendored.

## User-supplied Task system plan

The uploaded `task_system_implementation_plan.md` (dated 2026-08-27) informed
canonical-state versus generated-index separation, file safety, and requirement
traceability. It is a proposed implementation plan, not proof of a running system.
Its response ledger, paired skills, first-turn hooks, task JSON state, director
integration, absolute local paths, and planning-only authorization are not adopted.
The current user separately authorized this skill's implementation.

## Format and host references

- OpenAI, Build skills: https://learn.chatgpt.com/docs/build-skills
- Agent Skills specification: https://agentskills.io/specification

The package uses their documented local skill format and explicit-invocation
metadata. Runtime model obedience and installation in a user's Codex host must
not be inferred from these references or the package's structural tests.
