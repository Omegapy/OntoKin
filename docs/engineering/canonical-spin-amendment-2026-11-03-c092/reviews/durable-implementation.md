# C092 final Agent and durable review

**Decision: block current Agent delivery and complete durable acceptance.** Candidate `68898e9b73efd20b37842897cbdfb2f61d4801ca` preserves the adopted compatibility policy, but the actual original-bound A08 export did not complete. The separate CLI and native recording gates cannot replace this Agent result.

## Exact candidate and evidence binding

The candidate tree is `eb6ff3fbe4694866f11dae988def4c7b1498524b`. Its actual engine package identity is `sha256:36ee084ce33a200cbfc38833f801c053562678c371487dcb5e1a23495b95898c`. The failed A08 ran against an isolated working draft before publication. An independent byte comparison confirms all 189 package files, all relevant A08 inputs, and the source/destination basis files equal the final published candidate. The existing failure therefore applies to this exact product. The original receipt still identifies its original draft scope; the separate `candidate03-bindings01/RESULT.json` records the correspondence.

## Actual current result

| Check | Observed result |
| --- | --- |
| A08 create | Succeeded; 7,865 operations, 1096.653 ms |
| A08 full production export | Failed; 189,856 operations, deadline diagnostic at 30000.313 ms |
| Source and host allowances | Original 1,000,000 operations and 30,000 ms retained |
| Refusal | `OKL-E-RESOURCE`, `execution_deadline_exceeded`, stage `recording_export_readback` |
| Complete A08 artifact | None; the closed store has zero artifact rows |
| Exact current request/response schema checks | Four passed against unchanged .22 schemas |
| Failed-store integrity | SQLite integrity check passed; both stored payload/response texts match exactly |
| Known guard regressions | All 31 safely refused; zero foreign getter or function-body calls |

Three bounded correctness-preserving guard optimizations were tried. All their original failures are retained. The last uninstrumented result above is the acceptance evidence; the separately retained cProfile run is diagnostic only. It attributes 21.045 seconds cumulatively to 130,091 private guard calls within 31.897 seconds of profiled execution, and still fails the same original request deadline. These profiled timings are not used as an acceptance result.

## Compatibility decisions and their limits

The adopted source method remains `ontokin.source-pose-projective-dyadic-torque/0.2`, basis version `0.4`, with existing .22 closed payload shapes and durable schema `ontokin.torque-program-agent-store/0.1`. Independent extraction confirms producer and reader use the same ordered basis recipe. The current source implementation basis is `sha256:8f1b6e452cf1b4cbc28eac5947e3ffd375c0a8fa139c885cedebb5fd2a0ee3f8` and its derivation basis is `sha256:11a74707f182e8ffb568f6246f5fae653d5a1d4d5098a752e55d98420856c1be`. These are reconstructed identities; no current A08 artifact is available.

The genuine earlier cross-version run passed 182 checks and 57 exchanges on candidate02 `8762e740abd5e8175d015fb5c15b36fe0fbcbff6`, including old-engine fences, exact historical idempotence, current reset/validation, complete actual new GLB retrieval, and current supplied-byte acceptance with old-basis refusal. The old artifact was also genuinely returned under C091 in 122 checks and 38 exchanges. Those successes and the 192 earlier schema checks are preserved. Their approval remains scoped to candidate02 and does not approve the final candidate.

On the final candidate, full cross-version execution, current successful export/retrieval, and reopen continuation have not passed a complete current run. The complete original Agent workflow set and required small-chunk loops also remain open. No synthetic identity result is presented as an actual current implementation result.

## Required next step

Repair the concrete callback-guard cost while preserving the exact numerical method, every required admission, original callbacks, source/host limits, and frozen predicates. Then rerun the full current durable and original Agent gates on the repaired exact candidate. Keep the old successful receipts and each failed attempt intact.

The detailed machine-readable review binds all supporting records by exact byte length and SHA-256.
