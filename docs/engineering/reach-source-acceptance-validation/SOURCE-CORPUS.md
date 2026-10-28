# Reach source corpus development checks

This contribution supplies actual source checks for all **45 adopted cases**:
the original P01–P26 and N01–N15, plus lifecycle L01–L04. Its
[literal mapping](source-case-map.json) identifies every executable method,
fixture, source revision, complete action set and asserted field. The original
308 sample sides and supplementary 51 sample sides remain unchanged.

The scope is preparation and execution of a development cohort. A passing
cohort does not close the `source_execution` role, an entire R/Q requirement,
the reach release or the full product goal. The
[adopted release contract](../../language-design/planar-reach-v0.1/release-contract.md)
retains those obligations.

## Source requests and expected values

Each sample side is a **separate fresh source request**. The test loads the
unchanged complete file manifest, verifies entry/module/program identities,
compiles the actual source and replays the real simulator to the indicated
exact side. Compilation and replay share the compiler's one `reach_work`
context. No counter is reset or enlarged during a request, no output set is
reduced, and no source is rewritten to reach a supported subset. Release and
rollback checks retain one shared context across their incoming and outgoing
sides. Separate prefix requests compile afresh and retain their own complete
context.

Expected values come from the frozen acceptance JSON and its explicit retained
transform equations. The production solver, sampler and exporter are never
used to choose expected values. The checker
uses a disclosed independent quaternion inverse to re-express the observed
elbow world position in the observed base frame; that operation consumes only
observed data and compares its result with the existing frozen base position.
Available source/request operation counters after completed construction and
replay are preserved in the run observations. Early construction failures
retain their actual diagnostics; a returned compiler counter is unavailable
when construction never completes.

Two additional expected transforms use only frozen inputs and the unchanged
independent Decimal oracle's elementary sine/cosine functions. For each
original case, the world target is the frozen world elbow plus the authored
root rotation applied to `(target - frozen base-frame elbow)`. The retained
author equation fixes the canonical base angle, root elapsed `min(t, 3)` and
optional world-Z spin of `1/4 rad/s`. The frozen elbow anchors already include
the authored mount and root translation; no production pose or new mount
layout supplies an expected value. P16's explicit free-orientation rule is
evaluated at three and four seconds by left-multiplying the frozen release
quaternion by the world-Z rotation from its frozen angular velocity and exact
elapsed time, followed by the inherited normalization/sign rule. Both original
oracle and author-script hashes are checked. These additions keep the existing
position and orientation bounds unchanged.

## Assertions and explicit limits

Target and joint-coordinate values, physical/per-action joint rates and other
canonical scalar fields require exact binary64 bits, including the canonical
zero and half-turn cases. Exact clock and identity fields are compared without
a tolerance. Positions and measured residual differences use the frozen
`1e-9 m` source tolerance. Satisfied terminal residuals must independently stay
at or below that bound. Orientations use the adopted `2e-15 rad` reference
angle tolerance, computed with quaternion chord lengths to avoid cancellation
in `acos` close to zero.

Every actual sample checks the complete object, visible-object and action
sets. L01–L04 compare the complete retained reach projections, direct physical
joint coordinates/rates, actual action status and actual joint action owners.
Expected owners come from the frozen claimed-joint identities, including
paused ownership and later replacement owners; terminal records stay latched.
Negative cases must fail
at the intended construction or admission phase with the adopted envelope,
category and reach subcode. Admission failures preserve the incoming state,
event position and claims. P17 and L04 also exercise successful short requests,
exact later failed prefixes and whole-boundary rollback. P11 checks the other
arm and head goal. P16 checks both incoming joint rates, exact saved-state
transfer, own mass, world force, force completion and the frozen freed-payload
positions and independently evaluated orientations at three and four seconds.
P17 and L04 diagnostic times must equal their explicit frozen failure times;
L04's failing element identity must match its explicitly named frozen action.
The retained valid-prefix side is not treated as an instruction to choose a
particular diagnostic side or primary byte-span granularity. Observed P17/L04
diagnostic locations and sides remain available for separate review; no absent
per-case span or side expectation is invented.

The adopted input records do not state a separate acceptance tolerance for
derived world linear/angular velocity. This cohort records finite values,
exact-bit equality and component errors against every corresponding frozen
value. Those comparisons remain **pending an explicit adopted bound**; the
supplement's `2e-12` preparation-only libm cross-check is not substituted as
a source release tolerance. Exact joint-rate assertions remain mandatory.

Visible-set and nonempty geometry assertions do not constitute an independent
full vertex/region/PBR check. P20 evaluates the frozen repaired program; its
actual Agent edit and sibling-preservation workflow remains LP02's separate
obligation. This cohort performs no GLB delivery, native/browser rendering,
continuous-motion certification, full compatibility run or final release audit.

## Execution

Observe the repository's exclusive executor window before actual execution:

```bash
python3 tools/run_reach_source_corpus.py --output /tmp/reach-source-corpus-001
```

Use a new output directory outside the checkout. The driver records the exact
Git commit/tree/status, all tracked and untracked nonignored file hashes,
interpreter/platform, literal method inventory, actual unittest log/results,
source requests, numerical measurements and before/after input equality. It
fails on missing files, tracked/index mismatches, a changed frozen input,
inventory mismatch, any test failure/error/skip, expected-failure exemption or
input instability. Deliberate changes must be staged before execution. A
dirty working tree is explicitly identified as not fully contained in the
reported local HEAD commit through `head_revision_contains_all_tested_inputs`.
The driver does not verify remote publication and always records
`remote_publication_verified: false`; a separate remote observation must bind
the published commit/tree and exact tested input bytes. Failed attempts must
be retained separately.

The new mapping must be published before a final acceptance execution. An
early development run can reveal defects, but cannot retroactively establish
that publication or any missing release role. Actual results belong in a
separately identified execution record; this preparation note contains none.
