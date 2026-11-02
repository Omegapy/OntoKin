# C088 independent design review

Status: recommendation for a separate adoption decision. This review does not adopt, implement, execute or release the proposed operation.

Reviewer: `/root/membership_review`. Source basis: observed C087 main `a969a668f9fdf021793366ac5f5b9a8f9cd0fa56`. `SOURCE-BASIS.json` records the exact Git blob and SHA-256 identities of nine inspected production files fetched read-only at that commit. The proposal, AGENTS, GOAL and STATUS were read from the root's recorded GitHub observations. No product workloads were executed and no source or frozen inputs were modified.

## Decision

I recommend adopting a small `has_key(collection, query) -> Bool` operation for the next explicitly selected language profile, subject to independently frozen controls and actual validation. Its benefit is a simpler, common typed question in reusable component libraries: select a sparse per-occurrence override when supplied, otherwise retain the catalog default. A single inferred-element predicate removes the accumulator, callback and element-specific helper declaration required by the existing reduction pattern. That is a concrete API simplification; it is not measured evidence of lower authoring effort, faster execution or improved model quality.

For ordinary authored flat keyed data, membership is already expressible. The original two-case reduction/conditional workaround is an essential semantic control and must remain intact. No claim that this primitive enables previously impossible authored-map behavior is justified. There is also no basis for calling it the project's largest missing capability. Mechanisms, general dynamics, articulation, deformation, richer appearance and named engine delivery remain required work under GOAL.

The primitive is preferable to a new fallback-returning lookup for this increment because it composes with the existing conditional and preserves existing missing-index behavior. It must not mutate the map, add defaults, silently discard unknown override names, coerce payloads or expand the user-function type system.

## Observed source behavior

The following are source observations, not new C088 guarantees:

| Current source | Observation |
| --- | --- |
| `validator.py` 582–589 | Ordinary calls evaluate the callee, then all argument expressions left to right, before builtin signature checking. |
| `validator.py` 607–625 | Abstract conditionals check both branches. Dynamic execution first obtains the statically checked result type, then evaluates the selected branch. |
| `construction.py` 2258–2266 | Indexing checks `Keyed` and String types, then returns an unknown element under abstract evaluation before stable-key domain validation. |
| `validator.py` 46, 141–144 | Stable keys match `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. Invalid keys use a generic bounded `OKL-E-ID` diagnostic. |
| `construction.py` 531–551 | Authored keyed elements are restricted to immutable leaf families; `Ref` and nested `Keyed` are excluded. |
| `construction.py` 1071–1082 | The reduction operation also invokes that leaf restriction. It cannot directly reduce a generated `Keyed<Ref<C>>` view. |
| `construction.py` 2206–2256 | Reading generated parts creates an immutable `Keyed<Ref<C>>` view, checks access, marks the generated dependency and attaches taint. |
| `construction.py` 2768–2774 | Existing `len` accepts `Keyed` values including generated views and calls `_mark_generated` on their taints. |
| `construction.py` 821–912 | Ordinary expression flow carries actual map/reduce/filter/merge/zip/rekey origins and generated-view taints to its result. |
| `construction.py` 2336–2442 | Constant and parameter folding admit an explicit set of call names. A new call omitted from these sets cannot silently acquire that cache path. |
| `construction.py` 2785–2816 | Pure binding memoization already exists and replays source, function and generated dependencies. A repeated binding read is not necessarily a repeated expression invocation. |
| `execution_budget.py` 131–146 | A tick polls the callback first, increments/checks operations next, then checks the original deadline. Callback exceptions are retained by identity. |

## Recommended version and name boundary

Use an ordinary positional call under proposed source `.21` / `keyed-membership-0.1`, explicit Agent/0.21 and recorded GLB/0.21. These names require the parent's separate adoption decision. Bundle/files and ordinary service/export defaults remain unchanged.

Reserve `has_key` only in a declaring `.21` unit. Apply that reservation consistently to imports, top-level definitions, members, parameters, local declarations and callback binders using the existing source-sensitive binding rules. Name lookup must select the builtin from the declaring unit, not the entry program's version. Earlier units legally declaring a function or member named `has_key` retain that binding. A `.21` entry may call an older module's function as `legacy.has_key(...)`; that qualified function is not the new builtin.

Implementation must update both `construction.predefined` and linker `_unique` consistently. Do not add the new name globally to old `PREDEFINED`. Add a new feature membership set and extend the inherited .20 membership set: `.20` String behavior is currently guarded by exact `STRING_CONCAT_PROFILE` comparisons in several paths, including `_string_addition_syntax` and dependency loading. Merely adding a new profile constant would lose inherited String concatenation or incorrectly refuse valid .20 dependencies.

No explicit generic type argument is needed. `has_key<Length>(...)`, named arguments, new method syntax and a new lexical keyword should not be introduced as part of this operation.

## Admitted values and generated views

Accept each currently legal authored immutable `Keyed<T>` leaf family. Preserve exact type dimensions and nominal/frame meanings. Do not permit newly authored `Keyed<Ref<C>>` annotations/literals, `Keyed<Keyed<T>>`, arbitrary Geometry containers or payload conversion.

I recommend also accepting the existing generated `Keyed<Ref<C>>` views as read-only inputs. `len` and indexing provide the relevant precedent. Access checks, generated-shape restrictions and the `CON-007` cycle diagnosis must remain exactly effective. The predicate provides no writable key, occurrence identity, construction authority, physical authority or motion authority.

This inclusion needs explicit scope wording: the demonstrated reduction helper covers authored leaf maps, but does not directly accept generated reference views. Generated-view membership is therefore an additional read-only inspection convenience, not simply the same reduction spelling for every accepted type. Require positive present/absent generated-view cases, private access refusal, same/other generated-shape cycles, propagation through true and false results, helpers and derived binding memoization. If these cases cannot be validated, do not quietly accept the type.

## Evaluation and static behavior

Retain ordinary eager call behavior: evaluate callee, collection expression, query expression once each and in that order. Invalid payload construction in the collection must fail before query evaluation can mask it. Ordinary child-expression errors and source validation retain their existing precedence. In particular, malformed argument expressions may fail before arity is checked because that is how ordinary calls already work.

After argument evaluation, check arity, collection type/admitted family, then the query's exact String type. Under abstract evaluation return unknown Bool regardless of literals or known keys. Do not perform dynamic native collection validation, key-domain validation or membership comparison during abstract evaluation. This mirrors current indexing and keeps unselected branches fully type/name/access checked without introducing a new dynamic error in them.

For dynamic execution, preserve generated-view checks before the private membership work. Use the current admitted complete-request ledger. Validate collection shape and every key before deciding membership. Query String payload validation/domain checking follows complete input admission. Search the canonical keys and return true for the first exact match, false otherwise. Empty input still validates the query. Never normalize, case-fold, compare values, reevaluate payload expressions, produce a filtered collection or create a temporary set/dictionary.

## Recommended bounded work contract

The following schedule is a proposed decision, not an observed implementation result. Each tick uses the current `SharedExecutionBudget`, preserves callback exception identity and restores the previous stage in `finally`.

| Stage | Additional charges | Work authorized |
| --- | ---: | --- |
| `keyed_membership_admission` | 1 | Inspect native container metadata and bounded entry count. |
| `keyed_membership_input` | n | Before each entry's bounded shape, key, ordering and leaf-type admission. |
| `keyed_membership_query` | 1 | Admit exact String payload and stable-key domain. |
| `keyed_membership_scan` | k | Before each key equality comparison; stop at first exact match. |
| `keyed_membership_publication` | 1 | Before publishing either Boolean result. |

Here n is input cardinality and k is the actual number of examined keys. Additional work is `n + k + 3`: 3 for empty input and at most 515 for 256 entries. Ordinary parser, evaluator, dependency/provenance and logical-value bookkeeping charges remain additional and unchanged. These are semantic work units over already bounded keys, not a claim that a string comparison has constant hardware cost.

Complete input admission is deliberately separate from the potentially short equality scan. It prevents a first-key match from hiding malformed later keys or mismatched native leaf types, gives stable failure precedence, and bounds all new work. Because it examines both admission and comparison keys, it must not be advertised as a measured speedup over reduction.

Native admission should require exact `KeyedValue`, tuple `entries`, at most 256 entries, exact two-item tuple entries, exact `str` keys, strictly increasing canonical keys, exact `Value` leaves with the exact resolved element `Type`, and known leaves. Do not invoke arbitrary host iteration/comparison methods or inspect leaf payload contents. Check key lengths using bounded native metadata before regex validation. Each key is 1–64 ASCII characters with the existing key rule. A query of any other length rejects after its query-stage charge without scanning its full contents. The static signature and native admission must have separate explicit tests.

Require an existing `SharedExecutionBudget` with non-null resolved authority and admitted entry revision before private execution. Use the existing missing-context diagnosis; create no fallback ledger. The actual ledger remains responsible for current host/caller limits, cancellation and original deadline. Accepted models, stored artifacts and earlier results grant no future execution authority.

Do not add `has_key` to constant or parameter folding. Every actual invocation pays the defined stages. Existing binding memoization remains valid and preserves its dependency replay; do not promise that repeated reads of a derived Bool reexecute the predicate. Test repeated direct calls, repeated binding reads, changed overrides, reopened stores and new current-authority admission separately.

## Recommended diagnostic identities

These are proposed exact diagnostic strings for adoption. Membership-specific errors should point to the whole call, matching the existing indexing error-span convention; errors while evaluating children retain their own locations.

| Condition | Code / phase | Message and details |
| --- | --- | --- |
| Arity | `OKL-E-TYPE` / `type` | `has_key requires exactly two positional arguments.`; `received` count. |
| Invalid collection kind/native shape | `OKL-E-TYPE` / `type` | `has_key requires an immutable Keyed value.` |
| Wrong query type/native payload | `OKL-E-TYPE` / `type` | `has_key query requires exactly String.` |
| Mismatched native leaf type | `OKL-E-TYPE` / `type` | `has_key input entry has a different resolved leaf type.` |
| Noncanonical/duplicate native keys | `OKL-E-ID` / `binding` | `has_key input keys must be unique canonical stable keys.` |
| Invalid input/query stable key | `OKL-E-ID` / `binding` | Reuse the exact generic `validator.key` message, without echoing an oversized query. |
| More than 256 native entries | `OKL-E-RESOURCE` / `support` | `Keyed membership input exceeds 256 entries.`; `budget: keyed_entries`, `limit: 256`, `consumed: count`. |
| Missing current context | `OKL-E-RESOURCE` / `support` | `Construction requires one admitted execution context.`; `budget_reason: execution_context_required`. |

The exact generic key message is: `Stable keys must contain 1–64 ASCII letters, digits, '.', '_', or '-', and begin with a letter or digit.` Unsupported authored element families retain the inherited `_keyed_leaf` diagnostic; generated `Ref` is the explicit read-only exception, not a relaxation of authored types. Ledger operation/deadline errors and generated-access/cycle errors retain inherited identities. Signature detail fields and malformed native-leaf shape precedence must be settled explicitly in adoption before the independent oracle is frozen.

## Evidence needed before integration

The parent must independently freeze literal truth values, widths, namespaces and scopes before runtime work. The original proposal already specifies a thorough source/Agent/resource matrix. Give particular attention to false-result dependencies, invalid unselected branches, eager input payload errors, older helpers named `has_key`, generated taints and repeated-binding memoization. Native boundary tests must assert actual prefix charges and callback/deadline precedence rather than infer them from the formula alone.

The representative model should use two independently named panel occurrences sharing a pinned catalog and geometry library, with separate sparse width overrides. Verify insertion, replacement, removal and invalid-override rollback; unchanged sibling geometry, materials, texture bytes/UVs and independent recorded motion; exact retained keys and stable repair source spans. Literal selections and the existing reduction helper serve as immediate-predecessor semantic controls. They do not certify the new operation's work schedule.

No full feature release, full-product acceptance, original-gate pass, engine import, live physics or measured authoring benefit follows from this design recommendation. All C087 retained gates and original failures remain unchanged.

## Review limitations

The review inspected nine exact production files and selected type-set definitions through committed GitHub reads. Full source recovery and repository-wide implementation planning are owned by the parent/recovery worker. No product code, product workload, new test expectation or runtime output was generated here. A failed attempt to send all fetched source text through one shell command was rejected before process creation with an argument-list-size error; exact source copies were subsequently verified by Git blob identity using small metadata inputs. That tooling attempt affected no repository file.
