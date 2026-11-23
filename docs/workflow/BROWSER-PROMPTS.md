# Prompts for successive browser chats

Use one complete prompt in a fresh ChatGPT browser thread; replace bracketed inputs.

**Mandatory:** each fresh thread is a **different, ephemeral host**. Previous
filesystem paths, Python/Node installs and running processes are unavailable;
use saved GitHub/Library inputs and rebuild only what the current task needs.
Do not investigate previous virtual hosts. See [EPHEMERAL-HOST](EPHEMERAL-HOST.md).

| Situation | Prompt/inputs |
| --- | --- |
| Continue one declared phase; resume active scope before queued work | [Prompt 1: continue development](prompts/CONTINUE.md): latest successfully saved ZIP; optional task/phase override. Blank resumes active authorized scope; only with none active may it select the next bounded step from approved work. |
| Reconcile interruption; resume first unmet gate | [Prompt 2: recover interrupted work](prompts/RECOVER.md): last complete ZIP, any newer recovery file, brief interruption description. Never authorizes another milestone. |

The [entry point](../../CHATGPT-START-HERE.md) loads current instructions. Both prompts
require [PROTOCOL section 4](PROTOCOL.md#4-implement-delegate-and-bound-the-session)
and [HANDOFF.md](HANDOFF.md) in full: context controls, early recovery before
substantial/long work, verified saved handoff at phase stop, session/parent gates,
Library/receipt verification and online-continuation/C262 preservation boundaries.
A planned pause is not a blocker; continue unfinished work in a fresh parent chat.
Assume no token meter, advance length warning or automatic new-chat creation.

Each ZIP includes `PROMPT-1-CONTINUE.md` and `PROMPT-2-RECOVER.md`; HANDOFF governs
unique unpublished bytes/unknown operations, freezing and external save receipts.
[C264 clarification](tasks/C264/REQUIREMENTS.md) retains saved delivery;
[conversation-length repair](tasks/CHAT-LENGTH-20261118/REQUIREMENTS.md) adds explicit
phase stops/worker context controls without changing product scope.

A partial handoff leaves the parent `in_progress` or `review`.
