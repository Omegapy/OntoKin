# Reach recording continuation, October 23, 2026

Checkpoint **011** continues checkpoints [010](checkpoint-010.json) and
[009](../reach-recording-validation-2026-10-22/README.md). The latest complete
source GLB/0.6 run remains **22/28** under the unchanged **100,000-operation**
request limit. **P05, P09, P11, P16, P23 and L03** still fail at that cap.
No additional complete recording pass is claimed by this checkpoint.

[PR #27](https://github.com/Omegapy/OntoKin/pull/27) remains draft and must not be
merged before every mandatory acceptance gate passes. Main remains
`2bb4588e121fcfe99b4d42c734b15b38362f3642`. The complete product goal remains open.

## Tested source and publication

Published source
[`7a50c86057b8517169c4f4b39189ee027e5c108c`](https://github.com/Omegapy/OntoKin/commit/7a50c86057b8517169c4f4b39189ee027e5c108c)
has exactly the Git tree of tested local commit
`7ebe5c2988eaa0c24adfdd18cb286d4c28da60fb`:
`390223ba9c4feea0256c5815ccb0ff8b2c269973`.
The continuation branch is `work/reach06-recordings-20261023-7of9-e619`;
the original baseline is `6cf8c525429076ce37efd4ecea95fd01f83365ea`.

The complete latest run is `combined-recordings-006`. Every materialized input
matches its committed Git identity before and after execution. P20 uses
**95,435**, L01 **92,793**, and L02 **85,593** operations. Intermediate runs,
including small pass-case cost regressions from the reference plan, remain
visible in the raw evidence rather than being replaced by only the best counts.

| Focused scope | Actual result | Evidence directory |
| --- | --- | --- |
| Captured dynamic roots | 92/92 passed | `captured-dynamic-b04a27c-focused` |
| Literal JSON text blocks | 37/37 passed | `json-literal-focused-001` |
| Immutable surface construction leaves | 66/66 passed | `construction-surface-focused-001` |
| Integrated independent source plans | 137/137 passed | `reference-plan-integrated-focused-002` |
| Integrated endpoint operands | 85/85 passed | `endpoint-integrated-focused-001` |
| Numerical identity, source rates and native-reference bridge | 60/60 passed | `numeric-basis-focused-001` |

Every listed cohort has zero failures, errors and skips and stable materialized
inputs. Each report names its actual source commit and tree. These separate
cohorts are not summed or represented as one latest-source regression run.
Checkpoint010's 227-method cohort, checkpoint009's 234 methods and the earlier
686-method evidence retain their original source identities and meaning.

## Evidence and recovery

The [machine-readable checkpoint](checkpoint-011.json) lists all 28 current
recording results, identified test cohorts, rejected candidates and execution
limits. The [archive manifest](checkpoint-011-manifest.json) binds **484 new raw
members** in **14 parts**, each smaller than 1 MB for repository API recovery.
The joined ZIP is 12,340,050 bytes, SHA-256
`b0cdfa8ab5ac4625a94d0e061b3ac390a29625bbb9a8bd18858240954330ddc4`.
All member SHA-256 values, ZIP CRCs and the concatenated part identity passed.
Concatenate parts in manifest order, verify the joined identity, then extract.

Checkpoint011 is incremental. Its manifest names 236 unchanged member paths
available in the original [checkpoint010 manifest](checkpoint-010-manifest.json);
the original archive still contains all 238 members. New or changed raw members
include complete runs, before/after inventories, source GLBs and reports,
test logs and exact method IDs, failed traces, diagnostic drivers, local commit
objects, exact patches and local-to-published tree mappings. No failed attempt
was relabeled as accepted evidence.

The [documentation check](checkpoint-011-docs.txt) is preserved separately.
It reports the historical binary-archive links unavailable in this sparse
recovery; its overall status is not represented as passed.

## Integrated changes

- Actual selected dynamic roots now use captured anchor, force, gravity and
  spin operands with the original ballistic equation and exact clock order.
  P16 captures all 202 interior keys in its three phases and computes its
  whole-phase excess allowances once. The full recording still fails.
- The independent reader retains bounded source-formula plans, fresh source
  receipts and the existing numerical cache. Prescribed translation and
  Cartesian spin formulas use copied inputs; the Y-axis head preserves its
  ordinary local compositions. Stationary values remain in the original
  256-entry cache. Eviction, source/model/arithmetic-owner changes, narrowing,
  callback exceptions and reentrancy remain covered by focused checks.
- One endpoint comparison reuses completed stored-coordinate conversions and
  admitted immutable source cells after fresh current-domain guards. A small
  native claim eliminates a redundant sufficient inequality. The exact L1
  bounds, normalization fallback and position-callback order are unchanged.
- Bounded literal ASCII JSON blocks use exact encoded lengths; other strings
  keep the existing Unicode/escape path. Logical occurrences, byte/depth/cycle
  limits and cancellation remain checked. No extra text cache is added.
- Sealed surface construction leaves reuse immutable values, with ordered
  occurrence guards, fresh wrappers and unchanged logical-value accounting.
  P23 construction is cheaper, but its complete export remains over budget.
- The source numerical implementation identity now includes
  `reach_recording_capture.py` in the writer, independent verifier and rate
  audit. The independent plan is included in the rate/native-reference input
  lists. This fixes omitted implementation provenance; equations and public
  limits are unchanged. The latest counts include the additional hash work.

The related derivations are [source plans](../reach-reference-phase-plans.md),
[endpoint operands](../reach-endpoint-operand-reuse.md), and the existing
[endpoint proof](../reach-independent-endpoint-bounds.md).

## Rejected and interrupted attempts

The source-template candidate at `20eb63f` passed 13/14 new methods but added
**1,272** operations to the checked P23 prefix (52,783 versus 51,511).
Its correctness, mutation, owner, callback and cache tests are preserved, but
the candidate is not integrated. Broader phase-node reuse preserved exact
checked maps, states and boundaries yet saved only 24 P11 operations, added
26 on P16, and did not improve P23; broader selection was worse. It is also
not integrated.

An early reference-plan observer signature incompatibility, its repaired
performance assertion, the first integrated invocation's misspelled test
module, and all other failed development attempts remain visible. The clean
accepted runs are named explicitly above. A first profiling observer hit the
unchanged elapsed-time limit and was interrupted; its executed driver and
interruption record are retained. The replacement lighter observer completed
all six cap-failure diagnostics with stable inputs. Neither diagnostic raises
the operation or elapsed-time allowance.

## Execution limits and next gate

All runtime, test, tool, fixture and specification files are materialized and
Git-verified. **37 historical binary evidence archives/parts remain
unmaterialized**, with exact original Git blob identities retained in the tree
and every execution inventory. Missing runtime or fixture inputs cause the
development driver to fail. The stock release collectors are unchanged.

The development schema is `ontokin.reach-sparse-development-execution/0.1`;
`release_acceptance` and `release_input_closure` remain false. These runs do
not establish complete regression, CPython compatibility, historical archive
closure or the finite release gate.

Continue mixed native/ordinary sampling for P11 and bounded phase-wide
independent source receipts for P05/P09/L03, alongside measured investigation
of P16/P23's remaining source work. Those follow-up candidates are not verified
or integrated by checkpoint011. Run focused correctness first and the complete
28-recording suite after integration, with unchanged fixtures and limits.

After **28/28**, execute Agent delivery, complete regression, CPython
3.11/3.12/3.13, independent rate/native/browser/visual checks, inherited/hostile
roles and every R01–R12/Q01–Q22 requirement under the
[adopted contract](../../language-design/planar-reach-v0.1/ADOPTION.md).
No main integration lease, hosted job dispatch, paid execution or Actions
setting change occurs at this checkpoint.
