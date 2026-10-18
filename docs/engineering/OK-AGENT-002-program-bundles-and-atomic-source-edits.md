---
project: OntoKin
document_id: OK-AGENT-002
title: Program Bundles and Atomic Source Edits
version: 0.1
date: 2026-10-18
status: experimental-reference-implementation-release-gate-tracked-separately
language_contract: OK-LANG-002 v0.1.1
agent_contract: ontokin.agent/0.2
diagnostic_contract: ontokin.diagnostic/0.2
implementation: ontokin-reference 0.4.0
---

# Program bundles and atomic source edits

## 1. Purpose and authority

An agent must be able to author a reusable component library, bind the exact library it inspected, generate independently identified parts, and repair one occurrence without changing its siblings. A single source-file hash cannot identify that whole program. This engineering contract binds the adopted [OK-LANG-002](../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) to a separate local agent interface.

The new service is `ontokin.agent/0.2`. The existing [OK-AGENT-001](OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) service, `ontokin.agent/0.1`, continues to mean one exact source file. Its retained 0.3.0 measurements remain historical. This document fixes the operation shapes and behavior of the experimental 0.4.0 implementation. Its [measured evidence](construction-validation/README.md) and complete release/publication gate are tracked separately; the full project remains governed by [GOAL](../../GOAL.md) and [STATUS](../../STATUS.md).

The interface remains local and experimental. It introduces no model call during evaluation, network package resolver, host-language extension, shared network listener, distributed transaction service, or production compiler guarantee. Ordinary source validation and playback use deterministic explicit inputs under the named profile and numerical limits.

## 2. Entry points and independent storage

Python clients use:

```python
from pathlib import Path
from ontokin.program_agent import ProgramAgentService

with ProgramAgentService(Path(".ontokin-state")) as service:
    receipt = service.submit(request)
    service.work_next()
    # Use a new status request identity to inspect the retained result.
```

`handle(request, wait=True)` is the synchronous convenience method. `submit`, `work_next`, `get_run`, `accepted_revision`, `expire_result`, and `close` retain the established durable lifecycle. `read_program(project_id, program_revision)` returns the exact immutable `ProgramBundle`; `read_unit(project_id, program_revision, source_id)` returns one detached exact `Source`. These local Python reads do not substitute for versioned transport requests when demonstrating the agent workflow.

The command-line binding is selected explicitly:

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.2 --store .ontokin-state
python3 -m ontokin agent --protocol ontokin.agent/0.2 --store .ontokin-state --request request.json --wait
```

Without `--protocol`, the CLI retains `ontokin.agent/0.1`. A request does not select or migrate a store by changing its `schema_version`. Invalid JSON and startup errors use the explicitly selected response protocol. JSONL defaults to durable queued receipts and a background worker; `--wait` returns terminal responses synchronously. End of input drains this process's queued worker before exit. One-request mode without `--wait` retains the request for a later worker.

The new database is **`program-agent.sqlite3`**, with schema `ontokin.program-agent-store/0.1`. The old `agent.sqlite3` is separate even in the same directory. SQLite document-key columns retain internal implementation names shared with the tested store; none of those names becomes a public claim that a program hash is a file hash. Program snapshots persist canonical inline bundle JSON and verify the adopted program manifest hash when read. Each source string round-trips to its original UTF-8 bytes.

Both stores use the existing local transaction, worker fencing, process identity, WAL, synchronous persistence, request digest, accepted-once snapshot, run compare-and-swap, and artifact retention machinery. There is no implicit conversion of existing projects, cursors, requests, or runs. Moving a project between protocols requires deliberate source authoring through the selected interface.

## 3. Exact request and response contracts

The [request schema](../language-design/agent-v0.2/request.schema.json), [response schema](../language-design/agent-v0.2/response.schema.json), and [diagnostic schema](../language-design/agent-v0.2/diagnostic.schema.json) define the JSON shapes. The additional byte, exact numeric-token, source-scope, dependency, and state rules in this document and OK-LANG-002 are also mandatory. JSON Schema's mathematical `integer` category does not distinguish `1` from `1.0`; protocol counts and offsets require integer JSON tokens, as enforced by the decoder/validator.

Every request identifies `schema_version`, `project_id`, `request_id`, and `operation`. Project/request identities are nonempty strings of at most 200 UTF-8 bytes. Unknown fields and operations reject. Canonical request identity sorts object members while preserving every value and array order. A repeated identity with the same canonical payload returns its retained receipt/result; a changed payload under that identity rejects and cannot enqueue another effect.

The response contains `program_revision`, `accepted_program_revision`, requested/achieved levels, run identity, diagnostics, result, progress, truncation/cursor, and any protocol error. A top-level `source_revision` or old `accepted_revision` is not part of this envelope. Per-file source hashes occur in source records, edit preconditions, diagnostics, manifests, and value origins, where their meaning is explicit.

| Operation | Required operation fields | Additional behavior |
| --- | --- | --- |
| `discover` | `profile`, `limit` | Optional `filter`, `cursor`, and either an inline `bundle` or retained `program_revision`; optional work budgets. |
| `create` | `bundle`, `expected_program_revision: null`, `requested_level` | Requires no accepted head; optional explicit delivery settings and budgets. |
| `edit` | `expected_program_revision`, `patches`, `requested_level` | Optional atomic `module_changes`, delivery settings, and budgets. At least one patch/change is required. |
| `validate` | `program_revision`, `requested_level` | May diagnose retained rejected candidates; evaluated validation covers a fresh complete authored horizon. |
| `inspect` | `program_revision`, `selector`, `fields`, `limit` | Optional matching run/time/frame, pinned cursor, and budgets; never advances the run. |
| `evaluate` | `program_revision`, `run_id`, `until_seconds` | `run_id: null` starts an ordinary run; an existing run may advance its available prefix. |
| `reset` | `program_revision` | Creates a fresh run at time zero before events; optional budgets. |
| `status` / `cancel` | `target_request_id` | Retain the established retry, cancellation, terminal, and unknown-outcome meanings. |
| `export` | `program_revision`, `destination` | Destination must be `ontokin.glb/0.2`; optional export settings and budgets. |
| `artifact` | `artifact_id` | Retrieve exact retained GLB bytes by offset, in chunks of at most 65,536 bytes. |

The semantic profile is `construction-0.1`. Generic `requested_level: delivered` without a supported explicit destination remains unavailable. Delivery options require an explicit destination and a delivered stage; the old `ontokin.glb/0.1` target cannot receive a construction bundle.

## 4. Candidate formation and atomic source editing

`create.bundle` uses [ontokin.bundle/0.1](../language-design/construction-v0.1/bundle.schema.json). Structurally valid bundles receive an immutable program revision before parsing or linking. Invalid source, absent imports, mismatched pins, or conflicting supplied versions can therefore remain inspectable candidates. Malformed transport with duplicate canonical source IDs, invalid descriptor shape, or exceeded input bounds has no fabricated parsed-source diagnostic.

Every patch contains exactly:

```json
{
  "source_id": "entry",
  "source_revision": "sha256:<exact old file hash>",
  "element_id": ["keyed-rack", "demo", "first"],
  "start_byte": 1044,
  "end_byte": 1051,
  "expected_text": "0.75[m]",
  "replacement": "0.9[m]"
}
```

The shown coordinates select the declared length expression in the original [Rack entry](../language-design/construction-v0.1/01-keyed-rack/main.ok); the placeholder hash must be replaced with that exact unit revision. All patches refer to the **same original expected program**, not intermediate text produced by earlier patches. Each source ID/hash, UTF-8 boundary, expected byte slice, and writable element scope must match. Patch ranges in one source cannot overlap or repeat an insertion offset. One source's coordinates never authorize a write in another source.

Inspection exposes explicit whole-unit source scopes as `["sources", source_id]`, including for malformed source. Those are intentionally broad authoring targets. Definition scopes identify their nominal module/class/member declaration; root occurrence scopes permit changes inside the root initializer. A generated occurrence does not acquire writable bytes in its shared collection or class declaration. An agent requesting an occurrence-local repair uses the inspected public initializer target, or explicitly chooses a broader source/definition edit and accepts its dependent scope.

`module_changes` contains explicit records:

```json
{"operation": "add", "module": {"package_id": "example.part", "version": "1.0.0", "filename": "part.ok", "source": "<exact source>"}}
```

```json
{"operation": "remove", "source_id": "package:example.part@1.0.0", "source_revision": "sha256:<old source hash>"}
```

```json
{"operation": "replace", "source_id": "package:example.part@1.0.0", "source_revision": "sha256:<old source hash>", "module": {"package_id": "example.part", "version": "1.0.1", "filename": "part.ok", "source": "<exact new source>"}}
```

Adds cannot overwrite a source already present in the original bundle. Replacement/removal requires the exact prior source hash. A source cannot be patched and replaced/removed, or changed twice, in one candidate. Replacement cannot collide with another original source ID, including another module scheduled for removal. The entry is edited through source patches; this slice does not supply an entry-filename rename operation.

A changed library and every affected import pin belong to one candidate. No partial file edit is accepted. After complete requested-stage validation and surviving-occurrence nominal identity checks, acceptance rechecks the expected whole-program head inside the final transaction. A concurrent winner makes the other candidate stale. Its immutable candidate and any explicitly retained isolated diagnostic run remain identified; it cannot overwrite the winner or publish a delivery artifact as accepted success.

## 5. Inspection, provenance, and discovery

Inspection supports identity, source, values, geometry, matter, relations, actions, state, and support groups. Selectors use an element ID, kind, exact display path, class name, role, relation, and/or source ID. Class names can use the canonical nominal class identity string or an accessible class name in the entry namespace. Display paths preserve literal key steps: `first.fingers["left.eye"].blade` has one input key `left.eye`.

A generated property result separates the imported parameter's definition span/hash from its effective value origin and its available root initializer. `parameter_path` is an array of typed `member`/`key` steps; `rendered_path` supplies valid literal-key source text. `assignment_span` is present only for an override actually authored in that selected root initializer. An unavailable target says why and supplies no fabricated coordinates. The generated object's own unique declaration span is null; its shared collection declaration and keyed input provenance remain separate records.

A collection exposes its declared identity, canonical ordered keys, per-entry occurrence IDs, and read-only reference view. It has no body, mass, frame, transform, or simulation state. Actual generated children retain their actual owning object, even though their IDs include a collection/key step. Property and mechanical records use the existing normalized model distinctions.

Selecting the source group additionally returns the exact source texts needed by the selected records and their definitions/initializer targets. A source-ID selector can narrow source retrieval; an oversized page is an explicit resource failure. A source-only inspection can succeed at returning a malformed candidate's exact file scope and diagnostics with `index_complete: false`; this does not claim represented or constructed success.

Global discovery exposes the construction built-ins and limits. Program-context discovery adds the actual linked public module/class/function/member declarations with exact original UTF-8 spans, package-qualified nominal IDs, and import alias access paths. Private definitions are not offered as public authoring names. Discovery of a signature does not certify every possible invocation, effective inherited value, construction, or physical outcome; those require validation and occurrence inspection.

## 6. Runs, cursors, failures, and atomic publication

Ordinary evaluation and export require a snapshot accepted at least once. Retained older accepted programs remain usable when named explicitly; their results continue to identify the old program. They are never relabeled as current. Rejected candidates can have isolated validation runs for diagnosis but cannot start ordinary runs through that status alone.

A run binds the full program and loaded implementation digest. Prefix evaluation does not preflight a later failure as if it had already happened. It returns the actual last valid interval, including event boundary side. A failed run cannot advance; reset creates another run. Inspection requires a matching interval and never extends it. World-measured velocity retains its established meaning when re-expressed in another frame.

Cursors bind the program, implementation, project, run/sample context, selector, frame, and selected fields. Discovery additionally binds the catalog and linked program context. Altered or mismatched cursors reject. Pagination declares truncation and continuation; a short result caused by exhaustion cannot be called complete.

Accepted head changes, run compare-and-swap, artifacts, and terminal results share one transaction. The complete response is checked before serialization and again before commit. An encoded result failure rolls back all new acceptance/run/artifact effects while preserving already-retained immutable candidates. Control responses use a savepoint around cancellation and envelope validation so an unreturnable control result does not silently commit a cancellation.

Retries, queued cancellation, cooperative running cancellation, dead-process fencing, implementation mismatch, retained unknown outcomes, and administrative result expiry preserve the original operation contracts. A tombstone prevents replay under an expired identity. Local process recovery is conservative; it does not steal work from a proven live worker or supply a distributed lease.

## 7. Limits and error locations

The language/profile limits in OK-LANG-002 apply to the whole source closure. Requests and responses additionally have a 4 MiB compact UTF-8 JSON limit, at most 100,000 logical JSON value entries, and at most 128 nested JSON containers. Counting visits repeated shared values on every occurrence and stops before allocating an unbounded encoded string. Cyclic host values, non-finite numbers, invalid Unicode scalars, and non-string JSON object keys reject.

`max_objects` (1,000), `max_operations` (100,000), `max_result_items` (1,000), `max_elapsed_ms` (30,000), and `max_value_entries` (100,000) can lower the corresponding work budget. A request cannot raise profile limits. Identity paths permit 256 segments; display/query paths permit 32,768 UTF-8 bytes. Cursor transport permits 65,536 bytes. There are at most 1,000 patches and 32 explicit module-change records per request, subject to the stricter resulting bundle limits. Exact source content is capped at 2,000,000 aggregate bytes; the JSON envelope also counts escaping and metadata.

Cancellation and deadlines remain cooperative. Limits are bounded reference-operation contracts, not operating-system resource isolation or hard real-time preemption. Actual performance claims require identified measured cases.

`ontokin.diagnostic/0.2` includes the containing program revision and each actual primary/related source ID/hash/file/span. Cross-file diagnostics never pretend all spans came from the entry file. A program-wide condition without a source node has `primary: null`, null primary source fields, and `location_status: program_condition_without_source_span`; it does not invent an entry offset. Structural transport errors use `protocol_error` and have no fabricated source span.

## 8. Verification gate and remaining work

C08, C09, C13, C18, C19, and C20 in OK-LANG-002 cover scoped editing, exact candidate locations, access/nominal identity, the program lifecycle, deterministic closure identity, and actual delivery. They complement the module/construction/mechanical/resource cases. The original 43 source cases, A01–A10, service tests, and GLB/browser regressions must also retain their meanings.

The release must exercise actual requests, concurrent commit/run races, changed dependencies, rejected UTF-8 candidates, retries, cancellation, independent-process recovery, source/artifact hash integrity, and a generated assembly's decoded/rendered output. Source schemas and this contract fix expectations; neither is an execution report. The [construction validation record](construction-validation/README.md) identifies measured implementation, fixtures, numerical and visual checks, CI, and the release status.
