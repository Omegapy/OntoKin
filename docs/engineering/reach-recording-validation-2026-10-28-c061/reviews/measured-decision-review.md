# C061 measured decision review

Date: 2026-10-28. Reviewer: `c060_review`. Scope: static review of the completed round-001 evidence, final diagnostic tools and unchanged runtime source. No product import, request, audit replay, test, archive, compression or SQLite operation was performed for this review.

## Disposition

**NO-GO for an isolated axial reader-setup optimization as the sole way to complete these original requests within 100,000 shared operations.** P11 has no observed axial setup work to remove. For L03, even free replacement of all 376 observed axial setup operations leaves a conservative necessary-work lower bound of **100,218** operations, conditional on preserving exact setup outputs and all downstream charged paths and cache behavior. This is a source-derived bound for that narrow proposal, not a measured complete-request cost or a statement about all possible algorithms.

No inconsistency was found between the recorded cutoff, disjoint axial spans, named admission counters and the proposed bound. No runtime candidate or further product run is needed to reject this isolated lever in the declared scope.

## Evidence and source identity

The actual P11 and L03 `audit-001/audit.json` files report diagnostic audit success with **381,009** and **677,251** assertions respectively. Both retain `product_request_status="failed"`, `accepted_artifact=false`, `release_acceptance=false` and `complete_stock_harness=false`. Their comparisons record identical original settings, complete work maps, raw reader bytes, causal exceptions, underlying tracebacks, final cache occupancy and the 36 loaded runtime modules for control and capture. These support the recorded accounting equivalence; they do not establish timing neutrality or speedup.

The executed source is commit `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`, tree `037157a58442ba1956597d32e1e540802f9ed896`. The audit records a named partial checkout with 491 verified materialized files, 9,527,653 materialized bytes and all 65 runtime files; 2,890 tracked files were omitted, their payload bytes were not verified and history is shallow. This is not a complete stock-harness execution.

I independently compared all 65 current runtime files under `ontokin-c061-run/ontokin/` with the actual L03 pre-request input manifest: byte lengths, SHA-256 values and Git blob identities all match. The final collector and adapter hashes match the previously reviewed frozen tools. I also checked the byte lengths and SHA-256 values of both cases' summary, work-ledger and reader-setup-analysis files against their audit member descriptors. This review consumes the existing audit receipts; it does not rerun their assertions.

## Measured setup opportunity

The measured setup interval ends at the first `_key_comparisons` entry. The collector restores the setup wrappers before calling that original function. Both audits confirm the boundary and native dispatch/restoration checks. Work after that boundary is outside this proposed optimization.

| Recorded setup work | P11 | L03 |
| --- | ---: | ---: |
| Total shared/Reach operations | 23,171 | 17,185 |
| Axial calls | 0 | 4 |
| Axial inclusive shared/Reach/checkpoint operations | 0 | 376 |
| Axial exclusive operations | 0 | 174 |
| Axial helper operations included above | 0 | 202 |

The four L03 axial spans are nonoverlapping: IDs 23, 33, 44 and 56, with inclusive costs **84 + 84 + 104 + 104 = 376**. Their exclusive costs are **39 + 39 + 48 + 48 = 174**. Their direct helper work is **22 `_l1` calls × 6 = 132**, plus **14 `_axis_transport` calls × 5 = 70**. Thus **174 + 132 + 70 = 376**. The inclusive 376 already contains all 202 helper operations; subtracting both would double-count the opportunity. The surrounding `_phase` inclusive totals also contain these axial spans and cannot be added as another saving.

These are measured nested scalar deltas. Full named-category maps exist at coarse setup boundaries; `nested_full_category_attribution_available=false` and nested exclusive category maps remain unavailable. No unmeasured per-function category split is needed for this bound.

## L03 lower bound and absence of double-counting

The original shared counter ends at **100,001**, including the one refused tick. `ConstructionBudget.tick` increments before rejecting an operation above its cap; `ReachExecutionWork.charge` calls that external callback before admitting its own category increment. Therefore the conservative base is **100,000 successfully charged operations**, excluding the refused attempt.

The L03 evidence contains 178 retained keys, six carriers and 1,062 interval/carrier certificate rows. Keys 0 through 153 were entered; keys 0 through 152 returned provisionally. Key 153 fails during its source orientation work, before the interval loop can process any row for the pair with left index 152. The work ledger records 912 traversed interval rows and 150 remaining rows. The named counters independently agree: `independent_key_pose=924`, and each of `independent_interval_claim`, `independent_sufficient_arc_domain` and `independent_certificate_member` is 912.

The unchanged [reader source](https://github.com/Omegapy/OntoKin/blob/bd5a09618c123a0b1d3339df3a944cfd6ed63b56/ontokin/reach_conformance.py) establishes the following necessary additional work for successful completion:

| Still-unexecuted work | Why a successful unchanged path must pay it | Minimum ticks |
| --- | --- | ---: |
| Keys 154 through 177: 24 keys × 6 carriers | `_key_comparisons` unconditionally ticks `independent_key_pose` in its initial carrier loop, before stationary/reuse decisions. | 144 |
| Intervals with left indices 152 through 176: 25 intervals × 6 carriers | Each row must pass `_IntervalCertificateClaims.check`, `_certified_stored_arc` and `_CertificateBatch.add`; these separately tick `independent_interval_claim`, `independent_sufficient_arc_domain` and `independent_certificate_member`. | 450 |

The first two row charges precede their local shortcuts. `_CertificateBatch.add` has no successful route past the member charge; any earlier failure would prevent completion. The caller obtains `following = _key_comparisons(...)` before its per-carrier interval loop, which places all 150 counted rows after the actual partial-key refusal. These three categories represent distinct calls, not alternative branches.

The 144 key admissions are also disjoint from the interval charges. The existing 924 key admissions equal **154 × 6**, so all six admissions for partial key 153 are already in the 100,000-operation base and are deliberately not counted again. All 1,062 `independent_certificate_identity` setup charges are already paid; none is added to the tail bound. The 150 untraversed rows comprise the current unprocessed interval plus the 24 later intervals, not 150 new keys.

Granting the candidate free replacement of the entire measured axial setup region gives:

```text
100,000 successful original charges
    - 376 entire observed axial setup region
    + 144 mandatory admissions for wholly unvisited keys
    + 450 mandatory admissions for untraversed interval/carrier rows
= 100,218 > 100,000.
```

This deliberately omits the refused tick, every remaining charge inside partial key 153, all other future arithmetic and clock work, final source/certificate admission, any restart/replay and every replacement, guard or cache cost. It is consequently a favorable bound for the candidate, not an estimate of the complete tail.

The necessary condition is exact preservation of setup results and unchanged downstream work selection, callback behavior and cache behavior. A proposal that also changes later sharing, downstream cache contents, subsequent charge counts or validation paths needs its own analysis and is outside this conclusion. No causal saving or source-reuse authority is established merely by repeated operand descriptors.

## Optional narrower helper-cache ceiling

The helper repeat inventory contains four exact typed argument groups across 36 calls. Keeping one cold calculation for each group costs **6 + 5 + 6 + 6 = 23**, so the optimistic gross helper saving is **202 − 23 = 179**. For a conventional cache charging one lookup per call and one insertion per cold group, the net is at most **179 − 36 − 4 = 139**, before proof, guard, promotion, eviction or fallback costs. This applies only to that specified cold-cache strategy. It is unnecessary for the stronger whole-region bound above and should not be described as an implemented or measured optimization.

## Exact reviewed file identities

All hashes below are SHA-256. Runtime/tool paths are relative to `ontokin-c061-run/`; evidence paths are relative to `c061-evidence/round-001/` in the shared workspace.

| Runtime or tool | Bytes | SHA-256 |
| --- | ---: | --- |
| `ontokin/reach_conformance.py` | 206759 | `b4c657eac72186203960b18738f65f08e700f52dffa11c1364c6b4609c59a81a` |
| `ontokin/reach_reference.py` | 259473 | `e17fb50c54f41e13b42ce5bc2c6464544c26992299b474032ad2b19e0485949f` |
| `ontokin/reach_numeric.py` | 38427 | `1bd7da1d6721369d8662ba314e08c8704abfd24a4d9707113da4ac296d92ea0a` |
| `ontokin/construction.py` | 98274 | `eae788d2e4c2a6c0cac76e578c3a1be683fca415e62b6e6e3b55f807d7f346c2` |
| `tools/capture_reach_reader_setup.py` | 50678 | `b90854f1a73053a3f9f9ebd7b67662d27b788f478a39a36cbc95abad2429183e` |
| `tools/audit_reach_reader_setup.py` | 41586 | `ef322586e7693647f07f6901737611c82c844e2a6ed98578f499ac49bf994602` |
| `tools/audit_reach_recording_work.py` | 71385 | `5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf` |

| Evidence file | Bytes | SHA-256 |
| --- | ---: | --- |
| `P11/audit-001/audit.json` | 15920 | `84cbd12d7ce539d77b451be8c55859094711825bc8a2447d2a8dfcfad0c15fb6` |
| `P11/audit-001/summary.json` | 25544 | `25bc5cbde7a9a1a3fd430a8d2efb55183a23a4f64b9ea1849e1f7482392fe5ee` |
| `P11/audit-001/work-ledger.json` | 157069 | `c87c718ed44bb4b8f957307148f4fdcd11514db1968dddfe25d35f9a0bb776af` |
| `P11/audit-001/reader-setup-analysis.json` | 93365 | `a4989f71014bd6f12e897f86e97696d7c0680efda7919362b7c65ab5e976179c` |
| `P11/capture/reader-setup.json` | 998296 | `49fa81a134a14e962d21737197faa1ad32b0d148a15422757275958279f4f55a` |
| `L03/audit-001/audit.json` | 16969 | `927698c0839abdc8a0f13c2e3f245bbd787e30759eba0f2efbc2a1cb2cf3ebc7` |
| `L03/audit-001/summary.json` | 27721 | `07c392bc8a6fde0d66d36d38565e347d05217bd4020e9907fd44f63b5e55d013` |
| `L03/audit-001/work-ledger.json` | 483097 | `6d84fac2d367dc71b825f2632387e625fe34405cc14a2432b98ec9cbcb61cda9` |
| `L03/audit-001/reader-setup-analysis.json` | 87752 | `67a0408aff087cb6a00b486872946edf4c8a729b7a7e0d15c6f741f15b031254` |
| `L03/capture/reader-setup.json` | 622142 | `c86c6bd6c32f0294907a32b01a8f468824cf425e6b0eb36d59ecc1f020a8ffb5` |

Only this review file was written. Runtime, tools, evidence and remote state were left unchanged. All operations pause after the final review hash is reported.
