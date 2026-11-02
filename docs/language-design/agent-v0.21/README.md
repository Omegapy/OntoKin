# Experimental keyed membership Agent/0.21

This explicit interface selects the adopted [C088 membership decision](../keyed-membership-v0.1/ADOPTION.md) and [exact specification](../keyed-membership-v0.1/SPECIFICATION.md). The [independent input packet](../keyed-membership-v0.1/freeze/README.md) was published and read back before runtime changes. Implementation, executed validation, integration and complete release acceptance remain separately identified facts.

The binding is `ontokin.agent/0.21`, for source `0.21`, profile `keyed-membership-0.1` and recorded `ontokin.glb/0.21`. Immutable transport remains `ontokin.bundle/0.2` and `ontokin.files/0.2`. Explicit storage is `keyed-membership-program-agent.sqlite3`, schema `ontokin.keyed-membership-program-agent-store/0.1`. CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 remain the ordinary defaults.

## Source operation and authority

`has_key(collection, query) -> Bool` asks whether an exact stable key occurs in an existing immutable Keyed collection. It supports the existing admitted authored leaf families and read-only generated `Keyed<Ref<C>>` views. Generated access, dependencies and `CON-007` shape restrictions remain mandatory; Ref does not become a new authored annotation or writable object API.

The callee and both arguments evaluate eagerly in ordinary left-to-right call order. Signature checks precede abstract behavior. A well-typed abstract or unknown call returns unknown Bool without dynamic input admission, key-domain validation or a scan. A known call fully admits all canonical entries before checking the query, then compares only keys through the first match or the end. Invalid payload construction or a malformed tail cannot be concealed by an early matching key.

Queries use `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. Empty, overlong, Unicode, whitespace or punctuation-leading queries fail explicitly. A valid absent key returns false. Ordinary indexing retains its existing missing-key diagnostic, so a conditional can guard the lookup and select a fallback.

Each call admits at most **256 entries**. The five actual stages are `keyed_membership_admission`, `keyed_membership_input`, `keyed_membership_query`, `keyed_membership_scan` and `keyed_membership_publication`. Successful additional work is **`n + k + 3`** operations, excluding inherited argument/expression/provenance work. Empty input costs 3; a first match in 256 entries costs 260; a last or absent query in 256 entries costs 515.

Every stage uses the original admitted complete-request ledger, deadline, current host authority, caller reductions and cancellation callback. Missing context is refused. The operation creates no independent allowance and consumes no computed String byte reservation. Ordinary defaults remain 100,000 operations and 30,000 ms. Larger source requests require independently current host ceilings; caller caps only reduce allowed work.

Only a declaring `.21` unit reserves the bare name. Earlier helpers, locals and aliases keep their existing meaning, and qualified older helpers remain callable. `.21` inherits bounded `.20` String addition with its original 65,536-byte result cap, 4,194,304-byte cumulative request cap and `string-concat-0.1` resource diagnostics. Earlier declaring units retain their own operator semantics.

## Agent workflow and discovery

`KeyedMembershipAgentService` inherits discover, create, edit, validate, inspect, surface.mesh_page, evaluate, reset, export, artifact, status and cancel. Requests retain exact program/source revisions, source-owned UTF-8 byte patches, atomic accepted-state rollback, idempotent request identities, durable reopen and historical artifact retrieval. A retained never-accepted diagnostic source snapshot cannot gain an accepted revision, run or artifact. Accepted source and historical store contents never grant authority for a new execution.

Requests remain bounded to 8,388,608 UTF-8 JSON bytes. Source, surface, asset and artifact inspection retain the existing bounded pages and slices. Cursor contexts remain revision-bound. A same-ID retry returns the exact historical outcome; a changed payload cannot reuse that identity. Unknown publication outcomes retain the inherited reconciliation and same-ID fencing rules.

Discovery adds `keyed_membership_interface`. Its `source_expressions.has_key` exposes the signature, declaring boundary, admitted collections, key domain, eager/static behavior, all five stage names, charge formula, generated restrictions, provenance and current authority. The inherited String entry states its `.20` and `.21` declaring profiles while retaining the original diagnostic profile and fixed caps. Discovery does not evaluate a linked program's output.

The [request schema](request.schema.json), [response schema](response.schema.json) and [diagnostic schema](diagnostic.schema.json) preserve the earlier operation and provenance shapes. [SCHEMA-DERIVATION.json](SCHEMA-DERIVATION.json) records all 26 structural scalar changes and the exact unchanged `.20` source schema hashes. There is no new public membership-lineage family.

## Sparse overrides and repair

The [examples](../../../examples/keyed-membership/README.md) contain two occurrences of one pinned three-panel library and catalog. A sparse width map configures the first occurrence without changing the sibling. Insertion, update, removal and restoration preserve surviving generated keys, source/library/image pins, appearance and independently specified motion. A selected invalid width fails the inherited geometry rules. An unused override creates no new generated panel.

Both true and false results retain actual collection/query dependencies, generated taints and the inherited map/reduction/filter/merge/zip/rekey contributor records. Membership does not fabricate a selected payload origin. Original source bytes, pins and locations remain the repair authority. Actual calls are not folded into constant or parameter result caches; inherited immutable binding reuse remains distinct from invoking the function again.

The [eleven frozen workflow scenarios](../keyed-membership-v0.1/freeze/agent/request-workflows.json) specify concrete source repairs, bounded inspections, rollback, stale revisions/cursors, cancellation at every membership stage, reopen/retry/reset, current host and caller caps, interrupted publication, exact artifact slices, and warm/reopened provenance. Those requirements are inputs, not automatic passing results.

## Delivery boundary

Recorded GLB/0.21 inherits geometry, material, UV, image and animation representation. Complete comparison against independently authored `.20` literal/reduction controls allows only the individually enumerated source/version/revision/provenance and implementation-fingerprint differences. Native validation and directly reviewed captures are separate observations. A valid artifact does not establish Unreal import, live engine physics, measured authoring benefit, complete experimental-feature release or full-product acceptance. Every [retained gate](../../engineering/keyed-membership-2026-11-02-c088/RETAINED-GATES.md) and every domain in [GOAL](../../../GOAL.md) remains required.
