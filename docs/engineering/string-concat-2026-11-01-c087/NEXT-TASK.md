# Proposed C088: bounded keyed membership for optional component configuration

**Status: proposal for the next bounded task; no adoption or implementation authority is established by this file.** Review one pure membership predicate against a representative reusable modeling task. Proceed to implementation only after the separate contract decision and independent exact input freeze below have been published and read back.

## 1. Reconcile the actual C087 handoff first

Start with the final `README-START-HERE.md`, recovery verifier, handoff, retained gates and integration/readback records. Recover the exact identified source, native Git object chain, frozen inputs, amendments and original failed attempts. Verify all hashes, file modes, tree, commit and parent chain before editing. Read current `AGENTS.md`, `GOAL.md`, `STATUS.md` and the applicable validation and integration policy. Inspect the current remote head and integration lease before declaring an isolated working scope.

This proposal reviewed combined C087 implementation `af585dd9a6d952a61a0ea8b45d3597ef6cc4b796` (tree `82c9d138fb5aedc2f4ca12483caa96bb9ade3455`). At this review, the full inherited validation, new source/Agent evidence and independent readers were still running. This file does not predict their disposition or the eventual integration commit. Use the final handoff's observed identities and results. Complete any outstanding C087 task before starting C088 implementation.

## 2. The existing solution and the utility question

Keyed membership is already expressible. A typed helper can reduce equality over the collection's keys and use the existing conditional to guard indexing:

```ontokin
return if reduce_keyed<Bool>(values, false,
    (found, key, value) -> found or key == query)
    then values[query] else fallback;
```

The included `membership-workaround.ok` and its independently written expectations were run on unchanged exact C086 `5d83b07354296a891c1a6acd70efc77322d2127f`, using Python 3.12.14. The present-key case produced the expected 2 m width; the missing-key case selected its 1 m fallback without dynamically indexing the absent entry. `workaround-observation.json`, the two raw logs and `SOURCE-BASIS.json` retain the exact command, source and expected-input hashes. This is a two-case language observation, not a comparative performance or authoring study.

The current workaround needs a typed reduction/helper or a filtered intermediate for each use. A purpose-specific predicate could provide the same direct question across admitted immutable keyed data without an accumulator, callback or result collection. The proposed utility is a small standard operation for agent-authored reusable libraries. It does not add a previously impossible programming behavior.

The representative modeling task is a pinned panel or structural-component library with a complete catalog of default dimensions and a sparse map of optional per-key dimensions. A lookup selects a supplied override when present and its catalog default otherwise. Two independent occurrences share the catalog and geometry library while receiving different override maps. Existing String concatenation/rekeying supplies distinct namespaces; existing map construction supplies the actual independently identifiable parts.

An agent inserts, changes and removes one occurrence's override, then inspects and repairs its dimensions. The other occurrence, original catalog/library bytes, retained keys, materials, textures and independent recorded motion remain unchanged. An invalid selected dimension still fails the existing geometry domain checks atomically. An unguarded absent lookup still fails. The new operation would not create an override, discard an unexpected catalog key, or validate cross-map configuration automatically.

Select this narrow reusable-program question for C088 because the optional-configuration task has an existing semantic control, concrete geometry and a scoped-edit workflow. Broader exterior topology, deformation and mechanical gaps remain required work; they need different numerical and domain decisions. This choice does not claim that membership is the largest product gap. If review finds the existing typed helper adequate and no meaningful benefit from a primitive, retain that finding and select another bounded modeling increment instead of adding an unused API.

## 3. Contract decision before runtime work

Review the preferred single spelling `has_key(collection, key) -> Bool`. Do not add a fallback-returning lookup, option type, exception handling, collection mutation, generic user-function system or additional String operation in the same increment. Source `.21` / `keyed-membership-0.1`, explicit Agent/0.21 and recorded GLB/0.21 are provisional names only. The adoption must settle exact bindings and preserve ordinary CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 defaults.

The recommended semantic boundary for review is:

- Accept one already valid finite immutable `Keyed<T>` and one exact String query. Infer the existing element type; introduce no new allowed element family, coercion or payload conversion. Explicitly decide whether generated `Keyed<Ref<...>>` views are in scope. If accepted, retain every existing access, generated-shape, cycle and taint restriction; membership is no new authority over generated parts.
- Evaluate the collection once, then the query once. The collection is an ordinary eager value: membership must not suppress errors incurred while constructing its payload. Search only its admitted stable keys. Do not evaluate payloads again, compare values or materialize a new collection.
- Return true exactly when the valid query key is present, and false for a valid absent key, including an empty collection. Preserve case, punctuation and full spelling. The proposed query-domain decision is the unchanged 1–64 ASCII-character stable-key rule used by indexing; an invalid query remains an explicit key-domain error rather than a false answer. Freeze the exact validation order and source span.
- Under abstract/static evaluation, check both input types and return unknown Bool. Freeze whether any literal key-domain validation occurs statically by comparison with inherited indexing; do not quietly turn static absence into false or inspect unknown payloads. Unselected branches retain complete inherited type/name/access checking. Dynamic branch selection continues to determine whether an actual lookup or fallback executes.
- Gate the new name and behavior by the unit declaring the call. An older imported helper does not acquire a new builtin from the entry program. Earlier definitions legally using the same unreserved name retain their original binding. Review imports, shadowing, aliasing and declaration diagnostics before choosing a reserved name.
- Preserve every actual input/query dependency, definition read, generated-view taint and inherited map/filter/reduce/merge/zip/rekey record needed to explain the selected branch. True and false observations both depend on the admitted collection. No membership result is a writable key, a source span or a new generated identity. Avoid adding a public lineage family unless the representative inspection task demonstrates a precise need.

Define the real bounded algorithm and charge schedule before writing the oracle. A straightforward canonical-key scan is bounded by 256 entries and 64 characters per valid key; it can stop at the first exact match after the collection and query have been admitted. Choose exact operation charges and cancellation/deadline checkpoints for admission, each examined key and Boolean publication. Specify empty and absent cases. Do not build a set/dictionary or scan an oversized query before authorizing the corresponding work. The fixed String-result/cumulative caps from C087, source limits, value accounting and numerical/cache/cursor bounds remain independent.

Use the complete request's current admitted ledger and original deadline. Existing acceptance, caches, stores and artifacts grant no future execution authority. Decide cache eligibility and actual-read replay explicitly. Callback exceptions retain their original identity; input/domain, current-authority and publication failures need predetermined precedence and exact diagnostics.

## 4. Independent freeze and acceptance evidence

Before runtime changes, publish a reviewed adoption with the grammar/name-binding decision, admitted types, exact signatures, evaluation and static rules, real work schedule, diagnostics/locations, provenance and output allowances. A different reviewer must author expected values, refusals and workflow observations independently from that contract and original source.

The complete freeze should cover empty, singleton, first/middle/last/absent membership; reordered keys; case and punctuation differences; 1/64/65-character and invalid queries; every admitted element family; wrong arguments/types/arity; eager invalid input payloads; unknown locals, empty callback bodies and unselected branches; source-version/name-binding boundaries; composition with all inherited keyed transformations and String concatenation; guarded and unguarded lookup; generated-view taints/cycles; dependencies on both false and true results; current host ceilings and reducing caller caps; exact cancellation/deadline/operation boundaries; and repeated calls/caches/reopened stores.

Freeze the representative task's literal Boolean, selected-width and final-key expectations, geometry/PBR/UV/image facts, fixed animation observations and targeted-edit invariants. Include a failed selected override, valid insertion/removal, unchanged sibling/library, stale revision/cursor, rollback, reopen/retry, changed request payload and interrupted-publication cases. Keep source/program/image hashes and byte spans exact. The schema remains closed and bounded; no output inspection should require an unbounded membership trace.

Preflight independently authored immediate-predecessor controls on exact unchanged C087. Use both explicit literal selections and the existing typed reduction helper where useful; expected answers must precede execution. A helper control does not establish the new operation's charge schedule. Publish and read back all reviewed frozen bytes/modes and their commit/tree before implementation. Later input defects require separate reviewed preconditioned overlays that preserve the originals and their failures.

After implementation, run the complete frozen source/Agent/resource cases, independent store and artifact readers, hostile mutations and complete immediate-predecessor workflows with exact retained-artifact comparisons. Run the mandatory inherited local validation roles and fresh native delivery/capture checks for the actual affected scope. Bind every result to the candidate source, input hashes, commands, environment pins and artifact identities. Use the current observed-head integration process; verify actual resulting main. A passing development increment remains distinct from complete feature release and full-product acceptance.

## 5. Retained obligations

Carry forward the final C087 retained-gate record verbatim by identity, together with the original C086/C085/C084 failed and recovered attempts. Original28 remains 24/28 and overall failed unless a separate original-gate execution establishes otherwise. Preserve the external-case, interpreter, comparison/passive-authority, adverse-timing, complete-reach, storage-cause and missing-history limitations at their actual recorded dispositions. New higher-budget results cannot retroactively pass an original gate. Do not edit original horizons, rates, equations, fixtures, helpers, oracles or tolerances.

The full `GOAL.md` remains authoritative: reusable typed authoring; useful exterior form and appearance; physical interactions and mechanisms; creatures and purposeful movement; flight/swimming; vegetation; terrain/structures; liquids/deformable matter; richer animation and actual named engine delivery. This predicate creates no physical, engine or release authority. Measured authoring benefit still requires a documented direct-tool baseline, unseen variants, repair effort, cost and quality. Hosted workflows stay manual-only with default-false opt-in. This proposal starts no implementation, job, worker or continuation schedule.
