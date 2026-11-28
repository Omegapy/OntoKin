# C272: C253 edit, animation and clean-rebuild qualification

C272 qualifies OntoKin's existing route for changing an animated assembly through Agent/0.2 on
the frozen [C253](../localized-repair-c253/README.md) cases:
- V1 changes the first rack's middle finger from 0.65 m to 0.75 m;
- V2 changes it back from 0.75 m to 0.65 m;
- N1 must refuse 0.75 kg given as a length.

A scripted client, not a model, makes the edits. The unchanged
[C255 checker](../localized-repair-c255/CONTRACT.md) and the checks below judge the actual
source and GLB bytes.

Requirements: [task C272](../../workflow/tasks/C272/REQUIREMENTS.md). Records:
[coverage](COVERAGE.md), [reconciliation](RECONCILIATION.md), [gaps and the owner's choice](GAPS.md),
[controls](CONTROLS.md), [report](REPORT.md).

## Run it

Prerequisites:
- the checkout's `.venv` with the `python-verification` profile ready (`.venv/bin/python tools/doctor_local.py`);
- `python3.12` on `PATH`, which the package-smoke setup tool uses for the rebuild environments;
- network access to the package index once per run, because the clean build environment installs `setuptools>=77` as LOCAL-SETUP describes;
- a clean commit: the command refuses to run while the product, the frozen inputs or this directory hold uncommitted changes, because the rebuild uses the committed revision.

On macOS, use the resolved temporary directory, as LOCAL-SETUP shows:

```sh
export TMPDIR="$(cd "${TMPDIR:-/tmp}" && pwd -P)"
.venv/bin/python docs/engineering/localized-repair-c272/qualify.py --output-dir ../OntoKin-local/c272/runs/NEW_NAME
```

The output directory must be new or empty and outside every checkout. A run takes about
three to four minutes on the owner's Mac. It exits with 0 only when all three cases and every
control pass. No model is called, and no step is done by hand.

## What a run writes

| Path in the output directory | Content |
| --- | --- |
| `RESULTS.json` | Revision, executor, and for each case and check `passed`, `failed` or `not_run`, the C255 faults, the failed property rows, the pose errors, the locality, the identities and the controls |
| `delivery/cases/CASE/record/` | The harness's external record of each case: `exchanges.jsonl` (each request and response as it happened), `authority.json` (the accepted-state record in C255's hex transport), `accepted-state.json`, `outcome.json`, and the start, candidate and retained files |
| `delivery/cases/CASE/client/` | The scripted client's requests |
| `delivery/cases/CASE/store/` | The service's own store |

The harness builds the semantic sidecar itself with the product's `build_semantic_manifest`,
from the program read back through the service and the GLB bytes retrieved; no Agent/0.2
operation delivers it. The package-smoke setup tool also writes its own report into the
checkout's ignored `build/local-environment/`.
| `cases/CASE/score.json` | The per-property table, the 126 pose rows, the workflow checks and the C255 result |
| `cases/CASE/rebuild.json`, `rebuild/` | The two clean rebuilds per case: workspace listings, invocation, import locations, wheel identity and logs |
| `cases/CASE/semantic-final.json` | The delivered semantic record with its field pointers, source literals and cross-checks |
| `controls/` | The real service runs of the two end-to-end fault controls |

## Components

| File | Role | Imports the product? |
| --- | --- | --- |
| `runner.py` | The external harness and scripted client: fresh store per case, frozen-input check, exchange record, accepted-state record, retry and stale cases | yes, to drive it |
| `rebuild.py`, `rebuild_entry.py` | Package-smoke rebuild in empty workspaces; the entry runs only inside the installed wheel's environment | entry only, from the wheel |
| `observe.py` | The unchanged C256, C257, C258 and C267 interfaces, loaded from their pinned bytes | no |
| `semantic_observe.py` | The delivered semantic record, with cross-checks against decoded motion (option A) | no |
| `score.py` | The C255 observation, its verdict and the per-property table | no |
| `controls.py`, `glb_edit.py` | Evaluator and residual controls and the GLB mutations they use | no |
| `qualify.py` | The one command | through `runner` and `rebuild` |
| `run_observer_regression.py` | The twelve recorded observer groups, optionally with this directory's tests | no |

## Limits

The result covers seven sampled times on one public, previously used family. It covers
construction-0.1 source, Agent/0.2 and GLB/0.2 on the executor named in `RESULTS.json`. The
animation is source-defined and delivered as recorded playback. The GLB carries no sites,
actions or events; only the sidecar does. The semantic values are delivered producer claims,
checked against C255's independent expectations and cross-checked against decoded motion;
they are not a re-interpretation of the source expressions.

A pass establishes none of the following:
- continuous motion or dynamics;
- live physics, collision or action execution in a destination;
- support in Blender, Unreal, Godot or OpenUSD;
- an authoring advantage;
- full A1, C260 qualification or product acceptance.
