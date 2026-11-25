# Action reference

The action ID is written to canonical history for a successful mutation. Use one action per helper call. `show`, `list`, and `validate` are read-only; they must not initialize a catalog or repair generated files.

| Action ID | User operation | Helper route | Canonical mutation | Generated-file write | Required authority or precondition |
| --- | --- | --- | --- | --- | --- |
| `TO-IP-001` | Create a draft plan | `create --input FILE|-` | Creates one `plan.json` | Creates plan projections and refreshes the managed index | Explicit skill activation, exact project root, reviewed create input |
| `TO-IP-002` | Show or resume an exact plan | `show SELECTOR` | None | None | Exact ID, exact directory name, or unique complete title |
| `TO-IP-003` | List managed plans | `list [--status STATE]` | None | None | Optional supported lifecycle-state filter |
| `TO-IP-004` | Revise the plan baseline | `update SELECTOR --expect-revision N --expect-sha256 HASH --input FILE|-` | Updates one `plan.json` | Rebuilds that plan's projections and refreshes the index | Current revision and SHA-256; material scope returns the plan to `draft` |
| `TO-IP-005` | Update phase content, dependencies, gates, scope, or risks | `update-phase SELECTOR PHASE-ID --expect-revision N --expect-sha256 HASH --input FILE|-` | Updates one `plan.json` | Rebuilds that plan's projections and refreshes the index | Current revision and SHA-256; phase status remains derived |
| `TO-IP-006` | Update task content or status | `update-task SELECTOR TASK-ID --expect-revision N --expect-sha256 HASH --input FILE|-` | Updates one `plan.json` | Rebuilds that plan's projections and refreshes the index | Current revision and SHA-256; legal transition and predecessor gates |
| `TO-IP-007` | Record task or requirement evidence | `record-evidence SELECTOR TARGET-ID --expect-revision N --expect-sha256 HASH --input FILE|-` | Appends evidence to one `plan.json` | Rebuilds that plan's projections and refreshes the index | Exact plan is `in_progress` for observed evidence; current revision and SHA-256; concise, criterion-linked, `result_status`-classified, non-secret evidence with a reviewable locator for agent/tool observations |
| `TO-IP-008` | Change plan lifecycle state | `set-status SELECTOR --expect-revision N --expect-sha256 HASH --status STATE --reason TEXT --confirmed` | Updates one `plan.json` | Rebuilds that plan's projections and refreshes the index | Current revision and SHA-256, transition gates, reason, current confirmation |
| `TO-IP-009` | Validate one plan or the catalog | `validate [SELECTOR]` | None | None | No confirmation; corruption or drift is reported, not repaired |
| `TO-IP-010` | Rebuild one plan's projections | `rebuild-projections SELECTOR` | None | Replaces only deterministic files for the selected plan | Valid canonical state; use after projection drift or partial publication |
| `TO-IP-011` | Rebuild the managed catalog index | `reindex` | None | Replaces only `Implementation_Plans/INDEX.md` | Every managed canonical record must validate; unmanaged content is ignored and preserved |
| `TO-IP-012` | Apply one bounded recovery | `reconcile SELECTOR --input FILE|- --confirmed` | Only when the reviewed recovery specification explicitly permits it | Only the reviewed recovery scope | Exact plan selector for plan scope or literal `catalog` for catalog scope, current confirmation, active-writer check, valid recovery specification |

Before any existing-plan mutation, run `show`, then pass the returned canonical revision and SHA-256 exactly. Mutation and recovery payloads are defined in [plan-contract.md](references/plan-contract.md).

## Operation notes

- Resume is a read-only `show`. Continue with a separate, explicitly requested mutation.
- Creation records a planning baseline only. It cannot preload completed tasks, satisfied requirements, or implementation evidence.
- Pause or block active tasks before a material baseline, phase, or task-content revision.
- `update-phase` cannot set an independent phase status or blocker. Record a blocker on its bounded task through `update-task`; the helper then derives phase state.
- A task can become `completed` only when its acceptance criteria have meaningful current evidence.
- A task cannot start or complete until its task predecessors and declared predecessor phases are complete or validly dispositioned as the contract permits.
- Evidence records separate type, `result_status`, and verification level. A planned result never reports a command or test as run.
- A task can become `skipped` only with a nonblank reason and current explicit authority. Its requirement coverage must also have an accepted disposition before plan completion. Revising either skip field while it remains skipped requires a new current confirmation.
- `set-status` does not execute work. The `ready` to `in_progress` transition records that the user separately authorized the exact plan; it does not broaden that authority.
- If a canonical write succeeds and projection publication fails, do not repeat the mutating action. Use `TO-IP-010` and, if needed, `TO-IP-011`.
- `reconcile` is not a general repair or migration command. Its only actions are reviewed `remove_abandoned_lock`, `remove_released_lock`, `remove_orphan_temp`, and `remove_partial_create` scopes. It never guesses missing intent or evidence, steals a live lock, adopts unmanaged plans, or deletes a managed plan.
