# Next bounded task: qualify the offline corpus and oracle component

Reconcile the actual published C253 revision, reviews, current integration
owner, branches and saved handoff before editing. Read AGENTS, GOAL, STATUS,
this directory's [decision](DECISION.md), [protocol](PROTOCOL.md),
[scoring specification](SCORING.md), [corpus](corpus.json) and
[run plan](RUN-PLAN.json).

## One objective

Implement one standard-library-only offline component that loads the frozen
corpus, independently derives its expected semantic/geometry/pose records,
and evaluates inert observation records against those expectations. It must
cover V1, V2 and N1's accepted-state preservation rules without importing
OntoKin runtime modules or invoking native applications.

Use the bound raw source as evidence and the reviewed closed-form equations
as oracle authority. Preserve all original source bytes, tolerances and
historical expectations. Add positive, boundary and adversarial controls for
the faults listed in SCORING. State exactly which rules still require a later
native artifact reader, revision coordinator or execution runner.

## Completion and stopping condition

The independent reviewer verifies formulas, all 18 identities, 126 poses,
allowed/forbidden changes, dependency/source binding, retained-state checks
and complete rejection of the named inert faults. Relevant component tests,
manifest checks and repository documentation checks pass on exact source.
Publish the reviewed component if the coordination and integration gates are
satisfied; create, verify and confirm the next saved handoff, then stop.

Do not implement the general runner, call a model, launch Blender/Godot/USD,
qualify native packages, create new evaluation assets, add adapters or resume
C251 sampling. A static observation checker cannot establish real artifact
extraction, model performance or comparative advantage. Missing evidence is
reported as a later prerequisite, never filled with a passing synthetic result.
