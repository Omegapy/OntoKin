# C080: opaque source-authored labels and panels

Candidate `9ee7f115a0bc0a56e61ac726b6f20753ca46b0bb`, tree `01be77b0a7f8b0179e5b16f3172bdaedb81e5f9a`, has completed the bounded C080 candidate checks recorded in [validation-summary.json](validation-summary.json). The implementation adds explicit source `0.13` / `textured-surfaces-0.1`, immutable bundle/files `0.2`, Agent/0.13 and recorded GLB/0.13. It remains experimental development; complete feature and product release acceptance remain false.

The [adopted contract](../../language-design/textured-surfaces-v0.1/ADOPTION.md), [authoring guide](../../language-design/textured-surfaces-v0.1/README.md), [Agent/0.13 guide](../../language-design/agent-v0.13/README.md), and [original independent freeze](../../../examples/textured-surfaces/acceptance-freeze.json) define this finite scope. The full [GOAL](../../../GOAL.md) and [retained gates](RETAINED-GATES.md) remain authoritative.

## What this candidate supports

An existing unplaced native surface can bind a content-pinned opaque PNG to one or more existing material-region keys. One explicit planar affine map per region uses raw recipe coordinates before rigid placement; exact rational evaluation of canonical binary64 inputs is rounded once before binary32 UV delivery. PNG upper-left is UV `(0,0)`, V increases downward, and sampling is nearest with clamp-to-edge. Samples are converted from sRGB to linear before multiplying the unchanged linear base-color factor; existing metallic, roughness, normal and back-face meanings remain intact.

An immutable bundle admits at most four images, each at most 300,000 bytes and 256 by 256 pixels, with separate aggregate bounds. The finite PNG subset is noninterlaced 8-bit RGB or fully opaque RGBA. Declared source closure, CRCs, chunk order, bounded decompression and filter reconstruction are checked under current execution authority. The Agent supports all twelve existing operations, exact source-and-asset transactions, failed-edit rollback, source-only attachment preservation, bounded byte retrieval, current-host reauthorization, cancellation and atomic export publication.

Actual embedded PNG bytes, UV accessors, material/texture/sampler references and source provenance are validated. Unsupported appearance or deformation additions in supplied .13 GLBs are refused. This increment adds no physical mass, collision body, deformation or motion authority; automatic unwrapping, atlases, normal maps, transparency, live destination physics and Unreal import remain outside the adopted promise.

## Actual candidate evidence

| Scope | Recorded result |
| --- | --- |
| Complete local driver | All **34 planned roles passed** in the completed second invocation. **3,759 unit tests** executed, with zero skips or expected failures and a complete passing regression log. Environment: `3.12.14`. |
| C080 source and workflow producer | **102 active cases**, including **45 delivered sources**; **18 workflows**, **16 asset-slice boundary probes**, **2 envelope probes**, **19 hostile supplied-GLB controls**, 15 inline transport and 6 file-transport controls. |
| Independent source/PNG/UV reader | All 102 case outcomes, 45 delivered source artifacts, 9 Agent artifacts and 19 hostile controls passed their separate checks. The 47 original PNG inputs include valid and deliberately malformed cases. |
| Independent raw Agent audit | **119 exchanges / 116 durable request identities**, all twelve operations, 46 retained source snapshots, 9 artifacts and 11 runs. |
| Pinned native destination | **54 GLBs** passed Khronos with zero errors and warnings; Three.js/Chromium decoded **59 actual ImageBitmap images** and checked **five recorded pose times per artifact**. |
| Actual C080 texture image review | **35 captured views** were directly inspected: **21 source views** and **14 Agent views**. These are finite camera views at 0.5 seconds; the separate native reader checks playback times. |
| Fresh inherited full-driver image review | All **35 actual captures** from **6 inherited browser roles** were directly inspected and matched to their role reports and hashes. This is a separate capture inventory. |
| Fresh immediate predecessor .12 | **82 cases / 1,089 assertions**, **121 schema-validated exchanges / 117 durable identities**. |
| Independent .12 raw audit | **24,568 checks**, zero failed, retained as its own evidence scope. |
| Predecessor exact-stream comparison | **1,095 checks** cover all **32 GLBs: 30 .12 and 2 .8 controls**. Every complete BIN chunk is exact. Raw JSON differs only at the actual source-implementation fingerprint, verified against the corresponding source bytes. |

The independent audit, workflow assertions, unit tests and destination observations overlap. Their counts are not summed into a total. The finished local run still identifies **16 inherited external pending cases**; their actual IDs and originating reports are preserved in the summary. One installed interpreter establishes evidence for that interpreter. Required Python 3.11/3.12/3.13 compatibility and other external roles retain their prior boundaries.

The stream comparison permits only the source and destination numerical implementation fingerprint paths. Only the source path actually differed. It verifies each changed value against exact corresponding source files before comparing the remaining raw JSON and complete binary chunk. The original C079 baseline is published candidate `18eeaaa8884b82ccb33b5afef7e70fa09cc9fa52`, not an inferred or substituted source revision.

## Image and numerical interpretation

The source and Agent image reviews bind their exact capture hashes to the actual destination report. Some pocket interiors are occluded in oblique views; underside views do not expose them. The generated repair deliberately overlaps a neighboring panel because the authored parameter controls both placement and mapping. The duplicate-revision RGB reference resolves to an uncaptured source name; actual RGB grids are directly visible in the assembly and generated captures. Seven of nine Agent artifacts supplied the fourteen captured Agent views, while all nine received native destination checks.

Screenshots are qualitative evidence of the visible views. Exact PNG identity, native decoded pixels, UV values, source correspondence and sampler behavior have separate readers. The independent CPU color formula uses its stated binary64 tolerance. Measured Float32 GPU midpoint samples have their own reported precision and do not claim that CPU tolerance. These observations establish no Unreal import, live physics or universal appearance/deformation support.

The inherited full driver's visual, Agent-demo, construction-demo, surface-native, surface-Agent and impulse-Agent browser roles have their own fresh image inventory and actual review. Every reported and actual PNG in those six browser directories is covered. These views are not included in the 35 C080 texture views, and the separate reviews retain their visibility limits.

## Failures, corrections and separate attempts

The original 314-file input freeze is unchanged. Its first actual run rejected two inputs originally labeled valid: the inherited loft used four facets where the existing constructor requires at least eight, and a .12 user function used reserved `digest` as a parameter name. [Input erratum 001](../../language-design/textured-surfaces-v0.1/INPUT-ERRATA-001.md) preserves those original failed expectations and receipts. A separately published correction changes only the facet count, the parameter name and dependent pins; active corpus version 2 explicitly selects 100 original and two corrected cases.

The first producer also retained implementation diagnostic mismatches and an envelope-harness exception. The next attempt retained the remaining nested basis-unit diagnostic mismatch. Corrected runtime/harness versions and later passing attempts have distinct source identities; the earlier failures remain failed observations.

An initial independent Agent audit attempted to parse a deliberately cleared durable request payload. Its failure remains retained. The corrected auditor verifies the existing non-replayable reset tombstone against the exact hash-matching original raw request; runtime retention semantics and acceptance limits are unchanged.

The first full-driver invocation was deliberately interrupted after **351.259 seconds** with source unchanged. It did not reach a passing unit-suite result. The inherited C079 unit role had taken 1059.790 seconds, longer than the driver's default 900-second per-command allowance. The second invocation explicitly used **1800 seconds per command** and has its own completed receipts. This orchestration change did not alter source execution defaults, host authority, expected outcomes or product budgets. The first invocation is not relabeled as passing or as an observed 900-second timeout.

## Source preservation and publication boundary

The independent preservation audit retains every **4,460 C079 tracked path**, its protected historical sets, all original adoption/freeze inputs, and the separate correction inputs. In particular, the C079 95-path input freeze, original C080 314-path freeze, separate 19-path correction freeze and adoption/erratum records remain exact. Detailed scopes and hashes are recorded separately rather than combined into a misleading count.

This document records candidate validation. The raw-evidence archive descriptor and member inventory, any durable archive save, evidence revision E, the expected-head lease and actual merge, resulting-main checks, exact-final role F, portable extraction/restoration and final delivery have separate later records. No successful durable upload or completed integration is established by this candidate record. The coordinator will attach those records to the actual published identities.

No hosted execution was dispatched by these checks. Workflows remain manual-only with default-false opt-in. Normal product limits remain **100,000 operations / 30,000 ms**; higher source requests require separate current host authorization, and caller limits only reduce work. CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 remain the defaults.

## Frozen evidence and continuation

The [archive descriptor](evidence-archive.json) identifies the completed local raw freeze: **5,350 members / 63,927,372 bytes**, with complete readback and unchanged original inputs. The portable handoff retains this archive, all 13 complete source-role indices and actual raw commits, the complete C079 predecessor packet, and separately recorded later integration and delivery outcomes. The original engineering draft and every failed or interrupted attempt remain in the frozen evidence.

After actual resulting-main verification, exact-final checks, complete portable delivery and explicit C080 scope closure, the [next bounded proposal](NEXT-TASK.md) is pure key-preserving construction transformations. It requires a new decision and independent freeze before implementation.
