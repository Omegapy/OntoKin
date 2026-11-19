# Conversation length: research and prompt repair

Sources accessed November 18, 2026, America/Denver. This note separates documented product behavior, observations from this session, and proposed workflow rules.

## Official findings

Three concepts must remain distinct:

1. **Conversation length** concerns accumulated content in a particular chat. A direct November 1, 2026 response by **OpenAI_Support** says that messages and replies contribute; the limit is not simply a fixed message count or chat age. It distinguishes this limit from temporary usage limits that reset. This is a support statement, not an inference from other users’ reports. [OpenAI Support clarification](https://community.openai.com/t/chatgpt-plus-conversations-reaching-maximum-length-unusually-fast-across-multiple-new-chats/1396609/37).
2. **Model context window** describes how many tokens the model can process in a request. Tokens are model processing units, not whitespace-separated words. API context specifications do not establish the maximum lifetime length of a browser conversation. [Understanding and counting tokens](https://help.openai.com/en/articles/4936856-understanding-and-counting-tokens).
3. **Usage allowance** limits available usage over a period. GPT-6 Pro Chat message allowances are separate from the shared Work/Codex allowance. A browser conversation-length error alone does not establish that either allowance is exhausted. [Managing usage with GPT-6 Astra](https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex).

No universal numeric browser conversation maximum was found in the official guidance reviewed. This is a research limitation, not proof that no unpublished or account-specific threshold exists.

ChatGPT Work subagents are available to eligible accounts. They delegate bounded work to agent threads and return results to the main conversation. Official guidance recommends returning summaries instead of intermediate output and notes that subagents consume additional tokens. It does not guarantee that delegation resets the parent’s length limit, creates a replacement user chat, or makes a conversation unlimited. [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

Codex documentation describes automatic compaction and the CLI’s `/compact` command, which summarizes earlier context. This does not establish a portable workaround for a full ordinary ChatGPT browser conversation. [Best practices](https://learn.chatgpt.com/guides/best-practices).

## Observed session and repository baseline

The current host exposes **four active-agent slots, including the coordinator**. This is an observed session tool constraint, not an official product-wide guarantee. Worker count must fit the available slots.

The coordinator independently measured repository content at `main` commit `6122bd272c3f5b960ed5c1d6434ebf5f7f9b4020`:

| Material audited | Characters | Whitespace words |
| --- | ---: | ---: |
| Nine required documents | 81,152 | 9,615 |
| Those documents plus three repository skills and C267 task, requirements, and plan | 108,280 | 12,806 |

These are content measurements, **not token counts**. The expanded selection includes the learning skill; it does not describe identical loading in every session.

## Proposed prompt rules

These are our design recommendations, not OpenAI requirements:

- Read the minimum context needed for the current phase; avoid repeatedly importing the complete document set.
- Use only the workers needed for independent, bounded tasks. Request concise findings and artifact references.
- Save recoverable state at phase boundaries: objective, decisions, completed work, current files, validation evidence, unresolved questions, and next action.
- Stop at the defined phase boundary. Resume a new phase in a fresh main conversation when appropriate, using the saved recovery state.
- Do not promise that a worker handoff or compaction will reset a browser conversation limit.
