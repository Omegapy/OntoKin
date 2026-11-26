# C271 delivery requirement in local mode

Dated addition of 2026-11-26, phase C271-P29-R07-local-publication, owner
`c271-p29-r07-e586f7497142`. It adds a rule for the phases that follow; it changes no earlier
record.

## What C271 required so far

R05, unchanged: "Confirm early recovery before substantial work. Verify and save each phase
handoff and matching prompts; publish its separate receipt. Keep parent and scope issue open
until every requirement, integration and final delivery gate passes."

Every C271 phase from P01 to P29 R06 ran as a ChatGPT browser session. Each confirmed an early
recovery ZIP, saved a verified handoff with matching prompts in ChatGPT Library and published a
separate receipt. The branch's `docs/workflow/CURRENT.json` recorded this as its
`delivery_policy`: kind `browser-session`, required, completion gate "confirmed saved ZIP plus
external delivery receipt". The R02 next action also named "a verified saved handoff".

## The owner's direction

- On November 24, 2026 the owner moved ordinary development to the local clone
  ([decision](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/engineering/local-migration-20261124/DECISION.md)).
  A local session or scope closes on a source checkpoint, a truthful task and session record,
  verified push state when online and durable evidence; a ZIP is optional unless the selected
  task requires one. The decision keeps C271 separate and says that its own delivery
  requirements are reconciled when the scope is next selected.
- On November 25, 2026 the owner approved TRD-20261125-CE424ADD, revision 2, state
  `trd_done`, SHA-256 `063e8e1a88ef7224420c34dbdb92d2a25b4365a96962ad0e834951b652ff516b`, and
  the implementation plan PLAN-20261126-F3122BB2 with its decisions, and instructed: "execute
  PLAN-20261126-F3122BB2". The TRD's REQ-002 and REQ-003 select local mode for this continuation
  and require this reconciliation; its decision D03 explains it. The TRD is committed unchanged
  at `TRDs/trd_c271-p29-exact-publication-in-local-mode_2026-11-25.md` on this branch.

## How R05 applies from this continuation on

A C271 phase carried out in local mode closes on the local closing state of current main's
[HANDOFF, local sessions](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/HANDOFF.md#local-sessions):

1. a source checkpoint, which is a commit on this branch;
2. truthful records: `task.json` agrees with the acceptance actually reached, the session
   checkpoint follows current main's session template, and the branch's `CURRENT.json` points
   to both;
3. push state read from the remote, or recorded as unconfirmed when offline;
4. durable evidence: exact bytes, identities and a durable location, with failures and
   not-run checks.

In local mode, R05's "confirm early recovery" is met by a recoverable Git and checkpoint state
before substantial work (current main's PROTOCOL section 8, local rule), here the declaration
commit and its push. "Verify and save each phase handoff and matching prompts; publish its
separate receipt" is met by the four items above. A new ChatGPT Library ZIP, prompts or a
separate receipt is therefore not a closing condition of C271-P29-R07. If the owner later
requires a ZIP for C271, that adds only the package, verification and save rules.

## What does not change

- The wording of R01 to R05 and of every earlier phase section in `REQUIREMENTS.md`,
  `PLAN.md` and `task.json`.
- R05 stays `not_done`. Its last sentence still binds: the parent and the scope issue stay
  open until every requirement, integration and final delivery gate passes. In local mode the
  final delivery gate of the parent is the local scope completion of current main's HANDOFF:
  all task acceptance, verified integration and resulting main, observed branch and worktree
  disposition, and a closing report.
- Earlier handoffs, receipts, early recovery packages and failed observations keep their bytes
  and their interpretation. No historical ZIP, receipt or gate that was not met is recorded as
  passed, and no earlier phase's delivery state is changed.
- The browser-session policy stays recorded as the rule that governed P01 to P29 R06; the
  branch's `CURRENT.json` keeps it unchanged in `browser_delivery_policy_history`.
- A later C271 phase that runs as a browser session follows the browser rules again.
