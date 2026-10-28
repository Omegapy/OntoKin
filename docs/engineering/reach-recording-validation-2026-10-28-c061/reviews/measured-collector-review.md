# C061 measured collector review

Reviewer: `/root/c061_collector`. This review followed root's explicit release of the execution window in Issue #26 comment 6483342626. It reads existing evidence and source only. The reviewer ran no OntoKin import, product request, test suite, audit entry point, archive operation, compression, or SQLite workload. Small standard-library JSON inspections, integer sums, and file hashes were used to crosscheck the already recorded results.

## Exact scope

Both observed pairs identify executed commit `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`, tree `037157a58442ba1956597d32e1e540802f9ed896`. Product failures and source/input closure are recorded by the strict audits; this review independently checks the setup observations and their interpretation. The retained GLBs remain unvalidated reader inputs.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| P11 `capture/reader-setup.json` | 998296 | `49fa81a134a14e962d21737197faa1ad32b0d148a15422757275958279f4f55a` |
| P11 `audit-001/reader-setup-analysis.json` | 93365 | `a4989f71014bd6f12e897f86e97696d7c0680efda7919362b7c65ab5e976179c` |
| L03 `capture/reader-setup.json` | 622142 | `c86c6bd6c32f0294907a32b01a8f468824cf425e6b0eb36d59ecc1f020a8ffb5` |
| L03 `audit-001/reader-setup-analysis.json` | 87752 | `67a0408aff087cb6a00b486872946edf4c8a729b7a7e0d15c6f741f15b031254` |
| Collector source | 50678 | `b90854f1a73053a3f9f9ebd7b67662d27b788f478a39a36cbc95abad2429183e` |
| Setup auditor source | 41586 | `ef322586e7693647f07f6901737611c82c844e2a6ed98578f499ac49bf994602` |
| `ontokin/reach_reference.py` | 259473 | `e17fb50c54f41e13b42ce5bc2c6464544c26992299b474032ad2b19e0485949f` |
| `ontokin/reach_conformance.py` | 206759 | `b4c657eac72186203960b18738f65f08e700f52dffa11c1364c6b4609c59a81a` |

## Attribution crosschecks

P11 has 93 spans and 188 endpoint events; L03 has 83 spans and 168 events. Independently replaying the recorded endpoint ordering confirms contiguous event ordinals, balanced entry/exit stacks, actual parent/depth relationships, and no open span at the first key. The setup entry shared count agrees with `capture.json`; its cutoff agrees with the first key entry in `key-ledger.json`. All 18 setup targets have restoration records at first-key entry, reader exit and final cleanup. No observation error is recorded.

Subtracting immediate children from every raw span, summing the resulting exclusive costs, and adding the unwrapped residual reproduces all three setup metrics exactly:

| Metric | P11 | L03 |
| --- | ---: | ---: |
| Shared and admitted Reach setup operations | 23171 | 17185 |
| Generic `checkpoint` setup operations | 13121 | 8900 |
| Top-level observed shared operations | 22144 | 16116 |
| Unwrapped shared residual | 1027 | 1069 |
| Unwrapped `checkpoint` residual | 0 | 0 |

The residuals include the 1020/1062 certificate-identity charges and seven other charges. They are retained, not assigned to a convenient measured function. Coarse spans have complete category snapshots. Nested spans support exact shared/Reach/`checkpoint` attribution only; they do not establish other per-function category counts.

The principal phase measurements are:

| Observed work | P11 | L03 |
| --- | ---: | ---: |
| `_phase` calls | 60 | 24 |
| `_phase` inclusive operations | 6006 | 3300 |
| `_phase` exclusive operations | 6006 | 2924 |
| `_axial_derivatives` calls | 0 | 4 |
| `_axial_derivatives` inclusive operations | 0 | 376 |
| `_axial_derivatives` exclusive operations | 0 | 174 |
| Axial-scoped `_l1` operations | 0 | 132 |
| Axial-scoped `_axis_transport` operations | 0 | 70 |

For P11, 40 phase calls are children of `_phase_tables` and 20 are children of final `point_phase` calls. For L03 the split is 18 and six. No observed phase call occurs inside reference construction for these two requests. These are case observations; the general source permits phase calls during release/impulse handling too.

For L03, the four axial calls cost 84, 84, 104 and 104 operations for `rig.arm.forearm.frame` and `rig.tool.frame` across intervals [0,2] and [2,3]. The exact reconciliation is `174 + 132 + 70 = 376`. Those values are included in `_phase`'s 3300; adding them again would double-count them.

## Repetition and the selected NO-GO

P11 never enters the axial path in the measured setup. There is therefore no P11 operation saving available from the selected axial-only or axial-helper-only change on the unchanged path.

L03 has three repeated typed `_l1` inputs, with 12, six and four calls, each costing six operations and returning one observed result variant. Its 14 axial-scoped axis-transport calls share one exact typed argument group and one result variant, at five operations per call. Removing all repeated helper calls after one first call per group would omit at most `19*6 + 13*5 = 179` observed original charges before any fresh admission, lookup, insertion, invalidation or displacement cost. That is a favorable gross count, not a valid implementation or measured net saving. It overlaps the 376 axial charges and cannot be added to them.

The helper wrappers were active only under axial spans. Zero P11 helper observations do not mean P11 never calls `_l1` or `_axis_transport` elsewhere. Within-process state/model identities and equal typed operands do not prove source equivalence, callback safety, or reuse authority.

A stronger, conditional source bound also supports rejecting this isolated setup route as the sole L03 repair. If exact setup outputs and every downstream charged path/cache behavior remain unchanged, even deleting all 376 observed axial charges leaves the 24 wholly unvisited keys and 150 untraversed interval/carrier rows. Their already-required admissions contribute at least `24*6 + 150*3 = 594` further charges. The three row charges are the unconditional successful-path calls in `_IntervalCertificateClaims.check`, `_certified_stored_arc`, and `_CertificateBatch.add`. Starting from 100000 admitted charges, the favorable bound is `100000 - 376 + 594 = 100218`, before finishing the interrupted key and other omitted work. The refused attempted tick is not counted as admitted work.

This is a narrow unchanged-output/downstream-path bound. A change to downstream cache behavior or a different algorithm requires a separate cost analysis. It does not measure complete tail cost, prove a universal impossibility, or support changing the limits. The C061 result should remain a diagnostic NO-GO for its selected isolated route, with no runtime candidate selected and no optimization saving claimed.

## Review disposition

No blocker was found for publishing the stated diagnostic attribution and scoped NO-GO. Product requests still failed; setup audit success is not product acceptance. The current evidence does not establish timing neutrality, a completed export, a new original28 result, Agent delivery, broader regression, destination acceptance, or release completion. C035 remains held and M1 rejected. The next scope must be separately declared rather than expanding this completed experiment.
