# Independent closing inherited-run review

**Status: passed.** The terminal inherited run completed 34 planned roles. This receipt is scoped to the exact run, source binding and retained evidence; the C091 canonical-history blocker remains open.

## Exact identity

- Product/source commit: `8190ed7f0f9e1fbd908ec6f01c63ec53ccd51508`.
- Source tree: `3b4297cc8c7a8bcf3f6cfb60beba65eda43dc8d4`.
- Terminal summary SHA-256: `20e65ed88f54b1b7984484924b8e4cf6065d9bd24bdae1e06bd5ce4176c5bf23` (54,541 bytes).
- Review JSON SHA-256: `5fcbb9da9c0f00f2ccbe4911cc47e28aaf397a1a2477fc2c6c7d9c9c073617c2`.
- Run: `/workspace/scratch/b46faa606e44/c091-evidence/inherited-full02`.
- Source-before/source-after: exactly equal; SHA-256 `476d787edc415b2b72ee5a0269cc41584b8d6639e34f0b55a990a448c4ca21cd`.
- Inventory: 12,352 files / 712,578,494 bytes; each original body and ordinary mode was independently bound to the native source commit.

## Executed checks

The complete unit run executed **4,102 tests** in 1287.161 seconds with zero skips or expected failures. The separately selected force-Agent cohort executed **106 tests** in 67.786 seconds, also with zero skips or expected failures. The cohort is a separate execution, not an additional unique-test count.

All 34 role commands, dependencies, working directories, return codes, exact log bodies and declared report bodies were reconciled with the pinned runner plan. The independent review passed 410/410 checks.

| Role | Outcome | Seconds |
|---|---|---:|
| force-agent-tools | passed (exit 0) | 0.115 |
| unit-tests | passed (exit 0) | 1291.122 |
| source | passed (exit 0) | 0.970 |
| agent | passed (exit 0) | 1.270 |
| construction | passed (exit 0) | 39.897 |
| surface | passed (exit 0) | 24.351 |
| impulse | passed (exit 0) | 57.091 |
| documents | passed (exit 0) | 1.318 |
| force-agent-tests | passed (exit 0) | 68.124 |
| force-agent-build | passed (exit 0) | 13.805 |
| force-agent-audit | passed (exit 0) | 1.820 |
| node-tools | passed (exit 0) | 0.069 |
| browser-ready | passed (exit 0) | 1.436 |
| prototype-build | passed (exit 0) | 0.064 |
| prototype-format | passed (exit 0) | 0.165 |
| surface-native-build | passed (exit 0) | 7.420 |
| surface-native-format | passed (exit 0) | 0.718 |
| surface-agent-build | passed (exit 0) | 68.881 |
| surface-agent-format | passed (exit 0) | 0.871 |
| impulse-agent-build | passed (exit 0) | 16.663 |
| impulse-agent-format | passed (exit 0) | 0.488 |
| viewer-build | passed (exit 0) | 0.219 |
| visual-build | passed (exit 0) | 8.389 |
| visual-format | passed (exit 0) | 0.217 |
| agent-demo-build | passed (exit 0) | 7.735 |
| agent-demo-format | passed (exit 0) | 0.165 |
| construction-demo-build | passed (exit 0) | 10.999 |
| construction-demo-format | passed (exit 0) | 0.165 |
| visual-browser | passed (exit 0) | 2.828 |
| agent-demo-browser | passed (exit 0) | 1.529 |
| construction-demo-browser | passed (exit 0) | 1.824 |
| surface-native-browser | passed (exit 0) | 3.395 |
| surface-agent-browser | passed (exit 0) | 4.893 |
| impulse-agent-browser | passed (exit 0) | 5.407 |

### Conformance report counts

```json
{
  "agent": {
    "failed": 0,
    "passed": 10,
    "total": 10
  },
  "construction": {
    "all_adopted_cases_selected": true,
    "case_gate_complete": false,
    "failed": 0,
    "passed": 19,
    "pending": 1,
    "total": 20
  },
  "impulse": {
    "all_adopted_cases_selected": true,
    "failed": 0,
    "full_gate_complete": false,
    "passed": 8,
    "pending": 4,
    "total": 12
  },
  "source": {
    "assertions": 694,
    "expected_invalid_or_conflicting": 29,
    "expected_unsupported": 2,
    "expected_valid": 12,
    "failed": 0,
    "passed": 43,
    "total": 43
  },
  "surface": {
    "all_adopted_cases_selected": true,
    "failed": 0,
    "full_gate_complete": false,
    "passed": 1,
    "pending": 11,
    "total": 12
  }
}
```

There are 16 retained pending external cases. Their identities and reasons remain in RESULT.json; a passed local role does not turn a pending external attestation into a completed gate.

## Source and packaging preservation

The primary checkout’s 188 product modules still match the closing pin byte-for-byte and in ordinary file mode. All nine inherited numerical modules remain byte-identical to C090 commit `94a7796a54725ca764b2027deb43f09204f8a6de`. The two approved evidence packaging tools and unchanged recovery common helper still match their reviewed hashes. No product file or test output was modified by this independent review.

| Workspace | Original run outcome | Ordinary files checked | Exact files retained | Retained bytes | Reconstructible files omitted |
|---|---|---:|---:|---:|---:|
| full01 | failed | 12,316 | 37 | 4,184,205 | 12,279 |
| full02 | passed | 12,364 | 37 | 4,184,205 | 12,327 |

Every actual ordinary workspace file was independently rehashed. Generated, changed, new and non-native bodies and modes match the preserved copies; omitted files match source-before and the native source history. The earlier run’s failed result is retained. Both delta trees and the source object closure are necessary inputs to the final evidence capture.

## Captures and output scope

The completed browser reports contain **35 actual PNG captures**. Each reported path was reconciled with the files present; each body was hashed and decoded as a valid PNG. `CAPTURE-INVENTORY.json` records their dimensions, fixture/time fields and hashes. `ARTIFACT-INVENTORY.json` inventories 2982 outer artifact files.

| Browser role | Actual captures |
|---|---:|
| visual-browser | 3 |
| agent-demo-browser | 1 |
| construction-demo-browser | 1 |
| surface-native-browser | 6 |
| surface-agent-browser | 12 |
| impulse-agent-browser | 12 |

Image interpretation is a separate root review. This receipt certifies capture membership, byte identity and decodability only.

## Retained limits and failures

- The canonical-history reproduction remains an open semantic blocker. This inherited run does not resolve it.
- The run uses one installed Python version; it does not complete the three-version matrix.
- Pending external conformance attestations remain pending. No remote checks or hosted jobs were executed.
- Two reviewer preparation errors are retained with their original attempts and explicit classifications. Corrected review attempts reran the affected comparisons; no product or test failure was reclassified.
- Full release, full product conformance and GOAL completion are not claimed.

## Receipt closure

The exact source binding, terminal role review, artifact/capture inventories and both workspace-delta reviews are listed with SHA-256 identities in `RESULT.json`. The original test outputs remain unchanged.
