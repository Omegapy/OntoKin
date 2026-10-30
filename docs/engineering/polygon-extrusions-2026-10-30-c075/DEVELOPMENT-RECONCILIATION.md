# C075 development reconciliation

Prepared from preserved artifacts on 2026-10-30. This note records fixture preparation, new-test corrections and development checker attempts. It adds no test execution. Final suite and release-candidate results belong in the separate final evidence record.

## Frozen fixture preparation

The original `examples/polygon-extrusions/acceptance-freeze.json` and its frozen files remain preserved. The original assembly, repaired assembly and generated scene used the reserved keyword `parts` as an import alias. The retained reproduction reports `OKL-E-SYNTAX`, with `Expected 'IDENT'; found 'parts'.`, for all three. The wrong-unit point reports `OKL-E-UNIT` (`Expected Length, received Time.`); its original expectation incorrectly named `OKL-E-TYPE`.

Correction `C075-001` added separate `corrected/assembly.ok`, `corrected/assembly-repaired.ok`, `corrected/generated.ok` and `corrected/expected.json`. The alias became `libparts`; the diagnostic expectation became `OKL-E-UNIT`. The correction records no change to geometry expectations or runtime requirements. Original inputs, the pinned parts library and analytic expectations were retained.

Evidence:

- `/tmp/c075-geometry-development/preparation-reproduction.json`: explicitly a later reproduction of the original defects at geometry commit `6f037e17ad91ef6909a064cdab2b390ca0cfa5a3`, not the original first execution or acceptance evidence.
- `/tmp/ontokin-c075/examples/polygon-extrusions/acceptance-correction-001.json`: selected corrected files and exact hashes.
- `/tmp/ontokin-c075/docs/language-design/polygon-extrusion-v0.1/FIXTURE-CORRECTION-001.md`: preparation correction and preservation scope.

## New Agent test expectation

`/tmp/c075-agent-first.log` records 20 new Agent tests: 19 passed and `test_binary32_collapse_never_publishes_an_artifact` failed. Its assertion required the entire retained state, including runs, to remain unchanged after export rejection. The observed difference was a retained run; the accepted source and artifact list remained unchanged.

Commit `3fb8cc44de2b52d5b9da5d167428458fba48c4c7` changed only that new test. It now checks the inherited valid-prefix behavior: unchanged accepted source and artifacts, one run bound to the same program, valid through one second, `candidate_only=false`, no delivered level and no artifact ID. It did not change runtime behavior or an older test. The existing Agent/0.7 adoption document describes retained explicit valid-prefix evidence. `/tmp/c075-agent-cohort.log` records the subsequent 78-test Agent/C074 cohort pass with no failures, errors or skips.

## Development acceptance attempts

Each directory below preserves its own `summary.json`, `source-before.json`, inputs and outputs reached before termination. Failed attempts also retain `failure.traceback`; corresponding console summaries are `/tmp/c075-acceptance-devNNN.log`. Later success does not replace any failed result.

| Attempt and evidence directory | Recorded outcome and checker correction |
|---|---|
| `dev001` — `/tmp/c075-acceptance-dev001` | Failed `rectangle exact carrier inventory` after the rectangle had been delivered. The traceback shows the checker expected `Demo.shape`; the retained GLB records the object path `shape`. The checker path expectation was corrected. No Agent exchanges had run. |
| `dev002` — `/tmp/c075-acceptance-dev002` | All 28 source-case records passed, then the declaration-reordering comparison failed. It compared whole material dictionaries, including source-specific `extras.ontokin.program_revision`. The two retained GLBs have distinct revision metadata. The checker was narrowed to region, positions, normals and PBR material values for the geometry-equivalence claim. No Agent exchanges had run. |
| `dev003` — `/tmp/c075-acceptance-dev003` | Stopped with `KeyError: 'next_cursor'` after five exchanges. The checker read the mesh-page result body; `exchange-005.json` records a successful response with `next_cursor` in the outer envelope. The checker was corrected to read that envelope field. |
| `dev004` — `/tmp/c075-acceptance-dev004` | Failed `Exact vertex repair selects frozen repaired bundle` after seven exchanges. `exchange-007.json` records a successful edit. The expected bundle had been constructed with the repaired fixture's filename, while the actual byte edit retained `assembly.ok`. The checker now combines the frozen repaired bytes with the original entry filename and modules before comparing program revisions. |
| `dev005` — `/tmp/c075-acceptance-dev005` | Completed 57 exchanges and recorded 12 artifacts, then schema validation stopped with `_WrappedReferencingError` for `https://ontokin.org/schemas/force-v0.1/forces.schema.json`. The local checker registry lacked the referenced schema. The Agent export receipt recorded 8,915 operations. The overall attempt remains failed; no completed schema-pass count is claimed. |
| `dev006` — `/tmp/c075-acceptance-dev006` | Passed after the local schema registry was extended. It records 28 source cases, 212 passing assertions, 12 artifacts, 57 schema-validated exchanges and 55 durable requests. Agent export used 8,915 operations. The source-before/source-after equality assertion passed. |

These stopping points are evidenced fixture/checker issues, rather than evidence that the runtime failed their corresponding operation. This classification does not convert any failed attempt into acceptance.

The recorded source bindings also differ. Attempts 001–003 identify head `6a6ed020c85a31a5de633d0352fa574c9a2ce2ff`; attempts 002–003 record a modified checker. Attempts 004–005 identify head `177f0d53b9c97286a24966bb0558e78f114062bc`, with checker and request-schema working changes. Attempt 006 identifies clean commit `879e02899b3f782d7ac8f309b3c715d946b2e976`, tree `7c7d3d65605d6250487709304718ff95e894451b`. All six summaries retain `release_acceptance=false` and `remote_head_verified=false`.

## Development destination check

`/tmp/c075-destination-dev001/summary.json` records a passing development destination check at the same clean `879e028…` commit and `7c7d3d6…` tree. It covers 12 artifacts with Khronos errors and warnings both zero, Three.js loading and native motion observations. Browser observations cover `concave-bracket`, `placed-bracket`, `generated` and `agent-repaired`, with two captures each and no recorded page errors or failed requests. The environment records Node `v22.16.0`, Three.js `0.180.0`, glTF Validator `2.0.0-dev.3.10`, Playwright `1.56.1` and Chromium `141.0.7390.37`.

That summary retains `release_acceptance=false`; each browser result still says `visual_review=pending_actual_image_inspection`. It establishes the recorded development checks, not completed human visual review or validation of the later published candidate.

The actual published candidate is commit `d3f0d69b953550b60b5eb0a0b41bc390ba934985`, tree `ea880242abd9e323c1d80a46c2b01bdbd35a2aa8`. Development results above remain bound to their recorded sources. Final results for that candidate are reported separately.
