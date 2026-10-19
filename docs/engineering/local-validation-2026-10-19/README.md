# Local validation migration — October 19, 2026

## Decision and verified scope

The owner requested a way to develop OntoKin without paying for GitHub Actions. [OK-ENG-006](../OK-ENG-006-local-validation-and-hosted-ci-policy.md) makes identified local checks the normal requirement for routine development and integration. The workflow is retained for deliberate manual use, with a boolean opt-in defaulting to false and a guard on every hosted job. Ordinary pushes and pull requests containing that definition request no hosted runner jobs.

This change was reviewed against all **54 Markdown/text files** at original main `4737ede6967e27a42960cfaa1d46272377980a9d`. Their path and blob inventory is in [validation.json](validation.json). Numerical expectations, language semantics, historical evidence and the full product goal are preserved.

**Verified code commit:** [`04622489c269695bb8c4942090935020293f590e`](https://github.com/Omegapy/OntoKin/commit/04622489c269695bb8c4942090935020293f590e)  
**Verified tree:** `dcf4848e2abf8565ad4a7083fa308b0b430b9bab`  
**Change review:** [PR #15](https://github.com/Omegapy/OntoKin/pull/15)  
**Integration state and next project gate:** [STATUS](../../../STATUS.md)

## Executed checks

The complete local command ran from 16:02:06 to 16:10:51 UTC on October 19, 2026:

```bash
python3 tools/check_local.py --full --output-dir build/local-checks/migration-20261019
```

| Evidence | Actual result |
| --- | --- |
| Complete local plan | All 30 steps returned 0 and passed; 525.530 seconds |
| Full regression suite | 689 tests, no failures/errors/skips/expected failures; 185.536 seconds inside unittest |
| Original source conformance | 43/43 cases and 694 assertions passed |
| Original Agent conformance | A01–A10 passed |
| Construction cases | C01–C19 passed; C20 retains its pending external destination attestation |
| Surface cases | 1 passed, 11 pending external evidence, zero failures |
| Impulse cases | 8 passed, 4 pending external evidence, zero failures |
| Documentation preservation | 29 historical sources, 233 sections and 677 local links passed |
| Visual workflow | All 21 original build/format/browser commands passed, after two successful tool/browser preflights |
| Source integrity | All 599 original input files unchanged before/after; isolated immutable inputs also matched |

The seven Python/documentation checks plus two readiness checks and 21 visual commands account for all 30 steps. Format and browser checks used freshly built products. Logs preserve individual commands and outcomes. The pending external cases remain visible in the JSON record: C20; M01–M09, M11 and M12; I07, I09, I11 and I12. No full release or product completion is claimed.

Actual environment: **Python 3.12.14, Node 24.19.0, Chromium 141.0.7390.37, Linux x86_64**. Pinned verifier dependencies were esbuild 0.25.10, gltf-validator 2.0.0-dev.3.10, Playwright 1.56.1 and Three.js 0.180.0. The guide recommends Node 22; this run does not establish Node 22, Python 3.11/3.13 or macOS compatibility.

## Retained evidence and completion record

[validation.json](validation.json) is the compact review record. [evidence.zip](evidence.zip) preserves 2,203 members, including all 30 logs, 14 reports, immutable protocol exchanges/source snapshots, 52 GLB files, 35 PNG captures and generated demonstration products. `bundle-index.json` records member paths, byte counts and SHA-256 identities. Original source files and installed dependencies are available from the identified repository revision; mutable service-store databases and caches are excluded.

Archive: **10,491,902 bytes**  
SHA-256: `849a01a4d2791a1e7b8dee2acf8cba35aa0e757ea51c8e2e47fde8c007948801`  
Git blob: `3a63c8e4889a2875efa72153523dd898ed3987cb`

### Saved-summary discrepancy

The terminal returned exit code 0, and an immediate read showed the final passing summary. A later read retained the preceding `running` checkpoint, already containing all 30 passed step records. The cause is not established. **The raw `summary.json` is preserved unchanged** with SHA-256 `bf6e9412f67fc136311099f6fa3c2d2c3416969b729a048f2825752c420735de`.

The separate `completion.json` records the observed terminal completion and a subsequent audit: all ordered commands match the plan; every log/report hash matches; each report parses; source-before, source-after and current original inputs agree; immutable workspace inputs agree; all 689 tests executed without skips. It does not masquerade as the original final JSON or invent its hash. Packaging verified that binding and preserved both records. No test, raw report, numerical expectation or pending gate was changed to obtain completion.

## Representative visual review

Six captures were actually inspected for this tooling migration. Their hashes and observations are in `validation.json`; the PNGs are retained in the archive.

| Capture | Observation |
| --- | --- |
| Gravity and release | Carrier, payload, trajectory and controls render; the payload is below the carrier at 1.500 seconds. |
| Agent authoring | Both assemblies render with distinct heights; the viewer retains its explicit imported-GLB numerical limitation. |
| Keyed rack | Two racks with different bar counts and a rotated arm render with readable inspection controls. |
| Native studio | Both lofts, the blue upper region and clay surfaces render with source/GLB identities. |
| Repaired palette | Both lofts and the blue region render; material values and artifact identity are readable. |
| Impulse P04 | The rotated body is above the grid at 1.500 seconds; its blue cap and identities are visible. |

These are observations of identified captures, not proof of continuous motion by themselves or a complete release-level visual review. Independent numerical/format reports supply their own bounded results.

## Hosted CI and remaining limits

The candidate had no GitHub Actions runs when inspected. Account spending settings and repository visibility were not changed. **The repository-wide Actions switch was not changed**; older branches can retain automatic workflow definitions until synchronized. Their workflows must be converted before future integration under the current policy.

This migration does not validate or merge PR #14, implement GLB/0.5, or complete F01–F12. Future complete release audits need the separately versioned provider-neutral evidence contract required by OK-ENG-006. Existing releases remain tied to their historical implementation identities.
