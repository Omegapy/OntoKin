# C221 results: authority binding passed; destination work remains pending

## Implemented scope

C221/0.1.0 completes the bounded [authority-binding scope](SCOPE.md). The standard-library [checker](../../../tools/second_target_c221/check_bindings.py) admits the eight exact C220 input files, independently reconstructs the two source-unit revisions and accepted program identity, and joins the full 18-part map against retained semantic and GLB metadata. It does not execute source or start a target. The [contract](CONTRACT.md) defines the finite trust boundary and the distinction between public admission and internal structural controls.

The original implementation was independently reviewed at worker commit `d16dde5b6017df2c37b2537ba4fa0a30ba46be09`, tree `998e4db5e3307849783acbd8f2b259c43a311af1`. Its checker SHA-256 is `fff5569d31b3cd900385ac4b955dc5b30c8ee440ef16d8851b5a0ffb5d03aa4b`. Root integration preserves the exact file bytes; actual published revisions and resulting-main checks are recorded separately in [STATUS](../../../STATUS.md) and [scope issue #174](https://github.com/Omegapy/OntoKin/issues/174). A tree-equivalent publication does not make local and published commits identical.

## Executed checks

| Check | Observed result | Evidence |
| --- | --- | --- |
| Actual retained-input admission | Eight file locks, two source units, 18 parts | [Input report](evidence/INPUT-CHECK.json) |
| Source provenance | 52 span occurrences over 16 distinct ranges | [Independent reference audit](evidence/REFERENCE-AUDIT.json) |
| Geometry-reference inventory | 54 accessor uses, 7,800 instance triangles, 23,400 instance corners | [Input report](evidence/INPUT-CHECK.json) |
| Author controls | 20 methods; zero failures, errors or skips | [Control result](evidence/AUTHOR-CONTROLS.json) |
| Independent controls | 39 passed: 24 public CLI checks and 15 structural controls | [Independent review](evidence/INDEPENDENT-REVIEW.json) |
| Independent static audit | 337 assertions passed | [Reference audit](evidence/REFERENCE-AUDIT.json) |
| Final author delta | Same checker bytes; tests and contract reviewed | [Delta review](evidence/FINAL-DELTA-REVIEW.json) |

Executed environment: Linux x86-64 and CPython 3.12.14. The committed author controls can be rerun with:

```bash
python3 -B tools/second_target_c221/tests/run_controls.py --package-root /absolute/extracted-handoff --report /absolute/outside/author-controls.json
```

The independent driver, detailed reports, raw outputs and original failed draft/reviewer checks are retained in the complete handoff. The [recovery checkpoint](https://chatgpt.com/library?file_id=libfile_fde3_f-291e4dc20a7c8191b1c1a0cef9ad3956_2ab2a24d43748191957f9bcc356b59de&account_id=personal) preserves actual source and evidence.

## Failure accounting and limits

An initial uncommitted CLI draft tried to canonicalize a Python set while comparing bundle field names and refused the run. The author changed that field-set comparison to sorted lists before the first committed checker; the original failed output and later successful checks remain preserved. The independent reviewer initially expected 52 distinct source spans. Its corrected static check counts 52 occurrences over 16 distinct ranges; both the mistaken expectation and its correction remain visible. Neither event is reported as a passing initial run.

The input admission controls reject changed files, forged authority documents, stale or swapped identity, missing/duplicate parts, altered spans, malformed/truncated input, unsafe paths, symlinks, wrong modes and nonregular files. Separate structural controls establish that descriptive names do not select identity. A name edit to an actual locked file still fails exact-byte admission.

These are finite file-integrity and structural checks. Accessor hashes/counts do not establish destination geometry, material, normal or pose fidelity. Retained C218 comparison evidence is byte-bound without replaying its historical numerical acceptance. Source acceptance remains the preserved C210 result. Godot build lineage, runtime/API behavior and useful rendering remain unverified. The original Blender normal failure, original failed regressions, held prototypes and all broader unrun gates remain unchanged.

All target/native starts, version probes, source evaluations, exports, imports, renders and native scene writes in C221 are zero. No dependencies or workflows change. Fresh local CPU controls and preservation/link checks are the applicable cohort for this isolated tool. The full product driver, conformance and export workflows are not rerun because their runtime/semantic/exporter inputs are unchanged and their source execution is outside this preparation scope. No complete regression or receiving pass is claimed.

The [next task](NEXT-TASK.md) is CPU-only observation-schema and geometry-correspondence preparation. The observer, numerical material/pose comparison, two-target report, persistence, process ledger, exact cameras/settings and resource/stop protocol remain pending. C221 stops after its verified saved handoff.
