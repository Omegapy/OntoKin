# Reach source acceptance development checks

This record distinguishes actual branch execution from the still-open
[complete reach release](../../language-design/planar-reach-v0.1/release-contract.md).
The adopted authority is [OK-LANG-006/0.1.0](../../language-design/planar-reach-v0.1/ADOPTION.md).
None of the results below establishes full-product completion.

## Why this checkpoint exists

The combined reach implementation and the [PR #22 test repair](https://github.com/Omegapy/OntoKin/pull/22)
needed fresh execution against the current compiler, evaluator and Agent service.
The recovered current source enabled that execution. It exposed three outdated
legacy test expectations, seven failing Agent-delivery methods and a reproducible
source-export operation-budget failure. The observations are retained separately
from the corrections and subsequent attempts.

The test correction in [PR #23](https://github.com/Omegapy/OntoKin/pull/23)
replaces Agent/0.6 as an unknown-protocol example with an explicitly unsupported
`ontokin.agent/9999` value, extends rejection of mismatched 0.5/0.6 request
envelopes, and includes the registered GLB/0.6 capabilities key. The existing
defaults and unknown-protocol rejection remain checked. Registration is a
capability inventory fact; it does not establish successful delivery.

## Executed checkpoints

All runs below used CPython 3.12.14 on Linux x86_64. The raw records retain the
exact interpreter, platform, commands, literal method inventory, result entries,
logs and before/after source hashes.

| Record | Actual source commit | Observed result |
| --- | --- | --- |
| `repaired-001` | `f45f66e428cffe965dc6e50d0746c862b916263e` | All 14 reference/protocol integration methods passed, including all 42 LP steps. Zero failures, errors or skips. |
| `full-001` | `f45f66e428cffe965dc6e50d0746c862b916263e` | All 1,021 discovered methods executed: 1,011 passed, 10 failed, zero errors or skips. Three legacy expectations failed; seven Agent-delivery methods failed. |
| `export-001` | `f45f66e428cffe965dc6e50d0746c862b916263e` | Both actual P01 exports, for a 0.25-second prefix and a full 3 seconds at 2 fps without helpers, failed with `OKL-E-RESOURCE`. Neither produced an artifact. |
| `legacy-002` | `80f487dd40302040e89b2980560ecdf21c4f0252` | All 32 methods in the three corrected legacy modules passed. Zero failures, errors or skips. |
| `local-driver-001` | `80f487dd40302040e89b2980560ecdf21c4f0252` | `tools/check_local.py --force-agent` failed before executing any check stage because the isolated Git fetch could not read a missing historical archive blob. |

The earlier failed integration attempt and every failed record above retain
their original outcomes. Results from different source commits must not be
combined into a fictional successful full-suite run.

### Shared-budget export reproduction

The source probes use the unchanged `compile_construction` work context for
`export_glb`, including independent destination validation. The configured
maximum remains 100,000 operations. Both attempts reached 100,001 total
operations and failed. The quarter-second export reached independent boundary
validation; the 3-second export failed during sampling. The final reach-only
counter of 95,851 excludes earlier compiler work charged to the same total
budget. It is not evidence of a larger allowance or a contradictory limit.

The probes instrumented stage observations while calling the original stage
function; they did not change arithmetic, limits, fixtures or output behavior.
Successful source and Agent delivery remain required.

## Exact source recovery

GitHub artifact `12183769150` supplied the historical source bundle. Its downloaded
ZIP SHA-256 is `3c783a352888b429d538d9665105cb8081f964af04e668bbe43a43e67fe93067`.
Current text and small binary files were recovered by exact Git blob identity.
The first executions had all 1,134 executable/documentation files available but
lacked 15 historical binary archive parts. Their reports correctly retain
`complete_checkout: false`.

Fresh GitHub Contents directory metadata later supplied authorized temporary
download links for the 15 remaining blobs. Their total 107,079,993 bytes were
verified against their exact Git hashes and sizes before import. The resulting
checkout has all 1,149 tracked files, a clean worktree, actual GitHub commit
`80f487dd40302040e89b2980560ecdf21c4f0252` and tree
`f59a37783e35c43517e8acc351385b253004c05e`.

This resolves the local recovery defect. It does not relabel the original
preflight failure or constitute a release audit of the recovered historical
archives. Temporary download credentials are not part of the retained evidence.

## Source corpus work and remaining gate

The [source-corpus companion](SOURCE-CORPUS.md) and its
[literal case mapping](source-case-map.json) check the frozen 41 original cases and four
lifecycle cases directly against actual construction/evaluation requests. Its
literal mapping, request granularity, asserted fields and any comparisons
without an adopted numerical threshold are recorded separately from execution
outcomes. The production runtime and frozen expectations remain unchanged.

The next finite acceptance gate still requires the complete R01–R12/Q01–Q22
obligations, actual source/Agent/native/browser execution, declared Python
compatibility, mandatory inherited roles and stable eligible inputs. Existing
recording-budget and independent-reference work has separate branch ownership.
No hosted job was dispatched or retried for this checkpoint.

The [documentation review](documentation-review.json) records the narrative
inventory, scope and status/authority findings. Historical draft and implementation
labels remain intact; current STATUS, adoption and identified release evidence
govern current support claims. The review distinguishes the accepted source and
valid incoming state from a failed run descriptor that may advance to that prefix.

Detailed execution archives and the final machine-readable checkpoint will be
added after the next exclusive executor window. Until then this is a development
checkpoint, with source-corpus and official-driver reruns pending.
