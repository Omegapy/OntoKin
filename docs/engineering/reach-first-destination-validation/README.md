# First actual reach destination validation

**The identified P01 quarter-second source artifact passed actual Khronos, Three.js controlled playback and Chromium WebGL checks.** All three new screenshots were opened and reviewed. A later probe run rejected all seven intentionally corrupted artifact/reference variants at their intended checks. This is one short source-component artifact, not the complete reach release, the prescribed source/Agent artifact corpus, or the full product goal.

The [execution archive](execution-001.tar.xz), [summary and archive identity](summary.json), and [visual review](visual-review.json) retain the raw inputs, outputs, browser harness, readbacks, captures, producer report/patch, unsuccessful attempts and exact before/after source identities. The existing [95-document/15-diagram review](../reach-release-review/documentation-review.md) remains unchanged; all its inventory hashes matched at the recovered source cut.

## Exact implementation and artifact

| Identity | Value |
| --- | --- |
| Successful reference/native/browser source commit | `bf35720a42b954a43910506d61a2725492c75185` |
| Tooling implementation | `35ede0a`, merged with root checkpoint `2bdbf6c` |
| Successful hostile-probe source commit | Recorded exactly in `actual-artifact-probes-stage-002.json` inside the archive; includes the noninitial-key correction `a2ea386`. |
| Source program | Frozen P01 bundle, `sha256:b5f5d362666a22b18ae02a338bb869a49748469542121749291fb4a68a823c43` |
| Actual GLB | `sha256:52078036996a5a257ebab07117f59c8087db7c92c7cbbc3277c050bfe1ebd824`, **161,360 bytes** |
| Recording settings | Exact `end=0.25`, `fps=2`, `helpers=false`; original `.001 m`, `.001 rad` and `1e-6 s` caps retained |
| Environment | CPython 3.12.14; Node 22.23.3; Three.js 0.180.0; Khronos validator 2.0.0-dev.3.10; Playwright 1.56.1; Chromium 141.0.7390.37 / build 1194; WebGL2 through ANGLE SwiftShader |

The earlier producer run retained its original dirty implementation report and exact patch. That run reported **90,381 shared callback operations** under the unchanged 100,000 allowance. This destination role did not rerun the export or reinterpret the producer result. It used the exact supplied bytes, checked that their source/destination numerical-basis hashes matched this native verification source cut, and built independent source expectations. Subsequent numerical implementation changes require fresh artifacts; this old-basis artifact must not be relabeled as a later exporter result.

## Executed checks

| Check | Result |
| --- | --- |
| Bridge clock and frozen-case tests | **3 passed**, including exact source clock versus binary destination clock and rejection of a mismatched frozen program revision. |
| Native verifier resource probes | **9 named tests passed**, zero failures/skips; direct TAP output retained. |
| Browser capture selection probes | **3 assertion groups passed**, including paused/resumed L01 and post-release P16 selection. |
| Independent source bridge | Passed; fixed samples inside the requested prefix and exact phase neighbors retained; no production pose sampler used. |
| Actual Khronos validation | Zero errors and zero warnings. |
| Actual Three.js and controlled destination | Passed the complete supplied-byte observations listed below. |
| Actual browser controls and readbacks | All 72 requested source observations passed; play advanced, pause remained stable across frames, and playback stopped at the exact end without wrapping. |
| Actual image review | Three original PNGs viewed; concrete observations and legitimate side-view occlusion recorded. |
| Actual-artifact hostile probes, second attempt | Passing baseline and **7/7 intended rejections**. |

The native run checked **8 retained keys, 7 adjacent intervals with eight distinct interiors each, and both sides of two source boundaries**. Its 68 mandatory samples plus two in-prefix frozen observations and two phase neighbors total **72 observations**. They cover **432 carrier poses, 1,152 world sites and 160,848 repeated world vertices**. The scene contains **6 carriers, 1,370 occurrence vertices, 8 material primitives and 1,260 triangles**.

Maximum independently bounded native discrepancies were:

| Quantity | Maximum observed upper bound | Required cap |
| --- | ---: | ---: |
| Carrier position | `9.838144560088829e-5 m` | `.001 m` |
| Proper orientation | `9.424965516774587e-8 rad` | `.001 rad` |
| World site | `9.838144560088829e-5 m` | `.001 m` |
| World vertex | `9.838526580143945e-5 m` | `.001 m` |
| Local vertex | `8.429369670776957e-9 m` | `.00001 m` |

Every executed stage receipt records its exact command, Git identity, interpreter, elapsed time, raw log hash and stable source inventories before and after. The bridge's separately bounded aggregate offline arithmetic is explicitly not a production request-budget pass.

## Actual visible result

The front image shows the complete gray base, blue/gold support, two arm sections and gold end sphere without viewport clipping. The intermediate image shows the forearm and tool moving upward while the base/support remain fixed, using the same camera. The end-on side image retains the complete silhouette but naturally overlaps the arm sections and tool; unseen back faces and undersides are not claimed visually inspected.

| Capture | Actual displayed time | SHA-256 |
| --- | --- | --- |
| `P01-front.png` | `0 s` | `de7a46c2778491702659774051108b6d5e3e396cb3db5cc1281b842661533232` |
| `P01-side.png` | `0 s` | `0830bb1b7efe634f64c1aa6730dc3df84962be3fb4781124ed7ca4be14ff9f26` |
| `P01-intermediate.png` | `0.12500000372529 s` | `a16ee87209be9532d92c00462174b837d410ca257a29ef907dae37fd5def0ef6` |

The intermediate native schedule requested `0.1250000037252903`; Chromium's actual range control accepted/displayed `0.12500000372529`. Both clocks and their numerical comparison are retained. The difference is within the unchanged time tolerance. Source/artifact identity labels and actual controls remain visible in all images. The short prefix depicts initial action motion, not goal completion.

## Independent rejection evidence and preserved failures

The passing probe baseline is the original exact artifact. Each geometry/material/motion mutation retains the full carrier inventory and independent source answer, then recomputes artifact/reference transport identities. Therefore the following rejections are not simple transport-hash failures:

| Isolated mutation | Actual rejection code |
| --- | --- |
| Local vertex component | `geometry` |
| Triangle index membership | `geometry` |
| PBR metallic factor | `material` |
| Noninitial recorded translation | `native_position` |
| Noninitial recorded proper orientation | `native_rotation` |
| Removed required `key:0` source observation | `sample_coverage` |
| Oversized native accessor declaration | `resource`, before native loader execution |

The first mutation attempt changed key zero's translation. It was correctly rejected earlier by the initial-carrier/first-key identity guard, so that attempt did **not** establish the intended numerical motion comparison. Its failed probe receipt is preserved. The corrected probe changes a noninitial key, preserves the initial binding, and reaches the intended position/orientation comparisons.

The first browser attempt could not spawn Git under the restricted process sandbox (`EPERM`) and did not launch Chromium. The authorized retry used a fresh output directory with the required local process permissions and passed. The first planner command produced a valid plan, but its outer receipt writer collided with the same `native-plan.json` filename; the original plan/log and a separately named successful rerun are both retained. None of these attempts was rewritten into a success.

## Remaining acceptance

Complete source and Agent delivery, all 28 mandatory source GLBs and ten required retrieved artifacts, the prescribed 18 browser artifacts and at least 54 fresh reviewed reach captures, the full independent source/certificate/rate obligations, R01–R12/Q01–Q22, all 42 LP steps, compatibility, inherited workflows, final release audit and resulting-main checks remain separate gates. This record supplies one passing short source component and focused native rejection evidence. It supplies no Agent transport pass, current full-duration exporter pass, or product completion claim.
