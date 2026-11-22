# C271 P15 independent first-refusal review

Reviewer: `/root/loader_review`.

**Verdict: the first actual static-admission refusal is confirmed. Stop this technical phase.** The existing reader rejects the selected current Python process's libc because its dynamic table contains tags outside the reader's allowed set. No correction to the recorded outcome is required. No later gate, repair or input substitution is authorized by this review.

## Exact input and source

The recorded input is `/usr/lib/x86_64-linux-gnu/libc.so.6`, 1,995,216 bytes, SHA-256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`. The Director's collector selects the sole `libc.so.6` pathname in its own `/proc/self/maps`, records that path in `INTENT.json`, captures the file's bytes and identity, and then calls the unchanged public metadata reader.

The independent crosscheck parsed the captured ELF bytes without importing the product or retrying that helper. Every dynamic entry through `DT_NULL` agrees with the recorded result. A bounded read of the same actual canonical path also agrees byte for byte, with the same device and inode and a stable before/after file identity. This confirms the captured file binding. It does not reconstruct the earlier process's historical maps or assert a complete runtime dependency inventory.

The reader remains `prototypes/static_tray_v01/current_host_inspection_v01.py` at retained revision `875c81c506d4e5431b909e190ce294c61312029e`, SHA-256 `a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4`. This review verified its current bytes and statically compared its literal allowed-tag assignment and predicate. The public wrapper calls `_read_elf_metadata` directly. `_require` raises `HostInspectionError`, which prefixes the category with `CHI-`.

## Exact first predicate

The first failed check is line 1162 of that exact source:

```python
_require(all(tag in ordinary for tag, _ in entries), "UNSUPPORTED", "Unreviewed ELF dynamic loader feature")
```

The first entry that makes this predicate false is tag `0x70000000` (decimal 1,879,048,192), at file offset 1,980,896. Its value is `0x28000` (163,840). Tags `0x70000001` and `0x70000003` also lie outside the same literal allowed set, at offsets 1,980,912 and 1,980,928. These are facts from the exact inert bytes; assigning additional symbolic names or deciding their semantics is unnecessary to verify this refusal.

The recorded result is therefore consistent with the source: code `CHI-UNSUPPORTED`, reason `Unreviewed ELF dynamic loader feature`, state `REJECTED`, and no underlying exception cause.

The `Unsupported dynamic flags` check occurs later, at lines 1166–1167. It was not reached. The recorded `DT_FLAGS` value of 24 is preserved raw evidence, not the observed first cause. This review did not evaluate that later predicate or any subsequent admission or plan gate.

## Required phase disposition

The Director's observation sequence contains exactly two records: the already bound loader returned metadata, then the actual libc produced the typed refusal. The collector stops immediately on an outcome other than `metadata_returned`. `OUTCOME.json` records `stopped_at_first_refusal: true` and `remaining_input_checks: not_run`.

This is the first concrete blocker for the attempted actual input admission under the unchanged accepted contract. H0 remains unaccepted. There is no adopted operational plan and no H1 approval. Stop technical work in this selected phase and preserve the refusal for the verified partial handoff. Do not continue package, kernel, origin, dependency-closure or plan-eligibility checks; do not alter product, contract or tests, substitute another libc/runtime, or retry the original helper.

The earlier external acceptance of the exact loader's four-entry suffix union remains valid within its stated scope. It did not approve actual libc admission, a complete H0 result or an operational plan. This refusal adds no product approval field, runtime completeness selector or artificial N57 result.

## Evidence and execution disclosure

`CROSSCHECK.json` binds the exact input records, collector, unchanged reader, captured binary and independent result. `verify_first_refusal.py` is the executed standard-library-only review script. It reads source as text/AST and parses bytes; it does not import the product or invoke the original helper.

The Director's admission attempt did import the unchanged production module and call its static data reader, as `OUTCOME.json` explicitly reports. The earlier `HOST-OBSERVATION-BOUNDARY.json` described an earlier point in the session and remains historical evidence; its then-current statement about no product import is not extended to this later observation.

Python tool processes ran. No Node, ldd, direct loader/image command, installation, H1 command, original-seven cohort, full routine, native/model/hosted trial, repair or later-gate probe was performed by this review. The already used bootstrap loader may run implicitly when a Python tool process starts; this is not a claim that no loader instructions executed.

No mandatory correction to the frozen outcome was found. The mandatory disposition is the phase stop above. Active reviewer jobs and unknown operations: none.
