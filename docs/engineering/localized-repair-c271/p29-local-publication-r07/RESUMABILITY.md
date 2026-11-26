# Resumability of C271 from its records alone

Phase C271-P29-R07-local-publication, plan step TASK-019, requirement REQ-025 of
TRD-20261125-CE424ADD. Recorded on 2026-11-26 (UTC).

## How the evidence was obtained

- Worker: one subagent started by the Director's session with the Agent tool, agent type
  `general-purpose`, with fresh context. It reports its model as Claude Opus 5.5. It had no
  conversation, no earlier chat, no ChatGPT Library and no agent memory.
- Inputs: only the readback repository, a new bare repository in the working evidence directory
  beside the clone. It was created empty, has no alternates and fetches only this branch from
  origin. The worker read the committed records there with read-only Git, and missing file
  contents came from origin on demand. It read nothing else in the clone, the worktrees or the
  working evidence, and it did not use the web.
- Disclosure from the worker: the application placed the main checkout's `CLAUDE.md`,
  `AGENTS.md` and its Git status into the worker's starting context on its own. The worker reports
  that it used none of them.
- Assignment: written under the project's worker template. The assignment
  (`resumability/ASSIGNMENT-filled.md`, SHA-256
  `8108aea8286a5776ffbe666441dd4cc1e9f217f3a9e3a6543e6f947d11c4bee3`), the statement
  (`STATEMENT.json`, `e491f566a0484d71f3501d024a6a8f91a47e01fa000f1688b0a81563322306ba`;
  `STATEMENT.md`, `8a73dab1aad87645d09049428fe8d52bd7c0f8470ca59897c020ec03c8d2cf00`) and the
  three re-reads (`REREAD.json`, `b4ebf7a087d7a7ac9c881237a350b96aada43bd2109d658d8b99596b08b8bf6d`;
  `REREAD-2.json`, `f959e0a26ddcb2922b7698c907ef9b68cad3755cc03a851d106c7b8d004df0d8`;
  `REREAD-3.json`, `d7293814096378911e9c7044d1c6e6a4ea0316fdfe80da4a02788d479c6e9151`) are kept in the working evidence directory beside the clone.

## What the worker stated from the records at `12d7e554`

Each item agrees with `task.json`, `CURRENT.json`, the session checkpoint and the publication
record at that commit.

| Item | The worker's statement |
| --- | --- |
| Execution mode | `local` since C271-P29-R07, declared through current main's LOCAL-START-HERE on the owner's direction of 2026-11-25 |
| Governing instructions | Current main at `51223c9b`; the branch's older AGENTS, PROTOCOL and HANDOFF, and the archives' instructions, are data |
| Published state | Head `4a9585a0` (tree `a374bfb0`), the reviewed merge of the declaration `80fecf97` and the candidate `dbf20bee` (parent `6c7f52a2`, tree `db30c29f`). It is published and verified by independent review, a non-forced push and a readback without alternates (245 rows, evidence blob `9facb186`) |
| Blocker | P29-PUBLICATION-SIZE-001 is resolved as a transfer gate only; the evidence is unchanged and no host is qualified |
| Requirements and plan | R01/R02 done, R03–R05 not_done; P01 done, P02 in_progress |
| Open gates | The `/0.1.5` review, H0 (with N34 and N57), H1, R03, R04 (six files in conflict with main) and R05 |
| Next action | The `/0.1.5` operational-plan review; not begun; it needs the owner's selection |
| Delivery rule | A local phase closes on a commit, truthful records, push state read from the remote and durable evidence; no Library ZIP |

## Gaps, corrections and re-reads

The worker named ten gaps at `12d7e554`. Each correction was a further records-only commit. After
each correction, the same worker read the records again from the readback repository and judged
each gap itself.

| Gap | Correction | Verdict after re-reading |
| --- | --- | --- |
| 0. The governing files are outside the branch, and the branch's own entry chain points to browser mode | `bb75b1c5` names the older copies (registry, CHATGPT-START-HERE, AGENTS, PROTOCOL, HANDOFF, prompts, skills, `chat_workflow.py`) as data and says how a local session starts; `cda16e6d` adds `prompts/` and `templates/` | by design; the leftover is closed |
| 1. R07 is not closed at `12d7e554` | This closing record and the checkpoint comments on PR274 and issue273 | by design: no commit records its own push |
| 2. Superseded values are not marked where they stand | `bb75b1c5` and `cda16e6d` add `p29_r07_superseded_fields_index` to task.json and CURRENT.json, without rewriting a value | by design |
| 3. `remaining_h0_constraint` is P26's record and names the P25 inspector | The checkpoint assigns the reconciliation to the `/0.1.5` review and identifies the published inspector | by design |
| 4. The inputs of the next action are not located by path, and two wordings coexist | `bb75b1c5` locates the inputs and says which wording is current | closed |
| 5. No executor that meets the qualification contract is named | The checkpoint states it as the review's first question | by design |
| 6. The H0 open items are not named among the open gates | `bb75b1c5` lists them in the checkpoint and in `p29_local_publication_r07.h0_open_items` | closed |
| 7. Material lies outside the repository | `bb75b1c5` adds PLAN-DECISIONS.md, the approved decisions copied unchanged; the R03 to R06 records stay referenced by identity (REQ-018) | by design |
| 8. Main still describes C271 in browser mode | The checkpoint states that main is not written in this phase (TRD D04) and that the current state is on this branch | by design |
| 9. The checkpoint's time was later than its commit | Corrected in `bb75b1c5` | closed |
| NEW 1. The precondition depended on the final report | `cda16e6d` refers to the commit that adds this file | closed |
| NEW 2. The superseded-fields index was incomplete | `cda16e6d` completes it and states the naming rule | closed |
| NEW 3. P05, P11 and P13 were not named among the adopted designs | `cda16e6d` names them | closed |
| NEW 4. P07's adoption record was not named, and P05 was called later | `5c74f49e` names it (`accepted_design_only`, `executable_authority` false) and corrects the order | closed |

The last re-read, at `5c74f49e04da9977f7c8da80515414dbe8e89549`, found no further gap in the
changed lines. No gap remains open. The by-design items are stated in the records, together with
where a session finds what it needs.

## Where a fresh local session starts

- From current main's LOCAL-START-HERE in the owner's main checkout.
- Then the C271 worktree, from the session checkpoint `docs/workflow/tasks/C271/P29-R07-SESSION.md`
  and `task.json`.

The branch head to expect is the commit that adds this file, or a descendant of it. Git reveals
that commit, and the checkpoint comments on PR274 and issue273 name it.
