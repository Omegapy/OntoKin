# Current-host CPU readback execution contract

**Identifier:** `ontokin.current-host-readback/0.1.0`  
**Decision state:** Draft for independent P05 review. Adoption, implementation, host qualification and R03 acceptance are separate gates.  
**Source baseline:** `743409619a8663682750b0ca29c50547a25dde41`, tree `8202185735f50aa91078a9206c351d917084ed16`.  
**Scope:** The original three synthetic CPU readback methods and four coordinator controls in `tests/test_static_tray_readback_v01.py`, within the complete existing default regression inventory.

## 1. Decision and historical boundary

The historical C225 preparer authenticates one particular C199 environment. Its required Node executable is unavailable among the inspected sources. The available executable differs in bytes even though a version string alone might look compatible. This contract defines a distinct execution provider whose actual inputs must be qualified. It does not restore or reinterpret C199/C225.

The new provider may relocate verification inputs to an external, task-specific directory and qualify the explicitly selected Node build below. It preserves the original test identities, scientific checks, library bytes, numerical thresholds, source budgets, process supervision and failure accounting. It grants no native transaction, Blender start, source export, historical schedule reopening, release acceptance or comparative claim. Original failed and incomplete attempts remain immutable.

P05 changes documentation only. A future implementation may change the original CPU class's imports, availability decorator, setup and teardown to select this provider explicitly. The seven original test method bodies, `check_case`, coordinator seam bodies, synthetic construction and independent geometry oracle remain unchanged. The old `format_check.py`, `readback.mjs`, C225 preparer and `SOURCE_HASHES`, C199 manifest/HOST, dependency archive and historical controls remain unchanged. Their exact source objects are retained in the mapping inventory.

The C225 helper also pins the old test file. It must continue to refuse an operational checkout with revised setup bytes. Historical exact replay therefore uses its identified original checkout and its original prerequisites. No new setup module, hash rewrite or successful current-host result makes that old helper pass or qualifies that historical replay.

This is a branch-scoped implementation design. Only the separate adoption record, after independent review, can accept it for the next bounded C271 implementation phase. Main integration, runtime readiness and R03–R05 remain open.

## 2. Explicit provider and original default discovery

The proposed Python entry point is `prototypes/static_tray_v01/current_host_readback_v01.py`. The proposed JavaScript probe is `prototypes/static_tray_v01/current_host_readback_v01.mjs`. The proposed preparer is `tools/prepare_current_host_readback.py`. These paths do not exist at the P05 baseline and are not implemented in this phase. The preparer will be a distinct new tool, not an edit to C225.

The operational driver gains explicit `--readback-config ABSOLUTE_FILE` and `--readback-config-sha256 EXPECTED_DIGEST` arguments. The expected digest is frozen in the independently reviewed execution plan outside the configuration. Before preparation, the driver compares the actual file against that supplied expected digest and records both in the run summary. It does not treat a newly computed self-description as approval. The driver passes the exact selected path and digest to the Python test process through documented `ONTOKIN_CURRENT_HOST_READBACK_CONFIG` and `ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256` variables. The provider reads only those variables as its selection interface; it does not discover a host by probing old paths or importing ambient configuration. The Node child receives only the original fixed Node environment.

For a normal execution that includes the unit stage, absent, malformed, unapproved or mismatched configuration is a failed preparation with an actionable error. `--list` may enumerate the unchanged plan without a configuration or any runtime starts. Direct invocation of the original unittest module uses the same explicit configuration interface. Its setup fails visibly when the interface or prerequisites are absent. Remove the old import-time `skipUnless` only as the reviewed future setup change; do not replace it with another skip, expected failure, conditional test exclusion or fallback suite.

Default discovery remains `python -m unittest discover -s tests -v`. The original seven method identities remain in that inventory. Default discovery with `-s tests` reports `test_static_tray_readback_v01.Class.method`; explicit package invocation reports `tests.test_static_tray_readback_v01.Class.method`. Record the actual raw IDs and reconcile this one declared namespace alias using the same source path, class, method and body hash. Do not merge duplicate executions or conceal changed IDs by arbitrary normalization. Their method bodies and shared `check_case`/seam bodies retain the baseline AST identities; the source map also preserves exact baseline file bytes. Future setup/import edits require a reviewed diff. New provider controls are additional methods and cannot substitute for any original outcome. Record every discovered method, attempted method, actual result, skip, expected failure, error and interruption; a count or `OK` footer alone is insufficient.

The whole-suite inventory in the source map includes statically resolved generated methods and identifies its analysis limits. Before a qualifying full routine, collect the actual runtime discovery inventory without running methods and reconcile it exactly with the baseline plus approved additions. Import failure, unexpected IDs, exclusions, unresolved dynamic inventory or any missing required method blocks qualification. Static inventory in P05 is not a test execution result.

## 3. Source identity and isolated workspace

The configuration identifies the clean candidate commit/tree, complete execution-relevant repository-relative source inventory and hashes, approved runtime/input lock and approved output parent. Preparation must fail on dirty or untracked executable source, extra executable inputs, missing source or changes after the inventory was frozen. Original baseline and proposed operational source identities are separate records. Proposed-source hashes are unavailable until implementation; record that fact rather than inventing them.

`check_local.py` copies its source into an isolated workspace. A configuration must not silently redirect this workspace to execute the original checkout. After the ordinary source-copy/Git checks, the driver derives a new workspace binding at a fresh external path. It records both roots, the identical commit/tree, equality of the complete copied immutable-source inventory, the selected configuration digest and the actual workspace-relative provider/probe paths. Any approved generated-file exclusion must be exactly the existing driver's exclusion, with original source bytes preserved; it is not a new executable-source exception.

The provider verifies that its own root and each source role are the bound isolated workspace, not another checkout. It checks the source inventory before preparing the manifest, before each checker, and after the cohort. Original-checkout source equality is checked at the driver's existing end gate. A workspace rebind is an explicit derivation with its own identity and evidence, never an edit to the signed-off input file or an implicit string replacement.

### Mandatory per-checker call seam

The future test import explicitly binds `guarded_run_process` from the new provider as the name `run_process` used by unchanged `check_case`. This is a visible, reviewed import adaptation. It is not a runtime monkeypatch and does not alter the original supervisor implementation. The coordinator seams continue calling their original `format_check` entry point and retain their existing mocks.

The adapter has the original caller-compatible signature: `guarded_run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None)`. It resolves only the documented config path/digest, reads the bounded job identified by the exact argv, and checks the job/manifest/config/source/runtime/dependency/stage bindings before calling the original `supervisor.run_process` exactly once. It passes through the supplied existing Clock, absolute stage_end, argv, environment and callback semantics. It neither resets nor extends any deadline; its own preflight and postflight can only reduce the remaining allowance. Optional arguments retain the original signature. Normal CPU jobs must supply the exact declared environment; a non-None cancellation allowance is admitted only for a specifically identified, independently frozen fault-control case. No ambient variable or default setting selects cancellation. Observe and record actual starts without changing or duplicating the original callback.

After every actual supervisor outcome, the adapter preserves its exact process receipt and cause and performs the declared postflight binding/clock checks. If postflight passes, a genuine supervisor `Stop` is re-raised unchanged, preserving its `process_record` and the original expected negative-control behavior. New provider/config/preflight/postflight/evidence errors raise `CurrentHostBindingError`, a distinct `RuntimeError`, not a subclass of `Stop`. This includes any `Stop` raised by the adapter's own `Clock.check` or binding verification: preserve the original timeout/state metadata and cause, but expose it through the distinct provider error. Only a `Stop` originating in the single delegated supervisor call is eligible for unchanged re-raise after successful postflight. Thus the original negative method cannot swallow a provider refusal and count a rejected reference as qualified. A postflight failure overrides even an expected exit-1 result, while retaining that actual result and cause as evidence. It never launches a second checker.

Each attempt has a separate durable provider ledger: expected and actual command/start count, preflight identity, supervisor receipt or explicit no-start, postflight state, failure/cause and artifact hashes. Evidence write/cleanup uncertainty is failed or unknown, never success. Setup records its failure in its own `try/finally` before re-raising, because unittest may never call `tearDownClass` after a failed `setUpClass`. Teardown and the independent outcome audit reconcile the completed ledgers and expected three checker cases; neither may repair or erase an earlier failure. Evidence lives under the predeclared external output parent and survives setup and teardown failure. Every actual post-start outcome retains the original supervisor receipt even if later input checks or evidence finalization fail.

The driver retains every existing selected stage and its current source-preservation checks. The full routine remains a later phase with a justified per-command outer timeout, presently proposed as 3,600 seconds. That driver timeout does not change source or readback deadlines.

## 4. Selected runtime and host qualification

The only supported Node version for this first provider is **`v24.22.1`**. No range, nearest version or fallback is admitted. This keeps the selected version constant while qualifying a different identified build and host. It does not assume binary or behavioral equivalence.

The selected candidate executable was inspected statically in P05:

| Binding | Selected candidate |
| --- | --- |
| SHA-256 | `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa` |
| Bytes | `126951512` |
| Mode | `0o755` |
| Observed source | `/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node` |
| Observed source alias | Regular file; resolved path equals named path |
| Qualification | Not executed or qualified in P05 |

This is the currently supplied runtime's candidate identity, not a vendor-authenticated distribution claim. P05 preserves these candidate bytes in a separate verified input archive, with its exact saved identity recorded in RUNTIME-CANDIDATE-LOCATION.json. That archive contains only the executable and source metadata and remains unqualified. A future preparer retrieves that exact saved archive, copies those exact bytes into an absent task-specific runtime directory and verifies them before execution; it never replaces the shared executable or its aliases. The final selected absolute executable path is frozen before any qualifying command. If the bytes or supported version differ, stop; adopting another build or version needs a separately reviewed versioned amendment before execution.

The new `HOST.json` is a fresh current-host observation. It records actual platform/architecture, kernel/libc identity, Python executable/version and required package pins, Node source/destination provenance and aliases, executable digest/size/mode, ELF interpreter and shared-library resolution, loader configuration, and the tools used to inspect that closure. Its filename, schema and digest are distinct from the old HOST document. Bind the inspector executable/script and interpreter, including `/usr/bin/ldd`, before using them. Record their own relevant runtime inputs; do not describe an uninspected whole operating system as authenticated.

Use a declared clean environment without inherited `NODE_OPTIONS`, `NODE_PATH`, `LD_PRELOAD`, `LD_LIBRARY_PATH`, Python startup hooks or other executable injection. Capture the actual environment and commands. Node `--version` and the bounded closure inspection are preparation processes, with a five-second deadline per command; record attempt, PID/start, output, exit and cleanup evidence. A version string is only one predicate after exact executable/source binding. Resolve all declared aliases and shared-library files; reject unresolved entries and `not found`. Fresh observations and a reviewed immutable lock must precede the qualifying CPU checkers. Recheck the exact file/mode/alias/loader closure before and after execution. Do not blindly execute a mismatched binary merely to learn its version.

Runtime qualification requires the full provider control plan and the original CPU outcomes. A matching version, a hash inventory or a successful ldd is only preparation evidence. If the provider cannot establish the declared closure on this host, it stops with a concrete refusal. It must not copy old closure records and label them current.

## 5. Exact dependencies and installation

Retain the exact 24 external readback files selected by C199/C225: the validator, Three.js and module loader, including the existing loader's source. The source map binds their path-relative identities from the original C199 manifest and authenticated C195 archive. Versions remain validator `2.0.0-dev.3.10` and Three.js `0.186.1` / revision `186`; neither the unrelated general tools lock nor an npm latest install may substitute.

Recovery uses the authenticated archive bytes and a predeclared member inventory. Reject absolute/traversing/duplicate names, symlinks/hardlinks, special files, excess byte limits, mismatched bytes, missing/extra files or directories and unexpected extraction modes. The selected dependency destination must be absent or contain the complete exact declared tree. Existing exact content may be verified and reused. Partial, changed, extra, symlinked or inaccessible content is refused; never repair it silently in place.

For installation, stage verified files under the same parent and use atomic no-replace publication. Bind ancestor-path assumptions and reconcile races. A conflict or uncertain rename requires readback of that exact destination before any retry. Do not delete another writer's content, mutate shared runtime paths, install mount namespaces or introduce global symlinks. Runtime and dependency directories remain outside Git and phase source archives; preserve their authenticated source identity and full reproduction receipt instead.

## 6. Versioned manifest and reader boundary

The configuration schema is `ontokin.current-host-readback-config/0.1.0`. Required fields bind the contract and its approved source identity, candidate commit/tree, source inventory path/size/digest, exact selected runtime build and destination, qualified host-lock path/size/digest, dependency inventory, allowed evidence root, original-method map/discovery identity and parent/derived-workspace relationship. Its expected digest and independent approval live in the separate execution plan, avoiding a circular self-approval field. Unknown, omitted or extra execution-bearing fields are refused. The implementation must derive and review its exact schema and canonical serialization from these requirements before runtime qualification.

New manifest schema: `ontokin.current-host-readback-lock/0.1.0`. New current-host observation schema: `ontokin.current-host-readback-host/0.1.0`. New result schema: `ontokin.current-host-readback-result/0.1.0`. The configuration identifies this contract/version and the independently accepted source/control inventory. Reject all other versions at the new entry point. Old entry points retain their old schemas and guards.

The manifest binds configuration, host lock, source commit/tree and workspace derivation; exact dependency/source/runtime roles; executable path/version/digest/size/mode and aliases; complete file sets; fixed options/environment/limits; probe/module-loader paths; fresh output paths; and the original twelve ordered slot rows from C198 controls. The slot rows remain a structural obligation of the inherited CPU setup. The unused native-schedule path must remain absent, and this provider permits only the three declared synthetic CPU jobs. Those rows confer no native or twelve-check execution authorization.

Fresh manifest, stage, job, probe and evidence paths use exclusive creation. The CPU helper's positive/negative artifacts and existing JSON serialization stay unchanged. Each job binds the exact manifest digest, input GLB and independent audit digests, case, fixed CPU slot label and result path. The new probe's argv retains `--no-addons`, `--max-old-space-size=256`, the exact module-loader entry and the original `--job FILE` shape. No unbound extra flag or executable is admitted.

Before dynamic library imports, the new probe validates the explicit schema, job/input/manifest binding, supported Node version and actual executable path/bytes/mode, source-probe ownership, dependency role/file set and runtime/host bindings. It must not trust a manifest merely because the parent supplied it. The Python provider and JavaScript boundary both enforce their mapped predicates; the new manifest's self-declared hash is not independent approval. Refuse a cross-checkout manifest or an unchecked workspace rewrite.

The scientific body of the original JavaScript probe is copied without semantic changes into the separately named probe. The map identifies exact source segments and every version/schema/bootstrap adaptation. The implementation must provide a reviewed token/AST-equivalence check for preserved JS segments, using an identified parser where available; P05's manually inspected line/segment hashes are static evidence only. Moving the code into a shared body is not part of this selected design: it would alter old source bindings and requires a new decision.

Preserve canonical comparisons, finite-value requirements, exact semantic IDs/names/relationships, scene/node/mesh/animation counts, parent/child ordering checks, matrices, vertex/normal/index layouts, materials/textures, bounds, external-resource rejection, validator diagnostics, post-read input hashing, result size and exclusive write/fsync behavior. Both readers must consume the actual unchanged GLB; metadata or a synthetic success report cannot replace an import. Preserve original exception-to-failed-result behavior and exit codes.

## 7. Fixed scientific, resource and lifecycle obligations

| Obligation | Required value or behavior |
| --- | --- |
| Source execution | 100,000 operations / 30,000 ms; unchanged |
| Outer CPU readback | 30,000 ms monotonic allowance |
| Child work / cleanup | 28,000 ms / 2,000 ms within that allowance |
| GLB / result / log maximum | 8 MiB / 4 MiB / 4 MiB respectively; preserve both stream/aggregate rules from supervisor |
| Job / manifest / audit input maximum | 32 KiB / 1 MiB / 4 MiB, plus exact existing per-role limits |
| Position / translational matrix tolerance | 0.000005 m |
| Other matrix and normal tolerance | 0.000001 |
| Imported scene | One scene, 14 semantic nodes, 12 meshes, zero animation and cameras |
| Validator | Zero errors/warnings and no truncated result; original fixed options |
| Negative reference | Add exactly 0.001 to left/base `world_matrix[0][3]`; preserve all other input bytes except its explanatory scope |
| Required negative outcome | Same GLB as Q01 positive; rejected import comparison with intended `matrix_0_3` finding; checker exit 1 is expected test success |
| Process starts | One actual checker per original CPU case; exactly three for one complete original CPU cohort |
| Lifecycle | Original supervisor, process groups, reaping, closed handles, cleanup and uncertain-outcome handling |

Preserve the original Python `run_process` and coordinator mechanisms. Do not replace timeout/cleanup predicates with a successful smoke test. The four coordinator controls remain explicitly mocked seams; they do not prove actual native cleanup. The three CPU checkers provide real Node start/exit/cleanup receipts. Label every other controlled child or mocked boundary separately, without double counting.

Each positive probe retains all original measurements and exact comparisons. Independently recompute all expected numerical rows against the original reference; historically these three cases each produced 2,060 scalar rows. Verify the observed inventory rather than passing solely because that count matches. The changed reference must yield exactly the intended numerical discrepancy under the original thresholds, as required by the C225 outcome audit, while its unittest assertions remain unchanged. The CPU independent audit uses the measurement interface; it does not thereby exercise every full-layout rule in the reader. Map and preserve those rules without claiming they were executed by these methods.

Unknown child, cleanup, pending-marker or write outcomes remain unknown/failed as observed. Never report a successful skip or retry as the original pass. Every separately authorized new attempt uses fresh paths and preserves the earlier attempt and its denominator. No automatic retry follows a timeout.

## 8. Predeclared provider controls and future gates

The machine-readable control plan in `CONTRACT.json` binds each requirement to an observable refusal and execution boundary. Before implementation qualification, an independent author freezes exact positive and mutated inputs, expected rejection stage/code and expected process count. Controls cover executable digest/size/mode/version/path/alias, missing/changed runtime or loader files, inspector provenance, missing/extra/changed/symlinked dependencies, cross-checkout or changed source, wrong schema/options/slot/argv, time-of-use changes, unsafe existing destinations, missing selection, mutated manifest, extra/missing method identity and interrupted cleanup/finalization.

File/manifest controls use actual isolated inputs. Tests of a simulated version response or cleanup fault must be labeled mocked boundary evidence and cannot establish the real host or real process outcome. Parent-side pre-execution input refusals require zero checker starts. A separately declared direct-probe negative control starts one Node checker and must fail before importing reader libraries; its actual start is retained. These are different control routes, with different predeclared counts. Distinguish these from bounded preparation probes, the three original real checkers and any separately predeclared lifecycle test processes. Preserve the actual changed-reference negative through both retained readers.

Gate D: independent review accepts this exact design and complete source map; P05 can then deliver and stop. Gate I: a fresh bounded phase implements only the accepted design, binds every changed source, preserves the mapped method/scientific predicates and passes focused provider controls with independent review. Gate H: a selected actual host and exact source/dependencies qualify under the frozen positive/refusal plan, with the original seven-method results and complete process/artifact evidence. Gate R: a later full routine executes every required original method and stage on the eligible environment, with zero missing/skipped obligations and independent R03 acceptance. R04 integration and R05 final parent closure retain their own gates.

If design equivalence cannot be established, leave the design unadopted and deliver the concrete blocker. If future implementation or host qualification fails, preserve that result and stop at its declared boundary. No gate may be satisfied by rewriting expectations, old pins, a count-only inventory or a replacement suite.

## Source support

This design derives from the exact baseline versions of `tests/test_static_tray_readback_v01.py`, `prototypes/static_tray_v01/{format_check.py,readback.mjs,supervisor.py,lock.py,transaction.py,canonical.py}`, `tests/test_static_tray_reader_v01.py`, the independent `tools/static_tray_reader_v01` sources, C198 controls, C199 external inputs/HOST, C225 `PREPARATION.md`/helper/`REVIEW.md`, and the P04 current-host proposal. The original-method/predicate map supplies exact hashes, source anchors, call relations, adapted guards and coverage limits. Existing OK-ENG-006/009 and C271 requirements retain their authority. This file itself reports no behavioral execution.
