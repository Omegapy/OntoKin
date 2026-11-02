# Independent C088 production review

**Verdict: accept the finite increment, subject to the retained release gates.** No blocking or nonblocking production defect was found in the reviewed changes.

Candidate: `39afec7971b9221fe58cf7c7d002505d172dd64f`; tree `26b6417d082bd26fa6ace1e718455aeaa7822ccb`. Predecessor: `a969a668f9fdf021793366ac5f5b9a8f9cd0fa56`; tree `2000393ec35ebc50d1517e71c7c1e630227b3a47`.

The review binds 171 runtime/interface-test files totaling 3,376,879 bytes. Inventory SHA-256: `8106567eb6ffc85a0c330b49f46d7bee046d59ec944703fe233b72799b562400`. Records SHA-256: `1f0e0609ce3328eed19c5aaf61b392ea8de8bbd7c0f8c6881fd7787d262e972e`.

I authored independent input and observation tools, not the runtime. This pass reviewed every changed runtime file and the nine new interface tests, together with the unchanged call, cache, type, ledger, protocol, transaction and delivery paths. It performed no candidate execution and made no production changes. Worktree bytes and executable modes matched Git before and after.

## R01 — Declaring-version, capability and name boundaries

The .21 parser is selected only by the explicit header/profile. Capability sets add .21 to inherited features without enabling membership in old units. Linking refuses earlier importers of .21 while allowing .21 to import .20. Name reservation flows through top-level definitions/import aliases, members, parameters, locals, keyed callback binders and generated-part binders. Older names retain their original resolution and qualified imported helpers remain callable.

Source basis: `Specification sections 1-3`; `ontokin/syntax21.py:Parser21`; `ontokin/syntax02.py:parse_source_unit`; `ontokin/profile_capabilities.py`; `ontokin/linker.py:_bindings/link_program`; `ontokin/construction.py:predefined/signature/typecheck_body/_map_binders/effective/name`.

## R02 — Types, native shape closure and bounded key semantics

The source builtin checks arity, Keyed family and exact String query before abstract return. The generated Ref exception is confined to consuming an existing Keyed view; authored Keyed<Ref> and nested Keyed admission remain unchanged. Native admission requires exact KeyedValue/tuple/entry/str/Value/Type wrappers, bounded canonical ASCII keys, complete leaf knownness and exact flattened resolved descriptors including units, numeric child type and Ref nominal identity. The shallow descriptor rejects malformed optional metadata, cycles, deep child containers, Bool exponents, dimensionless Quantity and oversized names without invoking foreign equality/hash. Complete tail admission precedes query checking and key-only scanning; captured entries/type descriptor survive the defined callback replacements.

Source basis: `Specification sections 3-6`; `ontokin/construction.py:parse_type/_keyed_leaf/builtin`; `ontokin/keyed_membership.py:_type_descriptor/_key_domain/has_key`.

## R03 — Eager/static order and diagnostic identity

Inherited ordinary calls evaluate callee and every argument left to right before builtin signature checks. Well-typed abstract/unknown calls return unknown Bool without native stages or query-domain checking. The new builtin/native failures use the whole call node; original child exceptions and their nodes propagate. New key/shape/type/resource messages and details follow the frozen contract. The seven initial reader differences were the inherited private None/public {} diagnostic projection, not runtime failures; that separate reader correction is preserved.

Source basis: `Specification sections 3,4,6`; `ontokin/validator.py:expression`; `ontokin/construction.py:expression/builtin`; `ontokin/keyed_membership.py`; `ontokin/diagnostics.py:Diagnostic.to_dict`; `ontokin/validator.py:fail`.

## R04 — Current ledger, exact stages, caps and interruptions

The helper requires a resolved, admitted actual SharedExecutionBudget and uses it directly. It adds admission 1, input n, query 1, scan k and publication 1 charges with no payload evaluation or String-byte reservation. Each stage charges before its work; callback precedes increment, operation cap precedes the original deadline, and finally restores the caller stage. The evaluator preserves callback exception identity. Request creation and reopen routes retain a fresh request-owned ledger/current policy; no stored receipt or warmed compiler grants authority to a later request.

Source basis: `Specification sections 5-6`; `ontokin/keyed_membership.py:has_key`; `ontokin/execution_budget.py:SharedExecutionBudget.tick/promote`; `ontokin/construction.py:builtin`; `ontokin/budget_agent.py:_BudgetCheck`; `ontokin/budget_program_runtime.py:ExecutionProgramBudget`.

## R05 — Constant/parameter caches and inherited String behavior

has_key is absent from both immutable-call allowlists. Parent classification fails through a has_key child, so neither direct invocation nor a containing planned expression silently avoids membership stages. Existing syntax-only caches and immutable derived binding reuse remain intact. The .21 String route calls the unchanged concat_strings helper, preserving original String diagnostics, per-result/cumulative byte caps, stage accounting and cache exclusion.

Source basis: `Specification sections 1,7`; `ontokin/construction.py:_CONSTANT_CALLS/_PARAMETER_CALLS/_constant_names/_parameter_plan/expression/_string_addition`.

## R06 — Dependencies, generated restrictions and detached origins

The builtin consumes both ordinary argument expressions and marks both operands generated taints before native work. Inherited expression frames retain all six existing detached origin families for true and false outcomes; the helper does not index or manufacture a selected-leaf record. Access and CON-007 restrictions remain in the existing read/shape paths. Independent source and Agent readers checked actual member dependencies, exact origin spans, true/false flow, warm inspection and reopened stores.

Source basis: `Specification section 7`; `ontokin/construction.py:_observe_value_flow/_finish_value_flow/_inherit_value_info/_mark_generated/member/builtin`; `ontokin/program_runtime.py:_project`.

## R07 — Explicit API, protocol/store/default and delivery bindings

The new service/runtime/protocol/store use explicit .21 identities, a separate filename/schema and the inherited source/asset transport. Legacy registries and CLI/Python defaults remain untouched. Export selection, support metadata and closed texture delivery explicitly bind the matching .21 destination. Catalog data are detached copies and current host ceilings are recomputed. All three .21 Agent schemas independently match .20 modulo precisely enumerated binding/document identity scalars; no new provenance or authority fields are admitted.

Source basis: `Specification sections 1,8`; `ontokin/keyed_membership_agent.py`; `ontokin/keyed_membership_program_runtime.py`; `ontokin/keyed_membership_protocol.py`; `ontokin/keyed_membership_store.py`; `ontokin/keyed_membership_agent_catalog.py`; `ontokin/cli.py`; `ontokin/agent_cli.py`; `ontokin/budget_runtime.py`; `ontokin/scene.py`; `ontokin/evaluator.py`; `ontokin/texture_gltf.py`.

## R08 — Atomic publication, rollback, retry and persistence

The .21 adapters introduce no custom acceptance/commit shortcut. Exact source bytes and assets remain immutable snapshots; accepted heads, runs, identity metadata and artifacts share inherited transactions and stale/cancel/owner fences. The injected precommit BaseException leaves no committed artifact, then close fences the target exactly as unknown_outcome. Independent closed SQLite snapshots and raw transcripts establish invalid-edit rollback, stale edit/cursor behavior, no replay of fenced request IDs, fresh-ID recovery and no confused prepared-only artifact acceptance.

Source basis: `Specification section 8`; `ontokin/keyed_membership_agent.py`; `ontokin/keyed_membership_store.py`; `ontokin/texture_agent.py`; `ontokin/texture_program_runtime.py`; `ontokin/budget_agent.py:_execute/_export/_read_artifact/_persist_task_metadata/_check_task_response`; `ontokin/agent.py:_finish/_commit_task`; `ontokin/agent_store.py:close`.

## R09 — Change containment and focused interface tests

All 171 scoped runtime/interface-test files match exact candidate Git blobs/modes. Changes comprise 7 new runtime modules, 12 modified runtime modules and one new file containing 9 interface tests. Across the complete C087 tree, 8,799 of 8,812 original paths retain exactly the same blobs/modes; the only 13 modified original paths are those 12 runtime modules and docs/README.md. No original file is removed. All original 334 tests, 158 tools, fixtures and example answers are unchanged. The 9 new tests supplement frozen external acceptance with discovery/default/schema/type-lineage/CLI checks and do not replace predecessor gates.

Source basis: `RUNTIME-BLOB-INVENTORY.json`; `PREDECESSOR-PRESERVATION.json`; `STATIC-COMPATIBILITY-PROOF.json`; `tests/test_keyed_membership_interfaces.py`.

## Verification supporting the review

The independently authored source/native/control acceptance passed 1,776,399 checks, including 188 candidate source records, 6,871 native/resource records, 256 original C087 controls and 256 candidate controls. All 14 original-control GLBs remain completely byte-identical. The actual Agent/state/ledger/provenance/store acceptance passed 31,006 checks over all 11 workflows, including 114 fresh/warm/reopened requests. All 16 actual non-GLB hostile classes refused; fresh positive rereads after those mutations passed, and every original artifact byte remained unchanged.

The first private diagnostic reader and the first Agent run remain preserved. The diagnostic issue was an inherited private-None/public-empty-object projection in the independent reader. The Agent issue was seven wrong source-scope request identities; the separate reviewed/published transport amendment changed only those request leaves. Neither was repaired by changing production or semantic answers.

Complete GLB semantic/paired/hostile validation, native browser evidence and full inherited regression are separately owned; their independent records must be retained and bound by the root release gate.

## Retained release gates

- **G01** Complete required unchanged inherited-suite execution on this runtime-equivalent cut and preserve every failed/recovered attempt and its exact classification. Owned by root/inspect_handoff; still running when this review was assigned.
- **G02** Root must assemble and bind independent complete GLB/artifact hostile and native-browser/visual approvals to this exact source and artifact cohort. Other agents report passes; their detailed receipts remain separately authoritative.
- **G03** Final published production files, schemas and modes must remain identical to this reviewed inventory/schema proof, or changes require renewed review and relevant verification. Final tool/document publication and remote byte readback must be retained. Future final-source-equivalence/publication gate.
- **G04** Retain all specification section 10 and C087 RETAINED-GATES obligations, including historically failed/pending suites, environments, missing evidence and external attestations. C088 is finite experimental support and cannot retroactively close them. Retained; this verdict does not waive any historical or future gate.

This verdict does not grant universal conformance or change any retained historical failure, missing evidence, pending environment or external attestation. Exact machine-readable findings, evidence hashes and scope are in `REVIEW.json`.
