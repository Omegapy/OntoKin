# P16 inert control contract

Control version: `ontokin.c271.libc-plt-controls/1`.

These are frozen future obligations, not executed product tests. All ELF inputs are synthetic regular files with mode `0o600`, not executable programs. JSON observations have explicitly nonoperational schema names. Every expectation is authored literally before any future implementation execution. No genuine operational positive is present.

## Routes and meanings

| Route | Future adapter boundary | Meaning of a positive |
| --- | --- | --- |
| `legacy_public_metadata` | Existing `read_elf_metadata` | Existing metadata behavior only. |
| `legacy_literal_plan_reader` | Existing `/0.1.0` reader dispatch, on this non-Python fixture | Same default tag refusal; not whole-plan validation. |
| `legacy_origin_plan_reader` | Existing `/0.1.1` private dispatch, with the Python subject distinct from this libc fixture | Same default tag refusal; no token rule applied to libc. |
| `libc_plt_metadata` | Proposed private fixed-trio metadata reader | Existing metadata returned for synthetic data; no selected-image pin, plan, closure, PLT correctness or host acceptance. |
| `new_profile_rule` | Proposed exact new schema/profile/object selector only | Selection of the new private branch; no other plan prerequisite proved. Old-schema inputs here test only this new selector, not the old `_plan_shape` diagnostic. |
| `binding_relations` | Proposed selected-role/descriptor/pin primitive | Equality of explicitly mocked, logical observations. No real file binding or operational acceptance. |
| `external_digest` | Existing `_check_plan_digest` primitive | External comparator identity only. |
| `recheck_boundary` | Existing `_recheck` wrapper around an actually invoked new binding primitive | The declared drift and preserved underlying cause under mocked before/after observations. |
| `metadata_fault` | Actual private data reader with the named callback/I/O observation seam | Only the specified propagation/refusal and descriptor cleanup. |

The binding positive deliberately uses the real pinned descriptors as **mocked observations**. `actual_fixture_bytes` separately identifies different synthetic bytes. The synthetic-pin negative coherently substitutes those synthetic descriptors into every logical subject binding and must fail the fixed operational pin. A future adapter may not modify the production constants to make a synthetic positive look operational, treat a mock descriptor as an actual `_bound` success, or dispatch on a case identifier to manufacture an exception.

## Refusal selectors and precedence

New selectors use `HostInspectionError`; `state` remains `REJECTED`, with no cause unless specified. The `details` object contains only the listed `stage` and `rule_id` for these new primitive refusals.

| Boundary | Code | Exact reason | Stage / rule |
| --- | --- | --- | --- |
| New pair mismatch | `CHI-PLAN` | `Unsupported libc PLT schema/profile pair` | `profile_selection` / `PLT-PROFILE` |
| New closed object/type/schema fault | `CHI-PLAN` | `Invalid libc PLT policy shape` | `profile_selection` / `PLT-SHAPE` |
| Selected dependency/interpreter/forbidden-role fault | `CHI-INSPECTOR` | `Selected libc is not the bound author-Python dependency` | `libc_plt_binding` / `PLT-ROLE` |
| Corresponding descriptor/alias/file/image-row disagreement | `CHI-INSPECTOR` | `Libc PLT descriptors or aliases disagree` | `libc_plt_binding` / `PLT-DESCRIPTORS` |
| Coherent but unselected libc/loader digest/size/mode | `CHI-INSPECTOR` | `Libc PLT input is not the selected libc/loader pair` | `libc_plt_binding` / `PLT-PIN` |
| New raw primitive on other admitted architecture/type | `CHI-UNSUPPORTED` | `Libc PLT metadata requires x86-64 ET_DYN` | `libc_plt_tags` / `PLT-ARCH` |
| Incomplete or repeated trio | `CHI-UNSUPPORTED` | `Libc PLT metadata requires one complete tag trio` | `libc_plt_tags` / `PLT-TRIO` |

Order is normative. Existing external authentication and earlier inherited structural/schema guards remain earlier. Within the new selector: pair, then closed shape. Within the pure binding primitive: role relation, corresponding descriptor equality, fixed pins. Actual `_bound` checks then follow before the private parser. Within the private raw reader: inherited ELF structural/terminator checks; new architecture/type; unknown-tag predicate; trio multiplicity; unchanged flags; remaining strings/search-path/identity checks. N14/N15 isolate the relative precedence of unknown tags, missing trio and architecture. Old routes keep their original ordering.

Existing unknown tags retain `CHI-UNSUPPORTED / Unreviewed ELF dynamic loader feature`. Existing flag failures retain `CHI-UNSUPPORTED / Unsupported dynamic flags`, including the synthetic `DT_FLAGS=0x18` case. Existing errors keep their original details; no annotation is added simply because this private route called them. The external-digest primitive retains its existing `LP-EXTERNAL-DIGEST` selector. The repeated combined-profile route retains `CHI-DRIFT / An admitted input changed before/after the command`, `stage=recheck`, `rule_id=LP-RECHECK`, and its exact underlying exception.

## Opaque-value and legacy coverage

The positive metadata cases include the P15 numeric tuple, all zero values, all `2^64-1` values, inconsistent small values, permitted inherited flags, absent flags and reordered trio entries. All return the exact unchanged metadata dictionary in `EXPECTATIONS.json`. The synthetic address in the P15-tuple case lies beyond its tiny file; this is intentional evidence of the stated future **no-dereference** contract, not a valid PLT claim. No tag-derived read or allocation is permitted.

The refusal cases isolate AArch64 collisions, ET_EXEC outside the new target scope, the unrecognized processor-tag hole, other unknown tags, each missing and duplicated trio member, equal and unequal duplicates, unchanged flags and duplicate flags, and later inherited string/path/ELF faults. Old public and both old profile reader routes continue to reject the trio. Tagless x86-64 and AArch64 public metadata retain their existing positive results.

The profile/binding cases separately test new version selection, closed shape, the actual Python needed-name relation, named-role membership, alias/file/image consistency, loader relationship, forbidden extension role, coherent wrong pins and a synthetic input's inability to satisfy the real pin. Their context is deliberately smaller than an operational plan. A later test cannot label this as an actual whole-plan positive.

## Callback and descriptor controls

The future private route must expose bounded named callback checkpoints `before_libc_plt_tag_policy`, `during_libc_plt_tag_scan` and `before_final_elf_identity`, each calling the unchanged zero-argument `check`. These names identify future test seams; they add no public option or environment selector. Old routes must not gain extra checkpoint calls.

Fault contexts require the adapter to inject at the named actual boundary and prove that the boundary was reached. A custom `RuntimeError` sentinel propagates as the same object. A `HostInspectionError` callback sentinel retains object identity and its original details. I/O `OSError` retains the existing bounded-parser wrapping behavior with the original cause. The close spy must observe exactly one close of the descriptor actually opened by the reader on success, refusal and each post-open fault. No expected result may be synthesized by raising before the production boundary.

The short-read case changes only the returned bytes for the declared dynamic-table `pread`. The identity cases change only the final descriptor or named-path identity observation, after the original file was read. These are mocked I/O-boundary controls, not current-host races. All fixture files remain unchanged.

## Author integrity checks and later execution

`build_inert_controls.py` writes fixed headers, segment records, dynamic entries and string bytes; it never implements the proposed acceptance predicate. `verify_inert_controls.py` checks manifests, inert modes, construction bytes, control/expectation coverage and source-preservation bindings without importing production. It does not run the generated fixtures or an operational adapter, and its assertion count is not a product-test count.

A future adapter must bind its own exact source, map each route to the actual production symbol, consume each original expectation unchanged, and disclose which observations are mocked. Static source review must also verify early role/pin proof before helpers/Git/commands and repeated proof on rechecks. All inherited 271 runtime controls and P13's separate historical N57 accounting remain required. No passing gate is inferred from this corpus's size, a source scan, a successful author check or a future private primitive positive.
