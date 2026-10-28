# C060 — original P11/L03 recording work diagnostic

## Result and scope

C060 adds a reproducible diagnostic of where the original P11 and L03 recording requests spend their existing operation allowance. **All four product calls failed at the unchanged shared operation limit.** The two final independent evidence audits passed, and four targeted corruptions were rejected across the two audited tool revisions. This checkpoint establishes a consistent work ledger for the executed prefixes; it does not deliver a successful P11 or L03 export.

The exact tested source was commit `5170bb99bfb045c651e1aabb1ac5f24c9d2259dc`, tree `ed848bced2c9f8cf4027ffd278b6bf9e0be606e6`. The candidate adds `tools/probe_reach_recording_work.py` and `tools/capture_reach_recording_work.py`; it makes no product numerical change. The independent auditor was written and run afterward, outside the product checkout. The final tested auditor is 71,385 bytes with SHA-256 `5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf`; `audit-002` binds the actual external executable and capture argv as well as the diagnostic evidence. Publication of this report or auditor does not change which commit the four product receipts identify. [P11 audit](evidence/P11/audit.json), [L03 audit](evidence/L03/audit.json).

The executed checkout contained **488 of 3,329 tracked files**, totaling 9,364,004 verified materialized bytes, including all 65 tracked runtime files. Its manifests explicitly identify 2,841 omitted tracked payloads. Before/after manifests match across both arms and both cases. The auditor reconstructed the full Git tree identity from the materialized and omitted entries and verified the exact commit object, but it did not verify omitted payload bytes. History is shallow. This is a transparently scoped partial checkout, with `complete_stock_harness=false`. [Input inventory](evidence/inputs-before.json), [source verification](evidence/P11/audit.json).

There is no accepted GLB, completed full 28-case corpus run, release acceptance, demonstrated speedup, measured optimization saving, or complete-request cost in this checkpoint. The retained `.glb` files are explicitly named `unvalidated-reader-input.glb`. The unchanged baseline documentation/navigation gate exited 1: it verified all 29 preserved source documents, 233 sections, and registries, then found exactly 12 unavailable historical archive targets while checking 269 documents and 2,009 links. Those targets exceed the available binary retrieval limit. This is an explicit recovery limitation, not a passing gate; the final publication must retain its separate receipt.

## Original requests and actual results

Both requests kept `fps=1.0`, `helpers=false`, position and rotation tolerances `0.001`, time tolerance `0.000001`, the 100,000-operation limit, 30,000 ms elapsed cap, 32,768-bit operand cap, and 256-entry work-cache cap. P11 retained its original three-second horizon; L03 retained four seconds. Construction limits and original source manifests are also unchanged. [P11 original request](evidence/P11/request-result.json), [L03 original request](evidence/L03/request-result.json).

| Actual product invocation | UTC start, 2026-10-28 | Raw process exit | Shared operations at failure | Admitted Reach operations |
| --- | --- | ---: | ---: | ---: |
| P11 control | 21:30:55.898 | 1 | 100,001 | 93,277 |
| P11 capture | 21:31:03.253 | 1 | 100,001 | 93,277 |
| L03 control | 21:31:18.073 | 1 | 100,001 | 95,767 |
| L03 capture | 21:31:30.896 | 1 | 100,001 | 95,767 |

All four calls were serial and finished without a command timeout. Their retained failure is `OKL-E-RESOURCE`, `Construction exceeded max_operations.` Actual command, working directory, source identity, stdout/stderr hashes, start/end times, and raw exit status are preserved in [P11 control](evidence/commands/P11-control.json), [P11 capture](evidence/commands/P11-capture.json), [L03 control](evidence/commands/L03-control.json), and [L03 capture](evidence/commands/L03-capture.json).

The native construction callback increments the shared counter to 100,001 and then raises before the Reach category charge is recorded. That last attempted operation therefore appears in the shared total and not in a fabricated Reach category. Earlier non-Reach construction work accounts for the rest of the shared/Reach difference.

## Disjoint work partition

The table contains shared operation deltas, not elapsed times. Producer intervals exclude the separately listed one-charge stage markers; all intervals between the planning and geometry markers are aggregated. Marker names describe existing code boundaries and do not by themselves prove a single mathematical algorithm owns the whole interval.

| Executed segment | P11 | L03 |
| --- | ---: | ---: |
| Construction | 7,391 | 4,499 |
| Construction return → planning marker | 48 | 15 |
| Planning → geometry, including phase intervals | 21,319 | 19,982 |
| Geometry → sampling | 2,558 | 3,044 |
| Sampling → certification | 14,818 | 16,561 |
| Certification → encoding | 10,774 | 7,128 |
| Original producer stage-marker charges | 7 | 8 |
| Encoding marker exit → reader entry | 4,500 | 3,751 |
| Independent reader initialization → first key entry | **23,171** | **17,185** |
| All entered key calls, including the partial failed key | 10,286 | 19,498 |
| Work between entered keys | 5,129 | 8,330 |
| Final unwind after failed key exit | 0 | 0 |
| **Entire attempted request** | **100,001** | **100,001** |

Every admitted category delta is nonnegative and every segment reconciles to the original full work map. Construction contains 668 P11 / 266 L03 Reach operations. The entered-key rows contain 10,285 / 19,497 admitted Reach operations plus the single refused shared tick. All other table entries equal their admitted Reach deltas. Full per-marker, per-key, inter-key, and category detail is retained in [P11 work ledger](evidence/P11/work-ledger.json) and [L03 work ledger](evidence/L03/work-ledger.json).

Both producers reached the independent reader with complete encoded input: P11 at 61,415 shared operations and L03 at 54,988. The reader then consumed 38,586 / 45,013 attempted shared operations before failure. Reader initialization is a measured span with substantial work in both cases; it is not yet a measured saving opportunity.

## What the failed reader actually visited

| Observed census | P11 | L03 |
| --- | ---: | ---: |
| Keys in supplied bytes | 52 | 178 |
| Carrier nodes | 20 | 6 |
| Adjacent-key/carrier certificate identities | 1,020 | 1,062 |
| Entered key calls | 37 | 154 |
| Returned provisional key calls | 36 | 153 |
| Partial failed key, zero based | 36 | 153 |
| Exact authored time of partial key | 36/25 | 244/89 |
| Wholly unvisited keys | 15 | 24 |
| Provisionally traversed interval rows | 700 | 912 |
| Interval rows not yet traversed | 320 | 150 |

The partial keys consumed 147 / 234 shared operations, including the refused tick. Neither source batch reached final admission. A returned provisional key or traversed row is not a completed continuous proof. [P11 summary](evidence/P11/summary.json), [L03 summary](evidence/L03/summary.json).

P11 failed during exact multiplication while evaluating the centered offset for `rig.head.eyes["right"].frame`. L03 failed during a coefficient division in independent series initialization while evaluating `rig.arm.forearm.frame`; retained locals include coefficient index 7, degree 14, and exponent 129. The L03 entry snapshot retains cursors at 64 updates, while the failing orientation path records `advance=false`. These are observed locations and retained fields, not proof that changing cursor retirement would complete either request. [P11 failure analysis](evidence/P11/failure-analysis.json), [L03 failure analysis](evidence/L03/failure-analysis.json).

The standard-library auditor independently decoded GLB chunks, accessor layouts, exact binary32 clock/transform values, carrier mappings, and certificate identities, and reconciled them with capture arrays. It did not evaluate source semantics or certify the numerical bounds. Baseline postfailure bytes, capture postfailure bytes, and the live captured reader argument agree exactly within each case. [P11 byte census](evidence.zip.parts.json), [L03 byte census](evidence.zip.parts.json).

## Observation checks and negative controls

The collector wraps only the existing `validate_export`, `_key_comparisons`, and `recording_stage` entry points, forwards each original call unchanged, and restores the original functions. Recorded identities are all true and observation-error lists are empty. No trace/profile hook or charged arithmetic replacement was used. Controls and captures agree on complete work maps, limits, diagnostic, failure, actual loaded OntoKin modules, underlying traceback, formatted traceback, and causal exception graph. Only explicitly named, source-bound capture-wrapper frames are removed for traceback comparison. This supports observation neutrality for these two pairs; wall-clock neutrality is not claimed. [P11 audit](evidence/P11/audit.json), [L03 audit](evidence/L03/audit.json).

The earlier `audit-001` pair passed with auditor SHA-256 `b928b033522c998396f3d703a2cdc55000eaf8364e44b78c0abed3a446d04725`. Its three offline negative probes each exited 1 at the intended check: one changed capture work count; one changed a retained GLB byte; one changed a post-run input manifest. Those results remain attributed to that earlier revision. [Earlier negative-check summary](evidence/negative-audit-checks/summary.json).

After tightening actual executable/argv binding, both final `audit-002` runs passed. A fourth negative probe changed the external command executable and was rejected by the final auditor. These audits and negative probes executed no product request; the product-call count remains four. [Executable negative check](evidence/negative-audit-checks/command-executable/check.json).

## Isolated producer π screen: NO-GO

The separate [producer π review](review-pi-screen.md) rejects isolated shortening of the producer's `atan(1/239)` recurrence as the sole fix under unchanged returned dyadic endpoints, keys, geometry, other charged paths, cache behavior, and independent validation. P11 performed no cold producer π evaluation. L03 performed one at precision 96: removing even all 27 iterations gives an overgenerous upper bound of 108 saved recurrence charges. Its 24 wholly unvisited keys alone require at least `24 × 6 = 144` existing `independent_key_pose` admissions.

Thus even the favorable accounting bound is `100000 − 108 + 144 = 100036 > 100000`, before completing the interrupted key or other remaining work. This is a finite NO-GO for that isolated lever. It neither establishes a numerically valid shorter series nor rules out broader algorithms or combinations of changes.

## Finite next research target

Decompose the independent reader initialization span—23,171 shared operations for P11 and 17,185 for L03—before selecting another optimization. Its largest recorded category is the generic `checkpoint`: 13,121 / 8,900. Other visible contributors include source geometry-point checks (2,404 / 1,082), certificate identity checks (1,020 / 1,062), bound decoding, source/metadata serialization, and exact arithmetic. The `checkpoint` category alone does not identify one owner or removable work. [P11 work ledger](evidence/P11/work-ledger.json), [L03 work ledger](evidence/L03/work-ledger.json).

The next bounded investigation should map existing reader boundaries for GLB reading and numeric-basis verification; source/reference and metadata construction; clocks and geometry; phase/boundary proof setup; and certificate identity/track setup before the first key. Its deliverable is a disjoint attribution with a specific cost argument and preserved source-independence obligations. Any added observations must retain the same original request, native work/callback owners, caps, complete byte checks, and baseline/capture equivalence. A failed neutrality check stops that candidate. No tail resumption, counter reset, smaller fixture, reduced horizon, skipped validation, or presumed free replacement work belongs to this experiment.

## Reproduction and retained evidence

The implemented entry points are the [request probe](../../../tools/probe_reach_recording_work.py),
[passive capture](../../../tools/capture_reach_recording_work.py), and
[independent auditor](../../../tools/audit_reach_recording_work.py).

Run product requests serially from a clean checkout of the tested commit, with fresh output directories outside the checkout. The probe is a purpose-built partial-checkout diagnostic; the capture calls its `build()` API and puts those outputs under `diagnostic/`. Neither invocation is the stock complete-checkout source-corpus harness.

The product invocations are below; set `C060_REPO`, `C060_OUT`, and `C060_PY` to absolute paths. The first is the source checkout, the second a fresh evidence root whose parent exists, and the third the chosen Python interpreter. Each actual C060 invocation returned **1**. The calling process must preserve that status rather than normalize it to success.

```bash
"$C060_PY" -B "$C060_REPO/tools/probe_reach_recording_work.py" \
  --case P11 --output-dir "$C060_OUT/P11/control"
"$C060_PY" -B "$C060_REPO/tools/capture_reach_recording_work.py" \
  --case P11 --output-dir "$C060_OUT/P11/capture" --repo "$C060_REPO"
"$C060_PY" -B "$C060_REPO/tools/probe_reach_recording_work.py" \
  --case L03 --output-dir "$C060_OUT/L03/control"
"$C060_PY" -B "$C060_REPO/tools/capture_reach_recording_work.py" \
  --case L03 --output-dir "$C060_OUT/L03/capture" --repo "$C060_REPO"
```

For a complete fresh audit, the caller must also write actual-command receipts in `C060_OUT/commands/CASE-control.json` and `CASE-capture.json`, retaining stdout/stderr files, raw exit code, actual command/cwd, source commit, start/end times, timeout state, and byte hashes, using the schema in the four linked receipts. The probe and capture do not fabricate these external process receipts. The auditor requires them. The commands above alone therefore produce request evidence, not a complete audited evidence bundle.

Set `C060_AUDITOR` to the absolute path of the separately retained auditor, then run:

```bash
"$C060_PY" -B "$C060_AUDITOR" \
  --baseline "$C060_OUT/P11/control" --capture "$C060_OUT/P11/capture" \
  --output-dir "$C060_OUT/P11/audit-new"
"$C060_PY" -B "$C060_AUDITOR" \
  --baseline "$C060_OUT/L03/control" --capture "$C060_OUT/L03/capture" \
  --output-dir "$C060_OUT/L03/audit-new"
```

The auditor uses Python's standard library and Git commit-object reading; it imports no OntoKin code. It validates the executed source bytes at the recorded checkout path, and verifies source/log locations recorded in the receipts. Preserve those paths or reproduce fresh evidence with fresh receipts; moving an archive does not silently rebind provenance. Use `--baseline-command` and `--capture-command` only to identify actual receipt files at explicit locations. Every audit output directory must be new.

Each case retains control and capture input manifests, original request results, all three unvalidated input-byte copies, the capture key/stage/failure ledgers, and the independent `audit.json`, `summary.json`, `work-ledger.json`, `byte-census.json`, `failure-analysis.json`, and stable input receipts. The audit is a consistency and census result for failed requests. Full source-corpus, native/browser destination, visual, documentation, and release obligations remain separate.


## Publication, preservation and next handoff

The raw request and audit evidence, both auditor revisions, all four actual product calls,
all four actual audit calls, all four deliberate rejection probes, and exact copies
of the 488 executed inputs are retained in the ordered archive parts described by
[the archive manifest](evidence.zip.parts.json). [The member manifest](evidence.members.json)
binds every retained member's length and SHA-256. Large byte-census JSON files are
archive members `P11/audit-002/byte-census.json` and `L03/audit-002/byte-census.json`.
Readable files under `evidence/` are byte-identical copies of selected raw records.
Absolute historical paths remain in original receipts; no path was silently rewritten.
Publication documentation checks performed after archive construction are retained
separately under `evidence/`, with their actual input identities and raw command results.

The original source and commit objects are retained for inspection and replay at
their identified paths. This is an executed-input subset with an explicit omitted
inventory, not a replacement for a complete checkout or stock release harness.

These new archive parts are ordinary Git payloads under this checkpoint directory.
The existing `.gitattributes` selects only `docs/engineering/lfs-archives/` for LFS.
No attribute rule, historical payload, pointer, upload claim, or migration status
changes here. Independent remote byte retrieval of each new part is required before
claiming its publication; the PR records the actual readback. This follows the
preserve-payload rule in [OK-ENG-010](../OK-ENG-010-git-lfs-archive-storage.md).

The unchanged [documentation checker](../../maintenance/reorganization-2026-10-17/verify_reorganization.py)
returned raw exit 1 on the clean diagnostic candidate: all 29 preserved sources,
233 sections, and exact registry rows verified, but 12 historical archive link targets
were unavailable locally. The [baseline result](evidence/documentation-baseline.json)
and [actual command](evidence/documentation-baseline-command.json) retain the failure.
Those 12 blobs total 74,915,834 bytes and exist in the verified remote tree. The
connected file endpoint returned empty content for large binary files; the text blob
endpoint could not decode them. They were not replaced by placeholders. Candidate
documentation results are recorded separately in the PR and checkpoint evidence;
this gate remains failed until the unchanged checker succeeds in a complete executor.
The [publication candidate result](evidence/documentation-candidate.json) and
[its actual command](evidence/documentation-candidate-command.json) preserve the
same 12-failure vector after adding C060. No new documentation failure was observed.

Independent reviews cover [source provenance](review-source-integrity.md),
[the diagnostic implementation and isolated pi screen](review-pi-screen.md), and
[the final auditor](review-auditor.md). The current scope and required continuation
are in [HANDOFF](HANDOFF.md) and [the bounded next task](NEXT-TASK.md).

To reconstruct the ZIP, set `C060_DOC` to this directory and `C060_ARCHIVE` to a
fresh output file outside the checkout. The following verifies every ordered part
and the assembled archive before reporting success:

```bash
python3 - "$C060_DOC" "$C060_ARCHIVE" <<'PY'
import hashlib, json, pathlib, sys
directory, destination = map(pathlib.Path, sys.argv[1:])
manifest = json.loads((directory / 'evidence.zip.parts.json').read_bytes())
whole = hashlib.sha256()
size = 0
with destination.open('xb') as output:
    for part in manifest['parts']:
        raw = (directory / part['path']).read_bytes()
        if len(raw) != part['bytes'] or hashlib.sha256(raw).hexdigest() != part['sha256']:
            raise ValueError('Archive part identity differs: ' + part['path'])
        output.write(raw)
        whole.update(raw)
        size += len(raw)
if size != manifest['bytes'] or whole.hexdigest() != manifest['sha256']:
    raise ValueError('Assembled archive identity differs')
print(destination, size, whole.hexdigest())
PY
```
