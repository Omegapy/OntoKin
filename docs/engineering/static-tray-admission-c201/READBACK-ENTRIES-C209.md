# C209: exact C201 readback package entries

C209 adds a CPU-only file-binding component for the future C201 readback job.
Readback means reopening the accepted GLB with Khronos Validator and Three.js.
The component identifies which package files that future checker may use. It
does not run Node, intercept a Node import, implement a checker, or establish
that JavaScript has no other dynamic dependency.

The implementation is
[`readback_entries.py`](../../../prototypes/static_tray_admission_c201/readback_entries.py).
It uses the existing accepted-source checks in
[`readback_binding.py`](../../../prototypes/static_tray_admission_c201/readback_binding.py)
without changing the C208 implementation or its `readback-job/0.1` contract.
The new, explicitly selected job schema is `ontokin.c201.readback-job/0.2`.

## Operations and authority

| Operation | Checked behavior |
| --- | --- |
| `bind_entry_readbacks(transactions)` | Revalidates the retained C205/C206 transaction session and its actual package files and declared graph. Writes nothing. |
| `prepare_entry_readback(bindings, slot, accepted=handle)` | Checks the exact accepted transaction and dependencies, then writes one job/0.2 in its bound empty Node output directory. |
| `inspect_entry_readback_job(handle)` | Rereads the accepted closure, entry files and job, then returns a fresh data object. |
| `resolve_entry_import(handle, importer=key, specifier=text)` | Checks a CPU mapping against the exact job and declared direct graph edge. Returns one bound file record; starts no process. |

Prepared handles and jobs retain false `authenticated_execution`,
`node_start_authorized`, `native_start_authorized`, `native_readiness`,
`admission_completed` and `next_slot_authorized` fields. The entry section also
sets `ambient_imports=false` and `node_resolution_authorized=false`.
These fields state the component's limits. A structurally valid record does not
grant a capability or prove a process observation.

The C208 inspector and result verifier reject a C209 prepared handle. There is
no C209 result verifier in this increment. The next wrapper/probe increment must
define its compatible result contract and preserve C208's measurement, failure,
timing and uncertainty obligations. Relabeling a job or successful C208 result
cannot supply that missing compatibility or execution evidence.

## Exact selected package files

The fixed relative entry paths below are grounded in the retained C200
[`format_check.py`](../../../prototypes/static_tray_v01/format_check.py) mapping.
Package roots may differ between hosts, but all selected inputs must lie under
the independently sealed host root. Each package root must be separate; roots
cannot contain one another. All five package entries must belong to the C205
`node_packages` role.

| Named key | Required package and path |
| --- | --- |
| `validator_package` | Exactly one `package.json` naming `gltf-validator`, version `2.0.0-dev.3.10` |
| `validator_entry` | `index.js` beside that metadata file |
| `three_package` | Exactly one `package.json` naming `three`, version `0.186.1` |
| `three_entry` | `build/three.webgpu.js` under the same Three.js package root |
| `gltf_loader_entry` | `examples/jsm/loaders/GLTFLoader.js` under that Three.js root |

The new selector policy is deliberately explicit. Validator metadata must name
`main: "index.js"`, use absent or `commonjs` type, and have no `exports` override.
Three.js metadata must use `type: "module"`, with exact string selectors
`"./webgpu": "./build/three.webgpu.js"` and
`"./examples/jsm/*": "./examples/jsm/*"`. Conditional objects, alternate entry
paths and aliased selectors do not substitute. Other metadata fields remain
bound by the complete file hash but do not select an import.

These selector rules are C209 compatibility requirements. This CPU increment
uses synthetic metadata and does not claim to have inspected installed packages
on a production host. The future independent host seal must verify actual
metadata and all input bytes. A real selector mismatch is a compatibility
blocker requiring explicit review; it must not be silently normalized away.
Three.js revision `186` remains the intended readback observation; this component
does not execute JavaScript to measure that revision.

The other named entries bind the C205 `node_loader`, `admission_node_probe` and
`admission_format_check` roles, and this new binding helper. Every named record
contains its canonical input key, exact absolute path, byte count, SHA-256 and
permission mode. The C205 safe-file reader rejects symlinks, hardlinks, unsafe
ancestor paths, changed files and overlarge reads. Metadata parsing rejects
duplicate JSON fields and uses a 32,768-byte bound.

## Sealed graph and role requirements

The `dependency_entries` section uses
`ontokin.c201.readback-entries/0.1`. It retains the independently sealed complete
closure digest, named roles, package identities, and the Node-facing graph with
exact file bindings. C205's graph is supplied and sealed independently; C209
does not infer it by scanning JavaScript or certify all dynamic imports.

Required direct relationships are:

- The C201 probe depends on all five named package files.
- The Node loader depends on the selected Three.js entry and metadata.
- Validator and Three.js entries depend on their respective metadata.
- GLTFLoader depends on the selected Three.js entry and metadata.

The wrapper must transitively reach every named role, both the new helper and
the C208 helper, and the exact Node executable. A file's presence somewhere in
the overall lock or its membership in a host role is insufficient. The Node
subgraph may contain only the probe, loader and declared package inputs. Each
reachable package dependency must stay inside one of the two selected package
roots. Package inputs cannot simultaneously claim another C205 host role.
The two helper bindings must match the checked component source bytes.

The factory adds no new top-level C205 roles and does not modify its lock schema.
A newly sealed lock must include this helper in its source inventory and in the
wrapper's transitive dependency closure. The future wrapper, probe and loader
remain distinct unimplemented or unverified roles even when synthetic role
files satisfy these CPU controls.

## CPU import mapping

The mapping operation takes an exact bound importer input key. It accepts an
exact normalized absolute file path, an explicit relative file path inside the
same package, or the single retained bare alias `three`. That alias maps to the
selected `build/three.webgpu.js`, subject to a direct dependency edge from the
requesting importer. Every mapping requires the target to be a checked file in
the Node subgraph and a declared direct dependency.

It rejects ambient package lookup, bare package subpaths, inferred extensions,
directory indexes, builtins, file/network URLs, encoded separators, URL queries,
fragments and relative traversal outside the importing package. A globally
inventoried file does not satisfy a missing direct edge. There is no fallback
to Node's resolver or to the current directory. A later actual loader must
enforce the adopted policy in its Node execution context; this Python mapping
alone does not constrain another program's imports.

## Writes, failure and preserved state

The accepted pointer and all transaction artifacts remain read-only. Preparation
rechecks the lock, actual file bytes and accepted closures before and after the
exclusive job write. The existing 4,194,304-byte result/job allowance still
applies. No clock, native allowance, Node allowance or historical expectation
changes.

A preparation attempt consumes its slot in this in-memory component session.
Any preparation failure stops later attempts in that session. Interruption
reports `UNKNOWN`; partial files and the original accepted pointer remain.
Creating a fresh object cannot authorize a retry. Durable one-use receipts,
coordinator stopping and trusted restart handling remain later gates.

The [focused controls](../../../tests/test_static_tray_admission_c201_readback_entries.py)
exercise actual private file reads/writes and accepted-source resolution, with
synthetic package modules and synthetic external receipts. Child-start seams
are blocked. Metadata, roles, graph edges, aliases, stale bindings, post-bind
changes and failed/unknown writes have separate negative controls.

```sh
python3 -B -m unittest tests.test_static_tray_admission_c201_readback_entries -v
```

The four frozen C201 protocol documents and C199/C200 historical source, locks,
evidence, budgets and closed schedules remain unchanged. The C208 original main
fixture timeout and its separately successful rerun remain distinct evidence;
the cause is unproven. The inherited full regression remains failed, with
4,239 distinct passing methods and thirteen torque-read methods not run after
the unchanged 30,000 ms setup timeout. None of those gates is relabeled by this
component. The full [GOAL](../../../GOAL.md) remains open.
