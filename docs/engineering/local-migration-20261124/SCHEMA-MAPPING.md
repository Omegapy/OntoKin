# Workflow record schemas: earlier and current fields

**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md),
REQ-027 and REQ-028. **Tool:** [chat_workflow.py](../../../tools/chat_workflow.py).

The [registry](../../workflow/registry.json) and [CURRENT](../../workflow/CURRENT.json)
move to `schema_version` 2. Task, memory and knowledge records stay at schema 1; a
task record may carry one new optional field. The checker accepts both schemas of the
registry and CURRENT, so records written under schema 1, including those on the C271
branch and in historical handoffs, keep their meaning and still validate. Any other
version is refused. No record on another branch is rewritten.

## Registry

| Schema 1 | Schema 2 | Meaning |
| --- | --- | --- |
| `entrypoint` | `modes.browser.entrypoint` | Unchanged value. Schema 1 predates local mode, so its single entry point is read as the browser entry point. |
| `required_reads` | `modes.browser.required_reads` | Unchanged list. Each mode's list must contain its own entry point. |
| None | `modes.local.entrypoint`, `modes.local.required_reads` | Local entry point and read set. |
| None | `modes.*.declared_by` | What declares the mode: the entry document, or the recorded mode of a resumed task. Never a path or an agent name. |
| `repository`, `skills`, `task_root`, `memory`, `knowledge`, `current` | Same names | Unchanged. |

Schema 2 has exactly the modes `local` and `browser`, each with its own entry point, and
no top-level `entrypoint` or `required_reads`.

## CURRENT

| Schema 1 | Schema 2 | Meaning |
| --- | --- | --- |
| `project`, `latest_task`, `active_task`, `observed_main`, `snapshot_date`, `next_action`, `boundaries` | Same names | Unchanged meaning. `observed_main` stays a recorded observation that can be older than the actual head. |
| None | `execution_mode` | Mode of the selected task, or null without an active task. It must equal the active task's recorded mode. |
| None | `checkpoint.record`, `checkpoint.session` | Paths of the active task's record and its latest session checkpoint; the session may be null. |
| None | `unfinished` | Concise references to unfinished scopes that are not selected: task, state, mode, branch, observed head and time, pull request, issue, open gates and the record that explains them. |
| `delivery_policy` | `delivery_policy.browser` | Unchanged object. `delivery_policy.local` names the local closing contract. |
| `historical_handoff`, `latest_handoff`, `previous_handoff`, `latest_recovery`, `older_handoffs` | Linked by `history` | Not embedded any more. The unchanged earlier file is [CURRENT-before-migration.json](CURRENT-before-migration.json). |
| `previous_recovery`, `older_recoveries` and other embedded receipts of schema 1 records | Linked by `history` when such a record is compacted | Refused as embedded fields in schema 2. |
| None | `history` | Retained files with path, SHA-256, size, source commit, the keys they hold and their purpose. The checker compares digest and size with the retained bytes. |

A browser session that needs the C262 archive identity or an earlier saved handoff reads it
from the file that `history` names.

## Task records

| Field | Change |
| --- | --- |
| `execution_mode` | Optional; `local` or `browser`. Required for the active task of a schema 2 CURRENT, where it must agree. |
| `base_sha` | A new task records the commit supplied with `--base`, or the observed local head of the checkout. It never inherits `CURRENT.observed_main`. Without either, `new-task` refuses. |
| `base_observation` | Written into new drafts: where the base came from, and the recorded `observed_main` when it differs. |

`new-task` contacts no remote. A head that was observed on the remote, for example with
`git ls-remote`, is supplied with `--base`.

## Brief output

`brief` adds `modes`. `required_reads` is the read set of the selected task's mode; under
schema 1 it is the single read set, as before; without a recorded mode it is null, because no
mode is guessed.
