# Judgement of the fresh-session demonstration

**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md),
TASK-030; REQ-019, REQ-020, REQ-021, REQ-023, REQ-024 and REQ-029. **Judged by:** Director
`local-migration-f58a0f3c1d5a`, from the accounts, the repository and the sessions' own local logs. The
accounts stay as their sessions wrote them.

## Sessions

All were started by the owner in the Code tab of the Claude desktop application, version
6.28899.6, with the bundled Claude Code 2.1.330, on 2026-11-25.

| Session | What it was asked | Result |
| --- | --- | --- |
| First run, 18:37Z to 18:40Z, migration worktree, Worktree mode off, [account](FRESH-SESSION-1.md) | `Continue.` | **Does not count.** The Director had saved a private agent note at 18:32Z about the unpublished commit and about who may write the record. The application put it into this session, which read it before the checkpoint. The note was removed at 18:40Z |
| Check, 18:40Z, the same worktree | "Check where a session works" | **Does not count.** Worktree mode was off |
| **Clean run**, 19:09Z to 19:11Z, migration worktree, Worktree mode off, [account](FRESH-SESSION.md) | `Continue.` | Counts |
| Check, 19:52Z, the migration worktree | The same text, pasted from a link | **Does not count.** Worktree mode was off |

## Acceptance criteria of TASK-030

| Criterion | Judgement | Basis |
| --- | --- | --- |
| The Code tab opened the local project and ran the documented workflow; its version was read from the application | Met | Clean run: working folder, entry point `claude-desktop` and version 2.1.330 in its log; application version from the installed application. It read the entry document and the records, ran the doctor and both checks with the worktree's `.venv`, committed one file, pushed and confirmed the push |
| The account matches the repository records | Met | Task, environment, completed work, last completed gate, next action and blockers compared with [CURRENT](../../workflow/CURRENT.json), the ledger and the checkpoint at `d70d3ad90a6f03656cd383105c346ca1275774b9`: equal. Its four differences concern wording, the later commit, a path and statements it did not check |
| Shared instructions, Claude adapter and six skills loaded or discovered | Met | Its log shows exactly two instruction files before the first action, `CLAUDE.md` and the imported `AGENTS.md`; its skill list names the six project skills |
| On `Continue` the next unmet gate, nothing restarted, no milestone selected | Met | It carried out TASK-030 only and stopped; the commit changes one file |
| Worktree mode enabled deliberately, then checkout path and branch verified | **Not observed; waived by the owner** | Every session ran with Worktree mode off. On 2026-11-25 the owner directed: "This wasting a lot of time and tokens let's move one, gits works perfectly". The Director took this as the decision to go on without this observation. The rule itself stays in [LOCAL-PROMPTS](../../workflow/LOCAL-PROMPTS.md) and [LOCAL-SETUP](../../development/LOCAL-SETUP.md#work-in-a-second-worktree); no parallel editing took place in the application |

Verification step "used no content from the prior conversation": confirmed for the clean run. Its
log holds no memory index, no summary and no other session's text, the memory directory was empty,
and it did not open the first account.

## What the logs show beyond the accounts

- **Startup report.** Both accounts say that the startup items were reported. Both sessions
  observed every item and wrote it into the account, but neither showed the owner a report in
  its replies before it wrote the file. REQ-024 asks for that. LOCAL-START-HERE now says it more
  plainly (`402a7d8ed8512535e2f87ed123c3f6a7b418dea0`). One guided run with that text followed, a subagent
  in its own clone. Its prompt said that it was a fresh local session, that the folder was the
  owner's persistent clone, to read CLAUDE.md and AGENTS.md first, that the owner's only message
  was `Continue.`, and to write to the owner whenever the instructions ask for it; CURRENT and the
  checkpoint of its clone had been changed to hand it a rehearsal step. It replied with all seven
  items at 19:17:46Z and made its first change at 19:17:53Z. Because the prompt itself asked it to
  write to the owner, this does not show what the sentence causes. **No unguided session was
  observed to report first. The owner accepted this on 2026-11-25.**
- **Fetch.** The first run also ran `git fetch`, which changed nothing.
- **The instruction.** The application marked the text as pasted, because a link had filled it
  in; the owner sent it.

## Limits

One application version, one model and one machine. The Worktree switch itself was not seen by
the sessions; its state is read from what the application did. Nothing is claimed about the application's Worktree mode.
