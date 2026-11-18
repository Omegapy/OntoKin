# Prompts for successive browser chats

Use one of these complete prompts at the start of a new ChatGPT browser thread:

| Situation | Prompt |
| --- | --- |
| Continue through one bounded next step and deliver its handoff | [Prompt 1: continue development](prompts/CONTINUE.md) |
| Recover an interrupted thread or finish a missing delivery | [Prompt 2: recover interrupted work](prompts/RECOVER.md) |

Copy the selected prompt and replace its bracketed inputs. Prompt 1 needs the
latest successfully saved ZIP link. A task override is optional; leaving it
blank authorizes selecting the next bounded step from current approved work.
Prompt 2 needs the last complete ZIP and, when available, a newer recovery file
and a brief description of the interruption. It resumes the remaining scope.

The repository [entry point](../../CHATGPT-START-HERE.md) loads current
instructions. GitHub holds current code and work state. Both prompts require
a verified session ZIP saved in the existing `OntoKin` Library folder before
completion. The [handoff contract](HANDOFF.md) defines its contents, verification
and delivery evidence. Each saved ZIP includes copies named
`PROMPT-1-CONTINUE.md` and `PROMPT-2-RECOVER.md`.

Save recoverable progress early and after meaningful stages. These procedures
do not depend on automatic conversation compaction or advance warning that a
thread will end. They cannot guarantee that an unexpected interruption occurs
after a save.

The session ZIP supports online continuation from GitHub. Preserve the C262
archive separately for its historical evidence and original offline recovery
contract. A smaller session ZIP does not replace that archive or claim to
contain all historical source material.

These updated replacement prompts implement the owner's November 18, 2026
clarification in [C264](tasks/C264/REQUIREMENTS.md). They preserve separate
continuation and recovery workflows; the complete earlier prompt wording was
not available for a line-by-line edit.
