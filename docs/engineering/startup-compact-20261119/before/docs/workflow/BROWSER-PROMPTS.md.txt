# Prompts for successive browser chats

Use one complete prompt in a fresh ChatGPT browser thread and replace its
bracketed inputs.

| Situation | Prompt |
| --- | --- |
| Continue one declared phase; resume the active scope before selecting queued work | [Prompt 1: continue development](prompts/CONTINUE.md) |
| Reconcile an interruption and resume its first unmet gate | [Prompt 2: recover interrupted work](prompts/RECOVER.md) |

Prompt 1 takes the latest successfully saved ZIP and an optional task or phase
override. A blank override resumes an active authorized scope; only when none
is active does it authorize selecting the next bounded step from approved work.
Prompt 2 takes the last complete ZIP, any newer recovery file and a brief
interruption description. It never authorizes another milestone.

The [entry point](../../CHATGPT-START-HERE.md) loads current instructions.
[PROTOCOL section 4](PROTOCOL.md#4-implement-delegate-and-bound-the-session) owns
the common context controls: one phase per chat, applicable instructions read
once, bounded workers with fresh context when supported, compact reports and
detailed evidence in files. Subagents do not reset the parent conversation.
These procedures assume no token meter, advance length warning or automatic
new-chat creation.

Both prompts require a confirmed early recovery ZIP before substantial or long
work and a verified saved handoff at the declared phase stop. A partial handoff
can finish the session while the parent task stays `in_progress` or `review`.
A planned pause is not a blocker. Continue that task in a fresh parent chat.
Only all acceptance, integration and delivery gates establish task completion.

[HANDOFF.md](HANDOFF.md) defines the required contents, exact verification,
Library save and external receipt. Each ZIP includes `PROMPT-1-CONTINUE.md` and
`PROMPT-2-RECOVER.md`. Preserve unique unpublished bytes and unknown operations;
freeze once and do not rebuild just to add the later save receipt.

Session ZIPs support online continuation. Keep the separate C262 archive and
its historical offline recovery obligations unchanged. The [C264 clarification](tasks/C264/REQUIREMENTS.md)
retains its saved-delivery requirement; the [conversation-length repair](tasks/CHAT-LENGTH-20261118/REQUIREMENTS.md)
adds explicit phase stops and worker context controls without changing product scope.
