# Recorded force release: execution and recovery record

**Status: F01–F12 passed; main integration pending.** Attempt 008 closes the
identified finite force source, Agent/0.5 and recorded GLB/0.5 release. The full
[GOAL](../../../GOAL.md) remains in progress. All earlier failures and the
interrupted attempt 007 remain separately preserved. The acceptance contract is
[OK-ENG-008](../OK-ENG-008-force-release-conformance.md), with recorded delivery
defined by [OK-ENG-007](../OK-ENG-007-native-force-glb-export.md).

## Accepted attempt 008

The [independent audit](audit-008.json) passed **all twelve F01–F12 gates and all
required roles**, with zero failed or pending gates. The
[measured checkpoint](checkpoint-008.json) identifies published source
`c7db6520e172b2b38591969a4bdf75f97a993dbb`, tree
`e10a8869d3f5d2259d3db9a3b7d78b0633d8e5bd`, and all 482 eligible inputs.
Actual execution ran from **2026-10-20T04:02:55.905569Z** to
**2026-10-20T04:31:57.333421Z**. The source stayed unchanged throughout all
twenty stages and the subsequent independent audit.

Implementation remains `ontokin-reference` 0.4.0, with runtime identity
`sha256:0ff20c31e7233a21f164891576181cd4c11e3301e07567915502440be4137ea0`.
The additive mapping is
`sha256:8ecb81ebced19858fdd101f490ab3c6eeec975e23036567c5dfc28d66d76566d`.

| Required evidence | Actual result |
| --- | --- |
| Adopted force source | 56/56 source cases passed with the original expectations and explicit adopted errata. |
| Mapped methods | 242/242 actual methods passed, with no skips or substituted test identities. |
| Full compatibility | 878/878 tests passed separately on CPython 3.11.17, 3.12.14 and 3.13.16; no failures, errors, skips or expected failures. |
| Source Agent workflow | 418 exchanges, 25 source snapshots and 334 predetermined samples; independent source/message audit passed. |
| Agent delivery workflow | 412 exchanges, seven delivered GLBs and eleven retrieved chunks; independent workflow and retained-byte readers passed. |
| Source native delivery | 23 GLBs plus five required failures without artifacts; 857 fixed and 16,596 dense pose observations; no Khronos errors or warnings. |
| Agent native delivery | Seven retrieved GLBs; 424 fixed and 6,139 dense pose observations; no Khronos errors or warnings. |
| Force browsers | Complete nine-case source and seven-case Agent corpora; 27 source and 21 Agent PNGs actually reviewed. |
| Inherited complete workflow | 34/34 local steps passed; all 35 legacy PNGs actually reviewed; current core, Agent, C/M/I and provider roles independently reconciled. |
| Evidence closure | 5,261 inventoried files / 116,199,174 bytes passed independent hash and length verification. |
| Final release audit | F01–F12 passed, all required roles passed, full-product certification remains false. |

The three named reviewers inspected all **83 new captures**, retaining concrete
observations against their exact source, GLB and PNG identities. No blocking
visual defect was observed. Composed side views sometimes hide rear forms through
camera alignment; wide spin/impulse framing limits fine surface detail. Those
limits are recorded per image. Static image review and numerical motion checks
retain their separate roles.

Node 22.20.0 and the unchanged pinned native/browser tools were used with actual
Chromium 141.0.7390.37, WebGL2 / ANGLE SwiftShader. Every Python environment used
the six exact verification-only package pins. No hosted job was dispatched or
retried; GitHub reported no runs for the tested head or observed main revision.
No unexecuted destination or platform is claimed.

The evidence manifest hash is
`sha256:24e3d38198abcb29c55799195a76478fcf9bd235a4fa4cd7775e967f9bd5479f`;
the final audit hash is
`sha256:8f78950e2b9c68a4a6023e2565b862b0da6190d450ed2eb10a6d0cdf9d8c4cc8`.
The accepted archive contains the complete collected root, the final audit,
performed reviews, all 31 review sheets and identified orchestration records.

## Interrupted attempt 007

Attempt 007 started on the same published source at
**2026-10-20T02:35:00.323937Z**. Eleven stages completed successfully through the
Agent browser. The application connection was interrupted before a regression
execution record was produced. The [recovery record](connection-recovery-007.json)
retains the observed process/ref reconciliation. Its original driver still says
`running`; those bytes are preserved, and no completion or release pass is
inferred. Attempt 008 started in a fresh directory and executed all twenty roles.

## Actual attempt 006

Published source `eb4f51108d398d298d2c9d845a16d3a50811cc8a`, tree
`2b5f491dee5e719c522d89fad1443cf34a552659`, completed all twenty actual execution
roles from **2026-10-20T01:29:34.495282Z** to
**2026-10-20T01:59:28.803497Z**. Source remained stable. Its implementation
identity was `ontokin-reference` 0.4.0,
`sha256:c6118fdc5f82b6a8c79e51280c0c3b16567934b459f0c1adb1aede35a1f36272`.

| Executed role | Retained observation |
| --- | --- |
| Adopted force source | All 56 source cases; 372 retained physical samples independently checked. |
| Mapped methods | All 240 actual method IDs passed, with no skips. |
| Complete compatibility | All 876 tests passed separately on CPython 3.11.17, 3.12.14 and 3.13.16. |
| Source Agent workflow | 418 actual exchanges and an independent recovered-message audit. |
| Agent delivery workflow | 412 actual exchanges, seven retrieved GLBs and eleven artifact chunks; independent workflow audit passed. |
| Source native delivery | 23 GLBs, five required failures without artifacts, 857 fixed and 16,596 dense pose observations. |
| Agent native delivery | Seven exact retrieved GLBs, 424 fixed and 6,139 dense pose observations. |
| Force browsers | Nine source cases / 27 PNGs and seven Agent cases / 21 PNGs; all 48 images actually reviewed. |
| Inherited complete local workflow | All 34 selected steps executed successfully, including original source/Agent, C/M/I and all 35 inherited visual captures. |
| Retained file closure | 5,238 identified files / 110,540,038 bytes passed independent hash and length checks. |
| Final release audit | **F01–F10 passed; F11 and F12 failed.** The original failed audit remains unchanged. |

Native and browser tools used Node 22.20.0, Three.js 0.180.0,
gltf-validator 2.0.0-dev.3.10, Playwright 1.56.1 and esbuild 0.25.10. Actual
Chromium was 141.0.7390.37 with Headless Chromium WebGL2 / ANGLE SwiftShader.
The three Python environments used the six exact verification-package pins.
No hosted job was dispatched or retried. GitHub reported no run for the tested
head when reconciled; this is not a claim about repository-wide Actions settings.

## Why execution success did not close the release

The source browser selected and rendered the required nine-case browser corpus,
but its `complete_browser_corpus` flag compared that selection against all
twenty-three available source export cases. The required nine-case selection
therefore incorrectly reported `false`. The auditor rejected that contradiction.
The corrected producer defines the required corpus once and checks its actual
fixture identities. Partial selections and different selections of the same
length remain incomplete; duplicate and unknown names remain invalid.

The complete visual driver retained all 482 current eligible input paths with
exactly matching hashes and lengths. Its `Path` ordering differed from the force
auditor's POSIX-string ordering at a sibling file/directory boundary. The auditor
incorrectly treated the ordering difference as changed input. The correction
compares the same named bytes in canonical string-path order. It preserves both
original inventories and their original hashes. Missing, additional, duplicated,
renamed, changed-length and changed-hash entries still fail. The
[explicit additive mapping decision](mapping-addendum-2026-10-20.json) adds the
two regression methods to F12, preserving every earlier mapped method, fixture,
source expectation and acceptance limit. The next current inventory contains
878 tests and 242 mapped methods, executed by the accepted attempt 008 above.

A [non-certifying comparison diagnostic](force05-audit-006-comparison-diagnostic.json)
previewed these two corrections in memory against the unchanged retained files.
It reached the remaining browser and inherited raw readers without another
exception. This diagnostic is neither a committed checker execution nor release
acceptance. The [actual browser selection preflight](force05-browser-selection-preflight.json)
executes the real selector prefix for nine positive/negative selections; it does
not load a GLB or open a browser. Attempt 008 subsequently supplied fresh
complete execution and newly identified visual review after publication.

## Earlier failures and storage observations

All earlier failed attempt outputs, logs, immutable request/response exchanges,
source snapshots and produced artifacts are retained separately. Mutable SQLite
databases, WAL/SHM files and process-local caches are excluded and disclosed in
each archive inventory.

| Attempt | Observed failure |
| --- | --- |
| 001 | An obsolete mapped test alias and an outdated source-delivery rejection probe prevented the mapped role from completing. The actual historical destination guard was preserved. |
| 002 | The workflow checker omitted the service-added implementation identity from the closed delivered-failure result shape; 237/240 mapped methods passed. Missing and forged identity regressions were added. |
| 003 | Actual Agent delivery encountered `sqlite3.DatabaseError: database disk image is malformed` after the first five roles passed. Seven GLBs had been retrieved before the later failure. |
| 004 | The full Python 3.11 run passed 875/876 tests. A surface capability assertion had not included the explicitly adopted GLB/0.5 target; all its earlier target assertions were preserved. |
| 005 | Actual source Agent workflow encountered a malformed SQLite database despite all agents being paused. |
| 006 | All twenty commands passed; the final audit rejected the browser completeness flag and the ordering comparison described above. |

The [checkpoint data](checkpoint-006.json) retains each attempt's actual
timestamps, command outcomes and log hashes. The storage diagnostics include an
unchanged delivery workflow passing in the original workspace and unchanged
source/delivery workflows passing under `/tmp`. The successful complete attempt
006 used `/tmp` and an exclusive executor window. Both locations reported the
same device and filesystem identifier. These observations do not establish the
cause of intermittent SQLite corruption or prove a filesystem-location remedy.
Runtime behavior, WAL settings and the regression suite's own concurrency tests
were unchanged.

A later [archive integrity observation](archive-integrity-observation.json)
recorded a closed, verified diagnostic ZIP subsequently losing its tail. Its
saved length/hash and the ZIP reader detected the damage before publication.
After concurrent agents were paused, serial reconstruction from the unchanged
retained members reproduced the **exact original archive SHA-256**. The rejected
bytes were not accepted as evidence. The responsible environment component
remains unidentified, so subsequent publication and actual execution are
serialized and checked against their retained hashes.

## Durable bytes and reproduction

| Archive | Member inventory | Meaning |
| --- | --- | --- |
| [Attempts 001–005 parts](force05-failed-attempts-001-005.zip.parts.json) | [4,664 members](force05-failed-attempts-001-005.members.json) | Original failed release runs. |
| [Diagnostics and preflights parts](force05-diagnostics-and-preflights-serial.zip.parts.json) | [4,128 members](force05-diagnostics-and-preflights-serial.members.json) | Separately identified developmental checks and storage probes, serially reconstructed with the original hash. |
| [Attempt 006 parts](force05-attempt-006.zip.parts.json) | [5,240 members](force05-attempt-006.members.json) | Complete collected evidence, original failed audit and actual visual reviews. |
| [Interrupted attempt 007 parts](force05-interrupted-attempt-007.zip.parts.json) | [2,101 members](force05-interrupted-attempt-007.members.json) | Original incomplete execution and connection-recovery observation. |
| [Accepted attempt 008 parts](force05-accepted-attempt-008.zip.parts.json) | [5,267 members](force05-accepted-attempt-008.members.json) | Complete passing evidence root, independent audit, all actual reviews and orchestration. |

Each member inventory names every relative file, SHA-256 and byte length. The
archive builder reopened each ZIP, checked CRCs and verified every member against
its original bytes. The archive hash itself was checked again after copying into
the repository. A large single-blob upload failed before GitHub stored that blob;
no branch was moved. The repository therefore retains at most 8 MiB per part,
with an ordered part manifest preserving the exact whole-archive hash. The offline
[reconstruction script](restore_archives.py) verifies every part, joins the
original bytes and rechecks the complete ZIP hash and CRCs:

```bash
python docs/engineering/force-release-validation/restore_archives.py --output-dir /tmp/ontokin-force-archives
python -m zipfile -e /tmp/ontokin-force-archives/force05-attempt-006.zip /tmp/ontokin-force-attempt006
python -m zipfile -e /tmp/ontokin-force-archives/force05-accepted-attempt-008.zip /tmp/ontokin-force-attempt008
```

Extract attempt 006 into a new directory, then inspect
`attempt-006/evidence.json`, `attempt-006/audit.json`, the execution envelopes and
the separately authored visual reviews. Re-auditing it at its identified source
revision reproduces the recorded failure; later corrected code cannot relabel
those old execution inputs as current acceptance.

For accepted attempt 008, use implementation commit
`c7db6520e172b2b38591969a4bdf75f97a993dbb` and its pinned verification tools, then
audit the extracted immutable root:

```bash
python tools/run_force_conformance.py audit --evidence /tmp/ontokin-force-attempt008/attempt-008/evidence.json --evidence-root /tmp/ontokin-force-attempt008/attempt-008 --output /tmp/ontokin-force-attempt008-reaudit.json
```

The [actual reconstruction observation](archive-parts-verification-008.json)
records successful restoration of all five archives, exact whole-archive hashes
and ZIP CRC verification. The accepted archive SHA-256 is
`6351496602bc77c302c54263e243990bf0d1b8df37c3fca2b356806ecc503c41`.

The captured [execution driver](run_force05_release_acceptance.py),
[collection-plan preparer](prepare_force05_evidence_plan.py),
[archive writer](archive_force05_retained_files.py),
[comparison diagnostic](diagnose_force05_audit_006.py) and
[selector preflight](check_force05_browser_selection.mjs) preserve the actual
orchestration, including original absolute environment paths. Configure the
identified interpreters and tools in a fresh environment when reproducing them.
They do not replace the committed collector or independent conformance auditor.

The next gate is durable publication and verified main integration of accepted
attempt 008. Reusable planar reach actions remain an unadopted next contract.
Contacts, continuous torque, general mechanisms, purposeful
locomotion/manipulation, deformable matter, live destinations, other full-product
domains and the measured direct-tool authoring comparison remain open.
