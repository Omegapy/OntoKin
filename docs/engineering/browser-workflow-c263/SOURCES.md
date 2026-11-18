# C263 source register

Inspected November 18, 2026. These sources inform the workflow adaptation;
they do not grant tools or change OntoKin product semantics.

## User request and shared design

The owner asked to keep OntoKin in GitHub and give each new ChatGPT browser
thread directions that support continued development. The request includes
extracting requirements, making an implementation plan and implementing it
directly in GitHub, then waiting for further direction.

The three supplied reference files were read in full from Library, version 0:

| Reference | Identity | Inspected extent |
| --- | --- | --- |
| Sys4AI README.md | `libfile_fde3_f-7d0bc26f2f848191a429dc2957471d5f_2ab2a24d43748191957f9bcc356b59de` | 357 lines; 19,741 bytes |
| Sys4AI ROLE.md | `libfile_fde3_f-dba5bd6643d481919864f7a4bc563b1a_2ab2a24d43748191957f9bcc356b59de` | 323 lines; 18,390 bytes |
| Sys4AI AGENTS.md | `libfile_fde3_f-be7ed6821d348191a2d1016fbdbd7073_2ab2a24d43748191957f9bcc356b59de` | 175 lines; 9,701 bytes |

Their reusable design includes a Director, bounded roles, requirements and
plans, source-backed memory/learning, project knowledge and recovery. Their
local desktop service, depot propagation, native task/memory adapters and
advanced ontology implementation were referenced but not supplied. C263
implements its own smaller GitHub procedures and offline tool, without
claiming to import those missing packages. The references are design inputs,
not governing OntoKin instructions. No private conversation transcript or
desktop-specific absolute path is copied into the workflow.

## Official OpenAI documentation

1. [Prompting GPT-6.2 in Codex](https://learn.chatgpt.com/guides/prompting-gpt-6-2-astra).
   Applied ideas: explicit completion criteria, independent delegation when
   available, focused project instructions and review at the intended use
   conditions. Codex-specific host/model controls are not represented as browser
   features supplied by this repository.
2. [Using GPT-6, selected GPT-6 Astra guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra).
   Applied ideas: continue authorized work, resolve conflicting guidance,
   define delegation and calibrate verification to the actual task. The original
   parameterized page was used; its Markdown variant returned a different
   model page and was not treated as the requested source.
3. [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
   Its automatic discovery description is for Codex. C263 therefore explicitly
   requires the browser agent to fetch instruction files rather than assuming
   that a repository URL loads them.
4. [Build skills](https://learn.chatgpt.com/docs/build-skills).
   Repository procedures and installed/plugin-distributed skills have different
   discovery paths. C263 uses a registry and explicit full-file reads; it does
   not claim that adding SKILL.md installs a browser feature.

Actual available tools in this session included GitHub read/write, commit and
PR/merge operations, a Linux terminal and subagents. Those observations support
this implementation only. The protocol checks capabilities again in each new
session instead of assuming either universal access or universal restrictions.

## Linked video

[GPT 6.2 Astra Just Shocked The A.I World, TheAIGRID](https://www.youtube.com/watch?v=hx1wLU9fldA).
Direct public YouTube retrieval exposed the title, creator, description and
chapters, including a chapter about testing on one's own benchmarks. The
transcript service had insufficient credits; the public caption endpoint
returned no caption text. No full transcript or viewing is claimed.

The workflow's fresh-start, recovery and failure-path checks are our
project-specific application of the description's evaluation theme. They are
not presented as instructions quoted from the video. Claims about model
behavior or benchmark scores in the description were not adopted as facts.

## Repository and historical handoff

- Starting [main commit](https://github.com/Omegapy/OntoKin/commit/bbe30e2f5863d743bd2393466341511b4924ad9d),
  tree `aa192e047a7e7ddfd8e0436b5bae31f32bcb554a`.
- [C261 integration](../localized-repair-c261/INTEGRATION.md),
  [C260 contract](../localized-repair-c260/CONTRACT.md),
  [C252 decision](../review-integration-c252/DECISION.md),
  [local validation policy](../OK-ENG-006-local-validation-and-hosted-ci-policy.md)
  and [branch lifecycle](../OK-ENG-009-development-integration-and-branch-lifecycle.md).
- C262 root README, checkpoint, handoff and next-task files, plus the completed
  delivery checkpoint and closed [scope251](https://github.com/Omegapy/OntoKin/issues/251).
  Exact identities and migration limits are in [MIGRATION.md](MIGRATION.md).

The [requirements](../../workflow/tasks/C263/REQUIREMENTS.md) and
[plan](../../workflow/tasks/C263/PLAN.md) separate observed inputs from the
chosen implementation.
