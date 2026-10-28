# C061 final static diagnostic-tooling review

Date: 2026-10-28. Independent reviewer: `/root/c060_review`.

## Decision and execution boundary

**No blocking issue was found in the reviewed collector and auditor for the proposed four-request attribution round.** This is a static tooling decision, not a passing diagnostic result, optimization approval or recording acceptance.

The root must freeze and publish the actual tool/source bytes, record the exact resulting commit/tree, finish all input recovery intended for the run, and declare its exclusive execution window before starting the first request. All four original requests must use that same stable checkout. A failed observation, failed neutrality audit or changed input stops the attribution round; this review does not authorize an unbounded retry or tuning loop.

This reviewer performed only source reads, standard-library hashing and Python abstract-syntax parsing. No collector, auditor or product module was imported or executed. No product request, test, numerical replay or archive construction occurred in this review. I am paused after writing this record and will perform no further edits or execution during the root's exclusive request window unless explicitly reassigned after that window.

## Exact reviewed files

Paths are relative to `/workspace/scratch/16cb56e5d545/ontokin-c061`.

| File | Bytes | SHA-256 | Git blob SHA |
| --- | ---: | --- | --- |
| `tools/capture_reach_reader_setup.py` | 50,678 | `b90854f1a73053a3f9f9ebd7b67662d27b788f478a39a36cbc95abad2429183e` | `5bab7a11c705b414aac35f3c3070d0ae156021ee` |
| `tools/audit_reach_reader_setup.py` | 41,586 | `ef322586e7693647f07f6901737611c82c844e2a6ed98578f499ac49bf994602` | `5520c85e6d4319ec1121da54eff2ae38db010041` |
| Unchanged dependency `tools/audit_reach_recording_work.py` | 71,385 | `5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf` | `3e0aaa33d1cc4a9d6d4c437464862b066cdae399` |

All three files passed syntax parsing in this review. Syntax parsing did not execute imports or establish runtime correctness. Product-source identities and the structural feasibility assessment are recorded separately in `structural-review.md`.

## Collector assessment

The new collector is a separate file. It retains the C060 original-request/key/stage observations and calls the unchanged probe API with the original float `fps=1.0`. It adds eighteen high-level setup boundaries without replacing low-level arithmetic, work charging, cache methods, construction callbacks or trace/profile hooks.

The setup wrappers are installed only after the original reader-entry checks have retained the actual work, construction budget, byte argument, options and callback identities. They are removed at the first key entry, before the saved original key function executes, and again in reader and final cleanup. This keeps the added wrappers out of later key evaluation. The complete `_verify_certificates` call is deliberately unwrapped; its pre-key work remains an explicit residual instead of being misreported as setup.

The reviewed wrapper targets are:

- `gltf.read_glb` and `_validate_geometry`;
- `scene.program_metadata`;
- `reach_reference.build_reference`;
- reader numeric-basis, metadata, clock, geometry, phase-table, boundary-allowance, projection and track functions;
- `ReachReference.boundary_states`, `point_phase`, `_phase` and `_axial_derivatives`;
- `_l1` and `_axis_transport` only while an axial span is active.

These are outside the native-pinned arithmetic/dispatch sets inspected in the reference plan, centered evaluator and certificate reader. Each wrapper invokes its saved original once with the original positional and keyword values. The wrapper records argument and callback identities and restores every installation in `finally`. It does not call source or arithmetic helpers to obtain observations.

The event tree retains parent IDs, depths and monotonically assigned entry/exit event ordinals. Recursive `_assert_projection` invocations forward directly to the saved function and remain in the outer projection span. `_phase` calls during reference construction retain their actual parent segment. This supports nonoverlapping offline accounting rather than adding recursive inclusive totals.

Reference-cache observation is deferred until an initialized reference is available. The `build_reference` wrapper retains the returned reference before its exit snapshot. Nested phase/axial descriptors detach exact carrier and interval fields, process-local source/state identities and arithmetic-domain fields. Returned phase paths are read from actual native `ReferencePhase` fields. Attachment descriptors preserve tuple/list, integer/float/Fraction and interval distinctions. Float values use exact hexadecimal representation; rational leaves retain their numerator and denominator.

Observation structure is explicitly bounded: at most 4,096 recorded setup spans, stack depth below 64, typed descriptor depth at most eight, at most 512 visited cells per typed descriptor, bounded sequences and strings, and 32,768-bit integer leaves. Cache scans enforce the existing 256-entry limits; category maps are bounded. These are diagnostic structure limits, not a measured memory or timing claim. Serialization size checks occur after the request. Actual memory use and elapsed neutrality remain unmeasured until execution, and the original 30,000 ms product cap remains authoritative.

Observation errors are recorded and invalidate capture rather than being substituted for an original product exception. Saved originals use bare rethrow on product failure, while guarded observation cleanup preserves the failure. The combined result requires the inherited capture checks as well as the new setup artifact; `captured_setup` alone does not certify a failed-request pair.

## Auditor assessment

The new auditor loads the unchanged C060 standard-library auditor only after verifying its exact SHA-256. It changes only the declared collector pathname and retains the original named traceback-wrapper policy. It executes the inherited source/commit/tree, complete work-map, original settings, retained-byte, traceback/exception graph, command-receipt, failure-local and stable-input checks before accepting the new setup attribution.

The final setup checker verifies:

- the same case, source revision/tree and actually executed collector descriptor;
- the exact eighteen wrapper targets, their module/qualified name, source path and source first line derived from the bound source syntax;
- the ordered first-key, reader-exit and final-cleanup restoration receipts, with wrappers present at the first restoration and originals present afterward;
- exact entry/cutoff agreement with the inherited reader and first-key records;
- full setup category totals against the original independent work ledger;
- contiguous event ordinals, preordered span IDs, balanced nesting, parent/depth agreement, no crossing siblings and no open spans at the setup boundary;
- monotone counter changes and nonnegative exclusive costs after subtracting direct children;
- axial-only attachment observations and enclosing phase context;
- native typed operand/result structure and process-local reference/model/arithmetic identity consistency;
- source-cache occupancy and categories at the first-key boundary, cross-checked against the inherited key ledger;
- unchanged analysis inputs and absence of imported OntoKin modules in the offline auditor.

During review, the author added the first-key cache-category comparison. It consolidates the inherited `reference_pose:<kind>` categories into `reference_pose` before comparing them with the new coarse cache snapshot. Final audit hardening also requires the new auditor, unchanged core auditor, collector and original probe to be materialized in the verified source snapshot, and independently rechecks their descriptors. The maximum-span check accepts the legitimate exact 4,096-span boundary. The exact reviewed hash above includes those changes. The collector's final change clarifies that collector-specific output occurs after execution; the probe itself writes its input inventory before the request. This correction changes no executable statement or source line count.

The auditor retains the original failed product status. It rejects unsupported acceptance/savings claims and never evaluates source, resumes failed work or accepts a GLB. Its repeated-argument inventory explicitly leaves cache authority and net savings unestablished.

## Required interpretation of the resulting ledger

**Full named categories are observed at coarse setup boundaries. Nested structural functions have shared/Reach/checkpoint scalar observations.** The auditor reconciles disjoint coarse stages plus every unwrapped gap to the complete setup category map. It independently reconciles all nested exclusive scalar work plus residual to the setup scalar total.

The current output sets `nested_full_category_attribution_available=false` and `exclusive_category_delta=null` for nested function maps. This is an honest limitation. A later report must not describe those nested records as a measured complete named-category profile. It may use their measured shared/Reach/checkpoint costs, while showing all named categories at the coarse stage level. No named category is inferred merely because a function is expected to call the generic tick.

The generic `checkpoint` pool remains distinct from a function name. The repeated typed values and state IDs identify observations; they do not establish valid cache keys, unchanged live source authority, positive net saving or completion cost. Any runtime candidate needs a separate derivation and full admission/insertion/eviction/fallback accounting.

## Import and source stability

The collector imports its product modules before calling the probe's `build()` function and therefore before that function's input snapshot. The new explicit `scene` import refers to a module already used by the original export path. No new runtime family is added by the setup wrappers. Modules are imported before wrapper installation, avoiding native-dispatch snapshots initialized from setup wrappers.

The control imports through the unchanged original probe. Static import inspection is not proof of identical runtime import sets: the inherited auditor still compares the actual loaded OntoKin module inventory from control and capture and verifies each module against the materialized manifest. Any difference fails the pair. The diagnostic helper import name is not treated as a new product capability.

Both product arms must record identical before/after input inventories. Any recovery, editing, archive construction, test output inside the checkout or head change during that window invalidates the premise. Final tool publication and root source/input checks therefore precede product execution.

The root's stated execution plan uses a separate named partial checkout: the original C060 488 input paths, plus the unchanged C060 auditor and the two new tools, for an intended 491 materialized files including all 65 runtime files. Its larger documentation-recovery checkout remains separate. This is a plan disclosed before execution, not a verified resulting inventory in this review. The actual receipts must establish the final count, byte identities, all omitted paths and complete Git tree identity. The partial diagnostic does not become a stock whole-checkout test because all runtime files are present.

## What remains unverified

No fresh request has run under this reviewed tooling. Actual span counts, descriptor compatibility with both original fixtures, neutrality, full stage totals, observation overhead, negative-audit rejection and diagnostic outcomes remain to be demonstrated. All earlier C060 results remain attributed to their original implementation and cannot be reused as evidence that this new collector ran successfully.

This review clears only the finite attribution attempt. It does not select an axial reuse implementation, accept C061 as complete, close the C060 documentation gate, change LFS migration status, permit main integration or claim any original recording passes. The root retains responsibility for execution serialization, exact evidence, a finite decision and further scope control.
