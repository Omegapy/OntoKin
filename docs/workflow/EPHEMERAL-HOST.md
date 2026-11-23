# Ephemeral host rule for ChatGPT browser development

**Mandatory for every new OntoKin ChatGPT browser discussion.** Treat each new thread as operating on a **different, disposable execution host**. Never assume the new thread has access to the previous thread's virtual machine, filesystem, installed tools, Python or Node environments, packages, processes, running subagents, environment variables, mounts, working directories, or temporary files. This is an operational rule, regardless of how the platform implements session isolation.

## Durable continuity versus host-local state

- **Durable project state:** live GitHub repository objects, source commits, active issues/PRs, and actually saved, verified ChatGPT Library files (plus any separately verified persistent service).
- **Nonportable state:** paths such as `/workspace/scratch/...`, `/tmp/...`, previous checkout locations, installed dependencies, temporary virtual environments, staged executable trees, in-memory processes, prior host inventories, and uncommitted files not saved in a handoff.
- Previous host paths, machine profiles, readback inventories and installation receipts are **historical evidence**, not claims that anything exists on the current host. Preserve their original hashes, modes, commands, paths and provenance; do not rewrite them to pretend they refer to this session.

## Startup and execution on the current host

1. Read the latest verified handoff and live GitHub instructions, reconcile active scope/refs/receipts, and distinguish portable artifacts from historical paths.
2. Inspect **only the current host capabilities relevant to the next authorized gate**. Make a small, bounded readiness check; do not spend successive phases profiling a temporary host or searching for the prior host.
3. Reconstruct or stage only needed inputs from versioned GitHub sources and available saved artifacts. Use fresh current-session locations, reproducible commands, pinned versions and verified checksums/modes as appropriate. Record newly measured environment facts as facts about **this run only**.
4. If the necessary capability or artifact is unavailable, record one concrete blocker and a reproducible recovery action. Do **not** attempt to reconnect to, rediscover, preserve or repair a previous conversation's ephemeral host.
5. Execute the actual authorized development/verification gate when its prerequisites are ready. A previous host's successful receipt proves that historical execution only; do not substitute it for an unrun current-host check. Conversely, do not repeat historical environment work without a new task-specific reason.

**Environment setup is a prerequisite, not the product milestone.** A task may expressly require host-dependent validation, but it must identify the finite acceptance condition and stop. Persistent progress is source, evidence, and instructions, not a long-lived execution machine.

## Handoffs to the next thread

Every new browser-session handoff must place this rule prominently in `README-START-HERE.md`, `PROMPT-1-CONTINUE.md`, `PROMPT-2-RECOVER.md`, and `HOST-ENVIRONMENT.md`. Identify the verified portable inputs and reconstruction procedure; label old absolute paths as historical/nonportable. Record current-host facts only with their source session and observation time. Save verified ZIP and separate receipt in the existing `OntoKin` Library folder. Preserve historical ZIPs and their receipts without alteration.

## C271 P22 interpretation

The P22 `INSTALLED_EXACT` installation receipts for two Node files and 24 readback-dependency files are valid **past-host preparation evidence**, not proof of currently existing directories. The next C271 phase must first reconcile its P22 terminal delivery and live PR274/issue273. If still authorized, plan the first unmet H0 operational gate using the frozen source commit `527368bd5195c439762b43e2cc836ff9822213f8` and preserved inventory identities. Reconstruct required Node/dependency or P20 seven-wheel inputs in **this** host only if needed for that gate; never try to recover their old temporary paths. Preserve the H0/H1 boundary, original-seven/full-routine exclusions, existing branch/PR and historical receipts. Do not infer acceptance of H0 or later gates from the P22 receipt.

These instructions clarify the workflow; they do not change OntoKin language semantics, test acceptance criteria or prior evidence.
